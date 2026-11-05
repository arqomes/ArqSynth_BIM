"""(0.398) Anotar ▸ Tipos de cota… — the dimension types' editor, as Revit's Type Properties of a dimension (the owner,
2026-11-05: «um motor de edição da aparência da cota»): on the left the project's types — its own style (the one every
dimension without a type is drawn with) and the named ones — duplicated, renamed, deleted, or started from one of the
usual looks; in the middle every property of the type chosen, by groups (Graphics, Extension lines, Text, Units and
values, Openings and equal ones); on the right a sample on paper — a chain, its overall, a door's width with its
height, a vertical one — drawn as the plans, sheets, PDF, SVG and DXF will draw it (core/dim_layout), again at each
change. OK keeps them all: one undo step."""

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..core import dim_layout
from ..i18n import decimal_sep, t
from ..model import dimensions as dims_model
from . import theme
from .material_editor import ColourButton

PREVIEW_SCALE = 50                 # the sample drawn at 1:50…
PREVIEW_PEN = 0.18                 # …with the dimensions' usual pen (mm)

# (key, kind, extra): kind "choice" (its values), "mm" (spin: low, high, step), "factor", "int", "bool", "str",
# "colour", "font", "rounding"
GROUPS = (
    ("graphics", (("mark", "choice", dim_layout.MARKS), ("mark_size", "mm", (0.5, 10.0, 0.1)),
                  ("mark_pen", "mm", (0.0, 2.0, 0.05)), ("pen", "mm", (0.0, 2.0, 0.05)), ("colour", "colour", None),
                  ("line_over", "mm", (0.0, 10.0, 0.25)))),
    ("witness", (("witness", "choice", ("gap", "fixed")), ("witness_gap", "mm", (0.0, 10.0, 0.25)),
                 ("witness_over", "mm", (0.0, 10.0, 0.25)), ("witness_length", "mm", (0.5, 50.0, 0.5)),
                 ("witness_pen", "mm", (0.0, 2.0, 0.05)))),
    ("text", (("font", "font", None), ("text", "mm", (1.0, 10.0, 0.1)), ("width_factor", "factor", (0.3, 3.0, 0.05)),
              ("bold", "bool", None), ("italic", "bool", None), ("underline", "bool", None),
              ("text_offset", "mm", (0.0, 10.0, 0.1)), ("text_place", "choice", ("above", "centre")),
              ("reading", "choice", ("aligned", "horizontal")), ("background", "choice", ("transparent", "opaque")),
              ("text_colour", "colour", None), ("fit", "choice", ("auto", "keep")))),
    ("units", (("unit", "choice", dim_layout.UNITS), ("decimals", "int", (0, 4)), ("rounding", "rounding", None),
               ("unit_symbol", "bool", None), ("sup_mm", "bool", None), ("prefix", "str", None),
               ("suffix", "str", None))),
    ("openings", (("opening_height", "bool", None), ("eq_text", "str", None))),
)


