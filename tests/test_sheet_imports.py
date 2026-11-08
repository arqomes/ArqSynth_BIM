"""0.472 — Drawings from outside on a sheet (DWG/DXF, pictures, SVG) and the company's own title block."""

import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model import sheets as sm  # noqa: E402
from arqbim.model.document import Document  # noqa: E402

DXF = """0
SECTION
2
HEADER
9
$INSUNITS
70
4
0
ENDSEC
0
SECTION
2
ENTITIES
0
LINE
8
0
10
0
20
0
11
2000
21
0
0
LINE
8
0
10
2000
20
0
11
2000
21
1000
0
TEXT
8
0
10
100
20
500
40
100
1
Pormenor A
0
ENDSEC
0
EOF
"""


class Model(unittest.TestCase):
    """The kinds by extension; a drawing put on a sheet saved and read back — its file found beside the project when
    the folder moved; the company's title block (0.472's rows: read as a drawing), its size, kept by the project's
    fields."""

    def test_kinds_and_dict(self):
        self.assertEqual([sm.import_kind(p) for p in ("a.DWG", "b.dxf", "c.svg", "d.png", "e.JPG", "f.txt")],
                         ["cad", "cad", "svg", "image", "image", None])
        with tempfile.TemporaryDirectory() as tmp:
            project = os.path.join(tmp, "obra")
            os.makedirs(os.path.join(project, "desenhos"))
            path = os.path.join(project, "desenhos", "planta.dxf")
            with open(path, "w") as f:
                f.write(DXF)
            item = sm.SheetImport("cad", path, "planta.dxf", (100.0, 80.0), scale=20, units=0.001)
            sheet = sm.Sheet("Folha 1", imports=[item])
            data = sm.to_dict(sheet, project)
            self.assertEqual(data["imports"][0]["relative"], os.path.join("desenhos", "planta.dxf"))
            moved = os.path.join(tmp, "obra2")
            shutil.move(project, moved)
            back = sm.from_dict(data, moved)
            self.assertEqual(len(back.imports), 1)
            self.assertEqual(back.imports[0].path, os.path.join(moved, "desenhos", "planta.dxf"))
            self.assertEqual((back.imports[0].scale, back.imports[0].at, back.imports[0].uid),
                             (20, (100.0, 80.0), item.uid))

    def test_company(self):
        """(0.473) 0.472's rows of boxes, read: a drawing — its logo's box, the company's name and contacts as texts,
        a field in each box — as large as the rows were (170 × 57,5 mm)."""
        company = sm.clean_company(dict(sm.DEFAULT_ROWS, name="Atelier X", contacts="Rua A, 1\nLisboa"))
        kinds = [i["kind"] for i in company["items"]]
        self.assertEqual(kinds.count("image"), 1)
        texts = [i["text"] for i in company["items"] if i["kind"] == "text"]
        self.assertIn("Atelier X", texts)
        self.assertIn("Rua A, 1\nLisboa", texts)
        fields = {i["field"] for i in company["items"] if i["kind"] == "field"}
        self.assertEqual(fields, {"project", "client", "site", "author", "stage", "title", "scale", "date", "number"})
        self.assertEqual(sm.drawn_size(company["items"]), (170.0, 57.5))
        sm.use_company(company)
        self.assertEqual(sm.block_size("custom"), (170.0, 57.5))
        self.assertIsNone(sm.clean_company({"rows": [{"h": 5, "cells": [["nada", 1]]}]}))
        read = sm.read_title_fields({"project": "Moradia", sm.COMPANY_KEY: company})
        self.assertEqual(read[sm.COMPANY_KEY], company)
        self.assertEqual(sm.title_texts(read, "Planta", "01", "obra")["project"], "Moradia")
        self.assertIn("custom", sm.TEMPLATES)


