"""Batched display (render/batches.py), without a window or GPU: the bookkeeping only."""

import dataclasses
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arqbim.core.mesh import TriMesh  # noqa: E402
from arqbim.render import batches  # noqa: E402  (first: it makes pygfx load without uharfbuzz if blocked)

import pygfx as gfx  # noqa: E402

I4 = np.eye(4)
RED, BLACK, BLUE = (1.0, 0, 0, 1.0), (0, 0, 0, 1.0), (0, 0, 1.0, 1.0)


def box(x=0.0, size=1.0):
    """A cube as an IFC element would come from the geometry kernel (12 triangles)."""
    v = np.array([(x + i * size, j * size, k * size) for i in (0, 1) for j in (0, 1) for k in (0, 1)], float)
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    tris = [t for a, b, c, d in quads for t in ((a, b, c), (a, c, d))]
    return TriMesh(v, tris)


class Pieces(unittest.TestCase):
    def test_feature_edges_of_a_box(self):
        mesh = box()
        pairs, faces = mesh.edge_array()
        self.assertEqual(len(pairs), 12)                    # the 6 square faces' diagonals are not drawn
        self.assertTrue(np.all(faces >= 0) and mesh.is_closed())
        self.assertEqual(len(mesh.visible_edges()), 12)     # the dict form, for the inferences

    def test_piece_ready_for_the_gpu(self):
        p = batches.Piece(box(), I4, RED, BLACK)
        self.assertEqual((p.triangles, len(p.positions), len(p.edges)), (12, 36, 24))
        self.assertEqual(p.positions.dtype, np.float32)

    def test_plain_pieces_together(self):
        """0.344: many plain pieces made together are the same as one by one — positions, normals, faces, edges
        (lifted off their faces), colours, bounds —; an open mesh (a border edge) and an empty one among them."""
        open_mesh = TriMesh(np.array([(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0.5)], float), [[0, 1, 2], [1, 3, 2]])
        empty = TriMesh(np.zeros((0, 3)), np.zeros((0, 3), np.int64))
        cube = box(6.0)
        parts = TriMesh(cube.verts, cube.tris, colors=np.linspace(0.0, 1.0, 36).reshape(12, 3))   # (its own colours)
        meshes = [box(), open_mesh, parts, empty, box(3.0, 2.0)]
        colours = [RED, BLUE, None, RED, BLUE]
        together = batches.plain_pieces(meshes, colours, BLACK)
        for mesh, colour, p in zip([box(), open_mesh, parts, empty, box(3.0, 2.0)], colours, together):
            q = batches.Piece(mesh, I4, colour, BLACK)
            for name in ("positions", "normals", "owner", "edges", "pattern", "pattern_colors"):
                np.testing.assert_allclose(getattr(p, name), getattr(q, name), atol=1e-6, err_msg=name)
                self.assertEqual(getattr(p, name).dtype, getattr(q, name).dtype, name)
            if q.own is None:
                self.assertEqual((p.face_color, p.own), (q.face_color, None))
            else:
                np.testing.assert_allclose(p.own, q.own, atol=1e-6)
                np.testing.assert_allclose(p.face_color, q.face_color, atol=1e-6)
            self.assertEqual((p.edge_color, p.seams, p.triangles), (q.edge_color, q.seams, q.triangles))
        np.testing.assert_allclose(meshes[4].bounds()[1], (5.0, 2.0, 2.0))
        self.assertIsNone(meshes[3].bounds())
        self.assertEqual(batches.plain_pieces([], [], BLACK), [])


