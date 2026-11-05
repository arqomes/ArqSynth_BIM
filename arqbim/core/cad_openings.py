"""Openings and furniture from a CAD plan's blocks (0.160, Phase 8, step 1): each block inserted, its lines where
they are (moved, turned, scaled). A door or a window is the part of its block that lies in a wall's thickness —
from there to there along the wall: its width and place; a door's leaf and swing go to one side (the side it opens
to). Which is which: the block's or the layer's name (PORTA / DOOR…, JANELA / WINDOW…), else a block with an arc (a
swing) is a door, one without, a window. The rest of the blocks on the furniture's layers are furniture: their
outline (the hull of their lines) where they are, turned as inserted.

Pure numpy: plan points in metres (the link's placement applied)."""

import math
import re
from dataclasses import dataclass

import numpy as np

from . import cad

DOOR_WORDS = re.compile(r"(?i)port|door|pt\d|^p\d")
WINDOW_WORDS = re.compile(r"(?i)jan|win|caixilh|vidr|jn\d|^j\d")
FURNITURE_WORDS = re.compile(r"(?i)mob|furn|equip|sanit|loi[cç]|cozinh|kitchen|mesa|cadeir|cama|sof")
BAND = 0.05                     # m beyond a wall's faces: a block's point this near is in the wall
MIN_WIDTH = 0.30                # m: an opening narrower than this is not one
GAP_REACH = 0.05                # m: an opening covers a gap in a wall to this much from its ends


@dataclass
class BlockInstance:
    layer: str
    block: str
    points: np.ndarray          # (N, 2) every point of its lines, in the plan (m)
    lines: list                 # [(N, 2) polylines] in the plan
    at: tuple                   # where it is inserted (plan)
    rotation: float             # degrees (the insert's, the link's turn added)
    arc: bool                   # it has an arc (a door's swing)
    height: float = None        # (0.212) its height, as written beside it on the drawing (m), or None
    sill: float = None          # (0.212) a window's sill, as written beside it, or None


def instances(drawing, place, layers=None, turn=0.0):
    """The blocks inserted in the drawing (on these layers, when given), their lines placed by `place` (a link's:
    (K, 2, 2) drawing-unit segments -> plan segments), their turn the insert's and `turn` (the link's)."""
    out = []
    for e in drawing.entities:
        if e.kind != "insert" or e.block not in drawing.blocks or (layers is not None and e.layer not in layers):
            continue
        lines = []
        for _layer, pts in cad.entity_polylines(e, drawing.blocks):
            if len(pts) < 2:
                continue
            p = np.asarray(pts, dtype=float)
            segs = place(np.stack((p[:-1], p[1:]), axis=1) * 1.0)
            lines.append(np.vstack((segs[:, 0], segs[-1:, 1])))
        if not lines:
            continue
        _base, inner = drawing.blocks[e.block]
        arc = any(sub.kind == "arc" or (sub.kind == "polyline" and any(abs(b) > 1e-6 for b in sub.bulges))
                  for sub in inner)
        at = place(np.array([[e.points[0], e.points[0]]], dtype=float))[0, 0]
        out.append(BlockInstance(e.layer, e.block, np.vstack(lines), lines, (float(at[0]), float(at[1])),
                                 float(e.rotation) + float(turn), arc))
    return out


SIZE = re.compile(r"(\d+(?:[.,]\d+)?)\s*[x×X*]\s*(\d+(?:[.,]\d+)?)")
SILL = re.compile(r"(?i)\b(?:peitoril|parapeito|ptr|pt\.?|p\.e\.?|sill)(?:\s+|\s*[=:]\s*)(\d+(?:[.,]\d+)?)")
HEIGHT = re.compile(r"(?i)\b(?:h|alt(?:ura)?)\s*[=:]\s*(\d+(?:[.,]\d+)?)")
AFTER = re.compile(r"[/+]\s*(\d+(?:[.,]\d+)?)")
TEXT_REACH = 1.5                # m: a size written this near an opening's middle is its (0.212)


def _metres(value, scale=None):
    """A length written on a drawing: in metres when small, in centimetres when tens or hundreds, in millimetres when
    thousands (or as `scale` says)."""
    v = float(value.replace(",", "."))
    if scale is not None:
        return v * scale
    return v / 1000.0 if v >= 1000 else (v / 100.0 if v >= 10 else v)


