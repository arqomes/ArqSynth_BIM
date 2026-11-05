"""Move (SketchUp 'M') and Rotate (SketchUp 'Q'), with copies.

Both act on the selection, or, with nothing selected, on the object under the
first click (it becomes the selection). They work on sketches and on IFC
elements alike: an IFC element's placement moves, its geometry is untouched,
and a wall takes its doors and windows along. A door or window moved alone
slides along its wall (and up/down for the sill), it never leaves the wall.

Move: click the base point, then the destination (inferences and red / green
/ blue axes), or type the distance in the direction shown. Rotate: click the
centre, a point giving the starting direction, then the final direction (the
protractor snaps to 15°), or type the angle. Rotations are about a vertical
axis. In both, a value typed right after finishing corrects the last one.

Copies (as in SketchUp): tap Ctrl to switch copying on/off (or hold Ctrl on
the last click). Right after a copy, type "3x" for three copies at the same
spacing (or angle), "/3" to split the distance (or angle) into three.

Faces of sketches picked alone (0.310): just they move or turn, the faces
beside them stretch (model/parts.py). Loose lines picked alone (0.373): just
they move or turn, the lines joined to their ends stretch. Copies of either
(0.373) are sketches of their own, as SketchUp's.
"""

from dataclasses import dataclass

import numpy as np

from ..core.inference import ENDPOINT, MIDPOINT, ON_EDGE
from ..core.transform import plan_angle, rotation_about_z, snap_angle, transform_segments, translation
from ..core.units import format_angle, format_length, parse_angle, parse_array, parse_lengths
from ..i18n import decimal_sep, refusal, t
from ..model import annotations as notes2d
from ..model import bim, parts
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, Tool, default_normal, point_from, show_snap, start_plane

Z = np.array((0.0, 0.0, 1.0))
ARC_STEPS = 32


def _fmt(value):
    return format_length(value, decimal_sep())


def _angle(value):
    return format_angle(value, decimal_sep())


@dataclass
class _Last:
    cmd: object
    ids: list               # the objects acted on (the originals, when copying)
    origin: np.ndarray      # Move: base point; Rotate: centre
    step: object            # Move: displacement (vector); Rotate: angle (degrees)
    copy: bool
    parts: tuple = None     # (0.373) (faces, lines picked alone, sketches pasted) acted on instead of objects


