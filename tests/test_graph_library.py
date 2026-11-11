"""0.544 — Gráfico Visual, step 7: every node at work (the palette's loop) and the perforated panels' table."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from arqbim.core.graph import REGISTRY, examples  # noqa: E402


class Library(unittest.TestCase):
    def test_every_node_plays(self):
        for key in REGISTRY.keys():
            if key == "imagem":
                continue                                   # (needs a picture: shown with its message)
            g, nid, sweep = examples.example(key)
            for k in (0, 6, 12):
                if sweep:
                    g.set_param(nid, sweep[0], examples.frame_value(sweep, k, 24))
                out = g.evaluate()
                self.assertIn(nid, out, "{}: {}".format(key, g.errors))

    def test_loop_has_no_jump(self):
        s = ("x", 0.0, 1.0)
        values = [examples.frame_value(s, k, 24) for k in range(25)]
        self.assertEqual(values[0], 0.0)
        self.assertEqual(values[12], 1.0)
        self.assertEqual(values[24], values[0])

    def test_palette_demo(self):
        from PySide6 import QtWidgets

        from arqbim.ui import visual_graph as vg
        QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        for key in ("grelha", "atrator", "perfurar", "extrudir"):      # (0.541: each node's picture, Shift+A's menu)
            self.assertIsNotNone(vg.node_thumb(key), key)

    def test_table(self):
        from arqbim.core.graph import templates
        from arqbim.core.graph.nodes_panels import cladding_pattern
        from arqbim.ifc import catalog
        from arqbim.model import bim, schedules
        from arqbim.model.document import Document
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        g = templates.atrator_hexagono()
        out = g.evaluate()
        bim.add_cladding(doc, wall, 1, "perfurado", 0.0, cladding_pattern(out["n6"]["bim"]))
        self.assertEqual(schedules.counts(doc)["perforated"], 1)
        row = schedules.rows(doc, "perforated")[0]
        self.assertGreaterEqual(row["panels"], 2)
        self.assertGreater(row["holes"], 1000)
        self.assertTrue(0 < row["open_area"] < 100)
        self.assertIn("perforated", schedules.ORDER)


if __name__ == "__main__":
    unittest.main()
