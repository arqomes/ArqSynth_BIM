"""Print drawings (model/drawings.py) to a vector PDF with Qt's QPdfWriter: lines and
fills stay vectors (sharp at any zoom, measurable). One view on A3 landscape at the largest
usual scale that fits, or sheets (model/sheets.py) with several views, one page each. A
title block bottom right. Each view: the edges seen beyond the cut, then the cut filled
dark (it hides the edges under the walls), then its outline; its name and scale below.

The same painting draws a sheet on screen (ui/sheet_view.py): paint_sheet works on any
QPainter, given how many of its units make a millimetre.
"""

import datetime
import math
import os
import re

import numpy as np
from PySide6 import QtCore, QtGui

from ..i18n import t
from ..model import graphic_styles as styles_model
from ..model import sheets as sheets_model
from ..model.sheets import LABEL_H, MARGIN, SCALES, TITLE_H, TITLE_W
from . import pattern_paint

CUT_PEN = 0.50             # mm: outline of what is cut
SEEN_PEN = 0.18            # mm: edges seen beyond the cut, plan symbols (door swings)
HATCH_PEN = 0.10           # mm: hatch lines
DIM_PEN = 0.13             # mm: dimension lines
LINE_PEN = 0.25            # mm: the lines drawn in a view (0.120)
ROOM_TEXT = 2.5            # mm on paper: a room's name (0.125); its area a little smaller
# (0.398: the dimensions' gaps, marks and texts are their type's — core/dim_layout)
UNDERLAY = QtGui.QColor("#a8a8a8")   # a plan's underlay storey
CONTOUR = QtGui.QColor("#7d6a4f")    # the terrain's contour lines (0.155)
GRID_INK = QtGui.QColor("#3a5a7a")   # the structural grid
GRID_PEN = 0.18            # mm: its axes
GRID_BUBBLE = 3.5          # mm on paper: the radius of an axis's bubble
WHITE = QtGui.QColor("white")
# (a cut material's fill and hatch, and the pens: the project's graphic style, model/graphic_styles.py, 0.126;
# CUT_PEN… above are its usual widths, kept for the symbols drawn at a fixed weight)
RESOLUTION = 600           # dots per inch of the PDF's coordinates (the result is vector anyway)
IMAGE_SVG = 2.0            # (0.369) pixels a painter unit of a plan's background image cut for an SVG (192 dpi there)


def fit_scale(drawing, width_mm, height_mm):
    """The largest usual scale (smallest 1:N) at which the drawing fits in width × height mm."""
    lo, hi = drawing.bounds()
    size = (hi - lo) * 1000.0                         # mm at 1:1
    for n in SCALES:
        if size[0] / n <= width_mm and size[1] / n <= height_mm:
            return n
    return SCALES[-1]


def paint_drawing(painter, drawing, scale, centre, dpmm, label=None):
    """The drawing at 1:scale with its middle at `centre` (mm on the sheet); its label below."""
    lo, hi = drawing.bounds()
    mid = (lo + hi) / 2
    cx, cy = centre

    def to_page(p):
        """metres (drawing) -> painter units on the sheet (y down)."""
        p = np.asarray(p, dtype=float)
        x = (cx + (p[..., 0] - mid[0]) * 1000.0 / scale) * dpmm
        y = (cy - (p[..., 1] - mid[1]) * 1000.0 / scale) * dpmm
        return np.stack((x, y), axis=-1)

    def pen(mm):
        p = QtGui.QPen(QtGui.QColor("black"), mm * dpmm)
        p.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        p.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        return p

    gstyle = getattr(drawing, "graphic_style", None) or styles_model.DEFAULTS      # (the project's pens, 0.126)
    seen_pen, cut_pen, hatch_pen = (styles_model.pen(gstyle, k) for k in ("seen", "cut", "hatch"))
    if getattr(drawing, "images", None):              # its background images, under all, inside it (0.207)
        _images(painter, drawing.images, to_page, to_page(lo), to_page(hi))
    # another storey under it, in grey (the plan's underlay, 0.65)
    if len(drawing.underlay):
        seg = to_page(drawing.underlay)
        grey = pen(seen_pen)
        grey.setColor(UNDERLAY)
        painter.setPen(grey)
        painter.drawLines([QtCore.QLineF(a[0], a[1], b[0], b[1]) for a, b in seg])
    if getattr(drawing, "slope_fills", None):         # the terrains coloured by slope, under all (0.201)
        _slope_fills(painter, drawing.slope_fills, to_page)
    # the terrain's contour lines (0.155): thin, the major ones (every fifth) thicker, in a soft earth colour
    for segs, major, _h in getattr(drawing, "contours", ()):
        seg = to_page(segs)
        line = pen(seen_pen * (1.6 if major else 0.7))
        line.setColor(CONTOUR)
        painter.setPen(line)
        painter.drawLines([QtCore.QLineF(a[0], a[1], b[0], b[1]) for a, b in seg])
    for segs, major, h in getattr(drawing, "contours", ()):       # the major ones' heights along them (0.202)
        if major:
            _contour_labels(painter, segs, h, to_page, scale, dpmm)
    if len(getattr(drawing, "batters", ())):          # their slopes: where they meet the ground, the ticks (0.203)
        painter.setPen(pen(seen_pen * 0.8))
        seg = to_page(drawing.batters)
        painter.drawLines([QtCore.QLineF(a[0], a[1], b[0], b[1]) for a, b in seg])
    # its platforms (0.157): their outline, a little thicker, and their height in the middle
    for ring, words in getattr(drawing, "platforms", ()):
        painter.setPen(pen(seen_pen * 1.8))
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawPolygon(_polygon(to_page(ring)))
        x, y = (float(c) / dpmm for c in to_page(np.asarray(ring, dtype=float).mean(axis=0)))
        _text(painter, dpmm, x, y - 2.5 * 1.6, 400.0, 2.5 * 1.6, words, 2.5 / 0.3528)
    # (0.315) its view style's: the faces seen, painted (the farthest first), and their surface patterns
    if getattr(drawing, "faces", None):
        _faces(painter, drawing.faces, to_page, dpmm)
    for segs, colour in getattr(drawing, "surface_lines", ()):
        line = pen(hatch_pen)
        line.setColor(QtGui.QColor(colour))
        painter.setPen(line)
        seg = to_page(segs)
        painter.drawLines([QtCore.QLineF(a[0], a[1], b[0], b[1]) for a, b in seg])
    # edges seen beyond the cut
    if len(drawing.lines):
        seg = to_page(drawing.lines)
        painter.setPen(pen(seen_pen))
        painter.drawLines([QtCore.QLineF(a[0], a[1], b[0], b[1]) for a, b in seg])
    # what is cut: filled by material (dark, grey or hatched; holes stay open), a thin line between
    # the layers of an element, then the outline of all that is cut, joined (no line where two walls meet)
    by_hatch, seams, outline = _paths(drawing)
    k = 1000.0 / scale * dpmm
    to_sheet = QtGui.QTransform(k, 0.0, 0.0, -k, (cx - mid[0] * 1000.0 / scale) * dpmm,
                                (cy + mid[1] * 1000.0 / scale) * dpmm)
    own_cuts = getattr(drawing, "cut_patterns", None) or {}
    for kind, path in by_hatch.items():
        path = to_sheet.map(path)
        if kind in own_cuts:                    # (0.314) its material's own: white, its background, its foreground
            painter.fillPath(path, WHITE)
            background, foreground = own_cuts[kind]
            pattern_paint.paint_pair(painter, path, background, foreground, dpmm, width=hatch_pen * dpmm)
            continue
        library = None
        if isinstance(kind, str) and kind.startswith("colour:"):     # (a graphic rule's colour: a phase…)
            fill, angles, spacing = QtGui.QColor(kind[len("colour:"):]), (), 0.0
        else:                                                          # (the project's hatches, 0.126)
            colour, angles, spacing = styles_model.hatch(gstyle, kind)
            fill = QtGui.QColor(colour)
            library = styles_model.library_pattern(gstyle, kind)      # (0.314: or a pattern of the library)
        painter.fillPath(path, fill)
        if library:
            pattern_paint.paint(painter, path, library, "black", dpmm, hatch_pen * dpmm)
        if angles:
            _hatch(painter, path, angles, spacing * dpmm, pen(hatch_pen))
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    if not seams.isEmpty():
        painter.setPen(pen(hatch_pen))
        painter.drawPath(to_sheet.map(seams))
    painter.setPen(pen(cut_pen))
    painter.drawPath(to_sheet.map(outline))
    breaks = getattr(drawing, "breaks", None)       # (0.333) between elements unjoined by hand: as the outline
    if breaks is not None and len(breaks):
        seg = to_page(breaks)
        painter.drawLines([QtCore.QLineF(a[0], a[1], b[0], b[1]) for a, b in seg])
    # the pipes and ducts above the cut, dashed (0.135)
    if getattr(drawing, "above", None):
        dashed = pen(seen_pen)
        dashed.setDashPattern([6, 3])
        painter.setPen(dashed)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        for ring in drawing.above:
            painter.drawPolygon(_polygon(to_page(ring)))
    if getattr(drawing, "zones", None):               # the free zones in front of the fixtures, dashed (0.140)
        thin = pen(seen_pen * 0.7)
        thin.setDashPattern([4, 3])
        painter.setPen(thin)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        for ring in drawing.zones:
            painter.drawPolygon(_polygon(to_page(ring)))
    if getattr(drawing, "points", None):              # the electrical points' symbols (0.143)
        from ..ifc.electrical import point_symbol
        painter.setPen(pen(seen_pen))
        for kind, back, angle in drawing.points:
            lines, solids = point_symbol(kind, back, angle, scale / 1000.0)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            if lines:
                seg = to_page(np.array(lines))
                painter.drawLines([QtCore.QLineF(a[0], a[1], b[0], b[1]) for a, b in seg])
            painter.setBrush(QtGui.QColor("black"))
            for poly in solids:
                painter.drawPolygon(_polygon(to_page(np.array(poly))))
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    if getattr(drawing, "slopes", None):              # the pipes that fall: an arrow and "1 %" (0.136)
        _slopes(painter, drawing.slopes, to_page, scale, dpmm, pen(styles_model.pen(gstyle, "dimension")))
    # plan symbols (doors: linings, the leaf open, the swing arc)
    if len(drawing.symbols):
        seg = to_page(drawing.symbols)
        painter.setPen(pen(seen_pen))
        painter.drawLines([QtCore.QLineF(a[0], a[1], b[0], b[1]) for a, b in seg])
    if drawing.grids:
        _grids(painter, drawing.grids, to_page, dpmm)
    if getattr(drawing, "rooms", None):
        _rooms(painter, drawing.rooms, to_page, dpmm)
    if getattr(drawing, "annotations", None):
        _annotations(painter, drawing.annotations, to_page, dpmm, pen, gstyle)
    if getattr(drawing, "marks", None):
        _marks(painter, drawing.marks, to_page, dpmm, pen, gstyle)
    if getattr(drawing, "callouts", None):
        _callouts(painter, drawing.callouts, to_page, dpmm, pen, gstyle)
    if getattr(drawing, "levels", None):
        _levels(painter, drawing, to_page, dpmm, pen, gstyle)
    if getattr(drawing, "north", False):
        _north(painter, to_page(hi), dpmm, pen)
    style = getattr(drawing, "dim_style", None) or {}
    dim_pen = styles_model.pen(gstyle, "dimension")       # (0.398: mm — a dimension type may have its own)
    if drawing.dims:
        _dimensions(painter, drawing.dims, to_page, scale, dpmm, dim_pen, style)
    if getattr(drawing, "angles", None):
        _angles(painter, drawing.angles, to_page, scale, dpmm, dim_pen, style)
    if getattr(drawing, "slope_fills", None):         # their legend, in its lower left corner (0.201)
        _slope_legend(painter, to_page(lo), dpmm, {band for band, _parts in drawing.slope_fills})
    if label:
        bottom = cy + (hi[1] - lo[1]) * 1000.0 / scale / 2
        if getattr(drawing, "marks", None):           # (under the heads of the marks at its bottom, 0.121)
            from ..model.symbols import ELEVATION_OUT, HEAD
            bottom += ELEVATION_OUT + HEAD * 1.5
        _text(painter, dpmm, cx - 100, bottom + 1.5, 200, LABEL_H - 2, "{}   1:{}".format(label, scale), 8,
              bold=True, align=QtCore.Qt.AlignmentFlag.AlignHCenter)


