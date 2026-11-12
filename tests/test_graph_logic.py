"""0.542 — Gráfico Visual, 2.ª fase, step 6: the logic nodes (modulators from the surface, mixing, remapping, points
chosen and joined, holes brought to an open area and corrected for fabrication) and the ready graphs that use them."""

import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["ARQSYNTH_HOME"] = tempfile.mkdtemp(prefix="arqsynth_logic_")

from arqbim.core.graph import Graph, nodes_3d, nodes_logic, operators, templates  # noqa: E402


def surface(g):
    nodes_3d.MODEL["doc"] = None
    return g.add_node("fachada_bim")                     # (the example face: 4 × 2,7 m, a window 1,4–2,6 × 0,9–2,1)


def field_of(key, params=None, panel=False):
    g = Graph()
    n = g.add_node(key, params or {})
    if panel:
        g.connect(surface(g), "painel", n, "painel")
    out = g.evaluate()
    assert not g.errors, g.errors
    return out[n]["campo"]


class Modulators(unittest.TestCase):
    def test_near_the_openings(self):
        f = field_of("distancia_vaos", {"alcance": 0.5}, panel=True)
        v = f(np.array([(1.35, 1.5), (1.15, 1.5), (0.2, 0.2)]))
        self.assertGreater(v[0], 0.9)
        self.assertTrue(0.3 < v[1] < 0.7)
        self.assertEqual(v[2], 0.0)
        inv = field_of("distancia_vaos", {"alcance": 0.5, "inverter": True}, panel=True)
        self.assertEqual(inv(np.array([(0.2, 0.2)]))[0], 1.0)

    def test_near_the_outline_and_a_line(self):
        f = field_of("distancia_contorno", {"alcance": 0.4}, panel=True)
        v = f(np.array([(0.01, 1.0), (0.7, 0.45)]))
        self.assertGreater(v[0], 0.95)
        self.assertEqual(v[1], 0.0)
        line = field_of("distancia_linha", {"x1": 0, "y1": 0, "x2": 4, "y2": 0, "alcance": 1.0})
        w = line(np.array([(2.0, 0.0), (2.0, 0.5), (2.0, 2.0), (6.0, 0.0)]))
        self.assertEqual((w[0], w[2], w[3]), (1.0, 0.0, 0.0))
        self.assertAlmostEqual(w[1], 0.5)

    def test_zone_waves_random(self):
        z = field_of("mascara", {"x": 1, "y": 1, "largura": 1, "altura": 0.5})
        self.assertEqual(list(z(np.array([(1.2, 1.1), (1.6, 1.0), (1.0, 1.3)]))), [1.0, 0.0, 0.0])
        e = field_of("mascara", {"x": 1, "y": 1, "largura": 1, "altura": 1, "forma": "elipse", "inverter": True})
        self.assertEqual(list(e(np.array([(1.0, 1.0), (1.45, 1.45)]))), [0.0, 1.0])
        w = field_of("ondas", {"comprimento": 1.0})
        self.assertAlmostEqual(w(np.array([(0.25, 0.0)]))[0], 1.0)
        self.assertAlmostEqual(w(np.array([(0.75, 3.0)]))[0], 0.0)
        r1 = field_of("aleatorio", {"tamanho": 0.1, "semente": 3})
        pts = np.random.default_rng(0).uniform(0, 3, (400, 2))
        a, b = r1(pts), field_of("aleatorio", {"tamanho": 0.1, "semente": 4})(pts)
        self.assertTrue(np.array_equal(a, r1(pts)) and not np.array_equal(a, b))
        self.assertTrue(0.35 < a.mean() < 0.65 and a.min() >= 0 and a.max() <= 1)
        self.assertEqual(r1(np.array([(0.11, 0.1)]))[0], r1(np.array([(0.14, 0.13)]))[0])     # (the same cell)

    def test_mix_and_remap(self):
        g = Graph()
        a = g.add_node("gradiente", {"angulo": 0.0})
        g.connect(surface(g), "painel", a, "painel")
        z = g.add_node("mascara", {"x": 3.0, "y": 1.35, "largura": 2.0, "altura": 2.7})
        m = g.add_node("misturar", {"modo": "multiplicar"})
        g.connect(a, "campo", m, "a")
        g.connect(z, "campo", m, "b")
        rm = g.add_node("remapear", {"degraus": 3})
        g.connect(a, "campo", rm, "campo")
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        pts = np.array([(1.0, 1.0), (3.0, 1.0)])
        self.assertEqual(list(out[m]["campo"](pts)), [0.0, 0.75])
        g.set_param(m, "modo", "máximo")
        self.assertEqual(list(g.evaluate()[m]["campo"](pts)), [0.25, 1.0])
        g.set_param(m, "fator", 0.0)                         # (none of the second)
        self.assertEqual(list(g.evaluate()[m]["campo"](pts)), [0.25, 0.75])
        steps = out[rm]["campo"](np.column_stack((np.linspace(0, 4, 200), np.ones(200))))
        self.assertEqual(sorted(set(np.round(steps, 6))), [0.0, 0.5, 1.0])


