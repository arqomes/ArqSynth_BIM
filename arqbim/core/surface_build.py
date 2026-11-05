"""The parametric surfaces' construction (0.395, the addon's «Construção»): what is made on a surface — each section a
system of pieces, made in this order (the structure first, the cladding after):

    shell      a shell of a thickness (centred, out or in), its edges closed
    ribs       ribs along u and/or v (the edges included), as profiles following the surface
    slats      slats / a brise one way (between the edges), off the surface if asked
    weave      strips both ways passing over and under each other (a fabric)
    gridshell  straight bars node to node: «quad», «tri», «diagrid» (the diagonals only) or «hex», with nodes
    edge       a ring beam round the surface's edge
    supports   columns under the lowest points of the edge, down to a level
    panels     panels on a grid of cells (quads or triangles) with a joint: solid, glass, metal or fibre cement;
               framed glazing; cells left open by a formula («pixel» façade); an opening in each by a formula and an
               image; or fine perforation (real holes) over the whole façade
    spider     point-fixed glass floating off the surface, held by spiders (arms and articulated bolts) at the nodes

Every section's numbers may be formulas of the surface's inputs. The pieces come out as triangles grouped by material
(catalog keys: each section's own, or the one asked for), with a register of the parts (a cut list: the bars by
length to the mm, the panels with their warp — how far the 4th corner is off the plane of the other 3).

Pure numpy and shapely, metres, the surface's coordinates."""

import math

import numpy as np

from . import surface_expr as expr
from .param_surface import SurfaceError, grid_normals, kept, resample

SECTIONS = ("shell", "ribs", "slats", "weave", "gridshell", "edge", "supports", "panels", "spider")
ORIENTS = ("normal", "vertical", "smooth")
TEMPLATES = {
    "shell": {"thickness": 0.12, "offset": "center", "material": ""},
    "ribs": {"count_u": 3, "count_v": 5, "width": 0.06, "depth": 0.18, "orient": "normal", "material": ""},
    "slats": {"direction": "u", "count": 24, "width": 0.045, "depth": 0.09, "offset": 0.0, "orient": "normal",
              "material": ""},
    "weave": {"count_u": 10, "count_v": 10, "width": 0.09, "depth": 0.02, "amplitude": 0.05, "offset": 0.0,
              "material": ""},
    "gridshell": {"mode": "diagrid", "u": 12, "v": 8, "size": 0.05, "nodes": True, "node_size": 0.09,
                  "orient": "normal", "material": ""},
    "edge": {"width": 0.08, "depth": 0.16, "orient": "normal", "material": ""},
    "supports": {"count": 4, "size": 0.15, "base_z": 0.0, "material": ""},
    "panels": {"pattern": "quad", "u": 8, "v": 6, "thickness": 0.02, "gap": 0.012, "max_warp": 0.02, "kind": "solid",
               "frame": 0.0, "fill": 1.0, "open": 0.0, "mask": "", "mask_invert": False, "perf": False,
               "perf_spacing": 0.08, "perf_min": 0.006, "perf_max": 0.05, "perf_margin": 0.02, "material": ""},
    "spider": {"u": 5, "v": 4, "thickness": 0.012, "gap": 0.02, "arm": 0.12, "reach": 0.15, "size": 0.05,
               "material": ""},
}
CHOICES = {("shell", "offset"): ("center", "out", "in"), ("slats", "direction"): ("u", "v"),
           ("gridshell", "mode"): ("quad", "tri", "diagrid", "hex"), ("panels", "pattern"): ("quad", "tri"),
           ("panels", "kind"): ("solid", "glass", "metal", "fibro")}
for _s in ("ribs", "slats", "gridshell", "edge"):
    CHOICES[(_s, "orient")] = ORIENTS
COUNTS = {"count_u", "count_v", "count", "u", "v"}              # whole numbers
# the material each family is made of (catalog keys) — a section's «material» changes its main one
FAMILIES = {"estrutura": "aco_preto", "ferragem": "inox", "vidro": "vidro", "ripas": "madeira",
            "casca": "betao_armado", "painel": "aluminio_branco", "metal": "aluminio", "fibro": "fibrocimento",
            "superficie": "concreto"}
SECTION_FAMILY = {"shell": "casca", "ribs": "estrutura", "slats": "ripas", "weave": "ripas", "gridshell": "estrutura",
                  "edge": "estrutura", "supports": "estrutura", "panels": "painel", "spider": "ferragem"}
PANEL_FAMILY = {"solid": "painel", "glass": "vidro", "metal": "metal", "fibro": "fibro"}
PANEL_KIND = {"solid": "painel", "glass": "vidro", "metal": "painel metalico", "fibro": "painel fibrocimento"}
MAX_HOLES = 20000               # fine perforation: at most this many holes over the whole surface
HOLE_SIDES = 12
MAX_TRIANGLES = 1_500_000       # the whole construction: more is refused (too heavy to show)


# ---------------------------------------------------------------- small helpers

def _unit(v, fallback=(0.0, 0.0, 1.0)):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return np.where(n > 1e-12, v / np.maximum(n, 1e-12), np.broadcast_to(np.asarray(fallback, float), v.shape))


def _stations(n, ends=True):
    if n <= 0:
        return []
    if ends:
        return [0.5] if n == 1 else [k / (n - 1) for k in range(n)]
    return [(k + 0.5) / n for k in range(n)]


def polygon_area(p):
    p = np.asarray(p, float)
    total = np.zeros(3)
    for k in range(1, len(p) - 1):
        total += np.cross(p[k] - p[0], p[k + 1] - p[0])
    return 0.5 * float(np.linalg.norm(total))


def panel_warp(c):
    """How far (m) the 4th corner is off the plane of the first three (0 for a triangle)."""
    c = np.asarray(c, float)
    if len(c) < 4:
        return 0.0
    n = np.cross(c[1] - c[0], c[2] - c[0])
    ln = np.linalg.norm(n)
    return abs(float((c[3] - c[0]) @ (n / ln))) if ln > 1e-12 else 0.0


def inset(corners, d):
    """The polygon's edges moved in by `d` (a true inset: the joint between neighbours exactly 2d)."""
    c = np.asarray(corners, float)
    k = len(c)
    centre = c.mean(axis=0)
    out = []
    for i in range(k):
        e1 = _unit(c[i - 1] - c[i])
        e2 = _unit(c[(i + 1) % k] - c[i])
        bis = e1 + e2
        if np.linalg.norm(bis) < 1e-9:
            bis = centre - c[i]
        bis = _unit(bis)
        half_sin = float(np.linalg.norm(np.cross(e1, bis)))
        move = min(d / max(half_sin, 0.1), 0.9 * float(np.linalg.norm(centre - c[i])))
        out.append(c[i] + bis * move)
    return np.asarray(out)


def min_bend_radius(points, corner_deg=45.0):
    """The tightest bend (m) of a polyline (its corners sharper than `corner_deg` are joints, not bends), or None."""
    p = np.asarray(points, float)
    best = None
    lim = math.cos(math.radians(corner_deg))
    for a, b, c in zip(p, p[1:], p[2:]):
        ab, bc, ca = b - a, c - b, a - c
        la, lb = np.linalg.norm(ab), np.linalg.norm(bc)
        if la < 1e-9 or lb < 1e-9 or float(ab @ bc) / (la * lb) < lim:
            continue
        cr = np.linalg.norm(np.cross(ab, bc))
        if cr < 1e-12:
            continue
        r = la * lb * float(np.linalg.norm(ca)) / (2.0 * cr)
        if r < 500.0 and (best is None or r < best):
            best = r
    return best


def _length(points, cyclic=False):
    p = np.asarray(points, float)
    if cyclic:
        p = np.vstack((p, p[:1]))
    return float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum())


