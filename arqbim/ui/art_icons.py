"""(0.535, the owner: «organize também os ícones para serem como dos revit», then «Sim, redesenhar») The ribbon's
pictures as Revit draws its own — not copies of them: each object seen from above at a three-quarter angle (isometric),
its faces in three tones of its material (the top light, the left middle, the right dark), a thin dark outline; the
marks (arrows, points, the work plane) in blue, what is new in yellow. Drawn in code (nothing to ship or license),
for the light theme: theme.icon() turns their ink and white for the dark one, their materials stay.

A picture is a list of paths in its own units (an isometric point is (x − y)·cos 30°, (x + y)·sin 30° − z); it is fitted
whole into the 32 px square, so each one is drawn at its own scale. icon(name): the picture's QIcon, or None for a
command not drawn here (its older icon stays)."""

import math

from PySide6 import QtCore, QtGui

from . import theme

C30, S30 = math.cos(math.radians(30)), 0.5
BOX = 27.0                      # px of the 32 the picture fills (its outline round it)
OUTLINE, THIN = 1.15, 0.7       # px: the outline, the details


def _colour(key):
    """A colour of theme.ART by its name (a material: its top's tone, for a flat fill) or written («#rrggbb»)."""
    value = theme.ART.get(key, key) if isinstance(key, str) else key
    return QtGui.QColor(value[0] if isinstance(value, tuple) else value)


