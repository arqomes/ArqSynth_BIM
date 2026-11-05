"""(0.289) The door and window generator's window: a door / window type's design (core/joinery) drawn in elevation as
it is changed — the frame and its casings, the bars, each leaf with the sign of how it opens (the lines meeting at
its hinges, a sliding one's arrow) — and changed: a ready-made layout of the library; the cell clicked: how it opens,
what fills it, its width, its row's height; cells split and joined, rows added and taken away; the frame's and
leaves' sizes; the materials. What is wrong is said under it; OK keeps the design (self.design)."""

import dataclasses

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import joinery as core
from ..core.units import format_length, parse_length
from ..i18n import decimal_sep, lang, t
from ..ifc import catalog
from . import theme

ORDER = {"stone": 0, "frame": 1, "panel": 2, "wood": 2, "vent": 2, "glass": 3, "frosted": 3, "leaf": 4, "hardware": 5,
         "screen_frame": 6, "screen": 7, "shutter": 8, "grille": 9, "portada": 10, "louvre": 11, "louvre_in": 11}
# (their alpha, drawn over what is behind them — (0.295) shut portadas too: the leaves behind them still to be seen)
SEE_THROUGH = {"glass": 150, "frosted": 210, "screen": 70, "portada": 120, "louvre": 90}
SIGN = QtGui.QColor("#3b4452")
SELECTED = QtGui.QColor(31, 95, 214, 70)


def _len(value):
    return format_length(value, decimal_sep(), 3)


def _rgb(key):
    m = catalog.MATERIALS.get(key)
    r, g, b = m.color if m is not None else (0.7, 0.71, 0.72)
    return QtGui.QColor(int(r * 255), int(g * 255), int(b * 255))


def _op_name(key):
    o = core.OPERATIONS[key]
    return o.name_pt if lang() == "pt" else o.name_en


def paint_pieces(p, design, width, height, pieces, to_screen, line=1.0, signs=1.3):
    """(0.313) A design's pieces (core.pieces) drawn seen from its outer side (y0) — the farthest first, and of those
    as far the frame, the solid panels, the glass, the leaves' frames… (0.294: as prisms — an arch's pieces too) — in
    their materials' colours, and how each leaf opens (signs: its pen's width; 0: not drawn). to_screen(x, z): a
    QPointF. The generator's elevation and the types' miniatures (ui/type_thumbs)."""
    outline = QtGui.QPen(QtGui.QColor("#2b2f36"), line)
    for role, poly, _ya, _yb in sorted(pieces, key=lambda q: (-round((q[2] + q[3]) / 2, 4), ORDER[q[0]])):
        colour = _rgb(getattr(design, core.ROLE_MATERIAL[role]))
        if role in SEE_THROUGH:
            colour.setAlpha(SEE_THROUGH[role])
        p.setPen(outline)
        p.setBrush(colour)
        p.drawPolygon(QtGui.QPolygonF([to_screen(x, z) for x, z in poly]))
    if signs > 0:
        p.setPen(QtGui.QPen(SIGN, signs))               # how each leaf opens (core: as the drawings show it)
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        for polyline in core.elevation_signs(design, width, height):
            p.drawPolyline([to_screen(x, z) for x, z in polyline])


def operations_for(kind, row):
    """The ways a cell can open: a door's leaves (its bottom row) as doors open, or fixed; any other as windows do."""
    if kind == "door" and row == 0:
        return [k for k in core.OPERATIONS if k == "fixed" or core.door_leaf(k)]
    return [k for k in core.OPERATIONS if core.OPERATIONS[k].door in ("", "FIXEDPANEL", "SWINGING", "SLIDING")
            or kind == "window"]


