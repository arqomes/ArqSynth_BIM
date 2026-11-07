"""Arcs and circles in plan (0.103: curved walls). Pure geometry.

An arc is (centre, radius, start, sweep): from the angle `start` (radians, from the red axis) turning `sweep`
(positive: counter-clockwise; ±2π: a whole circle)."""

import math

import numpy as np

FULL = 2 * math.pi
SEGMENT_DEG = 3.0          # a curve drawn on the screen (or for the rooms): a point every 3°


def _xy(p):
    return np.array((float(p[0]), float(p[1])))


def is_full(sweep):
    return abs(abs(sweep) - FULL) < 1e-9


def arc_through(a, b, p):
    """The arc from a to b passing through p (plan points): (centre, radius, start, sweep), or None when the
    three are in a line."""
    a, b, p = _xy(a), _xy(b), _xy(p)
    d = 2 * (a[0] * (b[1] - p[1]) + b[0] * (p[1] - a[1]) + p[0] * (a[1] - b[1]))
    if abs(d) < 1e-9 * max(1.0, float(np.linalg.norm(b - a)) ** 2):
        return None
    sa, sb, sp = a @ a, b @ b, p @ p
    c = np.array(((sa * (b[1] - p[1]) + sb * (p[1] - a[1]) + sp * (a[1] - b[1])) / d,
                  (sa * (p[0] - b[0]) + sb * (a[0] - p[0]) + sp * (b[0] - a[0])) / d))
    r = float(np.linalg.norm(a - c))
    start = math.atan2(a[1] - c[1], a[0] - c[0])
    end = math.atan2(b[1] - c[1], b[0] - c[0])
    through = math.atan2(p[1] - c[1], p[0] - c[0])
    ccw = (end - start) % FULL
    if (through - start) % FULL < ccw:
        return c, r, start, ccw
    return c, r, start, -(FULL - ccw)


def arc_with_radius(a, b, radius, side):
    """The arc from a to b of this radius (at least half the chord) bulging towards the point `side`; the
    shorter one. (centre, radius, start, sweep) or None."""
    a, b, side = _xy(a), _xy(b), _xy(side)
    chord = b - a
    length = float(np.linalg.norm(chord))
    if length < 1e-9 or radius < length / 2 - 1e-9:
        return None
    mid = (a + b) / 2
    n = np.array((-chord[1], chord[0])) / length                        # left of a -> b
    bulge_left = float((side - mid) @ n) > 0
    h = math.sqrt(max(radius ** 2 - (length / 2) ** 2, 0.0))
    centre = mid - n * h if bulge_left else mid + n * h                 # (the centre on the other side)
    sag = radius - h
    through = mid + n * sag if bulge_left else mid - n * sag
    return arc_through(a, b, through)


def arc_tangent(a, direction, b):
    """(0.454) Revit's «Tangent End Arc»: the arc from a, leaving it along `direction` (plan), to b —
    (centre, radius, start, sweep), or None when b is straight ahead or behind (no arc turns there)."""
    a, b, d = _xy(a), _xy(b), _xy(direction)
    n = float(np.linalg.norm(d))
    if n < 1e-12:
        return None
    d = d / n
    left = np.array((-d[1], d[0]))
    v = b - a
    across = float(v @ left)                                    # how far b lies to the left of the way out
    if abs(across) < 1e-6 * max(1.0, float(np.linalg.norm(v))):
        return None
    signed = float(v @ v) / (2 * across)                        # the centre: that far to the left of a
    centre = a + left * signed
    start = math.atan2(a[1] - centre[1], a[0] - centre[0])
    end = math.atan2(b[1] - centre[1], b[0] - centre[0])
    sweep = (end - start) % FULL if signed > 0 else -((start - end) % FULL)   # (to the left: counter-clockwise)
    return centre, abs(signed), start, sweep


def arc_from_centre(centre, a, b, turn):
    """(0.454) Revit's «Center-ends Arc»: about `centre`, from a (its radius) to the direction of b, turning
    counter-clockwise when `turn` > 0, clockwise otherwise — (centre, radius, start, sweep), or None."""
    c, a, b = _xy(centre), _xy(a), _xy(b)
    radius = float(np.linalg.norm(a - c))
    if radius < 1e-9 or float(np.linalg.norm(b - c)) < 1e-9:
        return None
    start = math.atan2(a[1] - c[1], a[0] - c[0])
    end = math.atan2(b[1] - c[1], b[0] - c[0])
    sweep = (end - start) % FULL if turn > 0 else -((start - end) % FULL)
    if abs(sweep) < 1e-6:
        return None
    return c, radius, start, sweep


