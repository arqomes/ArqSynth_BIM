"""0.540 — Gráfico Visual, step 3: the window (cards, wires, measures, pictures) — no model, offscreen."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6 import QtWidgets  # noqa: E402

from arqbim.ui import visual_graph as vg  # noqa: E402

APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class Window(unittest.TestCase):
    def setUp(self):
        self.win = vg.GraphWindow()
        self.win.show()
        APP.processEvents()

    def tearDown(self):
        self.win.close()

    def test_starter_graph_pictures(self):
        self.assertEqual(len(self.win.cards), 6)
        self.assertEqual(len(self.win.wires), 5)
        self.assertEqual(self.win.graph.errors, {"n6": self.win.graph.errors.get("n6")} if "n6" in
                         self.win.graph.errors else {})
        for nid, card in self.win.cards.items():
            self.assertIsNotNone(card.image, nid)
        out = os.environ.get("ARQ_SHOT")
        if out:
            self.win.cards["n4"].setSelected(True)
            APP.processEvents()
            self.win.grab().save(out)

    def test_palette_link_and_params(self):
        top = self.win.palette.topLevelItem(0)
        item = next(top.child(k) for k in range(top.childCount())
                    if top.child(k).data(0, 256) == "painel_plano")     # Base ▸ Painel plano
        nid = self.win.add_from_palette(item)
        self.assertIn(nid, self.win.graph.nodes)
        self.win.scene.clearSelection()
        self.win.cards[nid].setSelected(True)
        APP.processEvents()
        self.assertEqual(self.win.params.nid, nid)
        self.assertEqual(self.win.params.form.rowCount(), 4)
        self.win.set_param(nid, "largura", 99)
        self.assertEqual(self.win.graph.nodes[nid]["params"]["largura"], 12.0)
        self.win._link("n2", "pontos", "n4", "campo")             # points into a field: refused, nothing changes
        self.assertEqual(len(self.win.wires), 5)
        self.win._link(nid, "painel", "n2", "painel")             # a new panel replaces the old link
        self.assertEqual(len(self.win.wires), 5)
        self.win.evaluate()
        self.assertEqual(self.win.results["n2"]["pontos"]["panel"]["width"], 12.0)

    def test_delete_and_files(self):
        self.win.cards["n3"].setSelected(True)
        self.win.delete_chosen()
        self.assertNotIn("n3", self.win.graph.nodes)
        self.assertEqual(len(self.win.wires), 4)
        path = os.path.join(tempfile.mkdtemp(), "g.json")
        self.assertTrue(self.win.save_graph(path))
        self.win.new_graph()
        self.assertEqual(self.win.cards, {})
        self.assertTrue(self.win.open_graph(path))
        self.assertEqual(len(self.win.cards), 5)

    def test_apply_to_a_wall(self):
        import types

        import numpy as np

        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        main = types.SimpleNamespace(doc=doc, viewport=types.SimpleNamespace(selection={wall}))
        self.win.main = main
        self.assertEqual(self.win.chosen_wall(), wall)
        made = self.win.apply_to_model()
        self.assertEqual(len(made), 1)
        d = doc.ifc.pattern_params(made[0])
        per_panel = len(self.win.results["n6"]["bim"]["holes"])
        self.assertGreaterEqual(d["count"], 2 * per_panel)       # two 3 m boards along the 6 m wall (at least)

    def test_report_picture(self):
        rep = {"ok": False, "bad": 3, "holes": 10, "open_area": 0.3, "min_bridge": 0.001, "problems": ["x"]}
        img = vg.picture("report", rep, 200, 120)
        self.assertFalse(img.isNull())


if __name__ == "__main__":
    unittest.main()
