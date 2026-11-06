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
        self._boxes = None
        self._hulls = {}

    def keep(self, key, make):
        if key not in self.kept:
            self.kept[key] = make()
        return self.kept[key]

    # ------------------------------------------------------------ (0.422) what is near, quickly
    def boxes(self):
        """[(object, lo (3,), hi (3,))] of the model's elements — made once per check (with their boxes as arrays,
        for near())."""
        if self._boxes is None:
            out = []
            for obj in self.doc.objects.values():
                mesh = getattr(obj, "mesh", None)
                if not getattr(obj, "is_bim", False) or mesh is None:
                    continue
                v = np.asarray(mesh.verts, dtype=float).reshape(-1, 3)
                if len(v):
                    out.append((obj, v.min(axis=0), v.max(axis=0)))
            self._boxes = out
            self._lo = np.array([b[1][:2] for b in out]).reshape(-1, 2)
            self._hi = np.array([b[2][:2] for b in out]).reshape(-1, 2)
        return self._boxes

    def near(self, x0, y0, x1, y1, classes=None, storey=None):
        """The elements (of these classes, on this storey) whose plan box meets the box x0…x1 × y0…y1:
        [(object, lo, hi)]."""
        boxes = self.boxes()
        hit = np.nonzero((self._lo[:, 0] <= x1) & (self._hi[:, 0] >= x0)
                         & (self._lo[:, 1] <= y1) & (self._hi[:, 1] >= y0))[0]
        out = []
        for i in hit:
            o, lo, hi = boxes[i]
            if (classes is None or o.ifc_class in classes) and (storey is None or o.storey == storey):
                out.append((o, lo, hi))
        return out

    def hull(self, obj):
        """An element's outline in plan (the convex hull of its points), made once."""
        if obj.id not in self._hulls:
            import shapely
            v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
            self._hulls[obj.id] = shapely.convex_hull(shapely.multipoints(v[:, :2]))
        return self._hulls[obj.id]

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
    """For each (x, y) point, the z where a vertical ray from z0 (up or down) first meets the triangles (nan: none).
    (0.422) All points against all triangles at once (P × T arrays)."""
    a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    out = np.full(len(points), np.nan)
    ab, ac = b - a, c - a
    det = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0]
    ok = np.abs(det) > 1e-12
    if not ok.any() or not len(points):
        return out
    a, ab, ac, det = a[ok], ab[ok], ac[ok], det[ok]
    p = np.asarray(points, dtype=float).reshape(-1, 2)
    px = p[:, 0:1] - a[None, :, 0]
    py = p[:, 1:2] - a[None, :, 1]
    u = (px * ac[None, :, 1] - py * ac[None, :, 0]) / det[None, :]
    v = (ab[None, :, 0] * py - ab[None, :, 1] * px) / det[None, :]
    inside = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
    z = a[None, :, 2] + u * ab[None, :, 2] + v * ac[None, :, 2]
    if up:
        z = np.where(inside & (z > z0 + 1e-6), z, np.inf)
        best = z.min(axis=1)
        out = np.where(np.isfinite(best), best, np.nan)
    else:
        z = np.where(inside & (z < z0 - 1e-6), z, -np.inf)
        best = z.max(axis=1)
        out = np.where(np.isfinite(best), best, np.nan)
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

def storey_walls(ctx, storey):
    """(0.422) [(Polygon, its bounds)] of a storey's walls and columns in plan — read once per check."""
    def make():
        from shapely.geometry import Polygon
        try:
            polys = [Polygon(w).buffer(0) for w in ctx.doc.ifc.storey_obstacles(storey)]
        except Exception:                               # noqa: BLE001
            polys = []
        return [(p, p.bounds) for p in polys if not p.is_empty]
    return ctx.keep(("storey_walls", storey), make)


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
            mine = unary_union([_poly(r) for r in rooms])
            x0, y0, x1, y1 = mine.bounds
            others = [_poly(r) for r in facts.rooms.values()
                      if r.storey == storey and r.guid not in dwelling.rooms and not uses.is_common(r.use)]
            near = [w for w, (a0, b0, a1, b1) in storey_walls(ctx, storey)
                    if a0 <= x1 + 0.05 and a1 >= x0 - 0.05 and b0 <= y1 + 0.05 and b1 >= y0 - 0.05
                    and w.distance(mine) < 0.02]
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


