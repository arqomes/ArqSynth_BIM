"""Análise da estrutura (0.165): the structure analysed as a 3D frame — each column and beam with its forces'
envelope over the combinations (N, V, M in its span and over its supports; a column's largest moment) and the one
that governs, each beam's deflection (mid-span, quasi-permanent, as L/…); the load path checked (what goes in, what
comes down); the wind's drift; (0.222) each storey's sway and its second order's θ under the wind and the earthquake
each way. A double-click on a line selects the element."""

from PySide6 import QtCore, QtWidgets

from ..i18n import decimal_sep, t
from ..model import design_text as dt
from . import theme

GUID = QtCore.Qt.ItemDataRole.UserRole


def _num(v, d=1):
    return ("{:." + str(d) + "f}").format(v).replace(".", decimal_sep())


class AnalysisDialog(QtWidgets.QDialog):
    def __init__(self, parent, analyse, names):
        """analyse() -> (model, loads, Analysis); names: {GlobalId: element name}."""
        super().__init__(parent)
        self.setWindowTitle(t("analysis.title"))
        self.analyse, self.names = analyse, names
        self.on_select = None
        self.on_save = None             # (0.221) () -> Analysis: the results saved in the IFC
        layout = QtWidgets.QVBoxLayout(self)
        self.summary = QtWidgets.QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.table = QtWidgets.QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([t("analysis.col." + c) for c in
                                              ("element", "length", "n_min", "n_max", "v", "m_pos", "m_neg",
                                               "deflection", "combo")])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.cellDoubleClicked.connect(self._chosen)
        layout.addWidget(self.table, 1)
        # (0.222) each storey's sway under the wind and the earthquake: the second order's θ
        self.sways = QtWidgets.QTableWidget(0, 8)
        self.sways.setHorizontalHeaderLabels([t("analysis.sway.col." + c) for c in
                                              ("case", "level", "height", "p", "v", "drift", "theta", "verdict")])
        self.sways.verticalHeader().setVisible(False)
        self.sways.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sways.horizontalHeader().setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.sways.setToolTip(t("analysis.sway_note"))
        self.sways.setMaximumHeight(170)
        layout.addWidget(self.sways)
        note = QtWidgets.QLabel(t("analysis.note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.C["note"])
        layout.addWidget(note)
        buttons = QtWidgets.QHBoxLayout()
        again = QtWidgets.QPushButton(t("analysis.again"))
        again.clicked.connect(self.refresh)
        self.save_button = QtWidgets.QPushButton(t("analysis.save"))              # (0.221)
        self.save_button.setToolTip(t("analysis.save_tip"))
        self.save_button.clicked.connect(self._save)
        close = QtWidgets.QPushButton(t("elprop.close"))
        close.clicked.connect(self.accept)
        buttons.addWidget(again)
        buttons.addWidget(self.save_button)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(980, 560)
        self.result = None
        self.refresh()

    def _save(self):
        """(0.221) The results in the IFC: the window's owner does it (one undo step)."""
        if self.on_save is not None:
            result = self.on_save()
            self.summary.setText(self.summary.text() + " " + (t("analysis.saved") if result is not None
                                                              and not result.error else t("analysis.not_saved")))

    def _wall_rows(self, result):
        """(0.336) A line for each load-bearing wall: its length, the compression on each metre at its base (ULS
        1,35G+1,50Q, and G alone), the largest horizontal force it takes (ULS: the wind × 1,5, the earthquake × 1),
        and from which action."""
        for w in sorted(result.walls, key=lambda w: self.names.get(w.guid, w.guid)):
            row = self.table.rowCount()
            self.table.insertRow(row)
            for c, value in enumerate(dt.wall_values(w, self.names.get(w.guid, w.guid))):
                item = QtWidgets.QTableWidgetItem(value)
                item.setData(GUID, w.guid)
                item.setToolTip(t("analysis.wall_note"))
                if 0 < c < 8:
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, c, item)

    def refresh(self):
        _model, _loads, result = self.analyse()
        self.result = result
        self.table.setRowCount(0)
        self.sways.setRowCount(0)
        if result.error:
            self.summary.setText(t("analysis.error", e=dt.error_text(result.error)))
            self.sways.setVisible(False)
            return
        self._wall_rows(result)                             # (0.336) the load-bearing walls first
        if not result.members:
            self.summary.setText(t("analysis.walls_only", w=len(result.walls)))
            self.sways.setVisible(False)
            return
        order = sorted(result.members, key=lambda m: (m.kind != "column", self.names.get(m.guid, m.id), m.id))
        for m in order:
            row = self.table.rowCount()
            self.table.insertRow(row)
            name = self.names.get(m.guid, m.id)
            if "/" in m.id:
                name += " ({})".format(m.id.split("/")[-1])
            span = ""
            if m.kind == "beam" and m.deflection > 1e-9:
                span = "{} mm (L/{:.0f})".format(_num(m.deflection * 1000, 1), m.length / m.deflection)
            values = (name, _num(m.length, 2), _num(m.n_min), _num(m.n_max), _num(m.v),
                      _num(m.m_pos if m.kind == "beam" else m.m_column), _num(m.m_neg if m.kind == "beam" else 0.0),
                      span, m.combo)
            for c, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setData(GUID, m.guid)
                if 0 < c < 8:
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                if c == 7 and m.kind == "beam" and m.deflection > m.length / 250:
                    item.setForeground(theme.colour("fail"))       # (beyond L/250: told in red)
                self.table.setItem(row, c, item)
        for p in sorted(result.panels, key=lambda p: self.names.get(p.guid, p.guid)):     # (0.223: the slabs)
            row = self.table.rowCount()
            self.table.insertRow(row)
            for c, value in enumerate(dt.panel_values(p, self.names.get(p.guid, p.guid))):
                item = QtWidgets.QTableWidgetItem(value)
                item.setData(GUID, p.guid)
                item.setToolTip(t("analysis.slab_note", size=_num(result.shell_size, 2)))
                if 0 < c < 8:
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                if c == 7 and p.deflection > p.span / 250:
                    item.setForeground(theme.colour("fail"))
                self.table.setItem(row, c, item)
        drift = "1/{:.0f}".format(1 / result.drift_wind) if result.drift_wind > 1e-12 else "—"
        second = dt.second_order_text(result)
        self.summary.setText(t("analysis.summary", n=len(result.members), put=_num(result.loads_in),
                               up=_num(result.reactions_up), drift=drift) + (" " + second if second else "")
                             + (" " + t("analysis.walls_too", w=len(result.walls)) if result.walls else ""))
        for values, verdict in dt.sway_rows(result):
            row = self.sways.rowCount()
            self.sways.insertRow(row)
            for c, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                if 0 < c < 7:
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                if c >= 6 and verdict != "ignored":
                    item.setForeground(theme.colour("attention" if verdict == "amplified" else "fail"))
                self.sways.setItem(row, c, item)
        self.sways.setVisible(self.sways.rowCount() > 0)

    def _chosen(self, row, _column):
        item = self.table.item(row, 0)
        if item is not None and self.on_select is not None:
            self.on_select([item.data(GUID)])
