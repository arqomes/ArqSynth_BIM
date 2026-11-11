"""0.541 — Gráfico Visual, 2.ª fase: the library of operators (outside the project), the surface of the model as the
graph's start, the editor on it (live picture, Shift+A's menu, «Guardar operador»), the side panel."""

import os
import sys
import tempfile
import types
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["ARQSYNTH_HOME"] = tempfile.mkdtemp(prefix="arqsynth_ops_")      # (never the owner's library)

from PySide6 import QtCore, QtWidgets  # noqa: E402

from arqbim.core.graph import nodes_3d, operators  # noqa: E402
from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import Document  # noqa: E402
from arqbim.ui import operators_panel, visual_graph as vg  # noqa: E402

APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def a_wall(length=6.0):
    doc = Document()
    wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((length, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
    return doc, wall


class Library(unittest.TestCase):
    def test_seeded_saved_and_found_again(self):
        names = [op["name"] for op in operators.listing()]
        self.assertIn("Atrator em favo", names)                     # (the program's own, the first time)
        self.assertNotIn("Imagem → painel perfurado", names)
        slug = operators.save("Fachada às bolinhas", operators.starter(), png=b"\x89PNG")
        self.assertEqual(slug, "fachada_as_bolinhas")
        self.assertTrue(os.path.dirname(operators.thumbnail_path(slug)).startswith(os.environ["ARQSYNTH_HOME"]))
        name, _about, graph = operators.load(slug)
        self.assertEqual((name, len(graph.nodes)), ("Fachada às bolinhas", 6))
        other = operators.save("Fachada às bolinhas", operators.starter())
        self.assertNotEqual(other, slug)                            # (a second of the same name: its own file)
        copy = operators.duplicate(slug)
        self.assertTrue(os.path.exists(operators.thumbnail_path(copy)))
        operators.rename(copy, "Outra")
        self.assertEqual(operators.load(copy)[0], "Outra")
        out = os.path.join(tempfile.mkdtemp(), "o.json")
        operators.export_to(slug, out)
        back = operators.import_from(out)
        self.assertEqual(operators.load(back)[0], "Fachada às bolinhas")
        for s in (other, copy, back):
            operators.delete(s)
        self.assertEqual(sum(op["name"] == "Fachada às bolinhas" for op in operators.listing()), 1)

    def test_the_wall_is_not_kept(self):
        g = operators.starter()
        operators.retarget(g, "UMA_PAREDE", "trás")
        slug = operators.save("Sem parede", g)
        kept = operators.load(slug)[2]
        self.assertEqual({d["params"]["parede"] for d in kept.nodes.values() if "parede" in d["params"]}, {""})

    def test_surface_of_the_model(self):
        doc, wall = a_wall()
        frame = bim.wall_frame(doc, wall)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, frame.x0 + 3.0, 1)
        face = nodes_3d.wall_face(doc, wall)
        self.assertAlmostEqual(face.bounds[2], 6.0, 1)
        self.assertLess(face.area, 6.0 * face.bounds[3] - 1.0)      # (its door left out)
        self.assertFalse(face.contains(__import__("shapely").Point(3.4, 1.0)))
        self.assertEqual(len(nodes_3d.example_face().interiors), 1)
        nodes_3d.MODEL["doc"] = None
        self.assertAlmostEqual(nodes_3d.target_face("x").bounds[2], 4.0)    # (no model: the example face)

    def test_apply_to_a_wall_whole(self):
        doc, wall = a_wall()
        made = operators.apply_to(doc, operators.starter(), wall, "trás")
        self.assertEqual(len(made), 1)
        p = doc.ifc.pattern_params(made[0])
        self.assertGreater(p["count"], 500)
        self.assertAlmostEqual(p["sheet_w"], 6.0, 1)                # (the face whole: one board, not repeated)
        self.assertEqual(int(doc.ifc._params(doc.ifc.by_guid(made[0])).get("Lado")), -1)

    def test_apply_a_module_repeats(self):
        doc, wall = a_wall()
        slug = next(op["slug"] for op in operators.listing() if op["name"] == "Atrator em favo")
        made = operators.apply_to(doc, slug, wall)
        g = operators.load(slug)[2]
        per_panel = len(g.evaluate()["n6"]["bim"]["holes"])
        self.assertGreaterEqual(doc.ifc.pattern_params(made[0])["count"], 2 * per_panel)


class Editor(unittest.TestCase):
    def setUp(self):
        self.doc, self.wall = a_wall()
        self.main = types.SimpleNamespace(doc=self.doc, viewport=types.SimpleNamespace(selection={self.wall}))
        self.win = vg.GraphWindow(graph=None, wall="", side="frente")
        self.win.main = self.main
        self.win.show()
        APP.processEvents()

    def tearDown(self):
        self.win.close()

    def test_surface_follows_the_graph(self):
        w = self.win
        self.assertIn("exemplo", w.target_label.text())
        self.assertIn("fabric", w.verdict.text() + "fabric")
        first = vg.surface_picture(w.graph, w.results, 400, 300)
        w.set_param("n4", "d_max", 0.02)
        w.evaluate()
        second = vg.surface_picture(w.graph, w.results, 400, 300)
        self.assertNotEqual(first, second)                          # (the surface changed with the measure)
        w.take_chosen_wall()
        self.assertEqual(w.wall, self.wall)
        self.assertAlmostEqual(w.results["n1"]["painel"]["width"], 6.0, 1)
        self.assertEqual(w.graph.nodes["n6"]["params"]["parede"], self.wall)
        w.side_box.setCurrentText("trás")
        self.assertEqual(w.graph.nodes["n6"]["params"]["lado"], "trás")
        made = w.apply_to_model()
        self.assertEqual(len(made), 1)
        out = os.environ.get("ARQ_SHOT")
        if out:
            w.grab().save(out)

    def test_shift_a_menu(self):
        w = self.win
        w.ask_node()
        menu = w.node_menu
        self.assertTrue(menu.isVisible())
        self.assertGreater(len(menu.keys()), 12)
        with_picture = sum(not menu.list.item(k).icon().isNull() for k in range(menu.list.count()))
        self.assertGreater(with_picture, 12)                        # (each with the picture of what it does)
        menu.search.setText("voron")
        self.assertEqual(menu.keys(), ["voronoi"])
        before = len(w.cards)
        menu._pick(menu.list.currentItem())
        self.assertEqual(len(w.cards), before + 1)
        self.assertFalse(menu.isVisible())
        out = os.environ.get("ARQ_SHOT_MENU")
        if out:
            w.ask_node()
            APP.processEvents()
            w.node_menu.grab().save(out)
            w.node_menu.hide()

    def test_shift_a_key(self):
        from PySide6 import QtGui
        w = self.win
        event = QtGui.QKeyEvent(QtCore.QEvent.Type.KeyPress, QtCore.Qt.Key.Key_A,
                                QtCore.Qt.KeyboardModifier.ShiftModifier, "A")
        w.view.keyPressEvent(event)
        self.assertTrue(w.node_menu is not None and w.node_menu.isVisible())
        w.node_menu.hide()

    def test_node_joined_logically(self):
        w = self.win
        w.scene.clearSelection()
        wire = next(x for x in w.wires if x.link == ("n1", "painel", "n2", "painel"))
        wire.setSelected(True)
        nid = w.add_node_at("subdividir")                           # (in the middle of the chosen wire)
        self.assertIn(("n1", "painel", nid, "painel"), w.graph.links)
        self.assertIn((nid, "painel", "n2", "painel"), w.graph.links)
        w.scene.clearSelection()
        w.cards["n4"].setSelected(True)
        solid = w.add_node_at("extrudir")                           # (after the chosen card)
        self.assertIn(("n4", "furos", solid, "furos"), w.graph.links)

    def test_save_as_operator(self):
        w = self.win
        w.name = "Do teste"
        w.slug = operators.save("Do teste", w.graph)
        w.set_param("n2", "passo", 0.2)
        self.assertEqual(w.save_operator(), w.slug)
        self.assertEqual(operators.load(w.slug)[2].nodes["n2"]["params"]["passo"], 0.2)
        self.assertTrue(os.path.getsize(operators.thumbnail_path(w.slug)) > 500)


class Panel(unittest.TestCase):
    def test_panel(self):
        host = QtWidgets.QMainWindow()
        panel = operators_panel.OperatorsPanel(host)
        seen = []
        chosen = [0]
        panel.target = lambda: chosen[0]
        panel.on_apply = lambda slug, side: seen.append(("apply", slug, side))
        panel.on_new = lambda side: seen.append(("new", side))
        panel.on_edit = lambda slug, side: seen.append(("edit", slug, side))
        panel.reload()
        self.assertGreaterEqual(panel.list.count(), 4)
        self.assertFalse(panel.list.item(0).icon().isNull())        # (its thumbnail drawn)
        self.assertFalse(panel.apply_button.isEnabled())            # (no wall chosen)
        self.assertIn("Nenhuma", panel.target_label.text())
        chosen[0] = 2
        panel.refresh_target()
        self.assertTrue(panel.apply_button.isEnabled())
        panel.apply_button.click()
        panel.side.setCurrentText("trás")
        panel.edit_button.click()
        panel.new_button.click()
        slug = panel.current()
        self.assertEqual(seen, [("apply", slug, None), ("edit", slug, "trás"), ("new", "trás")])
        panel.search.setText("voronoi")
        self.assertEqual(sum(not panel.list.item(k).isHidden() for k in range(panel.list.count())), 1)


if __name__ == "__main__":
    unittest.main()
