"""(0.535, the owner: «organize também os ícones para serem como dos revit», then «Sim, redesenhar») The ribbon's
pictures as Revit draws its own — not copies of them: each object seen from above at a three-quarter angle (isometric),
its faces in three tones of its material (the top light, the left middle, the right dark), a thin dark outline; the
marks (arrows, points, the work plane) in blue, what is new in yellow. Drawn in code (nothing to ship or license),
for the light theme: theme.icon() turns their ink and white for the dark one, their materials stay.

A picture is a list of paths in its own units (an isometric point is (x − y)·cos 30°, (x + y)·sin 30° − z); it is fitted
whole into the 32 px square, so each one is drawn at its own scale. icon(name): the picture's QIcon, or None for a
command not drawn here (its older icon stays).

(0.536) Every tab drawn: Instalações, Inserir, Anotar, Analisar, Massa e Estudos, Terreno, Colaborar, Visualizar,
Gerenciar, Início and «Modificar | Paredes» after Modelagem, Arquitetura and Estrutura (0.535) — the drawings in plan
or elevation where Revit's are (dimensions, sections, sheets), in space where it shows the object."""

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
    top = theme.ART["roof"][0]
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
    top, _left, right = theme.ART["wall"]
    y0 = 0.0 if back is None else back
    a.face([(x0, 0.8, z0), (x1, 0.8, z0), (x1, 0.8, z1), (x0, 0.8, z1)], "paper" if back is None else right)
    a.face([(x0, y0, z0), (x0, 0.8, z0), (x0, 0.8, z1), (x0, y0, z1)], right, "ink", THIN)
    a.face([(x0, y0, z0), (x1, y0, z0), (x1, 0.8, z0), (x0, 0.8, z0)], top, "ink", THIN)


def _wall_opening(a):
    _host(a)
    _hole(a, 2, 4, 0.8, 2.6, None)


def _roof_opening(a):
    top, _left, right = theme.ART["roof"]
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


def _organic_form(a):
    """(0.555) A membrane lifted by a mast over its outline."""
    a.poly([(3, 26), (17, 30), (29, 24), (15, 20)], "glass", "ink", 0.8)
    path = QtGui.QPainterPath(QtCore.QPointF(3, 26))
    path.cubicTo(9, 22, 14, 8, 16, 5)
    path.cubicTo(18, 8, 24, 20, 29, 24)
    a.path(path, None, "blue", 1.8)
    path = QtGui.QPainterPath(QtCore.QPointF(17, 30))
    path.cubicTo(17, 22, 16.5, 10, 16, 5)
    a.path(path, None, "blue", 1.2)
    a.line((16, 5), (16, 22), "ink", 1.0, dash=[2, 2])


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


# ------------------------------------------------------------ (0.536, 3.ª leva) helpers

def _hull(points):
    """The convex hull of points in the picture's plane (monotone chain)."""
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in points))
    if len(pts) < 3:
        return pts

    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _ring3(a, centre, r, axis, steps=28):
    """A circle in space round an axis (0 = x, 1 = y, 2 = z), seen isometric: its points."""
    u, v = [i for i in range(3) if i != axis]
    out = []
    for s in range(steps):
        t = 2 * math.pi * s / steps
        q = list(centre)
        q[u] += r * math.cos(t)
        q[v] += r * math.sin(t)
        out.append(a.iso(*q))
    return out


def _cylinder(a, p0, p1, r, material, line="ink"):
    """A round piece from p0 to p1 along x, y or z: its body and the end one sees (the one further along the axis)."""
    d = [p1[i] - p0[i] for i in range(3)]
    k = max(range(3), key=lambda i: abs(d[i]))
    top, left, _right = theme.ART[material] if isinstance(material, str) else material
    r0, r1 = _ring3(a, p0, r, k), _ring3(a, p1, r, k)
    a.poly(_hull(r0 + r1), left, line)
    a.poly(r1 if d[k] > 0 else r0, top, line)


def _check(a, x, y, s, colour="green"):
    a.poly([(x - s, y), (x - s * 0.35, y + s * 0.7), (x + s, y - s * 0.8)], None, colour, s * 0.45, closed=False)


def _warning(a, x, y, s):
    a.poly([(x, y - s), (x + s * 1.1, y + s * 0.85), (x - s * 1.1, y + s * 0.85)], "yellow", "ink", 0.8)
    a.line((x, y - s * 0.4), (x, y + s * 0.3), "ink", s * 0.28)
    a.circle((x, y + s * 0.6), s * 0.12, "ink", None)


def _link(a, x, y, s, colour="blue"):
    """A chain's two links: linked."""
    for dx in (-0.3, 0.3):
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(-s * 0.5, -s * 0.22, s, s * 0.44), s * 0.22, s * 0.22)
        t = QtGui.QTransform()
        t.translate(x + dx * s, y - dx * s)
        t.rotate(-45)
        a.path(t.map(path), None, colour, max(1.2, s * 0.16))


def _picture(a, x, y, w, h):
    a.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], theme.ART["glass"][0])
    a.poly([(x, y + h), (x + w * 0.35, y + h * 0.45), (x + w * 0.6, y + h * 0.75), (x + w * 0.78, y + h * 0.55),
            (x + w, y + h * 0.85), (x + w, y + h)], "grass", None)
    a.circle((x + w * 0.75, y + h * 0.28), min(w, h) * 0.12, "yellow", None)
    a.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], None, "ink")


def _cloud(a, cx, cy, r, n=34, colours=("blue", "green", "roof")):
    """A cloud of points (a scan): on a sunflower's spiral, so always the same."""
    for k in range(n):
        rr = r * math.sqrt((k + 0.5) / n)
        th = k * 2.39996
        a.circle((cx + rr * math.cos(th), cy + rr * math.sin(th) * 0.8), r * 0.09, colours[k % len(colours)], None)


def _pencil(a, x, y, s):
    """A pencil, its point at (x, y), going up to the right."""
    ux, uy = 0.7071, -0.7071
    px, py = -uy, ux
    w = s * 0.17

    def at(t, side):
        return (x + ux * t + px * side, y + uy * t + py * side)
    a.poly([at(0, 0), at(s * 0.25, w), at(s * 0.25, -w)], theme.ART["wood"][0])
    a.poly([at(0, 0), at(s * 0.09, w * 0.36), at(s * 0.09, -w * 0.36)], "ink", None)
    a.poly([at(s * 0.25, w), at(s * 0.85, w), at(s * 0.85, -w), at(s * 0.25, -w)], "yellow")
    a.poly([at(s * 0.85, w), at(s, w), at(s, -w), at(s * 0.85, -w)], "red")


def _bolt(a, x, y, s):
    """A lightning bolt: electricity."""
    a.poly([(x + s * 0.15, y - s), (x - s * 0.45, y + s * 0.1), (x - s * 0.02, y + s * 0.1), (x - s * 0.2, y + s),
            (x + s * 0.45, y - s * 0.15), (x + s * 0.02, y - s * 0.15)], "yellow", "ink", 0.8)


def _gear(a, cx, cy, r, teeth=8):
    pts = []
    for k in range(teeth * 4):
        t = 2 * math.pi * k / (teeth * 4)
        rr = r if (k % 4) in (0, 1) else r * 0.74
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    a.poly(pts, "concrete")
    a.circle((cx, cy), r * 0.32, "paper")


def _person(a, x, y, s, colour):
    a.circle((x, y - s * 0.55), s * 0.3, colour)
    path = QtGui.QPainterPath()
    path.moveTo(x - s * 0.62, y + s * 0.62)
    path.cubicTo(x - s * 0.62, y - s * 0.25, x + s * 0.62, y - s * 0.25, x + s * 0.62, y + s * 0.62)
    path.closeSubpath()
    a.path(path, colour)


def _lock(a, x, y, s, opened=False):
    """A padlock; opened: its shackle up, out of the body on the left."""
    up = s * 0.4 if opened else 0.0
    path = QtGui.QPainterPath(QtCore.QPointF(x - s * 0.35, y - s * (0.75 if opened else 0.5)))
    path.lineTo(x - s * 0.35, y - s * 0.5 - up)
    path.arcTo(QtCore.QRectF(x - s * 0.35, y - s * 0.85 - up, s * 0.7, s * 0.7), 180, -180)
    path.lineTo(x + s * 0.35, y - s * 0.5)
    a.path(path, None, "ink", s * 0.16)
    a.poly([(x - s * 0.55, y - s * 0.5), (x + s * 0.55, y - s * 0.5), (x + s * 0.55, y + s * 0.45),
            (x - s * 0.55, y + s * 0.45)], "yellow")
    a.circle((x, y - s * 0.05), s * 0.12, "ink", None)


def _eye(a, cx, cy, s):
    path = QtGui.QPainterPath(QtCore.QPointF(cx - s, cy))
    path.quadTo(cx, cy - s * 0.9, cx + s, cy)
    path.quadTo(cx, cy + s * 0.9, cx - s, cy)
    a.path(path, "paper")
    a.circle((cx, cy), s * 0.38, "blue", None)
    a.circle((cx, cy), s * 0.15, "ink", None)


def _cube2d(a, cx, cy, s, material):
    """A small cube drawn in the picture's plane (centre, half-width)."""
    top, left, right = theme.ART[material]
    h = s * 0.58
    a.poly([(cx, cy - h * 2), (cx + s, cy - h), (cx, cy), (cx - s, cy - h)], top)
    a.poly([(cx - s, cy - h), (cx, cy), (cx, cy + h * 1.8), (cx - s, cy + h * 0.8)], left)
    a.poly([(cx + s, cy - h), (cx, cy), (cx, cy + h * 1.8), (cx + s, cy + h * 0.8)], right)


