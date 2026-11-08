"""(0.470) Sheets: A4 among the papers and a paper stood up (the owner: «deve incluir tamanho A4»); a sheet's type
(paper, how it stands, its title block) given to several at once, one undo step; the navigator's Folhas tab, last
(«Colocar a opção de filtro da folha também no rodapé… deve ficar última aba»); a sheet's properties in the
Properties panel with «Editar tipo…» and its own window («A edição do tipo da folha e propriedades devem ficar na
coluna de propriedade. E a edição numa janela própria que abre como no revit»); zoom on the sheet («permitir zoom na
folha»)."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "/tmp"), "arqbim_test_cache"))

from PySide6 import QtCore, QtWidgets  # noqa: E402

APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from arqbim.model import sheets as sheets_model  # noqa: E402
from arqbim.model.document import Document  # noqa: E402


class Papers(unittest.TestCase):
    def test_a4_and_portrait(self):
        self.assertEqual(list(sheets_model.PAPERS)[0], "A4")
        self.assertEqual(sheets_model.paper_size("A4"), (297.0, 210.0))
        self.assertEqual(sheets_model.paper_size("A4", portrait=True), (210.0, 297.0))
        sheet = sheets_model.Sheet("Folha", "A4", portrait=True, template="compact")
        self.assertEqual(sheet.size(), (210.0, 297.0))
        self.assertEqual(sheet.kind, ("A4", True, "compact"))
        again = sheets_model.from_dict(sheets_model.to_dict(sheet))
        self.assertEqual(again.kind, sheet.kind)
        self.assertFalse(sheets_model.from_dict(sheets_model.to_dict(sheets_model.Sheet("Velha"))).portrait)
        left, top, w, h = sheets_model.drawing_area("A4", "compact", portrait=True)
        self.assertLess(w, h)                                     # (standing: taller than wide)
        bx, by, bw, bh = sheets_model.title_box(sheet.size(), "compact")
        self.assertLessEqual(bx + bw, 210.0 - sheets_model.MARGIN + 1e-6)

    def test_sheet_type_undo(self):
        doc = Document()
        try:
            doc.make_sheets([("A", []), ("B", []), ("C", [])], "A3", "full")
            doc.set_sheet_type([0, 2], "A4", True, "strip", fields={"client": "Câmara"})
            self.assertEqual([s.kind for s in doc.sheets],
                             [("A4", True, "strip"), ("A3", False, "full"), ("A4", True, "strip")])
            self.assertEqual(doc.title_block.get("client"), "Câmara")
            doc.undo()
            self.assertEqual({s.kind for s in doc.sheets}, {("A3", False, "full")})
            self.assertNotIn("client", doc.title_block)
        finally:
            doc.modified = False


class FolhasTab(unittest.TestCase):
    def test_tab(self):
        from arqbim.ui.project_tree import SCOPES, ProjectTree
        self.assertEqual(SCOPES[-1], "sheets")                    # (the last: the last thing done)
        panel = ProjectTree(None)
        panel.show_project(None, [], {"sheets": [("Folha 1", [("Planta — Térreo", "plan", "g1")]),
                                                 ("Folha 2", [])]})
        panel.set_scope("sheets")
        self.assertEqual(panel.scope_bar.tabText(panel.scope_bar.currentIndex()), "Folhas")
        root = panel.tree.rootIndex()
        self.assertTrue(root.isValid())
        self.assertEqual(panel.tree.itemFromIndex(root).data(0, QtCore.Qt.ItemDataRole.UserRole), ("views", "sheets"))
        self.assertTrue(panel.in_scope(("sheet", 0)) and not panel.in_scope(("views", "plans")))
        asked = []
        panel.on_sheet = lambda *a: asked.append(a)
        panel._later = lambda f, *a: f(*a)
        panel._clicked(panel._items[("sheet", 1)], 0)             # (one click: its properties)
        self.assertEqual(asked, [("props", 1)])
        menu = panel.menu_for(("sheet", 0), panel._items[("sheet", 0)])
        self.assertIn("Editar tipo…", [a.text() for a in menu.actions()])
        panel.set_scope("all")
        self.assertFalse(panel.tree.rootIndex().isValid())
        self.assertTrue(panel.focus(("views", "sheets")))         # (the module bar's Folhas: still shown)
        panel.set_scope("views")
        panel.deleteLater()


class SheetProperties(unittest.TestCase):
    def test_panel_and_window(self):
        from arqbim.ui.properties import PropertiesPanel
        from arqbim.ui.sheet_type_dialog import RevisionsDialog, SheetTypeDialog, kinds
        doc = Document()
        try:
            doc.make_sheets([("Plantas", []), ("Alçados", [])], "A3", "full")
            sheet = doc.sheets[0]
            self.assertEqual(len(kinds()), len(sheets_model.PAPERS) * 2 * len(sheets_model.TEMPLATES))
            panel = PropertiesPanel(None)
            edits = []
            panel.on_edit = lambda action, guid, value: edits.append((action, guid, value))
            panel.show_sheet(doc, sheet, "01", kinds(), "Casa")
            self.assertEqual(panel.header_title.text(), "Plantas")
            self.assertEqual(panel.type_combo.currentText(), "A3 horizontal · Completo")
            self.assertIn("sheet_edit_type", panel.editors)
            self.assertEqual(panel.editors["sheet_number"].placeholderText(), "01 (automático)")
            combo = panel.editors["sheet_type"]
            k = next(i for i in range(combo.count()) if tuple(combo.itemData(i)) == ("A4", False, "full"))
            combo.activated.emit(k)
            panel.editors["sheet_edit_type"].click()
            for _ in range(5):
                APP.processEvents()
            self.assertEqual(edits, [("sheet_type", sheet.uid, ("A4", False, "full")),
                                     ("sheet_edit_type", sheet.uid, None)])
            text = panel.text() if hasattr(panel, "text") else ""
            self.assertIn("Carimbo (em todas as folhas)", text)
            # the type's own window
            dialog = SheetTypeDialog(None, sheet, doc.sheets, {"client": "Câmara"}, "Casa", "01")
            self.assertEqual(dialog.kind(), ("A3", False, "full"))
            self.assertIn("(2)", dialog.all_of_type.text())                # (both sheets are of its type)
            dialog.paper.setCurrentIndex(dialog.paper.findData("A4"))
            dialog.way.setCurrentIndex(1)
            self.assertEqual(dialog.kind(), ("A4", True, "full"))
            self.assertEqual(dialog.type_name.text(), "A4 vertical · Completo")
            self.assertEqual(dialog.picture.kind, ("A4", True, "full"))
            self.assertTrue(dialog.everyone())
            dialog.only_this.setChecked(True)
            self.assertFalse(dialog.everyone())
            self.assertEqual(dialog.fields()["client"], "Câmara")
            revisions = RevisionsDialog(None, sheet)
            revisions.new_revision("Licenciamento")
            self.assertEqual([r["code"] for r in revisions.revisions()], ["A"])
            for w in (dialog, revisions, panel):
                w.deleteLater()
        finally:
            doc.modified = False


class SheetZoom(unittest.TestCase):
    def test_zoom(self):
        from arqbim.ui.sheet_view import SheetWindow
        sheet = sheets_model.Sheet("Folha")
        host = types.SimpleNamespace(doc=types.SimpleNamespace(sheets=[sheet]))
        window = SheetWindow(host)
        window._uid = sheet.uid
        canvas = window.canvas
        canvas.resize(800, 600)
        s0, x0, y0 = canvas.fit()
        at = QtCore.QPointF(300.0, 200.0)
        before = canvas.to_mm(at)
        canvas.zoom_at(2.0, at)
        s1, _x, _y = canvas.fit()
        self.assertAlmostEqual(s1, 2.0 * s0)
        after = canvas.to_mm(at)
        self.assertAlmostEqual(before[0], after[0], places=6)       # (the paper under the mouse stays under it)
        self.assertAlmostEqual(before[1], after[1], places=6)
        canvas.zoom_at(1 / 10.0)                                    # (no farther than the whole sheet)
        self.assertEqual((canvas.zoom, canvas.pan), (1.0, (0.0, 0.0)))
        canvas.zoom_at(3.0)
        canvas.fit_all()
        self.assertEqual(canvas.fit(), (s0, x0, y0))
        window.deleteLater()


if __name__ == "__main__":
    unittest.main()
