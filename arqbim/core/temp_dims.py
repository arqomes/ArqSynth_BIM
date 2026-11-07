"""Temporary dimensions (0.61), as Revit's: dimensions shown while drawing (the length and
the angle of what is drawn, the distance from the point it starts from) and on the element
selected (a wall's length and its distances to the walls round it, a door's distances to the
wall ends, a line's length), whose value can be clicked and typed over. Pure numpy: what a
dimension is and the lines it is drawn with.

(0.361) Drawn as the owner's Blender addon draws them (ArqSynth Modeler, «wall_dimensions»): open arrows, the line
dashed (whole while its value is typed over), the extension lines going on past it; a wall's relations to the walls
round it — across to the nearest parallel wall on each side, along beyond each free end to the first wall there —
measured from axis to axis or from face to face (the owner, 2026-11-02: «não aparece a relação da parede com outras
paredes. Gostaria de ter opções de cotas de eixo a eixo, e de face a face»).

(0.372) As the addon draws them now (its «wall_dimensions» v3.5 and the owner's picture): the lines whole (dim_segments
still dashes them when asked), light blue, each value on a dark box laid on its line (render/viewport.show_temp_dims).
"""

import math
from dataclasses import dataclass

import numpy as np

GAP_PX = 3           # gap between what is measured and an extension line
OFFSET_PX = 22       # a dimension is drawn this far to the side of what it measures
OVER_PX = 9          # (0.361) an extension line goes on this far past the dimension line
ARROW_PX = 9        # an open arrow's length…
WING_PX = 3.5        # …and half its width
DASH_PX = (8.0, 5.0)  # the line's dash and gap (as the addon's), while not typed over
PARALLEL = math.cos(math.radians(1.0))   # (0.361) walls within 1° of each other are parallel
TOUCH = 1e-3         # walls closer than this touch (joined): no relation between them
SAME_FLOOR = 1.0     # walls whose bases are this close are on the same floor
ACROSS_AT = 0.2      # the relations across a wall are measured this far along the overlap (its length's value is in
#                      the middle)
# (0.446) how they look — the owner, with Revit's pictures: «quero ter essa experiência no desenho como a do revit»:
# "revit": thin lines with a small oblique cross on each end, the value beside the line on its far side (no box), the
# angle a wide arc from a grey reference line, crossed at its ends; "addon": as 0.372 (open arrows, the value on a box)
LOOK = {"name": "revit"}
TICK_PX = 5.0        # (0.446) half a cross's stroke
TEXT_GAP_PX = 3.0    # (0.446) between a dimension's line and its value
REF_OVER = 1.45      # (0.446) an angle's reference line goes on this far past its arc (in radii)


def revit():
    """(0.446) Are they drawn as Revit's?"""
    return LOOK["name"] == "revit"


def _cross(p, d, n, size):
    """The two strokes of a small oblique cross at p (Revit's tick): along d ± n, `size` from p each way."""
    u, v = (d + n) / math.sqrt(2.0), (d - n) / math.sqrt(2.0)
    return [(p - u * size, p + u * size), (p - v * size, p + v * size)]


@dataclass
class TempDim:
    a: np.ndarray                 # measured from…
    b: np.ndarray                 # …to (world)
    normal: np.ndarray            # the plane it is drawn in: its offset is across a-b in that plane
    side: float = 1.0             # +1: drawn to the left of a→b (seen against the normal), -1: to the right
    key: object = None            # what typing a value over it changes (None: only shown)
    offset_px: float = OFFSET_PX
    kind: str = "measure"         # (0.361) "measure": the element's own; "relation": to another element;
    #                               (0.386) "label": its value's box alone, laid along a→b at its middle — no lines
    shown: float = None           # (0.386) the value written (default: the length a→b)

    @property
    def value(self):
        if self.shown is not None:
            return float(self.shown)
        return float(np.linalg.norm(np.asarray(self.b, dtype=float) - np.asarray(self.a, dtype=float)))


