"""Polygon mesh for sketch geometry.

Faces are lists of vertex indices, counter-clockwise seen from outside, so the
normal follows the right-hand rule. Only convex faces for now (rectangles and
the quads Push/Pull creates); display triangulation is a simple fan.
"""

import math

import numpy as np

SMOOTH_DEG = 20.0          # a bend smaller than this between the strips of a curved surface: no edge drawn…
SMOOTH_FAMILY = 3          # …when at least this many parallel edges bend the same (a tessellated curve)
SMOOTH_SURFACE = 12        # …or this many, whatever their direction (0.136: a surface curved both ways, a bend's)
WELD = 1e-5                # m: (0.257) corners closer than this are one (planar_union)


def polygon_normal(pts):
    """Unit normal of a planar polygon (Newell's method, robust for any shape)."""
    pts = np.asarray(pts, dtype=float)
    nxt = np.roll(pts, -1, axis=0)
    n = np.array([
        np.sum((pts[:, 1] - nxt[:, 1]) * (pts[:, 2] + nxt[:, 2])),
        np.sum((pts[:, 2] - nxt[:, 2]) * (pts[:, 0] + nxt[:, 0])),
        np.sum((pts[:, 0] - nxt[:, 0]) * (pts[:, 1] + nxt[:, 1])),
    ])
    length = np.linalg.norm(n)
    return n / length if length > 0 else n


def edge_key(a, b):
    return (a, b) if a < b else (b, a)


def triangulate_polygon(pts):
    """Triangles (index triples into pts) covering a simple planar polygon,
    convex or not (ear clipping), with the polygon's own winding."""
    n = len(pts)
    if n < 3:
        return []
    pts = np.asarray(pts, dtype=float)
    normal = polygon_normal(pts)
    drop = int(np.argmax(np.abs(normal)))
    p = pts[:, [i for i in range(3) if i != drop]]
    area2 = sum(p[i, 0] * p[(i + 1) % n, 1] - p[(i + 1) % n, 0] * p[i, 1] for i in range(n))
    idx = list(range(n)) if area2 >= 0 else list(range(n))[::-1]   # work counter-clockwise

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    tris = []
    while len(idx) > 3:
        m = len(idx)
        for k in range(m):
            i0, i1, i2 = idx[(k - 1) % m], idx[k], idx[(k + 1) % m]
            a, b, c = p[i0], p[i1], p[i2]
            if cross(a, b, c) <= 1e-12:
                continue                     # reflex corner: not an ear
            if any(cross(a, b, p[j]) >= -1e-12 and cross(b, c, p[j]) >= -1e-12 and cross(c, a, p[j]) >= -1e-12
                   for j in idx if j not in (i0, i1, i2)):
                continue                     # another corner inside: not an ear
            tris.append((i0, i1, i2))
            idx.pop(k)
            break
        else:
            break                            # degenerate polygon: keep what we have
    if len(idx) == 3:
        tris.append(tuple(idx))
    if area2 < 0:
        tris = [(a, c, b) for a, b, c in tris]   # back to the polygon's own winding
    return tris


def is_convex_polygon(pts):
    pts = np.asarray(pts, dtype=float)
    n = polygon_normal(pts)
    k = len(pts)
    return all(np.cross(pts[(i + 1) % k] - pts[i], pts[(i + 2) % k] - pts[(i + 1) % k]).dot(n) >= -1e-12
               for i in range(k))


