"""(0.313) Each type's miniature, as Revit's Type Selector shows its preview, and the list that picks a type by it:

- a door / window: its design in elevation (core.joinery's pieces in their materials' colours, how its leaves open);
- a wall: its layers in section, side by side (the outside on the left), each in its material's colour and hatch;
- a slab, a roof, a strip footing: its layers stacked (the first at the bottom);
- a column, a pile, a pad, a pile cap (its piles under it): its section seen from above; a beam: its section;
- a pipe, a duct, a conduit: its section, hollow.

Walls, slabs and roofs drawn at one scale (40 cm the miniature's width): a thicker one looks thicker. Each made once
for its type and its materials' colours (a QIcon, kept)."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import joinery as core_joinery
from ..ifc import catalog
from . import pattern_paint
from .joinery_dialog import paint_pieces

LIST_SIZE = 56                     # px: a miniature in the lists that pick a type
SIZES = (24, 128)                  # px: drawn at these (a small one with lines that still show), scaled between
SCALE_TO = 0.40                    # m: walls', slabs' and roofs' layers drawn so that this takes the miniature
INK = QtGui.QColor("#2b2f36")
HATCH = {"brick": QtCore.Qt.BrushStyle.BDiagPattern, "concrete": QtCore.Qt.BrushStyle.Dense6Pattern,
         "insulation": QtCore.Qt.BrushStyle.DiagCrossPattern, "stone": QtCore.Qt.BrushStyle.FDiagPattern,
         "earth": QtCore.Qt.BrushStyle.Dense5Pattern}
_KEPT = {}


def _colour(key):
    m = catalog.MATERIALS.get(key)
    r, g, b = m.color if m is not None else (0.70, 0.71, 0.72)
    return QtGui.QColor.fromRgbF(*[min(max(float(c), 0.0), 1.0) for c in (r, g, b)])


def _materials(spec):
    """The keys of the materials a type is drawn with."""
    if isinstance(spec, catalog.OpeningSpec):
        design = catalog.design_of(spec)
        return tuple(sorted({getattr(design, m) for m in set(core_joinery.ROLE_MATERIAL.values())}))
    return tuple(sorted({m for m, _t in spec.layers} | ({spec.material} if spec.material else set())))


def icon(spec):
    """The type's miniature (QIcon), made once for it and its materials' colours."""
    key = (spec, tuple((m, catalog.MATERIALS[m].color, catalog.MATERIALS[m].graphics()) if m in catalog.MATERIALS
                       else (m, None) for m in _materials(spec)))
    found = _KEPT.get(key)
    if found is None:
        found = QtGui.QIcon()
        for size in SIZES:
            found.addPixmap(pixmap(spec, size))
        _KEPT[key] = found
    return found


def pixmap(spec, size):
    """The type's miniature drawn `size` px square, on nothing (transparent)."""
    image = QtGui.QPixmap(size, size)
    image.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(image)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    try:
        if isinstance(spec, catalog.OpeningSpec):
            _opening(p, spec, size)
        elif spec.kind == "wall":
            _wall(p, spec, size)
        elif spec.kind in ("slab", "roof") or (spec.kind == "footing" and spec.strip):
            _stack(p, spec, size)
        elif spec.kind in ("pipe", "duct", "conduit"):
            _hollow(p, spec, size)
        else:
            _section(p, spec, size)
    finally:
        p.end()
    return image


def _pen(size):
    return QtGui.QPen(INK, max(0.8, size / 100))


