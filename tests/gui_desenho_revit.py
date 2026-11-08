"""(0.455, the owner: «faça teste em todos esses novos recursos para corrigir os erros») The drawing features as
Revit's (0.447-0.455) driven in the real window as the owner does — clicks on the plan, the contextual bar's icons,
values typed — each checked; PASS / FAIL per step and a picture per step (tests/saida_gui/desenho_revit). Off screen,
with settings of its own in a temporary folder (the owner's program and settings untouched):

    python tests/gui_desenho_revit.py        (exits 1 when a step fails)"""
import math
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HOME = tempfile.mkdtemp(prefix="arqsynth_desenho_")
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ.setdefault("ARQBIM_RECENT_GROUP", "recentes_dos_testes")
for _name in ("XDG_CONFIG_HOME", "ARQSYNTH_HOME", "ARQBIM_CACHE_DIR"):
    os.environ.setdefault(_name, os.path.join(_HOME, _name.lower()))
    os.makedirs(os.environ[_name], exist_ok=True)
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "tests", "saida_gui", "desenho_revit")
os.makedirs(OUT, exist_ok=True)

import numpy as np  # noqa: E402
from PySide6 import QtCore, QtGui, QtTest, QtWidgets  # noqa: E402

from arqbim.app import create_window  # noqa: E402
from arqbim.core.sketch_geometry import transform_point  # noqa: E402
from arqbim.model import bim  # noqa: E402

Qt = QtCore.Qt
QtWidgets.QMessageBox.question = staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Discard)
QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue("unidades/comprimento", "m")
app, win = create_window()
win.resize(1920, 933)
win.show()
canvas, vp = win.canvas, win.viewport
results = []
mouse = [0.0, 0.0]


def pump(ms=120):
    end = time.time() + ms / 1000
    while time.time() < end:
        app.processEvents()
        time.sleep(0.004)


def deliver():
    if hasattr(canvas, "_process_events"):
        canvas._process_events()


def qp(x, y):
    return QtCore.QPoint(int(round(x)), int(round(y)))


def move_to(p, steps=3, mods=Qt.KeyboardModifier.NoModifier):
    x, y = vp.project(np.asarray(p, float))
    start = np.array(mouse)
    target = getattr(canvas, "_subwidget", canvas)
    for i in range(1, steps + 1):
        q = start + (np.array((x, y)) - start) * i / steps
        mouse[:] = q
        ev = QtGui.QMouseEvent(QtCore.QEvent.Type.MouseMove, QtCore.QPointF(qp(*q)),
                               QtCore.QPointF(target.mapToGlobal(qp(*q))), Qt.MouseButton.NoButton,
                               Qt.MouseButton.NoButton, mods)
        QtWidgets.QApplication.sendEvent(target, ev)
        pump(20)
        deliver()


def click_at(p, mods=Qt.KeyboardModifier.NoModifier):
    move_to(p)
    pump(60)
    QtTest.QTest.mousePress(canvas, Qt.MouseButton.LeftButton, mods, qp(*mouse))
    pump(30)
    deliver()
    QtTest.QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, mods, qp(*mouse))
    pump(60)
    deliver()


def key(k):
    QtTest.QTest.keyClick(canvas, k)
    pump(60)


def type_value(text):
    QtTest.QTest.keyClicks(canvas, text)
    pump(40)
    key(Qt.Key.Key_Return)
    pump(120)


def bar_icon(field, value):
    """A click on the contextual bar's icon (as the owner)."""
    row = win.context_bar.fields[field][0]
    for b in row.findChildren(QtWidgets.QToolButton):
        if b.objectName() == "ctx_{}_{}".format(field, value):
            b.click()
            pump(150)
            return True
    raise RuntimeError("no icon {} {}".format(field, value))


def bar_value(field, value):
    win._context_option(field, value)
    pump(80)


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print("PASS" if ok else "FAIL", name, detail, flush=True)


def shot(name):
    pump(250)
    win.grab().save(os.path.join(OUT, "recursos_{}.png".format(name)))


def fresh(center, radius=6.0):
    win.set_tool("select")
    win.doc.modified = False
    win.act_new.trigger()
    pump(500)
    win.set_plan(True)
    pump(400)
    vp.set_view("top", center=np.array(center, float), radius=radius)
    pump(400)
    return win.doc


