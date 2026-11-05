"""Storeys panel ("Pavimentos"): the building's levels, highest at the top as in
a section; the one being drawn on is in bold. Click = draw on it; double-click
the name or the level to change it; "+ New" adds one 3 m above the highest.

Edits are reported through callbacks; the main window turns them into
undoable commands. They run once the Qt signal has returned, because applying
an edit rebuilds this list (and deletes the item that sent the signal).
"""

from PySide6 import QtCore, QtWidgets

from ..core.units import format_length, parse_length
from ..i18n import decimal_sep, t

GUID = QtCore.Qt.ItemDataRole.UserRole


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
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.only_active = QtWidgets.QCheckBox(t("storeys.only_active"))
        layout.addWidget(self.only_active)
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

        self._levels = {}
        self._filling = False
        self.table.itemClicked.connect(self._clicked)
        self.table.itemChanged.connect(self._changed)
        self.btn_new.clicked.connect(lambda: self._later(self.on_new))
        self.btn_delete.clicked.connect(self._delete)
        self.btn_typical.clicked.connect(lambda: self._later(self.on_typical))
        self.only_active.toggled.connect(lambda on: self._later(self.on_only_active, on))

    @staticmethod
    def _later(fn, *args):
        if fn is not None:
            QtCore.QTimer.singleShot(0, lambda: fn(*args))

    # ------------------------------------------------------------ content

    def show_storeys(self, levels, active, typical=None):
        """levels: [(guid, name, level m)] lowest first; active: guid drawn on; typical: {guid: the letter of
        its set of equal storeys} (0.90: "=A" in the third column)."""
        typical = typical or {}
        self._filling = True
        self.table.clear()
        self._levels = {g: (name, z) for g, name, z in levels}
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
            self.table.addTopLevelItem(item)
            if guid == active:
                self.table.setCurrentItem(item)
        self.btn_delete.setEnabled(len(levels) > 1)
        self.btn_typical.setText(t("storeys.untypical" if active in typical else "storeys.typical"))
        self.btn_typical.setEnabled(len(levels) > 1)
        self._filling = False

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
