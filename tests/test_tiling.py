"""0.562 — Gerador de revestimentos, step 1: the layout of a finish's pieces (core/tiling.py)."""

import math
import os
import sys
import unittest

import numpy as np
import shapely
from shapely.geometry import Polygon

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arqbim.core import tiling as tl  # noqa: E402

ROOM = [(0, 0), (4.1, 0), (4.1, 3.05), (0, 3.05)]


def covered(r):
    return sum(p.area for p in r.pieces)


def overlaps(r):
    polys = [Polygon(p.points, p.holes) for p in r.pieces]
    tree = shapely.STRtree(polys)
    a, b = tree.query(polys, predicate="overlaps")
    bad = [(i, j) for i, j in zip(a, b) if i < j and polys[i].intersection(polys[j]).area > 1e-7]
    return len(bad)


class EveryBond(unittest.TestCase):
    def test_each_covers_without_overlap(self):
        """Every bond, joints off: the pieces cover the room but for the joints, and none overlaps another."""
        for key in tl.PATTERNS:
            d = {"pattern": key, "w": 0.6, "h": 0.2, "joint": 0.0}
            if key == "livre":
                d.update(w=0.4, h=0.4, unit=[[(0, 0), (0.4, 0), (0, 0.4)], [(0.4, 0), (0.4, 0.4), (0, 0.4)]])
            if key in ("hexagono", "escama"):
                d.update(w=0.3)
            with self.subTest(key):
                r = tl.lay(ROOM, d)
                self.assertGreater(len(r.pieces), 10)
                self.assertAlmostEqual(covered(r), 4.1 * 3.05, delta=0.02 * 4.1 * 3.05, msg=key)
                self.assertEqual(overlaps(r), 0, key)

    def test_joints_take_their_share(self):
        r = tl.lay(ROOM, {"w": 0.5, "h": 0.5, "joint": 0.01})
        whole = [p for p in r.pieces if p.whole]
        self.assertTrue(whole)
        self.assertAlmostEqual(whole[0].area, 0.49 * 0.49, places=6)

    def test_separate_joints(self):
        r = tl.lay(ROOM, {"w": 0.5, "h": 0.25, "joint": 0.002, "joint_v": 0.01})
        p = next(p for p in r.pieces if p.whole)
        xs, ys = [q[0] for q in p.points], [q[1] for q in p.points]
        self.assertAlmostEqual(max(xs) - min(xs), 0.49, places=6)
        self.assertAlmostEqual(max(ys) - min(ys), 0.248, places=6)


class Origin(unittest.TestCase):
    def test_corner(self):
        r = tl.lay(ROOM, {"w": 1.0, "h": 1.0, "joint": 0.0})
        self.assertEqual(r.counts()["A"], (12, 8))          # 4 × 3 whole; 4 + 3 + 1 cut

    def test_centre_on_a_piece(self):
        """Centred on a piece's middle: the cuts are the same both sides."""
        r = tl.lay([(0, 0), (5.0, 0), (5.0, 1.0), (0, 1.0)], {"w": 1.0, "h": 1.0, "joint": 0.0, "origin": "centro",
                                                              "align": "peca"})
        self.assertEqual(r.counts()["A"], (5, 0))
        r = tl.lay([(0, 0), (4.5, 0), (4.5, 1.0), (0, 1.0)], {"w": 1.0, "h": 1.0, "joint": 0.0, "origin": "centro",
                                                              "align": "peca"})
        cuts = sorted(p.area for p in r.pieces if not p.whole)
        self.assertEqual(len(cuts), 2)
        self.assertAlmostEqual(cuts[0], cuts[1], places=6)

    def test_point_and_shift(self):
        r = tl.lay(ROOM, {"w": 1.0, "h": 1.0, "joint": 0.0, "origin": "ponto", "point": (0.3, 0.0)})
        xs = sorted({round(min(q[0] for q in p.points), 6) for p in r.pieces})
        self.assertIn(0.3, xs)
        self.assertIn(1.3, xs)

    def test_auto_leaves_no_thin_strip(self):
        """A room 4.1 wide in 0.6 tiles from the corner leaves a 0.5 strip; 3.05 high leaves a 0.05 one. Auto starts
        where the narrowest cut is widest."""
        d = {"w": 0.6, "h": 0.6, "joint": 0.0}
        corner = tl.lay(ROOM, d)
        auto = tl.lay(ROOM, dict(d, origin="auto"))
        self.assertLess(corner.narrowest, 0.06)
        self.assertGreater(auto.narrowest, 0.15)
        self.assertEqual(auto.summary(0.1)["narrow"], 0)

    def test_angle_turns_it(self):
        r = tl.lay(ROOM, {"w": 1.0, "h": 0.2, "joint": 0.0, "angle": 90.0})
        p = next(p for p in r.pieces if p.whole)
        xs, ys = [q[0] for q in p.points], [q[1] for q in p.points]
        self.assertAlmostEqual(max(xs) - min(xs), 0.2, places=6)
        self.assertAlmostEqual(max(ys) - min(ys), 1.0, places=6)


