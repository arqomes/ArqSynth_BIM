"""The straight skeleton of an outline (0.190): the roof of a building whose eaves all rise inwards at one slope.
Pure Python (numpy) and shapely (to cut the faces at the end).

The eaves move in together, all at the same speed (a wavefront): each corner of the wavefront runs along the
bisector of its two sides, as fast as keeps it on both; the wavefront changes at events —
    a side shrinks to nothing (its two corners meet there): they become one corner;
    a corner turned in (reflex) runs into a side across: the wavefront is split in two there;
    two sides facing each other come onto one line (a wing of even width closing up): the part between them is a
    ridge, and the corners at its far end become one;
and a part that has closed up (three corners met) ends. The corners' tracks are the skeleton — hips, valleys,
ridges —; with the outline they cut it into the roof's faces, one per side: each face is the ground its side
sweeps, its height there that side's distance in (× the slope).

Events are found again at each step among all the corners (the outlines of buildings are small: a few dozen
sides); several at the same moment (a rectangle's two ends) are taken one after the other."""

import math

import numpy as np

EPS = 1e-9
TIME_EPS = 1e-7
TRACE = None            # (a list: the events are written in it, to look into an outline)
JOIN_TOL = 1e-3         # m (in the wavefront's time: × the slope): a corner as high from each of its faces


class _Corner:
    __slots__ = ("p", "t", "v", "left", "right", "prev", "next", "alive")

    def __init__(self, p, t, left, right, sides):
        self.p, self.t, self.left, self.right = np.asarray(p, dtype=float), float(t), left, right
        self.v = _velocity(sides[left], sides[right])
        self.prev = self.next = None
        self.alive = True

    def at(self, t):
        return self.p + self.v * (t - self.t)


def _velocity(a, b):
    """How a corner between sides a (before it) and b (after it) moves, to stay on both as they move in at speed 1:
    n_a · v = 1 and n_b · v = 1; sides in line: straight in; facing each other: it stays."""
    na, nb = a[3], b[3]
    det = na[0] * nb[1] - na[1] * nb[0]
    if abs(det) < 1e-12:
        return na.copy() if float(np.dot(na, nb)) > 0 else np.zeros(2)
    return np.array(((nb[1] - na[1]) / det, (na[0] - nb[0]) / det))


def _reflex(sides, c):
    ea, eb = sides[c.left][2], sides[c.right][2]
    return ea[0] * eb[1] - ea[1] * eb[0] < -1e-12


def _facing(sides, c):
    return float(np.dot(sides[c.left][3], sides[c.right][3])) < -1 + 1e-9


def _ring(start):
    out, c = [start], start.next
    while c is not start:
        out.append(c)
        c = c.next
        if len(out) > 100000:
            raise RuntimeError("broken wavefront")
    return out


class _Wavefront:
    def __init__(self, sides):
        self.sides = sides
        self.segments = []
        self.rings = []

    def end(self, c, q):
        if np.linalg.norm(q - c.p) > EPS:
            self.segments.append((tuple(c.p), tuple(q)))
        c.alive = False

    def line(self, a, b):
        if np.linalg.norm(np.asarray(b) - np.asarray(a)) > EPS:
            self.segments.append((tuple(a), tuple(b)))

    def close(self, ring, t):
        """A part of the wavefront that has closed up: its corners' tracks to where they are, joined in a line."""
        live = _ring(ring)
        where = [c.at(t) for c in live]
        for c, q in zip(live, where):
            self.end(c, q)
        for k in range(len(where) - 1):
            self.line(where[k], where[k + 1])

    def settle(self, x, t):
        """The new corner x put in: a part closed up ends; two sides facing each other on one line close up the
        part between them (a ridge) — the corners at its far end become one — until x is a plain corner."""
        while True:
            live = _ring(x)
            if len(live) < 3:
                self.close(x, t)
                return
            if not _facing(self.sides, x):
                self.rings.append(x)
                return
            y, z = x.prev, x.next                   # (the far ends of its two sides, on the same line now)
            q, qy, qz = x.at(t), y.at(t), z.at(t)
            dy, dz = float(np.linalg.norm(qy - q)), float(np.linalg.norm(qz - q))
            if abs(dy - dz) <= 1e-7:                 # both ends together: one corner there, the wing gone
                far = (qy + qz) / 2
                self.end(x, far)
                self.end(y, far)
                self.end(z, far)
                if y is z:
                    return
                new = _Corner(far, t, y.left, z.right, self.sides)
                new.prev, new.next = y.prev, z.next
                y.prev.next = new
                z.next.prev = new
            elif dy < dz:                            # the nearer end goes on along the other side
                self.end(x, qy)
                self.end(y, qy)
                new = _Corner(qy, t, y.left, x.right, self.sides)
                new.prev, new.next = y.prev, z
                y.prev.next = new
                z.prev = new
            else:
                self.end(x, qz)
                self.end(z, qz)
                new = _Corner(qz, t, x.left, z.right, self.sides)
                new.prev, new.next = y, z.next
                y.next = new
                z.next.prev = new
            x = new


