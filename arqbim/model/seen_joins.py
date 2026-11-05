"""(0.320) The seams between elements of one material, left out of what is seen: where two elements' faces lie in one
plane, turned the same way and of the same material — two walls of a type in a row, a wall going on as the one above
it; (0.352) a wall's end and the face of the wall it turns the corner to, its plaster going round —, an edge of one in
the middle of their faces joined is not drawn (as Revit cleans up joined walls); where the material changes, it stays. In the 3D view, the elevations and sections on screen, and on the sheets. Only the drawing:
each element keeps its own shape. Pure NumPy and shapely; the elements near one found by a grid of boxes, so an edit
looks only round itself."""

import numpy as np

TOL = 1e-5            # m: a point this close to a plane is on it; two planes this close are one
INSIDE = 1e-4         # m: an edge this deep inside the faces joined is a seam (not their outline)
SHORTEST = 1e-3       # m: what is left of a seam partly joined, shorter than this, goes
CELL = 2.0            # m: the grid of boxes the neighbours are found by
MANY_CELLS = 4000     # an element over more cells than this (a terrain, a huge slab) is looked at with every one
# the elements that join (built of their materials, side by side); a door, a window, a fixture keep their lines
JOINED = ("IfcWall", "IfcWallStandardCase", "IfcWallElementedCase", "IfcSlab", "IfcColumn", "IfcBeam", "IfcMember",
          "IfcFooting", "IfcPile", "IfcRoof", "IfcCovering", "IfcPlate", "IfcStair", "IfcStairFlight", "IfcRamp",
          "IfcRampFlight", "IfcChimney", "IfcBuildingElementProxy")


class Planes:
    """An element's faces by plane: (normals (P, 3), offsets (P,), [its triangles' indices] per plane)."""

    def __init__(self, mesh):
        verts = np.asarray(mesh.verts, dtype=float)
        tris = np.asarray(mesh.tris, dtype=np.int64)
        normals = np.asarray(mesh.normals, dtype=float).reshape(-1, 3)
        if not len(tris):
            self.normals, self.offsets, self.groups = np.zeros((0, 3)), np.zeros(0), []
            return
        offsets = np.einsum("ij,ij->i", normals, verts[tris[:, 0]])
        codes = np.round(normals * 1e4).astype(np.int64)            # (one number per way a face turns…)
        turn = (codes[:, 0] * 20011 + codes[:, 1]) * 20011 + codes[:, 2]
        at = np.round(offsets * 1e4).astype(np.int64)               # (…and one per plane that way)
        order = np.lexsort((at, turn))
        new = np.ones(len(order), dtype=bool)
        new[1:] = (turn[order][1:] != turn[order][:-1]) | (at[order][1:] != at[order][:-1])
        starts = np.flatnonzero(new)
        first = order[starts]
        self.normals = normals[first]
        self.offsets = offsets[first]
        self.groups = np.split(order, starts[1:])


def material_info(ifc, guid):
    """What an element's faces are made of, read once: ("layers", [(name, normal, d0, d1)]) of layers, ("one",
    name) of one material, or None (none, several not in layers — a door —, or the IFC not read yet)."""
    try:
        bands = ifc.layer_bands(guid)
        if bands:
            return "layers", [(name, np.asarray(n, dtype=float), d0, d1) for name, n, d0, d1 in bands]
        names = ifc.material_names(guid)
    except (RuntimeError, AttributeError):
        return None
    return ("one", names[0]) if len(names) == 1 else None


def face_material(info, normal, offset):
    """The material of an element's faces in one plane: of layers, a side's — the layer it is on — or, across them
    (a top, an end), all its layers in order; else its one material. None: not known (never joined)."""
    if info is None:
        return None
    if info[0] == "one":
        return info[1]
    layers = info[1]
    n = layers[0][1]
    along = float(np.asarray(normal) @ n)
    if abs(along) > 0.999:                               # (a side: the layer whose face it is)
        at = offset * along
        best = min(layers, key=lambda layer: min(abs(layer[2] - at), abs(layer[3] - at)))
        if min(abs(best[2] - at), abs(best[3] - at)) < 1e-3:
            return best[0]
        return None
    return "layers:" + "|".join(str(name) for name, *_r in sorted(layers, key=lambda layer: layer[2]))


