"""(0.298) The icons of the ribbon's commands that had only their initials: drawn as the tools' (a dark outline, light
fills, a blue mark), 32 px, so that the ribbon reads as one family. icon(name) -> QIcon, or None for a name not
drawn here."""

import math

from PySide6 import QtCore, QtGui

from . import theme

INK = "#27313d"
BLUE = "#2f6fe4"
RED = "#c0392b"
GREEN = "#2e9e4f"
PAPER = "#ffffff"
WALL = "#c97a5c"
STONE = "#d6d3cc"
LIGHT = "#eef2f8"


def _pt(x, y):
    return QtCore.QPointF(x, y)


def _poly(*xy):
    return QtGui.QPolygonF([_pt(x, y) for x, y in xy])


class _Pen:
    """The painter of one icon, with its pens at hand."""

    def __init__(self):
        self.pm = QtGui.QPixmap(32, 32)
        self.pm.fill(QtCore.Qt.GlobalColor.transparent)
        self.p = QtGui.QPainter(self.pm)
        self.p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.ink()

    def pen(self, colour, width=1.4, dash=None):
        pen = QtGui.QPen(QtGui.QColor(colour), width)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        if dash:
            pen.setDashPattern(dash)
        self.p.setPen(pen)
        return self

    def ink(self, width=1.4, dash=None):
        return self.pen(INK, width, dash)

    def blue(self, width=1.8, dash=None):
        return self.pen(BLUE, width, dash)

    def fill(self, colour=None):
        self.p.setBrush(QtGui.QColor(colour) if colour else QtCore.Qt.BrushStyle.NoBrush)
        return self

    def line(self, x0, y0, x1, y1):
        self.p.drawLine(_pt(x0, y0), _pt(x1, y1))

    def lines(self, *xy):
        self.p.drawPolyline(_poly(*xy))

    def shape(self, *xy):
        self.p.drawPolygon(_poly(*xy))

    def rect(self, x, y, w, h, r=0.0):
        if r:
            self.p.drawRoundedRect(QtCore.QRectF(x, y, w, h), r, r)
        else:
            self.p.drawRect(QtCore.QRectF(x, y, w, h))

    def circle(self, x, y, r):
        self.p.drawEllipse(_pt(x, y), r, r)

    def arrow(self, x0, y0, x1, y1, head=4.0):
        """A line ending in a filled head at (x1, y1), in the pen's colour."""
        self.line(x0, y0, x1, y1)
        a = math.atan2(y1 - y0, x1 - x0)
        colour = self.p.pen().color()
        self.p.save()
        self.p.setBrush(colour)
        self.shape((x1, y1), (x1 - head * math.cos(a - 0.45), y1 - head * math.sin(a - 0.45)),
                   (x1 - head * math.cos(a + 0.45), y1 - head * math.sin(a + 0.45)))
        self.p.restore()

    def text(self, x, y, w, h, s, colour=BLUE, size=8, bold=True):
        font = self.p.font()
        font.setPixelSize(size)
        font.setBold(bold)
        self.p.setFont(font)
        self.p.save()
        self.p.setPen(QtGui.QColor(colour))
        self.p.drawText(QtCore.QRectF(x, y, w, h), QtCore.Qt.AlignmentFlag.AlignCenter, s)
        self.p.restore()

    def done(self):
        self.p.end()
        return theme.icon(self.pm)


# ------------------------------------------------------------ the shared pieces

def _cube(d, x=16, y=17, s=9, colours=("#e9edf3", "#c9d2de", "#dde3eb"), wire=False):
    """An isometric cube centred near (x, y), s its half-width."""
    top = ((x, y - s), (x + s, y - s / 2), (x, y), (x - s, y - s / 2))
    left = ((x - s, y - s / 2), (x, y), (x, y + s), (x - s, y + s / 2))
    right = ((x, y), (x + s, y - s / 2), (x + s, y + s / 2), (x, y + s))
    for face, colour in zip((top, left, right), colours):
        d.fill(None if wire else colour)
        d.shape(*face)


def _sheet(d, x=8, y=4, w=16, h=24, fold=5):
    d.fill(PAPER)
    d.shape((x, y), (x + w - fold, y), (x + w, y + fold), (x + w, y + h), (x, y + h))
    d.lines((x + w - fold, y), (x + w - fold, y + fold), (x + w, y + fold))


def _storeys(d, n=3, x0=5, x1=21, y0=8, step=7, lit=None):
    """Storey levels: lines with a level mark at the left, the lit one in blue."""
    for k in range(n):
        y = y0 + k * step
        (d.blue(1.8) if k == lit else d.ink(1.3)).line(x0 + 4, y, x1, y)
        d.fill(BLUE if k == lit else PAPER).shape((x0, y - 2.5), (x0 + 3, y), (x0, y + 2.5))
    d.ink()


def _tab(d, x=4, y=7, w=24, h=19):
    d.fill(LIGHT)
    d.rect(x, y + 4, w, h - 4, 1.5)
    d.fill(PAPER)
    d.shape((x, y + 4), (x + 2, y), (x + 11, y), (x + 13, y + 4))


def _folder(d, colour="#f3d27a", front="#f7e2a6"):
    d.fill(colour).shape((4, 9), (12, 9), (14, 11), (26, 11), (26, 25), (4, 25))
    d.fill(front).shape((5, 14), (27, 14), (26, 25), (4, 25))


def _link(d, x, y):
    """A chain link (two rounded loops), in blue."""
    d.blue(1.6).fill(None)
    d.p.save()
    d.p.translate(x, y)
    d.p.rotate(-35)
    d.rect(-6, -2.2, 7, 4.4, 2.2)
    d.rect(-1, -2.2, 7, 4.4, 2.2)
    d.p.restore()
    d.ink()


