"""Placing an element by a point (0.86), as the ArqSynth Modeler's placement keys: which of its section's nine
points — the middle, the corners, the middles of the sides — goes on the point clicked (Space / Shift+Space go
round them), and its quarter turns (R / Shift+R)."""

import math

import numpy as np

# the nine points, in half sizes along the section's own x and y: the middle first, then round from the corner
# at the bottom left (as the numbers on a keypad, from 1)
INSERTION = ((0, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0))
QUARTER = 90


def turn(angle, step):
    """A quarter turn more (step +1) or less (-1), in degrees from 0 to 270."""
    return (int(angle) + step * QUARTER) % 360


def next_insertion(index, step):
    return (int(index) + step) % len(INSERTION)


def axes(angle):
    """The section's own x and y (level unit vectors) turned `angle` degrees from the red axis."""
    a = math.radians(angle)
    return np.array((math.cos(a), math.sin(a), 0.0)), np.array((-math.sin(a), math.cos(a), 0.0))


def place_box(point, width, depth, angle=0, insertion=0):
    """Where a width × depth section goes with its insertion point on `point`: (its middle, its x direction,
    its four corners counter-clockwise from the bottom left)."""
    p = np.asarray(point, dtype=float)
    x, y = axes(angle)
    ox, oy = INSERTION[insertion]
    centre = p - x * ox * width / 2 - y * oy * depth / 2
    corners = [centre + x * sx * width / 2 + y * sy * depth / 2 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    return centre, x, corners
