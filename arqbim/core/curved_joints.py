"""Corners with curved walls (0.189): a straight wall and a curved one, or two curved ones, joined end to end —
worked out from their axes alone. Pure numpy.

A wall's end as it meets the other (End): a straight wall's — its axis end, the way into its body from there
(`ray`), its thickness; a curved wall's — the centre and radius of its axis too: its faces are then two circles,
not two lines.

The corner is a mitre made exact: the line through the point where the two inner faces meet and the point where
the two outer faces meet (an arc's face met where it truly is, not along its tangent) cuts both walls. Each one's
axis end goes to where its axis crosses that line, its end cut along it: the two bodies share that edge, with no gap
and no overlap. Ends in line (an arc going on from a straight wall along its tangent) already meet squarely: they
are not joined."""

import math
from dataclasses import dataclass

import numpy as np

from .walls import MAX_CUT_TAN, can_join, cut_angle, horizontal_dir, left_normal

NEAR = 3.0      # × the thicker wall: farther from the corner, the faces "meeting" is not a corner


@dataclass
class End:
    point: np.ndarray           # the axis end (x, y, z)
    ray: np.ndarray             # horizontal unit vector, from the end into the wall's body
    thickness: float
    centre: np.ndarray = None   # a curved wall's: its axis circle (x, y), radius
    radius: float = None

    @property
    def curved(self):
        return self.centre is not None


def straight_end(point, ray, thickness):
    return End(np.asarray(point, dtype=float), np.asarray(ray, dtype=float), float(thickness))


def arc_end(centre, radius, angle, turn, thickness, z=0.0):
    """A curved wall's end: its axis round `centre` of `radius`, the end at `angle` (radians); turn +1 when its body
    goes on counter-clockwise from there, -1 clockwise."""
    c, s = math.cos(angle), math.sin(angle)
    point = np.array((centre[0] + radius * c, centre[1] + radius * s, z))
    ray = np.array((-s, c, 0.0)) * (1.0 if turn > 0 else -1.0)
    return End(point, ray, float(thickness), np.array((float(centre[0]), float(centre[1]))), float(radius))


def _toward(ray, other):
    n = left_normal(ray)
    return n if float(np.dot(n, other)) > 0 else -n


def _face(end, n):
    """The face of the wall on the side `n` (horizontal unit vector, across it at its end): ("line", point,
    direction) or ("circle", centre, radius)."""
    if not end.curved:
        return ("line", (end.point + n * end.thickness / 2)[:2], end.ray[:2])
    radial = (end.point[:2] - end.centre) / end.radius
    outward = float(np.dot(n[:2], radial)) > 0
    return ("circle", end.centre, end.radius + (end.thickness / 2 if outward else -end.thickness / 2))


def _line_circle(p, d, c, r):
    """The points where the line p + s·d (d a unit vector) crosses the circle (c, r)."""
    w = p - c
    b = float(np.dot(d, w))
    disc = b * b - (float(np.dot(w, w)) - r * r)
    if disc < 0:
        return []
    root = math.sqrt(disc)
    return [p + d * (-b - root), p + d * (-b + root)]


def _circle_circle(c1, r1, c2, r2):
    d = float(np.linalg.norm(c2 - c1))
    if d < 1e-12 or d > r1 + r2 + 1e-12 or d < abs(r1 - r2) - 1e-12:
        return []
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(max(r1 * r1 - a * a, 0.0))
    u = (c2 - c1) / d
    m = c1 + u * a
    v = np.array((-u[1], u[0]))
    return [m + v * h, m - v * h]


def _meet(f, g, near):
    """Where two faces (lines / circles) cross, nearest `near` (x, y); None if they do not."""
    if f[0] == "line" and g[0] == "line":
        p, d, q, e = f[1], f[2], g[1], g[2]
        den = d[0] * e[1] - d[1] * e[0]
        if abs(den) < 1e-12:
            return None
        w = q - p
        points = [p + d * ((w[0] * e[1] - w[1] * e[0]) / den)]
    elif f[0] == "circle" and g[0] == "circle":
        points = _circle_circle(f[1], f[2], g[1], g[2])
    else:
        line, circle = (f, g) if f[0] == "line" else (g, f)
        points = _line_circle(line[1], line[2], circle[1], circle[2])
    if not points:
        return None
    return min(points, key=lambda q: float(np.linalg.norm(q - near)))


