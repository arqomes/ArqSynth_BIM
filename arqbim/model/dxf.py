"""A view's drawing to DXF (Phase 5, step 6): for AutoCAD and the other CAD programs — what model/drawings.py
makes (the plan of a storey, a section, an elevation) in metres (1 unit = 1 m), each kind of line on a layer
of its own: what is cut, what is seen, the hatches, the plan symbols, the dimensions, the 2D drawing and its
texts, the rooms, the grid, the views' marks. Texts and the marks' sizes are those on paper at the view's scale.

Written by hand as DXF R12 (ASCII, the version every CAD program reads), no library: LINE, POLYLINE (VERTEX,
SEQEND), CIRCLE and TEXT entities, and the layers' table. Solid fills (concrete…) go as their outline only —
R12 has no hatch entity; hatches by lines go as lines. Pure (no Qt)."""

import math
import os

import numpy as np

from ..core import drawing2d
from ..i18n import decimal_sep
from . import annotations as notes2d
from . import graphic_styles as styles_model
from . import symbols as marks_model

LAYERS = {                     # name -> AutoCAD colour index
    "CORTE": 7, "VISTO": 8, "TRAMAS": 9, "SIMBOLOS": 7, "SUBJACENTE": 9, "COTAS": 1, "DESENHO": 7,
    "TEXTOS": 7, "SALAS": 3, "GRELHA": 5, "MARCAS": 7, "ACIMA": 4, "ZONAS_LIVRES": 3,
    "ELETRICIDADE": 6, "CURVAS_NIVEL": 32, "CURVAS_MESTRAS": 34,      # (the terrain's contour lines, 0.155)
    "PLATAFORMAS": 30,                                                # (its platforms, 0.157)
    "TALUDES": 32,                                                    # (their slopes, 0.203)
    "IMAGENS": 8,                                                     # (background images' frames, 0.207)
}
CAP = 0.72                      # (0.398) a text's capitals: of its em (a DXF text's height is theirs)


class _Writer:
    def __init__(self):
        self.rows = []
        self.lo = np.array((np.inf, np.inf))
        self.hi = np.array((-np.inf, -np.inf))

    def _grow(self, *points):
        for p in points:
            p = np.asarray(p, dtype=float)[:2]
            self.lo, self.hi = np.minimum(self.lo, p), np.maximum(self.hi, p)

    def _put(self, *pairs):
        for code, value in pairs:
            if isinstance(value, float):
                value = "{:.6f}".format(value)
            self.rows.append("{}\n{}".format(code, value))

    def line(self, layer, a, b):
        self._grow(a, b)
        self._put((0, "LINE"), (8, layer), (10, float(a[0])), (20, float(a[1])), (30, 0.0),
                  (11, float(b[0])), (21, float(b[1])), (31, 0.0))

    def polyline(self, layer, points, closed=False):
        points = [np.asarray(p, dtype=float) for p in points]
        if len(points) < 2:
            return
        self._grow(*points)
        self._put((0, "POLYLINE"), (8, layer), (66, 1), (10, 0.0), (20, 0.0), (30, 0.0), (70, 1 if closed else 0))
        for p in points:
            self._put((0, "VERTEX"), (8, layer), (10, float(p[0])), (20, float(p[1])), (30, 0.0))
        self._put((0, "SEQEND"), (8, layer))

    def circle(self, layer, centre, radius):
        self._grow(np.asarray(centre) - radius, np.asarray(centre) + radius)
        self._put((0, "CIRCLE"), (8, layer), (10, float(centre[0])), (20, float(centre[1])), (30, 0.0),
                  (40, float(radius)))

    def text(self, layer, at, height, text, angle=0.0, centred=False, width=1.0, oblique=0.0):
        """A text from `at` (its baseline's start; centred: its middle there); (0.398) its width factor, its slant."""
        if not text:
            return
        self._grow(at)
        pairs = [(0, "TEXT"), (8, layer), (10, float(at[0])), (20, float(at[1])), (30, 0.0), (40, float(height)),
                 (1, str(text).replace("\n", " ")), (50, float(angle))]
        if abs(float(width) - 1.0) > 1e-6:
            pairs.append((41, float(width)))
        if abs(float(oblique)) > 1e-6:
            pairs.append((51, float(oblique)))
        if centred:                                       # (72 = 1: centred; 73 = 2: middle — at the 11 point)
            pairs += [(72, 1), (73, 2), (11, float(at[0])), (21, float(at[1])), (31, 0.0)]
        self._put(*pairs)

    def solid(self, layer, points):
        """(0.398) A filled triangle or quadrilateral (an arrow's head, a piece of a dot)."""
        pts = [np.asarray(p, dtype=float) for p in points][:4]
        if len(pts) < 3:
            return
        self._grow(*pts)
        if len(pts) == 3:
            pts.append(pts[2])
        pairs = [(0, "SOLID"), (8, layer)]
        for k, p in enumerate((pts[0], pts[1], pts[3], pts[2])):     # (SOLID's corners go 1, 2, 4, 3)
            pairs += [(10 + k, float(p[0])), (20 + k, float(p[1])), (30 + k, 0.0)]
        self._put(*pairs)

    def document(self, layers=None):
        """The DXF text; layers: {name: colour} (the drawings' LAYERS by default)."""
        layers = LAYERS if layers is None else layers
        lo = self.lo if np.all(np.isfinite(self.lo)) else np.zeros(2)
        hi = self.hi if np.all(np.isfinite(self.hi)) else np.zeros(2)
        head = ["0\nSECTION", "2\nHEADER", "9\n$ACADVER", "1\nAC1009",
                "9\n$EXTMIN", "10\n{:.6f}".format(lo[0]), "20\n{:.6f}".format(lo[1]), "30\n0.0",
                "9\n$EXTMAX", "10\n{:.6f}".format(hi[0]), "20\n{:.6f}".format(hi[1]), "30\n0.0",
                "0\nENDSEC", "0\nSECTION", "2\nTABLES", "0\nTABLE", "2\nLAYER", "70\n{}".format(len(layers))]
        for name, colour in layers.items():
            head += ["0\nLAYER", "2\n{}".format(name), "70\n0", "62\n{}".format(colour), "6\nCONTINUOUS"]
        head += ["0\nENDTAB", "0\nENDSEC", "0\nSECTION", "2\nENTITIES"]
        return "\n".join(head + self.rows + ["0\nENDSEC", "0\nEOF"]) + "\n"


