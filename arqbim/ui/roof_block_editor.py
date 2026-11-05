"""The roof block editor (0.263), as the add-on's roof block panel: a roof by blocks' blocks one by one — where
(its middle, its turn), how big, its overhang, (0.356) its height (the whole block up or down); each side's water or
gable, its slope and the height of its eave; blocks duplicated and removed. (0.356) Opened by a double click on the
roof in the view, on the block clicked. The blocks drawn in the plan as they are being changed: the roof they make (its
waters shaded), the block chosen marked, the letters of its sides (a click on one: water ⇄ gable) and the fall of
its waters arrowed. Applying makes the roof again (one undo step, done by the window: on_save)."""

import math

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..core import roof_blocks as rb
from ..core.units import format_angle, format_length, parse_angle, parse_length
from ..i18n import decimal_sep, t
from . import theme

ACCENT = "#1a73e8"
LIGHT = np.array((-0.6, 0.8))           # (the waters shaded as lit from the upper left of the plan)
DUPLICATE_STEP = 1.0                    # m: a duplicate beside the block it copies (along its x)


def _len(value):
    return format_length(value, decimal_sep(), 3).replace("~ ", "")


def _contains(block, x, y, grow=0.0):
    a = math.radians(block.angle)
    dx, dy = x - block.cx, y - block.cy
    lx, ly = dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)
    return abs(lx) <= block.width / 2 + grow + 1e-9 and abs(ly) <= block.depth / 2 + grow + 1e-9


