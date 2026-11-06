"""(0.423) Town planning: the lot (ifc/lot.py) and the building on it, as the town plans and the codes measure them —
the footprint («área de implantação»), the gross floor area («área de construção»), the indices, the storeys above
and below the ground, the façade's height («cércea»), the setbacks from the lot's sides («afastamentos»), what is
built outside the lot, how much of it is sealed («impermeabilização»).

What is built on a storey: its walls and columns and what they enclose (core/rooms.regions), less its exterior rooms
(a patio enclosed by walls counts as built until a room says it is outside). The ground: the storey nearest the level
0 — those under it are below the ground («caves»). Measured only from the walls and columns this program made
(ifc/spaces.storey_obstacles)."""

import numpy as np

from ..core import lot as core_lot
from . import measures as ms
from . import uses

FACADE = ("IfcWall", "IfcWallStandardCase", "IfcCurtainWall", "IfcRailing")     # what makes a façade's height
NOT_BUILDING = ("IfcGeographicElement", "IfcSite", "IfcSpace", "IfcOpeningElement", "IfcAnnotation", "IfcGrid",
                "IfcVirtualElement")
SEALED = ("IfcSlab", "IfcCovering")


def lot_info(ctx):
    """The lot ({"outline", "fronts", "chosen", "name", "area", "roles", "polygon"}), its front found from the
    entrance when none was chosen — or None."""
    def make():
        try:
            info = ctx.doc.ifc.lot()
        except Exception:                               # noqa: BLE001 (the IFC still being read)
            info = None
        if info is None:
            return None
        fronts = info["fronts"] or core_lot.auto_fronts(info["outline"], entrance(ctx))
        return dict(info, fronts=fronts, roles=core_lot.roles(info["outline"], fronts),
                    polygon=core_lot.polygon(info["outline"]))
    return ctx.keep("lot", make)


def entrance(ctx):
    """The middle (x, y) of the building's entrance: the widest door between a room (or a place the walls close)
    and the outside, on the storey nearest the ground — or None."""
    facts = ctx.facts
    ground = ground_storey(ctx)
    best = None
    for door in facts.doors:
        a, b = facts.sides.get(door.guid, (None, None))
        if (a is None) == (b is None):
            continue
        rank = (door.storey == ground, door.width)
        if best is None or rank > best[0]:
            best = (rank, door.middle)
    return best[1] if best is not None else None


def levels(ctx):
    def make():
        try:
            return {g: float(z) for g, _n, z in ctx.doc.storeys()}
        except Exception:                               # noqa: BLE001
            return {}
    return ctx.keep("levels", make)


def ground_storey(ctx):
    found = levels(ctx)
    return min(found, key=lambda g: (abs(found[g]), -found[g])) if found else None


def ground_level(ctx):
    g = ground_storey(ctx)
    return levels(ctx).get(g, 0.0) if g is not None else 0.0


def storey_footprint(ctx, storey):
    """What is built on a storey in plan (a shapely shape), or None."""
    def make():
        from shapely.ops import unary_union
        from ..core import rooms as core_rooms
        walls = [p for p, _box in ms.storey_walls(ctx, storey)]       # (0.424: read once, with the gross areas')
        if not walls:
            return None
        shape = unary_union(walls + core_rooms.regions(walls))
        outside = [ms._poly(r) for r in ctx.facts.rooms.values()
                   if r.storey == storey and (r.external or uses.is_exterior(r.use))]
        if outside:
            shape = shape.difference(unary_union(outside).buffer(0.01))
        if shape.is_empty:
            return None
        import shapely
        shapely.prepare(shape)                          # (asked «is this point in it?» for every façade)
        return shape
    return ctx.keep(("footprint", storey), make)


def storeys_built(ctx, above=True):
    """The storeys above (or under) the ground with something built on them."""
    ground = ground_level(ctx)
    out = []
    for g, z in sorted(levels(ctx).items(), key=lambda kv: kv[1]):
        if (z >= ground - 0.5) == above and storey_footprint(ctx, g) is not None:
            out.append(g)
    return out


def footprint(ctx):
    """The building's footprint: the union of what is built on the storeys above the ground — or None."""
    def make():
        from shapely.ops import unary_union
        shapes = [storey_footprint(ctx, g) for g in storeys_built(ctx)]
        return unary_union(shapes) if shapes else None
    return ctx.keep("footprint_all", make)


