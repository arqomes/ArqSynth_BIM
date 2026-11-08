"""(0.478) A table of the project's own as a spreadsheet (model/table_sheet): its zones, formulas written as in Excel and
kept by zone and field (still right when the model has more or fewer elements, or the columns change), merges, formats,
borders, rows put and taken away, the project's data in a text, the workbook's formulas."""

import unittest

from arqbim.model import schedules
from arqbim.model import table_sheet as ts

KEYS = ["name", "length", "height"]


def grid(layout, n=3, keys=KEYS, tokens=None):
    headings = {"name": "Nome", "length": "Comprimento", "height": "Altura", "area": "Área"}
    values = {"name": lambda k: "P{}".format(k + 1), "length": lambda k: float(k + 2), "height": lambda k: 2.8,
              "area": lambda k: 10.0}
    data = [[values[c](k) for c in keys] for k in range(n)]
    totals = [("Total: {}".format(n) if c == "name" else sum(r[j] for r in data) if c in ("length", "area") else None)
              for j, c in enumerate(keys)]
    return ts.build(layout, keys, [headings[c] for c in keys], data, totals, tokens=tokens)


def at(a1):
    letters = "".join(ch for ch in a1 if ch.isalpha())
    return int("".join(ch for ch in a1 if ch.isdigit())) - 1, ts.col_index(letters)


def text(rows, a1):
    g, c = at(a1)
    return rows[g][c].text


def write(layout, geom, a1, value):
    g, c = at(a1)
    return ts.set_value(layout, geom, g, c, value)


class Letters(unittest.TestCase):
    def test_columns(self):
        self.assertEqual([ts.col_letter(k) for k in (0, 1, 25, 26, 27)], ["A", "B", "Z", "AA", "AB"])
        self.assertEqual([ts.col_index(x) for x in ("A", "Z", "AA", "AB")], [0, 25, 26, 27])


class Zones(unittest.TestCase):
    def test_rows_of_each_zone(self):
        rows, geom = grid(ts.Layout(top=2, bottom=1))
        self.assertEqual(geom.rows, 2 + 1 + 3 + 1 + 1)
        self.assertEqual([geom.zone_of(g) for g in range(geom.rows)],
                         [("T", 0), ("T", 1), ("H", 0), ("D", 0), ("D", 1), ("D", 2), ("S", 0), ("N", 0)])
        self.assertEqual(geom.grid_row("N", 0), 7)
        self.assertEqual(text(rows, "A3"), "Nome")
        self.assertEqual(text(rows, "B4"), "2")
        self.assertEqual(text(rows, "B7"), "9")
        self.assertEqual(text(rows, "A7"), "Total: 3")


