"""Structural drawings (0.168, Phase 9, step 5). The structure plan of a storey: cut just under its slabs — its
columns and beams cut, its footings seen below, its slabs' outlines dashed above —, the grid, each member tagged
(«P1 30×30», «V2 20×40», «L1 h = 0,15», «S1 1,20×1,20»), the tags made when drawn, so they follow the model.
Reinforcement drawings: a member's bars drawn from the IFC as they are in the model —
a beam's elevation (its concrete, its bars bent into the supports, a line for each stirrup) and its section at
mid-span (the stirrup with its hooks, the bars as dots); a column's elevation and its section at mid-height; a
footing's plan (its mesh both ways) and its section; a slab's plan with its mesh. Each set labelled with its
bars, its position (the bar schedule's) and its length. An ordinary drawing (model.drawings.Drawing: its lines
and its annotations, metres), so a sheet, its PDF and its DXF take it as they take a plan."""

import re

import numpy as np

from ..i18n import decimal_sep, t
from . import design_text as dt
from .drawings import CUT_HEIGHT, Drawing

BAR_PEN = 0.50                  # mm on paper: the bars, heavier than the concrete's outline
LINK_PEN = 0.25
TEXT = 2.5                      # mm: the labels
DOT = 0.006                     # m: the least radius of a bar's dot in a section (before it is enlarged)
ZOOM = 2.5                      # a section laid out this much larger — its labels and dimensions spaced as beside a 1:50
#                                 elevation —, then (0.234) brought back to its real size: its own view, at 1:20
TEXT_SCALE = 50                 # the labels' room counted at this scale (see _room_for_texts)
CUT_SCALE = 20                  # (0.234) …and a section's, at its own (sheets.USUAL_SCALES)
CUTS = {"beam": "A", "column": "B", "footing": "C"}     # (0.234) the members drawn with a section: its letter
MARK_PEN = 0.70                 # mm: (0.236) where a section is cut, a stroke heavier than the bars…
MARK = (0.04, 0.12)             # m: …this far off the outline, at its two ends (at 1:50)


def _poly(points, width=BAR_PEN):
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    return ("polyline", [(pts, False)], "none", "", pts[0], TEXT, "continuous", width)


def _dot(centre, r):
    a = np.linspace(0.0, 2.0 * np.pi, 13)[:-1]
    ring = np.column_stack((centre[0] + r * np.cos(a), centre[1] + r * np.sin(a)))
    return ("region", [(ring, True)], "solid", "", ring[0], TEXT, "continuous", None)


def _text(where, words, size=TEXT):
    return ("text", [], "none", words, np.asarray(where, dtype=float), size, "continuous", None)


def _rect(x0, y0, x1, y1):
    return np.array((((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))))


def _crossing(bar, axis, at):
    """Where a bar's centreline (N, 3) crosses the plane `axis`·p = at: the point, or None."""
    p = np.asarray(bar, dtype=float)
    s = p @ axis
    for k in range(len(p) - 1):
        a, b = s[k], s[k + 1]
        if (a - at) * (b - at) <= 0.0 and abs(b - a) > 1e-9:
            return p[k] + (p[k + 1] - p[k]) * (at - a) / (b - a)
    return None


def _row_label(drawing, ann, where, row):
    """A set's label (its bars, position, length) — (0.238) one a hand may move, kept in drawing.movable by its
    role and position."""
    drawing.movable.append((len(ann), "{}:{}".format(row["role"], row["mark"])))
    ann.append(_text(where, _label(row)))


def apply_moves(doc, drawing, view):
    """(0.238) The labels of a view's drawing moved by hand (its own property: Document.move_label) where they were
    put — after its extent is counted (kept as its frame), so the view does not shift with them."""
    if drawing is None or not drawing.movable:
        return drawing
    if drawing.frame is None:
        box = drawing.bounds()
        if box is not None:
            drawing.frame = (float(box[0][0]), float(box[0][1]), float(box[1][0]), float(box[1][1]))
    labels = doc.view_settings(view).labels or {}
    for i, key in drawing.movable:
        if key in labels and i < len(drawing.annotations):
            a = drawing.annotations[i]
            drawing.annotations[i] = a[:4] + (np.asarray(a[4], dtype=float) + labels[key],) + a[5:]
    return drawing


