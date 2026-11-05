"""(0.395) The lines of the model a parametric surface is made of: a sketch's chains — an arc's or a Bézier curve's
points as drawn, else its loose lines (or its faces' outer edges) joined end to end into polylines, open or closed —
in world coordinates; and the sketch's own name (uid) by which the surface follows it."""

import uuid

import numpy as np

from ..core import curves as core_curves
from ..core.mesh import edge_key


def _world(sketch, pts):
    m = np.asarray(sketch.matrix, dtype=float)
    p = np.asarray(pts, dtype=float).reshape(-1, 3)
    return p @ m[:3, :3].T + m[:3, 3]


def _chains(edges, verts):
    """Polylines through edges [(a, b)]: [(indices, closed)] — split at the points where three or more meet."""
    nbr = {}
    for a, b in edges:
        if a == b:
            continue
        nbr.setdefault(a, set()).add(b)
        nbr.setdefault(b, set()).add(a)
    used = set()
    out = []

    def walk(start, nxt):
        path = [start, nxt]
        used.add(edge_key(start, nxt))
        prev, cur = start, nxt
        while len(nbr.get(cur, ())) == 2:
            following = [n for n in nbr[cur] if n != prev][0]
            key = edge_key(cur, following)
            if key in used:
                break
            used.add(key)
            path.append(following)
            prev, cur = cur, following
        return path

    for v in sorted(nbr, key=lambda k: (len(nbr[k]) == 2, k)):      # (from the ends and branch points first)
        if len(nbr[v]) == 2:
            continue
        for n in sorted(nbr[v]):
            if edge_key(v, n) not in used:
                out.append((walk(v, n), False))
    for v in sorted(nbr):                                          # (what is left: closed loops)
        for n in sorted(nbr[v]):
            if edge_key(v, n) not in used:
                path = walk(v, n)
                closed = len(path) > 3 and path[-1] == path[0]
                out.append((path[:-1] if closed else path, closed))
    return out


def sketch_chains(sketch):
    """[(points (k, 3) world, closed)] of a sketch's lines (the longest first)."""
    curve = getattr(sketch, "curve", None)
    if curve:
        pts = core_curves.curve_points(curve)
        if pts is not None and len(pts) >= 2:
            return [(_world(sketch, pts), core_curves.is_closed(curve))]
    mesh = sketch.mesh
    if mesh.faces:
        uses = mesh.edge_faces()
        edges = [e for e, fis in uses.items() if len(fis) == 1] + [tuple(e) for e in mesh.lines]
    else:
        edges = [tuple(e) for e in mesh.lines]
    verts = np.asarray(mesh.verts, dtype=float).reshape(-1, 3)
    out = []
    for idx, closed in _chains(edges, verts):
        if len(idx) >= 2:
            out.append((_world(sketch, verts[idx]), closed))
    out.sort(key=lambda c: -float(np.linalg.norm(np.diff(c[0], axis=0), axis=1).sum()))
    return out


def chain_near(sketch, point):
    """The sketch's chain nearest a world point: (points, closed) or None."""
    chains = sketch_chains(sketch)
    if not chains:
        return None
    p = np.asarray(point, dtype=float)

    def dist(c):
        pts = c[0]
        a, b = pts[:-1], pts[1:]
        if c[1]:
            a, b = pts, np.roll(pts, -1, axis=0)
        d = b - a
        dd = np.maximum(np.einsum("ij,ij->i", d, d), 1e-24)
        s = np.clip(np.einsum("ij,ij->i", p - a, d) / dd, 0.0, 1.0)
        return float(np.min(np.linalg.norm(a + d * s[:, None] - p, axis=1)))
    return min(chains, key=dist)


def ensure_uid(sketch):
    """The sketch's own lasting name (given now if it has none)."""
    if not getattr(sketch, "uid", None):
        sketch.uid = uuid.uuid4().hex[:12]
    return sketch.uid
