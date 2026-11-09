"""(0.479) The small line glyphs of the ArqSynth Presentation's interface, drawn here (no picture files): the pages'
buttons (Capa, Texto, Planta, Modelo 3D, Concept), a scene card's six buttons (atualizar, favorita, visível, duplicar,
editar, apagar), the icons of the right column's strip (Camadas, Cena, Câmara, Sol, Ambientes, 360°) and of the
commands over the 3D view. Drawn as the Presentation draws its own (thin round strokes on a 24-unit square), in the
colour given — always one of ui/theme.py's."""

import math

from PySide6 import QtCore, QtGui

GRID = 24.0                 # the glyphs' own square (as the Presentation's icons)
SCALE = 2                   # drawn at twice the size: sharp on a screen at 125 % or 200 %


def _line(p, *pts):
    p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in pts]))


def _draw(p, kind):
    """The glyph `kind` on the painter (already scaled to the 24-unit square, its pen set)."""
    if kind == "layers":
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(12, 3), QtCore.QPointF(21, 8), QtCore.QPointF(12, 13),
                                       QtCore.QPointF(3, 8)]))
        _line(p, (3, 12.5), (12, 17.5), (21, 12.5))
        _line(p, (3, 16.5), (12, 21.5), (21, 16.5))
    elif kind == "scene":                                   # a picture: the scene's frame
        p.drawRoundedRect(QtCore.QRectF(3, 5, 18, 14), 2, 2)
        _line(p, (3, 16), (9, 11), (13, 15), (16, 12), (21, 16))
        p.drawEllipse(QtCore.QPointF(16.5, 8.8), 1.4, 1.4)
    elif kind == "camera":                                  # a film camera: the camera's move
        p.drawRoundedRect(QtCore.QRectF(2.5, 7, 13, 10), 2, 2)
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(15.5, 10.5), QtCore.QPointF(21.5, 7.5),
                                       QtCore.QPointF(21.5, 16.5), QtCore.QPointF(15.5, 13.5)]))
    elif kind == "sun":
        p.drawEllipse(QtCore.QPointF(12, 12), 4, 4)
        for k in range(8):
            a = k * math.pi / 4
            _line(p, (12 + 6.5 * math.cos(a), 12 + 6.5 * math.sin(a)), (12 + 9 * math.cos(a), 12 + 9 * math.sin(a)))
    elif kind == "tag":                                     # the rooms' labels
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(3, 3), QtCore.QPointF(11.5, 3), QtCore.QPointF(21, 12.5),
                                       QtCore.QPointF(12.5, 21), QtCore.QPointF(3, 11.5)]))
        p.drawEllipse(QtCore.QPointF(7.5, 7.5), 1.4, 1.4)
    elif kind == "pano":                                    # a 360° panorama
        p.drawEllipse(QtCore.QPointF(12, 12), 9, 9)
        p.drawEllipse(QtCore.QRectF(3, 9, 18, 6))
        _line(p, (12, 3), (12, 21))
    elif kind == "upload":                                  # Exportar / atualizar
        _line(p, (12, 15), (12, 3))
        _line(p, (7, 8), (12, 3), (17, 8))
        _line(p, (3, 15), (3, 20), (21, 20), (21, 15))
    elif kind == "plus":
        _line(p, (12, 5), (12, 19))
        _line(p, (5, 12), (19, 12))
    elif kind in ("eye", "eye_off"):
        path = QtGui.QPainterPath(QtCore.QPointF(2.5, 12))
        path.cubicTo(5.5, 6, 18.5, 6, 21.5, 12)
        path.cubicTo(18.5, 18, 5.5, 18, 2.5, 12)
        p.drawPath(path)
        p.drawEllipse(QtCore.QPointF(12, 12), 3, 3)
        if kind == "eye_off":
            _line(p, (4, 4), (20, 20))
    elif kind in ("star", "star_on"):
        pts = [QtCore.QPointF(12 + (9.5 if k % 2 == 0 else 4.2) * math.sin(k * math.pi / 5),
                              12.8 - (9.5 if k % 2 == 0 else 4.2) * math.cos(k * math.pi / 5)) for k in range(10)]
        if kind == "star_on":
            p.setBrush(p.pen().color())
        p.drawPolygon(QtGui.QPolygonF(pts))
    elif kind == "refresh":                                 # atualizar: the camera taken again
        p.drawArc(QtCore.QRectF(4, 4, 16, 16), 60 * 16, 270 * 16)
        _line(p, (17.5, 2.5), (17.5, 7.5), (12.5, 7.5))
    elif kind == "copy":
        p.drawRoundedRect(QtCore.QRectF(8, 8, 13, 13), 2, 2)
        _line(p, (5, 16), (3.5, 16), (3.5, 3.5), (16, 3.5), (16, 5))
    elif kind == "pencil":
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(16.5, 3.5), QtCore.QPointF(20.5, 7.5), QtCore.QPointF(8, 20),
                                       QtCore.QPointF(3.5, 20.5), QtCore.QPointF(4, 16)]))
        _line(p, (14, 6), (18, 10))
    elif kind == "trash":
        _line(p, (3.5, 6), (20.5, 6))
        _line(p, (9, 6), (9, 3.5), (15, 3.5), (15, 6))
        _line(p, (5.5, 6), (6.5, 20.5), (17.5, 20.5), (18.5, 6))
        _line(p, (10, 10.5), (10, 16.5))
        _line(p, (14, 10.5), (14, 16.5))
    elif kind == "cube":                                    # Modelo 3D
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(12, 2.5), QtCore.QPointF(20.5, 7), QtCore.QPointF(20.5, 17),
                                       QtCore.QPointF(12, 21.5), QtCore.QPointF(3.5, 17), QtCore.QPointF(3.5, 7)]))
        _line(p, (3.5, 7), (12, 11.5), (20.5, 7))
        _line(p, (12, 11.5), (12, 21.5))
    elif kind == "cover":                                   # Capa: a page with its title
        p.drawRoundedRect(QtCore.QRectF(3.5, 4.5, 17, 15), 1.5, 1.5)
        _line(p, (3.5, 12), (20.5, 12))
    elif kind == "text":                                    # Texto
        p.drawRoundedRect(QtCore.QRectF(3.5, 4.5, 17, 15), 1.5, 1.5)
        _line(p, (7, 9), (17, 9))
        _line(p, (7, 12.5), (17, 12.5))
        _line(p, (7, 16), (13, 16))
    elif kind == "plan":                                    # Planta
        p.drawRoundedRect(QtCore.QRectF(3.5, 4.5, 17, 15), 1.5, 1.5)
        _line(p, (3.5, 9), (20.5, 9))
        _line(p, (9, 9), (9, 19.5))
    elif kind == "concept":                                 # Concept: shapes joined
        p.drawEllipse(QtCore.QPointF(7, 7), 3.5, 3.5)
        p.drawRoundedRect(QtCore.QRectF(13.5, 13.5, 7, 7), 1.5, 1.5)
        _line(p, (7, 10.5), (7, 17), (13.5, 17))
    elif kind == "split":                                   # DIVIDIDO: two columns
        p.drawRoundedRect(QtCore.QRectF(3.5, 4.5, 17, 15), 2, 2)
        _line(p, (12, 4.5), (12, 19.5))
    elif kind == "tabs":                                    # ABAS: a list
        for y in (7, 12, 17):
            _line(p, (9, y), (20.5, y))
            p.drawPoint(QtCore.QPointF(4.5, y))
    elif kind == "film":                                    # CENAS
        p.drawRoundedRect(QtCore.QRectF(3.5, 3.5, 17, 17), 2, 2)
        _line(p, (8, 3.5), (8, 20.5))
        _line(p, (16, 3.5), (16, 20.5))
        _line(p, (3.5, 12), (20.5, 12))
    elif kind == "expand":                                  # the whole model in view
        _line(p, (3.5, 9), (3.5, 3.5), (9, 3.5))
        _line(p, (15, 3.5), (20.5, 3.5), (20.5, 9))
        _line(p, (20.5, 15), (20.5, 20.5), (15, 20.5))
        _line(p, (9, 20.5), (3.5, 20.5), (3.5, 15))
    elif kind == "focus":                                   # what is selected in view
        p.drawEllipse(QtCore.QPointF(12, 12), 3, 3)
        _line(p, (3.5, 8), (3.5, 3.5), (8, 3.5))
        _line(p, (16, 3.5), (20.5, 3.5), (20.5, 8))
        _line(p, (20.5, 16), (20.5, 20.5), (16, 20.5))
        _line(p, (8, 20.5), (3.5, 20.5), (3.5, 16))
    elif kind in ("lock", "unlock"):
        p.drawRoundedRect(QtCore.QRectF(5, 11, 14, 10), 2, 2)
        path = QtGui.QPainterPath(QtCore.QPointF(8, 11))
        path.lineTo(8, 7.5)
        path.cubicTo(8, 2.5, 16, 2.5, 16, 7.5)
        if kind == "lock":
            path.lineTo(16, 11)
        p.drawPath(path)
    elif kind == "palette":                                 # Renderizado
        path = QtGui.QPainterPath(QtCore.QPointF(12, 3))
        path.cubicTo(17.5, 3, 21, 6.5, 21, 10.5)
        path.cubicTo(21, 13.5, 17.5, 13, 16, 14.5)
        path.cubicTo(14.5, 16.5, 16.5, 19, 14, 20.5)
        path.cubicTo(8, 21.5, 3, 17, 3, 12)
        path.cubicTo(3, 7, 7, 3, 12, 3)
        p.drawPath(path)
        for x, y in ((7.5, 10.5), (10.5, 7), (15, 7.5)):
            p.drawEllipse(QtCore.QPointF(x, y), 1.2, 1.2)
    elif kind == "auto":                                    # Auto: a gauge
        p.drawArc(QtCore.QRectF(3, 5, 18, 18), 0, 180 * 16)
        _line(p, (12, 14), (16, 9))
    elif kind == "search":
        p.drawEllipse(QtCore.QPointF(10.5, 10.5), 6.5, 6.5)
        _line(p, (15.5, 15.5), (20.5, 20.5))
    elif kind == "down":
        _line(p, (6, 9), (12, 15), (18, 9))
    elif kind == "right":
        _line(p, (9, 6), (15, 12), (9, 18))
    elif kind == "walk":                                    # Passeio: two footprints
        for x, y, s in ((8.5, 13.5, 1.0), (15.5, 9.5, 1.0)):
            p.drawEllipse(QtCore.QRectF(x - 2.6, y - 5.5, 5.2 * s, 8.5))
            p.drawEllipse(QtCore.QPointF(x, y + 5.6), 1.9, 1.6)
    elif kind == "play":
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(7, 4.5), QtCore.QPointF(19, 12), QtCore.QPointF(7, 19.5)]))
    elif kind == "section":                                 # Cortes: a block cut by a plane
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(4, 9), QtCore.QPointF(12, 5), QtCore.QPointF(20, 9),
                                       QtCore.QPointF(20, 18), QtCore.QPointF(12, 22), QtCore.QPointF(4, 18)]))
        _line(p, (4, 9), (12, 13), (20, 9))
        _line(p, (12, 13), (12, 22))
        pen = QtGui.QPen(p.pen())
        pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        p.setPen(pen)
        _line(p, (2, 14), (22, 14))
    elif kind == "shapes":                                  # (0.487) Diagramas: a triangle, a box, a circle
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(12, 2.5), QtCore.QPointF(17, 10.5), QtCore.QPointF(7, 10.5)]))
        p.drawRoundedRect(QtCore.QRectF(3, 13.5, 8, 8), 1, 1)
        p.drawEllipse(QtCore.QPointF(17, 17.5), 4, 4)
    elif kind == "pause":
        p.drawRoundedRect(QtCore.QRectF(6, 5, 4, 14), 1, 1)
        p.drawRoundedRect(QtCore.QRectF(14, 5, 4, 14), 1, 1)
    elif kind == "rotate_l":
        p.drawArc(QtCore.QRectF(4, 4, 16, 16), 90 * 16, 250 * 16)
        _line(p, (7, 2.5), (12, 4), (8, 7.5))
    elif kind == "rotate_r":
        p.drawArc(QtCore.QRectF(4, 4, 16, 16), -160 * 16, 250 * 16)
        _line(p, (17, 2.5), (12, 4), (16, 7.5))


