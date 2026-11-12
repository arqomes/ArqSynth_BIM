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
        for d in (dlg, again):                                       # (gone before Qt is: no crash at the end)
            d.close()
            d.deleteLater()
        APP.processEvents()


class CutList(unittest.TestCase):
    """0.552 — the sheet on a parametric surface in its cut list (CSV) and its summary."""

    def test_sheet_part(self):
        from arqbim.core import surface_build
        doc = Document()
        surface = dome(doc)
        self.assertFalse(any(p["kind"] == "chapa perfurada" for p in doc.ifc.surface_parts(surface)))
        operators.apply_to(doc, operators.starter(), surface)
        parts = doc.ifc.surface_parts(surface)
        sheet = next(p for p in parts if p["kind"] == "chapa perfurada")
        got = doc.ifc.surface_perforation(surface)
        self.assertEqual(sheet["holes"], got["count"])
        self.assertAlmostEqual(sheet["area"], ps.Surface(doc.ifc.surface_definition(surface)).area(), places=3)
        self.assertIn("chapa perfurada", doc.ifc.surface_summary(surface)["families"])
        path = os.path.join(tempfile.mkdtemp(), "pecas.csv")
        surface_build.write_csv(path, parts, "Cúpula")
        with open(path, encoding="utf-8-sig") as f:
            text = f.read()
        self.assertIn("Chapa perfurada — {} furos".format(got["count"]), text)


class PerModule(unittest.TestCase):
    """0.552 — open area module by module (after Subdividir)."""

    def _graph(self, each):
        g = Graph()
        p = g.add_node("painel_plano", {"largura": 3.0, "altura": 1.0, "margem": 0.03})
        s = g.add_node("subdividir", {"colunas": 3, "linhas": 1, "junta": 0.01})
        g.connect(p, "painel", s, "painel")
        q = g.add_node("grelha", {"passo": 0.05})
        g.connect(s, "painel", q, "painel")
        grad = g.add_node("gradiente", {"angulo": 0.0})
        g.connect(s, "painel", grad, "painel")
        f = g.add_node("perfurar", {"d_min": 0.005, "d_max": 0.03})
        g.connect(q, "pontos", f, "pontos")
        g.connect(grad, "campo", f, "campo")
        o = g.add_node("area_aberta", {"alvo": 20.0, "por_modulo": each})
        g.connect(f, "furos", o, "furos")
        c = g.add_node("verificar_fabrico", {"ponte_min": 0.001})
        g.connect(o, "furos", c, "furos")
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        return out[c]["relatorio"]

    def test_each_module_or_the_whole(self):
        whole = self._graph(False)
        self.assertEqual(len(whole["modules"]), 3)
        self.assertGreater(max(whole["modules"]) - min(whole["modules"]), 0.05)     # (the gradient: unequal)
        each = self._graph(True)
        self.assertTrue(all(abs(m - 0.20) < 0.002 for m in each["modules"]), each["modules"])
        from arqbim.core.graph import nodes_logic
        self.assertEqual(len(nodes_logic.modules_of({"shape": __import__("shapely").box(0, 0, 1, 1)})), 1)


def polygon_sketch(doc, pts, name="Polígono"):
    """A flat face drawn (a polygon) — world points (x, y, z)."""
    from arqbim.core.mesh import PolyMesh
    from arqbim.model.document import AddObject, SketchObject
    obj = SketchObject(name, np.eye(4), PolyMesh([np.array(p, float) for p in pts], [list(range(len(pts)))]))
    doc.execute(AddObject(obj))
    return obj


