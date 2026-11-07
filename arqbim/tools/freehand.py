"""Freehand and Bézier curves (0.373 — the owner: «linha livre, curvas de Bézier»).

Freehand (SketchUp's): press where it starts (on the ground or on a face) and drag; it follows the mouse on that
plane and, let go, keeps a point where it bends (core/curves.simplify). Ending where it began — or crossing itself —
closes a face, as a closed outline of lines does.

Bézier (as the pen of a drawing program): a click puts a corner point; pressing and dragging puts a smooth one, its
tangent pulled out the way the mouse goes (the other side mirrored). The curve follows the mouse to the next point.
Enter, the right button, Esc or a second click on the last point end it; a click on the first point closes it — a
face. Picked with Select, its points and tangents have grips that change its shape (tools/select.py, curve grips).
Both are picked whole and closing an outline with lines drawn before makes the face, as SketchUp's.

(0.411, the owner: «a curva Bézier não é uma curva, mas uma linha reta. Esperava nós na linha que podem ser movidos
criando a curva — faça como o Blender») As Blender's: a click puts a smooth point whose tangents are worked out by
themselves («Auto» — core/curves.auto_handles), so the curve passes smoothly through every point clicked (the mouse
too, while drawing); pressed and dragged, its tangent pulled by hand, as before; Alt and a click, a corner. Picked
with Select, a «+» halfway along each span: dragged, a new point there and the curve bends; a point moved keeps its
automatic tangents (and its neighbours' follow)."""

import numpy as np

from ..core import curves
from ..core.mesh import PolyMesh
from ..core.sketch_geometry import ray_plane
from ..i18n import decimal_sep, t
from ..model import line_faces
from ..model.document import AddObject, SketchObject
from ..render.viewport import PREVIEW
from .base import (LEFT, RIGHT, Option, Tool, draw_option, moved_enough, point_from, show_snap, start_plane,
                   switch_draw)

CLOSE_PX = 12               # the end this near the start (on the screen): closed
STEP_PX = 3.0               # a freehand point kept every this many pixels while dragging
STEPS = (6, 8, 12, 16, 24)  # Bézier: pieces between two points


def _curve_object(doc, points, curve, closed):
    pts = [np.asarray(p, dtype=float) for p in points]
    if closed and len(pts) > 2 and np.linalg.norm(pts[0] - pts[-1]) < 1e-9:
        pts = pts[:-1]
    pairs = [(k, k + 1) for k in range(len(pts) - 1)] + ([(len(pts) - 1, 0)] if closed and len(pts) > 2 else [])
    return SketchObject(t("obj." + curve["kind"], n=doc.next_number()), np.eye(4), PolyMesh(pts, lines=pairs),
                        curve=curve)


def put_curve(tool, obj, plane, label, closed_key, made_key, **kw):
    """The curve sketch put in the document: the faces it closes made with it (line_faces), else as it is."""
    closed = line_faces.close_with(tool.doc, obj, plane, label, view_dir=tool.viewport.view_direction())
    if closed is not None:
        tool.host.message(t(closed_key, a="{:.2f}".format(closed.area).replace(".", decimal_sep())))
        return tool.doc.last_command()
    cmd = tool.doc.execute(AddObject(obj, label))
    tool.host.message(t(made_key, **kw))
    return cmd


