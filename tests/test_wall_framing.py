"""0.437 — A wall's light frame (the addon's «Steel Frame / Wood Frame»)."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

from arqbim.core import wall_framing as wf  # noqa: E402
from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import Document  # noqa: E402


class Layout(unittest.TestCase):
    """A 4,00 × 2,80 m wall, its core 10 cm: steel at 60 cm — two plates, 8 studs (an end one at each end, six at the
    spacing), one row of blocking (7 pieces); a door 1,00–1,90 m, 2,10 m high: the bottom plate cut at it, a jamb each
    side, a header over it, two cripples over the header where the studs were; a window: its sill and cripples under
    it; wood at 40 cm: more studs."""

    def test_plain(self):
        pieces = wf.layout(4.0, 2.8, -0.05, 0.05, (), "steel", 0.60, 1)
        s = wf.summary(pieces)
        self.assertEqual(s["plate"][0], 2)
        self.assertEqual(s["stud"][0], 8)
        self.assertEqual(s["blocking"][0], 7)
        self.assertAlmostEqual(s["stud"][1], 8 * (2.8 - 2 * 0.04), places=6)
        self.assertTrue(all(abs(p.lo[1] + 0.05) < 1e-9 and abs(p.hi[1] - 0.05) < 1e-9 for p in pieces))
        wood = wf.summary(wf.layout(4.0, 2.8, -0.05, 0.05, (), "wood", 0.40, 0))
        self.assertGreater(wood["stud"][0], 8)
        self.assertNotIn("blocking", wood)

    def test_door_and_window(self):
        pieces = wf.layout(4.0, 2.8, -0.05, 0.05, [(1.0, 1.9, 0.0, 2.1)], "steel", 0.60, 1)
        s = wf.summary(pieces)
        self.assertEqual(s["plate"][0], 3)                    # (the bottom one in two, the top one whole)
        self.assertEqual(s["jamb"][0], 2)
        self.assertEqual(s["header"][0], 1)
        self.assertEqual(s["cripple"][0], 2)
        self.assertNotIn("sill", s)
        studs = [p for p in pieces if p.role == "stud"]
        self.assertFalse(any(p.hi[0] > 0.96 and p.lo[0] < 1.94 for p in studs))    # (none through the door)
        header = next(p for p in pieces if p.role == "header")
        self.assertAlmostEqual(header.lo[2], 2.1)
        self.assertAlmostEqual(header.size[0], 0.9 + 2 * 0.04)
        blocking = [p for p in pieces if p.role == "blocking"]
        self.assertFalse(any(p.lo[0] < 1.94 and p.hi[0] > 0.96 for p in blocking))   # (not across the door)
        window = wf.summary(wf.layout(4.0, 2.8, -0.05, 0.05, [(1.0, 2.2, 0.9, 2.1)], "steel", 0.60, 0))
        self.assertEqual(window["sill"][0], 1)
        self.assertEqual(window["cripple"][0], 4)             # (two over, two under)
        self.assertEqual(window["plate"][0], 2)               # (the bottom plate whole under a window)


class WallFramingIfc(unittest.TestCase):
    """On a 4 m wall with a door: a steel frame — its assembly, its pieces (IfcMember: PLATE, STUD, Verga…) of steel,
    inside the wall; undo; the wall made 6 m long: its frame made again (more studs); its spacing changed; wood; a copy
    of the wall gets a frame of its own; the wall deleted: its frame with it; valid IFC."""

    def test_frame(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        frame = bim.wall_frame(doc, wall)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, 1.5, -1)
        bim.set_wall_framing(doc, wall, kind="steel")
        ifc = doc.ifc
        assembly = ifc.framing_of(wall)
        self.assertIsNotNone(assembly)
        parts = [p for rel in assembly.IsDecomposedBy for p in rel.RelatedObjects]
        self.assertTrue(all(p.is_a("IfcMember") for p in parts))
        kinds = {p.PredefinedType for p in parts}
        self.assertTrue({"PLATE", "STUD", "USERDEFINED"} <= kinds)
        s = ifc.framing_summary(wall)
        self.assertEqual((s["jamb"][0], s["header"][0]), (2, 1))
        self.assertEqual(ifc.framing_settings(wall), ("steel", 0.60, 1))
        lo, hi = None, None
        for p in parts:
            v = doc.get(p.GlobalId).mesh.verts
            lo = v.min(axis=0) if lo is None else np.minimum(lo, v.min(axis=0))
            hi = v.max(axis=0) if hi is None else np.maximum(hi, v.max(axis=0))
        self.assertTrue(lo[1] >= -0.1 - 1e-6 and hi[1] <= 0.1 + 1e-6)          # (inside the wall)
        self.assertAlmostEqual(lo[0], 0.0, places=5)
        self.assertAlmostEqual(hi[0], 4.0, places=5)
        material = parts[0].HasAssociations[0].RelatingMaterial.Name
        self.assertIn("Aço", material)
        studs = s["stud"][0]
        doc.undo()
        self.assertIsNone(ifc.framing_of(wall))
        doc.redo()
        self.assertIsNotNone(ifc.framing_of(wall))
        bim.resize_wall(doc, wall, at_end=2.0)                    # (6 m: its frame made again)
        self.assertGreater(ifc.framing_summary(wall)["stud"][0], studs)
        bim.set_wall_framing(doc, wall, spacing=0.40)
        self.assertEqual(ifc.framing_settings(wall)[1], 0.40)
        bim.set_wall_framing(doc, wall, kind="wood")
        self.assertEqual(ifc.framing_settings(wall)[0], "wood")
        self.assertIn("Madeira", [p for rel in ifc.framing_of(wall).IsDecomposedBy
                                  for p in rel.RelatedObjects][0].HasAssociations[0].RelatingMaterial.Name)
        shift = np.eye(4)
        shift[1, 3] = 5.0
        copies = bim.copy_objects(doc, [wall], [shift], "Copiar")
        copy = next(g for g in copies if doc.ifc.by_guid(g) is not None and doc.ifc.by_guid(g).is_a("IfcWall"))
        self.assertIsNotNone(ifc.framing_of(copy))
        self.assertNotEqual(ifc.framing_of(copy).GlobalId, ifc.framing_of(wall).GlobalId)
        self.assertIsNotNone(ifc.framing_of(wall))
        self.assertEqual(doc.ifc.validate(), [])
        before = len(doc.ifc.file.by_type("IfcMember"))
        bim.delete(doc, [copy])
        self.assertLess(len(doc.ifc.file.by_type("IfcMember")), before)
        self.assertIsNotNone(ifc.framing_of(wall))
        bim.set_wall_framing(doc, wall, kind="")
        self.assertIsNone(ifc.framing_of(wall))
        self.assertEqual(len(doc.ifc.file.by_type("IfcMember")), 0)


if __name__ == "__main__":
    unittest.main()