class DocumentSheets(unittest.TestCase):
    """In a project: a DXF put on a sheet (one undo step), moved, given another scale, taken off; the company's title
    block given to every sheet (their template «custom»), kept when the project's fields change, saved and opened
    again with the drawing; the PDF of a sheet with only a drawing on it."""

    def test_document(self):
        doc = Document()
        bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        k = doc.add_sheet()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "detalhe.dxf")
            with open(path, "w") as f:
                f.write(DXF)
            item = sm.SheetImport("cad", path, "detalhe.dxf", (150.0, 100.0), scale=20)
            doc.add_sheet_import(k, item)
            self.assertEqual(len(doc.sheets[k].imports), 1)
            doc.undo()
            self.assertEqual(len(doc.sheets[k].imports), 0)
            doc.redo()
            uid = doc.sheets[k].imports[0].uid
            doc.change_sheet_import(k, uid, at=(200.0, 120.0), scale=50)
            self.assertEqual((doc.sheets[k].imports[0].at, doc.sheets[k].imports[0].scale), ((200.0, 120.0), 50))
            company = {"items": [{"kind": "rect", "pts": [[-100, -30], [0, 0]], "pen": 0.35},
                                 {"kind": "text", "pts": [[-98, -28], [-40, -20]], "text": "Atelier X\nLisboa"},
                                 {"kind": "field", "pts": [[-98, -18], [-2, -10]], "field": "title", "size": 9}]}
            doc.set_company_title_block(company, [k])
            self.assertEqual(doc.sheets[k].template, "custom")
            self.assertEqual(doc.title_block[sm.COMPANY_KEY]["items"][1]["text"], "Atelier X\nLisboa")
            doc.set_title_block({"project": "Moradia T3"})
            self.assertEqual(len(doc.title_block[sm.COMPANY_KEY]["items"]), 3)        # (kept)
            ifc_path = os.path.join(tmp, "obra.ifc")
            doc.save(ifc_path)
            again = Document()
            again.open(ifc_path)
            self.assertEqual(again.sheets[k].template, "custom")
            self.assertEqual(again.title_block[sm.COMPANY_KEY], sm.clean_company(company))
            self.assertEqual([i.name for i in again.sheets[k].imports], ["detalhe.dxf"])
            doc.change_sheet_import(k, uid, remove=True)
            self.assertEqual(doc.sheets[k].imports, [])


class Painting(unittest.TestCase):
    """The size a drawing takes on the paper: a DXF of 2000 × 1000 mm at 1:20 — 100 × 50 mm (its text inside); a
    picture 80 mm wide in its proportions."""

    def test_sizes(self):
        from PySide6 import QtGui, QtWidgets
        _app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        from arqbim.ui import pdf
        with tempfile.TemporaryDirectory() as tmp:
            dxf = os.path.join(tmp, "d.dxf")
            with open(dxf, "w") as f:
                f.write(DXF)
            size = pdf.import_size(sm.SheetImport("cad", dxf, scale=20, units=0.001))
            self.assertAlmostEqual(size[0], 100.0, places=3)
            self.assertAlmostEqual(size[1], 50.0, places=3)
            png = os.path.join(tmp, "p.png")
            image = QtGui.QImage(400, 200, QtGui.QImage.Format.Format_RGB32)
            image.fill(QtGui.QColor("red"))
            self.assertTrue(image.save(png))
            self.assertEqual(pdf.import_size(sm.SheetImport("image", png, width=80.0)), (80.0, 40.0))
            picture = QtGui.QImage(420, 297, QtGui.QImage.Format.Format_RGB32)
            picture.fill(QtGui.QColor("white"))
            painter = QtGui.QPainter(picture)
            pdf.paint_imports(painter, 1.0, [sm.SheetImport("cad", dxf, at=(210.0, 148.0), scale=20, units=0.001),
                                             sm.SheetImport("image", png, at=(60.0, 60.0), width=80.0)])
            painter.end()
            self.assertEqual(picture.pixelColor(60, 60).name(), "#ff0000")      # (the picture there)
            dark = sum(1 for x in range(160, 261) if min(picture.pixelColor(x, y).lightness() for y in (172, 173, 174)) < 250)
            self.assertGreater(dark, 50)                                         # (the DXF's bottom line)


if __name__ == "__main__":
    unittest.main()
