"""(0.313) Widgets checked without showing a window (Qt off screen): the types' miniatures and the type chosen on top
of the Properties panel, in the contextual bar and in the type editor's list — (0.314) the materials' graphics and
their cuts on paper, (0.315) the drawings by their view's style."""

import dataclasses
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"          # (no window on the screen, whatever the other tests use)
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "/tmp"), "arqbim_test_cache"))

import numpy as np  # noqa: E402
from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402

APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import Document  # noqa: E402
from arqbim.ui import type_thumbs  # noqa: E402


def pump():
    for _ in range(5):
        APP.processEvents()


def tearDownModule():
    """(0.318) Every window these tests made closed and deleted while Qt is still there: left to Python's own clean-up
    at the end, so many of them crashed the process once everything had passed (segmentation fault)."""
    for widget in QtWidgets.QApplication.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete.value)
    pump()


def inked(pixmap):
    """How many of a picture's pixels are drawn (not transparent)."""
    image = pixmap.toImage()
    return sum(image.pixelColor(x, y).alpha() > 0 for x in range(0, image.width(), 2) for y in range(0, image.height(), 2))


class TypeMiniatures(unittest.TestCase):
    """0.313 — every type of the catalogue has its miniature (a door's, a wall's layers, a column's section, a pipe's…),
    made once."""

    def test_every_type(self):
        for spec in list(catalog.types()) + list(catalog.openings()):
            pic = type_thumbs.icon(spec).pixmap(type_thumbs.LIST_SIZE, type_thumbs.LIST_SIZE)
            self.assertFalse(pic.isNull(), spec.key)
            self.assertGreater(inked(pic), 20, spec.key)
        spec = catalog.OPENING_BY_KEY["janela_120"]
        self.assertIs(type_thumbs.icon(spec), type_thumbs.icon(spec))                  # (kept)


