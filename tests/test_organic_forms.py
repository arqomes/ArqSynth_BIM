"""0.555 — Gerador de formas orgânicas, step 2: the organic op of the Superfície paramétrica, over an outline drawn, a
wall's face, a slab, a ceiling — or measures."""

import math
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["ARQSYNTH_HOME"] = tempfile.mkdtemp(prefix="arqsynth_organic_")

from arqbim.core import param_surface as ps  # noqa: E402
from arqbim.core.mesh import PolyMesh  # noqa: E402
from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import AddObject, Document, SketchObject  # noqa: E402


def polygon(doc, pts):
    obj = SketchObject("Polígono", np.eye(4), PolyMesh([np.array(p, float) for p in pts], [list(range(len(pts)))]))
    doc.execute(AddObject(obj))
    return obj


def world_rows(doc, guid):
    on = ps.Surface(doc.ifc.surface_definition(guid))
    m = doc.ifc._placement_si(doc.ifc.by_guid(guid))
    rows = on.rows.reshape(-1, 3)
    return (m @ np.column_stack((rows, np.ones(len(rows)))).T).T[:, :3].reshape(on.rows.shape)


class FromMeasures(unittest.TestCase):
    def test_shapes(self):
        r = bim.organic_shape("retangulo", (5, 5, 0), 10, 6)
        self.assertEqual(r.shape, (4, 3))
        c = bim.organic_shape("circulo", (0, 0, 1), 8)
        np.testing.assert_allclose(np.hypot(c[:, 0], c[:, 1]), 4.0)
        self.assertEqual(len(bim.organic_shape("poligono", (0, 0, 0), 6, sides=7)), 7)

    def test_each_behaviour(self):
        for behaviour, height in (("catenaria", 3.0), ("almofada", 1.5), ("membrana", 4.0), ("catenaria", -1.0)):
            doc = Document()
            guid = bim.add_organic_form(doc, bim.organic_shape("retangulo", (0, 0, 0), 12, 8), behaviour, height)
            self.assertEqual(doc.ifc.kind_of(guid), "param_surface")
            self.assertEqual(doc.ifc.surface_usage(guid), "cobertura")
            rows = world_rows(doc, guid)
            z = rows[..., 2]
            if height > 0:
                self.assertAlmostEqual(z.max(), height, delta=0.02, msg=behaviour)
            else:
                self.assertAlmostEqual(z.min(), height, delta=0.02, msg=behaviour)
            edge = np.concatenate((rows[0], rows[-1], rows[:, 0], rows[:, -1]))
            self.assertLess(np.abs(edge[:, 2]).max(), 1e-6, behaviour)          # (its edge on the outline)
            self.assertLessEqual(np.abs(rows[..., 0]).max(), 6.0 + 0.6, behaviour)
            verts, faces = doc.ifc.triangulate([guid])[guid]
            self.assertGreater(len(faces), 100)

    def test_circle_rings(self):
        doc = Document()
        guid = bim.add_organic_form(doc, bim.organic_shape("circulo", (0, 0, 0), 10), "catenaria", 3.0,
                                    grid="aneis")
        rows = world_rows(doc, guid)
        self.assertAlmostEqual(rows[..., 2].max(), 3.0, delta=0.02)
        self.assertAlmostEqual(rows[-1, :, 2].max(), rows[-1, :, 2].min())       # (its middle one point)


