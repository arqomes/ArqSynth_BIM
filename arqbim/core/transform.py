"""Move and Rotate (SketchUp 'M' and 'Q'): the transformation matrices. Pure numpy.

Rotations are about a vertical axis only: walls, slabs and columns stay upright
(an IFC wall must keep its Z axis up), and plans rotate as on the drawing board.
"""

import math

import numpy as np

ANGLE_STEP = 15.0          # the protractor snaps to multiples of 15°...
ANGLE_SNAP = 2.0           # ...when the mouse is within 2° of one


def translation(v):
    m = np.eye(4)
    m[:3, 3] = np.asarray(v, dtype=float)
    return m


def rotation_about_z(center, degrees):
    """Rotation by `degrees` (counter-clockwise seen from above) about the vertical line through `center`."""
    a = math.radians(degrees)
    r = np.eye(4)
    r[0, 0], r[0, 1], r[1, 0], r[1, 1] = math.cos(a), -math.sin(a), math.sin(a), math.cos(a)
    c = np.asarray(center, dtype=float)
    return translation(c) @ r @ translation(-c)


def plan_angle(u, v):
    """Signed angle in degrees from direction u to direction v, seen from above (counter-clockwise > 0)."""
    return math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]))


def snap_angle(degrees, step=ANGLE_STEP, tolerance=ANGLE_SNAP):
    """(angle, snapped): the nearest multiple of `step` when within `tolerance`."""
    nearest = round(degrees / step) * step
    if abs(degrees - nearest) <= tolerance:
        return float(nearest), True
    return float(degrees), False


def transform_segments(segments, matrix):
    """(N, 3) points (segment ends) moved by a 4x4 matrix."""
    pts = np.asarray(segments, dtype=float).reshape(-1, 3)
    m = np.asarray(matrix, dtype=float)
    return pts @ m[:3, :3].T + m[:3, 3]