def _bolt(d, x=0, y=0, colour="#f2c230"):
    d.fill(colour).ink(1.2).shape((x + 17, y + 3), (x + 8, y + 17), (x + 15, y + 17), (x + 12, y + 29),
                                  (x + 23, y + 13), (x + 16, y + 13), (x + 19, y + 3))


def _drop(d, x=14, y=16, colour="#7ab0e0"):
    path = QtGui.QPainterPath(_pt(x, y - 11))
    path.cubicTo(x + 3, y - 5, x + 8, y - 1, x + 8, y + 4)
    path.cubicTo(x + 8, y + 9, x - 8, y + 9, x - 8, y + 4)
    path.cubicTo(x - 8, y - 1, x - 3, y - 5, x, y - 11)
    d.fill(colour).ink(1.2)
    d.p.drawPath(path)


def _cross(d, x, y, r=3.5, colour=RED):
    d.pen(colour, 2.0)
    d.line(x - r, y - r, x + r, y + r)
    d.line(x - r, y + r, x + r, y - r)
    d.ink()


def _tick(d, x, y, s=1.0, colour=GREEN):
    d.pen(colour, 2.2)
    d.lines((x - 4 * s, y), (x - 1.2 * s, y + 3 * s), (x + 5 * s, y - 4 * s))
    d.ink()


def _plus(d, x, y, r=4.0):
    d.fill(BLUE).pen(BLUE, 1.0).circle(x, y, r + 1.5)
    d.pen(PAPER, 1.8)
    d.line(x - r + 1, y, x + r - 1, y)
    d.line(x, y - r + 1, x, y + r - 1)
    d.ink()


def _gear(d, x, y, r=5.0):
    d.fill("#dfe6f1").ink(1.1)
    teeth = []
    for k in range(16):
        a = math.pi * 2 * k / 16
        rr = r + (1.6 if k % 2 == 0 else 0.0)
        teeth.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    d.shape(*teeth)
    d.fill(PAPER).circle(x, y, r * 0.38)


def _grid(d, n=3, x0=6, y0=6, size=20, colour=INK):
    d.pen(colour, 1.0, [2, 1.5])
    for k in range(n):
        v = x0 + size * k / (n - 1)
        d.line(v, y0 - 2, v, y0 + size + 2)
        d.line(x0 - 2, y0 + size * k / (n - 1), x0 + size + 2, y0 + size * k / (n - 1))
    d.ink()


def _mouse(d):
    d.fill(PAPER).ink(1.3)
    d.rect(9, 5, 14, 22, 7)
    d.line(9, 13, 23, 13)
    d.line(16, 5, 16, 13)
    d.fill(BLUE).pen(BLUE, 1.0).rect(14.5, 7, 3, 4.5, 1.5)
    d.ink()


def _component(d, x=14, y=17, s=8, colour="#e9dcc9"):
    _cube(d, x, y, s, (colour, "#d9c6a8", "#e3d2b8"))


# ------------------------------------------------------------ each command

def _ai_install(d):
    d.fill(PAPER).ink(1.3)
    d.rect(3, 4, 20, 14, 4)
    d.shape((8, 18), (8, 23), (13, 18))
    d.text(3, 4, 20, 14, "IA", size=9)
    d.blue(1.8)
    d.line(22, 22, 26, 26)
    d.fill(LIGHT).ink(1.2).rect(24, 23, 6, 6, 1.0)
    d.line(25.5, 23, 25.5, 21)
    d.line(28.5, 23, 28.5, 21)


def _box(d):
    _cube(d, 16, 16, 11, wire=True)
    d.blue(1.0)
    for x, y in ((16, 5), (27, 10.5), (27, 21.5), (16, 27), (5, 21.5), (5, 10.5)):
        d.fill(BLUE).rect(x - 1.8, y - 1.8, 3.6, 3.6)


def _box_selection(d):
    d.ink(1.0, [2, 1.5])
    _cube(d, 16, 16, 12, wire=True)
    d.ink()
    _cube(d, 16, 17, 5, ("#c97a5c", "#a9644a", "#b86e52"))


def _cad_links(d):
    d.p.save()
    d.p.translate(-3, 1)
    _sheet(d)
    d.p.restore()
    _sheet(d, 11, 3, 16, 22)
    d.text(11, 9, 14, 8, "DXF", size=6)
    _link(d, 11, 25)


def _check_ids(d):
    _sheet(d, 6, 3, 18, 25)
    d.text(6, 8, 16, 8, "IDS", size=7)
    for y in (19, 23):
        d.ink(1.0).line(10, y, 19, y)
    _tick(d, 23, 22)


def _verify_settings(d):
    """(0.417) The project's regulations: a law's sheet with § and a gear."""
    _sheet(d, 6, 3, 18, 25)
    d.text(6, 7, 16, 10, "§", size=10)
    for y in (19, 23):
        d.ink(1.0).line(10, y, 19, y)
    _gear(d, 23, 22, 4.5)


def _verify_panel(d):
    """(0.418) The Verification panel: a law's sheet with § and what passes and fails."""
    _sheet(d, 4, 3, 18, 25)
    d.text(4, 7, 16, 10, "§", size=10)
    _tick(d, 22, 15, 0.8)
    _cross(d, 24, 24, 3.0)


def _check_ifc(d):
    _cube(d, 13, 15, 9)
    d.fill(PAPER).pen(GREEN, 1.4).circle(23, 23, 6.5)
    _tick(d, 23, 23, 0.8)


