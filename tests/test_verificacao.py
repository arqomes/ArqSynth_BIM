"""(0.416+) The Verifier: the reader (rooms' uses, dwellings, types), the rules and the watcher.
    wsl: bash unit_one.sh tests.test_verificacao"""

import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

import ifcopenshell  # noqa: E402

from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import Document  # noqa: E402
from arqbim.verify import dwellings as dw  # noqa: E402
from arqbim.verify import reader, uses  # noqa: E402


def square(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def t2_house(doc):
    """A one-storey house 10 × 8 m: a living room and a kitchen at the front, two bedrooms at the back; a door from
    outside into the living room, doors between the rooms. {name: room GlobalId}, {name: wall GlobalId}."""
    spec = catalog.BY_KEY["parede_alv_20"]
    corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (10.0, 8.0, 0.0), (0.0, 8.0, 0.0))]
    outer = bim.add_wall_loop(doc, corners, spec)
    middle = bim.add_wall(doc, np.array((5.0, 0.0, 0.0)), np.array((5.0, 8.0, 0.0)), spec)
    left = bim.add_wall(doc, np.array((0.0, 4.0, 0.0)), np.array((5.0, 4.0, 0.0)), spec)
    right = bim.add_wall(doc, np.array((5.0, 4.0, 0.0)), np.array((10.0, 4.0, 0.0)), spec)
    door = catalog.OPENING_BY_KEY["porta_90"]
    for wall, s in ((outer[0], 2.0), (middle, 1.5), (left, 2.0), (right, 2.0)):
        bim.add_opening(doc, wall, door, bim.wall_frame(doc, wall), s, -1)
    rooms = {name: bim.add_room(doc, p, name) for name, p in (("Sala", (2.5, 2.0)), ("Cozinha", (7.5, 2.0)),
                                                             ("Quarto 1", (2.5, 6.0)), ("Quarto 2", (7.5, 6.0)))}
    return rooms, {"outer": outer, "middle": middle, "left": left, "right": right}


class Uses(unittest.TestCase):
    def test_by_name(self):
        cases = {"Quarto 2": "quarto", "Suíte": "quarto", "Sala comum": "sala", "Sala de jantar": "refeicoes",
                 "Cozinha": "cozinha", "WC": "instalacao_sanitaria", "I.S. 1": "instalacao_sanitaria",
                 "Casa de banho": "instalacao_sanitaria", "Quarto de banho": "instalacao_sanitaria",
                 "Hall": "vestibulo", "Corredor": "corredor", "Despensa": "arrumos", "Lavandaria": "tratamento_roupa",
                 "Patamar": "comum", "Varanda": "varanda", "Garagem": "garagem", "Escritório": "escritorio",
                 "Sala/Cozinha": "sala_cozinha", "Bedroom": "quarto", "Living room": "sala", "Ambiente 3": None}
        for name, use in cases.items():
            self.assertEqual(uses.from_name(name), use, name)

    def test_by_contents_and_chosen(self):
        self.assertEqual(uses.deduce("Ambiente 4", {"toilet": 1, "basin": 1}), ("instalacao_sanitaria", "contents"))
        self.assertEqual(uses.deduce("Quarto 3", {"shower": 1}), ("instalacao_sanitaria", "contents"))
        self.assertEqual(uses.deduce("Sala", {"sink": 1, "cooker": 1}), ("sala_cozinha", "contents"))
        self.assertEqual(uses.deduce("Ambiente", {"bed": 1}), ("quarto", "contents"))
        self.assertEqual(uses.deduce("Sala", {"sofa": 1}), ("sala", "name"))
        self.assertEqual(uses.deduce("Ambiente", {}, external=True), ("varanda", "none"))
        self.assertEqual(uses.deduce("Quarto", {}, chosen="escritorio"), ("escritorio", "chosen"))
        self.assertEqual(uses.from_label("Instalação sanitária"), "instalacao_sanitaria")
        self.assertEqual(uses.from_label("Bedroom"), "quarto")