class PolyMesh:
    def __init__(self, verts=(), faces=(), hidden=(), voids=(), lines=(), paint=()):
        self.verts = [np.array(v, dtype=float) for v in verts]
        self.faces = [list(f) for f in faces]
        # (0.392) Each face's paint (the Paint bucket, as SketchUp's): a material key, or None (its own colour).
        self.paint = [p or None for p in list(paint)[:len(self.faces)]]
        self.paint += [None] * (len(self.faces) - len(self.paint))
        # Edges not drawn: helper splits between coplanar faces (SketchUp shows
        # an imprinted rectangle as a face with a hole; we split the host face instead).
        self.hidden = set(hidden)
        # Through-holes made by Push/Pull: (front polygon points, through vector), in
        # object space. Kept so that Classify can turn them into IFC openings.
        self.voids = [([np.array(p, dtype=float) for p in pts], np.array(vec, dtype=float))
                      for pts, vec in voids]
        # Loose edges (no face): lines drawn with the Line tool that do not close a face.
        self.lines = [tuple(e) for e in lines]

    def copy(self):
        return PolyMesh(self.verts, self.faces, self.hidden, self.voids, self.lines, self.painted())

    def add_vert(self, co):
        self.verts.append(np.array(co, dtype=float))
        return len(self.verts) - 1

    def add_face(self, indices, paint=None):
        """(0.392) paint: the new face's (a piece of a painted face keeps its paint), else none."""
        self.painted()
        self.faces.append(list(indices))
        self.paint.append(paint or None)
        return len(self.faces) - 1

    def remove_face(self, fi):
        """Removes the face only; vertices stay (indices of later faces shift)."""
        self.painted()
        del self.faces[fi]
        del self.paint[fi]

    def painted(self):
        """(0.392) The faces' paint, one per face (kept as long as the faces' list, whatever changed it)."""
        paint = getattr(self, "paint", None)
        if paint is None:
            paint = self.paint = []
        if len(paint) != len(self.faces):
            del paint[len(self.faces):]
            paint += [None] * (len(self.faces) - len(paint))
        return paint

    def paint_of(self, fi):
        paint = self.painted()
        return paint[fi] if 0 <= fi < len(paint) else None

    def flip_face(self, fi):
        self.faces[fi].reverse()

    # ------------------------------------------------------------ geometry

    def face_points(self, fi):
        return np.array([self.verts[i] for i in self.faces[fi]])

    def face_normal(self, fi):
        return polygon_normal(self.face_points(fi))

    def face_area(self, fi):
        pts = self.face_points(fi)
        total = np.zeros(3)
        for i in range(1, len(pts) - 1):
            total += np.cross(pts[i] - pts[0], pts[i + 1] - pts[0])
        return 0.5 * np.linalg.norm(total)

    def volume(self):
        """Signed volume; positive when the mesh is closed with outward normals."""
        vol = 0.0
        for f in self.faces:
            p0 = self.verts[f[0]]
            for i in range(1, len(f) - 1):
                vol += np.dot(p0, np.cross(self.verts[f[i]], self.verts[f[i + 1]]))
        return vol / 6.0

    # ------------------------------------------------------------ topology

    def edge_faces(self):
        """{(a, b) with a < b: [face indices]}"""
        out = {}
        for fi, f in enumerate(self.faces):
            for i in range(len(f)):
                out.setdefault(edge_key(f[i], f[(i + 1) % len(f)]), []).append(fi)
        return out

    def visible_edges(self):
        out = {e: fis for e, fis in self.edge_faces().items() if e not in self.hidden}
        for a, b in self.lines:
            out.setdefault(edge_key(a, b), [])
        return out

    def is_closed(self):
        """Every edge shared by exactly two faces, traversed in opposite directions
        (i.e. a watertight solid with consistent normals)."""
        if not self.faces:
            return False
        directed = {}
        for f in self.faces:
            for i in range(len(f)):
                key = (f[i], f[(i + 1) % len(f)])
                if key in directed:
                    return False
                directed[key] = True
        return all((b, a) in directed for (a, b) in directed)

    def faces_using_verts(self, vert_ids):
        vert_ids = set(vert_ids)
        return [fi for fi, f in enumerate(self.faces) if vert_ids.intersection(f)]

    # ------------------------------------------------------------ display

    def triangulate(self):
        """(triangles as (T, 3) vertex indices, owning face index per triangle)."""
        tris, owner = [], []
        for fi, f in enumerate(self.faces):
            pts = [self.verts[i] for i in f]
            if len(f) == 3 or is_convex_polygon(pts):
                local = [(0, i, i + 1) for i in range(1, len(f) - 1)]
            else:
                local = triangulate_polygon(pts)     # e.g. an L-shaped room
            for a, b, c in local:
                tris.append((f[a], f[b], f[c]))
                owner.append(fi)
        return np.array(tris, dtype=np.int64).reshape(-1, 3), np.array(owner, dtype=np.int64)

    def transformed(self, matrix):
        m = np.asarray(matrix, dtype=float)
        verts = [(m @ np.append(v, 1.0))[:3] for v in self.verts]
        voids = [([(m @ np.append(p, 1.0))[:3] for p in pts], m[:3, :3] @ vec) for pts, vec in self.voids]
        return PolyMesh(verts, self.faces, self.hidden, voids, self.lines, self.painted())


