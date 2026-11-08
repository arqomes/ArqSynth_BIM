"""The symbols of the views (Phase 5, step 2), worked out from the model and the views — never kept, so they
are always right: in a plan, each section's line across the building with a head at each end (its tag in a
circle, an arrow the way it looks) and the four elevation marks round it (a letter, an arrow towards the
building); in a section or an elevation, a level mark at each storey (its line across the drawing, the level
and the storey's name at its end); on a plan's paper, the north arrow (the project's north: up, +Y).

Pure geometry on the document's objects and views (no Qt, no GPU)."""

import math
from dataclasses import dataclass

import numpy as np

# (sizes on paper, as drawn by hand — on screen times the view's scale; they do not make a drawing bigger, so
# the scale a sheet chooses for it stays the same)
SECTION_OVER = 4.0          # mm: a section's line runs this far past the building on each side
ELEVATION_OUT = 16.0        # mm: the elevation marks stand this far out from the building (past the sections' heads)
LEVEL_OVER = 8.0            # mm: a level's line runs this far past the drawing on each side
HEAD = 4.0                  # mm: the radius of a section's / an elevation's head
NORTH = 6.0                 # mm: the north arrow's radius
SLOPE_ARROW = 8.0           # mm: a sloped pipe's arrow, beside it (0.136)
SLOPE_GAP = 1.2             # mm: between the pipe and its arrow
SLOPE_TEXT = 2.0            # mm: its slope ("1 %") written over the arrow


def slope_mark(mid, down, radius, mm):
    """(0.136) The mark beside a pipe that falls, in plan: (the arrow's line a → b (b downhill), its head (3
    points), the middle of its text, the text's angle in degrees — read from below or from the right). mm: metres
    in the model per mm on paper."""
    d = np.asarray(down, dtype=float) / max(float(np.linalg.norm(down)), 1e-12)
    angle = float(np.degrees(np.arctan2(d[1], d[0])))
    if angle > 90.0 + 1e-6 or angle <= -90.0 + 1e-6:
        angle += -180.0 if angle > 0 else 180.0
    up = np.array((-np.sin(np.radians(angle)), np.cos(np.radians(angle))))   # (the text's up: the arrow's side)
    centre = np.asarray(mid, dtype=float)[:2] + up * (float(radius) + SLOPE_GAP * mm)
    a, b = centre - d * SLOPE_ARROW / 2 * mm, centre + d * SLOPE_ARROW / 2 * mm
    head = arrow(b, d, SLOPE_ARROW * 0.25 * mm)
    return a, b, head, centre + up * SLOPE_TEXT * 0.9 * mm, angle


@dataclass
class Mark:
    kind: str               # "section" | "elevation"
    tag: str                # what its head says ("1", "A", "N"…)
    a: np.ndarray           # plan (2,): a section's ends; an elevation's: where its head is (a == b)
    b: np.ndarray
    look: np.ndarray        # plan (2,): the way it looks (its arrows)
    ref: str = ""           # the view it stands for: the section's name, the elevation's side
    own: bool = False       # (0.358) a section's line with its own ends: not put out past them on paper


def extent(doc):
    """(lo, hi) in plan of the building (its IFC elements as shown), or None."""
    boxes = [o.mesh.bounds() for o in doc.objects.values() if o.is_bim and len(o.mesh.verts)]
    boxes = [b for b in boxes if b is not None]
    if not boxes:
        return None
    lo = np.min([b[0] for b in boxes], axis=0)
    hi = np.max([b[1] for b in boxes], axis=0)
    return lo[:2].astype(float), hi[:2].astype(float)


def plan_box(doc, storey):
    """(lo, hi) in plan of the building and the dimension lines of its plan (0.123): the elevation marks stand
    out beyond the façades' dimensions, not on them. None if there is no building."""
    from . import dimensions as dims_model
    box = extent(doc)
    if box is None:
        return None
    lo, hi = box
    o, u, v = np.zeros(3), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
    pts = []
    for dim in doc.dimensions_of(("plan", storey)):
        if dim.vertex is not None:
            continue
        a, b = dims_model.ends(doc, dim)
        _p1, _p2, l1, l2, _length = dims_model.placed(a, b, dims_model.line_point(doc, dim), o, u, v, dim.direction)
        pts += [l1, l2]
    if pts:
        lo, hi = np.minimum(lo, np.min(pts, axis=0)), np.maximum(hi, np.max(pts, axis=0))
    return lo, hi


def short_tag(name):
    """A head's text: a section named "Corte 1" says "1"; another name, its first letters."""
    words = (name or "").split()
    if not words:
        return "?"
    return words[-1] if len(words[-1]) <= 3 else words[0][:3]


