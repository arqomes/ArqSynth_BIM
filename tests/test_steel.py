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
        v = doc.get(beam).mesh.verts
        np.testing.assert_allclose((v.min(axis=0), v.max(axis=0)), ((0.0, -0.075, 2.7), (5.0, 0.075, 3.0)), atol=1e-6)
        self.assertAlmostEqual(doc.get(beam).mesh.volume(), 5.0 * steel.properties("IPE300")["A"] * 1e-4, places=4)
        c = doc.get(column).mesh.verts
        np.testing.assert_allclose((c.min(axis=0), c.max(axis=0)), ((-0.1, -0.1, 0.0), (0.1, 0.1, 3.0)), atol=1e-6)
        e = doc.ifc.by_guid(beam)
        profile = ue.get_material(ue.get_type(e)).MaterialProfiles[0].Profile
        self.assertEqual((profile.is_a(), profile.ProfileName), ("IfcIShapeProfileDef", "IPE300"))
        self.assertAlmostEqual(ue.get_psets(e)["Qto_BeamBaseQuantities"]["NetWeight"], 5.0 * 42.2, places=6)
        shown = doc.ifc.describe(beam)["steel"]                         # (what the Properties show)
        self.assertEqual((shown[0], shown[1], shown[2]), ("IPE 300", "Aço estrutural S275", 42.2))
        self.assertAlmostEqual(shown[3], 211.0, places=6)
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


def dataclasses_replace(spec, **fields):
    import dataclasses
    return dataclasses.replace(spec, **fields)


if __name__ == "__main__":
    unittest.main()
