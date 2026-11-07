"""(0.450) The drawing shapes' icons, as Revit's «Draw» panel shows them (the owner: «no revit quando ativar comando de
parede, piso, linha, ou qualquer outro que envolve desenhar, aparece essas opções que permite desenhar em retângulo,
arco etc. … poderia ser em ícones para ocupar menos espaços»): small, drawn in code, one per shape a tool offers on the
contextual bar — a line, a chain, a rectangle, a circle, arcs, a curve, by hand, a face picked, the magic wand, roof
blocks, the terrain, a filled region, a mask, a text, marks. The bar shows a tool's «shape» as a row of these when it
has one for each of its choices (ui/context_bar.py)."""

import math

from PySide6 import QtCore, QtGui

from . import theme

SIZE = 32
INK = QtGui.QColor("#2a2a2a")
BLUE = QtGui.QColor("#1f5fd6")
FILL = QtGui.QColor("#e6e1d6")
_CACHE = {}


def _canvas():
    pm = QtGui.QPixmap(SIZE, SIZE)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    return pm, p


def _pen(color, width=2.2, dash=None):
    pen = QtGui.QPen(color, width)
    pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
    pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    if dash:
        pen.setDashPattern(dash)
    return pen


def _dots(p, *points, r=2.4):
    p.setPen(_pen(BLUE, 1.0))
    p.setBrush(BLUE)
    for x, y in points:
        p.drawEllipse(QtCore.QPointF(x, y), r, r)
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)


def _poly(p, points, closed=False):
    poly = QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in points])
    if closed:
        p.drawPolygon(poly)
    else:
        p.drawPolyline(poly)


def _arc(p, cx, cy, r, start, span):
    """An arc about (cx, cy), from `start` degrees (counter-clockwise, y up) over `span`."""
    p.drawArc(QtCore.QRectF(cx - r, cy - r, 2 * r, 2 * r), int(start * 16), int(span * 16))


def _at(cx, cy, r, deg):
    return cx + r * math.cos(math.radians(deg)), cy - r * math.sin(math.radians(deg))


def _line(p):
    p.setPen(_pen(INK))
    p.drawLine(QtCore.QPointF(6, 26), QtCore.QPointF(26, 6))
    _dots(p, (6, 26), (26, 6))


def _chain(p):
    p.setPen(_pen(INK))
    _poly(p, [(5, 25), (12, 9), (20, 22), (27, 7)])
    _dots(p, (5, 25), (12, 9), (20, 22), (27, 7))


def _chain_arc(p):
    p.setPen(_pen(INK))
    _poly(p, [(5, 26), (12, 12)])
    _arc(p, 19, 15, 7.5, 160, -200)
    _dots(p, (5, 26), (12, 12), _at(19, 15, 7.5, -40))


def _rect(p):
    p.setPen(_pen(INK))
    p.drawRect(QtCore.QRectF(5, 8, 22, 16))
    _dots(p, (5, 24), (27, 8))


def _circle(p):
    p.setPen(_pen(INK))
    p.drawEllipse(QtCore.QPointF(16, 16), 11, 11)
    p.setPen(_pen(INK, 1.2, (2, 2)))
    p.drawLine(QtCore.QPointF(16, 16), QtCore.QPointF(*_at(16, 16, 11, 30)))
    _dots(p, (16, 16))


def _polygon(p):
    p.setPen(_pen(INK))
    _poly(p, [_at(16, 16, 11, 90 + k * 60) for k in range(6)], closed=True)
    _dots(p, (16, 16))


def _arc_three(p):
    p.setPen(_pen(INK))
    _arc(p, 16, 22, 12, 10, 160)
    _dots(p, _at(16, 22, 12, 10), _at(16, 22, 12, 90), _at(16, 22, 12, 170))


def _arc_two(p):
    p.setPen(_pen(INK))
    _arc(p, 16, 22, 12, 10, 160)
    _dots(p, _at(16, 22, 12, 10), _at(16, 22, 12, 170))
    p.setPen(_pen(INK, 1.2, (2, 2)))
    p.drawLine(QtCore.QPointF(16, 22), QtCore.QPointF(16, 10))


def _arc_centre(p):
    p.setPen(_pen(INK))
    _arc(p, 12, 22, 14, 0, 80)
    p.setPen(_pen(INK, 1.2, (2, 2)))
    p.drawLine(QtCore.QPointF(12, 22), QtCore.QPointF(26, 22))
    p.drawLine(QtCore.QPointF(12, 22), QtCore.QPointF(*_at(12, 22, 14, 80)))
    _dots(p, (12, 22))