class Dwellings(unittest.TestCase):
    def test_flats_on_a_landing(self):
        """Two flats off a common landing: each its own dwelling, its entrance the door from the landing; their type
        by their bedrooms."""
        rooms = [dw.Room("landing", "s0", 0.0, square(4, 0, 6, 6), name="Patamar", use="comum"),
                 dw.Room("a_sala", "s0", 0.0, square(0, 0, 4, 3), use="sala", area=12.0),
                 dw.Room("a_q", "s0", 0.0, square(0, 3, 4, 6), use="quarto", area=12.0),
                 dw.Room("b_sala", "s0", 0.0, square(6, 0, 10, 3), use="sala", area=12.0),
                 dw.Room("b_q1", "s0", 0.0, square(6, 3, 8, 6), use="quarto", area=6.0),
                 dw.Room("b_q2", "s0", 0.0, square(8, 3, 10, 6), use="quarto", area=6.0)]
        doors = [dw.Door("d1", "s0", (4.0, 1.5), (1.0, 0.0), 0.2), dw.Door("d2", "s0", (2.0, 3.0), (0.0, 1.0), 0.2),
                 dw.Door("d3", "s0", (6.0, 1.5), (1.0, 0.0), 0.2), dw.Door("d4", "s0", (7.0, 3.0), (0.0, 1.0), 0.2),
                 dw.Door("d5", "s0", (9.0, 3.0), (0.0, 1.0), 0.2)]
        found, of_room = dw.find(rooms, doors)
        self.assertEqual([(d.name, d.typology, d.entrances) for d in found],
                         [("Fogo A", "T1", ["d1"]), ("Fogo B", "T2", ["d3"])])
        self.assertNotIn("landing", of_room)
        self.assertEqual(of_room["b_q2"], "Fogo B")

    def test_a_house_on_two_storeys_and_names_by_hand(self):
        """No common areas: the storeys of a house, one over the other, are one dwelling — the bedrooms upstairs
        count. A name written in one room is the whole dwelling's («Moradia»)."""
        rooms = [dw.Room("sala", "s0", 0.0, square(0, 0, 6, 5), use="sala", area=30.0),
                 dw.Room("q1", "s1", 3.0, square(0, 0, 3, 5), use="quarto", area=15.0),
                 dw.Room("q2", "s1", 3.0, square(3, 0, 6, 5), use="quarto", area=15.0)]
        doors = [dw.Door("d", "s1", (3.0, 2.5), (1.0, 0.0), 0.2)]
        found, _ = dw.find(rooms, doors)
        self.assertEqual([(d.name, d.typology, len(d.storeys)) for d in found], [("Fogo A", "T2", 2)])
        rooms[1].manual = "Moradia"
        found, of_room = dw.find(rooms, doors)
        self.assertEqual([(d.name, d.typology, d.manual) for d in found], [("Moradia", "T2", True)])
        self.assertEqual(of_room["sala"], "Moradia")

    def test_a_duplex(self):
        """A building with a common stair: the flat's upper floor (no door of its own to a common area) is one dwelling
        with the floor under it; the other flat of the ground floor stays apart; two rooms joined by no door are made
        one dwelling by giving them the same name."""
        rooms = [dw.Room("hall", "s0", 0.0, square(4, 0, 6, 6), use="comum"),
                 dw.Room("a", "s0", 0.0, square(0, 0, 4, 6), use="sala", area=24.0),
                 dw.Room("b", "s0", 0.0, square(6, 0, 10, 6), use="sala", area=24.0),
                 dw.Room("a_up", "s1", 3.0, square(0, 0, 4, 6), use="quarto", area=24.0)]
        doors = [dw.Door("d1", "s0", (4.0, 3.0), (1.0, 0.0), 0.2), dw.Door("d2", "s0", (6.0, 3.0), (1.0, 0.0), 0.2)]
        found, of_room = dw.find(rooms, doors)
        self.assertEqual([(d.name, d.typology) for d in found], [("Fogo A", "T1"), ("Fogo B", "T0")])
        self.assertEqual(of_room["a_up"], of_room["a"])


