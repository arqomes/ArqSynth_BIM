"""Clashes between two meshes (0.149, Phase 6, step 6): do two closed triangle meshes go into each other? — an edge
of one going through a face of the other (a pipe through a beam: the pipe's long edges cross the beam's faces, the
beam's edges cross the pipe's), or one wholly inside the other (a thin pipe in a thick slab). Touching (a face on a
face, an edge ending on a face) is not a clash: the edges are taken without their ends, the faces without their
borders (by a small margin).

Pure numpy, vectorised (no loop per triangle)."""

import numpy as np

MARGIN = 1e-4               # m: how far into the other an edge must go to count (touching is not a clash)


def boxes_overlap(a, b, margin=0.0):
    """Do two boxes (lowest, highest corner) overlap (by more than `margin`)?"""
    return bool(np.all(np.asarray(a[0]) < np.asarray(b[1]) - margin) and np.all(np.asarray(b[0]) < np.asarray(a[1]) - margin))


def edges_through(p, q, tris, margin=MARGIN):
    """Which of the segments p[i] → q[i] go through one of the triangles (T, 3, 3) — not at their ends, not at the
    triangles' borders. Returns a boolean (E,) array, and the first point of each that does (E, 3)."""
    p, q, tris = np.asarray(p, float), np.asarray(q, float), np.asarray(tris, float)
    hit = np.zeros(len(p), dtype=bool)
    where = np.zeros((len(p), 3))
    if not len(p) or not len(tris):
        return hit, where
    d = q - p                                                  # (E, 3)
    length = np.linalg.norm(d, axis=1)
    v0, e1, e2 = tris[:, 0], tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]    # (T, 3)
    area = np.linalg.norm(np.cross(e1, e2), axis=1)                                # (T,)
    for start in range(0, len(p), 256):                        # (in chunks: E × T stays small)
        dd, pp, ll = d[start:start + 256], p[start:start + 256], length[start:start + 256]
        h = np.cross(dd[:, None, :], e2[None, :, :])           # (e, T, 3)
        a = np.einsum("ijk,jk->ij", h, e1)                     # (e, T)
        ok = np.abs(a) > 1e-12
        f = np.where(ok, 1.0 / np.where(ok, a, 1.0), 0.0)
        s = pp[:, None, :] - v0[None, :, :]
        u = f * np.einsum("ijk,ijk->ij", s, h)
        qv = np.cross(s, e1[None, :, :])
        v = f * np.einsum("ik,ijk->ij", dd, qv)
        t = f * np.einsum("jk,ijk->ij", e2, qv)
        # (a margin in metres along the edge and inside the face: touching is not going through)
        tm = MARGIN / np.maximum(ll, 1e-12)[:, None]
        bm = margin * (np.linalg.norm(e1, axis=1) + np.linalg.norm(e2, axis=1))[None, :] / np.maximum(area, 1e-12)[None, :]
        inside = ok & (u > bm) & (v > bm) & (u + v < 1.0 - bm) & (t > tm) & (t < 1.0 - tm)
        rows = inside.any(axis=1)
        hit[start:start + 256] = rows
        first = np.argmax(inside, axis=1)
        tt = t[np.arange(len(dd)), first]
        where[start:start + 256] = pp + dd * tt[:, None]
    return hit, where


def inside_mesh(points, tris):
    """Which points are inside the closed mesh (T, 3, 3): a ray along a slanted direction, counted crossings odd."""
    points, tris = np.asarray(points, float), np.asarray(tris, float)
    if not len(points) or not len(tris):
        return np.zeros(len(points), dtype=bool)
    ray = np.array((0.5773, 0.5774, 0.5773))
    out = np.zeros(len(points), dtype=bool)
    v0, e1, e2 = tris[:, 0], tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]
    h = np.cross(ray[None, :], e2)                             # (T, 3)
    a = np.einsum("ij,ij->i", e1, h)
    ok = np.abs(a) > 1e-12
    f = np.where(ok, 1.0 / np.where(ok, a, 1.0), 0.0)
    for k, pt in enumerate(points):
        s = pt - v0
        u = f * np.einsum("ij,ij->i", s, h)
        qv = np.cross(s, e1)
        v = f * (qv @ ray)
        t = f * np.einsum("ij,ij->i", e2, qv)
        out[k] = int(np.count_nonzero(ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9))) % 2 == 1
    return out


def clash(mesh_a, mesh_b):
    """Where two meshes (verts (N, 3), tris (T, 3) each) go into each other: a point (3,), or None."""
    va, ta = np.asarray(mesh_a[0], float), np.asarray(mesh_a[1], int)
    vb, tb = np.asarray(mesh_b[0], float), np.asarray(mesh_b[1], int)
    if not len(ta) or not len(tb):
        return None
    tris_a, tris_b = va[ta], vb[tb]
    for verts, tris, other in ((va, ta, tris_b), (vb, tb, tris_a)):
        pairs = np.unique(np.sort(np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), axis=1), axis=0)
        hit, where = edges_through(verts[pairs[:, 0]], verts[pairs[:, 1]], other)
        if hit.any():
            return where[np.argmax(hit)]
    # (one wholly in the other: its middle inside it)
    for verts, other in ((va, tris_b), (vb, tris_a)):
        middle = verts.mean(axis=0)
        if inside_mesh(middle[None, :], other)[0]:
            return middle
    return None
