"""Walls and floors from a point cloud (0.162, Phase 8, step 2: scan to BIM):

1. the heights where many points lie — floors and ceilings (a histogram of the heights, its peaks);
2. a slice at mid height, above the furniture and through the windows (1,0 to 1,4 m over the floor), thinned to a
   point every centimetre;
3. its lines, one after another — the line most points lie on (RANSAC), its runs along it (a gap splits them),
   those points then taken away;
4. made square: the lines within 5° of the building's main direction (or square to it) turned to it;
5. the walls: two lines a wall's thickness apart (core/cad_walls: the faces of a wall seen from both rooms),
   joined across the gaps a door or a window leaves; a line alone (a façade seen from inside only) a wall of
   OUTER_T outwards — away from where the points are.

Pure numpy: points in metres, in the plan's coordinates."""

import math

import numpy as np

from . import cad_walls

SLICE = (1.0, 1.4)              # m over the floor
CELL = 0.01                     # m: the slice thinned to a point per cell
TOL = 0.015                     # m: a point this near a line is on it
MIN_RUN = 0.40                  # m: a line's run at least this long counts
RUN_GAP = 0.20                  # m: points this far apart along a line split it
MIN_POINTS = 25                 # points on a line, at least
MAX_LINES = 400
TRIES = 250                     # lines tried for each one found
SQUARE_DEG = 5.0                # a line this near the main directions is turned to them
BRIDGE = 3.0                    # m: a gap in a wall's faces this long (a door, a window) is bridged
OUTER_T = 0.30                  # m: a wall seen from one side only (its other face unseen)
LONE_MIN = 1.0                  # m: a line alone at least this long makes such a wall
LONE_SIDE_REACH = 15.0          # m: its inside is the side with more of the slice's points this near…
LONE_SIDE_END = 0.3             # …over its length and this much beyond its ends
LEVEL_CELL = 0.02               # m: the heights' histogram
LEVEL_SHARE = 0.04              # a height with at least this share of the points is a floor or a ceiling


def levels(points, cell=LEVEL_CELL, share=LEVEL_SHARE):
    """The heights where many points lie, lowest first (floors and ceilings)."""
    z = np.asarray(points, dtype=float)[:, 2]
    if not len(z):
        return []
    lo = float(z.min())
    bins = ((z - lo) / cell).astype(np.int64)
    counts = np.bincount(bins)
    need = max(share * len(z), 10)
    out = []
    for k in np.flatnonzero(counts >= need):
        left = counts[k - 1] if k > 0 else 0
        right = counts[k + 1] if k + 1 < len(counts) else 0
        if counts[k] >= left and counts[k] >= right:
            h = lo + (k + 0.5) * cell
            if not out or h - out[-1] > 0.10:
                out.append(h)
    return out


MIN_STOREY = 2.0                # m (0.214): a floor to its ceiling at least this high is a storey
SLAB_RANGE = (0.08, 1.0)        # m: a ceiling to the floor over it (a slab between storeys)


def storeys(heights, min_height=MIN_STOREY, slab=SLAB_RANGE):
    """(0.214) The storeys of a scan's level heights (`levels`, lowest first): [(floor, height)] — a floor and the
    next height MIN_STOREY over it its ceiling; the floor over it the next height a slab's thickness higher."""
    out, k = [], 0
    hs = list(heights)
    while k < len(hs):
        floor = hs[k]
        top = next((j for j in range(k + 1, len(hs)) if hs[j] - floor >= min_height), None)
        if top is None:
            break
        out.append((float(floor), float(hs[top] - floor)))
        nxt = next((j for j in range(top + 1, len(hs)) if slab[0] <= hs[j] - hs[top] <= slab[1]), None)
        if nxt is None:
            break
        k = nxt
    return out


def slice_xy(points, floor, band=SLICE, cell=CELL):
    """The plan points of the slice `band` over the floor, one per cell."""
    p = np.asarray(points, dtype=float)
    keep = (p[:, 2] >= floor + band[0]) & (p[:, 2] <= floor + band[1])
    xy = p[keep, :2]
    if not len(xy):
        return xy
    cells = np.unique(np.floor(xy / cell).astype(np.int64), axis=0)
    return (cells + 0.5) * cell


