"""0.473 — The company's title block drawn by hand on the sheet: its items, its size from the corner, the views kept
clear of it (above it, or beside it when it goes up the side), its fields, the office's copy with its pictures, and
how it is painted."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

from arqbim.model import sheets as sm  # noqa: E402


class Items(unittest.TestCase):
    """What an item may be: a known kind, two points, a known field; its thickness and size within reason."""

    def test_clean(self):
        self.assertIsNone(sm.clean_item({"kind": "circle", "pts": [[0, 0], [1, 1]]}))
        self.assertIsNone(sm.clean_item({"kind": "line", "pts": [[0, 0]]}))
        self.assertIsNone(sm.clean_item({"kind": "line", "pts": [[0, 0], [float("nan"), 1]]}))
        self.assertIsNone(sm.clean_item({"kind": "field", "pts": [[0, 0], [1, 1]], "field": "senha"}))
        line = sm.clean_item({"kind": "line", "pts": [[-10, -5], [0, -5]], "pen": 9})
        self.assertEqual((line["pen"], line["pts"]), (3.0, [[-10.0, -5.0], [0.0, -5.0]]))
        rect = sm.clean_item({"kind": "rect", "pts": [[-10, -5], [0, 0]], "fill": "vermelho"})
        self.assertEqual(rect["fill"], "")
        own = sm.clean_item({"kind": "field", "pts": [[-50, -8], [0, -3]], "field": "extra:Processo n.º"})
        self.assertEqual((own["field"], own["align"], own["colour"]), ("extra:Processo n.º", "left", "#000000"))
        self.assertEqual(sm.clean_company({"items": []}), {"items": []})          # (all taken away: allowed)


class Size(unittest.TestCase):
    """How far it goes from the corner; the views above it, or beside a strip going up the side."""

    def test_size_and_area(self):
        full = sm.template_items("full")
        self.assertEqual(sm.drawn_size(full), (120.0, 40.0))
        sm.use_company({"items": full})
        self.assertFalse(sm.block_beside((420.0, 297.0), "custom"))
        self.assertEqual(sm.drawing_area("A3", "custom"), sm.drawing_area("A3", "full"))
        strip = sm.template_items("strip", 297.0 - 2 * sm.MARGIN)
        self.assertEqual(sm.drawn_size(strip), (50.0, 277.0))
        sm.use_company({"items": strip})
        self.assertTrue(sm.block_beside((420.0, 297.0), "custom"))
        left, top, width, height = sm.drawing_area("A3", "custom")
        self.assertAlmostEqual(width, 420.0 - 2 * sm.MARGIN - 50.0 - 12, places=6)
        self.assertAlmostEqual(height, 297.0 - 2 * sm.MARGIN - 8, places=6)
        sm.use_company({"items": []})
        self.assertEqual(sm.drawing_area("A3", "custom"), (14.0, 14.0, 392.0, 269.0))
        sm.use_company(None)
        self.assertEqual(sm.drawn_size(sm.company()["items"]), (170.0, 57.5))       # (the program's own)


class Fields(unittest.TestCase):
    """What a field shows: the project's, the sheet's, its last revision, how many sheets, the project's own."""

    def test_texts(self):
        fields = {"project": "Moradia T3", sm.EXTRA_KEY: [["Processo n.º", "123/2026"]]}
        texts = sm.title_texts(fields, "Planta do piso 0", "A-02", "obra", [{"code": "A", "date": "", "text": "x"},
                                                                        {"code": "B", "date": "", "text": "y"}], 7)
        self.assertEqual((sm.field_text(texts, "project"), sm.field_text(texts, "title"),
                          sm.field_text(texts, "revision"), sm.field_text(texts, "count")),
                         ("Moradia T3", "Planta do piso 0", "B", "7"))
        self.assertEqual(sm.field_text(texts, "extra:Processo n.º"), "123/2026")
        self.assertEqual(sm.field_text(texts, "extra:Outro"), "")


