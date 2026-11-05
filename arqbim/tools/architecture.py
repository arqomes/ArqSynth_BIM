"""Architecture tools of the addon's inventory and the study's ribbon (0.374):

- Gutter («Calha»): over a roof, the eave nearest the mouse is shown; a click hangs a gutter along it, outside.
- Elevator («Elevador»): its shaft's outline follows the mouse on the active storey (R / Shift+R turn it 90°); a click
  puts the shaft and the car there, up to over the top storey.
- Room separator («Separador»): two clicks, and on from there (Esc ends): lines that bound rooms where there is no
  wall; the rooms of the storey are found again with them."""

import numpy as np

from ..core import band_solid
from ..core.units import format_length
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, Tool, show_snap
from .bim_draw import MIN_LENGTH, _PointTool, length_option

ANGLES = (0, 90, 180, 270)


def _fmt(v):
    return format_length(v, decimal_sep())


class GutterTool(Tool):
    name = "gutter"
    placement = True                    # (Esc: back to Select)

    def __init__(self, host):
        super().__init__(host)
        self._eaves = None              # (roof id, its mesh, [(a, b, outward)])

    def hint(self):
        return t("hint.gutter")

    def _eave_at(self, x, y):
        hit = self.viewport.pick_point(x, y)
        obj = self.doc.get(hit[0]) if hit is not None else None
        if obj is None or not obj.is_bim or self.doc.ifc.kind_of(obj.id) != "roof":
            return None
        if self._eaves is None or self._eaves[0] != obj.id or self._eaves[1] is not obj.mesh:
            self._eaves = (obj.id, obj.mesh, bim.roof_eaves(self.doc, obj.id))
        p = np.asarray(hit[2], dtype=float)[:2]
        best = None
        for a, b, out in self._eaves[2]:
            d = b[:2] - a[:2]
            s = np.clip(float((p - a[:2]) @ d) / max(float(d @ d), 1e-12), 0.0, 1.0)
            dist = float(np.linalg.norm(a[:2] + d * s - p))
            if best is None or dist < best[0]:
                best = (dist, a, b, out)
        return (obj.id,) + best[1:] if best is not None else None

    def pointer_move(self, x, y, modifiers):
        found = self._eave_at(x, y)
        if found is None:
            self.viewport.clear_overlays()
            return
        _roof, a, b, out = found
        from ..ifc.architecture import GUTTER, GUTTER_DROP
        w, h, _s = GUTTER
        # (0.384) the gutter as a solid, where it will hang: under the eave's upper edge, outside it
        tris, segs = band_solid.band_solid([a[:2] + out[:2] * w, b[:2] + out[:2] * w], [a[:2], b[:2]],
                                           float(a[2]) - GUTTER_DROP - h, h, closed=False)
        self.viewport.show_volume(tris, segs, [PREVIEW] * len(segs))
        joins = bim.gutter_joins(self.doc, a, b, out)
        self.viewport.show_tip(t("tip.gutter_joined" if joins else "tip.gutter",
                                 l=_fmt(float(np.linalg.norm((b - a)[:2]))), n=len(joins)), (a + b) / 2)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        found = self._eave_at(x, y)
        if found is None:
            self.host.message(t("err.gutter_roof"), warning=True)
            return
        roof, a, b, out = found
        joins = bim.gutter_joins(self.doc, a, b, out)
        bim.add_gutter(self.doc, a, b, out, storey=self.doc.ifc.storey_of(roof))
        text = t("info.gutter", l=_fmt(float(np.linalg.norm((b - a)[:2]))), roof=self.doc.get(roof).name)
        if joins:
            text += " " + t("info.gutter_joined", n=len(joins))
        self.host.message(text)

    def cancel(self):
        self.viewport.clear_overlays()


class ElevatorTool(_PointTool):
    name = "elevator"
    placement = True
    common_keys = frozenset(("r", "shift+r"))

    def __init__(self, host):
        super().__init__(host)
        self.width, self.depth, self.angle = 1.60, 1.75, 0
        self._at = None

    def options(self):
        return [length_option("width", "ctx.elevator_width", self.width),
                length_option("depth", "ctx.elevator_depth", self.depth),
                Option("angle", t("ctx.angle"), "choice", self.angle, tuple((a, "{}°".format(a)) for a in ANGLES))]

    def set_option(self, key, value):
        if key == "width" and value >= 0.8:
            self.width = float(value)
        elif key == "depth" and value >= 0.8:
            self.depth = float(value)
        elif key == "angle":
            self.angle = int(value) % 360
        self.host.set_hint(self.hint())

    def common_key(self, name):
        self.angle = (self.angle + (90 if name == "r" else -90)) % 360
        self.host.set_hint(self.hint())
        if self._at is not None:
            self._show(self._at)
        return True

    def hint(self):
        return t("hint.elevator", w=_fmt(self.width), d=_fmt(self.depth))

    def _ring(self, corner):
        c, s = np.cos(np.radians(self.angle)), np.sin(np.radians(self.angle))
        x, y = np.array((c, s, 0.0)), np.array((-s, c, 0.0))
        t_ = 0.15
        pts = [(-t_, 0.0), (self.width + t_, 0.0), (self.width + t_, self.depth + t_), (-t_, self.depth + t_)]
        return [corner + x * a + y * b for a, b in pts]

    def _show(self, corner):
        ring = self._ring(corner)
        self.viewport.show_lines([q for k in range(4) for q in (ring[k], ring[(k + 1) % 4])], [PREVIEW] * 8)

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
        if p is None:
            return
        self._at = p
        self._show(p)
        show_snap(self.viewport, snap, p)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        p, _snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
        if p is None:
            return
        try:
            bim.add_elevator(self.doc, (float(p[0]), float(p[1])), self.width, self.depth, self.angle)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self.host.message(t("info.elevator", w=_fmt(self.width), d=_fmt(self.depth)))

    def cancel(self):
        self._at = None
        self.viewport.clear_overlays()


class SeparatorTool(_PointTool):
    name = "room_separator"
    common_keys = frozenset(("x", "y", "n"))

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self._start = None

    def hint(self):
        return t("hint.separator_next" if self._start is not None else "hint.separator")

    def pointer_move(self, x, y, modifiers):
        level = self.doc.work_level()
        p, snap = self._point(x, y, level, self._start, modifiers)
        if p is None:
            return
        if self._start is not None:
            self.viewport.show_lines([self._start, p], [PREVIEW, PREVIEW])
        show_snap(self.viewport, snap, p)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        level = self.doc.work_level()
        p, _snap = self._point(x, y, level, self._start, modifiers)
        if p is None:
            return
        if self._start is None:
            self._start = p
            self.host.set_hint(self.hint())
            return
        if np.linalg.norm((p - self._start)[:2]) < MIN_LENGTH:
            return
        bim.add_separator(self.doc, self._start[:2], p[:2])
        self.host.message(t("info.separator", l=_fmt(float(np.linalg.norm((p - self._start)[:2])))))
        self._start = p

    def cancel(self):
        self._start = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