class FreehandTool(Tool):
    name = "freehand"

    def __init__(self, host):
        super().__init__(host)
        self._reset()

    def _reset(self):
        self._plane = None          # (point, normal) drawn on
        self._pts = []              # world points so far
        self._last_xy = None
        self._drawing = False

    def hint(self):
        return t("hint.freehand.drag" if self._drawing else "hint.freehand.start")

    def options(self):
        return [draw_option("freehand")]                    # (0.450: the drawing tools, as Revit's «Draw» panel)

    def set_option(self, key, value):
        if key == "draw":
            switch_draw(self, value)

    def _on_plane(self, x, y):
        origin, direction = self.viewport.ray(x, y)
        point, normal = self._plane
        p = ray_plane(origin, direction, point, normal)
        return p if p is not None else ray_plane(origin, direction, point, -normal)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        plane = start_plane(self.host, x, y, modifiers)
        if plane is None:
            self.host.message(t("err.no_point"), warning=True)
            return
        self._plane = (np.asarray(plane.point, float), np.asarray(plane.normal, float))
        self._pts = [np.asarray(plane.point, float).copy()]
        self._last_xy = (x, y)
        self._drawing = True
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())

    def pointer_move(self, x, y, modifiers):
        if not self._drawing:
            plane = start_plane(self.host, x, y, modifiers)
            show_snap(self.viewport, plane.snap if plane else None, plane.point if plane else None)
            return
        if np.hypot(x - self._last_xy[0], y - self._last_xy[1]) < STEP_PX:
            return
        p = self._on_plane(x, y)
        if p is None:
            return
        self._pts.append(p)
        self._last_xy = (x, y)
        segs = [q for a, b in zip(self._pts, self._pts[1:]) for q in (a, b)]
        closing = self._closing(x, y)
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))
        self.viewport.show_marker(self._pts[0] if closing else p, PREVIEW)
        self.viewport.show_tip(t("snap.close") if closing else "", self._pts[0] if closing else None)

    def _closing(self, x, y):
        if len(self._pts) < 4:
            return False
        sx, sy = self.viewport.project(self._pts[0])
        far = max(np.hypot(*(np.array(self.viewport.project(p)) - (sx, sy))) for p in self._pts[::4])
        return np.hypot(x - sx, y - sy) <= CLOSE_PX and far > 3 * CLOSE_PX

    def pointer_up(self, x, y, button, modifiers):
        if button != LEFT or not self._drawing:
            return
        closed = self._closing(x, y)
        point, normal = self._plane
        pts = self._pts + ([self._pts[0].copy()] if closed else [])
        tol = curves.FREEHAND_PX * self.viewport.world_per_pixel(point)
        kept = curves.simplify(pts, tol)
        self._reset()
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        if closed:
            kept[-1] = kept[0].copy()
        if len(kept) < 2 or sum(np.linalg.norm(b - a) for a, b in zip(kept, kept[1:])) < 0.001:
            self.host.message(t("hint.freehand.start"), warning=True)
            return
        obj = _curve_object(self.doc, kept, {"kind": "freehand"}, closed and len(kept) > 3)
        put_curve(self, obj, (point, normal), t("cmd.freehand"), "info.freehand_face", "info.freehand",
                  n=len(obj.mesh.lines))

    def cancel(self):
        self._reset()
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())