# ------------------------------------------------------------------ a room's shape (0.419)

def _poly(room):
    from shapely.geometry import Polygon
    poly = Polygon(room.outline, room.holes)
    return poly if poly.is_valid else poly.buffer(0)


def _pieces(geom):
    if geom.is_empty:
        return 0
    return len(getattr(geom, "geoms", [geom]))


def inscribed_circle(poly):
    """The diameter (m) of the largest circle inside a plan (its pole of inaccessibility)."""
    from shapely.ops import polylabel
    if poly.is_empty:
        return 0.0
    if poly.geom_type == "MultiPolygon":
        return max(inscribed_circle(p) for p in poly.geoms)
    centre = polylabel(poly, tolerance=0.005)
    return 2.0 * float(poly.exterior.distance(centre) if not poly.interiors else poly.boundary.distance(centre))


def narrowest(poly):
    """A room's narrowest width (m): eroded from its walls, the half-width at which it splits in two (a neck) or is
    gone — a corridor 1,20 m wide with a door jamb leaving 0,90 m: 0,90."""
    whole = _pieces(poly)
    lo, hi = 0.0, inscribed_circle(poly) / 2.0 + 0.01
    for _k in range(18):
        mid = (lo + hi) / 2.0
        eroded = poly.buffer(-mid, join_style=2)
        if eroded.is_empty or _pieces(eroded) > whole or eroded.area < 1e-6:
            hi = mid
        else:
            lo = mid
    return round(2.0 * lo, 3)


def inscribed_square(poly):
    """The side (m) of the largest square, square to the walls, that fits in a room."""
    lo, hi = 0.0, inscribed_circle(poly) / 2.0 * 1.5 + 0.01
    for _k in range(18):
        mid = (lo + hi) / 2.0
        eroded = poly.buffer(-mid, join_style=2, mitre_limit=10.0)
        if eroded.is_empty or eroded.area < 1e-8:
            hi = mid
        else:
            lo = mid
    return round(2.0 * lo, 3)


def free_circle(ctx, room):
    """The diameter (m) of the largest circle on a room's floor clear of what stands in it (fittings, cabinets,
    furniture): the CTE's cylinder of 1,50 m in a kitchen (art. 41.º d) and a bathroom (art. 43.º n.º 4)."""
    from shapely.geometry import MultiPoint
    from shapely.ops import unary_union
    poly = _poly(room)
    blocks = []
    for obj_id, _kind in ctx.facts.inside.get(room.guid, ()):
        obj = ctx.doc.get(obj_id)
        mesh = getattr(obj, "mesh", None)
        if mesh is None:
            continue
        v = np.asarray(mesh.verts, dtype=float).reshape(-1, 3)
        low = v[v[:, 2] <= v[:, 2].min() + 0.30]                  # (what stands on the floor, up to 0,30 m)
        if len(low) >= 3:
            blocks.append(MultiPoint([tuple(p) for p in low[:, :2]]).convex_hull)
    clear = poly.difference(unary_union(blocks)) if blocks else poly
    return inscribed_circle(clear)


_SHAPES = {}                # (0.422) (measure, a room's outline and holes) -> its value: kept from check to check


def _room_shape(name):
    def fn(ctx, s):
        room = ctx.facts.rooms.get(s.id)
        if name == "circulo_livre":                     # (what stands in it changes without the room changing)
            return free_circle(ctx, room)
        key = (name, tuple(map(tuple, room.outline)), tuple(tuple(map(tuple, h)) for h in room.holes))
        if key in _SHAPES:
            return _SHAPES[key]
        poly = _poly(room)
        if name == "circulo_inscrito":
            value = inscribed_circle(poly)
        elif name == "largura_min":
            value = narrowest(poly)
        elif name == "quadrado_inscrito":
            value = inscribed_square(poly)
        elif name == "comprimento":
            box = poly.minimum_rotated_rectangle
            pts = np.asarray(box.exterior.coords)[:4]
            value = float(max(np.linalg.norm(pts[1] - pts[0]), np.linalg.norm(pts[2] - pts[1])))
        else:
            value = None
        if len(_SHAPES) > 20000:
            _SHAPES.clear()
        _SHAPES[key] = value
        return value
    return fn