class Elevation(QtWidgets.QWidget):
    """The design drawn in elevation, seen along +y — from the side its leaves are pushed open from, where IFC's left
    and right are —; a click picks a cell."""
    picked = QtCore.Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.design, self.size, self.selected = None, (1.0, 1.0), (0, 0)
        self.pieces, self.bounds = [], (0.0, 1.0, 1.0)
        self.setMinimumSize(320, 380)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

    def show_design(self, design, width, height, selected):
        self.design, self.size, self.selected = design, (width, height), selected
        depth = design.depth if design.depth > 0 else 0.2
        self.pieces = core.pieces(design, width, height, 0.0, depth, (0.0, depth))
        xs = [x for _r, poly, _a, _b in self.pieces for x, _z in poly] or [0.0, width]
        zs = [z for _r, poly, _a, _b in self.pieces for _x, z in poly] or [height]
        # (what it takes: its casings, (0.295) its portadas turned back beside it)
        self.bounds = (min(min(xs), 0.0), max(max(xs), width), max(max(zs), height))
        self.update()

    def _frame(self):
        """(scale, x of 0, y of the bottom) to draw it, with its casings and portadas, in the middle with room for
        its sizes."""
        lo, hi, top = self.bounds
        room_w, room_h = self.width() - 70, self.height() - 70
        k = min(room_w / (hi - lo), room_h / top)
        x0 = 45 + (room_w - (hi - lo) * k) / 2 - lo * k
        bottom = self.height() - 40 - (room_h - top * k) / 2
        return k, x0, bottom

    def _to_screen(self, x, z):
        k, x0, bottom = self._frame()
        return QtCore.QPointF(x0 + x * k, bottom - z * k)

    def paintEvent(self, _event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QtGui.QColor("white"))
        if self.design is None:
            return
        d = self.design
        width, height = self.size
        paint_pieces(p, d, width, height, self.pieces, self._to_screen)
        lights, _bars = core.layout(d, width, height)
        for lt in lights:
            if (lt.row, lt.index) == self.selected:                 # (0.296: a leaf under an arch to its curve)
                p.setPen(QtGui.QPen(QtGui.QColor("#1f5fd6"), 2.5))
                p.setBrush(SELECTED)
                p.drawPolygon(QtGui.QPolygonF([self._to_screen(x, z)
                                               for x, z in core.light_outline(d, width, height, lt)]))
        p.setPen(QtGui.QPen(QtGui.QColor("#2b2f36"), 1.0))
        a, b = self._to_screen(0.0, 0.0), self._to_screen(width, 0.0)
        p.drawText(QtCore.QRectF(a.x(), a.y() + 6, b.x() - a.x(), 18), QtCore.Qt.AlignmentFlag.AlignHCenter,
                   _len(width))
        top = self._to_screen(0.0, height)
        p.save()
        p.translate(self._to_screen(self.bounds[0], 0.0).x() - 26, (a.y() + top.y()) / 2)   # (left of it all)
        p.rotate(-90)
        p.drawText(QtCore.QRectF(-60, 0, 120, 18), QtCore.Qt.AlignmentFlag.AlignHCenter, _len(height))
        p.restore()

    def mousePressEvent(self, event):
        if self.design is None:
            return
        pos = event.position()
        for lt in core.layout(self.design, *self.size)[0]:
            ring = QtGui.QPolygonF([self._to_screen(x, z) for x, z in core.light_outline(self.design, *self.size, lt)])
            if ring.containsPoint(pos, QtCore.Qt.FillRule.OddEvenFill):
                self.picked.emit(lt.row, lt.index)
                return