class Reader(unittest.TestCase):
    def test_a_t2_house(self):
        """A house drawn as an architect does: four rooms named, doors between them and one from outside — one
        dwelling, T2; a room's use chosen by hand counts (an office made a bedroom: T3) and is undone; a toilet put in
        a room named «Ambiente» makes it a bathroom."""
        doc = Document()
        rooms, _walls = t2_house(doc)
        facts = reader.read(doc)
        self.assertEqual([(d.name, d.typology) for d in facts.dwellings], [("Fogo A", "T2")])
        self.assertEqual({facts.rooms[g].use for g in rooms.values()}, {"sala", "cozinha", "quarto"})
        self.assertEqual(facts.why[rooms["Sala"]], "name")
        self.assertEqual(len(facts.dwellings[0].entrances), 1)
        bim.set_room_use(doc, rooms["Cozinha"], "quarto")
        facts = reader.read(doc)
        self.assertEqual((facts.dwellings[0].typology, facts.why[rooms["Cozinha"]]), ("T3", "chosen"))
        doc.undo()
        self.assertEqual(reader.read(doc).dwellings[0].typology, "T2")
        bim.set_room_dwelling(doc, rooms["Quarto 2"], "Fogo 1.º Esq.")
        facts = reader.read(doc)
        self.assertEqual([(d.name, d.typology) for d in facts.dwellings], [("Fogo 1.º Esq.", "T2")])
        doc.undo()
        self.assertEqual([d.name for d in reader.read(doc).dwellings], ["Fogo A"])

    def test_saved_in_the_file_and_not_kept_in_memory(self):
        """Saving writes each room's use (IfcSpace.ObjectType) and the dwelling (an IfcZone, «T2», its four rooms) into
        the file; in memory the model stays as it was; opened again, the zone is taken out (found again)."""
        doc = Document()
        rooms, _walls = t2_house(doc)
        before = len(list(doc.ifc.file))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa_t2.ifc")
            doc.save(path)
            self.assertEqual(len(list(doc.ifc.file)), before)                   # (nothing left in memory)
            self.assertEqual(len(doc.ifc.file.by_type("IfcZone")), 0)
            written = ifcopenshell.open(path)
            zones = written.by_type("IfcZone")
            self.assertEqual([(z.Name, z.LongName) for z in zones], [("Fogo A", "T2")])
            members = {o.GlobalId for rel in zones[0].IsGroupedBy for o in rel.RelatedObjects}
            self.assertEqual(members, set(rooms.values()))
            self.assertEqual(written.by_guid(rooms["Quarto 1"]).ObjectType, "Quarto")
            self.assertEqual(doc.ifc.by_guid(rooms["Quarto 1"]).ObjectType, None)
            again = Document()
            again.open(path)
            self.assertEqual(len(again.ifc.file.by_type("IfcZone")), 0)
            self.assertEqual([(d.name, d.typology) for d in reader.read(again).dwellings], [("Fogo A", "T2")])
            self.assertEqual(again.ifc.validate(), [])


class Formulas(unittest.TestCase):
    def test_sums_and_names(self):
        from arqbim.verify import expr
        self.assertAlmostEqual(expr.evaluate("3,50+0,15"), 3.65)
        self.assertAlmostEqual(expr.evaluate("2x1,20"), 2.4)
        self.assertAlmostEqual(expr.evaluate("2 × (1,5 + 0,5) ÷ 4"), 1.0)
        self.assertAlmostEqual(expr.evaluate("1.2 * area_habitavel", {"area_habitavel": 50}), 60.0)
        self.assertAlmostEqual(expr.evaluate("max(2; 3,5)"), 3.5)
        for bad in ("__import__('os')", "1/0", "2 +", "a + 1"):
            self.assertIsNone(expr.try_evaluate(bad), bad)


CV = {"country": "CV", "building_use": "habitacao", "work": "nova"}