class Batches(unittest.TestCase):
    def setUp(self):
        self.root = gfx.Group()
        self.b = batches.BatchedElements(self.root)

    def test_one_batch_per_storey_and_pick_back(self):
        self.b.put("a", batches.Piece(box(0), I4, RED, BLACK), "terreo")
        self.b.put("b", batches.Piece(box(2), I4, RED, BLACK), "terreo")
        self.b.put("c", batches.Piece(box(4), I4, RED, BLACK), "piso1")
        self.b.flush()
        self.assertEqual(len(self.b.batches), 2)
        self.assertEqual(len(self.root.children), 6)        # mesh + lines + poché per batch, not per element
        self.assertFalse(any(b.poche.visible for b in self.b.batches))   # the poché is for plans only
        ground = self.b.where["b"]
        self.assertEqual(ground.pick(12 + 5), ("b", 5))     # triangle 17 of the batch = face 5 of "b"
        self.assertEqual(self.b.pick(ground.mesh, 3), ("a", 3))

    def test_big_models_are_split(self):
        old = batches.MAX_TRIANGLES
        batches.MAX_TRIANGLES = 30
        try:
            for k in range(6):
                self.b.put(k, batches.Piece(box(2 * k), I4, RED, BLACK), None)
            self.b.flush()
            self.assertEqual(len(self.b.batches), 3)        # 12 triangles each, at most 30 per batch
        finally:
            batches.MAX_TRIANGLES = old

    def test_many_batches_a_few_per_image(self):
        """0.328 — many batches changed at once (a file opened): with a time budget, at least one made now and the
        others left (pending) for the next images; with no budget, all; a few changed (an edit): all at once, whatever
        the budget."""
        for k in range(10):
            self.b.put(k, batches.Piece(box(2 * k), I4, RED, BLACK), "piso{}".format(k))
        self.assertTrue(self.b.flush(budget=0.0))
        made = [b for b in self.b.batches if not b.dirty]
        self.assertEqual(len(made), 1)
        self.assertTrue(self.b.pending())
        self.assertIsNone(self.b.batches[-1].mesh)            # (not drawn yet)
        self.assertFalse(self.b.flush())
        self.assertFalse(self.b.pending())
        for k in range(batches.FEW_BATCHES):
            self.b.put(k, batches.Piece(box(2 * k + 1), I4, RED, BLACK), "piso{}".format(k))
        self.assertFalse(self.b.flush(budget=0.0))            # (an edit: all in one image)
        self.assertFalse(self.b.pending())

    def test_recolour_while_a_piece_waits(self):
        """0.333 — an element's piece replaced by a bigger one (dressed by its materials, its colours by vertex) and,
        before its batch is made again, recoloured (selected): nothing written in the old place (they no longer fit:
        a ValueError since 0.328 left batches waiting for a few images); made again, its new colours in."""
        self.b.put("a", batches.Piece(box(0), I4, RED, BLACK), None)
        self.b.put("b", batches.Piece(box(2), I4, RED, BLACK), None)
        self.b.flush()
        two = TriMesh(np.concatenate((box(0).verts, box(0, 0.5).verts + (0, 0, 1.0))),
                      list(box(0).tris) + [tuple(int(i) + 8 for i in t) for t in box(0).tris])
        self.b.put("a", batches.Piece(two, I4, RED, BLACK), None)            # (72 vertices where it had 36)
        per_vertex = np.tile(np.array(BLUE, dtype=np.float32), (72, 1))
        self.b.recolor("a", per_vertex, BLACK)                                # (no error)
        self.b.flush()
        batch = self.b.where["a"]
        v0, nv, _e0, _ne = batch.ranges["a"]
        self.assertEqual(nv, 72)
        self.assertTrue(np.allclose(batch.mesh.geometry.colors.data[v0:v0 + nv], BLUE))
        v0, nv, _e0, _ne = batch.ranges["b"]
        self.assertTrue(np.allclose(batch.mesh.geometry.colors.data[v0:v0 + nv], RED))

    def test_own_colours_kept_through_a_selection(self):
        """0.259: an element with each triangle's own colour (half red, half blue): drawn so, by vertex; selected,
        all in the selection's colour; let go, its own colours back — next to a one-colour element, untouched;
        another piece added after it (written after the others) with its own colours too."""
        mesh = box(0)
        own = TriMesh(mesh.verts, mesh.tris, colors=[(1.0, 0.0, 0.0)] * 6 + [(0.0, 0.0, 1.0)] * 6)
        self.b.put("a", batches.Piece(own, I4, None, BLACK), None)
        self.b.put("b", batches.Piece(box(2), I4, RED, BLACK), None)
        self.b.flush()
        batch = self.b.where["a"]
        colours = batch.mesh.geometry.colors.data
        self.assertTrue(np.allclose(colours[:18, :3], (1.0, 0.0, 0.0)) and np.allclose(colours[18:36, :3], (0, 0, 1)))
        self.b.recolor("a", BLUE, BLACK)
        self.assertTrue(np.allclose(colours[:36], BLUE))
        self.b.recolor("a", None, BLACK)
        self.assertTrue(np.allclose(colours[:18, :3], (1.0, 0.0, 0.0)) and np.allclose(colours[18:36, :3], (0, 0, 1)))
        self.assertTrue(np.allclose(colours[36:72], RED))
        self.b.put("c", batches.Piece(TriMesh(box(4).verts, box(4).tris, colors=[(0.0, 0.0, 1.0)] * 12), I4, None,
                                      BLACK), None)
        self.b.flush()
        colours = self.b.where["c"].mesh.geometry.colors.data
        v0, nv, _e0, _ne = self.b.where["c"].ranges["c"]
        self.assertTrue(np.allclose(colours[v0:v0 + nv, :3], (0, 0, 1)))

    def test_selection_recolours_only_that_element(self):
        self.b.put("a", batches.Piece(box(0), I4, RED, BLACK), None)
        self.b.put("b", batches.Piece(box(2), I4, RED, BLACK), None)
        self.b.flush()
        self.b.recolor("b", BLUE, BLUE)
        colors = self.b.where["b"].mesh.geometry.colors.data
        self.assertTrue(np.allclose(colors[:36], RED) and np.allclose(colors[36:72], BLUE))
        self.assertFalse(self.b.where["a"].dirty)           # nothing rebuilt

    def test_an_edit_reuses_the_gpu_buffers(self):
        self.b.put("a", batches.Piece(box(0), I4, RED, BLACK), None)
        self.b.put("b", batches.Piece(box(2), I4, RED, BLACK), None)
        self.b.flush()
        batch = self.b.where["a"]
        geometry = batch.mesh.geometry
        self.assertEqual(geometry.indices.draw_range, (0, 24))     # 24 triangles drawn, the rest is room
        self.b.put("a", batches.Piece(box(0, size=2.0), I4, RED, BLACK), None)   # same size: same buffers
        self.b.remove("b")
        self.b.flush()
        self.assertIs(batch.mesh.geometry, geometry)
        self.assertEqual(geometry.indices.draw_range, (0, 12))
        self.assertEqual(batch.lines.geometry.positions.draw_range, (0, 24))
        self.assertAlmostEqual(float(geometry.positions.data[:36, 0].max()), 2.0)
        self.assertTrue(np.allclose(geometry.positions.data[36:], geometry.positions.data[0]))   # room: unused
        for k in range(3):                                         # more than the room: bigger buffers
            self.b.put("c{}".format(k), batches.Piece(box(4 + 2 * k), I4, RED, BLACK), None)
        self.b.flush()
        self.assertIsNot(batch.mesh.geometry, geometry)
        self.assertEqual(batch.mesh.geometry.indices.draw_range, (0, 48))

    def test_new_pieces_are_written_after_the_others(self):
        for k in range(4):
            self.b.put(k, batches.Piece(box(2 * k), I4, RED, BLACK), None)
        self.b.flush()
        batch = self.b.where[0]
        geometry = batch.mesh.geometry                                  # 144 vertices used, room for 186
        self.b.put("e", batches.Piece(box(8), I4, BLUE, BLACK), None)    # only added: no full rebuild
        self.b.flush()
        self.assertIs(batch.mesh.geometry, geometry)
        self.assertEqual(geometry.indices.draw_range, (0, 60))
        self.assertEqual(batch.ranges["e"], (144, 36, 96, 24))
        self.assertTrue(np.allclose(geometry.colors.data[144:180], BLUE))
        self.assertEqual(batch.pick(48 + 5), ("e", 5))
        self.b.recolor("e", RED, RED)
        self.assertTrue(np.allclose(geometry.colors.data[144:180], RED))

    def test_recolour_while_pieces_are_being_added(self):
        """0.96: an element recoloured after another was added to its batch (not rebuilt yet): its colour is in
        the buffer after the rebuild, which only adds the new one after the others."""
        for k in range(4):
            self.b.put(k, batches.Piece(box(2 * k), I4, RED, BLACK), None)
        self.b.flush()
        geometry = self.b.where[0].mesh.geometry                        # (room for more after the 4)
        self.b.put("e", batches.Piece(box(8), I4, RED, BLACK), None)       # (dirty: to be appended)
        self.b.recolor(0, BLUE, BLUE)
        self.b.flush()
        self.assertIs(self.b.where[0].mesh.geometry, geometry)            # (appended: not made again)
        self.assertTrue(np.allclose(geometry.colors.data[:36], BLUE))

    def test_edit_and_remove_rebuild_only_their_batch(self):
        self.b.put("a", batches.Piece(box(0), I4, RED, BLACK), "terreo")
        self.b.put("c", batches.Piece(box(4), I4, RED, BLACK), "piso1")
        self.b.flush()
        upstairs = self.b.where["c"].mesh
        self.b.put("a", batches.Piece(box(0, size=2.0), I4, RED, BLACK), "terreo")
        self.b.remove("c")
        self.b.flush()
        self.assertEqual(len(self.b.batches), 1)            # the empty storey batch is gone
        self.assertNotIn(upstairs, self.root.children)
        self.assertAlmostEqual(float(self.b.where["a"].mesh.geometry.positions.data[:, 0].max()), 2.0)

    def test_plan_cuts_and_fills_what_is_cut(self):
        self.b.put("a", batches.Piece(box(0), I4, RED, BLACK), "terreo")
        self.b.flush()
        batch = self.b.where["a"]
        self.b.set_cut(True, [(0.0, 0.0, -1.0, -0.5)], (0.0, 0.0, 0.01))
        self.assertEqual(self.b.face_material.side, "front")
        self.assertTrue(batch.poche.visible and batch.poche.geometry is batch.mesh.geometry)
        self.assertEqual(self.b.poche_material.clipping_planes[0][2:], (-1.0, -0.5))
        self.assertTrue(np.allclose(batch.poche.local.position, (0.0, 0.0, 0.01)))
        self.assertEqual(self.b.pick(batch.poche, 3), ("a", 3))         # clicking what is cut picks it
        self.b.set_cut(False)
        self.assertEqual((self.b.face_material.side, batch.poche.visible), ("both", False))
        self.assertEqual(self.b.face_material.clipping_planes, [])

    def test_hide_a_storey(self):
        self.b.put("a", batches.Piece(box(0), I4, RED, BLACK), "terreo")
        self.b.put("c", batches.Piece(box(4), I4, RED, BLACK), "piso1")
        self.b.flush()
        self.b.set_visible(lambda storey: storey == "piso1")
        self.assertEqual((self.b.is_visible("a"), self.b.is_visible("c")), (False, True))