# ------------------------------------------------------------------ stairs, ramps, railings (0.419)

def stair_info(ctx, guid):
    """{rise, width, going, risers, riser, flights: [(foot (3,), way (2,), n, h)], world placement}."""
    def make():
        from ..core import stairs as core_stairs
        ifc = ctx.doc.ifc
        p = ifc.stair_params(guid)
        n, h = core_stairs.risers(p["rise"])
        m = np.asarray(ifc.placement(guid), dtype=float)
        flights = []
        for piece in core_stairs.layout(p["form"], p["rise"], p["width"], p["going"], p["turn"]):
            if piece[0] != "flight":
                continue
            _kind, (ox, oy), (dx, dy), k, hk, z0 = piece
            foot = m @ np.array((ox, oy, z0, 1.0))
            way = m[:2, :2] @ np.array((dx, dy))
            flights.append((foot[:3], way / max(np.linalg.norm(way), 1e-9), int(k), float(hk)))
        return {"rise": p["rise"], "width": p["width"], "going": p["going"], "risers": n, "riser": h,
                "flights": flights, "form": p["form"]}
    return ctx.keep(("stair", guid), make)


def stair_headroom(ctx, guid):
    """The clear height (m) over a stair's treads, to what is over them (the slab above, a beam), at the lowest."""
    info = stair_info(ctx, guid)
    lowest = None
    for foot, way, n, h in info["flights"]:
        for i in range(n):
            p = foot[:2] + way * info["going"] * (i + 0.5)
            z = foot[2] + h * (i + 1)
            for cls, lo, hi, verts, tris in ctx.solids():
                if cls not in ABOVE or hi[2] <= z + 0.5 or not (lo[0] <= p[0] <= hi[0] and lo[1] <= p[1] <= hi[1]):
                    continue
                hit = _ray_hits([tuple(p)], z + 0.5, verts, tris, up=True)[0]
                if not np.isnan(hit):
                    lowest = hit - z if lowest is None else min(lowest, hit - z)
    return None if lowest is None else round(float(lowest), 3)


def ramp_info(ctx, guid):
    start, end, width, rise, _t = ctx.doc.ifc.ramp_params(guid)
    length = float(np.linalg.norm(np.asarray(end)[:2] - np.asarray(start)[:2]))
    return {"length": length, "width": float(width), "rise": float(rise)}


# ------------------------------------------------------------------ the dwelling's bathrooms and storage (0.419)

def _complete_bathrooms(ctx, d):
    """The dwelling's complete bathrooms (a toilet, a basin and a shower or a bath): [area]."""
    out = []
    for g in d.rooms:
        r = ctx.facts.rooms.get(g)
        c = ctx.facts.contents.get(g, {})
        if r is not None and r.use == "instalacao_sanitaria" and c.get("toilet") and c.get("basin") and \
                (c.get("shower") or c.get("bath")):
            out.append(float(r.area))
    return out


def _bathrooms(ctx, d, needs=()):
    """The dwelling's bathrooms (rooms of that use) with all of `needs` inside (a need a tuple: any of them)."""
    out = []
    for g in d.rooms:
        r = ctx.facts.rooms.get(g)
        c = ctx.facts.contents.get(g, {})
        if r is None or r.use != "instalacao_sanitaria":
            continue
        if all(any(c.get(k) for k in (need if isinstance(need, tuple) else (need,))) for need in needs):
            out.append(float(r.area))
    return out


