"""0.494 — The steel sections and grades (core/steel.py): the catalogue's outlines against the published masses, the
properties against the catalogues' (ArcelorMittal's «Sections and merchant bars», EN 10219-2), names, grades."""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arqbim.core import steel  # noqa: E402


class Catalogue(unittest.TestCase):
    def test_every_outline_weighs_what_is_published(self):
        """Each hot-rolled section's outline (its radii, a UPN's slope) gives the mass its standard publishes: I and H
        and angles to 1 %, channels to 2 %; and every section has a closed, anticlockwise outline."""
        families = {f for f, _c, _s in steel.FAMILIES}
        self.assertEqual({s.family for s in steel.SECTIONS.values()}, families)
        self.assertGreater(len(steel.SECTIONS), 300)
        for sec in steel.SECTIONS.values():
            name = sec.name
            p = steel.properties(name)
            self.assertGreater(p["A"], 0.0, name)
            if sec.mass:
                limit = 0.02 if sec.family in steel.U_FAMILIES else 0.01
                self.assertLess(abs(p["A"] * 1e-4 * steel.DENSITY / sec.mass - 1.0), limit, name)

    def test_properties_as_the_catalogues(self):
        """IPE 300, HEB 200, UPN 200, L 100×10, SHS 100×100×5 (EN 10219), CHS 114,3×5: the catalogues' values."""
        published = {
            "IPE300": {"A": 53.81, "Iy": 8356, "Iz": 603.8, "Wel_y": 557.1, "Wpl_y": 628.4, "Wpl_z": 125.2,
                       "iy": 12.46, "iz": 3.35, "It": 20.12, "Iw": 125.9e3},
            "HEB200": {"A": 78.08, "Iy": 5696, "Iz": 2003, "Wel_y": 569.6, "Wpl_y": 642.5, "Wpl_z": 305.8,
                       "iy": 8.54, "iz": 5.07, "It": 59.28, "Iw": 171.1e3},
            "SHS100x100x5": {"A": 18.36, "Iy": 271.1, "Wel_y": 54.2, "Wpl_y": 64.9, "It": 441.0},
            "CHS114.3x5": {"A": 17.17, "Iy": 256.9, "Wel_y": 44.9, "Wpl_y": 59.8, "It": 513.8},
            "L100x10": {"A": 19.15, "Iy": 176.7},
            "UPN200": {"A": 32.2, "Iy": 1910, "Iz": 148, "Wel_y": 191},
        }
        tolerance = {"It": 0.06, "Iw": 0.03, "UPN200": 0.03}
        for name, values in published.items():
            p = steel.properties(name)
            for key, value in values.items():
                limit = max(tolerance.get(key, 0.01), tolerance.get(name, 0.0))
                self.assertLess(abs(p[key] / value - 1.0), limit, "{} {}: {} ≠ {}".format(name, key, p[key], value))

    def test_names_and_lookups(self):
        """Any way of writing a name finds its section; shown with spaces, × and a decimal comma."""
        for written in ("IPE 300", "ipe300", "IPE300"):
            self.assertEqual(steel.get(written).name, "IPE300")
        self.assertEqual(steel.get("CHS 114,3×5").name, "CHS114.3x5")
        self.assertEqual(steel.get("L 100×10").name, "L100x10")
        self.assertIsNone(steel.get("IPE 301"))
        self.assertEqual([steel.display(n) for n in ("IPE300", "L100x10", "L100x50x8", "SHS100x100x5",
                                                     "CHS114.3x5", "C160x60x20x2.5", "OMEGA40x50x20x1.5")],
                         ["IPE 300", "L 100×10", "L 100×50×8", "SHS 100×100×5", "CHS Ø114,3×5",
                          "C 160×60×20×2,5", "Ω 40×50×20×1,5"])
        self.assertEqual([s.name for s in steel.sections("HEB")][:3], ["HEB100", "HEB120", "HEB140"])
        self.assertEqual(steel.size(steel.get("Z200x70x20x2")), (138.0, 200.0))

    def test_grades(self):
        """EC3-1-1 Table 3.1: fy and fu by thickness; a material's grade."""
        self.assertEqual(steel.strength("S275", 10.7), (275.0, 430.0))
        self.assertEqual(steel.strength("S355", 45.0), (335.0, 470.0))
        self.assertEqual(steel.grade_of("aco_s355"), "S355")
        self.assertIsNone(steel.grade_of("concreto"))

    def test_outline_shapes(self):
        """The outlines in their boxes, their middles at the origin; a tube with its hole; a channel's web on the
        left; a Z's upper flange to the right."""
        for name in ("IPE300", "UPN200", "L100x50x8", "RHS200x100x8", "C160x60x20x2", "Z160x60x20x2",
                     "OMEGA40x50x20x1.5"):
            sec = steel.get(name)
            outer, holes = steel.outline(sec)
            xs, ys = [p[0] for p in outer], [p[1] for p in outer]
            w, h = steel.size(sec)
            self.assertAlmostEqual(max(xs) - min(xs), w, places=6, msg=name)
            self.assertAlmostEqual(max(ys) - min(ys), h, places=6, msg=name)
            self.assertAlmostEqual(max(xs) + min(xs), 0.0, places=6, msg=name)
            self.assertGreater(steel._ring_moments(outer)[0], 0.0, name)                   # (anticlockwise)
            self.assertEqual(len(holes), 1 if sec.family in ("SHS", "RHS", "CHS") else 0)
        self.assertLess(steel.properties("UPN200")["centroid"][0], 0.0)                     # (its web on the left)
        z = steel.properties("Z200x70x20x2")
        self.assertLess(abs(z["centroid"][0]), 1e-6)                                         # (point-symmetric)
        self.assertTrue(math.isfinite(steel.properties("OMEGA40x50x20x1.5")["Wpl_y"]))


