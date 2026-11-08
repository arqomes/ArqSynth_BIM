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


def moved_lines(doc, moves, also=()):
    """The loose lines' meshes after moving the ends at the points `moves` [(before, after)] â€”
    {obj_id: (object, new mesh)} â€” and the segments touched, in world coordinates, for a preview.
    (0.459) also: sketches with faces — a polygon whose side is picked — whose corners there move too."""
    out, touched = {}, []
    for obj in doc.objects.values():
        if not (is_lines(obj) or (obj.id in also and not obj.is_bim)):
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
        sides = list(mesh.lines) + [(f[k], f[(k + 1) % len(f)]) for f in mesh.faces for k in range(len(f))]
        for i, j in sides:
            if i in moved or j in moved:
                touched.append((transform_point(obj.matrix, mesh.verts[i]), transform_point(obj.matrix, mesh.verts[j])))
    return out, touched


def move_points(doc, moves, label=None, also=()):
    """Move the loose lines' ends lying at `moves`' points [(before, after)]: the lines joined there
    follow. One undo step. Returns how many lines changed; LineRefused("too_short") if a segment
    would vanish. (0.459) also: as moved_lines'."""
    found, touched = moved_lines(doc, moves, also)
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
    them — (0.455, the owner: «o arco não é um arco, mas um monte de segmentos, não dá pra selecionar o raio inteiro
    para ajustar o raio como no revit») an arc of its own, as the Arc tool's: picked whole, its radius in its
    Properties and its temporary dimension (fillet_radius keeps it tangent to the two). One undo step.
    LineRefused("parallel") / ("too_big"). Returns (the fillet, the arc's id)."""
    from ..core import curves
    from ..core.fillet import fillet
    from ..core.mesh import PolyMesh
    from .document import AddObject, JoinedCommand, SketchObject
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

    trim(oa_id, ia, ja, f.ends[0], f.tangents[0])
    trim(ob_id, ib, jb, f.ends[1], f.tangents[1])
    curve = curves.arc_curve((float(f.centre[0]), float(f.centre[1]), z), (0.0, 0.0, 1.0),
                             (float(f.tangents[0][0]), float(f.tangents[0][1]), z), math.degrees(f.sweep))
    pts = curves.curve_points(curve)
    arc = SketchObject(t("obj.arc", n=doc.next_number()), np.eye(4),
                       PolyMesh(pts, lines=[(k, k + 1) for k in range(len(pts) - 1)]), curve=curve)
    doc.execute(JoinedCommand([ReplaceMeshes([(k, objs[k].mesh, m) for k, m in meshes.items()], label or ""),
                               AddObject(arc, label or "")], label or ""))
    return f, arc.id


def face_edge_at(obj, point, tol=1e-3):
    """(0.455) The side (i, j) of a flat sketch face's outline nearest the world `point` (within `tol`) with its ends
    (a, b) world — ((i, j), (a, b)) — or None."""
    if obj is None or obj.is_bim or not obj.mesh.faces:
        return None
    world = [transform_point(obj.matrix, v) for v in obj.mesh.verts]
    point = np.asarray(point, dtype=float)
    best = None
    for face in obj.mesh.faces:
        for k, i in enumerate(face):
            j = face[(k + 1) % len(face)]
            a, b = world[i], world[j]
            d = b - a
            s = float(np.clip((point - a) @ d / max(float(d @ d), 1e-12), 0.0, 1.0))
            gap = float(np.linalg.norm(a + d * s - point))
            if best is None or gap < best[0]:
                best = (gap, (i, j), (a, b))
    if best is None or best[0] > tol:
        return None
    return best[1], best[2]


def fillet_face(doc, first, keep_first, second, keep_second, radius, label=None):
    """(0.455, the owner: «tentei fazer isso no polígono, mas não funcionou») Revit's «Fillet Arc» on a polygon — a
    sketch's flat, level face (an outline closed with the Line tool, a rectangle): the corner between two of its sides
    — first = (obj_id, i, j), second likewise, sharing that corner — rounded by an arc of `radius` tangent to both,
    the face kept whole. One undo step. LineRefused("not_corner" | "not_level" | "parallel" | "too_big")."""
    from ..core.fillet import arc_points, fillet
    from .document import ReplaceMesh
    (obj_id, ia, ja), (other, ib, jb) = first, second
    obj = doc.get(obj_id)
    shared = {ia, ja} & {ib, jb}
    if other != obj_id or obj is None or len(shared) != 1 or {ia, ja} == {ib, jb}:
        raise LineRefused("not_corner")
    c = shared.pop()
    far_a, far_b = (ja if ia == c else ia), (jb if ib == c else ib)
    world = [transform_point(obj.matrix, v) for v in obj.mesh.verts]
    if max(abs(float(w[2]) - float(world[c][2])) for w in world) > 1e-6:
        raise LineRefused("not_level")                     # (the fillet is drawn in the plan)
    faces = [k for k, face in enumerate(obj.mesh.faces) if c in face]
    if len(faces) != 1 or any(c in line for line in obj.mesh.lines):
        raise LineRefused("not_corner")                    # (a corner shared with another face, or a line)
    face = obj.mesh.faces[faces[0]]
    n = face.index(c)
    if {face[n - 1], face[(n + 1) % len(face)]} != {far_a, far_b}:
        raise LineRefused("not_corner")
    f = fillet((world[far_a], world[c]), keep_first, (world[far_b], world[c]), keep_second, radius=radius)
    if f is None:
        raise LineRefused("parallel")
    reach = float(np.linalg.norm(f.tangents[0] - f.cross))
    if any(reach > room - TOL for room in f.room):
        raise LineRefused("too_big")
    z = float(world[c][2])
    inv = np.linalg.inv(obj.matrix)
    pts = [transform_point(inv, (float(x), float(y), z)) for x, y in arc_points(f)]   # (from a's side to b's)
    if face[n - 1] != far_a:                                  # (the face goes round from b's side)
        pts = pts[::-1]
    mesh = obj.mesh.copy()
    mesh.verts[c] = np.asarray(pts[0], dtype=float)           # (the corner becomes the arc's first point…)
    added = [mesh.add_vert(p) for p in pts[1:]]               # (…and the others follow it, in the face's order)
    mesh.faces[faces[0]] = face[:n] + [c] + added + face[n + 1:]
    doc.execute(ReplaceMesh(obj.id, obj.mesh, mesh, label or ""))
    return f


def _world_curve(obj):
    """(0.455) An arc sketch's data in world coordinates: (centre, normal, start, angle in degrees)."""
    c = obj.curve
    m = np.asarray(obj.matrix, dtype=float)
    normal = m[:3, :3] @ np.asarray(c["normal"], dtype=float)
    normal = normal / max(float(np.linalg.norm(normal)), 1e-12)
    return (transform_point(m, np.asarray(c["centre"], float)), normal, transform_point(m, np.asarray(c["start"], float)),
            float(c["angle"]))


def tangent_lines(doc, arc_id):
    """(0.455) The straight loose lines leaving an arc's two ends along it — as a fillet's — [(obj_id, i, j, the far
    end (world)) at its start, the same at its end], or None when it is not so at both."""
    from ..core import curves
    obj = doc.get(arc_id)
    if obj is None or not obj.curve or obj.curve.get("kind") != "arc" or curves.is_closed(obj.curve) or \
            obj.curve.get("pie"):
        return None
    centre, normal, start, angle = _world_curve(obj)
    turn = 1.0 if angle >= 0 else -1.0
    end = centre + curves._rotate(start - centre, normal, math.radians(angle))
    way = lambda p: np.cross(normal, p - centre) * turn                     # noqa: E731  (along the arc there)
    out = []
    for point, away in ((start, -way(start)), (end, way(end))):
        away = away / max(float(np.linalg.norm(away)), 1e-12)
        found = None
        for o in doc.objects.values():
            if o.id == arc_id or not is_lines(o) or o.curve:
                continue
            for i, j, a, b in segments(o):
                for near, far, ii, jj in ((a, b, i, j), (b, a, j, i)):
                    d = far - near
                    n = float(np.linalg.norm(d))
                    if np.linalg.norm(near - point) <= 1e-4 and n > MIN_LENGTH and float(d @ away) / n > 0.9999:
                        found = (o.id, ii, jj, far)
                        break
                if found:
                    break
            if found:
                break
        if found is None:
            return None
        out.append(found)
    return out


def fillet_radius(doc, arc_id, radius, label=None):
    """(0.455) A fillet arc's radius changed as Revit's: still tangent to the two lines it joins — they are trimmed or
    stretched to where the new arc touches them (curve_edit.reshape: the lines at its ends follow). False when the
    arc is not a fillet's (no straight line along each end); LineRefused("too_big") when the lines are too short."""
    from ..core import curves
    from ..core.fillet import fillet
    from . import curve_edit
    lines = tangent_lines(doc, arc_id)
    if lines is None:
        return False
    obj = doc.get(arc_id)
    centre, normal, start, angle = _world_curve(obj)
    end = centre + curves._rotate(start - centre, normal, math.radians(angle))
    (_oa, _ia, _ja, far_a), (_ob, _ib, _jb, far_b) = lines
    f = fillet((far_a, start), far_a, (far_b, end), far_b, radius=float(radius))
    if f is None:
        raise LineRefused("parallel")
    reach = float(np.linalg.norm(f.tangents[0] - f.cross))      # (the same on both: the arc is symmetric)
    if any(reach >= float(np.linalg.norm(np.asarray(far, dtype=float)[:2] - f.cross)) - MIN_LENGTH
           for far in (far_a, far_b)):
        raise LineRefused("too_big")
    z = float(start[2])
    inv = np.linalg.inv(np.asarray(obj.matrix, dtype=float))
    sweep = math.degrees(f.sweep) * (1.0 if float(normal[2]) >= 0 else -1.0)
    curve = curves.arc_curve(transform_point(inv, (float(f.centre[0]), float(f.centre[1]), z)),
                             np.asarray(obj.curve["normal"], dtype=float),
                             transform_point(inv, (float(f.tangents[0][0]), float(f.tangents[0][1]), z)), sweep)
    curve_edit.reshape(doc, arc_id, curve, label or t("cmd.fillet_radius"))
    return True


# ---------------------------------------------------------------- (0.459) a polygon's sides and arcs, as Revit's sketch

def face_loop(obj, face_k):
    """A polygon's (a flat sketch face's) outline: (its corners' indices, their points in the sketch's own frame) —
    None when the face is not flat in its frame (a volume's)."""
    if obj is None or obj.is_bim or not 0 <= face_k < len(obj.mesh.faces):
        return None
    face = [int(i) for i in obj.mesh.faces[face_k]]
    pts = [np.asarray(obj.mesh.verts[i], dtype=float) for i in face]
    if len(pts) < 3 or max(abs(float(p[2] - pts[0][2])) for p in pts) > 1e-6:
        return None
    return face, pts


def face_run(obj, face_k, k):
    """(0.459, the owner: «não consigo selecionar linhas e arcos no polígono para ajustar») The side k of a polygon
    (from its corner k to the next) as Revit's sketch picks it: an arc drawn in pieces — a fillet's, a circle's —
    whole: (its corners' indices, the arc_runs.Run in the sketch's frame), else the side alone: (its two corners,
    None)."""
    from ..core import arc_runs
    loop = face_loop(obj, face_k)
    if loop is None:
        face = list(obj.mesh.faces[face_k])
        return [face[k], face[(k + 1) % len(face)]], None
    face, pts = loop
    run = arc_runs.run_around(pts, k, closed=True)
    if run is None:
        return [face[k], face[(k + 1) % len(face)]], None
    return [face[i] for i in run.indices], run


def set_face_side(doc, obj_id, i, j, length):
    """(0.459) A polygon's side i → j `length` long: its corner j moves along it (the side after it follows, and the
    loose lines there)."""
    obj = doc.get(obj_id)
    a, b = transform_point(obj.matrix, obj.mesh.verts[i]), transform_point(obj.matrix, obj.mesh.verts[j])
    d = b - a
    if length < MIN_LENGTH or np.linalg.norm(d) < MIN_LENGTH:
        raise LineRefused("too_short")
    return move_points(doc, [(b, a + d / np.linalg.norm(d) * length)], t("cmd.line_length"), also={obj_id})


def face_arc_radius(doc, obj_id, face_k, run, radius, label=None):
    """(0.459) A polygon's arc drawn in pieces — its corners `run` (indices, in the face's order) — given `radius`
    (world), as Revit's sketch arc: a fillet's — the sides before and after it straight along its ends — made again
    between them (they are trimmed or stretched); another about its centre (a circle: the whole). One undo step.
    LineRefused("parallel" | "too_big" | "not_corner")."""
    from ..core import arc_runs
    from ..core.fillet import arc_points, fillet
    from ..core.outline_shapes import crossing
    from .document import ReplaceMesh
    obj = doc.get(obj_id)
    loop = face_loop(obj, face_k)
    if loop is None or any(v not in loop[0] for v in run) or len(run) < 3:
        raise LineRefused("not_corner")
    face, pts = loop
    n = len(face)
    pos = [face.index(v) for v in run]
    z = float(pts[0][2])
    flat = [p[:2] for p in pts]
    run_pts = [flat[p] for p in pos]
    centre = arc_runs.centre_of(run_pts[0], run_pts[len(run_pts) // 2], run_pts[-1])
    if centre is None:
        raise LineRefused("not_corner")
    old = float(np.linalg.norm(run_pts[0] - centre))
    r = float(radius) / max(float(np.linalg.norm(obj.matrix[:3, 0])), 1e-12)
    if r < MIN_LENGTH:
        raise LineRefused("too_short")
    mesh = obj.mesh.copy()
    if len(run) >= n:                                          # a circle: the whole of it
        for v, p in zip(run, run_pts):
            mesh.verts[v] = np.array((*(centre + (p - centre) * r / old), z))
        doc.execute(ReplaceMesh(obj.id, obj.mesh, mesh, label or t("cmd.fillet_radius")))
        return
    prev, nxt = flat[(pos[0] - 1) % n], flat[(pos[-1] + 1) % n]
    t0, t1 = run_pts[0], run_pts[-1]
    along = lambda far, p: abs(float((p - far) @ (p - centre))) <= 1e-2 * float(np.linalg.norm(p - far)) * old  # noqa
    if along(prev, t0) and along(nxt, t1):                     # a fillet: made again between its two sides
        corner = crossing(prev, t0 - prev, nxt, t1 - nxt)
        f = fillet((prev, corner), prev, (nxt, corner), nxt, radius=r) if corner is not None else None
        if f is None:
            raise LineRefused("parallel")
        reach = float(np.linalg.norm(f.tangents[0] - f.cross))
        if any(reach > room - MIN_LENGTH for room in f.room):
            raise LineRefused("too_big")
        new = [np.asarray(p, dtype=float) for p in arc_points(f)]
    else:                                                      # an arc alone: about its centre
        new = [centre + (p - centre) * r / old for p in run_pts]
    order = face[pos[0]:] + face[:pos[0]]                      # (the face from the arc's first corner on)
    rest = order[len(run):]
    ids = list(run[:len(new)]) + [mesh.add_vert((0.0, 0.0, z)) for _ in range(len(new) - len(run))]
    for v, p in zip(ids, new):
        mesh.verts[v] = np.array((float(p[0]), float(p[1]), z))
    mesh.faces[face_k] = ids + rest
    doc.execute(ReplaceMesh(obj.id, obj.mesh, mesh, label or t("cmd.fillet_radius")))


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
