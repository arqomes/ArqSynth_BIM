"""(0.566, PLANO.md «Gerador de revestimentos 3D em IFC», step 5) «Faixas, cercadura e mistura» of a Revestimento: the
bands across it (a frieze at a height, a skirting row, a dado) and the border round it, each its own piece, bond and
material over the finish's; and the mix — the pieces of the main layout each one of a few materials at random (stone
and wood of several tones, a two-colour wall)."""

from PySide6 import QtWidgets

from ..core import tiling as tl
from ..i18n import lang
from ..ifc import catalog

COLS = ("Tipo", "De (m)", "Até / largura (m)", "Material", "Peça L (m)", "Peça A (m)", "Aparelho")


def _materials():
    pt = lang() == "pt"
    return sorted(((m.name_pt if pt else m.name_en), k) for k, m in catalog.MATERIALS.items())


class CoveringExtrasDialog(QtWidgets.QDialog):
    def __init__(self, zones=(), mix=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Faixas, cercadura e mistura")
        self.resize(820, 420)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(QtWidgets.QLabel("Faixas (a uma altura, medida a partir do fundo da face) e cercadura (à volta "
                                       "da face), cada uma com a sua peça e o seu material:"))
        self.table = QtWidgets.QTableWidget(0, len(COLS))
        self.table.setHorizontalHeaderLabels(COLS)
        self.table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.table)
        row = QtWidgets.QHBoxLayout()
        add_band = QtWidgets.QPushButton("+ Faixa")
        add_border = QtWidgets.QPushButton("+ Cercadura")
        remove = QtWidgets.QPushButton("− Tirar a escolhida")
        add_band.clicked.connect(lambda: self.add({"kind": "faixa", "y0": 1.2, "y1": 1.25, "w": 0.25, "h": 0.05,
                                                   "material": "marmore"}))
        add_border.clicked.connect(lambda: self.add({"kind": "cercadura", "width": 0.10, "w": 0.30, "h": 0.10,
                                                     "material": "granito"}))
        remove.clicked.connect(lambda: self.table.removeRow(self.table.currentRow()))
        for b in (add_band, add_border, remove):
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        box = QtWidgets.QGroupBox("Mistura — cada peça um destes materiais, ao acaso (vazio: o do revestimento)")
        form = QtWidgets.QHBoxLayout(box)
        self.mix = []
        mats = _materials()
        current = list((mix or {}).get("materials", []))
        for k in range(3):
            c = QtWidgets.QComboBox()
            c.addItem("—", "")
            for name, key in mats:
                c.addItem(name, key)
            if k < len(current):
                c.setCurrentIndex(max(0, c.findData(current[k])))
            form.addWidget(c)
            self.mix.append(c)
        self.seed = QtWidgets.QSpinBox()
        self.seed.setRange(0, 9999)
        self.seed.setValue(int((mix or {}).get("seed", 1)))
        self.seed.setPrefix("variação ")
        form.addWidget(self.seed)
        lay.addWidget(box)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok |
                                             QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)
        for z in zones or ():
            self.add(z)

    def add(self, z):
        r = self.table.rowCount()
        self.table.insertRow(r)
        kind = QtWidgets.QComboBox()
        kind.addItem("Faixa", "faixa")
        kind.addItem("Cercadura", "cercadura")
        kind.setCurrentIndex(0 if z.get("kind") == "faixa" else 1)
        self.table.setCellWidget(r, 0, kind)
        band = z.get("kind") == "faixa"
        self.table.setItem(r, 1, QtWidgets.QTableWidgetItem("{:.3f}".format(float(z.get("y0", 0.0))) if band else ""))
        self.table.setItem(r, 2, QtWidgets.QTableWidgetItem("{:.3f}".format(float(z.get("y1", 0.0) if band
                                                                                  else z.get("width", 0.1)))))
        mat = QtWidgets.QComboBox()
        for name, key in _materials():
            mat.addItem(name, key)
        mat.setCurrentIndex(max(0, mat.findData(z.get("material", "marmore"))))
        self.table.setCellWidget(r, 3, mat)
        self.table.setItem(r, 4, QtWidgets.QTableWidgetItem("{:.3f}".format(float(z.get("w", 0.25)))))
        self.table.setItem(r, 5, QtWidgets.QTableWidgetItem("{:.3f}".format(float(z.get("h", 0.05)))))
        pat = QtWidgets.QComboBox()
        for key, (pt_name, en) in tl.PATTERNS.items():
            if key != "livre":
                pat.addItem(pt_name if lang() == "pt" else en, key)
        pat.setCurrentIndex(max(0, pat.findData(z.get("pattern", "eito"))))
        self.table.setCellWidget(r, 6, pat)

    @staticmethod
    def _num(item, default):
        try:
            return float((item.text() if item is not None else "").replace(",", "."))
        except ValueError:
            return default

    def values(self):
        """(zones, mix)."""
        zones = []
        for r in range(self.table.rowCount()):
            kind = self.table.cellWidget(r, 0).currentData()
            z = {"kind": kind, "material": self.table.cellWidget(r, 3).currentData(),
                 "w": self._num(self.table.item(r, 4), 0.25), "h": self._num(self.table.item(r, 5), 0.05),
                 "pattern": self.table.cellWidget(r, 6).currentData()}
            if kind == "faixa":
                z.update(y0=self._num(self.table.item(r, 1), 1.2), y1=self._num(self.table.item(r, 2), 1.25))
            else:
                z["width"] = self._num(self.table.item(r, 2), 0.1)
            zones.append(z)
        mats = [c.currentData() for c in self.mix if c.currentData()]
        return zones, ({"materials": mats, "seed": self.seed.value()} if mats else {})