def _cut_mark(ann, at, out, letter):
    """(0.236) Where a member's section is cut, at one end of its line: a heavy stroke off the outline at `at`,
    pointing `out` (a unit 2D vector), its letter beside it — on the right of an upright stroke, over a level one."""
    at, out = np.asarray(at, dtype=float), np.asarray(out, dtype=float)
    ann.append(_poly((at + out * MARK[0], at + out * MARK[1]), MARK_PEN))
    if abs(out[1]) > abs(out[0]):
        where = at + (0.03, MARK[0] if out[1] > 0 else -MARK[1] - 0.03)
    else:
        where = at + (-MARK[1] if out[0] < 0 else MARK[0], 0.02)
    ann.append(_text(where, letter))


def _dim(drawing, p1, p2, offset, value=None):
    """(0.232) A dimension from p1 to p2 (2D, the drawing's), its line `offset` away (on the left of p1 → p2: a
    positive offset), reading `value` (m; their distance — a section drawn enlarged reads its real size)."""
    from . import dimensions as dims_model
    a, b = np.asarray(p1, dtype=float), np.asarray(p2, dtype=float)
    d = b - a
    length = float(np.linalg.norm(d))
    if length < 1e-6:
        return
    n = np.array((-d[1], d[0])) / length
    value = length if value is None else value
    drawing.dims.append((a, b, a + n * offset, b + n * offset, dims_model.text(value, decimal_sep())))


def _label(row):
    if row["role"] in ("stirrups", "ties"):
        return t("rdraw.links", n=row["count"], d=row["diameter"], s=dt.spacing_text(row["spacing"]), m=row["mark"])
    if row["role"] in ("mesh_x", "mesh_y", "top_x", "top_y", "wall_v", "wall_h"):
        return t("rdraw.top_mesh" if row["role"].startswith("top_") else "rdraw.mesh", n=row["count"],
                 d=row["diameter"], s=dt.spacing_text(row["spacing"]), m=row["mark"], l=dt.num(row["length"], 2))
    return t("rdraw.bars", n=row["count"], d=row["diameter"], m=row["mark"], l=dt.num(row["length"], 2))


def sets_of(doc, host):
    """[(schedule row, [bar centrelines (N, 3)])] of a member's reinforcement."""
    rows = [r for r in doc.ifc.rebar_rows() if r["host"] == host]
    return [(r, doc.ifc.rebar_bars(r["guid"])) for r in rows]


def rebar_drawing(doc, host, title, cut=False):
    """The reinforcement drawing of a member (its GlobalId) — (0.234) or, cut=True, its section (a beam's A–A, a
    column's B–B, a footing's C–C; a slab has none) at its real size, a view of its own —, or None when it has no
    bars or is not one this program lays them in."""
    sets = sets_of(doc, host)
    if not sets:
        return None
    kind = doc.ifc.kind_of(host)
    make = {"beam": _beam, "column": _column, "footing": _footing, "slab": _slab, "wall": _wall}.get(kind)
    if make is None or (cut and kind not in CUTS):
        return None
    drawing, section = Drawing(title), Drawing(title)
    make(doc, host, sets, drawing, section)
    if cut:
        _shrink(section, 1.0 / ZOOM)
        _room_for_texts(section, CUT_SCALE)
        return section
    _room_for_texts(drawing)
    return drawing


def has_cut(doc, host):
    """(0.234) Whether a member's reinforcement has a section of its own (rebar_drawing cut=True)."""
    return doc.ifc.kind_of(host) in CUTS


def cut_letter(doc, host):
    return CUTS.get(doc.ifc.kind_of(host), "A")


def _shrink(drawing, k):
    """(0.234) A drawing laid out larger brought to its real size: its lines, annotations and dimensions times k
    (their pens and texts are on paper: they stay)."""
    drawing.lines = drawing.lines * k
    drawing.annotations = [(kind, [(np.asarray(p, dtype=float) * k, closed) for p, closed in shapes], hatch, words,
                            np.asarray(where, dtype=float) * k, *rest)
                           for kind, shapes, hatch, words, where, *rest in drawing.annotations]
    drawing.dims = [(p1 * k, p2 * k, l1 * k, l2 * k, words, *own) for p1, p2, l1, l2, words, *own in drawing.dims]


STRUCTURE = ("IfcColumn", "IfcBeam", "IfcFooting", "IfcPile")
UNDER_SLAB = 0.01               # m: a structure plan is cut this far under its storey's lowest slab soffit


