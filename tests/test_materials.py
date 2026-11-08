"""(0.469) The materials' textures in the 3D view's Realistic style: an element's textured faces gathered by material,
their pictures' coordinates on the faces; the batches' textured meshes (made, left out for a selected element, gone
when the style shows none); the view styles' «textures» kept. (0.470) In the realistic render: a material's own look
kept in the scene (its pictures found, its faces' pictures' coordinates) and Mitsuba's material of it."""

import dataclasses
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "/tmp"), "arqbim_test_cache"))

import numpy as np  # noqa: E402
from PySide6 import QtGui, QtWidgets  # noqa: E402

APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from arqbim.core import pbr  # noqa: E402
from arqbim.ifc import catalog  # noqa: E402


def picture(folder, name="tijolo.png", top="#d02020", bottom="#2040d0", size=(32, 32)):
    """A picture: its top half one colour, its bottom half another."""
    path = os.path.join(folder, name)
    image = QtGui.QImage(*size, QtGui.QImage.Format.Format_RGB32)
    image.fill(QtGui.QColor(bottom))
    p = QtGui.QPainter(image)
    p.fillRect(0, 0, size[0], size[1] // 2, QtGui.QColor(top))
    p.end()
    image.save(path)
    return path


class Textured(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="arqsynth_tex_")
        self.path = picture(self.folder)
        self.old = catalog.MATERIALS["reboco"]
        look = dataclasses.replace(pbr.preset("matte").with_map("base", self.path), width=0.5, height_m=0.25)
        catalog.MATERIALS["reboco"] = dataclasses.replace(self.old, look=look)

    def tearDown(self):
        catalog.MATERIALS["reboco"] = self.old

    def test_groups(self):
        from arqbim.model import material_textures
        corners = np.array([[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0)],           # (a wall's face, y = 0)
                            [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0)]])          # (a floor)
        normals = np.array([(0.0, -1.0, 0.0), (0.0, 0.0, 1.0)])
        groups = material_textures.groups(corners, normals, ["reboco", "bloco"])
        self.assertEqual([g[0] for g in groups], ["reboco"])                 # (only the one with pictures)
        key, points, each, uv = groups[0]
        self.assertEqual((points.shape, each.shape, uv.shape), ((3, 3), (3, 3), (3, 2)))
        np.testing.assert_allclose(points[:, 1], -material_textures.LIFT, atol=1e-7)   # (a hair off the face)
        np.testing.assert_allclose(uv, [(0.0, 0.0), (2.0, 0.0), (2.0, 4.0)], atol=1e-6)   # (0,5 × 0,25 m pictures)
        self.assertEqual(material_textures.groups(corners, normals, ["bloco", "bloco"]), [])
        self.assertEqual(material_textures.groups(corners, normals, None), [])

    def test_batches(self):
        import pygfx as gfx
        from arqbim.core.mesh import TriMesh
        from arqbim.model import material_textures
        from arqbim.render.batches import BatchedElements, Piece
        made = []

        def factory(key):
            made.append(key)
            return gfx.MeshBasicMaterial(color="#ffffff")
        root = gfx.Group()
        bim = BatchedElements(root)
        bim.texture_factory = factory
        mesh = TriMesh([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)], [(0, 1, 2), (0, 2, 3)])
        piece = Piece(mesh, np.eye(4), (0.5, 0.5, 0.5, 1.0), (0.0, 0.0, 0.0, 1.0))
        tri = np.array([[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0)]])
        piece.textures = material_textures.groups(tri, [(0.0, 0.0, 1.0)], ["reboco"])
        bim.put("a", piece, "s")
        bim.flush()
        batch = bim.where["a"]
        self.assertEqual(list(batch.texture_meshes), ["reboco"])
        mesh_t = batch.texture_meshes["reboco"]
        self.assertIn(mesh_t, root.children)
        self.assertEqual(mesh_t.geometry.texcoords.data.shape, (3, 2))
        bim.hide_textures("a", True)                    # (selected: its highlight seen)
        self.assertTrue(bim.pending())
        bim.flush()
        self.assertEqual(batch.texture_meshes, {})
        self.assertNotIn(mesh_t, root.children)
        bim.hide_textures("a", False)
        bim.flush()
        self.assertEqual(list(batch.texture_meshes), ["reboco"])
        self.assertEqual(made, ["reboco"])                    # (its material made once…)
        bim.forget_textures()                                 # (…and again when the materials change)
        bim.flush()
        self.assertEqual(made, ["reboco", "reboco"])
        bim.set_visible(lambda key: False)
        self.assertFalse(batch.texture_meshes["reboco"].visible)
        plain = Piece(mesh, np.eye(4), (0.5, 0.5, 0.5, 1.0), (0.0, 0.0, 0.0, 1.0))
        bim.put("a", plain, "s")                              # (the style shows none: they go)
        bim.flush()
        self.assertEqual(batch.texture_meshes, {})

    def test_view_style(self):
        from arqbim.model import view_styles as vs
        self.assertTrue(vs.BUILTIN["realistic"].textures)
        self.assertFalse(vs.BUILTIN["shaded"].textures)
        mine = vs.new_from(vs.BUILTIN["realistic"], "Apresentação")
        again = vs.from_dict(vs.to_dict(mine))
        self.assertTrue(again.textures)
        self.assertFalse(vs.from_dict({"name": "Antigo"}).textures)


