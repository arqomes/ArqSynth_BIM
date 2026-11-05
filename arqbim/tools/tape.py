"""Tape Measure (SketchUp 'T'): guide lines and measuring.

- Click an edge (or a guide line), move away and click: a guide line parallel
  to it through the point under the mouse (on the ground, on a face...), at the
  distance shown; or type the distance + Enter. Typing another value right
  after corrects the last guide.
- Click a point (endpoint, midpoint...), move and click: measures the distance.

Guide lines are not IFC: they are saved with the sketches. Every drawing tool
snaps to them ("On guide") and to where they cross ("Intersection").
Edit ▸ Delete guide lines removes them all (one undo step).
"""

from dataclasses import dataclass

import numpy as np

from ..core.inference import GUIDE_HALF_LENGTH, ON_EDGE, ON_FACE, ON_GUIDE
from ..core.lines import guide_at_distance, guide_through
from ..core.sketch_geometry import normalize, ray_plane
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, t
from ..model.document import AddGuide, Guide
from ..render.viewport import GUIDE_COLOR, PREVIEW
from .base import LEFT, RIGHT, SNAPPABLE, Tool, default_normal, show_snap

Z = np.array((0.0, 0.0, 1.0))
_GUIDE_RGBA = tuple(int(GUIDE_COLOR[i:i + 2], 16) / 255 for i in (1, 3, 5)) + (1.0,)


def _fmt(value):
    return format_length(value, decimal_sep())


@dataclass
class _Op:
    mode: str              # "guide" (from an edge) | "measure" (from a point)
    start: np.ndarray
    edge: tuple            # (a, b) of the edge / guide the new guide is parallel to
    normal: np.ndarray     # plane the mouse moves on
    current: np.ndarray = None


@dataclass
class _Last:
    cmd: object
    edge: tuple
    side: np.ndarray       # a point on the side of the edge where the guide went


def guide_plane(a, b, view_dir):
    """Plane a guide parallel to the edge a-b follows when the mouse is over
    nothing (no face, no point): the edge's own level for a level edge, else the
    plane through the edge that faces the viewer."""
    d = normalize(np.asarray(b, dtype=float) - np.asarray(a, dtype=float))
    if abs(d[2]) < 1e-6:
        return Z.copy()
    n = view_dir - np.dot(view_dir, d) * d
    if np.linalg.norm(n) < 1e-9:
        n = np.cross(d, Z) if abs(d[2]) < 0.99 else np.array((1.0, 0.0, 0.0))
    return normalize(n)