class JoineryDialog(QtWidgets.QDialog):
    """The generator on a door / window type (an OpeningSpec): OK keeps the design changed in self.design."""

    def __init__(self, parent, spec):
        super().__init__(parent)
        self.setWindowTitle(t("joinery.title"))
        self.spec = spec
        self.kind = spec.kind
        self.size = (spec.width, spec.height)
        self.design = catalog.design_of(spec)
        self.selected = (0, 0)
        outer = QtWidgets.QVBoxLayout(self)
        body = QtWidgets.QHBoxLayout()
        outer.addLayout(body, 1)
        self.elevation = Elevation()
        body.addWidget(self.elevation, 1)
        scroll = QtWidgets.QScrollArea()                # (its fields scroll on a small screen)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        panel = QtWidgets.QWidget()
        right = QtWidgets.QVBoxLayout(panel)
        scroll.setWidget(panel)
        scroll.setMinimumWidth(400)
        body.addWidget(scroll)
        name = spec.name_pt if lang() == "pt" else spec.name_en
        head = QtWidgets.QLabel("<b>{}</b><br>{} × {}".format(name, _len(spec.width), _len(spec.height)))
        right.addWidget(head)
        form = QtWidgets.QFormLayout()
        self.model = QtWidgets.QComboBox()
        self.model.addItem(t("joinery.own"), None)
        for key, pt, en, _rows in core.MODELS[self.kind]:
            self.model.addItem(pt if lang() == "pt" else en, key)
        form.addRow(t("joinery.model"), self.model)
        self.arch = QtWidgets.QComboBox()                       # (0.294) its head: square or arched
        for value, label in (("", "joinery.arch_none"), ("round", "joinery.arch_round"),
                             ("segmental", "joinery.arch_segmental"), ("pointed", "joinery.arch_pointed")):
            self.arch.addItem(t(label), value)
        form.addRow(t("joinery.arch"), self.arch)
        self.arch_rise = QtWidgets.QLineEdit()
        form.addRow(t("joinery.arch_rise"), self.arch_rise)
        right.addLayout(form)
        # the cell clicked
        self.cell_box = QtWidgets.QGroupBox()
        cf = QtWidgets.QFormLayout(self.cell_box)
        self.operation = QtWidgets.QComboBox()
        cf.addRow(t("joinery.operation"), self.operation)
        self.fill = QtWidgets.QComboBox()
        for key, (pt, en) in core.FILLS.items():
            self.fill.addItem(pt if lang() == "pt" else en, key)
        cf.addRow(t("joinery.fill"), self.fill)
        self.cell_width = QtWidgets.QLineEdit()
        self.cell_width.setPlaceholderText(t("joinery.auto"))
        cf.addRow(t("joinery.cell_width"), self.cell_width)
        self.row_height = QtWidgets.QLineEdit()
        self.row_height.setPlaceholderText(t("joinery.auto"))
        cf.addRow(t("joinery.row_height"), self.row_height)
        grid = QtWidgets.QGridLayout()
        self.split = QtWidgets.QPushButton(t("joinery.split"))
        self.join = QtWidgets.QPushButton(t("joinery.join"))
        self.add_row = QtWidgets.QPushButton(t("joinery.add_row"))
        self.remove_row = QtWidgets.QPushButton(t("joinery.remove_row"))
        for k, b in enumerate((self.split, self.join, self.add_row, self.remove_row)):
            grid.addWidget(b, k // 2, k % 2)
        cf.addRow(grid)
        right.addWidget(self.cell_box)
        # the frame's and leaves' sizes, the materials
        sizes = QtWidgets.QGroupBox(t("joinery.profiles"))
        sf = QtWidgets.QFormLayout(sizes)
        self.sizes = {}
        fields = [("frame", "joinery.frame"), ("depth", "joinery.depth"), ("sash", "joinery.sash"),
                  ("sash_depth", "joinery.sash_depth"), ("mullion", "joinery.mullion"), ("glass", "joinery.glass")]
        if self.kind == "door":
            fields.append(("casing", "joinery.casing"))
        # (0.290) a door's soleira / a window's peitoril: its thickness (none: blank) and how far it stands out
        fields += [("stone", "joinery.threshold" if self.kind == "door" else "joinery.sill"),
                   ("stone_out", "joinery.stone_out"),
                   ("shutter", "joinery.shutter")]                    # (0.291) an estore: its box's height
        for attr, label in fields:
            edit = QtWidgets.QLineEdit()
            sf.addRow(t(label), edit)
            self.sizes[attr] = edit
        if self.kind == "door":
            self.sizes["depth"].setPlaceholderText(t("joinery.wall_depth"))
        self.sizes["stone"].setPlaceholderText(t("joinery.none"))
        self.sizes["shutter"].setPlaceholderText(t("joinery.none"))
        self.shutter_closed = QtWidgets.QSpinBox()                      # (0.291) how far it is let down
        self.shutter_closed.setRange(0, 100)
        self.shutter_closed.setSuffix(" %")
        sf.addRow(t("joinery.shutter_closed"), self.shutter_closed)
        self.screen = QtWidgets.QCheckBox(t("joinery.screen"))
        self.grille = QtWidgets.QCheckBox(t("joinery.grille"))
        sf.addRow(self.screen)
        sf.addRow(self.grille)
        self.louvres = QtWidgets.QComboBox()                            # (0.295) portadas de lâminas
        for value in ("", "left", "right", "pair"):
            self.louvres.addItem(t("joinery.louvres_" + (value or "none")), value)
        sf.addRow(t("joinery.louvres"), self.louvres)
        self.louvres_open = QtWidgets.QCheckBox(t("joinery.louvres_open"))
        sf.addRow(self.louvres_open)
        self.casing_sides = QtWidgets.QComboBox()
        for value in ("both", "open", "push"):
            self.casing_sides.addItem(t("joinery.casing_" + value), value)
        if self.kind == "door":
            sf.addRow(t("joinery.casing_sides"), self.casing_sides)
        self.drip = QtWidgets.QCheckBox(t("joinery.drip"))
        if self.kind == "window":
            sf.addRow(self.drip)
        self.hardware = QtWidgets.QCheckBox(t("joinery.hardware"))
        sf.addRow(self.hardware)
        right.addWidget(sizes)
        materials = QtWidgets.QGroupBox(t("joinery.materials"))
        mf = QtWidgets.QFormLayout(materials)
        self.materials = {}
        for attr, label in (("frame_material", "joinery.frame_material"), ("panel_material", "joinery.panel_material"),
                            ("glass_material", "joinery.glass_material"), ("stone_material", "joinery.stone_material"),
                            ("hardware_material", "joinery.hardware_material"),
                            ("shutter_material", "joinery.shutter_material"),
                            ("screen_material", "joinery.screen_material"),
                            ("grille_material", "joinery.grille_material"),
                            ("louvres_material", "joinery.louvres_material")):
            combo = QtWidgets.QComboBox()
            for m in catalog.MATERIALS.values():
                combo.addItem(m.name_pt if lang() == "pt" else m.name_en, m.key)
            mf.addRow(t(label), combo)
            self.materials[attr] = combo
        right.addWidget(materials)
        self.ifc = QtWidgets.QLabel()
        self.ifc.setStyleSheet("QLabel { color: %s; }" % theme.C["ctx_text"])
        right.addWidget(self.ifc)
        self.warning = QtWidgets.QLabel()
        self.warning.setWordWrap(True)
        self.warning.setStyleSheet("QLabel { color: %s; }" % theme.C["fail"])
        right.addWidget(self.warning)
        right.addStretch(1)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.ok = buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        outer.addWidget(buttons)
        screen = QtWidgets.QApplication.primaryScreen()
        room = screen.availableGeometry().height() - 80 if screen is not None else 760
        self.resize(940, max(520, min(860, room)))

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.elevation.picked.connect(self.pick)
        self.model.activated.connect(self._model_chosen)
        self.operation.activated.connect(lambda _i: self._cell(operation=self.operation.currentData()))
        self.fill.activated.connect(lambda _i: self._cell(fill=self.fill.currentData()))
        self.cell_width.editingFinished.connect(self._cell_width)
        self.row_height.editingFinished.connect(self._row_height)
        self.split.clicked.connect(lambda: self._change(core.split(self.design, *self.selected)))
        self.join.clicked.connect(lambda: self._change(core.join(self.design, *self.selected)))
        self.add_row.clicked.connect(self._add_row)
        self.remove_row.clicked.connect(self._remove_row)
        for attr, edit in self.sizes.items():
            edit.editingFinished.connect(lambda a=attr: self._size(a))
        for attr, combo in self.materials.items():
            combo.activated.connect(lambda _i, a=attr: self._change(dataclasses.replace(
                self.design, **{a: self.materials[a].currentData()})))
        self.casing_sides.activated.connect(lambda _i: self._change(dataclasses.replace(
            self.design, casing_sides=self.casing_sides.currentData())))
        self.arch.activated.connect(lambda _i: self._arch())
        self.arch_rise.editingFinished.connect(self._arch)
        self.drip.toggled.connect(lambda on: self._change(dataclasses.replace(self.design, drip=bool(on))))
        self.hardware.toggled.connect(lambda on: self._change(dataclasses.replace(self.design, hardware=bool(on))))
        self.screen.toggled.connect(lambda on: self._change(dataclasses.replace(self.design, screen=bool(on))))
        self.grille.toggled.connect(lambda on: self._change(dataclasses.replace(self.design, grille=bool(on))))
        self.louvres.activated.connect(lambda _i: self._change(dataclasses.replace(
            self.design, louvres=self.louvres.currentData())))
        self.louvres_open.toggled.connect(lambda on: self._change(dataclasses.replace(self.design,
                                                                                      louvres_open=bool(on))))
        self.shutter_closed.editingFinished.connect(lambda: self._change(dataclasses.replace(
            self.design, shutter_closed=self.shutter_closed.value() / 100.0)))
        self._show()

    # ------------------------------------------------------------ showing

    def _show(self):
        d, (i, j) = self.design, self.selected
        i = min(i, len(d.rows) - 1)
        j = min(j, len(d.rows[i].cells) - 1)
        self.selected = (i, j)
        self.elevation.show_design(d, *self.size, self.selected)
        key = core.matching_model(d)
        self.model.setCurrentIndex(max(0, self.model.findData(key)) if key else 0)
        cell = d.rows[i].cells[j]
        self.cell_box.setTitle(t("joinery.cell", row=i + 1, cell=j + 1))
        self.operation.clear()
        for k in operations_for(self.kind, i):
            self.operation.addItem(_op_name(k), k)
        if self.operation.findData(cell.operation) < 0:
            self.operation.addItem(_op_name(cell.operation), cell.operation)
        self.operation.setCurrentIndex(self.operation.findData(cell.operation))
        self.fill.setCurrentIndex(self.fill.findData(cell.fill))
        self.cell_width.setText(_len(cell.width) if cell.width > 0 else "")
        self.row_height.setText(_len(d.rows[i].height) if d.rows[i].height > 0 else "")
        self.join.setEnabled(j + 1 < len(d.rows[i].cells))
        self.remove_row.setEnabled(len(d.rows) > 1)
        for attr, edit in self.sizes.items():
            value = getattr(d, attr)
            blank = value <= 0 and (attr in ("stone", "shutter") or (attr == "depth" and self.kind == "door"))
            edit.setText("" if blank else _len(value))
        blocker = QtCore.QSignalBlocker(self.shutter_closed)
        self.shutter_closed.setValue(int(round(d.shutter_closed * 100)))
        self.shutter_closed.setEnabled(d.shutter > 0)
        del blocker
        for attr, combo in self.materials.items():
            combo.setCurrentIndex(max(0, combo.findData(getattr(d, attr))))
        self.casing_sides.setCurrentIndex(max(0, self.casing_sides.findData(d.casing_sides)))
        self.arch.setCurrentIndex(max(0, self.arch.findData(d.arch)))
        self.arch_rise.setEnabled(d.arch == "segmental")
        self.arch_rise.setText(_len(core.arch_rise(d, self.size[0])) if d.arch == "segmental" else "")
        for box, on in ((self.drip, d.drip), (self.hardware, d.hardware), (self.screen, d.screen),
                        (self.grille, d.grille), (self.louvres_open, d.louvres_open)):
            blocker = QtCore.QSignalBlocker(box)
            box.setChecked(on)
            del blocker
        self.louvres.setCurrentIndex(max(0, self.louvres.findData(d.louvres)))
        self.louvres_open.setEnabled(bool(d.louvres))
        found = core.door_operation(d) if self.kind == "door" else core.window_partitioning(d)
        self.ifc.setText(t("joinery.ifc", name=found[0] + (" ({})".format(found[1]) if found[1] else "")))
        wrong = core.problems(d, *self.size)
        self.warning.setText("\n".join(t(k, **v) for k, v in wrong))
        self.ok.setEnabled(not wrong)

    def pick(self, row, index):
        self.selected = (row, index)
        self._show()

    # ------------------------------------------------------------ changes

    def _change(self, design):
        self.design = design
        self._show()

    def _cell(self, **changes):
        self._change(core.set_cell(self.design, *self.selected, **changes))

    def _length(self, edit, zero_ok=True):
        text = edit.text().strip()
        if not text:
            return 0.0 if zero_ok else None
        value = parse_length(text)
        return value if value is not None and value >= 0 else None

    def _cell_width(self):
        value = self._length(self.cell_width)
        if value is None:
            self._show()
            return
        self._cell(width=value)

    def _row_height(self):
        value = self._length(self.row_height)
        if value is None:
            self._show()
            return
        self._change(core.set_row(self.design, self.selected[0], value))

    def _size(self, attr):
        optional = ("depth", "casing", "stone", "stone_out", "shutter")  # (none: blank or 0)
        value = self._length(self.sizes[attr], zero_ok=attr in optional)
        if value is None or (value <= 0 and attr not in optional):
            self._show()
            return
        self._change(dataclasses.replace(self.design, **{attr: value}))

    def _arch(self):
        """(0.294) The arch chosen (a segmental one's rise as typed): its row over the others — (0.296) its leaves kept
        where they can open under it, else fixed."""
        arch = self.arch.currentData()
        rise = self._length(self.arch_rise) if arch == "segmental" else 0.0
        if rise is None:
            self._show()
            return
        if (arch, rise) == (self.design.arch, self.design.arch_rise if arch == "segmental" else 0.0):
            return
        self._change(core.with_arch(self.design, arch, self.size[0], rise or 0.0))

    def _add_row(self):
        i = self.selected[0]
        self.design = core.add_row(self.design, i)
        self.selected = (i + 1, 0)
        self._show()

    def _remove_row(self):
        self._change(core.remove_row(self.design, self.selected[0]))

    def _model_chosen(self, _index):
        key = self.model.currentData()
        if key is None:
            return
        self.selected = (0, 0)
        self._change(dataclasses.replace(self.design, rows=core.model(self.kind, key)))