class SteelTypes(unittest.TestCase):
    """The steel types in the IFC: the real section, named as the other programs name it; read back; weighed."""

    def test_columns_and_beams_of_steel(self):
        """An IPE 300 beam 5 m long and an HEB 200 column 3 m tall: their bodies the real sections (IfcIShapeProfileDef
        «IPE300»), the beam's top at its level, its weight 5 × 42,2 kg; the types read back as the catalogue's; every
        family's profile made and read back, the file valid; a type changed to another section: its beams follow."""
        os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))
        import ifcopenshell.util.element as ue
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim, project_types
        from arqbim.model.document import Document
        doc = Document()
        column = bim.add_column(doc, np.array((0.0, 0.0, 0.0)), catalog.BY_KEY["pilar_heb200"], 3.0)
        beam = bim.add_beam(doc, np.array((0.0, 0.0, 3.0)), np.array((5.0, 0.0, 3.0)), catalog.BY_KEY["viga_ipe300"],
                            3.0)
        v = doc.get(beam).mesh.verts                    # ((0.495) from the column's flange tips, + 10 mm: 4,89 m)
        np.testing.assert_allclose((v.min(axis=0), v.max(axis=0)), ((0.11, -0.075, 2.7), (5.0, 0.075, 3.0)), atol=1e-6)
        self.assertAlmostEqual(doc.get(beam).mesh.volume(), 4.89 * steel.properties("IPE300")["A"] * 1e-4, places=4)
        c = doc.get(column).mesh.verts
        np.testing.assert_allclose((c.min(axis=0), c.max(axis=0)), ((-0.1, -0.1, 0.0), (0.1, 0.1, 3.0)), atol=1e-6)
        e = doc.ifc.by_guid(beam)
        profile = ue.get_material(ue.get_type(e)).MaterialProfiles[0].Profile
        self.assertEqual((profile.is_a(), profile.ProfileName), ("IfcIShapeProfileDef", "IPE300"))
        self.assertAlmostEqual(ue.get_psets(e)["Qto_BeamBaseQuantities"]["NetWeight"], 4.89 * 42.2, places=6)
        shown = doc.ifc.describe(beam)["steel"]                         # (what the Properties show)
        self.assertEqual((shown[0], shown[1], shown[2]), ("IPE 300", "Aço estrutural S275", 42.2))
        self.assertAlmostEqual(shown[3], 4.89 * 42.2, places=6)
        self.assertEqual(doc.ifc.steel_section(column), "HEB200")
        read = project_types.read_type(doc.ifc, ue.get_type(e), "beam")
        self.assertEqual((read.section, read.shape, read.material, read.profile), ("IPE300", "steel", "aco_s275",
                                                                                   (0.15, 0.30)))
        for name in ("UPN200", "UPE200", "L100x10", "L100x50x8", "SHS100x100x5", "RHS200x100x8", "CHS114.3x5",
                     "C160x60x20x2", "Z160x60x20x2", "OMEGA40x50x20x1.5", "HEM300"):
            spec = catalog.steel_spec(catalog.BY_KEY["viga_ipe300"], name, "S355")
            spec = dataclasses_replace(spec, key="t:" + name)
            g = bim.add_beam(doc, np.array((0.0, 3.0, 3.0)), np.array((4.0, 3.0, 3.0)), spec, 3.0)
            back = project_types.read_type(doc.ifc, ue.get_type(doc.ifc.by_guid(g)), "beam")
            self.assertEqual((back.section, back.material), (steel.get(name).name, "aco_s355"), name)
            area = doc.get(g).mesh.volume() / 4.0 * 1e4
            self.assertLess(abs(area / steel.properties(name)["A"] - 1.0), 0.02, name)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.save_type(doc, catalog.steel_spec(catalog.BY_KEY["viga_ipe300"], "IPE400", "S275"),
                      catalog.BY_KEY["viga_ipe300"])
        v = doc.get(beam).mesh.verts
        self.assertAlmostEqual(float(v.max(axis=0)[2] - v.min(axis=0)[2]), 0.40, places=6)     # (now an IPE 400)


