"""Line tool and guide lines (SketchUp's Line and Tape Measure). Pure numpy.

- axis_inference: while drawing, lock to the red (X), green (Y) or blue (Z)
  axis through the last point when the mouse passes close to it on screen.
- polygon_frame: a closed planar outline becomes a face in its own frame.
- guide lines: infinite lines parallel to an edge, at a chosen distance.
"""

import math

import numpy as np

from .mesh import polygon_normal
from .sketch_geometry import closest_on_line_to_ray, normalize

AXES = (("x", np.array((1.0, 0.0, 0.0))), ("y", np.array((0.0, 1.0, 0.0))), ("z", np.array((0.0, 0.0, 1.0))))
AXIS_PX = 14


def axis_inference(last, origin, direction, mouse, project, radius_px=AXIS_PX):
    """Point on the X/Y/Z axis through `last` closest to the mouse ray, when that
    axis passes within `radius_px` of the mouse on screen. Returns (point, axis
    name) or (None, None). `project`: (N, 3) world -> (N, 2) screen."""
    last = np.asarray(last, dtype=float)
    mouse = np.asarray(mouse, dtype=float)
    best = None
    for name, axis in AXES:
        s = closest_on_line_to_ray(origin, direction, last, axis)
        if s is None or abs(s) < 1e-6:
            continue
        p = last + axis * s
        xy = project(p[None, :])[0]
        if np.any(np.isnan(xy)):
            continue
        dist = float(np.hypot(*(xy - mouse)))
        if dist <= radius_px and (best is None or dist < best[0]):
            best = (dist, p, name)
    return (best[1], best[2]) if best else (None, None)


def drop_collinear(points, tol=1e-9):
    """The outline without corners that lie on a straight side (clicks along an edge)."""
    pts = [np.asarray(p, dtype=float) for p in points]
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            if np.linalg.norm(np.cross(b - a, c - b)) <= tol * max(np.linalg.norm(b - a) * np.linalg.norm(c - b), 1e-12):
                del pts[i]
                changed = True
                break
    return pts


ARC_STEP_DEG = 15.0         # (0.151) an arc's pieces at most this many degrees each


