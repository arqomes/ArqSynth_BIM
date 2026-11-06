"""0.440 — Loose furniture of the program's own (the owner: «Sim, peças próprias»)."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

import ifcopenshell.util.element as ue  # noqa: E402

from arqbim.core import loose_furniture as lf  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import Document  # noqa: E402


class Pieces(unittest.TestCase):
    """Every piece of the catalogue: its parts inside its box (w × d × h, from the floor), of the catalogue's materials;
    a bigger sofa, more cushions; a double bed two pillows, a single one one; sizes out of range refused."""

    def test_parts(self):
        from arqbim.ifc import catalog
        for key, (_g, _t, _n, (w, d, h)) in lf.PIECES.items():
            parts = lf.parts(key)
            self.assertTrue(parts, key)
            for p in parts:
                x0, y0, z0, x1, y1, z1 = p.box
                self.assertTrue(x0 >= -w / 2 - 0.011 and x1 <= w / 2 + 0.011, key)
                self.assertTrue(y0 >= -d / 2 - 0.011 and y1 <= d / 2 + 0.011, key)
                self.assertTrue(z0 >= -1e-9 and z1 <= h + 1e-9, key)
                self.assertIn(p.material, catalog.MATERIALS, key)
        pillows = lambda key: sum(1 for p in lf.parts(key) if p.material == "tecido_claro") - 1     # noqa: E731
        self.assertEqual((pillows("cama_casal"), pillows("cama_solteiro")), (2, 1))
        cushions = lambda key: sum(1 for p in lf.parts(key) if abs(p.box[5] - 0.54) < 1e-9)  # noqa
        self.assertEqual((cushions("sofa_2"), cushions("sofa_3")), (2, 3))
        self.assertIsNone(lf.check("sofa_3", 2.2, 0.9, 0.85))
        self.assertEqual(lf.check("sofa_3", 0.05, 0.9, 0.85), "loose_size")
        self.assertEqual(lf.check("nada", 1, 1, 1), "loose_bad")


class LooseIfc(unittest.TestCase):
    """Every piece put in the model: an IfcFurniture of its kind (BED, SOFA, CHAIR, TABLE, DESK, SHELF, USERDEFINED
    with its ObjectType), as big as its sizes, coloured by its parts, its nominal sizes, not built in; a sofa turned 90°;
    made wider (its middle stays); another piece (its sizes); the double bed a double bed for the Checker; valid IFC."""

    def test_pieces(self):
        doc = Document()
        made = {}
        for k, key in enumerate(lf.PIECES):
            made[key] = bim.add_loose(doc, key, np.array((k * 3.0, 0.0, 0.0)))
        ifc = doc.ifc
        for key, guid in made.items():
            e = ifc.by_guid(guid)
            self.assertEqual(e.PredefinedType, lf.PIECES[key][1])
            if e.PredefinedType == "USERDEFINED":
                self.assertEqual(e.ObjectType, lf.PIECES[key][2][0])
            v = doc.get(guid).mesh.verts
            size = v.max(axis=0) - v.min(axis=0)
            w, d, h = lf.defaults(key)
            self.assertAlmostEqual(size[2], h, places=3, msg=key)
            self.assertLess(abs(size[0] - w), 0.03, key)
            q = ue.get_psets(e)["Pset_FurnitureTypeCommon"]
            self.assertIs(q["IsBuiltIn"], False)
        self.assertEqual(doc.ifc.validate(), [])
        sofa = bim.add_loose(doc, "sofa_3", np.array((0.0, 10.0, 0.0)), 90.0)
        v = doc.get(sofa).mesh.verts
        size = v.max(axis=0) - v.min(axis=0)
        self.assertAlmostEqual(size[1], 2.20, places=3)                    # (turned: its width along y)
        centre = (v.max(axis=0) + v.min(axis=0)) / 2
        bim.set_loose(doc, sofa, width=2.60)
        v = doc.get(sofa).mesh.verts
        self.assertAlmostEqual((v.max(axis=0) - v.min(axis=0))[1], 2.60, places=3)
        self.assertTrue(np.allclose(((v.max(axis=0) + v.min(axis=0)) / 2)[:2], centre[:2], atol=1e-6))
        bim.set_loose(doc, sofa, piece="poltrona")
        p = ifc.loose_params(sofa)
        self.assertEqual((p["piece"], p["width"]), ("poltrona", 0.85))
        self.assertEqual(ifc.by_guid(sofa).PredefinedType, "CHAIR")
        with self.assertRaises(ValueError):
            bim.set_loose(doc, sofa, height=9.0)
        from arqbim.verify import reader
        obj = doc.get(made["cama_casal"])
        self.assertEqual(reader._kind_of(ifc, obj), "double_bed")
        self.assertEqual(reader._kind_of(ifc, doc.get(made["cama_solteiro"])), "bed")
        self.assertEqual(reader._kind_of(ifc, doc.get(made["sofa_2"])), "sofa")
        doc.undo()
        self.assertEqual(ifc.loose_params(sofa)["piece"], "sofa_3")


if __name__ == "__main__":
    unittest.main()