class Formulas(unittest.TestCase):
    def test_kept_by_zone_and_still_right_with_more_rows(self):
        layout = ts.Layout(top=1, bottom=1)                         # (T1, H2, D3-5, S6, N7)
        _rows, geom = grid(layout)
        layout = write(layout, geom, "B7", "=SOMA(B3:B5)*1,23")
        kept = layout.cells["N:0:length"]["v"]
        self.assertEqual(kept, "=SOMA([D1@length]:[D3@length])*1,23")
        rows, geom = grid(layout)
        self.assertEqual(text(rows, "B7"), "11,07")                 # 9 × 1,23
        self.assertEqual(rows[6][1].raw, "=SOMA(B3:B5)*1,23")
        layout = ts.insert_rows(layout, "T", 0)                     # (a title row more over it: the same cells)
        moved, geom = grid(layout)
        self.assertEqual(moved[7][1].raw, "=SOMA(B4:B6)*1,23")
        self.assertEqual(text(moved, "B8"), "11,07")

    def test_follows_its_field_when_the_columns_change(self):
        layout = ts.Layout(bottom=1)                                # (H1, D2-4, S5, N6)
        _rows, geom = grid(layout)
        layout = write(layout, geom, "A6", "=SOMA(B:B)")
        layout = write(layout, geom, "B6", "nota")                  # (a note under the lengths)
        layout = ts.set_format(layout, geom, [(1, 1)], b=True)      # (the elements' column B: bold)
        rows, geom = grid(layout, keys=["name", "area", "length"])  # (a column put before it)
        self.assertEqual(rows[5][0].raw, "=SOMA(C:C)")
        self.assertEqual(text(rows, "A6"), "9")
        self.assertEqual(text(rows, "C6"), "nota")                  # (the note went with its column)
        self.assertTrue(rows[1][2].fmt.get("b") and not rows[1][1].fmt.get("b"))
        rows, geom = grid(layout, keys=["name", "height"])          # (its field taken away)
        self.assertEqual(text(rows, "A6"), "#REF!")

    def test_column_of_the_elements(self):
        layout = ts.Layout(bottom=2)                                # (H1, D2-4, S5, N6-7)
        _rows, geom = grid(layout)
        layout = write(layout, geom, "B6", "=soma(b:b)")
        layout = write(layout, geom, "B7", "=MÉDIA(B:B)")
        rows, geom = grid(layout, n=5)                              # (H1, D2-6, S7, N8-9)
        self.assertEqual(text(rows, "B8"), "20")                    # 2+3+4+5+6
        self.assertEqual(text(rows, "B9"), "4")
        self.assertEqual(rows[7][1].raw, "=SOMA(B:B)")

    def test_functions_and_errors(self):
        layout = ts.Layout(bottom=6)                                # (B5 the totals: 9; the notes B6-B11)
        _rows, geom = grid(layout)
        for a1, formula in (("B6", "=ARRED(10/3;2)"), ("B7", "=SE(B5>2;\"comprida\";\"curta\")"), ("B8", "=1/0"),
                            ("B9", "=XPTO(1)"), ("B10", "=B99"), ("B11", "=B5+1"), ("C11", "=B11*2"),
                            ("C10", "=B7+1"), ("C9", "=MÁXIMO(B2:B4;7)")):
            layout = write(layout, geom, a1, formula)
        rows, geom = grid(layout)
        self.assertEqual([text(rows, x) for x in ("B6", "B7", "B8", "B9", "B10", "B11", "C11", "C10", "C9")],
                         ["3,33", "comprida", "#DIV/0!", "#NOME?", "#REF!", "10", "20", "#VALOR!", "7"])

    def test_loop(self):
        layout = ts.Layout(bottom=2)
        _rows, geom = grid(layout)
        layout = write(layout, geom, "B6", "=B7")
        layout = write(layout, geom, "B7", "=B6")
        rows, _geom = grid(layout)
        self.assertEqual(text(rows, "B6"), "#CIRC!")

    def test_nothing_else_runs(self):
        layout = ts.Layout(bottom=1)
        _rows, geom = grid(layout)
        for formula in ("=__import__(\"os\")", "=(1).real", "=[1,2]", "=_sum(1)"):
            rows, _g = grid(write(layout, geom, "A6", formula))
            self.assertTrue(text(rows, "A6").startswith("#"), formula)

    def test_the_elements_rows_are_the_model(self):
        layout = ts.Layout()
        _rows, geom = grid(layout)
        self.assertIsNone(write(layout, geom, "B3", "7"))

    def test_heading_renamed_and_total_overwritten(self):
        layout = ts.Layout()                                        # (H1, D2-4, S5)
        _rows, geom = grid(layout)
        layout = write(layout, geom, "B1", "Comp. (m)")
        layout = write(layout, geom, "B5", "=SOMA(B:B)*2")
        rows, _geom = grid(layout)
        self.assertEqual(text(rows, "B1"), "Comp. (m)")
        self.assertEqual(text(rows, "B5"), "18")

    def test_project_data_in_a_text(self):
        layout = ts.Layout(top=1)
        _rows, geom = grid(layout)
        layout = write(layout, geom, "A1", "{projeto} — {n} paredes")
        rows, _geom = grid(layout, tokens={"projeto": "Moradia", "n": 3})
        self.assertEqual(text(rows, "A1"), "Moradia — 3 paredes")
        self.assertEqual(rows[0][0].raw, "{projeto} — {n} paredes")


class Rows(unittest.TestCase):
    def test_put_and_taken_away(self):
        layout = ts.Layout(bottom=2)                                # (H1, D2-4, S5, N6-7)
        _rows, geom = grid(layout)
        layout = write(layout, geom, "B7", "=B5*2")                 # (the totals × 2)
        layout = write(layout, geom, "A6", "Nota")
        layout = ts.insert_rows(layout, "N", 0)                     # (a row above the note: N6-8)
        self.assertEqual(layout.bottom, 3)
        self.assertEqual(layout.cells["N:1:name"]["v"], "Nota")
        rows, geom = grid(layout)
        self.assertEqual(text(rows, "B8"), "18")
        layout = write(layout, geom, "C8", "=A7")                   # (points at the note)
        layout = ts.delete_rows(layout, "N", 1)                     # (the note's row gone: N6-7)
        self.assertEqual(layout.bottom, 2)
        rows, _geom = grid(layout)
        self.assertEqual(text(rows, "C7"), "#REF!")
        self.assertEqual(text(rows, "B7"), "18")

    def test_top_rows_move_what_points_at_them(self):
        layout = ts.Layout(top=1)                                   # (T1, H2, D3-5, S6)
        _rows, geom = grid(layout)
        layout = write(layout, geom, "A1", "Mapa de paredes")
        layout = write(layout, geom, "C6", "=A1")
        layout = ts.insert_rows(layout, "T", 0)
        rows, _geom = grid(layout)
        self.assertEqual(text(rows, "A2"), "Mapa de paredes")
        self.assertEqual(text(rows, "C7"), "Mapa de paredes")


