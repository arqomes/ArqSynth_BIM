"""«Explorar cores» (0.374, the owner's interface study): the interface's nine colours — the bar and background, the
ribbon, the panels, the headers, the accent, the text, the drawing area, the dividers, the fields — tuned live. It
starts from the palette in use (or the study's beige); a preset button puts one of the study's five; each colour by its
picker or its code (#D9C5AE); the result is the owner's own palette («personalizado»), kept on this computer. «Copiar
paleta CSS» copies it as the study does; «Repor bege» puts the beige back."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from . import theme


class ThemeStudio(QtWidgets.QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle(t("act.theme_studio").replace("…", ""))
        self.setModal(False)
        current = theme.C.get("palette")
        self.colours = dict(current) if current else dict(theme.custom_palette() or theme.STUDY["bege"])
        box = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(t("studio.intro"))
        intro.setWordWrap(True)
        box.addWidget(intro)
        presets = QtWidgets.QHBoxLayout()
        for name in theme.STUDY:
            b = QtWidgets.QPushButton(t("act.theme_" + name))
            b.clicked.connect(lambda _=False, n=name: self.preset(n))
            presets.addWidget(b)
        box.addLayout(presets)
        grid = QtWidgets.QGridLayout()
        self.pickers, self.codes = {}, {}
        for k, key in enumerate(theme.TOKENS):
            label = QtWidgets.QLabel(t("studio." + key))
            pick = QtWidgets.QPushButton()
            pick.setFixedSize(34, 24)
            pick.clicked.connect(lambda _=False, c=key: self.pick(c))
            code = QtWidgets.QLineEdit()
            code.setMaxLength(7)
            code.setFixedWidth(84)
            code.editingFinished.connect(lambda c=key: self.typed(c))
            grid.addWidget(label, k // 2, (k % 2) * 3)
            grid.addWidget(pick, k // 2, (k % 2) * 3 + 1)
            grid.addWidget(code, k // 2, (k % 2) * 3 + 2)
            self.pickers[key], self.codes[key] = pick, code
        box.addLayout(grid)
        actions = QtWidgets.QHBoxLayout()
        copy = QtWidgets.QPushButton(t("studio.copy"))
        copy.clicked.connect(self.copy)
        reset = QtWidgets.QPushButton(t("studio.reset"))
        reset.clicked.connect(lambda: self.preset("bege"))
        close = QtWidgets.QPushButton(t("studio.close"))
        close.clicked.connect(self.close)
        for b in (copy, reset):
            actions.addWidget(b)
        actions.addStretch(1)
        actions.addWidget(close)
        box.addLayout(actions)
        self.feedback = QtWidgets.QLabel("")
        box.addWidget(self.feedback)
        self._show()

    def _show(self):
        for key in theme.TOKENS:
            value = self.colours[key]
            self.pickers[key].setStyleSheet("QPushButton { background: %s; border: 1px solid #888; }" % value)
            self.codes[key].setText(value.upper())

    def preset(self, name):
        """One of the study's palettes, put as it is."""
        self.colours = dict(theme.STUDY[name])
        self._show()
        self.win.set_theme(name)
        self.feedback.setText(t("studio.applied"))

    def _apply(self):
        """The colours as they are now: the owner's own palette, kept and in use."""
        theme.keep_palette(self.colours)
        self.win.set_theme(theme.CUSTOM)
        self._show()

    def pick(self, key):
        chosen = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.colours[key]), self, t("studio." + key))
        if chosen.isValid():
            self.set_colour(key, chosen.name())

    def typed(self, key):
        text = self.codes[key].text().strip()
        if not text.startswith("#"):
            text = "#" + text
        if QtCore.QRegularExpression("^#[0-9a-fA-F]{6}$").match(text).hasMatch():
            self.set_colour(key, text.lower())
        else:
            self.codes[key].setText(self.colours[key].upper())
            self.feedback.setText(t("studio.bad_code"))

    def set_colour(self, key, value):
        if self.colours.get(key) == value:
            return
        self.colours[key] = value
        self._apply()
        self.feedback.setText(t("studio.kept"))

    def css(self):
        return ":root {\n" + "\n".join("  --{}: {};".format(k, self.colours[k]) for k in theme.TOKENS) + "\n}"

    def copy(self):
        QtWidgets.QApplication.clipboard().setText(self.css())
        self.feedback.setText(t("studio.copied"))
