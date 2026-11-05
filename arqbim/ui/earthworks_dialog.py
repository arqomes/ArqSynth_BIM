"""Aterro e escavação (0.157): the platforms of the terrains, one per line — its name, height, area, the earth
taken away (cut) and brought (fill) for it alone — and the totals of each terrain (all its platforms together:
where they overlap, counted once). A platform chosen can be deleted (one undo step)."""

from PySide6 import QtCore, QtWidgets

from ..core import earthworks
from ..core.units import format_length
from ..i18n import decimal_sep, t
from ..model import bim

REF = QtCore.Qt.ItemDataRole.UserRole


def _m3(v):
    return "{:.1f} m³".format(v).replace(".", decimal_sep())


class EarthworksDialog(QtWidgets.QDialog):
    def __init__(self, parent, doc, terrains):
        """terrains: the GlobalIds of the terrains."""
        super().__init__(parent)
        self.setWindowTitle(t("earth.title"))
        self.doc, self.terrains = doc, list(terrains)
        layout = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(t("earth.intro"))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([t("earth.name"), t("earth.height"), t("earth.area"), t("earth.cut"),
                                              t("earth.fill")])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)
        self.totals = QtWidgets.QLabel()
        layout.addWidget(self.totals)
        buttons = QtWidgets.QHBoxLayout()
        self.remove_button = QtWidgets.QPushButton(t("earth.remove"))
        self.remove_button.clicked.connect(self._remove)
        close = QtWidgets.QPushButton(t("elprop.close"))
        close.clicked.connect(self.accept)
        buttons.addWidget(self.remove_button)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(680, 340)
        self.rows = []
        self.refresh()

    def refresh(self):
        """Each platform's own volumes; the totals of all."""
        self.table.setRowCount(0)
        self.rows, total_cut, total_fill = [], 0.0, 0.0
        for guid in self.terrains:
            platforms = self.doc.ifc.terrain_platforms(guid)
            if not platforms:
                continue
            survey = self.doc.ifc.terrain_survey(guid)
            for k, plat in enumerate(platforms):
                cut, fill = earthworks.volumes(survey, earthworks.proposed(survey, [plat]))
                row = self.table.rowCount()
                self.table.insertRow(row)
                values = (plat.name, format_length(plat.z, decimal_sep()),
                          "{:.2f} m²".format(plat.polygon().area).replace(".", decimal_sep()), _m3(cut), _m3(fill))
                for c, text in enumerate(values):
                    item = QtWidgets.QTableWidgetItem(text)
                    if c:
                        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, c, item)
                self.rows.append((guid, k))
            cut, fill = self.doc.ifc.terrain_volumes(guid)
            total_cut, total_fill = total_cut + cut, total_fill + fill
        self.totals.setText(t("earth.totals", c=_m3(total_cut), f=_m3(total_fill),
                              b=_m3(total_cut - total_fill)) if self.rows else t("earth.none"))
        self.remove_button.setEnabled(bool(self.rows))
        if self.rows:
            self.table.selectRow(0)

    def _remove(self):
        row = self.table.currentRow()
        if not 0 <= row < len(self.rows):
            return
        guid, k = self.rows[row]
        bim.remove_platforms(self.doc, guid, [k])
        self.refresh()
