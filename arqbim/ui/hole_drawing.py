"""(0.551) The hole of one's own drawing: a small window to draw a hole's outline — a click puts a corner, dragging a
corner moves it, the right button takes it away — or to start from a ready one (star, cross, drop, leaf, arrow). Its
result is core/surfaces.drawn_text's shape text, which «Perfurar» uses with «Forma: desenho»."""

import math

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..core import surfaces
from . import theme

GRID = 10                     # the pad's grid: points snap to it (1/GRID of its width)
PICK = 9                      # px: how near a corner a click takes it


def _circle(n, r=1.0, start=90.0):
    a = np.radians(start + np.arange(n) * 360.0 / n)
    return np.column_stack((r * np.cos(a), r * np.sin(a)))


def ready_shapes():
    """{name: points} the pad starts from."""
    star = _circle(10)
    star[1::2] *= 0.45
    cross = np.array([(-1, -0.3), (-0.3, -0.3), (-0.3, -1), (0.3, -1), (0.3, -0.3), (1, -0.3), (1, 0.3), (0.3, 0.3),
                      (0.3, 1), (-0.3, 1), (-0.3, 0.3), (-1, 0.3)], dtype=float)
    t = np.radians(np.linspace(0, 360, 25)[:-1])
    drop = np.column_stack((np.sin(t) * (1 - np.sin(t / 2)) * 0.9, -np.cos(t)))
    leaf = np.vstack((np.column_stack((np.sin(np.linspace(0, math.pi, 12)) * 0.45, np.linspace(-1, 1, 12))),
                      np.column_stack((-np.sin(np.linspace(math.pi, 0, 12)[1:-1]) * 0.45, np.linspace(1, -1, 12)[1:-1]))))
    arrow = np.array([(0, 1), (0.8, 0.1), (0.3, 0.1), (0.3, -1), (-0.3, -1), (-0.3, 0.1), (-0.8, 0.1)], dtype=float)
    return {"Estrela": star, "Cruz": cross, "Gota": drop, "Folha": leaf, "Seta": arrow, "Hexágono": _circle(6)}


