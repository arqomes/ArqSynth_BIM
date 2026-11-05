"""Drawing walls point by point (Revit / ArchiCAD style). Pure numpy.

Reference line: the line the user draws can be the wall's axis, or its left
or right face (seen in the drawing direction). The axis is then that line
moved sideways by half the thickness, so an outline typed along the outside
faces gives exactly those outside sizes.

Corners: at a right-angle corner the earlier wall runs through the corner and
the new wall butts against its face, so the corner is closed with no overlap
and no gap (IFC volumes and quantities stay right). Everything is worked out
from the two AXIS lines (where they cross), so it is the same for walls drawn
by the axis or by a face, within one chain or against walls drawn earlier,
separately (find_joint): a new wall starting at another wall's end makes a
corner, starting along its middle a T junction.
"""

import math

import numpy as np

AXIS_TOLERANCE = math.sin(math.radians(2.5))   # lock to the red/green axis within 2.5°
PERPENDICULAR = 0.01
MIN_JOIN_ANGLE = math.radians(15)               # sharper corners are not joined (the mitre would be too long)
MAX_CUT_TAN = 1.0 / math.tan(MIN_JOIN_ANGLE / 2)
REFERENCES = ("axis", "left", "right")
_REFERENCE_SIDE = {"axis": 0.0, "left": -0.5, "right": 0.5}   # axis offset to the left, × thickness


def horizontal_dir(start, end):
    d = (np.asarray(end, dtype=float) - np.asarray(start, dtype=float)) * np.array((1, 1, 0))
    n = np.linalg.norm(d)
    return d / n if n > 1e-9 else None


def left_normal(d):
    """Horizontal unit vector to the left of the direction d (seen from above)."""
    return np.array((-d[1], d[0], 0.0))


def axis_lock(start, end):
    """Snap the direction start->end to world X (red) or Y (green) when close.
    Returns (end, axis) with axis in {"x", "y", None}."""
    start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    d = horizontal_dir(start, end)
    if d is None:
        return end, None
    if abs(d[1]) < AXIS_TOLERANCE:
        return np.array((end[0], start[1], start[2])), "x"
    if abs(d[0]) < AXIS_TOLERANCE:
        return np.array((start[0], end[1], start[2])), "y"
    return np.array((end[0], end[1], start[2])), None


def perpendicular(a, b):
    return a is not None and b is not None and abs(float(np.dot(a, b))) < PERPENDICULAR


def can_join(a, b):
    """Two wall directions that can make a corner: not (nearly) in line, not too sharp."""
    return a is not None and b is not None and abs(float(a[0] * b[1] - a[1] * b[0])) >= math.sin(MIN_JOIN_ANGLE)


def axis_offset(reference, thickness):
    """How far the axis lies to the left of the drawn line (negative: to the right)."""
    return _REFERENCE_SIDE[reference] * thickness


def offset_axis(start, end, reference, thickness):
    """The wall axis for a line drawn start -> end as `reference` ("axis",
    "left" face or "right" face, seen in the drawing direction)."""
    start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    d = horizontal_dir(start, end)
    if d is None:
        return start, end
    shift = left_normal(d) * axis_offset(reference, thickness)
    return start + shift, end + shift


def axis_crossing(p, d, q, e):
    """Where the horizontal line (p, d) crosses the line (q, e) in plan, at p's level; None if parallel."""
    den = d[0] * e[1] - d[1] * e[0]
    if abs(den) < 1e-12:
        return None
    w = np.asarray(q, dtype=float) - np.asarray(p, dtype=float)
    s = (w[0] * e[1] - w[1] * e[0]) / den
    c = np.asarray(p, dtype=float) + np.asarray(d, dtype=float) * s
    return np.array((c[0], c[1], float(p[2])))


def find_joint(point, direction, axes, thickness=0.0, tol=1e-4):
    """An existing wall the new wall starts or ends on (at any angle from 15°).

    point: the new wall's axis start (or end); direction: its direction.
    axes: [(guid, axis start, axis end, thickness)] of the walls (base level).
    The two axis lines must cross within half a wall thickness of `point`
    (measured along the new wall).
    Returns (guid, where, wall direction, thickness) with where in
    {"start", "end"} (corner) or "mid" (T junction: the new wall only meets
    the face), or None.
    """
    p = np.asarray(point, dtype=float)
    best = None
    for guid, s, e, t_wall in axes:
        s, e = np.asarray(s, dtype=float), np.asarray(e, dtype=float)
        if abs(s[2] - p[2]) > tol:
            continue                          # another level
        d = horizontal_dir(s, e)
        if d is None or not can_join(direction, d):
            continue
        c = axis_crossing(p, direction, s, d)
        sin = abs(float(direction[0] * d[1] - direction[1] * d[0]))
        reach = max(t_wall, thickness) / 2 / sin + tol
        gap = float(np.linalg.norm((c - p)[:2]))
        if gap > reach:
            continue                          # the new wall does not start / end at this wall
        along, length = float((c - s)[:2].dot(d[:2])), float(np.linalg.norm((e - s)[:2]))
        if abs(along) <= reach:
            where = "start"
        elif abs(along - length) <= reach:
            where = "end"
        elif 0 < along < length:
            where = "mid"
        else:
            continue
        key = (where == "mid", gap)
        if best is None or key < best[0]:
            best = (key, (guid, where, d, t_wall))
    return best[1] if best else None


def _toward(ray, other):
    """The side normal of a wall running along `ray` that faces `other`."""
    n = left_normal(ray)
    return n if float(np.dot(n, other)) > 0 else -n


