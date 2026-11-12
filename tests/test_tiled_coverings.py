"""0.563 — Gerador de revestimentos, step 2: the Revestimento element in IFC (ifc/tiled_coverings.py)."""

import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["ARQSYNTH_HOME"] = tempfile.mkdtemp(prefix="arqsynth_tiled_")

import ifcopenshell.util.element  # noqa: E402
from shapely.geometry import Polygon  # noqa: E402

from arqbim.core.mesh import TriMesh  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import Document  # noqa: E402

WALL = [(0, 0, 0), (4, 0, 0), (4, 0, 2.7), (0, 0, 2.7)]       # an upright face, facing −y
DOOR = [(1, 0, 0), (1.9, 0, 0), (1.9, 0, 2.1), (1, 0, 2.1)]
FLOOR = [(0, 0, 0), (5, 0, 0), (5, 3.2, 0), (0, 3.2, 0)]


def mesh(doc, g):
    v, f = doc.ifc.triangulate([g])[g]
    return np.asarray(v), np.asarray(f).reshape(-1, 3)


def chain(doc, pts, spec):
    """(0.568) A closed chain of walls through the points, joined at their corners (as drawn one after another)."""
    walls = []
    for k, (a, b) in enumerate(zip(pts, pts[1:] + pts[:1])):
        a3, b3 = np.array((a[0], a[1], 0.0)), np.array((b[0], b[1], 0.0))
        prev = (walls[-1], a3 - np.array((pts[k - 1][0], pts[k - 1][1], 0.0))) if walls else None
        first = (walls[0], np.array((pts[1][0] - pts[0][0], pts[1][1] - pts[0][1], 0.0))) \
            if k == len(pts) - 1 else None
        walls.append(bim.add_wall(doc, a3, b3, spec, prev=prev, first=first))
    return walls


