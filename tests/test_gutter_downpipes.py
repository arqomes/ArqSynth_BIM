"""0.438 — A gutter's half-round section and its downpipes."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import Document  # noqa: E402


class GutterDownpipes(unittest.TestCase):
    """A roof over four walls, 3 m up: a half-round gutter along its longest eave with downpipes at both ends — its
    section round (no flat bottom), its two downpipes down to the ground (round, 8 cm, under the gutter); made a box
    again with a downpipe at its end only: one; none: none; the gutter deleted: its downpipes with it; valid IFC."""

    def test_gutter(self):
        doc = Document()
        spec = catalog.BY_KEY["parede_alv_20"]
        for a, b in (((0, 0), (10, 0)), ((10, 0), (10, 6)), ((10, 6), (0, 6)), ((0, 6), (0, 0))):
            bim.add_wall(doc, np.array(a + (0.0,), dtype=float), np.array(b + (0.0,), dtype=float), spec, height=3.0)
        roof = bim.add_roof(doc, [(-0.1, -0.1), (10.1, -0.1), (10.1, 6.1), (-0.1, 6.1)], catalog.BY_KEY.get(
            "cobertura_telha", next(s for s in catalog.types() if s.kind == "roof")))
        eaves = bim.roof_eaves(doc, roof)
        a, b, out = max(eaves, key=lambda e: float(np.linalg.norm(e[1] - e[0])))
        gutter = bim.add_gutter(doc, a, b, out, shape="meia_cana", downpipes="ambos")
        ifc = doc.ifc
        self.assertEqual(ifc.gutter_shape(gutter), "meia_cana")
        self.assertEqual(ifc.gutter_downpipes(gutter), "ambos")
        pipes = ifc.downpipes_of(gutter)
        self.assertEqual(len(pipes), 2)
        for _end, pipe in pipes:
            v = doc.get(pipe.GlobalId).mesh.verts
            lo, hi = v.min(axis=0), v.max(axis=0)
            self.assertAlmostEqual(lo[2], 0.0, places=4)                   # (down to the ground)
            self.assertAlmostEqual(hi[0] - lo[0], 0.08, places=3)
            self.assertGreater(hi[2], 2.5)
            self.assertEqual(pipe.PredefinedType, "RIGIDSEGMENT")
        gv = doc.get(gutter).mesh.verts
        low = gv[:, 2].min()
        self.assertLess(int(np.sum(np.abs(gv[:, 2] - low) < 1e-6)), 4)      # (a half-round: no flat bottom)
        self.assertEqual(ifc.validate(express_rules=True), [])
        bim.set_gutter(doc, gutter, shape="caixa", downpipes="fim")
        self.assertEqual((ifc.gutter_shape(gutter), ifc.gutter_downpipes(gutter)), ("caixa", "fim"))
        self.assertEqual(len(ifc.downpipes_of(gutter)), 1)
        doc.undo()
        self.assertEqual(len(ifc.downpipes_of(gutter)), 2)
        doc.redo()
        bim.set_gutter(doc, gutter, downpipes="nenhum")
        self.assertEqual(ifc.downpipes_of(gutter), [])
        bim.set_gutter(doc, gutter, downpipes="inicio")
        bim.delete(doc, [gutter])
        self.assertEqual([e for e in ifc.file.by_type("IfcFlowSegment") if ifc._params(e).get("Elemento") == "downpipe"],
                         [])
        self.assertEqual(ifc.validate(express_rules=True), [])


if __name__ == "__main__":
    unittest.main()
