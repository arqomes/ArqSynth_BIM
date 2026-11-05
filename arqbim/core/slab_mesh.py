"""A slab's mesh of triangles (0.223, Phase 9, step 3: the slabs as shells): over its outline (its holes left out) —
an edge along a beam's axis just beside it moved onto it (a slab drawn to the beam's face) —, nodes along its edges, along the
beams under it and at the columns it rests on (shared with the frame: the beams cut at them), a square grid inside;
joined by Delaunay (GEOS), those inside kept, each counter-clockwise. The edges and the beams sampled no farther
apart than the grid, the inner grid kept half a step off them: their sides are the triangles' sides."""

import math

import numpy as np

SNAP = 1e-4                     # m: points this near are one
NEAR_HARD = 0.2                 # (× the size) an edge's point this near a beam's or a column's is left out for it
REACH = 0.40                    # m: a beam's axis this far outside the slab's edge: the slab meshed to it


def _cross(a, b):
    return float(a[0] * b[1] - a[1] * b[0])


def _samples(a, b, size):
    """Points from a to b no farther apart than size, both ends in."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    n = max(int(math.ceil(float(np.linalg.norm(b - a)) / size - 1e-9)), 1)
    return [tuple(a + (b - a) * k / n) for k in range(n + 1)]


def snapped(outline, lines=(), reach=REACH):
    """The outline with each edge that runs along a beam's axis (parallel, within reach, along half its length or
    more) moved onto it — the slab spanning to its beams' axes, as the analytical model has it."""
    pts = [np.asarray(p, dtype=float) for p in outline]
    if len(pts) > 3 and np.allclose(pts[0], pts[-1]):
        pts = pts[:-1]
    n = len(pts)
    if n < 3 or not lines:
        return [tuple(p) for p in pts]
    shifts = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        length = float(np.linalg.norm(b - a))
        best = None
        if length > SNAP:
            d = (b - a) / length
            normal = np.array((-d[1], d[0]))
            for p, q in lines:
                p, q = np.asarray(p, dtype=float), np.asarray(q, dtype=float)
                lb = float(np.linalg.norm(q - p))
                if lb <= SNAP or abs(float(_cross(d, (q - p) / lb))) > math.sin(math.radians(5.0)):
                    continue
                off = float((p - a) @ normal)
                if not SNAP < abs(off) <= reach:
                    continue
                t1, t2 = sorted((float((p - a) @ d), float((q - a) @ d)))
                if min(t2, length) - max(t1, 0.0) < 0.5 * min(length, lb):
                    continue
                if best is None or abs(off) < abs(best):
                    best = off
        shifts.append(normal * best if best is not None else np.zeros(2))
    out = []
    for i in range(n):                                      # (each corner where its two edges' lines now meet)
        a0, a1 = pts[i - 1] + shifts[i - 1], pts[i] + shifts[i - 1]
        b0, b1 = pts[i] + shifts[i], pts[(i + 1) % n] + shifts[i]
        da, db = a1 - a0, b1 - b0
        den = float(_cross(da, db))
        if abs(den) < 1e-12:
            out.append(tuple(pts[i] + (shifts[i - 1] + shifts[i]) / 2.0))
        else:
            s = float(_cross(b0 - a0, db)) / den
            out.append(tuple(a0 + da * s))
    return out


def domain(outline, holes=(), lines=(), reach=REACH):
    """The slab's area meshed: its outline (snapped to its beams' axes) less its holes."""
    from shapely.geometry import Polygon
    poly = Polygon(snapped(outline, lines, reach), [list(h) for h in holes])
    return poly if poly.is_valid else poly.buffer(0)


def mesh(outline, size=0.5, holes=(), lines=(), points=(), reach=REACH):
    """(vertices (N, 2), triangles [(i, j, k)] counter-clockwise) of a slab: outline [(x, y)], holes [[(x, y)]],
    size the step (m); lines [((x, y), (x, y))] the beams (the parts over the slab meshed through, each sampled from
    its ends: two slabs on one beam share its nodes), points [(x, y)] the columns."""
    import shapely
    from shapely import contains_xy, delaunay_triangles
    from shapely.geometry import LineString, MultiPoint
    area = domain(outline, holes, lines, reach)
    if area.is_empty or area.area <= 1e-9:
        return np.zeros((0, 2)), []
    grown = area.buffer(SNAP * 10)
    hard = [tuple(map(float, p)) for p in points if contains_xy(grown, float(p[0]), float(p[1]))]
    for a, b in lines:
        if LineString((a, b)).intersects(grown):
            hard += [q for q in _samples(a, b, size) if contains_xy(grown, q[0], q[1])]
    edge = []
    parts = [area] if area.geom_type == "Polygon" else [g for g in area.geoms if g.geom_type == "Polygon"]
    for g in parts:
        for ring in [g.exterior] + list(g.interiors):
            c = list(ring.coords)
            for a, b in zip(c[:-1], c[1:]):
                edge += _samples(a, b, size)[:-1]
    hard_arr = np.array(hard, dtype=float).reshape(-1, 2)
    if len(hard_arr) and edge:
        e = np.array(edge)
        near = np.min(np.hypot(e[:, None, 0] - hard_arr[None, :, 0], e[:, None, 1] - hard_arr[None, :, 1]), axis=1)
        edge = [q for q, d in zip(edge, near) if d > NEAR_HARD * size]
    x0, y0, x1, y1 = area.bounds
    gx, gy = np.meshgrid(np.arange(x0 + size, x1 - 1e-9, size), np.arange(y0 + size, y1 - 1e-9, size))
    grid = np.column_stack((gx.ravel(), gy.ravel()))
    if len(grid):
        grid = grid[contains_xy(area, grid[:, 0], grid[:, 1])]
    if len(grid):
        grid = grid[shapely.distance(area.boundary, shapely.points(grid)) >= 0.5 * size]
    if len(grid) and len(hard_arr):
        d = np.min(np.hypot(grid[:, None, 0] - hard_arr[None, :, 0], grid[:, None, 1] - hard_arr[None, :, 1]), axis=1)
        grid = grid[d >= 0.5 * size]
    vertices, index = [], {}
    for q in hard + edge + [tuple(q) for q in grid]:
        key = (round(q[0] / SNAP), round(q[1] / SNAP))
        if key not in index:
            index[key] = len(vertices)
            vertices.append((float(q[0]), float(q[1])))
    if len(vertices) < 3:
        return np.array(vertices).reshape(-1, 2), []
    verts = np.array(vertices)
    tris = []
    least = 1e-6 * size * size
    for t in delaunay_triangles(MultiPoint(vertices)).geoms:
        c = list(t.exterior.coords)[:3]
        ids = [index.get((round(x / SNAP), round(y / SNAP))) for x, y in c]
        if None in ids:
            continue
        (ax, ay), (bx, by), (cx, cy) = verts[ids]
        area2 = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
        if abs(area2) / 2.0 <= least:
            continue
        if not contains_xy(area, (ax + bx + cx) / 3.0, (ay + by + cy) / 3.0) or not grown.contains(t):
            continue
        tris.append(tuple(ids) if area2 > 0 else (ids[0], ids[2], ids[1]))
    used = sorted({i for t in tris for i in t})
    remap = {old: new for new, old in enumerate(used)}
    return verts[used], [tuple(remap[i] for i in t) for t in tris]