def outer_names(info):
    """(0.352) The materials of a layered element's two outer layers (its finishes: what goes round its ends), or ()."""
    if info is None or info[0] != "layers":
        return ()
    layers = info[1]
    return min(layers, key=lambda layer: layer[2])[0], max(layers, key=lambda layer: layer[3])[0]


def _goes_on(mine, info, theirs, other_info):
    """Do two elements' faces in one plane read as one: of one material — (0.352) or a wall's end and the face its
    finish goes round to, at an outside corner (that face's material one of the end's wall's outer layers, as
    material_looks paints that end)?"""
    if theirs is None:
        return False
    if theirs == mine:
        return True
    if mine.startswith("layers:") and not theirs.startswith("layers:"):
        return theirs in outer_names(info)
    if theirs.startswith("layers:") and not mine.startswith("layers:"):
        return mine in outer_names(other_info)
    return False


def seams(mesh, planes, info, others):
    """An element's seams with its neighbours: (each of its edges (mesh.edge_array) kept or not (E,), what is left of
    those partly joined (K, 2, 3), each one's plane's normal (K, 3)) — or None when nothing is left out. others:
    [(mesh, Planes, material_info)] of the elements near it. An edge of its faces in a plane is a seam where, a hair
    beyond it (away from its face), a neighbour's face of that plane and material goes on (NumPy only: the line a
    hair beyond, clipped by those faces' triangles)."""
    pairs, faces = mesh.edge_array()
    if not len(pairs) or not others or not len(planes.offsets):
        return None
    # the planes it shares with each of them, turned the same way: {its plane: [(other, its plane there)]}
    shared = {}
    for other_mesh, other, other_info in others:
        if not len(other.offsets):
            continue
        same = (planes.normals @ other.normals.T > 1.0 - 1e-6) & \
            (np.abs(planes.offsets[:, None] - other.offsets[None, :]) < TOL)
        for i, j in zip(*np.nonzero(same)):
            shared.setdefault(int(i), []).append((other_mesh, other, other_info, int(j)))
    if not shared:
        return None
    verts = np.asarray(mesh.verts, dtype=float)
    tris = np.asarray(mesh.tris, dtype=np.int64)
    va, vb = verts[pairs[:, 0]], verts[pairs[:, 1]]
    keep = np.ones(len(pairs), dtype=bool)
    extra, extra_n = [], []
    in_plane = np.zeros(len(tris), dtype=bool)
    for i, found in shared.items():
        n, d = planes.normals[i], planes.offsets[i]
        mine = face_material(info, n, d)
        if mine is None:
            continue
        cover = [np.asarray(m.verts, dtype=float)[np.asarray(m.tris)[other.groups[j]]]
                 for m, other, other_info, j in found
                 if _goes_on(mine, info, face_material(other_info, other.normals[j], other.offsets[j]), other_info)]
        if not cover:
            continue
        in_plane[:] = False
        in_plane[planes.groups[i]] = True
        first = in_plane[faces[:, 0]]
        second = (faces[:, 1] >= 0) & in_plane[np.maximum(faces[:, 1], 0)]
        on = np.flatnonzero(keep & (first | second) & (np.abs(va @ n - d) < TOL) & (np.abs(vb @ n - d) < TOL))
        if not len(on):
            continue
        u, w = _frame(n)
        flat = lambda p: np.stack((p @ u, p @ w), axis=-1)            # noqa: E731
        a2, b2 = flat(va[on]), flat(vb[on])
        face = np.where(first[on], faces[on, 0], faces[on, 1])
        centre = flat(verts[tris[face]].mean(axis=1))
        along = b2 - a2
        length = np.linalg.norm(along, axis=1)
        across = np.stack((-along[:, 1], along[:, 0]), axis=1) / np.maximum(length, 1e-12)[:, None]
        away = np.where(np.einsum("ij,ij->i", centre - a2, across) > 0, -1.0, 1.0)
        shift = across * (away * INSIDE)[:, None]                   # (a hair beyond the edge, off its face)
        lo, hi = _clipped(a2 + shift, b2 + shift, flat(np.concatenate(cover)))
        for k, e in enumerate(on):
            covered = _merged(lo[k], hi[k])
            if not covered or length[k] < 1e-9:
                continue
            gaps = _gaps(covered, 3 * INSIDE / length[k])
            if sum(t1 - t0 for t0, t1 in gaps) * length[k] > length[k] - 3 * INSIDE:
                continue                                            # (nothing of it joined)
            keep[e] = False
            for t0, t1 in gaps:                                     # (partly joined: the rest stays)
                if (t1 - t0) * length[k] >= SHORTEST:
                    a, b = va[e], vb[e]
                    extra.append(np.array((a + (b - a) * t0, a + (b - a) * t1)))
                    extra_n.append(n)
    if keep.all() and not extra:
        return None
    return keep, (np.array(extra) if extra else np.zeros((0, 2, 3))), (np.array(extra_n) if extra_n else
                                                                     np.zeros((0, 3)))


