"""0.475 — The programme's manager: lines per storey with their use and the area wanted, a JSON list as an AI writes
it, how each line stands against the rooms placed (green / orange), and the conflicting zones by type of building (a
bathroom opening straight into the kitchen)."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model import program_rules as pr  # noqa: E402
from arqbim.model import room_program as rp  # noqa: E402
from arqbim.model.document import Document  # noqa: E402

STOREYS = [("G0", "Piso 0", 0.0), ("G1", "Piso 1", 3.0), ("GM1", "Cave", -3.0)]


class Json(unittest.TestCase):
    """A programme in JSON: by storeys or a flat list, keys in Portuguese or English, the uses and storeys found."""

    def test_storeys_and_uses(self):
        text = """{"tipo": "Habitação", "pisos": [
            {"nome": "Piso 0", "ambientes": [{"nome": "Sala", "uso": "estar", "area": 25},
                                             {"nome": "Casa de banho", "area": "4,5"},
                                             {"nome": "Quarto", "uso": "Quarto", "área": 12, "quantidade": 2}]},
            {"nome": "Piso 3", "ambientes": [{"nome": "Terraço", "uso": "exterior"}]}]}"""
        building, needs = rp.parse_json(text, STOREYS)
        self.assertEqual(building, "habitacao")
        self.assertEqual([(n.name, n.use, n.area, n.count, n.storey) for n in needs],
                         [("Sala", "estar", 25.0, 1, "G0"), ("Casa de banho", "sanitario", 4.5, 1, "G0"),
                          ("Quarto", "quarto", 12.0, 2, "G0"), ("Terraço", "exterior", 0.0, 1, "Piso 3")])
        self.assertTrue(needs[3].external)

    def test_flat_english(self):
        text = """[{"name": "Kitchen", "use": "kitchen", "area": 14, "floor": "1"},
                   {"name": "Vault", "category": "cofre", "level": "Cave"}, "Corredor"]"""
        building, needs = rp.parse_json(text, STOREYS)
        self.assertIsNone(building)
        self.assertEqual([(n.name, n.use, n.storey) for n in needs],
                         [("Kitchen", "cozinha", "G1"), ("Vault", "cofre", "GM1"), ("Corredor", "circulacao", "")])
        self.assertEqual(rp.parse('[{"nome": "Sala"}]')[0].name, "Sala")             # (parse: JSON too)
        with self.assertRaises(ValueError):
            rp.parse_json("isto não é json")

    def test_kept(self):
        needs = [rp.Need("Sala", 25.0, 1, False, "estar", "G0"), rp.Need("Pátio", external=True)]
        text = rp.to_text(needs, "restaurante", [("sanitario", "estar")])
        building, back, rules = rp.program_from_text(text)
        self.assertEqual((building, rules), ("restaurante", [("sanitario", "estar")]))
        self.assertEqual(back, needs)
        old = '[{"n": "Quarto", "a": 12, "q": 2, "e": false}]'                       # (0.357's)
        self.assertEqual([(n.name, n.area, n.count) for n in rp.from_text(old)], [("Quarto", 12.0, 2)])


class States(unittest.TestCase):
    """Green when as many rooms as asked are placed, each as large as wanted; orange when fewer or smaller; a room
    placed from a line counts for it, another by its name on the line's storey."""

    def test_states(self):
        sala = rp.Need("Sala", 25.0, storey="G0")
        quartos = rp.Need("Quarto", 12.0, 2, storey="G0")
        wc = rp.Need("WC")
        cozinha = rp.Need("Cozinha", 10.0, storey="G1")
        spaces = [{"guid": "a", "name": "Sala", "area": 26.0, "storey": "G0"},
                  {"guid": "b", "name": "Quarto 1", "area": 13.0, "storey": "G0"},
                  {"guid": "c", "name": "Quarto", "area": 11.0, "storey": "G0"},
                  {"guid": "d", "name": "Cozinha", "area": 12.0, "storey": "G0"},      # (another storey's)
                  {"guid": "e", "name": "wc", "area": 3.0, "storey": "G1"}]
        links = {"b": quartos.uid}
        found = {s.need.name: s for s in rp.states([sala, quartos, wc, cozinha], spaces, links, STOREYS)}
        self.assertEqual(found["Sala"].status, "ok")
        self.assertEqual((found["Quarto"].status, sorted(found["Quarto"].rooms)), ("short", ["b", "c"]))
        self.assertEqual(found["WC"].status, "ok")                                   # (no area wanted, any storey)
        self.assertEqual(found["Cozinha"].status, "todo")