class TypeOnTop(unittest.TestCase):
    """0.313 — the Properties panel's type on top, under the name, as Revit's Type Selector: a list of the types with
    their miniatures; chosen there, the element's type changes; several elements: theirs, blank if it differs, none if
    they are of different kinds."""

    @classmethod
    def setUpClass(cls):
        from arqbim.ui.properties import PropertiesPanel
        cls.doc = doc = Document()
        cls.wall = bim.add_wall(doc, (0.0, 0.0, 0.0), (8.0, 0.0, 0.0), catalog.BY_KEY["parede_alv_20"])
        cls.other = bim.add_wall(doc, (0.0, 5.0, 0.0), (6.0, 5.0, 0.0), catalog.BY_KEY["parede_alv_15"])
        cls.same = bim.add_wall(doc, (0.0, 9.0, 0.0), (6.0, 9.0, 0.0), catalog.BY_KEY["parede_alv_20"])
        cls.window = bim.add_opening(doc, cls.wall, catalog.OPENING_BY_KEY["janela_120"],
                                     bim.wall_frame(doc, cls.wall), 1.0, -1)
        cls.column = bim.add_column(doc, np.array((10.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        cls.host = QtWidgets.QMainWindow()
        cls.panel = PropertiesPanel(cls.host)

    @classmethod
    def tearDownClass(cls):
        cls.doc.modified = False

    def test_on_top_with_miniatures(self):
        p = self.panel
        p.show_selection(self.doc, [self.window])
        combo = p.editors.get("type")
        self.assertIsInstance(combo, type_thumbs.TypeCombo)
        self.assertIs(combo, p.type_combo)
        self.assertEqual(p.header_texts.indexOf(combo), 2)                  # (under the name and its line)
        self.assertEqual(combo.currentText(), "Janela 120×120 (peitoril 1,00)")
        self.assertTrue(all(not combo.itemIcon(k).isNull() for k in range(combo.count())))
        self.assertEqual(combo.count(), sum(s.kind == "window" for s in catalog.openings()))
        self.assertFalse(p.header_icon.pixmap().isNull())                    # (its own miniature beside it)
        self.assertTrue(p.header_sub.isHidden())                              # (its type's name: in the list)
        self.assertTrue(p.text().startswith("Tipo: Janela 120×120"))

    def test_chosen_there(self):
        p = self.panel
        edits = []
        p.on_edit = lambda action, guid, value: edits.append((action, guid, value))
        try:
            p.show_selection(self.doc, [self.wall])
            combo = p.editors["type"]
            i = combo.findText("Parede alvenaria 15 cm")
            combo.setCurrentIndex(i)
            combo.activated.emit(i)
            pump()
        finally:
            p.on_edit = None
        self.assertEqual([(a, g, v.key) for a, g, v in edits], [("type", self.wall, "parede_alv_15")])

    def test_several(self):
        p = self.panel
        p.show_selection(self.doc, [self.wall, self.same])
        self.assertEqual(p.type_combo.currentText(), "Parede alvenaria 20 cm")
        self.assertTrue(p.header_sub.text() == "Paredes" and not p.header_sub.isHidden())
        p.show_selection(self.doc, [self.wall, self.other])
        self.assertEqual(p.type_combo.currentIndex(), -1)                     # (it differs: blank)
        self.assertTrue(p.type_combo.property("varies"))
        p.show_selection(self.doc, [self.wall, self.column])
        self.assertIsNone(p.type_combo)                                       # (walls and a column: no one list)
        self.assertNotIn("type", p.editors)
        p.show_selection(self.doc, [])
        self.assertIsNone(p.type_combo)


class TypeInTheBar(unittest.TestCase):
    """0.313 — the contextual bar's choice of a type: each with its miniature; another choice: a plain list."""

    def test_bar(self):
        from arqbim.tools.base import Option
        from arqbim.tools.bim_draw import type_option
        from arqbim.ui.context_bar import ContextBar
        host = QtWidgets.QMainWindow()
        bar = ContextBar("ctx", host)
        bar.show_items([("option", type_option(catalog.BY_KEY["parede_alv_20"], "wall")),
                        ("option", Option("side", "Lado", "choice", "a", (("a", "A"), ("b", "B"))))])
        types, side = bar.fields["type"][0], bar.fields["side"][0]
        self.assertIsInstance(types, type_thumbs.TypeCombo)
        self.assertEqual(types.currentData(), "parede_alv_20")
        self.assertTrue(all(not types.itemIcon(k).isNull() for k in range(types.count())))
        self.assertNotIsInstance(side, type_thumbs.TypeCombo)


class MaterialGraphics(unittest.TestCase):
    """0.314 — the materials window's graphics, as Revit's: the surface (foreground and background patterns, each its
    colour, the shading colour, the transparency) and the cut (the same; none: the category's pattern, said so), each
    with its sample; what the window makes of them; a wall's miniature with its material's own cut."""

    def test_window(self):
        from arqbim.ui import pattern_paint
        from arqbim.ui.material_editor import MaterialEditor
        doc = Document()
        try:
            d = MaterialEditor(None, doc)
            d.select("azulejo")
            self.assertEqual(d.surface.combos[0].key(), "tile_15")
            self.assertTrue(d.cut_note.isVisibleTo(d))                       # (no cut of its own: its category's)
            d.select("bloco")
            d.cut.combos[0].set_key("diagonal")
            d.cut.combos[1].set_key("solid")
            d.cut.colours[1].set_colour("#f2dcd2")
            d.surface.combos[0].set_key("brick")
            d.transparency.setValue(20)
            pump()
            spec = d.draft()
            self.assertEqual((spec.cut_fg, spec.cut_bg), (("diagonal", "#2b2f36"), ("solid", "#f2dcd2")))
            self.assertEqual(spec.surface_fg[0], "brick")
            self.assertAlmostEqual(spec.transparency, 0.2)
            self.assertFalse(d.cut_note.isVisibleTo(d))
            self.assertFalse(d.surface_sample.pixmap().isNull())
            self.assertFalse(d.cut_sample.pixmap().isNull())
            combo = pattern_paint.PatternCombo()
            self.assertEqual(combo.key(), None)
            self.assertTrue(all(not combo.itemIcon(k).isNull() for k in range(combo.count())
                                if combo.itemData(k) is not None))
            # a wall's miniature with its block cut so: drawn (made again for the material's new graphics)
            old = catalog.MATERIALS["bloco"]
            wall = catalog.BY_KEY["parede_alv_20"]
            before = type_thumbs.icon(wall)
            catalog.MATERIALS["bloco"] = spec
            try:
                after = type_thumbs.icon(wall)
                self.assertIsNot(before, after)
                self.assertGreater(inked(after.pixmap(type_thumbs.LIST_SIZE, type_thumbs.LIST_SIZE)), 20)
            finally:
                catalog.MATERIALS["bloco"] = old
        finally:
            doc.modified = False


class CutsOnPaper(unittest.TestCase):
    """0.314 — a plan on paper: a wall's block layer cut with its material's own patterns (its background colour, its
    lines), the plaster with its category's in the project's graphic style; that style's library patterns (insulation)
    drawn over their fill."""

    def test_own_cut(self):
        import dataclasses
        from PySide6 import QtGui
        from arqbim.model import drawings
        from arqbim.model import graphic_styles as gs
        from arqbim.ui import pdf
        doc = Document()
        try:
            bim.add_wall(doc, (0.0, 0.0, 0.0), (4.0, 0.0, 0.0), catalog.BY_KEY["parede_alv_20"])
            block = catalog.MATERIALS["bloco"]
            own = dataclasses.replace(block, cut_fg=("diagonal", "#000000"), cut_bg=("solid", "#00ff00"))
            bim.save_material(doc, own, block)
            plan = drawings.plan(doc, doc.active_storey, "P")
            keys = [h for _r, h in plan.fills]
            self.assertEqual(sorted(keys), ["gypsum", "gypsum", "mat:Bloco cerâmico"])   # (0.320: by material)
            self.assertEqual(plan.cut_patterns["mat:Bloco cerâmico"], (("solid", "#00ff00"), ("diagonal", "#000000")))
            image = QtGui.QImage(800, 300, QtGui.QImage.Format.Format_RGB32)
            image.fill(QtGui.QColor("white"))
            painter = QtGui.QPainter(image)
            pdf.paint_drawing(painter, plan, 20, (100.0, 37.5), 4.0)          # (1:20, 4 px a mm)
            painter.end()
            # (the wall 40 px thick, 130 to 170: its plaster 4 px each side, its block between)
            colours = {image.pixelColor(x, 150).name() for x in range(40, 760, 3)}
            self.assertIn("#00ff00", colours)                                 # (the block: its own background)
            self.assertTrue(colours - {"#00ff00"})                            # (…and its lines, thinner than a pixel)
            plaster = {image.pixelColor(x, 132).name() for x in range(40, 760, 3)}
            self.assertIn("#b9b9b9", plaster)                                 # (the plaster: its category's grey)
            # the graphic style with the library's insulation pattern for a category
            style = gs.clean({"hatches": {"gypsum": {"fill": "#ffffff", "pattern": "pat:insulation"}}})
            self.assertEqual(gs.library_pattern(style, "gypsum"), "insulation")
            self.assertEqual(gs.hatch(style, "gypsum")[1], ())
            plan.graphic_style = style
            plan._qt_paths = None
            image.fill(QtGui.QColor("white"))
            painter = QtGui.QPainter(image)
            pdf.paint_drawing(painter, plan, 20, (100.0, 37.5), 4.0)
            painter.end()
            band = [image.pixelColor(x, y).name() for x in range(40, 760, 2) for y in (131, 132, 133)]
            self.assertNotIn("#b9b9b9", band)                                 # (no longer grey…)
            self.assertGreater(band.count("#ffffff"), len(band) // 4)         # (…but white…)
            self.assertGreater(sum(QtGui.QColor(c).lightness() < 200 for c in band), 10)   # (…with its zigzags)
        finally:
            doc.modified = False


class ChoosingPatterns(unittest.TestCase):
    """0.319 — the materials window's patterns chosen as in Revit: each a button with its sample; clicked (or the
    group's sample clicked), a window with every pattern's sample — the drafting ones and the model ones apart —, «No
    pattern», «New…» / «Edit…» (the fill patterns' window); what is chosen is the material's."""

    def _answer(self, button, act):
        def go():
            picker = getattr(button, "_picker", None)
            if picker is None or not picker.isVisible():
                QtCore.QTimer.singleShot(50, go)
                return
            act(picker)
        QtCore.QTimer.singleShot(50, go)

    def test_choose(self):
        from PySide6 import QtTest
        from arqbim.ui import pattern_picker
        from arqbim.ui.material_editor import MaterialEditor
        doc = Document()
        try:
            d = MaterialEditor(None, doc)
            d.select("reboco")
            fg = d.cut.combos[0]
            self.assertIsInstance(fg, pattern_picker.PatternButton)
            self.assertFalse(fg.model and d.surface.combos[0].model is False)   # (cut: drafting; surface: model)
            self.assertTrue(d.surface.combos[0].model)

            def choose_sand(picker):
                self.assertTrue(picker.drafting.isChecked())                     # (a cut: drafting first)
                picker.choose("sand")
                picker.accept()
            self._answer(fg, choose_sand)
            QtTest.QTest.mouseClick(fg, QtCore.Qt.MouseButton.LeftButton)
            self.assertEqual(fg.key(), "sand")
            self.assertIn("Areia", fg.text())
            self.assertEqual(d.draft().cut_fg[0], "sand")
            self.assertFalse(d.cut_note.isVisibleTo(d))

            def choose_tiles(picker):
                self.assertTrue(picker.model.isChecked())                        # (a surface: model first)
                picker.choose("tile_20")
                picker.accept()
            self._answer(d.surface.combos[0], choose_tiles)
            QtTest.QTest.mouseClick(d.surface_sample, QtCore.Qt.MouseButton.LeftButton)   # (the sample clicked)
            self.assertEqual(d.draft().surface_fg[0], "tile_20")

            self._answer(fg, lambda picker: picker.choose_none())
            QtTest.QTest.mouseClick(fg, QtCore.Qt.MouseButton.LeftButton)
            self.assertIsNone(fg.key())
            self.assertIsNone(d.draft().cut_fg)

            old = pattern_picker.EDITOR                                          # («New…»: the patterns' window)
            pattern_picker.EDITOR = lambda parent, key, new: "diagonal_wide" if new else key
            try:
                def make_one(picker):
                    self.assertTrue(picker.new.isVisibleTo(picker))
                    picker._edit(new=True)
                    picker.accept()
                self._answer(fg, make_one)
                QtTest.QTest.mouseClick(fg, QtCore.Qt.MouseButton.LeftButton)
                self.assertEqual(fg.key(), "diagonal_wide")
            finally:
                pattern_picker.EDITOR = old
            d.close()
        finally:
            doc.modified = False


class MaterialLibrary(unittest.TestCase):
    """0.318 — the materials' library: each family's (masonry, concrete, insulation, wood, stone, metals, finishes)
    with their cut and surface hatches, their patterns known; the materials window by family and searched."""

    def test_library(self):
        from arqbim.core import patterns as core_patterns
        from arqbim.ui.material_editor import MaterialEditor
        for key in ("tijolo_11", "betao_armado", "xps", "la_rocha", "pinho", "granito", "aco_s275", "estuque",
                    "porcelanico", "vidro_duplo"):
            self.assertIn(key, catalog.MATERIALS)
        names = [m.name_pt for m in catalog.MATERIALS.values()]
        self.assertEqual(len(names), len(set(names)))                         # (no two with one name)
        for m in catalog.MATERIALS.values():
            for value in (m.cut_fg, m.cut_bg, m.surface_fg, m.surface_bg):
                self.assertTrue(value is None or core_patterns.get(value[0]) is not None, (m.key, value))
        self.assertTrue(catalog.MATERIALS["betao_armado"].own_cut)
        self.assertEqual(catalog.family_of(catalog.MATERIALS["xps"]), "insulation")
        doc = Document()
        try:
            d = MaterialEditor(None, doc)
            d.family.setCurrentIndex(d.family.findData("insulation"))
            shown = [d.list.item(k).text() for k in range(d.list.count())]
            self.assertIn("Lã de rocha", shown)
            self.assertIn("Poliestireno extrudido (XPS)", shown)
            self.assertNotIn("Concreto", shown)
            d.family.setCurrentIndex(0)
            d.search.setText("granito")
            self.assertEqual([d.list.item(k).text() for k in range(d.list.count())], ["Granito"])
            d.select("concreto")                                              # (asked for: shown, filter undone)
            self.assertEqual(d.current.key, "concreto")
            # (0.397) the window and the Materials Browser beside the Properties: the same list, the same order —
            # alphabetical, accents left out (Aço before Água) —, the same families and search
            from arqbim.ui.properties import PropertiesPanel
            panel = PropertiesPanel(None)
            role = QtCore.Qt.ItemDataRole.UserRole

            def keys(w):
                return [w.item(k).data(role) for k in range(w.count())]
            for family, words in ((None, ""), ("metal", ""), ("paint", ""), (None, "aço")):
                d.family.setCurrentIndex(d.family.findData(family))
                d.search.setText(words)
                panel.mat_family.setCurrentIndex(panel.mat_family.findData(family))
                panel.mat_search.setText(words)
                panel._fill_materials()
                self.assertEqual(keys(d.list), keys(panel.materials), (family, words))
                self.assertTrue(keys(d.list), (family, words))
            d.family.setCurrentIndex(0)
            d.search.setText("")
            names = [d.list.item(k).text() for k in range(d.list.count())]
            self.assertLess(names.index("Aço A400 NR"), names.index("Água (piscina, lago)"))
            self.assertLess(names.index("Água (piscina, lago)"), names.index("Azulejo cerâmico"))
            panel.deleteLater()
        finally:
            doc.modified = False


class PatternWindow(unittest.TestCase):
    """0.318 — the fill patterns' window: the program's locked (duplicated to be changed: a brick bond copied as the
    project's), a new one of the project's — crossed lines, then its own families, its sample; what it saves."""

    def tearDown(self):
        from arqbim.core import patterns as core_patterns
        core_patterns.set_project(())

    def test_window(self):
        from arqbim.core import patterns as core_patterns
        from arqbim.ui.pattern_editor import PatternEditor
        saved = []

        def save(pattern, old):
            saved.append((pattern, old))
            core_patterns.set_project([p for p in core_patterns.project_patterns() if p.key != (old or pattern.key)]
                                      + [pattern])
            return pattern.key

        d = PatternEditor(None, select="brick")
        d.on_save = save
        self.assertFalse(d.apply.isEnabled())                  # (the program's: locked)
        copy_key = d.duplicate_pattern()
        self.assertEqual(core_patterns.get(copy_key).families, core_patterns.get("brick").families)
        self.assertTrue(core_patterns.get(copy_key).model and copy_key.startswith("p:"))
        key = d.new_pattern()
        self.assertEqual(d.current.key, key)
        d.shape.setCurrentIndex(d.shape.findData("cross"))
        d.angle.setValue(30.0)
        d.spacing.setValue(1.5)
        draft = d.draft()
        self.assertEqual(core_patterns.shape_of(draft), ("cross", 30.0, 1.5))
        d.shape.setCurrentIndex(d.shape.findData("custom"))
        d._add_row((60.0, 0.0, 0.0, 0.5, 2.0, (2.0, -1.0)))
        d.table.item(d.table.rowCount() - 1, 5).setText("2 -1 0 -1")
        draft = d.draft()
        self.assertEqual(draft.families[-1], (60.0, 0.0, 0.0, 0.5, 2.0, (2.0, -1.0, 0.0, -1.0)))
        self.assertFalse(d.preview.pixmap().isNull())
        d.name.setText("Juntas")
        d.apply_changes()
        self.assertEqual(saved[-1][0].name, "Juntas")
        self.assertIn("Juntas", [d.list.item(k).text() for k in range(d.list.count())])
        d.name.setText("Tijolo à vista")                       # (a name taken: refused)
        self.assertIsInstance(d.draft(), str)


class DrawPanel(unittest.TestCase):
    """0.450 — as Revit's «Draw» panel (the owner: «… poderia ser em ícones para ocupar menos espaços»): a tool's shapes
    on the contextual bar as a row of icons, the one in use lit, a click on another choosing it; the drawing tools of
    lines side by side, a click going to another; the 2D drawing's mask (a region filled white, its outline not on
    paper)."""

    @staticmethod
    def _host(doc):
        from types import SimpleNamespace
        host = SimpleNamespace(doc=doc, viewport=SimpleNamespace(current_view=lambda: None,
                                                                 tracking=SimpleNamespace(clear=lambda: None),
                                                                 clear_overlays=lambda: None),
                               set_hint=lambda *a: None, set_vcb=lambda *a: None, message=lambda *a, **k: None)
        return host

    def test_shapes_as_icons(self):
        from arqbim.tools.bim_draw import WallTool
        from arqbim.ui import context_bar
        doc = Document()
        try:
            tool = WallTool(self._host(doc))
            picked = []
            window = QtWidgets.QMainWindow()
            bar = context_bar.ContextBar("ctx", window)
            bar.on_option = lambda k, v: picked.append((k, v))
            bar.show_items([("option", o) for o in tool.options()])
            row = bar.fields["shape"][0]
            self.assertTrue(row.property("icons"))
            buttons = {b.objectName(): b for b in row.findChildren(QtWidgets.QToolButton)}
            self.assertEqual(len(buttons), 12)             # line, rectangle, 2 polygons, 3 arcs, circle, fillet, pick,
            #                                                face, wand
            self.assertTrue(buttons["ctx_shape_line"].isChecked())
            self.assertFalse(buttons["ctx_shape_line"].icon().isNull())
            buttons["ctx_shape_pick"].click()
            self.assertEqual(picked, [("shape", "pick")])
            tool.set_option("shape", "pick")
            self.assertFalse(bar.sync(tool.options()))              # (0.453: no Chain, no Radius there — made again)
            bar.show_items([("option", o) for o in tool.options()])
            buttons = {b.objectName(): b for b in bar.fields["shape"][0].findChildren(QtWidgets.QToolButton)}
            tool.set_option("offset", 0.5)
            self.assertTrue(bar.sync(tool.options()))               # (the same settings: kept in step)
            self.assertTrue(buttons["ctx_shape_pick"].isChecked() and not buttons["ctx_shape_line"].isChecked())
            buttons["ctx_shape_pick"].click()                       # (the one in use again: it stays)
            self.assertEqual(len(picked), 1)
            self.assertTrue(buttons["ctx_shape_pick"].isChecked())
            tool.set_option("shape", "rect")                        # (no Offset for a rectangle: made again)
            self.assertFalse(bar.sync(tool.options()))
            bar.show_items([("option", o) for o in tool.options() if o.key == "type"])   # (a type stays a list)
            self.assertIsInstance(bar.fields["type"][0], QtWidgets.QComboBox)
            window.deleteLater()
        finally:
            doc.modified = False

    def test_drawing_tools_and_mask(self):
        from arqbim.model import annotations as notes2d
        from arqbim.tools.base import switch_draw
        from arqbim.tools.draft import DraftTool
        from arqbim.tools.line import LineTool
        doc = Document()
        try:
            host = self._host(doc)
            went = []

            def set_tool(name):
                went.append(name)
                host.tool = tools[name]
            tools = {"line": LineTool(host), "rectangle": object()}
            host.set_tool = set_tool
            host.tool = tools["line"]
            line = tools["line"]
            self.assertEqual(line.options()[0].key, "draw")
            line.set_option("draw", "line_arc")                     # (its arcs, as Tab)
            self.assertTrue(line.arc and not went)
            line.set_option("draw", "rectangle")                    # another tool
            self.assertEqual(went, ["rectangle"])
            host.tool = line
            self.assertTrue(switch_draw(line, "line") and not line.arc)
            draft = DraftTool(host)
            draft.cancel = lambda: None
            draft.set_option("shape", "mask")
            self.assertEqual((draft.shape, draft.hatch), ("region", "mask"))
            self.assertEqual(draft.options()[0].value, "mask")      # (the mask's icon lit)
            draft.set_option("shape", "region")
            self.assertEqual(draft.hatch, "diagonal")
            self.assertIn("mask", notes2d.HATCHES)
        finally:
            doc.modified = False


class BrowserTabs(unittest.TestCase):
    """0.461 — the owner: «no rodapé, vamos colocar outras abas de filtro, Geral… Vistas… Biblioteca… Projeto»: the
    Project Browser's own tabs at its foot — what its tree shows: all of it, the views, the library, the model —; a
    group focused from the module bar brings its tab up; the search within the tab."""

    def test_scopes(self):
        from arqbim.ui import project_tree
        panel = project_tree.ProjectTree(None)
        try:
            spatial = ("P", "IfcProject", "Projeto", None,
                       [("B", "IfcBuilding", "Edifício", None, [("S", "IfcBuildingStorey", "Térreo", 0.0, [])])])
            panel.show_project(spatial, [(1, "Parede 1", "IfcWall", "S"), (2, "Esboço 1", None, None)],
                               {"plans": [("S", "Térreo", 0.0)]}, {"components": [("T", "Porta P1", 2, True)],
                                                                    "groups": []})
            tabs = [panel.scope_bar.tabText(k) for k in range(panel.scope_bar.count())]
            self.assertEqual(tabs, ["Tudo", "Vistas", "Biblioteca", "Projeto"])
            self.assertEqual(panel.scope_bar.shape(), QtWidgets.QTabBar.Shape.RoundedSouth)    # (at its foot)

            def shown():
                tree = panel.tree
                return [tree.topLevelItem(k).data(0, project_tree.KEY)[0] for k in range(tree.topLevelItemCount())
                        if not tree.topLevelItem(k).isHidden()]
            panel.set_scope("all")
            self.assertEqual(shown(), ["views", "library", "spatial", "cat"])
            panel.scope_bar.setCurrentIndex(1)                                   # (a click on «Vistas»)
            self.assertEqual((panel.scope, shown()), ("views", ["views"]))
            panel.set_scope("library")
            self.assertEqual(shown(), ["library"])
            panel.set_scope("project")
            self.assertEqual(shown(), ["spatial", "cat"])
            panel.search.setText("Parede")                                       # (the search: within the tab)
            self.assertEqual(shown(), ["spatial"])
            panel.search.setText("")
            self.assertTrue(panel.focus(("library",)))                           # (the module bar's Library)
            self.assertEqual((panel.scope, panel.scope_bar.currentIndex(), shown()), ("library", 2, ["library"]))
            panel.show_project(spatial, [(1, "Parede 1", "IfcWall", "S")], {"plans": [("S", "Térreo", 0.0)]},
                               {"components": [], "groups": []})
            self.assertEqual(shown(), ["library"])                               # (rebuilt: the tab kept)
            again = project_tree.ProjectTree(None)                               # (the next session: the same tab)
            self.assertEqual((again.scope, again.scope_bar.currentIndex()), ("library", 2))
            again.set_scope("all")
            again.deleteLater()
        finally:
            panel.deleteLater()


class HatchesOnScreen(unittest.TestCase):
    """0.317 — a plan's cut for the screen as on paper (model/cut_hatches.py): a wall's block with its own background
    (pink) and lines, its plaster in its category's grey, a column in its category's dark fill; each element apart (its
    selection); the coarse detail left to the dark poché. And a plan with no style drawing the floor's tiles."""

    def test_cut_on_screen(self):
        from arqbim.model import cut_hatches, drawings
        from arqbim.model import graphic_styles as gs
        doc = Document()
        try:
            block = catalog.MATERIALS["bloco"]
            bim.save_material(doc, dataclasses.replace(block, cut_fg=("diagonal", "#000000"),
                                                       cut_bg=("solid", "#f3d9cc")), block)
            wall = bim.add_wall(doc, (0.0, 0.0, 0.0), (4.0, 0.0, 0.0), catalog.BY_KEY["parede_alv_20"])
            column = bim.add_column(doc, np.array((2.0, 2.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
            objs = [o for o in doc.objects.values() if o.is_bim]
            n, cut = np.array((0.0, 0.0, -1.0)), 1.2
            origin, u, v = np.array((0.0, 0.0, cut)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
            fills, own, whose = drawings.cut_fills(doc, objs, n, -cut, origin, u, v)
            self.assertEqual(set(whose), {wall, column})
            self.assertIn("mat:Bloco cerâmico", own)
            parts = cut_hatches.build(fills, whose, own, gs.defaults(), 50, origin, u, v, n * 0.003)
            tris, rgb, segs, seg_rgb = parts[wall]
            self.assertTrue(np.allclose(tris[..., 2], cut - 0.003))             # (a hair under the cut)
            colours = {tuple(np.round(c * 255).astype(int)) for c in rgb}
            self.assertIn((0xf3, 0xd9, 0xcc), colours)                          # (the block's own background)
            self.assertIn((0xb9, 0xb9, 0xb9), colours)                          # (the plaster: its category's grey)
            self.assertGreater(len(segs), 10)                                   # (its lines, its outline)
            self.assertIn((0x3c, 0x3c, 0x3c), {tuple(np.round(c * 255).astype(int)) for c in parts[column][1]})
            area = sum(abs(np.cross(t[1] - t[0], t[2] - t[0])[2]) / 2 for t in tris)
            self.assertAlmostEqual(area, 4.0 * 0.2, places=3)                   # (the wall's whole cut, filled)
            # (0.428) the outline round all that is cut apart from the seams inside it (the plaster's on the block):
            # the wall's 4 × 0,2 m and the column's 0,3 × 0,3 m round; the seams round the block — (0.444) the plaster
            # turned round the wall's free ends: 3,96 m along each face, 0,16 m across each end
            outline = parts[None][2]
            seams = parts[cut_hatches.SEAMS][2]
            length = lambda s: float(np.linalg.norm(s[:, 1] - s[:, 0], axis=1).sum())      # noqa: E731
            self.assertAlmostEqual(length(outline), 2 * (4.0 + 0.2) + 4 * 0.3, places=2)
            self.assertAlmostEqual(length(seams), 2 * 3.96 + 2 * 0.16, delta=0.05)
            coarse, own2, whose2 = drawings.cut_fills(doc, objs, n, -cut, origin, u, v, detail="coarse")
            self.assertEqual(cut_hatches.build(coarse, whose2, own2, gs.defaults(), 50, origin, u, v, n * 0.003), {})
        finally:
            doc.modified = False

    def test_floor_tiles_on_paper(self):
        from arqbim.model import drawings, project_types
        doc = Document()
        try:
            floor = catalog.TypeSpec("t:new", "slab", "Laje com azulejo", "Laje com azulejo",
                                     layers=(("concreto", 0.15), ("azulejo", 0.01)))
            guid = bim.save_type(doc, floor)
            catalog.set_project(project_types.read(doc.ifc), project_types.materials(doc.ifc))
            bim.add_slab(doc, np.array((0.0, 0.0, 0.0)), 3.0, 2.0, catalog.BY_KEY["t:" + guid])
            plan = drawings.plan(doc, doc.active_storey, "P")
            self.assertTrue(plan.surface_lines)                                 # (the tiles, seen from above)
            segs = np.concatenate([s for s, _c in plan.surface_lines])
            self.assertTrue(np.all((segs[..., 0] >= -1e-6) & (segs[..., 0] <= 3.0 + 1e-6)))
        finally:
            doc.modified = False
            catalog.set_project(())


class HatchesByCategory(unittest.TestCase):
    """0.318 — a view style's hatches by category: the walls cut in concrete on dark grey and seen as face brick, over
    their materials', in a plan and an elevation on paper; kept with the style; set in the view styles' window."""

    def test_category_hatches(self):
        from arqbim.model import drawings
        from arqbim.model import view_styles as vs
        from arqbim.ui.view_styles_dialog import ViewStylesDialog
        doc = Document()
        try:
            bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 4.0, 0.0),
                                                          (0.0, 4.0, 0.0))], catalog.BY_KEY["parede_alv_20"])
            walls = ("IfcWall", ("concrete", "#ffffff"), ("solid", "#555555"), ("brick", "#7a3f2a"), None)
            style = dataclasses.replace(vs.new_from(vs.BUILTIN["hidden"], "Licenciamento"), categories=(walls,))
            self.assertEqual(vs.from_dict(vs.to_dict(style)), style)              # (kept with the style)
            doc.set_view_styles([style])
            doc.set_view_props(("plan", doc.active_storey), style=style.uid)
            plan = drawings.plan(doc, doc.active_storey, "P")
            self.assertEqual({h for _r, h in plan.fills}, {"cat:IfcWall"})       # (whole, not by layers)
            self.assertEqual(plan.cut_patterns["cat:IfcWall"], (("solid", "#555555"), ("concrete", "#ffffff")))
            doc.set_view_props(("elevation", "S"), style=style.uid)
            south = drawings.elevation(doc, "S", "Sul")
            self.assertEqual({c for _s, c in south.surface_lines}, {"#7a3f2a"})  # (the walls' brick, seen)
            d = ViewStylesDialog(None, doc.view_styles, select=style.uid)
            self.assertEqual(d.categories.count(), 1)
            self.assertIn("Paredes", d.categories.item(0).text())
            slabs = ("IfcSlab", None, None, ("tile_30", "#909090"), None)
            self.assertTrue(d.edit_category(entry=slabs))
            self.assertEqual(d.styles[0].category("IfcSlab"), slabs[1:])
            self.assertEqual(d.categories.count(), 2)
        finally:
            doc.modified = False


class HatchesByElement(unittest.TestCase):
    """0.331 — a view's hatches by element (Revit's «Override graphics in view ▸ by element»): one wall of four cut in a
    dark solid over the view style's walls' concrete, the others as they were; two given the same hatch joined as one
    material; a wall's brick seen in an elevation that has no style, not in another view; kept with the view (written
    and read back); one undo step; put back; the window that asks for them."""

    def test_element_hatches(self):
        import json
        from arqbim.model import drawings, view_templates
        from arqbim.model import view_styles as vs
        from arqbim.ui.view_styles_dialog import ElementHatches
        doc = Document()
        try:
            walls = bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 4.0, 0.0),
                                                                  (0.0, 4.0, 0.0))], catalog.BY_KEY["parede_alv_20"])
            concrete = ("IfcWall", ("concrete", "#ffffff"), ("solid", "#555555"), None, None)
            style = dataclasses.replace(vs.new_from(vs.BUILTIN["hidden"], "Licenciamento"), categories=(concrete,))
            doc.set_view_styles([style])
            plan_view = ("plan", doc.active_storey)
            doc.set_view_props(plan_view, style=style.uid)
            dark = (("solid", "#333333"), None, None, None)
            self.assertTrue(doc.set_element_hatches(plan_view, [walls[0]], dark))
            self.assertFalse(doc.set_element_hatches(plan_view, [walls[0]], dark))       # (unchanged)
            plan = drawings.plan(doc, doc.active_storey, "P")
            mine = drawings.ELEMENT_CUT + repr((None, ("solid", "#333333")))
            self.assertEqual({h for _r, h in plan.fills}, {mine, "cat:IfcWall"})
            self.assertEqual(plan.cut_patterns[mine], (None, ("solid", "#333333")))
            doc.set_element_hatches(plan_view, [walls[1]], dark)
            plan = drawings.plan(doc, doc.active_storey, "P")
            self.assertEqual(sum(1 for _r, h in plan.fills if h == mine), 1)          # (the two joined, one region)
            own = doc.view_props[plan_view]
            back = view_templates.own_from_dict(json.loads(json.dumps(view_templates.own_to_dict(own))))
            self.assertEqual(view_templates.settings_of(None, back).elements, doc.view_settings(plan_view).elements)
            self.assertIsNone(view_templates.element_hatches({"x": [None, None, None, None], "y": [1, 2]}))
            brick = (None, None, ("brick", "#7a3f2a"), None)
            doc.set_element_hatches(("elevation", "S"), [walls[0]], brick)
            south = drawings.elevation(doc, "S", "Sul")
            self.assertIn("#7a3f2a", {c for _s, c in south.surface_lines})          # (no style: still drawn)
            north = drawings.elevation(doc, "N", "Norte")
            self.assertNotIn("#7a3f2a", {c for _s, c in north.surface_lines})        # (that view only)
            doc.undo()
            self.assertIsNone(doc.view_settings(("elevation", "S")).elements)
            self.assertTrue(doc.set_element_hatches(plan_view, walls[:2], None))
            self.assertIsNone(doc.view_settings(plan_view).elements)
            self.assertEqual({h for _r, h in drawings.plan(doc, doc.active_storey, "P").fills}, {"cat:IfcWall"})
            dialog = ElementHatches(None, dark, "Paredes × 1", "Piso 0")
            self.assertEqual(dialog.entry(), dark)
            self.assertTrue(dialog.reset_button.isEnabled())
            dialog.reset_button.click()
            self.assertIsNone(dialog.entry())
            empty = ElementHatches(None, None, "Paredes × 2", "Piso 0")
            self.assertFalse(empty.reset_button.isEnabled())
            self.assertIsNone(empty.entry())
            for d in (dialog, empty):
                d.deleteLater()
        finally:
            doc.modified = False


