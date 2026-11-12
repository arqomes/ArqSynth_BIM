"""0.561 — Gerador de formas orgânicas, step 6: organic outlines (smoothing, differential growth)."""

import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arqbim.core import organic_lines as ol  # noqa: E402


def square(size=4.0, z=1.0):
    return np.array([(0, 0, z), (size, 0, z), (size, size, z), (0, size, z)], float)


def area(points):
    x, y = points[:, 0], points[:, 1]
    return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


class Smooth(unittest.TestCase):
    def test_rounded_same_area(self):
        out = ol.smooth(square())
        self.assertEqual(len(out), 4 * 2 ** 4)
        self.assertAlmostEqual(area(out), 16.0, places=6)
        self.assertTrue(np.allclose(out[:, 2], 1.0))
        seg = np.diff(np.vstack((out, out[:1])), axis=0)[:, :2]
        a, b = seg, np.roll(seg, -1, axis=0)
        cos = (a * b).sum(1) / np.linalg.norm(a, axis=1) / np.linalg.norm(b, axis=1)
        self.assertLess(np.degrees(np.arccos(np.clip(cos, -1, 1))).max(), 20.0)   # (no sharp corner left)
        line = ol.smooth(np.array([(0, 0, 0), (2, 0, 0), (2, 2, 0)], float), closed=False)
        self.assertTrue(np.allclose(line[0], (0, 0, 0)) and np.allclose(line[-1], (2, 2, 0)))


class Growth(unittest.TestCase):
    def test_grows_without_crossing(self):
        a = np.radians(np.arange(0, 360, 20))
        ring = np.column_stack((np.cos(a), np.sin(a), np.zeros(len(a))))
        out = ol.grow(ring, steps=150, spacing=0.1, seed=3)
        length = float(np.linalg.norm(np.diff(np.vstack((out, out[:1])), axis=0), axis=1).sum())
        self.assertGreater(length, 2 * math.pi * 1.5)                              # (it grew)
        self.assertFalse(ol.crosses_itself(out))                                  # (never across itself)
        self.assertTrue(np.allclose(out[:, 2], 0.0))
        again = ol.grow(ring, steps=150, spacing=0.1, seed=3)
        self.assertTrue(np.allclose(out, again))                                  # (the same seed: the same line)

    def test_inside_a_bound(self):
        a = np.radians(np.arange(0, 360, 30))
        ring = np.column_stack((0.5 * np.cos(a) + 2, 0.5 * np.sin(a) + 2, np.zeros(len(a))))
        out = ol.grow(ring, steps=250, spacing=0.08, bound=square(4.0, 0.0))
        self.assertTrue(np.all((out[:, :2] > -1e-6) & (out[:, :2] < 4.0 + 1e-6)))


if __name__ == "__main__":
    unittest.main()


class InTheModel(unittest.TestCase):
    """(0.561) bim.organic_line and the graph node «contorno_organico»."""

    def setUp(self):
        from arqbim.core.mesh import PolyMesh
        from arqbim.ifc import catalog
        from arqbim.model.document import AddObject, Document, SketchObject
        self.doc = Document()
        catalog.ensure(self.doc) if hasattr(catalog, "ensure") else None
        pts = [(0, 0, 0), (6, 0, 0), (6, 4, 0), (0, 4, 0)]
        sk = SketchObject("Polígono", np.eye(4), PolyMesh([np.array(p, float) for p in pts],
                                                           [list(range(len(pts)))]))
        self.doc.execute(AddObject(sk))
        self.sk = sk.id

    def test_smooth_makes_a_new_line(self):
        from arqbim.model import bim
        before = len(self.doc.objects)
        new = bim.organic_line(self.doc, self.sk, "suavizar", rounds=3)
        self.assertNotEqual(new, self.sk)
        self.assertEqual(len(self.doc.objects), before + 1)
        pts = np.array(self.doc.get(new).mesh.verts)
        self.assertGreater(len(pts), 20)
        self.doc.undo()
        self.assertEqual(len(self.doc.objects), before)

    def test_grow_meanders_inside(self):
        from arqbim.core import organic_lines as ol
        from arqbim.model import bim
        new = bim.organic_line(self.doc, self.sk, "crescer", steps=60, spacing=0.25, seed=3, inside=True)
        pts = np.array(self.doc.get(new).mesh.verts)
        self.assertGreater(len(pts), 30)
        self.assertTrue((pts[:, 0] > -0.05).all() and (pts[:, 0] < 6.05).all())
        self.assertFalse(ol.crosses_itself(pts, True))

    def test_graph_node(self):
        from arqbim.core.graph.registry import REGISTRY
        self.assertIn("contorno_organico", REGISTRY)