def _hatch(w, ring, angles, spacing):
    """A cut's hatch, as lines inside its outline — (0.253) or a region (a shapely geometry) — (as
    annotations.hatch_lines, at any angle)."""
    from shapely.geometry import LineString, Polygon
    poly = ring if hasattr(ring, "geom_type") else Polygon(ring).buffer(0)
    if poly.is_empty or spacing <= 0:
        return
    x0, y0, x1, y1 = poly.bounds
    c = np.array(((x0 + x1) / 2, (y0 + y1) / 2))
    half = math.hypot(x1 - x0, y1 - y0) / 2 + spacing
    for a in angles:
        d = np.array((math.cos(math.radians(a)), math.sin(math.radians(a))))
        n = np.array((-d[1], d[0]))
        for k in range(-int(half / spacing), int(half / spacing) + 1):
            q = c + n * (k * spacing)
            cut = poly.intersection(LineString([q - d * half, q + d * half]))
            for g in getattr(cut, "geoms", [cut]):
                if g.geom_type == "LineString" and g.length > 1e-9:
                    xy = list(g.coords)
                    w.line("TRAMAS", xy[0], xy[-1])


def _dimensions(w, drawing, mm):
    """(0.398) The view's dimensions laid out by core/dim_layout as their types say (as on paper): lines, filled marks
    (SOLID), texts (their height the letters' capitals: CAP of the em; their width factor; italic as an oblique)."""
    from ..core import dim_layout
    style = getattr(drawing, "dim_style", None) or {}
    pen = styles_model.pen(getattr(drawing, "graphic_style", None), "dimension")
    layout = dim_layout.of_drawing(drawing.dims, style, mm, pen)
    for v2, r, start, sweep, text, a2, b2 in getattr(drawing, "angles", ()):
        layout.extend(dim_layout.angle_layout(v2, r, start, sweep, text, a2, b2, style, mm, pen))
    write_layout(w, layout, "COTAS")


def write_layout(w, layout, layer):
    """(0.398) A core.dim_layout.Layout in DXF on `layer`."""
    for a, b, _pen, _colour, _owner in layout.lines:
        w.line(layer, a, b)
    for pts, _colour, _owner in layout.fills:
        pts = np.asarray(pts, dtype=float)
        for k in range(1, len(pts) - 1):                     # (a fan of SOLID triangles)
            w.solid(layer, (pts[0], pts[k], pts[k + 1]))
    for item in layout.texts:
        w.text(layer, item.at, item.height * CAP, item.text, item.angle, centred=True, width=item.width,
               oblique=15.0 if item.italic else 0.0)