class Office(unittest.TestCase):
    """«Guardar no escritório»: the drawing in the suite's folder, its picture copied beside it under a name of its
    own; read back with the picture found there. 0.472's file (rows, a logo beside it) read as a drawing."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get("ARQSYNTH_HOME")
        os.environ["ARQSYNTH_HOME"] = os.path.join(self.tmp.name, "suite")

    def tearDown(self):
        if self.old is None:
            os.environ.pop("ARQSYNTH_HOME", None)
        else:
            os.environ["ARQSYNTH_HOME"] = self.old
        self.tmp.cleanup()

    def test_save_and_load(self):
        from arqbim.model import company_title_block as office
        logo = os.path.join(self.tmp.name, "logo.png")
        with open(logo, "wb") as f:
            f.write(b"\x89PNG not really")
        company = {"items": [{"kind": "image", "pts": [[-40, -20], [-2, -2]], "path": logo},
                             {"kind": "text", "pts": [[-90, -20], [-42, -12]], "text": "Atelier"}]}
        where = office.save(company)
        with open(where, encoding="utf-8") as f:
            stored = json.load(f)["items"][0]["path"]
        self.assertTrue(stored.startswith(office.PICTURE) and not os.path.isabs(stored))
        os.remove(logo)                                    # (the original gone: the copy is used)
        back = office.load()
        self.assertTrue(os.path.isfile(back["items"][0]["path"]))
        self.assertEqual(back["items"][1]["text"], "Atelier")
        with open(where, "w", encoding="utf-8") as f:      # (0.472's file)
            json.dump(dict(sm.DEFAULT_ROWS, name="Atelier Antigo", logo="carimbo_logotipo.png"), f)
        old = office.load()
        self.assertIn("Atelier Antigo", [i.get("text") for i in old["items"]])
        image = next(i for i in old["items"] if i["kind"] == "image")
        self.assertEqual(image["path"], os.path.join(os.environ["ARQSYNTH_HOME"], "carimbo_logotipo.png"))


class Painting(unittest.TestCase):
    """The drawing painted on the paper: a black rectangle filled, a field with the sheet's text in its box; an empty
    field shows nothing on paper (its name only while the title block is drawn)."""

    def test_paint(self):
        from PySide6 import QtGui, QtWidgets
        _app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        from arqbim.ui import pdf
        items = [sm.clean_item({"kind": "rect", "pts": [[-30, -20], [-20, -10]], "fill": "#000000", "pen": 0.25}),
                 sm.clean_item({"kind": "field", "pts": [[-90, -20], [-35, -10]], "field": "title", "size": 24}),
                 sm.clean_item({"kind": "field", "pts": [[-90, -8], [-35, -2]], "field": "client", "size": 12})]

        def painted(placeholders):
            picture = QtGui.QImage(420, 297, QtGui.QImage.Format.Format_RGB32)
            picture.fill(QtGui.QColor("white"))
            painter = QtGui.QPainter(picture)
            pdf.paint_drawn(painter, 1.0, 410.0, 287.0, items, {"title": "PLANTA"}, placeholders=placeholders)
            painter.end()
            return picture

        def ink(picture, x0, y0, x1, y1):
            return sum(1 for x in range(x0, x1) for y in range(y0, y1) if picture.pixelColor(x, y).lightness() < 200)
        paper = painted(False)
        self.assertEqual(paper.pixelColor(385, 272).name(), "#000000")           # (inside the filled rectangle)
        self.assertGreater(ink(paper, 320, 267, 375, 277), 20)                   # (PLANTA)
        self.assertEqual(ink(paper, 320, 279, 375, 285), 0)                      # (no client: nothing)
        drawn = painted(True)
        grey = sum(1 for x in range(320, 375) for y in range(279, 285)
                   if drawn.pixelColor(x, y).name() != "#ffffff")
        self.assertGreater(grey, 5)                                              # («‹Dono de obra›» while drawn)


if __name__ == "__main__":
    unittest.main()