class _TransformTool(Tool):
    """What Move and Rotate share: the objects acted on, their 'ghost' outline,
    copying and series of copies."""

    accepts_typing = True
    label_key = ""

    def __init__(self, host):
        super().__init__(host)
        self._ids = []
        self._parts = None      # (0.310) the faces of sketches picked alone acted on instead (viewport.face_selection)
        self._lines = None      # (0.373) …or the loose lines picked alone (viewport.line_selection)
        self._loose = None      # (0.373) …or sketches not in the document, pasted (copies of lines / faces alone)
        self._segs = None       # world segment ends of the objects' edges, (2N, 3)
        self._last = None
        self.copy = False       # Ctrl switches it

    # ------------------------------------------------------------ what moves

    def _object_at(self, x, y):
        obj_id = self.viewport.pick_object(x, y)
        if obj_id is None:
            snap, _hit = self.viewport.snap(x, y)
            if snap is not None and snap.kind in (ENDPOINT, MIDPOINT, ON_EDGE):
                obj_id = snap.obj_id
        return obj_id if self.doc.get(obj_id) is not None else None

    def _take(self, x, y):
        """The objects to act on: the selection, else the one under the cursor — or (0.310) the faces of sketches
        picked alone: just they move (the faces beside them stretch); (0.373) the loose lines picked alone: just
        they (the lines joined to their ends stretch)."""
        ids = [i for i in self.viewport.selection if self.doc.get(i) is not None]
        self._loose = None
        self._lines = dict(self.viewport.line_selection) if not ids else None
        if self._lines:
            self._parts, self._ids = None, []
            self._segs = parts.line_segments(self.doc, self._lines)
            return True
        self._parts = dict(self.viewport.face_selection) if not ids else None
        if self._parts:
            self._ids, self._segs = [], parts.segments(self.doc, self._parts)
            return True
        if not ids:
            obj_id = self._object_at(x, y)
            ids = [obj_id] if obj_id is not None else []
            if ids:
                self.viewport.set_selection(set(ids))
        self._ids = ids
        segs = []
        for i in ids:
            obj = self.doc.get(i)
            v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
            world = v @ obj.matrix[:3, :3].T + obj.matrix[:3, 3]
            for a, b in obj.mesh.visible_edges():
                segs += [world[a], world[b]]
        self._segs = np.array(segs, dtype=float).reshape(-1, 3)
        return bool(ids)

    def _take_annotations(self, plan_only=False):
        """(0.120) The lines, regions and texts selected in the view shown, when nothing else is: they are what
        moves (plan_only: only in a plan — turned about the vertical there, 0.191)."""
        self._parts = self._lines = self._loose = None
        anns = [a for a in self.viewport.selected_annotations if a in self.doc.annotations]
        plane = self.viewport.view_plane()
        if anns and not self.viewport.selection and plane is not None and (self.viewport.plan or not plan_only):
            self._ids, self._anns = [], anns
            origin, u, v, _n = plane
            to3 = lambda q: origin + u * q[0] + v * q[1]           # noqa: E731
            segs = [to3(q) for a in anns for s in notes2d.segments(a, origin, u, v) for q in s]
            self._segs = np.array(segs, dtype=float).reshape(-1, 3)
            return True
        self._anns = []
        return False

    def _only_fillings(self, ids=None):
        ids = self._ids if ids is None else ids
        return bool(ids) and all(bim.is_filling(self.doc, i) for i in ids)

    def _ghost(self, matrix, extra=(), extra_colors=()):
        """The objects' edges where they would go, plus helper lines."""
        moved = transform_segments(self._segs, matrix) if self._segs is not None and len(self._segs) else []
        segs = list(moved) + list(extra)
        colors = [PREVIEW] * len(moved) + list(extra_colors)
        self.viewport.show_lines(segs, colors)

    # ------------------------------------------------------------ copying

    def activate(self):
        self.copy = False                       # each time the tool is chosen, it starts by moving
        super().activate()

    def _with_mode(self, text):
        return t("hint.copy_mode") + text if self.copy else text

    def ctrl_tap(self):
        self.copy = not self.copy
        self.host.set_hint(self.hint())
        self.host.message(t("info.copy_on" if self.copy else "info.copy_off"))

    def options(self):
        return [Option("copy", t("ctx.copy"), "toggle", self.copy)]

    def set_option(self, key, value):
        if key == "copy" and bool(value) != self.copy:
            self.ctrl_tap()

    def _matrix(self, origin, step):
        raise NotImplementedError

    def _scaled(self, step, factor):
        return step * factor

    def _commit(self, ids, origin, step, copy, n=1, divide=False):
        """Move / rotate (or copy, n copies) `ids`. Returns True if done."""
        factors = [k / n for k in range(1, n + 1)] if divide else list(range(1, n + 1))
        steps = [self._scaled(step, f) for f in factors]
        picked = getattr(self, "_parts", None)
        lines = getattr(self, "_lines", None)
        loose = getattr(self, "_loose", None)
        if (picked or lines or loose) and not ids:
            if copy or loose:                           # (0.373) copies of them: sketches of their own, picked
                made = loose or (parts.line_copies(self.doc, lines) if lines else parts.face_copies(self.doc, picked))
                new = parts.add_copies(self.doc, made, [self._matrix(origin, s) for s in steps], t("cmd.copy"))
                self._last = _Last(self.doc.last_command(), [], origin, step, True, (picked, lines, loose))
                self.viewport.set_selection(set(new))
                self.host.message(t("info.copied", n=len(new)))
                return True
            try:
                if lines:                               # (0.373) lines picked alone: they move, they stay picked
                    parts.transform_lines(self.doc, lines, self._matrix(origin, steps[0]), t(self.label_key))
                    self.viewport.select_lines({k: v for k, v in lines.items() if self.doc.get(k) is not None})
                else:                                   # (0.310) faces picked alone: they move, they stay picked
                    parts.transform(self.doc, picked, self._matrix(origin, steps[0]), t(self.label_key))
                    self.viewport.select_faces(picked)
            except ValueError as exc:
                self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
                return False
            self._last = _Last(self.doc.last_command(), [], origin, step, False, (picked, lines, loose))
            return True
        try:
            if self._only_fillings(ids):
                # doors / windows alone: slide (or copy) along their wall
                if copy:
                    new = [g for i in ids for g in bim.copy_filling(self.doc, i, steps)]
                else:
                    for i in ids:
                        bim.slide_filling(self.doc, i, steps[0])
                    new = []
            elif copy:
                new = bim.copy_objects(self.doc, ids, [self._matrix(origin, s) for s in steps],
                                       t("cmd.copy"))
            else:
                if not bim.transform_objects(self.doc, ids, self._matrix(origin, steps[0]), t(self.label_key)):
                    return False
                new = []
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return False
        self._last = _Last(self.doc.last_command(), list(ids), origin, step, copy)
        if copy:
            self.viewport.set_selection(set(new))       # the copies are selected (to move them on)
            self.host.message(t("info.copied", n=len(new)))
        return True

    def _typed_series(self, text):
        """'3x' or '/3' typed right after a copy: redo it as a series. True if it was that."""
        series = parse_array(text)
        last = self._last
        if series is None or last is None or not last.copy or self.doc.last_command() is not last.cmd:
            return False
        self.doc.undo()
        self._restore(last)
        self._commit(last.ids, last.origin, last.step, True, n=series[1], divide=series[0] == "divide")
        return True

    def _restore(self, last):
        """(0.373) What the last move / copy acted on, back (a value typed after it does it again)."""
        self._parts, self._lines, self._loose = last.parts if last.parts is not None else (None, None, None)

    def cancel(self):
        self._reset()
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")


