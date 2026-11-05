"""Faces closed by new lines with the loose lines already drawn (0.373), as SketchUp makes them whatever chain each
line was drawn in: an arc ending on two lines, a line closing an outline drawn before, a freehand loop. One undo
step: the new lines go in, the loops become a face sketch (one per plane, its faces sharing their edges), and the
lines on a loop leave the loose-line sketches they were in (the rest stay lines; a curve that lost pieces is a curve
no more)."""

from dataclasses import dataclass

import numpy as np

from ..core.lines import LOOP_TOL, close_loops, drop_collinear, polygon_frame
from ..core.mesh import PolyMesh
from ..i18n import t
from . import line_edit
from .document import ReplaceObjects, SketchObject


@dataclass
class Closed:
    """What closing made: the face sketches, their faces' area (m²), the ends of the new lines left as lines."""
    faces: list
    area: float
    corners: int
    loose: list                 # the sketches of lines left (the new ones' remainder, the old ones cut)


def _world(obj):
    v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
    return v @ obj.matrix[:3, :3].T + obj.matrix[:3, 3]


def _lines_sketch(name, pieces, matrix=None, obj_id=None, curve=None):
    """A loose-line sketch of world pieces [(p, q)] (its points joined where they meet), in `matrix`'s frame."""
    m = np.eye(4) if matrix is None else np.asarray(matrix, dtype=float)
    inv = np.linalg.inv(m)
    verts, pairs = [], []
    for p, q in pieces:
        ids = []
        for w in (p, q):
            k = next((i for i, v in enumerate(verts) if np.linalg.norm(v - w) <= LOOP_TOL), None)
            if k is None:
                verts.append(np.asarray(w, dtype=float))
                k = len(verts) - 1
            ids.append(k)
        if ids[0] != ids[1]:
            pairs.append(tuple(ids))
    local = [inv[:3, :3] @ v + inv[:3, 3] for v in verts]
    return SketchObject(name, m, PolyMesh(local, lines=pairs), obj_id=obj_id, curve=curve)


def face_sketch(doc, loops, view_dir=None):
    """One sketch with the loops' faces (on one plane, sharing their points), or None."""
    rings = [np.asarray(drop_collinear(loop), dtype=float) for loop in loops]
    frame = polygon_frame(rings[0], view_dir=view_dir)
    if frame is None:
        return None
    matrix = frame[0]
    inv = np.linalg.inv(matrix)
    verts, faces = [], []
    for ring in rings:
        local = (inv @ np.column_stack((ring, np.ones(len(ring)))).T).T[:, :3]
        if np.any(np.abs(local[:, 2]) > LOOP_TOL * 10):
            continue
        local[:, 2] = 0.0
        x, y = local[:, 0], local[:, 1]
        if float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)) < 0:
            local = local[::-1]
        face = []
        for q in local:
            k = next((i for i, v in enumerate(verts) if np.linalg.norm(v - q) <= LOOP_TOL), None)
            if k is None:
                verts.append(q)
                k = len(verts) - 1
            face.append(k)
        faces.append(face)
    if not faces:
        return None
    return SketchObject(t("obj.name", n=doc.next_number()), matrix, PolyMesh(verts, faces))


def close_with(doc, new, plane, label, view_dir=None, keep_new=True):
    """The new loose-line sketch `new` (not in the document yet; its lines on `plane` = (point, normal)) put in, and
    the faces it closes with the loose lines there made — in one undo step. Returns Closed, or None when it closes
    nothing (then nothing was done: the caller adds it as it would)."""
    others = [o for o in doc.objects.values() if line_edit.is_lines(o) and o.id != new.id]
    w_new = _world(new)
    new_segs = [(w_new[i], w_new[j]) for i, j in new.mesh.lines]
    old, owner = [], []
    for o in others:
        w = _world(o)
        for k, (i, j) in enumerate(o.mesh.lines):
            old.append((w[i], w[j]))
            owner.append((o, k))
    loops, pieces = close_loops(new_segs, old, plane)
    if not loops:
        return None
    face = face_sketch(doc, loops, view_dir)
    if face is None:
        return None
    left_new = [(p, q) for ps in pieces[:len(new_segs)] for p, q, used in ps if not used]
    changed = {}
    for (o, k), ps in zip(owner, pieces[len(new_segs):]):
        cut = len(ps) > 1 or any(used for _p, _q, used in ps)
        entry = changed.setdefault(o.id, [o, [], False, False])
        entry[1] += [(p, q) for p, q, used in ps if not used]
        entry[2] |= cut
        entry[3] |= any(used for _p, _q, used in ps)
    remove, add = [], [face]
    for obj_id, (o, kept, cut, used) in changed.items():
        if not cut:
            continue
        remove.append(o)
        if kept:
            curve = ({"kind": "curve"} if used else o.curve) if o.curve else None
            add.append(_lines_sketch(o.name, kept, o.matrix, obj_id=o.id, curve=curve))
    loose = [a for a in add[1:]]
    if left_new and keep_new:
        whole = len(left_new) == len(new_segs)
        rest = _lines_sketch(new.name or t("obj.lines", n=doc.next_number()), left_new, new.matrix, obj_id=new.id,
                             curve=(new.curve if whole else {"kind": "curve"}) if new.curve else None)
        add.append(rest)
        loose.append(rest)
    doc.execute(ReplaceObjects(remove, add, label))
    area = sum(face.mesh.face_area(k) for k in range(len(face.mesh.faces)))
    return Closed([face], area, len(face.mesh.faces[0]), loose)