class ViewCube(unittest.TestCase):
    """The view cube's clicks (render/viewcube.py, 0.81): a ray cast at the cube and its ring."""

    def setUp(self):
        from arqbim.render import viewcube
        self.vc = viewcube
        names = ("top", "bottom", "front", "back", "right", "left", "ring", "home", "roll_ccw", "roll_cw", "menu",
                 "arrow")
        self.cube = viewcube.ViewCube({n: np.zeros((8, 8, 4), np.uint8) for n in names})
        self.size = (800, 600)

    def look(self, eye, up=(0.0, 0.0, 1.0)):
        cam = gfx.PerspectiveCamera(45)
        cam.local.position = eye
        cam.show_pos((0.0, 0.0, 0.0), up=up)
        self.cube.follow(cam.local.rotation)

    def at(self, p):
        """Where a point of the cube's scene is in the view."""
        rx, ry, rw, rh = self.cube.rect(self.size)
        c = np.asarray(self.cube.camera.camera_matrix, float) @ np.append(np.asarray(p, float), 1.0)
        return rx + (c[0] / c[3] + 1) / 2 * rw, ry + (1 - c[1] / c[3]) / 2 * rh

    def hit(self, p):
        return self.cube.hit(*self.at(p), self.size)

    def test_from_above(self):
        self.look((0.0, 0.0, 10.0), up=(0.0, 1.0, 0.0))
        mid = (self.vc.RING_IN + self.vc.RING_OUT) / 2
        self.assertEqual(self.hit((0.0, 0.0, 0.5)), ("cube", (0.0, 0.0, 1.0)))         # TOPO
        self.assertEqual(self.hit((0.45, 0.45, 0.5)), ("cube", (1.0, 1.0, 1.0)))       # its corner
        self.assertEqual(self.hit((0.0, 0.45, 0.5)), ("cube", (0.0, 1.0, 1.0)))        # its edge
        self.assertEqual(self.hit((0.0, mid, self.vc.RING_Z)), ("compass", (0.0, 1.0)))   # N
        self.assertEqual(self.hit((mid * 0.7, mid * 0.7, self.vc.RING_Z)), ("ring",))     # between N and E
        self.assertIsNone(self.cube.hit(10, 300, self.size))                          # elsewhere in the view
        self.assertTrue(self.cube.square)                                             # its triangles shown
        rx, ry, _w, _h = self.cube.rect(self.size)
        bx, by, bw, bh = self.cube.buttons["up"][1]
        self.assertEqual(self.cube.hit(rx + bx + bw / 2, ry + by + bh / 2, self.size), ("button", "up"))
        self.assertEqual(self.cube.seen, {"top"})
        self.assertEqual(len(self.cube.outline.geometry.positions.data), 8)         # its 4 edges only

    def test_from_a_corner(self):
        self.look((5.0, -5.0, 5.0))
        self.assertFalse(self.cube.square)                   # no triangles nor roll arrows
        self.assertEqual(self.cube.seen, {"top", "front", "right"})
        self.assertEqual(len(self.cube.outline.geometry.positions.data), 18)        # 9 edges: the 3 hidden ones not
        rx, ry, _w, _h = self.cube.rect(self.size)
        bx, by, bw, bh = self.cube.buttons["roll_cw"][1]
        self.assertNotEqual(self.cube.hit(rx + bx + bw / 2, ry + by + bh / 2, self.size), ("button", "roll_cw"))
        self.assertEqual(self.hit((0.5, -0.5, 0.5)), ("cube", (1.0, -1.0, 1.0)))
        self.assertEqual(self.hit((0.5, 0.0, 0.0)), ("cube", (1.0, 0.0, 0.0)))         # DIREITA
        lit = self.cube.faces["top"].material.color, self.cube.faces["right"].material.color
        self.assertGreater(lit[0].r, lit[1].r)               # the top lighter than the side