def paint_table(painter, table, centre, dpmm, label=None):
    """A schedule's table on a sheet (0.132, model/drawings.TableDrawing) with its middle at `centre` (mm): a row
    of headings (bold, grey under), its rows, its totals, thin lines between the cells; its name (`label`, else
    its title) under it, as a view's."""
    from ..model.drawings import TABLE_ROW, TABLE_TEXT
    w, h = table.paper_size()
    x0, y0 = centre[0] - w / 2, centre[1] - h / 2
    widths = table.widths()
    if getattr(table, "cells", None):                       # (0.478) a table of the project's, as its grid
        _paint_grid(painter, table, x0, y0, widths, dpmm, TABLE_TEXT / 0.3528)
        _text(painter, dpmm, x0 - 50.0, y0 + h + 1.5, w + 100.0, LABEL_H - 2, label or table.title, 8, bold=True,
              align=QtCore.Qt.AlignmentFlag.AlignHCenter)
        return
    thin = QtGui.QPen(QtGui.QColor("black"), 0.13 * dpmm)
    painter.setPen(QtGui.QPen(QtGui.QColor("black"), 0.35 * dpmm))
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    painter.drawRect(QtCore.QRectF(x0 * dpmm, y0 * dpmm, w * dpmm, h * dpmm))
    painter.fillRect(QtCore.QRectF(x0 * dpmm, y0 * dpmm, w * dpmm, TABLE_ROW * dpmm), QtGui.QColor("#e6e6e6"))
    size = TABLE_TEXT / 0.3528
    for r, cells in enumerate([table.header] + list(table.rows)):
        y = y0 + r * TABLE_ROW
        x = x0
        for c, width in enumerate(widths):
            text = str(cells[c]) if c < len(cells) else ""
            right = r > 0 and bool(re.match(r"^[\d\-+,.]+( m| m²| m³)?$", text))
            _text(painter, dpmm, x + 1.2, y + 0.4, width - 2.4, TABLE_ROW - 0.8, text, size, bold=(r == 0),
                  align=QtCore.Qt.AlignmentFlag.AlignRight if right else QtCore.Qt.AlignmentFlag.AlignLeft, elide=True)
            x += width
        painter.setPen(thin)
        painter.drawLine(QtCore.QPointF(x0 * dpmm, (y + TABLE_ROW) * dpmm),
                         QtCore.QPointF((x0 + w) * dpmm, (y + TABLE_ROW) * dpmm))
    x = x0
    painter.setPen(thin)
    for width in widths[:-1]:
        x += width
        painter.drawLine(QtCore.QPointF(x * dpmm, y0 * dpmm),
                         QtCore.QPointF(x * dpmm, (y0 + TABLE_ROW * (len(table.rows) + 1)) * dpmm))
    if table.totals:
        _text(painter, dpmm, x0 + 1.2, y0 + TABLE_ROW * (len(table.rows) + 1) + 0.4, w - 2.4, TABLE_ROW - 0.8,
              table.totals, size, bold=True, elide=True)
    _text(painter, dpmm, x0 - 50.0, y0 + h + 1.5, w + 100.0, LABEL_H - 2, label or table.title, 8, bold=True,
          align=QtCore.Qt.AlignmentFlag.AlignHCenter)                  # (under it, as a view's name)


def _paint_grid(painter, table, x0, y0, widths, dpmm, size):
    """(0.478) A table of the project's on a sheet as its grid is (model/table_sheet): each cell's fill and text (bold,
    italic, aligned — the headings centred on light grey, the numbers to the right), its merged cells; from the
    headings to the totals ruled thin, as a table always was, the title and note rows free; the cells' own borders over
    it all (thick ones thicker)."""
    from ..model.drawings import TABLE_ROW
    lefts = [x0]
    for width in widths:
        lefts.append(lefts[-1] + width)
    spans = {(g, c): (rows, cols) for g, c, rows, cols in table.spans}
    covered = {(g + i, c + j) for (g, c), (rows, cols) in spans.items() for i in range(rows) for j in range(cols)
               if i or j}
    thin = QtGui.QPen(QtGui.QColor("black"), 0.13 * dpmm)
    pens = {False: QtGui.QPen(QtGui.QColor("black"), 0.25 * dpmm), True: QtGui.QPen(QtGui.QColor("black"), 0.5 * dpmm)}
    align = {"left": QtCore.Qt.AlignmentFlag.AlignLeft, "center": QtCore.Qt.AlignmentFlag.AlignHCenter,
             "right": QtCore.Qt.AlignmentFlag.AlignRight}
    body = [g for g, line in enumerate(table.cells) if line and line[0]["zone"] in ("H", "D", "S")]
    borders = []
    for g, line in enumerate(table.cells):
        for c, cell in enumerate(line):
            if (g, c) in covered or c >= len(widths):
                continue
            rows, cols = spans.get((g, c), (1, 1))
            x, y = lefts[c], y0 + g * TABLE_ROW
            wd, ht = lefts[min(c + cols, len(widths))] - x, rows * TABLE_ROW
            zone = cell["zone"]
            fill = cell.get("f") or ("#e6e6e6" if zone == "H" else None)
            if fill:
                painter.fillRect(QtCore.QRectF(x * dpmm, y * dpmm, wd * dpmm, ht * dpmm), QtGui.QColor(fill))
            how = cell.get("a") or ("center" if zone == "H" else "right" if cell.get("num") else "left")
            _text(painter, dpmm, x + 1.2, y + 0.4, wd - 2.4, ht - 0.8, str(cell["text"]), size,
                  bold=cell.get("b", zone in ("H", "S")), align=align[how], elide=True, italic=cell.get("i", False))
            if cell.get("bd"):
                borders.append((x, y, wd, ht, cell["bd"], bool(cell.get("bw"))))
    if body:                                                # (the table itself: thin lines, its outline thicker)
        top, bottom = y0 + body[0] * TABLE_ROW, y0 + (body[-1] + 1) * TABLE_ROW
        painter.setPen(thin)
        for g in body[:-1]:
            yy = (y0 + (g + 1) * TABLE_ROW) * dpmm
            painter.drawLine(QtCore.QPointF(x0 * dpmm, yy), QtCore.QPointF(lefts[-1] * dpmm, yy))
        inside = {(g, k) for (g0, c0), (rows, cols) in spans.items() for g in range(g0, g0 + rows)
                  for k in range(c0 + 1, c0 + cols)}            # (no line through a merged heading or total)
        for g in body:
            ya, yb = (y0 + g * TABLE_ROW) * dpmm, (y0 + (g + 1) * TABLE_ROW) * dpmm
            for k in range(1, len(widths)):
                if (g, k) not in inside:
                    painter.drawLine(QtCore.QPointF(lefts[k] * dpmm, ya), QtCore.QPointF(lefts[k] * dpmm, yb))
        painter.setPen(QtGui.QPen(QtGui.QColor("black"), 0.35 * dpmm))
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawRect(QtCore.QRectF(x0 * dpmm, top * dpmm, (lefts[-1] - x0) * dpmm, (bottom - top) * dpmm))
    for x, y, wd, ht, sides, thick in borders:              # (the cells' own, over it all)
        painter.setPen(pens[thick])
        a, b = QtCore.QPointF(x * dpmm, y * dpmm), QtCore.QPointF((x + wd) * dpmm, y * dpmm)
        d, e = QtCore.QPointF(x * dpmm, (y + ht) * dpmm), QtCore.QPointF((x + wd) * dpmm, (y + ht) * dpmm)
        for side, (p, q) in (("l", (a, d)), ("t", (a, b)), ("r", (b, e)), ("b", (d, e))):
            if side in sides:
                painter.drawLine(p, q)