class SteelMembers(unittest.TestCase):
    """(0.495) Steel pieces between two points: a sloped rafter by its top, a brace, X bracing between two columns."""

    def test_pieces_between_two_points(self):
        """A rafter IPE 300 from (0, 0, 6) to (6, 0, 7) as a beam, by its top middle: its top on the line, sloped, 1
        undo step; its line read back (start, end, length) and its section; turned 90° it lies on its side; the same
        L 80×8 brace type as a purlin makes a purlin type; X bracing between two HEB columns 5 m apart, 4 m tall: two
        IfcMember BRACE from foot to top, crossing; a type change follows; the file valid."""
        import ifcopenshell.util.element as ue
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        rafter = bim.add_steel_member(doc, (0.0, 0.0, 6.0), (6.0, 0.0, 7.0), catalog.BY_KEY["viga_ipe300"])
        e = doc.ifc.by_guid(rafter)
        self.assertEqual((e.is_a(), doc.ifc.kind_of(rafter)), ("IfcBeam", "steel_member"))
        p = doc.ifc.steel_member_params(rafter)
        np.testing.assert_allclose((p["start"], p["end"]), ((0, 0, 6), (6, 0, 7)), atol=1e-6)
        self.assertAlmostEqual(p["length"], math.hypot(6.0, 1.0))
        self.assertEqual((p["function"], p["cardinal"], p["section"]), ("beam", 8, "IPE300"))
        v = doc.get(rafter).mesh.verts
        self.assertAlmostEqual(float(v[:, 2].max()), 7.0, places=4)                         # (its top on the line,
        self.assertAlmostEqual(float(v[:, 2].min()), 6.0 - 0.30 * 6.0 / math.hypot(6.0, 1.0), places=3)  # its ends square)
        doc.undo()
        self.assertIsNone(doc.ifc.by_guid(rafter))
        doc.redo()
        side = bim.add_steel_member(doc, (0.0, 3.0, 3.0), (5.0, 3.0, 3.0), catalog.BY_KEY["viga_ipe300"], rotation=90.0,
                                    cardinal=5)
        v = doc.get(side).mesh.verts
        self.assertAlmostEqual(float(v[:, 2].max() - v[:, 2].min()), 0.15, places=4)          # (on its side)
        purlin = bim.add_steel_member(doc, (0.0, 6.0, 3.0), (5.0, 6.0, 3.0), catalog.BY_KEY["contrav_l80"],
                                      function="purlin")
        t_ = ue.get_type(doc.ifc.by_guid(purlin))
        self.assertEqual((ue.get_predefined_type(doc.ifc.by_guid(purlin)), t_.is_a(), t_.PredefinedType, t_.Name),
                         ("PURLIN", "IfcMemberType", "PURLIN", "Madre L 80×8 — S275"))
        a = bim.add_column(doc, np.array((0.0, 10.0, 0.0)), catalog.BY_KEY["pilar_heb200"], 4.0)
        b = bim.add_column(doc, np.array((5.0, 10.0, 0.0)), catalog.BY_KEY["pilar_heb200"], 4.0)
        braces = bim.x_brace(doc, a, b, catalog.BY_KEY["contrav_l80"])
        self.assertEqual(len(braces), 2)
        for g in braces:
            m = doc.ifc.by_guid(g)
            self.assertEqual((m.is_a(), ue.get_predefined_type(m), ue.get_type(m).Name),
                             ("IfcMember", "BRACE", "Contraventamento L 80×8 — S275"))
            q = doc.ifc.steel_member_params(g)
            self.assertAlmostEqual(q["length"], math.hypot(5.0, 4.0))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.set_type(doc, braces[0], catalog.BY_KEY["contrav_chs76"])
        self.assertEqual(doc.ifc.steel_section(braces[0]), "CHS76.1x4")
        self.assertAlmostEqual(doc.ifc.steel_member_params(braces[0])["length"], math.hypot(5.0, 4.0))
        info = doc.ifc.describe(braces[0])
        self.assertEqual((info["kind"], info["params"]["function"]), ("steel_member", "brace"))

    def test_steel_beams_stop_at_the_columns(self):
        """An IPE 300 beam drawn from the middle of an HEB 300 column to another's, 6 m apart: along the columns'
        webs (their own y) it stops 10 mm short of their flanges; turned, it reaches their webs between the flanges
        (an IPE 200, 100 mm wide, fits the HEB 300's 208 mm); a concrete beam goes on to the middles as before."""
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        for x in (0.0, 6.0):
            bim.add_column(doc, np.array((x, 0.0, 0.0)), catalog.BY_KEY["pilar_heb200"], 3.0)
        flange = bim.add_beam(doc, np.array((0.0, 0.0, 3.0)), np.array((6.0, 0.0, 3.0)), catalog.BY_KEY["viga_ipe300"],
                              3.0)
        v = doc.get(flange).mesh.verts
        # (an HEB column made with x_dir along X: its flanges across X? its depth along its own y — the beam along X
        # meets its web side: an IPE 300 is 150 wide, the HEB 200's clear web 200 − 30 − 36 = 134: it does not fit,
        # so it stops at the flanges' tips, 100 + 10 mm from the middle)
        np.testing.assert_allclose((v[:, 0].min(), v[:, 0].max()), (0.11, 5.89), atol=1e-6)
        small = bim.add_beam(doc, np.array((0.0, 0.0, 2.5)), np.array((6.0, 0.0, 2.5)), catalog.BY_KEY["viga_ipe200"],
                             2.5)
        v = doc.get(small).mesh.verts                  # (an IPE 200, 100 wide, fits: onto the web, 4,5 + 10 mm)
        np.testing.assert_allclose((v[:, 0].min(), v[:, 0].max()), (0.0145, 5.9855), atol=1e-6)
        a = bim.add_column(doc, np.array((0.0, 10.0, 0.0)), catalog.BY_KEY["pilar_heb200"], 3.0)
        bim.add_column(doc, np.array((0.0, 16.0, 0.0)), catalog.BY_KEY["pilar_heb200"], 3.0)
        along = bim.add_beam(doc, np.array((0.0, 10.0, 3.0)), np.array((0.0, 16.0, 3.0)),
                             catalog.BY_KEY["viga_ipe300"], 3.0)
        v = doc.get(along).mesh.verts                  # (along their depth: onto the flanges' faces, 100 + 10 mm)
        np.testing.assert_allclose((v[:, 1].min(), v[:, 1].max()), (10.11, 15.89), atol=1e-6)
        self.assertIsNotNone(a)
        concrete = bim.add_beam(doc, np.array((0.0, 0.0, 2.0)), np.array((6.0, 0.0, 2.0)), catalog.BY_KEY["viga_20x40"],
                                2.0)
        v = doc.get(concrete).mesh.verts
        np.testing.assert_allclose((v[:, 0].min(), v[:, 0].max()), (0.0, 6.0), atol=1e-6)


def dataclasses_replace(spec, **fields):
    import dataclasses
    return dataclasses.replace(spec, **fields)


if __name__ == "__main__":
    unittest.main()
