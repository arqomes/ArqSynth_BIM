"""0.477 — A table exported as JSON for other programs (KazaFix Cost): its format and version, its columns' keys,
headings and units, the rows by key with numbers as numbers (a text with a decimal comma read as one), the totals of
the summed columns; a total's line left out."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arqbim.model import schedules  # noqa: E402


class Json(unittest.TestCase):
    def test_json(self):
        header = ["Nome", "Comprimento", "Área", "Volume", "Quantidade", "Área bruta"]
        keys = ["name", "length", "area", "volume", "count", "formula:0"]
        table = [["Parede 1", 5.0, "14,00", 2.8, 1, 14.0], ["Parede 2", 3.0, 8.4, 1.68, 1, "8,40"], [],
                 ["Total: 2"]]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "paredes.json")
            schedules.write_table(path, header, table, title="Paredes", columns=keys, project="Moradia")
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        self.assertEqual((data["formato"], data["versao"], data["titulo"], data["projeto"]),
                         ("arqsynth-tabela", 1, "Paredes", "Moradia"))
        self.assertEqual([(c["chave"], c["nome"], c["unidade"]) for c in data["colunas"]],
                         [("name", "Nome", ""), ("length", "Comprimento", "m"), ("area", "Área", "m2"),
                          ("volume", "Volume", "m3"), ("count", "Quantidade", "un"), ("formula:0", "Área bruta", "")])
        self.assertEqual(len(data["linhas"]), 2)
        self.assertEqual(data["linhas"][0]["area"], 14.0)                   # ("14,00": a number)
        self.assertEqual(data["linhas"][1]["formula:0"], 8.4)
        self.assertEqual(data["totais"]["length"], 8.0)
        self.assertAlmostEqual(data["totais"]["area"], 22.4)
        self.assertEqual(data["totais"]["count"], 2)
        self.assertNotIn("name", data["totais"])
        self.assertIn(".json", schedules.TABLE_FORMATS)


if __name__ == "__main__":
    unittest.main()
