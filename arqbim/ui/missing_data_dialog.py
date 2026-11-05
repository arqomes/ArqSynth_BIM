"""Collaborate ▸ Dados IFC em falta… (0.273): before delivering, what the model's elements do not say yet — for each
class (its standard set), each property and how many elements have no value for it (theirs or their type's), the
most missing first; a double click selects them (to fill them in the Properties or their type). «Preencher o que o
programa sabe» writes what it can work out (a model made before, or by another program): one undo step."""

from PySide6 import QtCore, QtWidgets

from ..i18n import has, t

GUIDS = QtCore.Qt.ItemDataRole.UserRole


def _label(prop):
    return t("ifcprop." + prop) if has("ifcprop." + prop) else prop


class MissingDataDialog(QtWidgets.QDialog):
    def __init__(self, parent, doc):
        super().__init__(parent)
        self.setWindowTitle(t("missing.title"))
        self.doc = doc
        self.on_select = None             # (GlobalIds) -> None: the window selects them
        self.on_fill = None               # () -> how many written
        layout = QtWidgets.QVBoxLayout(self)
        note = QtWidgets.QLabel(t("missing.note"))
        note.setWordWrap(True)
        layout.addWidget(note)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels([t("missing.property"), t("missing.without"), t("missing.with")])
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tree.itemDoubleClicked.connect(self._picked)
        layout.addWidget(self.tree, 1)
        self.summary = QtWidgets.QLabel("")
        layout.addWidget(self.summary)
        buttons = QtWidgets.QHBoxLayout()
        self.fill = QtWidgets.QPushButton(t("missing.fill"))
        self.fill.setToolTip(t("missing.fill_tip"))
        self.fill.clicked.connect(self.fill_known)
        self.select = QtWidgets.QPushButton(t("missing.select"))
        self.select.clicked.connect(lambda: self._picked(self.tree.currentItem()))
        close = QtWidgets.QPushButton(t("blocked.close"))
        close.clicked.connect(self.reject)
        buttons.addWidget(self.fill)
        buttons.addStretch(1)
        buttons.addWidget(self.select)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(640, 560)
        self.refresh()

    def refresh(self):
        self.tree.clear()
        found = self.doc.ifc.missing_data()
        holes = 0
        for cls, pset, rows in found:
            total = rows[0][2] if rows else 0
            top = QtWidgets.QTreeWidgetItem([t("missing.class", cls=cls, n=total, pset=pset), "", ""])
            font = top.font(0)
            font.setBold(True)
            top.setFont(0, font)
            self.tree.addTopLevelItem(top)
            top.setFirstColumnSpanned(True)
            for prop, without, n in sorted(rows, key=lambda r: -len(r[1])):
                item = QtWidgets.QTreeWidgetItem([_label(prop), str(len(without)), str(n - len(without))])
                item.setToolTip(0, "{}.{}".format(pset, prop))
                item.setData(0, GUIDS, without)
                top.addChild(item)
                holes += len(without)
            top.setExpanded(len(found) <= 3)
        self.summary.setText(t("missing.summary", n=len(found), holes=holes) if found else t("missing.none"))

    def _picked(self, item):
        guids = item.data(0, GUIDS) if item is not None else None
        if guids and self.on_select is not None:
            self.on_select(list(guids))
            self.accept()

    def fill_known(self):
        n = self.on_fill() if self.on_fill is not None else 0
        self.refresh()
        self.summary.setText(t("missing.filled", n=n) + "  " + self.summary.text())
        return n
