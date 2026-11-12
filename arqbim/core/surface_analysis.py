"""(0.559, PLANO.md «Gerador de formas orgânicas», step 8) A parametric surface looked at for building it: its
curvature at each point (flat, curved one way, a dome, a saddle), how flat each panel of its grid is (flat glass, glass
bent cold, bent hot), and the surface unrolled in strips along its grid (each strip flattened as it is, for cutting a
membrane, a sheet or timber) — written as DXF."""

import math

import numpy as np

CLASSES = ("plana", "simples", "cupula", "sela")        # flat, single curvature, synclastic, anticlastic
CLASS_TEXT = {"plana": "plana", "simples": "curva num sentido (cilíndrica)", "cupula": "dupla curvatura (cúpula)",
              "sela": "dupla curvatura (sela)"}
CLASS_RGBA = {"plana": (0.62, 0.66, 0.70, 0.85), "simples": (0.30, 0.65, 0.35, 0.85),
              "cupula": (0.90, 0.50, 0.15, 0.85), "sela": (0.25, 0.45, 0.90, 0.85)}
FLAT_K = 0.02                  # 1/m: a curvature under this (a radius over 50 m) counts as none
WARP = (("vidro plano", 0.002, (0.30, 0.70, 0.35, 0.85)),       # warp over its diagonal: up to this…
        ("vidro curvado a frio", 0.01, (0.95, 0.75, 0.20, 0.85)),
        ("curvar a quente / painel curvo", math.inf, (0.85, 0.25, 0.20, 0.85)))


def _closed(rows, close_u):
    p = np.asarray(rows, dtype=float)
    return np.concatenate((p, p[:, :1]), axis=1) if close_u else p


def curvatures(rows, close_u=False):
    """(k1, k2) the principal curvatures (1/m) at each point of the grid — the grid's own derivatives (the
    fundamental forms by finite differences)."""
    p = _closed(rows, close_u)
    pu = np.gradient(p, axis=1)
    pv = np.gradient(p, axis=0)
    puu = np.gradient(pu, axis=1)
    pvv = np.gradient(pv, axis=0)
    puv = np.gradient(pu, axis=0)
    n = np.cross(pu, pv)
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-12)
    E, F, G = (pu * pu).sum(-1), (pu * pv).sum(-1), (pv * pv).sum(-1)
    L, M, N = (puu * n).sum(-1), (puv * n).sum(-1), (pvv * n).sum(-1)
    den = np.maximum(E * G - F * F, 1e-18)
    K = (L * N - M * M) / den
    H = (E * N - 2 * F * M + G * L) / (2 * den)
    root = np.sqrt(np.maximum(H * H - K, 0.0))
    k1, k2 = H + root, H - root
    if close_u:
        k1, k2 = k1[:, :-1], k2[:, :-1]
    return k1, k2


def classify(k1, k2, flat=FLAT_K):
    """Each point's kind: «plana», «simples», «cupula» (both curvatures one way), «sela» (opposite ways)."""
    a1, a2 = np.abs(k1) >= flat, np.abs(k2) >= flat
    out = np.full(np.shape(k1), "plana", dtype=object)
    out[a1 ^ a2] = "simples"
    both = a1 & a2
    out[both & (k1 * k2 > 0)] = "cupula"
    out[both & (k1 * k2 < 0)] = "sela"
    return out


def cell_corners(rows, close_u=False):
    p = _closed(rows, close_u)
    return p[:-1, :-1], p[:-1, 1:], p[1:, 1:], p[1:, :-1]


def warp(rows, close_u=False):
    """Each cell's warp: how far its fourth corner is off the plane of the other three, over its diagonal."""
    a, b, c, d = cell_corners(rows, close_u)
    n = np.cross(b - a, d - a)
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-12)
    off = np.abs(((c - a) * n).sum(-1))
    diag = np.maximum(np.linalg.norm(c - a, axis=-1), 1e-12)
    return off / diag


def report(rows, close_u=False):
    """{"curvature": {class: share of the points}, "panels": {kind: count}, "k_max": 1/m}."""
    k1, k2 = curvatures(rows, close_u)
    kinds = classify(k1, k2)
    total = kinds.size
    w = warp(rows, close_u)
    panels = {}
    lo = 0.0
    for name, hi, _rgba in WARP:
        panels[name] = int(((w > lo - 1e-15) & (w <= hi)).sum()) if lo == 0 else int(((w > lo) & (w <= hi)).sum())
        lo = hi
    return {"curvature": {c: float((kinds == c).sum()) / total for c in CLASSES}, "panels": panels,
            "k_max": float(max(np.abs(k1).max(), np.abs(k2).max()))}


