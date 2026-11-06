"""0.433 — Slabs with a height of their own at each corner (the addon's «piso com declive por vértice»)."""

import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

import ifcopenshell.util.element as ue  # noqa: E402

from arqbim.core import sloped_slab  # noqa: E402
from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import Document  # noqa: E402


def _volume(verts, tris):
    a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def _closed(tris):
    edges = {}
    for a, b, c in tris:
        for p, q in ((a, b), (b, c), (c, a)):
            edges[(p, q)] = edges.get((p, q), 0) + 1
    return all(edges.get((q, p), 0) == n for (p, q), n in edges.items())


def _bounds(doc, guid):
    v = doc.get(guid).mesh.verts
    return v.min(axis=0), v.max(axis=0)


class SlopedBody(unittest.TestCase):
    """The body: closed, its volume the plan's area times its thickness (upright), its holes' corners on its top."""

    def test_body(self):
        out = [(0.0, 0.0), (4.0, 0.0), (4.0, 2.0), (0.0, 2.0)]
        verts, tris = sloped_slab.body(out, [], [0.0, 0.0, 0.1, 0.1], 0.12)
        self.assertTrue(_closed(tris))
        self.assertAlmostEqual(_volume(verts, tris), 8 * 0.12, places=6)
        self.assertEqual(sorted({round(z, 3) for z in verts[:4, 2]}), [0.12, 0.22])
        hole = [(1.0, 0.5), (1.0, 1.5), (2.0, 1.5), (2.0, 0.5)]
        verts, tris = sloped_slab.body(list(reversed(out)), [hole], [0.1, 0.1, 0.0, 0.0], 0.12)
        self.assertTrue(_closed(tris))
        self.assertAlmostEqual(_volume(verts, tris), 7 * 0.12, places=6)
        self.assertAlmostEqual(sloped_slab.surface(out, [0, 0, 0.1, 0.1])(2.0, 1.0), 0.05)
        self.assertTrue(sloped_slab.is_flat([0.0, 1e-9, 0.0]))
        self.assertFalse(sloped_slab.is_flat([0.0, 0.01, 0.0]))