def turn_of(centre, a, b):
    """(0.454) Which way a turns towards b about the centre by the shorter way: +1 counter-clockwise, -1 not."""
    c, a, b = _xy(centre), _xy(a), _xy(b)
    u, v = a - c, b - c
    return 1 if float(u[0] * v[1] - u[1] * v[0]) >= 0 else -1


def along(angle, sweep):
    """(0.454) The unit direction (plan) the arc goes at `angle`, following its sweep."""
    return np.array((-math.sin(angle), math.cos(angle))) * (1.0 if sweep >= 0 else -1.0)


def point_at(centre, radius, angle):
    return np.array((centre[0] + radius * math.cos(angle), centre[1] + radius * math.sin(angle)))


def arc_points(centre, radius, start, sweep, step_deg=SEGMENT_DEG):
    """Points along the arc, both ends included (a whole circle: without repeating the first)."""
    n = max(int(math.ceil(abs(math.degrees(sweep)) / step_deg)), 2)
    if is_full(sweep):
        return [point_at(centre, radius, start + sweep * k / n) for k in range(n)]
    return [point_at(centre, radius, start + sweep * k / n) for k in range(n + 1)]


def band(centre, radius, start, sweep, thickness, step_deg=SEGMENT_DEG):
    """A curved wall's plan as polygons [(x, y)…] (a whole circle: two halves, as a ring has a hole)."""
    if is_full(sweep):
        half = math.copysign(math.pi, sweep)
        return band(centre, radius, start, half, thickness, step_deg) + \
            band(centre, radius, start + half, half, thickness, step_deg)
    outer = arc_points(centre, radius + thickness / 2, start, sweep, step_deg)
    inner = arc_points(centre, radius - thickness / 2, start, sweep, step_deg)
    return [[tuple(p) for p in outer + inner[::-1]]]


def axis_radius(drawn, sweep, reference, thickness):
    """The axis radius of a curved wall drawn as `reference` ("axis" / "left" / "right" face, seen along the
    arc): turning counter-clockwise, its left is towards the centre."""
    side = {"axis": 0.0, "left": 0.5, "right": -0.5}[reference] * thickness
    return drawn + side if sweep > 0 else drawn - side


# ------------------------------------------------------------ doors and windows in a curved wall (0.177)

def tangent_frame(centre, radius, angle):
    """4x4 at the axis point at `angle` (on the level of centre's z): x along the arc counter-clockwise, y towards
    the centre, z up — the frame a door or window of a curved wall is placed in, as in a straight wall's."""
    c, s = math.cos(angle), math.sin(angle)
    m = np.eye(4)
    m[:3, 0] = (-s, c, 0.0)
    m[:3, 1] = (-c, -s, 0.0)
    m[:3, 3] = (float(centre[0]) + radius * c, float(centre[1]) + radius * s, float(centre[2]))
    return m


def opening_depth(radius, thickness, width, margin=0.01):
    """(y_lo, y_hi) in the tangent frame at an opening's middle: the box an opening `width` wide cuts to go right
    through the wall — from just outside its outer face to just beyond its inner face at the opening's edges, where
    the arc has turned in (the chord's sagitta) —, or None when the inner face is too tight for it."""
    inner, half = radius - thickness / 2, width / 2
    if inner <= half + 1e-6:
        return None
    return (-thickness / 2 - margin, radius - math.sqrt(inner * inner - half * half) + margin)


def angle_along(start, sweep, radius, along):
    """The angle of the axis point `along` m from the arc's start, following it."""
    return start + math.copysign(along / radius, sweep if sweep else 1.0)


def along_at(start, sweep, radius, angle):
    """How far along the arc (m from its start, following it) the angle is — beyond its ends: the nearer end."""
    turn = ((angle - start) * (1.0 if sweep >= 0 else -1.0)) % FULL
    if is_full(sweep) or turn <= abs(sweep):
        return turn * radius
    return abs(sweep) * radius if turn - abs(sweep) < FULL - turn else 0.0


def opening_along(start, sweep, radius, width, angle, clearance=0.05, step=0.01):
    """The middle of an opening `width` wide (m along the arc from its start) nearest `angle`, rounded to the
    centimetre and kept `clearance` from the arc's ends — or None when the arc is too short for it."""
    length = radius * abs(sweep)
    t = round(along_at(start, sweep, radius, angle) / step) * step
    if is_full(sweep):
        return t % length
    lo, hi = width / 2 + clearance, length - width / 2 - clearance
    if hi < lo - 1e-9:
        return None
    return float(min(max(t, lo), hi))
