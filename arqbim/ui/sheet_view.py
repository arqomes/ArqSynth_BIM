"""A sheet (Phase 3, step 8): a sheet of paper with its views, as it will print — shown in its
tab over the 3D view (0.56; before, a window of its own). Drag a view to move it (it stays
there); Delete takes it off the sheet; a view's scale is "automatic" (the largest at which all
the views laid out fit, the same for all) or chosen. Paper A3 … A0, landscape. Export PDF
writes it as on screen, with the model as it is now. (0.238) A label of a reinforcement drawing or a
structure plan dragged moves alone (the view's own property; a double click puts it back).

The drawings (hidden lines) take a moment for a big model: they are made once, kept by the
main window until the model changes, and remade here with "Update drawings".
"""

import copy

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..model import sheets as sheets_model
from . import pdf

PAPER_BG = QtGui.QColor("#7d7f83")
PICKED = QtGui.QColor("#1f74d1")


class SheetCanvas(QtWidgets.QWidget):
    """The sheet drawn to fit the widget."""

    def __init__(self, window):
        super().__init__(window)
        self.owner = window          # the SheetWindow (not QWidget.window())
        self.selected = None          # index of the view picked on the sheet
        self._drag = None             # (view index, mouse mm at the start, centre at the start)
        self._label = None            # (0.238) a label dragged: (view index, its annotation, key, mouse mm, its spot)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(640, 460)

    def fit(self):
        """(pixels per mm, x, y of the paper's corner) to show the whole sheet with a margin."""
        w, h = self.owner.sheet.size() if self.owner.sheet is not None else sheets_model.PAPERS["A3"]
        s = min((self.width() - 24) / w, (self.height() - 24) / h)
        return s, (self.width() - w * s) / 2, (self.height() - h * s) / 2

    def to_mm(self, pos):
        s, x0, y0 = self.fit()
        return (pos.x() - x0) / s, (pos.y() - y0) / s

    def paintEvent(self, _event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), PAPER_BG)
        sheet = self.owner.sheet
        if sheet is None:
            return
        s, x0, y0 = self.fit()
        w, h = sheet.size()
        painter.fillRect(QtCore.QRectF(x0 + 3, y0 + 3, w * s, h * s), QtGui.QColor(0, 0, 0, 60))   # shadow
        painter.fillRect(QtCore.QRectF(x0, y0, w * s, h * s), QtGui.QColor("white"))
        painter.translate(x0, y0)
        pdf.paint_sheet(painter, s, (w, h), self.owner.host.title_block(sheet), self.owner.placed,
                        template=sheet.template)
        frame = self.owner.frame_of(self.selected)
        if frame is not None:
            left, top, fw, fh = frame.rect()
            pen = QtGui.QPen(PICKED, 1.5, QtCore.Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawRect(QtCore.QRectF((left - 2) * s, (top - 2) * s, (fw + 4) * s, (fh + 4) * s))
        painter.end()

    def view_at(self, x, y):
        """The view whose frame is under (x, y) mm (the one drawn last if they overlap)."""
        for k in reversed(range(len(self.owner.frames))):
            frame = self.owner.frames[k]
            if frame is not None and frame.contains(x, y):
                return k
        return None

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.MouseButton.LeftButton:
            return
        x, y = self.to_mm(event.position())
        self.selected = self.view_at(x, y)
        frame = self.owner.frame_of(self.selected)
        self._drag = (self.selected, (x, y), frame.centre) if frame is not None else None
        hit = self.owner.label_at(x, y)                  # (0.238) on a label: the label is dragged, not the view
        if hit is not None:
            k, i, key = hit
            self.selected, self._drag = k, None
            self._label = (k, i, key, (x, y), np.array(self.owner._drawings[k].annotations[i][4], dtype=float))
        self.owner.picked(self.selected)
        self.update()

    def mouseDoubleClickEvent(self, event):
        """On the title block: fill it in. (0.238) On a label moved by hand: back to its place."""
        if event.button() != QtCore.Qt.MouseButton.LeftButton:
            return
        x, y = self.to_mm(event.position())
        hit = self.owner.label_at(x, y)
        if hit is not None:
            self._drag = self._label = None
            self.owner.move_label(hit[0], hit[2], None)
        elif self.on_title_block(x, y):
            self._drag = None
            self.owner.edit_title_block()

    def on_title_block(self, x, y):
        sheet = self.owner.sheet
        if sheet is None:
            return False
        left, top, w, h = sheets_model.title_box(sheet.size(), sheet.template)      # (its template's, 0.129)
        return left <= x <= left + w and top <= y <= top + h

    def mouseMoveEvent(self, event):
        if self._label is not None:                      # (0.238) the label follows the mouse
            k, i, _key, (x0, y0), spot = self._label
            x, y = self.to_mm(event.position())
            self.owner.drag_label(k, i, spot + self.owner.to_metres(k, x - x0, y - y0))
            return
        if self._drag is None:
            return
        k, (x0, y0), (cx, cy) = self._drag
        x, y = self.to_mm(event.position())
        self.owner.drag(k, (cx + x - x0, cy + y - y0))

    def mouseReleaseEvent(self, event):
        if self._label is not None and event.button() == QtCore.Qt.MouseButton.LeftButton:
            k, i, key, (x0, y0), spot = self._label
            self._label = None
            x, y = self.to_mm(event.position())
            if abs(x - x0) + abs(y - y0) > 0.5:
                self.owner.move_label(k, key, self.owner.to_metres(k, x - x0, y - y0), add=True)
            else:
                self.owner.refresh()                     # (a click is not a move: the drawing as it was)
            return
        if self._drag is None or event.button() != QtCore.Qt.MouseButton.LeftButton:
            return
        k, (x0, y0), (cx, cy) = self._drag
        self._drag = None
        x, y = self.to_mm(event.position())
        if abs(x - x0) + abs(y - y0) > 0.5:                      # (a click is not a move)
            self.owner.move_view(k, (cx + x - x0, cy + y - y0))

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key.Key_Delete, QtCore.Qt.Key.Key_Backspace) and self.selected is not None:
            self.owner.take_off(self.selected)
            return
        super().keyPressEvent(event)


