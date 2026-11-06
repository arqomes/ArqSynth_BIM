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


def _room_shape(name):
    def fn(ctx, s):
        room = ctx.facts.rooms.get(s.id)
        poly = _poly(room)
        if name == "circulo_inscrito":
            return inscribed_circle(poly)
        if name == "largura_min":
            return narrowest(poly)
        if name == "quadrado_inscrito":
            return inscribed_square(poly)
        if name == "circulo_livre":
            return free_circle(ctx, room)
        if name == "comprimento":
            box = poly.minimum_rotated_rectangle
            pts = np.asarray(box.exterior.coords)[:4]
            return float(max(np.linalg.norm(pts[1] - pts[0]), np.linalg.norm(pts[2] - pts[1])))
        return None
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
        for obj in ctx.doc.objects.values():
            if not getattr(obj, "is_bim", False) or obj.ifc_class not in FRONT or obj.id in (window_id, own_wall):
                continue
            mesh = getattr(obj, "mesh", None)
            if mesh is None or obj is own:
                continue
            v = np.asarray(mesh.verts, dtype=float).reshape(-1, 3)
            if len(v) < 3:
                continue
            top = float(v[:, 2].max()) - floor
            if top <= 0.5:
                continue
            hull = MultiPoint([tuple(p) for p in v[:, :2]]).convex_hull
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
        "circulo_inscrito": _room_shape("circulo_inscrito"),          # (0.419)
        "largura_min": _room_shape("largura_min"),
        "quadrado_inscrito": _room_shape("quadrado_inscrito"),
        "circulo_livre": _room_shape("circulo_livre"),
        "comprimento": _room_shape("comprimento"),
        "envidracado": lambda ctx, s: round(sum(g for _w, g in room_windows(ctx, s.id)), 4),      # (0.420)
        "area_iluminada": lambda ctx, s: lit_area(ctx, _room(ctx, s)),
        "area_sem_luz": lambda ctx, s: max(0.0, float(_room(ctx, s).area) - lit_area(ctx, _room(ctx, s))),
        "n_vaos_exteriores": lambda ctx, s: float(len(room_windows(ctx, s.id))),
    },
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
