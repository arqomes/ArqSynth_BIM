"""(0.452) Revit's «Fillet Arc» (the owner: «o arco por seleção de 2 elementos»): the arc of a radius tangent to two
straight lines — two walls' axes, two lines — on the side of each where it was picked; where it touches each (the end
of each to bring there), its centre, its start and its sweep. Pure numpy, in the plan."""

import math
from dataclasses import dataclass

import numpy as np

MIN_ANGLE = math.radians(2.0)      # lines nearer to parallel than this (or to a straight line on): no fillet


@dataclass
class Fillet:
    cross: np.ndarray        # where the two lines meet (x, y)
    ends: tuple              # ("start" | "end", …): the end of each segment on the crossing's side
    tangents: tuple          # (x, y) where the arc touches each line
    centre: np.ndarray       # (x, y)
    radius: float
    start: float             # radians: the arc from its first tangent point…
    sweep: float             # …turning this much (counter-clockwise if positive) to the second
    room: tuple              # how far each tangent point may go from the crossing (each segment's kept length)


def _unit(v):
    v = np.asarray(v, dtype=float)[:2]
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else None


def crossing(a, b, c, d):
    """Where the lines a→b and c→d cross (plan), or None (parallel)."""
    a, b, c, d = (np.asarray(p, dtype=float)[:2] for p in (a, b, c, d))
    r, s = b - a, d - c
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-12:
        return None
    w = c - a
    return a + r * ((w[0] * s[1] - w[1] * s[0]) / den)


def fillet(first, keep_first, second, keep_second, radius=None, through=None):
    """The fillet of the segments `first` = (a, b) and `second`, each kept on the side of its `keep` point (where it was
    picked): of `radius`, or — None — through `through` (the point the mouse is at: its distance from the crossing
    along the bisector). None when they are parallel, in a line, or the radius is not one."""
    x = crossing(*first, *second)
    if x is None:
        return None
    ways, ends, room = [], [], []
    for (a, b), keep in ((first, keep_first), (second, keep_second)):
        a, b = np.asarray(a, dtype=float)[:2], np.asarray(b, dtype=float)[:2]
        d = _unit(b - a)
        if d is None:
            return None
        at = float((x - a) @ d)                              # (the crossing along it, from a)
        kept = float((np.asarray(keep, dtype=float)[:2] - a) @ d)
        if kept < at:                                         # (kept before the crossing: its end moves there)
            ways.append(-d)
            ends.append("end")
            room.append(at)                                   # (from the crossing back to its start)
        else:
            ways.append(d)
            ends.append("start")
            room.append(float(np.linalg.norm(b - a)) - at)
    u, v = ways
    angle = math.acos(max(-1.0, min(1.0, float(u @ v))))
    if angle < MIN_ANGLE or math.pi - angle < MIN_ANGLE:
        return None
    half = angle / 2.0
    bisector = _unit(u + v)
    if radius is None:
        if through is None:
            return None
        s = float((np.asarray(through, dtype=float)[:2] - x) @ bisector)     # (the arc's middle that far out)
        k = 1.0 / math.sin(half) - 1.0
        radius = s / k if k > 1e-9 else 0.0
    if radius is None or radius <= 1e-6:
        return None
    reach = radius / math.tan(half)
    tangents = (x + u * reach, x + v * reach)
    centre = x + bisector * (radius / math.sin(half))
    start = math.atan2(*(tangents[0] - centre)[::-1])
    end = math.atan2(*(tangents[1] - centre)[::-1])
    sweep = (end - start + math.pi) % (2.0 * math.pi) - math.pi          # (the short way round)
    return Fillet(x, tuple(ends), tangents, centre, float(radius), start, sweep, tuple(room))


def arc_points(f, step_deg=6.0):
    """The fillet's arc as points (N, 2), from its first tangent point to its second."""
    n = max(2, int(math.ceil(abs(math.degrees(f.sweep)) / step_deg)))
    angles = f.start + np.linspace(0.0, f.sweep, n + 1)
    return f.centre + f.radius * np.column_stack((np.cos(angles), np.sin(angles)))
