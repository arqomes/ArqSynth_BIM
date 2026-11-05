"""Inference engine (SketchUp-style snaps).

Finds what the cursor is "on": an endpoint, a midpoint, the origin, an edge or
a face. Pure numpy: the screen projection is passed in as a function, so the
engine is testable without a window or GPU.

Priority (as in SketchUp): endpoint > intersection > midpoint > origin >
where two edges under the cursor cross (0.60) > on edge > on guide > on face.
Points hidden behind the face under the cursor are ignored. Guide lines (Tape
Measure) take part: the cursor snaps along them and to their intersections
with other guides and with edges. Alignments with acquired points: tracking.py.
"""

from dataclasses import dataclass

import numpy as np

from .sketch_geometry import transform_point

ENDPOINT, MIDPOINT, ORIGIN, ON_EDGE, ON_FACE = "endpoint", "midpoint", "origin", "on_edge", "on_face"
INTERSECTION, ON_GUIDE = "intersection", "on_guide"
POINT_KINDS = (ENDPOINT, INTERSECTION, MIDPOINT, ORIGIN)
_RANK = {ENDPOINT: 0, INTERSECTION: 1, MIDPOINT: 2, ORIGIN: 3}

POINT_RADIUS_PX = 12
EDGE_RADIUS_PX = 7
GUIDE_HALF_LENGTH = 1000.0   # guide lines are "infinite": 2 km segments
_I4 = np.eye(4)


@dataclass
class Snap:
    kind: str
    point: np.ndarray
    obj_id: object = None
    edge: tuple = None       # (a, b) world segment, for ON_EDGE / ON_GUIDE


class SnapBlock:
    """One object's snap candidates (world space): its edges, their midpoints and
    the corners they use. Made once per version of the object."""

    def __init__(self, obj):
        self.obj_id = obj.id
        if hasattr(obj.mesh, "edge_array"):
            # IFC element: whole numpy blocks (no loop per edge)
            pairs, _faces = obj.mesh.edge_array()
            m = np.asarray(obj.matrix, dtype=float)
            world = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
            self.a, self.b = world[pairs[:, 0]], world[pairs[:, 1]]
            self.corners = world[np.unique(pairs)] if len(pairs) else np.zeros((0, 3))
        else:
            world = [transform_point(obj.matrix, v) for v in obj.mesh.verts]
            keys = list(obj.mesh.visible_edges())
            self.a = np.array([world[i] for i, _j in keys]).reshape(-1, 3)
            self.b = np.array([world[j] for _i, j in keys]).reshape(-1, 3)
            self.corners = np.array([world[i] for i in sorted({v for e in keys for v in e})]).reshape(-1, 3)


class SnapGeometry:
    """World-space snap candidates of a set of objects (or of their ready-made blocks), plus
    the origin, the guide lines and where they cross."""

    def __init__(self, objects=(), guides=(), blocks=None):
        from .lines import line_line_intersection
        pts, kinds, owners = [np.zeros((1, 3))], [ORIGIN], [None]
        ea, eb, eowners = [], [], []
        for block in (blocks if blocks is not None else [SnapBlock(o) for o in objects]):
            a, b, used = block.a, block.b, block.corners
            if not len(a):
                continue
            pts += [(a + b) / 2, used]
            kinds += [MIDPOINT] * len(a) + [ENDPOINT] * len(used)
            owners += [block.obj_id] * (len(a) + len(used))
            ea.append(a)
            eb.append(b)
            eowners += [block.obj_id] * len(a)
        edge_a = np.concatenate(ea) if ea else np.zeros((0, 3))
        edge_b = np.concatenate(eb) if eb else np.zeros((0, 3))
        ekinds = [ON_EDGE] * len(edge_a)
        guides = [(np.asarray(p, dtype=float), np.asarray(d, dtype=float)) for p, d in guides]
        ga, gb = [], []
        for i, (p, d) in enumerate(guides):
            # where the guide crosses another guide or an edge
            for q, e in guides[i + 1:]:
                x = line_line_intersection(p, d, q, e)
                if x is not None:
                    pts.append(x.reshape(1, 3))
                    kinds.append(INTERSECTION)
                    owners.append(None)
            crossings = _crossings(p, d, edge_a, edge_b)
            pts.append(crossings)
            kinds += [INTERSECTION] * len(crossings)
            owners += [None] * len(crossings)
            ga.append(p - d * GUIDE_HALF_LENGTH)
            gb.append(p + d * GUIDE_HALF_LENGTH)
            eowners.append(None)
            ekinds.append(ON_GUIDE)
        self.points = np.concatenate(pts)
        self.kinds = kinds
        self.owners = owners
        self.edge_a = np.concatenate([edge_a, np.array(ga).reshape(-1, 3)])
        self.edge_b = np.concatenate([edge_b, np.array(gb).reshape(-1, 3)])
        self.edge_owners = eowners
        self.edge_kinds = ekinds


