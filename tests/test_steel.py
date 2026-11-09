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


class SteelCuts(unittest.TestCase):
    """(0.496) Ends cut: a portal's knee in a mitre; a secondary beam coped onto a girder."""

    def test_a_knee_in_a_mitre(self):
        """A column IPE 300 (a steel piece, upright, 0 → 4 m) and a rafter IPE 300 from its top out 5 m, rising
        0,5 m: mitred, both lines end at the knee, each piece drawn out and cut by the plane that halves their angle —
        nothing of either beyond it (the column's material all on its side of the plane, the rafter's on its own); the
        lines read back as they are; one undo step; refused for two pieces that do not meet; the file valid."""
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        post = bim.add_steel_member(doc, (0.0, 0.0, 0.0), (0.0, 0.0, 4.0), catalog.BY_KEY["viga_ipe300"],
                                    function="column", cardinal=5, rotation=90.0)
        rafter = bim.add_steel_member(doc, (0.0, 0.0, 4.0), (5.0, 0.0, 4.5), catalog.BY_KEY["viga_ipe300"], cardinal=5)
        self.assertTrue(bim.mitre(doc, post, rafter))
        p, r = doc.ifc.steel_member_params(post), doc.ifc.steel_member_params(rafter)
        np.testing.assert_allclose((p["start"], p["end"], r["start"], r["end"]),
                                   ((0, 0, 0), (0, 0, 4), (0, 0, 4), (5, 0, 4.5)), atol=1e-6)
        up = np.array((0.0, 0.0, 1.0))
        out = np.array((5.0, 0.0, 0.5)) / np.linalg.norm((5.0, 0.0, 0.5))
        n = (up - (-out)) / np.linalg.norm(up + out)            # (the post's: away from it, past the knee)
        knee = np.array((0.0, 0.0, 4.0))
        pv, rv = doc.get(post).mesh.verts, doc.get(rafter).mesh.verts
        self.assertLess(float(((pv - knee) @ n).max()), 1e-4)            # (the post: none past the plane)
        self.assertGreater(float(((rv - knee) @ n).min()), -1e-4)        # (the rafter: none behind it)
        self.assertGreater(float(pv[:, 2].max()), 4.05)                   # (drawn out past the knee's line: its
        self.assertGreater(float(pv[:, 0].min()), -0.16)                  # outer corner filled)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertEqual(doc.ifc.steel_cuts(doc.ifc.by_guid(post))[0], [])
        far = bim.add_steel_member(doc, (10.0, 0.0, 0.0), (10.0, 0.0, 4.0), catalog.BY_KEY["viga_ipe300"],
                                   function="column")
        self.assertFalse(bim.mitre(doc, far, rafter))

    def test_a_beam_coped_onto_a_girder(self):
        """An IPE 200 drawn onto an IPE 400 girder, their tops level: it stops at the girder's web (+ 10 mm) and its
        top flange is coped back past the girder's flange (its top cut down by the girder's tf + r + 5 mm); its
        bottom, higher than the girder's bottom flange, is not; the girder is not touched."""
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        ipe400 = catalog.steel_spec(catalog.BY_KEY["viga_ipe300"], "IPE400", "S275")
        girder = bim.add_beam(doc, np.array((0.0, 0.0, 3.0)), np.array((6.0, 0.0, 3.0)), ipe400, 3.0)
        beam = bim.add_beam(doc, np.array((3.0, 5.0, 3.0)), np.array((3.0, 0.0, 3.0)), catalog.BY_KEY["viga_ipe200"],
                            3.0)
        v = doc.get(beam).mesh.verts
        self.assertAlmostEqual(float(v[:, 1].min()), 0.0043 + 0.010, places=6)        # (tw 8,6 / 2 + 10 mm)
        cuts, copes, _ext = doc.ifc.steel_cuts(doc.ifc.by_guid(beam))
        self.assertEqual(len(copes), 1)
        zone = (13.5 + 21.0) / 1000.0 + 0.005
        near = v[v[:, 1] < 0.0143 + (180 - 8.6) / 2000.0 - 0.010 + 0.005]        # (where the girder's flange is)
        self.assertLess(float(near[:, 2].max()), 3.0 - zone + 1e-6)                     # (coped)
        self.assertAlmostEqual(float(v[:, 2].max()), 3.0, places=6)                     # (its top further on)
        self.assertAlmostEqual(float(doc.get(girder).mesh.verts[:, 1].max()), 0.09, places=6)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class Connections(unittest.TestCase):
    """(0.497) Steel connections: the base plate."""

    def test_base_plate(self):
        """Under an HEB 200 column: one connection (an IfcElementAssembly) of a plate 400 × 400 × 20 (the column + 100
        each side) with its four holes, four anchor bolts M20 (down 20 + 30 + 400 mm, standing 80 over the plate) and
        the weld all round; its values changed (6 bolts, 500 wide): made again; the column given an HEB 300: the plate
        follows (500 × 500); too short an edge: warned (EN 1993-1-8); a bolt deleted: the whole connection goes; the
        column deleted: its connection with it; the file valid; undo."""
        import ifcopenshell.util.element as ue
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        column = bim.add_column(doc, np.array((2.0, 1.0, 0.0)), catalog.BY_KEY["pilar_heb200"], 3.0)
        concrete = bim.add_column(doc, np.array((8.0, 1.0, 0.0)), catalog.BY_KEY["pilar_30"], 3.0)
        made = bim.add_base_plates(doc)                               # (every steel column: not the concrete one)
        self.assertEqual(len(made), 1)
        self.assertEqual(bim.add_base_plates(doc), [])                # (it has one already)
        assembly = doc.ifc.by_guid(made[0])

        def parts():
            return {p.is_a(): [q for q in doc.ifc.connection_parts(assembly) if q.is_a() == p.is_a()]
                    for p in doc.ifc.connection_parts(assembly)}

        found = parts()
        self.assertEqual({k: len(v) for k, v in found.items()},
                         {"IfcPlate": 1, "IfcMechanicalFastener": 4, "IfcFastener": 1})
        plate = found["IfcPlate"][0]
        v = doc.get(plate.GlobalId).mesh.verts
        np.testing.assert_allclose((v.min(axis=0), v.max(axis=0)), ((1.8, 0.8, -0.02), (2.2, 1.2, 0.0)), atol=1e-6)
        bolt = found["IfcMechanicalFastener"][0]
        b = doc.get(bolt.GlobalId).mesh.verts
        self.assertAlmostEqual(float(b[:, 2].min()), -0.45, places=6)
        self.assertAlmostEqual(float(b[:, 2].max()), 0.08, places=6)
        self.assertEqual(ue.get_predefined_type(bolt), "ANCHORBOLT")
        weld = found["IfcFastener"][0]
        self.assertAlmostEqual(ue.get_psets(weld)["Pset_FastenerWeld"]["a"] * doc.ifc.unit_scale, 0.006)   # (6 mm)
        self.assertEqual(doc.ifc.kind_of(plate.GlobalId), "steel_part")
        info = doc.ifc.describe(plate.GlobalId)
        self.assertEqual((info["params"]["connection"], info["params"]["n"], info["params"]["warnings"]),
                         ("base_plate", 4, []))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.set_connection(doc, plate.GlobalId, n=6, A=500.0)
        found = parts()
        self.assertEqual(len(found["IfcMechanicalFastener"]), 6)
        v = doc.get(found["IfcPlate"][0].GlobalId).mesh.verts
        self.assertAlmostEqual(float(v[:, 0].max() - v[:, 0].min()), 0.5, places=6)
        bim.set_connection(doc, plate.GlobalId, A=0.0)
        bim.set_type(doc, column, catalog.steel_spec(catalog.BY_KEY["pilar_heb200"], "HEB300", "S275"))
        v = doc.get(parts()["IfcPlate"][0].GlobalId).mesh.verts       # (it follows the column: 300 + 200)
        self.assertAlmostEqual(float(v[:, 0].max() - v[:, 0].min()), 0.5, places=6)
        bim.set_connection(doc, made[0], e=20.0)
        self.assertEqual([c for c, _v in doc.ifc.connection_warnings(made[0])], ["edge"])
        bim.delete(doc, [parts()["IfcMechanicalFastener"][0].GlobalId])
        self.assertIsNone(doc.ifc.by_guid(made[0]))
        doc.undo()
        self.assertIsNotNone(doc.ifc.by_guid(made[0]))
        bim.delete(doc, [column])
        self.assertIsNone(doc.ifc.by_guid(made[0]))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        self.assertIsNotNone(concrete)


