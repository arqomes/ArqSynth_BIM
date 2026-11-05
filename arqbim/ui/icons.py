"""Toolbar icons drawn in code (no image files to ship or license)."""

import numpy as np
from PySide6 import QtCore, QtGui

from . import theme

SIZE = 32
INK = QtGui.QColor("#222")
BLUE = QtGui.QColor("#1f5fd6")
FILL = QtGui.QColor("#ebe7df")


def _canvas():
    pm = QtGui.QPixmap(SIZE, SIZE)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    return pm, p


def _pen(color, width=2.0):
    pen = QtGui.QPen(color, width)
    pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
    pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    return pen


def select_icon():
    pm, p = _canvas()
    arrow = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in
                             [(9, 4), (9, 26), (14, 21), (18, 29), (21, 27.5), (17, 19.5), (24, 19.5)]])
    p.setPen(_pen(INK, 1.8))
    p.setBrush(QtGui.QColor("white"))
    p.drawPolygon(arrow)
    p.end()
    return theme.icon(pm)


def rectangle_icon():
    pm, p = _canvas()
    p.setPen(_pen(INK, 2.2))
    p.setBrush(FILL)
    p.drawRect(QtCore.QRectF(5, 8, 22, 16))
    p.setPen(_pen(BLUE, 1))
    p.setBrush(BLUE)
    p.drawEllipse(QtCore.QPointF(5, 24), 2.6, 2.6)
    p.drawEllipse(QtCore.QPointF(27, 8), 2.6, 2.6)
    p.end()
    return theme.icon(pm)


def line_icon():
    """Line: a pencil drawing a segment between two points."""
    pm, p = _canvas()
    for color, width in ((FILL, 5.0), (INK, 2.2)):         # light halo: visible on dark toolbars too
        p.setPen(_pen(color, width))
        p.drawLine(QtCore.QPointF(5, 27), QtCore.QPointF(20, 12))
    p.setPen(_pen(BLUE, 1))
    p.setBrush(BLUE)
    p.drawEllipse(QtCore.QPointF(5, 27), 2.6, 2.6)
    p.setPen(_pen(INK, 1.4))
    p.setBrush(QtGui.QColor("#f2c94c"))
    pencil = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(20, 12), (26, 4), (30, 8), (23, 15)]])
    p.drawPolygon(pencil)
    p.setBrush(INK)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(20, 12), (21.5, 10.2), (23, 15)]]))
    p.end()
    return theme.icon(pm)


def tape_icon():
    """Tape measure: the case with its blade, and a dashed guide line."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.6))
    p.setBrush(QtGui.QColor("#f2c94c"))
    p.drawRoundedRect(QtCore.QRectF(3, 10, 14, 14), 3, 3)
    p.setBrush(QtGui.QColor("#ffffff"))
    p.drawEllipse(QtCore.QPointF(10, 17), 3, 3)
    p.setBrush(QtGui.QColor("#e8e3d6"))
    p.drawRect(QtCore.QRectF(17, 20, 12, 4))
    for x in (20, 23, 26):
        p.drawLine(QtCore.QPointF(x, 20), QtCore.QPointF(x, 22))
    pen = _pen(QtGui.QColor("#9a9a9a"), 1.6)
    pen.setDashPattern([3, 2])
    p.setPen(pen)
    p.drawLine(QtCore.QPointF(3, 5), QtCore.QPointF(29, 5))
    p.end()
    return theme.icon(pm)


def move_icon():
    """Move: four arrows."""
    pm, p = _canvas()
    p.setPen(_pen(BLUE, 2.4))
    c = 16
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        tip = QtCore.QPointF(c + dx * 12, c + dy * 12)
        p.drawLine(QtCore.QPointF(c, c), tip)
        side = QtCore.QPointF(dy * 4, dx * 4)
        back = QtCore.QPointF(c + dx * 8, c + dy * 8)
        p.drawLine(tip, back + side)
        p.drawLine(tip, back - side)
    p.end()
    return theme.icon(pm)


def rotate_icon():
    """Rotate: a circular arrow around a centre point."""
    pm, p = _canvas()
    p.setPen(_pen(BLUE, 2.4))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawArc(QtCore.QRectF(5, 5, 22, 22), 30 * 16, 270 * 16)
    tip = QtCore.QPointF(25.5, 10.5)
    p.drawLine(tip, QtCore.QPointF(26.5, 4.5))
    p.drawLine(tip, QtCore.QPointF(20.0, 9.0))
    p.setPen(_pen(FILL, 1))
    p.setBrush(FILL)
    p.drawEllipse(QtCore.QPointF(16, 16), 2.4, 2.4)
    p.end()
    return theme.icon(pm)


def push_pull_icon():
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.8))
    p.setBrush(FILL)
    front = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(4, 18), (19, 18), (19, 29), (4, 29)]])
    top = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(4, 18), (11, 12), (26, 12), (19, 18)]])
    side = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(19, 18), (26, 12), (26, 23), (19, 29)]])
    for poly in (front, side, top):
        p.drawPolygon(poly)
    p.setPen(_pen(BLUE, 2.4))
    p.drawLine(QtCore.QPointF(15, 15), QtCore.QPointF(15, 3))
    p.drawLine(QtCore.QPointF(15, 3), QtCore.QPointF(11, 7))
    p.drawLine(QtCore.QPointF(15, 3), QtCore.QPointF(19, 7))
    p.end()
    return theme.icon(pm)


def bim_icon():
    """Classify: a wall with its layers."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.4))
    for x, w, color in ((5, 4, "#eeeae2"), (9, 12, "#c97a5c"), (21, 4, "#eeeae2")):
        p.setBrush(QtGui.QColor(color))
        p.drawRect(QtCore.QRectF(x, 6, w, 20))
    font = p.font()
    font.setPixelSize(8)
    font.setBold(True)
    p.setFont(font)
    p.setPen(_pen(BLUE, 1))
    p.drawText(QtCore.QRectF(0, 24, 32, 9), QtCore.Qt.AlignmentFlag.AlignCenter, "IFC")
    p.end()
    return theme.icon(pm)


def app_icon():
    """The window's icon: the ArqSynth symbol (0.82); a house if its file is missing."""
    from .brand import app_icon as brand_icon
    icon = brand_icon()
    if icon is not None:
        return icon
    pm, p = _canvas()
    p.setPen(_pen(BLUE, 2.2))
    p.setBrush(QtGui.QColor("#dbe6f8"))
    house = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(5, 15), (16, 5), (27, 15), (27, 28), (5, 28)]])
    p.drawPolygon(house)
    p.end()
    return theme.icon(pm)


def wall_icon():
    """Wall: an L of walls in plan, with the drawing point."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.4))
    p.setBrush(QtGui.QColor("#c97a5c"))
    path = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in
                            [(4, 6), (27, 6), (27, 11), (9, 11), (9, 28), (4, 28)]])
    p.drawPolygon(path)
    p.setPen(_pen(BLUE, 1))
    p.setBrush(BLUE)
    p.drawEllipse(QtCore.QPointF(27, 8.5), 2.6, 2.6)
    p.end()
    return theme.icon(pm)


def slab_icon():
    """Slab: a thick plate in perspective."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.4))
    p.setBrush(QtGui.QColor("#c9c7c1"))
    top = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(3, 15), (14, 8), (29, 12), (18, 19)]])
    front = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(3, 15), (18, 19), (18, 24), (3, 20)]])
    side = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(18, 19), (29, 12), (29, 17), (18, 24)]])
    for poly, color in ((front, "#b5b2ab"), (side, "#a19e97"), (top, "#d6d3cc")):
        p.setBrush(QtGui.QColor(color))
        p.drawPolygon(poly)
    p.end()
    return theme.icon(pm)


def column_icon():
    """Column (0.66): an upright square post in perspective."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.4))
    front = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(11, 9), (19, 9), (19, 29), (11, 29)]])
    side = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(19, 9), (24, 5), (24, 25), (19, 29)]])
    top = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(11, 9), (16, 5), (24, 5), (19, 9)]])
    for poly, color in ((front, "#b8c4cc"), (side, "#98a6b0"), (top, "#d3dce2")):
        p.setBrush(QtGui.QColor(color))
        p.drawPolygon(poly)
    p.end()
    return theme.icon(pm)


def beam_icon():
    """Beam (0.66): a level bar resting on two posts."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.4))
    p.setBrush(QtGui.QColor("#b8c4cc"))
    p.drawRect(QtCore.QRectF(5, 14, 5, 15))
    p.drawRect(QtCore.QRectF(22, 14, 5, 15))
    p.setBrush(QtGui.QColor("#8f9ea9"))
    p.drawRect(QtCore.QRectF(3, 8, 26, 6))
    p.end()
    return theme.icon(pm)


def footing_icon():
    """Footing (0.68): a post standing on a wide block below the ground line."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.4))
    p.setBrush(QtGui.QColor("#b8c4cc"))
    p.drawRect(QtCore.QRectF(13, 3, 6, 15))                       # the column
    for poly, color in (([(4, 21), (24, 21), (24, 29), (4, 29)], "#a19e97"),           # the footing: front
                        ([(24, 21), (29, 17), (29, 25), (24, 29)], "#8b8881"),         # side
                        ([(4, 21), (9, 17), (29, 17), (24, 21)], "#c9c7c1")):          # top
        p.setBrush(QtGui.QColor(color))
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in poly]))
    p.setBrush(QtGui.QColor("#b8c4cc"))
    p.drawRect(QtCore.QRectF(13, 15, 6, 4))                       # (the column's foot, over the footing's top)
    p.end()
    return theme.icon(pm)


def pipe_icon():
    """Pipe (0.69): a round tube lying across, its open end seen as a ring."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.4))
    p.setBrush(QtGui.QColor("#5b8fc9"))
    p.drawRect(QtCore.QRectF(9, 11, 19, 10))
    p.drawEllipse(QtCore.QPointF(28, 16), 2.5, 5)                 # the far end
    p.setBrush(QtGui.QColor("#9dbde3"))
    p.drawEllipse(QtCore.QPointF(9, 16), 4, 5)                    # the near end: the ring…
    p.setBrush(QtGui.QColor("#ffffff"))
    p.drawEllipse(QtCore.QPointF(9, 16), 2, 2.6)                  # …and the hole
    p.end()
    return theme.icon(pm)


def duct_icon():
    """Duct (0.69): a rectangular duct in perspective, its open end towards us."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.4))
    for poly, color in (([(4, 13), (12, 8), (29, 8), (21, 13)], "#d6dbe0"),             # top
                        ([(21, 13), (29, 8), (29, 18), (21, 23)], "#a3abb3")):          # side
        p.setBrush(QtGui.QColor(color))
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in poly]))
    p.setBrush(QtGui.QColor("#b8bfc6"))
    p.drawRect(QtCore.QRectF(4, 13, 17, 10))                      # the open end
    p.setBrush(QtGui.QColor("#ffffff"))
    p.drawRect(QtCore.QRectF(7, 15.5, 11, 5))
    p.end()
    return theme.icon(pm)


def grid_icon():
    """Grid axis (0.67): two crossing dash-dot axes, each with its bubble."""
    pm, p = _canvas()
    pen = _pen(INK, 1.3)
    pen.setDashPattern([4, 2, 1, 2])
    for a, b in (((12, 30), (12, 9)), ((3, 20), (24, 20))):
        p.setPen(_pen(FILL, 3.0))
        p.drawLine(QtCore.QPointF(*a), QtCore.QPointF(*b))
        p.setPen(pen)
        p.drawLine(QtCore.QPointF(*a), QtCore.QPointF(*b))
    p.setPen(_pen(BLUE, 1.4))
    p.setBrush(QtGui.QColor("#ffffff"))
    p.drawEllipse(QtCore.QPointF(12, 6), 4, 4)
    p.drawEllipse(QtCore.QPointF(27, 20), 4, 4)
    p.end()
    return theme.icon(pm)


def door_icon():
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.6))
    p.setBrush(QtGui.QColor("#eeeae2"))
    p.drawRect(QtCore.QRectF(4, 3, 24, 27))                       # wall
    p.setBrush(QtGui.QColor("#a8794f"))
    p.drawRect(QtCore.QRectF(10, 9, 12, 21))                      # door leaf
    p.setBrush(INK)
    p.drawEllipse(QtCore.QPointF(19.5, 20), 1.2, 1.2)             # handle
    p.end()
    return theme.icon(pm)


def window_icon():
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.6))
    p.setBrush(QtGui.QColor("#eeeae2"))
    p.drawRect(QtCore.QRectF(4, 3, 24, 27))                       # wall
    p.setBrush(QtGui.QColor("#9cc3d9"))
    p.drawRect(QtCore.QRectF(8, 8, 16, 13))                       # glass
    p.drawLine(QtCore.QPointF(16, 8), QtCore.QPointF(16, 21))
    p.end()
    return theme.icon(pm)


def section_icon():
    """Section: the cut line with its two heads, looking the same way (as on a drawn plan)."""
    pm, p = _canvas()
    p.setPen(_pen(FILL, 4.5))                                      # light halo: visible on dark toolbars too
    p.drawLine(QtCore.QPointF(5, 18), QtCore.QPointF(27, 18))
    pen = _pen(INK, 2.0)
    pen.setDashPattern([4, 2, 1, 2])
    p.setPen(pen)
    p.drawLine(QtCore.QPointF(5, 18), QtCore.QPointF(27, 18))
    for color, width in ((FILL, 3.0), (INK, 1.4)):
        p.setPen(_pen(color, width))
        p.setBrush(INK)
        for x in (5, 27):
            p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(x - 4, 18), QtCore.QPointF(x + 4, 18),
                                           QtCore.QPointF(x, 9)]))
    p.setPen(_pen(BLUE, 1))
    p.setBrush(BLUE)
    p.drawRect(QtCore.QRectF(11, 21, 10, 7))                      # what the section cuts
    p.end()
    return theme.icon(pm)


def dimension_icon():
    """Dimension: two extension lines, the dimension line with 45° ticks, a value over it."""
    pm, p = _canvas()
    for color, extra in ((FILL, 2.6), (INK, 0.0)):                # light halo: visible on dark toolbars too
        p.setPen(_pen(color, 1.4 + extra))
        p.drawLine(QtCore.QPointF(6, 27), QtCore.QPointF(6, 13))
        p.drawLine(QtCore.QPointF(26, 27), QtCore.QPointF(26, 13))
        p.setPen(_pen(color, 1.8 + extra))
        p.drawLine(QtCore.QPointF(4, 17), QtCore.QPointF(28, 17))
        for x in (6, 26):
            p.drawLine(QtCore.QPointF(x - 3, 20), QtCore.QPointF(x + 3, 14))
    p.setPen(_pen(BLUE, 2.0))
    p.drawLine(QtCore.QPointF(11, 9), QtCore.QPointF(21, 9))      # the value
    p.end()
    return theme.icon(pm)


def room_icon():
    """Room (0.99): a room in plan, filled light, with its label."""
    pm, p = _canvas()
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(QtGui.QColor(237, 227, 158))
    p.drawRect(QtCore.QRectF(6, 6, 20, 20))
    p.setBrush(QtGui.QColor("#3a4250"))
    for r in ((4, 4, 24, 2.5), (4, 25.5, 24, 2.5), (4, 4, 2.5, 24), (25.5, 4, 2.5, 24)):
        p.drawRect(QtCore.QRectF(*r))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(11, 14), QtCore.QPointF(21, 14))
    p.setPen(_pen(BLUE, 1.0))
    p.drawLine(QtCore.QPointF(12.5, 18.5), QtCore.QPointF(19.5, 18.5))
    p.end()
    return theme.icon(pm)


def split_wall_icon():
    """Split wall (0.104): a wall in plan cut in two by a blue line, the two parts a little apart."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(3, 13, 11.5, 6))
    p.drawRect(QtCore.QRectF(17.5, 13, 11.5, 6))
    p.setPen(_pen(BLUE, 1.8))
    p.drawLine(QtCore.QPointF(16, 6), QtCore.QPointF(16, 26))
    p.end()
    return theme.icon(pm)