class Points(unittest.TestCase):
    def _points(self, key, params=None):
        g = Graph()
        n = g.add_node(key, params or {})
        g.connect(surface(g), "painel", n, "painel")
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        return out[n]["pontos"]

    def test_rings_and_spiral(self):
        rings = self._points("radial", {"x": 0.7, "y": 1.35, "passo": 0.1})
        d = np.hypot(rings["xy"][:, 0] - 0.7, rings["xy"][:, 1] - 1.35)
        self.assertTrue(np.allclose(d / 0.1, np.round(d / 0.1), atol=1e-6))
        spiral = self._points("radial", {"x": 2.0, "y": 1.35, "passo": 0.1, "espiral": True})
        area = nodes_3d.example_face().buffer(-0.1).area
        self.assertTrue(0.7 < len(spiral["xy"]) * 0.01 / area < 1.3)        # (each with about passo² of room)

    def test_along_the_outline(self):
        frame = self._points("contorno_pontos", {"onde": "vãos", "distancia": 0.15, "passo": 0.05, "filas": 2})
        xy = frame["xy"]
        self.assertGreater(len(xy), 150)
        dx = np.maximum(np.abs(xy[:, 0] - 2.0) - 0.6, 0.0)
        dy = np.maximum(np.abs(xy[:, 1] - 1.5) - 0.6, 0.0)
        away = np.maximum(dx, dy)
        self.assertTrue(np.all((np.abs(away - 0.15) < 1e-4) | (np.abs(away - 0.20) < 1e-4)))

    def test_choose_misalign_join(self):
        g = Graph()
        s = surface(g)
        q = g.add_node("grelha", {"passo": 0.1})
        g.connect(s, "painel", q, "painel")
        v = g.add_node("distancia_vaos", {"alcance": 0.3})
        g.connect(s, "painel", v, "painel")
        e = g.add_node("escolher_pontos", {"limiar": 0.01, "inverter": True})
        g.connect(q, "pontos", e, "pontos")
        g.connect(v, "campo", e, "campo")
        j = g.add_node("desalinhar", {"quanto": 0.5})
        g.connect(e, "pontos", j, "pontos")
        c = g.add_node("contorno_pontos", {"distancia": 0.1, "passo": 0.1})
        g.connect(s, "painel", c, "painel")
        u = g.add_node("juntar_pontos")
        g.connect(e, "pontos", u, "a")
        g.connect(c, "pontos", u, "b")
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        all_, kept = out[q]["pontos"]["xy"], out[e]["pontos"]["xy"]
        self.assertLess(len(kept), len(all_))
        gaps = nodes_logic.openings(out[s]["painel"])
        import shapely
        self.assertGreaterEqual(shapely.distance(gaps, shapely.points(kept)).min(), 0.29)
        moved = out[j]["pontos"]["xy"]
        self.assertEqual(len(moved), len(kept))
        shift = np.hypot(*(moved - kept).T)
        self.assertTrue(0 < shift.max() <= 0.05 + 1e-9)
        self.assertEqual(len(out[u]["pontos"]["xy"]), len(kept) + len(out[c]["pontos"]["xy"]))


