"""Ações e materiais (0.164): the structure's settings — its concrete and steel, the use of its floors and roof,
the finishes and partitions, the wind's zone and terrain, the seismic zones (action of type 1 and 2), the ground
type, the importance class, the soil's allowable pressure — and, worked out with them, each storey's loads and the
wind's and the earthquake's forces on it. OK keeps the settings and loads the analytical model (cases G and Q)."""

import dataclasses

from PySide6 import QtCore, QtWidgets

from ..core import actions as act
from ..i18n import decimal_sep, t
from . import theme


def _num(v, d=1):
    return ("{:." + str(d) + "f}").format(v).replace(".", decimal_sep())


class ActionsDialog(QtWidgets.QDialog):
    def __init__(self, parent, settings, work_out):
        """work_out(settings) -> (model, loads) (bim.actions_of)."""
        super().__init__(parent)
        self.setWindowTitle(t("actions.title"))
        self.work_out = work_out
        layout = QtWidgets.QVBoxLayout(self)
        top = QtWidgets.QHBoxLayout()
        left, right = QtWidgets.QFormLayout(), QtWidgets.QFormLayout()
        self.fields = {}

        def choice(form, name, options, labels=None):
            box = QtWidgets.QComboBox()
            for k in options:
                box.addItem(labels(k) if labels else k, k)
            box.setCurrentIndex(max(box.findData(getattr(settings, name)), 0))
            box.currentIndexChanged.connect(lambda _i: self.refresh())
            form.addRow(t("actions." + name), box)
            self.fields[name] = box

        def number(form, name, low, high, suffix, step=0.1):
            box = QtWidgets.QDoubleSpinBox()
            box.setRange(low, high)
            box.setDecimals(2)
            box.setSingleStep(step)
            box.setSuffix(suffix)
            box.setValue(float(getattr(settings, name)))
            box.valueChanged.connect(lambda _v: self.refresh())
            form.addRow(t("actions." + name), box)
            self.fields[name] = box

        choice(left, "concrete", list(act.CONCRETE))
        choice(left, "steel", list(act.STEEL))
        choice(left, "use", list(act.USES), lambda k: t("actions.use." + k))
        choice(left, "roof_use", list(act.USES), lambda k: t("actions.use." + k))
        number(left, "finishes", 0.0, 20.0, " kN/m²")
        number(left, "partitions", 0.0, 10.0, " kN/m²")
        number(left, "soil_kpa", 50.0, 2000.0, " kPa", 10.0)
        choice(left, "slabs", list(act.SLAB_MODELS), lambda k: t("actions.slabs." + k))          # (0.223)
        choice(right, "wind_zone", list(act.WIND_ZONES))
        choice(right, "terrain", list(act.TERRAIN), lambda k: t("actions.terrain." + k))       # (0.219: the NA's)
        choice(right, "seismic_zone_1", [k for k in act.SEISMIC_ZONES if k.startswith("1")])
        choice(right, "seismic_zone_2", [k for k in act.SEISMIC_ZONES if k.startswith("2")])
        choice(right, "ground", list(act.GROUND_S_MAX))
        choice(right, "importance", list(act.IMPORTANCE))
        choice(right, "snow_zone", list(act.SNOW_ZONES), lambda k: t("actions.snow_zone." + k))     # (0.217)
        number(right, "altitude", 0.0, 3000.0, " m", 10.0)
        # (0.337) the load-bearing walls' masonry (EC6)
        from ..core import ec6
        choice(left, "masonry_unit", list(ec6.UNITS), lambda k: t("actions.masonry_unit." + k))
        choice(left, "masonry_group", list(ec6.GROUPS))
        number(left, "masonry_fb", 1.0, 80.0, " N/mm²", 0.5)
        choice(left, "masonry_mortar", list(ec6.MORTARS))
        number(left, "masonry_gamma", 1.5, 3.0, "", 0.1)
        top.addLayout(left)
        top.addLayout(right)
        layout.addLayout(top)
        self.table = QtWidgets.QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([t("actions.col." + c) for c in
                                              ("level", "area", "g", "q", "weight", "wind_x", "wind_y", "quake_1",
                                               "quake_2")])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)
        self.summary = QtWidgets.QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        note = QtWidgets.QLabel(t("actions.note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.C["note"])
        layout.addWidget(note)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.resize(860, 620)
        self.loads = None
        self.refresh()

    def settings(self):
        values = {}
        for name, w in self.fields.items():
            values[name] = w.currentData() if isinstance(w, QtWidgets.QComboBox) else float(w.value())
        return dataclasses.replace(act.Settings(), **values)

    def refresh(self):
        _model, loads = self.work_out(self.settings())
        self.loads = loads
        self.table.setRowCount(0)
        for st in loads.storeys:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for c, value in enumerate((_num(st.level, 2), _num(st.area, 1), _num(st.g), _num(st.q), _num(st.weight),
                                       _num(st.wind_x), _num(st.wind_y), _num(st.quake_1), _num(st.quake_2))):
                item = QtWidgets.QTableWidgetItem(value)
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, c, item)
        if loads.storeys:
            s = self.settings()
            self.summary.setText(t("actions.summary", t1=_num(loads.period, 2), sd1=_num(loads.sd_1, 2),
                                   sd2=_num(loads.sd_2, 2), b1=_num(loads.base_1), b2=_num(loads.base_2))
                                 + " " + t("actions.snow_summary", sk=_num(act.snow_ground(s.snow_zone, s.altitude), 2),
                                           s=_num(s.snow(), 2), q=_num(s.imposed(roof=True), 2)))
        else:
            self.summary.setText(t("actions.none"))
