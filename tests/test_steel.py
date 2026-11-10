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
        self.assertAlmostEqual(float(np.linalg.norm(purlins[0].end - purlins[0].start)), 24.0 + 2 * 0.15)  # (0.504:
        # past the end frames)
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
        self.assertEqual(kinds.count("steel_connection"), 4 + 8 + 20)       # (0.503: the wall braces' 8 gussets;
        # 0.504: the purlins' cleats — 5 a slope, on 2 frames)
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


class Marks(unittest.TestCase):
    """(0.500) Part marks and the steel lists."""

    def test_assign_keeps_marks(self):
        """The same pieces share a mark; numbered by prefix; a piece that stays the same keeps its mark; one that
        changed gets the next free number; renumbered: all anew."""
        from arqbim.core import steel_marks
        first = steel_marks.assign([("a", "V", ("IPE300", 5000), ""), ("b", "V", ("IPE300", 5000), ""),
                                    ("c", "V", ("IPE200", 4000), ""), ("d", "P", ("HEB200", 3000), "")])
        self.assertEqual(first["a"], first["b"])
        self.assertEqual(sorted(first.values()), ["P1", "V1", "V2", "V2"])          # (IPE 200 V1, IPE 300 V2)
        again = steel_marks.assign([("a", "V", ("IPE300", 5000), first["a"]), ("b", "V", ("IPE300", 5100), first["b"]),
                                    ("c", "V", ("IPE200", 4000), first["c"]), ("d", "P", ("HEB200", 3000), "P1")])
        self.assertEqual((again["a"], again["c"], again["d"]), (first["a"], first["c"], "P1"))   # (kept)
        self.assertNotIn(again["b"], (again["a"], again["c"]))                                   # (b changed: new)
        self.assertEqual(again["b"], "V3")
        cut = [{"end": 1, "p": [0.0, 0.1, 0.0], "n": [0.0, 0.7, 0.7]}]
        mirrored = [{"end": 1, "p": [0.0, -0.1, 0.0], "n": [0.0, -0.7, 0.7]}]
        flipped = [{"end": 0, "p": [0.0, 0.1, 0.0], "n": [0.0, 0.7, -0.7]}]
        sig = steel_marks.shape_signature
        self.assertEqual(sig(cut, [], (0.2, 0.0), True), sig(mirrored, [], (0.2, 0.0), True))   # (turned round)
        self.assertEqual(sig(cut, [], (0.0, 0.2), True), sig(flipped, [], (0.2, 0.0), True))    # (end for end)
        self.assertNotEqual(sig(cut, [], (0.2, 0.0), False), sig(mirrored, [], (0.2, 0.0), False))
        self.assertEqual(sorted(steel_marks.sort_key(m) for m in ("V10", "P2", "V2", "Ch1", "CV1")),
                         sorted(steel_marks.sort_key(m) for m in ("P2", "V2", "V10", "CV1", "Ch1")))

    def test_lists_of_a_shed(self):
        """A shed of 2 frames: the bill of materials — the columns one mark (4 alike), the rafters another (4 alike:
        mitred alike), the purlins, the braces, the plates; kg and m² totals; the bolts list — anchor bolts M20 × 530
        (4 per plate); numbered: the marks written on the pieces (their Tag), one undo step; again: none changes."""
        from arqbim.ifc import catalog
        from arqbim.model import bim, schedules
        from arqbim.model.document import Document
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"])
        rows = schedules.rows(doc, "steel")
        by_mark = {r["mark"]: r for r in rows}
        self.assertEqual((by_mark["P1"]["pieces"], by_mark["P1"]["section"]), (4, "HEB 200"))
        self.assertEqual((by_mark["V1"]["pieces"], by_mark["V1"]["section"]), (4, "IPE 300"))
        self.assertTrue(any(m.startswith("M") for m in by_mark) and any(m.startswith("CV") for m in by_mark))
        self.assertEqual(by_mark["Ch1"]["pieces"], 4)
        self.assertGreater(sum(r["weight"] for r in rows), 1000.0)
        self.assertEqual([r["mark"][0] for r in rows][:2], ["P", "V"])
        bolts = schedules.rows(doc, "bolts")
        self.assertEqual(sorted((b["bolt"], b["count"]) for b in bolts),
                         sorted([("M20 × 530", 16), ("M16 × 35", 16), ("M12 × 25", 40)]))   # (0.503: the gussets' —
        # 2 at each end of the 8 wall braces; 0.504: the purlins' cleats — 2 each, 20)
        self.assertGreater(bim.number_steel(doc), 0)
        tags = {doc.ifc.by_guid(g).Tag for r in rows for g in r["guids"]}
        self.assertEqual(tags, set(by_mark))
        self.assertEqual(doc.ifc.describe(by_mark["P1"]["guids"][0])["steel_mark"], "P1")      # (the Properties')
        self.assertEqual(bim.number_steel(doc), 0)
        doc.undo()
        self.assertTrue(all(not doc.ifc.by_guid(g).Tag for r in rows for g in r["guids"]))
        counts = schedules.counts(doc)
        self.assertEqual((counts["steel"], counts["bolts"]), (len(rows), 3))


class Fabrication(unittest.TestCase):
    """(0.501) DSTV NC1 files and the bars' cutting."""

    def test_nc1_and_parse(self):
        """An NC1 written and read back: its ST values in the standard's order, its holes, a plate's outline."""
        from arqbim.core import dstv
        text = dstv.nc1(dict(order="1", drawing="V1", phase="1", mark="V1", grade="S275", quantity=4, profile="IPE300",
                             code="I", length=5980.5, h=300, b=150, tf=10.7, tw=7.1, r=15, kg_m=42.2, paint_m=1.16,
                             cuts=(0.0, 45.0, 0.0, 0.0)), [("v", 50.0, 100.0, 22.0)], None)
        self.assertTrue(text.startswith("ST\n") and text.rstrip().endswith("EN"))
        back = dstv.parse(text)
        self.assertEqual(back["ST"][:9], ["1", "V1", "1", "V1", "S275", "4", "IPE300", "I", "5980.50"])
        self.assertEqual(back["ST"][16:20], ["0.00", "45.00", "0.00", "0.00"])
        self.assertEqual(back["BO"], [("v", 50.0, 100.0, 22.0)])
        plate = dstv.parse(dstv.nc1(dict(order="1", drawing="Ch1", phase="1", mark="Ch1", grade="S275", quantity=1,
                                         profile="PL20*400", code="B", length=400, h=400, b=0, tf=0, tw=20, r=0,
                                         kg_m=62.8, paint_m=0.8), [], [(0, 0), (400, 0), (400, 400), (0, 400)]))
        self.assertEqual(len(plate["AK"]), 5)                                      # (closed)

    def test_cutting(self):
        """Pieces of 5,9 m, 5,9 m, 3 m and 2 m out of 12 m bars: first fit, longest first — 2 bars; each cut loses
        3 mm; a piece longer than a bar: a bar of its own."""
        from arqbim.core import bar_cutting
        bars = bar_cutting.plan([("V1", 5900.0), ("V1", 5900.0), ("V2", 3000.0), ("V3", 2000.0)])
        self.assertEqual(len(bars), 2)
        self.assertEqual([m for m, _l in bars[0]["pieces"]], ["V1", "V1"])
        self.assertAlmostEqual(bars[0]["left"], 12000 - 5900 * 2 - 3)
        n, bought, used, waste, offcuts = bar_cutting.summary(bars)
        self.assertEqual((n, bought), (2, 24.0))
        self.assertAlmostEqual(used, 16.8)
        self.assertEqual(len(bar_cutting.plan([("P1", 13000.0)])), 1)

    def test_shed_files(self):
        """A shed's NC1 files: one per mark (P1, V1, M1, CV1, CV2, Ch1…), the columns' with their mitre angle at
        the top, the base plates' with their outline and 4 holes Ø22; and the bars to buy, a section each."""
        import tempfile
        from arqbim.core import dstv
        from arqbim.ifc import catalog
        from arqbim.model import bim, steel_fabrication
        from arqbim.model.document import Document
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"])
        files = steel_fabrication.nc1_files(doc)
        self.assertTrue({"P1", "V1", "M1", "Ch1"} <= set(files))
        column = dstv.parse(files["P1"])
        self.assertEqual((column["ST"][3], column["ST"][5], column["ST"][6], column["ST"][7]), ("P1", "4", "HEB200", "I"))
        self.assertGreater(abs(float(column["ST"][17])), 1.0)                          # (its top cut at an angle)
        plate = dstv.parse(files["Ch1"])
        self.assertEqual((plate["ST"][7], len(plate["BO"]), plate["BO"][0][3]), ("B", 4, 22.0))
        rows = steel_fabrication.cutting(doc)
        self.assertEqual({r["section"] for r in rows} >= {"HEB 200", "IPE 300"}, True)
        self.assertTrue(all(r["bars"] >= 1 and r["bought"] >= r["used"] for r in rows))
        folder = tempfile.mkdtemp(prefix="arqsynth_nc1_")
        paths = steel_fabrication.write(doc, folder)
        self.assertTrue(any(p.endswith("P1.nc1") for p in paths) and any(p.endswith(".csv") for p in paths))
        # (0.511) each NC1 marked (SI: its mark, on the web near its start; a plate's clear of its holes) and the
        # plates' DXF: each plate mark's outline (a gusset's own), its holes, its texts
        self.assertEqual(column["SI"], ["P1"])
        self.assertEqual(plate["SI"], ["Ch1"])
        import math
        si = files["Ch1"].split("SI\n", 1)[1].split()
        x, y = float(si[1].rstrip("u")), float(si[2])
        self.assertTrue(all(math.hypot(x - hx, y - hy) >= 2 * d for _f, hx, hy, d in plate["BO"]))
        dxf_path = next(p for p in paths if p.endswith("chapas.dxf"))
        with open(dxf_path, encoding="ascii") as f:
            text = f.read()
        self.assertTrue(text.startswith("0\nSECTION") and text.rstrip().endswith("EOF"))
        self.assertEqual(text.count("\nCIRCLE\n"), 4 + 2 + 2)                # (base plate 4, gusset 2, cleat 2)
        self.assertEqual(text.count("\nPOLYLINE\n"), 3)
        self.assertIn("\nCh2\n", text)