class BlockPlan(QtWidgets.QWidget):
    """The blocks seen from above: the roof's waters shaded, every block's rectangle (its walls' line) dashed, the
    one chosen in blue with its overhang, its sides' letters (filled: a water) and its waters' fall."""

    picked = QtCore.Signal(int)             # a block clicked
    side_clicked = QtCore.Signal(int)       # a letter of the chosen block's sides (0..3: N, E, S, W) clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(380, 320)
        self.blocks, self.current = [], -1
        self._view = None                   # (scale, ox, oy) of the last drawing
        self.letters = []                   # [(QPointF, side)] where the chosen block's letters were drawn

    def show_blocks(self, blocks, current):
        self.blocks, self.current = list(blocks), current
        self.update()

    def _frame(self):
        pts = [p for b in self.blocks for p in rb.rect(b, b.overhang)]
        if not pts:
            return None
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        margin = 34
        k = min((self.width() - 2 * margin) / max(x1 - x0, 1e-6), (self.height() - 2 * margin) / max(y1 - y0, 1e-6))
        return k, (self.width() - (x1 - x0) * k) / 2 - x0 * k, (self.height() + (y1 - y0) * k) / 2 + y0 * k

    def to_screen(self, x, y):
        k, ox, oy = self._view
        return QtCore.QPointF(ox + x * k, oy - y * k)

    def to_plan(self, px, py):
        k, ox, oy = self._view
        return (px - ox) / k, (oy - py) / k

    def _polygon(self, pts):
        return QtGui.QPolygonF([self.to_screen(x, y) for x, y in pts])

    def paintEvent(self, _event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QtGui.QColor("#f4f5f6"))
        self._view, self.letters = self._frame(), []
        if self._view is None:
            p.end()
            return
        try:
            regions = rb.regions(self.blocks) if all(rb.problem(b) is None for b in self.blocks) else []
        except Exception:                                   # (a block being typed in that makes no roof yet)
            regions = []
        for coeff, geometry in regions:
            fall = np.array((-coeff[0], -coeff[1]))
            n = float(np.hypot(*fall))
            colour = QtGui.QColor("#dfe3e6") if n < 1e-9 else \
                QtGui.QColor("#d9a68c").lighter(int(108 + 14 * float(fall / n @ LIGHT)))
            for polygon in rb.polygons(geometry):
                path = QtGui.QPainterPath()
                path.addPolygon(self._polygon(list(polygon.exterior.coords)))
                for hole in polygon.interiors:
                    path.addPolygon(self._polygon(list(hole.coords)))
                p.setPen(QtGui.QPen(QtGui.QColor("#8d5a45"), 1))
                p.setBrush(colour)
                p.drawPath(path)
        dashed = QtGui.QPen(QtGui.QColor("#5f6368"), 1, QtCore.Qt.PenStyle.DashLine)
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        for i, b in enumerate(self.blocks):
            if i != self.current:
                p.setPen(dashed)
                p.drawPolygon(self._polygon(rb.rect(b)))
        if 0 <= self.current < len(self.blocks):
            self._draw_chosen(p, self.blocks[self.current])
        p.end()

    def _draw_chosen(self, p, b):
        accent = QtGui.QColor(ACCENT)
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.setPen(QtGui.QPen(accent, 1, QtCore.Qt.PenStyle.DashLine))
        p.drawPolygon(self._polygon(rb.rect(b, b.overhang)))
        p.setPen(QtGui.QPen(accent, 2.2))
        p.drawPolygon(self._polygon(rb.rect(b)))
        c = np.array((b.cx, b.cy))
        font = p.font()
        font.setBold(True)
        p.setFont(font)
        for k, side in enumerate(rb.SIDES):
            out, half = rb.side_way(b, k)
            mid = c + out * half
            if b.water[k]:                                  # (its fall: down to that side)
                length = 0.22 * min(b.width, b.depth)
                tail, head = self.to_screen(*(mid - out * length)), self.to_screen(*(mid - out * 0.04 * length))
                p.setPen(QtGui.QPen(accent, 1.6))
                p.drawLine(tail, head)
                d = np.array((head.x() - tail.x(), head.y() - tail.y()))
                d = d / max(float(np.hypot(*d)), 1e-9)
                side_ = np.array((-d[1], d[0]))
                tip = np.array((head.x(), head.y()))
                for s in (1, -1):
                    end = tip - d * 7 + side_ * 4 * s
                    p.drawLine(head, QtCore.QPointF(end[0], end[1]))
            edge = self.to_screen(*(c + out * (half + b.overhang)))
            v = self.to_screen(*(c + out * (half + b.overhang + 1.0)))
            d = np.array((v.x() - edge.x(), v.y() - edge.y()))
            d = d / max(float(np.hypot(*d)), 1e-9)
            at = QtCore.QPointF(edge.x() + d[0] * 15, edge.y() + d[1] * 15)
            p.setPen(QtGui.QPen(accent, 1.2))
            p.setBrush(accent if b.water[k] else QtGui.QColor("white"))
            p.drawEllipse(at, 10, 10)
            p.setPen(QtGui.QColor("white") if b.water[k] else accent)
            p.drawText(QtCore.QRectF(at.x() - 10, at.y() - 10, 20, 20), QtCore.Qt.AlignmentFlag.AlignCenter,
                       t("blockside." + side))
            self.letters.append((at, k))

    def mousePressEvent(self, event):
        if self._view is None or event.button() != QtCore.Qt.MouseButton.LeftButton:
            return
        pos = event.position()
        for at, k in self.letters:
            if math.hypot(pos.x() - at.x(), pos.y() - at.y()) <= 11:
                self.side_clicked.emit(k)
                return
        x, y = self.to_plan(pos.x(), pos.y())
        under = [i for i, b in enumerate(self.blocks) if _contains(b, x, y)] or \
            [i for i, b in enumerate(self.blocks) if _contains(b, x, y, b.overhang)]
        if under:                                           # (one over another: each click the next of them)
            self.picked.emit(under[(under.index(self.current) + 1) % len(under)] if self.current in under
                             else under[-1])