def _grids(painter, grids, to_page, dpmm):
    """The structural grid's axes (0.67): dash-dot lines, a bubble with the tag beyond each end."""
    line = QtGui.QPen(GRID_INK, GRID_PEN * dpmm)
    line.setDashPattern([12, 3, 2, 3])
    ring = QtGui.QPen(GRID_INK, CUT_PEN * 0.6 * dpmm)
    r = GRID_BUBBLE * dpmm
    for a2, b2, tag in grids:
        a, b = to_page(np.array([a2, b2]))
        d = b - a
        if np.linalg.norm(d) < 1e-9:
            continue
        d = d / np.linalg.norm(d)
        painter.setPen(line)
        painter.drawLine(QtCore.QLineF(a[0], a[1], b[0], b[1]))
        for end, out in ((a, -d), (b, d)):
            centre = end + out * r
            painter.setPen(ring)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QtCore.QPointF(float(centre[0]), float(centre[1])), r, r)
            _text(painter, dpmm, float(centre[0]) / dpmm - GRID_BUBBLE, float(centre[1]) / dpmm - GRID_BUBBLE,
                  2 * GRID_BUBBLE, 2 * GRID_BUBBLE, tag, GRID_BUBBLE * 1.6 / 0.3528,
                  align=QtCore.Qt.AlignmentFlag.AlignHCenter, colour=GRID_INK)


def _annotations(painter, annotations, to_page, dpmm, pen, gstyle=None):
    """What is drawn in the view (0.120): its regions filled (grey, or white with their hatch), then the lines
    over them — each its own width and line type (0.126; else the project's pen for them) —, then the texts,
    their size on the paper, whatever the scale."""
    from ..model.annotations import HATCH_SPACING, keynote_box
    hatch_pen = styles_model.pen(gstyle, "hatch")
    for item in annotations:
        kind, shapes, hatch = item[0], item[1], item[2]
        if kind == "level":                                  # (0.192) a level mark's two quarters, black
            for quarter in hatch:
                path = QtGui.QPainterPath()
                path.addPolygon(_polygon(to_page(np.asarray(quarter))))
                path.closeSubpath()
                painter.fillPath(path, QtGui.QColor("black"))
            continue
        if kind != "region" or not shapes:
            continue
        path = QtGui.QPainterPath()
        path.addPolygon(_polygon(to_page(shapes[0][0])))
        path.closeSubpath()
        if hatch == "solid":
            painter.fillPath(path, QtGui.QColor("#9a9a9a"))
        elif hatch == "mask":                                # (0.450) a masking region: white, hiding what is under
            painter.fillPath(path, WHITE)
        elif hatch in ("diagonal", "cross"):
            painter.fillPath(path, WHITE)
            _hatch(painter, path, (45,) if hatch == "diagonal" else (45, -45), HATCH_SPACING * dpmm, pen(hatch_pen))
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    for item in annotations:
        shapes = item[1]
        if item[0] == "region" and item[2] == "mask":        # (0.450: a mask's outline is not on paper)
            continue
        line, width = (item[6], item[7]) if len(item) > 7 else ("continuous", None)
        width = float(width) if width else styles_model.pen(gstyle, "drawn")
        p = pen(width)
        dashes = styles_model.DASHES.get(line)
        if dashes:                                           # (Qt counts a dash in pen widths)
            p.setDashPattern([d / width for d in dashes])
            p.setCapStyle(QtCore.Qt.PenCapStyle.FlatCap)
        painter.setPen(p)
        for pts, closed in shapes:
            poly = _polygon(to_page(pts))
            if closed:
                painter.drawPolygon(poly)
            else:
                painter.drawPolyline(poly)
    for item in annotations:
        kind, text, at, size = item[0], item[3], item[4], item[5]
        if kind == "keynote" and item[1]:                    # (0.194) its box on the leader's tip, its code in it
            start, tip = to_page(np.asarray(item[1][0][0][0])), to_page(np.asarray(at))
            box, middle = keynote_box(start, tip, text, size, dpmm)
            painter.setBrush(WHITE)
            painter.setPen(pen(styles_model.pen(gstyle, "drawn")))
            painter.drawPolygon(_polygon(box))
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            x, y = float(middle[0]) / dpmm, float(middle[1]) / dpmm
            _text(painter, dpmm, x - 50.0, y - size * 0.8, 100.0, size * 1.6, text, size / 0.3528,
                  align=QtCore.Qt.AlignmentFlag.AlignHCenter)
            continue
        if kind in ("text", "spot", "level") and text:
            x, y = (float(c) / dpmm for c in to_page(at))
            turned = float(item[8]) if len(item) > 8 and item[8] else 0.0
            if abs(turned) > 1e-9:                      # (0.191) a text turned about where it starts
                painter.save()
                painter.translate(x * dpmm, y * dpmm)
                painter.rotate(-turned)                 # (the page's y runs down: counter-clockwise is negative)
                _text(painter, dpmm, 0.0, -size * 1.6, 400.0, size * 1.6, text, size / 0.3528)
                painter.restore()
                continue
            _text(painter, dpmm, x, y - size * 1.6, 400.0, size * 1.6, text, size / 0.3528)


def _slopes(painter, slopes, to_page, scale, dpmm, line):
    """(0.136) A plan's pipes that fall: beside each an arrow down its fall, its slope written over it — their size
    on the paper, whatever the scale."""
    from ..model.symbols import SLOPE_TEXT, slope_mark
    for mid, down, text, radius in slopes:
        a, b, head, at, angle = slope_mark(mid, down, radius, scale / 1000.0)
        pa, pb = to_page(np.array([a, b]))
        painter.setPen(line)
        painter.drawLine(QtCore.QLineF(pa[0], pa[1], pb[0], pb[1]))
        painter.setBrush(QtGui.QColor("black"))
        painter.drawPolygon(_polygon(to_page(np.array(head))))
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        x, y = (float(c) for c in to_page(np.asarray(at, dtype=float)))
        painter.save()
        painter.translate(x, y)
        painter.rotate(-angle)                         # (the page's y runs down)
        _text(painter, dpmm, -15.0, -SLOPE_TEXT * 0.8, 30.0, SLOPE_TEXT * 1.6, text, SLOPE_TEXT / 0.3528,
              align=QtCore.Qt.AlignmentFlag.AlignHCenter)
        painter.restore()


_PICTURES = {}             # (0.207) the background images' pictures read: path -> (its file's time, QImage or None)


def _picture(path):
    """A background image's picture (read once, again when its file changes), or None (missing, damaged)."""
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        return None
    found = _PICTURES.get(path)
    if found is None or found[0] != stamp:
        image = QtGui.QImage(path)
        found = _PICTURES[path] = (stamp, None if image.isNull() else image)
    return found[1]


def _images(painter, images, to_page, corner_a, corner_b):
    """(0.207) A plan's background images on paper: each picture laid on its corners (turned, scaled), at its
    opacity, cut to the drawing's extent (corner_a, corner_b: painter units)."""
    x0, x1 = sorted((float(corner_a[0]), float(corner_b[0])))
    y0, y1 = sorted((float(corner_a[1]), float(corner_b[1])))
    for corners, path, opacity, *kept in images:
        picture = _picture(path)
        if picture is None or picture.width() == 0 or picture.height() == 0:
            continue
        lower_left, _lower_right, upper_right, upper_left = (to_page(c) for c in corners)
        across = (upper_right - upper_left) / picture.width()       # (a pixel to the right, on the page)
        down = (lower_left - upper_left) / picture.height()          # (a pixel down)
        target, own = painter, None
        if not pattern_paint.keeps_clip(painter):       # (0.369: an SVG keeps no clip — cut on a picture of its own,
            size = QtCore.QSize(max(1, math.ceil((x1 - x0) * IMAGE_SVG)),           # the drawing's extent, laid in)
                                max(1, math.ceil((y1 - y0) * IMAGE_SVG)))
            own = QtGui.QImage(size, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
            own.fill(QtCore.Qt.GlobalColor.transparent)
            target = QtGui.QPainter(own)
            target.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform)
            target.scale(IMAGE_SVG, IMAGE_SVG)
            target.translate(-x0, -y0)
        target.save()
        target.setClipRect(QtCore.QRectF(x0, y0, x1 - x0, y1 - y0), QtCore.Qt.ClipOperation.IntersectClip)
        if kept:                                        # (only the part kept, 0.209)
            part = QtGui.QPainterPath()
            part.addPolygon(_polygon(to_page(kept[0])))
            target.setClipPath(part, QtCore.Qt.ClipOperation.IntersectClip)
        target.setOpacity(float(opacity))
        target.setTransform(QtGui.QTransform(float(across[0]), float(across[1]), float(down[0]), float(down[1]),
                                             float(upper_left[0]), float(upper_left[1])), True)
        target.drawImage(QtCore.QPointF(0.0, 0.0), picture)
        target.restore()
        if own is not None:
            target.end()
            painter.drawImage(QtCore.QRectF(x0, y0, x1 - x0, y1 - y0), own)


