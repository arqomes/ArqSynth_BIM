"""(0.307) The Caixilho Studio — the door and window editor as the owner's prototype draws it (2026-10-29): a dark window
with the openings being worked on as tabs (J01, P01…; + starts one from a ready-made layout, Duplicar copies one);
the opening at a scale on a grid — the mullions and transoms dragged in from the dashed strips above and to its left,
moved by their amber grips (or the arrow keys: 10 mm, Shift 100), taken out with ×, its right edge, its foot and its
corner dragged; its sizes in chains under it and beside it, typed with sums ("2400/3"), «EQ» on columns as wide as
another —, seen from outside or from inside; «Travessas ligadas» (the transoms at one height go together) and «Igualar
colunas»; a click on a panel: a card with its way of opening, its fill, split it, copy it along its row. Under it the
opening's kind, reference, system, the colour of its profiles, its frame and its sill, and what it is: its size, how
much is glass, how much opens, its IFC class; «Inserir no modelo» keeps them all as types and places the one shown.

The model and what is done to it are core/caixilho; this draws it and passes on the clicks."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import caixilho as cx
from ..core import joinery as core_joinery
from ..i18n import lang, t
from . import theme

# (0.308) The studio's colours follow the program's theme: the light one — the ribbon's whites and greys, its dark
# blue header, its blue —; the owner's prototype's dark one (0.338: both in ui/theme, the program's).
THEMES = theme.THEMES
THEME = theme.NAME
C = dict(THEMES.get(THEME) or theme.C)    # (0.540: a study palette in use — «revit», «bege»… — its own colours)
BG, BAR, LINE, CANVAS, GRID = C["window"], C["bar"], C["line"], C["canvas"], C["grid"]
TEXT, MUTED, CARD, EDGE, EDGE_2 = C["text"], C["muted"], C["card"], C["edge"], C["edge_2"]
ACCENT, ACCENT_STRONG, SELECT = C["accent"], C["accent_strong"], C["select"]


def use_theme(name=None):
    """(0.339) The studio's colours those of a theme — the program's in use (the dark one: the owner's prototype's,
    as it was drawn); the studio takes them each time it opens."""
    global THEME, BG, BAR, LINE, CANVAS, GRID, TEXT, MUTED, CARD, EDGE, EDGE_2, ACCENT, ACCENT_STRONG, SELECT
    THEME = name or theme.NAME
    C.clear()
    C.update(theme.theme_of(THEME))                 # (0.374: also the study's palettes)
    BG, BAR, LINE, CANVAS, GRID = C["window"], C["bar"], C["line"], C["canvas"], C["grid"]
    TEXT, MUTED, CARD, EDGE, EDGE_2 = C["text"], C["muted"], C["card"], C["edge"], C["edge_2"]
    ACCENT, ACCENT_STRONG, SELECT = C["accent"], C["accent_strong"], C["select"]
SANS = ["IBM Plex Sans", "Segoe UI", "Noto Sans", "DejaVu Sans", "Sans Serif"]
MONO = ["IBM Plex Mono", "Cascadia Mono", "Consolas", "DejaVu Sans Mono", "Monospace"]

# the fills as the prototype paints them: (fill, swatch, ink)
FILL_LOOK = {"glass": ("glass", "#10314d"), "frosted": ("#d6e2eb", "#23384a"), "panel": ("#6c7177", "#eef1f4"),
             "wood": ("wood", "#fff6ea"), "louvre": ("louvre", "#f1f4f7")}
SNAP_PX = 7                     # px: a mullion or transom this near the middle of its two panels goes on it


def _font(families, px, weight=QtGui.QFont.Weight.Normal):
    f = QtGui.QFont()
    f.setFamilies(families)
    f.setPixelSize(px)
    f.setWeight(weight)
    return f


def _drop(widget):
    """A widget taken away now (hidden, out of its parent), deleted when Qt gets round to it."""
    widget.hide()
    widget.setParent(None)
    widget.deleteLater()


def _r10(v):
    return int(round(v / cx.STEP)) * cx.STEP


def _mm(v):
    return str(int(round(v)))


def _m2(v):
    return "{:.2f} m²".format(v).replace(".", ",")


def _brush(look, rect):
    """A fill's brush over `rect`: the glass's gradient, the wood's grain, the louvres' slats, or a colour."""
    if look == "glass":
        g = QtGui.QLinearGradient(rect.topLeft(), rect.bottomRight())
        g.setColorAt(0.0, QtGui.QColor(160, 205, 238, 158))
        g.setColorAt(1.0, QtGui.QColor(108, 156, 204, 107))
        return QtGui.QBrush(g)
    if look in ("wood", "louvre"):
        pm = QtGui.QPixmap(10, 10) if look == "wood" else QtGui.QPixmap(9, 9)
        p = QtGui.QPainter(pm)
        if look == "wood":
            p.fillRect(0, 0, 7, 10, QtGui.QColor("#97663b"))
            p.fillRect(7, 0, 3, 10, QtGui.QColor("#a8774a"))
        else:
            p.fillRect(0, 0, 9, 6, QtGui.QColor("#7c848e"))
            p.fillRect(0, 6, 9, 3, QtGui.QColor("#555c65"))
        p.end()
        return QtGui.QBrush(pm)
    return QtGui.QBrush(QtGui.QColor(look))


def _points(text, rect, mirror=False):
    """A sign's points ("x,y x,y…" in 0..100) in `rect` (5 % in from its sides)."""
    out = []
    for pair in text.split():
        x, y = (float(v) for v in pair.split(","))
        if mirror:
            x = 100.0 - x
        out.append(QtCore.QPointF(rect.left() + rect.width() * (0.05 + 0.9 * x / 100.0),
                                  rect.top() + rect.height() * (0.05 + 0.9 * y / 100.0)))
    return out


def draw_sign(p, op, rect, ink, mirror=False, width=1.3):
    """How a panel opens, as the prototype draws it (its lines meeting at its hinges)."""
    a, b, c = cx.SIGNS.get(op, ("", "", ""))
    for text, dashed in ((a, False), (b, True), (c, False)):
        if not text:
            continue
        pen = QtGui.QPen(QtGui.QColor(ink), width)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        if dashed:
            pen.setDashPattern([4, 3])
        p.setPen(pen)
        p.drawPolyline(_points(text, rect, mirror))


def op_label(op_key, kind, short=False):
    key = "caixilho.{}.{}{}".format("door" if kind == "door" else "win", op_key, ".s" if short else "")
    return t(key)


# ------------------------------------------------------------ the card of a panel

