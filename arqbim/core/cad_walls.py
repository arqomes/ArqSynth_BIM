"""Walls from a CAD plan's lines (0.159, Phase 8, step 1): a wall drawn as two parallel lines — its faces — between
MIN_T and MAX_T apart, over a stretch of both; its axis the line in between, its thickness their distance.

1. The pairs of parallel lines near enough, over a stretch of both, the nearest first: each stretch of a line is
   taken once (a wall's face is not also the face of the wall beyond it).
2. The pieces along one line, of one thickness, touching or overlapping, joined (a polyline's sides, a wall
   drawn in bits).
3. At a corner or a T, the ends taken to where the axes meet (the corner square no pair covers).

Pure numpy: plan points in metres. What is made of them (walls joined at their corners) is model/bim's."""

import math

import numpy as np

MIN_T, MAX_T = 0.05, 0.60       # m: a wall's thickness drawn
MIN_LENGTH = 0.10               # m: shorter lines are left out (ticks, hatches)
MIN_OVERLAP = 0.15              # m: two faces side by side at least this long make a wall
PARALLEL = math.sin(math.radians(1.0))
SAME_LINE = 0.01                # m: pieces this near one line are on it
GAP = 0.02                      # m: pieces this near end to end are one
CORNER_REACH = 0.05             # m beyond the half thicknesses: an end this near another axis goes to it
MIN_CORNER = math.sin(math.radians(15.0))


def _free(interval, used):
    """The longest part of [a, b] not in the used intervals."""
    a, b = interval
    pieces = [(a, b)]
    for u0, u1 in used:
        nxt = []
        for p0, p1 in pieces:
            if u1 <= p0 or u0 >= p1:
                nxt.append((p0, p1))
                continue
            if u0 > p0:
                nxt.append((p0, u0))
            if u1 < p1:
                nxt.append((u1, p1))
        pieces = nxt
    return max(pieces, key=lambda p: p[1] - p[0], default=(a, a))


def pieces(segments, min_t=MIN_T, max_t=MAX_T):
    """The wall pieces of pairs of parallel lines: [(start (2,), end (2,), thickness)]."""
    segs = np.asarray(segments, dtype=float).reshape(-1, 2, 2)
    length = np.linalg.norm(segs[:, 1] - segs[:, 0], axis=1)
    segs, length = segs[length >= MIN_LENGTH], length[length >= MIN_LENGTH]
    if len(segs) < 2:
        return []
    p0, d = segs[:, 0], (segs[:, 1] - segs[:, 0]) / length[:, None]
    found = []
    for i in range(len(segs)):
        j = np.arange(i + 1, len(segs))
        if not len(j):
            break
        cross = d[i, 0] * d[j, 1] - d[i, 1] * d[j, 0]
        par = np.abs(cross) < PARALLEL
        w = p0[j] - p0[i]
        offset = np.abs(d[i, 0] * w[:, 1] - d[i, 1] * w[:, 0])
        ok = par & (offset >= min_t - 1e-6) & (offset <= max_t + 1e-6)
        for k in j[ok]:
            t0 = float((segs[k, 0] - p0[i]) @ d[i])
            t1 = float((segs[k, 1] - p0[i]) @ d[i])
            s0, s1 = max(0.0, min(t0, t1)), min(float(length[i]), max(t0, t1))
            if s1 - s0 >= MIN_OVERLAP:
                found.append((float(np.abs(d[i, 0] * (p0[k] - p0[i])[1] - d[i, 1] * (p0[k] - p0[i])[0])), i, int(k),
                              s0, s1))
    found.sort(key=lambda c: c[0])
    used = {}
    out = []
    for thick, i, k, s0, s1 in found:
        a, b = _free((s0, s1), used.get(i, []))
        if b - a < MIN_OVERLAP:
            continue
        # the same stretch on the other line, and what of it is free
        ta = float((p0[i] + d[i] * a - p0[k]) @ d[k])
        tb = float((p0[i] + d[i] * b - p0[k]) @ d[k])
        lo, hi = min(ta, tb), max(ta, tb)
        c, e = _free((max(lo, 0.0), min(hi, float(length[k]))), used.get(k, []))
        if e - c < MIN_OVERLAP:
            continue
        # back on line i: the stretch free on both
        q0, q1 = p0[k] + d[k] * c, p0[k] + d[k] * e
        a2, b2 = sorted((float((q0 - p0[i]) @ d[i]), float((q1 - p0[i]) @ d[i])))
        a, b = max(a, a2), min(b, b2)
        if b - a < MIN_OVERLAP:
            continue
        used.setdefault(i, []).append((a, b))
        ta, tb = sorted((float((p0[i] + d[i] * a - p0[k]) @ d[k]), float((p0[i] + d[i] * b - p0[k]) @ d[k])))
        used.setdefault(k, []).append((ta, tb))
        n = np.array((-d[i, 1], d[i, 0]))
        side = 1.0 if float((p0[k] - p0[i]) @ n) > 0 else -1.0
        mid = n * side * thick / 2
        out.append((p0[i] + d[i] * a + mid, p0[i] + d[i] * b + mid, thick))
    return out


