"""0.551 — Gráfico Visual, finishing: «Tirar o aplicado», the false ceiling's height under a slab, a parametric
surface's side, ceilings and surfaces in the perforated panels' table, the hole of one's own drawing."""

import os
import sys
import tempfile
import types
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["ARQSYNTH_HOME"] = tempfile.mkdtemp(prefix="arqsynth_finish_")

from PySide6 import QtWidgets  # noqa: E402

from arqbim.core import param_surface as ps  # noqa: E402
from arqbim.core import surfaces  # noqa: E402
from arqbim.core.graph import Graph, nodes_3d, operators  # noqa: E402
from arqbim.core.graph.nodes_panels import dxf_text  # noqa: E402
from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim, schedules  # noqa: E402
from arqbim.model.document import Document  # noqa: E402

APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
OUTLINE = [(0.0, 0.0), (5.0, 0.0), (5.0, 4.0), (0.0, 4.0)]


def dome(doc, h=0.8):
    data = ps.default_definition("grid")
    data["inputs"] = {"L": 6.0, "W": 4.0, "H": h}
    data["surface"].update(u=12, v=8)
    return bim.add_param_surface(doc, data, np.array((0.0, 0.0, 0.0)))


class TakeOff(unittest.TestCase):
    def test_wall_ceiling_surface(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        ceiling = bim.add_ceiling(doc, OUTLINE)
        surface = dome(doc)
        panel = operators.apply_to(doc, operators.starter(), wall)[0]
        operators.apply_to(doc, operators.starter(), ceiling)
        operators.apply_to(doc, operators.starter(), surface)
        self.assertEqual(set(operators.finishes_of(doc, [wall, ceiling, surface])), {panel, ceiling, surface})
        operators.remove(doc, panel)
        self.assertIsNone(doc.ifc.by_guid(panel))                     # (a wall's panel: deleted)
        operators.remove(doc, ceiling)
        self.assertIsNone(doc.ifc.ceiling_perforation(ceiling))       # (a ceiling: plain again, still there)
        self.assertIsNotNone(doc.ifc.by_guid(ceiling))
        operators.remove(doc, surface)
        self.assertIsNone(doc.ifc.surface_perforation(surface))
        self.assertEqual(operators.finishes_of(doc, [wall, ceiling, surface]), [])
        doc.undo()
        self.assertIsNotNone(doc.ifc.surface_perforation(surface))    # (Ctrl+Z puts it back)
        with self.assertRaises(ValueError):
            operators.remove(doc, wall)                               # (a wall itself keeps none)


class UnderASlab(unittest.TestCase):
    def test_drop(self):
        doc = Document()
        slab = bim.add_slab_outline(doc, OUTLINE, 3.0, catalog.BY_KEY["laje_15"])
        bottom = doc.ifc.slab_outline(slab)["bottom"]
        made = operators.apply_to(doc, operators.starter(), slab, drop=0.55)[0]
        self.assertAlmostEqual(doc.ifc.ceiling_params(made)["z"], bottom - 0.55, places=4)


class SurfaceSide(unittest.TestCase):
    def test_back(self):
        doc = Document()
        surface = dome(doc)
        operators.apply_to(doc, operators.starter(), surface, "trás")
        self.assertEqual(operators.operator_of(doc, surface)["side"], "trás")
        verts, _f = doc.ifc.triangulate([surface])[surface]
        top = verts[np.hypot(verts[:, 0] - 3.0, verts[:, 1] - 2.0) < 0.3, 2]
        self.assertTrue(len(top) and top.max() < 0.8)                 # (under the dome's top: its back side)
        before = doc.ifc.surface_perforation(surface)["count"]
        data = doc.ifc.surface_definition(surface)
        data["inputs"]["H"] = 1.2                                     # (made again: still on its back)
        bim.set_param_surface(doc, surface, data)
        verts, _f = doc.ifc.triangulate([surface])[surface]
        top = verts[np.hypot(verts[:, 0] - 3.0, verts[:, 1] - 2.0) < 0.3, 2]
        self.assertTrue(top.max() < 1.2)
        self.assertGreater(doc.ifc.surface_perforation(surface)["count"], before * 0.8)
        self.assertTrue(nodes_3d.seen_mirrored(doc, surface, "trás"))
        self.assertFalse(nodes_3d.seen_mirrored(doc, surface, "frente"))


class Table(unittest.TestCase):
    def test_ceilings_and_surfaces_listed(self):
        doc = Document()
        ceiling = bim.add_ceiling(doc, OUTLINE)
        surface = dome(doc)
        bim.add_ceiling(doc, [(10, 0), (12, 0), (12, 2), (10, 2)])        # (a plain one: not listed)
        operators.apply_to(doc, operators.starter(), ceiling)
        operators.apply_to(doc, operators.starter(), surface)
        rows = {r["guid"]: r for r in schedules.rows(doc, "perforated")}
        self.assertEqual(set(rows), {ceiling, surface})
        self.assertEqual(schedules.counts(doc)["perforated"], 2)
        self.assertEqual(rows[ceiling]["host"], "teto")
        self.assertEqual(rows[ceiling]["holes"], doc.ifc.ceiling_perforation(ceiling)["count"])
        self.assertAlmostEqual(rows[ceiling]["area"], 20.0, places=3)
        self.assertTrue(0 < rows[surface]["open_area"] < 100)


class DrawnHole(unittest.TestCase):
    def test_text(self):
        text = surfaces.drawn_text([(10, 10), (30, 10), (20, 40)])
        ring = surfaces.drawn_ring(text)
        self.assertAlmostEqual(np.ptp(ring[:, 1]), 1.0, places=3)     # (1 across: its height, the larger)
        self.assertAlmostEqual(float(surfaces.hole_area(text, np.array([0.1]))[0]), 0.5 * (2 / 3) * 0.01, places=5)
        for bad in ([(0, 0), (1, 1)], [(0, 0), (1, 1), (1, 0), (0, 1)]):              # (too few; sides crossing)
            with self.assertRaises(ValueError):
                surfaces.drawn_text(bad)
        self.assertTrue(surfaces.valid_shape(text))
        self.assertFalse(surfaces.valid_shape("desenho:0,0 1,1"))
        back = surfaces.free_read(surfaces.free_text(text, [(0.1, 0.2, 0.03, 30.0, 1.5)]))
        self.assertEqual(back[0], text)
        np.testing.assert_allclose(back[1][0], (0.1, 0.2, 0.03, 30.0, 1.5))

    def test_in_a_graph_on_a_wall_and_in_the_dxf(self):
        g = Graph()
        nodes_3d.MODEL["doc"] = None
        s = g.add_node("fachada_bim")
        q = g.add_node("grelha", {"passo": 0.15})
        g.connect(s, "painel", q, "painel")
        f = g.add_node("perfurar", {"forma": "desenho", "d_max": 0.1, "rodar": 15.0})
        g.connect(q, "pontos", f, "pontos")
        c = g.add_node("verificar_fabrico")
        g.connect(f, "furos", c, "furos")
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        self.assertTrue(out[f]["furos"]["shape"].startswith("desenho:"))          # (a star, not drawn yet)
        self.assertTrue(out[c]["relatorio"]["ok"], out[c]["relatorio"]["problems"])
        dxf = dxf_text(out[f]["furos"])
        self.assertNotIn("CIRCLE", dxf)
        self.assertGreater(dxf.count("POLYLINE\n8\nFUROS"), 100)
        cross = surfaces.drawn_text([(-1, -0.3), (-0.3, -0.3), (-0.3, -1), (0.3, -1), (0.3, -0.3), (1, -0.3),
                                     (1, 0.3), (0.3, 0.3), (0.3, 1), (-0.3, 1), (-0.3, 0.3), (-1, 0.3)])
        g.set_param(f, "desenho", cross)
        out = g.evaluate()
        self.assertEqual(out[f]["furos"]["shape"], cross)
        g.set_param(f, "desenho", "desenho:0,0 1,1")
        g.evaluate()
        self.assertIn("desenho", g.errors[f])
        g.set_param(f, "desenho", cross)
        b = g.add_node("aplicar_parede", {"repetir": False})
        g.connect(c, "furos", b, "furos")
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        made = operators.apply_to(doc, g, wall)[0]
        p = doc.ifc.pattern_params(made)
        self.assertGreater(p["count"], 100)
        self.assertTrue(doc.ifc._params(doc.ifc.by_guid(made))["FurosLivres"].startswith("desenho:"))

    def test_drawing_window(self):
        from arqbim.ui import hole_drawing
        dlg = hole_drawing.HoleDrawing("")
        self.assertEqual(len(dlg.pad.points), 10)                     # (a star to start from)
        self.assertTrue(dlg.ok.isEnabled())
        dlg.pad.set_points(dlg.ready["Cruz"])
        dlg._accept()
        self.assertEqual(len(surfaces.drawn_ring(dlg.result_text)), 12)
        dlg.pad.set_points([(0, 0), (1, 1)])
        self.assertFalse(dlg.ok.isEnabled())
        again = hole_drawing.HoleDrawing(dlg.result_text)
        self.assertEqual(len(again.pad.points), 12)
        out = os.environ.get("ARQ_SHOT")
        if out:
            again.resize(380, 480)
            again.show()
            APP.processEvents()
            again.grab().save(out)


class Panel(unittest.TestCase):
    def test_names_and_take_off(self):
        from arqbim.ui import operators_panel
        host = QtWidgets.QMainWindow()
        panel = operators_panel.OperatorsPanel(host)
        took = []
        panel.target, panel.kept = (lambda: 1), (lambda: 1)
        panel.on_remove = lambda: took.append(1)
        panel.reload()
        self.assertEqual((panel.update_button.text(), panel.edit_wall_button.text(), panel.remove_button.text()),
                         ("Atualizar o aplicado", "Editar o aplicado", "Tirar o aplicado"))
        self.assertTrue(panel.remove_button.isEnabled())
        panel.remove_button.click()
        self.assertEqual(took, [1])
        panel.kept = lambda: 0
        panel.refresh_target()
        self.assertFalse(panel.remove_button.isEnabled())
        self.assertIsInstance(types.SimpleNamespace(), object)


if __name__ == "__main__":
    unittest.main()