def pixmap(kind, colour, size=18, width=1.7):
    """The glyph `kind` (see _draw) in `colour` (a QColor or "#rrggbb"), `size` pixels square."""
    pm = QtGui.QPixmap(size * SCALE, size * SCALE)
    pm.setDevicePixelRatio(SCALE)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    p.scale(size / GRID, size / GRID)
    pen = QtGui.QPen(QtGui.QColor(colour), width * GRID / size)          # (`width` pixels whatever the size)
    pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    _draw(p, kind)
    p.end()
    return pm


def icon(kind, colour, size=18, on_colour=None):
    """A QIcon of the glyph; `on_colour`: another colour when its button is on (checked)."""
    out = QtGui.QIcon(pixmap(kind, colour, size))
    if on_colour is not None:
        out.addPixmap(pixmap(kind, on_colour, size), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    return out


KINDS = ("layers", "scene", "camera", "sun", "tag", "pano", "upload", "plus", "eye", "eye_off", "star", "star_on",
         "refresh", "copy", "pencil", "trash", "cube", "cover", "text", "plan", "concept", "split", "tabs", "film",
         "expand", "focus", "lock", "unlock", "palette", "auto", "search", "down", "right", "play", "rotate_l",
         "rotate_r", "walk", "pause", "section", "shapes")
