"""A tile of the user's own (0.281), as the add-on's «Registar telha»: a component measured — its width, length and
height (a size not between 2 cm and 3 m: is it in metres?) — and its laying data from its maker: the cover width
and gauge (90 % and 80 % of its size proposed, as the add-on), its weight, whether its rows are staggered. Applying
registers it (one undo step, done by the window: on_apply)."""

from PySide6 import QtWidgets

from ..core import roof_tiles as core_tiles
from ..core.units import format_length, parse_length
from ..i18n import decimal_sep, t
from . import theme


def _len(value):
    return format_length(value, decimal_sep(), 3).replace("~ ", "")


class TileDialog(QtWidgets.QDialog):
    def __init__(self, parent, name, verts):
        super().__init__(parent)
        self.setWindowTitle(t("tiledlg.title"))
        self.on_apply = None                # (name, cover width, gauge, weight, stagger) -> True if registered
        width, length, height, cover, gauge, warnings = core_tiles.measure(verts)
        self.size = (width, length)
        form = QtWidgets.QFormLayout(self)
        note = QtWidgets.QLabel(t("tiledlg.note"))
        note.setWordWrap(True)
        form.addRow(note)
        form.addRow(t("tiledlg.measured"), QtWidgets.QLabel("{} × {} × {}".format(_len(width), _len(length),
                                                                                  _len(height))))
        self.name = QtWidgets.QLineEdit(name)
        self.cover = QtWidgets.QLineEdit(_len(cover))
        self.gauge = QtWidgets.QLineEdit(_len(gauge))
        self.weight = QtWidgets.QLineEdit("3")
        self.stagger = QtWidgets.QCheckBox(t("props.tiles_stagger"))
        self.stagger.setChecked(True)
        form.addRow(t("tiledlg.name"), self.name)
        form.addRow(t("tiledlg.cover"), self.cover)
        form.addRow(t("tiledlg.gauge"), self.gauge)
        form.addRow(t("tiledlg.weight"), self.weight)
        form.addRow(self.stagger)
        self.problem = QtWidgets.QLabel("\n".join(t("tiledlg.warn." + w) for w in warnings))
        self.problem.setWordWrap(True)
        self.problem.setStyleSheet("color: %s;" % theme.C["fail"])
        form.addRow(self.problem)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText(t("tiledlg.apply"))
        buttons.accepted.connect(self.apply)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        """(name, cover width, gauge, weight, stagger) as typed, or a reason why not (a text)."""
        cover, gauge = parse_length(self.cover.text()), parse_length(self.gauge.text())
        try:
            weight = float(self.weight.text().replace(",", ".").replace("kg", "").strip())
        except ValueError:
            weight = None
        if not self.name.text().strip() or None in (cover, gauge, weight) or weight < 0 or \
                not 0.02 <= cover <= 3.0 or not 0.02 <= gauge <= 3.0:
            return t("tiledlg.bad")
        if cover > self.size[0] + 1e-6 or gauge > self.size[1] + 1e-6:    # (the add-on's warnings, here refused)
            return t("tiledlg.bigger")
        return self.name.text().strip(), cover, gauge, weight, self.stagger.isChecked()

    def apply(self):
        found = self.values()
        if isinstance(found, str):
            self.problem.setText(found)
            return False
        if self.on_apply is not None and self.on_apply(*found):
            self.accept()
            return True
        return False