def line_tool():
    """The Line, drawing lines (its bar's first icon: as the owner after another of its icons)."""
    win.set_tool("line")
    pump(100)
    bar_icon("draw", "line")


def walls(doc):
    return [(g, s, e) for g, s, e, _t in bim.wall_axes(doc)]


def curved(doc):
    out = []
    for o in doc.objects.values():
        if o.is_bim and doc.ifc.kind_of(o.id) == "curved_wall":
            c, r, s, sw, _h, _t = doc.ifc.curved_wall_params(o.id)
            out.append((np.round(c[:2], 3).tolist(), round(r, 3), round(abs(math.degrees(sw)), 1)))
    return out


def sketches(doc):
    return [o for o in doc.objects.values() if not o.is_bim]


def r3(p):
    return tuple(round(float(v), 3) for v in p[:2])


def same(a, b, tol=0.02):
    """Nested numbers equal within `tol` (a click on the screen lands a few millimetres off)."""
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(same(x, y, tol) for x, y in zip(a, b))
    try:
        return abs(float(a) - float(b)) <= (tol if abs(float(b)) < 30 else 1.0)
    except (TypeError, ValueError):
        return a == b


def has(items, wanted, tol=0.02):
    return any(same(x, wanted, tol) for x in items)


def run(name, fn):
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        check(name, False, "ERRO: {!r}".format(exc))
    try:
        win.set_tool("select")
        key(Qt.Key.Key_Escape)
    except Exception:  # noqa: BLE001
        pass


# ------------------------------------------------------------------ the Wall


def wall_radius():
    doc = fresh((2.5, 2.0, 0.0))
    win.set_tool("wall")
    bar_value("radius", 1.0)
    for p in ((0, 0, 0), (5, 0, 0), (5, 4, 0)):
        click_at(p)
    key(Qt.Key.Key_Escape)
    shot("parede_raio")
    w, c = walls(doc), curved(doc)
    check("parede_raio_dos_cantos", len(w) == 2 and same(c, [[[4.0, 1.0], 1.0, 90.0]]), "{} {}".format(
        [(r3(s), r3(e)) for _g, s, e in w], c))
    bar_value("radius", 0.0)


def wall_chain_off():
    doc = fresh((2.0, 2.0, 0.0))
    win.set_tool("wall")
    bar_value("chain", False)
    for p in ((0, 0, 0), (4, 0, 0), (0, 3, 0), (4, 3, 0)):
        click_at(p)
    key(Qt.Key.Key_Escape)
    shot("parede_cadeia")
    w = sorted((r3(s), r3(e)) for _g, s, e in walls(doc))
    check("parede_cadeia_desligada", same(w, [((0.0, 0.0), (4.0, 0.0)), ((0.0, 3.0), (4.0, 3.0))]), w)
    bar_value("chain", True)


def wall_offset():
    doc = fresh((2.0, 0.5, 0.0))
    win.set_tool("wall")
    bar_value("offset", 0.5)
    for p in ((0, 0, 0), (4, 0, 0)):
        click_at(p)
    key(Qt.Key.Key_Escape)
    shot("parede_afastamento")
    w = [(r3(s), r3(e)) for _g, s, e in walls(doc)]
    check("parede_afastamento", same(w, [((0.0, 0.5), (4.0, 0.5))]), w)
    bar_value("offset", 0.0)


def wall_arcs():
    doc = fresh((4.0, 3.0, 0.0), 7.0)
    win.set_tool("wall")
    bar_icon("shape", "arc")                         # start, end, then the bulge
    for p in ((0, 0, 0), (4, 0, 0), (2, 1, 0)):
        click_at(p)
    c = curved(doc)
    check("parede_arco_3_pontos", same(c, [[[2.0, -1.5], 2.5, 106.3]], 0.05), c)
    bar_icon("shape", "arc_center")                  # centre, start (the radius), end (the way the mouse goes)
    click_at((8, 0, 0))
    click_at((10, 0, 0))
    move_to((9.9, 0.8, 0))
    move_to((9.2, 1.7, 0))
    click_at((8, 2, 0))
    c = curved(doc)
    check("parede_arco_centro_pontas", len(c) == 2 and same(c[1], [[8.0, 0.0], 2.0, 90.0], 0.05), c)
    bim.add_wall(doc, (0.0, 5.0, 0.0), (4.0, 5.0, 0.0), win.tools["wall"].spec)
    pump(200)
    bar_icon("shape", "arc_tangent")
    move_to((3.95, 5.0, 0))
    click_at((3.98, 5.02, 0))                        # the wall's end
    click_at((5, 6, 0))
    c = curved(doc)
    check("parede_arco_tangente", len(c) == 3 and same(c[2], [[4.0, 6.0], 1.0, 90.0], 0.05), c)
    bar_icon("shape", "line")                        # straight on from the arc's end
    click_at((5, 8, 0))
    key(Qt.Key.Key_Escape)
    w = [(r3(s), r3(e)) for _g, s, e in walls(doc)]
    check("parede_tangente_depois_reta", has(w, ((5.0, 6.0), (5.0, 8.0))), w)
    shot("parede_arcos")


