"""0.545 — Gráfico Visual: triangles, lozenges and slots; each hole turned and stretched — in the nodes, in the
model's perforated finish (FurosLivres, old texts still read), in the DXF and in the fabrication check."""

import math
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["ARQSYNTH_HOME"] = tempfile.mkdtemp(prefix="arqsynth_shapes_")

from arqbim.core import surfaces  # noqa: E402
from arqbim.core.graph import Graph, nodes_3d, nodes_logic, operators, templates  # noqa: E402
from arqbim.core.graph.nodes_panels import dxf_text, hole_extras  # noqa: E402


def holes_graph(**perf):
    nodes_3d.MODEL["doc"] = None
    g = Graph()
    s = g.add_node("fachada_bim")
    q = g.add_node("grelha", {"passo": 0.2})
    g.connect(s, "painel", q, "painel")
    f = g.add_node("perfurar", dict({"d_max": 0.04}, **perf))
    g.connect(q, "pontos", f, "pontos")
    return g, f


class Geometry(unittest.TestCase):
    def test_text_old_and_new(self):
        old = surfaces.free_read("redondo|100.0,200.0,30.0;300.0,200.0,20.0")
        self.assertEqual(old[1].shape, (2, 5))
        self.assertEqual(list(old[1][0]), [0.1, 0.2, 0.03, 0.0, 1.0])
        text = surfaces.free_text("ranhura", [(0.1, 0.2, 0.01), (0.3, 0.2, 0.01, 45.0, 4.0)])
        self.assertEqual(text, "ranhura|100.0,200.0,10.0;300.0,200.0,10.0,45.0,4.000")
        back = surfaces.free_read(text)
        self.assertEqual(list(back[1][1]), [0.3, 0.2, 0.01, 45.0, 4.0])
        self.assertIsNone(surfaces.free_read("estrela|1,2,3"))
        self.assertIsNone(surfaces.free_read("redondo|1,2,3,4"))

    def test_areas_and_reach(self):
        import shapely
        for shape, ratio in (("redondo", 1.0), ("quadrado", 1.0), ("hexagonal", 1.0), ("triangular", 1.0),
                             ("losango", 1.0), ("ranhura", 4.0), ("redondo", 2.5), ("losango", 2.0)):
            ring = surfaces.hole_rings(shape, [(1.0, 2.0)], [0.1], [30.0], [ratio])[0]
            poly = shapely.Polygon(ring)
            area = float(surfaces.hole_area(shape, np.array([0.1]), np.array([ratio]))[0])
            self.assertAlmostEqual(poly.area, area, delta=area * 0.06, msg=shape)    # (a circle drawn in segments)
            reach = float(surfaces.hole_reach(shape, np.array([0.1]), np.array([ratio]))[0])
            far = np.hypot(ring[:, 0] - 1.0, ring[:, 1] - 2.0).max()
            self.assertAlmostEqual(far, reach, delta=1e-6, msg=shape)
        slot = surfaces.hole_rings("ranhura", [(0, 0)], [0.01], [90.0], [4.0])[0]         # (upright: 10 × 40 mm)
        self.assertAlmostEqual(np.ptp(slot[:, 0]), 0.01, places=6)
        self.assertAlmostEqual(np.ptp(slot[:, 1]), 0.04, places=6)
        self.assertAlmostEqual(float(surfaces.hole_reach("ranhura", 0.01)), 0.015)       # (none given: 3 times)

    def test_mesh_with_slots(self):
        from shapely.geometry import box
        face = box(0, 0, 1, 0.5)
        found = surfaces.free_perforation(face, "ranhura", [(0.3, 0.25, 0.02, 90.0, 5.0), (0.7, 0.25, 0.02)], 0.02,
                                          (1.0, 0.5), False)
        angle, ratio = surfaces.extras(found[0][2])
        self.assertEqual((list(angle), list(ratio)), ([90.0, 0.0], [5.0, 1.0]))
        verts, tris = surfaces.free_mesh(face, 0.003, found, "ranhura")
        top = verts[tris][np.all(np.isclose(verts[tris][:, :, 2], 0.003), axis=1)]
        a, b, c = top[:, 0, :2], top[:, 1, :2], top[:, 2, :2]
        area = 0.5 * np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])).sum()
        gone = float(surfaces.hole_area("ranhura", np.array([0.02, 0.02]), np.array([5.0, 1.0])).sum())
        self.assertAlmostEqual(area, 0.5 - gone, delta=gone * 0.06)
        long_one = surfaces.free_perforation(face, "ranhura", [(0.5, 0.25, 0.02, 90.0, 30.0)], 0.02, (1.0, 0.5), False)
        self.assertEqual(len(long_one[0][1]), 0)                   # (60 cm upright in a 50 cm board: left out)