class RoofBlockEditor(QtWidgets.QDialog):
    FIELDS = (("cx", "len"), ("cy", "len"), ("angle", "angle"), ("width", "len"), ("depth", "len"),
              ("overhang", "len"))

    def __init__(self, parent, blocks, level, name="", current=0):
        """`blocks` in the plan (the world's x, y), their eaves over `level` — the roof's; (0.356) `current`: the block
        chosen first (the one double-clicked in the view)."""
        super().__init__(parent)
        self.setWindowTitle(t("blocked.title", roof=name))
        self.blocks = list(blocks)
        self.level = float(level)
        self.current = 0
        self.on_save = None                 # (blocks, in the plan) -> True if saved
        self._filling = False
        outer = QtWidgets.QHBoxLayout(self)
        left = QtWidgets.QVBoxLayout()
        self.list = QtWidgets.QListWidget()
        self.list.setMinimumWidth(290)
        left.addWidget(self.list, 1)
        row = QtWidgets.QHBoxLayout()
        self.duplicate = QtWidgets.QPushButton(t("types.duplicate"))
        self.remove = QtWidgets.QPushButton(t("types.delete"))
        row.addWidget(self.duplicate)
        row.addWidget(self.remove)
        left.addLayout(row)
        outer.addLayout(left)
        middle = QtWidgets.QVBoxLayout()
        self.plan = BlockPlan()
        middle.addWidget(self.plan, 1)
        tip = QtWidgets.QLabel(t("blocked.hint"))
        tip.setWordWrap(True)
        tip.setStyleSheet("color: %s;" % theme.C["note"])
        middle.addWidget(tip)
        outer.addLayout(middle, 1)
        right = QtWidgets.QVBoxLayout()
        form = QtWidgets.QFormLayout()
        self.form = QtWidgets.QComboBox()
        for f in rb.FORMS:
            self.form.addItem(t("roofform." + f), f)
        self.form.addItem(t("blocked.custom"), "custom")
        form.addRow(t("blocked.form"), self.form)
        self.editors = {}
        for field, kind in self.FIELDS:
            w = QtWidgets.QLineEdit()
            w.editingFinished.connect(lambda f=field: self._field_edited(f))
            self.editors[field] = (kind, w)
            form.addRow(t("blocked." + field), w)
        # (0.356) the block's height: its lowest eave — changed, the whole block goes up or down (all its eaves)
        self.height = QtWidgets.QLineEdit()
        self.height.setToolTip(t("blocked.height_tip"))
        self.height.editingFinished.connect(self._height_edited)
        form.addRow(t("blocked.height"), self.height)
        right.addLayout(form)
        box = QtWidgets.QGroupBox(t("blocked.sides"))
        grid = QtWidgets.QGridLayout(box)
        for col, key in enumerate(("blocked.water", "blocked.slope", "blocked.eave"), start=1):
            grid.addWidget(QtWidgets.QLabel(t(key)), 0, col)
        self.sides = []
        for k, side in enumerate(rb.SIDES):
            grid.addWidget(QtWidgets.QLabel(t("blockside." + side)), k + 1, 0)
            water, slope, eave = QtWidgets.QCheckBox(), QtWidgets.QLineEdit(), QtWidgets.QLineEdit()
            water.toggled.connect(lambda on, k=k: self._water(k, on))
            slope.editingFinished.connect(lambda k=k: self._side_edited(k, "slope"))
            eave.editingFinished.connect(lambda k=k: self._side_edited(k, "eave"))
            for col, w in enumerate((water, slope, eave), start=1):
                grid.addWidget(w, k + 1, col)
            self.sides.append((water, slope, eave))
        right.addWidget(box)
        right.addStretch(1)
        self.problem = QtWidgets.QLabel("")
        self.problem.setWordWrap(True)
        self.problem.setStyleSheet("color: %s;" % theme.C["fail"])
        right.addWidget(self.problem)
        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.apply = QtWidgets.QPushButton(t("blocked.apply"))
        close = QtWidgets.QPushButton(t("blocked.close"))
        buttons.addWidget(self.apply)
        buttons.addWidget(close)
        right.addLayout(buttons)
        outer.addLayout(right)
        self.list.currentRowChanged.connect(self.choose)
        self.plan.picked.connect(self.choose)
        self.plan.side_clicked.connect(lambda k: self.sides[k][0].toggle())
        self.form.currentIndexChanged.connect(lambda _i: self._form_chosen())
        self.duplicate.clicked.connect(self.duplicate_current)
        self.remove.clicked.connect(self.remove_current)
        self.apply.clicked.connect(self.save)
        close.clicked.connect(self.reject)
        self.resize(1120, 640)
        self._fill_list()
        self.choose(current if 0 <= current < len(self.blocks) else 0)

    # ------------------------------------------------------------ the list

    def _label(self, i, b):
        form = rb.form_of(b)
        width = format_length(b.width, decimal_sep(), 2).replace("~ ", "").rsplit(" ", 1)[0]     # (its unit once)
        name = t("roofform." + form) if form != "custom" else t("blocked.custom_short")
        return t("blocked.block", n=i + 1, form=name, w=width,
                 d=format_length(b.depth, decimal_sep(), 2).replace("~ ", ""))

    def _fill_list(self):
        self.list.blockSignals(True)
        self.list.clear()
        for i, b in enumerate(self.blocks):
            self.list.addItem(self._label(i, b))
        self.list.setCurrentRow(self.current)
        self.list.blockSignals(False)

    def choose(self, i):
        if not 0 <= i < len(self.blocks):
            return
        self.current = i
        self.list.blockSignals(True)
        self.list.setCurrentRow(i)
        self.list.blockSignals(False)
        self._fill()

    # ------------------------------------------------------------ the fields

    def _fill(self):
        b = self.blocks[self.current]
        self._filling = True
        self.form.setCurrentIndex(max(self.form.findData(rb.form_of(b)), 0))
        for field, (kind, w) in self.editors.items():
            value = getattr(b, field)
            w.setText(format_angle(value, decimal_sep()) if kind == "angle" else _len(value))
        self.height.setText(_len(self.level + min(b.eave)))
        for k, (water, slope, eave) in enumerate(self.sides):
            water.setChecked(bool(b.water[k]))
            slope.setText(format_angle(b.slope[k], decimal_sep()))
            eave.setText(_len(self.level + b.eave[k]))
            slope.setEnabled(bool(b.water[k]))
            eave.setEnabled(bool(b.water[k]) or b.flat)     # (flat: its top at the highest of them)
        self._filling = False
        self.remove.setEnabled(len(self.blocks) > 1)
        self._refresh()

    def _set(self, block):
        self.blocks[self.current] = block
        item = self.list.item(self.current)
        if item is not None:
            item.setText(self._label(self.current, block))
        self._fill()

    def _field_edited(self, field):
        if self._filling:
            return
        kind, w = self.editors[field]
        value = parse_angle(w.text()) if kind == "angle" else parse_length(w.text())
        if value is None:
            self.problem.setText(t("blocked.bad_number"))
            self.apply.setEnabled(False)
            return
        if abs(float(value) - getattr(self.blocks[self.current], field)) > 1e-9:
            self._set(rb.replace(self.blocks[self.current], **{field: float(value)}))
        else:
            self._refresh()

    def _height_edited(self):
        """(0.356) The block's height typed: all its eaves up or down by as much as its lowest one moved."""
        if self._filling:
            return
        value = parse_length(self.height.text())
        if value is None:
            self.problem.setText(t("blocked.bad_number"))
            self.apply.setEnabled(False)
            return
        b = self.blocks[self.current]
        shift = float(value) - (self.level + min(b.eave))
        if abs(shift) < 1e-9:
            self._refresh()
            return
        self._set(rb.replace(b, eave=tuple(e + shift for e in b.eave)))

    def _water(self, k, on):
        if self._filling:
            return
        b = self.blocks[self.current]
        water = list(b.water)
        water[k] = bool(on)
        self._set(rb.replace(b, water=tuple(water)))

    def _side_edited(self, k, what):
        if self._filling:
            return
        b = self.blocks[self.current]
        w = self.sides[k][1 if what == "slope" else 2]
        value = parse_angle(w.text()) if what == "slope" else parse_length(w.text())
        if value is None:
            self.problem.setText(t("blocked.bad_number"))
            self.apply.setEnabled(False)
            return
        values = list(b.slope if what == "slope" else b.eave)
        new = float(value) if what == "slope" else float(value) - self.level
        if abs(new - values[k]) < 1e-9:
            self._refresh()
            return
        values[k] = new
        self._set(rb.replace(b, **{what: tuple(values)}))

    def _form_chosen(self):
        if self._filling:
            return
        form = self.form.currentData()
        b = self.blocks[self.current]
        if form == "custom" or form == rb.form_of(b):
            return
        self._set(rb.replace(b, water=rb.make(0.0, 0.0, 0.0, b.width, b.depth, form).water))

    def _refresh(self):
        """The plan drawn again; what makes a block unusable said (Apply off)."""
        trouble = None
        for i, b in enumerate(self.blocks):
            key = rb.problem(b)
            if key:
                trouble = t("blocked.problem", n=i + 1, e=t("refuse." + key))
                break
        self.problem.setText(trouble or "")
        self.apply.setEnabled(trouble is None)
        self.plan.show_blocks(self.blocks, self.current)

    # ------------------------------------------------------------ the buttons

    def duplicate_current(self):
        """A copy of the block chosen, beside it (a metre along its x), chosen."""
        b = self.blocks[self.current]
        a = math.radians(b.angle)
        self.blocks.append(rb.replace(b, cx=b.cx + DUPLICATE_STEP * math.cos(a),
                                      cy=b.cy + DUPLICATE_STEP * math.sin(a)))
        self.current = len(self.blocks) - 1
        self._fill_list()
        self._fill()

    def remove_current(self):
        if len(self.blocks) <= 1:
            return False
        del self.blocks[self.current]
        self.current = min(self.current, len(self.blocks) - 1)
        self._fill_list()
        self._fill()
        return True

    def save(self):
        if self.on_save is None or any(rb.problem(b) for b in self.blocks):
            return False
        return bool(self.on_save(list(self.blocks)))
