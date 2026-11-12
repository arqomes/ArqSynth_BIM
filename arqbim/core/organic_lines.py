"""(0.561, PLANO.md «Gerador de formas orgânicas», step 6) Organic outlines: a polygon rounded into a smooth curve (no
smaller for it), and a line that grows — differential growth: it lengthens, folds and meanders without ever crossing
itself, as a coral or the edge of a lettuce leaf — for slabs, planters, benches, brise-soleils; the result is a line
of the model, which an organic form can be made over. All in the line's own plane."""

import math

import numpy as np


def _plane(points):
    """(origin, x, y, normal) of the points' plane (level ones: x east, normal up)."""
    from .param_surface import outline_frame
    p = np.asarray(points, float)
    if len(p) >= 3:
        try:
            return outline_frame(p)
        except ValueError:
            pass
    return p.mean(axis=0), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0)), np.array((0.0, 0.0, 1.0))


def _to2d(points):
    o, x, y, n = _plane(points)
    p = np.asarray(points, float) - o
    return np.column_stack((p @ x, p @ y)), (o, x, y)


def _to3d(xy, frame):
    o, x, y = frame
    return o + xy[:, :1] * x + xy[:, 1:2] * y


def _area(xy):
    x, y = xy[:, 0], xy[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def smooth(points, closed=True, rounds=4, keep_size=True):
    """The line rounded by corner cutting (Chaikin: each corner cut at ¼ and ¾ of its sides, again and again) — a
    closed one scaled back about its middle to the area it had (it would shrink)."""
    xy, frame = _to2d(points)
    a0 = abs(_area(xy)) if closed else 0.0
    for _ in range(int(rounds)):
        nxt = np.roll(xy, -1, axis=0) if closed else xy[1:]
        cur = xy if closed else xy[:-1]
        q, r = 0.75 * cur + 0.25 * nxt, 0.25 * cur + 0.75 * nxt
        out = np.empty((2 * len(cur), 2))
        out[0::2], out[1::2] = q, r
        xy = out if closed else np.vstack((xy[:1], out, xy[-1:]))
    if closed and keep_size and a0 > 1e-12:
        c = xy.mean(axis=0)
        xy = c + (xy - c) * math.sqrt(a0 / max(abs(_area(xy)), 1e-12))
    return _to3d(xy, frame)


def _resample(xy, closed, step):
    seg = np.roll(xy, -1, axis=0) - xy if closed else np.diff(xy, axis=0)
    lengths = np.linalg.norm(seg, axis=1)
    total = float(lengths.sum())
    n = max(int(round(total / step)), 8 if closed else 2)
    s = np.concatenate(([0.0], np.cumsum(lengths)))
    pts = np.vstack((xy, xy[:1])) if closed else xy
    at = np.linspace(0.0, total, n, endpoint=not closed)
    return np.column_stack((np.interp(at, s, pts[:, 0]), np.interp(at, s, pts[:, 1])))


def grow(points, closed=True, steps=200, spacing=None, seed=1, bound=None, max_points=4000, rate=0.01):
    """Differential growth of a line: each step its points are pulled towards their neighbours along it (it stays
    smooth), pushed away from every other point nearer than a few spacings (it never crosses itself), nudged at random
    (it wanders), and a point is added in the middle of each piece grown longer than the spacing (it lengthens).
    `bound`: a closed outline it stays inside (the plan it may fill). Returns the line's points (world)."""
    xy, frame = _to2d(points)
    size = float(np.ptp(xy, axis=0).max()) or 1.0
    d = float(spacing) if spacing else size / 60.0
    box = None
    if bound is not None:
        from shapely.geometry import Polygon
        o, x, y = frame
        bp = np.asarray(bound, float) - o
        box = Polygon(np.column_stack((bp @ x, bp @ y))).buffer(-d * 0.5)
        c = xy.mean(axis=0)                              # (it starts small in the middle — on the bound it could
        xy = c + (xy - c) * 0.4                          # never move — and grows to fill the room)
    xy = _resample(xy, closed, d)
    rng = np.random.default_rng(seed)
    reach = d * 2.2
    for _ in range(int(steps)):
        n = len(xy)
        prev = np.roll(xy, 1, axis=0) if closed else np.vstack((xy[:1], xy[:-1]))
        nxt = np.roll(xy, -1, axis=0) if closed else np.vstack((xy[1:], xy[-1:]))
        move = ((prev + nxt) / 2.0 - xy) * 0.1             # (smooth along it, a little)
        for other in (prev, nxt):                          # (each piece a spring of the spacing's length)
            v = other - xy
            ln = np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12)
            move += v / ln * (ln - d) * 0.25
        cell = np.floor(xy / reach).astype(np.int64)       # (pushed apart: neighbours through a grid of cells)
        keys = cell[:, 0] * 1_000_003 + cell[:, 1]
        order = np.argsort(keys)
        sk = keys[order]
        push = np.zeros_like(xy)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                k2 = (cell[:, 0] + dx) * 1_000_003 + cell[:, 1] + dy
                lo, hi = np.searchsorted(sk, k2), np.searchsorted(sk, k2, side="right")
                width = hi - lo
                if not width.any():
                    continue
                for m in range(int(width.max())):
                    has = width > m
                    i = np.nonzero(has)[0]
                    j = order[lo[has] + m]
                    gap = np.abs(i - j)
                    if closed:
                        gap = np.minimum(gap, n - gap)
                    far = gap > 1                           # (its own neighbours along it: their spring)
                    i, j = i[far], j[far]
                    v = xy[i] - xy[j]
                    dist = np.linalg.norm(v, axis=1)
                    near = (dist < reach) & (dist > 1e-12)
                    i, v, dist = i[near], v[near], dist[near]
                    f = (reach - dist) / reach
                    np.add.at(push, i, v / dist[:, None] * f[:, None] * d * 0.5)
        move += push + rng.normal(0.0, d * 0.02, xy.shape)
        size_move = np.linalg.norm(move, axis=1, keepdims=True)   # (no step longer than a third of the spacing:
        move *= np.minimum(1.0, d * 0.3 / np.maximum(size_move, 1e-12))   # a point never jumps over the line)
        if not closed:
            move[0] = move[-1] = 0.0                       # (an open line keeps its two ends)
        new = xy + move
        if box is not None:                               # (kept inside: a point that would leave stays)
            import shapely
            ok = shapely.contains_xy(box, new[:, 0], new[:, 1])
            new[~ok] = xy[~ok]
        xy = new
        seg = (np.roll(xy, -1, axis=0) - xy) if closed else np.diff(xy, axis=0)
        # (pieces grown long — and, at random, a few more: the line's growth — get a point in their middle; their
        # springs then want more length than there is, and the line folds)
        long_ = (np.linalg.norm(seg, axis=1) > d * 1.25) | (rng.random(len(seg)) < rate)
        room = max_points - len(xy)
        if long_.any() and room > 0:
            if long_.sum() > room:                        # (no more than the room left)
                long_[np.nonzero(long_)[0][room:]] = False
            mids = xy[:len(seg)] + seg / 2.0
            out = []
            for k in range(len(xy)):
                out.append(xy[k])
                if k < len(seg) and long_[k]:
                    out.append(mids[k])
            xy = np.array(out)
    return _to3d(xy, frame)


def crosses_itself(points, closed=True):
    """Whether the line crosses itself (shapely: a ring that is not simple)."""
    from shapely.geometry import LinearRing, LineString
    xy, _f = _to2d(points)
    g = LinearRing(xy) if closed else LineString(xy)
    return not g.is_simple