def lines(xy, tol=TOL, min_run=MIN_RUN, gap=RUN_GAP, most=MAX_LINES, seed=0):
    """The straight runs the points lie on: (K, 2, 2) segments."""
    rng = np.random.default_rng(seed)
    left = np.asarray(xy, dtype=float)
    out = []
    while len(left) >= MIN_POINTS and len(out) < most:
        i, j = rng.integers(0, len(left), size=(2, TRIES))
        d = left[j] - left[i]
        length = np.linalg.norm(d, axis=1)
        ok = length > 0.10
        if not np.any(ok):
            break
        i, d, length = i[ok], d[ok], length[ok]
        n = np.column_stack((-d[:, 1], d[:, 0])) / length[:, None]
        # each point's distance to each line tried: (N, K), in single precision (a big slice: little memory)
        dist = np.abs(left.astype(np.float32) @ n.T.astype(np.float32)
                      - np.einsum("kj,kj->k", n, left[i]).astype(np.float32))
        counts = (dist < tol).sum(axis=0)
        best = int(np.argmax(counts))
        if counts[best] < MIN_POINTS:
            break
        on = dist[:, best] < tol
        pts = left[on]
        centre = pts.mean(axis=0)                           # (the line through them, fitted)
        u = np.linalg.svd(pts - centre, full_matrices=False)[2][0]
        nn = np.array((-u[1], u[0]))
        on = np.abs((left - centre) @ nn) < tol
        pts = left[on]
        along = np.sort((pts - centre) @ u)
        cuts = np.flatnonzero(np.diff(along) > gap)
        starts = np.concatenate(([0], cuts + 1))
        ends = np.concatenate((cuts, [len(along) - 1]))
        for s, e in zip(starts, ends):
            if along[e] - along[s] >= min_run and e - s + 1 >= MIN_POINTS // 3:
                out.append((centre + u * along[s], centre + u * along[e]))
        left = left[~on]
    return np.array(out, dtype=float).reshape(-1, 2, 2)


RADIUS_RANGE = (0.8, 40.0)      # m (0.215): a curved wall's radius, scanned
MIN_ARC = 1.0                   # m: an arc this long at least
MIN_ARC_DEG = 12.0              # …and turning this much at least (a long flat "arc" is a line)
MIN_SAGITTA = 0.05              # m: …and leaving its chord this far at least (flatter: a straight wall's line)
ARC_CENTRE = 0.06               # m: two arcs' centres this near (fitted to points): one wall's two faces


def _circle(p, q, r):
    """The circle through three plan points: (centre (2,), radius) — None when they are (nearly) in a line."""
    ax, ay = p
    bx, by = q
    cx, cy = r
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return None
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    centre = np.array((ux, uy))
    return centre, float(np.linalg.norm(np.asarray(p) - centre))


def off_arcs(xy, found, tol=TOL):
    """(0.215) The points not on any of the arcs found — what the straight lines are looked for in (else a curved
    wall's points would make short lines, its chords)."""
    pts = np.asarray(xy, dtype=float)
    keep = np.ones(len(pts), dtype=bool)
    for centre, radius, a0, a1 in found:
        rel = pts - np.asarray(centre, dtype=float)
        on = np.abs(np.linalg.norm(rel, axis=1) - radius) < tol * 1.5
        angle = (np.degrees(np.arctan2(rel[:, 1], rel[:, 0])) - a0) % 360.0
        keep &= ~(on & (angle <= (a1 - a0) % 360.0 + 1e-6 if (a1 - a0) % 360.0 > 1e-6 else on))
    return pts[keep]


def arcs(xy, tol=TOL, gap=RUN_GAP, most=60, seed=0):
    """(0.215) The arcs the points lie on (curved walls' faces): [(centre (2,), radius, start, end)] — degrees,
    counter-clockwise —, one after another (RANSAC on circles through three points), those points then taken away;
    an arc split where its points leave a gap."""
    rng = np.random.default_rng(seed)
    left = np.asarray(xy, dtype=float)
    out = []
    misses = 0                                               # (circles in a row that made no arc: straight walls)
    while len(left) >= 2 * MIN_POINTS and len(out) < most and misses < 4:
        before = len(out)
        tried = []
        for _ in range(TRIES):
            i = rng.integers(0, len(left), size=3)
            if len(set(i.tolist())) < 3:
                continue
            found = _circle(*left[i])
            if found is None or not RADIUS_RANGE[0] <= found[1] <= RADIUS_RANGE[1]:
                continue
            centre, radius = found
            count = int(np.count_nonzero(np.abs(np.linalg.norm(left - centre, axis=1) - radius) < tol))
            tried.append((count, centre, radius))
        tried.sort(key=lambda c: -c[0])
        if not tried or tried[0][0] < 2 * MIN_POINTS:
            break
        best = None
        for _count, centre, radius in tried[:5]:             # (the best few, each fitted to its points — those a
            on = np.abs(np.linalg.norm(left - centre, axis=1) - radius) < tol     # little farther first, or a short
            for reach in (2 * tol, 2 * tol, tol, tol):       # arc's ends are left out and it leans; then nearer, so
                fitted = _fit_circle(left[on])               # a circle first caught across two faces lets one go —;
                if fitted is None:                           # the one with the longest unbroken arcs kept)
                    break
                centre, radius = fitted
                on = np.abs(np.linalg.norm(left - centre, axis=1) - radius) < reach
            close = np.abs(np.linalg.norm(left - centre, axis=1) - radius) < 0.6 * tol
            score = sum(a1 - a0 for a0, a1 in _runs(left[close], centre, radius, gap)) * radius   # (the longest arcs
            if best is None or score > best[0]:              # unbroken, of the points nearest it: a circle near a face
                best = (score, centre, radius, on)           # but not on it holds them only in short runs)
        _score, centre, radius, on = best
        out += [(centre, radius, math.degrees(a0), math.degrees(a1)) for a0, a1 in _runs(left[on], centre, radius, gap)]
        left = left[~on]
        misses = 0 if len(out) > before else misses + 1
    return out