def short_tag(name):
    """«Pilar 3» → «P3», «Viga 12» → «V12»; a name without a number, as it is."""
    m = re.match(r"^\s*(\D+?)\s*(\d+)\s*$", name or "")
    return "{}{}".format(m.group(1)[0].upper(), m.group(2)) if m else (name or "")


def _cm(v):
    return "{:g}".format(round(v * 100, 1)).replace(".", decimal_sep())


def _structure_of(doc, storey):
    """(its level, its columns, beams, footings and piles, [(its structural slabs, their outlines)]) — None when
    it is no storey."""
    levels = {g: z for g, _n, z in doc.storeys()}
    if storey not in levels:
        return None
    members = [o for o in doc.objects.values() if o.is_bim and o.storey == storey and o.ifc_class in STRUCTURE]
    slabs = []
    for o in doc.objects.values():
        if o.is_bim and o.storey == storey and o.ifc_class == "IfcSlab" and doc.ifc.kind_of(o.id) == "slab":
            info = doc.ifc.slab_outline(o.id)
            if info is not None and info.get("function", "estrutural") == "estrutural":
                slabs.append((o, info))
    return levels[storey], members, slabs


def structure_plan(doc, storey, title):
    """The structure plan of a storey (its GlobalId), or None when it has no columns, beams nor footings."""
    from .drawings import _draw
    found = _structure_of(doc, storey)
    if found is None or not found[1]:
        return None
    level, members, slabs = found
    soffits = [float(i["bottom"]) for _o, i in slabs if float(i["bottom"]) > level + 0.5]
    tops = [float(o.mesh.bounds()[1][2]) for o in members if o.ifc_class == "IfcBeam" and o.mesh.bounds() is not None]
    if soffits:
        cut = min(soffits) - UNDER_SLAB
    elif tops:
        cut = max(tops) - 0.05
    else:
        cut = level + CUT_HEIGHT
    origin, u, v = np.array((0.0, 0.0, level)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
    drawing = _draw(doc, members, np.array((0.0, 0.0, -1.0)), -cut, origin, u, v, title, detail="coarse")
    drawing.above = [np.asarray(i["outline"], dtype=float) for _o, i in slabs]       # (dashed: over the cut)
    drawing.grids = [(np.array(a.start, dtype=float), np.array(a.end, dtype=float), a.tag)
                     for a in getattr(doc, "grids", ())]
    drawing.north = True
    drawing.annotations = _tags(doc, drawing, members, slabs)
    return drawing


UNDER_BEAMS = 0.05              # m: (0.235) a formwork plan seen from below is cut this far under its lowest soffit


def structure_below(doc, storey, title):
    """(0.235) The formwork plan of a storey seen from below — reflected, as in a mirror on the floor, so it lies as
    its plan does —: cut just under its beams' and slabs' soffits, its columns cut, its beams and slabs seen from
    under them (a slab's edges hidden where a beam is in front), its openings; the grid, each member tagged as in
    the structure plan. None when it has neither beams nor slabs over its level."""
    from .drawings import _draw
    found = _structure_of(doc, storey)
    if found is None:
        return None
    level, members, slabs = found
    columns = [o for o in members if o.ifc_class == "IfcColumn"]
    beams = [o for o in members if o.ifc_class == "IfcBeam" and o.mesh.bounds() is not None]
    over = [(o, i) for o, i in slabs if float(i["bottom"]) > level + 0.5]
    soffits = [float(i["bottom"]) for _o, i in over] + [float(o.mesh.bounds()[0][2]) for o in beams]
    soffits = [z for z in soffits if z > level + 0.5]
    if not soffits:
        return None
    cut = min(soffits) - UNDER_BEAMS
    origin, u, v = np.array((0.0, 0.0, level)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
    seen = columns + beams + [o for o, _i in over]
    drawing = _draw(doc, seen, np.array((0.0, 0.0, 1.0)), cut, origin, u, v, title, detail="coarse")
    drawing.grids = [(np.array(a.start, dtype=float), np.array(a.end, dtype=float), a.tag)
                     for a in getattr(doc, "grids", ())]
    drawing.north = True
    drawing.annotations = _tags(doc, drawing, columns + beams, over)
    return drawing


def _tags(doc, drawing, members, slabs):
    """Each member's tag (its short name and size) beside it, each slab's in it: text annotations — (0.238) each
    one a hand may move, kept in drawing.movable by its member's GlobalId."""
    from shapely.geometry import Polygon
    from ..core import steel
    ann = []
    for o in members:
        tag = short_tag(o.name)
        section = doc.ifc.steel_section(o.id) if o.ifc_class in ("IfcColumn", "IfcBeam") else None
        try:
            if o.ifc_class == "IfcColumn":
                centre, _x, (a, b), _base, _top = doc.ifc.column_box(o.id)
                drawing.movable.append((len(ann), o.id))
                ann.append(_text((centre[0] + max(a, b) + 0.05, centre[1] + max(a, b) + 0.05),
                                 "{} {}".format(tag, steel.display(section)) if section else      # (0.494: «P1 HEB 200»)
                                 "{} {}×{}".format(tag, _cm(2 * a), _cm(2 * b))))
            elif o.ifc_class == "IfcBeam":
                start, end, _t, width, height = doc.ifc.beam_params(o.id)
                d = np.asarray(end[:2], dtype=float) - np.asarray(start[:2], dtype=float)
                n = np.array((-d[1], d[0])) / max(float(np.linalg.norm(d)), 1e-9)
                if (abs(d[0]) >= abs(d[1]) and n[1] < 0) or (abs(d[0]) < abs(d[1]) and n[0] < 0):
                    n = -n                    # (over a beam along X, right of one along Y: the text runs off it)
                mid = (np.asarray(start[:2], dtype=float) + np.asarray(end[:2], dtype=float)) / 2
                drawing.movable.append((len(ann), o.id))
                ann.append(_text(mid + n * (width / 2 + 0.08), "{} {}".format(tag, steel.display(section)) if section
                                 else "{} {}×{}".format(tag, _cm(width), _cm(height))))
            elif o.ifc_class == "IfcFooting":
                centre, _x, length, width, _top = doc.ifc.footing_params(o.id)
                drawing.movable.append((len(ann), o.id))
                ann.append(_text((centre[0] - length / 2, centre[1] - width / 2 - 0.25),
                                 "{} {}×{}".format(tag, dt.num(length, 2), dt.num(width, 2))))
        except (KeyError, TypeError, ValueError, AttributeError, IndexError):
            continue                                                 # (one this program did not make so)
    for o, info in slabs:
        c = Polygon(info["outline"]).representative_point()
        drawing.movable.append((len(ann), o.id))
        ann.append(_text((c.x, c.y), t("rdraw.slab_tag", tag=short_tag(o.name), h=dt.num(info["thickness"], 2))))
    return ann


def _room_for_texts(drawing, scale=TEXT_SCALE):
    """Its extent (Drawing.frame) with room for its labels, whose size is on paper — counted at 1:`scale`, the
    scale these drawings take: a sheet then lays the next view clear of them."""
    pts = [drawing.lines.reshape(-1, 2)] if len(drawing.lines) else []
    for kind, shapes, _h, words, where, size, *_rest in drawing.annotations:
        pts += [np.asarray(p, dtype=float) for p, _closed in shapes]
        if kind == "text":
            w, h = len(words) * 0.55 * size * scale / 1000.0, 1.6 * size * scale / 1000.0
            pts.append(np.array((where, where + (w, h))))
    if pts:                       # (0.234) its dimensions too — their lines and room for a text beyond them: a
        for p1, _p2, l1, l2, _words, *_own in drawing.dims:          # sheet's label under the view stays clear
            out = np.asarray(l1, dtype=float) - np.asarray(p1, dtype=float)
            out = out / max(float(np.linalg.norm(out)), 1e-9) * 1.6 * TEXT * scale / 1000.0
            pts.append(np.array((l1, l2, l1 + out, l2 + out), dtype=float))
    if pts:
        allp = np.vstack(pts)
        lo, hi = allp.min(axis=0), allp.max(axis=0)
        drawing.frame = (float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1]))


