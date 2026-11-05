"""View ▸ Graphic styles… (0.126): the project's hatches and pens on paper (model/graphic_styles.py) — a row per
kind of material cut (its pattern, colour, angle, spacing in mm) and the width of each pen; a little preview of
each hatch as it prints."""

import math

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..model import graphic_styles as styles_model
from . import pattern_paint
from . import theme


class _Swatch(QtWidgets.QWidget):
    """A material's hatch as it prints, a square of paper (painted from the row's settings)."""

    def __init__(self, row):
        super().__init__()
        self.row = row
        self.setFixedSize(40, 24)

    def paintEvent(self, _event):
        style = {"hatches": {"other": self.row.value()}}
        fill, angles, spacing = styles_model.hatch(style, "other")
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), QtGui.QColor(fill))
        library = styles_model.library_pattern(style, "other")          # (0.314)
        if library:
            path = QtGui.QPainterPath()
            path.addRect(QtCore.QRectF(self.rect()))
            p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            pattern_paint.paint(p, path, library, "black", pattern_paint.SAMPLE_MM, 1.0)
        p.setPen(QtGui.QPen(QtGui.QColor("black"), 1.0))
        step = max(spacing * 3.0, 2.0)                    # (about 3 pixels a mm)
        for a in angles:
            d = QtCore.QPointF(math.cos(math.radians(a)), -math.sin(math.radians(a)))
            n = QtCore.QPointF(-d.y(), d.x())
            c = QtCore.QPointF(self.width() / 2, self.height() / 2)
            for k in range(-20, 21):
                q = c + n * (k * step)
                p.drawLine(q - d * 60, q + d * 60)
        p.setPen(QtGui.QPen(QtGui.QColor("#555555"), 1.0))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))
        p.end()


class _Row:
    """One kind of material's settings in the dialog."""

    def __init__(self, dialog, key, value):
        self.key = key
        self.pattern = QtWidgets.QComboBox()
        for name in styles_model.patterns():                  # (0.318: and the project's own)
            if name.startswith("pat:"):                       # (0.314: the drafting patterns of core.patterns)
                self.pattern.addItem(pattern_paint.name(name[4:]), name)
            else:
                self.pattern.addItem(t("gstyle.pattern." + name), name)
        self.pattern.setCurrentIndex(max(0, self.pattern.findData(value["pattern"])))
        self.colour = QtWidgets.QPushButton()
        self.colour.setFixedWidth(64)
        self._fill = value["fill"]
        self._paint_button()
        self.colour.clicked.connect(lambda: self._pick(dialog))
        self.angle = QtWidgets.QDoubleSpinBox()
        self.angle.setRange(-90.0, 90.0)
        self.angle.setDecimals(0)
        self.angle.setSuffix("°")
        self.angle.setValue(value["angle"])
        self.spacing = QtWidgets.QDoubleSpinBox()
        self.spacing.setRange(0.3, 10.0)
        self.spacing.setDecimals(1)
        self.spacing.setSingleStep(0.1)
        self.spacing.setSuffix(" mm")
        self.spacing.setValue(value["spacing"])
        self.swatch = _Swatch(self)
        for signal in (self.pattern.currentIndexChanged, self.angle.valueChanged, self.spacing.valueChanged):
            signal.connect(lambda *_a: self.swatch.update())
        self.pattern.currentIndexChanged.connect(lambda _i: self._sizes())
        self._sizes()

    def _sizes(self):
        """(0.314) A pattern of the library has its own sizes: no angle nor spacing to give it."""
        own = str(self.pattern.currentData()).startswith("pat:")
        self.angle.setEnabled(not own)
        self.spacing.setEnabled(not own)

    def _paint_button(self):
        ink = "#000000" if QtGui.QColor(self._fill).lightnessF() > 0.5 else "#ffffff"    # (0.340: readable on it)
        self.colour.setStyleSheet("QPushButton {{ background: {}; color: {}; border: 1px solid #777; }}"
                                  .format(self._fill, ink))
        self.colour.setText(self._fill)

    def _pick(self, dialog):
        chosen = QtWidgets.QColorDialog.getColor(QtGui.QColor(self._fill), dialog, t("gstyle.colour"))
        if chosen.isValid():
            self.set_fill(chosen.name())

    def set_fill(self, colour):
        self._fill = colour
        self._paint_button()
        self.swatch.update()

    def value(self):
        return {"fill": self._fill, "pattern": self.pattern.currentData(), "angle": self.angle.value(),
                "spacing": self.spacing.value()}


class GraphicStylesDialog(QtWidgets.QDialog):
    def __init__(self, parent, style):
        super().__init__(parent)
        self.setWindowTitle(t("gstyle.title"))
        layout = QtWidgets.QVBoxLayout(self)
        note = QtWidgets.QLabel(t("gstyle.note"))
        note.setWordWrap(True)
        note.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        layout.addWidget(note)
        grid = QtWidgets.QGridLayout()
        for c, head in enumerate(("gstyle.material", "gstyle.pattern", "gstyle.colour", "gstyle.angle",
                                  "gstyle.spacing", "gstyle.preview")):
            label = QtWidgets.QLabel(t(head))
            label.setStyleSheet("QLabel { font-weight: bold; }")
            grid.addWidget(label, 0, c)
        self.rows = {}
        for r, key in enumerate(styles_model.MATERIALS, start=1):
            row = _Row(self, key, style["hatches"][key])
            self.rows[key] = row
            grid.addWidget(QtWidgets.QLabel(t("gstyle.mat." + key)), r, 0)
            for c, w in enumerate((row.pattern, row.colour, row.angle, row.spacing, row.swatch), start=1):
                grid.addWidget(w, r, c)
        layout.addLayout(grid)
        pens = QtWidgets.QGroupBox(t("gstyle.pens"))
        form = QtWidgets.QFormLayout(pens)
        self.pens = {}
        for key in styles_model.PENS:
            box = QtWidgets.QDoubleSpinBox()
            box.setRange(0.05, 2.0)
            box.setDecimals(2)
            box.setSingleStep(0.05)
            box.setSuffix(" mm")
            box.setValue(style["pens"][key])
            self.pens[key] = box
            form.addRow(t("gstyle.pen." + key), box)
        layout.addWidget(pens)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel
                                             | QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults).setText(t("gstyle.defaults"))
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore)
        layout.addWidget(buttons)

    def restore(self):
        """The usual hatches and pens back (as until 0.125)."""
        usual = styles_model.defaults()
        for key, row in self.rows.items():
            value = usual["hatches"][key]
            row.pattern.setCurrentIndex(row.pattern.findData(value["pattern"]))
            row.angle.setValue(value["angle"])
            row.spacing.setValue(value["spacing"])
            row.set_fill(value["fill"])
        for key, box in self.pens.items():
            box.setValue(usual["pens"][key])

    def style(self):
        return {"hatches": {key: row.value() for key, row in self.rows.items()},
                "pens": {key: box.value() for key, box in self.pens.items()}}
