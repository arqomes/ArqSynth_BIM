"""Verificação EC2 e armaduras (0.166): each concrete member of the structure checked by Eurocode 2 with the forces
of the analysis — its status (OK, attention, fails) and utilisation, the reinforcement it needs (bars, stirrups /
ties, meshes), whether the model's bars are these, what governs; all its notes below for the line chosen. Then the
reinforcement put in the model (one undo step) and the bar schedule. A double-click on a line selects the element.
(0.337) The load-bearing masonry walls too, by Eurocode 6: no bars, the masonry's fk in the summary; (0.345) the
façade ones, load-bearing or not, out of their plane by the wind."""

import numpy as np
from PySide6 import QtCore, QtWidgets

from ..core import ec2
from ..i18n import t
from ..model.design_text import bars_text, error_text, main_note, masonry, masonry_fk, note_text, num, ordered
from . import theme

GUID = QtCore.Qt.ItemDataRole.UserRole
STATUS_KEYS = {ec2.OK: "ok", ec2.WARN: "attention", ec2.FAIL: "fail"}    # (0.339) a status's colour in the theme
BAR_KEYS = ("bottom", "top", "bars", "links", "mesh_x", "mesh_y", "top_x", "top_y", "layers", "bottom_cont",
            "bottom_zones", "top_cont", "top_zones", "vertical", "horizontal")


def _numbers(value):
    """A kept value as its numbers, rounded (a pair, a list of zones, one number), or None."""
    if value is None or value == [] or value == ():
        return None
    return [round(float(v), 4) for v in np.ravel(np.asarray(value, dtype=float))]


def same_bars(stored, kept):
    """The model's bars (as kept with them) are those of this design."""
    if not kept:
        return None
    return all(_numbers(stored.get(k)) == _numbers(kept.get(k)) for k in BAR_KEYS)


class DesignDialog(QtWidgets.QDialog):
    def __init__(self, parent, design, names, settings, kept=None):
        """design() -> (model, loads, analysis, [ElementDesign]); names: {GlobalId: element name}; settings: the
        project's (core.actions.Settings); kept(guid) -> the design its bars in the model were laid out from."""
        super().__init__(parent)
        self.setWindowTitle(t("ec2.title"))
        self.design, self.names, self.settings, self.kept = design, names, settings, kept
        self.on_select = self.on_make = self.on_schedule = None
        layout = QtWidgets.QVBoxLayout(self)
        self.summary = QtWidgets.QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([t("ec2.col." + c) for c in
                                              ("element", "status", "ratio", "bars", "model", "note")])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.cellDoubleClicked.connect(self._chosen)
        self.table.itemSelectionChanged.connect(self._show_notes)
        layout.addWidget(self.table, 1)
        self.details = QtWidgets.QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(130)
        layout.addWidget(self.details)
        note = QtWidgets.QLabel(t("ec2.note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.C["note"])
        layout.addWidget(note)
        buttons = QtWidgets.QHBoxLayout()
        again = QtWidgets.QPushButton(t("ec2.again"))
        again.clicked.connect(self.refresh)
        self.make_button = QtWidgets.QPushButton(t("ec2.make"))
        self.make_button.clicked.connect(self._make)
        schedule = QtWidgets.QPushButton(t("ec2.schedule"))
        schedule.clicked.connect(lambda: self.on_schedule() if self.on_schedule else None)
        close = QtWidgets.QPushButton(t("elprop.close"))
        close.clicked.connect(self.accept)
        for b in (again, self.make_button, schedule):
            buttons.addWidget(b)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(1060, 620)
        self.designs = []
        self.refresh()

    def refresh(self):
        _model, _loads, analysis, designs = self.design()
        designs = ordered(designs, self.names)
        self.designs = designs
        self.table.setRowCount(0)
        self.details.clear()
        if analysis is not None and analysis.error and not designs:
            self.summary.setText(t("analysis.error", e=error_text(analysis.error)))
            self.make_button.setEnabled(False)
            return
        if not designs:
            self.summary.setText(t("ec2.none"))
            self.make_button.setEnabled(False)
            return
        self.make_button.setEnabled(any(e.design.status != ec2.FAIL for e in designs if not masonry(e)))
        for e in designs:
            d = e.design
            row = self.table.rowCount()
            self.table.insertRow(row)
            if masonry(e):                              # (0.337) masonry: no bars to lay out
                model = "—"
            else:
                kept = self.kept(e.guid) if self.kept else None
                same = same_bars(e.stored(self.settings), kept)
                model = t("ec2.model.none") if same is None else t("ec2.model.same" if same else "ec2.model.other")
            governs = main_note(d)
            values = (self.names.get(e.guid, e.guid), t("ec2.status." + d.status),
                      "{:.0f} %".format(100.0 * d.ratio), bars_text(e.kind, d), model,
                      note_text(governs) if governs is not None else "")
            for c, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setData(GUID, e.guid)
                if c == 1:
                    item.setForeground(theme.colour(STATUS_KEYS[d.status]))
                if c == 2:
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, c, item)
        n = len(designs)
        counts = {s: sum(1 for e in designs if e.design.status == s) for s in (ec2.OK, ec2.WARN, ec2.FAIL)}
        text = t("ec2.summary", n=n, ok=counts[ec2.OK], w=counts[ec2.WARN], f=counts[ec2.FAIL],
                 c=self.settings.concrete, s=self.settings.steel)
        walls = sum(1 for e in designs if masonry(e))
        if walls:                                       # (0.337) the masonry's strength, EC6 (0.346: its types')
            text += " " + t("ec6.summary", n=walls, fk=masonry_fk(designs, self.settings))
        if analysis is not None and analysis.error:      # (0.230: the strip footings without a frame analysed)
            text = t("analysis.error", e=error_text(analysis.error)) + " " + text
        self.summary.setText(text)

    def _show_notes(self):
        rows = {i.row() for i in self.table.selectedItems()}
        if not rows:
            self.details.clear()
            return
        e = self.designs[min(rows)]
        lines = ["{} — {}".format(self.names.get(e.guid, e.guid), t("ec2.status." + e.design.status))]
        for n in e.design.notes:
            mark = {ec2.OK: "·", ec2.WARN: "!", ec2.FAIL: "✗"}[n.status]
            lines.append("{} {}".format(mark, note_text(n)))
        self.details.setPlainText("\n".join(lines))

    def _make(self):
        if self.on_make is not None:
            self.on_make(self.designs)
            self.refresh()

    def _chosen(self, row, _column):
        item = self.table.item(row, 0)
        if item is not None and self.on_select is not None:
            self.on_select([item.data(GUID)])
