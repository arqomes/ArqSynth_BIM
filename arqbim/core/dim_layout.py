"""(0.398) One drawer for every dimension, as its dimension type says — on screen, on paper (PDF), in SVG and in DXF
(the owner, 2026-11-05: «um motor de edição da aparência da cota»). Until then each of the four drew them its own way,
with sizes of its own.

Pure NumPy. A dimension string — one dimension, or a chain of them on one line — is laid out in the view's 2D frame, in
metres of the model, at the view's scale (`mm`: metres of the model per millimetre of paper): its lines, each with its
pen (mm on paper) and colour; its filled marks; the boxes behind its texts; its texts, each centred where it goes,
turned and sized. An output only draws what it is given.

A dimension type is a dict of STYLE_DEFAULTS' keys, as Revit's Type Properties of a dimension:
- graphics: the mark at the ends (MARKS), its size and pen; the line's pen and colour, how far it goes on past the
  extension lines; the extension lines — from a gap off the element, or of a fixed length —, their gap, overrun, pen;
- text: its height (mm on paper: the letters' em), font, width factor, bold, italic, underlined; its distance from the
  line; over the line or in a gap of it; read along the line or always level; on an opaque box; its colour; a value that
  does not fit between its extension lines moved out of the way (beyond the string's end, or up with a short leader);
- units: m, cm or mm, the decimals, rounded to so many mm, the unit's symbol, the millimetres raised (2,47⁵), a prefix
  and a suffix;
- an opening's height under its width (a door's, a window's); the text of the equal ones («IG»)."""

import math
from dataclasses import dataclass, field

import numpy as np

MARKS = ("tick", "tick_heavy", "arrow", "arrow_open", "arrow_closed", "dot", "dot_open", "none")
ARROWS = ("arrow", "arrow_open", "arrow_closed")
UNITS = ("m", "cm", "mm")
ROUNDINGS = (0.0, 0.5, 1.0, 5.0, 10.0, 50.0)          # mm: a value rounded to so many millimetres (0: as it is)
FONTS = ("", "Arial", "Arial Narrow", "Calibri", "Century Gothic", "Courier New", "Times New Roman", "Verdana")
DEFAULT_FONT = "Segoe UI"                              # ("" in a type: the program's, as the sheets' texts)
HEAVY_PEN = 0.5                                        # mm: a heavy tick's pen when its type does not say one
SUP_SCALE, SUP_RAISE = 0.62, 0.32                      # the raised millimetres: of the text's height, raised by
BELOW_SCALE = 0.85                                     # an opening's height under the line: of the text's height
PAD = 0.5                                              # mm on paper round a text (its box, the gap it needs)

STYLE_DEFAULTS = {
    # (0.124's four)
    "text": 2.2, "mark": "tick", "unit": "m", "decimals": 2,
    # graphics
    "mark_size": 2.2, "mark_pen": 0.0, "pen": 0.0, "colour": "#000000", "line_over": 0.0,
    "witness": "gap", "witness_gap": 1.5, "witness_over": 1.5, "witness_length": 5.0, "witness_pen": 0.0,
    # text
    "font": "", "width_factor": 1.0, "bold": False, "italic": False, "underline": False, "text_offset": 0.6,
    "text_place": "above", "reading": "aligned", "background": "transparent", "text_colour": "", "fit": "auto",
    # units and values
    "rounding": 0.0, "unit_symbol": False, "sup_mm": False, "prefix": "", "suffix": "",
    "opening_height": False, "eq_text": "IG",
}
CHOICES = {"mark": MARKS, "unit": UNITS, "witness": ("gap", "fixed"), "text_place": ("above", "centre"),
           "reading": ("aligned", "horizontal"), "background": ("transparent", "opaque"), "fit": ("auto", "keep")}
RANGES = {"text": (1.0, 10.0), "mark_size": (0.5, 10.0), "mark_pen": (0.0, 2.0), "pen": (0.0, 2.0),
          "line_over": (0.0, 10.0), "witness_gap": (0.0, 10.0), "witness_over": (0.0, 10.0),
          "witness_length": (0.5, 50.0), "witness_pen": (0.0, 2.0), "width_factor": (0.3, 3.0),
          "text_offset": (0.0, 10.0)}
INTS = {"decimals": (0, 4)}
BOOLS = ("bold", "italic", "underline", "unit_symbol", "sup_mm", "opening_height")
STRINGS = ("font", "prefix", "suffix", "eq_text")
COLOURS = ("colour", "text_colour")
SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

