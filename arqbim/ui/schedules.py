"""Schedules panel ("Tabelas"), at the bottom of the window (View ▸ Schedules, Ctrl+T):
the elements of one category with their quantities and totals, or one line per type.
Like a spreadsheet: names, wall lengths and heights, column heights can be typed in a
cell (one undo step each, as in the Properties panel). A click selects the element in
3D, a double-click on a cell one cannot edit frames it; "Export CSV" writes the table
for Excel. Brought up to date whenever the model changes while it is shown.

(0.477, the owner: «A aba de tabelas também deve ser gerenciada pelo painel lateral, mas a tabela deve ser gerada na
tela e não no rodapé») The table is a view of its own, in a tab over the canvas as a sheet is (("table", its ref): a
category's key or "def:<uid>"), its title over it as Revit's («<Paredes>»); the tables are chosen in the side panel
«Tabelas» (ui/tables_panel.py) and its commands are on the parameters' bar (context_items): Propriedades… (as Revit's
Table Properties), Por tipo, Realçar no modelo, Pôr na folha, Exportar….
"""

import re

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.units import format_length, parse_length
from ..i18n import decimal_sep, t
from ..model import schedules
from ..model.document import VIEWS_CHANGED

GUID = QtCore.Qt.ItemDataRole.UserRole
ACTION = QtCore.Qt.ItemDataRole.UserRole + 1


def _number(column, value):
    if value is None:
        return ""
    sep = decimal_sep()
    if column in ("area", "projected"):                     # (0.265: a roof's area in plan too)
        return "{:.2f} m²".format(value).replace(".", sep)
    if column == "volume":
        return "{:.3f} m³".format(value).replace(".", sep)
    return format_length(value, sep).replace("~ ", "")


