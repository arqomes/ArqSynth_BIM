"""The contextual bar (0.85; 0.183: the interface's panel 3), as Revit's Options Bar and the ArqSynth Modeler's
header: under the ribbon, it changes with the tool and with what is selected —

- a drawing tool: its name and its settings, changed right there (the type, the height, the wall's reference
  line, the storey drawn on…), kept in step when they change some other way (Tab, a typed height, a menu);
- Select: the selection's shapes and filters and, with something selected, what it is and the buttons for it.

The window says what goes on it (items); this bar only makes the widgets and says when one is changed."""

from PySide6 import QtCore, QtWidgets

from ..core.units import format_length, parse_length
from ..i18n import decimal_sep
from ..ifc import catalog
from . import shape_icons, theme, type_thumbs

# (0.450) the choices drawn as a row of icons, as Revit's «Draw» panel — a tool's shape, an arc's way of drawing, the
# drawing tools one goes to from another —, when there is an icon for each of their values (ui/shape_icons.py)
ICON_KEYS = ("shape", "mode", "draw")
ICON_PX = 20


def iconic(option):
    """(0.450) Is this choice shown as a row of icons?"""
    return option.kind == "choice" and option.key in ICON_KEYS and len(option.choices) > 1 and \
        all(shape_icons.has(v) for v, _text in option.choices)

def style():
    """(0.183, the interface's panel 3) the window's colour, the tool's icon and name first, the fields framed; one
    written wrong turns red a moment (0.338: the theme's colours)."""
    c = theme.C
    return ("QToolBar#context { background: %s; border: none; border-bottom: 1px solid %s; padding: 2px 8px;"
            " spacing: 4px; }"
            "QLabel#ctx_title { font-weight: 600; color: %s; padding: 0 6px 0 2px; }"
            "QLabel#ctx_label { color: %s; padding: 0 2px 0 8px; }"
            "QLabel#ctx_hint { color: %s; padding: 0 6px; }"
            "QLabel#ctx_text { color: %s; padding: 0 6px; }"
            "QLineEdit, QComboBox { border: 1px solid %s; border-radius: 4px; padding: 2px 6px; min-height: 18px;"
            " background: %s; color: %s; }"
            "QLineEdit:focus, QComboBox:focus { border-color: %s; }"
            "QLineEdit[invalid=\"true\"] { border-color: %s; background: %s; }"
            "QToolBar#context QToolButton { padding: 3px 7px; border-radius: 4px; }"
            "QToolBar#context QToolButton:hover { background: %s; }"
            "QToolBar#context QToolButton:checked { background: %s; }"
            % (c["window"], c["line"], c["text"], c["off_text"], c["hint"], c["ctx_text"], c["edge_2"], c["input"],
               c["text"], c["select"], c["warning"], c["invalid_bg"], c["button_hover"], c["select_soft"]))


INVALID_MS = 1500


def _type_spec(value):
    """(0.313) The catalogue's (or the project's) type whose key is this choice's value, or None."""
    if not isinstance(value, str):
        return None
    return catalog.BY_KEY.get(value) or catalog.OPENING_BY_KEY.get(value)
BAR_HEIGHT = 33                 # px: (0.225) always this tall — its fields', the tallest — the view never moving…
PROBE_HEIGHT = 24               # …round a list of this height (the style's 22 px, its padding and border)