def rough_openings(ctx, room_id):
    """(0.421) The area of a room's openings to the outside measured in the rough (RGEU art. 71.º: «medidos no
    tosco»): each window's and glazed door's width × height."""
    total = 0.0
    s = ctx.doc.ifc.unit_scale
    for w, _g in room_windows(ctx, room_id):
        e = ctx.doc.ifc.by_guid(w.guid)
        if e is not None:
            total += float(e.OverallWidth or 0.0) * s * float(e.OverallHeight or 0.0) * s
    return round(total, 4)


def opposite_facades(ctx, d):
    """(0.421) 1 when a dwelling has windows to the outside on two opposite façades (RGEU art. 72.º: cross
    ventilation), else 0."""
    found = []                                          # (across its wall, where it is)
    for g in d.rooms:
        for w, _glass in room_windows(ctx, g):
            n = np.asarray(w.normal, dtype=float)
            found.append((n / max(np.linalg.norm(n), 1e-9), np.asarray(w.middle, dtype=float)))
    for i, (a, pa) in enumerate(found):
        for b, pb in found[i + 1:]:
            # two walls square to the same way (parallel), at least 2 m apart across it: two opposite façades
            if abs(float(np.dot(a, b))) > 0.7 and abs(float(np.dot(pb - pa, a))) > 2.0:
                return 1.0
    return 0.0


def different_facades(ctx, d):
    """(0.421) 1 when a dwelling has windows to the outside on façades of different orientation (CTE art. 76.º n.º 4):
    two walls not parallel, or parallel and apart (opposite façades); else 0."""
    found = []
    for g in d.rooms:
        for w, _glass in room_windows(ctx, g):
            n = np.asarray(w.normal, dtype=float)
            found.append((n / max(np.linalg.norm(n), 1e-9), np.asarray(w.middle, dtype=float)))
    for i, (a, pa) in enumerate(found):
        for b, pb in found[i + 1:]:
            if abs(float(np.dot(a, b))) < 0.7 or abs(float(np.dot(pb - pa, a))) > 2.0:
                return 1.0
    return 0.0


def _storage_area(ctx, d):
    """The dwelling's storage (CTE art. 45.º): its storerooms and pantries, and its wardrobes' floor."""
    total = 0.0
    for g in d.rooms:
        r = ctx.facts.rooms.get(g)
        if r is not None and r.use == "arrumos":
            total += float(r.area)
        for obj_id, kind in ctx.facts.inside.get(g, ()):
            if kind == "wardrobe":
                obj = ctx.doc.get(obj_id)
                if obj is not None and getattr(obj, "mesh", None) is not None:
                    v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
                    span = v.max(axis=0) - v.min(axis=0)
                    total += float(span[0] * span[1])
    return round(total, 3)


# ------------------------------------------------------------------ daylight and what stands in front (0.420)

LIGHT_REACH = 6.0           # m: the part of a room lit by a window (CTE art. 76.º n.º 2)
LOOK_AHEAD = 60.0           # m: how far in front of a window obstacles are looked for
BAND = 2.0                  # m each side of a window's axis (CTE art. 77.º n.º 3)
FRONT = ("IfcWall", "IfcWallStandardCase", "IfcCurtainWall", "IfcColumn", "IfcBuildingElementProxy", "IfcSlab",
         "IfcRoof", "IfcStair", "IfcRailing", "IfcSite", "IfcGeographicElement")


def _shares(total, sizes, gap):
    """Lengths of parts along `total` with `gap` between them: those with a size keep it, the others share the rest."""
    sizes = list(sizes)
    fixed = sum(s for s in sizes if s > 0)
    free = sum(1 for s in sizes if s <= 0)
    rest = max(0.0, total - fixed - gap * max(0, len(sizes) - 1))
    return [s if s > 0 else (rest / free if free else 0.0) for s in sizes]