class PanelCard(QtWidgets.QFrame):
    """The card over the panel clicked: its way of opening (a grid of signs), its fill (swatches), split it, copy it
    along its row."""

    def __init__(self, studio):
        super().__init__(studio.canvas)
        self.studio = studio
        self.setObjectName("card")
        self.setFixedWidth(276)
        self.setStyleSheet(
            "#card { background: %s; border: 1px solid %s; border-radius: 14px; }"
            "QLabel { color: %s; background: transparent; }"
            "QPushButton { height: 32px; border: 1px solid %s; border-radius: 8px; background: %s; color: %s;"
            " font-size: 12px; }"
            "QPushButton:hover { background: %s; }" % (CARD, EDGE_2, TEXT, EDGE_2, C["button"], TEXT, C["button_hover"]))
        box = QtWidgets.QVBoxLayout(self)
        box.setContentsMargins(12, 12, 12, 12)
        box.setSpacing(10)
        head = QtWidgets.QHBoxLayout()
        self.title = QtWidgets.QLabel()
        self.title.setFont(_font(SANS, 12, QtGui.QFont.Weight.DemiBold))
        self.dims = QtWidgets.QLabel()
        self.dims.setFont(_font(MONO, 11))
        self.dims.setStyleSheet("color: %s;" % ACCENT)
        close = QtWidgets.QToolButton()
        close.setText("×")
        close.setStyleSheet("QToolButton { border: 0; color: %s; font-size: 15px; }" % MUTED)
        close.clicked.connect(lambda: studio.select(None))
        head.addWidget(self.title)
        head.addWidget(self.dims)
        head.addStretch(1)
        head.addWidget(close)
        box.addLayout(head)
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(6)
        box.addLayout(self.grid)
        swatches = QtWidgets.QHBoxLayout()
        swatches.setSpacing(8)
        self.fill_buttons = {}
        for fill in cx.FILLS:
            b = QtWidgets.QToolButton()
            b.setObjectName("fill_" + fill)
            b.setFixedSize(34, 34)
            b.setToolTip(t("caixilho.fill." + fill))
            b.clicked.connect(lambda _=False, f=fill: studio.set_fill(f))
            swatches.addWidget(b)
            self.fill_buttons[fill] = b
        self.fill_name = QtWidgets.QLabel()
        self.fill_name.setStyleSheet("color: %s; font-size: 11px;" % MUTED)
        swatches.addWidget(self.fill_name)
        swatches.addStretch(1)
        box.addLayout(swatches)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(6)
        for text, slot in ((t("caixilho.split_v"), studio.split_v), (t("caixilho.split_h"), studio.split_h),
                           (t("caixilho.copy_row"), studio.copy_row)):
            b = QtWidgets.QPushButton(text)
            b.clicked.connect(slot)
            row.addWidget(b)
        box.addLayout(row)
        self.op_buttons = {}

    def show_for(self, op, c, r, mirror):
        panel = op.cols[c].panels[r]
        self.title.setText(op_label(panel.op, op.kind))
        self.dims.setText("{} × {}".format(op.cols[c].w, panel.h))
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w is not None:
                _drop(w)
        self.op_buttons = {}
        for k, key in enumerate(cx.ops_for(op, c, r)):
            on = key == panel.op
            b = QtWidgets.QToolButton()
            b.setObjectName("op_" + key)
            b.setFixedSize(58, 46)
            b.setToolTip(op_label(key, op.kind))
            b.setText(op_label(key, op.kind, short=True))
            b.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            b.setIcon(self._sign_icon(key, C["select_ink"] if on else C["off_text"], mirror))
            b.setIconSize(QtCore.QSize(22, 22))
            b.setStyleSheet("QToolButton { border: 1px solid %s; border-radius: 9px; background: %s; color: %s;"
                            " font-size: 9px; padding: 2px; }"
                            % ((C["select_border"], C["select_soft"], C["select_ink"]) if on
                               else (EDGE, C["button"], C["off_text"])))
            b.clicked.connect(lambda _=False, o=key: self.studio.set_op(o))
            self.grid.addWidget(b, k // 4, k % 4)
            self.op_buttons[key] = b
        for fill, b in self.fill_buttons.items():
            look, _ink = FILL_LOOK[fill]
            pm = QtGui.QPixmap(30, 30)
            pm.fill(QtCore.Qt.GlobalColor.transparent)
            p = QtGui.QPainter(pm)
            p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.setBrush(_brush(look, QtCore.QRectF(0, 0, 30, 30)))
            p.drawEllipse(QtCore.QRectF(0, 0, 30, 30))
            p.end()
            b.setIcon(QtGui.QIcon(pm))
            b.setIconSize(QtCore.QSize(30, 30))
            b.setStyleSheet("QToolButton { border: 2px solid %s; border-radius: 17px; background: transparent; }"
                            % (SELECT if fill == panel.fill else EDGE_2))
        self.fill_name.setText(t("caixilho.fill." + panel.fill))
        self.adjustSize()

    @staticmethod
    def _sign_icon(key, ink, mirror):
        pm = QtGui.QPixmap(22, 22)
        pm.fill(QtCore.Qt.GlobalColor.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        colour = QtGui.QColor(ink)
        colour.setAlpha(128)
        p.setPen(QtGui.QPen(colour, 1.2))
        p.drawRect(QtCore.QRectF(0.5, 0.5, 21, 21))
        draw_sign(p, key, QtCore.QRectF(-0.6, -0.6, 23.2, 23.2), ink, mirror, 1.5)
        p.end()
        return QtGui.QIcon(pm)


# ------------------------------------------------------------ the drawing

class StudioCanvas(QtWidgets.QWidget):
    """The opening at a scale on a grid, its grips, its sizes; what is clicked and dragged goes to the studio."""

    def __init__(self, studio):
        super().__init__(studio)
        self.studio = studio
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.setMinimumSize(900, 520)
        self.drag = None              # (what, its start (x, y), the opening as it was)
        self.ghost = None             # ("col" | "row", x mm, y mm) while a new mullion / transom is dragged in
        self.hover = None
        self.inputs = {}              # size key -> QLineEdit
        self.merges = []              # the × buttons

    # ---------------- where things are

    def frame(self):
        """(s px per mm, L, T, sw, sh) of the opening in the canvas."""
        op = self.studio.op
        pl, pt = 150.0, 84.0
        aw, ah = max(self.width() - 300.0, 200.0), max(self.height() - 200.0, 150.0)
        s = min(aw / op.W, ah / op.H)
        sw, sh = op.W * s, op.H * s
        return s, pl + (aw - sw) / 2, pt + (ah - sh) / 2, sw, sh

    def dx(self, x0, w):
        op = self.studio.op
        return op.W - x0 - w if self.studio.view == "interior" else x0

    def panel_rects(self):
        """[(c, r, QRectF)] of the panels in the canvas, the frame's and the bars' widths left round them."""
        op = self.studio.op
        s, L, T, _sw, _sh = self.frame()
        f, pf = max(3.0, op.aro * s), max(3.0, op.aro * 0.8 * s)
        cw = cx.cum(cx.widths(op))
        out = []
        for c, col in enumerate(op.cols):
            x0 = self.dx(cw[c], col.w)
            left = L + x0 * s + (f if x0 <= 0.5 else pf / 2)
            right = L + (x0 + col.w) * s - (f if x0 + col.w >= op.W - 0.5 else pf / 2)
            y = 0
            for r, panel in enumerate(col.panels):
                top = T + y * s + (f if r == 0 else pf / 2)
                bottom = T + (y + panel.h) * s - (f if r == len(col.panels) - 1 else pf / 2)
                out.append((c, r, QtCore.QRectF(left, top, max(2.0, right - left), max(2.0, bottom - top))))
                y += panel.h
        return out

    def mullions(self):
        """[(i, x px)] of the mullions (after column i)."""
        op = self.studio.op
        s, L, _T, _sw, _sh = self.frame()
        cw = cx.cum(cx.widths(op))
        return [(i, L + (op.W - cw[i + 1] if self.studio.view == "interior" else cw[i + 1]) * s)
                for i in range(len(op.cols) - 1)]

    def transoms(self):
        """[(c, b, x0 px, x1 px, y px)] of the transoms (under panel b of column c)."""
        op = self.studio.op
        s, L, T, _sw, _sh = self.frame()
        cw = cx.cum(cx.widths(op))
        out = []
        for c, col in enumerate(op.cols):
            cy = cx.cum(cx.heights(col))
            x0 = L + self.dx(cw[c], col.w) * s
            for b in range(len(col.panels) - 1):
                out.append((c, b, x0, x0 + col.w * s, T + cy[b + 1] * s))
        return out

    def hit(self, pos):
        """What is under the mouse: ("corner",), ("W",), ("H",), ("col", i), ("row", c, b), ("newcol",), ("newrow",),
        ("panel", c, r), or None."""
        s, L, T, sw, sh = self.frame()
        x, y = pos.x(), pos.y()
        if abs(x - (L + sw)) <= 8 and abs(y - (T + sh)) <= 8:
            return ("corner",)
        if L <= x <= L + sw and T - 34 <= y <= T - 12:
            return ("newcol",)
        if T <= y <= T + sh and L - 34 <= x <= L - 12:
            return ("newrow",)
        for i, mx in self.mullions():
            if abs(x - mx) <= 8 and T <= y <= T + sh:
                return ("col", i)
        for c, b, x0, x1, ty in self.transoms():
            if abs(y - ty) <= 8 and x0 <= x <= x1:
                return ("row", c, b)
        if L + sw - 6 <= x <= L + sw + 6 and T <= y <= T + sh:
            return ("W",)
        if T + sh - 6 <= y <= T + sh + 6 and L <= x <= L + sw:
            return ("H",)
        for c, r, rect in self.panel_rects():
            if rect.contains(pos):
                return ("panel", c, r)
        return None

    def to_mm(self, pos):
        """(x mm from the opening's left — as it is, not as seen —, y mm from its top) of a point, on the 10 mm grid."""
        op = self.studio.op
        s, L, T, _sw, _sh = self.frame()
        x = (pos.x() - L) / s
        if self.studio.view == "interior":
            x = op.W - x
        return min(max(_r10(x), 0), op.W), min(max(_r10((pos.y() - T) / s), 0), op.H)

    # ---------------- the mouse and the keys

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.MouseButton.LeftButton:
            return
        what = self.hit(event.position())
        if what is None:
            self.studio.select(None)
            self.studio.handle = None
            self.update()
            return
        if what[0] == "panel":
            self.studio.select((what[1], what[2]))
            return
        self.studio.handle = what if what[0] in ("col", "row") else None
        self.drag = (what, event.position(), cx.clone(self.studio.op))
        if what[0] in ("newcol", "newrow"):
            self._ghost(what[0], event.position())
        self.setFocus()

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self.drag is None:
            what = self.hit(pos)
            shape = {"corner": QtCore.Qt.CursorShape.SizeFDiagCursor, "W": QtCore.Qt.CursorShape.SizeHorCursor,
                     "H": QtCore.Qt.CursorShape.SizeVerCursor, "col": QtCore.Qt.CursorShape.SizeHorCursor,
                     "row": QtCore.Qt.CursorShape.SizeVerCursor, "newcol": QtCore.Qt.CursorShape.DragCopyCursor,
                     "newrow": QtCore.Qt.CursorShape.DragCopyCursor, "panel": QtCore.Qt.CursorShape.PointingHandCursor}
            self.setCursor(shape.get(what[0], QtCore.Qt.CursorShape.ArrowCursor) if what else
                           QtCore.Qt.CursorShape.ArrowCursor)
            return
        what, start, snap = self.drag
        s = self.frame()[0]
        dx, dy = (pos.x() - start.x()) / s, (pos.y() - start.y()) / s
        mirror = self.studio.view == "interior"
        op = cx.clone(snap)
        if what[0] == "col":
            i = what[1]
            cx.move_mullion(op, i, _r10(snap.cols[i].w + (-dx if mirror else dx)), SNAP_PX / s)
        elif what[0] == "row":
            c, b = what[1], what[2]
            old = cx.cum(cx.heights(snap.cols[c]))[b + 1]
            cx.move_boundary(op, c, old, _r10(old + dy), self.studio.linked, SNAP_PX / s)
        elif what[0] in ("W", "H", "corner"):
            if what[0] != "H":
                cx.resize(op, W=_r10(snap.W + dx), from_left=mirror)
            if what[0] != "W":
                cx.resize(op, H=_r10(snap.H + dy))
        else:
            self._ghost(what[0], pos)
            return
        self.studio.change(op, keep_selection=True)

    def mouseReleaseEvent(self, event):
        if self.drag is None:
            return
        what = self.drag[0]
        self.drag = None
        if what[0] in ("newcol", "newrow") and self.ghost is not None:
            kind, x, y = self.ghost
            self.ghost = None
            op = cx.clone(self.studio.op)
            done = cx.insert_col(op, x) if kind == "col" else \
                cx.insert_row(op, y, None if self.studio.linked else x)
            if done:
                self.studio.change(op)
            self.update()

    def _ghost(self, what, pos):
        x, y = self.to_mm(pos)
        self.ghost = ("col" if what == "newcol" else "row", x, y)
        self.update()

    def keyPressEvent(self, event):
        moves = {QtCore.Qt.Key.Key_Left: (-1, 0), QtCore.Qt.Key.Key_Right: (1, 0), QtCore.Qt.Key.Key_Up: (0, -1),
                 QtCore.Qt.Key.Key_Down: (0, 1)}
        handle = self.studio.handle
        if event.key() in moves and handle is not None:
            step = 100 if event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier else cx.STEP
            vx, vy = moves[event.key()]
            op = cx.clone(self.studio.op)
            if handle[0] == "col" and vx:
                i = handle[1]
                cx.move_mullion(op, i, op.cols[i].w + vx * step * (-1 if self.studio.view == "interior" else 1))
            elif handle[0] == "row" and vy:
                c, b = handle[1], handle[2]
                old = cx.cum(cx.heights(op.cols[c]))[b + 1]
                cx.move_boundary(op, c, old, old + vy * step, self.studio.linked)
            else:
                return
            self.studio.change(op, keep_selection=True)
            return
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.studio.select(None)
            self.studio.handle = None
            self.update()
            return
        super().keyPressEvent(event)

    # ---------------- painting

    def paintEvent(self, _event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QtGui.QColor(CANVAS))
        p.setPen(QtGui.QPen(QtGui.QColor(GRID), 1))
        for x in range(0, self.width(), 20):
            p.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 20):
            p.drawLine(0, y, self.width(), y)
        studio, op = self.studio, self.studio.op
        s, L, T, sw, sh = self.frame()
        mirror = studio.view == "interior"
        # the strips to drag a mullion and a transom in from
        p.setFont(_font(SANS, 11))
        pen = QtGui.QPen(QtGui.QColor(C["strip"]), 1)
        pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        for rect, text, vertical in ((QtCore.QRectF(L, T - 34, sw, 22), t("caixilho.new_mullion"), False),
                                     (QtCore.QRectF(L - 34, T, 22, sh), t("caixilho.new_transom"), True)):
            p.setPen(pen)
            p.setBrush(QtGui.QColor(*C["strip_fill"]))
            p.drawRoundedRect(rect, 6, 6)
            p.setPen(QtGui.QColor(MUTED))
            if vertical:
                p.save()
                p.translate(rect.center())
                p.rotate(-90)
                p.drawText(QtCore.QRectF(-rect.height() / 2, -rect.width() / 2, rect.height(), rect.width()),
                           QtCore.Qt.AlignmentFlag.AlignCenter, text)
                p.restore()
            else:
                p.drawText(rect, QtCore.Qt.AlignmentFlag.AlignCenter, text)
        # the opening: its frame (in its profiles' colour), a shadow under it
        for k in range(6, 0, -1):
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.setBrush(QtGui.QColor(*C["shadow"], 14))
            p.drawRoundedRect(QtCore.QRectF(L - k, T + 22 - k * 1.5, sw + 2 * k, sh + 2 * k), 4, 4)
        p.setPen(QtGui.QPen(QtGui.QColor(*C["outline"]), 1))
        p.setBrush(QtGui.QColor(studio.frame_colour()))
        p.drawRect(QtCore.QRectF(L, T, sw, sh))
        sel = studio.selected
        for c, r, rect in self.panel_rects():
            panel = op.cols[c].panels[r]
            look, ink = FILL_LOOK.get(panel.fill, FILL_LOOK["glass"])
            p.setPen(QtGui.QPen(QtGui.QColor(*C["panel_edge"]), 1))
            p.setBrush(_brush(look, rect))
            p.drawRect(rect)
            draw_sign(p, panel.op, rect, ink, mirror)
            if panel.op == "fixed":
                p.setFont(_font(MONO, 10))
                colour = QtGui.QColor(ink)
                colour.setAlpha(190)
                p.setPen(colour)
                p.drawText(QtCore.QPointF(rect.left() + 6, rect.bottom() - 5), "F")
            if sel == (c, r):
                p.setPen(QtGui.QPen(QtGui.QColor(SELECT), 2))
                p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                p.drawRect(rect.adjusted(1, 1, -1, -1))
                p.drawRect(rect.adjusted(-2, -2, 2, 2))
        # the grips
        p.setPen(QtGui.QPen(QtGui.QColor(*C["grip_outline"]), 2))
        p.setBrush(QtGui.QColor(ACCENT))
        for i, mx in self.mullions():
            p.drawRoundedRect(QtCore.QRectF(mx - 2, T + sh / 2 - 18, 4, 36), 2, 2)
            if studio.handle == ("col", i):
                p.save()
                p.setPen(QtGui.QPen(QtGui.QColor(ACCENT), 1, QtCore.Qt.PenStyle.DotLine))
                p.drawLine(QtCore.QPointF(mx, T), QtCore.QPointF(mx, T + sh))
                p.restore()
        for c, b, x0, x1, y in self.transoms():
            p.drawRoundedRect(QtCore.QRectF((x0 + x1) / 2 - 18, y - 2, 36, 4), 2, 2)
        p.setPen(QtGui.QPen(QtGui.QColor(ACCENT), 2))
        p.setBrush(QtGui.QColor(BG))
        p.drawRoundedRect(QtCore.QRectF(L + sw - 8, T + sh - 8, 16, 16), 3, 3)
        # a mullion or transom being dragged in
        if self.ghost is not None:
            kind, gx, gy = self.ghost
            pen = QtGui.QPen(QtGui.QColor(SELECT), 2)
            pen.setStyle(QtCore.Qt.PenStyle.DashLine)
            p.setPen(pen)
            if kind == "col":
                x = L + (op.W - gx if mirror else gx) * s
                p.drawLine(QtCore.QPointF(x, T), QtCore.QPointF(x, T + sh))
                tag, at = t("caixilho.ghost_col", a=gx, b=op.W - gx), QtCore.QPointF(x + 8, T + 8)
            else:
                y = T + gy * s
                p.drawLine(QtCore.QPointF(L, y), QtCore.QPointF(L + sw, y))
                tag = t("caixilho.ghost_row", h=op.H - gy) + ("" if studio.linked else t("caixilho.ghost_one"))
                at = QtCore.QPointF(L + 8, y + 8)
            p.setFont(_font(MONO, 11, QtGui.QFont.Weight.DemiBold))
            box = QtCore.QRectF(at, QtCore.QSizeF(p.fontMetrics().horizontalAdvance(tag) + 16, 22))
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.setBrush(QtGui.QColor(SELECT))
            p.drawRoundedRect(box, 6, 6)
            p.setPen(QtGui.QColor(C["select_text"]))
            p.drawText(box, QtCore.Qt.AlignmentFlag.AlignCenter, tag)
        self._paint_dims(p, s, L, T, sw, sh)
        p.end()

    def _dim(self, p, a, b, colour, horizontal, ext_from):
        """A dimension line from a to b (its ticks at 45°) and its extension lines back to ext_from."""
        ext = QtGui.QPen(QtGui.QColor(*C["ext"]), 1, QtCore.Qt.PenStyle.DotLine)
        p.setPen(ext)
        if horizontal:
            for x in (a.x(), b.x()):
                p.drawLine(QtCore.QPointF(x, ext_from), QtCore.QPointF(x, a.y()))
        else:
            for y in (a.y(), b.y()):
                p.drawLine(QtCore.QPointF(ext_from, y), QtCore.QPointF(a.x(), y))
        p.setPen(QtGui.QPen(QtGui.QColor(colour), 1))
        p.drawLine(a, b)
        for q in (a, b):
            p.drawLine(QtCore.QPointF(q.x() - 4, q.y() + 4), QtCore.QPointF(q.x() + 4, q.y() - 4))

    @staticmethod
    def _eq(p, at, kept):
        """«EQ» by a size as large as another of its chain; bold, in the stronger blue, when its parameter keeps it so
        (0.309)."""
        p.setFont(_font(MONO, 9, QtGui.QFont.Weight.Bold if kept else QtGui.QFont.Weight.Normal))
        p.setPen(QtGui.QColor(ACCENT_STRONG if kept else ACCENT))
        p.drawText(at, "EQ")

    def _paint_dims(self, p, s, L, T, sw, sh):
        studio, op = self.studio, self.studio.op
        cw = cx.cum(cx.widths(op))
        y_c, y_w = T + sh + 34, T + sh + 74
        for c, col in enumerate(op.cols):
            x = L + self.dx(cw[c], col.w) * s
            self._dim(p, QtCore.QPointF(x, y_c), QtCore.QPointF(x + col.w * s, y_c), ACCENT, True, T + sh + 4)
            if len(op.cols) > 1 and (op.eq_cols or any(o.w == col.w for k, o in enumerate(op.cols) if k != c)):
                self._eq(p, QtCore.QPointF(x + col.w * s / 2 + 26, y_c - 9), op.eq_cols)
        self._dim(p, QtCore.QPointF(L, y_w), QtCore.QPointF(L + sw, y_w), ACCENT_STRONG, True, y_c + 4)
        x_h = L - 70
        self._dim(p, QtCore.QPointF(x_h, T), QtCore.QPointF(x_h, T + sh), ACCENT_STRONG, False, L - 40)
        c = studio.dim_column()
        cy = cx.cum(cx.heights(op.cols[c]))
        x_r = L + sw + 34
        panels = op.cols[c].panels
        for r, panel in enumerate(panels):
            self._dim(p, QtCore.QPointF(x_r, T + cy[r] * s), QtCore.QPointF(x_r, T + cy[r + 1] * s), ACCENT, False,
                      L + sw + 4)
            if len(panels) > 1 and (op.eq_rows or any(o.h == panel.h for k, o in enumerate(panels) if k != r)):
                past = QtGui.QFontMetrics(_font(MONO, 13)).horizontalAdvance(_mm(panel.h)) + 18   # (after its size)
                self._eq(p, QtCore.QPointF(x_r + 8 + past, T + (cy[r] + panel.h / 2) * s + 4), op.eq_rows)
        p.setFont(_font(SANS, 11))
        p.setPen(QtGui.QColor(MUTED))
        p.drawText(QtCore.QPointF(x_r - 4, T - 18), t("caixilho.column", n=c + 1))
        p.setFont(_font(SANS, 11))
        p.setPen(QtGui.QColor(C["hint"]))
        p.drawText(QtCore.QPointF(16, self.height() - 12), t("caixilho.hint"))

    # ---------------- the sizes typed, the × buttons (widgets over the drawing)

    def place_widgets(self):
        """The sizes' fields and the × buttons where the drawing has them now."""
        studio, op = self.studio, self.studio.op
        s, L, T, sw, sh = self.frame()
        wanted = {}
        cw = cx.cum(cx.widths(op))
        y_c, y_w = T + sh + 34, T + sh + 74
        for c, col in enumerate(op.cols):
            x = L + self.dx(cw[c], col.w) * s
            wanted["c{}".format(c)] = (col.w, QtCore.QPointF(x + col.w * s / 2 - 32, y_c - 25), ACCENT, False,
                                       QtCore.Qt.AlignmentFlag.AlignCenter, t("caixilho.aria_col", n=c + 1))
        wanted["W"] = (op.W, QtCore.QPointF(L + sw / 2 - 32, y_w - 25), ACCENT_STRONG, True,
                       QtCore.Qt.AlignmentFlag.AlignCenter, t("caixilho.aria_W"))
        wanted["H"] = (op.H, QtCore.QPointF(L - 140, T + sh / 2 - 11), ACCENT_STRONG, True,
                       QtCore.Qt.AlignmentFlag.AlignRight, t("caixilho.aria_H"))
        c = studio.dim_column()
        cy = cx.cum(cx.heights(op.cols[c]))
        for r, panel in enumerate(op.cols[c].panels):
            wanted["r{}_{}".format(c, r)] = (panel.h, QtCore.QPointF(L + sw + 42, T + (cy[r] + panel.h / 2) * s - 11),
                                             ACCENT, False, QtCore.Qt.AlignmentFlag.AlignLeft,
                                             t("caixilho.aria_row", r=r + 1, c=c + 1))
        for key in list(self.inputs):
            if key not in wanted:
                _drop(self.inputs.pop(key))
        for key, (value, at, colour, bold, align, tip) in wanted.items():
            edit = self.inputs.get(key)
            if edit is None:
                edit = QtWidgets.QLineEdit(self)
                edit.setObjectName("dim_" + key)
                edit.setFixedSize(64, 22)
                edit.editingFinished.connect(lambda k=key: studio.typed(k, self.inputs[k].text()))
                self.inputs[key] = edit
            edit.setToolTip(tip)
            edit.setAlignment(align)
            edit.setFont(_font(MONO, 13, QtGui.QFont.Weight.DemiBold if bold else QtGui.QFont.Weight.Medium))
            edit.setStyleSheet("QLineEdit { border: 0; border-bottom: 1px dashed transparent; background: transparent;"
                               " color: %s; } QLineEdit:focus { border-bottom: 1px dashed %s; }" % (colour, colour))
            if not edit.hasFocus():
                edit.setText(_mm(value))
            edit.move(int(at.x()), int(at.y()))
            edit.show()
        for b in self.merges:
            _drop(b)
        self.merges = []
        for i, mx in self.mullions():
            self._merge_button(mx - 12, T + sh / 2 + 26, lambda _=False, k=i: studio.merge_col(k),
                               t("caixilho.remove_mullion"))
        seen = set()
        for c, b, x0, x1, y in self.transoms():
            key = round(cx.cum(cx.heights(op.cols[c]))[b + 1])
            if studio.linked and key in seen:
                continue
            seen.add(key)
            self._merge_button((x0 + x1) / 2 + 26, y - 12, lambda _=False, cc=c, bb=b: studio.merge_row(cc, bb),
                               t("caixilho.remove_transom"))

    def _merge_button(self, x, y, slot, tip):
        b = QtWidgets.QToolButton(self)
        b.setText("×")
        b.setToolTip(tip)
        b.setFixedSize(24, 24)
        b.setStyleSheet("QToolButton { border: 1px solid %s; border-radius: 12px; background: %s; color: %s;"
                        " font-size: 13px; }" % (EDGE_2, CARD, MUTED))
        b.clicked.connect(slot)
        b.move(int(x), int(y))
        b.show()
        self.merges.append(b)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.studio.refresh()


# ------------------------------------------------------------ the window

class CaixilhoStudio(QtWidgets.QDialog):
    """The studio on some openings (core/caixilho.Opening): «Inserir no modelo» (insert=True) or «Guardar» accepts it
    — self.items as they are now, self.active the one shown, self.inserting whether to place it."""

    def __init__(self, parent, items, active=0, insert=True, taken=(), single=False):
        """single: one opening of a type being edited elsewhere — no new ones, no other kind."""
        use_theme()                                 # (0.339: the program's theme, light or dark)
        super().__init__(parent)
        self.setWindowTitle("Caixilho Studio")
        self.items = [cx.clone(it) for it in items] or [cx.default_window()]
        self.originals = [cx.clone(it) for it in self.items]
        self.active = min(max(active, 0), len(self.items) - 1)
        self.taken = set(taken)            # (names of the project's other types: a new one's reference not one)
        self.view, self.linked = "exterior", True
        self.selected, self.handle = None, None
        self.inserting = False
        self.setStyleSheet("QDialog { background: %s; } QLabel { color: %s; }" % (BG, TEXT))
        self.setFont(_font(SANS, 13))
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._header())
        outer.addWidget(self._tabs_bar())
        self.canvas = StudioCanvas(self)
        outer.addWidget(self.canvas, 1)
        self._overlay()
        self.card = PanelCard(self)
        self.card.hide()
        self.toast = QtWidgets.QLabel(self.canvas)
        self.toast.setStyleSheet("QLabel { padding: 9px 14px; border-radius: 10px; background: %s; color: %s;"
                                 " font-size: 12px; font-weight: 600; }" % (SELECT, C["toast_text"]))
        self.toast.hide()
        outer.addWidget(self._footer(insert))
        for w in (self.new_button, self.duplicate_button, self.kinds_box):
            w.setVisible(not single)
        screen = QtWidgets.QApplication.primaryScreen()
        room = screen.availableGeometry() if screen is not None else QtCore.QRect(0, 0, 1280, 860)
        self.resize(min(1280, room.width() - 40), min(860, room.height() - 60))
        self.refresh()

    # ---------------- what it is working on

    @property
    def op(self):
        return self.items[self.active]

    def frame_colour(self):
        op = self.op
        if op.colour in cx.COLOUR_HEX:
            return cx.COLOUR_HEX[op.colour]
        from ..ifc import catalog
        m = catalog.MATERIALS.get(cx.profile_material(op))
        r, g, b = m.color if m is not None else (0.6, 0.62, 0.64)
        return QtGui.QColor(int(r * 255), int(g * 255), int(b * 255)).name()

    def dim_column(self):
        if self.selected is not None:
            return self.selected[0]
        return len(self.op.cols) - 1 if self.view == "interior" else 0

    def change(self, op, keep_selection=False):
        """The opening shown is now `op` (a clone, changed) — (0.309) its columns and its panels kept equal if they are
        to be; a word when that is turned on or off (a mullion or a transom moved by hand turns it off)."""
        before = self.op
        cx.keep_equal(op)
        self.items[self.active] = op
        if not keep_selection or (self.selected is not None and (
                self.selected[0] >= len(op.cols) or self.selected[1] >= len(op.cols[self.selected[0]].panels))):
            self.selected = None
        if self.handle is not None and self.handle[0] == "col" and self.handle[1] >= len(op.cols) - 1:
            self.handle = None
        self.refresh()
        said = [t("caixilho.{}_{}".format(flag, "on" if getattr(op, flag) else "off"))
                for flag in ("eq_cols", "eq_rows") if getattr(op, flag) != getattr(before, flag)]
        if said:
            self.flash(" · ".join(said))

    def edit(self, change):
        """A change of the opening shown: `change(op)` on a clone of it."""
        op = cx.clone(self.op)
        if change(op) is not False:
            self.change(op, keep_selection=True)

    # ---------------- the parts of the window

    def _header(self):
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(40)
        bar.setStyleSheet("background: %s; border-bottom: 1px solid %s;" % (C["header"], C["header"]))
        row = QtWidgets.QHBoxLayout(bar)
        row.setContentsMargins(16, 0, 16, 0)
        row.setSpacing(12)
        from . import icons
        mark = QtWidgets.QLabel()                       # (the brand's own symbol, as the program's header has it)
        mark.setPixmap(icons.app_icon().pixmap(22, 22))
        mark.setStyleSheet("border: 0;")
        row.addWidget(mark)
        brand = QtWidgets.QLabel("ArqSynth BIM")
        brand.setFont(_font(SANS, 13, QtGui.QFont.Weight.DemiBold))
        brand.setStyleSheet("color: %s; border: 0;" % C["header_text"])
        row.addWidget(brand)
        name = QtWidgets.QLabel("Caixilho Studio")
        name.setStyleSheet("color: %s; border: 0;" % C["header_muted"])
        row.addWidget(name)
        row.addStretch(1)
        self.scale = QtWidgets.QLabel()
        self.scale.setFont(_font(MONO, 11))
        self.scale.setStyleSheet("color: %s; border: 0;" % C["header_muted"])
        row.addWidget(self.scale)
        return bar

    def _tabs_bar(self):
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(46)
        bar.setStyleSheet("background: %s; border-bottom: 1px solid %s;" % (BAR, LINE))
        self.tab_row = QtWidgets.QHBoxLayout(bar)
        self.tab_row.setContentsMargins(12, 0, 12, 0)
        self.tab_row.setSpacing(4)
        self.tab_row.setAlignment(QtCore.Qt.AlignmentFlag.AlignBottom)
        self.tab_buttons = []
        self.new_button = QtWidgets.QToolButton()
        self.new_button.setText("+")
        self.new_button.setToolTip(t("caixilho.new"))
        self.new_button.setFixedSize(38, 34)
        self.new_button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.new_button.setStyleSheet("QToolButton { border: 1px dashed %s; border-radius: 8px; background: "
                                      "transparent; color: %s; font-size: 18px; margin-bottom: 4px; }"
                                      "QToolButton::menu-indicator { image: none; width: 0; }" % (C["strip"], TEXT))
        menu = QtWidgets.QMenu(self.new_button)
        menu.setStyleSheet("QMenu { background: %s; border: 1px solid %s; border-radius: 12px; padding: 8px;"
                           " color: %s; } QMenu::item { padding: 10px; border-radius: 8px; }"
                           " QMenu::item:selected { background: %s; }" % (CARD, EDGE_2, TEXT, C["button_hover"]))
        head = menu.addAction(t("caixilho.start_from"))
        head.setEnabled(False)
        for label, make in cx.PRESETS:
            sample = make()
            act = menu.addAction("{}    {}×{}".format(t(label), sample.W, sample.H))
            act.setObjectName(label.split(".")[-1])                # («preset_door_side»…)
            act.triggered.connect(lambda _=False, m=make: self.add_item(m()))
        self.new_button.setMenu(menu)
        self.presets_menu = menu
        self.duplicate_button = QtWidgets.QPushButton(t("caixilho.duplicate"))
        self.duplicate_button.setFixedHeight(34)
        self.duplicate_button.setStyleSheet("QPushButton { border: 1px solid %s; border-radius: 8px; background: "
                                            "transparent; color: %s; font-size: 12px; padding: 0 12px;"
                                            " margin-bottom: 4px; }" % (EDGE, MUTED))
        self.duplicate_button.clicked.connect(self.duplicate)
        self.tab_row.addWidget(self.new_button)
        self.tab_row.addWidget(self.duplicate_button)
        self.tab_row.addStretch(1)
        return bar

    def _overlay(self):
        """The bar over the drawing's top left: the view, the linked transoms, (0.309) the parameters «equal widths»
        and «equal heights» and «all equal» (both on)."""
        box = QtWidgets.QWidget(self.canvas)
        row = QtWidgets.QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        seg = QtWidgets.QFrame()
        seg.setStyleSheet("QFrame { background: %s; border: 1px solid %s; border-radius: 9px; }" % (CARD, EDGE))
        sl = QtWidgets.QHBoxLayout(seg)
        sl.setContentsMargins(3, 3, 3, 3)
        sl.setSpacing(0)
        self.view_buttons = {}
        for key in ("exterior", "interior"):
            b = QtWidgets.QPushButton(t("caixilho.view_" + key))
            b.setObjectName("view_" + key)
            b.setFixedHeight(26)
            b.setFont(_font(SANS, 12))
            b.setMinimumWidth(QtGui.QFontMetrics(b.font()).horizontalAdvance(b.text()) + 28)
            b.clicked.connect(lambda _=False, k=key: self.set_view(k))
            sl.addWidget(b)
            self.view_buttons[key] = b
        row.addWidget(seg)
        self.link_button = QtWidgets.QPushButton(t("caixilho.linked"))
        self.link_button.setObjectName("linked")
        self.link_button.setFixedHeight(32)
        self.link_button.clicked.connect(self.toggle_linked)
        row.addWidget(self.link_button)
        self.eq_buttons = {}
        for flag in ("eq_cols", "eq_rows"):
            b = QtWidgets.QPushButton("○ " + t("caixilho." + flag))
            b.setObjectName(flag)
            b.setFixedHeight(32)
            b.setToolTip(t("caixilho.{}_tip".format(flag)))
            b.clicked.connect(lambda _=False, f=flag: self.toggle_equal(f))
            row.addWidget(b)
            self.eq_buttons[flag] = b
        eq = QtWidgets.QPushButton(t("caixilho.eq_all"))
        eq.setObjectName("eq_all")
        eq.setFixedHeight(32)
        eq.setToolTip(t("caixilho.eq_all_tip"))
        eq.clicked.connect(lambda: self.edit(lambda op: cx.set_equal(op, cols=True, rows=True)))
        row.addWidget(eq)
        for b in (self.link_button, eq):
            b.setStyleSheet(self._toggle_style(False))
        box.move(16, 12)
        box.adjustSize()
        self.overlay = box

    def _footer(self, insert):
        foot = QtWidgets.QWidget()
        foot.setStyleSheet("QWidget#foot { background: %s; border-top: 1px solid %s; }" % (C["footer"], LINE))
        foot.setObjectName("foot")
        foot.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        box = QtWidgets.QVBoxLayout(foot)
        box.setContentsMargins(20, 14, 20, 14)
        box.setSpacing(12)
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(22)

        def field(label, widget):
            col = QtWidgets.QVBoxLayout()
            col.setSpacing(5)
            caption = QtWidgets.QLabel(label.upper())
            caption.setStyleSheet("color: %s; font-size: 10px; letter-spacing: 1px;" % MUTED)
            col.addWidget(caption)
            col.addWidget(widget)
            top.addLayout(col)

        kinds = QtWidgets.QFrame()
        kinds.setStyleSheet("QFrame { background: %s; border: 1px solid %s; border-radius: 9px; }" % (CANVAS, EDGE))
        kl = QtWidgets.QHBoxLayout(kinds)
        kl.setContentsMargins(3, 3, 3, 3)
        kl.setSpacing(0)
        self.kind_buttons = {}
        for key in ("window", "door"):
            b = QtWidgets.QPushButton(t("caixilho.kind_" + key))
            b.setObjectName("kind_" + key)
            b.setFixedHeight(28)
            b.clicked.connect(lambda _=False, k=key: self.edit(lambda op: cx.set_kind(op, k)))
            kl.addWidget(b)
            self.kind_buttons[key] = b
        self.kinds_box = kinds
        field(t("caixilho.kind"), kinds)
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setObjectName("reference")
        self.name_edit.setFixedSize(150, 34)
        self.name_edit.setFont(_font(MONO, 13))
        self.name_edit.setStyleSheet(self._input_style(TEXT))
        self.name_edit.editingFinished.connect(self.rename)
        field(t("caixilho.reference"), self.name_edit)
        systems = QtWidgets.QWidget()
        sy = QtWidgets.QHBoxLayout(systems)
        sy.setContentsMargins(0, 0, 0, 0)
        sy.setSpacing(6)
        self.system_buttons = {}
        for key in cx.SYSTEMS:
            b = QtWidgets.QPushButton(t("caixilho.system." + key))
            b.setObjectName("system_" + key)
            b.setFixedHeight(34)
            b.clicked.connect(lambda _=False, k=key: self.set_system(k))
            sy.addWidget(b)
            self.system_buttons[key] = b
        field(t("caixilho.system"), systems)
        colours = QtWidgets.QWidget()
        co = QtWidgets.QHBoxLayout(colours)
        co.setContentsMargins(0, 2, 0, 2)
        co.setSpacing(8)
        self.colour_buttons = {}
        for key in cx.COLOURS:
            b = QtWidgets.QToolButton()
            b.setObjectName("colour_" + key)
            b.setFixedSize(30, 30)
            b.setToolTip(t("caixilho.colour." + key))
            b.clicked.connect(lambda _=False, k=key: self.set_colour(k))
            co.addWidget(b)
            self.colour_buttons[key] = b
        field(t("caixilho.colour"), colours)
        self.number_edits = {}
        for key in ("aro", "sill"):
            edit = QtWidgets.QLineEdit()
            edit.setObjectName("field_" + key)
            edit.setFixedSize(78, 34)
            edit.setFont(_font(MONO, 13))
            edit.setStyleSheet(self._input_style(ACCENT))
            edit.editingFinished.connect(lambda k=key: self.typed(k, self.number_edits[k].text()))
            self.number_edits[key] = edit
            col = QtWidgets.QVBoxLayout()
            col.setSpacing(5)
            caption = QtWidgets.QLabel(t("caixilho." + key).upper())
            caption.setStyleSheet("color: %s; font-size: 10px; letter-spacing: 1px;" % MUTED)
            col.addWidget(caption)
            col.addWidget(edit)
            top.addLayout(col)
            if key == "sill":
                self.sill_caption = caption
        top.addStretch(1)
        more = QtWidgets.QPushButton(t("caixilho.more"))
        more.setObjectName("more")
        more.setFixedHeight(34)
        more.setStyleSheet("QPushButton { padding: 0 12px; background: transparent; border: 1px solid %s;"
                           " border-radius: 8px; color: %s; font-size: 12px; }" % (EDGE, MUTED))
        more.clicked.connect(self.more_options)
        top.addWidget(more, 0, QtCore.Qt.AlignmentFlag.AlignBottom)
        self.plan_button = QtWidgets.QPushButton(t("caixilho.plan"))          # (0.359) a door's plan
        self.plan_button.setObjectName("plan")
        self.plan_button.setFixedHeight(34)
        self.plan_button.setToolTip(t("caixilho.plan_tip"))
        self.plan_button.setStyleSheet(more.styleSheet())
        self.plan_button.clicked.connect(self.plan_options)
        self.plan_button.setVisible(self.op.kind == "door")
        top.addWidget(self.plan_button, 0, QtCore.Qt.AlignmentFlag.AlignBottom)
        box.addLayout(top)
        line = QtWidgets.QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background: %s;" % LINE)
        box.addWidget(line)
        bottom = QtWidgets.QHBoxLayout()
        bottom.setSpacing(26)
        self.metric_labels = {}
        for key in ("size", "glass", "open", "ifc"):
            pair = QtWidgets.QHBoxLayout()
            pair.setSpacing(8)
            caption = QtWidgets.QLabel(t("caixilho.metric_" + key))
            caption.setStyleSheet("color: %s; font-size: 11px;" % MUTED)
            value = QtWidgets.QLabel()
            value.setObjectName("metric_" + key)
            value.setFont(_font(MONO, 13))
            pair.addWidget(caption)
            pair.addWidget(value)
            bottom.addLayout(pair)
            self.metric_labels[key] = value
        bottom.addStretch(1)
        self.warning = QtWidgets.QLabel()
        self.warning.setStyleSheet("color: %s; font-size: 11px;" % C["warning"])
        bottom.addWidget(self.warning)
        cancel = QtWidgets.QPushButton(t("caixilho.cancel"))
        cancel.setFixedHeight(38)
        cancel.setStyleSheet("QPushButton { padding: 0 16px; background: transparent; border: 1px solid %s;"
                             " border-radius: 10px; color: %s; font-size: 13px; }" % (EDGE, MUTED))
        cancel.clicked.connect(self.reject)
        bottom.addWidget(cancel)
        self.save_button = QtWidgets.QPushButton(t("caixilho.save"))
        self.save_button.setObjectName("save")
        self.save_button.setFixedHeight(38)
        self.save_button.setStyleSheet("QPushButton { padding: 0 16px; background: %s; border: 1px solid %s;"
                                       " border-radius: 10px; color: %s; font-size: 13px; }"
                                       % (C["button"], EDGE_2, TEXT))
        self.save_button.clicked.connect(lambda: self.finish(False))
        bottom.addWidget(self.save_button)
        self.insert_button = QtWidgets.QPushButton(t("caixilho.insert"))
        self.insert_button.setObjectName("insert")
        self.insert_button.setFixedHeight(38)
        self.insert_button.setStyleSheet("QPushButton { padding: 0 20px; border: 0; border-radius: 10px; background: "
                                         "%s; color: %s; font-size: 13px; font-weight: 600; }"
                                         "QPushButton:disabled { background: %s; color: %s; }"
                                         % (ACCENT, C["accent_text"], C["accent_off"], C["accent_off_text"]))
        self.insert_button.clicked.connect(lambda: self.finish(True))
        self.insert_button.setVisible(insert)
        bottom.addWidget(self.insert_button)
        box.addLayout(bottom)
        return foot

    @staticmethod
    def _toggle_style(on):
        """(0.309) A button of the bar over the drawing: on (a parameter turned on), as a chosen system's."""
        return ("QPushButton { padding: 0 12px; background: %s; border: 1px solid %s; border-radius: 9px; color: %s;"
                " font-size: 12px; }" % ((C["system_on_bg"], ACCENT, C["system_on_text"]) if on else (CARD, EDGE, TEXT)))

    @staticmethod
    def _input_style(colour):
        return ("QLineEdit { padding: 0 10px; border: 1px solid %s; border-radius: 8px; background: %s; color: %s; }"
                % (EDGE, CANVAS, colour))

    # ---------------- showing it

    def refresh(self):
        if not hasattr(self, "metric_labels"):
            return
        op = self.op
        self._fill_tabs()
        for key, b in self.view_buttons.items():
            on = key == self.view
            b.setStyleSheet("QPushButton { padding: 0 12px; border: 0; border-radius: 6px; background: %s; color: %s;"
                            " font-size: 12px; }" % ((C["chip_on"], C["chip_on_text"]) if on else ("transparent", MUTED)))
        self.link_button.setText(("● " if self.linked else "○ ") + t("caixilho.linked"))
        for flag, b in self.eq_buttons.items():
            on = getattr(op, flag)
            b.setText(("● " if on else "○ ") + t("caixilho." + flag))
            b.setStyleSheet(self._toggle_style(on))
        self.overlay.adjustSize()                       # (its buttons as wide as their styles make them)
        for key, b in self.kind_buttons.items():
            on = key == op.kind
            b.setStyleSheet("QPushButton { padding: 0 14px; border: 0; border-radius: 6px; background: %s; color: %s;"
                            " font-size: 12px; }" % ((C["chip_on"], C["chip_on_text"]) if on else ("transparent", MUTED)))
        if not self.name_edit.hasFocus():
            self.name_edit.setText(op.name)
        for key, b in self.system_buttons.items():
            on = key == op.system
            b.setStyleSheet("QPushButton { padding: 0 12px; border: 1px solid %s; border-radius: 8px; background: %s;"
                            " color: %s; font-size: 12px; }"
                            % ((ACCENT, C["system_on_bg"], C["system_on_text"]) if on
                               else (EDGE, "transparent", C["off_text"])))
        for key, b in self.colour_buttons.items():
            b.setStyleSheet("QToolButton { border-radius: 15px; border: 2px solid %s; background: %s; }"
                            % (ACCENT if key == op.colour else EDGE_2, cx.COLOUR_HEX[key]))
        for key, edit in self.number_edits.items():
            if not edit.hasFocus():
                edit.setText(_mm(getattr(op, key)))
        self.number_edits["sill"].setVisible(op.kind == "window")
        self.sill_caption.setVisible(op.kind == "window")
        m = cx.metrics(op)
        self.metric_labels["size"].setText("{} × {} mm".format(op.W, op.H))
        self.metric_labels["glass"].setText("{} · {} %".format(_m2(m["glass"]), int(round(m["glass"] / m["area"] * 100))))
        self.metric_labels["open"].setText("{} · {} %".format(_m2(m["open"]), int(round(m["open"] / m["area"] * 100))))
        self.metric_labels["ifc"].setText(cx.ifc_class(op))
        wrong = cx.problems(op)
        self.warning.setText(t(*wrong[0][:1], **wrong[0][1]) if wrong else "")
        self.save_button.setEnabled(not wrong)
        self.insert_button.setEnabled(not wrong)
        s = self.canvas.frame()[0]
        ratio = 1.0 / (s * 0.2646)
        nice = min((5, 10, 20, 25, 50, 100), key=lambda v: abs(v - ratio))
        self.scale.setText(t("caixilho.scale", n=nice))
        self.canvas.place_widgets()
        self._show_card()
        self.canvas.update()

    def _fill_tabs(self):
        for b in self.tab_buttons:
            self.tab_row.removeWidget(b)
            _drop(b)
        self.tab_buttons = []
        for k, it in enumerate(self.items):
            on = k == self.active
            b = QtWidgets.QToolButton()
            b.setObjectName("tab_{}".format(k))
            b.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            b.setText("{}   {}×{}".format(it.name, it.W, it.H))
            b.setIcon(self._kind_icon(it.kind, TEXT if on else MUTED))
            b.setFixedHeight(38)
            b.setStyleSheet("QToolButton { padding: 0 14px; border: 0; border-top-left-radius: 8px;"
                            " border-top-right-radius: 8px; background: %s; color: %s; font-size: 13px;"
                            " font-weight: 600; %s }"
                            % (C["tab_on"] if on else "transparent", TEXT if on else MUTED,
                               "border-top: 2px solid %s;" % ACCENT if on else ""))
            b.clicked.connect(lambda _=False, i=k: self.show_item(i))
            self.tab_row.insertWidget(k, b)
            self.tab_buttons.append(b)

    @staticmethod
    def _kind_icon(kind, colour):
        pm = QtGui.QPixmap(16, 16)
        pm.fill(QtCore.Qt.GlobalColor.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.setPen(QtGui.QPen(QtGui.QColor(colour), 1.3))
        if kind == "door":
            p.drawRect(QtCore.QRectF(4, 1.5, 8, 13))
            p.setBrush(QtGui.QColor(colour))
            p.drawEllipse(QtCore.QPointF(10, 8.5), 0.9, 0.9)
        else:
            p.drawRect(QtCore.QRectF(2, 3, 12, 10))
            p.drawLine(QtCore.QPointF(8, 3), QtCore.QPointF(8, 13))
        p.end()
        return QtGui.QIcon(pm)

    def _show_card(self):
        sel = self.selected
        if sel is None:
            self.card.hide()
            return
        self.card.show_for(self.op, sel[0], sel[1], self.view == "interior")
        rect = next(r for c, rr, r in self.canvas.panel_rects() if (c, rr) == sel)
        x = min(max(rect.center().x() - 138, 8), self.canvas.width() - 284)
        y = min(max(rect.center().y() - 118, 52), self.canvas.height() - self.card.height() - 8)
        self.card.move(int(x), int(y))
        self.card.show()
        self.card.raise_()

    # ---------------- what is done

    def show_item(self, i):
        self.active = i
        self.selected = self.handle = None
        self.refresh()

    def add_item(self, op):
        op.name = cx.next_name(self.items + [cx.Opening(n, "", 0, 0, 0, 0, "", "", []) for n in self.taken], op.kind)
        self.items.append(op)
        self.originals.append(None)
        self.show_item(len(self.items) - 1)

    def duplicate(self):
        op = cx.clone(self.op)
        op.key = None
        self.add_item(op)

    def select(self, cell):
        self.selected = cell
        self.refresh()

    def set_view(self, view):
        self.view = view
        self.refresh()

    def toggle_linked(self):
        self.linked = not self.linked
        self.refresh()

    def toggle_equal(self, flag):
        """(0.309) The parameter «equal widths» (eq_cols) or «equal heights» (eq_rows) turned on or off."""
        on = not getattr(self.op, flag)
        self.edit(lambda op: cx.set_equal(op, **{"cols" if flag == "eq_cols" else "rows": on}))

    def set_op(self, op_key):
        c, r = self.selected
        self.edit(lambda op: setattr(op.cols[c].panels[r], "op", op_key))

    def set_fill(self, fill):
        c, r = self.selected
        self.edit(lambda op: setattr(op.cols[c].panels[r], "fill", fill))

    def split_v(self):
        if self.selected is not None:
            c = self.selected[0]
            self.edit(lambda op: cx.split_v(op, c) or False)
            self.select(None)

    def split_h(self):
        if self.selected is not None:
            c, r = self.selected
            self.edit(lambda op: cx.split_h(op, c, r) or False)
            self.select(None)

    def copy_row(self):
        if self.selected is not None:
            c, r = self.selected
            self.edit(lambda op: cx.copy_along_row(op, c, r))

    def merge_col(self, i):
        self.edit(lambda op: cx.merge_col(op, i))
        self.select(None)

    def merge_row(self, c, b):
        self.edit(lambda op: cx.merge_row(op, c, b, self.linked))
        self.select(None)

    def typed(self, key, text):
        op = cx.clone(self.op)
        if cx.set_size(op, key, text, self.linked):
            self.change(op, keep_selection=True)
        else:
            self.refresh()

    def rename(self):
        name = self.name_edit.text().strip()[:40]
        if name:
            self.edit(lambda op: setattr(op, "name", name))

    def set_system(self, system):
        def change(op):
            op.system, op.material = system, ""
        self.edit(change)

    def set_colour(self, colour):
        def change(op):
            op.colour, op.material = colour, ""
        self.edit(change)

    def more_options(self):
        """What the studio's drawing does not show — the frame's depth, the leaves, the glass, a sill stone or a
        threshold, an arch, portadas, an estore, a screen, a grille, the hardware — in a small window of its own."""
        dialog = MoreOptions(self, cx.to_design(self.op), self.op.W / 1000.0)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.edit(lambda op: setattr(op, "base", dialog.design))

    def plan_options(self):
        """(0.359) How the door is drawn in plan — open with its swing or closed with the swing's line, the swing's
        lines, its casings, its threshold —, with its plan drawn as it changes, in a small window of its own."""
        dialog = PlanOptions(self, cx.to_design(self.op), self.op.W / 1000.0)
        self._plan_dialog = dialog                       # (tests)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.edit(lambda op: setattr(op, "base", dialog.design))

    def finish(self, inserting):
        if cx.problems(self.op):
            return
        self.inserting = inserting
        self.accept()

    def flash(self, text):
        self.toast.setText(text)
        self.toast.adjustSize()
        self.toast.move(self.canvas.width() - self.toast.width() - 16, 12)
        self.toast.show()
        QtCore.QTimer.singleShot(2800, self.toast.hide)

    def changed_items(self):
        """[(opening, design)] of the openings new or changed (as joinery designs by columns)."""
        out = []
        for op, before in zip(self.items, self.originals):
            if before is None or not cx.same(op, before) or op.base != before.base:
                out.append((op, cx.to_design(op)))
        return out


PLAN_WALL = 0.20                   # m: (0.359) the wall the plan's preview shows the door in


class PlanPreview(QtWidgets.QWidget):
    """(0.359) A door's plan as the plans draw it (core.joinery: its pieces filled, its symbol's lines), in a wall
    PLAN_WALL thick, the wall's faces either side."""

    PIECES = {"aro": "#c9a27a", "remate": "#e2c49f", "folha": "#b07a4a", "soleira": "#b8b8b0"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.design, self.door_width = None, 0.9
        self.setMinimumSize(360, 300)

    def show_design(self, design, width):
        self.design, self.door_width = design, width
        self.update()

    def paintEvent(self, _event):
        if self.design is None:
            return
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QtGui.QColor(CANVAS))
        w, t_ = self.door_width, PLAN_WALL
        depth = self.design.depth if 0 < self.design.depth < t_ else t_
        y0 = (t_ - depth) / 2
        k = min(self.width() / (w + 0.8), self.height() / (w + t_ + 0.4)) * 0.9
        ox = (self.width() - w * k) / 2
        oy = self.height() - 0.25 * k

        def at(x, y):
            return QtCore.QPointF(ox + x * k, oy - y * k)

        p.setPen(QtGui.QPen(QtGui.QColor(TEXT), 1.4))
        p.setBrush(QtGui.QColor("#d9d4c7"))                      # (the wall either side)
        for x0, x1 in ((-0.4, 0.0), (w, w + 0.4)):
            p.drawPolygon(QtGui.QPolygonF([at(x0, 0), at(x1, 0), at(x1, t_), at(x0, t_)]))
        p.setPen(QtGui.QPen(QtGui.QColor(TEXT), 1.0))
        for role, ring, _key in core_joinery.plan_pieces(self.design, w, 2.1, y0, y0 + depth, (0.0, t_)):
            p.setBrush(QtGui.QColor(self.PIECES.get(role, "#cccccc")))
            p.drawPolygon(QtGui.QPolygonF([at(x, y) for x, y in ring]))
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        for line in core_joinery.plan_symbol(self.design, w, 2.1, y0, y0 + depth, (0.0, t_)):
            p.drawPolyline(QtGui.QPolygonF([at(x, y) for x, y in line]))
        p.end()


class PlanOptions(QtWidgets.QDialog):
    """(0.359) A door in plan, as the owner asked (2026-11-02): drawn open — its leaf open with its swing — or closed
    — the leaf in its frame, the swing shown by its line —, the swing's lines solid or dashed, its casings (how far onto
    the wall, how thick, on which faces), its threshold; its plan drawn as it changes. self.design changed."""

    def __init__(self, parent, design, width):
        super().__init__(parent)
        self.setWindowTitle(t("caixilho.plan"))
        self.design = design
        self.width_m = width
        self.setStyleSheet("QDialog { background: %s; } QLabel, QCheckBox { color: %s; }"
                           "QLineEdit, QComboBox { background: %s; color: %s; border: 1px solid %s; border-radius: 6px;"
                           " padding: 3px 6px; }" % (BG, TEXT, CANVAS, TEXT, EDGE))
        columns = QtWidgets.QHBoxLayout(self)
        form = QtWidgets.QFormLayout()
        columns.addLayout(form)
        self.shown = QtWidgets.QComboBox()
        for value, label in ((True, "caixilho.plan_open"), (False, "caixilho.plan_closed")):
            self.shown.addItem(t(label), value)
        self.shown.setCurrentIndex(0 if design.plan_open else 1)
        form.addRow(t("caixilho.plan_shown"), self.shown)
        self.swing = QtWidgets.QComboBox()
        for value in ("solid", "dashed"):
            self.swing.addItem(t("caixilho.swing_" + value), value)
        self.swing.setCurrentIndex(max(0, self.swing.findData(design.swing_style)))
        form.addRow(t("caixilho.swing"), self.swing)
        form.addRow(t("caixilho.plan_frame"), QtWidgets.QLabel("{:.0f} mm".format(design.frame * 1000)))
        self.sizes = {}
        for attr, label in (("casing", "joinery.casing"), ("casing_depth", "caixilho.casing_depth"),
                            ("stone", "joinery.threshold")):
            edit = QtWidgets.QLineEdit("{:.0f}".format(getattr(design, attr) * 1000))
            edit.setObjectName("plan_" + attr)
            edit.editingFinished.connect(self._changed)
            form.addRow(t(label) + " (mm)", edit)
            self.sizes[attr] = edit
        self.casing_sides = QtWidgets.QComboBox()
        for value in ("both", "open", "push"):
            self.casing_sides.addItem(t("joinery.casing_" + value), value)
        self.casing_sides.setCurrentIndex(max(0, self.casing_sides.findData(design.casing_sides)))
        form.addRow(t("joinery.casing_sides"), self.casing_sides)
        for box in (self.shown, self.swing, self.casing_sides):
            box.currentIndexChanged.connect(lambda _i: self._changed())
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._ok)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        self.preview = PlanPreview()
        columns.addWidget(self.preview, 1)
        self._changed()

    def _values(self):
        values = {}
        for attr, edit in self.sizes.items():
            v = cx.evaluate(edit.text())
            if v is None or v < 0:
                return None
            values[attr] = v / 1000.0
        values.update(plan_open=bool(self.shown.currentData()), swing_style=self.swing.currentData(),
                      casing_sides=self.casing_sides.currentData())
        return values

    def _changed(self):
        import dataclasses
        values = self._values()
        if values is not None:
            self.preview.show_design(dataclasses.replace(self.design, **values), self.width_m)

    def _ok(self):
        import dataclasses
        values = self._values()
        if values is None:
            return
        self.design = dataclasses.replace(self.design, **values)
        self.accept()


