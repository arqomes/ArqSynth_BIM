"""BIM actions on the document: Classify (sketch volume -> IFC element), direct
walls and slabs, doors/windows, and Delete. Each is one undo step."""

import copy

import numpy as np

from ..core.classify import box_from_axis, box_from_rect, upright_box
from ..core.mesh import PolyMesh
from ..core.walls import can_join, horizontal_dir, is_square, joint, offset_axis
from ..i18n import lang, t
from ..ifc import catalog
from .document import (GRID_DEFAULTS, STOREY_CHANGED, GridAxis, GridChange, IfcCommand, RemoveObjects,
                       ReplaceObjects, SketchObject)

WALL_HEIGHT = 2.80
MIN_WALL = 0.10            # m: a wall a proposal lowers stays at least this tall (0.98)

_IFC_CLASS = {"wall": "IfcWall", "slab": "IfcSlab", "column": "IfcColumn", "beam": "IfcBeam", "footing": "IfcFooting",
              "pipe": "IfcPipeSegment", "duct": "IfcDuctSegment", "conduit": "IfcCableCarrierSegment"}


class ClassifyResult:
    def __init__(self):
        self.guids = []        # created elements
        self.refused = []      # sketch objects that are not plain upright boxes
        self.adjusted = []     # (sketch name, volume size, type size): the type decided the size


def _voids_fit(box, kind):
    """Holes of a sketch box can become IFC openings: across a wall, or vertical in a slab."""
    if not box.voids:
        return True
    if kind == "wall":
        axis = box.y_dir
    elif kind == "slab":
        axis = np.array((0.0, 0.0, 1.0))
    else:
        return False
    return all(abs(abs(np.dot(vec / np.linalg.norm(vec), axis)) - 1) < 1e-6 for _pts, vec in box.voids)


def classify(doc, obj_ids, spec):
    """Turn the selected sketch volumes into parametric IFC elements of type `spec`.
    One undo step for the whole selection."""
    res = ClassifyResult()
    items = []
    for obj_id in obj_ids:
        obj = doc.get(obj_id)
        if obj is None or obj.is_bim:
            continue
        box = upright_box(obj)
        if box is None or not _voids_fit(box, spec.kind):
            res.refused.append(obj)
            continue
        items.append((obj, box))
        if spec.kind == "wall" and abs(box.width - spec.thickness) > 1e-4:
            res.adjusted.append((obj.name, box.width, spec.thickness))
        elif spec.kind == "slab" and abs(box.height - spec.thickness) > 1e-4:
            res.adjusted.append((obj.name, box.height, spec.thickness))
        elif spec.kind == "column" and (abs(box.length - max(spec.profile)) > 1e-4
                                        or abs(box.width - min(spec.profile)) > 1e-4):
            res.adjusted.append((obj.name, (box.length, box.width), spec.profile))
        elif spec.kind == "beam" and (abs(box.width - spec.profile[0]) > 1e-4 or abs(box.height - spec.profile[1]) > 1e-4):
            res.adjusted.append((obj.name, (box.width, box.height), spec.profile))
        elif spec.kind == "footing" and abs(box.height - spec.thickness) > 1e-4:
            res.adjusted.append((obj.name, box.height, spec.thickness))
    if not items:
        return res

    language = lang()
    prefix = t("elem." + spec.kind)

    def action(ifc):
        start = ifc.count(_IFC_CLASS[spec.kind])
        return [ifc.create_from_box(spec, box, "{} {}".format(prefix, start + k + 1), language).GlobalId
                for k, (_obj, box) in enumerate(items)]

    cmd = doc.execute(IfcCommand(t("cmd.classify"), action, remove_sketches=[o for o, _ in items]))
    res.guids = cmd.result
    return res


class _WallAxes:
    """(0.225) The walls' axes kept with a document: those it says changed (its notices, as the view hears them)
    worked out again, all of them when a storey changed or the file is another."""

    def __init__(self, doc):
        self.model = id(doc.ifc)
        self.axes = {}                  # GlobalId -> (guid, start, end, thickness), or None: not a wall of ours
        doc.subscribe(self._changed)

    def _changed(self, changed, removed):
        if STOREY_CHANGED in changed:
            self.axes.clear()
            return
        for g in list(changed) + list(removed):
            self.axes.pop(g, None)


def wall_axes(doc):
    """[(guid, axis start, axis end, thickness)] of the walls made by ArqBIM
    (the ones whose corners can be joined) — (0.225) kept with the document, each worked out again when it changes
    (selecting a wall asked for them all each time, for its temporary dimensions)."""
    kept = getattr(doc, "_wall_axes", None)
    if not isinstance(kept, _WallAxes):
        kept = doc._wall_axes = _WallAxes(doc)
    if kept.model != id(doc.ifc):
        kept.axes.clear()
        kept.model = id(doc.ifc)
    out = []
    with doc.ifc.remembering():                         # (the storeys' placements, the kinds: once for all)
        for obj in doc.objects.values():
            if not obj.is_bim or obj.ifc_class not in ("IfcWall", "IfcWallStandardCase"):
                continue
            if obj.id not in kept.axes:
                kept.axes[obj.id] = (obj.id, *doc.ifc.wall_axis(obj.id)) if doc.ifc.kind_of(obj.id) == "wall" \
                    else None
            if kept.axes[obj.id] is not None:
                out.append(kept.axes[obj.id])
    return out


def add_wall(doc, start, end, spec, height=WALL_HEIGHT, prev=None, first=None, start_join=None, end_join=None,
             storey=None):
    """Wall along the axis start -> end (base at start's level), centred on the axis.

    start_join / end_join: (guid, "start" | "end" | "mid", direction) of an
    existing wall this one starts / ends on (core.walls.find_joint), for clean
    corners and T junctions. prev / first: (guid, direction) of the previous
    wall of a chain and of its first wall (when this wall closes the chain),
    i.e. a join at that wall's end / start. storey: GlobalId of the storey the
    wall goes in (default: the one it stands on).
    Returns the new wall's GlobalId.
    """
    language, prefix = lang(), t("elem.wall")
    cmd = IfcCommand(t("cmd.wall"), None)
    cmd.action = lambda ifc: _make_wall(ifc, start, end, spec, height, prev, first, start_join, end_join, storey,
                                        language, prefix, cmd.changed)
    return doc.execute(cmd).result


def _make_wall(ifc, start, end, spec, height, prev, first, start_join, end_join, storey, language, prefix,
               changed):
    """add_wall's work, inside the IFC transaction (a chain of walls is made in one step, 0.102): the walls it
    is joined to are trimmed / extended to the corner (their GlobalIds added to `changed`)."""
    if prev and start_join is None:
        start_join = (prev[0], "end", prev[1])
    if first and end_join is None:
        end_join = (first[0], "start", first[1])
    d = horizontal_dir(start, end)
    t_new = spec.thickness
    ends = {"start": np.asarray(start, dtype=float), "end": np.asarray(end, dtype=float)}
    cuts = {}                             # the new wall's end -> cut angle
    others = []                           # (guid, its end, new point, cut) of the walls joined to
    links = []                            # (other guid, its end, the new wall's end): joints to record
    for join, my_end in ((start_join, "start"), (end_join, "end")):
        if join is None or not can_join(d, join[2]):
            continue
        guid, where = join[0], join[1]
        other_end = "path" if where == "mid" else where
        s, e, t_other = ifc.wall_axis(guid)
        # right angle: the other wall runs through the corner, the new one stops at its face;
        # other angles: mitre; T junction: the new wall stops on the other's face
        result = joint((s, e), t_other, other_end, (ends["start"], ends["end"]), t_new, my_end)
        if result is None:
            continue                                                # too sharp: left as drawn
        ends[my_end], cuts[my_end] = result["butt"]
        if result["through"] is not None:
            others.append((guid, other_end, *result["through"]))
        links.append((guid, other_end, my_end))
    box = box_from_axis(ends["start"], ends["end"], t_new, height)
    new_cuts = {end_: cut for end_, cut in cuts.items() if not is_square(cut, end_ == "start")}
    for guid, other_end, point, cut in others:
        ifc.set_wall_end(guid, other_end, point, cut)
        if guid not in changed:
            changed.append(guid)
    name = "{} {}".format(prefix, ifc.count("IfcWall") + 1)
    wall = ifc.create_from_box(spec, box, name, language, storey=storey)
    if new_cuts:
        ifc.set_wall_cuts(wall.GlobalId, start=new_cuts.get("start"), end=new_cuts.get("end"))
    for guid, other_end, my_end in links:
        ifc.connect_walls(guid, other_end, wall.GlobalId, my_end)   # remembered: they stay joined
    for guid in ifc.join_ends(wall.GlobalId):          # (0.189) an end on a curved wall's: a corner with it
        if guid not in changed:
            changed.append(guid)
    return wall.GlobalId


def split_wall(doc, guid, s, gap=0.0):
    """A wall split `s` m from its start (0.104): two walls, each with its doors and windows; in a group, every
    copy is split the same. (0.300) gap: a gap that wide centred on the point, the parts not joined. One undo step.
    Returns the new wall's GlobalId."""
    gs = _and_copies(doc, guid)
    if gap > 1e-9:
        made = _edit(doc, lambda ifc: [ifc.split_wall_gap(g, s, gap) for g in gs], gs, "cmd.split_gap")
    else:
        made = _edit(doc, lambda ifc: [ifc.split_wall(g, s) for g in gs], gs, "cmd.split_wall")
    return made[0]


def corner_walls(doc, a, keep_a, b, keep_b):
    """Two walls trimmed / extended to the corner where their axes meet (0.104), each keeping the side of the
    point clicked on it, joined there. One undo step."""
    _edit(doc, lambda ifc: ifc.corner_walls(a, keep_a, b, keep_b), [a, b], "cmd.corner_walls")


def set_wall_corner(doc, guid, end, style):
    """(0.301, Revit's Wall Joins) The right-angle corner at a wall's "start" / "end" made "butt" (this wall running
    through, the other stopped at its face) or "mitre". One undo step. Returns the corner's other wall."""
    found = doc.ifc.corner_joint(guid, end)
    others = [g for g in (found[1], found[3]) if g != guid] if found else []
    return _edit(doc, lambda ifc: ifc.set_corner(guid, end, style), [guid] + others, "cmd.wall_joins")


def trim_extend_wall(doc, guid, boundary, keep):
    """(0.300) A wall trimmed / extended to a boundary wall's axis line, keeping the side of the point `keep` (plan)
    clicked on it; joined to the boundary where it meets it (a T, or a corner at its end). One undo step. Returns
    True when joined."""
    return _edit(doc, lambda ifc: ifc.trim_extend_wall(guid, boundary, keep), [guid, boundary], "cmd.trim_extend")


def _mirrored_sketch(doc, obj, mat, copy):
    """A sketch reflected: its points through the reflection (its matrix taken in), its faces turned round so
    that they still look out. The same sketch moved (its id kept), or a new one (copy)."""
    from ..core.mesh import PolyMesh
    m = mat @ obj.matrix
    verts = [(m @ np.append(v, 1.0))[:3] for v in obj.mesh.verts]
    faces = [list(reversed(f)) for f in obj.mesh.faces]
    voids = [([(m @ np.append(p, 1.0))[:3] for p in pts], m[:3, :3] @ vec) for pts, vec in obj.mesh.voids]
    mesh = PolyMesh(verts, faces, obj.mesh.hidden, voids, getattr(obj.mesh, "lines", ()), obj.mesh.painted())
    if copy:
        name = t("obj.name", n=doc.next_number()) if mesh.faces else t("obj.lines", n=doc.next_number())
        return SketchObject(name, np.eye(4), mesh)
    new = obj.copy()
    new.matrix, new.mesh = np.eye(4), mesh
    return new


def _with_finishes(doc, guids):
    """Elements copied (0.119): a wall's finishes go with it — those picked without their wall are left out."""
    out = [g for g in guids if doc.ifc.kind_of(g) != "cladding"]
    return out + [c for c in doc.ifc.claddings_of(out) if c not in out]


def mirror_objects(doc, obj_ids, a, b, copy=False):
    """Selected sketches and elements reflected about the vertical plane through the plan line a -> b (0.108):
    moved there, or (copy) mirror-image copies made there — the corners between the walls copied are made again
    between their copies. A door / window goes with its wall. One undo step. Returns (the ids made or moved,
    the elements left out: those that cannot be mirrored)."""
    from ..ifc.mirror import reflection
    mat = reflection(a, b)
    objs = [doc.get(i) for i in obj_ids if doc.get(i) is not None]
    sketches = [o for o in objs if not o.is_bim]
    elements = [o.id for o in objs if o.is_bim and not is_filling(doc, o.id) and doc.ifc.kind_of(o.id) != "space"]
    left_out = [g for g in elements if not doc.ifc.mirrorable(g)]
    elements = [g for g in elements if g not in left_out]
    # the footings and piles under them go with them (as with Move, 0.93)
    elements += [f for fs in doc.ifc.supports_of(elements).values() for f in fs if f not in elements]
    # (a wall's finishes: copied with it, else made again on it after, 0.119)
    elements = _with_finishes(doc, elements) if copy else [g for g in elements if doc.ifc.kind_of(g) != "cladding"]
    mirrored = [_mirrored_sketch(doc, o, mat, copy) for o in sketches]
    if not elements:
        if mirrored:
            if copy:
                doc.execute(ReplaceObjects([], mirrored, t("cmd.mirror")))
            else:
                doc.execute(ReplaceObjects(sketches, mirrored, t("cmd.mirror")))
        return [o.id for o in mirrored], left_out
    language = lang()
    joints = {}                                         # (the walls' joints, to be made again between copies)
    for g in elements:
        for rel, through, through_end, butt, butt_end in doc.ifc.wall_joints(g):
            joints[rel.id()] = (through, through_end, butt, butt_end)
    changed = [] if copy else sorted(set(elements) | {f for g in elements for f in _fillings(doc, g)}
                                     | set(doc.ifc.joined_walls(elements)))
    inside = set(elements)

    def action(ifc):
        swap = {"start": "end", "end": "start", "path": "path"}
        if copy:
            ifc.copy_map = {}
            made = {g: ifc.copy_element(g).GlobalId for g in elements}
            for g in made.values():
                ifc.mirror_element(g, mat, language)
            for through, through_end, butt, butt_end in joints.values():
                if through in made and butt in made:
                    ifc.connect_walls(made[through], swap[through_end], made[butt], swap[butt_end])
            ifc.remap_ties(ifc.copy_map)                # (a beam copied with its columns: between the copies)
            return list(made.values())
        for rel_id, (through, _te, butt, _be) in joints.items():   # joints with walls staying behind: let go
            if not (through in inside and butt in inside):
                ifc.file.remove(ifc.file.by_id(rel_id))
        for g in elements:
            ifc.mirror_element(g, mat, language)
        return list(elements)

    remove = [] if copy else sketches
    cmd = doc.execute(IfcCommand(t("cmd.mirror"), action, remove_sketches=remove, add_sketches=mirrored,
                                 changed=changed))
    return [o.id for o in mirrored] + cmd.result, left_out


def add_roof(doc, outline, spec, form="hip", slope=30.0, overhang=0.5, eave=None, storey=None):
    """A roof (0.111) over `outline` (the walls' outer line, plan): flat, shed, gable or hip at `slope` degrees,
    its eaves `overhang` out, its top over the walls' line at `eave` (default: resting on the walls under it —
    0.275: its underside on their inner top edge —, else the storey's level + 2,80). One undo step. Returns its
    GlobalId."""
    storey = storey or doc.active_storey
    if eave is None:
        eave = roof_seated(doc, outline, spec, 0.0 if form == "flat" else slope, storey)
    language, prefix = lang(), t("elem.roof")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcRoof") + 1)
        return ifc.add_roof(spec, outline, form, slope, overhang, eave, name, language, storey=storey).GlobalId

    return doc.execute(IfcCommand(t("cmd.roof"), action)).result


def _seated_block(doc, block, thickness, storey, base=None):
    """(0.275) A block resting on the walls under it: (the level its eaves are over, the block with each water's
    eave so that its underside sits on their inner top edge — core/roofs.seat by its own slope); base: the roof's
    level its eaves are measured from (None: the walls' top). No wall under it: as it was, at the storey's + 2,80."""
    from ..core import roof_blocks as core_blocks
    from ..core import roofs as core_roofs
    top, wall = roof_bearing(doc, core_blocks.rect(block), storey)
    if top is None:
        level = roof_eave(doc, core_blocks.rect(block), storey)
        rise = 0.0 if base is None else level - base
        return (level if base is None else base), core_blocks.replace(block, eave=(float(rise),) * 4)
    rise = 0.0 if base is None else top - base
    eaves = tuple(float(rise + core_roofs.seat(s if w else 0.0, thickness, wall))
                  for s, w in zip(block.slope, block.water))
    return (top if base is None else base), core_blocks.replace(block, eave=eaves)


def add_block_roof(doc, block, spec, storey=None, on_walls=True):
    """(0.262) A roof by blocks, its first block `block` (core/roof_blocks.Block, in the plan): its level the top of
    the walls under the block (else the storey's + 2,80) — (0.275) each water resting on them (not `on_walls`: its
    own eaves kept). One undo step. Returns its GlobalId."""
    from ..core import roof_blocks as core_blocks
    storey = storey or doc.active_storey
    if on_walls:
        eave, block = _seated_block(doc, block, spec.thickness, storey)
    else:
        eave = roof_eave(doc, core_blocks.rect(block), storey)
    language, prefix = lang(), t("elem.roof")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcRoof") + 1)
        return ifc.add_block_roof(spec, block, eave, name, language, storey=storey).GlobalId

    return doc.execute(IfcCommand(t("cmd.roof"), action)).result


def add_roof_block(doc, roof, block, storey=None, on_walls=True):
    """(0.262) One more block in a roof by blocks — its eaves on the walls under it (their top over the roof's
    level; 0.275: each water resting on them); not `on_walls`: its own eaves kept. One undo step."""
    if on_walls:
        p = doc.ifc.roof_params(roof)
        _level, block = _seated_block(doc, block, p["thickness"], storey or doc.active_storey, base=p["eave"])
    _edit(doc, lambda ifc: ifc.add_roof_block(roof, block), [roof], "cmd.roof_block")


def set_roof_carpentry(doc, roof, settings=None):
    """(0.276) A pitched roof's carpentry made (again): wall plates, ridge board, hip and valley rafters, purlins,
    rafters and battens under its cover, the cover raised onto them. One undo step. Returns the assembly's
    GlobalId."""
    language = lang()
    return _edit(doc, lambda ifc: ifc.set_roof_carpentry(roof, settings, language).GlobalId, [roof],
                 "cmd.carpentry")


def remove_roof_carpentry(doc, roof):
    """(0.276) A roof's carpentry taken away, its cover back on the walls. One undo step."""
    return _edit(doc, lambda ifc: ifc.remove_roof_carpentry(roof), [roof], "cmd.carpentry_off")


def set_roof_tiles(doc, roof, key=None, stagger=None):
    """(0.279) A pitched roof's tiles laid (again) on its cover: key, the tile (None: the one it has, else
    Marselha); stagger, every other row half a tile across (None: as it was / as the tile is laid). One undo step.
    Returns the tiles' GlobalId (an IfcCovering)."""
    language = lang()
    return _edit(doc, lambda ifc: ifc.set_roof_tiles(roof, key, stagger, language).GlobalId, [], "cmd.tiles",
                 plan=False)


def tile_shape(doc, instance):
    """(0.281) A component's shape in its own frame (metres), from one of its instances: (vertices, triangles), or
    None."""
    obj = doc.get(instance)
    e = doc.ifc.by_guid(instance)
    if obj is None or e is None or not len(obj.mesh.faces):
        return None
    m = doc.ifc._placement_si(e)
    return (np.asarray(obj.mesh.verts, dtype=float) - m[:3, 3]) @ m[:3, :3], np.asarray(obj.mesh.faces,
                                                                                         dtype=np.int64)


def register_tile(doc, instance, name, cover_width, gauge, weight, stagger=True):
    """(0.281) A component (one of its instances given) registered as a tile of the user's own, as the add-on's
    «Registar telha»: its shape and its maker's data (cover width, gauge, weight). One undo step. Returns its key."""
    verts, tris = tile_shape(doc, instance)
    language = lang()
    return doc.execute(IfcCommand(t("cmd.register_tile"), lambda ifc: ifc.register_tile(
        verts, tris, name, cover_width, gauge, weight, stagger, language))).result


def remove_roof_tiles(doc, roof):
    """(0.279) A roof's tiles taken away. One undo step."""
    return _edit(doc, lambda ifc: ifc.remove_roof_tiles(roof), [], "cmd.tiles_off", plan=False)


def set_roof_blocks(doc, roof, blocks, world=False):
    """(0.262) A roof by blocks' blocks (in its own frame; `world`: in the plan, 0.263) changed. One undo step."""
    _edit(doc, lambda ifc: (ifc.set_roof_blocks_world if world else ifc.set_roof_blocks)(roof, blocks), [roof],
          "cmd.roof_block")


def fit_block_to_walls(doc, block, storey=None, only=None):
    """(0.262) A block drawn over the building (its middle within the walls round it, in the plan): each side of it
    lying on a straight wall along it — on its axis, a face or between — taken out to that wall's outer face, the
    walls' line its eave is over (as the Roof's outline by the walls): no wall stands out of its overhang. Its other
    sides as drawn; a block outside the walls (a porch against them) as drawn. `only`: those sides (0..3: N, E, S,
    W) alone — (0.264) the one a grip moved."""
    from shapely.geometry import Point, Polygon
    import shapely
    from ..core import roof_blocks as core_blocks
    storey = storey or doc.active_storey
    a = np.radians(block.angle)
    ex, ey = np.array((np.cos(a), np.sin(a))), np.array((-np.sin(a), np.cos(a)))
    c = np.array((block.cx, block.cy))
    # N, E, S, W: the side's outward normal, along it, its distance from the middle, its half length
    sides = [[ey, ex, block.depth / 2, block.width / 2], [ex, ey, block.width / 2, block.depth / 2],
             [-ey, ex, block.depth / 2, block.width / 2], [-ex, ey, block.width / 2, block.depth / 2]]
    reach = [s[2] for s in sides]
    walls = []
    for g in doc.ifc.storey_elements(storey) if storey else ():
        if doc.ifc.kind_of(g) != "wall":
            continue
        p, q, thickness = doc.ifc.wall_axis(g)
        p, q = np.asarray(p[:2], dtype=float), np.asarray(q[:2], dtype=float)
        length = float(np.linalg.norm(q - p))
        if length > 1e-6:
            walls.append((p, q, float(thickness), (q - p) / length))
    # (the walls' footprints, a half thickness longer at each end to close their corners: the rooms they ring)
    bodies = shapely.union_all([Polygon([tuple(p - u * h + nu * h), tuple(q + u * h + nu * h),
                                         tuple(q + u * h - nu * h), tuple(p - u * h - nu * h)])
                                for p, q, th, u in walls for h, nu in [(th / 2, np.array((-u[1], u[0])))]]) \
        if walls else None
    rooms = [Polygon(ring) for poly in core_blocks.polygons(bodies) for ring in poly.interiors] if walls else []
    middle = Point(float(c[0]), float(c[1]))
    if not any(room.contains(middle) for room in rooms):
        return block
    for p, q, thickness, u in walls:
        for k, (normal, along, half, half_len) in enumerate(sides):
            if only is not None and k not in only or abs(float(u @ normal)) > 0.02:     # (about 1°) not along it
                continue
            off = float((p - c) @ normal)
            if abs(off - half) > thickness / 2 + 0.02:
                continue
            ta, tb = sorted((float((p - c) @ along), float((q - c) @ along)))
            if min(tb, half_len) - max(ta, -half_len) < 0.10:       # (only touching its end)
                continue
            reach[k] = max(reach[k], off + thickness / 2)
    n, e, s, w = reach
    if all(abs(r - side[2]) < 1e-9 for r, side in zip(reach, sides)):
        return block
    mid = c + ex * (e - w) / 2 + ey * (n - s) / 2
    return core_blocks.replace(block, cx=float(mid[0]), cy=float(mid[1]), width=float(e + w), depth=float(n + s))


CEILING_HEIGHT = 2.60       # m over the storey (0.118)


def _coverings(ifc, predefined):
    return sum(1 for e in ifc.file.by_type("IfcCovering") if e.PredefinedType == predefined)


def add_ceiling(doc, outline, height=CEILING_HEIGHT, style="continuous", holes=(), storey=None, gap=0.0,
                bulkhead=None, loops=None):
    """A ceiling (0.118) over `outline` (plan, with holes), its underside `height` over the storey; (0.119) a
    shadow gap `gap` along its edge, a bulkhead (width, drop) round it; (0.456) `loops`: its outline as drawn, its
    sides arcs or curves (core/outline_loops). One undo step. Returns its GlobalId."""
    storey = storey or doc.active_storey
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    language, prefix = lang(), t("elem.ceiling")

    def action(ifc):
        name = "{} {}".format(prefix, _coverings(ifc, "CEILING") + 1)
        ceiling = ifc.add_ceiling(outline, level + float(height), name, style, holes, language, storey=storey)
        if loops:
            ifc.set_covering_outline(ceiling.GlobalId, loops)
        if gap or bulkhead:
            ifc.set_ceiling(ceiling.GlobalId, gap=gap or None, bulkhead=bulkhead)
        return ceiling.GlobalId

    return doc.execute(IfcCommand(t("cmd.ceiling"), action)).result


def add_flooring(doc, outline, finish="ceramico", holes=(), storey=None, loops=None):
    """(0.374, the study's «Piso») A floor finish over `outline` (plan, with holes) on the storey's level: an
    IfcCovering FLOORING of that finish; (0.456) `loops`: its outline as drawn (arcs, curves). One undo step. Returns
    its GlobalId."""
    storey = storey or doc.active_storey
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    language, prefix = lang(), t("elem.flooring")

    def action(ifc):
        name = "{} {}".format(prefix, _coverings(ifc, "FLOORING") + 1)
        guid = ifc.add_flooring(outline, level, name, finish, holes, language, storey=storey).GlobalId
        if loops:
            ifc.set_covering_outline(guid, loops)
        return guid

    return doc.execute(IfcCommand(t("cmd.flooring"), action)).result


def set_ceiling(doc, guid, style=None, height=None, gap=None, bulkhead=None):
    """A ceiling's style, its height over its storey (0.118), its shadow gap or its bulkhead (width, drop; 0.119).
    One undo step."""
    z = None
    if height is not None:
        storey = doc.ifc.storey_of(guid)
        z = next((lv for g, _n, lv in doc.ifc.storeys() if g == storey), 0.0) + float(height)
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.set_ceiling(g, style, z, gap, bulkhead) for g in gs], gs, "cmd.ceiling_edit")


CEILING_DROP = 0.30          # (0.549) m: a false ceiling made under a slab hangs this far under it


def perforate_ceiling(doc, guid, pattern):
    """(0.549) A ceiling's holes — a Visual Graph operator's (ifc.set_ceiling_perforation: free, free_repeat,
    sheet_w, sheet_h, margin, operator; free «»: none again). In a group, every copy. One undo step."""
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.set_ceiling_perforation(g, pattern) for g in gs], gs, "cmd.ceiling_edit", plan=False)
    return guid


def perforated_ceiling_under(doc, slab, pattern, drop=CEILING_DROP):
    """(0.549) A perforated false ceiling made under a slab: the slab's plan, its underside `drop` under the
    slab's, with a Visual Graph operator's holes. One undo step. Returns the ceiling's GlobalId."""
    info = doc.ifc.slab_outline(slab)
    if info is None:
        raise ValueError("essa laje não serve para um teto falso")
    language, prefix = lang(), t("elem.ceiling")
    z = float(info["bottom"]) - float(drop)

    def action(ifc):
        name = "{} {}".format(prefix, _coverings(ifc, "CEILING") + 1)
        ceiling = ifc.add_ceiling(info["outline"], z, name, "continuous", info["holes"], language)
        ifc.set_ceiling_perforation(ceiling.GlobalId, pattern)
        return ceiling.GlobalId

    return doc.execute(IfcCommand(t("cmd.ceiling"), action)).result


def add_plane_panel(doc, frame, face, pattern, source=""):
    """(0.553) A perforated panel on a flat face drawn in the model (ifc.add_plane_panel). One undo step. Its
    GlobalId."""
    language = lang()

    def action(ifc):
        count = sum(1 for e in ifc.file.by_type("IfcPlate") if ifc._params(e).get("Elemento") == "plane_panel")
        return ifc.add_plane_panel(frame, face, pattern, "{} {}".format(t("elem.perforated"), count + 1),
                                   source, language).GlobalId

    return doc.execute(IfcCommand(t("cmd.perforated"), action)).result


def covering_frame(points):
    """(0.563) (frame (4, 4), to_plane) of a face to lay a Revestimento on — on a wall x level along it and y up,
    on a floor x east and y north (core/tiling.face_frame); to_plane(points) its points in the frame's x, y."""
    from ..core import tiling as tl
    fr = tl.face_frame(points)
    o, x, y, n = fr
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, y, n, o
    return m, (lambda pts: tl.to_plane(pts, fr))


def add_covering(doc, points, finish, holes=(), layout=None, source="", **changes):
    """(0.563) A Revestimento (ifc.add_tiled_covering) on the flat face `points` (3D, its outline; `holes` 3D too),
    of the finish `finish` (core/covering_finishes), its layout and anything else changed. One undo step. Its
    GlobalId."""
    from shapely.geometry import Polygon
    frame, flat = covering_frame(points)
    face = Polygon(flat(points), [flat(h) for h in holes if len(h) >= 3]).buffer(0)
    language = lang()

    def action(ifc):
        count = sum(1 for e in ifc.file.by_type("IfcCovering") if ifc._params(e).get("Elemento") == "tiled_covering")
        return ifc.add_tiled_covering(frame, face, finish, "{} {}".format(t("elem.tiled_covering"), count + 1),
                                      layout, source, language, **changes).GlobalId

    return doc.execute(IfcCommand(t("cmd.tiled_covering"), action)).result


def covering_face(doc, guid, point, normal):
    """(0.564) (outline, holes, normal) of the flat face of `guid` — an element or a drawing — round `point` facing
    `normal` (world), or None."""
    from ..core import face_region
    obj = doc.get(guid)
    if obj is None:
        return None
    if obj.is_bim:
        return doc.ifc.tiled_on(guid, point, normal)
    m = np.asarray(getattr(obj, "matrix", np.eye(4)), float)
    tris, _owner = obj.mesh.triangulate()
    if not len(tris):
        return None
    verts = np.array([(m @ np.append(v, 1.0))[:3] for v in obj.mesh.verts])
    found = face_region.face_at(verts, tris, point, normal)
    if found is None:                                    # (a drawing's face may be wound either way)
        found = face_region.face_at(verts, tris, point, -np.asarray(normal, float))
        if found is not None:
            found = (found[0], found[1], -found[2])
    return found


def cover_face(doc, guid, point, normal, finish, layout=None, **changes):
    """(0.564) A Revestimento on the flat face of `guid` (an element: it follows it; a drawing: laid where it is)
    clicked at `point`, facing `normal`. One undo step. Its GlobalId — None when there is no flat face there."""
    found = covering_face(doc, guid, point, normal)
    if found is None:
        return None
    outline, holes, n = found
    from ..ifc.tiled_coverings import face_frame_and_shape
    frame, face = face_frame_and_shape(outline, holes)
    language, bim_host = lang(), doc.get(guid).is_bim

    def action(ifc):
        count = sum(1 for e in ifc.file.by_type("IfcCovering") if ifc._params(e).get("Elemento") == "tiled_covering")
        e = ifc.add_tiled_covering(frame, face, finish, "{} {}".format(t("elem.tiled_covering"), count + 1),
                                   layout, guid, language, **changes)
        if bim_host:
            ifc.remember_face(e.GlobalId, guid, point, n)
        return e.GlobalId

    return doc.execute(IfcCommand(t("cmd.tiled_covering"), action)).result


def cover_drawings(doc, sketches, finish, layout=None, **changes):
    """(0.564) A Revestimento on each closed drawing chosen (a polygon, a rectangle, a circle drawn on a plane or a
    face) — its whole face (level ones from above). One undo step. Their GlobalIds."""
    from ..ifc.tiled_coverings import face_frame_and_shape
    from .surface_curves import sketch_chains
    jobs = []
    for g in sketches:
        obj = doc.get(g)
        if obj is None or obj.is_bim:
            continue
        for pts, closed in sketch_chains(obj):
            pts = np.asarray(pts, float)
            if not closed or len(pts) < 3:
                continue
            if np.linalg.norm(pts[0] - pts[-1]) < 1e-9:
                pts = pts[:-1]
            from ..core.mesh import polygon_normal
            n = np.asarray(polygon_normal(pts), float)
            if abs(n[2]) > 0.7 and n[2] < 0:             # (a level drawing: covered from above)
                pts = pts[::-1]
            frame, face = face_frame_and_shape(pts)
            if face.area > 1e-4:
                jobs.append((frame, face, g))
    if not jobs:
        raise ValueError("tiling_empty")
    language = lang()

    def action(ifc):
        out = []
        for frame, face, g in jobs:
            count = sum(1 for e in ifc.file.by_type("IfcCovering")
                        if ifc._params(e).get("Elemento") == "tiled_covering")
            out.append(ifc.add_tiled_covering(frame, face, finish, "{} {}".format(t("elem.tiled_covering"), count + 1),
                                              layout, g, language, **changes).GlobalId)
        return out

    return doc.execute(IfcCommand(t("cmd.tiled_covering"), action)).result


def set_covering(doc, guid, **changes):
    """(0.563) A Revestimento changed (ifc.set_tiled_covering: layout, finish, material, thickness, bed, grout…).
    One undo step."""
    language = lang()
    _edit(doc, lambda ifc: ifc.set_tiled_covering(guid, lang=language, **changes), [guid], "cmd.tiled_covering")
    return guid


def set_plane_panel(doc, guid, pattern=None, frame=None, face=None):
    """(0.553) A plane panel's holes, plane or shape. One undo step."""
    _edit(doc, lambda ifc: ifc.set_plane_panel(guid, pattern, frame, face), [guid], "cmd.cladding_edit")
    return guid


def perforate_surface(doc, guid, pattern):
    """(0.550) A parametric surface's perforated sheet — a Visual Graph operator's holes
    (ifc.set_surface_perforation; free «»: none again). In a group, every copy. One undo step."""
    gs = _and_copies(doc, guid)
    language = lang()
    _edit(doc, lambda ifc: [ifc.set_surface_perforation(g, pattern, language) for g in gs], gs,
          "cmd.param_surface_edit", plan=False)
    return guid


def set_flooring(doc, guid, finish):
    """(0.415) A floor finish's finish (its material and thickness). In a group, every copy. One undo step."""
    gs = _and_copies(doc, guid)
    language = lang()
    _edit(doc, lambda ifc: [ifc.set_flooring(g, finish, language) for g in gs], gs, "cmd.flooring_edit", plan=False)


WALL_FINISH_HEIGHT = 2.10   # m: tiles up to the doors' heads (0.119)


def add_cladding(doc, wall, side, finish="azulejo", height=WALL_FINISH_HEIGHT, pattern=None, region=None):
    """A finish (0.119: tiles, plaster, stone) on the face `side` (±1) of a wall, from its base up to `height`,
    cut round its doors and windows; it follows the wall. (0.389) `pattern`: its pattern's measures; `region`:
    {start, end, base} a rectangle on the face. One undo step. Returns its GlobalId."""
    language = lang()
    own = {"perfurado": ("elem.perforated", "cmd.perforated"), "ripado": ("elem.ripado", "cmd.ripado")}   # (0.434)
    name_key, cmd_key = own.get(finish, ("elem.cladding", "cmd.cladding"))
    prefix = t(name_key)

    def action(ifc):
        name = "{} {}".format(prefix, _coverings(ifc, "CLADDING") + 1)
        return ifc.add_cladding(wall, side, finish, height, name, language, pattern, region).GlobalId

    return doc.execute(IfcCommand(t(cmd_key), action)).result


def set_cladding(doc, guid, height=None, finish=None, **pattern):
    """A wall finish's height or finish changed (0.119) — or its pattern's measures (0.173: width, gap, direction,
    diameter, pitch, margin; 0.175: amplitude, wavelength, shift, depth). One undo step."""
    gs = _and_copies(doc, guid)
    layers = [c for g in gs for c in doc.ifc.face_claddings(g) if c not in gs]     # (0.178) those over it follow
    _edit(doc, lambda ifc: [ifc.set_cladding(g, height, finish, **pattern) for g in gs], gs + layers,
          "cmd.cladding_edit")


def _profile_name(ifc, profile):
    n = sum(1 for e in ifc.profiles() if ifc._params(e).get("Perfil") == profile)
    return "{} {}".format(profile_label(profile), n + 1)


