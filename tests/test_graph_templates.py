"""0.541 — Gráfico Visual, step 4: the ready graphs (picture → perforated panel and the others)."""

import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from arqbim.core.graph import Graph, templates  # noqa: E402


class Templates(unittest.TestCase):
    def test_all_work_out(self):
        for key in templates.TEMPLATES:
            if key == "imagem_painel":
                continue
            g = templates.make(key)
            g.evaluate()
            self.assertEqual(g.errors, {}, key)
            self.assertEqual(Graph.from_json(g.to_json()).to_json(), g.to_json())

    def test_picture_to_panel(self):
        try:
            import PySide6  # noqa: F401
        except ImportError:
            self.skipTest("sem Qt")
        folder = tempfile.mkdtemp()
        path = os.path.join(folder, "foto.pgm")
        w, h = 64, 32                                     # dark on the left, light on the right
        row = bytes(int(255 * x / (w - 1)) for x in range(w))
        with open(path, "wb") as fh:
            fh.write(b"P5 %d %d 255\n" % (w, h) + row * h)
        g = templates.make("imagem_painel", ficheiro=path)
        dxf = next(n for n, d in g.nodes.items() if d["type"] == "exportar_dxf")
        g.set_param(dxf, "ficheiro", os.path.join(folder, "painel.dxf"))
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        check = next(n for n, d in g.nodes.items() if d["type"] == "verificar_fabrico")
        holes = out[check]["furos"]
        left = holes["d"][holes["xy"][:, 0] < 0.6].mean()
        right = holes["d"][holes["xy"][:, 0] > 1.8]
        self.assertGreater(left, 0.015)
        self.assertTrue(len(right) == 0 or right.mean() < left / 2)
        rep = out[check]["relatorio"]
        self.assertEqual(rep["bad"], int(np.sum(holes["bad"])))
        self.assertEqual(rep["small"], 0)                 # (no hole under 4 mm is cut: fabricable from the start)
        self.assertTrue(os.path.exists(os.path.join(folder, "painel.dxf")))


if __name__ == "__main__":
    unittest.main()
