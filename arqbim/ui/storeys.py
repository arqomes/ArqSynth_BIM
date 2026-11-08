"""Storeys panel ("Pavimentos"): the building's levels, highest at the top as in
a section; the one being drawn on is in bold. Click = draw on it; double-click
the name or the level to change it; "+ New" adds one 3 m above the highest.

Edits are reported through callbacks; the main window turns them into
undoable commands. They run once the Qt signal has returned, because applying
an edit rebuilds this list (and deletes the item that sent the signal).
"""

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.units import format_length, parse_length
from ..i18n import decimal_sep, t

GUID = QtCore.Qt.ItemDataRole.UserRole
# (0.462) the levels' colours offered: the drawing's ink, a few, any other (picked)
LEVEL_COLOURS = (("auto", ""), ("black", "#000000"), ("blue", "#3a6fb5"), ("red", "#d23c3c"), ("green", "#2e9e4f"),
                 ("grey", "#7a7a7a"), ("other", "?"))


class LevelPreview(QtWidgets.QWidget):
    """(0.462) A level as its style draws it, on paper (ui/symbol_styles_dialog.draw_level)."""

    def __init__(self):
        super().__init__()
        self.style = None
        self.setMinimumHeight(64)

    def show_style(self, style):
        self.style = dict(style)
        self.update()

    def paintEvent(self, _event):
        if not self.style:
            return
        from .symbol_styles_dialog import draw_level
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QtGui.QColor("#ffffff"))
        draw_level(p, self.style, self.width(), self.height(), min(self.width() / 70.0, self.height() / 14.0))
        p.end()


def level_text(z):
    return ("+" if z > 1e-9 else "") + format_length(z, decimal_sep(), unit="m").replace("~ ", "")   # (levels: m)