class PatternsAlignedByHand(unittest.TestCase):
    """0.332 — model patterns aligned by hand (Revit's Align on a pattern line): a face's pattern laid from another
    origin; a wall's tiles moved 10 cm along it and kept in the wall, following it when it moves; turned; one undo step;
    put back as they were."""

    @staticmethod
    def _upright(segs, keep=None):
        """The x of the upright lines among segments (K, 2, 3)."""
        segs = np.asarray(segs).reshape(-1, 2, 3)
        if keep is not None:
            segs = segs[keep(segs)]
        upright = segs[np.abs(segs[:, 0, 0] - segs[:, 1, 0]) < 1e-9]
        return sorted({round(float(x), 4) for x in upright[:, 0, 0]})

    def test_laid_from_another_origin(self):
        from arqbim.core import patterns as core_patterns
        floor = np.array((((0, 0, 0), (1, 0, 0), (1, 1, 0)), ((0, 0, 0), (1, 1, 0), (0, 1, 0))), dtype=float)
        up = np.array(((0, 0, 1), (0, 0, 1)), dtype=float)
        self.assertTrue({0.3, 0.6, 0.9} <= set(self._upright(core_patterns.on_triangles("tile_30", floor, up))))
        moved = core_patterns.on_triangles("tile_30", floor, up, frame=lambda n: (
            np.array((0.05, 0.0, 0.0)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))))
        self.assertTrue({0.05, 0.35, 0.65, 0.95} <= set(self._upright(moved)))
        self.assertTrue(np.allclose(moved[..., 2], 0.0))
        u, v = core_patterns.turned_axes((0.0, 0.0, 1.0), 90.0)
        self.assertTrue(np.allclose(u, (0.0, 1.0, 0.0)) and np.allclose(v, (-1.0, 0.0, 0.0)))

    def test_align_on_a_wall(self):
        from arqbim.ifc import pattern_align
        from arqbim.model import material_looks
        doc = Document()
        try:
            wall = bim.add_wall(doc, (0.0, 0.0, 0.0), (4.0, 0.0, 0.0), catalog.BY_KEY["parede_alv_20"])
            tiles = (("tile_30", "#909090"), None)

            def joints():                     # (the upright joints on the wall's south face, y = -0.1)
                seen = material_looks.look(doc.ifc, doc.get(wall), (0.5, 0.5, 0.5), colours=False, patterns=True,
                                           clear=False, surface=tiles)
                segs = np.concatenate([s for s, _c in seen.patterns])
                return self._upright(segs, lambda s: (np.abs(s[:, :, 1] + 0.1) < 0.01).all(axis=1))

            self.assertIn(0.3, joints())
            south = (0.0, -1.0, 0.0)
            bim.align_pattern(doc, wall, south, (0.0, -0.1, 0.0), shift=(0.1, 0.0, 0.0))
            self.assertEqual(list(pattern_align.read(doc.ifc, wall)), ["0.000,-1.000,0.000"])
            self.assertTrue({0.1, 0.4, 0.7} <= set(joints()))
            self.assertNotIn(0.3, joints())
            m = np.eye(4)
            m[0, 3] = 1.0
            bim.transform_objects(doc, [wall], m, "mover")                     # (the tiles follow the wall)
            self.assertTrue({1.1, 1.4, 1.7} <= set(joints()))
            bim.align_pattern(doc, wall, south, (2.0, -0.1, 1.0), angle=45.0)
            self.assertAlmostEqual(pattern_align.read(doc.ifc, wall)["0.000,-1.000,0.000"][3], 45.0)
            self.assertFalse({1.1, 1.4, 1.7} & set(joints()))                    # (turned: no upright joints there)
            doc.undo()
            self.assertAlmostEqual(pattern_align.read(doc.ifc, wall)["0.000,-1.000,0.000"][3], 0.0)
            self.assertTrue(bim.reset_patterns(doc, [wall]))
            self.assertEqual(pattern_align.read(doc.ifc, wall), {})
            self.assertIn(1.2, joints())                                         # (as always: the world's 30 cm)
            self.assertFalse(bim.reset_patterns(doc, [wall]))
        finally:
            doc.modified = False


