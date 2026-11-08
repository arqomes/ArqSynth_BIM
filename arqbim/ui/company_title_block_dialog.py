"""(0.472) «Editar carimbo…» (the owner: «um botão editar o carimbo para que o utilizador possa editar o carimbo
fazendo de forma personalizada de acordo com a sua empresa»): the company's own title block, drawn as it will print
while it is made —

- the company: its name, its contacts (a few lines), its logo (a picture);
- the title block's width and its rows, top to bottom: each row its height and its boxes, each box what it shows (the
  logo, the company, the project, the drawing, the scale…) and its share of the row; rows and boxes added, taken away,
  moved;
- each field's own name («Obra» → «Projeto», as the office says);
- kept with the project (and on this sheet or every sheet, «Da empresa»); «Guardar como carimbo da empresa» keeps it
  in the suite's folder for every new project, «Usar o da empresa» brings it back.

The window gives what was made (company()); the main window does it (one undo step)."""

import copy
import os

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..model import company_title_block as company_file
from ..model import sheets as sheets_model
from . import pdf

PREVIEW_PX = 400


class BlockPicture(QtWidgets.QWidget):
    """The title block as it will print, with the project's texts."""

    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog
        self.setMinimumSize(PREVIEW_PX, 170)

    def paintEvent(self, _event):
        company = self.dialog.company()
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor("#8a8d92"))
        if company is None:
            painter.end()
            return
        previous = sheets_model.company()
        sheets_model.use_company(company)
        try:
            bw, bh = sheets_model.block_size("custom")
            m = sheets_model.MARGIN
            dpmm = min((self.width() - 20) / bw, (self.height() - 20) / bh)
            x0, y0 = (self.width() - bw * dpmm) / 2, (self.height() - bh * dpmm) / 2
            painter.fillRect(QtCore.QRectF(x0, y0, bw * dpmm, bh * dpmm), QtGui.QColor("white"))
            painter.translate(x0 - m * dpmm, y0 - m * dpmm)
            texts = dict(self.dialog.texts, company=company["name"], contacts=company["contacts"],
                         logo=company["logo"], labels=company["labels"], scale="1:100",
                         date=QtCore.QDate.currentDate().toString("dd/MM/yyyy"))
            texts[sheets_model.EXTRA_KEY], texts["revisions"] = [], []
            pdf._title_block(painter, dpmm, bw + 2 * m, bh + 2 * m, texts, "", "custom")
        finally:
            sheets_model.use_company(previous)
            painter.end()


class RowEditor(QtWidgets.QFrame):
    """A row of the title block: its height and its boxes (what each shows, its share of the row)."""

    def __init__(self, dialog, row):
        super().__init__()
        self.dialog = dialog
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        layout.addWidget(QtWidgets.QLabel(t("ctb.row_h")))
        self.row_height = QtWidgets.QDoubleSpinBox()
        self.row_height.setRange(3.0, 80.0)
        self.row_height.setDecimals(1)
        self.row_height.setSuffix(" mm")
        self.row_height.setValue(float(row["h"]))
        self.row_height.valueChanged.connect(dialog.changed)
        layout.addWidget(self.row_height)
        self.cells = QtWidgets.QHBoxLayout()
        self.cells.setSpacing(2)
        layout.addLayout(self.cells, 1)
        self.boxes = []
        for key, share in row["cells"]:
            self.add_cell(key, share)
        for text, tip, act in (("+", "ctb.add_cell", lambda: (self.add_cell("blank", 1.0), dialog.changed())),
                               ("−", "ctb.remove_cell", self.remove_cell),
                               ("↑", "ctb.row_up", lambda: dialog.move_row(self, -1)),
                               ("↓", "ctb.row_down", lambda: dialog.move_row(self, 1)),
                               ("×", "ctb.remove_row", lambda: dialog.remove_row(self))):
            button = QtWidgets.QToolButton()
            button.setText(text)
            button.setToolTip(t(tip))
            button.clicked.connect(act)
            layout.addWidget(button)

    def add_cell(self, key, share):
        combo = QtWidgets.QComboBox()
        for field in sheets_model.COMPANY_FIELDS:
            combo.addItem(t("tb." + field), field)
        combo.setCurrentIndex(max(0, combo.findData(key)))
        combo.currentIndexChanged.connect(self.dialog.changed)
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(0.1, 20.0)
        spin.setDecimals(1)
        spin.setSingleStep(0.5)
        spin.setValue(float(share))
        spin.setToolTip(t("ctb.share_tip"))
        spin.valueChanged.connect(self.dialog.changed)
        self.cells.addWidget(combo, 2)
        self.cells.addWidget(spin, 0)
        self.boxes.append((combo, spin))

    def remove_cell(self):
        if len(self.boxes) <= 1:
            return
        combo, spin = self.boxes.pop()
        for w in (combo, spin):
            self.cells.removeWidget(w)
            w.deleteLater()
        self.dialog.changed()

    def row(self):
        return {"h": self.row_height.value(), "cells": [[c.currentData(), s.value()] for c, s in self.boxes]}