def profile_label(key):
    """(0.245) A profile's name: the catalogue's (core/profiles.PROFILES), or a project's own (its key "custom:" +
    its name)."""
    from ..core import profiles as core_profiles
    return key[len(core_profiles.CUSTOM):] if core_profiles.is_custom(key) else t("profile." + key)


def profile_choices(doc):
    """(0.245) [(key, name)] of the profiles one can run: the catalogue's, then the project's own."""
    from ..core import profiles as core_profiles
    own = sorted(doc.ifc.custom_profiles()) if hasattr(doc.ifc, "custom_profiles") else []
    return [(k, t("profile." + k)) for k in core_profiles.PROFILES] + [(core_profiles.CUSTOM + n, n) for n in own]


def face_section(obj):
    """(0.245) A flat sketch's outline as a profile's section [(a, b)…] m — drawn on the ground: a along X, b along
    Y; drawn upright: a along its face, b up. ValueError when it is not one flat face."""
    from ..core.sketch_geometry import transform_point
    mesh = getattr(obj, "mesh", None)
    if obj is None or getattr(obj, "is_bim", True) or mesh is None or not mesh.faces:
        raise ValueError("profile_face")
    fi = max(range(len(mesh.faces)), key=mesh.face_area)
    normal = np.asarray(obj.matrix[:3, :3] @ mesh.face_normal(fi), dtype=float)
    normal /= max(float(np.linalg.norm(normal)), 1e-12)
    pts = np.array([transform_point(obj.matrix, mesh.verts[i]) for i in mesh.faces[fi]], dtype=float)
    others = [f for f in range(len(mesh.faces)) if f != fi]
    if any(abs(abs(float(np.dot(obj.matrix[:3, :3] @ mesh.face_normal(f), normal))) - 1.0) > 1e-6 for f in others):
        raise ValueError("profile_face")                # (a volume, not a flat face)
    if abs(normal[2]) > 0.9:
        return [(float(p[0]), float(p[1])) for p in pts]
    along = np.array((-normal[1], normal[0], 0.0))
    along /= max(float(np.linalg.norm(along)), 1e-12)
    return [(float(p @ along), float(p[2])) for p in pts]


def roof_profile_from_face(doc, roof, obj_id):
    """(0.251) A roof over a rectangle made by extrusion of a flat sketch's outline (face_section: drawn upright,
    across the roof — or on the ground, x across and y up), at its real size: over the rectangle's middle, its lowest
    point at the eave. One undo step (the walls tied to the roof follow)."""
    section = face_section(doc.get(obj_id))
    doc.execute(IfcCommand(t("cmd.roof_profile"), lambda ifc: ifc.set_roof_section(roof, section), changed=[roof]))


def profile_from_face(doc, obj_id, name):
    """(0.245) A flat sketch's face kept in the project as a profile's section, under `name` (ifc
    add_custom_profile). One undo step. Returns its key ("custom:" + name)."""
    from ..core import profiles as core_profiles
    section = face_section(doc.get(obj_id))
    doc.execute(IfcCommand(t("cmd.profile_from_face"), lambda ifc: ifc.add_custom_profile(name, section)))
    return core_profiles.CUSTOM + str(name).strip()


def add_profile(doc, path, profile="rodape", closed=False, side=1, foot=None, width=None, height=None, storey=None):
    """(0.174) A profile (core/profiles.PROFILES: a skirting board, a cornice, a dado rail, an outside cornice) along
    `path` [(x, y[, z])…] (plan, on the storey's floor), to its left (side +1) or right; its foot over the floor its
    own unless given (a cornice: under the walls' top); broken at the doors of the walls it runs along. One undo
    step. Returns its GlobalId."""
    storey = storey or doc.active_storey
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    language = lang()
    pts = [tuple(float(c) for c in q[:2]) for q in path]

    def action(ifc):
        return ifc.add_profile([pts], closed, profile, _profile_name(ifc, profile), storey, level, width, height,
                               foot, side, lang=language).GlobalId

    return doc.execute(IfcCommand(t("cmd.profile"), action)).result


def room_profile(doc, point, profile="rodape", foot=None, width=None, height=None, storey=None):
    """(0.174) A profile round the room where `point` is (plan): along its walls' faces and round its columns, into
    the room, broken at its doors; it follows the room when its walls change. One undo step. Returns its GlobalId,
    or None when no room is enclosed there."""
    storey = storey or doc.active_storey
    rings = doc.ifc.room_rings(storey, (float(point[0]), float(point[1])))
    if rings is None:
        return None
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    language = lang()

    def action(ifc):
        return ifc.add_profile(rings, True, profile, _profile_name(ifc, profile), storey, level, width, height, foot,
                               1, room=(float(point[0]), float(point[1])), lang=language).GlobalId

    return doc.execute(IfcCommand(t("cmd.profile"), action)).result


def wall_sweep(doc, wall, point, profile="rodape", foot=None, storey=None):
    """(0.304, Revit's Wall Sweep) A profile on a wall's face, from the point clicked there (plan): along that face
    and, on the same side, the faces of the walls joined to it (its corners mitred), up to a free end — or all round;
    out of the walls; broken at their doors; it follows the walls when they change. One undo step. Returns its
    GlobalId, or None when the point is not on a straight wall's face."""
    run = doc.ifc.wall_face_run(wall, (float(point[0]), float(point[1])))
    if run is None:
        return None
    storey = storey or doc.ifc.storey_of(wall) or doc.active_storey
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    language = lang()
    pts, closed = run

    def action(ifc):
        return ifc.add_profile([pts], closed, profile, _profile_name(ifc, profile), storey, level, None, None, foot,
                               -1, lang=language, wall=(wall, (float(point[0]), float(point[1])))).GlobalId

    return doc.execute(IfcCommand(t("cmd.wall_sweep"), action)).result


def set_profile(doc, guid, profile=None, width=None, height=None, foot=None, side=None):
    """(0.174) A profile's section (another of the catalogue), its size, its foot over the floor, its side. One undo
    step."""
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.set_profile(g, profile, width, height, foot, side) for g in gs], gs, "cmd.profile_edit")


LIGHT_TRIM = 0.005          # m: a light's face under its ceiling's (its trim, seen)


def add_light(doc, point, kind="panel", storey=None):
    """A light (0.119) at `point` (plan) set in the ceiling over it — else at CEILING_HEIGHT over the storey: a
    60 × 60 panel or a downlight. One undo step. Returns its GlobalId."""
    storey = storey or doc.active_storey
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    z = doc.ifc.ceiling_z_at(point, storey)
    z = (level + CEILING_HEIGHT if z is None else z) - LIGHT_TRIM
    prefix = t("elem.light")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcLightFixture") + 1)
        return ifc.add_light((float(point[0]), float(point[1])), z, kind, name, storey=storey).GlobalId

    return doc.execute(IfcCommand(t("cmd.light"), action)).result


def add_air_terminal(doc, point, kind="diffuser_60", storey=None):
    """An air terminal (0.138) at `point` (plan) set in the ceiling over it — else at CEILING_HEIGHT over the storey:
    a diffuser (supply) or a grille (return), its port on top of its neck. One undo step. Returns its GlobalId."""
    storey = storey or doc.active_storey
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    z = doc.ifc.ceiling_z_at(point, storey)
    z = (level + CEILING_HEIGHT if z is None else z) - LIGHT_TRIM
    prefix = t("elem.air_terminal")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcAirTerminal") + 1)
        return ifc.add_air_terminal((float(point[0]), float(point[1])), z, kind, name, storey=storey).GlobalId

    return doc.execute(IfcCommand(t("cmd.air_terminal"), action)).result


def add_equipment(doc, point, kind="ducted_unit", angle=0.0, base=None, storey=None):
    """An HVAC unit (0.139) at `point` (plan: the middle of its base), its length along `angle` degrees, its base
    `base` m over the storey (None: the kind's usual — a ducted unit in the ceiling void, an AHU on the floor), its
    ports for its ducts and drain. One undo step. Returns its GlobalId."""
    from ..ifc.equipment import EQUIPMENT
    storey = storey or doc.active_storey
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    base = EQUIPMENT[kind][2] if base is None else float(base)
    prefix = t("elem.equipment")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcUnitaryEquipment") + 1)
        return ifc.add_equipment(np.array((float(point[0]), float(point[1]), level + base)), angle, kind, name,
                                 storey=storey).GlobalId

    return doc.execute(IfcCommand(t("cmd.equipment"), action)).result


def add_point(doc, back, kind="outlet", angle=0.0, height=None, storey=None):
    """An electrical point (0.143) of this kind, the middle of its back at `back` (at the storey's floor), its X along
    `angle` degrees, its middle `height` over the floor (None: its usual — an outlet 0,30 m, a switch 1,10 m): its
    cable's port. One undo step. Returns its GlobalId."""
    storey = storey or doc.active_storey
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    prefix = t("elem.point." + kind)

    def action(ifc):
        name = "{} {}".format(prefix, sum(ifc.count(c) for c in ("IfcOutlet", "IfcSwitchingDevice",
                                                                 "IfcElectricDistributionBoard", "IfcJunctionBox")) + 1)
        return ifc.add_point(np.array((float(back[0]), float(back[1]), level)), angle, kind, name, storey=storey,
                             height=height).GlobalId

    return doc.execute(IfcCommand(t("cmd.electrical"), action)).result


def door_places(doc, storey):
    """(0.145) The doors of a storey as a room's proposal needs them: [(their middle in plan (2,), width)]."""
    out = []
    for o in doc.objects.values():
        if not o.is_bim or o.ifc_class != "IfcDoor" or o.storey != storey:
            continue
        try:
            st = doc.ifc.filling_state(o.id)
        except Exception:                          # (a door made by another program: not in a wall of ours)
            continue
        frame = st["frame"]
        if st.get("curved"):                        # (0.177) in a curved wall: the frame tangent at its middle
            frame = doc.ifc.curved_frame(st["wall"], st["s"] + st["width"] / 2, st["width"])
            middle = frame.matrix[:3, 3]
        else:
            middle = frame.to_world((st["s"] + st["width"] / 2, (frame.y0 + frame.y1) / 2, frame.z0))
        out.append((np.asarray(middle[:2], dtype=float), st["width"]))
    return out


def propose_electrical(doc, storey=None, profiles=None, counts=None, rooms=None):
    """(0.145) The electrical points proposed for the rooms of a storey (or those of `rooms`): {room's GlobalId:
    (its name, profile, counts, items — electrical_proposal.propose_room's)}. profiles / counts: {room: …} chosen
    in place of the ones its name says."""
    from shapely.geometry import Polygon
    from ..core.rooms import label_point
    from . import electrical_proposal as ep
    storey = storey or doc.active_storey
    doors = door_places(doc, storey)
    out = {}
    for info in doc.ifc.spaces(storey):
        if rooms is not None and info["guid"] not in rooms:
            continue
        profile = (profiles or {}).get(info["guid"]) or ep.profile_of(info["name"])
        c = dict((counts or {}).get(info["guid"]) or ep.PROFILES[profile])
        poly = Polygon(info["outline"], info["holes"])
        middle = label_point(poly) if poly.is_valid and not poly.is_empty else np.mean(info["outline"], axis=0)
        out[info["guid"]] = (info["name"], profile, c, ep.propose_room(info["outline"], doors, c, middle))
    return out


def apply_electrical_proposal(doc, proposal, storey=None):
    """(0.145) The proposed points and lights made (one undo step), tagged as the electrical proposal. Returns their
    GlobalIds."""
    from . import electrical_proposal as ep
    storey = storey or doc.active_storey
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)

    def action(ifc):
        made = []
        for _room, (_name, _profile, _counts, items) in proposal.items():
            for kind, p, inward in items:
                if kind == "light":
                    z = ifc.ceiling_z_at(p, storey)
                    z = (level + CEILING_HEIGHT if z is None else z) - LIGHT_TRIM
                    e = ifc.add_light((float(p[0]), float(p[1])), z, "panel",
                                      "{} {}".format(t("elem.light"), ifc.count("IfcLightFixture") + 1), storey=storey)
                else:
                    count = sum(ifc.count(c) for c in ("IfcOutlet", "IfcSwitchingDevice",
                                                        "IfcElectricDistributionBoard", "IfcJunctionBox"))
                    e = ifc.add_point(np.array((float(p[0]), float(p[1]), level)), ep.angle_of(inward), kind,
                                      "{} {}".format(t("elem.point." + kind), count + 1), storey=storey)
                ifc._set_params(e, {"Proposta": ep.PROPOSAL})
                made.append(e.GlobalId)
        return made

    return doc.execute(IfcCommand(t("cmd.electrical_proposal"), action)).result


def remove_electrical_proposal(doc, storey=None):
    """(0.145) The points and lights of the electrical proposal (on a storey, or all) taken away, in one step.
    Returns how many."""
    from . import electrical_proposal as ep
    gone = doc.ifc.tagged(ep.PROPOSAL, storey)
    if gone:
        delete(doc, gone)
    return len(gone)


WATER_CLASSES = ("IfcPipeSegment", "IfcPipeFitting")


def propose_water(doc, storey=None):
    """(0.148) The water and drainage proposed for a storey's rooms with fixtures (model/water_proposal.py): {room:
    {"stack", "sewage", "cold", "hot", "fixtures"}}."""
    from ..ifc.sanitary import fixture_frame
    from . import water_proposal as wp
    storey = storey or doc.active_storey
    rooms = [(i["guid"], i["outline"]) for i in doc.ifc.spaces(storey)]
    fixtures = []
    for o in doc.objects.values():
        if o.is_bim and o.ifc_class == "IfcSanitaryTerminal" and o.storey == storey and doc.ifc.kind_of(o.id) == "fixture":
            fp = doc.ifc.fixture_params(o.id)
            m = fixture_frame(fp["back"], fp["angle"])
            fixtures.append((o.id, fp["kind"], fp["back"][:2], m[:2, 1]))
    return wp.propose(rooms, fixtures)


def apply_water_proposal(doc, plan, storey=None):
    """(0.148) The proposed stacks and water pipes made, and every fixture of those rooms connected to them only (not
    to other pipes of the project), in one undo step; all of it tagged as the water proposal. Returns the GlobalIds
    made."""
    from . import water_proposal as wp
    storey = storey or doc.active_storey
    levels = [z for _g, _n, z in doc.ifc.storeys()] or [0.0]
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    language = lang()
    cmd = IfcCommand(t("cmd.water_proposal"), None, changed=[])

    def action(ifc):
        before = {e.GlobalId for c in WATER_CLASSES for e in ifc.file.by_type(c)}
        only = set()
        word = t("elem.pipe")
        for _room, p in plan.items():
            stack = catalog.BY_KEY["tubo_100"]
            g = ifc.add_segment(stack, p["stack"], p["stack"], max(levels) + WALL_HEIGHT,
                                "{} {}".format(word, ifc.count("IfcPipeSegment") + 1), language, storey=storey,
                                end_z=level - 0.30).GlobalId
            ifc.set_system([g], "sewage" if p["sewage"] else "waste", language)
            only.add(g)
            for key, line, z in (("cold", p["cold"], wp.COLD_Z), ("hot", p["hot"], wp.HOT_Z)):
                if line is None:
                    continue
                g = ifc.add_segment(catalog.BY_KEY["tubo_25"], line[0], line[1], level + z,
                                    "{} {}".format(word, ifc.count("IfcPipeSegment") + 1), language,
                                    storey=storey).GlobalId
                ifc.set_system([g], key, language)
                only.add(g)
        for _room, p in plan.items():
            for fixture in p["fixtures"]:
                ifc.connect_fixture(fixture, language, cmd.changed, only)
        made = [e.GlobalId for c in WATER_CLASSES for e in ifc.file.by_type(c) if e.GlobalId not in before]
        for g in made:
            ifc._set_params(ifc.by_guid(g), {"Proposta": wp.PROPOSAL})
        return made

    cmd.action = action
    return doc.execute(cmd).result


def remove_water_proposal(doc, storey=None):
    """(0.148) The stacks, pipes and fittings of the water proposal (on a storey, or all) taken away, in one step.
    Returns how many."""
    from . import water_proposal as wp
    gone = doc.ifc.tagged(wp.PROPOSAL, storey, classes=WATER_CLASSES)
    if gone:
        delete(doc, gone)
    return len(gone)


CIRCUIT_LOADS = ("IfcOutlet", "IfcSwitchingDevice", "IfcLightFixture", "IfcJunctionBox", "IfcUnitaryEquipment",
                 "IfcElectricAppliance")                                            # (appliances: 0.198)


def circuit_kind(doc, points):
    """(0.144) The type a circuit of these points is (lights and switches: lighting; counter outlets: kitchen; an
    HVAC unit: hvac; else outlets)."""
    classes = {doc.get(g).ifc_class for g in points if doc.get(g) is not None}
    kinds = {doc.ifc.point_params(g)["kind"] for g in points
             if doc.get(g) is not None and doc.get(g).ifc_class in ("IfcOutlet", "IfcSwitchingDevice", "IfcJunctionBox")}
    if classes and classes <= {"IfcLightFixture", "IfcSwitchingDevice", "IfcJunctionBox"}:
        return "lighting"
    if "IfcUnitaryEquipment" in classes:
        return "hvac"
    if "IfcElectricAppliance" in classes:              # (0.198) an oven, a hob…: a circuit of its own
        return "appliance"
    if "outlet_counter" in kinds:
        return "kitchen"
    return "outlets"


def add_circuit(doc, points, kind=None):
    """(0.144) A new circuit (C1, C2…) with these electrical points and lights (out of any circuit they were in), of
    `kind` (None: worked out from them), on the board of their storey (if it has one). One undo step. Returns its
    GlobalId, or None if none of them can be on a circuit."""
    points = [g for g in points if doc.get(g) is not None and doc.get(g).ifc_class in CIRCUIT_LOADS]
    if not points:
        return None
    kind = kind or circuit_kind(doc, points)
    storey = doc.get(points[0]).storey
    board = next((o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcElectricDistributionBoard"
                  and o.storey == storey), None)
    made = doc.execute(IfcCommand(t("cmd.circuit"), lambda ifc: ifc.add_circuit(kind, points, board),
                                  touched=points)).result
    doc.schedules_changed()
    return made


def route_circuits(doc, circuits=None, spec=None, z=None):
    """(0.146) Ligar ao quadro: the conduits of these circuits (None: those of the active storey that have none) —
    from the board to each point in turn (ifc/conduits.py), `spec` the conduit's type (Ø20), z their height over
    the storey (2,75 m). One undo step. Returns {circuit: the conduits' GlobalIds}."""
    from ..ifc.conduits import CONDUIT_Z
    spec = spec or catalog.BY_KEY["tubo_vd20"]
    storey = doc.active_storey
    level = next((zz for g, _n, zz in doc.ifc.storeys() if g == storey), 0.0)
    if circuits is None:
        circuits = []
        for g, _name in doc.ifc.circuits():
            points = [p for p in doc.ifc.circuit_points(g) if doc.get(p) is not None and doc.get(p).storey == storey]
            if points and not doc.ifc.circuit_conduits(g):
                circuits.append(g)
    if not circuits:
        return {}
    language, out = lang(), {}
    height = level + (CONDUIT_Z if z is None else z)

    def action(ifc):
        for g in circuits:
            out[g] = ifc.route_circuit(g, spec, height, language)
        return out

    doc.execute(IfcCommand(t("cmd.route_circuits"), action))
    doc.schedules_changed()
    return out


def edit_circuit(doc, guid, **changes):
    """(0.144) A circuit's type, breaker, section or name changed. One undo step."""
    doc.execute(IfcCommand(t("cmd.circuit_edit"), lambda ifc: ifc.edit_circuit(guid, **changes)))
    doc.schedules_changed()


def remove_circuit(doc, guid):
    """(0.144) The circuit goes; its points stay, in none. One undo step."""
    points = doc.ifc.circuit_points(guid)
    doc.execute(IfcCommand(t("cmd.circuit_remove"), lambda ifc: ifc.remove_circuit(guid), touched=points))
    doc.schedules_changed()


def add_fixture(doc, back, kind="wc", angle=0.0, storey=None):
    """A sanitary fixture (0.140) of this kind, the middle of its back at `back` (its floor's height taken from the
    storey), its X along `angle` degrees: its connections (drain, cold, hot) and its free zone. One undo step.
    Returns its GlobalId."""
    storey = storey or doc.active_storey
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    prefix = t("elem.fixture." + kind)

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcSanitaryTerminal") + 1)
        return ifc.add_fixture(np.array((float(back[0]), float(back[1]), level)), angle, kind, name,
                               storey=storey).GlobalId

    return doc.execute(IfcCommand(t("cmd.fixture"), action)).result


def add_cabinet(doc, back, angle, cabinet, storey=None):
    """A cabinet (0.169: core.cabinets.Cabinet), the middle of its back at `back` (plan; its floor the storey's),
    its width along `angle` degrees. One undo step. Returns its GlobalId."""
    storey = storey or doc.active_storey
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    language, prefix = lang(), t("elem.cabinet." + cabinet.kind)

    def action(ifc):
        name = "{} {}".format(prefix, sum(1 for c in ifc.cabinets().values() if c.kind == cabinet.kind) + 1)
        return ifc.add_cabinet(np.array((float(back[0]), float(back[1]), level)), angle, cabinet, name, language,
                               storey=storey).GlobalId

    return doc.execute(IfcCommand(t("cmd.cabinet"), action)).result


def set_cabinet(doc, guid, **changes):
    """A cabinet's parameters (0.169: kind, width, height, depth, plinth, elevation, fronts, doors, drawers,
    shelves, handle). One undo step."""
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.set_cabinet(g, **changes) for g in gs], gs, "cmd.cabinet_edit")


def cabinet_outline(back, angle, cabinet):
    """Its plan's outline (4 corners, with its fronts) for a cabinet put with its back's middle at `back`."""
    a = np.radians(float(angle))
    x = np.array((np.cos(a), np.sin(a)))
    y = np.array((-x[1], x[0]))
    o = np.asarray(back, dtype=float)[:2] - x * cabinet.width / 2
    d = cabinet.overall_depth
    z = float(np.asarray(back, dtype=float)[2]) if len(back) > 2 else 0.0
    return [np.array((*(o + x * u + y * v), z)) for u, v in ((0, 0), (cabinet.width, 0), (cabinet.width, d), (0, d))]


def cabinet_backs(doc):
    """{GlobalId: (its back's middle (3,), its x direction (3,), its width)} of the cabinets of the active storey —
    for a new one to go flush against them."""
    out = {}
    try:
        found = doc.ifc.cabinets()
    except RuntimeError:
        return out
    for guid, c in found.items():
        obj = doc.get(guid)
        if obj is None or obj.storey != doc.active_storey:
            continue
        m = doc.ifc.placement(guid)
        x = m[:3, 0] / np.linalg.norm(m[:3, 0])
        out[guid] = (m[:3, 3] + x * c.width / 2, x, c.width)
    return out


def cut_list(doc, guids=None):
    """(0.169) The cut list of the cabinets (those of `guids`, or all) and (0.170) of their worktops: (rows —
    core.cabinets.cut_list, a worktop's pieces after them —, the hardware {kind: how many}, the board's area by
    material {material: m²})."""
    from ..core import cabinets as core_cab
    chosen = set(guids) if guids is not None else None
    layouts = [core_cab.layout(c) for c in doc.ifc.cabinets(chosen).values()]
    rows = core_cab.cut_list(layouts)
    for guid, (_outline, pieces, _top, thickness) in doc.ifc.worktops().items():
        if chosen is not None and guid not in chosen and not chosen & set(doc.ifc.worktop_hosts(guid)):
            continue
        for length, width in pieces:
            rows.append(("worktop", "worktop", round(length, 3), round(width, 3), round(thickness, 3), 1, 1))
    from ..core.profiles import PROFILES, is_custom
    from . import fabrication                          # (0.173) the patterned finishes' slats and panels
    rows += fabrication.pieces(doc, guids)[0]          # (0.174) and the profiles' pieces — lengths, not board
    return rows, core_cab.hardware(layouts), core_cab.area([r for r in rows if r[0] not in PROFILES
                                                            and not is_custom(r[0])])


def add_appliance(doc, back, kind="hob", angle=0.0, storey=None):
    """(0.171) An appliance (core/appliances.APPLIANCES) with the middle of its back at `back` (plan; its floor the
    storey's), its width along `angle` degrees; a hob over a worktop cuts it. One undo step. Returns its GlobalId."""
    storey = storey or doc.active_storey
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    language, prefix = lang(), t("appliance." + kind)

    def action(ifc):
        n = sum(1 for cls in ("IfcElectricAppliance", "IfcBurner") for e in ifc.file.by_type(cls)
                if ifc._params(e).get("Aparelho") == kind)
        return ifc.add_appliance(np.array((float(back[0]), float(back[1]), level)), angle, kind,
                                 "{} {}".format(prefix, n + 1), language, storey=storey).GlobalId

    return doc.execute(IfcCommand(t("cmd.appliance"), action)).result


def add_worktop(doc, hosts=None):
    """(0.170) A worktop over base units (their GlobalIds; None: every base unit of the active storey): their
    footprints out past their fronts, joined at the corners, on their top — tied to them. One undo step. Returns its
    GlobalId, or None when there are no base units."""
    found = doc.ifc.cabinets(set(hosts) if hosts is not None else None)
    hosts = [g for g, c in found.items() if c.kind == "base" and (hosts is not None or (
        doc.get(g) is not None and doc.get(g).storey == doc.active_storey))]
    if not hosts:
        return None
    language, prefix = lang(), t("elem.worktop")

    def action(ifc):
        name = "{} {}".format(prefix, len(ifc.worktops()) + 1)
        return ifc.add_worktop(sorted(hosts), name, language).GlobalId

    return doc.execute(IfcCommand(t("cmd.worktop"), action)).result


def make_kitchen(doc, points, side=1, wall_units=True, worktop=True, fronts="doors", handle="bar", storey=None,
                 corner="blind", finish="melamine"):
    """(0.170) A kitchen along a run (core.kitchens: `points` its back line along the walls' faces, in order; `side`
    +1 with the room on its left): its legs filled with base units, wall units over them (wall_units), a worktop
    over the base units (worktop). (0.239, 0.240) corner: its inside corners' units (kitchens.CORNERS: blind, L,
    L with a carousel below); (0.243) finish: its fronts'. One undo step. Returns {"base", "wall", "worktop"} the GlobalIds made."""
    from ..core import cabinets as core_cab
    from ..core import kitchens
    storey = storey or doc.active_storey
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    base_spots = kitchens.run_modules(points, side, kind="base", corners=corner)
    wall_spots = kitchens.run_modules(points, side, kind="wall", corners="l" if corner == "carousel" else corner) \
        if wall_units else []
    if not base_spots:
        return None
    language = lang()

    def action(ifc):
        made = {"base": [], "wall": [], "worktop": None}
        for kind, spots in (("base", base_spots), ("wall", wall_spots)):
            prefix = t("elem.cabinet." + kind)
            n = sum(1 for c in ifc.cabinets().values() if c.kind == kind)
            for k, (mid, angle, width, blind, corner_side, arm) in enumerate(spots):
                c = core_cab.Cabinet.of(kind, width=width, fronts="doors" if blind or arm else fronts, handle=handle,
                                        doors=2 if width - blind >= 0.60 else 1, blind=blind, corner_side=corner_side,
                                        arm=arm, interior="carousel" if arm and kind == "base" and
                                        corner == "carousel" else "", finish=finish)
                e = ifc.add_cabinet(np.array((float(mid[0]), float(mid[1]), level)), angle, c,
                                    "{} {}".format(prefix, n + k + 1), language, storey=storey)
                made[kind].append(e.GlobalId)
        if worktop and made["base"]:
            made["worktop"] = ifc.add_worktop(made["base"], "{} {}".format(t("elem.worktop"),
                                                                            len(ifc.worktops()) + 1),
                                              language).GlobalId
        return made

    return doc.execute(IfcCommand(t("cmd.kitchen"), action)).result


def add_terrain(doc, points, name=None, interval=None):
    """The terrain (0.155) through survey points (x, y, z: program coordinates) — in the site, not in a storey.
    One undo step. Returns its GlobalId; ValueError when the points make no surface (fewer than three, in a
    line)."""
    from ..core import terrain as terrain_geo
    if terrain_geo.tin(points) is None:
        raise ValueError("no surface")
    language, prefix = lang(), t("elem.terrain")

    def action(ifc):
        label = name or "{} {}".format(prefix, len(ifc.terrains()) + 1)
        return ifc.add_terrain(points, label, language, interval or terrain_geo.DEFAULT_INTERVAL).GlobalId

    return doc.execute(IfcCommand(t("cmd.terrain"), action)).result


def set_terrain_points(doc, guid, points):
    """A terrain made again through other points (added, moved, taken away): one undo step. ValueError when they
    make no surface."""
    from ..core import terrain as terrain_geo
    if terrain_geo.tin(points) is None:
        raise ValueError("no surface")
    doc.execute(IfcCommand(t("cmd.terrain_points"), lambda ifc: ifc.set_terrain_points(guid, points),
                           changed=[guid]))


def add_platform(doc, guid, outline, z, cut=None, fill=None, name=""):
    """A platform (0.157) on a terrain: the flat area `outline` (x, y) at the height z, its slopes round it (cut
    and fill batters, height over width) down or up to the ground. One undo step. Returns (cut, fill) m³ of all the
    terrain's platforms."""
    from ..core import earthworks
    platforms = doc.ifc.terrain_platforms(guid)
    label = name or "{} {}".format(t("elem.platform"), len(platforms) + 1)
    plat = earthworks.Platform([(float(x), float(y)) for x, y in outline], float(z),
                               earthworks.CUT_SLOPE if cut is None else float(cut),
                               earthworks.FILL_SLOPE if fill is None else float(fill), label)
    doc.execute(IfcCommand(t("cmd.platform"), lambda ifc: ifc.set_terrain_platforms(guid, platforms + [plat]),
                           changed=[guid]))
    return doc.ifc.terrain_volumes(guid)


def add_terrain_ramp(doc, guid, start, end, width, cut=None, fill=None, name=""):
    """(0.205) A ramp of access on a terrain, from start to end (x, y), `width` across: its height going evenly
    from the proposed ground's at its start to that at its end — a platform's, where it starts or ends on one —,
    its slopes round it as a platform's. One undo step. Returns (cut, fill) m³ of all the terrain's platforms.
    ValueError: too short, or an end off the terrain."""
    from ..core import earthworks
    from ..core import terrain as terrain_geo
    outline = earthworks.ramp_outline(start, end, width)
    if outline is None:
        raise ValueError("too short")
    verts, tris = doc.ifc.terrain_surface(guid)
    z0, z1 = (terrain_geo.height_at(verts, tris, np.asarray(p, dtype=float)[:2]) for p in (start, end))
    if z0 is None or z1 is None:
        raise ValueError("off the terrain")
    platforms = doc.ifc.terrain_platforms(guid)
    label = name or "{} {}".format(t("elem.terrain_ramp"), sum(p.is_ramp() for p in platforms) + 1)
    plat = earthworks.Platform(outline, float(z0), earthworks.CUT_SLOPE if cut is None else float(cut),
                               earthworks.FILL_SLOPE if fill is None else float(fill), label,
                               [tuple(map(float, start[:2])), tuple(map(float, end[:2]))], float(z1))
    doc.execute(IfcCommand(t("cmd.terrain_ramp"), lambda ifc: ifc.set_terrain_platforms(guid, platforms + [plat]),
                           changed=[guid]))
    return doc.ifc.terrain_volumes(guid)


def set_platform(doc, guid, index, outline=None, z=None):
    """(0.204) One of a terrain's platforms changed — its outline (x, y) and / or its height —, its slopes and the
    ground round it made again. One undo step. Returns (cut, fill) m³ of all the terrain's platforms."""
    import dataclasses
    platforms = doc.ifc.terrain_platforms(guid)
    if not 0 <= index < len(platforms):
        raise IndexError(index)
    changes = {}
    if outline is not None:
        changes["outline"] = [(float(x), float(y)) for x, y in outline]
    if z is not None:
        changes["z"] = float(z)
    platforms[index] = dataclasses.replace(platforms[index], **changes)
    doc.execute(IfcCommand(t("cmd.platform_edit"), lambda ifc: ifc.set_terrain_platforms(guid, platforms),
                           changed=[guid]))
    return doc.ifc.terrain_volumes(guid)


def remove_platforms(doc, guid, indices=None):
    """The terrain's platforms taken away (those at `indices`, or all): the ground as surveyed there again. One
    undo step."""
    platforms = doc.ifc.terrain_platforms(guid)
    keep = [] if indices is None else [p for k, p in enumerate(platforms) if k not in set(indices)]
    doc.execute(IfcCommand(t("cmd.remove_platform"), lambda ifc: ifc.set_terrain_platforms(guid, keep),
                           changed=[guid]))


def set_terrain_params(doc, guid, interval=None, depth=None):
    """A terrain's contour interval and/or its base's depth under its lowest point (m): one undo step."""
    doc.execute(IfcCommand(t("cmd.terrain_params"), lambda ifc: ifc.set_terrain_params(guid, interval, depth),
                           changed=[guid] if depth is not None else (), touched=[guid]))


def add_curtain_wall(doc, start, end, height=WALL_HEIGHT, mullions=1.5, transoms=1.0, storey=None, embed=True,
                     arc=None):
    """A curtain wall (0.117) along start -> end, `height` high, its mullions and transoms at most `mullions` /
    `transoms` apart; (0.188) embed: drawn in a wall, it cuts its opening in it (and keeps doing so); (0.252) arc:
    (centre, radius, start angle, sweep) — along that arc, in a curved wall. One undo step. Returns its GlobalId."""
    language, prefix = lang(), t("elem.curtain_wall")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcCurtainWall") + 1)
        return ifc.add_curtain_wall(start, end, height, mullions, transoms, name, language,
                                    storey=storey, embed=embed, arc=arc).GlobalId

    return doc.execute(IfcCommand(t("cmd.curtain_wall"), action)).result


def set_curtain_wall(doc, guid, **changes):
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.set_curtain_wall(g, **changes) for g in gs], gs, "cmd.curtain_wall_edit")


def set_keynote(doc, guid, code):
    """(0.194) An element's keynote — on its type, so every element of that type has it (else on the element) —
    from the program's table (its text comes with it; a code not in it keeps no text); "" takes it away. One undo
    step."""
    from . import keynotes
    text = keynotes.text_of(code, lang(), doc.ifc.keynote_table()) if code else ""     # (0.248: the project's first)
    sharers = doc.ifc.keynote_sharers(guid)
    doc.execute(IfcCommand(t("cmd.keynote"), lambda ifc: ifc.set_keynote(guid, code or None, text), touched=sharers))


def set_keynote_table(doc, entries):
    """(0.248) The project's own keynote table made `entries` {code: text} (the elements with a code changed take
    its text). One undo step; False when nothing changes."""
    clean = {str(k).strip(): str(v).strip() for k, v in entries.items() if str(k).strip()}
    if clean == doc.ifc.keynote_table():
        return False
    holders = [o.id for o in doc.objects.values() if o.is_bim and (doc.ifc.keynote_of(o.id) or ("",))[0] in clean]
    doc.execute(IfcCommand(t("cmd.keynote_table"), lambda ifc: ifc.set_keynote_table(clean), touched=holders))
    return True


def set_curtain_embedding(doc, guid, on):
    """(0.188) A curtain wall made to go into the wall it lies in (its opening cut there) or to come out of it. One
    undo step."""
    walls = [w for w in (doc.ifc.host_wall(guid), doc.ifc.embedding_wall(guid)) if w]
    _edit(doc, lambda ifc: ifc.set_embedding(guid, on), [guid] + walls, "cmd.curtain_embed")


def set_curtain_panel(doc, guid, cell, kind):
    """(0.181) A curtain wall's cell (column, row) made glass, opaque, a door or empty. One undo step."""
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.set_curtain_panel(g, cell, kind) for g in gs], gs, "cmd.curtain_panel")


def add_railing(doc, path, height=None, style="barras", closed=False, storey=None):
    """A railing (0.115) along `path` [(x, y, z)…] (level or sloping), `height` over it (None: its type's), of the
    type `style` (0.258: a railing type's key). One undo step. Returns its GlobalId."""
    language, prefix = lang(), t("elem.railing")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcRailing") + 1)
        return ifc.add_railing(path, height, style, name, closed=closed, storey=storey, lang=language).GlobalId

    return doc.execute(IfcCommand(t("cmd.railing"), action)).result


