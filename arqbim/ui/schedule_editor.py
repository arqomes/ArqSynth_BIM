"""Schedules ▸ New / Edit schedule… (0.131): a schedule of the project's own (model/schedules.ScheduleDef) — its
name and category, the columns it shows (ticked, in the order dragged), its formula columns (a name and an
expression of the number columns: "length * height"), its filters (a column, how, a value), the column it is
sorted by (and which way) and the one it is grouped by."""

from PySide6 import QtCore, QtWidgets

from ..i18n import t
from ..model import schedules
from . import theme


def _column_name(key):
    return t("sched.col." + key)


class ScheduleEditor(QtWidgets.QDialog):
    def __init__(self, parent, defn):
        """defn: the schedule to edit (a new one: made by the caller with its category)."""
        super().__init__(parent)
        self.setWindowTitle(t("sched.editor"))
        self.setMinimumWidth(560)
        self.uid = defn.uid
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        self.name = QtWidgets.QLineEdit(defn.name)
        form.addRow(t("sched.def_name") + ":", self.name)
        self.category = QtWidgets.QComboBox()
        for key in schedules.ORDER:
            self.category.addItem(t("sched.cat." + key), key)
        self.category.setCurrentIndex(max(0, self.category.findData(defn.category)))
        form.addRow(t("sched.def_category") + ":", self.category)
        layout.addLayout(form)

        layout.addWidget(QtWidgets.QLabel(t("sched.def_fields")))
        self.fields = QtWidgets.QListWidget()
        self.fields.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.fields.setMaximumHeight(150)
        layout.addWidget(self.fields)

        layout.addWidget(QtWidgets.QLabel(t("sched.def_formulas")))
        self.formulas = QtWidgets.QTableWidget(0, 2)
        self.formulas.setHorizontalHeaderLabels([t("sched.formula_name"), t("sched.formula_expr")])
        self.formulas.horizontalHeader().setStretchLastSection(True)
        self.formulas.verticalHeader().setVisible(False)
        self.formulas.setMaximumHeight(110)
        layout.addWidget(self.formulas)
        self.formula_hint = QtWidgets.QLabel()
        self.formula_hint.setWordWrap(True)
        self.formula_hint.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        layout.addWidget(self.formula_hint)
        layout.addLayout(self._buttons(self.formulas, lambda: self.add_formula("", "")))

        layout.addWidget(QtWidgets.QLabel(t("sched.def_filters")))
        self.filters = QtWidgets.QTableWidget(0, 3)
        self.filters.setHorizontalHeaderLabels([t("sched.filter_column"), t("sched.filter_op"),
                                                t("sched.filter_value")])
        self.filters.horizontalHeader().setStretchLastSection(True)
        self.filters.verticalHeader().setVisible(False)
        self.filters.setMaximumHeight(110)
        layout.addWidget(self.filters)
        layout.addLayout(self._buttons(self.filters, lambda: self.add_filter("", "=", "")))

        order = QtWidgets.QFormLayout()
        self.sort = QtWidgets.QComboBox()
        self.descending = QtWidgets.QCheckBox(t("sched.descending"))
        self.group = QtWidgets.QComboBox()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.sort, 1)
        row.addWidget(self.descending)
        order.addRow(t("sched.def_sort") + ":", row)
        order.addRow(t("sched.def_group") + ":", self.group)
        layout.addLayout(order)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._fill(defn)
        self.category.currentIndexChanged.connect(lambda _i: self._fill(self.definition()))

    @staticmethod
    def _buttons(table, on_add):
        bar = QtWidgets.QHBoxLayout()
        add = QtWidgets.QPushButton(t("tb.add_row"))
        remove = QtWidgets.QPushButton(t("tb.remove_row"))
        add.clicked.connect(on_add)
        remove.clicked.connect(lambda: table.removeRow(table.currentRow()) if table.currentRow() >= 0 else None)
        bar.addWidget(add)
        bar.addWidget(remove)
        bar.addStretch(1)
        return bar

    def _fill(self, defn):
        """The lists for the category chosen: its columns (those of defn ticked first, in its order)."""
        keys = schedules.available(self.category.currentData())
        chosen = [k for k in defn.fields if k in keys]
        self.fields.clear()
        for key in chosen + [k for k in keys if k not in chosen]:
            item = QtWidgets.QListWidgetItem(_column_name(key))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, key)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsDragEnabled)
            item.setCheckState(QtCore.Qt.CheckState.Checked if key in chosen else QtCore.Qt.CheckState.Unchecked)
            self.fields.addItem(item)
        numbers = [k for k in keys if k in schedules.NUMBERS]
        self.formula_hint.setText(t("sched.formula_hint", names=", ".join(numbers) or "—"))
        self.formulas.setRowCount(0)
        for label, expression in defn.formulas:
            self.add_formula(label, expression)
        self.filters.setRowCount(0)
        for column, op, value in defn.filters:
            self.add_filter(column, op, value)
        for combo, current in ((self.sort, defn.sort), (self.group, defn.group)):
            combo.clear()
            combo.addItem(t("sched.none"), "")
            for key in keys:
                combo.addItem(_column_name(key), key)
            combo.setCurrentIndex(max(0, combo.findData(current)))
        self.descending.setChecked(bool(defn.descending))

    def add_formula(self, label, expression):
        r = self.formulas.rowCount()
        self.formulas.insertRow(r)
        self.formulas.setItem(r, 0, QtWidgets.QTableWidgetItem(label))
        self.formulas.setItem(r, 1, QtWidgets.QTableWidgetItem(expression))

    def add_filter(self, column, op, value):
        r = self.filters.rowCount()
        self.filters.insertRow(r)
        columns = QtWidgets.QComboBox()
        for key in schedules.available(self.category.currentData()):
            columns.addItem(_column_name(key), key)
        columns.setCurrentIndex(max(0, columns.findData(column)))
        ops = QtWidgets.QComboBox()
        ops.addItems(list(schedules.OPERATORS))
        ops.setCurrentText(op if op in schedules.OPERATORS else "=")
        self.filters.setCellWidget(r, 0, columns)
        self.filters.setCellWidget(r, 1, ops)
        self.filters.setItem(r, 2, QtWidgets.QTableWidgetItem(value))

    def definition(self):
        """The schedule as set in the dialog."""
        fields = [self.fields.item(k).data(QtCore.Qt.ItemDataRole.UserRole) for k in range(self.fields.count())
                  if self.fields.item(k).checkState() == QtCore.Qt.CheckState.Checked]
        formulas = []
        for r in range(self.formulas.rowCount()):
            label = (self.formulas.item(r, 0).text() if self.formulas.item(r, 0) else "").strip()
            expression = (self.formulas.item(r, 1).text() if self.formulas.item(r, 1) else "").strip()
            if expression:
                formulas.append((label or expression, expression))
        filters = []
        for r in range(self.filters.rowCount()):
            column, op = self.filters.cellWidget(r, 0), self.filters.cellWidget(r, 1)
            value = (self.filters.item(r, 2).text() if self.filters.item(r, 2) else "").strip()
            if column is not None and op is not None:
                filters.append((column.currentData(), op.currentText(), value))
        defn = schedules.ScheduleDef(self.name.text().strip() or t("sched.untitled"), self.category.currentData(),
                                     fields, formulas, filters, self.sort.currentData() or "",
                                     self.descending.isChecked(), self.group.currentData() or "")
        defn.uid = self.uid
        return defn
