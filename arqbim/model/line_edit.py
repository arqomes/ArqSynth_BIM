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