class SchedulesPanel(QtWidgets.QWidget):
    """(0.477) A table shown in its tab over the canvas (it was a panel along the window's foot: its name kept)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("schedules")
        body = self
        layout = QtWidgets.QVBoxLayout(body)
        layout.setContentsMargins(6, 6, 6, 6)
        self.heading = QtWidgets.QLabel("")             # (0.477) its title over it, as Revit's «<Paredes>»
        self.heading.setObjectName("table_heading")
        self.heading.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.heading)
        bar = QtWidgets.QHBoxLayout()
        self.category = QtWidgets.QComboBox()
        for key in schedules.ORDER:
            self.category.addItem(t("sched.cat." + key), key)
        self.grouped = QtWidgets.QCheckBox(t("sched.by_type"))
        self.export = QtWidgets.QPushButton(t("sched.export"))
        self.new_def = QtWidgets.QPushButton(t("sched.new"))          # (0.131) the project's own schedules
        self.edit_def = QtWidgets.QPushButton(t("sched.edit"))
        self.delete_def = QtWidgets.QPushButton(t("sched.delete"))
        self.put = QtWidgets.QPushButton(t("sched.put"))            # (0.132) on a sheet
        self.put_menu = QtWidgets.QMenu(self.put)
        self.put.setMenu(self.put_menu)
        self.put_menu.aboutToShow.connect(self._fill_put_menu)
        self.totals = QtWidgets.QLabel()
        self.totals.setWordWrap(True)
        for w in (self.category, self.grouped, self.new_def, self.edit_def, self.delete_def, self.put, self.export):
            bar.addWidget(w)
            w.hide()                 # (0.477: the table is chosen in the side panel, its commands on the bar above)
        layout.addLayout(bar)
        self.table = QtWidgets.QTableWidget()
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked
                                   | QtWidgets.QAbstractItemView.EditTrigger.EditKeyPressed
                                   | QtWidgets.QAbstractItemView.EditTrigger.AnyKeyPressed)
        self.table.verticalHeader().setVisible(True)  # (0.477: the rows numbered, as Revit's and a spreadsheet's)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.totals)

        # callbacks set by the main window
        self.on_edit = None          # (action, guid, value)
        self.on_select = None        # (ids)
        self.on_frame = None         # (ids)
        self.on_shown = None         # () came into view while out of date
        self.on_export = None        # (header, table)
        self.on_defs = None          # (the project's own schedules, all of them, as they are to be now) (0.131)
        self.on_put = None           # (sheet index or None for a new one, "schedule", its ref) (0.132)
        self.on_ref = None           # (0.477) (its ref): another table shown in it (its tab follows)
        self.on_highlight = None     # (0.477) (ids): Realçar no modelo — the rows' elements chosen in the model

        # (0.477) its commands, on the window's parameters' bar while a table's tab is shown
        def act(text, slot, tip=None, checkable=False):
            a = QtGui.QAction(text, self)
            a.setCheckable(checkable)
            if tip:
                a.setToolTip(tip)
            a.triggered.connect(slot)
            return a
        self.act_properties = act(t("sched.properties"), lambda _on=False: self.properties(),
                                  t("sched.properties_tip"))
        self.act_grouped = act(t("sched.by_type"), lambda on: self.grouped.setChecked(on), checkable=True)
        self.grouped.toggled.connect(lambda on: self.act_grouped.setChecked(on))
        self.act_highlight = act(t("sched.highlight"), lambda _on=False: self.highlight(), t("sched.highlight_tip"))
        self.act_put = act(t("sched.put"), lambda _on=False: None)
        self.act_put.setMenu(self.put_menu)
        self.act_export = act(t("sched.export_short"), lambda _on=False: self._export(), t("sched.export_tip"))
        self.act_delete = act(t("sched.delete"), lambda _on=False: self._delete_schedule())

        self.doc = None
        self._stale = True
        self._filling = False
        self._shown = set()          # element ids in the table
        self._columns = ()
        self.category.currentIndexChanged.connect(lambda _i: self._ref_changed())
        self.grouped.toggled.connect(lambda _on: self.refresh())
        self.export.clicked.connect(self._export)
        self.new_def.clicked.connect(lambda: self.edit_schedule(None))
        self.edit_def.clicked.connect(lambda: self.edit_schedule(self._own()))
        self.delete_def.clicked.connect(self._delete_schedule)
        self.table.itemChanged.connect(self._changed)
        self.table.itemSelectionChanged.connect(self._selected)
        self.table.itemDoubleClicked.connect(self._double_clicked)
        self.restyle()

    def showEvent(self, event):
        super().showEvent(event)
        if self._stale and self.on_shown is not None:
            self.on_shown()

    def restyle(self):
        from . import theme
        self.heading.setStyleSheet("QLabel#table_heading { font-size: 15px; font-weight: 600; color: %s;"
                                   " padding: 4px; }" % theme.C["text"])

    @staticmethod
    def _later(fn, *args):
        if fn is not None:
            QtCore.QTimer.singleShot(0, lambda: fn(*args))

    # ------------------------------------------------------------ (0.477) the table in its tab

    def ref(self):
        """The table shown: a category's key, or "def:<uid>" (the project's own)."""
        return self.category.currentData()

    def show_ref(self, ref):
        """That table shown (its tab was chosen)."""
        k = self.category.findData(ref)
        if k < 0 and self.doc is not None:
            self._sync_categories()
            k = self.category.findData(ref)
        if k >= 0 and k != self.category.currentIndex():
            self.category.setCurrentIndex(k)           # (refreshes it)
        else:
            self.refresh()

    def _ref_changed(self):
        self.refresh()
        if self.on_ref is not None and self.ref():
            self.on_ref(self.ref())

    def title_of(self, ref):
        """A table's name: its category's («Paredes»), or the project's own one's."""
        if str(ref).startswith("def:"):
            own = next((d for d in getattr(self.doc, "schedule_defs", ()) if "def:" + d.uid == ref), None)
            return own.name if own is not None else t("sched.title")
        return t("sched.cat." + ref) if ref in schedules.CATEGORIES else t("sched.title")

    def context_items(self):
        """The parameters' bar while the table is shown: its name, Propriedades…, Por tipo (a category's), Realçar no
        modelo, Pôr na folha, Exportar… (and Apagar, the project's own)."""
        own = self._own()
        items = [("title", t("sched.bar_title", name=self.title_of(self.ref())))]
        items += [("action", self.act_properties)]
        if own is None:
            items.append(("action", self.act_grouped))
        items += [("separator",), ("action", self.act_highlight), ("action", self.act_put), ("action", self.act_export)]
        if own is not None:
            items += [("separator",), ("action", self.act_delete)]
        return items

    def properties(self):
        """Propriedades… (as Revit's Table Properties): the project's own table edited — a category's made one of the
        project's own, starting from its columns."""
        own = self._own()
        if own is not None:
            self.edit_schedule(own)
            return
        key = self.ref() if self.ref() in schedules.CATEGORIES else "walls"
        defn = schedules.ScheduleDef(t("sched.cat." + key), key, list(schedules.available(key)))
        self.edit_schedule(defn)                         # (a new one: added on OK)

    def highlight(self):
        """Realçar no modelo: the elements of the rows chosen (all of them, none chosen) chosen in the model."""
        rows = sorted({i.row() for i in self.table.selectionModel().selectedRows()}) or range(self.table.rowCount())
        ids = [self.table.item(r, 0).data(GUID) for r in rows if self.table.item(r, 0) is not None]
        ids = [i for i in ids if i is not None]
        if ids and self.on_highlight is not None:
            self._later(self.on_highlight, ids)
        return ids

    # ------------------------------------------------------------ content

    def wants(self, changed, removed):
        """Does a document change concern what is shown? (out of view: brought up to date later)"""
        if self.isHidden():
            self._stale = True
            return False
        return changed is None or self._stale or bool(removed) or any(i in self._shown for i in changed) \
            or any(self.doc.get(i) is not None and self.doc.get(i).is_bim for i in changed) \
            or VIEWS_CHANGED in changed                     # (the project's own schedules changed, 0.131)

    def mark_stale(self):
        self._stale = True

    def show_document(self, doc):
        self.doc = doc
        self.refresh()

    def _sync_categories(self):
        """The list: the categories ("Paredes (24)"), then the project's own schedules (0.131: "def:<uid>")."""
        current = self.category.currentData()
        defs = list(getattr(self.doc, "schedule_defs", []))
        wanted = list(schedules.ORDER) + ["def:" + d.uid for d in defs]
        self.category.blockSignals(True)
        if [self.category.itemData(k) for k in range(self.category.count())] != wanted:
            self.category.clear()
            for key in wanted:
                self.category.addItem("", key)
            self.category.setCurrentIndex(max(0, self.category.findData(current)))
        counts = schedules.counts(self.doc)
        for k, cat in enumerate(schedules.ORDER):
            self.category.setItemText(k, "{} ({})".format(t("sched.cat." + cat), counts[cat]))
        for k, d in enumerate(defs):
            self.category.setItemText(len(schedules.ORDER) + k, t("sched.own", name=d.name))
        self.category.blockSignals(False)

    def _own(self):
        """The project's own schedule shown, or None (a category)."""
        data = self.category.currentData() or ""
        if not data.startswith("def:") or self.doc is None:
            return None
        return next((d for d in self.doc.schedule_defs if "def:" + d.uid == data), None)

    def refresh(self):
        if self.doc is None:
            return
        self._stale = False
        self._sync_categories()
        self.heading.setText("<{}>".format(self.title_of(self.ref())))      # (0.477, as Revit's)
        own = self._own()
        self.grouped.setVisible(own is None)
        self.edit_def.setEnabled(own is not None)
        self.delete_def.setEnabled(own is not None)
        if own is not None:
            self._refresh_own(own)
            return
        key = self.category.currentData()
        rooms = key in schedules.ROOMS                      # (0.125: grouped by storey, not by type)
        self.grouped.setText(t("sched.by_storey" if rooms else "sched.by_type"))
        lines = schedules.rows(self.doc, key)
        total = schedules.totals(lines, key)
        self._filling = True
        self.table.clear()
        if self.grouped.isChecked():
            groups = schedules.by_type(lines, key)
            self._columns = ("type", "count") + tuple(c for c in schedules.CATEGORIES[key][1] if c in schedules.SUMMED)
            self.table.setColumnCount(len(self._columns))
            self.table.setRowCount(len(groups))
            for r, g in enumerate(groups):
                for c, col in enumerate(self._columns):
                    self._cell(r, c, col, g.get(col), None, None)
            self._shown = {line["guid"] for line in lines}
        else:
            self._columns = schedules.CATEGORIES[key][1]
            self.table.setColumnCount(len(self._columns))
            self.table.setRowCount(len(lines))
            for r, line in enumerate(lines):
                for c, col in enumerate(self._columns):
                    self._cell(r, c, col, line.get(col), line["guid"], schedules.editable(key, col, line))
            self._shown = {line["guid"] for line in lines}
        labels = [t("sched.col." + c) for c in self._columns]
        if rooms and self.grouped.isChecked():
            labels[0] = t("sched.col.storey")
        self.table.setHorizontalHeaderLabels(labels)
        self.table.resizeColumnsToContents()
        self._filling = False
        circuits = key == "circuits"
        parts = [t("sched.count_rooms" if rooms else ("sched.count_circuits" if circuits else "sched.count"),
                   n=total["count"])]
        for col in ("length", "area", "volume"):
            if total.get(col) is not None:
                parts.append("{}: {}".format(t("sched.col." + col), _number(col, total[col])))
        if circuits and total.get("power") is not None:            # (0.144) the installed power, its current
            parts.append("{}: {}   ({})".format(t("sched.col.power"), schedules.text_of("power", total["power"]),
                                                schedules.text_of("current", total["power"] / 230.0, decimal_sep())))
        self.totals.setText("   ".join(parts))
        if self.grouped.isChecked():
            groups = schedules.by_type(lines, key)
            self._export_rows = [[g.get(c) for c in self._columns] for g in groups]
        else:
            self._export_rows = [[line.get(c) for c in self._columns] for line in lines]

    def _label(self, own, col):
        """A column's heading: a formula's name, else the column's."""
        if col.startswith("formula:"):
            k = int(col.split(":")[1])
            return own.formulas[k][0] if own is not None and k < len(own.formulas) else col
        return t("sched.col." + col)

    def _refresh_own(self, own):
        """A schedule of the project's own (0.131): its columns and formulas, filtered, sorted — or one line per
        value of its group column."""
        columns, lines = schedules.apply(own, schedules.rows(self.doc, own.category))
        self._filling = True
        self.table.clear()
        if own.group:
            groups, self._columns = schedules.grouped(own, lines)
            self.table.setColumnCount(len(self._columns))
            self.table.setRowCount(len(groups))
            for r, g in enumerate(groups):
                for c, col in enumerate(self._columns):
                    self._cell(r, c, col, g.get(col), None, None)
            self._export_rows = [[g.get(c) for c in self._columns] for g in groups]
        else:
            self._columns = tuple(columns)
            self.table.setColumnCount(len(self._columns))
            self.table.setRowCount(len(lines))
            for r, line in enumerate(lines):
                for c, col in enumerate(self._columns):
                    action = None if col.startswith("formula:") else schedules.editable(own.category, col, line)
                    self._cell(r, c, col, line.get(col), line["guid"], action)
            self._export_rows = [[line.get(c) for c in self._columns] for line in lines]
        self._shown = {line["guid"] for line in lines}
        self.table.setHorizontalHeaderLabels([self._label(own, c) for c in self._columns])
        self.table.resizeColumnsToContents()
        self._filling = False
        parts = [t("sched.count_rooms" if own.category in schedules.ROOMS else "sched.count", n=len(lines))]
        for col in [c for c in own.fields if c in schedules.SUMMED] + \
                [schedules.formula_key(k) for k in range(len(own.formulas))]:
            values = [line[col] for line in lines if isinstance(line.get(col), (int, float))]
            if values:
                parts.append("{}: {}".format(self._label(own, col), _number(col, sum(values))))
        self.totals.setText("   ".join(parts))

    def edit_schedule(self, own):
        """New schedule… (own None: of the category shown) / Edit… : the editor, then the schedules as they are to
        be now (one undo step, by the window)."""
        from . import schedule_editor
        if own is None:
            key = self.category.currentData()
            category = key if key in schedules.ORDER else "walls"
            defn = schedules.ScheduleDef(t("sched.untitled"), category, list(schedules.available(category)))
        else:
            defn = own
        dialog = schedule_editor.ScheduleEditor(self, defn)
        self._editor = dialog                             # (tests fill it in)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        new = dialog.definition()
        defs = list(self.doc.schedule_defs)
        k = next((i for i, d in enumerate(defs) if d.uid == new.uid), None)
        if k is None:
            defs.append(new)
        else:
            defs[k] = new
        if self.on_defs is not None:
            self.on_defs(defs)
        self.category.setCurrentIndex(max(0, self.category.findData("def:" + new.uid)))
        self.refresh()

    def _fill_put_menu(self):
        """Put on a sheet ▸ the sheets there are, and a new one (0.132)."""
        self.put_menu.clear()
        ref = self.category.currentData()
        for k, sheet in enumerate(getattr(self.doc, "sheets", [])):
            self.put_menu.addAction(sheet.name, lambda k=k: self.put_on(k, ref))
        self.put_menu.addSeparator()
        self.put_menu.addAction(t("tree.new_sheet"), lambda: self.put_on(None, ref))

    def put_on(self, index, ref=None):
        """The schedule shown on sheet `index` (None: a new one)."""
        ref = ref or self.category.currentData()
        if self.on_put is not None and ref:
            self._later(self.on_put, index, "schedule", ref)

    def _delete_schedule(self):
        own = self._own()
        if own is None or self.on_defs is None:
            return
        self.on_defs([d for d in self.doc.schedule_defs if d.uid != own.uid])
        self.category.setCurrentIndex(0)
        self.refresh()

    def _cell(self, r, c, col, value, guid, action):
        if col.startswith("formula:"):                    # (a formula's value, 0.131)
            text = "" if value is None else "{:.2f}".format(value).replace(".", decimal_sep())
        elif col in schedules.NUMBERS:
            text = _number(col, value)
        elif col == "count":
            text = str(value)
        elif col in schedules.UNITS or col == "points":   # (a circuit's: W, A, mm², its points, 0.144)
            text = schedules.text_of(col, value, decimal_sep())
        else:
            text = str(value) if value is not None else ""
        item = QtWidgets.QTableWidgetItem(text)
        item.setData(GUID, guid)
        item.setData(ACTION, action)
        if col in schedules.NUMBERS or col in schedules.UNITS or col in ("count", "points", "pieces") or \
                col.startswith("formula:"):
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        if action is None:
            item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(r, c, item)

    def show_selection(self, ids):
        """Mark the rows of what is selected in 3D."""
        if self._filling or not self.isVisible():
            return
        ids = set(ids)
        current = {self.table.item(i.row(), 0).data(GUID) for i in self.table.selectionModel().selectedRows()}
        if current == ids:
            return
        self.table.blockSignals(True)
        self.table.clearSelection()
        mode = QtCore.QItemSelectionModel.SelectionFlag.Select | QtCore.QItemSelectionModel.SelectionFlag.Rows
        first = None
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item is not None and item.data(GUID) in ids:
                self.table.selectionModel().select(self.table.model().index(r, 0), mode)
                first = item if first is None else first
        if first is not None and len(ids) == 1:
            self.table.scrollToItem(first)
        self.table.blockSignals(False)

    def text(self):
        """The table as plain text (used by tests): one line per row, cells separated by ' | '."""
        lines = [" | ".join(self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount()))]
        for r in range(self.table.rowCount()):
            lines.append(" | ".join(self.table.item(r, c).text() for c in range(self.table.columnCount())))
        return "\n".join(lines)

    # ------------------------------------------------------------ user actions

    def _changed(self, item):
        if self._filling:
            return
        action, guid = item.data(ACTION), item.data(GUID)
        if action is None or guid is None:
            return
        text = item.text().strip()
        words = action.split(":")[0] in schedules.TEXT_ACTIONS        # (a name, a room's number or finishes)
        if action in ("circuit_breaker", "circuit_section"):          # (0.144) "16", "16 A", "2,5 mm²": the number
            found = re.search(r"\d+(?:[.,]\d+)?", text)
            value = float(found.group(0).replace(",", ".")) if found else None
        else:
            value = text if words else parse_length(text, unit="m")   # ("6", "6,20 m", "620cm"…: shown in m)
        if value is None or (value == "" and action in ("name", "room_name", "room_number", "circuit_name")):
            self._later(self.refresh)                         # not a value: show the model's again
            return
        if ":" in action:                                     # ("room_finish:FloorCovering": which one)
            action = tuple(action.split(":", 1))
        self._later(self.on_edit, action, guid, value)

    def _selected(self):
        if self._filling or self.grouped.isChecked():
            return
        ids = [self.table.item(i.row(), 0).data(GUID) for i in self.table.selectionModel().selectedRows()]
        self._later(self.on_select, [i for i in ids if i is not None])

    def _double_clicked(self, item):
        if item.data(ACTION) is None and item.data(GUID) is not None:
            self._later(self.on_frame, [item.data(GUID)])

    def _export(self):
        """The table as shown (its values as numbers, for Excel)."""
        header = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
        if self.on_export is not None:
            self.on_export(header, list(getattr(self, "_export_rows", [])), columns=list(self._columns))


def dock(parent):
    """(0.477) The table's page, hidden until a table's tab is chosen (the window puts it in place of the canvas)."""
    panel = SchedulesPanel(parent)
    panel.hide()
    return panel