def _quads_to_tris(q):
    """(n, 4) quads -> (2n, 3) triangles (0-1-2, 0-2-3)."""
    q = np.asarray(q, dtype=np.int64).reshape(-1, 4)
    return np.concatenate((q[:, [0, 1, 2]], q[:, [0, 2, 3]]))


def _cap(ring, start=0):
    """A convex-ish ring's cap as triangles (indices from `start`): a quad cut on its shorter diagonal, a fan else."""
    k = len(ring)
    if k == 4:
        r = np.asarray(ring, float)
        if np.sum((r[0] - r[2]) ** 2) <= np.sum((r[1] - r[3]) ** 2):
            return [[start, start + 1, start + 2], [start, start + 2, start + 3]]
        return [[start, start + 1, start + 3], [start + 1, start + 2, start + 3]]
    return [[start, start + i, start + i + 1] for i in range(1, k - 1)]


# ---------------------------------------------------------------- the pieces as triangles, by material

class Pieces:
    """Triangles gathered by material key: add(key, verts, tris)."""

    def __init__(self):
        self.parts = {}
        self.count = 0

    def add(self, key, verts, tris):
        verts = np.asarray(verts, dtype=float).reshape(-1, 3)
        tris = np.asarray(tris, dtype=np.int64).reshape(-1, 3)
        if not len(tris):
            return
        self.count += len(tris)
        if self.count > MAX_TRIANGLES:
            raise SurfaceError("construção pesada demais — reduza as divisões ou a perfuração")
        entry = self.parts.setdefault(key, [[], [], 0])
        entry[0].append(verts)
        entry[1].append(tris + entry[2])
        entry[2] += len(verts)

    def result(self):
        return {k: (np.concatenate(v), np.concatenate(t)) for k, (v, t, _n) in self.parts.items() if v}


def prisms(rings, cyclic=False):
    """Closed prisms through rings of corners (n_members, k_stations, c corners, 3): (verts, tris) — each member's
    sides outward (whatever way round its corners go), its ends capped unless cyclic."""
    R = np.asarray(rings, dtype=float)
    m, k, c = R.shape[:3]
    verts = R.reshape(-1, 3)
    base = (np.arange(m) * k * c)[:, None, None]
    # each member's way round: its sides outward when the corners go anticlockwise about the member's way
    t = R[:, min(1, k - 1)].mean(axis=1) - R[:, 0].mean(axis=1) if k > 1 else np.zeros((m, 3))
    turn = np.einsum("ij,ij->i", np.cross(R[:, 0, 1] - R[:, 0, 0], R[:, 0, 2] - R[:, 0, 1]), t)
    order = np.where(turn[:, None] >= 0, np.arange(c)[None, :], np.arange(c)[::-1][None, :])     # (m, c)
    spans = k if cyclic else k - 1
    s = np.arange(spans)
    e = np.arange(c)
    a0 = order[:, None, e] + (s[None, :, None] * c)                       # (m, spans, c) corner e at station s
    a1 = order[:, None, (e + 1) % c] + (s[None, :, None] * c)
    b0 = order[:, None, e] + (((s + 1) % k)[None, :, None] * c)
    b1 = order[:, None, (e + 1) % c] + (((s + 1) % k)[None, :, None] * c)
    quads = np.stack((a0, a1, b1, b0), axis=-1) + base[..., None]
    tris = [_quads_to_tris(quads.reshape(-1, 4))]
    if not cyclic:
        fan = np.array([[0, i, i + 1] for i in range(1, c - 1)])
        first = order[:, fan] + (np.arange(m) * k * c)[:, None, None]
        last = first + (k - 1) * c
        tris.append(first[:, :, ::-1].reshape(-1, 3))
        tris.append(last.reshape(-1, 3))
    return verts, np.concatenate(tris)


def member_rings(points, ups, width, depth, offset=0.0, cyclic=False, width1=None, depth1=None):
    """A profile width × depth following `points` (k, 3), its web along `ups` (k, 3), from `offset` to
    offset + depth off the line, centred across: its rings (k, 4, 3). width1/depth1: its size at the far end
    (tapered)."""
    p = np.asarray(points, float)
    k = len(p)
    if cyclic:
        t = np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)
    else:
        t = np.gradient(p, axis=0) if k > 2 else np.repeat((p[-1] - p[0])[None], k, axis=0)
    t = _unit(t, (1.0, 0.0, 0.0))
    up = np.asarray(ups, float)
    up = _unit(up - t * np.einsum("ij,ij->i", up, t)[:, None])
    lat = _unit(np.cross(t, up), (0.0, 1.0, 0.0))
    f = np.linspace(0.0, 1.0, k)[:, None]
    w = width + ((width1 if width1 is not None else width) - width) * f
    d = depth + ((depth1 if depth1 is not None else depth) - depth) * f
    base = p + up * offset
    half = lat * (w / 2.0)
    top = up * d
    return np.stack((base - half, base + half, base + half + top, base - half + top), axis=1)


def member_ups(samples, normals, orient):
    """The webs' way at each point of a member: the surface's normal, plumb, or carried along without spin."""
    p = np.asarray(samples, float)
    n = np.asarray(normals, float)
    t = _unit(np.gradient(p, axis=0) if len(p) > 2 else np.repeat((p[-1] - p[0])[None], len(p), axis=0),
              (1.0, 0.0, 0.0))
    if orient == "vertical":
        z = np.array((0.0, 0.0, 1.0))
        up = z - t * (t @ z)[:, None]
        bad = np.linalg.norm(up, axis=1) < 1e-6
        up[bad] = n[bad]
        return _unit(up)
    if orient == "smooth":
        out = np.empty_like(n)
        cur = n[0]
        for k in range(len(p)):
            cur = cur - t[k] * float(cur @ t[k])
            ln = np.linalg.norm(cur)
            cur = cur / ln if ln > 1e-9 else n[k]
            out[k] = cur
        return out
    return n


def bars(p0, p1, ups, size0, size1=None):
    """Straight square bars p0 → p1 (n, 3) each, their sides turned by `ups` (n, 3): (verts, tris) — centred on
    the line; size1: their size at p1 (tapered)."""
    p0, p1 = np.asarray(p0, float).reshape(-1, 3), np.asarray(p1, float).reshape(-1, 3)
    if not len(p0):
        return np.zeros((0, 3)), np.zeros((0, 3), np.int64)
    d = _unit(p1 - p0, (1.0, 0.0, 0.0))
    up = np.asarray(ups, float).reshape(-1, 3)
    lat = np.cross(d, up)
    weak = np.linalg.norm(lat, axis=1) < 1e-6
    if np.any(weak):
        alt = np.cross(d[weak], (1.0, 0.0, 0.0))
        alt2 = np.cross(d[weak], (0.0, 0.0, 1.0))
        lat[weak] = np.where(np.linalg.norm(alt, axis=1, keepdims=True) > 1e-6, alt, alt2)
    lat = _unit(lat)
    upv = _unit(np.cross(lat, d))
    s0 = np.broadcast_to(np.asarray(size0, float), (len(p0),))[:, None] / 2.0
    s1 = (np.broadcast_to(np.asarray(size1 if size1 is not None else size0, float), (len(p0),)))[:, None] / 2.0

    def ring(p, s):
        return np.stack((p - lat * s - upv * s, p + lat * s - upv * s, p + lat * s + upv * s, p - lat * s + upv * s),
                        axis=1)
    rings = np.stack((ring(p0, s0), ring(p1, s1)), axis=1)            # (n, 2, 4, 3)
    return prisms(rings)


def cubes(centres, size):
    c = np.asarray(centres, float).reshape(-1, 3)
    if not len(c):
        return np.zeros((0, 3)), np.zeros((0, 3), np.int64)
    h = size / 2.0
    rings = np.stack((c + (0, 0, -h), c + (0, 0, h)), axis=1)[:, :, None, :] + \
        np.array([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)])[None, None]
    return prisms(rings)