def tangent_arc(a, tangent, b, normal, step_deg=ARC_STEP_DEG):
    """(0.151) The arc from a to b leaving a along `tangent`, in the plane of `normal` (SketchUp's tangent arc): its
    points after a, b the last — [b] alone when b is straight ahead (no arc), [] when b is a. Pieces of at most
    `step_deg` degrees."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = normalize(np.asarray(normal, float))
    d = b - a
    d = d - d.dot(n) * n
    if np.linalg.norm(d) < 1e-9:
        return []
    tg = np.asarray(tangent, float)
    tg = tg - tg.dot(n) * n
    if np.linalg.norm(tg) < 1e-9:
        return [b]
    tg = normalize(tg)
    side = np.cross(n, tg)                                   # (left of the way it goes)
    h = float(d.dot(side))
    if abs(h) < 1e-9 * max(np.linalg.norm(d), 1.0):
        return [b]
    radius = float(d.dot(d)) / (2.0 * h)                     # (signed: negative turns right)
    centre = a + side * radius
    u0, u1 = a - centre, (a + d) - centre
    axis = normalize(np.cross(u0, tg))                       # (turning the way it leaves)
    sweep = float(np.arctan2(np.cross(u0, u1).dot(axis), u0.dot(u1)))
    if sweep < 0:
        sweep += 2 * np.pi
    steps = max(2, int(np.ceil(np.degrees(sweep) / step_deg)))
    out = []
    for k in range(1, steps + 1):
        angle = sweep * k / steps
        c, s = np.cos(angle), np.sin(angle)
        rotated = u0 * c + np.cross(axis, u0) * s + axis * axis.dot(u0) * (1 - c)    # (Rodrigues)
        out.append(centre + rotated)
    out[-1] = b.copy()
    return out


def polygon_frame(points, view_dir=None, tol=1e-5):
    """Frame of a closed planar outline: (4x4 matrix, local points with z = 0).

    The face normal is local +Z: up for level outlines, towards the viewer
    (against `view_dir`) otherwise. None if the points are not on one plane.
    """
    pts = np.asarray(points, dtype=float)
    if len(pts) < 3:
        return None
    n = polygon_normal(pts)
    if np.linalg.norm(n) < 1e-12:
        return None
    if np.any(np.abs((pts - pts[0]) @ n) > tol):
        return None
    if abs(n[2]) > 0.999:
        flip = n[2] < 0
    else:
        flip = view_dir is not None and float(np.dot(n, view_dir)) > 0
    if flip:
        pts, n = pts[::-1].copy(), -n
    u = normalize(pts[1] - pts[0])
    u = normalize(u - u.dot(n) * n)
    v = np.cross(n, u)
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = u, v, n, pts[0]
    local = (np.linalg.inv(m) @ np.column_stack((pts, np.ones(len(pts)))).T).T[:, :3]
    local[:, 2] = 0.0
    return m, local


LOOP_TOL = 1e-5             # (0.372) m: points this close are one, a point this near a line is on it


def _param_on(p, a, b, tol):
    """Where p lies on the segment a-b (0…1), when it is within tol of it; else None."""
    d = b - a
    dd = float(d @ d)
    if dd < 1e-24:
        return None
    s = float((p - a) @ d) / dd
    if s < -tol or s > 1.0 + tol or np.linalg.norm(a + d * s - p) > tol:
        return None
    return min(max(s, 0.0), 1.0)


def _crossing(a, b, c, d, tol):
    """(s on a-b, t on c-d) where two segments cross (non-parallel, nearer than tol), else None."""
    u, v, w = b - a, d - c, a - c
    uu, uv, vv, uw, vw = u @ u, u @ v, v @ v, u @ w, v @ w
    den = uu * vv - uv * uv
    if den <= 1e-12 * uu * vv:
        return None                                     # (parallel: their ends on each other are found apart)
    s, t = (uv * vw - vv * uw) / den, (uu * vw - uv * uw) / den
    if not (-1e-9 <= s <= 1 + 1e-9 and -1e-9 <= t <= 1 + 1e-9):
        return None
    if np.linalg.norm((a + u * s) - (c + v * t)) > tol:
        return None
    return min(max(s, 0.0), 1.0), min(max(t, 0.0), 1.0)


def chain_loops(points, tol=LOOP_TOL):
    """(0.372) Where a chain of lines (its points, in order) closes on itself, as SketchUp makes faces: a line that
    ends on the chain — on one of its points or along one of its lines, not only at its first point — or crosses it
    closes the loop it makes. Returns (loops, loose): each loop its outline's points once round (the smallest ones:
    two loops side by side, not the outline round both; on one plane), loose [(p, q)] the lines on no loop — the
    tail the chain started with, what goes on beyond a crossing —; ([], None) when it does not close."""
    pts = [np.asarray(p, dtype=float) for p in points]
    segs = [(pts[k], pts[k + 1]) for k in range(len(pts) - 1) if np.linalg.norm(pts[k + 1] - pts[k]) > tol]
    if len(segs) < 3:
        return [], None
    cuts = [{0.0, 1.0} for _ in segs]
    for i, (a, b) in enumerate(segs):
        for j, (c, d) in enumerate(segs):
            if i == j:
                continue
            for q in (c, d):                            # (an end on the other line: a T, or a line laid back on it)
                s = _param_on(q, a, b, tol)
                if s is not None:
                    cuts[i].add(s)
            hit = _crossing(a, b, c, d, tol)
            if hit is not None:
                cuts[i].add(hit[0])
    verts = []

    def vid(p):
        for k, q in enumerate(verts):
            if np.linalg.norm(q - p) <= tol:
                return k
        verts.append(p)
        return len(verts) - 1

    edges = set()
    for (a, b), params in zip(segs, cuts):
        ts = sorted(params)
        ids = [vid(a + (b - a) * s) for s in ts]
        for u, v in zip(ids, ids[1:]):
            if u != v:
                edges.add((min(u, v), max(u, v)))
    core = set(edges)
    while True:                                         # (the tails off: what is not on any loop)
        degree = {}
        for u, v in core:
            degree[u] = degree.get(u, 0) + 1
            degree[v] = degree.get(v, 0) + 1
        bare = {e for e in core if degree[e[0]] < 2 or degree[e[1]] < 2}
        if not bare:
            break
        core -= bare
    if not core:
        return [], None
    around = {}
    for u, v in core:
        around.setdefault(u, set()).add(v)
        around.setdefault(v, set()).add(u)
    loops, used, seen = [], set(), set()
    for start in list(around):                          # (each connected part on its own plane)
        if start in seen:
            continue
        part, stack = set(), [start]
        while stack:
            k = stack.pop()
            if k not in part:
                part.add(k)
                stack.extend(around[k] - part)
        seen |= part
        ids = sorted(part)
        p = np.array([verts[k] for k in ids])
        centre = p.mean(axis=0)
        _u, sv, vt = np.linalg.svd(p - centre)
        normal = vt[2]
        if len(ids) < 3 or sv[1] < tol or np.max(np.abs((p - centre) @ normal)) > tol * 10:
            continue                                    # (along one line, or not on one plane: no face)
        ex = vt[0]
        ey = np.cross(normal, ex)
        flat = {k: np.array(((verts[k] - centre) @ ex, (verts[k] - centre) @ ey)) for k in ids}
        order = {k: sorted(around[k], key=lambda w: math.atan2(*(flat[w] - flat[k])[::-1])) for k in ids}
        walked = set()
        for u in ids:
            for v in around[u]:
                if (u, v) in walked:
                    continue
                cycle, a, b = [], u, v
                while (a, b) not in walked:
                    walked.add((a, b))
                    cycle.append(a)
                    ring = order[b]
                    a, b = b, ring[(ring.index(a) - 1) % len(ring)]     # (the next one clockwise round b)
                ring2 = np.array([flat[k] for k in cycle])
                area = 0.5 * float(np.sum(ring2[:, 0] * np.roll(ring2[:, 1], -1)
                                          - np.roll(ring2[:, 0], -1) * ring2[:, 1]))
                if area > tol * tol and len(cycle) >= 3:                 # (inside, counter-clockwise; the outside
                    loops.append([verts[k].copy() for k in cycle])         #  round the part goes clockwise)
                    used |= {(min(x, y), max(x, y)) for x, y in zip(cycle, cycle[1:] + cycle[:1])}
    if not loops:
        return [], None
    loose = [(verts[u].copy(), verts[v].copy()) for u, v in sorted(edges - used)]
    return loops, loose


def _touching(a, b, A, B, tol):
    """Which of the segments A[k]-B[k] the segment a-b meets (an end on the other, or crossing it), within tol."""
    d = b - a
    D = B - A
    dd = float(d @ d)

    def on(p, s0, s1):                     # points p (n, 3) on segments s0-s1 (n, 3)
        v = s1 - s0
        vv = np.einsum("ij,ij->i", v, v)
        with np.errstate(divide="ignore", invalid="ignore"):
            s = np.clip(np.einsum("ij,ij->i", p - s0, v) / vv, 0.0, 1.0)
        s = np.nan_to_num(s)
        return np.linalg.norm(s0 + v * s[:, None] - p, axis=1) <= tol

    n = len(A)
    near = on(A, np.tile(a, (n, 1)), np.tile(b, (n, 1))) | on(B, np.tile(a, (n, 1)), np.tile(b, (n, 1))) \
        | on(np.tile(a, (n, 1)), A, B) | on(np.tile(b, (n, 1)), A, B)
    w = a - A                                                  # (crossing: the nearest points of the two lines)
    uv = D @ d
    vv = np.einsum("ij,ij->i", D, D)
    uw, vw = w @ d, np.einsum("ij,ij->i", D, w)
    den = dd * vv - uv * uv
    ok = den > 1e-12 * dd * np.maximum(vv, 1e-30)
    with np.errstate(divide="ignore", invalid="ignore"):
        s, t = (uv * vw - vv * uw) / den, (dd * vw - uv * uw) / den
    inside = ok & (s >= -1e-9) & (s <= 1 + 1e-9) & (t >= -1e-9) & (t <= 1 + 1e-9)
    gap = np.linalg.norm((a + np.outer(np.nan_to_num(s), d)) - (A + D * np.nan_to_num(t)[:, None]), axis=1)
    return near | (inside & (gap <= tol))


def close_loops(new, old, plane, tol=LOOP_TOL):
    """(0.373) The faces new lines close with the loose lines already there, as SketchUp makes them whatever chain
    each line was drawn in (an arc ending on two lines, a line closing an outline drawn before). `new`, `old`: [(p, q)]
    world segments; `plane`: (point, normal) the new ones lie on — the old ones on it, joined to the new ones through
    ends, T's or crossings, are what is looked at. Returns (loops, pieces): the outlines (points once round) of the
    smallest loops through a new line, and for each segment (new, then old) its pieces once cut where the others meet
    it [(p, q, on a loop)]. ([], None) when nothing closes."""
    origin, normal = np.asarray(plane[0], float), normalize(np.asarray(plane[1], float))
    segs = [(np.asarray(p, float), np.asarray(q, float)) for p, q in list(new) + list(old)]
    fresh = len(new)
    if not segs or not fresh:
        return [], None
    flat = [k for k, (p, q) in enumerate(segs)
            if k < fresh or (abs(float((p - origin) @ normal)) <= tol * 10 and abs(float((q - origin) @ normal)) <= tol * 10)]
    A = np.array([segs[k][0] for k in flat])
    B = np.array([segs[k][1] for k in flat])
    keep, todo = set(range(fresh)), list(range(fresh))             # (positions in `flat`: the new ones first)
    while todo:                                                    # (what is joined to the new lines, step by step)
        i = todo.pop()
        for j in np.flatnonzero(_touching(A[i], B[i], A, B, tol)):
            if int(j) not in keep:
                keep.add(int(j))
                todo.append(int(j))
    comp = sorted(keep)
    CA, CB = A[comp], B[comp]
    cuts = []
    for i in range(len(comp)):                                     # (each cut where the others' ends or lines meet it)
        a, b = CA[i], CB[i]
        d = b - a
        dd = float(d @ d)
        params = {0.0, 1.0}
        if dd > 1e-24:
            for P in (CA, CB):
                s = np.clip((P - a) @ d / dd, 0.0, 1.0)
                hit = np.linalg.norm(a + np.outer(s, d) - P, axis=1) <= tol
                params |= {float(x) for x in s[hit]}
            D, w = CB - CA, a - CA
            uv, vv = D @ d, np.einsum("ij,ij->i", D, D)
            uw, vw = w @ d, np.einsum("ij,ij->i", D, w)
            den = dd * vv - uv * uv
            ok = den > 1e-12 * dd * np.maximum(vv, 1e-30)
            with np.errstate(divide="ignore", invalid="ignore"):
                s, t = (uv * vw - vv * uw) / den, (dd * vw - uv * uw) / den
            s, t = np.nan_to_num(s), np.nan_to_num(t)
            inside = ok & (s > 1e-9) & (s < 1 - 1e-9) & (t >= -1e-9) & (t <= 1 + 1e-9)
            gap = np.linalg.norm(a + np.outer(s, d) - (CA + D * t[:, None]), axis=1)
            params |= {float(x) for x in s[inside & (gap <= tol)]}
        cuts.append(sorted(params))
    verts, cells = [], {}

    def vid(p):
        key = tuple(np.floor(p / (tol * 4)).astype(np.int64))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for k in cells.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                        if np.linalg.norm(verts[k] - p) <= tol:
                            return k
        verts.append(p)
        cells.setdefault(key, []).append(len(verts) - 1)
        return len(verts) - 1

    sub = []                                                       # per segment of comp: [(u, v)] its pieces
    for i, ts in enumerate(cuts):
        a, b = CA[i], CB[i]
        ids = [vid(a + (b - a) * s) for s in ts]
        sub.append([(u, v) for u, v in zip(ids, ids[1:]) if u != v])
    edges = {(min(u, v), max(u, v)) for ps in sub for u, v in ps}
    core = set(edges)
    at, degree = {}, {}
    for e in core:
        for v in e:
            at.setdefault(v, []).append(e)
            degree[v] = degree.get(v, 0) + 1
    loose_ends = [v for v, n in degree.items() if n < 2]
    while loose_ends:                                              # (the tails off, end by end: what is on no loop)
        v = loose_ends.pop()
        for e in at[v]:
            if e in core:
                core.discard(e)
                for w in e:
                    degree[w] -= 1
                    if degree[w] == 1:
                        loose_ends.append(w)
    starts = {(min(u, v), max(u, v)) for i in range(fresh) for u, v in sub[i]} & core
    if not starts:
        return [], None
    u_ax, v_ax = _plane_axes(normal)
    around = {}
    for u, v in core:
        around.setdefault(u, set()).add(v)
        around.setdefault(v, set()).add(u)
    flat2 = {k: np.array(((verts[k] - origin) @ u_ax, (verts[k] - origin) @ v_ax)) for k in around}
    order = {k: sorted(around[k], key=lambda w: math.atan2(*(flat2[w] - flat2[k])[::-1])) for k in around}
    loops, used, walked = [], set(), set()
    for u0, v0 in starts:
        for u, v in ((u0, v0), (v0, u0)):
            if (u, v) in walked:
                continue
            cycle, a, b = [], u, v
            while (a, b) not in walked and len(cycle) <= len(core) + 1:
                walked.add((a, b))
                cycle.append(a)
                ring = order[b]
                a, b = b, ring[(ring.index(a) - 1) % len(ring)]         # (the next one clockwise round b)
            ring2 = np.array([flat2[k] for k in cycle])
            area = 0.5 * float(np.sum(ring2[:, 0] * np.roll(ring2[:, 1], -1) - np.roll(ring2[:, 0], -1) * ring2[:, 1]))
            if area > tol * tol and len(cycle) >= 3:                     # (inside, counter-clockwise)
                loops.append([verts[k].copy() for k in cycle])
                used |= {(min(x, y), max(x, y)) for x, y in zip(cycle, cycle[1:] + cycle[:1])}
    if not loops:
        return [], None
    pieces = [[] for _ in segs]
    for i, k in enumerate(comp):
        whole = flat[k]
        pieces[whole] = [(verts[u].copy(), verts[v].copy(), (min(u, v), max(u, v)) in used) for u, v in sub[i]]
    for k, (p, q) in enumerate(segs):
        if not pieces[k]:
            pieces[k] = [(p, q, False)]
    return loops, pieces


def _plane_axes(normal):
    from .sketch_geometry import plane_axes
    return plane_axes(normal)


def paths(pairs):
    """(0.373) Lines (pairs of point numbers) as paths: each a list of point numbers in order, from a loose end or a
    fork to the next one; a closed loop with its first point again at the end."""
    around = {}
    for k, (a, b) in enumerate(pairs):
        around.setdefault(a, []).append((k, b))
        around.setdefault(b, []).append((k, a))
    used, out = set(), []

    def walk(start, k, nxt):
        path = [start]
        while True:
            used.add(k)
            path.append(nxt)
            ways = [(j, w) for j, w in around[nxt] if j not in used]
            if len(around[nxt]) != 2 or not ways:
                return path
            k, nxt = ways[0][0], ways[0][1]
    for v in [v for v in around if len(around[v]) != 2]:          # (from the ends and the forks first)
        for k, w in around[v]:
            if k not in used:
                out.append(walk(v, k, w))
    for k, (a, b) in enumerate(pairs):                             # (what is left: closed loops)
        if k not in used:
            out.append(walk(a, k, b))
    return out


def plane_of(points, view_dir=None, tol=1e-6):
    """(0.373) The plane the points lie on: (point, unit normal) — for points along one line, the level plane when it
    is level, else the plane through it that faces the viewer most; None when they are not on one plane."""
    pts = np.asarray(points, dtype=float).reshape(-1, 3)
    centre = pts.mean(axis=0)
    _u, s, vt = np.linalg.svd(pts - centre)
    span = float(s[0]) if len(s) else 0.0
    if len(s) > 1 and s[1] > max(tol, 1e-9 * span):
        normal = vt[2] if len(vt) > 2 else np.cross(vt[0], vt[1])
        if np.max(np.abs((pts - centre) @ normal)) > tol * 10 + 1e-9 * span:
            return None
        if normal[2] < -1e-9 or (abs(normal[2]) <= 1e-9 and view_dir is not None and float(normal @ view_dir) > 0):
            normal = -normal
        return centre, normalize(normal)
    along = vt[0]
    if abs(along[2]) < 1e-6:
        return centre, np.array((0.0, 0.0, 1.0))
    look = np.asarray(view_dir if view_dir is not None else (0.0, 1.0, 0.0), dtype=float)
    normal = look - float(look @ along) * along
    if np.linalg.norm(normal) < 1e-9:
        normal = np.cross(along, (1.0, 0.0, 0.0))
    return centre, -normalize(normal)


def offset_path(points2, distance, closed=False):
    """(0.373) A path (2D points) offset `distance` to its left (to its right if negative), its corners sharp; a
    closed one (its first point again at the end) inwards when it runs counter-clockwise. A list of paths (2D points;
    a closed one again ending on its first point) — empty when it vanishes."""
    from shapely.geometry import LineString, Polygon
    pts = [tuple(map(float, p)) for p in points2]
    if closed:
        poly = Polygon(pts[:-1] if pts[0] == pts[-1] else pts)
        if not poly.is_valid or poly.area <= 0:
            return []
        ccw = poly.exterior.is_ccw
        grown = poly.buffer(-float(distance) if ccw else float(distance), join_style="mitre", mitre_limit=10.0)
        parts = [grown] if grown.geom_type == "Polygon" else list(getattr(grown, "geoms", []))
        out = []
        for g in parts:
            if g.is_empty:
                continue
            ring = list(g.exterior.coords)
            if ring and Polygon(ring).exterior.is_ccw != ccw:
                ring = ring[::-1]
            out.append(ring)
        return out
    line = LineString(pts)
    if line.length <= 0:
        return []
    moved = line.offset_curve(float(distance), join_style="mitre", mitre_limit=10.0)
    parts = [moved] if moved.geom_type == "LineString" else list(getattr(moved, "geoms", []))
    return [list(g.coords) for g in parts if not g.is_empty and len(g.coords) >= 2]


def guide_through(a, b, point):
    """Guide parallel to the edge a-b passing through `point`.
    Returns (guide point, direction, distance from the edge line)."""
    a, b, point = (np.asarray(x, dtype=float) for x in (a, b, point))
    d = normalize(b - a)
    w = point - a
    perp = w - w.dot(d) * d
    return a + perp, d, float(np.linalg.norm(perp))


def guide_at_distance(a, b, point, distance):
    """Guide parallel to the edge a-b at `distance` from it, on the side of `point`.
    Returns (guide point, direction) or None if `point` is on the edge line."""
    a, b, point = (np.asarray(x, dtype=float) for x in (a, b, point))
    d = normalize(b - a)
    w = point - a
    perp = w - w.dot(d) * d
    length = np.linalg.norm(perp)
    if length < 1e-9:
        return None
    return a + perp / length * distance, d


def line_line_intersection(p1, d1, p2, d2, tol=1e-6):
    """Intersection point of two 3D lines, or None (parallel or skew)."""
    p1, d1, p2, d2 = (np.asarray(x, dtype=float) for x in (p1, d1, p2, d2))
    w = p1 - p2
    a, b, c = d1.dot(d1), d1.dot(d2), d2.dot(d2)
    d, e = d1.dot(w), d2.dot(w)
    denom = a * c - b * b
    if abs(denom) < 1e-12:
        return None
    s = (b * e - c * d) / denom
    t = (a * e - b * d) / denom
    q1, q2 = p1 + s * d1, p2 + t * d2
    if np.linalg.norm(q1 - q2) > tol:
        return None
    return (q1 + q2) / 2
