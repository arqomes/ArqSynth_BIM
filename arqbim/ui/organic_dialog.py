"""(0.555, PLANO.md «Gerador de formas orgânicas», step 2) The «Forma orgânica» window: over what is selected in the
model (a polygon or any closed drawing, a wall's face, a slab, a ceiling) or from measures (a rectangle, circle,
ellipse or regular polygon), the behaviour (membrane, cushion, catenary, smoothing), how high, the grid and what it is
used for — with a small picture of its section, drawn as it changes."""

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..core import form_finding as ff
from . import theme

BEHAVIOURS = (("catenaria", "Catenária — casca que só trabalha à compressão (abóbadas, Gaudí, Isler)"),
              ("almofada", "Almofada inflada — pressão por dentro (ETFE, «nuvens»)"),
              ("membrana", "Membrana tensionada — esticada por um mastro (tendas, velas)"),
              ("suavizar", "Suavizar — arredonda a forma, sem a encolher"))
SHAPES = (("retangulo", "Retângulo"), ("circulo", "Círculo"), ("elipse", "Elipse"), ("poligono", "Polígono regular"))
USAGES = (("", "Automático (cobertura; numa parede, fachada)"), ("cobertura", "Cobertura"), ("pala", "Pala"),
          ("estrutura", "Estrutura / pavilhão"), ("fachada", "Fachada"))


