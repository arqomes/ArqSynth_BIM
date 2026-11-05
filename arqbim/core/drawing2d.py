"""2D drawings from the 3D model (Phase 3, step 4): what a plan or section plane cuts
(closed outlines, to be filled — the poché) and the edges seen beyond it, flattened onto
the drawing's own axes. Pure numpy: no window, no GPU.

A view is a plane n·p = offset that keeps n·p >= offset (as the 3D view's clipping) and
two drawing axes u (to the right) and v (up), with an origin.
"""

import numpy as np

TOL = 1e-6          # m: points closer than this are the same point when outlines are joined


def cut_segments(verts, tris, normal, offset):
    """The segments where the triangles cross the plane n·p = offset: (K, 2, 3).
    A triangle lying in the plane gives nothing (its outline comes from its neighbours)."""
    v = np.asarray(verts, dtype=float).reshape(-1, 3)
    t = np.asarray(tris, dtype=np.int64).reshape(-1, 3)
    if not len(t):
        return np.zeros((0, 2, 3))
    d = v @ np.asarray(normal, dtype=float) - offset
    dt = d[t]                                             # (T, 3) signed distances of the corners
    above = dt > 0
    count = above.sum(axis=1)
    crossing = (count == 1) | (count == 2)
    t, dt, above = t[crossing], dt[crossing], above[crossing]
    if not len(t):
        return np.zeros((0, 2, 3))
    out = []
    for i, j in ((0, 1), (1, 2), (2, 0)):                 # each side of each triangle that crosses
        crosses = above[:, i] != above[:, j]
        out.append((crosses, _crossing_point(v[t[:, i]], v[t[:, j]], dt[:, i], dt[:, j])))
    # every crossing triangle has exactly two crossing sides: pair them in order
    points = np.stack([p for _c, p in out], axis=1)       # (T, 3 sides, 3)
    mask = np.stack([c for c, _p in out], axis=1)         # (T, 3)
    first = np.argmax(mask, axis=1)
    second = 2 - np.argmax(mask[:, ::-1], axis=1)
    rows = np.arange(len(t))
    return np.stack((points[rows, first], points[rows, second]), axis=1)


def _crossing_point(a, b, da, db):
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(np.abs(da - db) > 1e-15, da / (da - db), 0.5)
    return a + (b - a) * s[:, None]


def loops(segments, tol=TOL):
    """Join cut segments into closed outlines: a list of (N, 3) point arrays. Segments that
    do not close (an open mesh) are left out."""
    segs = np.asarray(segments, dtype=float).reshape(-1, 2, 3)
    if not len(segs):
        return []
    keys = np.round(segs / tol).astype(np.int64)
    ends = {}
    for k, (a, b) in enumerate(keys):
        for side, key in ((0, tuple(a)), (1, tuple(b))):
            ends.setdefault(key, []).append((k, side))
    used = np.zeros(len(segs), bool)
    out = []
    for start in range(len(segs)):
        if used[start] or np.allclose(segs[start, 0], segs[start, 1], atol=tol):
            used[start] = True
            continue
        used[start] = True
        ring = [segs[start, 0], segs[start, 1]]
        first, key = tuple(keys[start, 0]), tuple(keys[start, 1])
        while key != first:
            nxt = next(((k, side) for k, side in ends.get(key, ()) if not used[k]), None)
            if nxt is None:
                ring = None                               # open: not an outline
                break
            k, side = nxt
            used[k] = True
            ring.append(segs[k, 1 - side])
            key = tuple(keys[k, 1 - side])
        if ring is not None and len(ring) >= 4:
            out.append(np.array(ring[:-1]))
    return out


def _signed_area(ring):
    x, y = ring[:, 0], ring[:, 1]
    return 0.5 * float(np.dot(x[:-1], y[1:]) - np.dot(y[:-1], x[1:]) + x[-1] * y[0] - y[-1] * x[0])


def oriented(rings):
    """(0.253) One element's cut outlines (2D) turned one way — the outer ones counter-clockwise, those inside an
    odd number of the others (its holes) clockwise —, so that filled together with the winding rule what two
    elements share stays filled and a hole stays open. (loops gives them either way round, as its segments fall:
    a round wall's hole was filled, a column's overlap with a wall left out of the outline.)"""
    rings = [np.asarray(r, dtype=float) for r in rings]
    if len(rings) < 2:
        polys = [None] * len(rings)
    else:
        from shapely.geometry import Polygon
        polys = []
        for r in rings:
            p = Polygon(r) if len(r) >= 3 else None
            polys.append(p if p is None or p.is_valid else p.buffer(0))
    out = []
    for k, ring in enumerate(rings):
        p = polys[k]
        depth = 0 if p is None or p.is_empty else \
            sum(1 for j, q in enumerate(polys) if j != k and q is not None and not q.is_empty and q.contains(p))
        if (_signed_area(ring) > 0) != (depth % 2 == 0):
            ring = ring[::-1].copy()
        out.append(ring)
    return out


