"""Lines that divide faces (SketchUp): a line drawn across a face, from its outline to its
outline — or a path of lines through it — divides the face in two, and Push/Pull then moves
one part only. On a sketch the face itself is divided (a line across a box's top: two tops).
On an IFC wall or slab made by ArqBIM the face is covered by two sketch faces lying on it, of
any shape (a slanted line: two trapeziums or triangles; a level or upright one: rectangles):
pushed into the element, a part becomes a niche or an opening of its outline (bim.push_void);
pulled out, a sketch volume.
"""

from dataclasses import dataclass

import numpy as np

from ..core.mesh import PolyMesh
from ..core.sketch_geometry import rectangle_matrix, split_by_segment, split_face
from ..i18n import t
from .document import ReplaceObjects, SketchObject

TOL = 1e-5          # m: a point this near a face's outline is on it
LEVEL_TOL = 0.01    # m: on a wall, a line whose ends differ this little in height is level (a wall not
LEVEL_SLOPE = 0.0875    # along the red or green axis has no axis inference to make it exactly level)… or
#                     less than 5° off level / upright (drawn by hand): it is taken as level at its first point
EDGE_TOL = 0.02     # m: on a wall, an end of the line this near the face's side is on it (clicked by hand)


@dataclass
class Split:
    command: object     # one undo step: the faces divided, the lines used up
    start: int          # where in the path the dividing part starts (the lines before it stay lines)
    faces: int          # how many faces were divided
    host: str = None    # the wall / slab whose face got two parts, else None


def split_by_path(doc, path, lines=None, shown=None):
    """The Line tool's chain `path` (world points, the last one just added) divides faces?
    Tried: its last segment across the sketches' faces (any number of them), then a longer end
    of the path through one face, then the last segment across a wall's or slab's face.
    lines: the sketch object holding the chain's lines (vertex k = path[k]): the lines that became
    edges are taken out of it. shown(obj): only those on screen. Returns a Split or None."""
    path = [np.asarray(p, dtype=float) for p in path]
    if len(path) < 2:
        return None
    sketches = [o for o in doc.objects.values() if not o.is_bim and o.mesh.faces and (shown is None or shown(o))]
    for start in range(len(path) - 2, -1, -1):
        part = path[start:]
        done = []
        for obj in sketches:
            if not _near(obj, part):
                continue
            inv = np.linalg.inv(obj.matrix)
            local = [(inv @ np.append(p, 1.0))[:3] for p in part]
            mesh = obj.mesh.copy()
            if len(part) == 2:
                count = split_by_segment(mesh, local[0], local[1], TOL)
            else:
                count = int(any(split_face(mesh, fi, local, TOL) is not None for fi in range(len(mesh.faces))))
            if count:
                done.append((obj, mesh, count))
        if done:
            return _sketch_split(doc, done, start, lines)
    return _host_split(doc, path, lines, shown)


def _near(obj, points, tol=TOL):
    v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
    if not len(v):
        return False
    w = v @ obj.matrix[:3, :3].T + obj.matrix[:3, 3]
    lo, hi = w.min(axis=0) - tol, w.max(axis=0) + tol
    return all(np.all(p >= lo) and np.all(p <= hi) for p in points)


def _lines_left(lines, start):
    """The chain's lines object with only the lines before `start` (None: nothing left)."""
    if lines is None or start == 0:
        return None
    mesh = PolyMesh(lines.mesh.verts[:start + 1], lines=[(k, k + 1) for k in range(start)])
    return SketchObject(lines.name, lines.matrix, mesh, obj_id=lines.id)


def _sketch_split(doc, done, start, lines):
    remove, add = [], []
    for obj, mesh, _count in done:
        remove.append(obj)
        if len(obj.mesh.faces) == 1 and not obj.mesh.is_closed():
            # a flat sketch (a rectangle on a wall…): each part on its own, so each can be pushed
            # into its wall or slab, or pulled up, alone
            for k, face in enumerate(mesh.faces):
                ids = list(dict.fromkeys(face))
                part = PolyMesh([mesh.verts[i] for i in ids], [[ids.index(i) for i in face]])
                add.append(SketchObject(obj.name if k == 0 else t("obj.name", n=doc.next_number()), obj.matrix,
                                        part, obj_id=obj.id if k == 0 else None, component=obj.component))
        else:
            add.append(SketchObject(obj.name, obj.matrix, mesh, obj_id=obj.id, component=obj.component))
    if lines is not None:
        remove.append(lines)
        kept = _lines_left(lines, start)
        if kept is not None:
            add.append(kept)
    count = sum(c for _o, _m, c in done)
    return Split(ReplaceObjects(remove, add, t("cmd.split_face")), start, count)


def _host_split(doc, path, lines, shown):
    """The end of the path (its last segment, or more of it) across a face of an IFC wall / slab
    made by ArqBIM, from the face's outline to its outline: two sketch faces on that face, of any
    shape (in place of the face's own parts)."""
    from . import bim
    hosts = []
    for obj in doc.objects.values():
        if not obj.is_bim or obj.ifc_class not in bim.VOIDABLE or (shown is not None and not shown(obj)):
            continue
        box = obj.mesh.bounds()
        if box is not None and all(np.all(p >= box[0] - EDGE_TOL) and np.all(p <= box[1] + EDGE_TOL)
                                   for p in path[-2:]):
            hosts.append(obj)
    for start in range(len(path) - 2, -1, -1):
        for obj in hosts:
            try:
                frame = bim.element_frame(doc, obj.id)
            except Exception:                   # (the IFC is still being read)
                continue
            parts = _face_parts(frame, obj.mesh.verts, path[start:]) if frame is not None else None
            if parts is None:
                continue
            sheets = [SketchObject(t("obj.name", n=doc.next_number()), m, mesh) for m, mesh in parts]
            remove = [lines] if lines is not None else []
            kept = _lines_left(lines, start)
            command = ReplaceObjects(remove, sheets + ([kept] if kept is not None else []), t("cmd.split_face"))
            return Split(command, start, 1, obj.name)
    return None


