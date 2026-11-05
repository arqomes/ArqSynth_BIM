"""Columns from a CAD plan (0.211, Phase 8, step 1: «pilares (retângulos e círculos fechados)»): a column drawn as a
closed rectangle — four corners at right angles, its opposite sides alike — or as a circle, of a column's size
(MIN_SIDE to MAX_SIDE across): its middle, the way its section is turned (the rectangle's first side) and its size.

Pure numpy: plan points in metres. What is made of them is model/bim's."""

import math

import numpy as np

MIN_SIDE, MAX_SIDE = 0.12, 1.20             # m: a column's side (a circle's diameter), drawn
SQUARE = math.cos(math.radians(88.0))       # a corner this near a right angle is one
ALIKE = 0.01                                 # m: a rectangle's opposite sides differ by this at most
SAME = 0.02                                  # m: two middles this near: one column (drawn twice, or a hatch's outline)


def rectangle(points):
    """(centre (2,), its first side's way (2,), width along it, depth across) of a closed outline that is a
    rectangle — or None."""
    p = np.asarray(points, dtype=float).reshape(-1, 2)
    if len(p) == 5 and float(np.linalg.norm(p[0] - p[-1])) < 1e-9:
        p = p[:-1]                                   # (its first corner repeated at the end)
    if len(p) != 4:
        return None
    sides = np.roll(p, -1, axis=0) - p
    lengths = np.linalg.norm(sides, axis=1)
    if float(lengths.min()) < 1e-9:
        return None
    way = sides / lengths[:, None]
    if any(abs(float(way[k] @ way[(k + 1) % 4])) > SQUARE for k in range(4)):
        return None
    if abs(lengths[0] - lengths[2]) > ALIKE or abs(lengths[1] - lengths[3]) > ALIKE:
        return None
    return p.mean(axis=0), way[0], float(lengths[0] + lengths[2]) / 2, float(lengths[1] + lengths[3]) / 2


def columns(polygons, circles, min_side=MIN_SIDE, max_side=MAX_SIDE):
    """The columns of a plan's closed outlines and circles: [(centre (2,), x way (2,), width, depth, round)] — the
    rectangles and circles of a column's size, each middle once."""
    found = []
    for points in polygons:
        r = rectangle(points)
        if r is None:
            continue
        centre, way, width, depth = r
        if min(width, depth) >= min_side - 1e-6 and max(width, depth) <= max_side + 1e-6:
            found.append((centre, way, width, depth, False))
    for centre, radius in circles:
        diameter = 2.0 * float(radius)
        if min_side - 1e-6 <= diameter <= max_side + 1e-6:
            found.append((np.asarray(centre, dtype=float)[:2], np.array((1.0, 0.0)), diameter, diameter, True))
    kept = []
    for column in found:
        if all(float(np.linalg.norm(column[0] - other[0])) > SAME for other in kept):
            kept.append(column)
    return kept


def outline(column, segments=24):
    """A column's outline in plan, to show it: its corners, or its circle as `segments` points."""
    centre, way, width, depth, round_ = column
    if round_:
        return [centre + width / 2 * np.array((math.cos(a), math.sin(a)))
                for a in np.linspace(0.0, 2 * math.pi, segments, endpoint=False)]
    across = np.array((-way[1], way[0]))
    return [centre + way * sx * width / 2 + across * sy * depth / 2 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
