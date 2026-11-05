"""Railing (0.115): along a path clicked point by point (Enter ends it; Delete takes the last point back), round
a void of a slab (a click on the slab by a hole or an opening), or on both sides of a stair's flights (a click on
the stair) — Tab changes which; its type (0.258: the program's and the project's railing types) and height on the
contextual bar."""

import numpy as np

from ..core import railing_types as core_rail
from ..core.units import format_length
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, show_snap
from .bim_draw import MIN_LENGTH, _PointTool, length_option

SHAPES = ("path", "void", "stair", "opening")           # (0.374: in a door's / window's opening)


def _fmt(v):
    return format_length(v, decimal_sep())


class RailingTool(_PointTool):
    name = "railing"
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.railing"

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.shape = "path"
        self.style = core_rail.DEFAULT          # (0.258: a railing type's key)
        self.height = core_rail.PRESETS[core_rail.DEFAULT].height
        self._points = []
        self._end = None

    def activate(self):
        if self.style not in dict(self.doc.ifc.railing_type_choices()):     # (a type of another project)
            self.style = core_rail.DEFAULT
        super().activate()

    def options(self):
        return [Option("shape", t("ctx.railing_shape"), "choice", self.shape,
                       tuple((s, t("railshape." + s)) for s in SHAPES)),
                Option("style", t("ctx.railing_type"), "choice", self.style,
                       tuple(self.doc.ifc.railing_type_choices())),
                length_option("height", "ctx.height", self.height)]

    def set_option(self, key, value):
        if key == "shape" and value in SHAPES:
            self.shape = value
            self.cancel()
        elif key == "style" and value in dict(self.doc.ifc.railing_type_choices()):
            self.style = value
            self.height = self.doc.ifc.railing_type(value).height          # (its usual height)
        elif key == "height" and 0.3 <= value <= 3.0:
            self.height = value
        self.host.set_hint(self.hint())

    def tab(self):
        self.set_option("shape", SHAPES[(SHAPES.index(self.shape) + 1) % len(SHAPES)])
        return True

    def _type_name(self):
        return self.doc.ifc.railing_type(self.style).name

    def hint(self):
        return t("hint.railing." + self.shape, style=self._type_name().lower(), h=_fmt(self.height))

    def _element_at(self, x, y, kind):
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None
        obj = self.doc.get(hit[0])
        if obj is None or not obj.is_bim or self.doc.ifc.kind_of(obj.id) != kind:
            return None
        return obj.id, np.asarray(hit[2], dtype=float)

    def pointer_move(self, x, y, modifiers):
        if self.shape != "path":
            return
        last = self._points[-1] if self._points else None
        p, snap = self._point(x, y, None if last is None else last[2], last, modifiers)
        if p is None:
            return
        self._end = p
        pts = self._points + [p]
        segs = [q for a, b in zip(pts, pts[1:]) for q in (a, b)]
        if segs:
            top = [q + np.array((0.0, 0.0, self.height)) for q in pts]
            segs += [q for a, b in zip(top, top[1:]) for q in (a, b)]
            self.viewport.show_lines(segs, [PREVIEW] * len(segs))
        show_snap(self.viewport, snap, p)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._points:
                self.enter()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT:
            return
        if self.shape == "stair":
            found = self._element_at(x, y, "stair")
            if found is None:
                self.host.message(t("err.railing_stair"), warning=True)
                return
            made = bim.stair_railings(self.doc, found[0], 0.90, self.style)
            self.host.message(t("info.stair_railings", n=len(made)))
            return
        if self.shape == "opening":                     # (0.374) in a door's / window's opening, jamb to jamb
            found = self._element_at(x, y, "window") or self._element_at(x, y, "door")
            if found is None:
                self.host.message(t("err.railing_opening"), warning=True)
                return
            try:
                guid = bim.opening_railing(self.doc, found[0], self.height, self.style)
            except (ValueError, KeyError) as exc:
                self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
                return
            self._done(guid)
            return
        if self.shape == "void":
            found = self._element_at(x, y, "slab")
            guid = bim.void_railing(self.doc, found[0], found[1][:2], self.height, self.style) if found else None
            if guid is None:
                self.host.message(t("err.railing_void"), warning=True)
                return
            self._done(guid)
            return
        last = self._points[-1] if self._points else None
        p, _snap = self._point(x, y, None if last is None else last[2], last, modifiers)
        if p is None:
            return
        if last is not None and np.linalg.norm((p - last)[:2]) < MIN_LENGTH:
            return
        self._points.append(p)

    def enter(self):
        if self.shape != "path" or len(self._points) < 2:
            return
        try:
            guid = bim.add_railing(self.doc, [tuple(q) for q in self._points], self.height, self.style,
                                   storey=self.doc.active_storey)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self.cancel()
            return
        self.cancel()
        self._done(guid)

    def _done(self, guid):
        p = self.doc.ifc.describe(guid)["params"]
        self.host.message(t("info.railing", l=_fmt(p["length"]), style=p["type_name"].lower(), h=_fmt(p["height"])))

    def delete(self):
        if self._points:
            self._points.pop()
            self.viewport.clear_overlays()

    def cancel(self):
        self._points = []
        self._end = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