class Art:
    """A picture being drawn: its paths, in order, each with its fill and its line."""

    def __init__(self):
        self.items = []

    # ------------------------------------------------------------ in the picture's own plane
    def path(self, path, fill=None, line="ink", width=OUTLINE, dash=None):
        self.items.append((path, fill, line, width, dash))

    def poly(self, points, fill=None, line="ink", width=OUTLINE, closed=True, dash=None):
        path = QtGui.QPainterPath(QtCore.QPointF(*points[0]))
        for x, y in points[1:]:
            path.lineTo(x, y)
        if closed:
            path.closeSubpath()
        self.path(path, fill if closed else None, line, width, dash)

    def line(self, a, b, line="ink", width=OUTLINE, dash=None):
        self.poly([a, b], None, line, width, closed=False, dash=dash)

    def circle(self, centre, r, fill=None, line="ink", width=OUTLINE):
        path = QtGui.QPainterPath()
        path.addEllipse(QtCore.QPointF(*centre), r, r)
        self.path(path, fill, line, width)

    def arrow(self, a, b, colour="blue", width=1.6, head=0.32):
        """A line from a to b with its head at b (head: of its length)."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        ux, uy = dx / n, dy / n
        h = n * head
        self.line(a, b, colour, width)
        left = (b[0] - ux * h - uy * h * 0.6, b[1] - uy * h + ux * h * 0.6)
        right = (b[0] - ux * h + uy * h * 0.6, b[1] - uy * h - ux * h * 0.6)
        self.poly([left, b, right], colour, colour, width * 0.6)

    # ------------------------------------------------------------ in space, seen isometric
    @staticmethod
    def iso(x, y, z):
        return (x - y) * C30, (x + y) * S30 - z

    def face(self, points3d, fill, line="ink", width=OUTLINE, dash=None):
        self.poly([self.iso(*p) for p in points3d], fill, line, width, dash=dash)

    def line3(self, a, b, line="ink", width=THIN, dash=None):
        self.line(self.iso(*a), self.iso(*b), line, width, dash)

    def box(self, x, y, z, dx, dy, dz, material, line="ink"):
        """A box: its right (+x), left (+y) and top faces, in its material's dark, middle and light tones."""
        top, left, right = theme.ART[material] if isinstance(material, str) else material
        x1, y1, z1 = x + dx, y + dy, z + dz
        self.face([(x1, y, z), (x1, y1, z), (x1, y1, z1), (x1, y, z1)], right, line)
        self.face([(x, y1, z), (x1, y1, z), (x1, y1, z1), (x, y1, z1)], left, line)
        self.face([(x, y, z1), (x1, y, z1), (x1, y1, z1), (x, y1, z1)], top, line)

    # ------------------------------------------------------------ the picture
    def pixmap(self):
        rect = QtCore.QRectF()
        for path, *_rest in self.items:
            r = path.controlPointRect()
            rect = r if rect.isNull() else rect.united(r)
        scale = BOX / max(rect.width(), rect.height(), 1e-6)
        fit = QtGui.QTransform()
        fit.translate(16.0, 16.0)
        fit.scale(scale, scale)
        fit.translate(-rect.center().x(), -rect.center().y())
        pm = QtGui.QPixmap(64, 64)
        pm.fill(QtCore.Qt.GlobalColor.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.scale(2.0, 2.0)
        for path, fill, line, width, dash in self.items:
            p.setBrush(QtGui.QBrush(_colour(fill)) if fill is not None else QtCore.Qt.BrushStyle.NoBrush)
            if line is None:
                p.setPen(QtCore.Qt.PenStyle.NoPen)
            else:
                pen = QtGui.QPen(_colour(line), width)
                pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
                pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
                if dash:
                    pen.setDashPattern(dash)
                p.setPen(pen)
            p.drawPath(fit.map(path))
        p.end()
        pm.setDevicePixelRatio(2.0)
        return pm


# ------------------------------------------------------------ Modelagem (Revit's Modify)

def _select(a):
    a.poly([(9, 4), (9, 26), (14, 21), (18, 29), (21, 27.5), (17, 19.5), (24, 19.5)], "paper")


def _move(a):
    a.box(-0.7, -0.7, 0, 1.4, 1.4, 1.2, "concrete")
    cx, cy = a.iso(0, 0, 0.6)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        a.arrow((cx + dx * 1.3, cy + dy * 1.3), (cx + dx * 3.2, cy + dy * 3.2), width=1.5, head=0.4)


def _copy(a):
    ghost = [(0, 0, 0), (1.6, 0, 0), (1.6, 1.6, 0), (0, 1.6, 0)]
    a.face([(x, y, 1.4) for x, y, _z in ghost], None, "detail", THIN, dash=[3, 2])
    for x, y, _z in ghost:
        a.line3((x, y, 0), (x, y, 1.4), "detail", THIN, dash=[3, 2])
    a.face(ghost, None, "detail", THIN, dash=[3, 2])
    a.box(2.6, 1.0, 0, 1.6, 1.6, 1.4, "concrete")
    a.arrow(a.iso(1.0, 0.4, 2.2), a.iso(3.0, 1.2, 2.4), width=1.3, head=0.35)


def _rotate(a):
    a.box(-0.8, -0.8, 0, 1.6, 1.6, 1.3, "concrete")
    path = QtGui.QPainterPath()
    rect = QtCore.QRectF(-2.6, -2.2, 5.2, 3.0)
    path.arcMoveTo(rect, 200)
    path.arcTo(rect, 200, 250)
    a.path(path, None, "blue", 1.4)
    ex, ey = rect.center().x(), rect.top()               # (the arc ends at its top, going left: the head points left)
    a.poly([(ex + 0.5, ey - 0.5), (ex - 0.6, ey), (ex + 0.5, ey + 0.5)], "blue", "blue", 0.8)


def _mirror(a):
    a.line((16, 4), (16, 28), "ink", THIN, dash=[5, 2, 1, 2])
    a.poly([(5, 24), (13, 24), (13, 9)], "concrete")
    a.poly([(27, 24), (19, 24), (19, 9)], None, "blue", OUTLINE, dash=[3, 2])
    a.arrow((11, 6), (21, 6), width=1.2, head=0.25)


def _line(a):
    a.line((5, 27), (20, 12), "ink", 2.0)
    a.circle((5, 27), 2.2, "blue", "blue", 0.6)
    a.poly([(20, 12), (26, 4), (30, 8), (23, 15)], "yellow")
    a.poly([(20, 12), (21.5, 10.2), (23, 15)], "ink", "ink", 0.6)


def _arc(a):
    path = QtGui.QPainterPath()
    rect = QtCore.QRectF(4, 6, 24, 24)
    path.arcMoveTo(rect, 160)
    path.arcTo(rect, 160, -140)
    a.path(path, None, "ink", 2.0)
    for angle in (160, 20):
        a.circle((16 + 12 * math.cos(math.radians(angle)), 18 - 12 * math.sin(math.radians(angle))), 2.1, "blue",
                 "blue", 0.6)
    a.circle((16, 18), 1.3, "detail", "detail", 0.5)


def _rectangle(a):
    a.poly([(4, 8), (28, 8), (28, 24), (4, 24)], "concrete")
    a.circle((4, 24), 2.3, "blue", "blue", 0.6)
    a.circle((28, 8), 2.3, "blue", "blue", 0.6)


def _circle(a):
    a.circle((16, 16), 12, "concrete")
    a.line((16, 16), (26.4, 10), "blue", 1.4)
    a.circle((16, 16), 1.8, "blue", "blue", 0.6)


def _push_pull(a):
    a.box(0, 0, 0, 3, 3, 1.2, "concrete")
    a.face([(0, 0, 1.2), (3, 0, 1.2), (3, 3, 1.2), (0, 3, 1.2)], "yellow")
    a.arrow(a.iso(1.5, 1.5, 1.2), a.iso(1.5, 1.5, 4.0), width=1.8, head=0.38)


def _tape(a):
    a.poly([(3, 10), (17, 10), (17, 24), (3, 24)], "yellow")
    a.circle((10, 17), 3, "paper")
    a.poly([(17, 20), (29, 20), (29, 24), (17, 24)], "concrete")
    for x in (20, 23, 26):
        a.line((x, 20), (x, 22), "ink", THIN)
    a.line((3, 5), (29, 5), "detail", 1.2, dash=[3, 2])


def _dimension(a):
    a.line((5, 12), (5, 26), "ink", THIN)
    a.line((27, 12), (27, 26), "ink", THIN)
    a.line((5, 16), (27, 16), "ink", 1.2)
    a.line((3, 18), (7, 14), "ink", 1.6)
    a.line((25, 18), (29, 14), "ink", 1.6)
    a.poly([(11, 6), (21, 6), (21, 11), (11, 11)], "paper", "blue", 1.0)


def _component_make(a):
    a.box(0, 0, 0, 2.4, 2.4, 2.0, "wood")
    _spark(a, a.iso(2.6, -0.4, 3.4), 1.3)


def _group_make(a):
    a.box(0, 0, 0, 1.6, 1.6, 1.4, "concrete")
    a.box(2.2, 0.6, 0, 1.4, 1.4, 2.2, "wood")
    a.poly([a.iso(-0.6, -0.6, 3.0), a.iso(4.3, -0.6, 3.0), a.iso(4.3, 2.6, -0.4), a.iso(-0.6, 2.6, -0.4)], None,
           "blue", THIN, dash=[3, 2])


def _spark(a, centre, r):
    """A small yellow four-point star: done at once, new."""
    x, y = centre
    a.poly([(x, y - r), (x + r * 0.28, y - r * 0.28), (x + r, y), (x + r * 0.28, y + r * 0.28), (x, y + r),
            (x - r * 0.28, y + r * 0.28), (x - r, y), (x - r * 0.28, y - r * 0.28)], "yellow", "ink", 0.5)


# ------------------------------------------------------------ Arquitetura (Revit's Architecture ▸ Build…)

def _wall(a):
    a.box(0, 0, 0, 6, 1, 3.2, "wall")
    for z in (0.8, 1.6, 2.4):                                     # its courses of bricks, on its long face
        a.line3((0, 1, z), (6, 1, z), "detail", THIN)
    for k, z in enumerate((0.0, 0.8, 1.6, 2.4)):
        for x in ((1.5, 3.0, 4.5) if k % 2 else (0.75, 2.25, 3.75, 5.25)):
            a.line3((x, 1, z), (x, 1, z + 0.8), "detail", THIN)
    a.line3((0, 0.3, 3.2), (6, 0.3, 3.2), "detail", THIN)         # (its finish, on top)


def _host(a):
    """The wall a door or a window is in."""
    a.box(0, 0, 0, 6, 0.8, 3.4, "wall")


def _door(a):
    _host(a)
    a.face([(2, 0.8, 0), (4, 0.8, 0), (4, 0.8, 2.6), (2, 0.8, 2.6)], theme.ART["wood"][1])
    a.face([(2.25, 0.8, 0.25), (3.75, 0.8, 0.25), (3.75, 0.8, 2.35), (2.25, 0.8, 2.35)], None, "ink", THIN)
    hx, hy = a.iso(3.55, 0.8, 1.3)
    a.circle((hx, hy), 0.22, "yellow", "ink", 0.4)


def _window(a):
    _host(a)
    a.face([(1.6, 0.8, 1.0), (4.4, 0.8, 1.0), (4.4, 0.8, 2.7), (1.6, 0.8, 2.7)], "paper")
    a.face([(1.8, 0.8, 1.15), (4.2, 0.8, 1.15), (4.2, 0.8, 2.55), (1.8, 0.8, 2.55)], theme.ART["glass"][1], "ink",
           THIN)
    a.line3((3.0, 0.8, 1.15), (3.0, 0.8, 2.55), "paper", 1.0)
    a.line3((1.8, 0.8, 1.85), (4.2, 0.8, 1.85), "paper", 1.0)


def _loose_furniture(a):
    for x, y in ((0.1, 0.1), (1.35, 0.1), (0.1, 1.35), (1.35, 1.35)):        # (Revit's «Component»: a chair)
        a.box(x, y, 0, 0.15, 0.15, 1.0, "wood")
    a.box(0, 0, 1.0, 0.25, 1.6, 1.7, "wood")
    a.box(0, 0, 1.0, 1.6, 1.6, 0.25, "wood")


def _column(a):
    a.box(0, 0, 0, 1.8, 1.8, 0.3, "concrete")
    a.box(0.35, 0.35, 0.3, 1.1, 1.1, 4.2, "concrete")
    a.box(0.2, 0.2, 4.5, 1.4, 1.4, 0.3, "concrete")


def _roof(a):
    a.box(0, 0, 0, 5, 3.6, 1.8, "wall")
    a.face([(5, 0, 1.8), (5, 3.6, 1.8), (5, 1.8, 3.4)], theme.ART["wall"][2])
    a.face([(-0.3, -0.3, 1.5), (5.3, -0.3, 1.5), (5.3, 1.8, 3.6), (-0.3, 1.8, 3.6)], theme.ART["roof"][0])
    a.face([(-0.3, 1.8, 3.6), (5.3, 1.8, 3.6), (5.3, 3.9, 1.5), (-0.3, 3.9, 1.5)], theme.ART["roof"][1])
    for x in (1.1, 2.5, 3.9):                                      # (its rows of tiles)
        a.line3((x, 1.8, 3.6), (x, 3.9, 1.5), "detail", THIN)


def _ceiling(a):
    a.box(0, 0, 2.8, 5, 4, 0.25, "concrete")
    for x in (1.667, 3.333):
        a.line3((x, 0, 3.05), (x, 4, 3.05), "detail", THIN)
    a.line3((0, 2, 3.05), (5, 2, 3.05), "detail", THIN)
    a.line3((2.5, 2, 2.8), (2.5, 2, 1.7), "ink", THIN)            # (a light hanging from it)
    lx, ly = a.iso(2.5, 2, 1.7)
    a.poly([(lx - 0.9, ly + 0.7), (lx, ly - 0.2), (lx + 0.9, ly + 0.7)], "yellow", "ink", 0.6)


def _slab(a):
    a.box(0, 0, 0, 6, 4.5, 0.7, "concrete")
    for x in (1.0, 2.5, 4.0, 5.5):                                 # (its section, hatched)
        a.line3((x - 0.5, 4.5, 0.0), (x, 4.5, 0.7), "detail", THIN)


def _curtain_wall(a):
    top, left, right = theme.ART["steel"]
    a.face([(6, 0, 0), (6, 0.35, 0), (6, 0.35, 3.6), (6, 0, 3.6)], right)
    a.face([(0, 0.35, 0), (6, 0.35, 0), (6, 0.35, 3.6), (0, 0.35, 3.6)], theme.ART["glass"][1])
    a.face([(0, 0, 3.6), (6, 0, 3.6), (6, 0.35, 3.6), (0, 0.35, 3.6)], top)
    for x in (2, 4):
        a.line3((x, 0.35, 0), (x, 0.35, 3.6), left, 1.1)
    a.line3((0, 0.35, 1.8), (6, 0.35, 1.8), left, 1.1)
    a.line3((0.5, 0.35, 2.4), (1.4, 0.35, 3.2), "paper", THIN)    # (a gleam on the glass)


def _railing(a):
    a.box(-0.3, -0.4, -0.3, 6.6, 0.8, 0.3, "concrete")
    for x in (0, 2, 4, 6):
        a.box(x - 0.08, -0.08, 0, 0.16, 0.16, 2.2, "steel")
    for k in range(1, 12):
        x = k * 0.5
        if x not in (2.0, 4.0):
            a.line3((x, 0, 0.3), (x, 0, 2.1), theme.ART["steel"][2], THIN)
    a.box(-0.1, -0.12, 2.2, 6.2, 0.24, 0.16, "steel")


def _ramp(a):
    top, left, right = theme.ART["concrete"]
    a.face([(6, 0, 0), (6, 2.5, 0), (6, 2.5, 1.8), (6, 0, 1.8)], right)
    a.face([(0, 2.5, 0), (6, 2.5, 0), (6, 2.5, 1.8)], left)
    a.face([(0, 0, 0), (6, 0, 1.8), (6, 2.5, 1.8), (0, 2.5, 0)], top)
    a.arrow(a.iso(1.2, 1.25, 0.36), a.iso(4.8, 1.25, 1.44), width=1.3, head=0.3)


def _stair(a):
    for i in range(4):
        a.box(i * 1.2, 0, 0, 1.2, 2.4, (i + 1) * 0.8, "wood")


def _room(a):
    a.box(-0.3, -0.3, 0, 5.3, 0.3, 1.2, "wall")
    a.box(-0.3, 0, 0, 0.3, 4, 1.2, "wall")
    a.face([(0, 0, 0), (5, 0, 0), (5, 4, 0), (0, 4, 0)], theme.ART["room"][0], "blue", THIN)
    a.line3((1.8, 2, 0), (3.2, 2, 0), "blue", 1.0)
    a.line3((2.5, 1.3, 0), (2.5, 2.7, 0), "blue", 1.0)


def _storey_new(a):
    a.line((2, 18), (22, 18), "ink", 1.4)
    a.line((2, 24), (22, 24), "detail", THIN, dash=[4, 2])
    a.circle((26, 18), 4.0, "paper")
    path = QtGui.QPainterPath(QtCore.QPointF(26, 18))
    path.arcTo(QtCore.QRectF(22, 14, 8, 8), 90, 90)
    path.closeSubpath()
    path.moveTo(26, 18)
    path.arcTo(QtCore.QRectF(22, 14, 8, 8), 270, 90)
    path.closeSubpath()
    a.path(path, "ink", None)
    _spark(a, (6, 10), 3.2)


def _grid(a):
    a.line((5, 9), (28, 9), "ink", 1.0, dash=[6, 2, 1, 2])
    a.line((23, 4), (23, 28), "ink", 1.0, dash=[6, 2, 1, 2])
    a.circle((4.5, 9), 3.6, "paper")
    a.circle((23, 28.5), 3.6, "paper")
    a.line((3.2, 7.6), (5.8, 10.4), "blue", 1.0)
    a.line((23, 26.8), (23, 30.2), "blue", 1.0)


def _work_plane(a):
    a.face([(0, 0, 0), (5, 0, 0), (5, 5, 0), (0, 5, 0)], theme.ART["glass"][0], "blue", 1.0)
    for k in (1, 2, 3, 4):
        a.line3((k, 0, 0), (k, 5, 0), "blue", 0.5)
        a.line3((0, k, 0), (5, k, 0), "blue", 0.5)
    a.arrow(a.iso(2.5, 2.5, 0), a.iso(2.5, 2.5, 3.2), width=1.5, head=0.3)


# ------------------------------------------------------------ Estrutura (Revit's Structure ▸ Structure, Foundation)

def _beam(a):
    a.box(0, 0, 0, 6, 1.6, 0.25, "steel")
    a.box(0, 0.7, 0.25, 6, 0.2, 1.25, "steel")
    a.box(0, 0, 1.5, 6, 1.6, 0.25, "steel")


def _footing(a):
    a.box(0, 0, 0, 3.6, 3.6, 0.9, "concrete")
    a.box(1.2, 1.2, 0.9, 1.2, 1.2, 2.4, "concrete")


def _propose_structure(a):
    a.box(-0.4, -0.4, -0.3, 5.6, 1.8, 0.3, "concrete")             # (a frame on its slab, proposed at once)
    a.box(0, 0, 0, 1.0, 1.0, 3.4, "concrete")
    a.box(3.8, 0, 0, 1.0, 1.0, 3.4, "concrete")
    a.box(0, 0, 3.4, 4.8, 1.0, 0.9, "concrete")
    _spark(a, a.iso(3.4, -1.6, 5.4), 1.3)


# ------------------------------------------------------------ (0.535, 2.ª leva) the small ones of the three tabs

def _cross(a, centre, r, width=1.8):
    """A red ×: taken away."""
    x, y = centre
    a.line((x - r, y - r), (x + r, y + r), "red", width)
    a.line((x - r, y + r), (x + r, y - r), "red", width)


def _sheet(a, x, y, w, h, rows=3):
    """A sheet of paper with lines of text."""
    a.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], "paper")
    for k in range(rows):
        yy = y + h * (k + 1) / (rows + 1)
        a.line((x + w * 0.18, yy), (x + w * 0.82, yy), "detail", THIN)


