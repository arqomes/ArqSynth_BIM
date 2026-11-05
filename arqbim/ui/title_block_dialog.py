"""Sheets ▸ Title block…: the project's details printed in the title block of every sheet —
project, client, site, architect, design stage (model/sheets.TITLE_FIELDS), and (0.127) its own
fields (a label and a text each, printed over the title block) and how its sheets are numbered (a
prefix, so many digits) — and, when opened for a sheet, its name, number and revisions (a code,
a date, what changed). One undo step on OK (Document.set_title_block)."""

import datetime
import string

from PySide6 import QtWidgets

from ..i18n import t
from ..model.sheets import EXTRA_KEY, TITLE_FIELDS


def _table(headers, rows):
    """A small editable table with its rows, and its Add / Remove buttons under it."""
    table = QtWidgets.QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setStretchLastSection(True)
    table.verticalHeader().setVisible(False)
    table.setMinimumHeight(90)
    for row in rows:
        _add_row(table, row)
    return table


def _add_row(table, values):
    r = table.rowCount()
    table.insertRow(r)
    for c, value in enumerate(values):
        table.setItem(r, c, QtWidgets.QTableWidgetItem(str(value)))


def _rows(table):
    out = []
    for r in range(table.rowCount()):
        out.append([(table.item(r, c).text() if table.item(r, c) is not None else "").strip()
                    for c in range(table.columnCount())])
    return out


def _buttons(table, on_add):
    bar = QtWidgets.QHBoxLayout()
    add = QtWidgets.QPushButton(t("tb.add_row"))
    remove = QtWidgets.QPushButton(t("tb.remove_row"))
    add.clicked.connect(on_add)
    remove.clicked.connect(lambda: table.removeRow(table.currentRow()) if table.currentRow() >= 0 else None)
    bar.addWidget(add)
    bar.addWidget(remove)
    bar.addStretch(1)
    return bar


class TitleBlockDialog(QtWidgets.QDialog):
    def __init__(self, parent, fields, sheet=None, number="", project=""):
        """fields: the project's ({field: text}); sheet: the sheet it was opened for, or None;
        number: the number that sheet shows now; project: the name shown when none is given."""
        super().__init__(parent)
        self.setWindowTitle(t("tb.window"))
        self.setMinimumWidth(500)
        intro = QtWidgets.QLabel(t("tb.intro"))
        intro.setWordWrap(True)
        form = QtWidgets.QFormLayout()
        self.edits = {}
        for key in TITLE_FIELDS:
            if key == "stage":                      # the usual stages to choose, or any other typed
                edit = QtWidgets.QComboBox()
                edit.setEditable(True)
                edit.addItems([""] + t("tb.stages").split("|"))
                edit.setCurrentText(fields.get(key, ""))
            else:
                edit = QtWidgets.QLineEdit(fields.get(key, ""))
            self.edits[key] = edit
            form.addRow(t("tb." + key) + ":", edit)
        self.edits["project"].setPlaceholderText(t("tb.project_auto", name=project))

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addLayout(form)
        # (0.127) the project's own fields, and the numbering of its sheets
        own = QtWidgets.QGroupBox(t("tb.extra"))
        own_layout = QtWidgets.QVBoxLayout(own)
        self.extra = _table([t("tb.extra_label"), t("tb.extra_text")], fields.get(EXTRA_KEY) or [])
        own_layout.addWidget(self.extra)
        own_layout.addLayout(_buttons(self.extra, lambda: _add_row(self.extra, ("", ""))))
        layout.addWidget(own)
        numbering = QtWidgets.QGroupBox(t("tb.numbering"))
        numbering_form = QtWidgets.QFormLayout(numbering)
        self.prefix = QtWidgets.QLineEdit(fields.get("prefix", ""))
        self.prefix.setPlaceholderText(t("tb.prefix_hint"))
        self.digits = QtWidgets.QSpinBox()
        self.digits.setRange(1, 4)
        self.digits.setValue(int(fields.get("digits") or 2))
        numbering_form.addRow(t("tb.prefix") + ":", self.prefix)
        numbering_form.addRow(t("tb.digits") + ":", self.digits)
        layout.addWidget(numbering)

        self.name = self.number = self.revision_table = None
        if sheet is not None:
            box = QtWidgets.QGroupBox("{} — {}".format(t("tb.this_sheet"), sheet.name))
            sheet_layout = QtWidgets.QVBoxLayout(box)
            sheet_form = QtWidgets.QFormLayout()
            self.name = QtWidgets.QLineEdit(sheet.name)
            self.number = QtWidgets.QLineEdit(sheet.number)
            self.number.setPlaceholderText(t("tb.number_auto", n=number) if not sheet.number else "")
            sheet_form.addRow(t("tb.title") + ":", self.name)
            sheet_form.addRow(t("tb.number") + ":", self.number)
            sheet_layout.addLayout(sheet_form)
            sheet_layout.addWidget(QtWidgets.QLabel(t("tb.revisions")))
            self.revision_table = _table([t("tb.rev_code"), t("tb.rev_date"), t("tb.rev_text")],
                                         [(r["code"], r["date"], r["text"]) for r in sheet.revisions])
            sheet_layout.addWidget(self.revision_table)
            sheet_layout.addLayout(_buttons(self.revision_table, self.new_revision))
            layout.addWidget(box)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok |
                                             QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def new_revision(self, text=""):
        """A new revision row: the next letter after the last one (A, B, C…), today's date."""
        codes = [row[0] for row in _rows(self.revision_table) if row[0]]
        last = codes[-1] if codes else ""
        letters = string.ascii_uppercase
        code = letters[letters.index(last) + 1] if len(last) == 1 and last in letters[:-1] else \
            ("A" if not last else last + "'")
        _add_row(self.revision_table, (code, datetime.date.today().strftime("%d/%m/%Y"), text))

    def fields(self):
        """{field: text} as typed (empty ones left out by the document), its own fields, its numbering."""
        out = {key: (edit.currentText() if isinstance(edit, QtWidgets.QComboBox) else edit.text()).strip()
               for key, edit in self.edits.items()}
        out[EXTRA_KEY] = [row for row in _rows(self.extra) if row[0]]
        out["prefix"] = self.prefix.text().strip()
        out["digits"] = str(self.digits.value())
        return out

    def sheet_values(self):
        """(name, number) for the sheet, or (None, None) when opened without one."""
        if self.name is None:
            return None, None
        return self.name.text(), self.number.text()

    def revisions(self):
        """The sheet's revisions as typed: [{"code", "date", "text"}], or None when opened without one."""
        if self.revision_table is None:
            return None
        return [{"code": c, "date": d, "text": x} for c, d, x in _rows(self.revision_table)]
