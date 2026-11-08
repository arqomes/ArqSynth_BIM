"""(0.470) «Editar tipo…» of a sheet, as Revit's Type Properties of a title block (the owner: «A edição do tipo da folha
e propriedades devem ficar na coluna de propriedade. E a edição numa janela própria que abre como no revit»):

- its family — ArqSynth's title block — and its type: the paper (A4 to A0), how it stands (lying, standing), the title
  block's template (full, compact, a strip down the side), with a picture of the sheet as they make it;
- to whom the type's change goes: every sheet of the type (as Revit's), or this one alone;
- what the title block shows on every sheet: the project's fields, its own fields and how sheets are numbered (until
  0.469 the «Carimbo…» window's).

The window does what is asked (MainWindow.edit_sheet_type): one undo step."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..model import sheets as sheets_model
from .title_block_dialog import _add_row, _buttons, _rows, _table


def kinds():
    """Every sheet type there is: [(its name, (paper, portrait, template))] — each paper lying, then standing."""
    out = []
    for paper in sheets_model.PAPERS:
        for portrait in (False, True):
            for template in sheets_model.TEMPLATES:
                out.append((kind_label((paper, portrait, template)), (paper, portrait, template)))
    return out


def kind_label(kind):
    """A sheet type's name: «A3 horizontal · Completo»."""
    paper, portrait, template = kind
    return t("sheettype.name", paper=paper, way=t("props.sheet_way." + ("portrait" if portrait else "landscape")),
             template=t("sheet.template." + template))


class SheetPicture(QtWidgets.QWidget):
    """The sheet as its type makes it: the paper, its border, where the views go, the title block's boxes."""

    def __init__(self):
        super().__init__()
        self.kind = ("A3", False, "full")
        self.setMinimumSize(220, 170)

    def show_kind(self, kind):
        self.kind = tuple(kind)
        self.update()

    def paintEvent(self, _event):
        paper, portrait, template = self.kind
        w, h = sheets_model.paper_size(paper, portrait)
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        k = min((self.width() - 16) / w, (self.height() - 16) / h)
        x0, y0 = (self.width() - w * k) / 2, (self.height() - h * k) / 2

        def rect(x, y, rw, rh):
            return QtCore.QRectF(x0 + x * k, y0 + y * k, rw * k, rh * k)
        p.fillRect(rect(2, 2, w, h), QtGui.QColor(0, 0, 0, 40))              # (a shadow under the paper)
        p.fillRect(rect(0, 0, w, h), QtGui.QColor("#ffffff"))
        p.setPen(QtGui.QPen(QtGui.QColor("#9aa3ad"), 1.0))
        p.drawRect(rect(0, 0, w, h))
        m = sheets_model.MARGIN
        p.setPen(QtGui.QPen(QtGui.QColor("#2b2f36"), 1.2))
        p.drawRect(rect(m, m, w - 2 * m, h - 2 * m))
        left, top, aw, ah = sheets_model.drawing_area(paper, template, portrait)
        p.setPen(QtGui.QPen(QtGui.QColor("#6b8fc7"), 1.0, QtCore.Qt.PenStyle.DashLine))
        p.drawRect(rect(left, top, aw, ah))
        bx, by, _bw, _bh = sheets_model.title_box((w, h), template)
        if template == "custom":                         # (0.473) the company's drawing, small
            from . import pdf
            p.save()
            p.translate(x0, y0)
            pdf.paint_drawn(p, k, w - m, h - m, sheets_model.company()["items"], {})
            p.restore()
        p.setPen(QtGui.QPen(QtGui.QColor("#2b2f36"), 0.8))
        for cx, cy, cw, ch, _what, _size, bold in sheets_model.cells_of(template):
            box = rect(bx + cx, by + cy, cw, ch)
            if bold:
                p.fillRect(box, QtGui.QColor("#e8ecf2"))
            p.drawRect(box)
        p.setPen(QtGui.QColor("#5c6470"))
        font = p.font()
        font.setPointSizeF(max(font.pointSizeF() - 1.0, 7.0) if font.pointSizeF() > 0 else 8.0)
        p.setFont(font)
        p.drawText(rect(left, top, aw, ah), QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.TextFlag.TextWordWrap,
                   "{}\n{:.0f} × {:.0f} mm".format(paper, w, h))
        p.end()