class Holes(unittest.TestCase):
    def _graph(self, d_max=0.09):
        g = Graph()
        s = surface(g)
        q = g.add_node("grelha", {"passo": 0.1})
        g.connect(s, "painel", q, "painel")
        f = g.add_node("perfurar", {"d_max": d_max})
        g.connect(q, "pontos", f, "pontos")
        return g, s, f

    def test_scale_join_open_area(self):
        g, s, f = self._graph(0.04)
        k = g.add_node("escalar_furos", {"fator": 0.5})
        g.connect(f, "furos", k, "furos")
        o = g.add_node("area_aberta", {"alvo": 30.0})
        g.connect(f, "furos", o, "furos")
        capped = g.add_node("area_aberta", {"alvo": 60.0, "d_max": 0.05})
        g.connect(f, "furos", capped, "furos")
        both = g.add_node("juntar_furos")
        g.connect(f, "furos", both, "a")
        g.connect(k, "furos", both, "b")
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        self.assertTrue(np.allclose(out[k]["furos"]["d"], 0.02))
        self.assertAlmostEqual(nodes_logic.open_area(out[o]["furos"]), 0.30, places=3)
        self.assertAlmostEqual(out[capped]["furos"]["d"].max(), 0.05)        # (no further than the largest)
        self.assertEqual(len(out[both]["furos"]["xy"]), 2 * len(out[f]["furos"]["xy"]))

    def test_correct_for_fabrication(self):
        g, s, f = self._graph(0.099)                         # (bridges of 1 mm: refused)
        check = g.add_node("verificar_fabrico", {"ponte_min": 0.01})
        g.connect(f, "furos", check, "furos")
        fix = g.add_node("corrigir_fabrico", {"ponte_min": 0.01})
        g.connect(f, "furos", fix, "furos")
        after = g.add_node("verificar_fabrico", {"ponte_min": 0.01})
        g.connect(fix, "furos", after, "furos")
        out = g.evaluate()
        self.assertEqual(g.errors, {})
        self.assertFalse(out[check]["relatorio"]["ok"])
        rep = out[after]["relatorio"]
        self.assertTrue(rep["ok"], rep["problems"])
        self.assertGreaterEqual(rep["min_bridge"], 0.01 - 1e-6)
        self.assertGreater(out[fix]["furos"]["d"].min(), 0.08)       # (shrunk no more than needed)


class Ready(unittest.TestCase):
    def test_new_templates_are_fabricable(self):
        for key in ("vaos_emoldurados", "ondas_degraus", "aneis_ventilacao"):
            g = templates.make(key)
            nodes_3d.MODEL["doc"] = None
            out = g.evaluate()
            self.assertEqual(g.errors, {}, key)
            rep = next(v["relatorio"] for v in out.values() if "relatorio" in v)
            self.assertTrue(rep["ok"], "{}: {}".format(key, rep["problems"]))
            self.assertGreater(rep["holes"], 300, key)
        g = templates.make("aneis_ventilacao")
        out = g.evaluate()
        area = next(v["furos"] for n, v in out.items() if g.nodes[n]["type"] == "area_aberta")
        self.assertAlmostEqual(nodes_logic.open_area(area), 0.25, places=2)

    def test_library_takes_the_new_ones_once(self):
        names = [op["name"] for op in operators.listing()]
        self.assertIn("Janelas emolduradas", names)
        slug = next(op["slug"] for op in operators.listing() if op["name"] == "Janelas emolduradas")
        operators.delete(slug)
        self.assertNotIn("Janelas emolduradas", [op["name"] for op in operators.listing()])    # (not put back)
        with open(os.path.join(operators.folder(), operators.SEEDED), "w", encoding="utf-8") as f:
            f.write("ArqSynth\n")                             # (a library seeded by 0.541: only the new ones added)
        names = [op["name"] for op in operators.listing()]
        self.assertEqual(names.count("Atrator em favo"), 1)
        self.assertIn("Janelas emolduradas", names)


if __name__ == "__main__":
    unittest.main()