def _clipboard(a):
    a.poly([(6, 6), (24, 6), (24, 29), (6, 29)], "wood")
    _sheet(a, 8.5, 9, 13, 17)
    a.poly([(11, 3.5), (19, 3.5), (19, 8), (11, 8)], "concrete")


def _copy_clip(a):
    _clipboard(a)
    a.arrow((29, 2), (21, 12), width=1.6, head=0.35)


def _paste(a):
    _clipboard(a)
    a.arrow((20, 20), (30, 29), width=1.6, head=0.35)


def _paste_storeys(a):
    a.box(0, 0, 0, 4, 3, 0.35, "concrete")
    a.box(0, 0, 2.2, 4, 3, 0.35, "concrete")
    a.box(0, 0, 4.4, 4, 3, 0.35, "concrete")
    a.arrow(a.iso(4.6, 0, 0.4), a.iso(4.6, 0, 4.4), width=1.4, head=0.25)


def _l_walls(a, material="wall"):
    a.box(0, 0, 0, 1, 4, 2.4, material)
    a.box(1, 0, 0, 4, 1, 2.4, material)


def _wall_joins(a):
    _l_walls(a)
    a.face([(0, 0, 2.4), (1, 0, 2.4), (1, 1, 2.4), (0, 1, 2.4)], "yellow")


