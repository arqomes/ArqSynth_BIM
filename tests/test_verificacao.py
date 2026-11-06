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
    # (0.420) daylight: in each room a French door and a window (2,63 m² of glass ≥ 18,24 / 8: CTE art. 76.º)
    french, window = catalog.OPENING_BY_KEY["porta_sacada_140"], catalog.OPENING_BY_KEY["janela_120"]
    for wall, s, spec in ((outer[0], 0.4, window), (outer[0], 3.3, french), (outer[0], 5.5, window),
                          (outer[0], 7.5, french), (outer[2], 5.5, window), (outer[2], 7.1, french),
                          (outer[2], 0.5, window), (outer[2], 2.2, french)):
        bim.add_opening(doc, wall, spec, bim.wall_frame(doc, wall), s, -1)
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
        self.assertEqual(len(facts.dwellings[0].entrances), 5)          # (the front door and four French doors)
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


class Daylight(unittest.TestCase):
    """0.420: CTE arts. 76.º and 77.º."""

    def box(self, doc, w, d):
        spec = catalog.BY_KEY["parede_alv_20"]
        return bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (w, 0.0, 0.0), (w, d, 0.0),
                                                             (0.0, d, 0.0))], spec)

    def findings(self, doc, room):
        from arqbim.verify import check
        result = check.check(doc, dict(CV), force=True)
        return {f.rule.id: f for f in result.findings if f.subject.id == room}, result

    def test_no_window_a_small_one_and_a_deep_room(self):
        """A bedroom 4 × 10 m with no window: no opening to the outside (art. 76.º n.º 1); a window of 120 × 120 on its
        short side (0,78 m² of glass): less than an eighth of the 4,6 m deep strip it lights (6 m from it: 3,8 × 5,9 =
        22,4 m² → 2,80 m²), and the far end, more than 6 m away, unlit (a warning)."""
        doc = Document()
        outer = self.box(doc, 4.0, 10.0)
        room = bim.add_room(doc, (2.0, 5.0), "Quarto")
        mine, _r = self.findings(doc, room)
        self.assertEqual(mine["CV-CTE-76-1-vao"].status, "fail")
        bim.add_opening(doc, outer[0], catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, outer[0]), 1.4, -1)
        mine, _r = self.findings(doc, room)
        self.assertEqual(mine["CV-CTE-76-1-vao"].status, "ok")
        light = mine["CV-CTE-76-1-area"]
        self.assertEqual(light.status, "fail")
        self.assertAlmostEqual(light.value, 0.784, places=2)
        self.assertGreater(light.limit, 2.5)
        self.assertEqual(mine["CV-CTE-76-2"].status, "fail")
        self.assertEqual(mine["CV-CTE-76-2"].rule.severity, "warning")

    def test_a_wall_in_front_of_a_window(self):
        """A living room 5 × 4 with a French door to the outside and, 2,5 m in front of it, a wall 6 m high: closer
        than half its height (3 m) — art. 77.º fails; the wall moved to 4 m: it passes; nothing in front: passes."""
        from arqbim.verify import check
        doc = Document()
        outer = self.box(doc, 5.0, 4.0)
        bim.add_opening(doc, outer[0], catalog.OPENING_BY_KEY["porta_sacada_140"], bim.wall_frame(doc, outer[0]),
                        1.8, -1)
        bim.add_room(doc, (2.5, 2.0), "Sala")
        result = check.check(doc, dict(CV), force=True)
        front = [f for f in result.findings if f.rule.id == "CV-CTE-77-1"]
        self.assertEqual([(f.status, f.value) for f in front], [("ok", None)])
        spec = catalog.BY_KEY["parede_alv_20"]
        wall = bim.add_wall(doc, np.array((-3.0, -2.6, 0.0)), np.array((8.0, -2.6, 0.0)), spec, height=6.0)
        result = check.check(doc, dict(CV), force=True)
        front = next(f for f in result.findings if f.rule.id == "CV-CTE-77-1")
        self.assertEqual(front.status, "fail")
        self.assertAlmostEqual(front.value, 2.5 - 0.15 + 0.05, places=1)   # (from the wall's face, roughly)
        self.assertAlmostEqual(front.limit, 3.0)
        bim.delete(doc, [wall])
        bim.add_wall(doc, np.array((-3.0, -4.2, 0.0)), np.array((8.0, -4.2, 0.0)), spec, height=6.0)
        result = check.check(doc, dict(CV), force=True)
        self.assertEqual(next(f for f in result.findings if f.rule.id == "CV-CTE-77-1").status, "ok")