def _frame(n):
    """Two directions square to each other in the plane of normal n (no np.cross: a small array's is slow)."""
    x, y, z = (float(c) for c in n)
    if abs(x) < 0.9:                                             # (n × (1, 0, 0))
        u = np.array((0.0, z, -y))
    else:                                                        # (n × (0, 1, 0))
        u = np.array((-z, 0.0, x))
    u /= np.linalg.norm(u)
    w = np.array((y * u[2] - z * u[1], z * u[0] - x * u[2], x * u[1] - y * u[0]))
    return u, w


def _clipped(a, b, triangles):
    """For each line a[i]–b[i] (2D) and each triangle (K, 3, 2): the part of the line inside it, as t0 <= t <= t1
    along it ((E, K) each; empty where t1 <= t0)."""
    p = triangles
    turn = np.sign((p[:, 1, 0] - p[:, 0, 0]) * (p[:, 2, 1] - p[:, 0, 1])
                   - (p[:, 1, 1] - p[:, 0, 1]) * (p[:, 2, 0] - p[:, 0, 0]))           # (K,): counter-clockwise +1
    lo = np.zeros((len(a), len(p)))
    hi = np.ones((len(a), len(p)))
    hi[:, turn == 0] = -1.0                                       # (a triangle of no area covers nothing)
    d = b - a
    for j in range(3):
        s, e = p[:, j], p[:, (j + 1) % 3]
        side = e - s                                              # (K, 2)
        # inside: turn · cross(side, x - s) >= 0, with x = a + t·d: alpha + beta·t >= 0
        alpha = turn[None, :] * (side[None, :, 0] * (a[:, None, 1] - s[None, :, 1])
                                 - side[None, :, 1] * (a[:, None, 0] - s[None, :, 0]))
        beta = turn[None, :] * (side[None, :, 0] * d[:, None, 1] - side[None, :, 1] * d[:, None, 0])
        with np.errstate(divide="ignore", invalid="ignore"):
            t = -alpha / beta
        lo = np.where(beta > 1e-15, np.maximum(lo, t), lo)
        hi = np.where(beta < -1e-15, np.minimum(hi, t), hi)
        hi = np.where((np.abs(beta) <= 1e-15) & (alpha < -1e-12), -1.0, hi)   # (parallel and outside)
    return lo, hi


def _merged(lo, hi):
    """The intervals [lo, hi] that are not empty, joined: [(t0, t1)] in order."""
    out = []
    for t0, t1 in sorted((float(a), float(b)) for a, b in zip(lo, hi) if b > a):
        if out and t0 <= out[-1][1] + 1e-9:
            out[-1] = (out[-1][0], max(out[-1][1], t1))
        else:
            out.append((t0, t1))
    return out


def _gaps(covered, slack):
    """What of [0, 1] the intervals `covered` leave (a gap shorter than `slack` at an end is no gap)."""
    out, at = [], 0.0
    for t0, t1 in covered:
        if t0 > at + slack:
            out.append((at, t0))
        at = max(at, t1)
    if at < 1.0 - slack:
        out.append((at, 1.0))
    return out


def edges(mesh, joined):
    """An element's edges (K, 2, 3) as drawn: those `seams` keeps and what is left of the others."""
    pairs, _faces = mesh.edge_array()
    verts = np.asarray(mesh.verts, dtype=float)
    if joined is None:
        return np.stack((verts[pairs[:, 0]], verts[pairs[:, 1]]), axis=1) if len(pairs) else np.zeros((0, 2, 3))
    keep, extra, _n = joined
    kept = pairs[keep]
    out = np.stack((verts[kept[:, 0]], verts[kept[:, 1]]), axis=1) if len(kept) else np.zeros((0, 2, 3))
    return np.concatenate((out, extra)) if len(extra) else out