def _dim(a, p0, p1, ext=2.5, colour="ink"):
    """A dimension (as the drawings': its line, the extension lines, the slanted ticks)."""
    (x0, y0), (x1, y1) = p0, p1
    n = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / n, (y1 - y0) / n
    px, py = -uy, ux
    a.line(p0, p1, colour, 0.9)
    for x, y in (p0, p1):
        a.line((x - px * 1.4, y - py * 1.4), (x + px * ext, y + py * ext), colour, 0.7)
        a.line((x - (ux + px) * 1.3, y - (uy + py) * 1.3), (x + (ux + px) * 1.3, y + (uy + py) * 1.3), colour, 1.5)


def _plan_walls(a, x0, y0, x1, y1, t=2.2):
    """A room's walls in plan, cut (poché)."""
    a.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], theme.ART["wall"][2])
    a.poly([(x0 + t, y0 + t), (x1 - t, y0 + t), (x1 - t, y1 - t), (x0 + t, y1 - t)], "paper")


def _terrain(a, w=5.0, d=4.0, h=None):
    """A piece of ground: a block of earth, its top grass, with its contour lines."""
    h = h or (lambda x, y: 1.1 + 0.45 * math.sin(x * 1.1) + 0.35 * math.cos(y * 1.2))
    xs = [w * k / 12 for k in range(13)]
    ys = [d * k / 10 for k in range(11)]
    earth = theme.ART["earth"]
    a.poly([a.iso(w, y, 0) for y in ys] + [a.iso(w, y, h(w, y)) for y in reversed(ys)], earth[2])
    a.poly([a.iso(x, d, 0) for x in xs] + [a.iso(x, d, h(x, d)) for x in reversed(xs)], earth[1])
    top = ([a.iso(x, 0, h(x, 0)) for x in xs] + [a.iso(w, y, h(w, y)) for y in ys]
           + [a.iso(x, d, h(x, d)) for x in reversed(xs)] + [a.iso(0, y, h(0, y)) for y in reversed(ys)])
    a.poly(top, theme.ART["grass"][0])
    for yy in (d * 0.3, d * 0.65):
        a.poly([a.iso(x, yy, h(x, yy)) for x in xs], None, theme.ART["grass"][2], THIN, closed=False)
    return h


def _digit(a, d, x, y, hgt, colour="ink", width=1.2):
    """1, 2 or 3 drawn with strokes (no font), its box from (x, y) hgt tall and half as wide."""
    w = hgt * 0.5
    path = QtGui.QPainterPath()
    if d == 1:
        path.moveTo(x + w * 0.2, y + hgt * 0.2)
        path.lineTo(x + w * 0.6, y)
        path.lineTo(x + w * 0.6, y + hgt)
    elif d == 2:
        path.moveTo(x, y + hgt * 0.25)
        path.cubicTo(x, y - hgt * 0.08, x + w, y - hgt * 0.08, x + w, y + hgt * 0.3)
        path.cubicTo(x + w, y + hgt * 0.55, x, y + hgt * 0.8, x, y + hgt)
        path.lineTo(x + w, y + hgt)
    else:
        path.moveTo(x, y + hgt * 0.12)
        path.cubicTo(x + w * 0.5, y - hgt * 0.1, x + w * 1.1, y + hgt * 0.2, x + w * 0.35, y + hgt * 0.47)
        path.cubicTo(x + w * 1.2, y + hgt * 0.6, x + w * 0.8, y + hgt * 1.15, x, y + hgt * 0.9)
    a.path(path, None, colour, width)


# ------------------------------------------------------------ Instalações (Revit's Systems)

def _duct(a):
    a.box(0, 0, 0, 6, 1.8, 1.4, "steel")
    for x in (1.5, 4.5):                                          # (its joints, on the faces one sees)
        a.line3((x, 1.8, 0), (x, 1.8, 1.4), "ink", THIN)
        a.line3((x, 0, 1.4), (x, 1.8, 1.4), "ink", THIN)


def _air_terminal(a):
    a.box(0, 0, 2.2, 3.6, 3.6, 0.35, "steel")
    for k in (0.5, 1.0):
        a.face([(k, k, 2.55), (3.6 - k, k, 2.55), (3.6 - k, 3.6 - k, 2.55), (k, 3.6 - k, 2.55)], None, "ink", THIN)
    for x, y in ((0.6, 1.8), (1.8, 1.8), (3.0, 1.8)):
        a.arrow(a.iso(x + 0.6, y + 0.6, 2.0), a.iso(x + 0.6, y + 0.6, 0.0), width=1.1, head=0.35)


def _equipment(a):
    a.box(0, 0, 0, 4, 2.6, 3, "steel")
    a.poly(_ring3(a, (2, 2.6, 1.5), 1.05, 1), theme.ART["concrete"][2], "ink", THIN)
    c = a.iso(2, 2.6, 1.5)
    for t in (0, 60, 120):
        dx, dy = math.cos(math.radians(t)) * 0.95, math.sin(math.radians(t)) * 0.95
        a.line((c[0] - dx, c[1] - dy * 0.7), (c[0] + dx, c[1] + dy * 0.7), "ink", THIN)


def _pipe(a):
    _cylinder(a, (0, 0, 0), (6, 0, 0), 0.75, "water")
    _cylinder(a, (5.2, 0, 0), (5.7, 0, 0), 0.95, "water")


def _fixture(a):
    a.box(0, 0, 0, 3.6, 2.4, 0.6, "concrete")
    a.poly(_ring3(a, (1.8, 1.2, 0.6), 0.85, 2), theme.ART["water"][1], "ink", THIN)
    a.box(1.65, 0.1, 0.6, 0.3, 0.3, 0.8, "steel")
    a.box(1.65, 0.1, 1.4, 0.3, 0.8, 0.2, "steel")


def _water_net(a, material="water"):
    _cylinder(a, (0, 0, 0), (5, 0, 0), 0.35, material)
    _cylinder(a, (2.4, 0, 0), (2.4, 3.5, 0), 0.35, material)
    _cylinder(a, (5, 0, 0), (5, 0, 2.6), 0.35, material)


def _connect_network(a):
    _water_net(a)
    for p in ((2.4, 0, 0), (5, 0, 0)):
        x, y = a.iso(*p)
        a.circle((x, y), 0.45, "green", "ink", 0.6)


def _water_proposal(a):
    _water_net(a, "new")
    _spark(a, a.iso(0.6, -1.2, 2.2), 1.0)


def _remove_water_proposal(a):
    _water_net(a, "new")
    _cross(a, a.iso(3.6, 0.3, 1.8), 1.0, 2.0)


def _electrical(a):
    a.box(0, 0, 0, 2.6, 0.9, 3.8, "concrete")
    a.face([(0.3, 0.9, 0.3), (2.3, 0.9, 0.3), (2.3, 0.9, 3.5), (0.3, 0.9, 3.5)], theme.ART["concrete"][0], "ink",
           THIN)
    x, y = a.iso(1.3, 0.9, 1.9)
    _bolt(a, x, y, 1.0)


def _conduit(a):
    _cylinder(a, (0, 0, 0), (4, 0, 0), 0.3, "steel")
    _cylinder(a, (4, 0, 0), (4, 0, 3), 0.3, "steel")
    _cylinder(a, (3.7, 0, 0), (4.3, 0, 0), 0.42, "steel")


def _light(a):
    a.line((16, 2), (16, 10), "ink", 1.0)
    for t in (-50, -15, 15, 50):
        r = math.radians(t + 90)
        a.line((16 + 7.5 * math.cos(r), 18 + 7.5 * math.sin(r)), (16 + 12 * math.cos(r), 18 + 12 * math.sin(r)),
               "yellow", 1.6)
    a.circle((16, 17.5), 3.6, "yellow")
    a.poly([(9, 17), (23, 17), (19, 10), (13, 10)], "steel")


def _outlet(a, x, y):
    a.box(x, y, 0, 1.2, 0.5, 1.2, "concrete")


def _new_circuit(a):
    _outlet(a, 0, 0)
    _outlet(a, 4, 0)
    a.poly([a.iso(0.6, 0.5, 1.3), a.iso(2.6, 0.5, 3.4), a.iso(4.6, 0.5, 1.3)], None, "blue", 1.0, closed=False,
           dash=[3, 2])
    _spark(a, a.iso(2.6, 0.5, 4.6), 0.9)


def _route_circuits(a):
    _outlet(a, 0, 0)
    _outlet(a, 4.6, 2.4)
    a.poly([a.iso(0.6, 0.5, 1.2), a.iso(0.6, 0.5, 2.6), a.iso(5.2, 0.5, 2.6), a.iso(5.2, 2.9, 2.6),
            a.iso(5.2, 2.9, 1.2)], None, "blue", 1.3, closed=False)
    x, y = a.iso(2.9, 0.5, 2.6)
    _bolt(a, x, y - 1.2, 0.8)


def _electric_set(a):
    _outlet(a, 0, 0)
    _outlet(a, 2.4, 0)
    a.box(4.6, 0, 2.2, 1.2, 1.2, 0.4, "new")
    a.line3((5.2, 0.6, 2.6), (5.2, 0.6, 3.6), "ink", THIN)


def _electrical_proposal(a):
    _electric_set(a)
    _spark(a, a.iso(0.4, -1.0, 2.6), 0.9)


def _remove_electrical_proposal(a):
    _electric_set(a)
    _cross(a, a.iso(2.0, 0, 2.6), 0.9, 2.0)


def _electrical_check(a):
    _bolt(a, 11, 16, 11)
    _check(a, 23, 22, 6)