class AnyFace(unittest.TestCase):
    """0.553 — a polygon (any flat face drawn, at any angle) takes an operator: a perforated panel on it."""

    HEX = [(2 * np.cos(a), 2 * np.sin(a), 0.5) for a in np.radians(np.arange(0, 360, 60))]

    def test_level_polygon(self):
        from arqbim.core.graph import sketch_host
        doc = Document()
        obj = polygon_sketch(doc, self.HEX)
        self.assertEqual(operators.host_wall(doc, obj.id), obj.id)
        frame, face = sketch_host.plane_of(obj)
        self.assertAlmostEqual(face.area, 6 * np.sqrt(3) / 4 * 4, places=4)
        np.testing.assert_allclose(frame[:3, 2], (0, 0, 1), atol=1e-9)
        made = operators.apply_to(doc, operators.starter(), obj.id)
        self.assertEqual(len(made), 1)
        panel = made[0]
        self.assertEqual(doc.ifc.kind_of(panel), "plane_panel")
        self.assertEqual(doc.ifc.by_guid(panel).is_a(), "IfcPlate")
        got = doc.ifc.plane_panel_perforation(panel)
        self.assertGreater(got["count"], 500)
        verts, _f = doc.ifc.triangulate([panel])[panel]
        self.assertTrue(np.all(verts[:, 2] > 0.5) and np.all(verts[:, 2] < 0.51))   # (on it, its side up)
        self.assertLess(np.hypot(verts[:, 0], verts[:, 1]).max(), 2.0 + 1e-6)
        self.assertEqual(operators.finishes_of(doc, [obj.id]), [panel])            # (the polygon chosen: its panel)
        self.assertEqual(operators.finishes_of(doc, [panel]), [panel])
        self.assertIn(panel, {r["guid"] for r in schedules.rows(doc, "perforated")})
        g = operators.operator_of(doc, panel)["graph"]
        g.set_param("n2", "passo", 0.3)
        operators.update(doc, panel, g)
        self.assertLess(doc.ifc.plane_panel_perforation(panel)["count"], got["count"] / 4)
        operators.remove(doc, panel)
        self.assertIsNone(doc.ifc.by_guid(panel))
        doc.undo()
        self.assertIsNotNone(doc.ifc.by_guid(panel))

    def test_sloping_face_and_following_it(self):
        from arqbim.core.graph import sketch_host
        doc = Document()
        pts = [(0, 0, 0), (4, 0, 0), (4, 3, 2), (0, 3, 2)]                          # (a roof pitch)
        obj = polygon_sketch(doc, pts)
        frame, face = sketch_host.plane_of(obj)
        self.assertAlmostEqual(frame[2, 0], 0.0, places=9)                         # (its x level)
        self.assertAlmostEqual(face.area, 4 * np.hypot(3, 2), places=4)
        panel = operators.apply_to(doc, operators.starter(), obj.id)[0]
        verts, _f = doc.ifc.triangulate([panel])[panel]
        n = frame[:3, 2]
        d = (verts - pts[0]) @ n
        self.assertTrue(np.all(d > 0) and np.all(d < 0.006))                      # (on the face, off its side)
        before = doc.ifc.plane_panel_perforation(panel)["count"]
        live = doc.get(obj.id)                                                     # (the model's own sketch)
        live.mesh.verts[1] = np.array((8.0, 0.0, 0.0))                            # (the face drawn bigger…)
        live.mesh.verts[2] = np.array((8.0, 3.0, 2.0))
        operators.update(doc, panel)                                               # (…«Atualizar o aplicado»)
        self.assertGreater(doc.ifc.plane_panel_perforation(panel)["count"], before * 1.6)

    def test_upright_face_in_the_editor(self):
        from arqbim.ui import visual_graph as vg
        doc = Document()
        obj = polygon_sketch(doc, [(0, 0, 0), (3, 0, 0), (3, 0, 2), (0, 0, 2)])
        nodes_3d.MODEL["doc"] = doc
        main = types.SimpleNamespace(doc=doc, viewport=types.SimpleNamespace(selection={obj.id}))
        win = vg.GraphWindow(graph=None, wall=obj.id, side="frente")
        win.main = main
        win.set_target(obj.id, "frente")
        self.assertIn("face desenhada", win.target_label.text())
        self.assertAlmostEqual(win.results["n1"]["painel"]["width"], 3.0)
        tris, _c = vg.model_preview(doc, vg.final_result(win.graph, win.results)[2])
        y = tris[:, :, 1]
        self.assertTrue(np.all(np.abs(y) < 0.01) and np.all(y != 0))               # (on the face, off one side)
        made = win.apply_to_model()
        self.assertEqual(len(made), 1)
        self.assertEqual(win.apply_to_model(), made)                               # (again: that panel)
        win.close()


