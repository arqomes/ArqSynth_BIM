"""What a selection region on the screen takes (0.75): a box, a free lasso, a polygon clicked point by
point — or a fence, a line drawn across things. Pure numpy, on screen points (pixels), no GPU.

As in AutoCAD, Revit and SketchUp:
- "window" (drawn from left to right): what lies wholly inside the region;
- "crossing" (from right to left): what lies inside it or touches its border;
- "fence": what the line crosses (or a point of it lies on).

An object is given as its points on the screen (NaN where behind the camera) and its triangles or
its line segments (vertex indices)."""

import numpy as np

WINDOW, CROSSING, FENCE = "window", "crossing", "fence"
MIN_LASSO_STEP_PX = 4.0          # a lasso keeps a point every this many pixels (fewer edges to test)


def thin_path(points, step=MIN_LASSO_STEP_PX):
    """A free-hand path with its points at least `step` pixels apart (the last one kept)."""
    pts = [np.asarray(p, dtype=float) for p in points]
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    for p in pts[1:-1]:
        if np.linalg.norm(p - out[-1]) >= step:
            out.append(p)
    out.append(pts[-1])
    return out


def mode_of(points):
    """A box or a lasso drawn rightwards picks what is wholly inside (window); leftwards, what it
    touches (crossing) — told by where it went first, sideways."""
    for p in points[1:]:
        dx = p[0] - points[0][0]
        if abs(dx) > 1e-9:
            return WINDOW if dx > 0 else CROSSING
    return WINDOW


def points_in_polygon(pts, poly):
    """(N,) bool: each point inside the closed polygon (even-odd rule; on an edge counts as inside)."""
    pts = np.asarray(pts, dtype=float).reshape(-1, 2)
    poly = np.asarray(poly, dtype=float).reshape(-1, 2)
    if not len(pts) or len(poly) < 3:
        return np.zeros(len(pts), dtype=bool)
    x, y = pts[:, 0:1], pts[:, 1:2]
    a, b = poly, np.roll(poly, -1, axis=0)
    ax, ay, bx, by = a[:, 0], a[:, 1], b[:, 0], b[:, 1]
    with np.errstate(divide="ignore", invalid="ignore"):
        cross_x = ax + (y - ay) * (bx - ax) / (by - ay)
    inside = (((ay > y) != (by > y)) & (x < cross_x)).sum(axis=1) % 2 == 1
    # on an edge: inside
    ex, ey = bx - ax, by - ay
    length2 = np.maximum(ex * ex + ey * ey, 1e-18)
    t = np.clip(((x - ax) * ex + (y - ay) * ey) / length2, 0.0, 1.0)
    d2 = (ax + t * ex - x) ** 2 + (ay + t * ey - y) ** 2
    return inside | (d2 < 1e-12).any(axis=1)


def segments_cross(p1, p2, q1, q2):
    """True if any segment p1[i]→p2[i] meets any segment q1[j]→q2[j] (touching counts)."""
    p1, p2 = np.asarray(p1, float).reshape(-1, 1, 2), np.asarray(p2, float).reshape(-1, 1, 2)
    q1, q2 = np.asarray(q1, float).reshape(1, -1, 2), np.asarray(q2, float).reshape(1, -1, 2)
    if not p1.shape[0] or not q1.shape[1]:
        return False

    def orient(a, b, c):
        return (b[..., 0] - a[..., 0]) * (c[..., 1] - a[..., 1]) - (b[..., 1] - a[..., 1]) * (c[..., 0] - a[..., 0])

    d1, d2 = orient(q1, q2, p1), orient(q1, q2, p2)
    d3, d4 = orient(p1, p2, q1), orient(p1, p2, q2)
    proper = (d1 * d2 <= 0) & (d3 * d4 <= 0)
    # collinear pieces: they must overlap (both orientations 0 and the boxes overlapping)
    flat = (d1 == 0) & (d2 == 0)
    if flat.any():
        lo_p, hi_p = np.minimum(p1, p2), np.maximum(p1, p2)
        lo_q, hi_q = np.minimum(q1, q2), np.maximum(q1, q2)
        overlap = (lo_p <= hi_q).all(axis=-1) & (lo_q <= hi_p).all(axis=-1)
        proper = np.where(flat, overlap, proper)
    return bool(proper.any())


def points_in_triangles(pts, tri):
    """True if any point lies in any triangle (tri: (T, 3, 2))."""
    pts = np.asarray(pts, float).reshape(-1, 1, 2)
    tri = np.asarray(tri, float).reshape(1, -1, 3, 2)
    if not pts.shape[0] or not tri.shape[1]:
        return False
    a, b, c = tri[..., 0, :], tri[..., 1, :], tri[..., 2, :]

    def side(p, q, r):
        return (q[..., 0] - p[..., 0]) * (r[..., 1] - p[..., 1]) - (q[..., 1] - p[..., 1]) * (r[..., 0] - p[..., 0])

    s1, s2, s3 = side(a, b, pts), side(b, c, pts), side(c, a, pts)
    has_neg = (s1 < 0) | (s2 < 0) | (s3 < 0)
    has_pos = (s1 > 0) | (s2 > 0) | (s3 > 0)
    return bool((~(has_neg & has_pos)).any())


def _edges(xy, tris, segs):
    """The object's edges on the screen: (start points, end points), NaN ones left out."""
    pairs = []
    if tris is not None and len(tris):
        t = np.asarray(tris, dtype=np.int64).reshape(-1, 3)
        pairs.append(np.concatenate((t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]])))
    if segs is not None and len(segs):
        pairs.append(np.asarray(segs, dtype=np.int64).reshape(-1, 2))
    if not pairs:
        return np.zeros((0, 2)), np.zeros((0, 2))
    e = np.concatenate(pairs)
    a, b = xy[e[:, 0]], xy[e[:, 1]]
    ok = ~(np.isnan(a).any(axis=1) | np.isnan(b).any(axis=1))
    return a[ok], b[ok]


def takes(xy, region, mode, tris=None, segs=None):
    """Does the region (screen polygon; the fence: an open line) take the object whose screen points are
    `xy` (N, 2; NaN behind the camera), with triangles `tris` and/or line segments `segs`?"""
    xy = np.asarray(xy, dtype=float).reshape(-1, 2)
    region = np.asarray(region, dtype=float).reshape(-1, 2)
    valid = ~np.isnan(xy).any(axis=1)
    if not valid.any() or len(region) < 2:
        return False
    if mode == WINDOW:
        return bool(valid.all() and points_in_polygon(xy, region).all())
    lo, hi = xy[valid].min(axis=0), xy[valid].max(axis=0)
    rlo, rhi = region.min(axis=0), region.max(axis=0)
    if (lo > rhi).any() or (hi < rlo).any():
        return False                                   # (their boxes do not even meet)
    if mode == CROSSING:
        if len(region) >= 3 and points_in_polygon(xy[valid], region).any():
            return True
        r1, r2 = region, np.roll(region, -1, axis=0)
    else:                                              # a fence: its own segments, not closed
        r1, r2 = region[:-1], region[1:]
    a, b = _edges(xy, tris, segs)
    if segments_cross(a, b, r1, r2):
        return True
    if tris is not None and len(tris):                 # the region (or the fence) inside a face
        t = np.asarray(tris, dtype=np.int64).reshape(-1, 3)
        t = t[valid[t].all(axis=1)]
        return points_in_triangles(region, xy[t])
    return False