def discs(centres, axes, radius, thickness, segments=10):
    c = np.asarray(centres, float).reshape(-1, 3)
    if not len(c):
        return np.zeros((0, 3)), np.zeros((0, 3), np.int64)
    a = _unit(np.asarray(axes, float).reshape(-1, 3))
    x = np.cross(a, (1.0, 0.0, 0.0))
    weak = np.linalg.norm(x, axis=1) < 1e-6
    x[weak] = np.cross(a[weak], (0.0, 1.0, 0.0))
    x = _unit(x)
    y = np.cross(a, x)
    ang = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    ring = (np.cos(ang)[None, :, None] * x[:, None] + np.sin(ang)[None, :, None] * y[:, None]) * radius
    h = (a * thickness / 2.0)[:, None, :]
    rings = np.stack((c[:, None] - h + ring, c[:, None] + h + ring), axis=1)
    return prisms(rings)


def slab(corners, normal, thickness, base=0.0):
    """A plate over a flat-ish polygon: its bottom at `base` off it, its top `thickness` above, along `normal`."""
    c = np.asarray(corners, float)
    n = _unit(normal)
    if float(_poly_normal(c) @ n) < 0:
        c = c[::-1]
    k = len(c)
    bottom = c + n * base
    top = c + n * (base + thickness)
    verts = np.vstack((bottom, top))
    tris = [t[::-1] for t in _cap(c)] + _cap(c, k)
    for i in range(k):
        j = (i + 1) % k
        tris += [[i, j, k + j], [i, k + j, k + i]]
    return verts, np.asarray(tris)


def _poly_normal(p):
    n = np.zeros(3)
    for k in range(len(p)):
        n += np.cross(p[k], p[(k + 1) % len(p)])
    return _unit(n)


def slab_ring(outer, inner, normal, thickness):
    """A plate with an opening: the band between `outer` and `inner` (as many corners each), `thickness` along
    `normal`."""
    o, i = np.asarray(outer, float), np.asarray(inner, float)
    n = _unit(normal)
    if float(_poly_normal(o) @ n) < 0:
        o, i = o[::-1], i[::-1]
    k = len(o)
    top_o, top_i = o + n * thickness, i + n * thickness
    verts = np.vstack((o, i, top_o, top_i))       # 0..k-1 outer, k..2k-1 inner, 2k.. top outer, 3k.. top inner
    tris = []
    for a in range(k):
        b = (a + 1) % k
        tris += [[2 * k + a, 2 * k + b, 3 * k + b], [2 * k + a, 3 * k + b, 3 * k + a]]         # top band
        tris += [[a, k + b, b], [a, k + a, k + b]]                                             # bottom band
        tris += [[a, b, 2 * k + b], [a, 2 * k + b, 2 * k + a]]                                 # outer wall
        tris += [[k + a, 3 * k + b, k + b], [k + a, 3 * k + a, 3 * k + b]]                     # opening's wall
    return verts, np.asarray(tris)


def panel_slab(corners, normal, thickness, steps=3):
    """A warped quad as a plate following the bilinear patch of its corners (no crease), `thickness` along
    `normal`: steps × steps quads a side, its edges closed."""
    c = np.asarray(corners, float)
    if len(c) != 4:
        return slab(c, normal, thickness)
    n = _unit(normal)
    if float(_poly_normal(c) @ n) < 0:
        c = c[[0, 3, 2, 1]]
    s = np.linspace(0, 1, steps + 1)
    S, T = np.meshgrid(s, s, indexing="ij")                    # S along 0→1, T along 0→3
    P = ((1 - S) * (1 - T))[..., None] * c[0] + (S * (1 - T))[..., None] * c[1] + (S * T)[..., None] * c[2] + \
        ((1 - S) * T)[..., None] * c[3]
    m = steps + 1
    bottom = P.reshape(-1, 3)
    top = bottom + n * thickness
    verts = np.vstack((bottom, top))
    idx = np.arange(m * m).reshape(m, m)
    q = np.stack((idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]), axis=-1).reshape(-1, 4)
    tris = [_quads_to_tris(q + m * m), _quads_to_tris(q[:, ::-1])]
    border = list(idx[:, 0]) + list(idx[-1, 1:]) + list(idx[::-1, -1][1:]) + list(idx[0, ::-1][1:-1])
    walls = []
    for a, b in zip(border, border[1:] + border[:1]):
        walls.append([a, b, b + m * m, a + m * m])
    tris.append(_quads_to_tris(walls))
    return verts, np.concatenate(tris)


def inverse_bilinear(poly, p):
    """(s, t) in [0, 1]² of the plan point p in the quad poly (4, 2) (the addon's)."""
    a, b, c, d = (np.asarray(q, float) for q in poly)
    e, f, g, h = b - a, d - a, a - b + c - d, np.asarray(p, float) - a

    def cross2(u, v):
        return u[0] * v[1] - u[1] * v[0]
    k2, k1, k0 = cross2(g, f), cross2(e, f) + cross2(h, g), cross2(h, e)
    if abs(k2) < 1e-12:
        t = -k0 / k1 if abs(k1) > 1e-12 else 0.5
    else:
        disc = math.sqrt(max(k1 * k1 - 4 * k0 * k2, 0.0))
        t = (-k1 + disc) / (2 * k2)
        if not -0.001 <= t <= 1.001:
            t = (-k1 - disc) / (2 * k2)
    t = min(1.0, max(0.0, t))
    dx, dy = e[0] + g[0] * t, e[1] + g[1] * t
    s = (h[0] - f[0] * t) / dx if abs(dx) >= abs(dy) and abs(dx) > 1e-12 else \
        ((h[1] - f[1] * t) / dy if abs(dy) > 1e-12 else 0.5)
    return min(1.0, max(0.0, s)), t


def inverse_bilinear_many(poly, pts):
    """inverse_bilinear for many plan points (N, 2) at once: (s, t) arrays."""
    a, b, c, d = (np.asarray(q, float) for q in poly)
    p = np.asarray(pts, float).reshape(-1, 2)
    e, f, g = b - a, d - a, a - b + c - d
    h = p - a
    k2 = g[0] * f[1] - g[1] * f[0]
    k1 = (e[0] * f[1] - e[1] * f[0]) + (h[:, 0] * g[1] - h[:, 1] * g[0])
    k0 = h[:, 0] * e[1] - h[:, 1] * e[0]
    if abs(k2) < 1e-12:
        t = np.where(np.abs(k1) > 1e-12, -k0 / np.where(np.abs(k1) > 1e-12, k1, 1.0), 0.5)
    else:
        disc = np.sqrt(np.maximum(k1 * k1 - 4 * k0 * k2, 0.0))
        t = (-k1 + disc) / (2 * k2)
        t2 = (-k1 - disc) / (2 * k2)
        t = np.where((t >= -0.001) & (t <= 1.001), t, t2)
    t = np.clip(t, 0.0, 1.0)
    dx, dy = e[0] + g[0] * t, e[1] + g[1] * t
    use_x = np.abs(dx) >= np.abs(dy)
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(use_x, (h[:, 0] - f[0] * t) / np.where(np.abs(dx) > 1e-12, dx, 1.0),
                     (h[:, 1] - f[1] * t) / np.where(np.abs(dy) > 1e-12, dy, 1.0))
    s = np.where(np.maximum(np.abs(dx), np.abs(dy)) > 1e-12, s, 0.5)
    return np.clip(s, 0.0, 1.0), t


# ---------------------------------------------------------------- the surface as a continuous (u, v) sampler