PT = {"country": "PT", "building_use": "habitacao", "work": "nova"}


class Portugal(unittest.TestCase):
    """0.421: the RGEU and the DL 163/2006."""

    def test_the_t2_house_in_portugal(self):
        """The same T2 house checked in Portugal: its «Porta 90» doors (0,76 m clear) under the DL 163/2006's 0,77 m
        (NTA 4.9.1) — the entrance and the three inner ones; no bathroom: the RGEU's 3,5 m² (art. 68.º) and the NTA's
        bathroom with basin, toilet, bidet and bath (3.3.4); its rooms, gross area (83,64 ≥ 72), openings (1/10, in the
        rough) and cross ventilation (windows on the two long façades) pass."""
        from arqbim.verify import check
        doc = Document()
        t2_house(doc)
        result = check.check(doc, dict(PT), force=True)
        failed = {}
        for f in result.failures:
            failed.setdefault(f.rule.id, []).append(f)
        self.assertEqual(sorted(failed), ["PT-DL163-3.3.4", "PT-DL163-4.9.1-compartimentos",
                                          "PT-DL163-4.9.1-entrada", "PT-RGEU-68"])
        self.assertEqual(len(failed["PT-DL163-4.9.1-compartimentos"]), 3)
        self.assertEqual({p.id for p, own in result.packs if own}, {"PT-RGEU", "PT-DL163", "PLANO", "MODELO"})   # (0.423)
        self.assertEqual({p.id for p, own in result.packs if not own}, {"BOAS-PRATICAS"})      # (0.422)
        passed = {f.rule.id for f in result.findings if f.status == "ok"}
        self.assertTrue({"PT-RGEU-66-sala", "PT-RGEU-66-quartos", "PT-RGEU-67", "PT-RGEU-71-area", "PT-RGEU-72",
                         "PT-RGEU-69-sala", "PT-RGEU-66-suplemento"} <= passed)
        door = failed["PT-DL163-4.9.1-entrada"][0]
        self.assertIn("largura útil 0,76 m — DL 163/2006, NTA 4.9.1 (e 3.3.8): mínimo 0,77 m", check.message(door))

    def test_cape_verde_takes_portugal_only_where_its_code_is_silent(self):
        """Cabo Verde's CTE (art. 4.º): the Portuguese laws come as supplementary, and only their rules on topics the
        CTE does not cover are checked — none of the house's (a ramp inside a dwelling would be one)."""
        from arqbim.verify import check, project
        doc = Document()
        t2_house(doc)
        result = check.check(doc, dict(CV), force=True)
        self.assertEqual([(p.id, own) for p, own in result.packs],
                         [("CV-CTE", True), ("PT-RGEU", False), ("PT-DL163", False), ("BOAS-PRATICAS", False),
                          ("PLANO", True), ("MODELO", True)])
        self.assertEqual({f.rule.pack for f in result.findings} - {"BOAS-PRATICAS", "MODELO"}, {"CV-CTE"})
        supplementary = {r.id for r in project.active_rules(dict(CV)) if r.pack.startswith("PT-")}
        self.assertEqual(supplementary, {"PT-DL163-3.3.6"})
        practice = {r.id for r in project.active_rules(dict(CV)) if r.pack == "BOAS-PRATICAS"}
        self.assertNotIn("BP-pavimento-humido", practice)              # (CTE art. 98.º says it)
        self.assertIn("BP-gesso-humido", practice)

    def test_a_ramp_by_the_interpolated_rule(self):
        """A ramp of 0,50 m in 7 m (7,1 %): the NTA allows 7 % for 0,50 m (between 8 % at 0,40 and 6 % at 0,60) —
        fails by a little; in 8,5 m (5,9 %) it passes."""
        from arqbim.verify import check
        doc = Document()
        ramp = bim.add_ramp(doc, np.array((0.0, 0.0, 0.0)), np.array((7.0, 0.0, 0.0)), catalog.BY_KEY["laje_15"],
                            1.20, 0.50)
        result = check.check(doc, dict(PT), force=True)
        slope = next(f for f in result.findings if f.rule.id == "PT-DL163-2.5.1" and f.subject.id == ramp)
        self.assertEqual(slope.status, "fail")
        self.assertAlmostEqual(slope.limit, 7.0, places=3)
        self.assertAlmostEqual(slope.value, 50 / 7.0, places=3)