class ShopDrawing(unittest.TestCase):
    """(0.502) The steel pieces' fabrication drawing."""

    def test_parts_drawing(self):
        """A shed's pieces drawn once a mark: a line of text for each mark (P1, V1, M1, CV…, Ch1), each piece's outline
        side on — the column with its mitred top (an outline of more than 4 sides) —, its length and depth dimensioned;
        the plates flat with their 4 holes; on a sheet at 1:50; none for a model without steel."""
        from arqbim.ifc import catalog
        from arqbim.model import bim, drawings, sheets
        from arqbim.model.document import Document
        doc = Document()
        self.assertIsNone(drawings.of_view(doc, "steel_parts", "", "Peças"))
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"])
        drawing = drawings.of_view(doc, "steel_parts", "", "Peças de aço")
        texts = [a[3] for a in drawing.annotations if a[0] == "text"]
        for mark in ("P1", "V1", "M1", "Ch1"):
            self.assertTrue(any(s.startswith(mark + " —") for s in texts), mark)
        self.assertTrue(any("4 furos Ø22" in s and s.endswith("(1:10)") for s in texts))
        self.assertGreater(len(drawing.dims), 8)
        plate_dims = [d for d in drawing.dims if d[4] in ("50", "300", "400")]   # edge, holes, whole: real sizes (mm)
        self.assertTrue(all(d[4].isdigit() for d in drawing.dims))          # (0.504: whole millimetres)
        self.assertGreaterEqual(len(plate_dims), 4)
        self.assertGreater(len(drawing.lines), 30)
        self.assertIn("steel_parts", sheets.KINDS)
        self.assertEqual(sheets.USUAL_SCALES["steel_parts"], 50)


class Gussets(unittest.TestCase):
    """(0.503) The braces' gussets."""

    def _gussets(self, doc):
        return [a for a in doc.ifc.file.by_type("IfcElementAssembly")
                if doc.ifc.kind_of(a.GlobalId) == "steel_connection" and doc.ifc.connection_params(a.GlobalId)[0] ==
                "gusset"]

    def test_shed_gussets(self):
        """A shed's wall braces (L 80×8) get a gusset at each end on the HEB 200 columns — 8 in its two walls' end bay
        —: the brace held back the same at both ends, clear of the column's flanges' tips by the 20 mm gap; the plate
        10 mm thick in the brace's plane against the back of its leg, two M16 bolts through both, a weld; no warnings;
        the gussets alike share one mark, their NC1 with their own outline; the gap made 40: held back more."""
        import json
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim, steel_fabrication
        from arqbim.model.document import Document
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"])
        gussets = self._gussets(doc)
        self.assertEqual(len(gussets), 8)
        for a in gussets:
            _kind, (brace, column), params = doc.ifc.connection_params(a.GlobalId)
            parts = doc.ifc.connection_parts(a)
            self.assertEqual(sum(1 for p in parts if p.is_a("IfcMechanicalFastener")), 2)
            self.assertEqual(sum(1 for p in parts if p.is_a("IfcFastener")), 1)
            self.assertEqual(doc.ifc.connection_warnings(a.GlobalId), [])
            e0, e1 = doc.ifc.steel_cuts(doc.ifc.by_guid(brace))[2]
            self.assertAlmostEqual(e0, e1, places=6)
            self.assertLess(e0, -0.15)
            centre = doc.ifc.column_box(column)[0]
            verts = doc.get(brace).mesh.verts
            self.assertGreaterEqual(float(np.abs(verts[:, 0] - centre[0]).min()), 0.10 + 0.02 - 1e-3)
            plate = next(p for p in parts if p.is_a("IfcPlate"))
            pv = doc.get(plate.GlobalId).mesh.verts
            self.assertAlmostEqual(float(pv[:, 1].max() - pv[:, 1].min()), 0.010, places=4)     # (10 mm, across)
            self.assertAlmostEqual(float(pv[:, 1].max()), float(verts[:, 1].min()), places=4)  # (on the leg's back)
            record = json.loads(doc.ifc._params(plate)["Chapa"])
            self.assertEqual(len(record["furos"]), 2)
            self.assertGreaterEqual(len(record["contorno"]), 4)
        marks, _pieces = doc.ifc.steel_marks()
        plates = [p.GlobalId for a in gussets for p in doc.ifc.connection_parts(a) if p.is_a("IfcPlate")]
        self.assertEqual(len({marks[g] for g in plates}), 1)
        text = steel_fabrication.nc1_files(doc)[marks[plates[0]]]
        ak = text.split("AK\n", 1)[1].split("BO\n", 1)[0].strip().splitlines()
        self.assertEqual(len(ak), len(record["contorno"]) + 1)              # (its own outline, closed)
        brace = doc.ifc.connection_params(gussets[0].GlobalId)[1][0]
        before = doc.ifc.steel_cuts(doc.ifc.by_guid(brace))[2]
        bim.set_connection(doc, gussets[0].GlobalId, gap=40.0)
        after = doc.ifc.steel_cuts(doc.ifc.by_guid(brace))[2]
        end = int(doc.ifc.connection_params(gussets[0].GlobalId)[2]["end"])
        self.assertLess(after[end], before[end] - 0.015)
        self.assertAlmostEqual(after[1 - end], before[1 - end], places=6)

    def test_add_gussets_and_tubes(self):
        """A shed without its plates: no gussets; «Gousset» on all its braces: the wall braces' 8 (the roof's reach no
        column); again: none more; a tube brace is refused; deleting a brace takes its gussets; undone, back."""
        from arqbim.ifc import catalog
        from arqbim.ifc.edit import EditRefused
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"],
                       plates=False)
        self.assertEqual(self._gussets(doc), [])
        made = bim.add_gussets(doc)
        self.assertEqual(len(made), 8)
        self.assertEqual(bim.add_gussets(doc), [])
        columns = bim.steel_columns(doc)
        tube = bim.add_steel_member(doc, (0.0, 0.0, 0.0), (6.0, 0.0, 3.0), catalog.BY_KEY["contrav_chs76"],
                                    function="brace")
        self.assertEqual(bim.gusset_ends(doc, [tube]), [])
        with self.assertRaises(EditRefused):
            doc.ifc.add_connection("gusset", [tube, columns[0]])
        brace = doc.ifc.connection_params(made[0])[1][0]
        n = len(doc.ifc.connections_on([brace]))
        self.assertEqual(n, 2)
        bim.delete(doc, [brace])
        self.assertEqual(len(self._gussets(doc)), 6)
        doc.undo()
        self.assertEqual(len(self._gussets(doc)), 8)