def split_gap_icon():
    """Split with gap (0.300): a wall in plan in two parts with a gap between, its width marked in blue."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(2, 14, 11, 6))
    p.drawRect(QtCore.QRectF(19, 14, 11, 6))
    p.setPen(_pen(BLUE, 1.2))
    for x in (13, 19):
        p.drawLine(QtCore.QPointF(x, 6), QtCore.QPointF(x, 26))
    p.setPen(_pen(BLUE, 1.4))
    p.drawLine(QtCore.QPointF(13.5, 9), QtCore.QPointF(18.5, 9))
    p.setBrush(BLUE)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(13.2, 9), (15.6, 7.4), (15.6, 10.6)]]))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(18.8, 9), (16.4, 7.4), (16.4, 10.6)]]))
    p.end()
    return theme.icon(pm)


def trim_extend_icon():
    """Trim / extend to a boundary (0.300): a blue boundary line, two walls brought to it, one extended (dashed) and
    one trimmed."""
    pm, p = _canvas()
    p.setPen(_pen(BLUE, 2.0))
    p.drawLine(QtCore.QPointF(25, 3), QtCore.QPointF(25, 29))
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(3, 7, 13, 5))
    p.drawRect(QtCore.QRectF(3, 20, 22, 5))
    pen = _pen(INK, 1.0)
    pen.setDashPattern([2, 2])
    p.setPen(pen)
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRect(QtCore.QRectF(16, 7, 9, 5))
    p.drawLine(QtCore.QPointF(25, 22.5), QtCore.QPointF(30, 22.5))
    p.end()
    return theme.icon(pm)


def caixilho_icon():
    """Caixilho Studio (0.307): its mark — a window's frame with a mullion and a transom on an amber square."""
    pm, p = _canvas()
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(QtGui.QColor("#f0b44c"))
    p.drawRoundedRect(QtCore.QRectF(3, 3, 26, 26), 7, 7)
    p.setPen(_pen(QtGui.QColor("#17191c"), 2.2))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRect(QtCore.QRectF(9, 9, 14, 14))
    p.drawLine(QtCore.QPointF(16, 9), QtCore.QPointF(16, 23))
    p.drawLine(QtCore.QPointF(9, 15), QtCore.QPointF(23, 15))
    p.end()
    return theme.icon(pm)


def wall_opening_icon():
    """Wall opening (0.303): a wall in elevation with a rectangular hole, its corners marked in blue."""
    pm, p = _canvas()
    path = QtGui.QPainterPath()
    path.addRect(QtCore.QRectF(3, 5, 26, 23))
    path.addRect(QtCore.QRectF(10, 10, 12, 12))
    path.setFillRule(QtCore.Qt.FillRule.OddEvenFill)
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#e8c9bb"))
    p.drawPath(path)
    p.setPen(_pen(BLUE, 1.0))
    p.setBrush(BLUE)
    for x, y in ((10, 10), (22, 22)):
        p.drawRect(QtCore.QRectF(x - 2, y - 2, 4, 4))
    p.end()
    return theme.icon(pm)


def wall_sweep_icon():
    """Wall sweep (0.304): a wall in elevation with a skirting board along its foot and a cornice along its top, in
    blue (on the wall)."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#f6f3ec"))
    p.drawRect(QtCore.QRectF(3, 5, 26, 22))
    p.setPen(_pen(BLUE, 1.0))
    p.setBrush(QtGui.QColor("#9ab8f0"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(3, 27), (29, 27), (29, 23), (3, 23)]]))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(3, 5), (29, 5), (29, 8), (27, 10), (5, 10),
                                                                  (3, 8)]]))
    p.end()
    return theme.icon(pm)


def wall_reveal_icon():
    """Wall reveal (0.305): a wall in elevation with a level groove and a vertical one cut in it (dark lines, their
    edges in blue)."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#e8c9bb"))
    p.drawRect(QtCore.QRectF(3, 5, 26, 22))
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(QtGui.QColor("#8a5a48"))
    p.drawRect(QtCore.QRectF(3, 14, 26, 2.5))
    p.drawRect(QtCore.QRectF(19, 5, 2.5, 22))
    p.setPen(_pen(BLUE, 1.0))
    p.drawLine(QtCore.QPointF(3, 14), QtCore.QPointF(29, 14))
    p.drawLine(QtCore.QPointF(19, 5), QtCore.QPointF(19, 27))
    p.end()
    return theme.icon(pm)


def wall_joins_icon():
    """Wall joins (0.301): a corner of two walls in plan, mitred — the blue diagonal of the joint."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(3, 21), (21, 21), (27, 27), (3, 27)]]))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(21, 3), (27, 3), (27, 27), (21, 21)]]))
    p.setPen(_pen(BLUE, 2.0))
    p.drawLine(QtCore.QPointF(20, 20), QtCore.QPointF(28, 28))
    p.end()
    return theme.icon(pm)


def corner_walls_icon():
    """Trim / extend to corner (0.104): two walls in plan, one along, one across, meeting at a blue corner."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(3, 21, 18, 6))
    p.drawRect(QtCore.QRectF(23, 3, 6, 14))
    pen = _pen(BLUE, 1.4)
    pen.setDashPattern([2, 2])
    p.setPen(pen)
    p.drawLine(QtCore.QPointF(21, 24), QtCore.QPointF(29, 24))
    p.drawLine(QtCore.QPointF(26, 17), QtCore.QPointF(26, 27))
    p.setPen(_pen(BLUE, 1.0))
    p.setBrush(BLUE)
    p.drawEllipse(QtCore.QPointF(26, 24), 2.2, 2.2)
    p.end()
    return theme.icon(pm)


def roof_icon():
    """Roof (0.111): a hip roof in perspective over a wall."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#f6f3ec"))
    p.drawRect(QtCore.QRectF(6, 18, 20, 10))
    front = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(2, 19), (30, 19), (22, 8), (10, 8)]])
    side = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(2, 19), (10, 8), (6, 6), (1, 14)]])
    for poly, colour in ((side, "#9a5f4a"), (front, "#b9775f")):
        p.setBrush(QtGui.QColor(colour))
        p.drawPolygon(poly)
    p.setPen(_pen(BLUE, 1.4))
    p.drawLine(QtCore.QPointF(10, 8), QtCore.QPointF(22, 8))
    p.end()
    return theme.icon(pm)


def ceiling_icon():
    """Ceiling (0.118): a room in section with a tiled ceiling under the slab, a lamp."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c9c7c1"))
    p.drawRect(QtCore.QRectF(2, 3, 28, 4))
    p.setBrush(QtGui.QColor("#f2f1ec"))
    for x in range(4, 28, 6):
        p.drawRect(QtCore.QRectF(x, 11, 5, 2.5))
    p.setPen(_pen(BLUE, 1.4))
    p.drawLine(QtCore.QPointF(16, 13.5), QtCore.QPointF(16, 19))
    p.setBrush(QtGui.QColor("#ffd966"))
    p.drawEllipse(QtCore.QRectF(13, 19, 6, 4))
    p.setPen(_pen(INK, 1.0))
    p.drawLine(QtCore.QPointF(2, 29), QtCore.QPointF(30, 29))
    p.end()
    return theme.icon(pm)


def wall_finish_icon():
    """Wall finish (0.119): a wall in elevation, tiled up to a blue line (the finish's height)."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#f6f3ec"))
    p.drawRect(QtCore.QRectF(3, 3, 26, 26))
    p.setBrush(QtGui.QColor("#d7e6ea"))
    for row, y in enumerate(range(13, 29, 5)):
        for x in range(3 - (row % 2) * 3, 29, 6):
            p.drawRect(QtCore.QRectF(max(x, 3), y, min(6, 29 - max(x, 3)), min(5, 29 - y)))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(3, 13), QtCore.QPointF(29, 13))
    p.end()
    return theme.icon(pm)


def perforated_panel_icon():
    """Perforated panel (0.389): two boards side by side, full of round holes."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#d9b98c"))
    p.drawRect(QtCore.QRectF(3, 3, 12, 26))
    p.drawRect(QtCore.QRectF(17, 3, 12, 26))
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(QtGui.QColor(INK))
    for x0 in (3, 17):
        for row, y in enumerate(range(7, 27, 4)):
            for x in range(x0 + 3 + (row % 2) * 2, x0 + 11, 4):
                p.drawEllipse(QtCore.QPointF(x, y), 1.1, 1.1)
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(16, 2), QtCore.QPointF(16, 30))
    p.end()
    return theme.icon(pm)


def paint_icon():
    """Paint (0.391): SketchUp's bucket, tipped, paint running out of it."""
    pm, p = _canvas()
    p.save()
    p.translate(15, 15)
    p.rotate(-30)
    p.setPen(_pen(INK, 1.4))
    p.setBrush(QtGui.QColor("#e8e4da"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in ((-8, -6), (8, -6), (6, 9), (-6, 9))]))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawArc(QtCore.QRectF(-7, -13, 14, 12), 0, 180 * 16)            # (its handle)
    p.restore()
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(QtGui.QColor("#c8553d"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in ((4, 10), (9, 8), (8, 22), (5, 24), (3, 21))]))
    p.drawEllipse(QtCore.QPointF(5.5, 26.5), 3.0, 2.2)
    p.end()
    return theme.icon(pm)


def organic_roof_icon():
    """Organic roof (0.390): a curved gridshell over the ground — its arches, the grid's lines across them."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.drawLine(QtCore.QPointF(2, 27), QtCore.QPointF(30, 27))
    p.setPen(_pen(BLUE, 1.6))
    path = QtGui.QPainterPath(QtCore.QPointF(3, 27))
    path.cubicTo(QtCore.QPointF(5, 5), QtCore.QPointF(27, 5), QtCore.QPointF(29, 27))
    p.drawPath(path)
    p.setPen(_pen(BLUE, 1.0))
    for x in (9.5, 16.0, 22.5):                       # (the bars up over it)
        top = 27 - 17 * (1 - ((x - 16) / 13.5) ** 2)
        p.drawLine(QtCore.QPointF(x, 27), QtCore.QPointF(x, top))
    for y in (21, 15):                                # (and across)
        half = 13 * (1 - (27 - y) / 21.0) ** 0.5
        p.drawLine(QtCore.QPointF(16 - half, y), QtCore.QPointF(16 + half, y))
    p.end()
    return theme.icon(pm)


def param_surface_icon():
    """Parametric surface (0.395): a twisted sheet lofted between two curves (orange, the curves it is made of), its
    grid's lines running across it."""
    pm, p = _canvas()
    a = [(3, 22), (9, 14), (17, 17), (24, 9), (29, 11)]
    b = [(4, 29), (10, 24), (18, 27), (25, 20), (30, 22)]

    def curve(pts):
        path = QtGui.QPainterPath(QtCore.QPointF(*pts[0]))
        for k in range(1, len(pts) - 1, 2):
            path.quadTo(QtCore.QPointF(*pts[k]), QtCore.QPointF(*pts[k + 1]))
        return path
    p.setPen(_pen(BLUE, 1.0))
    for k in range(0, 5):                             # (the lines across, from one curve to the other)
        p.drawLine(QtCore.QPointF(*a[k]), QtCore.QPointF(*b[k]))
    p.setPen(_pen(QtGui.QColor("#e07b39"), 1.8))
    p.drawPath(curve(a))
    p.drawPath(curve(b))
    p.setPen(_pen(INK, 1.0))
    p.drawLine(QtCore.QPointF(6, 6), QtCore.QPointF(12, 3))      # (a little spark of a formula: f(u, v))
    p.drawLine(QtCore.QPointF(6, 6), QtCore.QPointF(6, 10))
    p.end()
    return theme.icon(pm)


def control_ring_icon():
    """Control ring (0.395): rings stacked, each smaller above the one below (orange the new one), an arrow up."""
    pm, p = _canvas()
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.setPen(_pen(BLUE, 1.4))
    p.drawEllipse(QtCore.QRectF(3, 21, 22, 8))
    p.drawEllipse(QtCore.QRectF(6, 13, 16, 6))
    p.setPen(_pen(QtGui.QColor("#e07b39"), 1.8))
    p.drawEllipse(QtCore.QRectF(9, 6, 10, 4))
    p.setPen(_pen(INK, 1.2))
    p.drawLine(QtCore.QPointF(27, 20), QtCore.QPointF(27, 5))
    p.drawLine(QtCore.QPointF(27, 5), QtCore.QPointF(24.5, 8))
    p.drawLine(QtCore.QPointF(27, 5), QtCore.QPointF(29.5, 8))
    p.end()
    return theme.icon(pm)


def light_icon():
    """Light (0.119): a ceiling in section with a panel set in it, its light below."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#f2f1ec"))
    p.drawRect(QtCore.QRectF(2, 6, 28, 3))
    p.setBrush(QtGui.QColor("#ffd966"))
    p.drawRect(QtCore.QRectF(10, 8, 12, 3))
    pen = _pen(QtGui.QColor("#e0a800"), 1.2)
    pen.setDashPattern([2, 2])
    p.setPen(pen)
    for x0, x1 in ((10, 4), (16, 16), (22, 28)):
        p.drawLine(QtCore.QPointF(x0, 12), QtCore.QPointF(x1, 26))
    p.setPen(_pen(BLUE, 1.2))
    p.drawLine(QtCore.QPointF(2, 29), QtCore.QPointF(30, 29))
    p.end()
    return theme.icon(pm)


def air_terminal_icon():
    """Air terminal (0.138): a square diffuser seen from below — its frame, its rings of blades — the air blowing out
    of its four sides."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#dfe4e9"))
    p.drawRect(QtCore.QRectF(7, 7, 18, 18))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRect(QtCore.QRectF(11, 11, 10, 10))
    p.setBrush(QtGui.QColor("#9aa6b2"))
    p.drawRect(QtCore.QRectF(14, 14, 4, 4))
    pen = _pen(BLUE, 1.2)
    p.setPen(pen)
    for a, b in (((16, 5), (16, 1)), ((16, 27), (16, 31)), ((5, 16), (1, 16)), ((27, 16), (31, 16))):
        p.drawLine(QtCore.QPointF(*a), QtCore.QPointF(*b))
    p.end()
    return theme.icon(pm)