def _marks(w, drawing, mm, gstyle=None):
    """The views' symbols (0.360: as the project's symbols' styles draw them — their heads' shape and arrow, the
    section's line whole or at its ends, the texts' heights)."""
    styles = {k: styles_model.symbol(gstyle, k) for k in styles_model.SYMBOL_KINDS}
    for m in getattr(drawing, "marks", ()):
        look = np.asarray(m.look, dtype=float)
        style = styles["section" if m.kind == "section" else "elevation"]
        head = style["size"] * mm
        if m.kind == "section":
            d = (m.b - m.a) / max(float(np.linalg.norm(m.b - m.a)), 1e-9)
            over = 0.0 if getattr(m, "own", False) else marks_model.SECTION_OVER * mm     # (0.358: its own ends)
            a, b = m.a - d * over, m.b + d * over
            for p, q in marks_model.line_pieces(a, b, style, mm)[0]:
                w.line("MARCAS", p, q)
            centres = (a - d * head, b + d * head)
        else:
            centres = (np.asarray(m.a, dtype=float) - look * marks_model.ELEVATION_OUT * mm,)
        for c in centres:
            lines, filled, hollow, _r = marks_model.head_shape(style, look, mm)
            if style["head"] == "circle":               # (a CAD circle, not its sides)
                w.circle("MARCAS", c, head)
                lines = []
            for p, q in lines:
                w.line("MARCAS", c + p, c + q)
            for tri in filled + hollow:
                w.polyline("MARCAS", [c + p for p in tri], closed=True)
            w.text("MARCAS", c, style["text"] * 0.92 * mm, m.tag, centred=True)
    levels = getattr(drawing, "levels", ())
    if levels:
        box = drawing.bounds()
        if box is not None:
            lo, hi = box
            level = styles["level"]
            for z, name in levels:
                a = np.array((lo[0] - marks_model.LEVEL_OVER * mm, z))
                b = np.array((hi[0] + marks_model.LEVEL_OVER * mm, z))
                for p, q in marks_model.line_pieces(a, b, level, mm)[0]:
                    w.line("MARCAS", p, q)
                w.text("MARCAS", b + np.array((2.5, 1.0)) * mm, level["text"] * mm,
                       "{}  {}".format(marks_model.level_text(z), name))