class Grid:
    def __init__(self, rows, close_u, trims=()):
        self.rows = np.asarray(rows, float)
        self.close_u = bool(close_u)
        self.trims = list(trims)
        self.nr, self.nc = self.rows.shape[:2]
        normals = grid_normals(self.rows, close_u)
        self.flipped = float(normals[..., 2].sum()) < -1e-6       # (the outside of a roof or a façade: up)
        self.normals = -normals if self.flipped else normals

    def _cell(self, u, v):
        u, v = np.asarray(u, float), np.asarray(v, float)
        if self.close_u:
            u = np.mod(u, 1.0)
            fu = u * self.nc
            i0 = np.minimum(np.floor(fu).astype(int), self.nc - 1)
            i1 = (i0 + 1) % self.nc
        else:
            u = np.clip(u, 0.0, 1.0)
            fu = u * (self.nc - 1)
            i0 = np.clip(np.floor(fu).astype(int), 0, self.nc - 2)
            i1 = i0 + 1
        v = np.clip(v, 0.0, 1.0)
        fv = v * (self.nr - 1)
        j0 = np.clip(np.floor(fv).astype(int), 0, self.nr - 2)
        return i0, i1, j0, j0 + 1, (fu - i0)[..., None], (fv - j0)[..., None]

    def _bilinear(self, field, u, v):
        i0, i1, j0, j1, a, b = self._cell(u, v)
        return (field[j0, i0] * (1 - a) * (1 - b) + field[j0, i1] * a * (1 - b) + field[j1, i1] * a * b +
                field[j1, i0] * (1 - a) * b)

    def point(self, u, v):
        return self._bilinear(self.rows, u, v)

    def normal(self, u, v):
        return _unit(self._bilinear(self.normals, u, v))

    def kept(self, points):
        return kept(np.asarray(points, float)[..., :2], self.trims)

    def iso(self, direction, s, count):
        """(points, normals) along the line `direction` ("u": u running, v = s) — count samples."""
        t = np.linspace(0.0, 1.0, count)
        u, v = (t, np.full_like(t, s)) if direction == "u" else (np.full_like(t, s), t)
        return self.point(u, v), self.normal(u, v)

    def has_pole(self):
        return any(np.all(np.linalg.norm(r - r[0], axis=1) < 1e-6) for r in self.rows)

    def runs(self, points, normals):
        """The polyline split where the trims take it away: [(points, normals)] of 2 points or more."""
        ok = self.kept(points)
        out, start = [], None
        for k, flag in enumerate(list(ok) + [False]):
            if flag and start is None:
                start = k
            elif not flag and start is not None:
                if k - start >= 2:
                    out.append((points[start:k], normals[start:k]))
                start = None
        return out

    def boundary_loops(self):
        """The edge as closed loops: closed in u — its two rings; else one loop round the grid."""
        R = self.rows
        if self.close_u:
            return [R[0], R[-1]]
        loop = np.vstack((R[0, :], R[1:, -1], R[-1, -2::-1], R[-2:0:-1, 0]))
        return [loop]


# ---------------------------------------------------------------- the builder

def _number(sec, name, key, env, default, positive=False, whole=False):
    try:
        v = expr.number(sec.get(key, default), env, "build.{}.{}".format(name, key))
    except expr.ExprError as exc:
        raise SurfaceError(str(exc)) from None
    if positive and v <= 0:
        raise SurfaceError("build.{}.{}: tem de ser positivo".format(name, key))
    return int(round(v)) if whole else v


def build(surface, sections=None, mask_loader=None):
    """The construction of a worked-out surface (param_surface.Surface): (pieces {material key: (verts, tris)},
    parts [dict], warnings [str]). `sections` the definition's «build» (else its own); `mask_loader(path)` → an
    image's brightness array (rows top to bottom, values 0–1) or None."""
    data = sections if sections is not None else (surface.data.get("build") or {})
    grid = Grid(surface.rows, surface.close_u, surface.trims)
    out = Pieces()
    parts, warnings = [], []
    env = surface.env
    for name in SECTIONS:
        sec = data.get(name)
        if not isinstance(sec, dict) or sec.get("enabled", True) is False:
            continue
        family = SECTION_FAMILY[name]
        own = sec.get("material") or FAMILIES[family]
        ctx = _Context(grid, out, parts, warnings, env, name, sec, own, mask_loader)
        BUILDERS[name](ctx)
    for k, p in enumerate(parts):
        p["id"] = "SRF-P{:02d}".format(k + 1)
    return out.result(), parts, warnings


class _Context:
    def __init__(self, grid, out, parts, warnings, env, name, sec, material, mask_loader):
        self.grid, self.out, self.parts, self.warnings = grid, out, parts, warnings
        self.env, self.name, self.sec, self.material = env, name, sec, material
        self.mask_loader = mask_loader

    def num(self, key, positive=False, whole=False):
        return _number(self.sec, self.name, key, self.env, TEMPLATES[self.name].get(key, 0.0), positive, whole)

    def choice(self, key):
        v = self.sec.get(key, TEMPLATES[self.name].get(key))
        allowed = CHOICES.get((self.name, key))
        if allowed and v not in allowed:
            raise SurfaceError("build.{}.{}: um de {}".format(self.name, key, ", ".join(allowed)))
        return v

    def add(self, verts, tris, material=None):
        self.out.add(material or self.material, verts, tris)


def _members(ctx, runs_of, label, kind, width, depth, offset, orient, cyclic=False):
    """Profiles along polylines [(name, points, normals)] — their pieces and their parts."""
    rings, closed_rings = [], []
    for nm, pts, nrm in runs_of:
        ups = member_ups(pts, nrm, orient)
        r = member_rings(pts, ups, width, depth, offset, cyclic)
        (closed_rings if cyclic else rings).append(r)
        part = {"name": nm, "kind": kind, "count": 1, "linear": True, "length": round(_length(pts, cyclic), 3),
                "width": width, "depth": depth}
        radius = min_bend_radius(np.vstack((pts, pts[:2])) if cyclic else pts)
        if radius is not None:
            part["radius"] = round(radius, 3)
        ctx.parts.append(part)
    for group, cyc in ((rings, False), (closed_rings, True)):
        if not group:
            continue
        by_len = {}
        for r in group:
            by_len.setdefault(len(r), []).append(r)
        for same in by_len.values():
            v, t = prisms(np.stack(same), cyclic=cyc)
            ctx.add(v, t)


def _iso_runs(ctx, direction, stations, label, prefix, offset_fn=None):
    g = ctx.grid
    n_axis = g.nc if direction == "u" else g.nr
    count = max(n_axis * 2, 24)
    out = []
    for k, s in enumerate(stations):
        pts, nrm = g.iso(direction, s, count)
        if offset_fn is not None:
            pts = pts + nrm * offset_fn(k, len(pts))[:, None]
        runs = g.runs(pts, nrm)
        for r, (p, n) in enumerate(runs):
            suffix = "" if len(runs) == 1 else "abcdefghijklmnopqrstuvwxyz"[r % 26]
            out.append(("{} {} {:02d}{}".format(prefix, direction.upper(), k + 1, suffix), p, n))
    return out


