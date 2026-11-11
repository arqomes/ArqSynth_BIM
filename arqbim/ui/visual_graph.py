"""(0.540) The Visual Graph's window (PLANO.md, «Gráfico Visual», step 3): the nodes as cards with a live picture of
their result, wires dragged from an output to an input, the chosen node's measures as sliders on the right with its
result in big, the palette of nodes by family on the left. Opened by the «Gráfico Visual» icon of the left bar.

Everything is worked out by core/graph (the window only draws and edits): a change waits a moment (the slider still
moving) and then the graph is worked out again — only what changed."""

import json
import math

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..core.graph import FAMILIES, REGISTRY, Graph, GraphError
from . import theme

CARD_W = 190
TITLE_H = 24
THUMB_H = 112
PORT_GAP = 20
PORT_R = 6
PAPER = QtGui.QColor("#ffffff")          # (the drawings on white paper, whatever the theme)
INK = QtGui.QColor("#2b2f36")
FAMILY_COLOURS = {"Base": "#7d8794", "Padrões": "#2f6fe4", "Moduladores": "#8e5bd6", "Operações": "#e08a2e",
                  "Orgânico": "#3a9a6a", "Fabrico": "#c0453f", "BIM": "#2e8b57"}
KIND_COLOURS = {"panel": "#7d8794", "points": "#2f6fe4", "field": "#8e5bd6", "holes": "#e08a2e",
                "report": "#c0453f", "file": "#555555", "bim": "#2e8b57", "mesh": "#3a9a6a"}
DEFAULT_DOMAIN = (0.0, 0.0, 3.0, 1.2)


# ------------------------------------------------------------------ the pictures of the results
def domain_of(results, graph):
    """The panel the pictures are drawn on: the first «Painel plano»'s (else 3 × 1,2 m)."""
    for nid, node in graph.nodes.items():
        if node["type"] == "painel_plano" and nid in results:
            return results[nid]["painel"]["shape"].bounds
    return DEFAULT_DOMAIN


