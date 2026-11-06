"""(0.433) A slab (a floor) with a height of its own at each corner — a balcony falling to its drain, a floor with a
slope —, as the addon's «piso com declive por vértice»: its top a surface through its corners at their heights
(triangulated through the outline's corners), its holes' corners on that surface, its underside the same surface a
thickness lower (measured upright), its sides upright. Pure NumPy / shapely: (verts (N, 3), triangles (T, 3))."""

import numpy as np

FLAT = 1e-6                 # m: corners all within this of 0: a flat slab (its extrusion, as always)


def is_flat(offsets):
    return not offsets or all(abs(float(z)) <= FLAT for z in offsets)


def _area(ring):
    p = np.asarray(ring, dtype=float)
    return 0.5 * float(np.dot(p[:, 0], np.roll(p[:, 1], -1)) - np.dot(p[:, 1], np.roll(p[:, 0], -1)))


def _triangles(points):
    """Triangles (indices) of a simple polygon by its corners (shapely's constrained Delaunay, mapped back)."""
    import shapely
    from shapely.geometry import Polygon
    poly = Polygon(points)
    if not poly.is_valid:
        return []
    found = shapely.constrained_delaunay_triangles(poly)
    pts = np.asarray(points, dtype=float)
    out = []
    for tri in getattr(found, "geoms", ()):
        corners = np.asarray(tri.exterior.coords, dtype=float)[:3]
        idx = [int(np.argmin(np.hypot(pts[:, 0] - x, pts[:, 1] - y))) for x, y in corners]
        if len(set(idx)) == 3:
            out.append(idx)
    return out


def surface(outline, offsets):
    """height(x, y): the top's height (over the slab's top when flat) at a point — through the triangles of the
    outline's corners at their heights; outside them, the nearest corner's."""
    pts = np.asarray(outline, dtype=float)
    z = np.asarray(offsets, dtype=float)
    tris = _triangles([tuple(p) for p in pts])

    def height(x, y):
        for a, b, c in tris:
            pa, pb, pc = pts[a], pts[b], pts[c]
            m = np.array(((pb[0] - pa[0], pc[0] - pa[0]), (pb[1] - pa[1], pc[1] - pa[1])))
            det = np.linalg.det(m)
            if abs(det) < 1e-12:
                continue
            u, v = np.linalg.solve(m, (x - pa[0], y - pa[1]))
            if u >= -1e-9 and v >= -1e-9 and u + v <= 1 + 1e-9:
                return float(z[a] + u * (z[b] - z[a]) + v * (z[c] - z[a]))
        k = int(np.argmin(np.hypot(pts[:, 0] - x, pts[:, 1] - y)))
        return float(z[k])
    return height


def body(outline, holes, offsets, thickness):
    """(verts (N, 3), triangles (T, 3)) of the slab's solid, in its own frame — z 0 its underside where flat: its top
    at `thickness` + each corner's offset. The holes' corners on the top's surface."""
    import shapely
    from shapely.geometry import Polygon
    height = surface(outline, offsets)
    rings = [[tuple(map(float, p)) for p in outline]] + [[tuple(map(float, p)) for p in h] for h in holes]
    for k, ring in enumerate(rings):                    # (the outline counter-clockwise, the holes clockwise)
        if (_area(ring) < 0) == (k == 0):
            ring.reverse()
    flat = [p for ring in rings for p in ring]
    poly = Polygon(rings[0], rings[1:])
    if not poly.is_valid:
        poly = poly.buffer(0)
    pts = np.asarray(flat, dtype=float)
    top_z = np.array([thickness + height(x, y) for x, y in flat])
    n = len(flat)
    verts = np.vstack((np.column_stack((pts, top_z)), np.column_stack((pts, top_z - thickness))))
    tris = []
    for tri in getattr(shapely.constrained_delaunay_triangles(poly), "geoms", ()):
        corners = np.asarray(tri.exterior.coords, dtype=float)[:3]
        idx = [int(np.argmin(np.hypot(pts[:, 0] - x, pts[:, 1] - y))) for x, y in corners]
        if len(set(idx)) < 3:
            continue
        a, b, c = idx
        u, w = pts[b] - pts[a], pts[c] - pts[a]
        if u[0] * w[1] - u[1] * w[0] < 0:
            b, c = c, b
        tris.append((a, b, c))                          # (the top, looking up)
        tris.append((a + n, c + n, b + n))              # (the underside, looking down)
    start = 0
    for ring in rings:                                  # (the sides, upright, looking out: the right of each side —
        m = len(ring)                                   #  out of the outline, into a hole — the rings so turned)
        for i in range(m):
            p, q = start + i, start + (i + 1) % m
            tris += [(p, q + n, q), (p, p + n, q + n)]
        start += m
    return verts, np.array(tris, dtype=np.int64)