def _build_shell(ctx):
    g = ctx.grid
    if g.has_pole():
        raise SurfaceError("superfícies com polo (revolução ou tampa em anéis) ainda não levam casca — use a grelha "
                           "de quatro lados")
    t = ctx.num("thickness", positive=True)
    lo, hi = {"center": (-t / 2, t / 2), "out": (0.0, t), "in": (-t, 0.0)}[ctx.choice("offset")]
    R, N = g.rows, g.normals
    nr, nc = g.nr, g.nc
    top = (R + N * hi).reshape(-1, 3)
    bot = (R + N * lo).reshape(-1, 3)
    idx = np.arange(nr * nc).reshape(nr, nc)
    cols = nc if g.close_u else nc - 1
    cells = []
    for j in range(nr - 1):
        for i in range(cols):
            i1 = (i + 1) % nc
            cells.append((idx[j, i], idx[j, i1], idx[j + 1, i1], idx[j + 1, i]))
    cells = np.asarray(cells, dtype=np.int64)
    mids = R.reshape(-1, 3)[cells].mean(axis=1)
    cells = cells[g.kept(mids)]
    if not len(cells):
        raise SurfaceError("o recorte tirou toda a casca")
    q_top = cells[:, ::-1] if g.flipped else cells
    q_bot = cells if g.flipped else cells[:, ::-1]
    m = nr * nc
    verts = np.vstack((top, bot))
    tris = [_quads_to_tris(q_top), _quads_to_tris(q_bot + m)]
    uses = {}
    for c in cells:
        for a, b in ((c[0], c[1]), (c[1], c[2]), (c[2], c[3]), (c[3], c[0])):
            key = (min(a, b), max(a, b))
            uses.setdefault(key, []).append((a, b, c))
    walls = []
    flat = R.reshape(-1, 3)
    for key, used in uses.items():
        if len(used) != 1:
            continue
        a, b, c = used[0]
        quad = [a, b, b + m, a + m]
        wn = np.cross(verts[quad[1]] - verts[quad[0]], verts[quad[2]] - verts[quad[1]])
        out_dir = (flat[a] + flat[b]) / 2 - flat[list(c)].mean(axis=0)
        walls.append(quad if float(wn @ out_dir) >= 0 else quad[::-1])
    if walls:
        tris.append(_quads_to_tris(walls))
    ctx.add(verts, np.concatenate(tris))
    P = flat[cells]
    area = 0.5 * (np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 3] - P[:, 0]), axis=1) +
                  np.linalg.norm(np.cross(P[:, 1] - P[:, 2], P[:, 3] - P[:, 2]), axis=1)).sum()
    ctx.parts.append({"name": "Casca", "kind": "casca", "area": round(float(area), 3), "thickness": t, "count": 1})


def _build_ribs(ctx):
    cu, cv = ctx.num("count_u", whole=True), ctx.num("count_v", whole=True)
    if cu <= 0 and cv <= 0:
        raise SurfaceError("build.ribs: pelo menos uma nervura (count_u ou count_v)")
    w, d = ctx.num("width", positive=True), ctx.num("depth", positive=True)
    orient = ctx.choice("orient")
    runs = _iso_runs(ctx, "u", _stations(cu), "nervura", "Nervura") + \
        _iso_runs(ctx, "v", _stations(cv), "nervura", "Nervura")
    _members(ctx, runs, "Nervura", "nervura", w, d, 0.0, orient)


def _build_slats(ctx):
    direction = ctx.choice("direction")
    n = ctx.num("count", positive=True, whole=True)
    w, d = ctx.num("width", positive=True), ctx.num("depth", positive=True)
    off = ctx.num("offset")
    runs = _iso_runs(ctx, direction, _stations(n, ends=False), "ripa", "Ripa")
    _members(ctx, runs, "Ripa", "ripa", w, d, off, ctx.choice("orient"))


def _build_weave(ctx):
    g = ctx.grid
    cu, cv = ctx.num("count_u", positive=True, whole=True), ctx.num("count_v", positive=True, whole=True)
    w, d = ctx.num("width", positive=True), ctx.num("depth", positive=True)
    amp, off = ctx.num("amplitude"), ctx.num("offset")
    runs = []
    for direction, count, crossings in (("u", cu, cv), ("v", cv, cu)):
        n_axis = g.nc if direction == "u" else g.nr
        samples = max(n_axis * 2, crossings * 6, 48)
        for k in range(count):
            s = (k + 0.5) / count
            sign = (1.0 if k % 2 == 0 else -1.0) * (-1.0 if direction == "v" else 1.0)
            pts, nrm = g.iso(direction, s, samples)
            t = np.linspace(0.0, 1.0, samples)
            lift = amp * sign * np.sin(np.pi * crossings * t)
            pts = pts + nrm * (off + lift)[:, None]
            for r, (p, nn) in enumerate(g.runs(pts, nrm)):
                runs.append(("Fita {} {:02d}{}".format(direction.upper(), k + 1, "" if not r else "abc"[r % 3]), p, nn))
    _members(ctx, runs, "Fita", "fita", w, d, -d / 2.0, "normal")


def _hex_lattice(nu, nv):
    off = [(0.0, 0.5), (0.433, 0.25), (0.433, -0.25), (0.0, -0.5), (-0.433, -0.25), (-0.433, 0.25)]
    span_u, span_v = 0.866 * nu + 0.433, 0.75 * nv + 0.75
    nodes, bars_ = {}, set()
    for j in range(nv):
        for i in range(nu):
            cx, cy = 0.866 * i + (0.433 if j % 2 else 0.0), 0.75 * j + 0.5
            keys = []
            for dx, dy in off:
                u = min(1.0, max(0.0, (cx + dx + 0.433) / span_u))
                v = min(1.0, max(0.0, (cy + dy) / span_v))
                key = (round(u, 5), round(v, 5))
                nodes[key] = (u, v)
                keys.append(key)
            for a, b in zip(keys, keys[1:] + keys[:1]):
                bars_.add((min(a, b), max(a, b)))
    return nodes, bars_


def _build_gridshell(ctx):
    g = ctx.grid
    mode = ctx.choice("mode")
    nu, nv = ctx.num("u", positive=True, whole=True), ctx.num("v", positive=True, whole=True)
    if nu > 128 or nv > 128:
        raise SurfaceError("build.gridshell: no máximo 128 divisões")
    size = ctx.num("size", positive=True)
    orient = ctx.choice("orient")
    if mode == "hex":
        lattice, pairs = _hex_lattice(nu, nv)
        keys = list(lattice)
        uv = np.array([lattice[k] for k in keys])
        pts, nrm = g.point(uv[:, 0], uv[:, 1]), g.normal(uv[:, 0], uv[:, 1])
        ok = g.kept(pts)
        where = {k: n for n, k in enumerate(keys)}
        edges = [(where[a], where[b]) for a, b in pairs if ok[where[a]] and ok[where[b]]]
    else:
        cols = nu if g.close_u else nu + 1
        J, I = np.meshgrid(np.arange(nv + 1), np.arange(cols), indexing="ij")
        u, v = I / nu, J / nv
        pts = g.point(u.ravel(), v.ravel())
        nrm = g.normal(u.ravel(), v.ravel())
        ok = g.kept(pts)
        node = lambda j, i: j * cols + i                           # noqa: E731
        edges = []
        for j in range(nv + 1):
            for i in range(cols):
                right = (i + 1) % cols if g.close_u else i + 1
                has_right = g.close_u or i + 1 <= nu
                if mode in ("quad", "tri"):
                    if has_right:
                        edges.append((node(j, i), node(j, right)))
                    if j < nv:
                        edges.append((node(j, i), node(j + 1, i)))
                if j < nv and has_right:
                    if mode == "tri":
                        edges.append((node(j, i), node(j + 1, right)) if (i + j) % 2 == 0 else
                                     (node(j, right), node(j + 1, i)))
                    elif mode == "diagrid":
                        edges += [(node(j, i), node(j + 1, right)), (node(j, right), node(j + 1, i))]
        edges = [(a, b) for a, b in edges if ok[a] and ok[b]]
    if not edges:
        raise SurfaceError("o gridshell ficou sem barras (o recorte tirou tudo?)")
    e = np.asarray(edges, dtype=np.int64)
    up = np.tile((0.0, 0.0, 1.0), (len(e), 1)) if orient == "vertical" else nrm[e[:, 0]] + nrm[e[:, 1]]
    v_, t_ = bars(pts[e[:, 0]], pts[e[:, 1]], up, size)
    ctx.add(v_, t_)
    lengths = np.round(np.linalg.norm(pts[e[:, 1]] - pts[e[:, 0]], axis=1), 3)
    for length, count in zip(*np.unique(lengths, return_counts=True)):
        ctx.parts.append({"name": "Barra {:.3f} m".format(length), "kind": "barra", "count": int(count),
                          "linear": True, "length": float(length), "size": size})
    if bool(ctx.sec.get("nodes", True)):
        ns = ctx.sec.get("node_size")
        ns = _number(ctx.sec, "gridshell", "node_size", ctx.env, max(1.8 * size, 0.02), True) if ns is not None \
            else max(1.8 * size, 0.02)
        used = np.unique(e.ravel())
        v_, t_ = cubes(pts[used], ns)
        ctx.add(v_, t_, FAMILIES["ferragem"])
        ctx.parts.append({"name": "Nó gridshell", "kind": "no", "count": int(len(used)), "hardware": True,
                          "size": ns})