class Materials(unittest.TestCase):
    """0.422: materials and good practice."""

    def test_families(self):
        from arqbim.verify import materials as mat
        self.assertTrue({"gesso_cartonado", "hidrofugo"} <= mat.families("Placa de gesso cartonado hidrófugo H1"))
        self.assertEqual(mat.families("Placa de gesso") & {"hidrofugo"}, set())
        self.assertIn("poliestireno", mat.families("XPS 40 mm"))
        self.assertIn("membrana", mat.families("Membrana betuminosa"))
        self.assertTrue(mat.galvanic({"aluminio"}, {"cobre"}))
        self.assertTrue(mat.eps_bitumen({"betume", "membrana"}, {"poliestireno", "isolante"}))
        self.assertTrue(mat.cement_on_lime(mat.families("Reboco de cimento"), mat.families("Alvenaria de pedra")))
        self.assertFalse(mat.cement_on_lime(mat.families("Reboco"), mat.families("Bloco cerâmico")))

    def test_drywall_bathroom_and_a_ground_slab(self):
        """A bathroom of drywall (plain gypsum board, «Placa de gesso»): a good-practice warning in Portugal (no law
        there says it); a concrete slab on the ground with no membrane: Cabo Verde's CTE art. 99.º (a warning) — and in
        Portugal the good practice's own."""
        from arqbim.verify import check
        doc = Document()
        dry = catalog.BY_KEY["parede_dry_10"]
        bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (2.5, 0.0, 0.0), (2.5, 2.0, 0.0),
                                                     (0.0, 2.0, 0.0))], dry)
        wc = bim.add_room(doc, (1.25, 1.0), "WC")
        slab = bim.add_slab(doc, np.array((0.0, 0.0, 0.0)), 2.5, 2.0, catalog.BY_KEY["laje_15"])
        result = check.check(doc, dict(PT), force=True)
        gypsum = next(f for f in result.findings if f.rule.id == "BP-gesso-humido" and f.subject.id == wc)
        self.assertEqual((gypsum.status, gypsum.value), ("fail", 4.0))
        self.assertEqual(gypsum.rule.severity, "warning")
        ground = next(f for f in result.findings if f.subject.id == slab and f.rule.id == "BP-pavimento-solo")
        self.assertEqual(ground.status, "fail")
        result = check.check(doc, dict(CV), force=True)
        ids = {f.rule.id for f in result.findings if f.subject.id == slab}
        self.assertIn("CV-CTE-99-1a", ids)
        self.assertNotIn("BP-pavimento-solo", ids)                     # (the CTE says it: the law's, not good practice)


