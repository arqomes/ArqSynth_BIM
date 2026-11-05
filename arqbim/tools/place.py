"""Place a component (Project panel ▸ Library ▸ a component ▸ Place another copy): its box
follows the mouse on the storey (inferences work as for walls), a click puts one more copy
there — its lowest corner at the point. Click again for more; Tab turns it 90°; Esc ends."""

import numpy as np

from ..i18n import t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, show_snap
from .bim_draw import _PointTool


class PlaceTool(_PointTool):
    name = "place"
    accepts_typing = False
    common_keys = frozenset(("r", "shift+r"))       # (0.86: as Tab, and back with Shift)
    placement = True
    keys_help = "keys.place"

    def __init__(self, host):
        super().__init__(host)
        self.type_guid = None
        self.type_name = ""
        self.size = np.zeros(3)
        self.angle = 0.0

    def use(self, type_guid):
        """The component to place (its box is shown under the mouse)."""
        self.type_guid = type_guid
        lo, hi = self.doc.ifc.component_box(type_guid)
        self.size = hi - lo                                            # (placed by its lowest corner)
        self.type_name = self.doc.ifc.by_guid(type_guid).Name or ""
        self.angle = 0.0

    def hint(self):
        return t("hint.place", name=self.type_name)

    def tab(self):
        return self.common_key("r")

    def common_key(self, name):
        self.angle = (self.angle + (90.0 if name == "r" else -90.0)) % 360.0     # a quarter turn
        if self._hover is not None:
            self._preview(*self._hover)
        self.host.message(t("info.turned", a=int(self.angle)))
        return True

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, self.doc.work_level())
        if p is None:
            return
        self._hover = (p, snap)
        self._preview(p, snap)

    def _preview(self, p, snap):
        a = np.radians(self.angle)
        rot = np.array(((np.cos(a), -np.sin(a), 0.0), (np.sin(a), np.cos(a), 0.0), (0.0, 0.0, 1.0)))
        sx, sy, sz = self.size
        corners = [rot @ np.array((x, y, z)) + p for z in (0.0, sz) for x, y in ((0, 0), (sx, 0), (sx, sy), (0, sy))]
        segs = []
        for ring in (corners[:4], corners[4:]):
            for i in range(4):
                segs += [ring[i], ring[(i + 1) % 4]]
        for i in range(4):
            segs += [corners[i], corners[i + 4]]
        self.viewport.show_lines(segs, [PREVIEW] * len(segs))
        show_snap(self.viewport, snap, p)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT or self.type_guid is None:
            return
        p, _snap = self._point(x, y, self.doc.work_level())
        if p is None:
            return
        guid = bim.place_component(self.doc, self.type_guid, p, self.doc.active_storey, self.angle)
        self.host.message(t("info.component_placed", name=self.type_name))
        self.viewport.set_selection({guid})

    def cancel(self):
        self.viewport.clear_overlays()