def wall_fillet():
    doc = fresh((2.5, 2.0, 0.0))
    win.set_tool("wall")
    for p in ((0, 0, 0), (5, 0, 0), (5, 4, 0)):
        click_at(p)
    key(Qt.Key.Key_Escape)
    bar_icon("shape", "fillet")
    click_at((2, 0, 0))
    click_at((5, 2, 0))
    move_to((4.6, 0.4, 0))
    type_value("1")
    shot("parede_concordancia")
    c = curved(doc)
    check("parede_concordancia", same(c, [[[4.0, 1.0], 1.0, 90.0]]), c)
    bar_icon("shape", "line")


def wall_pick():
    doc = fresh((2.0, 1.0, 0.0))
    line_tool()
    click_at((0, 0, 0))
    click_at((4, 0, 0))
    key(Qt.Key.Key_Escape)
    win.set_tool("wall")
    bar_icon("shape", "pick")
    bar_value("offset", 0.5)
    move_to((2, 0.08, 0))
    click_at((2, 0.08, 0))
    shot("parede_escolher_linhas")
    w = [(r3(s), r3(e)) for _g, s, e in walls(doc)]
    check("parede_escolher_linhas", same(w, [((0.0, 0.5), (4.0, 0.5))]), "{} {}".format(w, win.last_message))
    bar_value("offset", 0.0)
    bar_icon("shape", "line")


def wall_polygon():
    """(0.457) A hexagon of walls: its centre clicked, its radius typed."""
    doc = fresh((0.0, 0.0, 0.0), 6.0)
    win.set_tool("wall")
    bar_icon("shape", "poly_in")
    click_at((0, 0, 0))
    move_to((2, 0.2, 0))
    type_value("3")
    shot("parede_poligono")
    w = walls(doc)
    check("parede_poligono_inscrito", len(w) == 6 and all(same(float(np.linalg.norm(e[:2])), 3.0) for _g, _s, e in w),
          [r3(e) for _g, _s, e in w])
    bar_icon("shape", "line")


def wall_snaps():
    doc = fresh((2.0, 2.0, 0.0))
    win.set_tool("wall")
    click_at((0, 0, 0))
    a = math.radians(43.5)
    click_at((3 * math.cos(a), 3 * math.sin(a), 0))
    key(Qt.Key.Key_Escape)
    w = walls(doc)
    ang = math.degrees(math.atan2(*(w[0][2] - w[0][1])[1::-1])) if w else None
    check("parede_snap_45", ang is not None and abs(ang - 45.0) < 1e-6, ang)
    bim.add_wall(doc, (6.0, 0.0, 0.0), (6.0 + 4 * math.cos(math.radians(30)), 4 * math.sin(math.radians(30)), 0.0),
                 win.tools["wall"].spec)
    pump(200)
    click_at((0, 4, 0))
    a = math.radians(31.5)
    click_at((3 * math.cos(a), 4 + 3 * math.sin(a), 0))
    key(Qt.Key.Key_Escape)
    w = walls(doc)
    ang = math.degrees(math.atan2(*(w[-1][2] - w[-1][1])[1::-1])) if len(w) == 3 else None
    check("parede_snap_paralelo", ang is not None and abs(ang - 30.0) < 1e-6, ang)


# ------------------------------------------------------------------ the Line


def line_chain_off():
    doc = fresh((2.0, 1.0, 0.0))
    line_tool()
    bar_value("chain", False)
    for p in ((0, 0, 0), (3, 0, 0), (0, 2, 0), (3, 2, 0)):
        click_at(p)
    key(Qt.Key.Key_Escape)
    lines = [o for o in sketches(doc) if o.mesh.lines and not o.mesh.faces]
    check("linha_cadeia_desligada", len(lines) == 2 and all(len(o.mesh.lines) == 1 for o in lines),
          [len(o.mesh.lines) for o in lines])
    bar_value("chain", True)