def glazing(ctx, guid):
    """A window's (or a door's) glazed area (m²): its glass and frosted cells, less its frame, mullions and leaves."""
    def make():
        ifc = ctx.doc.ifc
        e = ifc.by_guid(guid)
        if e is None:
            return 0.0
        s = ifc.unit_scale
        width, height = float(e.OverallWidth or 0.0) * s, float(e.OverallHeight or 0.0) * s
        try:
            d = ifc.opening_design(e)
        except Exception:                               # noqa: BLE001 (another program's: most of it glass)
            return 0.7 * width * height if e.is_a("IfcWindow") else 0.0
        inner_w = width - 2.0 * d.frame
        inner_h = height - (2.0 if d.bottom else 1.0) * d.frame
        area = 0.0
        rows = list(d.rows)
        if d.columns:                                   # (by columns: each «row» a column from the left)
            for col, w in zip(rows, _shares(inner_w, [r.height for r in rows], d.mullion)):
                cells = list(col.cells)
                for cell, h in zip(cells, _shares(inner_h, [c.width for c in cells], d.mullion)):
                    if cell.fill in ("glass", "frosted"):
                        k = d.sash if cell.operation != "fixed" else 0.0
                        area += max(0.0, w - 2 * k) * max(0.0, h - 2 * k)
        else:
            for row, h in zip(rows, _shares(inner_h, [r.height for r in rows], d.mullion)):
                cells = list(row.cells)
                for cell, w in zip(cells, _shares(inner_w, [c.width for c in cells], d.mullion)):
                    if cell.fill in ("glass", "frosted"):
                        k = d.sash if cell.operation != "fixed" else 0.0
                        area += max(0.0, w - 2 * k) * max(0.0, h - 2 * k)
        return round(area, 4)
    return ctx.keep(("glass", guid), make)


def room_windows(ctx, room_id):
    """The windows and glazed doors of a room that open to the outside: [(dw.Door, glazed area)]."""
    out = []
    for w in ctx.facts.windows:
        a, b = ctx.facts.window_sides.get(w.guid, (None, None))
        if (a == room_id and b is None) or (b == room_id and a is None):
            g = glazing(ctx, w.guid)
            if g > 1e-6:
                out.append((w, g))
    return out


def lit_area(ctx, room):
    """The part of a room within 6 m of its windows to the outside (m²)."""
    def make():
        from shapely.geometry import LineString
        from shapely.ops import unary_union
        windows = room_windows(ctx, room.guid)
        if not windows:
            return 0.0
        poly = _poly(room)
        reach = []
        for w, _g in windows:
            n = np.asarray(w.normal, dtype=float)
            along = np.array((-n[1], n[0])) / max(np.linalg.norm(n), 1e-9)
            m = np.asarray(w.middle, dtype=float)
            half = max(w.width, 0.1) / 2.0
            reach.append(LineString([tuple(m - along * half), tuple(m + along * half)]).buffer(LIGHT_REACH))
        return float(poly.intersection(unary_union(reach)).area)
    return ctx.keep(("lit", room.guid), make)


def front_obstacle(ctx, window_id):
    """(distance, height above the room's floor) of what stands in front of a window to the outside — of all the
    obstacles in the 4 m band in front of it (2 m each side of its axis), the one that asks the most of it (CTE art.
    77.º: at least half its height away, and 3 m); (None, None) when nothing stands there."""
    def make():
        from shapely.geometry import LineString, MultiPoint, Polygon
        facts = ctx.facts
        w = next((x for x in facts.windows if x.guid == window_id), None)
        if w is None:
            return (None, None)
        a, b = facts.window_sides.get(window_id, (None, None))
        room = facts.rooms.get(a if b is None else b)
        if room is None:
            return (None, None)
        n = np.asarray(w.normal, dtype=float)
        n = n / max(np.linalg.norm(n), 1e-9)
        m = np.asarray(w.middle, dtype=float)
        poly = _poly(room)
        from shapely.geometry import Point
        if poly.distance(Point(*(m + n * 0.6))) < poly.distance(Point(*(m - n * 0.6))):
            n = -n                                         # (the outside is the side away from the room)
        along = np.array((-n[1], n[0]))
        face = m + n * 0.15                                 # (the wall's outer face, roughly)
        band = Polygon([tuple(face + along * BAND), tuple(face - along * BAND),
                        tuple(face - along * BAND + n * LOOK_AHEAD), tuple(face + along * BAND + n * LOOK_AHEAD)])
        front = LineString([tuple(face + along * BAND), tuple(face - along * BAND)])
        floor = float(room.level)
        own = ctx.doc.get(window_id)
        own_wall = None
        try:
            own_wall = ctx.doc.ifc.host_wall(window_id)
        except Exception:                                   # noqa: BLE001
            pass
        worst = None
        x0, y0, x1, y1 = band.bounds
        for obj, lo, hi in ctx.near(x0, y0, x1, y1, FRONT):          # (0.422: only what is in the band's box)
            if obj.id in (window_id, own_wall) or obj is own:
                continue
            top = float(hi[2]) - floor
            if top <= 0.5:
                continue
            hull = ctx.hull(obj)
            if hull.geom_type != "Polygon" or not hull.intersects(band):
                continue
            d = float(front.distance(hull.intersection(band)))
            if d < 0.30:                                    # (the window's own wall and what touches it)
                continue
            need = d - max(3.0, top / 2.0)
            if worst is None or need < worst[0]:
                worst = (need, d, top)
        return (None, None) if worst is None else (round(worst[1], 3), round(worst[2], 3))
    return ctx.keep(("front", window_id), make)


