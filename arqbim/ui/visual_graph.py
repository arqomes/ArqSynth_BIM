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
        if node["type"] in ("painel_plano", "fachada_bim") and nid in results:      # (0.542: the surface too)
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
        _holes(p, value["shape"], value["xy"], value["d"], s, ox, oy, value.get("bad"), 20000,
               *_extras_of(value))
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


# ------------------------------------------------------------------ the result on the surface (0.541)
RANK = {"mesh": 5, "bim": 4, "holes": 3, "points": 2, "field": 1, "panel": 1}
WALL = QtGui.QColor("#cfd4da")


def final_result(graph, results):
    """(node id, kind, value) of what the graph ends in — what the surface shows: the solid, else the panel on its
    wall, else the holes, the points, the modulator, the bare surface. The last of the best kind; None: nothing."""
    best = None
    for nid in graph.order():
        out = results.get(nid)
        spec = graph.registry.get(graph.nodes[nid]["type"])
        if out is None or not spec.outputs:
            continue
        port = spec.outputs[0]
        rank = RANK.get(port.kind, 0)
        if rank and (best is None or rank >= best[0]):
            best = (rank, nid, port.kind, out.get(port.name))
    return None if best is None else best[1:]


def _holes(p, shape, xy, d, s, ox, oy, bad=None, limit=40000, angle=None, ratio=None):
    """(0.545) `angle`, `ratio`: each hole's turn (°) and stretch — None: as the sizes carry them (surfaces.extras)."""
    from ..core import surfaces
    dark, red = QtGui.QColor("#1d2025"), QtGui.QColor(theme.ART["red"])
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    if angle is None or ratio is None:
        angle, ratio = surfaces.extras(d)
    angle, ratio = np.asarray(angle, dtype=float), np.asarray(ratio, dtype=float)
    plain = shape in ("redondo", "quadrado", "hexagonal") and not np.any(angle) and np.allclose(ratio, 1.0)
    rings = None if plain else surfaces.hole_rings(shape, xy[:limit], d[:limit], angle[:limit], ratio[:limit])
    for k, ((x, y), size) in enumerate(zip(xy[:limit], d[:limit])):
        p.setBrush(red if bad is not None and len(bad) > k and bad[k] else dark)
        cx, cy, r = ox + x * s, oy - y * s, max(0.6, size * s / 2.0)
        if rings is not None:
            p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(ox + u * s, oy - v * s) for u, v in rings[k]]))
        elif shape == "redondo":
            p.drawEllipse(QtCore.QPointF(cx, cy), r, r)
        elif shape == "quadrado":
            p.drawRect(QtCore.QRectF(cx - r, cy - r, 2 * r, 2 * r))
        else:
            rr = r * 2.0 / math.sqrt(3.0)
            p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(cx + rr * math.cos(math.radians(a)),
                                                          cy + rr * math.sin(math.radians(a)))
                                           for a in range(0, 360, 60)]))


def _extras_of(holes):
    from ..core.graph.nodes_panels import hole_extras
    return hole_extras(holes)


def _draw_applied(p, value, w, h, source=None):
    """The panel as it will stand on its wall's face (the example face: no wall): the face with its doors and
    windows, the boards, every hole — those «Verificar fabrico» refused in red (the face covered whole)."""
    from ..core import surfaces
    from ..core.graph import nodes_3d
    try:
        face = nodes_3d.target_face(value["wall"], value.get("side", "frente"))
    except ValueError:
        face = nodes_3d.example_face()
    if value.get("mirror") and source is not None:   # (0.546) the back face as one sees it: the holes as drawn
        face = nodes_3d.mirrored(face)
    s, ox, oy = _frame(w, h, face.bounds, pad=14)
    _outline(p, face, s, ox, oy, WALL)
    panel = value["panel"]
    holes = surfaces.hole_rows(value["holes"])
    if not value["repeat"] and source is not None and len(source["xy"]) == len(holes):
        _holes(p, value["shape"], source["xy"], source["d"], s, ox, oy, source.get("bad"), 40000,
               *_extras_of(source))
        return
    found = surfaces.free_perforation(face, value["shape"], holes, panel["margin"],
                                      (panel["width"], panel["height"]), bool(value["repeat"]))
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    for board, centres, sizes in found:
        p.setPen(QtGui.QPen(QtGui.QColor("#7d8794"), 1.0))
        _outline_dashed(p, board, s, ox, oy)
        _holes(p, value["shape"], centres, sizes, s, ox, oy)