class DimPreview(QtWidgets.QWidget):
    """A dimension type drawn on paper as it will print: a chain along a wall (with a piece too short for its value and
    a door's width with its height), its overall further out, a vertical one beside it."""

    def __init__(self):
        super().__init__()
        self.style = dim_layout.clean({})
        self.setMinimumSize(340, 280)

    def show_style(self, style):
        self.style = dim_layout.clean(style)
        self.update()

    def sample(self):
        """(the Layout, the wall's outline) in metres of the sample's frame."""
        s, dec = self.style, decimal_sep()
        xs = [0.0, 1.2, 1.35, 2.175, 4.0]                  # (0,15 a jamb's return; 0,825 a door, 2,10 high)
        y, wall = -0.10, 0.20
        pieces = []
        for k, (a, b) in enumerate(zip(xs, xs[1:])):
            below = dim_layout.label(2.10, dict(s, prefix="", suffix="", unit_symbol=False), dec).plain \
                if k == 2 and s["opening_height"] else ""
            pieces.append(dim_layout.Piece(np.array((a, y)), np.array((b, y)), np.array((a, -0.8)), np.array((b, -0.8)),
                                           dim_layout.label(b - a, s, dec, below=below), k))
        layout = dim_layout.string(pieces, s, PREVIEW_SCALE / 1000.0, PREVIEW_PEN)
        overall = dim_layout.Piece(np.array((0.0, y)), np.array((4.0, y)), np.array((0.0, -1.35)),
                                   np.array((4.0, -1.35)), dim_layout.label(4.0, s, dec), 9)
        layout.extend(dim_layout.string([overall], s, PREVIEW_SCALE / 1000.0, PREVIEW_PEN))
        side = dim_layout.Piece(np.array((4.0, y + wall)), np.array((4.0, 2.6)), np.array((4.75, y + wall)),
                                np.array((4.75, 2.6)), dim_layout.label(2.6 - y - wall, s, dec), 10)
        layout.extend(dim_layout.string([side], s, PREVIEW_SCALE / 1000.0, PREVIEW_PEN))
        return layout

    def paintEvent(self, _event):
        from . import pdf
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QtGui.QColor("#ffffff"))               # (on paper, in both themes)
        lo, hi = np.array((-0.6, -1.9)), np.array((5.6, 2.8))
        k = min(self.width() / (hi[0] - lo[0]), self.height() / (hi[1] - lo[1]))     # (px per metre)
        mid = (lo + hi) / 2
        cx, cy = self.width() / 2, self.height() / 2

        def to_page(q):
            q = np.asarray(q, dtype=float)
            return np.stack((cx + (q[..., 0] - mid[0]) * k, cy - (q[..., 1] - mid[1]) * k), axis=-1)

        # the walls measured: a wall along the chain (cut by the door) and one up the side
        grey = QtGui.QColor("#d9d9d9")
        p.setPen(QtGui.QPen(QtGui.QColor("#555555"), 1.0))
        p.setBrush(grey)
        for x0, x1 in ((0.0, 1.35), (2.175, 4.0)):
            corners = to_page(np.array(((x0, -0.1), (x1, -0.1), (x1, 0.1), (x0, 0.1))))
            p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*c) for c in corners]))
        corners = to_page(np.array(((3.8, 0.1), (4.0, 0.1), (4.0, 2.6), (3.8, 2.6))))
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*c) for c in corners]))
        dpmm = k * PREVIEW_SCALE / 1000.0                  # (px per mm of paper)
        pdf.paint_layout(p, self.sample(), to_page, dpmm)
        p.setPen(QtGui.QColor("#666666"))
        font = p.font()
        font.setPixelSize(11)
        p.setFont(font)
        p.drawText(QtCore.QRectF(6, self.height() - 20, self.width() - 12, 16),
                   QtCore.Qt.AlignmentFlag.AlignRight, "1:{}".format(PREVIEW_SCALE))
        p.end()


