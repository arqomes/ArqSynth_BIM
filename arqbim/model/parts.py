"""Faces of sketches picked alone (0.310, SketchUp's click on a face): Delete takes them out, Move / Rotate move or
turn just them — the faces beside them stretch. One undo step each.

`parts` is the viewport's face_selection: {obj_id: (frozenset of face indices, with their edges)}.

(0.373) Loose lines picked alone (SketchUp's click on an edge): `lines` is the viewport's line_selection — {obj_id:
frozenset of indices in the sketch's lines}. Delete takes them out; Move / Rotate move them, the loose lines whose
ends are at theirs stretch to stay joined (model/line_edit); copies of them, and of faces picked alone, are new
sketches."""

import numpy as np

from ..core import curves as core_curves
from ..core import sketch_geometry as sg
from ..core.mesh import PolyMesh
from ..i18n import t
from . import line_edit
from .document import JoinedCommand, RemoveObjects, ReplaceMeshes, ReplaceObjects, SketchObject


def _sketches(doc, parts):
    return [(doc.get(k), faces, edges) for k, (faces, edges) in parts.items()
            if doc.get(k) is not None and not doc.get(k).is_bim]


def count(doc, parts):
    """How many faces they are, as SketchUp counts them (an offset's frame of four strips: one)."""
    n = 0
    for obj, faces, _edges in _sketches(doc, parts):
        left = set(faces)
        while left:
            left -= sg.surface_faces(obj.mesh, next(iter(left)))
            n += 1
    return n


def area(doc, parts):
    """The faces' area (m², in the model: the sketches' placement counted)."""
    total = 0.0
    for obj, faces, _edges in _sketches(doc, parts):
        for g in faces:
            pts = np.array(sg.face_world_points(obj.matrix, obj.mesh, g))
            total += 0.5 * float(np.linalg.norm(sum(np.cross(pts[i] - pts[0], pts[i + 1] - pts[0])
                                                    for i in range(1, len(pts) - 1))))
    return total


def delete(doc, parts):
    """The faces taken out (their outline kept as lines, unless picked with their edges); a sketch left with
    nothing goes. How many faces went."""
    changes, gone, n = [], [], count(doc, parts)
    for obj, faces, edges in _sketches(doc, parts):
        after = sg.remove_faces(obj.mesh, faces, keep_edges=not edges)
        if after.faces or after.lines:
            changes.append((obj.id, obj.mesh, after))
        else:
            gone.append(obj)
    commands = ([ReplaceMeshes(changes, t("cmd.delete"))] if changes else []) + \
        ([RemoveObjects(gone, t("cmd.delete"))] if gone else [])
    if commands:
        doc.execute(commands[0] if len(commands) == 1 else JoinedCommand(commands, t("cmd.delete")))
    return n


def transform(doc, parts, matrix, label):
    """The faces moved / turned by `matrix` (world). The faces picked stay picked (their numbers kept)."""
    m = np.asarray(matrix, dtype=float)
    changes = []
    for obj, faces, _edges in _sketches(doc, parts):
        local = np.linalg.inv(obj.matrix) @ m @ obj.matrix
        changes.append((obj.id, obj.mesh, sg.move_part(obj.mesh, faces, local)))
    if changes:
        doc.execute(ReplaceMeshes(changes, label))
    return bool(changes)


def segments(doc, parts):
    """World ends of the faces' edges (their outline and the lines in them): (2N, 3), for a tool's ghost."""
    segs = []
    for obj, faces, _edges in _sketches(doc, parts):
        v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
        world = v @ obj.matrix[:3, :3].T + obj.matrix[:3, 3]
        for a, b in sg.part_edges(obj.mesh, faces):
            segs += [world[a], world[b]]
    return np.array(segs, dtype=float).reshape(-1, 3)


def face_copies(doc, parts):
    """(0.373) The faces picked alone as sketches of their own, where they are (not put in the document): what a copy
    of them is — the faces and their edges, as SketchUp copies a face."""
    out = []
    for obj, faces, _edges in _sketches(doc, parts):
        mesh = obj.mesh
        kept = [list(mesh.faces[g]) for g in sorted(faces) if g < len(mesh.faces)]
        paint = [mesh.paint_of(g) for g in sorted(faces) if g < len(mesh.faces)]     # (0.392: with their paint)
        if kept:
            out.append(SketchObject(obj.name, obj.matrix, sg.compact(PolyMesh(mesh.verts, kept, mesh.hidden,
                                                                              paint=paint))))
    return out


# ---------------------------------------------------------------- loose lines picked alone (0.373)

def _line_sketches(doc, lines):
    out = []
    for k, picked in lines.items():
        obj = doc.get(k)
        if line_edit.is_lines(obj):
            out.append((obj, sorted(i for i in picked if i < len(obj.mesh.lines))))
    return [(o, ks) for o, ks in out if ks]


def _world(obj):
    v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
    return v @ obj.matrix[:3, :3].T + obj.matrix[:3, 3]


def line_count(doc, lines):
    return sum(len(ks) for _o, ks in _line_sketches(doc, lines))


def line_length(doc, lines):
    """Their length together (m, in the model)."""
    total = 0.0
    for obj, ks in _line_sketches(doc, lines):
        w = _world(obj)
        total += sum(float(np.linalg.norm(w[obj.mesh.lines[k][1]] - w[obj.mesh.lines[k][0]])) for k in ks)
    return total


def line_segments(doc, lines):
    """World ends of the lines: (2N, 3), for a tool's ghost."""
    segs = []
    for obj, ks in _line_sketches(doc, lines):
        w = _world(obj)
        for k in ks:
            a, b = obj.mesh.lines[k]
            segs += [w[a], w[b]]
    return np.array(segs, dtype=float).reshape(-1, 3)


