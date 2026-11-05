"""The project's own keynote table (0.248): its codes and their texts, in a table one edits — a row added (or one of
the program's copied, to be changed), a row taken away; OK makes the project's table so (model.bim.set_keynote_table,
one undo step). The program's table stays as it is, beside it: a code given here is offered with this text."""

from PySide6 import QtWidgets

from ..i18n import lang, t
from ..model import keynotes


class KeynoteTableDialog(QtWidgets.QDialog):
    def __init__(self, parent, own):
        """own: {code: text} — the project's table now."""
        super().__init__(parent)
        self.setWindowTitle(t("kntable.title"))
        layout = QtWidgets.QVBoxLayout(self)
        note = QtWidgets.QLabel(t("kntable.note"))
        note.setWordWrap(True)
        layout.addWidget(note)
        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([t("kntable.code"), t("kntable.text")])
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)
        row = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QPushButton(t("kntable.add"))
        self.add_button.clicked.connect(lambda: self.add_row("", ""))
        self.copy = QtWidgets.QComboBox()                       # (one of the program's, to be changed)
        self.copy.addItem(t("kntable.copy"), None)
        for label, code in keynotes.choices(lang()):
            self.copy.addItem(label, code)
        self.copy.activated.connect(self._copied)
        self.remove_button = QtWidgets.QPushButton(t("kntable.remove"))
        self.remove_button.clicked.connect(self._remove)
        row.addWidget(self.add_button)
        row.addWidget(self.copy, 1)
        row.addWidget(self.remove_button)
        layout.addLayout(row)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        for code, text in sorted(own.items()):
            self.add_row(code, text)
        self.resize(640, 420)

    def add_row(self, code, text):
        k = self.table.rowCount()
        self.table.insertRow(k)
        self.table.setItem(k, 0, QtWidgets.QTableWidgetItem(code))
        self.table.setItem(k, 1, QtWidgets.QTableWidgetItem(text))
        return k

    def _copied(self, index):
        code = self.copy.itemData(index)
        if code:
            self.add_row(code, keynotes.text_of(code, lang()))
        self.copy.setCurrentIndex(0)

    def _remove(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for k in rows or ([self.table.rowCount() - 1] if self.table.rowCount() else []):
            self.table.removeRow(k)

    def entries(self):
        """{code: text} as the table has them (rows without a code left out; a code twice: the last)."""
        out = {}
        for k in range(self.table.rowCount()):
            code = (self.table.item(k, 0).text() if self.table.item(k, 0) else "").strip()
            text = (self.table.item(k, 1).text() if self.table.item(k, 1) else "").strip()
            if code:
                out[code] = text
        return out