def equipment_icon():
    """HVAC unit (0.139): a box in perspective with a fan's circle on its face and a duct leaving its side."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    for poly, color in (([(3, 12), (9, 7), (25, 7), (19, 12)], "#e6e9ec"),             # top
                        ([(19, 12), (25, 7), (25, 22), (19, 27)], "#b9c0c7")):         # side
        p.setBrush(QtGui.QColor(color))
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in poly]))
    p.setBrush(QtGui.QColor("#d3d8dd"))
    p.drawRect(QtCore.QRectF(3, 12, 16, 15))                                         # the front
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawEllipse(QtCore.QPointF(11, 19.5), 5, 5)
    p.drawLine(QtCore.QPointF(7.5, 16), QtCore.QPointF(14.5, 23))
    p.drawLine(QtCore.QPointF(14.5, 16), QtCore.QPointF(7.5, 23))
    p.setPen(_pen(BLUE, 1.2))
    p.setBrush(QtGui.QColor("#b8bfc6"))
    p.drawRect(QtCore.QRectF(25, 12, 5, 6))                                          # a duct leaving it
    p.end()
    return theme.icon(pm)


def fixture_icon():
    """Sanitary fixture (0.140): a WC seen from above — its cistern against the wall, its bowl — the free zone in
    front of it dashed."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.4))
    p.drawLine(QtCore.QPointF(3, 4), QtCore.QPointF(29, 4))                       # the wall
    p.setPen(_pen(INK, 1.1))
    p.setBrush(QtGui.QColor("#f4f6f8"))
    p.drawRect(QtCore.QRectF(10, 5, 12, 5))                                       # the cistern
    p.drawEllipse(QtCore.QRectF(11, 9, 10, 13))                                   # the bowl
    pen = _pen(QtGui.QColor("#3c8c4d"), 1.1)
    pen.setDashPattern([2, 2])
    p.setPen(pen)
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRect(QtCore.QRectF(6, 23, 20, 7))                                       # the free zone
    p.end()
    return theme.icon(pm)


def electrical_icon():
    """Electrical point (0.143): an outlet seen from the front — its plate, the round socket with its two holes —
    and a small lightning stroke."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#f4f4ef"))
    p.drawRoundedRect(QtCore.QRectF(4, 6, 20, 20), 3, 3)
    p.setBrush(QtGui.QColor("#dcdcd4"))
    p.drawEllipse(QtCore.QPointF(14, 16), 6.5, 6.5)
    p.setBrush(QtGui.QColor(INK))
    p.drawEllipse(QtCore.QPointF(11.5, 16), 1.2, 1.2)
    p.drawEllipse(QtCore.QPointF(16.5, 16), 1.2, 1.2)
    p.setPen(_pen(QtGui.QColor("#e0a800"), 1.4))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in ((29, 3), (25, 10), (28, 10), (24, 17))]))
    p.end()
    return theme.icon(pm)


def conduit_icon():
    """Conduit (0.146): a thin corrugated tube going up a wall and along under the ceiling to an outlet."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.drawLine(QtCore.QPointF(3, 3), QtCore.QPointF(29, 3))                       # the ceiling
    pen = _pen(QtGui.QColor("#7b5fb0"), 2.2)
    pen.setDashPattern([1.2, 0.6])
    p.setPen(pen)
    p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in ((7, 27), (7, 7), (25, 7), (25, 20))]))
    p.setPen(_pen(INK, 1.1))
    p.setBrush(QtGui.QColor("#f4f4ef"))
    p.drawRoundedRect(QtCore.QRectF(21, 20, 8, 8), 1.5, 1.5)                      # the outlet
    p.setBrush(QtGui.QColor("#c9ced4"))
    p.drawRect(QtCore.QRectF(3, 24, 8, 6))                                        # the board
    p.end()
    return theme.icon(pm)


def terrain_icon():
    """Terrain (0.155): a hill with its contour lines, three points on it."""
    pm, p = _canvas()
    p.setPen(_pen(QtGui.QColor("#7d6a4f"), 1.2))
    p.setBrush(QtGui.QColor("#cfd8b0"))
    p.drawEllipse(QtCore.QRectF(3, 7, 26, 20))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawEllipse(QtCore.QRectF(8, 11, 16, 12))
    p.drawEllipse(QtCore.QRectF(13, 14, 7, 6))
    p.setPen(_pen(BLUE, 2.0))
    for x, y in ((6, 24), (16, 9), (26, 21)):
        p.drawLine(QtCore.QPointF(x - 2, y), QtCore.QPointF(x + 2, y))
        p.drawLine(QtCore.QPointF(x, y - 2), QtCore.QPointF(x, y + 2))
    p.end()
    return theme.icon(pm)


def cad_link_icon():
    """Link a DXF (0.158): a sheet of plan linework with a chain link."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#ffffff"))
    p.drawRect(QtCore.QRectF(3, 3, 20, 24))
    p.setPen(_pen(QtGui.QColor("#4d6a94"), 1.4))
    p.drawRect(QtCore.QRectF(6, 7, 14, 10))
    p.drawLine(QtCore.QPointF(13, 7), QtCore.QPointF(13, 17))
    p.drawLine(QtCore.QPointF(6, 21), QtCore.QPointF(20, 21))
    p.setPen(_pen(BLUE, 2.0))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QtCore.QRectF(17, 18, 8, 5), 2.5, 2.5)
    p.drawRoundedRect(QtCore.QRectF(22, 23, 8, 5), 2.5, 2.5)
    p.end()
    return theme.icon(pm)


def cloud_link_icon():
    """Link a point cloud (0.161): a room's corner in dots."""
    pm, p = _canvas()
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    rng = np.random.default_rng(3)
    for _k in range(70):
        x, y = rng.random() * 24 + 4, rng.random() * 22 + 5
        on_wall = abs(x - 10) < 1.2 or abs(y - 22) < 1.2 or abs(x - 4 - (y - 5) * 0.0) < 0.5
        p.setBrush(QtGui.QColor("#4d6a94" if on_wall else "#9fb4cf"))
        p.drawEllipse(QtCore.QPointF(x, y), 1.0, 1.0)
    p.setPen(_pen(BLUE, 1.8))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QtCore.QRectF(19, 2, 8, 5), 2.5, 2.5)
    p.drawRoundedRect(QtCore.QRectF(24, 6, 6, 4), 2.0, 2.0)
    p.end()
    return theme.icon(pm)


def analyse_icon():
    """Analyse (0.165): a beam with its bending moment's curve under it."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.6))
    p.drawLine(QtCore.QPointF(3, 10), QtCore.QPointF(29, 10))
    for x in (3, 29):
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(x, 10), QtCore.QPointF(x - 3, 15), QtCore.QPointF(x + 3, 15)]))
    p.setPen(_pen(QtGui.QColor("#1f6fe0"), 1.8))
    path = QtGui.QPainterPath(QtCore.QPointF(3, 18))
    path.quadTo(QtCore.QPointF(16, 34), QtCore.QPointF(29, 18))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawPath(path)
    p.drawLine(QtCore.QPointF(3, 18), QtCore.QPointF(29, 18))
    p.end()
    return theme.icon(pm)


def verify_ec2_icon():
    """EC2 check and reinforcement (0.166): a beam's section with its bars and stirrup, a green tick."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.3))
    p.setBrush(QtGui.QColor("#b8c4cc"))
    p.drawRect(QtCore.QRectF(5, 4, 15, 24))                       # the concrete section
    p.setPen(_pen(QtGui.QColor("#9e3d29"), 1.4))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRect(QtCore.QRectF(8, 7, 9, 18))                        # the stirrup
    p.setBrush(QtGui.QColor("#9e3d29"))
    for x, y in ((9.5, 8.5), (15.5, 8.5), (9.5, 23.5), (12.5, 23.5), (15.5, 23.5)):
        p.drawEllipse(QtCore.QPointF(x, y), 1.4, 1.4)             # the bars
    p.setPen(_pen(QtGui.QColor("#2e7d32"), 2.4))
    p.drawLine(QtCore.QPointF(19, 21), QtCore.QPointF(23, 26))
    p.drawLine(QtCore.QPointF(23, 26), QtCore.QPointF(30, 14))
    p.end()
    return theme.icon(pm)


def rebar_schedule_icon():
    """Bar schedule (0.166): a list's lines beside a bent bar."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#ffffff"))
    p.drawRect(QtCore.QRectF(4, 4, 24, 24))
    for y in (10, 15, 20, 25):
        p.drawLine(QtCore.QPointF(4, y), QtCore.QPointF(28, y))
    p.drawLine(QtCore.QPointF(11, 4), QtCore.QPointF(11, 28))
    p.setPen(_pen(QtGui.QColor("#9e3d29"), 2.2))
    p.drawLine(QtCore.QPointF(14, 7), QtCore.QPointF(14, 12.5))
    p.drawLine(QtCore.QPointF(14, 12.5), QtCore.QPointF(26, 12.5))
    p.drawLine(QtCore.QPointF(26, 12.5), QtCore.QPointF(26, 7))
    p.end()
    return theme.icon(pm)


def cabinet_icon():
    """Cabinet (0.169): a base unit seen from the front — two doors with their handles, the worktop over, the plinth
    under."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#9c7a56"))
    p.drawRect(QtCore.QRectF(3, 8, 26, 3))                        # the worktop
    p.setBrush(QtGui.QColor("#f1eee8"))
    p.drawRect(QtCore.QRectF(4, 11, 12, 15))                      # the doors
    p.drawRect(QtCore.QRectF(16, 11, 12, 15))
    p.setBrush(QtGui.QColor("#5a6270"))
    p.drawRect(QtCore.QRectF(5, 26, 22, 3))                       # the plinth
    p.setPen(_pen(QtGui.QColor("#1f6fe0"), 1.8))
    p.drawLine(QtCore.QPointF(13.5, 13), QtCore.QPointF(13.5, 18))   # the handles
    p.drawLine(QtCore.QPointF(18.5, 13), QtCore.QPointF(18.5, 18))
    p.end()
    return theme.icon(pm)


def kitchen_icon():
    """Kitchen (0.170): a run of modules in L seen from above, against two walls."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 2.6))
    p.drawLine(QtCore.QPointF(4, 4), QtCore.QPointF(4, 28))       # the walls
    p.drawLine(QtCore.QPointF(4, 28), QtCore.QPointF(28, 28))
    p.setPen(_pen(INK, 1.0))
    p.setBrush(QtGui.QColor("#f1eee8"))
    for y in (5, 12):                                             # the modules along the left wall
        p.drawRect(QtCore.QRectF(5, y, 8, 7))
    for x in (5, 13, 20):                                         # …and along the bottom one
        p.drawRect(QtCore.QRectF(x, 19, 7, 8))
    p.setPen(_pen(QtGui.QColor("#1f6fe0"), 1.6))
    p.drawLine(QtCore.QPointF(14, 5), QtCore.QPointF(14, 18))     # the worktop's edge
    p.drawLine(QtCore.QPointF(14, 18), QtCore.QPointF(28, 18))
    p.end()
    return theme.icon(pm)


def appliance_icon():
    """Appliance (0.171): a hob's four rings seen from above, on the worktop."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#2b2d33"))
    p.drawRoundedRect(QtCore.QRectF(4, 6, 24, 20), 2, 2)
    p.setPen(_pen(QtGui.QColor("#e07b1f"), 1.6))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    for cx, cy, r in ((11, 12, 3.5), (21, 12, 3.0), (11, 20, 3.0), (21, 20, 3.5)):
        p.drawEllipse(QtCore.QPointF(cx, cy), r, r)
    p.end()
    return theme.icon(pm)


def profile_icon():
    """Profile Pen (0.174): a skirting board's section at a wall's foot and a cornice's cove under the ceiling,
    the pen's path along the wall in blue."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#f6f3ec"))
    p.drawRect(QtCore.QRectF(3, 3, 7, 26))                       # (the wall in section)
    p.setBrush(QtGui.QColor("#c8a27a"))
    skirting = QtGui.QPolygonF([QtCore.QPointF(10, 29), QtCore.QPointF(14, 29), QtCore.QPointF(14, 23),
                                QtCore.QPointF(12, 21), QtCore.QPointF(10, 21)])
    p.drawPolygon(skirting)
    p.setBrush(QtGui.QColor("#eceae4"))
    cove = QtGui.QPainterPath(QtCore.QPointF(10, 3))
    cove.lineTo(10, 11)
    cove.quadTo(11, 4, 18, 3)
    cove.closeSubpath()
    p.drawPath(cove)
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(18, 16), QtCore.QPointF(29, 16))
    p.drawEllipse(QtCore.QPointF(18, 16), 1.6, 1.6)
    p.end()
    return theme.icon(pm)


def worktop_icon():
    """Worktop (0.170): a slab over two base units."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#5c5c62"))
    p.drawRect(QtCore.QRectF(2, 9, 28, 4))
    p.setBrush(QtGui.QColor("#f1eee8"))
    p.drawRect(QtCore.QRectF(4, 13, 12, 13))
    p.drawRect(QtCore.QRectF(16, 13, 12, 13))
    p.end()
    return theme.icon(pm)


def cut_list_icon():
    """Cut list (0.169): a board with the parts marked on it, and a list."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#e9dcc6"))
    p.drawRect(QtCore.QRectF(3, 5, 18, 22))
    dashed = _pen(QtGui.QColor("#b0302a"), 1.0)
    dashed.setStyle(QtCore.Qt.PenStyle.DashLine)
    p.setPen(dashed)
    p.drawLine(QtCore.QPointF(3, 14), QtCore.QPointF(21, 14))
    p.drawLine(QtCore.QPointF(12, 5), QtCore.QPointF(12, 14))
    p.setPen(_pen(INK, 1.4))
    for y in (9, 15, 21, 27):
        p.drawLine(QtCore.QPointF(24, y), QtCore.QPointF(30, y))
    p.end()
    return theme.icon(pm)


def structure_quantities_icon():
    """Structure quantities (0.167): a concrete block with «m³» and a column of figures."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#b8c4cc"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(3, 12), QtCore.QPointF(11, 8), QtCore.QPointF(19, 12),
                                   QtCore.QPointF(19, 24), QtCore.QPointF(11, 28), QtCore.QPointF(3, 24)]))
    p.drawLine(QtCore.QPointF(3, 12), QtCore.QPointF(11, 16))
    p.drawLine(QtCore.QPointF(11, 16), QtCore.QPointF(19, 12))
    p.drawLine(QtCore.QPointF(11, 16), QtCore.QPointF(11, 28))
    p.setPen(_pen(QtGui.QColor("#1f6fe0"), 1.6))
    for y in (8, 14, 20, 26):
        p.drawLine(QtCore.QPointF(22, y), QtCore.QPointF(30, y))
    p.end()
    return theme.icon(pm)