class PurlinCleats(unittest.TestCase):
    """(0.504) The purlins' cleats."""

    def _cleats(self, doc):
        return [a for a in doc.ifc.file.by_type("IfcElementAssembly")
                if doc.ifc.kind_of(a.GlobalId) == "steel_connection" and doc.ifc.connection_params(a.GlobalId)[0] ==
                "purlin_cleat"]

    def _shed(self, **options):
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"],
                       **options)
        return doc

    def test_shed_cleats(self):
        """A shed's C 160 purlins get a cleat on each rafter they sit on (5 a slope, 2 slopes, 2 frames: 20): seen in
        the purlin's own frame, the plate 8 mm thick against the back of its web (x −38 to −30 mm), standing on the
        rafter's top (from 0 to 110 mm: 0,7 × 160), 100 mm along the purlin and under it — the purlins go 15 cm past
        the end frames —; two M12 through the plate and the web; a weld; no warnings; all one mark; its height typed
        90: made 90 high."""
        import numpy as np
        from arqbim.model import bim
        doc = self._shed()
        cleats = self._cleats(doc)
        self.assertEqual(len(cleats), 20)
        for a in cleats:
            _kind, (purlin, beam), _params = doc.ifc.connection_params(a.GlobalId)
            start, end, along, xl, yl, _mid = doc.ifc.brace_frame(purlin)
            parts = doc.ifc.connection_parts(a)
            plate = next(p for p in parts if p.is_a("IfcPlate"))
            r = (doc.get(plate.GlobalId).mesh.verts - start) * 1000.0
            x, y, s = r @ xl, r @ yl, r @ along
            np.testing.assert_allclose((x.min(), x.max(), y.min(), y.max()), (-38.0, -30.0, 0.0, 110.0), atol=0.05)
            self.assertAlmostEqual(float(s.max() - s.min()), 100.0, places=3)
            self.assertTrue(0.0 <= s.min() and s.max() <= float(np.linalg.norm(end - start)) * 1000.0)
            self.assertEqual(sum(1 for p in parts if p.is_a("IfcMechanicalFastener")), 2)
            self.assertEqual(sum(1 for p in parts if p.is_a("IfcFastener")), 1)
            self.assertEqual(doc.ifc.connection_warnings(a.GlobalId), [])
        marks, _pieces = doc.ifc.steel_marks()
        plates = [p.GlobalId for a in cleats for p in doc.ifc.connection_parts(a) if p.is_a("IfcPlate")]
        self.assertEqual(len({marks[g] for g in plates}), 1)
        bim.set_connection(doc, cleats[0].GlobalId, H=90.0)
        plate = next(p for p in doc.ifc.connection_parts(cleats[0]) if p.is_a("IfcPlate"))
        self.assertTrue(plate.Name.endswith("100×90×8"), plate.Name)

    def test_add_cleats(self):
        """A shed without its plates: no cleats; «Apoio de madre» on every purlin: the 20; again: none more; a tube
        is refused (it has no web to bolt through), and a purlin off the beam too; a rafter deleted takes its cleats;
        undone: back."""
        from arqbim.ifc import catalog
        from arqbim.ifc.edit import EditRefused
        from arqbim.model import bim
        doc = self._shed(plates=False)
        self.assertEqual(self._cleats(doc), [])
        made = bim.add_purlin_cleats(doc)
        self.assertEqual(len(made), 20)
        self.assertEqual(bim.add_purlin_cleats(doc), [])
        _kind, (purlin, rafter), _p = doc.ifc.connection_params(made[0])
        tube = bim.add_steel_member(doc, (0.0, 1.0, 7.0), (6.0, 1.0, 7.0), catalog.BY_KEY["contrav_chs76"],
                                    function="purlin")
        self.assertEqual(bim.purlin_seats(doc, [tube]), [])
        with self.assertRaises(EditRefused):
            doc.ifc.add_connection("purlin_cleat", [tube, rafter])
        other = next(g for g in doc.ifc.purlin_beams(purlin) if g != rafter) if len(doc.ifc.purlin_beams(purlin)) > 1 \
            else None
        far = next(o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcBeam"
                   and o.id not in doc.ifc.purlin_beams(purlin))
        with self.assertRaises(EditRefused):
            doc.ifc.add_connection("purlin_cleat", [purlin, far])
        self.assertIsNotNone(other)
        on_rafter = [a for a in self._cleats(doc) if doc.ifc.connection_params(a.GlobalId)[1][1] == rafter]
        self.assertEqual(len(on_rafter), 5)
        bim.delete(doc, [rafter])
        self.assertEqual(len(self._cleats(doc)), 15)
        doc.undo()
        self.assertEqual(len(self._cleats(doc)), 20)


