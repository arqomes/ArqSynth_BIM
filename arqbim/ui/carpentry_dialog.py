"""A roof's carpentry, its sizes chosen (0.277): the rafters' spacing, the tile's gauge (the battens'), the most a
rafter spans between purlins, and each kind of piece's section (width × height). Applying makes it again under the
roof with them (one undo step, done by the window: on_apply)."""

from PySide6 import QtWidgets

from ..core import roof_carpentry as core_carpentry
from ..core.units import format_length, parse_length
from ..i18n import decimal_sep, t
from . import theme


def _len(value):
    return format_length(value, decimal_sep(), 3).replace("~ ", "")


class CarpentryDialog(QtWidgets.QDialog):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.setWindowTitle(t("carpdlg.title"))
        self.on_apply = None                # (Settings) -> True if made
        form = QtWidgets.QFormLayout(self)
        note = QtWidgets.QLabel(t("carpdlg.note"))
        note.setWordWrap(True)
        form.addRow(note)
        self.spacing = QtWidgets.QLineEdit(_len(settings.rafter_spacing))
        self.gauge = QtWidgets.QLineEdit(_len(settings.gauge))
        self.span = QtWidgets.QLineEdit(_len(settings.purlin_span))
        form.addRow(t("carpdlg.spacing"), self.spacing)
        form.addRow(t("carpdlg.gauge"), self.gauge)
        form.addRow(t("carpdlg.span"), self.span)
        self.sections = {}
        for role in core_carpentry.ROLES:
            w, h = settings.section(role)
            width, height = QtWidgets.QLineEdit(_len(w)), QtWidgets.QLineEdit(_len(h))
            row = QtWidgets.QHBoxLayout()
            row.addWidget(width)
            row.addWidget(QtWidgets.QLabel("×"))
            row.addWidget(height)
            form.addRow(t("carp." + role), row)
            self.sections[role] = (width, height)
        self.problem = QtWidgets.QLabel("")
        self.problem.setStyleSheet("color: %s;" % theme.C["fail"])
        form.addRow(self.problem)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText(t("carpdlg.apply"))
        buttons.accepted.connect(self.apply)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def settings(self):
        """The settings as typed, or None (a value that is not a length, or not over zero)."""
        values = [parse_length(w.text()) for w in (self.spacing, self.gauge, self.span)]
        sections = {}
        for role, (w, h) in self.sections.items():
            pair = (parse_length(w.text()), parse_length(h.text()))
            if None in pair or min(pair) <= 0:
                return None
            sections[role] = pair
        if None in values or min(values) <= 0.01:
            return None
        return core_carpentry.Settings(rafter_spacing=values[0], gauge=values[1], purlin_span=values[2],
                                       sections=tuple(sorted(sections.items())))

    def apply(self):
        found = self.settings()
        if found is None:
            self.problem.setText(t("carpdlg.bad"))
            return False
        if self.on_apply is not None and self.on_apply(found):
            self.accept()
            return True
        return False
