"""The Notes panel (Phase 4, step 4): coordination notes (BCF topics) — each with its title,
state, author, date, the picture of the view it was made in, its description and comments.
"New note" keeps the view and the elements selected; "Go to the view" brings them back.
Notes are saved with the project (<name>.bcfzip) and exchanged with Revit, ArchiCAD,
Solibri… (Import / Export BCF)."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from . import theme

GUID = QtCore.Qt.ItemDataRole.UserRole


class NotesPanel(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__(t("notes.title"), parent)
        self.setObjectName("notes")
        self.on_new = self.on_go = self.on_comment = self.on_toggle = self.on_delete = None
        self.on_import = self.on_export = None
        self._notes = []
        body = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(body)
        row = QtWidgets.QHBoxLayout()
        self.buttons = {}
        for key, slot in (("new", lambda: self._call(self.on_new)), ("go", lambda: self._with_note(self.on_go)),
                          ("toggle", lambda: self._with_note(self.on_toggle)),
                          ("delete", lambda: self._with_note(self.on_delete)),
                          ("import", lambda: self._call(self.on_import)), ("export", lambda: self._call(self.on_export))):
            button = QtWidgets.QPushButton(t("notes." + key))
            button.clicked.connect(slot)
            row.addWidget(button)
            self.buttons[key] = button
        row.addStretch(1)
        layout.addLayout(row)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels([t("notes.col.title"), t("notes.col.status"), t("notes.col.author"),
                                   t("notes.col.date"), t("notes.col.comments")])
        self.tree.setRootIsDecorated(False)
        self.tree.currentItemChanged.connect(lambda _a, _b: self._show_current())
        self.tree.itemDoubleClicked.connect(lambda _item, _col: self._with_note(self.on_go))
        self.picture = QtWidgets.QLabel()
        self.picture.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.picture.setMinimumSize(200, 120)
        self.details = QtWidgets.QTextBrowser()
        self.comment = QtWidgets.QLineEdit()
        self.comment.setPlaceholderText(t("notes.comment_hint"))
        self.comment.returnPressed.connect(self._commented)
        right = QtWidgets.QWidget()
        rlayout = QtWidgets.QVBoxLayout(right)
        rlayout.setContentsMargins(0, 0, 0, 0)
        rlayout.addWidget(self.picture)
        rlayout.addWidget(self.details, 1)
        rlayout.addWidget(self.comment)
        split = QtWidgets.QSplitter()
        split.addWidget(self.tree)
        split.addWidget(right)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        layout.addWidget(split, 1)
        hint = QtWidgets.QLabel(t("notes.hint"))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.setWidget(body)
        self._show_current()

    @staticmethod
    def _call(fn):
        if fn is not None:
            fn()

    def _with_note(self, fn):
        note = self.current()
        if fn is not None and note is not None:
            fn(note)

    def _commented(self):
        text = self.comment.text().strip()
        note = self.current()
        if text and note is not None and self.on_comment is not None:
            self.comment.clear()
            self.on_comment(note, text)

    def show_notes(self, notes):
        """List the notes (the one chosen stays chosen, by its guid)."""
        chosen = self.current()
        chosen = chosen.guid if chosen is not None else None
        self._notes = list(notes)
        self.tree.blockSignals(True)
        self.tree.clear()
        pick = None
        for note in self._notes:
            item = QtWidgets.QTreeWidgetItem([note.title, t("notes.closed") if note.closed else t("notes.open"),
                                              note.author, note.date[:10], str(len(note.comments))])
            item.setData(0, GUID, note.guid)
            if note.closed:
                item.setForeground(0, QtGui.QBrush(theme.colour("neutral")))
            self.tree.addTopLevelItem(item)
            if note.guid == chosen:
                pick = item
        self.tree.blockSignals(False)
        if pick is None and self.tree.topLevelItemCount():
            pick = self.tree.topLevelItem(self.tree.topLevelItemCount() - 1)
        if pick is not None:
            self.tree.setCurrentItem(pick)
        self.tree.resizeColumnToContents(0)
        self._show_current()

    def current(self):
        item = self.tree.currentItem()
        guid = item.data(0, GUID) if item is not None else None
        return next((n for n in self._notes if n.guid == guid), None)

    def _show_current(self):
        note = self.current()
        for key in ("go", "toggle", "delete"):
            self.buttons[key].setEnabled(note is not None)
        self.comment.setEnabled(note is not None)
        if note is None:
            self.picture.clear()
            self.details.setHtml("")
            return
        pixmap = QtGui.QPixmap()
        if note.snapshot and pixmap.loadFromData(note.snapshot):
            self.picture.setPixmap(pixmap.scaled(320, 200, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                                 QtCore.Qt.TransformationMode.SmoothTransformation))
        else:
            self.picture.setText(t("notes.no_picture"))
        html = "<b>{}</b><br>{}".format(_html(note.title), _html(note.description).replace("\n", "<br>"))
        for author, date, text in note.comments:
            html += "<p><i>{} — {}</i><br>{}</p>".format(_html(author), _html(date[:16].replace("T", " ")), _html(text))
        self.details.setHtml(html)

    def text(self):
        """The notes as lines (used by tests)."""
        return "\n".join(" | ".join(self.tree.topLevelItem(k).text(c) for c in range(5))
                         for k in range(self.tree.topLevelItemCount()))


def _html(text):
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def dock(parent, beside=None):
    """At the bottom, as a tab next to `beside` (the Schedules), hidden until asked for."""
    panel = NotesPanel(parent)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, panel)
    if beside is not None:
        parent.tabifyDockWidget(beside, panel)
    panel.hide()
    return panel