# ------------------------------------------------------------ Inserir (Revit's Insert)

def _cad_sheet(a, x, y, w, h):
    a.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], "paper")
    a.poly([(x + w * 0.15, y + h * 0.2), (x + w * 0.7, y + h * 0.2), (x + w * 0.7, y + h * 0.55),
            (x + w * 0.45, y + h * 0.55), (x + w * 0.45, y + h * 0.8), (x + w * 0.15, y + h * 0.8)], None, "blue", 0.9)
    a.line((x + w * 0.45, y + h * 0.2), (x + w * 0.45, y + h * 0.55), "blue", 0.7)


def _cad_link(a):
    _cad_sheet(a, 3, 3, 20, 24)
    _link(a, 24, 24, 9)


def _cloud_link(a):
    _cloud(a, 14, 14, 11)
    _link(a, 24, 24, 9)


def _list_sheet(a, x, y, w, h):
    a.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], "paper")
    for k in range(4):
        yy = y + h * (k + 0.8) / 4.6
        a.poly([(x + 2, yy - 1), (x + 4, yy - 1), (x + 4, yy + 1), (x + 2, yy + 1)], "blue", None)
        a.line((x + 6, yy), (x + w - 2, yy), "detail", 0.8)


def _cad_links(a):
    _list_sheet(a, 3, 4, 20, 22)
    _link(a, 24, 24, 9)


def _cloud_links(a):
    _list_sheet(a, 3, 4, 20, 22)
    _cloud(a, 24, 23, 6.5, n=20)


def _import_image(a):
    _picture(a, 3, 9, 20, 16)
    a.arrow((30, 2), (21, 11), width=1.8, head=0.38)


def _import_model(a):
    a.box(0, 0, 0, 2.6, 2.6, 2.2, "concrete")
    a.arrow(a.iso(4.6, -1.4, 5.0), a.iso(2.2, 0.4, 2.8), width=1.8, head=0.38)


def _images(a):
    _picture(a, 10, 3, 19, 15)
    _picture(a, 3, 12, 19, 15)


def _import_components(a):
    a.poly([(3, 12), (12, 12), (14, 15), (29, 15), (29, 29), (3, 29)], "yellow")
    a.poly([(3, 17), (29, 17), (29, 29), (3, 29)], theme.ART["new"][0])
    _cube2d(a, 18, 8, 4.5, "wood")
    a.arrow((9, 2), (9, 13), width=1.6, head=0.4)


def _terrain_points(a):
    a.face([(0, 0, 0), (5, 0, 0), (5, 4, 0), (0, 4, 0)], theme.ART["grass"][0], "ink", THIN)
    for x, y, h in ((0.8, 0.8, 1.6), (3.8, 0.6, 2.4), (2.2, 2.2, 2.0), (4.2, 3.2, 1.2), (1.0, 3.3, 2.6)):
        a.line3((x, y, 0), (x, y, h), "detail", 0.7, dash=[2, 1.5])
        cx, cy = a.iso(x, y, h)
        a.circle((cx, cy), 0.32, "red", "ink", 0.5)


def _terrain_dxf(a):
    a.poly([(3, 3), (23, 3), (23, 27), (3, 27)], "paper")
    for k, c in enumerate(("grass", "earth", "grass")):
        path = QtGui.QPainterPath(QtCore.QPointF(4, 9 + k * 6))
        path.cubicTo(9, 4 + k * 6, 15, 15 + k * 6, 22, 8 + k * 6)
        a.path(path, None, theme.ART[c][2], 1.2)
    a.arrow((31, 18), (24, 25), width=1.6, head=0.4)


# ------------------------------------------------------------ Anotar (Revit's Annotate)

def _dim_exterior(a):
    _plan_walls(a, 8, 9, 28, 29)
    _dim(a, (8, 4), (28, 4))
    _dim(a, (3, 9), (3, 29))
    _spark(a, (30, 3), 3)


def _dim_interior(a):
    _plan_walls(a, 2, 2, 30, 30)
    a.poly([(15, 4), (17, 4), (17, 28), (15, 28)], theme.ART["wall"][2])
    _dim(a, (4.2, 15), (15, 15), ext=1.5)
    _dim(a, (17, 15), (27.8, 15), ext=1.5)
    _spark(a, (24, 8), 3)


def _dimension_walls(a):
    a.poly([(3, 18), (29, 18), (29, 24), (3, 24)], theme.ART["wall"][2])
    a.poly([(12, 18), (18, 18), (18, 24), (12, 24)], "paper")
    _dim(a, (3, 10), (12, 10))
    _dim(a, (12, 10), (18, 10))
    _dim(a, (18, 10), (29, 10))


def _dimension_facades(a):
    a.poly([(9, 14), (19, 6), (29, 14), (29, 28), (9, 28)], theme.ART["wall"][0])
    a.poly([(16, 19), (22, 19), (22, 28), (16, 28)], theme.ART["glass"][1])
    _dim(a, (3, 28), (3, 14))
    _dim(a, (3, 14), (3, 6))


def _dimension_rooms(a):
    _plan_walls(a, 3, 3, 29, 29)
    _dim(a, (5.2, 12), (26.8, 12), ext=1.5)
    _dim(a, (16, 5.2), (16, 26.8), ext=1.5)


def _dimension_style(a):
    _dim(a, (3, 8), (20, 8))
    a.poly([(14, 14), (30, 14), (30, 30), (14, 30)], "paper", "blue", 1.0)
    for k, x in enumerate((19, 26, 22)):
        y = 18.5 + k * 4.5
        a.line((16, y), (28, y), "detail", 0.9)
        a.circle((x, y), 1.3, "blue", None)


def _draft(a):
    a.poly([(3, 26), (3, 12), (14, 12)], None, "ink", 1.4, closed=False)
    a.line((3, 26), (16, 26), "ink", 1.4)
    _pencil(a, 15, 20, 16)


def _renumber(a):
    for k in range(3):
        x = 3 + k * 9.5
        a.circle((x + 3.5, 21), 4.2, "paper", "blue", 1.0)
        _digit(a, (1, 2, 3)[k], x + 2, 18.2, 5.6, "ink", 1.1)
    path = QtGui.QPainterPath(QtCore.QPointF(6.5, 13))
    path.cubicTo(10, 3, 22, 3, 25.5, 12)
    a.path(path, None, "blue", 1.4)
    a.poly([(23.8, 9.8), (25.5, 13), (27.6, 10)], "blue", "blue", 0.8)


def _keynote_table(a):
    a.poly([(3, 6), (25, 6), (25, 28), (3, 28)], "paper")
    a.poly([(3, 6), (25, 6), (25, 11), (3, 11)], theme.ART["glass"][0])
    for y in (16.5, 22):
        a.line((3, y), (25, y), "detail", 0.8)
    a.line((10, 6), (10, 28), "detail", 0.8)
    a.poly([(19, 19), (30, 19), (30, 26), (19, 26)], "new")
    a.line((21, 22.5), (28, 22.5), "ink", 0.9)


def _symbol_styles(a):
    a.circle((10, 13), 7.5, "paper")
    a.poly([(10, 6), (14, 18), (10, 15.5), (6, 18)], "ink", "ink", 0.6)
    a.circle((23, 23), 6, "paper")
    path = QtGui.QPainterPath()
    path.moveTo(17, 23)
    path.arcTo(QtCore.QRectF(17, 17, 12, 12), 180, 180)
    path.closeSubpath()
    a.path(path, "ink", "ink", 0.6)
    a.line((17, 23), (29, 23), "ink", 1.0)


# ------------------------------------------------------------ Analisar (Revit's Analyze)

def _frame_lines(a, colour, width=1.6, nodes=True):
    pts = [(6, 29), (6, 11), (26, 11), (26, 29)]
    a.poly(pts, None, colour, width, closed=False)
    if nodes:
        for x, y in pts:
            a.circle((x, y), 1.4, "paper", colour, 1.0)


def _analyse(a):
    _frame_lines(a, theme.ART["steel"][2], 2.4, nodes=False)
    for x in (10, 16, 22):
        a.arrow((x, 2), (x, 9.5), "red", 1.3, 0.35)
    path = QtGui.QPainterPath(QtCore.QPointF(6, 11))
    path.cubicTo(10, 24, 22, 24, 26, 11)
    a.path(path, None, "blue", 1.2)


def _analytical(a):
    _frame_lines(a, "blue", 1.4)
    a.line((6, 29), (26, 11), "blue", 0.9, dash=[3, 2])


def _actions(a):
    a.line((3, 24), (29, 24), "ink", 2.4)
    a.poly([(3, 10), (29, 10)], None, "red", 1.0, closed=False)
    for x in (4, 10, 16, 22, 28):
        a.arrow((x, 10), (x, 22), "red", 1.2, 0.3)
    a.poly([(3, 24), (5.5, 28.5), (0.5, 28.5)], "paper")
    a.poly([(29, 24), (31.5, 28.5), (26.5, 28.5)], "paper")


def _show_analytical(a):
    _frame_lines(a, "blue", 1.2)
    _eye(a, 22, 24, 7)


def _moments(a):
    path = QtGui.QPainterPath(QtCore.QPointF(3, 12))
    path.quadTo(16, 36, 29, 12)
    path.closeSubpath()
    a.path(path, theme.ART["roof"][0], "red", 1.0)
    for x in (8, 12, 16, 20, 24):
        depth = 12 * (1 - ((x - 16) / 13) ** 2)
        a.line((x, 12), (x, 12 + depth), "red", 0.6)
    a.line((3, 12), (29, 12), "ink", 2.2)
    for x in (3, 29):
        a.poly([(x, 12), (x + 2.5, 16), (x - 2.5, 16)], "paper")