def _join_geometry(a):
    a.box(0, 0, 0, 5, 3.5, 0.6, "concrete")
    a.box(1.2, 1.2, 0.6, 1.2, 1.2, 2.6, "concrete")
    a.line3((1.2, 2.4, 0.6), (2.4, 2.4, 0.6), "concrete", 1.6)      # (no line where they meet: one material)
    a.line3((2.4, 1.2, 0.6), (2.4, 2.4, 0.6), "concrete", 1.6)


def _unjoin_geometry(a):
    a.box(0, 0, 0, 5, 3.5, 0.6, "concrete")
    a.box(1.2, 1.2, 1.5, 1.2, 1.2, 2.6, "concrete")
    a.arrow(a.iso(3.2, 1.0, 1.0), a.iso(3.2, 1.0, 2.6), width=1.2, head=0.35)


def _align(a):
    a.line((26, 3), (26, 29), "blue", 1.4)
    a.poly([(5, 6), (16, 6), (16, 13), (5, 13)], "concrete", "detail", THIN, dash=[3, 2])
    a.poly([(15, 19), (26, 19), (26, 26), (15, 26)], "concrete")
    a.arrow((17, 9.5), (24, 9.5), width=1.2, head=0.4)


def _offset(a):
    a.poly([(4, 26), (4, 12), (18, 12), (18, 4)], None, "ink", 1.6, closed=False)
    a.poly([(10, 26), (10, 18), (24, 18), (24, 4)], None, "blue", 1.4, closed=False, dash=[3, 2])
    a.arrow((5, 22), (9, 22), width=1.0, head=0.45)


def _scale(a):
    a.poly([(4, 16), (14, 16), (14, 28), (4, 28)], "concrete", "detail", THIN, dash=[3, 2])
    a.poly([(4, 4), (28, 4), (28, 28), (4, 28)], None, "ink", 1.4)
    a.arrow((14, 16), (25, 7), width=1.3, head=0.3)


def _trim_extend(a):
    a.line((4, 6), (4, 28), "ink", 1.8)
    a.line((4, 28), (28, 28), "ink", 1.8)
    a.line((12, 6), (12, 20), "blue", 1.6)
    a.line((12, 20), (12, 28), "blue", 1.6, dash=[2, 2])
    a.circle((12, 28), 1.8, "yellow", "ink", 0.6)


def _corner_walls(a):
    a.box(0, 0, 0, 1, 3.4, 2.4, "wall")
    a.box(1.6, 0, 0, 3.4, 1, 2.4, "wall")
    a.face([(1, 0, 2.4), (1.6, 0, 2.4), (1.6, 1, 2.4), (1, 1, 2.4)], None, "blue", 1.0, dash=[2, 1.5])


def _split_wall(a):
    a.box(0, 0, 0, 2.8, 1, 3, "wall")
    a.box(3.2, 0, 0, 2.8, 1, 3, "wall")
    a.line3((3.0, 1, -0.6), (3.0, 1, 3.8), "blue", 1.2, dash=[3, 2])


def _split_gap(a):
    a.box(0, 0, 0, 2.4, 1, 3, "wall")
    a.box(3.6, 0, 0, 2.4, 1, 3, "wall")
    a.arrow(a.iso(3.0, 1, 1.5), a.iso(2.5, 1, 1.5), width=1.0, head=0.6)
    a.arrow(a.iso(3.0, 1, 1.5), a.iso(3.5, 1, 1.5), width=1.0, head=0.6)


def _array(a):
    a.line3((0.6, 1.2, 0), (5.0, 1.2, 0), "blue", 1.0, dash=[2, 2])
    for k in range(3):
        a.box(k * 2.2, 0, 0, 1.2, 1.2, 1.2, "concrete", "ink" if k == 0 else "detail")


def _delete(a):
    a.box(0, 0, 0, 2, 2, 1.6, "concrete")
    _cross(a, a.iso(1.7, 1.7, 2.6), 0.9, 2.2)


def _freehand(a):
    path = QtGui.QPainterPath(QtCore.QPointF(4, 24))
    path.cubicTo(8, 8, 12, 30, 17, 16)
    path.cubicTo(21, 5, 25, 20, 28, 8)
    a.path(path, None, "ink", 1.8)
    a.circle((4, 24), 1.8, "blue", "blue", 0.6)
    a.circle((28, 8), 1.8, "blue", "blue", 0.6)


