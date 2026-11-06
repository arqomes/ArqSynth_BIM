"""(0.429) A layered type's section drawn live in the type editor (Aprender com o Hestia, passo 3): its layers side by
side — a wall's from the outside (left) to the inside (right), a slab's / roof's from the top down —, each in its
material's cut colour and hatch, the lines between them thin and its outline thick, the core marked («núcleo»: the
layers given the structure function, else the thickest), each thickness written under it and the total. A drawing:
on white paper, in ink, whatever the theme."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.units import format_length
from ..i18n import decimal_sep, t
from ..ifc import catalog

PAPER, INK, NOTE = QtGui.QColor("#ffffff"), QtGui.QColor("#1d1d1b"), QtGui.QColor("#6b6b66")
CORE = QtGui.QColor("#c0392b")


def _cm(value):
    return format_length(value, decimal_sep(), 3)


def material_colours(key):
    """(fill, hatch colour or None, hatch kind or None) of a material where it is cut: its own cut background and
    pattern, else its colour lightened for paper."""
    m = catalog.MATERIALS.get(key)
    if m is None:
        return QtGui.QColor("#eeeeee"), None, None
    fill = None
    if m.cut_bg and m.cut_bg[1]:
        fill = QtGui.QColor(m.cut_bg[1])
    if fill is None:
        r, g, b = (float(c) for c in (m.color if m.color else (0.8, 0.8, 0.8))[:3])
        fill = QtGui.QColor.fromRgbF(r + (1 - r) * 0.55, g + (1 - g) * 0.55, b + (1 - b) * 0.55)
    if m.cut_fg and m.cut_fg[0]:
        return fill, QtGui.QColor(m.cut_fg[1] or "#000000"), m.cut_fg[0]
    return fill, None, None


def core_of(rows, functions):
    """The indices of the core layers: those of the structure (or substrate) function, else the thickest."""
    marked = [k for k, f in enumerate(functions or ()) if f in ("structure", "substrate")]
    if marked:
        return marked
    if not rows:
        return []
    return [max(range(len(rows)), key=lambda k: rows[k][1])]


class LayerSection(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.kind, self.rows, self.functions = "wall", [], ()
        self.setMinimumHeight(130)

    def set_layers(self, kind, rows, functions=()):
        """The type's kind and its layers [(material key, thickness m)] as typed (None: a thickness not readable)."""
        self.kind, self.rows, self.functions = kind, list(rows or ()), tuple(functions or ())
        self.update()

    def paintEvent(self, _event):                                   # noqa: N802 (Qt's name)
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        area = QtCore.QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.fillRect(area, PAPER)
        p.setPen(QtGui.QPen(QtGui.QColor("#d5d5d0"), 1))
        p.drawRect(area)
        rows = [(k, v) for k, v in self.rows if v and v > 0]
        if not rows:
            p.end()
            return
        total = sum(v for _k, v in rows)
        wall = self.kind == "wall"
        font = QtGui.QFont(self.font())
        font.setPointSizeF(max(7.0, font.pointSizeF() * 0.85))
        p.setFont(font)
        fm = QtGui.QFontMetricsF(font)
        if wall:                                                    # (across: outside left, inside right)
            span = area.width() - 90.0
            band = QtCore.QRectF(area.left() + 45.0, area.top() + 30.0, span, area.height() - 78.0)
        else:                                                       # (down: the top first)
            span = area.height() - 50.0
            band = QtCore.QRectF(area.left() + 70.0, area.top() + 20.0, area.width() - 160.0, span)
            rows = list(reversed(rows))                             # (a slab's layers bottom → top: drawn top first)
        scale = span / total
        core = set(core_of(self.rows, self.functions))
        order = list(range(len(self.rows)))
        if not wall:
            order = list(reversed(order))
        pos = band.left() if wall else band.top()
        pieces = []
        for (key, thickness), index in zip(rows, [k for k in order if self.rows[k][1] and self.rows[k][1] > 0]):
            size = thickness * scale
            rect = QtCore.QRectF(pos, band.top(), size, band.height()) if wall else \
                QtCore.QRectF(band.left(), pos, band.width(), size)
            fill, hatch, _kind = material_colours(key)
            p.fillRect(rect, fill)
            if hatch is not None:
                p.save()
                p.setClipRect(rect)
                p.setPen(QtGui.QPen(hatch, 0.8))
                step = 6.0
                x0, y0, x1, y1 = rect.left(), rect.top(), rect.right(), rect.bottom()
                d = -(y1 - y0)
                while d < (x1 - x0):
                    p.drawLine(QtCore.QPointF(x0 + d, y1), QtCore.QPointF(x0 + d + (y1 - y0), y0))
                    d += step
                p.restore()
            pieces.append((rect, key, thickness, index))
            pos += size
        p.setPen(QtGui.QPen(INK, 0.8))                              # (the lines between the layers: thin)
        for rect, *_rest in pieces[1:]:
            if wall:
                p.drawLine(rect.topLeft(), rect.bottomLeft())
            else:
                p.drawLine(rect.topLeft(), rect.topRight())
        outline = QtCore.QRectF(band.left(), band.top(), span if wall else band.width(),
                                band.height() if wall else span)
        p.setPen(QtGui.QPen(INK, 2.2))                              # (the outline: the cut, thick)
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.drawRect(outline)
        # the core: a red bracket on its layers
        cored = [r for r, _k, _t, i in pieces if i in core]
        if cored:
            p.setPen(QtGui.QPen(CORE, 1.6))
            if wall:
                a, b = min(r.left() for r in cored), max(r.right() for r in cored)
                y = band.top() - 8.0
                p.drawLine(QtCore.QPointF(a, y), QtCore.QPointF(b, y))
                p.drawLine(QtCore.QPointF(a, y), QtCore.QPointF(a, y + 5))
                p.drawLine(QtCore.QPointF(b, y), QtCore.QPointF(b, y + 5))
                p.drawText(QtCore.QRectF(a, y - fm.height() - 2, b - a, fm.height()),
                           QtCore.Qt.AlignmentFlag.AlignCenter, t("types.core"))
            else:
                a, b = min(r.top() for r in cored), max(r.bottom() for r in cored)
                x = band.right() + 8.0
                p.drawLine(QtCore.QPointF(x, a), QtCore.QPointF(x, b))
                p.drawLine(QtCore.QPointF(x, a), QtCore.QPointF(x - 5, a))
                p.drawLine(QtCore.QPointF(x, b), QtCore.QPointF(x - 5, b))
                p.drawText(QtCore.QRectF(x + 4, (a + b) / 2 - fm.height() / 2, 80, fm.height()),
                           QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter, t("types.core"))
        # each thickness, where it fits; the total
        p.setPen(INK)
        for rect, _key, thickness, _i in pieces:
            text = _cm(thickness)
            if wall:
                if fm.horizontalAdvance(text) + 4 <= rect.width():
                    p.drawText(QtCore.QRectF(rect.left(), band.bottom() + 3, rect.width(), fm.height()),
                               QtCore.Qt.AlignmentFlag.AlignCenter, text)
            elif fm.height() <= rect.height() + 2:
                p.drawText(QtCore.QRectF(band.left() - 66, rect.top(), 62, rect.height()),
                           QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter, text)
        p.setPen(NOTE)
        total_text = t("types.total", t=_cm(total))
        if wall:
            p.drawText(QtCore.QRectF(band.left(), band.bottom() + fm.height() + 6, span, fm.height()),
                       QtCore.Qt.AlignmentFlag.AlignCenter, total_text)
            p.drawText(QtCore.QRectF(area.left() + 2, band.top(), 40, band.height()),
                       QtCore.Qt.AlignmentFlag.AlignCenter, t("types.side_out"))
            p.drawText(QtCore.QRectF(band.right() + 3, band.top(), 40, band.height()),
                       QtCore.Qt.AlignmentFlag.AlignCenter, t("types.side_in"))
        else:
            p.drawText(QtCore.QRectF(band.left(), band.bottom() + 3, band.width(), fm.height()),
                       QtCore.Qt.AlignmentFlag.AlignCenter, total_text)
            p.drawText(QtCore.QRectF(band.left(), area.top() + 2, band.width(), 16),
                       QtCore.Qt.AlignmentFlag.AlignCenter, t("types.side_top"))
        p.end()