def mitre(c, ray_a, t_a, ray_b, t_b):
    """Mitre corner of two walls whose axes cross at c; ray_a / ray_b point from
    c along each wall. The cut runs from the inside corner to the outside corner
    (both faces meet there; with equal thicknesses it is the bisector).
    Returns (cut_a, cut_b): for each wall the horizontal unit normal of its cut,
    pointing away from that wall's body, or None if the corner is too sharp."""
    c = np.asarray(c, dtype=float)
    na, nb = _toward(ray_a, ray_b), _toward(ray_b, ray_a)
    inner = axis_crossing(c + na * t_a / 2, ray_a, c + nb * t_b / 2, ray_b)
    outer = axis_crossing(c - na * t_a / 2, ray_a, c - nb * t_b / 2, ray_b)
    if inner is None or outer is None:
        return None
    m = horizontal_dir(inner, outer)
    if m is None:
        return None
    n = left_normal(m)
    cut_a = n if float(np.dot(n, ray_a)) < 0 else -n
    cut_b = -cut_a
    for cut, ray in ((cut_a, ray_a), (cut_b, ray_b)):
        if abs(float(np.dot(cut, left_normal(ray)))) > MAX_CUT_TAN * abs(float(np.dot(cut, ray))):
            return None
    return cut_a, cut_b


def face_join(point, direction, at_start, wall_start, wall_end, wall_thickness):
    """A new wall meeting the side of another wall (T junction, any angle): its
    axis stops on that wall's face and its end is cut along the face.
    Returns (new axis point, cut normal pointing away from the new wall's body)."""
    s = np.asarray(wall_start, dtype=float)
    d_wall = horizontal_dir(wall_start, wall_end)
    ray = np.asarray(direction, dtype=float) * (1.0 if at_start else -1.0)   # from the joint along the new wall
    side = _toward(d_wall, ray)
    p = axis_crossing(point, direction, s + side * wall_thickness / 2, d_wall)
    if p is None:
        return np.asarray(point, dtype=float), None
    return p, -side


def cut_angle(normal, x_dir):
    """A cut normal as an angle (degrees) in the wall's own frame (X along the
    wall, Y to its left): 0 = square end, 180 = square start."""
    y_dir = left_normal(x_dir)
    return math.degrees(math.atan2(float(np.dot(normal, y_dir)), float(np.dot(normal, x_dir))))


def is_square(angle, at_start):
    target = 180.0 if at_start else 0.0
    return abs((angle - target + 180.0) % 360.0 - 180.0) < 1e-6


def footprint(length, thickness, start_cut=180.0, end_cut=0.0):
    """Plan of a wall in its own frame (axis from x = 0 to `length`, faces at
    y = ±t/2), with its ends cut at the given angles: 4 points, counter-clockwise."""
    def x_on_cut(x0, angle, y):
        a = math.radians(angle)
        return x0 - math.tan(a) * y if abs(math.cos(a)) > 1e-12 else x0
    h = thickness / 2
    return [(x_on_cut(0.0, start_cut, -h), -h), (x_on_cut(length, end_cut, -h), -h),
            (x_on_cut(length, end_cut, h), h), (x_on_cut(0.0, start_cut, h), h)]


def clear_range(length, thickness, start_cut=180.0, end_cut=0.0):
    """Part of the axis where the wall has its full thickness (for doors and windows)."""
    pts = footprint(length, thickness, start_cut, end_cut)
    return max(pts[0][0], pts[3][0]), min(pts[1][0], pts[2][0])


def joint(through, t_through, through_end, butt, t_butt, butt_end, tol=1e-4, mitred=False):
    """The clean joint of two walls, worked out from their axes alone.

    through / butt: (axis start, axis end) of each wall. `through` is the wall
    that keeps running at a right-angle corner, or the wall met at its side
    (through_end == "path", T junction); `butt` stops against it at its
    butt_end ("start" | "end"). Returns {"through": (point, cut) or None,
    "butt": (point, cut)}: the new axis end point and cut angle (degrees, in
    that wall's own frame) of each joined end; or None if they cannot join
    (in line, too sharp, at different levels, or the T falls off the wall).
    (0.301) mitred: a right-angle corner mitred too, as the other angles are
    (Revit's Wall Joins).
    """
    ts, te = (np.asarray(p, dtype=float) for p in through)
    bs, be = (np.asarray(p, dtype=float) for p in butt)
    dt, db = horizontal_dir(ts, te), horizontal_dir(bs, be)
    if dt is None or db is None or not can_join(dt, db) or abs(ts[2] - bs[2]) > tol:
        return None
    at_start = butt_end == "start"
    p = bs if at_start else be
    c = axis_crossing(p, db, ts, dt)
    if through_end == "path":
        along, length = float((c - ts)[:2].dot(dt[:2])), float(np.linalg.norm((te - ts)[:2]))
        if not tol < along < length - tol:
            return None
        q, cut = face_join(p, db, at_start, ts, te, t_through)
        return {"through": None, "butt": (q, cut_angle(cut, db))}
    if perpendicular(dt, db) and not mitred:
        # the through wall runs past the corner by half the other's thickness; the butt one stops at its face
        out = dt if through_end == "end" else -dt
        return {"through": (c + out * t_butt / 2, 0.0 if through_end == "end" else 180.0),
                "butt": (c + db * t_through / 2 * (1.0 if at_start else -1.0), 180.0 if at_start else 0.0)}
    cuts = mitre(c, -dt if through_end == "end" else dt, t_through, db if at_start else -db, t_butt)
    if cuts is None:
        return None
    return {"through": (c, cut_angle(cuts[0], dt)), "butt": (c, cut_angle(cuts[1], db))}
