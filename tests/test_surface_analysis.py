"""0.559 — Gerador de formas orgânicas, step 8: curvature, panels' flatness, unrolled strips."""

import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arqbim.core import form_finding as ff  # noqa: E402
from arqbim.core import surface_analysis as sa  # noqa: E402


def grid(fn, n=31, size=4.0):
    t = np.linspace(-size / 2, size / 2, n)
    x, y = np.meshgrid(t, t)
    return np.stack((x, y, fn(x, y)), axis=-1)


class Curvature(unittest.TestCase):
    def test_kinds(self):
        flat = grid(lambda x, y: 0 * x)
        self.assertTrue(np.all(sa.classify(*sa.curvatures(flat)) == "plana"))
        sphere = grid(lambda x, y: np.sqrt(25 - x * x - y * y))                   # (R = 5 m)
        k1, k2 = sa.curvatures(sphere)
        self.assertAlmostEqual(abs(float(k1[15, 15])), 0.2, delta=0.01)
        self.assertAlmostEqual(abs(float(k2[15, 15])), 0.2, delta=0.01)
        self.assertEqual(sa.classify(k1, k2)[15, 15], "cupula")
        cyl = grid(lambda x, y: np.sqrt(25 - x * x))
        self.assertEqual(sa.classify(*sa.curvatures(cyl))[15, 15], "simples")
        saddle = grid(lambda x, y: 0.1 * (x * x - y * y))
        self.assertEqual(sa.classify(*sa.curvatures(saddle))[15, 15], "sela")
        rep = sa.report(sphere)
        self.assertGreater(rep["curvature"]["cupula"], 0.9)

    def test_panels_and_colours(self):
        flat = grid(lambda x, y: 0 * x, 11)
        self.assertLess(sa.warp(flat).max(), 1e-12)
        self.assertEqual(sa.report(flat)["panels"]["vidro plano"], 100)
        saddle = grid(lambda x, y: 0.2 * x * y, 11)
        self.assertGreater(sa.warp(saddle).max(), 0.01)
        tris, cols = sa.coloured_cells(saddle, what="planarity")
        self.assertEqual(tris.shape, (200, 3, 3))
        self.assertEqual(cols.shape, (200, 4))
        tris, cols = sa.coloured_cells(saddle)
        self.assertTrue(np.allclose(cols[0], sa.CLASS_RGBA["sela"]))


class Unroll(unittest.TestCase):
    def test_cylinder_unrolls_exactly(self):
        a = np.linspace(0, math.pi, 25)
        rows = np.stack([np.column_stack((3 * np.cos(a), np.full(25, z), 3 * np.sin(a))) for z in (0.0, 1.0, 2.0)])
        out = sa.strips(rows)
        self.assertEqual(len(out), 2)
        b, t = out[0]
        self.assertAlmostEqual(float(np.linalg.norm(np.diff(b, axis=0), axis=1).sum()),
                               float(np.linalg.norm(np.diff(rows[0], axis=0), axis=1).sum()), places=6)
        self.assertTrue(np.allclose(np.linalg.norm(t - b, axis=1), 1.0))       # (a straight strip 1 m wide)
        self.assertAlmostEqual(sa.strip_area(b, t), 3 * math.pi * 24 * math.sin(math.pi / 48) / (math.pi / 2) / 1,
                               delta=0.2)

    def test_dome_area_kept(self):
        t = np.linspace(0, 6, 15)
        x, y = np.meshgrid(t, t)
        rows = ff.find(np.stack((x, y, 0 * x), axis=-1), "catenaria", 2.0)
        area = 0.0
        for b, tt in sa.strips(rows):
            area += sa.strip_area(b, tt)
        self.assertAlmostEqual(area, ff.surface_area(rows), delta=ff.surface_area(rows) * 0.02)
        text, n = sa.unrolled_dxf(rows, name="Cúpula")
        self.assertEqual(n, 14)
        self.assertIn("FAIXAS", text)
        self.assertIn("F14", text)


if __name__ == "__main__":
    unittest.main()