class DarkCanvas(unittest.TestCase):
    """0.341 — the dark views' colours: on the light canvas every colour as it is; on the dark one a grey turned over
    (black → light, white → nearly the background, a mid grey about as it was), a dark colour lightened with its hue
    (the grid's blue), a colour as it is (the selection's blue, brick); "#rrggbb", tuples and arrays alike; the
    batches' poché and hidden-line faces follow; a piece's own colours turned over when asked."""

    def tearDown(self):
        from arqbim.render import canvas
        canvas.set_dark(False)

    def test_ink(self):
        from arqbim.render import canvas
        self.assertFalse(canvas.set_dark(False))
        self.assertEqual(canvas.ink("#202020"), "#202020")
        self.assertTrue(canvas.set_dark(True))
        self.assertEqual(canvas.background(), canvas.BACKGROUNDS[True])
        black, white = gfx.Color(canvas.ink("#000000")), gfx.Color(canvas.ink("#ffffff"))
        self.assertGreater(black.r, 0.9)
        self.assertLess(white.r, 0.15)
        self.assertAlmostEqual(gfx.Color(canvas.ink("#808080")).r, 0.5, delta=0.05)
        self.assertEqual(canvas.ink("#1f5fd6"), "#1f5fd6")                  # (the selection's blue)
        self.assertEqual(canvas.ink("#c97a5c"), "#c97a5c")                  # (brick)
        grid = gfx.Color(canvas.ink("#4a6a8a"))
        self.assertGreater((max(grid.rgb) + min(grid.rgb)) / 2, 0.55)
        self.assertGreater(grid.b, grid.r)                                   # (still blue)
        turned = canvas.ink((0.0, 0.0, 0.0, 0.4))
        self.assertEqual(len(turned), 4)
        self.assertAlmostEqual(turned[3], 0.4)
        self.assertGreater(turned[0], 0.9)
        rgb = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [0.79, 0.48, 0.36], [0.29, 0.42, 0.54]])
        np.testing.assert_allclose(canvas.ink_array(rgb), [canvas.ink(tuple(c)) for c in rgb], atol=1e-3)

    def test_batches(self):
        from arqbim.render import canvas
        elements = batches.BatchedElements(gfx.Group())
        self.assertEqual(gfx.Color(elements.poche_material.color).hex, gfx.Color(batches.POCHE_COLOR).hex)
        canvas.set_dark(True)
        elements.set_canvas(True)
        self.assertGreater(gfx.Color(elements.poche_material.color).r, 0.6)            # (the cut: light)
        self.assertLess(gfx.Color(elements.face_materials["hidden"].color).r, 0.2)    # (white faces: dark)
        elements.set_canvas(False)                                                     # (the 3D view: as on paper)
        self.assertEqual(gfx.Color(elements.face_materials["hidden"].color).hex, "#ffffff")
        mesh = box()
        _tris, owner = mesh.triangulate()
        mesh.colors = np.ones((len(owner), 3))                             # (white parts, as a railing's own)
        plain = batches.Piece(mesh, I4, None, BLACK)
        turned = batches.Piece(mesh, I4, None, BLACK, turned=True)
        self.assertAlmostEqual(float(plain.own[0, 0]), 1.0)
        self.assertLess(float(turned.own[0, 0]), 0.05)                     # (physical: the dark grey's)


