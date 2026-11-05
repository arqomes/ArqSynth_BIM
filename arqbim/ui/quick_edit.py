"""(0.354) TAB, the quick edit: with elements chosen (Select), a small panel over the view beside them with what is most
often changed — their type on top, and the Properties panel's «Parâmetros» rows: a wall's length, its base and top
(storey and offset, height), its profile; a door's or window's sizes and swing; a slab's sizes and outline; a roof's…
—, made by a Properties panel of its own (PropertiesPanel(quick=True)), so every element the panel knows has its quick
edit, its edits going where the panel's go (one undo step each). The owner, 2026-11-02: «Vamos adotar a tecla TAB
para edição rápida dos elementos». TAB again (in the view), Esc, ×, another selection, another tool or a click in the
view close it; an edit made shows it again, changed. In the drawing tools TAB keeps its own use (a wall's reference
line, a component turned 90°): nothing is chosen there."""

from PySide6 import QtCore, QtWidgets

from ..i18n import t
from . import theme
from .properties import PropertiesPanel

WIDTH = 350                 # px
MOST_HEIGHT = 440           # px: taller than this, its rows scroll
ROW_PX = 27                 # px: a row of the panel with its field (a list, a box to type in)
GAP = 18                    # px between the elements' box on screen and the panel
MARGIN = 8                  # px kept from the view's edges


class QuickEdit(QtWidgets.QFrame):
    """The panel: a child of the views' area (as the notice balloon), shown by show_for(), hidden by close_panel()."""

    def __init__(self, parent, on_edit, on_edit_many):
        super().__init__(parent)
        self.setObjectName("quick_edit")
        self.panel = PropertiesPanel(self, quick=True)
        self.panel.hide()
        self.panel.on_edit = on_edit
        self.panel.on_edit_many = on_edit_many
        self.ids = []                               # what it shows
        column = QtWidgets.QVBoxLayout(self)
        column.setContentsMargins(6, 4, 6, 6)
        column.setSpacing(2)
        bar = QtWidgets.QHBoxLayout()
        self.title = QtWidgets.QLabel(t("quick.title"))
        self.title.setStyleSheet("QLabel { font-weight: 600; }")
        self.close_button = QtWidgets.QToolButton()
        self.close_button.setText("×")
        self.close_button.setAutoRaise(True)
        self.close_button.setToolTip(t("quick.close"))
        self.close_button.clicked.connect(self.close_panel)
        bar.addWidget(self.title, 1)
        bar.addWidget(self.close_button)
        column.addLayout(bar)
        column.addWidget(self.panel.content, 1)
        self.restyle()
        self.hide()

    def restyle(self):
        """In the theme's colours: a panel with a border, over the view."""
        c = theme.C
        self.setStyleSheet("QFrame#quick_edit { background: %s; border: 1px solid %s; border-radius: 6px; }"
                           % (c["panel"], c["line"]))
        self.panel.restyle()

    def show_for(self, doc, ids, near, view=None):
        """Shown for the elements `ids`, beside `near` (their box on the view, a QRect in the parent's coordinates):
        on its right, else its left, else under it, else over it — the first where it fits whole in the view (`view`:
        the drawing's rect, under the views' tabs; else the parent's), clear of them —, else where it covers least of
        them."""
        self.ids = list(ids)
        self.panel.show_selection(doc, self.ids)
        self.panel.tree.expandAll()
        rows = ROW_PX * max(1, self._row_count()) + 8 if self.panel.tree.topLevelItemCount() else 60
        height = min(MOST_HEIGHT, self.panel.header.sizeHint().height() + rows + 44)
        self.resize(WIDTH, height)
        area = (view or self.parentWidget().rect()).adjusted(MARGIN, MARGIN, -MARGIN, -MARGIN)
        middle = near.center()
        places = [QtCore.QPoint(near.right() + GAP, middle.y() - height // 2),          # (right, left, under, over)
                  QtCore.QPoint(near.left() - GAP - WIDTH, middle.y() - height // 2),
                  QtCore.QPoint(middle.x() - WIDTH // 2, near.bottom() + GAP),
                  QtCore.QPoint(middle.x() - WIDTH // 2, near.top() - GAP - height)]

        def inside(p):                                  # (pushed into the view)
            return QtCore.QPoint(max(area.left(), min(p.x(), area.right() - WIDTH)),
                                 max(area.top(), min(p.y(), area.bottom() - height)))

        def covered(p):
            box = QtCore.QRect(p, QtCore.QSize(WIDTH, height)).intersected(near)
            return box.width() * box.height() if not box.isEmpty() else 0

        fits = [p for p in places if area.contains(QtCore.QRect(p, QtCore.QSize(WIDTH, height)))]
        best = fits[0] if fits else min((inside(p) for p in places), key=covered)
        self.move(best)
        self.show()
        self.raise_()

    def _row_count(self):
        count = 0
        for k in range(self.panel.tree.topLevelItemCount()):
            item = self.panel.tree.topLevelItem(k)
            count += 1 + item.childCount()
        return count

    def refresh(self, doc, ids):
        """After a change: the same elements chosen — shown again, as they are now, where it is; others — closed."""
        if not self.isVisible():
            return
        alive = [i for i in self.ids if doc.get(i) is not None]
        if not alive or set(alive) != set(ids):
            self.close_panel()
            return
        self.panel.show_selection(doc, alive)
        self.panel.tree.expandAll()

    def close_panel(self):
        self.hide()
        self.ids = []

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Escape:   # (TAB inside it goes from one field to the next, as in a form)
            self.close_panel()
            event.accept()
            return
        super().keyPressEvent(event)