class SlopedSlabs(unittest.TestCase):
    """A slab's corners at their own heights: its body tessellated, its outline and thickness still read (its plan
    kept beside it); a corner moved keeps its height; one added takes its top's; its type changed keeps the slope;
    falling 2 % from a side; flat again: its extrusion; mirrored, its heights follow its corners; saved and opened
    again; the IFC valid; undo."""

    def test_sloped_slab(self):
        doc = Document()
        spec = catalog.BY_KEY["laje_12"]
        out = [(0.0, 0.0), (4.0, 0.0), (4.0, 2.0), (0.0, 2.0)]
        slab = bim.add_slab_outline(doc, out, 0.0, spec)
        info = doc.ifc.slab_outline(slab)
        self.assertIsNone(info["heights"])
        bim.set_slab_heights(doc, slab, [0.0, 0.0, 0.1, 0.1])
        e = doc.ifc.by_guid(slab)
        self.assertIsNone(doc.ifc._slab_solid(e))
        self.assertEqual(e.Representation.Representations[0].RepresentationType, "Tessellation")
        info = doc.ifc.slab_outline(slab)
        self.assertEqual([round(z, 3) for z in info["heights"]], [0.0, 0.0, 0.1, 0.1])
        self.assertAlmostEqual(info["thickness"], 0.12)
        self.assertAlmostEqual(info["area"], 8.0)
        self.assertEqual([tuple(np.round(p, 6)) for p in info["outline"]], out)
        lo, hi = _bounds(doc, slab)
        self.assertTrue(np.allclose(lo, (0.0, 0.0, -0.12), atol=1e-6) and np.allclose(hi, (4.0, 2.0, 0.1), atol=1e-6))
        q = ue.get_psets(e)["Qto_SlabBaseQuantities"]
        self.assertAlmostEqual(q["GrossVolume"], 8 * 0.12)
        params = doc.ifc.describe(slab)["params"]
        self.assertEqual((params["corners"], round(params["thickness"], 3)), (4, 0.12))
        # undo: flat again
        doc.undo()
        self.assertIsNone(doc.ifc.slab_outline(slab)["heights"])
        self.assertIsNotNone(doc.ifc._slab_solid(doc.ifc.by_guid(slab)))
        doc.redo()
        self.assertIsNotNone(doc.ifc.slab_outline(slab)["heights"])
        # one corner by itself
        bim.set_slab_corner_height(doc, slab, 1, -0.05)
        self.assertEqual([round(z, 3) for z in doc.ifc.slab_outline(slab)["heights"]], [0.0, -0.05, 0.1, 0.1])
        # a corner moved: the same corners, the same heights
        bim.set_slab_outline(doc, slab, [(0.0, 0.0), (5.0, 0.0), (4.0, 2.0), (0.0, 2.0)])
        info = doc.ifc.slab_outline(slab)
        self.assertEqual([round(z, 3) for z in info["heights"]], [0.0, -0.05, 0.1, 0.1])
        self.assertAlmostEqual(info["area"], 9.0)
        # a corner added in the middle of the side y = 2: its height the top's there (0,1)
        bim.set_slab_outline(doc, slab, [(0.0, 0.0), (5.0, 0.0), (4.0, 2.0), (2.0, 2.0), (0.0, 2.0)])
        heights = doc.ifc.slab_outline(slab)["heights"]
        self.assertEqual(len(heights), 5)
        self.assertAlmostEqual(heights[3], 0.1, places=6)
        # its type changed: the slope stays, the thickness is the new type's
        bim.set_type(doc, slab, catalog.BY_KEY["laje_15"])
        info = doc.ifc.slab_outline(slab)
        self.assertAlmostEqual(info["thickness"], 0.15)
        self.assertEqual(len(info["heights"]), 5)
        # falling 2 % from its first side (y = 0): the far side (y = 2) 4 cm lower
        bim.set_slab_slope(doc, slab, 2.0, 0)
        heights = doc.ifc.slab_outline(slab)["heights"]
        self.assertEqual([round(z, 4) for z in heights], [0.0, 0.0, -0.04, -0.04, -0.04])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        # saved and opened again
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "declive.ifc")
            doc.save(path)
            doc2 = Document()
            doc2.open(path)
            info2 = doc2.ifc.slab_outline(slab)
            self.assertEqual([round(z, 4) for z in info2["heights"]], [0.0, 0.0, -0.04, -0.04, -0.04])
            self.assertAlmostEqual(info2["thickness"], 0.15)
            lo, hi = _bounds(doc2, slab)
            self.assertAlmostEqual(lo[2], -0.15 - 0.04, places=5)
        # mirrored about x = 10: its heights go with their corners
        mirrored = [(20.0 - x, y) for x, y in doc.ifc.slab_outline(slab)["outline"]]
        before = dict(zip(mirrored, doc.ifc.slab_outline(slab)["heights"]))
        bim.mirror_objects(doc, [slab], np.array((10.0, 0.0, 0.0)), np.array((10.0, 1.0, 0.0)))
        info = doc.ifc.slab_outline(slab)
        for p, z in zip(info["outline"], info["heights"]):
            key = min(before, key=lambda q: np.hypot(q[0] - p[0], q[1] - p[1]))
            self.assertAlmostEqual(before[key], z, places=6)
        # flat again: its extrusion, no plan kept
        bim.set_slab_heights(doc, slab, [0.0] * len(info["outline"]))
        e = doc.ifc.by_guid(slab)
        self.assertIsNotNone(doc.ifc._slab_solid(e))
        self.assertFalse(doc.ifc._params(e).get("Planta"))
        self.assertIsNone(doc.ifc.slab_outline(slab)["heights"])
        # a round slab has no corners; a rectangle becomes a polygon
        circle = bim.add_slab_circle(doc, (30.0, 0.0), 1.0, 0.0, spec)
        with self.assertRaises(ValueError):
            bim.set_slab_heights(doc, circle, [0.0, 0.1, 0.2])
        rect = bim.add_slab(doc, np.array((0.0, 10.0, 0.0)), 4.0, 3.0, spec)
        bim.set_slab_slope(doc, rect, 1.0, 0)
        self.assertEqual(doc.ifc.slab_shape(rect), "poligono")
        self.assertEqual(len(doc.ifc.slab_outline(rect)["heights"]), 4)
        with self.assertRaises(ValueError):
            bim.set_slab_heights(doc, rect, [0.0, 0.0, 30.0, 0.0])                # (20 m at most)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


if __name__ == "__main__":
    unittest.main()