def with_projections(ctx):
    """The footprint and what juts out over the ground from the storeys above (balconies: slabs past the walls) —
    the setbacks are measured from these too (CTE art. 22.º n.º 4)."""
    def make():
        from shapely.ops import unary_union
        base = footprint(ctx)
        ground = ground_level(ctx)
        upper = {g for g, z in levels(ctx).items() if z > ground + 0.5}
        parts = [] if base is None else [base]
        for obj, _lo, _hi in ctx.near(-1e9, -1e9, 1e9, 1e9, ("IfcSlab",)):
            if obj.storey in upper:
                hull = ctx.hull(obj)
                if hull.geom_type == "Polygon":
                    parts.append(hull)
        return unary_union(parts) if parts else None
    return ctx.keep("projections", make)


def _area(shape):
    return round(float(shape.area), 2) if shape is not None else None


def implantation(ctx):
    return _area(footprint(ctx))


def floor_area(ctx):
    """The gross floor area above the ground: each storey's built area, summed."""
    built = storeys_built(ctx)
    return round(sum(float(storey_footprint(ctx, g).area) for g in built), 2) if built else None


def _index(value, lot):
    if value is None or lot is None or lot["area"] <= 1e-9:
        return None
    return round(float(value) / float(lot["area"]), 4)


def facade_height(ctx):
    """The «cércea»: from the ground to the top of the façade — the walls, curtain walls and railings on the
    building's outline (a parapet, a roof terrace's railing; not a pitched roof over the eaves)."""
    def make():
        base = footprint(ctx)
        if base is None:
            return None
        edge = base.boundary.buffer(0.15)
        x0, y0, x1, y1 = edge.bounds
        top = None
        for obj, _lo, hi in ctx.near(x0, y0, x1, y1, FACADE):
            if (top is None or hi[2] > top) and ctx.hull(obj).intersects(edge):
                top = float(hi[2])
        return round(top - ground_level(ctx), 3) if top is not None else None
    return ctx.keep("cercea", make)


def building_height(ctx):
    """From the ground to the building's highest point (a ridge, a chimney), or None."""
    def make():
        base = footprint(ctx)
        if base is None:
            return None
        x0, y0, x1, y1 = base.buffer(2.0).bounds
        tops = [float(hi[2]) for obj, _lo, hi in ctx.near(x0, y0, x1, y1) if obj.ifc_class not in NOT_BUILDING]
        return round(max(tops) - ground_level(ctx), 3) if tops else None
    return ctx.keep("altura_edificio", make)


def setback(ctx, role):
    """The least distance from the building (and what juts out of it) to the lot's sides of that role."""
    lot = lot_info(ctx)
    if lot is None:
        return None
    indices = [k for k, r in lot["roles"].items() if r == role]
    return core_lot.distance_to(with_projections(ctx), lot["outline"], indices)


def outside_lot(ctx):
    """How much of the building (m²) stands outside the lot."""
    lot = lot_info(ctx)
    shape = with_projections(ctx)
    if lot is None or lot["polygon"] is None or shape is None:
        return None
    return round(float(shape.difference(lot["polygon"]).area), 2)


def sealed(ctx):
    """The part of the lot built on or paved (0 to 1): the footprint and the slabs and floor finishes on the ground
    storey — a pool's too —, over the lot's area."""
    lot = lot_info(ctx)
    if lot is None or lot["polygon"] is None or lot["area"] <= 1e-9:
        return None
    from shapely.ops import unary_union
    parts = [] if footprint(ctx) is None else [footprint(ctx)]
    ground = ground_storey(ctx)
    for obj, _lo, _hi in ctx.near(*lot["polygon"].bounds, SEALED, ground):
        hull = ctx.hull(obj)
        if hull.geom_type == "Polygon":
            parts.append(hull)
    if not parts:
        return 0.0
    return round(float(unary_union(parts).intersection(lot["polygon"]).area) / float(lot["area"]), 4)


# ------------------------------------------------------------------ (0.424) façades: their height and what faces them

OPPOSITE = ("IfcWall", "IfcWallStandardCase", "IfcCurtainWall")     # what makes the façade opposite
LOOK = 60.0             # m: how far a façade looks for the one opposite
A_FACADE = 2.2          # m: a wall that high above the ground is a façade — a lower one is a garden wall


def _turned_out(ctx, x, y, n, storey=None):
    """n (a unit vector in plan) turned to point out of the building — away from its footprint."""
    ways = _ways_out(ctx, x, y, n, storey)
    return ways[0] if ways else np.asarray(n, dtype=float)


