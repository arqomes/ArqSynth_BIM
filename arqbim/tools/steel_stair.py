"""(0.509) The «Escada metálica» tool: as the Stair's two clicks — the middle of the first step on the floor, then the
way it goes up — a straight steel stair: its treads of grating or folded chequered plate between two stringers of
channel (core/steel_stair, ifc/steel_stairs). On the contextual bar: its rise (to the storey above unless typed), its
width, its going, its treads, its stringers' channel."""

import numpy as np

from ..core import stairs as core_stairs
from ..core import steel_stair as core_steel_stair
from ..core.units import format_length
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, show_snap
from .bim_draw import _PointTool, length_option


def _fmt(v):
    return format_length(v, decimal_sep())


class SteelStairTool(_PointTool):
    name = "steel_stair"
    keys_help = "keys.chain"
    accepts_typing = False
    common_keys = frozenset(("x", "y", "n"))

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.width, self.going = 1.00, 0.28
        self.rise = None                   # (None: up to the storey above)
        self.tread = "grelha"
        self.section = "UPN200"
        self._foot = None

    def _rise(self, z):
        return bim.stair_rise(self.doc, z) if self.rise is None else self.rise

    def options(self):
        from ..core import steel
        return [length_option("rise", "ctx.sstair_rise", self._rise(self.doc.work_level())),
                length_option("width", "ctx.sstair_width", self.width),
                length_option("going", "ctx.sstair_going", self.going),
                Option("tread", t("ctx.sstair_tread"), "choice", self.tread,
                       tuple((k, t("sstair." + k)) for k in core_steel_stair.TREADS)),
                Option("section", t("ctx.sstair_section"), "choice", self.section,
                       tuple((s, steel.display(s)) for s in core_steel_stair.STRINGERS))]

    def set_option(self, key, value):
        if key == "rise" and float(value) >= 0.3:
            self.rise = float(value)
        elif key == "width" and float(value) >= 0.5:
            self.width = float(value)
        elif key == "going" and float(value) >= 0.15:
            self.going = float(value)
        elif key == "tread" and value in core_steel_stair.TREADS:
            self.tread = value
        elif key == "section" and value in core_steel_stair.STRINGERS:
            self.section = value
        self.host.set_hint(self.hint())

    def hint(self):
        if self._foot is None:
            return t("hint.sstair_start")
        n, h = core_stairs.risers(self._rise(self._foot[2]))
        return t("hint.sstair_dir", n=n, h=_fmt(h), g=_fmt(self.going))

    def _outline(self, foot, d):
        """Its footprint seen from above (the treads' and the stringers'): line segments."""
        from ..core import steel
        n, _h = core_stairs.risers(self._rise(foot[2]))
        b = steel.get(self.section).b / 1000.0
        half = self.width / 2.0 + b
        length = (n - 1) * self.going
        left = np.array((-d[1], d[0]))
        corners = [(-core_steel_stair.NOSING, -half), (length, -half), (length, half), (-core_steel_stair.NOSING, half)]
        world = [foot + np.array((d[0] * x + left[0] * y, d[1] * x + left[1] * y, 0.01)) for x, y in corners]
        segs = [q for a, b_ in zip(world, world[1:] + world[:1]) for q in (a, b_)]
        for k in range(1, n - 1):                          # (the treads' lines)
            a = foot + np.array((d[0] * k * self.going, d[1] * k * self.going, 0.01))
            segs += [a + np.array((left[0], left[1], 0.0)) * self.width / 2.0,
                     a - np.array((left[0], left[1], 0.0)) * self.width / 2.0]
        return segs

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
        segs = self._outline(self._foot, d)
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
        self._make(self._foot, d)

    def _make(self, foot, d):
        rise = self._rise(foot[2])
        try:
            bim.add_steel_stair(self.doc, foot, d, rise, self.width, self.going, self.section, self.tread,
                                storey=self.doc.active_storey)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self.cancel()
            return
        n, h = core_stairs.risers(rise)
        from ..core import steel
        self.host.message(t("info.steel_stair", n=n, h=_fmt(h), t=n - 1, s=steel.display(self.section)))
        self.cancel()

    def cancel(self):
        self._foot = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
