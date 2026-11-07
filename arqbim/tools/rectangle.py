"""Rectangle tool (SketchUp 'R'): click, click (or drag); type '3,20;4,50' + Enter.

Both corners use inferences (endpoint, midpoint, edge, face, origin) and the
'square' inference. After finishing, typing new values + Enter resizes the
last rectangle. A rectangle drawn inside a face of a volume splits that face.
"""

from dataclasses import dataclass

import numpy as np

from ..core.inference import ON_FACE, square_inference
from ..core.sketch_geometry import (
    imprint_polygon, ray_plane, rectangle_matrix, rectangle_mesh, transform_point,
)
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, t
from ..model.document import AddObject, ReplaceMesh, SketchObject
from ..render.viewport import AXIS_U, AXIS_V
from .base import (
    LEFT, RIGHT, SQUARE_COLOR, Tool, draw_option, infer_point, inferred_style, moved_enough, outside_dim, show_snap,
    show_start_reference, start_plane, start_reference, switch_draw,
)

MIN_SIDE = 0.001


@dataclass
class _Op:
    a: np.ndarray
    n: np.ndarray
    u: np.ndarray
    v: np.ndarray
    face: tuple          # (obj_id, face_index) when drawn on a face, else None
    press: tuple
    du: float = 0.0
    dv: float = 0.0
    square: bool = False


@dataclass
class _Last:
    cmd: object
    a: np.ndarray
    u: np.ndarray
    v: np.ndarray
    du: float
    dv: float
    name: str
    face: tuple


def _fmt(value):
    return format_length(value, decimal_sep())