def _ways_out(ctx, x, y, n, storey=None):
    """The ways out of the building from a wall at (x, y) across n, by what is built on its storey 0,6 m to each
    side: the side not built — both for a wall standing alone (a garden wall), none for a wall inside."""
    import shapely
    base = storey_footprint(ctx, storey) if storey is not None else footprint(ctx)
    n = np.asarray(n, dtype=float)
    if base is None:
        return [n, -n]
    ahead = bool(shapely.contains_xy(base, x + n[0] * 0.6, y + n[1] * 0.6))
    behind = bool(shapely.contains_xy(base, x - n[0] * 0.6, y - n[1] * 0.6))
    if ahead and behind:
        return []
    if not ahead and not behind:
        return [n, -n]
    return [n] if not ahead else [-n]


def height_at(ctx, x, y):
    """The façade's height at a point of it (m above the ground): the top of the walls, curtain walls and railings
    there — or None."""
    from shapely.geometry import Point
    items, _hulls, tree = _facades(ctx, FACADE, 0.0)
    if tree is None:
        return None
    near = tree.query(Point(float(x), float(y)), predicate="dwithin", distance=0.3)
    tops = [items[int(i)][1] for i in near]
    return round(max(tops) - ground_level(ctx), 3) if tops else None


def facing(ctx, x, y, n, skip=()):
    """(distance, height above the ground) of the first façade in front of the point (x, y) looking along n — a wall
    or curtain wall at least a storey high, within 60 m —, or None."""
    import shapely
    from shapely.geometry import LineString, Point
    items, hulls, tree = _facades(ctx)
    if tree is None:
        return None
    start = Point(float(x), float(y))
    ray = LineString([(float(x), float(y)), (float(x + n[0] * LOOK), float(y + n[1] * LOOK))])
    crossed = tree.query(ray, predicate="intersects")
    if not len(crossed):
        return None
    least = shapely.distance(start, hulls[crossed])     # (along the ray it is at least this far)
    ground = ground_level(ctx)
    best = None
    for k in np.argsort(least):                         # (nearest first — stop when none can be nearer)
        if best is not None and least[k] > best[0]:
            break
        i = int(crossed[k])
        obj, top = items[i]
        if obj.id in skip:
            continue
        d = float(start.distance(hulls[i].intersection(ray)))
        if d < 0.3:                                     # (its own wall, and those that touch it)
            continue
        if best is None or d < best[0]:
            best = (round(d, 3), round(top - ground, 3))
    return best


def _facades(ctx, classes=OPPOSITE, low=A_FACADE):
    """([(element, its top)], their outlines in plan (an array), an STRtree of them) of the walls and curtain walls a
    storey high or more (or of these classes, this high) — made once per check."""
    def make():
        import shapely
        ground = ground_level(ctx)
        items, hulls = [], []
        for obj, _lo, hi in ctx.near(-1e12, -1e12, 1e12, 1e12, classes):
            if float(hi[2]) - ground < low:
                continue
            hull = ctx.hull(obj)
            if hull.geom_type == "Polygon":
                items.append((obj, float(hi[2])))
                hulls.append(hull)
        if not hulls:
            return [], None, None
        array = np.empty(len(hulls), dtype=object)
        array[:] = hulls
        return items, array, shapely.STRtree(array)
    return ctx.keep(("facades", classes, low), make)


def wall_faces(ctx, guid):
    """[(x, y, n)]: the middle of a wall's outer face and its outward direction (both faces of a wall standing
    alone) — [] for what is not a straight wall of this program."""
    def make():
        obj = ctx.doc.get(guid)                         # (0.424: from its outline in plan, already made — the
        if obj is None or getattr(obj, "mesh", None) is None:     # IFC's axis read for 900 walls was most of the time)
            return []
        hull = ctx.hull(obj)
        if hull.geom_type != "Polygon":
            return []
        corners = np.asarray(hull.minimum_rotated_rectangle.exterior.coords, dtype=float)[:4]
        a, b = corners[1] - corners[0], corners[2] - corners[1]
        along, across = (a, b) if np.linalg.norm(a) >= np.linalg.norm(b) else (b, a)
        length, thickness = float(np.linalg.norm(along)), float(np.linalg.norm(across))
        if length < 1e-6 or thickness < 1e-6:
            return []
        m = corners.mean(axis=0)
        out = []
        for n in _ways_out(ctx, m[0], m[1], across / thickness, obj.storey):
            face = m + n * (thickness / 2.0)
            out.append((float(face[0]), float(face[1]), n))
        return out
    return ctx.keep(("wall_faces", guid), make)


def wall_face(ctx, guid):
    """(x, y, n) of a wall's (first) outer face, or None."""
    faces = wall_faces(ctx, guid)
    return faces[0] if faces else None


