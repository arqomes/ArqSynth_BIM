"""(0.357) The Programme panel (programa de necessidades): the rooms the project asks for (model/room_program.py) —
each its name, the area wanted, how many, interior or exterior — and beside it how many are made and their area; a
name dragged from it onto the plan makes that room in the space dropped on (or names the room there). Imported from a
file (CSV / TXT); kept in the IFC. The owner, 2026-11-02: «Deve ser capaz de carregar um ficheiro com programas de
projetos onde já cria a lista dos ambientes. O utilizador pode simplesmente pegar e arrastar o nome para dentro do
ambiente para inserir»."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import decimal_sep, t
from ..model import room_program
from . import theme

MIME = "application/x-arqsynth-room"     # what a dragged name carries: JSON of the need


def _area(value):
    return "{:.2f} m²".format(value).replace(".", decimal_sep()) if value else "—"


class _List(QtWidgets.QTreeWidget):
    """The needs, dragged by their name (the need as JSON under MIME, its name as text)."""

    def __init__(self, panel):
        super().__init__()
        self.panel = panel
        self.setColumnCount(4)
        self.setHeaderLabels([t("program.col.name"), t("program.col.area"), t("program.col.made"),
                              t("program.col.made_area")])
        self.setRootIsDecorated(False)
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragOnly)
        self.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3):
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
        page = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(page)
        column.setContentsMargins(4, 4, 4, 4)
        self.hint = QtWidgets.QLabel(t("program.hint"))
        self.hint.setWordWrap(True)
        self.list = _List(self)
        row = QtWidgets.QHBoxLayout()
        self.import_button = QtWidgets.QPushButton(t("program.import"))
        self.import_button.clicked.connect(lambda: self.on_import() if self.on_import else None)
        self.clear_button = QtWidgets.QPushButton(t("program.clear"))
        self.clear_button.clicked.connect(lambda: self.on_clear() if self.on_clear else None)
        row.addWidget(self.import_button)
        row.addWidget(self.clear_button)
        row.addStretch(1)
        self.totals = QtWidgets.QLabel("")
        column.addWidget(self.hint)
        column.addWidget(self.list, 1)
        column.addWidget(self.totals)
        column.addLayout(row)
        self.setWidget(page)
        self.restyle()

    def restyle(self):
        self.hint.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])

    def show_program(self, needs, spaces):
        """The needs, each with how many are made and their area (spaces: IfcModel.spaces())."""
        self.list.clear()
        wanted = made_area = 0.0
        done = 0
        for need, made, area in room_program.progress(needs, spaces):
            kind = t("props.room_exterior_short") if need.external else ""
            item = QtWidgets.QTreeWidgetItem([need.name + (" ({})".format(kind) if kind else ""),
                                              _area(need.area * need.count if need.area else 0.0),
                                              "{} / {}".format(made, need.count), _area(area)])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, need)
            item.setToolTip(0, t("program.drag_tip", name=need.name))
            if made >= need.count:
                item.setForeground(2, QtGui.QBrush(theme.colour("ok")))
                done += 1
            self.list.addTopLevelItem(item)
            wanted += need.area * need.count
            made_area += area
        self.totals.setText(t("program.totals", n=len(needs), done=done, a=_area(wanted), m=_area(made_area))
                            if needs else t("program.empty"))
        self.clear_button.setEnabled(bool(needs))


def dock(parent, beside):
    """The panel as a tab next to `beside` (the Project panel), hidden until asked for."""
    panel = ProgramPanel(parent)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, panel)
    parent.tabifyDockWidget(beside, panel)
    panel.hide()
    return panel