def _section_rebar(a, x, y, w, h):
    a.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], "concrete")
    a.poly([(x + 2, y + 2), (x + w - 2, y + 2), (x + w - 2, y + h - 2), (x + 2, y + h - 2)], None,
           theme.ART["roof"][2], 0.9)
    for bx in (x + 3.2, x + w / 2, x + w - 3.2):
        a.circle((bx, y + h - 3.2), 1.1, theme.ART["roof"][2], None)
    for bx in (x + 3.2, x + w - 3.2):
        a.circle((bx, y + 3.2), 1.0, theme.ART["roof"][2], None)


def _verify_ec2(a):
    _section_rebar(a, 4, 4, 15, 24)
    _check(a, 24, 22, 5.5)


def _rebar_schedule(a):
    _sheet(a, 4, 3, 18, 25, rows=3)
    for k in range(3):
        y = 20 + k * 3.5
        a.line((14, y), (30, y), theme.ART["roof"][2], 1.6)


def _structure_quantities(a):
    _sheet(a, 4, 3, 18, 25, rows=4)
    _cube2d(a, 24, 22, 6, "concrete")


def _report(a, x=5, y=3):
    _sheet(a, x, y, 18, 25, rows=2)
    a.poly([(x + 2, y + 18), (x + 6, y + 14), (x + 10, y + 16), (x + 16, y + 10)], None, "blue", 1.1, closed=False)


def _calc_report(a):
    _report(a)
    _check(a, 25, 24, 5)


def _steel_report(a):
    _report(a, 3, 3)
    a.poly([(20, 18), (30, 18), (30, 20.5), (26, 20.5), (26, 26.5), (30, 26.5), (30, 29), (20, 29), (20, 26.5),
            (24, 26.5), (24, 20.5), (20, 20.5)], "steel")


def _verify_panel(a):
    a.poly([(4, 3), (24, 3), (24, 29), (4, 29)], "paper")
    for k in range(3):
        y = 8 + k * 7.5
        if k < 2:
            _check(a, 9, y, 2.4)
        else:
            _cross(a, (9, y), 1.8, 1.4)
        a.line((14, y), (21, y), "detail", 0.9)
    _warning(a, 25, 22, 6)


def _verify_settings(a):
    a.poly([(4, 3), (22, 3), (22, 29), (4, 29)], "paper")
    for k in range(3):
        y = 8 + k * 7.5
        _check(a, 9, y, 2.2)
        a.line((14, y), (19, y), "detail", 0.9)
    _gear(a, 24, 23, 7)


def _verify_sheet(a):
    _sheet(a, 4, 3, 20, 26, rows=4)
    a.poly([(4, 3), (24, 3), (24, 8), (4, 8)], "red")
    a.circle((23, 23), 6.5, "paper", "green", 1.4)
    _check(a, 23, 23, 3.4)


def _rules_editor(a):
    a.poly([(4, 5), (15, 7), (15, 29), (4, 27)], theme.ART["roof"][1])
    a.poly([(15, 7), (26, 5), (26, 27), (15, 29)], theme.ART["roof"][0])
    for k in range(3):
        a.line((17.5, 11 + k * 4), (23.5, 10 + k * 4), "paper", 0.9)
    _pencil(a, 17, 25, 15)


def _check_ifc(a):
    a.box(0, 0, 0, 2.6, 2.6, 2.2, "concrete")
    x, y = a.iso(3.4, -0.8, 2.4)
    a.circle((x, y), 2.0, "paper", "green", 1.2)
    _check(a, x, y, 1.05)


def _check_ids(a):
    _list_sheet(a, 3, 3, 20, 25)
    a.circle((24, 23), 6.5, "paper", "green", 1.4)
    _check(a, 24, 23, 3.4)


def _missing_data(a):
    a.box(0, 0, 0, 2.8, 2.8, 2.2, "concrete")
    x, y = a.iso(3.2, -0.6, 3.6)
    _warning(a, x, y, 1.5)


# ------------------------------------------------------------ Massa e Estudos, Terreno

def _calibrate_image(a):
    _picture(a, 3, 11, 26, 18)
    _dim(a, (3, 5), (29, 5), ext=4.5, colour="blue")


def _control_ring(a):
    _param_surface(a)
    for x in (9, 23):
        path = QtGui.QPainterPath()
        path.addEllipse(QtCore.QPointF(x, 19), 2.6, 8)
        a.path(path, None, "blue", 1.2)
        a.poly([(x - 1.2, 9.8), (x + 1.2, 9.8), (x + 1.2, 12.2), (x - 1.2, 12.2)], "paper", "blue", 0.8)


def _walls_from_cad(a):
    a.face([(0, 0, 0), (6, 0, 0), (6, 4, 0), (0, 4, 0)], "paper", "ink", THIN)
    a.poly([a.iso(0.6, 0.6, 0), a.iso(5.4, 0.6, 0), a.iso(5.4, 3.4, 0)], None, "blue", 0.9, closed=False)
    a.poly([a.iso(0.6, 0.6, 0), a.iso(0.6, 3.4, 0)], None, "blue", 0.9, closed=False)
    a.box(0.6, 3.0, 0, 4.8, 0.4, 2.2, "wall")
    a.arrow(a.iso(3.0, 1.6, 0.2), a.iso(3.0, 1.6, 2.6), width=1.3, head=0.35)


def _model_from_scan(a):
    for k in range(30):
        x = 0.3 + (k * 0.61) % 2.6
        y = 0.3 + (k * 0.37) % 2.6
        z = (k * 0.53) % 2.4
        cx, cy = a.iso(x, y, z)
        a.circle((cx, cy), 0.14, ("blue", "green", "roof")[k % 3], None)
    a.box(4.4, 0.4, 0, 2.2, 2.2, 2.4, "concrete")
    a.arrow(a.iso(2.6, -0.4, 2.6), a.iso(4.6, -0.4, 2.6), width=1.2, head=0.4)


def _site_location(a):
    a.face([(0, 0, 0), (5, 0, 0), (5, 5, 0), (0, 5, 0)], theme.ART["grass"][0], "ink", THIN)
    for k in (1.67, 3.33):
        a.line3((k, 0, 0), (k, 5, 0), theme.ART["grass"][2], 0.5)
        a.line3((0, k, 0), (5, k, 0), theme.ART["grass"][2], 0.5)
    x, y = a.iso(2.5, 2.5, 0)
    path = QtGui.QPainterPath(QtCore.QPointF(x, y))
    path.cubicTo(x - 1.0, y - 1.6, x - 1.6, y - 2.4, x - 1.6, y - 3.4)
    path.arcTo(QtCore.QRectF(x - 1.6, y - 5.0, 3.2, 3.2), 180, -180)
    path.cubicTo(x + 1.6, y - 2.4, x + 1.0, y - 1.6, x, y)
    a.path(path, "red")
    a.circle((x, y - 3.4), 0.6, "paper", "ink", 0.6)


def _terrain_icon(a):
    _terrain(a)


def _lot(a):
    a.poly([(3, 9), (24, 3), (29, 24), (8, 29)], theme.ART["grass"][0], None)
    a.poly([(3, 9), (24, 3), (29, 24), (8, 29)], None, "red", 1.4, dash=[6, 2, 1, 2])
    for x, y in ((3, 9), (24, 3), (29, 24), (8, 29)):
        a.circle((x, y), 1.4, "paper", "red", 0.9)


def _platform(a):
    _terrain(a)
    a.box(1.4, 1.0, 1.0, 2.4, 2.0, 0.45, "concrete")


def _terrain_ramp(a):
    _terrain(a)
    top, left, right = theme.ART["concrete"]
    a.face([(0.4, 2.7, 1.3), (4.6, 2.7, 2.8), (4.6, 2.7, 1.1), (0.4, 2.7, 1.1)], left)
    a.face([(4.6, 1.3, 2.8), (4.6, 2.7, 2.8), (4.6, 2.7, 1.1), (4.6, 1.3, 1.1)], right)
    a.face([(0.4, 1.3, 1.3), (4.6, 1.3, 2.8), (4.6, 2.7, 2.8), (0.4, 2.7, 1.3)], top)


def _edit_platform(a):
    _terrain(a)
    a.box(1.4, 1.0, 1.0, 2.4, 2.0, 0.45, "concrete")
    for p in ((1.4, 1.0, 1.45), (3.8, 1.0, 1.45), (3.8, 3.0, 1.45), (1.4, 3.0, 1.45)):
        x, y = a.iso(*p)
        a.poly([(x - 0.3, y - 0.3), (x + 0.3, y - 0.3), (x + 0.3, y + 0.3), (x - 0.3, y + 0.3)], "paper", "blue", 0.8)


def _earthworks(a):
    def g(x):
        return 17 + 6 * math.sin((x - 3) / 26 * 2 * math.pi)
    xs = [3 + 26 * k / 24 for k in range(25)]
    a.poly([(x, g(x)) for x in xs] + [(29, 29), (3, 29)], theme.ART["earth"][0], None)
    cut = [(x, g(x)) for x in xs if x <= 16] + [(16, 17)]
    fill = [(16, 17)] + [(x, g(x)) for x in xs if x >= 16]
    a.poly(cut + [(3, 17)], theme.ART["roof"][0], "red", 0.6)
    a.poly(fill + [(29, 17)], theme.ART["grass"][0], "green", 0.6)
    a.poly([(x, g(x)) for x in xs], None, theme.ART["grass"][2], 1.6, closed=False)
    a.line((3, 17), (29, 17), "ink", 1.6)


