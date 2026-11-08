"""(0.357) The Programme panel (programa de necessidades): the rooms the project asks for (model/room_program.py) —
each its name, the area wanted, how many, interior or exterior — and beside it how many are made and their area; a
name dragged from it onto the plan makes that room in the space dropped on (or names the room there). Imported from a
file (CSV / TXT); kept in the IFC. The owner, 2026-11-02: «Deve ser capaz de carregar um ficheiro com programas de
projetos onde já cria a lista dos ambientes. O utilizador pode simplesmente pegar e arrastar o nome para dentro do
ambiente para inserir».

(0.475, the owner: «A aba ambiente quero que funcione no painel lateral… o painel vai ser um gestor de programa de
necessidade») The side panel of the «Ambientes» module: the type of building, the storey shown, the list of that
storey's rooms — each its use, the area wanted and the one made —, a line coloured by how it stands: green (placed,
as large as wanted), orange (placed, short: to look at), red (it opens into a room of a use it should not: «zonas
conflitantes», said under the list and in the footer). A line clicked: the Room-from-the-programme tool places it with
a click in the plan (tools/room_need.py); dragged: dropped on the room. Lines added, edited (name, use, area, how many,
storey, exterior) and deleted here — each change one undo step —; imported from a file (CSV, TXT or JSON: a list an AI
made — «Pedir à IA…» copies the request to paste in it)."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import decimal_sep, lang, t
from ..model import program_rules, room_program
from . import theme

MIME = "application/x-arqsynth-room"     # what a dragged name carries: JSON of the need
ALL = "*"                                 # the storey choice: every storey's lines


def _area(value):
    """«40 m²», «22,04 m²» (no decimals when there are none: the column is narrow), «—» for none."""
    if not value:
        return "—"
    text = "{:.2f}".format(value)
    text = text[:-3] if text.endswith(".00") else text
    return text.replace(".", decimal_sep()) + " m²"


def _dot(colour):
    pix = QtGui.QPixmap(12, 12)
    pix.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pix)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(colour)
    p.drawEllipse(QtCore.QRectF(1, 1, 10, 10))
    p.end()
    return QtGui.QIcon(pix)


def status_colour(status):
    """The colour a line stands in: "ok" green, "short" orange, "conflict" red, "todo" the text's."""
    return {"ok": theme.colour("ok"), "short": theme.colour("attention"), "conflict": theme.colour("warning")}.get(
        status, theme.colour("text"))


class _List(QtWidgets.QTreeWidget):
    """The needs, dragged by their name (the need as JSON under MIME, its name as text)."""

    def __init__(self, panel):
        super().__init__()
        self.panel = panel
        self.setColumnCount(3)                      # (its use in its tip and under the list: the column is narrow)
        self.setHeaderLabels([t("program.col.name"), t("program.col.area_short"), t("program.col.made_area")])
        self.setRootIsDecorated(False)
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragOnly)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setMinimumWidth(150)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        for col in (1, 2):
            self.header().setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    def mimeData(self, items):
        data = QtCore.QMimeData()
        if items:
            need = items[0].data(0, QtCore.Qt.ItemDataRole.UserRole)
            data.setData(MIME, QtCore.QByteArray(room_program.to_text([need]).encode("utf-8")))
            data.setText(need.name)
        return data


