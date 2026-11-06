"""0.436 — The curtain wall by an upright face, and along a free arc (the addon's «Fachada de vidro» circular and
«por face»)."""

import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

from arqbim.core import arcs  # noqa: E402
from arqbim.core import sketch_geometry as sg  # noqa: E402
from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import AddObject, Document, SketchObject  # noqa: E402


def box_object(doc, origin, du, dv, height):
    m = sg.rectangle_matrix(np.array(origin, float), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0)))
    mesh = sg.rectangle_mesh(du, dv)
    sg.push_pull(mesh, 0, m, height)
    obj = SketchObject("Volume", m, mesh)
    doc.execute(AddObject(obj))
    return obj


def face_towards(obj, normal):
    """The index of the face of a sketch whose normal (world) is `normal`."""
    m = obj.matrix
    for fi in range(len(obj.mesh.faces)):
        n = m[:3, :3] @ obj.mesh.face_normal(fi)
        if np.allclose(n, normal, atol=1e-6):
            return fi
    return None


class UprightFace(unittest.TestCase):
    """A 6 × 4 × 9 m volume: its front face (−y) frames 6 × 9 m from (0, 0, 0) to (6, 0, 0), out −y; its top face is
    not upright; a 4 m wall's face: its length and height."""

    def test_volume_and_wall(self):
        doc = Document()
        mass = box_object(doc, (0.0, 0.0, 0.0), 6.0, 4.0, 9.0)
        front = face_towards(mass, (0.0, -1.0, 0.0))
        self.assertIsNotNone(front)
        a, b, height, n = bim.upright_face(doc, mass.id, front, np.array((3.0, 0.0, 4.0)))
        self.assertTrue(np.allclose(n, (0.0, -1.0, 0.0)))
        self.assertAlmostEqual(height, 9.0, places=5)
        self.assertAlmostEqual(abs(b[0] - a[0]), 6.0, places=5)
        self.assertAlmostEqual(min(a[0], b[0]), 0.0, places=5)
        self.assertAlmostEqual(a[1], 0.0, places=5)
        self.assertAlmostEqual(a[2], 0.0, places=5)
        top = face_towards(mass, (0.0, 0.0, 1.0))
        self.assertIsNone(bim.upright_face(doc, mass.id, top, np.array((3.0, 2.0, 9.0))))
        wall = bim.add_wall(doc, np.array((10.0, 0.0, 0.0)), np.array((14.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        mesh = doc.get(wall).mesh
        fi = next(i for i in range(len(mesh.faces)) if np.allclose(mesh.face_normal(i), (0.0, -1.0, 0.0), atol=1e-6))
        a, b, height, n = bim.upright_face(doc, wall, fi, np.array((12.0, -0.1, 1.0)))
        self.assertAlmostEqual(abs(b[0] - a[0]), 4.0, places=4)
        self.assertAlmostEqual(height, bim.WALL_HEIGHT, places=4)
        self.assertAlmostEqual(a[1], -0.1, places=5)


class FreeArc(unittest.TestCase):
    """A curtain wall along a free arc through (0, 0), (4, 0) and (2, 1) — no wall there: its radius and length the
    arc's, not embedded; valid IFC."""

    def test_free_arc(self):
        doc = Document()
        curve = arcs.arc_through((0.0, 0.0), (4.0, 0.0), (2.0, 1.0))
        centre, r, start, sweep = curve
        guid = bim.add_curtain_wall(doc, None, None, 3.0, 1.5, 1.0, arc=(np.array((centre[0], centre[1], 0.0)), r,
                                                                         start, sweep))
        p = doc.ifc.curtain_params(guid)
        self.assertAlmostEqual(p["radius"], 2.5, places=6)                 # (r² = 4 + (r − 1)²)
        self.assertAlmostEqual(p["length"], 2.5 * abs(sweep), places=6)
        self.assertTrue(np.allclose(p["start"][:2], (0.0, 0.0), atol=1e-6) or np.allclose(p["end"][:2], (0.0, 0.0),
                                                                                          atol=1e-6))
        self.assertIsNone(doc.ifc.host_wall(guid))
        mid = doc.get(guid).mesh.verts.max(axis=0)
        self.assertGreater(mid[1], 0.9)                                     # (it bulges to y ≈ 1)
        self.assertLess(abs(math.degrees(sweep)), 180.0)
        self.assertEqual(doc.ifc.validate(), [])


if __name__ == "__main__":
    unittest.main()
