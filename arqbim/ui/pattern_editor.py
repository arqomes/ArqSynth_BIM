"""(0.318) Manage ▸ Fill patterns…: the patterns materials and the project's graphic style are drawn with, as Revit's
Fill Patterns — the program's (fixed: duplicated to be changed) and the project's, made, named, duplicated, changed
and deleted. Each measured on paper (drafting: the same at any scale) or on the building (model: tiles, bricks…);
simple — parallel or crossed lines, an angle and a spacing — or its own families of lines (an angle, where they start,
how far the next one is along and across, their dashes). A sample of it, large. Saved in the project's IFC
(ifc/pattern_defs.py) by the window: on_save(pattern, old key) -> its key; on_delete(key) -> True if deleted."""

import uuid
from dataclasses import replace

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import patterns as core_patterns
from ..i18n import decimal_sep, t
from . import pattern_paint
from . import theme

SHAPES = ("lines", "cross", "custom")
COLUMNS = ("angle", "x", "y", "shift", "step", "dashes")
PREVIEW = (300, 170)


def _num(text):
    return float(str(text).strip().replace(",", ".")) if str(text).strip() else 0.0


def _txt(value):
    return "{:g}".format(float(value)).replace(".", decimal_sep())


class PatternEditor(QtWidgets.QDialog):
    def __init__(self, parent, select=None):
        super().__init__(parent)
        self.setWindowTitle(t("patt.title"))
        self.on_save = None
        self.on_delete = None
        self.current = None
        self._loading = False
        outer = QtWidgets.QVBoxLayout(self)
        body = QtWidgets.QHBoxLayout()
        outer.addLayout(body, 1)
        left = QtWidgets.QVBoxLayout()
        self.list = QtWidgets.QListWidget()
        self.list.setIconSize(QtCore.QSize(40, 18))
        self.list.setMinimumWidth(240)
        self.list.currentRowChanged.connect(lambda _r: self._show(self._chosen()))
        left.addWidget(self.list, 1)
        row = QtWidgets.QHBoxLayout()
        self.new = QtWidgets.QPushButton(t("patt.new"))
        self.duplicate = QtWidgets.QPushButton(t("types.duplicate"))
        self.remove = QtWidgets.QPushButton(t("types.delete"))
        for b in (self.new, self.duplicate, self.remove):
            row.addWidget(b)
        left.addLayout(row)
        body.addLayout(left)

        right = QtWidgets.QVBoxLayout()
        form = self.form = QtWidgets.QFormLayout()
        self.name = QtWidgets.QLineEdit()
        form.addRow(t("types.name"), self.name)
        self.kind = QtWidgets.QComboBox()
        self.kind.addItem(t("patt.kind.drafting"), False)
        self.kind.addItem(t("patt.kind.model"), True)
        form.addRow(t("patt.kind"), self.kind)
        self.shape = QtWidgets.QComboBox()
        for s in SHAPES:
            self.shape.addItem(t("patt.shape." + s), s)
        form.addRow(t("patt.shape"), self.shape)
        self.angle = QtWidgets.QDoubleSpinBox()
        self.angle.setRange(-180.0, 180.0)
        self.angle.setDecimals(1)
        self.angle.setSuffix("°")
        form.addRow(t("patt.angle"), self.angle)
        self.spacing = QtWidgets.QDoubleSpinBox()
        self.spacing.setRange(0.01, 5000.0)
        self.spacing.setDecimals(2)
        form.addRow(t("patt.spacing"), self.spacing)
        right.addLayout(form)
        self.table = QtWidgets.QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([t("patt.col." + c) for c in COLUMNS])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(120)
        right.addWidget(self.table)
        rows = QtWidgets.QHBoxLayout()
        self.add_row = QtWidgets.QPushButton(t("patt.add_row"))
        self.del_row = QtWidgets.QPushButton(t("patt.del_row"))
        rows.addWidget(self.add_row)
        rows.addWidget(self.del_row)
        rows.addStretch(1)
        right.addLayout(rows)
        self.table_hint = QtWidgets.QLabel(t("patt.table_hint"))
        self.table_hint.setWordWrap(True)
        self.table_hint.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        right.addWidget(self.table_hint)
        self.preview = QtWidgets.QLabel()
        self.preview.setFixedSize(*PREVIEW)
        right.addWidget(self.preview)
        self.locked = QtWidgets.QLabel(t("patt.builtin_note"))
        self.locked.setWordWrap(True)
        self.locked.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        right.addWidget(self.locked)
        right.addStretch(1)
        body.addLayout(right, 1)
        bottom = QtWidgets.QHBoxLayout()
        bottom.addStretch(1)
        self.apply = QtWidgets.QPushButton(t("types.apply"))
        self.apply.setDefault(True)
        close = QtWidgets.QPushButton(t("types.close"))
        bottom.addWidget(self.apply)
        bottom.addWidget(close)
        outer.addLayout(bottom)
        self.resize(820, 600)

        for signal in (self.kind.currentIndexChanged, self.shape.currentIndexChanged, self.angle.valueChanged,
                       self.spacing.valueChanged, self.table.itemChanged):
            signal.connect(lambda *_a: self._changed())
        self.add_row.clicked.connect(lambda: self._add_row((0.0, 0.0, 0.0, 0.0, 1.0, ())))
        self.del_row.clicked.connect(self._remove_row)
        self.new.clicked.connect(self.new_pattern)
        self.duplicate.clicked.connect(self.duplicate_pattern)
        self.remove.clicked.connect(self.delete_pattern)
        self.apply.clicked.connect(self.apply_changes)
        close.clicked.connect(self.reject)
        self._fill_list(select)

    # ------------------------------------------------------------ the list

    def _keys(self):
        program = [k for k in core_patterns.DRAFTING + core_patterns.MODEL if k != core_patterns.SOLID]
        return program + [p.key for p in core_patterns.project_patterns()]

    def _fill_list(self, select=None):
        blocker = QtCore.QSignalBlocker(self.list)
        self.list.clear()
        for key in self._keys():
            item = QtWidgets.QListWidgetItem(pattern_paint.icon(key), pattern_paint.name(key))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, key)
            if core_patterns.get(key).builtin:
                item.setForeground(theme.colour("note"))
            self.list.addItem(item)
        del blocker
        keys = self._keys()
        self.list.setCurrentRow(keys.index(select) if select in keys else 0)
        self._show(self._chosen())

    def _chosen(self):
        item = self.list.currentItem()
        return core_patterns.get(item.data(QtCore.Qt.ItemDataRole.UserRole)) if item is not None else None

    def select(self, key):
        self._fill_list(key)

    # ------------------------------------------------------------ the form

    def _show(self, pattern):
        self.current = pattern
        if pattern is None:
            return
        self._loading = True
        self.name.setText(pattern_paint.name(pattern.key))
        self.kind.setCurrentIndex(1 if pattern.model else 0)
        shape, angle, spacing = core_patterns.shape_of(pattern)
        self.shape.setCurrentIndex(SHAPES.index(shape))
        self.angle.setValue(angle if angle is not None else 45.0)
        self.spacing.setValue(spacing if spacing is not None else (0.2 if pattern.model else 2.0))
        self.table.setRowCount(0)
        for family in pattern.families:
            self._add_row(family, refresh=False)
        self._loading = False
        mine = not pattern.builtin
        for w in (self.name, self.kind, self.shape, self.angle, self.spacing, self.table, self.add_row, self.del_row,
                  self.apply, self.remove):
            w.setEnabled(mine)
        self.locked.setVisible(not mine)
        self._changed()

    def _add_row(self, family, refresh=True):
        angle, x0, y0, shift, step, dashes = family
        blocker = QtCore.QSignalBlocker(self.table)
        r = self.table.rowCount()
        self.table.insertRow(r)
        for c, value in enumerate((angle, x0, y0, shift, step)):
            self.table.setItem(r, c, QtWidgets.QTableWidgetItem(_txt(value)))
        self.table.setItem(r, 5, QtWidgets.QTableWidgetItem(" ".join(_txt(d) for d in dashes)))
        del blocker
        if refresh:
            self.shape.setCurrentIndex(SHAPES.index("custom"))
            self._changed()

    def _remove_row(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
            self._changed()

    def _changed(self):
        """The form as it stands: the spacing's unit, which fields count, the sample."""
        if self._loading:
            return
        model = bool(self.kind.currentData())
        self.spacing.setSuffix(" m" if model else " mm")
        custom = self.shape.currentData() == "custom"
        for w in (self.angle, self.spacing):
            self.form.setRowVisible(w, not custom)
        for w in (self.table, self.add_row, self.del_row, self.table_hint):
            w.setVisible(custom)
        draft = self.draft()
        image = QtGui.QPixmap(*PREVIEW)
        image.fill(QtGui.QColor("white"))
        if not isinstance(draft, str):
            p = QtGui.QPainter(image)
            p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            path = QtGui.QPainterPath()
            path.addRect(QtCore.QRectF(0, 0, *PREVIEW))
            # (a drafting pattern 4 px a mm; a model one at 1:20)
            pattern_paint.paint(p, path, draft, "#2b2f36", 4.0 * (50.0 if draft.model else 1.0), 1.0)
            p.setPen(QtGui.QPen(QtGui.QColor("#9aa3ad"), 1.0))
            p.drawRect(QtCore.QRectF(0.5, 0.5, PREVIEW[0] - 1, PREVIEW[1] - 1))
            p.end()
        self.preview.setPixmap(image)

    def _families(self):
        """The table's families, or an error text."""
        out = []
        for r in range(self.table.rowCount()):
            cells = [self.table.item(r, c).text() if self.table.item(r, c) is not None else "" for c in range(6)]
            try:
                angle, x0, y0, shift, step = (_num(v) for v in cells[:5])
                dashes = tuple(_num(d) for d in cells[5].replace(";", " ").split())
            except ValueError:
                return t("patt.err_number", row=r + 1)
            if abs(step) < 1e-9:
                return t("patt.err_step", row=r + 1)
            if dashes and dashes[0] < 0:
                dashes = (0.0,) + dashes                   # (it starts with a gap: a dot, then the gap)
            out.append((angle, x0, y0, shift, step, dashes))
        return tuple(out) if out else t("patt.err_empty")

    def draft(self):
        """The pattern as the form has it (with the shown one's key), or an error text."""
        p = self.current
        if p is None:
            return t("patt.err_empty")
        name = self.name.text().strip()
        if not name:
            return t("types.err_name")
        if any(pattern_paint.name(k) == name for k in self._keys() if k != p.key):
            return t("patt.err_same_name", name=name)
        model = bool(self.kind.currentData())
        shape = self.shape.currentData()
        if shape != "custom":
            return core_patterns.simple(p.key, name, model, self.angle.value(), self.spacing.value(),
                                        crossed=shape == "cross")
        families = self._families()
        if isinstance(families, str):
            return families
        return core_patterns.Pattern(p.key, model, families, name)

    # ------------------------------------------------------------ actions

    def _save(self, pattern, old=None):
        key = self.on_save(pattern, old) if self.on_save is not None else None
        if key is not None:
            self._fill_list(key)
        return key

    def apply_changes(self):
        new = self.draft()
        if isinstance(new, str):
            QtWidgets.QMessageBox.warning(self, t("patt.title"), new)
            return None
        return self._save(new, self.current.key)

    def _unique(self, base):
        names = {pattern_paint.name(k) for k in self._keys()}
        if base not in names:
            return base
        n = 2
        while "{} ({})".format(base, n) in names:
            n += 1
        return "{} ({})".format(base, n)

    def new_pattern(self):
        """A new pattern of the project's: diagonal lines 2 mm apart, to be changed."""
        key = core_patterns.PROJECT + uuid.uuid4().hex[:12]
        return self._save(core_patterns.simple(key, self._unique(t("patt.new_name")), False, 45.0, 2.0))

    def duplicate_pattern(self):
        """A copy of the one chosen (the program's or the project's), the project's own."""
        p = self.current
        if p is None:
            return None
        key = core_patterns.PROJECT + uuid.uuid4().hex[:12]
        made = replace(p, key=key, name=self._unique(t("vstyle.copy_of", name=pattern_paint.name(p.key))))
        return self._save(made)

    def delete_pattern(self):
        if self.current is not None and not self.current.builtin and self.on_delete is not None \
                and self.on_delete(self.current.key):
            self._fill_list()
