"""Wall finish and Light (0.119).

Wall finish: over a wall, the face under the cursor is shown with the finish on it (from its base up to its
height, the contextual bar's: tiles to 2,10 m by default); a click puts it there (IfcCovering CLADDING, tied to
the wall: it follows it, cut round its doors and windows). In a plan the face is the one on the cursor's side.
Light: a click puts a light in the ceiling over the point (a 60 × 60 panel or a downlight, IfcLightFixture)."""

import numpy as np

from ..core.ceilings import FINISHES, LIGHTS
from ..core.openings import face_rectangle
from ..core.units import format_length
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, SNAP_COLORS, Option, Tool
from .bim_draw import length_option


def _fmt(v):
    return format_length(v, decimal_sep())


class WallFinishTool(Tool):
    name = "wall_finish"
    placement = True                     # (Esc: back to Select)
    keys_help = "keys.wall_finish"

    def __init__(self, host):
        super().__init__(host)
        self.finish = "azulejo"
        self.height = bim.WALL_FINISH_HEIGHT
        self._frames = {}

    def options(self):
        return [Option("finish", t("ctx.finish"), "choice", self.finish,
                       tuple((k, t("finish." + k)) for k in FINISHES)),
                length_option("height", "ctx.finish_height", self.height)]

    def set_option(self, key, value):
        if key == "finish" and value in FINISHES:
            self.finish = value
        elif key == "height" and value >= 0.1:
            self.height = float(value)
        self.host.set_hint(self.hint())

    def hint(self):
        return t("hint.wall_finish", f=t("finish." + self.finish).lower(), h=_fmt(self.height))

    def _frame(self, wall):
        obj = self.doc.get(wall)
        cached = self._frames.get(wall)
        if cached is None or cached[0] != id(obj.mesh):
            cached = (id(obj.mesh), bim.wall_frame(self.doc, wall))
            self._frames[wall] = cached
        return cached[1]

    def _face_at(self, x, y):
        """(wall, its frame, side) of the wall face under the cursor, or None."""
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None
        obj = self.doc.get(hit[0])
        if obj is not None and obj.is_bim and self.doc.ifc.kind_of(obj.id) == "cladding":
            p = self.doc.ifc._params(self.doc.ifc.by_guid(obj.id))     # (0.178) a finish: a layer over it
            frame = self._frame(p["Parede"]) if self.doc.get(p.get("Parede")) is not None else None
            return (p["Parede"], frame, 1 if int(p.get("Lado") or 1) > 0 else -1) if frame is not None else None
        if obj is None or not obj.is_bim or self.doc.ifc.kind_of(obj.id) != "wall":
            return None
        frame = self._frame(obj.id)
        if frame is None:
            return None
        side = frame.face_side(obj.mesh.face_normal(hit[1]))
        if side == 0 and self.viewport.plan:
            y_local = frame.to_local(hit[2])[1]
            side = -1 if y_local < (frame.y0 + frame.y1) / 2 else 1
        return (obj.id, frame, side) if side else None

    def pointer_move(self, x, y, modifiers):
        found = self._face_at(x, y)
        if found is None:
            self.viewport.clear_overlays()
            return
        _wall, frame, side = found
        ring = face_rectangle(frame, frame.x0, frame.length, 0.0, min(self.height, frame.height), side)
        out = frame.matrix[:3, 1] / np.linalg.norm(frame.matrix[:3, 1]) * side * 0.01
        ring = [p + out for p in ring]
        segs = [q for p, r in zip(ring, ring[1:] + ring[:1]) for q in (p, r)]
        self.viewport.show_polygon(ring, segments=segs, colors=[PREVIEW] * len(segs))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        found = self._face_at(x, y)
        if found is None:
            self.host.message(t("err.no_wall"), warning=True)
            return
        wall, _frame, side = found
        try:
            bim.add_cladding(self.doc, wall, side, self.finish, self.height)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self.viewport.clear_overlays()
        self.host.message(t("info.wall_finish", f=t("finish." + self.finish), h=_fmt(self.height),
                            wall=self.doc.get(wall).name))

    def cancel(self):
        self.viewport.clear_overlays()


class LightTool(Tool):
    name = "light"
    placement = True
    keys_help = "keys.light"

    def __init__(self, host):
        super().__init__(host)
        self.kind = "panel"

    def options(self):
        return [Option("kind", t("ctx.light"), "choice", self.kind, tuple((k, t("light." + k)) for k in LIGHTS))]

    def set_option(self, key, value):
        if key == "kind" and value in LIGHTS:
            self.kind = value
        self.host.set_hint(self.hint())

    def hint(self):
        return t("hint.light", k=t("light." + self.kind).lower())

    def _point(self, x, y):
        hit = self.viewport.pick_point(x, y)
        if hit is not None:
            return np.asarray(hit[2], dtype=float)
        origin, direction = self.viewport.ray(x, y)
        level = self.doc.work_level()
        if abs(direction[2]) < 1e-9:
            return None
        s = (level - origin[2]) / direction[2]
        return origin + direction * s if s > 0 else None

    def pointer_move(self, x, y, modifiers):
        p = self._point(x, y)
        if p is None:
            self.viewport.show_marker(None)
            return
        z = self.doc.ifc.ceiling_z_at(p, self.doc.active_storey)
        point = np.array((p[0], p[1], p[2] if z is None else z))
        self.viewport.show_marker(point, SNAP_COLORS["endpoint"])
        self.viewport.show_tip(t("tip.light") if z is not None else t("tip.light_no_ceiling"), point)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        p = self._point(x, y)
        if p is None:
            return
        bim.add_light(self.doc, (float(p[0]), float(p[1])), self.kind)
        self.host.message(t("info.light", k=t("light." + self.kind)))

    def cancel(self):
        self.viewport.clear_overlays()
