"""(0.423) Town planning: the lot (ifc/lot.py) and the building on it, as the town plans and the codes measure them —
the footprint («área de implantação»), the gross floor area («área de construção»), the indices, the storeys above
and below the ground, the façade's height («cércea»), the setbacks from the lot's sides («afastamentos»), what is
built outside the lot, how much of it is sealed («impermeabilização»).

What is built on a storey: its walls and columns and what they enclose (core/rooms.regions), less its exterior rooms
(a patio enclosed by walls counts as built until a room says it is outside). The ground: the storey nearest the level
0 — those under it are below the ground («caves»). Measured only from the walls and columns this program made
(ifc/spaces.storey_obstacles)."""

from ..core import lot as core_lot
from . import measures as ms

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
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
        from ..core import rooms as core_rooms
        try:
            obstacles = ctx.doc.ifc.storey_obstacles(storey)
        except Exception:                               # noqa: BLE001
            obstacles = []
        walls = [Polygon(p).buffer(0) for p in obstacles if len(p) >= 3]
        walls = [p for p in walls if not p.is_empty]
        if not walls:
            return None
        shape = unary_union(walls + core_rooms.regions(obstacles))
        outside = [ms._poly(r) for r in ctx.facts.rooms.values() if r.storey == storey and r.external]
        if outside:
            shape = shape.difference(unary_union(outside).buffer(0.01))
        return None if shape.is_empty else shape
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


MEASURES = {
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