def _bezier(a):
    path = QtGui.QPainterPath(QtCore.QPointF(4, 26))
    path.cubicTo(8, 4, 24, 4, 28, 26)
    a.path(path, None, "ink", 1.8)
    for (x0, y0), (x1, y1) in (((4, 26), (8, 6)), ((28, 26), (24, 6))):
        a.line((x0, y0), (x1, y1), "blue", 0.8)
        a.poly([(x1 - 1.5, y1 - 1.5), (x1 + 1.5, y1 - 1.5), (x1 + 1.5, y1 + 1.5), (x1 - 1.5, y1 + 1.5)], "paper",
               "blue", 0.8)
        a.circle((x0, y0), 1.8, "blue", "blue", 0.6)


def _classify(a):
    sketch = [(0, 0, 0), (1.6, 0, 0), (1.6, 1.6, 0), (0, 1.6, 0)]
    a.face([(x, y, 2.4) for x, y, _z in sketch], None, "detail", THIN, dash=[3, 2])
    for x, y, _z in sketch:
        a.line3((x, y, 0), (x, y, 2.4), "detail", THIN, dash=[3, 2])
    a.box(3.4, 0.8, 0, 3.6, 0.8, 2.4, "wall")
    a.arrow(a.iso(1.9, 0.3, 1.4), a.iso(3.4, 0.6, 1.6), width=1.2, head=0.4)


def _materials(a):
    a.box(0, 0, 0, 1.6, 1.6, 1.6, "wood")
    a.box(2.2, 0, 0, 1.6, 1.6, 1.6, "concrete")
    a.box(1.1, 2.2, 0, 1.6, 1.6, 1.6, "glass")


def _caixilho(a):
    a.poly([(4, 4), (24, 4), (24, 28), (4, 28)], "paper")
    a.poly([(6.5, 6.5), (13, 6.5), (13, 25.5), (6.5, 25.5)], theme.ART["glass"][1], "ink", THIN)
    a.poly([(15, 6.5), (21.5, 6.5), (21.5, 25.5), (15, 25.5)], theme.ART["glass"][1], "ink", THIN)
    _spark(a, (26, 7), 4)


def _roof_profile(a):
    a.poly([(3, 24), (16, 8), (29, 24)], None, "ink", 1.8, closed=False)
    a.line((3, 28), (29, 28), "detail", THIN)
    for x, y in ((3, 24), (16, 8), (29, 24)):
        a.poly([(x - 1.6, y - 1.6), (x + 1.6, y - 1.6), (x + 1.6, y + 1.6), (x - 1.6, y + 1.6)], "paper", "blue", 1.0)


def _gutter(a):
    top, left, right = theme.ART["roof"]
    a.face([(0, 0, 2), (5, 0, 2), (5, 2.6, 0.6), (0, 2.6, 0.6)], top)
    a.box(-0.2, 2.6, 0.1, 5.4, 0.6, 0.45, "steel")
    a.box(4.4, 2.75, -2.2, 0.35, 0.35, 2.3, "steel")


def _drain(a):
    a.box(0, 0, 0, 5, 4, 0.5, "concrete")
    a.face([(2, 1.5, 0.5), (3, 1.5, 0.5), (3, 2.5, 0.5), (2, 2.5, 0.5)], "steel")
    a.line3((2.33, 1.5, 0.5), (2.33, 2.5, 0.5), "ink", THIN)
    a.line3((2.66, 1.5, 0.5), (2.66, 2.5, 0.5), "ink", THIN)
    a.arrow(a.iso(2.5, 2, 2.6), a.iso(2.5, 2, 0.9), width=1.3, head=0.35)


def _flooring(a):
    a.box(0, 0, 0, 5, 4, 0.5, "concrete")
    a.face([(0, 0, 0.5), (5, 0, 0.5), (5, 4, 0.5), (0, 4, 0.5)], "wood")
    for y in (0.8, 1.6, 2.4, 3.2):
        a.line3((0, y, 0.5), (5, y, 0.5), theme.ART["wood"][2], THIN)


def _edit_outline(a):
    a.box(0, 0, 0, 5, 4, 0.5, "concrete")
    corners = [(0, 0, 0.5), (5, 0, 0.5), (5, 4, 0.5), (0, 4, 0.5)]
    a.face(corners, None, "blue", 1.2, dash=[3, 2])
    for c in corners:
        x, y = a.iso(*c)
        a.poly([(x - 0.35, y - 0.35), (x + 0.35, y - 0.35), (x + 0.35, y + 0.35), (x - 0.35, y + 0.35)], "paper",
               "blue", 0.8)


def _curtain_panel(a):
    a.face([(0, 0, 0), (3, 0, 0), (3, 0, 4), (0, 0, 4)], "steel")
    a.face([(0.3, 0, 0.3), (2.7, 0, 0.3), (2.7, 0, 3.7), (0.3, 0, 3.7)], theme.ART["glass"][1])
    a.line3((0.6, 0, 2.6), (1.4, 0, 3.4), "paper", THIN)


def _railing_types(a):
    for x in (0, 2, 4):
        a.box(x - 0.08, -0.08, 0, 0.16, 0.16, 2.2, "steel")
    a.box(-0.1, -0.12, 2.2, 4.2, 0.24, 0.16, "steel")
    tx, ty = a.iso(4.4, 0, 3.4)
    _sheet(a, tx - 0.4, ty - 1.4, 2.6, 1.8, rows=2)


def _elevator(a):
    a.box(0, 0, 0, 2.6, 2.6, 4.6, "concrete")
    a.face([(0.5, 2.6, 0), (2.1, 2.6, 0), (2.1, 2.6, 2.6), (0.5, 2.6, 2.6)], "steel")
    a.line3((1.3, 2.6, 0), (1.3, 2.6, 2.6), "ink", THIN)
    ux, uy = a.iso(1.3, 2.6, 3.7)
    a.poly([(ux - 0.5, uy + 0.3), (ux, uy - 0.4), (ux + 0.5, uy + 0.3)], "yellow", "ink", 0.5)


def _floor_plate(a):
    a.face([(0, 0, 0), (5, 0, 0), (5, 4, 0), (0, 4, 0)], theme.ART["room"][0], "blue", THIN)


def _room_separator(a):
    _floor_plate(a)
    a.line3((2.5, -0.4, 0), (2.5, 4.4, 0), "blue", 1.6, dash=[3, 2])


def _rooms_identify(a):
    _floor_plate(a)
    a.line3((2.5, 0, 0), (2.5, 4, 0), "ink", 1.0)
    for x in (1.25, 3.75):
        a.line3((x - 0.5, 2, 0), (x + 0.5, 2, 0), "blue", 1.0)
        a.line3((x, 1.5, 0), (x, 2.5, 0), "blue", 1.0)
    _spark(a, a.iso(5.2, -0.6, 1.4), 0.9)