def _clashes(d):
    d.fill("#9cc3e6").ink(1.2)
    d.rect(3, 13, 26, 6, 2)
    d.fill("#c9c7c1")
    d.rect(13, 3, 6, 26)
    d.fill("#9cc3e6").pen(INK, 0)
    d.p.setPen(QtCore.Qt.PenStyle.NoPen)
    d.rect(13.6, 13.6, 4.8, 4.8)
    d.fill("#f2c230").pen(RED, 1.2)
    star = [(16 + (8 if k % 2 == 0 else 3.6) * math.cos(math.pi * k / 6 - math.pi / 2),
             16 + (8 if k % 2 == 0 else 3.6) * math.sin(math.pi * k / 6 - math.pi / 2)) for k in range(12)]
    d.shape(*star)


def _close_view(d):
    _tab(d)
    _cross(d, 16, 18, 4)


def _cloud_links(d):
    d.p.setPen(QtCore.Qt.PenStyle.NoPen)
    for x, y, c in ((8, 10, "#e07b5a"), (14, 7, "#7ab0e0"), (21, 10, "#9ccc7a"), (11, 15, "#e8c45a"),
                    (18, 14, "#b48ad6"), (25, 16, "#7ab0e0"), (6, 18, "#9ccc7a"), (15, 20, "#e07b5a")):
        d.fill(c)
        d.circle(x, y, 2.2)
    _link(d, 20, 25)


def _component_close(d):
    _component(d, 13, 17)
    d.blue(1.8).arrow(18, 22, 29, 22)


def _component_edit(d):
    _component(d, 13, 18)
    d.fill("#f3d27a").ink(1.1).shape((19, 13), (27, 5), (30, 8), (22, 16), (18, 17))
    d.line(25, 7, 28, 10)


def _component_make(d):
    _component(d, 13, 18)
    _plus(d, 25, 8)


def _delete(d):
    d.fill(LIGHT).ink(1.3)
    d.shape((8, 10), (24, 10), (22.5, 28), (9.5, 28))
    d.rect(6, 7, 20, 3, 1)
    d.rect(13, 4, 6, 3, 1)
    d.pen(RED, 1.6)
    for x in (12.5, 16, 19.5):
        d.line(x, 13, x, 25)
    d.ink()


def _dimension_style(d):
    d.ink(1.2)
    d.line(4, 9, 4, 17)
    d.line(28, 9, 28, 17)
    d.line(3, 13, 29, 13)
    d.blue(1.6)
    d.line(2.5, 15, 5.5, 11)
    d.line(26.5, 15, 29.5, 11)
    d.text(8, 2, 16, 9, "2,40", colour=INK, size=7)
    d.fill("#dfe6f1").ink(1.1).rect(8, 20, 16, 8, 1.5)
    d.text(8, 20, 16, 8, "Aa", size=7)


def _electrical_check(d):
    _bolt(d, -3, 0)
    d.fill(PAPER).pen(GREEN, 1.4).circle(24, 23, 6.5)
    _tick(d, 24, 23, 0.8)


def _front(d):
    d.fill(LIGHT).ink(1.3)
    d.shape((5, 27), (5, 14), (16, 5), (27, 14), (27, 27))
    d.fill("#9cc3e6").rect(9, 17, 5, 5)
    d.fill("#c9a27a").rect(18, 18, 5, 9)
    d.blue(1.6).arrow(16, 31, 16, 28.5, 3)


def _give_back(d):
    d.fill("#f3d27a").ink(1.2).circle(9, 12, 5)
    d.fill(PAPER).circle(9, 12, 1.6)
    d.ink(1.6).line(13, 15, 22, 24)
    d.line(18, 20, 20, 18)
    d.line(21, 23, 23, 21)
    d.blue(1.8).arrow(28, 9, 18, 4, 3.5)


def _graphic_styles(d):
    for y, w in ((7, 1.0), (13, 2.0), (20, 3.2)):
        d.ink(w).line(4, y, 20, y)
    d.blue(1.2, [2, 2]).line(4, 26, 20, 26)
    d.fill("#e8c45a").ink(1.1).shape((22, 25), (28, 9), (30, 10), (25, 27))
    d.fill(INK).shape((22, 25), (25, 27), (21.5, 29))


def _patterns(d):
    """(0.318) Fill patterns: three swatches — diagonal, crossed, bricks."""
    d.fill(PAPER).ink(1.1).rect(3, 4, 12, 11)
    d.fill(PAPER).ink(1.1).rect(17, 4, 12, 11)
    d.fill("#f3d9cc").ink(1.1).rect(3, 18, 26, 10)
    d.ink(0.8)
    for x0, y0, x1, y1 in ((3, 12, 11, 4), (3, 15, 14, 4), (7, 15, 15, 7),                 # (diagonal)
                           (17, 8, 29, 8), (17, 12, 29, 12), (21, 4, 21, 8), (26, 8, 26, 12), (21, 12, 21, 15),
                           (3, 28, 13, 18), (9, 28, 19, 18), (15, 28, 25, 18), (21, 28, 29, 20)):
        d.line(x0, y0, x1, y1)


def _view_styles(d):
    """(0.315) A view style: a shaded box with its shadow, a hatch on its face."""
    d.fill("#30000000").shape((14, 27), (29, 22), (29, 26), (18, 30))         # (Qt's #AARRGGBB)
    d.fill("#e9d8b4").ink(1.2).shape((4, 10), (14, 5), (24, 10), (14, 15))
    d.fill("#b98f5a").shape((4, 10), (14, 15), (14, 27), (4, 22))
    d.fill("#d4ae78").shape((14, 15), (24, 10), (24, 22), (14, 27))
    for k in range(3):
        d.ink(0.8).line(15.5, 19 + k * 3.2, 22.5, 15.5 + k * 3.2)