class JoinsByHand(unittest.TestCase):
    """0.333 — Unjoin / Join geometry (Revit's): two walls in a row, of one material, unjoined — kept in both, one undo
    step —: in the plan the line between them comes back (the cut's breaks, at their common end), in the elevation the
    edge between them too; on paper (PDF and DXF) the line drawn; joined again: as before. A corner (L) unjoined: its
    line there."""

    @staticmethod
    def _uprights(drawing):
        segs = np.asarray(drawing.lines).reshape(-1, 2, 2)
        return int(np.sum((np.abs(segs[:, 0, 0] - segs[:, 1, 0]) < 1e-6) & (np.abs(segs[:, 0, 1] - segs[:, 1, 1]) > 1.0)))

    def test_unjoin_and_join(self):
        import shutil
        import tempfile
        from arqbim.ifc import unjoin
        from arqbim.model import drawings, dxf
        from arqbim.ui import pdf
        doc = Document()
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        try:
            a, b = bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (8.0, 0.0, 0.0))],
                                     catalog.BY_KEY["parede_alv_20"], closed=False)
            plan = drawings.plan(doc, doc.active_storey, "P")
            self.assertEqual(len(plan.breaks), 0)
            seen = self._uprights(drawings.elevation(doc, "S", "Sul"))
            self.assertTrue(bim.unjoin(doc, a, b))
            self.assertFalse(bim.unjoin(doc, a, b))                              # (so already)
            self.assertEqual((unjoin.apart_from(doc.ifc, a), unjoin.apart_from(doc.ifc, b)), ({b}, {a}))
            plan = drawings.plan(doc, doc.active_storey, "P")
            self.assertGreater(len(plan.breaks), 0)
            self.assertTrue(np.allclose(plan.breaks[..., 0], 4.0, atol=1e-3))   # (at their common end)
            self.assertGreater(self._uprights(drawings.elevation(doc, "S", "Sul")), seen)   # (each one's end there)
            self.assertGreater(dxf.write(os.path.join(folder, "p.dxf"), plan), 0)
            from arqbim.model import sheets
            pdf.write(os.path.join(folder, "p.pdf"), plan, sheets.title_texts({}, "P", project="Ensaio"))
            self.assertGreater(os.path.getsize(os.path.join(folder, "p.pdf")), 1000)
            doc.undo()
            self.assertEqual(unjoin.apart_from(doc.ifc, a), frozenset())
            doc.redo()
            self.assertTrue(bim.unjoin(doc, a, b, apart=False))
            self.assertEqual(len(drawings.plan(doc, doc.active_storey, "P").breaks), 0)
            self.assertEqual(self._uprights(drawings.elevation(doc, "S", "Sul")), seen)
            c = bim.add_wall(doc, (8.0, 0.0, 0.0), (8.0, 3.0, 0.0), catalog.BY_KEY["parede_alv_20"])
            bim.unjoin(doc, b, c)
            corner = drawings.plan(doc, doc.active_storey, "P").breaks
            self.assertGreater(len(corner), 0)
            self.assertTrue(np.all(np.abs(corner[..., 0] - 8.0) < 0.2) and np.all(np.abs(corner[..., 1]) < 0.2))
        finally:
            doc.modified = False