CONTOUR_TEXT = 1.8         # mm on paper: a major contour line's height written along it (0.202)


def _contour_labels(painter, segs, height, to_page, scale, dpmm):
    """(0.202) A major contour line's height written along it, over it in a white halo, spread along it
    (terrain.label_spots), turned to read from below or from the right."""
    from ..core import terrain as terrain_geo
    from ..i18n import decimal_sep
    font = QtGui.QFont("Segoe UI")
    font.setPixelSize(max(1, round(CONTOUR_TEXT * dpmm)))
    path = QtGui.QPainterPath()
    path.addText(0.0, 0.0, font, terrain_geo.contour_text(height, decimal_sep()))
    middle = path.boundingRect().center()
    path.translate(-middle.x(), -middle.y())
    halo = QtGui.QPen(WHITE, 0.7 * dpmm)
    halo.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
    m = scale / 1000.0                                  # (m of the drawing in a mm of paper)
    for line in terrain_geo.chains(segs):
        for point, angle in terrain_geo.label_spots(line, terrain_geo.LABEL_EVERY * 1000.0 * m,
                                                    terrain_geo.LABEL_SHORTEST * 1000.0 * m):
            x, y = to_page(point)
            painter.save()
            painter.translate(float(x), float(y))
            painter.rotate(-angle)                       # (the page's y goes down)
            painter.strokePath(path, halo)
            painter.fillPath(path, CONTOUR)
            painter.restore()


SLOPE_ALPHA = 150          # the slope colours over the paper: a little see-through (0.201)
LEGEND_ROW, LEGEND_W, LEGEND_TEXT = 3.6, 30.0, 2.0      # mm on paper: the slope legend's rows, width, text


def _slope_fills(painter, fills, to_page):
    """(0.201) A plan's terrains coloured by slope: each band's shapes filled with its colour (no outline)."""
    from ..core.terrain import SLOPE_BANDS
    painter.setPen(QtCore.Qt.PenStyle.NoPen)
    for band, parts in fills:
        colour = QtGui.QColor(SLOPE_BANDS[band][1])
        colour.setAlpha(SLOPE_ALPHA)
        path = QtGui.QPainterPath()                        # (odd-even: the holes stay open)
        for outline, holes in parts:
            for ring in [outline] + list(holes):
                path.addPolygon(_polygon(to_page(ring)))
                path.closeSubpath()
        painter.fillPath(path, colour)


def slope_band_texts():
    """The slope bands' words for a legend ("até 5 %", "5 a 10 %"… "mais de 25 %"), in their order."""
    from ..core.terrain import SLOPE_BANDS
    from ..i18n import decimal_sep
    number = lambda v: "{:g}".format(v).replace(".", decimal_sep())        # noqa: E731
    out, low = [], None
    for limit, _colour in SLOPE_BANDS:
        if low is None:
            out.append(t("slope.up_to", b=number(limit)))
        elif limit == float("inf"):
            out.append(t("slope.over", a=number(low)))
        else:
            out.append(t("slope.between", a=number(low), b=number(limit)))
        low = limit
    return out


def _slope_legend(painter, corner, dpmm, bands):
    """(0.201) The slope colours' legend: a white box over the drawing's lower left corner (painter units), its
    title and a row per band — those in it."""
    from ..core.terrain import SLOPE_BANDS
    texts = slope_band_texts()
    rows = [k for k in range(len(SLOPE_BANDS)) if k in bands]
    height = LEGEND_ROW * (len(rows) + 1) + 1.0
    x0, y1 = float(corner[0]) / dpmm, float(corner[1]) / dpmm
    y0 = y1 - height
    frame = QtGui.QPen(QtGui.QColor("black"), 0.13 * dpmm)
    painter.setPen(frame)
    painter.setBrush(WHITE)
    painter.drawRect(QtCore.QRectF(x0 * dpmm, y0 * dpmm, LEGEND_W * dpmm, height * dpmm))
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    _text(painter, dpmm, x0 + 1.5, y0 + 0.5, LEGEND_W - 2.0, LEGEND_ROW, t("slope.legend"), LEGEND_TEXT / 0.3528,
          bold=True)
    for k, band in enumerate(rows):
        y = y0 + LEGEND_ROW * (k + 1) + 0.5
        colour = QtGui.QColor(SLOPE_BANDS[band][1])
        painter.setPen(frame)
        painter.setBrush(colour)
        painter.drawRect(QtCore.QRectF((x0 + 1.5) * dpmm, (y + 0.6) * dpmm, 4.0 * dpmm, (LEGEND_ROW - 1.2) * dpmm))
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        _text(painter, dpmm, x0 + 7.0, y, LEGEND_W - 8.0, LEGEND_ROW, texts[band], LEGEND_TEXT / 0.3528)


def _rooms(painter, rooms, to_page, dpmm):
    """A plan's rooms (0.125): in each, its name in capitals (bold), its number beside it, its area under them —
    their size on the paper, whatever the scale."""
    for at, name, number, area in rooms:
        x, y = (float(c) / dpmm for c in to_page(at))
        title = " ".join(w for w in ((name or "").upper(), number or "") if w)
        _text(painter, dpmm, x - 40.0, y - ROOM_TEXT * 1.7, 80.0, ROOM_TEXT * 1.6, title, ROOM_TEXT / 0.3528,
              bold=True, align=QtCore.Qt.AlignmentFlag.AlignHCenter)
        _text(painter, dpmm, x - 40.0, y + 0.2, 80.0, ROOM_TEXT * 1.4, area, ROOM_TEXT * 0.85 / 0.3528,
              align=QtCore.Qt.AlignmentFlag.AlignHCenter)


def _angles(painter, angles, to_page, scale, dpmm, pen_mm, style=None):
    """Angular dimensions (0.122) as drawn by hand: the arc round the corner with a 45° tick at each end (or the
    style's mark), its sides carried out to it (a gap from the object, a little beyond), the angle over its
    middle — (0.398) laid out by core/dim_layout, as its dimension type says."""
    from ..core import dim_layout
    layout = dim_layout.Layout()
    for v2, r, start, sweep, text, a2, b2 in angles:
        layout.extend(dim_layout.angle_layout(v2, r, start, sweep, text, a2, b2, style or {}, scale / 1000.0, pen_mm))
    paint_layout(painter, layout, to_page, dpmm)


