"""Modelo a partir da nuvem (0.162): of a linked point cloud, its floor and ceiling (the heights where its points
gather — found, and to correct), the slice its walls are read in, the thicknesses to look for and that of a wall
seen from one side only; the walls found shown in blue on the plan, and counted; a floor slab under them or not.
OK makes them (one undo step)."""

import numpy as np
from PySide6 import QtCore, QtWidgets

from ..core import cad_walls, scan_walls
from ..i18n import decimal_sep, t
from ..model import cloud_links as cloud_model


def _spin(low, high, value, suffix=" m", step=0.01):
    box = QtWidgets.QDoubleSpinBox()
    box.setRange(low, high)
    box.setDecimals(2)
    box.setSingleStep(step)
    box.setSuffix(suffix)
    box.setValue(value)
    return box


class ScanDialog(QtWidgets.QDialog):
    def __init__(self, parent, links, show_axes):
        super().__init__(parent)
        self.setWindowTitle(t("scan.title"))
        self.links, self.show_axes = list(links), show_axes
        layout = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(t("scan.intro"))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        form = QtWidgets.QFormLayout()
        self.cloud = QtWidgets.QComboBox()
        for link in self.links:
            self.cloud.addItem(link.name)
        self.cloud.currentIndexChanged.connect(lambda _i: self._levels())
        form.addRow(t("scan.cloud"), self.cloud)
        self.floor = _spin(-1000.0, 10000.0, 0.0)
        self.height = _spin(0.5, 50.0, 2.80)
        form.addRow(t("scan.floor"), self.floor)
        form.addRow(t("scan.height"), self.height)
        band = QtWidgets.QHBoxLayout()
        self.band0, self.band1 = _spin(0.1, 5.0, scan_walls.SLICE[0]), _spin(0.2, 5.0, scan_walls.SLICE[1])
        band.addWidget(self.band0)
        band.addWidget(QtWidgets.QLabel(t("cadwalls.to")))
        band.addWidget(self.band1)
        form.addRow(t("scan.slice"), band)
        thick = QtWidgets.QHBoxLayout()
        self.min_t, self.max_t = _spin(0.02, 2.0, cad_walls.MIN_T), _spin(0.02, 2.0, cad_walls.MAX_T)
        thick.addWidget(self.min_t)
        thick.addWidget(QtWidgets.QLabel(t("cadwalls.to")))
        thick.addWidget(self.max_t)
        form.addRow(t("cadwalls.thickness"), thick)
        self.outer = _spin(0.05, 1.0, scan_walls.OUTER_T)
        form.addRow(t("scan.outer"), self.outer)
        self.slab = QtWidgets.QCheckBox(t("scan.slab"))
        self.slab.setChecked(True)
        form.addRow(self.slab)
        self.all_storeys = QtWidgets.QCheckBox(t("scan.all_storeys"))              # (0.214)
        self.all_storeys.toggled.connect(lambda _on: self.refresh())
        form.addRow(self.all_storeys)
        layout.addLayout(form)
        again = QtWidgets.QPushButton(t("scan.again"))
        again.clicked.connect(self.refresh)
        layout.addWidget(again)
        self.found_label = QtWidgets.QLabel()
        self.found_label.setWordWrap(True)
        layout.addWidget(self.found_label)
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                                  | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.resize(520, 480)
        self.axes, self.outline, self.points = [], None, None
        self.openings = []                                   # (0.213) the doors and windows found in the walls
        self.storeys = []                                    # (0.214) [(floor, height)] found in the cloud
        self.per_storey = []                                 # (0.214) [(floor, height, axes, outline, openings,
        #                                                      curved walls (0.215))]
        self.arcs = []                                       # (0.215) the curved walls (cad_walls.arc_walls' form)
        self._levels()

    def link(self):
        k = self.cloud.currentIndex()
        return self.links[k] if 0 <= k < len(self.links) else None

    def _levels(self):
        """The cloud's floor and ceiling, found; then its walls."""
        link = self.link()
        cloud = cloud_model.cloud_of(link.path) if link is not None else None
        self.points = link.place(cloud.points) if cloud is not None and len(cloud) else None
        self.storeys = []
        if self.points is not None:
            found = scan_walls.levels(self.points)
            self.storeys = scan_walls.storeys(found)
            if self.storeys:                                 # (0.214: the lowest storey's floor and height)
                self.floor.setValue(self.storeys[0][0])
                self.height.setValue(max(self.storeys[0][1], 0.5))
            elif found:
                self.floor.setValue(found[0])
                if len(found) > 1:
                    self.height.setValue(max(found[-1] - found[0], 0.5))
        many = len(self.storeys) > 1
        self.all_storeys.setEnabled(many)
        blocker = QtCore.QSignalBlocker(self.all_storeys)
        self.all_storeys.setChecked(many)
        del blocker
        self.all_storeys.setText(t("scan.all_storeys_n", n=len(self.storeys), z=" / ".join(
            "{:.2f}".format(f).replace(".", decimal_sep()) for f, _h in self.storeys)) if many else t("scan.all_storeys"))
        self.refresh()

    def refresh(self):
        link = self.link()
        self.axes, self.outline, self.openings, self.per_storey, self.arcs = [], None, [], [], []
        if self.points is not None:
            many = self.all_storeys.isChecked() and len(self.storeys) > 1
            levels = self.storeys if many else [(self.floor.value(), self.height.value())]
            for floor, height in levels:                     # (0.214: each storey of the cloud, or the one asked)
                xy = scan_walls.slice_xy(self.points, floor, (self.band0.value(), self.band1.value()))
                curves = scan_walls.arcs(xy)                 # (0.215: the curved walls first, their points apart)
                rest = scan_walls.off_arcs(xy, curves)
                segs = scan_walls.lines(rest)
                axes = scan_walls.wall_axes(segs, rest, self.min_t.value(), self.max_t.value(), self.outer.value())
                curved = scan_walls.arc_axes(curves, xy, self.min_t.value(), self.max_t.value(), self.outer.value())
                outline = scan_walls.floor_outline(axes) if axes else None
                found = scan_walls.openings(self.points, axes, floor, height)
                self.per_storey.append((floor, height, axes, outline, found, curved))
                self.axes += axes
                self.arcs += curved
                self.openings += found
            self.outline = self.per_storey[0][3] if self.per_storey else None
        counts = {}
        for th in [w[2] for w in self.axes] + [w[4] for w in self.arcs]:
            counts[round(th * 100, 1)] = counts.get(round(th * 100, 1), 0) + 1
        text = ", ".join("{} × {} cm".format(n, ("{:g}".format(cm)).replace(".", decimal_sep()))
                         for cm, n in sorted(counts.items()))
        walls = len(self.axes) + len(self.arcs)
        said = t("cadwalls.found", n=walls, t=text) if walls else t("scan.none")
        if self.arcs:                                        # (0.215)
            said += " " + t("cadwalls.curved", n=len(self.arcs))
        if len(self.per_storey) > 1:                         # (0.214)
            said += " " + t("scan.in_storeys", n=len(self.per_storey))
        if self.openings:                                    # (0.213)
            doors = sum(1 for _i, k in self.openings if k == "door")
            said += " " + t("scan.openings", d=doors, w=len(self.openings) - doors)
        self.found_label.setText(said)
        self.buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(bool(self.axes or self.arcs))
        if self.show_axes is not None:
            self.show_axes(self.axes, link, self.floor.value(), self.arcs)
