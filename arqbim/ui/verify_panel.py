"""(0.418) The Verification panel: everything the Verifier found — by dwelling (and the building's common parts) or by
law —, filtered (failures and warnings, only failures, exceptions, what could not be measured, everything). A click
chooses what it is about and frames it; «Porquê» says the rule; «Exceção…» accepts a failure with the reason written
(it stays in the project and goes into the verification sheet: «vontade expressa do dono de obra», CTE art. 27.º
n.º 7…), and it is no longer counted.

The other checks the program already makes are here too, one click away — clashes, the IFC for certification, an
IDS, the electrical installation, the structure (EC2 / EC6): one place to look («tudo num só lugar»)."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..verify import check as check_mod
from ..verify import project
from ..verify import reader
from ..verify import rules as rules_mod
from . import theme

KEY = QtCore.Qt.ItemDataRole.UserRole
FILTERS = ("problems", "failures", "excepted", "unknown", "all")
GROUPS = ("dwelling", "law")


class VerifyPanel(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__(t("verify.panel.title"), parent)
        self.setObjectName("verify_panel")
        self.on_goto = None             # fn(finding)
        self.on_why = None              # fn(finding)
        self.on_except = None           # fn(finding, why or None)
        self.on_settings = None         # fn()
        self.on_other = None            # fn(name): another of the program's checks
        self.on_sheet = None            # fn(): (0.425) the verification sheet
        self.result, self.doc = None, None
        self._findings = {}
        body = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(body)
        row = QtWidgets.QHBoxLayout()
        self.filter = QtWidgets.QComboBox()
        for key in FILTERS:
            self.filter.addItem(t("verify.panel.filter." + key), key)
        self.filter.currentIndexChanged.connect(lambda _k: self.refresh())
        self.group = QtWidgets.QComboBox()
        for key in GROUPS:
            self.group.addItem(t("verify.panel.group." + key), key)
        self.group.currentIndexChanged.connect(lambda _k: self.refresh())
        self.why_button = QtWidgets.QPushButton(t("verify.strip.why"))
        self.why_button.clicked.connect(lambda: self._act("why"))
        self.except_button = QtWidgets.QPushButton(t("verify.panel.except"))
        self.except_button.clicked.connect(lambda: self._act("except"))
        self.settings_button = QtWidgets.QPushButton(t("verify.menu.settings"))
        self.settings_button.clicked.connect(lambda: self.on_settings and self.on_settings())
        self.other_button = QtWidgets.QPushButton(t("verify.panel.other"))
        menu = QtWidgets.QMenu(self.other_button)
        for name in ("clashes", "check_ifc", "check_ids", "electrical_check", "verify_ec2"):
            menu.addAction(t("verify.panel.other." + name), lambda n=name: self.on_other and self.on_other(n))
        self.other_button.setMenu(menu)
        self.sheet_button = QtWidgets.QPushButton(t("verify.panel.sheet"))          # (0.425)
        self.sheet_button.setToolTip(t("tip.verify_sheet"))
        self.sheet_button.clicked.connect(lambda: self.on_sheet and self.on_sheet())
        for w in (self.filter, self.group, self.why_button, self.except_button, self.settings_button,
                  self.sheet_button, self.other_button):
            row.addWidget(w)
        row.addStretch(1)
        layout.addLayout(row)
        self.summary = QtWidgets.QLabel("")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels([t("verify.panel.col.what"), t("verify.panel.col.result"),
                                   t("verify.panel.col.article")])
        self.tree.itemClicked.connect(self._clicked)
        self.tree.itemDoubleClicked.connect(self._clicked)
        self.tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._menu)
        self.tree.currentItemChanged.connect(lambda *_a: self._buttons())
        layout.addWidget(self.tree, 1)
        self.setWidget(body)
        self._buttons()

    # ------------------------------------------------------------ shown
    def show_result(self, doc, result):
        self.doc, self.result = doc, result
        if self.isVisible():
            self.refresh()

    def _wanted(self, f):
        which = self.filter.currentData()
        if which == "problems":
            return f.status == "fail"                       # (excepted ones too, marked: so they can be undone)
        if which == "failures":
            return f.failed and f.rule.severity == "error"
        if which == "excepted":
            return bool(f.excepted)
        if which == "unknown":
            return f.status == "unknown"
        return True

    def refresh(self):
        self.tree.clear()
        self._findings = {}
        r = self.result
        if r is None:
            self.summary.setText(t("verify.panel.none"))
            return
        c = r.counts()
        laws = ", ".join(p.short for p, own in r.packs if own and project.is_law(p) and (     # (0.423: the town
            p.id != project.PLAN_PACK or project.plan_values(r.settings))) or "—"           # plan with values)
        self.summary.setText(t("verify.panel.summary", laws=laws, e=c["error"], w=c["warning"], x=c["excepted"],
                               ok=c["ok"], u=c["unknown"]))
        facts = reader.read(self.doc) if self.doc is not None else None
        heads = {}
        by_law = self.group.currentData() == "law"
        for f in sorted(r.findings, key=lambda f: (f.status != "fail", f.rule.severity != "error", f.subject.name)):
            if not self._wanted(f):
                continue
            if by_law:
                pack = rules_mod.find(f.rule.pack)
                head = "{} — {}".format(pack.short, pack.title) if pack else f.rule.pack
            else:
                head = (r.dwelling_of(f, facts) if facts is not None else None) or t("verify.panel.building")
            parent = heads.get(head)
            if parent is None:
                parent = QtWidgets.QTreeWidgetItem([head, "", ""])
                font = parent.font(0)
                font.setBold(True)
                parent.setFont(0, font)
                self.tree.addTopLevelItem(parent)
                heads[head] = parent
            item = QtWidgets.QTreeWidgetItem([self._what(f), self._result(f), f.rule.article])
            item.setData(0, KEY, f.key)
            item.setToolTip(0, check_mod.message(f))
            item.setToolTip(2, "{}\n\n{}".format(f.rule.title, f.rule.text))
            colour = theme.C["neutral"] if f.excepted or f.status == "unknown" else (
                theme.C["ok"] if f.status == "ok" else theme.C["fail"] if f.rule.severity == "error"
                else theme.C["attention"])
            item.setForeground(1, QtGui.QBrush(QtGui.QColor(colour)))
            parent.addChild(item)
            self._findings[f.key] = f
        self.tree.expandAll()
        for col in (0, 1):
            self.tree.resizeColumnToContents(col)
        self._buttons()

    @staticmethod
    def _what(f):
        return "{} — {}".format(f.subject.name, f.rule.title)

    @staticmethod
    def _result(f):
        rule = f.rule
        side = t("verify.side." + ("min" if any(k.startswith("min") for k in rule.limit) else "max"))
        values = dict(value=check_mod.number(f.value, rule.unit), side=side, limit=check_mod.number(f.limit, rule.unit))
        if f.excepted:
            return t("verify.panel.excepted", why=f.excepted.get("why", ""), **values)
        return t({"ok": "verify.props.ok", "fail": "verify.props.fail"}.get(f.status, "verify.props.unknown"),
                 **values)

    # ------------------------------------------------------------ acting
    def current(self):
        item = self.tree.currentItem()
        return self._findings.get(item.data(0, KEY)) if item is not None else None

    def _buttons(self):
        f = self.current()
        self.why_button.setEnabled(f is not None)
        self.except_button.setEnabled(f is not None and f.status == "fail")
        self.except_button.setText(t("verify.panel.unexcept") if f is not None and f.excepted
                                   else t("verify.panel.except"))

    def _clicked(self, item, _column=0):
        f = self._findings.get(item.data(0, KEY))
        if f is not None and self.on_goto is not None:
            self.on_goto(f)
        self._buttons()

    def _act(self, what, finding=None):
        f = finding or self.current()
        if f is None:
            return
        if what == "why" and self.on_why is not None:
            self.on_why(f)
        elif what == "except" and self.on_except is not None:
            if f.excepted:
                self.on_except(f, None)
                return
            why, ok = QtWidgets.QInputDialog.getMultiLineText(
                self, t("verify.panel.except_title", rule=f.rule.title), t("verify.panel.except_ask"),
                t("verify.panel.except_hint"))
            if ok and why.strip():
                self.on_except(f, why.strip())

    def _menu(self, point):
        item = self.tree.itemAt(point)
        f = self._findings.get(item.data(0, KEY)) if item is not None else None
        if f is None:
            return
        menu = QtWidgets.QMenu(self)
        menu.addAction(t("verify.strip.goto"), lambda: self.on_goto and self.on_goto(f))
        menu.addAction(t("verify.strip.why"), lambda: self._act("why", f))
        if f.status == "fail":
            menu.addAction(t("verify.panel.unexcept") if f.excepted else t("verify.panel.except"),
                           lambda: self._act("except", f))
        menu.exec(self.tree.viewport().mapToGlobal(point))

    def text(self):
        """The panel's lines (for the tests)."""
        lines = [self.summary.text()]
        for k in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(k)
            lines.append(top.text(0))
            for j in range(top.childCount()):
                child = top.child(j)
                lines.append("    {} | {} | {}".format(child.text(0), child.text(1), child.text(2)))
        return "\n".join(lines)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()


def dock(parent, beside=None):
    """At the bottom, beside the IDS panel; hidden until asked for."""
    panel = VerifyPanel(parent)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, panel)
    if beside is not None:
        parent.tabifyDockWidget(beside, panel)
    panel.hide()
    return panel