class Nodes(unittest.TestCase):
    def test_perforate_shapes_and_check(self):
        for shape in ("triangular", "losango", "ranhura"):
            g, f = holes_graph(forma=shape, alongar=3.0, rodar=30.0)
            c = g.add_node("verificar_fabrico")
            g.connect(f, "furos", c, "furos")
            out = g.evaluate()
            self.assertEqual(g.errors, {}, shape)
            angle, ratio = hole_extras(out[c]["furos"])
            self.assertTrue(np.all(angle == 30.0) and np.all(ratio == 3.0))
            self.assertTrue(out[c]["relatorio"]["ok"], shape)
            self.assertAlmostEqual(out[c]["relatorio"]["open_area"], nodes_logic.open_area(out[f]["furos"]))
        g, f = holes_graph(forma="ranhura", alongar=6.0)             # (24 cm slots 20 cm apart: they touch)
        c = g.add_node("verificar_fabrico")
        g.connect(f, "furos", c, "furos")
        fix = g.add_node("corrigir_fabrico")
        g.connect(f, "furos", fix, "furos")
        c2 = g.add_node("verificar_fabrico")
        g.connect(fix, "furos", c2, "furos")
        out = g.evaluate()
        self.assertFalse(out[c]["relatorio"]["ok"])
        self.assertTrue(out[c2]["relatorio"]["ok"])
        self.assertTrue(np.all(hole_extras(out[fix]["furos"])[1] == 6.0))

    def test_turn_and_stretch(self):
        g, f = holes_graph(forma="ranhura")
        a = g.add_node("atrator", {"x": 2.0, "y": 1.35, "raio": 5.0})
        t = g.add_node("rodar_furos", {"modo": "ângulo fixo", "angulo": 20.0})
        g.connect(f, "furos", t, "furos")
        g.connect(a, "campo", t, "campo")
        k = g.add_node("alongar_furos", {"alongar": 5.0})
        g.connect(t, "furos", k, "furos")
        g.connect(a, "campo", k, "campo")
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        self.assertTrue(np.all(hole_extras(out[t]["furos"])[0] == 20.0))
        xy = out[f]["furos"]["xy"]
        ratio = hole_extras(out[k]["furos"])[1]
        near = np.hypot(xy[:, 0] - 2.0, xy[:, 1] - 1.35).argmin()
        self.assertGreater(ratio[near], ratio.min() + 0.2)
        self.assertTrue(np.all((ratio >= 1.0) & (ratio <= 5.0)))
        g.set_param(t, "modo", "para um ponto")
        g.set_param(t, "x", 2.0)
        g.set_param(t, "y", 1.35)
        g.set_param(t, "angulo", 0.0)
        ang = hole_extras(g.evaluate()[t]["furos"])[0]
        want = np.degrees(np.arctan2(1.35 - xy[:, 1], 2.0 - xy[:, 0]))
        self.assertTrue(np.allclose(ang, want))
        g.set_param(t, "modo", "ao longo do modulador")              # (round the attractor: square to the radius)
        ang = hole_extras(g.evaluate()[t]["furos"])[0]
        far = np.hypot(xy[:, 0] - 2.0, xy[:, 1] - 1.35) > 0.3
        turn = np.radians(ang[far] - want[far])
        self.assertTrue(np.allclose(np.abs(np.sin(turn)), 1.0, atol=0.05))
        g.set_param(t, "modo", "ao acaso")
        g.set_param(t, "angulo", 30.0)
        ang = hole_extras(g.evaluate()[t]["furos"])[0]
        self.assertTrue(np.all(np.abs(ang) <= 30.0) and ang.std() > 5.0)
        g.disconnect(t, "campo")
        g.set_param(t, "modo", "pelo modulador")
        g.evaluate()
        self.assertIn("modulador", g.errors[t])

    def test_dxf(self):
        g, f = holes_graph(forma="ranhura", alongar=4.0, rodar=90.0)
        text = dxf_text(g.evaluate()[f]["furos"])
        self.assertNotIn("CIRCLE", text)
        self.assertGreater(text.count("POLYLINE\n8\nFUROS"), 100)
        g2, f2 = holes_graph()
        self.assertIn("CIRCLE", dxf_text(g2.evaluate()[f2]["furos"]))


class InTheModel(unittest.TestCase):
    def test_slots_on_a_wall(self):
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        g = templates.make("ranhuras_a_fluir")
        made = operators.apply_to(doc, g, wall)[0]
        p = doc.ifc.pattern_params(made)
        self.assertGreater(p["count"], 300)
        text = doc.ifc._params(doc.ifc.by_guid(made))["FurosLivres"]
        self.assertTrue(text.startswith("ranhura|"))
        rows = surfaces.free_read(text)[1]
        self.assertGreater(rows[:, 3].std(), 10.0)                   # (turned each its way)
        self.assertTrue(rows[:, 4].min() >= 1.0 and rows[:, 4].max() > 2.0)
        area = float(surfaces.hole_area("ranhura", rows[:, 2], rows[:, 4]).sum())
        self.assertAlmostEqual(p["open_area"], area / (4.0 * bim.wall_frame(doc, wall).height), delta=0.01)
        nodes_3d.MODEL["doc"] = None
        rep = next(v["relatorio"] for v in g.evaluate().values() if "relatorio" in v)
        self.assertTrue(rep["ok"], rep["problems"])

    def test_pictures(self):
        from PySide6 import QtWidgets
        QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        from arqbim.ui import visual_graph as vg
        g = templates.make("ranhuras_a_fluir")
        nodes_3d.MODEL["doc"] = None
        img = vg.surface_picture(g, g.evaluate(), 640, 440)
        dark = sum(img.pixelColor(x, y).lightness() < 80 for x in range(0, 640, 4) for y in range(0, 440, 4))
        self.assertGreater(dark, 200)
        out = os.environ.get("ARQ_SHOT")
        if out:
            img.save(out)
        self.assertIsNotNone(vg.node_thumb("rodar_furos"))
        self.assertTrue(math.isfinite(1.0))


if __name__ == "__main__":
    unittest.main()