def paint_layout(painter, layout, to_page, dpmm, paper="#ffffff", recolour=None):
    """(0.398) A core.dim_layout.Layout painted: its lines (each its pen, mm on paper, and colour), its filled marks,
    the boxes behind its texts (in the paper's colour), its texts (centred, turned, their height in the model). to_page:
    the view's 2D metres → painter units; dpmm: painter units per mm of paper; recolour: (colour, owner) → the colour
    to paint with (a sample's, a selection's)."""
    paint = recolour or (lambda colour, _owner: colour)
    groups = {}
    for a, b, pen_mm, colour, owner in layout.lines:
        groups.setdefault((round(float(pen_mm), 3), paint(colour, owner)), []).append((a, b))
    painter.save()
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    for (pen_mm, colour), segs in groups.items():
        pen = QtGui.QPen(QtGui.QColor(colour), max(pen_mm * dpmm, 0.5))
        pen.setCapStyle(QtCore.Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        seg = to_page(np.array(segs, dtype=float))
        painter.drawLines([QtCore.QLineF(a[0], a[1], b[0], b[1]) for a, b in seg])
    painter.setPen(QtCore.Qt.PenStyle.NoPen)
    for pts, colour, owner in layout.fills:
        painter.setBrush(QtGui.QColor(paint(colour, owner)))
        painter.drawPolygon(_polygon(to_page(np.asarray(pts, dtype=float))))
    painter.setBrush(QtGui.QColor(paper))
    for corners, _owner in layout.backs:
        painter.drawPolygon(_polygon(to_page(np.asarray(corners, dtype=float))))
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    o, x = to_page(np.array(((0.0, 0.0), (1.0, 0.0))))
    k = float(np.linalg.norm(x - o))                      # (painter units per metre of the model)
    flip = float((to_page(np.array((0.0, 1.0))) - o)[1]) > 0      # (the page's y down)
    for item in layout.texts:
        _layout_text(painter, item, to_page(np.asarray(item.at, dtype=float)), k, flip, paint(item.colour, item.owner))
    painter.restore()


def _layout_text(painter, item, centre, k, flip, colour):
    """(0.398) One of a Layout's texts: centred at `centre` (painter units), turned, `item.height` the letters' em."""
    from ..core.dim_layout import DEFAULT_FONT
    font = QtGui.QFont(item.font or DEFAULT_FONT)
    font.setPixelSize(100)
    font.setBold(bool(item.bold))
    font.setItalic(bool(item.italic))
    s = float(item.height) * k / 100.0
    if s <= 0:
        return
    painter.save()
    painter.translate(QtCore.QPointF(float(centre[0]), float(centre[1])))
    painter.rotate(-item.angle if flip else item.angle)
    painter.scale(s * float(item.width or 1.0), s)
    painter.setFont(font)
    painter.setPen(QtGui.QColor(colour))
    painter.drawText(QtCore.QRectF(-4000.0, -70.0, 8000.0, 140.0), QtCore.Qt.AlignmentFlag.AlignCenter, item.text)
    painter.restore()


def _head(painter, centre, tag, look, dpmm, pen, style=None):
    """A section's / an elevation's / (0.360) a detail's head: as its style draws it (graphic_styles «symbols»: a
    circle, a square or none; its arrow filled, open or none along `look`; its tag's height; its pen) — page units, y
    down; look None: no arrow."""
    from ..model import graphic_styles
    from ..model.symbols import head_shape
    style = style or graphic_styles.symbol(None, "section")
    c = np.asarray(centre, dtype=float)
    lines, filled, hollow, r = head_shape(style, look, dpmm)
    painter.setPen(pen(style["pen"]))
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    painter.drawLines([QtCore.QLineF(*(c + a), *(c + b)) for a, b in lines])
    for tri in hollow:
        painter.drawPolygon(_polygon([c + q for q in tri]))
    painter.setBrush(QtGui.QColor("black"))
    for tri in filled:
        painter.drawPolygon(_polygon([c + q for q in tri]))
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    half = max(r / dpmm, style["text"])
    _text(painter, dpmm, float(c[0]) / dpmm - half, float(c[1]) / dpmm - half, 2 * half, 2 * half, tag,
          style["text"] / 0.3528, bold=True, align=QtCore.Qt.AlignmentFlag.AlignHCenter)


def _dashed_pen(pen, style, dpmm):
    """(0.360) A symbol's line's pen: its width, dashed as its style says (symbols.DASHES, mm on paper)."""
    from ..model.symbols import DASHES
    line = pen(style["pen"])
    dashes = DASHES.get(style.get("line"))
    if dashes:
        width = max(line.widthF(), 1e-6)
        line.setDashPattern([d * dpmm / width for d in dashes])
        if style.get("line") == "dotted":              # (0.465: round dots)
            line.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    return line


def _marks(painter, marks, to_page, dpmm, pen, gstyle=None):
    """A plan's sections (their line, dashed, past the building, a head at each end) and elevations (a head out
    from the building), 0.121 — kept at the building's edges, put out from them here, in mm on the paper. (0.360) As
    the project's symbols' styles draw them."""
    from ..model import graphic_styles
    from ..model.symbols import ELEVATION_OUT, SECTION_OVER, line_pieces
    section, elevation = graphic_styles.symbol(gstyle, "section"), graphic_styles.symbol(gstyle, "elevation")
    flip = np.array((1.0, -1.0))                      # (plan directions to the page: y down)
    for m in marks:
        look = np.asarray(m.look, dtype=float) * flip
        if m.kind == "section":
            a, b = to_page(np.array([m.a, m.b]))
            d = (b - a) / max(float(np.linalg.norm(b - a)), 1e-9)
            if not getattr(m, "own", False):              # (0.358: its own ends, as dragged: not past them)
                a, b = a - d * SECTION_OVER * dpmm, b + d * SECTION_OVER * dpmm
            painter.setPen(_dashed_pen(pen, section, dpmm))
            pieces, _dashes = line_pieces(a, b, section, dpmm)
            painter.drawLines([QtCore.QLineF(p[0], p[1], q[0], q[1]) for p, q in pieces])
            for end, out in ((a, -d), (b, d)):
                _head(painter, end + out * section["size"] * dpmm, m.tag, look, dpmm, pen, section)
        else:
            _head(painter, to_page(m.a) - look * ELEVATION_OUT * dpmm, m.tag, look, dpmm, pen, elevation)


def _callouts(painter, callouts, to_page, dpmm, pen, gstyle=None):
    """Its detail views' callouts (0.133): a dashed rectangle with rounded corners round each, and its tag in a
    circle over its top right corner, a short line to it. (0.360) As the project's symbols' style draws them."""
    from ..model import graphic_styles
    style = graphic_styles.symbol(gstyle, "detail")
    line = _dashed_pen(pen, style, dpmm)
    for (x0, y0, x1, y1), tag in callouts:
        a, b = to_page(np.array(((x0, y1), (x1, y0))))       # (top left, bottom right on the page)
        rect = QtCore.QRectF(QtCore.QPointF(*a), QtCore.QPointF(*b)).normalized()
        painter.setPen(line)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 2.0 * dpmm, 2.0 * dpmm)
        r = style["size"] * dpmm
        centre = np.array((rect.right() + r * 1.6, rect.top() - r * 1.6))
        painter.setPen(pen(style["pen"]))
        painter.drawLine(QtCore.QPointF(rect.right(), rect.top()), QtCore.QPointF(centre[0] - r * 0.7,
                                                                                  centre[1] + r * 0.7))
        _head(painter, centre, tag, None, dpmm, pen, style)


def _levels(painter, drawing, to_page, dpmm, pen, gstyle=None):
    """A section's / elevation's levels (0.121): a dash-dot line across it at each storey's level, at its right
    end a black triangle on the line and the level with the storey's name over it. (0.360) As the project's symbols'
    style draws them: the line, the mark (a triangle, a quartered circle, none), their sizes."""
    from ..i18n import decimal_sep
    from ..model import graphic_styles
    from ..model.symbols import level_parts
    style = graphic_styles.symbol(gstyle, "level")
    lo, hi = drawing.bounds()
    # (0.462) as the Storeys panel sets it (model/symbols.level_parts) — worked out at 1:1 on the page: the line, the
    # marks and the words in mm, then each point put on the page
    p0, p1 = to_page(np.array(((0.0, 0.0), (1.0, 0.0))))
    mm = 1.0 / max(abs(float(p1[0] - p0[0])) / dpmm, 1e-12)        # (metres in the drawing per mm on the page)
    ink = QtGui.QColor(style.get("colour") or "#000000")
    line = _dashed_pen(pen, style, dpmm)
    line.setColor(ink)
    thin = pen(style["pen"])
    thin.setColor(ink)
    from ..model.symbols import LEVEL_OVER
    ends = getattr(drawing, "level_ends", None)        # (0.464: dragged in its view: its lines' ends)
    own = drawing.bounds(with_levels=False) if ends else (lo, hi)              # (the drawing's own span)
    x0, x1 = (ends[0] + LEVEL_OVER * mm, ends[1] - LEVEL_OVER * mm) if ends else (lo[0], hi[0])
    for z, name in drawing.levels:
        parts = level_parts(z, x0, x1, name, style, mm, decimal_sep(), model=(own[0][0], own[1][0]))
        page = lambda q: to_page(np.array([q]))[0]                   # noqa: E731
        painter.setPen(line)
        painter.drawLines([QtCore.QLineF(*page(a), *page(b)) for a, b in parts.pieces])
        painter.setPen(thin)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        if parts.outline:
            painter.drawLines([QtCore.QLineF(*page(a), *page(b)) for a, b in parts.outline])
        painter.setBrush(ink)
        for poly in parts.filled:
            painter.drawPolygon(_polygon([page(q) for q in poly]))
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.setPen(ink)
        for at, text, align, size in parts.texts:
            x, y = (float(c) / dpmm for c in page(at))
            vertical, side = align.split("-")
            left = x - 80.0 if side == "right" else x
            top = y - size * 1.4 if vertical == "bottom" else y          # (its box over the line, or under it)
            _text(painter, dpmm, left, top, 80.0, size * 1.4, text, size / 0.3528,
                  align=QtCore.Qt.AlignmentFlag.AlignRight if side == "right" else QtCore.Qt.AlignmentFlag.AlignLeft,
                  colour=ink.name())


def _north(painter, corner, dpmm, pen):
    """A plan's north arrow (0.121): beyond its top right corner, a circle with the arrow up (the project's
    north, +Y) and an N over it."""
    from ..model.symbols import NORTH
    r = NORTH * dpmm
    c = np.asarray(corner, dtype=float) + np.array((r * 2.2, r * 1.2))
    painter.setPen(pen(CUT_PEN * 0.6))
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QtCore.QPointF(float(c[0]), float(c[1])), r, r)
    painter.setBrush(QtGui.QColor("black"))           # (a narrow arrow: its tip up, its foot in the circle)
    painter.drawPolygon(_polygon([c + np.array(q) * r for q in ((0.0, -0.92), (0.42, 0.62), (0.0, 0.35),
                                                                 (-0.42, 0.62))]))
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    _text(painter, dpmm, float(c[0]) / dpmm - NORTH, float(c[1]) / dpmm - NORTH * 2.6, 2 * NORTH, NORTH * 1.4,
          "N", NORTH * 0.9 / 0.3528, bold=True, align=QtCore.Qt.AlignmentFlag.AlignHCenter)


def _dimensions(painter, dims, to_page, scale, dpmm, pen_mm, style=None):
    """Dimensions as drawn by hand: extension lines (a gap from the object, a little beyond the
    line), the line with 45° ticks at its ends (or the style's mark, 0.124), the value over its
    middle, readable, as high as the style says — (0.398) each string laid out by core/dim_layout as its dimension
    type says (the same as on screen, in SVG and in DXF)."""
    from ..core import dim_layout
    paint_layout(painter, dim_layout.of_drawing(dims, style or {}, scale / 1000.0, pen_mm), to_page, dpmm)


def _polygon(ring):
    return QtGui.QPolygonF([QtCore.QPointF(float(x), float(y)) for x, y in ring])


