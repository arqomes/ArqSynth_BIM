"""(0.319) Choosing a fill pattern as Revit does: a button showing the pattern chosen (its sample and its name) — in the
materials window's Surface and Cut, in a view style's hatches by category —; clicked, a window with every pattern's
sample, large, the drafting ones (measured on paper) and the model ones (measured on the building) apart, and «None»,
«New…» and «Edit…» (the fill patterns' window, when the program has given one: EDITOR)."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import patterns as core_patterns
from ..i18n import t
from . import pattern_paint

ICON = (96, 44)                    # px: a pattern's sample in the window
BUTTON_ICON = (54, 20)             # px: on the button
# (parent, key or None) -> the key of the pattern chosen there (made, changed), or None: set by the main window
EDITOR = None


class PatternPicker(QtWidgets.QDialog):
    """The patterns to choose from: the drafting ones and the model ones, each a sample and its name."""

    def __init__(self, parent, key=None, model=False, title=None):
        super().__init__(parent)
        self.setWindowTitle(title or t("pick.title"))
        self.key = key
        found = core_patterns.get(key)
        model = found.model if found is not None and not found.solid else model
        layout = QtWidgets.QVBoxLayout(self)
        kinds = QtWidgets.QHBoxLayout()
        self.drafting = QtWidgets.QRadioButton(t("pick.drafting"))
        self.model = QtWidgets.QRadioButton(t("pick.model"))
        (self.model if model else self.drafting).setChecked(True)
        kinds.addWidget(self.drafting)
        kinds.addWidget(self.model)
        kinds.addStretch(1)
        layout.addLayout(kinds)
        self.list = QtWidgets.QListWidget()
        self.list.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self.list.setIconSize(QtCore.QSize(*ICON))
        self.list.setGridSize(QtCore.QSize(ICON[0] + 34, ICON[1] + 44))
        self.list.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.list.setMovement(QtWidgets.QListView.Movement.Static)
        self.list.setWordWrap(True)
        self.list.setSpacing(4)
        self.list.itemDoubleClicked.connect(lambda _i: self.accept())
        layout.addWidget(self.list, 1)
        row = QtWidgets.QHBoxLayout()
        self.none = QtWidgets.QPushButton(t("pick.none"))
        self.none.clicked.connect(self.choose_none)
        self.new = QtWidgets.QPushButton(t("pick.new"))
        self.new.clicked.connect(lambda: self._edit(new=True))
        self.edit = QtWidgets.QPushButton(t("pick.edit"))
        self.edit.clicked.connect(lambda: self._edit())
        for b in (self.new, self.edit):
            b.setVisible(EDITOR is not None)
        row.addWidget(self.none)
        row.addStretch(1)
        row.addWidget(self.new)
        row.addWidget(self.edit)
        layout.addLayout(row)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.drafting.toggled.connect(lambda _on: self._fill())
        self.resize(640, 520)
        self._fill()

    def _keys(self):
        return core_patterns.model_keys() if self.model.isChecked() else core_patterns.drafting_keys()

    def _fill(self):
        self.list.clear()
        mm = 1.0 if self.model.isChecked() else pattern_paint.SAMPLE_MM
        for key in self._keys():
            image = pattern_paint.sample(None, (key, "#2b2f36"), ICON, mm=mm)
            item = QtWidgets.QListWidgetItem(QtGui.QIcon(image), pattern_paint.name(key))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, key)
            item.setToolTip(pattern_paint.name(key))
            self.list.addItem(item)
            if key == self.key:
                self.list.setCurrentItem(item)

    def chosen(self):
        """The key chosen (None: none)."""
        item = self.list.currentItem()
        return item.data(QtCore.Qt.ItemDataRole.UserRole) if item is not None else self.key

    def choose(self, key):
        """A pattern chosen (also from a test): its kind shown, it picked."""
        found = core_patterns.get(key)
        if found is not None and not found.solid:
            (self.model if found.model else self.drafting).setChecked(True)
        self.key = key
        self._fill()

    def choose_none(self):
        self.key = None
        self.list.setCurrentItem(None)
        self.list.clearSelection()
        self.done(QtWidgets.QDialog.DialogCode.Accepted.value)

    def accept(self):
        if self.list.currentItem() is not None:
            self.key = self.chosen()
        super().accept()

    def _edit(self, new=False):
        """The fill patterns' window (EDITOR): a new one made there, or the one chosen changed; back here, it chosen."""
        if EDITOR is None:
            return
        made = EDITOR(self, None if new else self.chosen(), new)
        if made is not None:
            self.choose(made)
        else:
            self._fill()


class PatternButton(QtWidgets.QPushButton):
    """A pattern chosen, shown by its sample and its name; clicked, the PatternPicker. As PatternCombo was: key(),
    set_key(), refill(); `changed` when another is chosen."""

    changed = QtCore.Signal()

    def __init__(self, model=False, parent=None):
        super().__init__(parent)
        self.model = model                       # (the kind shown first: a surface's model patterns, a cut's drafting)
        self._key = None
        self.setIconSize(QtCore.QSize(*BUTTON_ICON))
        self.setMinimumWidth(190)
        self.setToolTip(t("pick.tip"))
        self.setStyleSheet("QPushButton { text-align: left; padding: 2px 6px; }")
        self.clicked.connect(self.pick)
        self.refill()

    def key(self):
        return self._key

    def set_key(self, key):
        self._key = key if core_patterns.get(key) is not None else None
        self.refill()

    def refill(self):
        """Its sample and name again (the pattern itself may have been changed)."""
        if self._key is not None and core_patterns.get(self._key) is None:
            self._key = None
        self.setIcon(pattern_paint.icon(self._key, BUTTON_ICON) if self._key else QtGui.QIcon())
        self.setText(pattern_paint.name(self._key) + "  ▾")

    def pick(self):
        picker = PatternPicker(self.window(), self._key, self.model)
        self._picker = picker                    # (tests)
        chosen = picker.exec() == QtWidgets.QDialog.DialogCode.Accepted
        self._picker = None
        if chosen and picker.key != self._key:
            self.set_key(picker.key)
        else:
            self.refill()                        # (the pattern itself may have been changed there)
        self.changed.emit()
