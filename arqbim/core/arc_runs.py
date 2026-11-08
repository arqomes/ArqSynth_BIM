"""(0.459) Arcs drawn in pieces found again — the owner: «não consigo selecionar linhas e arcos no polígono para
ajustar. Ao desenhar a parede por seleção de aresta, no arco ele só seleciona segmentos em vez de arco inteiro».

A polygon's rounded corner, a circle drawn with the Circle tool, an arc of the Line, a curved wall's face: each is
kept as straight pieces. The pieces round one picked that lie on one circle, turning the same way by small steps, are
that arc — picked whole, its centre and radius known (Revit's sketch arc). Pure numpy, in the plan (x, y) of the
points given (a sketch's own frame for a face on any plane)."""

import math

import numpy as np

MAX_STEP_DEG = 30.0     # a piece of an arc turns at most this much from the one before (a circle of 12 sides or more)
MIN_STEP_DEG = 0.05     # …and at least this much (straight on: not an arc)
SAME_LENGTH = 0.25      # its pieces as long as one another within this part


def _xy(p):
    return np.asarray(p, dtype=float)[:2]


def centre_of(a, b, c):
    """The centre of the circle through three points (plan), or None (in a line)."""
    a, b, c = _xy(a), _xy(b), _xy(c)
    d = 2.0 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    if abs(d) < 1e-12:
        return None
    aa, bb, cc = float(a @ a), float(b @ b), float(c @ c)
    return np.array(((aa * (b[1] - c[1]) + bb * (c[1] - a[1]) + cc * (a[1] - b[1])) / d,
                     (aa * (c[0] - b[0]) + bb * (a[0] - c[0]) + cc * (b[0] - a[0])) / d))


def turn(a, b, c):
    """The signed turn at b (radians, counter-clockwise positive) from a → b to b → c."""
    u, v = _xy(b) - _xy(a), _xy(c) - _xy(b)
    return math.atan2(float(u[0] * v[1] - u[1] * v[0]), float(u @ v))


class Run:
    """An arc found: `indices` of its points in order along the polyline (a loop's may go past its end), `centre`
    (x, y), `radius`, `sweep` (radians, signed, from its first point to its last) and `whole` (the loop is a circle)."""

    def __init__(self, indices, centre, radius, sweep, whole):
        self.indices, self.centre, self.radius, self.sweep, self.whole = indices, centre, radius, sweep, whole

    @property
    def start(self):
        """The angle of its first point about the centre."""
        return self._start

    def __repr__(self):
        return "Run({}, r={:.4f}, sweep={:.1f}°{})".format(self.indices, self.radius, math.degrees(self.sweep),
                                                          ", whole" if self.whole else "")