def _axis_on(end, q, m):
    """Where the wall's axis crosses the line through q along m, nearest its end (x, y); None if it does not."""
    axis = ("circle", end.centre, end.radius) if end.curved else ("line", end.point[:2], end.ray[:2])
    return _meet(axis, ("line", q, m), end.point[:2])


def _tangent(end, p):
    """The way into the wall's body at its axis point p (x, y): its ray, or along its arc there."""
    if not end.curved:
        return end.ray[:2]
    radial = (p - end.centre) / np.linalg.norm(p - end.centre)
    t = np.array((-radial[1], radial[0]))
    return t if float(np.dot(t, end.ray[:2])) > 0 else -t


def corner(a, b):
    """The exact mitre of two wall ends meeting (their axis ends at about the same place): [(new axis end (x, y,
    z), cut normal — horizontal, pointing away from that wall's body)] for a and for b; or None when they cannot be
    joined (in line, too sharp, their faces not meeting near the corner)."""
    if not can_join(a.ray, b.ray):
        return None
    c = (a.point[:2] + b.point[:2]) / 2
    na, nb = _toward(a.ray, b.ray), _toward(b.ray, a.ray)
    q_in = _meet(_face(a, na), _face(b, nb), c)
    q_out = _meet(_face(a, -na), _face(b, -nb), c)
    reach = NEAR * max(a.thickness, b.thickness)
    if q_in is None or q_out is None or max(np.linalg.norm(q_in - c), np.linalg.norm(q_out - c)) > reach:
        return None
    m = horizontal_dir(np.append(q_in, 0.0), np.append(q_out, 0.0))
    if m is None:
        return None
    m = m[:2]
    n = np.array((-m[1], m[0]))
    out = []
    for end in (a, b):
        p = _axis_on(end, q_in, m)
        if p is None or np.linalg.norm(p - end.point[:2]) > reach:
            return None
        ray = _tangent(end, p)
        cut = n if float(np.dot(n, ray)) < 0 else -n
        if abs(float(cut[0] * -ray[1] + cut[1] * ray[0])) > MAX_CUT_TAN * abs(float(np.dot(cut, ray))):
            return None                               # (too sharp: the cut would run far along the wall)
        out.append((np.array((p[0], p[1], end.point[2])), np.array((cut[0], cut[1], 0.0))))
    return out


def tee(butt, centre, radius, thickness, start=None, sweep=None):
    """(0.246) A straight wall's end meeting a curved wall at its side (a T): (new axis end (x, y, z), cut normal —
    horizontal, away from the straight wall's body). Its two faces stop where they meet the curved wall's face (the
    nearer of its two circles), its end cut along the chord between those two points (the arc's sagitta over a
    wall's thickness: a millimetre or two). None when they do not meet there — the end too far from that face, the
    wall along it, or (start, sweep given: the curved wall's own, radians) past its ends."""
    if butt.curved:
        return None
    c = np.asarray(centre, dtype=float)[:2]
    p, ray = butt.point[:2], butt.ray[:2]
    d = float(np.linalg.norm(p - c))
    if d < 1e-9:
        return None
    back = float(np.linalg.norm(p + ray * NEAR * max(butt.thickness, thickness) - c))   # (its body: which side)
    face = radius + thickness / 2 if back > radius else radius - thickness / 2
    if abs(d - face) > NEAR * max(butt.thickness, thickness):
        return None
    radial = (p - c) / d
    if not can_join(np.append(ray, 0.0), np.append(np.array((-radial[1], radial[0])), 0.0)):
        return None                                   # (along the curved wall: no T)
    n = np.array((-ray[1], ray[0]))
    hits = []
    for side in (1.0, -1.0):
        q = p + n * side * butt.thickness / 2
        found = _line_circle(q, -ray, c, face) + _line_circle(q, ray, c, face)
        if not found:
            return None
        hits.append(min(found, key=lambda h: float(np.linalg.norm(h - q))))
    if start is not None and sweep is not None:      # (on the arc, not past its ends)
        for h in hits:
            a = (math.atan2(h[1] - c[1], h[0] - c[0]) - start) % (2 * math.pi)
            if sweep > 0 and a > sweep + 1e-9 or sweep < 0 and a < 2 * math.pi + sweep - 1e-9:
                return None
    m = hits[1] - hits[0]
    if float(np.linalg.norm(m)) < 1e-9:
        return None
    m = m / np.linalg.norm(m)
    cut = np.array((-m[1], m[0]))
    cut = cut if float(np.dot(cut, ray)) < 0 else -cut
    if abs(float(cut[0] * -ray[1] + cut[1] * ray[0])) > MAX_CUT_TAN * abs(float(np.dot(cut, ray))):
        return None                                   # (too sharp)
    axis = _meet(("line", p, ray), ("line", hits[0], m), p)
    if axis is None:
        return None
    return np.array((axis[0], axis[1], butt.point[2])), np.array((cut[0], cut[1], 0.0))