def opening_railing(doc, filling, height=None, style="barras"):
    """(0.374, the addon's «Guarda de vão») A railing in a door's or window's opening, from jamb to jamb, in the
    middle of the wall's thickness, from its sill up. One undo step. Its GlobalId."""
    st = doc.ifc.filling_state(filling)
    if st.get("curved"):
        raise ValueError("curved")
    f = st["frame"]
    y = (f.y0 + f.y1) / 2
    z = f.z0 + float(st.get("sill") or 0.0)
    a = f.to_world((st["s"] + 0.01, y, z))
    b = f.to_world((st["s"] + st["width"] - 0.01, y, z))
    storey = doc.ifc.storey_of(filling) if hasattr(doc.ifc, "storey_of") else None
    return add_railing(doc, [tuple(map(float, a)), tuple(map(float, b))], height, style, storey=storey)


def stair_railings(doc, stair, height=0.90, style="barras"):
    """Railings on both sides of each flight of a stair, along its nosings (0.115). One undo step. Returns
    their GlobalIds. (0.282) Their handrails on past the ends as DL 163/2006 asks (annex 2.4.9): one going at the
    foot, keeping the slope; 0,30 m at the top, level."""
    from ..core import railing_types as core_rail
    paths = doc.ifc.stair_railing_paths(stair)
    extend = (float(doc.ifc.stair_params(stair)["going"]), core_rail.TOP_EXTENSION)
    language, prefix = lang(), t("elem.railing")

    def action(ifc):
        out = []
        for path in paths:
            name = "{} {}".format(prefix, ifc.count("IfcRailing") + 1)
            out.append(ifc.add_railing(path, height, style, name, lang=language, extend=extend).GlobalId)
        return out

    return doc.execute(IfcCommand(t("cmd.railing"), action)).result


def void_railing(doc, slab, point, height=None, style="barras"):
    """A railing round the void of a slab nearest a plan point (its hole, or an opening cut through it), on the
    slab's top (0.115). One undo step. Returns its GlobalId, or None (no void there)."""
    from shapely.geometry import Point, Polygon
    rings, top = doc.ifc.void_outlines(slab)
    if not rings:
        return None
    here = Point(float(point[0]), float(point[1]))
    ring = min(rings, key=lambda r: Polygon(r).exterior.distance(here))
    if Polygon(ring).exterior.distance(here) > 1.0:
        return None
    return add_railing(doc, [(x, y, top) for x, y in ring], height, style, closed=True)


def set_railing(doc, guid, height=None, style=None, extend=None):
    """A railing's height and/or its type (0.258: a railing type's key); (0.282) its handrail's extensions (at its
    start, at its end; m). One undo step."""
    gs = _and_copies(doc, guid)
    language = lang()
    _edit(doc, lambda ifc: [ifc.set_railing(g, height, style, lang=language, extend=extend) for g in gs], gs,
          "cmd.railing_edit")


def set_railing_type(doc, rt, old_key=None):
    """(0.258) A railing type saved in the project (new, or changed: its key was `old_key`) and every railing of it
    made again. One undo step. Returns those railings."""
    language = lang()
    railings = doc.ifc.railings_of_type(old_key or rt.key)
    doc.execute(IfcCommand(t("cmd.railing_type"), lambda ifc: ifc.set_railing_type(rt, old_key, language),
                           changed=railings))
    return railings


def remove_railing_type(doc, key):
    """(0.260) A project's own railing type taken away (not one in use, nor the program's). One undo step."""
    doc.execute(IfcCommand(t("cmd.railing_type_delete"), lambda ifc: ifc.remove_railing_type(key)))


def stair_rise(doc, z, storey=None):
    """The rise of a stair starting at the level z: up to the next storey's level, else 2,80."""
    above = sorted(level for _g, _n, level in doc.ifc.storeys() if level > z + 1e-6)
    return (above[0] - z) if above else WALL_HEIGHT


def add_stair(doc, foot, direction, spec, form="straight", rise=None, width=1.0, going=0.28, turn="left",
              storey=None):
    """A stair (0.114) from `foot` (the middle of its first riser) along `direction`: straight, L or U, rising
    `rise` (default: to the storey above). One undo step. Returns its GlobalId."""
    rise = stair_rise(doc, float(foot[2])) if rise is None else float(rise)
    language, prefix = lang(), t("elem.stair")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcStair") + 1)
        return ifc.add_stair(spec, foot, direction, form, rise, width, going, turn, name, language,
                             storey=storey).GlobalId

    return doc.execute(IfcCommand(t("cmd.stair"), action)).result


def set_stair(doc, guid, **changes):
    """A stair's form, turn, rise, width or tread (0.114). One undo step."""
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.set_stair(g, **changes) for g in gs], gs, "cmd.stair_edit")


def add_drain(doc, roof, point):
    """A roof drain on the roof's top at `point` (plan, 0.113). One undo step. Returns its GlobalId."""
    prefix = t("elem.drain")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcWasteTerminal") + 1)
        return ifc.add_drain(roof, point, name).GlobalId

    return doc.execute(IfcCommand(t("cmd.drain"), action)).result


def add_vertical_opening(doc, host, a, b):
    """A rectangular opening straight through a roof or a slab (0.113: a skylight's hole), between the plan
    corners a and b. One undo step. Returns its GlobalId."""
    prefix = t("elem.bare_opening")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcOpeningElement") + 1)
        return ifc.add_vertical_opening(host, a, b, name).GlobalId

    return doc.execute(IfcCommand(t("cmd.vertical_opening"), action, changed=[host])).result


def roof_bearing(doc, outline, storey=None):
    """(0.275) What a roof over `outline` rests on: (the highest top of the storey's walls that touch it, the
    thickest of those along its edge — what its underside sits on) — (None, 0.0) when no wall touches it."""
    from shapely.geometry import LinearRing, Polygon
    storey = storey or doc.active_storey
    area = Polygon(outline).buffer(0.05)
    edge = LinearRing(outline).buffer(0.30)
    tops, widths = [], []
    for g in doc.ifc.storey_elements(storey) if storey else ():
        kind = doc.ifc.kind_of(g)
        if kind not in ("wall", "curved_wall"):
            continue
        obj = doc.get(g)
        if obj is None:
            continue
        v = np.asarray(obj.mesh.verts, dtype=float)
        if not len(v):
            continue
        box = Polygon([(float(v[:, 0].min()), float(v[:, 1].min())), (float(v[:, 0].max()), float(v[:, 1].min())),
                       (float(v[:, 0].max()), float(v[:, 1].max())), (float(v[:, 0].min()), float(v[:, 1].max()))])
        if box.intersects(area):
            tops.append(float(v[:, 2].max()))
            if box.intersects(edge):
                widths.append(float(doc.ifc.wall_params(g)[2] if kind == "wall"
                                    else doc.ifc.curved_wall_params(g)[5]))
    return (max(tops), max(widths, default=0.0)) if tops else (None, 0.0)


def roof_eave(doc, outline, storey=None):
    """Where a roof over `outline` starts: the highest top of the walls of the storey that touch the outline,
    else the storey's level + 2,80."""
    storey = storey or doc.active_storey
    top, _wall = roof_bearing(doc, outline, storey)
    if top is not None:
        return top
    level = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    return level + WALL_HEIGHT


def roof_seated(doc, outline, spec, slope, storey=None):
    """(0.275) A roof's top over its walls' line resting on them — its underside on their inner top edge (as
    Revit's «Rafter»): their top + core/roofs.seat; no wall under it: the storey's level + 2,80, as before."""
    from ..core import roofs as core_roofs
    storey = storey or doc.active_storey
    top, wall = roof_bearing(doc, outline, storey)
    if top is None:
        return roof_eave(doc, outline, storey)
    return top + core_roofs.seat(slope, spec.thickness, wall)


def set_roof(doc, guid, **changes):
    """A roof's form, slope, overhang or eave height (0.111). In a group, every copy. One undo step. (0.275) A new
    slope or form keeps it resting on its walls, as Revit keeps a roof's plate: the top over their line moves by
    as much as the seat changes (its eave height, if given, as given)."""
    gs = _and_copies(doc, guid)
    plans = [(g, _reseated(doc, g, changes)) for g in gs]

    def action(ifc):
        for g, (own, blocks) in plans:
            ifc.set_roof(g, **own)
            if blocks is not None:                     # (a roof by blocks: each water's eave by its new slope)
                ifc.set_roof_blocks(g, blocks)

    _edit(doc, action, gs, "cmd.roof_edit")


def _reseated(doc, guid, changes, thickness=None):
    """(0.275) A roof's changes with what keeps it on its walls: (its set_roof's changes, its blocks or None).
    (0.278) thickness: its new type's — its underside stays where it is (on its walls, or where it was)."""
    from ..core import roof_blocks as core_blocks
    from ..core import roofs as core_roofs
    if "eave" in changes or not ({"slope", "form"} & set(changes)) and thickness is None:
        return dict(changes), None
    p = doc.ifc.roof_params(guid)
    storey = doc.ifc.storey_of(guid)
    t = p["thickness"]
    t2 = t if thickness is None else float(thickness)
    if p["form"] == "blocks":
        if "slope" not in changes and thickness is None:
            return dict(changes), None
        slope = float(changes["slope"]) if "slope" in changes else None
        blocks = []
        for local, world in zip(p["blocks"], doc.ifc.roof_blocks_world(guid)):
            top, wall = roof_bearing(doc, core_blocks.rect(world), storey)
            if top is None and thickness is None:
                eaves = local.eave
            else:
                eaves = []
                for e, s, w in zip(local.eave, local.slope, local.water):
                    old = s if w else 0.0
                    new = old if slope is None or top is None else (slope if w else 0.0)
                    eaves.append(e - core_roofs.seat(old, t, wall) + core_roofs.seat(new, t2, wall))
                eaves = tuple(eaves)
            blocks.append(core_blocks.replace(local, eave=eaves) if slope is None else
                          core_blocks.replace(local, slope=(slope,) * 4, eave=eaves))
        return dict(changes), blocks
    top, wall = roof_bearing(doc, p["outline"], storey)
    if top is None and thickness is None:
        return dict(changes), None
    old = 0.0 if p["form"] == "flat" else p["slope"]
    new = 0.0 if changes.get("form", p["form"]) == "flat" else float(changes.get("slope", p["slope"]))
    if top is None:                                    # (no wall under it: only its thickness moves its top)
        old = new
    eave = p["eave"] - core_roofs.seat(old, t, wall) + core_roofs.seat(new, t2, wall)
    return dict(changes, eave=eave), None


def _follow_seat(ifc, plans):
    """(0.278) Roofs given another thickness: their tops (or their blocks' eaves) where _reseated put them."""
    for g, (own, blocks) in plans:
        if own:
            ifc.set_roof(g, **own)
        if blocks is not None:
            ifc.set_roof_blocks(g, blocks)


def set_wall_profile(doc, guid, points, sides=None, holes=None):
    """A wall's elevation profile (0.109): [(x along its axis, z above its base)] corners — (0.375) its sides
    straight, arcs or Bézier curves (core/curves) —, or None for a plain wall again; (0.410) holes: the holes drawn
    in it ([[corners, sides]…]; None keeps its own). In a group, every copy the same. One undo step."""
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.set_wall_profile(g, points, sides, holes) for g in gs], gs, "cmd.wall_profile",
          plan=False)


def attach_top(doc, guids, slab, offset=0.0):
    """The tops of these walls and columns tied to a slab's underside (0.106, Revit's Attach Top): they grow or
    shrink to it, and follow it when it changes. One undo step. Returns those tied."""
    elements = [g for g in guids if doc.ifc.kind_of(g) in ("wall", "column")]
    roof = doc.ifc.kind_of(slab) == "roof"             # (0.112) a roof: the walls' tops take its underside

    def action(ifc):
        for g in elements:
            if roof:
                ifc.attach_to_roof(g, slab)
            else:
                ifc.set_constraints(g, top_slab=slab, top_offset=float(offset))
        return elements

    return _edit(doc, action, elements, "cmd.attach_top", plan=False)


def flip_walls(doc, guids):
    """(0.299, Revit's flip arrows) These walls turned inside out: their layers in the other order, the rest as it
    is. In a group, every copy. One undo step. Returns those flipped (those with layers)."""
    walls = sorted({c for g in guids if doc.ifc.kind_of(g) in ("wall", "curved_wall") and doc.ifc.layer_sense(g)
                    for c in _and_copies(doc, g)})
    if not walls:
        return []
    _edit(doc, lambda ifc: [ifc.flip_wall(g) for g in walls], walls, "cmd.flip_walls", plan=False)
    return walls


def join_wall_ends(doc, guids):
    """(0.299, Revit's Allow Join) The free ends of these walls joined again to the walls they reach (a corner or a
    T), the corners made. One undo step. Returns the walls changed (none: nothing to join)."""
    walls = [g for g in guids if doc.ifc.kind_of(g) in ("wall", "curved_wall")]
    if not walls:
        return []
    cmd = IfcCommand(t("cmd.join_wall_ends"), None, changed=walls)

    def action(ifc):
        done = ifc.join_free_ends(walls)
        cmd.changed += [g for g in done if g not in cmd.changed]
        return done

    cmd.action = action
    return doc.execute(cmd).result


def detach_top(doc, guids):
    """(0.298, Revit's Detach Top) The tops of these walls and columns no longer tied to a slab or roof: they keep the
    height they have. In a group, every copy. One undo step. Returns those let go."""
    tied = [c for g in guids if doc.ifc.kind_of(g) in ("wall", "column") and doc.ifc.top_tied(g)
            for c in _and_copies(doc, g)]
    tied = sorted(set(tied))
    if not tied:
        return []
    return _edit(doc, lambda ifc: [g for g in tied if ifc.detach_top(g)], tied, "cmd.detach_top", plan=False)


def attach_base(doc, guids, support):
    """(0.302, Revit's Attach Base) The bases of these walls and columns brought to the top face of a slab or footing
    and tied to it (they follow it). In a group, every copy. One undo step. Returns those tied."""
    elements = sorted({c for g in guids if doc.ifc.kind_of(g) in ("wall", "column") for c in _and_copies(doc, g)})
    if not elements:
        return []
    return _edit(doc, lambda ifc: [ifc.attach_base(g, support) or g for g in elements], elements, "cmd.attach_base",
                 plan=False)


def detach_base(doc, guids):
    """(0.302, Revit's Detach Base) The bases of these walls and columns no longer tied to a slab or footing. One undo
    step. Returns those let go."""
    tied = sorted({c for g in guids if doc.ifc.kind_of(g) in ("wall", "column") and doc.ifc.base_tied(g)
                   for c in _and_copies(doc, g)})
    if not tied:
        return []
    return _edit(doc, lambda ifc: [g for g in tied if ifc.detach_base(g)], tied, "cmd.detach_base", plan=False)


def reset_wall_profiles(doc, guids):
    """(0.298, Revit's Reset Profile) The walls with a drawn profile made plain rectangles in elevation again, as tall
    as the profile's top; one tied to a roof (its profile the roof's) no longer follows it. In a group, every copy.
    One undo step. Returns those reset."""
    walls = sorted({c for g in guids if doc.ifc.kind_of(g) == "wall" and doc.ifc.wall_profile(g) is not None
                    for c in _and_copies(doc, g)})
    if not walls:
        return []

    def action(ifc):
        for g in walls:
            ifc.set_wall_profile(g, None)
            if ifc.top_tied(g) == "roof":
                ifc.detach_top(g)
        return walls

    return _edit(doc, action, walls, "cmd.reset_profile", plan=False)


def merge_walls(doc, a, b):
    """Two walls in line, end to end, made one (0.105): `a` reaches over `b` and takes its doors and windows.
    One undo step."""
    _edit(doc, lambda ifc: ifc.merge_walls(a, b), [a], "cmd.merge_walls")


def orthogonalize(doc, guids, tolerance_deg=5.0):
    """The walls nearly along the red / green axis turned to be exactly along it (0.105); the walls joined to
    them follow. One undo step. Returns how many turned."""
    walls = [g for g in guids if doc.ifc.kind_of(g) == "wall"]
    if not doc.ifc.off_square(walls, tolerance_deg):
        return 0                                    # (0.325: no undo step with nothing in it)
    joined = set(walls) | set(doc.ifc.joined_walls(walls))
    # (0.407) their doors and windows drawn again too: they turn with the wall (placed in it), but until 0.406 they
    # were left drawn at the old angle — the window askew in the straight wall, the door's frame out of its faces
    changed = sorted(joined | {f for g in joined for f in _fillings(doc, g)})
    return len(_edit(doc, lambda ifc: ifc.orthogonalize(walls, tolerance_deg), changed, "cmd.orthogonalize"))


def unjoin_walls(doc, guids):
    """The joints of these walls at both ends let go (0.105, Revit's Disallow Join): they stay where they are
    but no longer follow the walls they met. One undo step. Returns how many joints went."""
    walls = [g for g in guids if doc.ifc.kind_of(g) == "wall"]
    if not any((a == g and ea in ("start", "end")) or (b == g and eb in ("start", "end"))
               for g in walls for _r, a, ea, b, eb in doc.ifc.wall_joints(g)):
        return 0                                    # (0.325: no undo step with nothing in it)
    return doc.execute(IfcCommand(t("cmd.unjoin_walls"), lambda ifc: sum(
        ifc.unjoin_end(g, end) for g in walls for end in ("start", "end")), touched=walls)).result


def add_curved_wall(doc, centre, radius, start, sweep, spec, height=WALL_HEIGHT, storey=None):
    """A curved wall (0.103): its axis the arc round `centre` (its base: centre's z) of `radius`, from the angle
    `start` turning `sweep` (radians, counter-clockwise if positive; ±2π: a circle). One undo step. Returns its
    GlobalId."""
    language, prefix = lang(), t("elem.wall")
    cmd = IfcCommand(t("cmd.wall"), None)

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcWall") + 1)
        guid = ifc.add_curved_wall(spec, centre, radius, start, sweep, height, name, language,
                                   storey=storey).GlobalId
        cmd.changed += [g for g in ifc.join_ends(guid) if g not in cmd.changed]   # (0.189) corners at its ends
        return guid

    cmd.action = action
    return doc.execute(cmd).result


def fillet_walls(doc, a, keep_a, b, keep_b, radius, spec, height=WALL_HEIGHT, storey=None):
    """(0.452, Revit's «Fillet Arc») Walls a and b joined by a curved wall of `radius` tangent to both, on the side of
    each where it was picked (keep_*: plan points) — both trimmed / extended to it. One undo step. Returns the curved
    wall's GlobalId."""
    language, prefix = lang(), t("elem.wall")
    cmd = IfcCommand(t("cmd.fillet"), None)

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcWall") + 1)
        guid = ifc.fillet_walls(a, keep_a, b, keep_b, radius, spec, height, name, language, storey=storey).GlobalId
        cmd.changed += [g for g in [a, b] + _fillings(doc, a) + _fillings(doc, b) if g not in cmd.changed]
        return guid

    cmd.action = action
    return doc.execute(cmd).result


def set_curved_wall(doc, guid, radius=None, sweep=None, height=None):
    """A curved wall's radius, sweep (radians) or height — its doors and windows going with it (0.177). One undo
    step."""
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.set_curved_wall(g, radius, sweep, height) for g in gs],
          gs + [f for g in gs for f in _fillings(doc, g)])


def set_curved_radius(doc, guid, radius):
    """(0.459, Revit's radius of an arc wall typed over) A fillet's curved wall — tangent to the straight walls at its
    two ends — made again with `radius`, still tangent to them (they are trimmed or extended); another curved wall's
    radius changed about its centre. One undo step."""
    ends = doc.ifc.fillet_ends(guid)
    if ends is None:
        set_curved_wall(doc, guid, radius=radius)
        return
    walls = [guid] + [g for g, _far in ends]
    changed = sorted(set(walls) | set(doc.ifc.joined_walls(walls)) | {f for g in walls for f in _fillings(doc, g)})
    _edit(doc, lambda ifc: ifc.refillet_wall(guid, radius), changed, label="cmd.fillet_radius")


def face_outline(doc, obj_id, face_index, point):
    """The outline under a click for walls along it (0.102): a slab's (its corners, at its top) or a level face
    of a sketch volume (with the level faces beside it on the same plane). ([(x, y)] counter-clockwise, z) or
    None — a round slab, a sloping or upright face."""
    from shapely.geometry import Point, Polygon
    from shapely.geometry.polygon import orient
    from shapely.ops import unary_union
    obj = doc.get(obj_id)
    if obj is None:
        return None
    if obj.is_bim:
        if doc.ifc.kind_of(obj_id) != "slab" or doc.ifc.slab_shape(obj_id) == "circulo":
            return None
        info = doc.ifc.slab_outline(obj_id)
        if info is None:
            return None
        ring = orient(Polygon(info["outline"]), 1.0)
        return [tuple(c) for c in list(ring.exterior.coords)[:-1]], info["top"]
    mesh, m = obj.mesh, obj.matrix
    world = lambda fi: [tuple((m @ np.append(v, 1.0))[:3]) for v in mesh.face_points(fi)]     # noqa: E731
    pts = world(face_index)
    z = pts[0][2]
    if any(abs(p[2] - z) > 1e-6 for p in pts):
        return None                                           # (not level)
    level = [Polygon([p[:2] for p in world(fi)]) for fi in range(len(mesh.faces))
             if all(abs(p[2] - z) < 1e-6 for p in world(fi))]
    merged = unary_union([p.buffer(0) for p in level if p.area > 1e-9])
    here = Point(float(point[0]), float(point[1]))
    for part in getattr(merged, "geoms", [merged]):
        if part.geom_type == "Polygon" and part.buffer(1e-6).contains(here):
            ring = orient(Polygon(part.exterior.coords).simplify(1e-6), 1.0)
            return [tuple(c) for c in list(ring.exterior.coords)[:-1]], z
    return None


def upright_face(doc, obj_id, face_index, point):
    """(0.436, the addon's «Fachada de vidro por face») The upright rectangle that frames an upright face under a click
    — of a sketch volume or an element — with the faces beside it on the same plane: (a, b, height, normal) — a, b the
    ends of its bottom edge (at its lowest, in the plane), normal level and out of it — or None (a level or sloping
    face, nothing there)."""
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    from ..core.mesh import polygon_normal
    obj = doc.get(obj_id)
    mesh = getattr(obj, "mesh", None)
    if obj is None or mesh is None or face_index is None or face_index >= len(mesh.faces):
        return None
    verts = np.asarray(mesh.verts, dtype=float)
    if not obj.is_bim and getattr(obj, "matrix", None) is not None:
        verts = (np.column_stack((verts, np.ones(len(verts)))) @ np.asarray(obj.matrix, dtype=float).T)[:, :3]
    faces = mesh.faces
    normals = getattr(mesh, "normals", None)

    def normal_of(fi):
        if obj.is_bim and normals is not None:
            return np.asarray(normals[fi], dtype=float)
        return polygon_normal(verts[list(faces[fi])])

    n = normal_of(face_index)
    if np.linalg.norm(n) < 1e-9 or abs(n[2]) > 0.02 * np.linalg.norm(n):
        return None
    n = np.array((n[0], n[1], 0.0)) / np.linalg.norm(n[:2])
    d = float(n @ verts[list(faces[face_index])][0])
    along = np.array((-n[1], n[0], 0.0))
    if obj.is_bim and normals is not None:            # (an element's triangles: those on its plane, at once)
        tris = np.asarray(faces, dtype=np.int64)
        cand = np.nonzero(np.asarray(normals, dtype=float) @ n >= 0.9995)[0]
        on = cand[np.abs(verts[tris[cand]] @ n - d).max(axis=1) <= 1e-4] if len(cand) else cand
        rings = [verts[tris[fi]] for fi in on]
    else:                                             # (a sketch's faces, each its own polygon)
        rings = [verts[list(faces[fi])] for fi in range(len(faces)) if float(normal_of(fi) @ n) >= 0.9995]
        rings = [pts for pts in rings if np.abs(pts @ n - d).max() <= 1e-4]
    parts = []
    for pts in rings:                                 # (the faces on its plane, as its outline in it: along, up)
        poly = Polygon([(float(q @ along), float(q[2])) for q in pts])
        if poly.area > 1e-9:
            parts.append(poly.buffer(1e-6))
    if not parts:
        return None
    merged = unary_union(parts)
    here = Point(float(np.asarray(point, dtype=float) @ along), float(point[2]))
    region = next((q for q in getattr(merged, "geoms", [merged]) if q.buffer(1e-4).contains(here)), None)
    if region is None:
        return None
    u0, z0, u1, z1 = region.bounds
    if u1 - u0 < 0.05 or z1 - z0 < 0.05:
        return None
    base = n * d
    a = base + along * u0
    b = base + along * u1
    a[2] = b[2] = z0
    return a, b, z1 - z0, n


def wall_spec_for(thickness):
    """(0.159) The wall type for a thickness drawn: the catalogue's or the project's of that thickness (to 5 mm),
    else a new one — plastered masonry from 10 cm, a board under that. (0.342) Not a load-bearing concrete one: a
    drawing does not say a wall is of concrete (and such a wall is load-bearing as made)."""
    from ..ifc.catalog import TypeSpec
    walls = [s for s in catalog.types() if s.kind == "wall" and not catalog.load_bearing_wall(s)]
    near = min(walls, key=lambda s: abs(s.thickness - thickness), default=None)
    if near is not None and abs(near.thickness - thickness) <= 0.005:
        return near
    cm = round(thickness * 100, 1)
    label = ("{:g}".format(cm)).replace(".", ",")
    key = "parede_cad_{}".format(int(round(thickness * 1000)))
    if key in catalog.BY_KEY:
        return catalog.BY_KEY[key]
    if thickness >= 0.10:
        layers = (("reboco", 0.015), ("bloco", round(thickness - 0.03, 4)), ("reboco", 0.015))
    else:
        layers = (("gesso", round(thickness, 4)),)
    spec = TypeSpec(key, "wall", "Parede {} cm".format(label), "Wall {} cm".format(label.replace(",", ".")),
                    layers=layers)
    catalog.add_project_type(spec)
    return spec


def column_spec_for(width, depth, round_=False):
    """(0.211) The column type for a section drawn (width along its way, depth across; round: a circle of that
    diameter): the catalogue's or the project's of that size (to 5 mm) — turned a quarter when its sides are the
    other way round —, else a new concrete one. Returns (type, turned)."""
    from ..ifc.catalog import TypeSpec
    shape = "circle" if round_ else None
    for spec in catalog.types():
        if spec.kind != "column" or spec.shape != shape or not spec.profile:
            continue
        w, d = spec.profile[:2]
        if abs(w - width) <= 0.005 and abs(d - depth) <= 0.005:
            return spec, False
        if not round_ and abs(w - depth) <= 0.005 and abs(d - width) <= 0.005:
            return spec, True
    cw, cd = int(round(width * 100)), int(round(depth * 100))
    key = "pilar_cad_circ_{}".format(cw) if round_ else "pilar_cad_{}x{}".format(cw, cd)
    if key in catalog.BY_KEY:
        return catalog.BY_KEY[key], False
    if round_:
        spec = TypeSpec(key, "column", "Pilar circular Ø{}".format(cw), "Round column Ø{}".format(cw),
                        profile=(cw / 100.0, cw / 100.0), material="concreto", shape="circle")
    else:
        spec = TypeSpec(key, "column", "Pilar de concreto {}×{}".format(cw, cd), "Concrete column {}×{}".format(cw, cd),
                        profile=(cw / 100.0, cd / 100.0), material="concreto")
    catalog.add_project_type(spec)
    return spec, False


def _footing_kind(doc, guid, centre, x_dir):
    """(0.228) What a footing is, for core.structural.Footing: a pad; a pile cap with its piles (from its middle,
    along its own x / y) and their diameter; a strip under its wall, with the wall's weight per metre."""
    from . import structure_loads
    import ifcopenshell.util.element as ue
    x = np.asarray(x_dir, dtype=float)[:2]
    x = x / np.linalg.norm(x)
    y = np.array((-x[1], x[0]))
    out = {"x_dir": (float(x[0]), float(x[1]))}
    predefined = ue.get_predefined_type(doc.ifc.by_guid(guid))
    params = doc.ifc._params(doc.ifc.by_guid(guid))
    if params.get("Apoia2"):                            # (0.250) a combined footing: its two columns
        spots = []
        for g in (params.get("Apoia"), params.get("Apoia2")):
            if g and doc.get(g) is not None:
                p = doc.ifc.placement(g)[:2, 3]
                spots.append((float(p[0]), float(p[1])))
        if len(spots) == 2:
            out.update(kind="combined", columns=tuple(spots))
            return out
    if predefined == "PILE_CAP":
        spots, diameter = [], 0.0
        for g in doc.ifc.footings_of([guid]).get(guid, []):
            if doc.ifc.by_guid(g).is_a("IfcPile"):
                p = doc.ifc.placement(g)[:2, 3] - np.asarray(centre, dtype=float)[:2]
                spots.append((float(p @ x), float(p @ y)))
                diameter = max(diameter, doc.ifc.pile_diameter(g))
        out.update(kind="cap", piles=tuple(spots), pile_d=diameter)
    elif predefined == "STRIP_FOOTING":
        wall = doc.ifc._params(doc.ifc.by_guid(guid)).get("Apoia") or ""
        load, thickness = 0.0, 0.0
        if wall and doc.get(wall) is not None and doc.ifc.kind_of(wall) == "wall":
            s, e, thickness = doc.ifc.wall_axis(wall)
            span = float(np.linalg.norm((e - s)[:2]))
            if span > 1e-6:
                load = abs(doc.get(wall).mesh.volume()) * structure_loads.WALL_KN_M3 / span
        out.update(kind="strip", wall=wall, wall_t=float(thickness), line_load=load)
    return out


def structural_elements(doc):
    """(0.163) The physical structure as core.structural reads it: (columns, beams, footings, panels, levels) — the
    columns, beams, footings and structural slabs made by this program."""
    from ..core import structural as st
    kinds = {}
    for obj in doc.objects.values():
        if obj.is_bim and obj.ifc_class in ("IfcColumn", "IfcBeam", "IfcFooting", "IfcSlab"):
            kinds[obj.id] = doc.ifc.kind_of(obj.id)
    hatches = doc.ifc.hatches(sorted(kinds)) if kinds else {}
    material = lambda g: "concrete" if hatches.get(g) in ("concrete", None) else hatches.get(g)   # noqa: E731
    columns, beams, footings, panels = [], [], [], []
    for guid, kind in sorted(kinds.items()):
        try:
            if kind == "column":
                centre, x_dir, (a, b), base, top = doc.ifc.column_box(guid)
                shape, web = doc.ifc.column_section(guid)                 # (0.227: round, L, T)
                columns.append(st.Column(guid, (float(centre[0]), float(centre[1])), base, top, (2 * a, 2 * b),
                                         material(guid), shape, web, (float(x_dir[0]), float(x_dir[1]))))
            elif kind == "beam":
                start, end, top, width, height = doc.ifc.beam_params(guid)
                beams.append(st.Beam(guid, (float(start[0]), float(start[1])), (float(end[0]), float(end[1])), top,
                                     (width, height), material(guid)))
            elif kind == "footing":
                centre, x_dir, length, width, top = doc.ifc.footing_params(guid)
                depth = top - float(doc.ifc.placement(guid)[2, 3])          # (its placement: its underside)
                footings.append(st.Footing(guid, (float(centre[0]), float(centre[1])), top, (length, width),
                                           depth, **_footing_kind(doc, guid, centre, x_dir)))
            elif kind == "slab":
                info = doc.ifc.slab_outline(guid)
                if info is not None and info.get("function", "estrutural") == "estrutural":
                    panels.append(st.Panel(guid, list(info["outline"]), float(info["top"]), float(info["thickness"])))
        except (KeyError, TypeError, ValueError, AttributeError, IndexError):
            continue                                        # (an element this program did not make as such)
    levels = [z for _g, _n, z in doc.ifc.storeys()]
    return columns, beams, footings, panels, levels


def structural_walls(doc):
    """(0.335) The load-bearing walls — those marked so (Pset_WallCommon.LoadBearing) — as core.structural reads them:
    [Wall], the straight ones this program made: their axis, base and top, their load-bearing layer (the one whose
    function in its type is the structure, else the thickest), their material (concrete or masonry), their doors' and
    windows' openings."""
    from ..core import structural as st
    guids = sorted(o.id for o in doc.objects.values() if o.is_bim and o.ifc_class in ("IfcWall", "IfcWallStandardCase"))
    bearing = doc.ifc.property_values(guids, ("pset", "Pset_WallCommon", "LoadBearing")) if guids else {}
    chosen = [g for g in guids if bearing.get(g) is True]
    if not chosen:
        return []
    hatches = doc.ifc.hatches(chosen, own=False)        # (its main material's category: concrete or not)
    cores = _wall_cores(doc, chosen)
    masonry = _wall_masonry(doc, chosen)                # (0.346: its type's, for Eurocode 6)
    out = []
    for guid in chosen:
        try:
            if doc.ifc.kind_of(guid) != "wall":
                continue                                    # (a curved wall, one of another program's: not yet)
            s, e, thickness = doc.ifc.wall_axis(guid)
            box = doc.get(guid).mesh.bounds()
            if box is None:
                continue
            base, top = float(box[0][2]), float(box[1][2])
            core = cores.get(guid, 0.0)
            openings = []
            for f in _fillings(doc, guid):
                state = doc.ifc.filling_state(f)
                openings.append((state["s"], state["s"] + state["width"], base + state["sill"],
                                 base + state["sill"] + state["height"]))
            out.append(st.Wall(guid, (float(s[0]), float(s[1])), (float(e[0]), float(e[1])), base, top,
                               float(thickness), float(core), "concrete" if hatches.get(guid) == "concrete"
                               else "masonry", tuple(openings), masonry.get(guid)))
        except (KeyError, TypeError, ValueError, AttributeError, IndexError, RuntimeError):
            continue
    return out


def _wall_masonry(doc, guids):
    """(0.346) {GlobalId: its type's own masonry for Eurocode 6 — (units, group, fb, mortar) — or None: the
    project's} of these walls."""
    import ifcopenshell.util.element
    from ..core import ec6
    out, seen = {}, {}
    for guid in guids:
        e = doc.ifc.by_guid(guid)
        type_ = ifcopenshell.util.element.get_type(e) if e is not None else None
        if type_ is None:
            out[guid] = None
            continue
        if type_.id() not in seen:
            seen[type_.id()] = ec6.decode(doc.ifc._params(type_).get("Alvenaria"))
        out[guid] = seen[type_.id()]
    return out


def _wall_cores(doc, guids):
    """{GlobalId: the thickness of its load-bearing layer} (m) of these walls: the layers whose function in its type
    is the structure (the strongest), else its thickest one (0: none known)."""
    layers = doc.ifc.layers(guids, single=True)
    strengths = doc.ifc.layer_strengths(guids)
    out = {}
    for guid in guids:
        spans = [abs(d1 - d0) for _k, _n, d0, d1 in layers.get(guid, ())]
        given = strengths.get(guid) or [None] * len(spans)
        if spans and any(v is not None for v in given):
            best = min(v for v in given if v is not None)
            out[guid] = sum(t for t, v in zip(spans, given) if v == best)
        else:
            out[guid] = max(spans, default=0.0)
    return out


FACADE_TOP = 0.10               # (0.345) m: a slab, beam or roof this near a wall's top holds it…
FACADE_END = 0.05               # …a column or a wall this near its end (beyond their faces) holds that side