class SnapIndex:
    """Snap candidates of a whole model, found near the cursor only.

    Each object keeps its SnapBlock (made the first time it is needed, again only
    when that object changes) and its bounding box. Under the mouse, a vectorised
    test of all the boxes against the view ray — thickened by the snap radius at
    each box's distance — keeps the few objects that can have a candidate near
    the cursor; the inference engine then works on those alone. Cost per mouse
    move no longer grows with the model's size (Phase 2, step 2).
    """

    def __init__(self):
        self.objects = {}            # obj_id -> object (sketch or IFC element)
        self.blocks = {}             # obj_id -> SnapBlock, made on demand
        # the boxes, one row per object, updated in place (a change touches one row, not the table)
        self._ids = []               # row -> obj_id (None: a free row)
        self._row = {}               # obj_id -> row
        self._lo = np.zeros((0, 3))
        self._hi = np.zeros((0, 3))
        self._alive = np.zeros(0, bool)
        self._todo = set()           # objects whose box is to be (re)made before the next query

    def update(self, obj):
        self.objects[obj.id] = obj
        self.blocks.pop(obj.id, None)
        self._todo.add(obj.id)

    def remove(self, obj_id):
        self.objects.pop(obj_id, None)
        self.blocks.pop(obj_id, None)
        self._todo.discard(obj_id)
        row = self._row.pop(obj_id, None)
        if row is not None:
            self._ids[row] = None
            self._alive[row] = False

    def clear(self):
        self.__init__()

    def prepare(self):
        """Make the pending boxes now (after opening a file), not on the first mouse move."""
        self._box_arrays()

    @staticmethod
    def _box(obj):
        if getattr(obj, "is_bim", False) and hasattr(obj.mesh, "bounds"):
            return obj.mesh.bounds()                             # IFC element: world coordinates, box kept
        v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
        if not len(v):
            return None
        m = np.asarray(obj.matrix, dtype=float)
        if not np.array_equal(m, _I4):                           # IFC elements: already in world coordinates
            v = v @ m[:3, :3].T + m[:3, 3]
        return v.min(axis=0), v.max(axis=0)

    def _box_arrays(self):
        if self._todo:
            new = [i for i in self._todo if i not in self._row]
            if new:                                              # room for the new objects
                if self._alive.size and (~self._alive).sum() > self._alive.size // 2:
                    self._compact()
                n = len(self._ids)
                self._ids += new
                self._row.update({obj_id: n + k for k, obj_id in enumerate(new)})
                self._lo = np.concatenate([self._lo, np.zeros((len(new), 3))])
                self._hi = np.concatenate([self._hi, np.zeros((len(new), 3))])
                self._alive = np.concatenate([self._alive, np.zeros(len(new), bool)])
            for obj_id in self._todo:
                row, box = self._row[obj_id], self._box(self.objects[obj_id])
                self._alive[row] = box is not None
                if box is not None:
                    self._lo[row], self._hi[row] = box
            self._todo = set()
        return self._ids, self._lo, self._hi

    def _compact(self):
        keep = np.flatnonzero(self._alive)
        self._ids = [self._ids[i] for i in keep]
        self._row = {obj_id: k for k, obj_id in enumerate(self._ids)}
        self._lo, self._hi, self._alive = self._lo[keep], self._hi[keep], self._alive[keep]

    def near(self, origin, direction, slope, radius_px=POINT_RADIUS_PX, pixel=0.0):
        """Ids of the objects whose box passes within `radius_px` pixels of the view ray.
        slope: world size of one pixel per metre of distance (2·tan(fov/2) / image height);
        pixel: world size of one pixel whatever the distance (a plan or section: no perspective)."""
        ids, lo, hi = self._box_arrays()
        if not self._alive.any():
            return []
        o, d = np.asarray(origin, dtype=float), np.asarray(direction, dtype=float)
        centre, half = (lo + hi) / 2, (hi - lo) / 2
        far = np.maximum((centre - o) @ d + np.linalg.norm(half, axis=1), 0.0)
        grow = (radius_px * (slope * far + pixel) + 1e-3)[:, None]    # the snap radius at the box's far side
        lo2, hi2 = lo - grow, hi + grow
        with np.errstate(divide="ignore", invalid="ignore"):
            inv = 1.0 / np.where(np.abs(d) > 1e-12, d, 1e-12)
            t1, t2 = (lo2 - o) * inv, (hi2 - o) * inv
        t_in = np.minimum(t1, t2).max(axis=1)
        t_out = np.maximum(t1, t2).min(axis=1)
        hit = (t_out >= np.maximum(t_in, 0.0)) & self._alive
        return [ids[i] for i in np.flatnonzero(hit)]

    def along(self, origin, direction, length, margin=0.0):
        """Ids of the objects whose box, grown by `margin`, a segment meets (from `origin`, `length` along the
        unit `direction`): what can be in the way of a step (core/collide)."""
        ids, lo, hi = self._box_arrays()
        if not self._alive.any():
            return []
        o, d = np.asarray(origin, dtype=float), np.asarray(direction, dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            inv = 1.0 / np.where(np.abs(d) > 1e-12, d, 1e-12)
            t1, t2 = (lo - margin - o) * inv, (hi + margin - o) * inv
        t_in = np.minimum(t1, t2).max(axis=1)
        t_out = np.maximum(t1, t2).min(axis=1)
        hit = (t_out >= np.maximum(t_in, 0.0)) & (t_in <= length) & self._alive
        return [ids[i] for i in np.flatnonzero(hit)]

    def block(self, obj_id):
        b = self.blocks.get(obj_id)
        if b is None:
            b = self.blocks[obj_id] = SnapBlock(self.objects[obj_id])
        return b

    def geometry(self, origin, direction, slope, guides=(), shown=None, radius_px=POINT_RADIUS_PX, keep=None,
                 pixel=0.0):
        """The SnapGeometry of what is near the cursor (shown(obj) filters hidden storeys;
        keep: [(normal, offset)] of a plan, a section or a section box — what is cut away
        (n·p < offset for one of them) is left out: its points, and the edges wholly beyond one).
        slope / pixel: see near."""
        ids = self.near(origin, direction, slope, radius_px, pixel)
        if shown is not None:
            ids = [i for i in ids if shown(self.objects[i])]
        blocks = [self.block(i) for i in ids]
        if keep:
            blocks = [_Kept(b, keep) for b in blocks]
        return SnapGeometry(guides=guides, blocks=blocks)


class _Kept:
    """A SnapBlock without what a plan, a section or a section box cuts away (n·p < offset)."""

    def __init__(self, block, planes):
        edges = np.ones(len(block.a), dtype=bool)
        corners = np.ones(len(block.corners), dtype=bool)
        for normal, offset in planes:
            n = np.asarray(normal, dtype=float)
            edges &= np.maximum(block.a @ n, block.b @ n) >= offset - 1e-9
            corners &= block.corners @ n >= offset - 1e-9
        self.obj_id = block.obj_id
        self.a, self.b = block.a[edges], block.b[edges]
        self.corners = block.corners[corners]


def _crossings(p, d, a, b, tol=1e-6):
    """Where the line (p, d) crosses the segments a[i]-b[i] (vectorised): (K, 3) points."""
    if not len(a):
        return np.zeros((0, 3))
    u = b - a
    w = p - a
    dd = float(d @ d)
    du = u @ d
    uu = np.einsum("ij,ij->i", u, u)
    dw = w @ d
    uw = np.einsum("ij,ij->i", u, w)
    denom = dd * uu - du * du
    ok = np.abs(denom) > 1e-12
    safe = np.where(ok, denom, 1.0)
    s = (du * uw - uu * dw) / safe                 # along the guide
    t = (dd * uw - du * dw) / safe                 # along the segment
    q1 = p + s[:, None] * d
    q2 = a + t[:, None] * u
    hit = ok & (np.linalg.norm(q1 - q2, axis=1) <= tol) & (t >= -1e-9) & (t <= 1 + 1e-9)
    return ((q1 + q2) / 2)[hit]


def _visible(points, origin, direction, hit):
    """Not behind the camera, and not hidden behind the face under the cursor.

    A point is hidden only if it lies on the far side of that face's plane AND
    farther away along the view ray. Points on the face itself (its corners and
    edges) stay visible even when seen at a grazing angle.
    """
    t = (points - origin) @ direction
    ok = t > 0
    if hit is not None:
        hit_point, normal = hit
        hit_t = float((hit_point - origin) @ direction)
        n = normal if float(np.dot(normal, origin - hit_point)) > 0 else -normal   # facing the camera
        tol = 1e-3 * abs(hit_t) + 0.002
        behind = ((points - hit_point) @ n) < -tol
        ok &= ~(behind & (t > hit_t + tol))
    return ok


def closest_on_segments(origin, direction, a, b):
    """For each segment a[i]-b[i], the point closest to the ray (vectorised)."""
    u = b - a
    w0 = a - origin
    uu = np.einsum("ij,ij->i", u, u)
    ud = u @ direction
    dd = direction @ direction
    uw = np.einsum("ij,ij->i", u, w0)
    dw = w0 @ direction
    denom = uu * dd - ud * ud
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(np.abs(denom) > 1e-12, (ud * dw - dd * uw) / denom, 0.0)
    s = np.clip(s, 0.0, 1.0)
    return a + s[:, None] * u


def find_snap(geom, mouse, project, origin, direction, hit=None,
              point_radius=POINT_RADIUS_PX, edge_radius=EDGE_RADIUS_PX):
    """Best snap under the mouse, or None.

    project(points (N, 3)) -> (N, 2) screen coordinates (NaN behind the camera).
    hit: (obj_id, world point, world normal) of the face under the cursor, or None.
    """
    mouse = np.asarray(mouse, dtype=float)
    face = (np.asarray(hit[1], dtype=float), np.asarray(hit[2], dtype=float)) if hit is not None else None

    if len(geom.points):
        xy = project(geom.points)
        dist = np.linalg.norm(xy - mouse, axis=1)
        ok = (dist <= point_radius) & _visible(geom.points, origin, direction, face)
        idx = np.flatnonzero(np.nan_to_num(ok, nan=False))
        if len(idx):
            # Same kind and same pixel (e.g. top and bottom corner seen from above): nearest to the eye wins.
            depth = (geom.points - origin) @ direction
            best = min(idx, key=lambda i: (_RANK[geom.kinds[i]], round(dist[i]), depth[i]))
            return Snap(geom.kinds[best], geom.points[best].copy(), geom.owners[best])

    if len(geom.edge_a):
        cp = closest_on_segments(origin, direction, geom.edge_a, geom.edge_b)
        xy = project(cp)
        dist = np.linalg.norm(xy - mouse, axis=1)
        ok = (dist <= edge_radius) & _visible(cp, origin, direction, face)
        idx = np.flatnonzero(np.nan_to_num(ok, nan=False))
        if len(idx) >= 2:
            crossing = _edges_crossing(geom, idx[np.argsort(dist[idx])][:8], mouse, project, point_radius)
            if crossing is not None:
                return crossing
        if len(idx):
            depth = (cp - origin) @ direction
            # an edge of the model wins over a guide line at the same distance
            best = min(idx, key=lambda i: (round(dist[i]), geom.edge_kinds[i] == ON_GUIDE, depth[i]))
            return Snap(geom.edge_kinds[best], cp[best].copy(), geom.edge_owners[best],
                        (geom.edge_a[best].copy(), geom.edge_b[best].copy()))

    if hit is not None:
        return Snap(ON_FACE, np.asarray(hit[1], dtype=float), hit[0])
    return None


def _edges_crossing(geom, idx, mouse, project, radius):
    """Where two of the edges under the mouse cross (0.60), if that is near the mouse: a Snap."""
    from .lines import line_line_intersection
    best = None
    for k, i in enumerate(idx):
        a1, b1 = geom.edge_a[i], geom.edge_b[i]
        u1 = b1 - a1
        for j in idx[k + 1:]:
            a2, b2 = geom.edge_a[j], geom.edge_b[j]
            u2 = b2 - a2
            if np.linalg.norm(np.cross(u1, u2)) <= 1e-9 * max(np.linalg.norm(u1) * np.linalg.norm(u2), 1e-12):
                continue                                         # parallel
            x = line_line_intersection(a1, u1, a2, u2, tol=1e-6)
            if x is None or not (_within(x, a1, u1) and _within(x, a2, u2)):
                continue
            xy = project(x[None, :])[0]
            if np.any(np.isnan(xy)):
                continue
            d = float(np.hypot(*(xy - mouse)))
            if d <= radius and (best is None or d < best[0]):
                best = (d, x, geom.edge_owners[i])
    return Snap(INTERSECTION, best[1], best[2]) if best is not None else None


def _within(p, a, u, tol=1e-6):
    uu = float(u @ u)
    s = float((p - a) @ u) / uu if uu > 1e-18 else -1.0
    return -tol <= s <= 1 + tol


def square_inference(du, dv, tolerance=0.03):
    """SketchUp's 'square' inference: snap the second side to the first when
    they differ by less than `tolerance` (relative). Returns (du, dv, snapped)."""
    a, b = abs(du), abs(dv)
    if a > 1e-9 and b > 1e-9 and abs(a - b) <= tolerance * max(a, b):
        return du, (1.0 if dv >= 0 else -1.0) * a, True
    return du, dv, False
