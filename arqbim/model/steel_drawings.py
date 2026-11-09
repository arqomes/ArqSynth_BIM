"""(0.502) The steel structure's fabrication drawing — «Peças de aço» (DetailCraft's shop drawings, all on one sheet):
each piece mark drawn once, side on, as it is cut (its body seen across its depth: the mitres' angles, the copes'
notches), with its length and its depth dimensioned and its line of text — mark, section, grade, how many, length,
weight —; each plate mark seen flat with its holes, its sizes and its holes' positions dimensioned. An ordinary
drawing (model.drawings.Drawing, metres), at 1:50 on a sheet (sheets.USUAL_SCALES)."""

import json

import numpy as np

from ..core import steel, steel_marks
from ..i18n import decimal_sep, t
from .rebar_drawings import TEXT, _room_for_texts, _text

SCALE = 50
ROW = 0.55                      # m (at 1:50: 11 mm) between one piece and the next, its text and dimension under it
TEXT_DROP = 0.40                # m under a piece: its line of text
PLATE_ZOOM = 5                  # plates drawn 5× (at 1:10): their holes and edge distances read at 1:50 are too small


def _n(v, d=2):
    return "{:.{}f}".format(float(v), d).replace(".", decimal_sep())


def _dim(drawing, p1, p2, offset, value=None):
    """(0.504) A dimension as rebar_drawings' (its line `offset` to the left of p1 → p2), its text in whole
    millimetres — the workshop's (a cleat's 25 mm, not «0,03»)."""
    a, b = np.asarray(p1, dtype=float), np.asarray(p2, dtype=float)
    d = b - a
    length = float(np.linalg.norm(d))
    if length < 1e-6:
        return
    n = np.array((-d[1], d[0])) / length
    mm = (length if value is None else value) * 1000.0
    drawing.dims.append((a, b, a + n * offset, b + n * offset, "{:.0f}".format(mm)))     # (whole mm, as cut)


def _outline(doc, guid, axis, depth_dir):
    """A piece's body seen across its depth: its outline in (along its axis, up its depth) — the union of its
    triangles flattened (the cut ends' angles, the copes' notches as they are)."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    obj = doc.get(guid)
    faces = getattr(obj.mesh, "tris", None) if obj is not None and obj.mesh is not None else None
    if faces is None or not len(faces):
        return None
    verts = obj.mesh.verts
    u, v = verts @ axis, verts @ depth_dir
    flat = np.column_stack((u, v))
    tris = []
    for face in faces:
        pts = flat[np.asarray(face[:3])]
        poly = Polygon(pts)
        if poly.area > 1e-9:
            tris.append(poly)
    if not tris:
        return None
    shape = unary_union(tris).buffer(0)
    if shape.geom_type != "Polygon":
        shape = max(getattr(shape, "geoms", [shape]), key=lambda g: g.area)
    return shape


def parts_drawing(doc, title):
    """The steel pieces' drawing, or None when the model has none."""
    from .drawings import Drawing
    try:
        marks, pieces = doc.ifc.steel_marks()
    except Exception:
        return None
    if not pieces:
        return None
    groups = {}
    for p in pieces:
        groups.setdefault(marks.get(p["guid"], ""), []).append(p)
    drawing = Drawing(title)
    lines, ann = [], []
    order = sorted(groups, key=steel_marks.sort_key)
    y = 0.0
    for mark in order:                                  # (the sections' marks down a first column…)
        if groups[mark][0]["prefix"] != "Ch":
            y = _profile(doc, drawing, lines, ann, mark, groups[mark], y)
    x0 = 0.0                                            # (…0.504: the plates' down a second, right of it — one
    if lines:                                           # column grew past what a sheet holds at 1:50)
        x0 = float(np.concatenate(lines)[..., 0].max())
        for _kind, _shapes, _h, words, where, size, *_rest in ann:
            x0 = max(x0, float(where[0]) + len(words) * 0.55 * size * SCALE / 1000.0)
        x0 += 1.0
    y = 0.0
    for mark in order:
        if groups[mark][0]["prefix"] == "Ch":
            y = _plate(doc, drawing, lines, ann, mark, groups[mark], y, x0)
    if not lines:
        return None
    drawing.lines = np.concatenate(lines)
    drawing.annotations = ann
    _room_for_texts(drawing, SCALE)
    return drawing


def _profile(doc, drawing, lines, ann, mark, members, y):
    """A section's mark: its outline side on with its top at y, its dimensions, its line of text; returns the next y."""
    p = members[0]
    g = p["guid"]
    m = doc.ifc.placement(g)
    axis = m[:3, 2] / np.linalg.norm(m[:3, 2])
    depth_dir = m[:3, 1] / np.linalg.norm(m[:3, 1])
    shape = _outline(doc, g, axis, depth_dir)
    if shape is None:
        return y
    x0, v0, x1, v1 = shape.bounds
    shift = np.array((-x0, y - v1))
    ring = np.asarray(shape.exterior.coords) + shift
    lines.append(np.stack((ring[:-1], ring[1:]), axis=1))
    length, depth = x1 - x0, v1 - v0
    _dim(drawing, (0.0, y - depth), (length, y - depth), -0.12, value=length)
    _dim(drawing, (length, y), (length, y - depth), 0.12, value=depth)
    sec = steel.get(p["signature"][0])
    weight = sum(q["weight"] for q in members)
    holes = doc.ifc.member_holes(g)                      # (0.512) its holes: the web's seen as circles
    for face, _hx, _hy, d0, world in holes:
        if face != "v":
            continue
        cx_, cy_ = float(world @ axis) - x0, float(world @ depth_dir) + shift[1]
        r = d0 / 2000.0
        ring_h = np.array([(cx_ + r * np.cos(a), cy_ + r * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 17)])
        lines.append(np.stack((ring_h[:-1], ring_h[1:]), axis=1))
    words = t("sdraw.piece", mark=mark, section=steel.display(sec.name) if sec else p["section"], grade=p["grade"],
              n=len(members), l=_n(length), kg=_n(weight, 0))
    if holes:
        words += t("sdraw.holes", n=len(holes), d=_n(holes[0][3], 0))
    ann.append(_text((0.0, y - depth - TEXT_DROP), words))
    return y - depth - TEXT_DROP - ROW


