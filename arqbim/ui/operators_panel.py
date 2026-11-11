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
        self.on_apply = None             # (slug, side)
        self.on_new = None               # (side)
        self.on_edit = None              # (slug, side)
        self.target = lambda: 0          # () -> how many walls are chosen in the model
        page = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(page)
        column.setContentsMargins(4, 4, 4, 4)
        self.hint = QtWidgets.QLabel("Escolha uma parede no modelo, um operador nesta lista, e «Aplicar».")
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
        self.list.currentItemChanged.connect(lambda _a, _b: self.refresh_target())
        self.list.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._menu)
        column.addWidget(self.list, 1)
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
        grid = QtWidgets.QGridLayout()
        self.apply_button.setDefault(True)
        grid.addWidget(self.apply_button, 0, 0, 1, 2)
        for k, b in enumerate((self.new_button, self.edit_button, self.dup_button, self.rename_button,
                               self.delete_button, self.import_button, self.export_button)):
            grid.addWidget(b, 1 + k // 2, k % 2)
        for b in (self.apply_button, self.new_button, self.edit_button, self.dup_button, self.rename_button,
                  self.delete_button, self.import_button, self.export_button):
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
        for label in (self.hint, self.folder_label):
            label.setStyleSheet(muted)
        self.target_label.setStyleSheet("font-weight: 600;")

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
        self.folder_label.setText("Guardados para todos os projetos em:\n" + operators.folder().replace("\\", "\\​")
                                  .replace("/", "/​"))
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
        self.target_label.setText("Nenhuma parede escolhida no modelo." if not n else
                                  "1 parede escolhida." if n == 1 else "{} paredes escolhidas.".format(n))
        one = self.current() is not None
        self.apply_button.setEnabled(one and n > 0)
        for b in (self.edit_button, self.dup_button, self.rename_button, self.delete_button, self.export_button):
            b.setEnabled(one)

    # ---- the buttons
    def _apply(self):
        if self.current() is None:
            return
        if not (self.target() if self.target else 0):
            QtWidgets.QMessageBox.information(self, "Operadores", "Escolha primeiro uma parede no modelo.")
            return
        if self.on_apply:
            self.on_apply(self.current(), self.chosen_side())

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
