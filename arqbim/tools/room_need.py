"""(0.475, the owner: «Para inserir uma área, pode selecionar e colocar no ambiente com clique, ou pegar e arrastar e
largar no ambiente») A line of the Programme panel clicked: this tool places it — a click inside walls makes that room
there (or names the room there), as Revit's «Place Room» with a room of its list; the room it would be is shown under
the mouse with its area against the one wanted (green: enough, orange: short). After it, the next line of the storey
still to place is taken, until Esc (back to Selecionar)."""

import numpy as np

from ..core.sketch_geometry import ray_plane
from ..i18n import decimal_sep, t
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Tool


def _m2(value):
    return "{:.2f} m²".format(value).replace(".", decimal_sep())


class RoomNeedTool(Tool):
    name = "room_need"
    title = "tool.room_need"
    placement = True                  # (Esc: back to Select)

    def __init__(self, host):
        super().__init__(host)
        self.need = None              # the programme line being placed (model/room_program.Need)

    def hint(self):
        if self.need is None:
            return t("hint.room_need_none")
        wanted = t("hint.room_need_area", a=_m2(self.need.area)) if self.need.area else ""
        return t("hint.room_need", name=self.need.name, area=wanted)

    def set_need(self, need):
        self.need = need
        self.host.set_hint(self.hint())

    def _point(self, x, y):
        z = self.doc.work_level()
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), np.array((0.0, 0.0, 1.0)))
        if p is None:
            p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), np.array((0.0, 0.0, -1.0)))
        return p

    def pointer_move(self, x, y, modifiers):
        p = self._point(x, y)
        if p is None or self.need is None:
            return
        region = self.doc.ifc.room_region(self.doc.active_storey, (float(p[0]), float(p[1])))
        if region is None:
            self.viewport.clear_overlays()
            self.viewport.show_label(t("err.room_open"), p)
            return
        z = self.doc.work_level() + 0.01
        ring = [np.array((cx, cy, z)) for cx, cy in list(region.exterior.coords)[:-1]]
        segs = [q for a, b in zip(ring, ring[1:] + ring[:1]) for q in (a, b)]
        self.viewport.show_polygon(ring, segments=segs, colors=[PREVIEW] * len(segs))
        text = "{} · {}".format(self.need.name, _m2(region.area))
        if self.need.area:
            text += "  " + (t("hint.room_need_enough") if region.area >= self.need.area - 0.005
                            else t("hint.room_need_short", a=_m2(self.need.area - region.area)))
        self.viewport.show_label(text, p)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT or self.need is None:
            return
        self.viewport.clear_overlays()
        self.host.place_room_need(self.need, x, y)

    def cancel(self):
        self.viewport.clear_overlays()
