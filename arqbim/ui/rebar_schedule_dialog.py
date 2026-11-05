"""Lista de armaduras (0.166): the bar schedule read from the IFC — each position (equal bars of one diameter, shape
and length) of each member: how many, how long each, its shape code, the total length, the weight; the totals by
diameter and the whole weight. Exported to CSV (Excel opens it as it is). A double-click selects the set."""

from PySide6 import QtCore, QtWidgets

from ..i18n import decimal_sep, t
from . import theme

GUID = QtCore.Qt.ItemDataRole.UserRole
COLUMNS = ("mark", "element", "role", "diameter", "count", "length", "shape", "total", "weight")


def _num(v, d=2):
    return ("{:." + str(d) + "f}").format(float(v)).replace(".", decimal_sep())


def role_text(role):
    return t("rsched.role." + role) if role else ""


def table_of(rows):
    """[[cell text]] of the schedule's rows (as the window and the CSV show them)."""
    return [[r["mark"], r["host_name"], role_text(r["role"]), str(r["diameter"]), str(r["count"]),
             _num(r["length"], 2), r["shape"], _num(r["count"] * r["length"], 2), _num(r["weight"], 1)]
            for r in rows]


def totals_text(totals):
    items = " · ".join(t("rsched.total_item", d=d, m=_num(m, 1), kg=_num(kg, 1)) for d, (m, kg) in totals.items())
    return t("rsched.totals", items=items, kg=_num(sum(kg for _m, kg in totals.values()), 1))


class RebarScheduleDialog(QtWidgets.QDialog):
    def __init__(self, parent, schedule):
        """schedule() -> (rows, totals) — model.bim.rebar_schedule."""
        super().__init__(parent)
        self.setWindowTitle(t("rsched.title"))
        self.schedule = schedule
        self.on_select = self.on_export = None
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([t("rsched.col." + c) for c in COLUMNS])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.cellDoubleClicked.connect(self._chosen)
        layout.addWidget(self.table, 1)
        self.totals = QtWidgets.QLabel()
        self.totals.setWordWrap(True)
        layout.addWidget(self.totals)
        note = QtWidgets.QLabel(t("rsched.note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.C["note"])
        layout.addWidget(note)
        buttons = QtWidgets.QHBoxLayout()
        self.export_button = QtWidgets.QPushButton(t("rsched.export"))
        self.export_button.clicked.connect(lambda: self.on_export() if self.on_export else None)
        close = QtWidgets.QPushButton(t("elprop.close"))
        close.clicked.connect(self.accept)
        buttons.addWidget(self.export_button)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(900, 560)
        self.rows = []
        self.refresh()

    def refresh(self):
        self.rows, totals = self.schedule()
        self.table.setRowCount(0)
        if not self.rows:
            self.totals.setText(t("rsched.empty"))
            self.export_button.setEnabled(False)
            return
        self.export_button.setEnabled(True)
        for r, cells in zip(self.rows, table_of(self.rows)):
            row = self.table.rowCount()
            self.table.insertRow(row)
            for c, value in enumerate(cells):
                item = QtWidgets.QTableWidgetItem(value)
                item.setData(GUID, r["guid"])
                if c in (0, 3, 4, 5, 7, 8):
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, c, item)
        self.totals.setText(totals_text(totals))

    def _chosen(self, row, _column):
        item = self.table.item(row, 0)
        if item is not None and self.on_select is not None:
            self.on_select([item.data(GUID)])
