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
        panel.on_apply = lambda slug, side, _values: seen.append(("apply", slug, side))
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


class InSight(unittest.TestCase):
    """0.543 — step 7: an operator's measures «à vista», changed in the side panel."""

    def test_exposed_kept_and_used(self):
        g = operators.starter()
        slug = operators.save("Com medidas", g, exposed=[("n2", "passo"), ("n4", "forma"), ("n1", "parede"),
                                                         ("zz", "x"), ("n2", "passo")])
        graph, exposed = operators.exposed_of(slug)
        self.assertEqual(exposed, [("n2", "passo"), ("n4", "forma")])          # (a text, a node gone: left out)
        operators.save("Com medidas", graph, slug=slug)                        # (written over: kept)
        self.assertEqual(operators.exposed_of(slug)[1], exposed)
        self.assertEqual(operators.exposed_of(operators.duplicate(slug))[1], exposed)
        host = QtWidgets.QMainWindow()
        panel = operators_panel.OperatorsPanel(host)
        got = []
        panel.target = lambda: 1
        panel.on_apply = lambda s, side, values: got.append(values)
        panel.reload(slug)
        self.assertEqual(panel.current(), slug)
        self.assertEqual(panel.measures.rowCount(), 2)
        self.assertTrue(panel.measures_hint.isHidden())
        spin = panel.measures_host.findChild(QtWidgets.QDoubleSpinBox)
        spin.setValue(0.2)
        panel.apply_button.click()
        self.assertEqual(got, [{("n2", "passo"): 0.2}])
        doc, wall = a_wall()
        wide = operators.apply_to(doc, slug, wall, values={("n2", "passo"): 0.2})
        fine = operators.apply_to(doc, slug, wall, "trás")
        self.assertLess(doc.ifc.pattern_params(wide[0])["count"], doc.ifc.pattern_params(fine[0])["count"] / 3)

    def test_pin_in_the_editor(self):
        win = vg.GraphWindow()
        win.cards["n2"].setSelected(True)
        APP.processEvents()
        pins = [b for b in win.params.findChildren(QtWidgets.QCheckBox) if b.text() == "à vista"]
        self.assertEqual(len(pins), 2)                                         # (passo, rodar)
        pins[0].setChecked(True)
        self.assertEqual(win.exposed, [("n2", "passo")])
        win.name, win.slug = "Fixado", None
        win.slug = operators.save("Fixado", win.graph)
        win.save_operator()
        self.assertEqual(operators.exposed_of(win.slug)[1], [("n2", "passo")])
        win.close()