def _beam(doc, host, sets, drawing, section):
    start, end, top, width, height = doc.ifc.beam_params(host)
    x = np.array((end[0] - start[0], end[1] - start[1], 0.0))
    length = float(np.linalg.norm(x))
    x /= max(length, 1e-12)
    y = np.array((-x[1], x[0], 0.0))
    z = np.array((0.0, 0.0, 1.0))
    o = np.array((start[0], start[1], top - height))
    ann, cut = [], []                                                # (the elevation's; the section A-A's, enlarged)
    below, above = -0.18, height + 0.12
    # (0.236) where A-A is cut, at mid-span: its marks over and under the beam — the labels a row further off when
    # the longest of them would reach them
    widest = max(len(_label(r)) for r, _b in sets) * 0.55 * TEXT * TEXT_SCALE / 1000.0
    if widest > length / 2 - 0.05:
        below, above = below - 0.14, above + 0.14
    _cut_mark(ann, (length / 2, height), (0.0, 1.0), CUTS["beam"])
    _cut_mark(ann, (length / 2, 0.0), (0.0, -1.0), CUTS["beam"])
    for row, bars in sets:
        if row["role"] == "stirrups":
            for bar in bars:
                p = (np.asarray(bar) - o) @ np.column_stack((x, z))
                ann.append(_poly(((p[:, 0].mean(), p[:, 1].min()), (p[:, 0].mean(), p[:, 1].max())), LINK_PEN))
            mid = min(bars, key=lambda b: abs(float((np.asarray(b) - o).mean(axis=0) @ x) - length / 2))
            q = (np.asarray(mid) - o) @ np.column_stack((y, z))
            cut.append(_poly(np.column_stack(((q[:, 0] + width / 2) * ZOOM, q[:, 1] * ZOOM)), LINK_PEN))
            _row_label(drawing, ann, (0.0, below), row)
            below -= 0.14
            continue
        for bar in bars:
            p = (np.asarray(bar) - o) @ np.column_stack((x, z))
            ann.append(_poly(p))
            hit = _crossing(bar, x, float(x @ o) + length / 2)
            if hit is not None:
                r = max(row["diameter"] / 2000.0, DOT)
                cut.append(_dot((((hit - o) @ y + width / 2) * ZOOM, ((hit - o) @ z) * ZOOM), r * ZOOM))
        if row["role"] == "top":
            _row_label(drawing, ann, (0.0, above), row)
            above += 0.14
        else:
            _row_label(drawing, ann, (0.0, below), row)
            below -= 0.14
    # (0.232) its dimensions: each bar that stops short its reach (the top's over the beam, the bottom's under its
    # labels), its length and height, its section's sides (their real sizes)
    for role, base in (("top", height), ("bottom", 0.0)):
        spans = set()
        for row, bars in sets:
            if row["role"] == role:
                for bar in bars:
                    u = (np.asarray(bar) - o) @ x
                    a, b = max(float(u.min()), 0.0), min(float(u.max()), length)
                    if b - a < length - 0.05:
                        spans.add((round(a, 3), round(b, 3)))
        for a, b in sorted(spans):
            _dim(drawing, (a, base), (b, base), (above + 0.10 - base) if role == "top" else (below - 0.05))
    _dim(drawing, (0.0, 0.0), (length, 0.0), below - 0.30)
    _dim(drawing, (0.0, height), (0.0, 0.0), -0.25)
    drawing.lines = _rect(0.0, 0.0, length, height)
    drawing.annotations = ann
    _dim(section, (0.0, 0.0), (width * ZOOM, 0.0), -0.40, value=width)
    _dim(section, (width * ZOOM, height * ZOOM), (width * ZOOM, 0.0), 0.15, value=height)
    section.lines = _rect(0.0, 0.0, width * ZOOM, height * ZOOM)
    section.annotations = cut


