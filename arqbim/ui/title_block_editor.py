"""(0.473, the owner: «se o carimbo pudesse abrir na tela e o utilizador usar as ferramentas de desenhos e inserir os
campos seria melhor e teria maior grau de personalização. Maior liberdade criativa») The company's title block drawn on
the sheet itself, as Revit's title block family in its editor. «Editar carimbo…» puts the sheet in this mode: the views
faded, a faint 5 mm grid round the corner, the title block's drawing on top — its empty fields by their names — and the
parameters' bar gives

- the tools: Selecionar, Linha, Retângulo, Texto, Campo, Imagem — two clicks (or a drag) for a line, a rectangle or a
  box for a text, a field or a picture (a click alone: a box of the usual size); a text written in place;
- the snaps of the drawing tools, in magenta: ends and corners, middles, lined up with them or with the border,
  horizontal and vertical, else a 0,5 mm grid;
- what is picked (or what the tool will draw): a line's thickness, a rectangle's fill, a text's words, the size, bold,
  how it lines up and its colour, the field (the project, the drawing, its number, the scale, the date, the revision,
  how many sheets… and the project's own fields), a picture's file;
- «Começar de» (the program's title blocks, the office's, blank), «Guardar no escritório», «Em todas as folhas»,
  «Concluir» (one undo step in the project) and «Cancelar».

Selecionar: a click picks (Shift: more), a window picks what is in it (from the right: what it touches), a drag moves
what is picked (the point taken snapped), the grips move a line's ends or a box's corners; a double click writes a text
(or changes a picture); Delete, Ctrl+C / Ctrl+V, Ctrl+A, the arrows (Shift: 5 mm), Ctrl+Z / Ctrl+Y (the drawing's own
steps until «Concluir»), Esc. Points in mm from the border's inside corner, bottom right (model/sheets.py)."""

import copy
import math
import os

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..model import company_title_block as company_file
from ..model import sheets as sheets_model
from . import pdf

TOOLS = ("select", "line", "rect", "text", "field", "image")
GRID = 0.5                     # mm: a point falls on it when nothing else is near
GRID_SHOWN = 5.0               # mm: the faint grid's step
SNAP_PX = 9                    # px: how near a point is taken
PICK_PX = 6                    # px: how near a line is picked
ORTHO_DEG = 4.0                # degrees from horizontal / vertical that become it
NUDGE, NUDGE_BIG = 0.5, 5.0    # mm: an arrow's step (Shift: the big one)
LINE_MARK = " ¶ "              # (a text's lines on the bar, which has one)
DEFAULT_BOX = {"text": 40.0, "field": 50.0, "image": 30.0}      # mm across: a box made with a click
STYLE_KEYS = ("pen", "fill", "size", "bold", "align", "colour", "field")
APPLIES = {"pen": ("line", "rect"), "fill": ("rect",), "size": ("text", "field"), "bold": ("text", "field"),
           "align": ("text", "field"), "colour": ("text", "field"), "field": ("field",), "text": ("text",)}
BLUE = QtGui.QColor("#1f74d1")
MAGENTA = QtGui.QColor("#d22bd2")
VEIL = QtGui.QColor(255, 255, 255, 175)
GRID_COLOUR = QtGui.QColor("#dde5ef")


def start_drawing(doc, sheet):
    """What the editor starts from: the project's company title block, else the office's, else the sheet's own
    template drawn as such (what the user sees there now)."""
    own = doc.title_block.get(sheets_model.COMPANY_KEY)
    found = sheets_model.clean_company(own) if own else None
    if found is not None:
        return found
    office = company_file.load()
    if office is not None:
        return office
    template = sheet.template if sheet.template in ("full", "compact", "strip") else "company"
    return {"items": sheets_model.template_items(template, sheet.size()[1] - 2 * sheets_model.MARGIN)}


def _seg_distance(p, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    length = dx * dx + dy * dy
    k = 0.0 if length < 1e-12 else min(max(((p[0] - ax) * dx + (p[1] - ay) * dy) / length, 0.0), 1.0)
    return math.hypot(p[0] - ax - k * dx, p[1] - ay - k * dy)


def _bounds(item):
    (ax, ay), (bx, by) = item["pts"]
    return min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)


def snap_points(item):
    """An item's points the others snap to: a line's ends and middle, a box's corners and the middles of its sides."""
    (ax, ay), (bx, by) = item["pts"]
    if item["kind"] == "line":
        return [((ax, ay), "end"), ((bx, by), "end"), (((ax + bx) / 2, (ay + by) / 2), "mid")]
    x0, y0, x1, y1 = _bounds(item)
    return [((x0, y0), "end"), ((x1, y0), "end"), ((x0, y1), "end"), ((x1, y1), "end"),
            (((x0 + x1) / 2, y0), "mid"), (((x0 + x1) / 2, y1), "mid"), ((x0, (y0 + y1) / 2), "mid"),
            ((x1, (y0 + y1) / 2), "mid")]


