"""Quantidades da estrutura (0.167): each concrete member's concrete, formwork and steel (of the bars in the model),
its steel's rate (in red when out of the usual for its kind); the totals by kind and of all. Exported to CSV; a
double-click selects the element."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..model import design_text as dt
from ..model import structure_quantities as sq
from . import theme

GUID = QtCore.Qt.ItemDataRole.UserRole
COLUMNS = ("element", "storey", "concrete", "formwork", "steel", "rate")


def table_of(rows, names):
    """[[cell text]] of the rows, then a line per kind and the total — as the window and the CSV show them."""
    out = []
    for r in rows:
        out.append([names.get(r.guid, r.guid), r.storey, dt.num(r.concrete, 3), dt.num(r.formwork, 2),
                    dt.num(r.steel, 1) if r.has_bars else "—", dt.num(r.rate, 0) if r.has_bars else "—"])
    by_kind, whole = sq.totals(rows)
    for kind in sq.KINDS:
        if kind in by_kind:
            c, f, s = by_kind[kind]
            out.append([t("qty.kind." + kind), "", dt.num(c, 3), dt.num(f, 2), dt.num(s, 1),
                        dt.num(s / c, 0) if c > 1e-9 and s > 0 else "—"])
    c, f, s = whole
    out.append([t("qty.total"), "", dt.num(c, 3), dt.num(f, 2), dt.num(s, 1), dt.num(s / c, 0) if c > 1e-9 and s > 0
                else "—"])
    return out


def ordered(rows, names):
    return sorted(rows, key=lambda r: (dt.KIND_ORDER.get(r.kind, 9), dt.natural(names.get(r.guid, r.guid))))


class QuantitiesDialog(QtWidgets.QDialog):
    def __init__(self, parent, quantities, names):
        """quantities() -> [QuantityRow]; names: {GlobalId: element name}."""
        super().__init__(parent)
        self.setWindowTitle(t("qty.title"))
        self.quantities, self.names = quantities, names
        self.on_select = self.on_export = None
        layout = QtWidgets.QVBoxLayout(self)
        self.summary = QtWidgets.QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.table = QtWidgets.QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([t("qty.col." + c) for c in COLUMNS])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.cellDoubleClicked.connect(self._chosen)
        layout.addWidget(self.table, 1)
        note = QtWidgets.QLabel(t("qty.note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.C["note"])
        layout.addWidget(note)
        buttons = QtWidgets.QHBoxLayout()
        self.export_button = QtWidgets.QPushButton(t("qty.export"))
        self.export_button.clicked.connect(lambda: self.on_export() if self.on_export else None)
        close = QtWidgets.QPushButton(t("elprop.close"))
        close.clicked.connect(self.accept)
        buttons.addWidget(self.export_button)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(820, 560)
        self.rows = []
        self.refresh()

    def refresh(self):
        self.rows = ordered(self.quantities(), self.names)
        self.table.setRowCount(0)
        if not self.rows:
            self.summary.setText(t("qty.none"))
            self.export_button.setEnabled(False)
            return
        self.export_button.setEnabled(True)
        bold = QtGui.QFont()
        bold.setBold(True)
        for k, cells in enumerate(table_of(self.rows, self.names)):
            row = self.table.rowCount()
            self.table.insertRow(row)
            r = self.rows[k] if k < len(self.rows) else None
            for c, value in enumerate(cells):
                item = QtWidgets.QTableWidgetItem(value)
                if r is not None:
                    item.setData(GUID, r.guid)
                    if c == 5 and r.implausible:
                        item.setForeground(theme.colour("fail"))
                else:
                    item.setFont(bold)
                if c >= 2:
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, c, item)
        _by_kind, (c, f, s) = sq.totals(self.rows)
        self.summary.setText(t("qty.summary", n=len(self.rows), c=dt.num(c, 2), f=dt.num(f, 1), s=dt.num(s, 0),
                               r=dt.num(s / c, 0) if c > 1e-9 else "—"))

    def _chosen(self, row, _column):
        item = self.table.item(row, 0)
        guid = item.data(GUID) if item is not None else None
        if guid and self.on_select is not None:
            self.on_select([guid])
