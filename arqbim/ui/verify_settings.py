"""(0.417) «Regulamentos do projeto»: the country the project is built in (its laws), the building's use, the kind of work
(new or an intervention, levels I–IV as Cabo Verde's CTE art. 6.º), its height (automatic from the storeys, or
typed), and which laws are checked — the country's own and the supplementary ones (Cabo Verde: the Portuguese, CTE
art. 4.º)."""

from PySide6 import QtCore, QtWidgets

from ..i18n import decimal_sep, lang, t
from ..verify import check as check_mod
from ..verify import project
from ..verify import rules as rules_mod
from . import theme


class VerifySettings(QtWidgets.QDialog):
    def __init__(self, parent, settings, auto_height, lot=None, summary=None):
        super().__init__(parent)
        self.setWindowTitle(t("verify.settings.title"))
        self.setMinimumWidth(520)
        self.lot = lot
        self.summary = summary or {}
        language = lang()
        self.all_packs = rules_mod.packs()
        form = QtWidgets.QFormLayout()
        self.country = QtWidgets.QComboBox()
        self.country.addItem(t("verify.settings.no_country"), None)
        for key in project.COUNTRIES:
            self.country.addItem(project.label(project.COUNTRIES, key, language), key)
        self.country.setCurrentIndex(max(0, self.country.findData(settings.get("country"))))
        form.addRow(t("verify.settings.country"), self.country)
        self.use = QtWidgets.QComboBox()
        for key in project.BUILDING_USES:
            self.use.addItem(project.label(project.BUILDING_USES, key, language), key)
        self.use.setCurrentIndex(max(0, self.use.findData(settings.get("building_use"))))
        form.addRow(t("verify.settings.use"), self.use)
        self.work = QtWidgets.QComboBox()
        for key in project.WORKS:
            self.work.addItem(project.label(project.WORKS, key, language), key)
        self.work.setCurrentIndex(max(0, self.work.findData(settings.get("work"))))
        form.addRow(t("verify.settings.work"), self.work)
        self.height = QtWidgets.QLineEdit("" if settings.get("height") is None else
                                          "{:.2f}".format(settings["height"]).replace(".", decimal_sep()))
        self.height.setPlaceholderText(t("verify.settings.height_auto", h=check_mod.number(auto_height, "m")))
        form.addRow(t("verify.settings.height"), self.height)
        self.packs = QtWidgets.QTreeWidget()
        self.packs.setHeaderHidden(True)
        self.packs.setRootIsDecorated(False)
        self.packs.setMinimumHeight(110)
        self.good_practice = QtWidgets.QCheckBox(t("verify.settings.good_practice"))      # (0.422)
        self.good_practice.setChecked(bool(settings.get("good_practice", True)))
        self.good_practice.toggled.connect(lambda _on: self._fill_packs())
        laws = QtWidgets.QWidget()
        box = QtWidgets.QVBoxLayout(laws)
        box.addLayout(form)
        box.addWidget(QtWidgets.QLabel(t("verify.settings.packs")))
        box.addWidget(self.packs)
        box.addWidget(self.good_practice)
        note = QtWidgets.QLabel(t("verify.settings.note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.C["note"])
        box.addWidget(note)
        self.tabs = QtWidgets.QTabWidget()                  # (0.423: the laws; the lot and the town plan)
        self.tabs.addTab(laws, t("verify.settings.packs"))
        self.tabs.addTab(self._plan_page(settings), t("verify.settings.plan"))
        outer = QtWidgets.QVBoxLayout(self)
        outer.addWidget(self.tabs)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)
        self.country.currentIndexChanged.connect(lambda _k: self._fill_packs())
        self._fill_packs()

    # ------------------------------------------------------------ (0.423) the lot and the town plan
    def _plan_page(self, settings):
        page = QtWidgets.QWidget()
        box = QtWidgets.QVBoxLayout(page)
        s = self.summary
        if self.lot is None:
            text = t("verify.settings.lot_none")
        else:
            text = t("verify.settings.lot", a=check_mod.number(self.lot["area"], "m2"), n=len(self.lot["outline"]),
                     i=check_mod.number(s.get("area_implantacao"), "m2"),
                     c=check_mod.number(s.get("area_construcao"), "m2"),
                     p="{:g}".format(s.get("pisos_acima_solo") or 0))
        self.lot_label = QtWidgets.QLabel(text)
        self.lot_label.setWordWrap(True)
        box.addWidget(self.lot_label)
        self.fronts = QtWidgets.QListWidget()               # the sides: which face the street
        if self.lot is not None:
            from ..core import lot as core_lot
            chosen = set(self.lot["fronts"]) if self.lot.get("chosen") else set()
            for k, (a, b) in enumerate(core_lot.sides(self.lot["outline"])):
                item = QtWidgets.QListWidgetItem(t("verify.settings.side", k=k + 1,
                                                   l=check_mod.number(core_lot.side_length(a, b), "m")))
                item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.CheckState.Checked if k in chosen else QtCore.Qt.CheckState.Unchecked)
                self.fronts.addItem(item)
            rows = max(1, min(self.fronts.count(), 6))          # (as tall as its sides, up to six)
            self.fronts.setFixedHeight(rows * self.fronts.sizeHintForRow(0) + 2 * self.fronts.frameWidth() + 4)
            box.addWidget(QtWidgets.QLabel(t("verify.settings.fronts")))
            box.addWidget(self.fronts)
            auto = QtWidgets.QLabel(t("verify.settings.front_auto"))
            auto.setStyleSheet("color: %s;" % theme.C["note"])
            box.addWidget(auto)
        else:
            self.fronts.hide()
        values = settings.get("pdm") or {}
        form = QtWidgets.QFormLayout()
        self.plan_name = QtWidgets.QLineEdit(values.get("name") or "")
        self.plan_name.setPlaceholderText(t("verify.settings.plan_name_hint"))
        form.addRow(t("verify.settings.plan_name"), self.plan_name)
        self.plan_fields = {}
        units = {"m": " (m)", "m2": " (m²)", "": ""}
        for key, measure, _side, unit in project.PLAN_FIELDS:
            edit = QtWidgets.QLineEdit("" if values.get(key) is None else
                                       "{:g}".format(float(values[key])).replace(".", decimal_sep()))
            edit.setPlaceholderText(t("verify.settings.plan_none"))
            now = s.get(measure)
            if now is not None:                             # (what the project has now, beside it)
                edit.setToolTip(t("verify.m." + measure) + ": " + check_mod.number(now, unit))
            self.plan_fields[key] = edit
            form.addRow(t("verify.plan.f." + key) + units.get(unit, ""), edit)
        box.addLayout(form)
        note = QtWidgets.QLabel(t("verify.settings.plan_note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.C["note"])
        box.addWidget(note)
        box.addStretch(1)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setWidget(page)
        return scroll

    def plan(self):
        """The town plan's values typed ({"name", key: value}; empty fields left out)."""
        from ..verify import expr
        out = {}
        name = self.plan_name.text().strip()
        if name:
            out["name"] = name
        for key, edit in self.plan_fields.items():
            text = edit.text().strip()
            if text:
                value = expr.try_evaluate(text)
                if value is not None:
                    out[key] = round(float(value), 4)
        return out

    def chosen_fronts(self):
        """The sides ticked as the front ([] none: automatic), or None (no lot)."""
        if self.lot is None:
            return None
        return [k for k in range(self.fronts.count())
                if self.fronts.item(k).checkState() == QtCore.Qt.CheckState.Checked]

    def _fill_packs(self):
        self.packs.clear()
        s = {"country": self.country.currentData(), "packs": None, "on": True,
             "good_practice": self.good_practice.isChecked() if hasattr(self, "good_practice") else True}
        for pack, own in project.active(s, self.all_packs):
            if pack.id == project.PLAN_PACK:                # (its own page)
                continue
            text = "{} — {} ({})".format(pack.short, pack.title, t("verify.settings.rules", n=len(pack.rules)))
            if not own:
                text += " — " + t("verify.settings.supplementary")
            item = QtWidgets.QTreeWidgetItem([text])
            item.setToolTip(0, "{}\n{}".format(pack.instrument, pack.source))
            self.packs.addTopLevelItem(item)

    def values(self):
        from ..core.units import parse_length
        text = self.height.text().strip()
        height = parse_length(text) if text else None
        return {"country": self.country.currentData(), "building_use": self.use.currentData(),
                "work": self.work.currentData(), "height": height, "packs": None, "on": True,
                "good_practice": self.good_practice.isChecked(), "pdm": self.plan()}


def ask(parent, settings, auto_height, lot=None, summary=None):
    """The dialog; (the settings chosen, the lot's front sides ticked — None: no lot), or None (cancelled)."""
    dialog = VerifySettings(parent, settings, auto_height, lot, summary)
    parent._verify_dialog = dialog                      # (the GUI test fills it in)
    try:
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return None
    finally:
        parent._verify_dialog = None
    QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue("verificacao/pais", dialog.values()["country"] or "")
    return dialog.values(), dialog.chosen_fronts()