def _slopes(a):
    a.poly([(3, 3), (29, 3), (29, 12), (3, 12)], theme.ART["grass"][0])
    a.poly([(3, 12), (29, 12), (29, 20), (3, 20)], "yellow")
    a.poly([(3, 20), (29, 20), (29, 29), (3, 29)], theme.ART["roof"][0])
    for x in (9, 23):
        a.arrow((x, 6), (x, 26), "ink", 1.3, 0.2)


# ------------------------------------------------------------ Colaborar (Revit's Collaborate)

def _new_note(a):
    a.poly([(4, 6), (26, 6), (26, 22), (20, 28), (4, 28)], "yellow")
    a.poly([(26, 22), (20, 22), (20, 28)], theme.ART["new"][2])
    for y in (12, 17):
        a.line((8, y), (22, y), "ink", 0.8)
    _spark(a, (27, 5), 3.5)


def _share(a):
    _person(a, 9, 18, 7, "blue")
    _person(a, 23, 18, 7, "green")
    a.arrow((12, 5), (21, 5), width=1.3, head=0.35)
    a.arrow((20, 29), (12, 29), "green", 1.3, 0.35)


def _open_shared(a):
    a.poly([(3, 9), (12, 9), (14, 12), (29, 12), (29, 29), (3, 29)], "yellow")
    a.poly([(3, 14), (29, 14), (29, 29), (3, 29)], theme.ART["new"][0])
    _person(a, 12, 22, 5, "blue")
    _person(a, 21, 22, 5, "green")


def _sync(a):
    for start in (30, 210):
        path = QtGui.QPainterPath()
        rect = QtCore.QRectF(5, 5, 22, 22)
        path.arcMoveTo(rect, start)
        path.arcTo(rect, start, 140)
        a.path(path, None, "blue", 1.8)
        end = math.radians(start + 140)
        ex, ey = 16 + 11 * math.cos(end), 16 - 11 * math.sin(end)
        tx, ty = -math.sin(end), -math.cos(end)                    # (the way the arc goes, in the picture)
        nx, ny = -ty, tx
        a.poly([(ex + tx * 3 + nx * 2, ey + ty * 3 + ny * 2), (ex + tx * 3 - nx * 2, ey + ty * 3 - ny * 2),
                (ex + tx * 0.2, ey + ty * 0.2)], "blue", "blue", 0.6)
    _cube2d(a, 16, 16.5, 5, "concrete")


def _reserve_views(a):
    a.poly([(3, 4), (23, 4), (23, 26), (3, 26)], "paper")
    a.poly([(6, 8), (20, 8), (20, 18), (6, 18)], theme.ART["glass"][0], "blue", 0.8)
    _lock(a, 24, 24, 7)


def _give_back(a):
    a.poly([(3, 4), (23, 4), (23, 26), (3, 26)], "paper")
    a.poly([(6, 8), (20, 8), (20, 18), (6, 18)], theme.ART["glass"][0], "blue", 0.8)
    _lock(a, 24, 24, 7, opened=True)


def _clashes(a):
    a.box(0, 0, 0, 5, 1.2, 1.2, "steel")
    _cylinder(a, (2.4, -1.6, 0.6), (2.4, 3.2, 0.6), 0.6, "water")
    x, y = a.iso(2.4, 0.6, 1.2)
    a.circle((x, y), 1.6, None, "red", 1.6)


# ------------------------------------------------------------ (0.536, 4.ª leva) helpers

def _screen(a, x, y, w, h, fill=None):
    """A screen (a view, a window): its frame and its stand."""
    a.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], "paper")
    a.poly([(x + 1.5, y + 1.5), (x + w - 1.5, y + 1.5), (x + w - 1.5, y + h - 1.5), (x + 1.5, y + h - 1.5)],
           fill or theme.ART["glass"][0], "ink", THIN)


def _arrow_out(a, x, y):
    a.arrow((x, y), (x + 9, y - 9), "green", 1.8, 0.4)


def _house_box(a):
    """A small house in space: the model one looks at."""
    a.box(0, 0, 0, 3, 2.4, 1.8, "wall")
    top, _left, right = theme.ART["roof"]
    a.face([(0, 0, 1.8), (3, 0, 1.8), (3, 1.2, 2.9), (0, 1.2, 2.9)], right)
    a.face([(0, 1.2, 2.9), (3, 1.2, 2.9), (3, 2.4, 1.8), (0, 2.4, 1.8)], top)
    a.face([(3, 0, 1.8), (3, 2.4, 1.8), (3, 1.2, 2.9)], theme.ART["wall"][2])


def _slab_stack(a, n=3, lit=None, material="concrete"):
    for k in range(n):
        a.box(0, 0, k * 1.6, 4, 3, 0.35, ("new" if k == lit else material))


def _floppy(a):
    a.poly([(4, 4), (24, 4), (28, 8), (28, 28), (4, 28)], "blue")
    a.poly([(9, 4), (21, 4), (21, 12), (9, 12)], "paper")
    a.poly([(17, 5.5), (19.5, 5.5), (19.5, 10.5), (17, 10.5)], "blue", None)
    a.poly([(8, 17), (24, 17), (24, 28), (8, 28)], "paper")
    for y in (21, 24.5):
        a.line((10.5, y), (21.5, y), "detail", 0.8)


def _folder(a, x=3, y=7, w=26, h=22):
    a.poly([(x, y), (x + w * 0.35, y), (x + w * 0.43, y + 3), (x + w, y + 3), (x + w, y + h), (x, y + h)], "yellow")


def _page(a, x, y, w, h, band=None):
    a.poly([(x, y), (x + w - 5, y), (x + w, y + 5), (x + w, y + h), (x, y + h)], "paper")
    a.poly([(x + w - 5, y), (x + w - 5, y + 5), (x + w, y + 5)], theme.ART["concrete"][0], "ink", THIN)
    if band:
        a.poly([(x - 2, y + h * 0.55), (x + w * 0.75, y + h * 0.55), (x + w * 0.75, y + h * 0.82),
                (x - 2, y + h * 0.82)], band)


def _tab(a, x, y, w, h, active=True):
    a.poly([(x, y + h), (x + 2, y), (x + w - 2, y), (x + w, y + h)], "paper" if active else theme.ART["concrete"][0])


def _mouse(a, x, y, s):
    path = QtGui.QPainterPath()
    path.addRoundedRect(QtCore.QRectF(x - s * 0.55, y - s, s * 1.1, s * 2), s * 0.55, s * 0.55)
    a.path(path, "paper")
    a.line((x - s * 0.55, y - s * 0.15), (x + s * 0.55, y - s * 0.15), "ink", 0.8)
    a.line((x, y - s), (x, y - s * 0.15), "ink", 0.8)
    path = QtGui.QPainterPath()
    path.addRoundedRect(QtCore.QRectF(x - s * 0.13, y - s * 0.78, s * 0.26, s * 0.46), s * 0.12, s * 0.12)
    a.path(path, "blue", "ink", 0.6)


# ------------------------------------------------------------ Visualizar (Revit's View)

def _view_styles(a):
    a.box(0, 0, 0, 2.6, 2.6, 2.4, "concrete")
    a.face([(0, 0, 2.4), (2.6, 0, 2.4), (2.6, 2.6, 2.4), (0, 2.6, 2.4)], None, "ink")
    a.box(3.6, 1.0, 0, 2.6, 2.6, 2.4, (theme.ART["paper"], theme.ART["paper"], theme.ART["paper"]), "blue")


def _graphic_styles(a):
    for k, w in enumerate((0.7, 1.5, 2.6)):
        a.line((4, 8 + k * 6), (20, 8 + k * 6), "ink", w)
    _pencil(a, 18, 27, 13)


def _templates(a):
    _page(a, 4, 3, 20, 26)
    a.poly([(7, 7), (19, 7), (19, 17), (7, 17)], theme.ART["glass"][0], "blue", 0.8)
    a.line((7, 21), (19, 21), "detail", 0.8)
    a.line((7, 24), (16, 24), "detail", 0.8)
    _spark(a, (27, 24), 3.5)


def _hatch_square(a, x, y, s):
    a.poly([(x, y), (x + s, y), (x + s, y + s), (x, y + s)], "paper")
    for k in range(1, 7):
        t = s * k / 7 * 2
        x0, x1 = max(0.0, t - s), min(s, t)
        a.line((x + x0, y + t - x0), (x + x1, y + t - x1), "ink", 0.7)
    a.poly([(x, y), (x + s, y), (x + s, y + s), (x, y + s)], None, "ink")


def _element_hatches(a):
    a.box(0, 0, 0, 4, 1.2, 2.6, "wall")
    for k in range(-5, 8):                                         # (its hatch on the face one sees: x − z = t)
        t = k * 0.6
        x0, x1 = max(0.0, t), min(4.0, t + 2.6)
        if x1 > x0:
            a.line3((x0, 1.2, x0 - t), (x1, 1.2, x1 - t), "ink", 0.6)
    x, y = a.iso(4.4, 1.6, 4.2)
    _hatch_square(a, x, y, 1.8)


def _reset_patterns(a):
    _hatch_square(a, 4, 8, 16)
    path = QtGui.QPainterPath()
    rect = QtCore.QRectF(16, 15, 13, 13)
    path.arcMoveTo(rect, 90)
    path.arcTo(rect, 90, 270)
    a.path(path, None, "blue", 1.6)
    a.poly([(22.5, 12.6), (25.4, 15), (22.5, 17.4)], "blue", "blue", 0.8)


