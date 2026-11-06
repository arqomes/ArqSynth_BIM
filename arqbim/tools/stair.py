"""Stair (0.114): a click on the middle of the first step (on the floor), a second one the way it goes up — a
straight stair, or an L or a U turning to the left or right at a landing; its rise (to the storey above), width
and tread on the contextual bar, the risers worked out (17 or 18 cm at most) and shown with the Blondel step.

(0.435, the addon's «Gerar escada»: a stair ready to put down) «Colocar ▸ Pronta»: the whole stair hangs on the
mouse, as a column or a component does; one click puts it there. R / Shift+R turn it a quarter, Space / Shift+Space
choose the point of its first step that goes on the point clicked — its middle, its outer corner, its inner one (the
side it turns to)."""

import numpy as np

from ..core import placement
from ..core import stairs as core_stairs
from ..core.units import format_length
from ..i18n import decimal_sep, refusal, t
from ..ifc import catalog
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, show_snap
from .bim_draw import _name, _PointTool, length_option, type_option

Z = np.array((0.0, 0.0, 1.0))
PLACINGS = ("two", "ready")                 # (0.435) by its foot and its way up; or ready, in one click
ANCHORS = ("center", "outside", "inside")   # (0.435) the point of its first step on the point clicked
ANGLES = (0, 90, 180, 270)


def _fmt(v):
    return format_length(v, decimal_sep())


class StairTool(_PointTool):
    name = "stair"
    keys_help = "keys.stair"
    accepts_typing = False

    @property
    def common_keys(self):
        if self.placing == "ready":                # (0.435) R turns it, Space its point, as a column's
            return frozenset(("x", "y", "n", "r", "shift+r", "space", "shift+space"))
        return frozenset(("x", "y", "n"))

    def common_key(self, name):
        if name in ("r", "shift+r"):
            self.angle = placement.turn(self.angle, 1 if name == "r" else -1)
            self.host.message(t("info.turned", a=self.angle))
        elif name in ("space", "shift+space"):
            k = (ANCHORS.index(self.anchor) + (1 if name == "space" else -1)) % len(ANCHORS)
            self.anchor = ANCHORS[k]
            self.host.message(t("info.stair_anchor", p=t("stairanchor." + self.anchor).lower()))
        else:
            return self.lock_key(name)
        self._again()
        return True

    def __init__(self, host):
        self.placing = "two"
        super().__init__(host)
        self.spec = catalog.BY_KEY["laje_15"]
        self.form = "straight"
        self.turn = "left"
        self.width = 1.00
        self.going = 0.28
        self.rise = None                   # (None: up to the storey above)
        self._foot = None
        self.angle = 90                    # (0.435) the way a ready stair goes up: degrees from the red axis
        self.anchor = "center"
        self._ready_at = None              # (the point under the mouse, a ready stair shown there)

    def _rise(self, z):
        return bim.stair_rise(self.doc, z) if self.rise is None else self.rise

    def options(self):
        out = [type_option(self.spec, "slab"),
               Option("placing", t("ctx.stair_placing"), "choice", self.placing,
                      tuple((p, t("stairplacing." + p)) for p in PLACINGS)),
               Option("form", t("ctx.stair_form"), "choice", self.form,
                      tuple((f, t("stairform." + f)) for f in core_stairs.FORMS)),
               Option("turn", t("ctx.stair_turn"), "choice", self.turn,
                      tuple((s, t("stairturn." + s)) for s in core_stairs.TURNS)),
               length_option("width", "props.width", self.width),
               length_option("going", "ctx.going", self.going),
               length_option("rise", "ctx.rise", self._rise(self.doc.work_level()))]
        if self.placing == "ready":
            out += [Option("angle", t("ctx.angle"), "choice", self.angle, tuple((a, "{}°".format(a)) for a in ANGLES)),
                    Option("anchor", t("ctx.stair_anchor"), "choice", self.anchor,
                           tuple((a, t("stairanchor." + a)) for a in ANCHORS))]
        return out

    def set_option(self, key, value):
        if key == "type":
            self.spec = catalog.BY_KEY[value]
        elif key == "placing" and value in PLACINGS:
            self.placing = value                   # (the bar shows its turn and its point then: _sync_context_bar)
            self.cancel()
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
        elif key == "angle":
            self.angle = int(value) % 360
        elif key == "anchor" and value in ANCHORS:
            self.anchor = value
        self._again()

    def _again(self):
        self.host.set_hint(self.hint())
        if self.placing == "ready" and self._ready_at is not None:
            self._show_ready(*self._ready_at)

    def _steps(self, z):
        n, h = core_stairs.risers(self._rise(z))
        return n, h

    def hint(self):
        z = self._foot[2] if self._foot is not None else self.doc.work_level()
        if self.placing == "ready":
            return t("hint.stair_ready", form=t("stairform." + self.form), w=_fmt(self.width), h=_fmt(self._rise(z)),
                     p=t("stairanchor." + self.anchor).lower())
        if self._foot is None:
            return t("hint.stair", form=t("stairform." + self.form), w=_fmt(self.width), h=_fmt(self._rise(z)))
        n, h = self._steps(z)
        return t("hint.stair_2", n=n, r=_fmt(h), g=_fmt(self.going), b=_fmt(2 * h + self.going))

    # ------------------------------------------------------------ (0.435) a ready stair

    def ready_foot(self, p):
        """(the middle of its first step, the way it goes up (2,)) of a ready stair with its anchor at p."""
        a = np.radians(self.angle)
        d = np.array((np.cos(a), np.sin(a)))
        left = np.array((-d[1], d[0]))
        inside = left if self.turn == "left" else -left     # (the side it turns to; a straight one's: the same)
        shift = {"center": 0.0, "outside": 1.0, "inside": -1.0}[self.anchor] * self.width / 2.0
        foot = np.asarray(p, dtype=float).copy()
        foot[:2] += inside * shift
        return foot, d

    def _outline(self, foot, d):
        pieces = core_stairs.layout(self.form, self._rise(foot[2]), self.width, self.going, self.turn)
        rings = core_stairs.footprint(pieces, self.width, self.going)
        segs = []
        c, s = d[0], d[1]
        for ring in rings:
            world = [foot + np.array((c * x_ - s * y_, s * x_ + c * y_, 0.01)) for x_, y_ in ring]
            segs += [q for a, b in zip(world, world[1:] + world[:1]) for q in (a, b)]
        return segs

    def _show_ready(self, p, snap):
        foot, d = self.ready_foot(p)
        segs = self._outline(foot, d)
        arrow = [foot + np.array((0.0, 0.0, 0.01)), foot + np.array((d[0], d[1], 0.0)) * 0.8 + np.array((0, 0, 0.01))]
        self.viewport.show_lines(segs + arrow, [PREVIEW] * (len(segs) + 2))
        show_snap(self.viewport, snap, p)
        self.viewport.show_tip(t("tip.stair_ready"), p)

    # ------------------------------------------------------------ the mouse

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, None if self._foot is None else self._foot[2], self._foot, modifiers)
        if p is None:
            return
        if self.placing == "ready":
            self._ready_at = (p, snap)
            self._show_ready(p, snap)
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
        if self.placing == "ready":
            foot, d = self.ready_foot(p)
            self._make(foot, d)
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
            bim.add_stair(self.doc, foot, d, self.spec, self.form, rise, self.width, self.going, self.turn,
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
        self._ready_at = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())

    def type_name(self):
        return _name(self.spec)