def _runs(pts, centre, radius, gap):
    """(0.215) The arcs (start, end radians, counter-clockwise) a circle's points lie along unbroken — split where they
    leave a gap — that are long enough (MIN_ARC, MIN_ARC_DEG); all round: [(0, 2π)]. None of a radius out of range."""
    if not len(pts) or not RADIUS_RANGE[0] <= radius <= RADIUS_RANGE[1]:
        return []
    angles = np.sort(np.arctan2(pts[:, 1] - centre[1], pts[:, 0] - centre[0]))
    n = len(angles)
    steps = np.diff(np.concatenate((angles, [angles[0] + 2 * math.pi])))
    cuts = np.flatnonzero(steps * radius > gap)
    if not len(cuts):
        return [(0.0, 2 * math.pi)]
    out = []
    for k, c in enumerate(cuts):                             # (each run between two gaps: from s to e)
        s, e = (c + 1) % n, cuts[(k + 1) % len(cuts)]
        a0 = float(angles[s])
        a1 = float(angles[e] if e >= s else angles[e] + 2 * math.pi)
        sagitta = radius * (1.0 - math.cos(min(a1 - a0, math.pi) / 2))
        if (a1 - a0) * radius >= MIN_ARC and math.degrees(a1 - a0) >= MIN_ARC_DEG and sagitta >= MIN_SAGITTA:
            out.append((a0, a1))
    return out


def _fit_circle(pts):
    """The circle fitted to plan points (least squares, Kåsa): (centre (2,), radius), or None."""
    pts = np.asarray(pts, dtype=float)
    if len(pts) < 3:
        return None
    a = np.column_stack((pts, np.ones(len(pts))))
    b = -(pts ** 2).sum(axis=1)
    try:
        (d, e, f), *_ = np.linalg.lstsq(a, b, rcond=None)
    except np.linalg.LinAlgError:
        return None
    centre = np.array((-d / 2, -e / 2))
    r2 = float(centre @ centre - f)
    if r2 <= 0:
        return None
    radius = math.sqrt(r2)
    for _trim in range(4):                                   # (a few points off the face — another wall's, crossing
        for _ in range(8):                                   # it — pull a short arc's fit: those far from the rest
            rel = pts - centre                               # taken out, and fitted again)
            dist = np.linalg.norm(rel, axis=1)
            if np.any(dist < 1e-9):
                break
            jac = np.column_stack((-rel / dist[:, None], -np.ones(len(pts))))   # (to the points' true distances:
            step, *_ = np.linalg.lstsq(jac, -(dist - radius), rcond=None)       # Gauss-Newton — Kåsa's fit leans
            centre, radius = centre + step[:2], radius + float(step[2])         # on a short arc)
            if float(np.abs(step).max()) < 1e-7:
                break
        res = np.abs(np.linalg.norm(pts - centre, axis=1) - radius)
        keep = res <= max(3.0 * 1.4826 * float(np.median(res)), 0.004)
        if keep.all() or keep.sum() < 3:
            break
        pts = pts[keep]
    return (centre, radius) if radius > 0 else None