def facade_walls(doc):
    """(0.345) The masonry walls of the façades — straight walls outside (Pset_WallCommon.IsExternal), not of
    concrete — as their bending out of their plane under the wind needs them: [dict] with guid, start, end (plan),
    base, top, t (the masonry's thickness: its load-bearing layer), whole (its area) and openings (theirs, m²),
    bearing (load-bearing), held (top, at its start, at its end: a slab, beam or roof on it; a column or another wall
    at that end)."""
    guids = sorted(o.id for o in doc.objects.values() if o.is_bim and o.ifc_class in ("IfcWall", "IfcWallStandardCase"))
    if not guids:
        return []
    outside = doc.ifc.property_values(guids, ("pset", "Pset_WallCommon", "IsExternal"))
    if not any(outside.get(g) is True for g in guids):
        return []
    bearing = doc.ifc.property_values(guids, ("pset", "Pset_WallCommon", "LoadBearing"))
    axes = {}
    for guid in guids:                                  # (every straight wall: the façade's may be held by them)
        try:
            box = doc.get(guid).mesh.bounds()
            if box is None or doc.ifc.kind_of(guid) != "wall":
                continue
            s, e, thickness = doc.ifc.wall_axis(guid)
            axes[guid] = (np.asarray(s[:2], dtype=float), np.asarray(e[:2], dtype=float), float(thickness),
                          float(box[0][2]), float(box[1][2]))
        except (KeyError, TypeError, ValueError, AttributeError, IndexError, RuntimeError):
            continue
    chosen = [g for g in guids if outside.get(g) is True and g in axes]
    if not chosen:
        return []
    hatches = doc.ifc.hatches(chosen, own=False)
    chosen = [g for g in chosen if hatches.get(g) != "concrete"]
    cores = _wall_cores(doc, chosen)
    masonry = _wall_masonry(doc, chosen)                # (0.346: its type's, for Eurocode 6)

    def boxes(classes):                                 # (lows (N, 3), highs (N, 3))
        found = [o.mesh.bounds() for o in doc.objects.values() if o.is_bim and o.ifc_class in classes
                 and o.mesh.bounds() is not None]
        return (np.array([b[0] for b in found], dtype=float).reshape(-1, 3),
                np.array([b[1] for b in found], dtype=float).reshape(-1, 3))

    over, columns = boxes(("IfcSlab", "IfcBeam", "IfcRoof")), boxes(("IfcColumn",))
    order = list(axes)                                  # (every straight wall, as arrays: their ends, thickness, z)
    starts = np.array([axes[g][0] for g in order]).reshape(-1, 2)
    spans = np.array([axes[g][1] for g in order]).reshape(-1, 2) - starts
    halves = np.array([axes[g][2] / 2.0 for g in order])
    lows, highs = np.array([axes[g][3] for g in order]), np.array([axes[g][4] for g in order])
    square = np.maximum(np.einsum("ij,ij->i", spans, spans), 1e-12)

    def inside(box, p, grow):                           # (which of the boxes have the point in plan)
        return (box[0][:, 0] - grow <= p[0]) & (p[0] <= box[1][:, 0] + grow) & \
            (box[0][:, 1] - grow <= p[1]) & (p[1] <= box[1][:, 1] + grow)

    index = {g: k for k, g in enumerate(order)}
    out = []
    for guid in chosen:
        s, e, thickness, base, top = axes[guid]
        half = thickness / 2.0
        reach = (over[0][:, 2] <= top + FACADE_TOP) & (over[1][:, 2] >= top - 0.02) & (over[0][:, 2] >= base + 0.5)
        held_top = bool(np.any(reach & np.any([inside(over, s + (e - s) * k, half) for k in (0.25, 0.5, 0.75)],
                                              axis=0)))
        tall = np.minimum(top, highs) - np.maximum(base, lows) >= (top - base) / 2.0
        tall[index[guid]] = False                       # (not itself)
        ends = []
        for p in (s, e):
            column = bool(np.any((columns[0][:, 2] < top) & (columns[1][:, 2] > base) &
                                 inside(columns, p, half + FACADE_END)))
            k = np.clip(np.einsum("ij,ij->i", p - starts, spans) / square, 0.0, 1.0)
            near = np.hypot(*(starts + k[:, None] * spans - p).T) <= half + halves + FACADE_END
            ends.append(column or bool(np.any(near & tall)))
        length = float(np.linalg.norm(e - s))
        along = (e - s) / max(length, 1e-9)
        area = 0.0
        for f in _fillings(doc, guid):                  # (each door's and window's size, from its own shape)
            obj = doc.get(f)
            verts = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3) if obj is not None and obj.mesh else None
            if verts is not None and len(verts):
                width = verts[:, :2] @ along
                area += float(width.max() - width.min()) * float(verts[:, 2].max() - verts[:, 2].min())
        out.append({"guid": guid, "start": tuple(s), "end": tuple(e), "base": base, "top": top,
                    "t": cores.get(guid) or thickness, "whole": length * (top - base), "openings": area,
                    "bearing": bearing.get(guid) is True, "held": (held_top, ends[0], ends[1]),
                    "masonry": masonry.get(guid)})
    return out


def analytical_model(doc):
    """(0.163) The analytical model made again from the physical structure, checked, and written to the IFC
    (IfcStructuralAnalysisModel): one undo step. Returns the core.structural.AnalyticalModel (its issues). (0.335)
    With the load-bearing walls."""
    from ..core import structural as st
    columns, beams, footings, panels, levels = structural_elements(doc)
    model = st.build(columns, beams, footings, panels, levels, structural_walls(doc))
    doc.execute(IfcCommand(t("cmd.analytical"), lambda ifc: ifc.write_analysis_model(model, t("elem.analytical"))))
    return model


def actions_of(doc, settings, elements=None):
    """(0.164) The analytical model and its actions with these settings, worked out — nothing written. elements:
    structural_elements(doc), when already read."""
    from ..core import structural as st
    from . import structure_loads
    columns, beams, footings, panels, levels = elements or structural_elements(doc)
    model = st.build(columns, beams, footings, panels, levels, structural_walls(doc))      # (0.335: its walls)
    walls = []
    for obj in doc.objects.values():
        if obj.is_bim and obj.ifc_class in ("IfcWall", "IfcWallStandardCase") and obj.mesh.bounds() is not None:
            lo, hi = obj.mesh.bounds()
            walls.append((abs(obj.mesh.volume()), float(lo[2]), float(hi[2])))
    foundation = min([c.base for c in columns] + [min(levels) if levels else 0.0])
    uses = {p.guid: doc.ifc.slab_use(p.guid) for p in panels}                       # (0.218: each slab's own)
    return model, structure_loads.building_actions(model, settings, walls, foundation,
                                                   {g: u for g, u in uses.items() if u})


def analyse_structure(doc, settings=None):
    """(0.165) The structure analysed with its settings (the project's, kept in the IFC): (analytical model, its
    loads, model.structure_analysis.Analysis). Nothing written."""
    from . import structure_analysis
    settings = settings or doc.ifc.structural_settings()
    model, loads = actions_of(doc, settings)
    return model, loads, structure_analysis.analyse(model, loads, settings)


def design_structure(doc, settings=None):
    """(0.166) The structure analysed and each of its concrete members verified by Eurocode 2, its reinforcement
    chosen: (analytical model, loads, Analysis, [model.structure_design.ElementDesign]). Nothing written."""
    from . import structure_analysis, structure_design
    settings = settings or doc.ifc.structural_settings()
    elements = structural_elements(doc)
    model, loads = actions_of(doc, settings, elements)
    analysis = structure_analysis.analyse(model, loads, settings)
    _columns, beams, footings, _panels, _levels = elements
    designs = structure_design.design_structure(model, analysis, loads, settings, beams, footings)
    from . import wall_lateral                          # (0.345) the façade walls out of their plane, by the wind
    designs = wall_lateral.check(facade_walls(doc), settings, designs, getattr(analysis, "walls", ()) or ())
    return model, loads, analysis, structure_design.unify_typical(designs, _typical_equals(doc, designs))


def _typical_equals(doc, designs):
    """(0.231) {GlobalId: the key of its equals} of the members on typical floors (a typical floor's group copies:
    the same role in each) — the lowest GlobalId of them, the same for all."""
    out = {}
    for e in designs:
        group = doc.ifc.group_of(e.guid)
        if group is None or not doc.ifc._params(group).get("Pavimento"):
            continue                                    # (an ordinary group's copies keep their own bars)
        out[e.guid] = min([e.guid] + doc.ifc.counterparts(e.guid))
    return out


def make_rebars(doc, designs, settings=None):
    """(0.166) The reinforcement of the members verified (not those that fail) put in the model: on each, its sets of
    bars (IfcReinforcingBar), those it had replaced; the positions numbered. One undo step. Returns (members,
    bars)."""
    from ..core import ec2
    settings = settings or doc.ifc.structural_settings()
    from . import design_text
    stored = {e.guid: e.stored(settings) for e in designs if e.design.status != ec2.FAIL
              and not design_text.masonry(e)}           # (0.337: a masonry wall has no bars; 0.342: a concrete one has)
    if not stored:
        return 0, 0
    language = lang()
    made = set(doc.execute(IfcCommand(t("cmd.rebars"), lambda ifc: ifc.write_rebars(stored, language))).result)
    return len(stored), sum(r["count"] for r in doc.ifc.rebar_rows() if r["guid"] in made)


def put_mesh(doc, hosts, mesh):
    """(0.522) A welded mesh (core.rebar_mesh.Mesh) on these slabs, the one each had replaced. One undo step.
    Returns the IfcReinforcingMeshes made."""
    hosts = [g for g in hosts if doc.ifc.by_guid(g) is not None and doc.ifc.by_guid(g).is_a("IfcSlab")]
    if not hosts:
        return []
    language = lang()
    return doc.execute(IfcCommand(t("cmd.mesh"), lambda ifc: ifc.write_meshes(hosts, mesh, language))).result or []


def remove_meshes(doc, hosts=None):
    """(0.522) The welded meshes of these slabs (None: all) taken out. One undo step. False if none."""
    if not doc.ifc.meshes_of(hosts):
        return False
    hosts = list(doc.ifc.meshes_of(hosts))
    doc.execute(IfcCommand(t("cmd.remove_mesh"), lambda ifc: ifc.remove_meshes(hosts)))
    return True


def remove_rebars(doc, hosts=None):
    """(0.166) The reinforcement of these members (None: all of it) taken out. One undo step. False if none."""
    if hosts is None:
        hosts = sorted({doc.ifc._params(e).get("Armadura") for e in doc.ifc.file.by_type("IfcReinforcingBar")} - {None})
    if not doc.ifc.rebars_of(hosts):
        return False
    doc.execute(IfcCommand(t("cmd.remove_rebars"), lambda ifc: ifc.remove_rebars(hosts)))
    return True


def structure_quantities(doc):
    """(0.167) [model.structure_quantities.QuantityRow] of the structure's concrete members: their concrete (their
    shapes' volume), formwork and steel (of the bars in the model)."""
    from . import structure_quantities as sq
    columns, beams, footings, panels, _levels = structural_elements(doc)
    steel, has = {}, set()
    for r in doc.ifc.rebar_rows() + mesh_schedule_rows(doc):        # (0.523: the meshes' steel too)
        if r["host"]:
            steel[r["host"]] = steel.get(r["host"], 0.0) + r["weight"]
            has.add(r["host"])
    storeys = {g: n for g, n, _z in doc.ifc.storeys()}

    def row(guid, kind, form):
        obj = doc.get(guid)
        volume = abs(obj.mesh.volume()) if obj is not None and obj.is_bim else 0.0
        return sq.QuantityRow(guid, kind, storeys.get(doc.ifc.storey_of(guid), ""), volume, form,
                              steel.get(guid, 0.0), guid in has)

    out = [row(c.guid, "column", sq.formwork("column", c.size, c.top - c.base)) for c in columns]
    out += [row(b.guid, "beam", sq.formwork("beam", b.size, float(np.hypot(b.end[0] - b.start[0],
                                                                            b.end[1] - b.start[1]))))
            for b in beams]
    for p in panels:
        from shapely.geometry import Polygon
        poly = Polygon(p.outline)
        out.append(row(p.guid, "slab", sq.formwork("slab", area=poly.area, perimeter=poly.length,
                                                   thickness=p.thickness)))
    out += [row(f.guid, "footing", sq.formwork("footing", perimeter=2.0 * (f.size[0] + f.size[1]),
                                               thickness=f.depth)) for f in footings]
    for w in structural_walls(doc):                     # (0.342) the load-bearing concrete walls
        if w.material != "concrete":
            continue
        height = w.top - w.base
        face = w.length * height - sum((s1 - s0) * (z1 - z0) for s0, s1, z0, z1 in w.openings)
        reveals = sum(2.0 * ((s1 - s0) + (z1 - z0)) for s0, s1, z0, z1 in w.openings)
        out.append(row(w.guid, "wall", sq.formwork("wall", area=face, perimeter=2.0 * height + reveals,
                                                   thickness=w.thickness)))
    return out


def report_data(doc, settings=None):
    """(0.167) What the calculation report is made of (model.structure_report.report_html): the project, the
    structure designed, its quantities, its reinforcement."""
    import datetime
    from .. import __version__
    settings = settings or doc.ifc.structural_settings()
    model, loads, analysis, designs = design_structure(doc, settings)
    projects = doc.ifc.file.by_type("IfcProject")
    project = {k: v for k, v in (doc.title_block or {}).items() if isinstance(v, str) and v}
    project.setdefault("project", (projects[0].Name if projects else "") or "")
    names = {o.id: o.name for o in doc.objects.values() if o.is_bim}
    import ifcopenshell.util.element                    # (0.346) the wall types with masonry of their own
    walls = [e.guid for e in designs if e.kind == "wall"]
    own_masonry = {}
    for guid, masonry in _wall_masonry(doc, walls).items():
        if masonry:
            type_ = ifcopenshell.util.element.get_type(doc.ifc.by_guid(guid))
            own_masonry[type_.Name or ""] = masonry
    return {"project": project, "date": datetime.date.today().strftime("%d-%m-%Y"), "version": __version__,
            "settings": settings, "model": model, "loads": loads, "analysis": analysis, "designs": designs,
            "names": names, "quantities": structure_quantities(doc), "rebars": rebar_schedule(doc),
            "drawings": _report_drawings(doc, names), "masonry_types": sorted(own_masonry.items())}


def _report_drawings(doc, names):
    """(0.233) [(element name, its reinforcement drawing as SVG, 1:50 — 0.234: and its section's, 1:20, beside it)]
    of the members with bars in the model, columns first, then beams, slabs, footings — each by name."""
    from . import design_text as dt
    from . import drawing_svg, rebar_drawings
    order = {"column": 0, "beam": 1, "slab": 2, "footing": 3, "wall": 4}
    hosts = sorted(doc.ifc.rebars_of(list(names)), key=lambda g: (order.get(doc.ifc.kind_of(g), 9),
                                                                    dt.natural(names.get(g, g))))
    out = []
    for g in hosts:
        drawing = rebar_drawings.apply_moves(doc, rebar_drawings.rebar_drawing(doc, g, names.get(g, g)),
                                             ("rebar", g))                  # (0.238: its labels as on its sheet)
        if drawing is not None:
            cut = rebar_drawings.rebar_drawing(doc, g, names.get(g, g), cut=True)
            out.append((names.get(g, g), drawing_svg.svg(drawing, rebar_drawings.TEXT_SCALE)
                        + (drawing_svg.svg(cut, rebar_drawings.CUT_SCALE) if cut is not None else "")))
    from . import rebar_details                         # (0.237) and the typical details, last
    details = rebar_details.details_drawing(doc, "") if out else None
    if details is not None:
        out.append((t("tree.rebar_details_view"), drawing_svg.svg(details, rebar_details.SCALE)))
    return out


def mesh_schedule_rows(doc):
    """(0.523) The welded meshes as rows of the bar schedule: marked M1, M2… (one per mesh of a diameter and spacing),
    their sheets (6,00 m long each) as the count, «Ø8//0,15» as the shape, their weight."""
    from ..core import rebar_mesh as rm
    out, marks = [], {}
    for r in doc.ifc.mesh_rows():
        mark = marks.setdefault((r["diameter"], round(r["spacing"], 3)), "M{}".format(len(marks) + 1))
        out.append({"mark": mark, "guid": r["guid"], "host": r["host"], "host_name": r["host_name"],
                    "role": "mesh_" + r["face"], "diameter": r["diameter"], "count": r["sheets"],
                    "length": rm.SHEET[0], "spacing": r["spacing"], "bends": "",
                    "shape": rm.Mesh(r["diameter"], r["spacing"]).name(",").replace(" ", ""),
                    "weight": r["weight"]})
    return out


def rebar_schedule(doc):
    """(0.166) The bar schedule: (rows by position — model.ifc rebar_rows —, {diameter mm: (m, kg)} totals)."""
    rows = doc.ifc.rebar_rows() + mesh_schedule_rows(doc)        # (0.523: the welded meshes after the bars)
    totals = {}
    for r in rows:
        m, kg = totals.get(r["diameter"], (0.0, 0.0))
        totals[r["diameter"]] = (m + r["count"] * r["length"], kg + r["weight"])
    return rows, dict(sorted(totals.items()))


def structural_actions(doc, settings=None):
    """(0.164) The structure's actions: its settings (when given) kept in the IFC, the analytical model made again,
    the gravity loads on it (cases G and Q in the IFC), the wind and seismic forces worked out. One undo step.
    Returns (core.structural.AnalyticalModel, model.structure_loads.BuildingActions)."""
    settings = settings or doc.ifc.structural_settings()
    model, loads = actions_of(doc, settings)

    def action(ifc):
        ifc.set_structural_settings(settings)
        ifc.write_analysis_model(model, t("elem.analytical"))
        ifc.write_loads(loads)

    doc.execute(IfcCommand(t("cmd.actions"), action))
    return model, loads


def save_analysis_results(doc, settings=None):
    """(0.221) The structure analysed and its results written in the IFC with the analytical model and its loads
    they belong to (made again): the combination, the supports' reactions, the members' moments
    (IfcStructuralResultGroup). One undo step. Returns the Analysis (its error, when it could not be done: nothing
    written)."""
    from . import structure_analysis
    settings = settings or doc.ifc.structural_settings()
    model, loads = actions_of(doc, settings)
    analysis = structure_analysis.analyse(model, loads, settings)
    if analysis.error:
        return analysis

    def action(ifc):
        ifc.write_analysis_model(model, t("elem.analytical"))
        ifc.write_loads(loads)
        ifc.write_results(analysis)

    doc.execute(IfcCommand(t("cmd.results"), action))
    return analysis


def opening_spec_for(kind, width, height=None, sill=None):
    """(0.160) The door / window type for a width drawn: the project's of that width (to 5 cm), else a new one — a
    door 2,10 m high, a window 1,20 m on a 1,00 m sill. (0.212) height, sill: as written beside it on the drawing
    (None: any) — the type of that height (and sill) too, to 2 cm."""
    from ..ifc.catalog import OpeningSpec
    tall = 2.10 if kind == "door" else 1.20
    height = None if height is None or not 0.3 <= float(height) <= 4.0 else float(height)
    sill = None if kind == "door" or sill is None or not 0.0 <= float(sill) <= 3.0 else float(sill)
    same = [o for o in catalog.openings() if o.kind == kind
            and (height is None or abs(o.height - height) <= 0.02)
            and (sill is None or abs(float(o.sill or 0.0) - sill) <= 0.02)]
    near = min(same, key=lambda o: abs(o.width - width), default=None)
    if near is not None and abs(near.width - width) <= 0.05:
        return near
    cm = int(round(width * 100))
    h_cm = int(round((height if height is not None else tall) * 100))
    s_cm = int(round((sill if sill is not None else 1.00) * 100))
    key = "{}_cad_{}".format("porta" if kind == "door" else "janela", cm)
    if height is not None or sill is not None:
        key += "x{}".format(h_cm) + ("" if kind == "door" else "_p{}".format(s_cm))
    if key in catalog.OPENING_BY_KEY:
        return catalog.OPENING_BY_KEY[key]
    sill_text = "{:.2f}".format(s_cm / 100.0)
    if kind == "door":
        spec = OpeningSpec(key, "door", "Porta {}×{}".format(cm, h_cm), "Door {}×{}".format(cm, h_cm), cm / 100.0,
                           h_cm / 100.0, operation="SINGLE_SWING_LEFT")
    else:
        spec = OpeningSpec(key, "window", "Janela {}×{} (peitoril {})".format(cm, h_cm, sill_text.replace(".", ",")),
                           "Window {}×{} (sill {})".format(cm, h_cm, sill_text), cm / 100.0, h_cm / 100.0,
                           sill=s_cm / 100.0, operation="SINGLE_PANEL", lining_depth=0.10)
    catalog.add_project_opening(spec)
    return spec


def walls_from_axes(doc, axes, height=WALL_HEIGHT, storey=None, level=None):
    """(0.159) Walls along axes found in a drawing — [(start (2,), end (2,), thickness)] — each of the type of its
    thickness, joined at its corners and T junctions to those made before it and to the walls already there. One
    undo step. Returns their GlobalIds."""
    return model_from_cad(doc, axes, height=height, storey=storey, level=level)["walls"]


def model_from_cad(doc, axes, openings=(), furniture=(), height=WALL_HEIGHT, storey=None, level=None, slab=None,
                   arcs=(), columns=()):
    """(0.159, 0.160) A drawing's walls, openings and furniture in one undo step: the walls along the axes found
    (walls_from_axes); each door / window block in the wall it lies in, of the type of its width, where it was
    drawn, opening to the side its swing was drawn on; each furniture block a component (one per block) placed where
    it was inserted, turned as it was. openings: [(cad_openings.BlockInstance, "door" | "window")]; furniture:
    cad_openings.furniture_items. slab (0.162): (outline [(x, y)], type) — the floor's slab under it all. arcs
    (0.210): the curved walls found (cad_walls.arc_walls: centre, radius, start, sweep, thickness). columns (0.211):
    cad_columns.columns — each a column as high as the walls, of the type of its section. Returns
    {"walls", "doors", "windows", "furniture", "slabs": [GlobalId], "left": n of the openings that fell in no
    wall}."""
    from ..core import cad_openings
    from ..core.openings import clamp_s, fits
    from ..core.walls import find_joint
    storey = storey or doc.active_storey
    z = next((lv for g, _n, lv in doc.ifc.storeys() if g == storey), 0.0) if level is None else level
    language, prefix = lang(), t("elem.wall")
    cmd = IfcCommand(t("cmd.walls_from_cad"), None)
    known = list(wall_axes(doc))

    # the longest first: the walls a shorter one meets (at a T) are there when it is made, so it stops at their face
    ordered = sorted(axes, key=lambda w: -float(np.hypot(w[1][0] - w[0][0], w[1][1] - w[0][1])))

    def make_openings(ifc, walls, report):
        for inst, kind in openings:
            found = None
            for wall in walls:
                s_, e_, th = ifc.wall_axis(wall)
                span = cad_openings.span_on(inst, s_, e_, th)
                if span is not None:
                    found = (wall, np.asarray(s_, dtype=float), np.asarray(e_, dtype=float), span)
                    break
            if found is None:
                report["left"] += 1
                continue
            wall, s_, e_, (s0, s1, side) = found
            d = (e_ - s_) / max(float(np.linalg.norm((e_ - s_)[:2])), 1e-12)
            frame = ifc.element_frame(wall)
            x0, x1 = sorted((frame.to_local(s_ + d * s0)[0], frame.to_local(s_ + d * s1)[0]))
            spec = opening_spec_for(kind, x1 - x0, getattr(inst, "height", None), getattr(inst, "sill", None))
            if not fits(frame, spec.width, spec.height, spec.sill):
                report["left"] += 1
                continue
            s = clamp_s(frame, x0 + (x1 - x0 - spec.width) / 2, spec.width)
            cls = "IfcDoor" if kind == "door" else "IfcWindow"
            name = "{} {}".format(t("elem." + kind), ifc.count(cls) + 1)
            new = ifc.add_opening(wall, spec, frame, s, side or -1, name, language)
            report["doors" if kind == "door" else "windows"].append(new.GlobalId)
            cmd.changed.append(wall)

    def make_furniture(ifc, report):
        types = {}
        for block, outline, at, angle in furniture:
            a = np.radians(angle)
            matrix = np.eye(4)
            matrix[:2, :2] = ((np.cos(a), -np.sin(a)), (np.sin(a), np.cos(a)))
            matrix[:3, 3] = (at[0], at[1], z)
            if block in types:
                inst = ifc.add_component_instance(types[block], matrix, storey)
            else:
                verts, faces = cad_openings.prism(outline, cad_openings.furniture_height(block))
                inst = ifc.create_component(block, "furniture", verts, faces, matrix, storey)
                types[block] = ifc.component_type(inst.GlobalId)
            report["furniture"].append(inst.GlobalId)

    def action(ifc):
        made = []
        for a, b, thickness in ordered:
            spec = wall_spec_for(thickness)
            start = np.array((float(a[0]), float(a[1]), float(z)))
            end = np.array((float(b[0]), float(b[1]), float(z)))
            direction = horizontal_dir(start, end)
            if direction is None:
                continue
            sj = find_joint(start, direction, known, spec.thickness)
            ej = find_joint(end, direction, known, spec.thickness)
            guid = _make_wall(ifc, start, end, spec, height, None, None, sj and sj[:3], ej and ej[:3], storey,
                              language, prefix, cmd.changed)
            made.append(guid)
            for k, (g, _s, _e, _t) in enumerate(known):      # (the walls it joined were trimmed / extended)
                if g in cmd.changed:
                    known[k] = (g,) + tuple(ifc.wall_axis(g))
            known.append((guid,) + tuple(ifc.wall_axis(guid)))
        straight = list(made)
        for centre, radius, start, sweep, thickness in arcs:     # (the curved ones, 0.210: their ends joined)
            spec = wall_spec_for(thickness)
            name = "{} {}".format(prefix, ifc.count("IfcWall") + 1)
            guid = ifc.add_curved_wall(spec, np.array((float(centre[0]), float(centre[1]), float(z))), float(radius),
                                       float(start), float(sweep), height, name, language, storey=storey).GlobalId
            cmd.changed += [g for g in ifc.join_ends(guid) if g not in cmd.changed]
            made.append(guid)
        report = {"walls": made, "doors": [], "windows": [], "furniture": [], "slabs": [], "left": 0, "columns": []}
        for centre, way, width, depth, round_ in columns:        # (0.211)
            spec, turned = column_spec_for(width, depth, round_)
            x = np.array((-way[1], way[0], 0.0)) if turned else np.array((way[0], way[1], 0.0))
            name = "{} {}".format(t("elem.column"), ifc.count("IfcColumn") + 1)
            report["columns"].append(ifc.add_column(spec, np.array((float(centre[0]), float(centre[1]), float(z))),
                                                    height, name, language, storey=storey, x_dir=x).GlobalId)
        if openings:
            make_openings(ifc, straight, report)                # (in the straight walls)
        if furniture:
            make_furniture(ifc, report)
        if slab is not None:
            outline, spec = slab
            name = "{} {}".format(t("elem.slab"), ifc.count("IfcSlab") + 1)
            report["slabs"].append(ifc.add_slab_outline(spec, [(float(x), float(y)) for x, y in outline],
                                                        _slab_bottom(doc, float(z), spec, "estrutural"), name,
                                                        language, storey=storey).GlobalId)
        return report

    cmd.action = action
    return doc.execute(cmd).result


def add_wall_loop(doc, points, spec, height=WALL_HEIGHT, reference="axis", storey=None, closed=True):
    """Walls along a line of plan points (0.102: a rectangle's sides, a face's outline), drawn as `reference`
    ("axis" / "left" / "right" face, seen along the points), each joined to the one before — and the last to the
    first when closed: one undo step. Returns their GlobalIds."""
    pts = [np.asarray(p, dtype=float) for p in points]
    n = len(pts)
    pairs = [(pts[k], pts[(k + 1) % n]) for k in range(n if closed else n - 1)]
    pairs = [(a, b) for a, b in pairs if np.linalg.norm((b - a)[:2]) > 1e-6]
    if not pairs:
        return []
    language, prefix = lang(), t("elem.wall")
    cmd = IfcCommand(t("cmd.walls"), None)

    def action(ifc):
        made, first, prev = [], None, None
        for k, (a, b) in enumerate(pairs):
            axis_a, axis_b = offset_axis(a, b, reference, spec.thickness)
            direction = horizontal_dir(a, b)
            closing = closed and k == len(pairs) - 1 and first is not None
            guid = _make_wall(ifc, axis_a, axis_b, spec, height, prev, first if closing else None, None, None,
                              storey, language, prefix, cmd.changed)
            made.append(guid)
            if first is None:
                first = (guid, direction)
            prev = (guid, direction)
        return made

    cmd.action = action
    return doc.execute(cmd).result


def _slab_bottom(doc, z, spec, function):
    """Where a new slab's underside goes for a click at the level z: a structural slab at a storey's level is
    that storey's floor (its top at the level); a finish (0.100), or a slab drawn elsewhere (on top of the
    walls), rests on the level."""
    on_level = any(abs(z - level) < 1e-6 for _g, _n, level in doc.ifc.storeys())
    return z - spec.thickness if on_level and function != "acabamento" else z


def add_slab(doc, corner, du, dv, spec, storey=None, function="estrutural"):
    """Slab over a level rectangle. At a storey's level (e.g. the ground, z = 0)
    it is that storey's floor slab, with its top at the level; elsewhere (e.g. on
    top of the walls) it rests on that level. storey: GlobalId (default: by level).
    function (0.100): "estrutural" / "acabamento" (on the level) / "excluida"."""
    z = float(corner[2])
    bottom = _slab_bottom(doc, z, spec, function)
    box = box_from_rect(corner, du, dv, bottom, bottom + spec.thickness)
    language, prefix = lang(), t("elem.slab")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcSlab") + 1)
        guid = ifc.create_from_box(spec, box, name, language, storey=storey).GlobalId
        ifc.set_slab_function(guid, function)
        return guid

    return doc.execute(IfcCommand(t("cmd.slab"), action)).result


def add_slab_outline(doc, outline, z, spec, storey=None, holes=(), function="estrutural", loops=None):
    """A slab over a plan outline [(x, y)…] (0.100: a polygon, or what the magic wand found — with its holes)
    clicked at the level z (its place as add_slab's). (0.456) loops: the outline as drawn (core/outline_loops — its
    sides arcs or curves: an ellipse, rounded corners), kept with it. One undo step. Returns its GlobalId."""
    bottom = _slab_bottom(doc, float(z), spec, function)
    outline = [(float(x), float(y)) for x, y in outline]
    holes = [[(float(x), float(y)) for x, y in h] for h in holes]
    language, prefix = lang(), t("elem.slab")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcSlab") + 1)
        guid = ifc.add_slab_outline(spec, outline, bottom, name, language, storey=storey, holes=holes,
                                    function=function).GlobalId
        if loops:
            ifc.set_slab_outline(guid, None, loops=loops)
        return guid

    return doc.execute(IfcCommand(t("cmd.slab"), action)).result


def add_slab_circle(doc, centre, radius, z, spec, storey=None, function="estrutural"):
    """A round slab (0.100): a true circle in the IFC. One undo step. Returns its GlobalId."""
    bottom = _slab_bottom(doc, float(z), spec, function)
    centre = (float(centre[0]), float(centre[1]))
    language, prefix = lang(), t("elem.slab")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcSlab") + 1)
        return ifc.add_slab_outline(spec, None, bottom, name, language, storey=storey, centre=centre,
                                    radius=float(radius), function=function).GlobalId

    return doc.execute(IfcCommand(t("cmd.slab"), action)).result


def add_ramp(doc, start, end, spec, width, rise, storey=None):
    """A straight ramp (0.101) from `start` (the middle of its foot) towards `end` (plan), `width` wide, rising
    `rise`, as thick as the slab type `spec` (IfcRamp). One undo step. Returns its GlobalId."""
    language, prefix = lang(), t("elem.ramp")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcRamp") + 1)
        return ifc.add_ramp(spec, start, end, width, rise, name, language, storey=storey).GlobalId

    return doc.execute(IfcCommand(t("cmd.ramp"), action)).result


def set_ramp(doc, guid, length=None, width=None, rise=None):
    """A ramp's length (its foot stays), width or rise. One undo step."""
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.set_ramp(g, length, width, rise) for g in gs], gs)


def slab_wand(doc, point, reach="interior", storey=None):
    """The magic wand (0.100): the outline of a slab where `point` (plan) is, inside the walls of the storey
    (default: the active one) — a shapely Polygon, or None (not inside closed walls)."""
    from ..core import slabs as core_slabs
    obstacles = doc.ifc.storey_obstacles(storey or doc.active_storey)
    return core_slabs.wand(obstacles, (float(point[0]), float(point[1])), reach)


def add_column(doc, base, spec, height=WALL_HEIGHT, storey=None, x_dir=(1.0, 0.0, 0.0), ties=None):
    """A column (0.66) standing at `base` (its foot's middle), `height` tall, its section turned along x_dir
    (0.86); ties: the two grid axes' uids it is tied to (0.92: placed on their crossing — it follows them). One
    undo step. Returns its GlobalId."""
    language, prefix = lang(), t("elem.column")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcColumn") + 1)
        e = ifc.add_column(spec, base, height, name, language, storey=storey, x_dir=x_dir)
        if ties:
            ifc.tie_to_grid(e.GlobalId, ties)
        return e.GlobalId

    return doc.execute(IfcCommand(t("cmd.column"), action)).result


def add_beam(doc, start, end, spec, top, storey=None):
    """A beam (0.66) from `start` to `end`, its top at the height `top`. One undo step. Returns its GlobalId."""
    language, prefix = lang(), t("elem.beam")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcBeam") + 1)
        a, b, copes = start, end, []
        if getattr(spec, "section", None):         # (0.495: a steel beam stops at the columns; 0.496: on a girder,
            a, b = ifc.beam_to_faces(start, end, top, spec)                          # at its web, coped)
            a, b, copes = ifc.beam_onto_beams(a, b, top, spec)
        e = ifc.add_beam(spec, a, b, top, name, language, storey=storey)
        if copes:
            ifc.set_steel_cuts(e, copes=copes)
            ifc.rebuild_beam(e.GlobalId)
        return e.GlobalId

    return doc.execute(IfcCommand(t("cmd.beam"), action)).result


def add_steel_member(doc, start, end, spec, function="beam", cardinal=None, rotation=0.0, storey=None):
    """(0.495) A steel piece (the section of `spec`) from `start` to `end` (3D), as a beam, column, brace, purlin or
    member, by its cardinal point (None: the function's), turned about its line. One undo step. Its GlobalId."""
    language = lang()
    word = {"beam": "elem.beam", "column": "elem.column", "brace": "elem.brace", "purlin": "elem.purlin",
            "member": "elem.member"}[function]
    cls = {"beam": "IfcBeam", "column": "IfcColumn"}.get(function, "IfcMember")

    def action(ifc):
        name = "{} {}".format(t(word), ifc.count(cls) + 1)
        return ifc.add_steel_member(spec, np.asarray(start, dtype=float), np.asarray(end, dtype=float), name, language,
                                    storey=storey, function=function, cardinal=cardinal, rotation=rotation).GlobalId

    return doc.execute(IfcCommand(t("cmd.steel_member"), action)).result


def mitre(doc, a, b):
    """(0.496) Two steel pieces cut to a mitre where their lines meet (a portal's knee). One undo step. False when
    their lines do not meet."""
    language = lang()
    kinds = {doc.ifc.kind_of(g) for g in (a, b)}
    if kinds != {"steel_member"} or not doc.ifc.mitre(a, b, language, dry=True):
        return False
    doc.execute(IfcCommand(t("cmd.steel_mitre"), lambda ifc: ifc.mitre(a, b, language), changed=[a, b]))
    return True


