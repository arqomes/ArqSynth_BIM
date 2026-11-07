"""Arc tool (0.373, SketchUp's 'A' — the owner: «preciso de ferramenta de arco nesse grupo»).

- Two points (the default, SketchUp's 2-point arc): a click where it starts, a click where it ends (the snaps and
  alignments, or the chord's length typed), then the mouse pulls its bulge out — it clicks into a half circle and
  into the arc tangent to the line it starts from —; a click, or the bulge typed ("0,5"), or its radius ("2r").
- Centre: a click at the centre, a click where it starts (its radius), then the angle it turns (15° steps; typed).
- Three points: where it starts, a point it passes through, where it ends.
- Sector: as Centre, closed by its two radii into a face (a pie).
The number of pieces is on the contextual bar ("12s" typed right after an arc changes it). On a sketch's face, an arc
from its outline to its outline divides it; one that closes an outline with lines drawn before makes the face, as
SketchUp's. The arc is picked whole and stays an arc (its radius, angle and pieces in its Properties); a value typed
right after it corrects it."""

import math
from dataclasses import dataclass

import numpy as np

from ..core import curves
from ..core.lines import polygon_frame
from ..core.mesh import PolyMesh
from ..core.sketch_geometry import ray_plane
from ..core.temp_dims import TempDim
from ..core.units import format_angle, format_length, parse_angle, parse_lengths
from ..i18n import decimal_sep, t
from ..model import imprint, line_edit, line_faces
from ..model.document import AddObject, SketchObject
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, Tool, draw_option, drawing_dims, point_from, show_snap, start_plane, switch_draw

MODES = ("two", "centre", "three", "pie")
SEGMENTS = (0, 6, 8, 12, 16, 24, 32, 48)          # 0: by its angle (a piece every 15°)
SNAP_PX = 10                # the bulge this near a half circle / the tangent arc (on the screen): taken
MIN_SIZE = 0.001
SNAPPED_COLOURS = {"half": (0.80, 0.10, 0.70, 1.0),            # magenta: a half circle (as SketchUp's)
                   "tangent": (0.00, 0.65, 0.80, 1.0)}         # cyan: tangent to the line it starts from


def _fmt(value):
    return format_length(value, decimal_sep())


@dataclass
class _Op:
    """An arc being drawn: its plane and the points clicked so far."""
    normal: np.ndarray
    points: list                # world points clicked (2 points: start, end; centre: centre, start; 3 points…)
    face: tuple = None          # the face it started on (obj_id, face index), or None
    arc: tuple = None           # (centre, start, angle) as it would be now
    snapped: str = ""           # "half" | "tangent" | "" — what the bulge clicked into
    tangent: np.ndarray = None  # the way the line it starts from goes on (looked for once, at the second click)


