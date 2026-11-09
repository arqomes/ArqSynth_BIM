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

    def test_transformed_handles_resized(self):
        """0.492 — Moved, turned and scaled by a matrix of the model's axes (the BIM's Mover, Rodar, Escala): the base's
        middle taken, the turn and the scale the Presentation's numbers again; the faces' grips at their middles; a face
        dragged out, the opposite one kept."""
        m = np.eye(4)
        m[:3, 3] = (1.0, -2.0, 0.5)
        moved = dia.transformed(box(), m)
        self.assertEqual((moved["position"], moved["rotation"], moved["scale"]), ((11.0, 3.0, 1.5), (0, 0, 0),
                                                                                   (1.0, 1.0, 1.0)))
        c, s = math.cos(math.radians(90)), math.sin(math.radians(90))
        turn = np.eye(4)
        turn[:2, :2] = ((c, -s), (s, c))                                  # (90° about the vertical, round the origin)
        turned = dia.transformed(box(), turn)
        np.testing.assert_allclose(turned["position"], (-5.0, 10.0, 1.0), atol=1e-6)
        np.testing.assert_allclose(turned["rotation"], (0.0, 90.0, 0.0), atol=1e-6)
        np.testing.assert_allclose(dia.shape(turned)[0].min(axis=0), (-6.0, 8.0, 1.0), atol=1e-6)
        twice = dia.transformed(box(), np.diag((2.0, 2.0, 2.0, 1.0)))
        np.testing.assert_allclose((twice["position"], twice["scale"]), ((20.0, 10.0, 2.0), (2.0, 2.0, 2.0)))
        self.assertEqual(dia.euler_of(np.eye(3)), (0.0, 0.0, 0.0))
        grips = dia.handles(box())
        self.assertEqual(len(grips), 6)
        top = next(p for k, side, p in grips if (k, side) == (1, 1))
        np.testing.assert_allclose(top, (10.0, 5.0, 4.0))
        east = next(p for k, side, p in grips if (k, side) == (0, 1))
        np.testing.assert_allclose(east, (12.0, 5.0, 2.5))
        self.assertEqual(len(dia.handles(box(type="plane"))), 4)
        wider = dia.resized(box(), 0, 1, 1.0)                              # (the east face 1 m out: the west stays)
        lo, hi = dia.shape(wider)[0].min(axis=0), dia.shape(wider)[0].max(axis=0)
        np.testing.assert_allclose((lo[0], hi[0]), (8.0, 13.0))
        taller = dia.resized(box(), 1, -1, 0.5)                            # (the bottom 0,5 m down: the top stays)
        lo, hi = dia.shape(taller)[0].min(axis=0), dia.shape(taller)[0].max(axis=0)
        np.testing.assert_allclose((lo[2], hi[2]), (0.5, 4.0))
        self.assertAlmostEqual(dia.resized(box(), 2, 1, -9.0)["dimensions"][2], 0.01)   # (never through itself)
        np.testing.assert_allclose(dia.face_axis(turned, 0), (0.0, 1.0, 0.0), atol=1e-9)

    @unittest.skipIf(dia.engine() is None, "sem o manifold3d")
    def test_combine_the_five(self):
        """0.493 — Two boxes (A 4 × 3 × 2 m³ = 24, B 2 × 2 × 2 = 8, sharing 4) combined as the Presentation combines
        them: União 28, A − B 20, B − A 4, Interseção 4, Diferença 24; the result solid, A's colour, named after the
        operation («União», then «União 2»), where its box is; its origins kept and hidden."""
        a = box(id="a", position=(0, 0, 0), color="#a78bfa", opacity=0.4)
        b = box(id="b", dimensions=(2, 2, 2), position=(2, 0, 0))
        for op, size, width in (("union", 28, 5), ("subtract", 20, 4), ("reverse_subtract", 4, 1),
                                ("intersect", 4, 1), ("difference", 24, 5)):
            items, r_id = dia.combine([a, b], "a", "b", op, "R")
            r = items[-1]
            self.assertEqual((r["id"], r["source"], r["type"], r["boolean"]["operation"]), (r_id, "boolean", "box", op))
            self.assertAlmostEqual(dia.volume(r), size, places=4)
            self.assertAlmostEqual(r["dimensions"][0], width, places=5)
            self.assertEqual((r["color"], r["opacity"], [o["visible"] for o in items[:2]]), ("#a78bfa", 1.0,
                                                                                            [False, False]))
        items, _r = dia.combine([a, b], "a", "b", "union", "União")
        np.testing.assert_allclose(items[-1]["position"], (0.5, 0.0, 0.0), atol=1e-6)    # (−2 … 3 along X)
        lo, hi = dia.shape(items[-1])[0].min(axis=0), dia.shape(items[-1])[0].max(axis=0)
        np.testing.assert_allclose((lo, hi), ((-2, -1, 0), (3, 1, 3)), atol=1e-5)
        again, _r2 = dia.combine(items, "a", "b", "union", "União", hide=False)
        self.assertEqual(again[-1]["name"], "União 2")
        self.assertEqual(dia.combine([a, b], "a", "b", "union", "União", hide=False)[0][0]["visible"], True)
        self.assertEqual(dia.clean(items[-1]), items[-1])                              # (kept as it is)

    @unittest.skipIf(dia.engine() is None, "sem o manifold3d")
    def test_combine_refused(self):
        """A plane (no thickness), two that do not meet in an intersection (nothing left), the same one twice, a result
        made of itself, a locked result updated: refused, nothing changed."""
        a, b = box(id="a", position=(0, 0, 0)), box(id="b", dimensions=(2, 2, 2), position=(2, 0, 0))
        cases = (([a, box(id="p", type="plane")], ("a", "p", "union"), "plane_thin"),
                 ([a, box(id="f", position=(50, 0, 0))], ("a", "f", "intersect"), "empty_result"),
                 ([a, b], ("a", "a", "union"), "pick_different"))
        for items, (x, y, op), code in cases:
            with self.assertRaises(dia.BooleanError) as caught:
                dia.combine(items, x, y, op, "R")
            self.assertEqual(caught.exception.code, code)
        items, r_id = dia.combine([a, b], "a", "b", "union", "R")
        self.assertEqual(dia.graph_error(items, r_id, "a", target=r_id), "cycle")
        locked = [dict(o, locked=True) if o["id"] == r_id else o for o in items]
        with self.assertRaises(dia.BooleanError) as caught:
            dia.combine(locked, "a", "b", "intersect", "R", target=r_id)
        self.assertEqual(caught.exception.code, "unlock_first")

    @unittest.skipIf(dia.engine() is None, "sem o manifold3d")
    def test_refreshed_when_an_origin_changes(self):
        """(the BIM's own) B moved 1 m east: the União calculated again by itself — 6 m wide, its middle 0,5 m east —,
        its name and look kept; a result moved by hand keeps where it was put (moved as its box moved); a result made
        of a result after it; a result that can no longer be made kept as it was, said why."""
        a, b = box(id="a", position=(0, 0, 0)), box(id="b", dimensions=(2, 2, 2), position=(2, 0, 0))
        items, r_id = dia.combine([a, b], "a", "b", "union", "União")
        items = [dict(o, color="#fb7185", position=(0.5, 10.0, 0.0)) if o["id"] == r_id else o for o in items]
        moved = [dict(o, position=(3.0, 0.0, 0.0)) if o["id"] == "b" else o for o in items]
        again, errors = dia.refreshed(moved)
        r = next(o for o in again if o["id"] == r_id)
        self.assertEqual((errors, r["name"], r["color"]), ([], "União", "#fb7185"))
        np.testing.assert_allclose((r["dimensions"][0], r["position"][0], r["position"][1]), (6.0, 1.0, 10.0),
                                   atol=1e-6)
        self.assertFalse(dia.stale(r, again))
        self.assertEqual(dia.refreshed(again)[0], again)                                # (nothing to do: the same)
        c = box(id="c", type="cylinder", dimensions=(2, 4, 2), position=(0, 0, 0))
        fresh, r_id = dia.combine([a, b, c], "a", "b", "union", "União")
        chain, c_id = dia.combine(fresh, r_id, "c", "subtract", "Subtração")             # ((A ∪ B) − C)
        far = [dict(o, position=(4.0, 0.0, 0.0)) if o["id"] == "b" else o for o in chain]
        done, errors = dia.refreshed(far)
        sizes = {o["id"]: dia.volume(o) for o in done if dia.is_boolean(o)}
        self.assertAlmostEqual(sizes[r_id], 32.0, places=4)                             # (apart: 24 + 8)
        self.assertAlmostEqual(sizes[c_id], 32.0 - 3 * 16 * math.sin(math.pi / 16), places=3)   # (a 32-gon's)
        self.assertEqual([dia.stale(o, done) for o in done if dia.is_boolean(o)], [False, False])
        inter, i_id = dia.combine([a, b], "a", "b", "intersect", "Interseção")
        apart = [dict(o, position=(40.0, 0.0, 0.0)) if o["id"] == "b" else o for o in inter]
        kept, errors = dia.refreshed(apart)
        self.assertEqual([(d["id"], code) for d, code in errors], [(i_id, "empty_result")])
        self.assertEqual(next(o for o in kept if o["id"] == i_id)["boolean"], inter[-1]["boolean"])

    @unittest.skipIf(dia.engine() is None, "sem o manifold3d")
    def test_result_removed_shape_and_presentation(self):
        """A result taken away gives its origins back as they were shown; an origin knows its results. Drawn sharp at
        its edges (the faces' normals across a fold their own). As the Presentation's DiagramObject: «boolean», the
        origins «bim_dia_…», the base in the GLB's axes, the mesh on the unit box."""
        a, b = box(id="a", position=(0, 0, 0)), box(id="b", dimensions=(2, 2, 2), position=(2, 0, 0))
        items, r_id = dia.combine([a, b], "a", "b", "union", "União")
        self.assertEqual([o["id"] for o in dia.dependents(items, "b")], [r_id])
        self.assertEqual([(o["id"], o["visible"]) for o in dia.without(items, r_id)], [("a", True), ("b", True)])
        points, normals, tri = dia.shape(items[-1])
        self.assertEqual(len(points), len(tri) * 3)
        np.testing.assert_allclose(np.abs(normals).max(axis=1), 1.0, atol=1e-9)        # (all along the axes)
        out = dia.to_presentation(items[-1], lambda p: (p[0], p[2], -p[1]))
        b_out = out["boolean"]
        self.assertEqual((out["source"], out["type"], b_out["operation"], b_out["inputA"], b_out["inputB"],
                          b_out["hiddenInputs"], b_out["base"]), ("boolean", "box", "union", "bim_dia_a", "bim_dia_b",
                                                                  ["bim_dia_a", "bim_dia_b"],
                                                                  {"position": [0.5, 0.0, 0.0],
                                                                   "dimensions": [5.0, 3.0, 2.0]}))
        unit = np.array(b_out["mesh"]["positions"]).reshape(-1, 3)
        np.testing.assert_allclose((unit.min(axis=0), unit.max(axis=0)), ((-0.5, 0, -0.5), (0.5, 1, 0.5)), atol=1e-6)
        self.assertAlmostEqual(b_out["mesh"]["unitVolume"], 28 / 30, places=6)

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
