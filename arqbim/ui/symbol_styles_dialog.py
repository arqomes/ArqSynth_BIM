"""(0.360) The symbols' generator (Anotar ▸ Símbolos…): how the views' symbols look — a section's (its head: a circle,
a square or none; its arrow filled, open or none; its line dash-dot, dashed, continuous or only at its ends; their sizes
and pen), an elevation's, a detail's callout, a level's mark (a triangle, a quartered circle) — each drawn as it
changes, as the plans, sections, sheets, PDF and DXF will draw it. The owner, 2026-11-02: «Precisamos de ter o gerador
de elementos onde o utilizador pode definir como será a aparência dos símbolos usados dentro do programa, seja da
corte, da vista, dos detalhes etc.». Kept in the project's graphic style («symbols»): one undo step."""

import copy

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import decimal_sep, t
from ..model import graphic_styles as styles_model
from ..model import symbols as marks_model
from . import theme

FIELDS = {                                  # each kind's fields, in order
    "section": ("head", "arrow", "size", "text", "line", "pen"),
    "elevation": ("head", "arrow", "size", "text", "pen"),
    "detail": ("head", "size", "text", "line", "pen"),
    "level": ("mark", "ends", "label", "size", "text", "line", "pen"),        # (0.462: at which end, its words)
}


class SymbolPreview(QtWidgets.QWidget):
    """A kind of symbol drawn as its style says, at 1:1 on paper (enlarged to fit)."""

    def __init__(self, kind):
        super().__init__()
        self.kind, self.style = kind, styles_model.symbol(None, kind)
        self.setMinimumSize(260, 170)

    def show_style(self, style):
        self.style = dict(style)
        self.update()

    def paintEvent(self, _event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QtGui.QColor("#ffffff"))                # (on paper)
        k = min(self.width(), self.height()) / 40.0                    # px per mm
        ink = QtGui.QColor("#000000")
        s = self.style

        def pen(mm, dashes=None):
            q = QtGui.QPen(ink, max(mm * k, 1.0))
            if dashes:
                q.setDashPattern([d * k / max(q.widthF(), 1e-6) for d in dashes])
            return q

        def head(c, look, tag):
            lines, filled, hollow, r = marks_model.head_shape(s, look, k)
            p.setPen(pen(s["pen"]))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            for a, b in lines:
                p.drawLine(QtCore.QPointF(*(c + a)), QtCore.QPointF(*(c + b)))
            for tri in hollow:
                p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*(c + q)) for q in tri]))
            p.setBrush(ink)
            for tri in filled:
                p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*(c + q)) for q in tri]))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            font = p.font()
            font.setBold(True)
            font.setPixelSize(max(6, int(s["text"] * k * 0.75)))
            p.setFont(font)
            half = max(r, s["text"] * k)
            p.setPen(ink)
            p.drawText(QtCore.QRectF(c[0] - half, c[1] - half, 2 * half, 2 * half),
                       QtCore.Qt.AlignmentFlag.AlignCenter, tag)

        w, h = self.width(), self.height()
        if self.kind == "section":
            a, b = np.array((w * 0.22, h * 0.55)), np.array((w * 0.78, h * 0.55))
            p.setPen(pen(s["pen"], marks_model.DASHES.get(s["line"])))
            for q0, q1 in marks_model.line_pieces(a, b, s, k)[0]:
                p.drawLine(QtCore.QPointF(*q0), QtCore.QPointF(*q1))
            for end, out in ((a, -1.0), (b, 1.0)):
                head(end + np.array((out * s["size"] * k, 0.0)), np.array((0.0, -1.0)), "1")
        elif self.kind == "elevation":
            head(np.array((w / 2, h * 0.6)), np.array((0.0, -1.0)), "A")
        elif self.kind == "detail":
            box = QtCore.QRectF(w * 0.12, h * 0.35, w * 0.5, h * 0.5)
            p.setPen(pen(s["pen"], marks_model.DASHES.get(s["line"])))
            p.drawRoundedRect(box, 2 * k, 2 * k)
            r = s["size"] * k
            centre = np.array((box.right() + r * 1.6, box.top() - r * 1.6))
            p.setPen(pen(s["pen"]))
            p.drawLine(QtCore.QPointF(box.right(), box.top()), QtCore.QPointF(centre[0] - r * 0.7, centre[1] + r * 0.7))
            head(centre, None, "D1")
        else:
            draw_level(p, s, w, h, k)
        p.end()