def _arc_tangent(p):
    """(0.454) Revit's «Tangent End Arc»: a wall, and the arc leaving its end, tangent."""
    p.setPen(_pen(QtGui.QColor("#9a9a9a"), 2.2))
    p.drawLine(QtCore.QPointF(4, 26), QtCore.QPointF(15, 26))
    p.setPen(_pen(INK))
    _arc(p, 15, 15, 11, -90, 150)
    _dots(p, (15, 26), _at(15, 15, 11, 60))


def _pie(p):
    p.setPen(_pen(INK))
    p.setBrush(FILL)
    p.drawPie(QtCore.QRectF(4, 8, 24, 24), 20 * 16, 120 * 16)
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    _dots(p, (16, 20))


def _bezier(p):
    path = QtGui.QPainterPath(QtCore.QPointF(5, 24))
    path.cubicTo(QtCore.QPointF(10, 4), QtCore.QPointF(22, 28), QtCore.QPointF(27, 8))
    p.setPen(_pen(INK))
    p.drawPath(path)
    p.setPen(_pen(BLUE, 1.0))
    p.drawLine(QtCore.QPointF(5, 24), QtCore.QPointF(10, 4))
    p.drawLine(QtCore.QPointF(27, 8), QtCore.QPointF(22, 28))
    _dots(p, (5, 24), (27, 8))


def _freehand(p):
    path = QtGui.QPainterPath(QtCore.QPointF(4, 22))
    path.cubicTo(QtCore.QPointF(8, 8), QtCore.QPointF(12, 28), QtCore.QPointF(17, 16))
    path.cubicTo(QtCore.QPointF(21, 6), QtCore.QPointF(24, 26), QtCore.QPointF(28, 10))
    p.setPen(_pen(INK))
    p.drawPath(path)


def _face(p):
    p.setPen(_pen(INK, 1.6))
    p.setBrush(FILL)
    _poly(p, [(4, 22), (14, 10), (28, 10), (18, 22)], closed=True)
    p.setBrush(QtGui.QColor("white"))
    p.setPen(_pen(INK, 1.4))
    _poly(p, [(19, 15), (19, 29), (22.5, 25.5), (25, 30.5), (27, 29.5), (24.5, 24.5), (29, 24.5)], closed=True)


def _wand(p):
    p.setPen(_pen(INK, 2.6))
    p.drawLine(QtCore.QPointF(6, 27), QtCore.QPointF(19, 14))
    p.setPen(_pen(BLUE, 1.6))
    for a in range(0, 360, 45):
        x, y = _at(23, 9, 6, a)
        p.drawLine(QtCore.QPointF(23, 9), QtCore.QPointF(x, y))


def _blocks(p):
    p.setPen(_pen(INK, 1.8))
    p.drawRect(QtCore.QRectF(4, 8, 24, 16))
    p.setPen(_pen(INK, 1.3))
    for a, b in (((4, 8), (11, 16)), ((4, 24), (11, 16)), ((11, 16), (21, 16)), ((28, 8), (21, 16)),
                 ((28, 24), (21, 16))):
        p.drawLine(QtCore.QPointF(*a), QtCore.QPointF(*b))


def _terrain(p):
    p.setPen(_pen(INK, 1.6))
    for k, y in enumerate((10, 17, 24)):
        path = QtGui.QPainterPath(QtCore.QPointF(4, y + 2))
        path.cubicTo(QtCore.QPointF(11, y - 4 - k), QtCore.QPointF(20, y + 6), QtCore.QPointF(28, y - 1))
        p.drawPath(path)


def _region(p):
    p.setPen(_pen(INK, 1.8))
    p.setBrush(FILL)
    p.drawRect(QtCore.QRectF(5, 7, 22, 18))
    p.setClipRect(QtCore.QRectF(5, 7, 22, 18))
    p.setPen(_pen(INK, 1.0))
    for k in range(-20, 30, 5):
        p.drawLine(QtCore.QPointF(k, 26), QtCore.QPointF(k + 20, 6))
    p.setClipping(False)


def _mask(p):
    p.setPen(_pen(INK, 1.4))
    for k in range(4, 30, 5):                                # (what is under it…)
        p.drawLine(QtCore.QPointF(k, 28), QtCore.QPointF(k + 6, 4))
    p.setPen(_pen(QtGui.QColor("#8a8a8a"), 1.3, (2, 2)))
    p.setBrush(QtGui.QColor("white"))                         # (…hidden by the white mask)
    p.drawRect(QtCore.QRectF(8, 9, 16, 14))


