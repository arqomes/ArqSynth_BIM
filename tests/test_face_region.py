"""0.564 — the flat face of an element round a point (core/face_region.py)."""

import os
import sys
import unittest

import numpy as np
from shapely.geometry import Polygon

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arqbim.core import face_region as fr  # noqa: E402
from arqbim.core import tiling as tl  # noqa: E402


def box_mesh(x0, y0, z0, x1, y1, z1):
    v = np.array([(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)], float)
    q = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    t = [(a, b, c) for a, b, c, d in q] + [(a, c, d) for a, b, c, d in q]
    return v, np.array(t)


class Faces(unittest.TestCase):
    def test_a_box_side(self):
        v, t = box_mesh(0, 0, 0, 4, 0.2, 2.7)
        out = fr.face_at(v, t, (2.0, 0.0, 1.0), (0, -1, 0))
        self.assertIsNotNone(out)
        outline, holes, n = out
        self.assertEqual(len(outline), 4)
        self.assertEqual(holes, [])
        self.assertAlmostEqual(Polygon(tl.to_plane(outline, tl.face_frame(outline))).area, 4 * 2.7, places=4)

    def test_a_face_with_a_hole(self):
        """A wall's face with a window: two boxes left and right, one under and one over — the face has a hole."""
        parts = [box_mesh(0, 0, 0, 1, 0.2, 2.7), box_mesh(2, 0, 0, 4, 0.2, 2.7), box_mesh(1, 0, 0, 2, 0.2, 1.0),
                 box_mesh(1, 0, 2.0, 2, 0.2, 2.7)]
        verts, tris, k = [], [], 0
        for v, t in parts:
            verts.append(v)
            tris.append(t + k)
            k += len(v)
        out = fr.face_at(np.vstack(verts), np.vstack(tris), (0.5, 0.0, 1.0), (0, -1, 0))
        outline, holes, _n = out
        self.assertEqual(len(holes), 1)
        area = Polygon(tl.to_plane(outline, tl.face_frame(outline)),
                       [tl.to_plane(h, tl.face_frame(outline)) for h in holes]).area
        self.assertAlmostEqual(area, 4 * 2.7 - 1.0, places=3)

    def test_nothing_there(self):
        v, t = box_mesh(0, 0, 0, 4, 0.2, 2.7)
        self.assertIsNone(fr.face_at(v, t, (2.0, 0.5, 1.0), (0, -1, 0)))


if __name__ == "__main__":
    unittest.main()
