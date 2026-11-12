"""(0.567, PLANO.md «Gerador de revestimentos 3D em IFC», step 4) The windows that lay many Revestimentos at once:

- «Revestir por categoria»: every wall (outside / inside / both), slab (top / underside / edges), column or beam —
  of those chosen, of the storey, or of the whole model — in one finish;
- «Revestir ambientes»: the rooms ticked, finished at once (floor, walls up to a height, skirting, ceiling), and the
  project's rules (kept, applied to every room whose name matches)."""

from PySide6 import QtWidgets

from ..core import covering_finishes as cf
from ..i18n import lang


def finish_combo(none=True, group=None):
    c = QtWidgets.QComboBox()
    if none:
        c.addItem("— (nenhum)", "")
    pt = lang() == "pt"
    for g in cf.GROUPS:
        if group is not None and g not in group:
            continue
        for k, f in cf.FINISHES.items():
            if f.group == g:
                c.addItem("{} ▸ {}".format(cf.GROUPS[g][0 if pt else 1], f.name_pt if pt else f.name_en), k)
    return c


class CategoryDialog(QtWidgets.QDialog):
    def __init__(self, chosen=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Revestir por categoria")
        form = QtWidgets.QFormLayout(self)
        self.category = QtWidgets.QComboBox()
        for k, label in (("parede", "Paredes"), ("laje", "Lajes"), ("pilar", "Pilares"), ("viga", "Vigas")):
            self.category.addItem(label, k)
        self.scope = QtWidgets.QComboBox()
        if chosen:
            self.scope.addItem("Os escolhidos ({})".format(chosen), "escolhidos")
        self.scope.addItem("Do pavimento ativo", "pavimento")
        self.scope.addItem("Do modelo todo", "modelo")
        self.sides = QtWidgets.QComboBox()
        for k, label in (("ambas", "As duas faces"), ("exterior", "Só a face exterior"),
                         ("interior", "Só a face interior (virada para um ambiente)")):
            self.sides.addItem(label, k)
        self.slab = QtWidgets.QComboBox()
        for k, label in (("topo", "O topo (pavimento)"), ("baixo", "Por baixo (teto)"), ("bordos", "Os bordos"),
                         ("topo,bordos", "O topo e os bordos")):
            self.slab.addItem(label, k)
        self.finish = finish_combo(none=False)
        form.addRow("Categoria", self.category)
        form.addRow("Quais", self.scope)
        form.addRow("Paredes: faces", self.sides)
        form.addRow("Lajes: faces", self.slab)
        form.addRow("Revestimento", self.finish)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok |
                                             QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Revestir")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        self.category.currentIndexChanged.connect(lambda _k: self._enable())
        self._enable()

    def _enable(self):
        k = self.category.currentData()
        self.sides.setEnabled(k == "parede")
        self.slab.setEnabled(k == "laje")

    def values(self):
        return {"category": self.category.currentData(), "scope": self.scope.currentData(),
                "sides": self.sides.currentData(), "slab_faces": tuple(self.slab.currentData().split(",")),
                "finish": self.finish.currentData()}


class RoomsDialog(QtWidgets.QDialog):
    """The rooms (of the storey) ticked and their finishes; the project's rules under it."""

    def __init__(self, rooms, rules, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Revestir ambientes")
        self.resize(760, 560)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(QtWidgets.QLabel("Ambientes a revestir agora:"))
        self.rooms = QtWidgets.QListWidget()
        for info in rooms:
            item = QtWidgets.QListWidgetItem("{} {}".format(info.get("number") or "", info.get("name") or "").strip()
                                             or info["guid"])
            item.setData(256, info["guid"])
            item.setCheckState(QtCore_checked(False))
            self.rooms.addItem(item)
        lay.addWidget(self.rooms)
        form = QtWidgets.QFormLayout()
        self.floor = finish_combo()
        self.walls = finish_combo()
        self.height = QtWidgets.QDoubleSpinBox()
        self.height.setRange(0.1, 10.0)
        self.height.setValue(2.10)
        self.height.setSuffix(" m")
        self.skirting = finish_combo(group=("remate",))
        self.ceiling = finish_combo()
        form.addRow("Pavimento", self.floor)
        form.addRow("Paredes", self.walls)
        form.addRow("…até à altura", self.height)
        form.addRow("Rodapé (onde as paredes não são revestidas)", self.skirting)
        form.addRow("Teto", self.ceiling)
        lay.addLayout(form)
        box = QtWidgets.QGroupBox("Regras do projeto (aplicadas a todos os ambientes cujo nome tem uma destas "
                                  "palavras; «|» entre elas)")
        bl = QtWidgets.QVBoxLayout(box)
        self.rules = QtWidgets.QTableWidget(0, 3)
        self.rules.setHorizontalHeaderLabels(("Regra", "Ambientes (palavras)", "O que faz"))
        self.rules.horizontalHeader().setStretchLastSection(True)
        bl.addWidget(self.rules)
        row = QtWidgets.QHBoxLayout()
        self.rule_name = QtWidgets.QLineEdit()
        self.rule_name.setPlaceholderText("Nome da regra (ex.: Instalações sanitárias)")
        self.rule_rooms = QtWidgets.QLineEdit()
        self.rule_rooms.setPlaceholderText("Palavras (ex.: WC|banho|sanitária)")
        save = QtWidgets.QPushButton("Guardar a escolha acima como regra")
        save.clicked.connect(self._save_rule)
        drop = QtWidgets.QPushButton("Tirar a regra escolhida")
        drop.clicked.connect(lambda: self.rules.removeRow(self.rules.currentRow()))
        for w in (self.rule_name, self.rule_rooms, save, drop):
            row.addWidget(w)
        bl.addLayout(row)
        self.apply_rules = QtWidgets.QCheckBox("Aplicar também as regras (refaz o que cada regra fez antes)")
        bl.addWidget(self.apply_rules)
        lay.addWidget(box)
        self._rules = list(rules)
        for r in self._rules:
            self._rule_row(r)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok |
                                             QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Revestir")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def _rule_row(self, r):
        k = self.rules.rowCount()
        self.rules.insertRow(k)
        what = ", ".join("{}: {}".format(label, cf.finish(r[key]).name_pt) for key, label in
                         (("floor", "pavimento"), ("walls", "paredes"), ("skirting", "rodapé"), ("ceiling", "teto"))
                         if r.get(key))
        if r.get("walls"):
            what += " até {:.2f} m".format(float(r.get("wall_height") or 2.1)).replace(".", ",")
        for c, text in enumerate((r["name"], r.get("rooms") or "", what)):
            self.rules.setItem(k, c, QtWidgets.QTableWidgetItem(text))

    def _save_rule(self):
        name = self.rule_name.text().strip()
        if not name:
            return
        r = dict(self.choice(), name=name, rooms=self.rule_rooms.text().strip())
        self._rules = [q for q in self._rules if q["name"] != name] + [r]
        self.rules.setRowCount(0)
        for q in self._rules:
            self._rule_row(q)

    def choice(self):
        return {"floor": self.floor.currentData(), "walls": self.walls.currentData(),
                "wall_height": self.height.value(), "skirting": self.skirting.currentData(),
                "ceiling": self.ceiling.currentData()}

    def values(self):
        """{rooms: [guids ticked], choice, rules: [the rules kept], apply_rules}."""
        kept = {self.rules.item(k, 0).text() for k in range(self.rules.rowCount()) if self.rules.item(k, 0)}
        ticked = [self.rooms.item(k).data(256) for k in range(self.rooms.count())
                  if self.rooms.item(k).checkState() == QtCore_checked(True)]
        return {"rooms": ticked, "choice": self.choice(), "rules": [r for r in self._rules if r["name"] in kept],
                "apply_rules": self.apply_rules.isChecked()}


def QtCore_checked(on):
    from PySide6 import QtCore
    return QtCore.Qt.CheckState.Checked if on else QtCore.Qt.CheckState.Unchecked
