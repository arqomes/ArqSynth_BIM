"""Cabinet (0.169, Phase 10, step 1): a kitchen or storage module — a base unit, a wall unit, a tall unit — put
with its back against a wall's face, facing the room, where the mouse is along it; beside a cabinet already there
(within 10 cm) it goes flush against its side, as a run of modules is built. Away from walls, at the point, turned
with R. Its width, fronts and handle chosen on the bar (or typed: its width)."""

import math

import numpy as np

from ..core import cabinets as core_cab
from ..core.units import parse_lengths
from ..i18n import t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, show_snap
from .bim_draw import ANGLES, _PointTool

FLUSH = 0.10                    # m: a cabinet this near another's side (along the wall) goes against it


class CabinetTool(_PointTool):
    name = "cabinet"
    placement = True
    accepts_typing = True
    common_keys = frozenset(("r", "shift+r"))
    keys_help = "keys.cabinet"

    def __init__(self, host):
        super().__init__(host)
        self.kind = "base"
        self.width = 0.60
        self.fronts = "doors"
        self.handle = "bar"
        self.finish = "melamine"            # (0.243) its fronts' finish
        self.angle = 0
        self._frames = {}

    def options(self):
        return [Option("kind", t("ctx.cabinet"), "choice", self.kind,
                       tuple((k, t("cabinet.kind." + k)) for k in core_cab.KINDS)),
                Option("width", t("ctx.width"), "choice", self.width,
                       tuple((w, "{:g} cm".format(round(w * 100))) for w in core_cab.WIDTHS)),
                Option("fronts", t("ctx.fronts"), "choice", self.fronts,
                       tuple((k, t("cabinet.fronts." + k)) for k in core_cab.FRONTS)),
                Option("handle", t("ctx.handle"), "choice", self.handle,
                       tuple((k, t("cabinet.handle." + k)) for k in core_cab.HANDLES)),
                Option("finish", t("ctx.finish"), "choice", self.finish,
                       tuple((k, t("cabinet.finish." + k)) for k in core_cab.FINISHES)),
                Option("angle", t("ctx.angle"), "choice", self.angle, tuple((a, "{}°".format(a)) for a in ANGLES))]

    def set_option(self, key, value):
        if key == "kind" and value in core_cab.KINDS:
            self.kind = value
            self.width = float(core_cab.DEFAULTS[value].get("width", self.width))   # (a wardrobe: its own)
            if self.fronts == "oven" and value != "tall":
                self.fronts = "doors"                   # (0.242: an oven only in a tall unit)
        elif key == "width" and 0.15 <= float(value) <= self._widest():
            self.width = float(value)
        elif key == "fronts" and value in core_cab.FRONTS:
            self.fronts = value
        elif key == "handle" and value in core_cab.HANDLES:
            self.handle = value
        elif key == "finish" and value in core_cab.FINISHES:
            self.finish = value
        elif key == "angle":
            self.angle = int(value)
        self._again()

    def typed(self, text):
        """Its width typed in the Measurements box (as lengths are typed)."""
        values = parse_lengths(text, 1)
        if values is None or values[0] is None or not 0.15 <= values[0] <= self._widest():
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        self.width = round(float(values[0]), 3)
        self.host.message(t("info.cabinet_width", w="{:g}".format(round(self.width * 100, 1))))
        self._again()

    def _widest(self):
        return 2.70 if self.kind == "wardrobe" else 1.50      # (0.241: a wardrobe up to a board's length)

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
        return t("hint.cabinet", k=t("cabinet.kind." + self.kind).lower(), w="{:g}".format(round(self.width * 100, 1)))

    def cabinet(self):
        return core_cab.Cabinet.of(self.kind, width=self.width, fronts=self.fronts, handle=self.handle,
                                   finish=self.finish)

    def _wall_frame(self, wall):
        obj = self.doc.get(wall)
        cached = self._frames.get(wall)
        if cached is None or cached[0] != id(obj.mesh):
            cached = (id(obj.mesh), bim.wall_frame(self.doc, wall))
            self._frames[wall] = cached
        return cached[1]

    def _flush(self, back, x_dir, width):
        """The back's middle moved along the wall against a cabinet beside it (its side within FLUSH)."""
        best, shift = FLUSH, 0.0
        for guid, (b, d, w) in bim.cabinet_backs(self.doc).items():
            v = (b - back)[:2]
            if abs(float(np.dot(d, x_dir)) - 1.0) > 1e-3 or abs(float(d[0] * v[1] - d[1] * v[0])) > 0.02:
                continue                                 # (not on the same line, the same way)
            s = float(np.dot((b - back)[:2], x_dir[:2]))           # (from its middle to the other's, along it)
            gap = abs(s) - (w + width) / 2                          # (> 0 apart, < 0 into it)
            if abs(gap) < best:
                best, shift = abs(gap), s - math.copysign((w + width) / 2, s)
        return back + x_dir * shift

    def _place(self, x, y, modifiers):
        """(the middle of its back (3,), its angle, the wall it is against or None, the snap) under the mouse."""
        level = self.doc.work_level()
        hit = self.viewport.pick_point(x, y)
        if hit is not None:
            obj = self.doc.get(hit[0])
            try:
                wall = obj is not None and obj.is_bim and self.doc.ifc.kind_of(obj.id) == "wall"
            except RuntimeError:
                wall = False
            frame = self._wall_frame(obj.id) if wall else None
            if frame is not None:
                local = frame.to_local(np.asarray(hit[2], dtype=float))
                side = frame.face_side(obj.mesh.face_normal(hit[1]))
                if side == 0:
                    side = -1 if local[1] < (frame.y0 + frame.y1) / 2 else 1
                width = self.width
                lo, hi = frame.x0 + width / 2, frame.x0 + frame.length - width / 2
                along = min(max(round(float(local[0]), 2), lo), hi) if hi >= lo else frame.x0 + frame.length / 2
                back = frame.to_world((along, frame.y1 if side > 0 else frame.y0, 0.0))
                back[2] = level
                out = frame.matrix[:3, 1] / np.linalg.norm(frame.matrix[:3, 1]) * side
                x_dir = np.cross(out, (0.0, 0.0, 1.0))
                back = self._flush(back, x_dir, width)
                return back, math.degrees(math.atan2(x_dir[1], x_dir[0])), obj.id, None
        p, snap = self._point(x, y, level, modifiers=modifiers)
        return (None if p is None else np.array((p[0], p[1], level))), float(self.angle), None, snap

    def _show(self, x, y, modifiers):
        back, angle, _wall, snap = self._place(x, y, modifiers)
        if back is None:
            return
        foot = bim.cabinet_outline(back, angle, self.cabinet())
        segs = [q for a, b in zip(foot, foot[1:] + foot[:1]) for q in (a, b)]
        self.viewport.show_polygon(foot, segments=segs, colors=[PREVIEW] * len(segs))
        show_snap(self.viewport, snap, back)

    def pointer_move(self, x, y, modifiers):
        self._hover = (x, y, modifiers)
        self._show(x, y, modifiers)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        back, angle, wall, _snap = self._place(x, y, modifiers)
        if back is None:
            return
        bim.add_cabinet(self.doc, back, angle, self.cabinet())
        self.viewport.clear_overlays()
        self.host.message(t("info.cabinet_wall" if wall else "info.cabinet", k=t("cabinet.kind." + self.kind)))

    def cancel(self):
        self.viewport.clear_overlays()
