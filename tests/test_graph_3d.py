"""0.542 — Gráfico Visual, step 5: Subdividir, Extrudir, Relevo, Dobrar, Fachada do modelo."""

import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from arqbim.core.graph import Graph, nodes_3d  # noqa: E402


def _holes(g, w=1.0, h=0.5):
    p = g.add_node("painel_plano", {"largura": w, "altura": h, "margem": 0.05, "espessura": 0.004})
    q = g.add_node("grelha", {"passo": 0.1})
    f = g.add_node("perfurar", {"d_max": 0.04})
    g.connect(p, "painel", q, "painel")
    g.connect(q, "pontos", f, "pontos")
    return p, q, f


class Nodes3D(unittest.TestCase):
    def test_subdivide(self):
        g = Graph()
        p, q, f = _holes(g, 3.0, 1.0)
        s = g.add_node("subdividir", {"colunas": 3, "junta": 0.02})
        g.connect(p, "painel", s, "painel")
        g.connect(s, "painel", q, "painel")
        x = g.add_node("exportar_dxf", {"ficheiro": os.path.join(tempfile.mkdtemp(), "m.dxf")})
        g.connect(f, "furos", x, "furos")
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        self.assertEqual(out[s]["painel"]["modules"], 3)
        xy = out[q]["pontos"]["xy"]
        self.assertFalse(((xy[:, 0] > 0.95) & (xy[:, 0] < 1.05)).any())   # nothing on the joint's margins

    def test_extrude_and_fold(self):
        g = Graph()
        _p, _q, f = _holes(g)
        e = g.add_node("extrudir")
        d = g.add_node("dobrar", {"posicao": 0.1, "angulo": 90.0})
        g.connect(f, "furos", e, "furos")
        g.connect(e, "malha", d, "malha")
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        v = out[e]["malha"]["verts"]
        self.assertAlmostEqual(v[:, 2].max(), 0.004)
        folded = out[d]["malha"]["verts"]
        self.assertAlmostEqual(folded[:, 2].max(), 0.1, places=6)          # the 10 cm flange stands up
        self.assertGreaterEqual(folded[:, 0].min(), 0.1 - 1e-9)             # (nothing left before the line)

    def test_relief(self):
        g = Graph()
        p = g.add_node("painel_plano", {"largura": 1.0, "altura": 1.0, "margem": 0.0})
        a = g.add_node("atrator", {"x": 0.5, "y": 0.5, "raio": 0.5})
        rl = g.add_node("relevo", {"altura": 0.05, "resolucao": 0.05})
        g.connect(p, "painel", rl, "painel")
        g.connect(a, "campo", rl, "campo")
        m = g.evaluate()[rl]["malha"]
        self.assertAlmostEqual(m["verts"][:, 2].max(), 0.053, places=6)
        self.assertEqual(len(m["tris"]), 2 * 20 * 20)

    def test_facade_from_model(self):
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        g = Graph()
        fb = g.add_node("fachada_bim", {"parede": wall})
        nodes_3d.MODEL["doc"] = None
        self.assertAlmostEqual(g.evaluate()[fb]["painel"]["width"], 4.0)     # (0.541: no model — the example face)
        nodes_3d.MODEL["doc"] = doc
        try:
            g.set_param(fb, "margem", 0.06)                  # (a new key: worked out again)
            panel = g.evaluate()[fb]["painel"]
        finally:
            nodes_3d.MODEL["doc"] = None
        self.assertAlmostEqual(panel["width"], 5.0, places=3)
        self.assertGreater(panel["height"], 2.0)

    def test_pictures(self):
        from arqbim.ui import visual_graph as vg
        from PySide6 import QtWidgets
        QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        g = Graph()
        _p, _q, f = _holes(g)
        e = g.add_node("extrudir")
        g.connect(f, "furos", e, "furos")
        img = vg.picture("mesh", g.evaluate()[e]["malha"], 200, 120)
        self.assertFalse(img.isNull())


if __name__ == "__main__":
    unittest.main()
