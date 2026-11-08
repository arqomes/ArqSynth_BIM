"""Circle tool (0.150, Phase 7, step 1 — as SketchUp's): a click at the centre (on the ground, on a face, the snaps and
alignments), a second click — or the radius typed, "1,50" + Enter — makes a circle (a face of 24 sides by default;
the contextual bar changes it); a value typed right after corrects the last one's radius. Drawn on a face of a
volume, it divides that face (to push it in or pull it out); pushed, its sides are one smooth surface.

(0.458, Revit's «Draw» panel, the owner: «Faço também os polígonos e a elipse na Linha? — Sim, faz») The same tool
draws, chosen on the bar's row:
- Revit's inscribed polygon — the centre, then a corner (or the radius typed) — and circumscribed polygon — the
  centre, then the middle of a side (or the distance to it typed) —, their sides on the bar (3 to 16): a face, as the
  circle;
- Revit's ellipse: the centre, the end of one axis (or that half-axis typed), then how far the other reaches (or
  typed): a face, as the circle;
- Revit's partial ellipse: the two ends of an axis (the snaps, the alignments, its length typed), then how tall (or
  typed): half an ellipse, a curve picked whole — its two half-axes as temporary dimensions, typed over, its ends and
  top as grips (model/curve_edit), its Properties —; one that closes an outline with lines drawn before makes the
  face, as an arc."""

import math
from dataclasses import dataclass

import numpy as np

from ..core import curves, outline_shapes
from ..core.inference import ON_FACE
from ..core.mesh import PolyMesh
from ..core.sketch_geometry import (
    CIRCLE_SIDES, circle_mesh, imprint_polygon, polygon_mesh, ray_plane, rectangle_matrix, transform_point,
)
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, t
from ..model import imprint, line_faces
from ..model.document import AddObject, ReplaceMesh, SketchObject
from ..render.viewport import PREVIEW
from .base import (LEFT, RIGHT, Option, Tool, draw_option, drawing_dims, infer_point, inferred_style, point_from,
                   show_snap, start_plane, switch_draw)

SIDES = (12, 16, 24, 32, 48, 64)
POLY_SIDES = outline_shapes.SIDES       # (0.458) a polygon's sides: 3 to 16
ELLIPSE_PIECES = (16, 24, 32, 48, 64)   # (0.458) an ellipse's pieces (a partial one's too)
KINDS = ("circle", "poly_in", "poly_out", "ellipse", "ellipse_part")
POLYGONS = ("poly_in", "poly_out")
MIN_RADIUS = 0.001


@dataclass
class _Op:
    centre: np.ndarray
    n: np.ndarray
    u: np.ndarray
    v: np.ndarray
    face: tuple          # (obj_id, face index) when drawn on a face, else None
    radius: float = 0.0
    towards: np.ndarray = None      # where the first corner is (from the centre); an ellipse: its first axis
    axis: bool = False              # (0.458) an ellipse: its first half-axis clicked (the other one by the mouse)
    start: np.ndarray = None        # (0.458) a partial ellipse: where its axis starts (the first click)
    end: np.ndarray = None          # …and ends (the second)
    minor: float = 0.0              # (0.458) an ellipse's other half-axis (signed: to the left of the first)


def _fmt(value):
    return format_length(value, decimal_sep())