def picture(kind, value, w, h, domain=DEFAULT_DOMAIN):
    """A QImage of a result: the panel, its points, a field in greys, the holes (those that fail in red), the
    report's verdict, a file's name."""
    img = QtGui.QImage(int(w), int(h), QtGui.QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(PAPER)
    p = QtGui.QPainter(img)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    try:
        _draw(p, kind, value, w, h, domain)
    finally:
        p.end()
    return img


def _frame(w, h, bounds, pad=8):
    """(scale, ox, oy): metres to pixels, the panel centred, y up."""
    x0, y0, x1, y1 = bounds
    s = min((w - 2 * pad) / max(x1 - x0, 1e-9), (h - 2 * pad) / max(y1 - y0, 1e-9))
    ox = (w - (x1 - x0) * s) / 2.0 - x0 * s
    oy = (h + (y1 - y0) * s) / 2.0 + y0 * s
    return s, ox, oy


def _outline(p, shape, s, ox, oy, fill=None):
    path = QtGui.QPainterPath()
    for part in getattr(shape, "geoms", [shape]):
        for ring in [part.exterior, *part.interiors]:
            pts = [QtCore.QPointF(ox + x * s, oy - y * s) for x, y in ring.coords]
            path.addPolygon(QtGui.QPolygonF(pts))
    p.setBrush(fill if fill is not None else QtCore.Qt.BrushStyle.NoBrush)
    p.setPen(QtGui.QPen(INK, 1.0))
    p.drawPath(path)


def _draw(p, kind, value, w, h, domain):
    if value is None:
        return
    if kind == "panel":
        s, ox, oy = _frame(w, h, value["shape"].bounds)
        _outline(p, value["shape"], s, ox, oy, QtGui.QColor("#e9edf2"))
        p.setPen(QtGui.QPen(QtGui.QColor("#9aa3ad"), 1.0, QtCore.Qt.PenStyle.DashLine))
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        _outline_dashed(p, value["inside"], s, ox, oy)
    elif kind == "points":
        s, ox, oy = _frame(w, h, value["panel"]["shape"].bounds)
        _outline(p, value["panel"]["shape"], s, ox, oy)
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(QtGui.QColor(KIND_COLOURS["points"]))
        rr = max(1.0, min(2.5, value["pitch"] * s * 0.18))
        for x, y in value["xy"][:20000]:
            p.drawEllipse(QtCore.QPointF(ox + x * s, oy - y * s), rr, rr)
    elif kind == "field":
        s, ox, oy = _frame(w, h, domain)
        x0, y0, x1, y1 = domain
        cols, rows = max(int((x1 - x0) * s), 1), max(int((y1 - y0) * s), 1)
        step = max(1, int(max(cols, rows) / 160))
        gx = x0 + (np.arange(0, cols, step) + 0.5) / s
        gy = y1 - (np.arange(0, rows, step) + 0.5) / s
        X, Y = np.meshgrid(gx, gy)
        v = value(np.column_stack((X.ravel(), Y.ravel()))).reshape(X.shape)
        grey = (255 - v * 230).astype(np.uint8)
        rgb = np.ascontiguousarray(np.repeat(grey[:, :, None], 3, axis=2))
        im = QtGui.QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.shape[1] * 3, QtGui.QImage.Format.Format_RGB888)
        p.drawImage(QtCore.QRectF(ox + x0 * s, oy - y1 * s, (x1 - x0) * s, (y1 - y0) * s), im.copy())
    elif kind == "holes":
        panel = value["panel"]
        s, ox, oy = _frame(w, h, panel["shape"].bounds)
        _outline(p, panel["shape"], s, ox, oy, QtGui.QColor("#d9dee5"))
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        dark, red = QtGui.QColor("#1d2025"), QtGui.QColor(theme.ART["red"])
        bad = value.get("bad")
        shape = value["shape"]
        for k, ((x, y), d) in enumerate(zip(value["xy"][:20000], value["d"][:20000])):
            p.setBrush(red if bad is not None and len(bad) > k and bad[k] else dark)
            cx, cy, r = ox + x * s, oy - y * s, max(0.6, d * s / 2.0)
            if shape == "redondo":
                p.drawEllipse(QtCore.QPointF(cx, cy), r, r)
            elif shape == "quadrado":
                p.drawRect(QtCore.QRectF(cx - r, cy - r, 2 * r, 2 * r))
            else:
                rr = r * 2.0 / math.sqrt(3.0)
                p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(cx + rr * math.cos(math.radians(a)),
                                                              cy + rr * math.sin(math.radians(a)))
                                               for a in range(0, 360, 60)]))
    elif kind == "report":
        good = value["ok"]
        p.setPen(QtGui.QColor(theme.ART["green"] if good else theme.ART["red"]))
        f = p.font()
        f.setPixelSize(max(11, int(h / 7)))
        f.setBold(True)
        p.setFont(f)
        head = "Fabricável" if good else f"{value['bad']} furos a corrigir"
        p.drawText(QtCore.QRectF(6, 4, w - 12, h / 3), QtCore.Qt.AlignmentFlag.AlignCenter, head)
        f.setBold(False)
        f.setPixelSize(max(10, int(h / 10)))
        p.setFont(f)
        p.setPen(INK)
        bridge = value.get("min_bridge")
        lines = [f"{value['holes']} furos · área aberta {value['open_area'] * 100:.0f} %"]
        if bridge is not None:
            lines.append(f"ponte mais fina {bridge * 1000:.1f} mm")
        lines += value["problems"][:2]
        p.drawText(QtCore.QRectF(6, h / 3, w - 12, h * 2 / 3 - 4),
                   QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop, "\n".join(lines))
    elif kind == "mesh":
        _draw_mesh(p, value, w, h)
    elif kind in ("file", "bim"):
        p.setPen(INK)
        text = value if kind == "file" else "{} furos por painel\n{}".format(
            len(value["holes"]), "parede escolhida" if value["wall"] else "escolha a parede")
        p.drawText(QtCore.QRectF(6, 6, w - 12, h - 12), QtCore.Qt.AlignmentFlag.AlignCenter |
                   QtCore.Qt.TextFlag.TextWordWrap, str(text).replace("/", "/​"))


def _draw_mesh(p, mesh, w, h, limit=60000):
    """(0.542) A solid seen from the front, below and to the right (an axonometric), shaded by a light from the
    top left; the far faces first."""
    v, t = np.asarray(mesh["verts"], dtype=float), np.asarray(mesh["tris"])
    if not len(t):
        return
    if len(t) > limit:
        t = t[np.linspace(0, len(t) - 1, limit).astype(int)]
    yaw, pitch = math.radians(-28.0), math.radians(-32.0)
    cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    x, y, z = v[:, 0], v[:, 1], v[:, 2]
    xr = x * cy - z * sy                                   # (turned about the panel's upright axis…)
    zr = x * sy + z * cy
    yr = y * cp - zr * sp                                  # (…then tipped towards the eye)
    depth = y * sp + zr * cp
    lo, hi = np.array([xr.min(), yr.min()]), np.array([xr.max(), yr.max()])
    s, ox, oy = _frame(w, h, (lo[0], lo[1], hi[0], hi[1]))
    sx, syy = ox + xr * s, oy - yr * s
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    light = np.array([-0.4, 0.6, 0.7]) / np.linalg.norm([-0.4, 0.6, 0.7])
    shade = 0.35 + 0.65 * np.abs(n @ light)
    order = np.argsort(depth[t].mean(1))
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    base = np.array([196, 202, 210])
    for k in order:
        col = (base * shade[k]).astype(int)
        p.setBrush(QtGui.QColor(int(col[0]), int(col[1]), int(col[2])))
        i, j, m = t[k]
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(sx[i], syy[i]), QtCore.QPointF(sx[j], syy[j]),
                                       QtCore.QPointF(sx[m], syy[m])]))