class TapeTool(Tool):
    name = "tape"
    accepts_typing = True

    def __init__(self, host):
        super().__init__(host)
        self._op = None
        self._last = None

    def hint(self):
        if self._op is None:
            return t("hint.tape.start")
        return t("hint.tape.guide") if self._op.mode == "guide" else t("hint.tape.measure")

    def vcb_title(self):
        return t("vcb.distance")

    # ------------------------------------------------------------ mouse

    def pointer_move(self, x, y, modifiers):
        if self._op is None:
            snap, _hit = self.viewport.snap(x, y)
            show_snap(self.viewport, snap if snap is not None and snap.kind in SNAPPABLE else None)
            return
        p, snap = self._mouse_point(x, y)
        if p is None:
            return
        self._op.current = p
        self._preview(snap)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self._op is None:
            self._begin(x, y)
        elif self._op.current is not None:
            self._finish()

    # ------------------------------------------------------------ keyboard

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        value = values[0]
        op = self._op
        if op is not None and op.mode == "guide":
            self._add_guide(op.edge, self._side_point(op), value)
            self.cancel()
            return
        if op is not None:
            self.host.message(t("hint.tape.measure"), warning=True)
            return
        last = self._last
        if last is not None and self.doc.last_command() is last.cmd:
            # SketchUp: a value typed right after finishing corrects the last guide
            self.doc.undo()
            self._add_guide(last.edge, last.side, value)
            return
        self.host.message(t("hint.tape.start"), warning=True)

    def cancel(self):
        self._op = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())

    # ------------------------------------------------------------ internals

    def _begin(self, x, y):
        snap, _hit = self.viewport.snap(x, y)
        if snap is None or snap.kind not in SNAPPABLE:
            self.host.message(t("hint.tape.start"), warning=True)
            return
        origin, direction = self.viewport.ray(x, y)
        if snap.kind in (ON_EDGE, ON_GUIDE) and snap.edge is not None:
            a, b = snap.edge
            self._op = _Op("guide", snap.point.copy(), (a.copy(), b.copy()), guide_plane(a, b, direction))
        else:
            self._op = _Op("measure", snap.point.copy(), None, default_normal(direction))
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())

    def _mouse_point(self, x, y):
        """Where the mouse is (as in SketchUp, the guide goes through it): an
        inferred point, else the face under the cursor, else the tool's plane.
        Returns (point, snap or None)."""
        op = self._op
        snap, _hit = self.viewport.snap(x, y)
        if snap is not None and (snap.kind in SNAPPABLE or snap.kind == ON_FACE):
            if op.mode == "measure" or \
                    np.linalg.norm(np.cross(snap.point - op.edge[0], normalize(op.edge[1] - op.edge[0]))) > 1e-6:
                # (a point on the edge line itself would give no distance)
                return snap.point.copy(), (snap if snap.kind in SNAPPABLE else None)
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, op.start, op.normal)
        if p is None:
            p = ray_plane(origin, direction, op.start, -op.normal)
        return p, None

    def _side_point(self, op):
        """A point on the side of the edge where the guide goes (the mouse side,
        else the 'left' of the edge on its plane)."""
        a, b = op.edge
        if op.current is not None and guide_at_distance(a, b, op.current, 1.0) is not None:
            return op.current
        return op.start + np.cross(op.normal, normalize(b - a))

    def _add_guide(self, edge, side, distance):
        a, b = edge
        found = guide_at_distance(a, b, side, distance)
        if found is None:
            return
        point, direction = found
        cmd = self.doc.execute(AddGuide(Guide(point, direction), t("cmd.guide")))
        self._last = _Last(cmd, edge, np.asarray(side, dtype=float).copy())
        self.host.set_vcb(_fmt(abs(distance)))
        self.host.message(t("info.guide", d=_fmt(abs(distance))))

    def _finish(self):
        op = self._op
        if op.mode == "guide":
            _point, _dir, dist = guide_through(op.edge[0], op.edge[1], op.current)
            if dist < 1e-6:
                return                                # still on the edge: keep moving
            self._add_guide(op.edge, op.current, dist)
        else:
            dist = float(np.linalg.norm(op.current - op.start))
            self.host.set_vcb(_fmt(dist))
            self.host.message(t("info.measure", d=_fmt(dist)))
        self.cancel()

    def _preview(self, snap):
        op = self._op
        if op.mode == "guide":
            a, b = op.edge
            point, direction, dist = guide_through(a, b, op.current)
            foot = a + np.dot(op.current - a, direction) * direction   # nearest point of the edge line
            segs = [point - direction * GUIDE_HALF_LENGTH, point + direction * GUIDE_HALF_LENGTH,
                    foot, op.current]
            colors = [_GUIDE_RGBA] * 2 + [PREVIEW] * 2
        else:
            dist = float(np.linalg.norm(op.current - op.start))
            segs, colors = [op.start, op.current], [PREVIEW] * 2
        self.viewport.show_lines(segs, colors)
        self.viewport.show_label(_fmt(dist), op.current)
        if snap is not None:
            show_snap(self.viewport, snap)
        else:
            self.viewport.show_marker(op.current)
            self.viewport.show_tip("", None)
        self.host.set_vcb(_fmt(dist))
