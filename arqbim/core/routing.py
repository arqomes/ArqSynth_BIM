"""Branches around obstacles (0.199, Phase 6, step 3: «o ramal ainda não contorna obstáculos»): the way in plan of
a branch's run from a to b when a column (or a pad footing) stands on the straight line — square turns only, along
the line a → b and across it, the fewest bends and the shortest, every straight run long enough for its bends.

The obstacles are boxes in plan (their corners), already grown by the pipe's radius and its clearance: the pipe's
axis may run along their sides. Each is taken by its bounds along the line and across it (a box at an angle to the
line: the rectangle round it).

Pure numpy, no IFC."""

import heapq

import numpy as np

BEND = 0.5                  # m: what a bend costs against length (fewer bends before a shorter way)
MAX_DETOUR = 3.0            # m: a way longer than the straight line by more than this is no way


def _bounds(boxes, a, u, v):
    """Each box's (s0, s1, t0, t1): along u and across (v) from a."""
    out = []
    for box in boxes:
        c = np.asarray(box, float)[:, :2] - a
        s, t = c @ u, c @ v
        out.append((float(s.min()), float(s.max()), float(t.min()), float(t.max())))
    return out


def blocked(a, b, boxes, tol=1e-7):
    """Does the straight line a → b (2,) go through one of the boxes (not along a side of it)?"""
    a, b = np.asarray(a, float)[:2], np.asarray(b, float)[:2]
    length = float(np.linalg.norm(b - a))
    if length < 1e-9:
        return False
    u = (b - a) / length
    v = np.array((-u[1], u[0]))
    return any(t0 < -tol and t1 > tol and s0 < length - tol and s1 > tol for s0, s1, t0, t1 in _bounds(boxes, a, u, v))


def route(a, b, boxes, min_run=0.0, first_along=False, last_along=True):
    """The way in plan from a to b (2,) around the boxes [(n, 2) corners each]: [points (2,)], a first, b last — [a,
    b] when the line is free —, or None (no way, or a far longer one). Every straight run is min_run long or more;
    first_along / last_along: the first / last run goes along a → b (a tee at that end, square to its main). A box
    a or b is in does not count."""
    a, b = np.asarray(a, float)[:2], np.asarray(b, float)[:2]
    length = float(np.linalg.norm(b - a))
    if length < 1e-9:
        return [a, b]
    u = (b - a) / length
    v = np.array((-u[1], u[0]))
    rects = [r for r in _bounds(boxes, a, u, v)
             if not (r[0] < 0.0 < r[1] and r[2] < 0.0 < r[3]) and not (r[0] < length < r[1] and r[2] < 0.0 < r[3])]
    if not any(t0 < 0.0 < t1 and s0 < length and s1 > 0.0 for s0, s1, t0, t1 in rects):
        return [a, b]
    # (where it may turn: along the boxes' sides, and far enough out for a run between two bends)
    ss = sorted({0.0, length, *(r[0] for r in rects), *(r[1] for r in rects),
                 *(s for r in rects for s in (r[0] - min_run, r[1] + min_run) if 0.0 < s < length)})
    ts = sorted({0.0, *(r[2] for r in rects), *(r[3] for r in rects),
                 *(min(r[2], -min_run) for r in rects), *(max(r[3], min_run) for r in rects)})

    def inside(s, t):
        return any(s0 < s < s1 and t0 < t < t1 for s0, s1, t0, t1 in rects)

    def free(p, q):                                # (a straight run along s or along t, through no box)
        (sa, ta), (sb, tb) = p, q
        lo_s, hi_s, lo_t, hi_t = min(sa, sb), max(sa, sb), min(ta, tb), max(ta, tb)
        for s0, s1, t0, t1 in rects:
            if lo_t == hi_t and t0 < lo_t < t1 and lo_s < s1 and hi_s > s0:
                return False
            if lo_s == hi_s and s0 < lo_s < s1 and lo_t < t1 and hi_t > t0:
                return False
        return True

    start, goal = (ss.index(0.0), ts.index(0.0)), (ss.index(length), ts.index(0.0))
    # Dijkstra over (node, the way the last run went): a move is one straight run to another node, square to the
    # last (no two runs one way: that is one longer run)
    ways = ((1, 0), (-1, 0), (0, 1), (0, -1))
    todo = [(0.0, 0, start, None, None)]
    best, back, n = {}, {}, 0
    while todo:
        cost, _n, node, way, prev = heapq.heappop(todo)
        if (node, way) in best:
            continue
        best[(node, way)] = cost
        back[(node, way)] = prev
        if node == goal and (not last_along or way == 0):
            break
        for k, (di, dj) in enumerate(ways):
            if way is not None and (k == way or k == way ^ 1):
                continue
            if way is None and first_along and k != 0:
                continue
            i, j = node
            here = (ss[i], ts[j])
            while True:
                i, j = i + di, j + dj
                if not (0 <= i < len(ss) and 0 <= j < len(ts)):
                    break
                there = (ss[i], ts[j])
                if inside(*there) or not free(here, there):
                    break
                run = abs(there[0] - here[0]) + abs(there[1] - here[1])
                if run >= min_run - 1e-9:
                    n += 1
                    heapq.heappush(todo, (cost + run + BEND, n, (i, j), k, (node, way)))
    else:
        return None
    # (the goal reached: back through the runs)
    key = (goal, way)
    nodes = []
    while key is not None:
        nodes.append(key[0])
        key = back[key]
    nodes.reverse()
    points = [a + u * ss[i] + v * ts[j] for i, j in nodes]
    total = sum(float(np.linalg.norm(q - p)) for p, q in zip(points, points[1:]))
    if total > length + MAX_DETOUR:
        return None
    points[0], points[-1] = a, b
    return points