def line_fillet():
    doc = fresh((2.0, 1.5, 0.0))
    line_tool()
    for p in ((0, 0, 0), (4, 0, 0), (4, 3, 0)):
        click_at(p)
    key(Qt.Key.Key_Escape)
    bar_icon("draw", "fillet")
    click_at((2, 0, 0))
    click_at((4, 2, 0))
    move_to((3.6, 0.4, 0))
    type_value("1")
    shot("linha_concordancia")
    arcs = [o for o in sketches(doc) if o.curve and o.curve.get("kind") == "arc"]
    check("linha_concordancia_um_arco", len(arcs) == 1, "objetos={} arcos={}".format(
        [(len(o.mesh.lines), bool(o.curve)) for o in sketches(doc)], len(arcs)))
    if not arcs:
        return
    from arqbim.core import curves
    arc = arcs[0]
    check("linha_concordancia_raio", abs(curves.arc_radius(arc.curve) - 1.0) < 1e-6, curves.arc_radius(arc.curve))
    # as Revit's: a click on the arc picks it whole; its radius shown; a click on the value, 0,5 typed
    win.set_tool("select")
    key(Qt.Key.Key_Escape)
    c = np.asarray(arc.curve["centre"], float)
    mid = c + 1.0 * np.array((math.cos(math.radians(-45)), math.sin(math.radians(-45)), 0.0))
    click_at(mid)
    pump(300)
    whole = vp.selection == {arc.id}
    dims = [d for d, _at, _t in vp.temp_dims if d.key and d.key[0] == "arc_radius"]
    check("linha_arco_escolhido_inteiro", whole and len(dims) == 1, "seleção={} cotas={}".format(
        vp.selection, [d.key for d, _a, _t in vp.temp_dims]))
    if not dims:
        return
    at = next(a for d, a, _t in vp.temp_dims if d is dims[0])
    sx, sy = vp.project(np.asarray(at, float))
    spot = next(((sx + dx, sy + dy) for r in range(0, 40, 2) for dx in range(-r, r + 1, 2) for dy in (-r, r)
                 if vp.temp_dim_at(sx + dx, sy + dy) is dims[0]), None)
    if spot is None:
        check("linha_raio_cota_clicavel", False, "o valor não se encontra no ecrã")
        return
    mouse[:] = spot
    QtTest.QTest.mousePress(canvas, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, qp(*spot))
    QtTest.QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, qp(*spot))
    pump(200)
    deliver()
    type_value("0,5")
    shot("linha_raio_0_5")
    arc = doc.get(arc.id)
    pts = []
    for o in sketches(doc):
        if not o.curve:
            pts += [r3(transform_point(o.matrix, v)) for v in o.mesh.verts]
    check("linha_raio_mudado_tangente", abs(curves.arc_radius(arc.curve) - 0.5) < 1e-6 and has(pts, (3.5, 0.0))
          and has(pts, (4.0, 0.5)), "{} {} {}".format(curves.arc_radius(arc.curve), pts, win.last_message))


def polygon_fillet():
    doc = fresh((2.0, 1.5, 0.0))
    line_tool()
    for p in ((0, 0, 0), (4, 0, 0), (4, 3, 0), (0, 3, 0), (0, 0, 0)):
        click_at(p)
    key(Qt.Key.Key_Escape)
    faces = [o for o in sketches(doc) if o.mesh.faces]
    line_tool()
    bar_icon("draw", "fillet")
    click_at((2, 0, 0))
    click_at((4, 1.5, 0))
    move_to((3.6, 0.4, 0))
    type_value("1")
    shot("poligono_concordancia")
    pts = []
    for o in sketches(doc):
        pts += [r3(transform_point(o.matrix, v)) for v in o.mesh.verts]
    check("poligono_concordancia", len(faces) == 1 and has(pts, (3.0, 0.0)) and has(pts, (4.0, 1.0))
          and not has(pts, (4.0, 0.0), 0.005), "faces={} msg={}".format(len(faces), win.last_message))