class MoveTool(_TransformTool):
    name = "move"
    label_key = "cmd.move"

    def __init__(self, host):
        super().__init__(host)
        self._reset()

    def _reset(self):
        self._base = None
        self._target = None

    def hint(self):
        return self._with_mode(t("hint.move.end") if self._base is not None else t("hint.move.start"))

    def vcb_title(self):
        return t("vcb.distance")

    def _matrix(self, origin, step):
        return translation(step)

    def _take(self, x, y):
        """The objects to move — or (0.120) the lines, regions and texts selected in the view shown."""
        if self._take_annotations():
            return True
        return super()._take(x, y)

    def _commit(self, ids, origin, step, copy, n=1, divide=False):
        anns = getattr(self, "_anns", None)
        if not anns or ids:
            return super()._commit(ids, origin, step, copy, n, divide)
        factors = [k / n for k in range(1, n + 1)] if divide else list(range(1, n + 1))
        steps = [np.asarray(step, dtype=float) * f for f in factors]
        if copy:
            new = [notes2d.moved_copy(a, s) for s in steps for a in anns]
            self.doc.execute(notes2d.AddAnnotations(new, t("cmd.copy")))
            self.viewport.select_annotations(set(new[-len(anns):]))
            self.host.message(t("info.copied", n=len(new)))
        else:
            self.doc.execute(notes2d.MoveAnnotations(anns, steps[0], t("cmd.move")))
        self._last = _Last(self.doc.last_command(), [], origin, step, copy)
        return True

    def _delta(self, target):
        """The move from the base point (a door/window alone keeps to its wall)."""
        delta = np.asarray(target, dtype=float) - self._base
        if self._only_fillings():
            st = self.doc.ifc.filling_state(self._ids[0])
            x = st["matrix"][:3, 0] / np.linalg.norm(st["matrix"][:3, 0])
            delta = x * float(delta.dot(x)) + Z * float(delta[2])
        return delta

    # ------------------------------------------------------------ mouse

    def pointer_move(self, x, y, modifiers):
        if self._base is None:
            plane = start_plane(self.host, x, y, modifiers)
            show_snap(self.viewport, plane.snap if plane else None, plane.point if plane else None)
            return
        found = point_from(self.viewport, self._base, default_normal(self.viewport.ray(x, y)[1]), x, y, modifiers)
        if found is None:
            return
        self._target, tip, marker, line = found
        delta = self._delta(self._target)
        end = self._base + delta
        self._ghost(translation(delta), [self._base, end], [line, line])
        dist = _fmt(float(np.linalg.norm(delta)))
        self.viewport.show_label(("+ " if self.copy else "") + dist, (self._base + end) / 2)
        self.viewport.show_marker(end, marker)
        self.viewport.show_tip(tip, end if tip else None)
        self.host.set_vcb(dist)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self._base is None:
            if not self._take(x, y):
                self.host.message(t("err.nothing_to_move"), warning=True)
                return
            plane = start_plane(self.host, x, y)
            if plane is None:
                return
            self._base = plane.point.copy()
            self.host.set_hint(self.hint())
            return
        if self._target is not None:
            held = any(m in ("Control", "Ctrl") for m in (modifiers or ()))
            self._finish(self._delta(self._target), self.copy or held)

    # ------------------------------------------------------------ keyboard

    def typed(self, text):
        if self._base is None and self._typed_series(text):
            return
        values = parse_lengths(text, 1)
        if values is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        length = values[0]
        if self._base is not None:
            delta = self._delta(self._target) if self._target is not None else np.zeros(3)
            if np.linalg.norm(delta) < 1e-9:
                self.host.message(t("hint.line.direction"), warning=True)
                return
            self._finish(delta / np.linalg.norm(delta) * length, self.copy)
            return
        last = self._last
        if last is not None and self.doc.last_command() is last.cmd:
            # a distance typed right after finishing corrects the last move / copy
            self.doc.undo()
            self._ids = last.ids
            self._restore(last)
            self._finish(last.step / np.linalg.norm(last.step) * length, last.copy, base=last.origin)
            return
        self.host.message(t("hint.move.start"), warning=True)

    # ------------------------------------------------------------ internals

    def _finish(self, delta, copy, base=None):
        delta = np.asarray(delta, dtype=float)
        if np.linalg.norm(delta) < 1e-9:
            return
        ids, base = list(self._ids), (self._base if base is None else base)
        self.viewport.clear_overlays()
        self._reset()
        self.host.set_hint(self.hint())
        if not self._commit(ids, base, delta, copy):
            return
        dist = float(np.linalg.norm(delta))
        self.host.set_vcb(_fmt(dist))
        if not copy and not ids and getattr(self, "_lines", None):
            self.host.message(t("info.lines_moved", d=_fmt(dist)))
        elif not copy and not ids and self._parts:
            self.host.message(t("info.part_moved", d=_fmt(dist)))
        elif not copy:
            self.host.message(t("info.moved", n=len(ids) or len(getattr(self, "_anns", None) or ()), d=_fmt(dist)))