def region(rings):
    """(0.253) What outlines turned as `oriented` turns them fill (a shapely geometry): those counter-clockwise
    joined, less those clockwise (the holes)."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    outer, holes = [], []
    for ring in rings:
        ring = np.asarray(ring, dtype=float)
        if len(ring) >= 3:
            p = Polygon(ring)
            (outer if _signed_area(ring) > 0 else holes).append(p if p.is_valid else p.buffer(0))
    if len(outer) == 1 and not holes:                 # (0.320: one outline, the most often — nothing to join)
        return outer[0]
    whole = unary_union(outer)
    return whole.difference(unary_union(holes)) if holes else whole


def nested(rings):
    """(0.320) What outlines turned as `rings_of` turns them fill when one region may lie in another's hole (the
    inner plaster of a room's walls inside the outer plaster's): each hole taken from the smallest outline round it
    only (`region` takes every hole from all)."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    outers, holes = [], []
    for ring in rings:
        ring = np.asarray(ring, dtype=float)
        if len(ring) >= 3:
            (outers if _signed_area(ring) > 0 else holes).append(Polygon(ring).buffer(0))
    mine = [[] for _o in outers]
    for hole in holes:
        if hole.is_empty:
            continue
        around = [k for k, o in enumerate(outers) if o.area > hole.area and o.buffer(1e-9).covers(hole)]
        if around:
            mine[min(around, key=lambda k: outers[k].area)].append(hole)
    return unary_union([o.difference(unary_union(h)) if h else o for o, h in zip(outers, mine)])


def rings_of(geometry):
    """(0.254) A shapely (multi)polygon's outlines, turned as `oriented` turns them (outer counter-clockwise, holes
    clockwise): [(N, 2)]."""
    from shapely.geometry.polygon import orient
    out = []
    for poly in getattr(geometry, "geoms", [geometry]):
        if poly.geom_type != "Polygon" or poly.is_empty:
            continue
        poly = orient(poly, 1.0)
        out.append(np.asarray(poly.exterior.coords, dtype=float)[:-1])
        out += [np.asarray(hole.coords, dtype=float)[:-1] for hole in poly.interiors]
    return out


def kept_edges(a, b, normal, offset):
    """The edges (a[i]–b[i]) on the kept side of the plane (n·p >= offset), those going through
    it cut short at the plane: (K, 2, 3)."""
    a, b = np.asarray(a, dtype=float).reshape(-1, 3), np.asarray(b, dtype=float).reshape(-1, 3)
    n = np.asarray(normal, dtype=float)
    da, db = a @ n - offset, b @ n - offset
    keep = (da >= -TOL) | (db >= -TOL)
    a, b, da, db = a[keep].copy(), b[keep].copy(), da[keep], db[keep]
    for p, dp, q, dq in ((a, da, b, db), (b, db, a, da)):
        out = dp < -TOL
        if out.any():
            p[out] = _crossing_point(q[out], p[out], dq[out], dp[out])
    return np.stack((a, b), axis=1) if len(a) else np.zeros((0, 2, 3))


def clip_between(ring, normal, d0, d1):
    """The part of an outline (N, 3) between two parallel planes, d0 <= n·p <= d1 (a material
    layer), or None: Sutherland–Hodgman against both sides (a slab of space is convex)."""
    n = np.asarray(normal, dtype=float)
    pts = np.asarray(ring, dtype=float)
    for m, d in ((n, d0), (-n, -d1)):
        s = pts @ m - d
        out = []
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            if s[i] >= 0:
                out.append(pts[i])
            if (s[i] >= 0) != (s[j] >= 0):
                out.append(pts[i] + (pts[j] - pts[i]) * (s[i] / (s[i] - s[j])))
        if len(out) < 3:
            return None
        pts = np.array(out)
    return pts


