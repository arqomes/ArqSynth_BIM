"""Parametric lines (0.62): the lines drawn with the Line tool stay editable â€” an end moved
(by its grip, or by typing its point), a segment's length or angle changed â€” and the lines
joined there follow: every loose line's end lying at the point moved goes with it, whatever
chain it was drawn in. One undo step. Faces are left alone (an outline closed into a face is
a face, edited with Push/Pull and Move).
"""

import math

import numpy as np

from ..core.sketch_geometry import transform_point
from ..i18n import t
from .document import ReplaceMeshes

TOL = 1e-6                # two ends this close are one point (joined)
MIN_LENGTH = 1e-3         # a segment shorter than this would vanish: refused


class LineRefused(ValueError):
    """An edit that would spoil a line (i18n "refuse." + code says why)."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def is_lines(obj):
    """Loose lines: a sketch of lines only (no face)."""
    return obj is not None and not obj.is_bim and bool(obj.mesh.lines) and not obj.mesh.faces


def segments(obj):
    """[(i, j, world a, world b)] of a lines sketch."""
    world = [transform_point(obj.matrix, v) for v in obj.mesh.verts]
    return [(i, j, world[i], world[j]) for i, j in obj.mesh.lines]


def moved_lines(doc, moves):
    """The loose lines' meshes after moving the ends at the points `moves` [(before, after)] â€”
    {obj_id: (object, new mesh)} â€” and the segments touched, in world coordinates, for a preview."""
    out, touched = {}, []
    for obj in doc.objects.values():
        if not is_lines(obj):
            continue
        inv = None
        mesh = None
        moved = {}
        for k, v in enumerate(obj.mesh.verts):
            w = transform_point(obj.matrix, v)
            for before, after in moves:
                if np.linalg.norm(w - np.asarray(before, dtype=float)) < TOL:
                    if mesh is None:
                        mesh, inv = obj.mesh.copy(), np.linalg.inv(obj.matrix)
                    mesh.verts[k] = transform_point(inv, np.asarray(after, dtype=float))
                    moved[k] = np.asarray(after, dtype=float)
                    break
        if mesh is None:
            continue
        out[obj.id] = (obj, mesh)
        for i, j in mesh.lines:
            if i in moved or j in moved:
                touched.append((transform_point(obj.matrix, mesh.verts[i]), transform_point(obj.matrix, mesh.verts[j])))
    return out, touched


def move_points(doc, moves, label=None):
    """Move the loose lines' ends lying at `moves`' points [(before, after)]: the lines joined there
    follow. One undo step. Returns how many lines changed; LineRefused("too_short") if a segment
    would vanish."""
    found, touched = moved_lines(doc, moves)
    if not found:
        return 0
    if any(np.linalg.norm(b - a) < MIN_LENGTH for a, b in touched):
        raise LineRefused("too_short")
    if any(getattr(obj, "curve", None) for obj, _mesh in found.values()):
        # (0.373) a curve (an arc…) whose point was dragged follows it no more: a curve still (picked whole)
        from .document import ReplaceObjects, SketchObject
        doc.execute(ReplaceObjects([obj for obj, _m in found.values()],
                                   [SketchObject(obj.name, obj.matrix, mesh, obj_id=obj.id, component=obj.component,
                                                 curve={"kind": "curve"} if obj.curve else None)
                                    for obj, mesh in found.values()], label or t("cmd.line_edit")))
        return len(found)
    doc.execute(ReplaceMeshes([(obj.id, obj.mesh, mesh) for obj, mesh in found.values()],
                              label or t("cmd.line_edit")))
    return len(found)


def segment_at(doc, obj_id, a, b):
    """(0.452) The piece (i, j) of a lines sketch whose ends are the world points a and b (either way), or None."""
    obj = doc.get(obj_id)
    if not is_lines(obj) or obj.curve:
        return None
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    for i, j, p, q in segments(obj):
        if (np.linalg.norm(p - a) <= TOL and np.linalg.norm(q - b) <= TOL) or \
                (np.linalg.norm(p - b) <= TOL and np.linalg.norm(q - a) <= TOL):
            return i, j
    return None


def fillet_lines(doc, first, keep_first, second, keep_second, radius, label=None):
    """(0.452, Revit's «Fillet Arc» on lines) Two loose lines' pieces — first = (obj_id, i, j), second likewise —
    trimmed / extended to where an arc of `radius`, tangent to both on the side of each where it was picked (keep_*:
    world points), touches them (each its own point there: a corner they shared is split), and the arc drawn between
    them, a line of the first's sketch. One undo step. LineRefused("parallel") / ("too_big")."""
    from ..core.fillet import arc_points, fillet
    (oa_id, ia, ja), (ob_id, ib, jb) = first, second
    oa, ob = doc.get(oa_id), doc.get(ob_id)
    wa = [transform_point(oa.matrix, v) for v in oa.mesh.verts]
    wb = [transform_point(ob.matrix, v) for v in ob.mesh.verts]
    f = fillet((wa[ia], wa[ja]), keep_first, (wb[ib], wb[jb]), keep_second, radius=radius)
    if f is None:
        raise LineRefused("parallel")
    reach = float(np.linalg.norm(f.tangents[0] - f.cross))
    if any(reach > room - TOL for room in f.room):
        raise LineRefused("too_big")
    meshes = {oa_id: oa.mesh.copy()}
    if ob_id != oa_id:
        meshes[ob_id] = ob.mesh.copy()
    objs = {oa_id: oa, ob_id: ob}
    z = float(wa[ia][2])

    def local(obj_id, p):
        m = np.linalg.inv(objs[obj_id].matrix)
        return (m @ np.array((float(p[0]), float(p[1]), z, 1.0)))[:3]

    def trim(obj_id, i, j, end, point):
        mesh = meshes[obj_id]
        new = mesh.add_vert(local(obj_id, point))
        k = next(n for n, ln in enumerate(mesh.lines) if tuple(ln) in ((i, j), (j, i)))
        a, b = mesh.lines[k]
        corner = j if end == "end" else i
        mesh.lines[k] = (new, b) if a == corner else (a, new)
        return new

    start = trim(oa_id, ia, ja, f.ends[0], f.tangents[0])
    trim(ob_id, ib, jb, f.ends[1], f.tangents[1])
    mesh = meshes[oa_id]                                     # (the arc in the first's sketch)
    last = start
    for p in arc_points(f)[1:]:
        nxt = mesh.add_vert(local(oa_id, p))
        mesh.lines.append((last, nxt))
        last = nxt
    doc.execute(ReplaceMeshes([(k, objs[k].mesh, m) for k, m in meshes.items()], label or ""))
    return f


def set_length(doc, obj_id, i, j, length):
    """Segment iâ†’j `length` long: its end j moves along it (the lines joined at j follow)."""
    obj = doc.get(obj_id)
    a, b = transform_point(obj.matrix, obj.mesh.verts[i]), transform_point(obj.matrix, obj.mesh.verts[j])
    d = b - a
    if length < MIN_LENGTH or np.linalg.norm(d) < MIN_LENGTH:
        raise LineRefused("too_short")
    return move_points(doc, [(b, a + d / np.linalg.norm(d) * length)], t("cmd.line_length"))


def set_angle(doc, obj_id, i, j, degrees):
    """Segment iâ†’j turned to `degrees` from the red axis (seen from above), its length and start kept."""
    obj = doc.get(obj_id)
    a, b = transform_point(obj.matrix, obj.mesh.verts[i]), transform_point(obj.matrix, obj.mesh.verts[j])
    flat = math.hypot(*(b - a)[:2])
    if flat < MIN_LENGTH:
        raise LineRefused("vertical_line")
    r = math.radians(degrees)
    end = np.array((a[0] + flat * math.cos(r), a[1] + flat * math.sin(r), b[2]))
    return move_points(doc, [(b, end)], t("cmd.line_angle"))


def set_point(doc, obj_id, k, point):
    """Vertex k of a lines sketch to the world point `point` (the lines joined there follow)."""
    obj = doc.get(obj_id)
    return move_points(doc, [(transform_point(obj.matrix, obj.mesh.verts[k]), np.asarray(point, dtype=float))])
