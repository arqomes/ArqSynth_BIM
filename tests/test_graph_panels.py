"""0.539 — Gráfico Visual, step 2: the first 12 nodes (perforated panels), worked out as a graph."""

import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arqbim.core.graph import REGISTRY, Graph  # noqa: E402

TWELVE = ("painel_plano", "grelha", "hexagono", "voronoi", "atrator", "gradiente", "imagem", "ruido", "perfurar",
          "verificar_fabrico", "exportar_dxf", "aplicar_parede")


def _panel(g, w=1.0, h=0.5, margin=0.05):
    return g.add_node("painel_plano", {"largura": w, "altura": h, "margem": margin})


class Nodes(unittest.TestCase):
    def test_registered(self):
        for k in TWELVE:
            self.assertIn(k, REGISTRY)
        fams = {c["key"]: c["family"] for c in REGISTRY.catalog()}
        self.assertEqual(fams["voronoi"], "Padrões")
        self.assertEqual(fams["aplicar_parede"], "BIM")

    def test_grid_inside_margin(self):
        g = Graph()
        p = _panel(g)
        q = g.add_node("grelha", {"passo": 0.1})
        g.connect(p, "painel", q, "painel")
        xy = g.evaluate()[q]["pontos"]["xy"]
        self.assertEqual(len(xy), 9 * 3)                         # 0,9 × 0,4 inside, a 0,1 pitch, whole cells
        self.assertTrue((xy[:, 0] >= 0.1 - 1e-9).all() and (xy[:, 0] <= 0.9 + 1e-9).all())

    def test_hexagon_neighbours(self):
        g = Graph()
        p = _panel(g, 2.0, 2.0)
        q = g.add_node("hexagono", {"passo": 0.1})
        g.connect(p, "painel", q, "painel")
        xy = g.evaluate()[q]["pontos"]["xy"]
        d = np.hypot(*(xy[:, None] - xy[None]).transpose(2, 0, 1))
        np.fill_diagonal(d, 9)
        self.assertAlmostEqual(float(d.min()), 0.1, places=6)
        self.assertEqual(int((np.abs(d[len(xy) // 2] - 0.1) < 1e-6).sum()), 6)   # one in the middle: 6 neighbours

    def test_voronoi_denser_near_attractor(self):
        g = Graph()
        p = _panel(g, 2.0, 1.0, 0.0)
        a = g.add_node("atrator", {"x": 0.0, "y": 0.5, "raio": 1.0})
        v = g.add_node("voronoi", {"quantidade": 400, "relaxar": 0})
        g.connect(p, "painel", v, "painel")
        g.connect(a, "campo", v, "densidade")
        xy = g.evaluate()[v]["pontos"]["xy"]
        self.assertEqual(len(xy), 400)
        self.assertGreater((xy[:, 0] < 1.0).sum(), 2 * (xy[:, 0] >= 1.0).sum())
        g.set_param(v, "relaxar", 3)
        self.assertEqual(len(g.evaluate()[v]["pontos"]["xy"]), 400)

    def test_perforate_with_gradient_and_check(self):
        g = Graph()
        p = _panel(g)
        q = g.add_node("grelha", {"passo": 0.05})
        gr = g.add_node("gradiente")
        f = g.add_node("perfurar", {"d_min": 0.0, "d_max": 0.04})
        c = g.add_node("verificar_fabrico", {"furo_min": 0.006, "ponte_min": 0.003})
        g.connect(p, "painel", q, "painel")
        g.connect(p, "painel", gr, "painel")
        g.connect(q, "pontos", f, "pontos")
        g.connect(gr, "campo", f, "campo")
        g.connect(f, "furos", c, "furos")
        out = g.evaluate()
        holes, rep = out[c]["furos"], out[c]["relatorio"]
        left, right = holes["d"][holes["xy"][:, 0] < 0.3], holes["d"][holes["xy"][:, 0] > 0.7]
        self.assertLess(left.mean(), right.mean())
        self.assertFalse(rep["ok"])                              # 4 cm holes at 5 cm: 1 cm bridge ok — but the
        self.assertGreater(rep["small"], 0)                      # left's tiny holes fail
        self.assertEqual(rep["bad"], int(holes["bad"].sum()))
        g.set_param(f, "d_min", 0.01)
        g.set_param(f, "d_max", 0.03)
        rep = g.evaluate()[c]["relatorio"]
        self.assertTrue(rep["ok"], rep["problems"])
        self.assertTrue(0.02 < rep["min_bridge"] < 0.025, rep["min_bridge"])   # 5 cm apart, ~2,8 cm holes
        g.set_param(f, "d_min", 0.048)
        g.set_param(f, "d_max", 0.048)
        rep = g.evaluate()[c]["relatorio"]
        self.assertGreater(rep["bridges"], 0)                    # 2 mm bridges: too thin

    def test_noise_and_attractor_ranges(self):
        g = Graph()
        n = g.add_node("ruido", {"escala": 0.3})
        a = g.add_node("atrator", {"x": 0, "y": 0, "raio": 1})
        out = g.evaluate()
        xy = np.random.default_rng(0).uniform(-2, 2, (500, 2))
        v = out[n]["campo"](xy)
        self.assertTrue(((v >= 0) & (v <= 1)).all() and v.std() > 0.05)
        self.assertEqual(out[a]["campo"]([(0, 0)])[0], 1.0)
        self.assertEqual(out[a]["campo"]([(5, 0)])[0], 0.0)

    def test_image_field(self):
        try:
            import PySide6  # noqa: F401
        except ImportError:
            self.skipTest("sem Qt")
        path = os.path.join(tempfile.mkdtemp(), "meio.pgm")
        with open(path, "wb") as fh:                               # left half black, right half white
            fh.write(b"P5 4 2 255\n" + bytes([0, 0, 255, 255] * 2))
        g = Graph()
        p = _panel(g, 2.0, 1.0)
        im = g.add_node("imagem", {"ficheiro": path})
        g.connect(p, "painel", im, "painel")
        f = g.evaluate()[im]["campo"]
        self.assertGreater(f([(0.4, 0.5)])[0], 0.9)
        self.assertLess(f([(1.6, 0.5)])[0], 0.1)
        g.set_param(im, "ficheiro", "")
        g.evaluate()
        self.assertEqual(g.errors[im], "escolha uma imagem")

    def test_dxf_and_bim(self):
        g = Graph()
        p = _panel(g)
        q = g.add_node("hexagono", {"passo": 0.1})
        f = g.add_node("perfurar", {"d_max": 0.05})
        path = os.path.join(tempfile.mkdtemp(), "painel.dxf")
        x = g.add_node("exportar_dxf", {"ficheiro": path})
        b = g.add_node("aplicar_parede", {"parede": "abc"})
        g.connect(p, "painel", q, "painel")
        g.connect(q, "pontos", f, "pontos")
        g.connect(f, "furos", x, "furos")
        g.connect(f, "furos", b, "furos")
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        n = len(out[f]["furos"]["xy"])
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertEqual(text[text.find("ENTITIES"):].count("\nFUROS\n"), n)   # one entity per hole
        self.assertIn("CONTORNO", text)
        self.assertTrue(text.rstrip().endswith("EOF"))
        self.assertEqual(len(out[b]["bim"]["holes"]), n)
        self.assertEqual(out[b]["bim"]["wall"], "abc")
        g2 = Graph.from_json(g.to_json())                        # the whole graph round its JSON
        self.assertEqual(len(g2.evaluate()[b]["bim"]["holes"]), n)


if __name__ == "__main__":
    unittest.main()