class CopyTool(MoveTool):
    """(0.326) Copiar, as Revit's Copy: the Move tool copying from the start (until then copying was Ctrl tapped in
    Move — a gesture nobody finds). Ctrl still turns it off. Ctrl+V starts it with the elements copied on the
    cursor (paste())."""
    name = "copy"

    def activate(self):
        super().activate()
        self.copy = True
        self.host.set_hint(self.hint())

    def paste(self, ids, base, sketches=None):
        """Ctrl+V: the elements copied follow the cursor from their base point; a click puts the copy there.
        (0.373) sketches: lines or faces picked alone that were copied (sketches of their own, not in the document)."""
        if sketches:
            self.viewport.set_selection(set())
            self._ids, self._parts, self._lines, self._loose = [], None, None, list(sketches)
            self._segs = parts.sketch_segments(sketches)
        else:
            self.viewport.set_selection(set(ids))
            if not self._take(0, 0):
                return False
        self._base = np.asarray(base, dtype=float).copy()
        self.host.set_hint(self.hint())
        return True


class ArrayTool(CopyTool):
    """(0.326) Matriz, as Revit's linear Array: copies in a row, as many as chosen on the bar — «each at this
    distance» (the 2nd, the 3rd… further on) or «spread over it» (the last where clicked). The same as a copy and
    «3x» / «/3» typed after it, in one go and in sight."""
    name = "array"
    COUNTS = (2, 3, 4, 5, 6, 8, 10, 12, 15, 20)

    def __init__(self, host):
        super().__init__(host)
        self.count = 3
        self.divide = False

    def options(self):
        return [Option("count", t("ctx.array_count"), "choice", self.count, tuple((n, str(n)) for n in self.COUNTS)),
                Option("spread", t("ctx.array_spread"), "choice", "divide" if self.divide else "each",
                       (("each", t("ctx.array_each")), ("divide", t("ctx.array_divide"))))]

    def set_option(self, key, value):
        if key == "count":
            self.count = int(value)
        elif key == "spread":
            self.divide = value == "divide"
        self.host.set_hint(self.hint())

    def ctrl_tap(self):
        pass                                        # (always copies)

    def _with_mode(self, text):
        how = t("ctx.array_divide" if self.divide else "ctx.array_each").lower()
        return t("hint.array_mode", n=self.count, how=how) + text

    def _commit(self, ids, origin, step, copy, n=1, divide=False):
        if copy and n == 1:                         # (a click: the row as chosen; «3x» typed after: as typed)
            n, divide = self.count, self.divide
        return super()._commit(ids, origin, step, copy, n, divide)


