"""Push/Pull tool (SketchUp 'P'): click a face, move, click; or type '2,80' + Enter.
After finishing, typing a new distance + Enter corrects the last Push/Pull.

A face with faces beside it moves away from where it was (0.310, as SketchUp's: an offset rectangle's middle pushed
down is a tray open on top). Ctrl tapped — or held on the click — «criar sólido» (SketchUp's new starting face): a
face is left where it started, so what comes out is a closed solid, up or down.

Several faces at once (0.311): a click on a face picked (Selecionar: Shift/Ctrl+click, or a sketch picked whole)
pushes / pulls all the faces picked the same distance, each along its own normal — those looking the same way go
exactly together, faces that touch go as one piece (sketch_geometry.push_pull_faces); one undo step, and they stay
picked where they end up. A click on one strip of an offset's frame takes the whole frame, the face SketchUp shows.

Pushing a rectangle into a solid makes a niche; reaching the face behind cuts a
hole right through. A rectangle drawn on an IFC wall or slab and pushed into it
becomes an IFC opening (through) or a niche (IfcOpeningElement). A side of such an
opening or niche (a reveal, the sill, the head, a niche's back) is pushed / pulled
on its own: the opening gets wider, narrower, deeper. A wall's base goes down or up
(its top stays)."""

from dataclasses import dataclass

import numpy as np

from ..core.sketch_geometry import (
    PushPullResult, closest_on_line_to_ray, face_world_normal, face_world_points, push_pull, push_pull_faces,
    surface_faces,
)
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, refusal, t
from ..model import bim, parts
from ..model.document import ReplaceMesh, ReplaceMeshes
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, SNAPPABLE, Option, Tool, moved_enough, show_snap


@dataclass
class _Op:
    obj_id: int
    fi: int
    before: object       # PolyMesh before the operation
    matrix: np.ndarray
    normal: np.ndarray   # world normal of the face
    anchor: np.ndarray   # clicked point on the face
    face_pts: list
    press: tuple
    d: float = 0.0       # distance asked (mouse or keyboard)
    applied: float = 0.0 # distance actually applied (after clamping)
    result: object = None
    mesh: object = None
    host: object = None  # bim.SheetHost when the face is a rectangle lying on an IFC wall/slab
    keep: bool = False   # (0.310) as previewed: a new starting face left (Ctrl) — a solid, not an opening


@dataclass
class _Last:
    cmd: object
    obj_id: int
    fi: int
    before: object
    matrix: np.ndarray
    sign: float
    keep: bool = False   # a new starting face left (Ctrl, 0.310)


@dataclass
class _Many:
    """(0.311) Push/Pull on several faces at once: the faces picked, or the strips of one flat face (a frame)."""
    targets: list        # [(obj_id, frozenset of faces, mesh before, matrix, bim.SheetHost or None)]
    picked: set          # the sketches whose faces were picked: picked again where they end up
    normal: np.ndarray   # world normal of the face clicked: the mouse measures along it
    anchor: np.ndarray
    face_pts: list
    press: tuple
    d: float = 0.0
    applied: float = 0.0
    results: dict = None # obj_id -> (mesh after, PushPullResult)
    keep: bool = False
    n: int = 0           # how many faces, as SketchUp counts them (counted once)


@dataclass
class _LastMany:
    cmd: object
    op: object           # the _Many done


@dataclass
class _LastVoid:
    cmd: object
    sheet_id: int


@dataclass
class _BimOp:
    """Push/Pull on a face of an IFC element made by ArqBIM: a parametric resize."""
    guid: str
    kind: str            # wall | slab | column
    axis: int            # element axis the face is across (0 = length, 1 = thickness, 2 = height)
    side: int            # +1: the face at the high end of that axis, -1: low end
    frame: object        # core.openings.WallFrame of the element
    normal: np.ndarray
    anchor: np.ndarray
    press: tuple
    d_min: float         # most negative distance allowed (keeps doors/openings inside, min size)
    d: float = 0.0
    applied: float = 0.0