class ViewSvg(unittest.TestCase):
    """0.369 — a view alone in SVG (Home ▸ Export ▸ Export view): Qt's SVG generator throws every clip away, so the
    hatches of a cut wall spread over the whole page (the sheets' SVG had it too, since 0.128); they are cut to their
    shape in geometry instead — a square ring's lines kept inside its band only, by its fill rule, and its dots —, the
    PDF and the screen still clipped by Qt. The SVG: in millimetres at the view's scale, as big as what it paints (its
    marks and dimensions too) and a margin, every hatch line of a wall's cut inside that wall."""

    def test_clip_segments(self):
        from arqbim.ui import pattern_paint
        ring = QtGui.QPainterPath()
        ring.addRect(QtCore.QRectF(0.0, 0.0, 10.0, 10.0))
        ring.addRect(QtCore.QRectF(3.0, 3.0, 4.0, 4.0))                  # (a hole: odd-even, Qt's own rule)
        lines = [((-5.0, 5.0), (15.0, 5.0)), ((-5.0, 1.0), (15.0, 1.0)), ((20.0, 0.0), (30.0, 10.0)),
                 ((5.0, 5.0), (6.0, 6.0))]
        kept = pattern_paint.clip_segments(ring, lines)
        np.testing.assert_allclose(kept, [((0.0, 5.0), (3.0, 5.0)), ((7.0, 5.0), (10.0, 5.0)),
                                          ((0.0, 1.0), (10.0, 1.0))], atol=1e-9)    # (outside, in the hole: none)
        self.assertEqual(pattern_paint.clip_segments(QtGui.QPainterPath(), lines).shape, (0, 2, 2))
        image = QtGui.QImage(20, 20, QtGui.QImage.Format.Format_RGB32)
        painter = QtGui.QPainter(image)
        self.assertTrue(pattern_paint.keeps_clip(painter))               # (a picture, the PDF: Qt clips)
        painter.end()

    def test_plan_in_svg(self):
        import re
        import tempfile
        import xml.etree.ElementTree as ElementTree
        from arqbim.model import drawings
        from arqbim.ui import pdf
        doc = Document()
        try:
            bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (6.0, 4.0, 0.0),
                                                          (0.0, 4.0, 0.0))], catalog.BY_KEY["parede_alv_20"])
            plan = drawings.plan(doc, doc.active_storey, "Planta")
            with tempfile.TemporaryDirectory() as folder:
                path = os.path.join(folder, "planta.svg")
                w, h = pdf.write_svg(path, plan, 50)
                root = ElementTree.parse(path).getroot()
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
        finally:
            doc.modified = False
        lo, hi = plan.bounds()
        self.assertGreater(w, (hi[0] - lo[0]) * 1000.0 / 50)                     # (its lines, a margin round them)
        self.assertLess(w, (hi[0] - lo[0]) * 1000.0 / 50 + 4 * pdf.PROBE_PAD)
        self.assertAlmostEqual(float(root.get("width")[:-2]), w, delta=0.5)
        self.assertTrue(root.get("width").endswith("mm"))
        self.assertNotIn("clip", text.lower())
        # every point drawn inside the paper (nothing spread over it, nothing cut at its edge)
        view = [float(v) for v in root.get("viewBox").split()]
        numbers = [float(v) for v in re.findall(r'points="([^"]+)"', text) for v in re.split(r"[ ,]+", v.strip()) if v]
        self.assertGreater(len(numbers), 100)
        xs, ys = numbers[0::2], numbers[1::2]
        self.assertTrue(view[0] <= min(xs) and max(xs) <= view[2] and view[1] <= min(ys) and max(ys) <= view[3])
        # the hatches (the hatch pen's lines): many, each short — inside a wall 20 cm thick, 4 mm at 1:50 —, none
        # across the page as Qt's generator drew them
        from arqbim.model import graphic_styles
        k = view[2] / w                                                         # (svg units a mm)
        pen = graphic_styles.pen(getattr(plan, "graphic_style", None) or graphic_styles.DEFAULTS, "hatch") * k
        lengths = []
        for group in root.iter():
            if group.tag.endswith("}g") and abs(float(group.get("stroke-width", -1)) - pen) < 0.02 * pen:
                for line in group:
                    if line.tag.endswith("polyline"):
                        pts = np.array([float(v) for v in re.split(r"[ ,]+", line.get("points").strip()) if v])
                        lengths.append(float(np.linalg.norm(np.diff(pts.reshape(-1, 2), axis=0), axis=-1).sum()))
        self.assertGreater(len(lengths), 20)
        self.assertLess(max(lengths), 12.0 * k)