class Pad(QtWidgets.QWidget):
    changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 320)
        self.points = []              # in −1…1, y up
        self._drag = None
        self.setMouseTracking(True)

    def _box(self):
        side = min(self.width(), self.height()) - 20
        return QtCore.QRectF((self.width() - side) / 2.0, (self.height() - side) / 2.0, side, side)

    def to_screen(self, p):
        b = self._box()
        return QtCore.QPointF(b.center().x() + p[0] * b.width() / 2.0, b.center().y() - p[1] * b.height() / 2.0)

    def to_pad(self, pos):
        b = self._box()
        x = (pos.x() - b.center().x()) / (b.width() / 2.0)
        y = -(pos.y() - b.center().y()) / (b.height() / 2.0)
        snap = 2.0 / GRID / 2.0                          # (half a grid square)
        return (max(-1.0, min(1.0, round(x / snap) * snap)), max(-1.0, min(1.0, round(y / snap) * snap)))

    def _near(self, pos):
        for k, p in enumerate(self.points):
            q = self.to_screen(p)
            if math.hypot(q.x() - pos.x(), q.y() - pos.y()) <= PICK:
                return k
        return None

    def set_points(self, pts):
        pts = np.asarray(pts, dtype=float).reshape(-1, 2)
        if len(pts):
            pts = pts - (pts.min(axis=0) + pts.max(axis=0)) / 2.0
            pts = pts / max(float(np.abs(pts).max()), 1e-9) * 0.9
        self.points = [tuple(map(float, p)) for p in pts]
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
        if k is not None:
            self._drag = k
            return
        self.points.append(self.to_pad(e.position()))
        self._drag = len(self.points) - 1
        self.update()
        self.changed.emit()

    def mouseMoveEvent(self, e):
        if self._drag is not None and e.buttons() & QtCore.Qt.MouseButton.LeftButton:
            self.points[self._drag] = self.to_pad(e.position())
            self.update()
            self.changed.emit()

    def mouseReleaseEvent(self, _e):
        self._drag = None

    def paintEvent(self, _e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QtGui.QColor("#ffffff"))            # (drawings on white paper, whatever the theme)
        b = self._box()
        p.setPen(QtGui.QPen(QtGui.QColor("#e3e7ec"), 1.0))
        for k in range(GRID + 1):
            x = b.left() + b.width() * k / GRID
            y = b.top() + b.height() * k / GRID
            p.drawLine(QtCore.QPointF(x, b.top()), QtCore.QPointF(x, b.bottom()))
            p.drawLine(QtCore.QPointF(b.left(), y), QtCore.QPointF(b.right(), y))
        p.setPen(QtGui.QPen(QtGui.QColor("#9aa3ad"), 1.0, QtCore.Qt.PenStyle.DashLine))
        p.drawLine(QtCore.QPointF(b.center().x(), b.top()), QtCore.QPointF(b.center().x(), b.bottom()))
        p.drawLine(QtCore.QPointF(b.left(), b.center().y()), QtCore.QPointF(b.right(), b.center().y()))
        if self.points:
            poly = QtGui.QPolygonF([self.to_screen(q) for q in self.points])
            p.setBrush(QtGui.QColor(29, 32, 37, 200) if self.valid() else QtGui.QColor(theme.ART["red"]))
            p.setPen(QtGui.QPen(QtGui.QColor("#1d2025"), 1.6))
            p.drawPolygon(poly) if len(self.points) >= 3 else p.drawPolyline(poly)
            p.setBrush(QtGui.QColor(theme.C["select"]))
            p.setPen(QtGui.QPen(QtGui.QColor("#ffffff"), 1.2))
            for q in self.points:
                p.drawEllipse(self.to_screen(q), 4.5, 4.5)

    def valid(self):
        try:
            surfaces.drawn_text(self.points)
        except ValueError:
            return False
        return True


class HoleDrawing(QtWidgets.QDialog):
    """`text`: the shape text to start from (« »: a star). After exec(): `result_text`."""

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Desenho do furo")
        self.result_text = None
        lay = QtWidgets.QVBoxLayout(self)
        hint = QtWidgets.QLabel("Clique para pôr cantos, arraste um canto para o mudar, botão direito tira-o. O "
                                "furo fica com o tamanho, a rotação e o alongamento do nó «Perfurar».")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        row = QtWidgets.QHBoxLayout()
        ready = QtWidgets.QComboBox()
        ready.addItem("Começar de…")
        self.ready = ready_shapes()
        ready.addItems(list(self.ready))
        ready.activated.connect(lambda k: k > 0 and self.pad.set_points(self.ready[ready.itemText(k)]))
        clear = QtWidgets.QPushButton("Limpar")
        clear.clicked.connect(lambda: self.pad.set_points([]))
        row.addWidget(ready, 1)
        row.addWidget(clear)
        lay.addLayout(row)
        self.pad = Pad()
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
        ring = surfaces.drawn_ring(text) if text else None
        self.pad.set_points(ring if ring is not None else self.ready["Estrela"])

    def _check(self):
        good = self.pad.valid()
        self.ok.setEnabled(good)
        self.status.setText("{} cantos.".format(len(self.pad.points)) if good else
                            "Faltam cantos, ou os lados cruzam-se.")
        self.status.setStyleSheet("" if good else "color: %s;" % theme.ART["red"])

    def _accept(self):
        try:
            self.result_text = surfaces.drawn_text(self.pad.points)
        except ValueError as e:
            self.status.setText(str(e))
            return
        self.accept()


def ask(text="", parent=None):
    """The shape text drawn (None: given up)."""
    dlg = HoleDrawing(text, parent)
    return dlg.result_text if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted else None
