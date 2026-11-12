"""0.563 — Gerador de revestimentos, step 2: the Revestimento element in IFC (ifc/tiled_coverings.py)."""

import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["ARQSYNTH_HOME"] = tempfile.mkdtemp(prefix="arqsynth_tiled_")

import ifcopenshell.util.element  # noqa: E402

from arqbim.core.mesh import TriMesh  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import Document  # noqa: E402

WALL = [(0, 0, 0), (4, 0, 0), (4, 0, 2.7), (0, 0, 2.7)]       # an upright face, facing −y
DOOR = [(1, 0, 0), (1.9, 0, 0), (1.9, 0, 2.1), (1, 0, 2.1)]
FLOOR = [(0, 0, 0), (5, 0, 0), (5, 3.2, 0), (0, 3.2, 0)]


def mesh(doc, g):
    v, f = doc.ifc.triangulate([g])[g]
    return np.asarray(v), np.asarray(f).reshape(-1, 3)


class Element(unittest.TestCase):
    def setUp(self):
        self.doc = Document()

    def test_on_a_wall(self):
        g = bim.add_covering(self.doc, WALL, "azulejo_30x60", holes=[DOOR])
        e = self.doc.ifc.by_guid(g)
        self.assertTrue(e.is_a("IfcCovering"))
        self.assertEqual(ifcopenshell.util.element.get_predefined_type(e), "CLADDING")
        ctype = ifcopenshell.util.element.get_type(e)
        self.assertEqual(ctype.Name, "Azulejo 30 × 60")
        mat = ifcopenshell.util.element.get_material(e, should_skip_usage=True)
        self.assertTrue(mat.is_a("IfcMaterialLayerSet"))
        self.assertEqual(len(mat.MaterialLayers), 2)
        info = self.doc.ifc.element_info(g)["params"] if hasattr(self.doc.ifc, "element_info") else None
        pg = ifcopenshell.util.element.get_psets(e)["ArqSynth_Paginacao"]
        self.assertGreater(pg["Pecas"], 40)
        self.assertEqual(pg["CortesEstreitos"], 0)              # (automatic start: no strip under 5 cm)
        q = ifcopenshell.util.element.get_psets(e)["Qto_CoveringBaseQuantities"]
        self.assertAlmostEqual(q["GrossArea"], 4 * 2.7 - 0.9 * 2.1, places=2)
        self.assertLess(q["NetArea"], q["GrossArea"])
        v, f = mesh(self.doc, g)
        self.assertTrue((v[:, 1] <= 1e-6).all(), "laid out of the wall, on its −y side")
        self.assertAlmostEqual(v[:, 1].min(), -0.014, places=4)  # (5 mm bed + 9 mm tile)
        door_mid = (v[:, 0] > 1.05) & (v[:, 0] < 1.85) & (v[:, 2] > 0.1) & (v[:, 2] < 2.0)
        self.assertFalse(door_mid.any(), "nothing over the door")
        rows = sorted({round(z, 4) for z in v[:, 2]})
        self.assertIn(0.0, rows)                                 # (from the wall's foot)
        info = info

    def test_floor_and_ceiling(self):
        g = bim.add_covering(self.doc, FLOOR, "soalho_carvalho")
        e = self.doc.ifc.by_guid(g)
        self.assertEqual(ifcopenshell.util.element.get_predefined_type(e), "FLOORING")
        v, _f = mesh(self.doc, g)
        self.assertAlmostEqual(v[:, 2].max(), 0.015, places=4)
        ceiling = list(reversed(FLOOR))
        g2 = bim.add_covering(self.doc, [(x, y, 2.6) for x, y, _z in ceiling], "porcelanico_60x60")
        self.assertEqual(ifcopenshell.util.element.get_predefined_type(self.doc.ifc.by_guid(g2)), "CEILING")
        v, _f = mesh(self.doc, g2)
        self.assertLess(v[:, 2].min(), 2.6)

    def test_closed_pieces(self):
        g = bim.add_covering(self.doc, FLOOR, "hexagono_20")
        v, f = mesh(self.doc, g)
        self.assertTrue(TriMesh(v, f).is_closed())

    def test_changes_and_undo(self):
        g = bim.add_covering(self.doc, WALL, "metro_10x20")
        e = self.doc.ifc.by_guid(g)
        n0 = ifcopenshell.util.element.get_psets(e)["ArqSynth_Paginacao"]["Pecas"]
        bim.set_covering(self.doc, g, layout={"pattern": "espinha_reta", "angle": 0.0})
        e = self.doc.ifc.by_guid(g)
        self.assertEqual(ifcopenshell.util.element.get_psets(e)["ArqSynth_Paginacao"]["Aparelho"], "espinha_reta")
        bim.set_covering(self.doc, g, finish="pedra_60x40")
        p = self.doc.ifc.tiled_params(g)
        self.assertEqual(p["material"], "pedra")
        self.assertEqual(p["layout"]["pattern"], "desencontrado")
        self.assertEqual(ifcopenshell.util.element.get_type(self.doc.ifc.by_guid(g)).Name,
                         "Pedra 60 × 40 (desencontrada)")
        self.doc.undo()
        self.doc.undo()
        e = self.doc.ifc.by_guid(g)
        self.assertEqual(ifcopenshell.util.element.get_psets(e)["ArqSynth_Paginacao"]["Pecas"], n0)

    def test_refused(self):
        with self.assertRaises(Exception):
            bim.add_covering(self.doc, WALL, "nada")
        g = bim.add_covering(self.doc, WALL, "azulejo_20x20")
        with self.assertRaises(Exception):
            bim.set_covering(self.doc, g, layout={"w": 0.0})
        with self.assertRaises(Exception):
            bim.set_covering(self.doc, g, material="kryptonite")

    def test_saved_and_read_again(self):
        g = bim.add_covering(self.doc, WALL, "tijolo_flamengo")
        path = os.path.join(tempfile.mkdtemp(), "r.ifc")
        self.doc.ifc.file.write(path)
        import ifcopenshell
        f = ifcopenshell.open(path)
        e = f.by_guid(g)
        self.assertTrue(e.is_a("IfcCovering"))
        self.assertEqual(len(e.Representation.Representations[0].Items), 3)   # (bricks, bed, mortar)


if __name__ == "__main__":
    unittest.main()