class ArcTool(Tool):
    name = "arc"
    accepts_typing = True
    typed_suffixes = "rs"       # "2r": a radius; "12s": its pieces (once a number is started)

    def __init__(self, host):
        super().__init__(host)
        self.mode = "two"
        self.segments = 0
        self._op = None
        self._cursor = None         # the last point under the mouse (world)
        self._hover_xy = None
        self._last = None           # (command, the arc's curve) of the arc just made: a value typed after corrects it

    # ------------------------------------------------------------ bar

    def options(self):
        return [draw_option("arc"),                         # (0.450: the drawing tools, as Revit's «Draw» panel)
                Option("mode", t("ctx.arc_mode"), "choice", self.mode, tuple((m, t("arcmode." + m)) for m in MODES)),
                Option("segments", t("ctx.arc_segments"), "choice", self.segments,
                       tuple((s, t("arcseg.auto") if s == 0 else str(s)) for s in SEGMENTS))]

    def set_option(self, key, value):
        if key == "draw":
            switch_draw(self, value)
            return
        if key == "mode" and value in MODES:
            self.mode = value
            self.cancel()
        elif key == "segments":
            self.segments = int(value)
        self.host.set_hint(self.hint())

    def hint(self):
        n = len(self._op.points) if self._op else 0
        return t("hint.arc.{}{}".format(self.mode, n))

    def vcb_title(self):
        if self._op is None:
            return t("vcb.length")
        if self.mode in ("centre", "pie"):
            return t("vcb.radius") if len(self._op.points) == 1 else t("vcb.angle")
        return t("vcb.length") if len(self._op.points) == 1 else t("vcb.bulge")

    # ------------------------------------------------------------ geometry

    def _pieces(self, angle):
        return self.segments or curves.segments_for(angle)

    def _plane_point(self, x, y):
        op = self._op
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, op.points[0], op.normal)
        if p is None:
            p = ray_plane(origin, direction, op.points[0], -op.normal)
        return p

    def _on_plane(self, p):
        """A point found (it may be a snap off the plane) brought onto the arc's plane."""
        op = self._op
        p = np.asarray(p, dtype=float)
        return p - float((p - op.points[0]) @ op.normal) * op.normal

    def _tangent(self, a):
        """The way a loose line ending at `a` goes on beyond it (an arc starting there leaves tangent to it), or
        None."""
        for obj in self.doc.objects.values():
            if not line_edit.is_lines(obj):
                continue
            world = [obj.matrix[:3, :3] @ v + obj.matrix[:3, 3] for v in obj.mesh.verts]
            for i, j in obj.mesh.lines:
                for p, q in ((world[i], world[j]), (world[j], world[i])):
                    if np.linalg.norm(q - a) < line_edit.TOL and np.linalg.norm(q - p) > 1e-9:
                        return (q - p) / np.linalg.norm(q - p)
        return None

    def _bulge_arc(self, x, y):
        """Two points clicked: the arc whose bulge the mouse shows (a half circle, the tangent one, near them)."""
        op = self._op
        a, b = op.points
        p = self._plane_point(x, y)
        if p is None:
            return None
        bulge = curves.bulge_of(a, b, p, op.normal)
        op.snapped = ""
        half = float(np.linalg.norm(b - a)) / 2
        mid = (a + b) / 2
        left = np.cross(op.normal, b - a)
        left = left / max(np.linalg.norm(left), 1e-12)
        ends = {"half": math.copysign(half, bulge or 1.0)}
        if op.tangent is not None:                    # (the arc leaving a along the line it starts from)
            on = curves.tangent_bulge(a, b, op.tangent, op.normal)
            if on is not None:
                ends = {"tangent": on, **ends}
        here = self.viewport.project(mid + left * bulge)
        for kind, value in ends.items():
            there = self.viewport.project(mid + left * value)
            if np.hypot(here[0] - there[0], here[1] - there[1]) <= SNAP_PX:
                bulge, op.snapped = value, kind
                break
        return curves.arc_by_bulge(a, b, bulge, op.normal), mid + left * bulge

    def _angle_arc(self, x, y):
        """Centre and start clicked: the arc turning to the mouse, in 15° steps near them."""
        op = self._op
        c, s = op.points
        p = self._plane_point(x, y)
        if p is None:
            return None
        u, w = s - c, p - c
        angle = math.degrees(math.atan2(float(np.cross(u, w) @ op.normal), float(u @ w)))
        prev = op.arc[2] if op.arc is not None else 0.0
        while angle - prev > 180:                     # (it goes on round, past a half turn, as the mouse goes)
            angle -= 360
        while prev - angle > 180:
            angle += 360
        angle = max(-360.0, min(360.0, angle))
        op.snapped = ""
        step = round(angle / 15.0) * 15.0
        if abs(angle - step) < 2.0:
            angle, op.snapped = step, "step"
        return (c, s, angle), p

    def _three_arc(self, x, y):
        """Start and a point on the way clicked: the arc through them to the mouse."""
        op = self._op
        found = point_from(self.viewport, op.points[1], op.normal, x, y)
        if found is None:
            return None
        end = self._on_plane(found[0])
        through = curves.arc_through(op.points[0], op.points[1], end)
        if through is None:
            return None
        centre, normal, angle = through
        if float(normal @ op.normal) < 0:             # (about the plane's own normal: the other way round)
            angle = -angle
        op.snapped = ""
        return (centre, op.points[0], angle), end

    def _arc_points(self, arc):
        centre, start, angle = arc
        return curves.arc_points(centre, self._op.normal, start, angle, self._pieces(angle))

    # ------------------------------------------------------------ mouse

    def pointer_move(self, x, y, modifiers):
        self._hover_xy = (x, y)
        op = self._op
        if op is None:
            plane = start_plane(self.host, x, y, modifiers)
            show_snap(self.viewport, plane.snap if plane else None, plane.point if plane else None)
            return
        if len(op.points) == 1:
            found = point_from(self.viewport, op.points[0], op.normal, x, y, modifiers)
            if found is None:
                return
            self._cursor, tip, marker, line = found
            self._cursor = self._on_plane(self._cursor)
            a = op.points[0]
            segs = [a, self._cursor]
            if self.mode in ("centre", "pie") and np.linalg.norm(self._cursor - a) > 1e-9:
                r = float(np.linalg.norm(self._cursor - a))       # (the whole circle it is on, faint)
                ring = curves.arc_points(a, op.normal, self._cursor, 360.0, 48)
                segs += [q for p, s in zip(ring, ring[1:] + ring[:1]) for q in (p, s)]
                self.host.set_vcb(_fmt(r))
            else:
                self.host.set_vcb(_fmt(float(np.linalg.norm(self._cursor - a))))
            self.viewport.show_polygon([], segments=segs, colors=[line] * 2 + [PREVIEW] * (len(segs) - 2))
            drawing_dims(self.viewport, a, self._cursor, op.normal)
            self.viewport.show_marker(self._cursor, marker)
            self.viewport.show_tip(tip, self._cursor if tip else None)
            return
        if self.mode == "two":
            made = self._bulge_arc(x, y)
        elif self.mode == "three":
            made = self._three_arc(x, y)
        else:
            made = self._angle_arc(x, y)
        if made is None or made[0] is None:
            return
        op.arc, self._cursor = made
        self._preview()

    def _preview(self):
        op = self._op
        pts = self._arc_points(op.arc)
        centre, start, angle = op.arc
        segs = [q for a, b in zip(pts, pts[1:]) for q in (a, b)]
        if self.mode == "pie":
            segs += [centre, pts[0], centre, pts[-1]]
        elif self.mode == "centre":
            segs += [centre, pts[0]]
        colours = [SNAPPED_COLOURS.get(op.snapped, PREVIEW)] * len(segs)
        self.viewport.show_polygon(pts if self.mode == "pie" else [], segments=segs, colors=colours)
        radius = float(np.linalg.norm(start - centre))
        if self.mode == "two":
            a, b = op.points
            mid = (a + b) / 2
            bulge_end = pts[len(pts) // 2] if len(pts) % 2 else (pts[len(pts) // 2 - 1] + pts[len(pts) // 2]) / 2
            self.viewport.show_temp_dims([TempDim(mid, bulge_end, op.normal)] if np.linalg.norm(bulge_end - mid) > 1e-6
                                         else [])
            bulge = float(np.linalg.norm(bulge_end - mid))
            self.host.set_vcb(_fmt(bulge))
            tip = t("snap.arc_" + op.snapped) if op.snapped else t("info.arc_radius", r=_fmt(radius))
        elif self.mode == "three":
            self.viewport.show_temp_dims([])
            self.host.set_vcb(_fmt(radius))
            tip = t("info.arc_radius", r=_fmt(radius))
        else:
            self.viewport.show_temp_dims([])
            self.host.set_vcb(format_angle(abs(angle), decimal_sep()))
            tip = format_angle(abs(angle), decimal_sep())
        self.viewport.show_marker(self._cursor, PREVIEW)
        self.viewport.show_tip(tip, self._cursor)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        op = self._op
        if op is None:
            plane = start_plane(self.host, x, y, modifiers)
            if plane is None:
                self.host.message(t("err.no_point"), warning=True)
                return
            self._op = _Op(np.asarray(plane.normal, float), [np.asarray(plane.point, float).copy()], plane.face)
            self.viewport.clear_overlays()
            self.host.set_hint(self.hint())
            return
        if len(op.points) == 1:
            found = point_from(self.viewport, op.points[0], op.normal, x, y, modifiers)
            if found is None or np.linalg.norm(self._on_plane(found[0]) - op.points[0]) < MIN_SIZE:
                return
            op.points.append(self._on_plane(found[0]))
            op.arc = None
            op.tangent = self._tangent(op.points[0]) if self.mode == "two" else None
            self.viewport.clear_overlays()
            self.host.set_hint(self.hint())
            return
        if op.arc is not None:
            self._make(op.arc)

    # ------------------------------------------------------------ keyboard

    def typed(self, text):
        raw = text.strip().lower()
        op = self._op
        if raw.endswith("s"):                         # (its pieces: now, or the arc just made)
            try:
                n = int(float(raw[:-1].replace(",", ".")))
            except ValueError:
                n = 0
            if n < curves.MIN_SEGMENTS:
                self.host.message(t("err.bad_value", t=text), warning=True)
                return
            self.segments = n
            self.host.message(t("info.arc_segments", n=n))
            if op is None and self._redo_last(segments=n):
                return
            if op is not None and op.arc is not None:
                self._preview()
            return
        radius = raw.endswith("r")
        if op is not None and len(op.points) == 2 and self.mode in ("centre", "pie"):
            value = parse_angle(raw)
            if value is None:
                self.host.message(t("err.bad_angle", t=text), warning=True)
                return
            c, s = op.points
            turn = op.arc[2] if op.arc is not None else 1.0
            self._make((c, s, math.copysign(min(abs(value), 360.0), turn or 1.0)))
            return
        values = parse_lengths(raw[:-1] if radius else raw, 1)
        if values is None or values[0] is None or values[0] <= 0:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        value = float(values[0])
        if op is None:
            if not self._redo_last(value=value, radius=radius):
                self.host.message(t("hint.arc." + self.mode + "0"), warning=True)
            return
        if len(op.points) == 1:                       # the chord (or the radius) that long, the way the mouse shows
            if self._cursor is None or np.linalg.norm(self._cursor - op.points[0]) < 1e-9:
                self.host.message(t("hint.line.direction"), warning=True)
                return
            d = (self._cursor - op.points[0]) / np.linalg.norm(self._cursor - op.points[0])
            op.points.append(op.points[0] + d * value)
            op.arc = None
            op.tangent = self._tangent(op.points[0]) if self.mode == "two" else None
            self.host.set_hint(self.hint())
            return
        if self.mode == "two":
            a, b = op.points
            side = curves.bulge_of(a, b, self._cursor, op.normal) if self._cursor is not None else 1.0
            bulge = curves.bulge_for_radius(a, b, value, side) if radius else math.copysign(value, side or 1.0)
            if bulge is None:
                self.host.message(t("err.arc_radius", r=_fmt(float(np.linalg.norm(b - a)) / 2)), warning=True)
                return
            self._make(curves.arc_by_bulge(a, b, bulge, op.normal))
            return
        self.host.message(t("hint.arc.three2"), warning=True)

    def _redo_last(self, value=None, radius=False, segments=None):
        """A value typed right after an arc: its bulge (or radius, or pieces) corrected. True if it was that."""
        last = self._last
        if last is None or self.doc.last_command() is not last[0]:
            return False
        arc, normal, mode, chord = last[1:]
        if mode == "two" and value is not None:
            a, b = chord
            side = curves.bulge_of(a, b, curves.arc_points(arc[0], normal, arc[1], arc[2], 4)[2], normal)
            bulge = curves.bulge_for_radius(a, b, value, side) if radius else math.copysign(value, side or 1.0)
            if bulge is None:
                return False
            arc = curves.arc_by_bulge(a, b, bulge, normal)
        elif mode in ("centre", "pie") and value is not None:
            arc = (arc[0], arc[0] + (arc[1] - arc[0]) / np.linalg.norm(arc[1] - arc[0]) * value, arc[2])
        elif segments is None:
            return False
        self.doc.undo()
        self._op = _Op(normal, [np.asarray(p, float) for p in chord], None)
        mode_was, self.mode = self.mode, mode
        self._make(arc)
        self.mode = mode_was
        return True

    def cancel(self):
        self._op = None
        self._cursor = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    # ------------------------------------------------------------ making it

    def _make(self, arc):
        op = self._op
        centre, start, angle = (np.asarray(arc[0], float), np.asarray(arc[1], float), float(arc[2]))
        radius = float(np.linalg.norm(start - centre))
        if radius < MIN_SIZE or abs(angle) < 1e-6:
            return
        pts = curves.arc_points(centre, op.normal, start, angle, self._pieces(angle))
        curve = curves.arc_curve(centre, op.normal, start, angle, self._pieces(angle), pie=self.mode == "pie")
        chord = [p.copy() for p in op.points]
        mode, normal = self.mode, op.normal.copy()
        self._op = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        label = t("cmd.arc")
        if mode == "pie":
            whole = abs(abs(angle) - 360.0) < 1e-9
            frame = polygon_frame(pts if whole else [centre] + pts, view_dir=self.viewport.view_direction())
            if frame is None:
                return
            obj = SketchObject(t("obj.name", n=self.doc.next_number()), frame[0],
                               PolyMesh(frame[1], [list(range(len(frame[1])))]))
            cmd = self.doc.execute(AddObject(obj, label))
            self.host.message(t("info.arc_pie", r=_fmt(radius), a=format_angle(abs(angle), decimal_sep())))
        else:
            whole = abs(abs(angle) - 360.0) < 1e-9
            pairs = [(k, (k + 1) % len(pts)) for k in range(len(pts) if whole else len(pts) - 1)]
            obj = SketchObject(t("obj.arc", n=self.doc.next_number()), np.eye(4), PolyMesh(pts, lines=pairs),
                               curve=curve)
            split = None if whole else imprint.split_by_path(self.doc, pts, None, self.viewport.is_shown)
            if split is not None and split.start == 0:     # (across a sketch's face: the face divided along it)
                cmd = self.doc.execute(split.command)
                self.host.message(t("info.split_host", wall=split.host) if split.host
                                  else t("info.split", n=split.faces))
            else:
                closed = line_faces.close_with(self.doc, obj, (centre, normal), label,
                                               view_dir=self.viewport.view_direction())
                if closed is not None:
                    cmd = self.doc.last_command()
                    self.host.message(t("info.arc_face", a="{:.2f}".format(closed.area).replace(".", decimal_sep())))
                else:
                    cmd = self.doc.execute(AddObject(obj, label))
                    self.host.message(t("info.arc_made", r=_fmt(radius), a=format_angle(abs(angle), decimal_sep()),
                                        n=len(pairs)))
        self._last = (cmd, (centre, start, angle), normal, mode, chord)
        self.host.set_vcb(_fmt(radius))
