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

(0.478, the owner: «A tela, deve ser em células como no excel e ter as ferramentas de união de células alinhamento,
desenho de bordas, cálculo como no excel») A table of the project's own is shown as a spreadsheet (model/table_sheet):
white as paper, its columns lettered and its rows numbered, the headings in its first row, free rows over it (titles)
and under it (notes), the totals' row; a formula bar over it (the cell chosen, what is in it — a formula as written);
cells merged, aligned, in bold or italic, coloured, bordered; formulas as Excel's. Its commands are on the parameters'
bar (Unir, N, I, Alinhar, Bordas, Fundo, Inserir, ƒx), on the right button, and in the side panel (Inserir na
tabela). A category's list stays a list: «Formatar como no Excel» makes it a table of the project's.
"""

import re

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.units import format_length, parse_length
from ..i18n import decimal_sep, t
from ..model import schedules, table_sheet
from ..model.document import VIEWS_CHANGED

GUID = QtCore.Qt.ItemDataRole.UserRole
ACTION = QtCore.Qt.ItemDataRole.UserRole + 1
PLACE = QtCore.Qt.ItemDataRole.UserRole + 2     # (0.478) a grid cell's (row, col)
RAW = QtCore.Qt.ItemDataRole.UserRole + 3       # (0.478) what is written in it, as written (a formula in A1)
BORDER = QtCore.Qt.ItemDataRole.UserRole + 4    # (0.478) (its bordered sides «ltrb», thick)

# (0.478) a table of the project's is paper: white, black ink, whatever the theme (as the drawings are)
PAPER, INK, HEAD_FILL, ERROR_INK = "#ffffff", "#000000", "#e8ecf2", "#c00000"
PAPER_STYLE = ("QTableWidget { background: #ffffff; color: #000000; gridline-color: #d0d4da;"
               " selection-background-color: rgba(47, 111, 228, 70); selection-color: #000000; }")
ALIGN = {"left": QtCore.Qt.AlignmentFlag.AlignLeft, "center": QtCore.Qt.AlignmentFlag.AlignHCenter,
         "right": QtCore.Qt.AlignmentFlag.AlignRight}
FUNCTIONS = (("sum", "SOMA"), ("avg", "MÉDIA"), ("count", "CONTAR.VAL"), ("max", "MÁXIMO"), ("min", "MÍNIMO"))
CLEAR_AND_SELECT = QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect


def _number(column, value):
    if value is None:
        return ""
    sep = decimal_sep()
    if column in ("area", "projected"):                     # (0.265: a roof's area in plan too)
        return "{:.2f} m²".format(value).replace(".", sep)
    if column == "volume":
        return "{:.3f} m³".format(value).replace(".", sep)
    return format_length(value, sep).replace("~ ", "")


def _numeric_column(col):
    return col in schedules.NUMBERS or col in schedules.UNITS or col in ("count", "points", "pieces") or \
        col.startswith("formula:")


class CellDelegate(QtWidgets.QStyledItemDelegate):
    """(0.478) A grid cell: its borders drawn over it; edited, what is written in it (a formula as written)."""

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        found = index.data(BORDER)
        if not found:
            return
        sides, thick = found
        painter.save()
        pen = QtGui.QPen(QtGui.QColor(INK), 2.0 if thick else 1.0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        r = QtCore.QRectF(option.rect).adjusted(0.5, 0.5, -0.5, -0.5)
        if "l" in sides:
            painter.drawLine(r.topLeft(), r.bottomLeft())
        if "t" in sides:
            painter.drawLine(r.topLeft(), r.topRight())
        if "r" in sides:
            painter.drawLine(r.topRight(), r.bottomRight())
        if "b" in sides:
            painter.drawLine(r.bottomLeft(), r.bottomRight())
        painter.restore()

    def setEditorData(self, editor, index):
        raw = index.data(RAW)
        if raw and isinstance(editor, QtWidgets.QLineEdit):
            editor.setText(str(raw))
            return
        super().setEditorData(editor, index)


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
        # (0.478) the formula bar (as Excel's): the cell chosen, what is in it
        self.cell_bar = QtWidgets.QWidget()
        cells = QtWidgets.QHBoxLayout(self.cell_bar)
        cells.setContentsMargins(0, 0, 0, 2)
        cells.setSpacing(4)
        self.address = QtWidgets.QLabel("")
        self.address.setObjectName("cell_address")
        self.address.setMinimumWidth(52)
        self.address.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        fx = QtWidgets.QLabel("ƒx")
        fx.setObjectName("cell_fx")
        self.formula = QtWidgets.QLineEdit()
        self.formula.setObjectName("cell_formula")
        self.formula.setPlaceholderText(t("grid.formula_hint"))
        self.formula.setToolTip(t("grid.fx_tip"))
        self.formula.returnPressed.connect(self._formula_entered)
        cells.addWidget(self.address)
        cells.addWidget(fx)
        cells.addWidget(self.formula, 1)
        layout.addWidget(self.cell_bar)
        self.cell_bar.hide()
        self.table = QtWidgets.QTableWidget()
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked
                                   | QtWidgets.QAbstractItemView.EditTrigger.EditKeyPressed
                                   | QtWidgets.QAbstractItemView.EditTrigger.AnyKeyPressed)
        self.table.verticalHeader().setVisible(True)  # (0.477: the rows numbered, as Revit's and a spreadsheet's)
        self.table.setAlternatingRowColors(True)
        self.table.setItemDelegate(CellDelegate(self.table))
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._menu)
        self.table.currentCellChanged.connect(lambda r, c, _r, _c: self._show_cell(r, c))
        self.table.horizontalHeader().sectionResized.connect(self._resized)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.totals)

        # callbacks set by the main window
        self.on_edit = None          # (action, guid, value)
        self.on_select = None        # (ids)
        self.on_frame = None         # (ids)
        self.on_shown = None         # () came into view while out of date
        self.on_export = None        # (header, table, columns=…, grid=…)
        self.on_defs = None          # (the project's own schedules, all of them, as they are to be now[, label]) (0.131)
        self.on_put = None           # (sheet index or None for a new one, "schedule", its ref) (0.132)
        self.on_ref = None           # (0.477) (its ref): another table shown in it (its tab follows)
        self.on_highlight = None     # (0.477) (ids): Realçar no modelo — the rows' elements chosen in the model
        self.on_message = None       # (0.478) (text, warning): said in the window's footer

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
        # (0.478) the cells' tools (a table of the project's), as Excel's ribbon
        self.act_make_own = act(t("grid.make_own"), lambda _on=False: self.make_own(), t("grid.make_own_tip"))
        self.act_merge = act(t("grid.merge"), lambda _on=False: self.merge_cells(), t("grid.merge_tip"))
        self.act_bold = act(t("grid.bold"), lambda _on=False: self.toggle("b"), t("grid.bold_tip"))
        self.act_italic = act(t("grid.italic"), lambda _on=False: self.toggle("i"), t("grid.italic_tip"))
        for a, how in ((self.act_bold, "setBold"), (self.act_italic, "setItalic")):
            font = a.font()
            getattr(font, how)(True)
            a.setFont(font)
        self.align_menu = QtWidgets.QMenu(t("grid.align"), self)
        for how in ("left", "center", "right", None):
            self.align_menu.addAction(t("grid.align." + (how or "auto")), lambda how=how: self.align(how))
        self.border_menu = QtWidgets.QMenu(t("grid.borders"), self)
        for kind in table_sheet.BORDERS:
            self.border_menu.addAction(t("grid.border." + kind), lambda kind=kind: self.borders(kind))
        self.fill_menu = QtWidgets.QMenu(t("grid.fill"), self)
        for colour in table_sheet.FILLS:
            swatch = QtGui.QPixmap(14, 14)
            swatch.fill(QtGui.QColor(colour))
            self.fill_menu.addAction(QtGui.QIcon(swatch), t("grid.fill." + colour), lambda c=colour: self.fill(c))
        self.fill_menu.addSeparator()
        self.fill_menu.addAction(t("grid.fill.none"), lambda: self.fill(""))
        self.insert_menu = QtWidgets.QMenu(t("grid.insert"), self)
        self.insert_menu.aboutToShow.connect(lambda: self._fill_insert_menu(self.insert_menu))
        self.fx_menu = QtWidgets.QMenu(t("grid.functions"), self)
        self.fx_menu.aboutToShow.connect(lambda: self._fill_fx_menu(self.fx_menu))
        self.act_align = self._menu_action(t("grid.align"), self.align_menu)
        self.act_borders = self._menu_action(t("grid.borders"), self.border_menu, t("grid.borders_tip"))
        self.act_fill = self._menu_action(t("grid.fill"), self.fill_menu, t("grid.fill_tip"))
        self.act_insert = self._menu_action(t("grid.insert"), self.insert_menu, t("grid.insert_tip"))
        self.act_fx = self._menu_action(t("grid.functions"), self.fx_menu, t("grid.functions_tip"))

        self.doc = None
        self._stale = True
        self._filling = False
        self._shown = set()          # element ids in the table
        self._columns = ()
        self._in_grid = None         # (0.478) a table of the project's shown as a spreadsheet
        self._grid = self._geom = self._layout = None
        self._widths = {}            # (0.478) columns widened by hand, kept a moment later (one undo step)
        self._widths_later = QtCore.QTimer(self)
        self._widths_later.setSingleShot(True)
        self._widths_later.setInterval(500)
        self._widths_later.timeout.connect(self._keep_widths)
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
        self.address.setStyleSheet("QLabel#cell_address { border: 1px solid %s; border-radius: 3px; padding: 2px 4px;"
                                   " color: %s; }" % (theme.C["line"], theme.C["text"]))

    @staticmethod
    def _later(fn, *args):
        if fn is not None:
            QtCore.QTimer.singleShot(0, lambda: fn(*args))

    def _say(self, text, warning=True):
        if self.on_message is not None:
            self.on_message(text, warning)

    def _menu_action(self, text, menu, tip=None):
        """(0.478) A command with a menu (Alinhar, Bordas…): its button opens the menu."""
        a = QtGui.QAction(text, self)
        a.setMenu(menu)
        if tip:
            a.setToolTip(tip)
        a.triggered.connect(lambda _on=False, a=a: self._pop(a))
        return a

    @staticmethod
    def _pop(action):
        for w in action.associatedObjects():
            if isinstance(w, QtWidgets.QToolButton) and w.isVisible():
                w.showMenu()
                return
        action.menu().popup(QtGui.QCursor.pos())

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
        modelo, Pôr na folha, Exportar… (and Apagar, the project's own); (0.478) a category's list «Formatar como no
        Excel», a table of the project's its cells' tools: Unir, N, I, Alinhar, Bordas, Fundo, Inserir, ƒx."""
        own = self._own()
        items = [("title", t("sched.bar_title", name=self.title_of(self.ref())))]
        items += [("action", self.act_properties)]
        if own is None:
            items += [("action", self.act_grouped), ("action", self.act_make_own)]
        else:
            items += [("separator",)] + [("action", a) for a in (
                self.act_merge, self.act_bold, self.act_italic, self.act_align, self.act_borders, self.act_fill,
                self.act_insert, self.act_fx)]
        items += [("separator",), ("action", self.act_highlight), ("action", self.act_put), ("action", self.act_export)]
        if own is not None:
            items += [("separator",), ("action", self.act_delete)]
        return items

    def properties(self, prepare=None):
        """Propriedades… (as Revit's Table Properties): the project's own table edited — a category's made one of the
        project's own, starting from its columns."""
        own = self._own()
        if own is not None:
            self.edit_schedule(own, prepare)
            return
        key = self.ref() if self.ref() in schedules.CATEGORIES else "walls"
        defn = schedules.ScheduleDef(t("sched.cat." + key), key, list(schedules.available(key)))
        self.edit_schedule(defn, prepare)                # (a new one: added on OK)

    def highlight(self):
        """Realçar no modelo: the elements of the rows chosen (all of them, none chosen) chosen in the model."""
        rows = sorted({i.row() for i in self.table.selectedIndexes()}) or range(self.table.rowCount())
        ids = [self.table.item(r, 0).data(GUID) for r in rows if self.table.item(r, 0) is not None]
        ids = list(dict.fromkeys(i for i in ids if i is not None))
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

    def _grid_mode(self, on):
        """(0.478) A table of the project's as a spreadsheet (white as paper, cell by cell) — or a category's list
        (row by row, in the theme's colours)."""
        if on == self._in_grid:
            return
        self._in_grid = on
        self.cell_bar.setVisible(on)
        self.totals.setVisible(not on)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems if on else
                                        QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(not on)
        self.table.setStyleSheet(PAPER_STYLE if on else "")
        if not on:
            self._grid = self._geom = self._layout = None

    def refresh(self):
        if self.doc is None:
            return
        self._stale = False
        self._sync_categories()
        self.heading.setText("<{}>".format(self.title_of(self.ref())))      # (0.477, as Revit's)
        own = self._own()
        self._grid_mode(own is not None)
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
        self.table.clearSpans()
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
        value of its group column; (0.478) as a spreadsheet (model/table_sheet): its title and note rows, its headings,
        its elements, its totals, its cells' formats, merges and formulas — the cell chosen kept where it was."""
        place = (self.table.currentRow(), self.table.currentColumn())
        ranges = [(r.topRow(), r.leftColumn(), r.bottomRow(), r.rightColumn()) for r in self.table.selectedRanges()]
        grid, geom, columns, lines, layout = schedules.grid_of(
            self.doc, own, lambda c: t("sched.col." + c), decimal_sep(), lambda n: t("grid.total_n", n=n),
            schedules.project_tokens(self.doc))
        self._grid, self._geom, self._layout, self._columns = grid, geom, layout, tuple(columns)
        grouped = bool(own.group)
        self._filling = True
        self.table.clear()
        self.table.clearSpans()
        self.table.setColumnCount(geom.width)
        self.table.setRowCount(geom.rows)
        self.table.setHorizontalHeaderLabels([table_sheet.col_letter(c) for c in range(geom.width)])
        self.table.setVerticalHeaderLabels([str(g + 1) for g in range(geom.rows)])
        for g, line in enumerate(grid):
            for c, cell in enumerate(line):
                col = columns[c]
                guid = action = None
                if cell.zone == "D" and not grouped:
                    guid = lines[cell.row].get("guid")
                    if not col.startswith("formula:"):
                        action = schedules.editable(own.category, col, lines[cell.row])
                item = QtWidgets.QTableWidgetItem(cell.text)
                item.setData(GUID, guid)
                item.setData(ACTION, action)
                item.setData(PLACE, (g, c))
                item.setData(RAW, cell.raw)
                self._look(item, cell, col)
                if cell.zone == "D" and action is None:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(g, c, item)
        for g, c, rows, cols in table_sheet.merges_in_grid(layout, geom):
            self.table.setSpan(g, c, rows, cols)
        self._fit(grid, geom, layout)
        if 0 <= place[0] < geom.rows and 0 <= place[1] < geom.width:
            self.table.setCurrentCell(*place)
            for top, left, bottom, right in ranges:
                bottom, right = min(bottom, geom.rows - 1), min(right, geom.width - 1)
                if top <= bottom and left <= right:
                    self.table.setRangeSelected(QtWidgets.QTableWidgetSelectionRange(top, left, bottom, right), True)
        self._filling = False
        self._shown = {line.get("guid") for line in lines if line.get("guid")}
        self._export_rows = [[line.get(c) for c in columns] for line in lines]
        self._show_cell(self.table.currentRow(), self.table.currentColumn())
        parts = [t("sched.count_rooms" if own.category in schedules.ROOMS else "sched.count", n=len(lines))]
        self.totals.setText("   ".join(parts))

    def _look(self, item, cell, col):
        """(0.478) A grid cell as formatted: bold (the headings and totals, by default), italic, aligned (the headings
        centred, the numbers to the right, by default), its fill (the headings', light grey-blue), its borders; the ink
        black (an error red)."""
        fmt, zone = cell.fmt, cell.zone
        font = item.font()
        font.setBold(fmt.get("b", zone in ("H", "S")))
        font.setItalic(fmt.get("i", False))
        item.setFont(font)
        how = fmt.get("a")
        if how is None:
            numeric = isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool)
            how = "center" if zone == "H" else ("right" if numeric or (zone in ("D", "S") and _numeric_column(col)
                                                                        and cell.text) else "left")
        item.setTextAlignment(ALIGN[how] | QtCore.Qt.AlignmentFlag.AlignVCenter)
        fill = fmt.get("f") or (HEAD_FILL if zone == "H" else None)
        if fill:
            item.setBackground(QtGui.QBrush(QtGui.QColor(fill)))
        item.setForeground(QtGui.QBrush(QtGui.QColor(ERROR_INK if cell.error else INK)))
        if fmt.get("bd"):
            item.setData(BORDER, (fmt["bd"], bool(fmt.get("bw"))))

    def _fit(self, grid, geom, layout):
        """(0.478) Each column as wide as what it holds (a merged cell's text left out: it spans), or as widened by
        hand."""
        plain = self.table.fontMetrics()
        font = QtGui.QFont(self.table.font())
        font.setBold(True)
        bold = QtGui.QFontMetrics(font)
        spanned = {(g + i, c + j) for g, c, rows, cols in table_sheet.merges_in_grid(layout, geom)
                   for i in range(rows) for j in range(cols)}
        for c in range(geom.width):
            key = self._columns[c]
            if key in layout.widths:
                self.table.setColumnWidth(c, layout.widths[key])
                continue
            widest = 0
            for g, line in enumerate(grid):
                cell = line[c]
                if (g, c) in spanned or not cell.text:
                    continue
                metrics = bold if cell.fmt.get("b", cell.zone in ("H", "S")) else plain
                widest = max(widest, metrics.horizontalAdvance(cell.text))
            self.table.setColumnWidth(c, min(max(widest + 18, 48), 420))

    def _resized(self, c, _old, new):
        """(0.478) A column widened by hand (a table of the project's): kept with it a moment later."""
        if self._filling or not self._in_grid or not 0 <= c < len(self._columns):
            return
        self._widths[self._columns[c]] = int(new)
        self._widths_later.start()

    def _keep_widths(self):
        if not self._widths or self._layout is None:
            return
        layout = table_sheet.copy_layout(self._layout)
        layout.widths.update(self._widths)
        self._widths = {}
        self._set_layout(layout)

    def edit_schedule(self, own, prepare=None):
        """New schedule… (own None: of the category shown) / Edit… : the editor, then the schedules as they are to
        be now (one undo step, by the window). prepare(dialog): (0.478) something done in it first (a calculated
        column put in)."""
        from . import schedule_editor
        if own is None:
            key = self.category.currentData()
            category = key if key in schedules.ORDER else "walls"
            defn = schedules.ScheduleDef(t("sched.untitled"), category, list(schedules.available(category)))
        else:
            defn = own
        dialog = schedule_editor.ScheduleEditor(self, defn)
        self._editor = dialog                             # (tests fill it in)
        if prepare is not None:
            prepare(dialog)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        new = dialog.definition()
        new.grid = dict(getattr(defn, "grid", None) or {})          # (0.478: its cells kept)
        defs = list(self.doc.schedule_defs)
        k = next((i for i, d in enumerate(defs) if d.uid == new.uid), None)
        if k is None:
            defs.append(new)
        else:
            defs[k] = new
        if self.on_defs is not None:
            self.on_defs(defs)
        self._sync_categories()                 # (0.478: listed even when the change did not refresh it — hidden)
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
        if _numeric_column(col):
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        if action is None:
            item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(r, c, item)

    def show_selection(self, ids):
        """Mark the rows of what is selected in 3D."""
        if self._filling or not self.isVisible():
            return
        ids = set(ids)
        current = {i.data(GUID) for i in self.table.selectedItems()} - {None}
        if current == ids:
            return
        self.table.blockSignals(True)
        self.table.clearSelection()
        mode = QtCore.QItemSelectionModel.SelectionFlag.Select | QtCore.QItemSelectionModel.SelectionFlag.Rows
        first = None
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item is not None and item.data(GUID) is not None and item.data(GUID) in ids:
                self.table.selectionModel().select(self.table.model().index(r, 0), mode)
                first = item if first is None else first
        if first is not None and len(ids) == 1:
            self.table.scrollToItem(first)
        self.table.blockSignals(False)

    def text(self):
        """The table as plain text (used by tests): one line per row, cells separated by ' | '."""
        lines = [" | ".join(self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount()))]
        for r in range(self.table.rowCount()):
            lines.append(" | ".join(self.table.item(r, c).text() if self.table.item(r, c) is not None else ""
                                    for c in range(self.table.columnCount())))
        return "\n".join(lines)

    # ------------------------------------------------------------ (0.478) the cells of a table of the project's

    def data_rows(self):
        """The grid rows of the elements (of a table of the project's), else all rows (a category's list)."""
        if self._geom is None:
            return list(range(self.table.rowCount()))
        return [g for g in range(self._geom.rows) if self._geom.zone_of(g)[0] == "D"]

    def _picked(self):
        """The grid cells chosen [(row, col)] (none: the current one)."""
        cells = sorted({(i.row(), i.column()) for i in self.table.selectedIndexes()})
        if not cells and self.table.currentRow() >= 0 and self.table.currentColumn() >= 0:
            cells = [(self.table.currentRow(), self.table.currentColumn())]
        return cells

    def _blocks(self):
        """The blocks chosen [(top, left, bottom, right)] (none: the current cell)."""
        out = [(r.topRow(), r.leftColumn(), r.bottomRow(), r.rightColumn()) for r in self.table.selectedRanges()]
        g, c = self.table.currentRow(), self.table.currentColumn()
        if not out and g >= 0 and c >= 0:
            out = [(g, c, g, c)]
        return out

    def _grid_ready(self):
        if self._own() is None or self._geom is None:
            return False
        if self.table.currentRow() < 0 and not self.table.selectedIndexes():
            self._say(t("grid.pick_cell"))
            return False
        return True

    def _set_layout(self, layout, label=None):
        """The table's cells as they are to be now: one undo step."""
        own = self._own()
        if own is None or self.on_defs is None or layout is None:
            return False
        defs = [schedules.with_layout(d, layout) if d.uid == own.uid else d for d in self.doc.schedule_defs]
        self.on_defs(defs, label or t("cmd.table_cells"))
        self.refresh()
        return True

    def write(self, g, c, text):
        """What is written in a grid cell («Mapa de vãos», «12», «=SOMA(C:C)*1,23»)."""
        if self._geom is None:
            return False
        layout = table_sheet.set_value(self._layout, self._geom, g, c, text)
        if layout is None:
            self._say(t("grid.no_model_cell"))
            return False
        return self._set_layout(layout)

    def toggle(self, name):
        """Negrito / Itálico on the cells chosen (as the current one is: the other way)."""
        if not self._grid_ready():
            return
        g, c = self._picked()[0]
        defaults = {"b": lambda z: z in ("H", "S"), "i": lambda z: False}[name]
        cell = self._grid[g][c]
        on = not cell.fmt.get(name, defaults(cell.zone))
        layout = self._layout
        for g, c in self._picked():
            zone = self._grid[g][c].zone
            layout = table_sheet.set_format(layout, self._geom, [(g, c)], **{name: None if on == defaults(zone)
                                                                             else on})
        self._set_layout(layout)

    def align(self, how):
        if self._grid_ready():
            self._set_layout(table_sheet.set_format(self._layout, self._geom, self._picked(), a=how))

    def fill(self, colour):
        if self._grid_ready():
            self._set_layout(table_sheet.set_format(self._layout, self._geom, self._picked(), f=colour or ""))

    def borders(self, kind):
        if not self._grid_ready():
            return
        layout = self._layout
        for top, left, bottom, right in self._blocks():
            layout = table_sheet.set_borders(layout, self._geom, top, left, bottom, right, kind)
        self._set_layout(layout)

    def merge_cells(self):
        """Unir (as Excel's «Unir e centrar»): the block chosen merged, its text centred — or, one cell chosen in a
        merged block, separated."""
        if not self._grid_ready():
            return
        top, left, bottom, right = self._blocks()[0]
        if top == bottom and left == right or table_sheet.merge_at(self._layout, self._geom, top, left) == \
                (top, left, bottom - top + 1, right - left + 1):
            if table_sheet.merge_at(self._layout, self._geom, top, left) is not None:
                self._set_layout(table_sheet.unmerge(self._layout, self._geom, top, left))
            return
        layout = table_sheet.merge(self._layout, self._geom, top, left, bottom, right)
        if layout is None:
            self._say(t("grid.no_merge"))
            return
        self._set_layout(table_sheet.set_format(layout, self._geom, [(top, left)], a="center"))

    def clear_cells(self):
        """Delete on the table: what is written in the cells chosen cleared (their formats kept). False: none of
        them could be (the elements' rows: the model's — the window deletes those elements, as Revit does)."""
        if self._geom is None or self._own() is None:
            return False
        cells = [(g, c) for g, c in self._picked() if (self._geom.zone_of(g) or ("D",))[0] != "D"]
        if not cells:
            return False
        layout = self._layout
        for g, c in cells:
            layout = table_sheet.set_value(layout, self._geom, g, c, "") or layout
        self._set_layout(layout)
        return True

    def insert_row(self, where):
        """Inserir ▸ Linha acima / abaixo (a title or note row: another beside it; the headings, the elements, the
        totals: one over or under the table), Linha de título, Linha de notas."""
        if self._own() is None or self._geom is None:
            return
        layout = self._layout
        if where == "title":
            zone, at = "T", layout.top
        elif where == "note":
            zone, at = "N", layout.bottom
        else:
            g = self.table.currentRow()
            zone, row = self._geom.zone_of(g) or ("N", layout.bottom)
            if zone in table_sheet.FREE:
                at = row if where == "above" else row + 1
            elif where == "above":
                zone, at = "T", layout.top
            else:
                zone, at = "N", 0
        new = table_sheet.insert_rows(layout, zone, at)
        if new is None:
            self._say(t("grid.no_row"))
            return
        self._set_layout(new)
        geom = table_sheet.Geometry(new.top, self._geom.n, new.totals, new.bottom, list(self._columns))
        g = geom.grid_row(zone, at)
        if g is not None:
            self.table.setCurrentCell(g, 0, CLEAR_AND_SELECT)

    def delete_row(self):
        """Apagar a linha: the title or note rows chosen taken away."""
        if self._own() is None or self._geom is None:
            return
        rows = sorted({g for g, _c in self._picked()}, reverse=True)
        free = [self._geom.zone_of(g) for g in rows if (self._geom.zone_of(g) or ("D",))[0] in table_sheet.FREE]
        if not free:
            self._say(t("grid.no_row"))
            return
        layout = self._layout
        for zone, row in free:
            layout = table_sheet.delete_rows(layout, zone, row) or layout
        self._set_layout(layout)

    def toggle_totals(self):
        if self._own() is not None and self._layout is not None:
            layout = table_sheet.copy_layout(self._layout)
            layout.totals = not layout.totals
            self._set_layout(layout)

    def free_fields(self):
        """The fields a table of the project's could show and does not."""
        own = self._own()
        if own is None:
            return []
        return [k for k in schedules.available(own.category) if k not in own.fields]

    def _set_def(self, defn, label=None):
        defs = [defn if d.uid == defn.uid else d for d in self.doc.schedule_defs]
        if self.on_defs is not None:
            self.on_defs(defs, label)
        self.refresh()

    def insert_field(self, key):
        """Inserir ▸ Coluna com o campo (as Revit's «Inserir coluna»): that field's column after the current one."""
        own = self._own()
        if own is None or key in own.fields or key not in schedules.available(own.category):
            return False
        fields = list(own.fields)
        c = self.table.currentColumn()
        col = self._columns[c] if 0 <= c < len(self._columns) else None
        fields.insert(fields.index(col) + 1 if col in fields else len(fields), key)
        new = schedules.def_from_dict(dict(schedules.def_to_dict(own), fields=fields))
        self._set_def(new)
        return True

    def remove_column(self):
        """Tirar a coluna (as Revit's «Eliminar coluna»): its field (or calculated value) out of the table."""
        own = self._own()
        c = self.table.currentColumn()
        if own is None or not 0 <= c < len(self._columns):
            return
        if len(self._columns) <= 1:
            self._say(t("grid.one_column"))
            return
        col = self._columns[c]
        data = schedules.def_to_dict(own)
        if col.startswith("formula:"):
            k = int(col.split(":")[1])
            data["formulas"] = [f for i, f in enumerate(data["formulas"]) if i != k]
        else:
            data["fields"] = [f for f in data["fields"] if f != col]
        self._set_def(schedules.def_from_dict(data))

    def formula_column(self):
        """Inserir ▸ Coluna calculada (ƒx)…: the table's Properties, a calculated value put in, to be written."""
        self.properties(lambda d: (d.tabs.setCurrentIndex(0), d.add_formula(t("sched.formula_new"), "")))

    def insert_function(self, fn):
        """ƒx ▸ Soma / Média / Contar / Máximo / Mínimo da coluna: that formula in the cell chosen («=SOMA(C:C)»)."""
        if not self._grid_ready():
            return False
        g, c = self.table.currentRow(), self.table.currentColumn()
        name = dict(FUNCTIONS).get(fn)
        letter = table_sheet.col_letter(c)
        return name is not None and self.write(g, c, "={}({}:{})".format(name, letter, letter))

    def insert_token(self, token):
        """ƒx ▸ Dados do projeto: «{projeto}», «{data}», «{tabela}», «{n}» added to the text of the cell chosen."""
        if not self._grid_ready():
            return False
        g, c = self.table.currentRow(), self.table.currentColumn()
        raw = self._grid[g][c].raw if 0 <= g < len(self._grid) else ""
        text = "{" + token + "}"
        if raw and not raw.startswith("="):
            text = raw + ("" if raw.endswith(" ") else " ") + text
        return self.write(g, c, text)

    def insert(self, kind, key):
        """(the side panel's «Inserir na tabela») kind "field" | "function" | "token" | "row"."""
        if kind == "field":
            return self.insert_field(key)
        if kind == "function":
            return self.insert_function(key)
        if kind == "token":
            return self.insert_token(key)
        if kind == "row":
            self.insert_row(key)
            return True
        return False

    def make_own(self):
        """Formatar como no Excel: a category's list made a table of the project's (its columns; by type, grouped),
        shown in its place. One undo step."""
        own = self._own()
        if own is not None or self.doc is None:
            return own
        key = self.ref() if self.ref() in schedules.CATEGORIES else "walls"
        fields = list(schedules.available(key))
        group = ""
        if self.grouped.isChecked():
            group = "storey" if key in schedules.ROOMS and "storey" in fields else ("type" if "type" in fields else "")
        defn = schedules.ScheduleDef(t("sched.cat." + key), key, fields, group=group)
        if self.on_defs is not None:
            self.on_defs(list(self.doc.schedule_defs) + [defn], t("cmd.table_cells"))
        self.grouped.setChecked(False)
        self.show_ref("def:" + defn.uid)
        self._say(t("info.table_made_own", name=defn.name), False)
        return defn

    def _fill_insert_menu(self, menu):
        menu.clear()
        free = self._geom is not None
        for text, where in (("grid.row_above", "above"), ("grid.row_below", "below"), ("grid.title_row", "title"),
                            ("grid.note_row", "note")):
            menu.addAction(t(text), lambda where=where: self.insert_row(where)).setEnabled(free)
        menu.addSeparator()
        sub = menu.addMenu(t("grid.column"))
        fields = self.free_fields()
        for key in fields:
            sub.addAction(t("sched.col." + key), lambda key=key: self.insert_field(key))
        sub.setEnabled(bool(fields))
        menu.addAction(t("grid.column_fx"), self.formula_column).setEnabled(free)
        menu.addSeparator()
        totals = menu.addAction(t("grid.totals_row"), self.toggle_totals)
        totals.setCheckable(True)
        totals.setChecked(bool(self._layout is not None and self._layout.totals))
        totals.setEnabled(free)

    def _fill_fx_menu(self, menu):
        menu.clear()
        for fn, _name in FUNCTIONS:
            menu.addAction(t("grid.fn." + fn), lambda fn=fn: self.insert_function(fn))
        menu.addSeparator()
        data = menu.addMenu(t("grid.data"))
        for token in table_sheet.TOKENS:
            data.addAction(t("grid.data." + token), lambda token=token: self.insert_token(token))

    def _menu(self, pos):
        """(0.478) The right button on the table: a list's — Formatar como no Excel…; a table of the project's — its
        cells' commands, as Excel's."""
        menu = QtWidgets.QMenu(self)
        if not self._in_grid:
            menu.addAction(self.act_make_own)
            menu.addSeparator()
            for a in (self.act_highlight, self.act_properties, self.act_export):
                menu.addAction(a)
            self._last_menu = menu
            menu.popup(self.table.viewport().mapToGlobal(pos))
            return
        index = self.table.indexAt(pos)
        if index.isValid() and (index.row(), index.column()) not in self._picked():     # (as Excel: that cell chosen)
            self.table.setCurrentCell(index.row(), index.column(), CLEAR_AND_SELECT)
        g = self.table.currentRow()
        zone = (self._geom.zone_of(g) or ("D",))[0] if self._geom is not None else "D"
        menu.addAction(t("grid.clear"), self.clear_cells).setEnabled(zone != "D")
        menu.addSeparator()
        top, left, bottom, right = (self._blocks() or [(g, 0, g, 0)])[0]
        block = table_sheet.merge_at(self._layout, self._geom, top, left) if self._layout is not None else None
        merged = block is not None and (top == bottom and left == right or
                                        block == (top, left, bottom - top + 1, right - left + 1))
        menu.addAction(t("grid.unmerge" if merged else "grid.merge_menu"), self.merge_cells)
        menu.addAction(t("grid.bold_tip"), lambda: self.toggle("b"))
        menu.addAction(t("grid.italic_tip"), lambda: self.toggle("i"))
        for sub in (self.align_menu, self.border_menu, self.fill_menu):
            menu.addMenu(sub)
        menu.addSeparator()
        insert = menu.addMenu(t("grid.insert"))
        self._fill_insert_menu(insert)
        self._fill_fx_menu(menu.addMenu(t("grid.functions_menu")))
        if zone in table_sheet.FREE:
            menu.addAction(t("grid.delete_row"), self.delete_row)
        c = self.table.currentColumn()
        if 0 <= c < len(self._columns):
            own = self._own()
            name = self._label(own, self._columns[c]) if own is not None else ""
            menu.addAction(t("grid.delete_column", name=name), self.remove_column)
        menu.addSeparator()
        for a in (self.act_highlight, self.act_properties, self.act_export):
            menu.addAction(a)
        self._last_menu = menu                          # (tests reach it)
        menu.popup(self.table.viewport().mapToGlobal(pos))

    def _show_cell(self, r, c):
        """(0.478) The formula bar: the cell chosen («C7») and what is in it (a formula as written)."""
        if not self._in_grid:
            return
        item = self.table.item(r, c) if r >= 0 and c >= 0 else None
        if item is None:
            self.address.setText("")
            self.formula.setText("")
            self.formula.setReadOnly(True)
            return
        self.address.setText("{}{}".format(table_sheet.col_letter(c), r + 1))
        self.formula.setText(item.data(RAW) or item.text())
        zone = (self._geom.zone_of(r) or ("D",))[0] if self._geom is not None else "D"
        self.formula.setReadOnly(zone == "D" and item.data(ACTION) is None)

    def _formula_entered(self):
        r, c = self.table.currentRow(), self.table.currentColumn()
        item = self.table.item(r, c) if r >= 0 and c >= 0 else None
        if item is None or self._geom is None:
            return
        text = self.formula.text()
        if text == (item.data(RAW) or item.text()):
            return                                       # (nothing new: no undo step)
        if (self._geom.zone_of(r) or ("D",))[0] == "D":
            if item.data(ACTION) is not None:
                item.setText(text)                       # (an element's value: the model's, as typed in the cell)
            else:
                self._say(t("grid.no_model_cell"))
            return
        self._later(self.write, r, c, text)

    # ------------------------------------------------------------ user actions

    def _changed(self, item):
        if self._filling:
            return
        place = item.data(PLACE)
        if place is not None and self._geom is not None and (self._geom.zone_of(place[0]) or ("D",))[0] != "D":
            if item.text() != (item.data(RAW) or ""):    # (0.478) a title, a note, a heading, a total written
                self._later(self.write, place[0], place[1], item.text())
            else:
                self._later(self.refresh)                # (nothing new: shown as it was — a heading's name back)
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
        if self._filling or (self.grouped.isChecked() and not self._in_grid):
            return
        ids = list(dict.fromkeys(i.data(GUID) for i in self.table.selectedItems() if i.data(GUID) is not None))
        if self._in_grid and not ids:
            return                                  # (0.478: a title, a note… chosen — the model's choice kept)
        self._later(self.on_select, ids)

    def _double_clicked(self, item):
        if item.data(ACTION) is None and item.data(GUID) is not None:
            self._later(self.on_frame, [item.data(GUID)])

    def _export(self):
        """The table as shown (its values as numbers, for Excel); (0.478) a table of the project's with its grid (its
        titles, notes, merges, formats and formulas)."""
        if self._in_grid and self._grid is not None:
            header = [cell.text for cell in self._grid[self._geom.top]]      # (the headings as shown: renamed too)
            grid = (self._grid, self._geom, self._layout, list(self._columns))
        else:
            header = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
            grid = None
        if self.on_export is not None:
            self.on_export(header, list(getattr(self, "_export_rows", [])), columns=list(self._columns), grid=grid)


def dock(parent):
    """(0.477) The table's page, hidden until a table's tab is chosen (the window puts it in place of the canvas)."""
    panel = SchedulesPanel(parent)
    panel.hide()
    return panel