def _fill(p, rect_or_path, material, size):
    """A shape in a material's colour and, over it, its hatch (brick, concrete, insulation…) — (0.314) its own cut
    patterns when it has them, over its colour."""
    p.setPen(_pen(size))
    p.setBrush(_colour(material))
    draw = p.drawPath if isinstance(rect_or_path, QtGui.QPainterPath) else p.drawRect
    draw(rect_or_path)
    m = catalog.MATERIALS.get(material)
    if m is not None and m.own_cut:
        path = rect_or_path if isinstance(rect_or_path, QtGui.QPainterPath) else QtGui.QPainterPath()
        if path is not rect_or_path:
            path.addRect(rect_or_path)
        pattern_paint.paint_pair(p, path, m.cut_bg, m.cut_fg, max(size / 64.0, 0.4), width=max(0.6, size / 140))
        p.setPen(_pen(size))
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        draw(rect_or_path)
        return
    style = HATCH.get(m.category) if m is not None else None
    if style is not None:
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 70), style))
        draw(rect_or_path)


def _opening(p, spec, size):
    design = catalog.design_of(spec)
    w, h = spec.width, spec.height
    depth = design.depth if design.depth > 0 else 0.2
    pieces = core_joinery.pieces(design, spec.width, spec.height, 0.0, depth, (0.0, depth))
    xs = [x for _r, poly, _a, _b in pieces for x, _z in poly] or [0.0, w]
    zs = [z for _r, poly, _a, _b in pieces for _x, z in poly] or [0.0, h]
    lo, hi, bottom, top = min(min(xs), 0.0), max(max(xs), w), min(min(zs), 0.0), max(max(zs), h)
    room = size * 0.88
    k = room / max(hi - lo, top - bottom)
    x0 = (size - (hi - lo) * k) / 2 - lo * k
    y0 = size - (size - (top - bottom) * k) / 2 + bottom * k

    def to_screen(x, z):
        return QtCore.QPointF(x0 + x * k, y0 - z * k)

    paint_pieces(p, design, spec.width, spec.height, pieces, to_screen, line=max(0.5, size / 160),
                 signs=max(0.6, size / 110) if size >= 48 else 0.0)


def _layers_scale(spec, size):
    return size * 0.84 / max(spec.thickness, SCALE_TO)


def _wall(p, spec, size):
    k = _layers_scale(spec, size)
    x = (size - spec.thickness * k) / 2
    top, height = size * 0.08, size * 0.84
    for material, thickness in spec.layers:              # (outside -> inside: left to right)
        band = max(thickness * k, 1.5)
        _fill(p, QtCore.QRectF(x, top, band, height), material, size)
        x += band


def _stack(p, spec, size):
    layers = spec.layers
    if spec.kind == "footing":                           # a strip footing: its section, as wide as it is
        width, depth = spec.profile[0], spec.thickness
        k = size * 0.84 / max(width, depth)
        rect = QtCore.QRectF((size - width * k) / 2, (size - depth * k) / 2, width * k, depth * k)
        _fill(p, rect, layers[0][0] if layers else "concreto", size)
        return
    k = _layers_scale(spec, size)
    left, width = size * 0.08, size * 0.84
    y = (size + spec.thickness * k) / 2                  # (the first layer at the bottom)
    for material, thickness in layers:
        band = max(thickness * k, 2.0)
        y -= band
        _fill(p, QtCore.QRectF(left, y, width, band), material, size)


def _outline(spec):
    """The section's outline (QPainterPath) in metres, its middle at 0 — up: +y as seen from above (a column) or up
    (a beam)."""
    a, b = (spec.profile or (0.3, 0.3))[:2]
    b = b or a
    path = QtGui.QPainterPath()
    web = spec.web or min(a, b) / 3
    if spec.round:
        path.addEllipse(QtCore.QPointF(0.0, 0.0), a / 2, a / 2)
    elif spec.shape == "L":                              # (its two legs: up the left, along the bottom)
        path.addPolygon(QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in (
            (-a / 2, -b / 2), (a / 2, -b / 2), (a / 2, -b / 2 + web), (-a / 2 + web, -b / 2 + web),
            (-a / 2 + web, b / 2), (-a / 2, b / 2))]))
        path.closeSubpath()
    elif spec.shape == "T":                              # (its flange on top, its web down the middle)
        path.addPolygon(QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in (
            (-a / 2, b / 2), (a / 2, b / 2), (a / 2, b / 2 - web), (web / 2, b / 2 - web), (web / 2, -b / 2),
            (-web / 2, -b / 2), (-web / 2, b / 2 - web), (-a / 2, b / 2 - web))]))
        path.closeSubpath()
    else:
        path.addRect(QtCore.QRectF(-a / 2, -b / 2, a, b))
    return path, a, b