FIT = 3.5 * 0.55 * TEXT * SCALE / 1000.0   # m drawn: what a dimension's text («0,05») needs between its ends


def _chain(drawing, stops, at, along, offset, zoom):
    """A chain of dimensions through `stops` (sorted, drawn), on the line `at`: edge to hole to hole to edge, and
    the whole further out; `along` "x" (under the plate) or "y" (on its right). (0.503) When a piece of the chain is
    too short for its text (a gusset's holes on a slant), from the first edge to each stop instead, each further out."""
    def pt(s):
        return (s, at) if along == "x" else (at, s)

    def dim(a, b, off):
        p, q = (pt(a), pt(b)) if along == "x" else (pt(b), pt(a))
        _dim(drawing, p, q, off, value=(b - a) / zoom)
    pieces = [(a, b) for a, b in zip(stops[:-1], stops[1:]) if b - a > 1e-6]
    if any(b - a < FIT for a, b in pieces):
        k = -1
        for k, s in enumerate(s for s in stops[1:] if s - stops[0] > 1e-6):
            dim(stops[0], s, offset * (1.0 + 1.4 * k))
        return abs(offset) * (1.0 + 1.4 * max(k, 0))
    for a, b in pieces:
        dim(a, b, offset)
    if len(stops) > 2:
        dim(stops[0], stops[-1], offset * 2.2)
        return abs(offset) * 2.2
    return abs(offset)


def _plate(doc, drawing, lines, ann, mark, members, y, x0=0.0):
    """A plate's mark: seen flat and enlarged (PLATE_ZOOM: at 1:10 on the 1:50 sheet, its dimensions reading its
    real sizes), its holes, chains of dimensions from its edges through its holes under it and on its right — its
    left edge at x0; returns the next y."""
    lines_before, dims_before, ann_before = len(lines), len(drawing.dims), len(ann)
    y = _plate_at_zero(doc, drawing, lines, ann, mark, members, y)
    if x0:                                              # (drawn from x = 0, then moved to its column)
        shift = np.array((x0, 0.0))
        for k in range(lines_before, len(lines)):
            lines[k] = lines[k] + shift
        for k in range(dims_before, len(drawing.dims)):
            p1, p2, l1, l2, words, *own = drawing.dims[k]
            drawing.dims[k] = (p1 + shift, p2 + shift, l1 + shift, l2 + shift, words, *own)
        for k in range(ann_before, len(ann)):
            item = list(ann[k])
            item[4] = np.asarray(item[4], dtype=float) + shift
            ann[k] = tuple(item)
    return y


def _plate_at_zero(doc, drawing, lines, ann, mark, members, y):
    e = doc.ifc.by_guid(members[0]["guid"])
    plate = json.loads(doc.ifc._params(e).get("Chapa") or "{}")
    if not plate:
        return y
    z = PLATE_ZOOM
    L, W, tp = float(plate["L"]) / 1000.0, float(plate["W"]) / 1000.0, float(plate["t"])
    Lz, Wz = L * z, W * z
    if plate.get("contorno"):                           # (0.503: a gusset's own outline, from its middle)
        corners = np.array([(Lz / 2.0 + cx / 1000.0 * z, y - Wz / 2.0 + cy / 1000.0 * z)
                            for cx, cy in plate["contorno"]])
    else:
        corners = np.array(((0.0, y - Wz), (Lz, y - Wz), (Lz, y), (0.0, y)))
    lines.append(np.stack((corners, np.roll(corners, -1, axis=0)), axis=1))
    xs = []
    for x, h, d in plate.get("furos", []):
        cx, cy = Lz / 2.0 + x / 1000.0 * z, y - Wz / 2.0 + h / 1000.0 * z
        r = d / 2000.0 * z
        ring = np.array([(cx + r * np.cos(a), cy + r * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 25)])
        lines.append(np.stack((ring[:-1], ring[1:]), axis=1))
        xs.append((cx, cy))
    along = sorted({0.0, Lz} | {round(cx, 5) for cx, _cy in xs})
    up = sorted({y - Wz, y} | {round(cy, 5) for _cx, cy in xs})
    under = _chain(drawing, along, y - Wz, "x", -0.12, z)
    _chain(drawing, up, Lz, "y", 0.12, z)
    d0 = plate["furos"][0][2] if plate.get("furos") else 0.0
    weight = sum(q["weight"] for q in members)
    drop = Wz + under + 0.01 + TEXT_DROP                 # (its line of text under its dimensions)
    shaped = bool(plate.get("contorno"))
    ann.append(_text((0.0, y - drop), t("sdraw.gusset" if shaped else "sdraw.plate", mark=mark, l=_n(L * 1000, 0),
                                        w=_n(W * 1000, 0),
                                        t=_n(tp, 0), holes=len(xs), d=_n(d0, 0), n=len(members),
                                        kg=_n(weight, 1), s=SCALE // z)))
    return y - drop - ROW
