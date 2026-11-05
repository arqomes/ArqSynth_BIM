"""Ramp (0.101): a straight ramp by its axis — a click on the middle of its foot, another on the middle of its head
(or its length typed: "6" or "6;0,5", the rise too). Its width and rise are on the contextual bar, its thickness
and material the slab type's; its slope is shown while it is drawn (IfcRamp)."""

import numpy as np

from ..core.units import parse_lengths
from ..i18n import decimal_sep, t
from ..ifc import catalog
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, drawing_dims, show_snap, show_start_reference, start_reference
from .bim_draw import MIN_LENGTH, _fmt, _name, _PointTool, box_edges, length_option, type_option

Z = np.array((0.0, 0.0, 1.0))


def slope_text(rise, length):
    return "{:.1f} %".format(100.0 * rise / length if length > 0 else 0.0).replace(".", decimal_sep())


class RampTool(_PointTool):
    name = "ramp"
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.chain"

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.spec = catalog.BY_KEY["laje_15"]
        self.width = 1.20
        self.rise = 0.50
        self._start = None
        self._end = None
        self._start_ref = None

    def set_spec(self, spec):
        self.spec = spec
        self.host.set_hint(self.hint())

    def options(self):
        return [type_option(self.spec, "slab"), length_option("width", "ctx.width", self.width),
                length_option("rise", "ctx.rise", self.rise)]

    def set_option(self, key, value):
        if key == "type":
            self.set_spec(catalog.BY_KEY[value])
        elif key == "width" and value >= 0.3:
            self.width = value
        elif key == "rise" and value >= 0.0:
            self.rise = value
        self.host.set_hint(self.hint())

    def hint(self):
        if self._start is not None:
            return t("hint.ramp.end")
        return t("hint.ramp.start", type=_name(self.spec), w=_fmt(self.width), h=_fmt(self.rise))

    def vcb_title(self):
        return t("vcb.length")

    def pointer_move(self, x, y, modifiers):
        if self._start is None:
            p, snap = self._point(x, y, modifiers=modifiers)
            if p is None:
                return
            self._hover = (p, snap)
            show_snap(self.viewport, snap, p)
            self._start_ref = start_reference(snap)
            show_start_reference(self.viewport, self._start_ref, p)
            return
        p, snap = self._point(x, y, self._start[2], self._start, modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        self._end = p
        self._preview(snap)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self._start is None:
            p, _snap = self._point(x, y, modifiers=modifiers)
            if p is not None:
                self._start = p
                self.host.set_hint(self.hint())
            return
        if self._end is not None:
            self._finish(self._end)

    def typed(self, text):
        values = parse_lengths(text, 2)
        if values is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        length, rise = values
        if rise is not None and rise >= 0.0:
            self.rise = rise
            self.host.set_hint(self.hint())
        if length is None:
            return
        if self._start is None and self._start_ref is not None and rise is None:
            src, direction = self._start_ref            # before the first click: its foot that far from there
            self._start = src + direction * length
            self.viewport.clear_overlays()
            self.host.set_hint(self.hint())
            self.host.message(t("info.start_typed", l=_fmt(length)))
            return
        if self._start is None:
            if self._hover is None:
                return
            self._start = self._hover[0].copy()             # forgiving: typed before clicking
        d = (self._end - self._start) if self._end is not None else np.array((1.0, 0.0, 0.0))
        d = np.array((d[0], d[1], 0.0))
        d = d / np.linalg.norm(d) if np.linalg.norm(d) > 1e-9 else np.array((1.0, 0.0, 0.0))
        self._finish(self._start + d * abs(length))

    def cancel(self):
        self._start = self._end = self._start_ref = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    def _corners(self, end):
        s = np.asarray(self._start, dtype=float)
        d = np.array((end[0] - s[0], end[1] - s[1], 0.0))
        length = float(np.linalg.norm(d))
        x = d / length
        y = np.cross(Z, x) * self.width / 2
        head = s + d + Z * self.rise
        tops = [s - y, s + d - y + Z * self.rise, s + d + y + Z * self.rise, s + y]
        bottoms = [p - Z * self.spec.thickness for p in tops]
        return bottoms, tops, length, head

    def _preview(self, snap):
        length = float(np.linalg.norm((self._end - self._start)[:2]))
        if length < 1e-6:
            return
        bottoms, tops, length, head = self._corners(self._end)
        segs = box_edges(bottoms, tops)
        self.viewport.show_polygon(tops, segments=segs, colors=[PREVIEW] * len(segs))
        drawing_dims(self.viewport, self._start, np.array((self._end[0], self._end[1], self._start[2])))
        show_snap(self.viewport, snap, self._end)
        self.viewport.show_label(t("tip.ramp_slope", s=slope_text(self.rise, length)), head)
        self.host.set_vcb(_fmt(length))

    def _finish(self, end):
        length = float(np.linalg.norm((end - self._start)[:2]))
        if length < MIN_LENGTH:
            return
        end = np.array((end[0], end[1], self._start[2]))
        bim.add_ramp(self.doc, self._start, end, self.spec, self.width, self.rise, storey=self.doc.active_storey)
        self.host.message(t("info.ramp", l=_fmt(length), h=_fmt(self.rise), s=slope_text(self.rise, length),
                            type=_name(self.spec)))
        self.cancel()