def _build_edge(ctx):
    w, d = ctx.num("width", positive=True), ctx.num("depth", positive=True)
    orient = ctx.choice("orient")
    g = ctx.grid
    runs = []
    for k, loop in enumerate(g.boundary_loops()):
        loop = np.asarray(loop, float)
        if len(loop) < 3:
            continue
        nrm = _closest_normals(g, loop)
        runs.append(("Anel de bordo {:02d}".format(k + 1), loop, nrm))
    if not runs:
        raise SurfaceError("a superfície não tem bordo")
    _members(ctx, runs, "Anel de bordo", "bordo", w, d, 0.0, orient, cyclic=True)


def _closest_normals(g, pts):
    flat, nrm = g.rows.reshape(-1, 3), g.normals.reshape(-1, 3)
    out = []
    for p in pts:
        out.append(nrm[int(np.argmin(np.sum((flat - p) ** 2, axis=1)))])
    return np.asarray(out)


def _build_supports(ctx):
    g = ctx.grid
    count = ctx.num("count", positive=True, whole=True)
    size = ctx.num("size", positive=True)
    base_z = ctx.num("base_z")
    pts = np.vstack(g.boundary_loops())
    order = np.argsort(pts[:, 2], kind="stable")
    span = max(float(np.ptp(pts[:, 0])), float(np.ptp(pts[:, 1])), 1.0)
    gap = span / (2.0 * count)
    picked = []
    for k in order:
        p = pts[k]
        if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= gap for q in picked):
            picked.append(p)
        if len(picked) >= count:
            break
    tops, bottoms = [], []
    for n, p in enumerate(picked):
        if p[2] - base_z <= 1e-6:
            ctx.warnings.append("pilar {}: o ponto de apoio já está abaixo da base".format(n + 1))
            continue
        tops.append(p)
        bottoms.append((p[0], p[1], base_z))
    if tops:
        v_, t_ = bars(np.asarray(bottoms), np.asarray(tops), np.tile((0.0, 1.0, 0.0), (len(tops), 1)), size)
        ctx.add(v_, t_)
    for n, (b, p) in enumerate(zip(bottoms, tops)):
        ctx.parts.append({"name": "Pilar {:02d}".format(n + 1), "kind": "pilar", "count": 1,
                          "height": round(float(p[2] - b[2]), 3), "size": size})


def _cell_corners(g, i, j, nu, nv):
    u0, u1, v0, v1 = i / nu, (i + 1) / nu, j / nv, (j + 1) / nv
    c = g.point(np.array((u0, u1, u1, u0)), np.array((v0, v0, v1, v1)))
    return c[::-1] if g.flipped else c


def _mask_sampler(ctx, invert):
    path = ctx.sec.get("mask") or ""
    if not path:
        return None
    img = ctx.mask_loader(path) if ctx.mask_loader is not None else None
    if img is None:
        ctx.warnings.append("imagem '{}' não encontrada — ignorada".format(path))
        return None
    img = np.asarray(img, float)
    h, w = img.shape[:2]

    def sample(u, v):
        x = min(w - 1, max(0, int(u * w)))
        y = min(h - 1, max(0, int((1.0 - v) * h)))
        val = float(img[y, x])
        return 1.0 - val if invert else val
    return sample


def _build_panels(ctx):
    g = ctx.grid
    pattern, kind = ctx.choice("pattern"), ctx.choice("kind")
    nu, nv = ctx.num("u", positive=True, whole=True), ctx.num("v", positive=True, whole=True)
    if nu > 128 or nv > 128:
        raise SurfaceError("build.panels: no máximo 128 divisões")
    thick, gap = ctx.num("thickness", positive=True), max(0.0, ctx.num("gap"))
    max_warp, frame = ctx.num("max_warp"), max(0.0, ctx.num("frame"))
    try:
        fill = expr.field(ctx.sec.get("fill", 1.0), ctx.env, ("u", "v"), "build.panels.fill")
        opening = expr.field(ctx.sec.get("open", 0.0), ctx.env, ("u", "v"), "build.panels.open")
    except expr.ExprError as exc:
        raise SurfaceError(str(exc)) from None
    mask = _mask_sampler(ctx, bool(ctx.sec.get("mask_invert", False)))
    perf = bool(ctx.sec.get("perf", False))
    family = PANEL_FAMILY[kind]
    material = ctx.sec.get("material") or FAMILIES[family]
    budget = [MAX_HOLES]
    warped = dropped = holes_total = 0
    open_total = 0.0
    for j in range(nv):
        for i in range(nu):
            uc, vc = (i + 0.5) / nu, (j + 0.5) / nv
            try:
                if float(np.asarray(fill(u=uc, v=vc))) < 0.5:
                    dropped += 1
                    continue
                hole_value = float(np.asarray(opening(u=uc, v=vc)))
            except expr.ExprError as exc:
                raise SurfaceError(str(exc)) from None
            cell = _cell_corners(g, i, j, nu, nv)
            centre = g.point(uc, vc)
            if not np.all(g.kept(np.vstack((cell, centre[None])))):
                continue
            normal = g.normal(uc, vc)
            faces = [cell] if pattern == "quad" else [cell[[0, 1, 2]], cell[[0, 2, 3]]]
            for f_k, face in enumerate(faces):
                tag = "{:02d}x{:02d}{}".format(i + 1, j + 1, "" if pattern == "quad" else "ab"[f_k])
                outer = inset(face, gap / 2.0)
                warp = panel_warp(outer)
                high = warp > max_warp
                warped += int(high)
                edges = [float(np.linalg.norm(outer[(k + 1) % len(outer)] - outer[k])) for k in range(len(outer))]
                area = polygon_area(outer)
                row = {"name": "Painel " + tag, "kind": PANEL_KIND[kind], "count": 1, "width": round(max(edges), 3),
                       "height": round(min(edges), 3), "thickness": thick, "area": round(area, 3),
                       "warp": round(warp, 4)}
                if high:
                    row["warp_high"] = True
                if frame > 1e-6:
                    inner = inset(outer, frame)
                    for k in range(len(outer)):
                        k1 = (k + 1) % len(outer)
                        v_, t_ = slab(np.array((outer[k], outer[k1], inner[k1], inner[k])), normal, thick)
                        ctx.add(v_, t_, FAMILIES["metal"])
                    v_, t_ = slab(inner, normal, thick * 0.4, base=thick * 0.3)
                    ctx.add(v_, t_, FAMILIES["vidro"])
                    a_in = polygon_area(inner)
                    ctx.parts.append({"name": "Caixilho " + tag, "kind": "caixilho", "count": 1,
                                      "thickness": thick, "area": round(area - a_in, 3)})
                    ctx.parts.append({"name": "Vidro " + tag, "kind": "vidro", "count": 1, "thickness": thick * 0.4,
                                      "area": round(a_in, 3), "warp": round(warp, 4)})
                    continue
                if perf:
                    n_holes, open_area = _perforated(ctx, outer, normal, thick, (i, j, nu, nv), mask, budget,
                                                     material)
                    holes_total += n_holes
                    open_total += open_area
                    if n_holes:
                        row.update(holes=n_holes, open_area=round(open_area, 4), area=round(area - open_area, 3))
                    ctx.parts.append(row)
                    continue
                hole = hole_value * (mask(uc, vc) if mask is not None else 1.0)
                hole = min(0.92, max(0.0, hole))
                if hole > 1e-4:
                    c0 = outer.mean(axis=0)
                    inner = c0 + (outer - c0) * math.sqrt(hole)
                    v_, t_ = slab_ring(outer, inner, normal, thick)
                    ctx.add(v_, t_, material)
                    row.update(open=round(hole, 3), area=round(area * (1.0 - hole), 3))
                elif len(outer) == 4:
                    v_, t_ = panel_slab(outer, normal, thick)
                    ctx.add(v_, t_, material)
                else:
                    v_, t_ = slab(outer, normal, thick)
                    ctx.add(v_, t_, material)
                ctx.parts.append(row)
    if warped:
        ctx.warnings.append("{} painel(éis) acima da planaridade admissível ({:.3f} m)".format(warped, max_warp))
    if dropped:
        ctx.warnings.append("{} célula(s) abertas pela expressão 'fill' (fachada pixel)".format(dropped))
    if holes_total:
        ctx.warnings.append("{} furo(s) nos painéis — {:.2f} m2 de área aberta".format(holes_total, open_total))
    if budget[0] <= 0:
        ctx.warnings.append("perfuração parada aos {} furos — aumente o espaçamento ou reduza a grelha".format(
            MAX_HOLES))


