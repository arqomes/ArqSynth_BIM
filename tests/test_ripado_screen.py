"""0.441 — A free-standing slatted screen (the addon's «Ripado» with no wall behind it)."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

from arqbim.model import bim  # noqa: E402
from arqbim.model.document import Document  # noqa: E402


class RipadoScreen(unittest.TestCase):
    """A 3 m screen, 2,40 m high, along y from (1, 1): 4 × 4 cm slats at 8 cm, a 5 cm frame, two battens on its back —
    its box (3 m along y, 2,40 high, 4 + 2 cm thick); made 4 m long (its start stays); moved: it stays as it is; level
    slats; the cut list has its slats, battens and frame; valid IFC; undo."""

    def test_screen(self):
        doc = Document()
        pattern = {"width": 0.04, "gap": 0.04, "thickness": 0.04, "frame": 0.05, "battens": 2}
        guid = bim.add_ripado_screen(doc, np.array((1.0, 1.0, 0.0)), np.array((1.0, 4.0, 0.0)), 2.40, pattern)
        ifc = doc.ifc
        e = ifc.by_guid(guid)
        self.assertEqual((e.is_a(), e.ObjectType, ifc.kind_of(guid)), ("IfcBuildingElementProxy", "Ripado",
                                                                       "ripado_screen"))
        v = doc.get(guid).mesh.verts
        lo, hi = v.min(axis=0), v.max(axis=0)
        self.assertAlmostEqual(hi[1] - lo[1], 3.0, places=4)
        self.assertAlmostEqual(hi[2] - lo[2], 2.40, places=4)
        self.assertAlmostEqual(hi[0] - lo[0], 0.06, places=4)                # (its slats and the battens behind)
        frames, battens, slats = ifc._screen_pieces(ifc.screen_params(guid))
        self.assertEqual((len(frames), len(battens)), (4, 2))
        self.assertEqual(len(slats), 1 + int((2.90 - 0.04) / 0.08 + 1e-9))
        self.assertEqual(ifc.validate(), [])
        bim.set_ripado_screen(doc, guid, length=4.0)
        v = doc.get(guid).mesh.verts
        self.assertAlmostEqual(v[:, 1].max() - v[:, 1].min(), 4.0, places=4)
        self.assertAlmostEqual(v[:, 1].min(), 1.0, places=4)
        m = np.eye(4)
        m[0, 3] = 2.0
        bim.transform_objects(doc, [guid], m, "Mover")
        bim.set_ripado_screen(doc, guid, direction="horizontal")
        v = doc.get(guid).mesh.verts
        self.assertAlmostEqual(v[:, 0].min(), 3.0 - 0.02 - 0.02, places=4)   # (moved: it stays there; battens behind)
        rows, _hw, _areas = bim.cut_list(doc)
        self.assertTrue({"slat", "batten", "ripado_frame"} <= {r[0] for r in rows})
        doc.undo()
        self.assertEqual(ifc.screen_params(guid)["direction"], "vertical")
        self.assertEqual(ifc.validate(), [])


if __name__ == "__main__":
    unittest.main()