def _faces(painter, faces, to_page, dpmm):
    """(0.315) The faces of a drawing painted, in order (the farthest first: the nearer cover them): each in its
    colour — the opaque ones with a hair of the same colour round them, so that no seam shows between two triangles
    of a face."""
    painter.save()
    seam = max(0.1 * dpmm, 1.0)
    for ring, rgb, alpha, _depth in faces:
        colour = QtGui.QColor.fromRgbF(*rgb, alpha)
        painter.setBrush(colour)
        if alpha >= 0.999:
            painter.setPen(QtGui.QPen(colour, seam))
        else:
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
        if isinstance(ring, list):                  # (0.316: a shadow, maybe with holes — light through a gap)
            path = QtGui.QPainterPath()
            path.setFillRule(QtCore.Qt.FillRule.OddEvenFill)
            for part in ring:
                path.addPolygon(_polygon(to_page(np.asarray(part, dtype=float))))
                path.closeSubpath()
            painter.drawPath(path)
        else:
            painter.drawPolygon(_polygon(to_page(np.asarray(ring, dtype=float))))
    painter.restore()


def _paths(drawing):
    """The cut of a drawing as Qt paths in metres (y up), made once per drawing: {hatch: fill},
    the seams between layers, and the outline of all that is cut joined into one (Qt's union)."""
    made = getattr(drawing, "_qt_paths", None)
    if made is not None:
        return made
    fills = drawing.fills or list(zip(drawing.cut, list(drawing.hatch) + [None] * len(drawing.cut)))
    by_hatch = {}
    for ring, hatch in fills:
        path = by_hatch.get(hatch)
        if path is None:
            path = by_hatch[hatch] = QtGui.QPainterPath()
            path.setFillRule(QtCore.Qt.FillRule.WindingFill)
        path.addPolygon(_polygon(ring))
        path.closeSubpath()
    seams = QtGui.QPainterPath()
    joined = getattr(drawing, "outline", None) is not None      # (0.320: each material's parts already one)
    if len(by_hatch) > 1 or (not joined and len(fills) > len(drawing.cut)):
        # the thin line only where the material changes: each material's parts joined first, so
        # the plaster of two walls that meet, or their blocks, run on without a line between them
        for path in by_hatch.values():
            seams.addPath(path if joined else path.simplified())
    outline = QtGui.QPainterPath()
    outline.setFillRule(QtCore.Qt.FillRule.WindingFill)
    for ring in drawing.outline if joined else drawing.cut:
        outline.addPolygon(_polygon(ring))
        outline.closeSubpath()
    made = drawing._qt_paths = (by_hatch, seams, outline if joined else outline.simplified())
    return made


def _hatch(painter, path, angles, spacing, pen):
    """Parallel lines `spacing` apart (painter units) at each angle, inside `path` only."""
    box = path.boundingRect()
    if box.isEmpty() or spacing <= 0:
        return
    painter.save()
    painter.setPen(pen)
    c = box.center()
    half = (box.width() + box.height()) / 2 + spacing                # covers the box at any angle
    lines = []
    for a in angles:
        d = QtCore.QPointF(np.cos(np.radians(a)), -np.sin(np.radians(a)))     # along the lines (y down)
        n = QtCore.QPointF(-d.y(), d.x())                                    # across them
        for k in range(-int(half / spacing), int(half / spacing) + 1):
            p = c + n * (k * spacing)
            lines.append(QtCore.QLineF(p - d * half, p + d * half))
    if pattern_paint.keeps_clip(painter):
        painter.setClipPath(path)
    else:                                           # (0.369: an SVG — cut to the path here, in geometry)
        kept = pattern_paint.clip_segments(path, [((ln.x1(), ln.y1()), (ln.x2(), ln.y2())) for ln in lines])
        lines = [QtCore.QLineF(a[0], a[1], b[0], b[1]) for a, b in kept]
    if lines:
        painter.drawLines(lines)
    painter.restore()


def _text(painter, dpmm, x, y, w, h, text, size, bold=False, align=QtCore.Qt.AlignmentFlag.AlignLeft,
          colour="black", elide=False, italic=False):
    """size in points, on the paper (so it zooms with the sheet on screen). elide: cut short
    with "…" if wider than w."""
    font = QtGui.QFont("Segoe UI")
    font.setPixelSize(max(1, round(size * 0.3528 * dpmm)))
    font.setBold(bold)
    font.setItalic(italic)
    painter.setFont(font)
    painter.setPen(QtGui.QColor(colour))
    if elide:
        text = painter.fontMetrics().elidedText(text, QtCore.Qt.TextElideMode.ElideRight, int(w * dpmm))
    painter.drawText(QtCore.QRectF(x * dpmm, y * dpmm, w * dpmm, h * dpmm),
                     align | QtCore.Qt.AlignmentFlag.AlignVCenter, text)


def sheet_texts(block, placed):
    """What a sheet's title block shows: its texts (sheets.title_texts) with the scales of its views and today's date;
    its number with its last revision's code."""
    scales = sorted({frame.scale for d, frame, _l in placed if not hasattr(d, "paper_size")})
    texts = dict(block, scale=" · ".join("1:{}".format(s) for s in scales),
                 date=datetime.date.today().strftime("%d/%m/%Y"))
    revisions = block.get("revisions") or []
    if revisions and revisions[-1].get("code") and texts.get("number"):    # (its last revision by its number)
        texts["number"] = "{} · {}".format(texts["number"], revisions[-1]["code"])
    return texts


def paint_sheet(painter, dpmm, size, block, placed, credit="", template="full", imports=(), title=True):
    """A sheet: its border, the views placed = [(drawing, Frame, label)], the title block (its
    texts: sheets.title_texts; the scale and the date are added here; 0.129: its template). size:
    (w, h) mm of the paper; dpmm: painter units per mm. credit: small, under the title block. (0.472) imports: the
    drawings from outside put on it (sheets.SheetImport). (0.473) title=False: the company's drawing left out (its
    editor draws it over)."""
    paint_imports(painter, dpmm, imports)
    for drawing, frame, label in placed:
        if hasattr(drawing, "paper_size"):               # (a schedule's table, 0.132)
            paint_table(painter, drawing, frame.centre, dpmm, label)
        else:
            paint_drawing(painter, drawing, frame.scale, frame.centre, dpmm, label)
    _title_block(painter, dpmm, size[0], size[1], sheet_texts(block, placed), credit, template, title)


def _writer(path, project, title):
    writer = QtGui.QPdfWriter(path)
    writer.setResolution(RESOLUTION)
    writer.setTitle("{} — {}".format(project, title))
    writer.setCreator("ArqSynth BIM")
    return writer


def _set_paper(writer, size):
    """The page of a sheet (w, h mm): lying down, or (0.470) standing up."""
    w, h = size
    page = QtGui.QPageSize(QtCore.QSizeF(min(w, h), max(w, h)), QtGui.QPageSize.Unit.Millimeter)  # portrait sizes
    turn = QtGui.QPageLayout.Orientation.Landscape if w > h else QtGui.QPageLayout.Orientation.Portrait
    writer.setPageLayout(QtGui.QPageLayout(page, turn, QtCore.QMarginsF(0, 0, 0, 0),
                                           QtGui.QPageLayout.Unit.Millimeter))


def write(path, drawing, block, credit=""):
    """One view on A3 at the largest usual scale that fits. block: the title block's texts
    (sheets.title_texts). Returns the scale (N of 1:N)."""
    size = sheets_model.PAPERS["A3"]
    left, top, width, height = sheets_model.drawing_area("A3")
    scale = fit_scale(drawing, width, height - LABEL_H)
    frame = sheets_model.Frame(scale, (left + width / 2, top + (height - LABEL_H) / 2), 0, 0)
    writer = _writer(path, block["project"], drawing.title)
    _set_paper(writer, size)
    painter = QtGui.QPainter(writer)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    paint_sheet(painter, RESOLUTION / 25.4, size, block, [(drawing, frame, None)], credit)
    painter.end()
    return scale


def write_sheets(path, pages, credit=""):
    """Several sheets, one page each. pages: [(sheets.Sheet, [(drawing, Frame, label)], title
    block texts)]."""
    project = pages[0][2]["project"]
    writer = _writer(path, project, pages[0][0].name if len(pages) == 1 else project)
    _set_paper(writer, pages[0][0].size())
    painter = QtGui.QPainter(writer)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    for k, (sheet, placed, block) in enumerate(pages):
        if k:
            _set_paper(writer, sheet.size())
            writer.newPage()
        paint_sheet(painter, RESOLUTION / 25.4, sheet.size(), block, placed, credit, sheet.template,
                    imports=getattr(sheet, "imports", ()))
    painter.end()


SVG_MARGIN = 6.0          # mm of white round a view drawn alone in SVG
PROBE_MM = 2.0             # px a mm of the small picture that measures what a view paints…
PROBE_PAD = 80.0           # …and the mm round its own lines there (its marks and dimensions stand out of them)


