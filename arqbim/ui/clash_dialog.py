"""Detetar conflitos (0.149–0.150, Phase 6, step 6): which disciplines against which (the installations against the
structure, against each other, against the walls), on the active storey or all; «Procurar» lists the clashes with
their status (new, still there, approved; the ones gone are counted as resolved); a double-click (or «Ver») selects
the two elements and frames them; «Aprovar» accepts one (a sleeve through a wall that is meant); «Criar nota BCF»
makes a coordination note of it; «Relatório…» writes the list as an HTML page."""

from PySide6 import QtCore, QtWidgets

from ..i18n import t
from ..model import clashes as clashes_model

KEY = QtCore.Qt.ItemDataRole.UserRole


class ClashDialog(QtWidgets.QDialog):
    def __init__(self, parent, doc):
        super().__init__(parent)
        self.setWindowTitle(t("clash.title"))
        self.doc = doc
        self.on_show = None             # (GlobalIds) -> None: select and frame them
        self.on_note = None             # (Clash) -> None: a BCF note of it
        self.on_report = None           # (clashes) -> None: the HTML page
        self.found = []
        layout = QtWidgets.QVBoxLayout(self)
        row = QtWidgets.QHBoxLayout()
        self.pairs = {}
        for pair in clashes_model.PAIRS:
            box = QtWidgets.QCheckBox(clashes_model.pair_text(pair))
            box.setChecked(pair in clashes_model.DEFAULT_PAIRS)
            self.pairs[pair] = box
            row.addWidget(box)
        layout.addLayout(row)
        row = QtWidgets.QHBoxLayout()
        self.storey_only = QtWidgets.QCheckBox(t("clash.storey_only"))
        self.storey_only.setChecked(True)
        self.search_button = QtWidgets.QPushButton(t("clash.search"))
        self.search_button.clicked.connect(self.search)
        row.addWidget(self.storey_only)
        row.addStretch(1)
        row.addWidget(self.search_button)
        layout.addLayout(row)
        self.summary = QtWidgets.QLabel(t("clash.hint"))
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels([t(k) for k in ("clash.col.n", "clash.col.a", "clash.col.b", "clash.col.pair",
                                                  "clash.col.status")])
        self.tree.setRootIsDecorated(False)
        self.tree.itemDoubleClicked.connect(lambda item, _c: self._show(item))
        layout.addWidget(self.tree, 1)
        row = QtWidgets.QHBoxLayout()
        self.show_button = QtWidgets.QPushButton(t("clash.show"))
        self.approve_button = QtWidgets.QPushButton(t("clash.approve"))
        self.note_button = QtWidgets.QPushButton(t("clash.note"))
        self.report_button = QtWidgets.QPushButton(t("clash.report"))
        close = QtWidgets.QPushButton(t("elprop.close"))
        self.show_button.clicked.connect(lambda: self._show(self.tree.currentItem()))
        self.approve_button.clicked.connect(self._approve)
        self.note_button.clicked.connect(self._note)
        self.report_button.clicked.connect(lambda: self.on_report and self.on_report(self.found))
        close.clicked.connect(self.accept)
        for b in (self.show_button, self.approve_button, self.note_button, self.report_button):
            row.addWidget(b)
        row.addStretch(1)
        row.addWidget(close)
        layout.addLayout(row)
        self.resize(820, 460)

    def search(self):
        pairs = [p for p, box in self.pairs.items() if box.isChecked()]
        storey = self.doc.active_storey if self.storey_only.isChecked() else None
        self.found = clashes_model.find(self.doc, pairs, storey)
        after = clashes_model.updated_status(self.doc.clash_status, self.found)
        resolved = sum(1 for k, v in after.items() if v == "resolved" and self.doc.clash_status.get(k) != "resolved")
        if after != self.doc.clash_status:
            self.doc.execute(clashes_model.SetClashStatus(after, t("clash.cmd_search")))
        self._fill()
        text = t("clash.count", n=len(self.found))
        if resolved:
            text += " · " + t("clash.resolved_since", n=resolved)
        self.summary.setText(text)
        return self.found

    def _fill(self):
        self.tree.clear()
        for k, c in enumerate(self.found, 1):
            a, b = self.doc.get(c.a), self.doc.get(c.b)
            status = self.doc.clash_status.get(c.key, "new")
            item = QtWidgets.QTreeWidgetItem([str(k), a.name if a else c.a, b.name if b else c.b,
                                              clashes_model.pair_text(c.pair), t("clashstatus." + status)])
            item.setData(0, KEY, k - 1)
            self.tree.addTopLevelItem(item)
        for col in range(5):
            self.tree.resizeColumnToContents(col)

    def _clash(self, item):
        if item is None:
            return None
        k = item.data(0, KEY)
        return self.found[k] if k is not None and 0 <= k < len(self.found) else None

    def _show(self, item):
        c = self._clash(item)
        if c is not None and self.on_show is not None:
            self.on_show([c.a, c.b])

    def _approve(self):
        c = self._clash(self.tree.currentItem())
        if c is None:
            return
        after = dict(self.doc.clash_status)
        after[c.key] = "approved"
        self.doc.execute(clashes_model.SetClashStatus(after, t("clash.cmd_approve")))
        self._fill()

    def _note(self):
        c = self._clash(self.tree.currentItem())
        if c is not None and self.on_note is not None:
            self.on_note(c)