def write(path, drawing, scale=100):
    """The drawing to a DXF file at `path` (metres). scale: the N of 1:N its texts and marks are sized for.
    Returns how many entities."""
    mm = float(scale) / 1000.0                       # metres in the model per mm on paper
    w = _Writer()
    gstyle = getattr(drawing, "graphic_style", None) or styles_model.DEFAULTS
    for a, b in np.asarray(drawing.underlay).reshape(-1, 2, 2):
        w.line("SUBJACENTE", a, b)
    for a, b in np.asarray(drawing.lines).reshape(-1, 2, 2):
        w.line("VISTO", a, b)
    outline = getattr(drawing, "outline", None)
    for ring in drawing.cut if outline is None else outline:        # (0.320: joined — no line between two walls)
        w.polyline("CORTE", ring, closed=True)
    for a, b in np.asarray(getattr(drawing, "breaks", ())).reshape(-1, 2, 2):   # (0.333: …unless unjoined by hand)
        w.line("CORTE", a, b)
    fills = drawing.fills or list(zip(drawing.cut, list(drawing.hatch) + [None] * len(drawing.cut)))
    by_hatch = {}                                    # (0.253: each hatch once, over its outlines less their holes)
    for ring, hatch in fills:
        if not (isinstance(hatch, str) and hatch.startswith("colour:")):
            by_hatch.setdefault(hatch, []).append(ring)
    for hatch, rings in by_hatch.items():
        _fill, angles, spacing = styles_model.hatch(gstyle, hatch)
        if angles:                                   # (0.320: joined — one material's parts may lie in a hole)
            _hatch(w, drawing2d.nested(rings) if outline is not None else drawing2d.region(rings), angles,
                   spacing * mm)
    for a, b in np.asarray(drawing.symbols).reshape(-1, 2, 2):
        w.line("SIMBOLOS", a, b)
    for ring in getattr(drawing, "above", ()):                      # (pipes and ducts above the cut, 0.135)
        w.polyline("ACIMA", ring, closed=True)
    for ring in getattr(drawing, "zones", ()):                       # (the fixtures' free zones, 0.140)
        w.polyline("ZONAS_LIVRES", ring, closed=True)
    for segs, major, h in getattr(drawing, "contours", ()):          # (the terrain's contour lines, 0.155)
        for a, b in segs:
            w.line("CURVAS_MESTRAS" if major else "CURVAS_NIVEL", a, b)
        if major:                                                    # (their heights along them, 0.202)
            from ..core import terrain as terrain_geo
            words = terrain_geo.contour_text(h, decimal_sep())
            for line in terrain_geo.chains(segs):
                for point, angle in terrain_geo.label_spots(line, terrain_geo.LABEL_EVERY * 1000.0 * mm,
                                                            terrain_geo.LABEL_SHORTEST * 1000.0 * mm):
                    w.text("CURVAS_MESTRAS", point, 1.8 * mm, words, angle=angle, centred=True)
    for a, b in getattr(drawing, "batters", ()):                     # (their slopes, 0.203)
        w.line("TALUDES", a, b)
    for corners, picture, _opacity, *kept in getattr(drawing, "images", ()):   # (background images: R12 has no
        frame = kept[0] if kept else corners                            # pictures — their frame (the part kept,
        w.polyline("IMAGENS", frame, closed=True)                       # 0.209) and file's name, 0.207)
        w.text("IMAGENS", np.asarray(frame[0], dtype=float) + (mm, mm), 2.5 * mm, os.path.basename(picture))
    for ring, words in getattr(drawing, "platforms", ()):            # (the terrain's platforms, 0.157)
        w.polyline("PLATAFORMAS", ring, closed=True)
        w.text("PLATAFORMAS", np.asarray(ring, dtype=float).mean(axis=0), 2.5 * mm, words)
    if getattr(drawing, "points", None):                             # (the electrical points' symbols, 0.143)
        from ..ifc.electrical import point_symbol
        for kind, back, angle in drawing.points:
            lines, solids = point_symbol(kind, back, angle, mm)
            for a, b in lines:
                w.line("ELETRICIDADE", a, b)
            for poly in solids:
                w.polyline("ELETRICIDADE", poly, closed=True)
    for mid, down, text, radius in getattr(drawing, "slopes", ()):   # (the pipes that fall: arrow and slope, 0.136)
        a, b, head, at, angle = marks_model.slope_mark(mid, down, radius, mm)
        w.line("COTAS", a, b)
        w.polyline("COTAS", head, closed=True)
        w.text("COTAS", at, marks_model.SLOPE_TEXT * mm, text, angle, centred=True)
    for a2, b2, tag in drawing.grids:
        a2, b2 = np.asarray(a2, dtype=float), np.asarray(b2, dtype=float)
        d = (b2 - a2) / max(float(np.linalg.norm(b2 - a2)), 1e-9)
        w.line("GRELHA", a2, b2)
        r = 3.5 * mm
        for end, out in ((a2, -d), (b2, d)):
            w.circle("GRELHA", end + out * r, r)
            w.text("GRELHA", end + out * r, r * 1.1, tag, centred=True)
    for at, name, number, area in getattr(drawing, "rooms", ()):
        title = " ".join(x for x in ((name or "").upper(), number or "") if x)
        w.text("SALAS", np.asarray(at) + np.array((0.0, 1.2)) * mm, 2.5 * mm, title, centred=True)
        w.text("SALAS", np.asarray(at) - np.array((0.0, 2.0)) * mm, 2.1 * mm, area, centred=True)
    for item in getattr(drawing, "annotations", ()):
        kind, shapes, hatch, text, at, size = item[:6]
        for pts, closed in shapes:
            w.polyline("DESENHO", pts, closed)
        if kind == "region" and shapes and hatch in ("diagonal", "cross"):
            _hatch(w, shapes[0][0], (45.0,) if hatch == "diagonal" else (45.0, -45.0),
                   notes2d.HATCH_SPACING * mm)
        if kind == "level":                               # (0.192) its filled quarters: outlined
            for quarter in hatch:
                w.polyline("DESENHO", quarter, True)
        if kind == "keynote" and shapes:                  # (0.194) its box on the leader's tip, its code in it
            box, middle = notes2d.keynote_box(shapes[0][0][0], at, text, float(size), mm)
            w.polyline("TEXTOS", box, True)
            w.text("TEXTOS", middle, float(size) * mm, text, centred=True)
            continue
        if kind in ("text", "spot", "level") and text:
            w.text("TEXTOS", at, float(size) * mm, text, angle=float(item[8]) if len(item) > 8 and item[8] else 0.0)
    _dimensions(w, drawing, mm)
    _marks(w, drawing, mm, gstyle)
    with open(path, "w", encoding="cp1252", errors="replace", newline="\r\n") as f:
        f.write(w.document())
    return len([r for r in w.rows if r.startswith("0\n") and r not in ("0\nVERTEX", "0\nSEQEND")])