def _grid_generate(d):
    _grid(d)
    for x, y in ((6, 6), (16, 6), (26, 6), (6, 16), (16, 16), (26, 16), (6, 26), (16, 26)):
        d.fill(INK).circle(x, y, 1.2)
    _plus(d, 25, 25, 3.5)


def _grid_settings(d):
    _grid(d)
    _gear(d, 23, 23, 5)


def _group_make(d):
    d.blue(1.3, [3, 2]).fill(None).rect(3, 4, 26, 24, 2)
    d.fill(WALL).ink(1.1).rect(7, 8, 9, 9)
    d.fill("#9cc3e6").circle(20, 20, 5)


def _group_ungroup(d):
    d.blue(1.3, [3, 2]).fill(None)
    d.lines((14, 4), (3, 4), (3, 15))
    d.lines((18, 28), (29, 28), (29, 17))
    d.fill(WALL).ink(1.1).rect(5, 7, 9, 9)
    d.fill("#9cc3e6").circle(22, 21, 5)
    d.ink(1.0, [1.5, 1.5]).line(18, 8, 13, 23)


def _images(d):
    d.fill(LIGHT).ink(1.2).rect(7, 4, 22, 17, 1.5)
    d.fill(PAPER).rect(3, 9, 22, 18, 1.5)
    d.fill("#9ccc7a").shape((5, 25), (12, 16), (17, 21), (20, 18), (23, 25))
    d.fill("#e8c45a").pen("#e8c45a", 1.0).circle(19, 13, 2.2)
    d.ink()


def _export_image(d):
    """(0.329) An image of the view: a framed picture of a house, an arrow out of it."""
    d.fill(LIGHT).ink(1.2).rect(3, 6, 22, 19, 1.5)
    d.fill("#9cc3e6").pen("#9cc3e6", 1.0).rect(4.5, 7.5, 19, 9)
    d.fill("#9ccc7a").pen("#9ccc7a", 1.0).rect(4.5, 19, 19, 4.5)
    d.fill(WALL).ink(1.1).shape((9, 21), (9, 15), (14, 11), (19, 15), (19, 21))
    d.fill(PAPER).rect(12.5, 16.5, 3, 4.5)
    d.blue(2.0).arrow(22, 22, 29, 29, 4.5)
    d.ink()


def _element_hatches(d):
    """(0.331) One element's own hatch: a wall's cut hatched in blue among plain ones, a pencil over it."""
    d.fill(STONE).ink(1.2).rect(3, 9, 7, 16)
    d.fill(STONE).rect(22, 9, 7, 16)
    d.fill(PAPER).rect(11, 9, 10, 16)
    d.p.save()
    d.p.setClipRect(QtCore.QRectF(11, 9, 10, 16))
    for k in range(-4, 3):
        d.blue(1.1).line(11 + k * 4, 25, 27 + k * 4, 9)
    d.p.restore()
    d.ink(1.2).fill(None).rect(11, 9, 10, 16)
    d.fill("#e8c45a").ink(1.0).shape((19, 4), (22, 1), (29, 8), (26, 11))
    d.ink()


def _reset_patterns(d):
    """(0.332) A face's tiles put back: a tiled square, a turning arrow over it."""
    d.fill(LIGHT).ink(1.2).rect(3, 7, 20, 20)
    d.ink(0.9)
    for k in (8, 13, 18):
        d.line(k, 7, k, 27)
        d.line(3, k + 4, 23, k + 4)
    d.blue(2.0).fill(None)
    d.p.drawArc(QtCore.QRectF(15, 3, 13, 13), 30 * 16, 270 * 16)
    d.blue(2.0).arrow(27, 12, 27.5, 7.5, 4.0)
    d.ink()


def _iso(d):
    _cube(d, 16, 17, 11)


def _keynote_table(d):
    d.fill(PAPER).ink(1.2).rect(3, 6, 26, 20, 1.5)
    d.line(3, 12, 29, 12)
    d.line(13, 6, 13, 26)
    for y in (17, 22):
        d.ink(0.9).line(3, y, 29, y)
    d.fill(BLUE).pen(BLUE, 1.0).rect(4.5, 7.5, 7, 3.5, 1)
    d.ink()


def _last_section(d):
    d.fill(STONE).ink(1.1).rect(4, 10, 24, 12)
    d.blue(1.8, [4, 2]).line(16, 3, 16, 29)
    d.blue(1.8)
    d.arrow(16, 4, 23, 4, 3.5)
    d.arrow(16, 28, 23, 28, 3.5)


def _materials(d):
    grad = QtGui.QRadialGradient(_pt(12.5, 12), 14)
    grad.setColorAt(0.0, QtGui.QColor("#ffffff"))
    grad.setColorAt(0.5, QtGui.QColor("#d8a07e"))
    grad.setColorAt(1.0, QtGui.QColor("#8a4f35"))
    d.p.setBrush(grad)
    d.ink(1.2).circle(16, 16, 11)


def _missing_data(d):
    d.fill(PAPER).ink(1.2).rect(3, 5, 22, 22, 1.5)
    for y in (11, 16, 21):
        d.ink(1.0).line(6, y, 22, y)
    d.fill(RED).pen(RED, 1.0).circle(24, 23, 6)
    d.text(18, 17, 12, 12, "!", colour=PAPER, size=10)