def skeleton(outline):
    """The skeleton of a simple outline [(x, y)…] (counter-clockwise or not; no holes): its segments [((x, y), (x,
    y))] — the corners' tracks — and the sides it was worked from [(start, end, direction, inward normal)] of the
    outline turned counter-clockwise."""
    pts = [np.asarray(p, dtype=float)[:2] for p in outline]
    area = sum(pts[k][0] * pts[(k + 1) % len(pts)][1] - pts[(k + 1) % len(pts)][0] * pts[k][1] for k in range(len(pts)))
    if area < 0:
        pts = pts[::-1]
    pts = [p for k, p in enumerate(pts) if np.linalg.norm(p - pts[k - 1]) > EPS]
    n = len(pts)
    sides = []
    for k in range(n):
        a, b = pts[k], pts[(k + 1) % n]
        e = (b - a) / np.linalg.norm(b - a)
        sides.append((a, b, e, np.array((-e[1], e[0]))))
    wave = _Wavefront(sides)
    corners = [_Corner(pts[k], 0.0, (k - 1) % n, k, sides) for k in range(n)]
    for k in range(n):
        corners[k].prev, corners[k].next = corners[k - 1], corners[(k + 1) % n]
    wave.rings = [corners[0]]
    now = 0.0
    for _step in range(40 * n + 40):
        rings, seen = [], set()
        for r in wave.rings:
            if r.alive and id(r) not in seen:
                members = _ring(r)
                seen.update(id(c) for c in members)
                rings.append(r)
        wave.rings = rings
        if not rings:
            break
        best = None                                  # (time, kind, data)
        for ring in rings:
            live = _ring(ring)
            for c in live:                           # a side shrinking to nothing
                w = c.next
                e = sides[c.right][2]
                length = float(np.dot(e, w.at(now) - c.at(now)))
                rate = float(np.dot(e, w.v - c.v))
                if length <= 1e-7 and rate <= 1e-9:   # (gone already: two corners on one point, not parting)
                    t = now
                elif rate < -1e-12:
                    t = now - length / rate
                else:
                    continue
                if t >= now - TIME_EPS and (best is None or t < best[0] - 1e-12):
                    best = (max(t, now), "edge", c)
            for r in live:                           # a corner turned in, running into a side across
                if not _reflex(sides, r):
                    continue
                for u in live:
                    w = u.next
                    if u is r or w is r or u.right in (r.left, r.right):
                        continue
                    a, _b, e, nrm = sides[u.right]
                    den = 1.0 - float(np.dot(nrm, r.v))
                    if den < 1e-12:
                        continue
                    t = float(np.dot(nrm, r.p - r.v * r.t - a)) / den
                    if t < now - TIME_EPS:
                        continue
                    x = float(np.dot(e, r.at(t)))
                    if not (float(np.dot(e, u.at(t))) + 1e-9 < x < float(np.dot(e, w.at(t))) - 1e-9):
                        continue
                    if best is None or t < best[0] - 1e-12:
                        best = (max(t, now), "split", (r, u))
        if best is None:                             # (nothing more happens: what is left must be flat)
            for ring in rings:
                if ring.alive:
                    where = [c.at(now) for c in _ring(ring)]
                    area = sum(where[k][0] * where[(k + 1) % len(where)][1] - where[(k + 1) % len(where)][0]
                               * where[k][1] for k in range(len(where))) / 2
                    if TRACE is not None:
                        TRACE.append(("stop", round(now, 6), [tuple(np.round(q, 4)) for q in where], area,
                                      [tuple(np.round(c.v, 3)) for c in _ring(ring)]))
                    if abs(area) > 1e-6:
                        raise RuntimeError("the wavefront stopped short")
                    wave.close(ring, now)
            break
        now, kind, data = best
        if TRACE is not None:
            TRACE.append((round(now, 6), kind, [tuple(np.round(c.at(now), 4)) for c in
                                                ((data,) if kind == "edge" else data)],
                          [len(_ring(r)) for r in rings]))
        if kind == "edge":
            c = data
            w = c.next
            q = (c.at(now) + w.at(now)) / 2
            wave.end(c, q)
            wave.end(w, q)
            if w.next is c:                          # (two corners left: closed up)
                continue
            x = _Corner(q, now, c.left, w.right, sides)
            x.prev, x.next = c.prev, w.next
            c.prev.next = x
            w.next.prev = x
            wave.settle(x, now)
        else:
            r, u = data
            w = u.next
            q = r.at(now)
            wave.end(r, q)
            x1 = _Corner(q, now, r.left, u.right, sides)              # (r's side before it, then the side met)
            x2 = _Corner(q, now, u.right, r.right, sides)             # (the side met, then r's side after it)
            rp, rn = r.prev, r.next
            x1.prev, x1.next = rp, w
            rp.next = x1
            w.prev = x1
            x2.prev, x2.next = u, rn
            u.next = x2
            rn.prev = x2
            wave.settle(x1, now)
            wave.settle(x2, now)
    return wave.segments, sides


