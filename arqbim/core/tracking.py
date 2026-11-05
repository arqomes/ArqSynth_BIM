"""Alignments (0.60): SketchUp's inference points, Revit's alignment lines, AutoCAD's object
tracking. Pure numpy: the screen projection is passed in, as for the snaps (inference.py).

- A point the cursor rests on for a moment (an endpoint, a midpoint, an intersection…) is
  "acquired" (Tracking.rest). The cursor then lines up with it along the red / green (/ blue)
  axis: a dashed line shows it and the point found is on it — and, with two such lines near
  the mouse, where they cross.
- An edge the cursor rests on is acquired too: drawing on from a point, the segment can be
  parallel or perpendicular to it (magenta), or run along its extension.
- Shift locks the line in use (Tracking.lock): every point found is then on it.
"""

import time
from dataclasses import dataclass, field

import numpy as np

from .inference import ON_EDGE, ON_FACE, ON_GUIDE, POINT_KINDS, POINT_RADIUS_PX
from .lines import AXES, AXIS_PX, line_line_intersection
from .sketch_geometry import closest_on_line_to_ray

ACQUIRE_S = 0.2          # resting this long on a point or an edge acquires it
MAX_POINTS = 3           # the points acquired last (older ones are let go)
MAX_EDGES = 2
ALIGN_PX = 10            # a line that passes this close to the mouse (screen pixels) is offered
AXIAL = 1 - 1e-6         # a direction this close to an axis is that axis

AXIS_KINDS = ("axis_x", "axis_y", "axis_z")
ALIGN_KINDS = ("align_x", "align_y", "align_z")
EDGE_KINDS = ("parallel", "perpendicular", "extension")
CROSSING, FOOT, LOCKED = "crossing", "perpendicular_foot", "locked"


@dataclass
class InferenceLine:
    point: np.ndarray        # where it comes from: the point drawn from, a point acquired, an edge's end
    direction: np.ndarray    # unit
    kind: str                # AXIS_KINDS, ALIGN_KINDS or EDGE_KINDS
    edge: tuple = None       # (a, b): the edge it comes from (parallel, perpendicular, extension)


@dataclass
class Inferred:
    point: np.ndarray
    kind: str                # a snap kind (inference.py), a line's kind, CROSSING, FOOT or LOCKED
    lines: list = field(default_factory=list)    # the InferenceLines it lies on (shown dashed)
    snap: object = None


def _unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else None


def _axial(d):
    return any(abs(float(d @ axis)) >= AXIAL for _name, axis in AXES)


class Tracking:
    """The points and edges acquired while drawing, and the line locked with Shift."""

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.points = []              # acquired points, the newest last
        self.edges = []               # acquired edges (a, b), the newest last
        self.lock = None              # InferenceLine kept while Shift is held
        self.current = None           # the line the last point found was on (Shift locks it)
        self._resting = None          # (key, since, ("point", p) | ("edge", (a, b)))

    def clear(self):
        self.points, self.edges = [], []
        self.lock = self.current = None
        self._resting = None

    def rest(self, snap):
        """The snap under the cursor now. What the cursor rested on long enough (now, or until it
        moved away) is acquired. Returns True when something new was acquired."""
        now = self.clock()
        if snap is not None and snap.kind in POINT_KINDS:
            p = np.asarray(snap.point, dtype=float)
            item = ("point", p.copy())
            key = ("point",) + tuple(np.round(p, 6))
        elif snap is not None and snap.kind == ON_EDGE and snap.edge is not None:
            a, b = (np.asarray(x, dtype=float) for x in snap.edge)
            item = ("edge", (a.copy(), b.copy()))
            key = ("edge",) + tuple(np.round(np.concatenate((a, b)), 6))
        else:
            item = key = None
        new = False
        if self._resting is not None and self._resting[0] != key:
            if now - self._resting[1] >= ACQUIRE_S:          # rested there, then moved away
                new = self._acquire(self._resting[2])
            self._resting = None
        if key is None:
            return new
        if self._resting is None:
            self._resting = (key, now, item)
        elif now - self._resting[1] >= ACQUIRE_S:
            new = self._acquire(item) or new
        return new

    def _acquire(self, item):
        kind, value = item
        if kind == "point":
            for k, p in enumerate(self.points):
                if np.linalg.norm(p - value) < 1e-6:
                    if k == len(self.points) - 1:
                        return False
                    self.points.append(self.points.pop(k))   # already there: the newest again
                    return False
            self.points = (self.points + [value])[-MAX_POINTS:]
            return True
        a, b = value
        d = _unit(b - a)
        if d is None:
            return False
        for k, (ea, eb) in enumerate(self.edges):
            e = _unit(eb - ea)
            if e is not None and abs(float(d @ e)) >= AXIAL and np.linalg.norm(np.cross(a - ea, e)) < 1e-6:
                if k == len(self.edges) - 1:
                    return False
                self.edges.append(self.edges.pop(k))
                return False
        self.edges = (self.edges + [(a, b)])[-MAX_EDGES:]
        return True