class EqualNodes(unittest.TestCase):
    """(0.505) «Aplicar aos nós iguais» — DetailCraft's «copy to equal nodes»."""

    def _shed(self, **options):
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"],
                       **options)
        return doc

    def _of(self, doc, kind):
        return [a for a in doc.ifc.file.by_type("IfcElementAssembly")
                if doc.ifc.kind_of(a.GlobalId) == "steel_connection" and doc.ifc.connection_params(a.GlobalId)[0] == kind]

    def test_values_to_the_others(self):
        """A shed: one base plate made 30 mm thick, applied: the other 3 too (none made); one gusset's gap 40, applied:
        the other 7 too, each brace held back as the first; one undo takes it back."""
        from arqbim.model import bim
        doc = self._shed()
        plates = self._of(doc, "base_plate")
        bim.set_connection(doc, plates[0].GlobalId, tp=30.0)
        self.assertEqual(bim.apply_to_equal(doc, plates[0].GlobalId), (3, 0))
        self.assertTrue(all(doc.ifc.connection_params(a.GlobalId)[2]["tp"] == 30.0 for a in self._of(doc, "base_plate")))
        gussets = self._of(doc, "gusset")
        bim.set_connection(doc, gussets[0].GlobalId, gap=40.0)
        self.assertEqual(bim.apply_to_equal(doc, gussets[0].GlobalId), (7, 0))
        holds = set()
        for a in self._of(doc, "gusset"):
            _k, (brace, _c), params = doc.ifc.connection_params(a.GlobalId)
            self.assertEqual(params["gap"], 40.0)
            holds.add(round(doc.ifc.steel_cuts(doc.ifc.by_guid(brace))[2][params["end"]], 6))
        self.assertEqual(len(holds), 1)
        doc.undo()
        self.assertEqual(sum(1 for a in self._of(doc, "gusset") if doc.ifc.connection_params(a.GlobalId)[2]["gap"] ==
                             40.0), 1)

    def test_put_on_free_nodes(self):
        """A shed without its plates: a base plate under one column, applied: under the other 3 (its values); one
        purlin's 2 cleats, one applied: the other its values, every other purlin's made (18); end plates on one IPE
        300 between two HEB 200 (their flanges to it), applied: on the other IPE 300 alike, not on an IPE 200."""
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim
        doc = self._shed(plates=False)
        columns = bim.steel_columns(doc)
        made = bim.add_base_plates(doc, [columns[0]], {"tp": 25.0})
        self.assertEqual(bim.apply_to_equal(doc, made[0]), (0, 3))
        self.assertEqual(sorted(doc.ifc.connection_params(a.GlobalId)[2]["tp"] for a in self._of(doc, "base_plate")),
                         [25.0] * 4)
        purlin = bim.purlin_seats(doc)[0][0]
        cleats = bim.add_purlin_cleats(doc, [purlin])
        self.assertEqual(len(cleats), 2)
        self.assertEqual(bim.apply_to_equal(doc, cleats[0]), (1, 18))
        self.assertEqual(len(self._of(doc, "purlin_cleat")), 20)
        from arqbim.model.document import Document
        doc = Document()
        for x in (0.0, 6.0, 12.0):
            bim.add_column(doc, np.array((x, 0.0, 0.0)), catalog.BY_KEY["pilar_heb200"], 3.5, x_dir=(0.0, 1.0, 0.0))
        b1 = bim.add_beam(doc, np.array((0.0, 0.0, 3.0)), np.array((6.0, 0.0, 3.0)), catalog.BY_KEY["viga_ipe300"], 3.0)
        b2 = bim.add_beam(doc, np.array((6.0, 0.0, 3.0)), np.array((12.0, 0.0, 3.0)), catalog.BY_KEY["viga_ipe300"], 3.0)
        b3 = bim.add_beam(doc, np.array((6.0, 0.0, 2.0)), np.array((12.0, 0.0, 2.0)), catalog.BY_KEY["viga_ipe200"], 2.0)
        ends = bim.add_beam_connections(doc, "end_plate", [b1])
        self.assertEqual(len(ends), 2)
        self.assertEqual(bim.apply_to_equal(doc, ends[0]), (1, 2))
        self.assertEqual(len(doc.ifc.connections_on([b2])), 2)
        self.assertEqual(doc.ifc.connections_on([b3]), [])


class BeamOnGirder(unittest.TestCase):
    """(0.506) A beam on a girder: the fin plate on the girder's web."""

    def test_fin_plate_on_a_girder(self):
        """An IPE 200 drawn to an IPE 300 girder's middle: stopped 10 mm from its web and coped (0.496); «Cutelo»: one
        fin plate, members (the beam, the girder), welded to the girder's web face (3,55 mm from its axis) and 115
        mm along the beam, beside the beam's web, 2 rows: no warnings — 3 rows: too tall for the IPE 200 —; the
        other end (free) none; «Aplicar aos nós iguais» with a second alike beam: put there with its values; an end
        plate is not put on a girder."""
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        girder = bim.add_beam(doc, np.array((0.0, 0.0, 3.0)), np.array((0.0, 6.0, 3.0)), catalog.BY_KEY["viga_ipe300"],
                              3.0)
        beam = bim.add_beam(doc, np.array((0.0, 2.0, 3.0)), np.array((4.0, 2.0, 3.0)), catalog.BY_KEY["viga_ipe200"],
                            3.0)
        self.assertEqual(doc.ifc.beam_end_girder(beam, 0), girder)
        self.assertIsNone(doc.ifc.beam_end_girder(beam, 1))
        self.assertEqual(bim.add_beam_connections(doc, "end_plate", [beam]), [])
        made = bim.add_beam_connections(doc, "fin_plate", [beam], {"rows": 2})
        self.assertEqual(len(made), 1)
        kind, members, params = doc.ifc.connection_params(made[0])
        self.assertEqual((kind, members, params["end"]), ("fin_plate", [beam, girder], 0))
        self.assertEqual(doc.ifc.connection_warnings(made[0]), [])
        a = doc.ifc.connection_of(made[0])
        plate = next(p for p in doc.ifc.connection_parts(a) if p.is_a("IfcPlate"))
        v = doc.get(plate.GlobalId).mesh.verts
        self.assertAlmostEqual(float(v[:, 0].min()), 0.00355, places=5)
        self.assertAlmostEqual(float(v[:, 0].max()), 0.00355 + 0.115, places=5)
        self.assertAlmostEqual(float(v[:, 1].max()), 2.0 - 0.0056 / 2.0, places=5)     # (beside the IPE 200's web)
        bim.set_connection(doc, made[0], rows=3)
        self.assertIn("tall", [c for c, _v in doc.ifc.connection_warnings(made[0])])
        second = bim.add_beam(doc, np.array((0.0, 4.0, 3.0)), np.array((4.0, 4.0, 3.0)), catalog.BY_KEY["viga_ipe200"],
                              3.0)
        self.assertEqual(bim.apply_to_equal(doc, made[0]), (0, 1))
        fins = [c for c in doc.ifc.connections_on([second]) if doc.ifc.connection_params(c.GlobalId)[0] == "fin_plate"]
        self.assertEqual(len(fins), 1)
        self.assertEqual(doc.ifc.connection_params(fins[0].GlobalId)[2]["rows"], 3)


class Truss(unittest.TestCase):
    """(0.507) The truss."""

    def test_layout(self):
        """12 m in panels of 1,5 m: 8 panels; a Pratt: 2 chords, 9 verticals, 8 diagonals falling towards the middle
        (from the top on the support's side to the bottom on the middle's); a Howe: rising towards it; a Warren: only
        its 2 end verticals, its diagonals in a zigzag; 10,5 m: 7 panels made 8 (an even number)."""
        import numpy as np
        from arqbim.core import steel_truss
        pratt = steel_truss.layout((0.0, 0.0, 0.0), (12.0, 0.0, 0.0), "pratt", 1.2, 1.5, 3.0)
        roles = [p.role for p in pratt.pieces]
        self.assertEqual((pratt.panels, roles.count("chord"), roles.count("vertical"), roles.count("diagonal")),
                         (8, 2, 9, 8))
        chords = [p for p in pratt.pieces if p.role == "chord"]
        self.assertEqual(sorted(round(float(c.start[2]), 6) for c in chords), [3.0, 4.2])
        for d in (p for p in pratt.pieces if p.role == "diagonal"):
            middle_side = d.end if abs(d.end[0] - 6.0) < abs(d.start[0] - 6.0) else d.start
            support_side = d.start if middle_side is d.end else d.end
            self.assertLess(middle_side[2], support_side[2])                 # (Pratt: down towards the middle)
        howe = steel_truss.layout((0.0, 0.0, 0.0), (12.0, 0.0, 0.0), "howe", 1.2, 1.5, 3.0)
        for d in (p for p in howe.pieces if p.role == "diagonal"):
            middle_side = d.end if abs(d.end[0] - 6.0) < abs(d.start[0] - 6.0) else d.start
            support_side = d.start if middle_side is d.end else d.end
            self.assertGreater(middle_side[2], support_side[2])              # (Howe: up towards the middle)
        warren = steel_truss.layout((0.0, 0.0, 0.0), (12.0, 0.0, 0.0), "warren", 1.2, 1.5, 3.0)
        self.assertEqual([p.role for p in warren.pieces].count("vertical"), 2)
        ups = [bool(d.end[2] > d.start[2]) for d in warren.pieces if d.role == "diagonal"]
        self.assertTrue(all(a != b for a, b in zip(ups, ups[1:])))           # (a zigzag)
        self.assertEqual(steel_truss.layout((0.0, 0.0, 0.0), (10.5, 0.0, 0.0), panel=1.5).panels, 8)
        np.testing.assert_allclose(pratt.pieces[0].end, (12.0, 0.0, 3.0))
        with self.assertRaises(ValueError):
            steel_truss.layout((0.0, 0.0, 0.0), (12.0, 0.0, 0.0), "fink")

    def test_made(self):
        """Made in the model, SHS 150 chords and CHS 76 web, 12 m: 19 members (IfcMember), the chords of SHS, the web
        of CHS, named Banzo / Montante / Diagonal; marks for them; the file valid; one undo takes it all."""
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        made = bim.steel_truss(doc, (0.0, 0.0, 0.0), (12.0, 0.0, 0.0), catalog.BY_KEY["pilar_shs150"],
                               catalog.BY_KEY["contrav_chs76"], kind="pratt", height=1.2, panel=1.5, elevation=3.0)
        self.assertEqual(len(made), 19)
        self.assertTrue(all(doc.ifc.by_guid(g).is_a("IfcMember") for g in made))
        sections = [doc.ifc.steel_section(g) for g in made]
        self.assertEqual(sum(1 for s in sections if s.startswith("SHS")), 2)
        self.assertEqual(sum(1 for s in sections if s.startswith("CHS")), 17)
        names = [doc.ifc.by_guid(g).Name.split(" ")[0] for g in made]
        self.assertEqual({names[0], names[2], names[-1]}, {"Banzo", "Montante", "Diagonal"})
        marks, _pieces = doc.ifc.steel_marks()
        self.assertTrue(all(marks.get(g) for g in made))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        self.assertTrue(all(doc.ifc.by_guid(g) is None for g in made))