def _areas(a):
    _floor_plate(a)
    for k in range(1, 9):                                          # (its hatch: lines x + y = t inside 5 × 4)
        t = k * 1.0
        x0, x1 = max(0.0, t - 4), min(5.0, t)
        a.line3((x0, t - x0, 0), (x1, t - x1, 0), "blue", 0.6)


def _room_program(a):
    _sheet(a, 4, 3, 18, 26, rows=5)
    for k in range(5):
        a.circle((7, 3 + 26 * (k + 1) / 6), 0.9, "room" if k else "green", None)
    a.poly([(20, 18), (30, 18), (30, 29), (20, 29)], theme.ART["room"][1], "blue", 1.0)


def _hole(a, x0, x1, z0, z1, back):
    """A hole in the host wall's face, seen through (back None) or with its back at y = back (a niche): its left jamb
    and its sill are the faces one sees inside it."""
    top, left, right = theme.ART["wall"]
    y0 = 0.0 if back is None else back
    a.face([(x0, 0.8, z0), (x1, 0.8, z0), (x1, 0.8, z1), (x0, 0.8, z1)], "paper" if back is None else right)
    a.face([(x0, y0, z0), (x0, 0.8, z0), (x0, 0.8, z1), (x0, y0, z1)], right, "ink", THIN)
    a.face([(x0, y0, z0), (x1, y0, z0), (x1, 0.8, z0), (x0, 0.8, z0)], top, "ink", THIN)


def _wall_opening(a):
    _host(a)
    _hole(a, 2, 4, 0.8, 2.6, None)


def _roof_opening(a):
    top, left, right = theme.ART["roof"]
    a.face([(0, 0, 2.4), (5, 0, 2.4), (5, 4, 0), (0, 4, 0)], top)            # (a pitch falling to the eaves)
    a.face([(1.6, 1.2, 1.68), (3.4, 1.2, 1.68), (3.4, 2.8, 0.72), (1.6, 2.8, 0.72)], "paper")
    a.face([(1.6, 1.2, 1.68), (1.6, 2.8, 0.72), (1.6, 2.8, 0.42), (1.6, 1.2, 1.38)], right, "ink", THIN)


def _niche(a):
    _host(a)
    _hole(a, 2, 4, 1.0, 2.4, 0.35)


def _paint(a):
    a.box(0, 0, 0, 4, 1, 2.6, "wall")
    a.face([(0, 1, 0), (2.2, 1, 0), (2.2, 1, 2.6), (0, 1, 2.6)], "blue", "ink")
    bx, by = a.iso(4.2, 1.6, 4.2)
    a.poly([(bx - 1.0, by - 0.9), (bx + 1.0, by - 0.9), (bx + 0.8, by + 1.0), (bx - 0.8, by + 1.0)], "steel")
    a.poly([(bx - 1.0, by - 0.9), (bx - 2.0, by + 0.3), (bx - 1.6, by + 0.9)], "blue", "blue", 0.6)


def _perforated_panel(a):
    a.face([(0, 0, 0), (4, 0, 0), (4, 0, 3), (0, 0, 3)], "steel")
    for x in (0.7, 1.55, 2.4, 3.25):
        for z in (0.6, 1.5, 2.4):
            cx, cy = a.iso(x, 0, z)
            a.circle((cx, cy), 0.17, "ink", None)


def _ripado_panel(a):
    a.box(0, 0, 0, 5, 0.6, 3, "wall")
    for k in range(5):
        a.box(0.25 + k * 1.0, 0.6, 0, 0.5, 0.35, 3, "wood")


def _wall_finish(a):
    a.box(0, 0, 0, 5, 0.9, 3, "wall")
    a.box(0, 0.9, 0, 5, 0.18, 3, "room")


def _wall_reveal(a):
    a.box(0, 0, 0, 5, 1, 3, "wall")
    a.face([(0, 1, 1.4), (5, 1, 1.4), (5, 1, 1.6), (0, 1, 1.6)], "ink", None)


def _profile(a):
    a.poly([(6, 28), (6, 6), (12, 6), (12, 10), (18, 10), (20, 16), (26, 16), (26, 28)], "concrete")


def _wall_sweep(a):
    a.box(0, 0, 0, 5, 1, 3, "wall")
    a.box(0, 1, 2.3, 5, 0.35, 0.35, "wood")


def _profile_from_face(a):
    a.face([(0, 0, 0), (4, 0, 0), (4, 0, 3), (0, 0, 3)], theme.ART["wall"][1])
    a.face([(0.4, 0, 0.4), (3.6, 0, 0.4), (3.6, 0, 2.6), (0.4, 0, 2.6)], None, "blue", 1.2, dash=[3, 2])
    a.arrow(a.iso(4.2, 0, 1.5), a.iso(6.0, 0, 1.5), width=1.2, head=0.4)


def _ripado_screen(a):
    a.box(-0.2, -0.3, 0, 5.4, 1.1, 0.25, "concrete")
    for k in range(5):
        a.box(0.15 + k * 1.05, 0, 0.25, 0.5, 0.5, 3.2, "wood")


def _kitchen(a):
    a.box(0, 0, 0, 5, 1.6, 2.0, "wood")
    a.box(-0.1, -0.1, 2.0, 5.2, 1.8, 0.2, "concrete")
    for x in (1.67, 3.33):
        a.line3((x, 1.6, 0.1), (x, 1.6, 1.9), theme.ART["wood"][2], THIN)
    a.face([(3.7, 0.4, 2.2), (4.7, 0.4, 2.2), (4.7, 1.3, 2.2), (3.7, 1.3, 2.2)], "steel")


def _cabinet(a):
    a.box(0, 0, 0, 2, 1.6, 3, "wood")
    a.line3((1, 1.6, 0.1), (1, 1.6, 2.9), theme.ART["wood"][2], THIN)
    for x in (0.8, 1.2):
        a.line3((x, 1.6, 1.3), (x, 1.6, 1.8), "ink", 1.0)


def _worktop(a):
    a.box(0, 0, 0, 6, 2, 0.35, "concrete")


def _appliance(a):
    a.box(0, 0, 0, 1.8, 1.8, 3.6, "steel")
    a.line3((0, 1.8, 2.4), (1.8, 1.8, 2.4), "ink", THIN)
    a.line3((1.5, 1.8, 2.7), (1.5, 1.8, 3.3), "ink", 1.2)
    a.line3((1.5, 1.8, 1.4), (1.5, 1.8, 2.1), "ink", 1.2)


def _cut_list(a):
    _sheet(a, 4, 3, 16, 24, rows=5)
    a.poly([(14, 20), (30, 20), (30, 25), (14, 25)], "wood")
    a.line((18, 20), (18, 25), theme.ART["wood"][2], THIN)


def _i_section(a, x, y, z, length, along="x"):
    """A steel I piece (1.8 wide, 1.6 deep): along x (a beam) or z (a column)."""
    w, d, t = 1.8, 1.6, 0.3
    if along == "x":
        a.box(x, y, z, length, w, t, "steel")
        a.box(x, y + (w - t) / 2, z + t, length, t, d - 2 * t, "steel")
        a.box(x, y, z + d - t, length, w, t, "steel")
    else:
        a.box(x, y, z, w, t, length, "steel")
        a.box(x + (w - t) / 2, y + t, z, t, d - 2 * t, length, "steel")
        a.box(x, y + d - t, z, w, t, length, "steel")