class CompanyTitleBlockDialog(QtWidgets.QDialog):
    def __init__(self, parent, company, texts, sheet_name=""):
        """company: the title block to start from (the project's, the office's or the program's); texts: the
        project's title block texts (sheets.title_texts), to show it as it will print."""
        super().__init__(parent)
        self.setWindowTitle(t("ctb.title"))
        self.setMinimumSize(1100, 660)
        self.texts = dict(texts)
        self._quiet = True
        start = sheets_model.clean_company(company) or sheets_model.clean_company(sheets_model.DEFAULT_COMPANY)
        outer = QtWidgets.QHBoxLayout(self)
        left = QtWidgets.QVBoxLayout()
        self.picture = BlockPicture(self)
        left.addWidget(QtWidgets.QLabel(t("ctb.preview")))
        left.addWidget(self.picture, 1)
        intro = QtWidgets.QLabel(t("ctb.intro"))
        intro.setWordWrap(True)
        left.addWidget(intro)
        outer.addLayout(left, 2)

        right = QtWidgets.QVBoxLayout()
        firm = QtWidgets.QGroupBox(t("ctb.company"))
        form = QtWidgets.QFormLayout(firm)
        self.name = QtWidgets.QLineEdit(start["name"])
        self.name.setPlaceholderText(t("ctb.name_hint"))
        self.contacts = QtWidgets.QPlainTextEdit(start["contacts"])
        self.contacts.setPlaceholderText(t("ctb.contacts_hint"))
        self.contacts.setMaximumHeight(70)
        self.logo = start["logo"]
        logo_row = QtWidgets.QHBoxLayout()
        self.logo_label = QtWidgets.QLabel()
        choose = QtWidgets.QPushButton(t("ctb.logo_choose"))
        choose.clicked.connect(self.choose_logo)
        clear = QtWidgets.QPushButton(t("ctb.logo_clear"))
        clear.clicked.connect(lambda: self.set_logo(""))
        logo_row.addWidget(self.logo_label, 1)
        logo_row.addWidget(choose)
        logo_row.addWidget(clear)
        form.addRow(t("ctb.name") + ":", self.name)
        form.addRow(t("ctb.contacts") + ":", self.contacts)
        form.addRow(t("ctb.logo") + ":", logo_row)
        self.block_width = QtWidgets.QDoubleSpinBox()
        self.block_width.setRange(40.0, 400.0)
        self.block_width.setDecimals(0)
        self.block_width.setSuffix(" mm")
        self.block_width.setValue(start["width"])
        form.addRow(t("ctb.width") + ":", self.block_width)
        right.addWidget(firm)

        rows_box = QtWidgets.QGroupBox(t("ctb.rows"))
        rows_col = QtWidgets.QVBoxLayout(rows_box)
        self.rows_area = QtWidgets.QVBoxLayout()
        self.rows_area.setSpacing(3)
        holder = QtWidgets.QWidget()
        holder.setLayout(self.rows_area)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(holder)
        rows_col.addWidget(scroll, 1)
        add_row = QtWidgets.QPushButton(t("ctb.add_row"))
        add_row.clicked.connect(lambda: (self._add_row({"h": 7.5, "cells": [["blank", 1.0]]}), self.changed()))
        rows_col.addWidget(add_row, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        right.addWidget(rows_box, 1)
        self.row_editors = []
        for row in start["rows"]:
            self._add_row(row)

        names = QtWidgets.QGroupBox(t("ctb.labels"))
        names_form = QtWidgets.QFormLayout(names)
        self.labels = {}
        for field in ("project", "client", "site", "author", "stage", "title", "scale", "date", "number", "company",
                      "contacts"):
            edit = QtWidgets.QLineEdit(start["labels"].get(field, ""))
            edit.setPlaceholderText(t("tb." + field))
            edit.textChanged.connect(self.changed)
            self.labels[field] = edit
            names_form.addRow(t("tb." + field) + ":", edit)
        names_scroll = QtWidgets.QScrollArea()
        names_scroll.setWidgetResizable(True)
        names_scroll.setWidget(names)
        names_scroll.setMaximumHeight(170)
        right.addWidget(names_scroll)

        apply = QtWidgets.QHBoxLayout()
        apply.addWidget(QtWidgets.QLabel(t("ctb.apply_to")))
        self.this_sheet = QtWidgets.QRadioButton(t("ctb.this_sheet", name=sheet_name) if sheet_name else
                                                 t("ctb.no_sheet"))
        self.all_sheets = QtWidgets.QRadioButton(t("ctb.all_sheets"))
        self.all_sheets.setChecked(True)
        self.this_sheet.setEnabled(bool(sheet_name))
        apply.addWidget(self.this_sheet)
        apply.addWidget(self.all_sheets)
        apply.addStretch(1)
        right.addLayout(apply)

        office = QtWidgets.QHBoxLayout()
        self.save_office = QtWidgets.QPushButton(t("ctb.save_office"))
        self.save_office.setToolTip(t("ctb.save_office_tip"))
        self.save_office.clicked.connect(self.save_as_office)
        self.load_office = QtWidgets.QPushButton(t("ctb.load_office"))
        self.load_office.setEnabled(company_file.load() is not None)
        self.load_office.clicked.connect(lambda: self.load(company_file.load()))
        reset = QtWidgets.QPushButton(t("ctb.reset"))
        reset.clicked.connect(lambda: self.load(sheets_model.DEFAULT_COMPANY, keep_firm=True))
        for b in (self.save_office, self.load_office, reset):
            office.addWidget(b)
        office.addStretch(1)
        right.addLayout(office)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        right.addWidget(buttons)
        outer.addLayout(right, 3)
        for w in (self.name, self.block_width):
            (w.textChanged if isinstance(w, QtWidgets.QLineEdit) else w.valueChanged).connect(self.changed)
        self.contacts.textChanged.connect(self.changed)
        self.set_logo(self.logo)
        self._quiet = False
        self.changed()

    # ------------------------------------------------------------ rows

    def _add_row(self, row):
        editor = RowEditor(self, row)
        self.row_editors.append(editor)
        self.rows_area.addWidget(editor)
        return editor

    def move_row(self, editor, step):
        k = self.row_editors.index(editor)
        j = k + step
        if not 0 <= j < len(self.row_editors):
            return
        self.row_editors[k], self.row_editors[j] = self.row_editors[j], self.row_editors[k]
        for e in self.row_editors:
            self.rows_area.removeWidget(e)
        for e in self.row_editors:
            self.rows_area.addWidget(e)
        self.changed()

    def remove_row(self, editor):
        if len(self.row_editors) <= 1:
            return
        self.row_editors.remove(editor)
        self.rows_area.removeWidget(editor)
        editor.deleteLater()
        self.changed()

    # ------------------------------------------------------------ the company

    def choose_logo(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("ctb.logo_choose"), os.path.expanduser("~"),
                                                        t("ctb.logo_filter"))
        if path:
            self.set_logo(path)

    def set_logo(self, path):
        self.logo = path or ""
        self.logo_label.setText(os.path.basename(self.logo) if self.logo else t("ctb.no_logo"))
        self.changed()

    def load(self, company, keep_firm=False):
        """Start again from another title block (the office's, the program's); keep_firm: the company's name,
        contacts and logo as they are."""
        company = sheets_model.clean_company(company)
        if company is None:
            return
        self._quiet = True
        if not keep_firm:
            self.name.setText(company["name"])
            self.contacts.setPlainText(company["contacts"])
            self.set_logo(company["logo"])
        self.block_width.setValue(company["width"])
        for e in self.row_editors:
            self.rows_area.removeWidget(e)
            e.deleteLater()
        self.row_editors = []
        for row in company["rows"]:
            self._add_row(row)
        for field, edit in self.labels.items():
            edit.setText(company["labels"].get(field, ""))
        self._quiet = False
        self.changed()

    def save_as_office(self):
        try:
            where = company_file.save(self.company())
        except (OSError, ValueError) as exc:
            QtWidgets.QMessageBox.warning(self, t("ctb.title"), t("ctb.save_failed", e=str(exc)))
            return
        self.load_office.setEnabled(True)
        QtWidgets.QMessageBox.information(self, t("ctb.title"), t("ctb.saved", f=where))

    # ------------------------------------------------------------ what was made

    def changed(self, *_args):
        if not self._quiet:
            self.picture.update()

    def company(self):
        """The company's title block as made here (sheets.clean_company), or None."""
        return sheets_model.clean_company({
            "name": self.name.text(), "contacts": self.contacts.toPlainText(), "logo": self.logo,
            "width": self.block_width.value(), "rows": [e.row() for e in self.row_editors],
            "labels": {f: e.text() for f, e in self.labels.items()}})

    def everyone(self):
        return self.all_sheets.isChecked()


def start_company(project_block):
    """The title block the window starts from: the project's own, else the office's, else the program's."""
    return copy.deepcopy(project_block.get(sheets_model.COMPANY_KEY)) or company_file.load() or \
        copy.deepcopy(sheets_model.DEFAULT_COMPANY)
