"""Circle tool (0.150, Phase 7, step 1 — as SketchUp's): a click at the centre (on the ground, on a face, the snaps and
alignments), a second click — or the radius typed, "1,50" + Enter — makes a circle (a face of 24 sides by default;
the contextual bar changes it); a value typed right after corrects the last one's radius. Drawn on a face of a
volume, it divides that face (to push it in or pull it out); pushed, its sides are one smooth surface."""

from dataclasses import dataclass

import numpy as np

from ..core.inference import ON_FACE
from ..core.sketch_geometry import (
    CIRCLE_SIDES, circle_mesh, imprint_polygon, ray_plane, rectangle_matrix, transform_point,
)
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, t
from ..model.document import AddObject, ReplaceMesh, SketchObject
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, Tool, drawing_dims, infer_point, inferred_style, show_snap, start_plane

SIDES = (12, 16, 24, 32, 48, 64)
MIN_RADIUS = 0.001


@dataclass
class _Op:
    centre: np.ndarray
    n: np.ndarray
    u: np.ndarray
    v: np.ndarray
    face: tuple          # (obj_id, face index) when drawn on a face, else None
    radius: float = 0.0
    towards: np.ndarray = None      # where the first corner is (from the centre)


def _fmt(value):
    return format_length(value, decimal_sep())


class CircleTool(Tool):
    name = "circle"
    accepts_typing = True

    def __init__(self, host):
        super().__init__(host)
        self.sides = CIRCLE_SIDES
        self._op = None
        self._last = None
        self._hover_xy = None

    def options(self):
        return [Option("sides", t("ctx.circle_sides"), "choice", self.sides, tuple((s, str(s)) for s in SIDES))]

    def set_option(self, key, value):
        if key == "sides":
            self.sides = int(value)
        self.host.set_hint(self.hint())

    def hint(self):
        return t("hint.circle.radius") if self._op else t("hint.circle.centre", n=self.sides)

    def vcb_title(self):
        return t("vcb.radius")

    def pointer_move(self, x, y, modifiers):
        self._hover_xy = (x, y)
        if self._op is None:
            plane = start_plane(self.host, x, y, modifiers)
            show_snap(self.viewport, plane.snap if plane else None, plane.point if plane else None)
            return
        op = self._op
        snap, _s, _hit = infer_point(self.viewport, x, y, op.centre, modifiers, plane=(op.centre, op.n))
        if snap is not None and snap.kind != ON_FACE:
            edge = snap.point - (snap.point - op.centre).dot(op.n) * op.n
        else:
            snap = None
            origin, direction = self.viewport.ray(x, y)
            edge = ray_plane(origin, direction, op.centre, op.n)
            if edge is None:
                edge = ray_plane(origin, direction, op.centre, -op.n)
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
        if self._op is not None:
            self._finish()
            return
        plane = start_plane(self.host, x, y, modifiers)
        if plane is None:
            self.host.message(t("err.no_point"), warning=True)
            return
        self._op = _Op(np.asarray(plane.point, float), np.asarray(plane.normal, float), np.asarray(plane.u, float),
                       np.asarray(plane.v, float), plane.face)
        self.host.set_hint(self.hint())

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None or values[0] is None or values[0] <= MIN_RADIUS:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        radius = float(values[0])
        if self._op is not None:
            self._op.radius = radius
            self._finish()
            return
        last = self._last
        if last is not None and self.doc.last_command() is last[0]:
            self.doc.undo()                       # (SketchUp: a value typed right after corrects the last circle)
            op = last[1]
            op.radius = radius
            self._create(op)
            return
        plane = start_plane(self.host, *self._hover_xy) if self._hover_xy else None
        if plane is None:
            self.host.message(t("hint.circle.centre", n=self.sides), warning=True)
            return
        self._op = _Op(np.asarray(plane.point, float), np.asarray(plane.normal, float), np.asarray(plane.u, float),
                       np.asarray(plane.v, float), plane.face, radius=radius)
        self._finish()

    def cancel(self):
        self._op = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    def _finish(self):
        op = self._op
        if op.radius < MIN_RADIUS:
            return
        self._op = None
        self.viewport.clear_overlays()
        self._create(op)
        self.host.set_hint(self.hint())

    def _frame(self, op):
        """The circle's frame: its local X towards where its first corner is."""
        x = op.towards if op.towards is not None else op.u
        x = x - x.dot(op.n) * op.n
        x = x / np.linalg.norm(x) if np.linalg.norm(x) > 1e-9 else op.u
        return rectangle_matrix(op.centre, x, np.cross(op.n, x))

    def _corners(self, op):
        m = self._frame(op)
        return [transform_point(m, p) for p in circle_mesh(op.radius, self.sides).verts]

    def _create(self, op):
        cmd = self._imprint(op) if op.face else None
        if cmd is None:
            obj = SketchObject(t("obj.name", n=self.doc.next_number()), self._frame(op), circle_mesh(op.radius, self.sides))
            cmd = self.doc.execute(AddObject(obj, t("cmd.circle")))
        self._last = (cmd, op)
        self.host.set_vcb(_fmt(op.radius))
        self.host.message(t("info.circle", r=_fmt(op.radius), n=self.sides))

    def _imprint(self, op):
        """Drawn inside a face of a volume: that face divided (SketchUp), to push it in or pull it out."""
        obj = self.doc.get(op.face[0])
        if obj is None or obj.is_bim:
            return None
        to_local = np.linalg.inv(obj.matrix)
        mesh = obj.mesh.copy()
        if imprint_polygon(mesh, op.face[1], [transform_point(to_local, c) for c in self._corners(op)]) is None:
            return None
        return self.doc.execute(ReplaceMesh(obj.id, obj.mesh, mesh, t("cmd.circle")))

    def _feedback(self, snap, edge):
        op = self._op
        ring = self._corners(op)
        segs = [q for a, b in zip(ring, ring[1:] + ring[:1]) for q in (a, b)] + [op.centre, edge]
        self.viewport.show_polygon(ring, segments=segs, colors=[PREVIEW] * len(segs))
        drawing_dims(self.viewport, op.centre, edge, op.n)
        if snap is not None:
            tip, marker, _line = inferred_style(snap)
            self.viewport.show_marker(edge, marker)
            self.viewport.show_tip(tip, edge)
        else:
            show_snap(self.viewport, None, None)
        self.host.set_vcb(_fmt(op.radius))
