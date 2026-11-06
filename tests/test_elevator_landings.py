"""0.438 — The elevator's landing doors, and the slabs it goes through opened round its shaft."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import Document  # noqa: E402


class ElevatorLandings(unittest.TestCase):
    """Two storeys (0 and 3 m), a floor slab of the upper one over 8 × 6 m: an elevator at (2, 2) — two landings, each
    its front wall and its door (its two leaves 2,10 m high, closed); the upper slab opened round the shaft (its area
    less the shaft's outer 1,90 × 2,05 m), the ground one not; valid IFC; undone: the slab whole again."""

    def test_landings(self):
        doc = Document()
        bim.add_storey(doc, "Piso 1", 3.0)
        storeys = sorted(doc.ifc.storeys(), key=lambda s: s[2])
        ground, upper = storeys[0][0], storeys[1][0]
        slab = bim.add_slab_outline(doc, [(0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)], 3.0,
                                    catalog.BY_KEY["laje_15"], storey=upper)
        floor = bim.add_slab_outline(doc, [(0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)], 0.0,
                                     catalog.BY_KEY["laje_15"], storey=ground)
        area = doc.ifc.slab_outline(slab)["area"]
        lift = bim.add_elevator(doc, (2.0, 2.0), storey=ground)
        p = doc.ifc._params(doc.ifc.by_guid(lift))
        self.assertEqual(int(p["Patamares"]), 2)
        self.assertAlmostEqual(float(p["PortaLargura"]), 0.90)
        self.assertEqual(len(doc.ifc.by_guid(slab).HasOpenings), 1)
        self.assertEqual(len(doc.ifc.by_guid(floor).HasOpenings or ()), 0)
        v = doc.get(slab).mesh.verts
        tris = doc.get(slab).mesh.tris
        top = v[:, 2].max()
        a, b, c = v[tris[:, 0]], v[tris[:, 1]], v[tris[:, 2]]
        n = np.cross(b - a, c - a)
        up = (n[:, 2] > 0) & (np.abs(a[:, 2] - top) < 1e-6)
        top_area = float(np.linalg.norm(n[up], axis=1).sum() / 2)
        self.assertAlmostEqual(top_area, area - (1.60 + 0.30) * (1.75 + 0.30), places=3)
        lv = doc.get(lift).mesh.verts
        self.assertLess(lv[:, 1].min(), 2.0 - 0.10)                            # (its front walls, before the shaft)
        self.assertEqual(doc.ifc.validate(), [])
        doc.undo()
        self.assertEqual(len(doc.ifc.by_guid(slab).HasOpenings or ()), 0)


if __name__ == "__main__":
    unittest.main()