class StoreysPanel(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__(t("storeys.title"), parent)
        self.setObjectName("storeys")
        body = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(body)
        layout.setContentsMargins(4, 4, 4, 4)
        self.table = QtWidgets.QTreeWidget()
        self.table.setColumnCount(3)
        self.table.setHeaderLabels([t("storeys.name"), t("storeys.level"), "="])
        self.table.headerItem().setToolTip(2, t("storeys.typical_tip"))
        self.table.setRootIsDecorated(False)
        # (0.463, the owner: «Se quiser selecionar um grupo de nível e igualar») several picked (Ctrl, Shift): «Igualar»
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked
                                   | QtWidgets.QAbstractItemView.EditTrigger.EditKeyPressed)
        self.table.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.setMaximumHeight(130)
        layout.addWidget(self.table)
        buttons = QtWidgets.QHBoxLayout()
        self.btn_new = QtWidgets.QPushButton(t("storeys.new"))
        self.btn_delete = QtWidgets.QPushButton(t("storeys.delete"))
        self.btn_typical = QtWidgets.QPushButton(t("storeys.typical"))      # (typical floors, 0.90)
        self.btn_typical.setToolTip(t("storeys.typical_tip"))
        buttons.addWidget(self.btn_new)
        buttons.addWidget(self.btn_delete)
        buttons.addWidget(self.btn_typical)
        # (0.465, the owner: «O botão = deve ligável e desligavel. Só faz o efeito quando o botão está ligado») the
        # typical floors' replication on / off
        self.btn_live = QtWidgets.QToolButton()
        self.btn_live.setText("=")
        self.btn_live.setCheckable(True)
        self.btn_live.setChecked(True)
        self.btn_live.setToolTip(t("storeys.live_tip"))
        font = self.btn_live.font()
        font.setBold(True)
        font.setPointSizeF(font.pointSizeF() * 1.3)
        self.btn_live.setFont(font)
        self.btn_live.setMinimumWidth(30)
        buttons.addWidget(self.btn_live)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.only_active = QtWidgets.QCheckBox(t("storeys.only_active"))     # (0.465: «No 3D, …»)
        self.only_active.setToolTip(t("tip.only_active"))
        layout.addWidget(self.only_active)
        layout.addWidget(self._look_box())                 # (0.462) the levels' look
        layout.addStretch(1)
        self.setWidget(body)

        # callbacks set by the main window
        self.on_activate = None      # (guid)
        self.on_rename = None        # (guid, name)
        self.on_level = None         # (guid, meters)
        self.on_new = None           # ()
        self.on_delete = None        # (guid)
        self.on_only_active = None   # (bool)
        self.on_typical = None       # () the active storey: made equal to others, or no longer (0.90)
        self.on_level_style = None   # (dict) the levels' look changed (0.462): their style's fields
        self.on_typical_live = None  # (bool) the typical floors' replication switched on / off (0.465, «=»)

        self._levels = {}
        self._filling = False
        self._picked = set()         # (0.463) the storeys picked in the list (kept as it is made again)
        self._active, self._typical = None, {}
        self.table.itemClicked.connect(self._clicked)
        self.table.itemChanged.connect(self._changed)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.btn_new.clicked.connect(lambda: self._later(self.on_new))
        self.btn_delete.clicked.connect(self._delete)
        self.btn_typical.clicked.connect(lambda: self._later(self.on_typical, sorted(self._picked)))
        self.btn_live.toggled.connect(lambda on: self._later(self.on_typical_live, on))
        self.only_active.toggled.connect(lambda on: self._later(self.on_only_active, on))

    @staticmethod
    def _later(fn, *args):
        if fn is not None:
            QtCore.QTimer.singleShot(0, lambda: fn(*args))

    # ------------------------------------------------------------ (0.462) the levels' look

    def _look_box(self):
        """(0.462, the owner: «A REPRESENTAÇÃO, OU APARÊNCIA ESSES ELEMENTOS DEVER SER CONFIGURADOS NESSA ABA. A LINHA E A
        EXTREMIDADE») The levels' look — their line, colour, end, at which end, their words, and whether 3D shows them —
        each change drawn at once in the sections, elevations, sheets and 3D (one undo step each)."""
        from ..model import graphic_styles as styles_model
        self._look_filling = False
        self._look = styles_model.symbol(None, "level")
        box = QtWidgets.QGroupBox(t("storeys.look"))
        box.setToolTip(t("storeys.look_tip"))
        form = QtWidgets.QFormLayout(box)
        form.setContentsMargins(6, 6, 6, 6)
        self.look_preview = LevelPreview()
        form.addRow(self.look_preview)

        from . import level_icons                         # (0.465, the owner: «opções visuais em vez de texto»)

        def choice(key, label):
            icon_of, size = level_icons.ICONS[key]
            row = level_icons.IconChoice(icon_of, size)
            for value in styles_model.SYMBOL_CHOICES[key]:
                row.addItem(t("symbols.{}.{}".format(key, value)), value)
            row.currentIndexChanged.connect(lambda _i: self._look_changed())
            form.addRow(t(label), row)
            return row
        self.look_line = choice("line", "storeys.look_line")
        self.look_colour = level_icons.IconChoice(level_icons.colour_icon,
                                                  (level_icons.SWATCH + 4, level_icons.SWATCH + 4))
        for key, value in LEVEL_COLOURS:
            self.look_colour.addItem(t("storeys.colour." + key), value)
        self.look_colour.currentIndexChanged.connect(lambda _i: self._colour_chosen())
        form.addRow(t("storeys.look_colour"), self.look_colour)
        self.look_mark = choice("mark", "storeys.look_mark")
        self.look_ends = choice("ends", "storeys.look_ends")
        self.look_label = choice("label", "storeys.look_label")
        self.look_over = QtWidgets.QCheckBox(t("storeys.look_over"))          # (0.464) or its sides only
        self.look_over.setToolTip(t("storeys.look_over_tip"))
        self.look_over.toggled.connect(lambda _on: self._look_changed())
        form.addRow(self.look_over)
        self.look_3d = QtWidgets.QCheckBox(t("storeys.look_3d"))
        self.look_3d.toggled.connect(lambda _on: self._look_changed())
        form.addRow(self.look_3d)
        self.show_level_style(self._look)
        return box

    def _colour_chosen(self):
        """«Other…»: a colour picked; the others are what they say."""
        if self._look_filling:
            return
        value = self.look_colour.currentData()
        if value == "?":
            picked = QtWidgets.QColorDialog.getColor(QtGui.QColor(self._look.get("colour") or "#000000"), self,
                                                     t("storeys.look_colour"))
            if not picked.isValid():
                self.show_level_style(self._look)
                return
            self._set_colour(picked.name())
        self._look_changed()

    def _set_colour(self, value):
        """The colour list showing `value` ("" automatic) — added to the list when it is none of its own."""
        k = self.look_colour.findData(value)
        if k < 0:
            self.look_colour.insertItem(self.look_colour.count() - 1, value, value)
            k = self.look_colour.findData(value)
        self.look_colour.blockSignals(True)
        self.look_colour.setCurrentIndex(k)
        self.look_colour.blockSignals(False)

    def level_style(self):
        """The levels' style as the panel shows it (their fields)."""
        colour = self.look_colour.currentData()
        return dict(self._look, line=self.look_line.currentData(), mark=self.look_mark.currentData(),
                    ends=self.look_ends.currentData(), label=self.look_label.currentData(),
                    colour=colour if colour != "?" else self._look.get("colour", ""), in_3d=self.look_3d.isChecked(),
                    over=self.look_over.isChecked())

    def show_level_style(self, style):
        """The levels' style (graphic_styles.symbol(…, "level")) shown, nothing sent back."""
        self._look_filling = True
        try:
            self._look = dict(style)
            for row in (self.look_line, self.look_mark, self.look_ends, self.look_label):
                if hasattr(row, "refresh"):
                    row.refresh()                          # (0.465: the theme's ink)
            for combo, key in ((self.look_line, "line"), (self.look_mark, "mark"), (self.look_ends, "ends"),
                               (self.look_label, "label")):
                combo.blockSignals(True)
                combo.setCurrentIndex(max(0, combo.findData(style.get(key))))
                combo.blockSignals(False)
            self._set_colour(style.get("colour") or "")
            for box, key in ((self.look_3d, "in_3d"), (self.look_over, "over")):
                box.blockSignals(True)
                box.setChecked(bool(style.get(key, True)))
                box.blockSignals(False)
            self.look_preview.show_style(self._look)
        finally:
            self._look_filling = False

    def _look_changed(self):
        if self._look_filling:
            return
        style = self.level_style()
        self.look_preview.show_style(style)
        self._later(self.on_level_style, style)

    # ------------------------------------------------------------ content

    def show_storeys(self, levels, active, typical=None, live=True):
        """levels: [(guid, name, level m)] lowest first; active: guid drawn on; typical: {guid: the letter of
        its set of equal storeys} (0.90: "=A" in the third column); live (0.465): their replication on («=» pressed;
        off: their letters greyed)."""
        typical = typical or {}
        self.btn_live.blockSignals(True)
        self.btn_live.setChecked(bool(live))
        self.btn_live.blockSignals(False)
        self._filling = True
        self.table.blockSignals(True)
        self.table.clear()
        self._levels = {g: (name, z) for g, name, z in levels}
        self._active, self._typical = active, dict(typical)
        picked = {g for g in self._picked if g in self._levels}
        self._picked = picked if len(picked) >= 2 else ({active} if active else set())     # (one: the active one)
        for guid, name, z in reversed(levels):
            item = QtWidgets.QTreeWidgetItem([name, level_text(z), "=" + typical[guid] if guid in typical else ""])
            item.setData(0, GUID, guid)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(1, QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            if guid == active:
                for col in (0, 1):
                    font = item.font(col)
                    font.setBold(True)
                    item.setFont(col, font)
            if guid in typical and not live:                # (0.465: «=» off — its mark greyed)
                item.setForeground(2, QtGui.QBrush(QtGui.QColor("#9a9a9a")))
                item.setToolTip(2, t("storeys.live_off_tip"))
            self.table.addTopLevelItem(item)
            if guid == active:
                self.table.setCurrentItem(item)
        for i in range(self.table.topLevelItemCount()):   # (0.463: those picked stay picked)
            item = self.table.topLevelItem(i)
            item.setSelected(item.data(0, GUID) in self._picked)
        self.table.blockSignals(False)
        self.btn_delete.setEnabled(len(levels) > 1)
        self._typical_button()
        self.btn_typical.setEnabled(len(levels) > 1)
        self._filling = False

    def _typical_button(self):
        """(0.463) «Separar» on a typical storey; «Igualar (n)» with several picked; else «Iguais…» (the dialog)."""
        if self._active in self._typical:
            self.btn_typical.setText(t("storeys.untypical"))
        elif len(self._picked) >= 2:
            self.btn_typical.setText(t("storeys.typical_n", n=len(self._picked)))
        else:
            self.btn_typical.setText(t("storeys.typical"))

    def _selection_changed(self):
        if self._filling:
            return
        self._picked = {item.data(0, GUID) for item in self.table.selectedItems()}
        self._typical_button()

    def item_for(self, guid):
        for i in range(self.table.topLevelItemCount()):
            item = self.table.topLevelItem(i)
            if item.data(0, GUID) == guid:
                return item
        return None

    def text(self):
        """Rows as plain text (used by tests): 'name | level' per storey, active one marked with *."""
        rows = []
        for i in range(self.table.topLevelItemCount()):
            item = self.table.topLevelItem(i)
            rows.append("{}{} | {}".format("*" if item.font(0).bold() else "", item.text(0), item.text(1)))
        return "\n".join(rows)

    # ------------------------------------------------------------ user actions

    def _clicked(self, item, _column):
        self._later(self.on_activate, item.data(0, GUID))

    def _changed(self, item, column):
        if self._filling:
            return
        guid = item.data(0, GUID)
        name, z = self._levels.get(guid, ("", 0.0))
        text = item.text(column).strip()
        if column == 0:
            if text and text != name:
                self._later(self.on_rename, guid, text)
            else:
                self._restore(item, 0, name)
        elif column == 2:                         # (the typical-floor mark is not typed)
            self._later(self.on_activate, guid)
        else:
            value = parse_length(text.replace("+", ""), unit="m")
            if value is None:
                self._restore(item, 1, level_text(z))
            elif abs(value - z) > 1e-9:
                self._later(self.on_level, guid, value)
            else:
                self._restore(item, 1, level_text(z))

    def _restore(self, item, column, text):
        self._filling = True
        item.setText(column, text)
        self._filling = False

    def _delete(self):
        item = self.table.currentItem()
        if item is not None:
            self._later(self.on_delete, item.data(0, GUID))


class TypicalDialog(QtWidgets.QDialog):
    """Typical floors (0.90): which storeys are to be equal to the active one (its elements copied to them),
    and the floor's name."""

    def __init__(self, parent, levels, active):
        super().__init__(parent)
        from .selection_dialogs import CheckList
        self.setWindowTitle(t("typical.title"))
        layout = QtWidgets.QVBoxLayout(self)
        name = dict((g, n) for g, n, _z in levels).get(active, "")
        note = QtWidgets.QLabel(t("typical.note", name=name))
        note.setWordWrap(True)
        layout.addWidget(note)
        self.list = CheckList()
        self.list.fill([("{}  ({})".format(n, level_text(z)), g, False) for g, n, z in reversed(levels) if g != active])
        layout.addWidget(self.list, 1)
        form = QtWidgets.QFormLayout()
        self.name = QtWidgets.QLineEdit(t("typical.default_name"))
        form.addRow(t("typical.name"), self.name)
        layout.addLayout(form)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.resize(420, 360)


def dock(parent, below=None):
    """The panel in the right dock area, above `below` (the Properties panel)."""
    panel = StoreysPanel(parent)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, panel)
    if below is not None:
        parent.splitDockWidget(panel, below, QtCore.Qt.Orientation.Vertical)
        parent.resizeDocks([panel, below], [230, 600], QtCore.Qt.Orientation.Vertical)   # most room to Properties
    return panel
