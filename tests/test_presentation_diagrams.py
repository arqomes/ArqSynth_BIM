"""0.487 — The ArqSynth Presentation's volumes for diagrams (model/presentation_diagrams.py)."""

import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arqbim.model import presentation_diagrams as dia  # noqa: E402


def box(**fields):
    return dia.clean(dict({"id": "a1", "type": "box", "name": "Caixa 1", "dimensions": (4, 3, 2),
                           "position": (10, 5, 1)}, **fields))


class Volumes(unittest.TestCase):
    def test_clean(self):
        """As the Presentation's normalizeDiagram: its five kinds only, each number in its range, a colour #rrggbb
        (else the first of the five), an opacity 0–1."""
        self.assertIsNone(dia.clean({"id": "x", "type": "pirâmide"}))
        self.assertIsNone(dia.clean({"type": "box"}))
        d = dia.clean({"id": "x", "type": "sphere", "dimensions": (-1, 2, "a"), "scale": (500, 1, 1),
                       "color": "azul", "opacity": 3, "rotation": (0, 90)})
        self.assertEqual((d["dimensions"], d["scale"], d["color"], d["opacity"], d["rotation"]),
                         ((0.01, 2.0, 2.0), (100.0, 1.0, 1.0), "#38bdf8", 1.0, (0.0, 90.0, 0.0)))
        self.assertEqual([x["id"] for x in dia.clean_all([box(), box(), {"id": "b", "type": "cone"}])], ["a1", "b"])

    def test_new_and_copy(self):
        """A new one beside the model (a fifth of its radius, 1–10 m; past its east side, at its lowest level), named
        «Caixa N» (the lowest free), the next colour, 85 %; a copy «… cópia», moved its width × 1,2 along X."""
        items = [box()]
        d = dia.new("cylinder", items, (0, 0, -1), (20, 10, 9), base="Cilindro")
        radius = math.dist((0, 0, -1), (20, 10, 9)) / 2
        unit = min(10.0, max(1.0, radius * 0.2))
        self.assertEqual((d["type"], d["name"], d["color"], d["opacity"]), ("cylinder", "Cilindro 1", "#f59e0b", 0.85))
        np.testing.assert_allclose(d["dimensions"], (unit, unit, unit), atol=1e-6)        # (kept to the micrometre)
        np.testing.assert_allclose(d["position"], (10 + 10 + unit, 5, -1), atol=1e-6)
        self.assertEqual(dia.new("box", items, None, None, base="Caixa")["name"], "Caixa 2")
        twin = dia.duplicate(dict(box(), locked=True), items)
        self.assertEqual((twin["name"], twin["locked"]), ("Caixa 1 cópia", False))
        self.assertNotEqual(twin["id"], "a1")
        np.testing.assert_allclose(twin["position"], (10 + 4 * 1.2, 5, 1))
        self.assertEqual(dia.duplicate(box(), items + [dict(twin)])["name"], "Caixa 1 cópia 2")

    def test_shape_in_the_model_axes(self):
        """Made as three.js makes it — the unit shape on its base, by the measures, the scale, the turn (Euler XYZ in
        the Presentation's axes), moved — in the model's axes: the base's middle where it is, the height up; turned 90°
        about the vertical its width goes along Y; a plane flat at its level."""
        points, normals, triangles = dia.shape(box())
        np.testing.assert_allclose(points.min(axis=0), (8, 4, 1))
        np.testing.assert_allclose(points.max(axis=0), (12, 6, 4))
        self.assertEqual(len(triangles), 12)
        np.testing.assert_allclose(np.linalg.norm(normals, axis=1), 1.0)
        turned, _n, _t = dia.shape(box(rotation=(0, 90, 0)))
        np.testing.assert_allclose(turned.min(axis=0), (9, 3, 1), atol=1e-9)
        np.testing.assert_allclose(turned.max(axis=0), (11, 7, 4), atol=1e-9)
        tall, _n, _t = dia.shape(box(scale=(1, 2, 1)))
        self.assertAlmostEqual(float(tall[:, 2].max()), 7.0)
        flat, _n, tri = dia.shape(box(type="plane"))
        np.testing.assert_allclose(flat[:, 2], 1.0)
        self.assertEqual(len(tri), 2)
        for kind in ("cylinder", "sphere", "cone"):
            pts, _n, tri = dia.shape(box(type=kind))
            np.testing.assert_allclose(pts.min(axis=0), (8, 4, 1), atol=1e-9)
            np.testing.assert_allclose(pts.max(axis=0), (12, 6, 4), atol=1e-9)
            self.assertTrue(len(tri) > 30)
        self.assertEqual(len(dia.outline(box())), 12)
        self.assertEqual(len(dia.outline(box(type="plane"))), 4)
        lo, hi = dia.bounds([box(), box(id="b", position=(0, 0, 0), visible=False)])
        np.testing.assert_allclose(lo, (8, 4, 1))

    def test_volume_and_presentation(self):
        """Its volume (box w·h·d, cylinder ×π/4, sphere ×π/6, cone ×π/12, plane 0); as the Presentation's
        DiagramObject — «bim_dia_<id>», the base's middle in the GLB's axes, the rest its own numbers."""
        self.assertAlmostEqual(dia.volume(box()), 24.0)
        self.assertAlmostEqual(dia.volume(box(type="cylinder")), 24.0 * math.pi / 4)
        self.assertAlmostEqual(dia.volume(box(type="plane")), 0.0)
        out = dia.to_presentation(box(rotation=(0, 45, 0), color="#a78bfa", description="Ampliação"),
                                  lambda p: (p[0], p[2], -p[1]))
        self.assertEqual(out, {"id": "bim_dia_a1", "name": "Caixa 1", "source": "primitive", "type": "box",
                               "dimensions": [4.0, 3.0, 2.0],
                               "transform": {"position": [10.0, 1.0, -5.0], "rotation": [0.0, 45.0, 0.0],
                                             "scale": [1.0, 1.0, 1.0]},
                               "material": {"color": "#a78bfa", "opacity": 1.0, "wireframe": False},
                               "visible": True, "locked": False, "metadata": {"description": "Ampliação"}})
        self.assertEqual([d["id"] for d in dia.with_one([box()], box(id="b"))], ["a1", "b"])
        self.assertEqual(dia.with_one([box()], box(name="Outra"))[0]["name"], "Outra")
        self.assertEqual(dia.without([box(), box(id="b")], "a1")[0]["id"], "b")


if __name__ == "__main__":
    unittest.main()
