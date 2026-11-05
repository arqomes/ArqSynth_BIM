"""Room (0.99), as Revit's: a click inside walls makes a room there — the space between the walls and columns
of the active storey that holds the point (IfcSpace), with the next number; under the mouse, the room it would
be is shown first. It follows its walls afterwards. In a plan (or the 3D view, on the active storey's level)."""

import numpy as np

from ..core.sketch_geometry import ray_plane
from ..i18n import decimal_sep, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Tool


class RoomTool(Tool):
    name = "room"
    placement = True                  # (Esc: back to Select)
    keys_help = "keys.room"

    def __init__(self, host):
        super().__init__(host)
        self._shown = None            # (the point, the region shown under the mouse)

    def hint(self):
        return t("hint.room")

    def _point(self, x, y):
        z = self.doc.work_level()
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), np.array((0.0, 0.0, 1.0)))
        if p is None:
            p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), np.array((0.0, 0.0, -1.0)))
        return p

    def pointer_move(self, x, y, modifiers):
        p = self._point(x, y)
        if p is None:
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
        self.viewport.show_label("{:.2f} m²".format(region.area).replace(".", decimal_sep()), p)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        p = self._point(x, y)
        if p is None:
            return
        guid = bim.add_room(self.doc, (float(p[0]), float(p[1])))
        self.viewport.clear_overlays()
        if guid is None:
            self.host.message(t("err.room_open"), warning=True)
            return
        info = self.doc.ifc.space_info(guid)
        self.host.message(t("info.room", name=info["name"], n=info["number"],
                            a="{:.2f}".format(info["area"]).replace(".", decimal_sep())))

    def cancel(self):
        self.viewport.clear_overlays()