def section_marks(doc, box=None, mm=0.0):
    """[Mark] of the named sections, for a plan: each one's line through its point, across the building and
    SECTION_OVER past it — mm: metres in the model per mm on paper (0: to the building's edge, as kept in a
    drawing; the painting adds it)."""
    box = extent(doc) if box is None else box
    if box is None:
        return []
    lo, hi = box
    corners = [np.array((x, y)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1])]
    out = []
    for s in getattr(doc, "sections", ()):
        n = np.asarray(s.normal, dtype=float)[:2]
        if np.linalg.norm(n) < 1e-9:
            continue
        n = n / np.linalg.norm(n)
        d = np.array((n[1], -n[0]))                       # along the cut: to the right when looking along n
        p = np.asarray(s.point, dtype=float)[:2]
        if getattr(s, "ends", None):                      # (0.358) its own ends (its grips dragged), on its line
            lo, hi = sorted(float((np.asarray(e, dtype=float) - p) @ d) for e in s.ends)
            out.append(Mark("section", short_tag(s.name), p + d * lo, p + d * hi, n, s.name, own=True))
            continue
        along = [float((c - p) @ d) for c in corners]
        a = p + d * (min(along) - SECTION_OVER * mm)
        b = p + d * (max(along) + SECTION_OVER * mm)
        out.append(Mark("section", short_tag(s.name), a, b, n, s.name))
    return out


ELEVATION_LOOKS = {"N": (0.0, -1.0), "S": (0.0, 1.0), "E": (-1.0, 0.0), "W": (1.0, 0.0)}   # as drawings'


def elevation_marks(doc, letters=None, box=None, mm=0.0):
    """[Mark] of the four elevations, for a plan: each ELEVATION_OUT out from the middle of the building's side
    it is seen from (mm: as section_marks'), its arrow towards it. letters: {side: the letter shown} (O for W in
    Portuguese)."""
    box = extent(doc) if box is None else box
    if box is None:
        return []
    lo, hi = box
    centre = (lo + hi) / 2
    half = (hi - lo) / 2
    out = []
    for side, look in ELEVATION_LOOKS.items():
        look = np.array(look)
        at = centre - look * (np.abs(look) @ half + ELEVATION_OUT * mm)
        out.append(Mark("elevation", (letters or {}).get(side, side), at, at.copy(), look, side))
    return out


def level_marks(doc):
    """[(level z, storey name)] of the storeys, lowest first — the level marks of a section / an elevation."""
    try:
        storeys = doc.ifc.storeys()
    except Exception:                                     # (the IFC still being read)
        return []
    return sorted(((float(z), name) for _g, name, z in storeys), key=lambda item: item[0])


def level_text(z, decimal=","):
    """'+3,00', '-0,50', '±0,00' — as a level is written on a drawing."""
    if abs(z) < 0.005:
        return "±0" + decimal + "00"
    return "{:+.2f}".format(z).replace(".", decimal)


def arrow(tip, look, size):
    """A head's arrow: a triangle (3 points, plan) whose tip is `tip`, pointing along `look`, `size` long."""
    look = np.asarray(look, dtype=float) / max(np.linalg.norm(look), 1e-12)
    side = np.array((-look[1], look[0]))
    base = np.asarray(tip, dtype=float) - look * size
    return [np.asarray(tip, dtype=float), base + side * size * 0.6, base - side * size * 0.6]


# ------------------------------------------------------------ (0.360) the symbols' styles (graphic_styles «symbols»)

DASHES = {"dashdot": (10.0, 2.5, 1.5, 2.5), "dashed": (6.0, 3.0), "continuous": None, "ends": None,   # mm on paper
          "dotted": (0.3, 1.5)}                  # (0.465: dots — round-capped on paper)
ENDS = 8.0                  # mm: a section's line drawn only at its ends ("ends"): this long at each


def head_shape(style, look=None, scale=1.0):
    """A head (a section's, an elevation's, a detail's) as its style draws it, round its centre (0, 0): (lines [(a, b)],
    filled triangles [(p, q, r)], open triangles [(p, q, r)], its radius) — in mm on paper times `scale` (the model's
    metres per mm, for a view); look: its arrow's way (none: no arrow)."""
    r = float(style.get("size", HEAD)) * scale
    lines = []
    if style.get("head", "circle") == "circle":
        pts = [np.array((math.cos(j * math.pi / 16), math.sin(j * math.pi / 16))) * r for j in range(33)]
        lines += list(zip(pts, pts[1:]))
    elif style.get("head") == "square":
        pts = [np.array(p) * r for p in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1))]
        lines += list(zip(pts, pts[1:]))
    filled, hollow = [], []
    kind = style.get("arrow", "filled")
    if look is not None and kind != "none" and np.linalg.norm(look) > 1e-12:
        look = np.asarray(look, dtype=float)[:2] / float(np.linalg.norm(np.asarray(look, dtype=float)[:2]))
        tri = arrow(look * r * 1.9, look, r * 0.9)
        (filled if kind == "filled" else hollow).append(tri)
    return lines, filled, hollow, r


def line_pieces(a, b, style, scale=1.0):
    """A section's / a level's / a detail's line from a to b as its style draws it: [(a, b)] — whole (continuous or
    dashed: the dashes are the drawing's), or only ENDS mm at each end ("ends") —, and its dashes (mm, or None)."""
    kind = style.get("line", "dashdot")
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if kind == "ends":
        length = float(np.linalg.norm(b - a))
        d = (b - a) / max(length, 1e-12)
        e = min(ENDS * scale, length / 2)
        return [(a, a + d * e), (b - d * e, b)], None
    return [(a, b)], DASHES.get(kind)