def _moments(d):
    d.fill(STONE).ink(1.2).rect(3, 7, 26, 4)
    d.fill(INK).shape((3, 11), (1, 15), (5, 15))
    d.shape((29, 11), (27, 15), (31, 15))
    d.blue(1.6).fill("#dce8ff")
    path = QtGui.QPainterPath(_pt(3, 18))
    path.quadTo(16, 36, 29, 18)
    path.closeSubpath()
    d.p.drawPath(path)


def _mouse_revit(d):
    _mouse(d)
    d.blue(1.4)
    d.arrow(3, 29, 3, 24, 2.5)
    d.arrow(3, 29, 8, 29, 2.5)
    d.arrow(29, 29, 29, 24, 2.5)
    d.arrow(29, 29, 24, 29, 2.5)


def _mouse_sketchup(d):
    _mouse(d)
    d.blue(1.6).fill(None)
    d.p.drawArc(QtCore.QRectF(2, 18, 28, 12), 200 * 16, 140 * 16)
    d.arrow(26.5, 28.2, 28.6, 26.6, 3)


def _window_in(d, dark):
    """(0.338) A small window of the program — its header bar dark, its body light or dark."""
    d.fill("#2a2f36" if dark else PAPER).ink(1.2).rect(3, 6, 26, 20, 2)
    d.fill("#1f2a37").pen("#1f2a37", 1.0).rect(3.6, 6.6, 24.8, 4.4, 1.5)
    d.ink(1.2).fill(None).rect(3, 6, 26, 20, 2)


def _theme_light(d):
    _window_in(d, False)
    d.fill("#f2c94c").pen("#d39e1a", 1.0).circle(16, 18.5, 3.6)         # a sun
    for k in range(8):
        a = k * math.pi / 4
        d.pen("#d39e1a", 1.2).line(16 + 5.2 * math.cos(a), 18.5 + 5.2 * math.sin(a),
                                   16 + 6.6 * math.cos(a), 18.5 + 6.6 * math.sin(a))


def _theme_dark(d):
    _window_in(d, True)
    path = QtGui.QPainterPath()                                          # a moon
    path.addEllipse(QtCore.QPointF(16, 18.5), 5.2, 5.2)
    bite = QtGui.QPainterPath()
    bite.addEllipse(QtCore.QPointF(18.6, 16.4), 4.4, 4.4)
    d.p.setPen(QtCore.Qt.PenStyle.NoPen)
    d.p.setBrush(QtGui.QColor("#f0b44c"))
    d.p.drawPath(path.subtracted(bite))


def _export_model(d):
    """(0.348) The model in 3D out to a file: a coloured cube, an arrow out of it."""
    d.ink(1.2)
    _cube(d, 13, 15, 9, colours=("#f2d7b8", "#c98f62", "#e3b48d"))
    d.blue(2.0).arrow(21, 21, 29, 29, 4.5)
    d.ink()


def _export_presentation(d):
    """(0.362) The model for the ArqSynth Presentation: a slide with a house on it and a play mark, an arrow out."""
    d.fill(LIGHT).ink(1.2).rect(2, 4, 23, 17, 2)
    d.fill("#e3b48d").ink(1.0).shape((6, 17), (6, 12), (10.5, 8), (15, 12), (15, 17))
    d.fill(BLUE).pen(BLUE, 1.0).shape((18, 9.5), (18, 15.5), (22.5, 12.5))
    d.fill().blue(2.0).arrow(17, 22, 29, 29, 4.5)
    d.ink()


def _presentation_panel(d):
    """(0.363) The scenes of the presentation: the first one large (a house on it, its star), the next ones in a row
    below."""
    d.fill("#ffffff").ink(1.2).rect(3, 2, 26, 17, 2)
    d.fill("#e3b48d").ink(1.0).shape((7, 16), (7, 11), (11.5, 7), (16, 11), (16, 16))
    star = [(24.0 + (3.8 if k % 2 == 0 else 1.6) * math.sin(math.radians(36 * k)),
             8.5 - (3.8 if k % 2 == 0 else 1.6) * math.cos(math.radians(36 * k))) for k in range(10)]
    d.fill(BLUE).pen(BLUE, 0.8).shape(*star)
    for x in (3, 12.5, 22):
        d.fill(LIGHT).ink(1.0).rect(x, 22, 7, 6.5, 1)
    d.ink()


def _panorama(d):
    """(0.368) A 360° panorama: a wide picture (a horizon and a sun), a turning arrow round it."""
    d.fill("#dcebfa").ink(1.1).rect(3, 8, 26, 13, 1.5)
    d.fill("#cfe3c4").ink(0.9).shape((3.5, 20.5), (3.5, 16), (10, 13.5), (16, 16.5), (22, 13), (28.5, 16),
                                     (28.5, 20.5))
    d.fill("#f2b84b").pen("#f2b84b", 0.8).circle(22, 11.5, 1.8)
    d.fill().blue(1.6)
    curve = [(16 + 13 * math.cos(math.radians(a)), 22 + 4.5 * math.sin(math.radians(a))) for a in range(200, 341, 20)]
    for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
        d.line(x0, y0, x1, y1)
    d.fill(BLUE).pen(BLUE, 1.0).shape((27.0, 24.5), (30.5, 25.5), (27.5, 28.0))
    d.ink()


def _import_model(d):
    """(0.351) A 3D model in from a file: an arrow into a coloured cube."""
    d.ink(1.2)
    _cube(d, 19, 17, 9, colours=("#f2d7b8", "#c98f62", "#e3b48d"))
    d.blue(2.0).arrow(3, 3, 11, 11, 4.5)
    d.ink()