def steel_columns(doc):
    """(0.497) The steel columns: columns of a steel section, and steel pieces standing up as columns."""
    out = []
    for g in [o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcColumn"]:
        if doc.ifc.steel_section(g) is not None:
            out.append(g)
    return out


def add_base_plates(doc, columns=None, params=None):
    """(0.497) A base plate under each steel column given (None: every steel column without one), its anchor bolts
    and its weld (parameters: mm; missing ones its defaults). One undo step. The connections' GlobalIds."""
    language = lang()
    columns = steel_columns(doc) if columns is None else [c for c in columns if doc.ifc.steel_section(c) is not None]
    columns = [c for c in columns if not any(doc.ifc.connection_params(a.GlobalId)[0] == "base_plate"
                                             for a in doc.ifc.connections_on([c]))]
    if not columns:
        return []

    def action(ifc):
        return [ifc.add_connection("base_plate", [c], params, language).GlobalId for c in columns]

    return doc.execute(IfcCommand(t("cmd.base_plate"), action)).result


def steel_shed(doc, origin, direction, length, column, rafter, purlin, brace, storey=None, **options):
    """(0.499) A steel shed (core/steel_shed): portal frames of `column` and `rafter` (steel types) along `length`,
    purlins of `purlin`, X bracing of `brace` in its end bays; its knees and ridges mitred, base plates under its
    columns. options: span, eave, slope (degrees), spacing, purlins (their spacing), bracing, plates. One undo step.
    The GlobalIds of what it made."""
    from ..core import steel as core_steel, steel_shed as core_shed
    language = lang()
    shed = core_shed.layout(origin, direction, length, rafter_depth=float(rafter.profile[1]),
                            **{k: v for k, v in options.items() if k in core_shed.DEFAULTS})
    specs = {"column": column, "rafter": rafter, "purlin": purlin, "brace": brace}
    words = {"column": "elem.column", "beam": "elem.beam", "purlin": "elem.purlin", "brace": "elem.brace"}
    classes = {"column": "IfcColumn", "beam": "IfcBeam", "purlin": "IfcMember", "brace": "IfcMember"}

    def action(ifc):
        made = []
        for piece in shed.pieces:
            name = "{} {}".format(t(words[piece.function]), ifc.count(classes[piece.function]) + 1)
            e = ifc.add_steel_member(specs[piece.role], piece.start, piece.end, name, language, storey=storey,
                                     function=piece.function, cardinal=piece.cardinal, rotation=piece.rotation)
            made.append(e.GlobalId)
        for i, j in shed.mitres:
            ifc.mitre(made[i], made[j], language)
        extra = []
        if options.get("knees") == "bolted":                   # (0.513) the knees and ridges bolted
            for i, j in shed.mitres:
                a = ifc.add_connection("knee_plate", [made[i], made[j]], None, language)
                extra += [a.GlobalId] + [p.GlobalId for p in ifc.connection_parts(a)]
        for k in shed.plates:
            a = ifc.add_connection("base_plate", [made[k]], None, language)
            extra += [a.GlobalId] + [p.GlobalId for p in ifc.connection_parts(a)]
        if shed.plates and getattr(brace, "section", None) and \
                core_steel.get(brace.section).family in ("L", "LU"):      # (0.503: the walls' braces on gussets)
            for k, piece in enumerate(shed.pieces):
                if piece.role != "brace":
                    continue
                for end, col in ifc.brace_end_columns(made[k]).items():
                    a = ifc.add_connection("gusset", [made[k], col], {"end": end}, language)
                    extra += [a.GlobalId] + [p.GlobalId for p in ifc.connection_parts(a)]
        if shed.plates and getattr(purlin, "section", None) and \
                core_steel.get(purlin.section).family in ("C", "Z", "UPN", "UPE"):   # (0.504: the purlins' cleats)
            for k, piece in enumerate(shed.pieces):
                if piece.role != "purlin":
                    continue
                for beam in ifc.purlin_beams(made[k]):
                    a = ifc.add_connection("purlin_cleat", [made[k], beam], None, language)
                    extra += [a.GlobalId] + [p.GlobalId for p in ifc.connection_parts(a)]
        return made + extra

    return doc.execute(IfcCommand(t("cmd.steel_shed"), action)).result


def steel_truss(doc, start, end, chord, web, storey=None, **options):
    """(0.507) A steel truss (core/steel_truss) from `start` to `end` (seen from above): its chords of `chord`, its
    verticals and diagonals of `web` (steel types). options: kind (pratt, howe, warren), height, panel, elevation. One
    undo step. The GlobalIds of its pieces."""
    from ..core import steel_truss as core_truss
    language = lang()
    truss = core_truss.layout(start, end, **{k: v for k, v in options.items() if k in core_truss.DEFAULTS})
    words = {"chord": "elem.chord", "vertical": "elem.truss_vertical", "diagonal": "elem.truss_diagonal"}

    def action(ifc):
        made = []
        for piece in truss.pieces:
            spec = chord if piece.role == "chord" else web
            name = "{} {}".format(t(words[piece.role]), ifc.count("IfcMember") + 1)
            made.append(ifc.add_steel_member(spec, piece.start, piece.end, name, language, storey=storey,
                                             function=piece.function, cardinal=piece.cardinal,
                                             rotation=piece.rotation).GlobalId)
        return made

    return doc.execute(IfcCommand(t("cmd.steel_truss"), action)).result


def add_steel_stair(doc, foot, direction, rise, width, going, section="UPN200", tread="grelha", storey=None):
    """(0.509) A straight steel stair (ifc/steel_stairs): its treads of grating or chequered plate, its two stringers
    of the channel `section`. One undo step. (its GlobalId, its stringers')."""
    language = lang()

    def action(ifc):
        name = "{} {}".format(t("elem.steel_stair"), ifc.count("IfcStair") + 1)
        stair = ifc.add_steel_stair(np.asarray(foot, dtype=float), direction, rise, width, going, section, tread,
                                    name=name, lang=language, storey=storey)
        return stair.GlobalId, ifc.steel_stair_params(stair.GlobalId)["stringers"]

    return doc.execute(IfcCommand(t("cmd.steel_stair"), action)).result


def number_steel(doc, renumber=False):
    """(0.500) The steel pieces' marks written (their IFC Tag): the same mark for the same pieces, kept where they can
    be (renumber: all anew). One undo step. How many marks changed."""
    out = {}

    def action(ifc):
        out["changed"] = ifc.set_steel_marks(renumber)

    marks, _pieces = doc.ifc.steel_marks(renumber)
    if not any((doc.ifc.by_guid(g).Tag or "") != m for g, m in marks.items()):
        return 0
    doc.execute(IfcCommand(t("cmd.number_steel"), action, touched=list(marks)))
    return len(out.get("changed") or ())


def add_beam_connections(doc, kind, beams, params=None):
    """(0.498) An end plate or a fin plate at each end of the steel beams given that reaches a steel column (and has
    no connection there yet) — (0.506) a fin plate also where it stops at a steel girder's web. One undo step. The
    connections' GlobalIds."""
    language = lang()
    todo = []
    for beam in beams:
        if doc.ifc.steel_section(beam) is None or doc.ifc.kind_of(beam) not in ("beam", "steel_member"):
            continue
        taken = {int(doc.ifc.connection_params(a.GlobalId)[2].get("end", -1)) for a in doc.ifc.connections_on([beam])
                 if doc.ifc.connection_params(a.GlobalId)[0] in ("end_plate", "fin_plate")}
        for end in (0, 1):
            column = doc.ifc.beam_end_column(beam, end)
            if column is None and kind == "fin_plate":           # (0.506: a beam on a girder — its web's cutelo)
                column = doc.ifc.beam_end_girder(beam, end)
            if column is not None and end not in taken:
                todo.append((beam, column, end))
    if not todo:
        return []

    from ..core import steel as core_steel
    from ..ifc.steel_connections import fin_rows

    def values(beam, end):                                   # (0.508: a fin plate's rows — what fits on the beam)
        out = dict(params or {}, end=end)
        if kind == "fin_plate" and "rows" not in out:
            out["rows"] = fin_rows(core_steel.get(doc.ifc.steel_section(beam)))
        return out

    def action(ifc):
        return [ifc.add_connection(kind, [b, c], values(b, end), language).GlobalId for b, c, end in todo]

    return doc.execute(IfcCommand(t("cmd." + kind), action, changed=list({b for b, _c, _e in todo}))).result


def gusset_ends(doc, braces=None):
    """(0.503) [(brace, column, end)] — the ends of the steel braces given (None: every one) that reach a steel column
    and have no gusset there yet; braces not of an angle left out."""
    from ..core import steel
    from ..ifc.steel_connections import ANGLE_FAMILIES
    if braces is None:
        braces = [o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcMember"]
    out = []
    for brace in braces:
        if doc.ifc.kind_of(brace) != "steel_member":
            continue
        sec = steel.get(doc.ifc.steel_section(brace) or "")
        if sec is None or sec.family not in ANGLE_FAMILIES:
            continue
        taken = {int(doc.ifc.connection_params(a.GlobalId)[2].get("end", -1)) for a in doc.ifc.connections_on([brace])
                 if doc.ifc.connection_params(a.GlobalId)[0] == "gusset"}
        for end, column in doc.ifc.brace_end_columns(brace).items():
            if end not in taken:
                out.append((brace, column, end))
    return out


def add_gussets(doc, braces=None, params=None):
    """(0.503) A gusset at each end of the steel braces given (None: every one) that reaches a steel column: the plate
    welded to the column, the brace held back clear of it and bolted to the plate. One undo step. The connections'
    GlobalIds."""
    language = lang()
    todo = gusset_ends(doc, braces)
    if not todo:
        return []

    def action(ifc):
        return [ifc.add_connection("gusset", [b, c], dict(params or {}, end=end), language).GlobalId
                for b, c, end in todo]

    return doc.execute(IfcCommand(t("cmd.gusset"), action, changed=list({b for b, _c, _e in todo}))).result


def purlin_seats(doc, purlins=None):
    """(0.504) [(purlin, beam)] — where the steel purlins given (None: every one; C, Z, channels) sit on steel beams
    without a cleat there yet."""
    from ..core import steel
    from ..ifc.steel_connections import CLEAT_FAMILIES
    if purlins is None:
        purlins = [o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcMember"]
    out = []
    for purlin in purlins:
        if doc.ifc.kind_of(purlin) != "steel_member" or \
                doc.ifc.steel_member_params(purlin)["function"] != "purlin":
            continue
        sec = steel.get(doc.ifc.steel_section(purlin) or "")
        if sec is None or sec.family not in CLEAT_FAMILIES:
            continue
        taken = {doc.ifc.connection_params(a.GlobalId)[1][1] for a in doc.ifc.connections_on([purlin])
                 if doc.ifc.connection_params(a.GlobalId)[0] == "purlin_cleat"}
        out += [(purlin, beam) for beam in doc.ifc.purlin_beams(purlin) if beam not in taken]
    return out


def add_purlin_cleats(doc, purlins=None, params=None):
    """(0.504) A cleat where each steel purlin given (None: every one) sits on a steel beam: a plate welded to the
    beam's top beside the purlin's web, bolted through it. One undo step. The connections' GlobalIds."""
    language = lang()
    todo = purlin_seats(doc, purlins)
    if not todo:
        return []

    def action(ifc):
        return [ifc.add_connection("purlin_cleat", [p, b], params, language).GlobalId for p, b in todo]

    return doc.execute(IfcCommand(t("cmd.purlin_cleat"), action)).result


def _node_key(doc, kind, members, end=None):
    """(0.505) What makes two nodes alike for a connection of `kind`: its pieces' sections — and for a beam's end on a
    column, whether it meets the column's flange or its web."""
    key = (kind,) + tuple(doc.ifc.steel_section(m) or "" for m in members)
    if kind in ("end_plate", "fin_plate") and end is not None:
        try:
            frame = doc.ifc._beam_end_frame(members[0], int(end))
            key += (doc.ifc._onto_flange(members[1], frame[1]),)
        except Exception:
            pass
    return key


def equal_nodes(doc, guid):
    """(0.505, DetailCraft's «copy to equal nodes») For a connection (or a part of it): (the other connections of its
    kind on alike nodes — their assemblies —, the alike nodes without one — [(members, end)]). Alike: the same
    sections (and, at a beam's end, the same face of the column)."""
    found = doc.ifc.connection_params(guid)
    if found is None:
        return [], []
    kind, members, params = found
    own = doc.ifc.connection_of(guid).GlobalId
    key = _node_key(doc, kind, members, params.get("end"))
    others = []
    for a in doc.ifc.file.by_type("IfcElementAssembly"):
        if a.GlobalId == own or doc.ifc.kind_of(a.GlobalId) != "steel_connection":
            continue
        k, m, p = doc.ifc.connection_params(a.GlobalId)
        if k == kind and _node_key(doc, k, m, p.get("end")) == key:
            others.append(a)
    free = []
    if kind == "base_plate":
        for c in steel_columns(doc):
            if (kind, doc.ifc.steel_section(c) or "") == key and not any(
                    doc.ifc.connection_params(a.GlobalId)[0] == "base_plate" for a in doc.ifc.connections_on([c])):
                free.append(([c], None))
    elif kind in ("end_plate", "fin_plate"):
        beams = [o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcBeam"
                 and doc.ifc.steel_section(o.id) == doc.ifc.steel_section(members[0])]
        for beam in beams:
            taken = {int(doc.ifc.connection_params(a.GlobalId)[2].get("end", -1)) for a in doc.ifc.connections_on([beam])
                     if doc.ifc.connection_params(a.GlobalId)[0] in ("end_plate", "fin_plate")}
            for end in (0, 1):
                column = doc.ifc.beam_end_column(beam, end)
                if column is None and kind == "fin_plate":       # (0.506: on a girder)
                    column = doc.ifc.beam_end_girder(beam, end)
                if column is not None and end not in taken and _node_key(doc, kind, [beam, column], end) == key:
                    free.append(([beam, column], end))
    elif kind == "gusset":
        free = [([b, c], end) for b, c, end in gusset_ends(doc) if _node_key(doc, kind, [b, c]) == key]
    elif kind == "purlin_cleat":
        free = [([p, b], None) for p, b in purlin_seats(doc) if _node_key(doc, kind, [p, b]) == key]
    return others, free


def apply_to_equal(doc, guid):
    """(0.505) A connection's values (all but which end it is at) given to every connection of its kind on alike nodes,
    and the same connection put on the alike nodes without one. One undo step. (how many changed, how many made)."""
    found = doc.ifc.connection_params(guid)
    if found is None:
        return 0, 0
    kind, _members, params = found
    others, free = equal_nodes(doc, guid)
    if not others and not free:
        return 0, 0
    language = lang()
    values = {k: v for k, v in params.items() if k != "end"}
    touched = [m for a in others for m in doc.ifc.connection_params(a.GlobalId)[1]]

    def action(ifc):
        for a in others:
            ifc.set_connection(a.GlobalId, language, **values)
        for members, end in free:
            ifc.add_connection(kind, members, dict(values, **({"end": end} if end is not None else {})), language)

    doc.execute(IfcCommand(t("cmd.apply_equal"), action,
                           changed=touched + [p.GlobalId for a in others for p in doc.ifc.connection_parts(a)]))
    return len(others), len(free)


def set_connection(doc, guid, **values):
    """(0.497) A connection's parameters changed (mm), from it or any of its parts: made again. One undo step."""
    language = lang()
    assembly = doc.ifc.connection_of(guid)
    if assembly is None:
        return None
    parts = [p.GlobalId for p in doc.ifc.connection_parts(assembly)]
    members = doc.ifc.connection_params(assembly.GlobalId)[1]          # (0.498: an end plate's beam changes too)
    return doc.execute(IfcCommand(t("cmd.connection"), lambda ifc: ifc.set_connection(guid, language, **values),
                                  changed=parts + members)).result


def knee_plates(doc, a, b, params=None):
    """(0.513) Two steel pieces whose lines meet (a portal's knee, its ridge) mitred and bolted: an end plate on each
    in the mitre's plane, bolted together, each piece held back by its plate. One undo step. The connection's
    GlobalId, or None (their lines do not meet; they have one already)."""
    language = lang()
    if doc.ifc.mitre_plane(a, b) is None:
        return None
    if any(doc.ifc.connection_params(c.GlobalId)[0] == "knee_plate" and set(doc.ifc.connection_params(c.GlobalId)[1])
           == {a, b} for c in doc.ifc.connections_on([a])):
        return None

    def action(ifc):
        ifc.mitre(a, b, language)
        return ifc.add_connection("knee_plate", [a, b], params, language).GlobalId

    return doc.execute(IfcCommand(t("cmd.knee_plate"), action, changed=[a, b])).result


def x_brace(doc, a, b, spec, shape="x"):
    """(0.495) Bracing between two columns (GlobalIds): «x» both diagonals, «/» from a's foot to b's top, «\\» from a's
    top to b's foot — along their axes, from their feet to the lower of their tops. One undo step. The GlobalIds."""
    language = lang()
    ca, _xa, _ha, base_a, top_a = doc.ifc.column_box(a)
    cb, _xb, _hb, base_b, top_b = doc.ifc.column_box(b)
    top = min(top_a, top_b)
    foot_a = np.array((ca[0], ca[1], base_a))
    foot_b = np.array((cb[0], cb[1], base_b))
    head_a, head_b = np.array((ca[0], ca[1], top)), np.array((cb[0], cb[1], top))
    lines = {"x": [(foot_a, head_b), (head_a, foot_b)], "/": [(foot_a, head_b)], "\\": [(head_a, foot_b)]}[shape]
    storey = doc.ifc.storey_of(a)

    def action(ifc):
        made = []
        for p, q in lines:
            name = "{} {}".format(t("elem.brace"), ifc.count("IfcMember") + 1)
            made.append(ifc.add_steel_member(spec, p, q, name, language, storey=storey, function="brace").GlobalId)
        return made

    return doc.execute(IfcCommand(t("cmd.x_brace"), action)).result


_PORT_SYSTEM = {"pipe": "PIPE", "duct": "DUCT", "conduit": "CABLE"}   # (a conduit to a point's cable port, 0.146)
APPROACH = 0.40             # m (0.139): how far out from a unit's side port a pipe / duct turns in to it
MIN_S_PIECE = 0.10          # m (0.197): the level piece left into a port after an S


def s_offset_limit(spec):
    """(0.197) Less height than this between a run and a side port it goes to — two square bends (each as far round
    as the section is wide) and a piece between would not fit — and it goes there by an S: two bends of 45°."""
    return 2.0 * float(spec.profile[0]) + 0.10


def add_segment(doc, start, end, spec, z, storey=None, after=None, end_z=None, tee=None, to_port=None,
                from_port=None, system=None):
    """A pipe or a duct (0.69) from `start` to `end`, its axis at the height `z` — at its end at `end_z`
    (0.136: sloped; at the same plan point, a vertical one — a stack, a riser), level when None. One undo
    step. after: the pipe / duct it goes on from (0.74) — else one of that kind ending at `start`, if any:
    they are joined (a bend in the corner, a reducer in line if another size — 0.137 —, or connected in
    line). tee (0.137): the pipe / duct (or a list of them) whose axis it ends on or starts from — split there by
    a tee. to_port (0.138): an element (a diffuser) whose free port it goes to — it ends over it and comes down to
    it (a bend), connected; from_port: one it starts from, connected. 0.139: a port on a unit's side is reached
    level — the segment ends a little out from it (APPROACH), goes up or down to its height there and in to it.
    system (0.141): the key of the system (ifc/systems.SYSTEMS) what it makes is put in. Returns its GlobalId."""
    language, prefix = lang(), t("elem." + spec.kind)
    port_kind = _PORT_SYSTEM[spec.kind]
    start3 = np.array((float(start[0]), float(start[1]), float(z)))
    if after is None or doc.ifc.by_guid(after) is None:
        after = doc.ifc.segment_ending_at(start3, spec.kind)
    approach = inward = None
    if to_port is not None:
        found = doc.ifc.free_port(to_port, near=end, system=port_kind)
        if found is not None:
            way = doc.ifc.port_way(found[0])
            if abs(way[2]) <= 0.7 and spec.kind != "conduit":    # (on a side: it comes in level, from a little out;
                #                                                  a conduit comes down to a point, 0.146)
                out = way[:2] / max(float(np.linalg.norm(way[:2])), 1e-12)
                approach = found[1][:2] + out * max(APPROACH, 3 * spec.profile[0])
                inward = -out
                end = approach
            else:
                end = found[1][:2]
    zz = float(z if end_z is None else end_z)

    def piece(ifc, a, b, z0, z1, like):
        name = "{} {}".format(prefix, ifc.count(_IFC_CLASS[spec.kind]) + 1)
        return ifc.add_segment(spec, a, b, z0, name, language, storey=storey, end_z=z1,
                               x_dir=ifc._across(like)).GlobalId

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count(_IFC_CLASS[spec.kind]) + 1)
        x_dir = ifc._across(after) if after is not None else None      # (a vertical one: turned as the last)
        new = ifc.add_segment(spec, start, end, z, name, language, storey=storey, end_z=end_z,
                              x_dir=x_dir).GlobalId
        made = [new]
        if after is not None:
            made.append(ifc.join_segments(after, new, language))
        for main in tees:
            ifc.add_tee(main, new, language)
        if from_port is not None:                  # (0.138) from a terminal's (a unit's) port
            found = ifc.free_port(from_port, near=start, system=port_kind)
            if found is not None:
                ifc.connect_to_port(new, found[0], at_end=False)
        if to_port is not None:                    # (0.138) to a terminal's (a unit's) port
            found = ifc.free_port(to_port, near=end, system=port_kind)
            if found is not None:
                port, at = found
                last = new
                here = approach if approach is not None else at[:2]
                drop = abs(float(at[2]) - zz)
                if approach is not None and 0.05 <= drop < s_offset_limit(spec) and \
                        drop < float(np.linalg.norm(at[:2] - approach)) - MIN_S_PIECE:
                    # (0.197) too little height for two square bends: an S — down (or up) at 45° on the way in
                    there = approach + inward * drop
                    v = piece(ifc, here, there, zz, float(at[2]), last)
                    made += [v, ifc.join_segments(last, v, language)]
                    last, here = v, there
                elif drop >= 0.05:                             # down (or up) to its height
                    v = piece(ifc, here, here, zz, float(at[2]), last)
                    made += [v, ifc.join_segments(last, v, language)]
                    last = v
                if approach is not None:                       # (0.139) and in to it, level
                    inn = piece(ifc, here, at[:2], float(at[2]), float(at[2]), last)
                    made += [inn, ifc.join_segments(last, inn, language)]
                    last = inn
                ifc.connect_to_port(last, port)
        if system is not None:                     # (0.141) what it made, in its system
            ifc.set_system([g for g in made if g], system, language)
        return new

    tees = [g for g in ([tee] if isinstance(tee, str) else (tee or ())) if g]       # (it may start on one, end on another)
    changed = [g for g in [after] + tees if g]
    return doc.execute(IfcCommand(t("cmd." + spec.kind), action, changed=changed)).result


def connect_to_network(doc, guids=None):
    """(0.142) Ligar à rede: each free outlet of these sanitary fixtures (None: every one of the active storey) gets
    its branch to the nearest pipe of its system (ifc/branches.py). One undo step. Returns [(fixture, outlet's
    name, system key, the pipe joined or None)]."""
    if guids is None:                              # (0.198: the appliances too — water, waste, gas)
        guids = [o.id for o in doc.objects.values() if o.is_bim and o.storey == doc.active_storey
                 and o.ifc_class in ("IfcSanitaryTerminal", "IfcElectricAppliance", "IfcBurner")]
    guids = [g for g in guids if doc.ifc.kind_of(g) in ("fixture", "appliance")]
    if not guids:
        return []
    language, report = lang(), []
    cmd = IfcCommand(t("cmd.connect_network"), None, changed=[])

    def action(ifc):
        for g in guids:
            report.extend((g, name, key, main) for name, key, main in ifc.connect_fixture(g, language, cmd.changed))

    cmd.action = action                            # (the pipes a tee splits: told to the command as they come)
    doc.execute(cmd)
    return report


def set_system(doc, guid, key):
    """(0.141) The run `guid` is in (it and the pipes / ducts and fittings connected to it) into the system `key`.
    One undo step. Returns the GlobalIds moved."""
    run = doc.ifc.run_of(guid)
    language = lang()
    doc.execute(IfcCommand(t("cmd.set_system"), lambda ifc: ifc.set_system(run, key, language), touched=run))
    return run


def resize_segment(doc, guid, length=None, z=None):
    """A pipe's / duct's length or axis height; what is connected to it goes along (0.74)."""
    gs = _and_copies(doc, guid)
    joined = {r for g in gs for r in doc.ifc.run(g)}
    _edit(doc, lambda ifc: [ifc.resize_segment(g, length, z) for g in gs], sorted(set(gs) | joined))


def set_site_location(doc, latitude, longitude, elevation=0.0):
    """Where the site is on Earth (0.70: georeferencing). One undo step."""
    doc.execute(IfcCommand(t("cmd.site_location"),
                           lambda ifc: ifc.set_site_location(latitude, longitude, elevation)))


def footing_place(doc, guid, spec):
    """Where a footing of type `spec` goes under the column or wall `guid` (0.68): (centre (plan), x direction,
    length, width, top) — under a column centred on its foot, turned with it; under a wall along its whole
    axis (a strip) or in its middle (a pad) — its top at the element's base. None for other elements."""
    kind = doc.ifc.kind_of(guid)
    if kind == "column":
        m = doc.ifc.placement(guid)
        x = m[:3, 0] / np.linalg.norm(m[:3, 0])
        length, width = (spec.profile[0], spec.profile[0]) if spec.strip else spec.profile
        return m[:2, 3].copy(), x, length, width, float(m[2, 3])
    if kind == "wall":
        s, e, _t = doc.ifc.wall_axis(guid)
        d = (e - s) * np.array((1.0, 1.0, 0.0))
        span = float(np.linalg.norm(d))
        if span < 1e-9:
            return None
        length, width = (span, spec.profile[0]) if spec.strip else spec.profile
        return ((s + e) / 2)[:2], d / span, length, width, float(s[2])
    return None


def add_footing(doc, place, spec, storey=None, under=None):
    """A footing (0.68) at `place` (footing_place, or a point's (centre, x, length, width, top)). One undo step.
    storey: GlobalId (default: the one its top is at); under: the column / wall it is under (0.93: tied to it, it
    goes with it). Returns its GlobalId."""
    centre, x_dir, length, width, top = place
    language, prefix = lang(), t("elem.footing")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcFooting") + 1)
        e = ifc.add_footing(spec, centre, x_dir, length, width, top, name, language, storey=storey)
        if under is not None:
            ifc.tie_footing(e.GlobalId, under)
        return e.GlobalId

    return doc.execute(IfcCommand(t("cmd.footing"), action)).result


def footings_under(doc, columns, spec):
    """Footings under columns (0.93, as the addon's "Sapatas" button): under each of `columns` — or, None, every
    column of the active storey — that has none tied to it yet: a pad of the type `spec`, centred on its foot,
    turned with it, its top at the column's base; tied to it. One undo step. Returns the new footings."""
    if columns is None:
        columns = [o.id for o in doc.objects.values()
                   if o.is_bim and o.ifc_class == "IfcColumn" and o.storey == doc.active_storey]
    columns = [g for g in columns if doc.ifc.kind_of(g) == "column"]
    have = doc.ifc.footings_of(columns)
    spots = [(g, footing_place(doc, g, spec)) for g in columns if g not in have]
    spots = [(g, p) for g, p in spots if p is not None]
    if not spots:
        return []
    language, prefix = lang(), t("elem.footing")

    def action(ifc):
        made = []
        for g, (centre, x_dir, length, width, top) in spots:
            name = "{} {}".format(prefix, ifc.count("IfcFooting") + 1)
            e = ifc.add_footing(spec, centre, x_dir, length, width, top, name, language)
            ifc.tie_footing(e.GlobalId, g)
            made.append(e.GlobalId)
        return made

    return doc.execute(IfcCommand(t("cmd.footings_under"), action)).result


def combined_place(doc, a, b, spec):
    """(0.249) Where a combined footing goes under columns a and b (core place as footing_place): along the line
    between their middles, centred between them, as long as that and a pad of `spec` past each (half its length
    beyond each column's middle), as wide as it; its top at the lower of their bases. None when they are not two
    columns, or stand in one place."""
    if doc.ifc.kind_of(a) != "column" or doc.ifc.kind_of(b) != "column":
        return None
    ma, mb = doc.ifc.placement(a), doc.ifc.placement(b)
    d = (mb[:3, 3] - ma[:3, 3]) * np.array((1.0, 1.0, 0.0))
    span = float(np.linalg.norm(d))
    if span < 1e-6:
        return None
    pad_l, pad_w = spec.profile
    return (((ma[:3, 3] + mb[:3, 3]) / 2)[:2], d / span, span + float(pad_l), float(pad_w),
            min(float(ma[2, 3]), float(mb[2, 3])))


def combined_footing(doc, a, b, spec):
    """(0.249) A combined footing (IFC: PAD_FOOTING, "an element that transfers the load of a single column —
    possibly two — to the ground") under columns a and b, of the pad type `spec` (combined_place): tied to both,
    made again under them when either moves. Their own footings stay (take them away if it replaces them). One undo
    step. Returns its GlobalId, or None when they are not two columns apart."""
    place = combined_place(doc, a, b, spec)
    if place is None:
        return None
    centre, x_dir, length, width, top = place
    language, prefix = lang(), t("elem.footing")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcFooting") + 1)
        e = ifc.add_footing(spec, centre, x_dir, length, width, top, name, language, storey=ifc.storey_of(a))
        ifc.tie_combined(e.GlobalId, a, b)
        return e.GlobalId

    return doc.execute(IfcCommand(t("cmd.combined_footing"), action)).result


def beams_between(doc, columns, spec):
    """Beams between columns (0.94, as the addon's "Vigas"): between the columns given — or, None, every column of
    the active storey — next to each other in a line along X or Y (5 cm tolerance), from face to face, their top
    at the columns' top; none where there is one already. Tied to their two columns: they follow them. One undo
    step. Returns the new beams."""
    from ..core.structure import neighbour_pairs
    if columns is None:
        columns = [o.id for o in doc.objects.values()
                   if o.is_bim and o.ifc_class == "IfcColumn" and o.storey == doc.active_storey]
    columns = [g for g in columns if doc.ifc.kind_of(g) == "column"]
    centres = {g: tuple(doc.ifc.placement(g)[:2, 3]) for g in columns}
    have = {frozenset(ab) for ab in doc.ifc.beams_of(columns).values()}
    pairs = [(a, b) for a, b in neighbour_pairs(centres) if frozenset((a, b)) not in have]
    if not pairs:
        return []
    language, prefix = lang(), t("elem.beam")

    def action(ifc):
        made = []
        for a, b in pairs:
            found = ifc.beam_between(a, b)
            if found is None or np.linalg.norm((found[1] - found[0])[:2]) < 0.1:
                continue                                  # (columns touching: no room for a beam)
            start, end, top = found
            name = "{} {}".format(prefix, ifc.count("IfcBeam") + 1)
            e = ifc.add_beam(spec, start, end, top, name, language, storey=ifc.storey_of(a))
            ifc.tie_beam(e.GlobalId, a, b)
            made.append(e.GlobalId)
        return made

    return doc.execute(IfcCommand(t("cmd.beams_between"), action)).result


def walls_under_beams(doc, beams, spec):
    """Walls between the columns and under the beams (0.95, the structure's infill walls): under each of `beams`
    — or, None, every beam tied to columns on the active storey — that has none yet: along it, from face to face
    of its columns, from their base up to the beam's underside, of the type `spec`. Tied to the beam: they
    follow it. One undo step. Returns the new walls."""
    if beams is None:
        beams = [o.id for o in doc.objects.values()
                 if o.is_bim and o.ifc_class == "IfcBeam" and o.storey == doc.active_storey]
    beams = [b for b in beams if doc.ifc.kind_of(b) == "beam"
             and doc.ifc._params(doc.ifc.by_guid(b)).get("PilarA")]
    have = set(doc.ifc.walls_of(beams).values())
    beams = [b for b in beams if b not in have]
    if not beams:
        return []
    language, prefix = lang(), t("elem.wall")

    def action(ifc):
        made = []
        for b in beams:
            a, e, height = ifc.wall_under(b)
            if height < 0.1 or np.linalg.norm((e - a)[:2]) < 0.1:
                continue
            name = "{} {}".format(prefix, ifc.count("IfcWall") + 1)
            wall = ifc.create_from_box(spec, box_from_axis(a, e, spec.thickness, height), name, language,
                                       storey=ifc.storey_of(b))
            ifc._set_params(wall, {"Viga": b})
            made.append(wall.GlobalId)
        return made

    return doc.execute(IfcCommand(t("cmd.walls_under_beams"), action)).result


PROPOSAL_CLASSES = ("IfcColumn", "IfcBeam", "IfcFooting", "IfcPile")


def proposal_elements(doc, storey=None):
    """The elements of the structure proposed from the walls of a storey (0.98; default: the active one)."""
    storey = storey or doc.active_storey
    out = []
    for cls in PROPOSAL_CLASSES:
        for e in doc.ifc.file.by_type(cls):
            p = doc.ifc._params(e)
            if p.get("Proposta") and p.get("PropostaPavimento") == storey:
                out.append(e.GlobalId)
    return out


def _restore_walls(ifc, storey):
    """The walls a proposal lowered (to its beams' underside) back to their height."""
    for e in ifc.file.by_type("IfcWall"):
        p = ifc._params(e)
        if p.get("AlturaAntesProposta") and p.get("PropostaPavimento") == storey:
            ifc.resize_wall(e.GlobalId, height=float(p["AlturaAntesProposta"]))
            ifc._set_params(e, {"AlturaAntesProposta": None, "PropostaPavimento": None})


def propose_structure(doc, walls, max_span, column_spec, beam_spec, footing_spec=None):
    """A structure proposed from the walls (0.98, as the addon's): on the walls given — or, None, every wall of the
    active storey — a column at each corner, T junction, crossing and free end, more along the walls so that
    none is more than `max_span` from the next; a beam between the columns next to each other along each wall,
    its top at the walls' top (the walls then stop at its underside); a footing under each column (footing_spec,
    or none). Everything marked as the proposal: made again, it replaces the one there was; remove_proposal
    takes it away. One undo step. Returns {"columns", "beams", "footings"} counts."""
    import uuid
    from ..core.structure import proposal_nodes
    storey = doc.active_storey
    if walls is None:
        walls = [o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcWall" and o.storey == storey]
    walls = [w for w in walls if doc.ifc.kind_of(w) == "wall"]
    if not walls:
        return None
    axes = {w: doc.ifc.wall_axis(w) for w in walls}
    # (a wall a proposal lowered: its height before it — the action puts it back first)
    heights = {w: float(doc.ifc._params(doc.ifc.by_guid(w)).get("AlturaAntesProposta")
                        or doc.ifc.wall_params(w)[1]) for w in walls}
    nodes, along = proposal_nodes([(axes[w][0][:2], axes[w][1][:2], axes[w][2]) for w in walls], max_span)
    old = proposal_elements(doc, storey)
    pid = uuid.uuid4().hex
    language = lang()
    restored = [e.GlobalId for e in doc.ifc.file.by_type("IfcWall")
                if doc.ifc._params(e).get("PropostaPavimento") == storey]

    def action(ifc):
        _restore_walls(ifc, storey)
        if old:
            ifc.remove(old)
        mark = {"Proposta": pid, "PropostaPavimento": storey}
        on = {k: [walls[i] for i, seq in enumerate(along) if k in seq] for k in range(len(nodes))}
        cols = {}
        for k, (x, y) in enumerate(nodes):
            near = on.get(k) or walls
            base = min(float(axes[w][0][2]) for w in near)
            height = max(heights[w] for w in near)
            name = "{} {}".format(t("elem.column"), ifc.count("IfcColumn") + 1)
            e = ifc.add_column(column_spec, np.array((x, y, base)), height, name, language, storey=storey)
            ifc._set_params(e, mark)
            cols[k] = e.GlobalId
        beams, lowered = 0, {}
        for i, seq in enumerate(along):
            for a, b in zip(seq, seq[1:]):
                found = ifc.beam_between(cols[a], cols[b])
                if found is None or np.linalg.norm((found[1] - found[0])[:2]) < 0.1:
                    continue
                name = "{} {}".format(t("elem.beam"), ifc.count("IfcBeam") + 1)
                e = ifc.add_beam(beam_spec, found[0], found[1], found[2], name, language, storey=storey)
                ifc.tie_beam(e.GlobalId, cols[a], cols[b])
                ifc._set_params(e, mark)
                beams += 1
                under = found[2] - beam_spec.profile[1] - float(axes[walls[i]][0][2])
                lowered[walls[i]] = min(lowered.get(walls[i], under), under)
        for w, height in lowered.items():                 # (the wall up to the beam's underside)
            if MIN_WALL <= height < heights[w] - 1e-6:
                try:
                    ifc.resize_wall(w, height=height)
                except Exception:                         # (a window up there: the wall is left as it was)
                    continue
                ifc._set_params(ifc.by_guid(w), {"AlturaAntesProposta": heights[w], "PropostaPavimento": storey})
        footings = 0
        if footing_spec is not None:
            for g in cols.values():
                centre, x_dir, length, width, top = _footing_spot(ifc, g, footing_spec)
                name = "{} {}".format(t("elem.footing"), ifc.count("IfcFooting") + 1)
                e = ifc.add_footing(footing_spec, centre, x_dir, length, width, top, name, language)
                ifc.tie_footing(e.GlobalId, g)
                for f in [e.GlobalId] + ifc.footings_of([e.GlobalId]).get(e.GlobalId, []):
                    ifc._set_params(ifc.by_guid(f), mark)
                footings += 1
        return {"columns": len(cols), "beams": beams, "footings": footings}

    changed = sorted(set(walls) | set(restored))
    return doc.execute(IfcCommand(t("cmd.propose_structure"), action, changed=changed)).result


def _footing_spot(ifc, column, spec):
    """(centre, x direction, length, width, top) of a pad under a column (as footing_place, from the IFC)."""
    m = ifc.placement(column)
    x = m[:3, 0] / np.linalg.norm(m[:3, 0])
    length, width = spec.profile
    return m[:2, 3].copy(), x, length, width, float(m[2, 3])


def remove_proposal(doc):
    """The structure proposed from the walls of the active storey taken away (0.98); the walls back to their
    height. One undo step. False if there is none."""
    storey = doc.active_storey
    old = proposal_elements(doc, storey)
    walls = [e.GlobalId for e in doc.ifc.file.by_type("IfcWall")
             if doc.ifc._params(e).get("PropostaPavimento") == storey]
    if not old and not walls:
        return False

    def action(ifc):
        _restore_walls(ifc, storey)
        if old:
            ifc.remove(old)

    doc.execute(IfcCommand(t("cmd.remove_proposal"), action, changed=walls))
    return True


def _bays_of(doc, beams):
    """The closed bays of these beams (None: the active storey's) — those tied to columns: ([[beam GlobalIds]
    round each bay], the beams tied to columns)."""
    from ..core.structure import bays
    if beams is None:
        beams = [o.id for o in doc.objects.values()
                 if o.is_bim and o.ifc_class == "IfcBeam" and o.storey == doc.active_storey]
    edges, owners, points = [], [], {}
    for b in beams:
        p = doc.ifc._params(doc.ifc.by_guid(b)) if doc.ifc.by_guid(b) is not None else {}
        a, c = p.get("PilarA"), p.get("PilarB")
        if not a or not c or doc.ifc.by_guid(a) is None or doc.ifc.by_guid(c) is None:
            continue
        for col in (a, c):
            points[col] = tuple(doc.ifc.placement(col)[:2, 3])
        edges.append((a, c))
        owners.append(b)
    return [[owners[k] for k in ring] for ring in bays(points, edges)], owners


SYSTEM_WAYS = {"x": ("x",), "y": ("y",), "grid": ("x", "y")}


def beam_system(doc, beams, way, mode, value, spec):
    """A beam system (0.97, Revit's): in each closed bay of these beams (None: the active storey's) along X or
    Y, beams running along `way` ("x", "y", or "grid": both) — `value` of them evenly spaced (mode "count"), or
    one every `value` m (mode "spacing") — between the bay's beams' inner faces, their top at theirs, of the type
    `spec`. A bay's system laid again replaces the one it had. Tied to the bay: laid again when it changes. One
    undo step. Returns (the new beams, how many bays were not rectangles)."""
    rings, owners = _bays_of(doc, beams)
    rects = [(r, doc.ifc.bay_rectangle(r)) for r in rings]
    skipped = sum(1 for _r, rect in rects if rect is None)
    rects = [(r, rect) for r, rect in rects if rect is not None]
    old = [b for b, (ring, _rule) in doc.ifc.systems_of(owners).items()
           if any(frozenset(ring) == frozenset(r) for r, _rect in rects)]
    if not rects:
        return [], skipped
    language, prefix = lang(), t("elem.beam")
    steel_floor = bool(getattr(spec, "section", None))

    def action(ifc):
        if old:
            for a in ifc.connections_on(old):                  # (0.508: their fin plates go with them)
                ifc.remove_connection(a.GlobalId)
            ifc.remove(old)
        made = []
        for ring, rect in rects:
            for w in SYSTEM_WAYS[way]:
                for k, ((sx, sy), (ex, ey)) in enumerate(ifc.system_lines(rect, w, mode, value)):
                    name = "{} {}".format(prefix, ifc.count("IfcBeam") + 1)
                    e = ifc.add_beam(spec, np.array((sx, sy, rect[4])), np.array((ex, ey, rect[4])), rect[4], name,
                                     language, storey=ifc.storey_of(ring[0]))
                    ifc._set_params(e, {"Vigas": ";".join(ring), "Sistema": "{}|{}|{}|{}".format(w, mode, value, k)})
                    made.append(e.GlobalId)
        if steel_floor:                                        # (0.508) a steel floor: each beam to the girders'
            from ..core import steel as core_steel             # webs, coped, a fin plate at each end on a girder
            from ..ifc.steel_connections import fin_rows
            rows = fin_rows(core_steel.get(spec.section))
            for g in made:
                ifc.steel_system_fit(g)
                for end in (0, 1):
                    girder = ifc.beam_end_girder(g, end)
                    if girder is not None:
                        ifc.add_connection("fin_plate", [g, girder], {"end": end, "rows": rows}, language)
        return made

    return doc.execute(IfcCommand(t("cmd.beam_system"), action, changed=[])).result, skipped


def slabs_in_bays(doc, beams, spec):
    """Slabs in the bays of the beams (0.96, as the addon's "Inserir lajes"): among the beams given — or, None,
    every beam of the active storey tied to columns — each closed bay (a smallest contour of beams between
    columns) gets a slab between the beams' inner faces, its top at theirs, of the type `spec`; none where there
    is one already. Only bays along X and Y for now (rectangles). Tied to its beams: it follows them. One undo
    step. Returns (the new slabs, how many bays were not rectangles)."""
    rings, owners = _bays_of(doc, beams)
    have = {frozenset(r) for r in doc.ifc.slabs_of(owners).values()}
    rings = [r for r in rings if frozenset(r) not in have]
    rects = [(r, doc.ifc.bay_rectangle(r)) for r in rings]
    skipped = sum(1 for _r, rect in rects if rect is None)
    rects = [(r, rect) for r, rect in rects if rect is not None]
    if not rects:
        return [], skipped
    language, prefix = lang(), t("elem.slab")

    def action(ifc):
        made = []
        for ring, (x0, y0, x1, y1, top) in rects:
            name = "{} {}".format(prefix, ifc.count("IfcSlab") + 1)
            box = box_from_rect(np.array((x0, y0, top - spec.thickness)), x1 - x0, y1 - y0, top - spec.thickness, top)
            slab = ifc.create_from_box(spec, box, name, language, storey=ifc.storey_of(ring[0]))
            ifc._set_params(slab, {"Vigas": ";".join(ring)})
            made.append(slab.GlobalId)
        return made

    return doc.execute(IfcCommand(t("cmd.slabs_in_bays"), action)).result, skipped


def _followers(doc, columns, moving=()):
    """The beams tied to these columns, the walls under them and the slabs in their bays (0.94–0.96): they change
    when the columns do."""
    beams = [b for b in doc.ifc.beams_of(columns) if b not in moving]
    walls = [w for w in doc.ifc.walls_of(beams) if w not in moving]
    slabs = [s for s in doc.ifc.slabs_of(beams) if s not in moving]
    systems = [b for b in doc.ifc.systems_of(beams) if b not in moving]
    return beams + walls + slabs + systems


def _with_footings(doc, moves):
    """Moves [(GlobalId, 4x4)] with the footings tied to the columns / walls that move (0.93) — and the piles
    under them (0.94) —, moving the same."""
    moving = {g for g, _m in moves}
    tied = doc.ifc.supports_of(list(moving))
    out = list(moves)
    for g, m in out:                                       # (grows as it goes: a cap's piles after the cap)
        for f in tied.get(g, ()):
            if f not in moving:
                out.append((f, m))
                moving.add(f)
    return out


def resize_beam(doc, guid, length=None, top=None):
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.resize_beam(g, length, top) for g in gs], gs)


def resize_footing(doc, guid, length=None, top=None):
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.resize_footing(g, length, top) for g in gs], gs)