def clip_ring_to_rect(ring, rect):
    """The part of a 2D outline (N, 2) inside the rectangle (x0, y0, x1, y1), or None (a crop
    region, 0.65): Sutherland–Hodgman against its four sides."""
    x0, y0, x1, y1 = rect
    pts = np.asarray(ring, dtype=float)
    for axis, d, sign in ((0, x0, 1.0), (0, x1, -1.0), (1, y0, 1.0), (1, y1, -1.0)):
        s = (pts[:, axis] - d) * sign
        out = []
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            if s[i] >= 0:
                out.append(pts[i])
            if (s[i] >= 0) != (s[j] >= 0):
                out.append(pts[i] + (pts[j] - pts[i]) * (s[i] / (s[i] - s[j])))
        if len(out) < 3:
            return None
        pts = np.array(out)
    return pts


def clip_segments_to_rect(segments, rect):
    """The parts of 2D segments (K, 2, 2) inside the rectangle (x0, y0, x1, y1): Liang–Barsky."""
    segs = np.asarray(segments, dtype=float).reshape(-1, 2, 2)
    if not len(segs):
        return segs
    a, d = segs[:, 0], segs[:, 1] - segs[:, 0]
    t0, t1 = np.zeros(len(segs)), np.ones(len(segs))
    ok = np.ones(len(segs), dtype=bool)
    x0, y0, x1, y1 = rect
    for p, q in ((-d[:, 0], a[:, 0] - x0), (d[:, 0], x1 - a[:, 0]), (-d[:, 1], a[:, 1] - y0), (d[:, 1], y1 - a[:, 1])):
        parallel = np.abs(p) < 1e-15
        ok &= ~(parallel & (q < 0))
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.where(parallel, 0.0, q / np.where(parallel, 1.0, p))
        t0 = np.where(~parallel & (p < 0), np.maximum(t0, r), t0)
        t1 = np.where(~parallel & (p > 0), np.minimum(t1, r), t1)
    ok &= t0 < t1 - 1e-12
    a, d, t0, t1 = a[ok], d[ok], t0[ok], t1[ok]
    return np.stack((a + d * t0[:, None], a + d * t1[:, None]), axis=1)


def flatten(points, origin, u, v):
    """3D points -> 2D drawing coordinates (metres along u and v from origin)."""
    p = np.asarray(points, dtype=float) - np.asarray(origin, dtype=float)
    return np.stack((p @ np.asarray(u, dtype=float), p @ np.asarray(v, dtype=float)), axis=-1)


# ------------------------------------------------------------ hidden lines (image space)

RESOLUTION = 1600           # pixels across the drawing's longer side (~0,25 mm on an A3 sheet)
CHUNK = 4_000_000           # pixels looked at in one go while filling the depth image


def depth_image(tri2d, depth, shape, keep_from):
    """The depth image of triangles: for each pixel, the smallest depth of the triangles covering
    its centre, counting only what is kept (depth >= keep_from: a section's near side is gone).
    tri2d: (T, 3, 2) pixel coordinates; depth: (T, 3) depth along the view at the corners."""
    h, w = shape
    zb = np.full(h * w, np.inf, dtype=np.float32)              # (32-bit: half the memory to go through)
    tri2d = np.asarray(tri2d, dtype=np.float32)
    depth = np.asarray(depth, dtype=np.float32)
    lo = np.floor(tri2d.min(axis=1)).astype(np.int32)
    hi = np.ceil(tri2d.max(axis=1)).astype(np.int32)
    lo = np.maximum(lo, 0)
    hi = np.minimum(hi, (w - 1, h - 1))
    bw, bh = hi[:, 0] - lo[:, 0] + 1, hi[:, 1] - lo[:, 1] + 1
    a, b, c = tri2d[:, 0], tri2d[:, 1], tri2d[:, 2]
    area = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    good = (bw > 0) & (bh > 0) & (np.abs(area) > 1e-6)       # (edge-on triangles cover no pixel centre)
    # nearest first, in waves: after each wave, what is already hidden behind it is skipped
    # (a facade hides the rows of rooms behind it: most triangles of an elevation are never drawn)
    nearest = np.maximum(depth.min(axis=1), np.float32(keep_from))
    order = np.flatnonzero(good)
    order = order[np.argsort(nearest[order], kind="stable")]
    keep_from = np.float32(keep_from - 1e-6)
    for wave in range(0, len(order), WAVE):
        idx = order[wave:wave + WAVE]
        if wave:
            idx = idx[nearest[idx] <= _farthest_under(zb.reshape(h, w), lo[idx], hi[idx]) + 1e-4]
        _fill(zb, w, idx, lo, bw, bh, a, b, c, area, depth, keep_from)
    return zb.reshape(h, w)


WAVE = 50_000               # triangles drawn before checking what the next ones would be hidden by