@dataclass
class Relation:
    """(0.361) A wall's relation to another wall: from a (on this one) to b (on the other)."""
    kind: str                     # "side": across, to the nearest parallel wall on that side; "end": beyond an end
    which: int                    # side: +1 left / -1 right of start→end; end: 0 its start, 1 its end
    a: np.ndarray
    b: np.ndarray
    other: object                 # the other wall (its id)

    @property
    def value(self):
        return float(np.linalg.norm(self.b - self.a))


@dataclass
class TempAngle:
    center: np.ndarray            # the angle's vertex
    start: np.ndarray             # unit direction it is measured from (the red axis…)
    degrees: float                # counter-clockwise about `normal`
    normal: np.ndarray
    radius_px: float = 42


def _unit(v):
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else None


def across(a, b, normal):
    """Unit vector in the plane (normal), across a→b to its left; None if a = b."""
    d = _unit(np.asarray(b, dtype=float) - np.asarray(a, dtype=float))
    if d is None:
        return None
    side = _unit(np.cross(normal, d))
    if side is None:                                      # a→b along the normal: any perpendicular
        side = _unit(np.cross(d, (1.0, 0.0, 0.0))) if abs(d[0]) < 0.9 else _unit(np.cross(d, (0.0, 1.0, 0.0)))
    return side


def dim_segments(dim, world_per_px, dashed=False):
    """World segments [(p, q)] of a dimension — its line (dashed: in dashes), an open arrow on each end (outside
    when it is too short for them), the extension lines past it (none for a relation, drawn on what it measures)
    — and where its value goes (the middle of its line). `world_per_px`: metres per screen pixel there."""
    a, b = np.asarray(dim.a, dtype=float), np.asarray(dim.b, dtype=float)
    if dim.kind == "label":                              # (0.386) the box alone, at the middle of a→b
        return [], (a + b) / 2
    n = across(a, b, np.asarray(dim.normal, dtype=float))
    if n is None:
        return [], a
    length = float(np.linalg.norm(b - a))
    d = (b - a) / length
    n = n * (1.0 if dim.side >= 0 else -1.0)
    px = world_per_px
    off = dim.offset_px * px
    l1, l2 = a + n * off, b + n * off
    segs = []
    if dashed and length > (DASH_PX[0] + DASH_PX[1]) * px:
        step, on = (DASH_PX[0] + DASH_PX[1]) * px, DASH_PX[0] * px
        for t0 in np.arange(0.0, length, step):
            segs.append((l1 + d * t0, l1 + d * min(t0 + on, length)))
    else:
        segs.append((l1, l2))
    if revit():                                          # (0.446) a cross on each end, the value beside the line
        segs += _cross(l1, d, n, TICK_PX * px) + _cross(l2, d, n, TICK_PX * px)
        if abs(dim.offset_px) > 1e-9:
            gap, over = GAP_PX * px, OVER_PX * px
            segs += [(a + n * gap, l1 + n * over), (b + n * gap, l2 + n * over)]
        return segs, (l1 + l2) / 2
    arrow, wing = ARROW_PX * px, WING_PX * px
    inside = length > 2.5 * arrow
    for end, back in ((l1, d), (l2, -d)):              # back: from the end into the line
        if not inside:
            back = -back                                 # (outside, pointing in, on a short leader)
            segs.append((end, end + back * arrow * 1.8))
        segs += [(end, end + back * arrow + n * wing), (end, end + back * arrow - n * wing)]
    if abs(dim.offset_px) > 1e-9:                      # (a relation, drawn on what it measures: its arrows only)
        gap, over = GAP_PX * px, OVER_PX * px
        segs += [(a + n * gap, l1 + n * over), (b + n * gap, l2 + n * over)]
    return segs, (l1 + l2) / 2