def draw_level(p, s, w, h, k=None):
    """(0.462) A level as its style draws it (model/symbols.level_parts), across a w × h preview at k px per mm on
    paper: its line, its mark(s), its words — in its colour (the paper's black when it has none)."""
    k = k or min(w, h) / 40.0
    ink = QtGui.QColor(s.get("colour") or "#000000")
    over = marks_model.LEVEL_OVER                  # (the line from margin to w − margin: its marks beyond, inside)
    margin = (2.0 * float(s.get("size", 1.8)) + 2.0) * k
    x0, x1 = margin / k + over, (w - margin) / k - over
    house = (x0 + (x1 - x0) * 0.32, x0 + (x1 - x0) * 0.68)         # (0.464) a building drawn faintly under it
    parts = marks_model.level_parts(3.0, x0, x1, t("symbols.storey"), s, 1.0, decimal_sep(), model=house)
    base = h * 0.55
    p.fillRect(QtCore.QRectF(house[0] * k, base - h * 0.35, (house[1] - house[0]) * k, h * 0.35 + h * 0.3),
               QtGui.QColor("#e4e4e4"))

    def at(q):
        return QtCore.QPointF(float(q[0]) * k, base - (float(q[1]) - 3.0) * k)

    def pen(mm, dashes=None):
        q = QtGui.QPen(QtGui.QBrush(ink), max(mm * k, 1.0))
        if dashes:
            q.setDashPattern([d * k / max(q.widthF(), 1e-6) for d in dashes])
            if tuple(dashes) == marks_model.DASHES["dotted"]:              # (0.465: round dots)
                q.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
                q.setWidthF(max(q.widthF(), 1.6))
        return q
    p.setPen(pen(s["pen"], parts.dashes))
    for q0, q1 in parts.pieces:
        p.drawLine(at(q0), at(q1))
    p.setPen(pen(s["pen"]))
    for q0, q1 in parts.outline:
        p.drawLine(at(q0), at(q1))
    p.setBrush(ink)
    for poly in parts.filled:
        p.drawPolygon(QtGui.QPolygonF([at(q) for q in poly]))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    font = p.font()
    font.setBold(False)
    p.setPen(ink)
    for q, text, align, size in parts.texts:
        font.setPixelSize(max(9, int(size * k * 0.75)))
        p.setFont(font)
        vertical, side = align.split("-")
        point = at(q)
        box = QtCore.QRectF(point.x() - w if side == "right" else point.x(),
                            point.y() - size * k * 1.4 if vertical == "bottom" else point.y(), w, size * k * 1.4)
        p.drawText(box, (QtCore.Qt.AlignmentFlag.AlignRight if side == "right" else QtCore.Qt.AlignmentFlag.AlignLeft)
                   | QtCore.Qt.AlignmentFlag.AlignVCenter, text)


class SymbolStylesDialog(QtWidgets.QDialog):
    """The project's symbols' styles (graphic_styles «symbols»), a tab a kind: its fields beside its preview."""

    def __init__(self, parent, style):
        super().__init__(parent)
        self.setWindowTitle(t("symbols.title"))
        self.base = styles_model.clean(style)
        self.editors = {}                      # (kind, field) -> widget
        self.previews = {}
        layout = QtWidgets.QVBoxLayout(self)
        note = QtWidgets.QLabel(t("symbols.note"))
        note.setWordWrap(True)
        note.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        layout.addWidget(note)
        self.tabs = QtWidgets.QTabWidget()
        for kind in styles_model.SYMBOL_KINDS:
            page = QtWidgets.QWidget()
            row = QtWidgets.QHBoxLayout(page)
            form = QtWidgets.QFormLayout()
            row.addLayout(form)
            current = self.base["symbols"][kind]
            for name in FIELDS[kind]:
                if name in styles_model.SYMBOL_CHOICES:
                    box = QtWidgets.QComboBox()
                    for value in styles_model.SYMBOL_CHOICES[name]:
                        box.addItem(t("symbols.{}.{}".format(name, value)), value)
                    box.setCurrentIndex(max(0, box.findData(current[name])))
                    box.currentIndexChanged.connect(lambda _i, k=kind: self._changed(k))
                else:
                    low, high = styles_model.SYMBOL_SIZES[name]
                    box = QtWidgets.QDoubleSpinBox()
                    box.setRange(low, high)
                    box.setDecimals(2)
                    box.setSingleStep(0.05 if name == "pen" else 0.5)
                    box.setSuffix(" mm")
                    box.setValue(current[name])
                    box.valueChanged.connect(lambda _v, k=kind: self._changed(k))
                form.addRow(t("symbols.field." + name), box)
                self.editors[(kind, name)] = box
            preview = SymbolPreview(kind)
            preview.show_style(current)
            self.previews[kind] = preview
            row.addWidget(preview, 1)
            self.tabs.addTab(page, t("symbols.kind." + kind))
        layout.addWidget(self.tabs)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel
                                             | QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        defaults = buttons.button(QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults)
        defaults.setText(t("symbols.defaults"))
        defaults.clicked.connect(self.restore)
        layout.addWidget(buttons)
        self.resize(640, 380)

    def _kind_style(self, kind):
        out = {}
        for name in FIELDS[kind]:
            box = self.editors[(kind, name)]
            out[name] = box.currentData() if isinstance(box, QtWidgets.QComboBox) else float(box.value())
        return dict(self.base["symbols"][kind], **out)

    def _changed(self, kind):
        self.previews[kind].show_style(self._kind_style(kind))

    def restore(self):
        """The usual symbols back (as drawn until 0.359)."""
        usual = styles_model.defaults()["symbols"]
        for (kind, name), box in self.editors.items():
            if isinstance(box, QtWidgets.QComboBox):
                box.setCurrentIndex(max(0, box.findData(usual[kind][name])))
            else:
                box.setValue(usual[kind][name])

    def style(self):
        """The whole graphic style with these symbols."""
        out = copy.deepcopy(self.base)
        out["symbols"] = {kind: self._kind_style(kind) for kind in styles_model.SYMBOL_KINDS}
        return out
