"""(0.314) The fill patterns (core/patterns.py) painted with a QPainter — on paper (the PDF, the sheets), in the
materials window's samples and the types' miniatures — and the lists that choose one, each with its sample."""

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..core import patterns as core_patterns
from ..i18n import t

SAMPLE_MM = 3.0            # px a mm in the samples (a drafting pattern as about on paper)
SAMPLE_M = 150.0           # px a metre in the samples (a model pattern at about 1:20)


def paint(painter, path, key, colour, unit, width, origin=(0.0, 0.0)):
    """A pattern inside a path: solid, filled in its colour; else its lines and dots in that colour, `width` wide.
    unit: painter units a pattern unit (a drafting pattern's mm, a model pattern's m); y down, the pattern's angles
    as seen (counter-clockwise); its lines through `origin` (painter units), so neighbouring shapes meet. key (0.318):
    or the pattern itself (one being made, in the pattern editor)."""
    pattern = key if isinstance(key, core_patterns.Pattern) else core_patterns.get(key)
    if pattern is None or path.isEmpty():
        return
    colour = QtGui.QColor(colour)
    if pattern.solid:
        painter.fillPath(path, colour)
        return
    ox, oy = float(origin[0]), float(origin[1])
    segs, dots = [], []
    boxes = [p.boundingRect() for p in path.toSubpathPolygons()] or [path.boundingRect()]
    for box in _merged(boxes):
        # (to the pattern's units, y up)
        s, d = core_patterns.families_segments(pattern.families,
                                               ((box.left() - ox) / unit, (oy - box.bottom()) / unit,
                                                (box.right() - ox) / unit, (oy - box.top()) / unit))
        segs.append(s)
        dots.append(d)
    segs = np.concatenate(segs) if segs else np.zeros((0, 2, 2))
    dots = np.concatenate(dots) if dots else np.zeros((0, 2))
    if not len(segs) and not len(dots):
        return
    lines = np.stack((ox + segs[..., 0] * unit, oy - segs[..., 1] * unit), axis=-1)       # (painter units)
    points = np.stack((ox + dots[:, 0] * unit, oy - dots[:, 1] * unit), axis=-1) if len(dots) else dots
    painter.save()
    if keeps_clip(painter):
        painter.setClipPath(path, QtCore.Qt.ClipOperation.IntersectClip if painter.hasClipping()
                            else QtCore.Qt.ClipOperation.ReplaceClip)
    else:                                           # (0.369: an SVG — cut to the path here, in geometry)
        lines = clip_segments(path, lines)
        points = np.array([p for p in points if path.contains(QtCore.QPointF(*p))]).reshape(-1, 2)
    pen = QtGui.QPen(colour, width)
    pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    if len(lines):
        painter.drawLines([QtCore.QLineF(a[0], a[1], b[0], b[1]) for a, b in lines])
    if len(points):
        dot = QtGui.QPen(colour, width * 1.6)
        dot.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        painter.setPen(dot)
        painter.drawPoints(QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in points]))
    painter.restore()


def keeps_clip(painter):
    """(0.369) Whether what the painter paints keeps its clip. Qt's SVG generator throws every clip away (Qt 6.12:
    the hatches of a cut wall spread over the whole page), so what is painted inside a shape for an SVG is cut to it
    in geometry instead (clip_segments)."""
    engine = painter.paintEngine()
    return engine is None or engine.type() != QtGui.QPaintEngine.Type.SVG


CLIP_CHUNK = 256           # segments crossed with all the path's edges at once (memory: this × the edges)


