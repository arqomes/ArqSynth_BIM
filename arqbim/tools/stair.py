"""Stair (0.114): a click on the middle of the first step (on the floor), a second one the way it goes up — a
straight stair, or an L or a U turning to the left or right at a landing; its rise (to the storey above), width
and tread on the contextual bar, the risers worked out (17 or 18 cm at most) and shown with the Blondel step."""

import numpy as np

from ..core import stairs as core_stairs
from ..core.units import format_length
from ..i18n import decimal_sep, refusal, t
from ..ifc import catalog
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, show_snap
from .bim_draw import _name, _PointTool, length_option, type_option

Z = np.array((0.0, 0.0, 1.0))


def _fmt(v):
    return format_length(v, decimal_sep())


class StairTool(_PointTool):
    name = "stair"
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.stair"
    accepts_typing = False

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.spec = catalog.BY_KEY["laje_15"]
        self.form = "straight"
        self.turn = "left"
        self.width = 1.00
        self.going = 0.28
        self.rise = None                   # (None: up to the storey above)
        self._foot = None

    def _rise(self, z):
        return bim.stair_rise(self.doc, z) if self.rise is None else self.rise

    def options(self):
        return [type_option(self.spec, "slab"),
                Option("form", t("ctx.stair_form"), "choice", self.form,
                       tuple((f, t("stairform." + f)) for f in core_stairs.FORMS)),
                Option("turn", t("ctx.stair_turn"), "choice", self.turn,
                       tuple((s, t("stairturn." + s)) for s in core_stairs.TURNS)),
                length_option("width", "props.width", self.width),
                length_option("going", "ctx.going", self.going),
                length_option("rise", "ctx.rise", self._rise(self.doc.work_level()))]

    def set_option(self, key, value):
        if key == "type":
            self.spec = catalog.BY_KEY[value]
        elif key == "form" and value in core_stairs.FORMS:
            self.form = value
        elif key == "turn" and value in core_stairs.TURNS:
            self.turn = value
        elif key == "width" and value >= 0.5:
            self.width = value
        elif key == "going" and value >= 0.15:
            self.going = value
        elif key == "rise" and value >= 0.3:
            self.rise = value
        self.host.set_hint(self.hint())

    def _steps(self, z):
        n, h = core_stairs.risers(self._rise(z))
        return n, h

    def hint(self):
        z = self._foot[2] if self._foot is not None else self.doc.work_level()
        if self._foot is None:
            return t("hint.stair", form=t("stairform." + self.form), w=_fmt(self.width), h=_fmt(self._rise(z)))
        n, h = self._steps(z)
        return t("hint.stair_2", n=n, r=_fmt(h), g=_fmt(self.going), b=_fmt(2 * h + self.going))

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, None if self._foot is None else self._foot[2], self._foot, modifiers)
        if p is None:
            return
        if self._foot is None:
            show_snap(self.viewport, snap, p)
            return
        d = (p - self._foot)[:2]
        if np.linalg.norm(d) < 1e-6:
            return
        d = d / np.linalg.norm(d)
        pieces = core_stairs.layout(self.form, self._rise(self._foot[2]), self.width, self.going, self.turn)
        rings = core_stairs.footprint(pieces, self.width, self.going)
        segs = []
        c, s = d[0], d[1]
        for ring in rings:
            world = [self._foot + np.array((c * x_ - s * y_, s * x_ + c * y_, 0.01)) for x_, y_ in ring]
            segs += [q for a, b in zip(world, world[1:] + world[:1]) for q in (a, b)]
        self.viewport.show_lines(segs, [PREVIEW] * len(segs))
        show_snap(self.viewport, snap, p)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        p, _snap = self._point(x, y, None if self._foot is None else self._foot[2], self._foot, modifiers)
        if p is None:
            return
        if self._foot is None:
            self._foot = p
            self.host.set_hint(self.hint())
            return
        d = (p - self._foot)[:2]
        if np.linalg.norm(d) < 0.05:
            return
        rise = self._rise(self._foot[2])
        try:
            bim.add_stair(self.doc, self._foot, d, self.spec, self.form, rise, self.width, self.going, self.turn,
                          storey=self.doc.active_storey)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self.cancel()
            return
        n, h = core_stairs.risers(rise)
        self.host.message(t("info.stair", form=t("stairform." + self.form), n=n, r=_fmt(h),
                            g=_fmt(self.going), h=_fmt(rise)))
        self.cancel()

    def cancel(self):
        self._foot = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())

    def type_name(self):
        return _name(self.spec)
