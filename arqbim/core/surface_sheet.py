"""(0.550) A perforated sheet (a Visual Graph operator's) on a parametric surface (core/param_surface.Surface).

The surface is a grid of points (rows: v, columns: u). It is *unrolled* for the editor into a rectangle as wide as
its mean length along u and as high as its mean length along v — every cell of the grid the same flat rectangle, so a
hole is about its true size where the surface is neither stretched nor squeezed. The flat sheet (core/surfaces
.free_mesh, in that rectangle) is then cut along the grid's lines and along each cell's diagonal — the one the surface
itself is triangulated by — and each of its points put on the surface's own triangle, off it along the surface's
normal: within a triangle of the surface the sheet stays flat (no line drawn across it), and it folds where the
surface itself folds."""

import numpy as np

from . import surfaces
from .param_surface import grid_normals, kept

STAND_OFF = 0.0015          # m: the sheet's back off the surface (clear of it where both are drawn)


def _lengths(points, axis):
    return np.linalg.norm(np.diff(points, axis=axis), axis=-1).sum(axis=axis)


def flat_size(surface):
    """(width, height) of the surface unrolled: its mean length along u and along v (at least 5 cm each)."""
    rows = surface.rows
    if surface.close_u:
        rows = np.concatenate((rows, rows[:, :1]), axis=1)
    return max(float(_lengths(rows, 1).mean()), 0.05), max(float(_lengths(rows, 0).mean()), 0.05)


def _grid(surface):
    """(points (nr, nc', 3), normals alike) — a surface closed round in u with its first column again at the end."""
    rows = surface.rows
    normals = grid_normals(rows, surface.close_u)
    if surface.close_u:
        rows = np.concatenate((rows, rows[:, :1]), axis=1)
        normals = np.concatenate((normals, normals[:, :1]), axis=1)
    return rows, normals


def flat_face(surface):
    """The surface unrolled, shapely: its rectangle (its corner at (0, 0)) less the cells a trim took away."""
    from shapely.geometry import box
    from shapely.ops import unary_union
    rows, _n = _grid(surface)
    width, height = flat_size(surface)
    nr, nc = rows.shape[:2]
    face = box(0.0, 0.0, width, height)
    if surface.trims:
        mids = ((rows[:-1, :-1] + rows[:-1, 1:] + rows[1:, 1:] + rows[1:, :-1]) / 4.0)[:, :, :2].reshape(-1, 2)
        gone = ~np.asarray(kept(mids, surface.trims)).reshape(nr - 1, nc - 1)
        if gone.any():
            sx, sy = width / (nc - 1), height / (nr - 1)
            face = face.difference(unary_union([box(i * sx, j * sy, (i + 1) * sx, (j + 1) * sy)
                                                for j, i in zip(*np.nonzero(gone))]).buffer(1e-9))
    return face


def _split_diagonals(verts, tris, sx, sy, forward):
    """The triangles (each within one cell) cut along their cell's diagonal: `forward[j, i]` — the one from the
    cell's (0, 0) corner to its (1, 1) corner; else the other."""
    nr, nc = forward.shape
    mid = verts[tris].mean(axis=1)
    ci = np.clip(np.floor(mid[:, 0] / sx).astype(int), 0, nc - 1)
    cj = np.clip(np.floor(mid[:, 1] / sy).astype(int), 0, nr - 1)
    a = verts[:, 0][tris] / sx - ci[:, None]
    b = verts[:, 1][tris] / sy - cj[:, None]
    fwd = forward[cj, ci]
    side = np.where(fwd[:, None], a - b, a + b - 1.0)             # (0 on the diagonal)
    side = np.where(np.abs(side) < 1e-9, 0.0, side)
    crossing = (side.max(axis=1) > 0) & (side.min(axis=1) < 0)
    if not crossing.any():
        return verts, tris
    new_v, new_t, n = [], [], len(verts)

    def cut(p, q, sp, sq):
        if tuple(q) < tuple(p):
            p, q, sp, sq = q, p, sq, sp
        return p + (q - p) * (sp / (sp - sq))
    for tri, s in zip(tris[crossing], side[crossing]):
        pts = [verts[k] for k in tri]
        for sign in (1.0, -1.0):
            part = []
            for k in range(3):
                p, q, sp, sq = pts[k], pts[(k + 1) % 3], s[k] * sign, s[(k + 1) % 3] * sign
                if sp >= 0:
                    part.append(p)
                if (sp > 0 > sq) or (sp < 0 < sq):
                    part.append(cut(p, q, sp, sq))
            for k in range(1, len(part) - 1):
                new_v += [part[0], part[k], part[k + 1]]
                new_t.append((n, n + 1, n + 2))
                n += 3
    return np.vstack((verts, np.array(new_v))), np.vstack((tris[~crossing], np.array(new_t, dtype=np.int64)))