def joined_lines(mesh, start):
    """The lines of a sketch joined to lines[start] through their ends (start's included): their indices — what
    SketchUp's double click on an edge picks."""
    around = {}
    for k, (a, b) in enumerate(mesh.lines):
        around.setdefault(a, []).append(k)
        around.setdefault(b, []).append(k)
    seen, todo = {start}, [start]
    while todo:
        for v in mesh.lines[todo.pop()]:
            for k in around[v]:
                if k not in seen:
                    seen.add(k)
                    todo.append(k)
    return frozenset(seen)


def touching_lines(doc, obj_ids, tol=line_edit.TOL):
    """The loose-line sketches joined to these through their ends, these included (what a triple click picks):
    their ids. Only the ends are looked at (a dictionary of rounded points, no search through every line)."""
    sketches = [o for o in doc.objects.values() if line_edit.is_lines(o)]
    key = lambda p: tuple(np.round(np.asarray(p) / (tol * 10)).astype(np.int64))     # noqa: E731
    at = {}
    for o in sketches:
        for p in _world(o)[sorted({v for e in o.mesh.lines for v in e})]:
            at.setdefault(key(p), set()).add(o.id)
    by_id = {o.id: o for o in sketches}
    seen, todo = set(obj_ids), list(obj_ids)
    while todo:
        o = by_id.get(todo.pop())
        if o is None:
            continue
        for p in _world(o)[sorted({v for e in o.mesh.lines for v in e})]:
            for other in at.get(key(p), ()):
                if other not in seen:
                    seen.add(other)
                    todo.append(other)
    return seen


def _without(obj, ks):
    """The sketch without its lines `ks` (None: nothing left). A curve losing some of its pieces is a curve no more."""
    mesh = obj.mesh.copy()
    mesh.lines = [e for k, e in enumerate(mesh.lines) if k not in set(ks)]
    mesh = sg.compact(mesh)
    if not mesh.lines:
        return None
    return SketchObject(obj.name, obj.matrix, mesh, obj_id=obj.id, component=obj.component)


def delete_lines(doc, lines):
    """The lines taken out (a sketch left with none goes). How many went."""
    changed, gone, n = [], [], 0
    for obj, ks in _line_sketches(doc, lines):
        n += len(ks)
        after = _without(obj, ks)
        if after is None:
            gone.append(obj)
        else:
            changed.append((obj, after))
    if changed or gone:
        doc.execute(ReplaceObjects([o for o, _a in changed] + gone, [a for _o, a in changed], t("cmd.delete")))
    return n


def transform_lines(doc, lines, matrix, label):
    """The lines moved / turned by `matrix` (world): their ends go, and every loose line's end lying where one of
    theirs was goes with it (the lines joined there stretch, as SketchUp's). A curve all of whose points went keeps
    its data (moved too); one bent by it is a curve no more. One undo step; their numbers kept. Raises
    line_edit.LineRefused("too_short") when a line would vanish."""
    m = np.asarray(matrix, dtype=float)
    ends = []
    for obj, ks in _line_sketches(doc, lines):
        w = _world(obj)
        for k in ks:
            for v in obj.mesh.lines[k]:
                if all(np.linalg.norm(w[v] - q) > line_edit.TOL for q in ends):
                    ends.append(w[v])
    if not ends:
        return False
    moves = [(p, m[:3, :3] @ p + m[:3, 3]) for p in ends]
    found, touched = line_edit.moved_lines(doc, moves)
    if any(np.linalg.norm(b - a) < line_edit.MIN_LENGTH for a, b in touched):
        raise line_edit.LineRefused("too_short")
    before, after = [], []
    for obj, mesh in found.values():
        curve = obj.curve
        if curve:
            moved = [k for k in range(len(mesh.verts)) if np.linalg.norm(mesh.verts[k] - obj.mesh.verts[k]) > 1e-12]
            curve = core_curves.transform_curve(curve, np.linalg.inv(obj.matrix) @ m @ obj.matrix) \
                if len(moved) == len(mesh.verts) else {"kind": "curve"}
        before.append(obj)
        after.append(SketchObject(obj.name, obj.matrix, mesh, obj_id=obj.id, component=obj.component, curve=curve))
    doc.execute(ReplaceObjects(before, after, label))
    return True


def line_copies(doc, lines):
    """The lines as sketches of their own, where they are (not put in the document): a copy of them — one sketch
    per sketch they come from (a curve picked whole stays a curve)."""
    out = []
    for obj, ks in _line_sketches(doc, lines):
        whole = len(ks) == len(obj.mesh.lines)
        mesh = obj.mesh.copy()
        mesh.lines = [obj.mesh.lines[k] for k in ks]
        out.append(SketchObject(obj.name, obj.matrix, sg.compact(mesh),
                                curve=obj.curve if whole else None))
    return out


def add_copies(doc, sketches, matrices, label):
    """Copies of sketches not in the document (face_copies, line_copies, the clipboard's): one set per matrix, in
    one undo step. Their ids."""
    new = []
    for m in matrices:
        for o in sketches:
            name = t("obj.name", n=doc.next_number()) if o.mesh.faces else t("obj.lines", n=doc.next_number())
            new.append(SketchObject(name, np.asarray(m, dtype=float) @ o.matrix, o.mesh.copy(),
                                    curve=getattr(o, "curve", None)))
    if new:
        doc.execute(ReplaceObjects([], new, label))
    return [o.id for o in new]


def sketch_segments(sketches):
    """World ends of the sketches' visible edges and lines (not in the document): (2N, 3), for a tool's ghost."""
    segs = []
    for o in sketches:
        w = _world(o)
        for a, b in o.mesh.visible_edges():
            segs += [w[a], w[b]]
    return np.array(segs, dtype=float).reshape(-1, 3)