def arc_segments(angle, world_per_px, steps=None):
    """World segments of an angle's arc (from its start direction, about its normal) and where
    its value goes (beyond the middle of the arc)."""
    c, s0, n = (np.asarray(v, dtype=float) for v in (angle.center, angle.start, angle.normal))
    r = angle.radius_px * world_per_px
    s1 = np.cross(n, s0)
    steps = steps or max(4, int(abs(angle.degrees) / (3 if revit() else 6)))
    pts = [c + r * (math.cos(math.radians(a)) * s0 + math.sin(math.radians(a)) * s1)
           for a in np.linspace(0.0, angle.degrees, steps + 1)]
    mid = math.radians(angle.degrees / 2)
    out = math.cos(mid) * s0 + math.sin(mid) * s1
    if revit():                                          # (0.446) the reference line well past the arc, a cross on
        end = math.radians(angle.degrees)               # each of the arc's ends; the value just outside its middle
        d1 = math.cos(end) * s0 + math.sin(end) * s1
        crosses = _cross(pts[0], s0, s1, TICK_PX * world_per_px) + _cross(pts[-1], d1, np.cross(n, d1),
                                                                          TICK_PX * world_per_px)
        return [(c, c + s0 * r * REF_OVER)] + list(zip(pts, pts[1:])) + crosses, \
            c + out * (r + 12.0 * world_per_px)
    segs = [(c, c + s0 * r * 1.25)] + list(zip(pts, pts[1:]))
    label = c + r * 1.35 * out
    return segs, label


def level_angle(a, b):
    """The angle (degrees, 0…360) of a→b from the red axis, counter-clockwise seen from above."""
    d = np.asarray(b, dtype=float) - np.asarray(a, dtype=float)
    return math.degrees(math.atan2(d[1], d[0])) % 360.0


def neighbour_walls(axis, others, max_distance=50.0):
    """The walls beside a straight wall, the nearest on each side: [(side +1 left / -1 right, signed
    distance between the axes, a point of this axis, its foot on the other)] for the parallel walls
    whose axes overlap it along its length (measured in the middle of the overlap).
    axis: (start, end); others: [(start, end)]."""
    s, e = (np.asarray(p, dtype=float) for p in axis)
    d = _unit((e - s) * (1, 1, 0))
    if d is None:
        return []
    left = np.array((-d[1], d[0], 0.0))
    length = float(np.linalg.norm((e - s)[:2]))
    best = {}
    for os_, oe in others:
        os_, oe = np.asarray(os_, dtype=float), np.asarray(oe, dtype=float)
        od = _unit((oe - os_) * (1, 1, 0))
        if od is None or abs(float(od @ d)) < 1 - 1e-6:
            continue                                         # not parallel
        dist = float((os_ - s) @ left)
        if abs(dist) < 1e-6 or abs(dist) > max_distance:
            continue                                         # in line with it, or too far
        t0, t1 = sorted((float((os_ - s) @ d), float((oe - s) @ d)))
        if t1 <= 1e-6 or t0 >= length - 1e-6:
            continue                                         # not beside it
        side = 1 if dist > 0 else -1
        if side not in best or abs(dist) < abs(best[side][1]):
            p = s + d * (max(0.0, t0) + min(length, t1)) / 2
            best[side] = (side, dist, p, p + left * dist)
    return [best[k] for k in sorted(best, reverse=True)]


def _cross2(u, v):
    return float(u[0] * v[1] - u[1] * v[0])