# (0.398) starting points for a new type, as offices draw them
PRESETS = {
    "architecture": {"mark": "tick", "mark_size": 2.2, "line_over": 1.5, "witness_gap": 1.5, "witness_over": 1.5},
    "heavy": {"mark": "tick_heavy", "mark_size": 2.5, "mark_pen": 0.5, "line_over": 0.0, "witness_gap": 1.5,
              "witness_over": 2.0},
    "engineering": {"mark": "arrow", "mark_size": 2.5, "line_over": 0.0, "witness_gap": 1.0, "witness_over": 2.0},
    "raised": {"mark": "tick", "unit": "m", "decimals": 2, "sup_mm": True, "line_over": 1.5},
    "centimetres": {"mark": "dot", "mark_size": 2.0, "unit": "cm", "decimals": 0, "line_over": 0.0},
}


def clean(style):
    """A dimension type read from a file or a window: its known keys with sensible values, the rest the defaults."""
    out = dict(STYLE_DEFAULTS)
    for key, value in (style or {}).items():
        if key in CHOICES:
            if value in CHOICES[key]:
                out[key] = value
        elif key in RANGES:
            try:
                low, high = RANGES[key]
                out[key] = min(max(float(value), low), high)
            except (TypeError, ValueError):
                pass
        elif key in INTS:
            try:
                low, high = INTS[key]
                out[key] = min(max(int(value), low), high)
            except (TypeError, ValueError):
                pass
        elif key in BOOLS:
            out[key] = bool(value)
        elif key in STRINGS:
            out[key] = str(value or "")[:40]
        elif key in COLOURS:
            text = str(value or "").strip()
            if text == "" and key == "text_colour" or _is_colour(text):
                out[key] = text.lower()
        elif key == "rounding":
            try:
                out[key] = min(ROUNDINGS, key=lambda r: abs(r - float(value)))
            except (TypeError, ValueError):
                pass
    return out


def _is_colour(text):
    return len(text) == 7 and text[0] == "#" and all(c in "0123456789abcdefABCDEF" for c in text[1:])


# ------------------------------------------------------------ the values

@dataclass
class Label:
    """What a dimension writes: its runs along the line — (text, scale of the height, raised by × the height) —, the
    words under the line (an opening's height) and over the value; `plain`, all of it as one string."""
    runs: list
    below: str = ""
    above: str = ""
    plain: str = ""
    shift: tuple = None            # (0.402) moved by hand from where it goes: (dx, dy) in the view's 2D frame, m


def number(length, style, decimal=","):
    """(digits, raised digit or "") of a length (m) as the type writes it: its unit, decimals, rounding — and, with
    the millimetres raised, the next digit apart when it is not 0 (2,475 m → "2,47" and "5")."""
    style = style if "sup_mm" in style else clean(style)
    unit = style.get("unit", "m")
    k = {"m": 1.0, "cm": 100.0, "mm": 1000.0}.get(unit, 1.0)
    value_mm = abs(float(length)) * 1000.0
    step_mm = float(style.get("rounding") or 0.0)
    if step_mm > 0:
        value_mm = round(value_mm / step_mm) * step_mm
    decimals = max(0, min(int(style.get("decimals", 2)), 4))
    value = value_mm / 1000.0 * k
    last = 10.0 ** (-decimals)                         # the last decimal written
    if style.get("sup_mm") and unit != "mm":
        tenths = int(math.floor(value / last * 10.0 + 0.5 + 1e-6))
        main, sup = divmod(tenths, 10)
        return "{:.{}f}".format(main * last, decimals).replace(".", decimal), (str(sup) if sup else "")
    steps = math.floor(value / last + 0.5 + 1e-6)      # (half up, as by hand: 82,5 → 83 — not to the even one)
    return "{:.{}f}".format(steps * last, decimals).replace(".", decimal), ""


def label(length, style, decimal=",", below="", above="", override=None, eq=False, prefix="", suffix="", shift=None):
    """A dimension's Label: its value as its type writes it (prefix, digits, raised millimetres, unit, suffix — the
    type's and its own), or `override` (a text written over it), or the type's «IG» (`eq`)."""
    style = style if "sup_mm" in style else clean(style)
    if override:
        runs = [(str(override), 1.0, 0.0)]
    elif eq:
        runs = [(style.get("eq_text") or "IG", 1.0, 0.0)]
    else:
        main, sup = number(length, style, decimal)
        runs = [(style.get("prefix", "") + (prefix or "") + main, 1.0, 0.0)]
        if sup:
            runs.append((sup, SUP_SCALE, SUP_RAISE))
        tail = (" " + style.get("unit", "m") if style.get("unit_symbol") else "") + (suffix or "") + \
            style.get("suffix", "")
        if tail:
            runs.append((tail, 1.0, 0.0))
    plain = "".join(text if scale >= 1.0 else text.translate(SUPERSCRIPT) for text, scale, _r in runs)
    return Label(runs, below or "", above or "", plain, tuple(shift) if shift is not None else None)