def _steel_member(a):
    _i_section(a, 0, 0, 0, 4.2, "z")


def _steel_shed(a):
    for x in (0, 5.2):
        a.box(x, 0, 0, 0.5, 0.5, 3.2, "steel")
    a.face([(0, 0.25, 3.2), (2.85, 0.25, 4.6), (2.85, 0.25, 4.15), (0.5, 0.25, 3.0)], theme.ART["steel"][1])
    a.face([(5.7, 0.25, 3.2), (2.85, 0.25, 4.6), (2.85, 0.25, 4.15), (5.2, 0.25, 3.0)], theme.ART["steel"][1])


def _steel_truss(a):
    a.poly([(3, 24), (16, 10), (29, 24)], None, "steel", 2.0, closed=False)
    a.line((3, 24), (29, 24), theme.ART["steel"][2], 2.0)
    for x in (9.5, 16, 22.5):
        a.line((x, 24), (x, 24 - (14 - abs(x - 16) * 14 / 13)), theme.ART["steel"][1], 1.2)
    for x0, x1 in ((9.5, 16), (22.5, 16)):
        a.line((x0, 24), (x1, 10 + 1.5), theme.ART["steel"][1], 1.2)


def _steel_stair(a):
    for i in range(4):
        a.box(i * 1.2, 0.2, (i + 1) * 0.8 - 0.15, 1.2, 2.0, 0.15, "wood")
    a.face([(0, 2.2, 0), (4.8, 2.2, 3.2), (4.8, 2.2, 2.6), (0.6, 2.2, 0)], theme.ART["steel"][1])


def _beam_system(a):
    a.box(0, 0, 0, 0.5, 5, 0.6, "steel")
    a.box(4.5, 0, 0, 0.5, 5, 0.6, "steel")
    for y in (0.6, 1.9, 3.2, 4.5):
        a.box(0.5, y - 0.15, 0.2, 4, 0.3, 0.4, "steel")


def _param_surface(a):
    path = QtGui.QPainterPath(QtCore.QPointF(3, 20))
    path.cubicTo(10, 8, 16, 26, 29, 12)
    path.lineTo(29, 20)
    path.cubicTo(16, 32, 10, 16, 3, 28)
    path.closeSubpath()
    a.path(path, "glass", "ink", OUTLINE)
    for t in (0.33, 0.66):
        a.line((3 + 26 * t, 18 - 4 * math.sin(t * 6)), (3 + 26 * t, 26 - 4 * math.sin(t * 6)), "blue", 0.6)


def _steel_mitre(a):
    a.poly([(3, 8), (26, 8), (19, 15), (3, 15)], theme.ART["steel"][1])
    a.poly([(26, 8), (26, 30), (19, 30), (19, 15)], theme.ART["steel"][2])
    a.line((27.5, 6.5), (17.5, 16.5), "blue", 1.4, dash=[3, 2])


def _combined_footing(a):
    a.box(0, 0, 0, 6, 2.4, 0.9, "concrete")
    a.box(0.6, 0.6, 0.9, 1.2, 1.2, 2.0, "concrete")
    a.box(4.2, 0.6, 0.9, 1.2, 1.2, 2.0, "concrete")


def _footings_under(a):
    a.box(0, 0, 0, 3.4, 3.4, 0.8, "concrete")
    a.box(1.1, 1.1, 0.8, 1.2, 1.2, 3.6, "concrete")
    a.arrow(a.iso(3.9, 1.7, 4.0), a.iso(3.9, 1.7, 1.4), width=1.3, head=0.25)


def _rebar_mesh(a):
    bar = theme.ART["roof"][2]
    for k in range(5):
        a.line3((k * 1.2, 0, 0), (k * 1.2, 4.8, 0), bar, 1.4)
        a.line3((0, k * 1.2, 0), (4.8, k * 1.2, 0), bar, 1.4)


def _bolts(a, points):
    for x, y in points:
        a.circle((x, y), 0.9, "ink", None)


def _base_plate(a):
    a.box(0, 0, 0, 4.2, 4.0, 0.35, "steel")
    for x, y in ((0.45, 0.45), (3.75, 0.45), (0.45, 3.55), (3.75, 3.55)):
        cx, cy = a.iso(x, y, 0.35)
        a.circle((cx, cy), 0.24, "ink", None)
    _i_section(a, 1.2, 1.2, 0.35, 3.6, "z")


def _end_plate(a):
    a.poly([(2, 12), (20, 12), (20, 15), (2, 15)], "steel")
    a.poly([(2, 23), (20, 23), (20, 26), (2, 26)], "steel")
    a.poly([(2, 15), (20, 15), (20, 23), (2, 23)], theme.ART["steel"][1])
    a.poly([(20, 6), (24, 6), (24, 32), (20, 32)], theme.ART["steel"][2])
    _bolts(a, [(22, 9), (22, 18), (22, 29)])


def _fin_plate(a):
    a.poly([(3, 6), (9, 6), (9, 30), (3, 30)], theme.ART["steel"][2])
    a.poly([(9, 13), (19, 13), (19, 23), (9, 23)], theme.ART["steel"][0])
    a.poly([(14, 15), (30, 15), (30, 21), (14, 21)], theme.ART["steel"][1])
    _bolts(a, [(16.5, 16.5), (16.5, 19.5)])


def _gusset(a):
    a.poly([(4, 4), (9, 4), (9, 30), (4, 30)], theme.ART["steel"][2])
    a.poly([(9, 6), (30, 6), (30, 11), (9, 11)], theme.ART["steel"][1])
    a.poly([(9, 11), (20, 11), (9, 22)], "steel")
    _bolts(a, [(12, 14), (15, 14), (12, 17)])


def _purlin_cleat(a):
    a.poly([(3, 20), (29, 12), (29, 17), (3, 25)], theme.ART["steel"][1])
    a.poly([(13, 11), (19, 9), (19, 15), (13, 17)], "steel")
    a.poly([(14, 4), (19, 4), (19, 9), (14, 9)], theme.ART["steel"][2])
    _bolts(a, [(16, 13)])


def _knee_plate(a):
    a.poly([(4, 4), (10, 4), (10, 30), (4, 30)], theme.ART["steel"][2])
    a.poly([(10, 8), (30, 2), (30, 8), (10, 14)], theme.ART["steel"][1])
    a.poly([(10, 14), (20, 11), (10, 22)], "steel")