class LayerPriorities(unittest.TestCase):
    """0.334 — each layer's function in its type (Revit's Structure [1] … Finish 2 [5]): kept in the IFC as the layer's
    Priority and Category (valid), read back; the elements' layers' strengths. A wall of concrete (its structure) and
    a thicker mineral wool (its insulation) — automatic, the wool would be its core —: another wall ending against it
    cuts in otherwise. The type editor's Function column."""

    def tearDown(self):
        catalog.set_project(())

    def _tee(self, functions):
        """A plan of a T: the tested wall through, a block wall ending against it — {hatch: area}, and the doc."""
        from arqbim.core import drawing2d
        from arqbim.model import drawings, project_types
        doc = Document()
        spec = catalog.TypeSpec("t:new", "wall", "Parede ensaio", "Parede ensaio",
                                layers=(("concreto", 0.10), ("la", 0.15)), functions=functions)
        guid = bim.save_type(doc, spec)
        catalog.set_project(project_types.read(doc.ifc), project_types.materials(doc.ifc))
        wall = bim.add_wall(doc, (0.0, 0.0, 0.0), (6.0, 0.0, 0.0), catalog.BY_KEY["t:" + guid])
        bim.add_wall(doc, (3.0, 0.125, 0.0), (3.0, 3.0, 0.0), catalog.BY_KEY["parede_alv_20"])
        areas = {}
        for ring, key in drawings.plan(doc, doc.active_storey, "P").fills:
            areas[key] = areas.get(key, 0.0) + drawing2d._signed_area(np.asarray(ring, dtype=float))
        return {k: round(a, 5) for k, a in areas.items()}, doc, wall, guid

    def test_functions_kept_and_used(self):
        from arqbim.model import project_types
        auto, doc0, _w, _g = self._tee(())
        doc0.modified = False
        mine, doc, wall, guid = self._tee(("structure", "thermal"))
        try:
            layers = doc.ifc.by_guid(guid).HasAssociations[0].RelatingMaterial.MaterialLayers
            self.assertEqual([(l.Priority, l.Category) for l in layers], [(90, "LoadBearing"), (50, "Insulation")])
            self.assertEqual(project_types.read_type(doc.ifc, doc.ifc.by_guid(guid), "wall").functions,
                             ("structure", "thermal"))
            self.assertEqual(sorted(doc.ifc.layer_strengths([wall])[wall]), [1, 3])
            self.assertEqual(doc.ifc.validate(express_rules=True), [])
            self.assertNotEqual(auto, mine)                                    # (the tee cut in otherwise…)
            self.assertAlmostEqual(sum(auto.values()), sum(mine.values()), places=4)   # (…the same all in all)
        finally:
            doc.modified = False

    def test_type_editor_column(self):
        from arqbim.ui.type_editor import TypeEditor
        doc = Document()
        try:
            spec = catalog.TypeSpec("t:x", "wall", "Parede ensaio", "Parede ensaio",
                                    layers=(("concreto", 0.10), ("la", 0.15)), functions=("structure", None))
            d = TypeEditor(None, doc, kind="wall")
            d.current = spec
            d._show(spec)
            self.assertEqual([d.layers.cellWidget(r, 2).currentData() for r in range(2)], ["structure", None])
            role = d.layers.cellWidget(1, 2)
            role.setCurrentIndex(role.findData("thermal"))
            self.assertEqual(d.draft().functions, ("structure", "thermal"))
            d.layers.setCurrentCell(1, 0)
            d._move_layer(-1)                                                  # (its function moves with it)
            self.assertEqual(d.draft().functions, ("thermal", "structure"))
            for r in range(2):
                d.layers.cellWidget(r, 2).setCurrentIndex(0)
            self.assertEqual(d.draft().functions, ())
            d.deleteLater()
        finally:
            doc.modified = False


class StyledDrawings(unittest.TestCase):
    """0.315 — the drawings by their view's style: an elevation in «Realista» — its faces painted (the farthest first),
    the stone in its shaded colour, the stone's courses seen on it, on paper; a plan's cut empty, by category, solid; a
    3D view on a sheet in lines as always, in «Cores consistentes» painted; a view with no style as before."""

    @classmethod
    def setUpClass(cls):
        from arqbim.model import project_types
        cls.doc = doc = Document()
        stone = catalog.TypeSpec("t:new", "wall", "Parede de pedra 23", "Parede de pedra 23",
                                 layers=(("pedra", 0.03), ("bloco", 0.18), ("reboco", 0.02)))
        guid = bim.save_type(doc, stone)
        catalog.set_project(project_types.read(doc.ifc), project_types.materials(doc.ifc))
        cls.walls = bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (8.0, 0.0, 0.0), (8.0, 5.0, 0.0),
                                                                   (0.0, 5.0, 0.0))], catalog.BY_KEY["t:" + guid])
        bim.add_opening(doc, cls.walls[0], catalog.OPENING_BY_KEY["janela_150"], bim.wall_frame(doc, cls.walls[0]),
                        3.0, -1)

    @classmethod
    def tearDownClass(cls):
        cls.doc.modified = False
        catalog.set_project(())

    def test_elevation(self):
        from PySide6 import QtGui
        from arqbim.model import drawings, material_looks
        from arqbim.ui import pdf
        doc = self.doc
        plain = drawings.elevation(doc, "S", "Sul")
        self.assertEqual(plain.faces, [])                                       # (no style: lines, as always…)
        self.assertTrue(plain.surface_lines)                                    # (…0.317: with the stone's courses)
        doc.set_view_props(("elevation", "S"), style="realistic")
        styled = drawings.elevation(doc, "S", "Sul")
        try:
            self.assertGreater(len(styled.faces), 10)
            depths = [f[3] for f in styled.faces]
            self.assertEqual(depths, sorted(depths, reverse=True))              # (the farthest first)
            stone = np.array(catalog.MATERIALS["pedra"].color)
            sun = doc.view_style("realistic").sun()                             # (0.316: lit by the style's sun)
            lit = material_looks.shade(stone[None, :], np.array([[0.0, -1.0, 0.0]]), sun)[0]
            self.assertTrue(any(np.allclose(f[1], lit, atol=1e-6) for f in styled.faces))
            shadows = [f for f in styled.faces if isinstance(f[0], list)]       # (0.316: the window's reveal's)
            self.assertTrue(shadows)
            self.assertTrue(all(np.allclose(f[1], stone * material_looks.SHADOW, atol=1e-6) or f[1] != tuple(lit)
                                for f in shadows))
            self.assertTrue(styled.surface_lines and styled.surface_lines[0][1] == "#8a8072")
            image = QtGui.QImage(900, 500, QtGui.QImage.Format.Format_RGB32)
            image.fill(QtGui.QColor("white"))
            painter = QtGui.QPainter(image)
            pdf.paint_drawing(painter, styled, 50, (75.0, 40.0), 6.0)
            painter.end()
            want = QtGui.QColor.fromRgbF(*lit)
            near = sum(abs(image.pixelColor(x, y).red() - want.red()) <= 2 and
                       abs(image.pixelColor(x, y).green() - want.green()) <= 2
                       for x in range(0, 900, 6) for y in range(0, 500, 6))
            self.assertGreater(near, 100)                                       # (the stone, painted)
        finally:
            self.doc.set_view_props(("elevation", "S"), style=None)

    def test_cuts(self):
        from arqbim.model import drawings, view_styles
        doc = self.doc
        key = ("plan", doc.active_storey)
        mine = view_styles.new_from(view_styles.BUILTIN["hidden"], "Corte vazio")
        doc.set_view_styles([dataclasses.replace(mine, cut="empty"),
                             dataclasses.replace(mine, name="Sólido", uid="s1", cut="solid")])
        try:
            doc.set_view_props(key, style=doc.view_styles[0].uid)
            self.assertEqual({h for _r, h in drawings.plan(doc, doc.active_storey, "P").fills},
                             {drawings.EMPTY_CUT})
            doc.set_view_props(key, style="s1")
            self.assertEqual({h for _r, h in drawings.plan(doc, doc.active_storey, "P").fills}, {None})
            doc.set_view_props(key, style=None)
            self.assertIn("masonry", {h for _r, h in drawings.plan(doc, doc.active_storey, "P").fills})
        finally:
            doc.set_view_props(key, style=None)
            doc.set_view_styles([])

    def test_3d_on_a_sheet(self):
        from arqbim.model import drawings
        doc = self.doc
        lines = drawings.view3d_drawing(doc, None, "3D")
        self.assertEqual(lines.faces, [])                                       # (shaded: in lines, as always)
        doc.set_view_props(("3d",), style="consistent")
        try:
            painted = drawings.view3d_drawing(doc, None, "3D")
            self.assertGreater(len(painted.faces), 10)
        finally:
            doc.set_view_props(("3d",), style=None)