def surface_picture(graph, results, w, h, nid=None):
    """(0.541) The picture of the surface being worked on: what the graph ends in (`nid`: that node's result
    instead) drawn on it."""
    img = QtGui.QImage(int(w), int(h), QtGui.QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(PAPER)
    found = None
    if nid is not None and results.get(nid) is not None:
        spec = graph.registry.get(graph.nodes[nid]["type"])
        if spec.outputs and spec.outputs[0].kind in RANK:
            found = (nid, spec.outputs[0].kind, results[nid].get(spec.outputs[0].name))
    found = found or final_result(graph, results)
    if found is None:
        return img
    node, kind, value = found
    p = QtGui.QPainter(img)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    try:
        if kind == "bim":
            link = next((l for l in graph.links if l[2] == node and l[3] == "furos"), None)
            source = results.get(link[0], {}).get(link[1]) if link else None
            _draw_applied(p, value, w, h, source)
        else:
            _draw(p, kind, value, w, h, domain_of(results, graph))
    finally:
        p.end()
    return img


SHEET_RGBA = (0.80, 0.83, 0.87, 0.93)
HOLE_RGBA = (0.10, 0.11, 0.13, 0.96)
BAD_RGBA = (0.85, 0.20, 0.18, 0.98)
MODEL_HOLES = 25000                 # more than this: the sheet alone is shown in the model (the editor shows all)


def model_preview(doc, value, bad=None):
    """(0.547) The panel as it will stand on its wall, for the model's own 3D view: (triangles (n, 3, 3) world,
    colours (n, 4)) — the sheet over the wall's face and each hole dark on it (red: refused by the check). Flat (no
    thickness cut): light enough to follow a slider. None: nothing to show (no wall, the wall gone)."""
    import shapely

    from ..core import surfaces
    from ..core.graph import nodes_3d
    wall = value.get("wall")
    if doc is None or not wall:
        return None
    front = value["side"] == "frente"
    flat = None                                          # (0.549) a ceiling, a slab: (its placement, its level)
    try:
        curved = nodes_3d.is_curved(doc, wall)
        kind = doc.ifc.kind_of(wall)
        if kind == "ceiling":
            face, frame = doc.ifc.ceiling_face(wall), None
            flat = (doc.ifc._placement_si(doc.ifc.by_guid(wall)), 0.0)
        elif kind == "slab":
            from shapely.geometry import Polygon

            from ..model.bim import CEILING_DROP
            info = doc.ifc.slab_outline(wall)
            face, frame = Polygon(info["outline"], info["holes"]).buffer(0), None
            flat = (np.eye(4), float(info["bottom"]) - CEILING_DROP)
        elif curved:                                     # (0.548) its face unrolled, the sheet bent round it
            frame, face, radius, turn = doc.ifc.curved_face(wall, 1 if front else -1)
        else:
            face = nodes_3d.wall_face(doc, wall)
            frame = doc.ifc.element_frame(wall)
    except Exception:  # (the wall gone meanwhile)
        return None
    panel = value["panel"]
    found = surfaces.free_perforation(face, value["shape"], value["holes"], panel["margin"],
                                      (panel["width"], panel["height"]), bool(value["repeat"]))
    lift = max(float(panel["thickness"]), 0.004)
    step = surfaces.strip_step(radius, frame.length) if curved else None

    def world(uv, off):
        if flat is not None:                             # (seen from under it: a hair under its underside)
            local = np.column_stack((uv, np.full(len(uv), flat[1] - off), np.ones(len(uv))))
            return (flat[0] @ local.T).T[:, :3]
        if curved:
            local = surfaces.bend(np.column_stack((uv, np.full(len(uv), off))), radius, turn,
                                  -1.0 if front else 1.0, step)
            local = np.column_stack((local, np.ones(len(uv))))
        else:
            y = frame.y1 + off if front else frame.y0 - off
            local = np.column_stack((frame.x0 + uv[:, 0], np.full(len(uv), y), frame.z0 + uv[:, 1],
                                     np.ones(len(uv))))
        return (frame.matrix @ local.T).T[:, :3]

    tris, colours = [], []
    for part in getattr(face, "geoms", [face]):
        if part.geom_type != "Polygon" or part.area < 1e-8:
            continue
        cut = shapely.constrained_delaunay_triangles(part)
        t = np.array([np.asarray(g.exterior.coords)[:3] for g in cut.geoms]).reshape(-1, 2)
        if curved:                                       # (fine enough along the arc to follow it)
            unrolled = np.column_stack((t, np.zeros(len(t))))
            unrolled, index = surfaces.split_strips(unrolled, np.arange(len(t)).reshape(-1, 3), step)
            t = unrolled[index].reshape(-1, 3)[:, :2]
        tris.append(world(t, lift).reshape(-1, 3, 3))
        colours.append(np.tile(SHEET_RGBA, (len(t) // 3, 1)))
    total = sum(len(c) for _q, c, _s in found)
    if total <= MODEL_HOLES:
        flags = None if bad is None or value["repeat"] or len(bad) != total else np.asarray(bad, dtype=bool)
        done = 0
        for _board, centres, sizes in found:
            if not len(centres):
                continue
            angle, ratio = surfaces.extras(sizes)
            for k, ring in enumerate(surfaces.hole_rings(value["shape"], centres, sizes, angle, ratio)):
                n = len(ring)
                fan = np.empty((n, 3, 2))
                fan[:, 0], fan[:, 1], fan[:, 2] = centres[k], ring, np.roll(ring, -1, axis=0)
                tris.append(world(fan.reshape(-1, 2), lift + 0.002).reshape(-1, 3, 3))
                red = flags is not None and flags[done + k]
                colours.append(np.tile(BAD_RGBA if red else HOLE_RGBA, (n, 1)))
            done += len(centres)
    if not tris:
        return None
    return np.concatenate(tris), np.concatenate(colours)


def png_bytes(image):
    data = QtCore.QByteArray()
    buffer = QtCore.QBuffer(data)
    buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(data)


def operator_png(graph, w=240, h=152):
    """An operator's thumbnail: its result on the example face."""
    from ..core.graph import operators
    operators.retarget(graph, "")
    return png_bytes(surface_picture(graph, graph.evaluate(), w, h))


_THUMBS = {}
# (0.542) measures that show a node best in its small picture, where its own would not tell it from its input
THUMB_PARAMS = {"remapear": {"degraus": 3}, "desalinhar": {"quanto": 0.9}, "escalar_furos": {"fator": 0.4},
                "contorno_pontos": {"passo": 0.1, "distancia": 0.15, "filas": 2}, "area_aberta": {"alvo": 45.0},
                "corrigir_fabrico": {"ponte_min": 0.08}}


def node_thumb(key, w=96, h=60):
    """(0.541) A node's small picture of what it does (its example worked out once), for the Shift+A menu."""
    if key not in _THUMBS:
        from ..core.graph import examples
        image = None
        try:
            g, nid, _sweep = examples.example(key)
            for node in g.nodes.values():               # (few and big: read at a glance in a small picture)
                if "passo" in node["params"]:
                    node["params"]["passo"] = 0.2
                if node["type"] == "perfurar":
                    node["params"].update(d_min=0.03, d_max=0.17)
                    if key in ("rodar_furos", "alongar_furos"):     # (0.545) seen on slots: round ones do not show
                        node["params"].update(forma="ranhura", d_min=0.04, d_max=0.05, alongar=2.5)
            g.nodes[nid]["params"].update(THUMB_PARAMS.get(key, {}))
            results = g.evaluate()
            out = results.get(nid)
            port = g.registry.get(g.nodes[nid]["type"]).outputs[0]
            if out is not None:
                image = picture(port.kind, out.get(port.name), w, h, domain_of(results, g))
        except Exception:  # (a node with no example: its name alone)
            image = None
        _THUMBS[key] = image
    return _THUMBS[key]


class SurfacePreview(QtWidgets.QWidget):
    """The surface being worked on, with the graph's result on it — redrawn whenever the graph is worked out."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 200)
        self.image = None
        self.source = None                       # () -> QImage of (w, h)

    def refresh(self):
        self.image = None
        self.update()

    def resizeEvent(self, e):
        self.image = None
        super().resizeEvent(e)

    def paintEvent(self, _e):
        p = QtGui.QPainter(self)
        if self.image is None and self.source is not None:
            self.image = self.source(self.width(), self.height())
        if self.image is not None:
            p.drawImage(0, 0, self.image)
        else:
            p.fillRect(self.rect(), PAPER)
        p.setPen(QtGui.QPen(theme.qcolor(theme.C["edge"]), 1.0))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))


class NodeMenu(QtWidgets.QFrame):
    """(0.541, the owner: «Podemos optar pela tecla Shift+A para inserir os nós. As opções poderiam vir com nomes e
    representação visual do que o comando faz») The menu of nodes at the mouse: each with its picture and name, by
    family; typing narrows it; Enter (or a click) puts the node where the mouse was."""
    chosen = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.WindowType.Popup)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Procurar nó… (escreva o nome)")
        self.search.textChanged.connect(self._filter)
        self.search.installEventFilter(self)
        self.list = QtWidgets.QListWidget()
        self.list.setIconSize(QtCore.QSize(96, 60))
        self.list.itemClicked.connect(self._pick)
        self.list.itemActivated.connect(self._pick)
        self.list.currentItemChanged.connect(lambda it, _old: self._about(it))
        self.about = QtWidgets.QLabel()
        self.about.setWordWrap(True)
        self.about.setMinimumHeight(48)
        self.about.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.about.setStyleSheet("color: %s;" % theme.qcolor(theme.C["muted"]).name())
        lay.addWidget(self.search)
        lay.addWidget(self.list, 1)
        lay.addWidget(self.about)
        self.resize(330, 520)
        by_family = {}
        for spec in REGISTRY.catalog():
            by_family.setdefault(spec["family"], []).append(spec)
        for family in FAMILIES:
            if family not in by_family:
                continue
            head = QtWidgets.QListWidgetItem(family.upper())
            head.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
            head.setForeground(QtGui.QBrush(QtGui.QColor(FAMILY_COLOURS[family])))
            f = head.font()
            f.setBold(True)
            head.setFont(f)
            self.list.addItem(head)
            for spec in by_family[family]:
                item = QtWidgets.QListWidgetItem(spec["label"])
                item.setData(QtCore.Qt.ItemDataRole.UserRole, spec["key"])
                item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, spec["description"])
                thumb = node_thumb(spec["key"])
                if thumb is not None:
                    item.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(thumb)))
                self.list.addItem(item)

    def keys(self):
        """The nodes in view (not narrowed away), in order."""
        return [self.list.item(k).data(QtCore.Qt.ItemDataRole.UserRole) for k in range(self.list.count())
                if not self.list.item(k).isHidden() and self.list.item(k).data(QtCore.Qt.ItemDataRole.UserRole)]

    def open_at(self, point):
        from . import menus
        self.search.clear()
        self._filter("")
        screen = QtGui.QGuiApplication.screenAt(point) or QtGui.QGuiApplication.primaryScreen()
        if screen is not None:                       # (wholly on the screen, clear of the taskbar's room)
            area = screen.availableGeometry()
            point = QtCore.QPoint(min(point.x(), area.right() - self.width()),
                                  max(area.top(), min(point.y(), area.bottom() - menus.TASKBAR_PX - self.height())))
        self.move(point)
        self.show()
        self.search.setFocus()

    def _filter(self, text):
        text = str(text).strip().lower()
        first = None
        for k in range(self.list.count()):
            item = self.list.item(k)
            key = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if not key:
                item.setHidden(bool(text))
                continue
            hit = not text or text in item.text().lower() or text in \
                str(item.data(QtCore.Qt.ItemDataRole.UserRole + 1)).lower()
            item.setHidden(not hit)
            if hit and first is None:
                first = item
        self.list.setCurrentItem(first)

    def _about(self, item):
        self.about.setText(str(item.data(QtCore.Qt.ItemDataRole.UserRole + 1) or "") if item is not None else "")

    def _pick(self, item):
        key = item.data(QtCore.Qt.ItemDataRole.UserRole) if item is not None else None
        if key:
            self.hide()
            self.chosen.emit(key)

    def eventFilter(self, obj, event):
        if obj is self.search and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() in (QtCore.Qt.Key.Key_Down, QtCore.Qt.Key.Key_Up):
                step = 1 if event.key() == QtCore.Qt.Key.Key_Down else -1
                k = self.list.currentRow()
                while 0 <= k + step < self.list.count():
                    k += step
                    item = self.list.item(k)
                    if not item.isHidden() and item.data(QtCore.Qt.ItemDataRole.UserRole):
                        self.list.setCurrentItem(item)
                        break
                return True
            if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                self._pick(self.list.currentItem())
                return True
        return super().eventFilter(obj, event)


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
        try:
            self.setPath(_wire(self.a.centre(), self.b.centre()))
        except RuntimeError:            # (asked for just before the canvas was drawn anew: its cards are gone)
            return
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
    add_requested = QtCore.Signal(QtCore.QPoint, QtCore.QPointF)

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
        if e.key() == QtCore.Qt.Key.Key_A and e.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
            self.ask_node()                                 # (0.541) Shift+A: the menu of nodes at the mouse
            return
        super().keyPressEvent(e)

    def ask_node(self):
        """The menu of nodes asked for where the mouse is (the canvas's middle: the mouse elsewhere)."""
        here = self.viewport().mapFromGlobal(QtGui.QCursor.pos())
        if not self.viewport().rect().contains(here):
            here = self.viewport().rect().center()
        self.add_requested.emit(self.viewport().mapToGlobal(here), self.mapToScene(here))

    def contextMenuEvent(self, e):
        if self.itemAt(e.pos()) is None:                    # (the right button on the empty canvas: the same menu)
            self.add_requested.emit(e.globalPos(), self.mapToScene(e.pos()))
            return
        super().contextMenuEvent(e)


# ------------------------------------------------------------------ the measures of the chosen node
class ParamsPanel(QtWidgets.QWidget):
    """The chosen node's measures — sliders with their number beside, ticks, lists, file fields —, its result in big
    and its description."""
    changed = QtCore.Signal(str, str, object)
    expose = QtCore.Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.nid = None
        self.exposed = None                    # (0.543) the window's list of (node id, measure) in sight — or None
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
            self.about.setText("Escolha um cartão para mudar as suas medidas. Junte nós com Shift+A (ou o botão "
                               "direito na tela) e ligue-os arrastando de uma saída (à direita do cartão) para uma "
                               "entrada (à esquerda).")
            self.preview.clear()
            return
        node = graph.nodes[nid]
        spec = graph.registry.get(node["type"])
        self.title.setText(spec.label)
        self.about.setText(spec.description + (f"\nExemplo: {spec.example}" if spec.example else ""))
        for port in spec.params:
            editor = self._editor(port, node["params"][port.name], node["type"])
            if self.exposed is not None and port.kind in ("number", "int", "bool", "choice"):
                # (0.543) «à vista»: this measure stands in the BIM's side panel, changed without the editor
                row = QtWidgets.QWidget()
                lay = QtWidgets.QHBoxLayout(row)
                lay.setContentsMargins(0, 0, 0, 0)
                pin = QtWidgets.QCheckBox("à vista")
                pin.setToolTip("Mostrar esta medida no painel lateral «Operadores», para a mudar sem abrir o "
                               "Gráfico Visual.")
                pin.setChecked((nid, port.name) in self.exposed)
                pin.toggled.connect(lambda on, n=port.name: self.expose.emit(self.nid, n, on))
                lay.addWidget(editor, 1)
                lay.addWidget(pin)
                editor = row
            self.form.addRow(port.label or port.name, editor)

    def show_picture(self, image):
        if image is None:
            self.preview.clear()
        else:
            self.preview.setPixmap(QtGui.QPixmap.fromImage(image))

    def _emit(self, name, value):
        if self.nid is not None:
            self.changed.emit(self.nid, name, value)

    def _editor(self, port, value, node_type, emit=None):
        """`emit(name, value)`: where a change goes (the node shown: its own; 0.543: the side panel's)."""
        emit = emit or self._emit
        if port.kind in ("number", "int"):
            return self._slider(port, value, emit)
        if port.kind == "bool":
            box = QtWidgets.QCheckBox()
            box.setChecked(bool(value))
            box.toggled.connect(lambda v, n=port.name: emit(n, v))
            return box
        if port.kind == "choice":
            combo = QtWidgets.QComboBox()
            combo.addItems(list(port.choices))
            combo.setCurrentText(str(value))
            combo.setMinimumWidth(40)
            combo.currentTextChanged.connect(lambda v, n=port.name: emit(n, v))
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

    def _slider(self, port, value, emit=None):
        emit = emit or self._emit
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
            emit(port.name, spin.value())

        def from_spin(v):
            if guard[0]:
                return
            guard[0] = True
            slider.setValue(to_slider(v))
            guard[0] = False
            emit(port.name, v)
        slider.valueChanged.connect(from_slider)
        spin.valueChanged.connect(from_spin)
        spin.setMinimumWidth(92)
        slider.setMinimumWidth(90)                 # (0.545: beside «à vista» it was squeezed to nothing)
        lay.addWidget(slider, 1)
        lay.addWidget(spin)
        return row


# ------------------------------------------------------------------ the window
def starter_graph():
    """What the window opens with: a panel with hexagonal holes, bigger near an attractor, checked for
    fabrication and ready for a wall — something to see at once, and to change."""
    from ..core.graph import operators
    return operators.starter()


class GraphWindow(QtWidgets.QMainWindow):
    """The Visual Graph: an operator's editor. `main`: the program's window (its model and its chosen wall) — None
    to use it alone. (0.541) `slug`/`name`: the library's operator being edited (None: a new one); `wall`, `side`:
    the wall's face it is worked on (""/"frente": the example face)."""

    def __init__(self, main=None, graph=None, slug=None, name="", wall="", side="frente", exposed=(), cladding=None):
        """(0.543) `exposed`: the operator's measures in sight in the side panel; `cladding`: the wall's finish
        being edited («Aplicar ao modelo» works it again instead of making another)."""
        super().__init__(main)
        self.exposed = [tuple(p) for p in exposed]
        self.cladding = cladding
        self._undo, self._redo, self._last_set = [], [], None
        self.setWindowFlag(QtCore.Qt.WindowType.Window)
        self.main = main
        self.resize(1500, 860)
        self.path = None
        self.slug, self.name = slug, name
        self.wall, self.side = wall or "", side or "frente"
        self.graph = graph or starter_graph()
        from ..core.graph import nodes_3d, operators
        nodes_3d.MODEL["doc"] = getattr(main, "doc", None)
        operators.retarget(self.graph, self.wall, self.side)
        self.node_menu = None
        self._drop = None                       # (where the node asked for by Shift+A goes)
        self.results = {}
        self.cards, self.wires = {}, []
        self.scene = QtWidgets.QGraphicsScene(self)
        self.view = GraphView(self.scene, self)
        self.setCentralWidget(self.view)
        self.view.link_made.connect(self._link)
        self.view.delete_pressed.connect(self.delete_chosen)
        self.view.add_requested.connect(self.ask_node)
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
        """(0.541, the owner: «A superfície fica visível numa tela, enquanto trabalho com os nós, fica a
        previsualização na superfície») The left side: the surface being worked on with the graph's result on it,
        alive; what it is (the wall, its face); the fabrication's verdict under it. The list of nodes that stood
        here is the Shift+A menu now."""
        dock = QtWidgets.QDockWidget("Superfície", self)
        dock.setObjectName("graph_surface")
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        holder = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(holder)
        lay.setContentsMargins(6, 6, 6, 6)
        self.target_label = QtWidgets.QLabel()
        self.target_label.setWordWrap(True)
        f = self.target_label.font()
        f.setBold(True)
        self.target_label.setFont(f)
        lay.addWidget(self.target_label)
        self.surface = SurfacePreview()
        self.surface.source = lambda w, h: surface_picture(self.graph, self.results, w, h, self._shown_node())
        lay.addWidget(self.surface, 1)
        self.show_final = QtWidgets.QCheckBox("Mostrar sempre o resultado final")
        self.show_final.setChecked(True)
        self.show_final.setToolTip("Ligado: a superfície mostra sempre o fim do gráfico. Desligado: mostra o "
                                   "resultado do cartão escolhido.")
        self.show_final.toggled.connect(lambda _on: self.surface.refresh())
        lay.addWidget(self.show_final)
        # (0.547) the panel on its wall in the model's own 3D view, following each change
        self.in_model = QtWidgets.QCheckBox("Ver também na vista 3D do modelo")
        self.in_model.setChecked(True)
        self.in_model.setToolTip("Mostra o painel sobre a parede, na vista do modelo, enquanto trabalha. É só para "
                                 "ver: fica na parede com «Aplicar ao modelo».")
        self.in_model.toggled.connect(lambda _on: self._show_in_model())
        lay.addWidget(self.in_model)
        self.verdict = QtWidgets.QLabel()
        self.verdict.setWordWrap(True)
        lay.addWidget(self.verdict)
        row = QtWidgets.QHBoxLayout()
        self.take_button = QtWidgets.QPushButton("Usar a parede escolhida")
        self.take_button.setToolTip("Passa a trabalhar sobre a parede que estiver escolhida no modelo.")
        self.take_button.clicked.connect(self.take_chosen_wall)
        self.take_button.setEnabled(self.main is not None)
        self.side_box = QtWidgets.QComboBox()
        self.side_box.addItems(["frente", "trás"])
        self.side_box.setCurrentText(self.side)
        self.side_box.currentTextChanged.connect(lambda s: self.set_target(self.wall, s))
        row.addWidget(self.take_button, 1)
        row.addWidget(QtWidgets.QLabel("Face:"))
        row.addWidget(self.side_box)
        lay.addLayout(row)
        hint = QtWidgets.QLabel("Shift+A (ou o botão direito na tela): juntar um nó.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: %s;" % theme.qcolor(theme.C["muted"]).name())
        lay.addWidget(hint)
        dock.setWidget(holder)
        dock.setMinimumWidth(420)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self._titles()

    def _shown_node(self):
        return None if self.show_final.isChecked() else self.params.nid

    def _titles(self):
        name = self.name or "operador novo"
        self.setWindowTitle("{} — Gráfico Visual — ArqSynth BIM".format(name))
        where = "Face de exemplo (nenhuma parede escolhida)"
        if self.wall:
            obj = self.main.doc.get(self.wall) if self.main is not None else None
            side = self.side
            where = None
            try:
                from ..core.graph import nodes_3d
                if nodes_3d.is_curved(self.main.doc, self.wall):      # (0.548) a curved wall's faces by where they are
                    side = "de dentro (desenrolada)" if self.side == "frente" else "de fora (desenrolada)"
                kind = self.main.doc.ifc.kind_of(self.wall)
                if kind == "ceiling":                                 # (0.549)
                    where = "{} · em planta de teto".format(getattr(obj, "name", None) or "Teto")
                elif kind == "slab":
                    where = "{} · teto falso por baixo (planta de teto)".format(getattr(obj, "name", None) or "Laje")
            except Exception:  # (no model behind the window)
                pass
            where = where or "{} · face {}".format(getattr(obj, "name", None) or "Parede", side)
        self.target_label.setText(where)

    def set_target(self, wall, side="frente"):
        """(0.541) The wall's face the graph works on (""/…: the example face): worked out and shown again."""
        from ..core.graph import operators
        if ((wall or ""), (side or "frente")) != (self.wall, self.side):
            self.cladding = None                    # (another face: «Aplicar» makes its own panel there)
        self.wall, self.side = wall or "", side or "frente"
        operators.retarget(self.graph, self.wall, self.side)
        if self.side_box.currentText() != self.side:
            self.side_box.blockSignals(True)
            self.side_box.setCurrentText(self.side)
            self.side_box.blockSignals(False)
        self._titles()
        if self.params.nid is not None:
            self.params.show_node(self.params.nid, self.graph)
        self.evaluate()

    def take_chosen_wall(self):
        wall = self.chosen_wall()
        if not wall:
            QtWidgets.QMessageBox.information(self, "Gráfico Visual", "Escolha primeiro uma parede no modelo.")
            return
        self.set_target(wall, self.side)

    # ---- Shift+A: the menu of nodes
    def ask_node(self, point=None, scene_pos=None):
        """(0.541) The menu of nodes shown at `point` (the screen's); the one picked goes to `scene_pos`."""
        if self.node_menu is None:
            self.node_menu = NodeMenu(self)
            self.node_menu.chosen.connect(lambda key: self.add_node_at(key, self._drop))
        if point is None:
            centre = self.view.viewport().rect().center()
            point, scene_pos = self.view.viewport().mapToGlobal(centre), self.view.mapToScene(centre)
        self._drop = scene_pos
        self.node_menu.open_at(point)

    def add_node_at(self, key, scene_pos=None):
        """A node put on the canvas (at the mouse). Logical joins made at once: a wire chosen — the node goes in the
        middle of it (where its kinds fit); a card chosen — its output joined to the new node's first input of the
        same kind."""
        if scene_pos is None:
            scene_pos = self.view.mapToScene(self.view.viewport().rect().center())
        chosen = self.scene.selectedItems()
        wire = next((it for it in chosen if isinstance(it, LinkItem)), None) if len(chosen) == 1 else None
        card = next((it for it in chosen if isinstance(it, CardItem)), None) if len(chosen) == 1 else None
        self.remember()
        nid = self.graph.add_node(key, pos=(scene_pos.x() - CARD_W / 2, scene_pos.y() - TITLE_H))
        spec = self.graph.registry.get(key)
        try:
            if wire is not None:
                f, o, t, i = wire.link
                kind_in = self.graph.registry.get(self.graph.nodes[f]["type"]).port("outputs", o).kind
                kind_out = self.graph.registry.get(self.graph.nodes[t]["type"]).port("inputs", i).kind
                into = next((p for p in spec.inputs if p.kind == kind_in), None)
                out = next((p for p in spec.outputs if p.kind == kind_out), None)
                if into is not None and out is not None:
                    self.graph.connect(f, o, nid, into.name)
                    self.graph.connect(nid, out.name, t, i)
            elif card is not None:
                taken = set()
                for port in card.spec.outputs:
                    into = next((p for p in spec.inputs if p.kind == port.kind and p.name not in taken), None)
                    if into is not None:
                        self.graph.connect(card.nid, port.name, nid, into.name)
                        taken.add(into.name)
        except GraphError as e:
            self.status.showMessage(str(e), 6000)
        self.rebuild()
        self.cards[nid].setSelected(True)
        self.schedule()
        return nid

    def _build_params(self):
        dock = QtWidgets.QDockWidget("Propriedades do nó", self)
        dock.setObjectName("graph_params")
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.params = ParamsPanel()
        self.params.exposed = self.exposed
        self.params.expose.connect(self.set_exposed)
        self.params.changed.connect(self.set_param)
        self.params.pick_wall = self.chosen_wall
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.params)
        dock.setWidget(scroll)
        dock.setMinimumWidth(430)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _build_toolbar(self):
        bar = self.addToolBar("Gráfico")
        bar.setObjectName("graph_bar")
        bar.setMovable(False)
        bar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.act_add = bar.addAction("＋ Nó  (Shift+A)", lambda: self.ask_node())
        self.act_add.setToolTip("Junta um nó: o menu mostra cada um com o desenho do que faz.")
        bar.addSeparator()
        self.act_undo = bar.addAction("Desfazer", self.undo)             # (0.543)
        self.act_undo.setShortcut(QtGui.QKeySequence.StandardKey.Undo)
        self.act_undo.setToolTip("Desfaz a última alteração ao gráfico (Ctrl+Z).")
        self.act_redo = bar.addAction("Refazer", self.redo)
        self.act_redo.setShortcuts([QtGui.QKeySequence.StandardKey.Redo, QtGui.QKeySequence("Ctrl+Y")])
        self.act_redo.setToolTip("Refaz o que se desfez (Ctrl+Y).")
        self._undo_buttons()
        bar.addSeparator()
        self.act_keep = bar.addAction("Guardar operador", self.save_operator)
        self.act_keep.setToolTip("Guarda este gráfico na biblioteca de operadores (o painel lateral do BIM): fica "
                                 "para todos os projetos.")
        self.act_keep_as = bar.addAction("Guardar como…", lambda: self.save_operator(new=True))
        bar.addSeparator()
        files = QtWidgets.QToolButton()
        files.setText("Ficheiro ▾")
        files.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        fmenu = QtWidgets.QMenu(files)
        self.act_new = fmenu.addAction("Limpar a tela", self.new_graph)
        self.act_open = fmenu.addAction("Abrir gráfico de um ficheiro…", self.open_graph)
        self.act_save = fmenu.addAction("Gravar gráfico num ficheiro…", self.save_graph)
        files.setMenu(fmenu)
        bar.addWidget(files)
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

    # ---- undo (0.543): the graph (and what is in sight) as it was before each change
    UNDO_DEPTH = 80

    def remember(self, measure=None):
        """The graph kept before a change. `measure` (node id, name): a slider being dragged — its many steps are
        one change."""
        if measure is not None and measure == self._last_set:
            return
        self._last_set = measure
        self._undo.append((self.graph.to_json(), list(self.exposed)))
        del self._undo[:-self.UNDO_DEPTH]
        self._redo.clear()
        self._undo_buttons()

    def _undo_buttons(self):
        self.act_undo.setEnabled(bool(self._undo))
        self.act_redo.setEnabled(bool(self._redo))

    def _restore(self, state):
        text, exposed = state
        self.graph = Graph.from_json(text)
        self.exposed[:] = exposed
        self._retarget()
        self._last_set = None
        self.rebuild()
        self.params.show_node(None, None)
        self.evaluate()
        self._undo_buttons()

    def undo(self):
        if self._undo:
            self._redo.append((self.graph.to_json(), list(self.exposed)))
            self._restore(self._undo.pop())

    def redo(self):
        if self._redo:
            self._undo.append((self.graph.to_json(), list(self.exposed)))
            self._restore(self._redo.pop())

    def set_exposed(self, nid, name, on):
        """(0.543) A measure put in (or taken from) the side panel's sight."""
        self.remember()
        pair = (nid, name)
        if on and pair not in self.exposed:
            self.exposed.append(pair)
        elif not on and pair in self.exposed:
            self.exposed.remove(pair)

    # ---- the AI's changes (0.543): its graph is this window's while it is open
    def replace_graph(self, graph):
        self.remember()
        self.graph = graph
        self._retarget()
        self.rebuild()
        self.params.show_node(None, None)
        self.evaluate()
        self.fit()

    def graph_changed(self):
        """The graph changed from outside (the AI's tools): drawn and worked out again."""
        self.rebuild()
        self.params.show_node(None, None)
        self.evaluate()

    def save_operator(self, new=False):
        """(0.541) The graph kept in the library of operators (asked its name the first time, or `new`): its
        thumbnail what the surface shows. Returns its slug (None: given up)."""
        from ..core.graph import operators
        if new or not self.slug:
            name, ok = QtWidgets.QInputDialog.getText(self, "Guardar operador", "Nome do operador:",
                                                      text=self.name or "Painel perfurado")
            if not ok or not name.strip():
                return None
            self.name, self.slug = name.strip(), None
        try:
            png = png_bytes(surface_picture(self.graph, self.results, 240, 152))
            self.slug = operators.save(self.name, Graph.from_dict(self.graph.to_dict()), slug=self.slug, png=png,
                                       exposed=self.exposed)
        except (GraphError, OSError) as e:
            QtWidgets.QMessageBox.warning(self, "Gráfico Visual", str(e))
            return None
        self._titles()
        self.status.showMessage("Operador «{}» guardado na biblioteca.".format(self.name), 6000)
        panel = getattr(self.main, "operators_panel", None)
        if panel is not None:
            panel.reload(self.slug)
        return self.slug

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

    def _link(self, f, o, t, i):
        self.remember()
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
        if chosen:
            self.remember()
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
        if not self.show_final.isChecked():
            self.surface.refresh()

    def set_param(self, nid, name, value):
        self.remember((nid, name))
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
        self.surface.refresh()                                 # (0.541) the surface follows every change
        self._show_in_model()
        self._verdict()
        bad = len(self.graph.errors)
        self.status.showMessage("Calculado." if not bad else f"{bad} nós com avisos (ver a vermelho).", 4000)

    def _show_in_model(self, off=False):
        """(0.547) The panel shown on its wall in the model's 3D view (taken away: `off`, the box unticked, no wall,
        nothing to apply)."""
        show = getattr(getattr(self.main, "viewport", None), "show_operator_preview", None)
        if show is None:
            return None
        found = None
        if not off and self.in_model.isChecked() and self.wall:
            last = final_result(self.graph, self.results)
            if last is not None and last[1] == "bim":
                link = next((l for l in self.graph.links if l[2] == last[0] and l[3] == "furos"), None)
                source = self.results.get(link[0], {}).get(link[1]) if link else None
                try:
                    found = model_preview(self.main.doc, dict(last[2], wall=last[2]["wall"] or self.wall),
                                          None if source is None else source.get("bad"))
                except Exception:  # (a preview never stops the editor)
                    found = None
        if found is None:
            show()
        else:
            show(*found)
        return found

    def closeEvent(self, e):
        self._show_in_model(off=True)                         # (its picture out of the model's view)
        super().closeEvent(e)

    def _verdict(self):
        """(0.541) Under the surface: the last «Verificar fabrico»'s verdict (how many holes, the open area, what
        fails) — else how many holes there are."""
        text, good = "", True
        for nid in self.graph.order():
            out = self.results.get(nid)
            if out is None:
                continue
            if "relatorio" in out:
                rep = out["relatorio"]
                good = rep["ok"]
                text = "{} furos · área aberta {:.0f} % · {}".format(
                    rep["holes"], rep["open_area"] * 100,
                    "fabricável" if good else "{} furos a corrigir (a vermelho)".format(rep["bad"]))
                if rep["problems"]:
                    text += "\n" + "; ".join(rep["problems"][:2])
            elif "furos" in out and not text:
                text = "{} furos (por verificar)".format(len(out["furos"]["xy"]))
        self.verdict.setText(text)
        self.verdict.setStyleSheet("color: %s; font-weight: 600;" % (theme.ART["green"] if good else theme.ART["red"]))

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
        self.remember()
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
        self.remember()
        self.graph = templates.make(key, **kw)
        self._retarget()
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
                opened = Graph.from_json(fh.read())
            self.remember()
            self.graph = opened
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
            QtWidgets.QMessageBox.warning(self, "Gráfico Visual", f"Não foi possível abrir:\n{e}")
            return False
        self._retarget()
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

    def _retarget(self):
        from ..core.graph import operators
        operators.retarget(self.graph, self.wall, self.side)

    def fit(self):
        rect = self.scene.itemsBoundingRect()
        if not rect.isEmpty():
            self.view.fitInView(rect.adjusted(-40, -40, 40, 40), QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    # ---- the model
    def chosen_wall(self):
        """The GlobalId of the wall chosen in the model ("" if none)."""
        if self.main is None:
            return ""
        from ..core.graph import operators
        doc = self.main.doc
        for guid in sorted(self.main.viewport.selection, key=str):
            wall = operators.host_wall(doc, guid)          # (0.543: a wall's panel chosen stands for its wall)
            if wall:
                return wall
        return ""

    def apply_to_model(self):
        """«Aplicar ao modelo»: the graph's panel as a perforated finish on the wall's face being worked on, the
        finish keeping the operator. (0.543) Again (or a wall's panel being edited): that finish worked out anew —
        not another over it."""
        if self.main is None:
            return []
        from ..core.graph import operators
        doc = self.main.doc
        try:
            if self.cladding and operators.operator_of(doc, self.cladding) is not None:
                made = [operators.update(doc, self.cladding, self.graph, self.name, self.slug or "")]
                self.status.showMessage("Painel da parede atualizado.", 6000)
                return made
            wall = self.wall or self.chosen_wall()
            if not wall:
                QtWidgets.QMessageBox.warning(self, "Gráfico Visual", "Não aplicado:\nescolha uma parede no modelo "
                                              "e carregue em «Usar a parede escolhida»")
                return []
            if not self.wall:
                self.set_target(wall, self.side)
            made = operators.apply_to(doc, self.graph, wall, self.side, name=self.name, slug=self.slug or "")
        except ValueError as e:                              # (GraphError; the model's refusals)
            QtWidgets.QMessageBox.warning(self, "Gráfico Visual", "Não aplicado:\n{}".format(e))
            return []
        if len(made) == 1:
            self.cladding = made[0]
        self._show_in_model(off=True)                         # (the panel itself is there now)
        self.status.showMessage(f"{len(made)} painel(éis) perfurado(s) aplicado(s) ao modelo.", 6000)
        return made