def _outline_dashed(p, shape, s, ox, oy):
    for part in getattr(shape, "geoms", [shape]):
        for ring in [part.exterior, *part.interiors]:
            p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(ox + x * s, oy - y * s) for x, y in ring.coords]))


# ------------------------------------------------------------------ the canvas
class PortItem(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, card, group, port):
        super().__init__(-PORT_R, -PORT_R, 2 * PORT_R, 2 * PORT_R, card)
        self.card, self.group, self.port = card, group, port
        self.setBrush(QtGui.QColor(KIND_COLOURS.get(port.kind, "#888888")))
        self.setPen(QtGui.QPen(PAPER, 1.5))
        self.setToolTip(f"{port.label or port.name} ({port.kind})")
        self.setCursor(QtCore.Qt.CursorShape.CrossCursor)
        self.setZValue(2)

    def centre(self):
        return self.scenePos()


class LinkItem(QtWidgets.QGraphicsPathItem):
    def __init__(self, link, out_port, in_port):
        super().__init__()
        self.link, self.a, self.b = link, out_port, in_port
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setZValue(-1)
        self.update_path()

    def update_path(self):
        self.setPath(_wire(self.a.centre(), self.b.centre()))
        colour = QtGui.QColor(KIND_COLOURS.get(self.a.port.kind, "#888888"))
        self.setPen(QtGui.QPen(colour, 4.0 if self.isSelected() else 2.4))

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            QtCore.QTimer.singleShot(0, self.update_path)
        return super().itemChange(change, value)


def _wire(a, b):
    dx = max(40.0, abs(b.x() - a.x()) / 2.0)
    path = QtGui.QPainterPath(a)
    path.cubicTo(QtCore.QPointF(a.x() + dx, a.y()), QtCore.QPointF(b.x() - dx, b.y()), b)
    return path


class CardItem(QtWidgets.QGraphicsObject):
    """A node: its family's colour on its title, its result's picture, its inputs on the left, outputs on the
    right, its error (if any) in red under it."""
    moved = QtCore.Signal()

    def __init__(self, nid, spec):
        super().__init__()
        self.nid, self.spec = nid, spec
        self.image = None
        self.error = ""
        rows = max(len(spec.inputs), len(spec.outputs), 1)
        self.h = TITLE_H + THUMB_H + 8 + rows * PORT_GAP
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setToolTip(spec.description)
        self.inputs, self.outputs = {}, {}
        top = TITLE_H + THUMB_H + 8 + PORT_GAP / 2.0
        for k, port in enumerate(spec.inputs):
            it = PortItem(self, "inputs", port)
            it.setPos(0, top + k * PORT_GAP)
            self.inputs[port.name] = it
        for k, port in enumerate(spec.outputs):
            it = PortItem(self, "outputs", port)
            it.setPos(CARD_W, top + k * PORT_GAP)
            self.outputs[port.name] = it

    def boundingRect(self):
        return QtCore.QRectF(-PORT_R - 2, -2, CARD_W + 2 * PORT_R + 4, self.h + 22)

    def paint(self, p, _option, _widget=None):
        c = theme.C
        body = QtCore.QRectF(0, 0, CARD_W, self.h)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        border = theme.qcolor(c["select"]) if self.isSelected() else theme.qcolor(c["edge_2"])
        p.setPen(QtGui.QPen(border, 2.4 if self.isSelected() else 1.0))
        p.setBrush(theme.qcolor(c["window"]))
        p.drawRoundedRect(body, 7, 7)
        band = QtGui.QColor(FAMILY_COLOURS.get(self.spec.family, "#888888"))
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(band)
        p.drawRoundedRect(QtCore.QRectF(0, 0, CARD_W, TITLE_H), 7, 7)
        p.drawRect(QtCore.QRectF(0, TITLE_H / 2, CARD_W, TITLE_H / 2))
        p.setPen(QtGui.QColor("#ffffff"))
        f = p.font()
        f.setBold(True)
        f.setPixelSize(12)
        p.setFont(f)
        p.drawText(QtCore.QRectF(8, 0, CARD_W - 16, TITLE_H), QtCore.Qt.AlignmentFlag.AlignVCenter, self.spec.label)
        thumb = QtCore.QRectF(6, TITLE_H + 4, CARD_W - 12, THUMB_H)
        if self.image is not None:
            p.drawImage(thumb, self.image)
        else:
            p.fillRect(thumb, theme.qcolor(c["canvas"]))
        p.setPen(QtGui.QPen(theme.qcolor(c["edge"]), 1.0))
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.drawRect(thumb)
        f.setBold(False)
        f.setPixelSize(11)
        p.setFont(f)
        p.setPen(theme.qcolor(c["text"]))
        for name, it in self.inputs.items():
            p.drawText(QtCore.QRectF(10, it.y() - 8, CARD_W / 2, 16), QtCore.Qt.AlignmentFlag.AlignVCenter,
                       it.port.label or name)
        for name, it in self.outputs.items():
            p.drawText(QtCore.QRectF(CARD_W / 2 - 10, it.y() - 8, CARD_W / 2, 16),
                       QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignRight,
                       it.port.label or name)
        if self.error:
            p.setPen(QtGui.QColor(theme.ART["red"]))
            p.drawText(QtCore.QRectF(0, self.h + 2, CARD_W, 18), QtCore.Qt.AlignmentFlag.AlignLeft, "⚠ " + self.error)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.moved.emit()
        return super().itemChange(change, value)