# ---------------------------------------------------------------- the structural grid (0.67)

def next_grid_tag(axes, numbered):
    """The next free tag: 1, 2, 3… (numbered), else A, B, C… (then AA…)."""
    used = {a.tag for a in axes}
    if numbered:
        n = 1
        while str(n) in used:
            n += 1
        return str(n)
    n = 0
    while True:
        tag, k = "", n
        while True:
            tag = chr(ord("A") + k % 26) + tag
            k = k // 26 - 1
            if k < 0:
                break
        if tag not in used:
            return tag
        n += 1


def set_grid(doc, axes, label, settings=None):
    """The structural grid becomes `axes` ([GridAxis]): one undo step, the IfcGrid written from them
    (or left out of the IFC while they do not run both ways). settings: the grid's new settings (0.91), in the
    same step. The columns tied to a crossing (0.92) go with it."""
    level = min((z for _g, _n, z in doc.ifc.storeys()), default=0.0)
    data = [(a.tag, tuple(a.start), tuple(a.end), a.numbered) for a in axes]
    change = (dict(doc.grid_settings), dict(settings)) if settings is not None else None
    # (the lines, not only the segments: an axis moved past the others' ends still takes its columns along)
    before, after = grid_crossings(doc.grids, bounded=False), grid_crossings(axes, bounded=False)
    moves = {}
    for guid, ties in doc.ifc.grid_ties().items():
        old, new = before.get(ties), after.get(ties)
        if old is not None and new is not None and np.hypot(new[0] - old[0], new[1] - old[1]) > 1e-9:
            moves[guid] = (new[0] - old[0], new[1] - old[1])
    supports = doc.ifc.supports_of(list(moves))                          # (their footings and piles too, 0.93)
    todo = list(moves)
    while todo:
        host = todo.pop()
        for f in supports.get(host, ()):
            if f not in moves:
                moves[f] = moves[host]
                todo.append(f)
    beams = _followers(doc, list(moves)) if moves else []                 # (they follow the columns, 0.94)
    changed = sorted(set(moves) | set(beams) | {f for g in moves for f in doc.ifc.counterparts(g)}) if moves else []

    def action(ifc):
        ifc.write_grid(data, level)
        ifc.follow_grid(moves)
        if moves:
            ifc.follow_columns(list(moves))

    doc.execute(GridChange(label, doc.grids, axes, IfcCommand(label, action, changed=changed), settings=change))


def grid_crossings(axes, indices=None, bounded=True):
    """{frozenset(two axes' uids): (x, y)} where two axes (not parallel) cross within their lengths — of the
    axes `indices` (0.92: Columns on the grid), or all; bounded=False: where their lines cross, anywhere."""
    chosen = [a for k, a in enumerate(axes) if indices is None or k in indices]
    out = {}
    for i, a in enumerate(chosen):
        p, r = np.array(a.start, dtype=float), np.array(a.end, dtype=float) - np.array(a.start, dtype=float)
        for b in chosen[i + 1:]:
            q, s = np.array(b.start, dtype=float), np.array(b.end, dtype=float) - np.array(b.start, dtype=float)
            cross = r[0] * s[1] - r[1] * s[0]
            if abs(cross) < 1e-9:
                continue                                  # (parallel)
            t_ = ((q - p)[0] * s[1] - (q - p)[1] * s[0]) / cross
            u_ = ((q - p)[0] * r[1] - (q - p)[1] * r[0]) / cross
            if not bounded or (-1e-9 <= t_ <= 1 + 1e-9 and -1e-9 <= u_ <= 1 + 1e-9):
                x = p + r * t_
                out[frozenset((a.uid, b.uid))] = (float(x[0]), float(x[1]))
    return out


def crossings_to_fill(doc, indices=None):
    """The crossings where Columns on the grid put a column (0.92): of the axes selected — both ways: where they
    cross; one way only: where they cross the axes of the other way; none: every crossing — less those that
    already have a column on the active storey. [(uids, (x, y))]."""
    axes = doc.grids
    if indices:
        chosen = set(indices)
        ways = {axes[k].numbered for k in chosen if 0 <= k < len(axes)}
        if len(ways) == 1:                                # one way only: with every axis of the other way
            chosen |= {k for k, a in enumerate(axes) if a.numbered not in ways}
        found = grid_crossings(axes, chosen)
    else:
        found = grid_crossings(axes)
    taken = []
    for o in doc.objects.values():
        if o.is_bim and o.ifc_class == "IfcColumn" and o.storey == doc.active_storey:
            c = doc.ifc.placement(o.id)[:2, 3]
            taken.append((float(c[0]), float(c[1])))
    return [(ties, p) for ties, p in sorted(found.items(), key=lambda kv: (kv[1][1], kv[1][0]))
            if not any(np.hypot(p[0] - x, p[1] - y) < 0.01 for x, y in taken)]


def columns_on_grid(doc, indices, spec, height=WALL_HEIGHT, storey=None):
    """Columns on the grid (0.92), as the addon's "Inserir pilares" (and better: they stay tied): one at each
    crossing (crossings_to_fill), centred on it, square to the grid, `height` tall, on `storey` — each tied to
    its two axes (it follows them). One undo step. Returns the new columns' GlobalIds."""
    spots = crossings_to_fill(doc, indices)
    if not spots:
        return []
    level = next((z for g, _n, z in doc.storeys() if g == storey), doc.work_level())
    language, prefix = lang(), t("elem.column")

    def action(ifc):
        made = []
        for ties, (x, y) in spots:
            name = "{} {}".format(prefix, ifc.count("IfcColumn") + 1)
            e = ifc.add_column(spec, np.array((x, y, level)), height, name, language, storey=storey)
            ifc.tie_to_grid(e.GlobalId, ties)
            made.append(e.GlobalId)
        return made

    return doc.execute(IfcCommand(t("cmd.columns_on_grid"), action)).result


def numbers_on(axis, settings):
    """Whether an axis is tagged with numbers (1, 2, 3…) under the grid's scheme (0.91): those running along Y
    ("numbers_y", the default), or those running along X ("letters_y")."""
    return axis.numbered != (settings.get("scheme") == "letters_y")


def renumbered(axes, settings):
    """The axes tagged again in order (0.91): the numbered ones 1, 2, 3… from left to right (or bottom to top),
    the lettered ones A, B, C… likewise — under the grid's scheme."""
    axes = copy.deepcopy(list(axes))
    for numbers in (True, False):
        family = [a for a in axes if numbers_on(a, settings) == numbers]
        family.sort(key=lambda a: (min(a.start[0], a.end[0]), min(a.start[1], a.end[1])) if a.numbered
                    else (min(a.start[1], a.end[1]), min(a.start[0], a.end[0])))
        done = []
        for a in family:
            a.tag = next_grid_tag(done, numbers)
            done.append(a)
    return axes


def set_grid_settings(doc, settings, renumber=False):
    """The grid's settings (0.91: tags scheme, dimensions in plans, bubbles' radius); renumber: its axes tagged
    again in order. One undo step."""
    new = dict(GRID_DEFAULTS)
    new.update(doc.grid_settings)
    new.update(settings)
    axes = renumbered(doc.grids, new) if renumber else copy.deepcopy(doc.grids)
    set_grid(doc, axes, t("cmd.grid_settings"), settings=new)


def add_grid_axis(doc, start, end, tag=None):
    """A new axis from `start` to `end` (plan points), tagged `tag` or the next free tag. Returns its tag."""
    axis = GridAxis("", (float(start[0]), float(start[1])), (float(end[0]), float(end[1])))
    axis.tag = tag or next_grid_tag(doc.grids, numbers_on(axis, doc.grid_settings))
    set_grid(doc, doc.grids + [axis], t("cmd.grid_axis"))
    return axis.tag


def rename_grid_axis(doc, index, tag):
    """A new tag for an axis; refused (False) if empty or another axis has it."""
    tag = str(tag).strip()
    if not 0 <= index < len(doc.grids) or not tag or any(a.tag == tag for k, a in enumerate(doc.grids) if k != index):
        return False
    axes = copy.deepcopy(doc.grids)
    axes[index].tag = tag
    set_grid(doc, axes, t("cmd.grid_rename"))
    return True


def remove_grid_axis(doc, index):
    remove_grid_axes(doc, [index])


def remove_grid_axes(doc, indices):
    """Delete these axes (0.72: several selected), one undo step."""
    gone = {k for k in indices if 0 <= k < len(doc.grids)}
    if gone:
        set_grid(doc, [a for k, a in enumerate(doc.grids) if k not in gone], t("cmd.grid_remove"))


class GridRefused(ValueError):
    """An edit of the grid that cannot be made; `code` says why (i18n "refuse.<code>")."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def move_grid_axes(doc, ends, label=None):
    """New ends for some axes (0.72: a grip dragged, a temporary dimension typed over): {index: (start,
    end)} as plan points. One undo step; an axis made too short is refused (GridRefused)."""
    axes = copy.deepcopy(doc.grids)
    for k, (start, end) in ends.items():
        if not 0 <= k < len(axes):
            continue
        start, end = (float(start[0]), float(start[1])), (float(end[0]), float(end[1]))
        if np.hypot(end[0] - start[0], end[1] - start[1]) < 0.1:
            raise GridRefused("too_small")
        axes[k].start, axes[k].end = start, end
    set_grid(doc, axes, label or t("cmd.grid_move"))


def grid_direction(axis):
    d = np.array(axis.end, dtype=float) - np.array(axis.start, dtype=float)
    return d / np.linalg.norm(d)


def aligned_ends(axes, index, which, tol=1e-3):
    """The ends of the axes parallel to `index` lined up with its end `which` ("start" / "end"): [(k, which)]
    — they move together, as Revit keeps grid bubbles aligned (0.72)."""
    d = grid_direction(axes[index])
    p = np.array(getattr(axes[index], which), dtype=float)
    out = []
    for k, axis in enumerate(axes):
        if k == index:
            continue
        dk = grid_direction(axis)
        if abs(d[0] * dk[1] - d[1] * dk[0]) > 1e-6:
            continue                                     # not parallel
        for end in ("start", "end"):
            if abs(np.dot(np.array(getattr(axis, end), dtype=float) - p, d)) < tol:
                out.append((k, end))
                break
    return out


def grid_neighbours(axes, index):
    """The nearest parallel axes on each side of `index`: [(k, signed distance)] (0.72, its temporary
    dimensions)."""
    d = grid_direction(axes[index])
    n = np.array((-d[1], d[0]))
    p = np.array(axes[index].start, dtype=float)
    sides = {}
    for k, axis in enumerate(axes):
        if k == index:
            continue
        dk = grid_direction(axis)
        if abs(d[0] * dk[1] - d[1] * dk[0]) > 1e-6:
            continue
        off = float(np.dot(np.array(axis.start, dtype=float) - p, n))
        if abs(off) < 1e-6:
            continue
        side = off > 0
        if side not in sides or abs(off) < abs(sides[side][1]):
            sides[side] = (k, off)
    return list(sides.values())


def generate_grid(doc, xs, ys, origin=(0.0, 0.0), extension=1.5, replace=False):
    """A grid made at once (0.72, the generator): numbered axes (running along Y) at the distances `xs` from
    the origin, lettered ones (along X) at `ys`; each reaching `extension` past the outermost of the others.
    Added to the axes there are (or replacing them). One undo step. Returns the tags made."""
    x0, y0 = float(origin[0]), float(origin[1])
    xs, ys = [float(v) for v in xs], [float(v) for v in ys]
    span_x = (min(xs, default=0.0), max(xs, default=10.0))
    span_y = (min(ys, default=0.0), max(ys, default=10.0))
    axes = [] if replace else copy.deepcopy(doc.grids)
    made = []
    for x in xs:
        axis = GridAxis("", (x0 + x, y0 + span_y[0] - extension), (x0 + x, y0 + span_y[1] + extension))
        axis.tag = next_grid_tag(axes, numbers_on(axis, doc.grid_settings))
        axes.append(axis)
        made.append(axis.tag)
    for y in ys:
        axis = GridAxis("", (x0 + span_x[0] - extension, y0 + y), (x0 + span_x[1] + extension, y0 + y))
        axis.tag = next_grid_tag(axes, numbers_on(axis, doc.grid_settings))
        axes.append(axis)
        made.append(axis.tag)
    set_grid(doc, axes, t("cmd.grid_generate"))
    return made


def spacings_to_positions(count, text):
    """The generator's input (0.72): `count` axes, `text` their spacing — one value ("5,00": all the same) or
    several ("5;5;6,50": in turn, the last one repeated). Positions from the first: [0, 5, 10…]; None if the
    text is not lengths."""
    from ..core.units import parse_length
    values = []
    for part in str(text).replace(" ", "").split(";"):
        if not part:
            continue
        v = parse_length(part)
        if v is None or v <= 0:
            return None
        values.append(v)
    if count <= 0:
        return []
    if not values:
        return None
    out = [0.0]
    for k in range(count - 1):
        out.append(out[-1] + values[min(k, len(values) - 1)])
    return out


# ---------------------------------------------------------------- storeys (levels)

def add_storey(doc, name, elevation):
    """New storey (one undo step). Returns its GlobalId."""
    return doc.execute(IfcCommand(t("cmd.storey"), lambda ifc: ifc.add_storey(name, elevation).GlobalId)).result


def set_storey_elevation(doc, guid, elevation):
    """Move a storey up/down: its walls, slabs, doors... go with it, and the walls / columns whose top is
    tied to it change height (0.73). One undo step."""
    tied = doc.ifc.constrained_to(guid)
    changed = sorted(set(doc.ifc.storey_elements(guid)) | set(tied) | {f for g in tied for f in _fillings(doc, g)})
    _edit(doc, lambda ifc: ifc.set_storey_elevation(guid, elevation), changed, label="cmd.storey")


def set_constraints(doc, guid, **changes):
    """A wall's or column's base / top (0.73, as Revit's): base (storey GlobalId), base_offset (m), top (storey
    GlobalId, None: not connected), top_offset, height (not connected). One undo step."""
    _edit(doc, lambda ifc: ifc.set_constraints(guid, **changes), [guid] + _fillings(doc, guid),
          label="cmd.constraints")


def rename_storey(doc, guid, name):
    _edit(doc, lambda ifc: ifc.rename(guid, name), [], label="cmd.storey")


def remove_storey(doc, guid):
    _edit(doc, lambda ifc: ifc.remove_storey(guid), [], label="cmd.storey")


# ---------------------------------------------------------------- editing IFC elements

def _edit(doc, action, changed, label="cmd.edit", plan=True):
    """One undo step; (0.267) plan False: nothing moves in the plan (a height): outside / inside not looked at."""
    return doc.execute(IfcCommand(t(label), action, changed=changed, plan=plan)).result


def _fillings(doc, guid):
    e = doc.ifc.by_guid(guid)
    return [f.RelatedBuildingElement.GlobalId for rel in (e.HasOpenings or ())
            for f in (rel.RelatedOpeningElement.HasFillings or ())]


def _and_copies(doc, guid):
    """The element and, if it is in a group, the same element in every other copy of the group:
    an edit made to one is repeated on all (Revit model groups)."""
    return [guid] + doc.ifc.counterparts(guid)


def resize_wall(doc, guid, at_start=0.0, at_end=0.0, height=None, at_base=0.0):
    """at_base: the base goes down by that much (negative: up), the top staying where it is. An end that
    moves keeps its joints (0.71): the walls joined there go along, and the walls joined to them stretch."""
    gs = _and_copies(doc, guid)
    if not (at_start or at_end):                          # (its height only: nothing moves in the plan)
        _edit(doc, lambda ifc: [ifc.resize_wall(g, at_start, at_end, height, at_base=at_base) for g in gs], gs,
              plan=False)
        return
    followers = [f for g in gs for f, _m in doc.ifc.followers(g, at_start, at_end)]
    stretched = doc.ifc.joined_walls(gs + followers)          # (and the walls joined to those that move)
    changed = sorted(set(gs) | set(followers) | set(stretched) | {f for g in followers for f in _fillings(doc, g)})

    def action(ifc):
        for g in gs:
            ifc.stretch_wall(g, at_start, at_end)
            if height is not None or at_base:
                ifc.resize_wall(g, height=height, at_base=at_base)

    _edit(doc, action, changed)


def resize_void(doc, guid, opening, lo, hi):
    """An empty opening or niche of a wall / slab becomes the box lo..hi of the element's frame
    (one of its sides moved with Push/Pull). One undo step."""
    _edit(doc, lambda ifc: ifc.resize_void(guid, opening, lo, hi), [guid], label="cmd.void_size")


def resize_slab(doc, guid, x0, y0, x1, y1):
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.resize_slab(g, x0, y0, x1, y1) for g in gs], gs)


def _per_copy(doc, guid, gs, fn):
    """fn(to_copy) for each of gs: to_copy takes a plan point of `guid` to the same place in that copy."""
    m = doc.ifc.placement(guid)
    inv = np.linalg.inv(m)
    out = {}
    for g in gs:
        mg = doc.ifc.placement(g)
        out[g] = fn(lambda q, mg=mg: tuple(float(c) for c in (mg @ inv @ np.array((float(q[0]), float(q[1]), m[2, 3],
                                                                                  1.0)))[:2]))
    return out


def set_slab_outline(doc, guid, outline=None, loops=None):
    """A slab's plan made the outline [(x, y)…] (0.100: its corners moved, added or taken away) — (0.410) or the
    loops drawn (core/outline_loops: the outline and its holes, their sides arcs or curves). In a group, every copy
    gets the same outline in its own place. One undo step."""
    from ..core import outline_loops
    gs = _and_copies(doc, guid)
    if loops is not None:
        per_copy = _per_copy(doc, guid, gs, lambda go: outline_loops.mapped(loops, go))
        _edit(doc, lambda ifc: [ifc.set_slab_outline(g, None, loops=per_copy[g]) for g in gs], gs, "cmd.slab_outline")
        return
    per_copy = _per_copy(doc, guid, gs, lambda go: [go(q) for q in outline])
    _edit(doc, lambda ifc: [ifc.set_slab_outline(g, per_copy[g]) for g in gs], gs, "cmd.slab_outline")


def set_wall_framing(doc, guid, kind=None, spacing=None, blocking=None):
    """(0.437, the addon's «Steel Frame / Wood Frame») A straight wall's light frame made or changed (kind "steel" /
    "wood"; the studs' spacing; the rows of blocking) — kind "": taken away. In a group, every copy. One undo step."""
    language = lang()
    gs = _and_copies(doc, guid)
    if kind == "":
        _edit(doc, lambda ifc: [ifc.remove_wall_framing(g) for g in gs], gs, "cmd.wall_framing")
        return
    _edit(doc, lambda ifc: [ifc.set_wall_framing(g, kind, spacing, blocking, language) for g in gs], gs,
          "cmd.wall_framing")


def set_slab_heights(doc, guid, heights):
    """(0.433, «piso com declive por vértice») Each corner of a slab's outline at its own height over its top (m, in
    its outline's order; all 0: flat). In a group, every copy the same. One undo step."""
    gs = _and_copies(doc, guid)
    values = [float(z) for z in heights]
    _edit(doc, lambda ifc: [ifc.set_slab_heights(g, values) for g in gs], gs, "cmd.slab_heights")


def set_slab_corner_height(doc, guid, index, height):
    """(0.433) One corner of a slab's outline at its own height over its top (the others as they are)."""
    from ..ifc.edit import EditRefused
    info = doc.ifc.slab_outline(guid)
    if info is None or info.get("radius") is not None:
        raise EditRefused("slab_circle")
    heights = list(info.get("heights") or [0.0] * len(info["outline"]))
    if not 0 <= int(index) < len(heights):
        raise EditRefused("not_editable")
    heights[int(index)] = float(height)
    set_slab_heights(doc, guid, heights)


def set_slab_slope(doc, guid, percent, side):
    """(0.433) A slab falling evenly from one side — `side` its outline's side (its corners `side` and `side`+1)
    stays at its top — to the far corners, `percent` % (1 % = 1 cm a metre): a balcony, a terrace to its drain."""
    from ..ifc.edit import EditRefused
    info = doc.ifc.slab_outline(guid)
    if info is None or info.get("radius") is not None:
        raise EditRefused("slab_circle")
    pts = np.asarray(info["outline"], dtype=float)
    n = len(pts)
    a, b = pts[int(side) % n], pts[(int(side) + 1) % n]
    d = b - a
    if np.linalg.norm(d) < 1e-9:
        raise EditRefused("not_editable")
    normal = np.array((-d[1], d[0])) / np.linalg.norm(d)
    if np.dot(pts.mean(axis=0) - a, normal) < 0:
        normal = -normal                                   # (into the slab)
    set_slab_heights(doc, guid, [round(-float(percent) / 100.0 * max(0.0, float(np.dot(p - a, normal))), 6) + 0.0
                                 for p in pts])


def set_covering_outline(doc, guid, loops):
    """(0.410) A floor finish's or a ceiling's plan made these loops (core/outline_loops: its outline and its holes,
    their sides arcs or curves). In a group, every copy in its own place. One undo step."""
    from ..core import outline_loops
    gs = _and_copies(doc, guid)
    per_copy = _per_copy(doc, guid, gs, lambda go: outline_loops.mapped(loops, go))
    _edit(doc, lambda ifc: [ifc.set_covering_outline(g, per_copy[g]) for g in gs], gs, "cmd.covering_outline")


def set_slab_radius(doc, guid, radius):
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.set_slab_radius(g, radius) for g in gs], gs)


def set_slab_use(doc, guids, use):
    """(0.218) Slabs' own use for their imposed load (core.actions.USES; "": the project's). One undo step."""
    gs = [g for guid in guids for g in _and_copies(doc, guid)]
    doc.execute(IfcCommand(t("cmd.slab_use"), lambda ifc: [ifc.set_slab_use(g, use) for g in gs], touched=gs))


def set_slab_function(doc, guids, function):
    """The function of slabs (0.100): structural, finish or excluded from the calculation — Pset_SlabCommon's
    LoadBearing follows. One undo step; their shapes stay."""
    gs = [g for guid in guids for g in _and_copies(doc, guid)]
    doc.execute(IfcCommand(t("cmd.slab_function"), lambda ifc: [ifc.set_slab_function(g, function) for g in gs],
                           touched=gs))


def resize_column(doc, guid, height):
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.resize_column(g, height) for g in gs], gs, plan=False)


def set_type(doc, guid, spec):
    """New type for a wall/slab/column (thickness/section follow) or a door/window (size follows)."""
    language = lang()
    gs = _and_copies(doc, guid)
    if spec.kind in ("door", "window"):
        walls = [doc.ifc.filling_state(g)["wall"] for g in gs]
        _edit(doc, lambda ifc: [ifc.set_filling_type(g, spec, language) for g in gs], gs + walls)
    elif spec.kind == "roof":                              # (0.278) its underside stays on its walls
        plans = [(g, _reseated(doc, g, {}, spec.thickness)) for g in gs]

        def action(ifc):
            for g, _plan in plans:
                ifc.set_roof_type(g, spec, language)
            _follow_seat(ifc, plans)

        _edit(doc, action, gs)
    else:
        neighbours = doc.ifc.joined_walls(gs)               # their corners follow the new thickness
        fillings = [f for g in gs for f in _fillings(doc, g)]
        beams = _followers(doc, gs) if spec.kind == "column" and doc.ifc.kind_of(guid) == "column" else []
        # (from the new faces, 0.94; (0.495) not a steel piece given a column's section)

        def action(ifc):
            for g in gs:
                ifc.set_element_type(g, spec, language)
            if beams:
                ifc.follow_columns(gs)

        _edit(doc, action, gs + fillings + neighbours + beams)


def save_type(doc, spec, old=None):
    """The type editor (0.87): the type `spec` made (old None) or changed (old: the TypeSpec it was) — every
    element of that type follows, with what is joined to it and the doors and windows in it. One undo step.
    Returns the IFC type's GlobalId."""
    from . import project_types
    language = lang()
    old_type = project_types.find_type(doc.ifc, old) if old is not None else None
    gs = project_types.instances(doc.ifc, old) if old is not None else []
    neighbours = doc.ifc.joined_walls(gs) if gs and spec.kind == "wall" else []
    fillings = [f for g in gs for f in _fillings(doc, g)] if spec.kind in ("wall", "slab") else []
    if spec.kind in ("door", "window"):                   # (0.88) their walls are cut again
        fillings = [doc.ifc.filling_state(g)["wall"] for g in gs]
    save = "save_opening_type" if spec.kind in ("door", "window") else "save_type"
    # (0.278) its roofs: their underside stays on their walls
    plans = [(g, _reseated(doc, g, {}, spec.thickness)) for g in gs if doc.ifc.kind_of(g) == "roof"]

    def action(ifc):
        guid, _changed = getattr(ifc, save)(spec, language, old_type.GlobalId if old_type is not None else None)
        _follow_seat(ifc, plans)
        return guid

    return doc.execute(IfcCommand(t("cmd.save_type"), action, changed=gs + fillings + neighbours)).result


def delete_type(doc, spec):
    """A type of the project that no element uses, removed (one undo step). False if it is in use."""
    from . import project_types
    type_ = project_types.find_type(doc.ifc, spec)
    if type_ is None or project_types.instances(doc.ifc, spec):
        return False
    doc.execute(IfcCommand(t("cmd.delete_type"), lambda ifc: ifc.remove_type(type_.GlobalId)))
    return True


def save_material(doc, spec, old=None):
    """The materials window (0.89): a material made (old None) or changed (old: the MaterialSpec it was) — its
    name, its hatch where cut (its IFC category), its colour, density and thermal conductivity. One undo step;
    the elements made of it are drawn again (their hatch)."""
    import ifcopenshell.util.element
    from . import project_types
    language = lang()
    found = project_types.find_material(doc.ifc, old) if old is not None else None
    users = []
    if found is not None:
        users = [e.GlobalId for e in ifcopenshell.util.element.get_elements_by_material(doc.ifc.file, found)
                 if getattr(e, "GlobalId", None) in doc.objects]
    def action(ifc):
        ifc.save_material(spec, language, found.Name if found is not None else None)
        ifc.fill_ifc_data(users)                            # (0.272: their U, from its thermal conductivity)

    doc.execute(IfcCommand(t("cmd.save_material"), action, touched=users))


def save_pattern(doc, pattern, old=None):
    """(0.318) A fill pattern of the project's made or changed (old: its key before), kept in its IFC. One undo step;
    the materials that use it are drawn again."""
    from ..core import patterns as core_patterns
    doc.execute(IfcCommand(t("cmd.save_pattern"), lambda ifc: ifc.save_pattern(pattern, old)))
    core_patterns.set_project(doc.ifc.patterns())
    return pattern.key


def delete_pattern(doc, key):
    """(0.318) A fill pattern of the project's deleted (one undo step). False for one of the program's."""
    from ..core import patterns as core_patterns
    found = core_patterns.get(key)
    if found is None or found.builtin:
        return False
    doc.execute(IfcCommand(t("cmd.delete_pattern"), lambda ifc: ifc.remove_pattern(key)))
    core_patterns.set_project(doc.ifc.patterns())
    return True


def delete_material(doc, spec):
    """A material of the project that nothing uses, removed (one undo step). False if it is in use (or is one
    of the catalogue's)."""
    import ifcopenshell.util.element
    from . import project_types
    found = project_types.find_material(doc.ifc, spec)
    if catalog.is_starter_material(spec.key) or found is None or project_types.material_users(doc.ifc, spec.key) \
            or ifcopenshell.util.element.get_elements_by_material(doc.ifc.file, found):
        return False
    doc.execute(IfcCommand(t("cmd.delete_material"), lambda ifc: ifc.remove_material(found.Name)))
    return True


def gutter_joins(doc, a, b, outward):
    """(0.384) The gutters a new one along a-b would meet at a corner: [(its end "a" / "b", the other's GlobalId, the
    other's end "a" / "b", the other's outward way)] — ends that meet in plan, at the same height, not in line."""
    from ..ifc.architecture import GUTTER_JOIN
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    way = (b - a)[:2] / max(float(np.linalg.norm((b - a)[:2])), 1e-12)
    joins = []
    for guid, ga, gb, gout, _ca, _cb in doc.ifc.gutter_lines():
        other = (gb - ga)[:2] / max(float(np.linalg.norm((gb - ga)[:2])), 1e-12)
        if abs(float(way[0] * other[1] - way[1] * other[0])) < 0.1:      # (in line, or parallel: no corner)
            continue
        for mine, p in (("a", a), ("b", b)):
            for theirs, q in (("a", ga), ("b", gb)):
                if np.linalg.norm((p - q)[:2]) < GUTTER_JOIN and abs(float(p[2] - q[2])) < 0.05:
                    joins.append((mine, guid, theirs, gout))
    return joins


def add_gutter(doc, a, b, outward, storey=None, shape="caixa", downpipes="nenhum"):
    """(0.374, the study's «Calha») A gutter along the eave a-b (world), outside it towards `outward`. (0.384) Its ends
    that meet another gutter's at a corner: both mitred there, one gutter round the corner. (0.438) Its section (caixa /
    meia_cana) and its downpipes (nenhum / inicio / fim / ambos). One undo step. Its GlobalId."""
    prefix, language = t("elem.gutter"), lang()
    joins = gutter_joins(doc, a, b, outward)
    out = np.asarray(outward, dtype=float)
    cut = {mine: gout for mine, _g, _t, gout in joins}

    def action(ifc):
        name = "{} {}".format(prefix, sum(1 for e in ifc.file.by_type("IfcFlowSegment")
                                          if ifc.kind_of(e.GlobalId) == "gutter") + 1)
        guid = ifc.add_gutter(a, b, outward, name, storey=storey, lang=language, cut_a=cut.get("a"),
                              cut_b=cut.get("b"), shape=shape, downpipes=downpipes).GlobalId
        lines = {g: (ca, cb) for g, _a, _b, _o, ca, cb in ifc.gutter_lines()}
        for _mine, other, theirs, _gout in joins:                  # (the other one mitred to this one too)
            ca, cb = lines.get(other, (None, None))
            ca, cb = (out, cb) if theirs == "a" else (ca, out)
            lines[other] = (ca, cb)
            ifc.set_gutter_cuts(other, ca, cb)
        return guid

    return doc.execute(IfcCommand(t("cmd.gutter"), action, changed=sorted({g for _m, g, _t, _o in joins}))).result