class TownPlanning(unittest.TestCase):
    """0.423: the lot (the IfcSite's footprint) and the town plan's values for the project."""

    def test_the_lot_in_the_ifc(self):
        """Drawn counter-clockwise or not, kept counter-clockwise; its front chosen; saved as the IfcSite's FootPrint
        (a closed polyline) and read again; undone step by step."""
        doc = Document()
        bim.set_lot(doc, list(reversed(square(-5.0, -6.0, 15.0, 20.0))))
        lot = doc.ifc.lot()
        self.assertAlmostEqual(lot["area"], 520.0)
        self.assertEqual((len(lot["outline"]), lot["fronts"], lot["chosen"]), (4, [], False))
        self.assertGreater(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(lot["outline"],
                                                                         lot["outline"][1:] + lot["outline"][:1])), 0)
        bim.set_lot_fronts(doc, [1])
        self.assertEqual(doc.ifc.lot()["fronts"], [1])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "lote.ifc")
            doc.save(path)
            site = ifcopenshell.open(path).by_type("IfcSite")[0]
            reps = [r for r in site.Representation.Representations if r.RepresentationIdentifier == "FootPrint"]
            self.assertEqual((len(reps), reps[0].RepresentationType, reps[0].Items[0].is_a()),
                             (1, "Curve2D", "IfcPolyline"))
            again = Document()
            again.open(path)
            self.assertAlmostEqual(again.ifc.lot()["area"], 520.0)
            self.assertEqual(again.ifc.lot()["fronts"], [1])
            self.assertEqual(again.ifc.validate(), [])
        doc.undo()
        self.assertEqual(doc.ifc.lot()["fronts"], [])
        doc.undo()
        self.assertIsNone(doc.ifc.lot())

    def test_sides_front_back(self):
        from arqbim.core import lot as core_lot
        outline = square(0.0, 0.0, 20.0, 30.0)
        self.assertEqual(core_lot.auto_fronts(outline, (10.0, 0.5)), [0])
        self.assertEqual(core_lot.roles(outline, [0]), {0: "frente", 1: "lateral", 2: "posterior", 3: "lateral"})
        self.assertEqual(core_lot.auto_fronts(outline), [1])                    # (no entrance: the longest side)

    def test_indices_setbacks_and_the_plan(self):
        """The T2 house (10 × 8 m, walls 20 cm) on a lot of 20 × 30 m: its footprint 10,2 × 8,2 m (the walls' outer
        faces: 83,64 m²), one storey above the ground; the front (the side nearest the entrance, in the wall at y = 0)
        4,9 m away, the sides 4,9 m, the back 16,9 m. The plan asks IOS ≤ 0,10 and 5 m to the front: both fail;
        moved back the lot passes the front; a lot that leaves the house half out: «outside the lot»."""
        from arqbim.verify import check, measures as ms, urban
        doc = Document()
        t2_house(doc)
        bim.set_lot(doc, square(-5.0, -5.0, 15.0, 25.0))
        settings = dict(CV, pdm={"name": "PDM da Praia", "ios_max": 0.10, "frontal_min": 5.0, "pisos_max": 2})
        result = check.check(doc, settings, force=True)
        ctx = ms.Context(doc, reader.read(doc), settings)
        values = urban.summary(ctx)
        self.assertAlmostEqual(values["area_lote"], 600.0)
        self.assertAlmostEqual(values["area_implantacao"], 83.64, places=1)
        self.assertAlmostEqual(values["indice_ocupacao"], 83.64 / 600.0, places=3)
        self.assertEqual(values["pisos_acima_solo"], 1.0)
        self.assertAlmostEqual(values["afastamento_frontal"], 4.9, places=2)
        self.assertAlmostEqual(values["afastamento_lateral"], 4.9, places=2)
        self.assertAlmostEqual(values["afastamento_posterior"], 16.9, places=2)
        self.assertEqual(values["fora_do_lote"], 0.0)
        self.assertGreater(values["cercea"], 2.5)
        by_rule = {f.rule.id: f for f in result.findings if f.subject.kind == "lot"}
        self.assertEqual(by_rule["PLANO-ios_max"].status, "fail")
        self.assertEqual(by_rule["PLANO-frontal_min"].status, "fail")
        self.assertEqual(by_rule["PLANO-pisos_max"].status, "ok")
        self.assertEqual(by_rule["PLANO-dentro"].status, "ok")
        self.assertIn("Lote: afastamento à frente do lote 4,90 m — PDM da Praia, parâmetro do plano: mínimo 5,00 m",
                      check.message(by_rule["PLANO-frontal_min"]))
        bim.set_lot(doc, square(-5.0, -5.5, 15.0, 25.0))
        result = check.check(doc, settings, force=True)
        self.assertEqual(next(f for f in result.findings if f.rule.id == "PLANO-frontal_min").status, "ok")
        bim.set_lot(doc, square(5.0, -5.0, 25.0, 25.0))
        result = check.check(doc, settings, force=True)
        inside = next(f for f in result.findings if f.rule.id == "PLANO-dentro")
        self.assertEqual(inside.status, "fail")
        self.assertAlmostEqual(inside.value, 5.1 * 8.2, places=0)

    def test_no_lot_but_a_plan(self):
        """The plan's values written and no lot drawn: its indices «not measured» (the panel says to draw it)."""
        from arqbim.verify import check
        doc = Document()
        t2_house(doc)
        result = check.check(doc, dict(CV, pdm={"ios_max": 0.5}), force=True)
        ios = next(f for f in result.findings if f.rule.id == "PLANO-ios_max")
        self.assertEqual(ios.status, "unknown")
        self.assertFalse(any(f.rule.id == "PLANO-dentro" for f in result.findings))


