"""(0.431) The model's own warnings (Aprender com o Hestia, passo 5 — and the commonest of Revit's): what is wrong with
the model itself, not with a law — walls drawn over each other, the same element twice in the same place, a room no
longer closed by its walls. Checked by the Verifier like any rule (the pack «Modelo», regulamentos/_geral/modelo.json,
always on): in the footer's count, the panel (Ir para, Exceção… with its note), the verification sheet."""

import numpy as np

from . import measures as ms
from . import uses

WALLS = ("IfcWall", "IfcWallStandardCase")
TWINS = ("IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcColumn", "IfcBeam", "IfcDoor", "IfcWindow", "IfcRoof",
         "IfcStair", "IfcRailing", "IfcCovering", "IfcFurniture", "IfcSanitaryTerminal", "IfcMember", "IfcPlate",
         "IfcFooting", "IfcBuildingElementProxy")
OVERLAP_M2 = 0.10           # m² two walls share in plan: more than a corner's (two 20 cm walls meeting: 0,04)
TWIN_TOL = 0.01             # m: two boxes this close at every corner: the same element twice


def _walls(ctx, storey):
    """([wall], their outlines in plan (an array), an STRtree of them) of a storey — made once per check."""
    def make():
        import shapely
        items, hulls = [], []
        for obj, lo, hi in ctx.near(-1e12, -1e12, 1e12, 1e12, WALLS, storey):
            hull = ctx.hull(obj)
            if hull.geom_type == "Polygon":
                items.append((obj, float(lo[2]), float(hi[2])))
                hulls.append(hull)
        if not hulls:
            return [], None, None
        array = np.empty(len(hulls), dtype=object)
        array[:] = hulls
        return items, array, shapely.STRtree(array)
    return ctx.keep(("model_walls", storey), make)


def overlaps(ctx, guid):
    """How much (m², in plan) of a wall lies over other walls of its storey at the same heights — counting only what
    is more than a corner's share."""
    import shapely
    obj = ctx.doc.get(guid)
    if obj is None or getattr(obj, "mesh", None) is None:
        return None
    items, hulls, tree = _walls(ctx, obj.storey)
    if tree is None:
        return 0.0
    hull = ctx.hull(obj)
    if hull.geom_type != "Polygon":
        return None
    lo, hi = obj.mesh.bounds()
    total = 0.0
    found = tree.query(hull, predicate="intersects")
    if len(found):
        shared = shapely.area(shapely.intersection(hulls[found], hull))
        for k, area in zip(found, shared):
            other, bottom, top = items[int(k)]
            if other.id == guid or area <= OVERLAP_M2:
                continue
            if top <= float(lo[2]) + 0.01 or bottom >= float(hi[2]) - 0.01:
                continue                                # (one over the other in height: not the same place)
            total += float(area)
    return round(total, 3)


def twins(ctx):
    """{GlobalId: its twin's GlobalId}: elements with another of their class in the same place (their boxes within
    1 cm at every corner) — made once per check."""
    def make():
        found, seen = {}, {}
        for o, lo, hi in ctx.boxes():
            if o.ifc_class not in TWINS:
                continue
            mark = (o.ifc_class, tuple(np.round(np.concatenate((lo, hi)) / TWIN_TOL).astype(np.int64)))
            if mark in seen:
                first = seen[mark]
                found[o.id] = first
                found.setdefault(first, o.id)
            else:
                seen[mark] = o.id
        return found
    return ctx.keep("twins", make)


def _region_of(ctx, room):
    """The index of the region (of its storey's walls and room separators) a room's middle is in, or None."""
    def regions():
        from shapely.prepared import prep
        from ..core import rooms as core_rooms
        try:
            found = core_rooms.regions(ctx.doc.ifc.storey_obstacles(room.storey, separators=True))
        except Exception:                               # noqa: BLE001
            found = []
        return [(prep(r), r.bounds) for r in found]

    def make():
        found = ctx.keep(("closed_regions", room.storey), regions)
        here = ms._poly(room).representative_point()
        for k, (region, (x0, y0, x1, y1)) in enumerate(found):
            if x0 <= here.x <= x1 and y0 <= here.y <= y1 and region.contains(here):
                return k
        return None
    return ctx.keep(("region_of", room.guid), make)


def enclosed(ctx, room_id):
    """1 when a room's middle is in a region its storey's walls (and room separators) close, else 0 — an outer wall
    taken away leaves it open."""
    room = ctx.facts.rooms.get(room_id)
    if room is None:
        return None
    return 1.0 if _region_of(ctx, room) is not None else 0.0


def sharing(ctx, room_id):
    """How many other rooms (inside ones) are in the same closed region as this one — a wall between them taken away
    (Revit's «multiple rooms in the same enclosed region»)."""
    room = ctx.facts.rooms.get(room_id)
    if room is None:
        return None
    mine = _region_of(ctx, room)
    if mine is None:
        return 0.0
    return float(sum(1 for r in ctx.facts.rooms.values() if r.guid != room_id and r.storey == room.storey
                     and not outside(r) and _region_of(ctx, r) == mine))


def conflicting(ctx, room_id):
    """(0.475) How many rooms this one opens into (a door between them) that its use should not — the rules of
    conflicting zones of the project's type of building (model/program_rules): a bathroom straight into the kitchen…"""
    def make():
        from ..model import program_rules
        try:
            found = program_rules.conflicts(ctx.doc, ctx.facts)
        except Exception:                               # noqa: BLE001 (the IFC still being read)
            found = []
        out = {}
        for a, b, _door, _rule in found:
            out[a] = out.get(a, 0) + 1
            out[b] = out.get(b, 0) + 1
        return out
    if room_id not in ctx.facts.rooms:
        return None
    return float(ctx.keep("conflicting_zones", make).get(room_id, 0))


def outside(room):
    """A room that is outside by what it is (a balcony, a courtyard) or as marked: not closed by walls."""
    return bool(room.external) or uses.is_exterior(room.use)


def subjects(ctx, building_use):
    """The «element» subjects: only the elements that have a twin (the others have nothing to say)."""
    from ..i18n import t
    out = []
    for guid in sorted(twins(ctx)):
        obj = ctx.doc.get(guid)
        if obj is None:
            continue
        out.append(ms.Subject("element", guid, obj.name or t("verify.kind.element"), [guid], obj.storey,
                              props={"building_use": building_use}))
    return out


WALL = {"sobreposicao": lambda ctx, s: overlaps(ctx, s.id)}
ROOM = {"fechado": lambda ctx, s: enclosed(ctx, s.id), "partilha_regiao": lambda ctx, s: sharing(ctx, s.id),
        "zona_conflitante": lambda ctx, s: conflicting(ctx, s.id)}                  # (0.475)
ELEMENT = {"duplicado": lambda ctx, s: 1.0 if s.id in twins(ctx) else 0.0}
