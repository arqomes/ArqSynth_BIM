"""(0.465, the owner: «colocar opções visuais em vez de texto») The levels' look chosen by pictures, not words: a row
of small buttons for each of its settings — the line (dash-dot, dashed, dotted, continuous, at its ends), the end (Revit's
quartered circle, a square, a triangle, none), at which end, the words (their layout), the colour (swatches) —, each
drawn as it will look; the words are their tooltips. IconChoice behaves as the list it replaces (currentData,
findData, setCurrentIndex, currentIndexChanged), so the panel's code and its tests stay as they were."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..model import symbols as marks_model
from . import theme

W, H = 44, 24               # px: an icon
SWATCH = 18                 # px: a colour's square


def _ink():
    """The pictures' ink: the theme's text (light on a dark panel, dark on a light one)."""
    return QtGui.QColor(theme.C.get("text", "#202020"))


def _canvas(w=W, h=H):
    pm = QtGui.QPixmap(w, h)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    return pm, p


def _pen(colour, width=1.4, dashes=None, round_=False):
    q = QtGui.QPen(QtGui.QBrush(colour), width)
    q.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap if round_ else QtCore.Qt.PenCapStyle.FlatCap)
    if dashes:
        q.setDashPattern([max(d * 1.6 / width, 0.2) for d in dashes])
    return q


def _mark(p, kind, x, y, s, colour, right=True):
    """A level's mark at the line's end (x, y), `s` px, as model/symbols.level_parts draws it."""
    d = 1.0 if right else -1.0
    p.setPen(_pen(colour, 1.0))
    p.setBrush(colour)
    if kind == "triangle":
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(x, y), QtCore.QPointF(x - s, y - s * 1.4),
                                       QtCore.QPointF(x + s, y - s * 1.4)]))
    elif kind == "target":
        c = QtCore.QPointF(x + d * s, y)
        rect = QtCore.QRectF(c.x() - s, c.y() - s, 2 * s, 2 * s)
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.drawEllipse(rect)
        p.setBrush(colour)
        p.drawPie(rect, 0, 90 * 16)
        p.drawPie(rect, 180 * 16, 90 * 16)
    elif kind == "square":
        q = 0.8 * s
        p.drawRect(QtCore.QRectF(min(x, x + d * 2 * q), y - q, 2 * q, 2 * q))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)


def line_icon(kind):
    """A level's line as it will be drawn."""
    pm, p = _canvas()
    ink, y = _ink(), H / 2
    if kind == "ends":
        p.setPen(_pen(ink, 1.6))
        p.drawLine(QtCore.QPointF(4, y), QtCore.QPointF(14, y))
        p.drawLine(QtCore.QPointF(W - 14, y), QtCore.QPointF(W - 4, y))
    else:
        dashes = marks_model.DASHES.get(kind)
        p.setPen(_pen(ink, 1.8 if kind == "dotted" else 1.4, dashes, round_=kind == "dotted"))
        p.drawLine(QtCore.QPointF(4, y), QtCore.QPointF(W - 4, y))
    p.end()
    return QtGui.QIcon(pm)


def mark_icon(kind):
    """A level's end: the line coming to it, the mark (none: the line only)."""
    pm, p = _canvas()
    ink, y = _ink(), H / 2 + 3
    end = W - 14
    p.setPen(_pen(ink, 1.2, (3.0, 1.5)))
    p.drawLine(QtCore.QPointF(3, y), QtCore.QPointF(end, y))
    _mark(p, kind, end, y, 5.0, ink)
    if kind == "none":                               # (only the words)
        p.setPen(ink)
        font = p.font()
        font.setPixelSize(8)
        p.setFont(font)
        p.drawText(QtCore.QRectF(end - 12, y - 11, 22, 9), QtCore.Qt.AlignmentFlag.AlignCenter, "+3")
    p.end()
    return QtGui.QIcon(pm)


def ends_icon(kind):
    """At which end(s) the mark is."""
    pm, p = _canvas()
    ink, y = _ink(), H / 2
    p.setPen(_pen(ink, 1.2, (3.0, 1.5)))
    p.drawLine(QtCore.QPointF(9, y), QtCore.QPointF(W - 9, y))
    if kind in ("right", "both"):
        _mark(p, "target", W - 9, y, 4.0, ink)
    if kind in ("left", "both"):
        _mark(p, "target", 9, y, 4.0, ink, right=False)
    p.end()
    return QtGui.QIcon(pm)


def label_icon(kind):
    """The words' layout round the line: «+3,00 Piso», «PISO | +3,00», the name over and the level under (Revit's), or
    the level over and the name under — in small letters."""
    pm, p = _canvas(W + 12, H + 6)
    ink, y = _ink(), (H + 6) / 2
    w = W + 12
    p.setPen(_pen(ink, 1.0, (3.0, 1.5)))
    p.drawLine(QtCore.QPointF(2, y), QtCore.QPointF(w - 8, y))
    _mark(p, "triangle", w - 8, y, 3.0, ink)
    font = p.font()
    font.setPixelSize(8)
    p.setFont(font)
    p.setPen(ink)
    over = QtCore.QRectF(0, y - 11, w - 13, 10)
    under = QtCore.QRectF(0, y + 1, w - 13, 10)
    right = QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
    if kind == "name_over":
        p.drawText(over, right, "Piso 1")
        p.drawText(under, right, "+3,00")
    elif kind == "level_over":
        p.drawText(over, right, "+3,00")
        p.drawText(under, right, "Piso 1")
    elif kind == "name_level":
        p.drawText(over, right, "PISO|+3")
    else:
        p.drawText(over, right, "+3 Piso")
    p.end()
    return QtGui.QIcon(pm)