def _section_outline(doc, host, a, b, ox, oy):
    """(0.227) A column's section drawn ZOOM times larger round (ox, oy): a rectangle — a circle, an L, a T as it
    is (its profile's)."""
    from ..core.space_frame import shape_rects
    shape, web = doc.ifc.column_section(host)
    if shape == "circle":
        ang = np.linspace(0.0, 2.0 * np.pi, 49)
        ring = np.column_stack((ox + a * ZOOM * np.cos(ang), oy + a * ZOOM * np.sin(ang)))
    elif shape in ("L", "T"):
        from shapely.geometry import box
        from shapely.ops import unary_union
        outline = unary_union([box(*r) for r in shape_rects(shape, 2.0 * a, 2.0 * b, web)])
        ring = np.asarray(outline.exterior.coords) * ZOOM + (ox, oy)
    else:
        return _rect(ox - a * ZOOM, oy - b * ZOOM, ox + a * ZOOM, oy + b * ZOOM)
    return np.stack((ring[:-1], ring[1:]), axis=1)


def _column(doc, host, sets, drawing, section):
    centre, xd, (a, b), base, top = doc.ifc.column_box(host)
    x = np.array((xd[0], xd[1], 0.0))
    y = np.array((-x[1], x[0], 0.0))
    z = np.array((0.0, 0.0, 1.0))
    o = np.array((centre[0], centre[1], base))
    h = top - base
    ann, cut = [], []                                                # (the elevation's; the section B-B's, at mid-height)
    _cut_mark(ann, (-a, h / 2.0), (-1.0, 0.0), CUTS["column"])        # (0.236: where it is cut)
    _cut_mark(ann, (a, h / 2.0), (1.0, 0.0), CUTS["column"])
    low = min([float(np.asarray(bb)[:, 2].min()) - base for _r, bars in sets for bb in bars] + [0.0])
    for k, (row, bars) in enumerate(sets):
        if row["role"] == "ties":
            for bar in bars:
                p = (np.asarray(bar) - o) @ np.column_stack((x, z))
                ann.append(_poly(((p[:, 0].min(), p[:, 1].mean()), (p[:, 0].max(), p[:, 1].mean())), LINK_PEN))
            mid = min(bars, key=lambda bb: abs(float(np.asarray(bb)[:, 2].mean()) - (base + h / 2)))
            level = float(np.asarray(mid)[:, 2].mean())
            for tie in bars:                                         # (0.227: an L's, a T's ties at that level)
                if abs(float(np.asarray(tie)[:, 2].mean()) - level) < 0.02:
                    q = (np.asarray(tie) - o) @ np.column_stack((x, y))
                    cut.append(_poly(q * ZOOM, LINK_PEN))
        else:
            for bar in bars:
                p = (np.asarray(bar) - o) @ np.column_stack((x, z))
                ann.append(_poly(p))
                hit = _crossing(bar, z, base + h / 2)
                if hit is not None:
                    r = max(row["diameter"] / 2000.0, DOT)
                    cut.append(_dot((((hit - o) @ x) * ZOOM, ((hit - o) @ y) * ZOOM), r * ZOOM))
        _row_label(drawing, ann, (-a, low - 0.30 - k * 0.16), row)      # (under the bars, their starters too)
    # (0.232) its dimensions: its height beside it, its section's sides (their real sizes; a round one's diameter)
    _dim(drawing, (-a, 0.0), (-a, h), 0.25)
    drawing.lines = _rect(-a, 0.0, a, h)
    drawing.annotations = ann
    _dim(section, (-a * ZOOM, -b * ZOOM), (a * ZOOM, -b * ZOOM), -0.40, value=2 * a)
    if doc.ifc.column_section(host)[0] != "circle":
        _dim(section, (a * ZOOM, b * ZOOM), (a * ZOOM, -b * ZOOM), 0.15, value=2 * b)
    section.lines = _section_outline(doc, host, a, b, 0.0, 0.0)
    section.annotations = cut