class GraphView(QtWidgets.QGraphicsView):
    """The canvas: drag from an output to an input to join them; the wheel zooms; the middle button (or the empty
    canvas dragged) pans; Delete removes the chosen cards and wires."""
    link_made = QtCore.Signal(str, str, str, str)
    delete_pressed = QtCore.Signal()

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QtGui.QPainter.RenderHint.Antialiasing | QtGui.QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(theme.qcolor(theme.C["canvas"]))
        self._drag = None          # (port, temporary wire)
        self._pan = None

    def drawBackground(self, p, rect):
        super().drawBackground(p, rect)
        p.setPen(QtGui.QPen(theme.qcolor(theme.C["grid"]), 1.0))
        step = 24
        x = math.floor(rect.left() / step) * step
        while x < rect.right():
            p.drawLine(QtCore.QPointF(x, rect.top()), QtCore.QPointF(x, rect.bottom()))
            x += step
        y = math.floor(rect.top() / step) * step
        while y < rect.bottom():
            p.drawLine(QtCore.QPointF(rect.left(), y), QtCore.QPointF(rect.right(), y))
            y += step

    def _port_at(self, pos):
        for it in self.items(pos):
            if isinstance(it, PortItem):
                return it
        return None

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.MouseButton.MiddleButton:
            self._pan = e.position()
            return
        port = self._port_at(e.position().toPoint()) if e.button() == QtCore.Qt.MouseButton.LeftButton else None
        if port is not None and port.group == "outputs":
            wire = QtWidgets.QGraphicsPathItem()
            wire.setPen(QtGui.QPen(QtGui.QColor(KIND_COLOURS.get(port.port.kind, "#888888")), 2.4,
                                   QtCore.Qt.PenStyle.DashLine))
            self.scene().addItem(wire)
            self._drag = (port, wire)
            return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._pan is not None:
            d = e.position() - self._pan
            self._pan = e.position()
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - d.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - d.y()))
            return
        if self._drag is not None:
            port, wire = self._drag
            wire.setPath(_wire(port.centre(), self.mapToScene(e.position().toPoint())))
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._pan is not None and e.button() == QtCore.Qt.MouseButton.MiddleButton:
            self._pan = None
            return
        if self._drag is not None:
            port, wire = self._drag
            self._drag = None
            self.scene().removeItem(wire)
            target = self._port_at(e.position().toPoint())
            if target is not None and target.group == "inputs":
                self.link_made.emit(port.card.nid, port.port.name, target.card.nid, target.port.name)
            return
        super().mouseReleaseEvent(e)

    def wheelEvent(self, e):
        f = 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
        scale = self.transform().m11() * f
        if 0.2 < scale < 3.0:
            self.scale(f, f)

    def keyPressEvent(self, e):
        if e.key() in (QtCore.Qt.Key.Key_Delete, QtCore.Qt.Key.Key_Backspace):
            self.delete_pressed.emit()
            return
        super().keyPressEvent(e)