def run_around(points, k, closed=False):
    """The arc drawn in pieces that the piece k of the polyline `points` (points[k] → points[k + 1]; closed: a loop)
    is part of — a Run — or None when that piece is straight (no neighbour on one circle with it)."""
    pts = [_xy(p) for p in points]
    n = len(pts)
    if n < 3 or not 0 <= k < (n if closed else n - 1):
        return None
    at = (lambda i: pts[i % n]) if closed else (lambda i: pts[i] if 0 <= i < n else None)
    lo, hi = math.radians(MIN_STEP_DEG), math.radians(MAX_STEP_DEG)

    def small(a, b, c, sign=0.0):
        if a is None or b is None or c is None:
            return 0.0
        t_ = turn(a, b, c)
        if not lo <= abs(t_) <= hi or (sign and t_ * sign <= 0):
            return 0.0
        return t_

    def alike(p, q, length):
        """(an arc's pieces are as long as one another: a straight side beside it, longer, is not one of them)"""
        d = float(np.linalg.norm(q - p))
        return abs(d - length) <= SAME_LENGTH * max(d, length)

    def grow(trio):
        """The run from three points in a row on a circle, grown both ways: (run, centre, radius, sign, whole) or
        None."""
        a, b, c = (at(i) for i in trio)
        t_ = small(a, b, c)
        if not t_ or not alike(b, c, float(np.linalg.norm(b - a))):
            return None
        centre = centre_of(a, b, c)
        if centre is None:
            return None
        run, radius, sign = list(trio), float(np.linalg.norm(b - centre)), math.copysign(1.0, t_)
        piece = float(np.linalg.norm(b - a))
        tol = max(5e-4, 1e-3 * radius)
        on = lambda p: p is not None and abs(float(np.linalg.norm(p - centre)) - radius) <= tol     # noqa: E731
        whole = False
        while True:                                   # on past its end…
            j = run[-1] + 1
            if closed and (j - run[0]) % n == 0:      # (round the loop: a circle)
                whole = bool(small(at(run[-2]), at(run[-1]), at(j), sign)) and \
                    bool(small(at(run[-1]), at(j), at(run[1]), sign))
                break
            if not on(at(j)) or not small(at(run[-2]), at(run[-1]), at(j), sign) or \
                    not alike(at(run[-1]), at(j), piece):
                break
            run.append(j)
        while not whole:                              # …and back past its start
            j = run[0] - 1
            if closed and (run[-1] - j) % n == 0:
                break
            if not on(at(j)) or not small(at(j), at(run[0]), at(run[1]), sign) or not alike(at(j), at(run[0]), piece):
                break
            run.insert(0, j)
        return run, centre, radius, sign, whole, tol

    # (the piece with the one before it, or with the one after it: the longer arc — a short straight side beside an
    # arc, as long as its pieces, makes a short one)
    grown = [g for g in (grow((k - 1, k, k + 1)), grow((k, k + 1, k + 2))) if g is not None]
    if not grown:
        return None
    run, centre, radius, sign, whole, tol = max(grown, key=lambda g: (g[4], len(g[0])))
    if not whole and len(run) < 3:
        return None
    if len(run) == 3:                                 # (two pieces only: as long as each other, as an arc's are)
        p, q, r = (at(i) for i in run)
        d1, d2 = float(np.linalg.norm(q - p)), float(np.linalg.norm(r - q))
        if abs(d1 - d2) > 0.02 * max(d1, d2):
            return None
    pts_run = [at(i) for i in run]
    if len(pts_run) >= 3:                             # (the circle through its first, middle and last points)
        better = centre_of(pts_run[0], pts_run[len(pts_run) // 2], pts_run[-1])
        if better is not None:
            r2 = float(np.linalg.norm(pts_run[0] - better))
            if all(abs(float(np.linalg.norm(p - better)) - r2) <= tol for p in pts_run):
                centre, radius = better, r2
    angles = [math.atan2(float(p[1] - centre[1]), float(p[0] - centre[0])) for p in pts_run]
    sweep = sum(((b - a + math.pi) % (2 * math.pi)) - math.pi for a, b in zip(angles, angles[1:]))
    if whole:
        sweep = math.copysign(2 * math.pi, sign)
    out = Run([i % n if closed else i for i in run], centre, radius, sweep, whole)
    out._start = angles[0]
    return out


def chain_through(edges, a, b, tol=1e-5):
    """The polyline of the segments `edges` [(p, q)…] through the segment a–b, followed at each end as long as one
    segment only goes on from there: (its points in order, closed, the index of a in them — the piece picked goes from
    there to the next) — or None when a–b is not one of them."""
    key = lambda p: tuple(int(round(float(c) / tol)) for c in np.asarray(p, dtype=float)[:3])     # noqa: E731
    ends = {}
    segs = [(np.asarray(p, dtype=float), np.asarray(q, dtype=float)) for p, q in edges]
    for i, (p, q) in enumerate(segs):
        ends.setdefault(key(p), []).append(i)
        ends.setdefault(key(q), []).append(i)
    ka, kb = key(a), key(b)
    first = next((i for i in set(ends.get(ka, ())) & set(ends.get(kb, ()))), None)
    if first is None:
        return None
    used = {first}

    def follow(point, came):
        out = []
        while True:
            nxt = [i for i in ends.get(key(point), ()) if i not in used]
            if len(nxt) != 1 or len(ends.get(key(point), ())) != 2:
                return out, False
            i = nxt[0]
            used.add(i)
            p, q = segs[i]
            point = q if key(p) == key(point) else p
            if key(point) == came:
                return out, True
            out.append(point)

    forward, closed = follow(np.asarray(b, dtype=float), ka)
    backward = [] if closed else follow(np.asarray(a, dtype=float), kb)[0]
    points = backward[::-1] + [np.asarray(a, dtype=float), np.asarray(b, dtype=float)] + forward
    return points, closed, len(backward)
