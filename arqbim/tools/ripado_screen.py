"""Free-standing slatted screen (0.441, the addon's «Ripado» with «Apoio: Livre»): drawn as a wall — a click at its
start and one at its end (or its length typed) —, its height and its slats (upright or level, their width, thickness
and pitch, a frame, battens on its back) on the bar, as the Ripado's on a wall (tools/ripado.py); under the mouse its
outline and its slats. A divider in a room, a brise outside."""

import numpy as np

from ..core import surfaces
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, drawing_dims, show_snap
from .bim_draw import MIN_LENGTH, _PointTool, length_option

Z = np.array((0.0, 0.0, 1.0))
MAX_SHOWN = 400


def _fmt(v):
    return format_length(v, decimal_sep())


class RipadoScreenTool(_PointTool):
    name = "ripado_screen"
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.chain"

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.height = 2.40
        self.direction = "vertical"
        self.width, self.depth, self.pitch = 0.04, 0.04, 0.08
        self.frame, self.battens = 0.0, 0
        self._start = self._end = None

    def options(self):
        return [length_option("height", "ctx.height", self.height),
                Option("direction", t("props.slat_direction"), "choice", self.direction,
                       (("vertical", t("slat.vertical")), ("horizontal", t("slat.horizontal")))),
                length_option("width", "props.slat_width", self.width),
                length_option("depth", "props.slat_depth", self.depth),
                length_option("pitch", "props.slat_pitch", self.pitch),
                length_option("frame", "props.ripado_frame", self.frame),
                Option("battens", t("props.ripado_battens"), "choice", str(self.battens),
                       tuple((str(n), t("ripado.no_battens") if n == 0 else str(n)) for n in range(0, 7)))]

    def set_option(self, key, value):
        if key == "height" and 0.1 <= value <= 20.0:
            self.height = float(value)
        elif key == "direction" and value in ("vertical", "horizontal"):
            self.direction = value
        elif key == "battens":
            try:
                self.battens = max(0, min(surfaces.MAX_BATTENS, int(value)))
            except (TypeError, ValueError):
                pass
        elif key in ("width", "depth") and 0.003 <= value <= 0.30:
            setattr(self, key, float(value))
        elif key == "pitch" and value > 0.005:
            self.pitch = float(value)
        elif key == "frame" and 0.0 <= value < 1.0:
            self.frame = float(value)
        if self.pitch < self.width + 1e-6:
            self.host.message(t("warn.slat_pitch", w=_fmt(self.width), p=_fmt(self.pitch)), warning=True)
        self.host.set_hint(self.hint())

    def pattern(self):
        return {"direction": self.direction, "width": self.width, "gap": max(0.0, self.pitch - self.width),
                "thickness": self.depth, "frame": self.frame, "battens": self.battens}

    def hint(self):
        if self._start is None:
            return t("hint.ripado_screen", h=_fmt(self.height), w=_fmt(self.width), p=_fmt(self.pitch))
        return t("hint.ripado_screen_2")

    def vcb_title(self):
        return t("vcb.length")

    # ------------------------------------------------------------ the mouse

    def _show(self, a, b):
        ring = [a, b, b + Z * self.height, a + Z * self.height]
        segs = [q for u, v in zip(ring, ring[1:] + ring[:1]) for q in (u, v)]
        length = float(np.linalg.norm((b - a)[:2]))
        from shapely.geometry import box
        d = dict(self.pattern())
        try:
            _band, _battens, slats, _inner = surfaces.ripado_parts(box(0.0, 0.0, length, self.height), d)
        except ValueError:
            slats = []
        x = (b - a) / max(length, 1e-9)
        if len(slats) <= MAX_SHOWN:
            for u0, v0, u1, v1 in slats:
                if self.direction == "horizontal":
                    segs += [a + x * u0 + Z * v0, a + x * u1 + Z * v0]
                else:
                    segs += [a + x * u0 + Z * v0, a + x * u0 + Z * v1]
        self.viewport.show_polygon(ring, segments=segs, colors=[PREVIEW] * len(segs))
        drawing_dims(self.viewport, a, b)
        self.host.set_vcb(_fmt(length))

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, None if self._start is None else self._start[2], self._start, modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        if self._start is None:
            show_snap(self.viewport, snap, p)
            return
        b = np.array((p[0], p[1], self._start[2]))
        if np.linalg.norm((b - self._start)[:2]) < 1e-6:
            return
        self._end = b
        self._show(self._start, b)
        show_snap(self.viewport, snap, p)

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
        values = parse_lengths(text, 1)
        if values is None or values[0] is None:
            if values is None:
                self.host.message(t("err.bad_value", t=text), warning=True)
            return
        if self._start is None:
            return
        d = (self._end - self._start) if self._end is not None else np.array((1.0, 0.0, 0.0))
        d = np.array((d[0], d[1], 0.0))
        d = d / np.linalg.norm(d) if np.linalg.norm(d) > 1e-9 else np.array((1.0, 0.0, 0.0))
        self._finish(self._start + d * abs(values[0]))

    def _finish(self, end):
        if np.linalg.norm((end - self._start)[:2]) < MIN_LENGTH:
            return
        end = np.array((end[0], end[1], self._start[2]))
        try:
            guid = bim.add_ripado_screen(self.doc, self._start, end, self.height, self.pattern(),
                                         storey=self.doc.active_storey)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self.cancel()
            return
        n = len(self.doc.ifc._screen_pieces(self.doc.ifc.screen_params(guid))[2])
        self.host.message(t("info.ripado_screen", name=self.doc.get(guid).name, n=n,
                            l=_fmt(float(np.linalg.norm((end - self._start)[:2])))))
        self.cancel()

    def cancel(self):
        self._start = self._end = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