def clip_segments(path, segs):
    """(0.369) The parts of segments ((N, 2, 2) painter units) inside a path, by its fill rule: each cut where it
    crosses the path's outlines, the pieces whose middle is inside kept — those that follow on joined again."""
    segs = np.asarray(segs, dtype=float).reshape(-1, 2, 2)
    edges = []
    for poly in path.toSubpathPolygons():
        ring = np.array([(p.x(), p.y()) for p in poly], dtype=float).reshape(-1, 2)
        if len(ring) >= 2:
            edges.append(np.stack((ring, np.roll(ring, -1, axis=0)), axis=1))    # (closed: the last back to the first)
    if not edges or not len(segs):
        return np.zeros((0, 2, 2))
    edges = np.concatenate(edges)
    a, e = edges[:, 0], edges[:, 1] - edges[:, 0]
    out = []
    for k in range(0, len(segs), CLIP_CHUNK):
        chunk = segs[k:k + CLIP_CHUNK]
        p, d = chunk[:, 0], chunk[:, 1] - chunk[:, 0]
        w = a[None, :, :] - p[:, None, :]
        denom = d[:, None, 0] * e[None, :, 1] - d[:, None, 1] * e[None, :, 0]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (w[..., 0] * e[None, :, 1] - w[..., 1] * e[None, :, 0]) / denom     # (along the segment)
            u = (w[..., 0] * d[:, None, 1] - w[..., 1] * d[:, None, 0]) / denom     # (along the edge)
        hit = (np.abs(denom) > 1e-12) & (t > 0.0) & (t < 1.0) & (u >= 0.0) & (u <= 1.0)
        for start, along, ts, crossed in zip(p, d, t, hit):
            cuts = np.unique(np.concatenate(((0.0, 1.0), ts[crossed])))
            first = None
            for lo, hi in zip(cuts[:-1], cuts[1:]):
                mid = start + along * ((lo + hi) / 2.0)
                if path.contains(QtCore.QPointF(mid[0], mid[1])):
                    first = lo if first is None else first
                    last = hi
                elif first is not None:
                    out.append((start + along * first, start + along * last))
                    first = None
            if first is not None:
                out.append((start + along * first, start + along * last))
    return np.array(out, dtype=float).reshape(-1, 2, 2)


def _merged(boxes):
    """Boxes that overlap joined into one (so no line is drawn twice there)."""
    out = []
    for box in sorted(boxes, key=lambda b: (b.left(), b.top())):
        for k, kept in enumerate(out):
            if kept.intersects(box):
                out[k] = kept.united(box)
                break
        else:
            out.append(QtCore.QRectF(box))
    return out


def unit_of(key, mm):
    """Painter units a pattern unit, given how many make a millimetre on the paper (a model pattern drawn at 1:20)."""
    pattern = key if isinstance(key, core_patterns.Pattern) else core_patterns.get(key)
    return mm * (1000.0 / 20.0 if pattern is not None and pattern.model else 1.0)


def paint_pair(painter, path, background, foreground, mm, width=None):
    """A background and a foreground (each (pattern, colour) or None) in a path; mm: painter units a millimetre."""
    for value in (background, foreground):
        if value:
            key, colour = value
            paint(painter, path, key, colour, unit_of(key, mm), width or max(0.6, mm * 0.25))


def sample(background, foreground, size=(40, 24), base=None, mm=SAMPLE_MM):
    """A sample of a pair of patterns over a base colour (a QColor, or None: white), a QPixmap."""
    w, h = size
    image = QtGui.QPixmap(w, h)
    image.fill(QtGui.QColor(base) if base is not None else QtGui.QColor("white"))
    p = QtGui.QPainter(image)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    path = QtGui.QPainterPath()
    path.addRect(QtCore.QRectF(0, 0, w, h))
    paint_pair(p, path, background, foreground, mm, width=1.0)
    p.setPen(QtGui.QPen(QtGui.QColor("#9aa3ad"), 1.0))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRect(QtCore.QRectF(0.5, 0.5, w - 1, h - 1))
    p.end()
    return image


def name(key):
    """A pattern's name as shown (0.318: a project's its own)."""
    return core_patterns.label(key, t)


def icon(key, size=(40, 18)):
    """A pattern's little sample (a model pattern smaller: a few tiles, bricks)."""
    pattern = key if isinstance(key, core_patterns.Pattern) else core_patterns.get(key)
    model = pattern is not None and pattern.model
    return QtGui.QIcon(sample(None, (key, "#2b2f36"), size, mm=1.0 if model else SAMPLE_MM))


class PatternCombo(QtWidgets.QComboBox):
    """A list of the patterns, each with its sample: none first, then the drafting ones (measured on paper), then the
    model ones (measured on the building) — (0.318) each the program's and then the project's."""

    def __init__(self, parent=None, none_text=None):
        super().__init__(parent)
        self.setIconSize(QtCore.QSize(40, 18))
        self.none_text = none_text
        self.refill()

    def refill(self):
        """(0.318) The patterns again (the project's changed), the one chosen kept."""
        keep = self.currentData() if self.count() else None
        blocker = QtCore.QSignalBlocker(self)
        self.clear()
        self.addItem(self.none_text or name(None), None)
        for keys in (core_patterns.drafting_keys(),
                     tuple(k for k in core_patterns.model_keys() if k != core_patterns.SOLID)):
            self.insertSeparator(self.count())
            for key in keys:
                self.addItem(icon(key), name(key), key)
        self.setCurrentIndex(max(0, self.findData(keep)) if keep else 0)
        del blocker

    def key(self):
        return self.currentData()

    def set_key(self, key):
        self.setCurrentIndex(max(0, self.findData(key)) if key else 0)