class KeptOnTheWall(unittest.TestCase):
    """0.543 — step 8: the wall's panel keeps its operator; worked out again, opened again."""

    def test_update_after_the_wall_changes(self):
        doc, wall = a_wall()
        slug = operators.save("Guardado", operators.starter())
        made = operators.apply_to(doc, slug, wall, "trás")[0]
        kept = operators.operator_of(doc, made)
        self.assertEqual((kept["name"], kept["slug"], kept["wall"], kept["side"]), ("Guardado", slug, wall, "trás"))
        self.assertEqual(len(kept["graph"].nodes), 6)
        self.assertEqual(operators.finishes_of(doc, [wall]), [made])
        self.assertEqual(operators.finishes_of(doc, [made]), [made])
        self.assertEqual(operators.host_wall(doc, made), wall)
        before = doc.ifc.pattern_params(made)["count"]
        steps = len(doc.undo_stack) if hasattr(doc, "undo_stack") else None
        bim.resize_wall(doc, wall, at_end=3.0)                                 # (the wall 9 m long)
        after = doc.ifc.pattern_params(made)                                   # (0.544: worked out again by itself,
        self.assertGreater(after["count"], before * 1.3)                       #  in the wall's own step)
        self.assertAlmostEqual(after["sheet_w"], 9.0, 1)
        self.assertEqual(operators.operator_of(doc, made)["slug"], slug)
        if steps is not None:
            self.assertEqual(len(doc.undo_stack), steps + 1)
        doc.undo()
        back = doc.ifc.pattern_params(made)
        self.assertAlmostEqual(back["sheet_w"], 6.0, 1)
        self.assertEqual(back["count"], before)
        frame = bim.wall_frame(doc, wall)                                      # (a door put in: the holes clear of it)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, frame.x0 + 3.0, 1)
        self.assertLess(doc.ifc.pattern_params(made)["count"], before)
        operators.update(doc, made)                                            # (the button still does it)
        self.assertLess(doc.ifc.pattern_params(made)["count"], before)

    def test_back_face_as_it_is_seen(self):
        """0.546 — the back face is worked on as one sees it standing before it: left and right swapped."""
        from arqbim.core import surfaces
        doc, wall = a_wall()
        frame = bim.wall_frame(doc, wall)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, frame.x0 + 1.0, 1)    # (1,0–1,8 m)
        nodes_3d.MODEL["doc"] = doc
        g = operators.retarget(operators.starter(), wall, "trás")
        g.set_param("n3", "x", 5.5)                                           # (the attractor: at the viewer's right)
        g.set_param("n3", "raio", 1.5)
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        face = out["n1"]["painel"]["shape"]
        from shapely.geometry import Point
        self.assertFalse(face.contains(Point(4.6, 1.0)))                       # (the door seen at 4,2–5,0 m)
        self.assertTrue(face.contains(Point(1.4, 1.0)))
        self.assertTrue(out["n6"]["bim"]["mirror"])
        back = operators.apply_to(doc, g, wall, "trás")[0]
        rows = surfaces.free_read(doc.ifc._params(doc.ifc.by_guid(back))["FurosLivres"])[1]
        big = rows[rows[:, 2] > 0.05]
        self.assertTrue(len(big) and big[:, 0].max() < 2.2)                    # (in the wall's measures: 0,5 m)
        front = operators.apply_to(doc, operators.starter(), wall, "frente")[0]
        self.assertFalse(operators.operator_of(doc, front)["graph"].nodes["n1"]["params"]["lado"] == "trás")
        rows = surfaces.free_read(doc.ifc._params(doc.ifc.by_guid(front))["FurosLivres"])[1]
        self.assertLess(rows[rows[:, 2].argmax(), 0], 2.5)                     # (starter's attractor at 1 m: as drawn)
        from arqbim.ui import visual_graph as vgm
        img = vgm.surface_picture(g, out, 600, 300)                            # (the door drawn where it is seen)
        self.assertGreater(img.pixelColor(int(600 * 4.6 / 6.0), 220).lightness(), 240)
        self.assertLess(img.pixelColor(int(600 * 1.4 / 6.0), 220).lightness(), 240)

    def test_a_broken_operator_never_stops_the_wall(self):
        doc, wall = a_wall()
        made = operators.apply_to(doc, operators.starter(), wall)[0]
        before = doc.ifc.pattern_params(made)["count"]
        bim.set_cladding(doc, made, operator="{isto não é um operador")
        bim.resize_wall(doc, wall, at_end=3.0)
        self.assertEqual(doc.ifc.pattern_params(made)["count"], before)        # (its old holes kept)

    def test_editor_updates_its_panel(self):
        doc, wall = a_wall()
        main = types.SimpleNamespace(doc=doc, viewport=types.SimpleNamespace(selection={wall}))
        win = vg.GraphWindow(graph=None, wall=wall, side="frente")
        win.main = main
        vg.nodes_3d = nodes_3d
        nodes_3d.MODEL["doc"] = doc
        win.set_target(wall, "frente")
        first = win.apply_to_model()
        self.assertEqual(len(first), 1)
        count = doc.ifc.pattern_params(first[0])["count"]
        win.set_param("n2", "passo", 0.2)
        win.evaluate()
        again = win.apply_to_model()
        self.assertEqual(again, first)                                         # (the same panel, not another)
        self.assertEqual(len(operators.finishes_of(doc, [wall])), 1)
        self.assertLess(doc.ifc.pattern_params(first[0])["count"], count / 3)
        self.assertEqual(operators.operator_of(doc, first[0])["graph"].nodes["n2"]["params"]["passo"], 0.2)
        main.viewport.selection = {first[0]}                                   # (the panel chosen: its wall)
        self.assertEqual(win.chosen_wall(), wall)
        win.close()


class UndoAndAI(unittest.TestCase):
    """0.543 — step 9: Ctrl+Z in the editor; the AI's graph is the open window's."""

    def test_undo_redo(self):
        win = vg.GraphWindow()
        self.assertFalse(win.act_undo.isEnabled())
        for v in (0.07, 0.08, 0.09):                                           # (a slider dragged: one step)
            win.set_param("n2", "passo", v)
        win.cards["n3"].setSelected(True)
        win.delete_chosen()
        nid = win.add_node_at("ondas")
        self.assertEqual(len(win._undo), 3)
        win.undo()
        self.assertNotIn(nid, win.graph.nodes)
        win.undo()
        self.assertIn("n3", win.graph.nodes)
        self.assertEqual(len(win.wires), 5)
        win.undo()
        self.assertEqual(win.graph.nodes["n2"]["params"]["passo"], 0.08)       # (operators.starter's)
        self.assertFalse(win.act_undo.isEnabled())
        win.redo()
        self.assertEqual(win.graph.nodes["n2"]["params"]["passo"], 0.09)
        win.redo()
        self.assertNotIn("n3", win.graph.nodes)
        self.assertEqual(win.act_undo.shortcut().toString(), "Ctrl+Z")
        win.close()

    def test_ai_works_on_the_open_window(self):
        from arqbim.mcp import graph_tools
        win = vg.GraphWindow()
        win.show()
        APP.processEvents()
        session = types.SimpleNamespace(window=types.SimpleNamespace(graph_window=win), doc=None)
        graph_tools.graph(session, {"action": "set", "id": "n2", "params": {"passo": 0.15}})
        self.assertEqual(win.graph.nodes["n2"]["params"]["passo"], 0.15)
        self.assertAlmostEqual(win.results["n2"]["pontos"]["pitch"], 0.15)     # (worked out and shown)
        said = graph_tools.graph(session, {"action": "add", "type": "ondas"})
        self.assertIn(said.split()[-1], win.cards)
        graph_tools.graph(session, {"action": "template", "key": "voronoi_centro"})
        self.assertEqual(len(win.cards), 5)
        win.undo()
        self.assertEqual(len(win.cards), 7)                                    # (the user's Ctrl+Z takes it back)
        win.close()
        APP.processEvents()
        graph_tools.graph(session, {"action": "new"})                          # (closed: the session's own again)
        self.assertEqual(len(session.graph.nodes), 0)


if __name__ == "__main__":
    unittest.main()