_WIDTHS = {",": 0.278, ".": 0.278, ":": 0.278, ";": 0.278, " ": 0.278, "-": 0.333, "'": 0.191, "(": 0.333,
           ")": 0.333, "/": 0.278, "°": 0.4, "²": 0.333, "×": 0.584, "+": 0.584, "=": 0.584, "≈": 0.584, "Ø": 0.778,
           "I": 0.278, "i": 0.222, "l": 0.222, "j": 0.222, "f": 0.278, "t": 0.278, "r": 0.333, "m": 0.833,
           "w": 0.722, "M": 0.833, "W": 0.944, "%": 0.889}


def text_width(text, height, style=None):
    """About how wide a text is (m, for a height in m) in the type's letters: their widths in Arial, the width
    factor, a little more in bold — enough to know whether it fits and where its box goes."""
    style = style or STYLE_DEFAULTS
    em = sum(_WIDTHS.get(c, 0.556 if c.isdigit() or c.islower() else 0.667) for c in str(text))
    return em * float(height) * float(style.get("width_factor", 1.0)) * (1.06 if style.get("bold") else 1.0)


# ------------------------------------------------------------ what is drawn

@dataclass
class Text:
    at: np.ndarray                 # its middle (the view's 2D frame, m)
    angle: float                   # degrees, counter-clockwise (y up): along the line, or 0 (level)
    height: float                  # m in the model: the letters' em
    text: str
    colour: str = "#000000"
    font: str = ""
    width: float = 1.0             # the width factor
    bold: bool = False
    italic: bool = False
    size: tuple = (0.0, 0.0)       # its box: (along it, across it), m
    owner: int = -1                # the piece it belongs to (its index in the string, or in the drawing's dims)


@dataclass
class Layout:
    lines: list = field(default_factory=list)      # (a (2,), b (2,), pen mm, colour, owner)
    fills: list = field(default_factory=list)      # (points (N, 2), colour, owner)
    backs: list = field(default_factory=list)      # (corners (4, 2), owner): boxes in the paper's colour
    texts: list = field(default_factory=list)      # Text

    def extend(self, other):
        self.lines += other.lines
        self.fills += other.fills
        self.backs += other.backs
        self.texts += other.texts
        return self


@dataclass
class Piece:
    """One dimension of a string: the point measured at each end, where its line runs, what it writes."""
    p1: np.ndarray
    p2: np.ndarray
    l1: np.ndarray
    l2: np.ndarray
    label: Label
    owner: int = -1


def _unit(v):
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else None


def reading(d):
    """The direction a text along `d` is read in: from below or from the right (its angle in (-90°, 90°])."""
    d = np.asarray(d, dtype=float)
    a = math.atan2(d[1], d[0])
    if a <= -math.pi / 2 + 1e-9 or a > math.pi / 2 + 1e-9:
        return -d
    return d


def end_mark(end, out, d, up, style, size, pen, colour, owner=-1):
    """A mark at an end of a dimension line: (lines, fills) — `out` the way out of the dimension there (an arrow's
    tip points along it), `d`/`up` the string's reading direction and its left (a tick's slant: the same at every end),
    `size` the mark's in m, `pen` mm."""
    mark = style.get("mark", "tick")
    end = np.asarray(end, dtype=float)
    lines, fills = [], []
    if mark in ("tick", "tick_heavy"):
        t = (d + up) / math.sqrt(2.0) * size / 2
        heavy = style.get("mark_pen") or (HEAVY_PEN if mark == "tick_heavy" else pen)
        lines.append((end - t, end + t, heavy, colour, owner))
    elif mark in ARROWS:
        side = np.array((-out[1], out[0]))
        base = end - out * size
        wing = size * (0.3 if mark == "arrow" else 0.33)
        tri = [end, base + side * wing, base - side * wing]
        mpen = style.get("mark_pen") or pen
        if mark == "arrow":
            fills.append((np.array(tri), colour, owner))
        elif mark == "arrow_open":
            lines += [(tri[1], end, mpen, colour, owner), (end, tri[2], mpen, colour, owner)]
        else:
            lines += [(tri[0], tri[1], mpen, colour, owner), (tri[1], tri[2], mpen, colour, owner),
                      (tri[2], tri[0], mpen, colour, owner)]
    elif mark in ("dot", "dot_open"):
        r = size * (0.2 if mark == "dot" else 0.25)
        ring = np.array([end + r * np.array((math.cos(a), math.sin(a))) for a in np.linspace(0, 2 * math.pi, 17)])
        if mark == "dot":
            fills.append((ring[:-1], colour, owner))
        else:
            mpen = style.get("mark_pen") or pen
            lines += [(p, q, mpen, colour, owner) for p, q in zip(ring, ring[1:])]
    return lines, fills


