"""Verificar a instalação elétrica (0.147): the problems found on the active storey, one per line (what is missing or
wrong); a double-click on one selects what it is about. «Verificar outra vez» looks again (after a correction)."""

from PySide6 import QtCore, QtWidgets

from ..i18n import t

GUIDS = QtCore.Qt.ItemDataRole.UserRole


class ElectricalCheckDialog(QtWidgets.QDialog):
    def __init__(self, parent, find):
        """find() -> [(what, text, GlobalIds)] (model/electrical_check.problems)."""
        super().__init__(parent)
        self.setWindowTitle(t("elcheck.title"))
        self.find = find
        self.on_select = None           # (GlobalIds) -> None
        layout = QtWidgets.QVBoxLayout(self)
        self.summary = QtWidgets.QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.list = QtWidgets.QListWidget()
        self.list.itemDoubleClicked.connect(self._chosen)
        layout.addWidget(self.list, 1)
        buttons = QtWidgets.QHBoxLayout()
        again = QtWidgets.QPushButton(t("elcheck.again"))
        again.clicked.connect(self.refresh)
        close = QtWidgets.QPushButton(t("elprop.close"))
        close.clicked.connect(self.accept)
        buttons.addWidget(again)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(620, 380)
        self.refresh()

    def refresh(self):
        found = self.find()
        self.list.clear()
        for _what, text, guids in found:
            item = QtWidgets.QListWidgetItem(text)
            item.setData(GUIDS, list(guids))
            self.list.addItem(item)
        self.summary.setText(t("elcheck.ok") if not found else t("elcheck.found", n=len(found)))
        self.found = found

    def _chosen(self, item):
        if self.on_select is not None:
            self.on_select(item.data(GUIDS) or [])