def _footing(doc, host, sets, drawing, section):
    centre, xd, length, width, top = doc.ifc.footing_params(host)
    depth = top - float(doc.ifc.placement(host)[2, 3])
    x = np.array((xd[0], xd[1], 0.0))
    y = np.array((-x[1], x[0], 0.0))
    z = np.array((0.0, 0.0, 1.0))
    o = np.array((centre[0], centre[1], top - depth))
    ann, cut = [], []                                                # (the plan's; the section C-C's, along its length)
    _cut_mark(ann, (-length / 2, 0.0), (-1.0, 0.0), CUTS["footing"])  # (0.236: where it is cut, across its middle)
    _cut_mark(ann, (length / 2, 0.0), (1.0, 0.0), CUTS["footing"])
    for k, (row, bars) in enumerate(sets):
        for bar in bars:                                             # (the plan: each bar end to end)
            p = (np.asarray(bar) - o) @ np.column_stack((x, y))
            ann.append(_poly(p[[0, -1]], BAR_PEN))
        if row["role"] in ("mesh_x", "top_x"):           # (the section: the bar it cuts along, bent — 0.250: the top's)
            mid = min(bars, key=lambda bb: abs(float((np.asarray(bb)[0] - o) @ y)))
            q = (np.asarray(mid) - o) @ np.column_stack((x, z))
            cut.append(_poly(q * ZOOM))
        else:                                                        # (…and those across it, as dots)
            r = max(row["diameter"] / 2000.0, DOT)
            for bar in bars:
                p = np.asarray(bar)
                cut.append(_dot((float((p.mean(axis=0) - o) @ x) * ZOOM, float(p[:, 2].min() - o[2]) * ZOOM),
                                r * ZOOM))
        _row_label(drawing, ann, (length / 2 + 0.15, width / 2 - 0.1 - k * 0.16), row)
    # (0.232) its dimensions: its plan's sides, its section's length and depth
    _dim(drawing, (-length / 2, width / 2), (length / 2, width / 2), 0.25)
    _dim(drawing, (-length / 2, -width / 2), (-length / 2, width / 2), 0.25)
    drawing.lines = _rect(-length / 2, -width / 2, length / 2, width / 2)
    drawing.annotations = ann
    _dim(section, (-length / 2 * ZOOM, 0.0), (length / 2 * ZOOM, 0.0), -0.40, value=length)
    _dim(section, (length / 2 * ZOOM, depth * ZOOM), (length / 2 * ZOOM, 0.0), 0.20, value=depth)
    section.lines = _rect(-length / 2 * ZOOM, 0.0, length / 2 * ZOOM, depth * ZOOM)
    section.annotations = cut