def _text(p):
    font = QtGui.QFont("Sans")
    font.setPixelSize(22)
    font.setBold(True)
    p.setFont(font)
    p.setPen(_pen(INK))
    p.drawText(QtCore.QRectF(0, 2, 32, 28), QtCore.Qt.AlignmentFlag.AlignCenter, "A")


def _spot(p):
    p.setPen(_pen(INK, 1.8))
    _poly(p, [(6, 22), (12, 14), (18, 22)], closed=True)
    p.drawLine(QtCore.QPointF(12, 22), QtCore.QPointF(28, 22))
    p.setPen(_pen(BLUE, 1.6))
    p.drawLine(QtCore.QPointF(18, 10), QtCore.QPointF(28, 10))


def _level(p):
    p.setPen(_pen(INK, 1.8))
    p.drawEllipse(QtCore.QPointF(12, 16), 6.5, 6.5)
    p.setBrush(INK)
    p.drawPie(QtCore.QRectF(5.5, 9.5, 13, 13), 0, 90 * 16)
    p.drawPie(QtCore.QRectF(5.5, 9.5, 13, 13), 180 * 16, 90 * 16)
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawLine(QtCore.QPointF(18.5, 16), QtCore.QPointF(29, 16))


def _keynote(p):
    p.setPen(_pen(INK, 1.8))
    p.drawRect(QtCore.QRectF(14, 5, 14, 11))
    p.drawLine(QtCore.QPointF(14, 14), QtCore.QPointF(6, 26))
    _dots(p, (6, 26))


def _pick(p):
    """(0.451) Revit's «Pick Lines»: a line, lit, and the arrow picking it."""
    p.setPen(_pen(QtGui.QColor("#9a9a9a"), 1.4, (3, 2)))
    p.drawLine(QtCore.QPointF(3, 12), QtCore.QPointF(29, 12))
    p.setPen(_pen(BLUE, 2.6))
    p.drawLine(QtCore.QPointF(3, 12), QtCore.QPointF(29, 12))
    p.setBrush(QtGui.QColor("white"))
    p.setPen(_pen(INK, 1.4))
    _poly(p, [(14, 10), (14, 26), (17.5, 22.5), (20, 27.5), (22, 26.5), (19.5, 21.5), (24, 21.5)], closed=True)


def _fillet(p):
    """(0.452) Revit's «Fillet Arc»: two lines and the arc between them."""
    p.setPen(_pen(QtGui.QColor("#9a9a9a"), 1.4, (3, 2)))
    p.drawLine(QtCore.QPointF(5, 26), QtCore.QPointF(5, 6))
    p.drawLine(QtCore.QPointF(5, 6), QtCore.QPointF(27, 6))
    p.setPen(_pen(INK))
    p.drawLine(QtCore.QPointF(5, 28), QtCore.QPointF(5, 17))
    p.drawLine(QtCore.QPointF(16, 6), QtCore.QPointF(28, 6))
    _arc(p, 16, 17, 11, 90, 90)
    _dots(p, (5, 17), (16, 6))


def _path(p):
    p.setPen(_pen(INK))
    _poly(p, [(5, 26), (5, 12), (18, 12), (18, 24), (27, 24)])
    _dots(p, (5, 26), (27, 24))


DRAWN = {
    "line": _line, "polyline": _chain, "poly": _chain, "polygon": _chain, "line_arc": _chain_arc,
    "rect": _rect, "rectangle": _rect, "retangulo": _rect, "circle": _circle, "circulo": _circle,
    "regular": _polygon, "poligono": _chain, "arc": _arc_three, "three": _arc_three, "two": _arc_two,
    "centre": _arc_centre, "pie": _pie, "bezier": _bezier, "curvo": _bezier, "freehand": _freehand, "face": _face,
    "wand": _wand, "blocks": _blocks, "terrain": _terrain, "region": _region, "mask": _mask, "text": _text,
    "spot": _spot, "level": _level, "keynote": _keynote, "path": _path, "pick": _pick, "fillet": _fillet,
    "arc_center": _arc_centre, "arc_tangent": _arc_tangent,
}


def has(name):
    return name in DRAWN


def icon(name):
    """The shape's icon (cached), or None when there is none."""
    if name not in DRAWN:
        return None
    if name not in _CACHE:
        pm, p = _canvas()
        try:
            DRAWN[name](p)
        finally:
            p.end()
        _CACHE[name] = theme.icon(pm)
    return _CACHE[name]