class WebTextures(unittest.TestCase):
    """0.471 — the owner: «Sim, liga» (Poly Haven's free textures in the Materials panel): its list and files read;
    the material made of a texture — its category, its pictures, its real size, a metal's metallic —; the panel's Web
    tab (offline: the list given, the pictures already in their folder): one click makes the material and gives it to
    the Paint bucket."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="arqsynth_tex_web_")
        self._folder = pbr.folder
        pbr.folder = lambda: self.folder

    def tearDown(self):
        pbr.folder = self._folder

    def test_rows_files_material(self):
        import json
        from arqbim.model import material_web
        text = json.dumps({
            "red_brick_03": {"name": "Red Brick 03", "categories": ["outdoor", "wall", "brick"],
                             "authors": {"Rob Tuytel": "All"}, "dimensions": [2000, 1000]},
            "blue_metal_plate": {"name": "Blue Metal Plate", "categories": ["metal", "collection: x"],
                                 "authors": {"A": "All"}, "dimensions": [1000, 1000]},
            "bad": "não é um"})
        rows = material_web.rows(text)
        self.assertEqual([r["name"] for r in rows], ["Blue Metal Plate", "Red Brick 03"])
        brick = rows[1]
        self.assertEqual((brick["dims"], brick["authors"]), ((2.0, 1.0), "Rob Tuytel"))
        self.assertTrue(brick["thumbnail"].startswith("https://cdn.polyhaven.com/") and "red_brick_03" in
                        brick["thumbnail"])
        self.assertEqual(rows[0]["categories"], ["metal"])                     # (its collections left out)
        self.assertEqual((material_web.category_of(brick), material_web.category_of(rows[0])), ("brick", "steel"))
        files = material_web.files(json.dumps({
            "Diffuse": {"1k": {"jpg": {"url": "https://x/d_1k.jpg"}}, "2k": {"jpg": {"url": "https://x/d_2k.jpg"}}},
            "nor_gl": {"2k": {"jpg": {"url": "https://x/n_2k.jpg"}}},
            "nor_dx": {"1k": {"jpg": {"url": "https://x/dx.jpg"}}},
            "arm": {"1k": {"jpg": {"url": "https://x/arm.jpg"}}}, "blend": {"1k": {"blend": {"url": "b"}}}}))
        self.assertEqual(files, {"base": "https://x/d_1k.jpg", "normal": "https://x/n_2k.jpg", "arm": "https://x/arm.jpg"})
        spec = material_web.material(brick, {"base": "/b.jpg", "roughness": "/r.jpg"}, (0.6, 0.3, 0.2), "Red Brick 03")
        self.assertEqual((spec.key, spec.name_pt, spec.category), ("m:new", "Red Brick 03", "brick"))
        self.assertEqual((spec.look.width, spec.look.height_m, spec.look.roughness), (2.0, 1.0, pbr.AS_PICTURE))
        self.assertEqual(spec.look.map("base"), ("/b.jpg", False))
        metal = material_web.material(rows[0], {"base": "/b.jpg", "metallic": "/m.png"}, (0.5, 0.5, 0.6), "Blue")
        self.assertEqual((metal.look.metallic, metal.finish), (pbr.AS_PICTURE, "metal"))

    def test_panel(self):
        from arqbim.model.document import Document
        from arqbim.ui.material_editor import MaterialEditor
        doc = Document()
        try:
            d = MaterialEditor(None, doc)
            saved, picked = [], []

            def save(spec, old):
                saved.append(spec)
                catalog.MATERIALS["m:" + spec.name_pt] = dataclasses.replace(spec, key="m:" + spec.name_pt)
                return "m:" + spec.name_pt
            d.on_save, d.on_pick = save, picked.append
            row = {"id": "red_brick_03", "name": "Tijolo Teste", "categories": ["brick", "wall"], "dims": (1.0, 0.5),
                   "authors": "Rob", "thumbnail": "", "page": "https://polyhaven.com/a/red_brick_03"}
            d._web_rows = [row]
            d.set_source("web")
            self.assertEqual([d.list.item(k).text() for k in range(d.list.count())], ["Tijolo Teste"])
            self.assertTrue(d.web_box.isVisibleTo(d) and not d.family.isVisibleTo(d))
            d.web_category.setCurrentIndex(d.web_category.findData("wood"))
            self.assertEqual(d.list.count(), 0)                                 # (by category)
            d.web_category.setCurrentIndex(0)
            folder = d.web_folder(row)                                         # (fetched before: in its folder)
            os.makedirs(folder)
            picture(folder, "base.jpg", "#b04020", "#b04020")
            picture(folder, "normal.jpg", "#8080ff", "#8080ff")
            d.list.itemClicked.emit(d.list.item(0))
            self.assertEqual(len(saved), 1)
            spec = saved[0]
            self.assertEqual((spec.name_pt, spec.category, spec.look.width, spec.look.height_m),
                             ("Tijolo Teste", "brick", 1.0, 0.5))
            self.assertEqual(sorted(s for s, _p, _i in spec.look.maps), ["base", "normal"])
            self.assertGreater(spec.color[0], spec.color[2])                   # (its colour: the picture's)
            self.assertEqual(picked, ["m:Tijolo Teste"])
            d.list.itemClicked.emit(d.list.item(0))                            # (made before: that one again)
            self.assertEqual((len(saved), picked[-1]), (1, "m:Tijolo Teste"))
            d.set_source("project")
            self.assertIn("Tijolo Teste", [d.list.item(k).text() for k in range(d.list.count())])
            d.deleteLater()
        finally:
            catalog.MATERIALS.pop("m:Tijolo Teste", None)
            doc.modified = False


class RenderLook(unittest.TestCase):
    """0.470 — a material's own realistic look in the realistic render: kept in the scene (its values, its pictures
    found, its faces' pictures' coordinates), read back; rendered by Mitsuba — a wall with a picture red on top, blue
    under: red high, blue low (the picture the right way up)."""

    def test_scene_and_render(self):
        import json
        import subprocess
        from arqbim.model import render_scene
        from arqbim.render import path_tracer
        folder = tempfile.mkdtemp(prefix="arqsynth_render_")
        path = picture(folder, size=(64, 64))
        look = dataclasses.replace(pbr.preset("matte").with_map("base", path), width=2.0, height_m=2.0)
        kept = render_scene.look_dict(look)
        self.assertEqual(kept["maps"], {"base": [path, False]})
        self.assertIsNone(kept["tint_rgb"])
        self.assertEqual(render_scene.look_dict(look.with_map("normal", "/nao/existe.png"))["maps"].keys(), {"base"})
        wall = np.array([[(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 0.0, 2.0)],
                         [(0.0, 0.0, 0.0), (2.0, 0.0, 2.0), (0.0, 0.0, 2.0)]], dtype=np.float32)
        uv = pbr.uv(wall.reshape(-1, 3), np.tile((0.0, -1.0, 0.0), (6, 1)), look).reshape(-1, 3, 2)
        scene = render_scene.RenderScene([("look:x", (0.8, 0.8, 0.8), wall)], eye=(1.0, -4.0, 1.0),
                                         target=(1.0, 0.0, 1.0), fov=40.0, sun=(0.2, -0.8, 0.55),
                                         lighting="sun", clean=False, looks={0: kept}, uvs={0: uv.astype(np.float32)})
        npz = os.path.join(folder, "cena.npz")
        scene.save(npz)
        again = render_scene.RenderScene.load(npz)
        self.assertEqual(again.looks, {0: json.loads(json.dumps(kept))})
        np.testing.assert_allclose(again.uvs[0], uv, atol=1e-6)
        try:
            import mitsuba  # noqa: F401
        except ImportError:
            self.skipTest("Mitsuba 3 is not installed")
        out = os.path.join(folder, "render.png")
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        done = subprocess.run(path_tracer.command(npz, out, 40, 40, 8), cwd=root, capture_output=True, text=True,
                              timeout=300, env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
        self.assertEqual(done.returncode, 0, done.stderr[-800:])
        image = QtGui.QImage(out)
        high, low = QtGui.QColor(image.pixel(20, 12)), QtGui.QColor(image.pixel(20, 28))
        self.assertGreater(high.red(), high.blue() + 30, (high.name(), low.name()))
        self.assertGreater(low.blue(), low.red() + 30, (high.name(), low.name()))
        # every picture a look may have, a clear coat, a light one: Mitsuba takes them all
        for kind in ("standard", "cloth", "emissive", "glass", "water"):
            full = dataclasses.replace(look, kind=kind, clearcoat=0.5, sheen=0.3, emission=800.0, roughness=0.5)
            for slot in pbr.SLOTS:
                full = full.with_map(slot, path, inverted=slot == "roughness")
            scene.looks = {0: render_scene.look_dict(full)}
            scene.save(npz)
            done = subprocess.run(path_tracer.command(npz, out, 16, 16, 2), cwd=root, capture_output=True, text=True,
                                  timeout=300, env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
            self.assertEqual(done.returncode, 0, (kind, done.stderr[-800:]))


if __name__ == "__main__":
    unittest.main()