def _farthest_under(zb, lo, hi):
    """For each box (lo, hi pixels), a depth nothing in it is beyond — conservative: from a
    max-pyramid of the depth image, at the level where the box spans at most 2 × 2 cells."""
    levels = [zb]
    while max(levels[-1].shape) > 1:
        z = levels[-1]
        if z.shape[0] % 2:
            z = np.vstack([z, np.full((1, z.shape[1]), np.inf, z.dtype)])
        if z.shape[1] % 2:
            z = np.hstack([z, np.full((z.shape[0], 1), np.inf, z.dtype)])
        levels.append(np.maximum(np.maximum(z[0::2, 0::2], z[1::2, 0::2]), np.maximum(z[0::2, 1::2], z[1::2, 1::2])))
    size = np.maximum(hi - lo, 1).max(axis=1)
    level = np.clip(np.ceil(np.log2(size)).astype(np.int64), 0, len(levels) - 1)
    out = np.empty(len(lo), np.float32)
    for k in np.unique(level):
        m = level == k
        z = levels[k]
        x0, y0 = np.minimum(lo[m, 0] >> k, z.shape[1] - 1), np.minimum(lo[m, 1] >> k, z.shape[0] - 1)
        x1, y1 = np.minimum(hi[m, 0] >> k, z.shape[1] - 1), np.minimum(hi[m, 1] >> k, z.shape[0] - 1)
        out[m] = np.maximum(np.maximum(z[y0, x0], z[y0, x1]), np.maximum(z[y1, x0], z[y1, x1]))
    return out


def _fill(zb, w, idx, lo, bw, bh, a, b, c, area, depth, keep_from):
    """Draw the triangles `idx` into the depth image (flat, row width w), row by row: for each row
    of pixels, where the triangle starts and ends; the depth from the triangle's plane
    (d = A·x + B·y + C). A chunk of pixels at a time."""
    h = zb.size // w
    # the depth plane of each triangle, in pixel coordinates
    d0, d1, d2 = depth[:, 0], depth[:, 1], depth[:, 2]
    with np.errstate(divide="ignore", invalid="ignore"):
        A = ((d1 - d0) * (c[:, 1] - a[:, 1]) - (d2 - d0) * (b[:, 1] - a[:, 1])) / area
        B = ((d2 - d0) * (b[:, 0] - a[:, 0]) - (d1 - d0) * (c[:, 0] - a[:, 0])) / area
        C = d0 - A * a[:, 0] - B * a[:, 1]                       # (seen edge-on: no area, no pixels)
    corners = np.stack((a, b, c), axis=1)                       # (T, 3, 2)
    estimate = (bw * bh)[idx].astype(np.int64)                  # (a bound: the triangle's box)
    start = 0
    while start < len(idx):
        stop = start + max(1, int(np.searchsorted(np.cumsum(estimate[start:]), CHUNK)))
        sel = idx[start:stop]
        start = stop
        # rows whose centre line crosses the triangle
        ys = corners[sel, :, 1]
        r0 = np.clip(np.ceil(ys.min(axis=1) - 0.5), 0, h).astype(np.int32)
        r1 = np.clip(np.ceil(ys.max(axis=1) - 0.5), 0, h).astype(np.int32)            # (exclusive)
        rows = np.maximum(r1 - r0, 0)
        tri = np.repeat(sel, rows)
        row = np.arange(int(rows.sum()), dtype=np.int32) - np.repeat((np.cumsum(rows) - rows).astype(np.int32), rows)
        row += np.repeat(r0, rows)
        yc = row.astype(np.float32) + np.float32(0.5)
        # where the row's centre line meets the three sides: the leftmost and rightmost
        left = np.full(len(tri), np.inf, np.float32)
        right = np.full(len(tri), -np.inf, np.float32)
        for i, j in ((0, 1), (1, 2), (2, 0)):
            p, q = corners[tri, i], corners[tri, j]
            lo_y, hi_y = np.minimum(p[:, 1], q[:, 1]), np.maximum(p[:, 1], q[:, 1])
            on = (yc >= lo_y) & (yc <= hi_y) & (hi_y > lo_y)
            with np.errstate(divide="ignore", invalid="ignore"):
                x = p[:, 0] + (yc - p[:, 1]) * (q[:, 0] - p[:, 0]) / (q[:, 1] - p[:, 1])
            left = np.where(on, np.minimum(left, x), left)
            right = np.where(on, np.maximum(right, x), right)
        c0 = np.clip(np.ceil(left - 0.5), 0, w).astype(np.int32)
        c1 = np.clip(np.ceil(right - 0.5), 0, w).astype(np.int32)                     # (exclusive)
        span = np.maximum(c1 - c0, 0)
        t = np.repeat(tri, span)
        px = np.arange(int(span.sum()), dtype=np.int32) - np.repeat((np.cumsum(span) - span).astype(np.int32), span)
        px += np.repeat(c0, span)
        py = np.repeat(row, span)
        d = A[t] * (px + np.float32(0.5)) + B[t] * (py + np.float32(0.5)) + C[t]
        ok = d >= keep_from
        np.minimum.at(zb, py[ok] * w + px[ok], d[ok])


