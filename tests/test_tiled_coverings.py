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
from shapely.geometry import Polygon  # noqa: E402

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


class OnTheModel(unittest.TestCase):
    """(0.564) Laid on a clicked face of an element (it follows it), and on drawings chosen."""

    def test_wall_face_follows(self):
        from arqbim.ifc import catalog
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        v, _f = mesh(doc, wall)
        front = float(v[:, 1].min())
        g = bim.cover_face(doc, wall, (2.5, front, 1.0), (0.0, -1.0, 0.0), "azulejo_20x20")
        self.assertIsNotNone(g)
        e = doc.ifc.by_guid(g)
        self.assertEqual(e.CoversElements[0].RelatingBuildingElement.GlobalId, wall)
        a0 = ifcopenshell.util.element.get_psets(e)["Qto_CoveringBaseQuantities"]["GrossArea"]
        self.assertAlmostEqual(a0, 5.0 * bim.WALL_HEIGHT, delta=0.3)
        frame = bim.wall_frame(doc, wall)                 # (a door put in: the finish cut round it, by itself)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, frame.x0 + 2.0, 1)
        e = doc.ifc.by_guid(g)
        a1 = ifcopenshell.util.element.get_psets(e)["Qto_CoveringBaseQuantities"]["GrossArea"]
        self.assertLess(a1, a0 - 1.0)
        self.assertGreater(a1, a0 - 3.0)
        doc.execute_remove = None
        from arqbim.model.document import IfcCommand
        doc.execute(IfcCommand("x", lambda ifc: ifc.remove([wall])))    # (the wall gone: its finish with it)
        self.assertIsNone(doc.ifc.by_guid(g))

    def test_drawing_chosen(self):
        from arqbim.core.mesh import PolyMesh
        from arqbim.model.document import AddObject, SketchObject
        doc = Document()
        pts = [(0, 0, 0), (3, 0, 0), (3, 2, 0), (0, 2, 0)]
        sk = SketchObject("Polígono", np.eye(4), PolyMesh([np.array(p, float) for p in pts], [[0, 1, 2, 3]]))
        doc.execute(AddObject(sk))
        made = bim.cover_drawings(doc, [sk.id], "porcelanico_60x60")
        self.assertEqual(len(made), 1)
        e = doc.ifc.by_guid(made[0])
        self.assertEqual(ifcopenshell.util.element.get_predefined_type(e), "FLOORING")
        v, _f = mesh(doc, made[0])
        self.assertGreater(v[:, 2].max(), 0.01)


class PieceByPiece(unittest.TestCase):
    """(0.566) Bands, a border, a mix of materials, pieces picked one by one."""

    def test_band_border_mix_picks(self):
        from arqbim.core import tiling as tl
        doc = Document()
        g = bim.add_covering(doc, WALL, "azulejo_20x20")
        bim.set_covering_extras(doc, g, zones=[{"kind": "faixa", "y0": 1.2, "y1": 1.25, "material": "marmore",
                                                "w": 0.25, "h": 0.05},
                                               {"kind": "cercadura", "width": 0.1, "material": "granito",
                                                "w": 0.3, "h": 0.1}])
        result, mats = doc.ifc.tiled_pieces(g)
        self.assertIn("marmore", mats)
        self.assertIn("granito", mats)
        band = [p for p, m in zip(result.pieces, mats) if m == "marmore"]
        ys = [q[1] for p in band for q in p.points]
        self.assertGreaterEqual(min(ys), 1.2 - 1e-6)
        self.assertLessEqual(max(ys), 1.25 + 1e-6)
        e = doc.ifc.by_guid(g)
        self.assertGreaterEqual(len(e.Representation.Representations[0].Items), 4)   # (tile, marble, granite, …)
        bim.set_covering_extras(doc, g, zones=[], mix={"materials": ["azulejo", "tinta_azul"], "seed": 3})
        _r, mats = doc.ifc.tiled_pieces(g)
        self.assertEqual(set(mats), {"azulejo", "tinta_azul"})
        main = next(p for p in _r.pieces if p.whole)
        c = Polygon(main.points).centroid
        bim.set_covering_extras(doc, g, mix={}, picks=[(c.x, c.y, "tinta_vermelha")])
        _r, mats = doc.ifc.tiled_pieces(g)
        self.assertEqual(mats.count("tinta_vermelha"), 1)
        self.assertEqual(mats.count(None), len(mats) - 1)
        with self.assertRaises(Exception):
            bim.set_covering_extras(doc, g, zones=[{"kind": "faixa", "y0": 1.0, "y1": 1.0}])
        doc.undo()
        doc.undo()
        _r, mats = doc.ifc.tiled_pieces(g)
        self.assertIn("marmore", mats)
        self.assertTrue(tl)