def opposite(ctx, guid):
    """(CTE art. 21.º, RGEU art. 59.º) The distance from a wall's outer face to the façade opposite — the nearest, of
    both faces for a wall standing alone —, or None (none within 60 m)."""
    found = [f for f in (facing(ctx, x, y, n, (guid,)) for x, y, n in wall_faces(ctx, guid)) if f is not None]
    return min(f[0] for f in found) if found else None


def window_face(ctx, window_id):
    """(x, y, n) of a window: the middle of its outer face, and the way out — or None."""
    def make():
        w = next((x for x in ctx.facts.windows if x.guid == window_id), None)
        if w is None:
            return None
        n = np.asarray(w.normal, dtype=float)
        n = n / max(float(np.linalg.norm(n)), 1e-9)
        m = np.asarray(w.middle, dtype=float)
        a, b = ctx.facts.window_sides.get(window_id, (None, None))
        room = ctx.facts.rooms.get(a if b is None else b)
        if room is not None:                            # (out: away from its room)
            from shapely.geometry import Point
            poly = ms._poly(room)
            if poly.distance(Point(*(m + n * 0.6))) < poly.distance(Point(*(m - n * 0.6))):
                n = -n
        else:
            n = _turned_out(ctx, m[0], m[1], n)
        host = _host(ctx, window_id)                    # (to its wall's outer face)
        wall = wall_face(ctx, host) if host else None
        off = float(np.dot(np.array(wall[:2]) - m, n)) if wall is not None else -1.0
        face = m + n * (off if 0.0 <= off <= 1.0 else 0.1)
        return float(face[0]), float(face[1]), n
    return ctx.keep(("window_face", window_id), make)


def _host(ctx, guid):
    try:
        return ctx.doc.ifc.host_wall(guid)
    except Exception:                                   # noqa: BLE001
        return None


def boundary_ahead(ctx, x, y, n):
    """(distance, role) to the lot's side straight ahead of the point (x, y) looking along n — or None (no lot, or
    no side ahead)."""
    lot = lot_info(ctx)
    if lot is None:
        return None
    from shapely.geometry import LineString, Point
    start = Point(float(x), float(y))
    ray = LineString([(float(x), float(y)), (float(x + n[0] * 1000.0), float(y + n[1] * 1000.0))])
    best = None
    for k, (a, b) in enumerate(core_lot.sides(lot["outline"])):
        hit = LineString([a, b]).intersection(ray)
        if hit.is_empty:
            continue
        d = float(start.distance(hit))
        if best is None or d < best[0]:
            best = (round(d, 3), lot["roles"].get(k))
    return best


def neighbour_setback(ctx, window_id):
    """How far a window looks to the next lot (CTE art. 22.º n.os 2 and 3): to the side of the lot straight in front
    of it, when that side is not the street — None when it faces the street, or there is no lot."""
    face = window_face(ctx, window_id)
    if face is None:
        return None
    found = boundary_ahead(ctx, *face)
    if found is None or found[1] == core_lot.FRONT:
        return None
    return found[0]


def patio_height(ctx, room_id):
    """The highest façade round a patio (m above its floor): the walls and curtain walls along its outline."""
    room = ctx.facts.rooms.get(room_id)
    if room is None:
        return None
    poly = ms._poly(room)
    edge = poly.boundary.buffer(0.35)
    x0, y0, x1, y1 = edge.bounds
    tops = [float(hi[2]) for obj, _lo, hi in ctx.near(x0, y0, x1, y1, OPPOSITE) if ctx.hull(obj).intersects(edge)]
    return round(max(tops) - float(room.level), 3) if tops else None


def over_street(ctx, slab_id):
    """How high over the ground a slab that juts out over the street is (CTE art. 24.º n.º 2: a balcony, a canopy
    past the lot's front) — the underside's height; None when it does not."""
    lot = lot_info(ctx)
    obj = ctx.doc.get(slab_id)
    if lot is None or lot["polygon"] is None or obj is None or getattr(obj, "mesh", None) is None:
        return None
    hull = ctx.hull(obj)
    if hull.geom_type != "Polygon":
        return None
    out = hull.difference(lot["polygon"])
    if out.is_empty or out.area < 0.01:
        return None
    from shapely.geometry import LineString
    fronts = [LineString(s) for k, s in enumerate(core_lot.sides(lot["outline"]))
              if lot["roles"].get(k) == core_lot.FRONT]
    if not fronts or min(f.distance(out) for f in fronts) > 0.05:
        return None
    lo, _hi = obj.mesh.bounds()
    return round(float(lo[2]) - ground_level(ctx), 3)