class RotateTool(_TransformTool):
    name = "rotate"
    label_key = "cmd.rotate"

    def __init__(self, host):
        super().__init__(host)
        self._reset()

    def _reset(self):
        self._center = None
        self._ref = None            # unit horizontal starting direction
        self._radius = 1.0
        self._value = 0.0           # current angle (degrees, counter-clockwise > 0)

    def hint(self):
        if self._center is None:
            return self._with_mode(t("hint.rotate.start"))
        return self._with_mode(t("hint.rotate.end") if self._ref is not None else t("hint.rotate.ref"))

    def vcb_title(self):
        return t("vcb.angle")

    def _matrix(self, origin, step):
        return rotation_about_z(origin, step)

    def _take(self, x, y):
        """The objects to turn — or (0.191) the drawings selected in a plan."""
        if self._take_annotations(plan_only=True):
            return True
        return super()._take(x, y)

    def _commit(self, ids, origin, step, copy, n=1, divide=False):
        anns = getattr(self, "_anns", None)
        if not anns or ids:
            return super()._commit(ids, origin, step, copy, n, divide)
        factors = [k / n for k in range(1, n + 1)] if divide else list(range(1, n + 1))
        up = np.array((0.0, 0.0, 1.0))                     # (a plan seen from above: counter-clockwise about it)
        if copy:
            new = []
            for f in factors:
                for a in anns:
                    c = notes2d.moved_copy(a, np.zeros(3))
                    c.points = notes2d.rotated_points(c.points, np.asarray(origin, dtype=float), up, step * f)
                    if c.kind == "text":
                        c.extra = dict(c.extra, angle=(notes2d.angle(c) + step * f + 180.0) % 360.0 - 180.0)
                    new.append(c)
            self.doc.execute(notes2d.AddAnnotations(new, t("cmd.copy")))
            self.viewport.select_annotations(set(new[-len(anns):]))
            self.host.message(t("info.copied", n=len(new)))
        else:
            self.doc.execute(notes2d.RotateAnnotations(anns, origin, up, step, t("cmd.rotate")))
        self._last = _Last(self.doc.last_command(), [], origin, step, copy)
        return True

    def _plan_dir(self, p):
        v = (np.asarray(p, dtype=float) - self._center) * np.array((1.0, 1.0, 0.0))
        n = np.linalg.norm(v)
        return (v / n, n) if n > 1e-9 else (None, 0.0)

    def _direction(self, angle):
        a = np.arctan2(self._ref[1], self._ref[0]) + np.radians(angle)
        return np.array((np.cos(a), np.sin(a), 0.0))

    def _arc(self, angle):
        steps = max(2, int(abs(angle) / 360 * ARC_STEPS * 4))
        pts = [self._center + self._direction(angle * k / steps) * self._radius for k in range(steps + 1)]
        segs = []
        for a, b in zip(pts, pts[1:]):
            segs += [a, b]
        return segs

    # ------------------------------------------------------------ mouse

    def pointer_move(self, x, y, modifiers):
        if self._center is None:
            plane = start_plane(self.host, x, y, modifiers)
            show_snap(self.viewport, plane.snap if plane else None, plane.point if plane else None)
            return
        found = point_from(self.viewport, self._center, Z, x, y, modifiers)
        if found is None:
            return
        p, tip, marker, _line = found
        v, dist = self._plan_dir(p)
        if v is None:
            return
        if self._ref is None:
            self.viewport.show_lines([self._center, self._center + v * dist], [PREVIEW, PREVIEW])
            self.viewport.show_marker(p, marker)
            self.viewport.show_tip(tip, p if tip else None)
            return
        self._value, snapped = snap_angle(plan_angle(self._ref, v))
        end = self._center + self._direction(self._value) * self._radius
        helpers = [self._center, self._center + self._ref * self._radius, self._center, end] + self._arc(self._value)
        self._ghost(rotation_about_z(self._center, self._value), helpers, [PREVIEW] * len(helpers))
        self.viewport.show_label(("+ " if self.copy else "") + _angle(self._value), end)
        self.viewport.show_marker(end, PREVIEW)
        self.viewport.show_tip(t("snap.angle_step") if snapped else "", end if snapped else None)
        self.host.set_vcb(_angle(self._value))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self._center is None:
            if not self._take(x, y):
                self.host.message(t("err.nothing_to_move"), warning=True)
                return
            if self._only_fillings():
                self.host.message(t("err.rotate_filling"), warning=True)
                self._ids = []
                return
            plane = start_plane(self.host, x, y)
            if plane is None:
                return
            self._center = plane.point.copy()
            self.host.set_hint(self.hint())
            return
        found = point_from(self.viewport, self._center, Z, x, y, modifiers)
        if found is None:
            return
        if self._ref is None:
            v, dist = self._plan_dir(found[0])
            if v is not None:
                self._ref, self._radius = v, max(dist, 0.3)
                self.host.set_hint(self.hint())
            return
        held = any(m in ("Control", "Ctrl") for m in (modifiers or ()))
        self._finish(self._value, self.copy or held)

    # ------------------------------------------------------------ keyboard

    def typed(self, text):
        if self._center is None and self._typed_series(text):
            return
        value = parse_angle(text)
        if value is None:
            self.host.message(t("err.bad_angle", t=text), warning=True)
            return
        if self._center is not None:
            # the typed angle turns the way the mouse turned (counter-clockwise if it has not)
            self._finish(value * (-1.0 if self._value < -1e-9 else 1.0), self.copy)
            return
        last = self._last
        if last is not None and self.doc.last_command() is last.cmd:
            self.doc.undo()                       # an angle typed right after finishing corrects the last one
            self._ids = last.ids
            self._finish(value * (-1.0 if last.step < 0 else 1.0), last.copy, center=last.origin)
            return
        self.host.message(t("hint.rotate.start"), warning=True)

    # ------------------------------------------------------------ internals

    def _finish(self, angle, copy, center=None):
        if abs(angle) < 1e-9:
            return
        ids, center = list(self._ids), (self._center if center is None else center)
        self.viewport.clear_overlays()
        self._reset()
        self.host.set_hint(self.hint())
        if not self._commit(ids, center, float(angle), copy):
            return
        self.host.set_vcb(_angle(angle))
        if not copy and not ids and self._lines:
            self.host.message(t("info.lines_rotated", a=_angle(angle)))
        elif not copy and not ids and self._parts:
            self.host.message(t("info.part_rotated", a=_angle(angle)))
        elif not copy:
            self.host.message(t("info.rotated", n=len(ids) or len(getattr(self, "_anns", None) or ()),
                                a=_angle(angle)))