def calc_report_icon():
    """Calculation report (0.167): a page with lines of text, a small table and the red stamp to sign."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#ffffff"))
    p.drawRect(QtCore.QRectF(6, 3, 20, 26))
    for y in (8, 11, 14):
        p.drawLine(QtCore.QPointF(9, y), QtCore.QPointF(23, y))
    p.drawRect(QtCore.QRectF(9, 17, 14, 6))
    p.drawLine(QtCore.QPointF(16, 17), QtCore.QPointF(16, 23))
    p.setPen(_pen(QtGui.QColor("#b0302a"), 1.6))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawEllipse(QtCore.QPointF(23, 25), 4.5, 4.5)
    p.end()
    return theme.icon(pm)


def actions_icon():
    """Actions (0.164): a slab with loads coming down on it, the wind from the side."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.3))
    p.setBrush(QtGui.QColor("#d9cfc0"))
    p.drawRect(QtCore.QRectF(8, 22, 20, 5))
    p.setPen(_pen(QtGui.QColor("#b0302a"), 1.6))
    for x in (11, 18, 25):
        p.drawLine(QtCore.QPointF(x, 6), QtCore.QPointF(x, 19))
        p.drawLine(QtCore.QPointF(x, 19), QtCore.QPointF(x - 2, 16))
        p.drawLine(QtCore.QPointF(x, 19), QtCore.QPointF(x + 2, 16))
    p.setPen(_pen(QtGui.QColor("#1f6fe0"), 1.6))
    p.drawLine(QtCore.QPointF(1, 24), QtCore.QPointF(7, 24))
    p.drawLine(QtCore.QPointF(7, 24), QtCore.QPointF(5, 22))
    p.drawLine(QtCore.QPointF(7, 24), QtCore.QPointF(5, 26))
    p.end()
    return theme.icon(pm)


def analytical_icon():
    """Analytical model (0.163): a frame's axes — two columns orange, a beam blue —, its supports, a tick."""
    pm, p = _canvas()
    p.setPen(_pen(QtGui.QColor("#e07b1f"), 2.2))
    p.drawLine(QtCore.QPointF(7, 26), QtCore.QPointF(7, 9))
    p.drawLine(QtCore.QPointF(25, 26), QtCore.QPointF(25, 9))
    p.setPen(_pen(QtGui.QColor("#1f6fe0"), 2.2))
    p.drawLine(QtCore.QPointF(7, 9), QtCore.QPointF(25, 9))
    p.setPen(_pen(QtGui.QColor("#b0302a"), 1.6))
    for x in (7, 25):
        p.drawRect(QtCore.QRectF(x - 3, 26, 6, 3))
    p.setPen(_pen(QtGui.QColor("#3a9a4a"), 2.0))
    p.drawLine(QtCore.QPointF(12, 17), QtCore.QPointF(15, 20))
    p.drawLine(QtCore.QPointF(15, 20), QtCore.QPointF(21, 13))
    p.end()
    return theme.icon(pm)


def model_from_scan_icon():
    """Model from the point cloud (0.162): a line of dots becomes a wall."""
    pm, p = _canvas()
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(QtGui.QColor("#4d6a94"))
    for k in range(9):
        p.drawEllipse(QtCore.QPointF(4 + k * 3, 7 + (k % 2) * 0.8), 1.0, 1.0)
        p.drawEllipse(QtCore.QPointF(4 + k * 3, 11 - (k % 2) * 0.8), 1.0, 1.0)
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(16, 13), QtCore.QPointF(16, 18))
    p.drawLine(QtCore.QPointF(16, 18), QtCore.QPointF(13, 15))
    p.drawLine(QtCore.QPointF(16, 18), QtCore.QPointF(19, 15))
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#d9cfc0"))
    p.drawRect(QtCore.QRectF(3, 21, 26, 7))
    p.end()
    return theme.icon(pm)


def walls_from_cad_icon():
    """Walls from the drawing (0.159): two thin lines of a plan become a wall (solid)."""
    pm, p = _canvas()
    p.setPen(_pen(QtGui.QColor("#4d6a94"), 1.2))
    p.drawLine(QtCore.QPointF(3, 6), QtCore.QPointF(29, 6))
    p.drawLine(QtCore.QPointF(3, 11), QtCore.QPointF(29, 11))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(16, 13), QtCore.QPointF(16, 18))
    p.drawLine(QtCore.QPointF(16, 18), QtCore.QPointF(13, 15))
    p.drawLine(QtCore.QPointF(16, 18), QtCore.QPointF(19, 15))
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#d9cfc0"))
    p.drawRect(QtCore.QRectF(3, 21, 26, 7))
    p.end()
    return theme.icon(pm)


def platform_icon():
    """Platform (0.157): a flat pad cut into a slope — the ground, the pad, its two slopes."""
    pm, p = _canvas()
    p.setPen(_pen(QtGui.QColor("#7d6a4f"), 1.3))
    p.setBrush(QtGui.QColor("#cfd8b0"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(2, 28), QtCore.QPointF(2, 22), QtCore.QPointF(9, 18),
                                   QtCore.QPointF(12, 15), QtCore.QPointF(22, 15), QtCore.QPointF(26, 11),
                                   QtCore.QPointF(30, 8), QtCore.QPointF(30, 28)]))
    p.setPen(_pen(BLUE, 2.2))
    p.drawLine(QtCore.QPointF(12, 15), QtCore.QPointF(22, 15))
    p.end()
    return theme.icon(pm)


def earthworks_icon():
    """Cut and fill (0.157): earth taken away (down arrow) and brought (up arrow) on a pad."""
    pm, p = _canvas()
    p.setPen(_pen(QtGui.QColor("#7d6a4f"), 1.3))
    p.setBrush(QtGui.QColor("#cfd8b0"))
    p.drawRect(QtCore.QRectF(3, 20, 26, 8))
    p.setPen(_pen(QtGui.QColor("#c8443a"), 2.0))
    p.drawLine(QtCore.QPointF(10, 4), QtCore.QPointF(10, 16))
    p.drawLine(QtCore.QPointF(10, 16), QtCore.QPointF(7, 13))
    p.drawLine(QtCore.QPointF(10, 16), QtCore.QPointF(13, 13))
    p.setPen(_pen(QtGui.QColor("#5fae5f"), 2.0))
    p.drawLine(QtCore.QPointF(22, 16), QtCore.QPointF(22, 4))
    p.drawLine(QtCore.QPointF(22, 4), QtCore.QPointF(19, 7))
    p.drawLine(QtCore.QPointF(22, 4), QtCore.QPointF(25, 7))
    p.end()
    return theme.icon(pm)


def terrain_points_icon():
    """Import survey points (0.155): a list of points with an arrow into a hill."""
    pm, p = _canvas()
    p.setPen(_pen(QtGui.QColor("#7d6a4f"), 1.2))
    p.setBrush(QtGui.QColor("#cfd8b0"))
    p.drawEllipse(QtCore.QRectF(11, 12, 19, 15))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawEllipse(QtCore.QRectF(16, 16, 9, 7))
    p.setPen(_pen(INK, 1.2))
    for k in range(4):
        p.drawLine(QtCore.QPointF(2, 4 + k * 4), QtCore.QPointF(10, 4 + k * 4))
    p.setPen(_pen(BLUE, 1.8))
    p.drawLine(QtCore.QPointF(6, 20), QtCore.QPointF(13, 20))
    p.drawLine(QtCore.QPointF(13, 20), QtCore.QPointF(10, 17))
    p.drawLine(QtCore.QPointF(13, 20), QtCore.QPointF(10, 23))
    p.end()
    return theme.icon(pm)


def _picture_frame(p):
    """A picture (0.154): its frame, a hill and a sun."""
    p.setPen(_pen(INK, 1.3))
    p.setBrush(QtGui.QColor("#dfe8f2"))
    p.drawRect(QtCore.QRectF(3, 6, 26, 20))
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(QtGui.QColor("#8fae7a"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(4, 25), QtCore.QPointF(12, 15), QtCore.QPointF(18, 21),
                                   QtCore.QPointF(22, 17), QtCore.QPointF(28, 25)]))
    p.setBrush(QtGui.QColor("#e8b84a"))
    p.drawEllipse(QtCore.QPointF(22, 11), 2.5, 2.5)


def image_icon():
    """Background image (0.154): a picture with a plus (import)."""
    pm, p = _canvas()
    _picture_frame(p)
    p.setPen(_pen(BLUE, 2.0))
    p.drawLine(QtCore.QPointF(6, 3), QtCore.QPointF(6, 11))
    p.drawLine(QtCore.QPointF(2, 7), QtCore.QPointF(10, 7))
    p.end()
    return theme.icon(pm)


def calibrate_image_icon():
    """Calibrate image (0.154): a picture with a measure across it, its two ticks."""
    pm, p = _canvas()
    _picture_frame(p)
    p.setPen(_pen(BLUE, 1.8))
    p.drawLine(QtCore.QPointF(6, 29), QtCore.QPointF(26, 29))
    p.drawLine(QtCore.QPointF(6, 26), QtCore.QPointF(6, 31))
    p.drawLine(QtCore.QPointF(26, 26), QtCore.QPointF(26, 31))
    p.end()
    return theme.icon(pm)


def scale_icon():
    """Scale (0.153): a small square at a corner and the same square bigger from that corner, an arrow out."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.0))
    pen = _pen(INK, 1.0)
    pen.setDashPattern([2, 2])
    p.setPen(pen)
    p.drawRect(QtCore.QRectF(4, 8, 20, 20))
    p.setPen(_pen(INK, 1.5))
    p.setBrush(QtGui.QColor(FILL))
    p.drawRect(QtCore.QRectF(4, 18, 10, 10))
    p.setPen(_pen(BLUE, 1.5))
    p.drawLine(QtCore.QPointF(14, 18), QtCore.QPointF(26, 6))
    p.drawLine(QtCore.QPointF(26, 6), QtCore.QPointF(20, 7))
    p.drawLine(QtCore.QPointF(26, 6), QtCore.QPointF(25, 12))
    p.end()
    return theme.icon(pm)


def offset_icon():
    """Offset (0.152): a face's outline and, inside it, the same outline offset (a frame), the arrows between them."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.5))
    p.setBrush(QtGui.QColor(FILL))
    p.drawRect(QtCore.QRectF(4, 6, 24, 20))
    p.setPen(_pen(BLUE, 1.4))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRect(QtCore.QRectF(10, 12, 12, 8))
    p.setPen(_pen(INK, 1.0))
    p.drawLine(QtCore.QPointF(5.5, 9), QtCore.QPointF(9, 12.5))
    p.drawLine(QtCore.QPointF(26.5, 23), QtCore.QPointF(23, 19.5))
    p.end()
    return theme.icon(pm)


def circle_icon():
    """Circle (0.150): a circle drawn from its centre, the radius out to where it passes."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.6))
    p.setBrush(QtGui.QColor(FILL))
    p.drawEllipse(QtCore.QPointF(16, 16), 11, 11)
    p.setPen(_pen(BLUE, 1.2))
    p.drawLine(QtCore.QPointF(16, 16), QtCore.QPointF(24, 8.5))
    p.setBrush(QtGui.QColor(INK))
    p.drawEllipse(QtCore.QPointF(16, 16), 1.4, 1.4)
    p.end()
    return theme.icon(pm)


def arc_icon():
    """Arc (0.373): an arc between its two ends, its bulge marked from the chord's middle."""
    pm, p = _canvas()
    path = QtGui.QPainterPath(QtCore.QPointF(4, 25))
    path.cubicTo(QtCore.QPointF(6, 9), QtCore.QPointF(26, 9), QtCore.QPointF(28, 25))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    for color, width in ((FILL, 5.0), (INK, 2.2)):         # (light halo: visible on dark toolbars too)
        p.setPen(_pen(color, width))
        p.drawPath(path)
    p.setPen(_pen(BLUE, 1.0))
    p.drawLine(QtCore.QPointF(16, 25), QtCore.QPointF(16, 14))
    p.setBrush(BLUE)
    for xy in ((4, 25), (28, 25)):
        p.drawEllipse(QtCore.QPointF(*xy), 2.6, 2.6)
    p.end()
    return theme.icon(pm)


def freehand_icon():
    """Freehand (0.373): a wavy line drawn by hand, a pencil at its end."""
    pm, p = _canvas()
    path = QtGui.QPainterPath(QtCore.QPointF(3, 24))
    path.cubicTo(QtCore.QPointF(7, 14), QtCore.QPointF(11, 30), QtCore.QPointF(15, 21))
    path.cubicTo(QtCore.QPointF(18, 14), QtCore.QPointF(19, 18), QtCore.QPointF(21, 13))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    for color, width in ((FILL, 5.0), (INK, 2.0)):
        p.setPen(_pen(color, width))
        p.drawPath(path)
    p.setPen(_pen(INK, 1.4))
    p.setBrush(QtGui.QColor("#f2c94c"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(21, 13), (26, 4), (30, 7), (24, 15)]]))
    p.setBrush(INK)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(21, 13), (22.2, 10.8), (24, 15)]]))
    p.end()
    return theme.icon(pm)


def work_plane_icon():
    """Work plane (0.412): a plane seen at a slant, its grid, the red and green axes along its edges."""
    pm, p = _canvas()
    quad = [QtCore.QPointF(*xy) for xy in ((4, 22), (17, 28), (28, 17), (15, 11))]
    p.setPen(_pen(BLUE, 1.6))
    p.setBrush(QtGui.QColor(61, 127, 214, 60))
    p.drawPolygon(QtGui.QPolygonF(quad))
    p.setPen(_pen(BLUE, 0.9))
    for k in (1, 2):                                 # its grid: two lines each way
        f = k / 3.0
        a, b = quad[0] + (quad[3] - quad[0]) * f, quad[1] + (quad[2] - quad[1]) * f
        c, d = quad[0] + (quad[1] - quad[0]) * f, quad[3] + (quad[2] - quad[3]) * f
        p.drawLine(a, b)
        p.drawLine(c, d)
    p.setPen(_pen(QtGui.QColor("#d64545"), 2.0))
    p.drawLine(quad[0], quad[1])
    p.setPen(_pen(QtGui.QColor("#3aa655"), 2.0))
    p.drawLine(quad[0], quad[3])
    p.end()
    return theme.icon(pm)


def bezier_icon():
    """Bézier curve (0.373): an S curve through two points, their tangents with handles, as a drawing program's."""
    pm, p = _canvas()
    a, b = QtCore.QPointF(5, 24), QtCore.QPointF(27, 8)
    ha, hb = QtCore.QPointF(14, 28), QtCore.QPointF(18, 4)
    p.setPen(_pen(QtGui.QColor("#8a8f99"), 1.0))
    p.drawLine(a, ha)
    p.drawLine(b, hb)
    path = QtGui.QPainterPath(a)
    path.cubicTo(ha, hb, b)
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    for color, width in ((FILL, 5.0), (INK, 2.2)):
        p.setPen(_pen(color, width))
        p.drawPath(path)
    p.setPen(_pen(BLUE, 1.0))
    p.setBrush(QtGui.QColor("white"))
    for h in (ha, hb):
        p.drawRect(QtCore.QRectF(h.x() - 2.2, h.y() - 2.2, 4.4, 4.4))
    p.setBrush(BLUE)
    for xy in (a, b):
        p.drawEllipse(xy, 2.6, 2.6)
    p.end()
    return theme.icon(pm)


