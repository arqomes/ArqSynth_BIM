"""(0.466) A component's miniature, as SketchUp's Components panel shows them: its shape seen from the front, a little
from the right and above, its faces in its pieces' colours shaded by a light, its edges (where faces fold, its
outline — not the triangles' sides) in a thin dark line; on a clear background. Drawn with QPainter, farthest
triangles first (no GPU), kept on disk (a file's: by its path and date; the project's: by its shape)."""

import hashlib
import math
import os

import numpy as np
from PySide6 import QtCore, QtGui

AZIMUTH = math.radians(-35.0)       # (seen from the front (−Y), turned a little to its right…)
ELEVATION = math.radians(28.0)      # (…and from above)
EDGE_DEG = 25.0                     # faces folding more than this: an edge drawn
MOST_EDGES = 60000                  # (a heavier shape: its faces only)
EDGE_INK = QtGui.QColor(30, 30, 30, 170)


def _axes():
    f = np.array((math.cos(ELEVATION) * math.sin(-AZIMUTH), math.cos(ELEVATION) * math.cos(-AZIMUTH),
                  -math.sin(ELEVATION)))        # (looking along f: towards +Y, down)
    right = np.cross(f, (0.0, 0.0, 1.0))
    right /= np.linalg.norm(right)
    up = np.cross(right, f)
    return right, up, f


def _feature_edges(corners, normals):
    """The edges to draw: [[(triangle, corner a, corner b)…]] — on the outline (a side of one triangle only) or where
    two faces fold more than EDGE_DEG —, each with the triangles it is a side of (drawn with one that is seen)."""
    keys = np.round(corners.reshape(-1, 3) * 1e5).astype(np.int64)
    _u, ids = np.unique(keys, axis=0, return_inverse=True)
    ids = ids.reshape(-1, 3)
    seen = {}
    for t, (a, b, c) in enumerate(ids):
        for i, j, k0, k1 in ((a, b, 0, 1), (b, c, 1, 2), (c, a, 2, 0)):
            key = (i, j) if i < j else (j, i)
            seen.setdefault(key, []).append((t, k0, k1))
    out = []
    fold = math.cos(math.radians(EDGE_DEG))
    for sides in seen.values():
        if len(sides) == 1:
            out.append(sides)
        elif len(sides) == 2:
            (t0, _k0, _k1), (t1, _a, _b) = sides
            if abs(float(normals[t0] @ normals[t1])) < fold:
                out.append(sides)
    return out


def render(corners, colours, size=128, background=None):
    """The miniature (QPixmap size × size) of triangles (T, 3, 3) metres in their colours (T, 3) sRGB 0–1."""
    pm = QtGui.QPixmap(size, size)
    pm.fill(background if background is not None else QtCore.Qt.GlobalColor.transparent)
    corners = np.asarray(corners, dtype=float).reshape(-1, 3, 3)
    if not len(corners):
        return pm
    colours = np.asarray(colours, dtype=float).reshape(-1, 3)
    right, up, f = _axes()
    x, y, depth = corners @ right, corners @ up, corners @ f        # (T, 3) each
    lo = np.array((x.min(), y.min()))
    hi = np.array((x.max(), y.max()))
    span = max(float(np.max(hi - lo)), 1e-9)
    k = size * 0.84 / span
    off = np.array((size, size)) / 2 - (lo + hi) / 2 * np.array((k, -k))
    px = x * k + off[0]
    py = -y * k + off[1]
    n = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    # the faces turned away left out — a solid's back, under what is seen (drawn farthest first, a big bottom face's
    # half came over its top) —, unless that leaves too little (faces the wrong way round, a sheet seen from behind)
    front = (n @ f) < 0
    keep = front if front.sum() >= 0.25 * len(n) else np.ones(len(n), dtype=bool)
    n = np.where((n @ f)[:, None] > 0, -n, n)                         # (both sides: the one towards the eye)
    light = -f + up * 0.7 + right * 0.4
    light /= np.linalg.norm(light)
    shade = 0.50 + 0.50 * np.clip(n @ light, 0.0, 1.0)
    rgb = np.clip(colours * shade[:, None], 0.0, 1.0)
    order = [t for t in np.argsort(-depth.mean(axis=1)) if keep[t]]   # (the farthest first)
    edges = {}
    if len(corners) <= MOST_EDGES:
        for sides in _feature_edges(corners, n):
            seen = [side for side in sides if keep[side[0]]]        # (with a triangle that is drawn: the last of them)
            if seen:
                t, a, b = max(seen, key=lambda side: -float(depth[side[0]].mean()))
                edges.setdefault(t, []).append((a, b))
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    edge_pen = QtGui.QPen(EDGE_INK, max(0.8, size / 160.0))
    for t in order:
        colour = QtGui.QColor.fromRgbF(*rgb[t])
        p.setPen(QtGui.QPen(colour, 1.0))                            # (no hair between two triangles)
        p.setBrush(colour)
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(px[t, i], py[t, i]) for i in range(3)]))
        for a, b in edges.get(t, ()):
            p.setPen(edge_pen)
            p.drawLine(QtCore.QPointF(px[t, a], py[t, a]), QtCore.QPointF(px[t, b], py[t, b]))
    p.end()
    return pm


# ---------------------------------------------------------------- kept on disk

def cache_dir():
    base = os.environ.get("ARQBIM_CACHE_DIR") or os.path.join(os.path.expanduser("~"), ".cache", "arqsynth")
    path = os.path.join(base, "miniaturas")
    os.makedirs(path, exist_ok=True)
    return path


def file_key(path):
    """A file's miniature's name: by its path, its date and its size (changed: drawn again)."""
    try:
        st = os.stat(path)
        text = "{}|{}|{}".format(os.path.abspath(path), int(st.st_mtime), st.st_size)
    except OSError:
        text = os.path.abspath(path)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def shape_key(corners):
    """The project's component's miniature's name: by its shape."""
    data = np.ascontiguousarray(np.round(np.asarray(corners, dtype=float), 5)).tobytes()
    return hashlib.sha1(data).hexdigest()


def cached(key, make, size=128):
    """The miniature kept under `key` — made by `make()` (a QPixmap, or None) and kept, the first time."""
    path = os.path.join(cache_dir(), "{}_{}.png".format(key, size))
    if os.path.exists(path):
        pm = QtGui.QPixmap(path)
        if not pm.isNull():
            return pm
    pm = make()
    if pm is not None and not pm.isNull():
        pm.save(path, "PNG")
    return pm