class RectangleTool(Tool):
    name = "rectangle"
    accepts_typing = True

    def __init__(self, host):
        super().__init__(host)
        self._op = None
        self._last = None
        self._hover_xy = None
        self._hover = None          # before the first click: the StartPlane under the mouse…
        self._start_ref = None      # …and where a typed distance would start from (base.start_reference)

    def hint(self):
        return t("hint.rect.end") if self._op else t("hint.rect.start")

    def options(self):
        return [draw_option("rectangle")]                   # (0.450: the drawing tools, as Revit's «Draw» panel)

    def set_option(self, key, value):
        if key == "draw":
            switch_draw(self, value)

    def vcb_title(self):
        return t("vcb.dims")

    # ------------------------------------------------------------ mouse

    def pointer_move(self, x, y, modifiers):
        self._hover_xy = (x, y)
        if self._op is None:
            plane = start_plane(self.host, x, y, modifiers)
            show_snap(self.viewport, plane.snap if plane else None, plane.point if plane else None)
            self._hover = plane
            self._start_ref = start_reference(plane.snap) if plane is not None else None
            show_start_reference(self.viewport, self._start_ref, plane.point if plane else None,
                                 plane.normal if plane else None)
            return
        op = self._op
        snap, _s, _hit = infer_point(self.viewport, x, y, None, modifiers, plane=(op.a, op.n))   # (snaps, alignments)
        corner = None
        if snap is not None and snap.kind != ON_FACE:
            corner = snap.point - (snap.point - op.a).dot(op.n) * op.n  # inferred point, onto the plane
            self.viewport.show_alignments(snap.lines, snap.point)
        else:
            snap = None
            self.viewport.show_alignments()
            origin, direction = self.viewport.ray(x, y)
            corner = ray_plane(origin, direction, op.a, op.n)
            if corner is None:
                corner = ray_plane(origin, direction, op.a, -op.n)
        if corner is not None:
            d = corner - op.a
            du, dv = float(d.dot(op.u)), float(d.dot(op.v))
            op.du, op.dv, op.square = square_inference(du, dv) if snap is None else (du, dv, False)
        self._feedback(snap)

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
        self._op = _Op(plane.point, plane.normal, plane.u, plane.v, plane.face, press=(x, y))
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self._feedback(None)

    def pointer_up(self, x, y, button, modifiers):
        if button == LEFT and self._op is not None and moved_enough(self._op.press, (x, y)):
            self._finish()

    # ------------------------------------------------------------ keyboard

    def typed(self, text):
        values = parse_lengths(text, 2)
        if values is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        a, b = values
        if self._op is not None:
            op = self._op
            if a is not None:
                op.du = (-1.0 if op.du < 0 else 1.0) * a
            if b is not None:
                op.dv = (-1.0 if op.dv < 0 else 1.0) * b
            self._finish()
            return
        last = self._last
        if last is not None and self.doc.last_command() is last.cmd:
            # SketchUp: a value typed right after finishing corrects the last rectangle.
            self.doc.undo()
            du = last.du if a is None else (-1.0 if last.du < 0 else 1.0) * a
            dv = last.dv if b is None else (-1.0 if last.dv < 0 else 1.0) * b
            self._create(last.a, last.u, last.v, du, dv, last.name, last.face)
            return
        if self._start_ref is not None and self._hover is not None and a is not None and b is None:
            # before the first click, on an alignment or an edge: the first corner that far from its point
            src, direction = self._start_ref
            plane = self._hover
            self._op = _Op(src + direction * a, plane.normal, plane.u, plane.v, plane.face, press=self._hover_xy)
            self.viewport.clear_overlays()
            self.host.set_hint(self.hint())
            self.host.message(t("info.start_typed", l=_fmt(a)))
            return
        # Forgiving: sizes typed before the first click start the rectangle under the mouse.
        plane = start_plane(self.host, *self._hover_xy) if self._hover_xy else None
        if plane is None:
            self.host.message(t("hint.rect.start"), warning=True)
            return
        self._op = _Op(plane.point, plane.normal, plane.u, plane.v, plane.face, press=self._hover_xy,
                       du=a if a is not None else 1.0, dv=b if b is not None else (a or 1.0))
        self._finish()

    def cancel(self):
        self._op = None
        self._start_ref = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    # ------------------------------------------------------------ internals

    def _finish(self):
        op = self._op
        if abs(op.du) < MIN_SIDE or abs(op.dv) < MIN_SIDE:
            return  # zero-size click: keep waiting for the opposite corner
        self._op = None
        self.viewport.clear_overlays()
        name = "" if op.face else t("obj.name", n=self.doc.next_number())
        self._create(op.a, op.u, op.v, op.du, op.dv, name, op.face)
        self.host.set_hint(self.hint())

    def _create(self, a, u, v, du, dv, name, face):
        cmd = self._imprint(a, u, v, du, dv, face) if face else None
        if cmd is None:
            name = name or t("obj.name", n=self.doc.next_number())
            obj = SketchObject(name, rectangle_matrix(a, u, v), rectangle_mesh(du, dv))
            cmd = self.doc.execute(AddObject(obj, t("cmd.rect")))
        self._last = _Last(cmd, a, u, v, du, dv, name, face)
        dims = "{} × {}".format(_fmt(abs(du)), _fmt(abs(dv)))
        self.host.set_vcb(dims)
        self.host.message(t("info.next_pp", a=_fmt(abs(du)), b=_fmt(abs(dv))))

    def _imprint(self, a, u, v, du, dv, face):
        """Rectangle drawn inside a face of a volume: split that face (SketchUp
        behaviour) so it can be pulled out (balcony) or pushed in (recess).
        Returns the command, or None when the rectangle does not fit in the face."""
        obj = self.doc.get(face[0])
        if obj is None or obj.is_bim:
            return None  # on an IFC element the rectangle stays a sketch lying on it
        to_local = np.linalg.inv(obj.matrix)
        corners = [a, a + u * du, a + u * du + v * dv, a + v * dv]
        mesh = obj.mesh.copy()
        if imprint_polygon(mesh, face[1], [transform_point(to_local, c) for c in corners]) is None:
            return None
        return self.doc.execute(ReplaceMesh(obj.id, obj.mesh, mesh, t("cmd.rect")))

    def _feedback(self, snap):
        op = self._op
        a, u, v = op.a, op.u * op.du, op.v * op.dv
        c = [a, a + u, a + u + v, a + v]
        segs = [c[0], c[1], c[3], c[2], c[1], c[2], c[0], c[3]]
        colors = [AXIS_U] * 4 + [AXIS_V] * 4
        if op.square:
            segs += [c[0], c[2]]
            colors += [SQUARE_COLOR] * 2
        self.viewport.show_polygon(c, segments=segs, colors=colors)
        dims = "{} × {}".format(_fmt(abs(op.du)), _fmt(abs(op.dv)))
        middle = (c[0] + c[2]) / 2
        self.viewport.show_temp_dims([outside_dim(c[0], c[1], middle, op.n), outside_dim(c[1], c[2], middle, op.n)])
        if snap is not None:
            tip, marker, _line = inferred_style(snap)
            self.viewport.show_marker(c[2], marker)
            self.viewport.show_tip(tip, c[2])
        elif op.square:
            self.viewport.show_marker(c[2], SQUARE_COLOR)
            self.viewport.show_tip(t("snap.square"), c[2])
        else:
            show_snap(self.viewport, None, None)
        self.host.set_vcb(dims)