class SheetWindow(QtWidgets.QWidget):
    """The sheet of the sheet tab shown (one page for all the sheet tabs: another tab, another sheet)."""

    def __init__(self, host, parent=None):
        super().__init__(parent)
        self.host = host              # the main window: document, drawings, PDF export
        self._uid = None              # the sheet shown (see sheet)
        self.frames = []              # sheets.Frame per view (None: nothing to draw)
        self.placed = []              # (drawing, frame, label) as painted
        self._made = {}               # drawing key -> Drawing shown (kept until "Update drawings")
        self._drawings = []           # per view of the sheet
        self._stale = False           # the model changed since they were made
        self._busy = self._later = False

        self.paper = QtWidgets.QComboBox()
        self.paper.addItems(list(sheets_model.PAPERS))
        self.paper.activated.connect(lambda _k: self._change(paper=self.paper.currentText()))
        self.template = QtWidgets.QComboBox()                   # (0.129) its title block's template
        for key in sheets_model.TEMPLATES:
            self.template.addItem(t("sheet.template." + key), key)
        self.template.activated.connect(lambda _k: self._change(template=self.template.currentData()))
        self.scale = QtWidgets.QComboBox()
        self.scale.addItem(t("sheet.scale_auto"), None)
        for n in sheets_model.SCALES:
            self.scale.addItem("1:{}".format(n), n)
        self.scale.activated.connect(self._scale_chosen)
        self.tidy = QtWidgets.QPushButton(t("sheet.tidy"))
        self.tidy.setToolTip(t("sheet.tidy_tip"))
        self.tidy.clicked.connect(self._tidy)
        self.refresh_button = QtWidgets.QPushButton(t("sheet.refresh"))
        self.refresh_button.clicked.connect(lambda: self.refresh(again=True))
        self.export = QtWidgets.QPushButton(t("sheet.export"))
        self.export.clicked.connect(lambda: self.host.export_sheets([self.sheet]))
        self.title_block = QtWidgets.QPushButton(t("sheet.title_block"))
        self.title_block.setToolTip(t("sheet.title_block_tip"))
        self.title_block.clicked.connect(self.edit_title_block)
        bar = QtWidgets.QHBoxLayout()
        bar.addWidget(QtWidgets.QLabel(t("sheet.paper")))
        bar.addWidget(self.paper)
        bar.addWidget(QtWidgets.QLabel(t("sheet.template")))
        bar.addWidget(self.template)
        bar.addWidget(self.title_block)
        bar.addSpacing(16)
        bar.addWidget(QtWidgets.QLabel(t("sheet.view_scale")))
        bar.addWidget(self.scale)
        bar.addWidget(self.tidy)
        bar.addStretch(1)
        bar.addWidget(self.refresh_button)
        bar.addWidget(self.export)
        self.canvas = SheetCanvas(self)
        self.hint = QtWidgets.QLabel(t("sheet.hint"))
        self.hint.setWordWrap(True)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(bar)
        layout.addWidget(self.canvas, 1)
        layout.addWidget(self.hint)

    # ------------------------------------------------------------ content

    @property
    def sheet(self):
        """The sheet shown, found by its uid (undo / redo put back copies of the sheets)."""
        return next((s for s in self.host.doc.sheets if s.uid == self._uid), None) if self._uid else None

    def show_sheet(self, sheet):
        """Show this sheet (its tab was chosen)."""
        if sheet.uid != self._uid:
            self.canvas.selected = None
        self._uid = sheet.uid
        if self._stale:
            self._made, self._stale = {}, False
            self._mark_up_to_date()
        self.refresh()
        self.canvas.setFocus()

    def refresh(self, again=False):
        """Lay the sheet out again with the drawings of its views (made if missing, or all
        again — the model as it is now: again=True)."""
        if self._busy:                # (making drawings: the window keeps going meanwhile)
            self._later = True
            return
        sheet = self.sheet
        if sheet is None:             # (gone: its tab closes)
            return
        self.paper.setCurrentText(sheet.paper)
        self.template.setCurrentIndex(max(0, self.template.findData(sheet.template)))
        keys = [self.host.drawing_key(v.kind, v.ref) for v in sheet.views]
        need = [v for key, v in zip(keys, sheet.views) if again or key not in self._made]
        if need:
            self._busy = True
            try:
                self._made.update(self.host.make_drawings(need, fresh=again))
            finally:
                self._busy = False
            if self._later:
                self._later = False
                QtCore.QTimer.singleShot(0, self.refresh)
        if again:
            self._stale = False
            self._mark_up_to_date()
        self._drawings = [self._made.get(key) for key in keys]
        self.frames = sheets_model.layout(sheet, [sheets_model.extent(d) for d in self._drawings],
                                          [self.host.doc.view_settings((v.kind, v.ref)).scale for v in sheet.views],
                                          len(self.host.doc.title_block.get(sheets_model.EXTRA_KEY) or ()))
        self._relabel()
        self.picked(self.canvas.selected if self.canvas.selected is not None
                    and self.canvas.selected < len(self.frames) else None)
        self.canvas.update()

    def _relabel(self):
        self.placed = [(self._drawings[k], frame, self.host.view_label(v.kind, v.ref))
                       for k, (v, frame) in enumerate(zip(self.sheet.views, self.frames)) if frame is not None]

    def model_changed(self):
        """The model changed: what is shown is out of date until updated (that takes a moment)."""
        self._stale = True
        self.refresh_button.setText(t("sheet.refresh_needed"))
        self.refresh_button.setStyleSheet("font-weight: bold")

    def _mark_up_to_date(self):
        self.refresh_button.setText(t("sheet.refresh"))
        self.refresh_button.setStyleSheet("")

    def frame_of(self, k):
        return self.frames[k] if k is not None and 0 <= k < len(self.frames) else None

    def text(self):
        """What the sheet shows, one line per view (used by tests)."""
        lines = []
        for k, view in enumerate(self.sheet.views if self.sheet is not None else ()):
            frame = self.frame_of(k)
            where = "—" if frame is None else "1:{} em ({:.0f}, {:.0f}) mm".format(frame.scale, *frame.centre)
            lines.append("{}: {}".format(self.host.view_label(view.kind, view.ref), where))
        return "\n".join(lines)

    # ------------------------------------------------------------ user actions

    def picked(self, k):
        self.canvas.selected = k
        self.scale.setEnabled(k is not None)
        self.scale.setCurrentIndex(max(0, self.scale.findData(self.sheet.views[k].scale)) if k is not None else 0)

    def drag(self, k, centre):
        """Show view k at `centre` while it is dragged (kept on release)."""
        frame = self.frame_of(k)
        if frame is None:
            return
        self.frames[k] = sheets_model.Frame(frame.scale, centre, frame.width, frame.height)
        self._relabel()
        self.canvas.update()

    def move_view(self, k, centre):
        self._change(view=k, at=(round(centre[0], 1), round(centre[1], 1)))

    # (0.238) the labels a hand may move (Drawing.movable): found on the sheet, dragged, kept as the view's own

    def label_spot(self, k, i):
        """Where label i of view k starts on the sheet (mm: its text's lower left), or None."""
        frame, drawing = self.frame_of(k), self._drawings[k] if 0 <= k < len(self._drawings) else None
        if frame is None or drawing is None or drawing.bounds() is None:
            return None
        lo, hi = drawing.bounds()
        mid, at = (lo + hi) / 2, np.asarray(drawing.annotations[i][4], dtype=float)
        return (frame.centre[0] + (at[0] - mid[0]) * 1000.0 / frame.scale,
                frame.centre[1] - (at[1] - mid[1]) * 1000.0 / frame.scale)

    def label_at(self, x, y):
        """(view index, annotation index, key) of the movable label under (x, y) mm, or None."""
        for k in reversed(range(len(self.frames))):
            drawing = self._drawings[k] if k < len(self._drawings) else None
            for i, key in getattr(drawing, "movable", None) or ():
                spot = self.label_spot(k, i)
                if spot is None:
                    break
                words, size = drawing.annotations[i][3], drawing.annotations[i][5]
                if spot[0] <= x <= spot[0] + len(words) * 0.55 * size and spot[1] - size * 1.6 <= y <= spot[1] + 0.5:
                    return k, i, key
        return None

    def to_metres(self, k, dx, dy):
        """A move on the sheet (mm, y down) in view k's drawing (m, y up)."""
        scale = self.frame_of(k).scale
        return np.array((dx * scale / 1000.0, -dy * scale / 1000.0))

    def drag_label(self, k, i, where):
        """Show label i of view k at `where` (m) while it is dragged — on a copy: the drawing kept is not touched."""
        shown = copy.copy(self._drawings[k])
        shown.annotations = list(shown.annotations)
        shown.annotations[i] = shown.annotations[i][:4] + (np.asarray(where, dtype=float),) + shown.annotations[i][5:]
        self._drawings[k] = shown
        self._relabel()
        self.canvas.update()

    def move_label(self, k, key, offset, add=False):
        """Label `key` of view k that far (m) from its place — add: from where it is —, None: back to its place."""
        view = (self.sheet.views[k].kind, self.sheet.views[k].ref)
        if offset is not None and add:
            old = (self.host.doc.view_settings(view).labels or {}).get(key, (0.0, 0.0))
            offset = (round(float(old[0] + offset[0]), 3), round(float(old[1] + offset[1]), 3))
        if not self.host.doc.move_label(view, key, offset):
            self.refresh()

    def take_off(self, k):
        self.canvas.selected = None
        self._change(view=k, remove=True)

    def _scale_chosen(self, _index):
        if self.canvas.selected is not None:
            self._change(view=self.canvas.selected, scale=self.scale.currentData())

    def _tidy(self):
        """Every view back to its automatic place."""
        self._change(tidy=True)

    def edit_title_block(self):
        if self.sheet is not None:
            self.host.edit_title_block(self.host.doc.sheets.index(self.sheet))

    def _change(self, **changes):
        index = self.host.doc.sheets.index(self.sheet)
        self.host.doc.change_sheet(index, **changes)             # (the document tells the window: refresh)
