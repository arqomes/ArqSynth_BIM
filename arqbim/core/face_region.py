"""(0.564, PLANO.md «Gerador de revestimentos», step 3) The flat face of an element round a point of it — the
triangles of its mesh in that plane joined into one polygon with its holes (a wall's face with its door and window
openings, a slab's edge, a column's side, a stair's tread) — what a Revestimento covers and follows. Pure geometry."""

import numpy as np
import shapely
from shapely.geometry import Point, Polygon
from shapely.geometry.polygon import orient

ON_PLANE = 1e-3            # m: a triangle this near the plane is in it
FACING = 0.9995            # cos: its normal this near the face's


def _frame(n):
    n = np.asarray(n, float)
    n = n / (np.linalg.norm(n) or 1.0)
    a = np.array((0.0, 0.0, 1.0)) if abs(n[2]) < 0.9 else np.array((1.0, 0.0, 0.0))
    x = np.cross(a, n)
    x /= np.linalg.norm(x)
    return x, np.cross(n, x), n


def clip_to_stretch(outline, holes, a, b, height):
    """(0.567) The parts of a face (3D outline and holes) between the two points a, b along it and from their level
    up `height` — a room's stretch of a wall's face: [(outline, holes)]."""
    from . import tiling as tl
    from shapely.geometry import box
    fr = tl.face_frame(outline)
    o, x, y, _n = fr
    flat = Polygon(tl.to_plane(outline, fr), [tl.to_plane(h, fr) for h in holes]).buffer(0)
    a, b = np.asarray(a, float), np.asarray(b, float)
    ua, ub = sorted((float((a - o) @ x), float((b - o) @ x)))
    z0 = float((a - o) @ y)
    cut = flat.intersection(box(ua, z0 - 1e-6, ub, z0 + float(height)))
    out = []
    for part in getattr(cut, "geoms", [cut]):
        if part.geom_type == "Polygon" and part.area > 1e-3:
            out.append((tl.to_space(list(part.exterior.coords)[:-1], fr),
                        [tl.to_space(list(h.coords)[:-1], fr) for h in part.interiors]))
    return out


def face_at(verts, tris, point, normal, reach=0.01):
    """(outline (N, 3), [holes (M, 3)…], normal) of the flat face of the mesh (verts (V, 3), tris (T, 3)) in the
    plane through `point` facing `normal`, the part of it the point is on (or nearest it, within `reach` — a face
    followed after a door was put where the point was) — None if there is none there."""
    v = np.asarray(verts, float)
    t = np.asarray(tris, np.int64).reshape(-1, 3)
    if not len(t):
        return None
    p0 = np.asarray(point, float)
    x, y, n = _frame(normal)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    nn = np.cross(b - a, c - a)
    ln = np.linalg.norm(nn, axis=1)
    ok = ln > 1e-12
    nn[ok] /= ln[ok, None]
    keep = ok & (nn @ n > FACING) & (np.abs((a - p0) @ n) < ON_PLANE) & (np.abs((b - p0) @ n) < ON_PLANE) \
        & (np.abs((c - p0) @ n) < ON_PLANE)
    if not keep.any():
        return None
    o = p0

    def flat(q):
        return np.column_stack(((q - o) @ x, (q - o) @ y))

    polys = [Polygon(np.vstack((flat(a[i:i + 1]), flat(b[i:i + 1]), flat(c[i:i + 1]))))
             for i in np.nonzero(keep)[0]]
    union = shapely.union_all(shapely.buffer(np.array(polys, dtype=object), 1e-6, join_style="mitre")).buffer(-1e-6,
                                                                                               join_style="mitre")
    here = Point(0.0, 0.0)
    parts = [g for g in getattr(union, "geoms", [union]) if g.geom_type == "Polygon" and g.area > 1e-6]
    if not parts:
        return None
    part = min(parts, key=lambda g: g.distance(here))
    if part.distance(here) > reach:
        return None
    part = orient(part.simplify(1e-5), 1.0)

    def space(ring):
        q = np.asarray(ring.coords)[:-1]
        return o + q[:, :1] * x + q[:, 1:2] * y

    return space(part.exterior), [space(r) for r in part.interiors], n