class NoticeBalloon(unittest.TestCase):
    """0.321 — the balloon over the view: a long refusal word-wrapped whole within the view (not cut), at the top in
    the middle, under the views' tabs; a short one as wide as its text; what a command did goes by itself after a time
    that grows with its length; the tool's step follows its changes; what is said in the same turn as a change of tool
    is not taken down by it, afterwards it is."""

    def setUp(self):
        from arqbim.ui import notice
        self.notice = notice
        self.area = QtWidgets.QWidget()
        self.area.resize(1100, 600)
        self.tabs = QtWidgets.QTabBar(self.area)
        self.tabs.addTab("3D")
        self.tabs.setGeometry(0, 0, 1100, 28)
        self.area.show()
        self.balloon = notice.Notice(self.area, tabs=self.tabs)

    def tearDown(self):
        self.area.close()
        self.area.deleteLater()
        pump()

    def test_long_text_whole(self):
        n = self.balloon
        text = ("Ainda não há eixos: desenhe-os (ferramenta Eixos) ou gere-os (BIM ▸ Gerar eixos…). " * 3).strip()
        n.say(text, warning=True)
        pump()
        g = n.geometry()
        self.assertTrue(n.isVisible())
        self.assertEqual(n.shown_text(), text)
        self.assertLessEqual(g.width(), self.notice.MAX_W)
        self.assertLessEqual(g.right(), 1100 - self.notice.SIDE + 1)              # (clear of the view cube)
        self.assertLessEqual(abs(g.center().x() - 550), 1)
        self.assertGreater(g.top(), self.tabs.geometry().bottom())
        self.assertGreater(n.text.height(), 2 * n.text.fontMetrics().height())    # (wrapped on several lines…)
        self.assertLessEqual(n.text.heightForWidth(n.text.width()), n.text.height())   # (…none cut off)
        self.area.resize(700, 600)                       # (the view narrower: left of the view cube's band, wider)
        pump()
        g = n.geometry()
        self.assertGreaterEqual(g.left(), self.notice.MARGIN)
        self.assertLessEqual(g.right(), 700 - self.notice.SIDE + 1)
        self.assertGreater(g.width(), 700 - 2 * self.notice.SIDE)
        self.assertEqual(n.timer.interval(), self.notice.WARNING_MS)

    def test_short_text_and_time(self):
        n = self.balloon
        n.say("Feito.")
        pump()
        self.assertEqual(n.kind, "info")
        self.assertLess(n.geometry().width(), 300)
        self.assertEqual(n.timer.interval(), 4000)
        self.assertEqual(self.notice.info_ms("x" * 400), 12000)
        n.timer.start(10)
        for _ in range(20):
            QtCore.QThread.msleep(5)
            pump()
        self.assertFalse(n.isVisible())

    def test_fresh_and_hint(self):
        n = self.balloon
        n.say("Selecione primeiro.", warning=True)
        n.dismiss()                                                               # (the same turn: it stays)
        n.hint("Parede", "Clique no início.")                                     # (nor does a tool's step hide it)
        self.assertEqual((n.kind, n.shown_text()), ("warning", "Selecione primeiro."))
        pump()
        n.hint("Parede", "Clique no início.")
        self.assertEqual((n.kind, n.title.text()), ("hint", "Parede"))
        n.hint_changed("Clique no fim.")
        self.assertEqual(n.shown_text(), "Clique no fim.")
        n.hint_changed("Parede: clique no fim.")                                  # (its name said once, on top)
        self.assertEqual(n.shown_text(), "Clique no fim.")
        pump()
        n.dismiss()
        self.assertFalse(n.isVisible())
        self.assertEqual(n.shown_text(), "")

    def test_button(self):
        """0.324 — the step that is missing as a button under the text, inside the balloon; clicked, the balloon goes
        and the step runs; the next message without one has none."""
        n = self.balloon
        ran = []
        n.say("Ainda não há eixos.", warning=True, action=("Gerar eixos…", lambda: ran.append(True)))
        pump()
        b = n.action_button.geometry()
        self.assertTrue(n.action_button.isVisibleTo(n))
        self.assertTrue(n.rect().contains(b))
        self.assertGreaterEqual(b.top(), n.text.geometry().bottom())
        n.action_button.click()
        self.assertEqual(ran, [True])
        self.assertFalse(n.isVisible())
        n.say("Feito.")
        self.assertFalse(n.action_button.isVisibleTo(n))

    def test_request(self):
        """0.322 — a command's request stays through clicks and selections; what is said meanwhile goes over it and,
        gone, the request is back; its × gives the command up; answered, it goes."""
        n = self.balloon
        given_up = []
        n.on_cancel = lambda: given_up.append(True)
        n.ask("Ligar o topo", "Clique nas paredes.\nEscolhidos: 0")
        pump()
        n.dismiss()                                                              # (a click in the view)
        self.assertEqual(n.kind, "ask")
        n.hint("Parede", "Clique no início.")                                    # (no tool's step over it)
        self.assertEqual(n.kind, "ask")
        n.say("Esse elemento não serve.", warning=True)
        n.ask("Ligar o topo", "Clique nas paredes.\nEscolhidos: 1")              # (said just now: it stays on top)
        self.assertEqual(n.kind, "warning")
        pump()
        n.dismiss()
        self.assertEqual((n.kind, n.shown_text()), ("ask", "Clique nas paredes.\nEscolhidos: 1"))
        n.close_button.click()
        self.assertEqual(given_up, [True])
        n.end_ask()
        self.assertFalse(n.isVisible())
        n.dismiss()
        self.assertIsNone(n.kind)


class HelpPlaces(unittest.TestCase):
    """0.327 — where each command is, said by the Help window: the first discipline that has it (Wall: Architecture ▸
    Walls; Plan: Annotate ▸ Views), the contextual tab's own (Merge walls: Modify | Walls); words found without their
    accents and case; every command on the ribbon has a place, and every first step a command on it."""

    def test_where(self):
        from arqbim.ui import help_window, ribbon
        self.assertEqual(help_window.where("wall"), ("architecture", "walls"))
        self.assertEqual(help_window.where("plan"), ("annotate", "views"))
        self.assertEqual(help_window.where("merge_walls"), ("ctx:walls", "geometry"))
        self.assertIsNone(help_window.where("nothing_of_the_kind"))
        self.assertEqual(help_window.where_text("wall"), "Arquitetura ▸ Paredes")
        self.assertEqual(help_window.folded("Coberturas e Ligações"), "coberturas e ligacoes")
        for tab in list(ribbon.DISCIPLINES) + ["ctx:" + k for k in ribbon.CONTEXTS]:
            for name in ribbon.items_of(tab):
                self.assertIsNotNone(help_window.where(name), name)
        for _text, name in help_window.FIRST_STEPS:
            self.assertIsNotNone(help_window.where(name), name)


class ImageOfTheView(unittest.TestCase):
    """0.329 — Export ▸ Image of the view: a size chosen sets the width, a width typed picks its size (or «Outra
    largura»), the height from the view's proportion; white proposed in a plan, the choice kept for the next time. The
    image written as PNG with its transparency, as JPEG on white; an A3 sheet's width at 300 ppp."""

    def setUp(self):
        from arqbim.ui import image_dialog
        image_dialog.ImageDialog.last = {"width": 1920, "background": None}
        self.addCleanup(setattr, image_dialog.ImageDialog, "last", {"width": 1920, "background": None})

    def test_dialog(self):
        from arqbim.ui import image_dialog

        def size_of(width):
            width = min(width, 7680)
            return width, width // 2

        dialog = image_dialog.ImageDialog(None, size_of, 900, cutting=True)
        self.assertEqual((dialog.width.value(), dialog.background.currentData()), (1920, "white"))
        self.assertIn("1920 × 960 px", dialog.size_text.text())
        self.assertEqual(dialog.width.maximum(), 7680)
        dialog.preset.setCurrentIndex(2)
        self.assertEqual(dialog.width.value(), 3840)
        dialog.width.setValue(1234)
        self.assertEqual(dialog.preset.currentIndex(), dialog.preset.count() - 1)
        dialog.width.setValue(900)
        self.assertEqual(dialog.preset.currentIndex(), dialog.preset.count() - 2)
        dialog.background.setCurrentIndex(2)
        self.assertEqual(dialog.values(), (900, "transparent"))
        again = image_dialog.ImageDialog(None, size_of, 900)
        self.assertEqual((again.width.value(), again.background.currentData()), (900, "transparent"))
        for d in (dialog, again):
            d.deleteLater()

    def test_written(self):
        import shutil
        import tempfile
        from PySide6 import QtGui
        from arqbim.ui import image_dialog
        rgba = np.zeros((40, 4961, 4), np.uint8)
        rgba[:, :100] = (200, 30, 30, 255)
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        png, jpg = os.path.join(folder, "vista.png"), os.path.join(folder, "vista.jpg")
        self.assertTrue(image_dialog.save_image(png, rgba))
        self.assertTrue(image_dialog.save_image(jpg, rgba))
        image, flat = QtGui.QImage(png), QtGui.QImage(jpg)
        self.assertEqual((image.width(), image.height()), (4961, 40))
        self.assertEqual(image.pixelColor(4000, 20).alpha(), 0)
        self.assertEqual(image.pixelColor(50, 20).red(), 200)
        self.assertGreater(min(flat.pixelColor(4000, 20).getRgb()[:3]), 245)
        self.assertAlmostEqual(image.dotsPerMeterX() * 0.0254, 300, delta=1)
        self.assertFalse(image_dialog.save_image(os.path.join(folder, "nao_existe", "vista.png"), rgba))


class QtInPortuguese(unittest.TestCase):
    """0.330 — Qt's own words in Portuguese of Portugal: the standard buttons (Guardar, Não guardar, Cancelar, Sim),
    the file window (Nome do ficheiro, Guardar), the text boxes' menu (Eliminar); the keys' names and the file window's
    keys as Qt has them; Brazilian Portuguese underneath for what is not listed; installed once; every %1 kept."""

    def setUp(self):
        from arqbim.ui import qt_portuguese
        self.installed = qt_portuguese.install(APP)
        self.addCleanup(self._remove)

    def _remove(self):
        from arqbim.ui import qt_portuguese
        for translator in self.installed:
            APP.removeTranslator(translator)
        qt_portuguese._installed.clear()

    def test_words(self):
        from arqbim.ui import qt_portuguese
        said = QtCore.QCoreApplication.translate
        self.assertEqual([said("QPlatformTheme", w) for w in ("Save", "Discard", "Cancel", "&Yes", "&No")],
                         ["Guardar", "Não guardar", "Cancelar", "&Sim", "&Não"])
        self.assertEqual(said("QFileDialog", "File &name:"), "&Nome do ficheiro:")
        self.assertEqual(said("QLineEdit", "Delete"), "Eliminar")
        self.assertEqual(said("QShortcut", "Ctrl"), "Ctrl")
        self.assertEqual(said("QShortcut", "Space"), "Space")
        self.assertEqual(said("QFileDialog", "Alt+Left"), "Alt+Left")
        # a text not listed: Brazilian Portuguese's when it has one, else Qt's own — never blank
        self.assertEqual(said("QLibrary", "Cannot load library %1: %2"), "Não foi possível carregar a biblioteca %1: %2")
        self.assertEqual(said("Nothing", "A text of no one's"), "A text of no one's")
        self.assertEqual(qt_portuguese.install(APP), self.installed)
        box = QtWidgets.QMessageBox()
        B = QtWidgets.QMessageBox.StandardButton
        box.setStandardButtons(B.Save | B.Discard | B.Cancel)
        self.assertEqual(sorted(b.text() for b in box.buttons()), ["Cancelar", "Guardar", "Não guardar"])
        box.deleteLater()
        for context, words in qt_portuguese.WORDS.items():
            for source, text in words.items():
                if text is not None:
                    self.assertEqual(source.count("%1"), text.count("%1"), (context, source))
                    self.assertEqual(source.count("%2"), text.count("%2"), (context, source))