def visible_parts(seg2d, segdepth, zb, tolerance):
    """The parts of segments that nothing hides: (K, 2, 2) pixel coordinates in, the visible
    pieces out (as fractions along each segment: (index, t0, t1) arrays). A sample is seen when
    its depth is at most the depth image's there + tolerance (it lies on the surface seen)."""
    seg2d = np.asarray(seg2d, dtype=float)
    segdepth = np.asarray(segdepth, dtype=float)
    h, w = zb.shape
    length = np.linalg.norm(seg2d[:, 1] - seg2d[:, 0], axis=1)
    n = np.maximum(np.ceil(length).astype(np.int64), 1) + 1                # samples per segment (~1 per pixel)
    owner = np.repeat(np.arange(len(seg2d)), n)
    local = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
    t = local / (n[owner] - 1)
    p = seg2d[owner, 0] + (seg2d[owner, 1] - seg2d[owner, 0]) * t[:, None]
    d = segdepth[owner, 0] + (segdepth[owner, 1] - segdepth[owner, 0]) * t
    px = np.clip(np.floor(p[:, 0]).astype(np.int64), 0, w - 1)
    py = np.clip(np.floor(p[:, 1]).astype(np.int64), 0, h - 1)
    # the farthest of the pixel and its four neighbours: a line along the outline of what is in
    # front of it stays (the pixel itself may already belong to the nearer surface)
    near = zb[py, px]
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        near = np.maximum(near, zb[np.clip(py + dy, 0, h - 1), np.clip(px + dx, 0, w - 1)])
    seen = d <= near + tolerance
    # runs of seen samples along each segment
    first = local == 0
    last = local == n[owner] - 1
    begins = seen & (first | ~np.roll(seen, 1))
    ends = seen & (last | ~np.roll(seen, -1))
    bi, ei = np.flatnonzero(begins), np.flatnonzero(ends)
    return owner[bi], t[bi], t[ei]


def hidden_lines_removed(triangles, edges, normal, offset, origin, u, v, resolution=RESOLUTION, with_index=False):
    """The edges (K, 2, 3) as a 2D drawing (metres along u and v) without what the triangles
    (T, 3, 3) hide, seen along `normal` with what is before the plane n·p = offset taken away
    (a section; for an elevation the plane is behind the viewer). Returns (M, 2, 2) — and, with_index, which
    edge each piece is of (M,)."""
    edges = np.asarray(edges, dtype=float).reshape(-1, 2, 3)
    if not len(edges):
        return (np.zeros((0, 2, 2)), np.zeros(0, dtype=np.int64)) if with_index else np.zeros((0, 2, 2))
    n = np.asarray(normal, dtype=float)
    e2 = flatten(edges, origin, u, v)
    lo, hi = e2.reshape(-1, 2).min(axis=0), e2.reshape(-1, 2).max(axis=0)
    pixel = max(float((hi - lo).max()) / resolution, 1e-4)                 # metres per pixel
    shape = (int((hi[1] - lo[1]) / pixel) + 2, int((hi[0] - lo[0]) / pixel) + 2)

    def to_px(p2):
        return (p2 - lo) / pixel

    tris = np.asarray(triangles, dtype=float).reshape(-1, 3, 3)
    zb = depth_image(to_px(flatten(tris, origin, u, v)), tris @ n, shape, offset) if len(tris) else \
        np.full(shape, np.inf)
    # a line lying on a surface seen at a slant changes depth by up to ~1 pixel per pixel
    index, t0, t1 = visible_parts(to_px(e2), edges @ n, zb, tolerance=0.01 + 2.0 * pixel)
    a, b = e2[index, 0], e2[index, 1]
    out = np.stack((a + (b - a) * t0[:, None], a + (b - a) * t1[:, None]), axis=1)
    keep = np.linalg.norm(out[:, 1] - out[:, 0], axis=1) > pixel * 0.5     # (dots are not lines)
    return (out[keep], np.asarray(index)[keep]) if with_index else out[keep]