def parse_size(text):
    """(0.212) An opening's size as written beside it — "0,90×2,10", "90x210", "1.20 x 1.10 / 1.00", "J1 1,20x1,10
    pt 1,00", "1200x1100 peitoril 1000": (width, height, sill) in metres, each None when not written."""
    width = height = sill = None
    found = SIZE.search(text or "")
    scale = None
    if found:
        a, b = found.group(1), found.group(2)
        big = max(float(a.replace(",", ".")), float(b.replace(",", ".")))
        scale = 0.001 if big >= 1000 else (0.01 if big >= 10 else 1.0)       # (one unit for both)
        width, height = _metres(a, scale), _metres(b, scale)
        rest = text[found.end():]
        after = AFTER.search(rest)
        if after:
            sill = _metres(after.group(1), scale)
    else:
        rest = text or ""
    words = SILL.search(rest)
    if words:
        sill = _metres(words.group(1), scale)
    tall = HEIGHT.search(text or "") if height is None else None
    if tall:
        height = _metres(tall.group(1), scale)
    return width, height, sill


def texts(drawing, place):
    """(0.212) The drawing's texts where they are in the plan: [(point (2,), words)]."""
    out = []
    for e in drawing.entities:
        if e.kind == "text" and e.text:
            at = place(np.array([[e.points[0], e.points[0]]], dtype=float))[0, 0]
            out.append((np.array((float(at[0]), float(at[1]))), e.text))
    return out


def read_sizes(found, words, reach=TEXT_REACH):
    """(0.212) Each opening's height (and a window's sill) from the size written nearest its middle, within reach —
    a text taken once, the nearest pairs first. Sets them on the instances; returns how many got one."""
    pairs = []
    for i, inst in enumerate(found):
        middle = np.asarray(inst.points, dtype=float).mean(axis=0)
        for k, (at, text) in enumerate(words):
            _w, height, sill = parse_size(text)
            if height is None and sill is None:
                continue
            gap = float(np.linalg.norm(at - middle))
            if gap <= reach:
                pairs.append((gap, i, k, height, sill))
    pairs.sort(key=lambda p: p[0])
    taken_i, taken_k = set(), set()
    for _gap, i, k, height, sill in pairs:
        if i in taken_i or k in taken_k:
            continue
        taken_i.add(i)
        taken_k.add(k)
        found[i].height, found[i].sill = height, sill
    return len(taken_i)


def kind_of(inst):
    """"door" | "window" | "furniture" | None of a block, by its name, then its layer's, then its shape."""
    for text in (inst.block, inst.layer):
        if DOOR_WORDS.search(text):
            return "door"
        if WINDOW_WORDS.search(text):
            return "window"
        if FURNITURE_WORDS.search(text):
            return "furniture"
    return None


def span_on(inst, a, b, thickness):
    """Where the block lies in the wall a → b (plan, its axis) of this thickness: (from, to along it from a, the side
    its leaf goes to: +1 left of a → b, -1 right, 0 none) — or None."""
    a, b = np.asarray(a, dtype=float)[:2], np.asarray(b, dtype=float)[:2]
    length = float(np.linalg.norm(b - a))
    if length < 1e-9:
        return None
    d = (b - a) / length
    n = np.array((-d[1], d[0]))
    rel = inst.points - a
    along, across = rel @ d, rel @ n
    band = np.abs(across) <= thickness / 2 + BAND
    if np.count_nonzero(band) < 2:
        return None
    s0, s1 = float(along[band].min()), float(along[band].max())
    if s1 - s0 < MIN_WIDTH or s0 < -BAND or s1 > length + BAND:
        return None
    out = ~band
    side = 0
    if np.any(out):
        m = float(across[out].mean())
        side = 1 if m > 0 else -1
    return max(s0, 0.0), min(s1, length), side