def string(pieces, style, mm, pen=0.18):
    """The Layout of a dimension string — `pieces` (Piece) on one line, side by side —, as its type (a clean
    dict) draws it at `mm` metres of the model per mm of paper; `pen` the project's for dimensions (mm), when the type
    does not say one."""
    style = style if "sup_mm" in style else clean(style)
    out = Layout()
    pieces = [p for p in pieces if np.linalg.norm(np.asarray(p.l2, float) - np.asarray(p.l1, float)) > 1e-9]
    if not pieces:
        return out
    d = reading(_unit(np.asarray(pieces[0].l2, float) - np.asarray(pieces[0].l1, float)))
    up = np.array((-d[1], d[0]))
    pieces = sorted(pieces, key=lambda p: float(((np.asarray(p.l1, float) + np.asarray(p.l2, float)) / 2) @ d))
    colour = style["colour"]
    ink = style["text_colour"] or colour
    line_pen = style["pen"] or pen
    witness_pen = style["witness_pen"] or line_pen
    mark = style["mark"]
    size = style["mark_size"] * mm
    height = style["text"] * mm
    pad = PAD * mm
    offset = style["text_offset"] * mm
    # the extension lines: one at each point of the line (two pieces side by side share theirs)
    seen = []
    for pc in pieces:
        for p, l in ((pc.p1, pc.l1), (pc.p2, pc.l2)):
            p, l = np.asarray(p, float), np.asarray(l, float)
            if any(np.linalg.norm(l - q) < 1e-6 for q in seen):
                continue
            seen.append(l)
            e = _unit(l - p)
            reach = float(np.linalg.norm(l - p))
            if e is None:
                continue
            if style["witness"] == "fixed":
                start = l - e * min(style["witness_length"] * mm, reach)
            else:
                if reach <= style["witness_gap"] * mm:
                    continue
                start = p + e * style["witness_gap"] * mm
            out.lines.append((start, l + e * style["witness_over"] * mm, witness_pen, colour, pc.owner))
    # the texts first: a centred one leaves a gap in its line
    gaps = {}
    raised = {}
    last = len(pieces) - 1
    for k, pc in enumerate(pieces):
        gap = _texts(out, pc, k, last, pieces, style, d, up, height, offset, size, pad, ink, line_pen, raised)
        if gap is not None:
            gaps[k] = gap
    # the line, piece by piece (but its texts' gaps), on past the string's ends; the marks
    marks_at = []
    for k, pc in enumerate(pieces):
        l1, l2 = np.asarray(pc.l1, float), np.asarray(pc.l2, float)
        lo, hi = (l1, l2) if float(l1 @ d) <= float(l2 @ d) else (l2, l1)
        length = float((hi - lo) @ d)
        for a, b in _without(lo, hi, d, gaps.get(k)):
            out.lines.append((a, b, line_pen, colour, pc.owner))
        if mark in ARROWS:
            inside = length >= size * 2.4
            for end, way in ((lo, -d), (hi, d)):
                tip_way = way if inside else -way
                lines, fills = end_mark(end, tip_way, d, up, style, size, line_pen, colour, pc.owner)
                out.lines += lines
                out.fills += fills
                if not inside:                     # (outside, pointing in: the line goes on past it)
                    out.lines.append((end, end + way * size * 1.8, line_pen, colour, pc.owner))
        else:
            for end in (lo, hi):
                if any(np.linalg.norm(end - q) < 1e-6 for q in marks_at):
                    continue
                marks_at.append(end)
                lines, fills = end_mark(end, d, d, up, style, size, line_pen, colour, pc.owner)
                out.lines += lines
                out.fills += fills
    over = style["line_over"] * mm
    if over > 0:
        first, final = pieces[0], pieces[-1]
        lo = min((np.asarray(first.l1, float), np.asarray(first.l2, float)), key=lambda q: float(q @ d))
        hi = max((np.asarray(final.l1, float), np.asarray(final.l2, float)), key=lambda q: float(q @ d))
        out.lines.append((lo - d * over, lo, line_pen, colour, first.owner))
        out.lines.append((hi, hi + d * over, line_pen, colour, final.owner))
    return out


