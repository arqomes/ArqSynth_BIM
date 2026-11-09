"""(0.502) The steel structure's fabrication drawing — «Peças de aço» (DetailCraft's shop drawings, all on one sheet):
each piece mark drawn once, side on, as it is cut (its body seen across its depth: the mitres' angles, the copes'
notches), with its length and its depth dimensioned and its line of text — mark, section, grade, how many, length,
weight —; each plate mark seen flat with its holes, its sizes and its holes' positions dimensioned. An ordinary
drawing (model.drawings.Drawing, metres), at 1:50 on a sheet (sheets.USUAL_SCALES)."""

import json

import numpy as np

from ..core import steel, steel_marks
from ..i18n import decimal_sep, t
from .rebar_drawings import _dim, _room_for_texts, _text

SCALE = 50
ROW = 0.55                      # m (at 1:50: 11 mm) between one piece and the next, its text and dimension under it
TEXT_DROP = 0.40                # m under a piece: its line of text
PLATE_ZOOM = 5                  # plates drawn 5× (at 1:10): their holes and edge distances read at 1:50 are too small


def _n(v, d=2):
    return "{:.{}f}".format(float(v), d).replace(".", decimal_sep())


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
    y = 0.0
    for mark in sorted(groups, key=steel_marks.sort_key):
        members = groups[mark]
        p = members[0]
        if p["prefix"] == "Ch":
            y = _plate(doc, drawing, lines, ann, mark, members, y)
        else:
            y = _profile(doc, drawing, lines, ann, mark, members, y)
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
    ann.append(_text((0.0, y - depth - TEXT_DROP), t("sdraw.piece", mark=mark, section=steel.display(sec.name)
                                                      if sec else p["section"], grade=p["grade"], n=len(members),
                                                      l=_n(length), kg=_n(weight, 0))))
    return y - depth - TEXT_DROP - ROW


def _chain(drawing, stops, at, along, offset, zoom):
    """A chain of dimensions through `stops` (sorted, drawn), on the line `at`: edge to hole to hole to edge, and
    the whole further out; `along` "x" (under the plate) or "y" (on its right)."""
    def pt(s):
        return (s, at) if along == "x" else (at, s)
    for a, b in zip(stops[:-1], stops[1:]):
        if b - a > 1e-6:
            p, q = (pt(a), pt(b)) if along == "x" else (pt(b), pt(a))
            _dim(drawing, p, q, offset, value=(b - a) / zoom)
    if len(stops) > 2:
        p, q = (pt(stops[0]), pt(stops[-1])) if along == "x" else (pt(stops[-1]), pt(stops[0]))
        _dim(drawing, p, q, offset * 2.2, value=(stops[-1] - stops[0]) / zoom)


def _plate(doc, drawing, lines, ann, mark, members, y):
    """A plate's mark: seen flat and enlarged (PLATE_ZOOM: at 1:10 on the 1:50 sheet, its dimensions reading its
    real sizes), its holes, chains of dimensions from its edges through its holes under it and on its right;
    returns the next y."""
    e = doc.ifc.by_guid(members[0]["guid"])
    plate = json.loads(doc.ifc._params(e).get("Chapa") or "{}")
    if not plate:
        return y
    z = PLATE_ZOOM
    L, W, tp = float(plate["L"]) / 1000.0, float(plate["W"]) / 1000.0, float(plate["t"])
    Lz, Wz = L * z, W * z
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
    _chain(drawing, along, y - Wz, "x", -0.12, z)
    _chain(drawing, up, Lz, "y", 0.12, z)
    d0 = plate["furos"][0][2] if plate.get("furos") else 0.0
    weight = sum(q["weight"] for q in members)
    drop = Wz + 0.27 + TEXT_DROP
    ann.append(_text((0.0, y - drop), t("sdraw.plate", mark=mark, l=_n(L * 1000, 0), w=_n(W * 1000, 0),
                                        t=_n(tp, 0), holes=len(xs), d=_n(d0, 0), n=len(members),
                                        kg=_n(weight, 1), s=SCALE // z)))
    return y - drop - ROW
