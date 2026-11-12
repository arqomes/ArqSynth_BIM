"""(0.553) The motif of a custom matrix (core/graph/nodes_logic «Matriz personalizada»): a cell where each click puts
a hole, dragging moves it, the right button takes it away and the mouse wheel over it makes it bigger or smaller —
the cells around drawn faintly, as the matrix will repeat it."""

import math

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.graph import nodes_logic
from . import theme

GRID = 8
PICK = 10


def ready_motifs():
    return {"Quatro, dois tamanhos": nodes_logic.read_motif(nodes_logic.MOTIF_DEFAULT),
            "Um ao centro": [(0.5, 0.5, 1.0)],
            "Diagonal": [(0.2, 0.2, 0.5), (0.5, 0.5, 1.0), (0.8, 0.8, 0.5)],
            "Cruz de cinco": [(0.5, 0.5, 1.0), (0.5, 0.15, 0.45), (0.5, 0.85, 0.45), (0.15, 0.5, 0.45),
                              (0.85, 0.5, 0.45)],
            "Três tamanhos": [(0.25, 0.3, 1.0), (0.7, 0.25, 0.6), (0.45, 0.75, 0.35)]}


class MotifPad(QtWidgets.QWidget):
    changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(340, 340)
        self.points = []                 # [(x, y, size)] in the cell (0–1), y up
        self.aspect = 1.0                # the cell's height over its width
        self.shift = 0.0                 # every other row's shift (a share of the cell's width)
        self._drag = None

    def _cell(self):
        side = min(self.width(), self.height()) / 2.0 - 10
        w, h = (side, side * self.aspect) if self.aspect <= 1 else (side / self.aspect, side)
        return QtCore.QRectF((self.width() - w) / 2.0, (self.height() - h) / 2.0, w, h)

    def to_screen(self, x, y, dx=0.0, dy=0.0):
        c = self._cell()
        return QtCore.QPointF(c.left() + (x + dx) * c.width(), c.bottom() - (y + dy) * c.height())

    def to_cell(self, pos):
        c = self._cell()
        x = (pos.x() - c.left()) / c.width()
        y = (c.bottom() - pos.y()) / c.height()
        snap = 1.0 / GRID / 2.0
        return (max(0.0, min(1.0, round(x / snap) * snap)), max(0.0, min(1.0, round(y / snap) * snap)))

    def _radius(self, s):
        c = self._cell()
        return max(3.0, s * min(c.width(), c.height()) * 0.22)

    def _near(self, pos):
        for k, (x, y, s) in enumerate(self.points):
            q = self.to_screen(x, y)
            if math.hypot(q.x() - pos.x(), q.y() - pos.y()) <= max(PICK, self._radius(s)):
                return k
        return None

    def set_points(self, pts):
        self.points = [(float(x), float(y), float(s)) for x, y, s in pts]
        self.update()
        self.changed.emit()

    def mousePressEvent(self, e):
        k = self._near(e.position())
        if e.button() == QtCore.Qt.MouseButton.RightButton:
            if k is not None:
                del self.points[k]
                self.update()
                self.changed.emit()
            return
        if k is None:
            x, y = self.to_cell(e.position())
            self.points.append((x, y, 1.0))
            k = len(self.points) - 1
            self.changed.emit()
        self._drag = k
        self.update()

    def mouseMoveEvent(self, e):
        if self._drag is not None and e.buttons() & QtCore.Qt.MouseButton.LeftButton:
            x, y = self.to_cell(e.position())
            self.points[self._drag] = (x, y, self.points[self._drag][2])
            self.update()
            self.changed.emit()

    def mouseReleaseEvent(self, _e):
        self._drag = None

    def wheelEvent(self, e):
        k = self._near(e.position())
        if k is None:
            return
        x, y, s = self.points[k]
        s = min(2.0, max(0.1, s + (0.1 if e.angleDelta().y() > 0 else -0.1)))
        self.points[k] = (x, y, round(s, 2))
        self.update()
        self.changed.emit()

    def paintEvent(self, _e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QtGui.QColor("#ffffff"))            # (drawings on white paper, whatever the theme)
        c = self._cell()
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(QtGui.QColor(29, 32, 37, 60))
        for j in (-1, 0, 1):                                         # (the cells around, faint)
            for i in (-1, 0, 1):
                if (i, j) == (0, 0):
                    continue
                dx = i + (self.shift if j % 2 else 0.0)
                for x, y, s in self.points:
                    p.drawEllipse(self.to_screen(x, y, dx, j), self._radius(s), self._radius(s))
        p.setPen(QtGui.QPen(QtGui.QColor("#e3e7ec"), 1.0))
        for k in range(GRID + 1):
            x = c.left() + c.width() * k / GRID
            y = c.top() + c.height() * k / GRID
            p.drawLine(QtCore.QPointF(x, c.top()), QtCore.QPointF(x, c.bottom()))
            p.drawLine(QtCore.QPointF(c.left(), y), QtCore.QPointF(c.right(), y))
        p.setPen(QtGui.QPen(QtGui.QColor(theme.C["select"]), 1.6))
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.drawRect(c)
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(QtGui.QColor("#1d2025"))
        for x, y, s in self.points:
            p.drawEllipse(self.to_screen(x, y), self._radius(s), self._radius(s))


class MotifDrawing(QtWidgets.QDialog):
    def __init__(self, text="", aspect=1.0, shift=0.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Motivo da matriz")
        self.result_text = None
        lay = QtWidgets.QVBoxLayout(self)
        hint = QtWidgets.QLabel("A célula a azul repete-se por toda a superfície. Clique põe um furo, arrastar "
                                "muda-o, roda do rato sobre ele muda o tamanho, botão direito tira-o.")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        row = QtWidgets.QHBoxLayout()
        ready = QtWidgets.QComboBox()
        ready.addItem("Começar de…")
        self.ready = ready_motifs()
        ready.addItems(list(self.ready))
        ready.activated.connect(lambda k: k > 0 and self.pad.set_points(self.ready[ready.itemText(k)]))
        clear = QtWidgets.QPushButton("Limpar")
        clear.clicked.connect(lambda: self.pad.set_points([]))
        row.addWidget(ready, 1)
        row.addWidget(clear)
        lay.addLayout(row)
        self.pad = MotifPad()
        self.pad.aspect, self.pad.shift = max(0.2, min(5.0, aspect)), shift
        lay.addWidget(self.pad, 1)
        self.status = QtWidgets.QLabel()
        lay.addWidget(self.status)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok |
                                             QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        self.ok = buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        lay.addWidget(buttons)
        self.pad.changed.connect(self._check)
        try:
            self.pad.set_points(nodes_logic.read_motif(text or nodes_logic.MOTIF_DEFAULT))
        except ValueError:
            self.pad.set_points(self.ready["Quatro, dois tamanhos"])

    def _check(self):
        n = len(self.pad.points)
        self.ok.setEnabled(n > 0)
        self.status.setText("{} furo(s) por célula.".format(n) if n else "Ponha pelo menos um furo na célula.")

    def _accept(self):
        if not self.pad.points:
            return
        self.result_text = nodes_logic.motif_text(self.pad.points)
        self.accept()


def ask(text="", aspect=1.0, shift=0.0, parent=None):
    dlg = MotifDrawing(text, aspect, shift, parent)
    return dlg.result_text if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted else None
