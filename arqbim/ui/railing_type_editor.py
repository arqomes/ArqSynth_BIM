"""The railing type editor (0.260), as Revit's Type Properties for railings: the program's railing types and the
project's own — made (duplicating one), changed and removed when no railing is of it. Each part of the type in its
group: the top rail, the posts and their base plates, what fills it, the bottom rail, a handrail on brackets, the
glass's base channel — its sizes and materials; a sample (2,40 m of it, seen from the front, in its materials'
colours) drawn as it is being changed. Applying saves it in the project (one undo step, done by the window:
on_save) and every railing of it is made again."""

import dataclasses

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..core import railing_types as rail
from ..core.units import format_length, parse_length
from ..i18n import decimal_sep, lang, t
from ..ifc import catalog
from . import theme

MATERIALS = ("aco", "inox", "aco_preto", "aluminio", "madeira", "carvalho", "nogueira", "vidro", "lacado_branco",
             "lacado_preto", "concreto", "pvc")
# the type's fields by part: (field, kind, choices) — kind "len" a length, "choice", "bool", "int", "mat"
GROUPS = (
    ("general", (("height", "len", None),)),
    ("top", (("top", "choice", rail.TOP_SHAPES), ("top_w", "len", None), ("top_h", "len", None),
             ("top_mat", "mat", None))),
    ("posts", (("post", "choice", rail.SHAPES + ("none",)), ("post_w", "len", None), ("post_d", "len", None),
               ("spacing", "len", None), ("plate", "choice", rail.PLATES), ("plate_w", "len", None),
               ("plate_t", "len", None), ("post_mat", "mat", None))),
    ("infill", (("infill", "choice", rail.INFILLS), ("bar", "choice", rail.SHAPES), ("bar_w", "len", None),
                ("bar_d", "len", None), ("gap", "len", None), ("count", "int", None), ("sheet_t", "len", None),
                ("infill_mat", "mat", None))),
    ("bottom", (("bottom", "bool", None), ("bottom_z", "len", None))),
    ("hand", (("hand", "bool", None), ("hand_side", "choice", rail.HAND_SIDES), ("hand_shape", "choice",
                                                                               ("round", "rect")),
              ("hand_w", "len", None), ("hand_z", "len", None), ("hand_off", "len", None), ("hand_mat", "mat", None))),
    ("shoe", (("shoe_w", "len", None), ("shoe_h", "len", None))),
)
SAMPLE = 2.40               # m: the sample drawn


def _len(value):
    return format_length(value, decimal_sep(), 3)


def _material_name(key):
    m = catalog.MATERIALS.get(key)
    return key if m is None else (m.name_pt if lang() == "pt" else m.name_en)


def new_key(taken):
    """A key for a new type of the project: "proprio_1", "proprio_2"… not taken."""
    k = 1
    while "proprio_{}".format(k) in taken:
        k += 1
    return "proprio_{}".format(k)


