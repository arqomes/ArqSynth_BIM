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
import os

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..model import sheets as sheets_model
from . import pdf

PAPER_BG = QtGui.QColor("#7d7f83")
PICKED = QtGui.QColor("#1f74d1")
ZOOM_STEP = 1.2                 # (0.470) a wheel's step nearer
ZOOM_LEAST, ZOOM_MOST = 1.0, 40.0    # …the whole sheet at least, 40 times nearer at most


class SheetCanvas(QtWidgets.QWidget):
    """The sheet drawn to fit the widget."""

    def __init__(self, window):
        super().__init__(window)
        self.owner = window          # the SheetWindow (not QWidget.window())
        self.selected = None          # index of the view picked on the sheet
        self._drag = None             # (view index, mouse mm at the start, centre at the start)
        self._label = None            # (0.238) a label dragged: (view index, its annotation, key, mouse mm, its spot)
        # (0.470, the owner: «permitir zoom na folha») how near it is seen: the wheel brings the paper under the mouse
        # nearer, the middle button drags it, a double click with it (or «Ver tudo») shows it whole again
        self.zoom = 1.0
        self.pan = (0.0, 0.0)         # px: the paper moved so from the middle
        self._panning = None          # the mouse where the middle button last was
        self._grab = None             # (0.472) a drawing from outside grabbed: (its uid, mouse mm, its centre)
        self._moving = None           # …and where it is while dragged: (uid, centre)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(640, 460)

    def fit(self):
        """(pixels per mm, x, y of the paper's corner): the whole sheet with a margin — (0.470) nearer by the zoom,
        moved by the pan."""
        w, h = self.owner.sheet.size() if self.owner.sheet is not None else sheets_model.PAPERS["A3"]
        s = min((self.width() - 24) / w, (self.height() - 24) / h) * self.zoom
        return s, (self.width() - w * s) / 2 + self.pan[0], (self.height() - h * s) / 2 + self.pan[1]

    def zoom_at(self, factor, pos=None):
        """(0.470) Nearer (factor > 1) or farther, the paper under `pos` (px; None: the middle) staying under it."""
        pos = pos if pos is not None else QtCore.QPointF(self.width() / 2, self.height() / 2)
        x, y = self.to_mm(pos)
        self.zoom = min(max(self.zoom * factor, ZOOM_LEAST), ZOOM_MOST)
        if self.zoom <= ZOOM_LEAST + 1e-9:
            self.pan = (0.0, 0.0)                         # (all of it again: in the middle)
        else:
            s, x0, y0 = self.fit()
            self.pan = (self.pan[0] + pos.x() - (x0 + x * s), self.pan[1] + pos.y() - (y0 + y * s))
        self.update()

    def fit_all(self):
        """(0.470) The whole sheet in view again."""
        self.zoom, self.pan = 1.0, (0.0, 0.0)
        self.update()

    def wheelEvent(self, event):
        steps = event.angleDelta().y() / 120.0
        if steps:
            self.zoom_at(ZOOM_STEP ** steps, event.position())
        event.accept()

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
        imports = list(sheet.imports)
        if self._moving is not None:                         # (0.472) a drawing from outside being dragged
            uid, at = self._moving
            imports = [copy.copy(i) for i in imports]
            for i in imports:
                if i.uid == uid:
                    i.at = at
        pdf.paint_sheet(painter, s, (w, h), self.owner.host.title_block(sheet), self.owner.placed,
                        template=sheet.template, imports=imports)
        frame = self.owner.frame_of(self.selected)
        rect = frame.rect() if frame is not None else None
        picked = next((i for i in imports if i.uid == self.owner.picked_import), None)
        if rect is None and picked is not None:
            size = pdf.import_size(picked)
            if size is not None:
                rect = (picked.at[0] - size[0] / 2, picked.at[1] - size[1] / 2, size[0], size[1])
        if rect is not None:
            left, top, fw, fh = rect
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
        if event.button() == QtCore.Qt.MouseButton.MiddleButton:       # (0.470) the paper dragged
            self._panning = event.position()
            self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
            return
        if event.button() != QtCore.Qt.MouseButton.LeftButton:
            return
        x, y = self.to_mm(event.position())
        mine = self.owner.import_picked()               # (0.472) the drawing picked, under the mouse: it, not a view
        size = pdf.import_size(mine) if mine is not None else None
        if size is not None and abs(x - mine.at[0]) <= size[0] / 2 and abs(y - mine.at[1]) <= size[1] / 2:
            self.selected, self._drag = None, None
            self._grab = (mine.uid, (x, y), tuple(mine.at))
            self.owner.picked(None, mine.uid)
            self.update()
            return
        self.selected = self.view_at(x, y)
        frame = self.owner.frame_of(self.selected)
        self._drag = (self.selected, (x, y), frame.centre) if frame is not None else None
        hit = self.owner.label_at(x, y)                  # (0.238) on a label: the label is dragged, not the view
        if hit is not None:
            k, i, key = hit
            self.selected, self._drag = k, None
            self._label = (k, i, key, (x, y), np.array(self.owner._drawings[k].annotations[i][4], dtype=float))
        uid = None
        if self.selected is None:                        # (0.472) a drawing from outside, under the views
            item = self.owner.import_at(x, y)
            if item is not None:
                uid = item.uid
                self._grab = (uid, (x, y), tuple(item.at))
        self.owner.picked(self.selected, uid)
        self.update()

    def mouseDoubleClickEvent(self, event):
        """On the title block: fill it in. (0.238) On a label moved by hand: back to its place. (0.470) With the
        middle button: the whole sheet again (as Revit's)."""
        if event.button() == QtCore.Qt.MouseButton.MiddleButton:
            self.fit_all()
            return
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
        if self._panning is not None:                    # (0.470) the paper follows the middle button
            at = event.position()
            self.pan = (self.pan[0] + at.x() - self._panning.x(), self.pan[1] + at.y() - self._panning.y())
            self._panning = at
            self.update()
            return
        if self._label is not None:                      # (0.238) the label follows the mouse
            k, i, _key, (x0, y0), spot = self._label
            x, y = self.to_mm(event.position())
            self.owner.drag_label(k, i, spot + self.owner.to_metres(k, x - x0, y - y0))
            return
        if self._grab is not None:                       # (0.472) the drawing from outside follows the mouse
            uid, (x0, y0), (cx, cy) = self._grab
            x, y = self.to_mm(event.position())
            self._moving = (uid, (cx + x - x0, cy + y - y0))
            self.update()
            return
        if self._drag is None:
            return
        k, (x0, y0), (cx, cy) = self._drag
        x, y = self.to_mm(event.position())
        self.owner.drag(k, (cx + x - x0, cy + y - y0))

    def mouseReleaseEvent(self, event):
        if self._panning is not None and event.button() == QtCore.Qt.MouseButton.MiddleButton:
            self._panning = None
            self.unsetCursor()
            return
        if self._label is not None and event.button() == QtCore.Qt.MouseButton.LeftButton:
            k, i, key, (x0, y0), spot = self._label
            self._label = None
            x, y = self.to_mm(event.position())
            if abs(x - x0) + abs(y - y0) > 0.5:
                self.owner.move_label(k, key, self.owner.to_metres(k, x - x0, y - y0), add=True)
            else:
                self.owner.refresh()                     # (a click is not a move: the drawing as it was)
            return
        if self._grab is not None and event.button() == QtCore.Qt.MouseButton.LeftButton:   # (0.472)
            uid, (x0, y0), (cx, cy) = self._grab
            self._grab = self._moving = None
            x, y = self.to_mm(event.position())
            if abs(x - x0) + abs(y - y0) > 0.5:
                self.owner.move_import(uid, (cx + x - x0, cy + y - y0))
            self.update()
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
        if event.key() in (QtCore.Qt.Key.Key_Delete, QtCore.Qt.Key.Key_Backspace) and \
                self.owner.picked_import is not None:                               # (0.472)
            self.owner.take_off_import(self.owner.picked_import)
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

        # (0.470, the owner: «A edição do tipo da folha e propriedades devem ficar na coluna de propriedade») its paper
        # and title block are its type: in the Properties panel (Editar tipo…). (0.472, the owner: «Os parâmetros da
        # folha também devem ficar na barra de parâmetros») its commands are on the window's parameters' bar, as a
        # tool's (context_items): the zoom, the scale of what is picked, Arrumar, Importar desenho…, Editar carimbo…,
        # Atualizar desenhos, Exportar PDF…
        self.canvas = SheetCanvas(self)
        self.picked_import = None     # (0.472) the uid of the drawing from outside picked on the sheet
        self.act_zoom_out = self._act(t("sheet.zoom_out_short"), "sheet.zoom_out", lambda: self.canvas.zoom_at(1 / 1.5))
        self.act_zoom_in = self._act(t("sheet.zoom_in_short"), "sheet.zoom_in", lambda: self.canvas.zoom_at(1.5))
        self.act_zoom_all = self._act(t("sheet.zoom_all"), "sheet.zoom_all_tip", self.canvas.fit_all)
        self.act_tidy = self._act(t("sheet.tidy"), "sheet.tidy_tip", self._tidy)
        self.act_import = self._act(t("sheet.import"), "sheet.import_tip", lambda: self.import_drawing())
        self.act_title_block = self._act(t("sheet.edit_title_block"), "sheet.edit_title_block_tip",
                                         lambda: self.host.edit_company_title_block())
        self.act_refresh = self._act(t("sheet.refresh"), None, lambda: self.refresh(again=True))
        self.act_export = self._act(t("sheet.export"), None, lambda: self.host.export_sheets([self.sheet]))
        self.hint = QtWidgets.QLabel(t("sheet.hint"))
        self.hint.setWordWrap(True)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.canvas, 1)
        layout.addWidget(self.hint)

    def _act(self, text, tip, slot):
        act = QtGui.QAction(text, self)
        if tip:
            act.setToolTip(t(tip))
        act.triggered.connect(lambda _on=False: slot())
        return act

    # ------------------------------------------------------------ (0.472) on the parameters' bar

    def context_items(self):
        """What the window's parameters' bar shows while the sheet is: its commands and the scale (or width) of the
        view or drawing picked."""
        from ..tools.base import Option
        items = [("title", t("ctx.sheet")), ("action", self.act_zoom_out), ("action", self.act_zoom_in),
                 ("action", self.act_zoom_all), ("separator",)]
        k, item = self.canvas.selected, self.import_picked()
        if k is not None and self.sheet is not None and k < len(self.sheet.views):
            choices = ((None, t("sheet.scale_auto")),) + tuple((n, "1:{}".format(n)) for n in sheets_model.SCALES)
            items.append(("option", Option("sheet_scale", t("sheet.view_scale").rstrip(":"), "choice",
                                           self.sheet.views[k].scale, choices)))
        elif item is not None and item.kind == "cad":
            choices = tuple((n, "1:{}".format(n)) for n in sheets_model.IMPORT_SCALES)
            items.append(("option", Option("sheet_import_scale", t("sheet.import_scale"), "choice", item.scale,
                                           choices)))
        elif item is not None:
            widths = sorted(set(sheets_model.IMPORT_WIDTHS) | {int(round(item.width))})
            items.append(("option", Option("sheet_import_width", t("sheet.import_width"), "choice",
                                           int(round(item.width)), tuple((w, "{} mm".format(w)) for w in widths))))
        else:
            items.append(("hint", t("sheet.pick_hint")))
        items += [("action", self.act_tidy), ("separator",), ("action", self.act_import),
                  ("action", self.act_title_block), ("separator",), ("action", self.act_refresh),
                  ("action", self.act_export)]
        return items

    def option(self, key, value):
        """A setting of the parameters' bar changed (the sheet's)."""
        if key == "sheet_scale" and self.canvas.selected is not None:
            self._change(view=self.canvas.selected, scale=value)
        elif key == "sheet_import_scale" and self.picked_import is not None:
            self._import_change(scale=int(value))
        elif key == "sheet_import_width" and self.picked_import is not None:
            self._import_change(width=float(value))

    def set_scale(self, value):
        """(tests) The scale of the view picked."""
        self.option("sheet_scale", value)

    # ------------------------------------------------------------ (0.472) drawings from outside

    def import_picked(self):
        sheet = self.sheet
        if sheet is None or self.picked_import is None:
            return None
        return next((i for i in sheet.imports if i.uid == self.picked_import), None)

    def import_at(self, x, y):
        """The drawing from outside under (x, y) mm (the one put last if they overlap), or None."""
        sheet = self.sheet
        for item in reversed(sheet.imports if sheet is not None else ()):
            size = pdf.import_size(item)
            if size is not None and abs(x - item.at[0]) <= size[0] / 2 and abs(y - item.at[1]) <= size[1] / 2:
                return item
        return None

    def import_drawing(self, path=None):
        """Importar desenho…: a DWG / DXF, a picture or an SVG put on the sheet, in the middle of where the views
        go — a CAD drawing at the largest usual scale at which it fits there, a picture half as wide."""
        sheet = self.sheet
        if sheet is None:
            return None
        if path is None:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("sheet.import"), self.host.documents_folder(),
                                                            t("sheet.import_filter"))
            if not path:
                return None
        kind = sheets_model.import_kind(path)
        if kind is None:
            self.host.message(t("sheet.import_kind"), warning=True)
            return None
        left, top, width, height = sheets_model.drawing_area(sheet.paper, sheet.template, sheet.portrait)
        item = sheets_model.SheetImport(kind, os.path.abspath(path), os.path.basename(path),
                                        (round(left + width / 2, 1), round(top + height / 2, 1)),
                                        width=float(min(150, int(width / 2))))
        if kind == "cad":
            try:
                from ..core import cad
                item.units = float(cad.read_file(path).units)
            except (OSError, ValueError):
                self.host.message(t("sheet.import_bad", f=os.path.basename(path)), warning=True)
                return None
            item.scale = sheets_model.IMPORT_SCALES[-1]
            for scale in sheets_model.IMPORT_SCALES:            # (the largest at which it fits)
                item.scale = scale
                size = pdf.import_size(item)
                if size is not None and size[0] <= width and size[1] <= height:
                    break
        if pdf.import_size(item) is None:
            self.host.message(t("sheet.import_bad", f=os.path.basename(path)), warning=True)
            return None
        self.host.doc.add_sheet_import(self.host.doc.sheets.index(sheet), item)
        self.picked(None, item.uid)
        self.host.message(t("info.sheet_import", name=item.name))
        self.canvas.update()
        return item

    def _import_change(self, **changes):
        sheet = self.sheet
        if sheet is not None and self.picked_import is not None:
            self.host.doc.change_sheet_import(self.host.doc.sheets.index(sheet), self.picked_import, **changes)

    def move_import(self, uid, at):
        sheet = self.sheet
        if sheet is not None:
            self.host.doc.change_sheet_import(self.host.doc.sheets.index(sheet), uid,
                                              at=(round(at[0], 1), round(at[1], 1)))

    def take_off_import(self, uid):
        sheet = self.sheet
        if sheet is not None:
            self.picked(self.canvas.selected, None)
            self.host.doc.change_sheet_import(self.host.doc.sheets.index(sheet), uid, remove=True)

    # ------------------------------------------------------------ content

    @property
    def sheet(self):
        """The sheet shown, found by its uid (undo / redo put back copies of the sheets)."""
        return next((s for s in self.host.doc.sheets if s.uid == self._uid), None) if self._uid else None

    def show_sheet(self, sheet):
        """Show this sheet (its tab was chosen)."""
        if sheet.uid != self._uid:
            self.canvas.selected = None
            self.canvas.zoom, self.canvas.pan = 1.0, (0.0, 0.0)      # (0.470: another sheet: all of it)
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
        sheets_model.use_company(self.host.doc.title_block.get(sheets_model.COMPANY_KEY))   # (0.472: its boxes)
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
                    and self.canvas.selected < len(self.frames) else None,
                    self.picked_import if any(i.uid == self.picked_import for i in sheet.imports) else None)
        self.canvas.update()

    def _relabel(self):
        self.placed = [(self._drawings[k], frame, self.host.view_label(v.kind, v.ref))
                       for k, (v, frame) in enumerate(zip(self.sheet.views, self.frames)) if frame is not None]

    def model_changed(self):
        """The model changed: what is shown is out of date until updated (that takes a moment)."""
        self._stale = True
        self.act_refresh.setText(t("sheet.refresh_needed"))

    def _mark_up_to_date(self):
        self.act_refresh.setText(t("sheet.refresh"))

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

    def picked(self, k, uid=None):
        """A view (k) or (0.472) a drawing from outside (uid) picked on the sheet — or nothing: the parameters' bar
        shows its scale."""
        self.canvas.selected, self.picked_import = k, uid
        if (k, uid) != getattr(self, "_shown_pick", (None, None)):
            self._shown_pick = (k, uid)                  # (the bar made again only when what is picked changes)
            if hasattr(self.host, "refresh_context_bar"):
                self.host.refresh_context_bar()

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

    def _tidy(self):
        """Every view back to its automatic place."""
        self._change(tidy=True)

    def edit_title_block(self):
        """(0.470) A double click on the title block: the sheet's type (Editar tipo…, its own window)."""
        if self.sheet is not None:
            self.host.edit_sheet_type(self.host.doc.sheets.index(self.sheet))

    def _change(self, **changes):
        index = self.host.doc.sheets.index(self.sheet)
        self.host.doc.change_sheet(index, **changes)             # (the document tells the window: refresh)