def add_loose(doc, key, centre, angle=0.0, storey=None, width=None, depth=None, height=None):
    """(0.440) A piece of loose furniture of the program's own (core/loose_furniture: «cama_casal», «sofa_3»…) with the
    middle of its footprint at `centre`, turned `angle` degrees. One undo step. Its GlobalId."""
    from ..core import loose_furniture as core_loose
    language = lang()
    label = core_loose.PIECES[key][2][0 if language == "pt" else 1] if key in core_loose.PIECES else key

    def action(ifc):
        n = sum(1 for e in ifc.file.by_type("IfcFurniture") if ifc._params(e).get("Peca") == key) + 1
        return ifc.add_loose(key, centre, angle, "{} {}".format(label, n), language, storey=storey, width=width,
                             depth=depth, height=height).GlobalId

    return doc.execute(IfcCommand(t("cmd.loose"), action)).result


def add_ripado_screen(doc, start, end, height, pattern=None, storey=None):
    """(0.441) A free-standing slatted screen (a divider, a brise) along start -> end, `height` high, its slats as
    `pattern` (width, gap, direction, thickness, frame, battens…). One undo step. Its GlobalId."""
    language, prefix = lang(), t("elem.ripado")

    def action(ifc):
        n = sum(1 for e in ifc.file.by_type("IfcBuildingElementProxy") if ifc.kind_of(e.GlobalId) == "ripado_screen")
        return ifc.add_ripado_screen(start, end, height, "{} {}".format(prefix, n + 1), pattern, storey=storey,
                                     lang=language).GlobalId

    return doc.execute(IfcCommand(t("cmd.ripado"), action)).result


def set_ripado_screen(doc, guid, **changes):
    """(0.441) A slatted screen's length, height or slats changed. In a group, every copy. One undo step."""
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.set_ripado_screen(g, **dict(changes)) for g in gs], gs, "cmd.ripado")


def set_loose(doc, guid, **changes):
    """(0.440) Another piece, or its sizes (piece, width, depth, height). In a group, every copy. One undo step."""
    language = lang()
    gs = _and_copies(doc, guid)
    _edit(doc, lambda ifc: [ifc.set_loose(g, lang=language, **changes) for g in gs], gs, "cmd.loose_edit")


def set_gutter(doc, guid, shape=None, downpipes=None):
    """(0.438) A gutter's section (caixa / meia_cana) or its downpipes (nenhum / inicio / fim / ambos) changed. One undo
    step."""
    language = lang()
    _edit(doc, lambda ifc: ifc.set_gutter(guid, shape, downpipes, language), [guid], "cmd.gutter_edit")


def paint_face(doc, guid, normal, point, key):
    """(0.391) A face of an element painted (the Paint bucket): the plane through `point` facing `normal` (world)
    with the material `key` — None takes its paint off (back to its own). One undo step."""
    from . import paint

    def action(ifc):
        n, d = paint.to_local(ifc, guid, normal, point)
        ifc._set_params(ifc.by_guid(guid), {paint.PARAM: paint.text(paint.with_face(paint.entries(ifc, guid), n, d,
                                                                                     key))})
    _edit(doc, action, [guid], "cmd.paint")


def paint_elements(doc, guids, key):
    """(0.391) All the faces of these elements one material (None: their paint taken off). One undo step."""
    from . import paint
    gs = [g for g in guids if doc.ifc.by_guid(g) is not None]

    def action(ifc):
        for g in gs:
            ifc._set_params(ifc.by_guid(g), {paint.PARAM: paint.text(paint.with_all(key))})
    if gs:
        _edit(doc, action, gs, "cmd.paint")


def replace_paint(doc, old, new):
    """(0.391) SketchUp's Shift+click: every face painted `old` in the model painted `new` (None: taken off) —
    returns how many elements changed. One undo step."""
    from . import paint
    found = []
    for e in doc.ifc.file.by_type("IfcElement"):
        data = paint.entries(doc.ifc, e.GlobalId)
        if any(d[-1] == old for d in data):
            found.append((e.GlobalId, data))
    if not found:
        return 0

    def action(ifc):
        for g, data in found:
            out = [d[:-1] + [new] for d in data if d[-1] == old] if new else []
            out = [d for d in data if d[-1] != old] + out
            ifc._set_params(ifc.by_guid(g), {paint.PARAM: paint.text(out)})
    _edit(doc, action, [g for g, _d in found], "cmd.paint")
    return len(found)


def add_organic_roof(doc, outline, base, storey=None, **params):
    """(0.390, the addon's «Cobertura orgânica») An organic roof over `outline` [(x, y)] (world plan), its edge at the
    level `base`: its form (cupula / abobada / onda) found from the outline, its system (casca / gridshell /
    envidracada / pergola), ring beam and supports as `params` say. One undo step. Its GlobalId."""
    prefix, language = t("elem.organic_roof"), lang()

    def action(ifc):
        name = "{} {}".format(prefix, sum(1 for e in ifc.file.by_type("IfcRoof")
                                          if ifc.kind_of(e.GlobalId) == "organic_roof") + 1)
        return ifc.add_organic_roof(outline, base, name, storey=storey, lang=language, **params).GlobalId

    return doc.execute(IfcCommand(t("cmd.organic_roof"), action)).result


def set_organic_roof(doc, guid, **changes):
    """(0.390) An organic roof's measures changed (its form, system, rise, grid, ring, supports…; `base`: its edge's
    level). One undo step."""
    gs = _and_copies(doc, guid)
    language = lang()
    _edit(doc, lambda ifc: [ifc.set_organic_roof(g, language, **changes) for g in gs], gs, "cmd.organic_roof_edit")


def add_param_surface(doc, data, origin, storey=None, usage="estrutura"):
    """(0.395, the addon's «Superfícies Paramétricas») A parametric surface of the definition `data` (its curves in
    coordinates from `origin`, a world point on the storey's floor). One undo step. Its GlobalId."""
    prefix, language = t("elem.param_surface"), lang()

    def action(ifc):
        count = sum(1 for cls in {c for c, _p in param_surface_usages().values()} for e in ifc.file.by_type(cls)
                    if ifc.kind_of(e.GlobalId) == "param_surface")
        return ifc.add_param_surface(data, origin, "{} {}".format(prefix, count + 1), storey=storey, usage=usage,
                                     lang=language).GlobalId

    return doc.execute(IfcCommand(t("cmd.param_surface"), action)).result


def param_surface_usages():
    from ..ifc.param_surfaces import USAGES
    return USAGES


def surface_from_sketches(doc, picks, op=None, usage="estrutura", storey=None, divisions=None, build=None, **fields):
    """(0.395) A parametric surface made of lines of the model: `picks` [(sketch id, world point near the chain wanted
    or None)] — each sketch then followed by the surface (its uid). The op asked for, or the one the curves make
    (core/param_surface.guess_op); `build` its first construction ({section: fields}). Its GlobalId."""
    from ..core import param_surface as ps
    from .surface_curves import chain_near, ensure_uid, sketch_chains
    level = doc.work_level()
    chosen = []
    for sid, near in picks:
        sk = doc.get(sid)
        if sk is None or sk.is_bim:
            continue
        chain = chain_near(sk, near) if near is not None else (sketch_chains(sk) or [None])[0]
        if chain is not None:
            chosen.append((sk, chain))
    if not chosen:
        raise ValueError("surface_no_curves")
    allp = np.vstack([c[0] for _s, c in chosen])
    origin = np.array((float(allp[:, 0].min()), float(allp[:, 1].min()), float(level)))
    curves = [(c[0] - origin, c[1], ensure_uid(sk)) for sk, c in chosen]
    try:
        data = ps.from_curves(curves, op=op, name=t("elem.param_surface"), divisions=divisions, **fields)
    except ps.SurfaceError as exc:
        raise ValueError(str(exc)) from None
    if data["surface"]["op"] == "revolve":           # (round a vertical axis through the profile's start)
        p0 = np.asarray(data["curves"][0]["points"][0], float)
        data["surface"]["origin"] = fields.get("origin") or [round(float(p0[0]), 6), round(float(p0[1]), 6)]
    if build:
        data["build"] = dict(build)
    return add_param_surface(doc, data, origin, storey=storey or doc.active_storey, usage=usage)


ORGANIC_SHAPES = ("retangulo", "circulo", "elipse", "poligono")


def organic_outline(doc, source):
    """(0.555) (outline — a closed ring of world points —, the sketch's lasting name or None, what it is: "sketch",
    "wall", "slab", "ceiling") of what an organic form is made over: a sketch's closed line or face (a polygon…), a
    straight wall's face (its front, less nothing: its doors are not holes yet), a slab's top, a ceiling's
    underside. ValueError where it gives no outline."""
    from ..core.graph.sketch_host import sketch_obj
    sk = sketch_obj(doc, source) or (doc.get(source) if source is not None else None)
    if sk is not None and not sk.is_bim:
        from .surface_curves import ensure_uid, sketch_chains
        closed = [c for c in sketch_chains(sk) if c[1] and len(c[0]) >= 3]
        if not closed:
            raise ValueError("surface_no_curves")
        return np.asarray(closed[0][0], float), ensure_uid(sk), "sketch"
    kind = doc.ifc.kind_of(source) if isinstance(source, str) and doc.ifc.by_guid(source) is not None else None
    if kind == "wall":
        frame = doc.ifc.element_frame(source)
        ring = [(frame.x0, 0.0), (frame.x0 + frame.length, 0.0), (frame.x0 + frame.length, frame.height),
                (frame.x0, frame.height)]
        return np.array([frame.to_world((u, frame.y1, frame.z0 + v)) for u, v in ring]), None, "wall"
    if kind == "slab":
        info = doc.ifc.slab_outline(source)
        if info is None:
            raise ValueError("surface_no_curves")
        return np.array([(x, y, info["top"]) for x, y in info["outline"]]), None, "slab"
    if kind == "ceiling":
        p = doc.ifc.ceiling_params(source)
        return np.array([(x, y, p["z"]) for x, y in p["outline"]]), None, "ceiling"
    raise ValueError("surface_no_curves")


def organic_shape(kind, centre, length=10.0, width=6.0, sides=6, segments=48):
    """(0.555) A closed ring of world points from measures: a rectangle `length` × `width`, a circle (diameter
    `length`), an ellipse (`length` × `width`) or a regular polygon of `sides` (across: `length`), about `centre`."""
    c = np.asarray(centre, dtype=float)
    if kind == "retangulo":
        pts = [(-length / 2, -width / 2), (length / 2, -width / 2), (length / 2, width / 2), (-length / 2, width / 2)]
    elif kind in ("circulo", "elipse"):
        b = length if kind == "circulo" else width
        a = np.radians(np.arange(segments) * 360.0 / segments)
        pts = list(zip(length / 2 * np.cos(a), b / 2 * np.sin(a)))
    elif kind == "poligono":
        n = max(3, int(sides))
        a = np.radians(90.0 + np.arange(n) * 360.0 / n)
        pts = list(zip(length / 2 * np.cos(a), length / 2 * np.sin(a)))
    else:
        raise ValueError(kind)
    return np.array([(c[0] + x, c[1] + y, c[2]) for x, y in pts])


def organic_line(doc, sketch, mode="suavizar", rounds=4, steps=150, spacing=None, seed=1, inside=False):
    """(0.561) A sketch's line made organic — «suavizar»: rounded (its area kept); «crescer»: grown (differential
    growth: it meanders without crossing itself; `inside`: kept within the line it grew from) — a new sketch of the
    model (a freehand line), the old one left. One undo step. Its id."""
    from ..core import organic_lines as ol
    from ..core.mesh import PolyMesh
    from .document import AddObject, SketchObject
    from .surface_curves import sketch_chains
    obj = doc.get(sketch)
    if obj is None or obj.is_bim:
        raise ValueError("surface_no_curves")
    chains = sketch_chains(obj)
    if not chains:
        raise ValueError("surface_no_curves")
    pts, closed = chains[0]
    if mode == "crescer":
        out = ol.grow(pts, closed, steps=int(steps), spacing=spacing, seed=int(seed),
                      bound=pts if inside and closed else None)
    else:
        out = ol.smooth(pts, closed, rounds=int(rounds))
    pairs = [(k, k + 1) for k in range(len(out) - 1)] + ([(len(out) - 1, 0)] if closed else [])
    new = SketchObject(t("obj.freehand", n=doc.next_number()), np.eye(4),
                       PolyMesh([np.asarray(p, float) for p in out], lines=pairs), curve={"kind": "freehand"})
    doc.execute(AddObject(new, t("cmd.freehand")))
    return new.id


def add_blobs(doc, sketches, usage=None, storey=None, fusion=2.0):
    """(0.560) Masses melted together (op «blobs»): each sketch chosen a ball — at its middle, its size its plan's
    larger half — lying on the working level. One undo step. Its GlobalId."""
    from ..core import param_surface as ps
    from .surface_curves import sketch_chains
    level = float(doc.work_level())
    balls = []
    for sk in sketches:
        if sk is None or sk.is_bim:
            continue
        chains = sketch_chains(sk)
        if not chains:
            continue
        pts = np.vstack([c[0] for c in chains])
        r = float(np.ptp(pts[:, :2], axis=0).max()) / 2.0
        if r > 0.01:
            c = (pts.min(axis=0) + pts.max(axis=0)) / 2.0
            balls.append((float(c[0]), float(c[1]), r))
    if not balls:
        raise ValueError("surface_no_curves")
    origin = np.array((min(b[0] for b in balls), min(b[1] for b in balls), level))
    data = ps.default_definition("blobs", t("elem.param_surface"))
    data["inputs"] = {}
    data["surface"]["fusion"] = float(fusion)
    data["surface"]["balls"] = [{"x": round(x - origin[0], 4), "y": round(y - origin[1], 4), "z": round(r * 0.6, 4),
                                 "r": round(r, 4)} for x, y, r in balls]
    try:
        ps.Surface(data)
    except ps.SurfaceError as exc:
        raise ValueError(str(exc)) from None
    return add_param_surface(doc, data, origin, storey=storey or doc.active_storey, usage=usage or "estrutura")


def add_organic_form(doc, outline, behaviour="catenaria", height=2.0, source_uid=None, usage=None, storey=None,
                     cell=None, grid="quadras", name=None, volume=""):
    """(0.555) An organic form (a Superfície paramétrica of op «organic») over a closed ring of world points: its
    shape found by `behaviour` (membrana, almofada, catenaria, suavizar), rising `height`. `source_uid`: the sketch
    it follows when its line changes. `cell`: the grid's cell (m; by its size if None). One undo step. Its
    GlobalId."""
    from ..core import param_surface as ps
    ring = np.asarray(outline, float).reshape(-1, 3)
    if len(ring) >= 2 and np.linalg.norm(ring[0] - ring[-1]) < 1e-9:
        ring = ring[:-1]
    if len(ring) < 3:
        raise ValueError("surface_no_curves")
    origin = ring.min(axis=0)
    size = float(np.ptp(ring, axis=0).max())
    step = float(cell) if cell else max(size / 28.0, 0.1)
    divisions = max(8, min(64, int(round(size / step))))
    data = ps.from_curves([(ring - origin, True, source_uid)], op="organic",
                          name=name or t("elem.param_surface"), divisions=(divisions, divisions),
                          behaviour=behaviour, height=float(height), grid=grid)
    if volume in ("assente", "lente"):              # (0.560) closed: a cushion on its base, or a lens
        data["surface"]["volume"] = volume
        data["surface"]["grid"] = "aneis"
    try:
        ps.Surface(data)
    except ps.SurfaceError as exc:
        raise ValueError(str(exc)) from None
    if usage is None:
        n = ps.outline_frame(ring)[3]
        usage = "fachada" if abs(n[2]) < 0.7 else "cobertura"
    return add_param_surface(doc, data, origin, storey=storey or doc.active_storey, usage=usage)


def control_ring(doc, sid, height=1.0, factor=0.75):
    """(0.395, the addon's «Anel de controlo») A copy of the sketch's curve `height` above it, `factor` its size
    about its middle — the next ring of a stack for a loft. One undo step; the new sketch's id."""
    import copy as _copy
    from .document import AddObject, SketchObject
    from .surface_curves import sketch_chains
    sk = doc.get(sid)
    if sk is None or sk.is_bim:
        raise ValueError("surface_no_curves")
    chains = sketch_chains(sk)
    if not chains:
        raise ValueError("surface_no_curves")
    c = np.vstack([p for p, _c in chains]).mean(axis=0)
    m = np.eye(4)
    m[:3, :3] *= float(factor)
    m[:3, 3] = c - float(factor) * c + np.array((0.0, 0.0, float(height)))
    new = SketchObject(sk.name, m @ np.asarray(sk.matrix, float), sk.mesh.copy(),
                       curve=_copy.deepcopy(getattr(sk, "curve", None)))
    doc.execute(AddObject(new, t("cmd.control_ring")))
    return new.id


def set_param_surface(doc, guid, data=None, usage=None):
    """(0.395) A parametric surface's definition changed (or its use: its class). One undo step."""
    gs = _and_copies(doc, guid)
    language = lang()
    _edit(doc, lambda ifc: [ifc.set_param_surface(g, data, language, usage=usage) for g in gs], gs,
          "cmd.param_surface_edit")


def roof_eaves(doc, roof):
    """(0.374) A roof's eaves: its lowest level edges along a sloping or upright face (not the soffit's diagonals),
    those on one line joined — [(a, b, outward)] world, outward the horizontal way away from the roof. (0.384) At the
    height of the eave's upper edge — the top of its fascia, where the roof's water runs off and a gutter hangs —, not
    at its foot (the owner: «a calha está muito baixa»)."""
    obj = doc.get(roof)
    mesh = obj.mesh if obj is not None else None
    if mesh is None or not len(mesh.verts):
        return []
    v = np.asarray(mesh.verts, dtype=float).reshape(-1, 3)
    tris = np.asarray(mesh.tris, dtype=np.int64).reshape(-1, 3)
    zmin = float(v[:, 2].min())
    low = np.abs(v[:, 2] - zmin) < 0.02
    n = np.cross(v[tris[:, 1]] - v[tris[:, 0]], v[tris[:, 2]] - v[tris[:, 0]])
    level = np.abs(n[:, 2]) > 0.999 * np.linalg.norm(n, axis=1)
    edges = set()
    for tri, flat in zip(tris, level):
        if flat:
            continue
        for i, j in ((0, 1), (1, 2), (2, 0)):
            a, b = int(tri[i]), int(tri[j])
            if low[a] and low[b] and np.linalg.norm(v[a, :2] - v[b, :2]) > 0.05:
                edges.add((min(a, b), max(a, b)))
    centre = v[:, :2].mean(axis=0)
    lines = []                                   # (direction, offset, lo, hi, z)
    for a, b in edges:
        p, q = v[a], v[b]
        d = (q - p)[:2] / np.linalg.norm((q - p)[:2])
        if d[0] < -1e-9 or (abs(d[0]) <= 1e-9 and d[1] < 0):
            d = -d
        nrm = np.array((-d[1], d[0]))
        off, s0, s1 = float(p[:2] @ nrm), float(p[:2] @ d), float(q[:2] @ d)
        for line in lines:
            if np.allclose(line[0], d, atol=1e-4) and abs(line[1] - off) < 0.01:
                line[2], line[3] = min(line[2], s0, s1), max(line[3], s0, s1)
                break
        else:
            lines.append([d, off, min(s0, s1), max(s0, s1), zmin])
    out = []
    for d, off, lo, hi, z in lines:
        nrm = np.array((-d[1], d[0]))
        base = nrm * off
        a2, b2 = base + d * lo, base + d * hi
        mid = (a2 + b2) / 2
        outward = nrm if float((mid - centre) @ nrm) > 0 else -nrm
        on_line = (np.abs(v[:, :2] @ nrm - off) < 0.02) & (v[:, :2] @ d > lo - 0.02) & (v[:, :2] @ d < hi + 0.02)
        z = float(v[on_line, 2].max()) if on_line.any() else z          # (the fascia's top over that line)
        out.append((np.array((a2[0], a2[1], z)), np.array((b2[0], b2[1], z)), np.array((outward[0], outward[1], 0.0))))
    return out


def add_elevator(doc, corner, width=1.60, depth=1.75, angle=0.0, storey=None):
    """(0.374, the study's «Elevador») An elevator shaft and car, `width` × `depth` inside, from the storey (default:
    the active one) up to the top storey's level plus a storey's height. One undo step. Its GlobalId."""
    storey = storey or doc.active_storey
    levels = sorted(z for _g, _n, z in doc.ifc.storeys())
    z0 = next((z for g, _n, z in doc.ifc.storeys() if g == storey), 0.0)
    above = [z for z in levels if z > z0 + 1e-6]
    z1 = (above[-1] if above else z0) + WALL_HEIGHT + 1.20          # (the machine-less top: over the last storey)
    prefix, language = t("elem.elevator"), lang()
    command = IfcCommand(t("cmd.elevator"), None)

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcTransportElement") + 1)
        guid = ifc.add_elevator(corner, width, depth, angle, z0, z1, name, storey=storey, lang=language).GlobalId
        command.changed += ifc.open_slabs_for(guid, t("elem.bare_opening"))      # (0.438) the slabs it goes through
        return guid

    command.action = action
    return doc.execute(command).result


def add_separator(doc, a, b, storey=None):
    """(0.374, the study's «Separador») A room separation line a-b (plan) on the storey: the rooms there are found
    again with it as a bound. One undo step. Its GlobalId."""
    storey = storey or doc.active_storey
    prefix = t("elem.separator")

    def action(ifc):
        name = "{} {}".format(prefix, ifc.count("IfcVirtualElement") + 1)
        guid = ifc.add_separator(a, b, name, storey).GlobalId
        ifc.update_spaces([storey])
        return guid

    return doc.execute(IfcCommand(t("cmd.separator"), action, changed=_storey_spaces(doc, storey))).result


def _storey_spaces(doc, storey):
    return [s.GlobalId for s in doc.ifc.file.by_type("IfcSpace") if doc.ifc.space_storey(s.GlobalId) == storey]


def identify_rooms(doc, storey=None):
    """(0.374, the study's «Identificar») A room in every space of the storey closed by its walls, columns and
    separators that has none yet — numbered on. One undo step. Their GlobalIds."""
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union
    storey = storey or doc.active_storey
    obstacles = [Polygon(p).buffer(0) for p in doc.ifc.storey_obstacles(storey, separators=True) if len(p) >= 3]
    if not obstacles:
        return []
    solid = unary_union(obstacles)
    lo_x, lo_y, hi_x, hi_y = solid.bounds
    free = box(lo_x - 1, lo_y - 1, hi_x + 1, hi_y + 1).difference(solid)
    parts = [g for g in getattr(free, "geoms", [free]) if g.geom_type == "Polygon"]
    outside = box(lo_x - 1, lo_y - 1, hi_x + 1, hi_y + 1).exterior
    have = [Polygon(info["outline"]) for info in (doc.ifc.space_info(g) for g in _storey_spaces(doc, storey))
            if info is not None and info.get("outline")]
    points = []
    for g in parts:
        if g.area < 0.5 or g.exterior.intersects(outside):         # (the outside, round the building; a crack)
            continue
        p = g.representative_point()
        if not any(h.buffer(0.01).contains(p) for h in have):
            points.append((float(p.x), float(p.y)))
    if not points:
        return []
    name, language = t("room.default"), lang()

    def action(ifc):
        out = []
        for p in points:
            number = ifc.next_space_number(storey)
            space = ifc.add_space(storey, p, name, number, language)
            if space is not None:
                out.append(space.GlobalId)
        return out

    return doc.execute(IfcCommand(t("cmd.rooms_identify"), action)).result


def storey_areas(doc):
    """(0.374, the study's «Áreas») Per storey: (name, level, net area (its rooms), gross area (inside its outer
    walls' outer faces), rooms) — the área útil and the área bruta."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    out = []
    for guid, name, z in doc.ifc.storeys():
        rooms = [doc.ifc.space_info(g) for g in _storey_spaces(doc, guid)]
        net = sum(float(r["area"]) for r in rooms if r is not None)
        shapes = [Polygon(p).buffer(0) for p in doc.ifc.storey_obstacles(guid) if len(p) >= 3]
        gross = 0.0
        if shapes:
            whole = unary_union(shapes).buffer(0.001)
            for g in getattr(whole, "geoms", [whole]):
                gross += Polygon(g.exterior).area if g.geom_type == "Polygon" else 0.0
        out.append((name, float(z), net, gross, len([r for r in rooms if r is not None])))
    return out


def add_room(doc, point, name=None, storey=None):
    """A room (0.99) where `point` (plan) is, between the walls of the storey (default: the active one) — its
    next number, its name (default "Sala"). One undo step. Returns its GlobalId, or None (not enclosed there)."""
    storey = storey or doc.active_storey
    point = (float(point[0]), float(point[1]))
    if doc.ifc.room_region(storey, point) is None:
        return None
    number = doc.ifc.next_space_number(storey)
    name = name or t("room.default")
    language = lang()
    return doc.execute(IfcCommand(t("cmd.room"), lambda ifc: ifc.add_space(storey, point, name, number,
                                                                            language).GlobalId)).result


def set_room(doc, guid, name=None, number=None, finishes=None, external=None):
    """A room's name, number and / or finishes (floor, walls, ceiling) — (0.357) interior or exterior (external). One
    undo step."""
    doc.execute(IfcCommand(t("cmd.room_edit"), lambda ifc: ifc.set_space_data(guid, name, number, finishes,
                                                                              external)))


def set_room_use(doc, guids, key):
    """(0.416) The use of these rooms chosen by hand (a verify/uses key), or None: found again from their name and
    what is inside. One undo step."""
    guids = [guids] if isinstance(guids, str) else list(guids)

    def action(ifc):
        for g in guids:
            ifc.set_space_use(g, key)
    doc.execute(IfcCommand(t("cmd.room_use"), action, plan=False))


def set_room_dwelling(doc, guids, name):
    """(0.416) The dwelling these rooms are in, by its name (a duplex, houses side by side…), or None: found from
    their doors. One undo step."""
    guids = [guids] if isinstance(guids, str) else list(guids)

    def action(ifc):
        for g in guids:
            ifc.set_space_dwelling(g, name)
    doc.execute(IfcCommand(t("cmd.room_dwelling"), action, plan=False))


def set_verify_settings(doc, values):
    """(0.416) The project's verification settings (verify/project.py). One undo step."""
    values = dict(values)
    doc.execute(IfcCommand(t("cmd.verify_settings"), lambda ifc: ifc.set_verify_settings(values), plan=False))


def set_lot(doc, outline, fronts=None, name=None):
    """(0.423) The lot drawn (its outline in plan): the IfcSite's footprint. One undo step. fronts: the sides facing
    the street (None: kept as they were, when it has as many sides)."""
    outline = [(float(x), float(y)) for x, y in outline]
    doc.execute(IfcCommand(t("cmd.lot"), lambda ifc: ifc.set_lot(outline, fronts, name), plan=False))


def set_lot_fronts(doc, fronts):
    """(0.423) The lot's sides facing the street (indices), or [] (found from the entrance). One undo step."""
    fronts = [int(k) for k in (fronts or ())]
    doc.execute(IfcCommand(t("cmd.lot_fronts"), lambda ifc: ifc.set_lot_fronts(fronts), plan=False))


def remove_lot(doc):
    """(0.423) The lot taken away. One undo step."""
    doc.execute(IfcCommand(t("cmd.remove_lot"), lambda ifc: ifc.remove_lot(), plan=False))


def lot_from_terrain(doc, guid=None):
    """(0.423) The outline of a terrain in plan (the one given, else the only one): the lot it was surveyed for — or
    None (no terrain, or more than one and none given)."""
    from ..core import lot as core_lot
    if guid is None:
        terrains = [o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcGeographicElement"]
        if len(terrains) != 1:
            return None
        guid = terrains[0]
    try:
        points = doc.ifc.terrain_survey(guid)
    except Exception:                                   # noqa: BLE001 (not a terrain of this program)
        obj = doc.get(guid)
        points = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3) if obj is not None else None
    return core_lot.from_terrain(points) if points is not None and len(points) >= 3 else None


def set_room_program(doc, needs, building=None, rules=None):
    """(0.357) The project's programme (model/room_program: [Need]) kept in it — (0.475) its type of building and its
    own conflicting pairs too, when given. One undo step."""
    needs = [copy.copy(n) for n in needs]
    doc.execute(IfcCommand(t("cmd.room_program"), lambda ifc: ifc.set_room_program(needs, building, rules)))


def room_from_program(doc, point, need, storey=None):
    """(0.357) A name of the programme dropped on the plan at `point`: the room there named so (and interior or
    exterior as it says) — the one already there, or a new one between the walls. One undo step. Returns
    (its GlobalId, made: True for a new one), or None (no room can be there)."""
    from shapely.geometry import Point, Polygon
    storey = storey or doc.active_storey
    point = (float(point[0]), float(point[1]))
    if doc.ifc.room_region(storey, point) is None:
        return None
    here = Point(point)
    for info in doc.ifc.spaces(storey):
        if Polygon(info["outline"], info["holes"]).contains(here):
            guid = info["guid"]
            doc.execute(IfcCommand(t("cmd.room_edit"), lambda ifc: ifc.set_room_need(guid, need)))   # (0.475)
            return guid, False
    number = doc.ifc.next_space_number(storey)
    language = lang()

    def make(ifc):
        space = ifc.add_space(storey, point, need.name, number, language)
        ifc.set_room_need(space.GlobalId, need)          # (0.475: the line's id and use kept in the room)
        return space.GlobalId

    return doc.execute(IfcCommand(t("cmd.room"), make)).result, True


def remove_rooms(doc, guids):
    """Rooms deleted (one undo step)."""
    guids = [g for g in guids if doc.ifc.by_guid(g) is not None]
    if guids:
        doc.execute(IfcCommand(t("cmd.room_delete"), lambda ifc: ifc.remove(guids)))


def set_status(doc, guids, status):
    """The phase of elements (IFC Status: "EXISTING", "NEW", "DEMOLISH", "TEMPORARY"; None
    clears it), one undo step; their shapes are not made again. Returns how many got it."""
    gs = [g for guid in guids for g in _and_copies(doc, guid)]
    return doc.execute(IfcCommand(t("cmd.status"), lambda ifc: ifc.set_status(gs, status), touched=gs)).result


def _hinges_away(ifc, guid, point):
    """(0.359) Has a door its hinges at the jamb farther from a plan point (it has one leaf that swings)?"""
    found = ifc.door_hinge(guid)
    if found is None:
        return False
    hinge, other = (np.asarray(p, dtype=float)[:2] for p in found)
    p = np.asarray(point, dtype=float)[:2]
    return float(np.linalg.norm(p - hinge)) > float(np.linalg.norm(p - other))


def flip_door(doc, guid, hinge=False, side=False):
    """A door's hinges to the other jamb (hinge) and/or opening to the other side of the wall (side)."""
    language = lang()
    gs = _and_copies(doc, guid)
    walls = [doc.ifc.filling_state(g)["wall"] for g in gs]
    _edit(doc, lambda ifc: [ifc.flip_door(g, hinge, side, language) for g in gs], gs + walls, "cmd.flip_door")


def move_filling(doc, guid, s=None, sill=None):
    gs = _and_copies(doc, guid)
    walls = [doc.ifc.filling_state(g)["wall"] for g in gs]
    _edit(doc, lambda ifc: [ifc.move_filling(g, s, sill) for g in gs], gs + walls)


def rename(doc, guid, name):
    _edit(doc, lambda ifc: ifc.rename(guid, name), [guid])


def fill_known_data(doc):
    """(0.273) What the program knows written into every element's IFC data (a model made before, or by another
    program). One undo step. Returns how many properties were written."""
    return doc.execute(IfcCommand(t("cmd.fill_data"), lambda ifc: ifc.fill_known_data(), plan=False)).result


def set_type_property(doc, spec, prop, value):
    """(0.271) A property of a type's standard IFC set (the fire rating of a wall type…): every element of the type
    has it unless one says otherwise by hand. The type put in the project if it was only the catalogue's. None: taken
    away. One undo step. Returns the type's elements."""
    from ..ifc.edit import EditRefused
    language = lang()

    def action(ifc):
        type_ = ifc.ensure_opening_type(spec, language) if spec.kind in ("door", "window") else \
            ifc.ensure_type(spec, language)
        data = ifc.type_data(type_)
        if data is None:
            raise EditRefused("not_editable")
        return ifc.set_type_property(type_, data[0], prop, value)

    return _edit(doc, action, [], "cmd.type_data", plan=False)


def set_type_entity_property(doc, type_guid, prop, value, pset=None):
    """(0.274) A property of an IFC type of the project (IfcWallType…, by its GlobalId) — its standard set's, or
    `pset`'s: every element of it has it unless one says otherwise by hand. One undo step. Returns its elements."""
    from ..ifc.edit import EditRefused

    def action(ifc):
        type_ = ifc.by_guid(type_guid)
        data = ifc.type_data(type_) if type_ is not None else None
        name = pset or (data[0] if data else None)
        if name is None:
            raise EditRefused("not_editable")
        return ifc.set_type_property(type_, name, prop, value)

    return _edit(doc, action, [], "cmd.type_data", plan=False)


def type_data(doc, spec):
    """(0.271) A type's standard IFC set as type_data gives it — the catalogue's type not in the project yet: its
    set's properties, none set."""
    from ..ifc.ifc_data import common_pset, template
    from . import project_types
    found = project_types.find_type(doc.ifc, spec)
    if found is not None:
        return doc.ifc.type_data(found)
    occurrence = {"door": "IfcDoor", "window": "IfcWindow"}.get(spec.kind) or _IFC_CLASS.get(spec.kind)
    name = common_pset(occurrence) if occurrence else None
    if name is None:
        return None
    return name, [(p, k, c, None) for p, k, c in template(name) if p not in ("Status", "Reference", "IsExternal")]


def set_property(doc, guid, pset, prop, value):
    """A property of an element written by hand (in a group, every copy). (0.266) A standard one is then the
    user's — the program does not change it again; cleared (None), it is the program's again: its own value back,
    if it has one. One undo step."""
    from ..ifc.ifc_data import common_pset
    gs = _and_copies(doc, guid)

    def action(ifc):
        for g in gs:
            ifc.set_property(g, pset, prop, value)
            e = ifc.by_guid(g)
            if e is not None and pset == common_pset(e.is_a()):
                ifc.mark_manual(g, pset, prop, value is not None)
                if value is None:                          # (the program's value back: outside or not too, 0.267)
                    ifc.update_external({ifc.storey_of(g)} - {None})
                    ifc.fill_ifc_data([g])

    _edit(doc, action, [])


def align_pattern(doc, guid, normal, pivot, angle=0.0, shift=(0.0, 0.0, 0.0)):
    """(0.332) An element's surface patterns on its faces turned `normal` aligned by hand, as Revit's Align on a
    pattern line: turned `angle` degrees about the face's normal through `pivot`, then moved by `shift` (on the face);
    kept in the element (ifc/pattern_align.py), so they follow it — in a group, every copy alike. One undo step."""
    from ..ifc import pattern_align
    gs = _and_copies(doc, guid)

    def action(ifc):
        pattern_align.align(ifc, guid, normal, pivot, angle, shift)
        kept = pattern_align.read(ifc, guid)
        for g in gs[1:]:
            pattern_align._write(ifc, g, kept)
    _edit(doc, action, gs, label="cmd.align_pattern", plan=False)


def reset_patterns(doc, guids):
    """(0.332) The elements' surface patterns as always again (not aligned by hand). One undo step; False when none
    was aligned."""
    from ..ifc import pattern_align
    gs = [g for guid in guids for g in _and_copies(doc, guid) if pattern_align.read(doc.ifc, g)]
    if not gs:
        return False
    _edit(doc, lambda ifc: [pattern_align.reset(ifc, g) for g in gs], gs, label="cmd.align_pattern", plan=False)
    return True


def unjoin(doc, a, b, apart=True):
    """(0.333) Two elements unjoined by hand (apart), as Revit's Unjoin Geometry — their cut and faces no longer
    cleaned up together: the line between them drawn — or joined again. Only the drawing changes. One undo step;
    False when they were so already."""
    from ..ifc import unjoin as ifc_unjoin
    if a == b or doc.ifc.by_guid(a) is None or doc.ifc.by_guid(b) is None or \
            (b in ifc_unjoin.apart_from(doc.ifc, a)) == bool(apart):
        return False
    _edit(doc, lambda ifc: ifc_unjoin.set_apart(ifc, a, b, apart), [a, b],
          label="cmd.unjoin_geometry" if apart else "cmd.join_geometry", plan=False)
    return True


# ---------------------------------------------------------------- groups (Revit model groups)

def group_members_of(doc, guid):
    """All the elements of the group copy this element is in, or None."""
    group = doc.ifc.group_of(guid)
    return doc.ifc.group_members(group) if group is not None else None


def make_group(doc, obj_ids, name):
    """The selected IFC elements become a group (a wall's doors/windows join too). Returns the group's GlobalId."""
    guids = [i for i in obj_ids if doc.get(i) is not None and doc.get(i).is_bim]
    if not guids:
        return None
    return doc.execute(IfcCommand(t("cmd.group"), lambda ifc: ifc.make_group(guids, name).GlobalId)).result


