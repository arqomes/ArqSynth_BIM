"""(0.426) «Editor de regulamentos»: the packs of rules, the program's and the architect's own — a pack's rules in a
table, their limits, how serious, whether checked against the published text, whether checked at all — and a
country's packs duplicated as another country's (Angola, Brasil, São Tomé…: the CTE of Cabo Verde as a start).

The program's packs are never changed: a change is saved as the architect's own copy of it (the same id: it wins),
in the folder of the architect's packs; «Repor o original» takes the copy away."""

import copy
import json
import os

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import lang, t
from ..verify import project
from ..verify import rules as rules_mod
from . import theme

COLUMNS = ("article", "title", "measure", "limit", "severity", "confirmed", "on")
UNITS = {"m": "m", "m2": "m²", "%": "%"}


def _limit_text(data):
    for key in ("min", "max"):
        if key in data:
            unit = UNITS.get(data.get("unit", ""), "") if isinstance(data[key], (int, float)) else ""
            return "{} {}{}".format(t("verify.side." + key), _number(data[key]), " " + unit if unit else "")
    for key in ("min_table", "max_table", "min_rank"):
        if key in data:
            return t("regs.table_limit")
    return ""


def _plain_limit(text):
    """What was typed in a limit's cell, without «mínimo»/«máximo» and the unit: «12,5», «max(5; …)»."""
    import re
    text = text.strip()
    for word in (t("verify.side.min"), t("verify.side.max")):
        if text.lower().startswith(word.lower()):
            text = text[len(word):].strip()
    return re.sub(r"\s*(m²|m2|m|%)\s*$", "", text).strip()


def _number(value):
    if isinstance(value, (int, float)):
        return "{:g}".format(value).replace(".", "," if lang() == "pt" else ".")
    return str(value)


