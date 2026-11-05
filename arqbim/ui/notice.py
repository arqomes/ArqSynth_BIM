"""(0.321) The balloon over the view: what a command says, whole and where it is seen.

Until 0.320 a command that could not act (nothing selected, no plan open, no grid yet…) said why on one line at the
foot of the window — cut short by the footer's other parts, gone in 10 s, and hidden for 10 s by the discipline's
own line when a tab was clicked just before. Whoever did not look down saw a button that "did nothing" (the owner,
2026-10-31: «testei algumas mas não funcionaram»). Now it is said here, at the top of the view, in the middle (clear
of the view cube), word-wrapped to its end:

- a refusal (⚠, amber) stays until the next click in the view, Esc, another tool or another selection (30 s at most);
- what a command did (blue) goes by itself, after a time that grows with its length;
- the tool just chosen (white, its icon and name) says its first step, until the first click in the view.

A message said in the same turn as a change of tool or of selection (a command that refuses and goes back to Select)
is not taken down by that change: it is "fresh" until Qt's next turn.

(0.322) A command waiting for the elements it needs (green, as Revit's contextual tab) asks for them: «Clique nas
paredes…», how many are chosen, Enter / Esc. That request stays until it is answered or cancelled; what is said
meanwhile (a wrong element clicked) shows over it and, once gone, the request is back.
"""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from . import theme


def colours(kind):
    """A kind's (background, border, the icon's colour) — (0.338) the theme's ("notice_warning"…)."""
    return theme.C["notice_" + kind]


MAX_W = 760                 # px: the widest it gets
SIDE = 150                  # px kept free on the right (the view cube) — and on the left, to be in the middle
ROOMY = 460                 # px: narrower than this in the middle, it goes left of the view cube's band instead
MARGIN = 12
TOP = 10                    # px under the views' tabs
PAD_X, PAD_Y, GAP, ICON, CLOSE = 12, 8, 10, 20, 18
WARNING_MS = 30000
FONT_PX = 13


def info_ms(text):
    """How long what a command did stays in sight: longer for a longer text (4 to 12 s)."""
    return max(4000, min(12000, 45 * len(text)))


def _step(title, text):
    """A tool's step under its name: «Cota: abra primeiro…» under «Cota» says the name once."""
    if title and text.lower().startswith(title.lower() + ":"):
        text = text[len(title) + 1:].strip()
        text = text[:1].upper() + text[1:]
    return text


def _glyph(kind, colour):
    """The balloon's icon, drawn: a triangle with "!" (a refusal), a circle with "i" (said)."""
    pm = QtGui.QPixmap(ICON * 2, ICON * 2)                 # (drawn at twice the size: sharp on a 125 % screen)
    pm.setDevicePixelRatio(2.0)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    c = QtGui.QColor(colour)
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.setBrush(c)
    if kind == "warning":
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(10, 1.5), QtCore.QPointF(19, 18), QtCore.QPointF(1, 18)]))
    else:
        p.drawEllipse(QtCore.QPointF(10, 10), 9, 9)
    p.setBrush(theme.colour("notice_button"))               # (white on the light theme)
    if kind == "warning":
        p.drawRoundedRect(QtCore.QRectF(9, 6.5, 2, 6.5), 1, 1)
        p.drawEllipse(QtCore.QPointF(10, 15.2), 1.2, 1.2)
    else:
        p.drawEllipse(QtCore.QPointF(10, 5.8), 1.3, 1.3)
        p.drawRoundedRect(QtCore.QRectF(9, 8.5, 2, 7), 1, 1)
    p.end()
    return pm