class _Writer(QtWidgets.QPlainTextEdit):
    """A text written in place, over its box: Enter keeps it (Shift+Enter: another line), Esc lets it be."""

    def __init__(self, editor, index, new):
        super().__init__(editor.window.canvas)
        self.editor, self.index, self.new = editor, index, new
        self.setObjectName("title_block_writer")
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setStyleSheet("QPlainTextEdit#title_block_writer { background: #ffffff; color: #111111;"
                           " border: 2px solid #1f74d1; }")
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter) and \
                not event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
            self.editor.finish_writing()
            return
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.editor.finish_writing(keep=False)
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        QtCore.QTimer.singleShot(0, lambda: self.editor.finish_writing(focus=False) if self.editor.writer is self
                                 else None)        # (a field of the bar clicked: the keyboard stays there)


class TitleBlockEditor(QtCore.QObject):
    """The title block being drawn on the sheet window's sheet (window: ui/sheet_view.SheetWindow); its canvas feeds
    it the mouse (mm on the paper) and the keys, and paints it."""

    def __init__(self, window, company):
        super().__init__(window)
        self.window = window
        self.doc = window.host.doc
        self.items = copy.deepcopy(company["items"])
        self.saved = copy.deepcopy(self.items)           # (as it was: Cancelar asks only when it changed)
        self.tool = "select"
        self.picked = []                                 # indices of the items picked
        self.undo_steps, self.redo_steps = [], []
        self.style = {"pen": 0.25, "fill": "", "size": 7.0, "bold": False, "align": "left", "colour": "#000000",
                      "field": "project"}
        self.everyone = True                             # «Concluir»: on every sheet
        self.start = None                                # the first point of what is being drawn
        self._pressed = None                             # (where the button went down: a drag draws too)
        self.mouse = None                                # where the mouse is (snapped)
        self.snapped_to = None                           # "end" | "mid" | "align" | "ortho" | "grid"
        self.guides = []                                 # [(from, to)]: the lines the point is lined up with
        self.grab = None                                 # moving: ("move" | "grip", …)
        self.box = None                                  # a window picking: (start, now)
        self.writer = None                               # the text being written
        self.clipboard = []
        self.next_picture = None                         # (tests: the picture «Imagem» takes, without asking)
        self.act_picture = self._act(t("tbe.picture"), lambda: self.choose_picture())
        self.act_delete = self._act(t("tbe.delete"), self.delete_picked)
        self.act_save_office = self._act(t("tbe.save_office"), self.save_office, "tbe.save_office_tip")
        self.act_done = self._act(t("tbe.done"), lambda: self.window.finish_editor(apply=True), "tbe.done_tip")
        self.act_cancel = self._act(t("tbe.cancel"), lambda: self.window.finish_editor(apply=False, ask=True))

    def _act(self, text, slot, tip=None):
        act = QtGui.QAction(text, self)
        if tip:
            act.setToolTip(t(tip))
        act.triggered.connect(lambda _on=False: slot())
        return act

    # ------------------------------------------------------------ where things are

    def corner(self):
        """(x, y) mm on the paper of the border's inside corner, bottom right (the items' origin)."""
        w, h = self.window.sheet.size()
        return w - sheets_model.MARGIN, h - sheets_model.MARGIN

    def inner(self):
        w, h = self.window.sheet.size()
        return w - 2 * sheets_model.MARGIN, h - 2 * sheets_model.MARGIN

    def rel(self, x, y):
        cx, cy = self.corner()
        return [x - cx, y - cy]

    def px(self):
        """Pixels a mm on the screen now."""
        return max(self.window.canvas.fit()[0], 1e-6)

    def company(self):
        return {"items": copy.deepcopy(self.items)}

    def changed_since_start(self):
        return self.items != self.saved

    # ------------------------------------------------------------ snaps and picking

    def snap(self, p, origin=None, skip=()):
        """(the point, what it fell on): an end or a corner, a middle, lined up with them or with the border
        (guides), horizontal / vertical from `origin`, else the grid. `skip`: items not snapped to (those moved)."""
        tol = SNAP_PX / self.px()
        iw, ih = self.inner()
        candidates = [((0.0, 0.0), "end"), ((-iw, 0.0), "end"), ((0.0, -ih), "end"), ((-iw, -ih), "end")]
        for k, item in enumerate(self.items):
            if k not in skip:
                candidates += snap_points(item)
        self.guides = []
        best = None
        for q, kind in candidates:
            d = math.hypot(q[0] - p[0], q[1] - p[1])
            if d <= tol and (best is None or d < best[0]):
                best = (d, q, kind)
        if best is not None:
            return [round(best[1][0], 3), round(best[1][1], 3)], best[2]
        x, y = p
        lock_x = lock_y = False
        kind = "grid"
        if origin is not None and math.hypot(x - origin[0], y - origin[1]) > tol:
            angle = math.degrees(math.atan2(abs(y - origin[1]), abs(x - origin[0])))
            if angle <= ORTHO_DEG:
                y, lock_y, kind = origin[1], True, "ortho"
            elif angle >= 90.0 - ORTHO_DEG:
                x, lock_x, kind = origin[0], True, "ortho"
        if not lock_x:                                   # (lined up with a point across: a column of texts)
            near = [q for q, _k in candidates if abs(q[0] - x) <= tol]
            if near:
                q = min(near, key=lambda q: abs(q[0] - x))
                x, lock_x, kind = q[0], True, "align" if kind == "grid" else kind
                self.guides.append((q, None))
        if not lock_y:
            near = [q for q, _k in candidates if abs(q[1] - y) <= tol]
            if near:
                q = min(near, key=lambda q: abs(q[1] - y))
                y, lock_y, kind = q[1], True, "align" if kind == "grid" else kind
                self.guides.append((q, None))
        if kind == "ortho":
            self.guides.append((tuple(origin), None))
        if not lock_x:
            x = round(x / GRID) * GRID
        if not lock_y:
            y = round(y / GRID) * GRID
        return [round(x, 3), round(y, 3)], kind

    def _hits(self, item, p, tol):
        if item["kind"] == "line":
            return _seg_distance(p, *item["pts"]) <= tol
        x0, y0, x1, y1 = _bounds(item)
        inside = x0 - tol <= p[0] <= x1 + tol and y0 - tol <= p[1] <= y1 + tol
        if item["kind"] == "rect" and not item["fill"]:               # (an empty rectangle: by its sides)
            return inside and not (x0 + tol < p[0] < x1 - tol and y0 + tol < p[1] < y1 - tol)
        return inside

    def item_at(self, p):
        """The item under p (mm from the corner): the one drawn last."""
        tol = PICK_PX / self.px()
        for k in reversed(range(len(self.items))):
            if self._hits(self.items[k], p, tol):
                return k
        return None

    def grip_at(self, p):
        """(item, 0 | 1) of a picked item's grip under p, or None."""
        tol = SNAP_PX / self.px()
        for k in self.picked:
            for j, q in enumerate(self.items[k]["pts"]):
                if math.hypot(q[0] - p[0], q[1] - p[1]) <= tol:
                    return k, j
        return None

    def in_window(self, a, b):
        """The items in the window from a to b (dragged from the right: those it touches)."""
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        crossing = b[0] < a[0]
        out = []
        for k, item in enumerate(self.items):
            ix0, iy0, ix1, iy1 = _bounds(item)
            if crossing:
                hit = not (ix1 < x0 or ix0 > x1 or iy1 < y0 or iy0 > y1)
            else:
                hit = x0 <= ix0 and ix1 <= x1 and y0 <= iy0 and iy1 <= y1
            if hit:
                out.append(k)
        return out

    # ------------------------------------------------------------ changes

    def _push(self):
        self.undo_steps.append(copy.deepcopy(self.items))
        del self.undo_steps[:-200]
        self.redo_steps = []

    def undo(self):
        if not self.undo_steps:
            return False
        self.redo_steps.append(copy.deepcopy(self.items))
        self.items = self.undo_steps.pop()
        self.set_picked([])
        self.changed()
        return True

    def redo(self):
        if not self.redo_steps:
            return False
        self.undo_steps.append(copy.deepcopy(self.items))
        self.items = self.redo_steps.pop()
        self.set_picked([])
        self.changed()
        return True

    def changed(self, bar=False):
        self.window.canvas.update()
        if bar:
            self._bar()

    def _bar(self):
        host = self.window.host
        if hasattr(host, "refresh_context_bar"):
            host.refresh_context_bar()

    def set_picked(self, picked):
        picked = [k for k in dict.fromkeys(picked) if 0 <= k < len(self.items)]
        if picked != self.picked:
            self.picked = picked
            self._bar()
        self.window.canvas.update()

    def add(self, item):
        """A new item drawn: one step; it is picked. Returns its index."""
        item = sheets_model.clean_item(item)
        if item is None:
            return None
        self._push()
        self.items.append(item)
        self.set_picked([len(self.items) - 1])
        self.changed(bar=True)
        return len(self.items) - 1

    def delete_picked(self):
        if not self.picked:
            return False
        self._push()
        gone = set(self.picked)
        self.items = [item for k, item in enumerate(self.items) if k not in gone]
        self.set_picked([])
        self.changed(bar=True)
        return True

    def nudge(self, dx, dy):
        if not self.picked:
            return False
        self._push()
        for k in self.picked:
            self.items[k]["pts"] = [[round(x + dx, 3), round(y + dy, 3)] for x, y in self.items[k]["pts"]]
        self.changed()
        return True

    def copy_picked(self):
        self.clipboard = [copy.deepcopy(self.items[k]) for k in self.picked]
        return bool(self.clipboard)

    def paste(self):
        """What was copied, its top-left corner at the mouse (or 5 mm up and left of where it was)."""
        if not self.clipboard:
            return False
        x0 = min(p[0] for i in self.clipboard for p in i["pts"])
        y0 = min(p[1] for i in self.clipboard for p in i["pts"])
        dx, dy = (self.mouse[0] - x0, self.mouse[1] - y0) if self.mouse is not None else (-5.0, -5.0)
        self._push()
        first = len(self.items)
        for item in self.clipboard:
            new = copy.deepcopy(item)
            new["pts"] = [[round(x + dx, 3), round(y + dy, 3)] for x, y in new["pts"]]
            self.items.append(new)
        self.set_picked(list(range(first, len(self.items))))
        self.changed(bar=True)
        return True

    # ------------------------------------------------------------ the tools

    def set_tool(self, name):
        name = name if name in TOOLS else "select"
        self.finish_writing()
        self.start = self._pressed = self.grab = self.box = None
        self.tool = name
        if name != "select":
            self.picked = []
        self.window.canvas.setCursor(QtCore.Qt.CursorShape.ArrowCursor if name == "select"
                                     else QtCore.Qt.CursorShape.CrossCursor)
        self.changed(bar=True)

    def _make(self, a, b, drag=True):
        """What the tool draws from a to b (mm from the corner)."""
        kind = self.tool
        if kind == "line":
            if math.hypot(b[0] - a[0], b[1] - a[1]) < 0.2:
                return None
            return self.add({"kind": "line", "pts": [a, b], "pen": self.style["pen"]})
        if kind == "rect":
            if abs(b[0] - a[0]) < 0.2 or abs(b[1] - a[1]) < 0.2:
                return None
            return self.add({"kind": "rect", "pts": [a, b], "pen": self.style["pen"], "fill": self.style["fill"]})
        if not drag or (abs(b[0] - a[0]) < 1.0 and abs(b[1] - a[1]) < 1.0):     # (a click: a box of the usual size)
            h = 15.0 if kind == "image" else round(max(self.style["size"] * 0.3528 * 1.7, 2.5), 1)
            b = [a[0] + DEFAULT_BOX[kind], a[1] + h]
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        box = [[x0, y0], [x1, y1]]
        if kind == "image":
            k = self.add({"kind": "image", "pts": box, "path": ""})
            if k is not None and not self.choose_picture(k, new=True):
                return None
            return k
        item = {"kind": kind, "pts": box, "size": self.style["size"], "bold": self.style["bold"],
                "align": self.style["align"], "colour": self.style["colour"]}
        if kind == "field":
            item["field"] = self.style["field"]
            return self.add(item)
        item["text"] = ""
        k = self.add(item)
        if k is not None:
            self.write(k, new=True)
        return k

    def press(self, x, y, modifiers=QtCore.Qt.KeyboardModifier.NoModifier):
        """The left button down at (x, y) mm on the paper."""
        p = self.rel(x, y)
        if self.writer is not None:
            self.finish_writing()
        if self.tool == "select":
            grip = self.grip_at(p)
            if grip is not None:
                self.grab = ("grip", grip, copy.deepcopy(self.items))
                return
            k = self.item_at(p)
            shift = bool(modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier)
            if k is None:
                if not shift:
                    self.set_picked([])
                self.box = (p, p)
                return
            if shift:
                self.set_picked([j for j in self.picked if j != k] if k in self.picked else self.picked + [k])
            elif k not in self.picked:
                self.set_picked([k])
            if k in self.picked:
                anchor = min((q for q, _kind in snap_points(self.items[k])),
                             key=lambda q: math.hypot(q[0] - p[0], q[1] - p[1]))
                self.grab = ("move", anchor, p, copy.deepcopy(self.items))
            return
        q, self.snapped_to = self.snap(p, self.start)
        self.mouse = q
        if self.start is None:
            self.start, self._pressed = q, q
        else:
            start, self.start = self.start, None
            self._make(start, q)
        self.window.canvas.update()

    def move(self, x, y, buttons=QtCore.Qt.MouseButton.NoButton, modifiers=QtCore.Qt.KeyboardModifier.NoModifier):
        p = self.rel(x, y)
        if self.grab is not None and self.grab[0] == "move":
            _kind, anchor, start, before = self.grab
            target, self.snapped_to = self.snap([anchor[0] + p[0] - start[0], anchor[1] + p[1] - start[1]],
                                                skip=self.picked)
            dx, dy = target[0] - anchor[0], target[1] - anchor[1]
            self.items = copy.deepcopy(before)
            for k in self.picked:
                self.items[k]["pts"] = [[round(a + dx, 3), round(b + dy, 3)] for a, b in self.items[k]["pts"]]
            self.mouse = target
        elif self.grab is not None:
            _kind, (k, j), before = self.grab
            other = before[k]["pts"][1 - j]
            q, self.snapped_to = self.snap(p, other if before[k]["kind"] == "line" else None, skip=(k,))
            self.items = copy.deepcopy(before)
            self.items[k]["pts"][j] = q
            self.mouse = q
        elif self.box is not None:
            self.box = (self.box[0], p)
            self.mouse = p
        elif self.tool != "select":
            self.mouse, self.snapped_to = self.snap(p, self.start)
        else:
            self.mouse, self.snapped_to, self.guides = p, None, []
        self.window.canvas.update()

    def release(self, x, y, _modifiers=QtCore.Qt.KeyboardModifier.NoModifier):
        p = self.rel(x, y)
        if self.grab is not None:
            before = self.grab[-1]
            self.grab = None
            if self.items != before:
                self.undo_steps.append(before)
                del self.undo_steps[:-200]
                self.redo_steps = []
            self.snapped_to, self.guides = None, []
            self.changed()
            return
        if self.box is not None:
            a, self.box = self.box[0], None
            if math.hypot(p[0] - a[0], p[1] - a[1]) * self.px() > 4:
                self.set_picked(self.in_window(a, p))
            self.window.canvas.update()
            return
        pressed, self._pressed = self._pressed, None
        if self.tool == "select" or pressed is None or self.start is None:
            return
        q, _kind = self.snap(p, self.start)
        if math.hypot(q[0] - pressed[0], q[1] - pressed[1]) * self.px() > 6:      # (a drag: drawn at once)
            start, self.start = self.start, None
            self._make(start, q)
        elif self.tool in ("text", "field", "image"):                           # (a click: a box of the usual size)
            start, self.start = self.start, None
            self._make(start, start, drag=False)
        self.window.canvas.update()

    def double_click(self, x, y):
        if self.tool != "select":
            return
        k = self.item_at(self.rel(x, y))
        if k is None:
            return
        if self.items[k]["kind"] == "text":
            self.write(k)
        elif self.items[k]["kind"] == "image":
            self.choose_picture(k)

    def right_click(self):
        """As Esc: what is being drawn let go, else the Selecionar tool."""
        self.escape()

    def escape(self):
        if self.writer is not None:
            self.finish_writing(keep=False)
        elif self.start is not None:
            self.start = None
            self.window.canvas.update()
        elif self.tool != "select":
            self.set_tool("select")
        elif self.picked:
            self.set_picked([])
        else:
            return False
        return True

    def key(self, event):
        """A key in the sheet: True when the title block took it."""
        key, mods = event.key(), event.modifiers()
        ctrl = bool(mods & QtCore.Qt.KeyboardModifier.ControlModifier)
        shift = bool(mods & QtCore.Qt.KeyboardModifier.ShiftModifier)
        Key = QtCore.Qt.Key
        if key in (Key.Key_Delete, Key.Key_Backspace):
            self.delete_picked()
            return True
        if key == Key.Key_Escape:
            self.escape()
            return True
        if ctrl and key == Key.Key_Z:
            (self.redo if shift else self.undo)()
            return True
        if ctrl and key == Key.Key_Y:
            self.redo()
            return True
        if ctrl and key == Key.Key_C:
            self.copy_picked()
            return True
        if ctrl and key == Key.Key_V:
            self.paste()
            return True
        if ctrl and key == Key.Key_A:
            self.set_tool("select")
            self.set_picked(list(range(len(self.items))))
            return True
        step = NUDGE_BIG if shift else NUDGE
        moves = {Key.Key_Left: (-step, 0.0), Key.Key_Right: (step, 0.0), Key.Key_Up: (0.0, -step),
                 Key.Key_Down: (0.0, step)}
        if key in moves:
            self.nudge(*moves[key])
            return True
        if key in (Key.Key_Return, Key.Key_Enter) and len(self.picked) == 1 and \
                self.items[self.picked[0]]["kind"] == "text":
            self.write(self.picked[0])
            return True
        return False

    @staticmethod
    def owns_shortcut(event):
        """The keys the title block takes before the window's shortcuts (Delete, Ctrl+Z…)."""
        Key = QtCore.Qt.Key
        if event.key() in (Key.Key_Delete, Key.Key_Backspace, Key.Key_Escape, Key.Key_Left, Key.Key_Right,
                           Key.Key_Up, Key.Key_Down, Key.Key_Return, Key.Key_Enter):
            return True
        return bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier) and \
            event.key() in (Key.Key_Z, Key.Key_Y, Key.Key_C, Key.Key_V, Key.Key_A)

    # ------------------------------------------------------------ texts and pictures

    def write(self, k, new=False):
        """Text k written in place, over its box."""
        self.finish_writing()
        item = self.items[k]
        canvas = self.window.canvas
        s, x0, y0 = canvas.fit()
        x, y, w, h = pdf.item_box(item, *self.corner())
        font = QtGui.QFont("Segoe UI")
        font.setPixelSize(max(12, round(item["size"] * 0.3528 * s)))
        font.setBold(item["bold"])
        writer = _Writer(self, k, new)
        writer.setFont(font)
        writer.setPlainText(item["text"])
        lines = max(1, item["text"].count("\n") + 1)
        height = max(h * s, QtGui.QFontMetrics(font).height() * lines + 10)
        writer.setGeometry(QtCore.QRect(round(x0 + x * s) - 2, round(y0 + y * s) - 2, max(round(w * s), 140) + 4,
                                        round(height) + 4))
        writer.selectAll()
        writer.show()
        writer.setFocus()
        self.writer = writer
        self.set_picked([k])
        return writer

    def finish_writing(self, keep=True, focus=True):
        writer, self.writer = self.writer, None
        if writer is None:
            return
        k, new = writer.index, writer.new
        words = writer.toPlainText().strip()
        writer.hide()
        writer.deleteLater()
        if 0 <= k < len(self.items) and self.items[k]["kind"] == "text":
            if keep and words:
                if words != self.items[k]["text"]:
                    if not new:
                        self._push()
                    self.items[k]["text"] = words
            elif new:                                    # (nothing written in a new text: it goes, and its step)
                del self.items[k]
                if self.undo_steps:
                    self.undo_steps.pop()
                self.picked = []
        if focus:
            self.window.canvas.setFocus()
        self.changed(bar=True)

    def choose_picture(self, k=None, path=None, new=False):
        """A picture (the logo…) for image item k (the one picked): its file asked for. False if none was given."""
        if k is None:
            k = self.picked[0] if len(self.picked) == 1 and self.items[self.picked[0]]["kind"] == "image" else None
        if k is None:
            return False
        if path is None:
            path, self.next_picture = self.next_picture, None
        if path is None:
            start = os.path.dirname(self.items[k]["path"]) if self.items[k]["path"] else \
                self.window.host.documents_folder() if hasattr(self.window.host, "documents_folder") else ""
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self.window, t("tbe.picture"), start,
                                                            t("tbe.picture_filter"))
        if not path:
            if new:                                      # (no picture for a new box: it goes, and its step)
                del self.items[k]
                if self.undo_steps:
                    self.undo_steps.pop()
                self.set_picked([])
                self.changed(bar=True)
            return False
        if not new:
            self._push()
        self.items[k]["path"] = os.path.abspath(path)
        self.changed(bar=True)
        return True

    # ------------------------------------------------------------ the bar

    def _picked_kinds(self):
        return {self.items[k]["kind"] for k in self.picked}

    def _value(self, name):
        for k in self.picked:
            if name in self.items[k]:
                return self.items[k][name]
        return self.style.get(name)

    def field_choices(self):
        out = [(f, pdf.field_label(f)) for f in sheets_model.FIELDS]
        for label, _text in self.doc.title_block.get(sheets_model.EXTRA_KEY) or ():
            out.append((sheets_model.EXTRA_FIELD + str(label), "{} ({})".format(label, t("tbe.own_field"))))
        return tuple(out)

    def context_items(self):
        """The parameters' bar while the title block is drawn: the tools, what is picked (or what the tool draws), the
        title block's commands."""
        from ..tools.base import Option
        # («Concluir» and «Cancelar» first, always in sight, as Revit's ✓ / ✗ of an edit mode; the title block's own
        # commands only while nothing is picked nor drawn — then what is picked takes their room)
        items = [("title", t("tbe.title")), ("action", self.act_done), ("action", self.act_cancel), ("separator",),
                 ("option", Option("sheet_tb_tool", "", "buttons", self.tool,
                                   tuple((k, t("tbe.tool_" + k)) for k in TOOLS))),
                 ("separator",)]
        kinds = self._picked_kinds() if self.picked else ({self.tool} if self.tool in sheets_model.ITEM_KINDS else set())
        if kinds and kinds <= {"line", "rect"}:
            pen = float(self._value("pen"))
            pens = sorted(set(sheets_model.PENS) | {pen})
            items.append(("option", Option("sheet_tb_pen", t("tbe.pen"), "choice", pen,
                                           tuple((v, "{} mm".format(str(v).replace(".", ","))) for v in pens))))
        if kinds == {"rect"}:
            items.append(("option", Option("sheet_tb_fill", t("tbe.fill"), "choice", self._value("fill"),
                                           tuple((f, t("tbe.fill_" + (f.lstrip("#") or "none")))
                                                 for f in sheets_model.FILLS))))
        if kinds == {"text"} and len(self.picked) == 1:
            words = self.items[self.picked[0]]["text"]
            items.append(("option", Option("sheet_tb_text", t("tbe.text"), "text", LINE_MARK.join(words.split("\n")))))
        if kinds == {"field"}:
            items.append(("option", Option("sheet_tb_field", t("tbe.field"), "choice", self._value("field"),
                                           self.field_choices())))
        if kinds and kinds <= {"text", "field"}:
            size = float(self._value("size"))
            sizes = sorted(set(sheets_model.TEXT_SIZES) | {size})
            items += [("option", Option("sheet_tb_size", t("tbe.size"), "choice", size,
                                        tuple((v, "{:g} pt".format(v).replace(".", ",")) for v in sizes))),
                      ("option", Option("sheet_tb_bold", t("tbe.bold"), "toggle", bool(self._value("bold")))),
                      ("option", Option("sheet_tb_align", t("tbe.align"), "choice", self._value("align"),
                                        tuple((a, t("tbe.align_" + a)) for a in sheets_model.ALIGNS))),
                      ("option", Option("sheet_tb_colour", t("tbe.colour"), "choice", self._value("colour"),
                                        tuple((c, t("tbe.colour_" + c.lstrip("#"))) for c in sheets_model.COLOURS)))]
        if self.picked and kinds == {"image"}:
            items.append(("action", self.act_picture))
        if self.picked:
            items.append(("action", self.act_delete))
        if not kinds:
            starts = (("", "—"),) + tuple((k, t("tbe.start_" + k)) for k in sheets_model.TEMPLATE_STARTS[:4]) + \
                (("office", t("tbe.start_office")), ("blank", t("tbe.start_blank")))
            items += [("option", Option("sheet_tb_start", t("tbe.start"), "choice", "", starts)),
                      ("action", self.act_save_office),
                      ("option", Option("sheet_tb_everyone", t("tbe.everyone"), "toggle", self.everyone))]
        return items

    def option(self, key, value):
        """A setting of the bar changed: the tool, what is picked (and what the tool draws next), the title block's."""
        name = key[len("sheet_tb_"):]
        if name == "tool":
            self.set_tool(value or "select")
            return
        if name == "start":
            self.start_from(value)
            return
        if name == "everyone":
            self.everyone = bool(value)
            self._bar()
            return
        if name == "align" and not value:               # (the one lit clicked again: it stays)
            self._bar()
            return
        if name == "text":
            value = "\n".join(part.strip() for part in str(value).split(LINE_MARK.strip())).strip()
        elif name in ("pen", "size"):
            value = float(value)
        elif name == "bold":
            value = bool(value)
        targets = [k for k in self.picked if self.items[k]["kind"] in APPLIES.get(name, ())]
        if targets and any(self.items[k].get(name) != value for k in targets):
            self._push()
            for k in targets:
                self.items[k][name] = value
        if name in STYLE_KEYS:
            self.style[name] = value
        self.changed(bar=True)

    def start_from(self, what):
        """«Começar de»: the drawing made again from one of the program's title blocks, the office's or nothing (one
        step: Ctrl+Z puts it back)."""
        if not what:
            return False
        if what == "office":
            office = company_file.load()
            if office is None:
                self.window.host.message(t("tbe.office_none"), warning=True)
                self._bar()
                return False
            items = office["items"]
        else:
            items = sheets_model.template_items(what, self.inner()[1])
        self._push()
        self.items = copy.deepcopy(items)
        self.set_picked([])
        self.zoom_in()
        self.changed(bar=True)
        return True

    def save_office(self):
        """«Guardar no escritório»: this title block for every new project (the suite's folder)."""
        try:
            where = company_file.save(self.company())
        except (OSError, ValueError) as exc:
            self.window.host.message(t("tbe.save_failed", e=str(exc)), warning=True)
            return None
        self.window.host.message(t("tbe.saved", f=where))
        return where

    # ------------------------------------------------------------ on the screen

    def zoom_in(self):
        """The sheet seen near its title block (and round it)."""
        w, h = self.window.sheet.size()
        bw, bh = sheets_model.drawn_size(self.items)
        bw, bh = min(max(bw, 80.0), w - 2 * sheets_model.MARGIN), min(max(bh, 40.0), h - 2 * sheets_model.MARGIN)
        pad = 20.0
        left, top = w - sheets_model.MARGIN - bw - pad, h - sheets_model.MARGIN - bh - pad
        self.window.canvas.zoom_to(left, top, bw + pad + sheets_model.MARGIN + 4, bh + pad + sheets_model.MARGIN + 4)

    def paint(self, painter, s, size, texts):
        """Over the sheet painted (painter at the paper's corner, s px a mm): the veil, the grid, the drawing — its
        empty fields by their names —, what is picked, what is being drawn, the snap."""
        w, h = size
        cx, cy = w - sheets_model.MARGIN, h - sheets_model.MARGIN
        painter.fillRect(QtCore.QRectF(0, 0, w * s, h * s), VEIL)
        bw, bh = sheets_model.drawn_size(self.items)
        if GRID_SHOWN * s >= 7:
            gw = min(max(bw, 80.0) + 40.0, w - 2 * sheets_model.MARGIN)
            gh = min(max(bh, 40.0) + 40.0, h - 2 * sheets_model.MARGIN)
            painter.setPen(QtGui.QPen(GRID_COLOUR, 1.0))
            lines = [QtCore.QLineF((cx - i * GRID_SHOWN) * s, (cy - gh) * s, (cx - i * GRID_SHOWN) * s, cy * s)
                     for i in range(int(gw // GRID_SHOWN) + 1)]
            lines += [QtCore.QLineF((cx - gw) * s, (cy - j * GRID_SHOWN) * s, cx * s, (cy - j * GRID_SHOWN) * s)
                      for j in range(int(gh // GRID_SHOWN) + 1)]
            painter.drawLines(lines)
        pen = QtGui.QPen(QtGui.QColor("#2b2f36"), max(0.35 * s, 1.0))       # (the border, over the veil)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        m = sheets_model.MARGIN
        painter.drawRect(QtCore.QRectF(m * s, m * s, (w - 2 * m) * s, (h - 2 * m) * s))
        if bw and bh:                                    # (what it takes from the views)
            painter.setPen(QtGui.QPen(QtGui.QColor(31, 116, 209, 120), 1.0, QtCore.Qt.PenStyle.DashLine))
            painter.drawRect(QtCore.QRectF((cx - bw) * s - 3, (cy - bh) * s - 3, bw * s + 3, bh * s + 3))
            self._label(painter, QtCore.QPointF((cx - bw) * s - 3, (cy - bh) * s - 8),
                        t("tbe.size_label", w=_mm(bw), h=_mm(bh)), BLUE)
        pdf.paint_drawn(painter, s, cx, cy, self.items, texts, placeholders=True)

        def at(p):
            return QtCore.QPointF((cx + p[0]) * s, (cy + p[1]) * s)
        for k in self.picked:                            # what is picked: blue, its grips
            item = self.items[k]
            painter.setPen(QtGui.QPen(BLUE, 2.0))
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            if item["kind"] == "line":
                painter.drawLine(at(item["pts"][0]), at(item["pts"][1]))
            else:
                x0, y0, x1, y1 = _bounds(item)
                painter.drawRect(QtCore.QRectF(at((x0, y0)), at((x1, y1))).adjusted(-2, -2, 2, 2))
            painter.setBrush(QtGui.QColor("#ffffff"))
            for q in item["pts"]:
                c = at(q)
                painter.drawRect(QtCore.QRectF(c.x() - 4, c.y() - 4, 8, 8))
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        if self.start is not None and self.mouse is not None:      # what is being drawn
            painter.setPen(QtGui.QPen(BLUE, 1.5, QtCore.Qt.PenStyle.DashLine))
            a, b = self.start, self.mouse
            if self.tool == "line":
                painter.drawLine(at(a), at(b))
                text = _mm(math.hypot(b[0] - a[0], b[1] - a[1]))
            else:
                painter.drawRect(QtCore.QRectF(at(a), at(b)).normalized())
                text = t("tbe.size_label", w=_mm(abs(b[0] - a[0])), h=_mm(abs(b[1] - a[1])))
            self._label(painter, at(b) + QtCore.QPointF(12, -10), text, BLUE)
        if self.box is not None:                         # a window picking
            a, b = self.box
            crossing = b[0] < a[0]
            painter.setPen(QtGui.QPen(BLUE, 1.0, QtCore.Qt.PenStyle.DashLine if crossing
                                      else QtCore.Qt.PenStyle.SolidLine))
            painter.setBrush(QtGui.QColor(31, 116, 209, 30))
            painter.drawRect(QtCore.QRectF(at(a), at(b)).normalized())
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        drawing = self.tool != "select" or (self.grab is not None)
        if drawing and self.mouse is not None and self.snapped_to is not None:
            c = at(self.mouse)
            painter.setPen(QtGui.QPen(MAGENTA, 1.2, QtCore.Qt.PenStyle.DashLine))
            for origin, _end in self.guides:
                painter.drawLine(at(origin), c)
            painter.setPen(QtGui.QPen(MAGENTA, 2.0))
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            if self.snapped_to == "end":
                painter.drawRect(QtCore.QRectF(c.x() - 5, c.y() - 5, 10, 10))
            elif self.snapped_to == "mid":
                painter.drawPolygon(QtGui.QPolygonF([c + QtCore.QPointF(0, -6), c + QtCore.QPointF(6, 5),
                                                     c + QtCore.QPointF(-6, 5)]))
            elif self.snapped_to in ("align", "ortho"):
                painter.drawLine(c + QtCore.QPointF(-5, -5), c + QtCore.QPointF(5, 5))
                painter.drawLine(c + QtCore.QPointF(-5, 5), c + QtCore.QPointF(5, -5))

    @staticmethod
    def _label(painter, where, text, colour):
        font = QtGui.QFont("Segoe UI")
        font.setPixelSize(11)
        painter.setFont(font)
        metrics = QtGui.QFontMetrics(font)
        box = QtCore.QRectF(where.x(), where.y() - metrics.ascent() - 2, metrics.horizontalAdvance(text) + 8,
                            metrics.height() + 3)
        painter.fillRect(box, QtGui.QColor(255, 255, 255, 220))
        painter.setPen(colour)
        painter.drawText(box, QtCore.Qt.AlignmentFlag.AlignCenter, text)


def _mm(value):
    return "{:.1f}".format(value).replace(".", ",") + " mm"
