"""The Requirements (IDS) panel (Phase 4, step 2): the model checked against an IDS file —
each requirement met or not, and under each one not met the elements that fail it, with why.
A click on an element selects and frames it; after fixing, "Check again". It also shows the
certification checks (0.70), and saves either as a report page."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import ids_reason, t
from . import theme

GUID = QtCore.Qt.ItemDataRole.UserRole


def result_text(req):
    """What the panel says of a requirement's result."""
    if req.result:
        return req.result
    if req.status is None:
        return t("ids.other_version")
    if req.usage == "prohibited":
        return t("ids.prohibited", n=req.applicable) if req.applicable else t("ids.met", n=0)
    if not req.applicable:
        return t("ids.missing") if req.usage == "required" else t("ids.not_applicable")
    failing = len({guid for guid, _label, _reason in req.failures})
    return t("ids.failed", f=failing, n=req.applicable) if req.failures else t("ids.met", n=req.applicable)


class IdsPanel(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__(t("ids.title"), parent)
        self.setObjectName("ids")
        self.on_open = None          # ()
        self.on_again = None         # ()
        self.on_select = None        # ([GlobalId])
        self.on_save = None          # () — the report as a page (0.70)
        self.last = None             # (title, [Requirement]) shown
        body = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(body)
        row = QtWidgets.QHBoxLayout()
        self.open_button = QtWidgets.QPushButton(t("ids.open"))
        self.open_button.clicked.connect(lambda: self.on_open and self.on_open())
        self.again = QtWidgets.QPushButton(t("ids.again"))
        self.again.setEnabled(False)
        self.again.clicked.connect(lambda: self.on_again and self.on_again())
        self.save_button = QtWidgets.QPushButton(t("ids.save_report"))
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(lambda: self.on_save and self.on_save())
        self.summary = QtWidgets.QLabel(t("ids.none"))
        self.summary.setWordWrap(True)
        row.addWidget(self.open_button)
        row.addWidget(self.again)
        row.addWidget(self.save_button)
        row.addWidget(self.summary, 1)
        layout.addLayout(row)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels([t("ids.col.requirement"), t("ids.col.result")])
        self.tree.setToolTip(t("ids.hint"))
        self.tree.itemClicked.connect(self._clicked)
        layout.addWidget(self.tree, 1)
        self.setWidget(body)

    def show_results(self, title, requirements, panel_title=None):
        """An IDS's requirements, or the certification checks (0.70: `panel_title` names the panel then)."""
        self.setWindowTitle(panel_title or t("ids.title"))
        self.last = (title, requirements)
        self.again.setEnabled(True)
        self.save_button.setEnabled(True)
        ok = sum(1 for r in requirements if r.status)
        self.summary.setText(t("ids.summary", title=title, ok=ok, n=len(requirements)))
        self.tree.clear()
        for req in requirements:
            item = QtWidgets.QTreeWidgetItem([("✓  " if req.status else "✗  ") + req.name, result_text(req)])
            colour = theme.colour("good" if req.status else ("neutral" if req.status is None else "bad"))
            item.setForeground(0, QtGui.QBrush(colour))
            item.setToolTip(0, req.description or req.name)
            self.tree.addTopLevelItem(item)
            for guid, label, reason in req.failures:
                child = QtWidgets.QTreeWidgetItem([label, ids_reason(reason)])
                child.setData(0, GUID, guid)
                child.setToolTip(1, ids_reason(reason))
                item.addChild(child)
            item.setExpanded(bool(req.failures) and len(req.failures) <= 20)
        self.tree.resizeColumnToContents(0)

    def _clicked(self, item, _column):
        guid = item.data(0, GUID)
        if guid and self.on_select is not None:
            self.on_select([guid])

    def text(self):
        """The results as lines (used by tests)."""
        lines = []
        for k in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(k)
            lines.append("{} | {}".format(item.text(0), item.text(1)))
            for j in range(item.childCount()):
                lines.append("    {} | {}".format(item.child(j).text(0), item.child(j).text(1)))
        return "\n".join(lines)


def dock(parent):
    """At the bottom (like the Schedules), hidden until an IDS is opened."""
    panel = IdsPanel(parent)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, panel)
    panel.hide()
    return panel