def click_dim(dim):
    """A click on a temporary dimension's value (as the owner: the value, then a number typed)."""
    at = next(a for d, a, _t in vp.temp_dims if d is dim)
    sx, sy = vp.project(np.asarray(at, float))
    spot = next(((sx + dx, sy + dy) for r in range(0, 40, 2) for dx in range(-r, r + 1, 2) for dy in (-r, r)
                 if vp.temp_dim_at(sx + dx, sy + dy) is dim), None)
    if spot is None:
        return False
    mouse[:] = spot
    QtTest.QTest.mousePress(canvas, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, qp(*spot))
    QtTest.QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, qp(*spot))
    pump(200)
    deliver()
    return True


def line_shapes():
    """(0.458) On the Line's row, Revit's polygons and ellipses: an inscribed hexagon (its radius typed), a square round
    a circle of 1 m, an ellipse (its half-axes typed) — faces —, a half ellipse picked whole, its half-axis typed
    over; the ribbon's Circle a circle again."""
    from arqbim.core import curves
    from arqbim.model import curve_edit
    doc = fresh((7.0, 3.0, 0.0), 10.0)
    line_tool()
    bar_icon("draw", "poly_in")
    check("linha_poligono_ferramenta", win.tool.name == "circle" and win.tool.kind == "poly_in",
          "{} {}".format(win.tool.name, getattr(win.tool, "kind", None)))
    click_at((0, 0, 0))
    move_to((2, 0.3, 0))
    type_value("2")
    faces = [o for o in sketches(doc) if o.mesh.faces]
    area = faces[-1].mesh.face_area(0) if faces else None
    check("linha_poligono_inscrito", len(faces) == 1 and len(faces[0].mesh.verts) == 6 and
          same(area, 3 * math.sqrt(3) / 2 * 4, 0.02), "{} {}".format(area, win.last_message))
    bar_icon("draw", "poly_out")
    bar_value("sides", 4)
    click_at((6, 0, 0))
    move_to((7, 0.05, 0))
    type_value("1")
    faces = [o for o in sketches(doc) if o.mesh.faces]
    area = faces[-1].mesh.face_area(0) if len(faces) == 2 else None
    check("linha_poligono_circunscrito", same(area, 4.0, 0.02), "{} {}".format(area, win.last_message))
    bar_icon("draw", "ellipse")
    click_at((12, 0, 0))
    move_to((14, 0.1, 0))
    type_value("3")
    move_to((12.5, 1.5, 0))
    type_value("2")
    faces = [o for o in sketches(doc) if o.mesh.faces]
    area = faces[-1].mesh.face_area(0) if len(faces) == 3 else None
    check("linha_elipse", same(area, math.pi * 6, 0.1), "{} {}".format(area, win.last_message))
    bar_icon("draw", "ellipse_part")
    click_at((0, 5, 0))
    click_at((4, 5, 0))
    move_to((2, 6.4, 0))
    type_value("1,5")
    shot("linha_formas")
    halves = [o for o in sketches(doc) if o.curve and o.curve.get("kind") == "ellipse"]
    pts = curves.ellipse_points(halves[0].curve, 2) if halves else []
    check("linha_meia_elipse", len(halves) == 1 and same([r3(p) for p in pts], [(0, 5), (2, 6.5), (4, 5)]),
          "{} {}".format([r3(p) for p in pts], win.last_message))
    if not halves:
        return
    half = halves[0]
    win.set_tool("select")
    key(Qt.Key.Key_Escape)
    click_at((2, 6.5, 0))
    pump(300)
    dims = [d for d, _at, _t in vp.temp_dims if d.key and d.key[0] in ("ellipse_axis", "ellipse_minor")]
    check("linha_meia_elipse_escolhida", vp.selection == {half.id} and len(dims) == 2, "seleção={} cotas={}".format(
        vp.selection, [d.key for d, _a, _t in vp.temp_dims]))
    axis = next((d for d in dims if d.key[0] == "ellipse_axis"), None)
    if axis is None or not click_dim(axis):
        check("linha_meia_elipse_cota_clicavel", False, "o valor não se encontra no ecrã")
        return
    type_value("3")
    shot("linha_meia_elipse_3")
    ends = [r3(p) for p in curve_edit._ends(doc.get(half.id))]
    check("linha_meia_elipse_semieixo", same(ends, [(-1, 5), (5, 5)]), "{} {}".format(ends, win.last_message))
    win.set_tool("circle")
    pump(100)
    check("circulo_da_fita_e_circulo", win.tool.kind == "circle", win.tool.kind)