# ------------------------------------------------------------------ materials (0.422)

def layer_families(ctx, guid):
    """[(material name, its families)] of an element's materials, in order (a wall's from one face to the other)."""
    from . import materials as mat

    def make():
        try:
            names = ctx.doc.ifc.material_names(guid)
        except Exception:                               # noqa: BLE001
            names = []
        return [(n, mat.families(n)) for n in names]
    return ctx.keep(("families", guid), make)


def contacts(ctx, guid, test):
    """How many pairs of layers side by side (an element's) the test finds harmful."""
    layers = layer_families(ctx, guid)
    return float(sum(1 for (_a, fa), (_b, fb) in zip(layers, layers[1:]) if test(fa, fb)))


def _room_side(ctx, guid):
    """The plan point of the room nearest a wall (its inside), or None."""
    from shapely.geometry import Point
    obj = ctx.doc.get(guid)
    if obj is None or getattr(obj, "mesh", None) is None:
        return None
    lo, hi = (np.asarray(c, dtype=float) for c in obj.mesh.bounds())
    centre = Point(float(lo[0] + hi[0]) / 2, float(lo[1] + hi[1]) / 2)
    best = None
    for r in ctx.facts.rooms.values():
        if r.storey != obj.storey or r.external:
            continue
        poly = _poly(r)
        d = poly.distance(centre)
        if d < 1.0 and (best is None or d < best[0]):
            best = (d, poly)
    if best is None:
        return None
    return np.asarray(best[1].representative_point().coords[0], dtype=float)


def outer_leaf(ctx, guid):
    """(0.422) A double masonry wall's outer leaf (m) — the masonry layer on the side away from the rooms, when the
    wall has two masonry leaves with something else between them (CTE art. 92.º n.º 3); None for any other wall."""
    from . import materials as mat
    if sum(1 for _n, f in layer_families(ctx, guid) if "alvenaria" in f) < 2:
        return None                                     # (0.422: one leaf — said by its materials' names, quickly)
    try:
        bands = ctx.doc.ifc.layer_bands(guid)
    except Exception:                                   # noqa: BLE001
        bands = None
    if not bands:
        return None
    fams = [mat.families(name) for name, _n, _d0, _d1 in bands]
    masonry = [k for k, f in enumerate(fams) if "alvenaria" in f]
    if len(masonry) < 2 or masonry[-1] - masonry[0] < 2 or \
            not any("alvenaria" not in fams[k] for k in range(masonry[0] + 1, masonry[-1])):
        return None
    inside = _room_side(ctx, guid)
    n = np.asarray(bands[0][1], dtype=float)
    first, last = bands[masonry[0]], bands[masonry[-1]]
    if inside is not None and float(np.dot(n[:2], inside)) < (bands[0][2] + bands[-1][3]) / 2:
        outer = last                                    # (the room on the low side: the outside is the high one)
    else:
        outer = first
    return round(float(outer[3] - outer[2]), 4)


