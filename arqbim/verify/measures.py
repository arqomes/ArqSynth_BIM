"""(0.417) The measurers («os medidores»): what is measured in the model, each with the name the rules use.

A rule never measures: it names a measure («area_util», «pe_direito_80», «largura_util»…) of a subject (a room, a
dwelling, a door, the building) and compares it. A new rule is data (regulamentos/); a new measure is code, here, with
its test. A measure that cannot be made (no ceiling over a room: its height is not known) is None — the rule is then
«not checked», never failed."""

from dataclasses import dataclass, field

import numpy as np

from . import uses

GRID = 0.50                 # m: the spacing of the points a room's ceiling height is measured at
MOST_POINTS = 160           # at most this many in a room (the grid widened for a big one)
INSET = 0.15                # m kept off the walls
ABOVE = ("IfcSlab", "IfcRoof", "IfcCovering", "IfcBeam")     # what a ceiling height is measured to
BELOW = ("IfcSlab", "IfcCovering")                           # …and from


@dataclass
class Subject:
    kind: str                   # "room" | "dwelling" | "door" | "building"
    id: str                     # a room's / door's GlobalId, a dwelling's name, "building"
    name: str                   # as said to the architect («Sala (Fogo A)»)
    elements: list = field(default_factory=list)    # GlobalIds to select / go to
    storey: str = None
    props: dict = field(default_factory=dict)       # what the rules filter on (use, typology, role…)


class Context:
    """What the measures read: the document, the reader's facts, the project's settings — and what was measured
    already (one measure asked by several rules is made once)."""

    def __init__(self, doc, facts, settings=None):
        self.doc, self.facts, self.settings = doc, facts, settings or {}
        self.kept = {}
        self._solids = None

    def keep(self, key, make):
        if key not in self.kept:
            self.kept[key] = make()
        return self.kept[key]

    # ------------------------------------------------------------ the model's solids, for heights
    def solids(self):
        """[(class, lo (3,), hi (3,), verts, tris)] of what can be over or under a room."""
        if self._solids is None:
            out = []
            for obj in self.doc.objects.values():
                if not getattr(obj, "is_bim", False) or obj.ifc_class not in ABOVE + BELOW:
                    continue
                mesh = getattr(obj, "mesh", None)
                if mesh is None or not hasattr(mesh, "tris") or not len(mesh.tris):
                    continue
                v = np.asarray(mesh.verts, dtype=float)
                out.append((obj.ifc_class, v.min(axis=0), v.max(axis=0), v, np.asarray(mesh.tris)))
            self._solids = out
        return self._solids


# ------------------------------------------------------------------ vertical rays

def _ray_hits(points, z0, verts, tris, up=True):
    """For each (x, y) point, the z where a vertical ray from z0 (up or down) first meets the triangles (nan: none)."""
    a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    out = np.full(len(points), np.nan)
    # 2D barycentric test of each point in each triangle, then the plane's z there
    ab, ac = b - a, c - a
    det = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0]
    ok = np.abs(det) > 1e-12
    if not ok.any():
        return out
    a, ab, ac, det = a[ok], ab[ok], ac[ok], det[ok]
    for k, (x, y) in enumerate(points):
        px, py = x - a[:, 0], y - a[:, 1]
        u = (px * ac[:, 1] - py * ac[:, 0]) / det
        v = (ab[:, 0] * py - ab[:, 1] * px) / det
        inside = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
        if not inside.any():
            continue
        z = a[inside, 2] + u[inside] * ab[inside, 2] + v[inside] * ac[inside, 2]
        z = z[z > z0 + 1e-6] if up else z[z < z0 - 1e-6]
        if len(z):
            out[k] = z.min() if up else z.max()
    return out