class RailingPreview(QtWidgets.QWidget):
    """2,40 m of a railing type, seen from the front (its pieces in their materials' colours) — and a hint of its
    depth: what is across it (the posts' plates, a handrail beside it) drawn lighter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(420, 220)
        self.rtype = None

    def show_type(self, rtype):
        self.rtype = rtype
        self.update()

    def paintEvent(self, _event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QtGui.QColor("#f4f5f6"))
        if self.rtype is None or rail.problem(self.rtype):
            p.end()
            return
        parts = rail.parts([(0.0, 0.0, 0.0), (SAMPLE, 0.0, 0.0)], self.rtype)
        top = max(self.rtype.height, self.rtype.hand_z if self.rtype.hand else 0.0) + 0.05
        margin = 16
        k = min((self.width() - 2 * margin) / SAMPLE, (self.height() - 2 * margin) / top)
        ox, oy = (self.width() - SAMPLE * k) / 2, self.height() - margin

        def at(x, z):
            return QtCore.QPointF(ox + x * k, oy - z * k)

        p.setPen(QtGui.QPen(QtGui.QColor("#9aa0a6"), 1))
        p.drawLine(at(-0.2, 0.0), at(SAMPLE + 0.2, 0.0))              # (the floor)
        order = sorted(parts, key=lambda part: 0 if part[0] == "pane" else (1 if part[0] == "plate" else 2))
        for part in order:
            colour = QtGui.QColor.fromRgbF(*catalog.MATERIALS.get(part[-1], catalog.MATERIALS["aco"]).color)
            if part[0] == "pane":
                _k, a, b, z0, z1, _t, mat = part
                if mat == "vidro":
                    colour.setAlphaF(0.45)
                poly = QtGui.QPolygonF([at(a[0], a[2] + z0), at(b[0], b[2] + z0), at(b[0], b[2] + z1),
                                        at(a[0], a[2] + z1)])
                p.setPen(QtGui.QPen(colour.darker(140), 1))
                p.setBrush(colour)
                p.drawPolygon(poly)
                continue
            if part[0] == "plate":
                _k, c, _shape, w, thick, _mat = part
                p.setPen(QtCore.Qt.PenStyle.NoPen)
                p.setBrush(colour)
                p.drawRect(QtCore.QRectF(at(c[0] - w / 2, thick), at(c[0] + w / 2, 0.0)))
                continue
            _k, a, b, shape, w, d, ref, _mat = part
            a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
            dx, dz = b[0] - a[0], b[2] - a[2]
            length = float(np.hypot(dx, dz))
            if length < 1e-9:                                         # (a bar across: its section)
                p.setPen(QtCore.Qt.PenStyle.NoPen)
                p.setBrush(colour)
                p.drawEllipse(at(a[0], a[2]), w * k / 2, w * k / 2)
                continue
            # its thickness seen from the front: across the railing (ref) it shows its depth, along it its width
            seen = w if abs(float(np.asarray(ref, dtype=float)[0])) > 0.5 or shape == "round" else d
            nx, nz = -dz / length * seen / 2, dx / length * seen / 2
            poly = QtGui.QPolygonF([at(a[0] + nx, a[2] + nz), at(b[0] + nx, b[2] + nz), at(b[0] - nx, b[2] - nz),
                                    at(a[0] - nx, a[2] - nz)])
            p.setPen(QtGui.QPen(colour.darker(150), 0.6))
            p.setBrush(colour)
            p.drawPolygon(poly)
        p.end()


class RailingTypeEditor(QtWidgets.QDialog):
    def __init__(self, parent, doc, key=None):
        super().__init__(parent)
        self.setWindowTitle(t("railtype.title"))
        self.doc = doc
        self.on_save = None           # (RailingType, old key or None) -> True if saved
        self.on_delete = None         # (key) -> True if removed
        self.current = None           # the type shown, as it is (in the project or the program)
        self.fresh = False            # a new one (a copy), not in the project yet
        self._filling = False
        outer = QtWidgets.QHBoxLayout(self)
        left = QtWidgets.QVBoxLayout()
        self.list = QtWidgets.QListWidget()
        self.list.setMinimumWidth(240)
        left.addWidget(self.list, 1)
        row = QtWidgets.QHBoxLayout()
        self.duplicate = QtWidgets.QPushButton(t("types.duplicate"))
        self.remove = QtWidgets.QPushButton(t("types.delete"))
        row.addWidget(self.duplicate)
        row.addWidget(self.remove)
        left.addLayout(row)
        outer.addLayout(left)
        right = QtWidgets.QVBoxLayout()
        form = QtWidgets.QFormLayout()
        self.name = QtWidgets.QLineEdit()
        form.addRow(t("railtype.name"), self.name)
        right.addLayout(form)
        self.preview = RailingPreview()
        right.addWidget(self.preview)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QtWidgets.QWidget()
        fields = QtWidgets.QVBoxLayout(inner)
        self.editors = {}
        for group, items in GROUPS:
            box = QtWidgets.QGroupBox(t("railtype.group." + group))
            lay = QtWidgets.QFormLayout(box)
            for field, kind, choices in items:
                lay.addRow(t("railtype." + field), self._editor(field, kind, choices))
            fields.addWidget(box)
        fields.addStretch(1)
        scroll.setWidget(inner)
        scroll.setMinimumWidth(380)
        right.addWidget(scroll, 1)
        self.problem = QtWidgets.QLabel("")
        self.problem.setStyleSheet("color: %s;" % theme.C["fail"])
        right.addWidget(self.problem)
        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.apply = QtWidgets.QPushButton(t("railtype.apply"))
        close = QtWidgets.QPushButton(t("railtype.close"))
        buttons.addWidget(self.apply)
        buttons.addWidget(close)
        right.addLayout(buttons)
        outer.addLayout(right, 1)
        self.list.currentRowChanged.connect(lambda _r: self._show_current())
        self.duplicate.clicked.connect(self.duplicate_current)
        self.remove.clicked.connect(self.remove_current)
        self.apply.clicked.connect(self.save)
        close.clicked.connect(self.reject)
        self.name.textEdited.connect(lambda _t: self._changed())
        self.resize(900, 720)
        self._fill_list(key)

    # ------------------------------------------------------------ the list

    def types(self):
        """{key: RailingType}: the program's (or the project's version of them) and the project's own."""
        out = dict(rail.PRESETS)
        out.update(self.doc.ifc.railing_types())
        return out

    def _fill_list(self, key=None):
        self.list.blockSignals(True)
        self.list.clear()
        own = self.doc.ifc.railing_types()
        for k, rt in self.types().items():
            item = QtWidgets.QListWidgetItem(rt.label(lang()) + ("" if k in rail.PRESETS else "  ★"))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, k)
            if k in own:
                item.setToolTip(t("railtype.in_project"))
            self.list.addItem(item)
        self.list.blockSignals(False)
        keys = [self.list.item(i).data(QtCore.Qt.ItemDataRole.UserRole) for i in range(self.list.count())]
        self.list.setCurrentRow(keys.index(key) if key in keys else 0)
        self._show_current()

    def select(self, key):
        for i in range(self.list.count()):
            if self.list.item(i).data(QtCore.Qt.ItemDataRole.UserRole) == key:
                self.list.setCurrentRow(i)
                return True
        return False

    def _show_current(self):
        item = self.list.currentItem()
        if item is None:
            return
        found = self.types().get(item.data(QtCore.Qt.ItemDataRole.UserRole))
        if found is None:                                 # (a copy not applied yet: as it was left)
            return
        self.fresh = False
        self.current = found
        self._fill(self.current)

    # ------------------------------------------------------------ the fields

    def _editor(self, field, kind, choices):
        if kind == "choice":
            w = QtWidgets.QComboBox()
            for c in choices:
                w.addItem(t("railopt.{}.{}".format(field, c)), c)
            w.currentIndexChanged.connect(lambda _i: self._changed())
        elif kind == "mat":
            w = QtWidgets.QComboBox()
            for m in MATERIALS:
                w.addItem(_material_name(m), m)
            w.currentIndexChanged.connect(lambda _i: self._changed())
        elif kind == "bool":
            w = QtWidgets.QCheckBox()
            w.toggled.connect(lambda _b: self._changed())
        elif kind == "int":
            w = QtWidgets.QSpinBox()
            w.setRange(0, 40)
            w.setSpecialValueText(t("railtype.by_gap"))
            w.valueChanged.connect(lambda _v: self._changed())
        else:
            w = QtWidgets.QLineEdit()
            w.editingFinished.connect(self._changed)
        self.editors[field] = (kind, w)
        return w

    def _fill(self, rt):
        self._filling = True
        self.name.setText(rt.label(lang()))
        for field, (kind, w) in self.editors.items():
            value = getattr(rt, field)
            if kind in ("choice", "mat"):
                i = w.findData(value)
                if i < 0 and kind == "mat":
                    w.addItem(_material_name(value), value)
                    i = w.count() - 1
                w.setCurrentIndex(max(i, 0))
            elif kind == "bool":
                w.setChecked(bool(value))
            elif kind == "int":
                w.setValue(int(value))
            else:
                w.setText(_len(value))
        self._filling = False
        self.remove.setEnabled(self.current is not None and self.current.key not in rail.PRESETS)
        self._changed()

    def edited(self):
        """The type as the fields say (None if a length cannot be read)."""
        if self.current is None:
            return None
        values = {}
        for field, (kind, w) in self.editors.items():
            if kind in ("choice", "mat"):
                values[field] = w.currentData()
            elif kind == "bool":
                values[field] = w.isChecked()
            elif kind == "int":
                values[field] = int(w.value())
            else:
                v = parse_length(w.text())
                if v is None:
                    return None
                values[field] = float(v)
        name = self.name.text().strip() or self.current.label(lang())
        names = {"name_pt": name} if lang() == "pt" else {"name_en": name}
        if self.fresh and lang() == "pt":
            names["name_en"] = name
        return dataclasses.replace(self.current, **names, **values)

    def _changed(self):
        if self._filling:
            return
        rt = self.edited()
        trouble = t("railtype.bad_length") if rt is None else rail.problem(rt)
        if rt is not None and trouble:
            trouble = t("refuse." + trouble)
        self.problem.setText(trouble or "")
        self.apply.setEnabled(not trouble)
        self.preview.show_type(rt)
        kind = rt.infill if rt is not None else None
        for field in ("bar", "bar_w", "bar_d", "gap", "count"):
            self.editors[field][1].setEnabled(kind in ("bars", "rails", "cables", "mesh", "zigzag"))
        self.editors["sheet_t"][1].setEnabled(kind in ("glass", "glass_channel", "panel"))
        for field in ("shoe_w", "shoe_h"):
            self.editors[field][1].setEnabled(kind == "glass_channel")
        hand = rt is not None and rt.hand
        for field in ("hand_side", "hand_shape", "hand_w", "hand_z", "hand_off", "hand_mat"):
            self.editors[field][1].setEnabled(hand)
        self.editors["bottom_z"][1].setEnabled(rt is not None and rt.bottom)

    # ------------------------------------------------------------ the buttons

    def duplicate_current(self):
        """A copy of the type shown, a new one of the project's (saved on Apply)."""
        if self.current is None:
            return
        taken = set(self.types())
        name = t("railtype.copy_of", name=self.current.label(lang()))
        copy = dataclasses.replace(self.current, key=new_key(taken), name_pt=name, name_en=name)
        item = QtWidgets.QListWidgetItem(name + "  ★")
        item.setData(QtCore.Qt.ItemDataRole.UserRole, copy.key)
        self.list.blockSignals(True)
        self.list.addItem(item)
        self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        self.current, self.fresh = copy, True
        self._fill(copy)
        self.remove.setEnabled(False)

    def save(self):
        rt = self.edited()
        if rt is None or rail.problem(rt) or self.on_save is None:
            return False
        old = None if self.fresh else self.current.key
        if not self.on_save(rt, old):
            return False
        self._fill_list(rt.key)
        return True

    def remove_current(self):
        if self.current is None or self.current.key in rail.PRESETS or self.on_delete is None:
            return False
        if not self.on_delete(self.current.key):
            return False
        self._fill_list()
        return True