# ------------------------------------------------------------------ the measures of the chosen node
class ParamsPanel(QtWidgets.QWidget):
    """The chosen node's measures — sliders with their number beside, ticks, lists, file fields —, its result in big
    and its description."""
    changed = QtCore.Signal(str, str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.nid = None
        self.pick_wall = None                  # set by the window: () -> GlobalId of the wall chosen, or ""
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        self.title = QtWidgets.QLabel()
        f = self.title.font()
        f.setBold(True)
        f.setPointSize(f.pointSize() + 2)
        self.title.setFont(f)
        self.preview = QtWidgets.QLabel()
        self.preview.setMinimumSize(280, 180)
        self.preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.about = QtWidgets.QLabel()
        self.about.setWordWrap(True)
        self.about.setStyleSheet("color: %s;" % theme.qcolor(theme.C["muted"]).name())
        self.form_host = QtWidgets.QWidget()
        self.form = QtWidgets.QFormLayout(self.form_host)
        self.form.setContentsMargins(0, 4, 0, 4)
        outer.addWidget(self.title)
        outer.addWidget(self.preview)
        outer.addWidget(self.about)
        outer.addWidget(self.form_host)
        outer.addStretch(1)
        self.show_node(None, None)

    def show_node(self, nid, graph):
        self.nid = nid
        while self.form.rowCount():
            self.form.removeRow(0)
        if nid is None or graph is None or nid not in graph.nodes:
            self.title.setText("Nenhum nó escolhido")
            self.about.setText("Escolha um cartão para mudar as suas medidas. Junte nós pela lista à esquerda "
                               "(duplo clique) e ligue-os arrastando de uma saída (à direita do cartão) para uma "
                               "entrada (à esquerda).")
            self.preview.clear()
            return
        node = graph.nodes[nid]
        spec = graph.registry.get(node["type"])
        self.title.setText(spec.label)
        self.about.setText(spec.description + (f"\nExemplo: {spec.example}" if spec.example else ""))
        for port in spec.params:
            self.form.addRow(port.label or port.name, self._editor(port, node["params"][port.name], node["type"]))

    def show_picture(self, image):
        if image is None:
            self.preview.clear()
        else:
            self.preview.setPixmap(QtGui.QPixmap.fromImage(image))

    def _emit(self, name, value):
        if self.nid is not None:
            self.changed.emit(self.nid, name, value)

    def _editor(self, port, value, node_type):
        if port.kind in ("number", "int"):
            return self._slider(port, value)
        if port.kind == "bool":
            box = QtWidgets.QCheckBox()
            box.setChecked(bool(value))
            box.toggled.connect(lambda v, n=port.name: self._emit(n, v))
            return box
        if port.kind == "choice":
            combo = QtWidgets.QComboBox()
            combo.addItems(list(port.choices))
            combo.setCurrentText(str(value))
            combo.currentTextChanged.connect(lambda v, n=port.name: self._emit(n, v))
            return combo
        row = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        edit = QtWidgets.QLineEdit(str(value or ""))
        edit.editingFinished.connect(lambda e=edit, n=port.name: self._emit(n, e.text()))
        lay.addWidget(edit, 1)
        if port.name == "ficheiro":
            button = QtWidgets.QPushButton("Escolher…")
            saving = node_type == "exportar_dxf"
            button.clicked.connect(lambda _=False, e=edit, s=saving, n=port.name: self._choose_file(e, s, n))
            lay.addWidget(button)
        elif port.name == "parede":
            button = QtWidgets.QPushButton("Parede escolhida")
            button.setToolTip("Escolha uma parede no modelo e carregue aqui.")
            button.clicked.connect(lambda _=False, e=edit, n=port.name: self._wall(e, n))
            lay.addWidget(button)
        return row

    def _choose_file(self, edit, saving, name):
        if saving:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Gravar o DXF", edit.text() or "painel.dxf",
                                                            "DXF (*.dxf)")
        else:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Escolher a imagem", edit.text(),
                                                            "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff)")
        if path:
            edit.setText(path)
            self._emit(name, path)

    def _wall(self, edit, name):
        guid = self.pick_wall() if self.pick_wall else ""
        if not guid:
            QtWidgets.QMessageBox.information(self, "Gráfico Visual", "Escolha primeiro uma parede no modelo.")
            return
        edit.setText(guid)
        self._emit(name, guid)

    def _slider(self, port, value):
        row = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lo = port.min if port.min is not None else 0.0
        hi = port.max if port.max is not None else 100.0
        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setRange(0, 1000)
        if port.kind == "int":
            spin = QtWidgets.QSpinBox()
            spin.setRange(int(lo), int(hi))
        else:
            spin = QtWidgets.QDoubleSpinBox()
            step = port.step or (hi - lo) / 100.0
            spin.setDecimals(max(0, min(4, int(math.ceil(-math.log10(step))) if step < 1 else 0)))
            spin.setRange(lo, hi)
            spin.setSingleStep(step)
        if port.unit:
            spin.setSuffix(" " + port.unit)
        spin.setValue(value)
        to_slider = lambda v: int(round((v - lo) / max(hi - lo, 1e-12) * 1000))   # noqa: E731
        slider.setValue(to_slider(value))
        guard = [False]

        def from_slider(k):
            if guard[0]:
                return
            guard[0] = True
            v = lo + (hi - lo) * k / 1000.0
            if port.step:
                v = lo + round((v - lo) / port.step) * port.step
            spin.setValue(int(round(v)) if port.kind == "int" else v)
            guard[0] = False
            self._emit(port.name, spin.value())

        def from_spin(v):
            if guard[0]:
                return
            guard[0] = True
            slider.setValue(to_slider(v))
            guard[0] = False
            self._emit(port.name, v)
        slider.valueChanged.connect(from_slider)
        spin.valueChanged.connect(from_spin)
        spin.setMinimumWidth(92)
        lay.addWidget(slider, 1)
        lay.addWidget(spin)
        return row


# ------------------------------------------------------------------ the window
def starter_graph():
    """What the window opens with: a panel with hexagonal holes, bigger near an attractor, checked for
    fabrication and ready for a wall — something to see at once, and to change."""
    from ..core.graph import templates
    return templates.atrator_hexagono()