class CheckCV(unittest.TestCase):
    """0.417: the T2 house checked by Cabo Verde's CTE."""

    def failures(self, doc):
        from arqbim.verify import check
        result = check.check(doc, dict(CV), force=True)
        return {f.rule.id: f for f in result.failures}, result

    def test_the_t2_house(self):
        """Its rooms are big enough, its gross area too; its entrance door, a «Porta 90» (0,76 m clear: 0,90 less its
        lining and its leaf), is too narrow for a building's entrance (0,90 m, art. 30.º); the inner doors pass
        (0,70 m). No ceiling or slab over it: its height is not measured (not a failure)."""
        from arqbim.verify import check
        doc = Document()
        t2_house(doc)
        failed, result = self.failures(doc)
        # (0.419: it has no bathroom — CTE art. 43.º n.º 3 — and no storage — art. 45.º, a warning)
        self.assertEqual(sorted(failed), ["CV-CTE-30-1a", "CV-CTE-43-3", "CV-CTE-45-2"])
        self.assertEqual(failed["CV-CTE-45-2"].rule.severity, "warning")
        door = failed["CV-CTE-30-1a"]
        self.assertAlmostEqual(door.value, 0.76)
        self.assertEqual("Porta 1 — Sala: largura útil 0,76 m — CTE, art. 30.º, n.º 1, al. a): mínimo 0,90 m "
                         "(valor a confirmar)", check.message(door))
        heights = [f for f in result.findings if f.rule.measure.startswith("pe_direito")]
        self.assertTrue(heights and all(f.status == "unknown" for f in heights))
        ok = {f.rule.id for f in result.findings if f.status == "ok"}
        self.assertTrue({"CV-CTE-40-AI-sala", "CV-CTE-40-AI-cozinha", "CV-CTE-40-AI-quartos", "CV-CTE-40-10",
                         "CV-CTE-30-1c"} <= ok)
        gross = next(f for f in result.findings if f.rule.id == "CV-CTE-40-10")
        self.assertAlmostEqual(gross.value, 10.2 * 8.2, places=2)       # (to the outer walls' outer faces)

    def test_a_small_living_room_and_a_low_ceiling(self):
        """A wall across the living room leaves it 4,8 × 2,4 = 11,52 m²: under the T2's 14 m² (Anexo I) — said in
        words; a ceiling at 2,50 m over the bedrooms: their height fails (2,70 m, art. 27.º), the corridor-like
        «Hall» made of the rest of the living room passes (2,40 m)."""
        from arqbim.verify import check
        doc = Document()
        rooms, _walls = t2_house(doc)
        spec = catalog.BY_KEY["parede_alv_20"]
        across = bim.add_wall(doc, np.array((0.0, 2.6, 0.0)), np.array((5.0, 2.6, 0.0)), spec)
        bim.add_opening(doc, across, catalog.OPENING_BY_KEY["porta_90"], bim.wall_frame(doc, across), 3.5, -1)
        hall = bim.add_room(doc, (2.5, 3.3), "Hall")
        bim.add_ceiling(doc, [(0.0, 0.0), (10.0, 0.0), (10.0, 8.0), (0.0, 8.0)], height=2.50)
        failed, result = self.failures(doc)
        sala = failed.get("CV-CTE-40-AI-sala")
        self.assertIsNotNone(sala)
        self.assertEqual(sala.subject.id, rooms["Sala"])
        self.assertAlmostEqual(sala.value, 4.8 * 2.4, places=2)
        self.assertIn("Sala (Fogo A): área útil 11,52 m² — CTE, art. 40.º, n.º 3 e Anexo I: mínimo 14,00 m²",
                      check.message(sala))
        low = [f for f in result.failures if f.rule.id == "CV-CTE-27-1-hab"]
        self.assertEqual({f.subject.id for f in low}, {rooms["Sala"], rooms["Cozinha"], rooms["Quarto 1"],
                                                       rooms["Quarto 2"]})
        self.assertAlmostEqual(low[0].value, 2.50, places=2)
        hall_ok = [f for f in result.findings if f.subject.id == hall and f.rule.id == "CV-CTE-27-1-sec"]
        self.assertEqual([f.status for f in hall_ok], ["ok"])


class Shapes(unittest.TestCase):
    def test_widths_circles_squares(self):
        """0.419: a corridor 1,20 × 6 m: its narrowest width 1,20 — a neck of 0,90 in it: 0,90; an L of 1,20 arms:
        1,20; a living room 4 × 3: a circle of 3 m, a square of 3 m."""
        from shapely.geometry import Polygon
        from arqbim.verify import measures as ms
        corridor = Polygon(square(0, 0, 6, 1.2))
        self.assertAlmostEqual(ms.narrowest(corridor), 1.20, places=2)
        neck = corridor.difference(Polygon(square(3, 0.9, 3.2, 1.2)))
        self.assertAlmostEqual(ms.narrowest(neck), 0.90, places=2)
        ell = Polygon([(0, 0), (6, 0), (6, 1.2), (1.2, 1.2), (1.2, 5), (0, 5)])
        self.assertAlmostEqual(ms.narrowest(ell), 1.20, places=2)
        room = Polygon(square(0, 0, 4, 3))
        self.assertAlmostEqual(ms.inscribed_circle(room), 3.0, places=2)
        self.assertAlmostEqual(ms.inscribed_square(room), 3.0, places=2)