class SteelFloor(unittest.TestCase):
    """(0.508) A steel floor: the beam system of steel beams."""

    def test_floor(self):
        """A 6 × 5 m bay of IPE 300 between HEB 200 columns; a beam system of 3 IPE 200 along Y: each stopped 10 mm
        from the girders' webs (13,55 mm from their axes) and coped, a fin plate of 2 rows (what fits an IPE 200) at
        each end, no warnings; laid again as 2: the old ones' plates gone with them (4 left); axis 2 moved 1 m out:
        the system laid again in the wider bay, its beams still at the webs, their plates on them."""
        import numpy as np
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        bim.generate_grid(doc, [0.0, 6.0], [0.0, 5.0])
        bim.columns_on_grid(doc, None, catalog.BY_KEY["pilar_heb200"], 3.0, doc.active_storey)
        bim.beams_between(doc, None, catalog.BY_KEY["viga_ipe300"])
        made, skipped = bim.beam_system(doc, None, "y", "count", 3, catalog.BY_KEY["viga_ipe200"])
        self.assertEqual((len(made), skipped), (3, 0))

        def connections():
            return [a for a in doc.ifc.file.by_type("IfcElementAssembly")
                    if doc.ifc.kind_of(a.GlobalId) == "steel_connection"]
        for g in made:
            start, end, _top, _w, _h = doc.ifc.beam_params(g)
            self.assertAlmostEqual(float(start[1]), 0.00355 + 0.010, places=5)
            self.assertAlmostEqual(float(end[1]), 5.0 - 0.00355 - 0.010, places=5)
            self.assertTrue(doc.ifc.steel_cuts(doc.ifc.by_guid(g))[1])                   # (coped)
            fins = doc.ifc.connections_on([g])
            self.assertEqual(sorted(doc.ifc.connection_params(a.GlobalId)[2]["end"] for a in fins), [0, 1])
            self.assertTrue(all(doc.ifc.connection_params(a.GlobalId)[2]["rows"] == 2 for a in fins))
            self.assertTrue(all(doc.ifc.connection_warnings(a.GlobalId) == [] for a in fins))
        made, _ = bim.beam_system(doc, None, "y", "count", 2, catalog.BY_KEY["viga_ipe200"])
        self.assertEqual(len(connections()), 4)
        idx = {a.tag: k for k, a in enumerate(doc.grids)}
        k = idx["2"]
        axis = doc.grids[k]
        bim.move_grid_axes(doc, {k: ((axis.start[0] + 1.0, axis.start[1]), (axis.end[0] + 1.0, axis.end[1]))})
        xs = sorted(round(float(doc.ifc.beam_params(g)[0][0]), 4) for g in made)
        self.assertGreater(xs[-1], 4.2)                                                 # (the wider bay's)
        for g in made:
            start = doc.ifc.beam_params(g)[0]
            self.assertAlmostEqual(float(start[1]), 0.01355, places=5)
            for a in doc.ifc.connections_on([g]):
                plate = next(p for p in doc.ifc.connection_parts(a) if p.is_a("IfcPlate"))
                v = doc.get(plate.GlobalId).mesh.verts
                self.assertLess(abs(float(v[:, 0].max()) - float(start[0])), 0.02)      # (beside the beam, moved)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])


class SteelStair(unittest.TestCase):
    """(0.509) The steel stair."""

    def test_geometry(self):
        """3 m in risers of at most 18 cm: 17 of 17,6 cm, 16 treads; grating 30 mm thick, chequered plate 6 mm with a
        40 mm lip; each over the one below by 3 cm; a stringer's cuts: level at the floor, plumb at the last riser's
        line (16 × 28 cm), level at the floor above."""
        from arqbim.core import steel_stair
        grid = steel_stair.treads(3.0, 0.28, "grelha")
        self.assertEqual(len(grid), 16)
        x0, x1, top, ring = grid[0]
        self.assertAlmostEqual(x0, -0.03)
        self.assertAlmostEqual(top - min(z for _x, z in ring), 0.030)
        plate = steel_stair.treads(3.0, 0.28, "chapa")
        self.assertAlmostEqual(plate[0][2] - min(z for _x, z in plate[0][3]), 0.040)
        start, end, cuts = steel_stair.stringer(3.0, 0.28, 0.2)
        self.assertLess(start[1], 0.0)
        self.assertGreater(end[0], 16 * 0.28)
        self.assertEqual([(k, n) for k, _p, n in cuts], [(0, (0.0, -1.0)), (1, (1.0, 0.0)), (1, (0.0, 1.0))])
        self.assertAlmostEqual(cuts[1][1][0], 16 * 0.28)

    def test_made(self):
        """A stair of 3 m, 1 m wide, chequered plate, UPN 200: an IfcStair (STRAIGHT_RUN_STAIR, 17 risers, 16 treads)
        and two stringers — steel pieces of UPN 200, their webs' inner faces at the stair's sides (±0,50 m) and their
        flanges out, standing on the floor (z 0) up to the floor above (z 3) and the last riser's line (4,48 m) —, of
        two marks (left- and right-handed); the file valid; deleting the stair takes its stringers; one undo brings all
        back."""
        import numpy as np
        import ifcopenshell.util.element as ue
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        stair, stringers = bim.add_steel_stair(doc, (0.0, 0.0, 0.0), (1.0, 0.0), 3.0, 1.0, 0.28, "UPN200", "chapa")
        e = doc.ifc.by_guid(stair)
        self.assertEqual(e.PredefinedType, "STRAIGHT_RUN_STAIR")
        common = ue.get_psets(e)["Pset_StairCommon"]
        self.assertEqual((common["NumberOfRiser"], common["NumberOfTreads"]), (17, 16))
        self.assertEqual(len(stringers), 2)
        for g, sign in zip(stringers, (1.0, -1.0)):
            self.assertEqual(doc.ifc.steel_section(g), "UPN200")
            v = doc.get(g).mesh.verts
            np.testing.assert_allclose((v[:, 2].min(), v[:, 2].max(), v[:, 0].max()), (0.0, 3.0, 4.48), atol=1e-6)
            y = v[:, 1] * sign
            self.assertAlmostEqual(float(y.min()), 0.5, places=6)
            self.assertTrue((np.abs(y - 0.5085) < 0.0006).any())             # (the web's back at the inner side)
        marks, _pieces = doc.ifc.steel_marks()
        self.assertEqual(len({marks[g] for g in stringers}), 2)
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        bim.delete(doc, [stair])
        self.assertTrue(all(doc.ifc.by_guid(g) is None for g in [stair] + stringers))
        doc.undo()
        self.assertTrue(all(doc.ifc.by_guid(g) is not None for g in [stair] + stringers))