def coloured_cells(rows, close_u=False, what="curvature"):
    """(triangles (n, 3, 3), colours (n, 4)) of the grid's cells coloured by `what` («curvature»: the class of the
    cell's corners, the most curved; «planarity»: its warp)."""
    a, b, c, d = cell_corners(rows, close_u)
    if what == "curvature":
        k1, k2 = curvatures(rows, close_u)
        kinds = classify(k1, k2)
        if close_u:
            kinds = np.concatenate((kinds, kinds[:, :1]), axis=1)
        rank = {"plana": 0, "simples": 1, "sela": 2, "cupula": 3}
        r = np.vectorize(rank.get)(kinds)
        cell = np.maximum.reduce([r[:-1, :-1], r[:-1, 1:], r[1:, 1:], r[1:, :-1]])
        names = {v: k for k, v in rank.items()}
        rgba = np.array([CLASS_RGBA[names[int(v)]] for v in cell.ravel()])
    else:
        w = warp(rows, close_u).ravel()
        rgba = np.empty((len(w), 4))
        lo = -1.0
        for _name, hi, colour in WARP:
            rgba[(w > lo) & (w <= hi)] = colour
            lo = hi
    t1 = np.stack((a, b, c), axis=-2).reshape(-1, 3, 3)
    t2 = np.stack((a, c, d), axis=-2).reshape(-1, 3, 3)
    tris = np.empty((2 * len(t1), 3, 3))
    tris[0::2], tris[1::2] = t1, t2
    cols = np.repeat(rgba, 2, axis=0)
    return tris, cols


# ---------------------------------------------------------------- unrolled in strips
def _place(a2, b2, A, B, C, away):
    """The flat place of C, given its triangle's A and B already flat (a2, b2), on the side of a2b2 away from the
    flat point `away` (None: to the left)."""
    ab = B - A
    d = float(np.linalg.norm(ab))
    along = float((C - A) @ ab) / max(d, 1e-12)
    height = float(np.linalg.norm(np.cross(ab, C - A))) / max(d, 1e-12)
    e = (b2 - a2) / max(float(np.linalg.norm(b2 - a2)), 1e-12)
    perp = np.array((-e[1], e[0]))
    side = 1.0
    if away is not None:
        u, w = b2 - a2, away - a2
        if float(u[0] * w[1] - u[1] * w[0]) > 0:
            side = -1.0
    return a2 + e * along + perp * height * side


def unroll_strip(bottom, top):
    """(bottom (n, 2), top (n, 2)) of the strip between two rows of points, flattened triangle by triangle (each
    keeps its sides' lengths): the strip of a membrane, a sheet or a batten to cut."""
    B, T = np.asarray(bottom, float), np.asarray(top, float)
    n = len(B)
    b2, t2 = np.zeros((n, 2)), np.zeros((n, 2))
    b2[1] = (float(np.linalg.norm(B[1] - B[0])), 0.0)
    t2[0] = _place(b2[0], b2[1], B[0], B[1], T[0], None)
    for i in range(n - 1):
        if i > 0:
            b2[i + 1] = _place(b2[i], t2[i], B[i], T[i], B[i + 1], b2[i - 1] if i else None)
        t2[i + 1] = _place(b2[i + 1], t2[i], B[i + 1], T[i], T[i + 1], b2[i])
    return b2, t2


def strips(rows, close_u=False, along="u"):
    """[(bottom, top)] every strip of the grid flattened — between rows (`along` «u») or between columns («v»)."""
    p = _closed(rows, close_u)
    if along == "v":
        p = np.transpose(p, (1, 0, 2))
    return [unroll_strip(p[j], p[j + 1]) for j in range(p.shape[0] - 1)]


def strip_area(bottom, top):
    ring = np.vstack((bottom, top[::-1]))
    x, y = ring[:, 0], ring[:, 1]
    return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def unrolled_dxf(rows, close_u=False, along="u", name="Superfície", gap=0.2):
    """The DXF text (mm) of the strips laid side by side, each its outline (layer FAIXAS), its folds between triangles
    (DOBRAS) and its number and size (TEXTOS)."""
    from ..model import dxf
    w = dxf._Writer()
    y0 = 0.0
    out = strips(rows, close_u, along)
    for k, (b, t) in enumerate(out):                     # (one above the other, each its own size)
        lo = np.vstack((b, t)).min(axis=0)
        b, t = b - lo + (0.0, y0), t - lo + (0.0, y0)
        ring = np.vstack((b, t[::-1])) * 1000.0
        w.polyline("FAIXAS", [tuple(q) for q in ring], closed=True)
        for i in range(1, len(b) - 1):
            w.polyline("DOBRAS", [tuple(b[i] * 1000.0), tuple(t[i] * 1000.0)], closed=False)
        size = np.vstack((b, t)).max(axis=0) - np.vstack((b, t)).min(axis=0)
        w.text("TEXTOS", (-900.0, float(y0 * 1000.0)), 80.0, "F{} · {:.2f} m²".format(k + 1, strip_area(b, t)))
        y0 += float(size[1]) + gap
    w.text("TEXTOS", (0.0, -350.0), 100.0, "{} — {} faixas".format(name, len(out)))
    return w.document({"FAIXAS": 7, "DOBRAS": 8, "TEXTOS": 3}), len(out)