class BeamConnections(unittest.TestCase):
    """(0.498) Beam to column: the end plate and the fin plate."""

    def test_end_plate(self):
        """An IPE 300 between two HEB 200 columns turned to meet it with their flanges, 6 m apart: an end plate at each
        end — the beam held back 10 mm (to the plate: 20 mm, against the flange's face, the beam had stopped 10 mm
        short), the plate 150 × 300 × 20 on the flange, 4 rows of 2 bolts M20 through the plate and the flange (35 mm),
        nuts beyond; no warnings; deleting a plate gives the beam its end back."""
        import ifcopenshell.util.element as ue
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        for x in (0.0, 6.0):
            bim.add_column(doc, np.array((x, 0.0, 0.0)), catalog.BY_KEY["pilar_heb200"], 3.5, x_dir=(0.0, 1.0, 0.0))
        beam = bim.add_beam(doc, np.array((0.0, 0.0, 3.0)), np.array((6.0, 0.0, 3.0)), catalog.BY_KEY["viga_ipe300"],
                            3.0)
        v = doc.get(beam).mesh.verts
        self.assertAlmostEqual(float(v[:, 0].min()), 0.11, places=6)                 # (stopped at the flange + 10)
        made = bim.add_beam_connections(doc, "end_plate", [beam])
        self.assertEqual(len(made), 2)
        v = doc.get(beam).mesh.verts
        np.testing.assert_allclose((v[:, 0].min(), v[:, 0].max()), (0.12, 5.88), atol=1e-6)   # (held back to its
        a = doc.ifc.by_guid(made[0])                                                           # plates)
        parts = doc.ifc.connection_parts(a)
        plate = next(p for p in parts if p.is_a("IfcPlate"))
        bolts = [p for p in parts if p.is_a("IfcMechanicalFastener")]
        self.assertEqual((len(bolts), ue.get_predefined_type(bolts[0])), (8, "BOLT"))
        pv = doc.get(plate.GlobalId).mesh.verts
        np.testing.assert_allclose((pv.min(axis=0), pv.max(axis=0)), ((0.10, -0.075, 2.70), (0.12, 0.075, 3.0)),
                                   atol=1e-6)
        bv = doc.get(bolts[0].GlobalId).mesh.verts                       # (through the plate and the flange, 35 mm,
        self.assertLess(float(bv[:, 0].min()), 0.085 - 0.010)                  # its washer and nut beyond)
        self.assertGreater(float(bv[:, 0].max()), 0.12 + 0.010)                # (its head on the beam's side)
        self.assertEqual(doc.ifc.connection_warnings(made[0]), [])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.set_connection(doc, made[0], tp=30.0)                                             # (thicker: the beam
        self.assertAlmostEqual(float(doc.get(beam).mesh.verts[:, 0].min()), 0.13, places=6)  # shorter)
        plate = next(p for p in doc.ifc.connection_parts(doc.ifc.by_guid(made[0])) if p.is_a("IfcPlate"))  # (made
        bim.delete(doc, [plate.GlobalId])                                                              # again)
        self.assertIsNone(doc.ifc.by_guid(made[0]))
        self.assertAlmostEqual(float(doc.get(beam).mesh.verts[:, 0].min()), 0.11, places=6)  # (its end back)

    def test_fin_plate(self):
        """An IPE 200 onto the webs of two HEB 200 (it fits between their flanges): a fin plate at each end — welded
        to the web's face, 115 mm along the beam, beside the beam's web, 2 rows of bolts through plate and web; 3 rows
        would not fit between the IPE 200's flanges: warned."""
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        for x in (0.0, 6.0):
            bim.add_column(doc, np.array((x, 0.0, 0.0)), catalog.BY_KEY["pilar_heb200"], 3.5)
        beam = bim.add_beam(doc, np.array((0.0, 0.0, 3.0)), np.array((6.0, 0.0, 3.0)), catalog.BY_KEY["viga_ipe200"],
                            3.0)
        made = bim.add_beam_connections(doc, "fin_plate", [beam], params={"rows": 2})
        self.assertEqual(len(made), 2)
        parts = doc.ifc.connection_parts(doc.ifc.by_guid(made[0]))
        plate = next(p for p in parts if p.is_a("IfcPlate"))
        pv = doc.get(plate.GlobalId).mesh.verts
        np.testing.assert_allclose((pv[:, 0].min(), pv[:, 0].max()), (0.0045, 0.0045 + 0.115), atol=1e-6)
        self.assertAlmostEqual(float(pv[:, 1].max() - pv[:, 1].min()), 0.010, places=6)   # (10 mm thick, beside the
        self.assertAlmostEqual(float(min(abs(pv[:, 1]))), 0.0028, places=6)               # web: 5,6 / 2 off the axis)
        self.assertEqual(sum(1 for p in parts if p.is_a("IfcMechanicalFastener")), 2)
        self.assertEqual(doc.ifc.connection_warnings(made[0]), [])
        bim.set_connection(doc, made[0], rows=3)
        self.assertEqual([c for c, _v in doc.ifc.connection_warnings(made[0])], ["tall"])
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class Shed(unittest.TestCase):
    """(0.499) The steel shed: portal frames, purlins, bracing, knees and ridges mitred, base plates."""

    def test_layout(self):
        """24 m long, frames about every 6 m: 5 frames of two columns and two rafters, the ridge 1,06 m over the
        eaves at 10° over 12 m; purlins on each slope the length of the shed, on the rafters' tops, leaning with the
        roof; X bracing in the two end bays (walls and roof: 16 braces); the columns' depth in their frame's plane."""
        import numpy as np
        from arqbim.core import steel_shed
        shed = steel_shed.layout((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 24.0, rafter_depth=0.36)
        roles = [p.role for p in shed.pieces]
        self.assertEqual((shed.frames, roles.count("column"), roles.count("rafter"), roles.count("brace")),
                         (5, 10, 10, 16))
        self.assertEqual(len(shed.mitres), 15)
        self.assertEqual(len(shed.plates), 10)
        apex = shed.pieces[1].end
        np.testing.assert_allclose(apex, (0.0, 6.0, 6.0 + 6.0 * math.tan(math.radians(10.0))), atol=1e-9)
        purlins = [p for p in shed.pieces if p.role == "purlin"]
        self.assertEqual(len(purlins) % 2, 0)
        self.assertAlmostEqual(float(np.linalg.norm(purlins[0].end - purlins[0].start)), 24.0)
        self.assertEqual(purlins[0].cardinal, 2)
        self.assertAlmostEqual(abs(purlins[0].rotation), 10.0, places=6)       # (leaning with the roof)
        self.assertAlmostEqual(abs(shed.pieces[0].rotation) % 180.0, 0.0, places=6)     # (span along Y: an upright
        turned = steel_shed.layout((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 12.0)               # piece's depth is along Y
        self.assertAlmostEqual(abs(turned.pieces[0].rotation) % 180.0, 90.0, places=6)   # already; along X: turned)

    def test_made(self):
        """Made in the model: HEA 300 columns, IPE 360 rafters, C purlins, L bracing — 2 frames 6 m apart over 12 m:
        the knees and the ridges cut (each column and rafter has its cuts), a base plate under each column, the file
        valid; one undo takes it all."""
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        hea = catalog.steel_spec(catalog.BY_KEY["pilar_heb200"], "HEA300", "S275")
        ipe = catalog.steel_spec(catalog.BY_KEY["viga_ipe300"], "IPE360", "S275")
        made = bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.0, hea, ipe, catalog.BY_KEY["madre_c160"],
                              catalog.BY_KEY["contrav_l80"])
        kinds = [doc.ifc.kind_of(g) for g in made]
        self.assertEqual(kinds.count("steel_connection"), 4)
        columns = [g for g in made if doc.ifc.kind_of(g) == "steel_member" and doc.ifc.by_guid(g).is_a("IfcColumn")]
        rafters = [g for g in made if doc.ifc.kind_of(g) == "steel_member" and doc.ifc.by_guid(g).is_a("IfcBeam")]
        self.assertEqual((len(columns), len(rafters)), (4, 4))
        for g in columns + rafters:
            self.assertTrue(doc.ifc.steel_cuts(doc.ifc.by_guid(g))[0], g)
        top = max(float(doc.get(g).mesh.verts[:, 2].max()) for g in rafters)
        self.assertGreater(top, 6.0 + 6.0 * math.tan(math.radians(10.0)))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertTrue(all(doc.ifc.by_guid(g) is None for g in made))


def dataclasses_replace(spec, **fields):
    import dataclasses
    return dataclasses.replace(spec, **fields)


if __name__ == "__main__":
    unittest.main()
