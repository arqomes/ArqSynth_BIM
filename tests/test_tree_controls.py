"""(0.524) The Project navigator's controls (model/controls): kept in the IFC, undone, read again from a saved file, and
what each leaves out (drawings for «imprimir não», renders for «renderizar não»)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim, controls, drawings, render_scene  # noqa: E402
from arqbim.model.document import Document  # noqa: E402


class TreeControls(unittest.TestCase):

    def walls(self):
        doc = Document()
        a = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        b = bim.add_wall(doc, (0, 3, 0), (5, 3, 0), catalog.BY_KEY["parede_alv_20"])
        return doc, a, b

    def test_flags_in_the_ifc_and_undo(self):
        doc, a, b = self.walls()
        self.assertEqual(controls.state_of(doc, [a, b], "hidden"), False)
        self.assertEqual(controls.set_flag(doc, [a], "hidden", True), 1)
        self.assertEqual(controls.state_of(doc, [a, b], "hidden"), None)          # some: half lit
        self.assertEqual(controls.set_flag(doc, [a], "hidden", True), 0)          # already so
        controls.set_flag(doc, [a, b], "locked", True)
        self.assertEqual(controls.state_of(doc, [a, b], "locked"), True)
        self.assertEqual(doc.ifc.controls_of(a), {"hidden", "locked"})
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        controls.refresh(doc, [a, b])
        self.assertFalse(controls.has(doc, b, "locked"))
        self.assertTrue(controls.has(doc, a, "hidden"))
        controls.set_flag(doc, [a], "hidden", False)                              # the last flag: its pset goes
        self.assertEqual(doc.ifc.all_controls(), {})

    def test_read_again_from_a_file(self):
        doc, a, _b = self.walls()
        controls.set_flag(doc, [a], "no_print", True)
        controls.set_flag(doc, [a], "no_render", True)
        path = os.path.join(tempfile.mkdtemp(), "controlos.ifc")
        doc.ifc.file.write(path)
        import ifcopenshell
        from arqbim.ifc.model import IfcModel
        again = IfcModel.__new__(IfcModel)
        again.file = ifcopenshell.open(path)
        self.assertEqual(IfcModel.all_controls(again), {a: {"no_print", "no_render"}})

    def test_left_out_of_drawings_and_renders(self):
        doc, a, b = self.walls()
        storey = doc.active_storey
        self.assertEqual(len(drawings.plan(doc, storey, "P").cut), 2)
        controls.set_flag(doc, [a], "no_print", True)
        self.assertEqual(len(drawings.plan(doc, storey, "P").cut), 1)             # not printed: off the drawing
        whole = sum(len(g[2]) for g in render_scene.gather(doc, [doc.get(a), doc.get(b)]))
        controls.set_flag(doc, [a], "no_render", True)
        part = sum(len(g[2]) for g in render_scene.gather(doc, [doc.get(a), doc.get(b)]))
        self.assertLess(part, whole)                                               # not rendered: off the render
        self.assertGreater(part, 0)


class ChangeStorey(unittest.TestCase):
    """(0.527) An element put on another storey: up by the difference of levels, its door with it, one undo step."""

    def test_wall_with_its_door_to_the_storey_above(self):
        doc = Document()
        ground = doc.active_storey
        upper = bim.add_storey(doc, "Piso 1", 3.0)
        wall = bim.add_wall(doc, (0, 0, 0), (5, 0, 0), catalog.BY_KEY["parede_alv_20"])
        door = bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], bim.wall_frame(doc, wall), 2.0, -1)
        z0 = float(doc.get(wall).mesh.bounds()[0][2])
        moved = bim.change_storey(doc, [wall], upper)
        self.assertEqual(moved, [wall])
        self.assertEqual(doc.get(wall).storey, upper)
        self.assertAlmostEqual(float(doc.get(wall).mesh.bounds()[0][2]), z0 + 3.0, places=4)
        if door is not None:
            self.assertEqual(doc.get(door).storey, upper)
        self.assertEqual(bim.change_storey(doc, [wall], upper), [])          # already there
        doc.undo()
        self.assertEqual(doc.get(wall).storey, ground)
        self.assertAlmostEqual(float(doc.get(wall).mesh.bounds()[0][2]), z0, places=4)
        bim.change_storey(doc, [wall], upper, keep_height=True)              # only the storey
        self.assertEqual(doc.get(wall).storey, upper)
        self.assertAlmostEqual(float(doc.get(wall).mesh.bounds()[0][2]), z0, places=4)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


if __name__ == "__main__":
    unittest.main()