def _room_points(room):
    """Points inside a room, on a grid, kept off its walls (at least its label point)."""
    from shapely.geometry import Point, Polygon
    from ..core.rooms import label_point
    poly = Polygon(room.outline, room.holes)
    if not poly.is_valid:
        poly = poly.buffer(0)
    inner = poly.buffer(-INSET)
    if inner.is_empty:
        inner = poly
    x0, y0, x1, y1 = inner.bounds
    step = GRID
    while ((x1 - x0) / step + 1) * ((y1 - y0) / step + 1) > MOST_POINTS:
        step *= 1.4
    xs = np.arange(x0 + step / 2, x1, step)
    ys = np.arange(y0 + step / 2, y1, step)
    pts = [(float(x), float(y)) for x in xs for y in ys if inner.contains(Point(x, y))]
    if not pts:
        pts = [tuple(map(float, label_point(poly)))]
    return pts


def room_heights(ctx, room):
    """The clear heights (m) at points spread over a room: from its floor (the top of the slab or floor finish under
    the point, else the storey's level) to what is over it (a ceiling, the slab or roof above, a beam); None where
    nothing is over it."""
    def make():
        pts = _room_points(room)
        level = float(room.level)
        floor = np.full(len(pts), level)
        top = np.full(len(pts), np.nan)
        xy = np.array(pts)
        lo_xy, hi_xy = xy.min(axis=0), xy.max(axis=0)
        for cls, lo, hi, verts, tris in ctx.solids():
            if hi[0] < lo_xy[0] or lo[0] > hi_xy[0] or hi[1] < lo_xy[1] or lo[1] > hi_xy[1]:
                continue
            if cls in ABOVE and hi[2] > level + 1.0:
                top = np.fmin(top, _ray_hits(pts, level + 1.0, verts, tris, up=True))   # (nan: no hit)
            if cls in BELOW and lo[2] < level + 1.0 and hi[2] > level - 0.5:
                z = _ray_hits(pts, level + 1.0, verts, tris, up=False)
                floor = np.where(np.isnan(z), floor, np.maximum(floor, z))
        heights = top - floor
        return [None if np.isnan(h) else float(h) for h in heights]
    return ctx.keep(("heights", room.guid), make)


def _height_measure(ctx, room, share):
    """The height a room has over `share` of its floor (1: everywhere — its lowest; 0,8: over 80 % of it)."""
    known = [h for h in room_heights(ctx, room) if h is not None]
    if not known or len(known) < 0.5 * len(room_heights(ctx, room)):
        return None
    known.sort()
    k = int(np.floor((1.0 - share) * (len(known) - 1) + 1e-9))
    return float(known[k])


# ------------------------------------------------------------------ the dwellings' gross area

def dwelling_gross_area(ctx, dwelling):
    """A dwelling's gross area (área bruta, CTE art. 40.º n.º 4): its rooms with the walls round them — the outer walls
    and those to the common areas whole, those to another dwelling half — on each storey, added. Measured from the
    rooms' plans and the storeys' walls."""
    def make():
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
        facts = ctx.facts
        total = 0.0
        by_storey = {}
        for g in dwelling.rooms:
            r = facts.rooms.get(g)
            if r is not None and not r.external:
                by_storey.setdefault(r.storey, []).append(r)
        for storey, rooms in by_storey.items():
            mine = unary_union([Polygon(r.outline, r.holes).buffer(0) for r in rooms])
            others = [Polygon(r.outline, r.holes).buffer(0) for r in facts.rooms.values()
                      if r.storey == storey and r.guid not in dwelling.rooms and not uses.is_common(r.use)]
            try:
                walls = [Polygon(w).buffer(0) for w in ctx.doc.ifc.storey_obstacles(storey)]
            except Exception:                           # noqa: BLE001
                walls = []
            near = [w for w in walls if w.distance(mine) < 0.02]
            around = unary_union(near).difference(mine) if near else None
            area = mine.area
            if around is not None and not around.is_empty:
                area += around.area
                if others:                                  # (the walls to another dwelling: half of them)
                    shared = around.intersection(unary_union(others).buffer(0.30))
                    area -= shared.area / 2.0
            total += area
        return float(total)
    return ctx.keep(("gross", dwelling.name), make)