# ------------------------------------------------------------ (0.462) a level, as its style draws it

LEVEL_GAP = 1.0             # mm on paper: between the line and its words, and the words and the mark


@dataclass
class LevelParts:
    """A level drawn (in a section's / an elevation's plane: x along it, z up — metres): its line's pieces and dashes,
    its marks' outlines (pairs), their filled parts (polygons), their circles (centre, radius — a CAD circle) and its
    words [(point, text, align, height in mm)] — align "bottom-right", "top-right", "bottom-left" or "top-left": the
    text's corner at the point."""
    pieces: list
    dashes: tuple
    outline: list
    filled: list
    circles: list
    texts: list


def _arc(c, r, a0, a1, n=8):
    return [c + r * np.array((math.cos(a), math.sin(a))) for a in np.linspace(a0, a1, n + 1)]


def level_parts(z, x0, x1, name, style, mm, decimal=",", model=None):
    """(0.462, the owner: «A REPRESENTAÇÃO, OU APARÊNCIA ESSES ELEMENTOS DEVER SER CONFIGURADOS NESSA ABA. A LINHA E A
    EXTREMIDADE») A level at height z across a drawing from x0 to x1 — its line LEVEL_OVER past it on each side —, as
    its style says: the line (dash-dot, dashed, continuous, at its ends only), at the end(s) it says (right, left,
    both) its mark — a triangle on the line, Revit's quartered circle, a square, none — and its words beside the mark,
    towards the drawing: the level and the name in one line, «NAME | level», the name over the line and the level
    under it (Revit's), or the level over and the name under. mm: metres per mm on paper. A LevelParts. (0.464) model:
    the drawing's own span (x0, x1) — with the style's «over» off, the line stops short of it (only its sides drawn)."""
    a = np.array((float(x0) - LEVEL_OVER * mm, float(z)))
    b = np.array((float(x1) + LEVEL_OVER * mm, float(z)))
    pieces, dashes = line_pieces(a, b, style, mm)
    if model is not None and not style.get("over", True):         # (0.464) not over the drawing: its sides only
        m0, m1 = float(model[0]) - LEVEL_GAP * mm, float(model[1]) + LEVEL_GAP * mm
        kept = []
        for p, q in pieces:
            lo, hi = sorted((float(p[0]), float(q[0])))
            for s0, s1 in ((lo, min(hi, m0)), (max(lo, m1), hi)):
                if s1 - s0 > 1e-9:
                    kept.append((np.array((s0, float(z))), np.array((s1, float(z)))))
        pieces = kept
    out = LevelParts(pieces, dashes, [], [], [], [])
    s = float(style.get("size", 1.8)) * mm
    gap = LEVEL_GAP * mm
    mark = style.get("mark", "triangle")
    height = float(style.get("text", 2.2))
    level = level_text(z, decimal)
    label = style.get("label", "level_name")
    for d in {"left": (-1.0,), "both": (-1.0, 1.0)}.get(style.get("ends"), (1.0,)):
        e = b if d > 0 else a
        inner = e[0] - d * gap                                    # (the words: from the line's end inwards)
        if mark == "triangle":                                    # (its tip on the line, its base over it)
            out.filled.append([e.copy(), e + np.array((-s, 1.4 * s)), e + np.array((s, 1.4 * s))])
            inner = e[0] - d * (s + gap)
        elif mark == "target":                                    # (Revit's: a circle quartered, two quarters full)
            c = e + np.array((d * s, 0.0))
            ring = _arc(c, s, 0.0, 2 * math.pi, 32)
            out.outline += list(zip(ring, ring[1:]))
            out.outline += [(c - (s, 0.0), c + (s, 0.0)), (c - (0.0, s), c + (0.0, s))]
            out.circles.append((c, s))
            out.filled.append([c] + _arc(c, s, 0.0, math.pi / 2))
            out.filled.append([c] + _arc(c, s, math.pi, 1.5 * math.pi))
        elif mark == "square":                                    # (a square on the line's end)
            q = 0.8 * s
            out.filled.append([e + (0.0, -q), e + (d * 2 * q, -q), e + (d * 2 * q, q), e + (0.0, q)])
        side = "right" if d > 0 else "left"
        over, under = np.array((inner, z + gap)), np.array((inner, z - gap))
        if label == "name_over":
            out.texts += [(over, name, "bottom-" + side, height), (under, level, "top-" + side, height)]
        elif label == "level_over":
            out.texts += [(over, level, "bottom-" + side, height), (under, name, "top-" + side, height)]
        elif label == "name_level":
            out.texts.append((over, "{} | {}".format(name, level), "bottom-" + side, height))
        else:
            out.texts.append((over, "{}  {}".format(level, name), "bottom-" + side, height))
    return out