class RealisticRender(unittest.TestCase):
    """0.343 — the realistic render's scene and its process: the test house's faces by finish — its windows' glass,
    its walls matte, its door satin (wood), the ground —, kept in a file and read back the same; the tone mapping (a
    mid grey's picture mid grey, a stray bright pixel calmed); a tiny render by Mitsuba 3 in its own process: the
    picture and its progress written, the sky over a ground."""

    def _house(self):
        from arqbim.model.document import Document
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
        from casa_exemplo import build_house
        doc = Document()
        build_house(doc)
        return doc

    def test_scene(self):
        import tempfile
        from arqbim.model import bim, render_scene
        doc = self._house()
        panel = bim.add_light(doc, (2.0, 2.0), "panel")
        bim.add_light(doc, (4.0, 2.0), "downlight")
        camera = {"eye": (-6.0, -9.0, 4.0), "target": (3.0, 2.0, 1.2), "fov": 40.0}
        scene = render_scene.scene_of(doc, list(doc.objects.values()), camera, (0.3, -0.5, 0.8), "night", -1.0)
        finishes = {f for f, _c, _t in scene.groups}
        self.assertTrue({"glass", "matte", "satin"} <= finishes, finishes)
        self.assertAlmostEqual(float(np.linalg.norm(scene.sun)), 1.0)
        self.assertIsNotNone(scene.ground)
        self.assertGreaterEqual(scene.ground[1], render_scene.GROUND_LEAST)
        # (0.343) the lights' faces that shine down, as bright as their flux over them: a 60 × 60 panel's 3600 lm
        self.assertEqual(len(scene.lights), 2)
        lum, faces = min(scene.lights, key=lambda x: x[0])
        self.assertAlmostEqual(lum, 3600.0 / (math.pi * 0.595 * 0.595), delta=30.0)
        self.assertTrue(np.all(faces[:, :, 2] < doc.get(panel).mesh.bounds()[0][2]))      # (just under it)
        self.assertGreater(max(x[0] for x in scene.lights), lum)                           # (the downlight brighter)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cena.npz")
            scene.save(path)
            back = render_scene.RenderScene.load(path)
        self.assertEqual([(f, c) for f, c, _t in back.groups], [(f, tuple(c)) for f, c, _t in scene.groups])
        self.assertEqual(back.triangles, scene.triangles)
        self.assertEqual((back.eye, back.fov), (scene.eye, 40.0))
        self.assertEqual([x[0] for x in back.lights], [x[0] for x in scene.lights])
        self.assertEqual((back.lighting, back.exposure, back.clean), ("night", -1.0, True))
        self.assertEqual(render_scene.finish_of("glass", 0.4), "glass")
        self.assertEqual(render_scene.finish_of("glass", 0.7), "frosted")
        self.assertEqual(render_scene.finish_of("steel", 1.0), "metal")
        self.assertEqual(render_scene.finish_of(None, 1.0), "matte")
        self.assertEqual(render_scene.finish_of("concrete", 1.0, "glossy"), "glossy")      # (the material's own)
        # (0.343) a material's own finish on its faces: the walls' plaster made glossy
        from arqbim.ifc import catalog
        from arqbim.model import project_types
        plaster = catalog.MATERIALS["reboco"]
        bim.save_material(doc, dataclasses.replace(plaster, finish="glossy"), plaster)
        catalog.set_project(project_types.read(doc.ifc), project_types.materials(doc.ifc))   # (as the window does)
        self.addCleanup(catalog.set_project, [])
        self.assertEqual(catalog.MATERIALS["reboco"].finish, "glossy")
        groups = render_scene.gather(doc, list(doc.objects.values()))
        self.assertIn(("glossy", tuple(np.round(np.asarray(plaster.color) * 255.0) / 255.0)),
                      {(f, tuple(c)) for f, c, _t in groups})

    def test_tone(self):
        from arqbim.render import path_tracer
        grey = np.full((20, 30, 3), 0.18)
        out = path_tracer.tone(grey)
        self.assertEqual(out.shape, (20, 30, 3))
        self.assertTrue(120 < int(out[10, 10, 0]) < 160)              # (mid grey, through the filmic curve: 141)
        hot = grey.copy()
        hot[5, 5] = 500.0                                               # (a stray bright pixel)
        self.assertLess(int(path_tracer.tone(hot)[5, 5, 0]), 200)
        np.testing.assert_allclose(path_tracer.linear([0.0, 1.0]), [0.0, 1.0])
        lamp = grey.copy()
        lamp[4:8, 4:8] = 500.0                                          # (a lamp's face: bright with its neighbours)
        self.assertEqual(int(path_tracer.tone(lamp)[5, 5, 0]), 255)
        self.assertLess(int(path_tracer.tone(grey, -1.0)[10, 10, 0]), int(out[10, 10, 0]))   # (exposure −1 EV)
        dark = np.full((20, 30, 3), 1e-6)                               # (night: no lighter than NIGHT_KEY)
        self.assertLess(int(path_tracer.tone(dark, 0.0, 1e-4)[10, 10, 0]), 20)

    def test_clean(self):
        """(0.343) The grain filter: a grainy wall over a floor (two faces, two colours) smoothed, the edge between
        them kept, its light kept; what shows the sky and the glass left as rendered."""
        from arqbim.render import path_tracer
        rng = np.random.default_rng(3)
        h, w = 40, 60
        albedo = np.zeros((h, w, 3))
        albedo[:20] = (0.8, 0.8, 0.8)
        albedo[20:] = (0.2, 0.3, 0.2)
        normal = np.zeros((h, w, 3))
        normal[:20, :, 1] = 1.0
        normal[20:, :, 2] = 1.0
        depth = np.full((h, w), 5.0)
        depth[:, :5] = 0.0                                              # (the sky)
        albedo[:, 50:] = 0.0                                            # (glass)
        truth = np.where(albedo > 0.0, albedo, 0.3) * 0.5
        noisy = truth * rng.gamma(4.0, 0.25, (h, w, 1))                 # (its grain: ±50 %)
        lum = 0.2126 * truth[..., 0] + 0.7152 * truth[..., 1] + 0.0722 * truth[..., 2]
        cleaned = path_tracer.clean(noisy, (0.5 * lum) ** 2, albedo, normal, depth)
        wall, floor = cleaned[2:17, 8:47, 1], cleaned[23:38, 8:47, 1]
        self.assertLess(float(wall.std() / wall.mean()), 0.15)
        self.assertLess(float(floor.std() / floor.mean()), 0.15)
        self.assertAlmostEqual(float(wall.mean()), 0.4, delta=0.04)
        self.assertAlmostEqual(float(floor.mean()), 0.15, delta=0.02)
        self.assertAlmostEqual(float(cleaned[19, 8:47, 1].mean()), 0.4, delta=0.06)        # (the edge kept)
        self.assertAlmostEqual(float(cleaned[20, 8:47, 1].mean()), 0.15, delta=0.03)
        np.testing.assert_allclose(cleaned[:, :5], noisy[:, :5], rtol=1e-5)                 # (the sky…)
        np.testing.assert_allclose(cleaned[:, 50:], noisy[:, 50:], rtol=1e-5)               # (…the glass)

    def test_render(self):
        import subprocess
        import tempfile
        from arqbim.model import render_scene
        from arqbim.render import path_tracer
        try:
            import mitsuba  # noqa: F401
        except ImportError:
            self.skipTest("Mitsuba 3 is not installed")
        doc = self._house()
        camera = {"eye": (-6.0, -9.0, 3.0), "target": (3.0, 2.0, 2.5), "fov": 50.0}
        scene = render_scene.scene_of(doc, list(doc.objects.values()), camera, (0.3, -0.5, 0.8))
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as tmp:
            path, picture = os.path.join(tmp, "cena.npz"), os.path.join(tmp, "render.png")
            scene.save(path)
            env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
            done = subprocess.run(path_tracer.command(path, picture, 96, 54, 4), cwd=root, env=env,
                                  capture_output=True, text=True, timeout=300)
            self.assertEqual(done.returncode, 0, done.stderr[-800:])
            import json
            with open(picture + ".json", encoding="utf-8") as fh:
                state = json.load(fh)
            self.assertTrue(state["finished"])
            self.assertEqual(state["samples"], 4)
            from PySide6 import QtGui
            image = QtGui.QImage(picture)
            self.assertEqual((image.width(), image.height()), (96, 54))
            sky, ground = QtGui.QColor(image.pixel(48, 2)), QtGui.QColor(image.pixel(48, 52))
            self.assertGreater(sky.blue(), sky.red())                  # (the sky blue over the ground)
            # (0.343) at night, inside, looking up at a light: it shines, the ceiling round it lit by it
            from arqbim.model import bim
            bim.add_light(doc, (2.0, 2.0), "panel")
            up = {"eye": (2.0, 2.0, 1.0), "target": (2.0, 2.0, 3.0), "up": (0.0, 1.0, 0.0), "fov": 60.0}
            scene = render_scene.scene_of(doc, list(doc.objects.values()), up, (0.3, -0.5, 0.8), "night")
            scene.save(path)
            done = subprocess.run(path_tracer.command(path, picture, 96, 54, 8), cwd=root, env=env,
                                  capture_output=True, text=True, timeout=300)
            self.assertEqual(done.returncode, 0, done.stderr[-800:])
            image = QtGui.QImage(picture)
            lamp, ceiling = QtGui.QColor(image.pixel(48, 27)), QtGui.QColor(image.pixel(4, 4))
            self.assertGreater(lamp.lightness(), 230)
            self.assertGreater(ceiling.lightness(), 10)
            self.assertLess(ceiling.lightness(), lamp.lightness())


if __name__ == "__main__":
    unittest.main()