def triangle_normals(verts, tris):
    """Unit normal of each triangle (zero-area triangles: not normalised)."""
    p = verts[tris]
    n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    length = np.linalg.norm(n, axis=1)
    return n / np.where(length > 0, length, 1.0)[:, None]


def slice_triangles(tris, normal, levels, eps=1e-6):
    """(0.315) Triangles (T, 3, 3) cut along the planes normal·p = each level (a wall's top across its layers): (the
    pieces (K, 3, 3), each turned as its triangle, and the triangle each came from (K,)). Those no plane crosses
    stay as they are."""
    tris = np.asarray(tris, dtype=float).reshape(-1, 3, 3)
    n = np.asarray(normal, dtype=float)
    depth = tris @ n
    lo, hi = depth.min(axis=1), depth.max(axis=1)
    levels = np.sort(np.asarray(levels, dtype=float))
    crossed = np.array([np.any((levels > a + eps) & (levels < b - eps)) for a, b in zip(lo, hi)], dtype=bool) \
        if len(tris) else np.zeros(0, dtype=bool)
    pieces, parent = [tris[~crossed]], [np.flatnonzero(~crossed)]
    for k in np.flatnonzero(crossed):
        cuts = [float(c) for c in levels if lo[k] + eps < c < hi[k] - eps]
        for a, b in zip([-np.inf] + cuts, cuts + [np.inf]):
            poly = _clip_side(_clip_side(list(tris[k]), n, a, 1.0), n, b, -1.0)
            if len(poly) >= 3:
                fan = np.array([(poly[0], poly[i], poly[i + 1]) for i in range(1, len(poly) - 1)])
                pieces.append(fan)
                parent.append(np.full(len(fan), k))
    return np.concatenate(pieces), np.concatenate(parent).astype(np.int64)


def _clip_side(poly, n, level, side):
    """A polygon's part where side·(n·p - level) >= 0 (Sutherland–Hodgman, one plane)."""
    if not np.isfinite(level) or not poly:
        return poly
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        dp, dq = side * (p @ n - level), side * (q @ n - level)
        if dp >= 0:
            out.append(p)
        if (dp >= 0) != (dq >= 0):
            out.append(p + (q - p) * (dp / (dp - dq)))
    return out