def damp_course(ctx, guid):
    """(0.422) 1 when a slab on the ground has a membrane layer (polythene, bitumen, PVC…) against the damp rising
    from the soil (CTE art. 99.º), else 0."""
    return 1.0 if any("membrana" in f for _n, f in layer_families(ctx, guid)) else 0.0


def plain_gypsum_in_wet(ctx, room_id):
    """(0.422) How many walls round a wet room have, on its side, plain (not water-resistant) gypsum board."""
    from shapely.geometry import MultiPoint
    from . import materials as mat
    room = ctx.facts.rooms.get(room_id)
    poly = _poly(room)
    inside = np.asarray(poly.representative_point().coords[0], dtype=float)
    count = 0
    x0, y0, x1, y1 = poly.bounds
    for obj, _lo, _hi in ctx.near(x0 - 0.1, y0 - 0.1, x1 + 0.1, y1 + 0.1,
                                  ("IfcWall", "IfcWallStandardCase", "IfcCovering"), room.storey):
        if ctx.hull(obj).distance(poly) > 0.05:
            continue
        try:
            bands = ctx.doc.ifc.layer_bands(obj.id)
        except Exception:                               # noqa: BLE001
            bands = None
        if bands:
            n = np.asarray(bands[0][1], dtype=float)
            side = float(np.dot(n[:2], inside))
            face = bands[0] if abs(side - bands[0][2]) < abs(side - bands[-1][3]) else bands[-1]
            names = [face[0]]
        else:
            names = ctx.doc.ifc.material_names(obj.id)
        for name in names:
            f = mat.families(name)
            if "gesso_cartonado" in f and "hidrofugo" not in f:
                count += 1
                break
    return float(count)


def floor_not_watertight(ctx, room_id):
    """(0.422) 1 when a wet room's floor finish (its «Acabamento do piso», or a floor finish laid in it) is wood or
    carpet — not watertight (CTE art. 98.º) —, else 0."""
    from . import materials as mat
    info = ctx.facts.infos.get(room_id) or {}
    texts = [(info.get("finishes") or {}).get("FloorCovering") or ""]
    room = ctx.facts.rooms.get(room_id)
    poly = _poly(room)
    from shapely.geometry import Point
    x0, y0, x1, y1 = poly.bounds
    for obj, lo, hi in ctx.near(x0, y0, x1, y1, ("IfcCovering",), room.storey):
        if hi[2] - lo[2] < 0.2 and poly.contains(Point(float(lo[0] + hi[0]) / 2, float(lo[1] + hi[1]) / 2)):
            texts += ctx.doc.ifc.material_names(obj.id)
    return 1.0 if any({"madeira", "alcatifa"} & mat.families(t) for t in texts if t) else 0.0


# ------------------------------------------------------------------ the registry

