"""Curtain wall (0.117): drawn as a wall, by its line — a click at its start and one at its end (or its length
typed) — its height and the most between its mullions and between its transoms on the contextual bar; the
mullions and transoms come out equal (IfcCurtainWall). (0.252) Started inside a curved wall, it runs round the
wall's arc (through the point clicked, within the wall's ends) and goes into it."""

import math

import numpy as np

from ..core import arcs
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, drawing_dims, show_snap
from .bim_draw import MIN_LENGTH, _PointTool, length_option

Z = np.array((0.0, 0.0, 1.0))


def _fmt(v):
    return format_length(v, decimal_sep())


class CurtainWallTool(_PointTool):
    name = "curtain_wall"
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.chain"

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.height = bim.WALL_HEIGHT
        self.mullions = 1.50
        self.transoms = 1.00
        self._start = None
        self._end = None
        self._wall = None            # (0.188) the wall the line drawn lies in (the curtain wall goes into it)
        self._curve = None           # (0.252) started in a curved wall: (its guid, centre, radius, start, sweep)…
        self._sweep = 0.0            # …and the arc drawn so far from the start (radians, + counter-clockwise)

    def options(self):
        return [length_option("height", "ctx.height", self.height),
                length_option("mullions", "ctx.mullions", self.mullions),
                length_option("transoms", "ctx.transoms", self.transoms)]

    def set_option(self, key, value):
        if key == "height" and value >= 0.3:
            self.height = value
        elif key == "mullions" and value >= 0.3:
            self.mullions = value
        elif key == "transoms" and value >= 0.3:
            self.transoms = value
        self.host.set_hint(self.hint())

    def hint(self):
        if self._curve is not None:
            return t("hint.curtain_wall_arc", wall=self._wall_name() or "")
        if self._start is not None:
            name = self._wall_name()
            return t("hint.curtain_wall_embed", wall=name) if name else t("hint.curtain_wall_2")
        return t("hint.curtain_wall", h=_fmt(self.height), m=_fmt(self.mullions), t=_fmt(self.transoms))

    def vcb_title(self):
        return t("vcb.length")

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, None if self._start is None else self._start[2], self._start, modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        if self._start is None:
            show_snap(self.viewport, snap, p)
            return
        self._end = p
        if self._curve is not None:                                    # (0.252) round the curved wall
            centre = self._curve[1]
            self._show_arc(self._arc_to(math.atan2(p[1] - centre[1], p[0] - centre[0])))
            show_snap(self.viewport, snap, p)
            return
        if np.linalg.norm((p - self._start)[:2]) < 1e-6:
            return
        a, b = self._start, np.array((p[0], p[1], self._start[2]))
        ring = [a, b, b + Z * self.height, a + Z * self.height]
        segs = [q for u, v in zip(ring, ring[1:] + ring[:1]) for q in (u, v)]
        self.viewport.show_polygon(ring, segments=segs, colors=[PREVIEW] * len(segs))
        drawing_dims(self.viewport, a, b)
        show_snap(self.viewport, snap, p)
        self.host.set_vcb(_fmt(float(np.linalg.norm((b - a)[:2]))))
        wall = self.doc.ifc.wall_for_line(a, b, self.height)          # (0.188) drawn in a wall: embedded in it
        if wall != self._wall:
            self._wall = wall
            self.host.set_hint(self.hint())

    def _wall_name(self):
        e = self.doc.ifc.by_guid(self._wall) if self._wall else None
        return e.Name if e is not None else None

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self._start is None:
            p, _snap = self._point(x, y, modifiers=modifiers)
            if p is not None:
                self._begin(p)
            return
        if self._curve is not None:
            self._finish_arc(self._sweep)
        elif self._end is not None:
            self._finish(self._end)

    def _begin(self, p):
        """The start clicked — (0.252) inside a curved wall: put on its arc through it, within its ends."""
        self._start = p
        found = self.doc.ifc.curved_wall_at(p, self.height)
        if found is not None:
            guid, centre, r, start, sweep = found
            _c, radius, _s, _w, _h, thickness = self.doc.ifc.curved_wall_params(guid)
            r = min(max(r, radius - thickness / 2), radius + thickness / 2)
            angle = math.atan2(p[1] - centre[1], p[0] - centre[0])
            if not arcs.is_full(sweep):                                # (a hair past an end: at the end)
                angle = arcs.angle_along(start, sweep, r, arcs.along_at(start, sweep, r, angle))
            self._curve = (guid, centre, r, start, sweep)
            self._wall, self._sweep = guid, 0.0
            self._start = np.array((centre[0] + r * math.cos(angle), centre[1] + r * math.sin(angle), p[2]))
        self.host.set_hint(self.hint())

    def _start_angle(self):
        centre = self._curve[1]
        return math.atan2(self._start[1] - centre[1], self._start[0] - centre[0])

    def _arc_to(self, angle):
        """The sweep from the start round the curved wall to `angle`: within the wall's ends (beyond them: to the
        nearer); in a whole circle, the shorter way."""
        _g, _c, r, start, sweep = self._curve
        a0 = self._start_angle()
        if arcs.is_full(sweep):
            return (angle - a0 + math.pi) % arcs.FULL - math.pi
        turn = 1.0 if sweep >= 0 else -1.0
        return turn * (arcs.along_at(start, sweep, r, angle) - arcs.along_at(start, sweep, r, a0)) / r

    def _show_arc(self, sweep):
        self._sweep = sweep
        _g, centre, r, _start, _sweep = self._curve
        z = float(self._start[2])
        a0 = self._start_angle()
        n = max(int(math.ceil(abs(math.degrees(sweep)) / arcs.SEGMENT_DEG)), 1)
        base = [np.array((centre[0] + r * math.cos(a0 + sweep * k / n), centre[1] + r * math.sin(a0 + sweep * k / n),
                          z)) for k in range(n + 1)]
        top = [q + Z * self.height for q in base]
        segs = [q for line in (base, top) for u, v in zip(line, line[1:]) for q in (u, v)]
        segs += [base[0], top[0], base[-1], top[-1]]
        self.viewport.show_lines(segs, [PREVIEW] * len(segs))
        self.host.set_vcb(_fmt(r * abs(sweep)))

    def _finish_arc(self, sweep):
        _g, centre, r, _start, _sweep = self._curve
        if r * abs(sweep) < MIN_LENGTH:
            return
        arc = (np.array((centre[0], centre[1], self._start[2])), r, self._start_angle(), sweep)
        try:
            guid = bim.add_curtain_wall(self.doc, None, None, self.height, self.mullions, self.transoms,
                                        storey=self.doc.active_storey, arc=arc)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self.cancel()
            return
        message = t("info.curtain_wall", l=_fmt(r * abs(sweep)), h=_fmt(self.height))
        host = self.doc.ifc.host_wall(guid)
        if host is not None:
            message += " " + t("info.curtain_embedded", wall=self.doc.ifc.by_guid(host).Name or "")
        self.host.message(message)
        self.cancel()

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None or values[0] is None:
            if values is None:
                self.host.message(t("err.bad_value", t=text), warning=True)
            return
        if self._start is None:
            if self._hover is None:
                return
            self._begin(self._hover[0].copy())
        if self._curve is not None:                                    # (0.252) that long round the arc
            r, sweep = self._curve[2], self._curve[4]
            self._finish_arc(math.copysign(abs(values[0]) / r, self._sweep or sweep))
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
            guid = bim.add_curtain_wall(self.doc, self._start, end, self.height, self.mullions, self.transoms,
                                        storey=self.doc.active_storey)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self.cancel()
            return
        message = t("info.curtain_wall", l=_fmt(float(np.linalg.norm((end - self._start)[:2]))), h=_fmt(self.height))
        host = self.doc.ifc.host_wall(guid)
        if host is not None:                                           # (0.188)
            message += " " + t("info.curtain_embedded", wall=self.doc.ifc.by_guid(host).Name or "")
        self.host.message(message)
        self.cancel()

    def cancel(self):
        self._start = self._end = self._wall = self._curve = None
        self._sweep = 0.0
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