class Section(QtWidgets.QWidget):
    """A section through the middle of a square form of that behaviour and height — to see what it does."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(110)
        self.behaviour, self.height_ = "catenaria", 2.0

    def show_form(self, behaviour, height):
        self.behaviour, self.height_ = behaviour, height
        self.update()

    def paintEvent(self, _e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QtGui.QColor("#ffffff"))
        n = 17
        t = np.linspace(0.0, 10.0, n)
        x, y = np.meshgrid(t, t)
        rows = np.stack((x, y, np.zeros_like(x)), axis=-1)
        fixed = None
        if self.behaviour == "membrana":
            fixed = ff.boundary_mask(rows.shape, False)
            fixed[n // 2, n // 2] = True
            rows[n // 2, n // 2, 2] = self.height_
        elif self.behaviour == "suavizar":
            rows[1:-1, 1:-1, 2] = abs(self.height_) * (1 + 0.3 * np.sin(x[1:-1, 1:-1] * 2) * np.cos(y[1:-1, 1:-1]))
        try:
            form = ff.find(rows, self.behaviour, self.height_, fixed=fixed, steps=800)
        except ff.FormError:
            return
        cut = form[n // 2]
        w, h = self.width(), self.height()
        top = max(4.0, float(np.abs(cut[:, 2]).max()))
        s = min((w - 20) / 10.0, (h - 20) / (top * 1.3 + 1e-9))
        base = h / 2.0 + (top * s / 2.0 if self.height_ >= 0 else -top * s / 2.0)
        pts = [QtCore.QPointF(10 + q[0] * s, base - q[2] * s) for q in cut]
        p.setPen(QtGui.QPen(QtGui.QColor("#9aa3ad"), 1.0, QtCore.Qt.PenStyle.DashLine))
        p.drawLine(QtCore.QPointF(10, base), QtCore.QPointF(w - 10, base))
        p.setPen(QtGui.QPen(QtGui.QColor(theme.C["select"]), 2.4))
        p.drawPolyline(QtGui.QPolygonF(pts))


class OrganicDialog(QtWidgets.QDialog):
    """`source_text`: what is selected, in words (None: nothing that serves — only measures)."""

    def __init__(self, source_text=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Forma orgânica")
        lay = QtWidgets.QVBoxLayout(self)
        self.on_chosen = QtWidgets.QRadioButton("Sobre o escolhido: {}".format(source_text or "—"))
        self.on_measures = QtWidgets.QRadioButton("Com medidas")
        self.on_chosen.setEnabled(source_text is not None)
        (self.on_chosen if source_text is not None else self.on_measures).setChecked(True)
        lay.addWidget(self.on_chosen)
        lay.addWidget(self.on_measures)
        self.measures = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(self.measures)
        form.setContentsMargins(18, 0, 0, 0)
        self.shape = QtWidgets.QComboBox()
        for key, label in SHAPES:
            self.shape.addItem(label, key)
        self.length = self._spin(12.0, 0.5, 200.0)
        self.width = self._spin(8.0, 0.5, 200.0)
        self.sides = QtWidgets.QSpinBox()
        self.sides.setRange(3, 24)
        self.sides.setValue(6)
        form.addRow("Forma", self.shape)
        form.addRow("Comprimento (ou diâmetro)", self.length)
        form.addRow("Largura", self.width)
        form.addRow("Lados", self.sides)
        lay.addWidget(self.measures)
        box = QtWidgets.QFormLayout()
        self.behaviour = QtWidgets.QComboBox()
        for key, label in BEHAVIOURS:
            self.behaviour.addItem(label, key)
        self.height_spin = self._spin(3.0, -50.0, 50.0)
        self.height_spin.setToolTip("Quanto sobe acima do contorno (na membrana: a altura do mastro). Negativa: "
                                    "pendurada, para baixo.")
        self.grid = QtWidgets.QComboBox()
        self.grid.addItem("Quadrícula (quatro lados)", "quadras")
        self.grid.addItem("Anéis até ao centro (redondos)", "aneis")
        self.usage = QtWidgets.QComboBox()
        for key, label in USAGES:
            self.usage.addItem(label, key)
        self.volume = QtWidgets.QComboBox()                # (0.560) a sheet, or a closed body
        self.volume.addItem("Superfície aberta", "aberta")
        self.volume.addItem("Volume assente (fechado por baixo)", "assente")
        self.volume.addItem("Volume em lente (as duas faces)", "lente")
        self.volume.addItem("Massas fundidas (dos círculos escolhidos)", "blobs")
        self.volume.setToolTip("Fechado: um volume (banco, pavilhão, almofada). Massas fundidas: cada círculo "
                               "escolhido é uma massa; juntas fundem-se como gotas.")
        box.addRow("Comportamento", self.behaviour)
        box.addRow("Altura (m)", self.height_spin)
        box.addRow("Grelha", self.grid)
        box.addRow("Corpo", self.volume)
        box.addRow("Uso", self.usage)
        lay.addLayout(box)
        self.section = Section()
        lay.addWidget(QtWidgets.QLabel("Corte pelo meio:"))
        lay.addWidget(self.section)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok |
                                             QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Criar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)
        for w in (self.on_chosen, self.on_measures):
            w.toggled.connect(lambda _on: self._enable())
        self.shape.currentIndexChanged.connect(lambda _k: self._enable())
        self.behaviour.currentIndexChanged.connect(lambda _k: self._draw())
        self.height_spin.valueChanged.connect(lambda _v: self._draw())
        self._enable()
        self._draw()

    @staticmethod
    def _spin(value, lo, hi):
        s = QtWidgets.QDoubleSpinBox()
        s.setRange(lo, hi)
        s.setDecimals(2)
        s.setSingleStep(0.5)
        s.setSuffix(" m")
        s.setValue(value)
        return s

    def _enable(self):
        own = self.on_measures.isChecked()
        self.measures.setEnabled(own)
        shape = self.shape.currentData()
        self.width.setEnabled(own and shape in ("retangulo", "elipse"))
        self.sides.setEnabled(own and shape == "poligono")
        if own and shape in ("circulo", "poligono") and self.grid.currentData() == "quadras":
            self.grid.setCurrentIndex(1)

    def _draw(self):
        self.section.show_form(self.behaviour.currentData(), self.height_spin.value())

    def values(self):
        """{"measures": bool, "shape", "length", "width", "sides", "behaviour", "height", "grid", "usage"}."""
        return {"measures": self.on_measures.isChecked(), "shape": self.shape.currentData(),
                "length": self.length.value(), "width": self.width.value(), "sides": self.sides.value(),
                "behaviour": self.behaviour.currentData(), "height": self.height_spin.value(),
                "grid": self.grid.currentData(), "usage": self.usage.currentData() or None,
                "volume": self.volume.currentData()}