class BezierTool(Tool):
    name = "bezier"

    def __init__(self, host):
        super().__init__(host)
        self.steps = curves.BEZIER_STEPS
        self._reset()

    def _reset(self):
        self._normal = None
        self._anchors = []          # [[point, handle in, handle out]] (world)
        self._auto = []             # (0.411) which points have automatic tangents (a click), the others by hand / corners
        self._press = None          # (x, y) of the button held on the last point put, while it may be dragged
        self._cursor = None
        self._closing = False

    def _smooth(self, anchors, auto, closed=False):
        """(0.411) The anchors with their automatic tangents worked out (as Blender's «Auto»)."""
        return curves.auto_handles(anchors, auto, closed)

    def options(self):
        return [draw_option("bezier"),                      # (0.450: the drawing tools, as Revit's «Draw» panel)
                Option("steps", t("ctx.bezier_steps"), "choice", self.steps, tuple((s, str(s)) for s in STEPS))]

    def set_option(self, key, value):
        if key == "draw":
            switch_draw(self, value)
            return
        if key == "steps":
            self.steps = int(value)
        self.host.set_hint(self.hint())

    def hint(self):
        if not self._anchors:
            return t("hint.bezier.start")
        return t("hint.bezier.drag" if self._press is not None else "hint.bezier.next")

    def _plane_point(self, x, y):
        origin, direction = self.viewport.ray(x, y)
        a = self._anchors[0][0]
        p = ray_plane(origin, direction, a, self._normal)
        return p if p is not None else ray_plane(origin, direction, a, -self._normal)

    def _flat(self, p):
        a = self._anchors[0][0]
        return np.asarray(p, float) - float((np.asarray(p, float) - a) @ self._normal) * self._normal

    def _near_first(self, x, y):
        if len(self._anchors) < 2:
            return False
        sx, sy = self.viewport.project(self._anchors[0][0])
        return bool(np.hypot(x - sx, y - sy) <= CLOSE_PX)

    def _show(self, extra=None):
        """The curve so far (and on to `extra`, (0.411) a smooth point where the mouse is: the curve passes through
        it), with the tangents of its last points."""
        anchors = [list(a) for a in self._anchors] + ([[extra, extra, extra]] if extra is not None else [])
        auto = list(self._auto) + ([True] if extra is not None else [])
        anchors = self._smooth(anchors, auto)
        pts = curves.bezier_points(anchors, False, self.steps) if len(anchors) > 1 else [anchors[0][0]]
        segs = [q for a, b in zip(pts, pts[1:]) for q in (a, b)]
        handles = []
        shown = anchors[-3:-1] if extra is not None else anchors[-2:]
        for p, hi, ho in shown:
            for h in (hi, ho):
                if np.linalg.norm(h - p) > 1e-9:
                    handles += [p, h]
        colours = [PREVIEW] * len(segs) + [(0.55, 0.55, 0.60, 1.0)] * len(handles)
        if segs or handles:
            self.viewport.show_polygon([], segments=segs + handles, colors=colours)
        self.viewport.show_grips([a[0] for a in self._anchors],
                                 [h for _p, hi, ho in shown for h in (hi, ho) if np.linalg.norm(h - _p) > 1e-9])

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self._finish(False)
            return
        if button != LEFT:
            return
        if not self._anchors:
            plane = start_plane(self.host, x, y, modifiers)
            if plane is None:
                self.host.message(t("err.no_point"), warning=True)
                return
            p = np.asarray(plane.point, float)
            self._normal = np.asarray(plane.normal, float)
            self._anchors = [[p.copy(), p.copy(), p.copy()]]
            self._auto = ["Alt" not in (modifiers or ())]       # (0.411: a click a smooth point, Alt a corner)
            self._press = (x, y)
            self.host.set_hint(self.hint())
            return
        if self._near_first(x, y):
            self._closing = True
            return
        last = self._anchors[-1][0]
        found = point_from(self.viewport, last, self._normal, x, y, modifiers)
        if found is None:
            return
        p = self._flat(found[0])
        if np.linalg.norm(p - last) < 1e-4:           # (a second click on the last point: it ends there)
            self._finish(False)
            return
        self._anchors.append([p.copy(), p.copy(), p.copy()])
        self._auto.append("Alt" not in (modifiers or ()))   # (0.411: a click a smooth point, Alt a corner)
        self._press = (x, y)
        self.host.set_hint(self.hint())

    def pointer_move(self, x, y, modifiers):
        if not self._anchors:
            plane = start_plane(self.host, x, y, modifiers)
            show_snap(self.viewport, plane.snap if plane else None, plane.point if plane else None)
            return
        if self._press is not None and moved_enough(self._press, (x, y)):
            h = self._plane_point(x, y)             # dragged: the point is smooth, its tangent out to the mouse
            if h is not None:
                p = self._anchors[-1][0]
                self._anchors[-1] = curves.smooth_anchor(p, h)
                self._auto[-1] = False                  # (0.411: its tangent by hand now)
                self._show()
                self.viewport.show_tip(t("snap.bezier_tangent"), h)
            return
        if self._press is not None:
            return
        if self._near_first(x, y):
            self._show(self._anchors[0][0])
            self.viewport.show_marker(self._anchors[0][0], PREVIEW)
            self.viewport.show_tip(t("snap.close"), self._anchors[0][0])
            return
        found = point_from(self.viewport, self._anchors[-1][0], self._normal, x, y, modifiers)
        if found is None:
            return
        self._cursor = self._flat(found[0])
        self._show(self._cursor)
        self.viewport.show_marker(self._cursor, found[2])
        self.viewport.show_tip(found[1], self._cursor if found[1] else None)

    def pointer_up(self, x, y, button, modifiers):
        if button != LEFT:
            return
        if self._closing:
            self._closing = False
            self._finish(True)
            return
        self._press = None
        self.host.set_hint(self.hint())

    def enter(self):
        self._finish(False)

    def cancel(self):
        if len(self._anchors) >= 2:                 # (Esc ends it as it is, as the Line's chain: not lost)
            self._finish(False)
            return
        self._reset()
        self.viewport.clear_overlays()
        self.viewport.show_grips()
        self.host.set_hint(self.hint())

    def deactivate(self):
        self.cancel()

    def _finish(self, closed):
        anchors, normal, auto = [list(a) for a in self._anchors], self._normal, list(self._auto)
        self._reset()
        self.viewport.clear_overlays()
        self.viewport.show_grips()
        self.host.set_hint(self.hint())
        if len(anchors) < 2:
            return
        anchors = self._smooth(anchors, auto, closed and len(anchors) > 2)
        pts = curves.bezier_points(anchors, closed, self.steps)
        curve = curves.bezier_curve(anchors, normal, closed, self.steps, auto)
        obj = _curve_object(self.doc, pts, curve, closed)
        put_curve(self, obj, (anchors[0][0], normal), t("cmd.bezier"), "info.bezier_face", "info.bezier",
                  n=len(anchors))
