"""Drain and Opening through a roof (0.113).

Drain: over a roof, the point on its top is shown; a click puts a roof drain there (IfcWasteTerminal ROOFDRAIN).
Opening: over a roof or a slab, two clicks give a rectangle in plan; it is cut straight through (a skylight's
hole, IfcOpeningElement) — or its size typed after the first corner ("1;0,8")."""

import numpy as np

from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, SNAP_COLORS, Tool

HOSTS = ("roof", "slab")


def _fmt(v):
    return format_length(v, decimal_sep())


def _host_at(tool, x, y, kinds):
    hit = tool.viewport.pick_point(x, y)
    if hit is None:
        return None
    obj = tool.doc.get(hit[0])
    if obj is None or not obj.is_bim or tool.doc.ifc.kind_of(obj.id) not in kinds:
        return None
    return obj.id, np.asarray(hit[2], dtype=float)


class DrainTool(Tool):
    name = "drain"
    placement = True                     # (Esc: back to Select)
    keys_help = "keys.drain"

    def hint(self):
        return t("hint.drain")

    def pointer_move(self, x, y, modifiers):
        found = _host_at(self, x, y, ("roof",))
        if found is None:
            self.viewport.show_marker(None)
            self.viewport.show_tip("", None)
            return
        roof, p = found
        z = self.doc.ifc.roof_height_at(roof, p)
        point = np.array((p[0], p[1], z))
        self.viewport.show_marker(point, SNAP_COLORS["endpoint"])
        self.viewport.show_tip(t("tip.drain"), point)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        found = _host_at(self, x, y, ("roof",))
        if found is None:
            self.host.message(t("err.drain_roof"), warning=True)
            return
        roof, p = found
        bim.add_drain(self.doc, roof, (float(p[0]), float(p[1])))
        self.host.message(t("info.drain", roof=self.doc.get(roof).name))

    def cancel(self):
        self.viewport.clear_overlays()


class VerticalOpeningTool(Tool):
    name = "roof_opening"
    accepts_typing = True
    placement = True
    keys_help = "keys.roof_opening"

    def __init__(self, host):
        super().__init__(host)
        self._first = None               # (host, first corner)
        self._end = None

    def hint(self):
        return t("hint.roof_opening_2") if self._first is not None else t("hint.roof_opening")

    def vcb_title(self):
        return t("vcb.dims")

    def _rect(self, a, b, z):
        return [np.array((x, y, z)) for x, y in ((a[0], a[1]), (b[0], a[1]), (b[0], b[1]), (a[0], b[1]))]

    def pointer_move(self, x, y, modifiers):
        found = _host_at(self, x, y, HOSTS)
        if self._first is None:
            if found is None:
                self.viewport.show_marker(None)
                return
            self.viewport.show_marker(found[1])
            return
        host, a = self._first
        if found is None or found[0] != host:
            return
        self._end = found[1]
        ring = self._rect(a, self._end, max(a[2], self._end[2]) + 0.02)
        segs = [q for p, r in zip(ring, ring[1:] + ring[:1]) for q in (p, r)]
        self.viewport.show_polygon(ring, segments=segs, colors=[PREVIEW] * len(segs))
        self.host.set_vcb("{} × {}".format(_fmt(abs(self._end[0] - a[0])), _fmt(abs(self._end[1] - a[1]))))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._first is not None:
                self.cancel()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT:
            return
        if self._first is None:
            found = _host_at(self, x, y, HOSTS)
            if found is None:
                self.host.message(t("err.roof_opening_host"), warning=True)
                return
            self._first = found
            self.host.set_hint(self.hint())
            return
        if self._end is not None:
            self._make(self._first[1], self._end)

    def typed(self, text):
        values = parse_lengths(text, 2)
        if values is None or self._first is None or values[0] is None:
            if values is None:
                self.host.message(t("err.bad_value", t=text), warning=True)
            return
        a = self._first[1]
        w, d = values[0], values[1] if values[1] is not None else values[0]
        sx = -1.0 if self._end is not None and self._end[0] < a[0] else 1.0
        sy = -1.0 if self._end is not None and self._end[1] < a[1] else 1.0
        self._make(a, a + np.array((sx * w, sy * d, 0.0)))

    def _make(self, a, b):
        host = self._first[0]
        try:
            bim.add_vertical_opening(self.doc, host, (float(a[0]), float(a[1])), (float(b[0]), float(b[1])))
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self.cancel()
            return
        self.host.message(t("info.roof_opening", a=_fmt(abs(b[0] - a[0])), b=_fmt(abs(b[1] - a[1])),
                            host=self.doc.get(host).name))
        self.cancel()

    def cancel(self):
        self._first = self._end = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