class GraphWindow(QtWidgets.QMainWindow):
    """The Visual Graph. `main`: the program's window (its model and its chosen wall) — None to use it alone."""

    def __init__(self, main=None, graph=None):
        super().__init__(main)
        self.setWindowFlag(QtCore.Qt.WindowType.Window)
        self.main = main
        self.setWindowTitle("Gráfico Visual — ArqSynth BIM")
        self.resize(1400, 820)
        self.path = None
        self.graph = graph or starter_graph()
        self.results = {}
        self.cards, self.wires = {}, []
        self.scene = QtWidgets.QGraphicsScene(self)
        self.view = GraphView(self.scene, self)
        self.setCentralWidget(self.view)
        self.view.link_made.connect(self._link)
        self.view.delete_pressed.connect(self.delete_chosen)
        self.scene.selectionChanged.connect(self._chosen)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(120)
        self.timer.timeout.connect(self.evaluate)
        self._build_palette()
        self._build_params()
        self._build_toolbar()
        self.status = self.statusBar()
        self.rebuild()
        self.evaluate()
        QtCore.QTimer.singleShot(0, lambda: self.view.fitInView(self.scene.itemsBoundingRect().adjusted(-40, -40, 40, 40),
                                                                QtCore.Qt.AspectRatioMode.KeepAspectRatio))

    # ---- around the canvas
    def _build_palette(self):
        dock = QtWidgets.QDockWidget("Nós", self)
        dock.setObjectName("graph_palette")
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.palette = QtWidgets.QTreeWidget()
        self.palette.setHeaderHidden(True)
        by_family = {}
        for spec in REGISTRY.catalog():
            by_family.setdefault(spec["family"], []).append(spec)
        for family in FAMILIES:
            if family not in by_family:
                continue
            top = QtWidgets.QTreeWidgetItem([family])
            top.setForeground(0, QtGui.QBrush(QtGui.QColor(FAMILY_COLOURS[family])))
            f = top.font(0)
            f.setBold(True)
            top.setFont(0, f)
            for spec in by_family[family]:
                it = QtWidgets.QTreeWidgetItem([spec["label"]])
                it.setData(0, QtCore.Qt.ItemDataRole.UserRole, spec["key"])
                it.setToolTip(0, spec["description"])
                top.addChild(it)
            self.palette.addTopLevelItem(top)
        self.palette.expandAll()
        self.palette.itemDoubleClicked.connect(lambda it, _c: self.add_from_palette(it))
        holder = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(holder)
        lay.setContentsMargins(4, 4, 4, 4)
        hint = QtWidgets.QLabel("Duplo clique para juntar um nó.")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addWidget(self.palette, 1)
        # (0.544) the chosen node at work: a short loop of its effect, and what it does
        self.demo = QtWidgets.QLabel()
        self.demo.setFixedHeight(130)
        self.demo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.demo_text = QtWidgets.QLabel()
        self.demo_text.setWordWrap(True)
        self.demo_text.setStyleSheet("color: %s;" % theme.qcolor(theme.C["muted"]).name())
        lay.addWidget(self.demo)
        lay.addWidget(self.demo_text)
        self._demo = None
        self.demo_timer = QtCore.QTimer(self)
        self.demo_timer.setInterval(110)
        self.demo_timer.timeout.connect(self._demo_step)
        self.palette.currentItemChanged.connect(lambda it, _old: self.show_demo(it))
        dock.setWidget(holder)
        dock.setMinimumWidth(190)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    DEMO_FRAMES = 24

    def show_demo(self, item):
        """(0.544) The palette's chosen node playing its loop (its measure swept there and back)."""
        from ..core.graph import examples
        self.demo_timer.stop()
        key = item.data(0, QtCore.Qt.ItemDataRole.UserRole) if item is not None else None
        if not key:
            self._demo = None
            self.demo.clear()
            self.demo_text.clear()
            return
        g, nid, sweep = examples.example(key)
        spec = REGISTRY.get(key)
        self._demo = [g, nid, sweep, 0]
        text = spec.description
        if sweep:
            p = spec.port("params", sweep[0])
            text += "\n(a variar: {})".format((p.label or p.name).lower())
        self.demo_text.setText(text)
        self._demo_step()
        if sweep:
            self.demo_timer.start()

    def _demo_step(self):
        from ..core.graph import examples
        if self._demo is None:
            return
        g, nid, sweep, k = self._demo
        if sweep:
            g.set_param(nid, sweep[0], examples.frame_value(sweep, k, self.DEMO_FRAMES))
            self._demo[3] = k + 1
        results = g.evaluate()
        out = results.get(nid)
        if out is None:
            self.demo.setText(g.errors.get(nid, ""))
            return
        port = g.registry.get(g.nodes[nid]["type"]).outputs[0]
        self.demo.setPixmap(QtGui.QPixmap.fromImage(picture(port.kind, out.get(port.name), 180, 122,
                                                            domain_of(results, g))))

    def _build_params(self):
        dock = QtWidgets.QDockWidget("Propriedades do nó", self)
        dock.setObjectName("graph_params")
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.params = ParamsPanel()
        self.params.changed.connect(self.set_param)
        self.params.pick_wall = self.chosen_wall
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.params)
        dock.setWidget(scroll)
        dock.setMinimumWidth(320)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _build_toolbar(self):
        bar = self.addToolBar("Gráfico")
        bar.setObjectName("graph_bar")
        bar.setMovable(False)
        bar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.act_new = bar.addAction("Novo", self.new_graph)
        self.act_open = bar.addAction("Abrir…", self.open_graph)
        self.act_save = bar.addAction("Gravar…", self.save_graph)
        from ..core.graph import templates                  # (0.541) ready graphs to start from
        button = QtWidgets.QToolButton()
        button.setText("Modelos ▾")
        button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QtWidgets.QMenu(button)
        for key, (name, about, _maker) in templates.TEMPLATES.items():
            act = menu.addAction(name, lambda k=key: self.load_template(k))
            act.setToolTip(about)
        menu.setToolTipsVisible(True)
        button.setMenu(menu)
        bar.addWidget(button)
        bar.addSeparator()
        self.act_fit = bar.addAction("Ver tudo", self.fit)
        bar.addSeparator()
        self.act_apply = bar.addAction("Aplicar ao modelo", self.apply_to_model)
        self.act_apply.setToolTip("Põe cada «Aplicar à parede/fachada» do gráfico como revestimento perfurado na sua "
                                  "parede.")
        self.act_apply.setEnabled(self.main is not None)

    # ---- the cards
    def rebuild(self):
        self.scene.clear()
        self.cards, self.wires = {}, []
        for nid, node in self.graph.nodes.items():
            self._card(nid, node)
        for link in self.graph.links:
            self._wire(link)

    def _card(self, nid, node):
        card = CardItem(nid, self.graph.registry.get(node["type"]))
        card.setPos(*node["pos"])
        card.moved.connect(lambda c=card: self._card_moved(c))
        self.scene.addItem(card)
        self.cards[nid] = card
        return card

    def _wire(self, link):
        f, o, t, i = link
        wire = LinkItem(link, self.cards[f].outputs[o], self.cards[t].inputs[i])
        self.scene.addItem(wire)
        self.wires.append(wire)

    def _card_moved(self, card):
        self.graph.nodes[card.nid]["pos"] = [card.pos().x(), card.pos().y()]
        for w in self.wires:
            if card.nid in (w.link[0], w.link[2]):
                w.update_path()

    def add_from_palette(self, item):
        key = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not key:
            return None
        centre = self.view.mapToScene(self.view.viewport().rect().center())
        nid = self.graph.add_node(key, pos=(centre.x() - CARD_W / 2 + 20 * (len(self.cards) % 5),
                                            centre.y() - 80 + 20 * (len(self.cards) % 5)))
        card = self._card(nid, self.graph.nodes[nid])
        self.scene.clearSelection()
        card.setSelected(True)
        self.schedule()
        return nid

    def _link(self, f, o, t, i):
        try:
            self.graph.connect(f, o, t, i)
        except (GraphError, KeyError) as e:
            self.status.showMessage(str(e), 6000)
            return
        for w in [w for w in self.wires if w.link[2] == t and w.link[3] == i]:
            self.scene.removeItem(w)
            self.wires.remove(w)
        self._wire((f, o, t, i))
        self.schedule()

    def delete_chosen(self):
        chosen = self.scene.selectedItems()
        for it in chosen:
            if isinstance(it, LinkItem) and it in self.wires:
                self.graph.disconnect(it.link[2], it.link[3])
        for it in chosen:
            if isinstance(it, CardItem):
                self.graph.remove_node(it.nid)
        self.rebuild()
        self.params.show_node(None, None)
        self.schedule()

    def _chosen(self):
        cards = [it for it in self.scene.selectedItems() if isinstance(it, CardItem)]
        nid = cards[0].nid if len(cards) == 1 else None
        if nid != self.params.nid:
            self.params.show_node(nid, self.graph)
        self._show_big()

    def set_param(self, nid, name, value):
        try:
            self.graph.set_param(nid, name, value)
        except (ValueError, GraphError) as e:
            self.status.showMessage(str(e), 6000)
            return
        self.schedule()

    # ---- working it out
    def schedule(self):
        self.timer.start()

    def evaluate(self):
        from ..core.graph import nodes_3d
        nodes_3d.MODEL["doc"] = getattr(self.main, "doc", None)     # (0.542) «Fachada do modelo» reads it
        try:
            self.results = self.graph.evaluate()
        except GraphError as e:
            self.status.showMessage(str(e), 6000)
            return
        domain = domain_of(self.results, self.graph)
        for nid, card in self.cards.items():
            spec = card.spec
            out = self.results.get(nid)
            card.error = self.graph.errors.get(nid, "")
            if out is not None and spec.key == "verificar_fabrico" and not out["relatorio"]["ok"]:
                card.error = "{} furos a corrigir (a vermelho)".format(out["relatorio"]["bad"])   # (0.541)
            cached = self.graph._cache.get(nid)
            key = (cached[0] if cached and out is not None else None, domain)
            if key[0] is not None and getattr(card, "drawn", None) == key:
                card.update()                                  # (its result as it was: its picture kept)
                continue
            card.drawn = key
            card.image = None
            if out is not None and spec.outputs:
                port = spec.outputs[0]
                card.image = picture(port.kind, out.get(port.name), CARD_W - 12, THUMB_H, domain)
            card.update()
        self._show_big()
        bad = len(self.graph.errors)
        self.status.showMessage("Calculado." if not bad else f"{bad} nós com avisos (ver a vermelho).", 4000)

    def _show_big(self):
        nid = self.params.nid
        out = self.results.get(nid) if nid else None
        if out is None:
            self.params.show_picture(None)
            return
        spec = self.graph.registry.get(self.graph.nodes[nid]["type"])
        port = spec.outputs[-1]            # (the check: its report in big — the card shows its holes)
        w = max(280, self.params.preview.width())
        self.params.show_picture(picture(port.kind, out.get(port.name), w, int(w * 0.62),
                                         domain_of(self.results, self.graph)))

    # ---- files
    def new_graph(self):
        self.graph = Graph()
        self.path = None
        self.rebuild()
        self.params.show_node(None, None)
        self.evaluate()

    def load_template(self, key):
        """(0.541) A ready graph in place of this one — the picture one asks for its picture first."""
        from ..core.graph import templates
        kw = {}
        if key == "imagem_painel":
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Escolher a imagem (escuro = furos grandes)", "",
                "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff)")
            kw["ficheiro"] = path or ""
        self.graph = templates.make(key, **kw)
        self.path = None
        self.rebuild()
        self.params.show_node(None, None)
        self.evaluate()
        self.fit()
        image = next((n for n, d in self.graph.nodes.items() if d["type"] == "imagem"), None)
        if image is not None and image in self.cards:          # (its measures in view: the picture can be chosen)
            self.cards[image].setSelected(True)

    def open_graph(self, path=None):
        if not path:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Abrir gráfico", "", "Gráfico ArqSynth (*.json)")
        if not path:
            return False
        try:
            with open(path, encoding="utf-8") as fh:
                self.graph = Graph.from_json(fh.read())
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
            QtWidgets.QMessageBox.warning(self, "Gráfico Visual", f"Não foi possível abrir:\n{e}")
            return False
        self.path = path
        self.rebuild()
        self.params.show_node(None, None)
        self.evaluate()
        self.fit()
        return True

    def save_graph(self, path=None):
        if not path:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Gravar gráfico", self.path or "painel.json",
                                                            "Gráfico ArqSynth (*.json)")
        if not path:
            return False
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.graph.to_json())
        self.path = path
        self.status.showMessage(f"Gravado em {path}", 5000)
        return True

    def fit(self):
        rect = self.scene.itemsBoundingRect()
        if not rect.isEmpty():
            self.view.fitInView(rect.adjusted(-40, -40, 40, 40), QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    # ---- the model
    def chosen_wall(self):
        """The GlobalId of the wall chosen in the model ("" if none)."""
        if self.main is None:
            return ""
        doc = self.main.doc
        for guid in list(self.main.viewport.selection):
            try:
                if doc.ifc.kind_of(guid) == "wall":
                    return guid
            except Exception:  # (an id not of the IFC: a sketch, a dimension)
                continue
        return ""

    def apply_to_model(self):
        """Each «Aplicar à parede/fachada» worked out: its panel as a perforated finish on its wall."""
        if self.main is None:
            return []
        from ..core.graph.nodes_panels import cladding_pattern
        from ..model import bim
        made, problems = [], []
        for nid, node in self.graph.nodes.items():
            if node["type"] != "aplicar_parede":
                continue
            out = (self.results.get(nid) or {}).get("bim")
            if out is None:
                problems.append(self.graph.errors.get(nid, "nó por calcular"))
                continue
            wall = out["wall"] or self.chosen_wall()
            if not wall:
                problems.append("escolha a parede (no modelo, e depois «Parede escolhida» no nó)")
                continue
            side = 1 if out["side"] == "frente" else -1
            try:
                made.append(bim.add_cladding(self.main.doc, wall, side, "perfurado", 0.0, cladding_pattern(out)))
            except ValueError as e:
                problems.append(str(e))
        if problems:
            QtWidgets.QMessageBox.warning(self, "Gráfico Visual", "Não aplicado:\n" + "\n".join(problems))
        if made:
            self.status.showMessage(f"{len(made)} painel(éis) perfurado(s) aplicado(s) ao modelo.", 6000)
        return made