class MoreOptions(QtWidgets.QDialog):
    """The opening's other options (the old generator's): self.design changed."""

    def __init__(self, parent, design, width):
        super().__init__(parent)
        self.setWindowTitle(t("caixilho.more"))
        self.design = design
        self.width = width
        self.setStyleSheet("QDialog { background: %s; } QLabel, QCheckBox { color: %s; }"
                           "QLineEdit, QComboBox { background: %s; color: %s; border: 1px solid %s; border-radius: 6px;"
                           " padding: 3px 6px; }" % (BG, TEXT, CANVAS, TEXT, EDGE))
        columns = QtWidgets.QHBoxLayout(self)
        form = QtWidgets.QFormLayout()
        columns.addLayout(form)
        self.sizes = {}
        door = design.kind == "door"
        sizes = [("depth", "joinery.depth"), ("sash", "joinery.sash"), ("sash_depth", "joinery.sash_depth"),
                 ("mullion", "joinery.mullion"), ("glass", "joinery.glass"),
                 ("stone", "joinery.threshold" if door else "joinery.sill"), ("stone_out", "joinery.stone_out"),
                 ("shutter", "joinery.shutter")]
        if door:
            sizes.append(("casing", "joinery.casing"))
        for attr, label in sizes:
            edit = QtWidgets.QLineEdit("{:.0f}".format(getattr(design, attr) * 1000))
            edit.setObjectName("more_" + attr)
            form.addRow(t(label) + " (mm)", edit)
            self.sizes[attr] = edit
        self.shutter_closed = QtWidgets.QSpinBox()
        self.shutter_closed.setRange(0, 100)
        self.shutter_closed.setSuffix(" %")
        self.shutter_closed.setValue(int(round(design.shutter_closed * 100)))
        form.addRow(t("joinery.shutter_closed"), self.shutter_closed)
        self.casing_sides = QtWidgets.QComboBox()
        for value in ("both", "open", "push"):
            self.casing_sides.addItem(t("joinery.casing_" + value), value)
        self.casing_sides.setCurrentIndex(max(0, self.casing_sides.findData(design.casing_sides)))
        if door:
            form.addRow(t("joinery.casing_sides"), self.casing_sides)
        self.arch = QtWidgets.QComboBox()
        for value, label in (("", "joinery.arch_none"), ("round", "joinery.arch_round"),
                             ("segmental", "joinery.arch_segmental"), ("pointed", "joinery.arch_pointed")):
            self.arch.addItem(t(label), value)
        self.arch.setCurrentIndex(max(0, self.arch.findData(design.arch)))
        form.addRow(t("joinery.arch"), self.arch)
        self.louvres = QtWidgets.QComboBox()
        for value in ("", "left", "right", "pair"):
            self.louvres.addItem(t("joinery.louvres_" + (value or "none")), value)
        self.louvres.setCurrentIndex(max(0, self.louvres.findData(design.louvres)))
        form.addRow(t("joinery.louvres"), self.louvres)
        self.checks = {}
        for attr, label in (("louvres_open", "joinery.louvres_open"), ("screen", "joinery.screen"),
                            ("grille", "joinery.grille"), ("hardware", "joinery.hardware"), ("drip", "joinery.drip")):
            box = QtWidgets.QCheckBox(t(label))
            box.setChecked(bool(getattr(design, attr)))
            form.addRow(box)
            self.checks[attr] = box
        right = QtWidgets.QFormLayout()
        columns.addLayout(right)
        from ..ifc import catalog
        self.materials = {}
        for attr, label in (("glass_material", "joinery.glass_material"), ("stone_material", "joinery.stone_material"),
                            ("hardware_material", "joinery.hardware_material"),
                            ("shutter_material", "joinery.shutter_material"),
                            ("screen_material", "joinery.screen_material"),
                            ("grille_material", "joinery.grille_material"),
                            ("louvres_material", "joinery.louvres_material")):
            combo = QtWidgets.QComboBox()
            for m in catalog.MATERIALS.values():
                combo.addItem(m.name_pt if lang() == "pt" else m.name_en, m.key)
            combo.setCurrentIndex(max(0, combo.findData(getattr(design, attr))))
            right.addRow(t(label), combo)
            self.materials[attr] = combo
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._ok)
        buttons.rejected.connect(self.reject)
        right.addRow(buttons)

    def _ok(self):
        import dataclasses
        values = {}
        for attr, edit in self.sizes.items():
            v = cx.evaluate(edit.text())
            if v is None or v < 0:
                edit.setFocus()
                return
            values[attr] = v / 1000.0
        values.update({attr: box.isChecked() for attr, box in self.checks.items()})
        values.update({attr: combo.currentData() for attr, combo in self.materials.items()})
        values["louvres"] = self.louvres.currentData()
        values["shutter_closed"] = self.shutter_closed.value() / 100.0
        values["casing_sides"] = self.casing_sides.currentData()
        design = dataclasses.replace(self.design, **values)
        self.design = core_joinery.with_arch(design, self.arch.currentData(), self.width) \
            if self.arch.currentData() != design.arch else design
        self.accept()
