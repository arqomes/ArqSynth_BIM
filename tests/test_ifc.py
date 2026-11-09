"""IFC layer tests (no window):  .venv\\Scripts\\python -m unittest discover -s tests"""

import dataclasses
import math
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# the geometry cache of the files the tests save goes to a temporary folder, not the user's
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

import ifcopenshell  # noqa: E402
import ifcopenshell.util.element as ue  # noqa: E402

from arqbim.core import sketch_geometry as sg  # noqa: E402
from arqbim.core.classify import upright_box  # noqa: E402
from arqbim.core.transform import rotation_about_z, translation  # noqa: E402
from arqbim.core.walls import find_joint, offset_axis  # noqa: E402
from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim, geomcache, schedules, sheets  # noqa: E402
from arqbim.model.document import (  # noqa: E402
    AddObject, Document, IfcCommand, ReplaceMesh, SketchObject, read_file, read_preview, sidecar_path,
)

I4 = np.eye(4)


def box_object(doc, origin, du, dv, height, u=(1, 0, 0), v=(0, 1, 0)):
    m = sg.rectangle_matrix(np.array(origin, float), np.array(u, float), np.array(v, float))
    mesh = sg.rectangle_mesh(du, dv)
    sg.push_pull(mesh, 0, m, height)
    obj = SketchObject("Esboço", m, mesh)
    doc.execute(AddObject(obj))
    return obj


def bounds(doc, guid):
    v = doc.get(guid).mesh.verts
    return v.min(axis=0), v.max(axis=0)


class UprightBox(unittest.TestCase):
    def test_box_on_ground(self):
        doc = Document()
        b = upright_box(box_object(doc, (1, 2, 0), 4.5, 0.2, 2.8))
        self.assertAlmostEqual(b.length, 4.5)
        self.assertAlmostEqual(b.width, 0.2)
        self.assertAlmostEqual(b.height, 2.8)
        self.assertTrue(np.allclose(b.base, (1, 2, 0)))

    def test_long_side_along_y(self):
        doc = Document()
        b = upright_box(box_object(doc, (0, 0, 0), 0.2, 5.0, 3.0))
        self.assertAlmostEqual(b.length, 5.0)
        self.assertTrue(np.allclose(np.abs(b.x_dir), (0, 1, 0)))

    def test_box_pulled_from_a_wall_face(self):
        # rectangle drawn on a vertical plane, pulled horizontally: still an upright box
        doc = Document()
        b = upright_box(box_object(doc, (0, 0, 0), 2.0, 3.0, 0.15, u=(1, 0, 0), v=(0, 0, 1)))
        self.assertAlmostEqual(b.height, 3.0)
        self.assertAlmostEqual(b.length, 2.0)
        self.assertAlmostEqual(b.width, 0.15)

    def test_not_a_box(self):
        doc = Document()
        flat = SketchObject("f", I4, sg.rectangle_mesh(1, 1))
        self.assertIsNone(upright_box(flat))
        obj = box_object(doc, (0, 0, 0), 3.2, 4.5, 2.8)
        front = next(fi for fi in range(6) if np.allclose(obj.mesh.face_normal(fi), (0, -1, 0)))
        sg.imprint_polygon(obj.mesh, front, [(1, 0, 1), (2, 0, 1), (2, 0, 2), (1, 0, 2)])
        sg.push_pull(obj.mesh, front, I4, 1.0)  # balcony
        self.assertIsNone(upright_box(obj))


class Classify(unittest.TestCase):
    def setUp(self):
        self.doc = Document()

    def test_wall(self):
        obj = box_object(self.doc, (1, 2, 0), 4.5, 0.2, 2.8)
        res = bim.classify(self.doc, [obj.id], catalog.BY_KEY["parede_alv_20"])
        self.assertEqual(len(res.guids), 1)
        self.assertIsNone(self.doc.get(obj.id))                       # the sketch became the wall
        wall = self.doc.ifc.by_guid(res.guids[0])
        self.assertEqual(wall.is_a(), "IfcWall")
        self.assertEqual(ue.get_type(wall).Name, "Parede alvenaria 20 cm")
        usage = ue.get_material(wall, should_skip_usage=False)
        self.assertEqual(usage.is_a(), "IfcMaterialLayerSetUsage")
        self.assertEqual([l.Material.Name for l in usage.ForLayerSet.MaterialLayers],
                         ["Reboco", "Bloco cerâmico", "Reboco"])
        self.assertAlmostEqual(sum(l.LayerThickness for l in usage.ForLayerSet.MaterialLayers), 200.0)
        lo, hi = bounds(self.doc, res.guids[0])
        self.assertTrue(np.allclose(lo, (1, 2, 0), atol=1e-6) and np.allclose(hi, (5.5, 2.2, 2.8), atol=1e-6))
        self.assertEqual(ue.get_container(wall).Name, "Térreo")
        self.assertAlmostEqual(ue.get_psets(wall)["Qto_WallBaseQuantities"]["Length"], 4500.0)
        info = self.doc.ifc.describe(res.guids[0])                    # what the properties panel shows
        self.assertEqual([n for n, _ in info["layers"]], ["Reboco", "Bloco cerâmico", "Reboco"])
        self.assertAlmostEqual(sum(t for _, t in info["layers"]), 0.20)

    def test_column_profile_is_described(self):
        obj = box_object(self.doc, (0, 0, 0), 0.3, 0.3, 2.8)
        guid = bim.classify(self.doc, [obj.id], catalog.BY_KEY["pilar_30"]).guids[0]
        name, x, y = self.doc.ifc.describe(guid)["profile"]
        self.assertEqual(name, "Concreto")
        self.assertAlmostEqual(x, 0.3)
        self.assertAlmostEqual(y, 0.3)

    def test_wall_thickness_comes_from_the_type(self):
        obj = box_object(self.doc, (0, 0, 0), 4.0, 0.15, 3.0)
        res = bim.classify(self.doc, [obj.id], catalog.BY_KEY["parede_alv_20"])
        self.assertEqual(len(res.adjusted), 1)
        lo, hi = bounds(self.doc, res.guids[0])
        self.assertAlmostEqual(hi[1] - lo[1], 0.20)                     # 20 cm, centred on the 15 cm volume
        self.assertAlmostEqual((hi[1] + lo[1]) / 2, 0.075)

    def test_slab_keeps_its_top(self):
        obj = box_object(self.doc, (0, 0, 2.88), 4.0, 3.0, 0.12)
        res = bim.classify(self.doc, [obj.id], catalog.BY_KEY["laje_12"])
        slab = self.doc.ifc.by_guid(res.guids[0])
        self.assertEqual(slab.is_a(), "IfcSlab")
        lo, hi = bounds(self.doc, res.guids[0])
        self.assertTrue(np.allclose(lo, (0, 0, 2.88), atol=1e-6) and np.allclose(hi, (4, 3, 3.0), atol=1e-6))

    def test_column_centred(self):
        obj = box_object(self.doc, (5, 5, 0), 0.3, 0.3, 2.8)
        res = bim.classify(self.doc, [obj.id], catalog.BY_KEY["pilar_30"])
        col = self.doc.ifc.by_guid(res.guids[0])
        self.assertEqual(ue.get_material(col, should_skip_usage=False).is_a(), "IfcMaterialProfileSetUsage")
        lo, hi = bounds(self.doc, res.guids[0])
        self.assertTrue(np.allclose(lo, (5, 5, 0), atol=1e-6) and np.allclose(hi, (5.3, 5.3, 2.8), atol=1e-6))

    def test_refused_and_type_reused(self):
        flat = SketchObject("f", I4, sg.rectangle_mesh(1, 1))
        self.doc.execute(AddObject(flat))
        a = box_object(self.doc, (0, 0, 0), 3, 0.2, 2.8)
        b = box_object(self.doc, (0, 3, 0), 3, 0.2, 2.8)
        res = bim.classify(self.doc, [flat.id, a.id, b.id], catalog.BY_KEY["parede_alv_20"])
        self.assertEqual((len(res.guids), len(res.refused)), (2, 1))
        self.assertEqual(len(self.doc.ifc.file.by_type("IfcWallType")), 1)
        names = sorted(self.doc.ifc.by_guid(g).Name for g in res.guids)
        self.assertEqual(names, ["Parede 1", "Parede 2"])

    def test_undo_redo_mixed_with_sketch_commands(self):
        doc = self.doc
        obj = box_object(doc, (0, 0, 0), 4, 0.2, 2.8)                   # sketch command
        guid = bim.classify(doc, [obj.id], catalog.BY_KEY["parede_alv_20"]).guids[0]   # IFC command
        other = box_object(doc, (0, 5, 0), 1, 1, 1)                     # sketch command
        before = other.mesh.copy()
        after = before.copy()
        sg.push_pull(after, 0, other.matrix, 0.5)
        doc.execute(ReplaceMesh(other.id, before, after))              # sketch command
        bim.delete(doc, [guid])                                         # IFC command
        self.assertEqual(doc.ifc.count("IfcWall"), 0)
        doc.undo()                                                      # wall back
        self.assertEqual(doc.ifc.count("IfcWall"), 1)
        self.assertIsNotNone(doc.get(guid))
        doc.undo()
        doc.undo()                                                      # sketch commands
        doc.undo()                                                      # classify undone: sketch back
        self.assertEqual(doc.ifc.count("IfcWall"), 0)
        self.assertIsNotNone(doc.get(obj.id))
        for _ in range(4):
            doc.redo()
        self.assertEqual(doc.ifc.count("IfcWall"), 0)                   # deleted again
        doc.undo()
        self.assertEqual(doc.ifc.by_guid(guid).is_a(), "IfcWall")       # same GlobalId


class DoorsAndWindows(unittest.TestCase):
    def setUp(self):
        self.doc = Document()
        obj = box_object(self.doc, (0, 0, 0), 4.5, 0.2, 2.8)
        self.wall = bim.classify(self.doc, [obj.id], catalog.BY_KEY["parede_alv_20"]).guids[0]
        self.frame = bim.wall_frame(self.doc, self.wall)
        self.vol = self.doc.get(self.wall).mesh.volume()

    def wall_volume(self):
        return self.doc.get(self.wall).mesh.volume()

    def test_wall_frame(self):
        f = self.frame
        self.assertAlmostEqual(f.length, 4.5)
        self.assertAlmostEqual(f.thickness, 0.2)
        self.assertAlmostEqual(f.height, 2.8)

    def test_positions(self):
        from arqbim.core import openings as op
        f = self.frame
        s, centred = op.s_from_cursor(f, f.to_world((2.3, f.y0, 1.0)), 0.8)
        self.assertTrue(centred)
        self.assertAlmostEqual(s, (4.5 - 0.8) / 2)                      # snapped to the wall centre
        s, centred = op.s_from_cursor(f, f.to_world((1.004, f.y0, 1.0)), 0.8)
        self.assertFalse(centred)
        self.assertAlmostEqual(s, 0.60)                                 # centred on cursor, whole cm
        self.assertAlmostEqual(op.s_from_typed(f, 0.5, 1.2, near_start=False), 4.5 - 0.5 - 1.2)
        self.assertAlmostEqual(op.s_from_typed(f, 0.0, 1.2, near_start=True), op.EDGE_CLEARANCE)
        self.assertFalse(op.fits(f, 0.9, 2.9, 0.0))                     # door taller than the wall

    def test_snaps(self):
        """(0.409) A wall 4,5 m long crossed by a wall whose faces are 2,0 and 2,2 m along it: two rooms' sides,
        0–2,0 and 2,2–4,5. An 80 cm door snaps to each one's middle and to a jamb 10 / 20 cm from the wall across
        (and from the wall's ends); elsewhere it is free, to the cm; never into the wall across."""
        from arqbim.core import openings as op
        f, w = self.frame, 0.8
        faces = [f.x0 + 2.0, f.x0 + 2.2]

        def at(x):
            return op.snap_s(f, f.to_world((f.x0 + x, f.y0, 1.0)), w, faces)

        s, what = at(1.03)                                      # (the middle of 0–2,0: s = 0,60)
        self.assertEqual(what, "middle")
        self.assertAlmostEqual(s - f.x0, 0.60)
        s, what = at(2.2 + 0.2 + 0.4 - 0.03)                    # (a jamb 0,20 from the wall across, 3 cm off)
        self.assertEqual(what, 0.20)
        self.assertAlmostEqual(s - f.x0, 2.4)
        s, what = at(2.0 - 0.1 - 0.4 + 0.02)                    # (its right jamb 0,10 from the wall across)
        self.assertEqual(what, 0.10)
        self.assertAlmostEqual(s - f.x0 + w, 1.9)
        s, what = at(3.6)                                       # (s 3,20: the middle of 2,2–4,5 is 2,95, the jambs
        self.assertEqual(what, "")                              #  0,20 / 0,10 from the end 3,50 / 3,60 — free)
        self.assertAlmostEqual(s - f.x0, 3.2, places=6)
        s, what = at(4.5 - 0.1 - 0.4 + 0.01)                    # (0,10 from the wall's end)
        self.assertEqual(what, 0.10)
        self.assertAlmostEqual(s - f.x0, 3.6)
        self.assertEqual(at(2.1)[1], "")                        # (over the wall across: no snap puts it into it)
        s, what = op.snap_s(f, f.to_world((f.x0 + 2.3, f.y0, 1.0)), w)     # (no wall across: the wall's centre)
        self.assertEqual(what, "centre")
        self.assertAlmostEqual(s - f.x0, (4.5 - w) / 2)

    def test_door_cuts_the_wall(self):
        spec = catalog.OPENING_BY_KEY["porta_80"]
        door = bim.add_opening(self.doc, self.wall, spec, self.frame, 1.0, -1)
        e = self.doc.ifc.by_guid(door)
        self.assertEqual(e.is_a(), "IfcDoor")
        self.assertEqual(ue.get_type(e).Name, "Porta 80×210")
        self.assertEqual(self.doc.ifc.host_wall(door), self.wall)
        self.assertEqual(self.doc.ifc.count("IfcOpeningElement"), 1)
        self.assertAlmostEqual(self.wall_volume(), self.vol - 0.8 * 2.1 * 0.2, places=6)
        lo, hi = bounds(self.doc, door)
        self.assertTrue(abs(lo[0] - 0.95) < 1e-6 and abs(hi[0] - 1.85) < 1e-6, (lo, hi))   # 80 cm + casings 5 cm
        self.assertAlmostEqual(lo[2], 0.0)
        self.assertEqual(self.doc.ifc.validate(express_rules=True), [])

    def test_window_from_the_other_side(self):
        spec = catalog.OPENING_BY_KEY["janela_120"]
        win = bim.add_opening(self.doc, self.wall, spec, self.frame, 2.0, +1)
        lo, hi = bounds(self.doc, win)
        self.assertTrue(np.allclose((lo[0], hi[0]), (2.0, 3.2), atol=0.03), (lo, hi))
        self.assertTrue(np.allclose((lo[2], hi[2]), (1.0, 2.2), atol=0.03), (lo, hi))
        self.assertTrue(0.0 <= lo[1] and abs(hi[1] - 0.23) < 1e-6, (lo, hi))   # inside the wall thickness, its
        #                                                                       peitoril 3 cm out of the face clicked (0.290)
        self.assertAlmostEqual(self.wall_volume(), self.vol - 1.2 * 1.2 * 0.2, places=6)

    def test_undo_redo_and_delete(self):
        door = bim.add_opening(self.doc, self.wall, catalog.OPENING_BY_KEY["porta_80"], self.frame, 0.5, -1)
        win = bim.add_opening(self.doc, self.wall, catalog.OPENING_BY_KEY["janela_120"], self.frame, 2.5, -1)
        both = self.vol - 0.8 * 2.1 * 0.2 - 1.2 * 1.2 * 0.2
        self.assertAlmostEqual(self.wall_volume(), both, places=6)
        self.doc.undo()
        self.assertIsNone(self.doc.get(win))
        self.assertAlmostEqual(self.wall_volume(), self.vol - 0.8 * 2.1 * 0.2, places=6)
        self.doc.redo()
        self.assertAlmostEqual(self.wall_volume(), both, places=6)
        bim.delete(self.doc, [door])                                    # the opening closes again
        self.assertEqual(self.doc.ifc.count("IfcOpeningElement"), 1)
        self.assertAlmostEqual(self.wall_volume(), self.vol - 1.2 * 1.2 * 0.2, places=6)
        self.doc.undo()
        self.assertAlmostEqual(self.wall_volume(), both, places=6)
        bim.delete(self.doc, [self.wall])                               # wall takes its door and window
        self.assertEqual([self.doc.ifc.count(c) for c in ("IfcWall", "IfcDoor", "IfcWindow", "IfcOpeningElement")],
                         [0, 0, 0, 0])
        self.doc.undo()
        self.assertEqual([self.doc.ifc.count(c) for c in ("IfcWall", "IfcDoor", "IfcWindow", "IfcOpeningElement")],
                         [1, 1, 1, 2])
        self.assertEqual(self.doc.ifc.validate(express_rules=True), [])

    def test_saved_and_reopened(self):
        door = bim.add_opening(self.doc, self.wall, catalog.OPENING_BY_KEY["porta_90"], self.frame, 0.5, -1)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.ifc")
            self.doc.save(path)
            doc2 = Document()
            doc2.open(path)
            self.assertEqual(doc2.ifc.host_wall(door), self.wall)
            self.assertAlmostEqual(doc2.get(self.wall).mesh.volume(), self.vol - 0.9 * 2.1 * 0.2, places=6)
            self.assertEqual(doc2.ifc.describe(door)["size"], (0.9, 2.1))


class DirectWallsAndSlabs(unittest.TestCase):
    """Wall tool (point by point, clean corners) and Slab tool, without sketches."""

    def draw_closed_rectangle(self, doc, spec):
        pts = [np.array(p, float) for p in ((0, 0, 0), (6, 0, 0), (6, 4, 0), (0, 4, 0))]
        guids, prev, first = [], None, None
        for i in range(4):
            a, b = pts[i], pts[(i + 1) % 4]
            d = (b - a) / np.linalg.norm(b - a)
            closing = (first if i == 3 else None)
            g = bim.add_wall(doc, a, b, spec, prev=prev, first=closing)
            guids.append(g)
            prev = (g, d)
            if i == 0:
                first = (g, d)
        return guids

    def test_closed_chain_has_clean_corners(self):
        doc = Document()
        guids = self.draw_closed_rectangle(doc, catalog.BY_KEY["parede_alv_20"])
        vols = [doc.get(g).mesh.volume() for g in guids]
        self.assertAlmostEqual(sum(vols), 20 * 0.2 * 2.8, places=6)        # no overlap, no gap
        allv = np.vstack([doc.get(g).mesh.verts for g in guids])
        self.assertTrue(np.allclose(allv.min(axis=0), (-0.1, -0.1, 0)) and np.allclose(allv.max(axis=0), (6.1, 4.1, 2.8)))
        lengths = [round(doc.ifc.wall_params(g)[0], 6) for g in guids]
        self.assertEqual(lengths, [6.2, 4.0, 6.0, 3.8])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()                                                          # closing wall + first wall's extension
        self.assertAlmostEqual(doc.ifc.wall_params(guids[0])[0], 6.1)
        doc.redo()
        self.assertAlmostEqual(doc.ifc.wall_params(guids[0])[0], 6.2)

    def add_separate(self, doc, a, b, spec):
        """One wall drawn on its own, joined to the walls already there (as the Wall tool does)."""
        a, b = np.array(a, float), np.array(b, float)
        d = (b - a) / np.linalg.norm(b - a)
        axes = bim.wall_axes(doc)
        sj, ej = find_joint(a, d, axes), find_joint(b, d, axes)
        return bim.add_wall(doc, a, b, spec, start_join=sj and sj[:3], end_join=ej and ej[:3])

    def test_separate_walls_make_clean_corners(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        pts = [(0, 0, 0), (6, 0, 0), (6, 4, 0), (0, 4, 0)]
        guids = [self.add_separate(doc, pts[i], pts[(i + 1) % 4], spec) for i in range(4)]
        vols = [doc.get(g).mesh.volume() for g in guids]
        self.assertAlmostEqual(sum(vols), 20 * 0.2 * 2.8, places=6)        # no overlap, no gap
        allv = np.vstack([doc.get(g).mesh.verts for g in guids])
        self.assertTrue(np.allclose(allv.min(axis=0), (-0.1, -0.1, 0)) and np.allclose(allv.max(axis=0), (6.1, 4.1, 2.8)))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()                                                          # last wall and both extensions
        self.assertAlmostEqual(sum(doc.get(g).mesh.volume() for g in guids[:3]), (6.1 + 4.0 + 5.9) * 0.2 * 2.8, places=6)
        self.assertAlmostEqual(doc.ifc.wall_params(guids[0])[0], 6.1)       # first wall back to before

    def test_wall_axis_after_extension(self):
        doc = Document()
        a = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        self.add_separate(doc, (5, 0, 0), (5, 3, 0), catalog.BY_KEY["parede_alv_15"])
        s, e, th = doc.ifc.wall_axis(a)
        self.assertTrue(np.allclose(s, 0) and np.allclose(e, (5.075, 0, 0)))
        self.assertAlmostEqual(th, 0.2)

    def test_t_junction_butts_against_the_face(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        a = bim.add_wall(doc, (0, 0, 0), (6, 0, 0), spec)
        b = self.add_separate(doc, (3, 0, 0), (3, 4, 0), spec)
        lo, _hi = bounds(doc, b)
        self.assertAlmostEqual(lo[1], 0.1)                                   # starts at the face of A
        self.assertAlmostEqual(doc.ifc.wall_params(a)[0], 6.0)               # A unchanged

    def draw_outline(self, doc, pts, spec, reference):
        """A closed chain drawn along `pts` by `reference` (as the Wall tool does)."""
        guids, prev, first = [], None, None
        for i in range(len(pts)):
            p, q = np.array(pts[i], float), np.array(pts[(i + 1) % len(pts)], float)
            a, b = offset_axis(p, q, reference, spec.thickness)
            d = (q - p) / np.linalg.norm(q - p)
            g = bim.add_wall(doc, a, b, spec, prev=prev, first=first if i == len(pts) - 1 else None)
            guids.append(g)
            prev = (g, d)
            if i == 0:
                first = (g, d)
        return guids

    def test_outline_drawn_by_the_outside_face(self):
        # counter-clockwise along the OUTSIDE: the right face; 10 × 8 outside, exactly
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        guids = self.draw_outline(doc, [(0, 0, 0), (10, 0, 0), (10, 8, 0), (0, 8, 0)], spec, "right")
        allv = np.vstack([doc.get(g).mesh.verts for g in guids])
        self.assertTrue(np.allclose(allv.min(axis=0), (0, 0, 0)) and np.allclose(allv.max(axis=0), (10, 8, 2.8)))
        total = sum(doc.get(g).mesh.volume() for g in guids)
        self.assertAlmostEqual(total, (10 * 8 - 9.6 * 7.6) * 2.8, places=6)   # no overlap, no gap
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_outline_drawn_by_the_inside_face(self):
        # counter-clockwise along the INSIDE: the left face; the room is 4 × 3 inside
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_15"]
        guids = self.draw_outline(doc, [(0, 0, 0), (4, 0, 0), (4, 3, 0), (0, 3, 0)], spec, "left")
        allv = np.vstack([doc.get(g).mesh.verts for g in guids])
        self.assertTrue(np.allclose(allv.min(axis=0)[:2], (-0.15, -0.15)) and np.allclose(allv.max(axis=0)[:2], (4.15, 3.15)))
        total = sum(doc.get(g).mesh.volume() for g in guids)
        self.assertAlmostEqual(total, (4.3 * 3.3 - 4 * 3) * 2.8, places=6)

    def test_hexagon_has_mitre_corners(self):
        # a regular hexagon drawn by the axis: 120° corners cut in mitre, no overlap, no gap
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        r = 4.0
        pts = [(r * np.cos(np.radians(60 * k)), r * np.sin(np.radians(60 * k)), 0.0) for k in range(6)]
        guids = self.draw_outline(doc, pts, spec, "axis")
        total = sum(doc.get(g).mesh.volume() for g in guids)
        self.assertAlmostEqual(total, 6 * r * 0.2 * 2.8, places=6)               # perimeter × thickness × height
        radii = np.linalg.norm(np.vstack([doc.get(g).mesh.verts for g in guids])[:, :2], axis=1)
        apothem = r * np.cos(np.radians(30))
        self.assertAlmostEqual(radii.max(), (apothem + 0.1) / np.cos(np.radians(30)), places=6)   # outer corners
        self.assertAlmostEqual(radii.min(), (apothem - 0.1) / np.cos(np.radians(30)), places=6)   # inner corners
        lengths = [round(doc.ifc.wall_params(g)[0], 6) for g in guids]
        self.assertEqual(lengths, [r] * 6)                                       # axis lengths, corner to corner
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_wall_at_an_angle_drawn_separately(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        a = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), spec)
        d = np.array((np.cos(np.radians(60)), np.sin(np.radians(60)), 0.0))
        b = self.add_separate(doc, (5, 0, 0), np.array((5, 0, 0)) + d * 3, spec)
        self.assertNotEqual(doc.ifc.wall_cuts(a), (180.0, 0.0))                  # A's end is cut in mitre
        self.assertAlmostEqual(doc.ifc.wall_cuts(a)[1], 30.0)                    # half of the 60° turn
        self.assertAlmostEqual(doc.ifc.wall_cuts(b)[0], 180.0 - 30.0)            # the same cut, seen from B
        vol = doc.get(a).mesh.volume() + doc.get(b).mesh.volume()
        self.assertAlmostEqual(vol, (5 + 3) * 0.2 * 2.8, places=6)
        # Push/Pull of A's far end keeps the mitre at the corner
        bim.resize_wall(doc, a, at_start=0.5)
        self.assertAlmostEqual(doc.ifc.wall_cuts(a)[1], 30.0)
        sb = doc.ifc.wall_axis(b)[0]
        bim.resize_wall(doc, a, at_end=-1.0)              # the corner end moves: B goes along, the mitre stays (0.71)
        self.assertAlmostEqual(doc.ifc.wall_cuts(a)[1], 30.0)
        np.testing.assert_allclose(doc.ifc.wall_axis(b)[0], sb - (1.0, 0.0, 0.0), atol=1e-6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_t_junction_at_an_angle(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        a = bim.add_wall(doc, (0, 0, 0), (8, 0, 0), spec)
        d = np.array((np.cos(np.radians(45)), np.sin(np.radians(45)), 0.0))
        b = self.add_separate(doc, (3, 0, 0), np.array((3, 0, 0)) + d * 3, spec)
        verts = doc.get(b).mesh.verts
        self.assertAlmostEqual(verts[:, 1].min(), 0.1)                           # cut along A's face
        self.assertAlmostEqual(doc.ifc.wall_params(a)[0], 8.0)                   # A unchanged
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_extend_keeps_doors_in_place(self):
        doc = Document()
        a = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        f = bim.wall_frame(doc, a)
        door = bim.add_opening(doc, a, catalog.OPENING_BY_KEY["porta_80"], f, 2.0, -1)
        before = doc.get(door).mesh.verts.min(axis=0).copy()
        doc.execute(IfcCommand("x", lambda ifc: ifc.extend_wall(a, 0.5, 0.25), changed=[a]))
        self.assertTrue(np.allclose(doc.get(door).mesh.verts.min(axis=0), before))
        lo, hi = bounds(doc, a)
        self.assertAlmostEqual(lo[0], -0.5)
        self.assertAlmostEqual(hi[0], 5.25)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_slabs_floor_and_roof(self):
        doc = Document()
        spec = catalog.BY_KEY["laje_12"]
        floor = bim.add_slab(doc, np.array((0.0, 0.0, 0.0)), 6.0, -4.0, spec)
        roof = bim.add_slab(doc, np.array((-0.1, -0.1, 2.8)), 6.2, 4.2, spec)
        lo, hi = bounds(doc, floor)
        self.assertTrue(np.allclose(lo, (0, -4, -0.12)) and np.allclose(hi, (6, 0, 0)))  # top at the ground level
        lo, hi = bounds(doc, roof)
        self.assertTrue(np.allclose(lo, (-0.1, -0.1, 2.8)) and np.allclose(hi, (6.1, 4.1, 2.92)))  # rests on 2,80


class Structure(unittest.TestCase):
    """0.66 (Phase 5, step 1): columns and beams drawn directly — IFC, quantities, edits, types."""

    def test_columns_and_a_beam(self):
        doc = Document()
        c1 = bim.add_column(doc, np.array((0.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        bim.add_column(doc, np.array((5.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        lo, hi = bounds(doc, c1)
        self.assertTrue(np.allclose(lo, (-0.15, -0.15, 0)) and np.allclose(hi, (0.15, 0.15, 2.8)), (lo, hi))
        self.assertEqual(doc.ifc.describe(c1)["kind"], "column")
        beam = bim.add_beam(doc, np.array((0.0, 0.0, 2.8)), np.array((5.0, 0.0, 2.8)), catalog.BY_KEY["viga_20x40"], 2.8)
        lo, hi = bounds(doc, beam)
        self.assertTrue(np.allclose(lo, (0, -0.1, 2.4)) and np.allclose(hi, (5, 0.1, 2.8)), (lo, hi))   # top at 2,80
        self.assertAlmostEqual(doc.get(beam).mesh.volume(), 5 * 0.2 * 0.4, places=6)
        e = doc.ifc.by_guid(beam)
        self.assertEqual((e.is_a(), ifcopenshell.util.element.get_type(e).is_a()), ("IfcBeam", "IfcBeamType"))
        info = doc.ifc.describe(beam)
        self.assertEqual(info["kind"], "beam")
        self.assertAlmostEqual(info["params"]["length"], 5.0)
        self.assertAlmostEqual(info["params"]["top"], 2.8)
        self.assertIn("Qto_BeamBaseQuantities", info["psets"])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.resize_beam(doc, beam, length=6.0)
        bim.resize_beam(doc, beam, top=3.0)
        bim.set_type(doc, beam, catalog.BY_KEY["viga_20x50"])                  # deeper: the top stays
        lo, hi = bounds(doc, beam)
        self.assertTrue(np.allclose(lo, (0, -0.1, 2.5)) and np.allclose(hi, (6, 0.1, 3.0)), (lo, hi))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        for _ in range(3):
            doc.undo()
        lo, hi = bounds(doc, beam)
        self.assertTrue(np.allclose(lo, (0, -0.1, 2.4)) and np.allclose(hi, (5, 0.1, 2.8)), (lo, hi))

    def test_a_long_sketch_box_classified_as_a_beam(self):
        doc = Document()
        obj = box_object(doc, (0, -0.1, 2.4), 4.0, 0.2, 0.4)
        res = bim.classify(doc, [obj.id], catalog.BY_KEY["viga_20x40"])
        self.assertEqual(len(res.guids), 1)
        lo, hi = bounds(doc, res.guids[0])
        self.assertTrue(np.allclose(lo, (0, -0.1, 2.4)) and np.allclose(hi, (4, 0.1, 2.8)), (lo, hi))
        self.assertEqual(doc.ifc.by_guid(res.guids[0]).is_a(), "IfcBeam")


class Footings(unittest.TestCase):
    """0.68 (Phase 5, step 3): pad footings under columns, strip footings under walls — IFC, edits, types."""

    def test_a_pad_under_a_column(self):
        doc = Document()
        col = bim.add_column(doc, np.array((2.0, 1.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        pad = catalog.BY_KEY["sapata_80"]
        place = bim.footing_place(doc, col, pad)
        np.testing.assert_allclose(place[0], (2.0, 1.0), atol=1e-9)
        guid = bim.add_footing(doc, place, pad)
        lo, hi = bounds(doc, guid)
        self.assertTrue(np.allclose(lo, (1.6, 0.6, -0.4)) and np.allclose(hi, (2.4, 1.4, 0.0)), (lo, hi))
        self.assertAlmostEqual(doc.get(guid).mesh.volume(), 0.8 * 0.8 * 0.4, places=6)
        e = doc.ifc.by_guid(guid)
        self.assertEqual((e.is_a(), ifcopenshell.util.element.get_predefined_type(e), ifcopenshell.util.element.get_type(e).is_a()),
                         ("IfcFooting", "PAD_FOOTING", "IfcFootingType"))
        usage = ifcopenshell.util.element.get_material(e, should_skip_usage=False)
        self.assertEqual(usage.LayerSetDirection, "AXIS3")
        info = doc.ifc.describe(guid)
        self.assertEqual((info["kind"], info["params"]["strip"]), ("footing", False))
        self.assertAlmostEqual(info["params"]["top"], 0.0)
        self.assertAlmostEqual(info["psets"]["Qto_FootingBaseQuantities"]["GrossVolume"], 0.256)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.set_type(doc, guid, catalog.BY_KEY["sapata_120"])           # bigger and deeper: centre and top stay
        lo, hi = bounds(doc, guid)
        self.assertTrue(np.allclose(lo, (1.4, 0.4, -0.5)) and np.allclose(hi, (2.6, 1.6, 0.0)), (lo, hi))
        bim.resize_footing(doc, guid, top=-0.2)
        self.assertAlmostEqual(bounds(doc, guid)[0][2], -0.7)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        doc.undo()
        lo, hi = bounds(doc, guid)
        self.assertTrue(np.allclose(lo, (1.6, 0.6, -0.4)) and np.allclose(hi, (2.4, 1.4, 0.0)), (lo, hi))

    def test_a_strip_under_a_wall(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((0.0, 4.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        strip = catalog.BY_KEY["sapata_corrida_50"]
        guid = bim.add_footing(doc, bim.footing_place(doc, wall, strip), strip)
        lo, hi = bounds(doc, guid)
        self.assertTrue(np.allclose(lo, (-0.25, 0, -0.3)) and np.allclose(hi, (0.25, 4, 0)), (lo, hi))
        e = doc.ifc.by_guid(guid)
        self.assertEqual(ifcopenshell.util.element.get_predefined_type(e), "STRIP_FOOTING")
        self.assertTrue(doc.ifc.describe(guid)["params"]["strip"])
        bim.resize_footing(doc, guid, length=5.0)                        # its start stays
        lo, hi = bounds(doc, guid)
        self.assertTrue(np.allclose(lo, (-0.25, 0, -0.3)) and np.allclose(hi, (0.25, 5, 0)), (lo, hi))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        self.assertIsNone(bim.footing_place(doc, bim.add_slab(doc, np.array((1.0, 1.0, 0.0)), 2.0, 2.0,
                                                              catalog.BY_KEY["laje_12"]),
                                            strip))                      # (not under a slab)

    def test_a_sketch_block_classified_as_a_footing(self):
        doc = Document()
        obj = box_object(doc, (0, 0, -0.5), 1.0, 1.0, 0.5)
        res = bim.classify(doc, [obj.id], catalog.BY_KEY["sapata_80"])
        self.assertEqual(len(res.guids), 1)
        self.assertEqual(len(res.adjusted), 1)                           # 0,50 deep → the type's 0,40
        lo, hi = bounds(doc, res.guids[0])
        self.assertTrue(np.allclose(lo, (0, 0, -0.4)) and np.allclose(hi, (1, 1, 0)), (lo, hi))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class Services(unittest.TestCase):
    """0.69 (Phase 5, step 4): pipes and ducts drawn like beams — IFC, quantities, edits, types."""

    def test_a_pipe(self):
        doc = Document()
        pipe = bim.add_segment(doc, np.array((0.0, 0.0, 0.3)), np.array((4.0, 0.0, 0.3)), catalog.BY_KEY["tubo_50"], 0.3)
        lo, hi = bounds(doc, pipe)
        self.assertTrue(np.allclose(lo, (0, -0.025, 0.275), atol=1e-3) and np.allclose(hi, (4, 0.025, 0.325), atol=1e-3),
                        (lo, hi))                                        # centred on its axis, at 0,30
        self.assertAlmostEqual(doc.get(pipe).mesh.volume(), math.pi * 0.025 ** 2 * 4, delta=0.02 * math.pi * 0.025 ** 2 * 4)
        e = doc.ifc.by_guid(pipe)
        type_ = ifcopenshell.util.element.get_type(e)
        self.assertEqual((e.is_a(), type_.is_a(), type_.PredefinedType), ("IfcPipeSegment", "IfcPipeSegmentType",
                                                                         "RIGIDSEGMENT"))
        psets = ifcopenshell.util.element.get_psets(type_)
        self.assertAlmostEqual(psets["Pset_PipeSegmentTypeCommon"]["NominalDiameter"] * doc.ifc.unit_scale, 0.05)
        info = doc.ifc.describe(pipe)
        self.assertEqual(info["kind"], "pipe")
        self.assertAlmostEqual(info["params"]["length"], 4.0)
        self.assertAlmostEqual(info["params"]["z"], 0.3)
        self.assertIsNone(info["profile"][2])                            # round: its diameter only
        self.assertAlmostEqual(info["profile"][1], 0.05)
        q = info["psets"]["Qto_PipeSegmentBaseQuantities"]
        self.assertAlmostEqual(q["GrossCrossSectionArea"], math.pi * 0.025 ** 2)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.resize_segment(doc, pipe, length=5.0)
        bim.resize_segment(doc, pipe, z=-0.5)                            # (under the floor)
        bim.set_type(doc, pipe, catalog.BY_KEY["tubo_100"])              # thicker: the axis stays
        lo, hi = bounds(doc, pipe)
        self.assertTrue(np.allclose(lo, (0, -0.05, -0.55), atol=1e-3) and np.allclose(hi, (5, 0.05, -0.45), atol=1e-3),
                        (lo, hi))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        for _ in range(3):
            doc.undo()
        lo, hi = bounds(doc, pipe)
        self.assertTrue(np.allclose(hi, (4, 0.025, 0.325), atol=1e-3), hi)

    def test_a_duct(self):
        doc = Document()
        duct = bim.add_segment(doc, np.array((0.0, 0.0, 2.5)), np.array((0.0, 3.0, 2.5)),
                               catalog.BY_KEY["conduta_30x20"], 2.5)
        lo, hi = bounds(doc, duct)
        self.assertTrue(np.allclose(lo, (-0.15, 0, 2.4)) and np.allclose(hi, (0.15, 3, 2.6)), (lo, hi))
        self.assertAlmostEqual(doc.get(duct).mesh.volume(), 0.3 * 0.2 * 3, places=6)
        e = doc.ifc.by_guid(duct)
        self.assertEqual((e.is_a(), ifcopenshell.util.element.get_type(e).is_a()), ("IfcDuctSegment", "IfcDuctSegmentType"))
        common = ifcopenshell.util.element.get_psets(ifcopenshell.util.element.get_type(e))["Pset_DuctSegmentTypeCommon"]
        self.assertEqual(common["Shape"], "RECTANGULAR")
        self.assertEqual(doc.ifc.describe(duct)["kind"], "duct")
        self.assertEqual(doc.get(duct).name, "Conduta 1")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class BrandRename(unittest.TestCase):
    """0.77: the program is ArqSynth BIM — a project saved by ArqBIM (its "ArqBIM_Parametros", its ".arqbim")
    opens and edits as before; saved again, it takes the new names. The old work folder is renamed once."""

    def test_an_arqbim_project_opens(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        doc.execute(AddObject(SketchObject("Esboço velho", np.eye(4), sg.rectangle_mesh(1.0, 1.0)), "Retângulo"))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "antigo.ifc")
            doc.save(path)
            self.assertTrue(sidecar_path(path).endswith(".arqsynthbim"))
            # as ArqBIM 0.76 wrote it: the old property set's name, the old side file
            with open(path, encoding="utf-8") as f:
                text = f.read()
            self.assertIn("ArqSynth_Parametros", text)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text.replace("ArqSynth_Parametros", "ArqBIM_Parametros"))
            os.replace(sidecar_path(path), os.path.join(tmp, "antigo.arqbim"))
            geomcache.forget(path)
            old = Document()
            old.open(path)
            self.assertEqual(old.ifc.kind_of(wall), "wall")                  # still editable
            self.assertEqual([o.name for o in old.sketches()], ["Esboço velho"])
            bim.resize_wall(old, wall, height=3.0)
            old.save(path)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            self.assertIn("ArqSynth_Parametros", text)
            self.assertNotIn("ArqBIM_Parametros", text)
            self.assertTrue(os.path.exists(os.path.join(tmp, "antigo.arqsynthbim")))
            geomcache.forget(path)

    def test_the_old_folder_is_renamed_once(self):
        from arqbim import paths
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "ArqBIM", "partilha"))
            with open(os.path.join(tmp, "ArqBIM", "partilha", "x.txt"), "w") as f:
                f.write("kept")
            folder = paths.user_dir(tmp, "partilha")
            self.assertEqual(folder, os.path.join(tmp, "ArqSynth BIM", "partilha"))
            with open(os.path.join(folder, "x.txt")) as f:
                self.assertEqual(f.read(), "kept")
            self.assertFalse(os.path.exists(os.path.join(tmp, "ArqBIM")))
            self.assertEqual(paths.user_dir(tmp), os.path.join(tmp, "ArqSynth BIM"))


class Connectors(unittest.TestCase):
    """0.74 (the owner: "the ducts and pipes have no connectors"): ports at both ends, a bend where a run turns,
    connected port to port."""

    def connections(self, doc, guid):
        return [doc.ifc.connected(p) is not None for p in doc.ifc.ports(guid)]

    def test_a_pipe_run_with_a_bend(self):
        doc = Document()
        spec = catalog.BY_KEY["tubo_50"]
        a = bim.add_segment(doc, np.array((0.0, 0.0, 0.3)), np.array((4.0, 0.0, 0.3)), spec, 0.3)
        self.assertEqual(len(doc.ifc.ports(a)), 2)
        b = bim.add_segment(doc, np.array((4.0, 0.0, 0.3)), np.array((4.0, 3.0, 0.3)), spec, 0.3, after=a)
        bends = doc.ifc.file.by_type("IfcPipeFitting")
        self.assertEqual(len(bends), 1)
        self.assertEqual(ifcopenshell.util.element.get_predefined_type(bends[0]), "BEND")
        sa, ea, _z = doc.ifc.segment_params(a)
        sb, eb, _z = doc.ifc.segment_params(b)
        np.testing.assert_allclose(ea, (3.95, 0.0, 0.3), atol=1e-6)        # stops where the bend starts (R = Ø)
        np.testing.assert_allclose(sb, (4.0, 0.05, 0.3), atol=1e-6)
        self.assertEqual(self.connections(doc, a), [False, True])
        self.assertEqual(self.connections(doc, b), [True, False])
        bend = doc.get(bends[0].GlobalId)
        self.assertAlmostEqual(bend.mesh.volume(), math.pi * 0.025 ** 2 * 0.05 * math.pi / 2, delta=5e-6)  # (facets)
        lo, hi = (np.array(v) for v in bend.mesh.bounds())
        self.assertTrue(np.allclose(lo[:2], (3.95, -0.025), atol=2e-3) and np.allclose(hi[:2], (4.025, 0.05), atol=2e-3),
                        (lo, hi))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        c = bim.add_segment(doc, np.array((4.0, 3.0, 0.3)), np.array((4.0, 5.0, 0.3)), spec, 0.3)    # found by its end
        self.assertEqual(doc.ifc.count("IfcPipeFitting"), 1)                                         # in line: no bend
        self.assertEqual(self.connections(doc, b), [True, True])
        self.assertEqual(self.connections(doc, c), [True, False])
        bim.delete(doc, [c])
        self.assertEqual(self.connections(doc, b), [True, False])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        for _ in range(3):
            doc.undo()
        np.testing.assert_allclose(doc.ifc.segment_params(a)[1], (4.0, 0.0, 0.3), atol=1e-6)
        self.assertEqual(doc.ifc.count("IfcPipeFitting"), 0)

    def test_a_joined_run_moves_together(self):
        doc = Document()
        spec = catalog.BY_KEY["tubo_50"]
        a = bim.add_segment(doc, np.array((0.0, 0.0, 0.3)), np.array((4.0, 0.0, 0.3)), spec, 0.3)
        b = bim.add_segment(doc, np.array((4.0, 0.0, 0.3)), np.array((4.0, 3.0, 0.3)), spec, 0.3, after=a)
        bend = doc.ifc.file.by_type("IfcPipeFitting")[0].GlobalId
        bim.resize_segment(doc, a, z=0.6)                                   # up: the whole run goes along
        self.assertAlmostEqual(doc.ifc.segment_params(b)[2], 0.6)
        self.assertAlmostEqual(float(np.mean(doc.get(bend).mesh.bounds(), axis=0)[2]), 0.6, places=6)
        bim.resize_segment(doc, a, length=2.95)                             # 1 m shorter: the bend and B follow
        np.testing.assert_allclose(doc.ifc.segment_params(b)[0], (3.0, 0.05, 0.6), atol=1e-6)
        self.assertEqual(self.connections(doc, a), [False, True])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_a_duct_turning_right(self):
        doc = Document()
        spec = catalog.BY_KEY["conduta_30x20"]
        a = bim.add_segment(doc, np.array((0.0, 0.0, 2.5)), np.array((0.0, 4.0, 2.5)), spec, 2.5)
        b = bim.add_segment(doc, np.array((0.0, 4.0, 2.5)), np.array((3.0, 4.0, 2.5)), spec, 2.5, after=a)
        bend = doc.get(doc.ifc.file.by_type("IfcDuctFitting")[0].GlobalId)
        self.assertAlmostEqual(bend.mesh.volume(), 0.3 * 0.2 * 0.3 * math.pi / 2, delta=0.002)   # Pappus: area × R × θ
        lo, hi = (np.array(v) for v in bend.mesh.bounds())
        self.assertTrue(np.allclose(lo, (-0.15, 3.7, 2.4), atol=0.01) and np.allclose(hi, (0.3, 4.15, 2.6), atol=0.01),
                        (lo, hi))
        np.testing.assert_allclose(doc.ifc.segment_params(b)[0], (0.3, 4.0, 2.5), atol=1e-6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class Certification(unittest.TestCase):
    """0.70 (Phase 5, step 5): the checks before certification — a model made by the program passes them all
    once its site is placed on Earth; the header names the program; the report page."""

    def test_checks_header_and_site(self):
        from arqbim.ifc import certify
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        frame = bim.wall_frame(doc, wall)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, frame.x0 + 1.0, 1)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["janela_120"], frame, frame.x0 + 3.0, 1)
        col = bim.add_column(doc, np.array((7.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        bim.add_footing(doc, bim.footing_place(doc, col, catalog.BY_KEY["sapata_80"]), catalog.BY_KEY["sapata_80"])
        bim.add_segment(doc, np.array((0.0, 1.0, 0.3)), np.array((3.0, 1.0, 0.3)), catalog.BY_KEY["tubo_50"], 0.3)
        _title, checks = certify.check(doc.ifc)
        failing = [c.name for c in checks if not c.status]
        self.assertEqual(len(failing), 1, [(c.name, c.failures[:2]) for c in checks if not c.status])
        self.assertEqual(checks[-1].usage, "optional")                     # only georeferencing, recommended
        bim.set_site_location(doc, 38.7223, -9.1393, 50.0)
        lat, lon, elevation = doc.ifc.site_location()
        self.assertAlmostEqual(lat, 38.7223, places=6)
        self.assertAlmostEqual(lon, -9.1393, places=6)
        self.assertAlmostEqual(elevation, 50.0)
        _title, checks = certify.check(doc.ifc)
        self.assertTrue(all(c.status for c in checks), [(c.name, c.failures[:2]) for c in checks if not c.status])
        page = certify.report_html(*certify.check(doc.ifc), "casa.ifc")
        self.assertIn("casa.ifc", page)
        self.assertIn(checks[0].name, page)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "certificar.ifc")
            doc.save(path)
            f = ifcopenshell.open(path)
            self.assertTrue(f.header.file_name.originating_system.startswith("ArqSynth BIM "))
            self.assertEqual(f.header.file_name.name, "certificar.ifc")
            geomcache.forget(path)
        doc.undo()
        self.assertEqual(doc.ifc.site_location(), (None, None, None))

    def test_a_foreign_element_out_of_place(self):
        import ifcopenshell.api.root
        from arqbim.ifc import certify
        doc = Document()
        stray = ifcopenshell.api.root.create_entity(doc.ifc.file, ifc_class="IfcWall", name="")
        _title, checks = certify.check(doc.ifc)
        spatial = next(c for c in checks if c.name == checks[2].name)
        self.assertFalse(spatial.status)
        self.assertEqual(spatial.failures[0][0], stray.GlobalId)


class BaseAndTop(unittest.TestCase):
    """0.73 (the owner: "base and top constraints, offsets", as Revit's): walls and columns tied to storeys."""

    def test_wall_and_column_follow_their_storeys(self):
        doc = Document()
        ground = doc.ifc.storeys()[0][0]
        first = bim.add_storey(doc, "Piso 1", 3.0)
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)),
                            catalog.BY_KEY["parede_alv_20"], storey=ground)
        c = doc.ifc.constraints(wall)
        self.assertEqual((c["base"], c["top"]), (ground, None))
        self.assertAlmostEqual(c["height"], 2.8)
        bim.set_constraints(doc, wall, top=first, top_offset=-0.2)           # up to Piso 1, 20 cm below it
        self.assertAlmostEqual(doc.ifc.wall_params(wall)[1], 2.8)
        bim.set_constraints(doc, wall, top_offset=0.0)
        self.assertAlmostEqual(doc.ifc.wall_params(wall)[1], 3.0)
        bim.set_storey_elevation(doc, first, 3.5)                            # Piso 1 goes up: the wall too
        self.assertAlmostEqual(doc.ifc.wall_params(wall)[1], 3.5)
        bim.set_constraints(doc, wall, base_offset=0.5)                      # on a 50 cm plinth, the top stays
        lo, hi = bounds(doc, wall)
        self.assertAlmostEqual(lo[2], 0.5)
        self.assertAlmostEqual(hi[2], 3.5)
        column = bim.add_column(doc, np.array((7.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8, storey=ground)
        bim.set_constraints(doc, column, base_offset=-0.5, top=first)       # from the footing up to Piso 1
        lo, hi = bounds(doc, column)
        self.assertAlmostEqual(lo[2], -0.5)
        self.assertAlmostEqual(hi[2], 3.5)
        self.assertEqual(doc.ifc.describe(column)["constraints"]["top"], first)
        bim.resize_column(doc, column, 3.8)                                  # taller by hand: the top offset follows
        self.assertAlmostEqual(doc.ifc.constraints(column)["top_offset"], -0.2)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        second = bim.add_storey(doc, "Piso 2", 6.5)
        bim.set_constraints(doc, wall, top=second)                           # up to Piso 2 …
        self.assertAlmostEqual(doc.ifc.wall_params(wall)[1], 6.0)
        bim.remove_storey(doc, second)                                       # … gone: not connected, as tall
        c = doc.ifc.constraints(wall)
        self.assertIsNone(c["top"])
        self.assertAlmostEqual(c["height"], 6.0)
        for _ in range(4):
            doc.undo()                                                       # back to before Piso 2
        bim.set_constraints(doc, column, base=first, base_offset=0.0, top=None, height=3.0)   # moved up to Piso 1
        self.assertEqual(doc.ifc.storey_of(column), first)
        self.assertAlmostEqual(bounds(doc, column)[0][2], 3.5)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class CurvedCornersIfc(unittest.TestCase):
    """0.189: corners with curved walls — a straight wall (0,0)-(4,0) and a quarter round from its end, down: joined
    by themselves (recorded), the corner exact (the straight wall's end corners are the curved one's: no gap, no
    overlap; their volumes as their plans); the straight wall thinner: made again; mirrored: still so; two curved
    walls end to end; a straight wall drawn to a curved wall's end; the IFC valid."""

    @staticmethod
    def _straight_corners(doc, guid, end):
        from arqbim.core.walls import footprint
        s, e, t = doc.ifc.wall_axis(guid)
        length = float(np.linalg.norm((e - s)[:2]))
        x = (e - s)[:2] / length
        y = np.array((-x[1], x[0]))
        pts = footprint(length, t, *doc.ifc.wall_cuts(guid))
        local = (pts[1], pts[2]) if end == "end" else (pts[0], pts[3])
        return [s[:2] + x * px + y * py for px, py in local]

    @staticmethod
    def _curved_corners(doc, guid, end):
        from arqbim.core.curved_joints import cut_ends
        centre, r, start, sweep, _h, t = doc.ifc.curved_wall_params(guid)
        (o0, i0), (o1, i1) = cut_ends(r, sweep, t, *doc.ifc.wall_cuts(guid))
        o, i = (o0, i0) if end == "start" else (o1, i1)
        at = lambda radius, a: centre[:2] + radius * np.array((math.cos(start + a), math.sin(start + a)))   # noqa: E731
        return [at(r + t / 2, o), at(r - t / 2, i)]

    def _same(self, a, b):
        self.assertTrue(any(np.allclose(a[0], q, atol=1e-6) for q in b) and
                        any(np.allclose(a[1], q, atol=1e-6) for q in b), (a, b))

    def test_straight_and_curved(self):
        from shapely.geometry import Polygon
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), spec)
        arc = bim.add_curved_wall(doc, (6.0, 0.0, 0.0), 2.0, math.pi, math.pi / 2, spec)
        self.assertEqual(doc.ifc.joined_walls([arc]), [wall])
        s, e, _t = doc.ifc.wall_axis(wall)
        self.assertGreater(e[0], 4.0)                                    # (to the exact corner, past 4 m)
        self._same(self._straight_corners(doc, wall, "end"), self._curved_corners(doc, arc, "start"))
        plan = Polygon(doc.ifc.curved_wall_band(arc)[0])
        self.assertAlmostEqual(doc.get(arc).mesh.volume(), plan.area * 2.8, places=3)
        self.assertAlmostEqual(Polygon(self._straight_corners(doc, wall, "start") + self._straight_corners(doc, wall, "end")[::-1]
                                       ).intersection(plan).area, 0.0, places=9)
        bim.set_type(doc, wall, catalog.BY_KEY["parede_alv_15"])          # thinner: the corner made again
        self.assertEqual(doc.ifc.joined_walls([arc]), [wall])
        self._same(self._straight_corners(doc, wall, "end"), self._curved_corners(doc, arc, "start"))
        bim.mirror_objects(doc, [wall, arc], np.array((0.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0)))
        self.assertEqual(doc.ifc.joined_walls([arc]), [wall])
        self._same(self._straight_corners(doc, wall, "start" if doc.ifc.wall_axis(wall)[0][0] < -3 else "end"),
                   self._curved_corners(doc, arc, "start"))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_two_curved_and_drawn_after(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        a = bim.add_curved_wall(doc, (0.0, 0.0, 0.0), 3.0, 0.0, math.pi / 2, spec)        # (3,0) -> (0,3)
        b = bim.add_curved_wall(doc, (3.0, -2.0, 0.0), 2.0, math.pi / 2, -math.pi / 2, spec)   # (3,0) -> (5,-2)
        self.assertEqual(doc.ifc.joined_walls([b]), [a])
        self._same(self._curved_corners(doc, a, "start"), self._curved_corners(doc, b, "start"))
        wall = bim.add_wall(doc, np.array((0.0, 6.0, 0.0)), np.array((0.0, 3.0, 0.0)), spec)   # down to a's end
        self.assertIn(a, doc.ifc.joined_walls([wall]))
        self._same(self._straight_corners(doc, wall, "end"), self._curved_corners(doc, a, "end"))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertEqual(doc.ifc.wall_cuts(a)[1], 0.0)                   # (undone: a's end square again)


class CurvedTees(unittest.TestCase):
    """0.246: a straight wall drawn up to a curved wall's side, at 45° — joined in a T (the curved wall runs on,
    "path"), its end on the curved wall's outer face: both its corners on that circle, the bodies not overlapping;
    the curved wall made bigger: the straight one follows it; one coming from inside stops on the inner face; one
    past the arc's end, or along it, not joined; valid IFC; undone: as it was drawn."""

    def test_tee(self):
        from shapely.geometry import Polygon
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        arc = bim.add_curved_wall(doc, (0.0, 0.0, 0.0), 3.0, 0.0, math.pi / 2, spec)
        u = np.array((math.cos(math.pi / 4), math.sin(math.pi / 4), 0.0))
        wall = bim.add_wall(doc, u * 6.0, u * 3.0, spec)                 # (to the curved wall's axis)
        self.assertIn(arc, doc.ifc.joined_walls([wall]))
        rel = next(r for r, a, ea, b, eb in doc.ifc.wall_joints(wall))
        self.assertEqual(rel.RelatingConnectionType, "ATPATH")
        _r, t = 3.0, 0.20
        for q in CurvedCornersIfc._straight_corners(doc, wall, "end"):
            self.assertAlmostEqual(float(np.linalg.norm(q)), 3.0 + t / 2, places=6)   # (on its outer face)
        band = Polygon(doc.ifc.curved_wall_band(arc)[0])
        s, e, _t = doc.ifc.wall_axis(wall)
        body = Polygon(CurvedCornersIfc._straight_corners(doc, wall, "start")
                       + CurvedCornersIfc._straight_corners(doc, wall, "end")[::-1])
        self.assertLess(body.intersection(band).area, 1e-4)
        bim.set_curved_wall(doc, arc, radius=3.5)                        # (the curved wall bigger: the T follows)
        for q in CurvedCornersIfc._straight_corners(doc, wall, "end"):
            self.assertAlmostEqual(float(np.linalg.norm(q)), 3.5 + t / 2, places=6)
        inner = bim.add_wall(doc, u * 1.0, u * 3.5, spec)                # (from inside)
        self.assertIn(arc, doc.ifc.joined_walls([inner]))
        for q in CurvedCornersIfc._straight_corners(doc, inner, "end"):
            self.assertAlmostEqual(float(np.linalg.norm(q)), 3.5 - t / 2, places=6)
        v = np.array((math.cos(math.radians(120)), math.sin(math.radians(120)), 0.0))
        past = bim.add_wall(doc, v * 6.0, v * 3.5, spec)                 # (past the arc's end: no T)
        self.assertNotIn(arc, doc.ifc.joined_walls([past]))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class EmbeddedCurtainWalls(unittest.TestCase):
    """0.188: a curtain wall drawn in a wall (8 m, 20 cm, 2,80 m) — 3 m long, 2,40 m high, from 2 m — cuts its
    opening there (the wall 1,44 m³ less), filling it as a door does; slid along the wall to 3 m; 4 m long (the
    opening follows); 6 m refused (it would leave the wall); the wall moved: the curtain wall goes with it; the wall
    mirrored: still in it; the wall 15 cm thick: its opening across the new thickness, the curtain wall as it was;
    embedding turned off (the wall whole, the curtain wall where it was) and on; one drawn apart and moved into the
    wall embeds itself; the IFC valid."""

    def test_embedded(self):
        from arqbim.core.transform import translation as move_by
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((8.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        full = doc.get(wall).mesh.volume()
        self.assertAlmostEqual(full, 8.0 * 2.8 * 0.2, places=6)
        cw = bim.add_curtain_wall(doc, np.array((2.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), 2.4, 1.5, 1.2)
        self.assertEqual(doc.ifc.host_wall(cw), wall)
        self.assertTrue(bim.is_filling(doc, cw))
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), full - 3.0 * 2.4 * 0.2, places=6)
        st = doc.ifc.filling_state(cw)
        self.assertAlmostEqual(st["s"], 2.0)
        self.assertAlmostEqual(st["width"], 3.0)
        bim.move_filling(doc, cw, s=3.0)                                 # slid along the wall
        self.assertTrue(np.allclose(doc.ifc.curtain_params(cw)["start"], (3.0, 0.0, 0.0), atol=1e-6))
        lo, hi = bounds(doc, cw)
        self.assertAlmostEqual(lo[0], 3.0, places=6)
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), full - 3.0 * 2.4 * 0.2, places=6)
        bim.set_curtain_wall(doc, cw, length=4.0)                        # longer: the opening follows
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), full - 4.0 * 2.4 * 0.2, places=6)
        with self.assertRaises(ValueError):
            bim.set_curtain_wall(doc, cw, length=6.0)                    # (3 + 6 > 8: out of the wall)
        self.assertAlmostEqual(doc.ifc.curtain_params(cw)["length"], 4.0)
        info = doc.ifc.describe(cw)
        self.assertTrue(info["params"]["embed"])
        self.assertAlmostEqual(info["params"]["from_start"], 3.0, places=6)
        self.assertAlmostEqual(info["params"]["to_end"], 1.0, places=6)
        bim.transform_objects(doc, [wall], move_by((0.0, 2.0, 0.0)), "mover")   # the wall moved: it goes too
        self.assertTrue(np.allclose(doc.ifc.curtain_params(cw)["start"], (3.0, 2.0, 0.0), atol=1e-6))
        self.assertEqual(doc.ifc.host_wall(cw), wall)
        bim.mirror_objects(doc, [wall], np.array((0.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0)))   # about x = 0
        p = doc.ifc.curtain_params(cw)
        self.assertEqual(doc.ifc.host_wall(cw), wall)
        self.assertIsNotNone(doc.ifc._in_wall(cw, wall))
        self.assertAlmostEqual(min(p["start"][0], p["end"][0]), -7.0, places=6)
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), full - 4.0 * 2.4 * 0.2, places=6)
        bim.set_type(doc, wall, catalog.BY_KEY["parede_alv_15"])          # thinner: the opening across it
        thin = doc.get(wall).mesh.volume()
        self.assertAlmostEqual(thin, 8.0 * 2.8 * 0.15 - 4.0 * 2.4 * 0.15, places=6)
        self.assertEqual(len(doc.ifc.by_guid(cw).Representation.Representations[0].Items), 4 + 3 + 6)
        bim.set_curtain_embedding(doc, cw, False)                        # out of the wall: the wall whole
        self.assertIsNone(doc.ifc.host_wall(cw))
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), 8.0 * 2.8 * 0.15, places=6)
        self.assertAlmostEqual(min(doc.ifc.curtain_params(cw)["start"][0], doc.ifc.curtain_params(cw)["end"][0]),
                               -7.0, places=6)
        bim.set_curtain_embedding(doc, cw, True)
        self.assertEqual(doc.ifc.host_wall(cw), wall)
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), thin, places=6)
        apart = bim.add_curtain_wall(doc, np.array((-5.0, 6.0, 0.0)), np.array((-4.0, 6.0, 0.0)), 2.0, 1.0, 1.0)
        self.assertIsNone(doc.ifc.host_wall(apart))
        bim.transform_objects(doc, [apart], move_by((2.5, -4.0, 0.0)), "mover")    # into the wall, by the other
        self.assertEqual(doc.ifc.host_wall(apart), wall)
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), thin - 1.0 * 2.0 * 0.15, places=6)
        with self.assertRaises(ValueError):
            bim.set_curtain_embedding(doc, bim.add_curtain_wall(doc, np.array((0.0, 9.0, 0.0)),
                                                                np.array((2.0, 9.0, 0.0)), 2.0, 1.0, 1.0), True)
        copies = bim.copy_filling(doc, apart, [np.array((1.2, 0.0, 0.0))])    # a copy along the wall
        self.assertEqual(len(copies), 1)
        self.assertEqual(doc.ifc.host_wall(copies[0]), wall)
        self.assertAlmostEqual(doc.ifc.curtain_params(copies[0])["length"], 1.0)
        st = doc.ifc.filling_state(cw)                                    # split between the two first ones
        st2 = doc.ifc.filling_state(apart)
        cut = (st["s"] + st["width"] + st2["s"]) / 2 if st2["s"] > st["s"] else (st2["s"] + st2["width"] + st["s"]) / 2
        other = bim.split_wall(doc, wall, cut)                            # (each part keeps its own, as doors)
        everyone = [e.GlobalId for e in doc.ifc.file.by_type("IfcCurtainWall")]
        embedded = [g for g in everyone if doc.ifc.host_wall(g)]
        self.assertEqual((len(everyone), len(embedded)), (4, 3))         # (none doubled by the split)
        self.assertEqual({doc.ifc.host_wall(g) for g in embedded}, {wall, other})
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        in_wall = sum(1 for g in embedded if doc.ifc.host_wall(g) == wall)
        bim.delete(doc, [wall])                                           # a wall takes what is in it, as a door
        self.assertEqual(len(doc.ifc.file.by_type("IfcCurtainWall")), 4 - in_wall)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        while doc.can_undo():
            doc.undo()
        self.assertEqual(len(doc.ifc.file.by_type("IfcCurtainWall")), 0)


class JoinedEdits(unittest.TestCase):
    """0.187: a change made in the Properties to several elements — one undo step for all of them, redone so."""

    def test_heights_of_three_walls_in_one_step(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        walls = [bim.add_wall(doc, np.array((0.0, 3.0 * k, 0.0)), np.array((4.0, 3.0 * k, 0.0)), spec)
                 for k in range(3)]
        before = len(doc._undo)
        mark = doc.undo_mark()
        for w in walls:
            bim.set_constraints(doc, w, height=3.4)
        self.assertEqual(doc.join_since(mark), 3)
        self.assertEqual(len(doc._undo), before + 1)
        self.assertTrue(all(abs(doc.ifc.wall_params(w)[1] - 3.4) < 1e-9 for w in walls))
        doc.undo()
        self.assertTrue(all(abs(doc.ifc.wall_params(w)[1] - 2.8) < 1e-9 for w in walls))
        self.assertTrue(all(abs(bounds(doc, w)[1][2] - 2.8) < 1e-6 for w in walls))
        doc.redo()
        self.assertTrue(all(abs(bounds(doc, w)[1][2] - 3.4) < 1e-6 for w in walls))
        doc.undo()
        doc.undo()                                                       # (and the third wall before it)
        self.assertEqual(len([o for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcWall"]), 2)
        mark = doc.undo_mark()
        self.assertEqual(doc.join_since(mark), 0)                        # (nothing done: nothing joined)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class TypeEditor(unittest.TestCase):
    """0.87: a type changed in the project — its walls follow (thickness, a door in them), the IFC type keeps
    its GlobalId and name, the project's version takes the catalogue entry's place; a new type, unused, can
    be removed; undo brings all back."""

    def tearDown(self):
        catalog.set_project(())

    def test_edit_duplicate_delete(self):
        from arqbim.model import project_types
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        a = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), spec)
        b = bim.add_wall(doc, np.array((5.0, 0.0, 0.0)), np.array((5.0, 4.0, 0.0)), spec, prev=(a, np.array((1.0, 0, 0))))
        frame = bim.wall_frame(doc, a)
        door = bim.add_opening(doc, a, catalog.OPENING_BY_KEY["porta_80"], frame, 1.0, 1)
        old = project_types.find_type(doc.ifc, spec)
        guid = old.GlobalId
        thicker = catalog.TypeSpec(spec.key, "wall", spec.name_pt, spec.name_en,
                                   layers=(("reboco", 0.02), ("bloco", 0.21), ("reboco", 0.02)))
        self.assertEqual(bim.save_type(doc, thicker, spec), guid)
        self.assertAlmostEqual(doc.ifc.wall_params(a)[2], 0.25)
        self.assertAlmostEqual(doc.ifc.wall_params(b)[2], 0.25)
        types = doc.ifc.file.by_type("IfcWallType")
        self.assertEqual([(t.GlobalId, t.Name) for t in types], [(guid, spec.name_pt)])
        self.assertIsNotNone(doc.ifc.by_guid(door))
        read = project_types.read(doc.ifc)
        self.assertEqual([(s.key, round(s.thickness, 6)) for s in read], [("parede_alv_20", 0.25)])
        catalog.set_project(read)
        self.assertAlmostEqual(catalog.BY_KEY["parede_alv_20"].thickness, 0.25)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        # a new one, from it: made, unused, removed
        new = catalog.TypeSpec("t:new", "wall", "Parede 30", "Parede 30",
                               layers=(("reboco", 0.02), ("bloco", 0.26), ("reboco", 0.02)))
        made = bim.save_type(doc, new)
        catalog.set_project(project_types.read(doc.ifc))
        self.assertIn("t:" + made, catalog.BY_KEY)
        self.assertEqual([s.name_pt for s in catalog.types() if s.kind == "wall"][-1], "Parede 30")
        self.assertFalse(bim.delete_type(doc, catalog.BY_KEY["parede_alv_20"]))       # in use
        self.assertTrue(bim.delete_type(doc, catalog.BY_KEY["t:" + made]))
        self.assertEqual(len(doc.ifc.file.by_type("IfcWallType")), 1)
        for _ in range(3):
            doc.undo()                                                       # removed, made, changed: undone
        self.assertAlmostEqual(doc.ifc.wall_params(a)[2], 0.20)
        self.assertEqual(project_types.read(doc.ifc), [])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_materials(self):
        """0.89: a material of the catalogue changed (its hatch, colour, density, conductivity) and a new one
        made and removed — kept in the IFC (category, style, IFC4 material psets); undo."""
        import ifcopenshell.util.element as ue_
        from arqbim.model import project_types
        doc = Document()
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        block = catalog.MATERIALS["bloco"]
        changed = catalog.MaterialSpec("bloco", block.name_pt, block.name_en, "concrete", (0.2, 0.3, 0.4), 1400.0, 0.45)
        bim.save_material(doc, changed, block)
        m = project_types.find_material(doc.ifc, block)
        self.assertEqual(m.Category, "concrete")
        psets = ue_.get_psets(m)
        self.assertAlmostEqual(psets["Pset_MaterialCommon"]["MassDensity"], 1400.0)
        self.assertAlmostEqual(psets["Pset_MaterialThermal"]["ThermalConductivity"], 0.45)
        read = {s.key: s for s in project_types.materials(doc.ifc)}
        self.assertEqual(read["bloco"].category, "concrete")
        self.assertTrue(np.allclose(read["bloco"].color, (0.2, 0.3, 0.4)))
        wall = doc.ifc.file.by_type("IfcWall")[0].GlobalId
        self.assertEqual(doc.ifc.layers([wall])[wall][1][0], "concrete")          # the block layer: its new hatch
        new = catalog.MaterialSpec("m:new", "Cortiça", "Cortiça", "insulation", (0.6, 0.45, 0.3), 120.0, 0.04)
        bim.save_material(doc, new)
        catalog.set_project(project_types.read(doc.ifc), project_types.materials(doc.ifc))
        self.assertIn("m:Cortiça", catalog.MATERIALS)
        self.assertTrue(bim.delete_material(doc, catalog.MATERIALS["m:Cortiça"]))
        self.assertFalse(bim.delete_material(doc, catalog.MATERIALS["bloco"]))   # the catalogue's: never
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        for _ in range(3):
            doc.undo()
        self.assertEqual(project_types.find_material(doc.ifc, block).Category, block.category)

    def test_material_graphics(self):
        """0.314: a material's graphics, as Revit's — its surface (foreground and background patterns, each in its
        colour, its transparency) and its cut (the same) — kept in the IFC (the surface style's Transparency, fill
        area styles «Surface» and «Cut» with a colour and hatchings, the patterns' keys in its parameter), read back
        the same after reopening; valid IFC4; a catalogue material's own (tiles) kept and taken away; another
        program's fill style read roughly."""
        import tempfile
        import ifcopenshell
        from arqbim.ifc import material_graphics
        from arqbim.model import project_types
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        block = catalog.MATERIALS["bloco"]
        changed = dataclasses.replace(block, surface_fg=("brick", "#7a3f2a"), surface_bg=("solid", "#c88a6a"),
                                      transparency=0.25, cut_fg=("diagonal", "#202020"), cut_bg=("solid", "#f2dcd2"))
        self.assertTrue(changed.own_cut and not block.own_cut)
        bim.save_material(doc, changed, block)
        m = project_types.find_material(doc.ifc, block)
        self.assertAlmostEqual(material_graphics.transparency(m), 0.25)
        item = material_graphics._styled_item(m)
        fills = {s.Name: s for s in item.Styles if s.is_a("IfcFillAreaStyle")}
        self.assertEqual(set(fills), {"Surface", "Cut"})
        self.assertTrue(fills["Surface"].ModelorDraughting)
        self.assertFalse(fills["Cut"].ModelorDraughting)
        surface = fills["Surface"].FillStyles
        self.assertEqual([(s.Name, round(s.Red, 3)) for s in surface if s.is_a("IfcColourRgb")],
                         [("Background", round(0xc8 / 255, 3))])
        hatchings = [s for s in surface if s.is_a("IfcFillAreaStyleHatching")]
        self.assertEqual(len(hatchings), 2)                                   # (a brick bond: courses and joints)
        self.assertEqual({h.HatchLineAppearance.Name for h in hatchings}, {"Foreground"})
        self.assertAlmostEqual(hatchings[0].StartOfNextHatchLine.wrappedValue, 65.0)   # (6,5 cm, in mm)
        self.assertEqual(len([s for s in fills["Cut"].FillStyles if s.is_a("IfcFillAreaStyleHatching")]), 1)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        read = {s.key: s for s in project_types.materials(doc.ifc)}
        self.assertEqual(read["bloco"].graphics(), changed.graphics())
        self.assertGreater(len(doc.get(wall).mesh.tris), 0)                  # (its shape still made)
        # reopened: the same
        path = os.path.join(tempfile.mkdtemp(), "graficos.ifc")
        doc.ifc.file.write(path)
        again = ifcopenshell.open(path)
        m2 = next(x for x in again.by_type("IfcMaterial") if x.Name == m.Name)
        self.assertEqual(project_types.read_material(m2).graphics(), changed.graphics())
        # a catalogue material with patterns of its own (the tiles' joints): made with them, not listed as changed
        tiles = catalog.MATERIALS["azulejo"]
        self.assertEqual(tiles.surface_fg[0], "tile_15")
        made = doc.ifc._material("azulejo", "pt")
        self.assertEqual(project_types.read_material(made).graphics(), tiles.graphics())
        self.assertNotIn("azulejo", {s.key for s in project_types.materials(doc.ifc)})
        bim.save_material(doc, dataclasses.replace(tiles, surface_fg=None), tiles)       # (taken away: kept so)
        self.assertIsNone(project_types.read_material(made).surface_fg)
        self.assertIn("azulejo", {s.key for s in project_types.materials(doc.ifc)})
        # another program's: a cut fill style with a colour and a hatching, no parameter
        f = doc.ifc.file
        other = f.create_entity("IfcMaterial", Name="Outro")
        style = f.create_entity("IfcSurfaceStyle", Name="Outro", Side="BOTH", Styles=[
            f.create_entity("IfcSurfaceStyleShading", SurfaceColour=f.create_entity(
                "IfcColourRgb", Name=None, Red=0.5, Green=0.5, Blue=0.5))])
        hatch = f.create_entity("IfcFillAreaStyleHatching", HatchLineAppearance=f.create_entity(
            "IfcCurveStyle", Name=None, CurveColour=f.create_entity("IfcColourRgb", Name=None, Red=1.0, Green=0.0,
                                                                      Blue=0.0)),
            StartOfNextHatchLine=f.create_entity("IfcPositiveLengthMeasure", 2.0), HatchLineAngle=0.7854)
        fill = f.create_entity("IfcFillAreaStyle", Name="Hatch", FillStyles=[
            f.create_entity("IfcColourRgb", Name=None, Red=1.0, Green=1.0, Blue=1.0), hatch])
        rep = f.create_entity("IfcStyledRepresentation", ContextOfItems=doc.ifc.body, Items=[
            f.create_entity("IfcStyledItem", Item=None, Styles=[style, fill])])
        f.create_entity("IfcMaterialDefinitionRepresentation", Representations=[rep], RepresentedMaterial=other)
        foreign = project_types.read_material(other)
        self.assertEqual((foreign.cut_fg, foreign.cut_bg), (("diagonal", "#ff0000"), ("solid", "#ffffff")))
        self.assertIsNone(foreign.surface_fg)

    def test_material_finish(self):
        """0.343: a material's finish in the realistic render kept in its parameter («Acabamento»), read back after
        reopening, the material then listed as changed; valid IFC4. A catalogue material that starts with a finish of
        its own (the white lacquer glossy) made with it; set back to its category's («auto»): kept so."""
        import tempfile
        import ifcopenshell
        from arqbim.ifc import material_graphics
        from arqbim.model import project_types
        doc = Document()
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        block = catalog.MATERIALS["bloco"]
        self.assertEqual(block.finish, "")
        bim.save_material(doc, dataclasses.replace(block, finish="glossy"), block)
        m = project_types.find_material(doc.ifc, block)
        self.assertEqual(material_graphics.read_finish(m), "glossy")
        self.assertEqual({s.key: s for s in project_types.materials(doc.ifc)}["bloco"].finish, "glossy")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        path = os.path.join(tempfile.mkdtemp(), "acabamento.ifc")
        doc.ifc.file.write(path)
        again = ifcopenshell.open(path)
        self.assertEqual(project_types.read_material(next(x for x in again.by_type("IfcMaterial")
                                                          if x.Name == m.Name)).finish, "glossy")
        lacquer = catalog.MATERIALS["lacado_branco"]
        self.assertEqual(lacquer.finish, "glossy")
        made = doc.ifc._material("lacado_branco", "pt")
        self.assertEqual(project_types.read_material(made).finish, "glossy")
        self.assertNotIn("lacado_branco", {s.key for s in project_types.materials(doc.ifc)})
        bim.save_material(doc, dataclasses.replace(lacquer, finish=""), lacquer)
        self.assertEqual(material_graphics.read_finish(made), "")
        self.assertEqual(project_types.read_material(made).finish, "")
        self.assertIn("lacado_branco", {s.key for s in project_types.materials(doc.ifc)})

    def test_door_type(self):
        """0.88: a door type made wider and taller — its doors, hinged on either side, follow; undo."""
        from arqbim.model import project_types
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        door80 = catalog.OPENING_BY_KEY["porta_80"]
        d1 = bim.add_opening(doc, wall, door80, bim.wall_frame(doc, wall), 0.5, 1)
        d2 = bim.add_opening(doc, wall, door80, bim.wall_frame(doc, wall), 3.0, 1)
        bim.flip_door(doc, d2, hinge=True)                                  # hinged on the right
        self.assertEqual(len(project_types.instances(doc.ifc, door80)), 2)
        wider = catalog.OpeningSpec("porta_80", "door", door80.name_pt, door80.name_en, 0.95, 2.20,
                                    operation=door80.operation)
        bim.save_type(doc, wider, door80)
        for d in (d1, d2):
            e = doc.ifc.by_guid(d)
            self.assertAlmostEqual(e.OverallWidth * doc.ifc.unit_scale, 0.95)
            self.assertAlmostEqual(e.OverallHeight * doc.ifc.unit_scale, 2.20)
        read = project_types.read_openings(doc.ifc)
        self.assertEqual([(o.key, round(o.width, 6)) for o in read], [("porta_80", 0.95)])
        self.assertEqual(len(doc.ifc.file.by_type("IfcDoorType")), 2)          # it and its right-hand one
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertAlmostEqual(doc.ifc.by_guid(d1).OverallWidth * doc.ifc.unit_scale, 0.80)
        self.assertEqual(project_types.read_openings(doc.ifc), [])


class GridSettings(unittest.TestCase):
    """0.91: the grid's dimensions in a plan (a chain and the overall one), the tags' scheme swapped and the axes
    renumbered in order, undo, and the settings kept in the .arqsynthbim file."""

    def test_dimensions_scheme_renumber_saved(self):
        from arqbim.model import dimensions as dims_model
        doc = Document()
        bim.generate_grid(doc, [0.0, 5.0, 10.0], [0.0, 6.0])
        self.assertEqual(sorted(a.tag for a in doc.grids), ["1", "2", "3", "A", "B"])
        plan = ("plan", doc.ifc.storeys()[0][0])
        self.assertEqual(doc.dimensions_of(plan), [])                       # (off by default)
        bim.set_grid_settings(doc, {"dims": True})
        dims = doc.dimensions_of(plan)
        lengths = sorted(round(float(np.linalg.norm((d.b - d.a)[:2])), 6) for d in dims)
        self.assertEqual(lengths, [5.0, 5.0, 6.0, 10.0])
        self.assertTrue(all(d.tag == "grid" for d in dims))
        self.assertIs(doc.dimensions_of(plan)[0], dims[0])                  # (the same until the grid changes)
        bim.set_grid_settings(doc, {"scheme": "letters_y", "bubble": 0.5}, renumber=True)
        vertical = sorted((a.start[0], a.tag) for a in doc.grids if a.numbered)
        self.assertEqual([tag for _x, tag in vertical], ["A", "B", "C"])
        self.assertEqual(sorted(a.tag for a in doc.grids if not a.numbered), ["1", "2"])
        self.assertEqual(bim.add_grid_axis(doc, (15.0, -1.5), (15.0, 7.5)), "D")     # a new vertical one: a letter
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "grelha.ifc")
            doc.save(path)
            again = Document()
            again.show_file(read_file(path))
            self.assertEqual(again.grid_settings, {"scheme": "letters_y", "dims": True, "bubble": 0.5})
        doc.undo()
        doc.undo()
        self.assertEqual(doc.grid_settings["scheme"], "numbers_y")
        self.assertEqual(sorted(a.tag for a in doc.grids), ["1", "2", "3", "A", "B"])
        self.assertEqual(len(dims_model.grid_chains(doc.grids, 0.0, plan)), 4)


class ColumnsOnGrid(unittest.TestCase):
    """0.92: columns at the crossings of the axes selected (both ways, one way, none: all), not twice; tied to
    their axes — an axis moved takes its columns along, renumbering keeps them tied; undo."""

    def test_columns_on_grid(self):
        doc = Document()
        bim.generate_grid(doc, [0.0, 5.0, 10.0], [0.0, 6.0])          # 1 2 3 vertical, A B horizontal
        idx = {a.tag: k for k, a in enumerate(doc.grids)}
        spec = catalog.BY_KEY["pilar_30"]
        storey = doc.active_storey
        made = bim.columns_on_grid(doc, [idx["2"], idx["A"]], spec, 2.8, storey)   # both ways: their crossing
        self.assertEqual(len(made), 1)
        self.assertTrue(np.allclose(doc.ifc.placement(made[0])[:2, 3], (5.0, 0.0)))
        made = bim.columns_on_grid(doc, [idx["1"]], spec, 2.8, storey)            # one way: with A and B
        self.assertEqual(sorted(tuple(np.round(doc.ifc.placement(g)[:2, 3], 6)) for g in made), [(0, 0), (0, 6)])
        made = bim.columns_on_grid(doc, None, spec, 2.8, storey)                  # all: the 3 left
        self.assertEqual(len(made), 3)
        self.assertEqual(bim.columns_on_grid(doc, None, spec, 2.8, storey), [])   # (not twice)
        self.assertEqual(len(doc.ifc.grid_ties()), 6)
        k = idx["2"]
        axis = doc.grids[k]
        bim.move_grid_axes(doc, {k: ((axis.start[0] + 1.0, axis.start[1]), (axis.end[0] + 1.0, axis.end[1]))})
        xs = sorted(round(float(doc.ifc.placement(g)[0, 3]), 6) for g in doc.ifc.grid_ties())
        self.assertEqual(xs, [0.0, 0.0, 6.0, 6.0, 10.0, 10.0])                    # axis 2's columns went to x 6
        bim.set_grid_settings(doc, {"scheme": "letters_y"}, renumber=True)        # tags change, ties stay
        bim.move_grid_axes(doc, {k: ((5.0, doc.grids[k].start[1]), (5.0, doc.grids[k].end[1]))})
        xs = sorted(round(float(doc.ifc.placement(g)[0, 3]), 6) for g in doc.ifc.grid_ties())
        self.assertEqual(xs, [0.0, 0.0, 5.0, 5.0, 10.0, 10.0])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        for _ in range(3):
            doc.undo()
        xs = sorted(round(float(doc.ifc.placement(g)[0, 3]), 6) for g in doc.ifc.grid_ties())
        self.assertEqual(xs, [0.0, 0.0, 5.0, 5.0, 10.0, 10.0])


class FootingsUnderColumns(unittest.TestCase):
    """0.93: a footing under every column (not twice), tied to it — a column moved takes its footing, an axis moved
    takes its columns and their footings; undo."""

    def test_footings_follow(self):
        doc = Document()
        bim.generate_grid(doc, [0.0, 5.0], [0.0, 6.0])
        cols = bim.columns_on_grid(doc, None, catalog.BY_KEY["pilar_30"], 2.8, doc.active_storey)
        made = bim.footings_under(doc, None, catalog.BY_KEY["sapata_80"])
        self.assertEqual(len(made), 4)
        self.assertEqual(bim.footings_under(doc, None, catalog.BY_KEY["sapata_80"]), [])      # (not twice)
        under = doc.ifc.footings_of(cols)
        self.assertEqual(sorted(len(v) for v in under.values()), [1, 1, 1, 1])

        def centre(g):
            return np.round(doc.ifc.footing_params(g)[0], 6)

        c0, f0 = cols[0], under[cols[0]][0]
        self.assertTrue(np.allclose(centre(f0), doc.ifc.placement(c0)[:2, 3]))
        m = np.eye(4)
        m[0, 3] = 2.0
        bim.transform_objects(doc, [c0], m, "mover")
        self.assertTrue(np.allclose(centre(f0), doc.ifc.placement(c0)[:2, 3]))
        idx = {a.tag: k for k, a in enumerate(doc.grids)}
        k = idx["2"]
        axis = doc.grids[k]
        bim.move_grid_axes(doc, {k: ((axis.start[0] + 1.0, axis.start[1]), (axis.end[0] + 1.0, axis.end[1]))})
        xs = sorted(round(float(centre(f)[0]), 6) for fs in doc.ifc.footings_of(cols).values() for f in fs)
        self.assertEqual(xs[-2:], [6.0, 6.0])                                      # axis 2's footings at x 6
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        doc.undo()
        self.assertTrue(np.allclose(centre(f0), doc.ifc.placement(c0)[:2, 3]))


class BeamsBetweenColumns(unittest.TestCase):
    """0.94: beams between six columns on a 3 × 2 grid — seven, face to face, their top at the columns' top, not
    twice; an axis moved: they stretch and shrink; a column of a smaller type: its beams reach its new faces; a
    beam copied with its columns is tied to the copies; undo."""

    def test_beams_between(self):
        doc = Document()
        bim.generate_grid(doc, [0.0, 5.0, 10.0], [0.0, 6.0])
        cols = bim.columns_on_grid(doc, None, catalog.BY_KEY["pilar_30"], 2.8, doc.active_storey)
        beams = bim.beams_between(doc, None, catalog.BY_KEY["viga_20x40"])
        self.assertEqual(len(beams), 7)
        self.assertEqual(bim.beams_between(doc, None, catalog.BY_KEY["viga_20x40"]), [])
        lengths = sorted(round(float(np.linalg.norm((e - s)[:2])), 6) for s, e, *_ in map(doc.ifc.beam_params, beams))
        self.assertEqual(lengths, [4.7] * 4 + [5.7] * 3)
        self.assertTrue(all(abs(doc.ifc.beam_params(b)[2] - 2.8) < 1e-9 for b in beams))       # top at 2,80
        idx = {a.tag: k for k, a in enumerate(doc.grids)}
        k = idx["2"]
        axis = doc.grids[k]
        bim.move_grid_axes(doc, {k: ((axis.start[0] + 1.0, axis.start[1]), (axis.end[0] + 1.0, axis.end[1]))})
        lengths = sorted(round(float(np.linalg.norm((e - s)[:2])), 6) for s, e, *_ in map(doc.ifc.beam_params, beams))
        self.assertEqual(lengths, [3.7, 3.7, 5.7, 5.7, 5.7, 5.7, 5.7])
        corner = next(c for c in cols if np.allclose(doc.ifc.placement(c)[:2, 3], (0.0, 0.0)))
        bim.set_type(doc, corner, catalog.BY_KEY["pilar_20"])                 # 20 × 20: its beams 5 cm longer
        lengths = sorted(round(float(np.linalg.norm((e - s)[:2])), 6) for s, e, *_ in map(doc.ifc.beam_params, beams))
        self.assertEqual(lengths, [3.7, 3.7, 5.7, 5.7, 5.7, 5.75, 5.75])
        m = np.eye(4)
        m[1, 3] = 10.0
        new = bim.copy_objects(doc, cols + beams, [m], "copiar")
        copied_beams = [g for g in new if doc.ifc.kind_of(g) == "beam"]
        ties = {doc.ifc._params(doc.ifc.by_guid(b)).get("PilarA") for b in copied_beams}
        self.assertTrue(ties and ties <= set(new))                            # tied to the copied columns
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        doc.undo()
        doc.undo()
        lengths = sorted(round(float(np.linalg.norm((e - s)[:2])), 6) for s, e, *_ in map(doc.ifc.beam_params, beams))
        self.assertEqual(lengths, [4.7] * 4 + [5.7] * 3)


class WallsUnderBeams(unittest.TestCase):
    """0.95: a wall under a beam between two columns — face to face, from the floor to the beam's underside; a
    column moved: the beam and its wall follow; not twice; undo."""

    def test_walls_under_beams(self):
        doc = Document()
        a = bim.add_column(doc, np.array((0.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        b = bim.add_column(doc, np.array((5.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        beam = bim.beams_between(doc, [a, b], catalog.BY_KEY["viga_20x40"])[0]
        walls = bim.walls_under_beams(doc, None, catalog.BY_KEY["parede_alv_15"])
        self.assertEqual(len(walls), 1)
        self.assertEqual(bim.walls_under_beams(doc, None, catalog.BY_KEY["parede_alv_15"]), [])
        length, height, thickness = doc.ifc.wall_params(walls[0])
        self.assertEqual([round(v, 6) for v in (length, height, thickness)], [4.7, 2.4, 0.15])
        lo, hi = bounds(doc, walls[0])
        self.assertAlmostEqual(lo[2], 0.0)
        self.assertAlmostEqual(hi[2], 2.4)
        m = np.eye(4)
        m[0, 3] = 1.0
        bim.transform_objects(doc, [b], m, "mover")
        self.assertAlmostEqual(doc.ifc.wall_params(walls[0])[0], 5.7)
        self.assertAlmostEqual(float(np.linalg.norm((doc.ifc.beam_params(beam)[1] - doc.ifc.beam_params(beam)[0])[:2])),
                               5.7)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertAlmostEqual(doc.ifc.wall_params(walls[0])[0], 4.7)


class SlabsInBays(unittest.TestCase):
    """0.96: a 3 × 2 frame of columns and beams — a slab in each of its two bays, between the beams' inner faces,
    its top at theirs; not twice; an axis moved: the slabs follow; undo."""

    def test_slabs_in_bays(self):
        doc = Document()
        bim.generate_grid(doc, [0.0, 5.0, 10.0], [0.0, 6.0])
        bim.columns_on_grid(doc, None, catalog.BY_KEY["pilar_30"], 2.8, doc.active_storey)
        bim.beams_between(doc, None, catalog.BY_KEY["viga_20x40"])
        slabs, skipped = bim.slabs_in_bays(doc, None, catalog.BY_KEY["laje_12"])
        self.assertEqual((len(slabs), skipped), (2, 0))
        self.assertEqual(bim.slabs_in_bays(doc, None, catalog.BY_KEY["laje_12"]), ([], 0))

        def boxes():
            return sorted(tuple(np.round(np.concatenate(bounds(doc, s)), 6)) for s in slabs)

        self.assertEqual(boxes(), [(0.1, 0.1, 2.68, 4.9, 5.9, 2.8), (5.1, 0.1, 2.68, 9.9, 5.9, 2.8)])
        idx = {a.tag: k for k, a in enumerate(doc.grids)}
        k = idx["2"]
        axis = doc.grids[k]
        bim.move_grid_axes(doc, {k: ((axis.start[0] + 1.0, axis.start[1]), (axis.end[0] + 1.0, axis.end[1]))})
        self.assertEqual(boxes(), [(0.1, 0.1, 2.68, 5.9, 5.9, 2.8), (6.1, 0.1, 2.68, 9.9, 5.9, 2.8)])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertEqual(boxes(), [(0.1, 0.1, 2.68, 4.9, 5.9, 2.8), (5.1, 0.1, 2.68, 9.9, 5.9, 2.8)])


class Sections(unittest.TestCase):
    """0.97: round, L and T columns and a T beam — their IFC profiles and areas; a beam between round columns
    face to face; an L type edited in the project (thicker legs) read back as an L."""

    def tearDown(self):
        catalog.set_project(())

    def test_round_l_t(self):
        from arqbim.model import project_types
        doc = Document()
        cols = {k: bim.add_column(doc, np.array((x, 0.0, 0.0)), catalog.BY_KEY[k], 2.8)
                for k, x in (("pilar_circ_30", 0.0), ("pilar_L_40", 5.0), ("pilar_T_50", 10.0))}
        areas = {k: ue.get_psets(doc.ifc.by_guid(g))["Qto_ColumnBaseQuantities"]["CrossSectionArea"]
                 for k, g in cols.items()}
        self.assertAlmostEqual(areas["pilar_circ_30"], math.pi * 0.15 ** 2)
        self.assertAlmostEqual(areas["pilar_L_40"], 0.15 * (0.40 + 0.40 - 0.15))
        self.assertAlmostEqual(areas["pilar_T_50"], 0.50 * 0.15 + 0.15 * (0.40 - 0.15))
        classes = {k: ue.get_material(doc.ifc.by_guid(g), should_skip_usage=True).MaterialProfiles[0].Profile.is_a()
                   for k, g in cols.items()}
        self.assertEqual(classes, {"pilar_circ_30": "IfcCircleProfileDef", "pilar_L_40": "IfcLShapeProfileDef",
                                   "pilar_T_50": "IfcTShapeProfileDef"})
        other = bim.add_column(doc, np.array((0.0, 5.0, 0.0)), catalog.BY_KEY["pilar_circ_30"], 2.8)
        beam = bim.beams_between(doc, [cols["pilar_circ_30"], other], catalog.BY_KEY["viga_T_60"])[0]
        s, e, top, width, height = doc.ifc.beam_params(beam)
        self.assertAlmostEqual(float(np.linalg.norm((e - s)[:2])), 4.7)          # round faces: Ø30
        self.assertEqual((round(width, 6), round(height, 6)), (0.6, 0.5))
        thicker = dataclasses.replace(catalog.BY_KEY["pilar_L_40"], web=0.20)
        bim.save_type(doc, thicker, catalog.BY_KEY["pilar_L_40"])
        read = {s.key: s for s in project_types.read(doc.ifc)}
        self.assertEqual((read["pilar_L_40"].shape, round(read["pilar_L_40"].web, 6)), ("L", 0.2))
        area = ue.get_psets(doc.ifc.by_guid(cols["pilar_L_40"]))["Qto_ColumnBaseQuantities"]["CrossSectionArea"]
        self.assertAlmostEqual(area, 0.20 * (0.40 + 0.40 - 0.20))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class BeamSystems(unittest.TestCase):
    """0.97: three beams along Y in each bay of a 3 × 2 frame (evenly spaced, face to face, top at the bay's);
    laid again as a grid of 2 + 2 (the old ones replaced); an axis moved: laid again in the bay as it is."""

    def test_beam_system(self):
        doc = Document()
        bim.generate_grid(doc, [0.0, 5.0, 10.0], [0.0, 6.0])
        bim.columns_on_grid(doc, None, catalog.BY_KEY["pilar_30"], 2.8, doc.active_storey)
        bim.beams_between(doc, None, catalog.BY_KEY["viga_20x40"])
        made, skipped = bim.beam_system(doc, None, "y", "count", 3, catalog.BY_KEY["viga_15x30"])
        self.assertEqual((len(made), skipped), (6, 0))
        xs = sorted(round(float(doc.ifc.beam_params(b)[0][0]), 6) for b in made)
        self.assertEqual(xs, [1.3, 2.5, 3.7, 6.3, 7.5, 8.7])
        lengths = {round(float(np.linalg.norm((doc.ifc.beam_params(b)[1] - doc.ifc.beam_params(b)[0])[:2])), 6)
                   for b in made}
        self.assertEqual(lengths, {5.8})
        self.assertTrue(all(abs(doc.ifc.beam_params(b)[2] - 2.8) < 1e-9 for b in made))
        made, _ = bim.beam_system(doc, None, "grid", "count", 2, catalog.BY_KEY["viga_15x30"])
        self.assertEqual(len(made), 8)
        self.assertEqual(len(doc.ifc.systems_of([b for b in doc.ifc.beams_of(
            [g for g in doc.objects if doc.ifc.kind_of(g) == "column"])])), 8)     # (the first 6 gone)
        idx = {a.tag: k for k, a in enumerate(doc.grids)}
        k = idx["3"]
        axis = doc.grids[k]
        bim.move_grid_axes(doc, {k: ((axis.start[0] + 2.0, axis.start[1]), (axis.end[0] + 2.0, axis.end[1]))})
        right = sorted(round(float(doc.ifc.beam_params(b)[0][0]), 6) for b in made
                       if doc.ifc._params(doc.ifc.by_guid(b))["Sistema"].startswith("y")
                       and doc.ifc.beam_params(b)[0][0] > 5.0)
        self.assertEqual(right, [7.366667, 9.633333])            # axis 3 beyond the others' ends: 5,1 .. 11,9
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class ProposeStructure(unittest.TestCase):
    """0.98: a 12 × 8 m room with a wall across — 9 columns, 10 beams along the walls (the walls down to the
    beams), 9 footings; proposed again: replaced, not added; removed: none left, the walls back to 2,80."""

    def test_propose_and_remove(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        walls = [bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
                 for a, b in (((0.0, 0.0), (12.0, 0.0)), ((12.0, 0.0), (12.0, 8.0)), ((12.0, 8.0), (0.0, 8.0)),
                              ((0.0, 8.0), (0.0, 0.0)), ((6.0, 0.0), (6.0, 8.0)))]
        args = (6.0, catalog.BY_KEY["pilar_20"], catalog.BY_KEY["viga_15x30"], catalog.BY_KEY["sapata_80"])
        counts = bim.propose_structure(doc, None, *args)
        self.assertEqual(counts, {"columns": 9, "beams": 10, "footings": 9})
        self.assertEqual(sorted({round(doc.ifc.wall_params(w)[1], 6) for w in walls}), [2.5])   # 2,80 − 30 cm
        counts = bim.propose_structure(doc, None, *args)                     # again: the same, replaced
        self.assertEqual(len(doc.ifc.file.by_type("IfcColumn")), 9)
        self.assertEqual(len(doc.ifc.file.by_type("IfcBeam")), 10)
        self.assertEqual(sorted({round(doc.ifc.wall_params(w)[1], 6) for w in walls}), [2.5])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        self.assertTrue(bim.remove_proposal(doc))
        self.assertEqual(len(doc.ifc.file.by_type("IfcColumn")) + len(doc.ifc.file.by_type("IfcFooting")), 0)
        self.assertEqual(sorted({round(doc.ifc.wall_params(w)[1], 6) for w in walls}), [2.8])
        self.assertFalse(bim.remove_proposal(doc))
        doc.undo()
        self.assertEqual(len(doc.ifc.file.by_type("IfcColumn")), 9)


class ArchitectureTools(unittest.TestCase):
    """0.374 — the addon's inventory and the owner's study: a room separator bounds rooms (not slabs); «Identificar»
    makes a room in each closed space; the areas (net, gross); a niche (RECESS, not through); a floor finish
    (IfcCovering FLOORING); a gutter on a roof's eave; an elevator; a guard in a window's opening; a valid IFC."""

    def test_architecture_tools(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        walls = []
        for a, b in (((0.0, 0.0), (10.0, 0.0)), ((10.0, 0.0), (10.0, 6.0)), ((10.0, 6.0), (0.0, 6.0)),
                     ((0.0, 6.0), (0.0, 0.0))):
            walls.append(bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec))
        sep = bim.add_separator(doc, (4.0, 0.1), (4.0, 5.9))
        self.assertEqual(doc.ifc.kind_of(sep), "separator")
        made = bim.identify_rooms(doc)
        self.assertEqual(sorted(round(doc.ifc.space_info(g)["area"], 2) for g in made),
                         [round(3.895 * 5.8, 2), round(5.895 * 5.8, 2)])          # (the separator: a hairline 1 cm)
        self.assertEqual(bim.identify_rooms(doc), [])                            # (each space has its room now)
        self.assertAlmostEqual(bim.slab_wand(doc, (2.0, 3.0)).area, 9.8 * 5.8, places=4)   # (slabs: no separator)
        (name, _z, net, gross, n), = bim.storey_areas(doc)
        self.assertEqual((n, round(net, 2)), (2, round(9.79 * 5.8, 2)))
        self.assertAlmostEqual(gross, 10.2 * 6.2, delta=0.02)                  # (the corners joined by the cm)
        niche = bim.add_wall_niche(doc, walls[0], 2.0, 0.6, 0.5, 1.0, 0.10, (0.0, -1.0, 0.0))
        opening = doc.ifc.by_guid(niche)
        self.assertEqual(opening.PredefinedType, "RECESS")
        with self.assertRaises(ValueError):                                     # (as deep as the wall: refused)
            bim.add_wall_niche(doc, walls[0], 5.0, 0.6, 0.5, 1.0, 0.25, (0.0, -1.0, 0.0))
        floor = bim.add_flooring(doc, [(0.1, 0.1), (3.9, 0.1), (3.9, 5.9), (0.1, 5.9)], "madeira")
        covering = doc.ifc.by_guid(floor)
        self.assertEqual((covering.is_a(), covering.PredefinedType, doc.ifc.kind_of(floor)),
                         ("IfcCovering", "FLOORING", "flooring"))
        roof = bim.add_roof(doc, [(-0.1, -0.1), (10.1, -0.1), (10.1, 6.1), (-0.1, 6.1)], catalog.BY_KEY.get(
            "cobertura_telha", next(s for s in catalog.types() if s.kind == "roof")))
        eaves = bim.roof_eaves(doc, roof)
        self.assertEqual(len(eaves), 4)
        a, b, out = max(eaves, key=lambda e: float(np.linalg.norm(e[1] - e[0])))
        gutter = bim.add_gutter(doc, a, b, out)
        self.assertEqual((doc.ifc.kind_of(gutter), doc.ifc.by_guid(gutter).PredefinedType), ("gutter", "GUTTER"))
        # (0.384) under the eave's upper edge (not hanging under its foot); the one next to it joined at the corner,
        # both mitred: each reaches the corner's outer point; undone, the first one's end plain again
        roof_v = np.asarray(doc.get(roof).mesh.verts)
        gv = np.asarray(doc.get(gutter).mesh.verts)
        self.assertGreater(float(a[2]), float(roof_v[:, 2].min()) + 0.05)               # (the fascia's top)
        self.assertAlmostEqual(float(gv[:, 2].max()), float(a[2]) - 0.02, places=3)
        nxt = next(e for e in eaves if any(np.linalg.norm((p - q)[:2]) < 0.03 for p in e[:2] for q in (a, b))
                   and not np.allclose(e[2], out))
        joined = bim.gutter_joins(doc, *nxt)
        self.assertEqual([(g, kind) for _m, g, kind, _o in joined][0][0], gutter)
        second = bim.add_gutter(doc, *nxt)
        corner = next(p for p in (a, b) if any(np.linalg.norm((p - q)[:2]) < 0.03 for q in nxt[:2]))
        outer = corner[:2] + (out[:2] + nxt[2][:2]) * 0.15                            # (the corner's outer point)
        for g in (gutter, second):
            gv = np.asarray(doc.get(g).mesh.verts)[:, :2]
            self.assertLess(float(np.min(np.linalg.norm(gv - outer, axis=1))), 0.01, g)
        lines = {g: (ca, cb) for g, _a, _b, _o, ca, cb in doc.ifc.gutter_lines()}
        self.assertTrue(any(c is not None for c in lines[gutter]) and any(c is not None for c in lines[second]))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertTrue(all(c is None for c in {g: (ca, cb) for g, _a, _b, _o, ca, cb
                                                 in doc.ifc.gutter_lines()}[gutter]))
        doc.redo()
        lift = bim.add_elevator(doc, (12.0, 0.0))
        self.assertEqual(doc.ifc.by_guid(lift).PredefinedType, "ELEVATOR")
        frame = bim.wall_frame(doc, walls[2])
        window = bim.add_opening(doc, walls[2], catalog.OPENING_BY_KEY["janela_120"], frame, frame.x0 + 3.0, 1)
        guard = bim.opening_railing(doc, window)
        self.assertEqual(doc.ifc.kind_of(guard), "railing")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class Rooms(unittest.TestCase):
    """0.99: a room clicked inside the walls — IfcSpace on its storey, numbered, its area; the wall across moved:
    the room follows; deleted: the room takes the whole house; its name and finishes; outside: no room; undo."""

    def test_rooms(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        for a, b in (((0.0, 0.0), (10.0, 0.0)), ((10.0, 0.0), (10.0, 6.0)), ((10.0, 6.0), (0.0, 6.0)),
                     ((0.0, 6.0), (0.0, 0.0))):
            bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
        middle = bim.add_wall(doc, np.array((4.0, 0.0, 0.0)), np.array((4.0, 6.0, 0.0)), spec)
        self.assertIsNone(bim.add_room(doc, (12.0, 3.0)))                       # outside the walls
        room = bim.add_room(doc, (2.0, 3.0), "Quarto")
        other = bim.add_room(doc, (7.0, 3.0))
        info = doc.ifc.space_info(room)
        self.assertEqual((info["name"], info["number"], round(info["area"], 4)), ("Quarto", "1", round(3.8 * 5.8, 4)))
        self.assertEqual(doc.ifc.space_info(other)["number"], "2")
        self.assertEqual(doc.ifc.space_storey(room), doc.active_storey)
        m = np.eye(4)
        m[0, 3] = 1.0
        bim.transform_objects(doc, [middle], m, "mover")                       # the wall across 1 m to the right
        self.assertAlmostEqual(doc.ifc.space_info(room)["area"], 4.8 * 5.8)    # 0,10 .. 4,90
        self.assertAlmostEqual(doc.ifc.space_info(other)["area"], 4.8 * 5.8)   # 5,10 .. 9,90
        bim.delete(doc, [middle])
        self.assertAlmostEqual(doc.ifc.space_info(room)["area"], 9.8 * 5.8)    # the whole house now
        bim.set_room(doc, room, name="Sala comum", finishes={"FloorCovering": "Soalho", "CeilingCovering": "Gesso"})
        info = doc.ifc.space_info(room)
        self.assertEqual((info["name"], info["finishes"]["FloorCovering"]), ("Sala comum", "Soalho"))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        doc.undo()
        self.assertAlmostEqual(doc.ifc.space_info(room)["area"], 4.8 * 5.8)
        bim.remove_rooms(doc, [other])
        self.assertEqual(len(doc.ifc.spaces()), 1)


class SlabsByOutline(unittest.TestCase):
    """0.100: slabs by their outline — an L polygon (IfcArbitraryClosedProfileDef, its area); a true circle
    (IfcCircleProfileDef) and its radius changed; the magic wand inside four walls, to their inner and outer
    faces; a finish rests on the level and does not carry (Pset_SlabCommon.LoadBearing); a corner moved (one
    undo step), a rectangle edited by its corners becomes a polygon; the type changed keeps the outline and the
    top; Push/Pull's resize refused on a polygon; the IFC valid."""

    def test_slabs_by_outline(self):
        doc = Document()
        spec = catalog.BY_KEY["laje_12"]
        el = [(0.0, 0.0), (6.0, 0.0), (6.0, 3.0), (3.0, 3.0), (3.0, 5.0), (0.0, 5.0)]
        poly = bim.add_slab_outline(doc, el, 0.0, spec)
        info = doc.ifc.slab_outline(poly)
        self.assertEqual((info["shape"], info["function"]), ("poligono", "estrutural"))
        self.assertAlmostEqual(info["area"], 24.0)
        self.assertAlmostEqual(info["top"], 0.0)                                # a floor: its top at the level
        self.assertAlmostEqual(info["bottom"], -0.12)
        solid = doc.ifc._slab_solid(doc.ifc.by_guid(poly))
        self.assertEqual(solid.SweptArea.is_a(), "IfcArbitraryClosedProfileDef")
        lo, hi = bounds(doc, poly)
        self.assertTrue(np.allclose(lo, (0.0, 0.0, -0.12)) and np.allclose(hi, (6.0, 5.0, 0.0)))
        q = ue.get_psets(doc.ifc.by_guid(poly))["Qto_SlabBaseQuantities"]
        self.assertAlmostEqual(q["GrossArea"], 24.0)
        circle = bim.add_slab_circle(doc, (10.0, 2.0), 1.5, 0.0, spec, function="acabamento")
        info = doc.ifc.slab_outline(circle)
        self.assertEqual(doc.ifc._slab_solid(doc.ifc.by_guid(circle)).SweptArea.is_a(), "IfcCircleProfileDef")
        self.assertAlmostEqual(info["area"], np.pi * 1.5 ** 2)
        self.assertAlmostEqual(info["bottom"], 0.0)                             # a finish rests on the level
        self.assertIs(ue.get_psets(doc.ifc.by_guid(circle))["Pset_SlabCommon"]["LoadBearing"], False)
        bim.set_slab_radius(doc, circle, 2.0)
        self.assertAlmostEqual(doc.ifc.slab_outline(circle)["area"], np.pi * 4.0)
        lo, hi = bounds(doc, circle)
        self.assertAlmostEqual(hi[0] - lo[0], 4.0, places=2)
        bim.set_slab_function(doc, [circle], "estrutural")
        self.assertIs(ue.get_psets(doc.ifc.by_guid(circle))["Pset_SlabCommon"]["LoadBearing"], True)
        # the magic wand inside four walls (20 cm, axes on a 10 × 6 rectangle)
        wall = catalog.BY_KEY["parede_alv_20"]
        for a, b in (((20.0, 0.0), (30.0, 0.0)), ((30.0, 0.0), (30.0, 6.0)), ((30.0, 6.0), (20.0, 6.0)),
                     ((20.0, 6.0), (20.0, 0.0))):
            bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), wall)
        self.assertIsNone(bim.slab_wand(doc, (35.0, 3.0)))
        inner = bim.slab_wand(doc, (22.0, 3.0))
        self.assertAlmostEqual(inner.area, 9.8 * 5.8, places=4)
        outer = bim.slab_wand(doc, (22.0, 3.0), "exterior")
        self.assertAlmostEqual(outer.area, 10.2 * 6.2, places=3)
        wand = bim.add_slab_outline(doc, list(outer.exterior.coords)[:-1], 0.0, spec)
        self.assertAlmostEqual(doc.ifc.slab_outline(wand)["area"], 10.2 * 6.2, places=3)
        # a corner of the L moved: (3, 5) -> (3, 6); undo
        moved = list(el)
        moved[4] = (3.0, 6.0)
        bim.set_slab_outline(doc, poly, moved)
        self.assertAlmostEqual(doc.ifc.slab_outline(poly)["area"], 18.0 + 3 * (2 + 3) / 2)   # (its top side slants)
        self.assertAlmostEqual(doc.ifc.slab_outline(poly)["top"], 0.0)
        doc.undo()
        self.assertAlmostEqual(doc.ifc.slab_outline(poly)["area"], 24.0)
        with self.assertRaises(ValueError):
            bim.set_slab_outline(doc, poly, [(0.0, 0.0), (4.0, 4.0), (4.0, 0.0), (0.0, 4.0)])   # sides crossing
        with self.assertRaises(ValueError):
            bim.resize_slab(doc, poly, 0.0, 0.0, 8.0, 8.0)                      # (a polygon: by its outline)
        # a rectangle edited by its corners: a polygon now
        rect = bim.add_slab(doc, np.array((0.0, 10.0, 0.0)), 4.0, 3.0, spec)
        self.assertEqual(doc.ifc.slab_shape(rect), "retangulo")
        self.assertAlmostEqual(doc.ifc.slab_outline(rect)["area"], 12.0)
        bim.set_slab_outline(doc, rect, [(0.0, 10.0), (4.0, 10.0), (4.0, 13.0), (1.0, 13.0)])
        self.assertEqual(doc.ifc.slab_shape(rect), "poligono")
        self.assertAlmostEqual(doc.ifc.slab_outline(rect)["area"], 10.5)
        # another type: the outline stays, the top too
        bim.set_type(doc, poly, catalog.BY_KEY["laje_15"])
        info = doc.ifc.slab_outline(poly)
        self.assertAlmostEqual(info["area"], 24.0)
        self.assertAlmostEqual(info["top"], 0.0)
        self.assertAlmostEqual(info["thickness"], 0.15)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class WallLoops(unittest.TestCase):
    """0.102: walls round a 6 × 4 rectangle — by its outer face (inside it), its inner face (outside), its axis:
    four walls joined at the corners in one undo step; along an L slab's outline (six walls); a level face of a
    sketch gives its outline; a round slab or an upright face give none."""

    def test_wall_loops(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        rect = [(0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (6.0, 4.0, 0.0), (0.0, 4.0, 0.0)]

        def extent(guids):
            lo = np.min([bounds(doc, g)[0] for g in guids], axis=0)
            hi = np.max([bounds(doc, g)[1] for g in guids], axis=0)
            return lo, hi

        def plan_area(guids):
            return sum(doc.ifc.wall_params(g)[0] * doc.ifc.wall_params(g)[2] for g in guids)

        outer = bim.add_wall_loop(doc, rect, spec, 2.8, "right")                 # the rectangle = outer faces
        self.assertEqual(len(outer), 4)
        lo, hi = extent(outer)
        self.assertTrue(np.allclose(lo, (0, 0, 0)) and np.allclose(hi, (6, 4, 2.8)), (lo, hi))
        self.assertAlmostEqual(plan_area(outer), 6 * 4 - 5.6 * 3.6)
        self.assertTrue(all(doc.ifc.wall_joints(g) for g in outer))              # joined at the corners
        doc.undo()                                                               # one step: all four
        self.assertEqual(len(doc.ifc.file.by_type("IfcWall")), 0)
        inner = bim.add_wall_loop(doc, rect, spec, 2.8, "left")                  # the rectangle = inner faces
        lo, hi = extent(inner)
        self.assertTrue(np.allclose(lo, (-0.2, -0.2, 0)) and np.allclose(hi, (6.2, 4.2, 2.8)), (lo, hi))
        doc.undo()
        axis = bim.add_wall_loop(doc, rect[::-1], spec, 2.8, "axis")              # (clockwise: the same)
        lo, hi = extent(axis)
        self.assertTrue(np.allclose(lo, (-0.1, -0.1, 0)) and np.allclose(hi, (6.1, 4.1, 2.8)), (lo, hi))
        doc.undo()
        # along a slab's outline: an L
        slab = bim.add_slab_outline(doc, [(0, 0), (6, 0), (6, 3), (3, 3), (3, 5), (0, 5)], 0.0,
                                    catalog.BY_KEY["laje_12"])
        ring, z = bim.face_outline(doc, slab, 0, (1.0, 1.0, 0.0))
        self.assertEqual((len(ring), z), (6, 0.0))
        walls = bim.add_wall_loop(doc, [(x, y, z) for x, y in ring], spec, 2.8, "right")
        self.assertEqual(len(walls), 6)
        self.assertTrue(all(doc.ifc.wall_joints(g) for g in walls))
        circle = bim.add_slab_circle(doc, (20.0, 0.0), 2.0, 0.0, catalog.BY_KEY["laje_12"])
        self.assertIsNone(bim.face_outline(doc, circle, 0, (20.0, 0.0, 0.0)))
        # a level face of a sketch: its outline, counter-clockwise
        a = SketchObject("a", translation((30, 0, 0)), sg.rectangle_mesh(4.0, 3.0))
        doc.execute(AddObject(a))
        ring, z = bim.face_outline(doc, a.id, 0, (31.0, 1.0, 0.0))
        self.assertEqual(len(ring), 4)
        self.assertAlmostEqual(sum(ring[k][0] * ring[(k + 1) % 4][1] - ring[(k + 1) % 4][0] * ring[k][1]
                                   for k in range(4)) / 2, 12.0)                  # (counter-clockwise)
        box = box_object(doc, (40, 0, 0), 2.0, 2.0, 1.0)
        side = next(fi for fi in range(6) if np.allclose(box.mesh.face_normal(fi), (0, -1, 0)))
        self.assertIsNone(bim.face_outline(doc, box.id, side, (41.0, 0.0, 0.5)))  # upright: none
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class SplitAndCorner(unittest.TestCase):
    """0.104: a 10 m wall with a door and a window, joined at its end to another, split at 5 m — two 5 m walls,
    the door with the first, the window and the corner with the second; a split through the door refused; undo.
    Two walls apart, trimmed / extended to their corner: they meet and are joined there."""

    def test_split_and_corner(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        a = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((10.0, 0.0, 0.0)), spec)
        c = bim.add_wall(doc, np.array((10.0, 0.0, 0.0)), np.array((10.0, 5.0, 0.0)), spec,
                         prev=(a, np.array((1.0, 0.0, 0.0))))
        frame = bim.wall_frame(doc, a)
        door = bim.add_opening(doc, a, catalog.OPENING_BY_KEY["porta_80"], frame, 2.0, 1)
        window = bim.add_opening(doc, a, catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, a), 7.0, 1)
        length_a = doc.ifc.wall_params(a)[0]
        with self.assertRaises(ValueError):
            bim.split_wall(doc, a, 2.4)                                        # through the door
        new = bim.split_wall(doc, a, 5.0)
        self.assertAlmostEqual(doc.ifc.wall_params(a)[0], 5.0)
        self.assertAlmostEqual(doc.ifc.wall_params(new)[0], length_a - 5.0)
        self.assertEqual(doc.ifc.host_wall(door), a)
        hosts = {doc.ifc.host_wall(w.GlobalId) for w in doc.ifc.file.by_type("IfcWindow")}
        self.assertEqual(hosts, {new})
        self.assertEqual(len(doc.ifc.file.by_type("IfcDoor")), 1)
        self.assertEqual(len(doc.ifc.file.by_type("IfcWindow")), 1)
        self.assertIn(c, doc.ifc.joined_walls([new]))                         # the corner went with it
        self.assertNotIn(c, doc.ifc.joined_walls([a]))
        s, e, _t = doc.ifc.wall_axis(new)
        self.assertTrue(np.allclose(s, (5.0, 0.0, 0.0)))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertEqual(len(doc.ifc.file.by_type("IfcWall")), 2)
        self.assertAlmostEqual(doc.ifc.wall_params(a)[0], length_a)
        del window
        # to the corner: A along X stops short, B along Y starts above it
        p = bim.add_wall(doc, np.array((20.0, 0.0, 0.0)), np.array((24.0, 0.0, 0.0)), spec)
        q = bim.add_wall(doc, np.array((26.0, 1.0, 0.0)), np.array((26.0, 5.0, 0.0)), spec)
        bim.corner_walls(doc, p, (21.0, 0.0), q, (26.0, 4.0))
        ps, pe, _t = doc.ifc.wall_axis(p)
        qs, qe, _t = doc.ifc.wall_axis(q)
        self.assertTrue(np.allclose(ps, (20.0, 0.0, 0.0)) and np.allclose(qe, (26.0, 5.0, 0.0)))
        self.assertLess(np.linalg.norm((pe - np.array((26.0, 0.0, 0.0)))[:2]), 0.11)
        self.assertLess(np.linalg.norm((qs - np.array((26.0, 0.0, 0.0)))[:2]), 0.11)
        self.assertIn(q, doc.ifc.joined_walls([p]))
        lo = np.min([bounds(doc, g)[0] for g in (p, q)], axis=0)
        hi = np.max([bounds(doc, g)[1] for g in (p, q)], axis=0)
        self.assertTrue(np.allclose(lo[:2], (20.0, -0.1)) and np.allclose(hi[:2], (26.1, 5.0)), (lo, hi))
        with self.assertRaises(ValueError):                                    # parallel walls: no corner
            r = bim.add_wall(doc, np.array((30.0, 0.0, 0.0)), np.array((34.0, 0.0, 0.0)), spec)
            s2 = bim.add_wall(doc, np.array((30.0, 2.0, 0.0)), np.array((34.0, 2.0, 0.0)), spec)
            bim.corner_walls(doc, r, (31.0, 0.0), s2, (31.0, 2.0))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class Roofs(unittest.TestCase):
    """0.111: a hip roof over a 10 × 6 m house (walls 2,80 high): IfcRoof HIP_ROOF with its own body, its top over
    the walls' line at 2,80, 50 cm eaves, 30°: its ridge, its volume (the sloped area × the thickness), its
    quantities; made a gable roof, then flat; moved; (0.246) an L outline given a gable roof — two slopes over each
    arm —, (0.179) a hip roof — its volume, its ridges' height —; the IFC valid."""

    def test_roofs(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        for a, b in (((0.0, 0.0), (10.0, 0.0)), ((10.0, 0.0), (10.0, 6.0)), ((10.0, 6.0), (0.0, 6.0)),
                     ((0.0, 6.0), (0.0, 0.0))):
            bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
        outline = [(-0.1, -0.1), (10.1, -0.1), (10.1, 6.1), (-0.1, 6.1)]          # (the walls' outer line)
        self.assertAlmostEqual(bim.roof_eave(doc, outline), 2.8)
        roof = bim.add_roof(doc, outline, catalog.BY_KEY["laje_15"], "hip", 30.0, 0.5)
        e = doc.ifc.by_guid(roof)
        self.assertEqual((e.is_a(), e.PredefinedType), ("IfcRoof", "HIP_ROOF"))
        t, cos = math.tan(math.radians(30)), math.cos(math.radians(30))
        # (0.275) resting on the walls: its underside on their inner top edge (2,80 at 20 cm in) — its top over
        # their outer line 0,15/cos 30° − 0,20 · tan 30° higher
        eave = 2.8 + 0.15 / cos - 0.2 * t
        self.assertAlmostEqual(doc.ifc.roof_params(roof)["eave"], eave, places=9)
        self.assertAlmostEqual(doc.ifc.roof_underside_at(roof, (0.1, 3.0)), 2.8, places=6)
        lo, hi = bounds(doc, roof)
        self.assertTrue(np.allclose(lo[:2], (-0.6, -0.6)) and np.allclose(hi[:2], (10.6, 6.6)), (lo, hi))
        self.assertAlmostEqual(hi[2], eave + 3.1 * t, places=6)                   # (the ridge: 3,10 in)
        self.assertAlmostEqual(lo[2], eave - 0.5 * t - 0.15 / cos, places=6)      # (the eave's underside)
        area = 11.2 * 7.2
        self.assertAlmostEqual(doc.get(roof).mesh.volume(), area / cos * 0.15, places=4)
        q = ue.get_psets(e)["Qto_RoofBaseQuantities"]
        self.assertAlmostEqual(q["ProjectedArea"], area)
        self.assertAlmostEqual(q["GrossArea"], area / cos)
        self.assertAlmostEqual(doc.ifc.roof_height_at(roof, (5.0, 3.0)), eave + 3.1 * t)
        bim.set_roof(doc, roof, form="gable")
        self.assertEqual(e.PredefinedType, "GABLE_ROOF")
        self.assertAlmostEqual(bounds(doc, roof)[1][2], eave + 3.1 * t, places=6)  # (the ridge along the length)
        bim.set_roof(doc, roof, form="flat")                                    # (flat: on the walls' top)
        lo, hi = bounds(doc, roof)
        self.assertAlmostEqual(hi[2], 2.95)
        self.assertAlmostEqual(lo[2], 2.8)
        m = np.eye(4)
        m[:3, 3] = (20.0, 0.0, 0.0)
        bim.transform_objects(doc, [roof], m, "mover")
        lo, _hi = bounds(doc, roof)
        self.assertTrue(np.allclose(lo[:2], (19.4, -0.6)))
        el = [(0, 0), (6, 0), (6, 3), (3, 3), (3, 5), (0, 5)]
        # (0.246) a gable roof over the L: two slopes over each arm — its volume the grown L's area sloped × the
        # thickness, its ridges at the hip roof's, a gable at the end of each arm (full height at the walls' line)
        from shapely.geometry import Polygon
        gable_el = bim.add_roof(doc, [(x + 80.0, y) for x, y in el], catalog.BY_KEY["laje_15"], "gable", 30.0, 0.5,
                                eave=3.0)
        self.assertEqual(doc.ifc.by_guid(gable_el).PredefinedType, "GABLE_ROOF")
        self.assertAlmostEqual(doc.get(gable_el).mesh.volume(),
                               Polygon(el).buffer(0.5, join_style=2).area / cos * 0.15, places=4)
        self.assertAlmostEqual(bounds(doc, gable_el)[1][2], 3.0 + 1.5 * t, places=6)
        self.assertAlmostEqual(doc.ifc.roof_height_at(gable_el, (86.0, 1.5)), 3.0 + 1.5 * t, places=6)
        flat_el = bim.add_roof(doc, el, catalog.BY_KEY["laje_15"], "flat", overhang=0.0, eave=6.0)
        self.assertAlmostEqual(ue.get_psets(doc.ifc.by_guid(flat_el))["Qto_RoofBaseQuantities"]["ProjectedArea"], 24.0)
        # (0.179) a hip roof over an L, 50 cm eaves: its volume the grown L's area sloped × the thickness; its top at
        # the arms' ridges; made flat and hip again
        hip_el = bim.add_roof(doc, [(x + 40.0, y) for x, y in el], catalog.BY_KEY["laje_15"], "hip", 30.0, 0.5,
                              eave=3.0)
        from shapely.geometry import Polygon
        grown = Polygon(el).buffer(0.5, join_style=2).area
        self.assertAlmostEqual(doc.get(hip_el).mesh.volume(), grown / cos * 0.15, places=4)
        self.assertAlmostEqual(bounds(doc, hip_el)[1][2], 3.0 + 1.5 * t, places=6)
        self.assertAlmostEqual(doc.ifc.roof_height_at(hip_el, (44.5, 1.5)), 3.0 + 1.5 * t, places=6)
        bim.set_roof(doc, hip_el, form="flat")
        bim.set_roof(doc, hip_el, form="hip")
        self.assertEqual(doc.ifc.by_guid(hip_el).PredefinedType, "HIP_ROOF")
        # (0.190) a hip roof over an L with slanted sides (the straight skeleton): its volume the grown outline's
        # area sloped × the thickness (one face per side, no gap, no overlap); its height on a hip; a gable refused
        slant = [(x + 60.0, y) for x, y in [(0, 0), (10, 0), (10, 4), (5, 5), (3, 10), (0, 9)]]
        with self.assertRaises(ValueError):
            bim.add_roof(doc, slant, catalog.BY_KEY["laje_15"], "gable")
        any_l = bim.add_roof(doc, slant, catalog.BY_KEY["laje_15"], "hip", 30.0, 0.5, eave=3.0)
        grown = Polygon(slant).buffer(0.5, join_style=2).area
        self.assertAlmostEqual(doc.get(any_l).mesh.volume(), grown / cos * 0.15, places=3)
        self.assertAlmostEqual(doc.ifc.roof_height_at(any_l, (68.0, 2.0)), 3.0 + 2.0 * t, places=6)
        self.assertEqual(doc.ifc.by_guid(any_l).PredefinedType, "HIP_ROOF")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class CurtainPanels(unittest.TestCase):
    """0.181: a curtain wall 6 m long and 4,40 m high (four columns, two rows of 2,20 m): the cell under a point
    found; a glass door in the second bottom cell — no transom under it, its leaf to the floor, a handle each side —;
    an opaque cell (6 cm), an empty one; a door up in the top row refused, and in a cell too low; the Properties
    count them; valid IFC."""

    def test_panels(self):
        doc = Document()
        cw = bim.add_curtain_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), 4.4, 1.5, 2.2)
        rep = lambda: [r for r in doc.ifc.by_guid(cw).Representation.Representations      # noqa: E731
                       if r.RepresentationIdentifier == "Body"][0]
        self.assertEqual(len(rep().Items), 5 + 3 + 8)
        self.assertEqual(doc.ifc.curtain_cell_at(cw, (2.2, 0.0, 1.0)), (1, 0))
        bim.set_curtain_panel(doc, cw, (1, 0), "door")
        self.assertEqual(len(rep().Items), 5 + 4 + 8 + 2)                    # (the bottom transom in two, handles)
        v = doc.get(cw).mesh.verts
        under = v[(v[:, 0] > 1.5) & (v[:, 0] < 3.0) & (np.abs(v[:, 1]) < 0.03)]     # (the leaf, its handles)
        self.assertAlmostEqual(float(under[:, 2].min()), 0.0, places=6)      # (the leaf to the floor)
        bim.set_curtain_panel(doc, cw, (2, 1), "solid")
        dims = [sorted((i.SweptArea.XDim * doc.ifc.unit_scale, i.SweptArea.YDim * doc.ifc.unit_scale))
                for i in rep().Items if i.SweptArea.is_a("IfcRectangleProfileDef")]
        self.assertTrue(any(abs(d[0] - 0.06) < 1e-9 for d in dims))
        styled = [i for i in rep().Items if any(s.is_a("IfcStyledItem") for s in i.StyledByItem or ())]
        self.assertEqual(len(styled), 1)                                      # (the opaque one: grey in the IFC)
        bim.set_curtain_panel(doc, cw, (3, 1), "empty")
        self.assertEqual(len(rep().Items), 5 + 4 + 7 + 2)
        with self.assertRaises(ValueError):
            bim.set_curtain_panel(doc, cw, (0, 1), "door")
        low = bim.add_curtain_wall(doc, np.array((0.0, 5.0, 0.0)), np.array((6.0, 5.0, 0.0)), 3.0, 1.5, 1.5)
        with self.assertRaises(ValueError):
            bim.set_curtain_panel(doc, low, (0, 0), "door")
        self.assertEqual(doc.ifc.describe(cw)["params"]["panels"], {"solid": 1, "door": 1, "empty": 1})
        self.assertEqual(doc.ifc.validate(), [])


class ExtrudedRoofsIfc(unittest.TestCase):
    """0.180: over a 10 × 6 m house (walls 2,80): a barrel roof springing at 30°, 50 cm eaves — IfcRoof BARREL_ROOF,
    one extruded solid with true arcs; its volume the arc band × the length; its crown; the gable wall under it
    tied to it: its top the arc's underside; made a butterfly — its valley, the wall's top following it; an L
    refused; the IFC valid."""

    def test_extruded_roofs(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        walls = [bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
                 for a, b in (((0.0, 0.0), (10.0, 0.0)), ((10.0, 0.0), (10.0, 6.0)), ((10.0, 6.0), (0.0, 6.0)),
                              ((0.0, 6.0), (0.0, 0.0)))]
        outline = [(-0.1, -0.1), (10.1, -0.1), (10.1, 6.1), (-0.1, 6.1)]
        roof = bim.add_roof(doc, outline, catalog.BY_KEY["laje_15"], "barrel", 30.0, 0.5)
        e = doc.ifc.by_guid(roof)
        self.assertEqual(e.PredefinedType, "BARREL_ROOF")
        items = [i for r in e.Representation.Representations for i in r.Items]
        self.assertEqual(len(items), 1)
        self.assertTrue(any(s.is_a("IfcArcIndex") for s in items[0].SweptArea.OuterCurve.Segments))
        radius = 3.1 / math.sin(math.radians(30))
        half = math.asin(3.6 / radius)                                  # (the grown span's half, 3,60 m)
        band = half * (radius ** 2 - (radius - 0.15) ** 2)
        self.assertAlmostEqual(doc.get(roof).mesh.volume() / (band * 11.2), 1.0, delta=0.01)
        t = math.tan(math.radians(30))
        eave = 2.8 + 0.15 / math.cos(math.radians(30)) - 0.2 * t          # (0.275: resting on the walls)
        crown = eave + radius * (1 - math.cos(math.radians(30)))
        self.assertAlmostEqual(bounds(doc, roof)[1][2], crown, delta=0.002)          # (the arc drawn in pieces)
        self.assertAlmostEqual(doc.ifc.roof_height_at(roof, (5.0, 3.0)), crown, places=6)
        bim.attach_top(doc, [walls[3]], roof)                            # (the gable wall at x = 0)
        self.assertAlmostEqual(float(doc.get(walls[3]).mesh.verts[:, 2].max()), crown - 0.15, delta=0.01)
        bim.set_roof(doc, roof, form="butterfly")
        self.assertEqual(e.PredefinedType, "BUTTERFLY_ROOF")
        self.assertAlmostEqual(doc.ifc.roof_height_at(roof, (5.0, 3.0)), eave - 3.1 * t, places=6)
        top = doc.get(walls[3]).mesh.verts
        middle = top[np.abs(top[:, 1] - 3.0) < 0.15][:, 2].max()
        self.assertAlmostEqual(float(middle), eave - 3.1 * t - 0.15 / math.cos(math.radians(30)), delta=0.02)
        with self.assertRaises(ValueError):
            bim.add_roof(doc, [(0, 0), (6, 0), (6, 3), (3, 3), (3, 5), (0, 5)], catalog.BY_KEY["laje_15"], "barrel")
        self.assertEqual(doc.ifc.validate(), [])


class Ceilings(unittest.TestCase):
    """0.118: the ceiling of a 10 × 6 m house's room (its walls' inner faces, a column a hole) at 2,60: IfcCovering
    CEILING of gypsum, its area; made of 60 × 60 tiles (cut round the edges, the joints between them: less than
    the area); 2,50 now; mirrored; the IFC valid."""

    def test_ceilings(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        for a, b in (((0.0, 0.0), (10.0, 0.0)), ((10.0, 0.0), (10.0, 6.0)), ((10.0, 6.0), (0.0, 6.0)),
                     ((0.0, 6.0), (0.0, 0.0))):
            bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
        bim.add_column(doc, np.array((5.0, 3.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        region = bim.slab_wand(doc, (2.0, 2.0), "interior")
        ceiling = bim.add_ceiling(doc, list(region.exterior.coords)[:-1], 2.6,
                                  holes=[list(h.coords)[:-1] for h in region.interiors])
        e = doc.ifc.by_guid(ceiling)
        self.assertEqual((e.is_a(), e.PredefinedType), ("IfcCovering", "CEILING"))
        lo, hi = bounds(doc, ceiling)
        self.assertAlmostEqual(lo[2], 2.6)
        area = 9.8 * 5.8 - 0.09
        self.assertAlmostEqual(ue.get_psets(e)["Qto_CoveringBaseQuantities"]["GrossArea"], area, places=4)
        self.assertAlmostEqual(doc.get(ceiling).mesh.volume(), area * 0.0125, places=5)
        bim.set_ceiling(doc, ceiling, style="tiles")
        vol = doc.get(ceiling).mesh.volume()
        self.assertLess(vol, area * 0.015)                                     # (the joints)
        self.assertGreater(vol, area * 0.015 * 0.95)
        self.assertGreater(len(e.Representation.Representations[0].Items), 150)
        bim.set_ceiling(doc, ceiling, height=2.5)
        self.assertAlmostEqual(bounds(doc, ceiling)[0][2], 2.5)
        bim.mirror_objects(doc, [ceiling], (20.0, 0.0), (20.0, 1.0))
        lo, hi = bounds(doc, ceiling)
        self.assertTrue(lo[0] > 29.9 and hi[0] < 40.0, (lo, hi))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class WallFinishesAndLights(unittest.TestCase):
    """0.119: tiles up to 2,10 on a face of a 5 m wall: IfcCovering CLADDING of ceramic tile, tied to the wall
    (IfcRelCoversBldgElements), 1 cm on that face, its area; a door put in the wall: cut round it; the wall 1 m
    longer, then moved: the tiles follow; copied: the copy's own tiles, tied to the copy; the wall deleted: its
    tiles too. A ceiling with a shadow gap and a bulkhead; a light set in it, another under the bulkhead. The IFC
    valid."""

    def test_wall_finishes(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        frame = bim.wall_frame(doc, wall)
        tiles = bim.add_cladding(doc, wall, -1, "azulejo", 2.1)
        e = doc.ifc.by_guid(tiles)
        self.assertEqual((e.is_a(), e.PredefinedType), ("IfcCovering", "CLADDING"))
        self.assertEqual([r.RelatingBuildingElement.GlobalId for r in e.CoversElements], [wall])
        self.assertEqual(ue.get_material(e).Name, "Azulejo cerâmico")
        lo, hi = bounds(doc, tiles)
        self.assertTrue(np.allclose(lo, (0.0, frame.y0 - 0.01, 0.0)) and np.allclose(hi, (5.0, frame.y0, 2.1)), (lo, hi))
        area = lambda: ue.get_psets(e)["Qto_CoveringBaseQuantities"]["NetArea"]    # noqa: E731
        self.assertAlmostEqual(area(), 5.0 * 2.1)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, 1.0, -1)
        self.assertLess(area(), 5.0 * 2.1 - 1.5)
        self.assertAlmostEqual(doc.get(tiles).mesh.volume(), area() * 0.01, places=5)
        bim.resize_wall(doc, wall, at_end=1.0)
        self.assertAlmostEqual(bounds(doc, tiles)[1][0], 6.0)
        m = np.eye(4)
        m[:3, 3] = (0.0, 3.0, 0.0)
        bim.transform_objects(doc, [wall], m, "mover")
        lo, hi = bounds(doc, tiles)
        self.assertTrue(np.allclose((lo[1], hi[1]), (3.0 + frame.y0 - 0.01, 3.0 + frame.y0)), (lo, hi))
        made = bim.copy_objects(doc, [wall], [translation((0.0, 5.0, 0.0))], "copiar")
        copies = doc.ifc.claddings_of(made)
        self.assertEqual(len(copies), 1)
        (copy, copied_wall), = copies.items()
        self.assertEqual([r.RelatingBuildingElement.GlobalId for r in doc.ifc.by_guid(copy).CoversElements],
                         [copied_wall])
        self.assertAlmostEqual(bounds(doc, copy)[0][1], 8.0 + frame.y0 - 0.01)
        bim.set_cladding(doc, tiles, height=1.2, finish="pedra")
        self.assertAlmostEqual(bounds(doc, tiles)[1][2], 1.2)
        self.assertAlmostEqual(bounds(doc, tiles)[0][1], 3.0 + frame.y0 - 0.03)
        new = bim.split_wall(doc, wall, 3.0)                    # (both parts keep it)
        (part,) = doc.ifc.claddings_of([new])
        self.assertTrue(np.allclose([bounds(doc, part)[0][0], bounds(doc, part)[1][0]], (3.0, 6.0)))
        self.assertAlmostEqual(bounds(doc, tiles)[1][0], 3.0)
        bim.merge_walls(doc, wall, new)                         # (one again)
        self.assertIsNone(doc.ifc.by_guid(part))
        self.assertAlmostEqual(bounds(doc, tiles)[1][0], 6.0)
        bim.delete(doc, [wall])
        self.assertIsNone(doc.ifc.by_guid(tiles))
        self.assertIsNotNone(doc.ifc.by_guid(copy))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_ceiling_gap_bulkhead_and_lights(self):
        doc = Document()
        outline = [(0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0)]
        ceiling = bim.add_ceiling(doc, outline, 2.6, gap=0.02, bulkhead=(0.5, 0.3))
        e = doc.ifc.by_guid(ceiling)
        lo, hi = bounds(doc, ceiling)
        self.assertTrue(np.allclose(lo, (0.02, 0.02, 2.3)) and np.allclose(hi[:2], (5.98, 3.98)), (lo, hi))
        self.assertAlmostEqual(ue.get_psets(e)["Qto_CoveringBaseQuantities"]["GrossArea"], 5.96 * 3.96, places=4)
        self.assertEqual(len(e.Representation.Representations[0].Items), 2)
        self.assertAlmostEqual(doc.ifc.ceiling_z_at((3.0, 2.0)), 2.6)
        self.assertAlmostEqual(doc.ifc.ceiling_z_at((0.2, 2.0)), 2.3)
        light = bim.add_light(doc, (3.0, 2.0), "panel")
        down = bim.add_light(doc, (0.2, 2.0), "downlight")
        self.assertEqual((doc.ifc.by_guid(light).is_a(), doc.ifc.by_guid(light).PredefinedType),
                         ("IfcLightFixture", "POINTSOURCE"))
        lo, hi = bounds(doc, light)
        self.assertTrue(np.allclose(lo, (2.7025, 1.7025, 2.595)) and np.allclose(hi, (3.2975, 2.2975, 2.655)), (lo, hi))
        self.assertAlmostEqual(bounds(doc, down)[0][2], 2.295)
        bim.set_ceiling(doc, ceiling, bulkhead=(0.0, 0.0), gap=0.0)
        self.assertEqual(len(e.Representation.Representations[0].Items), 1)
        self.assertAlmostEqual(bounds(doc, ceiling)[0][2], 2.6)
        bim.mirror_objects(doc, [light], (10.0, 0.0), (10.0, 1.0))
        self.assertAlmostEqual(float(np.mean(bounds(doc, light), axis=0)[0]), 17.0)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class CurtainWalls(unittest.TestCase):
    """0.117: a 6 m curtain wall 3 m high, mullions up to 1,50 apart (4 bays: 5 mullions), transoms up to 1,00 (3
    rows: 4 transoms) and 12 glass panels: IfcCurtainWall, aluminium and glass, its quantities; 7,5 m long now (5
    bays); moved and mirrored; the IFC valid."""

    def test_curtain_walls(self):
        doc = Document()
        cw = bim.add_curtain_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), 3.0, 1.5, 1.0)
        e = doc.ifc.by_guid(cw)
        self.assertEqual(e.is_a(), "IfcCurtainWall")
        self.assertEqual(len(e.Representation.Representations[0].Items), 5 + 4 + 12)
        lo, hi = bounds(doc, cw)
        self.assertTrue(np.allclose(lo, (0.0, -0.075, 0.0)) and np.allclose(hi, (6.0, 0.075, 3.0)), (lo, hi))
        mats = ue.get_material(e)
        self.assertEqual(mats.is_a(), "IfcMaterialConstituentSet")
        self.assertEqual(sorted(c.Material.Name for c in mats.MaterialConstituents), ["Alumínio", "Vidro"])
        q = ue.get_psets(e)["Qto_CurtainWallQuantities"]
        self.assertAlmostEqual(q["GrossSideArea"], 18.0)
        bim.set_curtain_wall(doc, cw, length=7.5)
        self.assertEqual(len(e.Representation.Representations[0].Items), 6 + 4 + 15)
        m = np.eye(4)
        m[:3, 3] = (0.0, 5.0, 0.0)
        bim.transform_objects(doc, [cw], m, "mover")
        bim.mirror_objects(doc, [cw], (10.0, 0.0), (10.0, 1.0))
        lo, hi = bounds(doc, cw)
        self.assertTrue(np.allclose((lo[0], hi[0]), (12.5, 20.0)) and np.allclose((lo[1], hi[1]), (4.925, 5.075)),
                        (lo, hi))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class SpiralAndVStairs(unittest.TestCase):
    """0.116: a V stair (a U with its flights side by side: 2 m wide in all) and a spiral one (SPIRAL_STAIR: its
    column as high as the rise, 15 wedge treads of true arcs round it, within its radius), its railing along its
    outer edge; the IFC valid."""

    def test_spiral_and_v(self):
        from arqbim.core import stairs as core_stairs
        doc = Document()
        slab = catalog.BY_KEY["laje_15"]
        v = bim.add_stair(doc, np.array((0.0, 0.0, 0.0)), (1.0, 0.0), slab, "v", 2.8)
        lo, hi = bounds(doc, v)
        self.assertAlmostEqual(hi[1] - lo[1], 2.0)
        self.assertEqual(doc.ifc.by_guid(v).PredefinedType, "HALF_TURN_STAIR")
        sp = bim.add_stair(doc, np.array((10.0, 0.0, 0.0)), (1.0, 0.0), slab, "spiral", 2.8, width=0.9, going=0.25)
        e = doc.ifc.by_guid(sp)
        self.assertEqual(e.PredefinedType, "SPIRAL_STAIR")
        self.assertEqual(len(e.Representation.Representations[0].Items), 1 + 15)
        lo, hi = bounds(doc, sp)
        self.assertAlmostEqual(hi[2], 2.8, places=6)                              # (the column)
        centre = np.array((10.0, core_stairs.COLUMN + 0.45))                     # (left of the foot)
        outer = core_stairs.COLUMN + 0.9
        corners = np.array([lo[:2], hi[:2]])
        self.assertTrue(np.all(np.abs(corners - centre) <= outer + 1e-6), (lo, hi))
        self.assertEqual(ue.get_psets(e)["Pset_StairCommon"]["NumberOfTreads"], 15)
        rails = bim.stair_railings(doc, sp)
        self.assertEqual(len(rails), 1)
        _lo, hi = bounds(doc, rails[0])
        self.assertAlmostEqual(hi[2], 2.8 + 0.9, delta=0.02)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class Railings(unittest.TestCase):
    """0.115: a railing along a level path (4 + 3 m, 1,00 high, bars): IfcRailing GUARDRAIL, its length, its height;
    made glass; the railings on a stair's two sides (sloping with it, 0,90 over its nosings); one round an opening
    cut through a slab (closed); mirrored; the IFC valid."""

    def test_railings(self):
        doc = Document()
        r = bim.add_railing(doc, [(0, 0, 0), (4, 0, 0), (4, 3, 0)], 1.0, "bars")
        e = doc.ifc.by_guid(r)
        self.assertEqual((e.is_a(), e.PredefinedType), ("IfcRailing", "GUARDRAIL"))
        lo, hi = bounds(doc, r)
        self.assertAlmostEqual(hi[2], 1.0, places=6)
        self.assertAlmostEqual(ue.get_psets(e)["Qto_RailingBaseQuantities"]["Length"] * doc.ifc.unit_scale, 7.0)
        bim.set_railing(doc, r, style="glass")                               # (a 0.115 style: its preset, 0.258)
        self.assertEqual(doc.ifc.railing_params(r)["type"], "vidro_grampos")
        stair = bim.add_stair(doc, np.array((10.0, 0.0, 0.0)), (1.0, 0.0), catalog.BY_KEY["laje_15"], "straight", 2.8)
        sides = bim.stair_railings(doc, stair)
        self.assertEqual(len(sides), 2)
        for g in sides:
            lo, hi = bounds(doc, g)
            self.assertAlmostEqual(hi[2], 2.8 + 0.9, delta=0.01)                  # (0,90 over the top nosing;
            self.assertAlmostEqual(lo[2], 0.0, delta=0.01)                         #  0.282: down to the floor)
        slab = bim.add_slab(doc, np.array((20.0, 0.0, 3.0)), 6.0, 4.0, catalog.BY_KEY["laje_15"])
        bim.add_vertical_opening(doc, slab, (22.0, 1.0), (24.0, 2.0))
        round_ = bim.void_railing(doc, slab, (21.8, 1.5))
        self.assertIsNotNone(round_)
        self.assertTrue(doc.ifc.railing_params(round_)["closed"])
        self.assertAlmostEqual(ue.get_psets(doc.ifc.by_guid(round_))["Qto_RailingBaseQuantities"]["Length"]
                               * doc.ifc.unit_scale, 6.0)
        lo, _hi = bounds(doc, round_)
        self.assertAlmostEqual(lo[2], 3.15, places=6)                              # (on the slab's top)
        bim.mirror_objects(doc, [r], (10.0, 0.0), (10.0, 1.0))
        lo, hi = bounds(doc, r)
        self.assertTrue(lo[0] > 15.9 and hi[0] < 20.1, (lo, hi))
        el = bim.add_stair(doc, np.array((30.0, 0.0, 0.0)), (1.0, 0.0), catalog.BY_KEY["laje_15"], "l", 2.8)
        both = bim.stair_railings(doc, el)                                     # (0.261: one each side, all the way)
        self.assertEqual(len(both), 2)
        for g in both:
            lo, hi = bounds(doc, g)
            self.assertAlmostEqual(hi[2], 2.8 + 0.9, delta=0.01)
            self.assertAlmostEqual(lo[2], 0.0, delta=0.01)                         # (0.282: its extension's foot)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class RailingTypesIfc(unittest.TestCase):
    """0.258: a railing of each of the program's types along a 3 m + 2 m path: an IfcRailing of an IfcRailingType
    (GUARDRAIL; the wall handrail HANDRAIL) with its fields in ArqSynth_Guarda and a constituent set of its
    materials, each piece styled with its material; two railings of one type: one IfcRailingType; a railing's own
    height; a type changed (its bars further apart, renamed): its railings made again, fewer bars; an old railing
    (0.115, Estilo glass) read as its preset; the IFC valid."""

    def test_types(self):
        from arqbim.core import railing_types as core_rail
        doc = Document()
        path = [(0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (3.0, 2.0, 0.0)]
        made = {}
        for k, key in enumerate(core_rail.PRESETS):
            shifted = [(x, y + 4.0 * k, z) for x, y, z in path]
            made[key] = bim.add_railing(doc, shifted, None, key)
            e = doc.ifc.by_guid(made[key])
            tp = ue.get_type(e)
            self.assertIsNotNone(tp, key)
            self.assertEqual(ue.get_psets(tp)["ArqSynth_Guarda"]["Chave"], key)
            self.assertEqual(tp.PredefinedType, "HANDRAIL" if key == "corrimao" else "GUARDRAIL")
            self.assertTrue(ue.get_material(tp).is_a("IfcMaterialConstituentSet"))
            items = e.Representation.Representations[0].Items
            self.assertTrue(items)
            self.assertTrue(all(item.StyledByItem for item in items), key)
            lo, hi = bounds(doc, made[key])
            self.assertAlmostEqual(hi[2], core_rail.PRESETS[key].height, delta=0.02, msg=key)
        twice = bim.add_railing(doc, [(0.0, -5.0, 0.0), (2.0, -5.0, 0.0)], 1.10, "barras")
        self.assertEqual(len([t for t in doc.ifc.file.by_type("IfcRailingType")
                              if ue.get_psets(t)["ArqSynth_Guarda"]["Chave"] == "barras"]), 1)
        self.assertAlmostEqual(bounds(doc, twice)[1][2], 1.10, places=6)              # (its own height)
        before = len(doc.ifc.by_guid(made["barras"]).Representation.Representations[0].Items)
        wider = dataclasses.replace(doc.ifc.railing_type("barras"), gap=0.20, name_pt="Barras largas")
        changed = bim.set_railing_type(doc, wider)
        self.assertEqual(set(changed), {made["barras"], twice})
        after = len(doc.ifc.by_guid(made["barras"]).Representation.Representations[0].Items)
        self.assertLess(after, before)
        self.assertEqual(ue.get_type(doc.ifc.by_guid(made["barras"])).Name, "Barras largas")
        self.assertIn(("barras", "Barras largas"), doc.ifc.railing_type_choices())
        old = doc.ifc.by_guid(made["travessas"])
        doc.ifc._set_params(old, {"Tipo": None, "Estilo": "glass"})
        self.assertEqual(doc.ifc.railing_params(old.GlobalId)["rtype"].key, "vidro_grampos")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class BlockRoofIfc(unittest.TestCase):
    """0.262: four walls 10 × 6 m and a roof by blocks over them — one hip block on the walls' line (30°, 50 cm
    overhang): an IfcRoof HIP_ROOF resting on the walls (its eave 2,80), 1,73 m up at its middle, its volume its
    plan × its upright thickness; a gable block across it: FREEFORM, its blocks kept, the top the higher of the two;
    a wall's top tied to it; all its slopes made 40°: higher, the wall follows; mirrored; saved and opened again;
    valid IFC; undone."""

    def test_block_roof(self):
        from arqbim.core import roof_blocks as rb
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        corners = [(0.0, 0.0), (10.0, 0.0), (10.0, 6.0), (0.0, 6.0)]
        walls = [bim.add_wall(doc, np.array(corners[k] + (0.0,)), np.array(corners[(k + 1) % 4] + (0.0,)), spec)
                 for k in range(4)]
        t30 = math.tan(math.radians(30))
        roof = bim.add_block_roof(doc, rb.make(5.0, 3.0, 0.0, 10.2, 6.2, "hip", 30.0, 0.5),
                                  catalog.BY_KEY["laje_15"])
        e = doc.ifc.by_guid(roof)
        self.assertEqual((e.is_a(), e.PredefinedType), ("IfcRoof", "HIP_ROOF"))
        p = doc.ifc.roof_params(roof)
        self.assertEqual((p["form"], len(p["blocks"])), ("blocks", 1))
        self.assertAlmostEqual(p["eave"], 2.8, places=6)
        seat = 0.15 / math.cos(math.radians(30)) - 0.2 * t30               # (0.275: each water resting on the walls)
        self.assertTrue(all(abs(e - seat) < 1e-6 for e in p["blocks"][0].eave), p["blocks"][0].eave)
        self.assertAlmostEqual(doc.ifc.roof_height_at(roof, (5.0, 3.0)), 2.8 + seat + 3.1 * t30, places=6)
        plan = 11.2 * 7.2
        self.assertAlmostEqual(doc.get(roof).mesh.volume(), plan * 0.15 / math.cos(math.radians(30)), places=4)
        q = ue.get_psets(e)["Qto_RoofBaseQuantities"]
        self.assertAlmostEqual(q["ProjectedArea"], plan, places=4)
        bim.add_roof_block(doc, roof, rb.make(8.0, 6.0, 0.0, 4.0, 8.0, "gable", 30.0, 0.5))
        e = doc.ifc.by_guid(roof)
        self.assertEqual(e.PredefinedType, "FREEFORM")
        blocks = doc.ifc.roof_params(roof)["blocks"]
        self.assertEqual(len(blocks), 2)
        top = rb.height_at(blocks, 8.0 - 5.0, 8.0 - 3.0)                     # (in its own frame: from (5, 3))
        self.assertAlmostEqual(doc.ifc.roof_height_at(roof, (8.0, 8.0)), 2.8 + top, places=6)
        north = walls[2]
        bim.attach_top(doc, [north], roof)
        lo, hi = bounds(doc, north)
        self.assertGreater(hi[2], 2.8 + 0.5)                                 # (a gable under the cross block)
        before = doc.ifc.roof_height_at(roof, (5.0, 3.0))
        bim.set_roof(doc, roof, slope=40.0)
        self.assertTrue(all(s == 40.0 for b in doc.ifc.roof_params(roof)["blocks"] for s in b.slope))
        self.assertGreater(doc.ifc.roof_height_at(roof, (5.0, 3.0)), before)
        self.assertGreater(bounds(doc, north)[1][2], hi[2])                  # (the wall followed)
        height = doc.ifc.roof_height_at(roof, (8.0, 8.0))
        bim.mirror_objects(doc, [roof], (20.0, 0.0), (20.0, 1.0))           # (about x = 20)
        self.assertAlmostEqual(doc.ifc.roof_height_at(roof, (32.0, 8.0)), height, places=6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "blocos.ifc")
            doc.save(path)
            other = Document()
            other.open(path)
            self.assertEqual(len(other.ifc.roof_params(roof)["blocks"]), 2)
            self.assertAlmostEqual(other.ifc.roof_height_at(roof, (32.0, 8.0)), height, places=6)
        while doc.can_undo():
            doc.undo()
        self.assertEqual(len(doc.ifc.file.by_type("IfcRoof")), 0)

    def test_edges_measured(self):
        """0.265: a hip roof by blocks 10,2 × 6,2 m over the walls' line, 50 cm overhang, 30°: its edges' lengths
        in the IFC (ArqSynth_ArestasCobertura) — 36,80 m of eaves round the grown rectangle, a 4 m ridge, four hips
        —, in its Properties and in the Roofs schedule with its sloped and plan areas; a gable block across it:
        valleys."""
        from arqbim.core import roof_blocks as rb
        from arqbim.model import schedules
        doc = Document()
        roof = bim.add_block_roof(doc, rb.make(5.0, 3.0, 0.0, 10.2, 6.2, "hip", 30.0, 0.5),
                                  catalog.BY_KEY["laje_15"])
        t30 = math.tan(math.radians(30))
        s = doc.ifc.unit_scale                                               # (the file's lengths: its unit)
        q = ue.get_psets(doc.ifc.by_guid(roof))["ArqSynth_ArestasCobertura"]
        self.assertAlmostEqual(q["Beirados"] * s, 36.8, places=4)
        self.assertAlmostEqual(q["Cumeeiras"] * s, 4.0, places=4)
        self.assertAlmostEqual(q["Rincoes"] * s, 4 * math.sqrt(2 * 3.6 ** 2 + (3.6 * t30) ** 2), places=4)
        self.assertAlmostEqual(doc.ifc.describe(roof)["params"]["edges"]["eave"], 36.8, places=4)
        row = schedules.rows(doc, "roofs")[0]
        self.assertAlmostEqual(row["eaves"], 36.8, places=4)
        self.assertAlmostEqual(row["projected"], 11.2 * 7.2, places=4)
        self.assertAlmostEqual(row["area"], 11.2 * 7.2 / math.cos(math.radians(30)), places=4)
        self.assertAlmostEqual(row["volume"], row["area"] * 0.15, places=4)
        bim.add_roof_block(doc, roof, rb.make(5.0, 6.0, 0.0, 3.0, 8.0, "gable", 30.0, 0.5))
        q = ue.get_psets(doc.ifc.by_guid(roof))["ArqSynth_ArestasCobertura"]
        self.assertGreater(q["Laros"], 0.0)

    def test_blocks_in_the_plan(self):
        """0.263: a roof by blocks' blocks read in the plan as they were given; the roof turned 90° about the
        origin: its blocks turned with it; a block changed in the plan (a water on its north side) and given back:
        the roof made again with it, one undo step."""
        from arqbim.core import roof_blocks as rb
        doc = Document()
        main = rb.make(5.0, 3.0, 0.0, 10.2, 6.2, "hip", 30.0, 0.5)
        roof = bim.add_block_roof(doc, main, catalog.BY_KEY["laje_15"])
        bim.add_roof_block(doc, roof, rb.make(8.0, 7.05, 0.0, 4.2, 6.1, "gable", 30.0, 0.5))
        world = doc.ifc.roof_blocks_world(roof)
        self.assertEqual([(round(b.cx, 6), round(b.cy, 6), round(b.angle, 6)) for b in world],
                         [(5.0, 3.0, 0.0), (8.0, 7.05, 0.0)])
        turn = np.eye(4)
        turn[:2, :2] = ((0.0, -1.0), (1.0, 0.0))
        bim.transform_objects(doc, [roof], turn, "rodar")
        world = doc.ifc.roof_blocks_world(roof)
        self.assertEqual([(round(b.cx, 6), round(b.cy, 6), round(b.angle, 6) % 360) for b in world],
                         [(-3.0, 5.0, 90.0), (-7.05, 8.0, 90.0)])
        before = doc.ifc.roof_height_at(roof, (-9.9, 8.0))
        wing = rb.replace(world[1], water=(True, True, False, True))
        bim.set_roof_blocks(doc, roof, [world[0], wing], world=True)
        self.assertEqual(doc.ifc.roof_params(roof)["blocks"][1].water, (True, True, False, True))
        self.assertEqual([(round(b.cx, 6), round(b.cy, 6)) for b in doc.ifc.roof_blocks_world(roof)],
                         [(-3.0, 5.0), (-7.05, 8.0)])
        self.assertLess(doc.ifc.roof_height_at(roof, (-9.9, 8.0)), before)   # (a hip end: lower near its end)
        doc.undo()
        self.assertEqual(doc.ifc.roof_params(roof)["blocks"][1].water, (False, True, False, True))

    def test_block_fitted_to_walls(self):
        """A block drawn on the walls' axes (0..10 × 0..6, walls 20 cm) taken out to their outer faces
        (−0,1..10,1 × −0,1..6,1), one on their inner faces too; one drawn already on the outer faces, or a porch
        against the walls (outside them), kept as drawn."""
        from arqbim.core import roof_blocks as rb
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        corners = [(0.0, 0.0), (10.0, 0.0), (10.0, 6.0), (0.0, 6.0)]
        for k in range(4):
            bim.add_wall(doc, np.array(corners[k] + (0.0,)), np.array(corners[(k + 1) % 4] + (0.0,)), spec)
        fitted = bim.fit_block_to_walls(doc, rb.make(5.0, 3.0, 0.0, 10.0, 6.0, "hip"))
        self.assertEqual(tuple(round(v, 6) for v in (fitted.cx, fitted.cy, fitted.width, fitted.depth)),
                         (5.0, 3.0, 10.2, 6.2))
        inner = bim.fit_block_to_walls(doc, rb.make(5.0, 3.0, 0.0, 9.8, 5.8, "hip"))      # (on the inner faces)
        self.assertAlmostEqual(inner.width, 10.2, places=6)
        drawn = rb.make(5.0, 3.0, 0.0, 10.2, 6.2, "hip")
        self.assertIs(bim.fit_block_to_walls(doc, drawn), drawn)
        porch = rb.make(5.0, -1.1, 0.0, 4.0, 2.0, "shed")                   # (against the wall's outer face)
        self.assertIs(bim.fit_block_to_walls(doc, porch), porch)
        only_east = bim.fit_block_to_walls(doc, rb.make(5.0, 3.0, 0.0, 10.0, 6.0, "hip"), only=(1,))   # (0.264)
        self.assertEqual(tuple(round(v, 6) for v in (only_east.cx - only_east.width / 2,
                                                     only_east.cx + only_east.width / 2, only_east.depth)),
                         (0.0, 10.1, 6.0))


class IfcDataIfc(unittest.TestCase):
    """0.266: each element with its standard IFC set — a wall drawn: Pset_WallCommon's every property listed (the
    phase apart), its Reference its type's name, by the program; a fire rating written by hand kept as the user's;
    its Reference written by hand kept when its type changes, cleared: the new type's name back; a door: its
    Reference its type's; the roofs', stairs' and ramps' LoadBearing read as such (not by its definition); a
    subclass the parent's set; valid IFC; undone."""

    def test_standard_sets(self):
        from arqbim.ifc.ifc_data import common_pset, template
        doc = Document()
        wall = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        e = doc.ifc.by_guid(wall)
        self.assertEqual(ue.get_psets(e)["Pset_WallCommon"]["Reference"], "Parede alvenaria 20 cm")
        name, rows = doc.ifc.ifc_data(wall)
        self.assertEqual(name, "Pset_WallCommon")
        by = {r[0]: r for r in rows}
        self.assertNotIn("Status", by)
        self.assertEqual(by["Reference"][3:], ("Parede alvenaria 20 cm", "auto"))
        self.assertEqual((by["FireRating"][1], by["FireRating"][3]), ("text", None))
        self.assertEqual(by["IsExternal"][1], "bool")
        bim.set_property(doc, wall, "Pset_WallCommon", "FireRating", "EI 60")
        by = {r[0]: r for r in doc.ifc.ifc_data(wall)[1]}
        self.assertEqual(by["FireRating"][3:], ("EI 60", "manual"))
        bim.set_property(doc, wall, "Pset_WallCommon", "Reference", "PE1")
        bim.set_type(doc, wall, catalog.BY_KEY["parede_alv_15"])
        self.assertEqual(ue.get_psets(doc.ifc.by_guid(wall))["Pset_WallCommon"]["Reference"], "PE1")
        bim.set_property(doc, wall, "Pset_WallCommon", "Reference", None)       # (cleared: the program's again)
        by = {r[0]: r for r in doc.ifc.ifc_data(wall)[1]}
        self.assertEqual(by["Reference"][3:], ("Parede alvenaria 15 cm", "auto"))
        frame = bim.wall_frame(doc, wall)
        door = bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, 1.0, -1)
        self.assertEqual(ue.get_psets(doc.ifc.by_guid(door))["Pset_DoorCommon"]["Reference"], "Porta 80×210")
        for cls, pset in (("IfcRoof", "Pset_RoofCommon"), ("IfcStair", "Pset_StairCommon"),
                          ("IfcRamp", "Pset_RampCommon")):
            self.assertEqual(common_pset(cls), pset)
            names = [p for p, _k, _c in template(pset)]
            self.assertIn("LoadBearing", names)
            self.assertFalse(any(" " in p for p in names))
        self.assertEqual(common_pset("IfcWallStandardCase"), "Pset_WallCommon")
        self.assertEqual(common_pset("IfcSanitaryTerminal"), "Pset_SanitaryTerminalTypeCommon")
        self.assertFalse(any(" " in prop for _p, prop, _k, _c in doc.ifc.property_templates(wall)))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        while doc.can_undo():
            doc.undo()
        self.assertEqual(len(doc.ifc.file.by_type("IfcWall")), 0)


class ExternalIfc(unittest.TestCase):
    """0.267: outside or inside worked out — three walls of a house (open): all outside; the fourth closes it: all
    four outside still; a partition across: inside; a door in the front wall: outside, one in the partition:
    inside; a garden wall apart: outside; the partition said outside by hand: kept when another wall is drawn;
    cleared: inside again; the west wall taken away (its room opened): the partition outside; valid IFC."""

    def test_external(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 6.0), (0.0, 6.0)]
        walls = [bim.add_wall(doc, np.array(pts[k] + (0.0,)), np.array(pts[(k + 1) % 4] + (0.0,)), spec)
                 for k in range(3)]

        def outside(g):
            return ue.get_psets(doc.ifc.by_guid(g))["Pset_WallCommon"]["IsExternal"]

        self.assertTrue(all(outside(g) for g in walls))
        walls.append(bim.add_wall(doc, np.array(pts[3] + (0.0,)), np.array(pts[0] + (0.0,)), spec))
        self.assertTrue(all(outside(g) for g in walls))
        partition = bim.add_wall(doc, np.array((4.0, 0.0, 0.0)), np.array((4.0, 6.0, 0.0)), spec)
        self.assertFalse(outside(partition))
        self.assertTrue(all(outside(g) for g in walls))
        front = bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, walls[0]),
                                1.0, -1)
        inner = bim.add_opening(doc, partition, catalog.OPENING_BY_KEY["porta_80"],
                                bim.wall_frame(doc, partition), 2.0, -1)
        self.assertTrue(ue.get_psets(doc.ifc.by_guid(front))["Pset_DoorCommon"]["IsExternal"])
        self.assertFalse(ue.get_psets(doc.ifc.by_guid(inner))["Pset_DoorCommon"]["IsExternal"])
        garden = bim.add_wall(doc, np.array((20.0, 0.0, 0.0)), np.array((25.0, 0.0, 0.0)), spec)
        self.assertTrue(outside(garden))
        rows = {r[0]: r for r in doc.ifc.ifc_data(partition)[1]}
        self.assertEqual(rows["IsExternal"][3:], (False, "auto"))
        bim.set_property(doc, partition, "Pset_WallCommon", "IsExternal", True)
        bim.add_wall(doc, np.array((20.0, 2.0, 0.0)), np.array((25.0, 2.0, 0.0)), spec)
        self.assertTrue(outside(partition))
        bim.set_property(doc, partition, "Pset_WallCommon", "IsExternal", None)      # (the program's again)
        self.assertFalse(outside(partition))
        bim.delete(doc, [walls[3]])                                         # (its rooms opened)
        self.assertTrue(outside(partition))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class TypeDataIfc(unittest.TestCase):
    """0.271: a type's IFC data — two walls of the 20 cm type; the type's fire rating EI 60: both have it (the type's,
    shown as such); one with EI 30 written by hand keeps it when the type says EI 90; load bearing set on the type:
    the walls' own «no» they were made with gives way to it; a value cleared from the type: gone; a catalogue type
    not in the project: its set, nothing set; undone; valid IFC."""

    def test_type_data(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        a = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), spec)
        b = bim.add_wall(doc, (0, 3, 0), (5, 3, 0), spec)
        self.assertEqual(sorted(bim.set_type_property(doc, spec, "FireRating", "EI 60")), sorted([a, b]))
        for g in (a, b):
            self.assertEqual(ue.get_psets(doc.ifc.by_guid(g))["Pset_WallCommon"]["FireRating"], "EI 60")
        rows = {r[0]: r for r in doc.ifc.ifc_data(a)[1]}
        self.assertEqual(rows["FireRating"][3:], ("EI 60", "type"))
        bim.set_property(doc, b, "Pset_WallCommon", "FireRating", "EI 30")
        bim.set_type_property(doc, spec, "FireRating", "EI 90")
        self.assertEqual(ue.get_psets(doc.ifc.by_guid(a))["Pset_WallCommon"]["FireRating"], "EI 90")
        self.assertEqual(ue.get_psets(doc.ifc.by_guid(b))["Pset_WallCommon"]["FireRating"], "EI 30")
        self.assertIs(ue.get_psets(doc.ifc.by_guid(a))["Pset_WallCommon"]["LoadBearing"], False)
        bim.set_type_property(doc, spec, "LoadBearing", True)
        self.assertIs(ue.get_psets(doc.ifc.by_guid(a))["Pset_WallCommon"]["LoadBearing"], True)
        name, rows = bim.type_data(doc, spec)
        self.assertEqual(name, "Pset_WallCommon")
        self.assertEqual({r[0]: r[3] for r in rows}["LoadBearing"], True)
        bim.set_type_property(doc, spec, "AcousticRating", "Rw 45")
        bim.set_type_property(doc, spec, "AcousticRating", None)
        self.assertNotIn("AcousticRating", ue.get_psets(doc.ifc.by_guid(a))["Pset_WallCommon"])
        _name, fresh = bim.type_data(doc, catalog.BY_KEY["parede_dry_10"])        # (not in the project)
        self.assertTrue(fresh and all(r[3] is None for r in fresh))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        for _ in range(4):
            doc.undo()
        self.assertEqual(ue.get_psets(doc.ifc.by_guid(a))["Pset_WallCommon"]["FireRating"], "EI 60")


class ThermalTransmittanceIfc(unittest.TestCase):
    """0.272: U by EN ISO 6946 — a 20 cm masonry wall (plaster 2 + block 16 + plaster 2 cm) with no thermal
    conductivities: no U; the plaster's given (0,80): still none (the block has none); the block's (0,35): U =
    1 / (0,13 + 2 × 0,02/0,80 + 0,16/0,35 + 0,04) on the wall, the program's; a concrete slab (λ 2,0, 15 cm): its
    U downwards (Rsi 0,17); a roof of it: upwards (Rsi 0,10); a U written by hand kept; valid IFC."""

    def test_u(self):
        import dataclasses
        doc = Document()
        wall = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])

        def u(g):
            return ue.get_psets(doc.ifc.by_guid(g)).get(
                {"IfcWall": "Pset_WallCommon", "IfcSlab": "Pset_SlabCommon", "IfcRoof": "Pset_RoofCommon"}[
                    doc.ifc.by_guid(g).is_a()], {}).get("ThermalTransmittance")

        self.assertIsNone(u(wall))
        for key, conductivity in (("reboco", 0.80),):
            old = catalog.MATERIALS[key]
            bim.save_material(doc, dataclasses.replace(old, conductivity=conductivity), old)
        self.assertIsNone(u(wall))
        old = catalog.MATERIALS["bloco"]
        bim.save_material(doc, dataclasses.replace(old, conductivity=0.35), old)
        expected = 1 / (0.13 + 2 * 0.02 / 0.80 + 0.16 / 0.35 + 0.04)
        self.assertAlmostEqual(u(wall), round(expected, 3), places=6)
        rows = {r[0]: r for r in doc.ifc.ifc_data(wall)[1]}
        self.assertEqual(rows["ThermalTransmittance"][4], "auto")
        old = catalog.MATERIALS["concreto"]
        slab = bim.add_slab(doc, (0, 0, 0), 5, 4, catalog.BY_KEY["laje_15"])
        bim.save_material(doc, dataclasses.replace(old, conductivity=2.0), old)
        self.assertAlmostEqual(u(slab), round(1 / (0.17 + 0.15 / 2.0 + 0.04), 3), places=6)
        roof = bim.add_roof(doc, [(0, 0), (5, 0), (5, 4), (0, 4)], catalog.BY_KEY["laje_15"], "flat", 0.0, 0.0,
                            eave=3.0)
        self.assertAlmostEqual(u(roof), round(1 / (0.10 + 0.15 / 2.0 + 0.04), 3), places=6)
        bim.set_property(doc, wall, "Pset_WallCommon", "ThermalTransmittance", 0.5)
        old = catalog.MATERIALS["bloco"]
        bim.save_material(doc, dataclasses.replace(old, conductivity=0.30), old)
        self.assertAlmostEqual(u(wall), 0.5)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class MissingDataIfc(unittest.TestCase):
    """0.273: what is missing before delivering — the example house (made before 0.266): its walls without a
    Reference; «fill in what the program knows»: their Reference their type's, outside or inside worked out, one undo
    step; two walls without a fire rating: both listed; the type's given: none missing."""

    def test_missing(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        doc = Document()
        doc.open(os.path.join(root, "exemplos", "casa_exemplo.ifc"))
        found = {cls: (pset, {p: (w, n) for p, w, n in rows}) for cls, pset, rows in doc.ifc.missing_data()}
        self.assertIn("IfcWall", found)
        pset, walls = found["IfcWall"]
        self.assertEqual(pset, "Pset_WallCommon")
        before = len(walls["Reference"][0])
        self.assertGreater(before, 0)
        written = bim.fill_known_data(doc)
        self.assertGreater(written, 0)
        walls = {p: (w, n) for cls, _p, rows in doc.ifc.missing_data() if cls == "IfcWall" for p, w, n in rows}
        self.assertEqual(walls["Reference"][0], [])
        self.assertEqual(walls["IsExternal"][0], [])
        doc.undo()
        walls = {p: (w, n) for cls, _p, rows in doc.ifc.missing_data() if cls == "IfcWall" for p, w, n in rows}
        self.assertEqual(len(walls["Reference"][0]), before)
        fresh = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        for y in (0.0, 3.0):
            bim.add_wall(fresh, (0, y, 0), (5, y, 0), spec)
        rows = {p: w for cls, _p, r in fresh.ifc.missing_data() if cls == "IfcWall" for p, w, _n in r}
        self.assertEqual(len(rows["FireRating"]), 2)
        bim.set_type_property(fresh, spec, "FireRating", "EI 60")
        rows = {p: w for cls, _p, r in fresh.ifc.missing_data() if cls == "IfcWall" for p, w, _n in r}
        self.assertEqual(rows["FireRating"], [])


class RoofCarpentryIfc(unittest.TestCase):
    """0.276: a hip roof over a 10 × 6 m house of 20 cm walls, its carpentry made — an IfcElementAssembly
    «Madeiramento» of IfcMembers (the plates PLATE, the rafters RAFTER, the purlins PURLIN, the battens and the
    ridge board USERDEFINED), of wood, closed; a plate on each wall's top; the cover raised so that the rafters lie
    on the plates' inner edge; made steeper: made again under it; taken away: the cover back on the walls; the roof
    deleted: its carpentry with it; valid IFC; undone."""

    def test_carpentry(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 6.0), (0.0, 6.0)]
        for k in range(4):
            bim.add_wall(doc, np.array(pts[k] + (0.0,)), np.array(pts[(k + 1) % 4] + (0.0,)), spec)
        roof = bim.add_roof(doc, [(-0.1, -0.1), (10.1, -0.1), (10.1, 6.1), (-0.1, 6.1)], catalog.BY_KEY["laje_15"],
                            "hip", 30.0, 0.5)
        before = doc.ifc.roof_params(roof)["eave"]
        assembly = bim.set_roof_carpentry(doc, roof)
        e = doc.ifc.by_guid(assembly)
        self.assertEqual((e.is_a(), e.PredefinedType, e.ObjectType), ("IfcElementAssembly", "USERDEFINED",
                                                                      "Madeiramento"))
        parts = [p for rel in e.IsDecomposedBy for p in rel.RelatedObjects]
        kinds = {p.PredefinedType for p in parts}
        self.assertTrue({"PLATE", "RAFTER", "PURLIN", "USERDEFINED"} <= kinds)
        self.assertEqual(ue.get_material(parts[0]).Name, "Madeira")
        self.assertTrue(all(doc.get(p.GlobalId).mesh.is_closed() for p in parts[:20]))
        found = doc.ifc.carpentry_summary(roof)
        self.assertEqual(found["frechal"][0], 4)
        self.assertAlmostEqual(found["frechal"][1], 2 * 10.0 + 2 * 6.0, delta=0.5)
        t, sec = math.tan(math.radians(30)), 1 / math.cos(math.radians(30))
        rise = 0.16 + (0.015 + 0.06) * sec + (0.1 - 0.04) * t
        self.assertAlmostEqual(doc.ifc.roof_params(roof)["eave"], before + rise, places=6)
        plate = next(p for p in parts if p.PredefinedType == "PLATE")
        self.assertAlmostEqual(float(doc.get(plate.GlobalId).mesh.verts[:, 2].min()), 2.8, places=6)
        bim.set_roof(doc, roof, slope=40.0)
        again = doc.ifc.carpentry_of(roof)
        self.assertIsNotNone(again)
        self.assertNotEqual(again.GlobalId, assembly)
        self.assertEqual(len(doc.ifc.file.by_type("IfcElementAssembly")), 1)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.remove_roof_carpentry(doc, roof)
        self.assertIsNone(doc.ifc.carpentry_of(roof))
        self.assertEqual(len(doc.ifc.file.by_type("IfcMember")), 0)
        sec40, t40 = 1 / math.cos(math.radians(40)), math.tan(math.radians(40))
        self.assertAlmostEqual(doc.ifc.roof_params(roof)["eave"], 2.8 + 0.15 * sec40 - 0.2 * t40, places=6)
        bim.set_roof_carpentry(doc, roof)
        bim.delete(doc, [roof])
        self.assertEqual(len(doc.ifc.file.by_type("IfcMember")), 0)
        doc.undo()
        self.assertGreater(len(doc.ifc.file.by_type("IfcMember")), 50)
        with self.assertRaises(ValueError):
            flat = bim.add_roof(doc, [(20, 0), (25, 0), (25, 4), (20, 4)], catalog.BY_KEY["laje_15"], "flat", 0.0,
                                0.0, eave=3.0)
            bim.set_roof_carpentry(doc, flat)


class CarpentrySizesIfc(unittest.TestCase):
    """0.277: a hip roof's carpentry made with its own sizes — rafters 0,60 m apart of 6 × 8 cm: fewer rafters than
    at 0,50, the sizes kept in the IFC (read back the same), the cover raised by the deeper rafters; the Carpentry
    schedule: a line a kind of piece, its section, pieces, metres and m³ (the same as the roof's summary)."""

    def test_sizes(self):
        from arqbim.core import roof_carpentry as rc
        from arqbim.ifc.carpentry import settings_from
        from arqbim.model import schedules
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 6.0), (0.0, 6.0)]
        for k in range(4):
            bim.add_wall(doc, np.array(pts[k] + (0.0,)), np.array(pts[(k + 1) % 4] + (0.0,)), spec)
        roof = bim.add_roof(doc, [(-0.1, -0.1), (10.1, -0.1), (10.1, 6.1), (-0.1, 6.1)], catalog.BY_KEY["laje_12"],
                            "hip", 30.0, 0.5)
        before = doc.ifc.roof_params(roof)["eave"]
        bim.set_roof_carpentry(doc, roof)
        rafters = doc.ifc.carpentry_summary(roof)["caibro"][0]
        sections = dict(rc.Settings().sections)
        sections["caibro"] = (0.06, 0.08)
        mine = rc.Settings(rafter_spacing=0.60, sections=tuple(sorted(sections.items())))
        bim.set_roof_carpentry(doc, roof, mine)
        self.assertLess(doc.ifc.carpentry_summary(roof)["caibro"][0], rafters)
        stored = settings_from(doc.ifc._params(doc.ifc.carpentry_of(roof)).get("Madeiramento"))
        self.assertEqual((stored.rafter_spacing, stored.section("caibro")), (0.60, (0.06, 0.08)))
        t, sec = math.tan(math.radians(30)), 1 / math.cos(math.radians(30))
        rise = 0.16 + (0.015 + 0.08) * sec + (0.1 - 0.04) * t
        self.assertAlmostEqual(doc.ifc.roof_params(roof)["eave"], before + rise, places=6)
        rows = schedules.rows(doc, "carpentry")
        found = doc.ifc.carpentry_summary(roof)
        self.assertEqual(len(rows), len(found))
        rafter_row = next(r for r in rows if r["pieces"] == found["caibro"][0])
        self.assertEqual(rafter_row["section"], "6 × 8 cm")
        self.assertAlmostEqual(sum(r["volume"] for r in rows), sum(v[2] for v in found.values()), places=6)


class RoofTilesIfc(unittest.TestCase):
    """0.279: a 10 × 6 m house's hip roof tiled with Marselha tiles — an IfcCovering of an IfcCoveringType ROOFING
    («Telha marselha», of ceramic tile) over the roof (IfcRelCoversBldgElements); its body a MappedRepresentation of
    three maps (the tile, the ridge tile, the cut tiles), the tile's mapped onto each whole tile; as many tiles as
    the core lays, their weight; on screen (read from its maps) as the core lays them, where the roof is; steeper:
    laid again; the plain tile chosen; carpentry made: the tiles go up with the cover; valid IFC; the roof deleted:
    its tiles with it; undone; a flat roof refused."""

    def test_tiles(self):
        from arqbim.core import roof_tiles as rt
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 6.0), (0.0, 6.0)]
        for k in range(4):
            bim.add_wall(doc, np.array(pts[k] + (0.0,)), np.array(pts[(k + 1) % 4] + (0.0,)), spec)
        roof = bim.add_roof(doc, [(-0.1, -0.1), (10.1, -0.1), (10.1, 6.1), (-0.1, 6.1)],
                            catalog.BY_KEY["cobertura_12"], "hip", 30.0, 0.5)
        guid = bim.set_roof_tiles(doc, roof)
        e = doc.ifc.by_guid(guid)
        self.assertEqual((e.is_a(), ue.get_predefined_type(e), ue.get_type(e).Name, ue.get_material(e).Name),
                         ("IfcCovering", "ROOFING", "Telha marselha", "Telha cerâmica"))
        self.assertEqual(e.CoversElements[0].RelatingBuildingElement.GlobalId, roof)
        body = e.Representation.Representations[0]
        self.assertEqual(body.RepresentationType, "MappedRepresentation")
        self.assertEqual(len({i.MappingSource.id() for i in body.Items}), 3)
        waters, edges, _sides = doc.ifc.roof_waters(roof)
        tiling = rt.lay(waters, edges, rt.TILES["marselha"])
        found = doc.ifc.tiles_summary(roof)
        self.assertEqual((found["tile"], found["tiles"], found["cut"], found["caps"]),
                         ("marselha", tiling.tiles, tiling.cut_count, len(tiling.caps)))
        self.assertAlmostEqual(found["weight"], tiling.weight, places=6)
        v, t = rt.merged(tiling)
        m = doc.ifc._placement_si(doc.ifc.by_guid(roof))
        v = v @ m[:3, :3].T + m[:3, 3]
        mesh = doc.get(guid).mesh
        self.assertEqual(len(mesh.faces), len(t))
        self.assertTrue(np.allclose(np.asarray(mesh.verts).min(axis=0), v.min(axis=0), atol=1e-6))
        self.assertTrue(np.allclose(np.asarray(mesh.verts).max(axis=0), v.max(axis=0), atol=1e-6))
        before = found["tiles"]
        bim.set_roof(doc, roof, slope=40.0)                 # (laid again on it)
        self.assertNotEqual(doc.ifc.tiles_summary(roof)["tiles"], before)
        self.assertEqual(len([c for c in doc.ifc.file.by_type("IfcCovering")]), 1)
        bim.set_roof_tiles(doc, roof, "plana")
        self.assertEqual((doc.ifc.tiles_summary(roof)["tile"], doc.ifc.tiles_summary(roof)["stagger"]),
                         ("plana", True))
        top = float(np.asarray(doc.get(doc.ifc.tiles_of(roof).GlobalId).mesh.verts)[:, 2].max())
        bim.set_roof_carpentry(doc, roof)                   # (the cover goes up: the tiles with it)
        self.assertGreater(float(np.asarray(doc.get(doc.ifc.tiles_of(roof).GlobalId).mesh.verts)[:, 2].max()),
                           top + 0.2)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.delete(doc, [roof])
        self.assertEqual(len(doc.ifc.file.by_type("IfcCovering")), 0)
        doc.undo()
        self.assertIsNotNone(doc.ifc.tiles_of(roof))
        bim.remove_roof_tiles(doc, roof)
        self.assertIsNone(doc.ifc.tiles_of(roof))
        self.assertEqual(len(doc.ifc.file.by_type("IfcRepresentationMap")) + len(doc.ifc.file.by_type("IfcMappedItem")),
                         0)
        flat = bim.add_roof(doc, [(20, 0), (25, 0), (25, 4), (20, 4)], catalog.BY_KEY["cobertura_15"], "flat", 0.0,
                            0.0, eave=3.0)
        with self.assertRaises(ValueError):
            bim.set_roof_tiles(doc, flat)
        guid = bim.set_roof_tiles(doc, roof, "sanduiche")  # (0.280) sandwich panels: steel, one a column
        e = doc.ifc.by_guid(guid)
        self.assertEqual((ue.get_type(e).Name, ue.get_material(e).Name), ("Painel sanduíche", "Aço galvanizado"))
        waters, edges, _sides = doc.ifc.roof_waters(roof)
        tiling = rt.lay(waters, edges, rt.TILES["sanduiche"])
        self.assertEqual(doc.ifc.tiles_summary(roof)["tiles"], tiling.tiles)
        self.assertEqual(len(doc.get(guid).mesh.faces), len(rt.merged(tiling)[1]))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class RailingExtensionsIfc(unittest.TestCase):
    """0.282: a straight stair's railings (2,80 m up, its going 0,28) with their handrails on past their ends as DL
    163/2006 asks (annex 2.4.9) — one going before the first nosing, keeping the slope, down to the floor; 0,30 m past
    the last, level, down to the floor above: kept in their parameters; the extensions changed in the Properties
    (none at the foot); a railing drawn along a path: none; a round one: none; valid IFC."""

    def test_extensions(self):
        doc = Document()
        stair = bim.add_stair(doc, np.array((10.0, 0.0, 0.0)), (1.0, 0.0), catalog.BY_KEY["laje_15"], "straight", 2.8,
                              going=0.28)
        rails = bim.stair_railings(doc, stair, style="corrimao")
        p = doc.ifc.stair_params(stair)
        last = 10.0 + (core_stairs_risers(2.8)[0] - 1) * 0.28           # (the last nosing, along x)
        for g in rails:
            self.assertEqual(doc.ifc.railing_params(g)["extend"], (0.28, 0.30))
            lo, hi = bounds(doc, g)
            self.assertAlmostEqual(lo[0], 10.0 - 0.28 - 0.042 / 2, delta=0.01)    # (a going before the first nosing)
            self.assertAlmostEqual(hi[0], last + 0.30 + 0.042 / 2, delta=0.01)    # (0,30 past the last)
            self.assertAlmostEqual(lo[2], 0.0, delta=1e-6)                         # (down to the floor)
        self.assertEqual(p["going"], 0.28)
        bim.set_railing(doc, rails[0], extend=(0.0, 0.30))
        lo, _hi = bounds(doc, rails[0])
        self.assertGreater(lo[0], 10.0 - 0.05)
        path = bim.add_railing(doc, [(0, 0, 0), (4, 0, 0)], 1.0, "barras")
        self.assertEqual(doc.ifc.railing_params(path)["extend"], (0.0, 0.0))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


def core_stairs_risers(rise):
    from arqbim.core import stairs as core_stairs
    return core_stairs.risers(rise)


class JoineryIfc(unittest.TestCase):
    """0.288 — doors and windows made by the generator: every one of the catalogue in a wall — its type keeping its
    design («Desenho»), its OperationType / PartitioningType the design's (and the door's / window's own), IFC's lining
    and panel properties (a door's lining as deep as its wall: no depth of its own), its materials as IFC names them
    («Lining», «Framing», «Glazing»); its body of pieces each in its colour; a door's plan symbol —; a window moved: its
    frame as deep as its design (7 cm, no longer 10); a door with a fanlight hinged on the other jamb: its fanlight and
    materials kept, its design the mirror image; a window type of three lights saved in the type editor, read back
    with its design; an old type with no design: one made from its IFC names; the IFC valid."""

    def test_joinery(self):
        from arqbim.core import joinery as jn
        from arqbim.model import project_types
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((18.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        made, s = {}, 0.4
        for o in catalog.OPENINGS:
            made[o.key] = bim.add_opening(doc, wall, o, bim.wall_frame(doc, wall), s, -1)
            s += o.width + 0.35
        for key, guid in made.items():
            e = doc.ifc.by_guid(guid)
            type_ = ue.get_type(e)
            design = doc.ifc.opening_design(type_)
            self.assertEqual(design, catalog.OPENING_BY_KEY[key].design, key)
            if e.is_a("IfcDoor"):
                self.assertEqual(type_.OperationType, jn.door_operation(design)[0])
                self.assertEqual(e.OperationType, type_.OperationType)
                self.assertTrue(doc.ifc.has_plan_symbol(guid))
            else:
                self.assertEqual(type_.PartitioningType, jn.window_partitioning(design)[0])
                self.assertEqual(e.PartitioningType, type_.PartitioningType)
            sets = {p.Name: p for p in type_.HasPropertySets or ()}
            lining = sets["DoorLiningProperties" if e.is_a("IfcDoor") else "WindowLiningProperties"]
            panels = [p for p in sets.values() if "PanelProperties" in p.is_a()]
            self.assertEqual(len(panels), len(design.rows[0].cells) if e.is_a("IfcDoor") else
                             sum(len(r.cells) for r in design.rows), key)
            parts = [c.Name for c in ue.get_material(type_).MaterialConstituents]
            self.assertEqual(parts, [p for p, _k in jn.constituents(design)], key)
            colours = doc.get(guid).mesh.colors
            self.assertEqual(len({tuple(np.round(c, 2)) for c in colours}), len(set(jn.meshes(
                design, 1.0, 2.0, 0.0, 0.1))), key)
        common = ue.get_psets(ue.get_type(doc.ifc.by_guid(made["janela_120"])))["Pset_WindowCommon"]
        self.assertTrue(0.3 < common["GlazingAreaFraction"] < 0.9 and common["HasSillExternal"])     # (0.291)
        self.assertNotIn("Pset_DoorCommon", ue.get_psets(ue.get_type(doc.ifc.by_guid(made["porta_80"]))))
        self.assertGreater(ue.get_psets(ue.get_type(doc.ifc.by_guid(made["porta_sacada_140"])))["Pset_DoorCommon"]
                           ["GlazingAreaFraction"], 0.4)
        door = doc.ifc.by_guid(made["porta_80"])
        lining = next(p for p in ue.get_type(door).HasPropertySets if p.is_a("IfcDoorLiningProperties"))
        self.assertIsNone(lining.LiningDepth)                               # (as deep as the wall)
        self.assertAlmostEqual(lining.CasingDepth * doc.ifc.unit_scale, 0.015)
        self.assertEqual(ue.get_type(doc.ifc.by_guid(made["janela_120"])).HasPropertySets[-1].PanelPosition, "RIGHT")
        from arqbim.model import drawings                                   # (0.292) the signs in elevation
        self.assertEqual(len(doc.ifc.elevation_signs([made["janela_120"]])[made["janela_120"]]), 2 * 2 * 2)
        south = drawings.elevation(doc, "S", "Sul")                         # (the face they are pushed from)
        north = drawings.elevation(doc, "N", "Norte")
        self.assertGreater(len(south.symbols), 20)
        self.assertGreater(len(north.symbols), 20)
        across = drawings.section(doc, (8.0, 0.0, 0.0), (0.0, 1.0, 0.0), "Corte")   # (through them: their cut)
        self.assertEqual(len(across.symbols), 0)
        window = made["janela_120"]
        bim.move_filling(doc, window, s=doc.ifc.filling_state(window)["s"] + 0.1)
        y = doc.get(window).mesh.verts[:, 1] + 0.1                          # (across the wall from its face)
        self.assertTrue(np.any(np.abs(y - 0.065) < 1e-6))                  # (its design's frame, 7 cm in the
        self.assertFalse(np.any(np.abs(y - 0.05) < 1e-6))                  # middle; 10 cm before)
        self.assertAlmostEqual(float(y.min()), -0.03, places=6)             # (0.290) its peitoril 3 cm out
        flip = made["porta_80_bandeira"]
        bim.flip_door(doc, flip, hinge=True)
        type_ = ue.get_type(doc.ifc.by_guid(flip))
        self.assertEqual((type_.Name, doc.ifc.by_guid(flip).OperationType),
                         ("Porta 80×210 + bandeira 50 (à direita)", "SINGLE_SWING_RIGHT"))
        self.assertAlmostEqual(ue.get_psets(type_)["ArqSynth_Parametros"]["Bandeira"], 0.5)
        self.assertEqual(doc.ifc.opening_design(type_), jn.mirrored(catalog.OPENING_BY_KEY["porta_80_bandeira"].design))
        self.assertEqual([c.Name for c in ue.get_material(type_).MaterialConstituents], ["Lining", "Framing", "Glazing"])
        three = catalog.OpeningSpec("t:new", "window", "Janela de 3", "Janela de 3", 1.8, 1.4, 0.9,
                                    design=jn.window(("fixed", "left", "right")))
        bim.save_type(doc, three)
        read = {s.name_pt: s for s in project_types.read_openings(doc.ifc)}
        self.assertEqual(read["Janela de 3"].design, three.design)
        self.assertEqual(read["Janela de 3"].operation, "TRIPLE_PANEL_VERTICAL")
        old = ue.get_type(doc.ifc.by_guid(made["porta_90"]))                # (as a file from before 0.288 has it)
        pset = doc.ifc.file.by_id(ue.get_psets(old)["ArqSynth_Parametros"]["id"])
        ifcopenshell.api.pset.remove_pset(doc.ifc.file, product=old, pset=pset)        # (its «Desenho» alone)
        old.Name = "Porta antiga"
        old.OperationType = "DOUBLE_DOOR_SINGLE_SWING"
        self.assertEqual([c.operation for c in doc.ifc.opening_design(old).rows[0].cells], ["left", "right"])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class ArchedOpeningsIfc(unittest.TestCase):
    """0.294 — an arched window (100×150, its round arch a fixed fanlight) in a wall: its opening the arch's outline
    extruded across the wall (the wall's volume less its area), moved along the wall and turned to the other side:
    still arched; the wall made thicker: the same; the IFC valid."""

    def test_arched(self):
        from arqbim.core import joinery as jn
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        full = doc.get(wall).mesh.volume()
        spec = catalog.OPENING_BY_KEY["janela_arco_100"]
        win = bim.add_opening(doc, wall, spec, bim.wall_frame(doc, wall), 2.0, -1)
        area = jn._area(jn.outline(spec.design, 1.0, 1.5))
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), full - area * 0.2, places=4)
        opening = doc.ifc.by_guid(win).FillsVoids[0].RelatingOpeningElement
        solid = opening.Representation.Representations[0].Items[0]
        self.assertEqual((solid.is_a(), solid.SweptArea.is_a()), ("IfcExtrudedAreaSolid", "IfcArbitraryClosedProfileDef"))
        bim.move_filling(doc, win, s=1.5)
        bim.flip_door(doc, win, side=True)
        opening = doc.ifc.by_guid(win).FillsVoids[0].RelatingOpeningElement
        self.assertTrue(opening.Representation.Representations[0].Items[0].SweptArea.is_a("IfcArbitraryClosedProfileDef"))
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), full - area * 0.2, places=4)
        bim.set_type(doc, wall, catalog.BY_KEY["parede_alv_25"] if "parede_alv_25" in catalog.BY_KEY
                     else catalog.BY_KEY["parede_alv_15"])
        opening = doc.ifc.by_guid(win).FillsVoids[0].RelatingOpeningElement
        self.assertTrue(opening.Representation.Representations[0].Items[0].SweptArea.is_a("IfcArbitraryClosedProfileDef"))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class OpeningsMapIfc(unittest.TestCase):
    """0.293 — the mapa de vãos: two doors 80×210 (one hinged on the right: counted with its type), two windows of two
    types — its types, the doors first, each kind by name, their counts and marks, a window's sill; drawn: each type's
    elevation, its two dimensions, its texts (name, size, sill, opening, count with marks); none in a project with no
    doors nor windows."""

    def test_map(self):
        from arqbim.model import drawings
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((10.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        frame = bim.wall_frame(doc, wall)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, 0.5, -1)
        right = bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, 2.0, -1)
        bim.flip_door(doc, right, hinge=True)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["janela_150"], bim.wall_frame(doc, wall), 6.0, -1)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, wall), 4.0, -1)
        used = doc.ifc.opening_types_used()
        self.assertEqual([u["name"] for u in used], ["Porta 80×210", "Janela 120×120 (peitoril 1,00)",
                                                     "Janela 150×120 (peitoril 1,00)"])
        self.assertEqual((used[0]["count"], used[0]["marks"]), (2, ["P1", "P2"]))
        self.assertAlmostEqual(used[1]["sill"], 1.0)
        self.assertTrue(np.allclose((used[1]["width"], used[1]["height"]), (1.2, 1.2)))
        drawing = drawings.of_view(doc, "openings", "", "Mapa de vãos")
        texts = [a[3] for a in drawing.annotations if a[0] == "text"]
        for words in ("Porta 80×210", "L × A: 1,20 × 1,20", "Peitoril: 1,00", "Abertura: batente",
                      "Abertura: correr", "Quantidade: 2 (P1, P2)", "Quantidade: 1 (J1)"):
            self.assertTrue(any(x.startswith(words) for x in texts), (words, texts))
        self.assertEqual(len(drawing.dims), 2 * 3)
        self.assertIsNotNone(drawing.frame)
        self.assertIsNone(drawings.of_view(Document(), "openings", "", "Mapa de vãos"))


class LouvresIfc(unittest.TestCase):
    """0.295 — portadas de lâminas on a window type (120×120, a pair, wooden): kept in its design; its windows' bodies
    with them in wood, shut in the opening flush with the wall's outer face; opened: beside the opening on the wall; in
    the mapa de vãos (drawn open, said); its glazing fraction as it was; the IFC valid."""

    def test_louvres(self):
        from arqbim.core import joinery as jn
        from arqbim.model import drawings
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        spec = catalog.OPENING_BY_KEY["janela_120"]
        win = bim.add_opening(doc, wall, spec, bim.wall_frame(doc, wall), 2.0, -1)
        before = ue.get_psets(ue.get_type(doc.ifc.by_guid(win)))["Pset_WindowCommon"]["GlazingAreaFraction"]
        new = catalog.with_design(spec, dataclasses.replace(spec.design, louvres="pair"))
        bim.save_type(doc, new, spec)
        type_ = ue.get_type(doc.ifc.by_guid(win))
        self.assertEqual(doc.ifc.opening_design(type_).louvres, "pair")
        wood = catalog.MATERIALS["madeira"].color
        mesh = doc.get(win).mesh
        self.assertTrue(any(np.allclose(c[:3], wood, atol=0.01) for c in mesh.colors))
        y = mesh.verts[:, 1] + 0.1                                      # (across the wall from its outer face)
        self.assertAlmostEqual(float(y.min()), -0.03, places=6)          # (its peitoril's nose, out of them)
        x = mesh.verts[:, 0]
        self.assertTrue(np.all((x > 2.0 - 0.02) & (x < 3.2 + 0.02)))   # (shut: in the opening)
        self.assertAlmostEqual(ue.get_psets(type_)["Pset_WindowCommon"]["GlazingAreaFraction"], before)
        opened = catalog.with_design(new, dataclasses.replace(new.design, louvres_open=True))
        bim.save_type(doc, opened, new)
        x = doc.get(win).mesh.verts[:, 0]
        self.assertAlmostEqual(float(x.min()), 2.0 - 0.598, places=4)  # (open: on the wall beside it)
        self.assertAlmostEqual(float(x.max()), 3.2 + 0.598, places=4)
        texts = [a[3] for a in drawings.of_view(doc, "openings", "", "Mapa de vãos").annotations if a[0] == "text"]
        self.assertIn("Com portadas de lâminas", texts)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class OrientWindowsIfc(unittest.TestCase):
    """0.297 — the peitoril to the outside by itself: in a 10 × 6 m house, a window placed from inside the south wall
    turned with its peitoril out of the house (its mirror type kept on the same jamb); one placed from outside left as
    it is; one in an inside wall left as clicked; one turned back in by hand — «LadoManual» — kept so when the walls
    change; one placed while the house was open, turned when its last wall closes it — and back with the undo; the
    IFC valid."""

    def test_orient(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 6.0), (0.0, 6.0)]
        walls = [bim.add_wall(doc, np.array(pts[k] + (0.0,)), np.array(pts[(k + 1) % 4] + (0.0,)), spec)
                 for k in range(3)]
        early = bim.add_opening(doc, walls[1], catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, walls[1]),
                                2.0, 1)                                             # (from inside, the house open)
        east = lambda g: float(doc.get(g).mesh.verts[:, 0].max())                  # noqa: E731
        self.assertLess(east(early), 10.1)                                          # (as clicked: its peitoril in)
        walls.append(bim.add_wall(doc, np.array(pts[3] + (0.0,)), np.array(pts[0] + (0.0,)), spec))
        self.assertAlmostEqual(east(early), 10.13, places=6)                        # (closed: turned out)
        doc.undo()
        self.assertLess(east(early), 10.1)
        doc.redo()
        self.assertAlmostEqual(east(early), 10.13, places=6)
        oscilo = catalog.OPENING_BY_KEY["janela_oscilo_100"]
        inside = bim.add_opening(doc, walls[0], oscilo, bim.wall_frame(doc, walls[0]), 2.0, 1)
        south = lambda g: float(doc.get(g).mesh.verts[:, 1].min())                 # noqa: E731
        self.assertAlmostEqual(south(inside), -0.13, places=6)                      # (its peitoril out of the house)
        self.assertEqual(ue.get_type(doc.ifc.by_guid(inside)).Name, oscilo.name_pt + " (espelhada)")
        outside = bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, walls[0]),
                                  7.0, -1)
        self.assertAlmostEqual(south(outside), -0.13, places=6)
        self.assertEqual(ue.get_type(doc.ifc.by_guid(outside)).Name, catalog.OPENING_BY_KEY["janela_120"].name_pt)
        middle = bim.add_wall(doc, np.array((6.0, 0.1, 0.0)), np.array((6.0, 5.9, 0.0)), spec)
        across = bim.add_opening(doc, middle, catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, middle),
                                 2.0, 1)
        before = doc.get(across).mesh.verts.copy()
        bim.flip_door(doc, outside, side=True)                                      # (by hand: in)
        self.assertAlmostEqual(float(doc.get(outside).mesh.verts[:, 1].max()), 0.13, places=6)
        self.assertIs(ue.get_psets(doc.ifc.by_guid(outside))["ArqSynth_Parametros"]["LadoManual"], True)
        bim.add_wall(doc, np.array((4.5, 0.1, 0.0)), np.array((4.5, 3.0, 0.0)), spec)      # (the walls change)
        self.assertAlmostEqual(float(doc.get(outside).mesh.verts[:, 1].max()), 0.13, places=6)   # (kept in)
        self.assertTrue(np.allclose(doc.get(across).mesh.verts, before))          # (an inside wall's: as it was)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class JoineryTypesIfc(unittest.TestCase):
    """0.289 — the generator's designs in the project: a tilt and turn window's type given a new design (a fixed light
    and the tilt and turn leaf) — its windows follow, their partitioning too; the wall mirrored: the window's type the
    mirror image («… (espelhada)», hidden from the types list, its windows counted with the type's); mirrored back: the
    type it came from; the type changed again: the mirrored windows follow, mirrored; the IFC valid."""

    def test_designs(self):
        from arqbim.core import joinery as jn
        from arqbim.model import project_types
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        spec = catalog.OPENING_BY_KEY["janela_oscilo_100"]
        win = bim.add_opening(doc, wall, spec, bim.wall_frame(doc, wall), 1.0, -1)
        new = catalog.with_design(spec, dataclasses.replace(spec.design, rows=jn.model("window", "oscilo_2")))
        bim.save_type(doc, new, spec)
        e = doc.ifc.by_guid(win)
        self.assertEqual((e.PartitioningType, ue.get_type(e).PartitioningType), ("DOUBLE_PANEL_VERTICAL",) * 2)
        self.assertEqual(doc.ifc.opening_design(e), new.design)
        bim.mirror_objects(doc, [wall], np.array((3.0, 0.0, 0.0)), np.array((3.0, 1.0, 0.0)))
        e = doc.ifc.by_guid(win)
        mirrored = ue.get_type(e)
        self.assertEqual(mirrored.Name, spec.name_pt + " (espelhada)")
        self.assertEqual(doc.ifc.opening_design(e), jn.mirrored(new.design))
        names = [s.name_pt for s in project_types.read_openings(doc.ifc)]
        self.assertNotIn(mirrored.Name, names)
        self.assertEqual(project_types.instances(doc.ifc, new), [win])
        bim.mirror_objects(doc, [wall], np.array((3.0, 0.0, 0.0)), np.array((3.0, 1.0, 0.0)))
        self.assertEqual(ue.get_type(doc.ifc.by_guid(win)).Name, spec.name_pt)
        bim.mirror_objects(doc, [wall], np.array((3.0, 0.0, 0.0)), np.array((3.0, 1.0, 0.0)))
        third = catalog.with_design(new, dataclasses.replace(new.design, rows=jn.model("window", "batente_bandeira")
                                                             [:1] + (jn.Row((jn.Cell("tilt_left"),), 0.4),)))
        bim.save_type(doc, third, project_types.read_opening(doc.ifc, project_types.find_type(doc.ifc, new), "window")
                      or new)
        e = doc.ifc.by_guid(win)
        self.assertTrue(ue.get_type(e).Name.endswith(" (espelhada)"))
        self.assertEqual(doc.ifc.opening_design(e), jn.mirrored(third.design))
        self.assertEqual(e.PartitioningType, "TRIPLE_PANEL_TOP")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class OwnTileIfc(unittest.TestCase):
    """0.281: a tile of the user's own — a component 30 × 45 × 2 cm (a sketch box made one) registered with its
    maker's data (cover 27 cm, gauge 38 cm, 3,1 kg): an IfcCoveringType ROOFING keeping its shape, not in the
    Library's components; listed among the tiles to lay; a hip roof tiled with it — about its waters' area over its
    cover × gauge, the covering of that very type, its weight; measured (an odd size warned); refused when its
    cover is under 2 cm; valid IFC; kept in the file."""

    def test_own_tile(self):
        from arqbim.core import roof_tiles as rt
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 6.0), (0.0, 6.0)]
        for k in range(4):
            bim.add_wall(doc, np.array(pts[k] + (0.0,)), np.array(pts[(k + 1) % 4] + (0.0,)), spec)
        roof = bim.add_roof(doc, [(-0.1, -0.1), (10.1, -0.1), (10.1, 6.1), (-0.1, 6.1)],
                            catalog.BY_KEY["cobertura_12"], "hip", 30.0, 0.5)
        sketch = box_object(doc, (20.0, 0.0, 0.0), 0.30, 0.45, 0.02)
        instance = bim.make_component(doc, [sketch.id], "Telha da fábrica", "generic")
        verts, tris = bim.tile_shape(doc, instance)
        width, length, height, cover, gauge, warnings = rt.measure(verts)
        self.assertEqual((round(width, 6), round(length, 6), round(height, 6), warnings), (0.30, 0.45, 0.02, []))
        self.assertAlmostEqual(cover, 0.27)
        self.assertEqual(rt.measure(np.asarray(verts) * 100)[5], ["size"])
        key = bim.register_tile(doc, instance, "Telha da fábrica", 0.27, 0.38, 3.1, False)
        type_ = doc.ifc.by_guid(key[2:])
        self.assertEqual((type_.is_a(), type_.PredefinedType, len(type_.RepresentationMaps)),
                         ("IfcCoveringType", "ROOFING", 1))
        self.assertNotIn(type_.GlobalId, [c[0] for c in doc.ifc.library()["components"]])
        self.assertIn((key, "Telha da fábrica"), doc.ifc.tile_choices())
        own = doc.ifc.tile_spec(key)
        self.assertEqual((own.cover_width, own.gauge, own.weight, own.stagger), (0.27, 0.38, 3.1, False))
        guid = bim.set_roof_tiles(doc, roof, key)
        self.assertEqual(ue.get_type(doc.ifc.by_guid(guid)).GlobalId, type_.GlobalId)
        found = doc.ifc.tiles_summary(roof)
        area = found["area"]
        self.assertTrue(area / (0.27 * 0.38) < found["tiles"] < 1.25 * area / (0.27 * 0.38), found)
        self.assertAlmostEqual(found["weight"], found["tiles"] * 3.1 + found["caps"] * rt.CAP.weight, places=6)
        with self.assertRaises(ValueError):
            bim.register_tile(doc, instance, "Estreita", 0.01, 0.38, 3.1)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        from arqbim.ifc.model import IfcModel
        with tempfile.TemporaryDirectory() as tmp:          # (kept in the file: read back the same)
            path = os.path.join(tmp, "telha.ifc")
            doc.ifc.file.write(path)
            again = IfcModel(ifcopenshell.open(path)).tile_types()[key]
        self.assertEqual((again.cover_width, again.gauge, len(again.custom[1])), (0.27, 0.38, len(own.custom[1])))


class RoofTypeIfc(unittest.TestCase):
    """0.278: roofs of a roof type (IfcRoofType NOTDEFINED: the roof keeps its own form) with its layers; its type
    changed — thicker: its underside stays on the walls, its carpentry made again under it; the type changed in the
    type editor: every roof of it follows; a roof made before (a slab's type, untyped) given a roof type; valid IFC;
    undone."""

    def _house(self, doc):
        spec = catalog.BY_KEY["parede_alv_20"]
        pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 6.0), (0.0, 6.0)]
        for k in range(4):
            bim.add_wall(doc, np.array(pts[k] + (0.0,)), np.array(pts[(k + 1) % 4] + (0.0,)), spec)
        return [(-0.1, -0.1), (10.1, -0.1), (10.1, 6.1), (-0.1, 6.1)]

    def test_roof_type(self):
        from arqbim.core import roofs as core_roofs
        doc = Document()
        tiles, concrete = catalog.BY_KEY["telhado_ceramico"], catalog.BY_KEY["cobertura_15"]
        roof = bim.add_roof(doc, self._house(doc), tiles, "hip", 30.0, 0.5)
        e = doc.ifc.by_guid(roof)
        type_ = ue.get_type(e)
        self.assertEqual((type_.is_a(), type_.Name, type_.PredefinedType, e.PredefinedType),
                         ("IfcRoofType", tiles.name_pt, "NOTDEFINED", "HIP_ROOF"))
        self.assertEqual([m.Material.Name for m in ue.get_material(type_).MaterialLayers], ["Telha cerâmica"])
        self.assertEqual(ue.get_material(e).is_a(), "IfcMaterialLayerSet")
        sec = 1 / math.cos(math.radians(30))
        eave = doc.ifc.roof_params(roof)["eave"]
        # (3 cm is too thin to span the wall's top: it rests 1 cm over the wall's outer top edge, not through it)
        self.assertLess(tiles.thickness * sec - 0.2 * math.tan(math.radians(30)), 0.0)
        self.assertAlmostEqual(eave, 2.8 + core_roofs.SEAT_MIN, places=6)
        bim.set_roof_carpentry(doc, roof)
        raised = doc.ifc.roof_params(roof)["eave"]
        tan = math.tan(math.radians(30))                   # (its rafters on the plates, the gap over them taken off)
        self.assertAlmostEqual(raised, 2.8 + tiles.thickness * sec - 0.2 * tan + 0.16 + 0.075 * sec + 0.06 * tan,
                               places=6)
        bim.set_type(doc, roof, concrete)                  # thicker: the top goes up, the underside stays
        p = doc.ifc.roof_params(roof)
        self.assertEqual((p["thickness"], p["spec"].key, ue.get_type(e).Name), (0.15, "cobertura_15",
                                                                                  concrete.name_pt))
        self.assertAlmostEqual(p["eave"], raised + (0.15 - tiles.thickness) * sec, places=6)
        self.assertIsNotNone(doc.ifc.carpentry_of(roof))
        self.assertEqual(ue.get_psets(doc.ifc.by_guid(roof))["Pset_RoofCommon"]["Reference"], concrete.name_pt)
        thicker = dataclasses.replace(concrete, layers=(("concreto", 0.20),))
        bim.save_type(doc, thicker, concrete)              # (the type editor) every roof of it follows
        p = doc.ifc.roof_params(roof)
        self.assertAlmostEqual(p["thickness"], 0.20, places=6)
        self.assertAlmostEqual(p["eave"], raised + (0.20 - tiles.thickness) * sec, places=6)
        self.assertEqual(len([k for k in doc.ifc.file.by_type("IfcRoofType") if k.Name == concrete.name_pt]), 1)
        old = bim.add_roof(doc, [(20.0, 0.0), (25.0, 0.0), (25.0, 4.0), (20.0, 4.0)], catalog.BY_KEY["laje_12"],
                           "flat", 0.0, 0.0, eave=3.0)          # (as before 0.278: a slab's layers, no type)
        self.assertIsNone(ue.get_type(doc.ifc.by_guid(old)))
        bim.set_type(doc, old, tiles)                      # (no wall under it: its underside stays)
        self.assertEqual(ue.get_type(doc.ifc.by_guid(old)).Name, tiles.name_pt)
        self.assertAlmostEqual(doc.ifc.roof_params(old)["eave"], 3.0 - 0.12 + tiles.thickness, places=6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertIsNone(ue.get_type(doc.ifc.by_guid(old)))
        doc.undo()
        doc.undo()
        self.assertEqual(ue.get_type(doc.ifc.by_guid(roof)).Name, concrete.name_pt)
        self.assertAlmostEqual(doc.ifc.roof_params(roof)["thickness"], 0.15, places=6)

    def test_block_roof_type(self):
        doc = Document()
        self._house(doc)
        from arqbim.core import roof_blocks as core_blocks
        from arqbim.core import roofs as core_roofs
        block = bim.fit_block_to_walls(doc, core_blocks.make(5.0, 3.0, 0.0, 10.0, 6.0, "hip", 30.0, 0.5))
        roof = bim.add_block_roof(doc, block, catalog.BY_KEY["telhado_ceramico"])
        self.assertEqual(ue.get_type(doc.ifc.by_guid(roof)).is_a(), "IfcRoofType")
        before = doc.ifc.roof_params(roof)["blocks"][0].eave
        bim.set_type(doc, roof, catalog.BY_KEY["cobertura_15"])
        after = doc.ifc.roof_params(roof)["blocks"][0].eave
        shift = core_roofs.seat(30.0, 0.15, 0.2) - core_roofs.seat(30.0, catalog.BY_KEY["telhado_ceramico"].thickness,
                                                                   0.2)
        for b, a in zip(before, after):
            self.assertAlmostEqual(a, b + shift, places=6)


class RailingTypeEditIfc(unittest.TestCase):
    """0.260: a type of the project's own (a copy of the cables, its cables 12 cm apart) saved with no railing of it
    — listed, its IfcRailingType made —; a railing made of it; removing it refused while in use, and the program's
    types never; the railing gone, removed (its IfcRailingType too); undone, back."""

    def test_own_type(self):
        from arqbim.ifc.edit import EditRefused
        doc = Document()
        own = dataclasses.replace(doc.ifc.railing_type("cabos"), key="proprio_1", name_pt="Cabos largos",
                                  name_en="Wide cables", gap=0.12)
        bim.set_railing_type(doc, own)
        self.assertIn("proprio_1", doc.ifc.railing_types())
        self.assertIn(("proprio_1", "Cabos largos"), doc.ifc.railing_type_choices())
        g = bim.add_railing(doc, [(0.0, 0.0, 0.0), (2.4, 0.0, 0.0)], None, "proprio_1")
        self.assertEqual(ue.get_type(doc.ifc.by_guid(g)).Name, "Cabos largos")
        with self.assertRaises(EditRefused):
            bim.remove_railing_type(doc, "proprio_1")
        with self.assertRaises(EditRefused):
            bim.remove_railing_type(doc, "barras")
        bim.delete(doc, [g])
        bim.remove_railing_type(doc, "proprio_1")
        self.assertNotIn("proprio_1", doc.ifc.railing_types())
        self.assertFalse([t for t in doc.ifc.file.by_type("IfcRailingType") if t.Name == "Cabos largos"])
        doc.undo()
        self.assertIn("proprio_1", doc.ifc.railing_types())
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class RailingColoursIfc(unittest.TestCase):
    """0.259: a railing of steel cables with a wooden rail: its mesh has each triangle's colour — the wood's and the
    stainless steel's among them —, a wall none (its class's colour); saved and opened again (its shapes then from
    the geometry cache), the colours are still there."""

    def test_colours(self):
        doc = Document()
        g = bim.add_railing(doc, [(0.0, 0.0, 0.0), (2.4, 0.0, 0.0)], None, "cabos")
        wall = bim.add_wall(doc, np.array((0.0, 3.0, 0.0)), np.array((4.0, 3.0, 0.0)), catalog.BY_KEY["parede_alv_20"])

        def colours(d):
            mesh = d.get(g).mesh
            self.assertIsNotNone(mesh.colors)
            self.assertEqual(len(mesh.colors), len(mesh.tris))
            return {tuple(round(float(v), 2) for v in c) for c in mesh.colors}

        found = colours(doc)
        for key in ("madeira", "inox"):
            self.assertIn(tuple(round(float(v), 2) for v in catalog.MATERIALS[key].color), found, key)
        self.assertIsNone(doc.get(wall).mesh.colors)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "guarda.ifc")
            doc.save(path)
            for _ in range(2):                                     # (the second time from the cache)
                other = Document()
                other.open(path)
                self.assertEqual(colours(other), found)


class Stairs(unittest.TestCase):
    """0.114: a stair rising 2,80 (16 risers of 17,5 cm, treads of 28 cm, 1 m wide) — straight: 4,20 m long, its
    volume its side × its width, Pset_StairCommon; an L (to the left: the second flight up +y from a landing); a
    U; mirrored: it turns the other way; the IFC valid."""

    def test_stairs(self):
        from arqbim.core import stairs as core_stairs
        doc = Document()
        slab = catalog.BY_KEY["laje_15"]
        straight = bim.add_stair(doc, np.array((0.0, 0.0, 0.0)), (1.0, 0.0), slab, "straight", 2.8)
        e = doc.ifc.by_guid(straight)
        self.assertEqual((e.is_a(), e.PredefinedType), ("IfcStair", "STRAIGHT_RUN_STAIR"))
        lo, hi = bounds(doc, straight)
        reach = 15 * 0.28 + core_stairs.BEARING                               # (its top resting on the floor)
        self.assertTrue(np.allclose(lo[:2], (0.0, -0.5)) and np.allclose(hi, (reach, 0.5, 2.8)), (lo, hi))
        ps = ue.get_psets(e)["Pset_StairCommon"]
        self.assertEqual((ps["NumberOfRiser"], ps["NumberOfTreads"]), (16, 15))
        self.assertAlmostEqual(ps["RiserHeight"] * doc.ifc.unit_scale, 0.175)
        side = core_stairs.flight_side(16, 0.175, 0.28, 0.15)
        area = abs(sum(side[k][0] * side[(k + 1) % len(side)][1] - side[(k + 1) % len(side)][0] * side[k][1]
                       for k in range(len(side)))) / 2
        self.assertAlmostEqual(doc.get(straight).mesh.volume(), area * 1.0, places=6)
        run = 7 * 0.28 + core_stairs.BEARING                                 # (each flight of the L / U: 8 risers)
        el = bim.add_stair(doc, np.array((10.0, 0.0, 0.0)), (1.0, 0.0), slab, "l", 2.8)
        lo, hi = bounds(doc, el)
        self.assertTrue(np.allclose(lo, (10.0, -0.5, 0.0)) and np.allclose(hi, (12.96, 0.5 + run, 2.8)), (lo, hi))
        self.assertEqual(doc.ifc.by_guid(el).PredefinedType, "QUARTER_TURN_STAIR")
        u = bim.add_stair(doc, np.array((20.0, 0.0, 0.0)), (1.0, 0.0), slab, "u", 2.8)
        lo, hi = bounds(doc, u)
        self.assertTrue(np.allclose(lo, (21.96 - run, -0.5, 0.0)) and np.allclose(hi, (22.96, 1.6, 2.8)), (lo, hi))
        self.assertEqual(ue.get_psets(doc.ifc.by_guid(u))["Pset_StairCommon"]["NumberOfTreads"], 14)
        bim.set_stair(doc, el, turn="right")
        lo, hi = bounds(doc, el)
        self.assertAlmostEqual(lo[1], -0.5 - run)
        bim.mirror_objects(doc, [el], (15.0, 0.0), (15.0, 1.0))
        self.assertEqual(doc.ifc.stair_params(el)["turn"], "left")
        bim.set_stair(doc, straight, form="u")                                # (its IFC kind follows)
        self.assertEqual(doc.ifc.by_guid(straight).PredefinedType, "HALF_TURN_STAIR")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class StairOneSlab(unittest.TestCase):
    """0.257: an L and a U rising 2,80 (1 m wide, 15 cm slab): their landing made with the flights — no edge drawn
    anywhere inside the landing's top (no tread of the flight on it, no seam), nor on its front below its top; the
    L's volume its two flights' sides × the width (the first with the landing), nothing counted twice; the IFC
    valid."""

    def test_one_slab(self):
        from arqbim.core import stairs as core_stairs
        doc = Document()
        slab = catalog.BY_KEY["laje_15"]
        for form, origin in (("l", 0.0), ("u", 10.0)):
            stair = bim.add_stair(doc, np.array((origin, 0.0, 0.0)), (1.0, 0.0), slab, form, 2.8)
            mesh = doc.get(stair).mesh
            pairs, _faces = mesh.edge_array()
            a, b = mesh.verts[pairs[:, 0]], mesh.verts[pairs[:, 1]]
            mid = (a + b) / 2
            x0 = origin + 7 * 0.28                                         # (the landing: from the last riser…)
            on_top = (np.abs(a[:, 2] - 1.4) < 1e-6) & (np.abs(b[:, 2] - 1.4) < 1e-6)
            inside = (mid[:, 0] > x0 + 0.01) & (mid[:, 0] < x0 + 0.99) & (mid[:, 1] > -0.49) & \
                (mid[:, 1] < (0.49 if form == "l" else 1.59))
            self.assertFalse(np.any(on_top & inside), (form, mid[on_top & inside]))
            front = (np.abs(mid[:, 0] - x0) < 1e-6) & (mid[:, 2] < 1.4 - 1e-6) & (mid[:, 2] > 1.25 + 1e-6) & \
                (np.abs(a[:, 2] - b[:, 2]) < 1e-9)                         # (a line along the landing's front)
            self.assertFalse(np.any(front), (form, mid[front]))
            if form == "l":
                def area(side):
                    return abs(sum(side[k][0] * side[(k + 1) % len(side)][1] - side[(k + 1) % len(side)][0] * side[k][1]
                                   for k in range(len(side)))) / 2
                first = core_stairs.flight_side(8, 0.175, 0.28, 0.15, ahead=1.0)
                second = core_stairs.flight_side(8, 0.175, 0.28, 0.15, 1.4, below=0.15)
                self.assertAlmostEqual(mesh.volume(), area(first) + area(second), places=6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class RoofParts(unittest.TestCase):
    """0.113: a flat roof made from a slab's outline (on its top); a drain on it (IfcWasteTerminal ROOFDRAIN, on its
    top); a 1 × 0,8 m opening right through a pitched roof (its volume less), going along when the roof is moved;
    the IFC valid."""

    def test_roof_parts(self):
        doc = Document()
        slab = bim.add_slab_outline(doc, [(0, 0), (8, 0), (8, 5), (0, 5)], 3.0, catalog.BY_KEY["laje_15"])
        ring, z = bim.face_outline(doc, slab, 0, (1.0, 1.0, 3.15))
        flat = bim.add_roof(doc, ring, catalog.BY_KEY["laje_15"], "flat", overhang=0.0, eave=z)
        lo, hi = bounds(doc, flat)
        self.assertAlmostEqual(hi[2], 3.15)
        drain = bim.add_drain(doc, flat, (4.0, 2.5))
        e = doc.ifc.by_guid(drain)
        self.assertEqual((e.is_a(), e.PredefinedType), ("IfcWasteTerminal", "ROOFDRAIN"))
        self.assertAlmostEqual(doc.ifc.placement(drain)[2, 3], 3.15)
        roof = bim.add_roof(doc, [(20, 0), (30, 0), (30, 6), (20, 6)], catalog.BY_KEY["laje_15"], "gable", 30.0, 0.0,
                            eave=3.0)
        vol = doc.get(roof).mesh.volume()
        hole = bim.add_vertical_opening(doc, roof, (22.0, 1.0), (23.0, 1.8))
        self.assertEqual(doc.ifc.by_guid(hole).is_a(), "IfcOpeningElement")
        cos = math.cos(math.radians(30))
        self.assertAlmostEqual(vol - doc.get(roof).mesh.volume(), 1.0 * 0.8 * 0.15 / cos, places=6)
        m = np.eye(4)
        m[:3, 3] = (0.0, 10.0, 0.0)
        bim.transform_objects(doc, [roof], m, "mover")
        self.assertAlmostEqual(vol - doc.get(roof).mesh.volume(), 1.0 * 0.8 * 0.15 / cos, places=6)   # (still cut)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class AttachToRoof(unittest.TestCase):
    """0.112: the four walls of a 10 × 6 m house and a column inside attached to its gable roof (30°, no eaves):
    the long walls stay 2,80 under the eaves, the end walls become gables (5 corners, their top the ridge's
    underside), the column reaches the slope over it; the roof made steeper, they follow; the IFC valid."""

    def test_attach_to_roof(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        walls = [bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
                 for a, b in (((0.0, 0.0), (10.0, 0.0)), ((10.0, 0.0), (10.0, 6.0)), ((10.0, 6.0), (0.0, 6.0)),
                              ((0.0, 6.0), (0.0, 0.0)))]
        column = bim.add_column(doc, np.array((5.0, 1.5, 0.0)), catalog.BY_KEY["pilar_30"], 2.0)
        roof = bim.add_roof(doc, [(-0.1, -0.1), (10.1, -0.1), (10.1, 6.1), (-0.1, 6.1)], catalog.BY_KEY["laje_15"],
                            "gable", 30.0, 0.0)
        bim.attach_top(doc, walls + [column], roof)
        t, cos = math.tan(math.radians(30)), math.cos(math.radians(30))
        under = 0.15 / cos
        eave = 2.8 + under - 0.2 * t                                          # (0.275: resting on the walls)
        ends = [w for w in walls if doc.ifc.wall_profile(w) is not None]
        self.assertEqual(len(ends), 2)                                        # (the gable ends)
        for w in ends:
            prof = doc.ifc.wall_profile(w)
            self.assertEqual(len(prof), 5)
            self.assertAlmostEqual(max(z for _x, z in prof), eave + 3.1 * t - under, places=6)
        for w in walls:
            if w not in ends:                                                 # (under the eaves: level)
                self.assertAlmostEqual(doc.ifc.wall_params(w)[1], eave + 0.1 * t - under, places=6)
        self.assertAlmostEqual(doc.ifc.constraints(column)["height"], eave + 1.6 * t - under, places=6)
        self.assertEqual(doc.ifc.constraints(column)["top_roof"], roof)
        bim.set_roof(doc, roof, slope=40.0)                                   # (still resting on the walls)
        t40, cos40 = math.tan(math.radians(40)), math.cos(math.radians(40))
        eave40 = 2.8 + 0.15 / cos40 - 0.2 * t40
        self.assertAlmostEqual(max(z for _x, z in doc.ifc.wall_profile(ends[0])), eave40 + 3.1 * t40 - 0.15 / cos40,
                               places=6)
        self.assertAlmostEqual(doc.ifc.constraints(column)["height"], eave40 + 1.6 * t40 - 0.15 / cos40, places=6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class OpeningKitsAndMarks(unittest.TestCase):
    """0.110: a door with a fanlight (80×210 + 50: 2,60 high in all, its type keeping the fanlight); doors and
    windows marked P1, P2… / J1… as they are placed, a copy the next mark; numbered again in reading order; a mark
    typed; an opening with no frame (the hole only); the IFC valid."""

    def test_kits_and_marks(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        top = bim.add_wall(doc, np.array((0.0, 5.0, 0.0)), np.array((8.0, 5.0, 0.0)), spec)
        low = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((8.0, 0.0, 0.0)), spec)
        kit = catalog.OPENING_BY_KEY["porta_80_bandeira"]
        d1 = bim.add_opening(doc, low, kit, bim.wall_frame(doc, low), 1.0, 1)
        type_ = ue.get_type(doc.ifc.by_guid(d1))
        self.assertAlmostEqual(ue.get_psets(type_)["ArqSynth_Parametros"]["Bandeira"], 0.5)
        d2 = bim.add_opening(doc, top, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, top), 5.0, 1)
        (lo1, hi1), (lo2, hi2) = bounds(doc, d1), bounds(doc, d2)
        self.assertAlmostEqual((hi1[2] - lo1[2]) - (hi2[2] - lo2[2]), 0.50, places=6)   # (the fanlight over it)
        self.assertGreater(len(doc.get(d1).mesh.verts), len(doc.get(d2).mesh.verts))    # (its transom and glass)
        w1 = bim.add_opening(doc, low, catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, low), 4.0, 1)
        tag = lambda g: doc.ifc.by_guid(g).Tag                                    # noqa: E731
        self.assertEqual((tag(d1), tag(d2), tag(w1)), ("P1", "P2", "J1"))
        m = np.eye(4)
        m[1, 3] = 10.0
        copies = bim.copy_objects(doc, [low], [m], "copiar")
        copied_doors = [d.GlobalId for d in doc.ifc.file.by_type("IfcDoor") if d.GlobalId not in (d1, d2)]
        self.assertEqual([tag(g) for g in copied_doors], ["P3"])
        self.assertEqual(bim.renumber_openings(doc), 5)
        # reading order: the copy (y = 10) first, then the top wall (5), then the low one (0)
        self.assertEqual((tag(copied_doors[0]), tag(d2), tag(d1)), ("P1", "P2", "P3"))
        bim.set_mark(doc, d1, "P10")
        self.assertEqual(tag(d1), "P10")
        vol = doc.get(top).mesh.volume()
        bare = bim.add_bare_opening(doc, top, catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, top), 1.0)
        e = doc.ifc.by_guid(bare)
        self.assertEqual((e.is_a(), e.HasFillings), ("IfcOpeningElement", ()))
        self.assertAlmostEqual(vol - doc.get(top).mesh.volume(), 1.2 * 1.2 * 0.2, places=6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        del copies


class WallProfile(unittest.TestCase):
    """0.109: a 6 m wall with a door given a gable profile (2,80 at the sides, 4,00 in the middle) — its volume,
    its height the gable's top; a profile cutting through the door refused; made 2 m longer, the gable stretches;
    plain again; the IFC valid."""

    def test_wall_profile(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, wall), 1.0, 1)
        door_cut = 0.8 * 2.1 * 0.2
        gable = [(0.0, 0.0), (6.0, 0.0), (6.0, 2.8), (3.0, 4.0), (0.0, 2.8)]
        bim.set_wall_profile(doc, wall, gable)
        area = 6 * 2.8 + 6 * 1.2 / 2
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), area * 0.2 - door_cut, places=6)
        self.assertAlmostEqual(doc.ifc.wall_params(wall)[1], 4.0)
        lo, hi = bounds(doc, wall)
        self.assertTrue(np.allclose((lo[1], hi[1]), (-0.1, 0.1)) and abs(hi[2] - 4.0) < 1e-6, (lo, hi))
        with self.assertRaises(ValueError):
            bim.set_wall_profile(doc, wall, [(0.0, 0.0), (6.0, 0.0), (6.0, 1.5), (0.0, 1.5)])    # through the door
        bim.resize_wall(doc, wall, at_end=2.0)
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), area * 8 / 6 * 0.2 - door_cut, places=6)
        self.assertEqual(len(doc.ifc.wall_profile(wall)), 5)
        self.assertAlmostEqual(max(x for x, _z in doc.ifc.wall_profile(wall)), 8.0)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.set_wall_profile(doc, wall, None)
        self.assertIsNone(doc.ifc.wall_profile(wall))
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), 8 * 4.0 * 0.2 - door_cut, places=6)

    def test_wall_profile_curves(self):
        """0.375 (the owner: «mais controlo para poder criar arcos ou curva Bézier»): a side of the profile an arc
        through a point (a round arch: its top, its area near a half disc's), another a Bézier curve; kept in the
        IFC and read back as drawn; stretched with the wall; straight again; a valid IFC."""
        import math
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        corners = [(0.0, 0.0), (6.0, 0.0), (6.0, 2.8), (0.0, 2.8)]
        arch = {"kind": "arc", "through": (3.0, 5.8)}                    # (a half circle of radius 3 on the top)
        bim.set_wall_profile(doc, wall, corners, [None, None, arch, None])
        pts, sides = doc.ifc.wall_profile_parts(wall)
        self.assertEqual((len(pts), sides[2]["kind"], tuple(np.round(sides[2]["through"], 6))), (4, "arc", (3.0, 5.8)))
        self.assertAlmostEqual(doc.ifc.wall_params(wall)[1], 5.8, places=6)
        area = 6 * 2.8 + math.pi * 9 / 2
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), area * 0.2, delta=area * 0.2 * 0.005)   # (in 5° pieces)
        bezier = {"kind": "bezier", "h1": (1.0, 2.0), "h2": (1.0, 0.8)}
        bim.set_wall_profile(doc, wall, corners, [None, None, arch, bezier])
        self.assertEqual([s and s["kind"] for s in doc.ifc.wall_profile_parts(wall)[1]], [None, None, "arc", "bezier"])
        self.assertGreater(len(doc.ifc.wall_profile(wall)), 40)            # (the outline: the curves in pieces)
        bim.resize_wall(doc, wall, at_end=2.0)                               # (stretched with the wall: 6 → 8 m)
        pts, sides = doc.ifc.wall_profile_parts(wall)
        self.assertAlmostEqual(sides[2]["through"][0], 4.0, places=6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.set_wall_profile(doc, wall, pts, [None] * 4)                     # (straight again: no curves kept)
        self.assertEqual(len(doc.ifc.wall_profile(wall)), 4)
        self.assertIsNone(doc.ifc._params(doc.ifc.by_guid(wall)).get("PerfilLados"))

    def test_wall_profile_holes(self):
        """0.410 (the owner: «desenhar (em edição) polígonos no meio para fazer buracos personalizados»): a 6 m wall
        with a door, a rectangular hole and a round one (four arcs) drawn in its profile — its volume less theirs, the
        body an extrusion with voids; kept in the IFC, stretched with the wall; the profile changed without saying
        the holes: they stay (one no longer inside goes); a hole over the door refused; a window over a hole
        refused; plain again: no holes; a valid IFC."""
        import math
        from arqbim.core import outline_loops
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, wall), 1.0, 1)
        door_cut = 0.8 * 2.1 * 0.2
        corners = [(0.0, 0.0), (6.0, 0.0), (6.0, 2.8), (0.0, 2.8)]
        square = outline_loops.rectangle((3.0, 1.0), (4.0, 2.0))
        disc = outline_loops.circle((5.0, 1.5), 0.4)
        bim.set_wall_profile(doc, wall, corners, [None] * 4, holes=[square, disc])
        holes = doc.ifc.wall_profile_holes(wall)
        self.assertEqual([len(h[0]) for h in holes], [4, 4])
        self.assertEqual([s and s["kind"] for s in holes[1][1]], ["arc"] * 4)
        solid = doc.ifc.by_guid(wall).Representation.Representations[0].Items[0]
        self.assertEqual(solid.SweptArea.is_a(), "IfcArbitraryProfileDefWithVoids")
        volume = (6 * 2.8 - 1.0 - math.pi * 0.16) * 0.2 - door_cut
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), volume, delta=0.002)
        q = ue.get_psets(doc.ifc.by_guid(wall))["Qto_WallBaseQuantities"]
        self.assertAlmostEqual(q["GrossSideArea"], 6 * 2.8 - 1.0 - math.pi * 0.16, delta=0.01)
        with self.assertRaises(ValueError):                              # (a hole over the door)
            bim.set_wall_profile(doc, wall, corners, [None] * 4, holes=[outline_loops.rectangle((0.9, 0.5),
                                                                                               (1.5, 1.5))])
        with self.assertRaises(ValueError):                              # (a hole poking out of the wall)
            bim.set_wall_profile(doc, wall, corners, [None] * 4, holes=[outline_loops.rectangle((5.5, 1.0),
                                                                                               (6.5, 2.0))])
        with self.assertRaises(ValueError):                              # (a window over a hole)
            bim.add_wall_opening(doc, wall, 2.8, 0.6, 0.6, 1.2)
        bim.resize_wall(doc, wall, at_end=2.0)                           # (stretched with the wall: 6 → 8 m)
        holes = doc.ifc.wall_profile_holes(wall)
        self.assertAlmostEqual(holes[0][0][0][0], 4.0, places=6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        # the profile changed, its holes not said: they stay — the round one, out of the shorter profile, goes
        bim.set_wall_profile(doc, wall, [(0.0, 0.0), (6.2, 0.0), (6.2, 2.8), (0.0, 2.8)])
        holes = doc.ifc.wall_profile_holes(wall)
        self.assertEqual(len(holes), 1)
        bim.set_wall_profile(doc, wall, None)
        self.assertEqual(doc.ifc.wall_profile_holes(wall), [])
        self.assertIsNone(doc.ifc._params(doc.ifc.by_guid(wall)).get("PerfilFuros"))


class OutlinesDrawn(unittest.TestCase):
    """0.410 (the owner: «assim como editamos o perfil da parede com Shift, Alt, quero que faça também o mesmo com o
    piso»; «buracos personalizados»): a slab's, a floor finish's and a ceiling's outline as drawn — sides arcs and
    curves, holes —, the body in pieces, the drawing kept beside it and read back while it is still that body."""

    def test_loops_text(self):
        from arqbim.core import outline_loops
        loops = [[[(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)],
                  [None, {"kind": "arc", "through": (5.0, 1.5)}, None, {"kind": "bezier", "h1": (-1, 2), "h2": (-1, 1)}]],
                 outline_loops.circle((2.0, 1.5), 0.5)]
        back = outline_loops.parse(outline_loops.text(loops))
        self.assertEqual([[s and s["kind"] for s in sd] for _c, sd in back],
                         [[None, "arc", None, "bezier"], ["arc"] * 4])
        self.assertTrue(outline_loops.matches(back, outline_loops.rings(loops)))
        self.assertFalse(outline_loops.matches(back, outline_loops.rings(loops)[:1]))
        self.assertIsNone(outline_loops.parse("nada"))
        self.assertIsNotNone(outline_loops.polygon(loops + [outline_loops.rectangle((3.5, 1.0), (4.5, 2.0))]))
        self.assertIsNone(outline_loops.polygon(loops + [outline_loops.rectangle((2.2, 1.2), (3.0, 1.8))]))  # (crosses)

    def test_slab_outline_drawn(self):
        import math
        from arqbim.core import outline_loops
        doc = Document()
        slab = bim.add_slab_outline(doc, [(0, 0), (6, 0), (6, 4), (0, 4)], 0.0, catalog.BY_KEY["laje_12"])
        loops = doc.ifc.slab_outline(slab)["loops"]
        self.assertEqual((len(loops), [s for s in loops[0][1]]), (1, [None] * 4))
        # the side x = 6 an arc bulging 1 m out; a square hole and a round one
        loops[0][1][1] = {"kind": "arc", "through": (7.0, 2.0)}
        loops += [outline_loops.rectangle((1.0, 1.0), (2.0, 2.0)), outline_loops.circle((4.0, 2.0), 0.5)]
        bim.set_slab_outline(doc, slab, loops=loops)
        info = doc.ifc.slab_outline(slab)
        self.assertEqual([[s and s["kind"] for s in sd] for _c, sd in info["loops"]],
                         [[None, "arc", None, None], [None] * 4, ["arc"] * 4])
        self.assertEqual(len(info["holes"]), 2)
        r = (1.0 + 4.0) / 2                                             # (the arc through (6,0) (7,2) (6,4): r 2,5)
        segment = r * r * math.acos((r - 1.0) / r) - (r - 1.0) * math.sqrt(2 * r * 1.0 - 1.0)
        area = 24 + segment - 1.0 - math.pi * 0.25
        self.assertAlmostEqual(info["area"], area, delta=0.02)
        self.assertEqual(doc.ifc._slab_solid(doc.ifc.by_guid(slab)).SweptArea.is_a(),
                         "IfcArbitraryProfileDefWithVoids")
        self.assertAlmostEqual(doc.get(slab).mesh.volume(), area * 0.12, delta=0.005)
        doc.undo()                                                      # (one undo step)
        self.assertEqual(len(doc.ifc.slab_outline(slab)["holes"]), 0)
        doc.redo()
        self.assertEqual(len(doc.ifc.slab_outline(slab)["loops"]), 3)
        # its corners moved the old way (by another command): the drawing no longer matches — its corners, straight
        ring = doc.ifc.slab_outline(slab)["outline"]
        bim.set_slab_outline(doc, slab, [(x + (0.5 if x > 6.5 else 0.0), y) for x, y in ring])
        loops = doc.ifc.slab_outline(slab)["loops"]
        self.assertFalse(outline_loops.curved(loops))
        self.assertGreater(len(loops[0][0]), 10)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_floor_and_ceiling_outline_drawn(self):
        from arqbim.core import outline_loops
        doc = Document()
        floor = bim.add_flooring(doc, [(0, 0), (5, 0), (5, 4), (0, 4)], "madeira")
        ceiling = bim.add_ceiling(doc, [(0, 0), (5, 0), (5, 4), (0, 4)])
        for guid in (floor, ceiling):
            loops = doc.ifc.ceiling_params(guid)["loops"]
            self.assertEqual(len(loops), 1)
            loops[0][1][0] = {"kind": "bezier", "h1": (1.5, -1.0), "h2": (3.5, -1.0)}      # (the side y = 0 curved out)
            loops.append(outline_loops.circle((2.5, 2.0), 0.6))
            bim.set_covering_outline(doc, guid, loops)
            p = doc.ifc.ceiling_params(guid)
            self.assertEqual([[s and s["kind"] for s in sd] for _c, sd in p["loops"]], [["bezier", None, None, None],
                                                                                         ["arc"] * 4])
            self.assertEqual(len(p["holes"]), 1)
            self.assertGreater(len(p["outline"]), 10)
            self.assertIsNotNone(doc.get(guid).mesh)
        q = ue.get_psets(doc.ifc.by_guid(floor))["Qto_CoveringBaseQuantities"]
        self.assertGreater(q["GrossArea"], 20.0 - 1.2)                   # (the curve adds, the round hole takes)
        with self.assertRaises(ValueError):                              # (a hole across the edge)
            bim.set_covering_outline(doc, floor, [[[(0, 0), (5, 0), (5, 4), (0, 4)], [None] * 4],
                                                  outline_loops.rectangle((4.5, 1.0), (5.5, 2.0))])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class Mirror(unittest.TestCase):
    """0.108: a corner of two walls with a door (hinged left), a column, an L slab and a beam mirrored about the
    line x = 10 as copies — the walls reflected (16..20), still joined; the door at the reflected place, hinged
    right; the column, slab (same area) and beam reflected; the originals as they were. Moved instead: a column
    reflected in place. The IFC valid."""

    def test_mirror(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        a = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), spec)
        b = bim.add_wall(doc, np.array((4.0, 0.0, 0.0)), np.array((4.0, 3.0, 0.0)), spec,
                         prev=(a, np.array((1.0, 0.0, 0.0))))
        door = bim.add_opening(doc, a, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, a), 1.0, 1)
        column = bim.add_column(doc, np.array((2.0, 5.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        slab = bim.add_slab_outline(doc, [(0, 6), (6, 6), (6, 9), (3, 9), (3, 11), (0, 11)], 0.0,
                                    catalog.BY_KEY["laje_12"])
        beam = bim.add_beam(doc, np.array((0.0, 12.0, 2.5)), np.array((4.0, 12.0, 2.5)), catalog.BY_KEY["viga_20x40"],
                            2.8)
        door_lo, door_hi = bounds(doc, door)
        made, left_out = bim.mirror_objects(doc, [a, b, door, column, slab, beam], (10.0, 0.0), (10.0, 1.0), copy=True)
        self.assertEqual(left_out, [])
        self.assertEqual(len(made), 5)                                       # (the door goes with its wall)
        walls = [g for g in made if doc.ifc.kind_of(g) == "wall"]
        lo = np.min([bounds(doc, g)[0] for g in walls], axis=0)
        hi = np.max([bounds(doc, g)[1] for g in walls], axis=0)
        alo = np.min([bounds(doc, g)[0] for g in (a, b)], axis=0)
        ahi = np.max([bounds(doc, g)[1] for g in (a, b)], axis=0)
        self.assertTrue(np.allclose((lo[0], hi[0]), (20 - ahi[0], 20 - alo[0])) and np.allclose(lo[1:], alo[1:]))
        self.assertIn(walls[1], doc.ifc.joined_walls([walls[0]]))           # the copies' corner
        doors = [d.GlobalId for d in doc.ifc.file.by_type("IfcDoor") if d.GlobalId != door]
        self.assertEqual(len(doors), 1)
        lo, hi = bounds(doc, doors[0])
        self.assertTrue(np.allclose((lo[0], hi[0]), (20 - door_hi[0], 20 - door_lo[0]), atol=1e-6), (lo, hi))
        self.assertTrue(np.allclose(lo[1:], door_lo[1:], atol=1e-6) and np.allclose(hi[1:], door_hi[1:], atol=1e-6))
        self.assertTrue(doc.ifc.by_guid(doors[0]).OperationType.endswith("RIGHT"))
        self.assertTrue(doc.ifc.by_guid(door).OperationType.endswith("LEFT"))
        col = next(g for g in made if doc.ifc.kind_of(g) == "column")
        self.assertTrue(np.allclose(doc.ifc.column_box(col)[0], (18.0, 5.0)))
        sl = next(g for g in made if doc.ifc.kind_of(g) == "slab")
        self.assertAlmostEqual(doc.ifc.slab_outline(sl)["area"], 24.0)
        lo, hi = bounds(doc, sl)
        self.assertTrue(np.allclose((lo[0], hi[0]), (14.0, 20.0)))
        bm = next(g for g in made if doc.ifc.kind_of(g) == "beam")
        s, e, _top, _w, _h = doc.ifc.beam_params(bm)
        self.assertTrue(np.allclose(sorted((s[0], e[0])), (16.0, 20.0)))
        self.assertTrue(np.allclose(doc.ifc.column_box(column)[0], (2.0, 5.0)))     # the originals stay
        moved, _l = bim.mirror_objects(doc, [column], (0.0, 0.0), (0.0, 1.0))
        self.assertEqual(moved, [column])
        self.assertTrue(np.allclose(doc.ifc.column_box(column)[0], (-2.0, 5.0)))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertTrue(np.allclose(doc.ifc.column_box(column)[0], (2.0, 5.0)))


class AttachTop(unittest.TestCase):
    """0.106: a wall and a column 2,80 high under a slab whose underside is at 3,00 — attached by their top, they
    reach it; the slab moved 50 cm up, they follow; another (thicker) slab type, its top kept, they follow its
    underside down; let go (not connected), they stay; undo."""

    def test_attach_top(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 1.0, 0.0)), np.array((6.0, 1.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        column = bim.add_column(doc, np.array((3.0, 3.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        slab = bim.add_slab_outline(doc, [(-1, -1), (7, -1), (7, 5), (-1, 5)], 3.0, catalog.BY_KEY["laje_12"])
        self.assertAlmostEqual(doc.ifc.slab_outline(slab)["bottom"], 3.0)           # (off a storey: on the level)
        self.assertEqual(bim.attach_top(doc, [wall, column, slab], slab), [wall, column])
        height = lambda g: doc.ifc.constraints(g)["height"]                           # noqa: E731
        self.assertAlmostEqual(height(wall), 3.0)
        self.assertAlmostEqual(height(column), 3.0)
        self.assertEqual(doc.ifc.constraints(wall)["top_slab"], slab)
        m = np.eye(4)
        m[2, 3] = 0.5
        bim.transform_objects(doc, [slab], m, "mover")
        self.assertAlmostEqual(height(wall), 3.5)
        self.assertAlmostEqual(height(column), 3.5)
        bim.set_type(doc, slab, catalog.BY_KEY["laje_15"])                             # (its top stays)
        self.assertAlmostEqual(height(wall), 3.47)
        lo, hi = bounds(doc, wall)
        self.assertAlmostEqual(hi[2], 3.47)
        bim.set_constraints(doc, wall, top=None)                                       # let go
        self.assertIsNone(doc.ifc.constraints(wall)["top_slab"])
        bim.transform_objects(doc, [slab], m, "mover")
        self.assertAlmostEqual(height(wall), 3.47)                                     # it stays
        self.assertAlmostEqual(height(column), 3.97)                                   # (the column still follows)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        for _ in range(3):
            doc.undo()
        self.assertAlmostEqual(height(wall), 3.5)


class DetachTopResetProfile(unittest.TestCase):
    """0.298 (the tab Modify | Walls): a wall and a column attached to a slab let go — they keep 3,00 when the slab
    goes up, undo ties them again; the gable walls of a house attached to its roof made plain again — a rectangle as
    tall as the gable's top, no longer the roof's (the roof made steeper, they stay); a long wall under the eaves let
    go of the roof; nothing tied, nothing done; the IFC valid."""

    def test_detach_and_reset(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 1.0, 0.0)), np.array((6.0, 1.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        column = bim.add_column(doc, np.array((3.0, 3.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        slab = bim.add_slab_outline(doc, [(-1, -1), (7, -1), (7, 5), (-1, 5)], 3.0, catalog.BY_KEY["laje_12"])
        bim.attach_top(doc, [wall, column], slab)
        self.assertEqual((doc.ifc.top_tied(wall), doc.ifc.top_tied(column)), ("slab", "slab"))
        self.assertEqual(sorted(bim.detach_top(doc, [wall, column, slab])), sorted([wall, column]))
        self.assertEqual((doc.ifc.top_tied(wall), doc.ifc.top_tied(column)), (None, None))
        m = np.eye(4)
        m[2, 3] = 0.5
        bim.transform_objects(doc, [slab], m, "mover")
        height = lambda g: doc.ifc.constraints(g)["height"]                           # noqa: E731
        self.assertAlmostEqual(height(wall), 3.0)
        self.assertAlmostEqual(height(column), 3.0)
        self.assertEqual(bim.detach_top(doc, [wall]), [])                              # (nothing tied)
        doc.undo()
        doc.undo()
        self.assertEqual(doc.ifc.top_tied(wall), "slab")
        house = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        walls = [bim.add_wall(house, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
                 for a, b in (((0.0, 0.0), (10.0, 0.0)), ((10.0, 0.0), (10.0, 6.0)), ((10.0, 6.0), (0.0, 6.0)),
                              ((0.0, 6.0), (0.0, 0.0)))]
        roof = bim.add_roof(house, [(-0.1, -0.1), (10.1, -0.1), (10.1, 6.1), (-0.1, 6.1)], catalog.BY_KEY["laje_15"],
                            "gable", 30.0, 0.0)
        bim.attach_top(house, walls, roof)
        ends = [w for w in walls if house.ifc.wall_profile(w) is not None]
        tops = {w: max(z for _x, z in house.ifc.wall_profile(w)) for w in ends}
        self.assertEqual(sorted(bim.reset_wall_profiles(house, walls)), sorted(ends))   # (the others: no profile)
        for w in ends:
            self.assertIsNone(house.ifc.wall_profile(w))
            self.assertIsNone(house.ifc.top_tied(w))
            self.assertAlmostEqual(house.ifc.wall_params(w)[1], tops[w])
        bim.set_roof(house, roof, slope=40.0)
        for w in ends:
            self.assertIsNone(house.ifc.wall_profile(w))                               # (they stay)
            self.assertAlmostEqual(house.ifc.wall_params(w)[1], tops[w])
        long_wall = next(w for w in walls if w not in ends)
        self.assertEqual(house.ifc.top_tied(long_wall), "roof")
        self.assertEqual(bim.detach_top(house, [long_wall]), [long_wall])
        before = house.ifc.wall_params(long_wall)[1]
        bim.set_roof(house, roof, slope=30.0)
        self.assertAlmostEqual(house.ifc.wall_params(long_wall)[1], before)
        self.assertEqual(bim.reset_wall_profiles(house, [long_wall]), [])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        self.assertEqual(house.ifc.validate(express_rules=True), [])


class FlipAndJoinWalls(unittest.TestCase):
    """0.299 (the tab Modify | Walls): a wall with its insulation on one face flipped — the insulation on the other
    face, the wall's body where it was; flipped back; flipped and given another type, still flipped and its layers in
    its thickness; undo. Two walls in a corner let go and joined again — the corner as it was; a wall ending on
    another's side, joined: a T, stopped at its face; one far away: nothing to join; the IFC valid."""

    def test_flip(self):
        doc = Document()
        etics = catalog.TypeSpec("parede_etics_test", "wall", "Parede com ETICS", "Wall with ETICS",
                                 layers=(("reboco", 0.02), ("bloco", 0.20), ("la", 0.06), ("reboco", 0.01)))
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), etics)

        def insulation():
            layers = doc.ifc.layers([wall])[wall]
            (n, d0, d1), = [(n, d0, d1) for hatch, n, d0, d1 in layers if hatch == "insulation"]
            return round(float(n @ np.array((0.0, 1.0, 0.0))) * (d0 + d1) / 2, 6)

        def span():
            layers = doc.ifc.layers([wall])[wall]
            return round(min(d0 for _h, _n, d0, _d1 in layers), 6), round(max(d1 for _h, _n, _d0, d1 in layers), 6)

        self.assertAlmostEqual(insulation(), 0.105)                  # (+y: 0.075..0.135 of −0.145..0.145)
        lo, hi = bounds(doc, wall)
        self.assertEqual(bim.flip_walls(doc, [wall]), [wall])
        self.assertEqual(doc.ifc.layer_sense(wall), "NEGATIVE")
        self.assertAlmostEqual(insulation(), -0.105)                 # (the other face)
        self.assertEqual(span(), (-0.145, 0.145))
        lo2, hi2 = bounds(doc, wall)
        self.assertTrue(np.allclose(lo, lo2) and np.allclose(hi, hi2))
        bim.flip_walls(doc, [wall])
        self.assertAlmostEqual(insulation(), 0.105)
        bim.flip_walls(doc, [wall])
        thick = catalog.TypeSpec("parede_etics_test2", "wall", "Parede com ETICS 35", "Wall with ETICS 35",
                                 layers=(("reboco", 0.02), ("bloco", 0.25), ("la", 0.06), ("reboco", 0.02)))
        bim.set_type(doc, wall, thick)
        self.assertEqual(doc.ifc.layer_sense(wall), "NEGATIVE")
        self.assertEqual(span(), (-0.175, 0.175))
        self.assertAlmostEqual(insulation(), -(0.175 - 0.02 - 0.03))   # (still on the other face)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        doc.undo()
        self.assertAlmostEqual(insulation(), 0.105)

    def test_join_ends(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        a = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), spec)
        b = bim.add_wall(doc, np.array((5.0, 0.0, 0.0)), np.array((5.0, 4.0, 0.0)), spec,
                         prev=(a, np.array((1.0, 0.0, 0.0))))
        corner = [bounds(doc, g) for g in (a, b)]
        bim.unjoin_walls(doc, [a, b])
        self.assertEqual(doc.ifc.joined_walls([a]), [])
        self.assertEqual(sorted(bim.join_wall_ends(doc, [a, b])), sorted([a, b]))
        self.assertEqual(doc.ifc.joined_walls([a]), [b])
        for g, (lo, hi) in zip((a, b), corner):
            lo2, hi2 = bounds(doc, g)
            self.assertTrue(np.allclose(lo, lo2, atol=1e-6) and np.allclose(hi, hi2, atol=1e-6), g)
        c = bim.add_wall(doc, np.array((2.0, 3.0, 0.0)), np.array((2.0, 0.0, 0.0)), spec)   # (on a's axis, not joined)
        self.assertNotIn(c, doc.ifc.joined_walls([a]))
        self.assertEqual(sorted(bim.join_wall_ends(doc, [c])), sorted([a, c]))
        self.assertIn(c, doc.ifc.joined_walls([a]))
        _s, end, _t = doc.ifc.wall_axis(c)
        self.assertAlmostEqual(end[1], 0.1)                          # (stopped at a's face)
        far = bim.add_wall(doc, np.array((0.0, 8.0, 0.0)), np.array((3.0, 8.0, 0.0)), spec)
        self.assertEqual(bim.join_wall_ends(doc, [far]), [])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class SplitGapTrimExtend(unittest.TestCase):
    """0.300 (the tab Modify | Walls): a 10 m wall with a door split at 5 m with a 4 cm gap — 4,98 + 4,98, the new
    part from 5,02, not joined to each other; a gap over the door refused. A boundary wall at x = 9: a wall short of it
    extended and one through it trimmed — both stop at its face, in T; one at its start makes a corner (the boundary
    runs on past it); one beyond its end stops on its line, not joined; a parallel one refused; undo; the IFC valid."""

    def test_split_gap(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((10.0, 0.0, 0.0)), spec)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, wall), 1.0, 1)
        with self.assertRaises(ValueError):
            bim.split_wall(doc, wall, 1.3, gap=0.1)                        # (in the door)
        new = bim.split_wall(doc, wall, 5.0, gap=0.04)
        self.assertAlmostEqual(doc.ifc.wall_params(wall)[0], 4.98)
        self.assertAlmostEqual(doc.ifc.wall_params(new)[0], 4.98)
        start, _end, _t = doc.ifc.wall_axis(new)
        self.assertAlmostEqual(start[0], 5.02)
        self.assertNotIn(new, doc.ifc.joined_walls([wall]))
        self.assertEqual(len(doc.ifc.file.by_type("IfcDoor")), 1)
        doc.undo()
        self.assertAlmostEqual(doc.ifc.wall_params(wall)[0], 10.0)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_trim_extend(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        boundary = bim.add_wall(doc, np.array((9.0, -2.0, 0.0)), np.array((9.0, 6.0, 0.0)), spec)
        short = bim.add_wall(doc, np.array((0.0, 3.0, 0.0)), np.array((5.0, 3.0, 0.0)), spec)
        long_ = bim.add_wall(doc, np.array((0.0, 1.0, 0.0)), np.array((12.0, 1.0, 0.0)), spec)
        low = bim.add_wall(doc, np.array((0.0, -2.0, 0.0)), np.array((5.0, -2.0, 0.0)), spec)
        beyond = bim.add_wall(doc, np.array((0.0, 10.0, 0.0)), np.array((5.0, 10.0, 0.0)), spec)
        side = bim.add_wall(doc, np.array((10.0, 0.0, 0.0)), np.array((10.0, 4.0, 0.0)), spec)
        end_x = lambda g: doc.ifc.wall_axis(g)[1][0]                                    # noqa: E731
        self.assertTrue(bim.trim_extend_wall(doc, short, boundary, (2.0, 3.0)))
        self.assertAlmostEqual(end_x(short), 8.9)
        self.assertTrue(bim.trim_extend_wall(doc, long_, boundary, (2.0, 1.0)))
        self.assertAlmostEqual(end_x(long_), 8.9)
        self.assertTrue({short, long_} <= set(doc.ifc.joined_walls([boundary])))
        self.assertTrue(bim.trim_extend_wall(doc, low, boundary, (2.0, -2.0)))
        self.assertAlmostEqual(end_x(low), 8.9)
        self.assertAlmostEqual(doc.ifc.wall_axis(boundary)[0][1], -2.1)              # (it runs on past the corner)
        self.assertFalse(bim.trim_extend_wall(doc, beyond, boundary, (2.0, 10.0)))
        self.assertAlmostEqual(end_x(beyond), 9.0)
        self.assertNotIn(beyond, doc.ifc.joined_walls([boundary]))
        with self.assertRaises(ValueError):
            bim.trim_extend_wall(doc, side, boundary, (10.0, 1.0))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertAlmostEqual(end_x(beyond), 5.0)


class AttachBase(unittest.TestCase):
    """0.302 (Revit's Attach / Detach Base): a wall and a column on a storey at 0,00 over a slab whose top is at −0,18
    — attached by their base they stand on it (base −0,18, top still 2,80); the slab 20 cm lower, they follow; the
    wall let go: the slab lower again, the wall stays and the column follows; nothing tied, nothing let go; undo; the
    IFC valid."""

    def test_attach_base(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        column = bim.add_column(doc, np.array((3.0, 0.6, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        slab = bim.add_slab_outline(doc, [(-1, -1), (6, -1), (6, 2), (-1, 2)], -0.3, catalog.BY_KEY["laje_12"])
        base = lambda g: float(doc.ifc._placement_si(doc.ifc.by_guid(g))[2, 3])        # noqa: E731
        top = lambda g: base(g) + doc.ifc.constraints(g)["height"]                    # noqa: E731
        self.assertEqual(sorted(bim.attach_base(doc, [wall, column, slab], slab)), sorted([wall, column]))
        for g in (wall, column):
            self.assertAlmostEqual(base(g), -0.18)
            self.assertAlmostEqual(top(g), 2.8)
            self.assertEqual(doc.ifc.base_tied(g), slab)
        m = np.eye(4)
        m[2, 3] = -0.2
        bim.transform_objects(doc, [slab], m, "mover")
        self.assertAlmostEqual(base(wall), -0.38)
        self.assertAlmostEqual(base(column), -0.38)
        self.assertAlmostEqual(top(wall), 2.8)
        self.assertEqual(bim.detach_base(doc, [wall]), [wall])
        self.assertIsNone(doc.ifc.base_tied(wall))
        bim.transform_objects(doc, [slab], m, "mover")
        self.assertAlmostEqual(base(wall), -0.38)                                     # (it stays)
        self.assertAlmostEqual(base(column), -0.58)                                   # (the column follows)
        self.assertEqual(bim.detach_base(doc, [wall]), [])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        doc.undo()
        self.assertEqual(doc.ifc.base_tied(wall), slab)


class WallOpening(unittest.TestCase):
    """0.303 (Revit's Wall Opening): a 1,20 × 1,00 opening 2 m along a 6 m wall, 0,90 over its base — a hole right
    through (its volume less), no door or window, an IfcOpeningElement; the wall moved, it goes along; one past the
    wall's top, or past its end, refused; in a gable profile, one under the gable allowed; undo; the IFC valid."""

    def test_wall_opening(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), spec)
        other = bim.add_wall(doc, np.array((6.0, 0.0, 0.0)), np.array((6.0, 4.0, 0.0)), spec,
                             prev=(wall, np.array((1.0, 0.0, 0.0))))
        volume = doc.get(wall).mesh.volume()
        hole = bim.add_wall_opening(doc, wall, 2.0, 1.2, 1.0, 0.9)
        e = doc.ifc.by_guid(hole)
        self.assertEqual((e.is_a(), e.PredefinedType, e.HasFillings), ("IfcOpeningElement", "OPENING", ()))
        self.assertAlmostEqual(volume - doc.get(wall).mesh.volume(), 1.2 * 1.0 * 0.2, places=6)
        lo, hi = doc.ifc.opening_bounds(wall)                                    # (in the wall's frame)
        self.assertTrue(np.allclose((lo[0], hi[0], lo[2], hi[2]), (2.0, 3.2, 0.9, 1.9), atol=1e-6), (lo, hi))
        y = float(doc.ifc._placement_si(e)[1, 3])
        m = np.eye(4)
        m[1, 3] = 1.0
        bim.transform_objects(doc, [wall], m, "mover")
        self.assertAlmostEqual(float(doc.ifc._placement_si(doc.ifc.by_guid(hole))[1, 3]) - y, 1.0)
        doc.undo()
        with self.assertRaises(ValueError):
            bim.add_wall_opening(doc, wall, 2.0, 1.2, 1.0, 2.0)                   # (past its top: 2,80)
        with self.assertRaises(ValueError):
            bim.add_wall_opening(doc, wall, 5.5, 0.8, 1.0, 0.9)                   # (past its end)
        bim.set_wall_profile(doc, other, [(0.0, 0.0), (4.0, 0.0), (4.0, 2.8), (2.0, 4.0), (0.0, 2.8)])
        bim.add_wall_opening(doc, other, 1.6, 0.8, 0.6, 3.0)                      # (under the gable)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        doc.undo()
        doc.undo()
        self.assertEqual(len(doc.ifc.file.by_type("IfcOpeningElement")), 0)


class WallSweep(unittest.TestCase):
    """0.304 (Revit's Wall Sweep): a 10 × 6 m house drawn as a loop, a door in its south wall — a skirting board
    clicked on the south wall's inner face runs all round the room (closed), less the door; an outside cornice
    clicked on its outer face runs all round the house; the east wall moved 1 m out, both follow (2 m longer); an L of
    two walls, a sweep on its outer face: from one free end to the other, not closed; the IFC valid."""

    def test_wall_sweep(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        walls = bim.add_wall_loop(doc, [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (10.0, 6.0, 0.0), (0.0, 6.0, 0.0)], spec)
        south = next(g for g in walls
                     if abs(doc.ifc.wall_axis(g)[0][1]) < 1e-6 and abs(doc.ifc.wall_axis(g)[1][1]) < 1e-6)
        east = next(g for g in walls if abs(doc.ifc.wall_axis(g)[0][0] - 10.0) < 1e-6
                    and abs(doc.ifc.wall_axis(g)[1][0] - 10.0) < 1e-6)
        bim.add_opening(doc, south, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, south), 4.0, 1)
        length = lambda g: doc.ifc.describe(g)["params"]["length"]                    # noqa: E731
        inside = bim.wall_sweep(doc, south, (5.0, 0.1), "rodape")
        self.assertTrue(doc.ifc.profile_params(inside)["closed"])
        inner = 2 * (9.8 + 5.8)
        before = length(inside)
        self.assertTrue(inner - 1.0 < before < inner - 0.6, before)                   # (less the door)
        outside = bim.wall_sweep(doc, south, (5.0, -0.1), "cimalha")
        self.assertTrue(doc.ifc.profile_params(outside)["closed"])
        self.assertAlmostEqual(length(outside), 2 * (10.2 + 6.2), places=2)
        m = np.eye(4)
        m[0, 3] = 1.0
        bim.transform_objects(doc, [east], m, "mover")
        self.assertAlmostEqual(length(inside) - before, 2.0, places=2)
        self.assertAlmostEqual(length(outside), 2 * (11.2 + 6.2), places=2)
        a = bim.add_wall(doc, np.array((0.0, 20.0, 0.0)), np.array((4.0, 20.0, 0.0)), spec)
        bim.add_wall(doc, np.array((4.0, 20.0, 0.0)), np.array((4.0, 23.0, 0.0)), spec,
                     prev=(a, np.array((1.0, 0.0, 0.0))))
        open_run = bim.wall_sweep(doc, a, (2.0, 19.9), "rodape")                     # (outside the L)
        self.assertFalse(doc.ifc.profile_params(open_run)["closed"])
        self.assertAlmostEqual(length(open_run), 4.1 + 3.1, places=2)
        self.assertIsNone(bim.wall_sweep(doc, a, (0.0, 20.0), "rodape"))             # (its end, not a face)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class WallReveal(unittest.TestCase):
    """0.305 (Revit's Wall Reveal): a 6 m wall with a level reveal 2 × 1 cm on its left face at 1,00 — its volume
    less by 6 × 0,02 × 0,01; made 2 m longer, the reveal too; a vertical one on its right face at 3,00; split at 5 m,
    both parts keep the level reveal and the first the vertical one; merged again, one level reveal; the vertical one
    taken away; a reveal deeper than half the wall refused; the IFC valid."""

    def test_wall_reveal(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), spec)
        volume = doc.get(wall).mesh.volume()
        level = bim.add_wall_reveal(doc, wall, 1, False, 1.0)
        self.assertEqual(doc.ifc.reveal_params(level), {"side": 1, "vertical": False, "at": 1.0, "width": 0.02,
                                                        "depth": 0.01})
        self.assertEqual(doc.ifc.by_guid(level).PredefinedType, "RECESS")
        self.assertAlmostEqual(volume - doc.get(wall).mesh.volume(), 6 * 0.02 * 0.01, places=7)
        bim.resize_wall(doc, wall, at_end=2.0)
        self.assertAlmostEqual(8 * 2.8 * 0.2 - doc.get(wall).mesh.volume(), 8 * 0.02 * 0.01, places=7)
        bim.add_wall_reveal(doc, wall, -1, True, 3.0)
        self.assertAlmostEqual(8 * 2.8 * 0.2 - doc.get(wall).mesh.volume(), (8 + 2.8) * 0.02 * 0.01, places=7)
        new = bim.split_wall(doc, wall, 5.0)
        kinds = lambda g: sorted(r["vertical"] for _o, r in doc.ifc.wall_reveals(g))   # noqa: E731
        self.assertEqual((kinds(wall), kinds(new)), ([False, True], [False]))
        self.assertAlmostEqual(3 * 2.8 * 0.2 - doc.get(new).mesh.volume(), 3 * 0.02 * 0.01, places=7)
        bim.merge_walls(doc, wall, new)
        self.assertEqual(kinds(wall), [False, True])
        vertical = next(o for o, r in doc.ifc.wall_reveals(wall) if r["vertical"])
        bim.remove_wall_reveal(doc, wall, vertical)
        self.assertEqual(kinds(wall), [False])
        with self.assertRaises(ValueError):
            bim.add_wall_reveal(doc, wall, 1, False, 2.0, 0.02, 0.15)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class WallJoins(unittest.TestCase):
    """0.301 (Revit's Wall Joins): an L of two walls drawn in a chain — the first runs through the corner (to 5,10),
    the second stops at its face; the second made to run through: it reaches 5,10 below the corner and the first
    stops at its face (4,90); mitred: both end at the axes' crossing, cut at 45°, kept when a wall moves (the corner
    still mitred); a corner at 60° refused (mitred anyway); an end with no corner refused; undo; the IFC valid."""

    def test_wall_joins(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        a = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), spec)
        b = bim.add_wall(doc, np.array((5.0, 0.0, 0.0)), np.array((5.0, 4.0, 0.0)), spec,
                         prev=(a, np.array((1.0, 0.0, 0.0))))
        end = lambda g: doc.ifc.wall_axis(g)[1]                                     # noqa: E731
        start = lambda g: doc.ifc.wall_axis(g)[0]                                   # noqa: E731
        self.assertAlmostEqual(end(a)[0], 5.1)                                      # (a runs through)
        self.assertAlmostEqual(start(b)[1], 0.1)
        self.assertEqual(bim.set_wall_corner(doc, b, "start", "butt"), a)
        self.assertAlmostEqual(start(b)[1], -0.1)                                   # (b runs through now)
        self.assertAlmostEqual(end(a)[0], 4.9)
        self.assertIn(b, doc.ifc.joined_walls([a]))
        bim.set_wall_corner(doc, a, "end", "mitre")
        self.assertAlmostEqual(end(a)[0], 5.0)
        self.assertAlmostEqual(start(b)[1], 0.0)
        self.assertAlmostEqual(abs(doc.ifc.wall_cuts(a)[1]), 45.0)
        m = np.eye(4)
        m[0, 3] = 1.0
        bim.transform_objects(doc, [b], m, "mover")                                 # (a stretches to it)
        self.assertAlmostEqual(end(a)[0], 6.0)
        self.assertAlmostEqual(abs(doc.ifc.wall_cuts(a)[1]), 45.0)                  # (still mitred)
        c = bim.add_wall(doc, np.array((0.0, 10.0, 0.0)), np.array((4.0, 10.0, 0.0)), spec)
        d = bim.add_wall(doc, np.array((4.0, 10.0, 0.0)), np.array((6.0, 10.0 + 2 * math.sqrt(3), 0.0)), spec,
                         prev=(c, np.array((1.0, 0.0, 0.0))))
        with self.assertRaises(ValueError):
            bim.set_wall_corner(doc, d, "start", "butt")
        with self.assertRaises(ValueError):
            bim.set_wall_corner(doc, c, "start", "butt")                            # (its start: no corner)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        doc.undo()
        doc.undo()
        doc.undo()
        self.assertAlmostEqual(end(a)[0], 4.9)                                      # (back to b through)


class MergeStraightenUnjoin(unittest.TestCase):
    """0.105: two walls in line made one — the second's door and its corner with a third go to the first (the
    door where it was); the second drawn the other way round too; walls apart or of another type refused. A wall
    2° off the red axis made straight, the wall joined to it following. A wall's joints let go: it stays put."""

    def test_merge_straighten_unjoin(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        a = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), spec)
        b = bim.add_wall(doc, np.array((5.0, 0.0, 0.0)), np.array((10.0, 0.0, 0.0)), spec)
        c = bim.add_wall(doc, np.array((10.0, 0.0, 0.0)), np.array((10.0, 5.0, 0.0)), spec,
                         prev=(b, np.array((1.0, 0.0, 0.0))))
        door = bim.add_opening(doc, b, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, b), 1.0, 1)
        lo0, hi0 = bounds(doc, door)
        bim.merge_walls(doc, a, b)
        self.assertIsNone(doc.ifc.by_guid(b))
        self.assertAlmostEqual(doc.ifc.wall_params(a)[0], 10.1)                 # (through the corner, as b was)
        self.assertEqual(doc.ifc.host_wall(door), a)
        lo1, hi1 = bounds(doc, door)
        self.assertTrue(np.allclose(lo0, lo1) and np.allclose(hi0, hi1))
        self.assertIn(c, doc.ifc.joined_walls([a]))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertIsNotNone(doc.ifc.by_guid(b))
        # the second the other way round
        p = bim.add_wall(doc, np.array((20.0, 0.0, 0.0)), np.array((25.0, 0.0, 0.0)), spec)
        q = bim.add_wall(doc, np.array((30.0, 0.0, 0.0)), np.array((25.0, 0.0, 0.0)), spec)
        bim.merge_walls(doc, p, q)
        s, e, _t = doc.ifc.wall_axis(p)
        self.assertTrue(np.allclose(s, (20.0, 0.0, 0.0)) and np.allclose(e, (30.0, 0.0, 0.0)))
        far = bim.add_wall(doc, np.array((40.0, 0.0, 0.0)), np.array((45.0, 0.0, 0.0)), spec)
        with self.assertRaises(ValueError):
            bim.merge_walls(doc, p, far)                                      # apart
        other = bim.add_wall(doc, np.array((30.0, 0.0, 0.0)), np.array((35.0, 0.0, 0.0)),
                             catalog.BY_KEY["parede_alv_15"])
        with self.assertRaises(ValueError):
            bim.merge_walls(doc, p, other)                                    # another type
        # nearly straight: made straight, the joined wall follows
        w = bim.add_wall(doc, np.array((0.0, 20.0, 0.0)), np.array((10.0, 20.0 + 10 * math.tan(math.radians(2)), 0.0)),
                         spec)
        ws, we, _t = doc.ifc.wall_axis(w)
        x = bim.add_wall(doc, we, we + np.array((0.0, 4.0, 0.0)), spec, prev=(w, (we - ws) / np.linalg.norm(we - ws)))
        self.assertIn(x, doc.ifc.joined_walls([w]))
        door = bim.add_opening(doc, w, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, w), 2.0, 1)
        window = bim.add_opening(doc, w, catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, w), 6.0, 1)
        across = {g: float(np.ptp(doc.get(g).mesh.verts[:, 1])) for g in (door, window)}
        self.assertEqual(bim.orthogonalize(doc, [w, x]), 1)
        s, e, _t = doc.ifc.wall_axis(w)
        self.assertAlmostEqual(s[1], e[1])
        # (0.407) its door and window drawn straight with it (they were left drawn at the old angle)
        for g in (door, window):
            lo, hi = bounds(doc, g)
            self.assertLess(hi[1] - lo[1], across[g] - 0.02)
            self.assertTrue(lo[1] > s[1] - 0.4 and hi[1] < s[1] + 0.4)
        self.assertIn(x, doc.ifc.joined_walls([w]))
        xs, _xe, _t = doc.ifc.wall_axis(x)
        self.assertLess(abs(xs[1] - s[1]), 0.11)                              # it still meets it
        # joints let go
        self.assertEqual(bim.unjoin_walls(doc, [c]), 1)
        self.assertNotIn(c, doc.ifc.joined_walls([b]))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        # (0.325) nothing to do: no undo step with nothing in it (the Ctrl+Z after it undid nothing to see)
        steps = len(doc._undo)
        self.assertEqual(bim.unjoin_walls(doc, [c]), 0)
        self.assertEqual(bim.orthogonalize(doc, [w]), 0)
        self.assertEqual(bim.renumber_openings(Document()), 0)
        self.assertEqual(len(doc._undo), steps)
        self.assertEqual(doc.ifc.off_square([w, far]), [])


class CurvedWalls(unittest.TestCase):
    """0.103: a quarter-circle wall of 5 m radius (true arcs in the IFC: its volume), a round wall (an
    IfcCircleHollowProfileDef) with a room inside it, the radius and sweep changed, another type (its axis stays),
    moved; the IFC valid."""

    def test_curved_walls(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        arc = bim.add_curved_wall(doc, (0.0, 0.0, 0.0), 5.0, 0.0, math.pi / 2, spec, 3.0)
        self.assertEqual(doc.ifc.kind_of(arc), "curved_wall")
        self.assertAlmostEqual(doc.get(arc).mesh.volume(), math.pi / 4 * (5.1 ** 2 - 4.9 ** 2) * 3.0, places=3)
        q = ue.get_psets(doc.ifc.by_guid(arc))["Qto_WallBaseQuantities"]
        self.assertAlmostEqual(q["Length"] * doc.ifc.unit_scale, 5.0 * math.pi / 2)
        lo, hi = bounds(doc, arc)
        self.assertTrue(np.allclose(lo[:2], (0.0, 0.0), atol=1e-6) and np.allclose(hi, (5.1, 5.1, 3.0), atol=1e-3))
        ring = bim.add_curved_wall(doc, (20.0, 0.0, 0.0), 3.0, 0.0, 2 * math.pi, spec, 2.8)
        e = doc.ifc.by_guid(ring)
        profiles = [i.SweptArea.is_a() for r in e.Representation.Representations for i in r.Items
                    if i.is_a("IfcExtrudedAreaSolid")]
        self.assertEqual(profiles, ["IfcCircleHollowProfileDef"])
        room = bim.add_room(doc, (20.0, 0.0))
        self.assertAlmostEqual(doc.ifc.space_info(room)["area"], math.pi * 2.9 ** 2, delta=0.02)
        bim.set_curved_wall(doc, arc, radius=6.0)
        bim.set_curved_wall(doc, arc, sweep=math.pi)
        _c, r, _s, sweep, h, t = doc.ifc.curved_wall_params(arc)
        self.assertEqual((r, round(sweep, 9), h, t), (6.0, round(math.pi, 9), 3.0, 0.2))
        bim.set_type(doc, arc, catalog.BY_KEY["parede_alv_15"])
        self.assertAlmostEqual(doc.ifc.curved_wall_params(arc)[5], 0.15)
        self.assertAlmostEqual(doc.get(arc).mesh.volume(), math.pi / 2 * (6.075 ** 2 - 5.925 ** 2) * 3.0, places=3)
        m = np.eye(4)
        m[:3, 3] = (1.0, 0.0, 0.0)
        bim.transform_objects(doc, [arc], m, "mover")
        self.assertTrue(np.allclose(doc.ifc.curved_wall_params(arc)[0], (1.0, 0.0, 0.0)))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        doc.undo()
        self.assertAlmostEqual(doc.ifc.curved_wall_params(arc)[5], 0.2)


class Ramps(unittest.TestCase):
    """0.101: a straight ramp 6 m long, 1,20 m wide, rising 50 cm — IfcRamp STRAIGHT_RUN_RAMP with its own body
    (its walking surface from 0 to 0,50, the slab's 15 cm under it), its slope in Pset_RampCommon; its length,
    width and rise changed (its foot stays); moved; copied; undo; the IFC valid."""

    def test_ramps(self):
        doc = Document()
        ramp = bim.add_ramp(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["laje_15"],
                            1.20, 0.50)
        e = doc.ifc.by_guid(ramp)
        self.assertEqual((e.is_a(), e.PredefinedType), ("IfcRamp", "STRAIGHT_RUN_RAMP"))
        self.assertEqual(doc.ifc.kind_of(ramp), "ramp")
        lo, hi = bounds(doc, ramp)
        self.assertTrue(np.allclose(lo, (0.0, -0.6, -0.15), atol=1e-6), lo)
        self.assertTrue(np.allclose(hi, (6.0, 0.6, 0.5), atol=1e-6), hi)
        slope = ue.get_psets(e)["Pset_RampCommon"]["RequiredSlope"]
        self.assertAlmostEqual(slope, np.arctan2(0.5, 6.0))
        self.assertEqual(ue.get_material(e).Name, ue.get_material(doc.ifc.by_guid(
            bim.add_slab(doc, np.array((10.0, 0.0, 0.0)), 1.0, 1.0, catalog.BY_KEY["laje_15"])),
            should_skip_usage=True).MaterialLayers[0].Material.Name)
        info = doc.ifc.describe(ramp)
        self.assertAlmostEqual(info["params"]["slope"], 0.5 / 6.0)
        bim.set_ramp(doc, ramp, length=8.0)
        bim.set_ramp(doc, ramp, width=1.5)
        bim.set_ramp(doc, ramp, rise=0.4)
        lo, hi = bounds(doc, ramp)
        self.assertTrue(np.allclose(lo, (0.0, -0.75, -0.15), atol=1e-6), lo)
        self.assertTrue(np.allclose(hi, (8.0, 0.75, 0.4), atol=1e-6), hi)
        m = np.eye(4)
        m[:3, 3] = (1.0, 2.0, 0.0)
        bim.transform_objects(doc, [ramp], m, "mover")
        start, end, width, rise, thickness = doc.ifc.ramp_params(ramp)
        self.assertTrue(np.allclose(start, (1.0, 2.0, 0.0)) and np.allclose(end, (9.0, 2.0, 0.0)))
        self.assertEqual((width, rise, thickness), (1.5, 0.4, 0.15))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()                                                        # (the move)
        doc.undo()                                                        # (the rise)
        self.assertAlmostEqual(doc.ifc.ramp_params(ramp)[3], 0.5)
        with self.assertRaises(ValueError):
            bim.set_ramp(doc, ramp, width=0.05)


class PileCapsAndRaft(unittest.TestCase):
    """0.94: a pile cap of 2 piles under a column — IfcFooting PILE_CAP and two IfcPile under it, tied to it; the
    column moved takes all; the cap deleted takes its piles; a raft is an IfcSlab BASESLAB."""

    def test_pile_cap_and_raft(self):
        doc = Document()
        col = bim.add_column(doc, np.array((2.0, 3.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        cap_spec = catalog.BY_KEY["bloco_2e"]
        cap = bim.add_footing(doc, bim.footing_place(doc, col, cap_spec), cap_spec, under=col)
        kind = lambda g: ue.get_predefined_type(doc.ifc.by_guid(g))          # noqa: E731  (the type's)
        self.assertEqual(kind(cap), "PILE_CAP")
        piles = doc.ifc.footings_of([cap])[cap]
        self.assertEqual(len(piles), 2)
        for p in piles:
            self.assertEqual((doc.ifc.by_guid(p).is_a(), kind(p)), ("IfcPile", "BORED"))
            lo, hi = bounds(doc, p)
            self.assertAlmostEqual(hi[2], -0.6)                       # its head under the cap (60 cm deep)
            self.assertAlmostEqual(lo[2], -8.6)                       # 8 m long
        xs = sorted(round(float(doc.ifc.placement(p)[0, 3]), 6) for p in piles)
        self.assertEqual(xs, [1.55, 2.45])                            # 15 cm + half a diameter in from the cap's ends
        m = np.eye(4)
        m[1, 3] = 1.0
        bim.transform_objects(doc, [col], m, "mover")
        for p in piles:
            self.assertAlmostEqual(float(doc.ifc.placement(p)[1, 3]), 4.0)
        bim.delete(doc, [cap])
        self.assertEqual(len(doc.ifc.file.by_type("IfcPile")), 0)
        raft = bim.add_slab(doc, np.array((0.0, 0.0, 0.0)), 8.0, 6.0, catalog.BY_KEY["radier_30"])
        self.assertEqual(kind(raft), "BASESLAB")
        self.assertEqual([t.PredefinedType for t in doc.ifc.file.by_type("IfcSlabType")], ["BASESLAB"])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class TypicalFloors(unittest.TestCase):
    """0.90: three storeys made equal from the first one's walls; a wall drawn on the third, joined to one of
    them, appears on all (joined there too); a wall made longer on one is longer on all; deleted on one, gone from
    all; a door in one, in all; undo; the storeys no longer equal: each keeps its own."""

    def test_typical_floors(self):
        doc = Document()
        ground = doc.ifc.storeys()[0][0]
        first = bim.add_storey(doc, "Piso 1", 3.0)
        second = bim.add_storey(doc, "Piso 2", 6.0)
        spec = catalog.BY_KEY["parede_alv_20"]
        a = bim.add_wall(doc, np.array((0.0, 0.0, 3.0)), np.array((5.0, 0.0, 3.0)), spec, storey=first)
        self.assertIsNotNone(bim.make_typical(doc, [first, second, ground], first, "Apartamento"))
        walls = lambda s: sorted(e.GlobalId for e in doc.ifc.file.by_type("IfcWall") if doc.ifc.storey_of(e.GlobalId) == s)
        self.assertEqual([len(walls(s)) for s in (ground, first, second)], [1, 1, 1])
        z = {s: bounds(doc, walls(s)[0])[0][2] for s in (ground, first, second)}
        self.assertEqual([round(z[s], 6) for s in (ground, first, second)], [0.0, 3.0, 6.0])
        # a wall drawn on Piso 2, from the end of the floor's wall: on every storey, joined
        b0 = walls(second)[0]
        b = bim.add_wall(doc, np.array((5.0, 0.0, 6.0)), np.array((5.0, 4.0, 6.0)), spec,
                         start_join=(b0, "end", np.array((1.0, 0.0, 0.0))), storey=second)
        self.assertEqual([len(walls(s)) for s in (ground, first, second)], [2, 2, 2])
        for s in (ground, first):
            new = [w for w in walls(s) if abs(doc.ifc.wall_params(w)[0] - 3.9) < 1e-6]   # (it butts on the other)
            self.assertEqual(len(new), 1)
            self.assertTrue(doc.ifc.wall_joints(new[0]))                            # joined there too
            self.assertTrue(any(abs(doc.ifc.wall_params(w)[0] - 5.1) < 1e-6 for w in walls(s)))   # (the corner)
        self.assertEqual(len(doc.ifc.counterparts(b)), 2)
        bim.resize_wall(doc, b, at_end=1.0)                                       # 1 m longer on all three
        self.assertTrue(all(any(abs(doc.ifc.wall_params(w)[0] - 4.9) < 1e-6 for w in walls(s))
                            for s in (ground, first, second)))
        frame = bim.wall_frame(doc, a)
        bim.add_opening(doc, a, catalog.OPENING_BY_KEY["porta_80"], frame, 1.0, 1)
        self.assertEqual(len(doc.ifc.file.by_type("IfcDoor")), 3)
        bim.delete(doc, [b])
        self.assertEqual([len(walls(s)) for s in (ground, first, second)], [1, 1, 1])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        for _ in range(4):
            doc.undo()                                                       # delete, door, resize, wall
        self.assertEqual([len(walls(s)) for s in (ground, first, second)], [1, 1, 1])
        self.assertTrue(bim.unmake_typical(doc, first))
        self.assertEqual(doc.ifc.typical_sets(), {})
        bim.add_wall(doc, np.array((0.0, 2.0, 3.0)), np.array((4.0, 2.0, 3.0)), spec, storey=first)
        self.assertEqual([len(walls(s)) for s in (ground, first, second)], [1, 2, 1])     # on its own now

    def test_typical_documentation(self):
        """0.463 — the owner: «tudo que se faz num nível igualado é replicado nos outros níveis, seja modelação,
        modificação, documentação»: a dimension and a text drawn in the plan of one of two equal storeys are in the
        other's plan (the same ones: moved in one, moved in both); a section's are its own; the storeys separated —
        each keeps them, the dimension hung on its own wall."""
        from arqbim.model import annotations as notes2d
        from arqbim.model import dimensions as dims_model
        doc = Document()
        try:
            first = bim.add_storey(doc, "Piso 1", 3.0)
            second = bim.add_storey(doc, "Piso 2", 6.0)
            spec = catalog.BY_KEY["parede_alv_20"]
            wall = bim.add_wall(doc, np.array((0.0, 0.0, 3.0)), np.array((5.0, 0.0, 3.0)), spec, storey=first)
            bim.make_typical(doc, [first, second], first, "Piso tipo")
            self.assertEqual(doc.twin_views(("plan", first)), {("plan", first), ("plan", second)})
            self.assertEqual(doc.twin_views(("section", "Corte 1")), {("section", "Corte 1")})
            text = notes2d.Annotation(("plan", first), "text", [np.array((1.0, 1.0, 3.0))], text="Sala")
            doc.execute(notes2d.AddAnnotation(text, "t"))
            dim = dims_model.Dimension(("plan", first), np.array((0.0, -0.1, 3.0)), np.array((5.0, -0.1, 3.0)),
                                       np.array((2.5, -1.0, 3.0)),
                                       refs=[(wall, np.array((0.0, -0.1, 0.0)), None), None])
            doc.execute(dims_model.AddDimension(dim, "d"))
            self.assertEqual(doc.annotations_of(("plan", second)), [text])          # (in the other's plan too)
            self.assertEqual(doc.dimensions_of(("plan", second)), [dim])
            self.assertTrue(bim.unmake_typical(doc, first))
            mine = doc.annotations_of(("plan", second))
            self.assertEqual(len(mine), 1)                                         # (a copy of its own)
            self.assertIsNot(mine[0], text)
            self.assertAlmostEqual(float(mine[0].points[0][2]), 6.0, places=9)
            self.assertEqual(doc.annotations_of(("plan", first)), [text])
            copy_dim = doc.dimensions_of(("plan", second))
            self.assertEqual(len(copy_dim), 1)
            twin_wall = copy_dim[0].refs[0][0]
            self.assertNotEqual(twin_wall, wall)                                    # (hung on its own storey's wall)
            self.assertEqual(doc.ifc.storey_of(twin_wall), second)
            doc.undo()                                                              # (one step: shared again)
            self.assertEqual(doc.annotations_of(("plan", second)), [text])
            self.assertEqual(len(doc.dimensions), 1)
            # (0.465, the owner: «O botão = deve ligável e desligavel. Só faz o efeito quando o botão está ligado»)
            doc.typical_live = False
            self.assertEqual(doc.annotations_of(("plan", second)), [])              # (off: each its own)
            self.assertEqual(doc.ifc.counterparts(wall), [])
            walls = lambda s: [e.GlobalId for e in doc.ifc.file.by_type("IfcWall") if doc.ifc.storey_of(e.GlobalId) == s]  # noqa
            bim.add_wall(doc, np.array((0.0, 3.0, 6.0)), np.array((4.0, 3.0, 6.0)), spec, storey=second)
            self.assertEqual((len(walls(first)), len(walls(second))), (1, 2))       # (made on Piso 2 only)
            bim.resize_wall(doc, wall, at_end=1.0)                                  # (Piso 1's longer, not Piso 2's)
            lengths = sorted(round(doc.ifc.wall_params(w)[0], 6) for w in walls(first) + walls(second))
            self.assertIn(6.0, lengths)
            self.assertIn(5.0, lengths)
            note = notes2d.Annotation(("plan", second), "text", [np.array((2.0, 2.0, 6.0))], text="Só aqui")
            doc.execute(notes2d.AddAnnotation(note, "t"))
            self.assertTrue(note.extra.get("alone"))
            doc.typical_live = True                                                 # (on again: equal again…)
            self.assertEqual(doc.annotations_of(("plan", first)), [text])           # (…but «Só aqui» stays its own)
            self.assertEqual(set(map(id, doc.annotations_of(("plan", second)))), {id(text), id(note)})
            self.assertEqual(len(doc.ifc.counterparts(wall)), 1)
        finally:
            doc.modified = False


class GridEditing(unittest.TestCase):
    """0.72 (the owner: "edit, select, align" and a generator): axes moved, aligned ends, neighbours, deleted,
    a grid generated."""

    def test_generator_and_spacings(self):
        self.assertEqual(bim.spacings_to_positions(4, "5"), [0.0, 5.0, 10.0, 15.0])
        self.assertEqual(bim.spacings_to_positions(4, "5;6,5"), [0.0, 5.0, 11.5, 18.0])     # the last one repeats
        self.assertIsNone(bim.spacings_to_positions(3, "cinco"))
        self.assertEqual(bim.spacings_to_positions(0, "5"), [])
        doc = Document()
        tags = bim.generate_grid(doc, [0.0, 5.0, 10.0], [0.0, 6.0], origin=(1.0, 2.0), extension=1.5)
        self.assertEqual(tags, ["1", "2", "3", "A", "B"])
        self.assertEqual(doc.grids[0].start, (1.0, 0.5))                  # 1,50 below A
        self.assertEqual(doc.grids[0].end, (1.0, 9.5))                    # and above B
        self.assertEqual(doc.grids[4].start, (-0.5, 8.0))
        self.assertEqual(doc.ifc.count("IfcGrid"), 1)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        more = bim.generate_grid(doc, [15.0], [], origin=(1.0, 2.0))      # added: the tags go on
        self.assertEqual(more, ["4"])
        bim.generate_grid(doc, [0.0, 4.0], [0.0], replace=True)
        self.assertEqual([a.tag for a in doc.grids], ["1", "2", "A"])
        doc.undo()
        self.assertEqual(len(doc.grids), 6)

    def test_move_align_and_delete(self):
        doc = Document()
        bim.generate_grid(doc, [0.0, 5.0, 10.0], [0.0, 6.0], extension=1.0)
        self.assertEqual(bim.aligned_ends(doc.grids, 0, "end"), [(1, "end"), (2, "end")])     # the bubbles up top
        self.assertEqual(sorted(bim.grid_neighbours(doc.grids, 1)), [(0, 5.0), (2, -5.0)])
        bim.move_grid_axes(doc, {1: ((6.0, -1.0), (6.0, 7.0))})                               # 1 m to the right
        self.assertEqual(doc.grids[1].start, (6.0, -1.0))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        with self.assertRaises(ValueError):
            bim.move_grid_axes(doc, {1: ((6.0, 0.0), (6.0, 0.01))})                          # too short
        bim.remove_grid_axes(doc, [0, 3])                                                     # 1 and A
        self.assertEqual([a.tag for a in doc.grids], ["2", "3", "B"])
        doc.undo()
        doc.undo()
        self.assertEqual(doc.grids[1].start, (5.0, -1.0))


class StructuralGrid(unittest.TestCase):
    """0.67 (Phase 5, step 2): the structural grid's axes — tags, the IfcGrid (only when valid), kept, undone."""

    def test_axes_and_the_ifc_grid(self):
        doc = Document()
        self.assertEqual(bim.add_grid_axis(doc, (0, -1), (0, 10)), "1")              # along Y: numbered
        self.assertEqual(doc.ifc.count("IfcGrid"), 0)               # one way only: kept out of the IFC (valid)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        self.assertEqual(bim.add_grid_axis(doc, (5, -1), (5, 10)), "2")
        self.assertEqual(bim.add_grid_axis(doc, (-1, 0), (6, 0)), "A")               # along X: lettered
        grids = doc.ifc.file.by_type("IfcGrid")
        self.assertEqual(len(grids), 1)
        self.assertEqual((sorted(a.AxisTag for a in grids[0].UAxes), [a.AxisTag for a in grids[0].VAxes]),
                         (["1", "2"], ["A"]))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        guid = grids[0].GlobalId
        self.assertTrue(bim.rename_grid_axis(doc, 2, "B"))
        self.assertFalse(bim.rename_grid_axis(doc, 2, "1"))                          # another axis has it
        self.assertEqual(doc.ifc.file.by_type("IfcGrid")[0].GlobalId, guid)          # the same grid
        read = sorted(doc.ifc.read_grids())
        self.assertEqual([r[0] for r in read], ["1", "2", "B"])
        np.testing.assert_allclose(read[1][1:], [(5, -1), (5, 10)], atol=1e-9)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "eixos.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        self.assertEqual([a.tag for a in again.grids], ["1", "2", "B"])
        self.assertEqual(again.grids[2].end, (6.0, 0.0))
        from arqbim.model import drawings
        plan = drawings.plan(doc, doc.active_storey, "P")
        self.assertEqual([g[2] for g in plan.grids], ["1", "2", "B"])               # on the plan's paper
        doc.set_view_props(("plan", doc.active_storey), crop=[1.0, -2.0, 7.0, 11.0])
        self.assertEqual([g[2] for g in drawings.plan(doc, doc.active_storey, "P").grids], ["2", "B"])
        doc.undo()
        bim.remove_grid_axis(doc, 0)
        self.assertEqual([a.tag for a in doc.grids], ["2", "B"])
        for _ in range(5):                                       # remove, rename, A, 2, 1 (the crop: undone above)
            doc.undo()
        self.assertEqual((doc.grids, doc.ifc.count("IfcGrid")), ([], 0))
        self.assertEqual(bim.next_grid_tag([], False), "A")
        from arqbim.model.document import GridAxis
        self.assertEqual(bim.next_grid_tag([GridAxis(chr(65 + k), (0, 0), (1, 0)) for k in range(26)], False), "AA")


class Voids(unittest.TestCase):
    """Holes and niches made with Push/Pull, in sketches and in IFC walls/slabs."""

    def sketch_with_hole(self, doc, origin, du, dv, height, face_normal, rect, depth):
        obj = box_object(doc, origin, du, dv, height)
        mesh = obj.mesh.copy()
        front = next(fi for fi in range(len(mesh.faces)) if np.allclose(mesh.face_normal(fi), face_normal))
        fi = sg.imprint_polygon(mesh, front, [np.array(p) - np.array(origin) for p in rect])
        r = sg.push_pull(mesh, fi, obj.matrix, -depth)
        self.assertEqual(r.mode, "hole")
        doc.execute(ReplaceMesh(obj.id, obj.mesh, mesh))
        return obj

    def test_classify_wall_with_a_hole(self):
        doc = Document()
        obj = self.sketch_with_hole(doc, (0, 0, 0), 4.5, 0.2, 2.8, (0, -1, 0),
                                    [(1, 0, 0.5), (2, 0, 0.5), (2, 0, 1.5), (1, 0, 1.5)], 0.2)
        res = bim.classify(doc, [obj.id], catalog.BY_KEY["parede_alv_20"])
        self.assertEqual(len(res.guids), 1)
        self.assertEqual(doc.ifc.count("IfcOpeningElement"), 1)
        self.assertAlmostEqual(doc.get(res.guids[0]).mesh.volume(), 4.5 * 0.2 * 2.8 - 0.2, places=6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_classify_slab_with_a_hole(self):
        doc = Document()
        obj = self.sketch_with_hole(doc, (0, 0, 2.88), 4, 3, 0.12, (0, 0, 1),
                                    [(1, 1, 3.0), (2, 1, 3.0), (2, 2, 3.0), (1, 2, 3.0)], 0.12)
        res = bim.classify(doc, [obj.id], catalog.BY_KEY["laje_12"])
        self.assertEqual(doc.ifc.count("IfcOpeningElement"), 1)
        self.assertAlmostEqual(doc.get(res.guids[0]).mesh.volume(), 4 * 3 * 0.12 - 0.12, places=6)
        # a column cannot take a hole
        obj2 = self.sketch_with_hole(doc, (10, 0, 0), 2.0, 0.6, 2.8, (0, -1, 0),
                                     [(10.5, 0, 1), (11.5, 0, 1), (11.5, 0, 2), (10.5, 0, 2)], 0.6)
        self.assertEqual(len(bim.classify(doc, [obj2.id], catalog.BY_KEY["pilar_30"]).refused), 1)

    def test_rectangle_pushed_into_an_ifc_wall(self):
        doc = Document()
        wall = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        vol = doc.get(wall).mesh.volume()

        def sheet():                                            # rectangle drawn on the wall's front face (y = -0.1)
            m = sg.rectangle_matrix(np.array((1.0, -0.1, 0.5)), np.array((1.0, 0, 0)), np.array((0, 0, 1.0)))
            s = SketchObject("s", m, sg.rectangle_mesh(1.2, 1.0))
            doc.execute(AddObject(s))
            return s

        s = sheet()
        host = bim.sheet_host(doc, s)
        self.assertEqual((host.guid, host.axis, host.side), (wall, 1, -1))
        self.assertAlmostEqual(host.thickness, 0.2)
        guid, through = bim.push_void(doc, s, host, 0.2)
        self.assertTrue(through)
        self.assertIsNone(doc.get(s.id))                        # the rectangle became the opening
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), vol - 1.2 * 1.0 * 0.2, places=6)
        doc.undo()
        self.assertIsNotNone(doc.get(s.id))
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), vol, places=6)

        guid, through = bim.push_void(doc, s, bim.sheet_host(doc, s), 0.05)   # niche
        self.assertFalse(through)
        self.assertEqual(doc.ifc.by_guid(guid).PredefinedType, "RECESS")
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), vol - 1.2 * 1.0 * 0.05, places=6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_a_side_of_an_opening_moves_and_the_base_goes_down(self):
        doc = Document()
        wall = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        vol, (lo0, hi0) = doc.get(wall).mesh.volume(), bounds(doc, wall)
        m = sg.rectangle_matrix(np.array((1.0, -0.1, 0.5)), np.array((1.0, 0, 0)), np.array((0, 0, 1.0)))
        s = SketchObject("s", m, sg.rectangle_mesh(1.2, 1.0))
        doc.execute(AddObject(s))
        opening, _through = bim.push_void(doc, s, bim.sheet_host(doc, s), 0.2)       # 1,2 × 1,0 m right through
        [(gid, lo, hi, filled, box)] = doc.ifc.voids(wall)
        self.assertEqual((gid, filled, box), (opening, False, True))
        self.assertTrue(np.allclose((lo[0], hi[0], lo[2], hi[2]), (1.0, 2.2, 0.5, 1.5)), (lo, hi))
        hi2 = hi.copy()
        hi2[0] += 0.5                                                 # its right side 50 cm further
        bim.resize_void(doc, wall, opening, lo, hi2)
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), vol - 1.7 * 1.0 * 0.2, places=6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), vol - 1.2 * 1.0 * 0.2, places=6)
        door = bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, wall), 3.0, -1)
        door_lo = bounds(doc, door)[0]
        bim.resize_wall(doc, wall, at_base=0.3)                       # the base 30 cm down, the top where it was
        lo1, hi1 = bounds(doc, wall)
        self.assertAlmostEqual(lo1[2], lo0[2] - 0.3)
        self.assertAlmostEqual(hi1[2], hi0[2])
        self.assertTrue(np.allclose(bounds(doc, door)[0], door_lo))      # the door and the opening stay put
        self.assertTrue(np.allclose(doc.ifc.voids(wall)[0][1], lo + (0, 0, 0.3)) or
                        np.allclose(doc.ifc.voids(wall)[1][1], lo + (0, 0, 0.3)))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        with self.assertRaises(ValueError):                           # up past the opening's sill: refused
            bim.resize_wall(doc, wall, at_base=-0.9)

    def test_line_across_a_wall_face_gives_two_rectangles(self):
        from arqbim.model import imprint
        doc = Document()
        wall = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        vol, top = doc.get(wall).mesh.volume(), float(bounds(doc, wall)[1][2])
        self.assertIsNotNone(imprint.split_by_path(doc, [(0, -0.1, 0.5), (5, -0.1, 1.0)]))   # slanted: two trapeziums
        self.assertIsNone(imprint.split_by_path(doc, [(1, -0.1, 1.0), (5, -0.1, 1.0)]))      # not across
        self.assertEqual(imprint.host_face(doc, (1, -0.1, 1.0), (5, -0.1, 1.0)), doc.get(wall).name)  # (to say why)
        split = imprint.split_by_path(doc, [(0, -0.1, 1.0), (5, -0.1, 1.15)])   # by hand, 2° off level: at its start
        self.assertEqual(split.host, doc.get(wall).name)
        doc.execute(split.command)
        sheets_ = [o for o in doc.sketches()]
        hosts = [bim.sheet_host(doc, s) for s in sheets_]
        self.assertEqual([(h.guid, h.axis, h.side) for h in hosts], [(wall, 1, -1)] * 2)
        self.assertEqual(sorted(round(s.mesh.face_area(0), 6) for s in sheets_), sorted([5.0, round(5 * (top - 1), 6)]))
        low = next(s for s, h in zip(sheets_, hosts) if h.local[:, 2].max() < 1.0 + 1e-6)
        bim.push_void(doc, low, bim.sheet_host(doc, low), 0.05)                          # a 5 cm recess below
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), vol - 5 * 1.0 * 0.05, places=6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        split = imprint.split_by_path(doc, [(2, -0.1, top), (2, -0.1, 1.0)])               # upright, on the top part
        doc.execute(split.command)                                                     # (the rectangle is divided)
        self.assertEqual(sorted(round(s.mesh.face_area(0), 6) for s in doc.sketches()),
                         sorted([round(2 * (top - 1), 6), round(3 * (top - 1), 6)]))
        self.assertTrue(all(bim.sheet_host(doc, s) is not None for s in doc.sketches()))

    def test_slanted_line_across_a_wall_and_a_niche_of_that_shape(self):
        from arqbim.model import imprint
        doc = Document()
        wall = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, wall), 4.0, -1)
        vol, top = doc.get(wall).mesh.volume(), float(bounds(doc, wall)[1][2])
        split = imprint.split_by_path(doc, [(0, -0.1, 0.0), (3.4, -0.1, top)])     # corner to the top edge
        self.assertIsNotNone(split)
        doc.execute(split.command)
        parts = doc.sketches()
        triangle = next(s for s in parts if len(s.mesh.faces[0]) == 3)
        self.assertAlmostEqual(triangle.mesh.face_area(0), 3.4 * top / 2, places=6)
        self.assertAlmostEqual(sum(s.mesh.face_area(0) for s in parts), 5 * top, places=6)
        host = bim.sheet_host(doc, triangle)
        self.assertEqual((host.guid, host.box), (wall, False))
        bim.push_void(doc, triangle, host, 0.05)                      # a 5 cm niche of that triangle
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), vol - 3.4 * top / 2 * 0.05, places=5)
        drawn = [v for v in doc.ifc.voids(wall) if not v[3]]
        self.assertEqual([v[4] for v in drawn], [False])              # not a box: its sides do not move one by one
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        bim.push_void(doc, triangle, bim.sheet_host(doc, triangle), 0.2)    # right through
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), vol - 3.4 * top / 2 * 0.2, places=5)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_line_across_a_sketch_box_and_a_flat_sketch(self):
        from arqbim.core.mesh import PolyMesh
        from arqbim.model import imprint
        doc = Document()
        box = box_object(doc, (0, 0, 0), 2.0, 1.0, 1.0)
        lines = SketchObject("l", I4, PolyMesh([(1, 0, 1), (1, 0.5, 1)], lines=[(0, 1)]))   # drawn so far
        doc.execute(AddObject(lines))
        split = imprint.split_by_path(doc, [(1, 0, 1), (1, 0.5, 1), (2, 0.5, 1)], lines)     # an L through the top
        self.assertEqual((split.start, split.faces), (0, 1))
        doc.execute(split.command)
        self.assertIsNone(doc.get(lines.id))                    # its lines are edges of the box now
        self.assertEqual(len(doc.get(box.id).mesh.faces), 7)
        self.assertTrue(doc.get(box.id).mesh.is_closed())
        doc.undo()
        self.assertEqual((len(doc.get(box.id).mesh.faces), doc.get(lines.id) is not None), (6, True))
        floor = SketchObject("chão", translation((10, 0, 0)), sg.rectangle_mesh(4.0, 2.0))
        doc.execute(AddObject(floor))
        doc.execute(imprint.split_by_path(doc, [(11, 0, 0), (11, 2, 0)]).command)
        parts = [o for o in doc.sketches() if o.matrix[0, 3] == 10]
        self.assertEqual(sorted(round(o.mesh.face_area(0), 6) for o in parts), [2.0, 6.0])   # two sketches
        doc.undo()
        self.assertEqual(len([o for o in doc.sketches() if o.matrix[0, 3] == 10]), 1)

    def test_hole_survives_save_and_reopen(self):
        doc = Document()
        obj = self.sketch_with_hole(doc, (0, 0, 0), 4.5, 0.2, 2.8, (0, -1, 0),
                                    [(1, 0, 0.5), (2, 0, 0.5), (2, 0, 1.5), (1, 0, 1.5)], 0.2)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.ifc")
            doc.save(path)
            doc2 = Document()
            doc2.open(path)
            sketch = doc2.sketches()[0]
            self.assertEqual(len(sketch.mesh.voids), 1)
            res = bim.classify(doc2, [sketch.id], catalog.BY_KEY["parede_alv_20"])
            self.assertEqual((len(res.guids), doc2.ifc.count("IfcOpeningElement")), (1, 1))


class EditIfc(unittest.TestCase):
    """Editing elements that are already IFC: sizes, type, doors/windows, name, properties."""

    def setUp(self):
        self.doc = doc = Document()
        self.wall = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        f = bim.wall_frame(doc, self.wall)
        self.door = bim.add_opening(doc, self.wall, catalog.OPENING_BY_KEY["porta_80"], f, 0.5, -1)
        self.win = bim.add_opening(doc, self.wall, catalog.OPENING_BY_KEY["janela_120"], f, 2.5, -1)
        m = sg.rectangle_matrix(np.array((4.0, -0.1, 0.5)), np.array((1.0, 0, 0)), np.array((0, 0, 1.0)))
        sheet = SketchObject("s", m, sg.rectangle_mesh(0.6, 0.6))
        doc.execute(AddObject(sheet))
        bim.push_void(doc, sheet, bim.sheet_host(doc, sheet), 0.05)          # a 5 cm niche

    def wall_volume(self):
        return self.doc.get(self.wall).mesh.volume()

    def expected(self, length=5.0, height=2.8, t=0.2, door_w=0.8, niche=0.05):
        return length * height * t - door_w * 2.1 * t - 1.2 * 1.2 * t - 0.6 * 0.6 * min(niche, t)

    def test_markers(self):
        ifc = self.doc.ifc
        self.assertEqual([ifc.kind_of(g) for g in (self.wall, self.door, self.win)], ["wall", "door", "window"])
        self.assertAlmostEqual(self.wall_volume(), self.expected(), places=6)

    def test_wall_length_and_height(self):
        door_before = self.doc.get(self.door).mesh.verts.min(axis=0).copy()
        bim.resize_wall(self.doc, self.wall, at_end=1.0)
        bim.resize_wall(self.doc, self.wall, at_start=0.5, height=3.2)
        self.assertEqual([round(v, 6) for v in self.doc.ifc.wall_params(self.wall)], [6.5, 3.2, 0.2])
        self.assertTrue(np.allclose(self.doc.get(self.door).mesh.verts.min(axis=0), door_before))
        self.assertAlmostEqual(self.wall_volume(), self.expected(6.5, 3.2), places=6)
        with self.assertRaises(ValueError):                                 # lower than the door
            bim.resize_wall(self.doc, self.wall, height=2.0)
        with self.assertRaises(ValueError):                                 # cuts the window off
            bim.resize_wall(self.doc, self.wall, at_end=-2.5)
        self.assertEqual([round(v, 6) for v in self.doc.ifc.wall_params(self.wall)], [6.5, 3.2, 0.2])
        self.assertEqual(self.doc.ifc.validate(express_rules=True), [])

    def test_wall_type_rebuilds_doors_windows_and_niches(self):
        bim.set_type(self.doc, self.wall, catalog.BY_KEY["parede_alv_15"])
        self.assertAlmostEqual(self.doc.ifc.wall_params(self.wall)[2], 0.15)
        self.assertAlmostEqual(self.wall_volume(), self.expected(t=0.15), places=6)
        y = self.doc.get(self.door).mesh.verts[:, 1]
        self.assertTrue(-0.075 - 0.06 < y.min() and y.max() < 0.075 + 0.06, (y.min(), y.max()))   # lining = 15 cm
        self.assertTrue(np.any(np.abs(np.abs(y) - 0.075) < 1e-6))         # (and its handles, 0.290: 5,8 cm out)
        self.assertEqual(ue.get_type(self.doc.ifc.by_guid(self.wall)).Name, "Parede alvenaria 15 cm")
        self.assertEqual(self.doc.ifc.validate(express_rules=True), [])
        self.doc.undo()
        self.assertAlmostEqual(self.wall_volume(), self.expected(), places=6)

    def test_move_and_retype_door_and_window(self):
        bim.move_filling(self.doc, self.door, s=1.0)
        lo = self.doc.get(self.door).mesh.verts.min(axis=0)
        self.assertAlmostEqual(lo[0], 1.0 - 0.05, places=3)                 # (0.288) its casings: 5 cm
        bim.move_filling(self.doc, self.win, sill=0.9)
        self.assertAlmostEqual(self.doc.get(self.win).mesh.verts[:, 2].min(), 0.9, places=3)
        with self.assertRaises(ValueError):
            bim.move_filling(self.doc, self.win, s=4.5)                     # would leave the wall
        bim.set_type(self.doc, self.door, catalog.OPENING_BY_KEY["porta_90"])
        self.assertAlmostEqual(self.wall_volume(), self.expected(door_w=0.9), places=6)
        self.assertEqual(self.doc.ifc.describe(self.door)["size"], (0.9, 2.1))
        p = self.doc.ifc.describe(self.door)["params"]
        self.assertAlmostEqual(p["from_start"], 1.0)
        self.assertAlmostEqual(p["to_end"], 5.0 - 1.0 - 0.9)
        self.assertEqual(self.doc.ifc.validate(express_rules=True), [])

    def test_slab_size_and_type(self):
        doc = self.doc
        slab = bim.add_slab(doc, np.array((0.0, 0.0, 2.8)), 4.0, 3.0, catalog.BY_KEY["laje_12"])
        m = sg.rectangle_matrix(np.array((1.0, 1.0, 2.92)), np.array((1.0, 0, 0)), np.array((0, 1.0, 0)))
        sheet = SketchObject("h", m, sg.rectangle_mesh(1.0, 1.0))
        doc.execute(AddObject(sheet))
        bim.push_void(doc, sheet, bim.sheet_host(doc, sheet), 1.0)          # hole through the slab
        bim.resize_slab(doc, slab, 0.0, 0.0, 5.0, 3.0)
        bim.set_type(doc, slab, catalog.BY_KEY["laje_15"])
        lo, hi = bounds(doc, slab)
        self.assertTrue(np.allclose(lo, (0, 0, 2.77)) and np.allclose(hi, (5, 3, 2.92)), (lo, hi))   # top kept
        self.assertAlmostEqual(doc.get(slab).mesh.volume(), 5 * 3 * 0.15 - 1.0 * 0.15, places=6)
        with self.assertRaises(ValueError):
            bim.resize_slab(doc, slab, 0.0, 0.0, 1.5, 3.0)                  # would cut the hole
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_column(self):
        doc = self.doc
        obj = box_object(doc, (8, 0, 0), 0.3, 0.3, 2.8)
        col = bim.classify(doc, [obj.id], catalog.BY_KEY["pilar_30"]).guids[0]
        bim.resize_column(doc, col, 3.0)
        bim.set_type(doc, col, catalog.BY_KEY["pilar_20"])
        self.assertAlmostEqual(doc.get(col).mesh.volume(), 0.2 * 0.2 * 3.0, places=6)

    def test_name_and_property(self):
        bim.rename(self.doc, self.wall, "Parede da sala")
        # (0.267: a wall alone is outside, worked out — said inside by hand here)
        bim.set_property(self.doc, self.wall, "Pset_WallCommon", "IsExternal", False)
        e = self.doc.ifc.by_guid(self.wall)
        self.assertEqual(e.Name, "Parede da sala")
        self.assertIs(ue.get_psets(e)["Pset_WallCommon"]["IsExternal"], False)
        self.assertEqual(self.doc.get(self.wall).name, "Parede da sala")
        self.doc.undo()
        self.assertIs(ue.get_psets(self.doc.ifc.by_guid(self.wall))["Pset_WallCommon"]["IsExternal"], True)


class Storeys(unittest.TestCase):
    """Pavimentos: elements drawn on a storey go in it and move with it."""

    def setUp(self):
        self.doc = Document()
        self.ground = self.doc.active_storey
        self.first = bim.add_storey(self.doc, "Piso 1", 3.0)
        self.doc.set_active_storey(self.first)

    def test_storeys_listed_and_valid(self):
        levels = self.doc.storeys()
        self.assertEqual([(n, z) for _g, n, z in levels], [("Térreo", 0.0), ("Piso 1", 3.0)])
        self.assertEqual(self.doc.work_level(), 3.0)
        self.assertAlmostEqual(self.doc.ifc.by_guid(self.first).Elevation, 3000.0)   # millimetres
        self.assertEqual(self.doc.ifc.validate(express_rules=True), [])
        self.doc.undo()                                       # the storey goes; drawing goes back to the ground
        self.assertEqual(len(self.doc.storeys()), 1)
        self.assertEqual(self.doc.active_storey, self.ground)

    def test_wall_and_door_on_a_storey_move_with_it(self):
        doc = self.doc
        wall = bim.add_wall(doc, (0, 0, 3.0), (5, 0, 3.0), catalog.BY_KEY["parede_alv_20"], storey=self.first)
        door = bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, wall), 2.0, -1)
        self.assertEqual((doc.get(wall).storey, doc.get(door).storey), (self.first, self.first))
        self.assertAlmostEqual(bounds(doc, wall)[0][2], 3.0)
        vol = doc.get(wall).mesh.volume()
        self.assertAlmostEqual(vol, 5 * 2.8 * 0.2 - 0.8 * 2.1 * 0.2, places=6)
        bim.set_storey_elevation(doc, self.first, 3.5)
        self.assertAlmostEqual(bounds(doc, wall)[0][2], 3.5)
        self.assertAlmostEqual(bounds(doc, door)[0][2], 3.5)
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), vol, places=6)   # the door's opening went along
        self.assertAlmostEqual(doc.ifc.wall_axis(wall)[0][2], 3.5)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertAlmostEqual(bounds(doc, wall)[0][2], 3.0)

    def test_floor_slab_and_classify_go_in_the_right_storey(self):
        doc = self.doc
        slab = bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 5.0, 4.0, catalog.BY_KEY["laje_12"], storey=self.first)
        lo, hi = bounds(doc, slab)
        self.assertAlmostEqual(hi[2], 3.0)                    # floor slab: top at the storey level
        self.assertEqual(doc.get(slab).storey, self.first)
        low = box_object(doc, (0, 5, 0), 3.0, 0.2, 2.8)        # a sketch on the ground
        high = box_object(doc, (0, 7, 3.0), 3.0, 0.2, 2.8)     # a sketch on Piso 1
        guids = bim.classify(doc, [low.id, high.id], catalog.BY_KEY["parede_alv_20"]).guids
        self.assertEqual([doc.get(g).storey for g in guids], [self.ground, self.first])

    def test_delete_storey_only_when_empty(self):
        doc = self.doc
        bim.add_wall(doc, (0, 0, 3.0), (5, 0, 3.0), catalog.BY_KEY["parede_alv_20"], storey=self.first)
        with self.assertRaises(ValueError):
            bim.remove_storey(doc, self.first)
        empty = bim.add_storey(doc, "Piso 2", 6.0)
        bim.remove_storey(doc, empty)
        self.assertEqual(len(doc.storeys()), 2)
        with self.assertRaises(ValueError):
            bim.remove_storey(Document(), Document().active_storey)   # the only storey stays

    def test_storeys_saved_and_reopened(self):
        doc = self.doc
        bim.add_wall(doc, (0, 0, 3.0), (5, 0, 3.0), catalog.BY_KEY["parede_alv_20"], storey=self.first)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "pisos.ifc")
            doc.save(path)
            f = ifcopenshell.open(path)
            names = sorted((s.Name, round(s.Elevation)) for s in f.by_type("IfcBuildingStorey"))
            wall = f.by_type("IfcWall")[0]
            self.assertEqual(names, [("Piso 1", 3000), ("Térreo", 0)])
            self.assertEqual(ue.get_container(wall).Name, "Piso 1")
            doc2 = Document()
            doc2.open(path)
            self.assertEqual([n for _g, n, _z in doc2.storeys()], ["Térreo", "Piso 1"])

    def test_spatial_tree_and_storeys_of_many(self):
        doc = self.doc
        bim.add_storey(doc, "Piso 2", 6.0)
        tree = doc.ifc.spatial_tree()
        self.assertEqual((tree[1], tree[2]), ("IfcProject", "Projeto"))
        site = tree[4][0]
        building = site[4][0]
        self.assertEqual((site[1], building[1]), ("IfcSite", "IfcBuilding"))
        self.assertEqual([(n[2], n[3]) for n in building[4]], [("Piso 2", 6.0), ("Piso 1", 3.0), ("Térreo", 0.0)])
        wall = bim.add_wall(doc, (0, 0, 3.0), (5, 0, 3.0), catalog.BY_KEY["parede_alv_20"], storey=self.first)
        door = bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, wall), 2.0, -1)
        low = bim.add_wall(doc, (0, 5, 0), (5, 5, 0), catalog.BY_KEY["parede_alv_20"], storey=self.ground)
        elements = [doc.ifc.by_guid(g) for g in (wall, door, low)]
        self.assertEqual(doc.ifc.storeys_of(elements), {g: doc.ifc.storey_of(g) for g in (wall, door, low)})
        self.assertEqual(doc.ifc.storeys_of(elements)[low], self.ground)


class MoveRotateIfc(unittest.TestCase):
    """Mover / Rodar IFC elements: the placement moves, the doors go along."""

    def setUp(self):
        self.doc = Document()
        self.wall = bim.add_wall(self.doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        self.door = bim.add_opening(self.doc, self.wall, catalog.OPENING_BY_KEY["porta_80"],
                                    bim.wall_frame(self.doc, self.wall), 2.0, -1)
        self.vol = self.doc.get(self.wall).mesh.volume()

    def test_move_wall_takes_its_door(self):
        doc = self.doc
        door_lo = bounds(doc, self.door)[0].copy()
        bim.transform_objects(doc, [self.wall], translation((1.0, 2.0, 0.0)), "Mover")
        self.assertTrue(np.allclose(bounds(doc, self.wall)[0], (1.0, 1.9, 0.0)))
        self.assertTrue(np.allclose(bounds(doc, self.door)[0], door_lo + (1.0, 2.0, 0.0)))
        self.assertAlmostEqual(doc.get(self.wall).mesh.volume(), self.vol, places=6)   # opening still cut
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertTrue(np.allclose(bounds(doc, self.door)[0], door_lo))

    def test_rotate_wall_then_join_a_new_one(self):
        doc = self.doc
        bim.transform_objects(doc, [self.wall], rotation_about_z((0, 0, 0), 90), "Rodar")
        s, e, _t = doc.ifc.wall_axis(self.wall)
        self.assertTrue(np.allclose(s, 0) and np.allclose(e, (0, 5, 0)))           # now along +y
        self.assertAlmostEqual(doc.get(self.wall).mesh.volume(), self.vol, places=6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_door_slides_along_its_wall(self):
        doc = self.doc
        x0 = bounds(doc, self.door)[0][0]
        bim.slide_filling(doc, self.door, (1.0, 0.7, 0.0))                          # across the wall: ignored
        self.assertAlmostEqual(bounds(doc, self.door)[0][0], x0 + 1.0)
        self.assertAlmostEqual(doc.get(self.wall).mesh.volume(), self.vol, places=6)
        with self.assertRaises(ValueError):
            bim.slide_filling(doc, self.door, (5.0, 0.0, 0.0))                      # would leave the wall
        moved = bim.transform_objects(doc, [self.door], translation((1, 0, 0)), "Mover")
        self.assertEqual(moved, [])                                                 # a door alone is slid, not moved

    def leaf_tip(self):
        """The plan symbol's point farthest from the wall: the open leaf's end, by the hinge jamb."""
        sym = self.doc.ifc.plan_symbols([self.door])[self.door].reshape(-1, 3)
        return sym[np.argmax(np.abs(sym[:, 1]))]

    def test_flip_door_hinge_and_side(self):
        doc = self.doc                                                  # door from x = 2.0 to 2.8, wall y ±0.1
        tip = self.leaf_tip()
        self.assertTrue(tip[0] < 2.1 and tip[1] > 0.7, tip)            # hinges at x = 2, opens to +y
        bim.flip_door(doc, self.door, hinge=True)
        tip = self.leaf_tip()
        self.assertTrue(tip[0] > 2.7 and tip[1] > 0.7, tip)            # the other jamb, the same side
        door = doc.ifc.by_guid(self.door)
        self.assertEqual((ue.get_type(door).Name, door.OperationType), ("Porta 80×210 (à direita)", "SINGLE_SWING_RIGHT"))
        bim.flip_door(doc, self.door, side=True)
        tip = self.leaf_tip()
        self.assertTrue(tip[0] > 2.7 and tip[1] < -0.7, tip)           # the same jamb, the other side
        self.assertEqual(ue.get_type(doc.ifc.by_guid(self.door)).Name, "Porta 80×210")
        self.assertAlmostEqual(doc.get(self.wall).mesh.volume(), self.vol, places=6)   # the same opening
        bim.set_type(doc, self.door, catalog.OPENING_BY_KEY["porta_90"])
        bim.flip_door(doc, self.door, hinge=True)
        bim.set_type(doc, self.door, catalog.OPENING_BY_KEY["porta_80"])           # another size keeps the hand
        self.assertEqual(ue.get_type(doc.ifc.by_guid(self.door)).Name, "Porta 80×210 (à direita)")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        for _ in range(5):
            doc.undo()
        tip = self.leaf_tip()
        self.assertTrue(tip[0] < 2.1 and tip[1] > 0.7, tip)


class WallJoinsKept(unittest.TestCase):
    """Ligações: the corners are remembered (IfcRelConnectsPathElements) and remade."""

    def setUp(self):
        self.doc = Document()
        self.spec = catalog.BY_KEY["parede_alv_20"]
        pts = [np.array(p, float) for p in ((0, 0, 0), (6, 0, 0), (6, 4, 0), (0, 4, 0))]
        self.walls, prev, first = [], None, None
        for i in range(4):
            a, b = pts[i], pts[(i + 1) % 4]
            d = (b - a) / np.linalg.norm(b - a)
            g = bim.add_wall(self.doc, a, b, self.spec, prev=prev, first=first if i == 3 else None)
            self.walls.append(g)
            prev = (g, d)
            if i == 0:
                first = (g, d)

    def total(self):
        return sum(self.doc.get(g).mesh.volume() for g in self.walls)

    def outer(self):
        v = np.vstack([self.doc.get(g).mesh.verts for g in self.walls])
        return v.min(axis=0), v.max(axis=0)

    def test_joints_are_recorded(self):
        rels = self.doc.ifc.file.by_type("IfcRelConnectsPathElements")
        self.assertEqual(len(rels), 4)
        self.assertEqual(sorted((r.RelatingConnectionType, r.RelatedConnectionType) for r in rels),
                         [("ATEND", "ATSTART")] * 3 + [("ATSTART", "ATEND")])
        self.assertEqual(self.doc.ifc.validate(express_rules=True), [])

    def test_moving_a_wall_stretches_its_neighbours(self):
        top = self.walls[2]                                       # the wall at y = 4
        bim.transform_objects(self.doc, [top], translation((0, 1.0, 0)), "Mover")
        lo, hi = self.outer()
        self.assertTrue(np.allclose(lo, (-0.1, -0.1, 0)) and np.allclose(hi, (6.1, 5.1, 2.8)))
        self.assertAlmostEqual(self.total(), 22 * 0.2 * 2.8, places=6)    # the room is 6 × 5 now, corners clean
        self.assertAlmostEqual(self.doc.ifc.wall_params(self.walls[1])[0], 5.0)
        self.assertEqual(self.doc.ifc.validate(express_rules=True), [])
        self.doc.undo()
        self.assertAlmostEqual(self.total(), 20 * 0.2 * 2.8, places=6)

    def test_thinner_wall_keeps_the_corners_clean(self):
        bim.set_type(self.doc, self.walls[1], catalog.BY_KEY["parede_alv_15"])   # the wall at x = 6
        lo, hi = self.outer()
        self.assertAlmostEqual(hi[0], 6.075)                                   # both its neighbours end at its face
        self.assertAlmostEqual(self.total(), (6.175 * 4.2 - 5.825 * 3.8) * 2.8, places=6)

    def test_rotating_a_wall_keeps_it_joined(self):
        right = self.walls[1]
        bim.transform_objects(self.doc, [right], rotation_about_z((6, 2, 0), 10), "Rodar")
        self.assertEqual(len(self.doc.ifc.file.by_type("IfcRelConnectsPathElements")), 4)
        self.assertNotEqual(self.doc.ifc.wall_cuts(self.walls[0])[1], 0.0)    # now a mitre corner
        self.assertEqual(self.doc.ifc.validate(express_rules=True), [])

    def test_a_longer_wall_takes_its_corner_along(self):
        # 0.71 (the owner: "they must stay joined"): the wall at x = 6 goes along, the top one stretches
        bim.resize_wall(self.doc, self.walls[0], at_end=1.0)
        self.assertEqual(len(self.doc.ifc.file.by_type("IfcRelConnectsPathElements")), 4)
        lo, hi = self.outer()
        self.assertTrue(np.allclose(lo, (-0.1, -0.1, 0)) and np.allclose(hi, (7.1, 4.1, 2.8)), (lo, hi))
        self.assertAlmostEqual(self.total(), 22 * 0.2 * 2.8, places=6)        # a 7 × 4 room, corners clean
        self.assertAlmostEqual(self.doc.ifc.wall_params(self.walls[2])[0], 7.0, delta=0.21)   # (± its corners)
        bim.resize_wall(self.doc, self.walls[0], height=3.0)                   # the height keeps the joints
        self.assertEqual(len(self.doc.ifc.file.by_type("IfcRelConnectsPathElements")), 4)
        self.assertEqual(self.doc.ifc.validate(express_rules=True), [])
        self.doc.undo()
        self.doc.undo()
        lo, hi = self.outer()
        self.assertTrue(np.allclose(hi, (6.1, 4.1, 2.8)), hi)

    def test_the_users_three_walls(self):
        # the owner's case (0.71): A along X, B back from its end, C on from B's end; A made 2 m shorter
        doc = Document()
        a = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((9.0, 0.0, 0.0)), self.spec)
        b = bim.add_wall(doc, np.array((9.0, 0.0, 0.0)), np.array((9.0, 5.0, 0.0)), self.spec,
                         prev=(a, np.array((1.0, 0.0, 0.0))))
        c = bim.add_wall(doc, np.array((9.0, 5.0, 0.0)), np.array((14.0, 5.0, 0.0)), self.spec,
                         prev=(b, np.array((0.0, 1.0, 0.0))))
        bim.resize_wall(doc, a, at_end=-2.0)
        sb, eb, _t = doc.ifc.wall_axis(b)
        sc, ec, _t = doc.ifc.wall_axis(c)
        self.assertAlmostEqual(sb[0], 7.0)                                     # B went along, still upright
        self.assertAlmostEqual(eb[0], 7.0)
        self.assertAlmostEqual(ec[0], 14.0)                                    # C's far end stays
        self.assertLess(sc[0], 7.2)                                            # C reaches back to B
        self.assertEqual(len(doc.ifc.file.by_type("IfcRelConnectsPathElements")), 2)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_copied_room_stays_joined_and_delete_cleans_up(self):
        bim.copy_objects(self.doc, self.walls, [translation((10, 0, 0))], "Copiar")
        self.assertEqual(len(self.doc.ifc.file.by_type("IfcRelConnectsPathElements")), 8)
        bim.delete(self.doc, [self.walls[0]])
        self.assertEqual(len(self.doc.ifc.file.by_type("IfcRelConnectsPathElements")), 6)
        self.assertEqual(self.doc.ifc.validate(express_rules=True), [])


class Groups(unittest.TestCase):
    """Grupos (Revit model groups): copies share edits element by element."""

    def setUp(self):
        self.doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        pts = [np.array(p, float) for p in ((0, 0, 0), (4, 0, 0), (4, 3, 0), (0, 3, 0))]
        self.walls, prev, first = [], None, None
        for i in range(4):
            a, b = pts[i], pts[(i + 1) % 4]
            d = (b - a) / np.linalg.norm(b - a)
            g = bim.add_wall(self.doc, a, b, spec, prev=prev, first=first if i == 3 else None)
            self.walls.append(g)
            prev = (g, d)
            if i == 0:
                first = (g, d)
        self.door = bim.add_opening(self.doc, self.walls[0], catalog.OPENING_BY_KEY["porta_80"],
                                    bim.wall_frame(self.doc, self.walls[0]), 1.5, -1)
        self.group = bim.make_group(self.doc, self.walls, "Quarto")

    def copy_group(self, matrix):
        members = self.doc.ifc.group_members(self.group)
        bim.copy_objects(self.doc, members, [matrix], "Copiar")
        groups = self.doc.ifc.group_copies(self.doc.ifc.group_model(self.doc.ifc.by_guid(self.group)))
        return [g for g in groups if g.GlobalId != self.group][-1]

    def twin(self, guid):
        return self.doc.ifc.counterparts(guid)[0]

    def test_group_holds_walls_and_door(self):
        ifc = self.doc.ifc
        members = ifc.group_members(self.group)
        self.assertEqual(len(members), 5)                                     # 4 walls + their door
        self.assertEqual(sorted(ifc.role_of(m) for m in members), [0, 1, 2, 3, 4])
        self.assertEqual(ifc.validate(express_rules=True), [])

    def test_copies_share_edits(self):
        ifc = self.doc.ifc
        copy = self.copy_group(translation((8, 0, 0)))
        self.assertEqual(len(ifc.group_members(copy)), 5)
        self.assertEqual(len(ifc.group_members(self.group)), 5)               # the original group did not grow
        wall_copy = self.twin(self.walls[1])
        bim.resize_wall(self.doc, wall_copy, height=3.2)                      # edit in the copy...
        self.assertAlmostEqual(ifc.wall_params(self.walls[1])[1], 3.2)        # ...the original follows
        bim.set_type(self.doc, self.door, catalog.OPENING_BY_KEY["porta_90"])
        self.assertAlmostEqual(ifc.describe(self.twin(self.door))["size"][0], 0.9)    # the copy's door too
        bim.slide_filling(self.doc, self.door, (0.5, 0, 0))
        xs = [self.doc.get(g).mesh.verts[:, 0].min() for g in (self.door, self.twin(self.door))]
        self.assertAlmostEqual(xs[1] - xs[0], 8.0)                            # the same place in each copy
        self.assertEqual(ifc.validate(express_rules=True), [])

    def test_new_window_and_delete_in_every_copy(self):
        ifc = self.doc.ifc
        copy = self.copy_group(translation((8, 0, 0)))
        win = bim.add_opening(self.doc, self.walls[2], catalog.OPENING_BY_KEY["janela_120"],
                              bim.wall_frame(self.doc, self.walls[2]), 1.0, -1)
        self.assertEqual(ifc.count("IfcWindow"), 2)
        self.assertEqual(ifc.role_of(win), ifc.role_of(self.twin(win)))
        self.assertEqual(len(ifc.group_members(copy)), 6)
        bim.delete(self.doc, [self.twin(win)])                                # deleted in the copy...
        self.assertEqual(ifc.count("IfcWindow"), 0)                           # ...and in the original
        self.assertEqual(ifc.validate(express_rules=True), [])

    def test_moving_an_element_moves_it_in_a_turned_copy(self):
        ifc = self.doc.ifc
        copy = self.copy_group(rotation_about_z((0, 0, 0), 90))
        wall = self.walls[3]                                                  # the wall at x = 0
        twin = self.twin(wall)
        before = self.doc.get(twin).mesh.verts.min(axis=0).copy()
        bim.transform_objects(self.doc, [wall], translation((-1.0, 0, 0)), "Mover")
        after = self.doc.get(twin).mesh.verts.min(axis=0)
        self.assertTrue(np.allclose(after - before, (0, -1.0, 0)))           # the same move, turned 90°
        whole = ifc.group_members(copy)
        lo = self.doc.get(self.walls[0]).mesh.verts.min(axis=0).copy()
        bim.transform_objects(self.doc, whole, translation((0, 20, 0)), "Mover")   # a whole copy moves alone
        self.assertTrue(np.allclose(self.doc.get(self.walls[0]).mesh.verts.min(axis=0), lo))

    def test_library_lists_the_group_and_its_copies(self):
        self.copy_group(translation((8, 0, 0)))
        groups = self.doc.ifc.library()["groups"]
        self.assertEqual([(name, len(copies)) for _m, name, copies in groups], [("Quarto", 2)])
        model = groups[0][0]
        self.assertEqual(len(bim.library_members(self.doc, "group", model)), 10)   # 2 copies × (4 walls + door)

    def test_ungroup_stops_sharing(self):
        ifc = self.doc.ifc
        self.copy_group(translation((8, 0, 0)))
        twin = self.twin(self.walls[1])
        bim.ungroup(self.doc, twin)
        self.assertEqual(ifc.counterparts(self.walls[1]), [])
        bim.resize_wall(self.doc, twin, height=3.5)
        self.assertAlmostEqual(ifc.wall_params(self.walls[1])[1], 2.8)
        self.assertEqual(ifc.validate(express_rules=True), [])

    def test_typical_floor(self):
        doc, ifc = self.doc, self.doc.ifc
        first = bim.add_storey(doc, "Piso 1", 3.0)
        members = ifc.group_members(self.group)
        bim.repeat_on_storeys(doc, members, [first])
        upper = [g for g in ifc.group_copies(ifc.group_model(ifc.by_guid(self.group))) if g.GlobalId != self.group]
        self.assertEqual(len(upper), 1)
        up_members = ifc.group_members(upper[0])
        self.assertTrue(all(ifc.storey_of(m) == first for m in up_members))
        self.assertAlmostEqual(min(doc.get(m).mesh.verts[:, 2].min() for m in up_members), 3.0)
        bim.resize_wall(doc, self.twin(self.walls[0]), height=2.6)            # edit upstairs...
        self.assertAlmostEqual(ifc.wall_params(self.walls[0])[1], 2.6)        # ...downstairs follows
        self.assertEqual(ifc.validate(express_rules=True), [])


class Components(unittest.TestCase):
    """Componentes: an IFC type holding the geometry once; copies share it; editing one changes all."""

    def setUp(self):
        self.doc = Document()
        sketch = box_object(self.doc, (2, 1, 0), 1.2, 0.8, 0.75)          # a table-sized block
        self.inst = bim.make_component(self.doc, [sketch.id], "Mesa", "furniture")

    def instances(self):
        return self.doc.ifc.component_instances(self.doc.ifc.component_type(self.inst))

    def test_component_from_a_sketch(self):
        doc = self.doc
        obj = doc.get(self.inst)
        self.assertEqual((obj.ifc_class, obj.name, doc.ifc.kind_of(self.inst)), ("IfcFurniture", "Mesa", "component"))
        self.assertEqual(doc.sketches(), [])                                  # the sketch became the component
        self.assertAlmostEqual(obj.mesh.volume(), 1.2 * 0.8 * 0.75, places=6)
        self.assertTrue(np.allclose(obj.mesh.verts.min(axis=0), (2, 1, 0)))
        self.assertEqual(doc.ifc.describe(self.inst)["instances"], 1)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_library_and_placing_another_copy(self):
        doc = self.doc
        type_guid = doc.ifc.component_type(self.inst)
        lib = doc.ifc.library()
        self.assertEqual([(g, n, len(i), p) for g, n, i, p in lib["components"]], [(type_guid, "Mesa", 1, True)])
        new = bim.place_component(doc, type_guid, np.array((5.0, 5.0, 0.0)), angle=90.0)
        self.assertEqual(len(self.instances()), 2)
        lo, hi = doc.get(new).mesh.verts.min(axis=0), doc.get(new).mesh.verts.max(axis=0)
        self.assertTrue(np.allclose(lo, (5 - 0.8, 5.0, 0.0)) and np.allclose(hi, (5.0, 5 + 1.2, 0.75)))   # turned
        self.assertEqual(sorted(bim.library_members(doc, "component", type_guid)), sorted([self.inst, new]))

    def test_bring_components_from_another_project(self):
        import ifcopenshell.util.unit
        from arqbim.ifc.model import IfcModel
        with tempfile.TemporaryDirectory() as tmp:
            mm = os.path.join(tmp, "biblioteca.ifc")
            self.doc.save(mm)
            geomcache.forget(mm)
            metres = os.path.join(tmp, "metros.ifc")             # the same in metres (another program's file)
            ifcopenshell.util.unit.convert_file_length_units(ifcopenshell.open(mm), "METER").write(metres)
            for path in (mm, metres):
                doc = Document()
                library, found = IfcModel.read_library(path)
                self.assertEqual([(n, c, k) for _i, n, c, k in found], [("Mesa", "IfcFurnitureType", 1)])
                guids = bim.import_components(doc, library, [found[0][0]])
                self.assertEqual([(n, len(i), p) for _g, n, i, p in doc.ifc.library()["components"]],
                                 [("Mesa", 0, True)])                        # in the library, no copy yet
                lo, hi = doc.ifc.component_box(guids[0])
                self.assertTrue(np.allclose(hi - lo, (1.2, 0.8, 0.75)), (path, lo, hi))   # in this project's mm
                new = bim.place_component(doc, guids[0], (3.0, 2.0, 0.0), angle=90.0)
                v = doc.get(new).mesh.verts
                self.assertTrue(np.allclose(v.min(axis=0), (2.2, 2.0, 0.0)) and np.allclose(v.max(axis=0),
                                                                                         (3.0, 3.2, 0.75)))
                self.assertEqual(bim.import_components(doc, library, [found[0][0]]), guids)   # not twice
                self.assertEqual(doc.ifc.count("IfcFurnitureType"), 1)
                self.assertEqual(doc.ifc.validate(express_rules=True), [])
                for _ in range(3):
                    doc.undo()
                self.assertIsNone(doc.ifc.by_guid(guids[0]))                   # undone: gone again
        doc.undo()
        self.assertEqual(len(self.instances()), 1)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_copies_share_the_geometry(self):
        doc = self.doc
        bim.copy_objects(doc, [self.inst], [translation((2 * k, 0, 0)) for k in (1, 2)], "Copiar")
        self.assertEqual(len(self.instances()), 3)
        self.assertEqual(len(doc.ifc.file.by_type("IfcRepresentationMap")), 1)
        self.assertEqual(len(doc.ifc.file.by_type("IfcPolygonalFaceSet")), 1)   # stored once
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_edit_one_changes_all(self):
        doc = self.doc
        bim.copy_objects(doc, [self.inst], [translation((2, 0, 0))], "Copiar")
        sketch_id = bim.edit_component(doc, self.inst)
        sketch = doc.get(sketch_id)
        self.assertIsNone(doc.get(self.inst))                                 # replaced by the sketch to edit
        self.assertEqual(sketch.component["guid"], self.inst)
        top = [fi for fi in range(len(sketch.mesh.faces))
               if np.allclose(sg.face_world_normal(sketch.matrix, sketch.mesh, fi), (0, 0, 1))][0]
        mesh = sketch.mesh.copy()
        sg.push_pull(mesh, top, sketch.matrix, 0.25)
        doc.execute(ReplaceMesh(sketch_id, sketch.mesh, mesh))
        bim.finish_component(doc, sketch_id)
        self.assertIsNotNone(doc.get(self.inst))                              # same GlobalId again
        vols = [round(doc.get(g).mesh.volume(), 6) for g in self.instances()]
        self.assertEqual(vols, [round(1.2 * 0.8 * 1.0, 6)] * 2)               # both copies are 1,00 m high now
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()                                                            # back to editing
        self.assertIsNone(doc.get(self.inst))
        doc.undo()
        doc.undo()                                                            # back to the component as made
        vols = [round(doc.get(g).mesh.volume(), 6) for g in self.instances()]
        self.assertEqual(vols, [round(1.2 * 0.8 * 0.75, 6)] * 2)

    def test_saved_reopened_and_editing_kept(self):
        doc = self.doc
        sketch_id = bim.edit_component(doc, self.inst)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "comp.ifc")
            doc.save(path)
            doc2 = Document()
            doc2.open(path)
            editing = [o for o in doc2.sketches() if o.component]
            self.assertEqual(len(editing), 1)                                 # still being edited after reopening
            self.assertIsNotNone(bim.finish_component(doc2, editing[0].id))
            self.assertEqual(doc2.ifc.validate(express_rules=True), [])
        self.assertIsNotNone(doc.get(sketch_id))


class CopyIfc(unittest.TestCase):
    """Copiar: a wall with its door, a series of copies, a door in its own wall."""

    def setUp(self):
        self.doc = Document()
        self.wall = bim.add_wall(self.doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        self.door = bim.add_opening(self.doc, self.wall, catalog.OPENING_BY_KEY["porta_80"],
                                    bim.wall_frame(self.doc, self.wall), 2.0, -1)
        self.vol = self.doc.get(self.wall).mesh.volume()

    def test_copy_wall_with_its_door(self):
        doc = self.doc
        new = bim.copy_objects(doc, [self.wall], [translation((0, 3, 0))], "Copiar")
        self.assertEqual(len(new), 1)
        copy = doc.get(new[0])
        self.assertAlmostEqual(copy.mesh.volume(), self.vol, places=6)               # its own opening is cut
        self.assertTrue(np.allclose(copy.mesh.verts.min(axis=0), (0, 2.9, 0)))
        self.assertEqual(doc.ifc.count("IfcDoor"), 2)
        self.assertEqual(copy.name, "Parede 2")
        self.assertEqual(doc.ifc.kind_of(new[0]), "wall")                           # still editable
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertEqual((doc.ifc.count("IfcWall"), doc.ifc.count("IfcDoor")), (1, 1))

    def test_series_of_copies(self):
        doc = self.doc
        new = bim.copy_objects(doc, [self.wall], [translation((0, 3 * k, 0)) for k in (1, 2, 3)], "Copiar")
        self.assertEqual(len(new), 3)
        ys = sorted(round(float(doc.get(g).mesh.verts[:, 1].min()), 6) for g in new)
        self.assertEqual(ys, [2.9, 5.9, 8.9])
        self.assertEqual(doc.ifc.count("IfcOpeningElement"), 4)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_copy_door_in_its_wall(self):
        doc = self.doc
        new = bim.copy_filling(doc, self.door, [np.array((-1.5, 0, 0)), np.array((1.5, 0, 0))])
        self.assertEqual(len(new), 2)
        self.assertAlmostEqual(doc.get(self.wall).mesh.volume(), self.vol - 2 * 0.8 * 2.1 * 0.2, places=6)
        self.assertTrue(all(doc.ifc.host_wall(g) == self.wall for g in new))
        with self.assertRaises(ValueError):
            bim.copy_filling(doc, self.door, [np.array((4.0, 0, 0))])               # would leave the wall
        self.assertEqual(doc.ifc.count("IfcDoor"), 3)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_copy_saved_and_reopened(self):
        doc = self.doc
        bim.copy_objects(doc, [self.wall], [translation((0, 3, 0))], "Copiar")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "copia.ifc")
            doc.save(path)
            doc2 = Document()
            doc2.open(path)
            walls = [o for o in doc2.objects.values() if o.is_bim and o.ifc_class == "IfcWall"]
            self.assertEqual(len(walls), 2)
            self.assertTrue(all(abs(w.mesh.volume() - self.vol) < 1e-6 for w in walls))


class AcceptanceHouse(unittest.TestCase):
    """Phase 1 criterion: walls, slab, 2 doors, 4 windows -> valid IFC that other programs can read."""

    def test_simple_house(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
        from casa_exemplo import build_house
        doc = Document()
        build_house(doc)
        counts = [doc.ifc.count(c) for c in ("IfcWall", "IfcSlab", "IfcDoor", "IfcWindow", "IfcOpeningElement")]
        self.assertEqual(counts, [4, 1, 2, 4, 6])
        self.assertEqual(len(doc.sketches()), 0)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.ifc")
            doc.save(path)
            f = ifcopenshell.open(path)
            for door in f.by_type("IfcDoor") + f.by_type("IfcWindow"):
                self.assertTrue(door.FillsVoids, door.Name)                 # every door/window fills an opening
                self.assertIsNotNone(ue.get_type(door))
                self.assertEqual(ue.get_container(door).Name, "Térreo")
            for wall in f.by_type("IfcWall"):
                self.assertEqual(ue.get_material(wall, should_skip_usage=False).is_a(), "IfcMaterialLayerSetUsage")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class Files(unittest.TestCase):
    def test_save_validate_reopen(self):
        doc = Document()
        wall = box_object(doc, (0, 0, 0), 4.5, 0.2, 2.8)
        slab = box_object(doc, (0, 0, 2.8), 4.5, 3.0, 0.12)
        col = box_object(doc, (6, 0, 0), 0.3, 0.3, 2.8)
        keep = box_object(doc, (10, 0, 0), 1, 1, 1)                    # stays a sketch
        bim.classify(doc, [wall.id], catalog.BY_KEY["parede_alv_20"])
        bim.classify(doc, [slab.id], catalog.BY_KEY["laje_12"])
        bim.classify(doc, [col.id], catalog.BY_KEY["pilar_30"])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])   # schema + IFC4 WHERE rules

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.ifc")
            doc.save(path)
            self.assertFalse(doc.modified)
            self.assertTrue(os.path.exists(sidecar_path(path)))
            f = ifcopenshell.open(path)                                 # what another program reads
            self.assertEqual(f.schema, "IFC4")
            self.assertEqual([len(f.by_type(c)) for c in ("IfcWall", "IfcSlab", "IfcColumn")], [1, 1, 1])
            self.assertEqual(len(f.by_type("IfcBuildingElementProxy")), 0)  # sketches never reach the IFC

            doc2 = Document()
            doc2.open(path)
            self.assertEqual(sorted(o.is_bim for o in doc2.objects.values()), [False, True, True, True])
            sketch = doc2.sketches()[0]
            self.assertAlmostEqual(sketch.mesh.transformed(sketch.matrix).volume(), 1.0)
            self.assertTrue(np.allclose(sketch.matrix[:3, 3], keep.matrix[:3, 3]))
            # the reopened file can be edited and is still valid
            new = box_object(doc2, (0, 6, 0), 3, 0.2, 2.8)
            bim.classify(doc2, [new.id], catalog.BY_KEY["parede_alv_20"])
            self.assertEqual(doc2.ifc.count("IfcWall"), 2)
            self.assertEqual(len(doc2.ifc.file.by_type("IfcWallType")), 1)
            self.assertEqual(doc2.ifc.validate(), [])


def Drawing2D_area(ring):
    x, y = ring[:, 0], ring[:, 1]
    return abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2


class Schedules(unittest.TestCase):
    """Tables of quantities read from the model (Phase 3, step 3)."""

    def setUp(self):
        self.doc = doc = Document()
        wall = catalog.BY_KEY["parede_alv_20"]
        self.w1 = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), wall)
        self.w2 = bim.add_wall(doc, (0, 4, 0), (4, 4, 0), wall)
        self.door = bim.add_opening(doc, self.w1, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, self.w1),
                                    1.0, -1)

    def test_walls_with_their_quantities(self):
        rows = schedules.rows(self.doc, "walls")
        self.assertEqual(len(rows), 2)
        r1 = next(r for r in rows if r["guid"] == self.w1)
        volume = 5 * 2.8 * 0.2 - 0.8 * 2.1 * 0.2                     # the door's opening taken off
        self.assertAlmostEqual(r1["length"], 5.0)
        self.assertAlmostEqual(r1["height"], 2.8)
        self.assertAlmostEqual(r1["thickness"], 0.2)
        self.assertAlmostEqual(r1["volume"], volume, places=6)
        self.assertAlmostEqual(r1["area"], volume / 0.2, places=6)
        self.assertEqual(r1["storey"], "Térreo")
        total = schedules.totals(rows, "walls")
        self.assertEqual(total["count"], 2)
        self.assertAlmostEqual(total["length"], 9.0)
        groups = schedules.by_type(rows, "walls")
        self.assertEqual([(g["count"], round(g["length"], 6)) for g in groups], [(2, 9.0)])
        self.assertEqual(schedules.editable("walls", "height", r1), "height")
        self.assertIsNone(schedules.editable("walls", "volume", r1))

    def test_doors_and_counts(self):
        doors = schedules.rows(self.doc, "doors")
        self.assertEqual(len(doors), 1)
        d = doors[0]
        self.assertEqual((round(d["width"], 6), round(d["height"], 6)), (0.8, 2.1))
        self.assertEqual(d["host"], self.doc.ifc.by_guid(self.w1).Name)
        self.assertIsNone(schedules.editable("doors", "height", d))
        self.assertEqual(schedules.counts(self.doc)["walls"], 2)

    def test_plan_and_section_drawings(self):
        from arqbim.model import drawings
        doc = Document()                                                     # two walls, no door
        bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        bim.add_wall(doc, (0, 4, 0), (4, 4, 0), catalog.BY_KEY["parede_alv_20"])
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual(len(plan.cut), 2)                                   # each wall cut at 1.20 m
        self.assertAlmostEqual(sum(Drawing2D_area(ring) for ring in plan.cut), 5 * 0.2 + 4 * 0.2, places=6)
        with_door = drawings.plan(self.doc, self.doc.active_storey, "Planta")
        self.assertEqual(len(with_door.cut), 3)                       # the wall in two, the other; the door ↓
        self.assertEqual(with_door.hatch, ["masonry"] * 3)            # clay block: hatched
        self.assertEqual({h for _r, h in with_door.fills}, {"gypsum", "masonry"})   # by layer (0.320: each material's
        self.assertEqual(len(with_door.outline), 3)                                 # parts joined; the thick line)
        self.assertAlmostEqual(sum(Drawing2D_area(r) for r, h in with_door.fills if h == "masonry"),
                               (4.2 + 4.0) * 0.16 - 4 * 0.02 * 0.16, places=6)   # the block: 16 cm of the 20 —
        # (0.444) less the plaster turned round the walls' 4 free ends (2 cm each); the door's lining covers its jambs
        sym = with_door.symbols.reshape(-1, 2)                         # its symbol: linings, leaf, swing arc
        self.assertTrue(len(with_door.symbols) > 10 and np.all(sym[:, 0] > 1.0 - 0.05 - 1e-6)     # (0.288: and its
                        and np.all(sym[:, 0] < 1.8 + 0.05 + 1e-6), sym.min(axis=0))            # casings, 5 cm on)
        self.assertAlmostEqual(float(sym[:, 1].min()), -0.1 - 0.015, places=6)  # from the face clicked (a casing)
        self.assertGreater(float(sym[:, 1].max()), 0.1 + 0.6)                   # opening to the other side
        section = drawings.section(self.doc, (2.0, 2.0, 0.0), (0.0, 1.0, 0.0), "Corte")
        lo, hi = section.bounds()
        self.assertAlmostEqual(float(hi[1]), 2.8, places=6)                  # heights as they are
        self.assertGreater(len(section.lines), 0)

    def test_plan_range_and_look(self):
        """0.65: a plan's detail level, crop region, view depth and underlay storey (on paper)."""
        from arqbim.model import drawings
        doc, storey = self.doc, self.doc.active_storey
        key = ("plan", storey)
        doc.set_view_props(key, detail="coarse")
        self.assertEqual({h for _r, h in drawings.plan(doc, storey, "P").fills}, {None})          # solid poché
        doc.set_view_props(key, detail="medium")
        self.assertEqual([h for _r, h in drawings.plan(doc, storey, "P").fills], ["masonry"] * 3)  # one hatch each
        doc.set_view_props(key, crop=[-1.0, -1.0, 3.0, 1.0])            # round the first wall's left part only
        cropped = drawings.plan(doc, storey, "P")
        lo, hi = cropped.bounds()
        self.assertTrue(lo[0] >= -1.0 - 1e-9 and hi[0] <= 3.0 + 1e-9 and hi[1] <= 1.0 + 1e-9, (lo, hi))
        self.assertEqual(len(cropped.cut), 2)                # the wall at y = 4 left out; the first one's two parts
        upper = bim.add_storey(doc, "Piso 1", 3.0)           # a storey above, with nothing on it
        up_key = ("plan", upper)
        self.assertIsNone(drawings.plan(doc, upper, "P1").bounds())
        doc.set_view_props(up_key, depth=3.5)                # it sees down to the ground storey
        self.assertGreater(len(drawings.plan(doc, upper, "P1").lines), 0)
        doc.set_view_props(up_key, depth=None, underlay="below")
        under = drawings.plan(doc, upper, "P1")
        self.assertIsNone(under.bounds())                    # (an underlay alone is not a drawing)
        self.assertGreater(len(under.underlay), 0)

    def test_door_plan_symbol_and_hatches_in_the_ifc(self):
        ifc = self.doc.ifc
        door = ifc.by_guid(self.door)
        reps = [(r.ContextOfItems.ContextType, r.RepresentationIdentifier, r.RepresentationType)
                for r in door.Representation.Representations]
        self.assertEqual(reps[0][:2], ("Model", "Body"))                      # the 3D body first (other programs)
        self.assertIn(("Plan", "Body", "Curve2D"), reps)
        self.assertEqual(ifc.validate(express_rules=True), [])
        bim.set_type(self.doc, self.w1, catalog.BY_KEY["parede_alv_15"])     # the door made again: one symbol
        door = ifc.by_guid(self.door)
        self.assertEqual(sum(r.ContextOfItems.ContextType == "Plan" for r in door.Representation.Representations), 1)
        self.assertEqual(len(ifc.file.by_type("IfcGeometricRepresentationSubContext")), 4)   # Body, Axis, Plan —
        #                                                                     (0.292) and its signs' ELEVATION_VIEW
        slab = bim.add_slab(self.doc, (0, 0, 0), 5, 4, catalog.BY_KEY["laje_12"])
        dry = bim.add_wall(self.doc, (0, 8, 0), (4, 8, 0), catalog.BY_KEY["parede_dry_10"])
        hatches = ifc.hatches([self.w2, slab, dry, self.door])
        self.assertEqual(hatches, {self.w2: "masonry", slab: "concrete", dry: "insulation",
                                   self.door: "wood"})                    # (its type's material since 0.70)

    def test_csv_for_excel(self):
        rows = schedules.rows(self.doc, "walls")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "paredes.csv")
            schedules.write_csv(path, ["Nome", "Comprimento"], [[r["name"], r["length"]] for r in rows])
            with open(path, encoding="utf-8-sig") as f:
                text = f.read()
        self.assertTrue(text.startswith("Nome;Comprimento"))
        self.assertIn(";5,000", text)

    def test_excel_workbook(self):
        """0.370: a table as an Excel workbook — its numbers as numbers (also those already written as text with the
        decimal comma, their decimals as shown; a code like «01» and «—» kept as text), the headings in bold with a
        filter over the rows before the totals, kept on top; the totals' line as it is; by the path's extension
        (write_table), else a CSV."""
        import openpyxl
        self.assertEqual([schedules.xlsx_value(v) for v in ("4,00", "12", "1 234,5", "01", "—", "Ø12", None, 2.5, 3)],
                         [(4.0, 2), (12, 0), (1234.5, 1), ("01", None), ("—", None), ("Ø12", None), (None, None),
                          (2.5, 1), (3, 0)])
        self.assertEqual(schedules.xlsx_value("4.25", decimal="."), (4.25, 2))
        rows = schedules.rows(self.doc, "walls")
        table = [[r["name"], r["length"], "12", "—", "19,1"] for r in rows] + [[], ["Total: 2 paredes"]]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "paredes.xlsx")
            schedules.write_table(path, ["Nome", "Comprimento", "Ø", "Nota", "Peso"], table, title="Paredes: térreo")
            sheet = openpyxl.load_workbook(path).active
            schedules.write_table(os.path.join(tmp, "paredes.csv"), ["Nome"], [["a"]])
            self.assertTrue(os.path.exists(os.path.join(tmp, "paredes.csv")))
        n = len(rows)
        self.assertEqual(sheet.title, "Paredes- térreo")                 # (':' is not allowed in a sheet's name)
        self.assertEqual([c.value for c in sheet[1]], ["Nome", "Comprimento", "Ø", "Nota", "Peso"])
        self.assertTrue(sheet["A1"].font.b)
        self.assertEqual((sheet.freeze_panes, sheet.auto_filter.ref), ("A2", "A1:E{}".format(n + 1)))
        self.assertEqual([sheet.cell(row=r, column=2).value for r in range(2, n + 2)], [r["length"] for r in rows])
        self.assertEqual(sheet["B2"].number_format, "0.00")                  # (a measure given as a number: 5,00)
        self.assertEqual((sheet["C2"].value, sheet["C2"].number_format, sheet["D2"].value), (12, "0", "—"))
        self.assertEqual((sheet["E2"].value, sheet["E2"].number_format), (19.1, "0.0"))   # (as it was shown)
        self.assertEqual(sheet.cell(row=n + 3, column=1).value, "Total: 2 paredes")


class Sheets(unittest.TestCase):
    """Sheets: several views on paper, laid out on their own or where put, kept beside the
    IFC (Phase 3, step 8)."""

    def setUp(self):
        self.doc = doc = Document()
        bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        bim.add_wall(doc, (0, 4, 0), (4, 4, 0), catalog.BY_KEY["parede_alv_20"])
        doc.add_section((2.0, 2.0, 0.0), (0.0, 1.0, 0.0))
        self.k = doc.add_sheet()
        for kind, ref in (("plan", doc.active_storey), ("section", "Corte 1"), ("elevation", "S")):
            doc.put_on_sheet(self.k, kind, ref)

    def frames(self):
        from arqbim.model import drawings
        sheet = self.doc.sheets[self.k]
        made = [drawings.of_view(self.doc, v.kind, v.ref, "") for v in sheet.views]
        return sheets.layout(sheet, [sheets.extent(d) for d in made])

    def test_laid_out_at_one_scale(self):
        doc = self.doc
        self.assertEqual(doc.sheets[self.k].name, "Folha 1")
        self.assertEqual(doc.put_on_sheet(self.k, "plan", doc.active_storey), (self.k, 0))   # not twice
        frames = self.frames()
        self.assertEqual([f.scale for f in frames], [50, 50, 50])        # 1:20 does not fit on A3
        left, top, width, height = sheets.drawing_area("A3")
        rects = [f.rect() for f in frames]
        for x, y, w, h in rects:
            self.assertTrue(left - 1e-6 <= x and x + w <= left + width + 1e-6 and top - 1e-6 <= y
                            and y + h <= top + height + 1e-6, (x, y, w, h))
        for a in range(3):
            for b in range(a + 1, 3):
                (ax, ay, aw, ah), (bx, by, bw, bh) = rects[a], rects[b]
                self.assertTrue(ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)   # apart
        self.assertAlmostEqual(frames[2].width, 5.0 * 1000 / 50, places=3)   # the south wall, 5 m long

    def test_scale_place_and_paper(self):
        doc = self.doc
        doc.change_sheet(self.k, view=0, scale=100)
        doc.change_sheet(self.k, view=1, at=(100.0, 80.0))
        frames = self.frames()
        self.assertEqual(frames[0].scale, 100)
        self.assertEqual(frames[1].centre, (100.0, 80.0))
        doc.change_sheet(self.k, paper="A1")
        self.assertEqual(self.frames()[2].scale, 20)                     # a bigger paper: a bigger scale
        doc.change_sheet(self.k, view=2, remove=True)
        self.assertEqual(len(doc.sheets[self.k].views), 2)

    def test_views_are_undone(self):
        from arqbim.model import dimensions as dims
        doc = self.doc                                  # (setUp: a section, a sheet with 3 views)
        dim = dims.Dimension(("section", "Corte 1"), np.zeros(3), np.array((0.0, 0.0, 2.8)), np.ones(3))
        doc.execute(dims.AddDimension(dim, "Cota"))
        uid = doc.sheets[self.k].uid
        doc.change_sheet(self.k, view=1, at=(100.0, 80.0))
        doc.undo()
        self.assertIsNone(doc.sheets[self.k].views[1].at)
        self.assertEqual(doc.sheets[self.k].uid, uid)                         # the same sheet, for its window
        self.assertTrue(doc.rename_section(0, "Corte A"))
        doc.remove_section(0)
        self.assertEqual((doc.sections, len(doc.sheets[self.k].views), doc.dimensions), ([], 2, []))
        doc.undo()                                                            # the section, its view, its dimension
        self.assertEqual([s.name for s in doc.sections], ["Corte A"])
        self.assertEqual(doc.sheets[self.k].views[1].ref, "Corte A")
        self.assertEqual(doc.dimensions, [dim])
        doc.undo()                                                            # the name
        self.assertEqual((doc.sections[0].name, dim.view, doc.sheets[self.k].views[1].ref),
                         ("Corte 1", ("section", "Corte 1"), "Corte 1"))
        doc.undo()                                                            # the dimension
        self.assertEqual(doc.dimensions, [])
        doc.redo()
        doc.redo()
        self.assertEqual((doc.sections[0].name, dim.view), ("Corte A", ("section", "Corte A")))
        k, j = doc.put_on_sheet(None, "elevation", "N")                       # on a new sheet: one step
        self.assertEqual((len(doc.sheets), k, j), (2, 1, 0))
        doc.undo()
        self.assertEqual(len(doc.sheets), 1)

    def test_too_big_and_empty(self):
        sheet = sheets.Sheet("F", views=[sheets.Placed("plan", "a"), sheets.Placed("plan", "b")])
        frames = sheets.layout(sheet, [(900.0, 600.0), None])
        self.assertEqual(frames[0].scale, 1000)                          # the smallest usual scale
        self.assertIsNone(frames[1])                                      # nothing to draw: no frame

    def test_kept_beside_the_ifc_and_following_the_sections(self):
        doc = self.doc
        doc.change_sheet(self.k, view=1, at=(100.0, 80.0), scale=20)
        doc.change_sheet(self.k, paper="A2")
        doc.add_sheet()
        self.assertEqual(doc.sheets[-1].name, "Folha 2")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "folhas.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        self.assertEqual([(s.name, s.paper) for s in again.sheets], [("Folha 1", "A2"), ("Folha 2", "A3")])
        self.assertEqual([(v.kind, v.scale, v.at) for v in again.sheets[0].views],
                         [("plan", None, None), ("section", 20, (100.0, 80.0)), ("elevation", None, None)])
        self.assertTrue(again.rename_section(0, "Corte A"))
        self.assertEqual(again.sheets[0].views[1].ref, "Corte A")         # the sheet follows the new name
        again.add_section((1.0, 1.0, 0.0), (1.0, 0.0, 0.0))
        self.assertFalse(again.rename_section(1, "Corte A"))             # two sections with one name: no
        again.remove_section(0)
        self.assertEqual([v.kind for v in again.sheets[0].views], ["plan", "elevation"])
        from arqbim.model import drawings
        self.assertIsNone(drawings.of_view(again, "plan", "no-such-storey", ""))

    def test_open_view_tabs_kept_beside_the_ifc(self):
        doc = self.doc
        camera = {"position": (1.0, 2.0, 30.0), "rotation": (0.0, 0.0, 0.0, 1.0), "focus": (1.0, 2.0, 0.0),
                  "fov": 0.0, "width": 12.0, "height": 12.0, "zoom": 1.0}
        doc.open_views = {"tabs": [{"key": ["3d"], "camera": None},
                                   {"key": ["plan", doc.active_storey], "camera": camera},
                                   {"key": ["sheet", doc.sheets[0].uid], "camera": None}],
                          "current": ["plan", doc.active_storey]}
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "abas.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        views = again.open_views
        self.assertEqual([tab["key"] for tab in views["tabs"]],
                         [("3d",), ("plan", doc.active_storey), ("sheet", doc.sheets[0].uid)])
        self.assertEqual(views["current"], ("plan", doc.active_storey))
        cam = views["tabs"][1]["camera"]
        self.assertTrue(np.allclose(cam["position"], (1.0, 2.0, 30.0)) and np.allclose(cam["focus"], (1.0, 2.0, 0.0)))
        self.assertEqual((cam["fov"], cam["height"]), (0.0, 12.0))
        with tempfile.TemporaryDirectory() as tmp:          # saved again as read (a project opened without a window)
            again.save(os.path.join(tmp, "de_novo.ifc"))

    def test_title_block(self):
        doc = self.doc                                  # (setUp: one sheet)
        doc.add_sheet()
        first, second = doc.sheets
        self.assertEqual([sheets.number_of(doc.sheets, s) for s in doc.sheets], ["01", "02"])   # by their order
        texts = sheets.title_texts(doc.title_block, first.name, "01", "casa")
        self.assertEqual((texts["project"], texts["client"], texts["title"]), ("casa", "", "Folha 1"))
        doc.set_title_block({"project": " Moradia em Sintra ", "client": "J. Silva", "stage": "Licenciamento",
                             "nonsense": "x"}, 0, "Plantas", "A.01")
        self.assertEqual(doc.title_block, {"project": "Moradia em Sintra", "client": "J. Silva",
                                           "stage": "Licenciamento"})
        self.assertEqual((first.name, sheets.number_of(doc.sheets, first)), ("Plantas", "A.01"))
        steps = len(doc._undo)
        doc.set_title_block(dict(doc.title_block), 0, "Plantas", "A.01")      # the same: no undo step
        self.assertEqual(len(doc._undo), steps)
        texts = sheets.title_texts(doc.title_block, first.name, "A.01", "casa")
        self.assertEqual((texts["project"], texts["stage"], texts["site"]), ("Moradia em Sintra", "Licenciamento", ""))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "legenda.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        self.assertEqual(again.title_block, doc.title_block)
        self.assertEqual([(s.name, s.number) for s in again.sheets], [("Plantas", "A.01"), ("Folha 2", "")])
        self.assertEqual([s.uid for s in again.sheets], [s.uid for s in doc.sheets])     # (their tabs find them)
        doc.undo()                                                            # one step: fields, name and number
        self.assertEqual((doc.title_block, doc.sheets[0].name, doc.sheets[0].number), ({}, "Folha 1", ""))
        doc.redo()
        self.assertEqual((doc.title_block["client"], doc.sheets[0].number), ("J. Silva", "A.01"))


class GraphicRules(unittest.TestCase):
    """Colour by a property (Phase 4, step 1): the values read from the IFC, the legend."""

    def test_values_and_legend(self):
        from arqbim.model import graphic_rules as rules
        doc = Document()
        w1 = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        w2 = bim.add_wall(doc, (0, 4, 0), (5, 4, 0), catalog.BY_KEY["parede_dry_10"])
        slab = bim.add_slab(doc, (0, 0, 0), 5, 4, catalog.BY_KEY["laje_12"])
        bim.set_property(doc, w2, "Pset_WallCommon", "IsExternal", False)  # (0.267: alone, both outside)
        ifc, ids = doc.ifc, [w1, w2, slab]
        self.assertEqual(ifc.property_values(ids, ("class",)), {w1: "IfcWall", w2: "IfcWall", slab: "IfcSlab"})
        self.assertEqual(ifc.property_values(ids, ("type",))[w2], "Parede drywall 10 cm")
        self.assertEqual(ifc.property_values(ids, ("material",)), {w1: "Bloco cerâmico", w2: "Lã mineral",
                                                                   slab: "Concreto"})
        outside = ifc.property_values(ids, ("external",))
        self.assertEqual((outside[w1], outside[w2]), (True, False))
        self.assertIn(("Pset_WallCommon", "IsExternal"), ifc.property_keys())
        self.assertEqual(ifc.property_values([w1], ("pset", "Pset_WallCommon", "IsExternal")), {w1: True})
        lines = rules.legend(outside)
        self.assertEqual([(label, colour, len(g)) for label, colour, g in lines],
                         [("Não", rules.NO, 2), ("Sim", rules.YES, 1)])        # (the slab: Pset_SlabCommon)
        lines = rules.legend({w1: "A", w2: None, slab: "B"})
        self.assertEqual([label for label, _c, _g in lines], ["A", "B", "(sem valor)"])   # no value last, grey
        self.assertEqual(rules.colours(lines)[w2], rules.NO_VALUE)


class ViewTemplates(unittest.TestCase):
    """View templates (Phase 4, step 3): settings given to several views, kept, undone."""

    def test_settings_drawings_and_kept(self):
        from arqbim.model import drawings
        from arqbim.model.view_templates import ViewTemplate
        doc = Document()
        bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        sketch = box_object(doc, (2, 1, 0), 1.2, 0.8, 0.75)
        bim.make_component(doc, [sketch.id], "Mesa", "furniture")
        storey = doc.active_storey
        plain = drawings.plan(doc, storey, "P")
        tpl = ViewTemplate("Planta de obra", cut_height=1.0, hidden=["IfcFurniture"], rule=("class",), scale=50)
        doc.set_templates([tpl])
        doc.assign_template(("plan", storey), tpl.uid)
        s = doc.view_settings(("plan", storey))
        self.assertEqual((s.cut_height, s.hidden, s.rule, s.scale, s.template),
                         (1.0, frozenset({"IfcFurniture"}), ("class",), 50, "Planta de obra"))
        self.assertEqual(doc.view_settings(("plan", "another")).cut_height, 1.20)        # no template: defaults
        templated = drawings.plan(doc, storey, "P")
        self.assertLess(len(templated.lines), len(plain.lines))                        # no table seen any more
        sheet = sheets.Sheet("F", views=[sheets.Placed("plan", storey)])
        self.assertEqual(sheets.layout(sheet, [sheets.extent(templated)], [s.scale])[0].scale, 50)
        doc.add_section((2.0, 2.0, 0.0), (0.0, 1.0, 0.0))
        doc.assign_template(("section", "Corte 1"), tpl.uid)
        doc.rename_section(0, "Corte A")
        self.assertEqual(doc.template_of(("section", "Corte A")).name, "Planta de obra")   # follows the name
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "modelos.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        self.assertEqual([t.name for t in again.templates], ["Planta de obra"])
        self.assertEqual(again.view_settings(("plan", storey)).hidden, frozenset({"IfcFurniture"}))
        self.assertEqual(again.template_of(("section", "Corte A")).uid, tpl.uid)
        for _ in range(5):                              # rename, assign, section, assign, templates
            doc.undo()
        self.assertEqual((doc.templates, doc.view_templates), ([], {}))

    def test_own_view_properties(self):
        """0.59: a view without a template has its own properties (the Properties panel with nothing
        selected): used on screen and on paper, under a template, kept, undone, renamed with a section."""
        from arqbim.model import drawings
        from arqbim.model.view_templates import ViewTemplate
        doc = Document()
        bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        sketch = box_object(doc, (2, 1, 0), 1.2, 0.8, 0.75)
        bim.make_component(doc, [sketch.id], "Mesa", "furniture")
        storey = doc.active_storey
        plan = ("plan", storey)
        plain = drawings.plan(doc, storey, "P")
        self.assertTrue(doc.set_view_props(plan, cut_height=1.5, hidden=["IfcFurniture"], scale=50))
        self.assertFalse(doc.set_view_props(plan, scale=50))                    # unchanged: no undo step
        doc.set_view_props(("3d",), phases="new", rule=("class",), style="hidden", edges=False, axonometric=True)
        s = doc.view_settings(plan)
        self.assertEqual((s.cut_height, s.hidden, s.scale, s.template), (1.5, frozenset({"IfcFurniture"}), 50, None))
        three = doc.view_settings(("3d",))
        self.assertEqual((three.phases, three.rule, three.cut_height), ("new", ("class",), 1.20))
        self.assertIn("EXISTING", three.hidden_phases)
        self.assertLess(len(drawings.plan(doc, storey, "P").lines), len(plain.lines))   # no table on paper
        tpl = ViewTemplate("Geral", cut_height=1.0)
        doc.set_templates([tpl])
        doc.assign_template(plan, tpl.uid)
        self.assertEqual((doc.view_settings(plan).cut_height, doc.view_settings(plan).hidden), (1.0, frozenset()))
        doc.assign_template(plan, None)                                          # its own again
        self.assertEqual(doc.view_settings(plan).cut_height, 1.5)
        doc.add_section((2.0, 2.0, 0.0), (0.0, 1.0, 0.0))
        doc.set_view_props(("section", "Corte 1"), scale=20)
        doc.rename_section(0, "Corte A")
        self.assertEqual(doc.view_settings(("section", "Corte A")).scale, 20)        # follows the name
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "vistas.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        self.assertEqual(again.view_settings(plan).cut_height, 1.5)
        self.assertEqual(again.view_settings(plan).hidden, frozenset({"IfcFurniture"}))
        self.assertEqual(again.view_settings(("3d",)).rule, ("class",))
        three = again.view_settings(("3d",))                                          # 0.63: its look
        self.assertEqual((three.style, three.edges, three.grid, three.axonometric), ("hidden", False, True, True))
        self.assertEqual(again.view_settings(("section", "Corte A")).scale, 20)
        self.assertEqual(again.view_settings(("3d",)).box, None)
        doc.set_view_props(plan, hidden=None, cut_height=None, scale=None)           # back to the defaults
        self.assertNotIn(plan, doc.view_props)
        doc.undo()
        self.assertEqual(doc.view_settings(plan).cut_height, 1.5)
        doc.remove_section(0)
        self.assertNotIn(("section", "Corte A"), doc.view_props)
        for _ in range(8):                  # remove, rename, props, section, assign ×2, templates, 3D props
            doc.undo()
        self.assertEqual(doc.view_props, {plan: {"cut_height": 1.5, "hidden": ["IfcFurniture"], "scale": 50}})
        doc.undo()
        self.assertEqual(doc.view_props, {})


    def test_named_3d_views_and_section_box(self):
        """0.64: named 3D views (their camera, look and box) and the 3D view's section box, kept and undone."""
        doc = Document()
        bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        camera = {"position": (10.0, -8.0, 6.0), "rotation": (0.1, 0.2, 0.3, 0.9), "focus": (2.0, 1.0, 1.0),
                  "fov": 45.0, "width": 10.0, "height": 10.0, "zoom": 1.0}
        doc.set_view_props(("3d",), box=[[0.0, -1.0, 0.0], [3.0, 1.0, 1.5]])
        key = doc.add_view3d(camera, {"style": "hidden", "box": [[0.0, -1.0, 0.0], [3.0, 1.0, 1.5]]})
        self.assertEqual(doc.view3d(key[1]).name, "3D 1")
        self.assertEqual(doc.add_view3d(camera)[0], "3d")
        self.assertEqual([v.name for v in doc.views3d], ["3D 1", "3D 2"])
        self.assertTrue(doc.rename_view3d(key[1], "Fachada"))
        self.assertFalse(doc.rename_view3d(key[1], "3D 2"))                       # another one has it
        doc.keep_view3d_camera(key[1], dict(camera, focus=(3.0, 1.0, 1.0)))
        self.assertEqual(doc.view_settings(key).style, "hidden")
        self.assertEqual(doc.view_settings(key).box, ((0.0, -1.0, 0.0), (3.0, 1.0, 1.5)))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "vistas3d.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        view = again.view3d(key[1])
        self.assertEqual((view.name, view.camera["focus"]), ("Fachada", (3.0, 1.0, 1.0)))
        self.assertEqual(again.view_settings(key).style, "hidden")
        self.assertEqual(again.view_settings(("3d",)).box, ((0.0, -1.0, 0.0), (3.0, 1.0, 1.5)))
        doc.remove_view3d(key[1])
        self.assertIsNone(doc.view3d(key[1]))
        self.assertNotIn(key, doc.view_props)
        for _ in range(4):                                      # remove, rename, 3D 2, 3D 1
            doc.undo()
        self.assertEqual(doc.views3d, [])
        doc.undo()                                              # the box
        self.assertIsNone(doc.view_settings(("3d",)).box)


class Phases(unittest.TestCase):
    """Phases of a renovation project (Phase 4, step 5): IFC Status, filtered views, yellows and reds."""

    def test_status_views_and_drawings(self):
        from arqbim.model import drawings
        from arqbim.model import graphic_rules as rules
        from arqbim.model.view_templates import phase_templates
        doc = Document()
        kept = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        built = bim.add_wall(doc, (0, 3, 0), (5, 3, 0), catalog.BY_KEY["parede_alv_20"])
        gone = bim.add_wall(doc, (0, 6, 0), (5, 6, 0), catalog.BY_KEY["parede_alv_20"])
        self.assertEqual(bim.set_status(doc, [kept], "EXISTING"), 1)
        bim.set_status(doc, [built], "NEW")
        bim.set_status(doc, [gone], "DEMOLISH")
        self.assertEqual([doc.status_of(g) for g in (kept, built, gone)], ["EXISTING", "NEW", "DEMOLISH"])
        e = doc.ifc.by_guid(built)
        statuses = [p for rel in e.IsDefinedBy for p in getattr(rel.RelatingPropertyDefinition, "HasProperties", ())
                    if p.Name == "Status"]
        self.assertEqual([p.is_a() for p in statuses], ["IfcPropertyEnumeratedValue"])    # as IFC4 says
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        existing, proposal, changes = phase_templates(lambda key: key)
        doc.set_templates([existing, proposal, changes])
        storey = doc.active_storey
        doc.assign_template(("plan", storey), existing.uid)
        self.assertEqual(len(drawings.plan(doc, storey, "P").cut), 2)       # the wall to build is not there yet
        doc.assign_template(("plan", storey), proposal.uid)
        self.assertEqual(len(drawings.plan(doc, storey, "P").cut), 2)       # the one demolished is gone
        doc.assign_template(("plan", storey), changes.uid)
        fills = [h for _ring, h in drawings.plan(doc, storey, "P").fills]
        self.assertIn("colour:" + rules.PHASE_COLOURS["NEW"], fills)          # reds
        self.assertIn("colour:" + rules.PHASE_COLOURS["DEMOLISH"], fills)     # yellows
        self.assertIn("masonry", fills)                                       # what stays: its hatch
        values = doc.ifc.property_values([kept, built, gone], ("status",))
        self.assertEqual([label for label, _c, _g in rules.legend(values, rules.STATUS)],
                         ["Existente", "A demolir", "Novo (a construir)"])
        bim.set_status(doc, [built], None)                                     # cleared
        self.assertIsNone(doc.status_of(built))
        doc.undo()
        self.assertEqual(doc.status_of(built), "NEW")


class SharedMerge(unittest.TestCase):
    """Team work on a shared folder (Phase 4, step 6): the three-way merge of IFC files."""

    def test_two_people_merged(self):
        from arqbim.model import sharing
        with tempfile.TemporaryDirectory() as tmp:
            doc = Document()
            w1 = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
            base = os.path.join(tmp, "base.ifc")
            doc.save(base)
            mine_doc = Document()
            mine_doc.open(base)
            w2 = bim.add_wall(mine_doc, (0, 4, 0), (5, 4, 0), catalog.BY_KEY["parede_alv_20"])
            bim.resize_wall(mine_doc, w1, height=3.2)                       # here: a wall more, the first higher
            mine = os.path.join(tmp, "mine.ifc")
            mine_doc.save(mine)
            theirs_doc = Document()
            theirs_doc.open(base)
            w3 = bim.add_wall(theirs_doc, (0, 8, 0), (5, 8, 0), catalog.BY_KEY["parede_dry_10"])
            bim.rename(theirs_doc, w1, "Parede da rua")                     # there: another wall, a new name
            theirs = os.path.join(tmp, "theirs.ifc")
            theirs_doc.save(theirs)
            texts = [open(p, encoding="utf-8").read() for p in (base, mine, theirs)]
            merged, conflicts = sharing.merge(*texts)
            out = os.path.join(tmp, "merged.ifc")
            with open(out, "w", encoding="utf-8") as f:
                f.write(merged)
            for p in (base, mine, theirs):
                geomcache.forget(p)
            result = Document()
            result.open(out)
            geomcache.forget(out)
        self.assertEqual(conflicts, [])
        walls = {g: o for g, o in result.objects.items() if o.is_bim and o.ifc_class == "IfcWall"}
        self.assertEqual(set(walls), {w1, w2, w3})                           # everyone's walls
        self.assertEqual(result.ifc.by_guid(w1).Name, "Parede da rua")      # their name…
        self.assertAlmostEqual(result.ifc.wall_params(w1)[1], 3.2)           # …and my height
        self.assertEqual({o.storey for o in walls.values()}, {result.active_storey})   # all on the storey
        self.assertEqual(result.ifc.validate(express_rules=True), [])

    def test_two_people_through_the_shared_folder(self):
        from arqbim.model import sharing
        old_root = os.environ.get("ARQBIM_SHARE_DIR")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                office = os.path.join(tmp, "servidor")
                os.makedirs(office)
                doc = Document()
                w1 = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
                doc.add_section((2.0, 2.0, 0.0), (0.0, 1.0, 0.0))
                path = os.path.join(tmp, "casa.ifc")
                doc.save(path)
                central = sharing.share(path, office)

                def local_of(name):                       # each one's computer: their own local folder
                    os.environ["ARQBIM_SHARE_DIR"] = os.path.join(tmp, "pc_" + name)
                    return sharing.open_shared(central)
                ana, rui = local_of("ana"), local_of("rui")
                self.assertEqual(sharing.central_of(ana), os.path.abspath(central))
                a = Document()
                a.open(ana)
                w2 = bim.add_wall(a, (0, 4, 0), (5, 4, 0), catalog.BY_KEY["parede_alv_20"])
                a.add_sheet()                             # Ana holds the views: her sheet goes too
                a.save(ana)
                sharing.Reservations(central).take("ana", [sharing.VIEWS])
                first = sharing.sync(ana, "ana")
                r = Document()
                r.open(rui)                               # Rui, meanwhile, from the old central
                w3 = bim.add_wall(r, (0, 8, 0), (5, 8, 0), catalog.BY_KEY["parede_alv_20"])
                r.save(rui)
                second = sharing.sync(rui, "rui")
                again = sharing.sync(ana, "ana")
                final = Document()
                final.open(ana)
                for p in (path, central, ana, rui):
                    geomcache.forget(p)
            self.assertEqual((first.mine_changed, first.theirs_changed, first.views), (True, False, "sent"))
            self.assertEqual((second.mine_changed, second.theirs_changed, second.views, second.conflicts),
                             (True, True, "received", []))
            self.assertEqual((again.mine_changed, again.theirs_changed), (False, True))
            walls = {g for g, o in final.objects.items() if o.is_bim and o.ifc_class == "IfcWall"}
            self.assertEqual(walls, {w1, w2, w3})                       # Ana now has Rui's wall too
            self.assertEqual(len(final.sheets), 1)
            self.assertEqual(final.ifc.validate(express_rules=True), [])
        finally:
            if old_root is None:
                os.environ.pop("ARQBIM_SHARE_DIR", None)
            else:
                os.environ["ARQBIM_SHARE_DIR"] = old_root

    def test_conflict_keeps_the_central_and_reservations(self):
        from arqbim.model import sharing
        base = "ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\n#1=IFCLABEL('a');\n#2=IFCX(#1,'b');\nENDSEC;\nEND-ISO-10303-21;\n"
        mine = base.replace("'b'", "'mine'")
        theirs = base.replace("'b'", "'theirs'")
        merged, conflicts = sharing.merge(base, mine, theirs)
        self.assertIn("#2=IFCX(#1,'theirs');", merged)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(sharing.split_args("IFCX('it''s, ok',(#1,#2),$)")[1], ["'it''s, ok'", "(#1,#2)", "$"])
        with tempfile.TemporaryDirectory() as tmp:
            central = os.path.join(tmp, "casa.ifc")
            res = sharing.Reservations(central)
            self.assertEqual(res.take("ana", ["w1", "w2"]), {})
            self.assertEqual(res.take("rui", ["w2", "w3"]), {"w2": "ana"})     # w2 is Ana's
            self.assertEqual({k: u for k, (u, _s) in res.read().items()}, {"w1": "ana", "w2": "ana", "w3": "rui"})
            res.give_back("ana")
            self.assertEqual({k: u for k, (u, _s) in res.read().items()}, {"w3": "rui"})


class Notes(unittest.TestCase):
    """Coordination notes (Phase 4, step 4): BCF topics kept with the project, undone, exchanged."""

    def test_kept_beside_the_ifc_undone_and_imported(self):
        from arqbim.model import notes as notes_model
        from arqbim.model.document import notes_file
        doc = Document()
        wall = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        note = notes_model.Note("Parede a mais", "confirmar com o cliente", author="arq", date=notes_model.now(),
                                camera=notes_model.Camera((2.0, -8.0, 3.0), (0.0, 1.0, -0.2)), selected=[wall])
        doc.change_notes("Nova nota", lambda d: d.notes.append(note))
        doc.change_notes("Comentar", lambda d: d.notes[0].comments.append(("eng", notes_model.now(), "visto")))
        self.assertEqual(len(doc.notes[0].comments), 1)
        doc.undo()
        self.assertEqual(doc.notes[0].comments, [])
        doc.redo()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "notas.ifc")
            doc.save(path)
            self.assertTrue(os.path.exists(notes_file(path)))               # notas.bcfzip beside notas.ifc
            again = Document()
            again.open(path)
            geomcache.forget(path)
            got = again.notes[0]
            self.assertEqual((got.title, got.selected, got.comments[0][2], got.guid),
                             ("Parede a mais", [wall], "visto", note.guid))
            self.assertTrue(np.allclose(got.camera.position, (2.0, -8.0, 3.0)))
            other = os.path.join(tmp, "dos_outros.bcfzip")                   # another's notes: one new, one changed
            theirs = notes_model.Note("Pilar fora do eixo", author="eng", date=notes_model.now())
            changed = notes_model.Note(got.title, got.description, notes_model.CLOSED, got.author, got.date,
                                       guid=got.guid)
            notes_model.save([changed, theirs], other, "Casa")
            found = notes_model.load(other)

            def merge(d):
                mine = {n.guid: k for k, n in enumerate(d.notes)}
                for n in found:
                    if n.guid in mine:
                        d.notes[mine[n.guid]] = n
                    else:
                        d.notes.append(n)
            again.change_notes("Importar", merge)
            self.assertEqual([(n.title, n.closed) for n in again.notes],
                             [("Parede a mais", True), ("Pilar fora do eixo", False)])
            with self.assertRaises(ValueError):
                notes_model.load(os.path.join(tmp, "notas.arqbim"))           # not a BCF


class IdsCheck(unittest.TestCase):
    """The model checked against an IDS (Phase 4, step 2), with ifctester."""

    def test_example_requirements(self):
        from arqbim.ifc import ids as ids_check
        from arqbim.i18n import ids_reason
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exemplos",
                            "requisitos_exemplo.ids")
        doc = Document()
        wall = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        door = bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, wall), 1.0, -1)
        bim.add_slab(doc, (0, 0, 0), 5, 4, catalog.BY_KEY["laje_12"])
        title, reqs = ids_check.check(doc.ifc, path)
        self.assertEqual(title, "Requisitos de exemplo (ArqBIM)")
        self.assertEqual([(r.name, r.status, r.applicable) for r in reqs],
                         [("Paredes: exterior ou interior", True, 1), ("Paredes com nome", True, 1),
                          ("Portas: resistência ao fogo", False, 1), ("Lajes com material", True, 1)])
        guid, label, reason = reqs[2].failures[0]
        self.assertEqual((guid, label), (door, "Porta 1 — IfcDoor"))
        self.assertEqual(ids_reason(reason), "Falta a propriedade pedida no conjunto")
        offered = {(ps, pr): kind for ps, pr, kind, _c in doc.ifc.property_templates(door)}
        self.assertEqual(offered.get(("Pset_DoorCommon", "FireRating")), "text")      # + Property… offers it
        bim.set_property(doc, door, "Pset_DoorCommon", "FireRating", "EI30")   # fixed: met
        _title, reqs = ids_check.check(doc.ifc, path)
        self.assertTrue(all(r.status for r in reqs))
        self.assertNotIn(("Pset_DoorCommon", "FireRating"),
                         {(ps, pr) for ps, pr, _k, _c in doc.ifc.property_templates(door)})
        acoustic = next(k for k in offered if k[0] != "Pset_DoorCommon")       # a set the door has not got yet
        kind = offered[acoustic]
        value = {"bool": True, "text": "x", "integer": 1, "number": 1.5, "length": 0.5}.get(kind, None)
        if kind == "choice":
            value = next(c for ps, pr, _k, c in doc.ifc.property_templates(door) if (ps, pr) == acoustic)[0]
        bim.set_property(doc, door, acoustic[0], acoustic[1], value)             # its set is made
        self.assertIn(acoustic[0], ue.get_psets(doc.ifc.by_guid(door)))
        bim.set_property(doc, door, "Projeto", "Fornecedor", "Silva Lda")         # a property of one's own
        bim.set_property(doc, door, "Projeto", "Custo", 350.0)
        self.assertEqual({k: v for k, v in ue.get_psets(doc.ifc.by_guid(door))["Projeto"].items() if k != "id"},
                         {"Fornecedor": "Silva Lda", "Custo": 350.0})
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "nao_e_ids.ids")
            with open(bad, "w", encoding="utf-8") as f:
                f.write("<qualquer/>")
            with self.assertRaises(ids_check.IdsError):
                ids_check.check(doc.ifc, bad)


class DetailViews(unittest.TestCase):
    """0.133: a detail view of a house's corner (its plan, 1:20) and one of a section: the plan's drawing has
    its callout, the detail's only what is in its rectangle (the walls' cut there, the dimension inside, not the
    one outside), its extent its rectangle, at its scale; on a sheet; renamed / removed with its section; kept;
    undone."""

    def test_details(self):
        from arqbim.model import dimensions as dims
        from arqbim.model import drawings
        doc = Document()
        bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (10.0, 6.0, 0.0),
                                                       (0.0, 6.0, 0.0))], catalog.BY_KEY["parede_alv_20"])
        plan = ("plan", doc.active_storey)
        inside = dims.Dimension(plan, np.array((-0.1, -0.1, 0.0)), np.array((0.5, -0.1, 0.0)),
                                np.array((0.2, -0.5, 0.0)))
        outside = dims.Dimension(plan, np.array((5.0, -0.1, 0.0)), np.array((9.0, -0.1, 0.0)),
                                 np.array((7.0, -0.5, 0.0)))
        doc.execute(dims.ReplaceDimensions([], [inside, outside], "Cotas"))
        k = doc.add_detail(plan, (1.0, 1.0, -1.0, -1.0))
        detail = doc.details[k]
        self.assertEqual((detail.name, detail.rect, detail.scale), ("Pormenor 1", (-1.0, -1.0, 1.0, 1.0), 20))
        whole = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual(whole.callouts, [((-1.0, -1.0, 1.0, 1.0), "1")])
        part = drawings.of_view(doc, "detail", detail.uid, "Pormenor 1")
        lo, hi = part.bounds()
        self.assertTrue(np.allclose(lo, (-1.0, -1.0)) and np.allclose(hi, (1.0, 1.0)))
        self.assertTrue(part.cut and all(np.all(np.abs(np.asarray(r)) <= 1.0 + 1e-6) for r in part.cut))
        self.assertEqual(len(part.dims), 1)
        self.assertFalse(part.north or part.marks or part.callouts)
        self.assertEqual(doc.view_settings(("detail", detail.uid)).scale, 20)
        sheet = sheets.Sheet("P", views=[sheets.Placed("detail", detail.uid)])
        (frame,) = sheets.layout(sheet, [sheets.extent(part)], [20])
        self.assertAlmostEqual(frame.width, 100.0)                       # (2 m at 1:20)
        doc.add_section((5.0, 3.0, 0.0), (0.0, -1.0, 0.0))
        doc.add_detail(("section", doc.sections[0].name), (0.0, 0.0, 2.0, 3.0), 10)
        doc.put_on_sheet(None, "detail", doc.details[1].uid)
        doc.rename_section(0, "Corte A")
        self.assertEqual(doc.details[1].parent, ("section", "Corte A"))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "pormenores.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        self.assertEqual([(d.name, d.parent[0], d.rect, d.scale) for d in again.details],
                         [("Pormenor 1", "plan", (-1.0, -1.0, 1.0, 1.0), 20),
                          ("Pormenor 2", "section", (0.0, 0.0, 2.0, 3.0), 10)])
        doc.remove_section(0)
        self.assertEqual(len(doc.details), 1)
        self.assertEqual(doc.sheets[0].views, [])                        # (its detail went from the sheet)
        doc.undo()
        self.assertEqual(len(doc.details), 2)


class ServicesAboveTheCut(unittest.TestCase):
    """0.135 (the owner's test: «a conduta não apareceu»): a duct drawn 2,50 m up — above the plan's 1,20 m cut —
    is in the plan's drawing as its outline, dashed (on paper and in DXF); a pipe at 0,30 m is not (it is seen
    as before); a duct of another storey is not."""

    def test_duct_above(self):
        from arqbim.model import drawings, dxf
        doc = Document()
        bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        bim.add_segment(doc, np.array((1.0, 2.0, 0.0)), np.array((6.0, 2.0, 0.0)), catalog.BY_KEY["conduta_30x20"],
                        2.5, storey=doc.active_storey)
        bim.add_segment(doc, np.array((1.0, 4.0, 0.0)), np.array((6.0, 4.0, 0.0)), catalog.BY_KEY["tubo_50"], 0.3,
                        storey=doc.active_storey)
        upper = bim.add_storey(doc, "Piso 1", 3.0)
        bim.add_segment(doc, np.array((1.0, 5.0, 3.0)), np.array((6.0, 5.0, 3.0)), catalog.BY_KEY["conduta_30x20"],
                        5.5, storey=upper)
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual(len(plan.above), 1)
        ring = plan.above[0]
        self.assertTrue(np.allclose(sorted({round(float(x), 3) for x in ring[:, 0]}), (1.0, 6.0)))
        self.assertTrue(np.allclose(sorted({round(float(y), 3) for y in ring[:, 1]}), (1.85, 2.15)))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "planta.dxf")
            dxf.write(path, plan, 100)
            with open(path, encoding="cp1252") as f:
                self.assertIn("ACIMA", f.read())


class SlopesStacksAndRisers(unittest.TestCase):
    """0.136 (Phase 6, step 1, water and drainage): a pipe that falls along it (its slope in the Properties, in the
    plan as an arrow and "1 %"), a stack (vertical) with its collector going on from its foot through a bend, a
    riser between two runs (a bend at each end) — a rectangular duct's too, its section the right way round."""

    def connections(self, doc, guid):
        return [doc.ifc.connected(p) is not None for p in doc.ifc.ports(guid)]

    def test_a_sloped_pipe(self):
        from arqbim.model import drawings, dxf
        doc = Document()
        pipe = bim.add_segment(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["tubo_100"],
                               0.30, storey=doc.active_storey, end_z=0.26)              # 1 %
        s, e, z = doc.ifc.segment_params(pipe)
        np.testing.assert_allclose(s, (0.0, 0.0, 0.30), atol=1e-9)
        np.testing.assert_allclose(e, (4.0, 0.0, 0.26), atol=1e-9)
        p = doc.ifc.describe(pipe)["params"]
        self.assertAlmostEqual(p["length"], math.hypot(4.0, 0.04))
        self.assertAlmostEqual(p["slope"], 0.01)
        self.assertAlmostEqual(p["end_z"], 0.26)
        self.assertFalse(p["vertical"])
        lo, hi = bounds(doc, pipe)
        self.assertAlmostEqual(float(lo[2]), 0.26 - 0.05, delta=2e-3)
        self.assertAlmostEqual(float(hi[2]), 0.30 + 0.05, delta=2e-3)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.resize_segment(doc, pipe, length=math.hypot(5.0, 0.05))              # longer: along its slope
        np.testing.assert_allclose(doc.ifc.segment_params(pipe)[1], (5.0, 0.0, 0.25), atol=1e-9)
        doc.undo()
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual(len(plan.slopes), 1)
        mid, down, text, radius = plan.slopes[0]
        np.testing.assert_allclose(mid, (2.0, 0.0), atol=1e-9)
        np.testing.assert_allclose(down, (1.0, 0.0), atol=1e-9)                   # (it falls towards its end)
        self.assertEqual(text, "1 %")
        self.assertAlmostEqual(radius, 0.05)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "planta.dxf")
            dxf.write(path, plan, 100)
            with open(path, encoding="cp1252") as f:
                self.assertIn("1 %", f.read())

    def test_a_stack_and_its_collector(self):
        doc = Document()
        spec = catalog.BY_KEY["tubo_100"]
        stack = bim.add_segment(doc, np.array((2.0, 2.0)), np.array((2.0, 2.0)), spec, 6.10,
                                storey=doc.active_storey, end_z=-0.30)        # from the roof down under the floor
        p = doc.ifc.describe(stack)["params"]
        self.assertTrue(p["vertical"])
        self.assertAlmostEqual(p["length"], 6.40)
        lo, hi = bounds(doc, stack)
        self.assertTrue(np.allclose(lo, (1.95, 1.95, -0.30), atol=2e-3) and np.allclose(hi, (2.05, 2.05, 6.10), atol=2e-3),
                        (lo, hi))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        found = doc.ifc.free_end_near((2.03, 2.0), "pipe", 0.30, 0.10)            # (its foot, whatever the height)
        self.assertEqual(found[0], stack)
        np.testing.assert_allclose(found[1], (2.0, 2.0, -0.30), atol=1e-9)
        self.assertIsNone(doc.ifc.free_end_near((2.5, 2.0), "pipe", 0.30, 0.10))
        collector = bim.add_segment(doc, np.array((2.0, 2.0)), np.array((6.0, 2.0)), spec, -0.30,
                                    storey=doc.active_storey, end_z=-0.34)    # found by the stack's foot
        bends = doc.ifc.file.by_type("IfcPipeFitting")
        self.assertEqual(len(bends), 1)
        self.assertEqual(self.connections(doc, stack), [False, True])
        self.assertEqual(self.connections(doc, collector), [True, False])
        cut = 0.10 * math.tan(math.acos(0.04 / math.hypot(4.0, 0.04)) / 2)        # R = Ø, at a little over 90°
        np.testing.assert_allclose(doc.ifc.segment_params(stack)[1], (2.0, 2.0, -0.30 + cut), atol=1e-6)
        bend = doc.get(bends[0].GlobalId)
        theta = math.acos(0.04 / math.hypot(4.0, 0.04))                         # (the turn: down, then along)
        self.assertAlmostEqual(bend.mesh.volume(), math.pi * 0.05 ** 2 * 0.10 * theta, delta=4e-5)   # Pappus
        lo, hi = (np.array(v) for v in bend.mesh.bounds())
        self.assertTrue(np.allclose(lo, (1.95, 1.95, -0.35), atol=3e-3) and np.allclose(hi[:2], (2.10, 2.05), atol=3e-3),
                        (lo, hi))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_a_riser(self):
        doc = Document()
        spec = catalog.BY_KEY["tubo_50"]
        a = bim.add_segment(doc, np.array((0.0, 0.0)), np.array((3.0, 0.0)), spec, 0.30, storey=doc.active_storey)
        b = bim.add_segment(doc, np.array((3.0, 0.0)), np.array((3.0, 0.0)), spec, 0.30, storey=doc.active_storey,
                            after=a, end_z=2.50)
        c = bim.add_segment(doc, np.array((3.0, 0.0)), np.array((3.0, 4.0)), spec, 2.50, storey=doc.active_storey,
                            after=b)
        self.assertEqual(doc.ifc.count("IfcPipeFitting"), 2)
        np.testing.assert_allclose(doc.ifc.segment_params(a)[1], (2.95, 0.0, 0.30), atol=1e-6)
        sb, eb, _z = doc.ifc.segment_params(b)
        np.testing.assert_allclose(sb, (3.0, 0.0, 0.35), atol=1e-6)
        np.testing.assert_allclose(eb, (3.0, 0.0, 2.45), atol=1e-6)
        np.testing.assert_allclose(doc.ifc.segment_params(c)[0], (3.0, 0.05, 2.50), atol=1e-6)
        self.assertEqual([self.connections(doc, g) for g in (a, b, c)], [[False, True], [True, True], [True, False]])
        low = min(doc.ifc.file.by_type("IfcPipeFitting"), key=lambda f: doc.get(f.GlobalId).mesh.bounds()[0][2])
        lo, hi = (np.array(v) for v in doc.get(low.GlobalId).mesh.bounds())
        self.assertTrue(np.allclose(lo, (2.95, -0.025, 0.275), atol=2e-3) and np.allclose(hi, (3.025, 0.025, 0.35),
                                                                                         atol=2e-3), (lo, hi))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.resize_segment(doc, a, z=0.60)                                   # up: the whole run goes along
        np.testing.assert_allclose(doc.ifc.segment_params(c)[0], (3.0, 0.05, 2.80), atol=1e-6)

    def test_a_short_riser(self):
        """0.138: a riser of 12 cm (shorter than an edit may leave once its bends are in) is made, not refused."""
        doc = Document()
        spec = catalog.BY_KEY["tubo_50"]
        a = bim.add_segment(doc, np.array((0.0, 0.0)), np.array((3.0, 0.0)), spec, 0.30, storey=doc.active_storey)
        b = bim.add_segment(doc, np.array((3.0, 0.0)), np.array((3.0, 0.0)), spec, 0.30, storey=doc.active_storey,
                            after=a, end_z=0.42)
        c = bim.add_segment(doc, np.array((3.0, 0.0)), np.array((3.0, 2.0)), spec, 0.42, storey=doc.active_storey,
                            after=b)
        self.assertEqual(doc.ifc.count("IfcPipeFitting"), 1)                # (no room for the second bend)
        self.assertEqual([self.connections(doc, g) for g in (a, b, c)], [[False, True], [True, True], [True, False]])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_a_duct_riser_keeps_its_section(self):
        doc = Document()
        spec = catalog.BY_KEY["conduta_30x20"]
        a = bim.add_segment(doc, np.array((0.0, 0.0)), np.array((4.0, 0.0)), spec, 2.50, storey=doc.active_storey)
        up = bim.add_segment(doc, np.array((4.0, 0.0)), np.array((4.0, 0.0)), spec, 2.50, storey=doc.active_storey,
                             after=a, end_z=3.50)
        lo, hi = bounds(doc, up)                                             # 0,30 wide across, as the run
        self.assertTrue(np.allclose(lo[:2], (3.9, -0.15), atol=2e-3) and np.allclose(hi[:2], (4.1, 0.15), atol=2e-3),
                        (lo, hi))
        bend = doc.get(doc.ifc.file.by_type("IfcDuctFitting")[0].GlobalId)
        self.assertAlmostEqual(bend.mesh.volume(), 0.3 * 0.2 * 0.3 * math.pi / 2, delta=0.002)   # area × R × θ
        lo, hi = (np.array(v) for v in bend.mesh.bounds())
        self.assertTrue(np.allclose(lo, (3.7, -0.15, 2.4), atol=0.01) and np.allclose(hi, (4.1, 0.15, 2.8), atol=0.01),
                        (lo, hi))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class TeesAndReducers(unittest.TestCase):
    """0.137 (Phase 6, step 1): a branch that ends on the middle of a main — a sloped pipe, a stack — splits it and
    a tee is put in (three ports, all connected; the branch flowing into it); one that starts on a main (supply)
    flows out of it; a pipe going on in line with another size gets a reducer (a cone), a duct too (faceted)."""

    def connections(self, doc, guid):
        return [doc.ifc.connected(p) is not None for p in doc.ifc.ports(guid)]

    def pipes(self, doc):
        return [e.GlobalId for e in doc.ifc.file.by_type("IfcPipeSegment")]

    def fittings(self, doc, kind):
        return [e for e in doc.ifc.file.by_type("IfcPipeFitting") + doc.ifc.file.by_type("IfcDuctFitting")
                if ifcopenshell.util.element.get_predefined_type(e) == kind]

    def test_a_branch_into_a_main(self):
        doc = Document()
        main = bim.add_segment(doc, np.array((0.0, 0.0)), np.array((6.0, 0.0)), catalog.BY_KEY["tubo_100"], 0.30,
                               storey=doc.active_storey, end_z=0.24)                # 1 %
        bim.set_status(doc, [main], "EXISTING")
        branch = bim.add_segment(doc, np.array((3.0, 3.0)), np.array((3.0, 0.0)), catalog.BY_KEY["tubo_50"], 0.32,
                                 storey=doc.active_storey, end_z=0.27, tee=main)    # into it, at its height there
        tees = self.fittings(doc, "JUNCTION")
        self.assertEqual(len(tees), 1)
        self.assertEqual(len(self.pipes(doc)), 3)                                   # the main in two, the branch
        rest = next(g for g in self.pipes(doc) if g not in (main, branch))
        np.testing.assert_allclose(doc.ifc.segment_params(main)[1], (2.95, 0.0, 0.2705), atol=2e-3)
        s, e, _z = doc.ifc.segment_params(rest)
        np.testing.assert_allclose(s, (3.05, 0.0, 0.2695), atol=2e-3)
        np.testing.assert_allclose(e, (6.0, 0.0, 0.24), atol=1e-6)                  # (where the main ended)
        self.assertEqual(doc.status_of(rest), "EXISTING")                          # (its phase too)
        np.testing.assert_allclose(doc.ifc.segment_params(branch)[1][:2], (3.0, 0.075), atol=2e-3)
        tee = tees[0].GlobalId
        self.assertEqual(self.connections(doc, tee), [True, True, True])
        self.assertEqual([self.connections(doc, g) for g in (main, rest, branch)], [[False, True], [True, False],
                                                                                    [False, True]])
        self.assertEqual(doc.ifc.ports(tee)[2].FlowDirection, "SINK")              # (the branch flows in)
        lo, hi = (np.array(v) for v in doc.get(tee).mesh.bounds())
        self.assertTrue(np.allclose(lo, (2.95, -0.05, 0.22), atol=3e-3) and np.allclose(hi, (3.05, 0.075, 0.32),
                                                                                    atol=3e-3), (lo, hi))
        self.assertEqual(doc.ifc.describe(tee)["kind"], "fitting")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertEqual(self.pipes(doc), [main])
        np.testing.assert_allclose(doc.ifc.segment_params(main)[1], (6.0, 0.0, 0.24), atol=1e-6)
        self.assertEqual(self.connections(doc, main), [False, False])

    def test_a_branch_into_a_stack(self):
        doc = Document()
        spec = catalog.BY_KEY["tubo_100"]
        stack = bim.add_segment(doc, np.array((2.0, 2.0)), np.array((2.0, 2.0)), spec, 6.10, storey=doc.active_storey,
                                end_z=-0.30)
        collector = bim.add_segment(doc, np.array((2.0, 2.0)), np.array((6.0, 2.0)), spec, -0.30,
                                    storey=doc.active_storey, end_z=-0.34)
        branch = bim.add_segment(doc, np.array((4.0, 2.0)), np.array((2.0, 2.0)), catalog.BY_KEY["tubo_50"], 0.50,
                                 storey=doc.active_storey, tee=stack)
        tee = self.fittings(doc, "JUNCTION")[0].GlobalId
        rest = next(g for g in self.pipes(doc) if g not in (stack, collector, branch))
        np.testing.assert_allclose(doc.ifc.segment_params(stack)[1], (2.0, 2.0, 0.55), atol=1e-6)
        np.testing.assert_allclose(doc.ifc.segment_params(rest)[0], (2.0, 2.0, 0.45), atol=1e-6)
        np.testing.assert_allclose(doc.ifc.segment_params(branch)[1], (2.075, 2.0, 0.50), atol=1e-6)
        self.assertEqual(self.connections(doc, rest), [True, True])                # (on to the collector's bend)
        self.assertEqual(self.connections(doc, tee), [True, True, True])
        self.assertTrue(doc.ifc.describe(rest)["params"]["vertical"])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_a_branch_from_a_main(self):
        doc = Document()
        main = bim.add_segment(doc, np.array((0.0, 0.0)), np.array((6.0, 0.0)), catalog.BY_KEY["tubo_50"], 0.50,
                               storey=doc.active_storey)
        branch = bim.add_segment(doc, np.array((2.0, 0.0)), np.array((2.0, 2.0)), catalog.BY_KEY["tubo_25"], 0.50,
                                 storey=doc.active_storey, tee=main)                # (supply: out of it)
        tee = self.fittings(doc, "JUNCTION")[0].GlobalId
        np.testing.assert_allclose(doc.ifc.segment_params(branch)[0], (2.0, 0.05, 0.50), atol=1e-6)
        self.assertEqual(self.connections(doc, branch), [True, False])
        self.assertEqual(doc.ifc.ports(tee)[2].FlowDirection, "SOURCE")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_reducers(self):
        doc = Document()
        a = bim.add_segment(doc, np.array((0.0, 0.0)), np.array((3.0, 0.0)), catalog.BY_KEY["tubo_100"], 0.30,
                            storey=doc.active_storey)
        b = bim.add_segment(doc, np.array((3.0, 0.0)), np.array((6.0, 0.0)), catalog.BY_KEY["tubo_50"], 0.30,
                            storey=doc.active_storey, after=a)
        reducers = self.fittings(doc, "TRANSITION")
        self.assertEqual(len(reducers), 1)
        np.testing.assert_allclose(doc.ifc.segment_params(a)[1], (2.9375, 0.0, 0.30), atol=1e-6)
        np.testing.assert_allclose(doc.ifc.segment_params(b)[0], (3.0625, 0.0, 0.30), atol=1e-6)
        cone = math.pi * 0.125 / 3 * (0.05 ** 2 + 0.05 * 0.025 + 0.025 ** 2)
        self.assertAlmostEqual(doc.get(reducers[0].GlobalId).mesh.volume(), cone, delta=0.04 * cone)
        self.assertEqual(self.connections(doc, reducers[0].GlobalId), [True, True])
        self.assertEqual([self.connections(doc, g) for g in (a, b)], [[False, True], [True, False]])
        c = bim.add_segment(doc, np.array((0.0, 3.0)), np.array((4.0, 3.0)), catalog.BY_KEY["conduta_50x30"], 2.5,
                            storey=doc.active_storey)
        bim.add_segment(doc, np.array((4.0, 3.0)), np.array((8.0, 3.0)), catalog.BY_KEY["conduta_30x20"], 2.5,
                        storey=doc.active_storey, after=c)
        duct = [e for e in self.fittings(doc, "TRANSITION") if e.is_a("IfcDuctFitting")]
        self.assertEqual(len(duct), 1)
        length = 1.5 * 0.20 + 0.05                                  # (by the larger change, the width's)
        frustum = length * (0.15 - 0.11 / 2 + 0.02 / 3)             # (its section shrinks evenly, both ways)
        self.assertAlmostEqual(doc.get(duct[0].GlobalId).mesh.volume(), frustum, places=6)
        lo, hi = (np.array(v) for v in doc.get(duct[0].GlobalId).mesh.bounds())
        self.assertTrue(np.allclose(lo, (4.0 - length / 2, 2.75, 2.35)) and np.allclose(hi, (4.0 + length / 2, 3.25, 2.65)),
                        (lo, hi))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class AirTerminals(unittest.TestCase):
    """0.138 (Phase 6, step 2, HVAC): round ducts; a diffuser in the ceiling (IfcAirTerminal, its port on top of its
    neck); a duct drawn to it comes down to it (a bend) and is connected; a return grille starts a duct (up from
    it); moved, its port goes along."""

    def test_a_diffuser_and_its_duct(self):
        doc = Document()
        diffuser = bim.add_air_terminal(doc, (3.0, 3.0), "diffuser_60")
        e = doc.ifc.by_guid(diffuser)
        self.assertEqual((e.is_a(), ifcopenshell.util.element.get_predefined_type(e)), ("IfcAirTerminal", "DIFFUSER"))
        info = doc.ifc.describe(diffuser)
        self.assertEqual((info["kind"], info["params"]["terminal"], info["params"]["air"]),
                         ("air_terminal", "diffuser_60", "supply"))
        lo, hi = bounds(doc, diffuser)
        self.assertTrue(np.allclose(lo, (2.7025, 2.7025, 2.595), atol=1e-3) and
                        np.allclose(hi, (3.2975, 3.2975, 2.785), atol=1e-3), (lo, hi))      # its face and neck
        port, at = doc.ifc.free_port(diffuser)
        self.assertEqual((port.PredefinedType, port.FlowDirection), ("DUCT", "SINK"))
        np.testing.assert_allclose(at, (3.0, 3.0, 2.785), atol=1e-6)
        self.assertEqual(doc.ifc.free_port_near((3.2, 3.1), 0.1)[0], diffuser)             # (on its face)
        self.assertIsNone(doc.ifc.free_port_near((3.5, 3.0), 0.1))
        spec = catalog.BY_KEY["conduta_d200"]
        duct = bim.add_segment(doc, np.array((0.0, 3.0)), np.array((3.0, 3.0)), spec, 3.0, storey=doc.active_storey,
                               to_port=diffuser)
        common = ifcopenshell.util.element.get_psets(ifcopenshell.util.element.get_type(doc.ifc.by_guid(duct)))
        self.assertEqual(common["Pset_DuctSegmentTypeCommon"]["Shape"], "ROUND")
        drops = [g.GlobalId for g in doc.ifc.file.by_type("IfcDuctSegment") if g.GlobalId != duct]
        self.assertEqual(len(drops), 1)
        self.assertTrue(doc.ifc.describe(drops[0])["params"]["vertical"])
        np.testing.assert_allclose(doc.ifc.segment_params(drops[0])[1], (3.0, 3.0, 2.785), atol=1e-6)
        self.assertEqual(doc.ifc.count("IfcDuctFitting"), 1)                               # (the bend down)
        self.assertIsNone(doc.ifc.free_port(diffuser))                                    # connected
        self.assertEqual(doc.ifc.describe(diffuser)["connections"], [doc.get(drops[0]).name])
        self.assertIsNone(doc.ifc.free_port_near((3.0, 3.0), 0.1))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertIsNotNone(doc.ifc.free_port(diffuser))

    def test_a_return_grille_starts_a_duct(self):
        doc = Document()
        grille = bim.add_air_terminal(doc, (2.0, 2.0), "grille_60x30")
        port, at = doc.ifc.free_port(grille)
        self.assertEqual(port.FlowDirection, "SOURCE")                                    # (the air goes out to it)
        rise = bim.add_segment(doc, at[:2], at[:2], catalog.BY_KEY["conduta_30x20"], float(at[2]),
                               storey=doc.active_storey, end_z=3.10, from_port=grille)
        self.assertIsNone(doc.ifc.free_port(grille))
        self.assertEqual([doc.ifc.connected(p) is not None for p in doc.ifc.ports(rise)], [True, False])
        bim.transform_objects(doc, [grille], translation((1.0, 0.0, 0.0)), "Mover")
        self.assertTrue(np.allclose(doc.ifc._placement_si(port)[:3, 3], at + (1.0, 0.0, 0.0), atol=1e-6))   # (along)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class HvacEquipment(unittest.TestCase):
    """0.139 (Phase 6, step 2, HVAC): units placed by a click (IfcUnitaryEquipment) with their ports — a ducted unit's
    on its ends (a duct starts from its supply, level; one drawn to its return comes down a little out from it and
    goes in level), an AHU's on top (a duct comes down to it); turned, its ports turn with it."""

    def test_a_ducted_unit_and_its_ducts(self):
        doc = Document()
        unit = bim.add_equipment(doc, (5.0, 3.0), "ducted_unit")
        e = doc.ifc.by_guid(unit)
        self.assertEqual((e.is_a(), ifcopenshell.util.element.get_predefined_type(e)),
                         ("IfcUnitaryEquipment", "AIRCONDITIONINGUNIT"))
        lo, hi = bounds(doc, unit)
        self.assertTrue(np.allclose(lo, (4.5, 2.65, 2.60)) and np.allclose(hi, (5.5, 3.35, 2.87)), (lo, hi))
        ports = {p.Name: p for p in doc.ifc.ports(unit)}
        self.assertEqual(sorted(ports), ["condensate", "gas", "liquid", "return", "supply"])   # (refrigerant: 0.196)
        self.assertEqual((ports["supply"].PredefinedType, ports["supply"].FlowDirection), ("DUCT", "SOURCE"))
        self.assertEqual(ports["condensate"].PredefinedType, "PIPE")
        np.testing.assert_allclose(doc.ifc._placement_si(ports["supply"])[:3, 3], (5.5, 3.0, 2.735), atol=1e-6)
        np.testing.assert_allclose(doc.ifc.port_way(ports["supply"]), (1.0, 0.0, 0.0), atol=1e-9)
        info = doc.ifc.describe(unit)
        self.assertEqual((info["kind"], info["params"]["equipment"]), ("equipment", "ducted_unit"))
        spec = catalog.BY_KEY["conduta_30x20"]
        supply = bim.add_segment(doc, np.array((5.5, 3.0)), np.array((8.0, 3.0)), spec, 2.735,
                                 storey=doc.active_storey, from_port=unit)                 # (from its supply)
        self.assertIsNotNone(doc.ifc.connected(ports["supply"]))
        self.assertIsNone(doc.ifc.connected(ports["return"]))
        before = len(doc.ifc.file.by_type("IfcDuctSegment"))
        bim.add_segment(doc, np.array((1.0, 3.0)), np.array((4.5, 3.0)), spec, 3.0, storey=doc.active_storey,
                        to_port=unit)                                                     # (to its return)
        self.assertEqual(len(doc.ifc.file.by_type("IfcDuctSegment")), before + 3)        # along, down, in
        self.assertIsNotNone(doc.ifc.connected(ports["return"]))
        inn = doc.ifc.owner_of(doc.ifc.connected(ports["return"])).GlobalId
        s, e2, _z = doc.ifc.segment_params(inn)
        np.testing.assert_allclose(e2, (4.5, 3.0, 2.735), atol=1e-6)                     # level, in to it
        self.assertAlmostEqual(float(s[2]), 2.735)
        self.assertNotEqual(inn, supply)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        turned = bim.add_equipment(doc, (8.0, 8.0), "ducted_unit", angle=90.0)
        supply2 = next(p for p in doc.ifc.ports(turned) if p.Name == "supply")
        np.testing.assert_allclose(doc.ifc._placement_si(supply2)[:3, 3], (8.0, 8.5, 2.735), atol=1e-6)
        np.testing.assert_allclose(doc.ifc.port_way(supply2), (0.0, 1.0, 0.0), atol=1e-9)

    def test_an_ahu_with_its_ducts_on_top(self):
        doc = Document()
        ahu = bim.add_equipment(doc, (3.0, 3.0), "ahu")
        lo, hi = bounds(doc, ahu)
        self.assertTrue(np.allclose(lo, (2.0, 2.5, 0.0)) and np.allclose(hi, (4.0, 3.5, 1.2)), (lo, hi))
        spec = catalog.BY_KEY["conduta_d250"]
        bim.add_segment(doc, np.array((8.0, 3.0)), np.array((3.6, 3.0)), spec, 2.8, storey=doc.active_storey,
                        to_port=ahu)                                                       # (down to its supply)
        supply = next(p for p in doc.ifc.ports(ahu) if p.Name == "supply")
        down = doc.ifc.owner_of(doc.ifc.connected(supply)).GlobalId
        self.assertTrue(doc.ifc.describe(down)["params"]["vertical"])
        np.testing.assert_allclose(doc.ifc.segment_params(down)[1], (3.6, 3.0, 1.2), atol=1e-6)
        self.assertIsNone(doc.ifc.connected(next(p for p in doc.ifc.ports(ahu) if p.Name == "return")))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class SanitaryFixtures(unittest.TestCase):
    """0.140 (Phase 6, step 3): sanitary fixtures made by the program (IfcSanitaryTerminal), their back against a
    wall, with their connections (the drain, cold and hot water: their system, their flow, the way their pipe goes)
    and the free zone in front, dashed in the plan; a pipe drawn to a basin's drain comes in to it, connected."""

    def test_a_wc_against_a_wall(self):
        from arqbim.model import drawings
        doc = Document()
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        wc = bim.add_fixture(doc, (2.0, 0.1), "wc", 0.0)
        e = doc.ifc.by_guid(wc)
        self.assertEqual((e.is_a(), ifcopenshell.util.element.get_predefined_type(e)), ("IfcSanitaryTerminal", "TOILETPAN"))
        lo, hi = bounds(doc, wc)
        self.assertTrue(np.allclose(lo, (1.81, 0.10, 0.0), atol=2e-3) and np.allclose(hi, (2.19, 0.78, 0.80), atol=2e-3),
                        (lo, hi))
        ports = {p.Name: p for p in doc.ifc.ports(wc)}
        self.assertEqual(sorted(ports), ["cold", "drain"])
        drain, cold = ports["drain"], ports["cold"]
        self.assertEqual((drain.PredefinedType, drain.SystemType, drain.FlowDirection), ("PIPE", "SEWAGE", "SOURCE"))
        self.assertEqual((cold.SystemType, cold.FlowDirection), ("DOMESTICCOLDWATER", "SINK"))
        np.testing.assert_allclose(doc.ifc._placement_si(drain)[:3, 3], (2.0, 0.1, 0.18), atol=1e-6)
        np.testing.assert_allclose(doc.ifc.port_way(drain), (0.0, -1.0, 0.0), atol=1e-9)      # (into the wall)
        np.testing.assert_allclose(doc.ifc._placement_si(cold)[:3, 3], (2.12, 0.1, 0.65), atol=1e-6)
        zone = np.array(doc.ifc.free_zones([wc])[wc])
        self.assertTrue(np.allclose(zone.min(axis=0)[:2], (1.6, 0.8)) and np.allclose(zone.max(axis=0)[:2], (2.4, 1.5)))
        info = doc.ifc.describe(wc)
        self.assertEqual((info["kind"], info["params"]["fixture"]), ("fixture", "wc"))
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual(len(plan.zones), 1)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_a_basin_and_its_drain(self):
        doc = Document()
        basin = bim.add_fixture(doc, (2.0, 0.0), "basin", 90.0)                      # (its X along +y: facing -x)
        drain = next(p for p in doc.ifc.ports(basin) if p.Name == "drain")
        at = doc.ifc._placement_si(drain)[:3, 3]
        np.testing.assert_allclose(at, (2.0, 0.0, 0.55), atol=1e-6)
        np.testing.assert_allclose(doc.ifc.port_way(drain), (1.0, 0.0, 0.0), atol=1e-9)
        self.assertEqual(doc.ifc.free_port_near(at[:2], 0.1, classes=("IfcSanitaryTerminal",), system="PIPE")[0], basin)
        pipe = bim.add_segment(doc, np.array((2.6, 3.0)), np.array((2.0, 0.0)), catalog.BY_KEY["tubo_50"], 0.40,
                               storey=doc.active_storey, to_port=basin)
        self.assertIsNotNone(doc.ifc.connected(drain))
        inn = doc.ifc.owner_of(doc.ifc.connected(drain)).GlobalId
        np.testing.assert_allclose(doc.ifc.segment_params(inn)[1], (2.0, 0.0, 0.55), atol=1e-6)    # (in, level)
        self.assertNotEqual(inn, pipe)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class ServiceSystems(unittest.TestCase):
    """0.141 (Phase 6): the systems — a run drawn in one (sewage) is in it, its bend too (IfcDistributionSystem,
    its ports' SystemType); another system is another group; the whole run moved to another system (the empty one
    goes); a tee takes its main's system, the branch keeps its own; a fixture's drain says which system."""

    def test_runs_in_their_systems(self):
        from arqbim.ifc.systems import SYSTEMS
        doc = Document()
        spec = catalog.BY_KEY["tubo_100"]
        a = bim.add_segment(doc, np.array((0.0, 0.0)), np.array((4.0, 0.0)), spec, 0.30, storey=doc.active_storey,
                            end_z=0.26, system="sewage")
        b = bim.add_segment(doc, np.array((4.0, 0.0)), np.array((4.0, 3.0)), spec, 0.26, storey=doc.active_storey,
                            end_z=0.23, after=a, system="sewage")
        bend = doc.ifc.file.by_type("IfcPipeFitting")[0].GlobalId
        self.assertEqual([doc.ifc.system_of(g) for g in (a, b, bend)], ["sewage"] * 3)
        systems = doc.ifc.file.by_type("IfcDistributionSystem")
        self.assertEqual([(s.Name, s.PredefinedType) for s in systems], [("Águas negras", "SEWAGE")])
        self.assertEqual({p.SystemType for g in (a, b, bend) for p in doc.ifc.ports(g)}, {"SEWAGE"})
        cold = bim.add_segment(doc, np.array((0.0, 2.0)), np.array((3.0, 2.0)), catalog.BY_KEY["tubo_25"], 0.60,
                               storey=doc.active_storey, system="cold")
        self.assertEqual(doc.ifc.system_of(cold), "cold")
        self.assertEqual(len(doc.ifc.file.by_type("IfcDistributionSystem")), 2)
        self.assertEqual(doc.ifc.describe(a)["system"], "sewage")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.set_system(doc, b, "waste")                                      # (the whole run)
        self.assertEqual([doc.ifc.system_of(g) for g in (a, b, bend)], ["waste"] * 3)
        self.assertEqual(sorted(s.PredefinedType for s in doc.ifc.file.by_type("IfcDistributionSystem")),
                         ["DOMESTICCOLDWATER", "WASTEWATER"])               # (the empty one went)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertEqual(doc.ifc.system_of(a), "sewage")
        self.assertTrue(SYSTEMS["sewage"][4] and not SYSTEMS["cold"][4])    # (a drain falls)

    def test_a_tee_takes_its_mains_system(self):
        doc = Document()
        main = bim.add_segment(doc, np.array((0.0, 0.0)), np.array((6.0, 0.0)), catalog.BY_KEY["tubo_100"], 0.30,
                               storey=doc.active_storey, end_z=0.24, system="sewage")
        branch = bim.add_segment(doc, np.array((3.0, 3.0)), np.array((3.0, 0.0)), catalog.BY_KEY["tubo_50"], 0.32,
                                 storey=doc.active_storey, end_z=0.27, tee=main, system="waste")
        tee = doc.ifc.file.by_type("IfcPipeFitting")[0].GlobalId
        rest = next(e.GlobalId for e in doc.ifc.file.by_type("IfcPipeSegment") if e.GlobalId not in (main, branch))
        self.assertEqual([doc.ifc.system_of(g) for g in (main, rest, tee, branch)], ["sewage", "sewage", "sewage",
                                                                                     "waste"])
        wc = bim.add_fixture(doc, (1.0, 2.0), "wc", 0.0)
        drain = next(p for p in doc.ifc.ports(wc) if p.Name == "drain")
        self.assertEqual(doc.ifc.port_system(drain), "sewage")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class ConnectToNetwork(unittest.TestCase):
    """0.142 (Phase 6, step 3: «ligar à rede, ramal automático»): a WC's drain gets its branch to the sewage collector
    (out of the wall, down, then at 2 %, a tee on it) and its cold water inlet from the cold water pipe (up from it,
    across, a tee); a washbasin's drain to a waste-water stack; outlets with no network for them are told."""

    def test_a_wc(self):
        doc = Document()
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        collector = bim.add_segment(doc, np.array((0.0, -0.6)), np.array((6.0, -0.6)), catalog.BY_KEY["tubo_100"],
                                    -0.30, storey=doc.active_storey, end_z=-0.36, system="sewage")
        cold = bim.add_segment(doc, np.array((0.0, -0.3)), np.array((6.0, -0.3)), catalog.BY_KEY["tubo_25"], 0.40,
                               storey=doc.active_storey, system="cold")
        wc = bim.add_fixture(doc, (2.0, 0.1), "wc", 0.0)
        report = bim.connect_to_network(doc, [wc])
        self.assertEqual(sorted((name, key, main) for _g, name, key, main in report),
                         [("cold", "cold", cold), ("drain", "sewage", collector)])
        self.assertTrue(all(doc.ifc.connected(p) is not None for p in doc.ifc.ports(wc)))
        tees = [e for e in doc.ifc.file.by_type("IfcPipeFitting") if ifcopenshell.util.element.get_predefined_type(e)
                == "JUNCTION"]
        self.assertEqual(len(tees), 2)
        drain = next(p for p in doc.ifc.ports(wc) if p.Name == "drain")
        branch = doc.ifc.run_of(doc.ifc.owner_of(doc.ifc.connected(drain)).GlobalId)
        pipes = [g for g in branch if doc.ifc.by_guid(g).is_a("IfcPipeSegment")]
        self.assertTrue(any(doc.ifc.describe(g)["params"]["vertical"] for g in pipes))          # (down first)
        sloped = [doc.ifc.describe(g)["params"]["slope"] for g in pipes if not doc.ifc.describe(g)["params"]["vertical"]
                  and abs(doc.ifc.describe(g)["params"]["slope"]) > 1e-6]
        self.assertTrue(any(abs(s - 0.02) < 1e-3 for s in sloped), sloped)                    # (then at 2 %)
        self.assertEqual({doc.ifc.system_of(g) for g in branch if g != collector}, {"sewage"})
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertTrue(all(doc.ifc.connected(p) is None for p in doc.ifc.ports(wc)))

    def test_a_basin_to_a_stack(self):
        doc = Document()
        stack = bim.add_segment(doc, np.array((3.0, -0.4)), np.array((3.0, -0.4)), catalog.BY_KEY["tubo_100"], 3.0,
                                storey=doc.active_storey, end_z=-0.30, system="waste")
        basin = bim.add_fixture(doc, (3.0, 0.1), "basin", 0.0)
        report = {name: main for _g, name, _key, main in bim.connect_to_network(doc)}         # (every one there)
        self.assertEqual(report, {"drain": stack, "cold": None, "hot": None})                 # (no water pipes)
        tee = next(e for e in doc.ifc.file.by_type("IfcPipeFitting")
                   if ifcopenshell.util.element.get_predefined_type(e) == "JUNCTION").GlobalId
        z = float(doc.ifc.placement(tee)[2, 3])
        self.assertAlmostEqual(z, 0.55 - 0.02 * 0.4, delta=0.06)                               # (its height: at 2 %)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_drain_wye(self):
        """0.200: a WC's drain meets the collector at 45°, pointing down it (a wye, «Forquilha»), a leg downstream of
        the square point; its water inlet keeps a square tee; on a stack, square as before."""
        doc = Document()
        bim.add_segment(doc, np.array((0.0, -0.6)), np.array((6.0, -0.6)), catalog.BY_KEY["tubo_100"], -0.30,
                        storey=doc.active_storey, end_z=-0.36, system="sewage")
        bim.add_segment(doc, np.array((0.0, -0.3)), np.array((6.0, -0.3)), catalog.BY_KEY["tubo_25"], 0.40,
                        storey=doc.active_storey, system="cold")
        wc = bim.add_fixture(doc, (2.0, 0.1), "wc", 0.0)
        bim.connect_to_network(doc, [wc])
        junctions = {e.Name: e for e in doc.ifc.file.by_type("IfcPipeFitting")
                     if ifcopenshell.util.element.get_predefined_type(e) == "JUNCTION"}
        self.assertEqual(sorted(junctions), ["Forquilha 1", "Tê 1"])
        wye = junctions["Forquilha 1"]
        at = doc.ifc.placement(wye.GlobalId)[:3, 3]
        self.assertAlmostEqual(float(at[0]), 2.0 + 0.25, delta=0.01)                  # (downstream: the main falls to +x)
        self.assertAlmostEqual(float(at[1]), -0.6, places=6)
        self.assertEqual(ifcopenshell.util.element.get_type(wye).Name, "Forquilha — Tubo PVC Ø100")
        ports = doc.ifc.ports(wye.GlobalId)
        self.assertTrue(all(doc.ifc.connected(p) is not None for p in ports))
        way = doc.ifc.port_way(ports[2])
        cos = abs(float(np.dot(way[:2] / np.linalg.norm(way[:2]), (1.0, 0.0))))
        self.assertAlmostEqual(cos, np.cos(np.radians(45.0)), delta=0.02)            # (its branch at 45°)
        drain = next(p for p in doc.ifc.ports(wc) if p.Name == "drain")
        branch = doc.ifc.run_of(doc.ifc.owner_of(doc.ifc.connected(drain)).GlobalId)
        on_main = lambda g: all(abs(float(q[1]) + 0.6) < 1e-6 for q in doc.ifc.segment_params(g)[:2])  # noqa: E731
        sloped = [doc.ifc.describe(g)["params"]["slope"] for g in branch if doc.ifc.by_guid(g).is_a("IfcPipeSegment")
                  and not on_main(g) and not doc.ifc.describe(g)["params"]["vertical"]]
        self.assertTrue(sloped and all(abs(abs(s) - 0.02) < 2e-3 for s in sloped if abs(s) > 1e-6), sloped)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_round_a_column_and_a_footing(self):
        """0.199: a column stands between the cold water pipe and the WC, a pad footing between the WC and the
        sewage collector: both branches go round them with square bends, none of their pipes through them."""
        from arqbim.core import routing
        doc = Document()
        collector = bim.add_segment(doc, np.array((0.0, -1.6)), np.array((6.0, -1.6)), catalog.BY_KEY["tubo_100"],
                                    -0.30, storey=doc.active_storey, end_z=-0.36, system="sewage")
        cold = bim.add_segment(doc, np.array((0.0, -1.5)), np.array((6.0, -1.5)), catalog.BY_KEY["tubo_25"], 0.40,
                               storey=doc.active_storey, system="cold")
        bim.add_column(doc, np.array((2.0, -0.8, 0.0)), catalog.BY_KEY["pilar_30"], height=3.0)
        bim.add_footing(doc, (np.array((2.0, -0.8)), np.array((1.0, 0.0, 0.0)), 0.8, 0.8, -0.10),
                        catalog.BY_KEY["sapata_80"])
        wc = bim.add_fixture(doc, (2.0, 0.1), "wc", 0.0)
        report = bim.connect_to_network(doc, [wc])
        self.assertEqual(sorted((name, key, main) for _g, name, key, main in report),
                         [("cold", "cold", cold), ("drain", "sewage", collector)])
        self.assertTrue(all(doc.ifc.connected(p) is not None for p in doc.ifc.ports(wc)))
        column = [np.array(((1.85, -0.95), (2.15, -0.95), (2.15, -0.65), (1.85, -0.65)))]
        footing = [np.array(((1.6, -1.2), (2.4, -1.2), (2.4, -0.4), (1.6, -0.4)))]
        moved = 0
        for e in doc.ifc.file.by_type("IfcPipeSegment"):
            s, end, _z = doc.ifc.segment_params(e.GlobalId)
            lo, hi = sorted((float(s[2]), float(end[2])))
            if hi > 0.0:
                self.assertFalse(routing.blocked(s, end, column), e.Name)            # (not through the column)
            if lo < -0.10 and hi > -0.50:
                self.assertFalse(routing.blocked(s, end, footing), e.Name)           # (nor through the footing)
            moved += abs(float(s[0]) - 2.0) > 0.2 or abs(float(end[0]) - 2.0) > 0.2
        self.assertGreaterEqual(moved, 2)                                            # (round them, to one side)
        bends = [e for e in doc.ifc.file.by_type("IfcPipeFitting") if ifcopenshell.util.element.get_predefined_type(e)
                 == "BEND"]
        self.assertGreaterEqual(len(bends), 6)
        self.assertEqual(len([e for e in doc.ifc.file.by_type("IfcPipeFitting")
                              if ifcopenshell.util.element.get_predefined_type(e) == "JUNCTION"]), 2)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class ElectricalPoints(unittest.TestCase):
    """0.143 (Phase 6, step 4): electrical points made by the program, against a wall at their usual heights —
    an outlet at 0,30 m, a switch at 1,10 m, the board — each with its cable's port; on the plan (and in DXF) their
    symbols, sized on paper."""

    def test_points_and_their_symbols(self):
        from arqbim.model import drawings, dxf
        doc = Document()
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        outlet = bim.add_point(doc, (1.0, 0.1), "outlet", 0.0)
        switch = bim.add_point(doc, (2.0, 0.1), "switch", 0.0)
        board = bim.add_point(doc, (3.0, 0.1), "board", 0.0)
        e = doc.ifc.by_guid(outlet)
        self.assertEqual((e.is_a(), ifcopenshell.util.element.get_predefined_type(e)), ("IfcOutlet", "POWEROUTLET"))
        lo, hi = bounds(doc, outlet)
        self.assertTrue(np.allclose(lo, (0.96, 0.10, 0.26), atol=1e-3) and np.allclose(hi, (1.04, 0.145, 0.34),
                                                                                     atol=1e-3), (lo, hi))
        port = doc.ifc.ports(outlet)[0]
        self.assertEqual((port.PredefinedType, port.SystemType, port.FlowDirection), ("CABLE", "ELECTRICAL", "SINK"))
        np.testing.assert_allclose(doc.ifc._placement_si(port)[:3, 3], (1.0, 0.1, 0.30), atol=1e-6)
        np.testing.assert_allclose(doc.ifc.port_way(port), (0.0, -1.0, 0.0), atol=1e-9)      # (into the wall)
        self.assertEqual(ifcopenshell.util.element.get_predefined_type(doc.ifc.by_guid(switch)), "TOGGLESWITCH")
        lo, hi = bounds(doc, switch)
        self.assertAlmostEqual(float(lo[2]), 1.06, places=3)
        self.assertEqual(doc.ifc.by_guid(board).is_a(), "IfcElectricDistributionBoard")
        self.assertEqual(doc.ifc.ports(board)[0].FlowDirection, "SOURCE")
        info = doc.ifc.describe(switch)
        self.assertEqual((info["kind"], info["params"]["point"]), ("electrical", "switch"))
        self.assertAlmostEqual(info["params"]["height"], 1.10)
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual(sorted(k for k, _b, _a in plan.points), ["board", "outlet", "switch"])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "planta.dxf")
            dxf.write(path, plan, 100)
            with open(path, encoding="cp1252") as f:
                self.assertIn("ELETRICIDADE", f.read())
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_symbols(self):
        from arqbim.ifc.electrical import point_symbol
        lines, solids = point_symbol("outlet", (1.0, 0.1, 0.0), 0.0, 0.1)
        pts = np.array([p for line in lines for p in line])
        self.assertTrue(np.all(pts[:, 1] >= 0.1 - 1e-9))                      # (in front of the wall, not in it)
        self.assertAlmostEqual(float(pts[:, 0].max() - pts[:, 0].min()), 0.4, places=6)   # (2 mm at 1:100, both ways)
        self.assertEqual(solids, [])
        _lines, solids = point_symbol("board", (3.0, 0.1, 0.0), 90.0, 0.1)
        self.assertEqual(len(solids), 1)


class CircuitsAndLoads(unittest.TestCase):
    """0.144 (Phase 6, step 4): circuits (IfcDistributionCircuit C1, C2…) of the selected points, their type from
    them, their power and current, the check (too many points, a current above the breaker, a thin cable); the load
    schedule (Tables ▸ Circuits); a circuit deleted, its points stay."""

    def test_circuits(self):
        from arqbim.model import schedules
        doc = Document()
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((8.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        board = bim.add_point(doc, (7.5, 0.1), "board", 0.0)
        outlets = [bim.add_point(doc, (0.5 + k, 0.1), "outlet", 0.0) for k in range(3)]
        switch = bim.add_point(doc, (4.0, 0.1), "switch", 0.0)
        light = bim.add_light(doc, (4.0, 2.0))
        c1 = bim.add_circuit(doc, outlets)
        c2 = bim.add_circuit(doc, [switch, light])
        r1, r2 = doc.ifc.circuit_report(c1), doc.ifc.circuit_report(c2)
        self.assertEqual((r1["name"], r1["kind"], r1["points"], r1["breaker"], r1["section"]),
                         ("C1", "outlets", 3, 16.0, 2.5))
        self.assertAlmostEqual(r1["power"], 900.0)
        self.assertAlmostEqual(r1["current"], 900.0 / 230.0)
        self.assertTrue(r1["ok"])
        self.assertEqual(r1["board"], board)
        self.assertEqual((r2["name"], r2["kind"], r2["power"]), ("C2", "lighting", 100.0))
        self.assertEqual(doc.ifc.circuit_of(light), c2)
        self.assertEqual([c.PredefinedType for c in doc.ifc.file.by_type("IfcDistributionCircuit")],
                         ["ELECTRICAL", "LIGHTING"])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        more = [bim.add_point(doc, (0.7 + 0.5 * k, 0.1), "outlet_double", 0.0) for k in range(6)]
        bim.add_circuit(doc, outlets + more, kind="outlets")              # (C3: they leave C1)
        self.assertEqual(doc.ifc.circuit_report(c1)["points"], 0)
        c3 = doc.ifc.circuit_of(more[0])
        r3 = doc.ifc.circuit_report(c3)
        self.assertEqual((r3["name"], r3["points"]), ("C3", 9))
        self.assertEqual(r3["why"], ["points"])                           # (9 on a circuit of outlets: 8 at most)
        bim.edit_circuit(doc, c3, breaker=10.0)
        self.assertEqual(sorted(doc.ifc.circuit_report(c3)["why"]), ["current", "points"])   # (3300 W at 10 A)
        bim.edit_circuit(doc, c3, breaker=32.0)
        self.assertIn("section", doc.ifc.circuit_report(c3)["why"])        # (2,5 mm² for 32 A: too thin)
        rows = schedules.rows(doc, "circuits")
        self.assertEqual([r["name"] for r in rows], ["C1", "C2", "C3"])
        self.assertEqual(schedules.text_of("power", rows[2]["power"]), "3300 W")
        self.assertEqual(schedules.text_of("section", 2.5), "2,5 mm²")
        self.assertEqual(schedules.text_of("current", 900.0 / 230.0), "3,91 A")
        self.assertEqual(schedules.editable("circuits", "breaker", rows[0]), "circuit_breaker")
        bim.remove_circuit(doc, c2)
        self.assertIsNone(doc.ifc.circuit_of(light))
        self.assertIsNotNone(doc.get(light))
        doc.undo()
        self.assertEqual(doc.ifc.circuit_of(light), c2)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class ElectricalProposal(unittest.TestCase):
    """0.145 (Phase 6, step 4: «perfis por tipo de sala»): a room's profile from its name; a bedroom with a door gets
    a light in its middle, a switch inside beside the door, its outlets along the walls away from the door and the
    corners, a data outlet; a kitchen its counter outlets; made in one step, tagged; taken away in one step."""

    def test_profiles(self):
        from arqbim.model import electrical_proposal as ep
        self.assertEqual([ep.profile_of(n) for n in ("Quarto 2", "Sala comum", "Cozinha", "WC suite", "Corredor",
                                                     "Arrumos")],
                         ["bedroom", "living", "kitchen", "bathroom", "corridor", "other"])

    def test_a_bedroom(self):
        from arqbim.model import electrical_proposal as ep
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (4.0, 3.0, 0.0),
                                                      (0.0, 3.0, 0.0))], spec)
        wall = next(o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcWall"
                    and abs(bounds(doc, o.id)[0][1] + 0.1) < 1e-6 and abs(bounds(doc, o.id)[1][1] - 0.1) < 1e-6)
        frame = bim.wall_frame(doc, wall)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, frame.x0 + 1.0, 1)
        bim.add_room(doc, (2.0, 1.5), "Quarto")
        proposal = bim.propose_electrical(doc)
        (_name, profile, counts, items), = proposal.values()
        self.assertEqual(profile, "bedroom")
        kinds = sorted(k for k, _p, _n in items)
        self.assertEqual(kinds, ["data_outlet", "light", "outlet", "outlet", "outlet", "switch"])
        light = next(p for k, p, _n in items if k == "light")
        np.testing.assert_allclose(light, (2.0, 1.5), atol=0.3)
        door = bim.door_places(doc, doc.active_storey)[0]
        switch = next((p, n) for k, p, n in items if k == "switch")
        gap = float(np.linalg.norm(switch[0] - door[0]))
        self.assertAlmostEqual(gap, door[1] / 2 + ep.SWITCH_BESIDE, delta=0.01)          # (beside the door)
        self.assertGreater(float(np.dot(switch[1], (2.0, 1.5) - switch[0])), 0)          # (facing the room)
        for k, p, _n in items:
            if k in ("outlet", "data_outlet"):
                self.assertGreater(float(np.linalg.norm(p - door[0])), door[1] / 2 + ep.KEEP_OFF - 1e-6)
        made = bim.apply_electrical_proposal(doc, proposal)
        self.assertEqual(len(made), 6)
        self.assertEqual(sorted(doc.ifc.tagged(ep.PROPOSAL)), sorted(made))
        self.assertEqual(doc.ifc.count("IfcOutlet"), 4)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        self.assertEqual(bim.remove_electrical_proposal(doc), 6)
        self.assertEqual(doc.ifc.count("IfcOutlet") + doc.ifc.count("IfcSwitchingDevice"), 0)
        doc.undo()
        self.assertEqual(doc.ifc.count("IfcOutlet"), 4)

    def test_a_kitchen(self):
        doc = Document()
        bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (3.0, 3.0, 0.0),
                                                      (0.0, 3.0, 0.0))], catalog.BY_KEY["parede_alv_20"])
        bim.add_room(doc, (1.5, 1.5), "Cozinha")
        (_name, profile, _c, items), = bim.propose_electrical(doc).values()
        self.assertEqual(profile, "kitchen")
        self.assertEqual(sum(1 for k, _p, _n in items if k == "outlet_counter"), 4)
        self.assertEqual(sum(1 for k, _p, _n in items if k == "switch"), 1)                # (no door: on a wall)


class Conduits(unittest.TestCase):
    """0.146 (Phase 6, step 4: «canalizações e ligação ao quadro»): conduits drawn as pipes (IfcCableCarrierSegment
    CONDUITSEGMENT, their bends IfcCableCarrierFitting); a circuit wired to its board — from the board to the nearest
    point, then on, up the wall, over the ceiling, down — every point connected, the conduits in the circuit, their
    length in the load schedule."""

    def test_a_conduit(self):
        doc = Document()
        spec = catalog.BY_KEY["tubo_vd20"]
        a = bim.add_segment(doc, np.array((0.0, 0.0)), np.array((3.0, 0.0)), spec, 2.75, storey=doc.active_storey)
        bim.add_segment(doc, np.array((3.0, 0.0)), np.array((3.0, 2.0)), spec, 2.75, storey=doc.active_storey, after=a)
        e = doc.ifc.by_guid(a)
        self.assertEqual((e.is_a(), ifcopenshell.util.element.get_predefined_type(e)),
                         ("IfcCableCarrierSegment", "CONDUITSEGMENT"))
        self.assertEqual(ifcopenshell.util.element.get_type(e).is_a(), "IfcCableCarrierSegmentType")
        q = ifcopenshell.util.element.get_psets(e)["Qto_CableCarrierSegmentBaseQuantities"]
        self.assertAlmostEqual(q["Length"] * doc.ifc.unit_scale, 2.98, places=6)        # (its bend: R = Ø)
        self.assertEqual({p.PredefinedType for p in doc.ifc.ports(a)}, {"CABLECARRIER"})
        bends = doc.ifc.file.by_type("IfcCableCarrierFitting")
        self.assertEqual([ifcopenshell.util.element.get_predefined_type(b) for b in bends], ["BEND"])
        self.assertEqual(doc.ifc.describe(a)["kind"], "conduit")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])

    def test_a_circuit_wired_to_its_board(self):
        from arqbim.model import schedules
        doc = Document()
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        board = bim.add_point(doc, (5.5, 0.1), "board", 0.0)
        outlets = [bim.add_point(doc, (float(x), 0.1), "outlet", 0.0) for x in (1, 2, 3)]
        circuit = bim.add_circuit(doc, outlets)
        made = bim.route_circuits(doc)
        self.assertEqual(list(made), [circuit])
        self.assertTrue(all(doc.ifc.connected(doc.ifc.ports(g)[0]) is not None for g in outlets + [board]))
        length = doc.ifc.conduit_length(circuit)
        self.assertTrue(17.0 < length < 18.0 + 1e-6, length)              # (1,25 + 2,5 + 2,45, then 2 × 5,9: bends off)
        self.assertEqual(len(doc.ifc.circuit_conduits(circuit)), 9)
        report = doc.ifc.circuit_report(circuit)
        self.assertEqual(report["points"], 3)                              # (the conduits are not points)
        self.assertAlmostEqual(report["conduit"], length)
        row = schedules.rows(doc, "circuits")[0]
        self.assertEqual(schedules.text_of("conduit", row["conduit"]), "{:.2f} m".format(length).replace(".", ","))
        self.assertEqual(bim.route_circuits(doc), {})                      # (wired already: none again)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertEqual(doc.ifc.circuit_conduits(circuit), [])


class ElectricalCheck(unittest.TestCase):
    """0.147 (Phase 6, step 4: «validação e quantidades»): what the check points out — no board, points in no
    circuit, a circuit not wired, a room with no light — gone as they are put right; the quantities (the points of
    each kind, the conduits' metres)."""

    def test_check_and_quantities(self):
        from arqbim.model import electrical_check, schedules
        doc = Document()
        bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (6.0, 4.0, 0.0),
                                                      (0.0, 4.0, 0.0))], catalog.BY_KEY["parede_alv_20"])
        bim.add_room(doc, (3.0, 2.0), "Sala")
        outlets = [bim.add_point(doc, (float(x), 0.1), "outlet", 0.0) for x in (1, 2)]
        storey = doc.active_storey
        what = lambda: sorted(w for w, _t, _g in electrical_check.problems(doc, storey))      # noqa: E731
        self.assertEqual(what(), ["loose", "no_board", "room_dark"])
        loose = next(g for w, _t, g in electrical_check.problems(doc, storey) if w == "loose")
        self.assertEqual(sorted(loose), sorted(outlets))
        bim.add_point(doc, (5.5, 0.1), "board", 0.0)
        circuit = bim.add_circuit(doc, outlets)
        self.assertEqual(what(), ["not_wired", "room_dark"])
        bim.route_circuits(doc)
        light = bim.add_light(doc, (3.0, 2.0))
        bim.add_circuit(doc, [light])
        self.assertEqual(what(), ["not_wired"])                          # (the light's circuit, C2, not wired yet)
        bim.route_circuits(doc)
        self.assertEqual(what(), [])
        rows = {r["item"]: r for r in schedules.rows(doc, "electrical")}
        self.assertEqual(rows["Tomada"]["count"], 2)
        self.assertEqual(rows["Quadro elétrico"]["count"], 1)
        self.assertEqual(rows["Luminárias"]["count"], 1)
        self.assertAlmostEqual(rows["Tubo VD Ø20"]["metres"],
                               sum(doc.ifc.conduit_length(g) for g, _n in doc.ifc.circuits()), places=6)
        self.assertEqual(rows["Circuitos"]["count"], 2)
        self.assertIsNotNone(circuit)


class WaterProposal(unittest.TestCase):
    """0.148 (Phase 6, step 5): a bathroom with a WC and a washbasin: the stack in the corner by the WC (sewage), the
    cold and hot water pipes along their wall, every outlet connected — to the proposal's pipes only; tagged; taken
    away in one step."""

    def test_a_bathroom(self):
        from arqbim.model import water_proposal as wp
        doc = Document()
        bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (4.0, 3.0, 0.0),
                                                      (0.0, 3.0, 0.0))], catalog.BY_KEY["parede_alv_20"])
        bim.add_room(doc, (2.0, 1.5), "WC")
        own = bim.add_segment(doc, np.array((0.5, 2.5)), np.array((3.5, 2.5)), catalog.BY_KEY["tubo_25"], 2.40,
                              storey=doc.active_storey, system="cold")          # (the user's: not to be joined)
        wc = bim.add_fixture(doc, (1.0, 0.1), "wc", 0.0)
        basin = bim.add_fixture(doc, (2.5, 0.1), "basin", 0.0)
        plan = bim.propose_water(doc)
        (p,) = plan.values()
        np.testing.assert_allclose(p["stack"], (0.25, 0.25), atol=1e-6)          # (the corner by the WC)
        self.assertTrue(p["sewage"])
        np.testing.assert_allclose(p["cold"][0], (0.3, 0.2), atol=1e-6)
        self.assertEqual(sorted(p["fixtures"]), sorted([wc, basin]))
        made = bim.apply_water_proposal(doc, plan)
        self.assertTrue(all(doc.ifc.connected(q) is not None for g in (wc, basin) for q in doc.ifc.ports(g)))
        self.assertEqual([doc.ifc.connected(q) for q in doc.ifc.ports(own)], [None, None])   # (left alone)
        self.assertEqual(len(doc.ifc.file.by_type("IfcPipeSegment")) - 1 - len([g for g in made if doc.ifc.by_guid(g)
                                                                                .is_a("IfcPipeSegment")]), 0)
        self.assertEqual(sorted(doc.ifc.tagged(wp.PROPOSAL, classes=bim.WATER_CLASSES)), sorted(made))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        self.assertEqual(bim.remove_water_proposal(doc), len(made))
        self.assertEqual([e.GlobalId for e in doc.ifc.file.by_type("IfcPipeSegment")], [own])
        doc.undo()
        self.assertTrue(all(doc.ifc.connected(q) is not None for q in doc.ifc.ports(wc)))


class Clashes(unittest.TestCase):
    """0.149 (Phase 6, step 6): a pipe through a beam clashes (the point between them); one under it does not; the
    pieces of one run (a bend) do not clash with each other; a duct across a pipe does; walls only when asked; the
    report page."""

    @staticmethod
    def box(lo, hi):
        from arqbim.core.mesh import TriMesh
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        v = np.array([(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)], float)
        tris = [(0, 2, 1), (1, 2, 3), (4, 5, 6), (5, 7, 6), (0, 1, 4), (1, 5, 4), (2, 6, 3), (3, 6, 7), (0, 4, 2),
                (2, 4, 6), (1, 3, 5), (3, 7, 5)]
        m = TriMesh(v, np.array(tris))
        return m.verts, m.tris

    def test_meshes(self):
        from arqbim.core import clash
        beam = self.box((0, -0.1, 2.4), (4, 0.1, 2.8))
        across = self.box((2, -1, 2.5), (2.1, 1, 2.6))                # (a thin bar through it)
        p = clash.clash(across, beam)
        self.assertIsNotNone(p)
        self.assertTrue(1.9 < p[0] < 2.2 and -0.2 < p[1] < 0.2, p)
        self.assertIsNone(clash.clash(self.box((0, -0.1, 2.0), (4, 0.1, 2.4)), beam))          # (touching under it)
        self.assertIsNone(clash.clash(self.box((0, 0.1, 2.4), (4, 0.3, 2.8)), beam))           # (beside it, touching)
        np.testing.assert_allclose(clash.clash(self.box((1, -0.05, 2.5), (1.2, 0.05, 2.6)), beam), (1.1, 0, 2.55))

    def test_disciplines(self):
        from arqbim.model import clashes
        doc = Document()
        beam = bim.add_beam(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["viga_20x40"], 2.80)
        through = bim.add_segment(doc, np.array((2.0, -2.0)), np.array((2.0, 2.0)), catalog.BY_KEY["tubo_100"], 2.60,
                                  storey=doc.active_storey)
        under = bim.add_segment(doc, np.array((0.5, 1.0)), np.array((5.5, 1.0)), catalog.BY_KEY["tubo_50"], 2.20,
                                storey=doc.active_storey)
        bim.add_segment(doc, np.array((5.5, 1.0)), np.array((5.5, 3.0)), catalog.BY_KEY["tubo_50"], 2.20,
                        storey=doc.active_storey, after=under)                 # (its bend: one run)
        found = clashes.find(doc)
        self.assertEqual([(c.a, c.b) for c in found if c.pair == ("services", "structure")], [(through, beam)])
        point = next(c.point for c in found if c.pair == ("services", "structure"))
        self.assertTrue(abs(point[0] - 2.0) < 0.1 and abs(point[1]) < 0.2, point)
        self.assertEqual([c for c in found if c.pair == ("services", "services")], [])
        duct = bim.add_segment(doc, np.array((4.0, -1.0)), np.array((4.0, 3.0)), catalog.BY_KEY["conduta_30x20"], 2.20,
                               storey=doc.active_storey)
        crossing = [c for c in clashes.find(doc) if c.pair == ("services", "services")]
        self.assertEqual([sorted((c.a, c.b)) for c in crossing], [sorted((duct, under))])
        wall = bim.add_wall(doc, np.array((3.0, -2.0, 0.0)), np.array((3.0, 3.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        self.assertFalse(any(wall in (c.a, c.b) for c in clashes.find(doc)))     # (walls: only when asked)
        with_walls = clashes.find(doc, clashes.PAIRS)
        self.assertTrue(any(c.b == wall and c.a == under for c in with_walls))
        page = clashes.report_html(doc, with_walls, "Conflitos")
        self.assertIn("<table>", page)
        self.assertIn(doc.get(beam).name, page)

    def test_statuses(self):
        """0.150: a clash new the first time, active after; approved stays approved; gone, it is resolved — kept with
        the project."""
        from arqbim.model import clashes
        doc = Document()
        beam = bim.add_beam(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["viga_20x40"], 2.80)
        a = bim.add_segment(doc, np.array((2.0, -2.0)), np.array((2.0, 2.0)), catalog.BY_KEY["tubo_100"], 2.60,
                            storey=doc.active_storey)
        b = bim.add_segment(doc, np.array((4.0, -2.0)), np.array((4.0, 2.0)), catalog.BY_KEY["tubo_100"], 2.60,
                            storey=doc.active_storey)

        def search():
            found = clashes.find(doc)
            doc.execute(clashes.SetClashStatus(clashes.updated_status(doc.clash_status, found), "Procurar"))
            return {c.key: doc.clash_status[c.key] for c in found}

        first = search()
        self.assertEqual(sorted(first.values()), ["new", "new"])
        key_a, key_b = "|".join(sorted((a, beam))), "|".join(sorted((b, beam)))
        self.assertEqual(search(), {key_a: "active", key_b: "active"})
        approved = dict(doc.clash_status, **{key_b: "approved"})
        doc.execute(clashes.SetClashStatus(approved, "Aprovar"))
        bim.resize_segment(doc, a, z=2.0)                                  # (lowered: under the beam)
        self.assertEqual(search(), {key_b: "approved"})
        self.assertEqual(doc.clash_status[key_a], "resolved")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "conflitos.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            self.assertEqual(again.clash_status, {key_a: "resolved", key_b: "approved"})
            geomcache.forget(path)
        doc.undo()                                                          # (the last search undone)
        self.assertEqual(doc.clash_status[key_a], "active")


class Terrains(unittest.TestCase):
    """0.155: a terrain through survey points — an IfcGeographicElement TERRAIN in the site (no storey), a closed
    triangulated solid, its material soil (hatched as earth when cut), valid IFC; its points read back; made again
    with one more point (one undo step); its contour lines in the ground floor's plan (none under a slab over it)
    and its cut hatched in a section; its interval and base changed."""

    def _points(self):
        return [(x, y, 10.0 + 0.1 * x + 0.05 * y) for x in (0.0, 10.0, 20.0, 30.0) for y in (0.0, 10.0, 20.0)]

    def test_terrain(self):
        import ifcopenshell.util.element as ue
        from arqbim.model import drawings
        doc = Document()
        guid = bim.add_terrain(doc, self._points())
        e = doc.ifc.by_guid(guid)
        self.assertEqual((e.is_a(), ue.get_predefined_type(e)), ("IfcGeographicElement", "TERRAIN"))
        self.assertTrue(ue.get_container(e).is_a("IfcSite"))
        self.assertIsNone(doc.get(guid).storey)
        self.assertEqual(doc.ifc.validate(), [])
        self.assertTrue(doc.get(guid).mesh.is_closed())
        self.assertEqual(doc.ifc.hatches([guid]).get(guid), "earth")
        np.testing.assert_allclose(sorted(map(tuple, doc.ifc.terrain_points(guid))), sorted(self._points()),
                                   atol=1e-6)
        info = doc.ifc.describe(guid)["params"]
        self.assertEqual((info["points"], round(info["area"], 6)), (12, 600.0))
        self.assertAlmostEqual(info["low"], 10.0)
        self.assertAlmostEqual(info["high"], 14.0)
        self.assertAlmostEqual(info["depth"], 1.0)
        # one more point, a hill in the middle: one undo step
        bim.set_terrain_points(doc, guid, list(self._points()) + [(15.0, 10.0, 16.0)])
        self.assertEqual(len(doc.ifc.terrain_points(guid)), 13)
        self.assertAlmostEqual(doc.ifc.terrain_info(guid)["high"], 16.0)
        doc.undo()
        self.assertEqual(len(doc.ifc.terrain_points(guid)), 12)
        # the plan of a storey at 10 m: the contour lines under its cut (11,2 m): 11 (10 m is only a corner)
        storey = doc.active_storey
        bim.set_storey_elevation(doc, storey, 10.0)
        drawing = drawings.plan(doc, storey, "Planta")
        self.assertEqual(sorted({round(h, 3) for _s, _m, h in drawing.contours}), [11.0])
        tall = drawings.plan(doc, storey, "Planta", cut_height=5.0)
        self.assertEqual(sorted({round(h, 3) for _s, _m, h in tall.contours}), [11.0, 12.0, 13.0])
        self.assertTrue(all(major == (round(h) % 5 == 0) for _s, major, h in drawing.contours))
        self.assertTrue(len(drawing.lines))                             # (its outline)
        self.assertLess(len(drawing.lines), 30)                         # (not its triangles)
        # a slab over the whole terrain at 14,5 m: its contour lines hidden under it
        bim.add_slab(doc, np.array((-1.0, -1.0, 14.5)), 32.0, 22.0, catalog.BY_KEY["laje_15"], storey=storey)
        covered = drawings.plan(doc, storey, "Planta", cut_height=5.0)
        self.assertEqual(covered.contours, [])
        # interval and base
        bim.set_terrain_params(doc, guid, interval=0.5, depth=3.0)
        self.assertAlmostEqual(doc.ifc.terrain_interval(guid), 0.5)
        self.assertAlmostEqual(doc.ifc.terrain_params(guid)["depth"], 3.0)
        self.assertAlmostEqual(float(doc.get(guid).mesh.bounds()[0][2]), 7.0)

    def test_spot_height(self):
        """0.156: a spot height in the ground floor's plan, on the terrain: the height there (12,00 at x = 15,
        y = 10), on its plan drawing; the terrain made higher there, the spot follows it."""
        from arqbim.model import annotations as notes2d
        from arqbim.model import drawings
        doc = Document()
        guid = bim.add_terrain(doc, self._points())
        storey = doc.active_storey
        bim.set_storey_elevation(doc, storey, 11.0)
        spot = notes2d.Annotation(("plan", storey), "spot", [np.array((15.0, 10.0, 11.0))])
        doc.execute(notes2d.AddAnnotation(spot, "Cota"))
        texts = [a[3] for a in drawings.plan(doc, storey, "Planta").annotations if a[0] == "spot"]
        self.assertEqual(texts, ["+12,00"])
        bim.set_terrain_points(doc, guid, list(self._points()) + [(15.0, 10.0, 12.10)])
        texts = [a[3] for a in drawings.plan(doc, storey, "Planta").annotations if a[0] == "spot"]
        self.assertEqual(texts, ["+12,10"])

    def test_platform(self):
        """0.157: a 6 × 4 m platform at 12 m on the terrain (10 to 14 m): the ground there flat at 12, the IFC still
        valid (the survey kept as IfcText), the survey's 12 points still there, earth cut and filled; kept when
        saved and opened again; on the plan its outline and «+12,00»; one more survey point keeps the platform;
        deleted, the ground as surveyed; undone, back."""
        from arqbim.core import terrain as terrain_geo
        from arqbim.model import drawings
        doc = Document()
        guid = bim.add_terrain(doc, self._points())
        outline = [(12.0, 8.0), (18.0, 8.0), (18.0, 12.0), (12.0, 12.0)]
        cut, fill = bim.add_platform(doc, guid, outline, 12.0)
        verts, tris = doc.ifc.terrain_surface(guid)
        self.assertAlmostEqual(terrain_geo.height_at(verts, tris, (15.0, 10.0)), 12.0, places=6)
        self.assertAlmostEqual(terrain_geo.height_at(verts, tris, (12.5, 8.5)), 12.0, places=6)
        self.assertEqual(doc.ifc.validate(), [])
        self.assertEqual(len(doc.ifc.terrain_survey(guid)), 12)
        self.assertGreater(cut, 0.5)
        self.assertGreater(fill, 0.5)
        info = doc.ifc.describe(guid)["params"]
        self.assertEqual((info["platforms"], info["points"]), (1, 12))
        storey = doc.active_storey
        bim.set_storey_elevation(doc, storey, 11.0)
        drawing = drawings.plan(doc, storey, "Planta")
        self.assertEqual([text for _r, text in drawing.platforms], ["+12,00"])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "plataforma.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            self.assertEqual(len(again.ifc.terrain_platforms(guid)), 1)
            np.testing.assert_allclose(again.ifc.terrain_platforms(guid)[0].outline, outline, atol=1e-6)
            geomcache.forget(path)
        bim.set_terrain_points(doc, guid, list(doc.ifc.terrain_survey(guid)) + [(30.0, 25.0, 15.0)])
        self.assertEqual(len(doc.ifc.terrain_survey(guid)), 13)
        verts, tris = doc.ifc.terrain_surface(guid)
        self.assertAlmostEqual(terrain_geo.height_at(verts, tris, (15.0, 10.0)), 12.0, places=6)
        bim.remove_platforms(doc, guid)
        self.assertEqual(doc.ifc.terrain_platforms(guid), [])
        verts, tris = doc.ifc.terrain_surface(guid)
        self.assertAlmostEqual(terrain_geo.height_at(verts, tris, (15.0, 10.0)), 12.0, places=6)  # (the plane)
        self.assertAlmostEqual(terrain_geo.height_at(verts, tris, (12.0, 12.0)), 11.8, places=6)
        doc.undo()
        self.assertEqual(len(doc.ifc.terrain_platforms(guid)), 1)

    def test_slope_colours_on_paper(self):
        """0.201: a plan whose view has the slope colours on: its terrain's surface in the bands of its slope, joined
        by band, the whole of it (600 m²); its crop region cuts them (100 m²); off, none; the view's property kept
        in the .arqbim file's way and undone."""
        from shapely.geometry import Polygon
        from arqbim.core import terrain as terrain_geo
        from arqbim.model import drawings
        from arqbim.model import view_templates as templates_model
        doc = Document()
        bim.add_terrain(doc, list(self._points()) + [(15.0, 10.0, 18.0)])           # (a steep hill in the middle)
        storey = doc.active_storey
        bim.set_storey_elevation(doc, storey, 10.0)
        self.assertEqual(drawings.plan(doc, storey, "Planta", cut_height=20.0).slope_fills, [])

        def area(fills):
            return sum(Polygon(o, h).area for _b, parts in fills for o, h in parts)

        self.assertTrue(doc.set_view_props(("plan", storey), slopes=True))
        fills = drawings.plan(doc, storey, "Planta", cut_height=20.0).slope_fills
        self.assertAlmostEqual(area(fills), 600.0, places=3)
        bands = [b for b, _p in fills]
        self.assertEqual(bands, sorted(set(bands)))                                 # (one entry per band)
        self.assertIn(len(terrain_geo.SLOPE_BANDS) - 1, bands)                      # (the hill: over 25 %)
        self.assertGreater(len(bands), 1)
        low = drawings.plan(doc, storey, "Planta").slope_fills                      # (cut at 11,20 m: less of it)
        self.assertLess(area(low), 600.0 - 1.0)
        doc.set_view_props(("plan", storey), crop=(0.0, 0.0, 10.0, 10.0))
        self.assertAlmostEqual(area(drawings.plan(doc, storey, "Planta", cut_height=20.0).slope_fills), 100.0, places=3)
        self.assertEqual(templates_model.own_from_dict({"slopes": True, "grid": False}), {"slopes": True, "grid": False})
        doc.undo()
        doc.undo()
        self.assertFalse(doc.view_settings(("plan", storey)).slopes)

    def test_terrain_ramp(self):
        """0.205: two platforms, at 11 m and at 13 m, and a 3 m wide ramp from the edge of one to the edge of the
        other: its ends at their heights, 12 m half way, its text in the plan («+11,00 / +13,00 · 16,7 %»), the IFC
        valid; undone, gone."""
        from arqbim.core import terrain as terrain_geo
        from arqbim.model import drawings
        doc = Document()
        guid = bim.add_terrain(doc, self._points())
        bim.add_platform(doc, guid, [(2.0, 8.0), (8.0, 8.0), (8.0, 12.0), (2.0, 12.0)], 11.0)
        bim.add_platform(doc, guid, [(20.0, 8.0), (26.0, 8.0), (26.0, 12.0), (20.0, 12.0)], 13.0)
        cut, fill = bim.add_terrain_ramp(doc, guid, (8.0, 10.0), (20.0, 10.0), 3.0)
        self.assertGreater(cut + fill, 0.5)
        ramp = doc.ifc.terrain_platforms(guid)[-1]
        self.assertTrue(ramp.is_ramp())
        self.assertAlmostEqual(ramp.z, 11.0, places=6)
        self.assertAlmostEqual(ramp.z_end, 13.0, places=6)
        verts, tris = doc.ifc.terrain_surface(guid)
        self.assertAlmostEqual(terrain_geo.height_at(verts, tris, (14.0, 10.0)), 12.0, places=5)
        self.assertAlmostEqual(terrain_geo.height_at(verts, tris, (14.0, 11.2)), 12.0, places=5)
        self.assertAlmostEqual(terrain_geo.height_at(verts, tris, (5.0, 10.0)), 11.0, places=6)    # (A as it was)
        storey = doc.active_storey
        bim.set_storey_elevation(doc, storey, 10.0)
        texts = [text for _r, text in drawings.plan(doc, storey, "Planta", cut_height=5.0).platforms]
        self.assertIn("+11,00 / +13,00 · 16,7 %", texts)
        self.assertEqual(doc.ifc.validate(), [])
        doc.undo()
        doc.undo()
        self.assertEqual(len(doc.ifc.terrain_platforms(guid)), 2)
        with self.assertRaises(ValueError):
            bim.add_terrain_ramp(doc, guid, (8.0, 10.0), (8.0, 10.0), 3.0)
        with self.assertRaises(ValueError):
            bim.add_terrain_ramp(doc, guid, (8.0, 10.0), (60.0, 10.0), 3.0)

    def test_edit_platform(self):
        """0.204: a platform's outline changed (a corner moved 3 m east): the ground flat at its height in the new
        part, as surveyed where it no longer is; its height changed too; one undo step each; the IFC valid."""
        from arqbim.core import terrain as terrain_geo
        doc = Document()
        guid = bim.add_terrain(doc, self._points())
        bim.add_platform(doc, guid, [(12.0, 8.0), (18.0, 8.0), (18.0, 12.0), (12.0, 12.0)], 12.0)
        cut, fill = bim.set_platform(doc, guid, 0, outline=[(12.0, 8.0), (21.0, 8.0), (21.0, 12.0), (12.0, 12.0)])
        self.assertTrue(cut > 0.5 and fill > 0.5)
        verts, tris = doc.ifc.terrain_surface(guid)
        self.assertAlmostEqual(terrain_geo.height_at(verts, tris, (20.0, 10.0)), 12.0, places=6)    # (now on it)
        np.testing.assert_allclose(doc.ifc.terrain_platforms(guid)[0].outline,
                                   [(12.0, 8.0), (21.0, 8.0), (21.0, 12.0), (12.0, 12.0)])
        self.assertEqual(doc.ifc.validate(), [])
        bim.set_platform(doc, guid, 0, z=12.5)
        verts, tris = doc.ifc.terrain_surface(guid)
        self.assertAlmostEqual(terrain_geo.height_at(verts, tris, (15.0, 10.0)), 12.5, places=6)
        doc.undo()
        doc.undo()
        verts, tris = doc.ifc.terrain_surface(guid)
        self.assertAlmostEqual(terrain_geo.height_at(verts, tris, (15.0, 10.0)), 12.0, places=6)
        self.assertNotAlmostEqual(terrain_geo.height_at(verts, tris, (20.5, 10.0)), 12.0, places=2)  # (off it: slope)
        with self.assertRaises(IndexError):
            bim.set_platform(doc, guid, 3, z=1.0)

    def test_platform_batters(self):
        """0.203: a 6 × 4 m platform at 12 m on the terrain (10 to 14 m, rising to the east): its plan has its slopes'
        lines and ticks — the crest of the cut to the east of it, the toe of the fill to the west —, in the DXF on
        their layer; without platforms, none."""
        from arqbim.model import drawings, dxf
        doc = Document()
        guid = bim.add_terrain(doc, self._points())
        storey = doc.active_storey
        bim.set_storey_elevation(doc, storey, 11.0)
        self.assertEqual(len(drawings.plan(doc, storey, "Planta").batters), 0)
        bim.add_platform(doc, guid, [(12.0, 8.0), (18.0, 8.0), (18.0, 12.0), (12.0, 12.0)], 12.0)
        plan = drawings.plan(doc, storey, "Planta")
        segs = plan.batters
        self.assertGreater(len(segs), 10)
        xs = segs[:, :, 0]
        self.assertTrue((xs.max(axis=1) > 18.05).any() and (xs.min(axis=1) < 11.95).any())  # (beyond both sides)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "taludes.dxf")
            dxf.write(path, plan, 200)
            with open(path, encoding="cp1252") as f:
                text = f.read()
        self.assertIn("TALUDES", text)
        self.assertGreater(text.count("\nTALUDES\n"), 10)

    def test_major_contour_heights(self):
        """0.202: the major contour line round the hill (15 m) has its height written along it in the DXF, on its
        layer, turned along it; the others (11 to 14) none."""
        from arqbim.model import drawings, dxf
        doc = Document()
        bim.add_terrain(doc, list(self._points()) + [(15.0, 10.0, 18.0)])
        storey = doc.active_storey
        bim.set_storey_elevation(doc, storey, 10.0)
        plan = drawings.plan(doc, storey, "Planta", cut_height=20.0)
        self.assertIn(15.0, [round(h, 3) for _s, major, h in plan.contours if major])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "terreno.dxf")
            dxf.write(path, plan, 100)
            with open(path, encoding="cp1252") as f:
                lines = [s.strip() for s in f.read().splitlines()]
        texts = []
        for k in range(len(lines) - 1):
            if lines[k] == "0" and lines[k + 1] == "TEXT":
                body = dict(zip(lines[k + 2:k + 40:2], lines[k + 3:k + 41:2]))
                texts.append((body.get("8"), body.get("1"), float(body.get("50", 0.0))))
        heights = [(layer, words) for layer, words, _a in texts if layer == "CURVAS_MESTRAS"]
        self.assertTrue(heights)
        self.assertEqual({words for _l, words in heights}, {"15"})
        self.assertTrue(all(-90.0 < a <= 90.0 for layer, _w, a in texts if layer == "CURVAS_MESTRAS"))

    def test_section_cut(self):
        from arqbim.model import drawings
        doc = Document()
        guid = bim.add_terrain(doc, self._points())
        drawing = drawings.section(doc, np.array((15.0, 10.0, 0.0)), np.array((0.0, 1.0, 0.0)), "Corte")
        self.assertIn("earth", [h for _ring, h in drawing.fills])
        cut = np.vstack(drawing.cut)
        self.assertAlmostEqual(float(cut[:, 1].max()), 10.0 + 0.1 * 30 + 0.05 * 10, places=3)   # (cut at y = 10)
        self.assertAlmostEqual(float(cut[:, 1].min()), 9.0, places=3)                          # (its base)
        self.assertTrue(guid)


class ImagesOnPaper(unittest.TestCase):
    """0.207: a storey's visible background image goes in its plan's drawing (its corners, picture, opacity) — not a
    hidden one, not another storey's —, and in the DXF as its frame and its file's name (R12 has no pictures)."""

    def test_plan_and_dxf(self):
        from arqbim.model import drawings, dxf, images
        from arqbim.model.document import ImagesChange
        doc = Document()
        storey = doc.active_storey
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        seen = images.placed("planta.png", "/tmp/planta_antiga.png", (800, 600), (3.0, 2.0), storey=storey)
        hidden = dataclasses.replace(images.placed("foto.png", "/tmp/foto.png", (400, 400), (0.0, 0.0), storey=storey),
                                     visible=False)
        upper = bim.add_storey(doc, "Piso 1", 3.0)
        other = images.placed("cima.png", "/tmp/cima.png", (400, 400), (0.0, 0.0), storey=upper)
        doc.execute(ImagesChange([], [seen, hidden, other], "Imagens"))
        plan = drawings.plan(doc, storey, "Planta")
        self.assertEqual([entry[1] for entry in plan.images], ["/tmp/planta_antiga.png"])
        corners, _path, opacity, kept = plan.images[0]
        np.testing.assert_allclose(kept, corners)                                  # (not cropped: all of it)
        np.testing.assert_allclose(corners, seen.corners())
        self.assertAlmostEqual(opacity, images.DEFAULT_OPACITY)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "planta.dxf")
            dxf.write(path, plan, 100)
            with open(path, encoding="cp1252") as f:
                text = f.read()
        self.assertIn("\nIMAGENS\n", text)
        self.assertIn("planta_antiga.png", text)

    def test_facade_photo_in_elevations(self):
        """0.208: a photo stood on the south face of a wall: in the south elevation, its corners in the drawing's frame
        (6 m wide, 3 m high), read from that side; not in the north one, nor in the plan."""
        from arqbim.model import drawings, images
        from arqbim.model.document import ImagesChange
        doc = Document()
        storey = doc.active_storey
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((10.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        photo = images.placed("fachada", "/tmp/fachada_sul.png", (400, 200), (0.0, 0.0), storey=storey)
        photo = photo.stood((2.0, -0.1, 0.0), (8.0, -0.1, 0.0), (0.0, -1.0, 0.0), 0.0)
        doc.execute(ImagesChange([], [photo], "Imagem"))
        south = drawings.elevation(doc, "S", "Alçado Sul")
        self.assertEqual(len(south.images), 1)
        corners = south.images[0][0]
        self.assertAlmostEqual(float(np.ptp(corners[:, 0])), 6.0)
        self.assertAlmostEqual(float(np.ptp(corners[:, 1])), 3.0)
        self.assertLess(corners[0][0], corners[1][0])                          # (read from the south: left to right)
        self.assertEqual(drawings.elevation(doc, "N", "Alçado Norte").images, [])
        self.assertEqual(drawings.plan(doc, storey, "Planta").images, [])

    def test_cropped_on_paper(self):
        """0.209: a picture cropped to its left half: the plan's drawing has its whole frame (for the picture) and
        the part kept (to cut it to); the DXF's frame is the part kept."""
        from arqbim.model import drawings, dxf, images
        from arqbim.model.document import ImagesChange
        doc = Document()
        storey = doc.active_storey
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((6.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        picture = images.placed("planta.png", "/tmp/planta_recortada.png", (1000, 500), (5.0, 2.5), storey=storey)
        doc.execute(ImagesChange([], [picture.cropped((0.0, 0.0), (0.5, 1.0))], "Imagem"))
        plan = drawings.plan(doc, storey, "Planta")
        corners, _path, _opacity, kept = plan.images[0]
        self.assertAlmostEqual(float(np.ptp(corners[:, 0])), 10.0)
        self.assertAlmostEqual(float(np.ptp(kept[:, 0])), 5.0)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "planta.dxf")
            dxf.write(path, plan, 100)
            with open(path, encoding="cp1252") as f:
                lines = [s.strip() for s in f.read().splitlines()]
        xs = [float(lines[k + 1]) for k in range(len(lines) - 1) if lines[k] == "10" and k > 0
              and "IMAGENS" in lines[max(0, k - 8):k]]
        self.assertTrue(xs and max(xs) <= 5.0 + 1e-6, xs)


class WallsFromCad(unittest.TestCase):
    """0.159: the walls of a 10 × 8 m room drawn in double lines with a wall across: five walls in one undo step —
    the outer ones of the 20 cm masonry type, the inner one of the 10 cm drywall, a 25 cm one of a new type —, their
    corners joined (together they cover what the drawing's double lines enclose, nothing twice; the inner one stops
    at the outer walls' faces), valid IFC; undone, none."""

    def test_walls(self):
        from arqbim.core import cad_walls
        rect = lambda x0, y0, x1, y1: [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)),  # noqa
                                       ((x0, y1), (x0, y0))]
        segs = rect(0, 0, 10, 8) + rect(0.2, 0.2, 4.95, 7.8) + rect(5.05, 0.2, 9.8, 7.8)
        doc = Document()
        axes = cad_walls.wall_axes(np.array(segs, dtype=float))
        made = bim.walls_from_axes(doc, axes)
        self.assertEqual(len(made), 5)
        types = sorted(doc.ifc.describe(g)["type"] for g in made)
        self.assertEqual(types.count("Parede alvenaria 20 cm"), 4)
        self.assertIn("Parede drywall 10 cm", types)
        params = [doc.ifc.wall_params(g) for g in made]
        outer = sum(length * th for length, _h, th in params if abs(th - 0.2) < 1e-6)
        self.assertAlmostEqual(outer, 10 * 8 - 9.6 * 7.6, places=6)    # (the ring of the outer walls, once)
        inner = [length for length, _h, th in params if abs(th - 0.1) < 1e-6]
        self.assertEqual([round(x, 6) for x in inner], [7.6])            # (face to face: a T at each end)
        self.assertEqual(doc.ifc.validate(), [])
        thick = bim.walls_from_axes(doc, [((0.0, 20.0), (5.0, 20.0), 0.25)])
        self.assertEqual(doc.ifc.describe(thick[0])["type"], "Parede 25 cm")
        doc.undo()
        doc.undo()
        self.assertEqual([o for o in doc.objects.values() if o.is_bim and o.ifc_class.startswith("IfcWall")], [])


class ModelFromCad(unittest.TestCase):
    """0.160: a room's DXF — its walls in double lines, a door's gap with a door block, a 1,20 m window block drawn
    in the top wall, two tables (one block twice) —: in one undo step four walls, the door (90 cm: the catalogue's)
    in the bottom wall from 4,0 to 4,9 m, the window (120 cm) in the top one, the tables a component placed twice;
    valid IFC; undone, nothing."""

    def _drawing(self):
        from arqbim.core import cad
        lines = [((0, 0), (4000, 0)), ((4900, 0), (10000, 0)), ((10000, 0), (10000, 8000)), ((10000, 8000), (0, 8000)),
                 ((0, 8000), (0, 0)), ((200, 200), (4000, 200)), ((4900, 200), (9800, 200)), ((9800, 200), (9800, 7800)),
                 ((9800, 7800), (200, 7800)), ((200, 7800), (200, 200)), ((4000, 0), (4000, 200)),
                 ((4900, 0), (4900, 200))]
        rows = ["0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4", "0", "ENDSEC", "0", "SECTION", "2", "BLOCKS",
                "0", "BLOCK", "8", "0", "2", "PORTA90", "10", "0", "20", "0",
                "0", "LINE", "8", "0", "10", "0", "20", "0", "11", "0", "21", "900",
                "0", "ARC", "8", "0", "10", "0", "20", "0", "40", "900", "50", "0", "51", "90", "0", "ENDBLK",
                "0", "BLOCK", "8", "0", "2", "JANELA120", "10", "0", "20", "0",
                "0", "LINE", "8", "0", "10", "0", "20", "0", "11", "1200", "21", "0",
                "0", "LINE", "8", "0", "10", "0", "20", "200", "11", "1200", "21", "200",
                "0", "LINE", "8", "0", "10", "0", "20", "100", "11", "1200", "21", "100", "0", "ENDBLK",
                "0", "BLOCK", "8", "0", "2", "MESA160", "10", "0", "20", "0",
                "0", "LWPOLYLINE", "8", "0", "90", "4", "70", "1", "10", "0", "20", "0", "10", "1600", "20", "0",
                "10", "1600", "20", "900", "10", "0", "20", "900", "0", "ENDBLK", "0", "ENDSEC",
                "0", "SECTION", "2", "ENTITIES"]
        for (x0, y0), (x1, y1) in lines:
            rows += ["0", "LINE", "8", "PAREDES", "10", str(x0), "20", str(y0), "11", str(x1), "21", str(y1)]
        rows += ["0", "INSERT", "8", "PORTAS", "2", "PORTA90", "10", "4000", "20", "200",
                 "0", "INSERT", "8", "JANELAS", "2", "JANELA120", "10", "6000", "20", "7800",
                 "0", "INSERT", "8", "MOBILIARIO", "2", "MESA160", "10", "2000", "20", "3000",
                 "0", "INSERT", "8", "MOBILIARIO", "2", "MESA160", "10", "6000", "20", "3000", "50", "90",
                 "0", "ENDSEC", "0", "EOF", ""]
        return cad.read("\n".join(rows))

    def test_model(self):
        from arqbim.core import cad, cad_openings, cad_walls
        drawing = self._drawing()
        place = lambda s: np.asarray(s, dtype=float) * 0.001                       # noqa: E731
        segs = place(cad.segments(cad.Drawing(drawing.entities, drawing.blocks, 1.0))["PAREDES"])
        blocks = cad_openings.instances(drawing, place, {"PORTAS", "JANELAS"})
        openings = [(b, cad_openings.kind_of(b)) for b in blocks]
        self.assertEqual(sorted(k for _b, k in openings), ["door", "window"])
        axes = cad_walls.wall_axes(segs, blocks=blocks)
        furniture = cad_openings.furniture_items(drawing, place, 0.001, {"MOBILIARIO"})
        doc = Document()
        report = bim.model_from_cad(doc, axes, openings, furniture)
        self.assertEqual((len(report["walls"]), len(report["doors"]), len(report["windows"]),
                          len(report["furniture"]), report["left"]), (4, 1, 1, 2, 0))
        door = doc.ifc.by_guid(report["doors"][0])
        self.assertAlmostEqual(door.OverallWidth * doc.ifc.unit_scale, 0.9, places=6)
        lo, hi = doc.get(report["doors"][0]).mesh.bounds()
        self.assertAlmostEqual(float(lo[0]), 4.0, delta=0.06)
        self.assertAlmostEqual(float(hi[0]), 4.9, delta=0.06)
        window = doc.ifc.by_guid(report["windows"][0])
        self.assertAlmostEqual(window.OverallWidth * doc.ifc.unit_scale, 1.2, places=6)
        wlo, whi = doc.get(report["windows"][0]).mesh.bounds()
        self.assertGreater(float(wlo[1]), 7.7)                              # (in the top wall)
        types = {doc.ifc.component_type(g) for g in report["furniture"]}
        self.assertEqual(len(types), 1)                                     # (one component, placed twice)
        self.assertEqual(doc.ifc.validate(), [])
        doc.undo()
        self.assertEqual([o for o in doc.objects.values() if o.is_bim], [])

    def test_sizes_written(self):
        """0.212: the drawing's sizes written beside its openings — «0,90x2,20» by the door, «1,20x1,10 pt 0,95» by
        the window: the door 2,20 m high, the window 1,10 m on a 0,95 m sill (types of those sizes)."""
        from arqbim.core import cad, cad_openings, cad_walls
        drawing = self._drawing()
        drawing.entities += [cad.Entity("text", "COTAS", [(4450.0, 600.0)], text="0,90x2,20"),
                             cad.Entity("text", "COTAS", [(6600.0, 7300.0)], text="1,20x1,10 pt 0,95")]
        place = lambda s: np.asarray(s, dtype=float) * 0.001                       # noqa: E731
        segs = place(cad.segments(cad.Drawing(drawing.entities, drawing.blocks, 1.0))["PAREDES"])
        blocks = cad_openings.instances(drawing, place, {"PORTAS", "JANELAS"})
        self.assertEqual(cad_openings.read_sizes(blocks, cad_openings.texts(drawing, place)), 2)
        openings = [(b, cad_openings.kind_of(b)) for b in blocks]
        doc = Document()
        report = bim.model_from_cad(doc, cad_walls.wall_axes(segs, blocks=blocks), openings)
        door = doc.ifc.by_guid(report["doors"][0])
        self.assertAlmostEqual(door.OverallHeight * doc.ifc.unit_scale, 2.20, places=6)
        window = doc.ifc.by_guid(report["windows"][0])
        self.assertAlmostEqual(window.OverallHeight * doc.ifc.unit_scale, 1.10, places=6)
        wlo, _whi = doc.get(report["windows"][0]).mesh.bounds()
        self.assertAlmostEqual(float(wlo[2]), 0.95, delta=0.02)                    # (on its sill)
        self.assertEqual(doc.ifc.validate(), [])

    def test_curved_walls(self):
        """0.210: a DXF with a straight wall (two lines 20 cm apart, 0 → 4 m) going on in a curved one (two arcs round
        (4; 3), 3 m and 3,2 m, from -90° to 0°): a straight wall and a curved one, 20 cm, in one undo step, joined end
        to end; valid IFC."""
        from arqbim.core import cad, cad_walls
        text = "\n".join([
            "0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "6", "0", "ENDSEC",
            "0", "SECTION", "2", "ENTITIES",
            "0", "LINE", "8", "PAREDES", "10", "0", "20", "0", "11", "4", "21", "0",
            "0", "LINE", "8", "PAREDES", "10", "0", "20", "-0.2", "11", "4", "21", "-0.2",
            "0", "ARC", "8", "PAREDES", "10", "4", "20", "3", "40", "3.0", "50", "-90", "51", "0",
            "0", "ARC", "8", "PAREDES", "10", "4", "20", "3", "40", "3.2", "50", "-90", "51", "0",
            "0", "ENDSEC", "0", "EOF", ""])
        drawing = cad.read(text)
        straight = cad.segments(drawing, straight=True)["PAREDES"]
        axes = cad_walls.wall_axes(straight)
        arcs = cad_walls.arc_walls(cad.arcs(drawing)["PAREDES"])
        self.assertEqual((len(axes), len(arcs)), (1, 1))
        doc = Document()
        report = bim.model_from_cad(doc, axes, arcs=arcs)
        self.assertEqual(len(report["walls"]), 2)
        _centre, radius, start, sweep, _h, thickness = doc.ifc.curved_wall_params(report["walls"][1])
        self.assertAlmostEqual(radius, 3.1, places=3)
        self.assertAlmostEqual(sweep, np.pi / 2, places=6)
        self.assertAlmostEqual(thickness, 0.2, places=3)
        self.assertEqual(doc.ifc.validate(), [])
        doc.undo()
        self.assertEqual([o for o in doc.objects.values() if o.is_bim], [])

    def test_columns(self):
        """0.211: a DXF's PILARES layer with a closed 50 × 20 rectangle (the catalogue's 20 × 50, turned) and a circle
        30 cm across: two columns as high as asked, of the 20 × 50 type turned a quarter and of the round Ø30 one, in
        one undo step; valid IFC."""
        from arqbim.core import cad, cad_columns
        text = "\n".join([
            "0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "6", "0", "ENDSEC",
            "0", "SECTION", "2", "ENTITIES",
            "0", "LWPOLYLINE", "8", "PILARES", "90", "4", "70", "1", "10", "1", "20", "1", "10", "1.5", "20", "1",
            "10", "1.5", "20", "1.2", "10", "1", "20", "1.2",
            "0", "CIRCLE", "8", "PILARES", "10", "4", "20", "4", "40", "0.15",
            "0", "ENDSEC", "0", "EOF", ""])
        polygons, circles = cad.closed_shapes(cad.read(text))["PILARES"]
        found = cad_columns.columns(polygons, circles)
        self.assertEqual(len(found), 2)
        doc = Document()
        report = bim.model_from_cad(doc, [], columns=found, height=3.0)
        self.assertEqual(len(report["columns"]), 2)
        names = sorted(ue.get_type(doc.ifc.by_guid(g)).Name for g in report["columns"])
        self.assertEqual(names, ["Pilar circular Ø30", "Pilar de concreto 20×50"])
        rect = next(g for g in report["columns"] if "20×50" in ue.get_type(doc.ifc.by_guid(g)).Name)
        lo, hi = bounds(doc, rect)
        np.testing.assert_allclose(hi - lo, (0.5, 0.2, 3.0), atol=1e-6)            # (turned: 50 along x)
        np.testing.assert_allclose((lo + hi)[:2] / 2, (1.25, 1.1), atol=1e-6)
        self.assertEqual(doc.ifc.validate(), [])
        doc.undo()
        self.assertEqual([o for o in doc.objects.values() if o.is_bim], [])


class ScanOpeningsModel(unittest.TestCase):
    """0.213: a scanned 6 m wall with a door's gap and a window's: the wall, a door 90 cm wide and 2,10 m high and a
    window 1,20 m on a 1,00 m sill in it, in one undo step; valid IFC."""

    def test_model(self):
        from arqbim.core import scan_walls
        pts = []
        for x in np.arange(0.0, 6.0001, 0.02):
            for z in np.arange(0.0, 2.8001, 0.04):
                if (2.0 < x < 2.9 and z < 2.1) or (4.0 < x < 5.2 and 1.0 < z < 2.2):
                    continue
                pts += [(x, -0.1, z), (x, 0.1, z)]
        walls = [(np.array((0.0, 0.0)), np.array((6.0, 0.0)), 0.2)]
        found = scan_walls.openings(np.array(pts), walls, 0.0, 2.8)
        doc = Document()
        report = bim.model_from_cad(doc, walls, found, height=2.8)
        self.assertEqual((len(report["walls"]), len(report["doors"]), len(report["windows"]), report["left"]),
                         (1, 1, 1, 0))
        s = doc.ifc.unit_scale
        door = doc.ifc.by_guid(report["doors"][0])
        self.assertAlmostEqual(door.OverallWidth * s, 0.9, delta=0.051)
        self.assertAlmostEqual(door.OverallHeight * s, 2.1, delta=0.051)
        window = doc.ifc.by_guid(report["windows"][0])
        self.assertAlmostEqual(window.OverallWidth * s, 1.2, delta=0.051)
        lo, _hi = doc.get(report["windows"][0]).mesh.bounds()
        self.assertAlmostEqual(float(lo[2]), 1.0, delta=0.06)
        self.assertEqual(doc.ifc.validate(), [])


class ModelFromScan(unittest.TestCase):
    """0.162: a room scanned from inside with a 10 cm wall across it: in one undo step five walls (the outer ones
    30 cm, outwards; the inner one 10 cm, a T at each end) as high as the room, a floor slab under them all; valid
    IFC."""

    def test_model(self):
        from arqbim.core import scan_walls
        rng = np.random.default_rng(5)
        pts = []
        zs = np.arange(0.0, 2.8001, 0.05)
        for x in np.arange(0.0, 6.0001, 0.04):
            pts += [(x, y, z) for y in (0.0, 4.0) for z in zs]
        for y in np.arange(0.0, 4.0001, 0.04):
            pts += [(x, y, z) for x in (0.0, 6.0) for z in zs]
            if not 1.0 < y < 1.9:
                pts += [(x, y, z) for x in (2.95, 3.05) for z in zs]
        pts = np.array(pts) + rng.normal(0.0, 0.002, (len(pts), 3))
        xy = scan_walls.slice_xy(pts, 0.0)
        walls = scan_walls.wall_axes(scan_walls.lines(xy), xy)
        outline = scan_walls.floor_outline(walls)
        doc = Document()
        report = bim.model_from_cad(doc, walls, height=2.8, slab=(outline, catalog.BY_KEY["laje_15"]))
        self.assertEqual((len(report["walls"]), len(report["slabs"])), (5, 1))
        heights = {round(doc.ifc.wall_params(g)[1], 6) for g in report["walls"]}
        self.assertEqual(heights, {2.8})
        lo, hi = doc.get(report["slabs"][0]).mesh.bounds()
        np.testing.assert_allclose((lo[0], lo[1], hi[0], hi[1]), (-0.3, -0.3, 6.3, 4.3), atol=0.02)
        self.assertEqual(doc.ifc.validate(), [])


class AnalyticalModelIfc(unittest.TestCase):
    """0.163: a frame drawn with the program's tools — four columns on footings, four beams, a slab — made an
    analytical model in the IFC: an IfcStructuralAnalysisModel (LOADING_3D) with eight nodes, four fixed supports,
    eight curve members joined to their nodes and to the column / beam each stands for, a surface member; valid IFC;
    made again, still one; read back as drawn."""

    def test_model(self):
        import ifcopenshell.util.element as ue
        doc = Document()
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        for x, y in corners:
            bim.add_column(doc, np.array((x, y, 0.0)), catalog.BY_KEY["pilar_20"], 3.0)
        bim.footings_under(doc, None, catalog.BY_KEY["sapata_120"])
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            bim.add_beam(doc, np.array((*a, 3.0)), np.array((*b, 3.0)), catalog.BY_KEY["viga_20x40"], 3.0)
        model = bim.analytical_model(doc)
        self.assertEqual([i.code for i in model.issues], [])
        analysis = doc.ifc.analysis_models()
        self.assertEqual(len(analysis), 1)
        self.assertEqual(analysis[0].PredefinedType, "LOADING_3D")
        grouped = [o for rel in analysis[0].IsGroupedBy for o in rel.RelatedObjects]
        nodes = [o for o in grouped if o.is_a("IfcStructuralPointConnection")]
        members = [o for o in grouped if o.is_a("IfcStructuralCurveMember")]
        self.assertEqual((len(nodes), len(members)), (8, 8))
        self.assertEqual(sum(1 for n in nodes if n.AppliedCondition is not None), 4)
        for m in members:
            self.assertEqual(len(m.ConnectedBy), 2)
            physical = [r.RelatingProduct for r in m.HasAssignments if r.is_a("IfcRelAssignsToProduct")]
            self.assertTrue(physical and physical[0].is_a() in ("IfcColumn", "IfcBeam"))
        self.assertEqual(doc.ifc.validate(), [])
        bim.analytical_model(doc)                                          # (made again: still one)
        self.assertEqual(len(doc.ifc.analysis_models()), 1)
        lines, supports, _panels = doc.ifc.analytical_lines()
        self.assertEqual(sorted(k for k, _a, _b in lines), ["beam"] * 4 + ["column"] * 4)
        self.assertEqual(sorted(k for _p, k in supports), ["fixed"] * 4)
        tops = sorted({round(float(max(a[2], b[2])), 6) for k, a, b in lines if k == "column"})
        self.assertEqual(tops, [3.0])
        self.assertTrue(ue)

    def test_load_bearing_walls(self):
        """0.335: four 20 cm walls drawn with the program's tools, marked load bearing (Pset_WallCommon), each on a
        strip footing, a slab on them, a door in one: the walls in the analytical model — their load-bearing layer
        the block (16 cm), the door's opening —, each on its footing, the slab held; in the IFC as surface members
        (SHELL) tied to their walls; valid; a wall not marked stays out."""
        doc = Document()
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (6.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        walls = bim.add_wall_loop(doc, corners, catalog.BY_KEY["parede_alv_20"])
        strip = catalog.BY_KEY["sapata_corrida_50"]
        for g in walls:
            bim.set_property(doc, g, "Pset_WallCommon", "LoadBearing", True)
            bim.add_footing(doc, bim.footing_place(doc, g, strip), strip, under=g)
        bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, walls[0]), 2.0, -1)
        top = float(doc.get(walls[0]).mesh.bounds()[1][2])
        bim.add_slab(doc, np.array((0.0, 0.0, top)), 6.0, 4.0, catalog.BY_KEY["laje_15"])
        loose = bim.add_wall(doc, (2.0, 1.0, 0.0), (2.0, 3.0, 0.0), catalog.BY_KEY["parede_alv_20"])
        model = bim.analytical_model(doc)
        self.assertEqual(sorted(w.guid for w in model.walls), sorted(walls))
        self.assertNotIn(loose, [w.guid for w in model.walls])
        self.assertEqual([i.code for i in model.issues], [])
        self.assertTrue(all(model.wall_bases[g][0] == "footing" for g in walls))
        first = next(w for w in model.walls if w.guid == walls[0])
        self.assertAlmostEqual(first.t, 0.16)
        self.assertEqual(len(first.openings), 1)
        s0, s1, z0, z1 = first.openings[0]
        self.assertAlmostEqual(s1 - s0, 0.80, places=2)
        grouped = [o for rel in doc.ifc.analysis_models()[0].IsGroupedBy for o in rel.RelatedObjects]
        shells = [o for o in grouped if o.is_a("IfcStructuralSurfaceMember") and o.PredefinedType == "SHELL"]
        self.assertEqual(sorted(o.Name for o in shells), sorted(walls))
        tied = {r.RelatingProduct.GlobalId for o in shells for r in o.HasAssignments if r.is_a("IfcRelAssignsToProduct")}
        self.assertEqual(tied, set(walls))
        self.assertEqual(doc.ifc.validate(), [])
        _lines, _supports, faces = doc.ifc.analytical_lines()
        self.assertEqual(len(faces), 5)                                  # (the slab and the four walls)

    def test_walls_checked(self):
        """0.337: the four load-bearing walls on their strip footings, a slab on them, their masonry the project's
        (clay, group 2, fb 10, M5; kept in the building): each checked by Eurocode 6 — OK, its notes —, no bars for
        them in the model; the calculation report with the masonry, the walls' loads and their verification."""
        from arqbim.core import ec2
        from arqbim.model import structure_report
        doc = Document()
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (6.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        walls = bim.add_wall_loop(doc, corners, catalog.BY_KEY["parede_alv_20"])
        strip = catalog.BY_KEY["sapata_corrida_50"]
        for g in walls:
            bim.set_property(doc, g, "Pset_WallCommon", "LoadBearing", True)
            bim.add_footing(doc, bim.footing_place(doc, g, strip), strip, under=g)
        top = float(doc.get(walls[0]).mesh.bounds()[1][2])
        bim.add_slab(doc, np.array((0.0, 0.0, top)), 6.0, 4.0, catalog.BY_KEY["laje_15"])
        settings = doc.ifc.structural_settings()
        settings.masonry_fb = 15.0
        doc.ifc.set_structural_settings(settings)
        self.assertEqual(doc.ifc.structural_settings().masonry_fb, 15.0)
        self.assertEqual(doc.ifc.structural_settings().masonry_group, "2")
        _m, _l, analysis, designs = bim.design_structure(doc)
        self.assertEqual(analysis.error, "")
        checked = [e for e in designs if e.kind == "wall"]
        self.assertEqual(sorted(e.guid for e in checked), sorted(walls))
        self.assertTrue(all(e.design.status == ec2.OK for e in checked))
        self.assertEqual(checked[0].design.notes[0].values["fb"], 15.0)
        self.assertEqual(sorted(e.kind for e in designs), ["footing"] * 4 + ["slab"] + ["wall"] * 4)
        members, _bars = bim.make_rebars(doc, designs)
        self.assertEqual(members, 5)                                      # (the footings and the slab)
        page = structure_report.report_html(bim.report_data(doc))
        for k in range(1, 10):
            self.assertIn("<h2>{}. ".format(k), page)
        self.assertIn("NP EN 1996-1-1", page)
        self.assertIn("fk", page)
        for g in walls:
            self.assertIn(doc.get(g).name, page)

    def test_concrete_walls(self):
        """0.342: four 20 cm reinforced concrete walls (the catalogue's new type — load-bearing as made), on strip
        footings, a slab on them, a door in one: each verified by Eurocode 2 with its bars (vertical and horizontal on
        each face); put in the model: their vertical bars both faces, their horizontal ones, the bars round the door —
        none in the door's hole —, the starters bent in the footing; the bar schedule's roles; the quantities (the
        walls' concrete, formwork, steel); the calculation report with their elevations; valid."""
        from arqbim.core import ec2
        from arqbim.ifc import catalog as cat
        from arqbim.model import structure_report
        doc = Document()
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (6.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        walls = bim.add_wall_loop(doc, corners, cat.BY_KEY["parede_betao_20"])
        self.assertTrue(all(ue.get_psets(doc.ifc.by_guid(g))["Pset_WallCommon"]["LoadBearing"] for g in walls))
        strip = cat.BY_KEY["sapata_corrida_50"]
        for g in walls:
            bim.add_footing(doc, bim.footing_place(doc, g, strip), strip, under=g)
        bim.add_opening(doc, walls[0], cat.OPENING_BY_KEY["porta_90"], bim.wall_frame(doc, walls[0]), 2.0, -1)
        top = float(doc.get(walls[0]).mesh.bounds()[1][2])
        bim.add_slab(doc, np.array((0.0, 0.0, top)), 6.0, 4.0, cat.BY_KEY["laje_15"])
        model, _l, analysis, designs = bim.design_structure(doc)
        self.assertEqual(sorted(w.guid for w in model.walls if w.material == "concrete"), sorted(walls))
        checked = [e for e in designs if e.kind == "wall"]
        self.assertEqual(len(checked), 4)
        self.assertTrue(all(e.design.status == ec2.OK and e.design.vertical and e.design.horizontal for e in checked))
        self.assertTrue(all(e.info.get("into", 0.0) > 0.2 for e in checked))      # (into the strip footing)
        members, _bars = bim.make_rebars(doc, designs)
        self.assertEqual(members, 9)                                          # (4 walls, 4 footings, the slab)
        rows = [r for r in doc.ifc.rebar_rows() if r["host"] == walls[0]]
        self.assertEqual({r["role"] for r in rows}, {"wall_v", "wall_h", "wall_trim"})
        door = doc.ifc.filling_state(next(o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcDoor"))
        start, end, _t = doc.ifc.wall_axis(walls[0])
        ux = (end - start) / np.linalg.norm(end - start)
        through = False
        for r in rows:
            if r["role"] != "wall_v":
                continue
            for bar in doc.ifc.rebar_bars(r["guid"]):
                s = float((bar.mean(axis=0) - start) @ ux)
                low, high = float(bar[:, 2].min()), float(bar[:, 2].max())
                if door["s"] < s < door["s"] + door["width"] and low < 1.0 < high:
                    through = True                                            # (a bar across the door's hole)
        self.assertFalse(through)
        bent = [b for r in rows if r["role"] == "wall_v" for b in doc.ifc.rebar_bars(r["guid"]) if len(b) == 3]
        self.assertTrue(bent and all(float(b[:, 2].min()) < float(start[2]) - 0.2 for b in bent))   # (starters)
        quantities = [q for q in bim.structure_quantities(doc) if q.kind == "wall"]
        self.assertEqual(len(quantities), 4)
        self.assertTrue(all(q.concrete > 0.5 and q.formwork > 10.0 and q.has_bars and q.steel > 10.0
                            for q in quantities))
        page = structure_report.report_html(bim.report_data(doc))
        self.assertIn(doc.get(walls[0]).name, page)
        self.assertIn("vert. Ø", page)
        self.assertEqual(doc.ifc.validate(), [])

    def test_facade_walls(self):
        """0.345: a house of four 20 cm masonry walls (not load-bearing) with a slab on them, a door and two windows,
        and a garden wall standing alone: the five outside (IsExternal), each with its masonry's 16 cm and its
        supports — the house's on their four edges (the slab on top, the walls at their ends), the garden wall only at
        its base —; verified out of their plane by the wind: the house's walls OK (by their arch under the slab when
        bending alone is not enough), the garden wall fails (2,80 m standing free); in the calculation report."""
        from arqbim.core import ec2
        from arqbim.ifc import catalog as cat
        from arqbim.model import design_text, structure_report
        doc = Document()
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (6.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        walls = bim.add_wall_loop(doc, corners, cat.BY_KEY["parede_alv_20"])
        bim.add_opening(doc, walls[0], cat.OPENING_BY_KEY["porta_90"], bim.wall_frame(doc, walls[0]), 2.5, -1)
        for at in (0.8, 4.2):
            bim.add_opening(doc, walls[0], cat.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, walls[0]), at, -1)
        top = float(doc.get(walls[0]).mesh.bounds()[1][2])
        bim.add_slab(doc, np.array((0.0, 0.0, top)), 6.0, 4.0, cat.BY_KEY["laje_12"])
        garden = bim.add_wall(doc, np.array((10.0, 0.0, 0.0)), np.array((14.0, 0.0, 0.0)), cat.BY_KEY["parede_alv_20"])
        found = {w["guid"]: w for w in bim.facade_walls(doc)}
        self.assertEqual(set(found), set(walls) | {garden})
        self.assertTrue(all(abs(found[g]["t"] - 0.16) < 1e-6 and found[g]["held"] == (True, True, True)
                            and not found[g]["bearing"] for g in walls), [found[g]["held"] for g in walls])
        self.assertEqual(found[garden]["held"], (False, False, False))
        self.assertGreater(found[walls[0]]["openings"], 3.0)                   # (the door and the two windows)
        _m, _l, _a, designs = bim.design_structure(doc)
        checked = {e.guid: e for e in designs if e.kind == "wall"}
        self.assertEqual(set(checked), set(walls) | {garden})
        self.assertTrue(all(checked[g].design.status == ec2.OK for g in walls),
                        [(checked[g].design.ratio, [n.code for n in checked[g].design.notes]) for g in walls])
        self.assertTrue(all(design_text.masonry(checked[g]) for g in walls))
        self.assertEqual(checked[garden].design.status, ec2.FAIL)
        self.assertEqual(design_text.main_note(checked[garden].design).values["edges"], "base")
        wind = next(n for n in checked[walls[0]].design.notes if n.code == "ec6_wind").values
        self.assertGreater(wind["open"], 1.2)                                  # (its openings' wind on it…)
        self.assertTrue(any(n.code == "ec6_wind_solid" for n in checked[walls[1]].design.notes))   # (…none)
        self.assertEqual(bim.make_rebars(doc, designs), (0, 0))                # (masonry: no bars)
        page = structure_report.report_html(bim.report_data(doc))
        self.assertIn("fxk1", page)
        self.assertIn(doc.get(garden).name, page)

    def test_masonry_by_type(self):
        """0.346: the 20 cm wall type given masonry of its own — concrete units of group 1, fb 15, mortar M10 — kept in
        its IfcWallType's parameter, read back (after reopening too); a house of four load-bearing walls of it on strip
        footings with a slab, a 15 cm garden wall of the project's masonry: each checked with its own (the notes say
        whose; fk 0,55 × 15^0,7 × 10^0,3 against the project's 3,66), the summary's fk a range, the report naming the
        type; set back to the project's: its parameter empty, its walls the project's."""
        import tempfile
        import ifcopenshell
        import ifcopenshell.util.element as ue2
        from arqbim.core import actions, ec6
        from arqbim.i18n import t
        from arqbim.ifc import catalog as cat
        from arqbim.model import design_text, project_types, structure_report
        doc = Document()
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (6.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        walls = bim.add_wall_loop(doc, corners, cat.BY_KEY["parede_alv_20"])
        strip = cat.BY_KEY["sapata_corrida_50"]
        for g in walls:
            bim.set_property(doc, g, "Pset_WallCommon", "LoadBearing", True)
            bim.add_footing(doc, bim.footing_place(doc, g, strip), strip, under=g)
        top = float(doc.get(walls[0]).mesh.bounds()[1][2])
        bim.add_slab(doc, np.array((0.0, 0.0, top)), 6.0, 4.0, cat.BY_KEY["laje_15"])
        garden = bim.add_wall(doc, np.array((10.0, 0.0, 0.0)), np.array((14.0, 0.0, 0.0)), cat.BY_KEY["parede_alv_15"])
        spec = cat.BY_KEY["parede_alv_20"]
        concrete = ("concrete", "1", 15.0, "M10")
        bim.save_type(doc, dataclasses.replace(spec, masonry=concrete), spec)
        type_ = ue2.get_type(doc.ifc.by_guid(walls[0]))
        self.assertEqual(doc.ifc._params(type_)["Alvenaria"], "unit=concrete;group=1;fb=15;mortar=M10")
        self.assertEqual({s.key: s for s in project_types.read(doc.ifc)}["parede_alv_20"].masonry, concrete)
        path = os.path.join(tempfile.mkdtemp(), "alvenaria.ifc")
        doc.ifc.file.write(path)
        reopened = ifcopenshell.open(path)
        again = next(x for x in reopened.by_type("IfcWallType") if x.Name == type_.Name)
        self.assertEqual(project_types.read_type(doc.ifc, again, "wall").masonry, concrete)
        self.assertEqual({w.guid: w.masonry for w in bim.structural_walls(doc)}, {g: concrete for g in walls})
        _m, _l, _a, designs = bim.design_structure(doc)
        by = {e.guid: e for e in designs if e.kind == "wall"}
        fk_own = 0.55 * 15.0 ** 0.7 * 10.0 ** 0.3
        for g in walls:
            material = next(n for n in by[g].design.notes if n.code == "ec6_material").values
            self.assertEqual((material["unit"], material["src"], material["mortar"]), ("concrete", "type", "M10"))
            self.assertAlmostEqual(material["fk"], fk_own)
        flexural = next(n for n in by[garden].design.notes if n.code == "ec6_flexural").values
        self.assertEqual((flexural["unit"], flexural["src"]), ("clay", "project"))
        self.assertTrue(all(design_text.note_text(n) for e in by.values() for n in e.design.notes))
        settings = doc.ifc.structural_settings()
        self.assertEqual(design_text.masonry_fk(designs, settings),
                         t("ec6.fk_range", a=design_text.num(ec6.strength(actions.Settings())[0], 2),
                           b=design_text.num(fk_own, 2)))
        data = bim.report_data(doc)
        self.assertEqual(data["masonry_types"], [(type_.Name, concrete)])
        self.assertIn(type_.Name, structure_report.report_html(data))
        # back to the project's
        bim.save_type(doc, dataclasses.replace(spec, masonry=None), dataclasses.replace(spec, masonry=concrete))
        type_ = ue2.get_type(doc.ifc.by_guid(walls[0]))
        self.assertFalse(doc.ifc._params(type_).get("Alvenaria"))             # (none: the project's)
        self.assertIsNone({s.key: s for s in project_types.read(doc.ifc)}.get("parede_alv_20"))
        self.assertTrue(all(w.masonry is None for w in bim.structural_walls(doc)))


class StructuralActionsIfc(unittest.TestCase):
    """0.164: the frame of 0.163 with a 15 cm slab on it, its settings changed (C30/37, wind zone B): kept in the
    building and read back; the load cases G and Q in the IFC, loading the analysis model — the slab's planar
    forces (G 5,25 kN/m²: its weight 3,75 and finishes 1,5 — a roof, no partitions; Q 0,4), each member's weight;
    valid IFC; the storey's seismic weight: the slab, the beams, the columns' upper halves; its forces."""

    def test_actions(self):
        from arqbim.core import actions
        doc = Document()
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        for x, y in corners:
            bim.add_column(doc, np.array((x, y, 0.0)), catalog.BY_KEY["pilar_20"], 3.0)
        bim.footings_under(doc, None, catalog.BY_KEY["sapata_120"])
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            bim.add_beam(doc, np.array((*a, 3.0)), np.array((*b, 3.0)), catalog.BY_KEY["viga_20x40"], 3.0)
        storey = bim.add_storey(doc, "Piso 1", 3.0) if hasattr(bim, "add_storey") else None
        bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 6.0, 4.0, catalog.BY_KEY["laje_15"], storey=storey)
        settings = actions.Settings(concrete="C30/37", wind_zone="B")
        model, loads = bim.structural_actions(doc, settings)
        back = doc.ifc.structural_settings()
        self.assertEqual((back.concrete, back.wind_zone, back.terrain), ("C30/37", "B", "III"))
        analysis = doc.ifc.analysis_models()[0]
        self.assertEqual(sorted(c.Name for c in analysis.LoadedBy), ["G", "Q"])
        g = next(c for c in analysis.LoadedBy if c.Name == "G")
        acts = [o for rel in g.IsGroupedBy for o in rel.RelatedObjects]
        planar = [a for a in acts if a.is_a("IfcStructuralPlanarAction")]
        self.assertEqual(len(planar), 1)
        self.assertAlmostEqual(planar[0].AppliedLoad.PlanarForceZ, -(0.15 * 25 + 1.5) * 1000.0, places=3)
        self.assertEqual(sum(1 for a in acts if a.is_a("IfcStructuralCurveAction")), 8)
        self.assertEqual(doc.ifc.validate(), [])
        self.assertEqual(len(loads.storeys), 1)
        st = loads.storeys[0]
        slab = (0.15 * 25 + 1.5) * 24.0
        beams = 0.2 * 0.4 * 25 * 20.0
        columns = 0.2 * 0.2 * 25 * 3.0 * 4 / 2
        self.assertAlmostEqual(st.weight, slab + beams + columns, delta=0.5)
        self.assertGreater(st.wind_x, 0)
        self.assertGreater(loads.base_1, 0)
        self.assertEqual(len(model.panels), 1)

    def test_results_in_ifc(self):
        """0.221: the frame analysed and its results saved: a load combination 1,35G+1,50Q (G 1,35 and Q 1,50 by
        factor), a result group for it (first order, linear) as the analysis model's result, a reaction at each of
        the 4 supports (their vertical sum the analysis's), each member's moments along it (11 values at their
        lengths); valid IFC with its rules; saved again: one set; undone: none."""
        doc = Document()
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        for x, y in corners:
            bim.add_column(doc, np.array((x, y, 0.0)), catalog.BY_KEY["pilar_20"], 3.0)
        bim.footings_under(doc, None, catalog.BY_KEY["sapata_120"])
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            bim.add_beam(doc, np.array((*a, 3.0)), np.array((*b, 3.0)), catalog.BY_KEY["viga_20x40"], 3.0)
        bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 6.0, 4.0, catalog.BY_KEY["laje_15"])
        analysis = bim.save_analysis_results(doc)
        self.assertEqual(analysis.error, "")
        f = doc.ifc.file
        model = doc.ifc.analysis_models()[0]
        (group,) = model.HasResults
        self.assertEqual((group.TheoryType, group.IsLinear), ("FIRST_ORDER_THEORY", True))
        combo = group.ResultForLoadGroup
        self.assertEqual((combo.PredefinedType, combo.Name), ("LOAD_COMBINATION", "1,35G+1,50Q"))
        factors = {r.RelatedObjects[0].Name: r.Factor for r in combo.IsGroupedBy
                   if r.is_a("IfcRelAssignsToGroupByFactor")}
        self.assertEqual(factors, {"G": 1.35, "Q": 1.5})
        reactions = [o for rel in group.IsGroupedBy for o in rel.RelatedObjects]
        points = [o for o in reactions if o.is_a("IfcStructuralPointReaction")]
        curves = [o for o in reactions if o.is_a("IfcStructuralCurveReaction")]
        self.assertEqual((len(points), len(curves)), (4, 8))
        up = sum(p.AppliedLoad.ForceZ for p in points) / 1000.0
        self.assertAlmostEqual(up, sum(r[2] for r in analysis.reactions.values()), places=3)
        self.assertEqual(len(curves[0].AppliedLoad.Values), 11)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.save_analysis_results(doc)
        self.assertEqual(len(f.by_type("IfcStructuralResultGroup")), 1)
        self.assertEqual(len(f.by_type("IfcStructuralPointReaction")), 4)
        doc.undo()
        doc.undo()
        self.assertEqual(f.by_type("IfcStructuralResultGroup"), ())

    def test_slab_use(self):
        """0.218: a slab's own use — the frame's roof slab marked storage (E1, 7,5 kN/m²): its imposed load and its
        storey's seismic weight with it (ψ2 0,8); back to the project's: 0,4; kept in the IFC; undone, gone."""
        from arqbim.core import actions
        doc = Document()
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        for x, y in corners:
            bim.add_column(doc, np.array((x, y, 0.0)), catalog.BY_KEY["pilar_20"], 3.0)
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            bim.add_beam(doc, np.array((*a, 3.0)), np.array((*b, 3.0)), catalog.BY_KEY["viga_20x40"], 3.0)
        slab = bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 6.0, 4.0, catalog.BY_KEY["laje_15"])
        settings = actions.Settings()
        _m, before = bim.actions_of(doc, settings)
        self.assertAlmostEqual(before.panel_q[slab], 0.4)
        bim.set_slab_use(doc, [slab], "E1")
        self.assertEqual(doc.ifc.slab_use(slab), "E1")
        self.assertEqual(doc.ifc.describe(slab)["params"]["use"], "E1")
        _m, after = bim.actions_of(doc, settings)
        self.assertAlmostEqual(after.panel_q[slab], 7.5)
        self.assertAlmostEqual(after.storeys[0].weight - before.storeys[0].weight, 0.8 * 7.5 * 24.0, delta=0.01)
        self.assertEqual(doc.ifc.validate(), [])
        doc.undo()
        self.assertEqual(doc.ifc.slab_use(slab), "")
        _m, back = bim.actions_of(doc, settings)
        self.assertAlmostEqual(back.panel_q[slab], 0.4)


class ReinforcementIfc(unittest.TestCase):
    """0.166: the frame of 0.164 checked by Eurocode 2 (all OK) and its reinforcement put in the model in one step:
    IfcReinforcingBars (MAIN, SHEAR, LIGATURE) of Ø in mm, as many swept disks as bars, their position (Tag) shared by
    equal bars, ribbed A500 NR steel, their count and weight (kg: the project gets its mass unit); the members'
    concrete pset and pitches; valid IFC. A beam made deeper: its bars laid out again on it (longer stirrups); removed:
    its bars go with it; undone, back. The bar schedule's totals are its rows'."""

    def test_rebars(self):
        import ifcopenshell.util.element as ue
        from arqbim.core import ec2
        doc = Document()
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        for x, y in corners:
            bim.add_column(doc, np.array((x, y, 0.0)), catalog.BY_KEY["pilar_30"], 3.0)
        bim.footings_under(doc, None, catalog.BY_KEY["sapata_120"])
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            bim.add_beam(doc, np.array((*a, 3.0)), np.array((*b, 3.0)), catalog.BY_KEY["viga_20x40"], 3.0)
        storey = bim.add_storey(doc, "Piso 1", 3.0) if hasattr(bim, "add_storey") else None
        bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 6.0, 4.0, catalog.BY_KEY["laje_15"], storey=storey)
        _model, _loads, analysis, designs = bim.design_structure(doc)
        self.assertEqual(analysis.error, "")
        self.assertEqual(sorted(e.kind for e in designs), ["beam"] * 4 + ["column"] * 4 + ["footing"] * 4 + ["slab"])
        self.assertTrue(all(e.design.status == ec2.OK for e in designs))
        members, bars = bim.make_rebars(doc, designs)
        self.assertEqual(members, 13)
        rebars = doc.ifc.file.by_type("IfcReinforcingBar")
        self.assertEqual(sorted({r.PredefinedType for r in rebars}), ["LIGATURE", "MAIN", "SHEAR"])
        total = 0
        for r in rebars:
            psets = ue.get_psets(r)
            count = psets["Qto_ReinforcingElementBaseQuantities"]["Count"]
            body = [rep for rep in r.Representation.Representations if rep.RepresentationIdentifier == "Body"][0]
            self.assertEqual(body.RepresentationType, "AdvancedSweptSolid")
            self.assertEqual(len(body.Items), count)
            self.assertAlmostEqual(body.Items[0].Radius * 2, r.NominalDiameter, places=6)
            self.assertIn(r.NominalDiameter, (8.0, 12.0))
            self.assertEqual(psets["Pset_ReinforcingBarCommon"]["Reference"], r.Tag)
            self.assertEqual(ue.get_material(r).Name, "Aço A500 NR")
            total += count
        self.assertEqual(total, bars)
        units = doc.ifc.file.by_type("IfcUnitAssignment")[0].Units
        self.assertTrue(any(getattr(u, "UnitType", None) == "MASSUNIT" for u in units))
        beams = sorted(o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcBeam")
        stirrups = lambda g: next(doc.ifc.by_guid(x) for x in doc.ifc.rebars_of([g])[g]      # noqa: E731
                                  if doc.ifc.by_guid(x).PredefinedType == "SHEAR")
        self.assertEqual(ue.get_psets(doc.ifc.by_guid(beams[0]))["Pset_ConcreteElementGeneral"]["StrengthClass"],
                         "C25/30")
        self.assertIn("Pset_ReinforcementBarPitchOfBeam", ue.get_psets(doc.ifc.by_guid(beams[0])))
        tags = {}
        for r in rebars:
            key = (r.NominalDiameter, round(r.BarLength), doc.ifc._params(r)["Dobragem"])
            tags.setdefault(key, set()).add(r.Tag)
        self.assertTrue(all(len(v) == 1 for v in tags.values()))         # (equal bars: one position)
        # (0.224) the slab's top bars over its four edge beams: both ways, at its top, bent down into the beams
        slab = next(o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcSlab")
        roles = {doc.ifc._params(doc.ifc.by_guid(g))["Funcao"] for g in doc.ifc.rebars_of([slab])[slab]}
        self.assertEqual(roles, {"mesh_x", "mesh_y", "top_x", "top_y"})
        top_bar = next(doc.ifc.by_guid(g) for g in doc.ifc.rebars_of([slab])[slab]
                       if doc.ifc._params(doc.ifc.by_guid(g))["Funcao"] == "top_x")
        self.assertEqual(ue.get_psets(top_bar)["Pset_ReinforcingBarCommon"]["BendingShapeCode"], "11")
        self.assertIn("superior X sobre os apoios", top_bar.Name)
        self.assertEqual(doc.ifc.validate(), [])
        self.assertTrue(all(any(o.id == r.GlobalId for o in doc.objects.values()) for r in rebars))
        # (0.285) each member aggregates its bars (IfcRelAggregates): parts of it, in its storey, not contained there
        for r in rebars:
            whole = ue.get_aggregate(r)
            self.assertEqual(whole.GlobalId, doc.ifc._params(r)["Armadura"])
            self.assertIsNone(ue.get_container(r, should_get_direct=True))
            self.assertEqual(doc.ifc.storey_of(r.GlobalId), doc.ifc.storey_of(whole.GlobalId))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        # a beam made deeper: its stirrups laid out again on it, longer
        before = stirrups(beams[0]).BarLength
        bim.set_type(doc, beams[0], catalog.BY_KEY["viga_20x50"])
        self.assertAlmostEqual(stirrups(beams[0]).BarLength - before, 200.0, delta=1.0)
        self.assertEqual(len(doc.ifc.by_guid(beams[0]).IsDecomposedBy), 1)       # (laid out again: one aggregation)
        # removed: its bars too; undone, back
        n = len(doc.ifc.rebars_of([beams[1]])[beams[1]])
        bim.delete(doc, [beams[1]])
        self.assertEqual(doc.ifc.rebars_of([beams[1]]), {})
        doc.undo()
        self.assertEqual(len(doc.ifc.rebars_of([beams[1]])[beams[1]]), n)
        rows, totals = bim.rebar_schedule(doc)
        self.assertAlmostEqual(sum(kg for _m, kg in totals.values()), sum(r["weight"] for r in rows), places=6)
        self.assertEqual(sorted(totals), [8, 12])
        self.assertTrue(bim.remove_rebars(doc))
        self.assertEqual(len(doc.ifc.file.by_type("IfcReinforcingBar")), 0)


class StructureReportIfc(unittest.TestCase):
    """0.167: the frame of 0.166 with its reinforcement: each member's concrete is its shape's volume (a 30 × 30
    column 3 m tall: 0,27 m³), its formwork, its steel the bars' weight in the model (the bar schedule's total); the
    calculation report has its nine sections, every member, the project's name from the title block, and says who
    signs; without reinforcement the steel is told missing."""

    def test_report(self):
        from arqbim.model import structure_report
        doc = Document()
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        for x, y in corners:
            bim.add_column(doc, np.array((x, y, 0.0)), catalog.BY_KEY["pilar_30"], 3.0)
        bim.footings_under(doc, None, catalog.BY_KEY["sapata_120"])
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            bim.add_beam(doc, np.array((*a, 3.0)), np.array((*b, 3.0)), catalog.BY_KEY["viga_20x40"], 3.0)
        bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 6.0, 4.0, catalog.BY_KEY["laje_15"])
        rows = bim.structure_quantities(doc)
        self.assertEqual(sorted(r.kind for r in rows), ["beam"] * 4 + ["column"] * 4 + ["footing"] * 4 + ["slab"])
        self.assertFalse(any(r.has_bars for r in rows))
        column = next(r for r in rows if r.kind == "column")
        self.assertAlmostEqual(column.concrete, 0.3 * 0.3 * 3.0, places=4)
        self.assertAlmostEqual(column.formwork, 3.6, places=6)
        _m, _l, _a, designs = bim.design_structure(doc)
        bim.make_rebars(doc, designs)
        rows = bim.structure_quantities(doc)
        self.assertTrue(all(r.has_bars for r in rows))
        _rows, totals = bim.rebar_schedule(doc)
        self.assertAlmostEqual(sum(r.steel for r in rows), sum(kg for _m, kg in totals.values()), places=6)
        doc.title_block = {"project": "Moradia T3", "client": "Dono de obra"}
        page = structure_report.report_html(bim.report_data(doc))
        self.assertTrue(page.startswith("<!doctype html>") and page.endswith("</html>"))
        for k in range(1, 10):
            self.assertIn("<h2>{}. ".format(k), page)
        self.assertIn("Moradia T3", page)
        for o in doc.objects.values():
            if o.is_bim and o.ifc_class in ("IfcColumn", "IfcBeam", "IfcFooting", "IfcSlab"):
                self.assertIn(o.name, page)
        self.assertIn("assina", page)
        self.assertIn("C25/30", page)
        self.assertIn("2.ª ordem: θ máximo", page)                        # (0.222: the storeys' sways)
        self.assertIn("EC8 4.3.1(7)", page)
        self.assertIn("elementos finitos triangulares DKT", page)          # (0.223: the slab as shells)
        self.assertIn("calculada como casca", page)
        self.assertIn("Desenhos de armaduras (1:50; cortes 1:20)", page)   # (0.233: each member's drawing in it)
        self.assertEqual(page.count("<svg"), 13 + 12 + 1)                  # (0.234: and its section, but a slab's;
        self.assertEqual(page.count("<figure>"), 13 + 1)                   # 0.237: the typical details, last)
        self.assertIn("<figcaption>Pormenores tipo de armaduras</figcaption>", page)
        for o in doc.objects.values():
            if o.is_bim and o.ifc_class in ("IfcColumn", "IfcBeam", "IfcFooting", "IfcSlab"):
                self.assertIn("<figcaption>{}</figcaption>".format(o.name), page)


class DrawingSvg(unittest.TestCase):
    """0.233: a drawing as SVG at 1:50 — its size the drawing's on paper plus its margins (a 6 m line: 120 mm), its
    lines, its polylines with their pens, its texts, its dimensions (their lines, ticks and text); an empty one
    nothing."""

    def test_svg(self):
        from arqbim.model import drawing_svg
        from arqbim.model.drawings import Drawing
        d = Drawing("x")
        d.lines = np.array((((0.0, 0.0), (6.0, 0.0)), ((0.0, 0.0), (0.0, 0.5))))
        d.annotations = [("polyline", [(np.array(((0.5, 0.1), (5.5, 0.1))), False)], "none", "",
                          np.array((0.5, 0.1)), 2.5, "continuous", 0.5),
                         ("text", [], "none", "2 Ø12 — pos. 1", np.array((0.0, -0.2)), 2.5, "continuous", None)]
        d.dims = [(np.array((0.0, 0.0)), np.array((6.0, 0.0)), np.array((0.0, -0.5)), np.array((6.0, -0.5)),
                   "6,00")]
        text = drawing_svg.svg(d, 50)
        self.assertTrue(text.startswith("<svg") and text.endswith("</svg>"))
        width = float(text.split('width="')[1].split("mm")[0])
        self.assertAlmostEqual(width, 6.0 * 1000 / 50 + 2 * drawing_svg.MARGIN, places=1)
        self.assertIn('stroke-width="0.5"', text)
        self.assertIn("2 Ø12 — pos. 1", text)
        self.assertIn(">6,00</text>", text)
        self.assertGreaterEqual(text.count("<path"), 2 + 1 + 5)          # (lines, the bar, the dimension's five)
        self.assertEqual(drawing_svg.svg(Drawing("vazio")), "")


class RebarDrawingsIfc(unittest.TestCase):
    """0.168: the reinforcement drawing of each member of the frame of 0.166, from its bars in the IFC — a beam's
    elevation (its outline, a heavy line for each bar, a thin one for each stirrup) and its section A–A (the bars
    cut as dots: 2 + 2), its labels with the positions; a column's, a footing's (its mesh's bars, both ways), a
    slab's; none for a member without bars."""

    def test_drawings(self):
        from arqbim.model import drawings, rebar_drawings
        doc = Document()
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        for x, y in corners:
            bim.add_column(doc, np.array((x, y, 0.0)), catalog.BY_KEY["pilar_30"], 3.0)
        bim.footings_under(doc, None, catalog.BY_KEY["sapata_120"])
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            bim.add_beam(doc, np.array((*a, 3.0)), np.array((*b, 3.0)), catalog.BY_KEY["viga_20x40"], 3.0)
        bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 6.0, 4.0, catalog.BY_KEY["laje_15"])
        beam = sorted(o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcBeam")[0]
        self.assertIsNone(drawings.of_view(doc, "rebar", beam, "x"))
        bim.make_rebars(doc, bim.design_structure(doc)[3])
        d = drawings.of_view(doc, "rebar", beam, "Viga")
        self.assertIsNotNone(d)
        self.assertEqual(len(d.lines), 4)                              # (its elevation's outline: 0.234, alone)
        texts = [dim[4] for dim in d.dims]                             # (0.232: its dimensions, real sizes)
        start, end, _top, _w, _h = doc.ifc.beam_params(beam)
        length = float(np.linalg.norm((end - start)[:2]))
        self.assertIn("{:.2f}".format(length).replace(".", ","), texts)
        self.assertIn("0,40", texts)
        polylines = [a for a in d.annotations if a[0] == "polyline"]
        sets = rebar_drawings.sets_of(doc, beam)
        bars = sum(len(b) for r, b in sets if r["role"] != "stirrups")
        stirrups = sum(len(b) for r, b in sets if r["role"] == "stirrups")
        self.assertEqual(len(polylines), bars + stirrups + 2)          # (0.236: and where A-A is cut, over and under)
        texts = [a[3] for a in d.annotations if a[0] == "text"]
        self.assertTrue(any("pos." in x for x in texts))
        self.assertEqual(texts.count("A"), 2)
        marks = [a[1][0][0] for a in polylines if a[7] == rebar_drawings.MARK_PEN]
        self.assertEqual(len(marks), 2)
        self.assertTrue(all(np.allclose(m[:, 0], length / 2) for m in marks))
        lo, hi = d.bounds()
        self.assertLess(hi[0] - lo[0], length + 1.0)                   # (0.234: its section no longer beside it)
        self.assertLess(lo[1], min(dim[2][1] for dim in d.dims) - 0.05)   # (…and room for its dimensions' texts)
        # (0.234) its section A–A, a view of its own at its real size: the stirrup, each bar cut at mid-span, its sides
        cd = drawings.of_view(doc, "rebar_cut", beam, "Viga")
        self.assertEqual(len(cd.lines), 4)
        clo, chi = cd.lines.reshape(-1, 2).min(axis=0), cd.lines.reshape(-1, 2).max(axis=0)
        self.assertTrue(np.allclose(chi - clo, (0.20, 0.40)))
        self.assertEqual(sum(1 for a in cd.annotations if a[0] == "polyline"), 1)
        self.assertEqual(sum(1 for a in cd.annotations if a[0] == "region"), bars)
        self.assertEqual(sorted(dim[4] for dim in cd.dims), ["0,20", "0,40"])
        self.assertTrue(all(abs(np.linalg.norm(dim[1] - dim[0]) - v) < 1e-6 for dim, v in zip(cd.dims, (0.2, 0.4))))
        self.assertFalse(any(a[0] == "text" for a in cd.annotations))  # (its name is the sheet's label)
        self.assertTrue(rebar_drawings.has_cut(doc, beam))
        sizes = {"IfcColumn": (("3,00",), ("0,30",)), "IfcFooting": (("1,20",), ("1,20", "0,50")),
                 "IfcSlab": (("6,00", "4,00"), ())}
        for cls in ("IfcColumn", "IfcFooting", "IfcSlab"):
            g = next(o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == cls)
            dd = drawings.of_view(doc, "rebar", g, cls)
            self.assertIsNotNone(dd, cls)
            self.assertTrue(any(a[0] == "polyline" for a in dd.annotations), cls)
            own, cut = sizes[cls]
            for text in own:                                           # (0.232)
                self.assertIn(text, [dim[4] for dim in dd.dims], cls)
            cc = drawings.of_view(doc, "rebar_cut", g, cls)
            self.assertEqual(cc is None, cls == "IfcSlab", cls)        # (a slab: no section)
            letter = {"IfcColumn": "B", "IfcFooting": "C"}.get(cls)  # (0.236: where it is cut, marked)
            self.assertEqual([a[3] for a in dd.annotations if a[0] == "text"].count(letter), 2 if letter else 0, cls)
            for text in cut:
                self.assertIn(text, [dim[4] for dim in cc.dims], cls)
        slab = next(o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcSlab")
        sd_ = drawings.of_view(doc, "rebar", slab, "L")                 # (0.224: its top bars told and drawn heavier)
        self.assertTrue(any("sup." in a[3] for a in sd_.annotations if a[0] == "text"))
        self.assertGreater(len({a[7] for a in sd_.annotations if a[0] == "polyline"}), 1)
        foot = next(o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcFooting")
        fd = drawings.of_view(doc, "rebar_cut", foot, "S")
        self.assertEqual(sum(1 for a in fd.annotations if a[0] == "region"), 7)      # (the bars across its section)
        self.assertEqual(rebar_drawings.cut_letter(doc, foot), "C")
        # (0.234) on a sheet: the elevation at 1:50, its section at 1:20 — kept in the file, read back
        from arqbim.model import sheets as sheets_model
        k, _j = doc.put_on_sheet(None, "rebar", beam, (("rebar_cut", beam),))
        sheet = doc.sheets[k]
        self.assertEqual([(v.kind, v.ref) for v in sheet.views], [("rebar", beam), ("rebar_cut", beam)])
        frames = sheets_model.layout(sheet, [sheets_model.extent(d), sheets_model.extent(cd)])
        self.assertEqual([f.scale for f in frames], [50, 20])
        again = sheets_model.from_dict(sheets_model.to_dict(sheet))
        self.assertEqual([(v.kind, v.ref) for v in again.views], [("rebar", beam), ("rebar_cut", beam)])
        doc.undo()
        self.assertEqual(len(doc.sheets), k)                           # (one step)
        # the structure plan: cut under the slab — the columns and beams cut, the slab dashed over, all tagged
        storey = doc.ifc.storeys()[0][0]
        sp = drawings.of_view(doc, "structure", storey, "Estrutura")
        self.assertGreaterEqual(len(sp.cut), 8)
        self.assertEqual(len(sp.above), 1)
        tags = sorted(a[3] for a in sp.annotations if a[0] == "text")
        for tag in ("P1 30×30", "V1 20×40", "L1 h = 0,15", "S1 1,20×1,20"):
            self.assertIn(tag, tags)
        self.assertEqual(rebar_drawings.short_tag("Pilar 12"), "P12")
        # (0.235) its formwork seen from below: cut under the beams (only the four columns cut), the beams' soffits
        # seen — a beam along Y has its edges at x = ±0,10 —, the slab tagged; no footing (under the cut)
        sb = drawings.of_view(doc, "structure_below", storey, "Cofragem")
        self.assertEqual(len(sb.cut), 4)
        self.assertEqual(sb.above, [])
        along_y = [s for s in sb.lines if abs(s[0][0] - s[1][0]) < 1e-6 and abs(s[0][1] - s[1][1]) > 1.0]
        self.assertTrue(any(abs(abs(s[0][0]) - 0.10) < 1e-3 for s in along_y))
        tags = sorted(a[3] for a in sb.annotations if a[0] == "text")
        for tag in ("P1 30×30", "V1 20×40", "L1 h = 0,15"):
            self.assertIn(tag, tags)
        self.assertFalse(any(x.startswith("S") for x in tags))
        self.assertIsNone(drawings.of_view(doc, "structure_below", "nenhum", "x"))
        from arqbim.model import sheets as sheets_model
        self.assertIn("structure_below", sheets_model.KINDS)


class LabelsByHandIfc(unittest.TestCase):
    """0.238: a reinforcement drawing's labels and a structure plan's tags each with a key (a bar's role and
    position, a member's GlobalId); one moved by hand is the view's own property — the label drawn that far off,
    the view's extent not moved with it —, one undo step, back to its place with None, kept in the .arqbim file
    and read back; the calculation report draws it there too."""

    def test_labels(self):
        from arqbim.model import drawings
        from arqbim.model import view_templates as templates_model
        doc = Document()
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        for x, y in corners:
            bim.add_column(doc, np.array((x, y, 0.0)), catalog.BY_KEY["pilar_30"], 3.0)
        bim.footings_under(doc, None, catalog.BY_KEY["sapata_120"])
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            bim.add_beam(doc, np.array((*a, 3.0)), np.array((*b, 3.0)), catalog.BY_KEY["viga_20x40"], 3.0)
        bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 6.0, 4.0, catalog.BY_KEY["laje_15"])
        bim.make_rebars(doc, bim.design_structure(doc)[3])
        beam = sorted(o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcBeam")[0]
        view = ("rebar", beam)
        d = drawings.of_view(doc, "rebar", beam, "Viga")
        keys = [key for _i, key in d.movable]
        self.assertEqual(len(keys), len(set(keys)))                    # (each its own)
        self.assertTrue(any(key.startswith("top:") for key in keys))
        i, key = d.movable[0]
        where, box = np.array(d.annotations[i][4]), d.bounds()
        self.assertTrue(doc.move_label(view, key, (0.5, -0.3)))
        self.assertEqual(doc.view_settings(view).labels, {key: (0.5, -0.3)})
        moved = drawings.of_view(doc, "rebar", beam, "Viga")
        self.assertTrue(np.allclose(moved.annotations[i][4], where + (0.5, -0.3)))
        self.assertTrue(all(np.allclose(a, b) for a, b in zip(moved.bounds(), box)))   # (the view stays)
        doc.undo()
        self.assertFalse(doc.view_settings(view).labels)
        doc.redo()
        self.assertEqual(doc.view_settings(view).labels, {key: (0.5, -0.3)})
        # a structure plan's tag: by its member
        storey = doc.ifc.storeys()[0][0]
        sp = drawings.of_view(doc, "structure", storey, "Estrutura")
        j, tag = next((j, k) for j, k in sp.movable if k == beam)
        at, sbox = np.array(sp.annotations[j][4]), sp.bounds()
        doc.move_label(("structure", storey), tag, (0.0, 1.0))
        sp2 = drawings.of_view(doc, "structure", storey, "Estrutura")
        self.assertTrue(np.allclose(sp2.annotations[j][4], at + (0.0, 1.0)))
        self.assertTrue(all(np.allclose(a, b) for a, b in zip(sp2.bounds(), sbox)))
        doc.move_label(("structure", storey), tag, None)               # (back to its place)
        self.assertNotIn("labels", doc.view_props.get(("structure", storey), {}))
        # kept in the file
        self.assertEqual(templates_model.own_from_dict(templates_model.own_to_dict(doc.view_props[view]))["labels"],
                         {key: [0.5, -0.3]})
        from arqbim.model import drawing_svg
        name = doc.get(beam).name
        entry = dict(bim.report_data(doc)["drawings"])[name]
        self.assertTrue(entry.startswith(drawing_svg.svg(drawings.of_view(doc, "rebar", beam, name), 50)))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "rotulos.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        self.assertEqual(again.view_settings(view).labels, {key: (0.5, -0.3)})


class RebarDetailsIfc(unittest.TestCase):
    """0.237: the typical details of the frame of 0.166, from its bars — none before it has bars; the joint of the
    first beam (V1) on its column, their bars cut out of the model round it (none past its window), the column's
    width and the beam's top bars' bent leg dimensioned; a lap splice of each main diameter, l0 the model's
    (core.rebar.lap_length with its concrete and steel) told and dimensioned; on a sheet at 1:20."""

    def test_details(self):
        import json
        from arqbim.core import actions as act
        from arqbim.core import rebar as rb
        from arqbim.model import design_text as dt
        from arqbim.model import drawings, rebar_details
        from arqbim.model import sheets as sheets_model
        doc = Document()
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        for x, y in corners:
            bim.add_column(doc, np.array((x, y, 0.0)), catalog.BY_KEY["pilar_30"], 3.0)
        bim.footings_under(doc, None, catalog.BY_KEY["sapata_120"])
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            bim.add_beam(doc, np.array((*a, 3.0)), np.array((*b, 3.0)), catalog.BY_KEY["viga_20x40"], 3.0)
        bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 6.0, 4.0, catalog.BY_KEY["laje_15"])
        self.assertIsNone(drawings.of_view(doc, "rebar_details", "", "x"))
        bim.make_rebars(doc, bim.design_structure(doc)[3])
        d = drawings.of_view(doc, "rebar_details", "", "Pormenores")
        self.assertIsNotNone(d)
        texts = [a[3] for a in d.annotations if a[0] == "text"]
        self.assertTrue(any(x.startswith("Nó viga-pilar — V1 / P") for x in texts))
        self.assertIn("Emendas por sobreposição", texts)
        info = json.loads(doc.ifc._params(doc.ifc.file.by_type("IfcReinforcingBar")[0])["Projeto"])
        fck, fyk = act.CONCRETE[info["concrete"]], act.STEEL[info["steel"]]
        diameters = sorted({r["diameter"] for r in doc.ifc.rebar_rows() if r["role"] in rebar_details.MAIN})
        self.assertGreaterEqual(len(diameters), 1)
        dims = [dim[4] for dim in d.dims]
        for dia in diameters:
            l0 = dt.num(rb.lap_length(dia, fck, fyk), 2)
            self.assertIn("Ø{} — l0 = 1,5 × lb,rqd = {} m ({}, {})".format(dia, l0, info["concrete"], info["steel"]),
                          texts)
            self.assertIn(l0, dims)
        self.assertIn("0,30", dims)                                    # (the column across)
        self.assertGreaterEqual(len(d.dims), 2 + len(diameters))       # (…and the top bars' leg into it)
        back, along, under, over = rebar_details.WINDOW
        joint = [a[1][0][0] for a in d.annotations if a[0] == "polyline"][:-2 * len(diameters)]
        self.assertGreater(len(joint), 10)                             # (the beam's, the column's bars and links)
        pts = np.vstack(joint)
        self.assertLessEqual(pts[:, 0].max(), 0.15 + along + 1e-6)
        self.assertGreaterEqual(pts[:, 0].min(), -0.15 - back - 1e-6)
        self.assertLessEqual(pts[:, 1].max(), over + 1e-6)
        k, _j = doc.put_on_sheet(None, "rebar_details", "")
        frames = sheets_model.layout(doc.sheets[k], [sheets_model.extent(d)])
        self.assertEqual(frames[0].scale, 20)


class CabinetsIfc(unittest.TestCase):
    """0.169: a base unit against a wall — an IfcFurniture USERDEFINED «Móvel inferior», built in, its nominal sizes
    in Pset_FurnitureTypeCommon, one swept solid per panel, its back on the wall and its width along it; valid IFC.
    Made wider and given drawers: its body made again, its left corner where it was; a size out of range refused (the
    step undone); the cut list of the project's cabinets; read back from the file."""

    def test_cabinets(self):
        import ifcopenshell.util.element as ue
        from arqbim.core import cabinets as cab
        doc = Document()
        g = bim.add_cabinet(doc, np.array((1.0, 2.0, 0.0)), 0.0, cab.Cabinet.of("base", width=0.60))
        e = doc.ifc.by_guid(g)
        self.assertEqual((e.is_a(), e.PredefinedType, e.ObjectType), ("IfcFurniture", "USERDEFINED", "Móvel inferior"))
        common = ue.get_psets(e)["Pset_FurnitureTypeCommon"]
        self.assertTrue(common["IsBuiltIn"])
        self.assertAlmostEqual(common["NominalLength"], 600.0, places=6)
        self.assertAlmostEqual(common["NominalHeight"], 870.0, places=6)
        body = [r for r in e.Representation.Representations if r.RepresentationIdentifier == "Body"][0]
        self.assertEqual(len(body.Items), len([p for p in cab.layout(cab.Cabinet.of("base")).panels]))
        lo, hi = doc.get(g).mesh.bounds()
        np.testing.assert_allclose(lo[:2], (0.7, 2.0), atol=1e-6)            # (its back's middle at (1, 2))
        self.assertAlmostEqual(hi[2], 0.87, places=6)
        self.assertEqual(doc.ifc.validate(), [])
        bim.set_cabinet(doc, g, width=0.80, fronts="drawers", drawers=4)
        c = doc.ifc.cabinet_params(g)
        self.assertEqual((c.width, c.fronts, c.drawers), (0.80, "drawers", 4))
        lo2, hi2 = doc.get(g).mesh.bounds()
        self.assertAlmostEqual(lo2[0], 0.7, places=6)
        self.assertAlmostEqual(hi2[0] - lo2[0], 0.80, places=6)
        steps = len(doc._undo)
        with self.assertRaises(Exception):
            bim.set_cabinet(doc, g, width=3.0)
        self.assertEqual((len(doc._undo), doc.ifc.cabinet_params(g).width), (steps, 0.80))
        bim.add_cabinet(doc, np.array((1.0, 2.0, 0.0)), 0.0, cab.Cabinet.of("wall", width=0.80))
        rows, hardware, areas = bim.cut_list(doc)
        self.assertEqual(hardware["runner"], 4)
        self.assertIn("front", areas)
        # (0.172) a wardrobe, its compartments changed: kept in its parameters, its body made again
        wr = bim.add_cabinet(doc, np.array((3.0, 2.0, 0.0)), 0.0, cab.Cabinet.of("wardrobe"))
        self.assertEqual(doc.ifc.by_guid(wr).ObjectType, "Roupeiro")
        bim.set_cabinet(doc, wr, interior="rail,drawers,shelves", width=1.2)
        self.assertEqual(doc.ifc.cabinet_params(wr).compartments, ["rail", "drawers", "shelves"])
        bim.set_cabinet(doc, g, kind="tall")                           # (another kind: its usual sizes)
        self.assertAlmostEqual(doc.ifc.cabinet_params(g).height, 2.02, places=9)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "moveis.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            self.assertEqual(sorted(c.kind for c in again.ifc.cabinets().values()), ["tall", "wall", "wardrobe"])
            self.assertEqual(again.ifc.describe(g)["kind"], "cabinet")


class KitchensIfc(unittest.TestCase):
    """0.170: a kitchen in L made in one step — its base units, its wall units, its worktop (an
    IfcSystemFurnitureElement WORKSURFACE on them, at 90 cm); valid IFC. A base unit made narrower: the worktop
    follows; two removed: it shrinks; all removed: it goes too; undone, back. The cut list has its pieces."""

    def test_kitchen(self):
        doc = Document()
        made = bim.make_kitchen(doc, [(0.0, 0.0), (3.0, 0.0), (3.0, 2.4)], 1)
        self.assertEqual((len(made["base"]), len(made["wall"])), (7, 8))    # (0.239: a blind corner in each run)
        corner = doc.ifc.cabinet_params(made["base"][3])
        self.assertEqual((round(corner.width, 2), round(corner.blind, 3), corner.corner_side), (1.0, 0.631, "right"))
        self.assertEqual(sum(1 for g in made["wall"] if doc.ifc.cabinet_params(g).blind > 0), 1)
        self.assertEqual(sum(1 for g in made["base"] if doc.ifc.cabinet_params(g).blind > 0), 1)
        bim.set_cabinet(doc, made["base"][3], corner_side="left")
        self.assertEqual(doc.ifc.cabinet_params(made["base"][3]).corner_side, "left")
        bim.set_cabinet(doc, made["base"][3], blind=0.0)
        self.assertEqual(doc.ifc.cabinet_params(made["base"][3]).blind, 0.0)
        doc.undo()
        doc.undo()
        self.assertEqual(doc.ifc.cabinet_params(made["base"][3]).corner_side, "right")
        top = doc.ifc.by_guid(made["worktop"])
        self.assertEqual((top.is_a(), top.PredefinedType), ("IfcSystemFurnitureElement", "WORKSURFACE"))
        lo, hi = doc.get(made["worktop"]).mesh.bounds()
        self.assertAlmostEqual(hi[2], 0.90, places=6)
        self.assertEqual(doc.ifc.validate(), [])
        area = lambda: doc.ifc.worktop_shape(made["worktop"])[1]               # noqa: E731
        before = sum(a * b for a, b in area())
        bim.set_cabinet(doc, made["base"][6], width=0.40)          # (the second leg's last: it ends 20 cm sooner)
        after = sum(a * b for a, b in area())
        self.assertAlmostEqual(before - after, 0.20 * (doc.ifc.cabinet_params(made["base"][6]).overall_depth + 0.02),
                               places=6)
        bim.delete(doc, made["base"][:2])
        self.assertEqual(len(doc.ifc.worktop_hosts(made["worktop"])), 5)
        bim.delete(doc, made["base"][2:])
        self.assertIsNone(doc.ifc.by_guid(made["worktop"]))
        doc.undo()
        self.assertIsNotNone(doc.ifc.by_guid(made["worktop"]))
        rows, _hw, _areas = bim.cut_list(doc)
        self.assertEqual(sum(1 for r in rows if r[0] == "worktop"), 2)


class KitchenCornersIfc(unittest.TestCase):
    """0.240: a kitchen in L with an L corner and its carousel — the base corner unit's arm 90 cm (its trays three
    quarters of a disc: an arbitrary profile), the wall one's 65 cm; the worktop over both runs, its second piece
    from the first's edge; the carousel among the hardware, not in the cut list; valid IFC. Its arm taken away: a
    straight unit again (its carousel refused, the step undone)."""

    def test_l_corners(self):
        from arqbim.ifc.edit import EditRefused
        doc = Document()
        made = bim.make_kitchen(doc, [(0.0, 0.0), (3.0, 0.0), (3.0, 2.4)], 1, corner="carousel")
        corner = [g for g in made["base"] if doc.ifc.cabinet_params(g).arm > 0]
        self.assertEqual(len(corner), 1)
        c = doc.ifc.cabinet_params(corner[0])
        self.assertEqual((round(c.arm, 2), c.corner_side, c.interior), (0.9, "right", "carousel"))
        self.assertEqual([round(doc.ifc.cabinet_params(g).arm, 2) for g in made["wall"]
                          if doc.ifc.cabinet_params(g).arm], [0.65])
        body = [r for r in doc.ifc.by_guid(corner[0]).Representation.Representations
                if r.RepresentationIdentifier == "Body"][0]
        self.assertEqual(sum(1 for i in body.Items if i.SweptArea.is_a("IfcArbitraryClosedProfileDef")), 2)
        self.assertEqual(doc.ifc.validate(), [])
        outline, pieces, _top, _t = doc.ifc.worktop_shape(made["worktop"])
        self.assertEqual(len(outline), 6)
        self.assertEqual(len(pieces), 2)
        rows, hardware, _areas = bim.cut_list(doc)
        self.assertEqual(hardware.get("carousel"), 1)
        self.assertFalse(any(r[0] == "carousel" for r in rows))
        with self.assertRaises(EditRefused):
            bim.set_cabinet(doc, corner[0], arm=0.0)              # (a carousel without its L: refused)
        self.assertAlmostEqual(doc.ifc.cabinet_params(corner[0]).arm, 0.9, places=6)


class SlidingDoorsIfc(unittest.TestCase):
    """0.241: a wardrobe of 2,40 m with three sliding doors in the IFC — its nominal depth out to its tracks, valid
    IFC; its doors in the cut list, its track set among the hardware; given hinged doors: back to its door's depth;
    one of 2,80 m refused."""

    def test_sliding(self):
        from arqbim.core import cabinets as cab
        from arqbim.ifc.edit import EditRefused
        doc = Document()
        g = bim.add_cabinet(doc, np.array((1.5, 0.0, 0.0)), 0.0, cab.Cabinet.of("wardrobe", width=2.40,
                                                                                 fronts="sliding", doors=3))
        c = doc.ifc.cabinet_params(g)
        self.assertEqual((c.fronts, c.doors), ("sliding", 3))
        import ifcopenshell.util.element as ue
        common = ue.get_psets(doc.ifc.by_guid(g))["Pset_FurnitureTypeCommon"]
        self.assertAlmostEqual(common["NominalDepth"] / 1000.0, c.overall_depth, places=6)     # (the file's mm)
        self.assertEqual(doc.ifc.validate(), [])
        rows, hardware, _areas = bim.cut_list(doc)
        self.assertEqual(sum(r[5] for r in rows if r[0] == "sliding_door"), 3)
        self.assertEqual(hardware.get("slide"), 1)
        bim.set_cabinet(doc, g, fronts="doors")
        self.assertAlmostEqual(doc.ifc.cabinet_params(g).overall_depth, cab.BACK + c.depth + cab.FRONT, places=9)
        with self.assertRaises(EditRefused):
            bim.set_cabinet(doc, g, width=2.80)


class OvenColumnIfc(unittest.TestCase):
    """0.242: a tall unit with an oven housing put — its oven made with it, in the same step (an IfcElectricAppliance
    ELECTRICCOOKER tied to it, at the housing's height, its door on the unit's fronts' face); the unit moved: the
    oven with it; given doors: the oven goes; undone: back; the unit deleted: the oven too; valid IFC."""

    def test_oven(self):
        from arqbim.core import cabinets as cab
        from arqbim.core.transform import translation

        def ovens():
            return [e for e in doc.ifc.file.by_type("IfcElectricAppliance")
                    if doc.ifc._params(e).get("Aparelho") == "oven_column"]

        doc = Document()
        g = bim.add_cabinet(doc, np.array((0.3, 0.0, 0.0)), 0.0, cab.Cabinet.of("tall", fronts="oven"))
        self.assertEqual(len(ovens()), 1)
        oven = ovens()[0]
        self.assertEqual(oven.PredefinedType, "ELECTRICCOOKER")
        self.assertEqual(doc.ifc._params(oven)["Hospedeiro"], g)
        lo, hi = doc.get(oven.GlobalId).mesh.bounds()
        self.assertAlmostEqual(lo[2], cab.OVEN_SILL, places=6)
        c = doc.ifc.cabinet_params(g)
        self.assertAlmostEqual(hi[1], cab.BACK + c.depth + 0.02, places=6)       # (its door over the fronts' face)
        self.assertEqual(doc.ifc.validate(), [])
        doc.undo()
        self.assertEqual(len(ovens()), 0)                                        # (one step with its unit)
        doc.redo()
        bim.transform_objects(doc, [g], translation((1.0, 0.0, 0.0)), "Mover")
        lo2, _hi2 = doc.get(ovens()[0].GlobalId).mesh.bounds()
        self.assertAlmostEqual(lo2[0] - lo[0], 1.0, places=6)
        bim.set_cabinet(doc, g, fronts="doors")
        self.assertEqual(len(ovens()), 0)
        doc.undo()
        self.assertEqual(len(ovens()), 1)
        bim.delete(doc, [g])
        self.assertEqual(len(ovens()), 0)


class FrontFinishesIfc(unittest.TestCase):
    """0.243: a base unit given fronts of white lacquer — its material a constituent set «Corpo» (the board) and
    «Frentes» (MDF lacado branco), shared by a second one; its fronts' items styled in that colour; its colour on
    screen that of the finish; valid IFC; back to melamine: its board alone again, no colour of its own."""

    def test_finishes(self):
        import ifcopenshell.util.element as ue
        from arqbim.core import cabinets as cab
        from arqbim.ifc import catalog
        doc = Document()
        a = bim.add_cabinet(doc, np.array((0.3, 0.0, 0.0)), 0.0, cab.Cabinet.of("base", finish="lacquer_white"))
        b = bim.add_cabinet(doc, np.array((0.9, 0.0, 0.0)), 0.0, cab.Cabinet.of("base"))
        bim.set_cabinet(doc, b, finish="lacquer_white")
        ma = ue.get_material(doc.ifc.by_guid(a), should_skip_usage=True)
        self.assertEqual(ma.is_a(), "IfcMaterialConstituentSet")
        self.assertEqual([(k.Name, k.Material.Name) for k in ma.MaterialConstituents],
                         [("Corpo", "Aglomerado melamínico"), ("Frentes", "MDF lacado branco")])
        self.assertEqual(ue.get_material(doc.ifc.by_guid(b), should_skip_usage=True).id(), ma.id())   # (shared)
        body = [r for r in doc.ifc.by_guid(a).Representation.Representations if r.RepresentationIdentifier == "Body"][0]
        styled = [i for i in body.Items if i.StyledByItem]
        lay = cab.layout(doc.ifc.cabinet_params(a))
        self.assertEqual(len(styled), sum(1 for p in lay.panels if p.material.startswith("front")))
        r, g, bb = catalog.MATERIALS["lacado_branco"].color
        self.assertEqual(doc.ifc.cabinet_colour(a), "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255),
                                                                                 round(bb * 255)))
        self.assertEqual(doc.ifc.validate(), [])
        bim.set_cabinet(doc, a, finish="melamine")
        self.assertEqual(ue.get_material(doc.ifc.by_guid(a), should_skip_usage=True).Name, "Aglomerado melamínico")
        self.assertIsNone(doc.ifc.cabinet_colour(a))


class CompartmentWidthsIfc(unittest.TestCase):
    """0.244: a wardrobe's division placed (its «Divisoes» kept and read back, its body made again — valid IFC); one
    leaving a compartment under 15 cm refused, the step undone; the compartments made three: even again."""

    def test_widths(self):
        from arqbim.core import cabinets as cab
        from arqbim.ifc.edit import EditRefused
        doc = Document()
        g = bim.add_cabinet(doc, np.array((0.6, 0.0, 0.0)), 0.0,
                            cab.Cabinet.of("wardrobe", width=1.20, interior="shelves,rail"))
        bim.set_cabinet(doc, g, splits="0.45")
        c = doc.ifc.cabinet_params(g)
        self.assertEqual(c.splits, "0.45")
        self.assertAlmostEqual(c.divisions[0], 0.45, places=9)
        self.assertEqual(doc.ifc.validate(), [])
        with self.assertRaises(EditRefused):
            bim.set_cabinet(doc, g, splits="1.15")
        self.assertEqual(doc.ifc.cabinet_params(g).splits, "0.45")
        bim.set_cabinet(doc, g, interior="shelves,rail,drawers", splits="")
        self.assertEqual(len(doc.ifc.cabinet_params(g).divisions), 2)


class OwnProfilesIfc(unittest.TestCase):
    """0.245: a flat sketch of an L (4 × 6 cm, drawn upright on a wall's plane) kept as the project's own profile «Friso
    L» — an IfcArbitraryClosedProfileDef of that name, nothing using it (one undo step); a volume or a name taken
    refused; run along a path: its section kept with it, its body swept, valid IFC; in the profiles one can choose and
    in the cut list by its name; made a skirting and back."""

    def test_own(self):
        from arqbim.core import profiles as pr
        from arqbim.ifc.edit import EditRefused
        doc = Document()
        m = sg.rectangle_matrix(np.array((0.0, 0.0, 1.0)), np.array((0.0, 1.0, 0.0)), np.array((0.0, 0.0, 1.0)))
        flat = SketchObject("f", m, sg.polygon_mesh([(0.0, 0.0), (0.04, 0.0), (0.04, 0.01), (0.01, 0.01),
                                                     (0.01, 0.06), (0.0, 0.06)]))
        doc.execute(AddObject(flat))
        key = bim.profile_from_face(doc, flat.id, "Friso L")
        self.assertEqual(key, "custom:Friso L")
        own = doc.ifc.custom_profiles()
        self.assertEqual(list(own), ["Friso L"])
        _unit, w, h = pr.unit_section(own["Friso L"])
        self.assertEqual((round(w, 3), round(h, 3)), (0.04, 0.06))
        doc.undo()
        self.assertEqual(doc.ifc.custom_profiles(), {})
        doc.redo()
        with self.assertRaises(EditRefused):
            bim.profile_from_face(doc, flat.id, "Friso L")
        box = box_object(doc, (2.0, 2.0, 0.0), 1.0, 1.0, 1.0)
        with self.assertRaises(ValueError):
            bim.face_section(box)
        g = bim.add_profile(doc, [(0.0, 0.0), (3.0, 0.0)], key, side=1)
        p = doc.ifc.profile_params(g)
        self.assertEqual((p["profile"], round(p["width"], 3), round(p["height"], 3)), (key, 0.04, 0.06))
        self.assertEqual(len(p["custom"]), 6)
        lo, hi = bounds(doc, g)
        self.assertAlmostEqual(hi[2] - lo[2], 0.06, places=6)
        self.assertEqual(doc.ifc.validate(), [])
        self.assertIn((key, "Friso L"), bim.profile_choices(doc))
        rows, _hw, areas = bim.cut_list(doc)
        self.assertTrue(any(r[0] == key for r in rows))
        bim.set_profile(doc, g, profile="rodape")
        self.assertEqual(doc.ifc.profile_params(g)["profile"], "rodape")
        bim.set_profile(doc, g, profile=key)
        self.assertEqual(round(doc.ifc.profile_params(g)["height"], 3), 0.06)


class KeynoteTableIfc(unittest.TestCase):
    """0.248: the project's own keynote table — kept in the IFC as references of «Notas-chave» that belong to no
    element (one undo step); offered beside the program's (its text first for a code it has too); a wall given one
    of its codes writes its text; the text changed: the wall's too; taken away: the wall keeps its own; valid IFC."""

    def test_table(self):
        from arqbim.model import keynotes
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), spec)
        self.assertTrue(bim.set_keynote_table(doc, {"10.01": "Painel acústico", "02.02": "Tijolo de 15 (projeto)"}))
        self.assertEqual(doc.ifc.keynote_table(), {"10.01": "Painel acústico", "02.02": "Tijolo de 15 (projeto)"})
        self.assertFalse(bim.set_keynote_table(doc, dict(doc.ifc.keynote_table())))      # (the same: no step)
        labels = dict((code, label) for label, code in keynotes.choices("pt", doc.ifc.keynote_table()))
        self.assertEqual(labels["10.01"], "10.01 — Painel acústico")
        self.assertEqual(labels["02.02"], "02.02 — Tijolo de 15 (projeto)")
        self.assertIn("01.01", labels)
        bim.set_keynote(doc, wall, "10.01")
        self.assertEqual(doc.ifc.keynote_of(wall), ("10.01", "Painel acústico"))
        bim.set_keynote_table(doc, {"10.01": "Painel acústico perfurado", "02.02": "Tijolo de 15 (projeto)"})
        self.assertEqual(doc.ifc.keynote_of(wall), ("10.01", "Painel acústico perfurado"))
        bim.set_keynote(doc, wall, "01.01")                              # (another: the table's entry stays)
        self.assertIn("10.01", doc.ifc.keynote_table())
        bim.set_keynote(doc, wall, "10.01")
        bim.set_keynote_table(doc, {})
        self.assertEqual(doc.ifc.keynote_table(), {})
        self.assertEqual(doc.ifc.keynote_of(wall), ("10.01", "Painel acústico perfurado"))
        doc.undo()
        self.assertEqual(len(doc.ifc.keynote_table()), 2)
        self.assertEqual(doc.ifc.validate(), [])


class CombinedFootingIfc(unittest.TestCase):
    """0.249: a combined footing under two columns 3 m apart (pad type 1,20 × 1,20 × 0,50): an IfcFooting PAD_FOOTING
    along the line between them, centred, 4,20 × 1,20, its top at their base — tied to both; one column moved 1 m
    further: made again, 5,20 long, still centred; a column given footings under it (Footings) then has its own too;
    the analytical model: both columns fixed on it, no footing alone; valid IFC; one step to undo."""

    def test_combined(self):
        from arqbim.core import structural as st
        doc = Document()
        a = bim.add_column(doc, np.array((0.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 3.0)
        b = bim.add_column(doc, np.array((3.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 3.0)
        pad = catalog.BY_KEY["sapata_120"]
        g = bim.combined_footing(doc, a, b, pad)
        e = doc.ifc.by_guid(g)
        self.assertEqual((e.is_a(), ifcopenshell.util.element.get_predefined_type(e)), ("IfcFooting", "PAD_FOOTING"))
        centre, x, length, width, top = doc.ifc.footing_params(g)
        self.assertTrue(np.allclose(centre, (1.5, 0.0)) and np.allclose(x[:2], (1.0, 0.0)))
        self.assertAlmostEqual(length, 3.0 + pad.profile[0], places=6)
        self.assertAlmostEqual(width, pad.profile[1], places=6)
        self.assertAlmostEqual(top, 0.0, places=6)
        self.assertEqual(sorted(doc.ifc.footings_of([a, b])), sorted([a, b]))
        m = np.eye(4)
        m[0, 3] = 1.0
        bim.transform_objects(doc, [b], m, "mover")
        centre, _x, length, _w, _t = doc.ifc.footing_params(g)
        self.assertAlmostEqual(length, 4.0 + pad.profile[0], places=6)
        self.assertTrue(np.allclose(centre, (2.0, 0.0)))
        columns, beams, footings, panels, levels = bim.structural_elements(doc)
        model = st.build(columns, beams, footings, panels, levels)
        self.assertEqual(len(model.supports), 2)
        self.assertFalse(any(i.code in ("footing_alone", "no_footing") for i in model.issues))
        self.assertEqual(doc.ifc.validate(), [])
        doc.undo()
        doc.undo()
        self.assertIsNone(doc.ifc.by_guid(g))
        self.assertIsNone(bim.combined_footing(doc, a, a, pad))


class CombinedFootingDesignIfc(unittest.TestCase):
    """0.250: a portal of two columns 3 m apart (3 m high, a beam between them) on a combined footing: the EC2 check
    designs it with both columns' reactions (its notes: the two columns, the moments along it), top bars along it;
    the columns' bars go down into it; its bars laid: the bottom mesh both ways and the top bars."""

    def test_design(self):
        doc = Document()
        a = bim.add_column(doc, np.array((0.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 3.0)
        b = bim.add_column(doc, np.array((3.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 3.0)
        bim.beams_between(doc, [a, b], catalog.BY_KEY["viga_20x40"])
        g = bim.combined_footing(doc, a, b, catalog.BY_KEY["sapata_120"])
        _m, _loads, _analysis, designs = bim.design_structure(doc)
        foot = next(d for d in designs if d.guid == g)
        codes = [n.code for n in foot.design.notes]
        self.assertIn("combined", codes)
        self.assertIn("combined_moments", codes)
        self.assertIsNotNone(foot.design.top_x)
        columns = [d for d in designs if d.kind == "column"]
        self.assertEqual(len(columns), 2)
        self.assertTrue(all(d.info["into"] > 0 for d in columns))
        bim.make_rebars(doc, designs)
        roles = {r["role"] for r in doc.ifc.rebar_rows() if r["host"] == g}
        self.assertEqual(roles, {"mesh_x", "mesh_y", "top_x"})
        self.assertEqual(doc.ifc.validate(), [])


class DrawnRoofIfc(unittest.TestCase):
    """0.251: a gable roof over a 10 × 6 m rectangle (50 cm eaves) given a section drawn upright (7 m wide: a flat
    underside, 20 cm at its edges, 1,50 m at its middle): an IfcRoof FREEFORM, its section over the span's middle
    run along its length — its top 1,50 over the eave in the middle, its underside the eave, its volume the
    section's area × its length —; made a gable roof and back; over an L refused; valid IFC."""

    def test_drawn(self):
        from shapely.geometry import Polygon
        from arqbim.ifc.edit import EditRefused
        doc = Document()
        outline = [(0.0, 0.0), (10.0, 0.0), (10.0, 6.0), (0.0, 6.0)]
        roof = bim.add_roof(doc, outline, catalog.BY_KEY["laje_15"], "gable", 30.0, 0.5, eave=3.0)
        section = [(0.0, 0.0), (7.0, 0.0), (7.0, 0.2), (3.5, 1.5), (0.0, 0.2)]
        m = sg.rectangle_matrix(np.array((0.0, -2.0, 0.0)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 0.0, 1.0)))
        flat = SketchObject("Secção", m, sg.polygon_mesh(section))
        doc.execute(AddObject(flat))
        bim.roof_profile_from_face(doc, roof, flat.id)
        self.assertEqual(doc.ifc.by_guid(roof).PredefinedType, "FREEFORM")
        self.assertAlmostEqual(doc.ifc.roof_height_at(roof, (5.0, 3.0)), 4.5, places=6)
        self.assertAlmostEqual(doc.ifc.roof_underside_at(roof, (5.0, 3.0)), 3.0, places=6)
        self.assertAlmostEqual(doc.ifc.roof_height_at(roof, (5.0, -0.5)), 3.2, places=6)       # (its edge)
        lo, hi = bounds(doc, roof)
        self.assertAlmostEqual(lo[2], 3.0, places=6)
        self.assertAlmostEqual(hi[2], 4.5, places=6)
        self.assertAlmostEqual(doc.get(roof).mesh.volume(), Polygon(section).area * 11.0, places=3)
        self.assertEqual(doc.ifc.validate(), [])
        bim.set_roof(doc, roof, form="gable")
        self.assertEqual(doc.ifc.by_guid(roof).PredefinedType, "GABLE_ROOF")
        bim.set_roof(doc, roof, form="custom")
        self.assertAlmostEqual(doc.ifc.roof_height_at(roof, (5.0, 3.0)), 4.5, places=6)
        el = bim.add_roof(doc, [(20, 0), (26, 0), (26, 3), (23, 3), (23, 5), (20, 5)], catalog.BY_KEY["laje_15"],
                          "hip", 30.0, 0.5, eave=3.0)
        with self.assertRaises(EditRefused):
            bim.roof_profile_from_face(doc, el, flat.id)


class CurvedCurtainWallIfc(unittest.TestCase):
    """0.252: a curved wall (5 m radius, a quarter circle from 0°, 20 cm, 2,80 m) and a curtain wall drawn on its arc
    from 30° to 60°, 2,40 m high (5 · π/6 ≈ 2,62 m long): it goes into the wall — its opening the ring's sector right
    through, the wall that much less —, its 3 mullions on the arc and its panels flat (chords); the cell under a
    point of it; slid along the wall; past the wall's end refused; the wall's radius 6 m: it follows (as far along,
    its own length, on the new arc); the wall mirrored: still in it; embedding off (the wall whole) and on; copied
    with the wall; valid IFC; all undone."""

    def test_curved(self):
        doc = Document()
        wall = bim.add_curved_wall(doc, np.zeros(3), 5.0, 0.0, math.pi / 2, catalog.BY_KEY["parede_alv_20"])
        full = doc.get(wall).mesh.volume()
        self.assertEqual(doc.ifc.curved_wall_at(np.array((5.0 * math.cos(0.5), 5.0 * math.sin(0.5), 0.0)), 2.4)[0],
                         wall)
        self.assertIsNone(doc.ifc.curved_wall_at(np.array((5.0, -1.0, 0.0)), 2.4))      # (past its start)
        self.assertIsNone(doc.ifc.curved_wall_at(np.array((5.0, 0.5, 0.0)), 3.0))       # (taller than it)
        sweep = math.radians(30)
        cw = bim.add_curtain_wall(doc, None, None, 2.4, 1.5, 1.2, arc=(np.zeros(3), 5.0, math.radians(30), sweep))
        self.assertEqual(doc.ifc.host_wall(cw), wall)
        p = doc.ifc.curtain_params(cw)
        self.assertAlmostEqual(p["length"], 5.0 * sweep, places=9)
        self.assertTrue(np.allclose(p["end"], (5.0 * math.cos(math.radians(60)), 5.0 * math.sin(math.radians(60)), 0.0)))
        cut = sweep * 5.0 * 0.2 * 2.4                                     # (the wall's 20 cm of the sector)
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), full - cut, delta=0.02 * cut)
        st = doc.ifc.filling_state(cw)
        self.assertTrue(st["curved"])
        self.assertAlmostEqual(st["s"], 5.0 * math.radians(30), places=6)
        self.assertAlmostEqual(st["width"], 5.0 * sweep, places=6)
        items = doc.ifc.by_guid(cw).Representation.Representations[0].Items
        self.assertEqual(len(items), 3 + 3 * 2 + 2 * 2)                   # (mullions, transoms by bay, panels)
        corner = doc.ifc.curtain_cell_box(cw, (1, 0))[1]
        self.assertAlmostEqual(float(np.hypot(corner[0], corner[1])), 5.0, places=6)    # (its corners on the arc)
        a = math.radians(52.5)
        self.assertEqual(doc.ifc.curtain_cell_at(cw, (5.0 * math.cos(a), 5.0 * math.sin(a), 1.8)), (1, 1))
        lo, hi = bounds(doc, cw)
        self.assertLess(lo[0], 5.0 * math.cos(math.radians(60)) + 0.01)
        bim.move_filling(doc, cw, s=3.5)                                  # slid along the wall
        p = doc.ifc.curtain_params(cw)
        self.assertTrue(np.allclose(p["start"], (5.0 * math.cos(0.7), 5.0 * math.sin(0.7), 0.0), atol=1e-6))
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), full - cut, delta=0.02 * cut)
        with self.assertRaises(ValueError):
            bim.move_filling(doc, cw, s=6.0)                              # (6 + 2,62 > 7,85: off its end)
        bim.set_curved_wall(doc, wall, radius=6.0)                        # the wall wider: it follows
        p = doc.ifc.curtain_params(cw)
        self.assertEqual(doc.ifc.host_wall(cw), wall)
        self.assertAlmostEqual(p["radius"], 6.0, places=9)
        self.assertAlmostEqual(p["length"], 5.0 * sweep, places=9)
        self.assertTrue(np.allclose(p["start"], (6.0 * math.cos(3.5 / 6), 6.0 * math.sin(3.5 / 6), 0.0), atol=1e-6))
        self.assertIsNotNone(doc.ifc._in_wall(cw, wall))
        bim.mirror_objects(doc, [wall], np.zeros(3), np.array((0.0, 1.0, 0.0)))     # about x = 0
        p = doc.ifc.curtain_params(cw)
        self.assertEqual(doc.ifc.host_wall(cw), wall)
        self.assertIsNotNone(doc.ifc._in_wall(cw, wall))
        self.assertTrue(np.allclose(p["start"], (-6.0 * math.cos(3.5 / 6), 6.0 * math.sin(3.5 / 6), 0.0), atol=1e-6))
        whole = 0.2 * 2.8 * 6.0 * math.pi / 2
        bim.set_curtain_embedding(doc, cw, False)                         # out of the wall: the wall whole
        self.assertIsNone(doc.ifc.host_wall(cw))
        self.assertAlmostEqual(doc.get(wall).mesh.volume(), whole, delta=0.01 * whole)
        bim.set_curtain_embedding(doc, cw, True)
        self.assertEqual(doc.ifc.host_wall(cw), wall)
        self.assertLess(doc.get(wall).mesh.volume(), whole - 0.5)
        copies = bim.copy_objects(doc, [wall], [translation((20.0, 0.0, 0.0))], "copiar")
        hosted = {doc.ifc.host_wall(e.GlobalId) for e in doc.ifc.file.by_type("IfcCurtainWall")}
        self.assertEqual(hosted, {wall, copies[0]})
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        while doc.can_undo():
            doc.undo()
        self.assertEqual(len(doc.ifc.file.by_type("IfcCurtainWall")), 0)


class OrientedCutsIfc(unittest.TestCase):
    """0.253: in a plan, a round wall's cut — its outer ring and its inner one (the hole) turned opposite ways, its
    area the ring's — and four walls with a column at each corner: every outline the same way round (what they share
    stays filled); in the DXF, no hatch line in the round room."""

    def test_oriented(self):
        from arqbim.core import cad
        from arqbim.model import drawings, dxf

        def area(ring):
            ring = np.asarray(ring, dtype=float)
            x, y = ring[:, 0], ring[:, 1]
            return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

        doc = Document()
        bim.add_curved_wall(doc, np.zeros(3), 3.0, 0.0, 2 * math.pi, catalog.BY_KEY["parede_alv_20"])
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        areas = sorted(area(r) for r in plan.cut)
        self.assertEqual(len(areas), 2)
        self.assertLess(areas[0], 0)
        self.assertGreater(areas[1], 0)
        self.assertAlmostEqual(sum(areas), math.pi * (3.1 ** 2 - 2.9 ** 2), delta=0.01)
        self.assertAlmostEqual(sum(area(r) for r, _h in plan.fills), math.pi * (3.1 ** 2 - 2.9 ** 2), delta=0.01)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "planta.dxf")
            dxf.write(path, plan, 100)
            hatch = [e for e in cad.read_file(path).entities if e.layer == "TRAMAS"]
        self.assertTrue(hatch)
        middles = [np.mean(np.asarray(e.points, dtype=float), axis=0) for e in hatch]
        self.assertGreater(min(float(np.hypot(*m)) for m in middles), 2.9 - 1e-6)     # (none in the room)
        doc = Document()
        spec, corners = catalog.BY_KEY["parede_alv_20"], [(0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0)]
        for k in range(4):
            bim.add_wall(doc, np.array(corners[k] + (0.0,)), np.array(corners[(k + 1) % 4] + (0.0,)), spec)
        column = next(s for s in catalog.BY_KEY.values() if s.kind == "column" and not s.round and s.shape is None)
        for c in corners:
            bim.add_column(doc, np.array(c + (0.0,)), column)
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual(len(plan.cut), 8)
        self.assertTrue(all(area(r) > 0 for r in plan.cut))
        # (0.254) the columns cut through the walls: the fills cover what is cut once (no wall's under a column)
        from arqbim.core import drawing2d
        whole = drawing2d.region(plan.cut).area
        self.assertAlmostEqual(sum(area(r) for r, _h in plan.fills), whole, places=6)
        columns = drawing2d.region([r for r, h in plan.fills if h == "concrete"])
        walls = drawing2d.region([r for r, h in plan.fills if h != "concrete"])
        self.assertAlmostEqual(walls.intersection(columns).area, 0.0, places=6)
        self.assertAlmostEqual(columns.area, 4 * column.profile[0] * column.profile[1], places=6)


class ChangesFromWorkerThread(unittest.TestCase):
    """0.254: a change made in a worker thread (as run_busy's: the analysis's results saved) is not told to the
    listeners there — it goes to the document's relay, which tells them in the main thread; with no relay (no
    window), as before."""

    def test_relay(self):
        import threading
        doc = Document()
        heard, relayed = [], []
        doc.subscribe(lambda changed, removed: heard.append((threading.current_thread() is threading.main_thread(),
                                                             set(changed))))
        doc.relay = relayed.append
        made = []
        worker = threading.Thread(target=lambda: made.append(
            bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])))
        worker.start()
        worker.join()
        self.assertEqual(heard, [])                                        # (nothing told in the worker)
        self.assertEqual(len(relayed), 1)
        relayed[0]()                                                      # (the window's thread)
        self.assertEqual(len(heard), 1)
        self.assertTrue(heard[0][0])
        self.assertIn(made[0], heard[0][1])
        doc.relay = None
        bim.add_wall(doc, np.array((0.0, 3.0, 0.0)), np.array((4.0, 3.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        self.assertEqual(len(heard), 2)


class SidecarReadOnce(unittest.TestCase):
    """0.255: a project opened — its side file (sketches, sections, sheets, dimensions…) parsed once for all the
    parts read from it (the sketches with the IFC, the rest when it is put on screen), and every part back."""

    def test_once(self):
        from unittest import mock
        from arqbim.model import document as document_module
        doc = Document()
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        doc.title_block = {"project": "Casa"}
        doc.grid_settings = dict(document_module.GRID_DEFAULTS, bubble=0.8)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.ifc")
            doc.save(path)
            real = document_module.json.load
            calls = []

            def counting(f, *args, **kwargs):
                calls.append(getattr(f, "name", ""))
                return real(f, *args, **kwargs)

            with mock.patch.object(document_module.json, "load", side_effect=counting):
                other = Document()
                other.open(path)
            side = [c for c in calls if c.endswith(document_module.SIDECAR_EXT)]
            self.assertEqual(len(side), 2)                     # (the sketches with the IFC; then all the rest)
            self.assertEqual(other.title_block.get("project"), "Casa")
            self.assertAlmostEqual(other.grid_settings["bubble"], 0.8)


class AppliancesIfc(unittest.TestCase):
    """0.171: in a straight kitchen, a hob put on its worktop: an IfcElectricAppliance ELECTRICCOOKER, and the worktop
    made again with its cut-out (a profile with a void); a kitchen sink beside it: a second one; the hob taken away:
    its cut-out goes; a dishwasher with its cold water and waste ports, a gas hob — an IfcBurner — with its gas port;
    a pipe in the new Gas system; valid IFC."""

    def test_appliances(self):
        doc = Document()
        made = bim.make_kitchen(doc, [(0.0, 0.0), (3.0, 0.0)], 1, wall_units=False)
        top = made["worktop"]

        def voids():
            body = [r for r in doc.ifc.by_guid(top).Representation.Representations
                    if r.RepresentationIdentifier == "Body"][0]
            profile = body.Items[0].SweptArea
            return len(profile.InnerCurves) if profile.is_a("IfcArbitraryProfileDefWithVoids") else 0

        self.assertEqual(voids(), 0)
        hob = bim.add_appliance(doc, np.array((0.9, 0.0, 0.0)), "hob", 0.0)
        e = doc.ifc.by_guid(hob)
        self.assertEqual((e.is_a(), e.PredefinedType), ("IfcElectricAppliance", "ELECTRICCOOKER"))
        self.assertEqual(voids(), 1)
        sink = bim.add_fixture(doc, np.array((2.1, 0.0, 0.0)), "kitchen_sink", 0.0)
        self.assertTrue(sink)
        self.assertEqual(voids(), 2)
        bim.delete(doc, [hob])
        self.assertEqual(voids(), 1)
        dw = bim.add_appliance(doc, np.array((4.0, 0.0, 0.0)), "dishwasher", 0.0)
        self.assertEqual(sorted((p.Name, p.SystemType) for p in doc.ifc.ports(dw)),
                         [("cold", "DOMESTICCOLDWATER"), ("drain", "WASTEWATER"), ("power", "ELECTRICAL")])   # (0.198)
        gas = bim.add_appliance(doc, np.array((5.0, 0.0, 0.0)), "gas_hob", 0.0)
        g = doc.ifc.by_guid(gas)
        self.assertEqual((g.is_a(), g.ObjectType), ("IfcBurner", "GASHOB"))
        self.assertEqual([p.SystemType for p in doc.ifc.ports(gas)], ["GAS"])
        from arqbim.ifc.systems import FROM_PORT, of_kind
        self.assertIn("gas", of_kind("pipe"))
        self.assertEqual(FROM_PORT["GAS"], "gas")
        self.assertEqual(doc.ifc.validate(), [])


class PatternedFinishesIfc(unittest.TestCase):
    """0.173: on a 4 m wall with a door, slats (ripado): one swept solid per piece, cut round the door; the gap made
    wider: fewer pieces; flutes (canelado); a perforated panel: one triangulated face set, read straight from the
    file (no kernel) — its holes; the wall longer: the finish follows; valid IFC; the cut list has the slats and the
    panels; the DXF for the CNC has each panel's outline and holes."""

    def test_patterns(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        frame = bim.wall_frame(doc, wall)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, 1.0, -1)
        slats = bim.add_cladding(doc, wall, -1, "ripado", 2.6)
        body = lambda g: [r for r in doc.ifc.by_guid(g).Representation.Representations           # noqa: E731
                          if r.RepresentationIdentifier == "Body"][0]
        d = doc.ifc.pattern_params(slats)
        self.assertEqual(len(body(slats).Items), d["count"])
        self.assertEqual(doc.ifc.describe(slats)["params"]["pattern"]["count"], d["count"])
        bim.set_cladding(doc, slats, gap=0.06)
        self.assertLess(doc.ifc.pattern_params(slats)["count"], d["count"])
        fluted = bim.add_cladding(doc, wall, 1, "canelado", 1.2)
        self.assertEqual(body(fluted).Items[0].SweptArea.OuterCurve.Segments[0].is_a("IfcArcIndex"), True)
        bim.delete(doc, [fluted])
        panel = bim.add_cladding(doc, wall, 1, "perfurado", 2.4)
        rep = body(panel)
        self.assertEqual((rep.RepresentationType, rep.Items[0].is_a()), ("Tessellation", "IfcTriangulatedFaceSet"))
        self.assertIsNotNone(doc.ifc._direct_mesh(doc.ifc.by_guid(panel)))
        holes = doc.ifc.pattern_params(panel)["count"]
        self.assertGreater(holes, 1000)
        self.assertGreater(len(doc.get(panel).mesh.tris), holes * 72 - 1)
        bim.resize_wall(doc, wall, at_end=1.0)
        self.assertGreater(doc.ifc.pattern_params(panel)["count"], holes)
        self.assertEqual(doc.ifc.validate(), [])
        rows, _hw, _areas = bim.cut_list(doc)
        self.assertEqual(sorted({r[0] for r in rows}), ["perforated", "slat"])
        from arqbim.model import fabrication
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "fabrico.dxf")
            panels, lengths = fabrication.write_dxf(path, doc)
            with open(path, encoding="cp1252") as f:
                text = f.read()
            self.assertGreater(panels, 1)
            self.assertGreater(lengths, 0)
            _rows, laid = fabrication.pieces(doc)
            self.assertTrue(any(len(rings[0]) > 4 for _n, _s, rings, _h, _d in laid))     # (cut round the door)
            self.assertEqual(text.count("\nCIRCLE\r\n") if "\r\n" in text else text.count("\nCIRCLE\n"),
                             doc.ifc.pattern_params(panel)["count"])

    def test_perforated_panel(self):
        """0.389: the perforated panel as a command: a rectangle on a 4 m wall's face (1 to 3 m along it, 0,5 to
        2,0 m up) with square holes on a 45° grid, boards 1 m wide 4 mm apart, a picture — valid IFC, its area the
        rectangle's, its holes only inside it; the rectangle edited; the DXF with squares (no circles); a whole-face
        panel follows the wall's height."""
        from PySide6 import QtGui
        from arqbim.model import fabrication
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        with tempfile.TemporaryDirectory() as tmp:
            picture = os.path.join(tmp, "furos.png")
            image = QtGui.QImage(40, 20, QtGui.QImage.Format.Format_RGB32)
            image.fill(QtGui.QColor("white"))
            for x in range(20):
                for y in range(20):
                    image.setPixelColor(x, y, QtGui.QColor("black"))
            self.assertTrue(image.save(picture))
            pattern = {"hole": "quadrado", "grid": "diagonal", "diameter": 0.02, "pitch": 0.05, "margin": 0.03,
                       "sheet_w": 1.0, "sheet_h": 2.44, "joint": 0.004, "mask": picture}
            panel = bim.add_cladding(doc, wall, 1, "perfurado", 2.0, pattern, {"start": 1.0, "end": 3.0, "base": 0.5})
            self.assertEqual(doc.ifc.validate(), [])
            d = doc.ifc.pattern_params(panel)
            self.assertEqual((d["hole"], d["grid"], len(d["panels"]), d["mask_found"]), ("quadrado", "diagonal", 2, True))
            frame = doc.ifc.element_frame(wall)
            u = np.array(d["holes"])
            self.assertTrue((u[:, 0] > frame.x0 + 1.0).all() and (u[:, 0] < frame.x0 + 2.0 + 1e-9).all())  # (dark half)
            self.assertTrue((u[:, 1] > 0.5).all() and (u[:, 1] < 2.0).all())
            info = doc.ifc.describe(panel)["params"]
            self.assertEqual((round(info["start"], 6), round(info["end"], 6), round(info["base"], 6), info["whole"]),
                             (1.0, 3.0, 0.5, False))
            q = ue.get_psets(doc.ifc.by_guid(panel))["Qto_CoveringBaseQuantities"]
            self.assertAlmostEqual(q["GrossArea"], 2.0 * 1.5, places=6)
            bim.set_cladding(doc, panel, end=2.0)
            self.assertAlmostEqual(doc.ifc.describe(panel)["params"]["end"], 2.0, places=6)
            path = os.path.join(tmp, "fabrico.dxf")
            fabrication.write_dxf(path, doc)
            with open(path, encoding="cp1252") as f:
                text = f.read()
            self.assertNotIn("\nCIRCLE", text)
            self.assertGreater(text.count("FUROS"), 10)
        whole = bim.add_cladding(doc, wall, -1, "perfurado", 0.0)
        info = doc.ifc.describe(whole)["params"]
        self.assertTrue(info["whole"])
        self.assertAlmostEqual(info["top"], doc.ifc.element_frame(wall).height, places=6)    # (all its height)
        self.assertEqual(doc.ifc.validate(), [])

    def test_paint(self):
        """0.391: the Paint bucket on a 4 m wall — one face painted terracotta: its triangles that colour whatever the
        view's colours (the others as they were), the eyedropper reads it, its area counted; kept in the wall's own
        coordinates (moved, the paint goes with it); the whole wall painted, then the terracotta replaced in the model;
        the paint taken off; valid IFC all along."""
        from arqbim.model import material_looks, paint
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        obj = doc.get(wall)
        tris, _owner = obj.mesh.triangulate()
        corners = np.asarray(obj.mesh.verts, dtype=float)[tris]
        normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
        normals /= np.linalg.norm(normals, axis=1, keepdims=True)
        south = np.flatnonzero(normals @ np.array((0.0, -1.0, 0.0)) > 0.99)
        point = corners[south[0]].mean(axis=0)
        bim.paint_face(doc, wall, (0.0, -1.0, 0.0), point, "tinta_terracota")
        obj = doc.get(wall)
        seen = material_looks.look(doc.ifc, obj, (0.5, 0.5, 0.5), False, False, False)
        terracotta = np.asarray(catalog.MATERIALS["tinta_terracota"].color)
        on = (seen.normals @ np.array((0.0, -1.0, 0.0)) > 0.99) & (np.abs(seen.corners.mean(axis=1)[:, 1] -
                                                                         point[1]) < 1e-6)
        self.assertTrue(seen.painted and on.any())
        self.assertTrue(np.allclose(seen.rgb[on], terracotta) and np.allclose(seen.rgb[~on], 0.5))
        face = next(k for k in range(len(obj.mesh.tris)) if obj.mesh.face_normal(k) @ np.array((0, -1, 0)) > 0.99)
        self.assertEqual(paint.material_at(doc.ifc, obj, face, (0.0, -1.0, 0.0), point), "tinta_terracota")
        self.assertAlmostEqual(paint.area_by_material(doc.ifc, obj)["tinta_terracota"], 4.0 * 2.8, delta=0.6)
        self.assertEqual(doc.ifc.validate(), [])
        bim.transform_objects(doc, [wall], translation((1.0, 2.0, 0.0)), "mover")
        planes = paint.world_planes(doc.ifc, wall)
        self.assertAlmostEqual(planes[0][1], -(point[1] + 2.0), places=6)      # (the plane moved with it)
        bim.paint_elements(doc, [wall], "tinta_verde")
        self.assertEqual(paint.entries(doc.ifc, wall), [["*", "tinta_verde"]])
        self.assertEqual(bim.replace_paint(doc, "tinta_verde", "tinta_azul"), 1)
        self.assertEqual(paint.entries(doc.ifc, wall), [["*", "tinta_azul"]])
        bim.paint_elements(doc, [wall], None)
        self.assertEqual(paint.entries(doc.ifc, wall), [])
        self.assertFalse(material_looks.look(doc.ifc, doc.get(wall), (0.5, 0.5, 0.5), False, False, False).painted)
        self.assertEqual(doc.ifc.validate(), [])
        # (0.392) a sketch's face painted (one undo step), Shift's replace through the sketches too, kept in the file
        from arqbim.core import sketch_geometry as sg
        from arqbim.model.document import AddObject, SketchObject
        box = sg.rectangle_mesh(2.0, 1.0)
        sg.push_pull(box, 0, np.eye(4), 1.0)
        sketch = SketchObject("Caixa", np.eye(4), box)
        doc.execute(AddObject(sketch))
        top = max(range(len(box.faces)), key=lambda g: box.face_points(g)[:, 2].mean())
        paint.paint_sketch(doc, [(doc.get(sketch.id), paint.sketch_face(doc.get(sketch.id).mesh, top), "tinta_ocre")])
        self.assertEqual(doc.get(sketch.id).mesh.paint_of(top), "tinta_ocre")
        doc.undo()
        self.assertIsNone(doc.get(sketch.id).mesh.paint_of(top))
        doc.redo()
        self.assertEqual(paint.paint_sketch(doc, paint.replace_in_sketches(doc, "tinta_ocre", "tinta_grafite")), 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "pintado.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            kept = again.sketches()[0].mesh
            self.assertEqual(sorted(p for p in kept.painted() if p), ["tinta_grafite"])

    def test_organic_roofs(self):
        """0.390: organic roofs over a 10 × 6 m rectangle at 3 m — each system (shell, gridshell, glazed, pergola)
        valid IFC, an IfcRoof FREEFORM with a body seen in the model; the gridshell's bars on its grid (black steel),
        the glass panes (glass); the vault's ends open arches (its top at the edge's middle); the ring beam under the
        edge and the supports down to the floor; moved, its outline goes with it; its measures changed."""
        doc = Document()
        rect = [(0.0, 0.0), (10.0, 0.0), (10.0, 6.0), (0.0, 6.0)]
        made = {}
        for system in ("casca", "gridshell", "envidracada", "pergola"):
            made[system] = bim.add_organic_roof(doc, rect, 3.0, system=system, form="cupula", rise=2.0)
        self.assertEqual(doc.ifc.validate(), [])
        for system, guid in made.items():
            e = doc.ifc.by_guid(guid)
            self.assertEqual((e.is_a(), e.PredefinedType, doc.ifc.kind_of(guid)), ("IfcRoof", "FREEFORM",
                                                                                  "organic_roof"))
            self.assertGreater(len(doc.get(guid).mesh.tris), 10, system)
            info = doc.ifc.describe(guid)["params"]
            self.assertEqual(info["system"], system)
            self.assertAlmostEqual(info["base"], 3.0, places=6)
            self.assertGreater(info["area"], 60.0)
            self.assertGreater(info["support_count"], 3)
            if system in ("gridshell", "envidracada"):
                self.assertGreater(info["bars"], 10)              # (both ways)
            if system == "pergola":
                self.assertEqual(info["bars"], 4)                 # (one way: 6 m at 1,2 m)
            if system == "envidracada":
                self.assertGreater(info["glass"], 50.0)
        bim.set_organic_roof(doc, made["gridshell"], form="abobada", spacing=1.5, supports="cantos")
        info = doc.ifc.describe(made["gridshell"])["params"]
        self.assertEqual((info["form"], info["spacing"], info["supports"], info["support_count"]),
                         ("abobada", 1.5, "cantos", 4))
        shape, _p = doc.ifc.organic_shape(made["gridshell"])
        self.assertAlmostEqual(float(shape.height(np.array([[-5.0, 0.0]]))[0]), 2.0, places=3)   # (an open arch)
        bim.set_organic_roof(doc, made["gridshell"], base=4.0)
        self.assertAlmostEqual(doc.ifc.describe(made["gridshell"])["params"]["base"], 4.0, places=6)
        with self.assertRaises(ValueError):
            bim.set_organic_roof(doc, made["casca"], spacing=0.05)
        self.assertEqual(doc.ifc.validate(), [])

    def test_wavy(self):
        """0.175: a wavy surface (ondulado) on a 4 m wall with a door: one swept solid per rib, its outline an
        indexed poly curve; out of the face from 2 cm to 8 cm; upright ribs with a larger wave (the crest 12 cm);
        valid IFC; the cut list with the ribs; the DXF with each rib's outline."""
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, wall), 1.0, -1)
        wavy = bim.add_cladding(doc, wall, 1, "ondulado", 2.4)
        items = [r for r in doc.ifc.by_guid(wavy).Representation.Representations
                 if r.RepresentationIdentifier == "Body"][0].Items
        d = doc.ifc.pattern_params(wavy)
        self.assertEqual(len(items), d["count"])
        self.assertTrue(all(i.is_a("IfcExtrudedAreaSolid") and i.SweptArea.OuterCurve.is_a("IfcIndexedPolyCurve")
                            for i in items))
        face = bim.wall_frame(doc, wall).y1
        verts = doc.get(wavy).mesh.verts
        self.assertAlmostEqual(float(verts[:, 1].max()) - face, 0.08, places=3)
        self.assertGreater(float(verts[:, 1].min()), face - 1e-6)
        bim.set_cladding(doc, wavy, amplitude=0.10, shift=0.0, direction="vertical")
        verts = doc.get(wavy).mesh.verts
        self.assertAlmostEqual(float(verts[:, 1].max()) - face, 0.12, places=3)
        self.assertEqual(doc.ifc.validate(), [])
        rows, _hw, _areas = bim.cut_list(doc)
        ribs = doc.ifc.pattern_params(wavy)["count"]
        self.assertEqual(sum(r[5] for r in rows if r[0] == "rib"), ribs)
        from arqbim.model import fabrication
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "fabrico.dxf")
            _panels, pieces = fabrication.write_dxf(path, doc)
            with open(path, encoding="cp1252") as f:
                text = f.read()
            self.assertEqual(pieces, ribs)
            self.assertGreaterEqual(text.count("POLYLINE"), ribs)


class ProfilesIfc(unittest.TestCase):
    """0.174: in a 5 × 4 m room (walls of 20 cm on their axes) with a door: a skirting board round it — an IfcCovering
    SKIRTINGBOARD, one triangulated face set read straight from the file —, along the walls' faces and broken at the
    door; the room made longer: the skirting follows it; a cornice in the same room right under the walls' top,
    whole (above the door); a dado rail along a path, on its right, made taller; moved, it goes along; mirrored, its
    side kept; valid IFC; the cut list and the DXF with the pieces and their mitres."""

    def test_profiles(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        corners = [(0.0, 0.0), (5.0, 0.0), (5.0, 4.0), (0.0, 4.0)]
        walls = []
        for k in range(4):                                     # (a chain, its corners joined — as drawn)
            a, b = np.array(corners[k] + (0.0,)), np.array(corners[(k + 1) % 4] + (0.0,))
            prev = (walls[-1], (a - np.array(corners[k - 1] + (0.0,))) / np.linalg.norm(
                a - np.array(corners[k - 1] + (0.0,)))) if walls else None
            first = (walls[0], np.array((1.0, 0.0, 0.0))) if k == 3 else None
            walls.append(bim.add_wall(doc, a, b, spec, prev=prev, first=first))
        frame = bim.wall_frame(doc, walls[0])
        bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY["porta_80"], frame, 2.0, -1)
        skirting = bim.room_profile(doc, (2.5, 2.0), "rodape")
        e = doc.ifc.by_guid(skirting)
        self.assertEqual((e.is_a(), e.PredefinedType), ("IfcCovering", "SKIRTINGBOARD"))
        self.assertIsNotNone(doc.ifc._direct_mesh(e))
        runs = doc.ifc.profile_runs(skirting)
        self.assertEqual([closed for _pts, closed in runs], [False])          # (broken at the door)
        inner = 2 * (4.8 + 3.8)
        length = doc.ifc.describe(skirting)["params"]["length"]
        self.assertTrue(inner - 1.2 < length < inner - 0.7, length)
        verts = doc.get(skirting).mesh.verts
        self.assertAlmostEqual(float(verts[:, 2].max()), 0.08, places=6)
        self.assertGreater(float(verts[:, 0].min()), 0.1 - 1e-6)              # (on the inner faces, into the room)
        bim.resize_wall(doc, walls[0], at_end=1.0)            # (the east wall goes along, the north one stretches)
        self.assertGreater(doc.ifc.describe(skirting)["params"]["length"], length + 1.5)
        longer = doc.ifc.describe(skirting)["params"]["length"]
        bim.add_opening(doc, walls[2], catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, walls[2]), 2.0, -1)
        self.assertEqual(len(doc.ifc.profile_runs(skirting)), 2)          # (a door put in the north wall: cut there)
        self.assertLess(doc.ifc.describe(skirting)["params"]["length"], longer - 0.7)    # (its body made again)
        cornice = bim.room_profile(doc, (2.5, 2.0), "sanca")
        top = float(doc.get(walls[0]).mesh.verts[:, 2].max())
        p = doc.ifc.describe(cornice)["params"]
        self.assertAlmostEqual(p["foot"] + p["height"], top, places=6)
        self.assertEqual([closed for _pts, closed in doc.ifc.profile_runs(cornice)], [True])
        rail = bim.add_profile(doc, [(1.0, 1.0), (3.0, 1.0), (3.0, 3.0)], "friso", side=-1)
        self.assertAlmostEqual(doc.ifc.describe(rail)["params"]["foot"], 0.90, places=9)
        bim.set_profile(doc, rail, height=0.08)
        self.assertAlmostEqual(float(doc.get(rail).mesh.verts[:, 2].max()), 0.98, places=6)
        self.assertLess(float(doc.get(rail).mesh.verts[:, 1].min()), 1.0 - 0.019)     # (to the path's right)
        bim.transform_objects(doc, [rail], np.array([[1, 0, 0, 0.5], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
                                                    dtype=float), "Mover")
        self.assertAlmostEqual(doc.ifc.profile_params(rail)["rings"][0][0][0], 1.5, places=6)
        bim.mirror_objects(doc, [rail], (2.0, 0.0), (2.0, 1.0))
        self.assertEqual(doc.ifc.profile_params(rail)["side"], -1)
        self.assertEqual(doc.ifc.validate(), [])
        rows, _hw, _areas = bim.cut_list(doc)
        self.assertEqual(sorted({r[0] for r in rows}), ["friso", "rodape", "sanca"])
        from arqbim.model import fabrication
        cuts = fabrication.profile_cuts(doc)
        self.assertTrue(any(key == "sanca" and abs(a0 - 45.0) < 0.1 for (key, _b, a0, _a1, _w), _n in cuts))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "fabrico.dxf")
            _panels, pieces = fabrication.write_dxf(path, doc)
            with open(path, encoding="cp1252") as f:
                text = f.read()
            self.assertGreater(pieces, 3)
            self.assertIn("Rodapé", text)


class FinishLayers(unittest.TestCase):
    """0.178: on one face of a wall, plaster to the top and tiles over it to 2,10 — the tiles stand off the wall by
    the plaster's 2 cm, layer 2 over «Reboco»; the plaster made stone (3 cm): the tiles go out with it; the other
    face's finish on the wall; the plaster deleted: the tiles back on the wall; undone: over it again; valid IFC."""

    def test_layers(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        y0 = bim.wall_frame(doc, wall).y0
        plaster = bim.add_cladding(doc, wall, -1, "reboco", 2.8)
        tiles = bim.add_cladding(doc, wall, -1, "azulejo", 2.1)
        other = bim.add_cladding(doc, wall, 1, "azulejo", 2.1)
        out = lambda g: float(doc.get(g).mesh.verts[:, 1].min())        # noqa: E731
        inner = lambda g: float(doc.get(g).mesh.verts[:, 1].max())      # noqa: E731
        self.assertAlmostEqual(inner(tiles), y0 - 0.02, places=6)
        self.assertAlmostEqual(out(tiles), y0 - 0.03, places=6)
        p = doc.ifc.describe(tiles)["params"]
        self.assertEqual((p["layer"], len(p["under"])), (2, 1))
        bim.set_cladding(doc, plaster, finish="pedra")
        self.assertAlmostEqual(inner(tiles), y0 - 0.03, places=6)
        self.assertAlmostEqual(float(doc.get(other).mesh.verts[:, 1].min()), bim.wall_frame(doc, wall).y1, places=6)
        bim.delete(doc, [plaster])
        self.assertAlmostEqual(inner(tiles), y0, places=6)
        doc.undo()
        self.assertAlmostEqual(inner(tiles), y0 - 0.03, places=6)
        self.assertEqual(doc.ifc.validate(), [])


class CurvedWallOpenings(unittest.TestCase):
    """0.177: a quarter-circle wall of 5 m radius with a door 3 m along it — an IfcDoor filling an opening that
    goes right through (the wall loses about the door's volume), the door at the axis there; a window's hole only
    (bare); the radius made 6 m: the door goes with it, still 3 m along; the arc made shorter than that: refused;
    the wall moved: its door too; valid IFC; the wall deleted: its door and hole go."""

    def test_curved_openings(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        arc = bim.add_curved_wall(doc, (0.0, 0.0, 0.0), 5.0, 0.0, math.pi / 2, spec, 3.0)
        whole = doc.get(arc).mesh.volume()
        door_spec = catalog.OPENING_BY_KEY["porta_80"]
        door = bim.add_curved_opening(doc, arc, door_spec, 3.0, -1)
        e = doc.ifc.by_guid(door)
        self.assertEqual(e.is_a(), "IfcDoor")
        lost = whole - doc.get(arc).mesh.volume()
        self.assertAlmostEqual(lost / (door_spec.width * door_spec.height * 0.2), 1.0, delta=0.05)

        def middle(guid):
            v = doc.get(guid).mesh.verts
            c = (v.min(axis=0) + v.max(axis=0)) / 2
            return math.hypot(c[0], c[1]), math.atan2(c[1], c[0]), c

        r, a, _c = middle(door)
        self.assertAlmostEqual(r, 5.0, delta=0.12)
        self.assertAlmostEqual(a, 3.0 / 5.0, delta=0.01)
        hole = bim.add_curved_opening(doc, arc, catalog.OPENING_BY_KEY["janela_120"], 6.0, 1, bare=True)
        self.assertEqual(doc.ifc.by_guid(hole).is_a(), "IfcOpeningElement")
        bim.set_curved_wall(doc, arc, radius=6.0)
        r, a, _c = middle(door)
        self.assertAlmostEqual(r, 6.0, delta=0.12)
        self.assertAlmostEqual(a, 3.0 / 6.0, delta=0.01)
        with self.assertRaises(ValueError):
            bim.set_curved_wall(doc, arc, sweep=4.0 / 6.0)              # (4 m long: the hole at 6 m falls off)
        self.assertAlmostEqual(doc.ifc.curved_wall_params(arc)[3], math.pi / 2, places=9)
        w = door_spec.width                                              # (its Properties: along the arc)
        self.assertAlmostEqual(doc.ifc.describe(door)["params"]["from_start"], 3.0 - w / 2, places=6)
        bim.move_filling(doc, door, s=4.0 - w / 2)
        self.assertAlmostEqual(middle(door)[1], 4.0 / 6.0, delta=0.01)
        bim.flip_door(doc, door, side=True)
        self.assertEqual(doc.ifc.filling_state(door)["side"], 1)
        bim.set_type(doc, door, catalog.OPENING_BY_KEY["porta_90"])
        st = doc.ifc.filling_state(door)
        self.assertAlmostEqual(st["width"], catalog.OPENING_BY_KEY["porta_90"].width, places=6)
        self.assertAlmostEqual(st["s"], 4.0 - w / 2, places=6)                 # (its left edge kept)
        tangent = doc.ifc.curved_frame(arc, st["s"] + st["width"] / 2, st["width"]).matrix[:3, 0]
        bim.slide_filling(doc, door, tangent * 0.5)                            # (dragged along the wall)
        st = doc.ifc.filling_state(door)
        self.assertAlmostEqual(st["s"], 4.5 - w / 2, places=6)
        (spot, _width), = bim.door_places(doc, doc.active_storey)
        self.assertAlmostEqual(math.hypot(*spot), 6.0, places=6)
        self.assertAlmostEqual(math.atan2(spot[1], spot[0]), (st["s"] + st["width"] / 2) / 6.0, places=6)
        _r, _a, before = middle(door)
        m = np.eye(4)
        m[:3, 3] = (1.0, 0.0, 0.0)
        bim.transform_objects(doc, [arc], m, "Mover")
        _r, _a, after = middle(door)
        np.testing.assert_allclose(after - before, (1.0, 0.0, 0.0), atol=1e-6)
        self.assertEqual(doc.ifc.validate(), [])
        bim.delete(doc, [arc])
        self.assertIsNone(doc.ifc.by_guid(door))
        self.assertIsNone(doc.ifc.by_guid(hole))


class SplatExport(unittest.TestCase):
    """0.176: a room (four walls, a window in one) as Gaussian splats: about as many as its surfaces' area
    holds at 8 cm; in Y-up coordinates (the walls' tops at y = their height); each splat a disc lying on its face
    (its quaternion turns z onto its normal); the colours of the materials, lit; the window's see-through; the PLY
    read back as written."""

    def test_splats(self):
        from arqbim.model import splat
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        walls = [bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
                 for a, b in (((0.0, 0.0), (5.0, 0.0)), ((5.0, 0.0), (5.0, 4.0)), ((5.0, 4.0), (0.0, 4.0)),
                              ((0.0, 4.0), (0.0, 0.0)))]
        bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY[next(k for k in catalog.OPENING_BY_KEY
                                                                   if catalog.OPENING_BY_KEY[k].kind == "window")],
                        bim.wall_frame(doc, walls[0]), 2.0, -1)
        data = splat.splats(doc, splat.QUALITY["low"])
        area = 0.0
        for obj in doc.objects.values():
            if obj.is_bim and obj.ifc_class not in splat.SKIP:
                v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
                tris = np.asarray(obj.mesh.triangulate()[0], dtype=np.int64).reshape(-1, 3)
                area += float(np.linalg.norm(np.cross(v[tris[:, 1]] - v[tris[:, 0]], v[tris[:, 2]] - v[tris[:, 0]]),
                                             axis=1).sum()) / 2
        n = len(data["x"])
        self.assertAlmostEqual(n / (area / 0.08 ** 2), 1.0, delta=0.05)
        top = float(max(o.mesh.verts[:, 2].max() for o in doc.objects.values() if o.is_bim))
        self.assertAlmostEqual(float(data["y"].max()), top, places=4)                 # (Y up)
        self.assertAlmostEqual(float(data["z"].max()), 0.13, places=4)                # (z = −y: the south wall's
        #                                                                               window's peitoril, 3 cm out: 0.290)
        q = np.column_stack([data["rot_{}".format(k)] for k in range(4)]).astype(float)
        self.assertTrue(np.allclose(np.linalg.norm(q, axis=1), 1.0, atol=1e-5))
        w, x, y, z = q.T                                                              # (z turned onto the normal)
        third = np.column_stack((2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)))
        normals = np.column_stack((data["nx"], data["ny"], data["nz"])).astype(float)
        self.assertTrue(np.allclose(third, normals, atol=1e-4))
        rgb = np.column_stack([data["f_dc_{}".format(k)] for k in range(3)]) * splat.SH_C0 + 0.5
        self.assertTrue(((rgb >= -1e-6) & (rgb <= 1 + 1e-6)).all())
        glass = np.isclose(data["opacity"], np.log(splat.GLASS / (1 - splat.GLASS)), atol=1e-5)
        self.assertTrue(glass.any() and (~glass).any())
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.ply")
            self.assertEqual(splat.write_ply(path, data), n)
            back = splat.read_ply(path)
            self.assertEqual(list(back), list(splat.PROPS))
            self.assertTrue(np.array_equal(back["x"], data["x"]) and np.array_equal(back["rot_3"], data["rot_3"]))

    def test_cloud_splats(self):
        """0.216: a point cloud as splats, straight from its points: thinned to one a 5 cm cell (a 1 cm grid of
        1 × 1 m: 400), round balls of the points' colours, Y up; grey without colours; with the model's in one file."""
        from arqbim.model import splat
        g = np.arange(0.0, 1.0, 0.01)
        pts = np.array([(x, y, 2.0) for x in g for y in g])
        red = np.tile((1.0, 0.0, 0.0), (len(pts), 1))
        data = splat.cloud_splats(pts, red, 0.05)
        self.assertEqual(len(data["x"]), 400)
        self.assertTrue(np.allclose(data["y"], 2.0))                                   # (Y up: its height)
        self.assertTrue(np.allclose(data["scale_0"], data["scale_2"]))                 # (balls)
        rgb = np.column_stack([data["f_dc_{}".format(k)] for k in range(3)]) * splat.SH_C0 + 0.5
        self.assertTrue(np.allclose(rgb, (1.0, 0.0, 0.0), atol=1e-5))
        grey = splat.cloud_splats(pts, None, 0.05)
        self.assertTrue(np.allclose(grey["f_dc_0"] * splat.SH_C0 + 0.5, 0.7, atol=1e-5))
        doc = Document()
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((3.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "tudo.ply")
            n = splat.export(doc, path, "low", clouds=[(pts, red)])
            alone = splat.export(doc, os.path.join(tmp, "nuvem.ply"), "low", clouds=[(pts, red)], model=False)
        self.assertGreater(n, alone)
        self.assertEqual(alone, len(splat.cloud_splats(pts, red, splat.QUALITY["low"])["x"]))


class SymbolStyles(unittest.TestCase):
    """0.360: the symbols' styles (the project's graphic style «symbols»)."""

    def test_clean_and_shapes(self):
        """A style read: its known parts kept (a square head, an open arrow, a line only at its ends, sizes in their
        range), the rest the usual; a head's shape by it — a circle's 32 sides, a square's 4, none; a filled or open
        arrow along its look, none —; a line whole and dashed, or only at its ends."""
        from arqbim.model import graphic_styles as gs
        from arqbim.model import symbols as sm
        style = gs.clean({"symbols": {"section": {"head": "square", "arrow": "open", "line": "ends", "size": 99,
                                                  "text": "x", "colour": "red"},
                                      "nothing": {"head": "square"}}})
        section = style["symbols"]["section"]
        self.assertEqual((section["head"], section["arrow"], section["line"], section["size"], section["text"]),
                         ("square", "open", "ends", 12.0, gs.DEFAULTS["symbols"]["section"]["text"]))
        self.assertNotIn("nothing", style["symbols"])
        self.assertEqual(gs.symbol(None, "level"), gs.DEFAULTS["symbols"]["level"])
        lines, filled, hollow, r = sm.head_shape(gs.symbol(None, "section"), np.array((0.0, 1.0)), 1.0)
        self.assertEqual((len(lines), len(filled), len(hollow), r), (32, 1, 0, 4.0))
        self.assertGreater(min(p[1] for p in filled[0]), r - 1e-9)                # (out of the head, the way it looks)
        lines, filled, hollow, _r = sm.head_shape(section, np.array((1.0, 0.0)), 1.0)
        self.assertEqual((len(lines), len(filled), len(hollow)), (4, 0, 1))
        lines, filled, hollow, _r = sm.head_shape(dict(section, head="none", arrow="none"), None, 1.0)
        self.assertEqual((lines, filled, hollow), ([], [], []))
        whole, dashes = sm.line_pieces((0.0, 0.0), (100.0, 0.0), gs.symbol(None, "section"))
        self.assertEqual((len(whole), dashes), (1, sm.DASHES["dashdot"]))
        ends, dashes = sm.line_pieces((0.0, 0.0), (100.0, 0.0), section)
        self.assertEqual(len(ends), 2)
        self.assertIsNone(dashes)
        self.assertAlmostEqual(float(np.linalg.norm(np.subtract(*ends[0]))), sm.ENDS)

    def test_the_drawings_follow(self):
        """A plan with a section, drawn to PDF and DXF with the usual symbols and with a square head, no arrow, only
        its ends: both written (the DXF has the square's 4 lines and no arrow polyline where it had a circle)."""
        from arqbim.model import drawings
        from arqbim.model import graphic_styles as gs
        from arqbim.model import dxf
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (6.0, 4.0, 0.0),
                                                      (0.0, 4.0, 0.0))], spec)
        doc.add_section(np.array((3.0, 2.0, 1.0)), np.array((0.0, 1.0, 0.0)))
        storey = doc.ifc.storeys()[0][0]
        counts = {}
        with tempfile.TemporaryDirectory() as tmp:
            for name, symbols in (("usual", None), ("square", {"section": {"head": "square", "arrow": "none",
                                                                           "line": "ends"}})):
                doc.graphic_style = gs.clean({"symbols": symbols} if symbols else None)
                drawing = drawings.plan(doc, storey, "Planta")
                path = os.path.join(tmp, name + ".dxf")
                dxf.write(path, drawing, 100)
                with open(path, encoding="cp1252") as fh:
                    text = fh.read()
                counts[name] = (text.count("\nCIRCLE\n"), text.count("\nLINE\n"))
        self.assertGreater(counts["usual"][0], counts["square"][0])              # (the section's heads no circles)
        doc.modified = False


class DoorPlan(unittest.TestCase):
    """0.359: a door in plan (the owner's document, 8th point)."""

    def test_pieces_and_symbol(self):
        """A wooden door's pieces in plan, each its own: two jambs (aro), its casings on both faces (remates), its
        soleira; drawn open — its leaf open with its swing, no leaf in the frame —, drawn closed — the leaf in the frame
        (a «folha» piece), the swing the arc and a thin line —; its swing dashed: in dashes."""
        from arqbim.core import joinery as jn
        door = jn.door("left", stone=0.02)
        width, height, y0, y1 = 0.9, 2.1, 0.0, 0.2
        roles = [r for r, _ring, _k in jn.plan_pieces(door, width, height, y0, y1, (0.0, 0.2))]
        self.assertEqual(sorted(roles), ["aro", "aro", "remate", "remate", "remate", "remate", "soleira"])
        opened = jn.plan_symbol(door, width, height, y0, y1, (0.0, 0.2))
        tall = [line for line in opened if len(line) == 5 and max(p[1] for p in line) > y1 + 0.5]
        self.assertEqual(len(tall), 1)                                   # (the leaf, open square to the wall)
        closed = jn.replace(door, plan_open=False)
        roles = [r for r, _ring, _k in jn.plan_pieces(closed, width, height, y0, y1, (0.0, 0.2))]
        self.assertIn("folha", roles)
        shut = jn.plan_symbol(closed, width, height, y0, y1, (0.0, 0.2))
        self.assertFalse([line for line in shut if len(line) == 5 and max(p[1] for p in line) > y1 + 0.5])
        thin = [line for line in shut if len(line) == 2 and abs(line[0][0] - line[1][0]) < 1e-9
                and abs(abs(line[1][1] - line[0][1]) - (width - 2 * door.frame)) < 0.05]
        self.assertEqual(len(thin), 1)                                   # (the swing's line where it opens to)
        dashed = jn.plan_symbol(jn.replace(closed, swing_style="dashed"), width, height, y0, y1, (0.0, 0.2))
        self.assertGreater(len(dashed), len(shut) + 5)
        restored = jn.from_json(jn.to_json(jn.replace(closed, swing_style="dashed")))
        self.assertEqual((restored.plan_open, restored.swing_style), (False, "dashed"))

    def test_in_the_model(self):
        """A 90 cm door in a wall: its pieces in the plan where it is (inside the opening's box), its hinges' jamb and
        the other 90 cm apart; placed with its hinges wanted at the other jamb, they are there (one step); a plan's cut
        draws it by its pieces (aro, remates…), not its body's cut, none merged with another."""
        from arqbim.model import drawings
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), spec)
        frame = bim.wall_frame(doc, wall)
        door = bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_90"], frame, 2.0, -1)
        pieces = doc.ifc.door_plan_pieces(door)
        lo, hi = doc.get(door).mesh.bounds()
        pts = np.array([p for _r, ring, _h in pieces for p in ring])
        self.assertTrue(np.all(pts >= lo[:2] - 0.1) and np.all(pts <= hi[:2] + 0.1))
        self.assertEqual(sum(1 for r, _ring, _h in pieces if r == "aro"), 2)
        hinge, other = doc.ifc.door_hinge(door)
        self.assertAlmostEqual(float(np.linalg.norm(np.subtract(hinge, other)[:2])), 0.9 - 0.0, delta=0.11)
        steps = len(doc._undo)
        second = bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_90"], frame, 3.5, -1,
                                 hinge_at=np.array(other) + np.array((1.5, 0.0, 0.0)))
        self.assertEqual(len(doc._undo), steps + 1)
        h2, o2 = doc.ifc.door_hinge(second)
        far = np.array(other)[:2] + np.array((1.5, 0.0))
        self.assertLess(float(np.linalg.norm(np.array(h2)[:2] - far)), float(np.linalg.norm(np.array(o2)[:2] - far)))
        z = 1.2
        objects = [doc.get(g) for g in (wall, door)]
        fills, _patterns, whose = drawings.cut_fills(doc, objects, np.array((0.0, 0.0, -1.0)), -z,
                                                     np.array((0.0, 0.0, z)), np.array((1.0, 0.0, 0.0)),
                                                     np.array((0.0, 1.0, 0.0)))
        mine = [ring for ring, owner in zip(fills, whose) if owner == door]
        self.assertEqual(len(mine), len(pieces))                       # (each piece its own fill)
        doc.modified = False


class RoomProgramme(unittest.TestCase):
    """0.357: the programme (programa de necessidades) and the rooms, interior or exterior."""

    def test_parse(self):
        """A spreadsheet's CSV in Portuguese (headings, «;», decimal commas, «exterior»), a plain list (one name a line)
        and a CSV with «,» (decimal points): their rooms, areas, how many, interior or exterior."""
        from arqbim.model import room_program as rp
        needs = rp.parse("Ambiente;Área (m²);Quantidade;Tipo\nQuarto;12,5;2;interior\nSala comum;20;;\n"
                         "Terraço;6,0;1;Exterior\n")
        self.assertEqual([(n.name, n.area, n.count, n.external) for n in needs],
                         [("Quarto", 12.5, 2, False), ("Sala comum", 20.0, 1, False), ("Terraço", 6.0, 1, True)])
        self.assertEqual([n.name for n in rp.parse("Cozinha\nWC\n\nEscritório\n")], ["Cozinha", "WC", "Escritório"])
        self.assertEqual([(n.name, n.area) for n in rp.parse("Quarto,12.5,1\nPátio,30,1,exterior")],
                         [("Quarto", 12.5), ("Pátio", 30.0)])
        self.assertEqual(rp.from_text(rp.to_text(needs)), needs)

    def test_rooms_from_the_programme(self):
        """A house split in two by a wall, the programme kept in the IFC: «Quarto» dropped in the left half — a room
        made there, named so, interior —; «Terraço» (exterior) dropped on it — the same room renamed, exterior (IFC's
        EXTERNAL, Pset_SpaceCommon.IsExternal) —; dropped outside the walls: nothing; the progress: how many made."""
        from arqbim.model import room_program as rp
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        pts = [(0.0, 0.0), (8.0, 0.0), (8.0, 4.0), (0.0, 4.0)]
        for k in range(4):
            bim.add_wall(doc, np.array(pts[k] + (0.0,)), np.array(pts[(k + 1) % 4] + (0.0,)), spec)
        bim.add_wall(doc, np.array((4.0, 0.0, 0.0)), np.array((4.0, 4.0, 0.0)), spec)
        needs = [rp.Need("Quarto", 12.0), rp.Need("Terraço", 6.0, 1, True)]
        bim.set_room_program(doc, needs)
        self.assertEqual(doc.ifc.room_program(), needs)
        guid, made = bim.room_from_program(doc, (2.0, 2.0), needs[0])
        self.assertTrue(made)
        info = doc.ifc.space_info(guid)
        self.assertEqual((info["name"], info["external"]), ("Quarto", False))
        self.assertEqual([(n.name, k) for n, k, _a in rp.progress(needs, doc.ifc.spaces())],
                         [("Quarto", 1), ("Terraço", 0)])
        again, made = bim.room_from_program(doc, (1.0, 3.0), needs[1])
        self.assertEqual((again, made), (guid, False))
        info = doc.ifc.space_info(guid)
        self.assertEqual((info["name"], info["external"]), ("Terraço", True))
        space = doc.ifc.by_guid(guid)
        self.assertEqual(space.PredefinedType, "EXTERNAL")
        self.assertTrue(ue.get_psets(space)["Pset_SpaceCommon"]["IsExternal"])
        self.assertIsNone(bim.room_from_program(doc, (20.0, 20.0), needs[0]))
        bim.set_room(doc, guid, external=False)
        self.assertFalse(doc.ifc.space_info(guid)["external"])
        doc.modified = False


class WallCorners(unittest.TestCase):
    """0.352: the outside corners of joined layered walls, as seen (material_looks: the 3D view by materials, the
    render, the GLB / SKP / 3DM) and drawn (seen_joins)."""

    def test_plaster_round_the_corner(self):
        """A room of four plastered brick walls (add_wall_loop): no brick on the outside — each wall's end in the face
        of the wall it turns to is plaster, as the faces are —, and no seam drawn up a façade where that end meets the
        other's face; a wall standing alone keeps its ends cut along its layers."""
        from arqbim.model import material_looks, seen_joins
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        walls = bim.add_wall_loop(doc, corners, spec)
        free = bim.add_wall(doc, np.array((10.0, 0.0, 0.0)), np.array((14.0, 0.0, 0.0)), spec)
        outer = (-0.1, 5.1, -0.1, 4.1)                        # (x min, x max, y min, y max of the room's outside)
        plaster = set()
        for g in walls:
            seen = material_looks.look(doc.ifc, doc.get(g), (0.5, 0.5, 0.5), colours=True, patterns=False)
            centres = seen.corners.mean(axis=1)
            side = np.abs(seen.normals[:, 2]) < 0.5
            out = side & ((np.abs(centres[:, 0] - outer[0]) < 1e-3) | (np.abs(centres[:, 0] - outer[1]) < 1e-3) |
                          (np.abs(centres[:, 1] - outer[2]) < 1e-3) | (np.abs(centres[:, 1] - outer[3]) < 1e-3))
            self.assertTrue(out.any())
            plaster |= set(seen.materials[out])
        self.assertEqual(len(plaster), 1)                    # (one material all round the outside: the plaster)
        seen = material_looks.look(doc.ifc, doc.get(free), (0.5, 0.5, 0.5), colours=True, patterns=False)
        ends = (np.abs(seen.normals[:, 0]) > 0.99)
        self.assertGreater(len(set(seen.materials[ends])), 1)     # (its ends: plaster, brick, plaster)
        found = seen_joins.all_seams([doc.get(g) for g in walls], doc.ifc)
        for g in walls:
            mesh = doc.get(g).mesh
            verts = np.asarray(mesh.verts, dtype=float)
            pairs, _faces = mesh.edge_array()
            keep = found[g][0] if g in found else np.ones(len(pairs), dtype=bool)
            a, b = verts[pairs[keep, 0]], verts[pairs[keep, 1]]
            upright = np.abs(a[:, 2] - b[:, 2]) > 0.5
            on_x = (np.abs(a[:, 0] - outer[1]) < 1e-3) & (np.abs(b[:, 0] - outer[1]) < 1e-3)
            inside = (a[:, 1] > outer[2] + 1e-3) & (a[:, 1] < outer[3] - 1e-3)
            self.assertFalse(np.any(upright & on_x & inside), doc.get(g).name)   # (none up the east façade)
        doc.modified = False


class GltfExport(unittest.TestCase):
    """0.348: a room (four walls, a window in one), a slab on it and a sketch box, in a GLB file read back: glTF 2.0,
    its chunks whole; the tree Model ▸ Storey ▸ Category ▸ element (the walls under «Paredes», each with its GlobalId,
    class and type in its extras), the sketch under «Esboços»; every triangle of the model there (flat, unit normals),
    Y up, near the origin (the offset kept); its materials by name — the plaster's, the glass see-through (BLEND, a
    glass finish) —; the position accessors' bounds as their points'."""

    def test_glb(self):
        from arqbim.i18n import t
        from arqbim.model import gltf_export
        from arqbim.model.document import AddObject, SketchObject
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        walls = [bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
                 for a, b in (((0.0, 0.0), (5.0, 0.0)), ((5.0, 0.0), (5.0, 4.0)), ((5.0, 4.0), (0.0, 4.0)),
                              ((0.0, 4.0), (0.0, 0.0)))]
        bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, walls[0]), 2.0, -1)
        top = float(doc.get(walls[0]).mesh.bounds()[1][2])
        bim.add_slab(doc, np.array((0.0, 0.0, top)), 5.0, 4.0, catalog.BY_KEY["laje_12"])
        m = sg.rectangle_matrix(np.array((8.0, 0.0, 0.0)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0)))
        box = sg.rectangle_mesh(1.0, 1.0)
        sg.push_pull(box, 0, m, 1.0)
        doc.execute(AddObject(SketchObject("Esboço", m, box)))
        objects = list(doc.objects.values())
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.glb")
            n, triangles = gltf_export.export(doc, objects, path, "Casa")
            gltf, binary = gltf_export.read(path)
        self.assertEqual(gltf["asset"]["version"], "2.0")
        self.assertEqual(gltf["buffers"][0]["byteLength"], sum(v["byteLength"] for v in gltf["bufferViews"]))
        self.assertGreaterEqual(len(binary), gltf["buffers"][0]["byteLength"])
        nodes = gltf["nodes"]
        root = nodes[gltf["scenes"][0]["nodes"][0]]
        self.assertEqual(root["name"], "Casa")
        tree = {nodes[s]["name"]: {nodes[c]["name"]: [nodes[e] for e in nodes[c]["children"]]
                                   for c in nodes[s]["children"]} for s in root["children"]}
        storey = next(n for _g, n, _z in doc.storeys())
        self.assertEqual(set(tree), {storey, t("gltf.sketches")})
        in_walls = tree[storey][t("tree.cat.IfcWall")]
        self.assertEqual({e["extras"]["GlobalId"] for e in in_walls}, set(walls))
        self.assertTrue(all(e["extras"]["ifcClass"] == "IfcWall" and e["extras"]["type"] == spec.name_pt
                            for e in in_walls))
        self.assertIn(t("tree.cat.IfcWindow"), tree[storey])
        area = 0.0                                  # (the walls cut along their layers: more triangles, the same area)
        for obj in objects:
            if getattr(obj, "ifc_class", None) in gltf_export.SKIP or obj.mesh is None:
                continue
            v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
            tri = np.asarray(obj.mesh.triangulate()[0], dtype=np.int64).reshape(-1, 3)
            area += float(np.linalg.norm(np.cross(v[tri[:, 1]] - v[tri[:, 0]], v[tri[:, 2]] - v[tri[:, 0]]),
                                         axis=1).sum()) / 2.0
        self.assertGreaterEqual(triangles, 360)
        self.assertEqual(n, sum(1 for o in objects if getattr(o, "ifc_class", None) not in gltf_export.SKIP))
        names = {mat["name"]: mat for mat in gltf["materials"]}
        self.assertIn(catalog.MATERIALS["reboco"].name_pt, names)
        glass = [mat for mat in gltf["materials"] if mat.get("alphaMode") == "BLEND"]
        self.assertTrue(glass and all(mat["extras"]["finish"] in ("glass", "frosted") for mat in glass))
        views = gltf["bufferViews"]
        lowest, highest = np.full(3, np.inf), np.full(3, -np.inf)
        written = 0.0
        for k in range(0, len(gltf["accessors"]), 2):
            a, b = gltf["accessors"][k], gltf["accessors"][k + 1]
            p = np.frombuffer(binary, dtype="<f4", count=a["count"] * 3,
                              offset=views[0]["byteOffset"] + a["byteOffset"]).reshape(-1, 3)
            nn = np.frombuffer(binary, dtype="<f4", count=b["count"] * 3,
                               offset=views[1]["byteOffset"] + b["byteOffset"]).reshape(-1, 3)
            self.assertEqual(a["count"] % 3, 0)
            np.testing.assert_allclose(p.min(axis=0), a["min"], atol=1e-6)
            np.testing.assert_allclose(p.max(axis=0), a["max"], atol=1e-6)
            np.testing.assert_allclose(np.linalg.norm(nn, axis=1), 1.0, atol=1e-5)
            lowest, highest = np.minimum(lowest, p.min(axis=0)), np.maximum(highest, p.max(axis=0))
            c = p.astype(float).reshape(-1, 3, 3)
            written += float(np.linalg.norm(np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0]), axis=1).sum()) / 2.0
        self.assertAlmostEqual(written / area, 1.0, places=4)                  # (every face there, once)
        offset = gltf["scenes"][0]["extras"]["offset"]
        self.assertAlmostEqual(offset[2], 0.0, places=3)                        # (its lowest point at y = 0)
        self.assertAlmostEqual(float(lowest[1]), 0.0, places=3)
        self.assertAlmostEqual(float(highest[1]), top + 0.12, places=3)          # (Y up: the slab's top)
        self.assertLess(abs(float(lowest[0] + highest[0])), 0.05)               # (centred near the origin)

    def test_for_the_presentation(self):
        """0.362: the model for the ArqSynth Presentation — a room on the ground floor (four walls, a window, a slab), two
        walls on a floor above named as two below, a named 3D view (the slabs hidden, a section box), a section: one
        GLB with the brand's handoff envelope in its asset extras (its target the Presentation, its checksum over the
        rest); every node's three.js name unique, no mesh or scene named; a layer per element, its id from its
        GlobalId, its first node its own; the scenes in order — the general view (at the model's middle), the 3D view
        (its camera in the GLB's axes, its vertical fov from pygfx's, the slab hidden, the box's six planes keeping
        what is inside it), a plan each floor (cut at 1,20 m above it, the other floor hidden), the section (its plane
        keeping what it looks at) —; the sun from the site when the site has a place. (0.363) The general view from the
        south-west, above (it was below, on the north-east); the section's scene known by its uid; each scene with
        the usual choices (in the sequence, a smooth flight of 1,2 s, no effect, caption or thumbnail)."""
        import json

        import pylinalg as la
        from arqbim.model import gltf_export, presentation_export as pe
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        walls = bim.add_wall_loop(doc, corners, spec)
        bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, walls[0]), 2.0, -1)
        slab = bim.add_slab(doc, np.array((0.0, 0.0, 2.8)), 5.0, 4.0, catalog.BY_KEY["laje_12"])
        upper = bim.add_storey(doc, "Piso 1", 3.0)
        above = [bim.add_wall(doc, np.array((0.0, k, 3.0)), np.array((5.0, k, 3.0)), spec, storey=upper)
                 for k in (0.0, 4.0)]
        for g, below in zip(above, walls):                                        # (the same names as two below)
            doc.ifc.by_guid(g).Name = doc.ifc.by_guid(below).Name
            doc.get(g).name = doc.get(below).name
        eye, focus = np.array((10.0, -8.0, 6.0)), np.array((2.5, 2.0, 1.0))
        back = (eye - focus) / np.linalg.norm(eye - focus)
        right = np.cross((0.0, 0.0, 1.0), back)
        right /= np.linalg.norm(right)
        turn = la.quat_from_mat(np.column_stack((right, np.cross(back, right), back)))
        camera = {"position": tuple(eye), "rotation": tuple(turn), "fov": 50.0, "width": 16.0, "height": 9.0,
                  "zoom": 1.0, "focus": focus}
        doc.add_view3d(camera, {"hidden": ["IfcSlab"], "box": [[0.0, 0.0, 0.0], [2.5, 4.0, 3.0]]})
        doc.add_section(np.array((2.5, 2.0, 0.0)), np.array((0.0, 1.0, 0.0)))
        self.assertEqual(pe.three_name("Parede 1.2: [a]/b"), "Parede_12_ab")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.glb")
            done = pe.export(doc, path, "Casa")
            gltf, _binary = gltf_export.read(path)
            description = pe.read(path)
        self.assertEqual((description["format"], description["formatVersion"], description["target"]["code"],
                          description["source"]["product"]), ("arqsynth-ecosystem-handoff", "1.0", "presentation",
                                                              "ArqSynth BIM"))
        rest = {k: v for k, v in description.items() if k != "checksum"}
        self.assertEqual(description["checksum"], pe.checksum(json.dumps(rest, ensure_ascii=False,
                                                                         separators=(",", ":"))))
        names = [pe.three_name(n["name"]) for n in gltf["nodes"]]
        self.assertEqual(len(names), len(set(names)))
        self.assertFalse(any("name" in m for m in gltf["meshes"]) or "name" in gltf["scenes"][0])
        model = description["presentation"]["model3d"]
        offset = np.asarray(model["offset"])
        node_of = {n["extras"]["GlobalId"]: n for n in gltf["nodes"] if "mesh" in n and "GlobalId" in n["extras"]}
        layers = {l["globalId"]: l for l in model["layers"]}
        self.assertEqual(set(layers), set(node_of))
        # (0.483) the window's glass: a child node of its own, named, in the window's layer (the Presentation made it a
        # layer «Window» of its own when it was a part of the window's mesh)
        window = next(g for g, n in node_of.items() if n["extras"]["ifcClass"] == "IfcWindow")
        glass = [gltf["nodes"][c] for c in node_of[window].get("children", ())]
        self.assertEqual(len(glass), 1)
        self.assertEqual(glass[0]["extras"], {"part": "clear"})
        self.assertTrue(glass[0]["name"].endswith(" vidro"))
        self.assertEqual(layers[window]["nodeIds"], [pe.three_name(node_of[window]["name"]),
                                                     pe.three_name(glass[0]["name"])])
        see = [gltf["materials"][p["material"]] for p in gltf["meshes"][glass[0]["mesh"]]["primitives"]]
        self.assertTrue(see and all(m.get("alphaMode") == "BLEND" for m in see))
        self.assertTrue(all(gltf["materials"][p["material"]].get("alphaMode") != "BLEND"
                            for p in gltf["meshes"][node_of[window]["mesh"]]["primitives"]))
        self.assertTrue(all(len(l["nodeIds"]) == 1 for g, l in layers.items() if g != window))
        self.assertTrue(set(walls) | set(above) | {slab} <= set(layers))
        self.assertTrue(all(l["id"] == "bim_" + g and l["nodeIds"][0] == pe.three_name(node_of[g]["name"])
                            for g, l in layers.items()))
        self.assertEqual(layers[above[0]]["name"], layers[walls[0]]["name"])      # (shown as it is called)
        self.assertNotEqual(node_of[above[0]]["name"], node_of[walls[0]]["name"])
        self.assertEqual(done, {"elements": len(layers), "triangles": done["triangles"], "layers": len(layers),
                                "scenes": 5})
        scenes = model["scenes"]
        self.assertEqual([s["kind"] for s in scenes], ["overview", "view3d", "plan", "plan", "section"])
        self.assertEqual(model["initialSceneId"], scenes[0]["id"])
        b = model["bounds"]
        np.testing.assert_allclose(scenes[0]["camera"]["target"], (np.array(b["min"]) + b["max"]) / 2, atol=1e-3)
        eye_gl = np.asarray(scenes[0]["camera"]["position"]) - scenes[0]["camera"]["target"]
        self.assertTrue(eye_gl[1] > 0 and eye_gl[0] < 0 and eye_gl[2] > 0)   # (above, west, south: −Z is north)
        self.assertEqual(scenes[4]["id"], "bim_scene_corte_" + doc.sections[0].uid)
        self.assertTrue(all(s["hidden"] is False and s["transition"] == {"type": "smooth", "seconds": 1.2}
                            and not {"effect", "narration", "thumbnail"} & set(s) for s in scenes))
        to_gl = lambda p: gltf_export._y_up(np.asarray(p, dtype=float) - offset)[0]     # noqa: E731
        view = scenes[1]
        np.testing.assert_allclose(view["camera"]["position"], to_gl(eye), atol=1e-3)
        np.testing.assert_allclose(view["camera"]["target"], to_gl(focus), atol=1e-3)
        self.assertAlmostEqual(view["camera"]["fov"], math.degrees(2 * math.atan(math.tan(math.radians(25)) * 2
                                                                                 / (1 + 16 / 9))), places=2)
        self.assertEqual(view["hiddenLayers"], ["bim_" + slab])
        planes = view["section"]["planes"]
        keeps = lambda p, ps: all(np.dot(q["normal"], to_gl(p)) + q["constant"] >= -1e-9 for q in ps)  # noqa: E731
        self.assertEqual(len(planes), 6)
        self.assertTrue(keeps((1.0, 2.0, 1.0), planes) and not keeps((4.0, 2.0, 1.0), planes)
                        and not keeps((1.0, 2.0, 3.5), planes))
        ground, first = scenes[2], scenes[3]
        self.assertEqual(ground["section"]["planes"][0]["normal"], [0.0, -1.0, 0.0])
        self.assertTrue(keeps((1.0, 1.0, 1.1), ground["section"]["planes"])
                        and not keeps((1.0, 1.0, 1.3), ground["section"]["planes"]))
        self.assertEqual(set(ground["hiddenLayers"]), {"bim_" + g for g in above})
        self.assertTrue({"bim_" + g for g in walls} <= set(first["hiddenLayers"]))
        self.assertTrue(keeps((1.0, 1.0, 4.1), first["section"]["planes"]))
        cut = scenes[4]["section"]["planes"]
        self.assertTrue(keeps((1.0, 3.0, 1.0), cut) and not keeps((1.0, 1.0, 1.0), cut))
        self.assertFalse(model["sun"]["useRealSun"])
        bim.set_site_location(doc, 38.72, -9.14)
        _gltf, _bin, again = pe.package(doc)
        self.assertEqual((again["presentation"]["model3d"]["sun"]["useRealSun"],
                          again["presentation"]["model3d"]["sun"]["latitude"]), (True, 38.72))

    def test_presentation_choices(self):
        """0.363: the scenes chosen in the Presentation panel — the views as scenes (the general view, a named 3D view,
        the storey's plan, a section), each known by a key that stays when its view is renamed; the order changed,
        the entry chosen, one left out, a cut, an effect, a caption with its time; one undo step each; only what
        differs kept, with the project (saved and opened again); in the GLB the scenes in that order with what was
        chosen and the thumbnails given (base64 JPEG); an entry left out gives way to the first one in."""
        import base64

        from arqbim.i18n import t
        from arqbim.model import presentation as pm, presentation_export as pe
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        bim.add_wall_loop(doc, corners, spec)
        camera = {"position": (10.0, -8.0, 6.0), "rotation": (0.0, 0.0, 0.0, 1.0), "fov": 50.0, "width": 16.0,
                  "height": 9.0, "zoom": 1.0, "focus": np.array((2.5, 2.0, 1.0))}
        view = doc.add_view3d(camera)[1]
        doc.add_section(np.array((2.5, 2.0, 0.0)), np.array((0.0, 1.0, 0.0)))
        section = doc.sections[0]
        storey = next(g for g, _n, _z in doc.storeys())
        keys = [s.key for s in pm.scenes(doc)]
        self.assertEqual(keys, ["geral", "vista_" + view, "planta_" + storey, "corte_" + section.uid])
        self.assertEqual(pm.initial(doc), "geral")
        doc.rename_section(0, "Corte A")
        self.assertEqual([s.key for s in pm.scenes(doc)], keys)
        self.assertEqual(pm.scenes(doc)[3].view, ("section", "Corte A"))
        steps = len(doc._undo)
        doc.set_presentation(pm.ordered(doc.presentation, [keys[3], keys[1], keys[0]]))
        doc.set_presentation(pm.with_initial(doc.presentation, keys[1]))
        doc.set_presentation(pm.changed(doc.presentation, keys[0], hidden=True))
        doc.set_presentation(pm.changed(doc.presentation, keys[3], transition="cut", effect="construction",
                                        effect_s=12, caption="  O corte pela sala.  ", seconds=8))
        doc.set_presentation(pm.changed(doc.presentation, keys[3], transition_s=1.2, effect_s=99))   # (as usual; too long)
        self.assertEqual(len(doc._undo), steps + 5)
        found = pm.scenes(doc)
        self.assertEqual([s.key for s in found], [keys[3], keys[1], keys[0], keys[2]])   # (the plan not in the order: last)
        self.assertEqual((found[0].transition, found[0].effect, found[0].effect_s, found[0].caption, found[0].seconds),
                         ("cut", "construction", 60.0, "O corte pela sala.", 8.0))
        self.assertTrue(found[2].hidden)
        self.assertEqual(doc.presentation["scenes"][keys[3]], {"transition": "cut", "effect": "construction",
                                                               "effect_s": 60.0, "caption": "O corte pela sala.",
                                                               "seconds": 8.0})
        self.assertEqual(pm.initial(doc), keys[1])
        doc.undo()
        self.assertEqual(pm.scenes(doc)[0].effect_s, 12.0)
        doc.redo()
        jpeg = b"\xff\xd8\xff\xe0 thumbnail \xff\xd9"
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            self.assertEqual(again.presentation, doc.presentation)
            self.assertEqual(again.sections[0].uid, section.uid)
            self.assertEqual([s.key for s in pm.scenes(again)], [keys[3], keys[1], keys[0], keys[2]])
            glb = os.path.join(tmp, "casa.glb")
            done = pe.export(again, glb, "Casa", thumbnails={keys[1]: jpeg})
            model = pe.read(glb)["presentation"]["model3d"]
        self.assertEqual(done["scenes"], 4)
        scenes = model["scenes"]
        self.assertEqual([s["id"] for s in scenes], ["bim_scene_" + k for k in (keys[3], keys[1], keys[0], keys[2])])
        self.assertEqual([s["order"] for s in scenes], [0, 1, 2, 3])
        self.assertEqual(model["initialSceneId"], "bim_scene_" + keys[1])
        cut = scenes[0]
        self.assertEqual((cut["transition"], cut["effect"], cut["narration"]),
                         ({"type": "cut", "seconds": 1.2}, {"type": "construction", "seconds": 60.0},
                          {"caption": "O corte pela sala.", "seconds": 8.0}))
        self.assertEqual(cut["name"], t("present.section", name="Corte A"))
        self.assertTrue(scenes[2]["hidden"] and not scenes[1]["hidden"])
        self.assertEqual(scenes[1]["thumbnail"], {"mimeType": "image/jpeg",
                                                  "data": base64.b64encode(jpeg).decode("ascii")})
        self.assertNotIn("thumbnail", scenes[0])
        doc.set_presentation(pm.changed(pm.with_initial(doc.presentation, keys[0]), keys[1], hidden=True))
        self.assertEqual(pm.initial(doc), keys[3])          # (the entry left out: the first one in the sequence)
        self.assertEqual(pm.clean({"order": "x", "scenes": {"a": {"effect": "fogo", "hidden": 0, "z": 1}}}),
                         pm.empty())

    def test_presentation_tab_settings(self):
        """0.479: what the ArqSynth Presentation tab keeps of a scene — its camera's projection, lens (the Presentation's
        20–65°), lock, visual mode, quality, ambient occlusion, the layers it hides, where a view's scene looks from,
        a name of its own, left out of what is sent —, each kept only when it differs, in range, with the project; a
        3D view named as a scene («Cena 1», another «Cena 1 (2)»); «Cena N» free, «… cópia»; every scene's
        transition at once (one undo step); in the GLB: an orthographic camera with the Presentation's stored zoom (2
        / the height seen), the lens, the lock, the mode with its quality, the layers hidden in the scene, the general
        view seen from where it was kept, the scene taken out not sent."""
        from arqbim.model import presentation as pm, presentation_export as pe
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        walls = bim.add_wall_loop(doc, corners, spec)
        camera = {"position": (10.0, -8.0, 6.0), "rotation": (0.0, 0.0, 0.0, 1.0), "fov": 50.0, "width": 16.0,
                  "height": 9.0, "zoom": 1.0, "focus": np.array((2.5, 2.0, 1.0))}
        view = doc.add_view3d(camera, name="Cena 1")[1]
        again = doc.add_view3d(camera, name="Cena 1")[1]
        self.assertEqual((doc.view3d(view).name, doc.view3d(again).name), ("Cena 1", "Cena 1 (2)"))
        doc.remove_view3d(again)
        self.assertEqual(pm.free_name(["Cena 1", "cena 2", "Vista geral"], "Cena"), "Cena 3")
        self.assertEqual(pm.copy_name("Cena 1", ["Cena 1", "Cena 1 cópia"], "cópia"), "Cena 1 cópia 2")
        key, storey = "vista_" + view, next(g for g, _n, _z in doc.storeys())
        plan = "planta_" + storey
        data = pm.changed(doc.presentation, key, projection="orthographic", fov=10, locked=True, style="clay",
                          quality="high", ao=False, ao_intensity=3, hidden_layers=[walls[1], walls[0], walls[1]])
        data = pm.changed(data, key, style="fogo", projection="isometrica", quality="ultra")      # (not theirs: kept)
        data = pm.changed(data, "geral", eye=(-6, -6, 5), target=(2.5, 2.0, 1.0), fov=40, name="  Entrada  ")
        data = pm.changed(data, plan, omit=True)
        steps = len(doc._undo)
        doc.set_presentation(data)
        kept = doc.presentation["scenes"]
        self.assertEqual(kept[key], {"projection": "orthographic", "fov": 20.0, "locked": True, "style": "clay",
                                     "quality": "high", "ao": False, "ao_intensity": 2.0,
                                     "hidden_layers": tuple(sorted(walls[:2]))})
        self.assertEqual(kept["geral"], {"eye": (-6.0, -6.0, 5.0), "target": (2.5, 2.0, 1.0), "fov": 40.0,
                                         "name": "Entrada"})
        self.assertEqual([s.key for s in pm.scenes(doc)], ["geral", key])
        self.assertEqual([s.key for s in pm.omitted(doc)], [plan])
        self.assertEqual(pm.scenes(doc)[0].name, "Entrada")
        self.assertEqual(pm.changed(doc.presentation, key, fov=0, hidden_layers=[])["scenes"][key].get("fov"), None)
        doc.set_presentation(pm.changed_all(doc.presentation, [s.key for s in pm.scenes(doc)], transition_s=2.5))
        self.assertEqual(len(doc._undo), steps + 2)
        self.assertEqual({s.transition_s for s in pm.scenes(doc)}, {2.5})
        self.assertEqual(pm.transition_of(pm.scenes(doc)), 2.5)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.ifc")
            doc.save(path)
            opened = Document()
            opened.open(path)
            self.assertEqual(opened.presentation, doc.presentation)
            self.assertEqual(pm.scenes(opened)[1].hidden_layers, tuple(sorted(walls[:2])))
            glb = os.path.join(tmp, "casa.glb")
            done = pe.export(opened, glb, "Casa")
            model = pe.read(glb)["presentation"]["model3d"]
        self.assertEqual(done["scenes"], 2)
        scenes = {s["id"]: s for s in model["scenes"]}
        self.assertNotIn("bim_scene_" + plan, scenes)                 # (taken out: not sent)
        cam = scenes["bim_scene_" + key]["camera"]
        self.assertEqual((cam["projection"], cam["fov"], cam["locked"]), ("orthographic", 20.0, True))
        distance = float(np.linalg.norm(np.subtract(cam["target"], cam["position"])))
        lens = pe._view_camera(camera, np.asarray(model["offset"]))["fov"]
        height = 2.0 * distance * math.tan(math.radians(lens) / 2.0)
        self.assertAlmostEqual(cam["orthographicZoom"], 2.0 / height, places=4)
        style = scenes["bim_scene_" + key]["style"]
        self.assertEqual((style["mode"], style["qualityProfile"], style["ambientOcclusion"],
                          style["ambientOcclusionIntensity"]), ("clay", "high", False, 2.0))
        self.assertEqual(sorted(scenes["bim_scene_" + key]["hiddenLayers"]), sorted("bim_" + g for g in walls[:2]))
        general = scenes["bim_scene_geral"]
        offset = np.asarray(model["offset"])
        self.assertEqual(general["name"], "Entrada")
        self.assertEqual(general["camera"]["position"], pe._list(pe._gl((-6.0, -6.0, 5.0), offset)))
        self.assertEqual(general["camera"]["target"], pe._list(pe._gl((2.5, 2.0, 1.0), offset)))
        self.assertEqual((general["camera"]["projection"], general["camera"]["fov"]), ("perspective", 40.0))
        self.assertNotIn("qualityProfile", general["style"])          # (nothing of the look chosen: as before)
        self.assertEqual(general["transition"], {"type": "smooth", "seconds": 2.5})

    def test_presentation_cuts(self):
        """0.484: a scene's section planes (the Presentation tab's «Cortes») — kept (type, position, side turned), those
        that are not of the Presentation's types left out, at most six; what each keeps (horizontal: what is under its
        height; Vertical X: the low x side; Vertical Z: the high y side; turned: the other); in the GLB with the scene's
        other planes, as THREE.Plane keeps them, with the Presentation's types."""
        from arqbim.model import gltf_export, presentation as pm, presentation_export as pe
        self.assertEqual(pm.cut_plane("horizontal", 1.2), ((0.0, 0.0, -1.0), (0.0, 0.0, 1.2)))
        self.assertEqual(pm.cut_plane("horizontal", 1.2, True), ((0.0, 0.0, 1.0), (0.0, 0.0, 1.2)))
        self.assertEqual(pm.cut_plane("transversal", 2.0), ((-1.0, 0.0, 0.0), (2.0, 0.0, 0.0)))
        self.assertEqual(pm.cut_plane("longitudinal", 3.0), ((0.0, 1.0, 0.0), (0.0, 3.0, 0.0)))
        doc = Document()
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        bim.add_wall_loop(doc, corners, catalog.BY_KEY["parede_alv_20"])
        doc.set_presentation(pm.changed(doc.presentation, "geral", cuts=[
            ["horizontal", 1.25, False], ("transversal", 2, 1), ["inclinado", 1.0, False], {"type": "longitudinal",
                                                                                           "position": 3.0}]))
        self.assertEqual(pm.scenes(doc)[0].cuts, (("horizontal", 1.25, False), ("transversal", 2.0, True),
                                                  ("longitudinal", 3.0, False)))
        self.assertEqual(len(pm.changed(doc.presentation, "geral", cuts=[["horizontal", k, False]
                                                                         for k in range(9)])["scenes"]["geral"]["cuts"]),
                         pm.MAX_CUTS)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            self.assertEqual(pm.scenes(again)[0].cuts, pm.scenes(doc)[0].cuts)
            glb = os.path.join(tmp, "casa.glb")
            pe.export(again, glb, "Casa")
            model = pe.read(glb)["presentation"]["model3d"]
        offset = np.asarray(model["offset"])
        planes = {p["id"]: p for p in model["scenes"][0]["section"]["planes"]}
        self.assertEqual(sorted(planes), ["cut_geral_1", "cut_geral_2", "cut_geral_3"])
        self.assertEqual([planes["cut_geral_{}".format(k)]["type"] for k in (1, 2, 3)],
                         ["horizontal", "transversal", "longitudinal"])
        flat = planes["cut_geral_1"]
        self.assertEqual(flat["normal"], [0.0, -1.0, 0.0])
        self.assertAlmostEqual(flat["constant"], 1.25 - offset[2], places=4)
        under = gltf_export._y_up(np.array((1.0, 1.0, 1.0)) - offset)[0]                # (1 m high: kept)
        self.assertGreater(np.dot(flat["normal"], under) + flat["constant"], 0.0)
        self.assertIsNone(model["scenes"][1]["section"]["planes"][1:] or None)      # (the plan: its own cut only)

    def test_presentation_tags(self):
        """0.485: the labels put in the Presentation tab — the model's (kept with the file), each scene with those it
        hides (labels gone left out); in the GLB as the Presentation's SpaceLabels (its fields, «bim_tag_<id>», the
        point and the normal in its axes) and each scene's hiddenLabels."""
        from arqbim.model import gltf_export, presentation as pm, presentation_export as pe, presentation_tags as pt
        doc = Document()
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        bim.add_wall_loop(doc, corners, catalog.BY_KEY["parede_alv_20"])
        sala = pt.new_tag("floor", (2.0, 1.5, 0.0), (0.0, 0.0, 1.0))
        rua = pt.new_tag("wall_leader", (0.0, 2.0, 1.4), (-1.0, 0.0, 0.0), [sala], style={"background": "#ffcc00"})
        self.assertEqual([sala["title"], sala["number"], rua["title"], rua["number"]],
                         ["Ambiente 1", "01", "Ambiente 2", "02"])
        self.assertEqual(rua["background"], "#ffcc00")
        doc.set_presentation(pm.with_tags(doc.presentation, [sala, rua]))
        doc.set_presentation(pm.changed(doc.presentation, "geral", hidden_tags=[rua["id"], rua["id"], "gone"]))
        self.assertEqual([t["id"] for t in pm.tags(doc)], [sala["id"], rua["id"]])
        self.assertEqual(pm.scenes(doc)[0].hidden_tags, tuple(sorted((rua["id"], "gone"))))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            self.assertEqual(pm.tags(again), pm.tags(doc))
            glb = os.path.join(tmp, "casa.glb")
            pe.export(again, glb, "Casa")
            model = pe.read(glb)["presentation"]["model3d"]
        offset = np.asarray(model["offset"])
        labels = {label["id"]: label for label in model["labels"]}
        self.assertEqual(sorted(labels), sorted(["bim_tag_" + sala["id"], "bim_tag_" + rua["id"]]))
        put = labels["bim_tag_" + sala["id"]]
        self.assertEqual({k: put[k] for k in ("title", "number", "shape", "placement", "background", "textColor",
                                              "leaderLength", "faceCamera", "hideWhenOccluded")},
                         {"title": "Ambiente 1", "number": "01", "shape": "rect", "placement": "floor",
                          "background": "#9ec8a0", "textColor": "#111111", "leaderLength": 0.8, "faceCamera": False,
                          "hideWhenOccluded": True})
        np.testing.assert_allclose(put["position"], gltf_export._y_up(np.array((2.0, 1.5, 0.0)) - offset)[0],
                                   atol=1e-4)
        self.assertEqual(put["normal"], [0.0, 1.0, 0.0])                                # (up, in its axes)
        self.assertEqual(labels["bim_tag_" + rua["id"]]["normal"], [-1.0, 0.0, 0.0])
        self.assertEqual(model["scenes"][0]["hiddenLabels"], ["bim_tag_" + rua["id"]])  # (the one gone: left out)
        self.assertNotIn("hiddenLabels", model["scenes"][1])

    def test_presentation_tag_frames(self):
        """0.485: where a label is drawn, as the Presentation's — on a floor its top to the north, turned by its
        rotation; on a wall its top up; standing high on its posts (two, one for a circle), facing its normal or, when
        it faces the camera, the viewer; beside a wall at the end of its leader. Its quad as big as the Presentation's
        (0,55 m high a rectangle, 0,95 m a circle, by its scale); a turn near a multiple of 45° put on it."""
        from arqbim.model import presentation_tags as pt
        floor = pt.new_tag("floor", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        f = pt.frame(floor, 2.0)
        bl, br, tr, tl = (np.array(p) for p in f["corners"])
        np.testing.assert_allclose(br - bl, (1.1, 0.0, 0.0), atol=1e-9)                # (2 × 0,55 m wide, east)
        np.testing.assert_allclose(tl - bl, (0.0, 0.55, 0.0), atol=1e-9)               # (its top to the north)
        self.assertAlmostEqual(bl[2], pt.LIFT)
        turned = pt.frame(dict(floor, rotation=90.0), 2.0)
        np.testing.assert_allclose(np.array(turned["corners"][1]) - turned["corners"][0], (0.0, 1.1, 0.0), atol=1e-9)
        wall = pt.frame(pt.new_tag("wall", (0.0, 0.0, 1.5), (0.0, -1.0, 0.0)), 1.0)
        bl, br, tr, tl = (np.array(p) for p in wall["corners"])
        np.testing.assert_allclose(tl - bl, (0.0, 0.0, 0.55), atol=1e-9)               # (its top up)
        self.assertAlmostEqual(abs(br[0] - bl[0]), 0.55)
        stand = pt.new_tag("standing", (1.0, 1.0, 0.0), (0.0, 0.0, 1.0))
        s = pt.frame(stand, 1.0)
        self.assertEqual(len(s["lines"]), 2)
        self.assertAlmostEqual(min(p[2] for p in s["corners"]), 1.1)                   # (on its posts of 1,1 m)
        circle = pt.frame(dict(stand, shape="circle"), 1.0)
        self.assertEqual(len(circle["lines"]), 1)
        self.assertAlmostEqual(circle["corners"][3][2] - circle["corners"][0][2], 0.95)
        facing = pt.frame(dict(stand, face_camera=True), 1.0, toward=(1.0, 0.0, 0.2))
        a, b = np.array(facing["corners"][0]), np.array(facing["corners"][1])
        self.assertAlmostEqual(float((b - a) @ np.array((1.0, 0.0, 0.0))), 0.0)        # (square to the viewer)
        lead = pt.frame(pt.new_tag("wall_leader", (0.0, 0.0, 1.5), (-1.0, 0.0, 0.0)), 1.0)
        (start, end), = lead["lines"]
        self.assertAlmostEqual(math.dist(start, end), 0.8)
        self.assertEqual([pt.snap_angle(v) for v in (2.0, 47.0, 52.0, 357.0, 120.0)], [0.0, 45.0, 52.0, 0.0, 120.0])
        self.assertIsNone(pt.clean_tag({"title": "sem id"}))
        kept = pt.clean_tag(dict(floor, scale=99, background="verde", placement="tecto", normal=(0, 0, 0)))
        self.assertEqual([kept["scale"], kept["background"], kept["placement"], kept["normal"]],
                         [5.0, "#9ec8a0", "floor", (0.0, 0.0, 1.0)])
        self.assertEqual(pt.free_number([dict(floor, title="Ambiente 1"), dict(floor, title="Ambiente 3")], "Ambiente"),
                         2)

    def test_presentation_camera_moves(self):
        """0.364: a scene's camera move (one of the Presentation's) — chosen with its time, a name it does not know
        not kept; in the GLB: its name, its time (the move's own when none was given), the building's measures (the
        GLB's box: its middle, the radius round it, its size) and, for a move inside a room, the room the 3D view
        looks into (a room drawn: the middle of its floor, in the GLB); the BIM's preview the same move in the same
        place (the model's axes)."""
        from arqbim.model import camera_moves as cm, presentation as pm, presentation_export as pe
        doc = Document()
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (6.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        bim.add_wall_loop(doc, corners, catalog.BY_KEY["parede_alv_20"])
        room = bim.add_room(doc, (3.0, 2.0), "Sala")
        self.assertIsNotNone(room)
        camera = {"position": (3.0, -8.0, 6.0), "rotation": (0.0, 0.0, 0.0, 1.0), "fov": 50.0, "width": 16.0,
                  "height": 9.0, "zoom": 1.0, "focus": np.array((3.0, 2.0, 1.2))}
        view = doc.add_view3d(camera)[1]
        storey = next(g for g, _n, _z in doc.storeys())
        inside, plan = "vista_" + view, "planta_" + storey
        doc.set_presentation(pm.changed(doc.presentation, "geral", move="orbit_rising"))
        doc.set_presentation(pm.changed(doc.presentation, inside, move="int_orbit_full", move_s=10))
        doc.set_presentation(pm.changed(doc.presentation, plan, move="voo_rasante"))
        found = {s.key: s for s in pm.scenes(doc)}
        self.assertEqual((found[plan].move, found[inside].move_s), ("", 10.0))
        self.assertEqual(pm.room_of(doc, found[inside])["guid"], room)
        with tempfile.TemporaryDirectory() as tmp:
            glb = os.path.join(tmp, "casa.glb")
            pe.export(doc, glb, "Casa")
            model = pe.read(glb)["presentation"]["model3d"]
        by_id = {s["id"]: s for s in model["scenes"]}
        outer = by_id["bim_scene_geral"]["cameraMove"]
        self.assertEqual((outer["preset"], outer["seconds"]), ("orbit_rising", 14.0))
        lo, hi = np.array(model["bounds"]["min"]), np.array(model["bounds"]["max"])
        np.testing.assert_allclose(outer["building"]["center"], (lo + hi) / 2, atol=1e-3)
        self.assertAlmostEqual(outer["building"]["radius"], float(np.linalg.norm(hi - lo)) / 2, places=3)
        np.testing.assert_allclose(outer["building"]["size"], hi - lo, atol=1e-3)
        self.assertNotIn("room", outer)
        self.assertNotIn("cameraMove", by_id["bim_scene_" + plan])
        move = by_id["bim_scene_" + inside]["cameraMove"]
        self.assertEqual((move["preset"], move["seconds"]), ("int_orbit_full", 10.0))
        offset = np.asarray(model["offset"])
        floor = cm.to_model(move["room"]["center"], offset)
        self.assertTrue(abs(floor[0] - 3.0) < 0.05 and abs(floor[1] - 2.0) < 0.05 and abs(floor[2]) < 1e-6)
        self.assertEqual(move["room"]["half"], [2.9, 1.9])                 # (inside the walls' faces)
        frames = pm.move_frames(doc, found[inside])
        self.assertEqual(len(frames), 10 * 30 + 1)
        building = cm.Building(tuple(move["building"]["center"]), move["building"]["radius"],
                               tuple(move["building"]["size"]))
        r = move["room"]
        sent = cm.points(cm.params("int_orbit_full", building, cm.Room(tuple(r["center"]), tuple(r["half"]),
                                                                       r["inradius"], r["height"])))
        np.testing.assert_allclose(frames[0][0], cm.to_model(sent[0], offset), atol=2e-3)
        np.testing.assert_allclose(frames[-1][0], cm.to_model(sent[-1], offset), atol=2e-3)
        np.testing.assert_allclose(frames[0][1], (floor[0], floor[1], 1.5), atol=2e-3)

    def test_presentation_environment(self):
        """0.365: a scene's sun (a day, an hour, still or through the day or the year), exposure (kept within the
        Presentation's 0,3–1,6) and sky — in the GLB with each scene; the sun previewed: none without a site's place,
        else the Presentation's sun there (through the day: from sunrise to sunset); the materials the Presentation
        draws its own way by their finish — the window's glass, a pond's water — and the light fixtures, with their
        flux and their faces' materials."""
        from arqbim.model import presentation as pm, presentation_export as pe, presentation_sun as ps
        doc = Document()
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        walls = bim.add_wall_loop(doc, corners, catalog.BY_KEY["parede_alv_20"])
        bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, walls[0]), 2.0, -1)
        light = bim.add_light(doc, (2.5, 2.0), "downlight")
        pond = catalog.TypeSpec("lago", "slab", "Lago", "Pond", layers=(("agua", 0.10),))
        bim.add_slab(doc, np.array((6.0, 0.0, 0.0)), 2.0, 3.0, pond, function="acabamento")
        doc.set_presentation(pm.changed(doc.presentation, "geral", sun_day=355, sun_minutes=600, sun_animate="day",
                                        exposure=9, sky=True))
        doc.set_presentation(pm.changed(doc.presentation, "geral", sun_animate="lua"))          # (not one: not kept)
        scene = pm.scenes(doc)[0]
        self.assertEqual((scene.sun_day, scene.sun_minutes, scene.sun_animate, scene.exposure, scene.sky),
                         (355, 600, "day", 1.6, True))
        self.assertEqual(pm.sun_frames(doc, scene), [])                                         # (no site: no day)
        bim.set_site_location(doc, 38.72, -9.14)
        frames = pm.sun_frames(doc, scene, 12)
        self.assertEqual(len(frames), 12)
        rise, sets = ps.daylight(38.72, -9.14, 355)
        self.assertAlmostEqual(frames[0][2], rise)
        self.assertAlmostEqual(frames[-1][2], sets)
        np.testing.assert_allclose(frames[5][0], ps.direction(38.72, -9.14, 355, frames[5][2]))
        with tempfile.TemporaryDirectory() as tmp:
            glb = os.path.join(tmp, "casa.glb")
            pe.export(doc, glb, "Casa")
            model = pe.read(glb)["presentation"]["model3d"]
        geral = model["scenes"][0]
        self.assertEqual(geral["environment"], {"sun": {"day": 355, "minutes": 600, "animate": "day"},
                                                "exposure": 1.6, "sky": True})
        self.assertEqual(model["scenes"][1]["environment"]["sun"], {"day": 172, "minutes": 720, "animate": "none"})
        finishes = {m["finish"]: m for m in model["materials"]}
        self.assertEqual(set(finishes), {"glass", "water"})
        self.assertEqual(finishes["water"]["name"], catalog.MATERIALS["agua"].name_pt)
        self.assertRegex(finishes["glass"]["color"], r"^#[0-9a-f]{6}$")
        [fixture] = model["lights"]
        self.assertEqual(fixture["lumens"], 800.0)
        self.assertTrue(fixture["materials"] and fixture["nodeId"] in
                        {n for l in model["layers"] if l["globalId"] == light for n in l["nodeIds"]})

    def test_presentation_spaces(self):
        """0.366: the rooms for the Presentation's labels and Virtual Walk — a house of two rooms (a living room and a
        kitchen) with a door between them and one from outside into the living room: the storey as a floor, each room
        its outline in the GLB, its middle inside it, its number, area and kind by its name; the doors with the rooms on
        each side (the outside None) and the way through them; the walk starts in the room one comes in by. Both off:
        no rooms sent; their kind by their name."""
        from arqbim.model import presentation as pm, presentation_export as pe
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (8.0, 0.0, 0.0), (8.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        walls = bim.add_wall_loop(doc, corners, spec)
        inner = bim.add_wall(doc, np.array((4.0, 0.0, 0.0)), np.array((4.0, 4.0, 0.0)), spec)
        door = catalog.OPENING_BY_KEY["porta_90"]
        bim.add_opening(doc, walls[0], door, bim.wall_frame(doc, walls[0]), 2.0, -1)
        bim.add_opening(doc, inner, door, bim.wall_frame(doc, inner), 2.0, -1)
        living = bim.add_room(doc, (2.0, 2.0), "Sala de estar")
        kitchen = bim.add_room(doc, (6.0, 2.0), "Cozinha")
        self.assertTrue(living and kitchen)
        with tempfile.TemporaryDirectory() as tmp:
            glb = os.path.join(tmp, "casa.glb")
            pe.export(doc, glb, "Casa")
            model = pe.read(glb)["presentation"]["model3d"]
        found = model["spaces"]
        offset = np.asarray(model["offset"])
        self.assertEqual((found["labels"], found["walk"]), (True, True))
        self.assertEqual([f["name"] for f in found["floors"]], [next(n for _g, n, _z in doc.storeys())])
        rooms = {r["id"]: r for r in found["rooms"]}
        self.assertEqual({rooms[living]["kind"], rooms[kitchen]["kind"]}, {"room", "kitchen"})
        self.assertAlmostEqual(rooms[living]["area"], 3.8 * 3.8, places=2)     # (inside the walls' faces)
        centre = rooms[kitchen]["center"]
        self.assertAlmostEqual(centre[0] + offset[0], 6.0, places=2)
        self.assertAlmostEqual(-centre[2] + offset[1], 2.0, places=1)
        doors = sorted(found["doors"], key=lambda d: d["to"] is None)
        self.assertEqual(len(doors), 2)
        between, outside = doors
        self.assertEqual({between["from"], between["to"]}, {living, kitchen})
        self.assertEqual((outside["from"], outside["to"]), (living, None))
        way = np.asarray(between["way"])
        to_kitchen = 1.0 if between["to"] == kitchen else -1.0
        np.testing.assert_allclose(way, (to_kitchen, 0.0, 0.0), atol=1e-6)    # (+x in the GLB: towards the kitchen)
        self.assertLess(abs(between["point"][0] + offset[0] - 4.0), 0.05)       # (in the wall: its leaf, its handle)
        self.assertEqual(found["start"], living)
        doc.set_presentation(pm.with_options(doc.presentation, labels=False, walk=False))
        _gltf, _bin, again = pe.package(doc)
        self.assertNotIn("spaces", again["presentation"]["model3d"])
        self.assertEqual([pm.room_kind(n) for n in ("Quarto 2", "WC suite", "Hall de entrada", "Varanda", "Sala")],
                         ["bedroom", "bathroom", "entry", "balcony", "room"])
        self.assertEqual(pm.room_kind("Pátio", external=True), "exterior")

    def test_presentation_package(self):
        """0.367: the package for the Presentation — the rooms of a plan placed on a sheet as zones of its page (as
        ui/pdf draws the plan: its middle at the frame's centre, at 1:scale, y down; in hundredths of the page), a room
        cropped out of the plan left out; the ZIP: the manifest (the GLB's envelope with `package`, its checksum over
        the rest), the GLB, each page's PDF; read back; a file name given once."""
        import json
        import zipfile

        from arqbim.model import drawings, gltf_export, presentation_export as pe, presentation_package as pp
        from arqbim.model import sheets as sheets_model
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (8.0, 0.0, 0.0), (8.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        bim.add_wall_loop(doc, corners, spec)
        bim.add_wall(doc, np.array((4.0, 0.0, 0.0)), np.array((4.0, 4.0, 0.0)), spec)
        living = bim.add_room(doc, (2.0, 2.0), "Sala")
        bim.add_room(doc, (6.0, 2.0), "Cozinha")
        storey = next(g for g, _n, _z in doc.storeys())
        drawing = drawings.plan(doc, storey, "Planta")
        frame = sheets_model.Frame(50, (200.0, 140.0), 0, 0)
        zones = pp.page_zones(doc, [(drawing, frame, ("plan", storey))], (420.0, 297.0))
        self.assertEqual(len(zones), 2)
        lo, hi = (np.asarray(c, dtype=float) for c in drawing.bounds())
        middle = (lo + hi) / 2
        sala = next(z for z in zones if z["room"] == living)
        corner = next(p for p in doc.ifc.space_info(living)["outline"])
        x = (200.0 + (corner[0] - middle[0]) * 1000.0 / 50) / 420.0 * 100.0
        y = (140.0 - (corner[1] - middle[1]) * 1000.0 / 50) / 297.0 * 100.0
        np.testing.assert_allclose(sala["points"][0], (x, y), atol=1e-3)
        self.assertEqual((sala["name"], sala["kind"], sala["area"]), ("Sala", "room", 14.44))
        self.assertEqual(pp.page_zones(doc, [(drawing, frame, ("section", "Corte 1"))], (420.0, 297.0)), [])
        cropped = drawings.crop(drawing, (0.0, 0.0, 4.0, 4.0)) if hasattr(drawings, "crop") else None
        if cropped is not None and cropped.bounds() is not None:
            names = {z["name"] for z in pp.page_zones(doc, [(cropped, frame, ("plan", storey))], (420.0, 297.0))}
            self.assertNotIn("Cozinha", names)
        used = set()
        self.assertEqual((pp.file_name("A-01", "Planta: Térreo", used), pp.file_name("A-01", "Planta: Térreo", used)),
                         ("folhas/A-01 Planta- Térreo.pdf", "folhas/A-01 Planta- Térreo (2).pdf"))
        gltf, binary, description = pe.package(doc, "Casa")
        page = {"id": "bim_sheet_x", "title": "A-01 Planta", "file": "folhas/A-01 Planta.pdf", "size": [420.0, 297.0],
                "zones": zones}
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.zip")
            written = pp.write(path, gltf_export.glb(gltf, binary), description, [page],
                               {page["file"]: b"%PDF-1.4 folha"})
            manifest, files = pp.read(path)
            with zipfile.ZipFile(path) as z:
                stored = {i.filename: i.compress_type for i in z.infolist()}
        self.assertEqual(manifest, written)
        self.assertNotIn("presentation", manifest)
        self.assertEqual((manifest["target"]["code"], manifest["package"]["model"], manifest["package"]["pages"][0]["id"]),
                         ("presentation", "modelo.glb", "bim_sheet_x"))
        rest = {k: v for k, v in manifest.items() if k != "checksum"}
        self.assertEqual(manifest["checksum"], pe.checksum(json.dumps(rest, ensure_ascii=False, separators=(",", ":"))))
        self.assertEqual((files["modelo.glb"][:4], files[page["file"]]), (b"glTF", b"%PDF-1.4 folha"))
        self.assertEqual(stored["modelo.glb"], zipfile.ZIP_STORED)
        self.assertIsNone(pp.read(path + ".nada"))

    def test_presentation_panoramas(self):
        """0.368: the 360° panoramas — kept with the views (one undo step a change, saved and read back with the
        project, their pictures in «<projeto> - panoramas» beside it), named one more than the highest; in the
        package: on the plans of their storey where their eye is (as the rooms' zones, in hundredths of the page), one
        out of the plan's drawing nowhere, each with its picture (stored, a JPEG does not shrink)."""
        import zipfile

        from arqbim.model import drawings, gltf_export, panoramas as pn, presentation_export as pe
        from arqbim.model import presentation_package as pp, sheets as sheets_model
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (8.0, 0.0, 0.0), (8.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
        bim.add_wall_loop(doc, corners, spec)
        storey = next(g for g, _n, _z in doc.storeys())
        self.assertIsNone(pn.folder(doc))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.ifc")
            doc.save(path)
            self.assertEqual(pn.folder(doc), os.path.join(tmp, "casa - panoramas"))
            os.makedirs(pn.folder(doc))
            self.assertEqual(pn.next_name(doc, "Panorama"), "Panorama 1")
            sala = pn.made(doc, "a.jpg", "Panorama 1", (2.0, 2.0, 1.6, 9.0), (0.0, 1.0, 0.2), storey)
            fora = pn.made(doc, "b.jpg", "Panorama 2", (20.0, 2.0, 1.6), (1.0, 0.0), storey)
            for p, data in ((sala, b"\xff\xd8sala"), (fora, b"\xff\xd8fora")):
                with open(pn.path_of(doc, p), "wb") as fh:
                    fh.write(data)
            self.assertEqual((sala["file"], sala["eye"], sala["forward"]), ("casa - panoramas/a.jpg", [2.0, 2.0, 1.6],
                                                                             [0.0, 1.0]))
            steps = len(doc._undo)
            doc.set_panoramas(pn.with_added(doc.panoramas, sala), "cmd.panorama")
            doc.set_panoramas(pn.with_added(doc.panoramas, fora), "cmd.panorama")
            self.assertEqual((len(doc._undo), pn.next_name(doc, "Panorama")), (steps + 2, "Panorama 3"))
            doc.undo()
            self.assertEqual([p["uid"] for p in doc.panoramas], [sala["uid"]])
            doc.redo()
            doc.save(path)
            again = Document()
            again.open(path)
            self.assertEqual(again.panoramas, doc.panoramas)
            self.assertEqual(pn.clean([{"uid": "x"}, {"uid": "y", "file": "f", "eye": (1, 2, 3), "forward": "ab"}]), [])
            self.assertEqual([p["uid"] for p in pn.without(doc.panoramas, sala["uid"])], [fora["uid"]])
            drawing = drawings.plan(doc, storey, "Planta")
            frame = sheets_model.Frame(50, (200.0, 140.0), 0, 0)
            placed = [(drawing, frame, ("plan", storey))]
            points = pp.panorama_points(placed, (420.0, 297.0), doc.panoramas)
            self.assertEqual([uid for uid, _x, _y in points], [sala["uid"]])           # (the other: outside the plan)
            room = {"guid": "r", "name": "Sala", "storey": storey, "height": 2.7,
                    "outline": [(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)]}
            label = pp.page_zones(doc, placed, (420.0, 297.0), rooms=[room])[0]["label"]
            np.testing.assert_allclose(points[0][1:], label, atol=1e-3)                # (the room's middle: there)
            self.assertEqual(pp.panorama_points([(drawing, frame, ("section", "x"))], (420.0, 297.0), doc.panoramas), [])
            entries = pp.panorama_entries(doc.panoramas, {"bim_sheet_x": points})
            self.assertEqual(entries[0], {"id": "bim_pano_" + sala["uid"], "name": "Panorama 1",
                                          "file": "panoramas/{}.jpg".format(sala["uid"]),
                                          "placements": [{"page": "bim_sheet_x", "x": points[0][1], "y": points[0][2]}]})
            self.assertEqual(entries[1]["placements"], [])
            gltf, binary, description = pe.package(doc, "Casa")
            pictures = {e["file"]: data for e, data in zip(entries, (b"\xff\xd8sala", b"\xff\xd8fora"))}
            zip_path = os.path.join(tmp, "casa.zip")
            written = pp.write(zip_path, gltf_export.glb(gltf, binary), description, [], {}, entries, pictures)
            manifest, files = pp.read(zip_path)
            with zipfile.ZipFile(zip_path) as z:
                stored = {i.filename: i.compress_type for i in z.infolist()}
        self.assertEqual((manifest, manifest["package"]["panoramas"]), (written, entries))
        self.assertEqual(files[entries[0]["file"]], b"\xff\xd8sala")
        self.assertEqual(stored[entries[1]["file"]], zipfile.ZIP_STORED)

    def test_planar_faces(self):
        """0.350: triangles joined into flat faces, as SketchUp draws them — a box's twelve its six faces (four corners
        each, counter-clockwise seen from outside), a wall's face with a window triangulated around it one face with
        its hole (clockwise), a fan of triangles on one line's points one face without them; a ring whose hole touches
        its outline at a corner its triangles alone, two squares apart in one plane two faces; a rectangle with a
        T-junction inside (a vertex on one side of a line only) one face of four corners, no slit."""
        from arqbim.model import cad3d_export
        box = sg.rectangle_mesh(2.0, 1.0)
        sg.push_pull(box, 0, np.eye(4), 3.0)
        tris = np.asarray(box.triangulate()[0], dtype=np.int64).reshape(-1, 3)
        corners = np.asarray(box.verts, dtype=float).reshape(-1, 3)[tris]
        points, faces = cad3d_export.planar_faces(corners)
        self.assertEqual(len(faces), 6)
        self.assertTrue(all(len(outer) == 4 and not holes for outer, holes in faces))
        centre = points.mean(axis=0)
        for outer, _h in faces:
            p = points[outer]
            n = np.cross(p, np.roll(p, -1, axis=0)).sum(axis=0)
            self.assertGreater(float(np.dot(n, p.mean(axis=0) - centre)), 0.0)      # (facing out)
        o = [(0, 0), (4, 0), (4, 3), (0, 3)]
        h = [(1, 1), (2, 1), (2, 2), (1, 2)]
        flat = [(o[0], o[1], h[0]), (o[1], h[1], h[0]), (o[1], o[2], h[1]), (o[2], h[2], h[1]),
                (o[2], o[3], h[2]), (o[3], h[3], h[2]), (o[3], o[0], h[3]), (o[0], h[0], h[3])]
        corners = np.array([[(x, 0.0, z) for x, z in tri] for tri in flat])          # (in the plane y = 0)
        corners = corners[:, ::-1]                       # (seen from −y: its front)
        points, faces = cad3d_export.planar_faces(corners)
        self.assertEqual(len(faces), 1)
        outer, holes = faces[0]
        self.assertEqual((len(outer), len(holes), len(holes[0])), (4, 1, 4))
        fan = np.array([[(0, 0, 0), (1, 0, 0), (1, 1, 0)], [(0, 0, 0), (1, 1, 0), (0.5, 1, 0)],
                        [(0, 0, 0), (0.5, 1, 0), (0, 1, 0)]], dtype=float)
        _p, faces = cad3d_export.planar_faces(fan)
        self.assertEqual([len(f[0]) for f in faces], [4])                          # (the point (0.5, 1) gone)
        squares = [(x, y) for x in range(3) for y in range(3) if (x, y) not in ((1, 1), (2, 2))]
        ring = np.array([tri for x, y in squares
                         for tri in (((x, y, 0), (x + 1, y, 0), (x + 1, y + 1, 0)),
                                     ((x, y, 0), (x + 1, y + 1, 0), (x, y + 1, 0)))], dtype=float)
        _p, faces = cad3d_export.planar_faces(ring)       # (its hole and its notch touching at (2, 2): no one loop)
        self.assertEqual(sorted(len(f[0]) for f in faces), [3] * 14)
        _p, faces = cad3d_export.planar_faces(ring[[0, 1, 4, 5]])    # (two squares apart in one plane: two faces)
        self.assertEqual(sorted(len(f[0]) for f in faces), [4, 4])
        _p, faces = cad3d_export.planar_faces(ring[:4])   # (two side by side: one, the points between them gone)
        self.assertEqual([len(f[0]) for f in faces], [4])
        tee = np.array([[(0, 0, 0), (1, 0, 0), (1, 0.5, 0)], [(0, 0, 0), (1, 0.5, 0), (1, 1, 0)],
                        [(0, 0, 0), (1, 1, 0), (0, 1, 0)], [(1, 0, 0), (3, 0, 0), (3, 1, 0)],
                        [(1, 0, 0), (3, 1, 0), (1, 1, 0)], [(0, 1, 0), (1, 1, 0), (0, 2, 0)],
                        [(1, 1, 0), (3, 1, 0), (3, 2, 0)], [(1, 1, 0), (3, 2, 0), (0, 2, 0)]], dtype=float)
        points, faces = cad3d_export.planar_faces(tee)    # (a vertex on one side of x = 1 only: no slit left)
        self.assertEqual([(len(f[0]), len(f[1])) for f in faces], [(4, 0)])
        self.assertEqual(sorted(map(tuple, points[faces[0][0]].tolist())),
                         [(0, 0, 0), (0, 2, 0), (3, 0, 0), (3, 2, 0)])

    def test_usdz(self):
        """0.371: the room as USDZ (augmented reality on an iPhone or iPad), read back with USD itself: a zip of one
        binary layer stored as it is (what AR Quick Look asks); Y up, metres, its default prim the model, named after
        it; storey ▸ category ▸ element prims shown by their names, each wall's GlobalId, class and type in its data; a
        mesh an element's material, flat, never subdivided, its points and normals one each a corner, every triangle
        the GLB's; each material a UsdPreviewSurface in its colour (linear) — the window's glass see-through, with its
        index of refraction; standing on the floor (its lowest point at 0), its middle over the origin."""
        import importlib.util
        import zipfile
        if importlib.util.find_spec("pxr") is None:
            self.skipTest("usd-core not installed")
        from pxr import Usd, UsdGeom, UsdShade
        from arqbim.i18n import t
        from arqbim.model import gltf_export, usdz_export
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        walls = [bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
                 for a, b in (((0.0, 0.0), (5.0, 0.0)), ((5.0, 0.0), (5.0, 4.0)), ((5.0, 4.0), (0.0, 4.0)),
                              ((0.0, 4.0), (0.0, 0.0)))]
        bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, walls[0]), 2.0, -1)
        elements, materials = gltf_export.gather(doc, list(doc.objects.values()))
        gltf, _binary = gltf_export.build(elements, materials, "Sala")
        glb_triangles = sum(gltf["accessors"][p["attributes"]["POSITION"]]["count"] // 3
                            for m in gltf["meshes"] for p in m["primitives"])
        storey = next(n for _g, n, _z in doc.storeys())
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sala.usdz")
            n, triangles = usdz_export.write_usdz(path, elements, materials, "Sala")
            with zipfile.ZipFile(path) as z:
                stored = [(i.filename, i.compress_type) for i in z.infolist()]
            stage = Usd.Stage.Open(path)
            self.assertEqual(stored, [("modelo.usdc", zipfile.ZIP_STORED)])
            self.assertEqual((n, triangles), (5, glb_triangles))
            self.assertEqual((UsdGeom.GetStageUpAxis(stage), UsdGeom.GetStageMetersPerUnit(stage)), ("Y", 1.0))
            model = stage.GetDefaultPrim()
            self.assertEqual((str(model.GetPath()), model.GetDisplayName()), ("/Modelo", "Sala"))
            meshes = [p for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)]
            self.assertEqual(len(meshes), sum(len(e["parts"]) for e in elements))
            counted = 0
            for prim in meshes:
                mesh = UsdGeom.Mesh(prim)
                points, normals = mesh.GetPointsAttr().Get(), mesh.GetNormalsAttr().Get()
                self.assertEqual((len(points), len(normals), mesh.GetSubdivisionSchemeAttr().Get()),
                                 (3 * len(mesh.GetFaceVertexCountsAttr().Get()), len(points), "none"))
                counted += len(mesh.GetFaceVertexCountsAttr().Get())
            self.assertEqual(counted, triangles)
            wall = next(p for p in meshes if p.GetParent().GetCustomDataByKey("GlobalId") == walls[0]).GetParent()
            self.assertEqual((wall.GetParent().GetDisplayName(), wall.GetParent().GetParent().GetDisplayName()),
                             (t("tree.cat.IfcWall"), storey))
            self.assertEqual((wall.GetCustomDataByKey("ifcClass"), wall.GetCustomDataByKey("type")),
                             ("IfcWall", spec.name_pt))
            surfaces = {}
            for prim in meshes:
                material = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()[0]
                surfaces[material.GetPrim().GetDisplayName()] = UsdShade.Shader(material.GetPrim().GetChild("Superficie"))
            glass = next(k for k, m in materials.items() if m["finish"] == "glass")
            shader = surfaces[materials[glass]["name"]]
            self.assertLess(shader.GetInput("opacity").Get(), 1.0)
            self.assertAlmostEqual(shader.GetInput("ior").Get(), 1.5)
            plaster = next(k for k, m in materials.items() if m["finish"] != "glass")
            np.testing.assert_allclose(tuple(surfaces[materials[plaster]["name"]].GetInput("diffuseColor").Get()),
                                       gltf_export._linear(materials[plaster]["rgb"]), atol=1e-6)
            box = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default"]).ComputeWorldBound(model).ComputeAlignedRange()
            lo, hi = np.array(box.GetMin()), np.array(box.GetMax())
            del stage
        self.assertAlmostEqual(lo[1], 0.0, places=5)                        # (on the floor)
        np.testing.assert_allclose((lo[0] + hi[0], lo[2] + hi[2]), (0.0, 0.0), atol=1e-5)

    def test_3dm_skp(self):
        """0.350: the room in Rhino's 3DM — read back with rhino3dm: metres; a layer a storey with its categories'
        inside («Storey::Paredes»); each wall's meshes named after it with its GlobalId, class and type as user text,
        on its layer, in its material (the plaster's there, the glass see-through); every triangle's area there — and
        in SketchUp's SKP, read back with OpenSKP: a group an element, named, tagged «Storey - Paredes», its data in the
        «ArqSynth» dictionary; the faces whole (fewer than the triangles), the same area; inches inside, so the room's
        size in metres when read."""
        import openskp
        import rhino3dm
        from arqbim.i18n import t
        from arqbim.model import cad3d_export, gltf_export
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        walls = [bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
                 for a, b in (((0.0, 0.0), (5.0, 0.0)), ((5.0, 0.0), (5.0, 4.0)), ((5.0, 4.0), (0.0, 4.0)),
                              ((0.0, 4.0), (0.0, 0.0)))]
        bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, walls[0]), 2.0, -1)
        top = float(doc.get(walls[0]).mesh.bounds()[1][2])
        elements, materials = gltf_export.gather(doc, list(doc.objects.values()))
        area = sum(float(np.linalg.norm(np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0]), axis=1).sum()) / 2.0
                   for e in elements for c in e["parts"].values())
        storey = next(n for _g, n, _z in doc.storeys())
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sala.3dm")
            n, triangles = cad3d_export.write_3dm(path, elements, materials)
            model = rhino3dm.File3dm.Read(path)
            skp = os.path.join(tmp, "sala.skp")
            n2, triangles2 = cad3d_export.write_skp(skp, elements, materials)
            parsed = openskp.SkpFile(skp).parse()
            scene = openskp.SkpFile(skp).build_scene()
        self.assertEqual((n, n2, triangles2), (5, 5, triangles))
        self.assertEqual(model.Settings.ModelUnitSystem, rhino3dm.UnitSystem.Meters)
        layers = {lay.FullPath: lay.Index for lay in model.Layers}
        wall_layer = "{}::{}".format(storey, t("tree.cat.IfcWall"))
        self.assertIn(wall_layer, layers)
        objs = list(model.Objects)
        mats = list(model.Materials)
        in_walls = [o for o in objs if o.Attributes.GetUserString("ifcClass") == "IfcWall"]
        self.assertEqual({o.Attributes.GetUserString("GlobalId") for o in in_walls}, set(walls))
        self.assertTrue(all(o.Attributes.LayerIndex == layers[wall_layer] for o in in_walls))
        self.assertTrue(all(o.Attributes.GetUserString("type") == spec.name_pt for o in in_walls))
        self.assertTrue(all(o.Attributes.Name == doc.get(o.Attributes.GetUserString("GlobalId")).name
                            for o in in_walls))
        self.assertIn(catalog.MATERIALS["reboco"].name_pt, {m.Name for m in mats})
        self.assertTrue(any(m.Transparency > 0.3 for m in mats))
        written = 0.0
        for o in objs:
            v = np.array([[p.X, p.Y, p.Z] for p in o.Geometry.Vertices])
            f = np.array([[q[0], q[1], q[2]] for q in o.Geometry.Faces])
            c = v[f]
            written += float(np.linalg.norm(np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0]), axis=1).sum()) / 2.0
        self.assertAlmostEqual(written / area, 1.0, places=4)
        groups = parsed.root.instances
        self.assertEqual(len(groups), 5)
        mine = [g for g in groups if g.attribute_dictionaries.get(cad3d_export.DICT, {}).get("ifcClass") == "IfcWall"]
        self.assertEqual({g.attribute_dictionaries[cad3d_export.DICT]["GlobalId"] for g in mine}, set(walls))
        self.assertTrue(all(g.layer == "{} - {}".format(storey, t("tree.cat.IfcWall")) for g in mine))
        self.assertTrue(all(g.name == doc.get(g.attribute_dictionaries[cad3d_export.DICT]["GlobalId"]).name
                            for g in mine))
        faces = sum(len(d.faces) for d in parsed.definitions.values())
        self.assertLess(faces, triangles / 2)                                       # (whole faces, not triangles)
        drawn, low, high = 0.0, np.full(3, np.inf), np.full(3, -np.inf)
        for p in scene.glb_primitives:
            pos = np.asarray(p.positions, dtype=float).reshape(-1, 3)
            c = pos[np.asarray(p.indices, dtype=np.int64).reshape(-1, 3)]
            drawn += float(np.linalg.norm(np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0]), axis=1).sum()) / 2.0
            low, high = np.minimum(low, pos.min(axis=0)), np.maximum(high, pos.max(axis=0))
        self.assertAlmostEqual(float(high[1] - low[1]), top, places=3)               # (Y up, metres: the walls' height)
        self.assertAlmostEqual(float(high[0] - low[0]), 5.2, delta=0.01)
        self.assertGreater(drawn / area, 0.99)

    def test_import_round_trip(self):
        """0.351: the room written in each format and read back (model/mesh_import.read), in metres with Z up — the
        same box (5,20 × 4,20 × its height, where it was), the same area; SKP, 3DM and GLB saying their unit, the
        plaster's colour among their parts (GLB: back from linear); OBJ asking (Y up, metres guessed), STL at 1:100 read
        in millimetres the size of a scale model (52 mm). Then into a new project: as a component where it was in the
        file — a type with a face set a material, each styled in its colour (the glass see-through), a copy there in
        those colours —; as a sketch: its faces whole, the same area."""
        from arqbim.model import cad3d_export, gltf_export, mesh_export, mesh_import
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        walls = [bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
                 for a, b in (((0.0, 0.0), (5.0, 0.0)), ((5.0, 0.0), (5.0, 4.0)), ((5.0, 4.0), (0.0, 4.0)),
                              ((0.0, 4.0), (0.0, 0.0)))]
        bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, walls[0]), 2.0, -1)
        elements, materials = gltf_export.gather(doc, list(doc.objects.values()))
        everything = np.concatenate([c.reshape(-1, 3, 3) for e in elements for c in e["parts"].values()])
        lo, hi = everything.reshape(-1, 3).min(axis=0), everything.reshape(-1, 3).max(axis=0)

        def area(c):
            c = np.asarray(c, dtype=float).reshape(-1, 3, 3)
            return float(np.linalg.norm(np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0]), axis=1).sum()) / 2.0

        plaster = np.array(catalog.MATERIALS["reboco"].color, dtype=float)
        read = {}
        with tempfile.TemporaryDirectory() as tmp:
            for kind in ("skp", "3dm", "glb", "obj", "stl"):
                path = os.path.join(tmp, "sala." + kind)
                if kind == "skp":
                    cad3d_export.write_skp(path, elements, materials)
                elif kind == "3dm":
                    cad3d_export.write_3dm(path, elements, materials)
                elif kind == "glb":
                    gltf_export.export(doc, list(doc.objects.values()), path, "Sala")
                elif kind == "obj":
                    mesh_export.write_obj(path, elements, materials)
                else:
                    mesh_export.write_stl(path, elements, 100)
                read[kind] = mesh_import.read(path)
            with self.assertRaises(ValueError):
                mesh_import.read(os.path.join(tmp, "sala.mtl"))
        for kind, model in read.items():
            parts = model.parts_m("mm" if kind == "stl" else None)
            pts = np.concatenate([c.reshape(-1, 3) for c in parts.values()])
            size = pts.max(axis=0) - pts.min(axis=0)
            if kind == "stl":
                np.testing.assert_allclose(size, (hi - lo) / 100.0, atol=1e-4)
                continue
            np.testing.assert_allclose(size, hi - lo, atol=2e-3, err_msg=kind)
            self.assertAlmostEqual(sum(area(c) for c in parts.values()) / area(everything), 1.0, places=3, msg=kind)
            if kind in ("skp", "3dm"):                    # (at the model's own coordinates; the others moved)
                np.testing.assert_allclose(pts.min(axis=0), lo, atol=1e-3)
            colours = np.array([k[1] for k in model.parts])
            self.assertTrue(np.any(np.all(np.abs(colours - plaster) < 0.01, axis=1)), kind)
        self.assertEqual([read[k].known for k in ("skp", "3dm", "glb", "obj")], [True, True, True, False])
        self.assertEqual((read["obj"].unit, read["obj"].up), ("m", "y"))
        self.assertTrue(any(alpha < 0.9 for _n, _rgb, alpha in read["glb"].parts))           # (the glass)
        new = Document()
        type_guid = bim.import_model_component(new, read["skp"], "Sala", "generic", in_place=True)
        type_ = new.ifc.by_guid(type_guid)
        items = type_.RepresentationMaps[0].MappedRepresentation.Items
        self.assertEqual(len(items), len(read["skp"].parts))
        self.assertTrue(all(i.is_a("IfcTriangulatedFaceSet") and i.StyledByItem for i in items))
        shading = [s for i in items for s in i.StyledByItem[0].Styles[0].Styles]
        self.assertTrue(any((getattr(s, "Transparency", None) or 0.0) > 0.1 for s in shading))     # (the glass)
        copies = new.ifc.component_instances(type_guid)
        self.assertEqual(len(copies), 1)
        mesh = new.get(copies[0]).mesh
        clo, chi = mesh.bounds()
        np.testing.assert_allclose(clo, lo, atol=1e-3)
        np.testing.assert_allclose(chi, hi, atol=1e-3)
        self.assertIsNotNone(mesh.colors)
        self.assertTrue(np.any(np.all(np.abs(np.asarray(mesh.colors, dtype=float) - plaster) < 0.01, axis=1)))
        sketch_id = bim.import_model_sketch(new, read["obj"], "Sala")
        sketch = new.get(sketch_id)
        self.assertFalse(sketch.is_bim)
        self.assertLess(len(sketch.mesh.faces), read["obj"].triangles() / 2)
        tris, _owner = sketch.mesh.triangulate()
        verts = np.asarray(sketch.mesh.verts, dtype=float).reshape(-1, 3) + sketch.matrix[:3, 3]
        self.assertAlmostEqual(area(verts[np.asarray(tris, dtype=np.int64).reshape(-1, 3)]) / area(everything), 1.0,
                               places=3)
        new.modified = False

    # (0.457) The Rhino file with a block is written in a process of its own, with rhino3dm alone: its
    # InstanceDefinitions.Add corrupts memory now and then (a crash, «Segmentation fault») once IfcOpenShell or Qt are
    # loaded in the same process — rhino3dm's, not the program's (which only reads blocks: mesh_import).
    BLOCKS_3DM = r'''
import math, sys
import rhino3dm as rh
f = rh.File3dm()
f.Settings.ModelUnitSystem = rh.UnitSystem.Millimeters
mat = rh.Material()
mat.Name = "Madeira"
mat.DiffuseColor = (150, 100, 50, 255)
mi = f.Materials.Add(mat)
box = rh.Mesh()
for p in ((0, 0, 0), (1000, 0, 0), (1000, 500, 0), (0, 500, 0), (0, 0, 800), (1000, 0, 800),
          (1000, 500, 800), (0, 500, 800)):
    box.Vertices.Add(*p)
for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
    box.Faces.AddFace(*q)
attr = rh.ObjectAttributes()
attr.MaterialIndex = mi
attr.MaterialSource = rh.ObjectMaterialSource.MaterialFromObject
index = f.InstanceDefinitions.Add("Caixa", "", "", "", rh.Point3d(0, 0, 0), (box,), (attr,))
idef = f.InstanceDefinitions.FindIndex(index)
f.Objects.AddInstanceObject(rh.InstanceReference(idef.Id, rh.Transform.Identity()))
turn = rh.Transform.Multiply(rh.Transform.Translation(2000, 0, 0),
                             rh.Transform.Rotation(math.pi / 2, rh.Vector3d(0, 0, 1), rh.Point3d(0, 0, 0)))
f.Objects.AddInstanceObject(rh.InstanceReference(idef.Id, turn))
f.Objects.AddExtrusion(rh.Extrusion.Create(rh.Circle(100.0).ToNurbsCurve(), 300.0, True))
sys.exit(0 if f.Write(sys.argv[1], 7) else 1)
'''

    def test_import_3dm_blocks(self):
        """0.351: a Rhino file in millimetres with a block placed twice (a box of a material, one moved 2 m and turned)
        and a surface saved without its mesh: the two copies read where they are, in metres, in the material's colour,
        the surface counted as left out."""
        import subprocess
        import sys
        from arqbim.model import mesh_import
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "blocos.3dm")
            made = subprocess.run([sys.executable, "-c", self.BLOCKS_3DM, path], capture_output=True, text=True,
                                  timeout=120)
            self.assertEqual(made.returncode, 0, made.stderr[-2000:])
            model = mesh_import.read(path)
        self.assertEqual(model.skipped, 1)
        parts = model.parts_m()
        self.assertEqual(len(parts), 1)
        (name, rgb, alpha), corners = next(iter(parts.items()))
        self.assertEqual(name, "Madeira")
        np.testing.assert_allclose(rgb, (150 / 255, 100 / 255, 50 / 255), atol=1e-6)
        self.assertEqual(len(corners), 24)                             # (two boxes, six quads each)
        pts = corners.reshape(-1, 3)
        np.testing.assert_allclose(pts.min(axis=0), (0.0, 0.0, 0.0), atol=1e-6)
        np.testing.assert_allclose(pts.max(axis=0), (2.0, 1.0, 0.8), atol=1e-6)    # (the turned one: 0,5 × 1 m)

    def test_obj_stl(self):
        """0.349: the same room in OBJ — an object a element, its vertices, normals and faces (each face's corners and
        normal in range), its materials in the MTL beside it (each used one there), Y up — and in STL at 1:100 — one
        solid of every triangle, in millimetres, Z up, on the plate (z = 0) and centred, unit normals."""
        from arqbim.model import gltf_export, mesh_export
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        walls = [bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
                 for a, b in (((0.0, 0.0), (5.0, 0.0)), ((5.0, 0.0), (5.0, 4.0)), ((5.0, 4.0), (0.0, 4.0)),
                              ((0.0, 4.0), (0.0, 0.0)))]
        bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, walls[0]), 2.0, -1)
        top = float(doc.get(walls[0]).mesh.bounds()[1][2])
        elements, materials = gltf_export.gather(doc, list(doc.objects.values()))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sala.obj")
            objects, triangles = mesh_export.write_obj(path, elements, materials)
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            with open(os.path.join(tmp, "sala.mtl"), encoding="utf-8") as fh:
                mtl = fh.read()
            stl = os.path.join(tmp, "sala.stl")
            solid = mesh_export.write_stl(stl, elements, 100)
            normals, corners = mesh_export.read_stl(stl)
            self.assertEqual(os.path.getsize(stl), 84 + 50 * solid)
        verts = np.array([[float(v) for v in line.split()[1:]] for line in lines if line.startswith("v ")])
        faces = [line.split()[1:] for line in lines if line.startswith("f ")]
        self.assertEqual(objects, 5)                                       # (four walls and the window)
        self.assertEqual(sum(1 for line in lines if line.startswith("o ")), objects)
        self.assertEqual((len(verts), len(faces)), (3 * triangles, triangles))
        self.assertEqual(sum(1 for line in lines if line.startswith("vn ")), triangles)
        used = {line.split()[1] for line in lines if line.startswith("usemtl ")}
        self.assertTrue(all("newmtl " + name in mtl for name in used))
        self.assertTrue(all(1 <= int(c.split("//")[0]) <= len(verts) and 1 <= int(c.split("//")[1]) <= triangles
                            for face in faces for c in face))
        self.assertAlmostEqual(float(verts[:, 1].max()), top, places=3)        # (Y up)
        self.assertEqual(solid, triangles)
        self.assertAlmostEqual(float(corners[:, :, 2].min()), 0.0, places=3)    # (on the plate…)
        self.assertAlmostEqual(float(corners[:, :, 2].max()), top * 10.0, places=2)   # (…1:100 in mm, Z up)
        self.assertLess(abs(float(corners[:, :, 0].min() + corners[:, :, 0].max())), 0.1)   # (centred)
        np.testing.assert_allclose(np.linalg.norm(normals, axis=1), 1.0, atol=1e-5)


class CadLinksKept(unittest.TestCase):
    """0.158: a DXF linked (its layer of dimensions hidden) is kept beside the IFC — not in it — and read back as it
    was; undone, gone."""

    def test_saved(self):
        from arqbim.model import cad_links as cm
        from arqbim.model.document import CadLinksChange
        doc = Document()
        with tempfile.TemporaryDirectory() as tmp:
            dxf = os.path.join(tmp, "planta.dxf")
            with open(dxf, "w") as f:
                f.write("0\nSECTION\n2\nENTITIES\n0\nLINE\n8\nPAREDES\n10\n0\n20\n0\n11\n5\n21\n0\n0\nENDSEC\n0\nEOF\n")
            link = cm.CadLink("planta", dxf, 1.0, (2.0, 3.0), storey=doc.active_storey, hidden=["COTAS"])
            doc.execute(CadLinksChange(doc.cad_links, [link], "Ligar"))
            self.assertEqual(sorted(cm.placed_segments(link)), ["PAREDES"])
            path = os.path.join(tmp, "ligado.ifc")
            doc.save(path)
            with open(path, encoding="utf-8") as f:
                self.assertNotIn("planta.dxf", f.read())
            again = Document()
            again.open(path)
            self.assertEqual([(c.uid, c.hidden, tuple(c.origin)) for c in again.cad_links],
                             [(link.uid, ["COTAS"], (2.0, 3.0))])
            geomcache.forget(path)
        doc.undo()
        self.assertEqual(doc.cad_links, [])


class BackgroundImagesKept(unittest.TestCase):
    """0.154: a background image imported, calibrated (one undo step each) and locked is kept beside the IFC — not in
    it — and read back as it was, on its storey; its picture beside the project."""

    def test_saved_and_undone(self):
        from arqbim.model import images as im
        from arqbim.model.document import ImagesChange
        doc = Document()
        with tempfile.TemporaryDirectory() as tmp:
            picture = os.path.join(tmp, "levantamento.png")
            with open(picture, "wb") as f:
                f.write(b"\x89PNG")
            image = im.placed("levantamento", picture, (1200, 800), (5.0, 5.0), doc.active_storey)
            doc.execute(ImagesChange(doc.images, [image], "Importar"))
            done = image.scaled(image.origin, 2.0)
            done.locked = True
            doc.execute(ImagesChange(doc.images, [done], "Calibrar"))
            path = os.path.join(tmp, "imagens.ifc")
            doc.save(path)
            with open(path, encoding="utf-8") as f:
                self.assertNotIn("levantamento", f.read())                # (not in the IFC)
            again = Document()
            again.open(path)
            self.assertEqual(len(again.images), 1)
            back = again.images[0]
            self.assertEqual((back.uid, back.storey, back.locked), (image.uid, doc.active_storey, True))
            self.assertAlmostEqual(back.width, 24.0)
            np.testing.assert_allclose(back.origin, done.origin, atol=1e-9)
            self.assertEqual(os.path.normpath(back.path), os.path.normpath(picture))
            geomcache.forget(path)
        doc.undo()
        self.assertAlmostEqual(doc.images[0].width, 12.0)
        self.assertFalse(doc.images[0].locked)
        doc.undo()
        self.assertEqual(doc.images, [])


class Views3DOnSheets(unittest.TestCase):
    """0.134: a house's 3D view on a sheet — drawn in lines, nothing cut, from the south-west (the 3D view) or
    from a named view's camera (from the north-east: another drawing); hidden edges left out; a view that is no
    longer there gives none; kept on a sheet."""

    def test_axonometric(self):
        from arqbim.model import drawings
        from arqbim.model.document import View3D
        doc = Document()
        bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (10.0, 6.0, 0.0),
                                                       (0.0, 6.0, 0.0))], catalog.BY_KEY["parede_alv_20"])
        iso = drawings.of_view(doc, "3d", "", "3D")
        self.assertEqual(iso.cut, [])
        self.assertGreater(len(iso.lines), 20)
        lo, hi = iso.bounds()
        self.assertGreater(float(hi[0] - lo[0]), 8.0)
        everything = drawings._draw(doc, [o for o in doc.objects.values() if o.is_bim],
                                    np.array(drawings.ISO) / np.linalg.norm(drawings.ISO), -1000.0,
                                    np.zeros(3), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0)), "x",
                                    hidden=False)
        self.assertLess(len(iso.lines), len(everything.lines))           # (the hidden edges left out)
        doc.views3d.append(View3D("Nordeste", "u1", {"position": (30.0, 30.0, 20.0), "focus": (5.0, 3.0, 1.0),
                                                     "rotation": (0, 0, 0, 1), "fov": 0, "width": 1, "height": 1,
                                                     "zoom": 1}))
        ne = drawings.of_view(doc, "3d", "u1", "Nordeste")
        self.assertGreater(len(ne.lines), 20)
        self.assertFalse(np.allclose(np.sort(ne.lines.reshape(-1))[:10], np.sort(iso.lines.reshape(-1))[:10]))
        self.assertIsNone(drawings.of_view(doc, "3d", "gone", "x"))
        sheet = sheets.Sheet("3D", views=[sheets.Placed("3d", "u1")])
        self.assertEqual(sheets.from_dict(sheets.to_dict(sheet)).views[0].kind, "3d")


class OwnSchedules(unittest.TestCase):
    """0.131: the project's own schedules — formulas (a decimal comma, ";" between arguments, nothing else
    run), a walls' schedule with its columns, a formula (length × height), a filter, sorted and grouped by
    storey; kept beside the IFC, undone."""

    def test_formulas(self):
        row = {"length": 4.0, "height": 2.5, "name": "Parede 1"}
        self.assertEqual(schedules.evaluate("length * height", row), 10.0)
        self.assertAlmostEqual(schedules.evaluate("length * 1,10", row), 4.4)
        self.assertEqual(schedules.evaluate("round(length / 3; 2)", row), 1.33)
        self.assertEqual(schedules.evaluate("max(length; height) - min(length; height)", row), 1.5)
        for bad in ("__import__('os')", "name * 2", "length.real", "open('x')", "1 / 0", "2 ** 100", "length *"):
            self.assertIsNone(schedules.evaluate(bad, row), bad)

    def test_walls_schedule(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        for a, b in (((0, 0, 0), (5, 0, 0)), ((0, 2, 0), (3, 2, 0)), ((0, 4, 0), (8, 4, 0))):
            bim.add_wall(doc, a, b, spec)
        upper = bim.add_storey(doc, "Piso 1", 3.0)
        bim.add_wall(doc, (0, 0, 3.0), (6, 0, 3.0), spec, storey=upper)
        defn = schedules.ScheduleDef("Paredes compridas", "walls", ["name", "storey", "length", "height"],
                                     formulas=[("Área bruta", "length * height")],
                                     filters=[("length", "≥", "4")], sort="length", descending=True)
        columns, lines = schedules.apply(defn, schedules.rows(doc, "walls"))
        self.assertEqual(columns, ["name", "storey", "length", "height", "formula:0"])
        self.assertEqual([round(r["length"], 2) for r in lines], [8.0, 6.0, 5.0])
        self.assertAlmostEqual(lines[0]["formula:0"], 8.0 * 2.8)
        defn.group = "storey"
        groups, keys = schedules.grouped(defn, lines)
        self.assertEqual(keys, ["storey", "count", "length", "formula:0"])
        self.assertEqual([(g["storey"], g["count"]) for g in groups], [("Piso 1", 1), ("Térreo", 2)])
        self.assertAlmostEqual(groups[1]["length"], 13.0)
        doc.execute(schedules.SetScheduleDefs([], [defn], "Tabela"))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "tabelas.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        (back,) = again.schedule_defs
        self.assertEqual((back.name, back.fields, back.formulas, back.filters, back.sort, back.descending,
                          back.group, back.uid), (defn.name, defn.fields, [("Área bruta", "length * height")],
                                                  [("length", "≥", "4")], "length", True, "storey", defn.uid))
        self.assertIsNone(schedules.def_from_dict({"name": "x", "category": "nonsense", "fields": []}))
        # (0.132) on a sheet: its table — the headings, the rows written as in the panel, the totals — sized on
        # paper whatever the scale; the walls' category too; kept with the sheet
        from arqbim.model import drawings
        table = drawings.of_view(doc, "schedule", "def:" + defn.uid, "Tabela")      # (as kept: by storey)
        self.assertEqual(table.title, "Paredes compridas")
        self.assertEqual(table.header, ["Pavimento", "Quantidade", "Comprimento", "Área bruta"])
        self.assertEqual(table.rows[0], ["Piso 1", "1", "6,00 m", "16,80"])
        self.assertIn("Área bruta: 53,20", table.totals)
        self.assertEqual(sheets.extent(table)[0], "mm")
        self.assertEqual(len(drawings.of_view(doc, "schedule", "walls", "Paredes").rows), 4)
        self.assertIsNone(drawings.of_view(doc, "schedule", "def:nonsense", "x"))
        sheet = sheets.Sheet("Quadros", views=[sheets.Placed("schedule", "def:" + defn.uid)])
        (frame,) = sheets.layout(sheet, [sheets.extent(table)])
        self.assertAlmostEqual(frame.width, table.paper_size()[0])
        self.assertEqual(sheets.from_dict(sheets.to_dict(sheet)).views[0].kind, "schedule")
        doc.undo()
        self.assertEqual(doc.schedule_defs, [])


class ApplianceGasAndPower(unittest.TestCase):
    """0.198: a gas hob and a gas pipe (copper Ø22, in the Gas system) behind it: "Ligar à rede" gives the hob its
    branch (copper Ø15) to the pipe, connected; an oven has its supply (a CABLE port, ELECTRICAL) and alone makes an
    appliance circuit of 3500 W (20 A, 4 mm²); the IFC valid."""

    def test_gas_and_power(self):
        doc = Document()
        bim.add_segment(doc, np.array((0.0, 0.6)), np.array((6.0, 0.6)), catalog.BY_KEY["gas_cobre_22"], 0.4,
                        storey=doc.active_storey, system="gas")
        hob = bim.add_appliance(doc, np.array((2.0, 0.0, 0.0)), "gas_hob", 180.0)    # (its back to the pipe)
        report = bim.connect_to_network(doc, [hob])
        self.assertEqual([(name, key) for _g, name, key, main in report if main], [("gas", "gas")])
        gas_port = doc.ifc.ports(hob)[0]
        self.assertIsNotNone(doc.ifc.connected(gas_port))
        oven = bim.add_appliance(doc, np.array((4.0, 3.0, 0.0)), "oven", 0.0)
        power = [p for p in doc.ifc.ports(oven) if p.PredefinedType == "CABLE"]
        self.assertEqual([(p.Name, p.SystemType, p.FlowDirection) for p in power], [("power", "ELECTRICAL", "SINK")])
        circuit = bim.add_circuit(doc, [oven])
        r = doc.ifc.circuit_report(circuit)
        self.assertEqual((r["kind"], r["power"], r["breaker"]), ("appliance", 3500.0, 20.0))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class DuctSOffsets(unittest.TestCase):
    """0.197: a duct (30 × 20) brought to a unit's side port 26,5 cm higher than the port — too little height for two
    square bends —: along, then down at 45° (an S: two bends of 45°), then level in to the port, connected; 1,20 m
    higher: straight down as before (two square bends)."""

    def _pieces(self, doc):
        out = []
        for e in doc.ifc.file.by_type("IfcDuctSegment"):
            s, end, _z = doc.ifc.segment_params(e.GlobalId)
            out.append((float(np.linalg.norm((end - s)[:2])), float(end[2] - s[2])))
        return out

    def test_s_and_square(self):
        doc = Document()
        unit = bim.add_equipment(doc, (5.0, 3.0), "ducted_unit")
        spec = catalog.BY_KEY["conduta_30x20"]
        bim.add_segment(doc, np.array((1.0, 3.0)), np.array((4.5, 3.0)), spec, 3.0, storey=doc.active_storey,
                        to_port=unit)                                     # (to its return, 26,5 cm under)
        pieces = self._pieces(doc)
        sloped = [(run, rise) for run, rise in pieces if run > 1e-6 and abs(rise) > 1e-6]
        self.assertEqual(len(sloped), 1)
        self.assertAlmostEqual(abs(sloped[0][1]), sloped[0][0], places=6)    # (45°)
        self.assertFalse(any(run < 1e-6 for run, _r in pieces))              # (no upright piece)
        bends = doc.ifc.file.by_type("IfcDuctFitting")
        self.assertEqual(len(bends), 2)
        port = next(p for p in doc.ifc.ports(unit) if p.Name == "return")
        self.assertIsNotNone(doc.ifc.connected(port))
        other = bim.add_equipment(doc, (5.0, 9.0), "ducted_unit")
        bim.add_segment(doc, np.array((1.0, 9.0)), np.array((4.5, 9.0)), spec, 3.935, storey=doc.active_storey,
                        to_port=other)                                    # (1,20 m over it: straight down)
        upright = [rise for run, rise in self._pieces(doc) if run < 1e-6]
        self.assertEqual(len(upright), 1)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class RefrigerantLines(unittest.TestCase):
    """0.196: a split system's refrigerant lines — the indoor wall unit and the outdoor unit each with a liquid and a
    gas port (REFRIGERATION, both ways); a copper 1/4" line from the indoor's liquid port to the outdoor's: both
    ports connected, the line in the system "Refrigerante — líquido"; the IFC valid."""

    def test_liquid_line(self):
        doc = Document()
        indoor = bim.add_equipment(doc, (2.0, 3.0), "split_wall")
        outdoor = bim.add_equipment(doc, (8.0, 3.0), "outdoor_unit")
        ports_in = {p.Name: p for p in doc.ifc.ports(indoor)}
        ports_out = {p.Name: p for p in doc.ifc.ports(outdoor)}
        self.assertEqual(sorted(ports_in), ["condensate", "gas", "liquid"])
        self.assertEqual(sorted(ports_out), ["gas", "liquid"])
        for p in (ports_in["liquid"], ports_out["gas"]):
            self.assertEqual((p.SystemType, p.FlowDirection, p.PredefinedType), ("REFRIGERATION", "SOURCEANDSINK", "PIPE"))
        self.assertEqual(doc.ifc.port_system(ports_in["liquid"]), "refrigerant_liquid")
        self.assertEqual(doc.ifc.port_system(ports_out["gas"]), "refrigerant_gas")
        liquid = doc.ifc._placement_si(ports_in["liquid"])[:3, 3]
        target = doc.ifc._placement_si(ports_out["liquid"])[:3, 3]
        bim.add_segment(doc, np.array(liquid[:2]), np.array((target[0] - 0.02, target[1])), catalog.BY_KEY["cobre_14"],
                        float(liquid[2]), storey=doc.active_storey, from_port=indoor, to_port=outdoor,
                        system="refrigerant_liquid")
        self.assertIsNotNone(doc.ifc.connected(ports_in["liquid"]))
        self.assertIsNotNone(doc.ifc.connected(ports_out["liquid"]))
        self.assertIsNone(doc.ifc.connected(ports_out["gas"]))
        pipes = [e.GlobalId for e in doc.ifc.file.by_type("IfcPipeSegment")]
        self.assertTrue(pipes and all(doc.ifc.system_of(g) == "refrigerant_liquid" for g in pipes))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class Keynotes(unittest.TestCase):
    """0.194: keynotes — "02.03" given to a wall goes on its type: the other wall of that type has it too, a wall of
    another type not; a tag in the plan writes the element's code, "?" before it had one, the new code when it
    changes; the legend (schedule "Notas-chave") lists each code with its text and count; taken away; an
    IfcClassificationReference of "Notas-chave", valid IFC; kept in the file and read back."""

    def test_keynotes(self):
        from arqbim.model import annotations as notes2d
        from arqbim.model import drawings, keynotes
        doc = Document()
        a = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        b = bim.add_wall(doc, np.array((0.0, 3.0, 0.0)), np.array((4.0, 3.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        c = bim.add_wall(doc, np.array((0.0, 6.0, 0.0)), np.array((4.0, 6.0, 0.0)), catalog.BY_KEY["parede_alv_15"])
        plan = ("plan", doc.active_storey)
        tag = notes2d.Annotation(plan, "keynote", [np.array((2.0, 0.0, 0.0)), np.array((3.0, 1.0, 0.0))],
                                 extra={"element": a})
        doc.execute(notes2d.AddAnnotation(tag, "Nota"))
        self.assertEqual(keynotes.tag_text(doc, tag), "?")
        bim.set_keynote(doc, a, "02.03")
        self.assertEqual(doc.ifc.keynote_of(a), ("02.03", "Alvenaria de tijolo cerâmico 20 cm"))
        self.assertEqual(doc.ifc.keynote_of(b)[0], "02.03")             # (the same type)
        self.assertIsNone(doc.ifc.keynote_of(c))
        self.assertEqual(keynotes.tag_text(doc, tag), "02.03")
        bim.set_keynote(doc, c, "02.02")
        legend = keynotes.legend_rows(doc)
        self.assertEqual([(r["code"], r["count"]) for r in legend], [("02.02", 1), ("02.03", 2)])
        self.assertEqual(schedules.rows(doc, "keynotes"), legend)
        drawing = drawings.plan(doc, doc.active_storey, "Planta")
        written = [x for x in drawing.annotations if x[0] == "keynote"]
        self.assertEqual(written[0][3], "02.03")
        self.assertEqual(len(written[0][1]), 1)                           # (its leader)
        refs = [r for r in doc.ifc.file.by_type("IfcClassificationReference")]
        self.assertTrue(refs and all(r.ReferencedSource.Name == "Notas-chave" for r in refs))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.set_keynote(doc, a, "02.04")                                  # (another: the type's changes)
        self.assertEqual(keynotes.tag_text(doc, tag), "02.04")
        doc.undo()
        self.assertEqual(keynotes.tag_text(doc, tag), "02.03")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "notas.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            self.assertEqual(again.ifc.keynote_of(b), ("02.03", "Alvenaria de tijolo cerâmico 20 cm"))
            self.assertEqual([a2.kind for a2 in again.annotations], ["keynote"])
            geomcache.forget(path)
        bim.set_keynote(doc, a, "")                                       # (taken away)
        self.assertIsNone(doc.ifc.keynote_of(b))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class DimensionTypes(unittest.TestCase):
    """0.193: dimension types — the project's style (metres, 2 decimals) and a type "Pormenor" (centimetres, arrows,
    3,5 mm): a dimension of that type written "450", the other "4,50"; on the drawing each with its own; one changed
    to the type, undone; a type gone: drawn by the project's; kept in the file beside the IFC and read back."""

    def test_types(self):
        from arqbim.model import dimensions as dims
        from arqbim.model import drawings
        doc = Document()
        plan = ("plan", doc.active_storey)
        project = dims.clean_style({"types": {"Pormenor": {"unit": "cm", "decimals": 0, "mark": "arrow", "text": 3.5},
                                              " ": {"unit": "mm"}}})
        self.assertEqual(dims.type_names(project), ["Pormenor"])          # (a nameless one dropped)
        doc.execute(dims.SetDimensionStyle(doc.dim_style, project, "Estilo"))
        plain = dims.Dimension(plan, np.array((0.0, 0.0, 0.0)), np.array((4.5, 0.0, 0.0)), np.array((2.0, -1.0, 0.0)))
        detail = dims.Dimension(plan, np.array((0.0, 2.0, 0.0)), np.array((4.5, 2.0, 0.0)), np.array((2.0, 3.0, 0.0)),
                                style="Pormenor")
        for d in (plain, detail):
            doc.execute(dims.AddDimension(d, "Cota"))
        drawing = drawings.plan(doc, doc.active_storey, "Planta")
        texts = sorted(d[4] for d in drawing.dims)
        self.assertEqual(texts, ["4,50", "450"])
        own = [d for d in drawing.dims if d[5]["mark"] == "arrow"]          # (0.398: each with its whole type)
        self.assertEqual(len(own), 1)
        self.assertEqual((own[0][5]["mark"], own[0][5]["text"]), ("arrow", 3.5))
        doc.execute(dims.SetDimensionTypeOf([plain], "Pormenor", "Tipo"))
        self.assertEqual(plain.style, "Pormenor")
        doc.undo()
        self.assertIsNone(plain.style)
        self.assertEqual(dims.style_of(project, dims.Dimension(plan, None, None, None, style="Outro"))["unit"], "m")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cotas.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            self.assertEqual(dims.type_names(again.dim_style), ["Pormenor"])
            self.assertEqual(sorted(str(d.style) for d in again.dimensions), ["None", "Pormenor"])
            geomcache.forget(path)


class LevelMarks(unittest.TestCase):
    """0.192: a level mark in a plan — over a slab whose top is 0,15 m up: "+0,15", always the model's (the slab
    raised: "+0,45"); its symbol a quartered circle with two quarters to fill, on the drawing and in the DXF (its
    text); outside the slab, the storey's "±0,00"."""

    def test_level_mark(self):
        from arqbim.model import annotations as notes2d
        from arqbim.model import drawings, dxf
        doc = Document()
        slab = bim.add_slab_outline(doc, [(0, 0), (4, 0), (4, 3), (0, 3)], 0.15, catalog.BY_KEY["laje_12"])
        plan = ("plan", doc.active_storey)
        mark = notes2d.Annotation(plan, "level", [np.array((2.0, 1.5, 0.0))])
        apart = notes2d.Annotation(plan, "level", [np.array((8.0, 1.5, 0.0))])
        for a in (mark, apart):
            doc.execute(notes2d.AddAnnotation(a, "Marca"))
        from arqbim.model import spots
        top = float(doc.get(slab).mesh.verts[:, 2].max())
        drawing = drawings.plan(doc, doc.active_storey, "Planta")
        marks = [a for a in drawing.annotations if a[0] == "level"]
        self.assertEqual(sorted(a[3] for a in marks), sorted([spots.text(top), "±0,00"]))
        self.assertTrue(all(len(a[2]) == 2 for a in marks))           # (two quarters to fill)
        self.assertEqual(len(marks[0][1]), 3)                         # (the circle and its two diameters)
        m = np.eye(4)
        m[:3, 3] = (0.0, 0.0, 0.3)
        bim.transform_objects(doc, [slab], m, "Subir")
        drawing = drawings.plan(doc, doc.active_storey, "Planta")
        raised = spots.text(top + 0.3)
        self.assertIn(raised, [a[3] for a in drawing.annotations if a[0] == "level"])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "planta.dxf")
            dxf.write(path, drawing, 50)
            with open(path, "rb") as f:
                self.assertIn(raised, f.read().decode("cp1252"))
        self.assertEqual(notes2d.from_dict(notes2d.to_dict(mark), np.zeros(3)).kind, "level")


class EditDrawings(unittest.TestCase):
    """0.191: the drawings in a view changed — a line's end moved (its grip), undone; a text's words, size and angle;
    a region's hatch; turned 90° about a point (the text's angle follows), undone; kept in the file beside the IFC;
    the text's angle on the drawing and in the DXF (its rotation, code 50)."""

    def test_edit_rotate_and_paper(self):
        from arqbim.model import annotations as notes2d
        from arqbim.model import drawings, dxf
        doc = Document()
        plan = ("plan", doc.active_storey)
        line = notes2d.Annotation(plan, "line", [np.array((0.0, 0.0, 0.0)), np.array((2.0, 0.0, 0.0))])
        text = notes2d.Annotation(plan, "text", [np.array((1.0, 1.0, 0.0))], text="Nota")
        region = notes2d.Annotation(plan, "region", [np.array(p) for p in ((3.0, 0.0, 0.0), (4.0, 0.0, 0.0),
                                                                           (4.0, 1.0, 0.0))])
        for a in (line, text, region):
            doc.execute(notes2d.AddAnnotation(a, "Desenho"))
        doc.execute(notes2d.EditAnnotation(line, "Mudar", points=[line.points[0], np.array((3.0, 1.0, 0.0))]))
        self.assertTrue(np.allclose(line.points[1], (3.0, 1.0, 0.0)))
        doc.undo()
        self.assertTrue(np.allclose(line.points[1], (2.0, 0.0, 0.0)))
        doc.execute(notes2d.EditAnnotation(text, "Mudar", text="Nota 2", size=3.5, extra={"angle": 30.0}))
        doc.execute(notes2d.EditAnnotation(region, "Mudar", hatch="cross"))
        self.assertEqual((text.text, text.size, notes2d.angle(text), region.hatch), ("Nota 2", 3.5, 30.0, "cross"))
        with self.assertRaises(KeyError):
            notes2d.EditAnnotation(text, "Mudar", colour="red")
        doc.execute(notes2d.RotateAnnotations([line, text], np.zeros(3), np.array((0.0, 0.0, 1.0)), 90.0, "Rodar"))
        self.assertTrue(np.allclose(line.points[1], (0.0, 2.0, 0.0), atol=1e-9))
        self.assertTrue(np.allclose(text.points[0], (-1.0, 1.0, 0.0), atol=1e-9))
        self.assertAlmostEqual(notes2d.angle(text), 120.0)
        doc.undo()
        self.assertTrue(np.allclose(line.points[1], (2.0, 0.0, 0.0), atol=1e-9))
        self.assertAlmostEqual(notes2d.angle(text), 30.0)
        back = notes2d.from_dict(notes2d.to_dict(text), np.zeros(3))
        self.assertEqual((back.text, back.size, notes2d.angle(back)), ("Nota 2", 3.5, 30.0))
        drawing = drawings.plan(doc, doc.active_storey, "Planta")
        written = [a for a in drawing.annotations if a[0] == "text"]
        self.assertEqual(len(written), 1)
        self.assertAlmostEqual(written[0][8], 30.0)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "planta.dxf")
            dxf.write(path, drawing, 50)
            with open(path, "rb") as f:
                lines = f.read().decode("cp1252").split("\r\n")
        pairs = [(lines[k].strip(), lines[k + 1]) for k in range(0, len(lines) - 1, 2)]
        k = pairs.index(("1", "Nota 2"))
        self.assertEqual(pairs[k + 1], ("50", "30.000000"))


class DxfExport(unittest.TestCase):
    """0.129: a house's plan (a door, a room, a dimension, a text and a hatched region drawn, a section) to DXF
    R12: pairs of code and value from start to EOF; the header's version, its layers; what is cut as closed
    polylines on CORTE, the masonry's hatch on TRAMAS, the door on SIMBOLOS, the dimension's value, the room's
    label and the text drawn; in metres."""

    def test_plan_to_dxf(self):
        from arqbim.model import annotations as notes2d
        from arqbim.model import dimensions as dims
        from arqbim.model import drawings, dxf
        doc = Document()
        walls = bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (10.0, 6.0, 0.0),
                                                               (0.0, 6.0, 0.0))], catalog.BY_KEY["parede_alv_20"])
        frame = bim.wall_frame(doc, walls[0])
        bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY["porta_80"], frame, frame.x0 + 2.0, -1)
        bim.add_room(doc, (5.0, 3.0), "Sala")
        plan = ("plan", doc.active_storey)
        doc.execute(dims.AddDimension(dims.Dimension(plan, np.array((-0.1, -0.1, 0.0)), np.array((10.1, -0.1, 0.0)),
                                                     np.array((5.0, -1.0, 0.0))), "Cota"))
        doc.execute(notes2d.AddAnnotation(notes2d.Annotation(plan, "text", [np.array((1.0, 1.0, 0.0))],
                                                             text="Nota"), "Texto"))
        doc.execute(notes2d.AddAnnotation(notes2d.Annotation(plan, "region", [np.array(p) for p in (
            (6.0, 1.0, 0.0), (8.0, 1.0, 0.0), (8.0, 2.0, 0.0), (6.0, 2.0, 0.0))]), "Região"))
        doc.add_section((5.0, 3.0, 0.0), (0.0, -1.0, 0.0))
        drawing = drawings.plan(doc, doc.active_storey, "Planta")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "planta.dxf")
            n = dxf.write(path, drawing, 50)
            with open(path, "rb") as f:
                raw = f.read()
        lines = raw.decode("cp1252").split("\r\n")
        self.assertEqual(lines[-1], "")
        lines = lines[:-1]
        self.assertEqual(len(lines) % 2, 0)
        pairs = [(int(lines[k]), lines[k + 1]) for k in range(0, len(lines), 2)]
        self.assertEqual(pairs[0], (0, "SECTION"))
        self.assertEqual(pairs[-1], (0, "EOF"))
        self.assertIn((1, "AC1009"), pairs)
        layers = [v for (c, v), (c2, v2) in zip(pairs, pairs[1:]) if (c, v) == (0, "LAYER") and c2 == 2 for v in [v2]]
        self.assertTrue({"CORTE", "TRAMAS", "SIMBOLOS", "COTAS", "SALAS", "TEXTOS", "MARCAS"} <= set(layers))
        entities, current = [], None
        for code, value in pairs[pairs.index((2, "ENTITIES")) + 1:]:
            if code == 0:
                current = [value, None, []]
                entities.append(current)
            elif code == 8:
                current[1] = value
            elif code == 1:
                current[2].append(value)
        kinds = {(e[0], e[1]) for e in entities}
        self.assertTrue({("POLYLINE", "CORTE"), ("LINE", "TRAMAS"), ("LINE", "SIMBOLOS"), ("LINE", "COTAS"),
                         ("CIRCLE", "MARCAS")} <= kinds, kinds)
        texts = {t for e in entities if e[0] == "TEXT" for t in e[2]}
        self.assertTrue({"10,20", "SALA 1", "Nota", "N", "1"} <= texts, texts)
        self.assertGreater(n, 50)
        xs = [float(v) for c, v in pairs if c == 10]
        self.assertTrue(-20.0 < min(xs) and max(xs) < 30.0)                   # (metres, not millimetres)


class SheetsByStoreyAndRevisions(unittest.TestCase):
    """0.127: Sheets by storey — a plan sheet for each of two storeys, one with the four elevations, one undo
    step; the numbering ("A-01", "A-001"); the project's own fields and a sheet's revisions — cleaned, kept
    beside the IFC, undone — and the rows over the title block kept clear of the views."""

    def test_sheets(self):
        doc = Document()
        bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        upper = bim.add_storey(doc, "Piso 1", 3.0)
        pages = [("Planta — " + name, [("plan", g)]) for g, name, _z in doc.storeys()]
        pages.append(("Alçados", [("elevation", s) for s in "NSEW"]))
        self.assertEqual(doc.make_sheets(pages, "A2"), 3)
        self.assertEqual([s.name for s in doc.sheets][-1], "Alçados")
        self.assertEqual(doc.sheets[0].paper, "A2")
        self.assertIn(("plan", upper), [(v.kind, v.ref) for s in doc.sheets for v in s.views])
        doc.undo()
        self.assertEqual(doc.sheets, [])
        doc.redo()
        fields = {"project": "Casa", sheets.EXTRA_KEY: [["Processo", "123/2026"], ["", "sem nome"]],
                  "prefix": "A-", "digits": "3"}
        doc.set_title_block(fields, 1, None, None, [{"code": "A", "date": "01/10/2026", "text": "Primeira"},
                                                     {"code": "", "date": "", "text": ""}])
        self.assertEqual(doc.title_block[sheets.EXTRA_KEY], [["Processo", "123/2026"]])
        self.assertEqual(sheets.number_of(doc.sheets, doc.sheets[1], doc.title_block), "A-002")
        self.assertEqual(sheets.number_of(doc.sheets, doc.sheets[0], {}), "01")
        self.assertEqual(doc.sheets[1].revisions, [{"code": "A", "date": "01/10/2026", "text": "Primeira"}])
        texts = sheets.title_texts(doc.title_block, "Planta", "A-002", "", doc.sheets[1].revisions)
        self.assertEqual((texts[sheets.EXTRA_KEY], texts["revisions"][0]["code"]), ([("Processo", "123/2026")], "A"))
        extents = [(10.0, 30.0)]
        free = sheets.layout(doc.sheets[0], extents)[0]
        crowded = sheets.layout(doc.sheets[1], extents, extra_rows=1)
        self.assertGreaterEqual(crowded[0].scale, free.scale)                  # (less room: not a bigger scale)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "folhas.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        self.assertEqual(again.sheets[1].revisions, doc.sheets[1].revisions)
        self.assertEqual(again.title_block.get("prefix"), "A-")
        self.assertEqual(again.title_block.get("digits"), "3")
        doc.undo()
        self.assertEqual(doc.sheets[1].revisions, [])
        self.assertNotIn("prefix", doc.title_block)

    def test_templates(self):
        """0.130: the title block's templates — full (as it was), compact, a strip down the right side: where
        they go, the room left for the views; a sheet's kept; made by Sheets by storey with one."""
        a3 = sheets.PAPERS["A3"]
        self.assertEqual(sheets.title_box(a3, "full"), (290.0, 247.0, 120.0, 40.0))
        self.assertEqual(sheets.block_size("compact"), (100.0, 22.0))
        x, y, w, h = sheets.title_box(a3, "strip")
        self.assertEqual((x, w), (360.0, 50.0))
        self.assertEqual(sheets.drawing_area("A3"), (14.0, 14.0, 392.0, 225.0))          # (as before)
        self.assertEqual(sheets.drawing_area("A3", "strip"), (14.0, 14.0, 338.0, 269.0))
        self.assertGreater(sheets.drawing_area("A3", "compact")[3], 225.0)
        doc = Document()
        doc.make_sheets([("Alto", [])], "A3", "strip")
        self.assertEqual(doc.sheets[0].template, "strip")
        back = sheets.from_dict(sheets.to_dict(doc.sheets[0]))
        self.assertEqual(back.template, "strip")
        self.assertEqual(sheets.from_dict({"name": "x", "template": "nonsense"}).template, "full")
        tall = (8.0, 26.0)                                    # (a tall drawing: more room beside a strip)
        one = [sheets.Placed("plan", "x")]
        full = sheets.layout(sheets.Sheet("a", views=list(one)), [tall])[0]
        strip = sheets.layout(sheets.Sheet("b", views=list(one), template="strip"), [tall])[0]
        self.assertLessEqual(strip.scale, full.scale)

    def test_sets(self):
        """0.128: sheet sets — a sheet in two, another in one; the names; the sheets of a set; kept; undone."""
        doc = Document()
        doc.make_sheets([("A", []), ("B", []), ("C", [])])
        doc.set_sheet_sets(0, ["Licenciamento", " Execução ", "Licenciamento", ""])
        doc.set_sheet_sets(2, ["Licenciamento"])
        self.assertEqual(doc.sheets[0].sets, ["Licenciamento", "Execução"])
        self.assertEqual(sheets.set_names(doc.sheets), ["Execução", "Licenciamento"])
        self.assertEqual([s.name for s in sheets.in_set(doc.sheets, "Licenciamento")], ["A", "C"])
        back = sheets.from_dict(sheets.to_dict(doc.sheets[0]))
        self.assertEqual(back.sets, ["Licenciamento", "Execução"])
        doc.undo()
        self.assertEqual(doc.sheets[2].sets, [])
        self.assertEqual([s.name for s in sheets.in_set(doc.sheets, "Licenciamento")], ["A"])


class GraphicStyles(unittest.TestCase):
    """0.126: the project's graphic style — the usual hatches (as before), one changed (masonry crossed, red),
    nonsense cleaned; a pen; changed and undone; the plan's drawing carries it; kept beside the IFC; a line
    drawn in a view, dashed and 0,35 mm, on paper with them."""

    def test_styles(self):
        from arqbim.model import annotations as notes2d
        from arqbim.model import drawings
        from arqbim.model import graphic_styles as gs
        self.assertEqual(gs.hatch(None, "masonry"), ("#ffffff", (45.0,), 1.0))
        self.assertEqual(gs.hatch(None, None), ("#3c3c3c", (), 1.0))                  # (unknown: dark)
        self.assertEqual(gs.hatch(None, "colour:#ff0000"), ("#3c3c3c", (), 1.0))
        style = gs.clean({"hatches": {"masonry": {"pattern": "cross", "fill": "#ff0000", "spacing": 99},
                                      "nonsense": {}},
                          "pens": {"cut": 0.7, "bogus": 3}})
        self.assertEqual(gs.hatch(style, "masonry"), ("#ff0000", (45.0, -45.0), 10.0))
        self.assertEqual(gs.pen(style, "cut"), 0.7)
        self.assertNotIn("nonsense", style["hatches"])
        self.assertEqual(gs.clean({"hatches": {"wood": {"fill": "red"}}})["hatches"]["wood"]["fill"], "#ffffff")
        doc = Document()
        bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        doc.execute(gs.SetGraphicStyle(doc.graphic_style, style, "Estilos"))
        line = notes2d.Annotation(("plan", doc.active_storey), "line", [np.array((0.0, 2.0, 0.0)),
                                                                          np.array((3.0, 2.0, 0.0))],
                                  extra={"line": "dashed", "width": 0.35})
        doc.execute(notes2d.AddAnnotation(line, "Desenho"))
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual(plan.graphic_style["pens"]["cut"], 0.7)
        self.assertEqual(plan.annotations[0][6:8], ("dashed", 0.35))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "estilos.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        self.assertEqual(again.graphic_style, style)
        self.assertEqual(again.annotations[0].extra, {"line": "dashed", "width": 0.35})
        doc.undo()                                                        # (the line)
        doc.undo()                                                        # (the style)
        self.assertEqual(doc.graphic_style, gs.DEFAULTS)


class RoomsOnPaper(unittest.TestCase):
    """0.125: a 10 × 6 m house split by a wall, its two rooms: the areas' schedule (by storey, then number; the
    area summed), the finishes' one (as set), editable cells (their Properties actions), one line per storey;
    the plan on paper with each room's label (name, number, area) inside it."""

    def test_schedules_and_labels(self):
        from arqbim.model import drawings
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (10.0, 6.0, 0.0),
                                                       (0.0, 6.0, 0.0))], spec)
        bim.add_wall(doc, np.array((4.0, 0.0, 0.0)), np.array((4.0, 6.0, 0.0)), spec)
        living = bim.add_room(doc, (7.0, 3.0), "Sala")
        bedroom = bim.add_room(doc, (2.0, 3.0), "Quarto")
        bim.set_room(doc, bedroom, finishes={"FloorCovering": "Soalho", "WallCovering": "Estuque"})
        self.assertEqual(schedules.counts(doc)["rooms"], 2)
        lines = schedules.rows(doc, "rooms")
        self.assertEqual([r["name"] for r in lines], ["Sala", "Quarto"])      # (by number: 1, 2)
        self.assertAlmostEqual(lines[0]["area"], 5.8 * 5.8, places=3)
        self.assertAlmostEqual(lines[1]["area"], 3.8 * 5.8, places=3)
        self.assertAlmostEqual(schedules.totals(lines, "rooms")["area"], 9.6 * 5.8, places=3)
        fin = {r["name"]: r for r in schedules.rows(doc, "finishes")}
        self.assertEqual((fin["Quarto"]["floor"], fin["Quarto"]["walls"], fin["Quarto"]["ceiling"]),
                         ("Soalho", "Estuque", ""))
        self.assertEqual(schedules.editable("finishes", "floor", fin["Quarto"]), "room_finish:FloorCovering")
        self.assertEqual(schedules.editable("rooms", "area", lines[0]), None)
        (storey,) = schedules.by_type(lines, "rooms")
        self.assertEqual(storey["count"], 2)
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        labels = {name: (at, number, area) for at, name, number, area in plan.rooms}
        self.assertEqual(sorted(labels), ["Quarto", "Sala"])
        self.assertTrue(4.1 < labels["Sala"][0][0] < 9.9 and 0.1 < labels["Sala"][0][1] < 5.9)
        self.assertEqual(labels["Quarto"][2], "22,04 m²")
        self.assertTrue(living and bedroom)


class OneClickDimensions(unittest.TestCase):
    """0.399: what a dimension is taken to on a wall (model/dim_refs: finish faces, core faces, axis, core's axis) and
    the outside dimensions round an L-shaped house (model/auto_dims.exterior), in any direction."""

    def setUp(self):
        self.doc = doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        self.walls = bim.add_wall_loop(doc, [np.array((x, y, 0.0)) for x, y in ((0, 0), (10, 0), (10, 5), (6, 5),
                                                                                 (6, 8), (0, 8))], spec)
        self.inner = bim.add_wall(doc, np.array((4.0, 0.1, 0.0)), np.array((4.0, 7.9, 0.0)), spec)
        bim.join_wall_ends(doc, [self.inner])
        frame = bim.wall_frame(doc, self.walls[0])
        bim.add_opening(doc, self.walls[0], catalog.OPENING_BY_KEY["porta_80"], frame, frame.x0 + 1.5, -1)

    def _texts(self, dims_found, tag=None):
        from arqbim.model import dimensions as dims
        o, u, v = np.zeros(3), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
        return [dims.text(dims.placed(*dims.ends(self.doc, d), d.at, o, u, v, d.direction)[4])
                for d in dims_found if tag is None or d.tag == tag]

    def test_wall_lines(self):
        from arqbim.model import dim_refs
        found = dim_refs.lines(self.doc, [self.inner])[self.inner]
        self.assertAlmostEqual(found.lo, -0.1)
        self.assertAlmostEqual(found.hi, 0.1)
        self.assertLess(found.core[1] - found.core[0], 0.2)          # (its block, without the plaster)
        self.assertGreater(found.core[1] - found.core[0], 0.05)
        self.assertEqual([k for _y, k in found.ys("faces")], ["face_lo", "face_hi"])
        self.assertEqual(found.ys("axis"), [(0.0, "axis")])
        walls = dim_refs.walls_of(self.doc, self.doc.active_storey)
        across = dim_refs.crossings(walls, np.array((-1.0, 3.0, 0.0)), np.array((1.0, 0.0, 0.0)), 12.0, "faces")
        self.assertEqual([round(c[0] - 1.0, 3) for c in across], [-0.1, 0.1, 3.9, 4.1, 9.9, 10.1])

    def test_outside(self):
        from arqbim.model import auto_dims
        from arqbim.model import dimensions as dims
        doc, storey = self.doc, self.doc.active_storey
        faces = auto_dims.exterior(doc, storey, "faces")
        self.assertEqual(len({d.tag for d in faces}), 4)
        south = self._texts(faces, "ext:270")
        self.assertEqual(south[:2], ["1,50", "0,80"])                   # (the openings' row first)
        self.assertEqual(south.count("10,20"), 1)                       # (its overall)
        north = self._texts(faces, "ext:90")
        self.assertIn("6,20", north)                                    # (the setback: its corners row)
        self.assertIn("4,00", north)
        self.assertEqual(north.count("0,20"), 4)                        # (the walls that reach it: their faces)
        self.assertTrue(all(d.chain for d in faces))
        rows = {}
        for d in faces:
            rows.setdefault(d.chain, []).append(d)
        self.assertTrue(all(len({x.tag for x in r}) == 1 for r in rows.values()))
        axes = auto_dims.exterior(doc, storey, "axis")
        self.assertEqual(self._texts(axes, "ext:270").count("10,00"), 1)
        self.assertEqual(self._texts(axes, "ext:90")[-1], "10,00")
        core = auto_dims.exterior(doc, storey, "core_faces")
        overall = self._texts(core, "ext:270")[-1]
        self.assertNotEqual(overall, "10,20")                           # (the outer core faces: in from the plaster)
        # an end on a wall's line stays on it: the wall moved, then given a thicker type
        doc.execute(dims.ReplaceDimensions([], faces, "Cotar"))
        inner_ends = [(d, k) for d in faces for k, r in enumerate(d.refs) if r is not None and r[0] == self.inner
                      and len(r) > 3]
        self.assertTrue(inner_ends)
        bim.set_type(doc, self.inner, catalog.BY_KEY["parede_alv_25"] if "parede_alv_25" in catalog.BY_KEY
                     else catalog.BY_KEY["parede_betao_25"])
        from arqbim.model import dim_refs
        lines = dim_refs.lines(doc, [self.inner])[self.inner]
        for d, k in inner_ends:
            p = dims.ends(doc, d)[k]
            y = lines.local(p)[1]
            self.assertTrue(min(abs(y - lines.lo), abs(y - lines.hi)) < 1e-6, (y, lines.lo, lines.hi))
        # any direction: the same house turned 30°
        turned = Document()
        c, s = np.cos(np.radians(30)), np.sin(np.radians(30))
        pts = [(x * c - y * s, x * s + y * c, 0.0) for x, y in ((0, 0), (10, 0), (10, 5), (6, 5), (6, 8), (0, 8))]
        bim.add_wall_loop(turned, [np.array(p) for p in pts], catalog.BY_KEY["parede_alv_20"])
        found = auto_dims.exterior(turned, turned.active_storey, "faces")
        self.assertEqual(len({d.tag for d in found}), 4)
        o, u, v = np.zeros(3), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
        values = [dims.text(dims.placed(*dims.ends(turned, d), d.at, o, u, v, d.direction)[4]) for d in found]
        self.assertEqual(values.count("10,20"), 2)                      # (south and north overall)
        self.assertEqual(values.count("8,20"), 2)                       # (east and west)
        self.assertIn("6,20", values)


class InsideDimensions(OneClickDimensions):
    """0.400: the rooms the walls close (no Room made), and their inside dimensions — width and depth through a point,
    a run across the building, along the walls with their openings — by finish faces, axes or core faces."""

    def _values(self, found):
        return self._texts(found)

    def test_rooms_and_modes(self):
        from arqbim.model import auto_dims
        doc, storey = self.doc, self.doc.active_storey
        rooms = auto_dims.rooms(doc, storey)
        self.assertEqual(sorted(round(r.area, 2) for r in rooms), [29.64, 33.24])   # (3,80 × 7,80; the L)
        size = auto_dims.interior(doc, storey, (2.0, 3.0), "faces", "size")
        self.assertEqual(sorted(self._values(size)), ["3,80", "7,80"])
        self.assertTrue(all(d.tag.startswith("int:size:") for d in size))
        self.assertTrue(any(abs(float(d.at[1]) - 3.0) < 1e-6 for d in size))      # (through the point clicked)
        run = auto_dims.interior(doc, storey, (2.0, 3.0), "faces", "run", directions="width")
        values = self._values(run)
        self.assertEqual(values, ["0,20", "3,80", "0,20", "5,80", "0,20"] if run[0].direction[0] > 0.5 else
                         ["0,20", "7,80", "0,20"])
        axes = auto_dims.interior(doc, storey, (2.0, 3.0), "axis", "run")
        self.assertIn("4,00", self._values(axes))
        self.assertIn("6,00", self._values(axes))
        frame = bim.wall_frame(doc, self.inner)
        bim.add_opening(doc, self.inner, catalog.OPENING_BY_KEY["porta_80"], frame, frame.x0 + 2.0, -1)
        along = auto_dims.interior(doc, storey, (7.0, 2.0), "faces", "walls")
        self.assertIn("0,80", self._values(along))                  # (the inner wall's door, from the right room)
        self.assertIn("4,00", self._values(along))                  # (the setback's wall)
        every = auto_dims.interior(doc, storey, None, "faces", "size", every=True)
        self.assertEqual(len({d.chain for d in every}), 4)          # (two strings in each room)
        self.assertEqual(auto_dims.interior(doc, storey, (20.0, 20.0), "faces", "size"), [])   # (outside: none)
        # (0.409) the L's inner corner on its width: 1,80 to the corner, 4,00 on; its depth wall to wall
        corner = auto_dims.interior(doc, storey, (8.0, 2.0), "faces", "size")
        self.assertEqual(sorted(self._values(corner)), ["1,80", "4,00", "4,80"])
        self.assertEqual(len({d.chain for d in corner}), 2)
        axes = auto_dims.interior(doc, storey, (8.0, 2.0), "axis", "size")
        self.assertIn("2,00", self._values(axes))                   # (axis to axis: 4 → 6)

    def test_axes_follow_the_nearest_wall(self):
        """(0.408) An L-shaped room with a wall askew (its longest side): near that wall the dimensions follow it, near
        the others they follow them (until 0.407 the wall askew everywhere)."""
        from shapely.geometry import Polygon
        from arqbim.model import auto_dims
        room = Polygon([(0, 0), (8, 0.28), (8, 6), (4, 6), (4, 3), (0, 3)])
        askew = np.array((8.0, 0.28)) / np.hypot(8.0, 0.28)
        self.assertTrue(np.allclose(auto_dims.room_axes(room)[0], askew))
        for point in ((6.0, 5.8), (7.9, 4.0), (0.2, 2.0)):
            width, depth = auto_dims.room_axes(room, point)
            self.assertTrue(np.allclose(width, (1.0, 0.0)) and np.allclose(depth, (0.0, 1.0)), point)
        self.assertTrue(np.allclose(auto_dims.room_axes(room, (4.0, 0.4))[0], askew))
        doc = Document()
        bim.add_wall_loop(doc, [np.array((x, y, 0.0)) for x, y in ((0, 0), (8, 0.28), (8, 6), (0, 6))],
                          catalog.BY_KEY["parede_alv_20"])
        near_top = auto_dims.interior(doc, doc.active_storey, (4.0, 5.5), "faces", "size")
        near_bottom = auto_dims.interior(doc, doc.active_storey, (4.0, 0.6), "faces", "size")
        self.assertTrue(near_top and near_bottom)
        self.assertTrue(any(np.allclose(d.direction[:2], (1.0, 0.0)) for d in near_top))
        self.assertTrue(any(np.allclose(d.direction[:2], askew, atol=1e-6) for d in near_bottom))
        # (0.409) a room with a wall askew (not nearly square): near its corner with the top, one along each of the two
        # («devia pegar as 2 paredes») — across, parallel to the top, to the wall askew; and along the wall askew
        slant = np.array((2.5, 7.0)) / np.hypot(2.5, 7.0)
        trapeze = Polygon([(0, 0), (4, 0), (6.5, 7), (0, 7)])
        found = auto_dims.room_axes(trapeze, (5.9, 6.7))
        self.assertTrue(np.allclose(found[0], slant) and np.allclose(found[1], (1.0, 0.0)), found)
        doc = Document()
        bim.add_wall_loop(doc, [np.array((x, y, 0.0)) for x, y in ((0, 0), (4, 0), (6.5, 7), (0, 7))],
                          catalog.BY_KEY["parede_alv_20"])
        dims = auto_dims.interior(doc, doc.active_storey, (5.6, 6.5), "faces", "size")
        self.assertEqual(len(dims), 2)                              # (no corner of the wall askew between)
        ways = sorted(tuple(np.round(d.direction[:2], 3)) for d in dims)
        self.assertEqual(ways, sorted([(1.0, 0.0), tuple(np.round(slant, 3))]))
        self.assertEqual(sorted(self._values(dims))[0][:2], "6,")  # (across, left wall to the wall askew: 6,1…)


class EditDimensionStrings(unittest.TestCase):
    """0.402: a string across three parallel walls (axis to axis, 3 + 5 m) edited as Revit's: its line moved off, a
    value moved apart, IG (the middle wall moved: 4 + 4), the witness line in the middle deleted (one of 8), a
    value typed (the far wall moved), its own words — each one undo step, all kept beside the IFC."""

    def setUp(self):
        from arqbim.model import dim_refs
        from arqbim.model import dimensions as dims
        self.dims = dims
        self.doc = doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        self.walls = [bim.add_wall(doc, np.array((0.0, y, 0.0)), np.array((6.0, y, 0.0)), spec) for y in (0.0, 3.0, 8.0)]
        chain = dims.new_chain()
        self.string = []
        for g0, g1, y0, y1 in ((self.walls[0], self.walls[1], 0.0, 3.0), (self.walls[1], self.walls[2], 3.0, 8.0)):
            a, b = np.array((2.0, y0, 0.0)), np.array((2.0, y1, 0.0))
            refs = [dim_refs.hang(doc, g0, a, "axis"), dim_refs.hang(doc, g1, b, "axis")]
            self.string.append(dims.Dimension(("plan", doc.active_storey), a, b, np.array((-1.0, 4.0, 0.0)), refs,
                                              direction=np.array((0.0, 1.0, 0.0)), chain=chain))
        doc.execute(dims.ReplaceDimensions([], self.string, "Cotar"))
        self.plane = (np.zeros(3), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0)), np.array((0.0, 0.0, 1.0)))

    def _values(self):
        o, u, v, _n = self.plane
        return [self.dims.text(self.dims.placed(*self.dims.ends(self.doc, d), self.dims.line_point(self.doc, d), o, u,
                                                v, d.direction)[4]) for d in self.doc.dimensions]

    def test_edits(self):
        from arqbim.model import dim_edit
        from arqbim.model import drawings
        doc, dims = self.doc, self.dims
        self.assertEqual(dim_edit.string_of(doc, self.string[1]), self.string)
        self.assertEqual(self._values(), ["3,00", "5,00"])
        dim_edit.move_line(doc, self.string, np.array((-1.0, 0.5, 0.0)), self.plane, "Linha")
        self.assertTrue(all(abs(float(dims.line_point(doc, d)[0]) + 2.0) < 1e-9 for d in self.string))
        dim_edit.move_text(doc, self.string[0], (0.3, 0.6), "Texto")
        piece = dims.piece_of(doc, self.string[0], *self.plane[:3], doc.dim_style)
        self.assertEqual(piece[6]["label"].shift, (0.3, 0.6))
        moved = dim_edit.equalize(doc, self.string, self.plane, "IG")
        self.assertEqual(moved, 1)
        self.assertTrue(all(d.eq for d in self.string))
        self.assertEqual([p[4] for p in drawings.plan(doc, doc.active_storey, "Planta").dims], ["IG", "IG"])
        self.assertAlmostEqual(float(doc.ifc.wall_axis(self.walls[1])[0][1]), 4.0)        # (the middle wall moved)
        doc.undo()
        self.assertAlmostEqual(float(doc.ifc.wall_axis(self.walls[1])[0][1]), 3.0)        # (one undo step)
        self.assertFalse(any(d.eq for d in self.string))
        self.assertTrue(dim_edit.remove_witness(doc, self.string, 1, "Apagar"))
        self.assertEqual(self._values(), ["8,00"])
        doc.undo()
        self.assertEqual(self._values(), ["3,00", "5,00"])
        self.assertTrue(dim_edit.set_value(doc, self.string[1], 6.0, self.plane, self.walls[2], "Valor"))
        self.assertEqual(self._values(), ["3,00", "6,00"])
        self.assertTrue(dim_edit.set_value(doc, self.string[0], 2.5, self.plane, self.walls[1], "Valor"))
        self.assertEqual(self._values(), ["2,50", "6,50"])                                 # (the middle one moved)
        dim_edit.set_note(doc, [self.string[0]], {"override": "VAR", "prefix": "", "suffix": "", "above": "",
                                                   "below": "h=2,10"}, "Texto")
        piece = dims.piece_of(doc, self.string[0], *self.plane[:3], doc.dim_style)
        self.assertEqual((piece[4], piece[6]["label"].below), ("VAR", "h=2,10"))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "editadas.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        back = [d for d in again.dimensions if d.note]
        self.assertEqual(back[0].note.get("override"), "VAR")
        self.assertEqual(len({d.chain for d in again.dimensions}), 1)
        self.assertEqual([len(d.refs[0]) for d in again.dimensions], [4, 4])               # (on the walls' axes)


class AutomaticDimensions(unittest.TestCase):
    """0.123: a 10 × 6 m house (walls 20 cm, a closed loop) with a door and a window in its south wall and a
    room: Dimension the façades — on each side, out from its face, the corners and the jambs (south: 6
    dimensions), its corners (only where there are openings: none here, a rectangle has two), its length;
    horizontal / vertical, the south row's sum its length; Dimension the rooms — 9,80 and 5,80 from wall to
    wall. Along a direction: the extension lines square to it, the points at different depths."""

    def test_facades_and_rooms(self):
        from arqbim.model import dimensions as dims
        from arqbim.model import drawings
        doc = Document()
        walls = bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (10.0, 6.0, 0.0),
                                                               (0.0, 6.0, 0.0))], catalog.BY_KEY["parede_alv_20"])
        south = walls[0]
        frame = bim.wall_frame(doc, south)
        bim.add_opening(doc, south, catalog.OPENING_BY_KEY["porta_80"], frame, frame.x0 + 2.0, -1)
        bim.add_opening(doc, south, catalog.OPENING_BY_KEY["janela_120"], frame, frame.x0 + 6.0, -1)
        found = dims.facade_chains(doc, doc.active_storey)
        by_side = {s: [d for d in found if d.tag == "facade:" + s] for s in "SNWE"}
        self.assertEqual([len(by_side[s]) for s in "SNWE"], [6, 1, 1, 1])     # (south: 5 in the chain + overall)
        o, u, v = np.zeros(3), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
        lengths = [dims.placed(d.a, d.b, d.at, o, u, v, d.direction)[4] for d in by_side["S"]]
        self.assertAlmostEqual(sum(lengths[:-1]), 10.2)
        self.assertAlmostEqual(lengths[-1], 10.2)
        self.assertTrue(all(np.allclose(d.direction, (1.0, 0.0, 0.0)) for d in by_side["S"]))
        self.assertAlmostEqual(float(by_side["S"][0].at[1]), -0.1 - 0.8)
        self.assertAlmostEqual(float(by_side["S"][-1].at[1]), -0.1 - 2.0)
        self.assertTrue(np.allclose(by_side["W"][0].direction, (0.0, 1.0, 0.0)))
        self.assertTrue(all(d.refs[0] is not None and d.refs[1] is not None for d in by_side["S"]))
        bim.add_room(doc, (5.0, 3.0), "Sala")
        rooms = dims.room_chains(doc, doc.active_storey)
        self.assertEqual(sorted(round(dims.placed(d.a, d.b, d.at, o, u, v, d.direction)[4], 3) for d in rooms),
                         [5.8, 9.8])
        doc.execute(dims.ReplaceDimensions([], found + rooms, "Cotar"))
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual(len(plan.dims), 9 + 2)
        # along a direction, the points at different depths: the line square to it, each extension line to it
        p1, p2, l1, l2, length = dims.placed(np.array((0.0, 0.0, 0.0)), np.array((3.0, 1.0, 0.0)),
                                             np.array((1.0, -1.0, 0.0)), o, u, v, np.array((1.0, 0.0, 0.0)))
        self.assertAlmostEqual(length, 3.0)
        self.assertTrue(np.allclose(l1, (0.0, -1.0)) and np.allclose(l2, (3.0, -1.0)), (l1, l2))


class ViewSymbols(unittest.TestCase):
    """0.121: a 10 × 6 m house with a section across it (looking south) and a storey at 3 m: in its plan, the
    section's line across the house (4 mm on paper past it: 0,40 m at 1:100), its tag "1", the four elevation
    marks (16 mm out), their arrows towards it, the north arrow — the plan no bigger for them; in the section,
    the two levels (±0,00 and +3,00)."""

    def test_marks_and_levels(self):
        from arqbim.model import drawings
        from arqbim.model import symbols
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        for a, b in (((0.0, 0.0), (10.0, 0.0)), ((10.0, 0.0), (10.0, 6.0)), ((10.0, 6.0), (0.0, 6.0)),
                     ((0.0, 6.0), (0.0, 0.0))):
            bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
        bim.add_storey(doc, "Piso 1", 3.0)
        doc.add_section((5.0, 3.0, 0.0), (0.0, -1.0, 0.0))
        lo, hi = symbols.extent(doc)
        self.assertTrue(np.allclose(lo, (-0.1, -0.1)) and np.allclose(hi, (10.1, 6.1)), (lo, hi))
        (cut,) = symbols.section_marks(doc)
        self.assertEqual((cut.tag, cut.ref), ("1", doc.sections[0].name))
        self.assertTrue(np.allclose(sorted((cut.a[0], cut.b[0])), (-0.1, 10.1)) and np.allclose((cut.a[1], cut.b[1]), 3.0))
        self.assertTrue(np.allclose(cut.look, (0.0, -1.0)))
        (at_100,) = symbols.section_marks(doc, mm=0.1)                     # (on screen at 1:100: 4 mm = 0,40 m)
        self.assertTrue(np.allclose(sorted((at_100.a[0], at_100.b[0])), (-0.5, 10.5)))
        marks = {m.ref: m for m in symbols.elevation_marks(doc, {"W": "O"}, mm=0.1)}
        self.assertTrue(np.allclose(marks["N"].a, (5.0, 7.7)) and np.allclose(marks["N"].look, (0.0, -1.0)))
        self.assertTrue(np.allclose(marks["W"].a, (-1.7, 3.0)) and marks["W"].tag == "O")
        self.assertEqual([symbols.short_tag(n) for n in ("Corte 1", "Corte A", "Cozinha", "")], ["1", "A", "Coz", "?"])
        self.assertEqual([symbols.level_text(z) for z in (0.0, 3.0, -0.5)], ["±0,00", "+3,00", "-0,50"])
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual(sorted(m.kind for m in plan.marks), ["elevation"] * 4 + ["section"])
        self.assertTrue(plan.north)
        b_lo, b_hi = plan.bounds()
        self.assertTrue(np.allclose(b_lo, (-0.1, -0.1)) and np.allclose(b_hi, (10.1, 6.1)), (b_lo, b_hi))
        #                                    (the marks do not make it bigger: a sheet's scale stays)
        section = drawings.section(doc, (5.0, 3.0, 0.0), (0.0, -1.0, 0.0), "C", ("section", doc.sections[0].name))
        self.assertEqual([round(z, 6) for z, _n in section.levels], [0.0, 3.0])
        self.assertEqual(section.marks, [])
        self.assertFalse(section.north)


class DrawingInViews(unittest.TestCase):
    """0.120: lines, a rectangle, a circle, an arc, a hatched region and a text drawn in the plan of a storey and
    in a section: their shapes in the view's frame; on paper (that view's drawing only); undone and done again;
    kept beside the IFC; a section renamed takes its own, removed takes them."""

    def setUp(self):
        from arqbim.model import annotations as notes2d
        self.n = notes2d
        self.doc = doc = Document()
        bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        doc.add_section((2.0, 2.0, 0.0), (0.0, -1.0, 0.0))
        plan = ("plan", doc.active_storey)
        p = lambda x, y: np.array((x, y, 0.0))        # noqa: E731
        self.made = [notes2d.Annotation(plan, "line", [p(0, 2), p(3, 2)]),
                     notes2d.Annotation(plan, "rectangle", [p(1, 3), p(3, 4)]),
                     notes2d.Annotation(plan, "circle", [p(6, 3), p(6.5, 3)]),
                     notes2d.Annotation(plan, "arc", [p(0, 5), p(2, 5), p(1, 6)]),
                     notes2d.Annotation(plan, "region", [p(0, 7), p(2, 7), p(2, 8), p(0, 8)], hatch="cross"),
                     notes2d.Annotation(plan, "text", [p(0, 9)], text="SALA 1"),
                     notes2d.Annotation(("section", "Corte 1"), "line", [np.array((0.0, 2.0, 0.0)),
                                                                           np.array((0.0, 2.0, 2.8))])]
        for ann in self.made:
            doc.execute(notes2d.AddAnnotation(ann, "Desenho"))

    def test_shapes_and_paper(self):
        from arqbim.model import drawings
        n, doc = self.n, self.doc
        o, u, v = np.zeros(3), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
        line, rect, circle, arc, region, text, _section = self.made
        self.assertEqual(len(n.segments(line, o, u, v)), 1)
        self.assertTrue(np.allclose(n.shape(rect, o, u, v)[0][0], [(1, 3), (3, 3), (3, 4), (1, 4)]))
        ring = n.shape(circle, o, u, v)[0][0]
        self.assertTrue(np.allclose(np.linalg.norm(ring - (6.0, 3.0), axis=1), 0.5))
        pts = n.shape(arc, o, u, v)[0][0]
        self.assertTrue(np.allclose(pts[0], (0, 5)) and np.allclose(pts[-1], (2, 5)))
        self.assertAlmostEqual(float(pts[:, 1].max()), 6.0, places=3)          # (through (1, 6): a half circle)
        self.assertAlmostEqual(n.area(region, o, u, v), 2.0)
        hatch = n.hatch_lines(n.shape(region, o, u, v)[0][0], "cross", 0.1)
        self.assertGreater(len(hatch), 20)
        self.assertTrue(np.all(hatch[:, :, 0] >= -1e-9) and np.all(hatch[:, :, 0] <= 2 + 1e-9))
        self.assertEqual(n.shape(text, o, u, v), [])
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual([a[0] for a in plan.annotations], ["line", "rectangle", "circle", "arc", "region", "text"])
        self.assertEqual(plan.annotations[5][3], "SALA 1")
        lo, hi = plan.bounds()
        self.assertTrue(hi[1] >= 9.0 and hi[0] >= 6.5, (lo, hi))                 # (they count in its extent)
        section = drawings.section(doc, (2.0, 2.0, 0.0), (0.0, -1.0, 0.0), "C", ("section", "Corte 1"))
        self.assertEqual([a[0] for a in section.annotations], ["line"])
        a2 = section.annotations[0][1][0][0]
        self.assertAlmostEqual(abs(float(a2[1, 1] - a2[0, 1])), 2.8)          # (upright in the section)
        doc.undo()
        self.assertEqual(len(doc.annotations), 6)
        doc.redo()
        self.assertEqual(len(doc.annotations), 7)
        doc.execute(n.RemoveAnnotations([rect, text], "Apagar"))
        self.assertEqual(len(doc.annotations_of(("plan", doc.active_storey))), 4)
        doc.undo()
        self.assertEqual(doc.annotations[1], rect)
        doc.execute(n.MoveAnnotations([line], (0.0, 1.0, 0.0), "Mover"))
        self.assertTrue(np.allclose(line.points[0], (0.0, 3.0, 0.0)))
        doc.undo()
        self.assertTrue(np.allclose(line.points[0], (0.0, 2.0, 0.0)))

    def test_kept_beside_the_ifc(self):
        doc = self.doc
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "desenho.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        self.assertEqual([a.kind for a in again.annotations], [a.kind for a in self.made])
        self.assertEqual(again.annotations[5].text, "SALA 1")
        self.assertEqual(again.annotations[4].hatch, "cross")
        self.assertTrue(np.allclose(again.annotations[3].points[2], (1.0, 6.0, 0.0)))
        again.rename_section(0, "Corte A")
        self.assertEqual(again.annotations[6].view, ("section", "Corte A"))
        again.undo()
        self.assertEqual(again.annotations[6].view, ("section", "Corte 1"))
        again.remove_section(0)
        self.assertEqual(len(again.annotations), 6)                  # (its drawings go with it)


class Dimensions(unittest.TestCase):
    """Cotas (Phase 3, step 14): kept in their view, an end on an element follows it."""

    def setUp(self):
        from arqbim.model import dimensions as dims
        self.dims = dims
        self.doc = doc = Document()
        self.wall = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        doc.add_section((2.0, 2.0, 0.0), (0.0, -1.0, 0.0))
        a, b = np.array((0.0, -0.1, 0.0)), np.array((5.0, -0.1, 0.0))        # the wall's outer face, end to end
        self.dim = dims.Dimension(("plan", doc.active_storey), a, b, np.array((2.5, -1.0, 0.0)),
                                  [dims.hang(doc, self.wall, a), dims.hang(doc, self.wall, b)])
        doc.execute(dims.AddDimension(self.dim, "Cota"))

    def test_in_its_plan_and_following_the_wall(self):
        from arqbim.model import drawings
        doc = self.doc
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual(len(plan.dims), 1)
        a2, b2, l1, l2, text = plan.dims[0][:5]                     # (0.398: then its type and its string)
        self.assertEqual(text, "5,00")
        self.assertAlmostEqual(float(l1[1] - a2[1]), -0.9, places=6)   # the line 0,90 m off the face, outside
        self.assertAlmostEqual(float(l2[1] - b2[1]), -0.9, places=6)
        self.assertEqual(drawings.section(doc, (2.0, 2.0, 0.0), (0.0, -1.0, 0.0), "C", ("section", "Corte 1")).dims,
                         [])                                        # not in another view
        bim.transform_objects(doc, [self.wall], translation((1.0, 2.0, 0.0)), "Mover")
        a, b = self.dims.ends(doc, self.dim)
        self.assertTrue(np.allclose(a, (1.0, 1.9, 0.0)) and np.allclose(b, (6.0, 1.9, 0.0)), (a, b))
        doc.undo()                                                  # the move
        doc.undo()                                                  # the dimension
        self.assertEqual(doc.dimensions, [])
        doc.redo()
        self.assertEqual(doc.dimensions, [self.dim])

    def test_kept_beside_the_ifc_and_following_the_section(self):
        doc = self.doc
        section_dim = self.dims.Dimension(("section", "Corte 1"), np.zeros(3), np.array((0.0, 0.0, 2.8)),
                                          np.array((1.0, 0.0, 1.4)))
        doc.execute(self.dims.AddDimension(section_dim, "Cota"))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cotas.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        self.assertEqual([d.view for d in again.dimensions], [("plan", doc.active_storey), ("section", "Corte 1")])
        plan_dim = again.dimensions[0]
        self.assertEqual(plan_dim.refs[0][0], self.wall)
        bim.transform_objects(again, [self.wall], translation((0.0, 3.0, 0.0)), "Mover")
        self.assertTrue(np.allclose(self.dims.ends(again, plan_dim)[0], (0.0, 2.9, 0.0)))   # still hangs on it
        again.rename_section(0, "Corte A")
        self.assertEqual(again.dimensions[1].view, ("section", "Corte A"))
        again.remove_section(0)
        self.assertEqual(len(again.dimensions), 1)                  # its dimensions go with it
        self.assertEqual(self.dims.text(4.5), "4,50")

    def test_ends_follow_a_longer_wall_a_moved_door_and_the_line(self):
        doc = self.doc                             # (setUp: from (0, -0,1) to (5, -0,1), on the wall's face)
        bim.resize_wall(doc, self.wall, at_end=1.0)
        a, b = self.dims.ends(doc, self.dim)
        self.assertTrue(np.allclose(a, (0.0, -0.1, 0.0)) and np.allclose(b, (6.0, -0.1, 0.0)), (a, b))
        bim.resize_wall(doc, self.wall, at_start=0.5)
        a, b = self.dims.ends(doc, self.dim)
        self.assertTrue(np.allclose(a[:2], (-0.5, -0.1)) and np.allclose(b[:2], (6.0, -0.1)), (a, b))
        door = bim.add_opening(doc, self.wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, self.wall),
                               1.0, -1)
        chain = self.dims.wall_chains(doc, [self.wall], doc.active_storey)
        doc.execute(self.dims.ReplaceDimensions([], chain, "Cotar"))
        jamb = [d for d in chain if d.refs[1] is not None and d.refs[1][0] == door][0]    # wall start -> door
        before = self.dims.ends(doc, jamb)[1][0]
        bim.move_filling(doc, door, s=bim.wall_frame(doc, self.wall).x0 + 2.0)
        self.assertAlmostEqual(self.dims.ends(doc, jamb)[1][0] - before, 1.0, places=6)    # the jamb went along
        line = self.dims.line_point(doc, jamb)
        bim.transform_objects(doc, [self.wall], translation((0.0, 3.0, 0.0)), "Mover")
        self.assertTrue(np.allclose(self.dims.line_point(doc, jamb) - line, (0.0, 3.0, 0.0)))   # and the line

    def test_angular(self):
        """0.122: the angle between two lines on the side where its arc is put (of the four they make); in the
        plan's drawing; its corner on a wall follows it; kept beside the IFC."""
        dims, doc = self.dims, self.doc
        v, a, b = np.zeros(2), np.array((1.0, 0.0)), np.array((0.5, np.sqrt(3) / 2))     # 60° apart
        r, start, sweep, value = dims.angle_arc(a, b, v, np.array((0.5, 0.3)))
        self.assertAlmostEqual(value, 60.0)
        self.assertAlmostEqual(start, 0.0)
        self.assertAlmostEqual(r, float(np.hypot(0.5, 0.3)))
        self.assertAlmostEqual(dims.angle_arc(a, b, v, np.array((-0.5, 0.3)))[3], 120.0)     # the other side
        self.assertAlmostEqual(dims.angle_arc(a, b, v, np.array((-0.5, -0.3)))[3], 60.0)     # across the corner
        self.assertIsNone(dims.angle_arc(a, a * 2, v, np.array((0.0, 1.0))))                 # (parallel)
        self.assertEqual([dims.angle_text(x) for x in (90.0, 22.5, 44.96)], ["90°", "22,5°", "45°"])
        corner = np.array((0.0, -0.1, 0.0))                                                  # the wall's start
        dim = dims.Dimension(("plan", doc.active_storey), np.array((2.0, -0.1, 0.0)), np.array((-1.0, -1.1, 0.0)),
                             np.array((1.0, 0.2, 0.0)), [dims.hang(doc, self.wall, np.array((2.0, -0.1, 0.0))), None],
                             vertex=corner, vertex_ref=dims.hang(doc, self.wall, corner))
        doc.execute(dims.AddDimension(dim, "Cota"))
        from arqbim.model import drawings
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual(len(plan.angles), 1)
        self.assertEqual(plan.angles[0][4], "45°")
        self.assertEqual(len(plan.dims), 1)                                  # (setUp's linear one)
        bim.transform_objects(doc, [self.wall], translation((0.0, 2.0, 0.0)), "Mover")
        self.assertTrue(np.allclose(dims.vertex_point(doc, dim), (0.0, 1.9, 0.0)))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "angulos.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        back = [d for d in again.dimensions if d.vertex is not None]
        self.assertEqual(len(back), 1)
        self.assertEqual(back[0].vertex_ref[0], self.wall)
        self.assertTrue(np.allclose(back[0].vertex, corner))

    def test_style(self):
        """0.124: the project's dimension style — the values in centimetres / millimetres, its decimals; a
        changed style undone; on paper (its text, its mark); kept beside the IFC."""
        dims, doc = self.dims, self.doc
        self.assertEqual([dims.text(4.5, ",", s) for s in ({"unit": "m", "decimals": 2}, {"unit": "cm", "decimals": 0},
                                                           {"unit": "mm", "decimals": 0},
                                                           {"unit": "cm", "decimals": 1})],
                         ["4,50", "450", "4500", "450,0"])
        self.assertEqual(dims.clean_style({"mark": "boom", "text": "x", "decimals": 9, "unit": "cm"}),
                         dict(dims.STYLE_DEFAULTS, unit="cm", decimals=4))     # (0.398: every key of a type)
        from arqbim.model import drawings
        new = {"text": 3.5, "mark": "arrow", "unit": "cm", "decimals": 0}
        doc.execute(dims.SetDimensionStyle(doc.dim_style, new, "Estilo"))
        plan = drawings.plan(doc, doc.active_storey, "Planta")
        self.assertEqual(plan.dims[0][4], "500")
        self.assertEqual(plan.dim_style["mark"], "arrow")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "estilo.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            geomcache.forget(path)
        self.assertEqual(again.dim_style, dims.clean_style(new))
        doc.undo()
        self.assertEqual(doc.dim_style, dims.STYLE_DEFAULTS)
        self.assertEqual(drawings.plan(doc, doc.active_storey, "Planta").dims[0][4], "5,00")

    def test_wall_chains(self):
        doc = self.doc
        bim.add_opening(doc, self.wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, self.wall), 1.0, -1)
        chain = self.dims.wall_chains(doc, [self.wall], doc.active_storey)
        lengths = [round(float(np.linalg.norm(d.b - d.a)), 6) for d in chain]
        self.assertEqual(lengths, [1.0, 0.8, 3.2, 5.0])                 # to the door, the door, after it; overall
        self.assertTrue(all(abs(d.a[1] + 0.1) < 1e-6 for d in chain))  # on a face (one wall alone: its -y side)
        self.assertEqual([round(float(d.at[1]), 6) for d in chain], [-0.9, -0.9, -0.9, -1.5])
        doc.execute(self.dims.ReplaceDimensions([], chain, "Cotar"))
        again = self.dims.wall_chains(doc, [self.wall], doc.active_storey)
        old = [d for d in doc.dimensions if d.tag == "wall:" + self.wall]
        doc.execute(self.dims.ReplaceDimensions(old, again, "Cotar"))
        self.assertEqual(len(doc.dimensions), 1 + 4)                   # replaced, not doubled (+ setUp's one)
        bim.transform_objects(doc, [self.wall], translation((0.0, 2.0, 0.0)), "Mover")
        self.assertAlmostEqual(float(self.dims.ends(doc, again[3])[0][1]), 1.9)   # they follow the wall
        doc.undo()
        doc.undo()
        self.assertEqual(doc.dimensions[1:], chain)


class FarFromOrigin(unittest.TestCase):
    """A georeferenced model (Revit's shared coordinates: the site 500 km away) is worked on
    near the origin; the IFC keeps its real coordinates."""

    FAR = np.array((512345.0, 4301234.0, 0.0))

    def setUp(self):
        import ifcopenshell.api.geometry  # noqa: F401
        doc = Document()
        self.wall = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        bim.add_opening(doc, self.wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, self.wall), 1.0, -1)
        f = doc.ifc.file
        site = f.by_type("IfcSite")[0]
        ifcopenshell.api.geometry.edit_object_placement(f, product=site, matrix=translation(self.FAR), is_si=True,
                                                        should_transform_children=True)
        box_object(doc, (1, 2, 0), 1, 1, 1)                              # a sketch, kept beside the IFC
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "georef.ifc")
        doc.save(self.path)

    def tearDown(self):
        geomcache.forget(self.path)
        self.tmp.cleanup()

    def world(self, doc, guid):
        import ifcopenshell.util.placement as up
        e = doc.ifc.by_guid(guid)
        return up.get_local_placement(e.ObjectPlacement)[:3, 3] * doc.ifc.unit_scale

    def test_opened_near_the_origin(self):
        doc = Document()
        doc.open(self.path)
        self.assertTrue(np.allclose(doc.ifc.origin, self.FAR))
        lo, hi = bounds(doc, self.wall)
        self.assertTrue(np.all(np.abs(lo) < 10) and np.all(np.abs(hi) < 10), (lo, hi))   # near (0, 0)
        a, b, _t = doc.ifc.wall_axis(self.wall)
        self.assertTrue(np.allclose(a, (0, 0, 0)) and np.allclose(b, (5, 0, 0)), (a, b))
        self.assertTrue(np.allclose(self.world(doc, self.wall), self.FAR))             # the IFC is unchanged
        # the sketch was drawn before the site was moved: it keeps its own (real) place
        sketch = doc.sketches()[0]
        self.assertTrue(np.allclose(sketch.matrix[:3, 3], np.array((1, 2, 0)) - self.FAR))

    def test_editing_writes_real_coordinates(self):
        doc = Document()
        doc.open(self.path)
        new = bim.add_wall(doc, (0, 3, 0), (4, 3, 0), catalog.BY_KEY["parede_alv_20"])
        self.assertTrue(np.allclose(self.world(doc, new), self.FAR + (0, 3, 0)))
        bim.transform_objects(doc, [self.wall], translation((0, -1, 0)), "Mover")
        self.assertTrue(np.allclose(self.world(doc, self.wall), self.FAR + (0, -1, 0)))
        lo, _hi = bounds(doc, self.wall)
        self.assertAlmostEqual(lo[1], -1.1, places=6)
        bim.resize_wall(doc, self.wall, height=3.2)                       # regenerated in place
        self.assertTrue(np.allclose(self.world(doc, self.wall), self.FAR + (0, -1, 0)))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        near = box_object(doc, (1, 6, 0), 1, 1, 1)                       # a sketch drawn by the building
        doc.add_section((2.0, 1.0, 0.0), (0.0, 1.0, 0.0))               # a named section, kept too
        doc.add_section((2.0, 5.0, 0.0), (1.0, 0.0, 0.0))
        doc.rename_section(1, "Corte da escada")
        doc.last_section = 0
        doc.save(self.path)
        again = Document()
        again.open(self.path)
        self.assertTrue(np.allclose(again.ifc.wall_axis(new)[0], (0, 3, 0)))
        found = [o for o in again.sketches() if np.allclose(o.matrix[:3, 3], near.matrix[:3, 3])]
        self.assertEqual(len(found), 1)
        self.assertTrue(np.allclose(again.section[0], (2.0, 1.0, 0.0)) and np.allclose(again.section[1], (0, 1, 0)))
        self.assertEqual([s.name for s in again.sections], ["Corte 1", "Corte da escada"])
        again.remove_section(0)
        self.assertEqual((len(again.sections), again.last_section), (1, None))
        self.assertEqual(again.sections[0].name, "Corte da escada")
        again.add_section((0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        self.assertEqual(again.sections[-1].name, "Corte 1")             # one more than the highest number


class GeometryCache(unittest.TestCase):
    """Shapes kept on disk: reopening an unchanged file reads them instead of the kernel."""

    def setUp(self):
        self.doc = Document()
        obj = box_object(self.doc, (0, 0, 0), 4.5, 0.2, 2.8)
        self.wall = bim.classify(self.doc, [obj.id], catalog.BY_KEY["parede_alv_20"]).guids[0]
        frame = bim.wall_frame(self.doc, self.wall)
        self.door = bim.add_opening(self.doc, self.wall, catalog.OPENING_BY_KEY["porta_80"], frame, 1.0, -1)
        slab = box_object(self.doc, (0, 0, 2.8), 4.5, 3.0, 0.12)
        bim.classify(self.doc, [slab.id], catalog.BY_KEY["laje_12"])
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "casa.ifc")
        self.doc.save(self.path)
        self.count = sum(1 for o in self.doc.objects.values() if o.is_bim)

    def tearDown(self):
        geomcache.forget(self.path)
        self.tmp.cleanup()

    def test_reopen_reads_the_cache(self):
        key = self.doc.ifc.geometry_key()
        self.assertEqual(len(geomcache.load(self.path, key)), self.count)
        cached = Document()
        cached.open(self.path)
        self.assertEqual(cached.cache_hits, self.count)                 # nothing worked out by the kernel
        geomcache.forget(self.path)
        fresh = Document()
        fresh.open(self.path)
        self.assertEqual(fresh.cache_hits, 0)
        self.assertEqual(len(geomcache.load(self.path, key)), self.count)   # written again for next time
        for guid in (self.wall, self.door):                             # same shapes, same visible edges
            a, b = cached.get(guid).mesh, fresh.get(guid).mesh
            self.assertTrue(np.allclose(a.verts, b.verts))
            self.assertTrue(np.array_equal(a.tris, b.tris))
            self.assertTrue(np.allclose(a.normals, b.normals))         # worked out for all elements at once
            for x, y in zip(a.edge_array(), b.edge_array()):
                self.assertTrue(np.array_equal(x, y))
            self.assertEqual(a.is_closed(), b.is_closed())
        self.assertAlmostEqual(cached.get(self.wall).mesh.volume(), fresh.get(self.wall).mesh.volume())

    def test_changed_file_is_worked_out_again(self):
        key = self.doc.ifc.geometry_key()
        st = os.stat(self.path)
        os.utime(self.path, ns=(st.st_atime_ns, st.st_mtime_ns + 10**9))   # another program saved it
        self.assertEqual(geomcache.load(self.path, key), {})
        self.assertEqual(geomcache.load(self.path, key + "; other kernel"), {})
        doc2 = Document()
        doc2.open(self.path)
        self.assertEqual(doc2.cache_hits, 0)

    def test_damaged_cache_is_ignored(self):
        with open(geomcache.cache_path(self.path), "wb") as f:
            f.write(b"not a cache")
        doc2 = Document()
        doc2.open(self.path)                                            # opens normally, from the kernel
        self.assertEqual(doc2.cache_hits, 0)
        self.assertEqual(sum(1 for o in doc2.objects.values() if o.is_bim), self.count)

    def test_shown_before_the_ifc_is_read(self):
        preview = read_preview(self.path)
        self.assertIsNotNone(preview)
        doc2 = Document()
        doc2.show_preview(preview)                                     # on screen, IFC not read yet
        self.assertTrue(doc2.loading)
        self.assertEqual(doc2.storeys(), self.doc.storeys())
        self.assertEqual(doc2.ifc.spatial_tree(), self.doc.ifc.spatial_tree())
        for guid in (self.wall, self.door):
            a, b = doc2.get(guid), self.doc.get(guid)
            self.assertEqual((a.name, a.ifc_class, a.storey), (b.name, b.ifc_class, b.storey))
        with self.assertRaises(RuntimeError):
            doc2.ifc.describe(self.wall)                               # editing waits for the IFC
        meshes = {g: doc2.get(g).mesh for g in (self.wall, self.door)}
        doc2.finish_opening(read_file(self.path, preview=preview))
        self.assertFalse(doc2.loading)
        self.assertTrue(all(doc2.get(g).mesh is m for g, m in meshes.items()))   # the same, not made again
        self.assertEqual(doc2.cache_hits, self.count)
        bim.resize_wall(doc2, self.wall, height=3.0)                    # and now it can be edited
        self.assertAlmostEqual(bounds(doc2, self.wall)[1][2], 3.0)

    def test_no_preview_of_a_changed_file(self):
        st = os.stat(self.path)
        os.utime(self.path, ns=(st.st_atime_ns, st.st_mtime_ns + 10**9))
        self.assertIsNone(read_preview(self.path))

    def test_edited_and_saved_again(self):
        doc2 = Document()
        doc2.open(self.path)
        bim.delete(doc2, [self.door])                                   # the wall closes again
        doc2.save(self.path)
        doc3 = Document()
        doc3.open(self.path)
        self.assertEqual(doc3.cache_hits, self.count - 1)
        self.assertIsNone(doc3.get(self.door))
        self.assertAlmostEqual(doc3.get(self.wall).mesh.volume(), 4.5 * 0.2 * 2.8, places=6)


class ShapedColumnsIfc(unittest.TestCase):
    """0.227: a frame with a round, an L, a T and a square column — each read with its section (the analytical
    model's), all verified by EC2 (their notes telling the section), their bars made: the round one's at one distance
    from its axis with round hoops, the L's ties round each of its legs; its drawing's section a circle."""

    def test_frame(self):
        from arqbim.model import drawings
        doc = Document()
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        kinds = ("pilar_circ_30", "pilar_L_40", "pilar_T_50", "pilar_30")
        columns = [bim.add_column(doc, np.array((x, y, 0.0)), catalog.BY_KEY[k], 3.0)
                   for (x, y), k in zip(corners, kinds)]
        bim.footings_under(doc, None, catalog.BY_KEY["sapata_120"])
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            bim.add_beam(doc, np.array((*a, 3.0)), np.array((*b, 3.0)), catalog.BY_KEY["viga_20x40"], 3.0)
        bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 6.0, 4.0, catalog.BY_KEY["laje_15"])
        self.assertEqual([doc.ifc.column_section(g)[0] for g in columns], ["circle", "L", "T", "rect"])
        self.assertAlmostEqual(doc.ifc.column_section(columns[1])[1], 0.15)
        model, _loads, analysis, designs = bim.design_structure(doc)
        shapes = {m.guid: m.shape for m in model.members if m.kind == "column"}
        self.assertEqual([shapes[g] for g in columns], ["circle", "L", "T", "rect"])
        by = {e.guid: e for e in designs}
        for g in columns[:3]:
            self.assertNotEqual(by[g].design.status, "falha")
            self.assertTrue(any(n.code == "column_shape" for n in by[g].design.notes))
        bim.make_rebars(doc, designs)
        rows = {}
        for g in columns:
            for r in doc.ifc.rebars_of([g])[g]:
                rows.setdefault((g, doc.ifc._params(doc.ifc.by_guid(r))["Funcao"]), []).extend(doc.ifc.rebar_bars(r))
        centre = doc.ifc.column_box(columns[0])[0]
        radii = {round(float(np.hypot(*(np.asarray(bar)[-1][:2] - centre))), 4) for bar in rows[(columns[0], "main")]}
        self.assertEqual(len(radii), 1)
        hoop = np.asarray(rows[(columns[0], "ties")][0])
        self.assertGreater(len(hoop), 20)                                       # (a round hoop)
        ties = rows[(columns[1], "ties")]
        levels = {round(float(np.mean(np.asarray(b)[:, 2])), 2) for b in ties}
        self.assertEqual(len(ties), 2 * len(levels))
        d = drawings.of_view(doc, "rebar_cut", columns[0], "Pilar")              # (0.234: a view of its own)
        self.assertGreater(len(d.lines), 40)                                    # (its section a circle)


class FoundationsIfc(unittest.TestCase):
    """0.228: a frame on pile caps (two of 2 piles, two of 4) and a wall on a strip footing — each footing read as
    it is (its piles from its middle, their diameter; the strip's wall and its weight per metre: its volume × 15 /
    its length), the strip not taken for a column's footing; the caps designed by struts and ties (2 and 4 piles),
    the strip with its wall's weight; all their bars made."""

    def test_frame(self):
        from arqbim.core import structural as st
        doc = Document()
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        cols = [bim.add_column(doc, np.array((x, y, 0.0)), catalog.BY_KEY["pilar_30"], 3.0) for x, y in corners]
        two = bim.footings_under(doc, cols[:2], catalog.BY_KEY["bloco_2e"])
        four = bim.footings_under(doc, cols[2:], catalog.BY_KEY["bloco_4e"])
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            bim.add_beam(doc, np.array((*a, 3.0)), np.array((*b, 3.0)), catalog.BY_KEY["viga_20x40"], 3.0)
        bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 6.0, 4.0, catalog.BY_KEY["laje_15"])
        wall = bim.add_wall(doc, np.array((10.0, 0.0, 0.0)), np.array((10.0, 5.0, 0.0)),
                            catalog.BY_KEY["parede_alv_20"])
        spec = catalog.BY_KEY["sapata_corrida_50"]
        strip = bim.add_footing(doc, bim.footing_place(doc, wall, spec), spec, under=wall)
        caps = [g for g in two + four if doc.ifc.by_guid(g).is_a("IfcFooting")]
        _c, _b, footings, _p, _l = bim.structural_elements(doc)
        by = {f.guid: f for f in footings}
        self.assertEqual(sorted(len(by[g].piles) for g in caps), [2, 2, 4, 4])
        self.assertTrue(all(by[g].kind == "cap" and abs(by[g].pile_d - 0.30) < 1e-9 for g in caps))
        f = by[strip]
        self.assertEqual((f.kind, f.wall), ("strip", wall))
        self.assertAlmostEqual(f.line_load, abs(doc.get(wall).mesh.volume()) * 15.0 / 5.0, places=6)
        self.assertAlmostEqual(f.wall_t, 0.2)
        model = bim.analytical_model(doc)
        self.assertFalse(any(i.code == "footing_alone" and strip in i.guids for i in model.issues))
        self.assertEqual(len(model.supports), 4)
        _m, _l2, _a, designs = bim.design_structure(doc)
        designed = {e.guid: e for e in designs if e.kind == "footing"}
        for g in caps:
            notes = {x.code: x for x in designed[g].design.notes}
            self.assertEqual(int(notes["pile_cap"].values["n"]), len(by[g].piles))
            self.assertIn("cap_tie", notes)
            self.assertNotEqual(designed[g].design.status, "falha")
        notes = {x.code: x for x in designed[strip].design.notes}
        self.assertAlmostEqual(notes["strip_bearing"].values["q"], f.line_load + 0.5 * 0.3 * 25)
        bim.make_rebars(doc, designs)
        made = doc.ifc.rebars_of(caps + [strip])
        self.assertTrue(all(made.get(g) for g in caps + [strip]))
        self.assertIsInstance(by[strip], st.Footing)


class CurtailmentIfc(unittest.TestCase):
    """0.229: an 8 × 5 m frame of 20 × 50 beams, its slab a hall (5 kN/m²) — its long beams' moment envelope along
    them from the analysis (21 points a piece), their bars that stop told and made: bars of two lengths at the bottom
    (end to end, and shorter in the span), the shorter ones inside the beam; kept with the bars and laid again the
    same when the beam is made deeper (its zones read back)."""

    def test_frame(self):
        doc = Document()
        corners = ((0.0, 0.0), (8.0, 0.0), (8.0, 5.0), (0.0, 5.0))
        for x, y in corners:
            bim.add_column(doc, np.array((x, y, 0.0)), catalog.BY_KEY["pilar_30"], 3.0)
        bim.footings_under(doc, None, catalog.BY_KEY["sapata_120"])
        beams = [bim.add_beam(doc, np.array((*corners[k], 3.0)), np.array((*corners[(k + 1) % 4], 3.0)),
                              catalog.BY_KEY["viga_20x50"], 3.0) for k in range(4)]
        slab = bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 8.0, 5.0, catalog.BY_KEY["laje_15"])
        bim.set_slab_use(doc, [slab], "C3")
        model, _loads, analysis, designs = bim.design_structure(doc)
        member = next(m for m in model.members if m.guid == beams[0])
        top, low = analysis.envelopes[member.id]
        self.assertEqual(len(top), 21)
        self.assertTrue(all(a >= b - 1e-9 for a, b in zip(top, low)))
        long_beam = next(e for e in designs if e.guid == beams[0])
        self.assertTrue(any(n.code == "curtail" for n in long_beam.design.notes))
        self.assertTrue(long_beam.design.bottom_zones)
        bim.make_rebars(doc, designs)
        bottoms = [doc.ifc.by_guid(g) for g in doc.ifc.rebars_of([beams[0]])[beams[0]]
                   if doc.ifc._params(doc.ifc.by_guid(g))["Funcao"] == "bottom"]
        lengths = sorted(round(b.BarLength) for b in bottoms)
        self.assertEqual(len(lengths), 2)
        self.assertLess(lengths[0], 8000 - 1000)
        kept = doc.ifc.rebar_design(beams[0])
        self.assertTrue(kept["bottom_zones"])
        before = len(bottoms)
        bim.set_type(doc, beams[0], catalog.BY_KEY["viga_20x40"])          # (laid again from its design)
        again = [g for g in doc.ifc.rebars_of([beams[0]])[beams[0]]
                 if doc.ifc._params(doc.ifc.by_guid(g))["Funcao"] == "bottom"]
        self.assertEqual(len(again), before)


class SplicesIfc(unittest.TestCase):
    """0.230: a 15 m wall on a strip footing — its bars along it (15 m) spliced in the model: none longer than 12 m,
    the pieces lapped (their steel more than the bars' by the laps); its bars across it as they were."""

    def test_strip(self):
        from arqbim.core import rebar as rb
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((15.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        spec = catalog.BY_KEY["sapata_corrida_50"]
        strip = bim.add_footing(doc, bim.footing_place(doc, wall, spec), spec, under=wall)
        _m, _l, _a, designs = bim.design_structure(doc)
        bim.make_rebars(doc, [e for e in designs if e.guid == strip])
        rows = {}
        for g in doc.ifc.rebars_of([strip])[strip]:
            e = doc.ifc.by_guid(g)
            rows.setdefault(doc.ifc._params(e)["Funcao"], []).extend(doc.ifc.rebar_bars(g))
        along = rows["mesh_x"]
        self.assertTrue(all(rb.BarSet.length_of(b) <= rb.STOCK + 1e-6 for b in along))
        self.assertGreater(sum(rb.BarSet.length_of(b) for b in along), 15.0 * len(along) / 2 * 0.9)
        self.assertTrue(all(rb.BarSet.length_of(b) < 1.0 for b in rows["mesh_y"]))


class TypicalRebarsIfc(unittest.TestCase):
    """0.231: a three-storey frame, its two upper floors typical — each column, beam and slab there and its equal on
    the other floor given the same reinforcement, the more stressed one's (the lower floor's columns: they carry
    more), each told so; the ground floor's members their own."""

    def test_frame(self):
        doc = Document()
        ground = doc.ifc.storeys()[0][0]
        first = bim.add_storey(doc, "Piso 1", 3.0)
        second = bim.add_storey(doc, "Piso 2", 6.0)
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        for storey, z in ((ground, 0.0), (first, 3.0)):
            for x, y in corners:
                bim.add_column(doc, np.array((x, y, z)), catalog.BY_KEY["pilar_30"], 3.0, storey=storey)
            for k in range(4):
                a, b = corners[k], corners[(k + 1) % 4]
                bim.add_beam(doc, np.array((*a, z + 3.0)), np.array((*b, z + 3.0)), catalog.BY_KEY["viga_20x40"],
                             z + 3.0, storey=storey)
            bim.add_slab(doc, np.array((0.0, 0.0, z + 3.0)), 6.0, 4.0, catalog.BY_KEY["laje_15"], storey=storey)
        doc.set_active_storey(ground)
        bim.footings_under(doc, None, catalog.BY_KEY["sapata_120"])
        self.assertIsNotNone(bim.make_typical(doc, [first, second], first, "Piso tipo"))
        _m, _l, analysis, designs = bim.design_structure(doc)
        self.assertEqual(analysis.error, "")
        by = {e.guid: e for e in designs}
        typical = [e for e in designs if any(n.code == "typical" for n in e.design.notes)]
        self.assertTrue(typical)
        pairs = 0
        for e in typical:
            others = [g for g in doc.ifc.counterparts(e.guid) if g in by]
            for g in others:
                self.assertEqual(by[g].design.bars, e.design.bars)
                self.assertEqual(by[g].design.bottom, e.design.bottom)
                self.assertEqual(by[g].design.mesh_x, e.design.mesh_x)
                pairs += 1
        self.assertGreater(pairs, 0)
        lower = [o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcColumn"
                 and o.storey == ground]
        self.assertTrue(all(not any(n.code == "typical" for n in by[g].design.notes) for g in lower))


class QuickReads(unittest.TestCase):
    """0.225: what made each edit heavy, made light without changing a result — an element's kind and its
    placement read straight (the same as IfcOpenShell's get_psets / get_local_placement, a wall turned on an upper
    storey and its door too); the storeys kept inside an edit, but a storey made in it seen at once; the walls'
    axes kept with the document, each worked out again when it changes (made longer, removed, undone); the
    searches for what follows a slab, a roof or a beam ask nothing when none changed."""

    def _model(self):
        doc = Document()
        upper = bim.add_storey(doc, "Piso 1", 3.0)
        a = bim.add_wall(doc, np.array((0.0, 0.0, 3.0)), np.array((4.0, 3.0, 3.0)), catalog.BY_KEY["parede_alv_20"],
                         storey=upper)
        b = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((0.0, 5.0, 0.0)), catalog.BY_KEY["parede_alv_15"])
        door = bim.add_opening(doc, a, catalog.OPENING_BY_KEY["porta_90"], bim.wall_frame(doc, a), 1.5, -1)
        slab = bim.add_slab(doc, np.array((0.0, 0.0, 3.0)), 4.0, 3.0, catalog.BY_KEY["laje_15"])
        return doc, upper, a, b, door, slab

    def test_same_reads(self):
        import ifcopenshell.util.placement as up
        from arqbim.ifc.edit import PARAM_PSET
        doc, upper, a, b, door, slab = self._model()
        ifc = doc.ifc
        for g in (a, b, door, slab, upper):
            e = ifc.by_guid(g)
            self.assertEqual(ifc.kind_of(g), ue.get_psets(e).get(PARAM_PSET, {}).get("Elemento"))
            want = up.get_local_placement(e.ObjectPlacement)
            self.assertTrue(np.allclose(ifc._local_placement(e.ObjectPlacement), want, atol=1e-9), g)
            with ifc.remembering():                         # (kept: the same)
                self.assertTrue(np.allclose(ifc._local_placement(e.ObjectPlacement), want, atol=1e-9))
                self.assertTrue(np.allclose(ifc._local_placement(e.ObjectPlacement), want, atol=1e-9))
        q = ue.get_psets(ifc.by_guid(a))["Qto_WallBaseQuantities"]
        s = ifc.unit_scale
        self.assertEqual(ifc.wall_params(a), (q["Length"] * s, q["Height"] * s, q["Width"] * s))
        self.assertEqual(ifc.kind_of(a), "wall")

    def test_storeys_in_an_edit(self):
        doc, upper, *_rest = self._model()
        ifc = doc.ifc
        before = ifc.storeys()
        with ifc.remembering():
            self.assertEqual(ifc.storeys(), before)
            ifc.begin()
            made = ifc.add_storey("Piso 2", 6.0).GlobalId     # (made inside: seen at once)
            self.assertIn(made, [g for g, _n, _z in ifc.storeys()])
            ifc.end()
            self.assertEqual(len(ifc.storeys()), len(before) + 1)
            doc.ifc.undo()                                  # (undone: gone again)
            self.assertEqual(ifc.storeys(), before)

    def test_wall_axes_follow(self):
        doc, upper, a, b, door, slab = self._model()
        axes = {g: (s, e) for g, s, e, _t in bim.wall_axes(doc)}
        self.assertEqual(set(axes), {a, b})
        bim.resize_wall(doc, b, at_end=1.0)                 # (5 m long: 6)
        s, e = next((s, e) for g, s, e, _t in bim.wall_axes(doc) if g == b)
        self.assertAlmostEqual(float(np.linalg.norm(e - s)), 6.0, places=6)
        bim.delete(doc, [b])
        self.assertEqual({g for g, *_r in bim.wall_axes(doc)}, {a})
        doc.undo()
        self.assertEqual({g for g, *_r in bim.wall_axes(doc)}, {a, b})

    def test_nothing_asked(self):
        doc, *_rest = self._model()
        ifc = doc.ifc
        reads = []
        original = ifc._params
        ifc._params = lambda e: reads.append(e) or original(e)
        try:
            self.assertEqual(ifc.slab_tops([]), [])
            self.assertEqual(ifc.roof_tops([]), [])
            self.assertEqual(ifc.walls_of([]), {})
            self.assertEqual(ifc.slabs_of([]), {})
            self.assertEqual(ifc.beams_of([]), {})
            self.assertEqual(ifc.systems_of([]), {})
        finally:
            ifc._params = original
        self.assertEqual(reads, [])


class ProjectPatterns(unittest.TestCase):
    """0.318 — the project's own fill patterns: a simple one (crossed lines, model) and one of its own families (a
    shifted, dashed one, drafting) kept in the IFC as fill area styles of their own, read back the same; a material's
    cut with one of them, after reopening the file; one deleted, undone; valid IFC4."""

    def tearDown(self):
        from arqbim.core import patterns as core_patterns
        core_patterns.set_project(())
        catalog.set_project(())

    def test_patterns(self):
        from arqbim.core import patterns as core_patterns
        from arqbim.model import project_types
        doc = Document()
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        grid = core_patterns.simple("p:grelha", "Grelha 40", True, 0.0, 0.40, crossed=True)
        own = core_patterns.Pattern("p:juntas", False, ((30.0, 0.5, 0.25, 1.2, 2.0, (3.0, -1.0, 0.0, -1.0)),
                                                        (120.0, 0.0, 0.0, 0.0, -1.5, ())), "Juntas oblíquas")
        self.assertEqual(core_patterns.shape_of(grid), ("cross", 0.0, 0.40))
        self.assertEqual(core_patterns.shape_of(own)[0], "custom")
        bim.save_pattern(doc, grid)
        bim.save_pattern(doc, own)
        read = {p.key: p for p in doc.ifc.patterns()}
        self.assertEqual(read["p:grelha"], grid)
        self.assertEqual(read["p:juntas"], own)
        self.assertIn("p:juntas", core_patterns.drafting_keys())
        self.assertIn("p:grelha", core_patterns.model_keys())
        block = catalog.MATERIALS["bloco"]
        bim.save_material(doc, dataclasses.replace(block, cut_fg=("p:juntas", "#202020"),
                                                   surface_fg=("p:grelha", "#808080")), block)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "padroes.ifc")
            doc.save(path)
            core_patterns.set_project(())                       # (as a program just opened)
            again = Document()
            again.open(path)
            core_patterns.set_project(again.ifc.patterns())
            self.assertEqual({p.key: p for p in again.ifc.patterns()}, read)
            mine = {s.key: s for s in project_types.materials(again.ifc)}["bloco"]
            self.assertEqual((mine.cut_fg, mine.surface_fg), (("p:juntas", "#202020"), ("p:grelha", "#808080")))
            again.modified = False
        self.assertTrue(bim.delete_pattern(doc, "p:juntas"))
        self.assertNotIn("p:juntas", {p.key for p in doc.ifc.patterns()})
        self.assertFalse(bim.delete_pattern(doc, "diagonal"))  # (the program's: never)
        doc.undo()
        self.assertIn("p:juntas", {p.key for p in doc.ifc.patterns()})
        doc.modified = False


class ViewStyles(unittest.TestCase):
    """0.315 — view styles: the program's (the 3D view's four looks and two more) and the project's, made, changed,
    deleted (one undo step; the views and templates given a deleted one back to the usual), kept beside the IFC and
    read back; given to a view (a drawing's: none until given) or by its template. And each triangle's material of
    a wall: its plaster outside, its block where its top is cut."""

    def test_styles(self):
        from arqbim.model import view_styles as vs
        from arqbim.model.view_templates import ViewTemplate
        doc = Document()
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        self.assertEqual(set(vs.BUILTIN), {"shaded", "hidden", "wire", "xray", "consistent", "realistic"})
        self.assertEqual(doc.view_style("nada"), vs.BUILTIN["shaded"])
        mine = vs.new_from(vs.BUILTIN["realistic"], "Apresentação")
        self.assertFalse(mine.builtin)
        self.assertTrue(mine.shadows and mine.patterns and mine.colours == "material")
        mine = dataclasses.replace(mine, faces="consistent", edge_width=2.0, cut="solid", sun_azimuth=250.0,
                                   sun_altitude=30.0)                      # (0.316: its sun, kept too)
        self.assertEqual(vs.from_dict({"name": "X", "sun_altitude": 95, "sun_azimuth": 370}).sun_altitude, 89.0)
        self.assertEqual(vs.from_dict({"name": "X", "sun_azimuth": 370}).sun_azimuth, 10.0)
        doc.set_view_styles([mine])
        self.assertEqual(doc.view_style(mine.uid), mine)
        plan = ("plan", doc.active_storey)
        self.assertIsNone(doc.view_settings(plan).drawn_style)              # (a drawing: none until given)
        doc.set_view_props(("3d",), style=mine.uid)
        doc.set_view_props(plan, style="consistent")
        self.assertEqual(doc.view_style_of(("3d",)), mine)
        self.assertEqual(doc.view_settings(plan).drawn_style, "consistent")
        tpl = ViewTemplate("Plantas", style=mine.uid)
        doc.set_templates([tpl])
        doc.assign_template(plan, tpl.uid)
        self.assertEqual(doc.view_settings(plan).drawn_style, mine.uid)      # (its template's)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "estilos.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            self.assertEqual(again.view_styles, [mine])
            self.assertEqual(again.view_style_of(("3d",)), mine)
            self.assertEqual(again.templates[0].style, mine.uid)
            again.modified = False
        doc.set_view_styles([])                                              # deleted: the views' back to usual
        self.assertNotIn("style", doc.view_props.get(("3d",), {}))
        self.assertIsNone(doc.templates[0].style)
        self.assertEqual(doc.view_style_of(("3d",)), vs.BUILTIN["shaded"])
        doc.undo()
        self.assertEqual(doc.view_style_of(("3d",)), mine)
        self.assertEqual(doc.templates[0].style, mine.uid)
        self.assertIsNone(vs.from_dict({"name": ""}))
        self.assertEqual(vs.from_dict({"name": "X", "faces": "?", "cut": "empty", "uid": "shaded"}).faces, "shaded")
        self.assertNotEqual(vs.from_dict({"name": "X", "uid": "shaded"}).uid, "shaded")   # (never a built-in's)
        doc.modified = False

    def test_face_materials(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        mesh = doc.get(wall).mesh
        tris, owner = mesh.triangulate()
        centres = mesh.verts[tris].mean(axis=1)
        normals = mesh.normals[owner]
        names, index = doc.ifc.face_materials(wall, centres, normals)
        self.assertEqual(set(names), {"Reboco", "Bloco cerâmico"})
        side = np.abs(normals[:, 1]) > 0.9                                   # (its two long faces: plaster)
        self.assertTrue(np.all(np.array(names)[index[side]] == "Reboco"))
        top = (normals[:, 2] > 0.9) & (np.abs(centres[:, 1]) < 0.05)        # (its top, across its middle: block)
        if top.any():
            self.assertTrue(np.all(np.array(names)[index[top]] == "Bloco cerâmico"))
        column = bim.add_column(doc, np.array((8.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        m = doc.get(column).mesh
        t2, o2 = m.triangulate()
        names2, index2 = doc.ifc.face_materials(column, m.verts[t2].mean(axis=1), m.normals[o2])
        self.assertEqual((names2, set(index2.tolist())), (["Concreto"], {0}))
        doc.modified = False


class DrawingAsRevit(unittest.TestCase):
    """0.447 — drawing as Revit's (the owner's pictures): a wall being drawn measured to the parallel walls beside it;
    a wall chosen alone with its flip arrow out of its outside face; a temporary dimension made permanent, hung on the
    walls it measures (it follows them)."""

    @staticmethod
    def _host(doc, viewport=None):
        from types import SimpleNamespace
        return SimpleNamespace(doc=doc, viewport=viewport, dim_faces=False, message=lambda *a, **k: None,
                               set_hint=lambda *a: None, set_vcb=lambda *a: None)

    def test_parallel_walls_while_drawing(self):
        from arqbim.tools.bim_draw import WallTool
        doc = Document()
        try:
            w20 = catalog.BY_KEY["parede_alv_20"]
            bim.add_wall(doc, (0.0, 0.0, 0.0), (0.0, 5.0, 0.0), w20)            # left, 3 m from the one drawn
            bim.add_wall(doc, (4.0, 0.0, 0.0), (4.0, 5.0, 0.0), w20)            # right, 1 m
            bim.add_wall(doc, (40.0, 0.0, 0.0), (40.0, 5.0, 0.0), w20)          # far away: not looked at
            tool = WallTool(self._host(doc))
            dims = tool._parallel_dims(np.array((3.0, 1.0, 0.0)), np.array((3.0, 4.0, 0.0)))
            self.assertEqual(sorted(round(d.value, 4) for d in dims), [1.0, 3.0])        # (axis to axis)
            self.assertTrue(all(d.kind == "relation" for d in dims))
            tool.host.dim_faces = True
            dims = tool._parallel_dims(np.array((3.0, 1.0, 0.0)), np.array((3.0, 4.0, 0.0)))
            self.assertEqual(sorted(round(d.value, 4) for d in dims), [0.8, 2.8])        # (face to face)
        finally:
            doc.modified = False

    def test_wall_flip_arrow(self):
        from arqbim.tools.select import wall_flips
        doc = Document()
        try:
            wall = bim.add_wall(doc, (0.0, 0.0, 0.0), (4.0, 0.0, 0.0), catalog.BY_KEY["parede_alv_20"])
            guid, flips, segs = wall_flips(doc, {wall})
            what, middle, a, b = flips[0]
            self.assertEqual((guid, what), (wall, "wall"))
            self.assertAlmostEqual(float(middle[0]), 2.0)                       # (at the wall's middle…)
            self.assertGreater(abs(float(a[1])), 0.1)                           # (…out of its face)
            self.assertTrue(len(segs) >= 3)
            side = np.sign(float(middle[1]))
            bim.flip_walls(doc, [wall])
            self.assertEqual(np.sign(float(wall_flips(doc, {wall})[1][0][1][1])), -side)   # (flipped: the other face)
            self.assertIsNone(wall_flips(doc, set()))
        finally:
            doc.modified = False

    def test_direction_snap(self):
        """0.448 — the owner: «snap a 0, 45, 90 grau… se desenhar uma linha ou construir uma parede a 30º, quando
        desenhar outra parede inclinada na mesma direção, ele faz o snap de paralelo»."""
        from arqbim.core.mesh import PolyMesh
        from arqbim.tools.base import direction_snap
        from arqbim.tools.bim_draw import WallTool
        doc = Document()
        try:
            polar = lambda p, deg, r: np.asarray(p, dtype=float) + r * np.array(           # noqa: E731
                (math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0.0))
            self.assertEqual(direction_snap(doc, np.zeros(3), polar((0, 0, 0), 44.0, 3.0))[1], "angle")    # 45°
            q = direction_snap(doc, np.zeros(3), polar((0, 0, 0), 91.5, 3.0))
            self.assertEqual(q[1], "axis_y")
            self.assertAlmostEqual(float(q[0][0]), 0.0, places=9)                                       # upright
            self.assertIsNone(direction_snap(doc, np.zeros(3), polar((0, 0, 0), 30.0, 3.0)))           # (free)
            wall = bim.add_wall(doc, (0.0, 0.0, 0.0), polar((0, 0, 0), 30.0, 4.0), catalog.BY_KEY["parede_alv_20"])
            start = np.array((1.0, 3.0, 0.0))
            q = direction_snap(doc, start, polar(start, 31.8, 2.5))                    # another wall, nearly so
            self.assertEqual(q[1], "parallel")
            self.assertAlmostEqual(q[3], 30.0, places=6)                               # exactly its way
            self.assertIsNotNone(q[2])                                                 # (the wall lit)
            self.assertIsNone(direction_snap(doc, start, polar(start, 34.0, 2.5)))     # (too far from it)
            line = SketchObject("l", I4, PolyMesh([(10.0, 0.0, 0.0), tuple(polar((10, 0, 0), 62.0, 3.0))],
                                                  lines=[(0, 1)]))
            doc.execute(AddObject(line))                                               # a loose line at 62°
            q = direction_snap(doc, np.array((12.0, 0.0, 0.0)), polar((12, 0, 0), 241.0, 2.0))   # the other way
            self.assertEqual(q[1], "parallel")
            self.assertAlmostEqual(q[3], 242.0, places=6)
            tool = WallTool(self._host(doc))                   # the Wall tool: Shift lets the direction go
            tool._start = start.copy()
            tool._preview = lambda *a, **k: None
            tool._wall_point = lambda x, y, level, modifiers=(): (polar(start, 31.8, 2.5), None, False)
            tool.pointer_move(0, 0, ())
            self.assertAlmostEqual(math.degrees(math.atan2(*(tool._end - start)[1::-1])), 30.0, places=6)
            tool.pointer_move(0, 0, ("Shift",))
            self.assertAlmostEqual(math.degrees(math.atan2(*(tool._end - start)[1::-1])), 31.8, places=6)
        finally:
            doc.modified = False

    def test_pick_lines_and_offset(self):
        """0.451 — Revit's «Pick Lines» and «Offset» (the owner: «criar por seleção… criar com offset a x distância»):
        a wall on the line picked, moved by the offset to the mouse's side — its body on that side when drawn by a
        face —; a wall drawn point by point that far to the left of its way."""
        from types import SimpleNamespace
        from arqbim.tools import pick_lines
        from arqbim.tools.bim_draw import WallTool
        doc = Document()
        real = pick_lines.edge_at
        try:
            edge = (np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)))
            vp = SimpleNamespace(ray=lambda x, y: (np.array((2.0, 1.0, 10.0)), np.array((0.0, 0.0, -1.0))),
                                 clear_overlays=lambda: None, show_tip=lambda *a: None, plan=False,
                                 tracking=SimpleNamespace(clear=lambda: None))
            tool = WallTool(self._host(doc, vp))
            pick_lines.edge_at = lambda viewport, document, x, y: edge          # (the line under the mouse)
            tool.shape, tool.offset = "pick", 0.5
            a, b, _e = tool._picked_wall(0, 0)                                   # (the mouse at y = 1: its left)
            self.assertAlmostEqual(float(a[1]), 0.5)
            self.assertAlmostEqual(float(np.linalg.norm(b - a)), 4.0)
            tool.reference = "right"                                             # by its right face: the body left
            a, b, _e = tool._picked_wall(0, 0)
            self.assertAlmostEqual(float(a[1]), 0.6)                             # (0,5 + 0,20 / 2)
            tool._pick_down(0, 0)
            walls = [g for g, _s, _e2, _t in bim.wall_axes(doc)]
            self.assertEqual(len(walls), 1)
            s, e, _th = doc.ifc.wall_axis(walls[0])
            self.assertAlmostEqual(float(s[1]), 0.6, places=6)
            self.assertAlmostEqual(float(np.linalg.norm(e - s)), 4.0, places=6)
            tool.reference, tool.offset = "axis", 0.3                            # drawn point by point
            a, b = tool._drawn_axis(np.array((0.0, 2.0, 0.0)), np.array((0.0, 6.0, 0.0)))
            self.assertAlmostEqual(float(a[0]), -0.3)                            # (left of going up: −x)
            self.assertEqual(pick_lines.side_of((0, 0, 0), (4, 0, 0), (1, -1, 0)), -1.0)
        finally:
            pick_lines.edge_at = real
            doc.modified = False

    def test_fillet_arc(self):
        """0.452 — Revit's «Fillet Arc» (the owner: «o arco por seleção de 2 elementos»): two walls in an L, a radius
        of 1 m — both cut back 1 m from the corner, a curved wall between them, tangent, joined to both; the radius
        from the mouse along the bisector; too big a radius refused."""
        from arqbim.core.fillet import fillet
        f = fillet(((0, 0), (5, 0)), (2, 0), ((5, -1), (5, 4)), (5, 2), radius=1.0)
        np.testing.assert_allclose(f.cross, (5, 0))
        self.assertEqual(f.ends, ("end", "start"))
        np.testing.assert_allclose(f.tangents[0], (4, 0), atol=1e-9)
        np.testing.assert_allclose(f.tangents[1], (5, 1), atol=1e-9)
        np.testing.assert_allclose(f.centre, (4, 1), atol=1e-9)
        self.assertAlmostEqual(abs(math.degrees(f.sweep)), 90.0, places=6)
        g = fillet(((0, 0), (5, 0)), (2, 0), ((5, -1), (5, 4)), (5, 2), through=(5 - 0.3, 0.3))   # (by the mouse)
        self.assertAlmostEqual(g.radius, 0.3 * 2 ** 0.5 / (2 ** 0.5 - 1), places=6)
        self.assertIsNone(fillet(((0, 0), (5, 0)), (2, 0), ((0, 1), (5, 1)), (2, 1), radius=1.0))   # (parallel)
        doc = Document()
        try:
            w20 = catalog.BY_KEY["parede_alv_20"]
            a = bim.add_wall(doc, (0.0, 0.0, 0.0), (5.0, 0.0, 0.0), w20)
            b = bim.add_wall(doc, (5.0, 0.0, 0.0), (5.0, 4.0, 0.0), w20, prev=(a, np.array((1.0, 0.0, 0.0))))
            arc = bim.fillet_walls(doc, a, (2.0, 0.0), b, (5.0, 2.0), 1.0, w20)
            sa, ea, _t = doc.ifc.wall_axis(a)
            sb, eb, _t = doc.ifc.wall_axis(b)
            self.assertAlmostEqual(float(ea[0]), 4.0, places=6)                 # (cut back to the arc)
            self.assertAlmostEqual(float(sb[1]), 1.0, places=6)
            self.assertEqual(doc.ifc.kind_of(arc), "curved_wall")
            centre, radius, _start, sweep, _h, _th = doc.ifc.curved_wall_params(arc)
            self.assertAlmostEqual(radius, 1.0, places=6)
            np.testing.assert_allclose(np.asarray(centre)[:2], (4.0, 1.0), atol=1e-6)
            self.assertAlmostEqual(abs(math.degrees(sweep)), 90.0, places=4)
            # (its ends on theirs: tangent, one band — no joint recorded, there is no corner to clean up)
            np.testing.assert_allclose(doc.ifc.joint_end(arc, "start").point[:2], ea[:2], atol=1e-6)
            np.testing.assert_allclose(doc.ifc.joint_end(arc, "end").point[:2], sb[:2], atol=1e-6)
            with self.assertRaises(Exception):                                  # (a radius past a wall's end)
                bim.fillet_walls(doc, a, (2.0, 0.0), b, (5.0, 2.0), 9.0, w20)
        finally:
            doc.modified = False

    def test_fillet_lines(self):
        """0.452 — the fillet arc between two loose lines of one chain (an L): each trimmed to its tangent point (the
        corner they shared split); one undo step. 0.455 (the owner: «o arco não é um arco, mas um monte de segmentos,
        não dá pra selecionar o raio inteiro para ajustar o raio como no revit»): the arc an arc of its own, picked
        whole; its radius changed — the two lines trimmed / stretched, the arc still tangent to both."""
        from arqbim.core import curves
        from arqbim.core.mesh import PolyMesh
        from arqbim.model import line_edit
        doc = Document()
        try:
            chain = SketchObject("l", I4, PolyMesh([(0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (4.0, 3.0, 0.0)],
                                                   lines=[(0, 1), (1, 2)]))
            doc.execute(AddObject(chain))
            first = (chain.id, *line_edit.segment_at(doc, chain.id, (0, 0, 0), (4, 0, 0)))
            second = (chain.id, *line_edit.segment_at(doc, chain.id, (4, 0, 0), (4, 3, 0)))
            _f, arc_id = line_edit.fillet_lines(doc, first, (2.0, 0.0, 0.0), second, (4.0, 2.0, 0.0), 1.0)
            segs = [(np.round(a, 6), np.round(b, 6)) for _i, _j, a, b in line_edit.segments(doc.get(chain.id))]
            ends = {tuple(p) for s in segs for p in s}
            self.assertEqual(len(segs), 2)                                     # (the lines: still two)
            self.assertIn((3.0, 0.0, 0.0), ends)                               # (trimmed back 1 m)
            self.assertIn((4.0, 1.0, 0.0), ends)
            self.assertNotIn((4.0, 0.0, 0.0), ends)                            # (the corner no longer used)
            arc = doc.get(arc_id)                                              # the arc: one, an arc's data
            self.assertEqual(arc.curve["kind"], "arc")
            self.assertAlmostEqual(curves.arc_radius(arc.curve), 1.0, places=9)
            np.testing.assert_allclose(arc.curve["centre"][:2], (3.0, 1.0), atol=1e-9)
            pts = [np.asarray(p) for p in arc.mesh.verts]
            np.testing.assert_allclose(pts[0][:2], (3.0, 0.0), atol=1e-9)
            np.testing.assert_allclose(pts[-1][:2], (4.0, 1.0), atol=1e-9)
            self.assertIsNotNone(line_edit.tangent_lines(doc, arc_id))         # (a fillet's: a line along each end)
            self.assertTrue(line_edit.fillet_radius(doc, arc_id, 0.5))         # its radius: 0,5 — still tangent
            arc = doc.get(arc_id)
            self.assertAlmostEqual(curves.arc_radius(arc.curve), 0.5, places=9)
            np.testing.assert_allclose(arc.curve["centre"][:2], (3.5, 0.5), atol=1e-9)
            ends = {tuple(np.round(p, 6)) for s in line_edit.segments(doc.get(chain.id)) for p in s[2:]}
            self.assertEqual(ends, {(0.0, 0.0, 0.0), (3.5, 0.0, 0.0), (4.0, 0.5, 0.0), (4.0, 3.0, 0.0)})
            with self.assertRaises(line_edit.LineRefused):                     # (past the lines' far ends)
                line_edit.fillet_radius(doc, arc_id, 5.0)
            doc.undo()                                                         # (the radius: one step)
            self.assertAlmostEqual(curves.arc_radius(doc.get(arc_id).curve), 1.0, places=9)
            doc.undo()                                                         # (the fillet: one step)
            self.assertIsNone(doc.get(arc_id))
            self.assertEqual(len(doc.get(chain.id).mesh.lines), 2)
        finally:
            doc.modified = False

    def test_fillet_polygon_and_radius_dimension(self):
        """0.455 — the owner: «tentei fazer isso no polígono, mas não funcionou»: a polygon's corner (a sketch's face)
        rounded, the face whole, going round either way; two sides that make no corner refused. An arc picked alone
        (Revit's): its radius as a temporary dimension; typed over — a fillet's still tangent to its lines."""
        from arqbim.core import curves
        from arqbim.core.mesh import PolyMesh
        from arqbim.model import line_edit
        from arqbim.tools.select import apply_dim, arc_radius_dims
        doc = Document()
        try:
            for corners in ([(0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (4.0, 3.0, 0.0), (0.0, 3.0, 0.0)],
                            [(0.0, 3.0, 0.0), (4.0, 3.0, 0.0), (4.0, 0.0, 0.0), (0.0, 0.0, 0.0)]):   # (both ways)
                face = SketchObject("f", I4, PolyMesh(corners, [[0, 1, 2, 3]]))
                doc.execute(AddObject(face))
                obj = doc.get(face.id)
                first = (face.id, *line_edit.face_edge_at(obj, (2.0, 0.0, 0.0))[0])
                second = (face.id, *line_edit.face_edge_at(obj, (4.0, 1.5, 0.0))[0])
                line_edit.fillet_face(doc, first, (2.0, 0.0, 0.0), second, (4.0, 1.5, 0.0), 1.0)
                obj = doc.get(face.id)
                self.assertEqual(len(obj.mesh.faces), 1)
                ring = [tuple(np.round(obj.mesh.verts[k][:2], 6) + 0.0) for k in obj.mesh.faces[0]]
                self.assertIn((3.0, 0.0), ring)
                self.assertIn((4.0, 1.0), ring)
                self.assertNotIn((4.0, 0.0), ring)
                self.assertAlmostEqual(obj.mesh.face_area(0), 12.0 - (1.0 - math.pi / 4), places=2)
                from shapely.geometry import Polygon
                self.assertTrue(Polygon(ring).is_valid)                       # (in order: no crossing)
                with self.assertRaises(line_edit.LineRefused):                # (opposite sides: no corner)
                    third = (face.id, *line_edit.face_edge_at(obj, (2.0, 3.0, 0.0))[0])
                    first = (face.id, *line_edit.face_edge_at(obj, (1.0, 0.0, 0.0))[0])
                    line_edit.fillet_face(doc, first, (1.0, 0.0, 0.0), third, (2.0, 3.0, 0.0), 0.5)
                doc.undo()
                self.assertEqual(len(doc.get(face.id).mesh.faces[0]), 4)       # (one step)
                doc.undo()
            chain = SketchObject("l", I4, PolyMesh([(0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (4.0, 3.0, 0.0)],
                                                   lines=[(0, 1), (1, 2)]))
            doc.execute(AddObject(chain))
            first = (chain.id, *line_edit.segment_at(doc, chain.id, (0, 0, 0), (4, 0, 0)))
            second = (chain.id, *line_edit.segment_at(doc, chain.id, (4, 0, 0), (4, 3, 0)))
            _f, arc_id = line_edit.fillet_lines(doc, first, (2.0, 0.0, 0.0), second, (4.0, 2.0, 0.0), 1.0)
            dims = arc_radius_dims(doc.get(arc_id))
            self.assertEqual(len(dims), 1)
            self.assertAlmostEqual(dims[0].value, 1.0, places=9)
            apply_dim(doc, dims[0], 0.5)
            self.assertAlmostEqual(curves.arc_radius(doc.get(arc_id).curve), 0.5, places=9)
            ends = {tuple(np.round(p, 6)) for s in line_edit.segments(doc.get(chain.id)) for p in s[2:]}
            self.assertIn((3.5, 0.0, 0.0), ends)                                # (the lines followed: tangent)
            free = SketchObject("a", I4, PolyMesh([(10.0, 0.0, 0.0)], lines=[]),
                                curve=curves.arc_curve((10.0, 0.0, 0.0), (0, 0, 1), (12.0, 0.0, 0.0), 90.0))
            from arqbim.model import curve_edit
            doc.execute(AddObject(curve_edit.remade(free, free.curve)))
            dims = arc_radius_dims(doc.get(free.id))
            apply_dim(doc, dims[0], 3.0)                                          # (an arc alone: about its centre)
            self.assertAlmostEqual(curves.arc_radius(doc.get(free.id).curve), 3.0, places=9)
        finally:
            doc.modified = False

    def test_fillet_drawn_in_a_view(self):
        """0.455 — the owner: «isso também deve ser colocado na região, máscara etc»: a region's (a mask's) corner
        rounded — a true arc, kept as the side's bulge: drawn as an arc, the same when moved or turned —; a
        rectangle's corner (a region with no hatch now); a polyline's; two sides that make no corner, a polyline's
        open end refused; two lines: trimmed, an arc of their own between them."""
        from arqbim.model import annotations as notes2d
        o, u, v = np.zeros(3), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
        view = ("plan", "s")
        pts = lambda *ps: [np.array(p, dtype=float) for p in ps]                      # noqa: E731
        region = notes2d.Annotation(view, "region", pts((0, 0, 0), (4, 0, 0), (4, 3, 0), (0, 3, 0)), hatch="mask")
        kind, new, bulges = notes2d.corner_fillet(region, 0, (2.0, 0.0), 1, (4.0, 1.5), 1.0, o, u, v)
        self.assertEqual((kind, len(new)), ("region", 5))
        self.assertAlmostEqual(bulges[1], math.tan(math.pi / 8), places=9)             # (a quarter turn)
        np.testing.assert_allclose([p[:2] for p in new[1:3]], [(3.0, 0.0), (4.0, 1.0)], atol=1e-9)
        region.points, region.extra = new, {"bulges": bulges}
        quarter = 12.0 - (1.0 - math.pi / 4)
        self.assertAlmostEqual(notes2d.area(region, o, u, v), quarter, places=2)
        ring = notes2d.shape(region, o, u, v)[0][0]
        on_arc = [q for q in ring if q[0] > 3.0 + 1e-9 and q[1] < 1.0 - 1e-9]
        self.assertTrue(on_arc and all(abs(float(np.linalg.norm(q - (3.0, 1.0))) - 1.0) < 1e-6 for q in on_arc))
        moved = notes2d.moved_copy(region, (10.0, 5.0, 0.0))                           # (moved: the same arc)
        self.assertAlmostEqual(notes2d.area(moved, o, u, v), quarter, places=2)
        region.points = notes2d.rotated_points(region.points, np.zeros(3), np.array((0, 0, 1.0)), 30.0)
        self.assertAlmostEqual(notes2d.area(region, o, u, v), quarter, places=2)       # (turned: the same)
        self.assertEqual(notes2d.from_dict(notes2d.to_dict(region), np.zeros(3)).extra["bulges"], bulges)
        with self.assertRaises(ValueError):                                            # (opposite sides)
            notes2d.corner_fillet(region, 0, (2.0, 0.0), 2, (2.0, 3.0), 0.5, o, u, v)
        rect = notes2d.Annotation(view, "rectangle", pts((0, 0, 0), (4, 3, 0)))
        kind, new, bulges = notes2d.corner_fillet(rect, 1, (4.0, 1.5), 2, (2.0, 3.0), 0.5, o, u, v)
        self.assertEqual((kind, len(new), len(bulges)), ("region", 5, 5))
        poly = notes2d.Annotation(view, "polyline", pts((0, 0, 0), (4, 0, 0), (4, 3, 0)))
        kind, new, bulges = notes2d.corner_fillet(poly, 0, (2.0, 0.0), 1, (4.0, 1.5), 1.0, o, u, v)
        self.assertEqual((kind, len(new), len(bulges)), ("polyline", 4, 3))
        a = notes2d.Annotation(view, "line", pts((0, 0, 0), (4, 0, 0)))
        b = notes2d.Annotation(view, "line", pts((5, -1, 0), (5, 4, 0)))
        pa, pb, arc = notes2d.lines_fillet(a, (2.0, 0.0), b, (5.0, 2.0), 1.0, o, u, v)
        np.testing.assert_allclose([p[:2] for p in pa], [(0.0, 0.0), (4.0, 0.0)], atol=1e-9)
        np.testing.assert_allclose([p[:2] for p in pb], [(5.0, 1.0), (5.0, 4.0)], atol=1e-9)
        drawn = notes2d.shape(notes2d.Annotation(view, "arc", arc), o, u, v)[0][0]      # (an arc of its own)
        self.assertTrue(all(abs(float(np.linalg.norm(q - (4.0, 1.0))) - 1.0) < 1e-6 for q in drawn))

    def test_chain_and_radius(self):
        """0.453 — Revit's «Chain» and «Radius» on the Wall's and the Line's bars: with a radius, the chain's corner
        rounded (a curved wall between the two, tangent); the chain off, each wall — each line — starts with a click
        of its own."""
        from types import SimpleNamespace
        from arqbim.tools.bim_draw import WallTool
        from arqbim.tools.line import LineTool
        doc = Document()
        try:
            vp = SimpleNamespace(clear_overlays=lambda: None, show_tip=lambda *a: None, plan=True,
                                 tracking=SimpleNamespace(clear=lambda: None), is_shown=lambda obj: True,
                                 view_direction=lambda: np.array((0.0, 0.0, -1.0)))
            tool = WallTool(self._host(doc, vp))
            tool.spec = catalog.BY_KEY["parede_alv_20"]
            self.assertIn("chain", [o.key for o in tool.options()])
            tool.set_option("radius", 1.0)
            tool._start = np.array((0.0, 0.0, 0.0))
            tool._add(np.array((5.0, 0.0, 0.0)))
            tool._add(np.array((5.0, 4.0, 0.0)))
            kinds = lambda: sorted(doc.ifc.kind_of(o.id) for o in doc.objects.values()   # noqa: E731
                                   if o.is_bim and o.ifc_class in ("IfcWall", "IfcWallStandardCase"))
            self.assertEqual(kinds(), ["curved_wall", "wall", "wall"])
            arc = next(o.id for o in doc.objects.values() if o.is_bim and doc.ifc.kind_of(o.id) == "curved_wall")
            centre, radius, _s, _sweep, _h, _th = doc.ifc.curved_wall_params(arc)
            self.assertAlmostEqual(radius, 1.0, places=6)
            np.testing.assert_allclose(np.asarray(centre)[:2], (4.0, 1.0), atol=1e-6)
            np.testing.assert_allclose(tool._start, (5.0, 4.0, 0.0))                       # (the chain goes on)
            tool.set_option("chain", False)
            tool._add(np.array((0.0, 4.0, 0.0)))
            self.assertIsNone(tool._start)                                                 # (the next: a click)
            self.assertEqual(len(kinds()), 5)                                              # (+ its corner rounded)
            # the Line: the chain off, each line a sketch of its own
            line = LineTool(self._host(doc, vp))
            self.assertIn("chain", [o.key for o in line.options()])
            line.set_option("chain", False)
            line._pts, line._normal = [np.array((0.0, 10.0, 0.0))], np.array((0.0, 0.0, 1.0))
            line._add(np.array((3.0, 10.0, 0.0)))
            self.assertEqual(line._pts, [])
        finally:
            doc.modified = False

    def test_revit_arcs(self):
        """0.454 — Revit's «Center-ends Arc» and «Tangent End Arc» on the Wall's bar: an arc about a centre, from its
        start, turning the way asked; an arc leaving a wall's end tangent to it (its axis from the wall's axis, whatever
        the line drawn), the next going on from its end — tangent arcs, then straight again."""
        from types import SimpleNamespace
        from arqbim.core import arcs
        from arqbim.tools.bim_draw import WallTool, _short_angle
        c, r, _s, sw = arcs.arc_tangent((0, 0), (1, 0), (1, 1))               # a quarter turn to the left
        np.testing.assert_allclose(c, (0, 1), atol=1e-9)
        self.assertAlmostEqual(r, 1.0)
        self.assertAlmostEqual(math.degrees(sw), 90.0)
        c, r, s, sw = arcs.arc_tangent((0, 0), (1, 0), (-1, -1))              # behind, on the right: ¾ clockwise
        np.testing.assert_allclose(c, (0, -1), atol=1e-9)
        self.assertAlmostEqual(math.degrees(sw), -270.0)
        np.testing.assert_allclose(arcs.along(s + sw, sw), (0, 1), atol=1e-9)  # (where it goes at its end)
        self.assertIsNone(arcs.arc_tangent((0, 0), (1, 0), (3, 0)))           # (straight ahead)
        _c, r, s, sw = arcs.arc_from_centre((0, 0), (2, 0), (0, 3), 1)
        self.assertEqual((round(r, 9), round(math.degrees(sw), 9)), (2.0, 90.0))
        self.assertAlmostEqual(math.degrees(arcs.arc_from_centre((0, 0), (2, 0), (0, 3), -1)[3]), -270.0)
        self.assertEqual(arcs.turn_of((0, 0), (2, 0), (1, -0.1)), -1)
        self.assertAlmostEqual(math.degrees(_short_angle((0, 0), (2, 0), (0, -3))), -90.0)
        doc = Document()
        try:
            w20 = catalog.BY_KEY["parede_alv_20"]
            wall = bim.add_wall(doc, (0.0, 0.0, 0.0), (4.0, 0.0, 0.0), w20)
            vp = SimpleNamespace(clear_overlays=lambda: None, show_tip=lambda *a: None, plan=True,
                                 tracking=SimpleNamespace(clear=lambda: None))
            tool = WallTool(self._host(doc, vp))
            pts, dirs = tool._wall_ends()                                      # (each end, the way out of it)
            self.assertEqual(sorted((tuple(np.round(p[:2], 6)), tuple(np.round(d, 6))) for p, d in zip(pts, dirs)),
                             [((0.0, 0.0), (-1.0, 0.0)), ((4.0, 0.0), (1.0, 0.0))])
            curved = lambda: [o.id for o in doc.objects.values()                                 # noqa: E731
                              if o.is_bim and doc.ifc.kind_of(o.id) == "curved_wall"]
            # the tangent arc from the wall's end at (4, 0), to (5, 1): a quarter round (4, 1)
            tool.set_option("shape", "arc_tangent")
            tool._way_out_at = lambda x, y, level: (np.array((4.0, 0.0, 0.0)), np.array((1.0, 0.0)))
            tool._tangent_down(0, 0, ())
            tool._tangent_finish(arcs.arc_tangent(tool._tangent[0], tool._tangent[1], (5.0, 1.0)))
            arc = curved()[0]
            centre, radius, _s, sweep, _h, _th = doc.ifc.curved_wall_params(arc)
            np.testing.assert_allclose(np.asarray(centre)[:2], (4.0, 1.0), atol=1e-6)
            self.assertAlmostEqual(radius, 1.0, places=6)
            self.assertAlmostEqual(abs(math.degrees(sweep)), 90.0, places=4)
            np.testing.assert_allclose(tool._tangent[0], (5.0, 1.0, 0.0), atol=1e-9)   # (the next from its end…)
            np.testing.assert_allclose(tool._tangent[1], (0.0, 1.0), atol=1e-9)        # (…going on its way)
            tool.set_option("shape", "line")                                           # straight again, from there
            np.testing.assert_allclose(tool._start, (5.0, 1.0, 0.0), atol=1e-9)
            tool._add(np.array((5.0, 4.0, 0.0)))
            self.assertEqual(len(bim.wall_axes(doc)), 2)
            tool.set_option("shape", "arc_tangent")                                    # and round again
            np.testing.assert_allclose(tool._tangent[1], (0.0, 1.0), atol=1e-9)
            tool.cancel()
            # drawn by its left face, from the wall's start (out to −x): its axis still starts on the wall's axis
            tool.reference = "left"
            tool._way_out_at = lambda x, y, level: (np.array((0.0, 0.0, 0.0)), np.array((-1.0, 0.0)))
            tool._tangent_down(0, 0, ())
            a = tool._tangent[0]
            np.testing.assert_allclose(a, (0.0, -0.1, 0.0), atol=1e-9)
            tool._tangent_finish(arcs.arc_tangent(a, (-1.0, 0.0), a[:2] + (-1.0, -1.0)))
            new = [g for g in curved() if g != arc][0]
            centre, radius, start, sweep, _h, _th = doc.ifc.curved_wall_params(new)
            ends = [arcs.point_at(centre, radius, x) for x in (start, start + sweep)]
            self.assertLess(min(float(np.linalg.norm(e)) for e in ends), 1e-6)         # (one end at (0, 0))
            tool.cancel()
            # the centre-ends arc: its centre (where the mouse is), its radius typed, then 90° typed
            tool.reference = "axis"
            tool.set_option("shape", "arc_center")
            tool._hover = (np.array((10.0, 0.0, 0.0)), None)
            tool._centre_typed("2")
            tool._centre_typed("90")
            last = [g for g in curved() if g not in (arc, new)][0]
            centre, radius, _s, sweep, _h, _th = doc.ifc.curved_wall_params(last)
            np.testing.assert_allclose(np.asarray(centre)[:2], (10.0, 0.0), atol=1e-6)
            self.assertAlmostEqual(radius, 2.0, places=6)
            self.assertAlmostEqual(abs(math.degrees(sweep)), 90.0, places=4)
            self.assertEqual(tool._arc, [])                                            # (done: the tool again)
        finally:
            doc.modified = False

    def test_wall_polygons(self):
        """0.457 — Revit's «Inscribed / Circumscribed Polygon» on the Wall's bar: a hexagon of walls about its centre,
        a corner where clicked (inscribed); an octagon round a circle of 2 m (circumscribed, its radius typed)."""
        from types import SimpleNamespace
        from arqbim.tools.bim_draw import WallTool
        doc = Document()
        try:
            vp = SimpleNamespace(clear_overlays=lambda: None, show_tip=lambda *a: None, plan=True,
                                 tracking=SimpleNamespace(clear=lambda: None))
            tool = WallTool(self._host(doc, vp))
            tool.set_option("shape", "poly_in")
            self.assertEqual(tool.options()[-1].key, "sides")
            tool._corner = np.zeros(3)
            tool._polygon_finish(np.array((3.0, 0.0, 0.0)))
            axes = bim.wall_axes(doc)
            self.assertEqual(len(axes), 6)
            self.assertTrue(all(abs(float(np.linalg.norm(e[:2])) - 3.0) < 1e-6 for _g, s, e, _t in axes))
            tool.set_option("shape", "poly_out")
            tool.set_option("sides", 8)
            tool._corner = np.array((20.0, 0.0, 0.0))
            tool._end = np.array((25.0, 0.0, 0.0))
            tool._shape_typed("2")
            axes = bim.wall_axes(doc)[6:]
            self.assertEqual(len(axes), 8)
            middles = [float(np.linalg.norm(((s + e) / 2)[:2] - (20.0, 0.0))) for _g, s, e, _t in axes]
            np.testing.assert_allclose(middles, [2.0] * 8, atol=1e-6)                # (its sides touch the circle)
        finally:
            doc.modified = False

    def test_line_polygons_and_ellipses(self):
        """0.458 — the owner: «Faço também os polígonos e a elipse na Linha? — Sim, faz»: on the Line's row, Revit's
        inscribed and circumscribed polygons, ellipse and partial ellipse (the Circle tool draws them) — a hexagon face,
        its corners on the circle; a square round it, its sides touching it; an ellipse face; a half ellipse, a curve
        picked whole: its two half-axes as temporary dimensions, typed over (the line joined at its end follows), its
        grips, carried by a mirror."""
        from types import SimpleNamespace
        from arqbim.core import curves
        from arqbim.core.mesh import PolyMesh
        from arqbim.model import curve_edit
        from arqbim.tools.base import SKETCH_DRAW, switch_draw
        from arqbim.tools.circle import CircleTool, _Op
        from arqbim.tools.select import apply_dim, arc_radius_dims
        doc = Document()
        try:
            vp = SimpleNamespace(clear_overlays=lambda: None, show_tip=lambda *a: None, is_shown=lambda o: True,
                                 view_direction=lambda: np.array((0.0, 0.0, -1.0)),
                                 tracking=SimpleNamespace(clear=lambda: None))
            host = self._host(doc, vp)
            tool = CircleTool(host)
            host.tool, host.set_tool = tool, lambda name: None
            self.assertTrue({"poly_in", "poly_out", "ellipse", "ellipse_part"} <= set(SKETCH_DRAW))
            z, x, y = np.array((0.0, 0.0, 1.0)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))

            def made(centre, radius=0.0, **kw):
                tool._op = _Op(np.asarray(centre, dtype=float), z, x, y, None, radius=radius, towards=x, **kw)
                tool._finish()
                obj = list(doc.objects.values())[-1]
                return obj, [obj.matrix[:3, :3] @ v + obj.matrix[:3, 3] for v in obj.mesh.verts]

            self.assertTrue(switch_draw(tool, "poly_in"))
            self.assertEqual((tool.kind, tool.options()[1].key, tool.poly_sides), ("poly_in", "sides", 6))
            obj, corners = made((0.0, 0.0, 0.0), 2.0)
            self.assertEqual((len(obj.mesh.faces), len(corners)), (1, 6))
            np.testing.assert_allclose([np.linalg.norm(c) for c in corners], [2.0] * 6, atol=1e-9)
            self.assertTrue(any(np.linalg.norm(c - (2.0, 0.0, 0.0)) < 1e-9 for c in corners))     # (a corner there)
            tool.set_option("draw", "poly_out")
            tool.set_option("sides", 4)
            obj, corners = made((10.0, 0.0, 0.0), 1.0)
            self.assertEqual(len(corners), 4)
            self.assertAlmostEqual(obj.mesh.face_area(0), 4.0, places=9)                  # (a 2 × 2 square…)
            middles = [(corners[k] + corners[(k + 1) % 4]) / 2 for k in range(4)]
            self.assertTrue(any(np.linalg.norm(m - (11.0, 0.0, 0.0)) < 1e-9 for m in middles))   # (…touching there)
            tool.set_option("draw", "ellipse")
            self.assertEqual(tool.options()[1].key, "pieces")
            obj, corners = made((20.0, 0.0, 0.0), 3.0, axis=True, minor=2.0)
            self.assertEqual(len(corners), curves.ELLIPSE_SEGMENTS)
            self.assertTrue(all(abs(((c[0] - 20.0) / 3) ** 2 + (c[1] / 2) ** 2 - 1.0) < 1e-9 for c in corners))
            self.assertAlmostEqual(obj.mesh.face_area(0) / (math.pi * 6.0), 1.0, delta=0.01)
            line = SketchObject("l", I4, PolyMesh([(26.0, 0.0, 0.0), (30.0, 0.0, 0.0)], lines=[(0, 1)]))
            doc.execute(AddObject(line))
            tool.set_option("draw", "ellipse_part")
            a, b = np.array((30.0, 0.0, 0.0)), np.array((34.0, 0.0, 0.0))
            obj, pts = made(a, start=a.copy(), end=b, minor=1.5)
            self.assertTrue(curves.is_half_ellipse(obj.curve) and not obj.mesh.faces)
            np.testing.assert_allclose(pts[0], a, atol=1e-9)
            np.testing.assert_allclose(pts[-1], b, atol=1e-9)
            np.testing.assert_allclose(pts[len(pts) // 2], (32.0, 1.5, 0.0), atol=1e-9)   # (its top: to the left)
            dims = arc_radius_dims(obj)
            self.assertEqual(sorted(round(d.value, 9) for d in dims), [1.5, 2.0])
            apply_dim(doc, next(d for d in dims if d.key[0] == "ellipse_axis"), 3.0)    # (about its centre)
            obj = doc.get(obj.id)
            ends = curve_edit._ends(obj)
            np.testing.assert_allclose(ends, [(29.0, 0.0, 0.0), (35.0, 0.0, 0.0)], atol=1e-9)
            joined = doc.get(line.id)
            self.assertTrue(any(np.linalg.norm(v - (29.0, 0.0, 0.0)) < 1e-9 for v in joined.mesh.verts))  # (followed)
            apply_dim(doc, next(d for d in arc_radius_dims(obj) if d.key[0] == "ellipse_minor"), 1.0)
            pts = curves.ellipse_points(doc.get(obj.id).curve, 2)
            np.testing.assert_allclose(pts[1], (32.0, 1.0, 0.0), atol=1e-9)
            ends, middles, _arrows, what, _adds = curve_edit.grips(doc.get(obj.id))
            self.assertEqual((len(ends), len(middles), what), (2, 1, ["start", "end", "mid"]))
            moved = curve_edit.dragged(doc.get(obj.id), "end", (37.0, 0.0, 0.0))
            np.testing.assert_allclose(curves.ellipse_points(moved, 2), [(29.0, 0.0, 0.0), (33.0, 1.0, 0.0),
                                                                         (37.0, 0.0, 0.0)], atol=1e-9)
            mirror = np.diag((1.0, -1.0, 1.0, 1.0))
            flipped = curves.transform_curve(moved, mirror)
            np.testing.assert_allclose(curves.ellipse_points(flipped), [mirror[:3, :3] @ p for p in
                                                                         curves.ellipse_points(moved)], atol=1e-9)
            tool.activate()                                                     # (the ribbon's Circle: a circle)
            self.assertEqual(tool.kind, "circle")
        finally:
            doc.modified = False

    def test_polygon_sides_and_arcs(self):
        """0.459 — the owner: «não consigo selecionar linhas e arcos no polígono para ajustar»: an arc drawn in pieces
        found again whole (a polygon's fillet, a circle — a straight side is not one); a polygon's side made longer by
        its dimension; its fillet's radius changed, still tangent to its two sides; a circle's radius."""
        from arqbim.core import arc_runs
        from arqbim.core.mesh import PolyMesh
        from arqbim.core.sketch_geometry import circle_mesh
        from arqbim.model import line_edit
        from arqbim.tools.align import level_edges
        from arqbim.tools.select import apply_dim
        from types import SimpleNamespace
        doc = Document()
        try:
            face = SketchObject("f", I4, PolyMesh([(0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (4.0, 3.0, 0.0), (0.0, 3.0, 0.0)],
                                                  [[0, 1, 2, 3]]))
            doc.execute(AddObject(face))
            obj = doc.get(face.id)
            first = (face.id, *line_edit.face_edge_at(obj, (2.0, 0.0, 0.0))[0])
            second = (face.id, *line_edit.face_edge_at(obj, (4.0, 1.5, 0.0))[0])
            line_edit.fillet_face(doc, first, (2.0, 0.0, 0.0), second, (4.0, 1.5, 0.0), 1.0)
            obj = doc.get(face.id)
            ring = [obj.mesh.verts[i] for i in obj.mesh.faces[0]]
            n = len(ring)
            on_arc = next(k for k in range(n) if 3.2 < ring[k][0] < 3.9 and ring[k][1] < 0.5)
            run = arc_runs.run_around(ring, on_arc, closed=True)
            self.assertIsNotNone(run)
            self.assertAlmostEqual(run.radius, 1.0, places=6)
            np.testing.assert_allclose(run.centre, (3.0, 1.0), atol=1e-6)
            self.assertAlmostEqual(abs(math.degrees(run.sweep)), 90.0, places=4)
            ends = [tuple(np.round(ring[run.indices[i]][:2], 6) + 0.0) for i in (0, -1)]
            self.assertEqual(sorted(ends), [(3.0, 0.0), (4.0, 1.0)])
            straight = next(k for k in range(n) if np.allclose(ring[k][:2], (0, 0)))
            self.assertIsNone(arc_runs.run_around(ring, straight, closed=True))        # (a side: straight)
            corners, found = line_edit.face_run(obj, 0, on_arc)
            self.assertEqual(len(corners), len(run.indices))
            # the arc's radius typed over (its temporary dimension): 0,5 — the sides trimmed, still tangent
            dim = SimpleNamespace(key=("face_arc", face.id, 0, tuple(corners)), value=1.0)
            apply_dim(doc, dim, 0.5)
            ring = [tuple(np.round(doc.get(face.id).mesh.verts[i][:2], 6) + 0.0) for i in doc.get(face.id).mesh.faces[0]]
            self.assertIn((3.5, 0.0), ring)
            self.assertIn((4.0, 0.5), ring)
            self.assertAlmostEqual(doc.get(face.id).mesh.face_area(0), 12.0 - (0.25 - math.pi * 0.25 / 4), places=2)
            doc.undo()                                                                 # (one step)
            self.assertAlmostEqual(doc.get(face.id).mesh.face_area(0), 12.0 - (1.0 - math.pi / 4), places=2)
            # a side's length typed over: its far corner moves along it
            obj = doc.get(face.id)
            i = next(v for v in obj.mesh.faces[0] if np.allclose(obj.mesh.verts[v][:2], (0, 3)))
            j = next(v for v in obj.mesh.faces[0] if np.allclose(obj.mesh.verts[v][:2], (0, 0)))
            apply_dim(doc, SimpleNamespace(key=("face_side", face.id, i, j), value=3.0), 5.0)
            np.testing.assert_allclose(doc.get(face.id).mesh.verts[j][:2], (0.0, -2.0), atol=1e-9)
            # a circle: its outline one arc, whole; its radius changed
            circle = SketchObject("c", I4, circle_mesh(2.0, 24))
            doc.execute(AddObject(circle))
            run = arc_runs.run_around(circle.mesh.verts, 5, closed=True)
            self.assertTrue(run.whole and abs(run.radius - 2.0) < 1e-9 and len(run.indices) == 24)
            corners, _run = line_edit.face_run(doc.get(circle.id), 0, 5)
            line_edit.face_arc_radius(doc, circle.id, 0, corners, 3.0)
            np.testing.assert_allclose([np.linalg.norm(v[:2]) for v in doc.get(circle.id).mesh.verts], [3.0] * 24)
            # its outline's edges as a chain (Pick Lines): the arc found from any of its pieces
            edges = level_edges(doc.get(circle.id))
            points, closed, k = arc_runs.chain_through(edges, edges[3][0], edges[3][1])
            self.assertTrue(closed and len(points) == 24)
            self.assertTrue(arc_runs.run_around(points, k, closed).whole)
        finally:
            doc.modified = False

    def test_curved_wall_radius(self):
        """0.459 — the owner: «Selecionei um arco na parede, mas não tem cota temporária para ajustar»: a curved wall's
        radius as a temporary dimension; a fillet's typed over — the walls trimmed, the arc still tangent to both —;
        another's about its centre."""
        from arqbim.tools.select import apply_dim, selection_dims
        doc = Document()
        try:
            w20 = catalog.BY_KEY["parede_alv_20"]
            a = bim.add_wall(doc, (0.0, 0.0, 0.0), (5.0, 0.0, 0.0), w20)
            b = bim.add_wall(doc, (5.0, 0.0, 0.0), (5.0, 4.0, 0.0), w20, prev=(a, np.array((1.0, 0.0, 0.0))))
            arc = bim.fillet_walls(doc, a, (2.0, 0.0), b, (5.0, 2.0), 1.0, w20)
            self.assertEqual(len(doc.ifc.fillet_ends(arc)), 2)
            dims = selection_dims(doc, {arc})
            self.assertEqual([d.key for d in dims], [("curved_radius", arc)])
            self.assertAlmostEqual(dims[0].value, 1.0, places=6)
            apply_dim(doc, dims[0], 2.0)
            centre, radius, _s, sweep, _h, _t = doc.ifc.curved_wall_params(arc)
            self.assertAlmostEqual(radius, 2.0, places=6)
            np.testing.assert_allclose(np.asarray(centre)[:2], (3.0, 2.0), atol=1e-6)
            self.assertAlmostEqual(abs(math.degrees(sweep)), 90.0, places=4)
            _sa, ea, _t = doc.ifc.wall_axis(a)
            sb, _eb, _t = doc.ifc.wall_axis(b)
            np.testing.assert_allclose(ea[:2], (3.0, 0.0), atol=1e-6)                 # (trimmed: tangent)
            np.testing.assert_allclose(sb[:2], (5.0, 2.0), atol=1e-6)
            doc.undo()                                                                 # (one step)
            self.assertAlmostEqual(doc.ifc.curved_wall_params(arc)[1], 1.0, places=6)
            np.testing.assert_allclose(doc.ifc.wall_axis(a)[1][:2], (4.0, 0.0), atol=1e-6)
            alone = bim.add_curved_wall(doc, (20.0, 0.0, 0.0), 3.0, 0.0, math.pi / 2, w20)
            self.assertIsNone(doc.ifc.fillet_ends(alone))
            apply_dim(doc, selection_dims(doc, {alone})[0], 4.0)                       # (alone: about its centre)
            centre, radius, *_rest = doc.ifc.curved_wall_params(alone)
            self.assertAlmostEqual(radius, 4.0, places=6)
            np.testing.assert_allclose(np.asarray(centre)[:2], (20.0, 0.0), atol=1e-6)
        finally:
            doc.modified = False

    def test_temporary_dimension_made_permanent(self):
        from types import SimpleNamespace
        from arqbim.core import temp_dims
        from arqbim.model import dimensions as dims_model
        from arqbim.tools.select import SelectTool
        doc = Document()
        try:
            w20 = catalog.BY_KEY["parede_alv_20"]
            wall = bim.add_wall(doc, (0.0, 0.0, 0.0), (4.0, 0.0, 0.0), w20)
            view = ("plan", doc.active_storey)
            vp = SimpleNamespace(selection_listeners=[], axes_listeners=[], annotation_listeners=[],
                                 current_view=lambda: view, world_per_pixel=lambda p: 0.01)
            tool = SelectTool(self._host(doc, vp))
            dim = temp_dims.TempDim(np.array((0.0, 0.1, 0.0)), np.array((4.0, 0.1, 0.0)), np.array((0, 0, 1.0)),
                                    key=("wall_length", wall), offset_px=30.0)
            tool._make_permanent(dim)
            self.assertEqual(len(doc.dimensions), 1)
            made = doc.dimensions[0]
            self.assertEqual(made.view, view)
            self.assertEqual([r[0] if r else None for r in made.refs], [wall, wall])    # (hung on the wall)
            self.assertAlmostEqual(float(made.at[1]), 0.1 + 0.30, places=6)              # (where its line was)
            bim.resize_wall(doc, wall, at_end=1.0)                                      # the wall 1 m longer…
            a, b = dims_model.ends(doc, made)
            self.assertAlmostEqual(float(np.linalg.norm(np.asarray(b) - np.asarray(a))), 5.0, places=6)   # …it too
        finally:
            doc.modified = False


class OutlinesAsRevit(unittest.TestCase):
    """0.456 — the owner: «Sim, põe» (Revit's «Draw» panel on a floor, a ceiling, a slab): a regular polygon inscribed
    and circumscribed, an ellipse (four Bézier quarters), the outline of the lines picked, the Offset, the corners'
    Radius — and a slab, a ceiling, a floor finish made over them (their curves kept as drawn)."""

    @staticmethod
    def _host(doc):
        from types import SimpleNamespace
        vp = SimpleNamespace(clear_overlays=lambda: None, show_tip=lambda *a: None, show_polygon=lambda *a, **k: None,
                             show_label=lambda *a: None, tracking=SimpleNamespace(clear=lambda: None))
        return SimpleNamespace(doc=doc, viewport=vp, message=lambda *a, **k: None, set_hint=lambda *a: None,
                               set_vcb=lambda *a: None)

    def test_shapes(self):
        from arqbim.core import curves, outline_loops, outline_shapes as sh
        loop = sh.regular((0, 0), (2, 0), 6, inscribed=True)
        self.assertTrue(all(abs(math.hypot(*c) - 2.0) < 1e-9 for c in loop[0]))            # (corners on the circle)
        loop = sh.regular((0, 0), (2, 0), 4, inscribed=False)
        np.testing.assert_allclose(sorted(round(abs(c), 9) for p in loop[0] for c in p), [2.0] * 8)   # (a 4×4 square)
        self.assertAlmostEqual(outline_loops.area([loop]), 16.0, places=9)
        ell = sh.ellipse((0, 0), (3, 0), 2)
        ring = curves.profile_outline(*ell)
        self.assertTrue(all(abs((x / 3) ** 2 + (y / 2) ** 2 - 1.0) < 2e-3 for x, y in ring))   # (on the ellipse)
        self.assertAlmostEqual(outline_loops.area([ell]), math.pi * 6, delta=0.05)
        rect = sh.picked([((0, 0), (1, 0)), ((4, -1), (0, 1)), ((5, 3), (-1, 0)), ((0, 5), (0, -1))])
        self.assertEqual(sorted(rect[0]), [(0.0, 0.0), (0.0, 3.0), (4.0, 0.0), (4.0, 3.0)])
        self.assertIsNone(sh.picked([((0, 0), (1, 0)), ((0, 1), (1, 0)), ((5, 3), (0, 1))]))   # (two parallel)
        grown = sh.offset(rect, 0.5)
        self.assertAlmostEqual(outline_loops.area([grown]), 5.0 * 4.0, places=9)
        self.assertIsNone(sh.offset(rect, -2.0))                                             # (in too far)
        round_ = sh.rounded(rect, 1.0)
        self.assertEqual(len(round_[0]), 8)
        self.assertAlmostEqual(outline_loops.area([round_]), 12.0 - 4 * (1 - math.pi / 4), places=2)
        small = sh.rounded(rect, 9.0)                                                        # (kept to the sides)
        self.assertIsNotNone(outline_loops.polygon([small]))

    def test_slab_ceiling_floor_made(self):
        from arqbim.core import outline_shapes as sh
        from arqbim.tools.slab import CeilingTool, FlooringTool, SlabTool
        doc = Document()
        try:
            host = self._host(doc)
            slab = SlabTool(host)
            self.assertEqual(len(slab.shapes), 8)
            slab.set_option("shape", "poly_in")
            self.assertEqual([o.key for o in slab.options()][-3:], ["sides", "offset", "radius"])
            slab.set_option("sides", 6)
            slab._finish_loop(sh.regular((0, 0), (2, 0), 6), 0.0)
            guid = [o.id for o in doc.objects.values() if o.is_bim][-1]
            self.assertAlmostEqual(doc.ifc.slab_outline(guid)["area"], 3 * math.sqrt(3) / 2 * 4, places=6)
            slab.set_option("shape", "ellipse")                         # an ellipse: its curves kept (its drawing)
            slab._finish_loop(sh.ellipse((10, 0), (13, 0), 2), 0.0)
            guid = [o.id for o in doc.objects.values() if o.is_bim][-1]
            self.assertAlmostEqual(doc.ifc.slab_outline(guid)["area"], math.pi * 6, delta=0.1)
            slab.set_option("shape", "rect")                            # a rectangle 10 cm out, its corners rounded
            slab.set_option("offset", 0.1)
            slab.set_option("radius", 0.5)
            slab._finish_loop([[(20, 0), (24, 0), (24, 3), (20, 3)], [None] * 4], 0.0)
            guid = [o.id for o in doc.objects.values() if o.is_bim][-1]
            self.assertAlmostEqual(doc.ifc.slab_outline(guid)["area"], 4.2 * 3.2 - 4 * 0.25 * (1 - math.pi / 4),
                                   delta=0.02)
            slab.set_option("shape", "pick")                             # the lines picked
            slab.offset = slab.radius = 0.0
            slab._lines = [(np.array(p, float), np.array(d, float), None)
                           for p, d in (((30, 0, 0), (1, 0, 0)), ((34, 0, 0), (0, 1, 0)), ((34, 3, 0), (-1, 0, 0)),
                                        ((30, 3, 0), (0, -1, 0)))]
            slab._finish_picked()
            guid = [o.id for o in doc.objects.values() if o.is_bim][-1]
            self.assertAlmostEqual(doc.ifc.slab_outline(guid)["area"], 12.0, places=6)
            for cls, kind in ((CeilingTool, "ceiling"), (FlooringTool, "flooring")):
                tool = cls(host)
                self.assertIn("ellipse", tool.shapes)
                tool.set_option("shape", "circle")
                self.assertFalse(tool.round_slab())
                tool._corner, tool._end = np.array((40.0, 0.0, 0.0)), np.array((42.0, 0.0, 0.0))
                tool._finish_loop(tool._centred_loop(tool._end), 0.0)
                made = [o.id for o in doc.objects.values() if o.is_bim and doc.ifc.kind_of(o.id) == kind]
                self.assertEqual(len(made), 1)
                params = doc.ifc.ceiling_params(made[0]) if kind == "ceiling" else None
                if params is not None:
                    from shapely.geometry import Polygon
                    self.assertAlmostEqual(Polygon(params["outline"]).area, math.pi * 4, delta=0.05)
        finally:
            doc.modified = False


class RegionOutlinesAsRevit(unittest.TestCase):
    """0.456 — a region / a mask drawn as a floor's outline (Revit's «Draw» panel on a filled region): a circle (its
    four arcs as bulges), a regular polygon, an ellipse (in pieces), the lines picked, a rectangle 10 cm out with its
    corners rounded — through the Desenho 2D tool."""

    def test_regions(self):
        from types import SimpleNamespace
        from arqbim.core import outline_loops, outline_shapes as sh
        from arqbim.model import annotations as notes2d
        from arqbim.tools.draft import DraftTool
        o, u, v, n = np.zeros(3), np.array((1.0, 0, 0)), np.array((0, 1.0, 0)), np.array((0, 0, 1.0))
        pts, bulges = notes2d.region_from_loop(outline_loops.circle((0, 0), 2.0))
        self.assertEqual(len(pts), 4)
        np.testing.assert_allclose(bulges, [math.tan(math.pi / 8)] * 4, atol=1e-9)        # (four quarter arcs)
        doc = Document()
        try:
            vp = SimpleNamespace(view_plane=lambda: (o, u, v, n), current_view=lambda: ("plan", "s"),
                                 clear_overlays=lambda: None, show_lines=lambda *a: None)
            host = SimpleNamespace(doc=doc, viewport=vp, message=lambda *a, **k: None, set_hint=lambda *a: None,
                                   set_vcb=lambda *a: None)
            tool = DraftTool(host)
            tool.set_option("shape", "mask")
            keys = [opt.key for opt in tool.options()]
            self.assertIn("mode", keys)
            area = lambda ann: notes2d.area(ann, o, u, v)                                  # noqa: E731
            tool.set_option("mode", "circle")
            tool._points = [np.zeros(3)]
            tool._region_finish(tool._region_loop(np.array((2.0, 0.0))))
            self.assertAlmostEqual(area(doc.annotations[-1]), math.pi * 4, delta=0.02)    # (a true circle)
            self.assertEqual(doc.annotations[-1].hatch, "mask")
            tool.set_option("mode", "poly_in")
            tool._points = [np.zeros(3)]
            tool._region_finish(tool._region_loop(np.array((2.0, 0.0))))
            self.assertAlmostEqual(area(doc.annotations[-1]), 3 * math.sqrt(3) / 2 * 4, places=6)
            tool.set_option("mode", "ellipse")
            tool._points = [np.zeros(3), np.array((3.0, 0.0, 0.0))]
            tool._region_finish(tool._region_loop(np.array((0.0, 2.0))))
            self.assertAlmostEqual(area(doc.annotations[-1]), math.pi * 6, delta=0.05)
            tool.set_option("mode", "pick")
            tool._lines = [(np.array(p, float), np.array(d, float), None)
                           for p, d in (((0, 0), (1, 0)), ((4, 0), (0, 1)), ((4, 3), (-1, 0)), ((0, 3), (0, -1)))]
            tool.enter()
            self.assertAlmostEqual(area(doc.annotations[-1]), 12.0, places=6)
            tool.set_option("mode", "rect")
            tool.set_option("offset", 0.1)
            tool.set_option("radius", 0.5)
            tool._points = [np.zeros(3)]
            tool._region_finish(tool._region_loop(np.array((4.0, 3.0))))
            self.assertAlmostEqual(area(doc.annotations[-1]), 4.2 * 3.2 - (1 - math.pi / 4), delta=0.01)
            self.assertEqual(len(doc.annotations), 5)
        finally:
            doc.modified = False


class AlignAnything(unittest.TestCase):
    """0.449 — the owner: «o comando alinhar … deve funcionar com linhas, pisos, e qualquer elementos no projeto»:
    any element's level edges, the nearest one (parallel to the reference); a loose line aligned alone (the line
    joined to it stretching), a slab moved whole, a door slid along its wall."""

    def _tool(self, doc):
        from types import SimpleNamespace
        from arqbim.tools.align import AlignTool
        return AlignTool(SimpleNamespace(doc=doc, viewport=None, message=lambda *a, **k: None,
                                         set_hint=lambda *a: None, set_vcb=lambda *a: None))

    def test_edges_and_the_nearest(self):
        from arqbim.tools.align import level_edges, nearest_edge
        doc = Document()
        try:
            slab = bim.add_slab(doc, np.array((0.0, 0.0, 0.0)), 4.0, 3.0, catalog.BY_KEY["laje_12"])
            edges = level_edges(doc.get(slab))
            self.assertGreaterEqual(len(edges), 4)
            k, d = nearest_edge(edges, (3.9, 1.5, 0.0), along=np.array((0.0, 1.0)))      # (its right side)
            self.assertAlmostEqual(float(edges[k][0][0]), 4.0, places=6)
            self.assertAlmostEqual(d, 0.1, places=6)
            k, _d = nearest_edge(edges, (3.9, 1.5, 0.0), along=np.array((1.0, 0.0)))      # (the nearest across)
            self.assertAlmostEqual(abs(float(edges[k][0][1]) - 1.5), 1.5, places=6)
            self.assertIsNone(nearest_edge(edges, (1, 1, 0), along=np.array((0.6, 0.8))))   # (none that way)
        finally:
            doc.modified = False

    def test_line_slab_and_door_aligned(self):
        from arqbim.core.mesh import PolyMesh
        from arqbim.model import line_edit
        doc = Document()
        try:
            chain = SketchObject("l", I4, PolyMesh([(0.0, 5.0, 0.0), (4.0, 5.0, 0.0), (4.0, 8.0, 0.0)],
                                                   lines=[(0, 1), (1, 2)]))
            doc.execute(AddObject(chain))
            slab = bim.add_slab(doc, np.array((0.0, 0.0, 0.0)), 4.0, 3.0, catalog.BY_KEY["laje_12"])
            wall = bim.add_wall(doc, (10.0, 0.0, 0.0), (16.0, 0.0, 0.0), catalog.BY_KEY["parede_alv_20"])
            door = bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, wall), 1.0, -1)
            tool = self._tool(doc)
            self.assertEqual([tool._how(i) for i in (chain.id, slab, door, wall)],
                             ["line", "element", "filling", "element"])
            # the upright line moved 1 m across (onto x = 5): it alone; the level one stretches to it
            a, b = np.array((4.0, 5.0, 0.0)), np.array((4.0, 8.0, 0.0))
            tool._align(chain.id, np.array((1.0, 0.0)), "line", (a, b))
            ends = sorted(tuple(np.round(p, 6)) for _i, _j, p, q in line_edit.segments(doc.get(chain.id))
                          for p in (p, q))
            self.assertIn((5.0, 8.0, 0.0), ends)
            self.assertIn((5.0, 5.0, 0.0), ends)
            self.assertIn((0.0, 5.0, 0.0), ends)                        # (the other end of the level one stays)
            before = np.asarray(doc.get(slab).mesh.bounds()[0], dtype=float)
            tool._align(slab, np.array((0.0, -0.5)), "element", None)   # the slab moved whole
            after = np.asarray(doc.get(slab).mesh.bounds()[0], dtype=float)
            np.testing.assert_allclose(after - before, (0.0, -0.5, 0.0), atol=1e-6)
            s0 = float(doc.ifc.filling_state(door)["s"])
            tool._align(door, np.array((0.5, 0.0)), "filling", None)    # the door along its wall
            self.assertAlmostEqual(float(doc.ifc.filling_state(door)["s"]) - s0, 0.5, places=6)
            with self.assertRaises(line_edit.LineRefused):              # (across its wall: refused)
                tool._align(door, np.array((0.0, 0.5)), "filling", None)
        finally:
            doc.modified = False


class JoinsByMaterial(unittest.TestCase):
    """0.320 — the cut and the views joined by material, as Revit cleans up joins (model/cut_joins.py,
    model/seen_joins.py): a room's walls cut — their block one ring, the plaster turning the corners in a mitre, the
    thick line only round all that is cut; a wall against another's side — its block in up to the other's block, the
    plaster interrupted; a column in a wall — the wall's fills less it; two walls of a type in a row seen in an
    elevation — no line where they meet, a line where the next one is of another material, only its part above the
    lower one where one is taller."""

    @staticmethod
    def _regions(drawing):
        from arqbim.core import drawing2d
        by = {}
        for ring, key in drawing.fills:
            by.setdefault(key, []).append(ring)
        return {key: drawing2d.nested(rings) for key, rings in by.items()}

    @staticmethod
    def _count(region):
        return len(getattr(region, "geoms", [region]))

    def test_curved_wall_layers(self):
        """0.460 — the owner: «a parede curva não tem camadas de reboco. devia ter já que são mesmo tipo»: a curved
        wall's layers cut in a plan as rings about its centre (plaster | block | plaster, as its type's), a whole
        circle's too; a fillet's plaster one with its straight walls' (no line where they meet)."""
        from arqbim.model import drawings
        doc = Document()
        try:
            w20 = catalog.BY_KEY["parede_alv_20"]
            arc = bim.add_curved_wall(doc, (0.0, 0.0, 0.0), 3.0, 0.0, math.pi / 2, w20)
            full = bim.add_curved_wall(doc, (20.0, 0.0, 0.0), 2.0, 0.0, 2 * math.pi, w20)
            layers = doc.ifc.curved_layers([arc, full])
            centre, rings = layers[arc]
            np.testing.assert_allclose(centre, (0.0, 0.0), atol=1e-9)
            self.assertEqual(len(rings), len(w20.layers))
            self.assertAlmostEqual(min(r0 for _h, r0, _r1 in rings), 2.9, places=6)
            self.assertAlmostEqual(max(r1 for _h, _r0, r1 in rings), 3.1, places=6)
            plan = drawings.plan(doc, doc.active_storey, "P")
            regions = self._regions(plan)
            self.assertEqual(set(regions), {"masonry", "gypsum"})                # (its plaster drawn, not only block)
            plaster = regions["gypsum"]
            self.assertEqual(self._count(plaster), 4)                            # (two arcs, two whole rings)
            block_area = math.pi / 4 * ((3.0 + 0.08) ** 2 - (3.0 - 0.08) ** 2) + \
                math.pi * ((2.0 + 0.08) ** 2 - (2.0 - 0.08) ** 2)                # (the block 16 cm, 2 cm each side)
            self.assertAlmostEqual(regions["masonry"].area / block_area, 1.0, delta=0.01)
            self.assertAlmostEqual(plaster.area / (block_area * 0.04 / 0.16), 1.0, delta=0.02)
        finally:
            doc.modified = False
        doc = Document()                                    # a fillet between two walls: their plaster goes on round it
        try:
            w20 = catalog.BY_KEY["parede_alv_20"]
            a = bim.add_wall(doc, (0.0, 0.0, 0.0), (5.0, 0.0, 0.0), w20)
            b = bim.add_wall(doc, (5.0, 0.0, 0.0), (5.0, 4.0, 0.0), w20, prev=(a, np.array((1.0, 0.0, 0.0))))
            bim.fillet_walls(doc, a, (2.0, 0.0), b, (5.0, 2.0), 1.0, w20)
            regions = self._regions(drawings.plan(doc, doc.active_storey, "P"))
            from shapely.geometry import Point
            at = lambda r: Point(4.0 + r * math.cos(-math.pi / 4), 1.0 + r * math.sin(-math.pi / 4))   # noqa: E731
            self.assertTrue(regions["gypsum"].contains(at(1.09)) and regions["gypsum"].contains(at(0.91)))  # (round it)
            self.assertTrue(regions["masonry"].contains(at(1.0)) and not regions["masonry"].contains(at(1.09)))
            self.assertEqual(self._count(regions["gypsum"]), 1)          # (one with the walls': round their free ends)
            self.assertEqual(self._count(regions["masonry"]), 1)
        finally:
            doc.modified = False

    def test_corners_and_tees(self):
        from arqbim.model import drawings
        doc = Document()
        try:
            w20 = catalog.BY_KEY["parede_alv_20"]
            bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (6.0, 4.0, 0.0),
                                                          (0.0, 4.0, 0.0))], w20)
            plan = drawings.plan(doc, doc.active_storey, "P")
            regions = self._regions(plan)
            self.assertEqual(set(regions), {"masonry", "gypsum"})
            self.assertEqual(self._count(regions["masonry"]), 1)                 # (the block: one ring round the room)
            self.assertEqual(len(regions["masonry"].interiors), 1)
            self.assertEqual(self._count(regions["gypsum"]), 2)                  # (the plaster: outside, inside)
            self.assertAlmostEqual(regions["masonry"].area, 3.2, places=4)      # (nothing lost, nothing twice)
            self.assertAlmostEqual(regions["gypsum"].area, 0.8, places=4)
            self.assertEqual(len(plan.outline), 2)                               # (the thick line: round, and the room)
            corners = [ring for ring in plan.outline if np.allclose(ring.min(axis=0), (-0.1, -0.1))]
            self.assertEqual(len(corners), 1)
            self.assertEqual(len(corners[0]), 4)                                 # (a rectangle: no step at a joint)
            bim.add_wall(doc, (3.0, 0.0, 0.0), (3.0, 4.0, 0.0), w20)             # a wall across, to the others' axes
            plan = drawings.plan(doc, doc.active_storey, "P")
            regions = self._regions(plan)
            self.assertEqual(self._count(regions["masonry"]), 1)                 # (its block in, joined to theirs)
            self.assertEqual(len(regions["masonry"].interiors), 2)
            self.assertEqual(self._count(regions["gypsum"]), 3)                  # (the inner plaster: two rooms')
            total = sum(r.area for r in regions.values())
            self.assertAlmostEqual(total, 4.0 + 0.2 * 3.8, places=4)             # (its overlap with them: once)
            self.assertEqual(len(plan.outline), 3)
        finally:
            doc.modified = False

    def test_corner_out_of_square(self):
        """0.442 — an L of walls a little out of square (3°): the two blocks worked out apart met along the mitre with
        its ends rounded a grid step apart, and the thick line went in and out along the crack — a line across the
        corner, on the screen and on paper. Now one block, one ring round it all, no line across the corner."""
        from arqbim.model import cut_hatches, drawings
        from arqbim.model import graphic_styles as gs
        doc = Document()
        try:
            w20 = catalog.BY_KEY["parede_alv_20"]
            a = math.radians(3.0)
            ux, uy = np.array((math.cos(a), math.sin(a), 0.0)), np.array((-math.sin(a), math.cos(a), 0.0))
            p1, p2 = ux * 5.0, ux * 5.0 + uy * 4.0
            first = bim.add_wall(doc, np.zeros(3), p1, w20)
            bim.add_wall(doc, p1, p2, w20, prev=(first, bim.horizontal_dir(np.zeros(3), p1)))
            plan = drawings.plan(doc, doc.active_storey, "P")
            regions = self._regions(plan)
            self.assertEqual(self._count(regions["masonry"]), 1)                 # (the block: one piece…)
            self.assertEqual(len(regions["masonry"].interiors), 0)               # (…with no crack in it)
            self.assertEqual(len(plan.outline), 1)                               # (the thick line: one ring round)
            objs = [o for o in doc.objects.values() if o.is_bim]
            n, cut = np.array((0.0, 0.0, -1.0)), 1.2
            origin, u, v = np.array((0.0, 0.0, cut)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
            fills, own, whose = drawings.cut_fills(doc, objs, n, -cut, origin, u, v)
            parts = cut_hatches.build(fills, whose, own, gs.defaults(), 50, origin, u, v, n * 0.003)
            across = []                                    # (the screen's thick and thin lines: none across the corner)
            for owner in (None, cut_hatches.SEAMS):
                for s in parts.get(owner, (None, None, np.zeros((0, 2, 3))))[2][:, :, :2]:
                    d = s[1] - s[0]
                    length = float(np.linalg.norm(d))
                    if length > 1e-3 and np.linalg.norm(s.mean(axis=0) - p1[:2]) < 0.45 and \
                            max(abs(float(d @ ux[:2])), abs(float(d @ uy[:2]))) / length < 0.999:
                        across.append(s)
            self.assertEqual(across, [])
        finally:
            doc.modified = False

    def test_closing_corner_turned(self):
        """0.443 — a room drawn as one chain, turned 72,4°: at the corner where the chain closes, the first wall's
        layers (cut apart at its other corner, a hair from each other) were two pieces, the corner took only the inner
        plaster and the outer plaster stopped short of it. Now both plasters are rings round the room."""
        from arqbim.model import drawings
        doc = Document()
        try:
            w20 = catalog.BY_KEY["parede_alv_20"]
            a = math.radians(72.4)
            ux, uy = np.array((math.cos(a), math.sin(a), 0.0)), np.array((-math.sin(a), math.cos(a), 0.0))
            o = np.array((-20.8404, 7.0293, 0.0))
            bim.add_wall_loop(doc, [o, o + ux * 6.5894, o + ux * 6.5894 + uy * 3.485, o + uy * 3.485], w20)
            regions = self._regions(drawings.plan(doc, doc.active_storey, "P"))
            self.assertEqual(self._count(regions["masonry"]), 1)
            plasters = list(getattr(regions["gypsum"], "geoms", [regions["gypsum"]]))
            self.assertEqual(len(plasters), 2)                                   # (outside and inside…)
            self.assertEqual([len(p.interiors) for p in plasters], [1, 1])      # (…each a ring round the room)
        finally:
            doc.modified = False

    def test_finish_turned_round_ends_and_jambs(self):
        """0.444 — as Revit's wrapping at ends and at inserts: the plaster turns round a wall's free end and a hole's
        jambs (2 cm, the block set back), into the jambs of an aluminium door up to its frame; not where a door's
        lining covers the jamb."""
        from shapely.geometry import Point
        from arqbim.model import drawings
        doc = Document()
        try:
            w20 = catalog.BY_KEY["parede_alv_20"]
            wall = bim.add_wall(doc, (0.0, 0.0, 0.0), (10.0, 0.0, 0.0), w20)
            frame = bim.wall_frame(doc, wall)
            bim.add_wall_opening(doc, wall, 2.0, 0.8, 2.0, 0.0)                          # a hole 2,0 – 2,8
            bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_sacada_140"], frame, 4.0, -1)   # 4,0 – 5,4
            bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, 7.0, -1)            # 7,0 – 7,8
            regions = self._regions(drawings.plan(doc, doc.active_storey, "P"))
            gypsum, masonry = regions["gypsum"], regions["masonry"]
            self.assertTrue(gypsum.contains(Point(0.01, 0.0)))          # (the free end: plaster across it…)
            self.assertTrue(masonry.contains(Point(0.03, 0.0)))         # (…the block set back 2 cm)
            self.assertTrue(gypsum.contains(Point(9.99, 0.0)))
            self.assertTrue(gypsum.contains(Point(1.99, 0.0)))          # (the hole's jambs)
            self.assertTrue(gypsum.contains(Point(2.81, 0.0)))
            self.assertTrue(masonry.contains(Point(1.97, 0.0)))
            self.assertTrue(gypsum.contains(Point(3.99, 0.07)))         # (the aluminium door: from each face…)
            self.assertTrue(gypsum.contains(Point(3.99, -0.07)))
            self.assertFalse(gypsum.contains(Point(3.99, 0.0)))         # (…up to its frame)
            self.assertTrue(masonry.contains(Point(6.99, 0.0)))         # (the lined door: its lining covers the jamb)
            self.assertFalse(gypsum.contains(Point(6.99, 0.07)))
        finally:
            doc.modified = False

    def test_column_in_wall(self):
        from arqbim.model import cut_joins, drawings
        doc = Document()
        try:
            wall = bim.add_wall(doc, (0.0, 0.0, 0.0), (4.0, 0.0, 0.0), catalog.BY_KEY["parede_alv_20"])
            column = bim.add_column(doc, np.array((2.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
            objs = [o for o in doc.objects.values() if o.is_bim]
            n, cut = np.array((0.0, 0.0, -1.0)), 1.2
            origin, u, v = np.array((0.0, 0.0, cut)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
            fills, _own, whose = drawings.cut_fills(doc, objs, n, -cut, origin, u, v)
            from shapely.ops import unary_union
            from arqbim.core import drawing2d
            mine = unary_union([drawing2d.region([r]) for (r, _k), w in zip(fills, whose) if w == wall])
            its = unary_union([drawing2d.region([r]) for (r, _k), w in zip(fills, whose) if w == column])
            self.assertLess(mine.intersection(its).area, 1e-8)                   # (the column's cut: its own)
            self.assertAlmostEqual(its.area, 0.09, places=4)
            whole = unary_union(list(cut_joins.merged(fills, whose).values()))
            self.assertAlmostEqual(whole.area, mine.area + its.area, places=6)
        finally:
            doc.modified = False

    def test_seams_in_elevation(self):
        from arqbim.model import drawings

        def joint_lines(doc, x, z0=0.05):
            drawing = drawings.elevation(doc, "S", "Sul")
            x -= drawings.elevation_plane(doc, "S")[0][0]                 # (the drawing's x: from its plane's point)
            seg = drawing.lines
            vertical = np.abs(seg[:, 0, 0] - seg[:, 1, 0]) < 1e-6
            at = np.abs(seg[:, 0, 0] - x) < 1e-3
            return [s for s in seg[vertical & at] if max(s[0][1], s[1][1]) > z0]

        doc = Document()
        try:
            w20 = catalog.BY_KEY["parede_alv_20"]
            bim.add_wall(doc, (0.0, 0.0, 0.0), (4.0, 0.0, 0.0), w20)
            bim.add_wall(doc, (4.0, 0.0, 0.0), (8.0, 0.0, 0.0), w20)               # the same type, in a row
            self.assertEqual(joint_lines(doc, 4.0), [])                           # (no line where they meet)
            dry = catalog.BY_KEY["parede_dry_10"]
            bim.add_wall(doc, (8.0, -0.05, 0.0), (11.0, -0.05, 0.0), dry)        # another material, flush outside
            self.assertTrue(joint_lines(doc, 8.0))                               # (a line where the material changes)
            doc2 = Document()
            bim.add_wall(doc2, (0.0, 0.0, 0.0), (4.0, 0.0, 0.0), w20, height=2.8)
            bim.add_wall(doc2, (4.0, 0.0, 0.0), (8.0, 0.0, 0.0), w20, height=3.4)   # taller: the seam above stays
            left = joint_lines(doc2, 4.0)
            self.assertTrue(left)
            self.assertGreater(min(min(s[0][1], s[1][1]) for s in left), 2.8 - 1e-3)
            doc2.modified = False
        finally:
            doc.modified = False


class ElementTypesSaved(unittest.TestCase):
    """0.414 (the owner: «quero todos os elementos IFC tenham tipo, guardado e aplicado a outros elementos»): a
    parametric surface's type saved (its form, modifiers, construction, use — not its curves), applied to another
    surface (it takes them, keeps its own curves, becomes a roof as the type says), the first changed and «Atualizar o
    tipo»: the other follows; none again: values kept; one undo step each; kept in the IFC, valid."""

    def test_surface_types(self):
        from arqbim.core import curves as cc
        from arqbim.core import surface_build as sb
        from arqbim.core.mesh import PolyMesh
        from arqbim.model import element_types, surface_edits
        from arqbim.model.document import AddObject, SketchObject
        doc = Document()

        def ring(cx, r, z):
            curve = {"kind": "arc", "centre": [cx, 5.0, z], "normal": [0, 0, 1], "start": [cx + r, 5.0, z],
                     "angle": 360.0, "segments": 32}
            pts = cc.curve_points(curve)
            sk = SketchObject("anel", np.eye(4), PolyMesh(pts, [], lines=[(k, (k + 1) % len(pts))
                                                                          for k in range(len(pts))]), curve=curve)
            doc.execute(AddObject(sk, "add"))
            return sk.id

        a = bim.surface_from_sketches(doc, [(ring(5.0, r, z), None) for r, z in ((5.0, 3.0), (2.0, 6.0))],
                                      build={"gridshell": dict(sb.TEMPLATES["gridshell"])})
        b = bim.surface_from_sketches(doc, [(ring(20.0, r, z), None) for r, z in ((4.0, 3.0), (1.5, 5.0))])
        self.assertTrue(element_types.has_types(doc, a))
        self.assertIsNone(doc.ifc.element_type_of(a))
        bim.set_param_surface(doc, a, surface_edits.apply_action(doc.ifc.surface_definition(a), "surface_mod_add",
                                                                  "twist"), usage="cobertura")
        kind_a = doc.ifc.by_guid(a).is_a()
        made = element_types.save_type(doc, a, "Cobertura torcida")
        self.assertEqual(doc.ifc.element_type_of(a), made)
        self.assertEqual(element_types.types_of(doc, "param_surface"), [(made, "Cobertura torcida")])
        self.assertTrue(doc.ifc.by_guid(made).is_a("IfcRoofType") and kind_a == "IfcRoof")
        self.assertNotIn("curves", doc.ifc.element_type_values(made)["definition"])
        with self.assertRaises(ValueError):                              # (a name already used)
            element_types.save_type(doc, a, "cobertura torcida")
        # applied to the other: its form, twist and gridshell, a roof — its own curves (around x = 20) kept
        curves_b = doc.ifc.surface_definition(b)["curves"]
        self.assertEqual(element_types.apply_type(doc, [b], made), [b])
        db = doc.ifc.surface_definition(b)
        self.assertEqual(db["curves"], curves_b)
        self.assertEqual([m["op"] for m in db["modifiers"]], ["twist"])
        self.assertIn("gridshell", db["build"])
        self.assertTrue(doc.ifc.by_guid(b).is_a("IfcRoof") and doc.ifc.element_type_of(b) == made)
        self.assertFalse(element_types.differs(doc, b))
        doc.undo()                                                       # (one step)
        self.assertNotIn("gridshell", doc.ifc.surface_definition(b).get("build") or {})
        self.assertIsNone(doc.ifc.element_type_of(b))
        doc.redo()
        # the first changed by hand, «Atualizar o tipo»: the other follows
        d = surface_edits.apply_action(doc.ifc.surface_definition(a), "surface_mod:0:angle", "60*v")
        bim.set_param_surface(doc, a, d)
        self.assertTrue(element_types.differs(doc, a))
        self.assertEqual(sorted(element_types.update_type(doc, a)), sorted([a, b]))
        self.assertEqual(doc.ifc.surface_definition(b)["modifiers"][0]["angle"], "60*v")
        self.assertFalse(element_types.differs(doc, a))
        # none: tied to no type, its values kept
        element_types.apply_type(doc, [b], None)
        self.assertIsNone(doc.ifc.element_type_of(b))
        self.assertEqual(doc.ifc.surface_definition(b)["modifiers"][0]["angle"], "60*v")
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        path = os.path.join(tempfile.mkdtemp(), "tipos.ifc")
        doc.save(path)
        again = Document()
        again.open(path)
        self.assertEqual(again.ifc.element_types("param_surface"), [(made, "Cobertura torcida")])
        self.assertEqual(again.ifc.element_type_of(a), made)
        # its use changed by hand (a roof no more): its type let go — IFC4 wants an IfcRoofType on roofs only
        bim.set_param_surface(again, a, usage="estrutura")
        self.assertIsNone(again.ifc.element_type_of(a))
        self.assertEqual(again.ifc.validate(express_rules=True), [])

    def test_other_kinds_types(self):
        """0.415 — the other elements that had no types: a floor finish, a ceiling, a wall's tiles, a stair, a ramp, a
        curtain wall, a cabinet — each pair: the first changed, its type saved, applied to the second: the second takes
        what is the type's (a finish, a style, a width, a spacing…) and keeps what is its own (its outline, its height,
        its length); a valid IFC with IfcCoveringType, IfcStairType… on them."""
        from arqbim.core import cabinets as core_cab
        from arqbim.model import element_types
        doc = Document()
        floors = [bim.add_flooring(doc, [(x, 0), (x + 4, 0), (x + 4, 3), (x, 3)]) for x in (0.0, 10.0)]
        bim.set_flooring(doc, floors[0], "madeira")
        ceilings = [bim.add_ceiling(doc, [(x, 0), (x + 4, 0), (x + 4, 3), (x, 3)]) for x in (0.0, 10.0)]
        bim.set_ceiling(doc, ceilings[0], style="tiles", gap=0.05)
        wall = bim.add_wall(doc, np.array((0.0, -5.0, 0.0)), np.array((6.0, -5.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        tiles = [bim.add_cladding(doc, wall, side, "azulejo", 1.2) for side in (1, -1)]
        bim.set_cladding(doc, tiles[0], finish="pedra")
        spec = catalog.BY_KEY["laje_15"]
        stairs = [bim.add_stair(doc, np.array((x, 10.0, 0.0)), (0.0, 1.0), spec, rise=2.8) for x in (0.0, 10.0)]
        bim.set_stair(doc, stairs[0], width=1.3, going=0.30)
        ramps = [bim.add_ramp(doc, np.array((x, 20.0, 0.0)), np.array((x + 6.0, 20.0, 0.0)), spec, 1.2, 0.5)
                 for x in (0.0, 10.0)]
        bim.set_ramp(doc, ramps[0], width=1.6)
        cws = [bim.add_curtain_wall(doc, np.array((x, 30.0, 0.0)), np.array((x + 5.0, 30.0, 0.0)), embed=False)
               for x in (0.0, 10.0)]
        bim.set_curtain_wall(doc, cws[0], mullions=1.0, transoms=0.7)
        cabinets = [bim.add_cabinet(doc, np.array((x, 40.0, 0.0)), 0.0, core_cab.Cabinet.of("base")) for x in (0.0, 10.0)]
        bim.set_cabinet(doc, cabinets[0], width=0.9, finish="oak")
        pairs = {"flooring": floors, "ceiling": ceilings, "cladding": tiles, "stair": stairs, "ramp": ramps,
                 "curtain_wall": cws, "cabinet": cabinets}
        for kind, (first, second) in pairs.items():
            self.assertEqual(doc.ifc.kind_of(first), kind)
            made = element_types.save_type(doc, first, "Tipo " + kind)
            element_types.apply_type(doc, [second], made)
            self.assertEqual(doc.ifc.element_type_of(second), made, kind)
            self.assertEqual(element_types.KINDS[kind].values(doc.ifc, second),
                             element_types.KINDS[kind].values(doc.ifc, first), kind)
        # what stays each one's own: the second floor's outline, the second ramp's length, the second stair's rise
        self.assertAlmostEqual(min(x for x, _y in doc.ifc.ceiling_params(floors[1])["outline"]), 10.0)
        self.assertEqual(doc.ifc._params(doc.ifc.by_guid(floors[1]))["Acabamento"], "madeira")
        self.assertAlmostEqual(doc.ifc.stair_params(stairs[1])["width"], 1.3)
        self.assertAlmostEqual(doc.ifc.stair_params(stairs[1])["rise"], 2.8)
        self.assertAlmostEqual(doc.ifc.curtain_params(cws[1])["length"], 5.0)
        self.assertTrue(doc.ifc.by_guid(element_types.types_of(doc, "stair")[0][0]).is_a("IfcStairType"))
        self.assertTrue(doc.ifc.by_guid(element_types.types_of(doc, "flooring")[0][0]).is_a("IfcCoveringType"))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class ParamSurfacesIfc(unittest.TestCase):
    """0.395 — a parametric surface as an element: made of curves of the model (each followed: moved, the surface made
    again in the same step; Ctrl+Z takes both back), its use its class (the same element), its construction in its
    materials' colours, saved and read again (the links too), a valid IFC."""

    def test_surface_element(self):
        from arqbim.core import surface_build as sb
        from arqbim.core.mesh import PolyMesh
        from arqbim.model import surface_edits
        from arqbim.model.document import AddObject, ReplaceObjects, SketchObject
        doc = Document()
        try:
            def ring(r, z):
                curve = {"kind": "arc", "centre": [5.0, 5.0, z], "normal": [0, 0, 1], "start": [5.0 + r, 5.0, z],
                         "angle": 360.0, "segments": 32}
                from arqbim.core import curves as cc
                pts = cc.curve_points(curve)
                lines = [(k, (k + 1) % len(pts)) for k in range(len(pts))]
                sk = SketchObject("anel", np.eye(4), PolyMesh(pts, [], lines=lines), curve=curve)
                doc.execute(AddObject(sk, "add"))
                return sk.id
            ids = [ring(5.0, 3.0), ring(3.5, 6.0), ring(1.5, 8.0)]
            g = bim.surface_from_sketches(doc, [(i, None) for i in ids],
                                          build={"gridshell": dict(sb.TEMPLATES["gridshell"])})
            e = doc.ifc.by_guid(g)
            self.assertTrue(e.is_a("IfcBuildingElementProxy"))
            self.assertEqual(doc.ifc.kind_of(g), "param_surface")
            d = doc.ifc.surface_definition(g)
            self.assertEqual(d["surface"]["op"], "loft")
            self.assertTrue(all(c.get("source") for c in d["curves"]))
            self.assertIsNotNone(doc.get(g).mesh.colors)                        # (its pieces in their colours)
            self.assertIn("barra", doc.ifc.surface_summary(g)["families"])
            # an edit as the Properties make it: a twist, the panels
            d2 = surface_edits.apply_action(d, "surface_mod_add", "twist")
            d2 = surface_edits.apply_action(d2, "surface_build_add", "panels")
            d2 = surface_edits.apply_action(d2, "surface_build:panels:kind", "glass")
            d2 = surface_edits.apply_action(d2, "surface_mod:0:angle", "30*v")
            bim.set_param_surface(doc, g, d2)
            d3 = doc.ifc.surface_definition(g)
            self.assertEqual(d3["modifiers"][0]["angle"], "30*v")
            self.assertEqual(d3["build"]["panels"]["kind"], "glass")
            # the middle ring lifted: the surface follows, one step
            sk = doc.get(ids[1])
            moved = sk.copy()
            lift = np.eye(4)
            lift[2, 3] = 1.0
            moved.matrix = lift @ sk.matrix
            doc.execute(ReplaceObjects([sk], [moved], "move"))
            self.assertAlmostEqual(doc.ifc.surface_definition(g)["curves"][1]["points"][0][2], 7.0)
            doc.undo()
            self.assertAlmostEqual(doc.ifc.surface_definition(g)["curves"][1]["points"][0][2], 6.0)
            self.assertAlmostEqual(doc.get(ids[1]).matrix[2, 3], 0.0)
            doc.redo()
            self.assertAlmostEqual(doc.ifc.surface_definition(g)["curves"][1]["points"][0][2], 7.0)
            # its use: its class, the same element
            bim.set_param_surface(doc, g, usage="cobertura")
            self.assertTrue(doc.ifc.by_guid(g).is_a("IfcRoof"))
            self.assertEqual(doc.ifc.surface_usage(g), "cobertura")
            # a definition that cannot be: refused, the surface as it was
            bad = surface_edits.apply_action(doc.ifc.surface_definition(g), "surface_build:gridshell:mode", "pent")
            with self.assertRaises(ValueError):
                bim.set_param_surface(doc, g, bad)
            self.assertEqual(doc.ifc.surface_definition(g)["build"]["gridshell"]["mode"], "diagrid")
            # the control ring: a copy above, smaller
            new = bim.control_ring(doc, ids[2], 1.0, 0.5)
            from arqbim.model.surface_curves import sketch_chains
            pts = sketch_chains(doc.get(new))[0][0]
            self.assertAlmostEqual(float(pts[:, 2].mean()), 9.0, places=6)
            self.assertAlmostEqual(float(np.linalg.norm(pts[0, :2] - (5.0, 5.0))), 0.75, places=6)
            # saved and read again: the links too
            path = os.path.join(tempfile.mkdtemp(), "sup.ifc")
            doc.save(path)
            doc2 = Document()
            doc2.open(path)
            try:
                sks = [o for o in doc2.sketches() if getattr(o, "uid", None)]
                self.assertEqual(len(sks), 3)
                found = doc2.ifc.surfaces_following([o.uid for o in sks])
                self.assertEqual(list(found), [g])
                import ifcopenshell.validate
                log = ifcopenshell.validate.json_logger()
                ifcopenshell.validate.validate(doc2.ifc.file, log)
                self.assertEqual(log.statements, [])
            finally:
                doc2.modified = False
        finally:
            doc.modified = False


if __name__ == "__main__":
    unittest.main()