def niche_icon():
    """Niche (0.374): a wall's face with a recess in it, its depth shaded."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.5))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(4, 5, 24, 22))
    p.setBrush(QtGui.QColor("#7d4a37"))
    p.drawRect(QtCore.QRectF(11, 11, 10, 9))
    p.setPen(_pen(BLUE, 1.2))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawLine(QtCore.QPointF(11, 20), QtCore.QPointF(14, 17))
    p.drawLine(QtCore.QPointF(21, 20), QtCore.QPointF(18, 17))
    p.end()
    return theme.icon(pm)


def flooring_icon():
    """Floor finish (0.374): a floor's tiles seen from above, in perspective."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.3))
    p.setBrush(QtGui.QColor(FILL))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in ((3, 24), (11, 9), (29, 9), (21, 24))]))
    p.setPen(_pen(BLUE, 1.0))
    for k in (1, 2):
        f = k / 3
        p.drawLine(QtCore.QPointF(3 + 18 * f, 24), QtCore.QPointF(11 + 18 * f, 9))
        p.drawLine(QtCore.QPointF(3 + 8 * f, 24 - 15 * f), QtCore.QPointF(21 + 8 * f, 24 - 15 * f))
    p.end()
    return theme.icon(pm)


def gutter_icon():
    """Gutter (0.374): a roof's slope ending over a half-round gutter, a drop."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.4))
    p.setBrush(QtGui.QColor("#b5533c"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in ((4, 16), (22, 4), (26, 7), (8, 19))]))
    p.setBrush(QtGui.QColor("#cfd6de"))
    p.drawChord(QtCore.QRectF(4, 14, 12, 12), 180 * 16, 180 * 16)
    p.setPen(_pen(BLUE, 1))
    p.setBrush(BLUE)
    p.drawEllipse(QtCore.QPointF(10, 27), 1.6, 2.2)
    p.end()
    return theme.icon(pm)


def elevator_icon():
    """Elevator (0.374): a shaft with its car and the up / down arrows."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.5))
    p.setBrush(QtGui.QColor("#e2e6eb"))
    p.drawRect(QtCore.QRectF(6, 3, 20, 26))
    p.setBrush(QtGui.QColor(FILL))
    p.drawRect(QtCore.QRectF(9, 12, 14, 14))
    p.setPen(_pen(BLUE, 1))
    p.setBrush(BLUE)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in ((12, 9), (16, 5), (20, 9))]))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in ((13, 17), (16, 21), (19, 17))]))
    p.end()
    return theme.icon(pm)


def room_separator_icon():
    """Room separator (0.374): two rooms in plan, a dashed line between them where there is no wall."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 2.0))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRect(QtCore.QRectF(4, 6, 24, 20))
    pen = _pen(BLUE, 1.6)
    pen.setDashPattern([2.5, 2.0])
    p.setPen(pen)
    p.drawLine(QtCore.QPointF(16, 6), QtCore.QPointF(16, 26))
    p.end()
    return theme.icon(pm)


def detail_icon():
    """Detail view (0.133): a wall's corner in plan, a dashed rectangle round it with a numbered bubble."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.0))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in ((4, 26), (4, 10), (20, 10), (20, 14), (8, 14),
                                                                   (8, 26))]))
    pen = _pen(BLUE, 1.4)
    pen.setDashPattern([2.5, 1.5])
    p.setPen(pen)
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QtCore.QRectF(2, 7, 20, 21), 3, 3)
    p.setPen(_pen(BLUE, 1.4))
    p.drawEllipse(QtCore.QPointF(26, 6), 4.5, 4.5)
    p.drawLine(QtCore.QPointF(22, 8), QtCore.QPointF(23, 8.5))
    p.setFont(QtGui.QFont("Segoe UI", 6, QtGui.QFont.Weight.Bold))
    p.drawText(QtCore.QRectF(21.5, 1.5, 9, 9), QtCore.Qt.AlignmentFlag.AlignCenter, "1")
    p.end()
    return theme.icon(pm)


def draft_icon():
    """2D drawing (0.120): a sheet with a hatched region, an arc and a line of text — a pencil's blue tip."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.0))
    p.setBrush(QtGui.QColor("#ffffff"))
    p.drawRect(QtCore.QRectF(3, 3, 22, 26))
    region = QtGui.QPainterPath()
    region.addRect(QtCore.QRectF(6, 15, 10, 8))
    p.save()
    p.setClipPath(region)
    p.setPen(_pen(QtGui.QColor("#777777"), 0.8))
    for k in range(-10, 20, 3):
        p.drawLine(QtCore.QPointF(6 + k, 23), QtCore.QPointF(14 + k, 15))
    p.restore()
    p.setPen(_pen(INK, 1.0))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRect(QtCore.QRectF(6, 15, 10, 8))
    p.drawArc(QtCore.QRectF(6, 5, 14, 14), 0, 180 * 16)
    p.drawLine(QtCore.QPointF(6, 26), QtCore.QPointF(18, 26))
    p.setPen(_pen(BLUE, 2.2))
    p.drawLine(QtCore.QPointF(29, 9), QtCore.QPointF(20, 20))
    p.end()
    return theme.icon(pm)


def curtain_wall_icon():
    """Curtain wall (0.117): a facade in elevation — glass panels in a grid of mullions and transoms."""
    pm, p = _canvas()
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(QtGui.QColor("#9cc3d9"))
    p.drawRect(QtCore.QRectF(4, 4, 24, 24))
    p.setPen(_pen(QtGui.QColor("#5f6b75"), 2.0))
    for c in (4, 12, 20, 28):
        p.drawLine(QtCore.QPointF(c, 4), QtCore.QPointF(c, 28))
    for c in (4, 16, 28):
        p.drawLine(QtCore.QPointF(4, c), QtCore.QPointF(28, c))
    p.setPen(_pen(BLUE, 1.2))
    p.drawLine(QtCore.QPointF(7, 7), QtCore.QPointF(10, 13))
    p.end()
    return theme.icon(pm)


def module_icon(name):
    """(0.184) The compact bar's modules, drawn small and plain: the project (a tree of views), the storeys
    (levels), the library (a box), the sheets, the rooms (a plan), the quantities (a table), the materials
    (swatches), the graphic rules (a brush), the settings (the gear)."""
    if name == "settings":
        return gear_icon()
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.5))
    if name == "project":
        p.drawRect(QtCore.QRectF(5, 5, 9, 6))
        for y in (16, 23):
            p.drawLine(QtCore.QPointF(9, 11), QtCore.QPointF(9, y + 3))
            p.drawLine(QtCore.QPointF(9, y + 3), QtCore.QPointF(15, y + 3))
            p.drawRect(QtCore.QRectF(15, y, 12, 6))
    elif name == "storeys":
        for k, y in enumerate((8, 15, 22)):
            p.setPen(_pen(BLUE if k == 1 else INK, 2.0 if k == 1 else 1.5))
            p.drawLine(QtCore.QPointF(5, y), QtCore.QPointF(27, y))
        p.setPen(_pen(INK, 1.5))
        p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(24, 26), QtCore.QPointF(27, 22), QtCore.QPointF(30, 26)]))
    elif name == "library":
        p.setBrush(QtGui.QColor("#e9dcc9"))
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(6, 10), QtCore.QPointF(16, 5), QtCore.QPointF(26, 10),
                                       QtCore.QPointF(26, 22), QtCore.QPointF(16, 27), QtCore.QPointF(6, 22)]))
        p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(6, 10), QtCore.QPointF(16, 15), QtCore.QPointF(26, 10)]))
        p.drawLine(QtCore.QPointF(16, 15), QtCore.QPointF(16, 27))
    elif name == "sheets":
        p.setBrush(QtGui.QColor("#ffffff"))
        p.drawRect(QtCore.QRectF(5, 7, 22, 17))
        p.drawRect(QtCore.QRectF(19, 18, 8, 6))                  # (its title block)
        p.setPen(_pen(BLUE, 1.4))
        p.drawRect(QtCore.QRectF(8, 10, 9, 8))
    elif name == "rooms":
        p.setPen(_pen(INK, 2.2))
        p.drawRect(QtCore.QRectF(5, 6, 22, 20))
        p.drawLine(QtCore.QPointF(16, 6), QtCore.QPointF(16, 18))
        p.setPen(_pen(BLUE, 1.4))
        p.drawText(QtCore.QRectF(5, 18, 11, 8), QtCore.Qt.AlignmentFlag.AlignCenter, "m²")
    elif name == "quantities":
        p.setBrush(QtGui.QColor("#ffffff"))
        p.drawRect(QtCore.QRectF(5, 6, 22, 20))
        p.setBrush(QtGui.QColor("#dfe8f6"))
        p.drawRect(QtCore.QRectF(5, 6, 22, 5))
        for y in (16, 21):
            p.drawLine(QtCore.QPointF(5, y), QtCore.QPointF(27, y))
        p.drawLine(QtCore.QPointF(13, 6), QtCore.QPointF(13, 26))
    elif name == "materials":
        for k, colour in enumerate(("#c9a27a", "#9cc3d9", "#b9775f")):
            p.setBrush(QtGui.QColor(colour))
            p.drawRoundedRect(QtCore.QRectF(5 + k * 4, 5 + k * 6, 14, 10), 2, 2)
    elif name == "rules":
        p.setBrush(QtGui.QColor("#f3d27a"))
        p.drawRect(QtCore.QRectF(7, 5, 12, 9))
        p.setBrush(QtGui.QColor("#7d858c"))
        p.drawRect(QtCore.QRectF(11, 14, 4, 13))
        p.setPen(_pen(BLUE, 1.6))
        p.drawLine(QtCore.QPointF(22, 8), QtCore.QPointF(28, 8))
        p.drawLine(QtCore.QPointF(22, 14), QtCore.QPointF(28, 14))
    p.end()
    return theme.icon(pm)


def gear_icon():
    """(0.183) The contextual bar's gear: the type in use, in the type editor."""
    import math
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.6))
    path = QtGui.QPainterPath()
    teeth = 8
    for k in range(teeth * 2):
        r = 12.5 if k % 2 == 0 else 9.5
        for s in (-1, 1):
            a = math.radians((k + 0.5 * s * 0.6) * 180.0 / teeth)
            q = QtCore.QPointF(16 + r * math.cos(a), 16 + r * math.sin(a))
            if k == 0 and s == -1:
                path.moveTo(q)
            else:
                path.lineTo(q)
    path.closeSubpath()
    p.setBrush(QtGui.QColor("#e9eef5"))
    p.drawPath(path)
    p.setBrush(QtGui.QColor("#ffffff"))
    p.drawEllipse(QtCore.QPointF(16, 16), 4.0, 4.0)
    p.end()
    return theme.icon(pm)


def curtain_panel_icon():
    """Curtain wall panel (0.181): the facade's grid, one cell made opaque, a door in the bottom row."""
    pm, p = _canvas()
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(QtGui.QColor("#9cc3d9"))
    p.drawRect(QtCore.QRectF(4, 4, 24, 24))
    p.setBrush(QtGui.QColor("#7d858c"))
    p.drawRect(QtCore.QRectF(20, 4, 8, 12))                    # (an opaque cell)
    p.setBrush(QtGui.QColor("#cfe3ee"))
    p.drawRect(QtCore.QRectF(12, 16, 8, 12))                   # (a door, to the floor)
    p.setPen(_pen(QtGui.QColor("#5f6b75"), 2.0))
    for c in (4, 12, 20, 28):
        p.drawLine(QtCore.QPointF(c, 4), QtCore.QPointF(c, 28))
    p.drawLine(QtCore.QPointF(4, 4), QtCore.QPointF(28, 4))
    p.drawLine(QtCore.QPointF(4, 16), QtCore.QPointF(28, 16))
    p.drawLine(QtCore.QPointF(4, 28), QtCore.QPointF(12, 28))
    p.drawLine(QtCore.QPointF(20, 28), QtCore.QPointF(28, 28))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(18, 21), QtCore.QPointF(18, 24))  # (its handle)
    p.end()
    return theme.icon(pm)


def railing_icon():
    """Railing (0.115): posts, a top rail and upright bars."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.0))
    p.drawLine(QtCore.QPointF(3, 27), QtCore.QPointF(29, 27))
    p.setPen(_pen(QtGui.QColor("#5f6b75"), 2.4))
    p.drawLine(QtCore.QPointF(4, 8), QtCore.QPointF(28, 8))
    for x in (5, 27):
        p.drawLine(QtCore.QPointF(x, 8), QtCore.QPointF(x, 27))
    p.setPen(_pen(QtGui.QColor("#8a959e"), 1.2))
    for x in range(9, 25, 4):
        p.drawLine(QtCore.QPointF(x, 9), QtCore.QPointF(x, 26))
    p.setPen(_pen(BLUE, 1.4))
    p.drawLine(QtCore.QPointF(4, 5), QtCore.QPointF(28, 5))
    p.end()
    return theme.icon(pm)


def ai_link_icon():
    """Ligação à IA (0.269): a speech bubble with «IA» in it and a plug's two pins under it."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.6))
    p.setBrush(QtGui.QColor("white"))
    p.drawRoundedRect(QtCore.QRectF(3, 4, 26, 17), 5, 5)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(10, 20.5), QtCore.QPointF(15, 20.5), QtCore.QPointF(10, 25)]))
    font = p.font()
    font.setBold(True)
    font.setPixelSize(11)
    p.setFont(font)
    p.setPen(BLUE)
    p.drawText(QtCore.QRectF(3, 4, 26, 17), QtCore.Qt.AlignmentFlag.AlignCenter, "IA")
    p.setPen(_pen(BLUE, 2.0))
    for x in (20, 25):
        p.drawLine(QtCore.QPointF(x, 24), QtCore.QPointF(x, 29))
    p.end()
    return theme.icon(pm)


def stair_icon():
    """Stair (0.114): a flight seen from its side, its steps and the waist under them."""
    pm, p = _canvas()
    steps = [(3, 28), (3, 24), (8, 24), (8, 20), (13, 20), (13, 16), (18, 16), (18, 12), (23, 12), (23, 8),
             (29, 8), (29, 12), (9, 28)]
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c9c7c1"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in steps]))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(4, 20), QtCore.QPointF(24, 4))
    p.end()
    return theme.icon(pm)


def drain_icon():
    """Drain (0.113): a flat roof's edge in section with a round grate and water running to it."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c9c7c1"))
    p.drawRect(QtCore.QRectF(3, 20, 26, 6))
    p.setBrush(QtGui.QColor("#6f7d8a"))
    p.drawEllipse(QtCore.QRectF(12, 16, 8, 5))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(4, 14), QtCore.QPointF(11, 17))
    p.drawLine(QtCore.QPointF(28, 14), QtCore.QPointF(21, 17))
    p.drawLine(QtCore.QPointF(16, 22), QtCore.QPointF(16, 30))
    p.end()
    return theme.icon(pm)


def roof_opening_icon():
    """Opening through a roof (0.113): a roof slope with a rectangular hole (a skylight) in blue."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#b9775f"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(2, 26), (30, 26), (24, 6), (8, 6)]]))
    p.setPen(_pen(BLUE, 1.4))
    p.setBrush(QtGui.QColor("#d8e6f7"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(11, 21), (21, 21), (19.5, 12), (12.5, 12)]]))
    p.end()
    return theme.icon(pm)