class ErectionPlan(unittest.TestCase):
    """(0.510) The erection plan."""

    def test_plan(self):
        """None for a model without steel; a shed's: its pieces seen from above (lines), the grid if there is one, a
        mark beside each piece (the columns' P1 four times, the rafters' V1, the purlins' M1, the braces'), none for the
        plates; at 1:100 on a sheet."""
        from arqbim.ifc import catalog
        from arqbim.model import bim, drawings, sheets
        from arqbim.model.document import Document
        doc = Document()
        self.assertIsNone(drawings.of_view(doc, "steel_erection", "", "Montagem"))
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"])
        drawing = drawings.of_view(doc, "steel_erection", "", "Planta de montagem")
        self.assertGreater(len(drawing.lines), 50)
        texts = [a[3] for a in drawing.annotations if a[0] == "text"]
        self.assertEqual(texts.count("P1"), 4)
        self.assertEqual(texts.count("V1"), 4)
        self.assertEqual(texts.count("M1"), 10)
        self.assertTrue(any(s.startswith("CV") for s in texts))
        self.assertFalse(any(s.startswith("Ch") for s in texts))
        self.assertTrue(drawing.north)
        self.assertEqual(sheets.USUAL_SCALES["steel_erection"], 100)
        self.assertIn("steel_erection", sheets.KINDS)


class MemberHoles(unittest.TestCase):
    """(0.512) The holes the connections' bolts make in the pieces."""

    def test_holes(self):
        """A shed: each purlin (C 160) has the 2 holes Ø14 of each cleat in its web — at 150 mm from its start (it goes
        15 cm past the end frame) and 25 / 85 mm up —, each wall brace those of its gussets (Ø18, 35 and 95 mm from
        its end), the columns and rafters none (welded); the purlins all one mark still; the NC1 of M1 with its 4 holes
        on face v; a piece turned end for end: the same holes' signature."""
        from arqbim.core import dstv, steel_marks
        from arqbim.ifc import catalog
        from arqbim.model import bim, steel_fabrication
        from arqbim.model.document import Document
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"])
        marks, pieces = doc.ifc.steel_marks()
        by = {}
        for p in pieces:
            by.setdefault(marks[p["guid"]], []).append(p["guid"])
        self.assertEqual(len(by["M1"]), 10)
        purlin = [(f, x, y, d) for f, x, y, d, _w in doc.ifc.member_holes(by["M1"][0])]
        self.assertEqual(purlin, [("v", 150.0, 25.0, 14.0), ("v", 150.0, 85.0, 14.0), ("v", 6150.0, 25.0, 14.0),
                                  ("v", 6150.0, 85.0, 14.0)])
        brace = doc.ifc.member_holes(by["CV1"][0])
        self.assertEqual([(f, x, d) for f, x, _y, d, _w in brace][:2], [("v", 35.0, 18.0), ("v", 95.0, 18.0)])
        self.assertEqual(doc.ifc.member_holes(by["P1"][0]), [])
        self.assertEqual(doc.ifc.member_holes(by["V1"][0]), [])
        nc1 = dstv.parse(steel_fabrication.nc1_files(doc)["M1"])
        self.assertEqual(nc1["BO"], [("v", 150.0, 25.0, 14.0), ("v", 150.0, 85.0, 14.0), ("v", 6150.0, 25.0, 14.0),
                                     ("v", 6150.0, 85.0, 14.0)])
        turned = [("v", 6300.0 - x, y, d) for f, x, y, d in purlin]
        self.assertEqual(steel_marks.holes_signature(purlin, 6300.0, 60.0),
                         steel_marks.holes_signature(turned, 6300.0, 60.0))


class KneePlate(unittest.TestCase):
    """(0.513) A mitre bolted."""

    def _shed(self, **options):
        from arqbim.ifc import catalog
        from arqbim.model import bim
        from arqbim.model.document import Document
        doc = Document()
        made = bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.0, catalog.BY_KEY["pilar_heb200"],
                              catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"],
                              catalog.BY_KEY["contrav_l80"], **options)
        return doc, made

    def test_knee_and_ridge(self):
        """A frame's knee (HEB 200 / IPE 300) and ridge bolted: each piece held back 20 mm from the mitre's plane, a
        plate 20 mm on each side of it (at the knee as wide as the HEB — 200 — and as deep as both cut sections),
        6 M20 through both, 2 welds; no warnings; the pieces get no holes from it (welded to the plates); the file
        valid; undone: the plain mitre back."""
        import numpy as np
        from arqbim.model import bim
        doc, made = self._shed(plates=False)
        column, rafter, rafter2 = made[:3]
        for a, b in ((column, rafter), (rafter, rafter2)):
            g = bim.knee_plates(doc, a, b)
            self.assertIsNotNone(g)
            self.assertIsNone(bim.knee_plates(doc, a, b))                    # (one there already)
            self.assertEqual(doc.ifc.connection_warnings(g), [])
            parts = doc.ifc.connection_parts(doc.ifc.connection_of(g))
            self.assertEqual(sum(1 for p in parts if p.is_a("IfcPlate")), 2)
            self.assertEqual(sum(1 for p in parts if p.is_a("IfcMechanicalFastener")), 6)
            self.assertEqual(sum(1 for p in parts if p.is_a("IfcFastener")), 2)
            _ka, _kb, joint, normal = doc.ifc.mitre_plane(a, b)[:4]
            for guid, sign in ((a, 1.0), (b, -1.0)):
                v = doc.get(guid).mesh.verts
                self.assertAlmostEqual(float(((v - joint) @ normal * sign).max()), -0.020, places=6)
                self.assertEqual(doc.ifc.member_holes(guid), [])
        knee = next(p for p in doc.ifc.connection_parts(doc.ifc.connections_on([column])[0]) if p.is_a("IfcPlate"))
        self.assertTrue(knee.Name.startswith("Chapa de topo 200×"))
        self.assertEqual(doc.ifc.validate(express_rules=True), [])
        doc.undo()
        doc.undo()
        _ka, _kb, joint, normal = doc.ifc.mitre_plane(column, rafter)[:4]
        v = doc.get(column).mesh.verts
        self.assertAlmostEqual(float(((v - joint) @ normal).max()), 0.0, places=6)

    def test_shed_bolted(self):
        """A shed with «Joelhos: aparafusados»: its 2 frames' 3 mitres each bolted (6), in one undo step."""
        doc, made = self._shed(knees="bolted")
        knees = [a for a in doc.ifc.file.by_type("IfcElementAssembly")
                 if doc.ifc.kind_of(a.GlobalId) == "steel_connection"
                 and doc.ifc.connection_params(a.GlobalId)[0] == "knee_plate"]
        self.assertEqual(len(knees), 6)
        doc.undo()
        self.assertTrue(all(doc.ifc.by_guid(g) is None for g in made))