def _painted_box(drawing, scale):
    """(x0, y0, x1, y1) mm round what paint_drawing paints of a drawing at 1:scale centred at (0, 0) — its elevation
    marks and dimensions, beyond its own lines, too: read off a small picture of it."""
    lo, hi = drawing.bounds()
    w = float(hi[0] - lo[0]) * 1000.0 / scale + 2.0 * PROBE_PAD
    h = float(hi[1] - lo[1]) * 1000.0 / scale + 2.0 * PROBE_PAD
    image = QtGui.QImage(math.ceil(w * PROBE_MM), math.ceil(h * PROBE_MM), QtGui.QImage.Format.Format_RGB32)
    image.fill(WHITE)
    painter = QtGui.QPainter(image)
    paint_drawing(painter, drawing, scale, (w / 2.0, h / 2.0), PROBE_MM)
    painter.end()
    pixels = np.frombuffer(image.constBits(), dtype=np.uint8).reshape(image.height(), image.bytesPerLine())
    pixels = pixels[:, :image.width() * 4].reshape(image.height(), image.width(), 4)[..., :3]
    rows, cols = np.nonzero((pixels < 250).any(axis=-1))
    if not len(rows):
        return -w / 2.0 + PROBE_PAD, -h / 2.0 + PROBE_PAD, w / 2.0 - PROBE_PAD, h / 2.0 - PROBE_PAD
    return (cols.min() / PROBE_MM - w / 2.0, rows.min() / PROBE_MM - h / 2.0,
            (cols.max() + 1) / PROBE_MM - w / 2.0, (rows.max() + 1) / PROBE_MM - h / 2.0)


def write_svg(path, drawing, scale, credit=""):
    """(0.369) One view alone as an SVG drawing at 1:scale, in millimetres — Inkscape, Illustrator and the browsers
    open it at its true size —, painted as on the sheets (paint_drawing) on white paper as big as what it paints
    (its marks and dimensions too) with a margin round it; lines, fills and texts stay vectors. Returns its (w, h)
    in mm."""
    from PySide6 import QtSvg
    x0, y0, x1, y1 = _painted_box(drawing, scale)
    w, h = x1 - x0 + 2.0 * SVG_MARGIN, y1 - y0 + 2.0 * SVG_MARGIN
    centre = (SVG_MARGIN - x0, SVG_MARGIN - y0)            # (where the drawing's middle falls on that paper)
    dpmm = 96.0 / 25.4
    target = QtSvg.QSvgGenerator()
    target.setFileName(path)
    target.setSize(QtCore.QSize(round(w * dpmm), round(h * dpmm)))
    target.setViewBox(QtCore.QRectF(0.0, 0.0, w * dpmm, h * dpmm))
    target.setResolution(96)
    target.setTitle(drawing.title or "")
    target.setDescription(credit or "ArqSynth BIM")
    painter = QtGui.QPainter(target)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    painter.fillRect(QtCore.QRectF(0.0, 0.0, w * dpmm, h * dpmm), WHITE)
    paint_drawing(painter, drawing, scale, centre, dpmm)
    painter.end()
    return w, h


def file_name(number, name):
    """A sheet's file name (0.128): "A-01 Planta — Térreo", with what a file name cannot have taken out."""
    text = " ".join(p for p in (str(number or "").strip(), str(name or "").strip()) if p) or "folha"
    return re.sub(r'[\\/:*?"<>|]+', "-", text)


def write_images(folder, pages, fmt="png", dpi=150, credit=""):
    """Each sheet to a file of its own in `folder` (0.128): a PNG picture at `dpi`, or an SVG drawing (lines
    and fills stay vectors). pages as write_sheets'. Returns the paths written."""
    from PySide6 import QtSvg
    out = []
    for sheet, placed, block in pages:
        w, h = sheet.size()
        path = os.path.join(folder, file_name(block.get("number"), sheet.name) + "." + fmt)
        if fmt == "svg":
            dpmm = 96.0 / 25.4
            target = QtSvg.QSvgGenerator()
            target.setFileName(path)
            target.setSize(QtCore.QSize(round(w * dpmm), round(h * dpmm)))
            target.setViewBox(QtCore.QRectF(0.0, 0.0, w * dpmm, h * dpmm))
            target.setResolution(96)
            target.setTitle(sheet.name)
            target.setDescription(credit or "ArqSynth BIM")
        else:
            dpmm = dpi / 25.4
            target = QtGui.QImage(round(w * dpmm), round(h * dpmm), QtGui.QImage.Format.Format_RGB32)
            target.setDotsPerMeterX(round(dpi / 0.0254))
            target.setDotsPerMeterY(round(dpi / 0.0254))
            target.fill(WHITE)
        painter = QtGui.QPainter(target)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        if fmt == "svg":
            painter.fillRect(QtCore.QRectF(0.0, 0.0, w * dpmm, h * dpmm), WHITE)
        paint_sheet(painter, dpmm, (w, h), block, placed, credit, sheet.template, imports=getattr(sheet, "imports", ()))
        painter.end()
        if fmt != "svg":
            target.save(path)
        out.append(path)
    return out


def print_sheets(printer, pages, credit=""):
    """Sheets on a printer (0.128: QPrinter, as its dialog left it), a page each, on their paper: landscape,
    from the paper's corner. pages as write_sheets'."""
    printer.setFullPage(True)
    painter = None
    for k, (sheet, placed, block) in enumerate(pages):
        _set_paper(printer, sheet.size())
        if painter is None:
            painter = QtGui.QPainter(printer)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        else:
            printer.newPage()
        paint_sheet(painter, printer.resolution() / 25.4, sheet.size(), block, placed, credit, sheet.template,
                    imports=getattr(sheet, "imports", ()))
    if painter is not None:
        painter.end()


CELL_LABEL = 4.5           # points: the small grey name of each box ("Obra", "Escala"…)


def _title_block(painter, dpmm, width, height, texts, credit, template="full", title=True):
    """The border of the sheet and, bottom right inside it, the title block of its template (sheets.CELLS):
    boxes, each with its name small at the top and its text under it (cut short with "…" if it does not fit);
    a strip's column down the right side; (0.473) the company's own drawing («custom»: sheets.company(); title=False:
    left out, for its editor)."""
    x0, y0, bw, bh = sheets_model.title_box((width, height), template)
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    painter.setPen(QtGui.QPen(QtGui.QColor("black"), 0.35 * dpmm))
    painter.drawRect(QtCore.QRectF(MARGIN * dpmm, MARGIN * dpmm, (width - 2 * MARGIN) * dpmm,
                                   (height - 2 * MARGIN) * dpmm))                 # the sheet's border
    if template == "custom":
        if title:
            paint_drawn(painter, dpmm, width - MARGIN, height - MARGIN, sheets_model.company()["items"], texts)
            if bw and bh and not sheets_model.block_beside((width, height), template):
                _over_title_block(painter, dpmm, x0, y0, texts, bw)
    else:
        if template == "strip":                                                    # (its column, 0.129)
            painter.drawLine(QtCore.QPointF(x0 * dpmm, MARGIN * dpmm),
                             QtCore.QPointF(x0 * dpmm, (height - MARGIN) * dpmm))
        painter.drawRect(QtCore.QRectF(x0 * dpmm, y0 * dpmm, bw * dpmm, bh * dpmm))
        label_h = CELL_LABEL * 0.3528 * 1.3                                       # points -> mm
        for x, y, w, h, key, size, bold in sheets_model.cells_of(template):
            painter.setPen(QtGui.QPen(QtGui.QColor("black"), 0.18 * dpmm))
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawRect(QtCore.QRectF((x0 + x) * dpmm, (y0 + y) * dpmm, w * dpmm, h * dpmm))
            _text(painter, dpmm, x0 + x + 1.2, y0 + y + 0.5, w - 2.4, label_h, t("tb." + key), CELL_LABEL,
                  colour="#6b6b6b")
            _text(painter, dpmm, x0 + x + 1.2, y0 + y + 0.5 + label_h, w - 2.4, h - 0.8 - label_h,
                  texts.get(key, ""), size, bold, elide=True)
        _over_title_block(painter, dpmm, x0, y0, texts, bw)
    if credit:
        _text(painter, dpmm, x0 - 60.0, height - MARGIN + 0.8, bw + 60.0, 2.6, credit, 5, colour="#6b6b6b",
              align=QtCore.Qt.AlignmentFlag.AlignRight)


ALIGN = {"left": QtCore.Qt.AlignmentFlag.AlignLeft, "center": QtCore.Qt.AlignmentFlag.AlignHCenter,
         "right": QtCore.Qt.AlignmentFlag.AlignRight}
PLACEHOLDER = "#8a94a3"           # (0.473) an empty field's name, a picture's place — only while the title block is drawn


def field_label(field):
    """(0.473) A field's name («Obra», «Escala»…; a project's own field: its own)."""
    if field.startswith(sheets_model.EXTRA_FIELD):
        return field[len(sheets_model.EXTRA_FIELD):]
    return t("tb." + field)


def item_box(item, cx, cy):
    """(0.473) (x, y, w, h) mm on the paper of an item of the company's drawing (its points from the corner cx, cy)."""
    (ax, ay), (bx, by) = item["pts"]
    return cx + min(ax, bx), cy + min(ay, by), abs(bx - ax), abs(by - ay)