class Shapes(unittest.TestCase):
    def test_holes_left_out(self):
        hole = [(1, 1), (2, 1), (2, 2), (1, 2)]
        r = tl.lay(ROOM, {"w": 0.3, "h": 0.3, "joint": 0.0}, holes=[hole])
        self.assertAlmostEqual(covered(r), 4.1 * 3.05 - 1.0, places=3)

    def test_running_bond_offsets(self):
        r = tl.lay([(0, 0), (3, 0), (3, 0.4), (0, 0.4)], {"pattern": "desencontrado", "w": 1.0, "h": 0.2,
                                                         "joint": 0.0, "bond": 0.5})
        rows = {}
        for p in r.pieces:
            rows.setdefault(round(min(q[1] for q in p.points), 3), set()).add(round(min(q[0] for q in p.points), 3))
        self.assertIn(0.5, rows[0.2])

    def test_kinds_of_bricks(self):
        r = tl.lay(ROOM, {"pattern": "flamengo", "w": 0.24, "h": 0.07, "joint": 0.01})
        self.assertEqual(set(r.counts()), {"A", "B"})
        r = tl.lay(ROOM, {"pattern": "opus", "w": 0.6, "h": 0.2, "joint": 0.005})
        self.assertEqual(set(r.counts()), {"A", "B", "C", "D"})

    def test_boards_of_the_lengths_given(self):
        r = tl.lay(ROOM, {"pattern": "reguas", "w": 1.2, "h": 0.15, "joint": 0.0, "lengths": [0.6, 0.9, 1.2]})
        lens = {round(max(q[0] for q in p.points) - min(q[0] for q in p.points), 3) for p in r.pieces if p.whole}
        self.assertTrue(lens <= {0.6, 0.9, 1.2}, lens)

    def test_too_many_refused(self):
        with self.assertRaises(tl.LayoutError):
            tl.lay([(0, 0), (100, 0), (100, 100), (0, 100)], {"w": 0.01, "h": 0.01})

    def test_bad_values_refused(self):
        for bad in ({"pattern": "x"}, {"w": 0}, {"joint": 0.5, "w": 0.6, "h": 0.6}, {"origin": "x"}):
            with self.assertRaises(tl.LayoutError):
                tl.layout(bad)


class OnAFace(unittest.TestCase):
    def test_wall_frame_x_level_y_up(self):
        wall = [(0, 0, 0), (0, 4, 0), (0, 4, 3), (0, 0, 3)]
        o, x, y, n = tl.face_frame(wall)
        self.assertAlmostEqual(abs(x[1]), 1.0)
        self.assertAlmostEqual(y[2], 1.0)
        xy = tl.to_plane(wall, (o, x, y, n))
        self.assertAlmostEqual(xy[:, 1].min(), 0.0)
        self.assertAlmostEqual(xy[:, 0].min(), 0.0)
        back = tl.to_space(xy, (o, x, y, n))
        self.assertTrue(np.allclose(back, wall))


if __name__ == "__main__":
    unittest.main()