class StartPageLists(unittest.TestCase):
    """0.387 — the recent documents: the most recent first, once; as many as kept; one taken off; their group apart
    for the tests (not the user's); a picture cut to its shape; the start page's file read; a TESTAR section found;
    the base files of the base folder."""

    def setUp(self):
        for name in ("ARQBIM_RECENT_GROUP", "ARQBIM_CACHE_DIR"):             # (put back as they were after)
            self.addCleanup(lambda n=name, v=os.environ.get(name): os.environ.__setitem__(n, v) if v is not None
                            else os.environ.pop(n, None))
        os.environ["ARQBIM_RECENT_GROUP"] = "recentes_teste_unidade"
        from arqbim.ui import recent
        recent._write([])
        recent.set_keep(recent.DEFAULT_KEEP)

    def test_recent(self):
        import tempfile
        from arqbim.ui import recent
        folder = tempfile.mkdtemp()
        paths = [os.path.join(folder, "p{}.ifc".format(k)) for k in range(4)]
        for p in paths:
            recent.add(p)
        recent.add(paths[1])
        self.assertEqual(recent.files(), [paths[1], paths[3], paths[2], paths[0]])
        recent.set_keep(2)
        self.assertEqual(recent.files(), [paths[1], paths[3]])
        recent.remove(paths[3])
        self.assertEqual(recent.files(), [paths[1]])
        os.environ["ARQBIM_CACHE_DIR"] = folder
        rgba = np.zeros((300, 600, 4), dtype=np.uint8)
        rgba[..., 3] = 255
        self.assertTrue(recent.save_thumb(paths[1], rgba))
        image = QtGui.QImage(recent.thumb_file(paths[1]))
        self.assertEqual((image.width(), image.height()), (recent.THUMB_W, recent.THUMB_H))
        self.assertFalse(recent.save_thumb(paths[1], None))

    def test_page_sources(self):
        import tempfile
        from arqbim.ui import start_page
        data = start_page.config()
        self.assertTrue(data["tutorials"] and "support_url" in data and "discussions" in data)
        self.assertTrue(start_page.testar_section("0.380").startswith("## 0.380 "))
        self.assertEqual(start_page.testar_section("9.999"), "")
        docs = tempfile.mkdtemp()
        os.makedirs(start_page.base_folder(docs))
        for name in ("b.ifc", "a.IFC", "notas.txt"):
            open(os.path.join(start_page.base_folder(docs), name), "w").close()
        self.assertEqual([os.path.basename(p) for p in start_page.base_files(docs)], ["a.IFC", "b.ifc"])


class MenusAtTheFoot(unittest.TestCase):
    """0.377 — a menu opened near the screen's foot goes up (the Windows taskbar's room left free, which Qt in WSLg
    does not know of); one with room below stays where it was asked; the settings menu's foot on its button's foot;
    a submenu watched once however many times it is asked."""

    def test_menus(self):
        from arqbim.ui import menus
        menu = QtWidgets.QMenu()
        for i in range(8):
            menu.addAction("item %d" % i)
        height = menu.sizeHint().height()
        screen = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        low = QtCore.QPoint(100, screen.bottom() - 10)
        self.assertEqual(menus.menu_point(menu, low), QtCore.QPoint(100, low.y() - height))
        high = QtCore.QPoint(100, screen.top() + 10)
        self.assertEqual(menus.menu_point(menu, high), high)
        button = QtWidgets.QToolButton()
        button.resize(40, 40)
        foot = button.mapToGlobal(QtCore.QPoint(40, 40))
        self.assertEqual(menus.above(menu, button), QtCore.QPoint(foot.x(), foot.y() - height))
        sub = menu.addMenu("sub")
        menus.keep_up(sub)
        menus.keep_up(sub)
        self.assertEqual(len(sub.findChildren(menus._KeepUp)), 1)
        button.deleteLater()
        menu.deleteLater()


class GroundGrid(unittest.TestCase):
    """0.393 (the owner: «a linha grid no tema escuro está muito forte») — the ground grid's colour from the background
    in use: as always on the light canvas; on the dark views and a dark palette's drawing area a little lighter than
    the ground (0,08), on a light palette's a little darker (0,14)."""

    def tearDown(self):
        from arqbim.render import canvas
        canvas.set_dark(False)
        canvas.set_tint(None)

    def test_soft_on_dark(self):
        from arqbim.render import canvas

        def lightness(h):
            c = h.lstrip("#")
            r, g, b = (int(c[k:k + 2], 16) / 255 for k in (0, 2, 4))
            return (max(r, g, b) + min(r, g, b)) / 2
        self.assertEqual(canvas.ground_grid("#c3c8cc"), "#c3c8cc")
        for dark, tint in ((True, None), (False, "#30302f"), (False, "#202630")):
            canvas.set_dark(dark)
            canvas.set_tint(tint)
            ground = canvas.background()[0]
            grid = canvas.ground_grid("#c3c8cc")
            self.assertAlmostEqual(lightness(grid) - lightness(ground), 0.08, delta=0.01)
        canvas.set_dark(False)
        canvas.set_tint("#bfb2a4")                                  # (a light palette: «bege»)
        ground = canvas.background()[0]
        self.assertAlmostEqual(lightness(ground) - lightness(canvas.ground_grid("#c3c8cc")), 0.14, delta=0.01)


class DarkTheme(unittest.TestCase):
    """0.338 — the two themes: the same colours named in both; the dark one's palette (the prototype's greys) on the
    Qt windows, the light one's the style's own again; an icon drawn for the light theme in the dark one — its black
    ink light, its white fill dark grey, its blue as it was —, the same pair when drawn again, back to the light one;
    the icons of a window's actions and buttons put in the theme in use."""

    def tearDown(self):
        from arqbim.ui import theme
        theme.apply("light")

    def test_palettes(self):
        from arqbim.ui import theme
        self.assertEqual(set(theme.THEMES["light"]), set(theme.THEMES["dark"]))
        theme.apply("dark")
        self.assertTrue(theme.is_dark())
        self.assertEqual((APP.palette().window().color().name(), APP.palette().text().color().name()),
                         ("#17191c", "#dde1e6"))
        self.assertEqual((theme.C["header"], theme.C["accent"]), ("#111316", "#f0b44c"))
        theme.apply("light")
        self.assertEqual(APP.palette().window().color().name(), APP.style().standardPalette().window().color().name())
        self.assertEqual(theme.C["header"], "#1f2a37")
        self.assertEqual(theme.qcolor("rgba(91,156,255,46)").getRgb(), (91, 156, 255, 46))
        self.assertEqual(theme.qcolor((47, 111, 228)).name(), "#2f6fe4")
        self.assertEqual(theme.apply("purple"), "light")
        from arqbim.ui import caixilho_studio as cs                 # (0.339) the studio takes the theme in use
        theme.apply("dark")
        cs.use_theme()
        self.assertEqual((cs.THEME, cs.BG, cs.ACCENT, cs.C["header"]), ("dark", "#17191c", "#f0b44c", "#111316"))
        theme.apply("light")
        cs.use_theme()
        self.assertEqual((cs.THEME, cs.BG, cs.ACCENT), ("light", "#ffffff", "#2f6fe4"))
        # (0.374) the owner's study's palettes: its nine colours in the theme, the Qt windows in them; dark ones dark
        theme.apply("bege")
        self.assertEqual((theme.C["header"], theme.C["bar"], theme.C["panel"]), ("#d9c5ae", "#e7d6c3", "#e6d4c1"))
        self.assertEqual((APP.palette().window().color().name(), theme.is_dark()), ("#e6d4c1", False))
        theme.apply("grafite")
        self.assertTrue(theme.is_dark())
        self.assertTrue(set(theme.THEMES["light"]) <= set(theme.C))           # (every key the program uses)
        theme.apply("light")

    def test_minimal_study_themes(self):
        from arqbim.ui import theme, ribbon, minimal_icons
        from arqbim.i18n import has
        self.assertEqual(set(theme.STUDY), {"bege", "pedra", "escuro", "grafite", "revit"})
        self.assertNotIn("theme_areia", ribbon.items_of("view"))
        self.assertIn("theme_revit", ribbon.items_of("view"))
        for name in theme.STUDY:
            theme.apply(name)
            self.assertTrue(has("act.theme_" + name))
            self.assertEqual(APP.palette().highlight().color().name(), theme.STUDY[name]["accent"])
            self.assertIn("background: %s" % theme.C["bar"], ribbon.header_style())
            for key in minimal_icons.SHAPES:
                image = minimal_icons.icon(key).pixmap(32, 32).toImage()
                self.assertFalse(image.isNull())
                self.assertTrue(any(image.pixelColor(x, y).alpha() for x in range(32) for y in range(32)))
        self.assertIsNone(minimal_icons.icon("unknown"))

    def test_icons(self):
        from arqbim.ui import theme
        pm = QtGui.QPixmap(16, 16)
        pm.fill(QtCore.Qt.GlobalColor.transparent)
        p = QtGui.QPainter(pm)
        p.fillRect(0, 0, 16, 4, QtGui.QColor("#222222"))            # the ink
        p.fillRect(0, 4, 16, 4, QtGui.QColor("#ffffff"))            # a paper fill
        p.fillRect(0, 8, 16, 4, QtGui.QColor("#2f6fe4"))            # the blue
        p.end()

        def at(icon, y):
            return icon.pixmap(16, 16).toImage().pixelColor(8, y)

        light = theme.icon(pm)
        self.assertEqual((at(light, 1).name(), at(light, 5).name()), ("#222222", "#ffffff"))
        theme.apply("dark")
        dark = theme.themed(light)
        self.assertNotEqual(dark.cacheKey(), light.cacheKey())
        self.assertGreater(at(dark, 1).lightness(), 190)
        self.assertLess(at(dark, 5).lightness(), 90)
        self.assertEqual(at(dark, 9).name(), "#2f6fe4")
        self.assertEqual(at(dark, 14).alpha(), 0)
        self.assertEqual(theme.icon(pm).cacheKey(), dark.cacheKey())          # (drawn again: the same pair)
        window = QtWidgets.QWidget()
        action = QtGui.QAction(light, "x", window)
        window.addAction(action)
        button = QtWidgets.QToolButton(window)
        button.setIcon(light)
        theme.retheme_icons(window)
        self.assertEqual((action.icon().cacheKey(), button.icon().cacheKey()), (dark.cacheKey(), dark.cacheKey()))
        theme.apply("light")
        self.assertEqual(theme.themed(dark).cacheKey(), light.cacheKey())
        theme.retheme_icons(window)
        self.assertEqual(button.icon().cacheKey(), light.cacheKey())
        window.deleteLater()


if __name__ == "__main__":
    unittest.main()