def renumber_icon():
    """Number doors and windows (0.110): a door in plan with its mark in a hexagon-ish tag."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(3, 22, 8, 5))
    p.drawRect(QtCore.QRectF(21, 22, 8, 5))
    p.setPen(_pen(INK, 1.0))
    p.drawArc(QtCore.QRectF(1, 12, 20, 20), 0 * 16, 90 * 16)
    p.setPen(_pen(BLUE, 1.4))
    p.setBrush(QtGui.QColor("white"))
    p.drawEllipse(QtCore.QRectF(15, 3, 14, 11))
    font = p.font()
    font.setPixelSize(8)
    font.setBold(True)
    p.setFont(font)
    p.drawText(QtCore.QRectF(15, 3, 14, 11), QtCore.Qt.AlignmentFlag.AlignCenter, "P1")
    p.end()
    return theme.icon(pm)


def wall_profile_icon():
    """Edit profile (0.109): a wall in elevation with a gable top, grips on its corners."""
    pm, p = _canvas()
    corners = [(4, 28), (28, 28), (28, 14), (16, 5), (4, 14)]
    p.setPen(_pen(INK, 1.3))
    p.setBrush(QtGui.QColor("#f6f3ec"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in corners]))
    p.setPen(_pen(INK, 1.0))
    p.setBrush(QtGui.QColor("white"))
    for x, y in corners:
        p.drawRect(QtCore.QRectF(x - 2.2, y - 2.2, 4.4, 4.4))
    p.setPen(_pen(BLUE, 1.0))
    p.setBrush(BLUE)
    p.drawRect(QtCore.QRectF(16 - 2.6, 5 - 2.6, 5.2, 5.2))
    p.end()
    return theme.icon(pm)


def mirror_icon():
    """Mirror (0.108): an L-shaped plan and its mirror image either side of a dashed blue axis."""
    pm, p = _canvas()
    pen = _pen(BLUE, 1.4)
    pen.setDashPattern([3, 2])
    p.setPen(pen)
    p.drawLine(QtCore.QPointF(16, 3), QtCore.QPointF(16, 29))
    p.setPen(_pen(INK, 1.2))
    for sign, colour in ((-1, "#c97a5c"), (1, "#e8c9bb")):
        pts = [(16 + sign * 3, 8), (16 + sign * 12, 8), (16 + sign * 12, 14), (16 + sign * 8, 14),
               (16 + sign * 8, 24), (16 + sign * 3, 24)]
        p.setBrush(QtGui.QColor(colour))
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in pts]))
    p.end()
    return theme.icon(pm)


def align_icon():
    """Align (0.107): a dashed reference line, a wall moved up to it, a blue arrow across."""
    pm, p = _canvas()
    pen = _pen(BLUE, 1.4)
    pen.setDashPattern([3, 2])
    p.setPen(pen)
    p.drawLine(QtCore.QPointF(3, 8), QtCore.QPointF(29, 8))
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(6, 20, 20, 6))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(16, 18), QtCore.QPointF(16, 11))
    p.setBrush(BLUE)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(16, 9), (13.2, 13), (18.8, 13)]]))
    p.end()
    return theme.icon(pm)


def attach_top_icon():
    """Attach top to slab (0.106): a wall seen from the side reaching up to a slab over it, a blue arrow up."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c9c7c1"))
    p.drawRect(QtCore.QRectF(3, 4, 26, 5))
    p.setBrush(QtGui.QColor("#f6f3ec"))
    p.drawRect(QtCore.QRectF(8, 9, 8, 20))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(23, 27), QtCore.QPointF(23, 13))
    p.setBrush(BLUE)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(23, 10.5), (20, 15), (26, 15)]]))
    p.end()
    return theme.icon(pm)


def flip_walls_icon():
    """Flip wall (0.299): a wall in plan with its insulation on one face, and Revit's blue double arrow across it."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.1))
    p.setBrush(QtGui.QColor("#f2d36b"))
    p.drawRect(QtCore.QRectF(3, 11, 18, 3.5))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(3, 14.5, 18, 7))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(26, 6), QtCore.QPointF(26, 26))
    p.setBrush(BLUE)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(26, 3.5), (22.8, 8.5), (29.2, 8.5)]]))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(26, 28.5), (22.8, 23.5), (29.2, 23.5)]]))
    p.end()
    return theme.icon(pm)


def join_wall_ends_icon():
    """Allow joins (0.299): two walls in plan meeting in a clean corner, a blue dot on the joint."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(3, 21), (23, 21), (23, 27), (3, 27)]]))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(17, 3), (23, 3), (23, 21), (17, 21)]]))
    p.setPen(_pen(BLUE, 1.4))
    p.setBrush(QtGui.QColor("white"))
    p.drawEllipse(QtCore.QPointF(20, 24), 3.6, 3.6)
    p.setBrush(BLUE)
    p.drawEllipse(QtCore.QPointF(20, 24), 1.6, 1.6)
    p.end()
    return theme.icon(pm)


def attach_base_icon():
    """Attach base (0.302): a wall seen from the side standing on a slab under it, a blue arrow down."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c9c7c1"))
    p.drawRect(QtCore.QRectF(3, 23, 26, 5))
    p.setBrush(QtGui.QColor("#f6f3ec"))
    p.drawRect(QtCore.QRectF(8, 3, 8, 20))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(23, 5), QtCore.QPointF(23, 18))
    p.setBrush(BLUE)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(23, 20.5), (20, 16), (26, 16)]]))
    p.end()
    return theme.icon(pm)


def detach_base_icon():
    """Detach base (0.302): a slab and, over it, a wall that no longer stands on it — a blue cut in the gap."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c9c7c1"))
    p.drawRect(QtCore.QRectF(3, 23, 26, 5))
    p.setBrush(QtGui.QColor("#f6f3ec"))
    p.drawRect(QtCore.QRectF(8, 3, 8, 14))
    p.setPen(_pen(BLUE, 1.8))
    p.drawLine(QtCore.QPointF(5, 21.5), QtCore.QPointF(19, 18.5))
    p.drawLine(QtCore.QPointF(23, 18), QtCore.QPointF(23, 4))
    p.setBrush(BLUE)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(23, 1.5), (20, 6), (26, 6)]]))
    p.end()
    return theme.icon(pm)


def detach_top_icon():
    """Detach top (0.298): a slab and, under it, a wall that no longer reaches it — a blue cut in the gap."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c9c7c1"))
    p.drawRect(QtCore.QRectF(3, 4, 26, 5))
    p.setBrush(QtGui.QColor("#f6f3ec"))
    p.drawRect(QtCore.QRectF(8, 15, 8, 14))
    p.setPen(_pen(BLUE, 1.8))
    p.drawLine(QtCore.QPointF(5, 13.5), QtCore.QPointF(19, 10.5))
    p.drawLine(QtCore.QPointF(23, 12), QtCore.QPointF(23, 26))
    p.setBrush(BLUE)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(23, 28.5), (20, 24), (26, 24)]]))
    p.end()
    return theme.icon(pm)


def reset_profile_icon():
    """Reset profile (0.298): a gable outline in dashes and the plain rectangle of the wall again, a blue arrow
    turning back."""
    pm, p = _canvas()
    pen = _pen(INK, 1.0)
    pen.setDashPattern([2, 2])
    p.setPen(pen)
    p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(4, 14), (13, 5), (22, 14)]]))
    p.setPen(_pen(INK, 1.3))
    p.setBrush(QtGui.QColor("#f6f3ec"))
    p.drawRect(QtCore.QRectF(4, 14, 18, 14))
    p.setPen(_pen(BLUE, 1.6))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawArc(QtCore.QRectF(19, 6, 10, 10), 200 * 16, -250 * 16)
    p.setBrush(BLUE)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(18.5, 9.0), (22.5, 10.5), (19.0, 13.5)]]))
    p.end()
    return theme.icon(pm)


def merge_walls_icon():
    """Merge walls (0.105): two walls in plan, end to end, joined by a blue bracket."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(3, 14, 13, 6))
    p.drawRect(QtCore.QRectF(16, 14, 13, 6))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(8, 10), QtCore.QPointF(24, 10))
    p.drawLine(QtCore.QPointF(8, 10), QtCore.QPointF(8, 12.5))
    p.drawLine(QtCore.QPointF(24, 10), QtCore.QPointF(24, 12.5))
    p.end()
    return theme.icon(pm)


def orthogonalize_icon():
    """Orthogonalize (0.105): a slanted wall in dashes and the same wall straight, a blue right angle."""
    pm, p = _canvas()
    pen = _pen(INK, 1.0)
    pen.setDashPattern([2, 2])
    p.setPen(pen)
    p.drawLine(QtCore.QPointF(4, 22), QtCore.QPointF(28, 17))
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(4, 22, 24, 5))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(6, 4), QtCore.QPointF(6, 18))
    p.drawLine(QtCore.QPointF(6, 18), QtCore.QPointF(14, 18))
    p.end()
    return theme.icon(pm)


def unjoin_walls_icon():
    """Disallow joins (0.105): a corner of two walls with a gap between them, and a blue cut."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(3, 21, 17, 6))
    p.drawRect(QtCore.QRectF(23, 3, 6, 15))
    p.setPen(_pen(BLUE, 1.8))
    p.drawLine(QtCore.QPointF(19, 16), QtCore.QPointF(27, 25))
    p.end()
    return theme.icon(pm)


def ramp_icon():
    """Ramp (0.101): a sloping slab in perspective, rising to the right, with an arrow up its slope."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.3))
    top = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(3, 24), (12, 27), (29, 12), (20, 9)]])
    front = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(3, 24), (12, 27), (12, 30), (3, 27)]])
    side = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(12, 27), (29, 12), (29, 16), (12, 30)]])
    for poly, color in ((front, "#b5b2ab"), (side, "#a19e97"), (top, "#d6d3cc")):
        p.setBrush(QtGui.QColor(color))
        p.drawPolygon(poly)
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(10, 21.5), QtCore.QPointF(21, 13.5))
    p.setBrush(BLUE)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(23, 12), (18.6, 13.2), (20.6, 15.8)]]))
    p.end()
    return theme.icon(pm)


def slab_outline_icon():
    """Edit outline (0.100): a slab's outline in plan with square grips on its corners, one being moved."""
    pm, p = _canvas()
    corners = [(4, 8), (20, 4), (28, 16), (16, 28), (6, 22)]
    p.setPen(_pen(INK, 1.4))
    p.setBrush(QtGui.QColor("#d6d3cc"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in corners]))
    p.setPen(_pen(INK, 1.0))
    p.setBrush(QtGui.QColor("white"))
    for x, y in corners:
        p.drawRect(QtCore.QRectF(x - 2.2, y - 2.2, 4.4, 4.4))
    p.setPen(_pen(BLUE, 1.0))
    p.setBrush(BLUE)
    p.drawRect(QtCore.QRectF(28 - 2.6, 16 - 2.6, 5.2, 5.2))
    p.end()
    return theme.icon(pm)


def columns_on_grid_icon():
    """Columns on the grid (0.92): two dash-dot axes each way, a column (a square) at every crossing."""
    pm, p = _canvas()
    pen = _pen(INK, 1.0)
    pen.setDashPattern([4, 2, 1, 2])
    p.setPen(pen)
    for c in (9, 23):
        p.drawLine(QtCore.QPointF(c, 3), QtCore.QPointF(c, 29))
        p.drawLine(QtCore.QPointF(3, c), QtCore.QPointF(29, c))
    p.setPen(_pen(INK, 1.0))
    p.setBrush(QtGui.QColor("#b8c4cc"))
    for x in (9, 23):
        for y in (9, 23):
            p.drawRect(QtCore.QRectF(x - 3, y - 3, 6, 6))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(25, 3), QtCore.QPointF(31, 3))       # a little "+": it adds them
    p.drawLine(QtCore.QPointF(28, 0.5), QtCore.QPointF(28, 5.5))
    p.end()
    return theme.icon(pm)


def footings_under_icon():
    """Footings under the columns (0.93): a column standing on its pad, seen from the side, with a "+"."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#b8c4cc"))
    p.drawRect(QtCore.QRectF(13, 4, 6, 18))                       # the column
    p.setBrush(QtGui.QColor("#a19e97"))
    p.drawRect(QtCore.QRectF(5, 22, 22, 7))                       # its footing
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(24, 6), QtCore.QPointF(30, 6))
    p.drawLine(QtCore.QPointF(27, 3), QtCore.QPointF(27, 9))
    p.end()
    return theme.icon(pm)


def beams_between_icon():
    """Beams between columns (0.94): two columns, a beam from one to the other at their top, a "+"."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#b8c4cc"))
    p.drawRect(QtCore.QRectF(4, 9, 5, 20))
    p.drawRect(QtCore.QRectF(23, 9, 5, 20))
    p.setBrush(QtGui.QColor("#a9b6bf"))
    p.drawRect(QtCore.QRectF(9, 9, 14, 5))                        # the beam, face to face
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(24, 4), QtCore.QPointF(30, 4))
    p.drawLine(QtCore.QPointF(27, 1), QtCore.QPointF(27, 7))
    p.end()
    return theme.icon(pm)


def walls_under_beams_icon():
    """Walls under the beams (0.95): two columns, the beam over them, the wall filling the space below."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(9, 14, 14, 15))                      # the wall
    p.setBrush(QtGui.QColor("#b8c4cc"))
    p.drawRect(QtCore.QRectF(4, 9, 5, 20))
    p.drawRect(QtCore.QRectF(23, 9, 5, 20))
    p.setBrush(QtGui.QColor("#a9b6bf"))
    p.drawRect(QtCore.QRectF(9, 9, 14, 5))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(24, 4), QtCore.QPointF(30, 4))
    p.drawLine(QtCore.QPointF(27, 1), QtCore.QPointF(27, 7))
    p.end()
    return theme.icon(pm)


def slabs_in_bays_icon():
    """Slabs in the beams' bays (0.96): a frame of beams seen from above, its two bays filled."""
    pm, p = _canvas()
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(QtGui.QColor("#c9c7c1"))
    p.drawRect(QtCore.QRectF(6, 9, 9, 15))
    p.drawRect(QtCore.QRectF(17, 9, 9, 15))
    p.setPen(_pen(INK, 1.0))
    p.setBrush(QtGui.QColor("#a9b6bf"))
    for r in ((4, 7, 24, 2), (4, 24, 24, 2), (4, 7, 2, 19), (15, 7, 2, 19), (26, 7, 2, 19)):
        p.drawRect(QtCore.QRectF(*r))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(24, 3), QtCore.QPointF(30, 3))
    p.drawLine(QtCore.QPointF(27, 0.5), QtCore.QPointF(27, 5.5))
    p.end()
    return theme.icon(pm)