def _thin_lines(a):
    a.poly([(3, 3), (29, 3), (29, 29), (3, 29)], None, "ink", 0.5)
    a.poly([(6, 6), (26, 6), (26, 26), (6, 26)], None, "ink", 0.5)
    a.poly([(15, 6), (17, 6), (17, 26), (15, 26)], None, "ink", 0.5)
    a.line((6, 16), (15, 16), "ink", 0.5)


def _render(a):
    grad = QtGui.QPainterPath()
    grad.addEllipse(QtCore.QPointF(14, 18), 10, 10)
    a.path(grad, theme.ART["glass"][1])
    a.circle((11, 15), 3.5, theme.ART["glass"][0], None)
    a.circle((26, 6), 3.6, "yellow")
    for t in range(0, 360, 45):
        r = math.radians(t)
        a.line((26 + 4.8 * math.cos(r), 6 + 4.8 * math.sin(r)), (26 + 6.4 * math.cos(r), 6 + 6.4 * math.sin(r)),
               "yellow", 1.1)


def _panorama(a):
    path = QtGui.QPainterPath()
    path.addEllipse(QtCore.QPointF(16, 16), 13, 5)
    a.path(path, None, "blue", 1.4)
    _picture(a, 6, 9, 20, 13)
    a.poly([(27.5, 13.5), (29.4, 17.5), (25.4, 17.7)], "blue", "blue", 0.8)


def _splat(a):
    for k, (x, y, rx, ry, c) in enumerate(((10, 12, 7, 4.5, "blue"), (20, 10, 6, 3.5, "yellow"),
                                            (16, 20, 8, 5, "green"), (24, 22, 5, 3, "red"),
                                            (8, 23, 4.5, 3, "roof"))):
        path = QtGui.QPainterPath()
        path.addEllipse(QtCore.QPointF(x, y), rx, ry)
        t = QtGui.QTransform()
        t.translate(x, y)
        t.rotate((k * 37) % 90 - 30)
        t.translate(-x, -y)
        a.path(t.map(path), c, None)


def _presentation_panel(a):
    _screen(a, 3, 5, 26, 18)
    a.poly([(13, 9), (13, 19), (21, 14)], "blue", None)
    a.line((16, 23), (16, 28), "ink", 1.2)
    a.line((10, 28), (22, 28), "ink", 1.6)


def _export_image(a):
    _picture(a, 3, 11, 20, 16)
    _arrow_out(a, 20, 13)


def _export_model(a):
    a.box(0, 0, 0, 2.6, 2.6, 2.2, "concrete")
    a.arrow(a.iso(2.2, 0.4, 2.6), a.iso(4.8, -1.6, 5.0), "green", 1.8, 0.38)


def _export_presentation(a):
    _screen(a, 3, 10, 22, 16)
    a.poly([(11, 14), (11, 22), (17.5, 18)], "blue", None)
    _arrow_out(a, 20, 12)


def _iso(a):
    _house_box(a)
    a.line3((-0.6, -0.6, 0), (3.6, -0.6, 0), "blue", 0.8)
    a.line3((-0.6, -0.6, 0), (-0.6, 3.0, 0), "blue", 0.8)
    a.line3((-0.6, -0.6, 0), (-0.6, -0.6, 3.4), "blue", 0.8)


def _top(a):
    a.poly([(6, 8), (26, 8), (26, 28), (6, 28)], theme.ART["roof"][0])
    a.line((6, 18), (26, 18), "ink", 1.0)
    a.arrow((16, 1), (16, 11), width=1.8, head=0.4)


def _front(a):
    a.poly([(10, 16), (20, 7), (30, 16), (30, 29), (10, 29)], theme.ART["wall"][0])
    a.poly([(17, 21), (23, 21), (23, 29), (17, 29)], theme.ART["wood"][1])
    a.arrow((1, 22), (8, 22), width=1.8, head=0.4)


def _view3d_new(a):
    _house_box(a)
    _spark(a, a.iso(3.6, -0.8, 4.2), 1.2)


def _plan(a):
    _plan_walls(a, 4, 4, 28, 28, t=2.2)
    a.poly([(15, 6.2), (17, 6.2), (17, 25.8), (15, 25.8)], theme.ART["wall"][2])
    a.poly([(6.2, 16), (11, 16), (11, 18), (6.2, 18)], theme.ART["wall"][2])
    path = QtGui.QPainterPath(QtCore.QPointF(17, 12))
    path.arcTo(QtCore.QRectF(11, 6.2, 12, 12), 0, -90)
    a.path(path, None, "detail", 0.7)


def _section_head(a, x, y, r, down=True):
    path = QtGui.QPainterPath()
    path.moveTo(x - r, y)
    path.arcTo(QtCore.QRectF(x - r, y - r, 2 * r, 2 * r), 180, 180 if down else -180)
    path.closeSubpath()
    a.path(path, "blue", "ink", 0.6)
    a.circle((x, y), r, None, "ink", 0.9)


def _section(a):
    a.poly([(8, 12), (24, 12), (24, 26), (8, 26)], theme.ART["wall"][0])
    a.line((3, 19), (29, 19), "ink", 1.2, dash=[6, 2, 1, 2])
    _section_head(a, 4, 9, 3.2)
    _section_head(a, 28, 9, 3.2)
    a.line((4, 12.2), (4, 19), "ink", 1.0)
    a.line((28, 12.2), (28, 19), "ink", 1.0)


def _detail(a):
    _plan_walls(a, 3, 3, 21, 21, t=2.0)
    a.circle((20, 20), 7, None, "blue", 1.3)
    a.line((25, 25), (30, 30), "blue", 2.2)


def _last_section(a):
    _section(a)
    path = QtGui.QPainterPath()
    path.arcMoveTo(QtCore.QRectF(18, 20, 11, 11), 200)
    path.arcTo(QtCore.QRectF(18, 20, 11, 11), 200, -250)
    a.path(path, None, "green", 1.5)
    a.poly([(17.4, 22.6), (19, 26.6), (21.3, 23.2)], "green", "green", 0.6)


def _box(a):
    _house_box(a)
    pts = [(-0.5, -0.5), (3.5, -0.5), (3.5, 2.9), (-0.5, 2.9)]
    for z in (-0.2, 3.4):
        a.face([(x, y, z) for x, y in pts], None, "blue", 0.9)
    for x, y in pts:
        a.line3((x, y, -0.2), (x, y, 3.4), "blue", 0.9)
    x, y = a.iso(3.5, 1.2, 1.6)
    a.poly([(x - 0.35, y - 0.35), (x + 0.35, y - 0.35), (x + 0.35, y + 0.35), (x - 0.35, y + 0.35)], "paper", "blue",
           0.8)


def _box_selection(a):
    a.box(0.6, 0.6, 0, 1.6, 1.6, 1.6, "wood")
    pts = [(0, 0), (2.8, 0), (2.8, 2.8), (0, 2.8)]
    for z in (-0.2, 2.2):
        a.face([(x, y, z) for x, y in pts], None, "blue", 0.9, dash=[3, 2])
    for x, y in pts:
        a.line3((x, y, -0.2), (x, y, 2.2), "blue", 0.9, dash=[3, 2])


def _position_camera(a):
    a.poly([(4, 10), (18, 10), (18, 20), (4, 20)], theme.ART["concrete"][2])
    a.poly([(18, 13), (25, 9), (25, 21), (18, 17)], theme.ART["concrete"][1])
    a.circle((9, 15), 2.6, theme.ART["glass"][1])
    for x in (6, 11, 16):
        a.line((11, 20), (x, 30), "ink", 1.2)
    a.line((26, 15), (31, 15), "blue", 1.2, dash=[2, 1.5])


def _look_around(a):
    _eye(a, 16, 18, 8)
    path = QtGui.QPainterPath()
    rect = QtCore.QRectF(4, 3, 24, 8)
    path.arcMoveTo(rect, 200)
    path.arcTo(rect, 200, -220)
    a.path(path, None, "blue", 1.4)
    a.poly([(26.6, 5.0), (29.2, 8.4), (25.2, 8.6)], "blue", "blue", 0.6)


def _walk(a):
    for k, (x, y, rot) in enumerate(((10, 24, -12), (19, 15, 8), (12, 7, -12))):
        path = QtGui.QPainterPath()
        path.addEllipse(QtCore.QPointF(x, y), 2.4, 4.0)
        path.addEllipse(QtCore.QPointF(x, y + 5.6), 1.7, 1.7)
        t = QtGui.QTransform()
        t.translate(x, y)
        t.rotate(rot)
        t.translate(-x, -y)
        a.path(t.map(path), "ink" if k % 2 == 0 else "detail", None)


def _panels(a):
    a.poly([(3, 4), (29, 4), (29, 28), (3, 28)], "paper")
    a.poly([(3, 4), (29, 4), (29, 8), (3, 8)], theme.ART["glass"][1])
    a.poly([(5, 10), (11, 10), (11, 26), (5, 26)], theme.ART["concrete"][0], "ink", THIN)
    a.poly([(13, 10), (27, 10), (27, 26), (13, 26)], theme.ART["glass"][0], "ink", THIN)


def _view_tabs(a):
    _tab(a, 3, 6, 12, 6, active=False)
    _tab(a, 13, 6, 12, 6, active=True)
    a.poly([(3, 12), (29, 12), (29, 28), (3, 28)], "paper")


def _next_view(a):
    _view_tabs(a)
    a.arrow((8, 20), (24, 20), width=1.8, head=0.35)


def _prev_view(a):
    _view_tabs(a)
    a.arrow((24, 20), (8, 20), width=1.8, head=0.35)


def _close_view(a):
    _view_tabs(a)
    _cross(a, (16, 20), 4, 2.0)