def _covered(a, b, n, t, lo, hi, segments):
    """Does one of the lines run along the face of the wall (axis a → b, its normal n, thickness t) over the
    stretch [lo, hi] along it — the face that goes on, unbroken, past a T?"""
    d = (b - a) / max(np.linalg.norm(b - a), 1e-12)
    for side in (1.0, -1.0):
        face = a + n * side * t / 2
        for p, q in segments:
            if abs(float((p - face) @ n)) > SAME_LINE or abs(float((q - face) @ n)) > SAME_LINE:
                continue
            s = sorted((float((p - face) @ d), float((q - face) @ d)))
            if s[0] <= lo + 1e-6 and s[1] >= hi - 1e-6:
                return True
    return False


MAX_OPENING = 3.5               # m: a gap a door or window block fills, at most (0.160)


def merged(found, segments=(), blocks=(), bridge=0.0):
    """Pieces on one line, of one thickness, touching or overlapping — or apart by less than a wall's thickness
    where their other face goes on unbroken (a T: the wall met broke this face only), or where a door or window
    block fills the gap (0.160: the wall goes on, its opening is cut later), or by less than `bridge` (a scan's
    doors and windows, 0.162) — made one."""
    from .cad_openings import covers_gap
    segments = [(np.asarray(p, dtype=float), np.asarray(q, dtype=float))
                for p, q in np.asarray(segments, dtype=float).reshape(-1, 2, 2)]
    left = list(found)
    out = []
    while left:
        a, b, t = left.pop(0)
        changed = True
        while changed:
            changed = False
            d = (b - a) / max(np.linalg.norm(b - a), 1e-12)
            n = np.array((-d[1], d[0]))
            for k, (c, e, t2) in enumerate(left):
                if abs(t2 - t) > 0.005 or abs(float((c - a) @ n)) > SAME_LINE or abs(float((e - a) @ n)) > SAME_LINE:
                    continue
                d2 = (e - c) / max(np.linalg.norm(e - c), 1e-12)
                if abs(d[0] * d2[1] - d[1] * d2[0]) > PARALLEL:
                    continue
                s = sorted((0.0, float((b - a) @ d)))
                r = sorted((float((c - a) @ d), float((e - a) @ d)))
                gap = max(r[0] - s[1], s[0] - r[1])
                g0, g1 = min(s[1], r[1]), max(s[0], r[0])
                if gap > GAP and not (gap <= MAX_T and _covered(a, b, n, t, g0, g1, segments)) \
                        and not (gap <= MAX_OPENING and any(covers_gap(k2, a, a + d, t, g0, g1) for k2 in blocks)) \
                        and not gap <= bridge:
                    continue
                lo, hi = min(s[0], r[0]), max(s[1], r[1])
                a, b = a + d * lo, a + d * hi
                left.pop(k)
                changed = True
                break
        out.append((a, b, t))
    return out


def _crossing(p, d, q, e):
    den = d[0] * e[1] - d[1] * e[0]
    if abs(den) < 1e-12:
        return None
    w = q - p
    return p + d * ((w[0] * e[1] - w[1] * e[0]) / den)