def _beyond(end, out, half, os_, oe, ohalf):
    """How far the wall whose axis ends at `end` (going on along `out`, half as thick as `half`) would go before
    it meets the wall os_→oe (half as thick as `ohalf`): (to its axis, to its near face), or None if it does not —
    behind the end, beside its way, or (parallel) not in line with it."""
    w = (oe - os_)[:2]
    olen = float(np.linalg.norm(w))
    if olen < 1e-9:
        return None
    sin = _cross2(out, w / olen)
    if abs(sin) < math.sin(math.acos(PARALLEL)):          # parallel: only a wall in line with it
        offset = abs(_cross2(out, (os_ - end)[:2]))
        if offset > max(TOUCH, min(half, ohalf)):
            return None
        near, far = sorted((float((os_ - end)[:2] @ out[:2]), float((oe - end)[:2] @ out[:2])))
        if far < -TOUCH:
            return None
        return near, near                                  # (end to end: the same from the axes or the faces)
    rel = (os_ - end)[:2]
    v = _cross2(rel, w) / _cross2(out[:2], w)              # along out, to the other's axis line
    u = _cross2(rel, out[:2]) / _cross2(out[:2], w)        # where on the other's axis (0…1)
    reach = (half + ohalf) / olen / abs(sin)
    if not -reach <= u <= 1.0 + reach:
        return None
    face = v - ohalf / abs(sin)
    if v < -ohalf / abs(sin) - TOUCH:                      # (the end goes through it: behind)
        return None
    return v, face


def wall_relations(axis, thickness, others, faces=False, max_distance=50.0):
    """(0.361) A straight wall's relations to the walls round it: [Relation] —
    - across: the nearest parallel wall on each side whose length overlaps it (measured at ACROSS_AT of the overlap);
    - along: beyond each end that is free, the first wall it would meet (one across its way, or one in line with it).
    faces: from face to face (the clear distance), else from axis to axis. Walls touching it (joined) are no
    relation. axis: (start, end); others: [(id, start, end, thickness)] (on the same floor)."""
    s, e = (np.asarray(p, dtype=float) for p in axis)
    d = _unit((e - s) * (1, 1, 0))
    if d is None:
        return []
    left = np.array((-d[1], d[0], 0.0))
    length = float(np.linalg.norm((e - s)[:2]))
    half = thickness / 2.0
    sides, ends = {}, {}
    for other, os_, oe, ot in others:
        os_, oe = np.array(os_, dtype=float), np.array(oe, dtype=float)
        os_[2] = oe[2] = s[2]
        od = _unit((oe - os_) * (1, 1, 0))
        if od is None:
            continue
        ohalf = ot / 2.0
        for which, end, out in ((0, s, -d), (1, e, d)):
            hit = _beyond(end, out, half, os_, oe, ohalf)
            if hit is not None and hit[0] <= max_distance and (which not in ends or hit[1] < ends[which][1]):
                ends[which] = (hit[0], hit[1], other)
        if abs(float(od @ d)) < PARALLEL:
            continue
        dist = float((os_ - s) @ left)                     # axis to axis, + on the left
        if abs(dist) - half - ohalf <= TOUCH or abs(dist) > max_distance:
            continue                                       # in line with it, against it, or too far
        t0, t1 = sorted((float((os_ - s) @ d), float((oe - s) @ d)))
        lo, hi = max(0.0, t0), min(length, t1)
        if hi - lo <= 1e-6:
            continue                                       # not beside it
        side = 1 if dist > 0 else -1
        if side not in sides or abs(dist) < abs(sides[side][0]):
            sides[side] = (dist, lo + (hi - lo) * ACROSS_AT, ohalf, other)
    out = []
    for side in sorted(sides, reverse=True):
        dist, at, ohalf, other = sides[side]
        p = s + d * at
        if faces:
            out.append(Relation("side", side, p + left * side * half, p + left * (dist - side * ohalf), other))
        else:
            out.append(Relation("side", side, p, p + left * dist, other))
    for which in sorted(ends):
        to_axis, to_face, other = ends[which]
        if to_face <= TOUCH:
            continue                                       # (the nearest touches it: joined there)
        end, way = (s, -d) if which == 0 else (e, d)
        out.append(Relation("end", which, end.copy(), end + way * (to_face if faces else to_axis), other))
    return out