class RulesEditor(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(t("regs.title"))
        self.resize(1240, 640)
        self.data = None                # the pack shown, as its JSON (a dict) — changed here until saved
        self.path = None                # where it is read from
        self.dirty = False
        split = QtWidgets.QSplitter()
        left = QtWidgets.QWidget()
        lbox = QtWidgets.QVBoxLayout(left)
        self.packs = QtWidgets.QTreeWidget()
        self.packs.setHeaderHidden(True)
        self.packs.currentItemChanged.connect(lambda *_a: self._choose())
        lbox.addWidget(self.packs, 1)
        for key, slot in (("regs.duplicate", self._duplicate), ("regs.new_country", self._new_country),
                          ("regs.restore", self._restore), ("regs.folder", self._open_folder)):
            button = QtWidgets.QPushButton(t(key))
            button.clicked.connect(slot)
            lbox.addWidget(button)
            setattr(self, key.split(".")[1] + "_button", button)
        split.addWidget(left)
        right = QtWidgets.QWidget()
        rbox = QtWidgets.QVBoxLayout(right)
        self.head = QtWidgets.QLabel("")
        self.head.setWordWrap(True)
        rbox.addWidget(self.head)
        self.table = QtWidgets.QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([t("regs.col." + c) for c in COLUMNS])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setVisible(False)
        self.table.itemChanged.connect(self._edited)
        rbox.addWidget(self.table, 1)
        note = QtWidgets.QLabel(t("regs.note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.C["note"])
        rbox.addWidget(note)
        split.addWidget(right)
        split.setSizes([220, 1000])
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Save
                                             | QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        outer = QtWidgets.QVBoxLayout(self)
        outer.addWidget(split, 1)
        outer.addWidget(buttons)
        self._fill()

    # ------------------------------------------------------------ the packs
    def _fill(self, select=None):
        self.packs.clear()
        language = lang()
        by_country = {}
        for pack in rules_mod.packs(again=True).values():
            by_country.setdefault(pack.country, []).append(pack)
        for country in sorted(by_country, key=lambda c: (c == "*", c)):
            name = project.country_name(country, language) if country != "*" and not country.startswith("@") \
                else t("regs.any_country")                  # (0.431: the model's warnings, any country too)
            top = QtWidgets.QTreeWidgetItem([name])
            top.setFlags(top.flags() & ~QtCore.Qt.ItemFlag.ItemIsSelectable)
            self.packs.addTopLevelItem(top)
            for pack in sorted(by_country[country], key=lambda p: p.id):
                own = rules_mod.is_users(pack)
                item = QtWidgets.QTreeWidgetItem(["{}{}".format(pack.short,
                                                                "  ({})".format(t("regs.yours")) if own else "")])
                item.setData(0, QtCore.Qt.ItemDataRole.UserRole, pack.id)
                item.setToolTip(0, "{}\n{}\n{}".format(pack.title, pack.instrument, pack.path))
                top.addChild(item)
                if pack.id == select:
                    self.packs.setCurrentItem(item)
            top.setExpanded(True)
        if self.packs.currentItem() is None and self.packs.topLevelItemCount():
            first = self.packs.topLevelItem(0)
            if first.childCount():
                self.packs.setCurrentItem(first.child(0))

    def current_id(self):
        item = self.packs.currentItem()
        return item.data(0, QtCore.Qt.ItemDataRole.UserRole) if item is not None else None

    def _choose(self):
        if self.dirty and not self._ask_save():
            return
        pack = rules_mod.find(self.current_id()) if self.current_id() else None
        if pack is None:
            self.data, self.path = None, None
            self.table.setRowCount(0)
            self.head.setText("")
            return
        with open(pack.path, encoding="utf-8") as f:
            self.data = json.load(f)
        self.path = pack.path
        self.head.setText(t("regs.head", short=pack.short, title=pack.title, instrument=pack.instrument,
                            whose=t("regs.yours") if rules_mod.is_users(pack) else t("regs.programs")))
        self.restore_button.setEnabled(rules_mod.is_users(pack) and rules_mod.has_builtin(pack.id))
        self._rules()

    def _rules(self):
        self.table.blockSignals(True)
        rules = self.data.get("rules", [])
        self.table.setRowCount(len(rules))
        for row, rule in enumerate(rules):
            values = (rule.get("article", ""), rule.get("title", ""), t("verify.m." + rule.get("measure", "")),
                      _limit_text(rule), None, None, None)
            for col, value in enumerate(values):
                key = COLUMNS[col]
                if key == "severity":
                    combo = QtWidgets.QComboBox()
                    for s in rules_mod.SEVERITIES:
                        combo.addItem(t("regs.severity." + s), s)
                    combo.setCurrentIndex(max(0, combo.findData(rule.get("severity", "error"))))
                    combo.currentIndexChanged.connect(lambda _k, r=row, c=combo: self._set(r, "severity",
                                                                                           c.currentData()))
                    self.table.setCellWidget(row, col, combo)
                    continue
                item = QtWidgets.QTableWidgetItem("" if value is None else str(value))
                if key in ("confirmed", "on"):
                    item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                    checked = rule.get("confirmed", False) if key == "confirmed" else not rule.get("off", False)
                    item.setCheckState(QtCore.Qt.CheckState.Checked if checked else QtCore.Qt.CheckState.Unchecked)
                elif key == "limit" and any(k in rule for k in ("min", "max")):
                    item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
                    item.setToolTip(t("regs.limit_tip"))
                else:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                if key == "title":
                    item.setToolTip("{}\n\n{}".format(rule.get("id", ""), rule.get("text", "")))
                self.table.setItem(row, col, item)
        self._widths()
        self.table.blockSignals(False)

    def _widths(self):
        """The rule's title and its measure as wide as they are given (wrapped), the rest as their contents — so the
        limit, the severity and the ticks are always in sight."""
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        for col, width in ((0, 140), (1, 290), (2, 150), (3, 150)):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeMode.Interactive)
            self.table.setColumnWidth(col, width)
        self.table.setWordWrap(True)
        self.table.resizeRowsToContents()

    def _set(self, row, key, value):
        rule = self.data["rules"][row]
        if rule.get(key) != value:
            rule[key] = value
            self.dirty = True

    def _edited(self, item):
        row, key = item.row(), COLUMNS[item.column()]
        rule = self.data["rules"][row]
        if key == "confirmed":
            self._set(row, "confirmed", item.checkState() == QtCore.Qt.CheckState.Checked)
        elif key == "on":
            on = item.checkState() == QtCore.Qt.CheckState.Checked
            if on:
                if rule.pop("off", None) is not None:
                    self.dirty = True
            else:
                self._set(row, "off", True)
        elif key == "limit":
            side = "min" if "min" in rule else "max"
            text = _plain_limit(item.text())
            from ..verify import expr
            value = expr.try_evaluate(text) if not any(c.isalpha() for c in text) else None
            new = round(float(value), 4) if value is not None else (text or rule[side])
            self._set(row, side, new)
            self.table.blockSignals(True)
            item.setText(_limit_text(rule))
            self.table.blockSignals(False)

    # ------------------------------------------------------------ saved
    def save(self):
        """The pack shown saved as the architect's own (a copy of the program's, by the same id: it wins)."""
        if self.data is None or not self.dirty:
            return True
        path = rules_mod.save_users(self.data)
        self.dirty = False
        rules_mod.packs(again=True)
        self._fill(select=self.data["id"])
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), t("regs.saved", path=path))
        return True

    def _ask_save(self):
        answer = QtWidgets.QMessageBox.question(
            self, t("regs.title"), t("regs.ask_save"),
            QtWidgets.QMessageBox.StandardButton.Save | QtWidgets.QMessageBox.StandardButton.Discard
            | QtWidgets.QMessageBox.StandardButton.Cancel)
        if answer == QtWidgets.QMessageBox.StandardButton.Cancel:
            return False
        if answer == QtWidgets.QMessageBox.StandardButton.Save:
            self.save()
        self.dirty = False
        return True

    def _duplicate(self):
        """The pack shown copied as a new one of the architect's (a new id, «(cópia)»)."""
        if self.data is None:
            return
        data = copy.deepcopy(self.data)
        data["id"] = rules_mod.free_id(data["id"] + "-COPIA")
        data["short"] = "{} ({})".format(data.get("short", data["id"]), t("regs.copy"))
        for rule in data.get("rules", []):
            rule["id"] = "{}~{}".format(data["id"], rule["id"])
        rules_mod.save_users(data)
        rules_mod.packs(again=True)
        self._fill(select=data["id"])

    def _new_country(self, code=None, name=None, source=None):
        """Another country: its code and name, and the country its packs start from (all of them copied, the rules'
        values marked «to be confirmed»)."""
        if code is None:
            dialog = NewCountry(self)
            if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
                return None
            code, name, source = dialog.values()
        made = rules_mod.new_country(code, name, source)
        project.forget_countries()
        rules_mod.packs(again=True)
        self._fill(select=made[0] if made else None)
        return made

    def _restore(self):
        pack_id = self.current_id()
        if pack_id and rules_mod.remove_users(pack_id):
            rules_mod.packs(again=True)
            self.dirty = False
            self._fill(select=pack_id)

    def _open_folder(self):
        folder = rules_mod.user_folder()
        os.makedirs(folder, exist_ok=True)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))

    def reject(self):
        if self.dirty and not self._ask_save():
            return
        super().reject()


class NewCountry(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(t("regs.new_country"))
        form = QtWidgets.QFormLayout(self)
        self.code = QtWidgets.QLineEdit()
        self.code.setMaxLength(3)
        self.code.setPlaceholderText("AO")
        self.name = QtWidgets.QLineEdit()
        self.name.setPlaceholderText("Angola")
        self.source = QtWidgets.QComboBox()
        language = lang()
        for code in project.countries():
            self.source.addItem(project.country_name(code, language), code)
        form.addRow(t("regs.country_code"), self.code)
        form.addRow(t("regs.country_name"), self.name)
        form.addRow(t("regs.country_from"), self.source)
        note = QtWidgets.QLabel(t("regs.country_note"))
        note.setWordWrap(True)
        form.addRow(note)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._ok)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _ok(self):
        if self.code.text().strip() and self.name.text().strip():
            self.accept()

    def values(self):
        return self.code.text().strip().upper(), self.name.text().strip(), self.source.currentData()