class DimTypesDialog(QtWidgets.QDialog):
    """The project's dimension types: its style (None) and the named ones, each a clean dict."""

    def __init__(self, parent, style):
        super().__init__(parent)
        self.setWindowTitle(t("dimstyle.title"))
        current = dims_model.clean_style(style)
        self.work = {None: {k: v for k, v in current.items() if k != "types"}}
        self.work.update({name: dict(s) for name, s in (current.get("types") or {}).items()})
        self._loading = False
        self.fields = {}

        outer = QtWidgets.QHBoxLayout(self)
        # the types
        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel(t("dimtype.list")))
        self.which = QtWidgets.QListWidget()
        self.which.setMinimumWidth(170)
        left.addWidget(self.which, 1)
        self.duplicate_button = QtWidgets.QPushButton(t("dimtype.duplicate"))
        self.rename_button = QtWidgets.QPushButton(t("dimtype.rename"))
        self.delete_button = QtWidgets.QPushButton(t("dimtype.delete"))
        for b in (self.duplicate_button, self.rename_button, self.delete_button):
            left.addWidget(b)
        left.addSpacing(8)
        left.addWidget(QtWidgets.QLabel(t("dimtype.preset")))
        self.preset = QtWidgets.QComboBox()
        self.preset.addItem(t("dimtype.preset.choose"), None)
        for key in dim_layout.PRESETS:
            self.preset.addItem(t("dimtype.preset." + key), key)
        left.addWidget(self.preset)
        outer.addLayout(left)
        # the properties, by groups
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(380)
        inside = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(inside)
        for group, items in GROUPS:
            box = QtWidgets.QGroupBox(t("dimstyle.g." + group))
            form = QtWidgets.QFormLayout(box)
            form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            for key, kind, extra in items:
                widget = self._field(key, kind, extra)
                self.fields[key] = widget
                label = QtWidgets.QLabel(t("dimstyle." + key))
                label.setWordWrap(True)
                form.addRow(label, widget)
            column.addWidget(box)
        column.addStretch(1)
        scroll.setWidget(inside)
        outer.addWidget(scroll, 1)
        # the sample, the example, the buttons
        right = QtWidgets.QVBoxLayout()
        self.preview = DimPreview()
        right.addWidget(self.preview, 1)
        self.example = QtWidgets.QLabel()
        self.example.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        self.example.setWordWrap(True)
        right.addWidget(self.example)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        right.addWidget(buttons)
        outer.addLayout(right, 1)

        self._fill_list()
        self.which.currentRowChanged.connect(lambda _r: self.load())
        self.duplicate_button.clicked.connect(lambda: self.duplicate())
        self.rename_button.clicked.connect(lambda: self.rename())
        self.delete_button.clicked.connect(lambda: self.delete())
        self.preset.activated.connect(lambda _i: self.apply_preset(self.preset.currentData()))
        self.which.setCurrentRow(0)
        self.load()
        self.resize(1080, 640)

    # ------------------------------------------------------------ the fields

    def _field(self, key, kind, extra):
        if kind == "choice":
            w = QtWidgets.QComboBox()
            for value in extra:
                w.addItem(t("dimstyle.{}.{}".format(key, value)), value)
            w.currentIndexChanged.connect(self._changed)
        elif kind in ("mm", "factor"):
            w = QtWidgets.QDoubleSpinBox()
            low, high, step = extra
            w.setRange(low, high)
            w.setSingleStep(step)
            w.setDecimals(2)
            if kind == "mm":
                w.setSuffix(" mm")
            if key in ("mark_pen", "pen", "witness_pen"):
                w.setSpecialValueText(t("dimstyle.as_line" if key != "pen" else "dimstyle.as_project"))
            w.valueChanged.connect(self._changed)
        elif kind == "int":
            w = QtWidgets.QSpinBox()
            w.setRange(*extra)
            w.valueChanged.connect(self._changed)
        elif kind == "bool":
            w = QtWidgets.QCheckBox()
            w.toggled.connect(self._changed)
        elif kind == "str":
            w = QtWidgets.QLineEdit()
            w.setMaxLength(40)
            w.textChanged.connect(self._changed)
        elif kind == "colour":
            w = QtWidgets.QWidget()
            row = QtWidgets.QHBoxLayout(w)
            row.setContentsMargins(0, 0, 0, 0)
            button = ColourButton(t("dimstyle." + key))
            row.addWidget(button)
            if key == "text_colour":
                same = QtWidgets.QCheckBox(t("dimstyle.as_line"))
                row.addWidget(same)
                same.toggled.connect(lambda on, b=button: (b.setEnabled(not on), self._changed()))
                w.same = same
            row.addStretch(1)
            w.button = button
            button.changed.connect(self._changed)
        elif kind == "font":
            w = QtWidgets.QComboBox()
            w.setEditable(True)
            for name in dim_layout.FONTS:
                w.addItem(name or t("dimstyle.font.program"), name)
            w.currentIndexChanged.connect(self._changed)
            w.editTextChanged.connect(self._changed)
        else:                                               # rounding
            w = QtWidgets.QComboBox()
            for r in dim_layout.ROUNDINGS:
                w.addItem(t("dimstyle.rounding.none") if r == 0 else
                          "{} mm".format(("%g" % r).replace(".", decimal_sep())), r)
            w.currentIndexChanged.connect(self._changed)
        w.setObjectName("dimstyle_" + key)
        w.setMinimumWidth(170)
        w.kind = kind
        return w

    def _read(self, key):
        w = self.fields[key]
        if w.kind in ("choice", "rounding"):
            return w.currentData()
        if w.kind == "font":
            text = w.currentText().strip()
            return "" if text in ("", t("dimstyle.font.program")) else text
        if w.kind in ("mm", "factor"):
            return float(w.value())
        if w.kind == "int":
            return int(w.value())
        if w.kind == "bool":
            return w.isChecked()
        if w.kind == "str":
            return w.text()
        if key == "text_colour" and w.same.isChecked():
            return ""
        return w.button.colour

    def _write(self, key, value):
        w = self.fields[key]
        if w.kind in ("choice", "rounding"):
            w.setCurrentIndex(max(0, w.findData(value)))
        elif w.kind == "font":
            k = w.findData(value)
            if k >= 0:
                w.setCurrentIndex(k)
            else:
                w.setEditText(value)
        elif w.kind in ("mm", "factor", "int"):
            w.setValue(value)
        elif w.kind == "bool":
            w.setChecked(bool(value))
        elif w.kind == "str":
            w.setText(str(value))
        else:
            if key == "text_colour":
                w.same.setChecked(not value)
                w.button.setEnabled(bool(value))
            w.button.set_colour(value or self.work.get(self.current(), {}).get("colour", "#000000"))

    # ------------------------------------------------------------ the types

    def _fill_list(self, select=None):
        blocker = QtCore.QSignalBlocker(self.which)
        self.which.clear()
        names = [None] + sorted((k for k in self.work if k is not None), key=str.lower)
        for name in names:
            item = QtWidgets.QListWidgetItem(t("dimtype.project") if name is None else name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, name)
            self.which.addItem(item)
        del blocker
        self.which.setCurrentRow(names.index(select) if select in names else 0)

    def current(self):
        item = self.which.currentItem()
        return item.data(QtCore.Qt.ItemDataRole.UserRole) if item is not None else None

    def select_type(self, name):
        """(tests) The type `name` chosen in the list (None: the project's style)."""
        for k in range(self.which.count()):
            if self.which.item(k).data(QtCore.Qt.ItemDataRole.UserRole) == name:
                self.which.setCurrentRow(k)
                return True
        return False

    def load(self):
        """The fields show the type chosen."""
        self._loading = True
        style = self.work.get(self.current(), self.work[None])
        for key in self.fields:
            self._write(key, style[key])
        name = self.current()
        self.rename_button.setEnabled(name is not None)
        self.delete_button.setEnabled(name is not None)
        self._loading = False
        self._show()

    def _changed(self, *_args):
        if self._loading:
            return
        name = self.current()
        style = dict(self.work.get(name, self.work[None]))
        for key in self.fields:
            style[key] = self._read(key)
        if style.get("unit") != self.work.get(name, {}).get("unit"):
            style["decimals"] = 2 if style["unit"] == "m" else 0      # (a new unit: its usual decimals)
            self._loading = True
            self._write("decimals", style["decimals"])
            self._loading = False
        self.work[name] = dim_layout.clean(style)
        self._show()

    def set_value(self, key, value):
        """(tests) A property of the type chosen set as if typed in its field."""
        self._write(key, value)
        self._changed()

    def _show(self):
        style = self.work.get(self.current(), self.work[None])
        self.preview.show_style(style)
        self.example.setText(t("dimstyle.example", v=dim_layout.label(2.475, style, decimal_sep()).plain))
        for key in ("witness_gap",):
            self.fields[key].setEnabled(style["witness"] == "gap")
        self.fields["witness_length"].setEnabled(style["witness"] == "fixed")

    def _name(self, title, start):
        name, ok = QtWidgets.QInputDialog.getText(self, title, t("dimtype.name"), text=start)
        name = (name or "").strip()
        if not ok or not name:
            return None
        if name in self.work:
            QtWidgets.QMessageBox.information(self, title, t("dimtype.exists", n=name))
            return None
        return name

    def duplicate(self, name=None):
        """A new type as the one chosen, named (asked when not given); chosen in the list. Its name, or None."""
        source = self.current()
        if name is None:
            base = t("dimtype.project") if source is None else source
            name = self._name(t("dimtype.duplicate"), t("dimtype.copy_of", n=base))
        if not name or name in self.work:
            return None
        self.work[name] = dict(self.work.get(source, self.work[None]))
        self._fill_list(name)
        self.load()
        return name

    def rename(self, name=None):
        old = self.current()
        if old is None:
            return None
        if name is None:
            name = self._name(t("dimtype.rename"), old)
        if not name or name in self.work:
            return None
        self.work[name] = self.work.pop(old)
        self.renamed = getattr(self, "renamed", {})
        self.renamed[old] = name
        self._fill_list(name)
        self.load()
        return name

    def delete(self):
        name = self.current()
        if name is None:
            return
        self.work.pop(name, None)
        self._fill_list(None)
        self.load()

    def apply_preset(self, key):
        """One of the usual looks given to the type chosen (its other properties as they were)."""
        if key not in dim_layout.PRESETS:
            return
        name = self.current()
        self.work[name] = dim_layout.clean(dict(self.work.get(name, self.work[None]), **dim_layout.PRESETS[key]))
        self.load()
        self.preset.setCurrentIndex(0)

    def style(self):
        """The project's dimension style as edited: its own properties and its types."""
        return dims_model.clean_style(dict(self.work[None], types={k: s for k, s in self.work.items() if k is not None}))