def arc_axes(found, xy, min_t=cad_walls.MIN_T, max_t=cad_walls.MAX_T, outer=OUTER_T):
    """(0.215) The curved walls of a scan's arcs: two round one centre a wall's thickness apart (cad_walls.arc_walls);
    an arc alone (a curved façade seen from inside) a wall `outer` thick, outwards — away from where the points
    are. [(centre, axis radius, start, sweep (radians), thickness)]."""
    paired = cad_walls.arc_walls(found, min_t, max_t, ARC_CENTRE)
    used = []
    for centre, radius, _s, _w, t in paired:
        used += [(centre, radius - t / 2), (centre, radius + t / 2)]
    middle = np.asarray(xy, dtype=float).mean(axis=0) if len(xy) else np.zeros(2)
    out = list(paired)
    for centre, radius, a0, a1 in found:
        if any(float(np.linalg.norm(np.asarray(centre) - c)) < ARC_CENTRE and abs(radius - r) < 0.03
               for c, r in used):
            continue
        inside = float(np.linalg.norm(middle - np.asarray(centre))) < radius     # (the room within the circle)
        start = math.radians(a0) % (2 * math.pi)
        sweep = math.radians(a1 - a0) % (2 * math.pi) or 2 * math.pi
        out.append((np.asarray(centre, dtype=float), radius + (outer / 2 if inside else -outer / 2), start, sweep,
                    outer))
    return out


def main_direction(segments):
    """The building's main direction (radians, 0 to 90°): the lines' directions, by their lengths, folded on 90°."""
    segs = np.asarray(segments, dtype=float).reshape(-1, 2, 2)
    if not len(segs):
        return 0.0
    d = segs[:, 1] - segs[:, 0]
    w = np.linalg.norm(d, axis=1)
    a = np.arctan2(d[:, 1], d[:, 0])
    m = np.angle(np.sum(w * np.exp(4j * a))) / 4          # (4 θ: the four square directions as one)
    return float(m % (math.pi / 2))


def squared(segments, deg=SQUARE_DEG):
    """The lines within `deg` of the main direction, or square to it, turned to it about their middle."""
    segs = np.asarray(segments, dtype=float).reshape(-1, 2, 2).copy()
    base = main_direction(segs)
    for k, (p, q) in enumerate(segs):
        d = q - p
        a = math.atan2(d[1], d[0])
        rel = (a - base) % (math.pi / 2)
        off = rel if rel < math.pi / 4 else rel - math.pi / 2
        if abs(math.degrees(off)) <= deg:
            target = a - off
            mid, half = (p + q) / 2, float(np.linalg.norm(d)) / 2
            u = np.array((math.cos(target), math.sin(target)))
            segs[k] = (mid - u * half, mid + u * half)
    return segs


def _explained(seg, walls, reach=0.03):
    """Is most of this line a face of one of the walls?"""
    p, q = seg
    for a, b, t in walls:
        d = (b - a) / max(float(np.linalg.norm(b - a)), 1e-12)
        n = np.array((-d[1], d[0]))
        if abs(abs(float((p - a) @ n)) - t / 2) > reach or abs(abs(float((q - a) @ n)) - t / 2) > reach:
            continue
        s = sorted((float((p - a) @ d), float((q - a) @ d)))
        length = float(np.linalg.norm(b - a))
        covered = max(0.0, min(s[1], length + t) - max(s[0], -t))
        if covered >= 0.6 * (s[1] - s[0]):
            return True
    return False


def floor_outline(walls):
    """The outline round the walls (their outer faces): the floor's slab under them — (N, 2), or None."""
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    shapes = [LineString([tuple(a), tuple(b)]).buffer(t / 2, cap_style=2, join_style=2) for a, b, t in walls]
    if not shapes:
        return None
    union = unary_union(shapes)
    polys = list(getattr(union, "geoms", [union]))
    big = max(polys, key=lambda g: g.area, default=None)
    if big is None or big.is_empty or big.geom_type != "Polygon":
        return None
    from shapely.geometry import Polygon
    return np.array(Polygon(big.exterior).simplify(0.005).exterior.coords)[:-1]


OPEN_CELL = 0.05                # m (0.213): a wall's band seen as cells along it and up it
PROBE = (1.15, 1.45)            # m over the floor: where an opening has no points (over a window's sill, under its head)
MIN_OPENING = 0.50              # m: an empty stretch narrower than this is not an opening
DOOR_SILL = 0.15                # m: points stopping this near the floor: a door (a window has a sill)
WALL_BAND = 0.06                # m beyond a wall's half thickness: its points


