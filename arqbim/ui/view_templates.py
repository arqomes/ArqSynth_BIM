"""View ▸ View templates…: make, change and delete the view templates (model/view_templates.py)
— name, a plan's cut height, the scale on sheets, what the elements are coloured by, which
categories are seen. One undo step when closed with OK. Views get a template in the Project
panel (right-click a view ▸ View template)."""

import copy

from PySide6 import QtCore, QtWidgets

from ..i18n import t
from ..model import graphic_rules as rules_model
from ..model import sheets as sheets_model
from ..model import view_styles as view_styles_model
from ..model.view_templates import PHASE_FILTERS, ViewTemplate, phase_templates
from .project_tree import category_label

COMMON = ("IfcWall", "IfcSlab", "IfcColumn", "IfcBeam", "IfcFooting", "IfcReinforcingBar", "IfcDoor", "IfcWindow",
          "IfcStair", "IfcRailing",
          "IfcRoof", "IfcCovering", "IfcFurniture", "IfcSanitaryTerminal", "IfcPipeSegment", "IfcPipeFitting",
          "IfcDuctSegment", "IfcDuctFitting", "IfcAirTerminal", "IfcUnitaryEquipment",
          "IfcOutlet", "IfcSwitchingDevice", "IfcElectricDistributionBoard", "IfcJunctionBox", "IfcCableCarrierSegment",
          "IfcCableCarrierFitting", "IfcBuildingElementProxy")


