"""(0.477, the owner: «A aba de tabelas também deve ser gerenciada pelo painel lateral… O painel lateral terá a árvore
de todas as tabelas criadas») The side panel of the «Quantidades» module, as Revit's Project Browser «Tabelas /
Quantidades»: the tree of every table — the project's own ones first, then the program's by what they list (the
model's quantities, rooms and finishes, doors and windows, installations, notes), each with how many lines it has —;
a click opens it in its tab over the canvas (ui/schedules.SchedulesPanel), the right button and the buttons under it:
Nova tabela…, Propriedades…, Duplicar, Apagar, Exportar…."""

from PySide6 import QtCore, QtWidgets

from ..i18n import t
from ..model import schedules
from . import theme

REF = QtCore.Qt.ItemDataRole.UserRole
OWN = "own"
# the program's tables, by what they list (each its group's name in i18n «tables.group.<key>»)
GROUPS = (("quantities", ("walls", "slabs", "roofs", "columns", "carpentry", "tiles", "other")),
          ("rooms", ("rooms", "finishes")),
          ("openings", ("doors", "windows")),
          ("services", ("circuits", "electrical")),
          ("notes", ("keynotes",)))


class TablesPanel(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__(t("tables.title"), parent)
        self.setObjectName("tables")
        self.on_open = None              # (ref): a table opened in its tab
        self.on_new = None               # (category key or None): Nova tabela…
        self.on_properties = None        # (ref)
        self.on_duplicate = None         # (ref)
        self.on_delete = None            # (ref) — the project's own
        self.on_export = None            # (ref)
        self.on_put = None               # (ref): Pôr na folha (a new one)
        self.doc = None
        page = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(page)
        column.setContentsMargins(4, 4, 4, 4)
        self.hint = QtWidgets.QLabel(t("tables.hint"))
        self.hint.setWordWrap(True)
        column.addWidget(self.hint)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText(t("tables.search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _text: self._filter())
        column.addWidget(self.search)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setMinimumWidth(140)
        self.tree.itemClicked.connect(lambda item, _c: self._open(item))
        self.tree.itemActivated.connect(lambda item, _c: self._open(item))
        self.tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._menu)
        column.addWidget(self.tree, 1)
        self.new_button = QtWidgets.QPushButton(t("tables.new"))
        self.new_button.setToolTip(t("tables.new_tip"))
        self.new_button.clicked.connect(lambda: self._call(self.on_new, self._category()))
        self.props_button = QtWidgets.QPushButton(t("sched.properties"))
        self.props_button.clicked.connect(lambda: self._call(self.on_properties, self.current()))
        self.dup_button = QtWidgets.QPushButton(t("tables.duplicate"))
        self.dup_button.clicked.connect(lambda: self._call(self.on_duplicate, self.current()))
        self.delete_button = QtWidgets.QPushButton(t("sched.delete"))
        self.delete_button.clicked.connect(lambda: self._call(self.on_delete, self.current()))
        self.export_button = QtWidgets.QPushButton(t("sched.export_short"))
        self.export_button.setToolTip(t("sched.export_tip"))
        self.export_button.clicked.connect(lambda: self._call(self.on_export, self.current()))
        grid = QtWidgets.QGridLayout()
        for k, b in enumerate((self.new_button, self.props_button, self.dup_button, self.delete_button,
                               self.export_button)):
            b.setMinimumWidth(40)
            b.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
            grid.addWidget(b, k // 2, k % 2)
        column.addLayout(grid)
        self.setWidget(page)
        self.tree.currentItemChanged.connect(lambda _a, _b: self._buttons())
        self.restyle()
        self._buttons()

    @staticmethod
    def _call(fn, *args):
        if fn is not None and all(a is not None for a in args):
            fn(*args)

    def restyle(self):
        self.hint.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])

    # ------------------------------------------------------------ the tree

    def show_document(self, doc, shown=None):
        """Every table of the document, with how many lines each has; `shown`: the ref of the table in view."""
        self.doc = doc
        keep = shown or self.current()
        counts = schedules.counts(doc)
        defs = list(getattr(doc, "schedule_defs", ()))
        self.tree.blockSignals(True)
        self.tree.clear()
        mine = QtWidgets.QTreeWidgetItem([t("tables.group.own") + " ({})".format(len(defs))])
        mine.setData(0, REF, None)
        mine.setFlags(mine.flags() & ~QtCore.Qt.ItemFlag.ItemIsSelectable)
        self.tree.addTopLevelItem(mine)
        current = None
        for d in sorted(defs, key=lambda d: d.name.lower()):
            leaf = QtWidgets.QTreeWidgetItem([d.name])
            leaf.setData(0, REF, "def:" + d.uid)
            leaf.setToolTip(0, t("tables.own_tip", cat=t("sched.cat." + d.category)))
            mine.addChild(leaf)
            current = leaf if keep == "def:" + d.uid else current
        mine.setExpanded(True)
        for group, keys in GROUPS:
            top = QtWidgets.QTreeWidgetItem([t("tables.group." + group)])
            top.setData(0, REF, None)
            top.setFlags(top.flags() & ~QtCore.Qt.ItemFlag.ItemIsSelectable)
            self.tree.addTopLevelItem(top)
            for key in keys:
                leaf = QtWidgets.QTreeWidgetItem(["{} ({})".format(t("sched.cat." + key), counts.get(key, 0))])
                leaf.setData(0, REF, key)
                top.addChild(leaf)
                current = leaf if keep == key else current
            top.setExpanded(True)
        if current is not None:
            self.tree.setCurrentItem(current)
        self.tree.blockSignals(False)
        self._filter()
        self._buttons()

    def current(self):
        item = self.tree.currentItem()
        return item.data(0, REF) if item is not None else None

    def item_for(self, ref):
        for k in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(k)
            for j in range(top.childCount()):
                if top.child(j).data(0, REF) == ref:
                    return top.child(j)
        return None

    def mark(self, ref):
        """(The table in view: its line chosen.)"""
        item = self.item_for(ref)
        if item is not None and item is not self.tree.currentItem():
            self.tree.blockSignals(True)
            self.tree.setCurrentItem(item)
            self.tree.blockSignals(False)
            self._buttons()

    def text(self):
        """(tests) The tree as lines: a group, then its tables indented."""
        lines = []
        for k in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(k)
            lines.append(top.text(0))
            lines += ["  " + top.child(j).text(0) for j in range(top.childCount())]
        return "\n".join(lines)

    def _category(self):
        """The category a new table starts from: the one chosen (a project's own table's), else walls."""
        ref = self.current()
        if ref and ref.startswith("def:"):
            own = next((d for d in getattr(self.doc, "schedule_defs", ()) if "def:" + d.uid == ref), None)
            return own.category if own is not None else "walls"
        return ref if ref in schedules.CATEGORIES else "walls"

    def _filter(self):
        words = self.search.text().strip().lower()
        for k in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(k)
            seen = 0
            for j in range(top.childCount()):
                hide = bool(words) and words not in top.child(j).text(0).lower()
                top.child(j).setHidden(hide)
                seen += not hide
            top.setHidden(bool(words) and not seen)

    def _buttons(self):
        ref = self.current()
        own = bool(ref) and ref.startswith("def:")
        for b in (self.props_button, self.dup_button, self.export_button):
            b.setEnabled(bool(ref))
        self.delete_button.setEnabled(own)

    def _open(self, item):
        ref = item.data(0, REF) if item is not None else None
        if ref and self.on_open is not None:
            self.on_open(ref)

    def _menu(self, pos):
        item = self.tree.itemAt(pos)
        ref = item.data(0, REF) if item is not None else None
        menu = QtWidgets.QMenu(self)
        if ref:
            menu.addAction(t("tables.open"), lambda: self._call(self.on_open, ref))
            menu.addAction(t("sched.properties"), lambda: self._call(self.on_properties, ref))
            menu.addAction(t("tables.duplicate"), lambda: self._call(self.on_duplicate, ref))
            menu.addAction(t("tables.put"), lambda: self._call(self.on_put, ref))
            menu.addAction(t("sched.export_short"), lambda: self._call(self.on_export, ref))
            if ref.startswith("def:"):
                menu.addSeparator()
                menu.addAction(t("sched.delete"), lambda: self._call(self.on_delete, ref))
            menu.addSeparator()
        menu.addAction(t("tables.new"), lambda: self._call(self.on_new, self._category()))
        from . import menus
        menu.exec(menus.menu_point(menu, self.tree.viewport().mapToGlobal(pos)))
