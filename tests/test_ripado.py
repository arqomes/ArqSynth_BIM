"""0.434 — The «Ripado» as a command of its own (the addon's): slats with a frame round them and battens behind."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

import ifcopenshell.util.element as ue  # noqa: E402
from shapely.geometry import box  # noqa: E402

from arqbim.core import surfaces  # noqa: E402
from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import Document  # noqa: E402


class RipadoParts(unittest.TestCase):
    """A 1,40 × 2,40 face: a 5 cm frame round it, its inside 1,30 × 2,30; three battens across upright slats, in equal
    bands of the inside; slats 4 cm at 8 cm centred inside the frame; a frame too wide refused."""

    def test_parts(self):
        d = dict(surfaces.DEFAULTS["ripado"], width=0.04, gap=0.04, frame=0.05, battens=3)
        band, battens, slats, inner = surfaces.ripado_parts(box(0.0, 0.0, 1.4, 2.4), d)
        self.assertAlmostEqual(inner.area, 1.3 * 2.3)
        self.assertAlmostEqual(band.area, 1.4 * 2.4 - 1.3 * 2.3)
        self.assertEqual(len(battens), 3)
        centres = sorted(round((q.bounds[1] + q.bounds[3]) / 2, 4) for q in battens)
        self.assertEqual(centres, [round(0.05 + (k + 0.5) * 2.3 / 3, 4) for k in range(3)])
        self.assertEqual(len(slats), 16)                     # (1,30 m: 1 + floor((1,30 − 0,04) / 0,08) = 16)
        left = min(u0 for u0, _v0, _u1, _v1 in slats)
        right = max(u1 for _u0, _v0, u1, _v1 in slats)
        self.assertAlmostEqual(left - 0.05, 1.35 - right, places=6)          # (centred)
        self.assertTrue(all(abs(v0 - 0.05) < 1e-6 and abs(v1 - 2.35) < 1e-6 for _u0, v0, _u1, v1 in slats))
        level = dict(d, direction="horizontal")
        _band, battens, slats, _inner = surfaces.ripado_parts(box(0.0, 0.0, 1.4, 2.4), level)
        self.assertTrue(all(q.bounds[3] - q.bounds[1] > 2.0 for q in battens))     # (upright battens)
        with self.assertRaises(ValueError):
            surfaces.ripado_parts(box(0.0, 0.0, 1.4, 2.4), dict(d, frame=0.70))


class RipadoOnWall(unittest.TestCase):
    """On a 4 m wall with a door: a slatted panel (1 to 3 m along, 0,3 to 2,4 m up) with a frame and two battens —
    its pieces (battens on the wall, slats over them, the frame as deep as both), its thickness in its quantities, its
    name «Ripado»; battens taken off: its slats on the wall again (as before 0.434); the frame refused too wide; the
    cut list has its slats, battens and frame; the IFC valid."""

    def test_on_wall(self):
        doc = Document()
        wall = bim.add_wall(doc, np.array((0.0, 0.0, 0.0)), np.array((4.0, 0.0, 0.0)), catalog.BY_KEY["parede_alv_20"])
        pattern = {"direction": "vertical", "width": 0.04, "gap": 0.04, "thickness": 0.03, "frame": 0.05,
                   "battens": 2, "batten_w": 0.05, "batten_d": 0.025}
        panel = bim.add_cladding(doc, wall, 1, "ripado", 2.4, pattern, {"start": 1.0, "end": 3.0, "base": 0.3})
        e = doc.ifc.by_guid(panel)
        self.assertTrue(e.Name.startswith("Ripado"))
        d = doc.ifc.pattern_params(panel)
        self.assertEqual((d["batten_count"], round(d["thickness"], 3), round(d["frame"], 3)), (2, 0.03, 0.05))
        items = [r for r in e.Representation.Representations if r.RepresentationIdentifier == "Body"][0].Items
        self.assertEqual(len(items), d["count"] + 2 + 1)     # (its slats, its two battens, its frame band)
        depths = sorted({round(i.Depth * doc.ifc.unit_scale, 4) for i in items})
        self.assertEqual(depths, [0.025, 0.03, 0.055])
        q = ue.get_psets(e)["Qto_CoveringBaseQuantities"]
        self.assertAlmostEqual(q["Width"] * doc.ifc.unit_scale, 0.055)
        lo = doc.get(panel).mesh.verts.min(axis=0)
        hi = doc.get(panel).mesh.verts.max(axis=0)
        frame = doc.ifc.element_frame(wall)
        self.assertAlmostEqual(hi[1] - frame.y1, 0.055, places=5)           # (out of the wall: battens + slats)
        self.assertAlmostEqual(lo[0], 1.0, places=5)
        self.assertAlmostEqual(hi[0], 3.0, places=5)
        self.assertEqual(doc.ifc.validate(), [])
        rows, _hw, _areas = bim.cut_list(doc)
        roles = {r[0] for r in rows}
        self.assertTrue({"slat", "batten", "ripado_frame"} <= roles)
        battens = [r for r in rows if r[0] == "batten"]
        self.assertEqual(sum(r[5] for r in battens), 2)
        self.assertAlmostEqual(battens[0][2], 1.9, places=3)               # (across the inside: 2,0 − 2 × 0,05)
        # battens taken off, no frame: the slats alone on the wall, as before
        bim.set_cladding(doc, panel, battens=0, frame=0.0)
        d = doc.ifc.pattern_params(panel)
        e = doc.ifc.by_guid(panel)
        items = [r for r in e.Representation.Representations if r.RepresentationIdentifier == "Body"][0].Items
        self.assertEqual(len(items), d["count"])
        self.assertAlmostEqual(ue.get_psets(e)["Qto_CoveringBaseQuantities"]["Width"] * doc.ifc.unit_scale, 0.03)
        with self.assertRaises(ValueError):
            bim.set_cladding(doc, panel, frame=1.2)
        with self.assertRaises(ValueError):
            bim.set_cladding(doc, panel, battens=40)
        doc.undo()
        self.assertEqual(doc.ifc.pattern_params(panel)["batten_count"], 2)


if __name__ == "__main__":
    unittest.main()