class TemplatesDialog(QtWidgets.QDialog):
    def __init__(self, parent, templates, classes, styles=()):
        super().__init__(parent)
        self.setWindowTitle(t("tpl.title"))
        self.view_styles = list(styles)                      # (0.315) the project's view styles, to give
        self.templates = copy.deepcopy(list(templates))     # edited here; the document gets them on OK
        self.classes = sorted(set(COMMON) | set(classes), key=lambda c: category_label(c).lower())
        self._loading = False

        self.list = QtWidgets.QListWidget()
        self.list.currentRowChanged.connect(self._show)
        new = QtWidgets.QPushButton(t("tpl.new"))
        new.clicked.connect(self._new)
        self.delete = QtWidgets.QPushButton(t("tpl.delete"))
        self.delete.clicked.connect(self._delete)
        phases = QtWidgets.QPushButton(t("tpl.make_phases"))
        phases.clicked.connect(self._make_phase_templates)
        left = QtWidgets.QVBoxLayout()
        left.addWidget(self.list, 1)
        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(new)
        buttons.addWidget(self.delete)
        left.addLayout(buttons)
        left.addWidget(phases)

        self.name = QtWidgets.QLineEdit()
        self.name.textEdited.connect(lambda text: self._set("name", text.strip() or self._current().name))
        self.cut = QtWidgets.QDoubleSpinBox()
        self.cut.setRange(0.30, 3.00)
        self.cut.setSingleStep(0.05)
        self.cut.setDecimals(2)
        self.cut.setSuffix(" m")
        self.cut.valueChanged.connect(lambda v: self._set("cut_height", round(float(v), 3)))
        self.scale = QtWidgets.QComboBox()
        self.scale.addItem(t("sheet.scale_auto"), 0)
        for n in sheets_model.SCALES:
            self.scale.addItem("1:{}".format(n), n)
        self.scale.activated.connect(lambda _k: self._set("scale", self.scale.currentData() or None))
        self.rule = QtWidgets.QComboBox()
        self.rule.addItem(t("rules.none"), "")
        for key in rules_model.RULES:
            self.rule.addItem(rules_model.rule_label(key), key[0])
        self.rule.activated.connect(lambda _k: self._set("rule", (self.rule.currentData(),)
                                                         if self.rule.currentData() else None))
        self.phases = QtWidgets.QComboBox()
        for key in PHASE_FILTERS:
            self.phases.addItem(t("tpl.phases." + key), key)
        self.phases.activated.connect(lambda _k: self._set("phases", self.phases.currentData()))
        self.style = QtWidgets.QComboBox()                   # (0.315) the view style its views are drawn with
        self.style.addItem(t("tpl.style_own"), "")
        for vs in view_styles_model.all_styles(self.view_styles):
            self.style.addItem(view_styles_model.label(vs, t), vs.uid)
        self.style.activated.connect(lambda _k: self._set("style", self.style.currentData() or None))
        self.visible = QtWidgets.QListWidget()
        for cls in self.classes:
            item = QtWidgets.QListWidgetItem("{}  ({})".format(category_label(cls), cls))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, cls)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Checked)
            self.visible.addItem(item)
        self.visible.itemChanged.connect(self._visible_changed)
        form = QtWidgets.QFormLayout()
        form.addRow(t("tpl.name"), self.name)
        form.addRow(t("tpl.cut"), self.cut)
        form.addRow(t("tpl.scale"), self.scale)
        form.addRow(t("tpl.rule"), self.rule)
        form.addRow(t("tpl.phases"), self.phases)
        form.addRow(t("tpl.style"), self.style)
        form.addRow(t("tpl.visible"), self.visible)
        self.form = QtWidgets.QWidget()
        self.form.setLayout(form)

        hint = QtWidgets.QLabel(t("tpl.hint"))
        hint.setWordWrap(True)
        ok = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                        | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        ok.accepted.connect(self.accept)
        ok.rejected.connect(self.reject)
        body = QtWidgets.QHBoxLayout()
        body.addLayout(left, 1)
        body.addWidget(self.form, 2)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(body, 1)
        layout.addWidget(hint)
        layout.addWidget(ok)
        self.resize(760, 520)
        self._fill_list(0)

    # ------------------------------------------------------------ the list

    def _fill_list(self, row):
        self.list.blockSignals(True)
        self.list.clear()
        for tpl in self.templates:
            self.list.addItem(tpl.name)
        self.list.blockSignals(False)
        self.form.setEnabled(bool(self.templates))
        self.delete.setEnabled(bool(self.templates))
        if self.templates:
            self.list.setCurrentRow(min(row, len(self.templates) - 1))
            self._show(self.list.currentRow())

    def _new(self):
        names = {tpl.name for tpl in self.templates}
        n = 1
        while t("tpl.default_name", n=n) in names:
            n += 1
        self.templates.append(ViewTemplate(t("tpl.default_name", n=n)))
        self._fill_list(len(self.templates) - 1)
        self.name.setFocus()
        self.name.selectAll()

    def _make_phase_templates(self):
        """The three templates of a renovation project: existing, proposal, changes (yellows and reds)."""
        names = {tpl.name for tpl in self.templates}
        made = [tpl for tpl in phase_templates(lambda key: t("tpl.name." + key)) if tpl.name not in names]
        self.templates += made
        self._fill_list(len(self.templates) - 1)

    def _delete(self):
        row = self.list.currentRow()
        if 0 <= row < len(self.templates):
            del self.templates[row]
            self._fill_list(row)

    def _current(self):
        row = self.list.currentRow()
        return self.templates[row] if 0 <= row < len(self.templates) else None

    # ------------------------------------------------------------ one template

    def _show(self, row):
        tpl = self._current()
        if tpl is None:
            return
        self._loading = True
        self.name.setText(tpl.name)
        self.cut.setValue(tpl.cut_height)
        self.scale.setCurrentIndex(max(0, self.scale.findData(tpl.scale or 0)))
        self.rule.setCurrentIndex(max(0, self.rule.findData(tpl.rule[0] if tpl.rule else "")))
        self.phases.setCurrentIndex(max(0, self.phases.findData(tpl.phases)))
        self.style.setCurrentIndex(max(0, self.style.findData(tpl.style or "")))
        for k in range(self.visible.count()):
            item = self.visible.item(k)
            hidden = item.data(QtCore.Qt.ItemDataRole.UserRole) in tpl.hidden
            item.setCheckState(QtCore.Qt.CheckState.Unchecked if hidden else QtCore.Qt.CheckState.Checked)
        self._loading = False

    def _set(self, attr, value):
        tpl = self._current()
        if tpl is None or self._loading:
            return
        setattr(tpl, attr, value)
        if attr == "name":
            self.list.currentItem().setText(value)

    def _visible_changed(self, _item):
        if self._loading:
            return
        hidden = [self.visible.item(k).data(QtCore.Qt.ItemDataRole.UserRole) for k in range(self.visible.count())
                  if self.visible.item(k).checkState() != QtCore.Qt.CheckState.Checked]
        self._set("hidden", hidden)