def covers_gap(inst, a, b, thickness, g0, g1):
    """Does the block fill the stretch [g0, g1] along the line a → b (a door drawn in a wall's gap)?"""
    a, b = np.asarray(a, dtype=float)[:2], np.asarray(b, dtype=float)[:2]
    d = (b - a) / max(float(np.linalg.norm(b - a)), 1e-12)
    n = np.array((-d[1], d[0]))
    rel = inst.points - a
    along, across = rel @ d, rel @ n
    band = np.abs(across) <= thickness / 2 + BAND
    if np.count_nonzero(band) < 2:
        return False
    return float(along[band].min()) <= g0 + GAP_REACH and float(along[band].max()) >= g1 - GAP_REACH


def footprint(inst):
    """A furniture block's outline in the plan: the convex hull of its lines — (N, 2), or None."""
    from shapely.geometry import MultiPoint
    hull = MultiPoint([tuple(p) for p in inst.points]).convex_hull
    if hull.geom_type != "Polygon" or hull.area < 0.01:
        return None
    return np.array(hull.exterior.coords)[:-1]


HEIGHTS = ((re.compile(r"(?i)mesa|table|secret|desk|bancada"), 0.75), (re.compile(r"(?i)cadeir|chair|banco"), 0.85),
           (re.compile(r"(?i)cama|bed"), 0.50), (re.compile(r"(?i)sof|couch"), 0.80),
           (re.compile(r"(?i)arm[aá]r|roupeir|wardrobe|estante|shelf"), 2.00),
           (re.compile(r"(?i)sanit|wc|lav|bid[eé]|duche|banh|bath|basin"), 0.80))
DEFAULT_HEIGHT = 0.75


def furniture_height(name):
    """How high a piece of furniture is made (m), by its block's name."""
    return next((h for words, h in HEIGHTS if words.search(name or "")), DEFAULT_HEIGHT)


def furniture_items(drawing, place, units, layers, turn=0.0):
    """The furniture blocks inserted on these layers: [(block name, its outline in its own frame (N, 2) m, where it
    is inserted (plan), its turn (degrees))] — one shape per block, as many places as it is inserted."""
    from shapely.geometry import MultiPoint
    shapes, out = {}, []
    for e in drawing.entities:
        if e.kind != "insert" or e.block not in drawing.blocks or e.layer not in layers:
            continue
        key = (e.block, round(e.scale[0], 6), round(e.scale[1], 6))
        if key not in shapes:
            base, inner = drawing.blocks[e.block]
            pts = []
            for sub in inner:
                for _layer, p in cad.entity_polylines(sub, drawing.blocks):
                    pts += [((x - base[0]) * e.scale[0] * units, (y - base[1]) * e.scale[1] * units) for x, y in p]
            hull = MultiPoint(pts).convex_hull if len(pts) >= 3 else None
            shapes[key] = (np.array(hull.exterior.coords)[:-1]
                           if hull is not None and hull.geom_type == "Polygon" and hull.area >= 0.01 else None)
        if shapes[key] is None:
            continue
        at = place(np.array([[e.points[0], e.points[0]]], dtype=float))[0, 0]
        out.append((e.block, shapes[key], (float(at[0]), float(at[1])), float(e.rotation) + float(turn)))
    return out


def prism(outline, height):
    """The solid of an outline (N, 2) raised `height`: (verts, faces — polygons, outwards)."""
    ring = [tuple(map(float, p)) for p in outline]
    from shapely.geometry import Polygon
    if Polygon(ring).exterior.is_ccw is False:
        ring = ring[::-1]
    n = len(ring)
    verts = [(x, y, 0.0) for x, y in ring] + [(x, y, float(height)) for x, y in ring]
    faces = [list(range(n - 1, -1, -1)), list(range(n, 2 * n))]
    faces += [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    return np.array(verts), faces


def turned_box(inst):
    """A furniture block's box in its own frame (as inserted, turned): (centre (2,), size (w, d), angle degrees)."""
    a = math.radians(inst.rotation)
    u, v = np.array((math.cos(a), math.sin(a))), np.array((-math.sin(a), math.cos(a)))
    pu, pv = inst.points @ u, inst.points @ v
    w, dd = float(pu.max() - pu.min()), float(pv.max() - pv.min())
    centre = u * (pu.max() + pu.min()) / 2 + v * (pv.max() + pv.min()) / 2
    return centre, (w, dd), inst.rotation