def colour_icon(value):
    """A colour's swatch: "" the drawing's own (half dark, half light), "?" another one (a palette)."""
    pm, p = _canvas(SWATCH + 4, SWATCH + 4)
    rect = QtCore.QRectF(2, 2, SWATCH, SWATCH)
    p.setPen(_pen(QtGui.QColor("#888888"), 1.0))
    if value == "":
        p.setBrush(QtGui.QColor("#ffffff"))
        p.drawRoundedRect(rect, 3, 3)
        p.setBrush(QtGui.QColor("#202020"))
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(2, 2), QtCore.QPointF(2 + SWATCH, 2),
                                       QtCore.QPointF(2, 2 + SWATCH)]))
    elif value == "?":
        for k, colour in enumerate(("#d23c3c", "#e8b923", "#2e9e4f", "#3a6fb5")):
            p.setBrush(QtGui.QColor(colour))
            p.drawPie(rect, int(k * 90 * 16), 90 * 16)
    else:
        p.setBrush(QtGui.QColor(value))
        p.drawRoundedRect(rect, 3, 3)
    p.end()
    return QtGui.QIcon(pm)


class _Flow(QtWidgets.QLayout):
    """(0.476) Side by side, on to the next line where the room ends — as words in a paragraph. In one row (5 × 50 px)
    beside its label, a setting's pictures asked for 369 px and widened the left column of panels for good (the 3D view
    narrower); now its least width is one picture's."""

    def __init__(self, parent=None, gap=2):
        super().__init__(parent)
        self._items, self._gap = [], gap
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def insertWidget(self, index, widget):
        self.addChildWidget(widget)
        self._items.insert(index, QtWidgets.QWidgetItem(widget))
        self.invalidate()

    def count(self):
        return len(self._items)

    def itemAt(self, k):
        return self._items[k] if 0 <= k < len(self._items) else None

    def takeAt(self, k):
        return self._items.pop(k) if 0 <= k < len(self._items) else None

    def expandingDirections(self):
        return QtCore.Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._place(QtCore.QRect(0, 0, width, 0), False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._place(rect, True)

    def sizeHint(self):                                  # (all in one line, as before)
        hints = [i.sizeHint() for i in self._items]
        return QtCore.QSize(sum(h.width() for h in hints) + self._gap * max(len(hints) - 1, 0),
                            max((h.height() for h in hints), default=0))

    def minimumSize(self):
        size = QtCore.QSize(0, 0)
        for i in self._items:
            size = size.expandedTo(i.minimumSize())
        return size

    def _place(self, rect, put):
        """The items laid in `rect` from its top left, a new line where the next does not fit: their height."""
        x, y, line = rect.x(), rect.y(), 0
        for i in self._items:
            hint = i.sizeHint()
            if x > rect.x() and x + hint.width() > rect.x() + rect.width():
                x, y, line = rect.x(), y + line + self._gap, 0
            if put:
                i.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), hint))
            x += hint.width() + self._gap
            line = max(line, hint.height())
        return y + line - rect.y()


class IconChoice(QtWidgets.QWidget):
    """A row of pictures, one of them chosen — a list's ways (addItem, insertItem, findData, currentData,
    setCurrentIndex, currentIndexChanged). (0.476) On two lines when the panel is narrow."""

    currentIndexChanged = QtCore.Signal(int)

    def __init__(self, icon_of, size=(W, H)):
        super().__init__()
        self._icon_of, self._size = icon_of, QtCore.QSize(*size)
        self._values, self._buttons = [], []
        self._current = -1
        self._ink = _ink().name()                       # (the theme's ink they were drawn with)
        self._row = _Flow(self)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)

    def _button(self, text, value):
        b = QtWidgets.QToolButton()
        b.setCheckable(True)
        b.setAutoRaise(True)
        b.setIcon(self._icon_of(value))
        b.setIconSize(self._size)
        b.setToolTip(text)
        b.setAccessibleName(text)
        b.setObjectName("choice_{}".format(value))
        b.clicked.connect(lambda _on=False, btn=b: self._clicked(btn))
        return b

    def addItem(self, text, value=None):
        self.insertItem(len(self._values), text, value)

    def insertItem(self, index, text, value=None):
        b = self._button(text, value)
        self._values.insert(index, value)
        self._buttons.insert(index, b)
        self._row.insertWidget(index, b)
        if self._current >= index:
            self._current += 1
        self._show()

    def _clicked(self, button):
        k = self._buttons.index(button)
        changed = k != self._current
        self._current = k
        self._show()
        if changed:
            self.currentIndexChanged.emit(k)

    def _show(self):
        for k, b in enumerate(self._buttons):
            b.setChecked(k == self._current)

    def count(self):
        return len(self._values)

    def itemData(self, k):
        return self._values[k] if 0 <= k < len(self._values) else None

    def findData(self, value):
        return self._values.index(value) if value in self._values else -1

    def currentIndex(self):
        return self._current

    def currentData(self):
        return self.itemData(self._current)

    def setCurrentIndex(self, k):
        if k == self._current or not -1 <= k < len(self._values):
            return
        self._current = k
        self._show()
        if not self.signalsBlocked():
            self.currentIndexChanged.emit(k)

    def refresh(self):
        """The pictures drawn again when the theme changed (their ink: light on dark, dark on light)."""
        ink = _ink().name()
        if ink == self._ink:
            return
        self._ink = ink
        for value, b in zip(self._values, self._buttons):
            b.setIcon(self._icon_of(value))

    def button(self, value):
        """The button of a value (tests)."""
        k = self.findData(value)
        return self._buttons[k] if k >= 0 else None


# each setting's pictures, and their size
ICONS = {"line": (line_icon, (W, H)), "mark": (mark_icon, (W, H)), "ends": (ends_icon, (W, H)),
         "label": (label_icon, (W + 12, H + 6))}
