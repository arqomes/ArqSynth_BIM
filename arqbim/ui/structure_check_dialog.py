"""Verificar o modelo estrutural (0.163): the analytical model made again and its problems, one per line — errors
first (they stop a calculation), then warnings and notes —; a double-click on one selects what it is about.
«Verificar outra vez» makes it again (after a correction)."""

from PySide6 import QtCore, QtWidgets

from ..core import structural as st
from ..i18n import t
from . import theme

GUIDS = QtCore.Qt.ItemDataRole.UserRole
ORDER = {st.ERROR: 0, st.WARNING: 1, st.INFO: 2}
SEVERITY_KEYS = {st.ERROR: "fail", st.WARNING: "attention", st.INFO: "off_text"}   # (0.339) in the theme's colours


class StructureCheckDialog(QtWidgets.QDialog):
    def __init__(self, parent, make):
        """make() -> core.structural.AnalyticalModel (made again, written to the IFC)."""
        super().__init__(parent)
        self.setWindowTitle(t("struct.title"))
        self.make = make
        self.on_select = None
        layout = QtWidgets.QVBoxLayout(self)
        self.summary = QtWidgets.QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.list = QtWidgets.QListWidget()
        self.list.itemDoubleClicked.connect(self._chosen)
        layout.addWidget(self.list, 1)
        note = QtWidgets.QLabel(t("struct.note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.C["note"])
        layout.addWidget(note)
        buttons = QtWidgets.QHBoxLayout()
        again = QtWidgets.QPushButton(t("struct.again"))
        again.clicked.connect(self.refresh)
        close = QtWidgets.QPushButton(t("elprop.close"))
        close.clicked.connect(self.accept)
        buttons.addWidget(again)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(640, 420)
        self.model = None
        self.refresh()

    def refresh(self):
        self.model = self.make()
        self.list.clear()
        for issue in sorted(self.model.issues, key=lambda i: (ORDER.get(i.severity, 3), i.code)):
            item = QtWidgets.QListWidgetItem("{} — {}".format(t("struct.sev." + issue.severity),
                                                             t("struct.issue." + issue.code)))
            item.setForeground(theme.colour(SEVERITY_KEYS.get(issue.severity, "text")))
            item.setData(GUIDS, list(issue.guids))
            self.list.addItem(item)
        n = st.counts(self.model.issues)
        columns = sum(1 for m in self.model.members if m.kind == "column")
        beams = sum(1 for m in self.model.members if m.kind == "beam")
        self.summary.setText(t("struct.summary", nodes=len(self.model.nodes), c=columns, b=beams,
                               s=len(self.model.supports), p=len(self.model.panels), e=n[st.ERROR],
                               w=n[st.WARNING]))

    def _chosen(self, item):
        if self.on_select is not None:
            self.on_select(item.data(GUIDS) or [])
