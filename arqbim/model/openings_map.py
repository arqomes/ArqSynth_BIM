"""(0.293) The mapa de vãos: every door and window type the project's doors and windows are of, drawn in elevation as
the generator makes them — seen from outside: the frame, the leaves, the glass, a sill or threshold, a shutter or a
grille, the signs of how each leaf opens — with its width and height dimensioned and, under it, its name, its size, a
window's sill, how it opens, how many there are and their marks. In rows, the doors first; an ordinary drawing
(model.drawings.Drawing, metres), at 1:50 on a sheet."""

import dataclasses

import numpy as np

from ..core import joinery as core
from ..i18n import decimal_sep, t
from .rebar_drawings import _dim, _poly, _room_for_texts, _text

SCALE = 50                      # its usual scale on a sheet (sheets.USUAL_SCALES): its texts' room counted so
PER_ROW = 6                     # types side by side
GAP = 0.6                       # m between two types (room for the height's dimension)
ROW_GAP = 0.5                   # m under a row's texts
TEXT = 2.5                      # mm: its texts
LINE = 0.18                     # m between two lines of text (at 1:50)
OUTLINE_PEN, SIGN_PEN = 0.25, 0.18
# (not the handles, nor a mesh's veil; (0.295) a portada's frame and its lâminas)
DRAWN = ("frame", "leaf", "panel", "glass", "stone", "shutter", "grille", "portada", "louvre", "louvre_in",
         "frosted", "wood", "vent")                                                                     # (0.306)
SHORT = {"fixed": "fixed", "left": "side", "right": "side", "tilt_left": "tilt", "tilt_right": "tilt", "top": "top",
         "bottom": "bottom", "pivot_h": "pivot", "pivot_v": "pivot", "slide_left": "slide", "slide_right": "slide",
         "slide_up": "sash", "swing_left": "swing", "swing_right": "swing", "fold_left": "fold", "fold_right": "fold"}


def _len(value):
    """A size in metres, its number alone ("1,20"): the texts say the unit once."""
    return "{:.2f}".format(value).replace(".", decimal_sep())


def _texts(item):
    """The lines under a type: its name, its size, a window's sill, how it opens, how many and their marks."""
    out = [item["name"], t("omap.size", w=_len(item["width"]), h=_len(item["height"]))]
    if item["kind"] == "window" and item["sill"] is not None:
        out.append(t("omap.sill", s=_len(item["sill"])))
    ways = list(dict.fromkeys(SHORT[c.operation] for r in item["design"].rows for c in r.cells))
    out.append(t("omap.opening", ways=" + ".join(t("omap.op." + w) for w in ways)))
    if item["design"].louvres:                                       # (0.295)
        out.append(t("omap.louvres"))
    marks = item["marks"]
    shown = ", ".join(marks[:8]) + ("…" if len(marks) > 8 else "")
    out.append(t("omap.count", n=item["count"]) + (" ({})".format(shown) if marks else ""))
    return out


def openings_map(doc, title):
    """The project's mapa de vãos, or None when it has no doors or windows (or while its IFC is read)."""
    try:
        found = doc.ifc.opening_types_used()
    except RuntimeError:
        return None
    if not found:
        return None
    from .drawings import Drawing
    drawing = Drawing(title)
    ann = []
    char = 0.55 * TEXT * SCALE / 1000.0            # m: about a letter of its texts
    top = 0.0
    for start in range(0, len(found), PER_ROW):
        row = found[start:start + PER_ROW]
        base = top - max(item["height"] for item in row)
        x = 0.0
        texts = 0
        for item in row:
            design, w, h = item["design"], item["width"], item["height"]
            if design.louvres:                  # (0.295) its portadas drawn open, beside it: it is seen behind them
                design = dataclasses.replace(design, louvres_open=True)
            depth = design.depth if design.depth > 0 else 0.2
            drawn = [poly for role, poly, _ya, _yb in core.pieces(design, w, h, 0.0, depth, (0.0, depth))
                     if role in DRAWN]                                  # (0.294: an arch's pieces too)
            left = min([0.0] + [px for poly in drawn for px, _pz in poly])
            right = max([w] + [px for poly in drawn for px, _pz in poly])
            x -= left
            for poly in drawn:
                ring = [(x + px, base + pz) for px, pz in poly]
                ann.append(_poly(ring + ring[:1], OUTLINE_PEN))
            for line in core.elevation_signs(design, w, h):
                ann.append(_poly([(x + px, base + pz) for px, pz in line], SIGN_PEN))
            _dim(drawing, (x, base), (x + w, base), -0.25)              # its width under it, its height on its left
            _dim(drawing, (x + left, base + h), (x + left, base), -0.25)
            lines = _texts(item)
            for k, words in enumerate(lines):
                ann.append(_text((x + left, base - 0.65 - k * LINE), words))
            texts = max(texts, len(lines))
            x += left + max(right - left, max(len(words) for words in lines) * char) + GAP
        top = base - 0.65 - texts * LINE - ROW_GAP
    drawing.lines = np.zeros((0, 2, 2))
    drawing.annotations = ann
    _room_for_texts(drawing, SCALE)
    return drawing