class ContextBar(QtWidgets.QToolBar):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.setMovable(False)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.setStyleSheet(style())
        # (0.225) one height whatever is on it (a tool's fields, Select's buttons, nothing): it used to follow
        # its tallest widget, and the view under it jumped up and down with each tool — a list's height (its
        # tallest field) measured in its style, for larger fonts
        probe = QtWidgets.QComboBox(self)
        probe.hide()
        probe.addItem("Xg")
        probe.ensurePolished()
        self.setFixedHeight(max(BAR_HEIGHT, probe.sizeHint().height() + BAR_HEIGHT - PROBE_HEIGHT))
        probe.deleteLater()
        self.on_option = None         # (key, value): a setting changed here
        self.on_done = None           # a setting was changed: the keyboard back to the view
        self.on_invalid = None        # (0.183) (text): a value written that is not one
        self.fields = {}              # key -> (widget, Option)

    # ------------------------------------------------------------ what is on it

    def show_items(self, items):
        """items: ("title", text[, icon]) | ("text", text) | ("hint", text: grey) | ("action", QAction) |
        ("icon_action", QAction: its icon only, 0.183) | ("separator",) | ("option", Option)."""
        for act in self.actions():
            self.removeAction(act)
            if act.parent() is self:              # (its labels, fields and separators: made again)
                act.deleteLater()
        self.fields = {}
        for item in items:
            kind = item[0]
            if kind == "separator":
                self.addSeparator()
            elif kind == "action":
                self.addAction(item[1])
            elif kind == "icon_action":
                button = QtWidgets.QToolButton(self)
                button.setDefaultAction(item[1])
                button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
                button.setIconSize(QtCore.QSize(18, 18))
                button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
                self.addWidget(button)
            elif kind == "title" and len(item) > 2 and item[2] is not None and not item[2].isNull():
                icon = QtWidgets.QLabel()
                icon.setPixmap(item[2].pixmap(20, 20))
                self.addWidget(icon)
                self.addWidget(self._label(item[1], "ctx_title"))
            elif kind in ("title", "text", "hint"):
                self.addWidget(self._label(item[1], "ctx_" + kind))
            elif kind == "option":
                self._add_option(item[1])

    @staticmethod
    def _label(text, name):
        label = QtWidgets.QLabel(text)
        label.setObjectName(name)
        return label

    def _add_option(self, option):
        if option.kind != "toggle":
            self.addWidget(self._label("{}:".format(option.label), "ctx_label"))
        if iconic(option):
            # (0.450) a row of icons, the one in use lit, each one's name in its tip — as Revit's «Draw» panel
            widget = QtWidgets.QWidget(self)
            widget.setProperty("icons", True)
            row = QtWidgets.QHBoxLayout(widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(1)
            for value, text in option.choices:
                button = QtWidgets.QToolButton(widget)
                button.setIcon(shape_icons.icon(value))
                button.setIconSize(QtCore.QSize(ICON_PX, ICON_PX))
                button.setToolTip(text)
                button.setAutoRaise(True)
                button.setCheckable(True)
                button.setChecked(value == option.value)
                button.setObjectName("ctx_{}_{}".format(option.key, value))
                button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
                button.clicked.connect(lambda _on=False, k=option.key, v=value, b=button: self._picked(k, v, b))
                row.addWidget(button)
        elif option.kind == "choice":
            # (0.313) a choice of types (walls, slabs, doors…): each with its miniature, large in the list
            widget = type_thumbs.TypeCombo() if any(_type_spec(v) for v, _text in option.choices) else \
                QtWidgets.QComboBox()
            widget.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents)
            self._fill(widget, option)
            widget.activated.connect(lambda i, w=widget, k=option.key: self._changed(k, w.itemData(i)))
        elif option.kind == "length":
            widget = QtWidgets.QLineEdit(format_length(option.value, decimal_sep()))
            widget.setFixedWidth(80)
            widget.editingFinished.connect(lambda w=widget, k=option.key: self._typed(k, w))
        elif option.kind == "buttons":
            # (0.410) side by side, the one on lit — a click on another lights it, on the lit one puts it out ("")
            widget = QtWidgets.QWidget(self)
            row = QtWidgets.QHBoxLayout(widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(2)
            for value, text in option.choices:
                button = QtWidgets.QToolButton(widget)
                button.setText(text)
                button.setCheckable(True)
                button.setChecked(value == option.value)
                button.setObjectName("ctx_{}_{}".format(option.key, value))
                button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
                button.clicked.connect(lambda _on=False, k=option.key, v=value: self._changed(
                    k, "" if self.fields[k][1].value == v else v))
                row.addWidget(button)
        else:
            widget = QtWidgets.QCheckBox(option.label)
            widget.setChecked(bool(option.value))
            widget.toggled.connect(lambda on, k=option.key: self._changed(k, on))
        widget.setObjectName("ctx_" + option.key)
        # (only a click gives it the keyboard: the keys typed in the view — a length, Tab, R — stay the tool's)
        widget.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.addWidget(widget)
        self.fields[option.key] = (widget, option)

    @staticmethod
    def _fill(combo, option):
        blocker = QtCore.QSignalBlocker(combo)
        combo.clear()
        for value, text in option.choices:
            spec = _type_spec(value) if isinstance(combo, type_thumbs.TypeCombo) else None
            if spec is not None:
                combo.addItem(type_thumbs.icon(spec), text, value)
            else:
                combo.addItem(text, value)
        combo.setCurrentIndex(max(0, combo.findData(option.value)))
        del blocker

    # ------------------------------------------------------------ kept in step

    def sync(self, options):
        """The tool's settings as they are now (changed with Tab, typed, chosen in a menu). False if they are
        not the ones on the bar (then it is to be made again)."""
        if [o.key for o in options] != list(self.fields):
            return False
        for option in options:
            widget, old = self.fields[option.key]
            self.fields[option.key] = (widget, option)
            blocker = QtCore.QSignalBlocker(widget)
            if widget.property("icons"):                    # (0.450) a row of icons: the one in use lit
                if option.choices != old.choices or not iconic(option):
                    del blocker
                    return False
                for button in widget.findChildren(QtWidgets.QToolButton):
                    button.setChecked(button.objectName() == "ctx_{}_{}".format(option.key, option.value))
            elif option.kind == "choice":
                if option.choices != old.choices:
                    self._fill(widget, option)
                else:
                    widget.setCurrentIndex(max(0, widget.findData(option.value)))
            elif option.kind == "length":
                if not widget.hasFocus():
                    widget.setText(format_length(option.value, decimal_sep()))
            elif option.kind == "buttons":
                for button in widget.findChildren(QtWidgets.QToolButton):
                    button.setChecked(button.objectName() == "ctx_{}_{}".format(option.key, option.value))
            else:
                widget.setChecked(bool(option.value))
            del blocker
        return True

    # ------------------------------------------------------------ changes

    def _typed(self, key, widget):
        text = widget.text()
        value = parse_length(text)
        old = self.fields[key][1].value
        if value is None and text.strip():          # (0.183) not a length: red a moment, and said why
            self._flag(widget)
            if self.on_invalid is not None:
                self.on_invalid(text)
        if value is None or value == old:
            widget.setText(format_length(old, decimal_sep()))
            return
        self._changed(key, value)

    @staticmethod
    def _flag(widget):
        """A field turned red for a moment (a value written wrong)."""
        def mark(on):
            try:
                widget.setProperty("invalid", on)
                widget.style().unpolish(widget)
                widget.style().polish(widget)
            except RuntimeError:                     # (the bar made again meanwhile)
                pass
        mark(True)
        QtCore.QTimer.singleShot(INVALID_MS, lambda: mark(False))

    def _picked(self, key, value, button):
        """(0.450) An icon of a row clicked: that shape (the one in use clicked again stays lit)."""
        if self.fields[key][1].value == value:
            button.setChecked(True)
            return
        self._changed(key, value)

    def _changed(self, key, value):
        if self.on_option is not None:
            self.on_option(key, value)
        if self.on_done is not None:
            self.on_done()