class FacadesAndSetbacks(unittest.TestCase):
    """0.424: the law's façade heights and setbacks — CTE arts. 21.º–24.º, RGEU arts. 59.º, 60.º, 62.º."""

    def test_windows_near_the_next_lot(self):
        """The T2 house's bedrooms look out to the back: with the lot's back side 3 m from that façade, their windows
        fail the CTE's art. 22.º n.º 2 (5 m at least, the façade being under 10 m high); at 5,2 m they pass; the front
        windows look at the street (art. 22.º n.º 1's, not measured: nothing drawn across it)."""
        from arqbim.verify import check
        doc = Document()
        rooms, walls = t2_house(doc)
        bim.set_lot(doc, square(-5.0, -5.0, 15.0, 11.1))
        result = check.check(doc, dict(CV), force=True)
        near = [f for f in result.findings if f.rule.id == "CV-CTE-22-2"]
        failed = [f for f in near if f.status == "fail"]
        self.assertEqual(len(failed), 4)                                # (two windows in each bedroom, at the back)
        self.assertAlmostEqual(failed[0].value, 3.0, places=2)
        self.assertAlmostEqual(failed[0].limit, 5.0, places=3)
        self.assertTrue(all(f.status == "ok" for f in near if f not in failed))
        bim.set_lot(doc, square(-5.0, -5.0, 15.0, 13.3))
        result = check.check(doc, dict(CV), force=True)
        self.assertFalse([f for f in result.failures if f.rule.id == "CV-CTE-22-2"])

    def test_a_tall_block_behind(self):
        """A block 9 m high, 10 × 4 m, 3,8 m behind the house: its façade facing the house is higher than the distance
        between them (CTE art. 21.º n.º 1: H ≤ L) — it fails; the house's own back façade (2,7 m high, lower than
        3,8 m) passes. In Portugal the RGEU's art. 59.º says the same, and art. 60.º asks the bedrooms' windows for
        10 m to the façade in front."""
        from arqbim.verify import check
        doc = Document()
        _rooms, walls = t2_house(doc)
        spec = catalog.BY_KEY["parede_alv_20"]
        block = bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 12.0, 0.0), (10.0, 12.0, 0.0),
                                                              (10.0, 16.0, 0.0), (0.0, 16.0, 0.0))], spec, height=9.0)
        result = check.check(doc, dict(CV), force=True)
        by_wall = {f.subject.id: f for f in result.findings if f.rule.id == "CV-CTE-21-1"}
        tall = by_wall[block[0]]
        self.assertEqual(tall.status, "fail")
        self.assertAlmostEqual(tall.value, 3.8, places=2)
        self.assertAlmostEqual(tall.limit, 9.0, places=2)
        back = by_wall[walls["outer"][2]]
        self.assertEqual(back.status, "ok")
        self.assertAlmostEqual(back.value, 3.8, places=2)
        result = check.check(doc, dict(PT), force=True)
        ids = {f.rule.id for f in result.failures}
        self.assertIn("PT-RGEU-59", ids)
        windows = [f for f in result.failures if f.rule.id == "PT-RGEU-60"]
        self.assertEqual(len(windows), 4)

    def test_a_courtyard_and_a_balcony_over_the_street(self):
        """A courtyard of 3 × 3 m (the use «Pátio» from its name) in walls 6 m high: the CTE asks for a circle of
        max(4; 6/2) = 4 m — it fails; a slab on the upper floor jutting 1 m past the lot's front, its underside 2,7 m
        above the ground: art. 24.º n.º 2 (3 m) fails."""
        from arqbim.verify import check, uses as uses_mod
        self.assertEqual(uses_mod.from_name("Pátio"), "patio")
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        bim.add_wall_loop(doc, [np.array(p) for p in ((0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (3.0, 3.0, 0.0),
                                                      (0.0, 3.0, 0.0))], spec, height=6.0)
        patio = bim.add_room(doc, (1.5, 1.5), "Pátio")
        result = check.check(doc, dict(CV), force=True)
        found = next(f for f in result.findings if f.rule.id == "CV-CTE-23-1a" and f.subject.id == patio)
        self.assertEqual(found.status, "fail")
        self.assertAlmostEqual(found.limit, 4.0, places=3)
        doc = Document()
        t2_house(doc)
        bim.set_lot(doc, square(-5.0, -0.5, 15.0, 25.0))           # (the front 0,6 m before the house's front face)
        upper = bim.add_storey(doc, "Piso 1", 2.7)
        slab = bim.add_slab(doc, np.array((1.0, -1.5, 2.7)), 3.0, 1.5, catalog.BY_KEY["laje_12"], storey=upper)
        result = check.check(doc, dict(CV), force=True)
        over = next((f for f in result.findings if f.rule.id == "CV-CTE-24-2" and f.subject.id == slab), None)
        self.assertIsNotNone(over)
        self.assertEqual(over.status, "fail")
        self.assertLess(over.value, 3.0)


class Sheet(unittest.TestCase):
    def test_the_verification_sheet(self):
        """0.425: the T2 house with its entrance door accepted as an exception — the sheet's data: the CTE, the table
        of areas (Fogo A, T2, its four rooms, 72,96 m² useful), every rule by article, the exception with its reason;
        as an HTML page and an Excel workbook of four sheets."""
        from arqbim.verify import check, sheet
        doc = Document()
        t2_house(doc)
        settings = dict(CV)
        door = next(f for f in check.check(doc, settings, force=True).failures if f.rule.id == "CV-CTE-30-1a")
        settings["exceptions"] = {door.key: {"why": "Porta existente a manter", "when": "2026-11-06"}}
        d = sheet.sheet(doc, settings, check.check(doc, settings, force=True))
        self.assertEqual(d["laws"][0][0], "CTE")
        self.assertFalse({"RGEU", "DL 163/2006"} & {law[0] for law in d["laws"]})    # (supplementary, not used here)
        self.assertEqual([(w["name"], w["typology"], len(w["rooms"]), w["useful"]) for w in d["dwellings"]],
                         [("Fogo A", "T2", 4, "72,96 m²")])
        self.assertTrue(any(r["article"].startswith("art. 40.º") for r in d["rows"]))
        self.assertEqual([(x["why"], x["state"]) for x in d["exceptions"]], [("Porta existente a manter", "excepted")])
        self.assertGreater(d["unconfirmed"], 0)
        page = sheet.page(d)
        self.assertIn("Fogo A (T2)", page)
        self.assertIn("Porta existente a manter", page)
        with tempfile.TemporaryDirectory() as tmp:
            path = sheet.write_xlsx(os.path.join(tmp, "ficha.xlsx"), d)
            from openpyxl import load_workbook
            book = load_workbook(path)
            self.assertEqual(book.sheetnames, ["Resumo", "Quadro de áreas", "Verificação", "Exceções"])
            marks = {str(row[6].value) for row in book["Verificação"].iter_rows(min_row=2)}
            self.assertTrue({"✗", "✓", "✓*"} <= marks)


class UsersPacks(unittest.TestCase):
    """0.426: the architect's own packs — a change saved as a copy that wins, a rule switched off, another country."""

    def setUp(self):
        from arqbim.verify import rules
        self.tmp = tempfile.mkdtemp()
        self.before = os.environ.get("ARQBIM_RULES_DIR")
        os.environ["ARQBIM_RULES_DIR"] = self.tmp
        rules.packs(again=True)

    def tearDown(self):
        import shutil
        from arqbim.verify import rules
        if self.before is None:
            os.environ.pop("ARQBIM_RULES_DIR", None)
        else:
            os.environ["ARQBIM_RULES_DIR"] = self.before
        rules.packs(again=True)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_a_copy_wins_and_the_original_comes_back(self):
        """The kitchen's least area raised to 20 m² in the architect's copy of the CTE: the T2 house's kitchen
        (18,24 m²) fails, the check made again though the document did not change; the rule switched off: not
        checked; «Repor o original»: 6,5 m² again."""
        import json
        from arqbim.verify import check, rules
        doc = Document()
        t2_house(doc)
        kitchen = lambda: [f for f in check.check(doc, dict(CV)).findings if f.rule.id == "CV-CTE-40-AI-cozinha"]  # noqa: E731
        self.assertEqual([f.status for f in kitchen()], ["ok"])
        pack = rules.find("CV-CTE")
        self.assertFalse(rules.is_users(pack))
        with open(pack.path, encoding="utf-8") as f:
            data = json.load(f)
        rule = next(r for r in data["rules"] if r["id"] == "CV-CTE-40-AI-cozinha")
        rule["min"] = 20
        path = rules.save_users(data)
        self.assertTrue(path.startswith(self.tmp))
        self.assertTrue(rules.is_users(rules.find("CV-CTE")))
        self.assertEqual([(f.status, f.limit) for f in kitchen()], [("fail", 20.0)])
        rule["off"] = True
        rules.save_users(data)
        self.assertEqual(kitchen(), [])
        self.assertTrue(rules.remove_users("CV-CTE"))
        self.assertFalse(rules.is_users(rules.find("CV-CTE")))
        self.assertEqual([(f.status, f.limit) for f in kitchen()], [("ok", 6.5)])

    def test_another_country(self):
        """Angola from Cabo Verde: «AO-CTE» with every value to be confirmed and no supplementary laws; Angola among
        the countries; the T2 house checked by it (and the good practice, as any country)."""
        from arqbim.verify import check, project, rules
        made = rules.new_country("ao", "Angola", "CV")
        self.assertEqual(made, ["AO-CTE"])
        pack = rules.find("AO-CTE")
        self.assertEqual((pack.country, pack.country_name, pack.fallback), ("AO", "Angola", []))
        self.assertFalse(any(r.confirmed for r in pack.rules))
        self.assertTrue(all(r.id.startswith("AO-CTE") for r in pack.rules))
        self.assertEqual(project.country_name("AO"), "Angola")
        doc = Document()
        t2_house(doc)
        result = check.check(doc, {"country": "AO", "building_use": "habitacao", "work": "nova"}, force=True)
        self.assertEqual({p.id for p, own in result.packs}, {"AO-CTE", "BOAS-PRATICAS", "PLANO", "MODELO"})
        self.assertIn("AO-CTE-30-1a", {f.rule.id for f in result.failures})


class ModelWarnings(unittest.TestCase):
    """0.431: the model's own warnings (the pack «Modelo», always on): walls over each other, an element twice in one
    place, a room its walls no longer close — and none in the T2 house as it is (its walls meet at corners and Ts)."""

    def test_the_t2_house_has_none(self):
        from arqbim.verify import check
        doc = Document()
        t2_house(doc)
        result = check.check(doc, dict(CV), force=True)
        self.assertFalse([f for f in result.failures if f.rule.pack == "MODELO"])
        self.assertTrue(any(f.rule.id == "MOD-ambiente-aberto" and f.status == "ok" for f in result.findings))

    def test_walls_twins_and_an_open_room(self):
        from arqbim.verify import check
        doc = Document()
        rooms, walls = t2_house(doc)
        spec = catalog.BY_KEY["parede_alv_20"]
        over = bim.add_wall(doc, np.array((1.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), spec)   # (on the front wall)
        column = bim.add_column(doc, np.array((20.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        twin = bim.add_column(doc, np.array((20.0, 0.0, 0.0)), catalog.BY_KEY["pilar_30"], 2.8)
        result = check.check(doc, dict(CV), force=True)
        failed = {}
        for f in result.failures:
            if f.rule.pack == "MODELO":
                failed.setdefault(f.rule.id, set()).add(f.subject.id)
        self.assertIn(over, failed.get("MOD-paredes-sobrepostas", set()))
        self.assertIn(walls["outer"][0], failed["MOD-paredes-sobrepostas"])
        self.assertEqual(failed.get("MOD-elemento-repetido"), {column, twin})
        self.assertNotIn("MOD-ambiente-aberto", failed)
        self.assertEqual({f.rule.severity for f in result.failures if f.rule.pack == "MODELO"}, {"warning"})
        doc.undo()
        doc.undo()
        doc.undo()
        bim.delete(doc, [walls["middle"]])              # (the middle wall gone: two rooms in one space each side)
        result = check.check(doc, dict(CV), force=True)
        joined = {f.subject.id for f in result.failures if f.rule.id == "MOD-ambientes-juntos"}
        self.assertEqual(joined, set(rooms.values()))
        doc.undo()
        bim.delete(doc, [walls["outer"][0]])            # (the front wall gone: the living room and kitchen open)
        result = check.check(doc, dict(CV), force=True)
        opened = {f.subject.id for f in result.failures if f.rule.id == "MOD-ambiente-aberto"}
        self.assertEqual(opened, {rooms["Sala"], rooms["Cozinha"]})


class Texts(unittest.TestCase):
    def test_the_verifiers_words_never_replace_the_programs(self):
        """0.427: the Verifier's texts (verify/texts.py) are added to the program's — a key already there would
        change a word elsewhere (0.426's «rules.title» renamed the «Regras gráficas» panel)."""
        import re
        from arqbim.verify import texts
        with open(os.path.join(os.path.dirname(__file__), "..", "arqbim", "i18n.py"), encoding="utf-8") as f:
            programs = set(re.findall(r'^\s+"([A-Za-z0-9_.]+)":', f.read(), re.M))
        self.assertEqual(sorted(set(texts.STRINGS) & programs), [])


class Steps(unittest.TestCase):
    def test_the_check_in_steps(self):
        """0.424: the check as a generator — a stop after the reading and after each rule (the watcher goes on between
        the window's events) — gives what check() gives; a document made anew is never given an old one's reading."""
        from arqbim.verify import check
        doc = Document()
        t2_house(doc)
        job = check.steps(doc, dict(CV), force=True)
        stops = 0
        while True:
            try:
                next(job)
                stops += 1
            except StopIteration as done:
                result = done.value
                break
        self.assertGreater(stops, 10)
        again = check.check(doc, dict(CV), force=True)
        self.assertEqual(sorted(f.key for f in result.failures), sorted(f.key for f in again.failures))
        revision = doc.revision
        del doc, job, again
        fresh = Document()
        while fresh.revision < revision:                # (a new document at the old one's revision)
            fresh.revision += 1
        self.assertEqual(reader.read(fresh).rooms, {})
        self.assertEqual(check.check(fresh, dict(CV)).findings, [])


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