class Rules(unittest.TestCase):
    """The types of building and their pairs; the uses read from words."""

    def test_rules(self):
        self.assertEqual(pr.type_from_text("Supermercado"), "supermercado")
        self.assertEqual(pr.type_from_text("esquadra de polícia"), "policia")
        self.assertEqual(pr.use_from_text("Casa de banho"), "sanitario")
        self.assertEqual(pr.use_from_text("", "Cozinha"), "cozinha")
        self.assertIn("cofre", pr.uses_for("banco"))
        self.assertNotIn("celas", pr.uses_for("banco"))
        self.assertIsNotNone(pr.conflict_of("habitacao", "cozinha", "sanitario"))      # (every building's, both ways)
        self.assertIsNone(pr.conflict_of("habitacao", "sanitario", "quarto"))
        self.assertIsNotNone(pr.conflict_of("restaurante", "sanitario", "refeicoes"))
        self.assertIsNone(pr.conflict_of("habitacao", "sanitario", "refeicoes"))
        self.assertIsNotNone(pr.conflict_of("banco", "cofre", "atendimento"))
        self.assertIsNotNone(pr.conflict_of("hospital", "sujos", "esterilizacao"))
        self.assertIsNotNone(pr.conflict_of("habitacao", "estar", "quarto", extra=[("quarto", "estar")]))
        for building in pr.BUILDING_TYPES:                                            # (every rule's uses are known)
            for a, b, why in pr.rules(building):
                self.assertIn(pr.EXTRA_USE.get(a, a), pr.USES, (building, a))
                self.assertIn(pr.EXTRA_USE.get(b, b), pr.USES, (building, b))
                self.assertTrue(why)


class Conflicts(unittest.TestCase):
    """A house split by a wall with a door in it: a bathroom placed from the programme on one side, the kitchen on the
    other — a conflict (both rooms), the Verifier's «Zonas conflitantes» warning on each; the door taken away: none."""

    def test_door_between(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        for a, b in (((0.0, 0.0), (10.0, 0.0)), ((10.0, 0.0), (10.0, 6.0)), ((10.0, 6.0), (0.0, 6.0)),
                     ((0.0, 6.0), (0.0, 0.0))):
            bim.add_wall(doc, np.array(a + (0.0,)), np.array(b + (0.0,)), spec)
        middle = bim.add_wall(doc, np.array((4.0, 0.0, 0.0)), np.array((4.0, 6.0, 0.0)), spec)
        frame = bim.wall_frame(doc, middle)
        door = bim.add_opening(doc, middle, catalog.OPENING_BY_KEY["porta_80"], frame, frame.x0 + 3.0, 1)
        wc, kitchen = rp.Need("WC", 4.0, use="sanitario"), rp.Need("Cozinha", 12.0, use="cozinha")
        bim.set_room_program(doc, [wc, kitchen], "habitacao")
        self.assertEqual(doc.ifc.room_program_type(), "habitacao")
        left, _made = bim.room_from_program(doc, (2.0, 3.0), wc)
        right, _made = bim.room_from_program(doc, (7.0, 3.0), kitchen)
        self.assertEqual(doc.ifc.room_program_links(), {left: wc.uid, right: kitchen.uid})
        found = pr.conflicts(doc)
        self.assertEqual(len(found), 1)
        self.assertEqual({found[0][0], found[0][1]}, {left, right})
        self.assertEqual(found[0][2], door)
        states = {s.need.name: s.status for s in rp.states(doc.ifc.room_program(), doc.ifc.spaces(),
                                                            doc.ifc.room_program_links(), doc.storeys())}
        self.assertEqual(states, {"WC": "ok", "Cozinha": "ok"})
        from arqbim.verify import check
        result = check.check(doc, settings={"country": "PT", "building_use": "habitacao", "on": True,
                                            "model_warnings": True})
        warned = {f.subject.id for f in result.failures if f.rule.id == "MOD-zonas-conflitantes"}
        self.assertEqual(warned, {left, right})
        bim.delete(doc, [door])                                                      # (the door taken away)
        self.assertEqual(pr.conflicts(doc), [])


if __name__ == "__main__":
    unittest.main()