class Neighbours:
    """Elements' boxes on a grid, to find those near one without looking at them all."""

    def __init__(self):
        self.boxes = {}
        self._flat = {}                 # (each box as six floats: compared without NumPy, many times)
        self.cells = {}
        self.big = set()

    def _cells(self, lo, hi):
        a = np.floor(np.asarray(lo, dtype=float) / CELL).astype(int)
        b = np.floor(np.asarray(hi, dtype=float) / CELL).astype(int)
        count = int(np.prod(b - a + 1))
        if count > MANY_CELLS:
            return None
        return [(x, y, z) for x in range(a[0], b[0] + 1) for y in range(a[1], b[1] + 1) for z in range(a[2], b[2] + 1)]

    def update(self, key, box):
        self.remove(key)
        if box is None:
            return
        lo, hi = (np.asarray(c, dtype=float) for c in box)
        self.boxes[key] = (lo, hi)
        self._flat[key] = tuple(float(c) for c in lo) + tuple(float(c) for c in hi)
        cells = self._cells(lo, hi)
        if cells is None:
            self.big.add(key)
            return
        for c in cells:
            self.cells.setdefault(c, set()).add(key)

    def remove(self, key):
        box = self.boxes.pop(key, None)
        if box is None:
            return
        self._flat.pop(key, None)
        self.big.discard(key)
        for c in self._cells(*box) or ():
            found = self.cells.get(c)
            if found is not None:
                found.discard(key)
                if not found:
                    del self.cells[c]

    def near(self, box, pad=INSIDE * 10):
        """The keys whose boxes touch `box` (lowest, highest)."""
        if box is None:
            return set()
        lo, hi = np.asarray(box[0], dtype=float) - pad, np.asarray(box[1], dtype=float) + pad
        found = set(self.big)
        for c in self._cells(lo, hi) or [c for c in self.cells]:
            found |= self.cells.get(c, set())
        x0, y0, z0 = (float(c) for c in lo)
        x1, y1, z1 = (float(c) for c in hi)
        flat = self._flat
        return {k for k in found if flat[k][0] <= x1 and flat[k][1] <= y1 and flat[k][2] <= z1
                and flat[k][3] >= x0 and flat[k][4] >= y0 and flat[k][5] >= z0}


def joinable(obj):
    """Is it an element whose seams are looked for (a wall, a slab, a column… — JOINED)?"""
    return obj is not None and obj.is_bim and obj.ifc_class in JOINED and hasattr(obj.mesh, "edge_array") \
        and hasattr(obj.mesh, "normals")


def all_seams(objects, ifc):
    """{element: seams()} of the elements among `objects` that have some (a drawing's: all at once)."""
    objects = [o for o in objects if joinable(o) and o.mesh.bounds() is not None]
    if len(objects) < 2:
        return {}
    index = Neighbours()
    by = {}
    for o in objects:
        index.update(o.id, o.mesh.bounds())
        by[o.id] = o
    planes, infos = {}, {}

    def planes_of(o):
        if o.id not in planes:
            planes[o.id] = Planes(o.mesh)
        return planes[o.id]

    def info_of(o):
        if o.id not in infos:
            infos[o.id] = material_info(ifc, o.id)
        return infos[o.id]

    out = {}
    for o in objects:
        near = [by[k] for k in index.near(o.mesh.bounds()) if k != o.id]
        if near:                                     # (0.333: not those unjoined from it by hand)
            apart = unjoined_from(ifc, o.id)
            near = [p for p in near if p.id not in apart]
        if not near or info_of(o) is None:
            continue
        mine = planes_of(o)
        # (only the neighbours with a plane of its own: their materials are asked for then)
        others = [p for p in near if share_plane(mine, planes_of(p)) and info_of(p) is not None]
        if not others:
            continue
        found = seams(o.mesh, mine, info_of(o), [(p.mesh, planes_of(p), info_of(p)) for p in others])
        if found is not None:
            out[o.id] = found
    return out


def unjoined_from(ifc, guid):
    """(0.333) The elements unjoined by hand from one (ifc/unjoin.py): their faces never hide its edges."""
    from ..ifc import unjoin
    try:
        return unjoin.apart_from(ifc, guid)
    except (AttributeError, RuntimeError):
        return frozenset()


def share_plane(a, b):
    """Have two elements' Planes one plane, turned the same way?"""
    if not len(a.offsets) or not len(b.offsets):
        return False
    same = (a.normals @ b.normals.T > 1.0 - 1e-6) & (np.abs(a.offsets[:, None] - b.offsets[None, :]) < TOL)
    return bool(same.any())