class SheetTypeDialog(QtWidgets.QDialog):
    def __init__(self, parent, sheet, sheets, fields, project="", number=""):
        """sheet: the sheet it was opened for; sheets: all of them (how many are of its type); fields: the project's
        title block ({field: text}); project: the name shown when none is given; number: the sheet's number now."""
        super().__init__(parent)
        self.setWindowTitle(t("sheettype.title"))
        self.setMinimumWidth(560)
        self.sheet = sheet
        outer = QtWidgets.QVBoxLayout(self)
        top = QtWidgets.QFormLayout()
        family = QtWidgets.QLabel(t("sheettype.family_name"))
        top.addRow(t("sheettype.family") + ":", family)
        self.type_name = QtWidgets.QLabel(kind_label(sheet.kind))
        self.type_name.setStyleSheet("QLabel { font-weight: 600; }")
        top.addRow(t("sheettype.type") + ":", self.type_name)
        outer.addLayout(top)

        # the type's parameters, and the sheet they make
        params = QtWidgets.QGroupBox(t("sheettype.params"))
        row = QtWidgets.QHBoxLayout(params)
        form = QtWidgets.QFormLayout()
        self.paper = QtWidgets.QComboBox()
        for key in sheets_model.PAPERS:
            w, h = sheets_model.PAPERS[key]
            self.paper.addItem("{}  ({:.0f} × {:.0f} mm)".format(key, min(w, h), max(w, h)), key)   # (ISO's way)
        self.way = QtWidgets.QComboBox()
        for portrait in (False, True):
            self.way.addItem(t("props.sheet_way." + ("portrait" if portrait else "landscape")), portrait)
        self.template = QtWidgets.QComboBox()
        for key in sheets_model.TEMPLATES:
            self.template.addItem(t("sheet.template." + key), key)
        paper, portrait, template = sheet.kind
        self.paper.setCurrentIndex(max(0, self.paper.findData(paper)))
        self.way.setCurrentIndex(1 if portrait else 0)
        self.template.setCurrentIndex(max(0, self.template.findData(template)))
        form.addRow(t("sheettype.paper") + ":", self.paper)
        form.addRow(t("sheettype.way") + ":", self.way)
        form.addRow(t("sheettype.template") + ":", self.template)
        row.addLayout(form, 1)
        self.picture = SheetPicture()
        row.addWidget(self.picture)
        outer.addWidget(params)
        for combo in (self.paper, self.way, self.template):
            combo.currentIndexChanged.connect(lambda _i: self._kind_changed())

        # to whom it goes (Revit: every sheet of the type)
        same = sum(1 for s in sheets if s.kind == sheet.kind)
        self.all_of_type = QtWidgets.QRadioButton(t("sheettype.all", n=same))
        self.only_this = QtWidgets.QRadioButton(t("sheettype.only", name=sheet.name))
        self.all_of_type.setChecked(True)
        apply = QtWidgets.QHBoxLayout()
        apply.addWidget(QtWidgets.QLabel(t("sheettype.apply_to")))
        apply.addWidget(self.all_of_type)
        apply.addWidget(self.only_this)
        apply.addStretch(1)
        outer.addLayout(apply)

        # what the title block shows on every sheet
        shown = QtWidgets.QGroupBox(t("sheettype.shown"))
        col = QtWidgets.QVBoxLayout(shown)
        fields_form = QtWidgets.QFormLayout()
        self.edits = {}
        for key in sheets_model.TITLE_FIELDS:
            if key == "stage":                      # the usual stages to choose, or any other typed
                edit = QtWidgets.QComboBox()
                edit.setEditable(True)
                edit.addItems([""] + t("tb.stages").split("|"))
                edit.setCurrentText(fields.get(key, ""))
            else:
                edit = QtWidgets.QLineEdit(fields.get(key, ""))
            self.edits[key] = edit
            fields_form.addRow(t("tb." + key) + ":", edit)
        self.edits["project"].setPlaceholderText(t("tb.project_auto", name=project))
        col.addLayout(fields_form)
        col.addWidget(QtWidgets.QLabel(t("tb.extra")))
        self.extra = _table([t("tb.extra_label"), t("tb.extra_text")], fields.get(sheets_model.EXTRA_KEY) or [])
        self.extra.setMaximumHeight(110)
        col.addWidget(self.extra)
        col.addLayout(_buttons(self.extra, lambda: _add_row(self.extra, ("", ""))))
        numbering = QtWidgets.QHBoxLayout()
        self.prefix = QtWidgets.QLineEdit(fields.get("prefix", ""))
        self.prefix.setPlaceholderText(t("tb.prefix_hint"))
        self.digits = QtWidgets.QSpinBox()
        self.digits.setRange(1, 4)
        self.digits.setValue(int(fields.get("digits") or 2))
        numbering.addWidget(QtWidgets.QLabel(t("tb.prefix") + ":"))
        numbering.addWidget(self.prefix, 1)
        numbering.addWidget(QtWidgets.QLabel(t("tb.digits") + ":"))
        numbering.addWidget(self.digits)
        col.addLayout(numbering)
        if number:
            note = QtWidgets.QLabel(t("sheettype.number_now", n=number))
            note.setStyleSheet("QLabel { color: palette(mid); }")
            col.addWidget(note)
        outer.addWidget(shown)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)
        self._kind_changed()

    def kind(self):
        """The type as chosen: (paper, portrait, template)."""
        return self.paper.currentData(), bool(self.way.currentData()), self.template.currentData()

    def everyone(self):
        """The change goes to every sheet of the type (else to this one alone)."""
        return self.all_of_type.isChecked()

    def _kind_changed(self):
        self.picture.show_kind(self.kind())
        self.type_name.setText(kind_label(self.kind()))

    def fields(self):
        """{field: text} as typed, its own fields, its numbering (as the title block keeps them)."""
        out = {key: (edit.currentText() if isinstance(edit, QtWidgets.QComboBox) else edit.text()).strip()
               for key, edit in self.edits.items()}
        out[sheets_model.EXTRA_KEY] = [row for row in _rows(self.extra) if row[0]]
        out["prefix"] = self.prefix.text().strip()
        out["digits"] = str(self.digits.value())
        return out


class RevisionsDialog(QtWidgets.QDialog):
    """(0.470) A sheet's revisions (a code, a date, what changed), from its Properties' «Revisões…»."""

    def __init__(self, parent, sheet):
        super().__init__(parent)
        self.setWindowTitle(t("sheettype.revisions_title", name=sheet.name))
        self.setMinimumWidth(460)
        layout = QtWidgets.QVBoxLayout(self)
        self.table = _table([t("tb.rev_code"), t("tb.rev_date"), t("tb.rev_text")],
                            [(r["code"], r["date"], r["text"]) for r in sheet.revisions])
        layout.addWidget(self.table)
        layout.addLayout(_buttons(self.table, self.new_revision))
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def new_revision(self, text=""):
        """A new row: the next letter, today's date (as the title block window's)."""
        from .title_block_dialog import TitleBlockDialog
        TitleBlockDialog.new_revision(self._as_title_block(), text)

    def _as_title_block(self):
        holder = type("_Holder", (), {})()
        holder.revision_table = self.table
        return holder

    def revisions(self):
        return [{"code": c, "date": d, "text": x} for c, d, x in _rows(self.table)]