def _section(p, spec, size):
    path, a, b = _outline(spec)
    k = size * 0.80 / max(a, b)
    to = QtGui.QTransform(k, 0.0, 0.0, -k, size / 2, size / 2)          # (metres, y up, to pixels)
    material = spec.material or (spec.layers[0][0] if spec.layers else "concreto")
    _fill(p, to.map(path), material, size)
    if spec.piles and spec.pile in catalog.BY_KEY:       # a pile cap: its piles, dashed, under it
        pile = catalog.BY_KEY[spec.pile]
        r = (pile.profile or (0.3, 0.3))[0] / 2
        places = {1: [(0.0, 0.0)], 2: [(-a / 2 + r * 2, 0.0), (a / 2 - r * 2, 0.0)],
                  3: [(-a / 2 + r * 2, -b / 2 + r * 2), (a / 2 - r * 2, -b / 2 + r * 2), (0.0, b / 2 - r * 2)]}
        spots = places.get(spec.piles, [(sx * (a / 2 - r * 2), sy * (b / 2 - r * 2))
                                        for sx in (-1, 1) for sy in (-1, 1)])
        pen = QtGui.QPen(INK, max(0.8, size / 110), QtCore.Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        for x, y in spots:
            p.drawEllipse(to.map(QtCore.QPointF(x, y)), r * k, r * k)


def _hollow(p, spec, size):
    path, a, b = _outline(spec)
    k = size * 0.80 / max(a, b)
    to = QtGui.QTransform(k, 0.0, 0.0, -k, size / 2, size / 2)
    inner = QtGui.QPainterPath()
    if spec.round:                                       # (its wall: the outer circle less one 72 % as wide)
        inner.addEllipse(QtCore.QPointF(0.0, 0.0), a * 0.36, a * 0.36)
    else:                                                # (a duct's sheet, all round)
        t = min(a, b) * 0.14
        inner.addRect(QtCore.QRectF(-a / 2 + t, -b / 2 + t, a - 2 * t, b - 2 * t))
    # (taken away in pixels: in metres the circles would come out as octagons)
    _fill(p, to.map(path).subtracted(to.map(inner)), spec.material or "pvc", size)


class TypeCombo(QtWidgets.QComboBox):
    """(0.313) A list of types with their miniatures, large, as Revit's Type Selector: on the button the chosen one's
    name (and a small miniature); open, each type's picture and its name."""

    def __init__(self, parent=None):
        super().__init__(parent)
        view = QtWidgets.QListView()
        view.setSpacing(1)
        view.setUniformItemSizes(True)
        self.setView(view)
        self.setItemDelegate(QtWidgets.QStyledItemDelegate(self))      # (the list's icon size, not the button's)
        self.setIconSize(QtCore.QSize(18, 18))
        view.setIconSize(QtCore.QSize(LIST_SIZE, LIST_SIZE))
        self.setMaxVisibleItems(7)
        self.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.setMinimumContentsLength(10)

    def add_type(self, spec, text, data):
        """A type in the list: its miniature (spec None: none), its name, its data."""
        if spec is not None:
            self.addItem(icon(spec), text, data)
        else:
            self.addItem(text, data)

    def showPopup(self):
        self.view().setIconSize(QtCore.QSize(LIST_SIZE, LIST_SIZE))
        self.view().setMinimumWidth(max(self.width(), 300))
        super().showPopup()