def inference_lines(tracking, last=None, plan=False, auto=(), plane=None):
    """The lines the cursor can follow: the axes through `last` (the point drawn from), parallel
    and perpendicular to the acquired edges through it, the axis lines through the acquired
    points and through `auto` — the corners near the cursor, lined up with by themselves (0.61,
    as Revit) — and the acquired edges' extensions. In a plan only what lies flat (no blue).
    plane: (point, normal) of the plane drawn on (the floor, a wall's face…) — the points and
    edges are brought onto it and only the axes lying in it are followed (lined up with a wall's
    top corner, the point stays on the floor), but for the axes through `last`."""
    axes = AXES[:2] if plan else AXES
    if plane is not None:
        origin, normal = (np.asarray(v, dtype=float) for v in plane)
        normal = _unit(normal)
        flat = lambda p: p - normal * float((p - origin) @ normal)      # noqa: E731
        in_plane = [(name, d) for name, d in AXES if abs(float(d @ normal)) < 1e-9]
    else:
        normal, flat, in_plane = None, (lambda p: p), list(AXES[:2])
    lines = []
    if last is not None:
        last = np.asarray(last, dtype=float)
        lines += [InferenceLine(last, d, "axis_" + name) for name, d in axes]
        for a, b in tracking.edges:
            e = _unit(b - a)
            if e is None or _axial(e) or (plan and abs(e[2]) > 1e-9):
                continue
            if normal is not None and abs(float(e @ normal)) > 1e-9:
                continue                              # (not along the plane drawn on)
            lines.append(InferenceLine(last, e, "parallel", (a, b)))
            n = normal if normal is not None else (np.array((0.0, 0.0, 1.0)) if abs(e[2]) < 1e-9 else None)
            p = _unit(np.cross(n, e)) if n is not None else None          # perpendicular, in the plane
            if p is not None and not _axial(p):
                lines.append(InferenceLine(last, p, "perpendicular", (a, b)))
    seen = [last] if last is not None else []

    def fresh(p):
        if any(np.linalg.norm(p - q) < 1e-6 for q in seen):
            return False
        seen.append(p)
        return True

    for p in tracking.points:
        q = flat(np.asarray(p, dtype=float))
        if fresh(q):
            lines += [InferenceLine(q, d, "align_" + name) for name, d in in_plane]
            if not plan and plane is None:
                lines.append(InferenceLine(q, AXES[2][1], "align_z"))
    for p in auto:
        q = flat(np.asarray(p, dtype=float))
        if fresh(q):
            lines += [InferenceLine(q, d, "align_" + name) for name, d in in_plane]
    for a, b in tracking.edges:
        e = _unit(b - a)
        if e is None or (normal is not None and abs(float(e @ normal)) > 1e-9):
            continue                                  # (an edge across the plane: its extension leaves it)
        a, b = flat(np.asarray(a, dtype=float)), flat(np.asarray(b, dtype=float))
        lines.append(InferenceLine(a, e, "extension", (a, b)))
    return lines


def near_lines(lines, origin, direction, mouse, project, radius_px=ALIGN_PX):
    """The lines passing within radius_px of the mouse on screen: [(pixels, point on it, line)],
    nearest first. A line is not offered at its own point (there that point is the snap), an
    extension only beyond its edge's ends."""
    mouse = np.asarray(mouse, dtype=float)
    found = []
    for line in lines:
        s = closest_on_line_to_ray(origin, direction, line.point, line.direction)
        if s is None:
            continue
        p = line.point + line.direction * s
        xy = project(p[None, :])[0]
        if np.any(np.isnan(xy)):
            continue
        dist = float(np.hypot(*(xy - mouse)))
        if dist > (max(radius_px, AXIS_PX) if line.kind in AXIS_KINDS else radius_px):   # (the axes: as before)
            continue
        if line.kind in AXIS_KINDS:
            if abs(s) < 1e-6:
                continue
        else:
            src = project(line.point[None, :])[0]
            if not np.any(np.isnan(src)) and float(np.hypot(*(xy - src))) < POINT_RADIUS_PX:
                continue
        if line.kind == "extension":
            length = float(np.linalg.norm(line.edge[1] - line.edge[0]))
            if -1e-9 <= s <= length + 1e-9:
                continue
        found.append((dist, p, line))
    found.sort(key=lambda c: (round(c[0] * 2) / 2, c[2].kind not in AXIS_KINDS))   # (one line twice: the axis)
    return found