def _perforated(ctx, outer, normal, thick, cell, mask, budget, material):
    """A panel with real holes cut in it (round, a grid along its own edges, their size by the image): (holes,
    open area)."""
    spacing = _number(ctx.sec, "panels", "perf_spacing", ctx.env, 0.08, True)
    pmin = max(0.0, _number(ctx.sec, "panels", "perf_min", ctx.env, 0.006))
    pmax = max(pmin, _number(ctx.sec, "panels", "perf_max", ctx.env, 0.05))
    margin = max(0.0, _number(ctx.sec, "panels", "perf_margin", ctx.env, 0.02))
    i, j, nu, nv = cell
    n = _unit(normal)
    o = outer[0]
    x = outer[1] - outer[0]
    x = _unit(x - n * float(x @ n))
    y = np.cross(n, x)
    rel = outer - o
    poly2d = np.column_stack((rel @ x, rel @ y))
    heights = rel @ n
    quad = len(outer) == 4
    if quad:
        span_s = (np.linalg.norm(outer[1] - outer[0]) + np.linalg.norm(outer[2] - outer[3])) / 2
        span_t = (np.linalg.norm(outer[3] - outer[0]) + np.linalg.norm(outer[2] - outer[1])) / 2
    else:
        span_s = span_t = math.sqrt(max(polygon_area(outer), 1e-9))
    steps_s, steps_t = max(int(round(span_s / spacing)), 1), max(int(round(span_t / spacing)), 1)
    from shapely.geometry import Polygon
    shape = Polygon(poly2d)
    if not shape.is_valid or shape.area < 1e-6:
        v_, t_ = slab(outer, n, thick)
        ctx.add(v_, t_, material)
        return 0, 0.0
    import shapely
    holes, open_area = [], 0.0
    ang = np.linspace(0, 2 * np.pi, HOLE_SIDES, endpoint=False)[::-1]          # (clockwise)
    FS, FT = np.meshgrid((np.arange(steps_s) + 0.5) / steps_s, (np.arange(steps_t) + 0.5) / steps_t, indexing="ij")
    FS, FT = FS.ravel(), FT.ravel()
    if quad:
        P = ((1 - FS) * (1 - FT))[:, None] * poly2d[0] + (FS * (1 - FT))[:, None] * poly2d[1] + \
            (FS * FT)[:, None] * poly2d[2] + ((1 - FS) * FT)[:, None] * poly2d[3]
    else:
        lo, hi = poly2d.min(axis=0), poly2d.max(axis=0)
        P = lo + (hi - lo) * np.column_stack((FS, FT))
    values = np.array([mask((i + fs) / nu, (j + ft) / nv) for fs, ft in zip(FS, FT)]) if mask is not None \
        else np.ones(len(FS))
    R = (pmin + (pmax - pmin) * values) / 2.0
    inside = shapely.contains_xy(shape, P[:, 0], P[:, 1])
    room = shapely.distance(shape.exterior, shapely.points(P))
    ok = (R > 1e-5) & inside & (room >= R + margin)
    for p, r in zip(P[ok], R[ok]):
        if budget[0] <= 0:
            break
        holes.append(np.column_stack((p[0] + r * np.cos(ang), p[1] + r * np.sin(ang))))
        open_area += math.pi * r * r
        budget[0] -= 1
    if not holes:
        if quad:
            v_, t_ = panel_slab(outer, n, thick)
        else:
            v_, t_ = slab(outer, n, thick)
        ctx.add(v_, t_, material)
        return 0, 0.0
    import shapely
    region = Polygon(poly2d, [h for h in holes])
    try:
        tris_geom = shapely.constrained_delaunay_triangles(region)
    except Exception:                      # noqa: BLE001  (no CDT: a solid plate rather than none)
        v_, t_ = slab(outer, n, thick)
        ctx.add(v_, t_, material)
        return 0, 0.0
    tri_pts = []
    for poly in getattr(tris_geom, "geoms", ()):
        c = np.asarray(poly.exterior.coords)[:3]
        tri_pts.append(c)
    if not tri_pts:
        v_, t_ = slab(outer, n, thick)
        ctx.add(v_, t_, material)
        return 0, 0.0
    tri_pts = np.asarray(tri_pts)                                   # (T, 3, 2)

    def height_at(pts2):
        if not quad:
            # a triangle: its plane
            a_, b_, c_ = poly2d
            m = np.array([[b_[0] - a_[0], c_[0] - a_[0]], [b_[1] - a_[1], c_[1] - a_[1]]])
            try:
                inv = np.linalg.inv(m)
            except np.linalg.LinAlgError:
                return np.zeros(len(pts2))
            st = (np.asarray(pts2) - a_) @ inv.T
            return heights[0] + st[:, 0] * (heights[1] - heights[0]) + st[:, 1] * (heights[2] - heights[0])
        s_, t_ = inverse_bilinear_many(poly2d, pts2)
        return ((1 - s_) * (1 - t_) * heights[0] + s_ * (1 - t_) * heights[1] + s_ * t_ * heights[2] +
                (1 - s_) * t_ * heights[3])

    flat = tri_pts.reshape(-1, 2)
    keys, inverse = np.unique(np.round(flat, 9), axis=0, return_inverse=True)
    h = height_at(keys)
    base = o + keys[:, :1] * x + keys[:, 1:2] * y + h[:, None] * n
    tri_idx = inverse.reshape(-1, 3)
    # each triangle turned to face along n (up)
    e1 = keys[tri_idx[:, 1]] - keys[tri_idx[:, 0]]
    e2 = keys[tri_idx[:, 2]] - keys[tri_idx[:, 0]]
    flip = (e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) < 0
    tri_idx[flip] = tri_idx[flip][:, ::-1]
    m = len(base)
    verts = [base, base + n * thick]
    tris = [tri_idx[:, ::-1], tri_idx + m]
    count = 2 * m
    # walls: the outline (anticlockwise) and each hole (clockwise), bottom to top
    ring2 = poly2d if Polygon(poly2d).exterior.is_ccw else poly2d[::-1]
    for loop in [ring2] + holes:
        lb = o + loop[:, :1] * x + loop[:, 1:2] * y + height_at(loop)[:, None] * n
        lt = lb + n * thick
        k = len(loop)
        verts += [lb, lt]
        a_ = np.arange(k)
        b_ = (a_ + 1) % k
        tris.append(_quads_to_tris(np.column_stack((a_, b_, b_ + k, a_ + k)) + count))
        count += 2 * k
    ctx.add(np.vstack(verts), np.concatenate(tris), material)
    return len(holes), open_area