@dataclass
class _VoidOp:
    """Push/Pull on a side of an empty opening or niche of an IFC wall / slab: that side moves."""
    guid: str            # the wall / slab
    void: str            # its IfcOpeningElement's GlobalId
    axis: int            # the element axis the side is across
    side: int            # +1: the side at the opening's low end (the face looks to +axis), -1: its high end
    frame: object
    lo: np.ndarray       # the opening's box, in the element's frame
    hi: np.ndarray
    normal: np.ndarray
    anchor: np.ndarray
    press: tuple
    d_min: float         # most negative distance: the opening grows (to 1 cm from the element's outline)
    d_max: float         # most positive: it shrinks (to 1 cm)
    d: float = 0.0
    applied: float = 0.0


@dataclass
class _LastBim:
    cmd: object
    op: object           # _BimOp or _VoidOp


def _frame_box(frame):
    return (np.array((frame.x0, frame.y0, frame.z0)),
            np.array((frame.x0 + frame.length, frame.y1, frame.z1)))


def _fmt(value):
    return format_length(value, decimal_sep())


class PushPullTool(Tool):
    name = "push_pull"
    accepts_typing = True

    def __init__(self, host):
        super().__init__(host)
        self._op = None
        self._last = None
        self._hover_xy = None
        self._voids = {}         # element GlobalId -> (id of its mesh, its openings) — read again when it changes
        self.solid = False       # (0.310) Ctrl tapped: a new starting face left — a closed solid either way
        self._held = False       # Ctrl held down (on the click, as Move's copy)

    def activate(self):
        self.solid = False                       # each time the tool is chosen, it starts by moving the face
        super().activate()

    def hint(self):
        text = t("hint.pp.drag") if self._op else t("hint.pp.start")
        return t("hint.pp_solid_mode") + text if self.solid else text

    def ctrl_tap(self):
        self.solid = not self.solid
        self.host.set_hint(self.hint())
        self.host.message(t("info.pp_solid_on" if self.solid else "info.pp_solid_off"))
        if isinstance(self._op, (_Op, _Many)):
            self._preview(self._op.d)

    def options(self):
        return [Option("solid", t("ctx.pp_solid"), "toggle", self.solid)]

    def set_option(self, key, value):
        if key == "solid" and bool(value) != self.solid:
            self.ctrl_tap()

    def _keep(self):
        return self.solid or self._held

    def vcb_title(self):
        return t("vcb.distance")

    # ------------------------------------------------------------ mouse

    def pointer_move(self, x, y, modifiers):
        self._hover_xy = (x, y)
        self._held = bool(set(modifiers or ()) & {"Control", "Ctrl"})
        if self._op is None:
            self._hover(x, y)
            return
        # SketchUp: hovering a point (e.g. the top corner of another volume)
        # pushes/pulls exactly up to that point's level.
        snap, _hit = self.viewport.snap(x, y)
        d = None
        if snap is not None and snap.kind in SNAPPABLE:
            d = float((snap.point - self._op.anchor).dot(self._op.normal))
            if abs(d) < 1e-6:
                d = None   # a point on the face's own plane (its own edges): no use, follow the mouse
        if d is None:
            snap = None
            d = self._distance_from_mouse(x, y)
        if d is not None:
            self._preview(d)
        if snap is not None:
            show_snap(self.viewport, snap)
        else:
            self.viewport.show_marker(None)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        held = bool(set(modifiers or ()) & {"Control", "Ctrl"})
        if self._op is not None:
            if held != self._held and isinstance(self._op, (_Op, _Many)):
                self._held = held
                self._preview(self._op.d)            # (Ctrl held on the last click: a solid)
            self._finish()
            return
        self._held = held
        self._start(x, y)

    def _start(self, x, y):
        """Start a Push/Pull on the face under (x, y). Returns True if started."""
        hit = self.viewport.pick(x, y)
        if hit is None:
            self.host.message(t("hint.pp.start"), warning=True)
            return False
        obj = self.doc.get(hit[0])
        if obj.is_bim:
            point = self.viewport.pick_point(x, y)
            return self._start_bim(obj, hit[1], point[2] if point is not None else None, x, y)
        fi = hit[1]
        normal = face_world_normal(obj.matrix, obj.mesh, fi)
        pts = face_world_points(obj.matrix, obj.mesh, fi)
        origin, direction = self.viewport.ray(x, y)
        denom = direction.dot(normal)
        anchor = origin + direction * ((pts[0] - origin).dot(normal) / denom) if abs(denom) > 1e-9 else pts[0]
        many = self._many(obj, fi, normal)
        if many is not None:
            faces, picked = many
            targets = [(k, frozenset(f), self.doc.get(k).mesh.copy(), self.doc.get(k).matrix.copy(),
                        bim.sheet_host(self.doc, self.doc.get(k))) for k, f in faces.items()]
            self._op = _Many(targets, picked, normal, anchor, pts, (x, y))
        else:
            self._op = _Op(obj.id, fi, obj.mesh.copy(), obj.matrix.copy(), normal, anchor, pts, (x, y),
                           host=bim.sheet_host(self.doc, obj))
        self.host.set_hint(self.hint())
        self._preview(0.0)
        return True

    def _many(self, obj, fi, normal):
        """(0.311) When a Push/Pull on face `fi` of sketch `obj` takes more than that face: ({obj_id: faces}, the
        sketches whose faces were picked). On a face picked (or of a sketch picked whole): all the faces picked, and
        of the sketches picked whole those looking the way the face clicked looks. Else the strips joined to it in
        one flat face (an offset's frame). None: that face alone, as before."""
        vp = self.viewport
        own = surface_faces(obj.mesh, fi)
        part = vp.face_selection.get(obj.id)
        if (part is not None and fi in part[0]) or obj.id in vp.selection:
            out = {}
            for k, (faces, _edges) in vp.face_selection.items():
                if self.doc.get(k) is not None and not self.doc.get(k).is_bim:
                    out[k] = set(faces)
            picked = set(out)
            for k in vp.selection:
                o = self.doc.get(k)
                if o is None or o.is_bim or k in out:
                    continue
                same = {g for g in range(len(o.mesh.faces))
                        if float(face_world_normal(o.matrix, o.mesh, g) @ normal) > 1 - 1e-6}
                if same:
                    out[k] = same
            out.setdefault(obj.id, set()).update(own)
            if len(out) > 1 or len(out[obj.id]) > 1:
                return out, picked
        if len(own) > 1 and all(float(face_world_normal(obj.matrix, obj.mesh, g) @ normal) > 1 - 1e-6 for g in own):
            return {obj.id: set(own)}, set()
        return None

    def pointer_up(self, x, y, button, modifiers):
        if button == LEFT and self._op is not None and moved_enough(self._op.press, (x, y)):
            self._finish()

    # ------------------------------------------------------------ keyboard

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        value = values[0]
        if self._op is not None:
            # the typed value goes the way the mouse went (outwards when it has not moved)
            self._preview((-1.0 if self._op.d < -1e-9 else 1.0) * value)
            self._finish()
            return
        last = self._last
        if isinstance(last, _LastBim) and self.doc.last_command() is last.cmd:
            # correct the last resize of an IFC element (or of a side of an opening)
            self.doc.undo()
            apply = self._apply_void if isinstance(last.op, _VoidOp) else self._apply_bim
            apply(last.op, (-1.0 if last.op.applied < -1e-9 else 1.0) * value)
            return
        if isinstance(last, _LastMany) and self.doc.last_command() is last.cmd:
            # correct the last Push/Pull of several faces: all of them again, from where they were
            self.doc.undo()
            op = last.op
            self._push_many(op, (-1.0 if op.applied < -1e-9 else 1.0) * value)
            if abs(op.applied) > 1e-9:
                self._commit_many(op)
            return
        if isinstance(last, _LastVoid) and self.doc.last_command() is last.cmd:
            # correct the last opening/niche: undo it (the rectangle comes back) and cut again
            self.doc.undo()
            sheet = self.doc.get(last.sheet_id)
            host = bim.sheet_host(self.doc, sheet) if sheet else None
            if host is not None:
                self._cut(sheet, host, min(value, host.thickness))
            return
        if last is not None and self.doc.last_command() is last.cmd:
            # SketchUp: a value typed right after finishing corrects the last Push/Pull.
            self.doc.undo()
            mesh = last.before.copy()
            result = push_pull(mesh, last.fi, last.matrix, last.sign * value, keep_start=last.keep)
            self._commit(last.obj_id, last.fi, last.before, last.matrix, mesh, result, last.keep)
            return
        # Forgiving: a distance typed over a face (without clicking) pushes/pulls that face.
        if self._hover_xy is not None and self._start(*self._hover_xy):
            self._preview(value)
            self._finish()
            return
        self.host.message(t("hint.pp.start"), warning=True)

    def cancel(self):
        if isinstance(self._op, _Op):
            self.viewport.refresh_object(self._op.obj_id)
        elif isinstance(self._op, _Many):
            for obj_id, *_rest in self._op.targets:
                self.viewport.refresh_object(obj_id)
        self._op = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    # ------------------------------------------------------------ internals

    def _hover(self, x, y):
        hit = self.viewport.pick(x, y)
        if hit is None:
            self.viewport.clear_overlays()
            return
        obj = self.doc.get(hit[0])
        if obj.is_bim:
            point = self.viewport.pick_point(x, y)
            void = self._void_face(obj, hit[1], point[2]) if point is not None else None
            if void is not None and void[3] == "":                   # (an opening drawn with slanted lines)
                self.viewport.clear_overlays()
                return
            if void is not None:                                     # a side of an opening: just that side
                frame, axis, side, _gid, lo, hi = void
                self.viewport.show_polygon(self._side_rect(frame, axis, lo[axis] if side > 0 else hi[axis], lo, hi))
                return
        face = self._bim_face(obj, hit[1]) if obj.is_bim else None
        if face is not None:
            frame, axis, side = face
            self.viewport.show_polygon(self._face_rect(frame, axis, side, 0.0))
        else:
            self.viewport.show_polygon(face_world_points(obj.matrix, obj.mesh, hit[1]))

    def _distance_from_mouse(self, x, y):
        op = self._op
        origin, direction = self.viewport.ray(x, y)
        if abs(direction.dot(op.normal)) > 0.995:
            # Looking straight along the normal: use the vertical mouse motion.
            towards_viewer = 1.0 if direction.dot(op.normal) < 0 else -1.0
            return (op.press[1] - y) * self.viewport.world_per_pixel(op.anchor) * towards_viewer
        return closest_on_line_to_ray(origin, direction, op.anchor, op.normal)

    # ------------------------------------------------------------ IFC elements

    def _bim_face(self, obj, fi):
        """(frame, axis, side) of an editable IFC element's face, or None."""
        if self.doc.ifc.kind_of(obj.id) not in ("wall", "slab", "column"):
            return None
        frame = bim.element_frame(self.doc, obj.id)
        n = np.linalg.inv(frame.matrix[:3, :3]) @ obj.mesh.face_normal(fi)
        axis = int(np.argmax(np.abs(n)))
        return frame, axis, (1 if n[axis] > 0 else -1)

    def _void_face(self, obj, fi, point):
        """If face `fi` of a wall / slab (hit at `point`) is a side of one of its openings or niches:
        (frame, axis, side, what, lo, hi) — what: its GlobalId, None if a door / window is in it, ""
        if it is not a box (an outline drawn with slanted lines). Else None."""
        if point is None or self.doc.ifc.kind_of(obj.id) not in ("wall", "slab"):
            return None
        cached = self._voids.get(obj.id)
        if cached is None or cached[0] != id(obj.mesh):
            try:
                cached = (id(obj.mesh), bim.element_frame(self.doc, obj.id), self.doc.ifc.voids(obj.id))
            except Exception:                       # (the IFC is still being read)
                return None
            self._voids[obj.id] = cached
        _mesh, frame, voids = cached
        if not voids:
            return None
        n = np.linalg.inv(frame.matrix[:3, :3]) @ obj.mesh.face_normal(fi)
        axis = int(np.argmax(np.abs(n)))
        side = 1 if n[axis] > 0 else -1             # (a side looking to +axis is at the opening's low end)
        local = frame.to_local(point)
        for gid, lo, hi, filled, box in voids:
            if not box and np.all(local >= lo - 2e-3) and np.all(local <= hi + 2e-3):
                return frame, axis, side, "", lo, hi          # (its sides are not moved one by one)
        if abs(n[axis]) < 0.99:
            return None
        others = [k for k in range(3) if k != axis]
        for gid, lo, hi, filled, box in voids:
            at = lo[axis] if side > 0 else hi[axis]
            if box and abs(local[axis] - at) < 2e-3 and all(lo[k] - 2e-3 <= local[k] <= hi[k] + 2e-3 for k in others):
                return frame, axis, side, (None if filled else gid), lo, hi
        return None

    @staticmethod
    def _side_rect(frame, axis, c, lo, hi):
        """World corners of the rectangle at `c` across `axis`, lo..hi along the other two (element frame)."""
        a, b = [k for k in range(3) if k != axis]
        pts = []
        for u, v in ((lo[a], lo[b]), (hi[a], lo[b]), (hi[a], hi[b]), (lo[a], hi[b])):
            p = np.zeros(3)
            p[axis], p[a], p[b] = c, u, v
            pts.append(frame.to_world(p))
        return pts

    @staticmethod
    def _box_after(frame, axis, side, d):
        lo, hi = _frame_box(frame)
        if side > 0:
            hi[axis] += d
        else:
            lo[axis] -= d
        return lo, hi

    def _face_rect(self, frame, axis, side, d):
        lo, hi = self._box_after(frame, axis, side, d)
        a, b = [k for k in range(3) if k != axis]
        c = hi[axis] if side > 0 else lo[axis]
        pts = []
        for u, v in ((lo[a], lo[b]), (hi[a], lo[b]), (hi[a], hi[b]), (lo[a], hi[b])):
            p = np.zeros(3)
            p[axis], p[a], p[b] = c, u, v
            pts.append(frame.to_world(p))
        return pts

    def _start_bim(self, obj, fi, point, x, y):
        kind = self.doc.ifc.kind_of(obj.id)
        if kind is None:
            self.host.message(t("err.not_editable"), warning=True)
            return False
        if kind in ("door", "window"):
            self.host.message(t("err.pp_filling"), warning=True)
            return False
        if kind in ("curved_wall", "ramp"):                          # (0.103 / 0.101: their sizes in Properties)
            self.host.message(t("err.pp_sizes_in_panel"), warning=True)
            return False
        if kind not in ("wall", "slab", "column"):
            self.host.message(t("err.pp_component"), warning=True)   # a component: edit it (all copies change)
            return False
        void = self._void_face(obj, fi, point)
        if void is not None:                       # a side of one of its openings / niches: that side moves
            if void[3] is None or void[3] == "":
                self.host.message(t("err.pp_door_opening" if void[3] is None else "err.pp_drawn_opening"), warning=True)
                return False
            return self._start_void(obj, void, point, x, y)
        frame, axis, side = self._bim_face(obj, fi)
        refuse = None
        if kind == "wall" and axis == 1:
            refuse = "err.pp_thickness"
        elif kind == "slab" and axis == 2:
            refuse = "err.pp_thickness"
        elif kind == "slab" and self.doc.ifc.slab_shape(obj.id) != "retangulo":
            refuse = "err.pp_slab_outline"                # (0.100: a polygon / circle changes by its outline)
        elif kind == "column" and not (axis == 2 and side > 0):
            refuse = "err.pp_section"
        if refuse:
            self.host.message(t(refuse), warning=True)
            return False
        # Most negative move allowed: keep a minimum size and every door/window/opening inside.
        lo, hi = _frame_box(frame)
        need = self.doc.ifc.opening_bounds(obj.id)
        if side > 0:
            keep = max(lo[axis] + 0.10, need[1][axis] if need is not None else -np.inf)
            d_min = keep - hi[axis]
        else:
            keep = min(hi[axis] - 0.10, need[0][axis] if need is not None else np.inf)
            d_min = lo[axis] - keep
        normal = obj.mesh.face_normal(fi)
        pts = self._face_rect(frame, axis, side, 0.0)
        origin, direction = self.viewport.ray(x, y)
        denom = direction.dot(normal)
        anchor = origin + direction * ((pts[0] - origin).dot(normal) / denom) if abs(denom) > 1e-9 else pts[0]
        self._op = _BimOp(obj.id, kind, axis, side, frame, normal, anchor, (x, y), min(d_min, 0.0))
        self.host.set_hint(self.hint())
        self._preview(0.0)
        return True

    # ------------------------------------------------------------ a side of an opening / niche

    def _start_void(self, obj, void, point, x, y):
        frame, axis, side, gid, lo, hi = void
        e_lo, e_hi = _frame_box(frame)
        # it can shrink to 1 cm (only the part inside the element counts: a through opening sticks out a hair)
        # and grow to 1 cm from the element's outline
        if side > 0:
            d_max = min(hi[axis], e_hi[axis]) - lo[axis] - 0.01
            d_min = -(lo[axis] - e_lo[axis] - 0.01)
        else:
            d_max = hi[axis] - max(lo[axis], e_lo[axis]) - 0.01
            d_min = -(e_hi[axis] - hi[axis] - 0.01)
        unit = frame.matrix[:3, axis] / np.linalg.norm(frame.matrix[:3, axis])
        self._op = _VoidOp(obj.id, gid, axis, side, frame, np.array(lo, dtype=float), np.array(hi, dtype=float),
                           unit * side, np.asarray(point, dtype=float), (x, y), min(d_min, 0.0), max(d_max, 0.0))
        self.host.set_hint(self.hint())
        self._preview(0.0)
        return True

    @staticmethod
    def _void_after(op, d):
        """The opening's box once its side moved d (along the side's normal: into the opening)."""
        lo, hi = op.lo.copy(), op.hi.copy()
        if op.side > 0:
            lo[op.axis] += d
        else:
            hi[op.axis] -= d
        return lo, hi

    def _preview_void(self, d):
        op = self._op
        d = min(max(d, op.d_min), op.d_max)
        op.d = op.applied = d
        lo, hi = self._void_after(op, d)
        corners = [op.frame.to_world(np.array([(lo, hi)[i][0], (lo, hi)[j][1], (lo, hi)[k][2]]))
                   for i in (0, 1) for j in (0, 1) for k in (0, 1)]
        segs = [p for a in range(8) for b in range(a + 1, 8) if bin(a ^ b).count("1") == 1
                for p in (corners[a], corners[b])]
        face = self._side_rect(op.frame, op.axis, lo[op.axis] if op.side > 0 else hi[op.axis], lo, hi)
        self.viewport.show_polygon(face, segments=segs, colors=[PREVIEW] * len(segs))
        size = (np.minimum(hi, _frame_box(op.frame)[1]) - np.maximum(lo, _frame_box(op.frame)[0]))[op.axis]
        self.viewport.show_label("{}  →  {}".format(_fmt(d), _fmt(size)), op.anchor + op.normal * d)
        self.viewport.show_tip("", None)
        self.host.set_vcb(_fmt(d))

    def _apply_void(self, op, d):
        d = min(max(d, op.d_min), op.d_max)
        lo, hi = self._void_after(op, d)
        try:
            bim.resize_void(self.doc, op.guid, op.void, lo, hi)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        op.applied = d
        self._last = _LastBim(self.doc.last_command(), op)
        across = 1 if self.doc.ifc.kind_of(op.guid) == "wall" else 2          # (the element's thickness)
        what = t("void.depth") if op.axis == across else t("void.height") if op.axis == 2 else t("void.width")
        e_lo, e_hi = _frame_box(op.frame)
        size = (np.minimum(hi, e_hi) - np.maximum(lo, e_lo))[op.axis]
        name = self.doc.get(op.guid).name if self.doc.get(op.guid) else ""
        self.host.message(t("info.void_size", name=name, what=what, v=_fmt(size)))
        self.host.set_vcb(_fmt(d))

    def _preview_bim(self, d):
        op = self._op
        d = max(d, op.d_min)
        op.d = op.applied = d
        lo, hi = self._box_after(op.frame, op.axis, op.side, d)
        corners = [op.frame.to_world(np.array([(lo, hi)[i][0], (lo, hi)[j][1], (lo, hi)[k][2]]))
                   for i in (0, 1) for j in (0, 1) for k in (0, 1)]
        segs = []
        for a in range(8):
            for b in range(a + 1, 8):
                if bin(a ^ b).count("1") == 1:     # box edges join corners differing in one axis
                    segs += [corners[a], corners[b]]
        face = self._face_rect(op.frame, op.axis, op.side, d)
        self.viewport.show_polygon(face, segments=segs, colors=[PREVIEW] * len(segs))
        size = (hi - lo)[op.axis]
        self.viewport.show_label("{}  →  {}".format(_fmt(d), _fmt(size)), op.anchor + op.normal * d)
        self.viewport.show_tip("", None)
        self.host.set_vcb(_fmt(d))

    def _apply_bim(self, op, d):
        d = max(d, op.d_min)
        lo, hi = _frame_box(op.frame)
        try:
            if op.kind == "wall" and op.axis == 0:
                bim.resize_wall(self.doc, op.guid, at_start=d if op.side < 0 else 0.0,
                                at_end=d if op.side > 0 else 0.0)
                what, size = t("props.length"), op.frame.length + d
            elif op.kind == "wall" and op.side < 0:           # its base: down (d > 0) or up, the top stays
                bim.resize_wall(self.doc, op.guid, at_base=d)
                what, size = t("props.height"), op.frame.height + d
            elif op.kind == "wall":
                bim.resize_wall(self.doc, op.guid, height=op.frame.height + d)
                what, size = t("props.height"), op.frame.height + d
            elif op.kind == "slab":
                lo2, hi2 = self._box_after(op.frame, op.axis, op.side, d)
                bim.resize_slab(self.doc, op.guid, lo2[0], lo2[1], hi2[0], hi2[1])
                what = t("props.lx") if op.axis == 0 else t("props.ly")
                size = (hi2 - lo2)[op.axis]
            else:
                bim.resize_column(self.doc, op.guid, op.frame.height + d)
                what, size = t("props.height"), op.frame.height + d
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        op.applied = d
        self._last = _LastBim(self.doc.last_command(), op)
        name = self.doc.get(op.guid).name if self.doc.get(op.guid) else ""
        self.host.message(t("info.edited", name=name, what=what, v=_fmt(size)))
        self.host.set_vcb(_fmt(d))

    # ------------------------------------------------------------ sketches

    def _preview(self, d):
        op = self._op
        if isinstance(op, _BimOp):
            self._preview_bim(d)
            return
        if isinstance(op, _VoidOp):
            self._preview_void(d)
            return
        if isinstance(op, _Many):
            self._preview_many(d)
            return
        tip = ""
        op.keep = self._keep()
        if op.host is not None and d < 0 and not op.keep:
            d = -min(-d, op.host.thickness)            # stops at the back face of the wall/slab
            tip = t("snap.through") if -d >= op.host.thickness - 1e-9 else t("snap.niche")
        mesh = op.before.copy()
        result = push_pull(mesh, op.fi, op.matrix, d, keep_start=op.keep)
        if result.mode == "hole":
            tip = t("snap.through")
        elif op.keep:
            tip = t("snap.pp_solid")
        op.d, op.applied, op.result, op.mesh = d, result.distance, result, mesh
        self.viewport.show_object(op.obj_id, mesh)
        offset = op.normal * op.applied
        moved = [p + offset for p in op.face_pts]
        segs = []
        for i, p in enumerate(moved):
            segs += [p, moved[(i + 1) % len(moved)]]
        segs += [op.anchor, op.anchor + offset]
        self.viewport.show_polygon(moved, segments=segs, colors=[PREVIEW] * len(segs))
        self.viewport.show_label(_fmt(op.applied), op.anchor + offset)
        self.viewport.show_tip(tip, moved[0] if tip else None)
        self.host.set_vcb(_fmt(op.applied))

    def _finish(self):
        op = self._op
        if abs(op.applied) < 1e-9:
            self.cancel()
            return
        self._op = None
        self.viewport.clear_overlays()
        if isinstance(op, _BimOp):
            self._apply_bim(op, op.applied)
        elif isinstance(op, _VoidOp):
            self._apply_void(op, op.applied)
        elif isinstance(op, _Many):
            self._commit_many(op)
        elif op.host is not None and op.applied < 0 and not op.keep:
            # a rectangle on an IFC wall/slab pushed in: an IFC opening or niche
            self.viewport.refresh_object(op.obj_id)
            self._cut(self.doc.get(op.obj_id), op.host, -op.applied)
        else:
            self._commit(op.obj_id, op.fi, op.before, op.matrix, op.mesh, op.result, op.keep)
        self.host.set_hint(self.hint())

    # ------------------------------------------------------------ several faces at once (0.311)

    def _push_many(self, op, d):
        """Each sketch's faces pushed `d` — the same for all of them: the tightest clamp wins (a rectangle lying on an
        IFC wall / slab stops at its back face, as one does). Sets op.d, op.results, op.applied."""
        hosts = [host for *_rest, host in op.targets if host is not None]
        if hosts and d < 0 and not op.keep:
            d = -min(-d, min(h.thickness for h in hosts))
        op.d = d
        for _pass in range(2):
            out = {}
            for obj_id, faces, before, matrix, _host in op.targets:
                mesh = before.copy()
                out[obj_id] = (mesh, push_pull_faces(mesh, faces, matrix, d, keep_start=op.keep))
            least = min((r.distance for _m, r in out.values()), key=abs)
            if all(abs(r.distance - least) < 1e-9 for _m, r in out.values()):
                break
            if abs(least) < 1e-9:                           # one of them cannot move: none does
                out = {k: (before.copy(), PushPullResult("none", 0.0, clamped=True))
                       for k, _f, before, _m, _h in op.targets}
                break
            d = least
        op.results, op.applied = out, least if abs(least) > 1e-9 else 0.0

    def _preview_many(self, d):
        op = self._op
        op.keep = self._keep()
        self._push_many(op, d)
        for obj_id, (mesh, _r) in op.results.items():
            self.viewport.show_object(obj_id, mesh)
        offset = op.normal * op.applied
        moved = [p + offset for p in op.face_pts]
        segs = []
        for i, p in enumerate(moved):
            segs += [p, moved[(i + 1) % len(moved)]]
        segs += [op.anchor, op.anchor + offset]
        self.viewport.show_polygon(moved, segments=segs, colors=[PREVIEW] * len(segs))
        self.viewport.show_label(_fmt(op.applied), op.anchor + offset)
        tip = t("snap.pp_solid") if op.keep else t("snap.pp_many", n=self._count(op)) if op.picked else ""
        self.viewport.show_tip(tip, moved[0] if tip else None)
        self.host.set_vcb(_fmt(op.applied))

    def _count(self, op):
        if not op.n:
            op.n = parts.count(self.doc, {k: (faces, False) for k, faces, *_rest in op.targets})
        return op.n

    def _commit_many(self, op):
        """One undo step: the sketches changed, and each rectangle lying on an IFC wall / slab pushed into it cut
        into it (an opening or a niche, as one alone). The faces picked stay picked where they now are."""
        d, n = op.applied, self._count(op)
        cut = {k for k, *_rest, host in op.targets if host is not None} if d < 0 and not op.keep else set()
        mark = self.doc.undo_mark()
        changes = [(k, before, op.results[k][0]) for k, _f, before, _m, _h in op.targets if k not in cut]
        if changes:
            self.doc.execute(ReplaceMeshes(changes, t("cmd.pp")))
        for k, _f, _b, _m, host in op.targets:
            if k in cut:
                bim.push_void(self.doc, self.doc.get(k), host, -d)
        self.doc.join_since(mark, t("cmd.pp"))
        self._last = _LastMany(self.doc.last_command(), op)
        self.host.set_vcb(_fmt(d))
        if op.picked:
            again = dict(self.viewport.face_selection)
            again.update({k: (frozenset(op.results[k][1].faces), False) for k in op.picked
                          if k not in cut and self.doc.get(k) is not None})
            self.viewport.select_faces(again)
        if any(r.clamped for _m, r in op.results.values()):
            self.host.message(t("warn.clamped", d=_fmt(d)), warning=True)
        elif op.picked or len(op.targets) > 1:
            self.host.message(t("info.pp_many_solid" if op.keep else "info.pp_many", n=n, d=_fmt(abs(d))))
        elif op.keep:
            self.host.message(t("info.pp_solid", d=_fmt(abs(d))))
        else:
            self.host.message(t("info.next_classify", d=_fmt(abs(d))))

    def _cut(self, sheet, host, depth):
        _guid, through = bim.push_void(self.doc, sheet, host, depth)
        self._last = _LastVoid(self.doc.last_command(), sheet.id)
        self.host.set_vcb(_fmt(depth))
        if through:
            self.host.message(t("info.void", wall=host.name))
        else:
            self.host.message(t("info.niche", d=_fmt(depth), wall=host.name))

    def _commit(self, obj_id, fi, before, matrix, mesh, result, keep=False):
        cmd = self.doc.execute(ReplaceMesh(obj_id, before, mesh, t("cmd.pp")))
        self._last = _Last(cmd, obj_id, fi, before, matrix, -1.0 if result.distance < 0 else 1.0, keep)
        self.host.set_vcb(_fmt(result.distance))
        link = getattr(self.doc.get(obj_id), "component", None)
        if keep and result.mode == "extrude":
            self.host.message(t("info.pp_solid", d=_fmt(abs(result.distance))))
        elif result.mode == "hole":
            self.host.message(t("info.hole", d=_fmt(abs(result.distance))))
        elif result.clamped:
            self.host.message(t("warn.clamped", d=_fmt(result.distance)), warning=True)
        elif link:
            self.host.message(t("info.component_editing", name=link["component"]))   # not "Classify": it is a component
        else:
            self.host.message(t("info.next_classify", d=_fmt(abs(result.distance))))