def _theme_light(a):
    a.circle((16, 16), 6.5, "yellow")
    for t in range(0, 360, 45):
        r = math.radians(t)
        a.line((16 + 9 * math.cos(r), 16 + 9 * math.sin(r)), (16 + 13 * math.cos(r), 16 + 13 * math.sin(r)), "yellow",
               1.8)


def _theme_dark(a):
    path = QtGui.QPainterPath()
    path.addEllipse(QtCore.QPointF(15, 16), 12, 12)
    cut = QtGui.QPainterPath()
    cut.addEllipse(QtCore.QPointF(21, 11), 10, 10)
    a.path(path.subtracted(cut), theme.ART["steel"][1])
    _spark(a, (25, 24), 3)


def _canvas_dark(a):
    a.poly([(3, 5), (29, 5), (29, 27), (3, 27)], theme.ART["steel"][2])
    for k in (1, 2, 3):
        a.line((3 + 26 * k / 4, 5), (3 + 26 * k / 4, 27), theme.ART["steel"][0], 0.6)
        a.line((3, 5 + 22 * k / 4), (29, 5 + 22 * k / 4), theme.ART["steel"][0], 0.6)


def _theme_studio(a):
    path = QtGui.QPainterPath()
    path.moveTo(16, 4)
    path.cubicTo(30, 4, 31, 17, 26, 21)
    path.cubicTo(22, 24, 20, 20, 18, 24)
    path.cubicTo(16, 29, 12, 29, 9, 27)
    path.cubicTo(2, 23, 2, 4, 16, 4)
    a.path(path, theme.ART["wood"][0])
    for (x, y), c in (((10, 10), "red"), ((17, 8.5), "yellow"), ((23.5, 11), "blue"), ((8, 18), "green")):
        a.circle((x, y), 2.4, c, "ink", 0.6)


def _mouse_sketchup(a):
    _mouse(a, 10, 17, 8)
    _cube2d(a, 24, 18, 4.5, "concrete")
    path = QtGui.QPainterPath()
    rect = QtCore.QRectF(17, 7, 14, 6)
    path.arcMoveTo(rect, 200)
    path.arcTo(rect, 200, -200)
    a.path(path, None, "blue", 1.2)


def _mouse_revit(a):
    _mouse(a, 10, 17, 8)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        a.arrow((24 + dx * 1.5, 18 + dy * 1.5), (24 + dx * 6, 18 + dy * 6), width=1.3, head=0.4)


# ------------------------------------------------------------ Gerenciar (Revit's Manage)

def _types(a):
    """A wall's type: its layers (masonry, insulation, plaster), seen at its end."""
    a.box(0, 0, 0, 4, 0.7, 2.6, "wall")
    a.box(0, 0.7, 0, 4, 0.35, 2.6, "new")
    a.box(0, 1.05, 0, 4, 0.2, 2.6, "concrete")


def _patterns(a):
    a.poly([(4, 4), (28, 4), (28, 28), (4, 28)], theme.ART["wall"][0])
    for k, y in enumerate((10, 16, 22)):
        a.line((4, y), (28, y), "ink", 0.8)
    for k, y in enumerate((4, 10, 16, 22)):
        for x in ((10, 22) if k % 2 == 0 else (16,)):
            a.line((x, y), (x, y + 6), "ink", 0.8)


def _type_lists(a):
    _list_sheet(a, 4, 4, 22, 24)
    for k in range(4):
        y = 4 + 24 * (k + 0.8) / 4.6
        a.poly([(6, y - 1.2), (8.4, y - 1.2), (8.4, y + 1.2), (6, y + 1.2)],
               ("wall", "concrete", "wood", "glass")[k], None)


def _phase(a):
    for k, (x0, x1, c) in enumerate(((3, 14, "concrete"), (10, 22, "wall"), (18, 29, "new"))):
        y = 8 + k * 7
        a.poly([(x0, y), (x1, y), (x1, y + 4.5), (x0, y + 4.5)], c)
    a.line((3, 29), (29, 29), "ink", 1.0)
    for x in (3, 11.7, 20.3, 29):
        a.line((x, 27.5), (x, 30.5), "ink", 1.0)


def _storey_up(a):
    _slab_stack(a, lit=2)
    a.arrow(a.iso(4.8, 0, 0.5), a.iso(4.8, 0, 3.8), width=1.5, head=0.3)


def _storey_down(a):
    _slab_stack(a, lit=0)
    a.arrow(a.iso(4.8, 0, 3.8), a.iso(4.8, 0, 0.5), width=1.5, head=0.3)


def _only_active(a):
    for k in range(3):
        a.box(0, 0, k * 1.6, 4, 3, 0.35, "new" if k == 1 else "concrete", "ink" if k == 1 else "detail")
    _eye(a, *a.iso(5.6, -0.6, 2.6), 1.3)


def _repeat(a):
    _slab_stack(a, n=2)
    a.box(0, 0, 3.2, 4, 3, 0.35, "new", "detail")
    a.arrow(a.iso(4.8, 0, 2.0), a.iso(4.8, 0, 3.4), width=1.3, head=0.4)


def _typical(a):
    _slab_stack(a, n=4, material="concrete")
    _spark(a, a.iso(4.6, -0.6, 6.4), 1.1)


def _component_edit(a):
    a.box(0, 0, 0, 2.4, 2.4, 2.0, "wood")
    x, y = a.iso(1.8, 0.0, 2.6)
    _pencil(a, x, y, 3.4)


def _component_close(a):
    a.box(0, 0, 0, 2.4, 2.4, 2.0, "wood")
    x, y = a.iso(3.4, -0.4, 2.8)
    a.circle((x, y), 1.4, "paper", "green", 1.0)
    _check(a, x, y, 0.75)


def _group_ungroup(a):
    a.box(0, 0, 0, 1.4, 1.4, 1.4, "concrete")
    a.box(3.0, 1.0, 0, 1.4, 1.4, 2.0, "wood")
    a.arrow(a.iso(1.9, 0.6, 1.0), a.iso(1.2, -0.2, 2.6), width=1.0, head=0.4)
    a.arrow(a.iso(2.6, 1.0, 1.0), a.iso(3.6, 1.4, 3.0), width=1.0, head=0.4)


def _chip(a, x, y, s):
    """A chip (the AI): its pins on the four sides, its body, a spark."""
    for k in (-0.4, 0.0, 0.4):
        for side in (-1, 1):
            a.line((x + k * s, y + side * s * 0.7), (x + k * s, y + side * s), "ink", 0.9)
            a.line((x + side * s * 0.7, y + k * s), (x + side * s, y + k * s), "ink", 0.9)
    a.poly([(x - s * 0.7, y - s * 0.7), (x + s * 0.7, y - s * 0.7), (x + s * 0.7, y + s * 0.7),
            (x - s * 0.7, y + s * 0.7)], theme.ART["steel"][2])
    _spark(a, (x, y), s * 0.5)


def _ai_link(a):
    _chip(a, 13, 13, 9)
    _link(a, 25, 25, 8)


def _ai_install(a):
    _chip(a, 13, 13, 9)
    a.arrow((25, 16), (25, 29), "green", 2.0, 0.4)


# ------------------------------------------------------------ Início (Revit's File)

def _new(a):
    _page(a, 6, 3, 20, 26)
    _spark(a, (25, 24), 4)


def _open(a):
    _folder(a)
    a.poly([(3, 29), (8, 15), (31, 15), (26, 29)], theme.ART["new"][0])


def _save(a):
    _floppy(a)


def _save_as(a):
    _floppy(a)
    _pencil(a, 21, 28, 12)


def _start_page(a):
    a.poly([(4, 15), (16, 4), (28, 15)], "roof")
    a.poly([(7, 14), (25, 14), (25, 28), (7, 28)], theme.ART["wall"][0])
    a.poly([(13, 19), (19, 19), (19, 28), (13, 28)], theme.ART["wood"][1])


def _new_from_base(a):
    _page(a, 9, 6, 20, 24)
    _page(a, 4, 2, 20, 24)
    a.poly([(7, 6), (17, 6), (17, 14), (7, 14)], theme.ART["glass"][0], "blue", 0.8)
    _spark(a, (25, 25), 4)


def _pdf(a):
    _page(a, 6, 3, 20, 26, band="red")


def _dxf(a):
    _page(a, 6, 3, 20, 26, band="blue")
    a.poly([(10, 8), (20, 8), (20, 14)], None, "blue", 0.9, closed=False)


def _sheets_pdf(a):
    _page(a, 10, 2, 18, 22)
    _page(a, 6, 5, 18, 22)
    _page(a, 3, 8, 18, 22, band="red")


def _sheets_by_storey(a):
    _page(a, 3, 3, 18, 24, band="red")
    for k in range(3):
        a.poly([(17, 25 - k * 4), (29, 25 - k * 4), (29, 27 - k * 4), (17, 27 - k * 4)],
               "new" if k == 1 else "concrete")


def _help(a):
    a.circle((16, 16), 13, "blue", None)
    path = QtGui.QPainterPath(QtCore.QPointF(11.5, 12))
    path.cubicTo(11.5, 6.5, 20.5, 6.5, 20.5, 11.5)
    path.cubicTo(20.5, 15, 16, 15, 16, 19)
    a.path(path, None, "paper", 2.6)
    a.circle((16, 23.5), 1.6, "paper", None)


def _quit(a):
    a.poly([(4, 3), (18, 3), (18, 29), (4, 29)], theme.ART["wood"][1])
    a.poly([(4, 3), (13, 6), (13, 31), (4, 29)], theme.ART["wood"][2])
    a.arrow((15, 16), (30, 16), "red", 2.0, 0.35)