def _symbol_styles(d):
    """(0.360) The symbols' generator: a section's head (a circle, its arrow) over a dash-dot line."""
    d.ink(1.0, dash=(3, 1.5, 1, 1.5)).line(3, 24, 29, 24)
    d.fill("#ffffff").ink(1.3).circle(16, 15, 7)
    d.fill(BLUE).pen(BLUE, 1.0).shape((16, 2), (12, 8), (20, 8))
    d.ink()


def _wall_gap(d, faces):
    """(0.361) Two walls in plan, their axes dash-dot, a wall's relation between them — from axis to axis, or from
    face to face."""
    d.fill(WALL).ink(1.0)
    d.rect(3, 4, 7, 24)
    d.rect(22, 4, 7, 24)
    d.fill().ink(0.8, dash=(4, 1.5, 1, 1.5))
    d.line(6.5, 2, 6.5, 30)
    d.line(25.5, 2, 25.5, 30)
    x0, x1 = (10.0, 22.0) if faces else (6.5, 25.5)
    d.pen(GREEN, 1.6)
    d.arrow((x0 + x1) / 2, 16, x0, 16, 3.5)
    d.arrow((x0 + x1) / 2, 16, x1, 16, 3.5)
    d.ink()


def _dims_axes(d):
    _wall_gap(d, faces=False)


def _dims_faces(d):
    _wall_gap(d, faces=True)


def _room_program(d):
    """(0.357) The programme: a list of rooms (a sheet with lines), one dragged out to a room."""
    _sheet(d, 4, 4, 15, 21, 4)
    d.ink(1.0)
    for y in (11, 15, 19):
        d.line(7, y, 15, y)
    d.fill(LIGHT).ink(1.2).rect(17, 15, 12, 12, 1)
    d.blue(2.0).arrow(13, 15, 23, 21, 3.5)
    d.ink()


def _render(d):
    """(0.343) A camera, a sun over it: the realistic render."""
    d.fill("#f2c94c").pen("#d39e1a", 1.0).circle(24, 8, 3.2)
    for k in range(8):
        a = k * math.pi / 4
        d.pen("#d39e1a", 1.0).line(24 + 4.4 * math.cos(a), 8 + 4.4 * math.sin(a),
                                   24 + 5.6 * math.cos(a), 8 + 5.6 * math.sin(a))
    d.fill(LIGHT).ink(1.3).rect(3, 13, 22, 14, 2)
    d.fill(LIGHT).rect(8, 10, 7, 3, 1)
    d.fill("#9cc3d9").ink(1.3).circle(14, 20, 4.5)
    d.fill(BLUE).pen(BLUE, 1.0).circle(14, 20, 1.6)


def _canvas_dark(d):
    """(0.341) A view with a dark background, a plan drawn in it light."""
    d.fill("#14284a").ink(1.2).rect(3, 5, 26, 22, 2)         # (colours, not greys: the same in both themes)
    d.fill(None).pen("#ffe6a0", 1.4).lines((9, 21), (9, 11), (16, 11), (16, 15), (23, 15), (23, 21), (9, 21))
    d.pen("#5b9cff", 1.4).line(12, 21, 14.5, 21)


def _new_note(d):
    d.fill("#fff6c9").ink(1.2).shape((4, 5), (24, 5), (24, 21), (12, 21), (7, 26), (7, 21), (4, 21))
    for y in (10, 15):
        d.ink(1.0).line(8, y, 20, y)
    _plus(d, 24, 22, 3.5)


def _next_view(d):
    _tab(d)
    d.blue(2.0).arrow(9, 18, 23, 18, 4.5)


def _only_active(d):
    d.p.setOpacity(0.35)
    _storeys(d, 3, lit=None)
    d.p.setOpacity(1.0)
    _storeys(d, 1, y0=15, lit=0)
    d.fill("#9cc3e6").ink(1.1).rect(22, 11, 7, 7, 1)


def _open_shared(d):
    _folder(d)
    d.blue(1.4)
    d.line(13, 20, 19, 17)
    d.line(19, 17, 24, 21)
    for x, y in ((13, 20), (19, 17), (24, 21)):
        d.fill(BLUE).circle(x, y, 2)


def _panels(d):
    d.fill(PAPER).ink(1.2).rect(3, 5, 26, 22, 1.5)
    d.fill("#dce8ff").rect(3, 5, 7, 22)
    d.rect(23, 5, 6, 22)
    d.fill(LIGHT).rect(10, 5, 13, 4)


def _phase(d):
    for k, (x, w, colour) in enumerate(((4, 12, "#c9c7c1"), (10, 13, "#9cc3e6"), (17, 12, "#9ccc7a"))):
        d.fill(colour).ink(1.1).rect(x, 6 + k * 7, w, 5, 1.5)
    d.blue(1.4).arrow(4, 28, 28, 28, 3)


def _prev_view(d):
    _tab(d)
    d.blue(2.0).arrow(23, 18, 9, 18, 4.5)


def _remove_electrical_proposal(d):
    _bolt(d, -4, 0)
    _cross(d, 24, 23, 4)


def _remove_water_proposal(d):
    _drop(d, 13, 15)
    _cross(d, 24, 23, 4)


def _repeat(d):
    _storeys(d, 3, lit=0)
    d.blue(1.4)
    d.arrow(25, 9, 25, 15, 3)
    d.arrow(25, 16, 25, 22, 3)


def _reserve_views(d):
    _sheet(d, 4, 3, 17, 24)
    d.fill("#f3d27a").ink(1.2).rect(16, 17, 12, 10, 1.5)
    d.fill(None).p.drawArc(QtCore.QRectF(18, 11, 8, 10), 0, 180 * 16)
    d.fill(INK).circle(22, 22, 1.2)


