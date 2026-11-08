"""Curtain wall (0.117): drawn as a wall, by its line — a click at its start and one at its end (or its length
typed) — its height and the most between its mullions and between its transoms on the contextual bar; the
mullions and transoms come out equal (IfcCurtainWall). (0.252) Started inside a curved wall, it runs round the
wall's arc (through the point clicked, within the wall's ends) and goes into it.

(0.436, the addon's «Fachada de vidro» circular and «por face») «Forma» on the bar: Linha, as always; Arco — three
clicks, its start, its end and a point the arc goes through (as the Wall's arc), free of any wall; Por face — over an
upright face of a volume or an element the rectangle that frames it (with the faces beside it on its plane) shows,
and a click puts a curtain wall there, as long and as high as it, just outside it."""

import math

import numpy as np

from ..core import arcs
from ..core.sketch_geometry import ray_plane
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, drawing_dims, show_snap
from .bim_draw import MIN_LENGTH, _PointTool, length_option

Z = np.array((0.0, 0.0, 1.0))
SHAPES = ("line", "arc", "face")            # (0.436)
OFF_FACE = 0.075                            # m: a curtain wall by a face stands this far out of it (half its depth)


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
        self.shape = "line"          # (0.436) line | arc (three clicks) | face
        self._arc = []               # (0.436) an arc's start and end clicked…
        self._free = None            # …and the arc through the mouse: (centre, radius, start, sweep)
        self._face = None            # (0.436) the face under the mouse: (a, b, height, normal) of its rectangle

    def options(self):
        return [Option("shape", t("ctx.cw_shape"), "choice", self.shape, tuple((s, t("cwshape." + s)) for s in SHAPES)),
                length_option("height", "ctx.height", self.height),
                length_option("mullions", "ctx.mullions", self.mullions),
                length_option("transoms", "ctx.transoms", self.transoms)]

    def set_option(self, key, value):
        if key == "shape" and value in SHAPES:
            self.shape = value
            self.cancel()
        elif key == "height" and value >= 0.3:
            self.height = value
        elif key == "mullions" and value >= 0.3:
            self.mullions = value
        elif key == "transoms" and value >= 0.3:
            self.transoms = value
        self.host.set_hint(self.hint())

    def hint(self):
        if self.shape == "face":
            return t("hint.curtain_face", m=_fmt(self.mullions), t=_fmt(self.transoms))
        if self.shape == "arc":
            return t(("hint.curtain_arc_start", "hint.curtain_arc_end", "hint.curtain_arc_bulge")[min(len(self._arc), 2)],
                     h=_fmt(self.height))
        if self._curve is not None:
            return t("hint.curtain_wall_arc", wall=self._wall_name() or "")
        if self._start is not None:
            name = self._wall_name()
            return t("hint.curtain_wall_embed", wall=name) if name else t("hint.curtain_wall_2")
        return t("hint.curtain_wall", h=_fmt(self.height), m=_fmt(self.mullions), t=_fmt(self.transoms))

    def vcb_title(self):
        return t("vcb.length")

    # ------------------------------------------------------------ (0.436) by a face; along a free arc

    def _face_at(self, x, y):
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None
        return bim.upright_face(self.doc, hit[0], hit[1], hit[2])

    def _face_ends(self, found):
        """(start, end, height) of the curtain wall over a face's rectangle: just outside it."""
        a, b, height, n = found
        return a + n * OFF_FACE, b + n * OFF_FACE, height

    def _show_face(self, found):
        a, b, height = self._face_ends(found)
        ring = [a, b, b + Z * height, a + Z * height]
        segs = [q for u, v in zip(ring, ring[1:] + ring[:1]) for q in (u, v)]
        length = float(np.linalg.norm((b - a)[:2]))
        from ..ifc.curtain_walls import divisions
        for s in divisions(length, self.mullions)[1:-1]:          # (its mullions and transoms, as they will be)
            q = a + (b - a) * (s / length)
            segs += [q, q + Z * height]
        for z in divisions(height, self.transoms)[1:-1]:
            segs += [a + Z * z, b + Z * z]
        self.viewport.show_polygon(ring, segments=segs, colors=[PREVIEW] * len(segs))
        self.viewport.show_tip("{} × {}".format(_fmt(length), _fmt(height)), ring[2])

    def _arc_lines(self, curve, z):
        centre, r, start, sweep = curve
        n = max(int(math.ceil(abs(math.degrees(sweep)) / arcs.SEGMENT_DEG)), 1)
        base = [np.array((centre[0] + r * math.cos(start + sweep * k / n), centre[1] + r * math.sin(start + sweep * k / n),
                          z)) for k in range(n + 1)]
        top = [q + Z * self.height for q in base]
        segs = [q for line in (base, top) for u, v in zip(line, line[1:]) for q in (u, v)]
        return segs + [base[0], top[0], base[-1], top[-1]]

    def _free_move(self, x, y, modifiers):
        first = self._arc[0] if self._arc else None
        p, snap = self._point(x, y, None if first is None else first[2], self._arc[-1] if self._arc else None,
                              modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        if not self._arc:
            show_snap(self.viewport, snap, p)
            return
        if len(self._arc) == 1:                    # (the chord, start -> end)
            self._end = p
            self.viewport.show_lines([self._arc[0], p], [PREVIEW, PREVIEW])
            drawing_dims(self.viewport, self._arc[0], p)
            show_snap(self.viewport, snap, p)
            self.host.set_vcb(_fmt(float(np.linalg.norm((p - self._arc[0])[:2]))))
            return
        self._free = arcs.arc_through(self._arc[0], self._arc[1], p)
        if self._free is None:
            self.viewport.show_lines([self._arc[0], self._arc[1]], [PREVIEW, PREVIEW])
            return
        segs = self._arc_lines(self._free, float(first[2]))
        self.viewport.show_lines(segs, [PREVIEW] * len(segs))
        show_snap(self.viewport, snap, p)
        self.host.set_vcb(_fmt(self._free[1] * abs(self._free[3])))

    def _free_down(self, x, y, modifiers):
        if len(self._arc) < 2:
            p = self._end if self._arc else self._point(x, y, modifiers=modifiers)[0]
            if p is not None and (not self._arc or np.linalg.norm((p - self._arc[0])[:2]) >= MIN_LENGTH):
                self._arc.append(np.array((p[0], p[1], self._arc[0][2] if self._arc else p[2])))
                self._end = None
                self.host.set_hint(self.hint())
            return
        if self._free is None:
            return
        centre, r, start, sweep = self._free
        if r * abs(sweep) < MIN_LENGTH:
            return
        z = float(self._arc[0][2])
        self._make(None, None, self.height, arc=(np.array((centre[0], centre[1], z)), r, start, sweep),
                   length=r * abs(sweep))

    def _make(self, start, end, height, arc=None, length=0.0):
        try:
            guid = bim.add_curtain_wall(self.doc, start, end, height, self.mullions, self.transoms,
                                        storey=self.doc.active_storey, arc=arc)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self.cancel()
            return
        message = t("info.curtain_wall", l=_fmt(length), h=_fmt(height))
        host = self.doc.ifc.host_wall(guid)
        if host is not None:
            message += " " + t("info.curtain_embedded", wall=self.doc.ifc.by_guid(host).Name or "")
        self.host.message(message)
        self.cancel()

    # ------------------------------------------------------------ the mouse

    def pointer_move(self, x, y, modifiers):
        if self.shape == "face":                   # (0.436)
            self._face = self._face_at(x, y)
            if self._face is None:
                self.viewport.clear_overlays()
                hit = self.viewport.pick_point(x, y)
                if hit is not None:
                    self.viewport.show_tip(t("tip.curtain_face_none"), hit[2])
                return
            self._show_face(self._face)
            return
        if self.shape == "arc":
            self._free_move(x, y, modifiers)
            return
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
            q = self._under_mouse(x, y, self._start[2])                # (0.474: not a facet's corner — see there)
            q = p if q is None else q
            self._show_arc(self._arc_to(math.atan2(q[1] - centre[1], q[0] - centre[0])))
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
        if self.shape == "face":                   # (0.436) a click on an upright face: over it
            found = self._face_at(x, y)
            if found is None:
                self.host.message(t("err.curtain_face_none"), warning=True)
                return
            a, b, height = self._face_ends(found)
            self._make(a, b, height, length=float(np.linalg.norm((b - a)[:2])))
            return
        if self.shape == "arc":
            self._free_down(x, y, modifiers)
            return
        if self._start is None:
            p, _snap = self._point(x, y, modifiers=modifiers)
            if p is not None:
                self._begin(p, self._under_mouse(x, y, p[2]))
            return
        if self._curve is not None:
            self._finish_arc(self._sweep)
        elif self._end is not None:
            self._finish(self._end)

    def _under_mouse(self, x, y, z):
        """(0.474) The point under the mouse on the level z, as it is — no snap. In a curved wall the snaps took the
        corners of its facets (the faces' edges are drawn as short straight pieces): the start and the end jumped a
        few degrees and onto a face (its radius 4,90 m, not the 5,00 m clicked); the arc's own ends are kept anyway
        (the sweep stays within the wall's)."""
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), Z)
        return p if p is not None else ray_plane(origin, direction, np.array((0.0, 0.0, z)), -Z)

    def _begin(self, p, raw=None):
        """The start clicked — (0.252) inside a curved wall: put on its arc through it (0.474: through the point
        under the mouse itself, `raw`), within its ends."""
        self._start = p
        found = self.doc.ifc.curved_wall_at(raw if raw is not None else p, self.height)
        if found is None and raw is not None:
            found = self.doc.ifc.curved_wall_at(p, self.height)
        elif found is not None and raw is not None:
            p = np.array((raw[0], raw[1], p[2]))
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
        if self.shape == "face":
            return
        if self.shape == "arc":                    # (0.436) after its start: the chord; after its end: the radius
            if not self._arc:
                if self._hover is None:
                    return
                self._arc.append(self._hover[0].copy())
            if len(self._arc) == 1:
                a = self._arc[0]
                d = (self._end - a) if self._end is not None else np.array((1.0, 0.0, 0.0))
                d = np.array((d[0], d[1], 0.0))
                d = d / np.linalg.norm(d) if np.linalg.norm(d) > 1e-9 else np.array((1.0, 0.0, 0.0))
                self._arc.append(a + d * abs(values[0]))
                self._end = None
                self.host.set_hint(self.hint())
                return
            side = self._hover[0] if self._hover is not None else self._arc[1]
            self._free = arcs.arc_with_radius(self._arc[0], self._arc[1], abs(values[0]), side)
            if self._free is None:
                self.host.message(t("err.wall_arc_radius", c=_fmt(float(np.linalg.norm(
                    (self._arc[1] - self._arc[0])[:2])) / 2)), warning=True)
                return
            self._free_down(0, 0, None)
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
        self._arc, self._free, self._face = [], None, None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