def openings(points, walls, floor, height, cell=OPEN_CELL, probe=PROBE):
    """(0.213) The doors and windows of the walls found in a scan: where, in a wall's band, there are no points at
    the probe's heights over a stretch MIN_OPENING wide at least (not at the wall's ends) — a door when they are
    missing down to the floor, else a window, its sill where the points under it stop; its top where they start
    again over it (the lintel; the ceiling when they do not). [(cad_openings.BlockInstance, "door" | "window")] —
    their width along the wall, their height and sill set."""
    from .cad_openings import BlockInstance
    p = np.asarray(points, dtype=float)
    out = []
    rows = max(int(math.ceil(height / cell)), 1)
    lo_r, hi_r = int(probe[0] / cell), min(int(probe[1] / cell), rows - 1)
    for a, b, t in walls:
        a, b = np.asarray(a, dtype=float)[:2], np.asarray(b, dtype=float)[:2]
        length = float(np.linalg.norm(b - a))
        if length < 2 * MIN_OPENING:
            continue
        d = (b - a) / length
        n = np.array((-d[1], d[0]))
        rel = p[:, :2] - a
        along, across = rel @ d, rel @ n
        z = p[:, 2] - floor
        near = (np.abs(across) <= t / 2 + WALL_BAND) & (along >= 0.0) & (along <= length) & (z >= 0.02) & \
            (z <= height - 0.02)
        if np.count_nonzero(near) < 20:
            continue
        cols = max(int(math.ceil(length / cell)), 1)
        grid = np.zeros((cols, rows), dtype=bool)
        grid[np.clip((along[near] / cell).astype(np.int64), 0, cols - 1),
             np.clip((z[near] / cell).astype(np.int64), 0, rows - 1)] = True
        empty = ~grid[:, lo_r:hi_r + 1].any(axis=1)
        k = 0
        while k < cols:
            if not empty[k]:
                k += 1
                continue
            c0 = k
            while k < cols and empty[k]:
                k += 1
            c1 = k - 1
            if (c1 - c0 + 1) * cell < MIN_OPENING or c0 == 0 or c1 == cols - 1:
                continue                                 # (narrow, or open at the wall's end: a corner)
            run = grid[c0:c1 + 1]
            under = [int(np.flatnonzero(col[:lo_r]).max()) + 1 if col[:lo_r].any() else 0 for col in run]
            over = [int(np.flatnonzero(col[hi_r + 1:]).min()) + hi_r + 1 if col[hi_r + 1:].any() else rows
                    for col in run]
            sill, top = float(np.median(under)) * cell, float(np.median(over)) * cell
            kind = "door" if sill <= DOOR_SILL else "window"
            # (its ends at the last points either side, at the probe's heights: not a cell's edge)
            band = near & (z >= probe[0]) & (z <= probe[1])
            left, right = along[band & (along < c0 * cell)], along[band & (along > (c1 + 1) * cell)]
            s0 = float(left.max()) if left.size else c0 * cell
            s1 = float(right.min()) if right.size else (c1 + 1) * cell
            ends = np.array((a + d * s0, a + d * s1))
            tall = None if top >= height - cell else (top if kind == "door" else top - sill)   # (no lintel seen:
            inst = BlockInstance("nuvem", kind, ends, [], tuple(float(c) for c in ends.mean(axis=0)), 0.0,    # the
                                 kind == "door", tall, None if kind == "door" else sill)                 # usual one)
            out.append((inst, kind))
    return out


def wall_axes(segments, xy, min_t=cad_walls.MIN_T, max_t=cad_walls.MAX_T, outer=OUTER_T):
    """The walls of a slice's lines: [(start (2,), end (2,), thickness)] — pairs of faces, and the lines alone
    (seen from one side) as walls of `outer` thickness on the side away from the points."""
    segs = squared(segments)
    # (a scan's thicknesses to the centimetre: the two faces' noise would keep one wall in pieces)
    found = [(a, b, round(t, 2)) for a, b, t in cad_walls.pieces(segs, min_t, max_t)]
    found = cad_walls.merged(found, segs, bridge=BRIDGE)
    xy = np.asarray(xy, dtype=float)
    lone = []
    for p, q in segs:
        if float(np.linalg.norm(q - p)) < LONE_MIN or _explained((p, q), found):
            continue
        d = (q - p) / float(np.linalg.norm(q - p))
        n = np.array((-d[1], d[0]))
        rel = xy - p
        along, across = rel @ d, rel @ n
        # the building is on the side where the slice's points are (the walls met at its ends count too)
        near = (along > -LONE_SIDE_END) & (along < float(np.linalg.norm(q - p)) + LONE_SIDE_END) \
            & (np.abs(across) < LONE_SIDE_REACH) & (np.abs(across) > 0.05)
        side = 1.0 if np.count_nonzero(near & (across > 0)) < np.count_nonzero(near & (across < 0)) else -1.0
        lone.append((p + n * side * outer / 2, q + n * side * outer / 2, outer))
    return cad_walls.cornered(cad_walls.merged(found + lone, (), bridge=BRIDGE))