def _roof_profile(d):
    d.fill(STONE).ink(1.2).shape((3, 18), (16, 7), (29, 18), (29, 21), (16, 10), (3, 21))
    d.fill(LIGHT).rect(6, 21, 20, 8)
    d.blue(1.6).fill(None)
    path = QtGui.QPainterPath(_pt(3, 15))
    path.cubicTo(10, 3, 22, 3, 29, 15)
    d.p.drawPath(path)


def _same_type(d):
    for y in (6, 20):
        d.fill(WALL).ink(1.1).rect(4, y, 15, 6)
    d.blue(2.0)
    d.line(22, 13, 29, 13)
    d.line(22, 18, 29, 18)


def _share(d):
    _folder(d)
    d.blue(1.8).arrow(15, 21, 27, 6, 4)


def _show_analytical(d):
    d.blue(1.6)
    d.line(6, 26, 6, 8)
    d.line(26, 26, 26, 8)
    d.line(6, 8, 26, 8)
    d.line(6, 17, 26, 17)
    for x, y in ((6, 8), (26, 8), (6, 17), (26, 17)):
        d.fill(PAPER).circle(x, y, 2.2)
    d.ink(1.4)
    for x in (6, 26):
        d.fill(INK).shape((x, 26), (x - 3, 30), (x + 3, 30))


def _site_location(d):
    d.fill("#9ccc7a").ink(1.1).shape((2, 26), (10, 20), (30, 22), (24, 29), (4, 29))
    d.fill(RED).pen(RED, 1.0)
    path = QtGui.QPainterPath(_pt(16, 24))
    path.cubicTo(10, 15, 9, 12, 9, 10)
    path.cubicTo(9, 2, 23, 2, 23, 10)
    path.cubicTo(23, 12, 22, 15, 16, 24)
    d.p.drawPath(path)
    d.fill(PAPER).circle(16, 10, 2.8)
    d.ink()


def _slopes(d):
    d.fill("#b9d99b").ink(1.2).shape((3, 27), (3, 20), (29, 8), (29, 27))
    d.blue(1.6).arrow(10, 21, 22, 15.5, 3.5)
    d.text(13, 22, 16, 8, "%", colour=INK, size=8)


def _storey_down(d):
    _storeys(d, 3, lit=2)
    d.blue(1.6).arrow(26, 5, 26, 24, 3.5)


def _storey_new(d):
    _storeys(d, 2, y0=13, step=9)
    d.blue(1.8, [3, 2]).line(9, 6, 21, 6)
    _plus(d, 26, 7, 3.5)


def _storey_up(d):
    _storeys(d, 3, lit=0)
    d.blue(1.6).arrow(26, 25, 26, 6, 3.5)


def _sync(d):
    d.fill(LIGHT).ink(1.2)
    path = QtGui.QPainterPath(_pt(7, 22))
    path.cubicTo(1, 22, 1, 13, 7.5, 13)
    path.cubicTo(8.5, 5, 20, 4.5, 21.5, 11)
    path.cubicTo(29, 11, 30, 22, 23, 22)
    path.closeSubpath()
    d.p.drawPath(path)
    d.blue(1.6).fill(None)
    d.p.drawArc(QtCore.QRectF(11, 12, 10, 10), 30 * 16, 150 * 16)
    d.p.drawArc(QtCore.QRectF(11, 12, 10, 10), 210 * 16, 150 * 16)
    d.arrow(20.3, 14.5, 20.6, 16.5, 2.5)
    d.arrow(11.7, 19.5, 11.4, 17.5, 2.5)


def _top(d):
    d.fill(LIGHT).ink(1.2).rect(5, 9, 22, 19)
    d.line(5, 9, 16, 18.5)
    d.line(27, 9, 16, 18.5)
    d.line(5, 28, 16, 18.5)
    d.line(27, 28, 16, 18.5)
    d.blue(1.6).arrow(16, 1, 16, 7, 3)


def _type_lists(d):
    for k, colour in enumerate((WALL, STONE, "#9cc3e6")):
        y = 6 + k * 8
        d.fill(colour).ink(1.1).rect(4, y, 7, 5, 1)
        d.ink(1.2).line(14, y + 2.5, 28, y + 2.5)
    d.ink()


def _types(d):
    for k, colour in enumerate(("#dfe6f1", "#e9edf3", PAPER)):
        d.fill(colour).ink(1.1).rect(4 + k * 4, 4 + k * 4, 18, 16, 2)
    d.fill(WALL).rect(15, 17, 8, 4)
    d.text(13, 11, 12, 7, "T", size=7)


def _typical(d):
    _storeys(d, 3, lit=None)
    d.blue(2.0)
    d.line(24, 12, 30, 12)
    d.line(24, 17, 30, 17)


def _view3d_new(d):
    _cube(d, 13, 17, 9)
    _plus(d, 25, 8, 3.5)


def _wall_plan(d, ring, closed=True):
    """(0.374) A wall in plan along `ring`: a thick terracotta band with its outline."""
    path = QtGui.QPainterPath(_pt(*ring[0]))
    for xy in ring[1:]:
        path.lineTo(_pt(*xy))
    if closed:
        path.closeSubpath()
    for colour, width in ((INK, 6.0), (WALL, 3.6)):
        pen = QtGui.QPen(QtGui.QColor(colour), width)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.MiterJoin)
        d.p.setPen(pen)
        d.p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        d.p.drawPath(path)


def _wall_rect(d):
    _wall_plan(d, [(6, 8), (26, 8), (26, 24), (6, 24)])


def _wall_circle(d):
    _wall_plan(d, [(16 + 10 * math.cos(math.radians(a)), 16 + 10 * math.sin(math.radians(a))) for a in range(0, 360, 20)])


