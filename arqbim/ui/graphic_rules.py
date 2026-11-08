"""The Graphic rules panel (Phase 4, step 1): "Colour by" a property — IFC class, type, storey,
material, outside / inside, fire rating, or any property in the file — and the legend: each
value with its colour and how many elements have it. A click on a line selects them."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..model import graphic_rules as rules_model

IDS = QtCore.Qt.ItemDataRole.UserRole


def _swatch(colour):
    pm = QtGui.QPixmap(14, 14)
    pm.fill(QtGui.QColor(colour))
    return QtGui.QIcon(pm)


class RulesPanel(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__(t("rules.title"), parent)
        self.setObjectName("graphic_rules")
        self.on_rule = None          # (key or None)
        self.on_select = None        # ([GlobalIds])
        self.on_properties = None    # () -> [(property set, property)] of the file
        body = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(body)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel(t("rules.colour_by")))
        self.rule = QtWidgets.QComboBox()
        self.rule.addItem(t("rules.none"), None)
        for key in rules_model.RULES:
            self.rule.addItem(rules_model.rule_label(key), key)
        self.rule.addItem(t("rules.other"), "other")
        self.rule.activated.connect(self._rule_chosen)
        row.addWidget(self.rule, 1)
        layout.addLayout(row)
        self.prop = QtWidgets.QComboBox()                  # the property, for "Another property…"
        self.prop.setVisible(False)
        self.prop.activated.connect(lambda _k: self._emit(self.prop.currentData()))
        layout.addWidget(self.prop)
        self.legend = QtWidgets.QTreeWidget()
        self.legend.setHeaderLabels([t("rules.value"), t("rules.count")])
        self.legend.setRootIsDecorated(False)
        self.legend.setToolTip(t("rules.hint"))
        self.legend.itemClicked.connect(self._clicked)
        layout.addWidget(self.legend, 1)
        self.hint = QtWidgets.QLabel(t("rules.hint"))
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)
        self.setWidget(body)

    def _emit(self, key):
        if self.on_rule is not None:
            QtCore.QTimer.singleShot(0, lambda: self.on_rule(tuple(key) if key else None))

    def _rule_chosen(self, _index):
        data = self.rule.currentData()
        self.prop.setVisible(data == "other")
        if data == "other":
            if self.on_properties is not None:
                self.set_properties(self.on_properties())
            if self.prop.count():
                self._emit(self.prop.currentData())
            return
        self._emit(data)

    def set_properties(self, keys):
        """The properties of the file, for "Another property…"."""
        self.prop.clear()
        for pset, prop in keys:
            self.prop.addItem("{} ▸ {}".format(pset, prop), ("pset", pset, prop))

    def show_rule(self, key):
        """Show `key` as the one chosen (a view template set it)."""
        key = tuple(key)
        for i in range(self.rule.count()):
            data = self.rule.itemData(i)
            if data not in (None, "other") and tuple(data) == key:
                self.rule.setCurrentIndex(i)
                self.prop.setVisible(False)
                return
        if key[0] == "pset":
            self.rule.setCurrentIndex(self.rule.count() - 1)          # Another property…
            if self.on_properties is not None:
                self.set_properties(self.on_properties())
            self.prop.setVisible(True)
            for i in range(self.prop.count()):
                if tuple(self.prop.itemData(i)) == key:
                    self.prop.setCurrentIndex(i)

    def reset(self):
        """Back to the usual colours (another file was opened)."""
        self.rule.setCurrentIndex(0)
        self.prop.setVisible(False)
        self.legend.clear()

    def show_legend(self, lines):
        self.legend.clear()
        for label, colour, guids in lines:
            item = QtWidgets.QTreeWidgetItem([label, str(len(guids))])
            item.setIcon(0, _swatch(colour))
            item.setData(0, IDS, guids)
            item.setTextAlignment(1, QtCore.Qt.AlignmentFlag.AlignRight)
            self.legend.addTopLevelItem(item)
        self.legend.resizeColumnToContents(0)

    def _clicked(self, item, _column):
        if self.on_select is not None:
            self.on_select(list(item.data(0, IDS) or []))

    def text(self):
        """The legend as lines (used by tests)."""
        return "\n".join("{} ({})".format(self.legend.topLevelItem(k).text(0), self.legend.topLevelItem(k).text(1))
                         for k in range(self.legend.topLevelItemCount()))


def dock(parent, beside):
    """The panel next to `beside` (the Storeys panel) — (0.461) not as a tab with it: the window puts the left panels in
    view one at a time (MainWindow._build_modules)."""
    panel = RulesPanel(parent)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, panel)
    return panel