# ------------------------------------------------------------------ Align, 2D drawing


def align_line():
    doc = fresh((2.0, 1.5, 0.0))
    bim.add_wall(doc, (0.0, 0.0, 0.0), (0.0, 4.0, 0.0), win.tools["wall"].spec)
    pump(200)
    line_tool()
    click_at((1, 1, 0))
    click_at((1, 3, 0))
    key(Qt.Key.Key_Escape)
    win.set_tool("align")
    click_at((0.1, 2.5, 0))                           # the wall's face (x = 0,10)
    click_at((1, 2, 0))                               # the line: onto it
    shot("alinhar_linha")
    xs = sorted({round(float(transform_point(o.matrix, v)[0]), 3) for o in sketches(doc) for v in o.mesh.verts})
    check("alinhar_linha_na_face", xs == [0.1], "{} {}".format(xs, win.last_message))


def draft_region_mask():
    doc = fresh((2.0, 1.5, 0.0))
    win.set_tool("draft")
    bar_icon("shape", "mask")
    for p in ((0, 0, 0), (3, 0, 0), (3, 2, 0), (0, 2, 0)):
        click_at(p)
    click_at((0, 0, 0))
    shot("mascara")
    notes = getattr(doc, "annotations", None) or []
    kinds = [(getattr(n, "kind", None), getattr(n, "hatch", None)) for n in notes]
    check("mascara_desenhada", ("region", "mask") in kinds, kinds)
    # the mask's corner rounded (Desenho 2D ▸ Arco de concordância), the radius typed
    bar_icon("shape", "fillet")
    click_at((1.5, 0, 0))
    click_at((3, 1, 0))
    move_to((2.7, 0.3, 0))
    type_value("0,5")
    shot("mascara_concordancia")
    mask = next((n for n in doc.annotations if n.kind == "region"), None)
    b = (mask.extra or {}).get("bulges") if mask is not None else None
    check("mascara_canto_em_arco", mask is not None and len(mask.points) == 5 and b and
          sum(1 for x in b if abs(x) > 1e-9) == 1, "{} {} {}".format(
              len(mask.points) if mask else None, b, win.last_message))
    # two lines drawn in the view: an arc of their own between them
    bar_icon("shape", "line")
    for p in ((0, 4, 0), (3, 4, 0), (4, 5, 0), (4, 8, 0)):
        click_at(p)
    bar_icon("shape", "fillet")
    click_at((1.5, 4, 0))
    click_at((4, 6.5, 0))
    move_to((3.6, 4.4, 0))
    type_value("1")
    shot("linhas_2d_concordancia")
    arcs2 = [n for n in doc.annotations if n.kind == "arc"]
    check("linhas_2d_arco", len(arcs2) == 1, "{} {}".format([n.kind for n in doc.annotations], win.last_message))


# ------------------------------------------------------------------ (0.456) the Slab, the Floor, the Ceiling


def made_of(doc, kind):
    return [o.id for o in doc.objects.values() if o.is_bim and doc.ifc.kind_of(o.id) == kind]


def covering_area(doc, guid):
    from shapely.geometry import Polygon
    p = doc.ifc.ceiling_params(guid)
    return Polygon(p["outline"]).area