def host_face(doc, a, b, shown=None):
    """The name of the IFC wall / slab (made by ArqBIM) on one of whose faces the segment a-b lies,
    or None — to say why a line drawn there did not divide it."""
    from . import bim
    for obj in doc.objects.values():
        if not obj.is_bim or obj.ifc_class not in bim.VOIDABLE or (shown is not None and not shown(obj)):
            continue
        box = obj.mesh.bounds()
        if box is None or not all(np.all(p >= box[0] - TOL) and np.all(p <= box[1] + TOL) for p in (a, b)):
            continue
        try:
            m = doc.ifc.placement(obj.id)
        except Exception:
            continue
        inv = np.linalg.inv(m)
        local = (inv @ np.column_stack((obj.mesh.verts, np.ones(len(obj.mesh.verts)))).T).T[:, :3]
        la, lb = (inv @ np.append(a, 1.0))[:3], (inv @ np.append(b, 1.0))[:3]
        for axis in range(3):
            for c in (local[:, axis].min(), local[:, axis].max()):
                if abs(la[axis] - c) < 1e-4 and abs(lb[axis] - c) < 1e-4:
                    return obj.name
    return None


def _face_parts(frame, verts, path):
    """[(matrix, mesh)] of the two sketch faces a path (world points: its ends on the outline, the
    others inside) makes across a face of the element measured by `frame` (its display vertices
    `verts`), or None. The face is the element's own rectangle there (a wall's mitred ends left out).
    Drawn by hand: a segment less than 5° off level / upright is made so (from its first point),
    and an end up to 2 cm from the outline is put on it."""
    inv = np.linalg.inv(frame.matrix)
    pl = [(inv @ np.append(p, 1.0))[:3] for p in path]
    local = (inv @ np.column_stack((verts, np.ones(len(verts)))).T).T[:, :3]
    box_lo = np.array((frame.x0, frame.y0, frame.z0))
    box_hi = np.array((frame.x0 + frame.length, frame.y1, frame.z1))
    for axis in range(3):
        for side, c in ((-1, float(local[:, axis].min())), (1, float(local[:, axis].max()))):
            if any(abs(p[axis] - c) > TOL for p in pl):
                continue
            i, j = [k for k in range(3) if k != axis]
            on = local[np.abs(local[:, axis] - c) < TOL][:, [i, j]]
            o_lo, o_hi = on.min(axis=0), on.max(axis=0)                 # the face's outline as drawn
            r_lo = np.maximum(box_lo[[i, j]], o_lo)                       # the rectangle the parts are made on
            r_hi = np.minimum(box_hi[[i, j]], o_hi)
            pts = [np.array((p[i], p[j])) for p in pl]
            for k in range(1, len(pts)):
                d = pts[k] - pts[k - 1]
                if abs(d[1]) <= max(LEVEL_TOL, LEVEL_SLOPE * abs(d[0])):
                    pts[k][1] = pts[k - 1][1]
                elif abs(d[0]) <= max(LEVEL_TOL, LEVEL_SLOPE * abs(d[1])):
                    pts[k][0] = pts[k - 1][0]
            ends_ok = True
            for k in (0, len(pts) - 1):
                q = pts[k]
                if not np.any((np.abs(q - o_lo) <= EDGE_TOL) | (np.abs(q - o_hi) <= EDGE_TOL)):
                    ends_ok = False
                    break
                q = np.clip(q, r_lo, r_hi)
                s = int(np.argmin((q[0] - r_lo[0], r_hi[0] - q[0], q[1] - r_lo[1], r_hi[1] - q[1])))
                q[s // 2] = (r_lo, r_hi)[s % 2][s // 2]                     # onto the nearest side
                pts[k] = q
            if not ends_ok:
                continue

            def to3(q):
                p = np.zeros(3)
                p[axis], p[i], p[j] = c, q[0], q[1]
                return p
            mesh = PolyMesh([to3(q) for q in ((r_lo[0], r_lo[1]), (r_hi[0], r_lo[1]), (r_hi[0], r_hi[1]),
                                              (r_lo[0], r_hi[1]))], [[0, 1, 2, 3]])
            if mesh.face_normal(0)[axis] * side < 0:
                mesh.flip_face(0)                                       # (facing out of the element)
            if split_face(mesh, 0, [to3(q) for q in pts], 1e-6) is None:
                continue
            return [_part(frame, axis, side, [mesh.verts[v] for v in f]) for f in mesh.faces]
    return None


def _part(frame, axis, side, ring):
    """A sketch face lying on the element's face (axis, side): `ring` (points of its frame), facing out."""
    m = frame.matrix
    i, j = [k for k in range(3) if k != axis]
    unit = [m[:3, k] / np.linalg.norm(m[:3, k]) for k in range(3)]
    u, v = unit[i], unit[j]
    if float(np.cross(u, v) @ (unit[axis] * side)) < 0:
        u, v = v, u
    world = [frame.to_world(p) for p in ring]
    origin = world[0]
    mesh = PolyMesh([((p - origin) @ u, (p - origin) @ v, 0.0) for p in world], [list(range(len(world)))])
    if mesh.face_normal(0)[2] < 0:
        mesh.flip_face(0)
    return rectangle_matrix(origin, u, v), mesh