class StairsRampsBathrooms(unittest.TestCase):
    def test_a_house_stair_too_narrow(self):
        """0.419: a stair 1,00 m wide in a house (no common areas: the dwelling's own) — under the CTE's 1,10 m (art.
        35.º n.º 3); its riser (2,80 m in 16: 0,175) and tread (0,28) pass; nothing over it: its headroom not
        measured."""
        from arqbim.verify import check
        doc = Document()
        t2_house(doc)
        stair = bim.add_stair(doc, np.array((6.0, 5.0, 0.0)), np.array((1.0, 0.0, 0.0)), catalog.BY_KEY["laje_15"],
                              rise=2.80, width=1.0, going=0.28)
        result = check.check(doc, dict(CV), force=True)
        mine = {f.rule.id: f for f in result.findings if f.subject.id == stair}
        self.assertEqual(mine["CV-CTE-35-3"].status, "fail")
        self.assertAlmostEqual(mine["CV-CTE-35-3"].value, 1.0)
        self.assertEqual((mine["CV-CTE-35-6-espelho"].status, mine["CV-CTE-35-6-cobertor"].status), ("ok", "ok"))
        self.assertAlmostEqual(mine["CV-CTE-35-6-espelho"].value, 0.175)
        self.assertEqual(mine["CV-CTE-35-11"].status, "unknown")
        self.assertNotIn("CV-CTE-35-2", mine)                            # (not a common stair)

    def test_a_steep_ramp_in_a_common_hall(self):
        """A ramp of 0,40 m in 4 m (10 %) in a building's common hall: over the CTE's 6 % (art. 36.º n.º 1)."""
        from arqbim.verify import check
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (8.0, 0.0, 0.0), (8.0, 4.0, 0.0),
                                                     (0.0, 4.0, 0.0))], spec)
        bim.add_room(doc, (4.0, 2.0), "Átrio comum")
        ramp = bim.add_ramp(doc, np.array((1.0, 2.0, 0.0)), np.array((5.0, 2.0, 0.0)), catalog.BY_KEY["laje_15"],
                            1.20, 0.40)
        result = check.check(doc, dict(CV), force=True)
        mine = {f.rule.id: f for f in result.findings if f.subject.id == ramp}
        self.assertEqual(mine["CV-CTE-36-1"].status, "fail")
        self.assertAlmostEqual(mine["CV-CTE-36-1"].value, 10.0, places=3)
        self.assertEqual((mine["CV-CTE-36-2"].status, mine["CV-CTE-36-3"].status), ("ok", "ok"))
        self.assertIn("inclinação 10,00 %", check.message(mine["CV-CTE-36-1"]))

    def test_a_complete_bathroom(self):
        """A studio: a living room and, through a door, a room «Ambiente» 1,8 × 3,8 m with a toilet, a basin and a
        shower — a bathroom by what is in it, complete, 6,84 m² (≥ 3,00: CTE art. 43.º n.º 3 passes)."""
        from arqbim.verify import check
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        outer = bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (6.0, 4.0, 0.0),
                                                             (0.0, 4.0, 0.0))], spec)
        inner = bim.add_wall(doc, np.array((4.0, 0.0, 0.0)), np.array((4.0, 4.0, 0.0)), spec)
        door = catalog.OPENING_BY_KEY["porta_90"]
        bim.add_opening(doc, outer[0], door, bim.wall_frame(doc, outer[0]), 1.5, -1)
        bim.add_opening(doc, inner, door, bim.wall_frame(doc, inner), 1.5, -1)
        bim.add_room(doc, (2.0, 2.0), "Sala")
        bath = bim.add_room(doc, (5.0, 2.0), "Ambiente")
        for kind, at in (("wc", (4.6, 3.9)), ("basin", (5.4, 3.9)), ("shower", (5.0, 1.0))):
            bim.add_fixture(doc, np.array(at + (0.0,)), kind, angle=180.0)
        result = check.check(doc, dict(CV), force=True)
        from arqbim.verify import reader
        facts = reader.read(doc)
        self.assertEqual(facts.rooms[bath].use, "instalacao_sanitaria")
        complete = next(f for f in result.findings if f.rule.id == "CV-CTE-43-3")
        self.assertEqual(complete.status, "ok", (complete.value, facts.contents[bath], facts.rooms[bath].area,
                                                 [(o.ifc_class, np.round(o.mesh.bounds(), 2).tolist())
                                                  for o in doc.objects.values()
                                                  if o.is_bim and o.ifc_class == "IfcSanitaryTerminal"]))


class Exceptions(unittest.TestCase):
    def test_an_exception_is_not_counted(self):
        """0.418: the entrance door's failure accepted (the reason kept in the project's settings): no longer a
        failure, still found (marked excepted); taken away: it fails again."""
        from arqbim.verify import check, project
        doc = Document()
        t2_house(doc)
        settings = dict(CV)
        result = check.check(doc, settings, force=True)
        door = next(f for f in result.failures if f.rule.id == "CV-CTE-30-1a")
        settings["exceptions"] = {door.key: {"why": "Porta existente, edifício classificado"}}
        bim.set_verify_settings(doc, settings)
        stored = project.settings(doc)
        self.assertEqual(stored["exceptions"][door.key]["why"], "Porta existente, edifício classificado")
        result = check.check(doc, stored, force=True)
        self.assertNotIn(door.key, {f.key for f in result.failures})
        self.assertEqual(result.counts()["excepted"], 1)
        doc.undo()
        self.assertIn(door.key, {f.key for f in check.check(doc, dict(CV), force=True).failures})


if __name__ == "__main__":
    unittest.main()