def paint_drawn(painter, dpmm, cx, cy, items, texts, placeholders=False):
    """(0.473) The company's title block as drawn (sheets.clean_item's items, from the border's inside corner cx, cy
    mm): its lines and rectangles at their thickness, its texts, its fields filled in with the sheet's texts, its
    pictures in their boxes. placeholders: an empty field shows its name, a picture without a file its place (while
    the title block is drawn)."""
    for item in items:
        kind = item["kind"]
        x, y, w, h = item_box(item, cx, cy)
        if kind == "line":
            (ax, ay), (bx, by) = item["pts"]
            painter.setPen(QtGui.QPen(QtGui.QColor("black"), item["pen"] * dpmm))
            painter.drawLine(QtCore.QPointF((cx + ax) * dpmm, (cy + ay) * dpmm),
                             QtCore.QPointF((cx + bx) * dpmm, (cy + by) * dpmm))
        elif kind == "rect":
            pen = QtGui.QPen(QtGui.QColor("black"), item["pen"] * dpmm)
            pen.setJoinStyle(QtCore.Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)
            painter.setBrush(QtGui.QColor(item["fill"]) if item["fill"] else QtCore.Qt.BrushStyle.NoBrush)
            painter.drawRect(QtCore.QRectF(x * dpmm, y * dpmm, w * dpmm, h * dpmm))
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        elif kind == "image":
            if picture_of(item["path"]) is not None:
                _fit_picture(painter, dpmm, item["path"], x, y, w, h)
            elif placeholders:
                pen = QtGui.QPen(QtGui.QColor(PLACEHOLDER), 1.0, QtCore.Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                box = QtCore.QRectF(x * dpmm, y * dpmm, w * dpmm, h * dpmm)
                painter.drawRect(box)
                painter.drawLine(box.topLeft(), box.bottomRight())
                painter.drawLine(box.topRight(), box.bottomLeft())
                _box_text(painter, dpmm, x, y, w, h, t("tbe.image"), 6.0, colour=PLACEHOLDER, align="center")
        else:
            words = item["text"] if kind == "text" else sheets_model.field_text(texts, item["field"])
            colour, italic = item["colour"], False
            if not words and placeholders:
                words = "‹{}›".format(t("tbe.text_new") if kind == "text" else field_label(item["field"]))
                colour, italic = PLACEHOLDER, True
            _box_text(painter, dpmm, x, y, w, h, words, item["size"], item["bold"], item["align"], colour, italic)


def _box_text(painter, dpmm, x, y, w, h, text, size, bold=False, align="left", colour="black", italic=False):
    """(0.473) A text in its box (x, y, w, h mm): one line in the box's middle (cut short with «…» when longer),
    several from its top."""
    if not text:
        return
    font = QtGui.QFont("Segoe UI")
    font.setPixelSize(max(1, round(size * 0.3528 * dpmm)))
    font.setBold(bold)
    font.setItalic(italic)
    painter.setFont(font)
    painter.setPen(QtGui.QColor(colour))
    flags = ALIGN.get(align, ALIGN["left"])
    rect = QtCore.QRectF(x * dpmm, y * dpmm, max(w, 0.5) * dpmm, max(h, 0.5) * dpmm)
    if "\n" in text:
        painter.drawText(rect, flags | QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.TextFlag.TextWordWrap, text)
        return
    text = painter.fontMetrics().elidedText(text, QtCore.Qt.TextElideMode.ElideRight, int(rect.width()) + 1)
    painter.drawText(rect, flags | QtCore.Qt.AlignmentFlag.AlignVCenter, text)


_SHEET_PICTURES = {}            # (0.472) path -> (modified time, QImage or None): logos, pictures put on sheets


def picture_of(path):
    """(0.472) A picture file, read once while it is unchanged (None when it cannot be read)."""
    try:
        stamp = os.path.getmtime(path)
    except (OSError, TypeError, ValueError):
        return None
    found = _SHEET_PICTURES.get(path)
    if found is None or found[0] != stamp:
        image = QtGui.QImage(path)
        found = _SHEET_PICTURES[path] = (stamp, None if image.isNull() else image)
    return found[1]


def _fit_picture(painter, dpmm, path, x, y, w, h):
    """(0.472) A picture fitted in the box (x, y, w, h mm), its proportions kept, in its middle."""
    image = picture_of(path) if path else None
    if image is None or w <= 0 or h <= 0:
        return
    k = min(w / image.width(), h / image.height())
    pw, ph = image.width() * k, image.height() * k
    painter.drawImage(QtCore.QRectF((x + (w - pw) / 2) * dpmm, (y + (h - ph) / 2) * dpmm, pw * dpmm, ph * dpmm), image)


def import_size(item):
    """(0.472) (w, h) mm a drawing put on a sheet takes (sheets.SheetImport), or None when its file cannot be read: a
    picture or an SVG `width` across in its proportions; a CAD drawing its extent at its scale."""
    if item.kind == "image":
        image = picture_of(item.path)
        return (item.width, item.width * image.height() / image.width()) if image is not None else None
    if item.kind == "svg":
        from PySide6 import QtSvg
        renderer = QtSvg.QSvgRenderer(item.path)
        size = renderer.defaultSize() if renderer.isValid() else None
        return (item.width, item.width * size.height() / max(size.width(), 1)) if size and size.width() > 0 else None
    found = cad_lines(item.path)
    if found is None:
        return None
    lo, hi = found[2]
    k = item.units * 1000.0 / max(int(item.scale), 1)
    return float(hi[0] - lo[0]) * k, float(hi[1] - lo[1]) * k


def cad_lines(path):
    """(0.472) A DWG's / DXF's (segments (K, 2, 2), texts [(point, words, height)], (lo, hi)) in drawing units, or
    None."""
    from ..model import cad_links
    found = cad_links.drawing_of(path)
    if found is None:
        return None
    drawing, raw = found
    segs = [s for s in raw.values() if len(s)]
    segs = np.concatenate(segs) if segs else np.zeros((0, 2, 2))
    words = [(np.asarray(e.points[0], dtype=float), e.text, float(e.radius or 0.0))
             for e in drawing.entities if e.kind == "text" and e.text]
    pts = [segs.reshape(-1, 2)] + ([np.array([p for p, _w, _h in words])] if words else [])
    pts = np.concatenate(pts) if any(len(p) for p in pts) else np.zeros((0, 2))
    if not len(pts):
        return None
    return segs, words, (pts.min(axis=0), pts.max(axis=0))


def paint_imports(painter, dpmm, imports):
    """(0.472) The drawings from outside put on a sheet (sheets.SheetImport), each round its centre: a picture, an
    SVG, a DWG / DXF's lines and texts at its scale (thin, black)."""
    for item in imports or ():
        size = import_size(item)
        if size is None:
            continue
        w, h = size
        left, top = item.at[0] - w / 2, item.at[1] - h / 2
        if item.kind == "image":
            _fit_picture(painter, dpmm, item.path, left, top, w, h)
        elif item.kind == "svg":
            from PySide6 import QtSvg
            QtSvg.QSvgRenderer(item.path).render(painter, QtCore.QRectF(left * dpmm, top * dpmm, w * dpmm, h * dpmm))
        else:
            segs, words, (lo, hi) = cad_lines(item.path)
            k = item.units * 1000.0 / max(int(item.scale), 1)          # drawing units -> mm on the paper
            mid = (lo + hi) / 2

            def at(p):
                return QtCore.QPointF((item.at[0] + (p[0] - mid[0]) * k) * dpmm, (item.at[1] - (p[1] - mid[1]) * k) * dpmm)

            painter.setPen(QtGui.QPen(QtGui.QColor("black"), max(0.13 * dpmm, 0.5)))
            painter.drawLines([QtCore.QLineF(at(a), at(b)) for a, b in segs])
            for p, text, height in words:
                size_mm = max(height * k, 1.0)
                font = QtGui.QFont("Segoe UI")
                font.setPixelSize(max(1, round(size_mm * dpmm)))
                painter.setFont(font)
                painter.setPen(QtGui.QColor("black"))
                painter.drawText(at(p), text)


def _over_title_block(painter, dpmm, x0, y0, texts, width=TITLE_W):
    """(0.127) Over the title block, as wide as it: the sheet's revisions (a header next to it, the oldest over
    it, the newest at the top) and, over them, the project's own fields (label: text)."""
    row = sheets_model.REVISION_ROW
    thin = QtGui.QPen(QtGui.QColor("black"), 0.18 * dpmm)
    top = y0
    revisions = texts.get("revisions") or []
    code_w, date_w = (14.0, 24.0) if width >= 100 else (9.0, 17.0)
    if revisions:
        columns = ((0.0, code_w, "code"), (code_w, date_w, "date"),
                   (code_w + date_w, width - code_w - date_w, "text"))
        lines = [{"code": t("tb.rev_code"), "date": t("tb.rev_date"), "text": t("tb.rev_text")}] + list(revisions)
        for k, line in enumerate(lines):
            y = y0 - (k + 1) * row
            for x, w, key in columns:
                painter.setPen(thin)
                painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                painter.drawRect(QtCore.QRectF((x0 + x) * dpmm, y * dpmm, w * dpmm, row * dpmm))
                _text(painter, dpmm, x0 + x + 1.0, y + 0.3, w - 2.0, row - 0.6, line.get(key, ""),
                      CELL_LABEL if k == 0 else 6, bold=False, colour="#6b6b6b" if k == 0 else "black", elide=True)
        top = y0 - len(lines) * row
    for k, (label, value) in enumerate(texts.get(sheets_model.EXTRA_KEY) or []):
        y = top - (k + 1) * row
        label_w = min(40.0, width * 0.4)
        for x, w, text, grey in ((0.0, label_w, label, True), (label_w, width - label_w, value, False)):
            painter.setPen(thin)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawRect(QtCore.QRectF((x0 + x) * dpmm, y * dpmm, w * dpmm, row * dpmm))
            _text(painter, dpmm, x0 + x + 1.0, y + 0.3, w - 2.0, row - 0.6, text, 5.5 if grey else 6.5,
                  colour="#6b6b6b" if grey else "black", elide=True)


def page_count(path):
    """How many pages a PDF written here has (used by tests)."""
    with open(path, "rb") as f:
        return len(re.findall(rb"/Type\s*/Page(?![s\w])", f.read()))