class Formats(unittest.TestCase):
    def test_merge_format_and_borders(self):
        layout = ts.Layout(top=1)                                   # (T1, H2, D3-5, S6)
        _rows, geom = grid(layout)
        layout = ts.merge(layout, geom, 0, 0, 0, 2)
        self.assertIsNone(ts.merge(layout, geom, 2, 0, 3, 0))       # (the elements' rows: not)
        self.assertIsNone(ts.merge(layout, geom, 0, 0, 1, 0))       # (across zones: not)
        self.assertEqual(ts.merges_in_grid(layout, geom), [(0, 0, 1, 3)])
        self.assertEqual(layout.merges, [["T", 0, "name", 1, 3]])
        self.assertEqual(ts.merge_at(layout, geom, 0, 2), (0, 0, 1, 3))
        layout = ts.set_format(layout, geom, [(0, 0)], b=True, a="center", f="#FFF2CC")
        layout = ts.set_format(layout, geom, [(4, 1)], a="right")  # (an element's cell: its column)
        self.assertEqual(layout.cells["T:0:name"], {"b": True, "a": "center", "f": "#fff2cc"})
        self.assertEqual(layout.cells["D:*:length"], {"a": "right"})
        layout = ts.set_borders(layout, geom, 1, 0, 5, 2, "outer")  # (the headings to the totals)
        self.assertEqual(layout.cells["H:0:name"].get("bd"), "lt")
        self.assertEqual(layout.cells["S:0:height"].get("bd"), "rb")
        self.assertEqual(layout.cells["D:*:name"].get("bd"), "l")
        layout = ts.set_borders(layout, geom, 2, 0, 4, 2, "outer")  # (the elements' rows: over and under them)
        self.assertEqual(layout.cells["H:0:length"].get("bd"), "tb")
        self.assertEqual(layout.cells["S:0:length"].get("bd"), "tb")
        layout = ts.set_borders(layout, geom, 1, 0, 5, 2, "none")
        self.assertNotIn("bd", layout.cells.get("H:0:name", {}))
        layout = ts.unmerge(layout, geom, 0, 1)
        self.assertEqual(layout.merges, [])

    def test_merged_heading_follows_its_field(self):
        layout = ts.Layout()
        _rows, geom = grid(layout)
        layout = ts.merge(layout, geom, 0, 1, 0, 2)                 # (Comprimento + Altura)
        self.assertEqual(layout.merges, [["H", 0, "length", 1, 2]])
        _rows, geom = grid(layout, keys=["length", "height", "name"])
        self.assertEqual(ts.merges_in_grid(layout, geom), [(0, 0, 1, 2)])

    def test_kept_in_the_file(self):
        defn = schedules.ScheduleDef("Paredes", "walls", ["name", "length"])
        layout = ts.Layout(top=1, bottom=1)
        layout.cells["T:0:name"] = {"v": "Mapa", "b": True}
        layout.cells["D:*:length"] = {"a": "right", "bd": "lr"}
        layout.merges.append(["T", 0, "name", 1, 2])
        again = schedules.def_from_dict(schedules.def_to_dict(schedules.with_layout(defn, layout)))
        back = schedules.layout_of(again)
        self.assertEqual((back.top, back.bottom, back.cells, back.merges), (1, 1, layout.cells, [["T", 0, "name", 1, 2]]))
        self.assertNotIn("grid", schedules.def_to_dict(defn))       # (none: the file as older versions wrote)

    def test_excel(self):
        layout = ts.Layout(top=1, bottom=1)                         # (T1, H2, D3-5, S6, N7)
        _rows, geom = grid(layout)
        layout = write(layout, geom, "B7", "=ARRED(SOMA(B:B)*1,23;2)")
        layout = write(layout, geom, "C7", "=B6+C6")
        _rows, geom = grid(layout)
        self.assertEqual(ts.to_excel(layout.cells["N:0:length"]["v"], geom), "=ROUND(SUM(B3:B5)*1.23,2)")
        self.assertEqual(ts.to_excel(layout.cells["N:0:height"]["v"], geom), "=B6+C6")
        self.assertIsNone(ts.to_excel("=[N9@length]", geom))         # (a row not there)
        self.assertIsNone(ts.to_excel("=[N1@area]", geom))           # (a field not there)


if __name__ == "__main__":
    unittest.main()
