"""(0.541, the owner: «O botão no BIM deve abrir apenas o painel lateral com os operadores guardados, nesse painel deve
ficar os botões de aplicar, criar novo, editar») The side panel of the «Gráfico Visual» module: the operators kept in
the suite's library (core/graph/operators.py) — each with its thumbnail and name —, what they will be applied to (the
wall chosen in the model, and its face), and the buttons: Aplicar, Criar novo, Editar, Duplicar, Mudar o nome,
Apagar, Importar…, Exportar…. A double click applies."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.graph import operators
from ..core.graph.graph import GraphError
from . import theme

SLUG = QtCore.Qt.ItemDataRole.UserRole
ICON = QtCore.QSize(120, 76)


class OperatorsPanel(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__("Operadores", parent)
        self.setObjectName("operators")
        self.on_apply = None             # (slug, side, values {(node id, measure): value})
        self.on_new = None               # (side)
        self.on_edit = None              # (slug, side)
        self.on_update = None            # (): the chosen walls' panels worked out again (0.543)
        self.on_edit_wall = None         # (): the chosen wall's panel opened in the editor (0.543)
        self.target = lambda: 0          # () -> how many walls are chosen in the model
        self.kept = lambda: 0            # () -> how many panels with an operator the chosen walls have (0.543)
        self.values = {}                 # the measures in sight changed for the next «Aplicar»
        page = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(page)
        column.setContentsMargins(4, 4, 4, 4)
        self.hint = QtWidgets.QLabel("Escolha uma parede, um teto ou uma laje no modelo, um operador nesta lista, e "
                                     "«Aplicar».")
        self.hint.setToolTip("Parede direita ou curva: o painel fica na face. Teto: o próprio teto fica perfurado. "
                             "Laje: faz-se um teto falso perfurado 30 cm por baixo dela.")
        self.hint.setWordWrap(True)
        column.addWidget(self.hint)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Procurar operador…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _t: self._filter())
        column.addWidget(self.search)
        self.list = QtWidgets.QListWidget()
        self.list.setIconSize(ICON)
        self.list.setMinimumWidth(140)
        self.list.setWordWrap(True)
        self.list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.itemDoubleClicked.connect(lambda _it: self._apply())
        self.list.currentItemChanged.connect(lambda _a, _b: (self._measures(), self.refresh_target()))
        self.list.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._menu)
        column.addWidget(self.list, 1)
        # (0.543) the chosen operator's measures «à vista»: changed here, without opening the editor
        self.measures_title = QtWidgets.QLabel("Medidas")
        self.measures_title.setObjectName("operators_measures_title")
        column.addWidget(self.measures_title)
        self.measures_host = QtWidgets.QWidget()
        self.measures = QtWidgets.QFormLayout(self.measures_host)
        self.measures.setContentsMargins(0, 0, 0, 0)
        self.measures.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapAllRows)
        column.addWidget(self.measures_host)
        self.measures_hint = QtWidgets.QLabel("Nenhuma à vista (no editor, marque «à vista» numa medida).")
        self.measures_hint.setWordWrap(True)
        column.addWidget(self.measures_hint)
        self.target_label = QtWidgets.QLabel()
        self.target_label.setWordWrap(True)
        self.target_label.setObjectName("operators_target")
        column.addWidget(self.target_label)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Face:"))
        self.side = QtWidgets.QComboBox()
        self.side.addItems(["à vista (automático)", *operators.SIDES])
        self.side.setToolTip("A face da parede que recebe o painel: a que está virada para si na vista 3D, ou a "
                             "que escolher aqui.")
        self.side.setMinimumWidth(40)
        row.addWidget(self.side, 1)
        column.addLayout(row)
        self.apply_button = QtWidgets.QPushButton("Aplicar")
        self.apply_button.setToolTip("Põe o operador escolhido na face da parede escolhida no modelo.")
        self.apply_button.clicked.connect(self._apply)
        self.new_button = QtWidgets.QPushButton("Criar novo")
        self.new_button.setToolTip("Abre o Gráfico Visual com a face da parede escolhida, para criar um operador.")
        self.new_button.clicked.connect(lambda: self.on_new and self.on_new(self.chosen_side()))
        self.edit_button = QtWidgets.QPushButton("Editar")
        self.edit_button.setToolTip("Abre o operador escolhido no Gráfico Visual, sobre a face da parede escolhida.")
        self.edit_button.clicked.connect(self._edit)
        self.dup_button = QtWidgets.QPushButton("Duplicar")
        self.dup_button.clicked.connect(self._duplicate)
        self.rename_button = QtWidgets.QPushButton("Mudar o nome")
        self.rename_button.clicked.connect(self._rename)
        self.delete_button = QtWidgets.QPushButton("Apagar")
        self.delete_button.clicked.connect(self._delete)
        self.import_button = QtWidgets.QPushButton("Importar…")
        self.import_button.clicked.connect(self._import)
        self.export_button = QtWidgets.QPushButton("Exportar…")
        self.export_button.clicked.connect(self._export)
        self.update_button = QtWidgets.QPushButton("Atualizar na parede")
        self.update_button.setToolTip("Refaz os painéis das paredes escolhidas com o operador que cada um guarda: "
                                      "depois de mudar a parede (uma janela nova, mais comprida).")
        self.update_button.clicked.connect(lambda: self.on_update and self.on_update())
        self.edit_wall_button = QtWidgets.QPushButton("Editar o da parede")
        self.edit_wall_button.setToolTip("Abre no Gráfico Visual o operador que o painel da parede escolhida guarda; "
                                         "«Aplicar ao modelo» refaz esse painel.")
        self.edit_wall_button.clicked.connect(lambda: self.on_edit_wall and self.on_edit_wall())
        grid = QtWidgets.QGridLayout()
        self.apply_button.setDefault(True)
        grid.addWidget(self.apply_button, 0, 0, 1, 2)
        for k, b in enumerate((self.new_button, self.edit_button, self.update_button, self.edit_wall_button)):
            grid.addWidget(b, 1 + k // 2, k % 2)
        # (0.543) the library's housekeeping in one «Mais ▾»: the list of operators keeps the room
        self.more_button = QtWidgets.QPushButton("Mais ▾")
        self.more_button.setToolTip("Duplicar, mudar o nome, apagar, importar e exportar operadores.")
        more = QtWidgets.QMenu(self.more_button)
        for b in (self.dup_button, self.rename_button, self.delete_button, self.import_button, self.export_button):
            act = more.addAction(b.text())
            act.triggered.connect(b.click)
            b.hide()
            b.act = act
        self.more_button.setMenu(more)
        self.more_button.setMinimumWidth(40)
        grid.addWidget(self.more_button, 3, 0, 1, 2)
        for b in (self.apply_button, self.new_button, self.edit_button, self.dup_button, self.rename_button,
                  self.delete_button, self.import_button, self.export_button, self.update_button,
                  self.edit_wall_button):
            b.setMinimumWidth(40)
            b.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
        column.addLayout(grid)
        self.folder_label = QtWidgets.QLabel()
        self.folder_label.setWordWrap(True)
        column.addWidget(self.folder_label)
        self.setWidget(page)
        self.visibilityChanged.connect(lambda shown: self.reload() if shown else None)
        self.restyle()

    def restyle(self):
        muted = "color: %s;" % theme.qcolor(theme.C["muted"]).name()
        for label in (self.hint, self.folder_label, self.measures_hint):
            label.setStyleSheet(muted)
        self.target_label.setStyleSheet("font-weight: 600;")
        self.measures_title.setStyleSheet("font-weight: 600;")

    def _measures(self):
        """(0.543) The chosen operator's measures in sight, as its editor shows them (sliders, ticks, lists)."""
        from . import visual_graph
        self.values = {}
        while self.measures.rowCount():
            self.measures.removeRow(0)
        slug, shown = self.current(), 0
        if slug is not None:
            try:
                graph, exposed = operators.exposed_of(slug)
            except GraphError:
                graph, exposed = None, []
            maker = getattr(self, "_maker", None) or visual_graph.ParamsPanel()
            self._maker = maker                        # (its editors are made by the editor's own code)
            for nid, name in exposed:
                node = graph.nodes[nid]
                spec = graph.registry.get(node["type"])
                port = spec.port("params", name)
                editor = maker._editor(port, node["params"][name], node["type"],
                                       emit=lambda _n, v, key=(nid, name): self.values.__setitem__(key, v))
                self.measures.addRow("{} · {}".format(spec.label, port.label or port.name), editor)
                shown += 1
        self.measures_hint.setVisible(slug is not None and not shown)
        self.measures_title.setVisible(slug is not None)

    # ---- the list
    def reload(self, keep=None):
        keep = keep or self.current()
        self.list.clear()
        for op in operators.listing():
            item = QtWidgets.QListWidgetItem(op["name"])
            item.setData(SLUG, op["slug"])
            item.setToolTip(op["about"] or op["name"])
            if not op["thumbnail"]:                    # (the program's own, or an imported one: drawn once)
                op["thumbnail"] = self._draw_thumbnail(op["slug"])
            if op["thumbnail"]:
                item.setIcon(QtGui.QIcon(op["thumbnail"]))
            self.list.addItem(item)
            if op["slug"] == keep:
                self.list.setCurrentItem(item)
        if self.list.currentItem() is None and self.list.count():
            self.list.setCurrentRow(0)
        self.folder_label.setText("Guardados para todos os projetos.")
        self.folder_label.setToolTip(operators.folder())
        self._filter()
        self.refresh_target()

    @staticmethod
    def _draw_thumbnail(slug):
        from . import visual_graph
        try:
            png = visual_graph.operator_png(operators.load(slug)[2])
            with open(operators.thumbnail_path(slug), "wb") as f:
                f.write(png)
        except Exception:  # (an operator that cannot be worked out: listed by its name alone)
            return ""
        return operators.thumbnail_path(slug)

    def _filter(self):
        text = self.search.text().strip().lower()
        for k in range(self.list.count()):
            item = self.list.item(k)
            item.setHidden(bool(text) and text not in item.text().lower())

    def current(self):
        item = self.list.currentItem()
        return item.data(SLUG) if item is not None else None

    def chosen_side(self):
        """"frente" | "trás" — or None: the face in view (the window works it out)."""
        return None if self.side.currentIndex() == 0 else self.side.currentText()

    def refresh_target(self):
        """What «Aplicar» would work on, said under the list; the buttons that need something chosen."""
        n = self.target() if self.target else 0
        self.target_label.setText("Nenhuma parede, teto ou laje escolhida." if not n else
                                  "1 superfície escolhida." if n == 1 else "{} superfícies escolhidas.".format(n))
        one = self.current() is not None
        kept = self.kept() if self.kept else 0
        if kept:
            self.target_label.setText(self.target_label.text() + " {} painel(éis) com operador.".format(kept))
        self.update_button.setEnabled(kept > 0)
        self.edit_wall_button.setEnabled(kept > 0)
        self.apply_button.setEnabled(one and n > 0)
        for b in (self.edit_button, self.dup_button, self.rename_button, self.delete_button, self.export_button):
            b.setEnabled(one)
            if getattr(b, "act", None) is not None:
                b.act.setEnabled(one)

    # ---- the buttons
    def _apply(self):
        if self.current() is None:
            return
        if not (self.target() if self.target else 0):
            QtWidgets.QMessageBox.information(self, "Operadores", "Escolha primeiro uma parede, um teto ou uma laje "
                                              "no modelo.")
            return
        if self.on_apply:
            self.on_apply(self.current(), self.chosen_side(), dict(self.values))

    def _edit(self):
        if self.current() is not None and self.on_edit:
            self.on_edit(self.current(), self.chosen_side())

    def _guard(self, fn, *args):
        try:
            return fn(*args)
        except (GraphError, OSError, KeyError, ValueError) as e:
            QtWidgets.QMessageBox.warning(self, "Operadores", str(e))
            return None

    def _duplicate(self):
        if self.current() is not None:
            self.reload(self._guard(operators.duplicate, self.current()))

    def _rename(self):
        item = self.list.currentItem()
        if item is None:
            return
        name, ok = QtWidgets.QInputDialog.getText(self, "Mudar o nome", "Nome do operador:", text=item.text())
        if ok and name.strip():
            self._guard(operators.rename, self.current(), name)
            self.reload()

    def _delete(self):
        item = self.list.currentItem()
        if item is None:
            return
        answer = QtWidgets.QMessageBox.question(
            self, "Apagar operador", "Apagar «{}» da biblioteca? Sai de todos os projetos (os painéis já aplicados "
            "ficam).".format(item.text()))
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            operators.delete(self.current())
            self.reload()

    def _import(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Importar operador", "", "Operador ArqSynth (*.json)")
        if path:
            self.reload(self._guard(operators.import_from, path))

    def _export(self):
        item = self.list.currentItem()
        if item is None:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Exportar operador", self.current() + ".json",
                                                        "Operador ArqSynth (*.json)")
        if path:
            self._guard(operators.export_to, self.current(), path)

    def _menu(self, pos):
        item = self.list.itemAt(pos)
        if item is None:
            return
        self.list.setCurrentItem(item)
        menu = QtWidgets.QMenu(self)
        apply_ = menu.addAction("Aplicar", self._apply)
        apply_.setEnabled(self.apply_button.isEnabled())
        menu.addAction("Editar", self._edit)
        menu.addAction("Duplicar", self._duplicate)
        menu.addAction("Mudar o nome", self._rename)
        menu.addAction("Exportar…", self._export)
        menu.addSeparator()
        menu.addAction("Apagar", self._delete)
        menu.exec(self.list.viewport().mapToGlobal(pos))