def _number_steel(a):
    _i_section(a, 0, 0, 0, 5, "x")
    tx, ty = a.iso(3.2, -1.2, 3.0)
    a.poly([(tx - 1.2, ty - 0.8), (tx + 1.2, ty - 0.8), (tx + 1.2, ty + 0.8), (tx - 1.2, ty + 0.8)], "paper", "blue",
           1.0)
    a.line((tx - 0.1, ty - 0.45), (tx - 0.1, ty + 0.45), "blue", 1.0)


def _steel_nc(a):
    _sheet(a, 4, 3, 18, 24, rows=2)
    for x, y in ((9, 18), (13, 18), (17, 18), (9, 22), (17, 22)):
        a.circle((x, y), 1.0, "ink", None)
    a.arrow((20, 24), (30, 30), width=1.5, head=0.4)


def _beams_between(a):
    for x in (0, 4.6):
        a.box(x, 0, 0, 0.8, 0.8, 3.6, "concrete")
    a.box(0.8, 0, 3.0, 3.8, 0.8, 0.6, "new")
    _spark(a, a.iso(2.7, -1.0, 5.0), 1.0)


def _walls_under_beams(a):
    a.box(0.2, 0.1, 0, 4.8, 0.6, 3.0, "new")
    a.box(0, 0, 3.0, 5.2, 0.8, 0.6, "concrete")
    _spark(a, a.iso(2.6, -1.0, 4.6), 1.0)


def _slabs_in_bays(a):
    for x in (0, 2.6, 5.2):
        for y in (0, 2.6):
            a.box(x, y, 0, 0.4, 0.4, 2.4, "concrete")
    a.box(0, 0, 2.4, 5.6, 3.0, 0.3, "new")
    _spark(a, a.iso(5.6, -0.8, 4.0), 1.0)


def _columns_on_grid(a):
    for k in (0.0, 4.0):
        a.line3((k, -1.4, 0), (k, 5.4, 0), "ink", 0.9, dash=[6, 2, 1, 2])
        a.line3((-1.4, k, 0), (5.4, k, 0), "ink", 0.9, dash=[6, 2, 1, 2])
    for x, y in ((0, 0), (4, 0), (0, 4), (4, 4)):                 # (the far ones first)
        a.box(x - 0.45, y - 0.45, 0, 0.9, 0.9, 2.6, "concrete")


def _remove_proposal(a):
    _propose_structure(a)
    _cross(a, a.iso(4.8, 0, 2.2), 1.2, 2.0)


def _grid_generate(a):
    for x in (6, 14, 22):
        a.line((x, 9), (x, 29), "ink", 0.8, dash=[5, 2, 1, 2])
        a.circle((x, 5.5), 3.2, "paper")
    _spark(a, (28, 22), 3.4)


def _grid_settings(a):
    for x in (5, 14):
        a.line((x, 9), (x, 30), "ink", 0.8, dash=[5, 2, 1, 2])
        a.circle((x, 5.5), 3.2, "paper")
    a.poly([(17, 14), (31, 14), (31, 30), (17, 30)], "paper", "blue", 1.0)
    for k, x in enumerate((21, 27, 24)):
        y = 18 + k * 4.5
        a.line((19, y), (29, y), "detail", 0.9)
        a.circle((x, y), 1.3, "blue", None)


DRAWN = {"select": _select, "move": _move, "copy": _copy, "rotate": _rotate, "mirror": _mirror, "line": _line,
         "arc": _arc, "rectangle": _rectangle, "circle": _circle, "push_pull": _push_pull, "tape": _tape,
         "dimension": _dimension, "component_make": _component_make, "group_make": _group_make,
         "wall": _wall, "door": _door, "window": _window, "loose_furniture": _loose_furniture, "column": _column,
         "roof": _roof, "ceiling": _ceiling, "slab": _slab, "curtain_wall": _curtain_wall, "railing": _railing,
         "ramp": _ramp, "stair": _stair, "room": _room, "storey_new": _storey_new, "grid": _grid,
         "work_plane": _work_plane, "beam": _beam, "footing": _footing, "propose_structure": _propose_structure,
         # (2.ª leva) Modelagem
         "copy_clip": _copy_clip, "paste": _paste, "paste_storeys": _paste_storeys, "wall_joins": _wall_joins,
         "join_geometry": _join_geometry, "unjoin_geometry": _unjoin_geometry, "align": _align, "offset": _offset,
         "scale": _scale, "trim_extend": _trim_extend, "corner_walls": _corner_walls, "split_wall": _split_wall,
         "split_gap": _split_gap, "array": _array, "delete": _delete, "freehand": _freehand, "bezier": _bezier,
         "classify": _classify, "materials": _materials,
         # Arquitetura
         "caixilho": _caixilho, "roof_profile": _roof_profile, "gutter": _gutter, "drain": _drain,
         "flooring": _flooring, "edit_outline": _edit_outline, "curtain_panel": _curtain_panel,
         "railing_types": _railing_types, "elevator": _elevator, "room_separator": _room_separator,
         "rooms_identify": _rooms_identify, "areas": _areas, "room_program": _room_program,
         "wall_opening": _wall_opening, "roof_opening": _roof_opening, "niche": _niche, "paint": _paint,
         "perforated_panel": _perforated_panel, "ripado_panel": _ripado_panel, "wall_finish": _wall_finish,
         "wall_reveal": _wall_reveal, "profile": _profile, "wall_sweep": _wall_sweep,
         "profile_from_face": _profile_from_face, "ripado_screen": _ripado_screen, "kitchen": _kitchen,
         "cabinet": _cabinet, "worktop": _worktop, "appliance": _appliance, "cut_list": _cut_list,
         # Estrutura
         "steel_member": _steel_member, "steel_shed": _steel_shed, "steel_truss": _steel_truss,
         "steel_stair": _steel_stair, "beam_system": _beam_system, "param_surface": _param_surface,
         "steel_mitre": _steel_mitre, "combined_footing": _combined_footing, "footings_under": _footings_under,
         "rebar_mesh": _rebar_mesh, "base_plate": _base_plate, "end_plate": _end_plate, "fin_plate": _fin_plate,
         "gusset": _gusset, "purlin_cleat": _purlin_cleat, "knee_plate": _knee_plate,
         "number_steel": _number_steel, "steel_nc": _steel_nc, "beams_between": _beams_between,
         "walls_under_beams": _walls_under_beams, "slabs_in_bays": _slabs_in_bays,
         "columns_on_grid": _columns_on_grid, "remove_proposal": _remove_proposal,
         "grid_generate": _grid_generate, "grid_settings": _grid_settings}
NAMES = tuple(DRAWN)
_PIXMAPS = {}


def pixmap(name):
    """The picture of a command (64 × 64 px, at device pixel ratio 2), drawn once — or None."""
    if name not in DRAWN:
        return None
    if name not in _PIXMAPS:
        art = Art()
        DRAWN[name](art)
        _PIXMAPS[name] = art.pixmap()
    return _PIXMAPS[name]


def icon(name):
    """The command's icon in the theme in use (theme.icon: its dark one made when wanted), or None."""
    pm = pixmap(name)
    return theme.icon(pm) if pm is not None else None