class Notice(QtWidgets.QWidget):
    """The balloon, a child of the views' area (over the 3D canvas, or a sheet), placed under `tabs` (the views'
    tab bar): say() / hint() show it, dismiss() takes it down."""

    def __init__(self, parent, tabs=None):
        super().__init__(parent)
        self.setObjectName("notice")
        self.tabs = tabs
        self.kind = None                  # "warning" | "info" | "hint" | "ask" while shown
        self.fresh = False
        self._ask = None                  # (0.322) (title, text, icon) of a command's request, under the rest
        self.on_cancel = None             # (0.322) the request's × : the command given up
        self._glyph_shown = False         # (0.338) its icon is its kind's glyph (drawn again in another theme)
        font = self.font()
        font.setPixelSize(FONT_PX)
        self.icon = QtWidgets.QLabel(self)
        self.title = QtWidgets.QLabel(self)
        bold = QtGui.QFont(font)
        bold.setBold(True)
        self.title.setFont(bold)
        self.text = QtWidgets.QLabel(self)
        self.text.setFont(font)
        self.text.setWordWrap(True)
        for label in (self.title, self.text):
            label.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self.close_button = QtWidgets.QToolButton(self)
        self.close_button.setText("×")
        self.close_button.setAutoRaise(True)
        self.close_button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.close_button.setToolTip(t("notice.close"))
        self.close_button.clicked.connect(self._close_clicked)
        self.action = None                # (0.324) what the button does: the step that is missing
        self.action_button = QtWidgets.QPushButton(self)
        self.action_button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.action_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.action_button.clicked.connect(self._run_action)
        self.action_button.hide()
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.dismiss(force=True))
        self.restyle()
        self.hide()
        parent.installEventFilter(self)

    def restyle(self):
        """(0.338) Its text and its × in the theme's colours (its box is painted with them each time)."""
        c = theme.C
        for label in (self.title, self.text):
            label.setStyleSheet("QLabel { color: %s; background: transparent; }" % c["notice_text"])
        self.close_button.setStyleSheet("QToolButton { color: %s; font-size: 15px; border: none; padding: 0; }"
                                        "QToolButton:hover { color: %s; }" % (c["notice_close"], c["notice_text"]))
        if self.kind is not None:
            self._style_button(self.kind)
            if self._glyph_shown:
                self.icon.setPixmap(_glyph(self.kind, colours(self.kind)[2]))
        self.update()

    def _style_button(self, kind):
        accent = colours(kind)[2]
        self.action_button.setStyleSheet(
            "QPushButton { background: %s; color: %s; border: 1px solid %s; border-radius: 4px;"
            " padding: 3px 12px; font-size: 12px; font-weight: 600; }"
            "QPushButton:hover { background: %s; color: %s; }"
            % (theme.C["notice_button"], accent, accent, accent, theme.C["notice_button"]))

    # ------------------------------------------------------------ what is said

    def say(self, text, warning=False, action=None):
        """A command's message: a refusal (warning) or what it did. (0.324) action: (label, callable) — a button for
        the step that is missing («Gerar eixos…»); clicked, the balloon goes and it runs."""
        self._show("warning" if warning else "info", "", text, None, action=action)
        self.timer.start(WARNING_MS if warning else info_ms(text))

    def hint(self, title, text, icon=None, action=None):
        """The tool just chosen: its name and its first step, until the first click in the view. Not over a refusal
        said in the same turn (that one is what matters). (0.324) action: as say()'s."""
        if not text or (self.fresh and self.kind == "warning") or self._ask is not None:
            return
        self._show("hint", title, _step(title, text), icon, action=action)
        self.timer.stop()

    def _run_action(self):
        run, self.action = (self.action[1] if self.action else None), None
        self.dismiss(force=True)
        if run is not None:
            run()

    def ask(self, title, text, icon=None):
        """(0.322) A command's request for elements (or its count changed): shown until end_ask(); what is said meanwhile
        goes over it for its time."""
        self._ask = (title, text, icon)
        if self.kind in (None, "ask", "hint") or not self.fresh:     # (not over what was just said: after it)
            self._show("ask", title, text, icon)
            self.timer.stop()

    def end_ask(self):
        """(0.322) The request answered or given up: it goes."""
        self._ask = None
        if self.kind == "ask":
            self.kind = None
            self.hide()

    def _close_clicked(self):
        if self.kind == "ask":
            if self.on_cancel is not None:
                self.on_cancel()
            else:
                self.end_ask()
        else:
            self.dismiss(force=True)

    def hint_changed(self, text):
        """The tool's step changed before its first click (Tab, an option): the balloon follows."""
        if self.kind == "hint" and self.isVisible() and text:
            text = _step(self.title.text(), text)
            if text != self.text.text():
                self._show("hint", self.title.text(), text, None, keep_icon=True, action=self.action)

    def dismiss(self, force=False):
        """Taken down: a click in the view, Esc, another tool, another selection — but not what was said in this same
        turn (a command that refused and then changed the tool), unless forced (its ×, its time)."""
        if self.kind in (None, "ask") or (self.fresh and not force):
            return
        self.kind = None
        self.timer.stop()
        self.hide()
        if self._ask is not None:                     # (0.322: a request standing under it: back in sight)
            self._show("ask", *self._ask)

    def shown_text(self):
        """What the balloon says now ("" when it is not shown)."""
        return self.text.text() if self.kind is not None else ""

    # ------------------------------------------------------------ drawn and placed

    def _show(self, kind, title, text, icon, keep_icon=False, action=None):
        label = action[0] if action else ""
        same = (kind == self.kind and text == self.text.text() and title == self.title.text()
                and label == (self.action[0] if self.action else ""))
        self.kind = kind
        self.fresh = True
        self.action = action
        QtCore.QTimer.singleShot(0, self._settle)
        if not same:
            self.title.setText(title)
            self.title.setVisible(bool(title))
            self.text.setText(text)
            self.action_button.setText(label)
            self.action_button.setVisible(bool(label))
            self._style_button(kind)
            if icon is not None and not icon.isNull():
                self.icon.setPixmap(icon.pixmap(ICON, ICON))
                self._glyph_shown = False
            elif not keep_icon:
                self.icon.setPixmap(_glyph(kind, colours(kind)[2]))
                self._glyph_shown = True
            self.place()
        self.show()
        self.raise_()
        self.update()

    def _settle(self):
        self.fresh = False

    def place(self):
        """Its size for its text (as wide as the text, at most MAX_W or what the view leaves), at the top of the view
        in the middle — or, in a narrow view, in the middle of what the view cube leaves on its left."""
        parent = self.parentWidget()
        room = parent.width()
        middle = room - 2 * SIDE >= ROOMY
        widest = int(min(MAX_W, room - 2 * SIDE) if middle else max(280, min(MAX_W, room - SIDE - 2 * MARGIN)))
        around = PAD_X * 2 + ICON + GAP * 2 + CLOSE
        fm = QtGui.QFontMetrics(self.text.font())
        natural = max(fm.horizontalAdvance(line) for line in self.text.text().split("\n")) + 4
        if self.title.isVisibleTo(self):
            natural = max(natural, QtGui.QFontMetrics(self.title.font()).horizontalAdvance(self.title.text()) + 4)
        button = self.action_button.sizeHint() if self.action_button.isVisibleTo(self) else QtCore.QSize(0, 0)
        text_w = max(120, button.width(), min(natural, widest - around))
        title_h = self.title.sizeHint().height() if self.title.isVisibleTo(self) else 0
        text_h = self.text.heightForWidth(text_w)
        if text_h < 0:
            text_h = self.text.sizeHint().height()
        button_h = button.height() + 6 if button.height() else 0       # (0.324: under the text)
        h = max(ICON, title_h + text_h + button_h) + 2 * PAD_Y
        w = around + text_w
        top = TOP
        if self.tabs is not None and self.tabs.isVisible():
            top += self.tabs.geometry().bottom() + 1
        left = (room - w) // 2 if middle else max(MARGIN, (room - SIDE - w) // 2)
        self.setGeometry(max(0, left), top, w, h)
        x = PAD_X + ICON + GAP
        self.icon.setGeometry(PAD_X, PAD_Y, ICON, ICON)
        self.title.setGeometry(x, PAD_Y, text_w, title_h)
        self.text.setGeometry(x, PAD_Y + title_h, text_w, text_h)
        if button_h:
            self.action_button.setGeometry(x, PAD_Y + title_h + text_h + 6, button.width(), button.height())
        self.close_button.setGeometry(w - PAD_X - CLOSE + 6, PAD_Y - 3, CLOSE, CLOSE)

    def paintEvent(self, event):
        if self.kind is None:
            return
        background, border, accent = colours(self.kind)
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        box = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QtGui.QPen(QtGui.QColor(border), 1))
        p.setBrush(QtGui.QColor(background))
        p.drawRoundedRect(box, 6, 6)
        p.setPen(QtCore.Qt.PenStyle.NoPen)                  # (a stripe of its colour down the left side)
        p.setBrush(QtGui.QColor(accent if self.kind != "hint" else border))
        p.drawRoundedRect(QtCore.QRectF(0.5, 0.5, 4, box.height()), 2, 2)
        p.end()

    def mousePressEvent(self, event):
        """A click on the balloon itself (not its ×) takes it down too: it was read — not a request (its × gives the
        command up)."""
        if self.kind != "ask":
            self.dismiss(force=True)
        event.accept()

    def eventFilter(self, obj, event):
        if obj is self.parentWidget() and event.type() == QtCore.QEvent.Type.Resize and self.kind is not None:
            self.place()
        return False
