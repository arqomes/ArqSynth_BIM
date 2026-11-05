"""Electrical point (0.143, Phase 6, step 4): an outlet, a switch, a data outlet, the distribution board or a junction
box (IfcOutlet, IfcSwitchingDevice, IfcElectricDistributionBoard, IfcJunctionBox), its back against the wall's face
under the mouse, at its usual height (on the contextual bar), with its cable's port; on a plan, its symbol."""

import numpy as np

from ..core.units import format_length
from ..i18n import decimal_sep, t
from ..ifc.electrical import POINTS, point_symbol
from ..ifc.sanitary import fixture_frame
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, show_snap
from .bim_draw import ANGLES, length_option
from .sanitary import SanitaryTool


class ElectricalTool(SanitaryTool):
    name = "electrical"
    keys_help = "keys.electrical"

    def __init__(self, host):
        super().__init__(host)
        self.kind = "outlet"
        self.height = POINTS[self.kind][3]

    def options(self):
        return [Option("kind", t("ctx.electrical"), "choice", self.kind, tuple((k, t("point." + k)) for k in POINTS)),
                length_option("height", "ctx.point_height", self.height),
                Option("angle", t("ctx.angle"), "choice", self.angle, tuple((a, "{}°".format(a)) for a in ANGLES))]

    def set_option(self, key, value):
        if key == "kind" and value in POINTS:
            self.kind = value
            self.height = POINTS[value][3]               # (its usual height)
        elif key == "height" and value >= 0.0:
            self.height = float(value)
        elif key == "angle":
            self.angle = int(value)
        self._again()

    def hint(self):
        return t("hint.electrical", k=t("point." + self.kind).lower(), h=format_length(self.height, decimal_sep()))

    def _width(self):
        return POINTS[self.kind][2][0]

    def _show(self, x, y, modifiers):
        back, angle, _wall, snap = self._place(x, y, modifiers)
        if back is None:
            return
        w, d, _h = POINTS[self.kind][2]
        m = fixture_frame(back, angle)
        foot = [m[:3, 3] + m[:3, 0] * u + m[:3, 1] * v for u, v in ((-w / 2, 0.0), (w / 2, 0.0), (w / 2, d), (-w / 2, d))]
        try:
            mm = (self.doc.view_settings(self.viewport.current_view()).scale or 100) / 1000.0
        except Exception:
            mm = 0.1
        lines, solids = point_symbol(self.kind, back, angle, mm)
        segs = [q for a, b in zip(foot, foot[1:] + foot[:1]) for q in (a, b)]
        segs += [np.array((p[0], p[1], back[2])) for a, b in lines for p in (a, b)]
        for poly in solids:
            ring = [np.array((p[0], p[1], back[2])) for p in poly]
            segs += [q for a, b in zip(ring, ring[1:] + ring[:1]) for q in (a, b)]
        self.viewport.show_polygon(foot, segments=segs, colors=[PREVIEW] * len(segs))
        show_snap(self.viewport, snap, back)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        back, angle, wall, _snap = self._place(x, y, modifiers)
        if back is None:
            return
        bim.add_point(self.doc, back, self.kind, angle, self.height)
        self.viewport.clear_overlays()
        self.host.message(t("info.point_wall" if wall else "info.point", k=t("point." + self.kind),
                            h=format_length(self.height, decimal_sep())))