class Element(unittest.TestCase):
    def setUp(self):
        self.doc = Document()

    def test_on_a_wall(self):
        g = bim.add_covering(self.doc, WALL, "azulejo_30x60", holes=[DOOR])
        e = self.doc.ifc.by_guid(g)
        self.assertTrue(e.is_a("IfcCovering"))
        self.assertEqual(ifcopenshell.util.element.get_predefined_type(e), "CLADDING")
        ctype = ifcopenshell.util.element.get_type(e)
        self.assertEqual(ctype.Name, "Azulejo 30 × 60")
        mat = ifcopenshell.util.element.get_material(e, should_skip_usage=True)
        self.assertTrue(mat.is_a("IfcMaterialLayerSet"))
        self.assertEqual(len(mat.MaterialLayers), 2)
        info = self.doc.ifc.element_info(g)["params"] if hasattr(self.doc.ifc, "element_info") else None
        pg = ifcopenshell.util.element.get_psets(e)["ArqSynth_Paginacao"]
        self.assertGreater(pg["Pecas"], 40)
        self.assertEqual(pg["CortesEstreitos"], 0)              # (automatic start: no strip under 5 cm)
        q = ifcopenshell.util.element.get_psets(e)["Qto_CoveringBaseQuantities"]
        self.assertAlmostEqual(q["GrossArea"], 4 * 2.7 - 0.9 * 2.1, places=2)
        self.assertLess(q["NetArea"], q["GrossArea"])
        v, f = mesh(self.doc, g)
        self.assertTrue((v[:, 1] <= 1e-6).all(), "laid out of the wall, on its −y side")
        self.assertAlmostEqual(v[:, 1].min(), -0.014, places=4)  # (5 mm bed + 9 mm tile)
        door_mid = (v[:, 0] > 1.05) & (v[:, 0] < 1.85) & (v[:, 2] > 0.1) & (v[:, 2] < 2.0)
        self.assertFalse(door_mid.any(), "nothing over the door")
        rows = sorted({round(z, 4) for z in v[:, 2]})
        self.assertIn(0.0, rows)                                 # (from the wall's foot)
        info = info

    def test_floor_and_ceiling(self):
        g = bim.add_covering(self.doc, FLOOR, "soalho_carvalho")
        e = self.doc.ifc.by_guid(g)
        self.assertEqual(ifcopenshell.util.element.get_predefined_type(e), "FLOORING")
        v, _f = mesh(self.doc, g)
        self.assertAlmostEqual(v[:, 2].max(), 0.015, places=4)
        ceiling = list(reversed(FLOOR))
        g2 = bim.add_covering(self.doc, [(x, y, 2.6) for x, y, _z in ceiling], "porcelanico_60x60")
        self.assertEqual(ifcopenshell.util.element.get_predefined_type(self.doc.ifc.by_guid(g2)), "CEILING")
        v, _f = mesh(self.doc, g2)
        self.assertLess(v[:, 2].min(), 2.6)

    def test_closed_pieces(self):
        g = bim.add_covering(self.doc, FLOOR, "hexagono_20")
        v, f = mesh(self.doc, g)
        self.assertTrue(TriMesh(v, f).is_closed())

    def test_changes_and_undo(self):
        g = bim.add_covering(self.doc, WALL, "metro_10x20")
        e = self.doc.ifc.by_guid(g)
        n0 = ifcopenshell.util.element.get_psets(e)["ArqSynth_Paginacao"]["Pecas"]
        bim.set_covering(self.doc, g, layout={"pattern": "espinha_reta", "angle": 0.0})
        e = self.doc.ifc.by_guid(g)
        self.assertEqual(ifcopenshell.util.element.get_psets(e)["ArqSynth_Paginacao"]["Aparelho"], "espinha_reta")
        bim.set_covering(self.doc, g, finish="pedra_60x40")
        p = self.doc.ifc.tiled_params(g)
        self.assertEqual(p["material"], "pedra")
        self.assertEqual(p["layout"]["pattern"], "desencontrado")
        self.assertEqual(ifcopenshell.util.element.get_type(self.doc.ifc.by_guid(g)).Name,
                         "Pedra 60 × 40 (desencontrada)")
        self.doc.undo()
        self.doc.undo()
        e = self.doc.ifc.by_guid(g)
        self.assertEqual(ifcopenshell.util.element.get_psets(e)["ArqSynth_Paginacao"]["Pecas"], n0)

    def test_refused(self):
        with self.assertRaises(Exception):
            bim.add_covering(self.doc, WALL, "nada")
        g = bim.add_covering(self.doc, WALL, "azulejo_20x20")
        with self.assertRaises(Exception):
            bim.set_covering(self.doc, g, layout={"w": 0.0})
        with self.assertRaises(Exception):
            bim.set_covering(self.doc, g, material="kryptonite")

    def test_saved_and_read_again(self):
        g = bim.add_covering(self.doc, WALL, "tijolo_flamengo")
        path = os.path.join(tempfile.mkdtemp(), "r.ifc")
        self.doc.ifc.file.write(path)
        import ifcopenshell
        f = ifcopenshell.open(path)
        e = f.by_guid(g)
        self.assertTrue(e.is_a("IfcCovering"))
        self.assertEqual(len(e.Representation.Representations[0].Items), 3)   # (bricks, bed, mortar)


if __name__ == "__main__":
    unittest.main()