def beam_system_icon():
    """A beam system (0.97): a bay of beams seen from above with parallel beams inside."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.0))
    p.setBrush(QtGui.QColor("#a9b6bf"))
    for r in ((4, 6, 24, 2.5), (4, 24, 24, 2.5), (4, 6, 2.5, 20.5), (25.5, 6, 2.5, 20.5)):
        p.drawRect(QtCore.QRectF(*r))
    p.setBrush(QtGui.QColor("#c9d3da"))
    for x in (11, 16, 21):
        p.drawRect(QtCore.QRectF(x - 0.75, 8.5, 1.5, 15.5))
    p.end()
    return theme.icon(pm)


def propose_structure_icon():
    """Propose a structure (0.98): walls in plan (light) with columns at their corners and a spark."""
    pm, p = _canvas()
    p.setPen(_pen(QtGui.QColor("#c97a5c"), 3.0))
    p.drawRect(QtCore.QRectF(6, 9, 20, 17))
    p.setPen(_pen(INK, 1.0))
    p.setBrush(QtGui.QColor("#b8c4cc"))
    for x, y in ((6, 9), (26, 9), (6, 26), (26, 26), (16, 9), (16, 26)):
        p.drawRect(QtCore.QRectF(x - 2.5, y - 2.5, 5, 5))
    p.setPen(_pen(BLUE, 1.5))
    for a, b in (((27, 1), (27, 5)), ((25, 3), (29, 3)), ((25.6, 1.6), (28.4, 4.4)), ((28.4, 1.6), (25.6, 4.4))):
        p.drawLine(QtCore.QPointF(*a), QtCore.QPointF(*b))
    p.end()
    return theme.icon(pm)


def remove_proposal_icon():
    """Remove the proposal (0.98): the columns of the proposal crossed out."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.0))
    p.setBrush(QtGui.QColor("#b8c4cc"))
    for x, y in ((8, 9), (24, 9), (8, 25), (24, 25)):
        p.drawRect(QtCore.QRectF(x - 3, y - 3, 6, 6))
    p.setPen(_pen(QtGui.QColor("#c0392b"), 2.4))
    p.drawLine(QtCore.QPointF(5, 5), QtCore.QPointF(27, 28))
    p.drawLine(QtCore.QPointF(27, 5), QtCore.QPointF(5, 28))
    p.end()
    return theme.icon(pm)


def plan_view_icon():
    """Plan of the active storey (0.84, the Docs environment): walls seen from above, cut, with a door's swing."""
    pm, p = _canvas()
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(QtGui.QColor("#ffffff"))
    p.drawRect(QtCore.QRectF(5, 5, 22, 22))
    p.setBrush(QtGui.QColor("#3a4250"))                           # the cut walls, solid but thin
    for r in ((5, 5, 22, 2), (5, 25, 8, 2), (19, 25, 8, 2), (5, 5, 2, 22), (25, 5, 2, 22), (15, 7, 1.6, 9)):
        p.drawRect(QtCore.QRectF(*r))
    p.setPen(_pen(BLUE, 1.3))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawLine(QtCore.QPointF(13, 26), QtCore.QPointF(13, 20))                      # the door, open
    p.drawArc(QtCore.QRectF(7, 20, 12, 12), 0 * 16, 90 * 16)
    p.end()
    return theme.icon(pm)


def dimension_walls_icon():
    """Dimension the walls (0.84): a wall in plan with the dimension along it."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(5, 18, 22, 6))
    for color, extra in ((FILL, 2.6), (INK, 0.0)):
        p.setPen(_pen(color, 1.3 + extra))
        p.drawLine(QtCore.QPointF(5, 15), QtCore.QPointF(5, 7))
        p.drawLine(QtCore.QPointF(27, 15), QtCore.QPointF(27, 7))
        p.drawLine(QtCore.QPointF(3, 10), QtCore.QPointF(29, 10))
        for x in (5, 27):
            p.drawLine(QtCore.QPointF(x - 2.5, 12.5), QtCore.QPointF(x + 2.5, 7.5))
    p.setPen(_pen(BLUE, 1.8))
    p.drawLine(QtCore.QPointF(11, 5), QtCore.QPointF(21, 5))
    p.end()
    return theme.icon(pm)


def dimension_facades_icon():
    """Dimension the façades (0.123): a building's outline in plan with three rows of dimensions below it."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in ((5, 4), (27, 4), (27, 16), (17, 16), (17, 12),
                                                                   (5, 12))]))
    p.setPen(_pen(INK, 1.0))
    for y, xs in ((20, (5, 11, 17, 27)), (24, (5, 17, 27)), (28, (5, 27))):
        p.drawLine(QtCore.QPointF(xs[0], y), QtCore.QPointF(xs[-1], y))
        for x in xs:
            p.drawLine(QtCore.QPointF(x - 1.5, y + 1.5), QtCore.QPointF(x + 1.5, y - 1.5))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(9, 12), QtCore.QPointF(13, 12))
    p.end()
    return theme.icon(pm)


def dimension_rooms_icon():
    """Dimension the rooms (0.123): a room in plan with its width and depth across it, wall to wall."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#c97a5c"))
    p.drawRect(QtCore.QRectF(3, 3, 26, 26))
    p.setBrush(QtGui.QColor("#ffffff"))
    p.drawRect(QtCore.QRectF(6, 6, 20, 20))
    p.setPen(_pen(BLUE, 1.2))
    p.drawLine(QtCore.QPointF(6, 13), QtCore.QPointF(26, 13))
    p.drawLine(QtCore.QPointF(19, 6), QtCore.QPointF(19, 26))
    for x, y in ((6, 13), (26, 13), (19, 6), (19, 26)):
        p.drawLine(QtCore.QPointF(x - 1.5, y + 1.5), QtCore.QPointF(x + 1.5, y - 1.5))
    p.end()
    return theme.icon(pm)


def view_templates_icon():
    """View templates (0.84): a stack of sheets with a tick — the same settings for several views."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.3))
    for k, shade in enumerate(("#d8dde5", "#e9edf2", "#ffffff")):
        p.setBrush(QtGui.QColor(shade))
        p.drawRect(QtCore.QRectF(4 + 3 * k, 4 + 3 * k, 18, 18))
    p.setPen(_pen(BLUE, 2.2))
    p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(14, 20), QtCore.QPointF(17, 23.5), QtCore.QPointF(23, 15)]))
    p.end()
    return theme.icon(pm)


# ---------------------------------------------------------------- navigation (0.78)

def _lens(p, cx=13, cy=13, r=8):
    """A magnifying glass: its ring (white inside) and its handle."""
    for color, extra in ((FILL, 2.6), (INK, 0.0)):
        p.setPen(_pen(color, 2.0 + extra))
        p.drawLine(QtCore.QPointF(cx + r * 0.72, cy + r * 0.72), QtCore.QPointF(29, 29))
    p.setPen(_pen(INK, 2.0))
    p.setBrush(QtGui.QColor("white"))
    p.drawEllipse(QtCore.QPointF(cx, cy), r, r)


def zoom_icon():
    pm, p = _canvas()
    _lens(p)
    p.setPen(_pen(BLUE, 2.0))
    p.drawLine(QtCore.QPointF(9, 13), QtCore.QPointF(17, 13))
    p.drawLine(QtCore.QPointF(13, 9), QtCore.QPointF(13, 17))
    p.end()
    return theme.icon(pm)


def zoom_all_icon():
    """Zoom all: the lens over a whole frame."""
    pm, p = _canvas()
    pen = _pen(BLUE, 1.6)
    p.setPen(pen)
    p.drawRect(QtCore.QRectF(2, 2, 28, 28))
    _lens(p, 13, 13, 7)
    p.end()
    return theme.icon(pm)


def zoom_window_icon():
    """Zoom window: the lens over a dashed box."""
    pm, p = _canvas()
    pen = _pen(BLUE, 1.6)
    pen.setDashPattern([3, 2])
    p.setPen(pen)
    p.drawRect(QtCore.QRectF(3, 3, 18, 15))
    _lens(p, 16, 16, 7)
    p.end()
    return theme.icon(pm)


def zoom_selection_icon():
    """Zoom to the selection: the lens over a selected (blue) block."""
    pm, p = _canvas()
    p.setPen(_pen(BLUE, 1.4))
    p.setBrush(QtGui.QColor("#bcd3f5"))
    p.drawRect(QtCore.QRectF(4, 5, 13, 11))
    _lens(p, 16, 16, 7)
    p.end()
    return theme.icon(pm)


def _arrow_icon(left):
    pm, p = _canvas()
    sx = 1 if left else -1                      # (the tip at x = 16 - 10·sx: the left one points left)
    pts = [(16 - 10 * sx, 16), (16 + 2 * sx, 6), (16 + 2 * sx, 12), (16 + 11 * sx, 12), (16 + 11 * sx, 20),
           (16 + 2 * sx, 20), (16 + 2 * sx, 26)]
    p.setPen(_pen(INK, 1.6))
    p.setBrush(QtGui.QColor("#d3dce2"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in pts]))
    p.end()
    return theme.icon(pm)


def view_back_icon():
    return _arrow_icon(True)


def view_forward_icon():
    return _arrow_icon(False)


def orbit_icon():
    """Orbit: a globe with an arrow round it."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.6))
    p.setBrush(QtGui.QColor("#d3dce2"))
    p.drawEllipse(QtCore.QPointF(16, 16), 8, 8)
    p.drawLine(QtCore.QPointF(8, 16), QtCore.QPointF(24, 16))
    p.setPen(_pen(BLUE, 2.2))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawArc(QtCore.QRectF(3, 7, 26, 18), 200 * 16, 300 * 16)
    p.setBrush(BLUE)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(27, 11), (30, 17), (24, 16)]]))
    p.end()
    return theme.icon(pm)


def pan_icon():
    """Pan: four arrows out from the middle."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 2.0))
    p.drawLine(QtCore.QPointF(16, 5), QtCore.QPointF(16, 27))
    p.drawLine(QtCore.QPointF(5, 16), QtCore.QPointF(27, 16))
    p.setBrush(INK)
    for tip, a, b in (((16, 3), (12, 8), (20, 8)), ((16, 29), (12, 24), (20, 24)),
                      ((3, 16), (8, 12), (8, 20)), ((29, 16), (24, 12), (24, 20))):
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*tip), QtCore.QPointF(*a), QtCore.QPointF(*b)]))
    p.end()
    return theme.icon(pm)


def position_camera_icon():
    """Position camera: a person standing on a point, the eye marked."""
    pm, p = _canvas()
    p.setPen(_pen(BLUE, 1.2))
    p.setBrush(BLUE)
    p.drawEllipse(QtCore.QPointF(16, 28), 3.5, 1.8)
    p.setPen(_pen(INK, 2.2))
    p.drawLine(QtCore.QPointF(16, 13), QtCore.QPointF(16, 22))
    p.drawLine(QtCore.QPointF(16, 22), QtCore.QPointF(12, 28))
    p.drawLine(QtCore.QPointF(16, 22), QtCore.QPointF(20, 28))
    p.drawLine(QtCore.QPointF(11, 16), QtCore.QPointF(21, 16))
    p.setBrush(QtGui.QColor("white"))
    p.drawEllipse(QtCore.QPointF(16, 8), 3.5, 3.5)
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(20, 8), QtCore.QPointF(29, 6))
    p.drawLine(QtCore.QPointF(20, 8), QtCore.QPointF(29, 11))
    p.end()
    return theme.icon(pm)


def look_around_icon():
    """Look around: an eye with a turning arrow under it."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.8))
    p.setBrush(QtGui.QColor("white"))
    path = QtGui.QPainterPath()
    path.moveTo(3, 13)
    path.quadTo(16, 1, 29, 13)
    path.quadTo(16, 25, 3, 13)
    p.drawPath(path)
    p.setBrush(BLUE)
    p.drawEllipse(QtCore.QPointF(16, 13), 4, 4)
    p.setPen(_pen(BLUE, 2.0))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawArc(QtCore.QRectF(6, 20, 20, 9), 200 * 16, 140 * 16)
    p.setBrush(BLUE)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in [(25, 22), (29, 27), (23, 27)]]))
    p.end()
    return theme.icon(pm)


def walk_icon():
    """Walk: two footprints."""
    pm, p = _canvas()
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QtGui.QColor("#5a6470"))
    for cx, cy in ((11, 20), (21, 11)):
        p.drawEllipse(QtCore.QPointF(cx, cy), 3.6, 6.0)
        p.drawEllipse(QtCore.QPointF(cx, cy + 8.5), 2.6, 2.4)
    p.end()
    return theme.icon(pm)


# ---------------------------------------------------------------- the view cube's pictures (0.79)

def _rgba(image):
    """A QImage as an (H, W, 4) uint8 array (RGBA)."""
    image = image.convertToFormat(QtGui.QImage.Format.Format_RGBA8888)
    w, h = image.width(), image.height()
    data = np.frombuffer(image.constBits(), np.uint8, count=image.bytesPerLine() * h)
    return data.reshape(h, image.bytesPerLine() // 4, 4)[:, :w].copy()


def cube_face_image(text, size=128):
    """A face of the view cube: light, a thin border, its name in the middle."""
    image = QtGui.QImage(size, size, QtGui.QImage.Format.Format_RGBA8888)
    image.fill(QtGui.QColor("#eef1f4"))
    p = QtGui.QPainter(image)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
    p.setPen(_pen(QtGui.QColor("#9aa6b2"), 3.0))
    p.drawRect(QtCore.QRectF(1.5, 1.5, size - 3, size - 3))
    font = p.font()
    font.setBold(True)
    font.setPixelSize(int(size * (0.19 if len(text) <= 7 else 0.15)))
    p.setFont(font)
    p.setPen(QtGui.QColor("#3a4450"))
    p.drawText(QtCore.QRectF(0, 0, size, size), QtCore.Qt.AlignmentFlag.AlignCenter, text)
    p.end()
    return _rgba(image)


CUBE_INK = QtGui.QColor("#3a4450")
CUBE_BLUE = QtGui.QColor("#4f8fd8")


def _cube_canvas(size):
    image = QtGui.QImage(size, size, QtGui.QImage.Format.Format_RGBA8888)
    image.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(image)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
    return image, p, size / 32.0


def house_image(size=64):
    """The view cube's house: back to the starting view."""
    image, p, s = _cube_canvas(size)
    p.setPen(_pen(CUBE_INK, 2.2 * s))
    p.setBrush(QtGui.QColor("#f7f9fb"))
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(x * s, y * s) for x, y in
                                   ((4, 16), (16, 5), (28, 16), (24, 16), (24, 28), (8, 28), (8, 16))]))
    p.setBrush(CUBE_BLUE)
    p.setPen(_pen(CUBE_INK, 1.4 * s))
    p.drawRect(QtCore.QRectF(13 * s, 20 * s, 6 * s, 8 * s))
    p.end()
    return _rgba(image)


def roll_image(clockwise, size=64):
    """A curved arrow over the cube: the view rolled 90° (clockwise or not)."""
    image, p, s = _cube_canvas(size)
    for color, width in ((QtGui.QColor("#f7f9fb"), 5.0), (CUBE_INK, 2.4)):
        p.setPen(_pen(color, width * s))
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        # (Qt: angles from 3 o'clock, counterclockwise; a clockwise arrow goes over the top to the right)
        p.drawArc(QtCore.QRectF(5 * s, 7 * s, 22 * s, 22 * s), (150 if clockwise else 30) * 16, (-120 if clockwise
                                                                                               else 120) * 16)
    tip = ((26, 13), (30, 22), (21, 20)) if clockwise else ((6, 13), (2, 22), (11, 20))
    p.setPen(_pen(CUBE_INK, 1.2 * s))
    p.setBrush(CUBE_INK)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(x * s, y * s) for x, y in tip]))
    p.end()
    return _rgba(image)