def roof_faces(outline):
    """The faces of a hip roof over the outline, all its sides rising at one slope: [(side (start, end, direction,
    inward normal), its polygon [(x, y)] counter-clockwise)] — or None when the skeleton did not cut it into one
    face per side."""
    from shapely.geometry import LineString, Point, Polygon
    from shapely.geometry.polygon import orient
    from shapely.ops import polygonize, unary_union
    try:
        segments, sides = skeleton(outline)
    except RuntimeError:
        return None
    poly = Polygon([tuple(s[0]) for s in sides])
    points = [tuple(map(float, s[0])) for s in sides]           # (ends a hair apart taken as one: the arithmetic's)

    def snap(p):
        for q in points:
            if math.dist(p, q) <= 1e-6:
                return q
        points.append((float(p[0]), float(p[1])))
        return points[-1]

    lines = [LineString([tuple(s[0]), tuple(s[1])]) for s in sides]
    for a, b in segments:
        a, b = snap(a), snap(b)
        if a != b:
            lines.append(LineString([a, b]))
    pieces = list(polygonize(unary_union(lines)))
    out = []
    for side in sides:
        a, b, _e, nrm = side
        probe = Point(*((a + b) / 2 + nrm * 1e-6))
        mine = [p for p in pieces if p.contains(probe)]
        if len(mine) != 1:
            return None
        face = orient(mine[0], 1.0)
        out.append((side, [tuple(c) for c in list(face.exterior.coords)[:-1]]))
    if abs(sum(Polygon(f).area for _s, f in out) - poly.area) > 1e-6 * max(poly.area, 1.0):
        return None
    heights = {}                                     # (one roof: each corner as high from every face it is on)
    for (a, _b, _e, nrm), face in out:
        for p in face:
            h = float(np.dot(nrm, np.asarray(p) - a))
            if h < -JOIN_TOL:
                return None
            heights.setdefault((round(p[0], 4), round(p[1], 4)), []).append(h)
    if any(max(v) - min(v) > JOIN_TOL for v in heights.values()):
        return None
    return out
