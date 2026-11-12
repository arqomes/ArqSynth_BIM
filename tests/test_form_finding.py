"""0.554 — Gerador de formas orgânicas, step 1: form finding (membrane, cushion, inverted catenary, smoothing)."""

import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arqbim.core import form_finding as ff  # noqa: E402


def square(n=21, size=4.0, z=0.0):
    t = np.linspace(0.0, size, n)
    x, y = np.meshgrid(t, t)
    return np.stack((x, y, np.full_like(x, z)), axis=-1)


class Membrane(unittest.TestCase):
    def test_flat_outline_flat_membrane(self):
        rows = square()
        rows[5:15, 5:15, 2] = 3.0                                   # (a lump inside: pulled flat)
        out = ff.find(rows, "membrana")
        self.assertLess(np.abs(out[..., 2]).max(), 1e-4)

    def test_mast(self):
        rows = square(31)
        fixed = ff.boundary_mask(rows.shape, False)
        fixed[15, 15] = True
        rows[15, 15, 2] = 3.0                                       # (a mast 3 m high in the middle)
        out = ff.find(rows, "membrana", fixed=fixed)
        z = out[..., 2]
        self.assertAlmostEqual(z[15, 15], 3.0)
        self.assertTrue(z[15, 10] > z[15, 5] > 0.0)                 # (falling from the mast to the edge)
        self.assertTrue(np.all(z[1:-1, 1:-1] <= 3.0 + 1e-9))
        mid = z[15, 1:15]                                           # (a tent: concave between mast and edge)
        line = np.linspace(z[15, 1], z[15, 15], len(mid) + 1)[:-1]
        self.assertTrue(np.all(mid[1:-1] <= line[1:-1] + 1e-6))
        cone = rows.copy()                                          # (a straight cone has more area: the
        r = np.hypot(cone[..., 0] - 2.0, cone[..., 1] - 2.0)         #  membrane is the least-tension one)
        cone[..., 2] = np.where(fixed, cone[..., 2], np.clip(3.0 * (1 - r / 2.0), 0.0, 3.0))
        cone[15, 15, 2] = 3.0
        self.assertLess(ff.surface_area(out), ff.surface_area(cone))


class Loaded(unittest.TestCase):
    def test_catenary_height_and_shape(self):
        out = ff.find(square(25), "catenaria", height=2.0)
        z = out[..., 2]
        self.assertAlmostEqual(z.max(), 2.0, places=6)
        self.assertAlmostEqual(z[12, 12], z.max(), places=3)        # (highest in the middle)
        np.testing.assert_allclose(out[..., :2], square(25)[..., :2], atol=1e-6)   # (its plan kept)
        self.assertTrue(np.allclose(z, z.T, atol=1e-4))             # (symmetric)
        down = ff.find(square(25), "catenaria", height=-1.0)        # (hung, not turned)
        self.assertAlmostEqual(down[..., 2].min(), -1.0, places=6)

    def test_cushion(self):
        rows = square(25)
        out = ff.find(rows, "almofada", height=1.0)
        z = out[..., 2]
        self.assertAlmostEqual(z.max(), 1.0, places=5)
        self.assertTrue(np.all(z[1:-1, 1:-1] > 0))
        np.testing.assert_allclose(out[0], rows[0], atol=1e-12)     # (its edge held)
        moved = np.hypot(*(out[1:-1, 1:-1, :2] - rows[1:-1, 1:-1, :2]).transpose(2, 0, 1))
        self.assertGreater(moved.max(), 0.02)                       # (its plan swells: pushed square to itself)
        self.assertGreater(ff.surface_area(out), ff.surface_area(rows))

    def test_ring_grid_with_a_tip(self):
        nu, nv = 32, 10
        a = np.linspace(0, 2 * math.pi, nu, endpoint=False)
        ring = np.column_stack((3 * np.cos(a), 3 * np.sin(a), np.zeros(nu)))
        t = (np.arange(nv + 1) / nv)[:, None, None]
        rows = ring[None] * (1 - t)                                 # (rings to the middle: its last row a tip)
        fixed = np.zeros(rows.shape[:2], dtype=bool)
        fixed[0] = True
        out = ff.find(rows, "catenaria", height=1.5, fixed=fixed, close_u=True)
        self.assertAlmostEqual(out[-1, :, 2].max(), out[-1, :, 2].min())
        self.assertAlmostEqual(out[..., 2].max(), 1.5, places=5)


class Smooth(unittest.TestCase):
    def test_no_shrinking(self):
        rows = square(21)
        rng = np.random.default_rng(1)
        rows[1:-1, 1:-1, 2] = 1.0 + rng.normal(0, 0.2, (19, 19))
        rows[0, :, 2] = rows[-1, :, 2] = rows[:, 0, 2] = rows[:, -1, 2] = 1.0
        out = ff.find(rows, "suavizar")
        self.assertLess(out[1:-1, 1:-1, 2].std(), rows[1:-1, 1:-1, 2].std() / 3)
        self.assertAlmostEqual(out[..., 2].mean(), rows[..., 2].mean(), delta=0.05)

    def test_errors(self):
        with self.assertRaises(ff.FormError):
            ff.find(square(), "torcer")
        with self.assertRaises(ff.FormError):
            ff.find(square()[:2], "membrana")


if __name__ == "__main__":
    unittest.main()
