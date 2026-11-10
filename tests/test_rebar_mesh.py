"""0.522 — Welded meshes drawn by hand (core/rebar_mesh.py, ifc/rebar.py): generic by Ø and spacing, cut by the slab's
outline less the cover, its sheets and weight, its checks, in the IFC as IfcReinforcingMesh and following the slab."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arqbim.core import rebar_mesh as rm  # noqa: E402

SQUARE = [(0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0)]


class MeshCoreTest(unittest.TestCase):
    def test_name_area_mass(self):
        m = rm.Mesh(6, 0.15)
        self.assertEqual(m.name(), "Ø6 // 0,15")
        self.assertAlmostEqual(m.area_per_m(), 0.2827 / 0.15, places=2)     # 1,88 cm²/m
        self.assertAlmostEqual(m.mass_per_m2(), 2 * 0.222 / 0.15, places=2)  # 2,96 kg/m²

    def test_wires_cut_by_cover(self):
        m = rm.Mesh(8, 0.20, "bottom", 0.025)
        laid = rm.wires(m, SQUARE, 3.0, 0.20)
        along, across = laid["bottom"]
        self.assertEqual(len(along), 20)                 # (4 − 0,05) / 0,20 → 20 wires along X
        self.assertEqual(len(across), 30)
        xs = [p[0] for b in along for p in b]
        self.assertAlmostEqual(min(xs), 0.025)
        self.assertAlmostEqual(max(xs), 5.975)
        self.assertAlmostEqual(along[0][0][2], 3.0 - 0.20 + 0.025 + 0.004)
        self.assertAlmostEqual(across[0][0][2], along[0][0][2] + 0.008)   # (the other way over it)

    def test_both_faces_and_angle(self):
        laid = rm.wires(rm.Mesh(6, 0.15, "both", 0.03, 90.0), SQUARE, 3.0, 0.20)
        self.assertEqual(set(laid), {"bottom", "top"})
        top_z = laid["top"][1][0][0][2]
        self.assertAlmostEqual(top_z, 3.0 - 0.03 - 0.003)
        b = laid["bottom"][0][0]                          # (at 90°: the first wires run along Y)
        self.assertAlmostEqual(b[0][0], b[1][0])

    def test_sheets_weight_checks(self):
        m = rm.Mesh(6, 0.15)
        self.assertEqual(rm.sheets(m, SQUARE), 2)        # 5,95 × 3,95 = 23,5 m² over 5,70 × 2,10 = 11,97
        self.assertAlmostEqual(rm.weight(m, SQUARE), 2 * 6.0 * 2.4 * m.mass_per_m2())
        ok = {k: good for k, good, _v in rm.checks(m, 0.20)}
        self.assertEqual(ok, {"cover": True, "spacing": True, "minimum": False, "fits": True})
        ok = {k: good for k, good, _v in rm.checks(rm.Mesh(8, 0.15), 0.20)}
        self.assertTrue(ok["minimum"])                   # 3,35 cm²/m ≥ 2,1
        ok = {k: good for k, good, _v in rm.checks(rm.Mesh(6, 0.30, cover=0.01), 0.12)}
        self.assertFalse(ok["cover"])
        self.assertFalse(ok["spacing"])


class MeshIfcTest(unittest.TestCase):
    def test_in_the_model(self):
        os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        slab = bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 6.0, 4.0, catalog.BY_KEY["laje_15"])
        made = bim.put_mesh(doc, [slab], rm.Mesh(8, 0.20, "both"))
        self.assertEqual(len(made), 2)
        e = doc.ifc.by_guid(made[0])
        self.assertTrue(e.is_a("IfcReinforcingMesh"))
        self.assertAlmostEqual(float(e.LongitudinalBarSpacing) * doc.ifc.unit_scale, 0.20)
        rows = doc.ifc.mesh_rows()
        self.assertEqual({r["face"] for r in rows}, {"bottom", "top"})
        self.assertEqual({(r["diameter"], round(r["spacing"], 2)) for r in rows}, {(8, 0.2)})
        self.assertGreater(rows[0]["sheets"], 0)
        self.assertEqual(doc.ifc.mesh_of(slab).diameter, 8)
        rows, totals = bim.rebar_schedule(doc)                          # (0.523) in the bar schedule
        self.assertEqual([(r["mark"], r["shape"]) for r in rows], [("M1", "Ø8//0,20")] * 2)
        self.assertAlmostEqual(totals[8][1], sum(r["weight"] for r in rows))
        q = next(r for r in bim.structure_quantities(doc) if r.guid == slab)
        self.assertAlmostEqual(q.steel, sum(r["weight"] for r in rows))
        again = bim.put_mesh(doc, [slab], rm.Mesh(6, 0.15))             # (replaced, not added)
        self.assertEqual(len(again), 1)
        self.assertEqual(len(doc.ifc.file.by_type("IfcReinforcingMesh")), 1)
        doc.undo()
        self.assertEqual(len(doc.ifc.file.by_type("IfcReinforcingMesh")), 2)
        self.assertTrue(bim.remove_meshes(doc, [slab]))
        self.assertEqual(len(doc.ifc.file.by_type("IfcReinforcingMesh")), 0)
        self.assertFalse(bim.remove_meshes(doc, [slab]))


if __name__ == "__main__":
    unittest.main()