def menu_image(size=64):
    """The cube's ▾: its menu."""
    image, p, s = _cube_canvas(size)
    p.setPen(_pen(CUBE_INK, 1.2 * s))
    p.setBrush(CUBE_INK)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(x * s, y * s) for x, y in ((9, 12), (23, 12), (16, 21))]))
    p.end()
    return _rgba(image)


def arrow_image(size=64):
    """A triangle beside the cube (pointing up; turned for the other sides): to the face next to it."""
    image, p, s = _cube_canvas(size)
    p.setPen(_pen(QtGui.QColor("#f7f9fb"), 2.0 * s))
    p.setBrush(CUBE_INK)
    p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(x * s, y * s) for x, y in ((16, 6), (28, 26), (4, 26))]))
    p.end()
    return _rgba(image)


def compass_image(letters, inner_ratio, size=256):
    """The ring under the cube: a light blue band with the four letters (N at the top, E on the right…);
    inner_ratio: its inner radius over the outer one."""
    image, p, s = _cube_canvas(size)
    c = size / 2
    outer, inner = c * 0.98, c * 0.98 * inner_ratio
    ring = QtGui.QPainterPath()
    ring.addEllipse(QtCore.QPointF(c, c), outer, outer)
    ring.addEllipse(QtCore.QPointF(c, c), inner, inner)
    p.setPen(_pen(QtGui.QColor("#2f6fb8"), 2.2 * s / 8))
    p.setBrush(QtGui.QColor(120, 170, 230, 190))
    p.drawPath(ring)
    font = p.font()
    font.setBold(True)
    font.setPixelSize(int((outer - inner) * 0.95))
    p.setFont(font)
    mid = (outer + inner) / 2
    for letter, (dx, dy) in zip(letters, ((0, -1), (1, 0), (0, 1), (-1, 0))):     # N, E, S, W/O
        x, y = c + dx * mid, c + dy * mid
        box = QtCore.QRectF(x - (outer - inner), y - (outer - inner) / 2, 2 * (outer - inner), outer - inner)
        p.setPen(QtGui.QColor("#ffffff"))
        p.drawText(box.translated(1.5, 1.5), QtCore.Qt.AlignmentFlag.AlignCenter, letter)
        p.setPen(QtGui.QColor("#16324f"))
        p.drawText(box, QtCore.Qt.AlignmentFlag.AlignCenter, letter)
    p.end()
    return _rgba(image)


def _iso_cube(p, faces, edges, hidden=False):
    """A small cube seen from above and the front-right (the footer's icons, 0.186): `faces` (top, left, right)
    brushes or None, `edges` its pen; `hidden` its three hidden edges dashed."""
    top = [(16, 4), (28, 10), (16, 16), (4, 10)]
    left = [(4, 10), (16, 16), (16, 29), (4, 23)]
    right = [(16, 16), (28, 10), (28, 23), (16, 29)]
    if hidden:
        pen = QtGui.QPen(edges)
        pen.setDashPattern([2, 2])
        p.setPen(pen)
        for a, b in (((16, 23), (4, 17)), ((16, 23), (28, 17)), ((16, 23), (16, 10))):
            p.drawLine(QtCore.QPointF(*a), QtCore.QPointF(*b))
    p.setPen(edges)
    for face, brush in zip((top, left, right), faces):
        p.setBrush(brush if brush is not None else QtCore.Qt.BrushStyle.NoBrush)
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in face]))


def orientation_icon():
    """(0.186) The footer's Orientation: the view cube, its top face blue."""
    pm, p = _canvas()
    _iso_cube(p, (QtGui.QColor("#9cc0f5"), QtGui.QColor("#ffffff"), QtGui.QColor("#dfe6ef")), _pen(INK, 1.5))
    p.end()
    return theme.icon(pm)


def view_style_icon(style="shaded"):
    """(0.186) A 3D view's graphic style, as a cube: shaded (coloured faces), hidden lines (white faces, the
    edges), wireframe (the edges, the hidden ones too), X-ray (faces seen through)."""
    pm, p = _canvas()
    faces = getattr(style, "faces", None)                 # (0.315: a view style, by how its faces are seen)
    if faces is not None:
        shadows = style.shadows
        style = {"white": "hidden", "none": "wire"}.get(faces, faces)
        if shadows and style == "shaded":
            style = "realistic"
    if style == "realistic":                              # (0.315) with its shadow on the ground
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(QtGui.QColor(0, 0, 0, 60))
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in ((16, 28), (30, 22), (30, 26), (20, 31))]))
    if style == "hidden":
        _iso_cube(p, (QtGui.QColor("#ffffff"),) * 3, _pen(INK, 1.5))
    elif style == "wire":
        _iso_cube(p, (None, None, None), _pen(INK, 1.3), hidden=True)
    elif style == "xray":
        _iso_cube(p, (QtGui.QColor(90, 150, 230, 70),) * 3, _pen(QtGui.QColor("#2f5fa8"), 1.3), hidden=True)
    elif style == "consistent":                           # (0.315) one colour, no light
        _iso_cube(p, (QtGui.QColor("#d4ae78"),) * 3, _pen(INK, 1.3))
    else:
        _iso_cube(p, (QtGui.QColor("#e9d8b4"), QtGui.QColor("#b98f5a"), QtGui.QColor("#d4ae78")), _pen(INK, 1.3))
    p.end()
    return theme.icon(pm)


def ground_grid_icon():
    """(0.186) The 3D view's ground grid: a grid of lines in perspective."""
    pm, p = _canvas()
    p.setPen(_pen(QtGui.QColor("#5b6b80"), 1.2))
    for k in range(5):                                   # the lines running away, closing up at the back
        f = k / 4.0
        p.drawLine(QtCore.QPointF(3 + 26 * f, 28), QtCore.QPointF(10 + 12 * f, 8))
    for y, x0, x1 in ((8, 10, 22), (13, 8.2, 23.8), (19.5, 6, 26), (28, 3, 29)):
        p.drawLine(QtCore.QPointF(x0, y), QtCore.QPointF(x1, y))
    p.end()
    return theme.icon(pm)


def _box(p, x, y, w=10, h=10, fill=FILL):
    p.setPen(_pen(INK, 1.6))
    p.setBrush(fill)
    p.drawRect(QtCore.QRectF(x, y, w, h))


def _arrow(p, a, b, colour=BLUE):
    """A blue arrow from a to b (points as tuples)."""
    p.setPen(_pen(colour, 2.2))
    p.drawLine(QtCore.QPointF(*a), QtCore.QPointF(*b))
    d = np.subtract(b, a, dtype=float)
    d /= np.linalg.norm(d) or 1.0
    n = np.array((-d[1], d[0]))
    for side in (1, -1):
        q = np.asarray(b, dtype=float) - d * 4.5 + n * 3.2 * side
        p.drawLine(QtCore.QPointF(*b), QtCore.QPointF(*q))


def copy_icon():
    """(0.326) Copy: a box left where it was (dashed) and its copy further on, an arrow between."""
    pm, p = _canvas()
    pen = _pen(INK, 1.4)
    pen.setDashPattern([2, 2])
    p.setPen(pen)
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRect(QtCore.QRectF(3, 15, 11, 11))
    _box(p, 18, 5, 11, 11)
    _arrow(p, (9, 13), (17, 10))
    p.setPen(_pen(BLUE, 2.0))
    p.drawLine(QtCore.QPointF(23, 21), QtCore.QPointF(23, 29))         # (a plus: a copy)
    p.drawLine(QtCore.QPointF(19, 25), QtCore.QPointF(27, 25))
    p.end()
    return theme.icon(pm)


def array_icon():
    """(0.326) Array: a row of three boxes at the same spacing, the spacing marked."""
    pm, p = _canvas()
    for x in (2, 12, 22):
        _box(p, x, 9, 8, 8)
    p.setPen(_pen(BLUE, 1.6))
    for x in (6, 16, 26):
        p.drawLine(QtCore.QPointF(x, 21), QtCore.QPointF(x, 27))
    p.drawLine(QtCore.QPointF(6, 24), QtCore.QPointF(26, 24))
    p.end()
    return theme.icon(pm)


def _two_walls(p, line):
    """(0.333) Two walls in an L, cut (hatched): their join with a line (unjoined) or without (joined)."""
    shape = QtGui.QPainterPath()
    shape.addPolygon(QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in
                                      ((4, 6), (12, 6), (12, 20), (28, 20), (28, 28), (4, 28), (4, 6))]))
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(FILL)
    p.drawPath(shape)
    p.save()
    p.setClipPath(shape)
    p.setPen(_pen(QtGui.QColor("#8a8a8a"), 1.0))
    for k in range(-30, 30, 4):
        p.drawLine(QtCore.QPointF(k, 30), QtCore.QPointF(k + 26, 4))
    p.restore()
    p.setPen(_pen(INK, 1.8))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawPath(shape)
    if line:
        p.setPen(_pen(INK, 1.8))
        p.drawLine(QtCore.QPointF(12, 20), QtCore.QPointF(12, 28))


def join_geometry_icon():
    """(0.333) Join Geometry: two walls meeting with no line between them, a blue tick."""
    pm, p = _canvas()
    _two_walls(p, False)
    p.setPen(_pen(BLUE, 2.2))
    p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(17, 9), QtCore.QPointF(21, 13), QtCore.QPointF(28, 4)]))
    p.end()
    return theme.icon(pm)


def unjoin_geometry_icon():
    """(0.333) Unjoin Geometry: two walls meeting with their line between them, the line in blue."""
    pm, p = _canvas()
    _two_walls(p, True)
    p.setPen(_pen(BLUE, 2.4))
    p.drawLine(QtCore.QPointF(12, 18), QtCore.QPointF(12, 30))
    p.setPen(_pen(BLUE, 2.0))
    p.drawLine(QtCore.QPointF(18, 5), QtCore.QPointF(26, 13))             # (a cross: apart)
    p.drawLine(QtCore.QPointF(26, 5), QtCore.QPointF(18, 13))
    p.end()
    return theme.icon(pm)


def copy_clip_icon():
    """(0.326) Ctrl+C: two sheets, one over the other."""
    pm, p = _canvas()
    _box(p, 5, 4, 14, 17, QtGui.QColor("white"))
    _box(p, 12, 10, 14, 17, QtGui.QColor("#e7eefb"))
    p.setPen(_pen(BLUE, 1.6))
    for y in (16, 20):
        p.drawLine(QtCore.QPointF(15, y), QtCore.QPointF(23, y))
    p.end()
    return theme.icon(pm)


def _clipboard(p):
    p.setPen(_pen(INK, 1.6))
    p.setBrush(QtGui.QColor("#e9dcc9"))
    p.drawRoundedRect(QtCore.QRectF(4, 5, 18, 23), 2, 2)
    p.setBrush(QtGui.QColor("#9aa6b6"))
    p.drawRoundedRect(QtCore.QRectF(9, 3, 8, 5), 1.5, 1.5)


def paste_icon():
    """(0.326) Ctrl+V: a clipboard, a sheet coming off it."""
    pm, p = _canvas()
    _clipboard(p)
    _box(p, 14, 13, 14, 16, QtGui.QColor("white"))
    p.end()
    return theme.icon(pm)


def paste_storeys_icon():
    """(0.326) Ctrl+Shift+V: a clipboard and the storeys above, a sheet on each."""
    pm, p = _canvas()
    _clipboard(p)
    p.setPen(_pen(BLUE, 2.0))
    for y in (12, 19, 26):
        p.drawLine(QtCore.QPointF(15, y), QtCore.QPointF(30, y))
    p.setPen(_pen(INK, 1.3))
    p.setBrush(QtGui.QColor("white"))
    for y in (7, 14, 21):
        p.drawRect(QtCore.QRectF(19, y, 7, 5))
    p.end()
    return theme.icon(pm)


TOOL_ICONS = {"select": select_icon, "line": line_icon, "rectangle": rectangle_icon, "push_pull": push_pull_icon,
              "move": move_icon, "rotate": rotate_icon, "tape": tape_icon, "wall": wall_icon, "slab": slab_icon,
              "column": column_icon, "beam": beam_icon, "footing": footing_icon, "pipe": pipe_icon, "duct": duct_icon,
              "grid": grid_icon,
              "door": door_icon, "window": window_icon, "section": section_icon, "dimension": dimension_icon,
              "orbit": orbit_icon, "pan": pan_icon, "zoom": zoom_icon, "zoom_window": zoom_window_icon,
              "position_camera": position_camera_icon, "look_around": look_around_icon, "walk": walk_icon,
              "room": room_icon, "ramp": ramp_icon, "split_wall": split_wall_icon, "corner_walls": corner_walls_icon,
              "split_gap": split_gap_icon, "trim_extend": trim_extend_icon,                       # (0.300)
              "wall_joins": wall_joins_icon,                                                      # (0.301)
              "wall_opening": wall_opening_icon,                                                  # (0.303)
              "wall_sweep": wall_sweep_icon, "wall_reveal": wall_reveal_icon,                     # (0.304, 0.305)
              "align": align_icon, "mirror": mirror_icon, "roof": roof_icon, "drain": drain_icon,
              "roof_opening": roof_opening_icon, "stair": stair_icon, "railing": railing_icon,
              "curtain_wall": curtain_wall_icon, "ceiling": ceiling_icon, "wall_finish": wall_finish_icon,
              "light": light_icon, "draft": draft_icon, "detail": detail_icon, "air_terminal": air_terminal_icon,
              "equipment": equipment_icon, "fixture": fixture_icon, "electrical": electrical_icon,
              "conduit": conduit_icon, "circle": circle_icon, "offset": offset_icon, "scale": scale_icon,
              "calibrate_image": calibrate_image_icon, "terrain": terrain_icon, "platform": platform_icon,
              "terrain_ramp": ramp_icon,                                                      # (0.205)
              "cabinet": cabinet_icon, "kitchen": kitchen_icon, "appliance": appliance_icon,
              "profile": profile_icon, "curtain_panel": curtain_panel_icon,
              "copy": copy_icon, "array": array_icon,                                         # (0.326)
              "join_geometry": join_geometry_icon, "unjoin_geometry": unjoin_geometry_icon,   # (0.333)
              "arc": arc_icon, "freehand": freehand_icon, "bezier": bezier_icon,               # (0.373)
              "work_plane": work_plane_icon,                                                  # (0.412)
              "niche": niche_icon, "flooring": flooring_icon, "gutter": gutter_icon,           # (0.374)
              "elevator": elevator_icon, "room_separator": room_separator_icon,
              "perforated_panel": perforated_panel_icon,                                # (0.389)
              "organic_roof": organic_roof_icon,                                        # (0.390)
    "param_surface": param_surface_icon,                                      # (0.395)
              "paint": paint_icon,                                                      # (0.391)
              "dim_exterior": dimension_facades_icon,                                   # (0.399)
              "dim_interior": dimension_rooms_icon}                                     # (0.400)
