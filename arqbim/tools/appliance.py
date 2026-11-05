"""Appliance (0.171, Phase 10, step 1): a hob (electric or gas) or a sink set in the worktop, an oven, a dishwasher, a
washing machine, a fridge, a microwave, a hood — its back against the wall's face under the mouse, at its usual
height; a hob in a worktop cuts it."""

from ..core import appliances as core_app
from ..i18n import t
from ..ifc.sanitary import fixture_frame
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, show_snap
from .bim_draw import ANGLES
from .sanitary import SanitaryTool


class ApplianceTool(SanitaryTool):
    name = "appliance"
    keys_help = "keys.appliance"

    def __init__(self, host):
        super().__init__(host)
        self.kind = "hob"

    def options(self):
        return [Option("kind", t("ctx.appliance"), "choice", self.kind,
                       tuple((k, t("appliance." + k)) for k in core_app.APPLIANCES if k not in core_app.HOUSED)),
                Option("angle", t("ctx.angle"), "choice", self.angle, tuple((a, "{}°".format(a)) for a in ANGLES))]

    def set_option(self, key, value):
        if key == "kind" and value in core_app.APPLIANCES and value not in core_app.HOUSED:
            self.kind = value
        elif key == "angle":
            self.angle = int(value)
        self._again()

    def hint(self):
        return t("hint.appliance", k=t("appliance." + self.kind).lower())

    def _width(self):
        return core_app.size(self.kind)[0]

    def _show(self, x, y, modifiers):
        back, angle, _wall, snap = self._place(x, y, modifiers)
        if back is None:
            return
        w, d, _h = core_app.size(self.kind)
        m = fixture_frame(back, angle)
        foot = [m[:3, 3] + m[:3, 0] * u + m[:3, 1] * v for u, v in ((-w / 2, 0.0), (w / 2, 0.0), (w / 2, d), (-w / 2, d))]
        segs = [q for a, b in zip(foot, foot[1:] + foot[:1]) for q in (a, b)]
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
        bim.add_appliance(self.doc, back, self.kind, angle)
        self.viewport.clear_overlays()
        self.host.message(t("info.appliance_wall" if wall else "info.appliance", k=t("appliance." + self.kind)))