class CircleTool(Tool):
    name = "circle"
    accepts_typing = True

    def __init__(self, host):
        super().__init__(host)
        self.kind = "circle"            # (0.458) or Revit's polygons, ellipse, partial ellipse
        self.sides = CIRCLE_SIDES
        self.poly_sides = 6
        self.pieces = curves.ELLIPSE_SEGMENTS
        self._op = None
        self._last = None
        self._hover_xy = None
        self._cursor = None             # (0.458) a partial ellipse: the point under the mouse (its axis' end)

    # ------------------------------------------------------------ bar

    def options(self):
        opts = [draw_option(self.kind)]                     # (0.450: the drawing tools, as Revit's «Draw» panel)
        if self.kind in POLYGONS:
            opts.append(Option("sides", t("ctx.sides"), "choice", self.poly_sides,
                               tuple((s, str(s)) for s in POLY_SIDES)))
        elif self.kind in ("ellipse", "ellipse_part"):
            opts.append(Option("pieces", t("ctx.arc_segments"), "choice", self.pieces,
                               tuple((s, str(s)) for s in ELLIPSE_PIECES)))
        else:
            opts.append(Option("sides", t("ctx.circle_sides"), "choice", self.sides, tuple((s, str(s)) for s in SIDES)))
        return opts

    def take_draw(self, value):
        """(0.458) A circle, a polygon or an ellipse, from the bar's row."""
        if value in KINDS:
            self.kind = value
            self.cancel()

    def activate(self):
        self.kind = "circle"            # (the ribbon's Circle: a circle — the bar's row then says another, if it does)
        super().activate()

    def set_option(self, key, value):
        if key == "draw" and value in KINDS:
            self.take_draw(value)
        elif key == "draw":
            switch_draw(self, value)
            return
        elif key == "sides" and self.kind in POLYGONS:
            self.poly_sides = int(value)
        elif key == "sides":
            self.sides = int(value)
        elif key == "pieces":
            self.pieces = int(value)
        self._say()

    def hint(self):
        op = self._op
        if self.kind in POLYGONS:
            return t("hint.polygon.radius_" + self.kind[5:]) if op else \
                t("hint.polygon.centre_" + self.kind[5:], n=self.poly_sides)
        if self.kind == "ellipse":
            return t("hint.ellipse.minor") if op and op.axis else t("hint.ellipse.axis") if op else \
                t("hint.ellipse.centre")
        if self.kind == "ellipse_part":
            return t("hint.ellipse_part.height") if op and op.end is not None else \
                t("hint.ellipse_part.end") if op else t("hint.ellipse_part.start")
        return t("hint.circle.radius") if op else t("hint.circle.centre", n=self.sides)

    def _say(self):
        """Its step on the status bar, and what the Measurements box asks for (0.458: a half-axis, a length…)."""
        self.host.set_hint(self.hint())
        if hasattr(self.host, "vcb_title_changed"):
            self.host.vcb_title_changed()

    def vcb_title(self):
        if self.kind == "ellipse_part":
            return t("vcb.half_axis") if self._op is not None and self._op.end is not None else t("vcb.length")
        if self.kind == "ellipse":
            return t("vcb.half_axis")
        return t("vcb.radius")

    # ------------------------------------------------------------ mouse

    def _plane_point(self, x, y):
        op = self._op
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, op.centre, op.n)
        return p if p is not None else ray_plane(origin, direction, op.centre, -op.n)

    def pointer_move(self, x, y, modifiers):
        self._hover_xy = (x, y)
        if self._op is None:
            plane = start_plane(self.host, x, y, modifiers)
            show_snap(self.viewport, plane.snap if plane else None, plane.point if plane else None)
            return
        op = self._op
        if self.kind == "ellipse_part" and op.end is None:  # (0.458) the axis, as a line: snaps, alignments
            self._axis_move(x, y, modifiers)
            return
        if self.kind == "ellipse_part" or op.axis:         # (0.458) the other half-axis: how far the mouse is
            p = self._plane_point(x, y)
            if p is None:
                return
            op.minor = float((p - op.centre) @ self._left(op))
            self._ellipse_feedback(p)
            return
        snap, _s, _hit = infer_point(self.viewport, x, y, op.centre, modifiers, plane=(op.centre, op.n))
        if snap is not None and snap.kind != ON_FACE:
            edge = snap.point - (snap.point - op.centre).dot(op.n) * op.n
        else:
            snap = None
            edge = self._plane_point(x, y)
        if edge is None:
            return
        d = edge - op.centre
        op.radius = float(np.linalg.norm(d))
        op.towards = d / op.radius if op.radius > 1e-9 else op.u
        self._feedback(snap, edge)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        op = self._op
        if op is not None:
            if self.kind == "ellipse_part" and op.end is None:
                found = point_from(self.viewport, op.start, op.n, x, y, modifiers)
                if found is not None:
                    self._axis_end(self._on_plane(found[0]))
                return
            if self.kind == "ellipse" and not op.axis:
                self._axis_set()
                return
            self._finish()
            return
        plane = start_plane(self.host, x, y, modifiers)
        if plane is None:
            self.host.message(t("err.no_point"), warning=True)
            return
        self._op = self._new_op(plane)
        self.viewport.clear_overlays()
        self._say()

    def _new_op(self, plane, radius=0.0):
        p = np.asarray(plane.point, float)
        return _Op(p.copy(), np.asarray(plane.normal, float), np.asarray(plane.u, float), np.asarray(plane.v, float),
                   plane.face, radius=radius, start=p.copy() if self.kind == "ellipse_part" else None)

    # ------------------------------------------------------------ keyboard

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None or values[0] is None or values[0] <= MIN_RADIUS:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        value = float(values[0])
        op = self._op
        if self.kind in ("ellipse", "ellipse_part") and op is not None:      # (0.458) step by step
            if self.kind == "ellipse_part" and op.end is None:              # the axis' length, the way the mouse goes
                if self._cursor is None or np.linalg.norm(self._cursor - op.start) < 1e-9:
                    self.host.message(t("hint.line.direction"), warning=True)
                    return
                d = (self._cursor - op.start) / np.linalg.norm(self._cursor - op.start)
                self._axis_end(op.start + d * value)
            elif self.kind == "ellipse" and not op.axis:                    # the first half-axis
                op.radius = value
                if op.towards is None:
                    op.towards = op.u
                self._axis_set()
            else:                                                           # the other one (on the mouse's side)
                op.minor = math.copysign(value, op.minor or 1.0)
                self._finish()
            return
        if op is not None:
            op.radius = value
            self._finish()
            return
        last = self._last
        if last is not None and self.doc.last_command() is last[0] and last[2] in ("circle",) + POLYGONS:
            self.doc.undo()                       # (SketchUp: a value typed right after corrects the last circle)
            op = last[1]
            op.radius = value
            kind, self.kind = self.kind, last[2]
            self._create(op)
            self.kind = kind
            return
        if self.kind in ("ellipse", "ellipse_part"):
            self.host.message(self.hint(), warning=True)
            return
        plane = start_plane(self.host, *self._hover_xy) if self._hover_xy else None
        if plane is None:
            self.host.message(self.hint(), warning=True)
            return
        self._op = self._new_op(plane, radius=value)
        self._finish()

    def cancel(self):
        self._op = None
        self._cursor = None
        self.viewport.clear_overlays()
        self._say()
        self.host.set_vcb("")

    # ------------------------------------------------------------ (0.458) ellipses, step by step

    def _on_plane(self, p):
        op = self._op
        p = np.asarray(p, dtype=float)
        return p - float((p - op.centre) @ op.n) * op.n

    def _left(self, op):
        """The way the other half-axis goes (to the left of the first, about the normal)."""
        a = op.end - op.start if self.kind == "ellipse_part" else op.towards
        w = np.cross(op.n, a)
        return w / max(float(np.linalg.norm(w)), 1e-12)

    def _axis_move(self, x, y, modifiers):
        op = self._op
        found = point_from(self.viewport, op.start, op.n, x, y, modifiers)
        if found is None:
            return
        self._cursor, tip, marker, line = found
        self._cursor = self._on_plane(self._cursor)
        self.viewport.show_polygon([], segments=[op.start, self._cursor], colors=[line, line])
        drawing_dims(self.viewport, op.start, self._cursor, op.n)
        self.viewport.show_marker(self._cursor, marker)
        self.viewport.show_tip(tip, self._cursor if tip else None)
        self.host.set_vcb(_fmt(float(np.linalg.norm(self._cursor - op.start))))

    def _axis_end(self, end):
        """A partial ellipse's axis ends here: the mouse then says how tall it is."""
        op = self._op
        if np.linalg.norm(end - op.start) < 2 * MIN_RADIUS:
            return
        op.end = np.asarray(end, dtype=float).copy()
        op.centre = (op.start + op.end) / 2
        op.minor = 0.0
        self.viewport.clear_overlays()
        self._say()
        self.host.set_vcb("")

    def _axis_set(self):
        """An ellipse's first half-axis clicked (or typed): the mouse then says how far the other reaches."""
        op = self._op
        if op.radius < MIN_RADIUS or op.towards is None:
            return
        op.axis = True
        op.minor = 0.0
        self.viewport.clear_overlays()
        self._say()
        self.host.set_vcb("")

    def _ellipse_curve(self, op):
        if self.kind == "ellipse_part":
            return curves.half_ellipse(op.start, op.end, op.minor, op.n, self.pieces)     # (the bar's Segments)
        return curves.ellipse_curve(op.centre, op.n, op.centre + op.towards * op.radius, op.minor, 0.0, 360.0,
                                    self.pieces)

    def _ellipse_feedback(self, p):
        op = self._op
        if abs(op.minor) < MIN_RADIUS:
            self.viewport.clear_overlays()
            return
        pts = curves.ellipse_points(self._ellipse_curve(op))
        ring = pts + pts[:1] if self.kind == "ellipse" else pts
        segs = [q for a, b in zip(ring, ring[1:]) for q in (a, b)]
        foot = op.centre + self._left(op) * op.minor
        segs += [op.centre, foot]
        if self.kind == "ellipse":
            segs += [op.centre, op.centre + op.towards * op.radius]
        else:
            segs += [op.start, op.end]
        self.viewport.show_polygon(pts if self.kind == "ellipse" else [], segments=segs, colors=[PREVIEW] * len(segs))
        drawing_dims(self.viewport, op.centre, foot, op.n)
        self.viewport.show_marker(foot, PREVIEW)
        self.viewport.show_tip("", None)
        self.host.set_vcb(_fmt(abs(op.minor)))

    # ------------------------------------------------------------ making it

    def _finish(self):
        op = self._op
        if self.kind in ("ellipse", "ellipse_part"):
            if abs(op.minor) < MIN_RADIUS:
                return
        elif op.radius < MIN_RADIUS or not self._local(op):
            return
        self._op = None
        self._cursor = None
        self.viewport.clear_overlays()
        if self.kind == "ellipse_part":
            self._make_partial(op)
        else:
            self._create(op)
        self._say()

    def _frame(self, op):
        """The circle's frame: its local X towards where its first corner is (an ellipse: along its first axis)."""
        x = op.towards if op.towards is not None else op.u
        x = x - x.dot(op.n) * op.n
        x = x / np.linalg.norm(x) if np.linalg.norm(x) > 1e-9 else op.u
        return rectangle_matrix(op.centre, x, np.cross(op.n, x))

    def _local(self, op):
        """The outline's corners in its frame: the circle's, the polygon's (0.458), the ellipse's (0.458)."""
        if self.kind in POLYGONS:
            loop = outline_shapes.regular((0.0, 0.0), (op.radius, 0.0), self.poly_sides, self.kind == "poly_in")
            return [] if loop is None else [(x, y, 0.0) for x, y in loop[0]]
        if self.kind == "ellipse":
            b = abs(op.minor) if op.axis else op.radius
            return [(op.radius * math.cos(2 * math.pi * k / self.pieces), b * math.sin(2 * math.pi * k / self.pieces),
                     0.0) for k in range(self.pieces)]
        return [tuple(v) for v in circle_mesh(op.radius, self.sides).verts]

    def _mesh(self, op):
        if self.kind == "circle":
            return circle_mesh(op.radius, self.sides)
        return polygon_mesh([(x, y) for x, y, _z in self._local(op)])

    def _corners(self, op):
        m = self._frame(op)
        return [transform_point(m, p) for p in self._local(op)]

    def _create(self, op):
        cmd = self._imprint(op) if op.face else None
        label = t("cmd.ellipse" if self.kind == "ellipse" else "cmd.polygon" if self.kind in POLYGONS else "cmd.circle")
        if cmd is None:
            obj = SketchObject(t("obj.name", n=self.doc.next_number()), self._frame(op), self._mesh(op))
            cmd = self.doc.execute(AddObject(obj, label))
        self._last = (cmd, op, self.kind)
        self.host.set_vcb(_fmt(op.radius))
        if self.kind in POLYGONS:
            self.host.message(t("info.polygon_" + self.kind[5:], n=self.poly_sides, r=_fmt(op.radius)))
        elif self.kind == "ellipse":
            self.host.message(t("info.ellipse", a=_fmt(op.radius), b=_fmt(abs(op.minor))))
        else:
            self.host.message(t("info.circle", r=_fmt(op.radius), n=self.sides))

    def _make_partial(self, op):
        """(0.458) Half an ellipse: a curve picked whole; across a sketch's face it divides it, closing an outline with
        lines drawn before it makes the face (as an arc)."""
        curve = self._ellipse_curve(op)
        pts = curves.ellipse_points(curve)
        pairs = [(k, k + 1) for k in range(len(pts) - 1)]
        obj = SketchObject(t("obj.ellipse", n=self.doc.next_number()), np.eye(4), PolyMesh(pts, lines=pairs),
                           curve=curve)
        label = t("cmd.ellipse")
        split = imprint.split_by_path(self.doc, pts, None, self.viewport.is_shown)
        if split is not None and split.start == 0:
            cmd = self.doc.execute(split.command)
            self.host.message(t("info.split_host", wall=split.host) if split.host else t("info.split", n=split.faces))
        else:
            closed = line_faces.close_with(self.doc, obj, (op.centre, op.n), label,
                                           view_dir=self.viewport.view_direction())
            if closed is not None:
                cmd = self.doc.last_command()
                self.host.message(t("info.ellipse_face", a="{:.2f}".format(closed.area).replace(".", decimal_sep())))
            else:
                cmd = self.doc.execute(AddObject(obj, label))
                self.host.message(t("info.ellipse_part", a=_fmt(float(np.linalg.norm(op.end - op.start))),
                                    b=_fmt(abs(op.minor))))
        self._last = (cmd, op, self.kind)
        self.host.set_vcb(_fmt(abs(op.minor)))

    def _imprint(self, op):
        """Drawn inside a face of a volume: that face divided (SketchUp), to push it in or pull it out."""
        obj = self.doc.get(op.face[0])
        if obj is None or obj.is_bim:
            return None
        to_local = np.linalg.inv(obj.matrix)
        mesh = obj.mesh.copy()
        if imprint_polygon(mesh, op.face[1], [transform_point(to_local, c) for c in self._corners(op)]) is None:
            return None
        label = t("cmd.ellipse" if self.kind == "ellipse" else "cmd.polygon" if self.kind in POLYGONS else "cmd.circle")
        return self.doc.execute(ReplaceMesh(obj.id, obj.mesh, mesh, label))

    def _feedback(self, snap, edge):
        op = self._op
        ring = self._corners(op)
        if not ring:
            self.viewport.clear_overlays()
            return
        segs = [q for a, b in zip(ring, ring[1:] + ring[:1]) for q in (a, b)] + [op.centre, edge]
        self.viewport.show_polygon(ring if self.kind != "ellipse" else [], segments=segs,
                                   colors=[PREVIEW] * len(segs))
        drawing_dims(self.viewport, op.centre, edge, op.n)
        if snap is not None:
            tip, marker, _line = inferred_style(snap)
            self.viewport.show_marker(edge, marker)
            self.viewport.show_tip(tip, edge)
        else:
            show_snap(self.viewport, None, None)
        self.host.set_vcb(_fmt(op.radius))