# ------------------------------------------------------------------ doors

def door_clear(ctx, guid):
    """(clear width, clear height) of a door (m): its opening less its lining on both sides and, for a hinged door,
    its leaf's thickness (open at 90°, it stands in the way); None when it is not known."""
    def make():
        ifc = ctx.doc.ifc
        e = ifc.by_guid(guid)
        if e is None:
            return None
        s = ifc.unit_scale
        width = float(e.OverallWidth or 0.0) * s
        height = float(e.OverallHeight or 0.0) * s
        if width <= 0:
            return None
        frame, leaf, sliding = 0.05, 0.04, False
        try:
            design = ifc.opening_design(e)
            frame, leaf = float(design.frame), float(design.sash_depth)
            ops = [cell.operation for cell in design.rows[0].cells] if design.rows else []
            sliding = bool(ops) and all(o.startswith("slide") or o == "fixed" for o in ops)
        except Exception:                               # noqa: BLE001 (another program's door: the usual sizes)
            pass
        clear_w = width - 2.0 * frame - (0.0 if sliding else leaf)
        clear_h = height - frame
        return (round(clear_w, 4), round(clear_h, 4))
    return ctx.keep(("door", guid), make)


# ------------------------------------------------------------------ the registry

def _room(ctx, subject):
    return ctx.facts.rooms.get(subject.id)


def _dwelling(ctx, subject):
    return ctx.facts.dwelling(subject.id)


def _bedroom_areas(ctx, d):
    return sorted((ctx.facts.rooms[g].area for g in d.rooms if g in ctx.facts.rooms
                   and uses.is_bedroom(ctx.facts.rooms[g].use) and not ctx.facts.rooms[g].external), reverse=True)


def _use_area(ctx, d, keys):
    return float(sum(ctx.facts.rooms[g].area for g in d.rooms if g in ctx.facts.rooms
                     and ctx.facts.rooms[g].use in keys))


MEASURES = {
    "room": {
        "area_util": lambda ctx, s: float(_room(ctx, s).area),
        "pe_direito_min": lambda ctx, s: _height_measure(ctx, _room(ctx, s), 1.0),
        "pe_direito_80": lambda ctx, s: _height_measure(ctx, _room(ctx, s), 0.8),
    },
    "dwelling": {
        "area_bruta": lambda ctx, s: dwelling_gross_area(ctx, _dwelling(ctx, s)),
        "area_util": lambda ctx, s: float(_dwelling(ctx, s).useful_area),
        "area_habitavel": lambda ctx, s: _use_area(ctx, _dwelling(ctx, s),
                                                  [k for k in uses.USES if uses.is_habitable(k)]),
        "areas_quartos": lambda ctx, s: _bedroom_areas(ctx, _dwelling(ctx, s)),
        "n_quartos": lambda ctx, s: float(_dwelling(ctx, s).bedrooms),
        "area_sala_cozinha_suplementos": lambda ctx, s: _use_area(
            ctx, _dwelling(ctx, s), ("sala", "cozinha", "sala_cozinha", "refeicoes", "tratamento_roupa")),
    },
    "door": {
        "largura_util": lambda ctx, s: (door_clear(ctx, s.id) or (None,))[0],
        "altura_util": lambda ctx, s: (door_clear(ctx, s.id) or (None, None))[1],
    },
    "building": {
        "n_pisos": lambda ctx, s: float(s.props.get("storeys", 0)),
        "altura": lambda ctx, s: s.props.get("height"),
    },
}


def measure(ctx, subject, name):
    fn = MEASURES.get(subject.kind, {}).get(name)
    if fn is None:
        return None
    try:
        return ctx.keep(("m", subject.kind, subject.id, name), lambda: fn(ctx, subject))
    except Exception:                                   # noqa: BLE001 (a measure that fails is «not known»)
        import logging
        logging.getLogger("arqbim").exception("measure %s of %s", name, subject.id)
        return None