def cornered(walls):
    """Each end taken to where its axis meets another wall's (within their half thicknesses): the corners and the
    T junctions a pair of faces does not cover."""
    walls = [(np.asarray(a, dtype=float), np.asarray(b, dtype=float), float(t)) for a, b, t in walls]
    out = []
    for i, (a, b, t) in enumerate(walls):
        d = (b - a) / max(np.linalg.norm(b - a), 1e-12)
        ends = [a.copy(), b.copy()]
        for which, p in enumerate((a, b)):
            outward = -d if which == 0 else d
            best = None
            for k, (c, e, t2) in enumerate(walls):
                if k == i:
                    continue
                d2 = (e - c) / max(np.linalg.norm(e - c), 1e-12)
                if abs(d[0] * d2[1] - d[1] * d2[0]) < MIN_CORNER:
                    continue
                x = _crossing(p, d, c, d2)
                if x is None:
                    continue
                along = float((x - p) @ outward)           # (> 0: beyond the end; < 0: back inside it)
                reach = t2 / 2 + t / 2 + CORNER_REACH
                if not -t2 / 2 - 1e-6 <= along <= reach:
                    continue
                on = float((x - c) @ d2)                   # (the crossing on the other wall, or by its end)
                length2 = float(np.linalg.norm(e - c))
                if not -t / 2 - CORNER_REACH <= on <= length2 + t / 2 + CORNER_REACH:
                    continue
                if best is None or abs(along) < abs(best[0]):
                    best = (along, x)
            if best is not None:
                ends[which] = best[1]
        if np.linalg.norm(ends[1] - ends[0]) > MIN_LENGTH:
            out.append((ends[0], ends[1], t))
    return out


SAME_CENTRE = 0.02              # m (0.210): two arcs' centres this near: one centre (a curved wall's two faces)


def _span(a0, a1):
    """An arc's span (start, sweep) in radians, counter-clockwise, sweep in (0, 2π]."""
    s = math.radians(a0) % (2 * math.pi)
    sweep = math.radians(a1 - a0) % (2 * math.pi)
    return s, (2 * math.pi if sweep < 1e-9 else sweep)


def _common(s0, w0, s1, w1):
    """The part (start, sweep) two spans have in common — the longest, round the circle — or None."""
    if w0 >= 2 * math.pi - 1e-9:
        return (s1, w1)
    if w1 >= 2 * math.pi - 1e-9:
        return (s0, w0)
    best = None
    for shift in (-2 * math.pi, 0.0, 2 * math.pi):
        lo, hi = max(s0, s1 + shift), min(s0 + w0, s1 + shift + w1)
        if hi - lo > 1e-9 and (best is None or hi - lo > best[1]):
            best = (lo % (2 * math.pi), hi - lo)
    return best


def arc_walls(arcs, min_t=MIN_T, max_t=MAX_T, same_centre=SAME_CENTRE):
    """(0.210) The curved walls of a plan's arcs: two arcs round one centre between min_t and max_t apart, over a
    stretch of both (MIN_OVERLAP along the axis), the nearest first, each arc taken once — [(centre (2,), the axis'
    radius, start, sweep (radians, counter-clockwise; 2π a ring), thickness)]. same_centre: how near their centres
    (a scan's arcs, fitted to points, a little looser)."""
    items = [(np.asarray(c, dtype=float), float(r)) + _span(a0, a1) for c, r, a0, a1 in arcs if float(r) > 0]
    pairs = []
    for i in range(len(items)):
        for k in range(i + 1, len(items)):
            ci, ri, si, wi = items[i]
            ck, rk, sk, wk = items[k]
            gap = abs(ri - rk)
            if float(np.linalg.norm(ci - ck)) > same_centre or not min_t - 1e-6 <= gap <= max_t + 1e-6:
                continue
            common = _common(si, wi, sk, wk)
            if common is None or common[1] * (ri + rk) / 2 < MIN_OVERLAP:
                continue
            pairs.append((gap, i, k, common))
    pairs.sort(key=lambda p: p[0])
    used, out = set(), []
    for gap, i, k, (start, sweep) in pairs:
        if i in used or k in used:
            continue
        used.update((i, k))
        centre = (items[i][0] + items[k][0]) / 2
        out.append((centre, (items[i][1] + items[k][1]) / 2, start, sweep, gap))
    return out


def wall_axes(segments, min_t=MIN_T, max_t=MAX_T, blocks=()):
    """The walls of a plan's lines: [(axis start (2,), axis end (2,), thickness)] — across the gaps the door and
    window blocks fill."""
    return cornered(merged(pieces(segments, min_t, max_t), segments, blocks))
