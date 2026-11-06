"""Lista de corte (0.169): the panels of the project's cabinets (or of those selected) as a joiner orders them — each
part's material, length × width × thickness in mm, how many, how many edges banded; the board's area by material and
the hardware (hinges, runners, handles, feet). Exported to CSV."""

from PySide6 import QtCore, QtWidgets

from ..i18n import t
from ..model import design_text as dt
from . import theme

COLUMNS = ("part", "material", "length", "width", "thickness", "count", "edges")


def table_of(rows):
    """[[cell text]] of the cut list's rows (as the window and the CSV show them)."""
    return [[_role(role), t("cut.mat." + mat), "{:.0f}".format(a * 1000), "{:.0f}".format(b * 1000),
             "{:.0f}".format(c * 1000), str(n), str(e)] for role, mat, a, b, c, n, e in rows]


def _role(role):
    """A part's name: the catalogue's — (0.245) a project's own profile: its own name."""
    from ..core.profiles import CUSTOM, is_custom
    return role[len(CUSTOM):] if is_custom(role) else t("cut.role." + role)


def summary_text(count, rows, hardware, areas):
    parts = sum(r[5] for r in rows)
    area_text = ", ".join("{} {} m²".format(t("cut.mat." + m), dt.num(a, 2)) for m, a in sorted(areas.items()))
    hw = ", ".join("{} {}".format(n, t("cut.hw." + k)) for k, n in sorted(hardware.items())) or "—"
    return t("cut.summary", n=count, parts=parts, areas=area_text or "—", hw=hw)


class CutListDialog(QtWidgets.QDialog):
    def __init__(self, parent, cut_list, count):
        """cut_list() -> (rows, hardware, areas) — model.bim.cut_list; count: how many cabinets."""
        super().__init__(parent)
        self.setWindowTitle(t("cut.title"))
        self.cut_list, self.count = cut_list, count
        self.on_export = self.on_dxf = None
        layout = QtWidgets.QVBoxLayout(self)
        self.summary = QtWidgets.QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.table = QtWidgets.QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([t("cut.col." + c) for c in COLUMNS])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)
        note = QtWidgets.QLabel(t("cut.note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.C["note"])
        layout.addWidget(note)
        buttons = QtWidgets.QHBoxLayout()
        self.export_button = QtWidgets.QPushButton(t("cut.export"))
        self.export_button.clicked.connect(lambda: self.on_export() if self.on_export else None)
        self.dxf_button = QtWidgets.QPushButton(t("fab.export"))          # (0.173) for the CNC
        self.dxf_button.clicked.connect(lambda: self.on_dxf() if self.on_dxf else None)
        close = QtWidgets.QPushButton(t("elprop.close"))
        close.clicked.connect(self.accept)
        buttons.addWidget(self.export_button)
        buttons.addWidget(self.dxf_button)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(820, 520)
        self.rows = []
        self.refresh()

    def refresh(self):
        self.rows, hardware, areas = self.cut_list()
        self.table.setRowCount(0)
        from ..core.profiles import PROFILES, is_custom                 # (0.174: the profiles too; 0.245: own)
        self.dxf_button.setEnabled(any(r[0] in ("slat", "flute", "perforated", "rib", "batten", "ripado_frame")
                                       or r[0] in PROFILES
                                       or is_custom(r[0]) for r in self.rows))
        if not self.rows:
            self.summary.setText(t("cut.none"))
            self.export_button.setEnabled(False)
            return
        self.export_button.setEnabled(True)
        for cells in table_of(self.rows):
            row = self.table.rowCount()
            self.table.insertRow(row)
            for c, value in enumerate(cells):
                item = QtWidgets.QTableWidgetItem(value)
                if c >= 2:
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, c, item)
        self.summary.setText(summary_text(self.count, self.rows, hardware, areas))
