"""Air terminal (0.138, Phase 6, step 2 — HVAC): a click puts a diffuser or a grille in the ceiling over the point
(IfcAirTerminal), with its port on top; a duct drawn to it comes down to it and is connected (the Duct tool).

HVAC unit (0.139): a click puts a unit (IfcUnitaryEquipment) — a ducted unit, a wall split, an outdoor unit, an
AHU — the middle of its base there, its base at the height on the contextual bar, turned with R; its ports where
its ducts (and its drain) are connected."""

import numpy as np

from ..core.units import format_length
from ..i18n import decimal_sep, t
from ..ifc.equipment import EQUIPMENT, footprint
from ..ifc.terminals import TERMINALS
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, SNAP_COLORS, Option, Tool, show_snap
from .bim_draw import ANGLES, _PointTool, box_edges, length_option


class AirTerminalTool(Tool):
    name = "air_terminal"
    placement = True                     # (Esc: back to Select)
    keys_help = "keys.air_terminal"

    def __init__(self, host):
        super().__init__(host)
        self.kind = "diffuser_60"

    def options(self):
        return [Option("kind", t("ctx.air_terminal"), "choice", self.kind,
                       tuple((k, t("terminal." + k)) for k in TERMINALS))]

    def set_option(self, key, value):
        if key == "kind" and value in TERMINALS:
            self.kind = value
        self.host.set_hint(self.hint())

    def hint(self):
        return t("hint.air_terminal", k=t("terminal." + self.kind).lower())

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
        try:
            z = self.doc.ifc.ceiling_z_at(p, self.doc.active_storey)
        except RuntimeError:
            z = None
        point = np.array((p[0], p[1], p[2] if z is None else z))
        self.viewport.show_marker(point, SNAP_COLORS["endpoint"])
        self.viewport.show_tip(t("tip.air_terminal") if z is not None else t("tip.air_terminal_no_ceiling"), point)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        p = self._point(x, y)
        if p is None:
            return
        bim.add_air_terminal(self.doc, (float(p[0]), float(p[1])), self.kind)
        self.host.message(t("info.air_terminal", k=t("terminal." + self.kind)))

    def cancel(self):
        self.viewport.clear_overlays()


class EquipmentTool(_PointTool):
    """HVAC unit (0.139): its outline under the mouse (the snaps and alignments, on the active storey), a click puts
    it; R / Shift+R turn it 90°."""

    name = "equipment"
    placement = True
    accepts_typing = False
    common_keys = frozenset(("r", "shift+r"))
    keys_help = "keys.equipment"

    def __init__(self, host):
        super().__init__(host)
        self.kind = "ducted_unit"
        self.base = EQUIPMENT[self.kind][2]
        self.angle = 0

    def options(self):
        return [Option("kind", t("ctx.equipment"), "choice", self.kind,
                       tuple((k, t("equipment." + k)) for k in EQUIPMENT)),
                length_option("base", "ctx.equipment_base", self.base),
                Option("angle", t("ctx.angle"), "choice", self.angle, tuple((a, "{}°".format(a)) for a in ANGLES))]

    def set_option(self, key, value):
        if key == "kind" and value in EQUIPMENT:
            self.kind = value
            self.base = EQUIPMENT[value][2]             # (its usual height)
        elif key == "base":
            self.base = float(value)
        elif key == "angle":
            self.angle = int(value)
        self._again()

    def common_key(self, name):
        self.angle = (self.angle + (90 if name == "r" else -90)) % 360
        self.host.message(t("info.turned", a=self.angle))
        self._again()
        return True

    def _again(self):
        self.host.set_hint(self.hint())
        if self._hover is not None:
            self._show(*self._hover)

    def hint(self):
        return t("hint.equipment", k=t("equipment." + self.kind), h=format_length(self.base, decimal_sep()))

    def _show(self, p, snap):
        base = np.array((p[0], p[1], self.doc.work_level() + self.base))
        foot = footprint(base, self.angle, self.kind)
        height = EQUIPMENT[self.kind][1][2]
        segs = box_edges(foot, [c + np.array((0.0, 0.0, height)) for c in foot])
        self.viewport.show_polygon(foot, segments=segs, colors=[PREVIEW] * len(segs))
        show_snap(self.viewport, snap, p)

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        self._show(p, snap)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        p, _snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
        if p is None:
            return
        bim.add_equipment(self.doc, (float(p[0]), float(p[1])), self.kind, self.angle, self.base)
        self.viewport.clear_overlays()
        self.host.message(t("info.equipment", k=t("equipment." + self.kind)))

    def cancel(self):
        self.viewport.clear_overlays()