class Erection(unittest.TestCase):
    """(0.514) The erection list."""

    def test_rows(self):
        """A shed: an assembly a piece (26: 4 columns, 4 rafters, 8 braces, 10 purlins), in the order they go up —
        the columns first (phase 1), then the rafters, the braces, the purlins; a column with its base plate and its 2
        gussets welded to it (Ch1, Ch2), heavier than the column alone by them; a rafter with its 5 cleats; the
        centres of gravity inside the shed; all the plates in some assembly: the total weight that of the bill of
        materials."""
        from arqbim.ifc import catalog
        from arqbim.model import bim, schedules
        from arqbim.model.document import Document
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"])
        rows = schedules.rows(doc, "erection")
        self.assertEqual(len(rows), 26)
        self.assertEqual([r["order"] for r in rows], list(range(1, 27)))
        self.assertEqual([r["phase_n"] for r in rows], sorted(r["phase_n"] for r in rows))
        self.assertEqual([r["mark"] for r in rows[:4]], ["P1"] * 4)
        self.assertEqual(rows[0]["parts"], "Ch1, Ch2")
        self.assertEqual(rows[0]["parts_n"], 3)
        rafter = next(r for r in rows if r["mark"] == "V1")
        self.assertEqual((rafter["parts"], rafter["parts_n"]), ("Ch3", 5))
        steel = {r["mark"]: r for r in schedules.rows(doc, "steel")}
        column_alone = steel["P1"]["weight"] / 4
        self.assertGreater(rows[0]["weight"], column_alone + 20.0)
        total = sum(r["weight"] for r in rows)
        self.assertAlmostEqual(total, sum(r["weight"] for r in steel.values()), delta=total * 0.002)
        for r in rows:
            x, y, z = (float(c.replace(",", ".")) for c in r["cog"].split("; "))
            self.assertTrue(-0.5 <= x <= 6.5 and -0.5 <= y <= 12.5 and 0.0 <= z <= 7.5, r["cog"])
        self.assertEqual(schedules.counts(doc)["erection"], 26)


class AssemblyDrawing(unittest.TestCase):
    """(0.515) The assemblies' drawing, with the welds."""

    def test_drawing(self):
        """A shed: an assembly line each — «Conjunto P1 — 4 un.» (a column with its base plate and gussets), «Conjunto
        V1» (a rafter with its cleats) —, the welds' throats by their symbols (a6 the base plate's, a5 the gussets', a4
        the cleats'), its view at 1:50; none for a model whose pieces have no plates welded to them."""
        from arqbim.ifc import catalog
        from arqbim.model import bim, drawings, sheets
        from arqbim.model.document import Document
        doc = Document()
        bim.steel_truss(doc, (0.0, 0.0, 0.0), (6.0, 0.0, 0.0), catalog.BY_KEY["pilar_shs150"],
                        catalog.BY_KEY["contrav_chs76"])
        self.assertIsNone(drawings.of_view(doc, "steel_assemblies", "", "Conjuntos"))
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"])
        drawing = drawings.of_view(doc, "steel_assemblies", "", "Conjuntos de aço")
        texts = [a[3] for a in drawing.annotations if a[0] == "text"]
        self.assertTrue(any(s.startswith("Conjunto P1 — 4 un.") for s in texts), texts)
        self.assertTrue(any(s.startswith("Conjunto V1") for s in texts))
        self.assertTrue({"a6", "a5", "a4"} <= set(texts))
        self.assertGreater(len(drawing.lines), 40)
        self.assertEqual(sheets.USUAL_SCALES["steel_assemblies"], 50)


class Eurocode3(unittest.TestCase):
    """(0.516) The steel checked by Eurocode 3."""

    def test_check(self):
        """By hand: an IPE 300 S275 (class 1, Wpl 628 cm³: Mc,Rd 172,7 kN·m) bent by 86,35 kN·m uses 50 %; an HEB 200
        S275 6 m tall (curve c about z, λ̄z 1,36, χ 0,363, Nb,Rd ≈ 780 kN) pressed by 390 kN about 50 % by
        buckling; a class 1 HEB 200; tension only on an angle: its area."""
        from arqbim.core import ec3
        bent = ec3.check("IPE300", "S275", 0.0, 86.35, 0.0, 0.0, 0.0, 6.0, 6.0, llt=1.0)    # (held every 1 m)
        self.assertEqual(bent["check"], "M")
        self.assertAlmostEqual(bent["util"], 0.5, delta=0.01)
        column = ec3.check("HEB200", "S275", -390.0, 0.0, 0.0, 0.0, 0.0, 6.0, 6.0)
        self.assertEqual(column["check"], "Nb")
        self.assertAlmostEqual(column["util"], 0.5, delta=0.02)
        self.assertEqual(column["class"], 1)
        tie = ec3.check("L80x8", "S275", 100.0, 0.0, 0.0, 0.0, 0.0, 8.0, 8.0)
        self.assertEqual(tie["check"], "N")
        self.assertAlmostEqual(tie["util"], 100.0 / (12.3 * 100 * 275 / 1000.0), delta=0.01)

    def test_lateral_torsional(self):
        """(0.519) By hand: an HEB 200 over 6 m between restraints — Mcr = π² E Iz / L² √(Iw/Iz + L² G It / π² E Iz) ≈
        258 kN·m, λ̄LT ≈ 0,83 (Mpl 176,7 kN·m), curve b, χLT ≈ 0,80 —: bent by 100 kN·m it uses ≈ 70 % (LT governing,
        not the 57 % of its section); restrained every 1,5 m, it is the section's; a tube is not prone to it."""
        from arqbim.core import ec3, steel
        self.assertAlmostEqual(ec3.m_cr(steel.get("HEB200"), 6.0) / 1e6, 258.0, delta=258.0 * 0.03)
        chi, lam = ec3.chi_lt(steel.get("HEB200"), 642.5e3, 275.0, 6.0)
        self.assertAlmostEqual(lam, 0.83, delta=0.02)
        self.assertAlmostEqual(chi, 0.80, delta=0.02)
        long = ec3.check("HEB200", "S275", 0.0, 100.0, 0.0, 0.0, 0.0, 6.0, 6.0)
        self.assertEqual(long["check"], "LT")
        self.assertAlmostEqual(long["util"], 100.0 / (chi * 176.7), delta=0.02)
        short = ec3.check("HEB200", "S275", 0.0, 100.0, 0.0, 0.0, 0.0, 6.0, 6.0, llt=1.5)
        self.assertEqual(short["check"], "M")
        self.assertEqual(ec3.chi_lt(steel.get("SHS150x150x8"), 1e5, 355.0, 6.0), (1.0, 0.0))

    def test_shed(self):
        """A 12 m × 12 m shed analysed: no mechanism; a row a piece (34); the frames' columns and rafters well within
        (between 10 and 80 %), the purlins nearly full (C 160 over 6 m), the braces in tension only (a few %); its table
        sorted by use, with its notes under."""
        from arqbim.ifc import catalog
        from arqbim.model import bim, schedules, steel_analysis
        from arqbim.model.document import Document
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 12.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"])
        found = steel_analysis.analyse(doc)
        self.assertEqual(found.error, "")
        by = {}
        for r in found.rows:
            by.setdefault(r["mark"], []).append(r)
        for mark in ("P1", "V1"):
            self.assertTrue(all(0.1 < r["utilisation"] < 0.8 for r in by[mark]), mark)
        purlins = [r["utilisation"] for r in by["M1"]]
        self.assertTrue(0.6 < max(purlins) < 1.2 and min(purlins) > 0.2, purlins)    # (the edge ones: half a strip)
        for mark in ("CV1", "CV2"):
            self.assertTrue(all(r["utilisation"] < 0.2 and "tension_only" in r["notes"] for r in by[mark]))
        rows = schedules.rows(doc, "steel_check")
        self.assertEqual(len(rows), len(found.rows) + 1)
        values = [r["utilisation"] for r in rows if r["utilisation"] is not None]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertIsNone(rows[-1]["guid"])


