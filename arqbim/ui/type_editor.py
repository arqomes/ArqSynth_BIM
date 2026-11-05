"""The type editor (0.87), as Revit's Type Properties: the project's types of walls, slabs, roofs (0.278), columns,
beams, footings, pipes and ducts — made, duplicated, changed (their layers and thicknesses, or their section and
material; their name) and removed when unused. Applying a change changes every element of that type (one undo
step, done by the window: on_save).

The catalogue's types are listed too: changing one makes it the project's (kept in its IFC)."""

import dataclasses

from PySide6 import QtCore, QtWidgets

from ..core import joinery as core_joinery
from ..core.units import format_length, parse_length
from ..i18n import decimal_sep, has, lang, t
from ..ifc import catalog
from ..model import project_types
from . import type_thumbs
from .joinery_dialog import Elevation
from . import theme

KIND_LABELS = {"wall": "types.walls", "slab": "types.slabs", "roof": "types.roofs", "column": "types.columns",
               "beam": "types.beams",
               "footing": "types.footings", "pile": "types.piles", "pipe": "types.pipes", "duct": "types.ducts",
               "door": "types.doors", "window": "types.windows", "conduit": "types.conduits"}
KINDS = catalog.KINDS + ("door", "window")
OPENING_KINDS = ("door", "window")


def _spec(key):
    return catalog.BY_KEY.get(key) or catalog.OPENING_BY_KEY.get(key)


def _name(spec):
    return spec.name_pt if lang() == "pt" else spec.name_en


def _material_name(key):
    m = catalog.MATERIALS.get(key)
    return key if m is None else (m.name_pt if lang() == "pt" else m.name_en)


def _len(value, decimals=3):
    return format_length(value, decimal_sep(), decimals)