def _screen_near(point, mouse, project, radius_px):
    xy = project(np.asarray(point, dtype=float)[None, :])[0]
    return not np.any(np.isnan(xy)) and float(np.hypot(*(xy - np.asarray(mouse, dtype=float)))) <= radius_px


def _on_segment(p, a, b, tol=1e-6):
    u = b - a
    uu = float(u @ u)
    if uu < 1e-18:
        return False
    s = float((p - a) @ u) / uu
    return -tol <= s <= 1 + tol


def infer(snap, lines, origin, direction, mouse, project, last=None, lock=None):
    """The point for the mouse, in this order: (Shift) on the locked line; a point (endpoint,
    intersection, midpoint, origin); where two lines cross; where a line crosses the edge under
    the mouse; the foot of the perpendicular from `last` to that edge; on that edge; on the
    nearest line; on a face. None: nothing (the caller takes its plane)."""
    origin, direction = np.asarray(origin, dtype=float), np.asarray(direction, dtype=float)
    edge = None
    if snap is not None and snap.kind in (ON_EDGE, ON_GUIDE) and snap.edge is not None:
        edge = tuple(np.asarray(x, dtype=float) for x in snap.edge)

    if lock is not None:
        if edge is not None:
            x = line_line_intersection(lock.point, lock.direction, edge[0], edge[1] - edge[0])
            if x is not None:
                return Inferred(x, LOCKED, [lock], snap)
        if snap is not None and snap.kind in POINT_KINDS + (ON_EDGE, ON_GUIDE):
            foot = lock.point + lock.direction * float((snap.point - lock.point) @ lock.direction)
            return Inferred(foot, LOCKED, [lock], snap)
        s = closest_on_line_to_ray(origin, direction, lock.point, lock.direction)
        if s is None:
            return None
        return Inferred(lock.point + lock.direction * s, LOCKED, [lock])

    if snap is not None and snap.kind in POINT_KINDS:
        return Inferred(np.asarray(snap.point, dtype=float).copy(), snap.kind, [], snap)

    near = near_lines(lines, origin, direction, mouse, project)
    axes = [line for _d, _p, line in near if line.kind in AXIS_KINDS]
    if axes:
        # along an axis from the point drawn from, a line parallel to it does not pull the point off it
        # (only the lines crossing it count: where they cross it)
        near = [c for c in near if c[2].kind in AXIS_KINDS
                or all(abs(float(c[2].direction @ a.direction)) < AXIAL for a in axes)]
    crossings = []
    for i, (_d1, _p1, l1) in enumerate(near):
        for _d2, _p2, l2 in near[i + 1:]:
            if abs(float(l1.direction @ l2.direction)) >= AXIAL:
                continue
            x = line_line_intersection(l1.point, l1.direction, l2.point, l2.direction)
            if x is not None and _screen_near(x, mouse, project, POINT_RADIUS_PX):
                on_axis = l1.kind in AXIS_KINDS or l2.kind in AXIS_KINDS
                xy = project(x[None, :])[0]
                crossings.append((not on_axis, float(np.hypot(*(xy - np.asarray(mouse, dtype=float)))), x, l1, l2))
    if crossings:
        _off, _dist, x, l1, l2 = min(crossings, key=lambda c: (c[0], c[1]))   # (on an axis first)
        return Inferred(x, CROSSING, [l1, l2])

    if edge is not None:
        a, b = edge
        for _d, _p, line in near:
            x = line_line_intersection(line.point, line.direction, a, b - a)
            if x is not None and _on_segment(x, a, b) and _screen_near(x, mouse, project, POINT_RADIUS_PX):
                return Inferred(x, "intersection", [line], snap)
        if last is not None:
            u = b - a
            uu = float(u @ u)
            if uu > 1e-18:
                foot = a + u * (float((np.asarray(last, dtype=float) - a) @ u) / uu)
                if (np.linalg.norm(foot - last) > 1e-6 and _on_segment(foot, a, b)
                        and _screen_near(foot, mouse, project, POINT_RADIUS_PX)):
                    return Inferred(foot, FOOT, [], snap)
        return Inferred(np.asarray(snap.point, dtype=float).copy(), snap.kind, [], snap)

    if near:
        _d, p, line = near[0]
        return Inferred(p, line.kind, [line])
    if snap is not None and snap.kind == ON_FACE:
        return Inferred(np.asarray(snap.point, dtype=float).copy(), ON_FACE, [], snap)
    return None
