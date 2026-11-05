"""Sketch-mode geometry: rectangles and SketchUp-style Push/Pull.

Pure numpy, no UI. All distances given to these functions are WORLD distances
(meters), even when the object is rotated or scaled; conversion to object
space happens here.
"""

from dataclasses import dataclass

import numpy as np

from .mesh import SMOOTH_DEG, PolyMesh, edge_key, polygon_normal

MIN_THICKNESS = 0.001  # 1 mm: Push/Pull never collapses a solid below this
_PERP_TOL = 1e-4

X, Y, Z = np.eye(3)


def normalize(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def transform_point(matrix, p):
    return (matrix @ np.append(p, 1.0))[:3]


def transform_dir(matrix, d):
    return matrix[:3, :3] @ d


# ---------------------------------------------------------------- rectangle

def plane_axes(normal):
    """In-plane axes (U, V) for a drawing plane, with U x V == normal.

    Horizontal planes use world X as U (red axis). Other planes use a
    horizontal U, so rectangles on walls come out level.
    """
    n = normalize(normal)
    if abs(n[2]) > 0.999:
        u = normalize(X - X.dot(n) * n)
    else:
        u = normalize(np.cross(Z, n))
    v = normalize(np.cross(n, u))
    return u, v


def rectangle_matrix(origin, u, v):
    """Object matrix whose local XY is the drawing plane and local Z its normal."""
    u, v = normalize(u), normalize(v)
    n = normalize(np.cross(u, v))
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = u, v, n, origin
    return m


CIRCLE_SIDES = 24           # (0.150) a circle's sides, as SketchUp's


def circle_mesh(radius, sides=CIRCLE_SIDES):
    """(0.150) A circle (a regular polygon of `sides`) of this radius centred on the local origin: a single face,
    its normal local +Z, its first corner on local +X."""
    corners = [(radius * np.cos(2 * np.pi * k / sides), radius * np.sin(2 * np.pi * k / sides), 0.0)
               for k in range(sides)]
    return PolyMesh(corners, [list(range(sides))])


def polygon_mesh(points):
    """(0.150) A flat polygon (local (x, y) points, counter-clockwise or not): a single face, its normal local +Z."""
    pts = [(float(x), float(y), 0.0) for x, y in points]
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts.reverse()
    return PolyMesh(pts, [list(range(len(pts)))])


def rectangle_mesh(du, dv):
    """Single face in object space, ordered so its normal is local +Z."""
    corners = [(0.0, 0.0, 0.0), (du, 0.0, 0.0), (du, dv, 0.0), (0.0, dv, 0.0)]
    if du * dv < 0.0:
        corners.reverse()
    return PolyMesh(corners, [[0, 1, 2, 3]])


# ---------------------------------------------------------------- push/pull

@dataclass
class PushPullResult:
    mode: str          # "prism" | "stretch" | "extrude" | "none"
    distance: float    # world distance actually applied
    clamped: bool = False
    faces: tuple = ()  # (push_pull_faces, 0.311) the faces where the faces pushed now are


def face_world_normal(matrix, mesh, fi):
    n = np.linalg.inv(matrix[:3, :3]).T @ mesh.face_normal(fi)
    return normalize(n)


def face_world_points(matrix, mesh, fi):
    return [transform_point(matrix, mesh.verts[i]) for i in mesh.faces[fi]]


def _is_isolated(mesh, fi):
    edges = mesh.edge_faces()
    f = mesh.faces[fi]
    return all(len(edges[(min(a, b), max(a, b))]) == 1
               for a, b in zip(f, f[1:] + f[:1]))


def _stretch_limits(mesh, fi, neighbours, matrix, normal_w, min_thickness):
    """World distance range the face can move without inverting its neighbours."""
    face_verts = set(mesh.faces[fi])
    p0 = transform_point(matrix, mesh.verts[mesh.faces[fi][0]])
    below, above = [], []
    for g in neighbours:
        for q in mesh.faces[g]:
            if q in face_verts:
                continue
            h = (transform_point(matrix, mesh.verts[q]) - p0).dot(normal_w)
            if h < -1e-6:
                below.append(h)
            elif h > 1e-6:
                above.append(h)
    lower = (max(below) + min_thickness) if below else None
    upper = (min(above) - min_thickness) if above else None
    return lower, upper


def _add_sides(mesh, ring, top_ring):
    sides = []
    n = len(ring)
    for i in range(n):
        j = (i + 1) % n
        sides.append(mesh.add_face((ring[i], ring[j], top_ring[j], top_ring[i])))
    return sides


def _soften_sides(mesh, ring, top_ring, sides):
    """(0.150) The side faces of a pushed curve (a circle's, an arc's strips) meet at small angles: the edges between
    them are hidden, as SketchUp softens them — a cylinder, not 24 boards. A box's corners stay."""
    limit = np.cos(np.radians(SMOOTH_DEG))
    n = len(sides)
    for i in range(n):
        a, b = mesh.face_normal(sides[i - 1]), mesh.face_normal(sides[i])
        if float(np.dot(a, b)) > limit:
            mesh.hidden.add(edge_key(ring[i], top_ring[i]))


def push_pull(mesh, fi, matrix, distance, min_thickness=MIN_THICKNESS, keep_start=False):
    """Push/Pull face `fi` of `mesh` (in place) by `distance` along its world normal.

    - Isolated face (a flat rectangle): becomes a closed prism; the original
      face stays as the base.
    - Face of a solid whose neighbours are perpendicular to the motion (box
      sides): the face just moves and the neighbours stretch, as in SketchUp.
      The motion is clamped so the solid never inverts.
    - Other faces: extruded with new side faces; the face moves away from where it was (0.310, as SketchUp: the
      middle of an offset rectangle pushed down is a tray open on top, pulled up a box with no bottom).
    - keep_start (SketchUp's Ctrl, «criar sólido», 0.310): a new face is left where it started — what comes out of
      it is a closed solid whichever way it goes (a box on a box's face, the tray closed on top).
    """
    if abs(distance) < 1e-9:
        return PushPullResult("none", 0.0)

    matrix = np.asarray(matrix, dtype=float)
    normal_w = face_world_normal(matrix, mesh, fi)
    to_local = np.linalg.inv(matrix[:3, :3])

    def local_offset(d):
        return to_local @ (normal_w * d)

    ring = list(mesh.faces[fi])

    if _is_isolated(mesh, fi):
        offset = local_offset(distance)
        top_ring = [mesh.add_vert(mesh.verts[i] + offset) for i in ring]
        sides = _add_sides(mesh, ring, top_ring)
        top = mesh.add_face(top_ring, mesh.paint_of(fi))     # (0.392: the top painted as the face)
        if distance > 0.0:
            mesh.flip_face(fi)  # original face becomes the base
        else:
            for f in sides + [top]:
                mesh.flip_face(f)
        _soften_sides(mesh, ring, top_ring, sides)
        return PushPullResult("prism", distance)

    neighbours = [g for g in mesh.faces_using_verts(ring) if g != fi]
    direction = normalize(local_offset(1.0))
    closed = mesh.is_closed()
    if not keep_start and all(abs(mesh.face_normal(g).dot(direction)) < _PERP_TOL for g in neighbours):
        lower, upper = _stretch_limits(mesh, fi, neighbours, matrix, normal_w, min_thickness)
        d = distance
        if lower is not None and d < lower:
            d = lower
        if upper is not None and d > upper:
            d = upper
        if (lower is not None and upper is not None and lower > upper) or abs(d) < 1e-9:
            return PushPullResult("none", 0.0, clamped=True)
        offset = local_offset(d)
        for i in ring:
            mesh.verts[i] = mesh.verts[i] + offset
        return PushPullResult("stretch", d, clamped=(d != distance))

    if closed and not keep_start:
        result = _push_part(mesh, fi, direction, normal_w, matrix, distance, local_offset, min_thickness)
        if result is not None:
            return result

    # Pushing into a solid: stop at the face behind, and if the face reaches it,
    # cut a hole right through (SketchUp behaviour, used to open voids in walls).
    clamped = False
    if distance < 0 and closed:
        back, depth, fits = _face_behind(mesh, fi, matrix, normal_w)
        if not keep_start and back is not None and fits and -distance >= depth - 1e-9:
            if _punch_hole(mesh, fi, back, local_offset(-depth)):
                return PushPullResult("hole", -depth, clamped=-distance > depth + 1e-9)
        if back is not None and -distance > depth - min_thickness:
            distance, clamped = -(depth - min_thickness), True
            if distance >= 0:
                return PushPullResult("none", 0.0, clamped=True)

    # Extrude with new side faces. The original face goes (a bump, a recess, a tray), unless a new starting face
    # is asked for (Ctrl): then it stays as the base, as for a prism, and what came out is closed.
    offset = local_offset(distance)
    top_ring = [mesh.add_vert(mesh.verts[i] + offset) for i in ring]
    sides = _add_sides(mesh, ring, top_ring)
    top = mesh.add_face(top_ring, mesh.paint_of(fi))         # (0.392: the face moved keeps its paint)
    if not keep_start:
        mesh.remove_face(fi)
    elif distance > 0.0:
        mesh.flip_face(fi)
    else:
        for f in sides + [top]:
            mesh.flip_face(f)
    _soften_sides(mesh, ring, top_ring, sides)
    return PushPullResult("extrude", distance, clamped=clamped)


def _push_part(mesh, fi, direction, normal_w, matrix, distance, local_offset, min_thickness):
    """Push/Pull a part of a divided face of a solid (the Line tool divided it): along the edges
    where the solid's side is across the motion (a box's side under half its top) that side
    stretches with it, as in SketchUp; along the others (the line that divided the face, where
    the other part stays) a new side face is made. A corner shared with what does not move is
    doubled. Returns None when it is not such a case (every edge one way or the other)."""
    ring = list(mesh.faces[fi])
    edges = mesh.edge_faces()

    def across(g):
        return abs(float(mesh.face_normal(g) @ direction)) < _PERP_TOL

    k = len(ring)
    others = [[g for g in edges.get(edge_key(ring[i], ring[(i + 1) % k]), []) if g != fi] for i in range(k)]
    slide = [bool(o) and all(across(g) for g in o) for o in others]
    if all(slide) or not any(slide):
        return None
    sliding = sorted({g for o, s in zip(others, slide) if s for g in o})
    lower, upper = _stretch_limits(mesh, fi, sliding, matrix, normal_w, min_thickness)
    d = distance
    if lower is not None and d < lower:
        d = lower
    if upper is not None and d > upper:
        d = upper
    if (lower is not None and upper is not None and lower > upper) or abs(d) < 1e-9:
        return PushPullResult("none", 0.0, clamped=True)
    offset = local_offset(d)
    users = {v: [g for g, f in enumerate(mesh.faces) if g != fi and v in f] for v in ring}
    stays = {v for v in ring if not all(across(g) for g in users[v])}     # also used by what does not move
    moved = {v: (mesh.add_vert(mesh.verts[v] + offset) if v in stays else v) for v in ring}
    sides = []
    for i in range(k):
        a, b = ring[i], ring[(i + 1) % k]
        if not slide[i]:
            sides.append((a, b, moved[b], moved[a]))
            continue
        for g in others[i]:                     # the side runs b -> a: it now goes round the moved edge
            f = mesh.faces[g]
            j = next(j for j in range(len(f)) if f[j] == b and f[(j + 1) % len(f)] == a)
            for x in reversed([moved[x] for x in (b, a) if moved[x] != x]):
                f.insert(j + 1, x)
    for v in ring:
        if v not in stays:
            mesh.verts[v] = mesh.verts[v] + offset
    mesh.faces[fi] = [moved[v] for v in ring]
    for quad in sides:
        mesh.add_face(quad)
    return PushPullResult("stretch", d, clamped=(d != distance))


def _face_behind(mesh, fi, matrix, normal_w):
    """The nearest face behind `fi` facing the other way (the back of a wall).

    Returns (face index, world distance, fits) where `fits` says whether `fi`
    seen straight through lands strictly inside that face (a hole is possible).
    (None, None, False) if there is no such face.
    """
    pts_w = face_world_points(matrix, mesh, fi)
    best = None
    for g in range(len(mesh.faces)):
        if g == fi or face_world_normal(matrix, mesh, g).dot(normal_w) > -1 + 1e-6:
            continue
        g_pts = face_world_points(matrix, mesh, g)
        depth = float((pts_w[0] - g_pts[0]).dot(normal_w))
        if depth <= 1e-9:
            continue
        projected = [p - normal_w * depth for p in pts_w]
        fits = len(g_pts) == 4 and _is_convex(g_pts, -normal_w) and \
            all(_strictly_inside(g_pts, -normal_w, p) for p in projected)
        key = (depth, not fits)
        if best is None or key < best[0]:
            best = (key, g, depth, fits)
    if best is None:
        return None, None, False
    return best[1], best[2], best[3]


def _punch_hole(mesh, fi, back, through):
    """Cut a hole from face `fi` through to face `back` (object-space vector
    `through`): mark the same rectangle on the back face, join both with tunnel
    faces and remove them. Returns False (mesh untouched) if not possible."""
    ring = list(mesh.faces[fi])
    front_pts = [mesh.verts[i].copy() for i in ring]
    projected = [p + through for p in front_pts]
    trial = mesh.copy()
    if imprint_polygon(trial, back, projected) is None:
        return False
    back_ring = trial.faces[back]
    match = []
    for p in projected:
        j = min(back_ring, key=lambda k: np.linalg.norm(trial.verts[k] - p))
        match.append(j)
    n = len(ring)
    for i in range(n):
        k = (i + 1) % n
        trial.add_face((ring[i], ring[k], match[k], match[i]))
    for f in sorted((fi, back), reverse=True):
        trial.remove_face(f)
    trial.voids.append((front_pts, np.array(through, dtype=float)))
    mesh.verts, mesh.faces, mesh.hidden, mesh.voids = trial.verts, trial.faces, trial.hidden, trial.voids
    mesh.paint = trial.painted()                                # (0.392)
    return True


# ---------------------------------------------------------------- several faces at once (0.311)

@dataclass
class _Piece:
    """What push_pull_faces does to a piece of faces that touch, worked out before anything moves."""
    faces: list
    unit: dict           # point -> its world motion for a Push/Pull of 1
    boundary: list       # (a, b, faces beside it) round the piece, a -> b as its face runs
    slide: list          # per boundary edge: the faces beside it stretch with it (a box's side under its top)
    stays: set           # points left where they are (a new one goes with the piece)
    soft: set            # hidden edges inside the piece (an offset's frame): hidden where it ends up too
    isolated: bool       # nothing beside it: it keeps its base, as a lone face does
    lower: float = -np.inf
    upper: float = np.inf


def _pieces(mesh, faces, edges):
    """The faces given, in pieces of faces that touch along an edge."""
    faces = set(faces)
    beside = {g: set() for g in faces}
    for fis in edges.values():
        mine = [g for g in fis if g in faces]
        for g in mine:
            beside[g].update(h for h in mine if h != g)
    pieces, left = [], set(faces)
    while left:
        seen = {min(left)}
        todo = list(seen)
        while todo:
            for h in beside[todo.pop()]:
                if h not in seen:
                    seen.add(h)
                    todo.append(h)
        left -= seen
        pieces.append(sorted(seen))
    return pieces


def _joint_motion(mesh, piece, matrix):
    """World motion of each point of a piece for a Push/Pull of 1: every face 1 out along its own normal, and where
    faces of it meet at an angle the point goes so that each of them is (no gap at the fold, a thicker shell)."""
    normals = {g: face_world_normal(matrix, mesh, g) for g in piece}
    around = {}
    for g in piece:
        for v in mesh.faces[g]:
            ns = around.setdefault(v, [])
            if all(float(normals[g] @ m) < 1 - 1e-9 for m in ns):
                ns.append(normals[g])
    return {v: ns[0] if len(ns) == 1 else np.linalg.lstsq(np.array(ns), np.ones(len(ns)), rcond=None)[0]
            for v, ns in around.items()}


def _piece_plan(mesh, piece, matrix, edges, closed, keep, shared, min_thickness):
    inside = set(piece)
    unit = _joint_motion(mesh, piece, matrix)
    boundary, soft = [], set()
    for g in piece:
        f = mesh.faces[g]
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            fis = edges[edge_key(a, b)]
            if sum(1 for h in fis if h in inside) > 1:
                if edge_key(a, b) in mesh.hidden:
                    soft.add(edge_key(a, b))
            else:
                boundary.append((a, b, [h for h in fis if h not in inside]))
    isolated = all(not others for _a, _b, others in boundary)
    users = {v: [] for v in unit}
    for h, f in enumerate(mesh.faces):
        if h not in inside:
            for v in set(f).intersection(users):
                users[v].append(h)
    normal = {h: face_world_normal(matrix, mesh, h) for hs in users.values() for h in hs}

    def follows(h, v):          # face h can stretch as point v moves (the motion lies in it)
        return abs(float(normal[h] @ unit[v])) < _PERP_TOL * float(np.linalg.norm(unit[v]))

    slide = [False] * len(boundary)
    if not keep and not isolated:
        slide = [bool(others) and all(follows(h, a) and follows(h, b) for h in others) for a, b, others in boundary]
        if not closed and not (all(slide) and all(follows(h, v) for v in unit for h in users[v])):
            slide = [False] * len(boundary)            # (an open sketch: new sides, as push_pull's)
    fixed = {v for (a, b, _o), s in zip(boundary, slide) if not s for v in (a, b)}
    stays = {v for v in unit if v in fixed or v in shared or not all(follows(h, v) for h in users[v])}
    plan = _Piece(list(piece), unit, boundary, slide, stays, soft, isolated)
    if any(slide):
        # the faces that stretch never turn inside out (push_pull's _stretch_limits, point by point)
        world = {}

        def at(i):
            if i not in world:
                world[i] = transform_point(matrix, mesh.verts[i])
            return world[i]
        for (a, b, others), s in zip(boundary, slide):
            for h in others if s else ():
                for v in (a, b):
                    u = unit[v]
                    for q in mesh.faces[h]:
                        if q in unit:
                            continue
                        level = float((at(q) - at(v)) @ u) / float(u @ u)
                        if level < -1e-6:
                            plan.lower = max(plan.lower, level + min_thickness)
                        elif level > 1e-6:
                            plan.upper = min(plan.upper, level - min_thickness)
    elif closed:
        # pushed into a solid: it stops short of the face behind (no hole through, as one face's can)
        for g in piece:
            _back, depth, _fits = _face_behind(mesh, g, matrix, face_world_normal(matrix, mesh, g))
            if depth is not None:
                plan.lower = max(plan.lower, -(depth - min_thickness))
    return plan


def _insert_round(face, a, b, new):
    """Face beside the edge a -> b of a piece that moved: it goes round the edge's new points `new` (a's, b's)."""
    k = len(face)
    for j in range(k):
        if face[j] == b and face[(j + 1) % k] == a:
            face[j + 1:j + 1] = [x for x in reversed(new) if x is not None]
            return
        if face[j] == a and face[(j + 1) % k] == b:     # (a sketch's face turned the other way)
            face[j + 1:j + 1] = [x for x in new if x is not None]
            return


def _soften_round(mesh, sides, moved):
    """push_pull's _soften_sides for the sides round a piece: [(a, b, side face)]."""
    limit = np.cos(np.radians(SMOOTH_DEG))
    ending = {b: fi for _a, b, fi in sides}
    for a, _b, fi in sides:
        if a in ending and float(np.dot(mesh.face_normal(ending[a]), mesh.face_normal(fi))) > limit:
            mesh.hidden.add(edge_key(a, moved[a]))


def _apply_piece(mesh, plan, d, keep, matrix):
    to_local = np.linalg.inv(matrix[:3, :3])
    offset = {v: to_local @ (u * d) for v, u in plan.unit.items()}
    if keep or plan.isolated:
        # a new face left where it started (Ctrl, or nothing beside it): a closed solid comes out
        top = {v: mesh.add_vert(mesh.verts[v] + offset[v]) for v in sorted(offset)}
        sides = [(a, b, mesh.add_face((a, b, top[b], top[a]))) for a, b, _o in plan.boundary]
        tops = [mesh.add_face([top[v] for v in mesh.faces[g]], mesh.paint_of(g)) for g in plan.faces]
        for g in (plan.faces if d > 0 else [fi for _a, _b, fi in sides] + tops):
            mesh.flip_face(g)
        mesh.hidden |= {edge_key(top[a], top[b]) for a, b in plan.soft}
        _soften_round(mesh, sides, top)
        return ("prism" if plan.isolated else "extrude"), tops
    moved = {v: (mesh.add_vert(mesh.verts[v] + offset[v]) if v in plan.stays else v) for v in sorted(offset)}
    quads = []
    for (a, b, others), s in zip(plan.boundary, plan.slide):
        if not s:
            quads.append((a, b))
            continue
        new = [moved[v] if moved[v] != v else None for v in (a, b)]
        for h in others:
            _insert_round(mesh.faces[h], a, b, new)
    for v in offset:
        if v not in plan.stays:
            mesh.verts[v] = mesh.verts[v] + offset[v]
    for g in plan.faces:
        mesh.faces[g] = [moved[v] for v in mesh.faces[g]]
    for a, b in plan.soft:
        if (moved[a], moved[b]) != (a, b):
            mesh.hidden.discard(edge_key(a, b))
            mesh.hidden.add(edge_key(moved[a], moved[b]))
    sides = [(a, b, mesh.add_face((a, b, moved[b], moved[a]))) for a, b in quads]
    _soften_round(mesh, sides, moved)
    return ("extrude" if sides else "stretch"), list(plan.faces)


def push_pull_faces(mesh, faces, matrix, distance, min_thickness=MIN_THICKNESS, keep_start=False):
    """(0.311) Push/Pull several faces of `mesh` at once (in place), all by the same `distance`, each along its own
    normal: faces looking the same way go exactly together; out for all when it is out for one. Faces that touch go
    as one piece — no wall between them, the lines between them kept on top (an offset's frame of four strips, two
    rooms of a plan); where they meet at an angle the points go so that each face is `distance` away (no gap).

    Each piece as push_pull does one face: with nothing beside it, it keeps its base (a closed solid); a face beside
    it lying along the motion (a box's side under its top) stretches with it; elsewhere new sides are made and the
    piece leaves its place (a tray, a box with no bottom), unless keep_start (Ctrl) leaves a face where it started.
    Pushed into a solid, it stops short of the face behind (one face alone can go right through: push_pull).

    The faces are only changed or added, never taken out: their numbers hold. The distance is clamped (the same for
    all) so no face turns inside out. result.faces: where the faces pushed now are (new ones, when a face was left
    where it started)."""
    if abs(distance) < 1e-9 or not faces:
        return PushPullResult("none", 0.0)
    matrix = np.asarray(matrix, dtype=float)
    edges = mesh.edge_faces()
    closed = mesh.is_closed()
    pieces = _pieces(mesh, faces, edges)
    count = {}
    for piece in pieces:
        for v in {v for g in piece for v in mesh.faces[g]}:
            count[v] = count.get(v, 0) + 1
    shared = {v for v, n in count.items() if n > 1}           # (pieces touching at a corner: each its own point)
    plans = [_piece_plan(mesh, p, matrix, edges, closed, keep_start, shared, min_thickness) for p in pieces]
    lower, upper = max(p.lower for p in plans), min(p.upper for p in plans)
    d = min(max(distance, lower), upper)
    if lower > upper or d * distance <= 0 or abs(d) < 1e-9:
        return PushPullResult("none", 0.0, clamped=True)
    modes, out, before = set(), [], len(mesh.faces)
    for plan in plans:
        mode, now = _apply_piece(mesh, plan, d, keep_start, matrix)
        modes.add(mode)
        out += now
    # where faces meeting at an angle did not all land flat (three or more round a point): folded, as Move does
    for g in sorted(set(out) | set(range(before, len(mesh.faces))) |
                    {h for p in plans for (_a, _b, others), s in zip(p.boundary, p.slide) if s for h in others}):
        added = _fold(mesh, g)
        if g in out:
            out += added
    mode = modes.pop() if len(modes) == 1 else "extrude"
    return PushPullResult(mode, d, clamped=abs(d - distance) > 1e-9, faces=tuple(out))


# ---------------------------------------------------------------- imprint

def _is_convex(pts, n):
    k = len(pts)
    return all(np.cross(pts[(i + 1) % k] - pts[i], pts[(i + 2) % k] - pts[(i + 1) % k]).dot(n) > 1e-12
               for i in range(k))


def _strictly_inside(poly, n, p, eps=1e-7):
    k = len(poly)
    return all(np.cross(poly[(i + 1) % k] - poly[i], p - poly[i]).dot(n) > eps for i in range(k))


def imprint_polygon(mesh, fi, points, tol=1e-6):
    """Draw a polygon ON face `fi` (SketchUp imprint): the face is split so the
    polygon becomes its own face, sharing edges with the rest of the solid.

    `points` are in object space and must lie on the face plane, strictly inside
    it. Supported for now: a quadrilateral inside a convex quadrilateral (a
    rectangle on a wall, slab or box face). The host face is split into the
    inner face plus four trapezoids; the four connecting edges are hidden.
    Returns the inner face index, or None if the case is not supported
    (the mesh is then left untouched).
    """
    host = mesh.faces[fi]
    if len(host) != 4 or len(points) != 4:
        made = _imprint_any(mesh, fi, points, tol)         # (0.150: a circle on a face, any convex in convex)
        return made if made is not None else _imprint_frame(mesh, fi, points, tol)    # (0.206: an L's offset)
    n = mesh.face_normal(fi)
    P = [mesh.verts[i] for i in host]
    R = [np.asarray(p, dtype=float) for p in points]
    if any(abs((r - P[0]).dot(n)) > tol for r in R):
        return None
    if polygon_normal(R).dot(n) < 0:
        R.reverse()
    if not _is_convex(P, n) or not _is_convex(R, n):
        return None
    if not all(_strictly_inside(P, n, r) for r in R):
        return None
    shift = min(range(4), key=lambda s: sum(np.linalg.norm(P[(i + s) % 4] - R[i]) for i in range(4)))
    p_ids = [host[(i + shift) % 4] for i in range(4)]
    quads_pts = [[mesh.verts[p_ids[i]], mesh.verts[p_ids[(i + 1) % 4]], R[(i + 1) % 4], R[i]] for i in range(4)]
    if not all(_is_convex(q, n) for q in quads_pts):
        return None

    r_ids = [mesh.add_vert(r) for r in R]
    mesh.faces[fi] = r_ids
    for i in range(4):
        mesh.add_face((p_ids[i], p_ids[(i + 1) % 4], r_ids[(i + 1) % 4], r_ids[i]), mesh.paint_of(fi))
        mesh.hidden.add(edge_key(p_ids[i], r_ids[i]))
    return fi


def _imprint_any(mesh, fi, points, tol=1e-6):
    """(0.150) A convex polygon (a circle's 24 sides…) strictly inside a convex face: the polygon becomes the face,
    the ring round it triangles between the two outlines (walked side by side, the shorter diagonal each step), their
    connecting edges hidden. Returns the inner face index, or None (not supported: the mesh untouched)."""
    host = list(mesh.faces[fi])
    n = mesh.face_normal(fi)
    P = [mesh.verts[i] for i in host]
    R = [np.asarray(p, dtype=float) for p in points]
    if len(R) < 3 or any(abs((r - P[0]).dot(n)) > tol for r in R):
        return None
    if polygon_normal(R).dot(n) < 0:
        R.reverse()
    if not _is_convex(P, n) or not _is_convex(R, n) or not all(_strictly_inside(P, n, r) for r in R):
        return None
    m, k = len(P), len(R)
    start = min(range(k), key=lambda j: float(np.linalg.norm(R[j] - P[0])))
    R = R[start:] + R[:start]
    r_ids = [mesh.add_vert(r) for r in R]
    mesh.faces[fi] = list(r_ids)
    i = j = 0
    while i < m or j < k:
        p0, p1 = host[i % m], host[(i + 1) % m]
        r0, r1 = r_ids[j % k], r_ids[(j + 1) % k]
        advance_p = j >= k or (i < m and np.linalg.norm(mesh.verts[p1] - mesh.verts[r0]) <=
                                np.linalg.norm(mesh.verts[r1] - mesh.verts[p0]))
        if advance_p:
            mesh.add_face((p0, p1, r0), mesh.paint_of(fi))
            mesh.hidden.add(edge_key(p1, r0))
            i += 1
        else:
            mesh.add_face((p0, r1, r0), mesh.paint_of(fi))
            mesh.hidden.add(edge_key(p0, r1))
            j += 1
    mesh.hidden.add(edge_key(host[0], r_ids[0]))
    return fi


def _imprint_frame(mesh, fi, points, tol=1e-6):
    """(0.206) A polygon with a corner for each of the face's — an offset of it, concave faces too (an L…) —
    strictly inside it: the polygon becomes the face, the frame round it one four-sided face per side (between a side
    of the face and the polygon's side beside it), their connecting edges hidden. Returns the inner face index, or
    None when they do not pair up so (the mesh untouched)."""
    from shapely.geometry import Polygon
    host = list(mesh.faces[fi])
    n = mesh.face_normal(fi)
    P = [mesh.verts[i] for i in host]
    R = [np.asarray(p, dtype=float) for p in points]
    m = len(P)
    if len(R) != m or m < 3 or any(abs((r - P[0]).dot(n)) > tol for r in R):
        return None
    if polygon_normal(R).dot(n) < 0:
        R.reverse()
    origin, u, v, _n = _face_frame(mesh, fi)

    def flat(q):
        return float((q - origin) @ u), float((q - origin) @ v)

    outer, inner = Polygon([flat(p) for p in P]), Polygon([flat(r) for r in R])
    if not outer.is_valid or not inner.is_valid or not outer.contains(inner) \
            or inner.exterior.intersects(outer.exterior):
        return None
    shift = min(range(m), key=lambda s: sum(float(np.linalg.norm(P[i] - R[(i + s) % m])) for i in range(m)))
    R = R[shift:] + R[:shift]
    quads = [Polygon([flat(P[i]), flat(P[(i + 1) % m]), flat(R[(i + 1) % m]), flat(R[i])]) for i in range(m)]
    frame = outer.area - inner.area
    if not all(q.is_valid and q.area > 1e-12 for q in quads) \
            or abs(sum(q.area for q in quads) - frame) > 1e-6 * max(outer.area, 1.0):
        return None                                # (the sides do not pair up: the quads would overlap)
    r_ids = [mesh.add_vert(r) for r in R]
    mesh.faces[fi] = list(r_ids)
    for i in range(m):
        mesh.add_face((host[i], host[(i + 1) % m], r_ids[(i + 1) % m], r_ids[i]), mesh.paint_of(fi))
        mesh.hidden.add(edge_key(host[i], r_ids[i]))
    return fi


# ---------------------------------------------------------------- a face picked alone (SketchUp's selection, 0.310)

def surface_faces(mesh, fi):
    """The faces of the face `fi` is part of, as SketchUp shows one: those joined to it across hidden edges (the four
    strips of an offset's frame, the triangles round a circle drawn on a face, a cylinder's side). A frozenset."""
    across = {}
    for e, fis in mesh.edge_faces().items():
        if e in mesh.hidden:
            for g in fis:
                across.setdefault(g, []).extend(h for h in fis if h != g)
    seen, todo = {fi}, [fi]
    while todo:
        for g in across.get(todo.pop(), ()):
            if g not in seen:
                seen.add(g)
                todo.append(g)
    return frozenset(seen)


def part_edges(mesh, faces):
    """The visible edges round and in the faces given: [(a, b)] (their outline, as SketchUp's double click adds)."""
    faces = set(faces)
    return [e for e, fis in mesh.visible_edges().items() if faces.intersection(fis)]


def compact(mesh):
    """The mesh without the points no face or line uses (indices renumbered; the hidden edges still there kept)."""
    used = sorted({i for f in mesh.faces for i in f} | {i for e in mesh.lines for i in e})
    new = {old: k for k, old in enumerate(used)}
    faces = [[new[i] for i in f] for f in mesh.faces]
    edges = {edge_key(f[i], f[(i + 1) % len(f)]) for f in faces for i in range(len(f))}
    hidden = {edge_key(new[a], new[b]) for a, b in mesh.hidden if a in new and b in new} & edges
    return PolyMesh([mesh.verts[i] for i in used], faces, hidden, mesh.voids,
                    [(new[a], new[b]) for a, b in mesh.lines], mesh.painted())


def remove_faces(mesh, faces, keep_edges=True):
    """Delete on faces picked alone: a new mesh without them. keep_edges: their outline stays as lines where no
    other face uses it (SketchUp keeps a deleted face's edges); else (picked with their edges, a double click) it
    goes too. The edges a face left still uses stay its own."""
    faces = set(faces)
    lines = list(mesh.lines)
    if keep_edges:
        for e, fis in mesh.edge_faces().items():
            if e not in mesh.hidden and fis and all(g in faces for g in fis):
                lines.append(e)
    kept = [f for g, f in enumerate(mesh.faces) if g not in faces]
    paint = [p for g, p in enumerate(mesh.painted()) if g not in faces]
    return compact(PolyMesh(mesh.verts, kept, mesh.hidden, mesh.voids, lines, paint))


def move_part(mesh, faces, matrix):
    """Faces picked alone moved (or turned) by `matrix` (object space): a new mesh, the faces beside them stretched
    as SketchUp's. A face that no longer lies flat is folded into triangles along hidden edges."""
    out = mesh.copy()
    moved = {i for g in faces for i in mesh.faces[g]}
    m = np.asarray(matrix, dtype=float)
    for i in moved:
        out.verts[i] = transform_point(m, mesh.verts[i])
    for g in [g for g, f in enumerate(out.faces) if moved.intersection(f) and len(f) > 3]:
        _fold(out, g)
    return out


def _fold(mesh, g):
    """A face that no longer lies flat folded into triangles along hidden edges (the first keeps its number). The
    faces added."""
    pts = mesh.face_points(g)
    n = polygon_normal(pts)
    if len(pts) <= 3 or np.linalg.norm(n) < 1e-12 or np.max(np.abs((pts - pts[0]) @ normalize(n))) < 1e-6:
        return []
    f = mesh.faces[g]
    local = PolyMesh(pts, [list(range(len(f)))]).triangulate()[0]
    tris = [[f[int(k)] for k in tri] for tri in local]
    mesh.faces[g] = tris[0]
    added = [mesh.add_face(tri, mesh.paint_of(g)) for tri in tris[1:]]
    ring = {edge_key(f[i], f[(i + 1) % len(f)]) for i in range(len(f))}
    mesh.hidden |= {edge_key(a, b) for tri in tris for a, b in zip(tri, tri[1:] + tri[:1])} - ring
    return added


# ---------------------------------------------------------------- dividing a face (Line tool)

def _face_frame(mesh, fi):
    """(origin, u, v, normal) of a face's plane, for tests in 2D."""
    n = mesh.face_normal(fi)
    u, v = plane_axes(n)
    return mesh.verts[mesh.faces[fi][0]], u, v, n


def _to2(points, origin, u, v):
    p = np.asarray(points, dtype=float).reshape(-1, 3) - origin
    return np.column_stack((p @ u, p @ v))


def _seg_dist(q, a, b):
    ab = b - a
    s = np.clip(float((q - a) @ ab) / max(float(ab @ ab), 1e-30), 0.0, 1.0)
    return float(np.linalg.norm(q - (a + s * ab)))


def _inside(poly2, q, tol):
    """Inside a simple polygon (2D) and farther than tol from its outline."""
    x, y = q
    inside = False
    k = len(poly2)
    for i in range(k):
        (x1, y1), (x2, y2) = poly2[i], poly2[(i + 1) % k]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside and min(_seg_dist(q, poly2[i], poly2[(i + 1) % k]) for i in range(k)) > tol


def _on_ring(mesh, ring, p, tol):
    """Where p is on a face's outline: ("vertex", k) at ring[k], ("edge", k) on the edge
    ring[k] -> ring[k + 1], or None."""
    for k, i in enumerate(ring):
        if np.linalg.norm(mesh.verts[i] - p) <= tol:
            return "vertex", k
    for k in range(len(ring)):
        if _seg_dist(p, mesh.verts[ring[k]], mesh.verts[ring[(k + 1) % len(ring)]]) <= tol:
            return "edge", k
    return None


def _cross2(a, b):
    return float(a[0] * b[1] - a[1] * b[0])


def _crossing(p, q, a, b):
    """(s along p-q, t along a-b) where the lines of the two 2D segments meet, or None (parallel)."""
    d1, d2 = q - p, b - a
    den = _cross2(d1, d2)
    if abs(den) < 1e-15:
        return None
    w = a - p
    return _cross2(w, d2) / den, _cross2(w, d1) / den


def _insert_on_edge(mesh, a, b, p):
    """A new vertex at p on the edge a-b, put into every face using that edge (a solid stays
    closed: no gap where the faces on both sides meet). Returns its index."""
    v = mesh.add_vert(p)
    for f in mesh.faces:
        for k in range(len(f)):
            if (f[k], f[(k + 1) % len(f)]) in ((a, b), (b, a)):
                f.insert(k + 1, v)
                break
    if edge_key(a, b) in mesh.hidden:
        mesh.hidden.discard(edge_key(a, b))
        mesh.hidden |= {edge_key(a, v), edge_key(v, b)}
    return v


def split_face(mesh, fi, path, tol=1e-6):
    """Divide face `fi` along `path` (object-space points on its plane), as a line drawn across
    a face in SketchUp: the first and last points on its outline (a corner or an edge), the
    others inside it, no part of the path outside the face. The face becomes two (fi and a new
    one, both facing as it did). A point on an edge is added to the faces on both sides of the
    edge, so a solid stays closed. Returns the new face's index, or None (mesh left as it was)."""
    path = [np.asarray(p, dtype=float) for p in path]
    if len(path) < 2 or np.linalg.norm(path[0] - path[-1]) <= tol:
        return None
    ring = list(mesh.faces[fi])
    origin, u, v, n = _face_frame(mesh, fi)
    if any(abs(float((p - origin) @ n)) > tol for p in path):
        return None
    if _on_ring(mesh, ring, path[0], tol) is None or _on_ring(mesh, ring, path[-1], tol) is None:
        return None
    poly2 = _to2([mesh.verts[i] for i in ring], origin, u, v)
    path2 = _to2(path, origin, u, v)
    if not all(_inside(poly2, q, tol) for q in path2[1:-1]):
        return None
    for p2, q2 in zip(path2, path2[1:]):
        length = float(np.linalg.norm(q2 - p2))
        if length <= tol or not _inside(poly2, (p2 + q2) / 2, tol):
            return None
        for k in range(len(poly2)):             # (a concave face: the segment must not go out and in)
            hit = _crossing(p2, q2, poly2[k], poly2[(k + 1) % len(poly2)])
            if hit is not None and tol / length < hit[0] < 1 - tol / length and -1e-9 <= hit[1] <= 1 + 1e-9:
                return None
    trial = mesh.copy()
    ends = []
    for p in (path[0], path[-1]):
        ring_t = trial.faces[fi]
        kind, k = _on_ring(trial, ring_t, p, tol)
        ends.append(ring_t[k] if kind == "vertex" else
                    _insert_on_edge(trial, ring_t[k], ring_t[(k + 1) % len(ring_t)], p))
    inner = [trial.add_vert(p) for p in path[1:-1]]
    ring_t = list(trial.faces[fi])
    m = len(ring_t)
    i_s, i_e = ring_t.index(ends[0]), ring_t.index(ends[1])

    def walk(i, j):
        return [ring_t[(i + k) % m] for k in range((j - i) % m + 1)]
    first, second = walk(i_s, i_e) + inner[::-1], walk(i_e, i_s) + inner
    if len(first) < 3 or len(second) < 3:
        return None
    trial.faces[fi] = first
    new = trial.add_face(second, trial.paint_of(fi))        # (0.392: both halves keep the face's paint)
    if trial.face_area(fi) < 1e-12 or trial.face_area(new) < 1e-12:
        return None
    mesh.verts, mesh.faces, mesh.hidden = trial.verts, trial.faces, trial.hidden
    mesh.paint = trial.painted()
    return new


def segment_pieces(mesh, fi, a, b, tol=1e-6):
    """The parts of the segment a-b (object space) that cross face `fi` from outline to outline,
    [(p, q)] — none if the segment is not on the face's plane."""
    ring = mesh.faces[fi]
    origin, u, v, n = _face_frame(mesh, fi)
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if abs(float((a - origin) @ n)) > tol or abs(float((b - origin) @ n)) > tol:
        return []
    poly2 = _to2([mesh.verts[i] for i in ring], origin, u, v)
    a2, b2 = _to2([a, b], origin, u, v)
    length = float(np.linalg.norm(b2 - a2))
    if length <= tol:
        return []
    ts = {0.0, 1.0}
    for k in range(len(poly2)):
        hit = _crossing(a2, b2, poly2[k], poly2[(k + 1) % len(poly2)])
        if hit is not None and 0.0 < hit[0] < 1.0 and -1e-9 <= hit[1] <= 1 + 1e-9:
            ts.add(float(hit[0]))
    ts = sorted(ts)
    pieces = []
    for t0, t1 in zip(ts, ts[1:]):
        if (t1 - t0) * length <= tol or not _inside(poly2, a2 + (b2 - a2) * (t0 + t1) / 2, tol):
            continue
        p, q = a + (b - a) * t0, a + (b - a) * t1
        if _on_ring(mesh, ring, p, tol) is not None and _on_ring(mesh, ring, q, tol) is not None:
            pieces.append((p, q))
    return pieces


def split_by_segment(mesh, a, b, tol=1e-6):
    """Divide every face of `mesh` that the segment a-b (object space) crosses from outline to
    outline — one line across a box's top that was already divided divides both parts. The
    mesh changes in place. Returns how many faces were divided."""
    count = 0
    for _ in range(64):
        for fi in range(len(mesh.faces)):
            pieces = segment_pieces(mesh, fi, a, b, tol)
            if pieces and split_face(mesh, fi, list(pieces[0]), tol) is not None:
                count += 1
                break
        else:
            break
    return count


# ---------------------------------------------------------------- rays

def ray_plane(origin, direction, plane_point, plane_normal):
    """Intersection of a ray with a plane, or None (parallel or behind)."""
    denom = direction.dot(plane_normal)
    if abs(denom) < 1e-9:
        return None
    t = (plane_point - origin).dot(plane_normal) / denom
    if t <= 0:
        return None
    return origin + t * direction


def closest_on_line_to_ray(origin, direction, line_point, line_dir):
    """Parameter s of the point line_point + s*line_dir closest to the ray, or None
    when the ray and the line are (almost) parallel."""
    w = origin - line_point
    a, b, c = direction.dot(direction), direction.dot(line_dir), line_dir.dot(line_dir)
    d, e = direction.dot(w), line_dir.dot(w)
    denom = a * c - b * b
    if abs(denom) < 1e-9:
        return None
    return (a * e - b * d) / denom