def ungroup(doc, guid):
    """The group copy `guid` is in stops being a group (its elements stay)."""
    group = doc.ifc.group_of(guid)
    if group is None:
        return None
    group_guid = group.GlobalId
    doc.execute(IfcCommand(t("cmd.ungroup"), lambda ifc: ifc.ungroup(group_guid)))
    return group_guid


def _whole_groups(doc, guids):
    """GlobalIds of the groups whose every element is among `guids` (doors / windows of selected walls count)."""
    selected = set(doc.ifc._with_fillings(guids))
    out = []
    for g in guids:
        group = doc.ifc.group_of(g)
        if group is not None and group.GlobalId not in out and set(doc.ifc.group_members(group)) <= selected:
            out.append(group.GlobalId)
    return out


def _alone_in_group(doc, guids):
    """Elements of a group acted on without the rest of their group copy: their edits are repeated."""
    whole = set(_whole_groups(doc, guids))
    return [g for g in guids if doc.ifc.group_of(g) is not None and doc.ifc.group_of(g).GlobalId not in whole]


def make_typical(doc, storeys, source, name):
    """Typical floors (0.90): these storeys made equal — the elements of `source` copied to the others; from
    then on what is drawn on one is drawn on all, edits and deletions too. One undo step. Returns the set's id."""
    storeys = [s for s in storeys if s]
    if source not in storeys or len(storeys) < 2:
        return None
    return doc.execute(IfcCommand(t("cmd.typical"), lambda ifc: ifc.make_typical(storeys, source, name))).result


def unmake_typical(doc, storey):
    """The set of equal storeys `storey` is in, undone: each storey keeps its elements, on its own."""
    model = doc.ifc.typical_of(storey)
    if model is None:
        return False
    # (0.463) the dimensions and the drawing its plans shared: each storey keeps them, a copy each (the walls they are
    # hung on: the storey's own, the same place in plan, when they are its group's copies)
    from . import annotations as notes2d
    from . import dimensions as dims_model
    from .document import JoinedCommand
    members = doc.ifc.typical_sets().get(model, [])
    levels = {g: z for g, _n, z in doc.storeys()}
    anns, dims = [], []
    for source in members:
        for target in members:
            if target == source:
                continue
            dz = levels.get(target, 0.0) - levels.get(source, 0.0)
            for a in [a for a in doc.annotations if a.view == ("plan", source) and not a.extra.get("alone")]:
                c = copy.deepcopy(a)
                c.view = ("plan", target)
                c.points = [np.asarray(p, dtype=float) + (0.0, 0.0, dz) for p in a.points]
                anns.append(c)
            for d in [d for d in doc.dimensions if d.view == ("plan", source) and not getattr(d, "alone", False)]:
                c = copy.deepcopy(d)
                c.view = ("plan", target)
                c.refs = [_counterpart_ref(doc, ref, target) for ref in (getattr(d, "refs", None) or ())]
                c.at_ref = _counterpart_ref(doc, d.at_ref, target)
                c.vertex_ref = _counterpart_ref(doc, d.vertex_ref, target)
                for name in ("a", "b", "at", "vertex"):
                    p = getattr(d, name, None)
                    if p is not None:
                        setattr(c, name, np.asarray(p, dtype=float) + (0.0, 0.0, dz))
                dims.append(c)
    label = t("cmd.untypical")
    steps = [IfcCommand(label, lambda ifc: ifc.unmake_typical(model))]
    if anns:
        steps.append(notes2d.AddAnnotations(anns, label))
    if dims:
        steps.append(dims_model.ReplaceDimensions([], dims, label))
    doc.execute(JoinedCommand(steps, label) if len(steps) > 1 else steps[0])
    return True


def _counterpart_ref(doc, ref, storey):
    """(0.463) A dimension's end hung on an element of a typical floor: hung on that element's copy on `storey` (the
    same role in its group there), else as it was."""
    if not ref:
        return ref
    try:
        guid = ref[0]
        group = doc.ifc.group_of(guid)
        role = doc.ifc.role_of(guid) if group is not None else None
        if role is None:
            return ref
        model = doc.ifc.typical_of(storey)
        for g in doc.ifc.group_copies(model) if model else ():
            if doc.ifc._params(g).get("Pavimento") == storey:
                twin = next((m for m in doc.ifc.group_members(g) if doc.ifc.role_of(m) == role), None)
                if twin is not None:
                    return (twin, *tuple(ref)[1:])
    except Exception:
        return ref
    return ref


def repeat_on_storeys(doc, obj_ids, storey_guids):
    """Copies of the selection on other storeys, at the same place in plan (a typical floor).
    Groups stay groups: an apartment edited on one floor changes on all. One undo step."""
    objs = [doc.get(i) for i in obj_ids if doc.get(i) is not None]
    bim_objs = [o for o in objs if o.is_bim]
    source = bim_objs[0].storey if bim_objs and bim_objs[0].storey else doc.active_storey
    levels = {g: z for g, _n, z in doc.storeys()}
    targets = [g for g in storey_guids if g in levels and g != source]
    if not targets:
        return []
    from ..core.transform import translation
    matrices = [translation((0.0, 0.0, levels[g] - levels.get(source, 0.0))) for g in targets]
    return copy_objects(doc, obj_ids, matrices, t("cmd.repeat"), storeys=targets)


# ---------------------------------------------------------------- components

COMPONENT_CATEGORIES = ("furniture", "sanitary", "generic")


def make_component(doc, sketch_ids, name, category, storey=None):
    """Turn sketch volumes into a component (an IFC type holding the geometry
    once) and its first instance, where the sketches were. One undo step.
    Returns the instance's GlobalId, or None if there is no face to use."""
    sketches = [doc.get(i) for i in sketch_ids if doc.get(i) is not None and not doc.get(i).is_bim]
    sketches = [o for o in sketches if o.mesh.faces]
    if not sketches:
        return None
    world, faces = [], []
    for o in sketches:
        base = len(world)
        world += [o.matrix[:3, :3] @ v + o.matrix[:3, 3] for v in o.mesh.verts]
        faces += [[base + i for i in f] for f in o.mesh.faces]
    world = np.array(world)
    origin = world.min(axis=0)                     # the component's own origin: its lowest corner
    local = world - origin
    matrix = np.eye(4)
    matrix[:3, 3] = origin
    action = lambda ifc: ifc.create_component(name, category, local, faces, matrix, storey).GlobalId  # noqa: E731
    return doc.execute(IfcCommand(t("cmd.component"), action, remove_sketches=sketches)).result


def place_component(doc, type_guid, point, storey=None, angle=0.0):
    """One more copy of a component, its lowest corner at `point` (an ArqBIM component's
    origin; for one from another program, its box's), turned `angle` degrees about the
    vertical. One undo step. Returns its GlobalId."""
    a = np.radians(angle)
    matrix = np.eye(4)
    matrix[:2, :2] = ((np.cos(a), -np.sin(a)), (np.sin(a), np.cos(a)))
    lo, _hi = doc.ifc.component_box(type_guid)
    matrix[:3, 3] = np.asarray(point, dtype=float) - matrix[:3, :3] @ lo
    action = lambda ifc: ifc.add_component_instance(type_guid, matrix, storey).GlobalId    # noqa: E731
    return doc.execute(IfcCommand(t("cmd.component_place"), action)).result


def import_components(doc, library, type_ids):
    """Bring components from another IFC file (IfcModel.read_library) into the project's
    library, ready to be placed. One undo step. Returns their GlobalIds."""
    action = lambda ifc: ifc.append_components(library, type_ids)        # noqa: E731
    return doc.execute(IfcCommand(t("cmd.import_components"), action)).result


def _indexed(corners):
    """Triangles' corners (T, 3, 3) → (vertices (V, 3), triangles (T, 3)): the corners closer than a micrometre one
    vertex."""
    pts = np.asarray(corners, dtype=float).reshape(-1, 3)
    _u, first, index = np.unique(np.round(pts * 1e6), axis=0, return_index=True, return_inverse=True)
    return pts[first], index.reshape(-1, 3)


def import_model_component(doc, model, name, category="furniture", unit=None, up=None, in_place=False):
    """(0.351) A 3D file read (model/mesh_import.Model3D, in `unit` with `up` its vertical when the file says none)
    made a component: an IFC type keeping its shape once, its pieces in their materials' colours, its own origin its
    lowest corner — its first copy where it was in the file (in_place), else none yet (placed after, where clicked).
    One undo step. Returns the type's GlobalId."""
    parts = model.parts_m(unit, up)
    origin = np.concatenate([c.reshape(-1, 3) for c in parts.values()]).min(axis=0)
    pieces = [(part, rgb, alpha) + _indexed(c - origin) for (part, rgb, alpha), c in parts.items()]
    matrix = None
    if in_place:
        matrix = np.eye(4)
        matrix[:3, 3] = origin
    action = lambda ifc: ifc.create_imported_component(name, category, pieces, matrix).GlobalId    # noqa: E731
    return doc.execute(IfcCommand(t("cmd.import_model"), action)).result


def import_model_sketch(doc, model, name, unit=None, up=None):
    """(0.351) A 3D file read made a sketch, where it was in the file: its triangles joined into whole faces
    (mesh_import.sketch_mesh), to edit with Push/Pull or make a component of. One undo step. Returns its id."""
    from .document import AddObject
    from .mesh_import import sketch_mesh
    mesh, origin = sketch_mesh(model.parts_m(unit, up))
    matrix = np.eye(4)
    matrix[:3, 3] = origin
    obj = SketchObject(name, matrix, mesh)
    doc.execute(AddObject(obj, t("cmd.import_model")))
    return obj.id


def library_members(doc, kind, ref):
    """What "select all copies" selects: a component's instances, or every element of every
    copy of a group model."""
    lib = doc.ifc.library()
    if kind == "component":
        return next((inst for g, _n, inst, _p in lib["components"] if g == ref), [])
    copies = next((c for m, _n, c in lib["groups"] if m == ref), [])
    return [g for members in copies for g in members]


def edit_component(doc, guid):
    """Open a component instance for editing: it becomes a sketch with the
    component's shape (Push/Pull, Rectangle... work on it); finish_component
    writes the new shape back to every copy. Returns the sketch's id."""
    type_guid = doc.ifc.component_type(guid)
    if type_guid is None:
        return None
    verts, faces = doc.ifc.component_mesh(type_guid)
    e = doc.ifc.by_guid(guid)
    group = doc.ifc.group_of(guid)
    link = {"type": type_guid, "guid": guid, "name": e.Name or "", "storey": doc.ifc.storey_of(guid),
            "component": doc.ifc.by_guid(type_guid).Name or "",
            "group": group.GlobalId if group is not None else None, "role": doc.ifc.role_of(guid)}
    sketch = SketchObject(link["component"], doc.ifc.placement(guid), PolyMesh(verts, faces), component=link)
    doc.execute(IfcCommand(t("cmd.component_edit"), lambda ifc: ifc.remove([guid]), add_sketches=[sketch]))
    return sketch.id


def finish_component(doc, sketch_id):
    """Close a component being edited: its new shape goes to the component (all
    copies change) and the instance comes back where the sketch is. One undo step."""
    sketch = doc.get(sketch_id)
    link = getattr(sketch, "component", None) if sketch is not None else None
    if link is None or not sketch.mesh.faces:
        return None
    others = doc.ifc.component_instances(link["type"])

    def action(ifc):
        ifc.set_component_mesh(link["type"], sketch.mesh.verts, sketch.mesh.faces)
        inst = ifc.add_component_instance(link["type"], sketch.matrix, link["storey"], link["name"], guid=link["guid"])
        group = ifc.by_guid(link["group"]) if link.get("group") else None
        if group is not None:
            ifc.join_group(inst.GlobalId, group, link["role"])     # back in its group
        return inst.GlobalId

    return doc.execute(IfcCommand(t("cmd.component_edit"), action, remove_sketches=[sketch], changed=others)).result


def is_filling(doc, guid):
    """A door or window (it lives in an opening of a wall) — (0.188) or a curtain wall embedded in one: it goes
    with its wall, and alone slides along it."""
    obj = doc.get(guid)
    if obj is None or not obj.is_bim:
        return False
    if obj.ifc_class in ("IfcDoor", "IfcWindow"):
        return True
    return obj.ifc_class == "IfcCurtainWall" and doc.ifc.host_wall(guid) is not None


def transform_objects(doc, obj_ids, matrix, label):
    """Move / rotate sketches and IFC elements by a 4x4 matrix, in one undo step.
    A wall takes its doors and windows along; a door/window whose wall is not
    moving is left out (use slide_filling). Returns the ids moved."""
    objs = [doc.get(i) for i in obj_ids if doc.get(i) is not None]
    sketches = [o for o in objs if not o.is_bim]
    moving = {o.id for o in objs if o.is_bim}
    guids = [g for g in moving if not is_filling(doc, g)]      # doors/windows follow their wall
    guids = [g for g in guids if doc.ifc.kind_of(g) != "cladding"]   # …and its finishes (made again on it, 0.119)
    if not sketches and not guids:
        return []
    moved = []
    for o in sketches:
        new = o.copy()
        new.matrix = np.asarray(matrix, dtype=float) @ o.matrix
        moved.append(new)
    if guids:
        # elements of a group moved without the rest of their group: the same move in every copy
        moves = [(g, np.asarray(matrix, dtype=float)) for g in guids]
        for g in _alone_in_group(doc, guids):
            for c in doc.ifc.counterparts(g):
                between = doc.ifc.placement_between(g, c)
                moves.append((c, between @ np.asarray(matrix, dtype=float) @ np.linalg.inv(between)))
        moves = _with_footings(doc, moves)                 # (a column's footing goes with it, 0.93)
        moved_ids = [g for g, _m in moves]
        neighbours = doc.ifc.joined_walls(moved_ids)        # they stretch to stay joined
        beams = _followers(doc, moved_ids, moved_ids)       # (beams and the walls under them follow, 0.94)
        changed = sorted(set(moved_ids) | set(neighbours) | set(beams)
                         | {f for g in moved_ids for f in _fillings(doc, g)})

        def action(ifc):
            for g, m in moves:
                ifc.transform(g, m)
            ifc.rejoin(moved_ids)
            ifc.follow_columns(moved_ids, keep=moved_ids)

        doc.execute(IfcCommand(label, action, remove_sketches=sketches, add_sketches=moved, changed=changed))
    else:
        doc.execute(ReplaceObjects(sketches, moved, label))
    return [o.id for o in sketches] + guids


def change_storey(doc, obj_ids, storey_guid, keep_height=False):
    """(0.527, the owner: «selecionar uma parede… vinculada num piso e mudá-la para outro piso… sem ter que apagar e
    criar de novo») IFC elements put in another storey, as Revit's «Level» changed in the properties: they go up or
    down by the difference between the two levels, keeping their height over their level (keep_height: they stay where
    they are, only their storey changes). Doors and windows go with their wall (alone: left out); the walls joined to
    them stretch to stay joined. One undo step. Returns the GlobalIds moved."""
    from ..core.transform import translation
    levels = {g: z for g, _n, z in doc.storeys()}
    if storey_guid not in levels:
        return []
    objs = [doc.get(i) for i in obj_ids if doc.get(i) is not None and doc.get(i).is_bim]
    guids = [o.id for o in objs if o.storey != storey_guid and not is_filling(doc, o.id)]
    if not guids:
        return []
    moves = [(g, None if keep_height or doc.get(g).storey not in levels else
              translation((0.0, 0.0, levels[storey_guid] - levels[doc.get(g).storey]))) for g in guids]
    neighbours = doc.ifc.joined_walls(guids)
    changed = sorted(set(guids) | set(neighbours) | {f for g in guids for f in _fillings(doc, g)})

    def action(ifc):
        for g, m in moves:
            if m is not None and abs(float(m[2, 3])) > 1e-9:
                ifc.transform(g, m)
            ifc.move_to_storey(g, storey_guid)
        ifc.rejoin(guids)
        return guids

    return doc.execute(IfcCommand(t("cmd.change_storey"), action, changed=changed)).result


def copy_objects(doc, obj_ids, matrices, label, storeys=None):
    """Copies of sketches and IFC elements, one set per matrix (several matrices
    = a series of copies), in one undo step. A wall's doors and windows are
    copied with it; doors/windows alone are left out (use copy_filling). A
    whole group copied is one more copy of that group (edits stay shared).
    storeys: for each matrix, the storey the copies go in (None: the same).
    Returns the new ids."""
    objs = [doc.get(i) for i in obj_ids if doc.get(i) is not None]
    sketches = [o for o in objs if not o.is_bim]
    guids = _with_finishes(doc, [o.id for o in objs if o.is_bim and not is_filling(doc, o.id)])
    whole = _whole_groups(doc, guids)
    new_sketches = []
    for m in matrices:
        for o in sketches:
            name = t("obj.name", n=doc.next_number()) if o.mesh.faces else t("obj.lines", n=doc.next_number())
            new_sketches.append(SketchObject(name, np.asarray(m, dtype=float) @ o.matrix, o.mesh.copy(),
                                             curve=getattr(o, "curve", None)))
    if guids:
        def action(ifc):
            out = []
            for k, m in enumerate(matrices):
                ifc.copy_map = {}
                copies = {}
                for g in guids:
                    new = ifc.copy_element(g)
                    ifc.transform(new.GlobalId, m)
                    if storeys is not None and storeys[k] is not None:
                        ifc.move_to_storey(new.GlobalId, storeys[k])
                    copies[g] = new.GlobalId
                    out.append(new.GlobalId)
                # walls copied together stay joined together (a copied room is still one room)
                joints = {j[0].id(): j for g in guids for j in ifc.wall_joints(g)}
                for _rel, through, through_end, butt, butt_end in joints.values():
                    if through in copies and butt in copies:
                        ifc.connect_walls(copies[through], through_end, copies[butt], butt_end)
                # a whole group copied is one more copy of it; part of a group copied is on its own
                grouped = set()
                for group_guid in whole:
                    group = ifc.by_guid(group_guid)
                    members = [ifc.copy_map[g] for g in ifc.group_members(group) if g in ifc.copy_map]
                    ifc.copy_group(group, members)
                    grouped |= set(members)
                for original, copy in ifc.copy_map.items():
                    if copy not in grouped and ifc.role_of(copy) is not None:
                        ifc._set_params(ifc.by_guid(copy), {"Papel": None})
                ifc.remap_ties(ifc.copy_map)                # (a copied beam: between the copied columns, 0.94)
            return out
        cmd = doc.execute(IfcCommand(label, action, add_sketches=new_sketches))
        return cmd.result + [o.id for o in new_sketches]
    if new_sketches:
        doc.execute(ReplaceObjects([], new_sketches, label))
    return [o.id for o in new_sketches]


def _along_wall(doc, guid, delta):
    """A world move of a door/window as (along its wall, up) in the wall's own frame."""
    st = doc.ifc.filling_state(guid)
    m = st["matrix"]
    x = m[:3, 0] / np.linalg.norm(m[:3, 0])
    if st.get("curved"):                            # (0.177) along the arc where it is: the tangent at its middle,
        m = doc.ifc.curved_frame(st["wall"], st["s"] + st["width"] / 2, st["width"]).matrix      # the way it runs
        x = m[:3, 0] * (1.0 if doc.ifc.curved_wall_params(st["wall"])[3] > 0 else -1.0)
    delta = np.asarray(delta, dtype=float)
    return float(delta.dot(x)), float(delta[2])


def copy_filling(doc, guid, deltas):
    """Copies of a door/window in its own wall, each moved by one of `deltas`
    (along the wall and up/down). In a group, every copy of the group gets it
    too. One undo step. Returns the new ids."""
    doors = _and_copies(doc, guid)
    shifts = [_along_wall(doc, guid, d) for d in deltas]
    walls = [doc.ifc.filling_state(d)["wall"] for d in doors]

    def action(ifc):
        out = []
        for dx, dz in shifts:
            role = None
            for i, door in enumerate(doors):
                st = ifc.filling_state(door)
                new = ifc.copy_filling(door)
                ifc.move_filling(new.GlobalId, s=st["s"] + dx, sill=st["sill"] + dz)
                group = ifc.group_of(door)
                if group is not None:
                    role = ifc.next_role(ifc.group_model(group)) if role is None else role
                    ifc.join_group(new.GlobalId, group, role)
                if i == 0:
                    out.append(new.GlobalId)
        return out

    return doc.execute(IfcCommand(t("cmd.copy"), action, changed=walls)).result


def slide_filling(doc, guid, delta):
    """Move a door/window by `delta` (world vector): along its wall and up/down
    (sill); it never leaves the wall. In a group, it moves in every copy. One undo step."""
    dx, dz = _along_wall(doc, guid, delta)
    gs = _and_copies(doc, guid)
    walls = [doc.ifc.filling_state(g)["wall"] for g in gs]

    def action(ifc):
        for g in gs:
            st = ifc.filling_state(g)
            ifc.move_filling(g, s=st["s"] + dx, sill=st["sill"] + dz)

    _edit(doc, action, gs + walls)


def delete(doc, obj_ids):
    """Delete sketches and/or IFC elements in one undo step. Deleting a door or
    window closes its opening; deleting a wall takes its doors and windows.
    An element of a group deleted alone goes from every copy of the group."""
    objs = [doc.get(i) for i in obj_ids if doc.get(i) is not None]
    sketches = [o for o in objs if not o.is_bim]
    guids = [o.id for o in objs if o.is_bim]
    for g in _alone_in_group(doc, guids):
        guids += [c for c in doc.ifc.counterparts(g) if c not in guids]
    caps = [g for g in guids if doc.ifc.kind_of(g) == "footing"]          # (a pile cap takes its piles, 0.94)
    for under in doc.ifc.supports_of(caps).values():
        guids += [p for p in under if p not in guids and doc.ifc.kind_of(p) == "pile"]
    guids += [c for c in doc.ifc.claddings_of(guids) if c not in guids]      # (a wall takes its finishes, 0.119)
    guids += doc.ifc.steel_stair_parts(guids)         # (0.509: a steel stair takes its stringers)
    guids += doc.ifc.connections_to_remove(guids)     # (0.497: a connection whole; a piece takes its connections)
    # (0.178) a finish going: those over it on its face come down onto what is left
    restack = sorted({c for g in guids if doc.ifc.kind_of(g) == "cladding" for c in doc.ifc.face_claddings(g)}
                     - set(guids))
    if guids:
        held = [m for g in guids if doc.ifc.kind_of(g) == "steel_connection"          # (0.498: an end plate's beam
                for m in doc.ifc.connection_params(g)[1][:1] if m not in guids]      # lengthened back)
        doc.execute(IfcCommand(t("cmd.delete"), lambda ifc: (ifc.release_connections(guids), ifc.remove(guids),
                                                             ifc.restack_claddings(restack)),
                               remove_sketches=sketches, changed=doc.ifc.affected_walls(guids) + restack + held))
    elif sketches:
        doc.execute(RemoveObjects(sketches, t("cmd.delete")))


VOIDABLE = ("IfcWall", "IfcWallStandardCase", "IfcSlab")


def element_frame(doc, guid):
    """An IFC element measured in its own placement frame (WallFrame), or None."""
    from ..core.openings import wall_frame as measure
    obj = doc.get(guid)
    if obj is None or not obj.is_bim:
        return None
    return doc.ifc.trim_frame(guid, measure(doc.ifc.placement(guid), obj.mesh.verts))


def wall_frame(doc, wall_guid):
    """A wall measured in its own frame (for placing doors/windows), or None."""
    obj = doc.get(wall_guid)
    if obj is None or not obj.is_bim or obj.ifc_class not in ("IfcWall", "IfcWallStandardCase"):
        return None
    return element_frame(doc, wall_guid)


class SheetHost:
    """A flat sketch face lying on a face of an IFC wall or slab (a rectangle, or any outline a
    line drew there). local: its corners in the element's frame, in order; box: an upright
    rectangle (the void is a box), else the void is that outline extruded."""

    def __init__(self, guid, name, frame, axis, side, local_pts, box=True):
        self.guid, self.name, self.frame, self.axis, self.side, self.local = guid, name, frame, axis, side, local_pts
        self.box = box
        self.lo = np.array((frame.x0, frame.y0, frame.z0))
        self.hi = np.array((frame.x0 + frame.length, frame.y1, frame.z1))
        self.thickness = float(self.hi[axis] - self.lo[axis])


def sheet_host(doc, sheet, tol=1e-4):
    """If `sheet` (a single flat sketch face) lies on a face of an IFC wall or slab,
    return a SheetHost: Push/Pull into it then cuts a void or a niche."""
    mesh = sheet.mesh
    if sheet.is_bim or len(mesh.faces) != 1 or len(mesh.faces[0]) < 3:
        return None
    pts = np.array([sheet.matrix[:3, :3] @ mesh.verts[i] + sheet.matrix[:3, 3] for i in mesh.faces[0]])
    normal = sheet.matrix[:3, :3] @ mesh.face_normal(0)
    for obj in doc.objects.values():
        if not obj.is_bim or obj.ifc_class not in VOIDABLE:
            continue
        box = obj.mesh.bounds()                   # (only the elements round the sheet are measured)
        if box is None or np.any(pts < box[0] - 1e-3) or np.any(pts > box[1] + 1e-3):
            continue
        try:
            frame = element_frame(doc, obj.id)
        except Exception:                         # (the IFC is still being read)
            continue
        inv = np.linalg.inv(frame.matrix)
        local = (inv @ np.column_stack((pts, np.ones(len(pts)))).T).T[:, :3]
        n = inv[:3, :3] @ normal
        n = n / np.linalg.norm(n)
        axis = int(np.argmax(np.abs(n)))
        if abs(n[axis]) < 1 - 1e-6:
            continue
        lo = np.array((frame.x0, frame.y0, frame.z0))
        hi = np.array((frame.x0 + frame.length, frame.y1, frame.z1))
        if n[axis] > 0 and np.all(np.abs(local[:, axis] - hi[axis]) < tol):
            side = 1
        elif n[axis] < 0 and np.all(np.abs(local[:, axis] - lo[axis]) < tol):
            side = -1
        else:
            continue
        others = [k for k in range(3) if k != axis]
        square = len(local) == 4 and all(          # (a box can be cut from an upright rectangle)
            np.all((np.abs(local[:, k] - local[:, k].min()) < tol) | (np.abs(local[:, k] - local[:, k].max()) < tol))
            for k in others)
        if all(np.all(local[:, k] >= lo[k] - tol) and np.all(local[:, k] <= hi[k] + tol) for k in others):
            return SheetHost(obj.id, obj.name, frame, axis, side, local, box=square)
    return None


def push_void(doc, sheet, host, depth):
    """Cut the sheet's outline into its host wall/slab: right through when
    `depth` reaches the thickness, else a niche of that depth — a box for an
    upright rectangle, else that outline extruded. The sketch face is used up.
    One undo step. Returns (opening GlobalId, through)."""
    through = depth >= host.thickness - 1e-6
    box_lo, box_hi = host.local.min(axis=0).copy(), host.local.max(axis=0).copy()
    a, margin = host.axis, 0.01
    if through:
        box_lo[a], box_hi[a] = host.lo[a] - margin, host.hi[a] + margin
    elif host.side > 0:
        box_lo[a], box_hi[a] = host.hi[a] - depth, host.hi[a] + margin
    else:
        box_lo[a], box_hi[a] = host.lo[a] - margin, host.lo[a] + depth
    name = t("elem.void" if through else "elem.niche")
    i, j = [k for k in range(3) if k != a]
    face = host.hi[a] if host.side > 0 else host.lo[a]

    def action(ifc):
        if not host.box:
            return ifc.add_void_profile(host.guid, host.frame.matrix, a, host.side, face,
                                        [(p[i], p[j]) for p in host.local], host.thickness + margin if through else depth,
                                        name, recess=not through).GlobalId
        return ifc.add_void(host.guid, host.frame.matrix, box_lo, box_hi, name, recess=not through).GlobalId

    cmd = doc.execute(IfcCommand(t("cmd.void"), action, remove_sketches=[sheet], changed=[host.guid]))
    return cmd.result, through


def add_bare_opening(doc, wall_guid, spec, frame, s):
    """An opening of a door's / window's size with no frame (0.110): the hole left empty; in a group, in every
    copy of the wall. One undo step. Returns its GlobalId."""
    walls = _and_copies(doc, wall_guid)
    prefix = t("elem.bare_opening")

    def action(ifc):
        first = None
        for wall in walls:
            name = "{} {}".format(prefix, ifc.count("IfcOpeningElement") + 1)
            wall_frame_ = frame if wall == wall_guid else ifc.element_frame(wall)
            new = ifc.add_bare_opening(wall, wall_frame_, s, spec.width, spec.height, spec.sill, name)
            first = first or new.GlobalId
        return first

    return doc.execute(IfcCommand(t("cmd.bare_opening"), action, changed=walls)).result


def add_wall_opening(doc, wall_guid, s, width, height, sill):
    """(0.303, Revit's Wall Opening) A rectangular opening through a straight wall, with no door or window: `s` m
    along it from its start to its left side, `sill` m over its base, `width` × `height`. It goes with the wall; in
    a group, in every copy. Refused outside the wall (its cut ends, its top or its profile). One undo step. Returns
    its GlobalId."""
    walls = _and_copies(doc, wall_guid)
    prefix = t("elem.wall_opening")
    s, width, height, sill = float(s), float(width), float(height), float(sill)

    def action(ifc):
        from shapely.geometry import box as shapely_box
        from ..ifc.edit import MIN_SIZE, EditRefused
        if width < MIN_SIZE / 2 - 1e-9 or height < MIN_SIZE / 2 - 1e-9:
            raise EditRefused("too_small")
        first = None
        for wall in walls:
            frame = ifc.trim_frame(wall, ifc.element_frame(wall))
            length, wall_height, _t = ifc.wall_params(wall)
            outline = shapely_box(0.0, 0.0, length, wall_height)
            profile = ifc.wall_profile(wall)
            if profile is not None:
                from ..core import outline_loops
                from ..core import slabs as core_slabs
                outline = core_slabs.outline_polygon(profile, outline_loops.rings(ifc.wall_profile_holes(wall))) or \
                    outline
            if (s < frame.x0 - 1e-6 or s + width > frame.x0 + frame.length + 1e-6 or sill < -1e-6
                    or not outline.buffer(1e-6).contains(shapely_box(s, sill, s + width, sill + height))):
                raise EditRefused("opening_outside")
            name = "{} {}".format(prefix, ifc.count("IfcOpeningElement") + 1)
            new = ifc.add_bare_opening(wall, ifc.element_frame(wall), s, width, height, sill, name)
            first = first or new.GlobalId
        return first

    return doc.execute(IfcCommand(t("cmd.wall_opening"), action, changed=walls)).result


def add_wall_niche(doc, wall_guid, s, width, height, sill, depth, outward):
    """(0.374, the addon's «Nicho») A rectangular niche in the face of a straight wall that `outward` (world, out of
    that face) points from: `s` m along it, `sill` over its base, `width` × `height`, `depth` m into the wall (less
    than its thickness). It goes with the wall; in a group, in every copy. One undo step. Its GlobalId."""
    walls = _and_copies(doc, wall_guid)
    prefix = t("elem.niche")
    s, width, height, sill, depth = float(s), float(width), float(height), float(sill), float(depth)

    def action(ifc):
        from shapely.geometry import box as shapely_box
        from ..ifc.edit import MIN_SIZE, EditRefused
        if width < MIN_SIZE / 2 - 1e-9 or height < MIN_SIZE / 2 - 1e-9 or depth < 0.005:
            raise EditRefused("too_small")
        first = None
        for wall in walls:
            frame = ifc.trim_frame(wall, ifc.element_frame(wall))
            length, wall_height, thickness = ifc.wall_params(wall)
            if depth >= thickness - 0.01:
                raise EditRefused("niche_deep")
            if (s < frame.x0 - 1e-6 or s + width > frame.x0 + frame.length + 1e-6 or sill < -1e-6
                    or not shapely_box(0.0, 0.0, length, wall_height).buffer(1e-6).contains(
                        shapely_box(s, sill, s + width, sill + height))):
                raise EditRefused("opening_outside")
            side = 1.0 if float(np.asarray(outward, dtype=float) @ frame.matrix[:3, 1]) >= 0 else -1.0
            name = "{} {}".format(prefix, ifc.count("IfcOpeningElement") + 1)
            new = ifc.add_niche(wall, ifc.element_frame(wall), s, width, height, sill, depth, side, name)
            first = first or new.GlobalId
        return first

    return doc.execute(IfcCommand(t("cmd.niche"), action, changed=walls)).result


def add_wall_reveal(doc, wall, side, vertical, at, width=0.02, depth=0.01):
    """(0.305, Revit's Wall Reveal) A groove in a straight wall's face (its left, side +1, or right): level along the
    whole wall, its middle `at` over the wall's base, or vertical up the whole wall, `at` along it; it fits the wall
    whenever the wall changes. In a group, in every copy. One undo step. Returns its GlobalId."""
    walls = _and_copies(doc, wall)
    prefix = t("elem.reveal")

    def action(ifc):
        first = None
        for g in walls:
            name = "{} {}".format(prefix, ifc.count("IfcOpeningElement") + 1)
            new = ifc.add_wall_reveal(g, side, vertical, at, width, depth, name)
            first = first or new.GlobalId
        return first

    return doc.execute(IfcCommand(t("cmd.wall_reveal"), action, changed=walls)).result


def remove_wall_reveal(doc, wall, opening):
    """(0.305) A reveal of a wall taken away. One undo step."""
    _edit(doc, lambda ifc: ifc.remove_wall_reveal(wall, opening), [wall], "cmd.remove_reveal")


def set_mark(doc, guid, mark):
    """A door's / window's mark (0.110: its IFC Tag, as "P3"). One undo step."""
    doc.execute(IfcCommand(t("cmd.mark"), lambda ifc: setattr(ifc.by_guid(guid), "Tag", str(mark) or None),
                           touched=[guid]))


def renumber_openings(doc):
    """Every door and window numbered again in the plans' reading order (0.110). One undo step. Returns how
    many."""
    guids = [e.GlobalId for cls in ("IfcDoor", "IfcWindow") for e in doc.ifc.file.by_type(cls)]
    if not guids:
        return 0                                    # (0.325: no undo step with nothing in it)
    return doc.execute(IfcCommand(t("cmd.renumber"), lambda ifc: ifc.renumber_openings(), touched=guids)).result


def add_opening(doc, wall_guid, spec, frame, s, side, hinge_at=None):
    """Door or window in a wall (one undo step); in a group, in every copy of
    that wall too. Returns the new element's GlobalId. (0.359) hinge_at: a door's hinges wanted at the jamb nearer
    this plan point (the mouse's end of the opening) — turned there in the same step when its type has them at the
    other."""
    language = lang()
    prefix = t("elem." + spec.kind)
    ifc_class = "IfcDoor" if spec.kind == "door" else "IfcWindow"
    walls = _and_copies(doc, wall_guid)

    def action(ifc):
        first, role = None, None
        for wall in walls:
            name = "{} {}".format(prefix, ifc.count(ifc_class) + 1)
            wall_frame_ = frame if wall == wall_guid else ifc.element_frame(wall)   # same place in each copy
            new = ifc.add_opening(wall, spec, wall_frame_, s, side, name, language)
            if hinge_at is not None and spec.kind == "door" and wall == wall_guid and \
                    _hinges_away(ifc, new.GlobalId, hinge_at):
                ifc.flip_door(new.GlobalId, True, False, language)
            group = ifc.group_of(wall)
            if group is not None:
                role = ifc.next_role(ifc.group_model(group)) if role is None else role
                ifc.join_group(new.GlobalId, group, role)
            first = first or new.GlobalId
        return first

    cmd = doc.execute(IfcCommand(t("cmd." + spec.kind), action, changed=walls))
    return cmd.result


def add_curved_opening(doc, wall_guid, spec, along, side, bare=False):
    """(0.177) A door or window — or, bare, only its hole — in a curved wall, its middle `along` m from the wall's
    start, turned to its face `side` (−1 the outer, +1 the inner); in a group, in every copy of the wall. One undo
    step. Returns its GlobalId."""
    language = lang()
    prefix = t("elem.bare_opening" if bare else "elem." + spec.kind)
    ifc_class = "IfcOpeningElement" if bare else ("IfcDoor" if spec.kind == "door" else "IfcWindow")
    walls = _and_copies(doc, wall_guid)

    def action(ifc):
        first = None
        for wall in walls:
            name = "{} {}".format(prefix, ifc.count(ifc_class) + 1)
            first = first or ifc.add_curved_opening(wall, spec, along, side, name, language, bare=bare).GlobalId
        return first

    label = "cmd.bare_opening" if bare else "cmd." + spec.kind
    return doc.execute(IfcCommand(t(label), action, changed=walls)).result