def _without(lo, hi, d, gap):
    """The line lo→hi (along d) but the stretch `gap` (from, to along d) left out."""
    if gap is None:
        return [(lo, hi)]
    s0, s1 = float(lo @ d), float(hi @ d)
    g0, g1 = max(gap[0], s0), min(gap[1], s1)
    if g1 <= g0:
        return [(lo, hi)]
    parts = []
    if g0 - s0 > 1e-9:
        parts.append((lo, lo + d * (g0 - s0)))
    if s1 - g1 > 1e-9:
        parts.append((lo + d * (g1 - s0), hi))
    return parts


def _texts(out, pc, k, last, pieces, style, d, up, height, offset, size, pad, ink, line_pen, raised):
    """A piece's value (its runs), and the words under and over it, put where they go; the gap they leave in the line
    (from, to along d) when written in it, else None."""
    l1, l2 = np.asarray(pc.l1, float), np.asarray(pc.l2, float)
    lo, hi = (l1, l2) if float(l1 @ d) <= float(l2 @ d) else (l2, l1)
    mid = (lo + hi) / 2
    length = float((hi - lo) @ d)
    tdir = np.array((1.0, 0.0)) if style["reading"] == "horizontal" else d
    tup = np.array((-tdir[1], tdir[0]))
    runs = pc.label.runs
    widths = [text_width(text, height * scale, style) for text, scale, _r in runs]
    w = sum(widths)
    if w <= 0:
        return None
    along = abs(w * float(tdir @ d)) + abs(height * float(tup @ d))
    across = abs(w * float(tdir @ up)) + abs(height * float(tup @ up))
    room = length - (size * 2.0 if style["mark"] in ARROWS else size * 0.6)
    where = "line"
    if style["fit"] == "auto" and along + 2 * pad > room:
        if len(pieces) == 1 or k == last:
            where = "after"
        elif k == 0:
            where = "before"
        else:
            where = "raised"
    shift = pc.label.shift
    if shift is not None and float(np.hypot(*shift)) > 1e-9:
        where = "moved"                                  # (0.402: dragged by hand — no longer moved out of the way)
    centred = style["text_place"] == "centre" and where == "line"
    if where == "moved":                                # (0.405: where it was dropped — its middle from the line's)
        c = mid + np.asarray(shift, dtype=float)
        rel = c - mid
        if abs(float(rel @ up)) > across * 1.5 + offset * 2 or abs(float(rel @ d)) > length / 2:   # (far: a leader)
            near = c - up * (across / 2 + pad * 0.3) if float(rel @ up) > 0 else c + up * (across / 2)
            out.lines.append((mid, near, line_pen * 0.8, ink, pc.owner))
    elif where == "line":
        c = mid if centred else mid + up * (offset + across / 2)
    elif where in ("before", "after"):
        end, way = (lo, -d) if where == "before" else (hi, d)
        c = end + way * (size * 0.8 + pad + along / 2) + up * (offset + across / 2)
    else:
        level = 2 if raised.get(k - 1) == 1 else 1
        raised[k] = level
        c = mid + up * (offset + across / 2 + level * (across + offset))
        out.lines.append((mid + up * offset * 0.4, c - up * (across / 2 + pad * 0.3), line_pen * 0.8, ink, pc.owner))
    angle = math.degrees(math.atan2(tdir[1], tdir[0]))
    x = -w / 2
    for (text, scale, rise), wi in zip(runs, widths):
        h = height * scale
        at = c + tdir * (x + wi / 2) + tup * rise * height
        out.texts.append(Text(at, angle, h, text, ink, style["font"], style["width_factor"], style["bold"],
                              style["italic"], (wi, h), pc.owner))
        x += wi
    if style["underline"]:
        base = c - tup * height * 0.45
        out.lines.append((base - tdir * w / 2, base + tdir * w / 2, line_pen * 0.8, ink, pc.owner))
    if style["background"] == "opaque" or centred:
        hw, hh = w / 2 + pad * 0.6, height / 2 + pad * 0.3
        out.backs.append((np.array([c - tdir * hw - tup * hh, c + tdir * hw - tup * hh, c + tdir * hw + tup * hh,
                                    c - tdir * hw + tup * hh]), pc.owner))
    below = pc.label.below
    if below:
        hb = height * BELOW_SCALE
        wb = text_width(below, hb, style)
        across_b = abs(wb * float(tdir @ up)) + abs(hb * float(tup @ up))
        base = c if where != "line" else mid
        cb = (c - up * (across / 2 + offset + across_b / 2)) if (centred or where != "line") else \
            base - up * (offset + across_b / 2)
        out.texts.append(Text(cb, angle, hb, below, ink, style["font"], style["width_factor"], style["bold"],
                              style["italic"], (wb, hb), pc.owner))
    above = pc.label.above
    if above:
        wa = text_width(above, height, style)
        out.texts.append(Text(c + up * (across / 2 + offset + height / 2), angle, height, above, ink, style["font"],
                              style["width_factor"], style["bold"], style["italic"], (wa, height), pc.owner))
    if centred:
        s = float(mid @ d)
        return (s - along / 2 - pad, s + along / 2 + pad)
    return None