def planar_union(verts, tris, grid=1e-7):
    """(0.257) The outer surface of solids that touch or overlap only along planes — a stair's flights and its landing
    — as one surface: in each plane, the faces turned the same way joined, those turned against each other (where two
    of the solids touch) taken away from both, and what is left triangulated again with its corners shared. So no
    seam is drawn where two of them meet flush, and nothing where one touches another. (verts, tris)."""
    import shapely
    v = np.asarray(verts, dtype=float).reshape(-1, 3)
    t = np.asarray(tris, dtype=np.int64).reshape(-1, 3)
    p = v[t]
    cross = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    size = np.linalg.norm(cross, axis=1)
    keep = size > 1e-12
    p, n, kept = p[keep], cross[keep] / size[keep][:, None], t[keep]
    if not len(p):
        return v, t
    lead = np.argmax(np.abs(n) > 1e-6, axis=1)                  # (each plane once, whichever way its faces turn)
    turn = np.sign(n[np.arange(len(n)), lead])
    axis = n * turn[:, None]
    offset = np.einsum("ij,ij->i", axis, p[:, 0])
    keys = np.column_stack((np.round(axis, 4), np.round(offset, 4))) + 0.0      # (+ 0.0: no −0.0 apart from 0.0)
    _u, group = np.unique(keys, axis=0, return_inverse=True)
    out_pts, out_tris = [], []
    for g in range(group.max() + 1):
        mine = np.flatnonzero(group.reshape(-1) == g)
        if len(mine) == 1 or (len(mine) == 2 and turn[mine[0]] == turn[mine[1]] and
                              len(set(kept[mine[0]]) & set(kept[mine[1]])) == 2):
            k = len(out_pts)                                     # (0.312) a face alone in its plane — a quad, a
            out_pts += list(p[mine].reshape(-1, 3))              # triangle —: as it is, nothing to join
            out_tris += [(k + 3 * i, k + 3 * i + 1, k + 3 * i + 2) for i in range(len(mine))]
            continue
        normal = axis[mine].mean(axis=0)
        normal /= np.linalg.norm(normal)
        u = np.cross(normal, (1.0, 0.0, 0.0) if abs(normal[0]) < 0.9 else (0.0, 1.0, 0.0))
        u /= np.linalg.norm(u)
        w = np.cross(normal, u)                                  # (u × w = the normal: counter-clockwise faces it)
        base = normal * float(offset[mine].mean())
        sides = {}
        for s in (1.0, -1.0):
            these = mine[turn[mine] == s]
            if len(these):
                q = p[these] - base
                flat = shapely.polygons(np.stack((q @ u, q @ w), axis=-1))
                sides[s] = shapely.union_all(flat[shapely.area(flat) > 1e-14], grid_size=grid)
        for s, region in sides.items():
            other = sides.get(-s)
            if other is not None and not other.is_empty:
                region = shapely.difference(region, other, grid_size=grid)
            region = region.simplify(0.0)                       # (no corner in the middle of a straight side)
            if region.is_empty:
                continue
            for tri in shapely.constrained_delaunay_triangles(region).geoms:
                if tri.area < 1e-12:
                    continue
                c = np.asarray(tri.exterior.coords, dtype=float)[:3]
                if (c[1, 0] - c[0, 0]) * (c[2, 1] - c[0, 1]) - (c[1, 1] - c[0, 1]) * (c[2, 0] - c[0, 0]) < 0:
                    c = c[::-1]                                  # (counter-clockwise: turned as `normal`)
                if s < 0:
                    c = c[::-1]                                  # (…or against it)
                k = len(out_pts)
                out_pts += [base + a * u + b * w for a, b in c]
                out_tris.append((k, k + 1, k + 2))
    if not out_tris:
        return v, t
    pts = np.array(out_pts)
    _k, first, inverse = np.unique(_welded(pts), return_index=True, return_inverse=True)     # (the corners the
    tris = inverse.reshape(-1)[np.array(out_tris)]                                             # planes share: one)
    tris = tris[(tris[:, 0] != tris[:, 1]) & (tris[:, 1] != tris[:, 2]) & (tris[:, 2] != tris[:, 0])]   # (a sliver
    return _mend(pts[first], tris)                              # between two corners a hair apart: gone)