def _layered(extra=None):
    """(0.422) The measures of an element of layers: its harmful contacts — and those of its own kind."""
    from . import materials as mat
    out = {"contactos_galvanicos": lambda ctx, s: contacts(ctx, s.id, mat.galvanic),
           "contactos_eps_betume": lambda ctx, s: contacts(ctx, s.id, mat.eps_bitumen),
           "contactos_cimento_cal": lambda ctx, s: contacts(ctx, s.id, mat.cement_on_lime)}
    out.update(extra or {})
    return out


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
        "circulo_inscrito": _room_shape("circulo_inscrito"),          # (0.419)
        "largura_min": _room_shape("largura_min"),
        "quadrado_inscrito": _room_shape("quadrado_inscrito"),
        "circulo_livre": _room_shape("circulo_livre"),
        "comprimento": _room_shape("comprimento"),
        "envidracado": lambda ctx, s: round(sum(g for _w, g in room_windows(ctx, s.id)), 4),      # (0.420)
        "area_iluminada": lambda ctx, s: lit_area(ctx, _room(ctx, s)),
        "area_sem_luz": lambda ctx, s: max(0.0, float(_room(ctx, s).area) - lit_area(ctx, _room(ctx, s))),
        "n_vaos_exteriores": lambda ctx, s: float(len(room_windows(ctx, s.id))),
        "area_vaos": lambda ctx, s: rough_openings(ctx, s.id),                                    # (0.421)
        "gesso_normal_em_humido": lambda ctx, s: plain_gypsum_in_wet(ctx, s.id),                  # (0.422)
        "pavimento_nao_estanque": lambda ctx, s: floor_not_watertight(ctx, s.id),
    },
    "wall": _layered(extra={"pano_exterior_duplo": lambda ctx, s: outer_leaf(ctx, s.id)}),     # (0.422)
    "slab": _layered(extra={"camada_estanque": lambda ctx, s: damp_course(ctx, s.id)}),
    "roof": _layered(),
    "window": {                                                                                    # (0.420)
        "afastamento_fronteiro": lambda ctx, s: front_obstacle(ctx, s.id)[0],     # (None: nothing in front)
        "altura_fronteira": lambda ctx, s: front_obstacle(ctx, s.id)[1],
        "area_vidro": lambda ctx, s: glazing(ctx, s.id),
    },
    "stair": {                                                        # (0.419)
        "espelho": lambda ctx, s: round(stair_info(ctx, s.id)["riser"], 4),
        "cobertor": lambda ctx, s: float(stair_info(ctx, s.id)["going"]),
        "largura_util": lambda ctx, s: float(stair_info(ctx, s.id)["width"]),
        "desnivel_lanco": lambda ctx, s: max((n * h for _f, _w, n, h in stair_info(ctx, s.id)["flights"]),
                                             default=None),
        "altura_livre": lambda ctx, s: stair_headroom(ctx, s.id),
        "blondel": lambda ctx, s: round(2.0 * stair_info(ctx, s.id)["riser"] + stair_info(ctx, s.id)["going"], 4),
    },
    "ramp": {
        "inclinacao": lambda ctx, s: (lambda r: 100.0 * r["rise"] / r["length"] if r["length"] > 1e-6 else None)(
            ramp_info(ctx, s.id)),
        "comprimento_lanco": lambda ctx, s: ramp_info(ctx, s.id)["length"],
        "largura_util": lambda ctx, s: ramp_info(ctx, s.id)["width"],
        "desnivel": lambda ctx, s: ramp_info(ctx, s.id)["rise"],
    },
    "railing": {
        "altura": lambda ctx, s: float(ctx.doc.ifc.railing_params(s.id)["height"]),
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
        "area_arrumos": lambda ctx, s: _storage_area(ctx, _dwelling(ctx, s)),                    # (0.419)
        "is_completa_maior": lambda ctx, s: max(_complete_bathrooms(ctx, _dwelling(ctx, s)), default=0.0),
        "n_is_completas": lambda ctx, s: float(len(_complete_bathrooms(ctx, _dwelling(ctx, s)))),
        "area_is_total": lambda ctx, s: round(sum(_bathrooms(ctx, _dwelling(ctx, s))), 4),        # (0.421)
        "n_is": lambda ctx, s: float(len(_bathrooms(ctx, _dwelling(ctx, s)))),
        "n_is_acessiveis": lambda ctx, s: float(len(_bathrooms(ctx, _dwelling(ctx, s), (
            "basin", "toilet", "bidet", ("bath", "shower"))))),
        "fachadas_opostas": lambda ctx, s: opposite_facades(ctx, _dwelling(ctx, s)),
        "fachadas_diferentes": lambda ctx, s: different_facades(ctx, _dwelling(ctx, s)),
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


from . import urban as _urban  # noqa: E402 (0.423: the lot's measures — urban.py reads this module's)

MEASURES["lot"] = _urban.MEASURES
for _kind, _more in (("wall", _urban.WALL), ("window", _urban.WINDOW), ("room", _urban.ROOM),   # (0.424)
                     ("slab", _urban.SLAB)):
    MEASURES[_kind].update(_more)


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