def _wall_arc(d):
    _wall_plan(d, [(16 + 11 * math.cos(math.radians(a)), 24 - 11 * math.sin(math.radians(a))) for a in range(0, 181, 15)],
               closed=False)


def _wall_face(d):
    d.ink(1.2).fill("#e3e6ea")
    d.shape((4, 22), (12, 10), (28, 10), (20, 22))
    _wall_plan(d, [(4, 22), (12, 10), (28, 10), (20, 22)])
    d.blue(1.6).arrow(25, 27, 21, 22)


def _wall_wand(d):
    d.ink(1.0)
    d.line(4, 10, 28, 10)
    d.line(4, 17, 28, 17)
    d.blue(1.2, dash=[2, 2]).fill()
    d.rect(9, 6, 13, 15)
    d.pen("#8a5a2b", 2.2).line(20, 28, 28, 20)
    d.pen("#f2c230", 1.4).line(28, 20, 29.5, 18.5)


def _rooms_identify(d):
    d.ink(2.0).fill()
    d.rect(4, 6, 24, 20)
    d.line(16, 6, 16, 26)
    d.text(4, 6, 12, 20, "1")
    d.text(16, 6, 12, 20, "2")


def _swatch(name):
    """(0.374) A study palette's icon: its bar, ribbon and panel colours, its accent."""
    def draw(d):
        from .theme import STUDY
        p = STUDY[name]
        d.ink(1.0).fill(p["base"])
        d.rect(4, 4, 24, 24, 3)
        d.fill(p["ribbon"])
        d.rect(4, 9, 24, 7)
        d.fill(p["panel"])
        d.rect(4, 16, 9, 12)
        d.pen(p["accent"], 2.4).line(14, 9.5, 27, 9.5)
    return draw


def _theme_studio(d):
    for k, colour in enumerate(("#d9c5ae", "#cbbc9e", "#bfc4c0", "#45413e", "#1b1b1b")):
        d.ink(1.0).fill(colour)
        d.circle(16 + 9 * math.cos(math.radians(90 + k * 72)), 16 - 9 * math.sin(math.radians(90 + k * 72)), 4.5)
    d.blue(1.6).fill("#2f75fd")
    d.circle(16, 16, 3)


def _areas(d):
    d.ink(1.4).fill(LIGHT)
    d.rect(5, 5, 22, 22)
    d.text(5, 8, 22, 16, "m²", colour=INK, size=10)


DRAWN = {"wall_rect": _wall_rect, "wall_circle": _wall_circle, "wall_arc": _wall_arc, "wall_face": _wall_face,
         "wall_wand": _wall_wand, "rooms_identify": _rooms_identify, "areas": _areas,             # (0.374)
         "theme_bege": _swatch("bege"), "theme_revit": _swatch("revit"), "theme_pedra": _swatch("pedra"),
         "theme_escuro": _swatch("escuro"), "theme_grafite": _swatch("grafite"), "theme_studio": _theme_studio,
         "ai_install": _ai_install, "box": _box, "box_selection": _box_selection, "cad_links": _cad_links,
         "check_ids": _check_ids, "check_ifc": _check_ifc, "clashes": _clashes, "close_view": _close_view,
         "verify_settings": _verify_settings, "verify_panel": _verify_panel,                           # (0.417)
         "cloud_links": _cloud_links, "component_close": _component_close, "component_edit": _component_edit,
         "component_make": _component_make, "delete": _delete, "dimension_style": _dimension_style,
         "electrical_check": _electrical_check, "element_hatches": _element_hatches, "export_image": _export_image,
         "export_model": _export_model, "import_model": _import_model, "room_program": _room_program,
         "export_presentation": _export_presentation, "presentation_panel": _presentation_panel,
         "panorama": _panorama,
         "symbol_styles": _symbol_styles, "dims_axes": _dims_axes, "dims_faces": _dims_faces,
         "front": _front,
         "give_back": _give_back,
         "graphic_styles": _graphic_styles, "view_styles": _view_styles, "patterns": _patterns,
         "grid_generate": _grid_generate, "grid_settings": _grid_settings,
         "group_make": _group_make, "group_ungroup": _group_ungroup, "images": _images, "iso": _iso,
         "keynote_table": _keynote_table, "last_section": _last_section, "materials": _materials,
         "missing_data": _missing_data, "moments": _moments, "mouse_revit": _mouse_revit,
         "mouse_sketchup": _mouse_sketchup, "new_note": _new_note, "next_view": _next_view,
         "only_active": _only_active, "open_shared": _open_shared, "panels": _panels, "phase": _phase,
         "prev_view": _prev_view, "remove_electrical_proposal": _remove_electrical_proposal,
         "remove_water_proposal": _remove_water_proposal, "repeat": _repeat, "reserve_views": _reserve_views,
         "reset_patterns": _reset_patterns,
         "roof_profile": _roof_profile, "same_type": _same_type, "share": _share,
         "show_analytical": _show_analytical, "site_location": _site_location, "slopes": _slopes,
         "storey_down": _storey_down, "storey_new": _storey_new, "storey_up": _storey_up, "sync": _sync,
         "theme_dark": _theme_dark, "theme_light": _theme_light, "canvas_dark": _canvas_dark, "render": _render,
         "top": _top, "type_lists": _type_lists, "types": _types, "typical": _typical, "view3d_new": _view3d_new}


def icon(name):
    """The icon drawn for a command of the ribbon, or None."""
    draw = DRAWN.get(name)
    if draw is None:
        return None
    d = _Pen()
    draw(d)
    return d.done()
