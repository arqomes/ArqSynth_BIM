"""0.540 — Gráfico Visual: a graph's holes as a wall's perforated finish (free holes, board by board)."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

from shapely.geometry import box  # noqa: E402

from arqbim.core import surfaces  # noqa: E402
from arqbim.core.graph import Graph  # noqa: E402
from arqbim.core.graph.nodes_panels import cladding_pattern  # noqa: E402
from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import Document  # noqa: E402


def _graph(shape="redondo", repeat=True):
    g = Graph()
    p = g.add_node("painel_plano", {"largura": 1.0, "altura": 1.2, "margem": 0.05, "espessura": 0.004})
    q = g.add_node("hexagono", {"passo": 0.1})
    f = g.add_node("perfurar", {"d_max": 0.05, "forma": shape})
    b = g.add_node("aplicar_parede", {"repetir": repeat})
    g.connect(p, "painel", q, "painel")
    g.connect(q, "pontos", f, "pontos")
    g.connect(f, "furos", b, "furos")
    out = g.evaluate()
    return out[b]["bim"], len(out[f]["furos"]["xy"])


class FreeHoles(unittest.TestCase):
    def test_text_round_trip(self):
        text = surfaces.free_text("hexagonal", [(0.1, 0.2, 0.03), (0.5, 0.6, 0.012)])
        shape, holes = surfaces.free_read(text)
        self.assertEqual(shape, "hexagonal")
        np.testing.assert_allclose(holes, [(0.1, 0.2, 0.03), (0.5, 0.6, 0.012)])
        self.assertIsNone(surfaces.free_read("estrela|1,2,3"))

    def test_boards_repeat_and_openings(self):
        face = box(0, 0, 3.0, 1.2).difference(box(1.2, 0.0, 1.8, 1.0))     # a door in the middle board
        holes = np.array([(0.5, 0.6, 0.05)])
        found = surfaces.free_perforation(face, "redondo", holes, 0.05, (1.0, 1.2), True)
        centres = np.concatenate([c for _q, c, _d in found])
        self.assertEqual(sorted(np.round(centres[:, 0], 6)), [0.5, 2.5])   # the middle one falls in the door
        once = surfaces.free_perforation(face, "redondo", holes, 0.05, (1.0, 1.2), False)
        self.assertEqual(sum(len(c) for _q, c, _d in once), 1)

    def test_mesh_closed(self):
        face = box(0, 0, 1.0, 1.0)
        found = surfaces.free_perforation(face, "hexagonal", np.array([(0.5, 0.5, 0.2)]), 0.05, (1.0, 1.0))
        v, t = surfaces.free_mesh(face, 0.01, found, "hexagonal")
        self.assertGreater(len(t), 0)
        top = v[t][:, :, 2].min(1) > 0.005                                  # the top's area: the face less the hole
        a = v[t[top]]
        e1, e2 = a[:, 1, :2] - a[:, 0, :2], a[:, 2, :2] - a[:, 0, :2]
        area = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]).sum()
        self.assertAlmostEqual(area, 1.0 - np.sqrt(3) / 2 * 0.2 ** 2, places=6)

    def test_on_a_wall(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((3.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        data, n = _graph()
        panel = bim.add_cladding(doc, wall, 1, "perfurado", 1.2, cladding_pattern(data))
        d = doc.ifc.pattern_params(panel)
        self.assertEqual(d["count"], 3 * n)                                # three boards of 1 m, each the same
        self.assertAlmostEqual(d["thickness"], 0.004)
        data, n = _graph("hexagonal", repeat=False)
        bim.set_cladding(doc, panel, **cladding_pattern(data))
        self.assertEqual(doc.ifc.pattern_params(panel)["count"], n)


if __name__ == "__main__":
    unittest.main()