class SteelWind(unittest.TestCase):
    """(0.518) The wind on the steel structure."""

    def test_wind(self):
        """A 12 m shed (ridge 7,06 m): the peak pressure at its height (zone A, terrain III — the project's actions),
        4 wind cases and their combinations (each leading, with the other's ψ0, and lifting against 1,0 G); the walls'
        columns of the faces across the wind loaded — the gables' corner columns bent about their weak axis, more
        used than with the gravity alone —; the wall braces working (in tension); no «wind» note left."""
        from arqbim.core import actions
        from arqbim.ifc import catalog
        from arqbim.model import bim, steel_analysis
        from arqbim.model.document import Document
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 12.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"])
        settings = doc.ifc.structural_settings()
        found = steel_analysis.analyse(doc, settings)
        ridge = 6.0 + 6.0 * __import__("math").tan(__import__("math").radians(10.0))
        self.assertAlmostEqual(found.loads["wind"], actions.peak_pressure(ridge, settings.wind_zone,
                                                                          settings.terrain), places=3)
        uls, sls = steel_analysis.combinations(settings, ["W1", "W2", "W3", "W4"])
        self.assertEqual((len(uls), len(sls)), (3 + 4 * 3, 1 + 4))
        self.assertNotIn("wind", found.notes)
        columns = [r for r in found.rows if r["mark"] == "P1"]
        self.assertGreater(max(r["utilisation"] for r in columns), 0.4)              # (the wind on the gables)
        braces = [r for r in found.rows if r["mark"] in ("CV1", "CV2")]
        self.assertTrue(any(r["n_ed"] > 10.0 for r in braces))


class Ec3Joints(unittest.TestCase):
    """(0.520) The connections checked by EN 1993-1-8."""

    def test_resistances(self):
        """By hand (class 8.8, γM2 1,25): an M20 (As 245 mm²) in shear 94,1 kN, in tension 141,1 kN; bearing on 10 mm of
        S275 with e1 = 40, d0 = 22 (αb 0,606): 52,1 kN; a fillet weld a = 5 in S275: 1,168 kN/mm; shear with tension:
        Fv/Fv,Rd + Ft/1,4 Ft,Rd."""
        from arqbim.core import ec3_joints as j
        self.assertAlmostEqual(j.shear_rd(20), 94.08, places=1)
        self.assertAlmostEqual(j.tension_rd(20), 141.12, places=1)
        self.assertAlmostEqual(j.bearing_rd(20, 22, 10, "S275", 40), 2.5 * (40 / 66) * 430 * 20 * 10 / 1.25 / 1000,
                               places=2)
        self.assertAlmostEqual(j.weld_rd(5, "S275"), 430 / (3 ** 0.5 * 0.85 * 1.25) * 5 / 1000, places=4)
        both = j.check_bolts(20, 22, 20, "S275", 50, 40.0, 70.0)
        self.assertAlmostEqual(both["ratios"]["FvFt"], 40 / 94.08 + 70 / (1.4 * 141.12), places=3)

    def test_shed(self):
        """A 12 m shed with bolted knees: every connection checked (base plates, gussets, cleats, knees); the knees'
        outer bolts in tension the most used, the cleats by bearing on the purlins' thin web, the gussets lightly; all
        within; its table with its notes under."""
        from arqbim.ifc import catalog
        from arqbim.model import bim, schedules, steel_analysis, steel_connection_check
        from arqbim.model.document import Document
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 12.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"],
                       knees="bolted")
        rows = steel_connection_check.check(doc, steel_analysis.analyse(doc))
        kinds = {r["kind"] for r in rows}
        self.assertEqual(kinds, {"base_plate", "gusset", "purlin_cleat", "knee_plate"})
        self.assertEqual(len(rows), schedules.counts(doc)["steel_joints"])
        worst = {k: max(r["utilisation"] for r in rows if r["kind"] == k) for k in kinds}
        self.assertTrue(all(0.0 < u <= 1.0 for u in worst.values()), worst)
        self.assertEqual(max(worst, key=worst.get), "knee_plate")
        self.assertTrue(all(r["governing"] == "Fb" for r in rows if r["kind"] == "purlin_cleat"))
        table = schedules.rows(doc, "steel_joints")
        self.assertEqual(len(table), len(rows) + 1)
        self.assertIsNone(table[-1]["guid"])


class SteelReport(unittest.TestCase):
    """(0.521) The steel structure's calculation report."""

    def test_page(self):
        """A 12 m shed's report: one page, its 8 sections — the project, the codes and S275's strengths, the actions
        (the wind's qp written), the model (its pieces, bars, links, supports), each piece's check, each connection's,
        the bill of materials with its total —, who signs; the same numbers as the tables."""
        from arqbim.ifc import catalog
        from arqbim.model import bim, steel_report
        from arqbim.model.document import Document
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 12.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"])
        data = steel_report.report_data(doc)
        page = steel_report.report_html(data)
        self.assertTrue(page.startswith("<!doctype html>"))
        for k in range(1, 9):
            self.assertIn("<h2>{}. ".format(k), page)
        self.assertIn("Aço S275", page)
        self.assertIn("qp = {} kN/m²".format("{:.2f}".format(data["analysis"].loads["wind"]).replace(".", ",")), page)
        self.assertIn("HEB 200", page)
        self.assertIn("Chapa de base", page)
        self.assertIn("assina", page)
        statuses = page.count("<td class='ok'>") + page.count("<td class='falha'>")
        self.assertEqual(statuses, len(data["analysis"].rows) + len(data["joints"]))      # (a piece, a connection)


class Ec3Colours(unittest.TestCase):
    """(0.517) The Graphic rules' «Utilização EC3»."""

    def test_bands(self):
        """The bands: to 50 % green, to 80 %, to 100 %, past it red; a 12 m shed's pieces each in one (the purlins
        high, the frames low), the other elements grey (no value); its legend in the bands' order."""
        from arqbim.ifc import catalog
        from arqbim.model import bim, graphic_rules, steel_analysis
        from arqbim.model.document import Document
        self.assertEqual([graphic_rules.ec3_band(u) for u in (0.2, 0.5, 0.7, 0.95, 1.0, 1.3)],
                         ["low", "low", "mid", "high", "high", "over"])
        self.assertIn(graphic_rules.EC3, graphic_rules.RULES)
        doc = Document()
        bim.steel_shed(doc, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 12.0, catalog.BY_KEY["pilar_heb200"],
                       catalog.BY_KEY["viga_ipe300"], catalog.BY_KEY["madre_c160"], catalog.BY_KEY["contrav_l80"])
        ids = [o.id for o in doc.objects.values() if o.is_bim]
        values = steel_analysis.bands(doc, ids)
        self.assertEqual(set(values), set(ids))
        columns = [g for g in ids if doc.ifc.kind_of(g) == "steel_member" and doc.ifc.by_guid(g).is_a("IfcColumn")]
        self.assertTrue(all(values[g] in ("low", "mid") for g in columns))        # (0.518: the corners in the wind)
        self.assertIn("low", [values[g] for g in columns])
        plates = [g for g in ids if doc.ifc.by_guid(g).is_a("IfcPlate")]
        self.assertTrue(all(values[g] is None for g in plates))
        lines = graphic_rules.legend(values, graphic_rules.EC3)
        order = [label for label, _c, _g in lines]
        self.assertEqual(order[0], "até 50 %")
        self.assertEqual(lines[0][1], "#59a14f")
        self.assertEqual(doc.ifc.property_values(ids[:3], graphic_rules.EC3), {g: None for g in ids[:3]})


def dataclasses_replace(spec, **fields):
    import dataclasses
    return dataclasses.replace(spec, **fields)


if __name__ == "__main__":
    unittest.main()