def arc_cut(angle, sweep, normal):
    """A curved wall's cut at its axis end at `angle`, as the angle (degrees) of the cut normal in the frame of its
    axis there: X along the wall (the way it runs, start to end), Y to its left — 0 a square end, 180 a square
    start, as a straight wall's."""
    c, s = math.cos(angle), math.sin(angle)
    x = np.array((-s, c, 0.0)) * (1.0 if sweep > 0 else -1.0)
    return cut_angle(np.asarray(normal, dtype=float), x)


def _square(angle, at_start):
    target = 180.0 if at_start else 0.0
    return abs((angle - target + 180.0) % 360.0 - 180.0) < 1e-9


def cut_ends(radius, sweep, thickness, start_cut=180.0, end_cut=0.0):
    """The angles (radians, in the wall's own frame: its start at 0, its end at `sweep`) where a curved wall's outer
    and inner faces end, its ends cut at those angles (see arc_cut): ((outer at start, inner at start), (outer at
    end, inner at end)). Square ends: ((0, 0), (sweep, sweep))."""
    if _square(start_cut, True) and _square(end_cut, False):
        return (0.0, 0.0), (sweep, sweep)
    out = []
    for a, cut in ((0.0, start_cut), (sweep, end_cut)):
        c, s = math.cos(a), math.sin(a)
        x = np.array((-s, c)) * (1.0 if sweep > 0 else -1.0)
        y = np.array((-x[1], x[0]))
        k = math.radians(cut)
        normal = x * math.cos(k) + y * math.sin(k)
        m = np.array((-normal[1], normal[0]))
        p = np.array((radius * c, radius * s))
        pair = []
        for r in (radius + thickness / 2, radius - thickness / 2):
            points = _line_circle(p, m, np.zeros(2), r)
            if not points:                            # (a cut that misses the face: square there)
                pair.append(a)
                continue
            q = min(points, key=lambda q: float(np.linalg.norm(q - p)))
            theta = math.atan2(q[1], q[0])
            pair.append(a + ((theta - a + math.pi) % (2 * math.pi) - math.pi))
        out.append(tuple(pair))
    return tuple(out)


def cut_band(centre, radius, start, sweep, thickness, start_cut=180.0, end_cut=0.0, step_deg=3.0):
    """A curved wall's plan as one polygon [(x, y)…] (not a whole circle), its ends cut (the rooms, the magic wand:
    its corners closed as its body's)."""
    (o0, i0), (o1, i1) = cut_ends(radius, sweep, thickness, start_cut, end_cut)

    def run(r, a0, a1):
        n = max(int(math.ceil(abs(math.degrees(a1 - a0)) / step_deg)), 2)
        return [(centre[0] + r * math.cos(start + a0 + (a1 - a0) * k / n),
                 centre[1] + r * math.sin(start + a0 + (a1 - a0) * k / n)) for k in range(n + 1)]

    return [run(radius + thickness / 2, o0, o1) + run(radius - thickness / 2, i1, i0)]
