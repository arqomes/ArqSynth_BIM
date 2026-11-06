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
    def __init__(self, parent, settings, auto_height):
        super().__init__(parent)
        self.setWindowTitle(t("verify.settings.title"))
        self.setMinimumWidth(520)
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
        box = QtWidgets.QVBoxLayout(self)
        box.addLayout(form)
        box.addWidget(QtWidgets.QLabel(t("verify.settings.packs")))
        box.addWidget(self.packs)
        box.addWidget(self.good_practice)
        note = QtWidgets.QLabel(t("verify.settings.note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.C["note"])
        box.addWidget(note)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        box.addWidget(buttons)
        self.country.currentIndexChanged.connect(lambda _k: self._fill_packs())
        self._fill_packs()

    def _fill_packs(self):
        self.packs.clear()
        s = {"country": self.country.currentData(), "packs": None, "on": True,
             "good_practice": self.good_practice.isChecked() if hasattr(self, "good_practice") else True}
        for pack, own in project.active(s, self.all_packs):
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
                "good_practice": self.good_practice.isChecked()}


def ask(parent, settings, auto_height):
    """The dialog; the settings chosen, or None (cancelled)."""
    dialog = VerifySettings(parent, settings, auto_height)
    if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
        return None
    QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue("verificacao/pais", dialog.values()["country"] or "")
    return dialog.values()
