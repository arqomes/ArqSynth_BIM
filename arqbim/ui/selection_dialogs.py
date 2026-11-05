"""Selection windows (0.76), as Revit's and AutoCAD's: the Filter of what is selected (its categories, with how
many of each, ticked off), what can be selected at all, and Select by… a category, type, material, storey,
phase or any property's value — in the view or in the whole project."""

from PySide6 import QtCore, QtWidgets

from ..i18n import t

CHECKED, UNCHECKED = QtCore.Qt.CheckState.Checked, QtCore.Qt.CheckState.Unchecked
KEY = QtCore.Qt.ItemDataRole.UserRole


def category_text(category):
    """A category's name for people: "Paredes", "Esboços", "Eixos"…"""
    if category == "sketch":
        return t("sel.cat.sketch")
    if category == "grid":
        return t("sel.cat.grid")
    from .project_tree import category_label
    return category_label(category)


class CheckList(QtWidgets.QListWidget):
    """A list of things to tick: [(text, key, ticked)]; `ticked()` gives the keys ticked."""

    def fill(self, rows):
        self.clear()
        for text, key, on in rows:
            item = QtWidgets.QListWidgetItem(text)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(CHECKED if on else UNCHECKED)
            item.setData(KEY, key)
            self.addItem(item)

    def ticked(self):
        return [self.item(k).data(KEY) for k in range(self.count()) if self.item(k).checkState() == CHECKED]

    def tick_all(self, on=True):
        for k in range(self.count()):
            self.item(k).setCheckState(CHECKED if on else UNCHECKED)


def _buttons(dialog, layout, checklist):
    row = QtWidgets.QHBoxLayout()
    for text, on in ((t("sel.tick_all"), True), (t("sel.tick_none"), False)):
        button = QtWidgets.QPushButton(text)
        button.clicked.connect(lambda _c=False, v=on: checklist.tick_all(v))
        row.addWidget(button)
    row.addStretch(1)
    layout.addLayout(row)
    box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                     | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    box.accepted.connect(dialog.accept)
    box.rejected.connect(dialog.reject)
    layout.addWidget(box)


class CategoryDialog(QtWidgets.QDialog):
    """Ticks per category: the Filter (what is selected: {category: how many}, all ticked) or the Selectable
    categories ({category: how many in the model}, ticked when they can be selected)."""

    def __init__(self, parent, title, note, counts, ticked):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(380)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(note)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.list = CheckList()
        rows = sorted(((category_text(c), c, n) for c, n in counts.items()), key=lambda r: r[0].lower())
        self.list.fill([("{}  ({})".format(text, n), c, c in ticked) for text, c, n in rows])
        layout.addWidget(self.list, 1)
        _buttons(self, layout, self.list)


class SelectByDialog(QtWidgets.QDialog):
    """Select by…: a criterion (category, type, material, storey, phase, IsExternal, fire rating or a property),
    its values found (with how many have each) to tick, where (the view or the whole project) and whether the
    elements found replace the selection or join it. `values(key, scope)` -> [(label, value, count)]."""

    def __init__(self, parent, criteria, values):
        super().__init__(parent)
        self.setWindowTitle(t("sel.by_title"))
        self.setMinimumSize(460, 420)
        self._values = values
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        self.criterion = QtWidgets.QComboBox()
        self._keys = [key for _label, key in criteria]       # (a tuple does not go through Qt's item data)
        for label, _key in criteria:
            self.criterion.addItem(label)
        form.addRow(t("sel.by_criterion"), self.criterion)
        self.scope = QtWidgets.QComboBox()
        self.scope.addItem(t("sel.scope_view"), "view")
        self.scope.addItem(t("sel.scope_project"), "project")
        form.addRow(t("sel.scope"), self.scope)
        layout.addLayout(form)
        self.list = CheckList()
        layout.addWidget(self.list, 1)
        self.add = QtWidgets.QCheckBox(t("sel.add_to_selection"))
        layout.addWidget(self.add)
        _buttons(self, layout, self.list)
        self.criterion.currentIndexChanged.connect(lambda _k: self._refill())
        self.scope.currentIndexChanged.connect(lambda _k: self._refill())
        self._refill()

    def key(self):
        return self._keys[self.criterion.currentIndex()]

    def set_key(self, key):
        self.criterion.setCurrentIndex(self._keys.index(key))

    def _refill(self):
        rows = self._values(self.key(), self.scope.currentData())
        self.list.fill([("{}  ({})".format(label, n), value, False) for label, value, n in rows])

    def choice(self):
        """(criterion key, values ticked, scope, add to the selection?)"""
        return self.key(), self.list.ticked(), self.scope.currentData(), self.add.isChecked()
