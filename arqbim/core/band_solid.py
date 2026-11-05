"""(0.383) The solid of walls being drawn by a rectangle, a face's outline, a circle or an arc, for its preview: the
band between its two faces raised to its height — the outer and inner faces, its top, its ends — as triangles, and its
edges as segments. (Before, only its two outlines at the foot and at the top were drawn: two flat rings, one over the
other, and no volume — the owner: «aparecem como 2 objetos separados, mas não se vê o volume».)

Pure geometry (numpy), no Qt, no GPU."""

import numpy as np


def ccw(ring):
    """The ring [(x, y)] turning counter-clockwise (reversed if it turned the other way)."""
    pts = [tuple(map(float, p[:2])) for p in ring]
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
    return pts if area >= 0 else pts[::-1]


def offset_ring(ring, d):
    """A counter-clockwise ring moved `d` outwards (d < 0: inwards), corner for corner — its sides parallel, its
    corners mitred — so that the two rings of a band match point for point."""
    pts = np.asarray([p[:2] for p in ring], dtype=float)
    n = len(pts)
    if n < 3 or abs(d) < 1e-12:
        return [tuple(p) for p in pts]
    edges = np.roll(pts, -1, axis=0) - pts
    lengths = np.linalg.norm(edges, axis=1)
    lengths[lengths < 1e-12] = 1.0
    normals = np.stack([edges[:, 1], -edges[:, 0]], axis=1) / lengths[:, None]     # (outwards, turning ccw)
    before = np.roll(normals, 1, axis=0)                     # the side ending at each corner
    cos = np.einsum("ij,ij->i", before, normals)
    mitre = (before + normals) / np.maximum(1.0 + cos, 0.1)[:, None]   # (a spike kept within ten times d)
    return [tuple(p) for p in pts + d * mitre]


def band_solid(outer, inner, z, height, closed=True, verticals=None):
    """The solid between two matching lines of points [(x, y)] — its outer and inner faces — from z to z + height:
    (triangles [(3, 3)…], segments [p, q, p, q…] — the lines at its foot and top, and the upright edges at
    `verticals`, indices: by default each point of a closed band, the two ends of an open one). Open (an arc): its
    two ends closed too."""
    outer = np.asarray([p[:2] for p in outer], dtype=float)
    inner = np.asarray([p[:2] for p in inner], dtype=float)
    n = min(len(outer), len(inner))
    if n < 2 or height <= 0:
        return [], []
    up = np.array((0.0, 0.0, height))

    def at(p, h=0.0):
        return np.array((p[0], p[1], z + h))

    ob, ib = [at(p) for p in outer[:n]], [at(p) for p in inner[:n]]
    ot, it = [p + up for p in ob], [p + up for p in ib]
    tris = []

    def quad(a, b, c, d):
        tris.extend((np.array((a, b, c)), np.array((a, c, d))))

    steps = range(n) if closed else range(n - 1)
    for i in steps:
        j = (i + 1) % n
        quad(ot[i], ot[j], it[j], it[i])                     # its top
        quad(ob[i], ob[j], ot[j], ot[i])                     # its outer face
        quad(ib[i], ib[j], it[j], it[i])                     # its inner face
    if not closed:
        for k in (0, n - 1):                                 # its ends
            quad(ob[k], ib[k], it[k], ot[k])
    segs = []
    for line in (ob, ib, ot, it):
        for i in steps:
            segs += [line[i], line[(i + 1) % n]]
    if verticals is None:
        verticals = range(n) if closed else (0, n - 1)
    for k in verticals:
        segs += [ob[k], ot[k], ib[k], it[k]]
    if not closed:
        segs += [ot[0], it[0], ot[n - 1], it[n - 1], ob[0], ib[0], ob[n - 1], ib[n - 1]]
    return tris, segs