def of_drawing(dims, project, mm, pen=0.18):
    """The Layout of a drawing's dimensions — `dims` as model/drawings keeps them: (p1, p2, l1, l2, text[, its type[,
    {"chain": its string, "label": Label}]]) — each string laid out as one, in its first piece's type; each line, mark
    and text owned by its piece's index in `dims`."""
    project = clean(project)
    strings, order = {}, []
    for k, item in enumerate(dims):
        p1, p2, l1, l2, text = item[:5]
        own = item[5] if len(item) > 5 and item[5] else project
        extra = item[6] if len(item) > 6 and item[6] else {}
        words = extra.get("label") or Label([(str(text), 1.0, 0.0)], plain=str(text))
        key = extra.get("chain") or "#{}".format(k)
        if key not in strings:
            strings[key] = (own, [])
            order.append(key)
        strings[key][1].append(Piece(np.asarray(p1, float), np.asarray(p2, float), np.asarray(l1, float),
                                     np.asarray(l2, float), words, k))
    out = Layout()
    for key in order:
        own, pieces = strings[key]
        out.extend(string(pieces, own, mm, pen))
    return out


def angle_layout(v2, r, start, sweep, text, a2, b2, style, mm, pen=0.18, owner=-1):
    """An angular dimension's Layout: its arc round the corner v2 (radius r, from `start`, `sweep` radians
    counter-clockwise), its type's mark at each end, its sides carried out to it (a gap from the element, a little
    beyond), the angle `text` over its middle, level."""
    style = style if "sup_mm" in style else clean(style)
    out = Layout()
    colour = style["colour"]
    ink = style["text_colour"] or colour
    line_pen = style["pen"] or pen
    size = style["mark_size"] * mm
    v2 = np.asarray(v2, float)
    n = max(int(math.degrees(sweep) / 3.0), 2)
    arc = [v2 + r * np.array((math.cos(start + sweep * k / n), math.sin(start + sweep * k / n))) for k in range(n + 1)]
    out.lines += [(p, q, line_pen, colour, owner) for p, q in zip(arc, arc[1:])]
    for turn, end, way in ((start, arc[0], -1.0), (start + sweep, arc[-1], 1.0)):
        radial = np.array((math.cos(turn), math.sin(turn)))
        tangent = np.array((-radial[1], radial[0])) * way
        lines, fills = end_mark(end, tangent, tangent, radial, style, size, line_pen, colour, owner)
        out.lines += lines
        out.fills += fills
        reach = 0.0
        for p in (a2, b2):
            q = np.asarray(p, float) - v2
            length = float(np.linalg.norm(q))
            if length > 1e-9 and float(q @ radial) / length > 0.999:
                reach = length
        if r > reach + style["witness_gap"] * mm:
            out.lines.append((v2 + radial * (reach + style["witness_gap"] * mm),
                              v2 + radial * (r + style["witness_over"] * mm), style["witness_pen"] or line_pen,
                              colour, owner))
    height = style["text"] * mm
    mid = start + sweep / 2
    c = v2 + (r + style["text_offset"] * mm + height * 0.7) * np.array((math.cos(mid), math.sin(mid)))
    out.texts.append(Text(c, 0.0, height, text, ink, style["font"], style["width_factor"], style["bold"],
                          style["italic"], (text_width(text, height, style), height), owner))
    return out