def cut_to_cells(surface, verts, tris):
    """A flat sheet's mesh (x, y in the unrolled rectangle, z off it) cut so that each triangle lies within one
    triangle of the surface."""
    rows, _n = _grid(surface)
    width, height = flat_size(surface)
    nr, nc = rows.shape[:2]
    sx, sy = width / (nc - 1), height / (nr - 1)
    verts, tris = surfaces.split_strips(verts, tris, sx)
    swapped, tris = surfaces.split_strips(verts[:, [1, 0, 2]], tris[:, ::-1], sy)       # (the same along y)
    verts, tris = swapped[:, [1, 0, 2]], tris[:, ::-1]
    d1 = ((rows[:-1, :-1] - rows[1:, 1:]) ** 2).sum(axis=-1)       # (as param_surface.triangulate: the shorter)
    d2 = ((rows[:-1, 1:] - rows[1:, :-1]) ** 2).sum(axis=-1)
    return _split_diagonals(verts, tris, sx, sy, d1 <= d2)


def to_surface(surface, xyz, out=1.0):
    """Points of the unrolled rectangle (x, y, z off it) on the surface (its own coordinates): on the surface's
    triangle under (x, y), z along the surface's normal there (`out` −1: the other way)."""
    rows, normals = _grid(surface)
    width, height = flat_size(surface)
    nr, nc = rows.shape[:2]
    xyz = np.asarray(xyz, dtype=float)
    u = np.clip(xyz[:, 0] / width, 0.0, 1.0) * (nc - 1)
    v = np.clip(xyz[:, 1] / height, 0.0, 1.0) * (nr - 1)
    i = np.clip(np.floor(u + 1e-9).astype(int), 0, nc - 2)
    j = np.clip(np.floor(v + 1e-9).astype(int), 0, nr - 2)
    a, b = np.clip(u - i, 0.0, 1.0)[:, None], np.clip(v - j, 0.0, 1.0)[:, None]
    forward = (((rows[:-1, :-1] - rows[1:, 1:]) ** 2).sum(axis=-1) <=
               ((rows[:-1, 1:] - rows[1:, :-1]) ** 2).sum(axis=-1))[j, i][:, None]

    def at(grid):
        p00, p10, p11, p01 = grid[j, i], grid[j, i + 1], grid[j + 1, i + 1], grid[j + 1, i]
        # the diagonal (0,0)–(1,1): the triangle under it (a ≥ b: p00 p10 p11) or over it (p00 p11 p01)
        fwd = np.where(a >= b, p00 + (p10 - p00) * a + (p11 - p10) * b, p00 + (p11 - p01) * a + (p01 - p00) * b)
        # the diagonal (1,0)–(0,1): the triangle by (0,0) (a + b ≤ 1: p00 p10 p01) or by (1,1) (p10 p11 p01)
        back = np.where(a + b <= 1.0, p00 + (p10 - p00) * a + (p01 - p00) * b,
                        p11 + (p01 - p11) * (1.0 - a) + (p10 - p11) * (1.0 - b))
        return np.where(forward, fwd, back)
    n = at(normals)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    return at(rows) + n * (out * xyz[:, 2:3])


def sheet(surface, shape, holes, margin, size, repeat, thickness, out=1.0, max_holes=None):
    """(vertices (surface's coordinates), triangles, how many holes, the holes' area) of a perforated sheet on the
    surface: free holes (surfaces.free_perforation's, on the unrolled rectangle) cut in it."""
    face = flat_face(surface)
    found = surfaces.free_perforation(face, shape, holes, margin, size, repeat)
    count = sum(len(c) for _q, c, _s in found)
    if max_holes is not None and count > max_holes:
        raise ValueError("pattern_many")
    verts, tris = surfaces.free_mesh(face, thickness, found, shape)
    if not len(tris):
        raise ValueError("too_small")
    verts, tris = surfaces.weld(*cut_to_cells(surface, verts, tris))
    verts = verts + (0.0, 0.0, STAND_OFF)
    area = sum(float(surfaces.hole_area(shape, s, surfaces.extras(s)[1]).sum()) for _q, _c, s in found)
    points = to_surface(surface, verts, out)
    if out < 0:
        tris = tris[:, ::-1]
    return points, tris, count, area