def slab_shapes():
    doc = fresh((6.0, 2.0, 0.0), 9.0)
    win.set_tool("slab")
    bar_icon("shape", "poly_in")                       # a hexagon inscribed: centre, its radius typed
    click_at((0, 0, 0))
    move_to((2, 0.3, 0))
    type_value("2")
    s = made_of(doc, "slab")
    area = doc.ifc.slab_outline(s[-1])["area"] if s else None
    check("laje_poligono_inscrito", s and same(area, 3 * math.sqrt(3) / 2 * 4, 0.02), area)
    bar_icon("shape", "ellipse")                       # an ellipse: centre, its half-axes typed (3 along x, 2)
    click_at((8, 0, 0))
    move_to((10, 0.0, 0))
    type_value("3")
    move_to((8.5, 1.5, 0))
    type_value("2")
    s = made_of(doc, "slab")
    area = doc.ifc.slab_outline(s[-1])["area"] if len(s) == 2 else None
    check("laje_elipse", area is not None and same(area, math.pi * 6, 0.05), "{} {}".format(area, win.last_message))
    shot("laje_formas")
    line_tool()                                        # four lines, then the outline of them picked
    for a, b in (((0, 4, 0), (4, 4, 0)), ((4, 3.5, 0), (4, 7.5, 0)), ((4.5, 7, 0), (-0.5, 7, 0)),
                 ((0, 7.5, 0), (0, 3.5, 0))):
        click_at(a)
        click_at(b)
        key(Qt.Key.Key_Escape)
    win.set_tool("slab")
    bar_icon("shape", "pick")
    for p in ((2, 4.05, 0), (4.05, 5.5, 0), (2, 7.05, 0), (0.05, 5.5, 0), (2, 4.05, 0)):
        click_at(p)
    s = made_of(doc, "slab")
    area = doc.ifc.slab_outline(s[-1])["area"] if len(s) == 3 else None
    check("laje_escolher_linhas", area is not None and same(area, 12.0, 0.15), "{} {}".format(area,
                                                                                               win.last_message))
    bar_icon("shape", "rect")                          # 10 cm out, its corners rounded 0,50
    bar_value("offset", 0.1)
    bar_value("radius", 0.5)
    click_at((8, 4, 0))
    click_at((12, 7, 0))
    s = made_of(doc, "slab")
    area = doc.ifc.slab_outline(s[-1])["area"] if len(s) == 4 else None
    check("laje_afastamento_raio", area is not None and same(area, 4.2 * 3.2 - (1 - math.pi / 4), 0.15), area)
    bar_value("offset", 0.0)
    bar_value("radius", 0.0)
    shot("laje_escolher_raio")


def coverings():
    doc = fresh((3.0, 1.0, 0.0), 7.0)
    win.set_tool("flooring")
    bar_icon("shape", "circle")
    click_at((0, 0, 0))
    click_at((1.5, 0, 0))
    f = made_of(doc, "flooring")
    check("piso_circulo", len(f) == 1 and same(covering_area(doc, f[0]), math.pi * 2.25, 0.1),
          [covering_area(doc, g) for g in f])
    win.set_tool("ceiling")
    bar_icon("shape", "poly_out")
    bar_value("sides", 8)
    click_at((6, 0, 0))
    click_at((7.5, 0, 0))
    c = made_of(doc, "ceiling")
    area = covering_area(doc, c[0]) if c else None
    check("teto_poligono_circunscrito", c and same(area, 8 * 1.5 ** 2 * math.tan(math.pi / 8), 0.15), area)
    shot("piso_teto")


def region_outlines():
    from arqbim.model import annotations as notes2d
    doc = fresh((3.0, 1.0, 0.0), 7.0)
    win.set_tool("draft")
    bar_icon("shape", "mask")
    bar_icon("mode", "circle")                         # a round mask: its centre, the radius typed
    click_at((0, 0, 0))
    move_to((1, 0.2, 0))
    type_value("1,5")
    bar_icon("mode", "poly_out")                       # another mask: a hexagon round a circle of 1 m
    click_at((5, 0, 0))
    move_to((6, 0.1, 0))
    type_value("1")
    shot("regiao_formas")
    plane = vp.view_plane()
    areas = [notes2d.area(a, *plane[:3]) for a in doc.annotations]
    check("regiao_mascara_circulo_hexagono", len(areas) == 2 and same(areas[0], math.pi * 2.25, 0.02) and
          same(areas[1], 6 * math.tan(math.pi / 6), 0.02), areas)
    bar_icon("mode", "poly")
    bar_icon("shape", "line")


for name, fn in (("laje_formas", slab_shapes), ("piso_teto", coverings), ("regiao_formas", region_outlines),
                 ("parede_raio", wall_radius), ("parede_cadeia", wall_chain_off), ("parede_afastamento", wall_offset),
                 ("parede_arcos", wall_arcs), ("parede_concordancia", wall_fillet), ("parede_escolher", wall_pick),
                 ("parede_snaps", wall_snaps), ("parede_poligono", wall_polygon), ("linha_cadeia", line_chain_off), ("linha_concordancia", line_fillet),
                 ("poligono_concordancia", polygon_fillet), ("alinhar", align_line), ("mascara", draft_region_mask),
                 ("linha_formas", line_shapes)):
    run(name, fn)
win.doc.modified = False
print("RESUMO: {} de {} passaram".format(sum(ok for _n, ok in results), len(results)))
for n, ok in results:
    if not ok:
        print("  falhou:", n)
sys.exit(0 if all(ok for _n, ok in results) else 1)