def backyard(ctx):
    """The free part of the lot behind the building (m²), as wide as the lot (RGEU art. 62.º): what lies past the
    building's rearmost point, towards the back."""
    lot = lot_info(ctx)
    base = footprint(ctx)
    if lot is None or lot["polygon"] is None or base is None:
        return None
    backs = [k for k, r in lot["roles"].items() if r == core_lot.BACK]
    if not backs:
        return None
    s = core_lot.sides(lot["outline"])
    facing_back = sum((core_lot.outward(*s[k]) * core_lot.side_length(*s[k]) for k in backs), np.zeros(2))
    if np.linalg.norm(facing_back) < 1e-9:
        return None
    u = facing_back / np.linalg.norm(facing_back)
    far = max(float(np.dot(u, c)) for c in np.asarray(base.convex_hull.exterior.coords))
    from shapely.geometry import Polygon
    side = np.array((-u[1], u[0]))
    big = 1e4
    o = u * far
    half = Polygon([tuple(o - side * big), tuple(o + side * big), tuple(o + side * big + u * big),
                    tuple(o - side * big + u * big)])
    return round(float(lot["polygon"].intersection(half).area), 2)


def across_street(ctx, guid):
    """(CTE art. 22.º n.º 1) How far a wall facing the street is from the façade across it — when that one is in the
    model (a neighbour drawn as walls); None otherwise."""
    face = wall_face(ctx, guid)
    if face is None:
        return None
    ahead = boundary_ahead(ctx, *face)
    if ahead is None or ahead[1] != core_lot.FRONT:
        return None
    found = facing(ctx, face[0], face[1], face[2], (guid,))
    return found[0] if found is not None and found[0] > ahead[0] else None


WALL = {
    "afastamento_fachada_via": lambda ctx, s: across_street(ctx, s.id),
    "altura_fachada": lambda ctx, s: (lambda f: height_at(ctx, f[0], f[1]) if f else None)(wall_face(ctx, s.id)),
    "afastamento_fachada_oposta": lambda ctx, s: opposite(ctx, s.id),
}
WINDOW = {
    "altura_fachada": lambda ctx, s: (lambda f: height_at(ctx, f[0], f[1]) if f else None)(window_face(ctx, s.id)),
    "afastamento_estrema": lambda ctx, s: neighbour_setback(ctx, s.id),
    "afastamento_fachada_fronteira": lambda ctx, s: (lambda f: (facing(
        ctx, f[0], f[1], f[2], (s.id, _host(ctx, s.id))) or (None,))[0] if f else None)(window_face(ctx, s.id)),
}
ROOM = {"altura_patio": lambda ctx, s: patio_height(ctx, s.id)}
SLAB = {"altura_sobre_via": lambda ctx, s: over_street(ctx, s.id)}


MEASURES = {
    "area_logradouro": lambda ctx, s: backyard(ctx),
    "area_lote": lambda ctx, s: (lambda lot: round(lot["area"], 2) if lot else None)(lot_info(ctx)),
    "area_implantacao": lambda ctx, s: implantation(ctx),
    "area_construcao": lambda ctx, s: floor_area(ctx),
    "indice_ocupacao": lambda ctx, s: _index(implantation(ctx), lot_info(ctx)),
    "indice_utilizacao": lambda ctx, s: _index(floor_area(ctx), lot_info(ctx)),
    "pisos_acima_solo": lambda ctx, s: float(len(storeys_built(ctx))) if footprint(ctx) is not None else None,
    "pisos_abaixo_solo": lambda ctx, s: float(len(storeys_built(ctx, above=False))),
    "cercea": lambda ctx, s: facade_height(ctx),
    "altura_edificio": lambda ctx, s: building_height(ctx),
    "afastamento_frontal": lambda ctx, s: setback(ctx, core_lot.FRONT),
    "afastamento_lateral": lambda ctx, s: setback(ctx, core_lot.SIDE),
    "afastamento_posterior": lambda ctx, s: setback(ctx, core_lot.BACK),
    "fora_do_lote": lambda ctx, s: outside_lot(ctx),
    "impermeabilizacao": lambda ctx, s: sealed(ctx),
}


def summary(ctx):
    """{measure: value} of the lot and the building on it (the Regulamentos dialog shows them)."""
    subject = ms.Subject("lot", "lot", "")
    return {name: ms.measure(ctx, subject, name) for name in MEASURES}