class OnTheModel(unittest.TestCase):
    """(0.564) Laid on a clicked face of an element (it follows it), and on drawings chosen."""

    def test_wall_face_follows(self):
        from arqbim.ifc import catalog
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((5.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        v, _f = mesh(doc, wall)
        front = float(v[:, 1].min())
        g = bim.cover_face(doc, wall, (2.5, front, 1.0), (0.0, -1.0, 0.0), "azulejo_20x20")
        self.assertIsNotNone(g)
        e = doc.ifc.by_guid(g)
        self.assertEqual(e.CoversElements[0].RelatingBuildingElement.GlobalId, wall)
        a0 = ifcopenshell.util.element.get_psets(e)["Qto_CoveringBaseQuantities"]["GrossArea"]
        self.assertAlmostEqual(a0, 5.0 * bim.WALL_HEIGHT, delta=0.3)
        frame = bim.wall_frame(doc, wall)                 # (a door put in: the finish cut round it, by itself)
        bim.add_opening(doc, wall, catalog.OPENING_BY_KEY["porta_80"], frame, frame.x0 + 2.0, 1)
        e = doc.ifc.by_guid(g)
        a1 = ifcopenshell.util.element.get_psets(e)["Qto_CoveringBaseQuantities"]["GrossArea"]
        self.assertLess(a1, a0 - 1.0)
        self.assertGreater(a1, a0 - 3.0)
        doc.execute_remove = None
        from arqbim.model.document import IfcCommand
        doc.execute(IfcCommand("x", lambda ifc: ifc.remove([wall])))    # (the wall gone: its finish with it)
        self.assertIsNone(doc.ifc.by_guid(g))

    def test_drawing_chosen(self):
        from arqbim.core.mesh import PolyMesh
        from arqbim.model.document import AddObject, SketchObject
        doc = Document()
        pts = [(0, 0, 0), (3, 0, 0), (3, 2, 0), (0, 2, 0)]
        sk = SketchObject("Polígono", np.eye(4), PolyMesh([np.array(p, float) for p in pts], [[0, 1, 2, 3]]))
        doc.execute(AddObject(sk))
        made = bim.cover_drawings(doc, [sk.id], "porcelanico_60x60")
        self.assertEqual(len(made), 1)
        e = doc.ifc.by_guid(made[0])
        self.assertEqual(ifcopenshell.util.element.get_predefined_type(e), "FLOORING")
        v, _f = mesh(doc, made[0])
        self.assertGreater(v[:, 2].max(), 0.01)


class PieceByPiece(unittest.TestCase):
    """(0.566) Bands, a border, a mix of materials, pieces picked one by one."""

    def test_band_border_mix_picks(self):
        from arqbim.core import tiling as tl
        doc = Document()
        g = bim.add_covering(doc, WALL, "azulejo_20x20")
        bim.set_covering_extras(doc, g, zones=[{"kind": "faixa", "y0": 1.2, "y1": 1.25, "material": "marmore",
                                                "w": 0.25, "h": 0.05},
                                               {"kind": "cercadura", "width": 0.1, "material": "granito",
                                                "w": 0.3, "h": 0.1}])
        result, mats = doc.ifc.tiled_pieces(g)
        self.assertIn("marmore", mats)
        self.assertIn("granito", mats)
        band = [p for p, m in zip(result.pieces, mats) if m == "marmore"]
        ys = [q[1] for p in band for q in p.points]
        self.assertGreaterEqual(min(ys), 1.2 - 1e-6)
        self.assertLessEqual(max(ys), 1.25 + 1e-6)
        e = doc.ifc.by_guid(g)
        self.assertGreaterEqual(len(e.Representation.Representations[0].Items), 4)   # (tile, marble, granite, …)
        bim.set_covering_extras(doc, g, zones=[], mix={"materials": ["azulejo", "tinta_azul"], "seed": 3})
        _r, mats = doc.ifc.tiled_pieces(g)
        self.assertEqual(set(mats), {"azulejo", "tinta_azul"})
        main = next(p for p in _r.pieces if p.whole)
        c = Polygon(main.points).centroid
        bim.set_covering_extras(doc, g, mix={}, picks=[(c.x, c.y, "tinta_vermelha")])
        _r, mats = doc.ifc.tiled_pieces(g)
        self.assertEqual(mats.count("tinta_vermelha"), 1)
        self.assertEqual(mats.count(None), len(mats) - 1)
        with self.assertRaises(Exception):
            bim.set_covering_extras(doc, g, zones=[{"kind": "faixa", "y0": 1.0, "y1": 1.0}])
        doc.undo()
        doc.undo()
        _r, mats = doc.ifc.tiled_pieces(g)
        self.assertIn("marmore", mats)
        self.assertTrue(tl)


class ManyAtOnce(unittest.TestCase):
    """(0.567) By category and by room."""

    def setUp(self):
        from arqbim.ifc import catalog
        self.doc = doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        pts = [(0.0, 0.0), (5.0, 0.0), (5.0, 4.0), (0.0, 4.0)]
        self.walls = chain(doc, pts, spec)
        rooms = bim.identify_rooms(doc) if hasattr(bim, "identify_rooms") else None
        self.rooms = [s["guid"] for s in doc.ifc.spaces()]

    def test_walls_inside_and_outside(self):
        if not self.rooms:
            self.skipTest("no room found")
        inside = bim.cover_category(self.doc, self.walls, "parede", "azulejo_20x20", sides="interior")
        outside = bim.cover_category(self.doc, self.walls, "parede", "pedra_60x40", sides="exterior")
        self.assertEqual(len(inside), 4)
        self.assertEqual(len(outside), 4)
        centre = np.array((2.5, 2.0, 0.0))
        for g, sign in [(g, 1) for g in inside] + [(g, -1) for g in outside]:
            m = self.doc.ifc._placement_si(self.doc.ifc.by_guid(g))
            towards = centre - m[:3, 3]
            towards[2] = 0.0
            self.assertGreater(sign * float(m[:3, 2] @ towards), 0.0)     # (inside: facing the room's middle)

    def test_a_room_at_once(self):
        if not self.rooms:
            self.skipTest("no room found")
        made = bim.cover_room(self.doc, self.rooms[0], floor="porcelanico_60x60", walls="azulejo_30x60",
                              wall_height=2.1, ceiling="porcelanico_60x60")
        kinds = [ifcopenshell.util.element.get_predefined_type(self.doc.ifc.by_guid(g)) for g in made]
        self.assertEqual(kinds.count("FLOORING"), 1)
        self.assertEqual(kinds.count("CEILING"), 1)
        self.assertEqual(kinds.count("CLADDING"), 4)
        for g in made:
            if ifcopenshell.util.element.get_predefined_type(self.doc.ifc.by_guid(g)) == "CLADDING":
                v, _f = mesh(self.doc, g)
                self.assertLessEqual(v[:, 2].max(), 2.1 + 1e-3)
        floor = next(g for g, k in zip(made, kinds) if k == "FLOORING")
        self.assertAlmostEqual(self.doc.ifc.describe(floor)["params"]["gross"], 4.8 * 3.8, delta=0.3)
        skirt = bim.cover_room(self.doc, self.rooms[0], skirting="rodape_madeira")
        self.assertEqual(len(skirt), 4)
        v, _f = mesh(self.doc, skirt[0])
        self.assertLessEqual(v[:, 2].max(), 0.08 + 1e-3)

    def test_rules_applied_twice(self):
        if not self.rooms:
            self.skipTest("no room found")
        from arqbim.model import covering_rules as cr
        room = self.doc.ifc.by_guid(self.rooms[0])
        from arqbim.model.document import IfcCommand
        self.doc.execute(IfcCommand("n", lambda ifc: setattr(ifc.by_guid(self.rooms[0]), "LongName", "WC social")))
        cr.save_rules(self.doc, [{"name": "Sanitárias", "rooms": "wc|banho", "floor": "porcelanico_60x60",
                                  "walls": "azulejo_30x60", "wall_height": 2.1},
                                 {"name": "Quartos", "rooms": "quarto", "floor": "soalho_carvalho"}])
        self.assertEqual(len(cr.rules(self.doc.ifc)), 2)
        made = cr.apply_rules(self.doc)
        self.assertEqual(len(made["Sanitárias"]), 5)
        n1 = sum(1 for e in self.doc.ifc.file.by_type("IfcCovering"))
        cr.apply_rules(self.doc)                       # (again: replaced, not doubled)
        n2 = sum(1 for e in self.doc.ifc.file.by_type("IfcCovering"))
        self.assertEqual(n1, n2)
        self.assertTrue(room)

    def test_corners_lapped_and_coping(self):
        outside = bim.cover_category(self.doc, self.walls, "parede", "pedra_60x40", sides="exterior") \
            if self.rooms else bim.cover_category(self.doc, self.walls, "parede", "pedra_60x40")
        lapped = [g for g in outside if any(self.doc.ifc.tiled_extend(g))]
        self.assertGreaterEqual(len(lapped), 2)
        tops = bim.cover_category(self.doc, self.walls, "parede", "capeamento_pedra", sides="topo")
        self.assertEqual(len(tops), 4)
        v, _f = mesh(self.doc, tops[0])
        self.assertGreater(v[:, 2].min(), bim.WALL_HEIGHT - 1e-3)


class Expansion(unittest.TestCase):
    def test_expansion_joints(self):
        from arqbim.core import tiling as tl
        from shapely.geometry import Polygon as P
        face = P([(0, 0), (10, 0), (10, 3), (0, 3)])
        r, _m = tl.lay_all(face, tl.layout({"w": 0.6, "h": 0.6, "joint": 0.0, "exp_every": 4.0, "exp_width": 0.01}))
        covered = sum(p.area for p in r.pieces)
        self.assertAlmostEqual(covered, 30.0 - 2 * 3 * 0.01, places=3)


class Catalogue(unittest.TestCase):
    """(0.569) Panels, seamless coats, a finish kept as one's own."""

    def test_every_finish_lays(self):
        from arqbim.core import covering_finishes as cf
        doc = Document()
        for key in [k for k in cf.FINISHES if k in cf.BUILT_IN]:
            with self.subTest(key):
                g = bim.add_covering(doc, WALL, key)
                self.assertIsNotNone(doc.ifc.by_guid(g))

    def test_seamless_one_piece(self):
        doc = Document()
        g = bim.add_covering(doc, WALL, "microcimento", holes=[DOOR])
        r = doc.ifc.tiled_layout(g)
        self.assertEqual(len(r.pieces), 1)

    def test_own_finish(self):
        from arqbim.core import covering_finishes as cf
        doc = Document()
        g = bim.add_covering(doc, WALL, "azulejo_20x20")
        bim.set_covering(doc, g, layout={"pattern": "diagonal", "joint": 0.004})
        key = bim.save_covering_finish(doc, g, "Azulejo da avó", library=False)
        self.assertTrue(key.startswith(cf.CUSTOM_PREFIX))
        self.assertEqual(ifcopenshell.util.element.get_type(doc.ifc.by_guid(g)).Name, "Azulejo da avó")
        g2 = bim.add_covering(doc, FLOOR, key)
        self.assertEqual(doc.ifc.tiled_params(g2)["layout"]["pattern"], "diagonal")
        path = os.path.join(tempfile.mkdtemp(), "own.ifc")
        doc.ifc.file.write(path)
        del cf.FINISHES[key]
        from arqbim.ifc.model import IfcModel
        again = IfcModel(ifcopenshell.open(path)) if hasattr(IfcModel, "__init__") else None
        self.assertEqual(again.tiled_params(g2)["layout"]["pattern"], "diagonal")
        self.assertIn(key, cf.FINISHES)                 # (the project's own put back in the catalogue)


class Quantities(unittest.TestCase):
    """(0.570) Pieces to buy, waste, joints, glue, grout; the layout drawing and the list."""

    def test_figures_and_exports(self):
        doc = Document()
        g = bim.add_covering(doc, WALL, "azulejo_20x20", holes=[DOOR])
        each, total = bim.covering_quantities(doc, [g])
        q = each[g]
        self.assertAlmostEqual(q["area"], doc.ifc.describe(g)["params"]["area"], places=3)
        self.assertGreaterEqual(q["buy_area"], q["area"])
        self.assertGreater(q["joints_m"], 50.0)
        self.assertGreater(q["glue_kg"], 0.0)
        self.assertGreater(q["grout_kg"], 0.0)
        self.assertEqual(q["whole"] + q["cut"], q["pieces"])
        folder = tempfile.mkdtemp()
        n, rows = bim.covering_export(doc, g, os.path.join(folder, "p.dxf"), os.path.join(folder, "p.xlsx"))
        self.assertEqual(n, q["pieces"])
        with open(os.path.join(folder, "p.dxf"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("CORTES", text)
        self.assertIn("VAOS", text)
        self.assertTrue(os.path.getsize(os.path.join(folder, "p.xlsx")) > 1000)
        self.assertGreater(rows, 5)