class ProgramPanel(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__(t("program.title"), parent)
        self.setObjectName("room_program")
        self.on_import = None            # callable(): a file chosen and read (the window's)
        self.on_clear = None             # callable(): the programme emptied
        self.on_change = None            # (0.475) callable(needs, building): the programme changed here
        self.on_place = None             # (0.475) callable(need): a line clicked — placed with a click in the plan
        self.on_storey = None            # (0.475) callable(storey GlobalId): another storey chosen here
        self.on_ai = None                # (0.475) callable(): the request for an AI copied
        self.needs, self.building = [], program_rules.DEFAULT_TYPE
        self.storeys = []                # [(GlobalId, name, level)]
        self.states = {}                 # need uid -> room_program.State
        self.red = set()                 # need uids in a conflict
        self._quiet = False
        page = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(page)
        column.setContentsMargins(4, 4, 4, 4)
        self.hint = QtWidgets.QLabel(t("program.hint"))
        self.hint.setWordWrap(True)
        column.addWidget(self.hint)
        form = QtWidgets.QFormLayout()
        self.type_box = QtWidgets.QComboBox()
        language = lang()
        for key in program_rules.BUILDING_TYPES:
            self.type_box.addItem(program_rules.type_label(key, language), key)
        self.type_box.activated.connect(lambda _i: self._type_chosen())
        self.storey_box = QtWidgets.QComboBox()
        self.storey_box.activated.connect(lambda _i: self._storey_chosen())
        form.addRow(t("program.building") + ":", self.type_box)
        form.addRow(t("program.storey") + ":", self.storey_box)
        column.addLayout(form)
        self.list = _List(self)
        self.list.itemClicked.connect(lambda item, _c: self._clicked(item))
        self.list.currentItemChanged.connect(lambda item, _old: self._show_line(item))
        column.addWidget(self.list, 1)
        self.conflicts = QtWidgets.QLabel("")
        self.conflicts.setWordWrap(True)
        self.conflicts.hide()
        column.addWidget(self.conflicts)
        self.totals = QtWidgets.QLabel("")
        self.totals.setWordWrap(True)
        column.addWidget(self.totals)

        # the line chosen: its name, use, area wanted, how many, storey, exterior
        self.editor = QtWidgets.QGroupBox(t("program.line"))
        edit = QtWidgets.QFormLayout(self.editor)
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.editingFinished.connect(lambda: self._edited("name"))
        self.use_box = QtWidgets.QComboBox()
        self.use_box.activated.connect(lambda _i: self._edited("use"))
        self.area_edit = QtWidgets.QLineEdit()
        self.area_edit.setPlaceholderText(t("program.area_optional"))
        self.area_edit.editingFinished.connect(lambda: self._edited("area"))
        self.count_box = QtWidgets.QSpinBox()
        self.count_box.setRange(1, 999)
        self.count_box.editingFinished.connect(lambda: self._edited("count"))
        self.line_storey = QtWidgets.QComboBox()
        self.line_storey.activated.connect(lambda _i: self._edited("storey"))
        self.external_box = QtWidgets.QCheckBox(t("program.external"))
        self.external_box.toggled.connect(lambda _on: self._edited("external"))
        edit.addRow(t("program.col.name") + ":", self.name_edit)
        edit.addRow(t("program.col.use") + ":", self.use_box)
        edit.addRow(t("program.col.area") + ":", self.area_edit)
        edit.addRow(t("program.count") + ":", self.count_box)
        edit.addRow(t("program.storey") + ":", self.line_storey)
        edit.addRow(self.external_box)                   # (the whole row: the column is narrow)
        self.external_box.setToolTip(t("program.external_tip"))
        column.addWidget(self.editor)

        self.add_button = QtWidgets.QPushButton(t("program.add"))
        self.add_button.setToolTip(t("program.add_tip"))
        self.add_button.clicked.connect(self.add_line)
        self.delete_button = QtWidgets.QPushButton(t("program.delete"))
        self.delete_button.clicked.connect(self.delete_line)
        self.clear_button = QtWidgets.QPushButton(t("program.clear"))
        self.clear_button.clicked.connect(lambda: self.on_clear() if self.on_clear else None)
        self.import_button = QtWidgets.QPushButton(t("program.import"))
        self.import_button.setToolTip(t("program.import_tip"))
        self.import_button.clicked.connect(lambda: self.on_import() if self.on_import else None)
        self.ai_button = QtWidgets.QPushButton(t("program.ai"))
        self.ai_button.setToolTip(t("program.ai_tip"))
        self.ai_button.clicked.connect(lambda: self.on_ai() if self.on_ai else None)
        buttons = QtWidgets.QGridLayout()                # (two a row: the column is narrow)
        for k, b in enumerate((self.add_button, self.delete_button, self.import_button, self.ai_button,
                               self.clear_button)):
            b.setMinimumWidth(40)
            b.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
            buttons.addWidget(b, k // 2, k % 2)
        column.addLayout(buttons)
        for box in (self.type_box, self.storey_box, self.use_box, self.line_storey):   # (as narrow as the column)
            box.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            box.setMinimumContentsLength(5)
        for f in (form, edit):                           # (a narrow column: the name over its field)
            f.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)
        for w in (self.name_edit, self.area_edit):
            w.setMinimumWidth(60)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(page)
        self.setWidget(scroll)
        self.restyle()
        self._show_line(None)

    def restyle(self):
        self.hint.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        self.conflicts.setStyleSheet("QLabel { color: %s; font-weight: 600; }" % theme.C["warning"])
        if self.needs or self.states:
            self._fill()

    # ------------------------------------------------------------ what is shown

    def shown_storey(self):
        """The storey whose lines are listed (a GlobalId), or ALL."""
        return self.storey_box.currentData() or ALL

    def show_program(self, needs, spaces=None, building=None, states=None, conflicts=(), storeys=(), active=None):
        """The needs (and, 0.475, the type of building, each need's room_program.State, the conflicts
        [(room, room, door, rule)], the project's storeys [(GlobalId, name, level)] and the active one: listed)."""
        self.needs = list(needs)
        self.building = building or program_rules.DEFAULT_TYPE
        self.storeys = list(storeys)
        if states is None:
            states = room_program.states(self.needs, spaces or [], {}, self.storeys)
        self.states = {s.need.uid: s for s in states}
        in_conflict = {g for a, b, _d, _r in conflicts for g in (a, b)}
        self.red = {s.need.uid for s in states if in_conflict & set(s.rooms)}
        self._conflict_lines = []
        names = {}
        for s in states:
            for g in s.rooms:
                names[g] = s.need.name
        language = lang()
        for a, b, _door, rule in conflicts:
            self._conflict_lines.append(t("program.conflict_line", a=names.get(a) or program_rules.use_label(
                rule[0], language), b=names.get(b) or program_rules.use_label(rule[1], language), why=rule[2]))
        self._quiet = True
        try:
            self.type_box.setCurrentIndex(max(0, self.type_box.findData(self.building)))
            chosen = self.storey_box.currentData()
            if chosen is None or (chosen != ALL and chosen not in {g for g, _n, _z in self.storeys}):
                chosen = active if active else ALL
            self._fill_storeys(self.storey_box, chosen, everyone=True)
        finally:
            self._quiet = False
        self._fill()

    def follow_storey(self, guid):
        """(The active storey changed elsewhere: its lines shown, unless every storey's are.)"""
        if guid and self.storey_box.currentData() not in (ALL, guid):
            self._quiet = True
            self.storey_box.setCurrentIndex(max(0, self.storey_box.findData(guid)))
            self._quiet = False
            self._fill()

    def _fill_storeys(self, box, chosen, everyone=False):
        box.clear()
        if everyone:
            box.addItem(t("program.all_storeys"), ALL)
        else:
            box.addItem(t("program.any_storey"), "")
        for guid, name, _z in sorted(self.storeys, key=lambda s: -s[2]):
            box.addItem(name, guid)
        box.setCurrentIndex(max(0, box.findData(chosen)))

    def _visible(self, need):
        shown = self.shown_storey()
        if shown == ALL:
            return True
        found = room_program.storey_of(need, self.storeys)
        return found is None or found == shown

    def _fill(self):
        keep = self.current_need()
        self.list.blockSignals(True)
        self.list.clear()
        language = lang()
        chosen = None
        wanted = made_area = 0.0
        done = 0
        listed = 0
        for need in self.needs:
            if not self._visible(need):
                continue
            listed += 1
            state = self.states.get(need.uid)
            status = "conflict" if need.uid in self.red else (state.status if state else "todo")
            made = state.made if state else 0
            area = state.area if state else 0.0
            label = need.name if need.count == 1 else "{} ×{}".format(need.name, need.count)
            if need.external:
                label += " ({})".format(t("props.room_exterior_short"))
            if room_program.storey_of(need, self.storeys) is None and need.storey and self.shown_storey() != ALL:
                label += "  [{}]".format(need.storey)
            item = QtWidgets.QTreeWidgetItem([label, _area(need.area * need.count if need.area else 0.0),
                                              _area(area) if need.count == 1 else "{}/{} · {}".format(
                                                  made, need.count, _area(area))])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, need)
            item.setData(1, QtCore.Qt.ItemDataRole.UserRole, status)
            colour = status_colour(status)
            item.setIcon(0, _dot(colour if status != "todo" else theme.colour("note")))
            if status != "todo":
                for col in range(3):
                    item.setForeground(col, QtGui.QBrush(colour))
            tip = "{}{}\n{}\n{}".format(need.name, " — " + program_rules.use_label(need.use, language) if need.use
                                        else "", t("program.status." + status, name=need.name),
                                        t("program.drag_tip", name=need.name))
            for col in range(3):
                item.setToolTip(col, tip)
            self.list.addTopLevelItem(item)
            if keep is not None and need.uid == keep.uid:
                chosen = item
            wanted += need.area * need.count
            made_area += area
            done += status == "ok"
        self.list.blockSignals(False)
        if chosen is not None:
            self.list.setCurrentItem(chosen)
        self._show_line(self.list.currentItem())
        self.totals.setText(t("program.totals", n=listed, done=done, a=_area(wanted), m=_area(made_area))
                            if listed else t("program.empty"))
        lines = getattr(self, "_conflict_lines", [])
        self.conflicts.setText("⚠ " + t("program.conflicts", n=len(lines)) + "\n" + "\n".join(lines[:6])
                               if lines else "")
        self.conflicts.setVisible(bool(lines))
        self.clear_button.setEnabled(bool(self.needs))

    def text(self):
        """(tests) The lines shown, each «name | use | wanted | made | status»."""
        out = []
        for k in range(self.list.topLevelItemCount()):
            item = self.list.topLevelItem(k)
            out.append(" | ".join([item.text(c) for c in range(3)] + [item.data(1, QtCore.Qt.ItemDataRole.UserRole)]))
        return "\n".join(out)

    def status_of(self, name):
        """(tests) How a line of this name stands ("todo", "ok", "short", "conflict"), or None."""
        for k in range(self.list.topLevelItemCount()):
            item = self.list.topLevelItem(k)
            if item.data(0, QtCore.Qt.ItemDataRole.UserRole).name == name:
                return item.data(1, QtCore.Qt.ItemDataRole.UserRole)
        return None

    # ------------------------------------------------------------ the line chosen

    def current_need(self):
        item = self.list.currentItem()
        return item.data(0, QtCore.Qt.ItemDataRole.UserRole) if item is not None else None

    def select(self, name):
        """(tests) The line of this name chosen (as a click on it: placed next with a click in the plan)."""
        for k in range(self.list.topLevelItemCount()):
            item = self.list.topLevelItem(k)
            if item.data(0, QtCore.Qt.ItemDataRole.UserRole).name == name:
                self.list.setCurrentItem(item)
                self._clicked(item)
                return item
        return None

    def _clicked(self, item):
        need = item.data(0, QtCore.Qt.ItemDataRole.UserRole) if item is not None else None
        if need is not None and self.on_place is not None:
            self.on_place(need)

    def _show_line(self, item):
        need = item.data(0, QtCore.Qt.ItemDataRole.UserRole) if item is not None else None
        self._quiet = True
        try:
            self.editor.setEnabled(need is not None)
            self.delete_button.setEnabled(need is not None)
            self.name_edit.setText(need.name if need else "")
            self.use_box.clear()
            self.use_box.addItem("—", "")
            language = lang()
            uses = program_rules.uses_for(self.building)
            if need is not None and need.use and need.use not in uses:
                uses.append(need.use)
            for key in sorted(uses, key=lambda k: program_rules.use_label(k, language).lower()):
                self.use_box.addItem(program_rules.use_label(key, language), key)
            self.use_box.setCurrentIndex(max(0, self.use_box.findData(need.use if need else "")))
            self.area_edit.setText("{:g}".format(need.area).replace(".", decimal_sep()) if need and need.area else "")
            self.count_box.setValue(need.count if need else 1)
            self._fill_storeys(self.line_storey, room_program.storey_of(need, self.storeys) or
                               (need.storey if need else ""))
            if need is not None and need.storey and self.line_storey.findData(need.storey) < 0 and \
                    room_program.storey_of(need, self.storeys) is None:
                self.line_storey.addItem(need.storey, need.storey)          # (a storey not made yet: its name)
                self.line_storey.setCurrentIndex(self.line_storey.count() - 1)
            self.external_box.setChecked(bool(need.external) if need else False)
        finally:
            self._quiet = False

    def _edited(self, what):
        if self._quiet:
            return
        need = self.current_need()
        if need is None:
            return
        changed = room_program.Need(need.name, need.area, need.count, need.external, need.use, need.storey, need.uid)
        if what == "name":
            text = self.name_edit.text().strip()
            if not text:
                self.name_edit.setText(need.name)
                return
            changed.name = text
        elif what == "use":
            changed.use = self.use_box.currentData() or ""
        elif what == "area":
            value = room_program._number(self.area_edit.text())
            changed.area = max(0.0, float(value or 0.0))
        elif what == "count":
            changed.count = int(self.count_box.value())
        elif what == "storey":
            changed.storey = self.line_storey.currentData() or ""
        elif what == "external":
            changed.external = self.external_box.isChecked()
        if changed == need:
            return
        self._commit([changed if n.uid == need.uid else n for n in self.needs], keep=changed.uid)

    def add_line(self):
        """«+ Ambiente»: a new line on the storey shown (any, when every one is), chosen to be named."""
        shown = self.shown_storey()
        need = room_program.Need(t("program.new_name"), storey="" if shown == ALL else shown)
        self._commit(self.needs + [need], keep=need.uid)
        self.name_edit.setFocus()
        self.name_edit.selectAll()
        return need

    def delete_line(self):
        need = self.current_need()
        if need is not None:
            self._commit([n for n in self.needs if n.uid != need.uid])

    def _commit(self, needs, keep=None):
        self.needs = list(needs)
        if keep is not None:
            self._keep_uid = keep
        if self.on_change is not None:
            self.on_change(self.needs, self.building)
        if keep is not None:
            for k in range(self.list.topLevelItemCount()):
                item = self.list.topLevelItem(k)
                if item.data(0, QtCore.Qt.ItemDataRole.UserRole).uid == keep:
                    self.list.setCurrentItem(item)
                    break

    def _type_chosen(self):
        if self._quiet:
            return
        building = self.type_box.currentData()
        if building and building != self.building:
            self.building = building
            if self.on_change is not None:
                self.on_change(self.needs, building)
            self._show_line(self.list.currentItem())

    def _storey_chosen(self):
        if self._quiet:
            return
        guid = self.storey_box.currentData()
        self._fill()
        if guid and guid != ALL and self.on_storey is not None:
            self.on_storey(guid)


def dock(parent, beside):
    """The panel as a tab next to `beside` (the Project panel), hidden until asked for."""
    panel = ProgramPanel(parent)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, panel)
    parent.tabifyDockWidget(beside, panel)
    panel.hide()
    return panel