# ------------------------------------------------------------ Modificar | Paredes (contextual)

def _flip_walls(a):
    a.box(0, 0, 0, 5, 1, 2.4, "wall")
    x, y = a.iso(2.5, 1.0, 3.6)
    a.arrow((x - 2, y), (x + 2, y), width=1.1, head=0.3)
    a.arrow((x + 2, y + 1.3), (x - 2, y + 1.3), width=1.1, head=0.3)


def _edit_profile(a):
    a.face([(0, 0, 0), (5, 0, 0), (5, 0, 3), (2.5, 0, 4.2), (0, 0, 3)], theme.ART["wall"][1])
    for p in ((0, 0, 3), (2.5, 0, 4.2), (5, 0, 3)):
        x, y = a.iso(*p)
        a.poly([(x - 0.3, y - 0.3), (x + 0.3, y - 0.3), (x + 0.3, y + 0.3), (x - 0.3, y + 0.3)], "paper", "blue", 0.8)
    a.face([(0, 0, 3), (2.5, 0, 4.2), (5, 0, 3)], None, "blue", 1.1)


def _reset_profile(a):
    a.face([(0, 0, 0), (5, 0, 0), (5, 0, 3), (0, 0, 3)], theme.ART["wall"][1])
    a.face([(0, 0, 3), (2.5, 0, 4.2), (5, 0, 3)], None, "detail", 0.8, dash=[3, 2])
    x, y = a.iso(2.5, 0, 1.5)
    path = QtGui.QPainterPath()
    rect = QtCore.QRectF(x - 1.1, y - 1.1, 2.2, 2.2)
    path.arcMoveTo(rect, 90)
    path.arcTo(rect, 90, 270)
    a.path(path, None, "blue", 1.4)


def _attach(a, top, attach):
    a.box(0, 0, 0, 4, 0.8, 2.4, "wall")
    z = 3.4 if top else -1.0
    a.box(-0.4, -0.6, z, 4.8, 2.0, 0.35, "concrete")
    x, y = a.iso(2.0, 0.8, 1.2)
    sign = -1 if top else 1
    if attach:
        a.arrow((x, y), (x, y + sign * 2.0), width=1.3, head=0.4)
    else:
        a.arrow((x, y + sign * 2.0), (x, y), width=1.3, head=0.4)
        _cross(a, (x + 1.6, y + sign * 1.0), 0.5, 1.2)


def _attach_top(a):
    _attach(a, True, True)


def _detach_top(a):
    _attach(a, True, False)


def _attach_base(a):
    _attach(a, False, True)


def _detach_base(a):
    _attach(a, False, False)


def _dims_axes(a):
    for y in (8, 22):
        a.poly([(3, y - 2.5), (29, y - 2.5), (29, y + 2.5), (3, y + 2.5)], theme.ART["wall"][0])
        a.line((3, y), (29, y), "ink", 0.7, dash=[5, 2, 1, 2])
    _dim(a, (16, 8), (16, 22), ext=1.2, colour="blue")


def _dims_faces(a):
    for y in (8, 22):
        a.poly([(3, y - 2.5), (29, y - 2.5), (29, y + 2.5), (3, y + 2.5)], theme.ART["wall"][0])
    _dim(a, (16, 10.5), (16, 19.5), ext=1.2, colour="blue")


def _merge_walls(a):
    a.box(0, 0, 0, 2.4, 1, 2.6, "wall")
    a.box(2.4, 0, 0, 2.4, 1, 2.6, "wall")
    a.line3((2.4, 1, 0), (2.4, 1, 2.6), "green", 1.2, dash=[2, 1.5])
    x, y = a.iso(2.4, 1, 3.6)
    a.arrow((x - 2.2, y), (x - 0.3, y), "green", 1.1, 0.4)
    a.arrow((x + 2.2, y), (x + 0.3, y), "green", 1.1, 0.4)


def _join_wall_ends(a):
    _l_walls(a)
    a.circle(a.iso(0.5, 0.5, 2.4), 0.6, "green", "ink", 0.6)


def _unjoin_walls(a):
    a.box(0, 0, 0, 1, 3.6, 2.4, "wall")
    a.box(1.5, 0, 0, 3.5, 1, 2.4, "wall")
    _cross(a, a.iso(1.25, 0.5, 3.2), 0.5, 1.4)


def _orthogonalize(a):
    a.poly([(4, 26), (6, 6), (27, 9)], None, "detail", 1.0, closed=False, dash=[3, 2])
    a.poly([(4, 27), (4, 6), (27, 6)], None, "ink", 2.0, closed=False)
    a.poly([(4, 10), (8, 10), (8, 6)], None, "blue", 1.0, closed=False)


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
         "grid_generate": _grid_generate, "grid_settings": _grid_settings,
         # (0.536) Instalações, Inserir, Anotar, Analisar, Massa, Terreno, Colaborar
         "duct": _duct, "air_terminal": _air_terminal, "equipment": _equipment, "pipe": _pipe, "fixture": _fixture,
         "connect_network": _connect_network, "water_proposal": _water_proposal,
         "remove_water_proposal": _remove_water_proposal, "electrical": _electrical, "conduit": _conduit,
         "light": _light, "new_circuit": _new_circuit, "route_circuits": _route_circuits,
         "electrical_proposal": _electrical_proposal, "remove_electrical_proposal": _remove_electrical_proposal,
         "electrical_check": _electrical_check,
         "cad_link": _cad_link, "cloud_link": _cloud_link, "cad_links": _cad_links, "cloud_links": _cloud_links,
         "import_image": _import_image, "import_model": _import_model, "images": _images,
         "import_components": _import_components, "terrain_points": _terrain_points, "terrain_dxf": _terrain_dxf,
         "dim_exterior": _dim_exterior, "dim_interior": _dim_interior, "dimension_walls": _dimension_walls,
         "dimension_facades": _dimension_facades, "dimension_rooms": _dimension_rooms,
         "dimension_style": _dimension_style, "draft": _draft, "renumber": _renumber,
         "keynote_table": _keynote_table, "symbol_styles": _symbol_styles,
         "analyse": _analyse, "analytical": _analytical, "actions": _actions, "show_analytical": _show_analytical,
         "moments": _moments, "verify_ec2": _verify_ec2, "rebar_schedule": _rebar_schedule,
         "structure_quantities": _structure_quantities, "calc_report": _calc_report, "steel_report": _steel_report,
         "verify_panel": _verify_panel, "verify_settings": _verify_settings, "verify_sheet": _verify_sheet,
         "rules_editor": _rules_editor, "check_ifc": _check_ifc, "check_ids": _check_ids,
         "missing_data": _missing_data,
         "calibrate_image": _calibrate_image, "control_ring": _control_ring, "organic_form": _organic_form,"walls_from_cad": _walls_from_cad,
         "model_from_scan": _model_from_scan,
         "site_location": _site_location, "terrain": _terrain_icon, "lot": _lot, "platform": _platform,
         "terrain_ramp": _terrain_ramp, "edit_platform": _edit_platform, "earthworks": _earthworks,
         "slopes": _slopes,
         "new_note": _new_note, "share": _share, "open_shared": _open_shared, "sync": _sync,
         "reserve_views": _reserve_views, "give_back": _give_back, "clashes": _clashes,
         # Visualizar, Gerenciar, Início, Modificar | Paredes
         "view_styles": _view_styles, "graphic_styles": _graphic_styles, "templates": _templates,
         "element_hatches": _element_hatches, "reset_patterns": _reset_patterns, "thin_lines": _thin_lines,
         "render": _render, "panorama": _panorama, "splat": _splat, "presentation_panel": _presentation_panel,
         "export_image": _export_image, "export_model": _export_model,
         "export_presentation": _export_presentation, "iso": _iso, "top": _top, "front": _front,
         "view3d_new": _view3d_new, "plan": _plan, "section": _section, "detail": _detail,
         "last_section": _last_section, "box": _box, "box_selection": _box_selection,
         "position_camera": _position_camera, "look_around": _look_around, "walk": _walk, "panels": _panels,
         "next_view": _next_view, "prev_view": _prev_view, "close_view": _close_view,
         "theme_light": _theme_light, "theme_dark": _theme_dark, "canvas_dark": _canvas_dark,
         "theme_studio": _theme_studio, "mouse_sketchup": _mouse_sketchup, "mouse_revit": _mouse_revit,
         "types": _types, "patterns": _patterns, "type_lists": _type_lists, "phase": _phase,
         "storey_up": _storey_up, "storey_down": _storey_down, "only_active": _only_active, "repeat": _repeat,
         "typical": _typical, "component_edit": _component_edit, "component_close": _component_close,
         "group_ungroup": _group_ungroup, "ai_link": _ai_link, "ai_install": _ai_install,
         "new": _new, "open": _open, "save": _save, "save_as": _save_as, "start_page": _start_page,
         "new_from_base": _new_from_base, "pdf": _pdf, "dxf": _dxf, "sheets_pdf": _sheets_pdf,
         "sheets_by_storey": _sheets_by_storey, "help": _help, "quit": _quit,
         "flip_walls": _flip_walls, "edit_profile": _edit_profile, "reset_profile": _reset_profile,
         "attach_top": _attach_top, "detach_top": _detach_top, "attach_base": _attach_base,
         "detach_base": _detach_base, "dims_axes": _dims_axes, "dims_faces": _dims_faces,
         "merge_walls": _merge_walls, "join_wall_ends": _join_wall_ends, "unjoin_walls": _unjoin_walls,
         "orthogonalize": _orthogonalize}
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