class FromTheModel(unittest.TestCase):
    def test_polygon_followed(self):
        doc = Document()
        obj = polygon(doc, [(0, 0, 0), (10, 0, 0), (12, 6, 0), (4, 9, 0), (-2, 5, 0)])
        ring, uid, what = bim.organic_outline(doc, obj.id)
        self.assertEqual((what, len(ring)), ("sketch", 5))
        guid = bim.add_organic_form(doc, ring, "almofada", 2.0, source_uid=uid)
        before = world_rows(doc, guid)[..., 0].max()
        self.assertTrue(doc.ifc.surfaces_following([uid]))
        live = doc.get(obj.id)
        chains = {uid: [(np.array([(0, 0, 0), (20, 0, 0), (22, 6, 0), (4, 9, 0), (-2, 5, 0)], float), True)]}
        doc.ifc.follow_curves(guid, chains)                                       # (the polygon drawn wider)
        self.assertGreater(world_rows(doc, guid)[..., 0].max(), before + 5.0)
        self.assertIsNotNone(live)

    def test_wall_face(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        ring, uid, what = bim.organic_outline(doc, wall)
        self.assertEqual((what, uid), ("wall", None))
        guid = bim.add_organic_form(doc, ring, "almofada", 0.6)
        self.assertEqual(doc.ifc.surface_usage(guid), "fachada")
        rows = world_rows(doc, guid)
        frame = doc.ifc.element_frame(wall)
        off = (rows.reshape(-1, 3) - frame.to_world((0.0, frame.y1, 0.0))) @ (frame.matrix[:3, 1] /
                                                                             np.linalg.norm(frame.matrix[:3, 1]))
        self.assertAlmostEqual(abs(off).max(), 0.6, delta=0.02)                   # (bulging off the face, 60 cm)
        self.assertLess(np.ptp(rows[..., 2]), frame.height + 0.3)

    def test_slab_and_ceiling(self):
        doc = Document()
        slab = bim.add_slab_outline(doc, [(0, 0), (8, 0), (8, 5), (0, 5)], 3.0, catalog.BY_KEY["laje_15"])
        ring, _uid, what = bim.organic_outline(doc, slab)
        self.assertEqual(what, "slab")
        guid = bim.add_organic_form(doc, ring, "catenaria", 2.0)
        top = doc.ifc.slab_outline(slab)["top"]
        self.assertAlmostEqual(world_rows(doc, guid)[..., 2].max(), top + 2.0, delta=0.02)
        ceiling = bim.add_ceiling(doc, [(0, 0), (4, 0), (4, 4), (0, 4)])
        ring, _uid, what = bim.organic_outline(doc, ceiling)
        self.assertEqual(what, "ceiling")
        guid = bim.add_organic_form(doc, ring, "catenaria", -0.5)                  # (hanging under the ceiling)
        self.assertAlmostEqual(world_rows(doc, guid)[..., 2].min(), doc.ifc.ceiling_params(ceiling)["z"] - 0.5,
                               delta=0.02)
        with self.assertRaises(ValueError):
            bim.organic_outline(doc, "nada")

    def test_editable_definition(self):
        doc = Document()
        guid = bim.add_organic_form(doc, bim.organic_shape("elipse", (0, 0, 0), 10, 6), "catenaria", 2.0)
        data = doc.ifc.surface_definition(guid)
        data["surface"]["height"] = 4.0
        bim.set_param_surface(doc, guid, data)
        self.assertAlmostEqual(world_rows(doc, guid)[..., 2].max(), 4.0, delta=0.03)
        data["surface"]["behaviour"] = "torcer"
        self.assertTrue(ps.validate(data))
        self.assertTrue(math.isfinite(doc.ifc.surface_summary(guid)["area"]))


class Control(unittest.TestCase):
    """0.556 — masts, supports, ridges and valleys, free edges."""

    def _form(self, **surface):
        data = ps.default_definition("organic")
        ring = bim.organic_shape("retangulo", (6, 4, 0), 12, 8)
        data["curves"] = [{"id": "c1", "points": ring.tolist(), "closed": True}]
        data["surface"].update(boundary="c1", **surface)
        self.assertEqual(ps.validate(data), [])
        on = ps.Surface(data)
        o, x, y, n = ps.outline_frame(np.asarray(ring, float))
        return on.rows, o, x, y

    def test_mast_and_support(self):
        rows, o, x, y = self._form(behaviour="membrana", height=0.0,
                                   points=[{"u": -3.0, "v": 0.0, "h": 5.0, "r": 0.3, "kind": "mastro"},
                                           {"u": 3.0, "v": 0.0, "h": 2.0, "r": 0.3, "kind": "mastro"}])
        z = rows[..., 2]
        near = lambda u, v: z.reshape(-1)[np.argmin(np.hypot(*((rows.reshape(-1, 3) - o) @ np.stack((x, y)).T
                                                               - (u, v)).T))]
        self.assertAlmostEqual(near(-3, 0), 5.0, places=6)
        self.assertAlmostEqual(near(3, 0), 2.0, places=6)
        self.assertTrue(0 < near(0, 0) < 5.0)

    def test_ridge_and_valley(self):
        rows, o, x, y = self._form(behaviour="membrana", height=0.0,
                                   lines=[{"a": [-5, 0], "b": [5, 0], "h": 3.0, "kind": "cumeeira"}])
        local = (rows.reshape(-1, 3) - o) @ np.stack((x, y)).T
        z = rows.reshape(-1, 3)[:, 2]
        on_line = (np.abs(local[:, 1]) < 0.15) & (np.abs(local[:, 0]) < 4.5)
        self.assertTrue(on_line.any())
        self.assertTrue(np.allclose(z[on_line], 3.0))
        catenary = self._form(behaviour="catenaria", height=3.0,
                              lines=[{"a": [-5, 0], "b": [5, 0], "h": -0.5, "kind": "vale"}])[0]
        self.assertLess(catenary[..., 2].min(), -0.4)                             # (a valley pulled down)

    def test_free_edges(self):
        held, o, x, y = self._form(behaviour="membrana", height=4.0)
        free = self._form(behaviour="membrana", height=4.0, free_edges=True)[0]
        mid = held.shape[0] // 2
        self.assertLess(np.abs(free[0, mid, 2] - held[0, mid, 2]), 10)            # (it is worked out)
        edge_y_held = (held[0, mid] - o) @ y
        edge_y_free = (free[0, mid] - o) @ y
        self.assertGreater(edge_y_free, edge_y_held + 0.3)                        # (its edge pulled in, as a sail)
        corners = [free[0, 0], free[0, -1], free[-1, 0], free[-1, -1]]
        self.assertTrue(all(abs(c[2]) < 1e-9 for c in corners))                   # (held at its corners)
        self.assertGreater(free[0, mid, 2], 0.05)                                 # (its free edge lifted)


class Oculus(unittest.TestCase):
    """0.557 — an oculus: an opening with a ring held at a height."""

    def test_oculus_in_a_shell(self):
        doc = Document()
        guid = bim.add_organic_form(doc, bim.organic_shape("retangulo", (0, 0, 0), 12, 12), "catenaria", 3.0)
        plain = len(ps.Surface(doc.ifc.surface_definition(guid)).mesh()[1])
        data = doc.ifc.surface_definition(guid)
        data["surface"]["holes"] = [{"u": 0.0, "v": 0.0, "r": 1.5, "h": 3.2, "held": True}]
        self.assertEqual(ps.validate(data), [])
        bim.set_param_surface(doc, guid, data)
        on = ps.Surface(doc.ifc.surface_definition(guid))
        verts, faces = on.mesh()
        self.assertLess(len(faces), plain - 20)                                   # (its middle left open)
        o, x, y, _n = ps.outline_frame(np.asarray(data["curves"][0]["points"], float))
        uv = (verts - o) @ np.stack((x, y)).T
        d = np.hypot(uv[:, 0], uv[:, 1])
        ring = np.abs(d - 1.5) < 1e-6
        self.assertGreater(int(ring.sum()), 8)                                    # (points on the ring itself)
        self.assertTrue(np.allclose(verts[ring, 2], 3.2))                         # (held at its height)
        mids = np.array([verts[f].mean(axis=0) for f in faces])
        md = np.hypot(*((mids - o) @ np.stack((x, y)).T).T)
        self.assertGreater(md.min(), 1.0)                                        # (nothing in its middle)
        free = dict(data["surface"]["holes"][0], held=False, h=0.0)               # (a free ring: as the dome is)
        data["surface"]["holes"] = [free]
        bim.set_param_surface(doc, guid, data)
        rows = ps.Surface(doc.ifc.surface_definition(guid)).rows
        uv = (rows.reshape(-1, 3) - o) @ np.stack((x, y)).T
        ring = np.abs(np.hypot(uv[:, 0], uv[:, 1]) - 1.5) < 1e-6
        zr = rows.reshape(-1, 3)[ring, 2]
        self.assertAlmostEqual(zr.max(), zr.min(), places=6)                      # (rigid: one height)
        self.assertGreater(zr.max(), 1.5)                                         # (lifted with the shell)
        mid = rows.shape[0] // 2
        self.assertGreater(rows[mid, mid // 2, 2], 1.0)                           # (a dome, not a cone)
        data["surface"]["holes"] = [{"u": 0.0, "v": 0.0, "r": -1, "h": 0}]
        self.assertTrue(ps.validate(data))


class Window(unittest.TestCase):
    def test_dialog(self):
        from PySide6 import QtWidgets
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        from arqbim.ui.organic_dialog import OrganicDialog
        dlg = OrganicDialog(None)
        self.assertFalse(dlg.on_chosen.isEnabled())
        self.assertTrue(dlg.on_measures.isChecked())
        dlg.shape.setCurrentIndex(1)                                               # (a circle: rings)
        self.assertEqual(dlg.grid.currentData(), "aneis")
        dlg.behaviour.setCurrentIndex(2)
        v = dlg.values()
        self.assertEqual((v["measures"], v["shape"], v["behaviour"]), (True, "circulo", "membrana"))
        out = os.environ.get("ARQ_SHOT")
        if out:
            dlg.show()
            app.processEvents()
            dlg.grab().save(out)
        dlg.close()
        dlg.deleteLater()
        chosen = OrganicDialog("o desenho «Polígono»")
        self.assertTrue(chosen.on_chosen.isChecked())
        self.assertFalse(chosen.measures.isEnabled())
        chosen.close()
        chosen.deleteLater()
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