class TypeEditor(QtWidgets.QDialog):
    def __init__(self, parent, doc, kind=None):
        super().__init__(parent)
        self.setWindowTitle(t("types.title"))
        self.doc = doc
        self.on_save = None           # (spec, old spec or None) -> the saved type's key, or None
        self.on_delete = None         # (spec) -> True if removed
        self.on_materials = None      # the materials window (0.89)
        self.current = None           # the type shown (as it is in the project)
        outer = QtWidgets.QVBoxLayout(self)
        body = QtWidgets.QHBoxLayout()
        outer.addLayout(body, 1)
        # the left side: the kind, its types, duplicate / remove
        left = QtWidgets.QVBoxLayout()
        self.kind = QtWidgets.QComboBox()
        for k in KINDS:
            self.kind.addItem(t(KIND_LABELS[k]), k)
        left.addWidget(self.kind)
        self.list = QtWidgets.QListWidget()
        self.list.setMinimumWidth(260)
        self.list.setIconSize(QtCore.QSize(40, 40))
        left.addWidget(self.list, 1)
        row = QtWidgets.QHBoxLayout()
        self.duplicate = QtWidgets.QPushButton(t("types.duplicate"))
        self.remove = QtWidgets.QPushButton(t("types.delete"))
        row.addWidget(self.duplicate)
        row.addWidget(self.remove)
        left.addLayout(row)
        body.addLayout(left)
        # the right side: the type's name and its layers / section
        right = QtWidgets.QVBoxLayout()
        form = QtWidgets.QFormLayout()
        self.name = QtWidgets.QLineEdit()
        form.addRow(t("types.name"), self.name)
        right.addLayout(form)
        self.layers_box = QtWidgets.QGroupBox(t("types.layers"))
        lb = QtWidgets.QVBoxLayout(self.layers_box)
        self.layers = QtWidgets.QTableWidget(0, 3)
        self.layers.setHorizontalHeaderLabels([t("types.material"), t("types.thickness"), t("types.function")])
        self.layers.horizontalHeaderItem(2).setToolTip(t("types.function_tip"))      # (0.334: each layer's priority)
        self.layers.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.layers.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.layers.verticalHeader().setVisible(False)
        lb.addWidget(self.layers)
        buttons = QtWidgets.QHBoxLayout()
        self.add_layer = QtWidgets.QPushButton(t("types.add_layer"))
        self.del_layer = QtWidgets.QPushButton(t("types.del_layer"))
        self.up = QtWidgets.QPushButton("↑")
        self.down = QtWidgets.QPushButton("↓")
        for b in (self.add_layer, self.del_layer, self.up, self.down):
            buttons.addWidget(b)
        buttons.addStretch(1)
        self.total = QtWidgets.QLabel()
        buttons.addWidget(self.total)
        lb.addLayout(buttons)
        self.layers_note = QtWidgets.QLabel()
        self.layers_note.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        lb.addWidget(self.layers_note)
        right.addWidget(self.layers_box)
        # (0.346) a wall type's own masonry for Eurocode 6 (off: the project's, in Actions and materials)
        from ..core import ec6
        self.masonry_box = QtWidgets.QGroupBox(t("types.masonry"))
        mf = QtWidgets.QFormLayout(self.masonry_box)
        self.masonry_own = QtWidgets.QCheckBox(t("types.masonry_own"))
        self.masonry_own.setToolTip(t("types.masonry_tip"))
        mf.addRow(self.masonry_own)
        self.masonry_unit = QtWidgets.QComboBox()
        for k in ec6.UNITS:
            self.masonry_unit.addItem(t("actions.masonry_unit." + k), k)
        self.masonry_group = QtWidgets.QComboBox()
        for k in ec6.GROUPS:
            self.masonry_group.addItem(k, k)
        self.masonry_fb = QtWidgets.QDoubleSpinBox()
        self.masonry_fb.setRange(1.0, 80.0)
        self.masonry_fb.setSingleStep(0.5)
        self.masonry_fb.setDecimals(1)
        self.masonry_fb.setSuffix(" N/mm²")
        self.masonry_mortar = QtWidgets.QComboBox()
        for k in ec6.MORTARS:
            self.masonry_mortar.addItem(k, k)
        for label, widget in (("actions.masonry_unit", self.masonry_unit), ("actions.masonry_group", self.masonry_group),
                              ("actions.masonry_fb", self.masonry_fb), ("actions.masonry_mortar", self.masonry_mortar)):
            mf.addRow(t(label), widget)
        self.masonry_own.toggled.connect(self._masonry_enabled)
        right.addWidget(self.masonry_box)
        self.section_box = QtWidgets.QGroupBox(t("types.section"))
        sf = QtWidgets.QFormLayout(self.section_box)
        self.shape = QtWidgets.QComboBox()                  # (0.97: a column's / beam's section)
        for value, label in ((None, "types.shape.rect"), ("circle", "types.shape.circle"), ("L", "types.shape.L"),
                             ("T", "types.shape.T")):
            self.shape.addItem(t(label), value)
        self.shape_label = QtWidgets.QLabel(t("types.shape"))
        sf.addRow(self.shape_label, self.shape)
        self.width = QtWidgets.QLineEdit()
        self.depth = QtWidgets.QLineEdit()
        self.web = QtWidgets.QLineEdit()
        self.material = QtWidgets.QComboBox()
        self.width_label, self.depth_label = QtWidgets.QLabel(), QtWidgets.QLabel()
        self.web_label = QtWidgets.QLabel(t("types.web"))
        sf.addRow(self.width_label, self.width)
        sf.addRow(self.depth_label, self.depth)
        sf.addRow(self.web_label, self.web)
        self.sill = QtWidgets.QLineEdit()                   # (a window: its sill when placed, 0.88)
        self.sill_label = QtWidgets.QLabel(t("types.sill"))
        sf.addRow(self.sill_label, self.sill)
        self.transom = QtWidgets.QLineEdit()                # (a door: its fanlight over the leaf, 0.110)
        self.transom_label = QtWidgets.QLabel(t("types.transom"))
        sf.addRow(self.transom_label, self.transom)
        self.design_preview = Elevation()                   # (0.289) a door's / window's design, and the generator
        self.design_preview.setMinimumSize(170, 200)
        self.design_preview.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        sf.addRow(self.design_preview)
        self.design_button = QtWidgets.QPushButton(t("joinery.button"))
        self.design_button.setToolTip(t("joinery.button_tip"))
        sf.addRow(self.design_button)
        self.pending_design = None        # the design the generator gave, not applied yet
        self.material_label = QtWidgets.QLabel(t("types.material"))
        sf.addRow(self.material_label, self.material)
        right.addWidget(self.section_box)
        # (0.271) the type's IFC data (its standard set: what every element of it has unless it says otherwise)
        self.data_box = QtWidgets.QGroupBox(t("types.ifc_data"))
        self.data_box.setToolTip(t("types.ifc_data_tip"))
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        inner = QtWidgets.QWidget()
        self.data_form = QtWidgets.QFormLayout(inner)
        scroll.setWidget(inner)
        scroll.setMinimumHeight(150)
        QtWidgets.QVBoxLayout(self.data_box).addWidget(scroll)
        right.addWidget(self.data_box)
        self.data_editors = {}            # property -> (kind, widget, value shown)
        self.on_type_data = None          # (spec, property, value) -> True if written
        self.used = QtWidgets.QLabel()
        self.used.setWordWrap(True)
        self.used.setStyleSheet("QLabel { color: %s; }" % theme.C["ctx_text"])
        right.addWidget(self.used)
        right.addStretch(1)
        body.addLayout(right, 1)
        bottom = QtWidgets.QHBoxLayout()
        self.materials = QtWidgets.QPushButton(t("act.materials"))       # (0.89: the materials window)
        bottom.addWidget(self.materials)
        bottom.addStretch(1)
        self.apply = QtWidgets.QPushButton(t("types.apply"))
        self.apply.setDefault(True)
        close = QtWidgets.QPushButton(t("types.close"))
        bottom.addWidget(self.apply)
        bottom.addWidget(close)
        outer.addLayout(bottom)
        self.resize(780, 680)                               # (0.271: room for the type's IFC data too)

        self.kind.currentIndexChanged.connect(lambda _i: self._fill_list())
        self.list.currentRowChanged.connect(lambda _r: self._show(self._chosen()))
        self.duplicate.clicked.connect(self.duplicate_type)
        self.remove.clicked.connect(self.delete_type)
        self.add_layer.clicked.connect(lambda: self._add_layer_row(self._default_material(), 0.02, select=True))
        self.del_layer.clicked.connect(self._remove_layer_row)
        self.up.clicked.connect(lambda: self._move_layer(-1))
        self.down.clicked.connect(lambda: self._move_layer(1))
        self.apply.clicked.connect(self.apply_changes)
        self.materials.clicked.connect(self._open_materials)
        self.shape.currentIndexChanged.connect(lambda _i: self._show_shape())
        self.design_button.clicked.connect(self._open_generator)
        for edit in (self.width, self.depth, self.transom):
            edit.editingFinished.connect(self._show_design)
        close.clicked.connect(self.reject)
        if kind in KINDS:
            self.kind.setCurrentIndex(KINDS.index(kind))
        self._fill_list()

    # ------------------------------------------------------------ the list

    def _kind(self):
        return self.kind.currentData()

    def _specs(self):
        every = catalog.openings() if self._kind() in OPENING_KINDS else catalog.types()
        return [s for s in every if s.kind == self._kind()]

    def _fill_list(self, select=None):
        blocker = QtCore.QSignalBlocker(self.list)
        self.list.clear()
        for spec in self._specs():
            n = len(project_types.instances(self.doc.ifc, spec))
            text = _name(spec) + ("   ({})".format(t("types.used", n=n)) if n else "")
            item = QtWidgets.QListWidgetItem(type_thumbs.icon(spec), text)       # (0.313: with its miniature)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, spec.key)
            self.list.addItem(item)
        del blocker
        keys = [self.list.item(i).data(QtCore.Qt.ItemDataRole.UserRole) for i in range(self.list.count())]
        self.list.setCurrentRow(keys.index(select) if select in keys else 0)
        self._show(self._chosen())

    def _chosen(self):
        item = self.list.currentItem()
        return _spec(item.data(QtCore.Qt.ItemDataRole.UserRole)) if item is not None else None

    def select(self, key):
        """Show the type of this key."""
        spec = _spec(key)
        if spec.kind != self._kind():
            self.kind.setCurrentIndex(KINDS.index(spec.kind))
        self._fill_list(select=key)

    # ------------------------------------------------------------ the form

    def _show_data(self, spec):
        """(0.271) The type's standard IFC set: every property, empty or set — a yes / no / «—» list, the
        enumeration's values, a text, a number or a length."""
        from ..model import bim
        while self.data_form.rowCount():
            self.data_form.removeRow(0)
        self.data_editors = {}
        data = bim.type_data(self.doc, spec) if spec is not None else None
        self.data_box.setVisible(data is not None)
        if data is None:
            return
        pset_name, rows = data
        self.data_box.setTitle(t("types.ifc_data") + " — " + pset_name)
        for prop, kind, choices, value in rows:
            label = QtWidgets.QLabel(t("ifcprop." + prop) if has("ifcprop." + prop) else prop)
            label.setToolTip("{}.{}".format(pset_name, prop))
            if kind in ("bool", "choice"):
                widget = QtWidgets.QComboBox()
                widget.addItem("—", None)
                options = ((t("rules.yes"), True), (t("rules.no"), False)) if kind == "bool" else \
                    tuple((str(c), c) for c in choices or ())
                for text, data_value in options:
                    widget.addItem(text, data_value)
                widget.setCurrentIndex(max(widget.findData(value), 0) if value is not None else 0)
            else:
                shown = "" if value is None else _len(value) if kind == "length" else \
                    str(value).replace(".", decimal_sep()) if isinstance(value, float) else str(value)
                widget = QtWidgets.QLineEdit(shown)
                widget.setPlaceholderText("—")
            self.data_form.addRow(label, widget)
            self.data_editors[prop] = (kind, widget, value)

    def data_edits(self):
        """{property: value} of the type's IFC data changed in the form (None: cleared) — or a text: a value that
        is not a number / a length."""
        out = {}
        for prop, (kind, widget, old) in self.data_editors.items():
            if isinstance(widget, QtWidgets.QComboBox):
                value = widget.currentData()
            else:
                text = widget.text().strip()
                if not text:
                    value = None
                elif kind == "length":
                    value = parse_length(text)
                    if value is None:
                        return t("types.err_data", prop=prop)
                    value /= self.doc.ifc.unit_scale
                    old = old / self.doc.ifc.unit_scale if isinstance(old, (int, float)) else old
                elif kind in ("number", "integer"):
                    try:
                        value = float(text.replace(",", "."))
                    except ValueError:
                        return t("types.err_data", prop=prop)
                    value = int(round(value)) if kind == "integer" else value
                else:
                    value = text
            if value != old and not (isinstance(value, float) and isinstance(old, float) and abs(value - old) < 1e-9):
                out[prop] = value
        return out

    def _show(self, spec):
        self.current = spec
        self.pending_design = None
        if spec is None:
            return
        self._show_data(spec)
        self.name.setText(_name(spec))
        self._show_masonry(spec)
        if spec.kind in OPENING_KINDS:
            self._show_opening(spec)
            return
        self.sill.setVisible(False)
        self.sill_label.setVisible(False)
        self.transom.setVisible(False)
        self.transom_label.setVisible(False)
        self.design_preview.setVisible(False)
        self.design_button.setVisible(False)
        self.section_box.setTitle(t("types.section"))
        layered = spec.kind in catalog.LAYERED
        self.layers_box.setVisible(layered)
        footing = spec.kind == "footing"
        self.section_box.setVisible(not layered or footing)
        if layered:
            self.layers.setRowCount(0)
            for k, (key, thickness) in enumerate(spec.layers):
                self._add_layer_row(key, thickness, catalog.layer_function(spec, k))
            self.layers_note.setText(t("types.layers_" + ("wall" if spec.kind == "wall" else "slab")))
            self._update_total()
        if not layered or footing:
            width, depth = spec.profile
            self.depth_label.setText(t("types.length" if footing else "types.height"))
            self.width.setText(_len(width))
            self.depth.setText(_len(depth))
            self.web.setText(_len(spec.web or 0.15))
            shaped = spec.kind in ("column", "beam")
            self.shape.setVisible(shaped)
            self.shape_label.setVisible(shaped)
            blocker = QtCore.QSignalBlocker(self.shape)
            self.shape.setCurrentIndex(max(0, self.shape.findData(spec.shape)))
            del blocker
            self._show_shape()
            self.material.setVisible(not footing)
            self.material_label.setVisible(not footing)
            if not footing:
                self._fill_materials(self.material, spec.material)
        self._show_use(spec)

    def _show_masonry(self, spec):
        """(0.346) A wall type's masonry: its own (ticked), else the project's shown (greyed)."""
        wall = spec.kind == "wall"
        self.masonry_box.setVisible(wall)
        if not wall:
            return
        own = getattr(spec, "masonry", None)
        if own is None:
            s = self.doc.ifc.structural_settings()
            own_values = (s.masonry_unit, str(s.masonry_group), float(s.masonry_fb), s.masonry_mortar)
        else:
            own_values = own
        unit, group, fb, mortar = own_values
        self.masonry_unit.setCurrentIndex(max(0, self.masonry_unit.findData(unit)))
        self.masonry_group.setCurrentIndex(max(0, self.masonry_group.findData(str(group))))
        self.masonry_fb.setValue(float(fb))
        self.masonry_mortar.setCurrentIndex(max(0, self.masonry_mortar.findData(mortar)))
        blocker = QtCore.QSignalBlocker(self.masonry_own)
        self.masonry_own.setChecked(own is not None)
        del blocker
        self._masonry_enabled(own is not None)

    def _masonry_enabled(self, on):
        for w in (self.masonry_unit, self.masonry_group, self.masonry_fb, self.masonry_mortar):
            w.setEnabled(bool(on))

    def _masonry(self):
        """(0.346) The wall type's own masonry as the form has it, or None (the project's)."""
        if not self.masonry_own.isChecked():
            return None
        return (self.masonry_unit.currentData(), self.masonry_group.currentData(), float(self.masonry_fb.value()),
                self.masonry_mortar.currentData())

    def _shape(self):
        spec = self.current
        return self.shape.currentData() if spec is not None and spec.kind in ("column", "beam") else None

    def _show_shape(self):
        """The section's fields for its shape: a circle its diameter only; an L or a T their legs' thickness."""
        spec = self.current
        if spec is None or spec.kind in OPENING_KINDS:
            return
        shape = self._shape()
        round_ = spec.kind in ("pipe", "pile") or shape == "circle"
        self.width_label.setText(t("types.diameter" if round_ else "types.width"))
        self.depth.setVisible(not round_ and not spec.strip)
        self.depth_label.setVisible(not round_ and not spec.strip)
        self.web.setVisible(shape in ("L", "T"))
        self.web_label.setVisible(shape in ("L", "T"))

    def _show_use(self, spec):
        n = len(project_types.instances(self.doc.ifc, spec))
        self.used.setText(t("types.apply_note", n=n) if n else t("types.unused"))
        in_project = project_types.find_type(self.doc.ifc, spec) is not None
        self.remove.setEnabled(in_project and n == 0)

    def _show_opening(self, spec):
        """A door or window type (0.88): its width and height, a window's sill when placed."""
        self.layers_box.setVisible(False)
        self.section_box.setVisible(True)
        self.section_box.setTitle(t("types.size"))
        for w in (self.shape, self.shape_label, self.web, self.web_label):
            w.setVisible(False)
        self.width_label.setText(t("types.width"))
        self.depth_label.setText(t("types.height"))
        self.width.setText(_len(spec.width))
        self.depth.setText(_len(spec.height))
        self.depth.setVisible(True)
        self.depth_label.setVisible(True)
        window = spec.kind == "window"
        self.sill.setVisible(window)
        self.sill_label.setVisible(window)
        self.sill.setText(_len(spec.sill))
        self.transom.setVisible(not window)
        self.transom_label.setVisible(not window)
        self.transom.setText(_len(spec.transom or 0.0))
        self.material.setVisible(False)
        self.material_label.setVisible(False)
        self.design_preview.setVisible(True)
        self.design_button.setVisible(True)
        self._show_design()
        self._show_use(spec)

    def _show_design(self):
        """(0.289) The design of the door / window type as the form has it now, small."""
        spec = self.draft() if self.current is not None and self.current.kind in OPENING_KINDS else None
        if spec is None or isinstance(spec, str):
            return
        self.design_preview.show_design(catalog.design_of(spec), spec.width, spec.height, (-1, -1))

    def _open_generator(self):
        """(0.289) The door and window editor — (0.307) the Caixilho Studio — on the type as the form has it: its
        design, size, sill and name kept until Apply."""
        from ..core import caixilho as cx
        from .caixilho_studio import CaixilhoStudio
        spec = self.draft()
        if isinstance(spec, str):
            QtWidgets.QMessageBox.warning(self, t("types.title"), spec)
            return
        item = cx.from_design(catalog.design_of(spec), spec.width, spec.height, spec.sill, _name(spec), spec.key)
        dialog = CaixilhoStudio(self, [item], insert=False, single=True)
        self._studio = dialog                               # (tests)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            op = dialog.op
            self.pending_design = cx.to_design(op)
            self.name.setText(op.name)
            self.width.setText(_len(op.W / 1000.0))
            self.depth.setText(_len(op.H / 1000.0))
            if spec.kind == "window":
                self.sill.setText(_len(op.sill / 1000.0))
            else:
                self.transom.setText(_len(core_joinery.transom_of(self.pending_design, op.H / 1000.0)))
            self._show_design()
        self._studio = None

    def _fill_materials(self, combo, key):
        combo.clear()
        for m in catalog.MATERIALS.values():
            combo.addItem(m.name_pt if lang() == "pt" else m.name_en, m.key)
        combo.setCurrentIndex(max(0, combo.findData(key)))

    def _default_material(self):
        return "reboco" if self._kind() == "wall" else "concreto"

    def _add_layer_row(self, key, thickness, function=None, select=False):
        row = self.layers.rowCount()
        self.layers.insertRow(row)
        combo = QtWidgets.QComboBox()
        self._fill_materials(combo, key)
        self.layers.setCellWidget(row, 0, combo)
        field = QtWidgets.QLineEdit(_len(thickness))
        field.editingFinished.connect(self._update_total)
        self.layers.setCellWidget(row, 1, field)
        role = QtWidgets.QComboBox()                        # (0.334) its function: its priority where elements meet
        role.addItem(t("types.function.auto"), None)
        for name in catalog.LAYER_FUNCTIONS:
            role.addItem(t("types.function." + name), name)
        role.setCurrentIndex(max(0, role.findData(function)))
        role.setToolTip(t("types.function_tip"))
        self.layers.setCellWidget(row, 2, role)
        if select:
            self.layers.setCurrentCell(row, 0)
        self._update_total()

    def _layer_functions(self):
        """(0.334) Each layer's function as chosen (None: automatic), or () when none is."""
        found = tuple(self.layers.cellWidget(r, 2).currentData() for r in range(self.layers.rowCount()))
        return found if any(found) else ()

    def _remove_layer_row(self):
        row = self.layers.currentRow()
        if row >= 0 and self.layers.rowCount() > 1:
            self.layers.removeRow(row)
            self._update_total()

    def _move_layer(self, step):
        row = self.layers.currentRow()
        rows = self._layer_rows()
        other = row + step
        if rows is None or row < 0 or not 0 <= other < len(rows):
            return
        functions = list(self._layer_functions()) or [None] * len(rows)
        rows[row], rows[other] = rows[other], rows[row]
        functions[row], functions[other] = functions[other], functions[row]
        self.layers.setRowCount(0)
        for (key, thickness), function in zip(rows, functions):
            self._add_layer_row(key, thickness, function)
        self.layers.setCurrentCell(other, 0)

    def _layer_rows(self):
        """[(material key, thickness)] as typed, or None if a thickness is not a length."""
        rows = []
        for r in range(self.layers.rowCount()):
            value = parse_length(self.layers.cellWidget(r, 1).text())
            if value is None:
                return None
            rows.append((self.layers.cellWidget(r, 0).currentData(), value))
        return rows

    def _update_total(self):
        rows = self._layer_rows()
        self.total.setText(t("types.total", t=_len(sum(v for _k, v in rows))) if rows else "")

    def draft(self):
        """The type as the form has it now (a TypeSpec, with the shown type's key), or an error text."""
        spec = self.current
        name = self.name.text().strip()
        if not name:
            return t("types.err_name")
        others = {_name(s) for s in self._specs() if s.key != spec.key}
        if name in others:
            return t("types.err_same_name", name=name)
        if spec.kind in OPENING_KINDS:
            width, height = parse_length(self.width.text()), parse_length(self.depth.text())
            sill = parse_length(self.sill.text()) if spec.kind == "window" else 0.0
            if width is None or height is None or sill is None or width <= 0.1 or height <= 0.1 or sill < 0:
                return t("types.err_size")
            transom = 0.0
            if spec.kind == "door":                         # (0.110) a fanlight: within the height, above 1,80
                text = self.transom.text().strip()
                transom = parse_length(text) if text else 0.0
                if transom is None or transom < 0 or (transom > 0 and height - transom < 1.80):
                    return t("types.err_transom")
            # (0.288: its design kept — its sizes of 0 share the new width and height; a door's fanlight as typed)
            new = dataclasses.replace(spec, name_pt=name, name_en=name, width=width, height=height, sill=sill,
                                      transom=transom)
            if self.pending_design is not None:              # (0.289: as the generator left it)
                new = dataclasses.replace(catalog.with_design(new, self.pending_design), transom=transom)
            return new
        layers, profile, material, functions = (), None, None, ()
        if spec.kind in catalog.LAYERED:
            layers = self._layer_rows()
            if not layers or any(v <= 0 for _k, v in layers):
                return t("types.err_thickness")
            layers = tuple(layers)
            functions = self._layer_functions()                     # (0.334)
        shape, web = spec.shape, spec.web
        if spec.kind not in catalog.LAYERED or spec.kind == "footing":
            shape = self._shape() if spec.kind in ("column", "beam") else spec.shape
            round_ = spec.kind in ("pipe", "pile") or shape == "circle"
            width = parse_length(self.width.text())
            depth = width if round_ else 0.0 if spec.strip else parse_length(self.depth.text())
            if width is None or depth is None or width <= 0 or (depth <= 0 and not spec.strip):
                return t("types.err_size")
            web = None
            if shape in ("L", "T"):
                web = parse_length(self.web.text())
                if web is None or web <= 0 or web >= min(width, depth):
                    return t("types.err_web")
            profile = (width, depth)
            if spec.kind != "footing":
                material = self.material.currentData()
        # (what the form does not show — a pile cap's piles, an IFC PredefinedType — stays as it was)
        return dataclasses.replace(spec, name_pt=name, name_en=name, layers=layers, profile=profile,
                                   material=material, shape=shape, web=web, functions=functions,
                                   masonry=self._masonry() if spec.kind == "wall" else spec.masonry)    # (0.346)

    # ------------------------------------------------------------ actions

    def _open_materials(self):
        """The materials window; back here, the lists of materials as they are now (the type's changes not
        applied yet are kept)."""
        if self.on_materials is None:
            return
        rows = self._layer_rows() if self.layers_box.isVisible() else None
        functions = list(self._layer_functions()) if rows else []
        material = self.material.currentData()
        self.on_materials()
        if rows:
            functions += [None] * (len(rows) - len(functions))
            self.layers.setRowCount(0)
            for (key, thickness), function in zip(rows, functions):
                self._add_layer_row(key, thickness, function)
        if self.material.isVisible():
            self._fill_materials(self.material, material)

    def apply_changes(self):
        """Apply: the type as the form has it, in the project (its elements follow)."""
        new = self.draft()
        edits = self.data_edits()
        if isinstance(new, str) or isinstance(edits, str):
            QtWidgets.QMessageBox.warning(self, t("types.title"), new if isinstance(new, str) else edits)
            return None
        old = self.current
        if _name(new) == _name(old) and dataclasses.replace(new, name_pt=old.name_pt, name_en=old.name_en) == old:
            # (0.271: its IFC data only changed — the type as it is)
            key = old.key
        else:
            if project_types.find_type(self.doc.ifc, old) is None:
                old = None                                # (a catalogue type the project has not used yet)
            key = self.on_save(new, old) if self.on_save is not None else None
        if key is not None:
            saved = _spec(key) or new
            for prop, value in edits.items():
                if self.on_type_data is not None:
                    self.on_type_data(saved, prop, value)
            self._fill_list(select=key)
        return key

    def duplicate_type(self):
        """A copy of the type shown, with a name of its own, added to the project."""
        new = self.draft()
        if isinstance(new, str):
            new = self.current
        names = {_name(s) for s in self._specs()}
        base, n = _name(new), 2
        while "{} ({})".format(base, n) in names:
            n += 1
        name = "{} ({})".format(base, n)
        copy = dataclasses.replace(new, key="t:new", name_pt=name, name_en=name)      # (0.288: a door's design too)
        key = self.on_save(copy, None) if self.on_save is not None else None
        if key is not None:
            self._fill_list(select=key)
        return key

    def delete_type(self):
        if self.current is not None and self.on_delete is not None and self.on_delete(self.current):
            self._fill_list()