class CustomMatrix(unittest.TestCase):
    """0.553 — a motif of one's own (points in a cell, each its size) repeated over the surface."""

    def test_matrix(self):
        from arqbim.core.graph import nodes_logic
        motif = nodes_logic.read_motif("0.25,0.5,1 0.75,0.5,0.4")
        self.assertEqual(motif, [(0.25, 0.5, 1.0), (0.75, 0.5, 0.4)])
        with self.assertRaises(ValueError):
            nodes_logic.read_motif("")
        g = Graph()
        p = g.add_node("painel_plano", {"largura": 2.0, "altura": 1.0, "margem": 0.0})
        m = g.add_node("matriz", {"largura": 0.2, "altura": 0.2, "motivo": "0.25,0.5,1 0.75,0.5,0.4"})
        g.connect(p, "painel", m, "painel")
        f = g.add_node("perfurar", {"d_min": 0.05, "d_max": 0.05})
        g.connect(m, "pontos", f, "pontos")
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        pts = out[m]["pontos"]
        self.assertAlmostEqual(pts["pitch"], 0.1)
        self.assertEqual(sorted(set(np.round(out[f]["furos"]["d"], 4))), [0.02, 0.05])   # (two sizes, as drawn)
        self.assertGreaterEqual(len(pts["xy"]), 90)                                # (10 × 5 cells, two a cell)
        g.set_param(m, "desvio", 0.5)                                               # (every other row shifted)
        g.set_param(m, "motivo", "0.5,0.5,1")
        xy = g.evaluate()[m]["pontos"]["xy"]
        rows = sorted(set(np.round(xy[:, 1], 6)))
        first = np.sort(xy[np.isclose(xy[:, 1], rows[0]), 0])
        second = np.sort(xy[np.isclose(xy[:, 1], rows[1]), 0])
        self.assertAlmostEqual((second[0] - first[0]) % 0.2, 0.1, places=6)
        g.set_param(m, "motivo", "0.25,0.5,1 0.75,0.5,0.4")
        e = g.add_node("escolher_pontos", {"limiar": 0.5})                           # (sizes go with the points)
        z = g.add_node("mascara", {"x": 0.5, "y": 0.5, "largura": 1.0, "altura": 1.0})
        g.connect(m, "pontos", e, "pontos")
        g.connect(z, "campo", e, "campo")
        out = g.evaluate()
        self.assertEqual(len(out[e]["pontos"]["w"]), len(out[e]["pontos"]["xy"]))

    def test_template_and_motif_window(self):
        from arqbim.core.graph import templates
        from arqbim.ui import motif_drawing
        g = templates.make("matriz_motivo")
        nodes_3d.MODEL["doc"] = None
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        rep = next(v["relatorio"] for v in out.values() if "relatorio" in v)
        self.assertTrue(rep["ok"], rep["problems"])
        dlg = motif_drawing.MotifDrawing("")
        self.assertEqual(len(dlg.pad.points), 4)
        dlg.pad.set_points(dlg.ready["Cruz de cinco"])
        dlg._accept()
        self.assertEqual(len(motif_drawing.nodes_logic.read_motif(dlg.result_text)), 5)
        out = os.environ.get("ARQ_SHOT_MOTIF")
        if out:
            dlg2 = motif_drawing.MotifDrawing(dlg.result_text, 1.0, 0.5)
            dlg2.resize(400, 500)
            dlg2.show()
            APP.processEvents()
            dlg2.grab().save(out)
            dlg2.close()
            dlg2.deleteLater()
        dlg.close()
        dlg.deleteLater()
        APP.processEvents()


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