def _wall(doc, host, sets, drawing, _section):
    """(0.342) A concrete wall's elevation (seen from its axis's left — its front): its outline and openings, the bars
    of that face (vertical, horizontal, round the openings) and the starters below it; each set labelled."""
    start, end, _t = doc.ifc.wall_axis(host)
    length, height, _w = doc.ifc.wall_params(host)
    a = np.asarray(start, dtype=float)
    ux = np.asarray(end, dtype=float) - a
    ux = ux / max(float(np.linalg.norm(ux)), 1e-9)
    nx = np.array((-ux[1], ux[0], 0.0))
    z = np.array((0.0, 0.0, 1.0))
    lines = list(_rect(0.0, 0.0, length, height))
    for rel in (doc.ifc.by_guid(host).HasOpenings or ()):
        for fill in (rel.RelatedOpeningElement.HasFillings or ()):
            try:
                st = doc.ifc.filling_state(fill.RelatedBuildingElement.GlobalId)
            except Exception:
                continue
            s0, sill = float(st["s"]), float(st.get("sill") or 0.0)
            lines += list(_rect(s0, sill, s0 + float(st["width"]), sill + float(st["height"])))
    drawing.lines = np.asarray(lines, dtype=float).reshape(-1, 2, 2)
    ann = []
    for k, (row, bars) in enumerate(sets):
        front = [b for b in bars if float((np.asarray(b, dtype=float).mean(axis=0) - a) @ nx) >= 0.0] or bars
        pen = BAR_PEN if row["role"] == "wall_trim" else LINK_PEN
        for bar in front:
            p = (np.asarray(bar, dtype=float) - a) @ np.column_stack((ux, z))
            ann.append(_poly(p, pen))
        _row_label(drawing, ann, (length + 0.3, height - 0.2 - k * 0.25), row)
    drawing.annotations = ann
    _dim(drawing, (0.0, 0.0), (length, 0.0), -0.40)
    _dim(drawing, (0.0, height), (0.0, 0.0), -0.40)


def _slab(doc, host, sets, drawing, _section):
    info = doc.ifc.slab_outline(host)
    outline = np.asarray(info["outline"], dtype=float) if info else np.zeros((0, 2))
    ring = np.vstack((outline, outline[:1])) if len(outline) else outline
    drawing.lines = np.stack((ring[:-1], ring[1:]), axis=1) if len(ring) > 1 else np.zeros((0, 2, 2))
    ann = []
    x1 = float(outline[:, 0].max()) if len(outline) else 0.0
    y1 = float(outline[:, 1].max()) if len(outline) else 0.0
    for k, (row, bars) in enumerate(sets):
        pen = BAR_PEN if row["role"].startswith("top_") else LINK_PEN      # (0.224: the top bars, heavier)
        for bar in bars:
            ann.append(_poly(np.asarray(bar)[:, :2], pen))
        _row_label(drawing, ann, (x1 + 0.3, y1 - 0.2 - k * 0.25), row)
    drawing.annotations = ann
    if len(outline):                                     # (0.232) its overall sides
        x0, y0 = float(outline[:, 0].min()), float(outline[:, 1].min())
        _dim(drawing, (x0, y0), (x1, y0), -0.40)
        _dim(drawing, (x0, y1), (x0, y0), -0.40)