def _build_spider(ctx):
    g = ctx.grid
    nu, nv = ctx.num("u", positive=True, whole=True), ctx.num("v", positive=True, whole=True)
    if nu > 128 or nv > 128:
        raise SurfaceError("build.spider: no máximo 128 divisões")
    thick, gap = ctx.num("thickness", positive=True), max(0.0, ctx.num("gap"))
    arm, reach, size = ctx.num("arm", positive=True), ctx.num("reach", positive=True), ctx.num("size", positive=True)
    glass = ctx.sec.get("material") if ctx.sec.get("material") else FAMILIES["vidro"]
    panes = {}
    for j in range(nv):
        for i in range(nu):
            uc, vc = (i + 0.5) / nu, (j + 0.5) / nv
            cell = _cell_corners(g, i, j, nu, nv)
            centre = g.point(uc, vc)
            if not np.all(g.kept(np.vstack((cell, centre[None])))):
                continue
            normal = g.normal(uc, vc)
            outer = inset(cell, gap / 2.0)
            v_, t_ = slab(outer + normal * arm, normal, thick)
            ctx.add(v_, t_, glass)
            panes[(i, j)] = (outer, normal, outer.mean(axis=0))
            edges = [float(np.linalg.norm(outer[(k + 1) % 4] - outer[k])) for k in range(4)]
            ctx.parts.append({"name": "Vidro {:02d}x{:02d}".format(i + 1, j + 1), "kind": "vidro", "count": 1,
                              "width": round(max(edges), 3), "height": round(min(edges), 3), "thickness": thick,
                              "area": round(polygon_area(outer), 3)})
    hw = FAMILIES["ferragem"]
    by_arms, bolts = {}, 0
    stand_a, stand_b, arm_a, arm_b, pins, washers, hubs = [], [], [], [], [], [], []
    for j in range(nv + 1):
        for i in range(nu + 1):
            base = g.point(i / nu, j / nv)
            if not np.all(g.kept(base[None])):
                continue
            around = [panes[c] for c in ((i, j), (i - 1, j), (i - 1, j - 1), (i, j - 1)) if c in panes]
            if not around:
                continue
            up = g.normal(i / nu, j / nv)
            hub = base + up * max(arm - 1.2 * size, 0.3 * arm)
            stand_a.append(base)
            stand_b.append(hub)
            hubs.append((hub, up))
            for outer, normal, centre in around:
                corner = outer[int(np.argmin(np.linalg.norm(outer - base, axis=1)))]     # (the corner at this node)
                to_c = centre - corner
                anchor = corner + _unit(to_c) * min(reach, 0.45 * float(np.linalg.norm(to_c)))
                end = anchor + normal * (arm - 0.1 * size)
                arm_a.append(hub)
                arm_b.append(end)
                pins.append((anchor + normal * (arm + thick / 2.0), normal))
                washers.append((anchor + normal * (arm - 0.05 * size), normal))
                washers.append((anchor + normal * (arm + thick + 0.05 * size), normal))
                bolts += 1
            by_arms[len(around)] = by_arms.get(len(around), 0) + 1
    if stand_a:
        sa, sb = np.asarray(stand_a), np.asarray(stand_b)
        v_, t_ = bars(sa, sb, np.tile((1.0, 0.0, 0.0), (len(sa), 1)) + 0.0, size * 0.5, size * 0.38)
        ctx.add(v_, t_, hw)
    if arm_a:
        aa, ab = np.asarray(arm_a), np.asarray(arm_b)
        v_, t_ = bars(aa, ab, np.tile((0.0, 0.0, 1.0), (len(aa), 1)), size * 0.4, size * 0.18)
        ctx.add(v_, t_, hw)
    for items, radius, height in ((pins, 0.1 * size, thick + 0.4 * size), (washers, 0.26 * size, 0.1 * size),
                                  (hubs, 0.55 * size, 0.4 * size)):
        if items:
            v_, t_ = discs(np.array([c for c, _a in items]), np.array([a for _c, a in items]), radius, height)
            ctx.add(v_, t_, hw)
    for k in sorted(by_arms):
        ctx.parts.append({"name": "Aranha {} ponta(s)".format(k), "kind": "aranha", "count": by_arms[k],
                          "hardware": True})
    if bolts:
        ctx.parts.append({"name": "Rótula", "kind": "rotula", "count": bolts, "hardware": True})


BUILDERS = {"shell": _build_shell, "ribs": _build_ribs, "slats": _build_slats, "weave": _build_weave,
            "gridshell": _build_gridshell, "edge": _build_edge, "supports": _build_supports,
            "panels": _build_panels, "spider": _build_spider}


# ---------------------------------------------------------------- how much

FAMILY_ORDER = ("casca", "nervura", "ripa", "fita", "bordo", "barra", "no", "pilar", "painel", "painel metalico",
                "painel fibrocimento", "caixilho", "vidro", "aranha", "rotula")


def quantities(parts):
    """{kind: {count, length_m, area_m2, volume_m3, warp_high, radius_min}} in FAMILY_ORDER."""
    out = {}
    for p in parts:
        b = out.setdefault(p["kind"], {"count": 0, "length_m": 0.0, "area_m2": 0.0, "volume_m3": 0.0,
                                       "warp_high": 0, "radius_min": None})
        n = int(p.get("count", 1))
        b["count"] += n
        length = float(p.get("length", 0.0)) * n
        b["length_m"] += length
        b["area_m2"] += float(p.get("area", 0.0)) * n
        kind = p["kind"]
        if kind in ("nervura", "ripa", "bordo", "fita"):
            b["volume_m3"] += length * float(p.get("width", 0.0)) * float(p.get("depth", 0.0))
        elif kind == "barra":
            b["volume_m3"] += length * float(p.get("size", 0.0)) ** 2
        elif kind == "pilar":
            h = float(p.get("height", 0.0)) * n
            b["length_m"] += h
            b["volume_m3"] += h * float(p.get("size", 0.0)) ** 2
        elif "area" in p and "thickness" in p:
            b["volume_m3"] += float(p["area"]) * float(p["thickness"]) * n
        b["warp_high"] += int(bool(p.get("warp_high"))) * n
        if p.get("radius") is not None:
            b["radius_min"] = p["radius"] if b["radius_min"] is None else min(b["radius_min"], p["radius"])
    order = {k: n for n, k in enumerate(FAMILY_ORDER)}
    return {k: {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in out[k].items()}
            for k in sorted(out, key=lambda k: order.get(k, len(order)))}


def write_csv(path, parts, title=""):
    """The cut list (one row a part, then the summary by family), «;» between columns (opens in Excel)."""
    import csv
    head = ["Etiqueta", "Peça", "Tipo", "Qtd", "Comprimento (m)", "Largura (m)", "Prof/Altura (m)", "Espessura (m)",
            "Área (m2)", "Raio curv. (m)", "Aviso"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        if title:
            w.writerow([title])
        w.writerow(head)
        for p in parts:
            w.writerow([p.get("id", ""), p.get("name", ""), p.get("kind", ""), p.get("count", 1),
                        _num(p.get("length", p.get("height"))), _num(p.get("width", p.get("size"))),
                        _num(p.get("depth", p.get("height"))), _num(p.get("thickness")), _num(p.get("area")),
                        _num(p.get("radius")), "torce além do admissível" if p.get("warp_high") else ""])
        w.writerow([])
        w.writerow(["RESUMO POR FAMÍLIA"])
        w.writerow(["Família", "Qtd", "Metros (m)", "Área (m2)", "Volume (m3)", "Raio mín. (m)", "Fora da planaridade"])
        for kind, b in quantities(parts).items():
            w.writerow([kind, b["count"], _num(b["length_m"]), _num(b["area_m2"]), _num(b["volume_m3"]),
                        _num(b["radius_min"]), b["warp_high"] or ""])
        w.writerow([])
        w.writerow(["Quantidades estimadas pelo ArqSynth; confirmar em projeto de execução."])


def _num(v):
    if v is None or v == "":
        return ""
    return "{:.3f}".format(float(v)).replace(".", ",")
