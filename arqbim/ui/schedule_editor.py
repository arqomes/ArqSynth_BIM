"""Schedules ▸ New / Edit schedule… (0.131): a schedule of the project's own (model/schedules.ScheduleDef) — its
name and category, the columns it shows (ticked, in the order dragged), its formula columns (a name and an
expression of the number columns: "length * height"), its filters (a column, how, a value), the column it is
sorted by (and which way) and the one it is grouped by.

(0.477, the owner: «seria bom copiar o revit a forma como cria os elementos e filtra as informações») As Revit's
«Propriedades da tabela», in tabs: Campos — «Selecionar campos disponíveis em» (the category), a search over the
names, «Campos disponíveis» and «Campos tabelados (na ordem)» side by side with the buttons between them (→ add, ←
take away, ↑ ↓ the order, fx a calculated value); Filtro; Classificar/Agrupar."""

from PySide6 import QtCore, QtWidgets

from ..i18n import t
from ..model import schedules
from . import theme

KEY = QtCore.Qt.ItemDataRole.UserRole


def _column_name(key):
    return t("sched.col." + key)


class ScheduleEditor(QtWidgets.QDialog):
    def __init__(self, parent, defn):
        """defn: the schedule to edit (a new one: made by the caller with its category)."""
        super().__init__(parent)
        self.setWindowTitle(t("sched.editor"))
        self.setMinimumSize(640, 520)
        self.uid = defn.uid
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        self.name = QtWidgets.QLineEdit(defn.name)
        form.addRow(t("sched.def_name") + ":", self.name)
        layout.addLayout(form)
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs, 1)

        # Campos
        fields_page = QtWidgets.QWidget()
        col = QtWidgets.QVBoxLayout(fields_page)
        top = QtWidgets.QFormLayout()
        self.category = QtWidgets.QComboBox()
        for key in schedules.ORDER:
            self.category.addItem(t("sched.cat." + key), key)
        self.category.setCurrentIndex(max(0, self.category.findData(defn.category)))
        top.addRow(t("sched.def_category") + ":", self.category)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText(t("sched.search_fields"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _t: self._filter_available())
        top.addRow(t("sched.search_label") + ":", self.search)
        col.addLayout(top)
        lists = QtWidgets.QHBoxLayout()
        left = QtWidgets.QVBoxLayout()
        self.available_label = QtWidgets.QLabel(t("sched.available"))
        left.addWidget(self.available_label)
        self.available = QtWidgets.QListWidget()
        self.available.itemDoubleClicked.connect(lambda _i: self.add_fields())
        left.addWidget(self.available, 1)
        lists.addLayout(left, 1)
        middle = QtWidgets.QVBoxLayout()
        middle.addStretch(1)
        for text, tip, slot in (("→", "sched.add_field", self.add_fields), ("←", "sched.remove_field", self.remove_fields),
                                ("ƒx", "sched.calculated", lambda: self.add_formula(t("sched.formula_new"), ""))):
            b = QtWidgets.QToolButton()
            b.setText(text)
            b.setToolTip(t(tip))
            b.clicked.connect(lambda _on=False, s=slot: s())
            middle.addWidget(b)
        middle.addStretch(1)
        lists.addLayout(middle)
        right = QtWidgets.QVBoxLayout()
        right.addWidget(QtWidgets.QLabel(t("sched.def_fields")))
        self.fields = QtWidgets.QListWidget()           # the fields shown, in their order
        self.fields.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.fields.itemDoubleClicked.connect(lambda _i: self.remove_fields())
        right.addWidget(self.fields, 1)
        order = QtWidgets.QHBoxLayout()
        for text, tip, step in (("↑", "sched.field_up", -1), ("↓", "sched.field_down", 1)):
            b = QtWidgets.QToolButton()
            b.setText(text)
            b.setToolTip(t(tip))
            b.clicked.connect(lambda _on=False, s=step: self.move_field(s))
            order.addWidget(b)
        order.addStretch(1)
        right.addLayout(order)
        lists.addLayout(right, 1)
        col.addLayout(lists, 1)
        col.addWidget(QtWidgets.QLabel(t("sched.def_formulas")))
        self.formulas = QtWidgets.QTableWidget(0, 2)
        self.formulas.setHorizontalHeaderLabels([t("sched.formula_name"), t("sched.formula_expr")])
        self.formulas.horizontalHeader().setStretchLastSection(True)
        self.formulas.verticalHeader().setVisible(False)
        self.formulas.setMaximumHeight(110)
        col.addWidget(self.formulas)
        self.formula_hint = QtWidgets.QLabel()
        self.formula_hint.setWordWrap(True)
        self.formula_hint.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        col.addWidget(self.formula_hint)
        col.addLayout(self._buttons(self.formulas, lambda: self.add_formula("", "")))
        self.tabs.addTab(fields_page, t("sched.tab.fields"))

        # Filtro
        filter_page = QtWidgets.QWidget()
        col = QtWidgets.QVBoxLayout(filter_page)
        col.addWidget(QtWidgets.QLabel(t("sched.def_filters")))
        self.filters = QtWidgets.QTableWidget(0, 3)
        self.filters.setHorizontalHeaderLabels([t("sched.filter_column"), t("sched.filter_op"),
                                                t("sched.filter_value")])
        self.filters.horizontalHeader().setStretchLastSection(True)
        self.filters.verticalHeader().setVisible(False)
        col.addWidget(self.filters, 1)
        col.addLayout(self._buttons(self.filters, lambda: self.add_filter("", "=", "")))
        self.tabs.addTab(filter_page, t("sched.tab.filter"))

        # Classificar/Agrupar
        order_page = QtWidgets.QWidget()
        order = QtWidgets.QFormLayout(order_page)
        self.sort = QtWidgets.QComboBox()
        self.descending = QtWidgets.QCheckBox(t("sched.descending"))
        self.group = QtWidgets.QComboBox()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.sort, 1)
        row.addWidget(self.descending)
        order.addRow(t("sched.def_sort") + ":", row)
        order.addRow(t("sched.def_group") + ":", self.group)
        self.tabs.addTab(order_page, t("sched.tab.sort"))

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

    @staticmethod
    def _item(key):
        item = QtWidgets.QListWidgetItem(_column_name(key))
        item.setData(KEY, key)
        return item

    def _fill(self, defn):
        """The lists for the category chosen: the fields it shows (in its order), the others available."""
        keys = schedules.available(self.category.currentData())
        chosen = [k for k in defn.fields if k in keys]
        self.fields.clear()
        for key in chosen:
            self.fields.addItem(self._item(key))
        self._fill_available()
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

    def _fill_available(self):
        shown = set(self.chosen_fields())
        self.available.clear()
        for key in schedules.available(self.category.currentData()):
            if key not in shown:
                self.available.addItem(self._item(key))
        self._filter_available()

    def _filter_available(self):
        words = self.search.text().strip().lower()
        seen = 0
        for k in range(self.available.count()):
            item = self.available.item(k)
            hide = bool(words) and words not in item.text().lower()
            item.setHidden(hide)
            seen += not hide
        self.available_label.setText(t("sched.available_n", n=seen))

    def chosen_fields(self):
        return [self.fields.item(k).data(KEY) for k in range(self.fields.count())]

    def add_fields(self, keys=None):
        """→ : the fields chosen on the left (or `keys`) shown, at the end."""
        if keys is None:
            keys = [i.data(KEY) for i in self.available.selectedItems()] or \
                ([self.available.currentItem().data(KEY)] if self.available.currentItem() is not None else [])
        for key in keys:
            if key not in self.chosen_fields() and key in schedules.available(self.category.currentData()):
                self.fields.addItem(self._item(key))
        self._fill_available()

    def remove_fields(self, keys=None):
        """← : the fields chosen on the right (or `keys`) no longer shown."""
        if keys is None:
            keys = [i.data(KEY) for i in self.fields.selectedItems()] or \
                ([self.fields.currentItem().data(KEY)] if self.fields.currentItem() is not None else [])
        for k in reversed(range(self.fields.count())):
            if self.fields.item(k).data(KEY) in keys:
                self.fields.takeItem(k)
        self._fill_available()

    def move_field(self, step):
        """↑ ↓ : the field chosen on the right one place up or down."""
        k = self.fields.currentRow()
        j = k + step
        if k < 0 or not 0 <= j < self.fields.count():
            return
        item = self.fields.takeItem(k)
        self.fields.insertItem(j, item)
        self.fields.setCurrentRow(j)

    def add_formula(self, label, expression):
        r = self.formulas.rowCount()
        self.formulas.insertRow(r)
        self.formulas.setItem(r, 0, QtWidgets.QTableWidgetItem(label))
        self.formulas.setItem(r, 1, QtWidgets.QTableWidgetItem(expression))
        self.tabs.setCurrentIndex(0)

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
        fields = self.chosen_fields()
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