def _welded(pts, size=WELD):
    """(0.312) Each point's label (the lowest index of those it is one with): the points in one cell of a grid `size`
    wide; and two a hair apart on either side of a cell's wall (an arch's corner reached by two ways), so near a wall
    that they are looked for among all — each such point one with all those closer than half `size`."""
    scaled = pts / size
    _k, first, cell = np.unique(np.round(scaled).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    label = first[cell.reshape(-1)]
    for i in np.flatnonzero(np.any(np.abs(scaled - np.floor(scaled) - 0.5) < 0.25, axis=1)):
        close = np.flatnonzero(np.einsum("ij,ij->i", pts - pts[i], pts - pts[i]) < (size / 2) ** 2)
        groups = np.unique(label[close])
        if len(groups) > 1:
            label[np.isin(label, groups)] = groups[0]
    return label


def _mend(verts, tris, gap=1e-7):
    """(0.312) The T-junctions of planar_union mended: a corner of one plane's faces in the middle of a side of
    another's (each plane is triangulated apart) splits that side's triangle, so every edge has its two triangles — a
    closed solid stays closed (IFC's Closed face set; the schedules' volumes). (verts, tris)."""
    tris = np.asarray(tris, dtype=np.int64).reshape(-1, 3)
    for _round in range(3):
        directed = np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
        _u, inverse, counts = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
        splits = {}                                              # {triangle: {its side: the corners on it, in order}}
        for d in np.flatnonzero(counts[inverse.reshape(-1)] == 1):
            a, b = directed[d]
            ab = verts[b] - verts[a]
            length = float(np.linalg.norm(ab))
            if length < 2 * gap:
                continue
            along = (verts - verts[a]) @ (ab / length)
            off = np.linalg.norm(verts - verts[a] - np.outer(along, ab / length), axis=1)
            on = np.flatnonzero((along > gap) & (along < length - gap) & (off < gap))
            if len(on):
                splits.setdefault(d % len(tris), {})[d // len(tris)] = on[np.argsort(along[on])]
        if not splits:
            break
        new = []
        for ti, sides in splits.items():
            corners = tris[ti]
            ring = []
            for k in range(3):                                   # (round the triangle, as it turns)
                ring += [int(corners[k])] + [int(i) for i in sides.get(k, ())]
            if len(sides) == 1:                                  # one side split: a fan from the corner across
                k = next(iter(sides))
                apex = int(corners[(k + 2) % 3])
                start = ring.index(apex)
                ring = ring[start:] + ring[:start]
                new += [(apex, ring[i], ring[i + 1]) for i in range(1, len(ring) - 1)]
            else:                                                # more: a fan from a new corner in its middle
                centre = len(verts)
                verts = np.vstack((verts, verts[corners].mean(axis=0)))
                new += [(ring[i], ring[(i + 1) % len(ring)], centre) for i in range(len(ring))]
        rest = np.ones(len(tris), dtype=bool)
        rest[list(splits)] = False
        tris = np.vstack((tris[rest], np.array(new, dtype=np.int64).reshape(-1, 3)))
    return verts, tris


class TriMesh:
    """Read-only triangle mesh for display of IFC elements (numpy arrays).

    Only "feature" edges are visible: edges between triangles that are not
    coplanar, and open borders. Triangle diagonals inside a flat face stay
    hidden, so a wall looks like a wall, not like a triangulated surface.
    Offers the subset of the PolyMesh interface the viewport and the
    inference engine use.
    """

    def __init__(self, verts, tris, edges=None, closed=None, normals=None, colors=None):
        """edges: (pairs (E, 2), faces (E, 2)) and normals already worked out (geometry cache), or None. colors
        (0.259): each triangle's own colour (T, 3), sRGB 0–1 — an element of parts of several materials (a
        railing's wooden rail, steel posts, glass) — or None (its class's colour)."""
        self.verts = np.asarray(verts, dtype=float).reshape(-1, 3)
        self.tris = np.asarray(tris, dtype=np.int64).reshape(-1, 3)
        self.normals = triangle_normals(self.verts, self.tris) if normals is None else normals
        self.colors = None if colors is None or len(colors) != len(self.tris) else \
            np.asarray(colors, dtype=np.float32).reshape(-1, 3)
        self._edges = None
        self._edge_array = None
        self._edge_faces = None
        self._soft = None                   # (0.136) the softened edges and their faces, for the drawings' outlines
        self._closed = closed
        self._bounds = None
        if edges is not None:
            self._edge_array = np.asarray(edges[0], dtype=np.int64).reshape(-1, 2)
            self._edge_faces = np.asarray(edges[1], dtype=np.int64).reshape(-1, 2)

    @property
    def faces(self):
        return self.tris

    soft_deg = None              # (0.555) a free-form surface's: every fold under this many degrees softened
    quiet = False                # (0.563) a finish of many pieces: the direction its pieces' faces look

    def silence(self, up):
        """(0.563) Only the edges round the faces looking `up` drawn (a Revestimento: each piece's outline on its
        face, not its sides)."""
        up = tuple(float(c) for c in up)
        if self.quiet != up:
            self.quiet = up
            self._edges = self._edge_array = self._edge_faces = None

    def soften(self, degrees):
        """(0.555) A free-form surface (a parametric one): its folds under `degrees` softened as its curved parts —
        not drawn as edges, as Revit's (its borders and real creases still are)."""
        if self.soft_deg == degrees:
            return
        self.soft_deg = float(degrees)
        self._edges = self._edge_array = self._edge_faces = self._soft = None

    def face_normal(self, fi):
        return self.normals[fi]

    def triangulate(self):
        return self.tris, np.arange(len(self.tris), dtype=np.int64)

    def _analyse(self):
        """Feature edges, vectorised: the edges between triangles that are not
        coplanar, and the open borders (all in numpy, no loop per edge)."""
        if len(self.tris) == 0:
            self._edge_array = np.zeros((0, 2), np.int64)
            self._edge_faces = np.zeros((0, 2), np.int64)
            self._closed = False
            return
        uniq, counts, first, second, cos = self._edge_table()
        flat = (counts == 2) & (cos > 1 - 1e-6)                  # a diagonal inside a flat face
        keep = ~flat & ~self._smooth(uniq, counts, cos)
        if self.quiet is not False:                              # (0.563) a finish of many pieces: only the outline
            up = np.asarray(self.quiet, dtype=float)             # of each piece's face seen — as Revit's pattern;
            on = (self.normals[first] @ up > 0.99) | ((second >= 0) & (self.normals[np.maximum(second, 0)] @ up
                                                                        > 0.99))
            keep = keep & on                                     # all of every piece's edges blacken a wall of
            # small tiles seen from afar
        self._edge_array = uniq[keep]
        self._edge_faces = np.column_stack((first[keep], second[keep]))
        self._closed = bool(np.all(counts == 2))

    def _edge_table(self):
        """Every edge once: (pairs (E, 2), how many triangles have it, its first and second triangle (-1: none),
        the cosine between their normals)."""
        t = len(self.tris)
        directed = np.concatenate([self.tris[:, [0, 1]], self.tris[:, [1, 2]], self.tris[:, [2, 0]]])
        owner = np.tile(np.arange(t), 3)
        keys = np.sort(directed, axis=1)
        uniq, inverse, counts = np.unique(keys, axis=0, return_inverse=True, return_counts=True)
        order = np.argsort(inverse.reshape(-1), kind="stable")
        starts = np.concatenate(([0], np.cumsum(counts)[:-1]))
        first = owner[order[starts]]
        second = np.where(counts >= 2, owner[order[np.minimum(starts + 1, len(order) - 1)]], -1)
        cos = np.einsum("ij,ij->i", self.normals[first], self.normals[np.maximum(second, 0)])
        return uniq, counts, first, second, cos

    def contour_edges(self, direction):
        """(0.136) The softened edges of its curved surfaces (not drawn as edges) that are on its outline seen
        along `direction` — where the surface turns from facing the viewer to facing away: a pipe's sides seen
        from above, a round column's in an elevation. (K, 2) vertex indices."""
        if self._soft is None:
            if len(self.tris) == 0:
                self._soft = (np.zeros((0, 2), np.int64), np.zeros((0, 2), np.int64))
            else:
                uniq, counts, first, second, cos = self._edge_table()
                soft = self._smooth(uniq, counts, cos)
                self._soft = (uniq[soft], np.column_stack((first[soft], second[soft])))
        pairs, faces = self._soft
        if not len(pairs):
            return pairs
        s = self.normals @ np.asarray(direction, dtype=float)
        s = np.where(np.abs(s) < 1e-9, 0.0, np.sign(s))
        return pairs[s[faces[:, 0]] != s[faces[:, 1]]]

    def _smooth(self, pairs, counts, cos):
        """The edges of a curved surface made of flat strips (a pipe, a round column, a curved wall), hidden as
        SketchUp softens them (0.69): a small bend (< SMOOTH_DEG) repeated on at least SMOOTH_FAMILY parallel
        edges of the same mesh — a single low ridge of a roof stays."""
        if self.soft_deg is not None:            # (0.555) a free-form surface: any small fold
            return (counts == 2) & (cos <= 1 - 1e-6) & (cos > math.cos(math.radians(self.soft_deg)))
        bent = (counts == 2) & (cos <= 1 - 1e-6) & (cos > math.cos(math.radians(SMOOTH_DEG)))
        if np.count_nonzero(bent) < SMOOTH_FAMILY:
            return np.zeros(len(pairs), dtype=bool)
        idx = np.flatnonzero(bent)
        d = self.verts[pairs[idx, 1]] - self.verts[pairs[idx, 0]]
        d /= np.maximum(np.linalg.norm(d, axis=1), 1e-12)[:, None]
        lead = np.argmax(np.abs(d) > 1e-6, axis=1)                 # one way for both ways along an edge
        d *= np.sign(d[np.arange(len(d)), lead])[:, None]
        angle = np.degrees(np.arccos(np.clip(cos[idx], -1.0, 1.0)))
        keys = np.column_stack((np.round(d, 3), np.round(angle * 2) / 2))
        _u, inverse, family = np.unique(keys, axis=0, return_inverse=True, return_counts=True)
        out = np.zeros(len(pairs), dtype=bool)
        out[idx] = family[inverse.reshape(-1)] >= SMOOTH_FAMILY
        _a, by_angle, many = np.unique(keys[:, 3], return_inverse=True, return_counts=True)     # (a torus, 0.136)
        out[idx] |= many[by_angle.reshape(-1)] >= SMOOTH_SURFACE
        return out

    def edge_array(self):
        """(E, 2) vertex indices of the visible edges, and (E, 2) their faces (second = -1 on a border)."""
        if self._edge_array is None:
            self._analyse()
        return self._edge_array, self._edge_faces

    def visible_edges(self):
        if self._edges is None:
            pairs, faces = self.edge_array()
            self._edges = {(int(a), int(b)): [int(f) for f in fs if f >= 0] for (a, b), fs in zip(pairs, faces)}
        return self._edges

    def is_closed(self):
        if self._closed is None:
            self._analyse()
        return self._closed

    def bounds(self):
        """(lowest, highest) corner of the box around the vertices, or None if there are none.
        Worked out once (opening a file: in the reading thread, not the window's)."""
        if self._bounds is None and len(self.verts):
            self._bounds = (self.verts.min(axis=0), self.verts.max(axis=0))
        return self._bounds

    def copy(self):
        return self  # read-only

    def transformed(self, matrix):
        m = np.asarray(matrix, dtype=float)
        return TriMesh(self.verts @ m[:3, :3].T + m[:3, 3], self.tris, colors=self.colors)

    def volume(self):
        p = self.verts[self.tris]
        return float(np.einsum("ij,ij->i", p[:, 0], np.cross(p[:, 1], p[:, 2])).sum() / 6.0)
