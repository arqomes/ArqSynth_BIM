"""Line tool (SketchUp 'L'): click point after point; every segment is kept.

- Inferences as in the other tools (endpoint, intersection, midpoint, on edge,
  on guide, on face) plus the red / green / blue axes through the last point,
  and the alignments (0.60, core/tracking.py): lined up with the points the
  cursor rested on, parallel / perpendicular to an edge it rested on; Shift
  locks the direction.
- Typing a length + Enter draws the next segment that long, in the direction
  the mouse shows.
- Coming back to the first point closes the outline: the lines become one
  face of any shape (L, U, triangle...) that Push/Pull can raise. (0.372) So does
  ending on the chain anywhere else — on one of its points or along one of its
  lines — or crossing it, as in SketchUp (core/lines.chain_loops): each loop it
  makes a face, the lines on no loop (the tail it started with, what goes on
  past a crossing) stay lines.
- A line across a face, from its outline to its outline (or a path of lines
  through it), divides the face: Push/Pull then moves one part only. On an
  IFC wall or slab, the face gets two rectangles (model/imprint.py).
- Esc or right click ends the chain; the open lines stay (they can be
  selected, deleted and are saved with the sketches).
- (0.151) Tab — or the contextual bar — makes the next segments arcs: tangent to the segment before
  (SketchUp's tangent arc; the first one, a half circle), in pieces of 15°; the outline closes into a
  face as with straight lines, and pulled, its curved sides are smooth.
"""

import numpy as np

from ..core.lines import LOOP_TOL, chain_loops, drop_collinear, polygon_frame, tangent_arc
from ..core.mesh import PolyMesh
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, refusal, t
from ..model import imprint, line_edit, line_faces
from ..model.document import AddObject, ReplaceMesh, ReplaceObjects, SketchObject
from ..render.viewport import PREVIEW
from .base import (
    LEFT, RIGHT, SNAP_COLORS, Option, Tool, draw_option, drawing_dims, point_from, show_snap, show_start_reference,
    start_plane, start_reference, switch_draw,
)
from ..core.sketch_geometry import ray_plane
from ..core.temp_dims import revit as revit_look
from . import pick_lines

CLOSE_PX = 12
MIN_LENGTH = 0.001


def _fmt(value):
    return format_length(value, decimal_sep())


def _area(value):
    """An area's number for «… m²» (0.372: a length's format added its own « m»: «20,00 m m²»)."""
    return "{:.2f}".format(value).replace(".", decimal_sep())


class LineTool(Tool):
    name = "line"
    accepts_typing = True

    def __init__(self, host):
        super().__init__(host)
        self._hover_xy = None
        self.arc = False        # (0.151) the next segments arcs, tangent to the one before
        self.picking = False    # (0.451) Revit's «Pick Lines»: a line on the line or edge clicked…
        self.offset = 0.0       # …this far from it, on the mouse's side
        self.filleting = False  # (0.452) Revit's «Fillet Arc»: two lines picked, the arc between them
        self.chain = True       # (0.453) Revit's «Chain»: off, each line starts with a click of its own
        self._fillet = []       # …the pieces picked: [((obj_id, i, j), the point clicked, (a, b) world)]
        self._fillet_now = None
        self._reset()

    def options(self):
        # (0.450) the drawing tools side by side, as Revit's «Draw» panel — its arcs one of them (Tab still turns them
        # on and off); (0.451) picking lines, with their offset
        current = "pick" if self.picking else "fillet" if self.filleting else "line_arc" if self.arc else "line"
        opts = [draw_option(current)]
        if self.picking:
            opts.append(Option("offset", t("ctx.offset"), "length", float(self.offset)))
        elif not self.filleting:                             # (0.453) Revit's «Chain»
            opts.append(Option("chain", t("ctx.chain"), "toggle", self.chain))
        return opts

    def take_draw(self, value):
        """(0.450) Straight lines, their arcs, picking lines (0.451) or a fillet arc (0.452), from the bar's row."""
        self.cancel()
        self.picking = value == "pick"
        self.filleting = value == "fillet"
        self.arc = value == "line_arc"
        self.host.set_hint(self.hint())

    def set_option(self, key, value):
        if key == "shape":
            self.arc = value == "arc"
        elif key == "draw" and value in ("line", "line_arc", "pick", "fillet"):
            self.take_draw(value)
        elif key == "draw":
            switch_draw(self, value)
            return
        elif key == "offset":
            self.offset = float(value)
        elif key == "chain":
            self.chain = bool(value)
        self.host.set_hint(self.hint())

    # ------------------------------------------------------------ (0.452) Revit's «Fillet Arc» on lines

    def _segment_at(self, x, y):
        """(the piece (obj_id, i, j), the point under the mouse, its ends (a, b) world) of the loose line under the
        mouse, or None."""
        snap, _hit = self.viewport.snap(x, y)
        if snap is None or snap.obj_id is None:
            return None
        obj = self.doc.get(snap.obj_id)
        point = np.asarray(snap.point, dtype=float)
        if obj is not None and not obj.is_bim and obj.mesh.faces:     # (0.455) a polygon's side (a sketch's face)
            found = line_edit.face_edge_at(obj, point)
            return None if found is None else ((snap.obj_id, *found[0]), point, found[1])
        if not line_edit.is_lines(obj) or obj.curve:
            return None
        best = None
        for i, j, a, b in line_edit.segments(obj):
            d = b - a
            s = float(np.clip((point - a) @ d / max(float(d @ d), 1e-12), 0.0, 1.0))
            gap = float(np.linalg.norm(a + d * s - point))
            if best is None or gap < best[0]:
                best = (gap, (snap.obj_id, i, j), (a, b))
        if best is None or best[0] > 1e-3:
            return None
        return best[1], point, best[2]

    def _fillet_move(self, x, y):
        if len(self._fillet) < 2:
            found = self._segment_at(x, y)
            self.viewport.clear_overlays()
            if found is not None and hasattr(self.viewport, "show_glyph"):
                self.viewport.show_glyph(None, None, found[2])
            self.viewport.show_tip(t("tip.fillet_line", n=len(self._fillet) + 1), found[1] if found else None)
            return
        from ..core.fillet import arc_points, fillet
        (_sa, keep_a, ea), (_sb, keep_b, eb) = self._fillet[:2]
        origin, direction = self.viewport.ray(x, y)
        mouse = ray_plane(origin, direction, ea[0], np.array((0.0, 0.0, 1.0)))
        f = fillet(ea, keep_a, eb, keep_b, through=mouse) if mouse is not None else None
        self._fillet_now = f
        if f is None:
            self.viewport.clear_overlays()
            return
        z = float(ea[0][2])
        pts = [np.array((*p, z)) for p in arc_points(f)]
        segs = [q for a, b in zip(pts, pts[1:]) for q in (a, b)]
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))
        if hasattr(self.viewport, "show_glyph"):
            self.viewport.show_glyph()
        self.viewport.show_tip(t("tip.fillet_radius", r=_fmt(f.radius)), pts[len(pts) // 2])
        self.host.set_vcb(_fmt(f.radius))

    def _fillet_down(self, x, y, radius=None):
        if len(self._fillet) < 2:
            found = self._segment_at(x, y)
            if found is None:
                self.host.message(t("tip.fillet_line", n=len(self._fillet) + 1), warning=True)
                return
            if self._fillet and self._fillet[0][0] == found[0]:
                return
            face = lambda pick: bool(self.doc.get(pick[0][0]).mesh.faces)           # noqa: E731
            if self._fillet and face(self._fillet[0]) != face(found):  # (0.455: two lines, or two sides of a polygon)
                self.host.message(t("err.edit_refused", e=refusal(line_edit.LineRefused("not_corner"))), warning=True)
                return
            self._fillet.append(found)
            self.host.set_hint(self.hint())
            return
        f = self._fillet_now if radius is None else True
        if f is None:
            self.host.message(t("err.fillet_none"), warning=True)
            return
        (seg_a, keep_a, _ea), (seg_b, keep_b, _eb) = self._fillet[:2]
        r = radius if radius is not None else self._fillet_now.radius
        polygon = self.doc.get(seg_a[0]) is not None and bool(self.doc.get(seg_a[0]).mesh.faces)
        try:
            if polygon:                                      # (0.455) a polygon's corner: the face rounded there
                line_edit.fillet_face(self.doc, seg_a, keep_a, seg_b, keep_b, r, t("cmd.fillet"))
            else:
                line_edit.fillet_lines(self.doc, seg_a, keep_a, seg_b, keep_b, r, t("cmd.fillet"))
        except line_edit.LineRefused as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self.host.message(t("info.fillet_polygon" if polygon else "info.fillet_lines", r=_fmt(r)))
        self._fillet, self._fillet_now = [], None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())

    def _pick_move(self, x, y):
        """(0.451) The line a click would make on the line or edge under the mouse, shown."""
        found = self._picked(x, y)
        if found is None:
            self.viewport.clear_overlays()
            return
        a, b, edge = found
        self.viewport.show_polygon([], segments=[a, b], colors=[PREVIEW, PREVIEW])
        if hasattr(self.viewport, "show_glyph"):
            self.viewport.show_glyph(None, None, edge)
        self.host.set_vcb(_fmt(float(np.linalg.norm(b - a))))

    def _picked(self, x, y):
        """(a, b, the edge picked) of the line a click would make, or None: on the edge, moved by the offset to the
        mouse's side."""
        edge = pick_lines.edge_at(self.viewport, self.doc, x, y)
        if edge is None:
            return None
        a, b = (np.asarray(p, dtype=float) for p in edge)
        origin, direction = self.viewport.ray(x, y)
        mouse = ray_plane(origin, direction, a, np.array((0.0, 0.0, 1.0)))
        side = pick_lines.side_of(a, b, mouse if mouse is not None else (a + b) / 2)
        a, b = pick_lines.offset_segment(a, b, abs(self.offset), side)
        return a, b, edge

    def _pick_down(self, x, y):
        found = self._picked(x, y)
        if found is None:
            self.host.message(t("tip.wall_pick_none"), warning=True)
            return
        a, b, _edge = found
        self._reset()
        self._pts = [a]
        self._append_line(b)
        self._reset()
        self.viewport.clear_overlays()
        self.host.message(t("info.line_on_picked", l=_fmt(float(np.linalg.norm(b - a)))))

    def tab(self):
        """Tab: straight lines ↔ arcs (0.151)."""
        self.arc = not self.arc
        self.host.message(t("info.line_arc" if self.arc else "info.line_straight"))
        self.host.set_hint(self.hint())
        return True

    def _arc_to(self, p):
        """(0.151) The arc's points from the chain's last point to p: tangent to the last segment; the first one a
        half circle (bulging to the right of the way it goes)."""
        last = self._pts[-1]
        if len(self._pts) >= 2 and np.linalg.norm(self._pts[-1] - self._pts[-2]) > 1e-9:
            tangent = self._pts[-1] - self._pts[-2]
        else:
            tangent = np.cross(np.asarray(p, float) - last, self._normal)
        return tangent_arc(last, tangent, p, self._normal)

    def _reset(self):
        self._fillet, self._fillet_now = [], None       # (0.452: the lines picked for a fillet, let go)
        self._pts = []          # points of the current chain (world)
        self._normal = None     # plane of the first click: where free points go
        self._obj_id = None     # sketch object holding the chain's lines
        self._end = None        # next point under the mouse
        self._closing = False
        self._hover = None      # before the first click: the StartPlane under the mouse…
        self._start_ref = None  # …and where a typed distance would start from (base.start_reference)

    def hint(self):
        if self.picking:                                     # (0.451)
            return t("hint.line.pick")
        if self.filleting:                                   # (0.452)
            return t("hint.line.fillet_" + str(min(len(self._fillet), 2)))
        if self.arc:
            return t("hint.line.arc_next") if self._pts else t("hint.line.arc_start")
        return t("hint.line.next") if self._pts else t("hint.line.start")

    def vcb_title(self):
        return t("vcb.length")

    # ------------------------------------------------------------ mouse

    def pointer_move(self, x, y, modifiers):
        self._hover_xy = (x, y)
        if self.picking:                                     # (0.451) Revit's «Pick Lines»
            self._pick_move(x, y)
            return
        if self.filleting:                                   # (0.452) Revit's «Fillet Arc»
            self._fillet_move(x, y)
            return
        if not self._pts:
            plane = start_plane(self.host, x, y, modifiers)
            show_snap(self.viewport, plane.snap if plane else None, plane.point if plane else None)
            self._hover = plane
            self._start_ref = start_reference(plane.snap) if plane is not None else None
            show_start_reference(self.viewport, self._start_ref, plane.point if plane else None,
                                 plane.normal if plane else None)
            return
        found = self._next_point(x, y, modifiers)
        if found is None:
            return
        self._end, tip, marker, line = found
        self._preview(tip, marker, line)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self.picking:                                     # (0.451) a line on the line or edge clicked
            self._pick_down(x, y)
            return
        if self.filleting:                                   # (0.452) two lines, then the arc between them
            self._fillet_down(x, y)
            return
        if not self._pts:
            plane = start_plane(self.host, x, y, modifiers)
            if plane is None:
                self.host.message(t("err.no_point"), warning=True)
                return
            self._pts = [plane.point.copy()]
            self._normal = plane.normal
            self.viewport.clear_overlays()
            self.host.set_hint(self.hint())
            return
        found = self._next_point(x, y, modifiers)
        if found is not None:
            self._add(found[0])

    # ------------------------------------------------------------ keyboard

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        length = values[0]
        if self.filleting:                                   # (0.452) the fillet's radius typed
            if len(self._fillet) >= 2 and length is not None and length > 0:
                self._fillet_down(0, 0, radius=length)
            return
        if not self._pts:
            if self._start_ref is None or self._hover is None:
                self.host.message(t("hint.start_typed"), warning=True)
                return
            # a distance typed before the first click: the line starts that far from the point followed
            src, direction = self._start_ref
            self._pts = [src + direction * length]
            self._normal = self._hover.normal
            self.viewport.clear_overlays()
            self.host.set_hint(self.hint())
            self.host.message(t("info.start_typed", l=_fmt(length)))
            return
        last = self._pts[-1]
        if self._end is None or np.linalg.norm(self._end - last) < 1e-9:
            self.host.message(t("hint.line.direction"), warning=True)
            return
        d = (self._end - last) / np.linalg.norm(self._end - last)
        self._add(last + d * length)

    def cancel(self):
        self._reset()
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    # ------------------------------------------------------------ inferences

    def _near_screen(self, point, x, y):
        px, py = self.viewport.project(point)
        return bool(np.hypot(px - x, py - y) <= CLOSE_PX)

    def _next_point(self, x, y, modifiers=()):
        """(point, tip, marker colour, line colour) for the mouse at (x, y), or None."""
        last = self._pts[-1]
        self._closing = False
        if len(self._pts) >= 3 and self._near_screen(self._pts[0], x, y) and "Shift" not in (modifiers or ()):
            self._closing = True
            self.viewport.show_alignments()
            return self._pts[0].copy(), t("snap.close"), SNAP_COLORS["endpoint"], PREVIEW
        return point_from(self.viewport, last, self._normal, x, y, modifiers)

    # ------------------------------------------------------------ internals

    def _add(self, p):
        last = self._pts[-1]
        if np.linalg.norm(p - last) < MIN_LENGTH:
            return                                  # same point: keep waiting
        if self.arc:
            self._add_arc(p)
            return
        if len(self._pts) >= 3 and np.linalg.norm(p - self._pts[0]) < 1e-6:
            self._close()
            return
        lines = self.doc.get(self._obj_id) if self._obj_id is not None else None
        split = imprint.split_by_path(self.doc, self._pts + [p], lines, self.viewport.is_shown)
        if split is not None:
            # across a face, from its outline to its outline: the face is divided (the lines become
            # its edges); the chain goes on from here
            self.doc.execute(split.command)
            self._pts, self._obj_id, self._end = [np.asarray(p, dtype=float).copy()], None, None
            self.viewport.clear_overlays()
            self.host.message(t("info.split_host", wall=split.host) if split.host
                              else t("info.split", n=split.faces))
            return
        if self._close_loops(self._pts + [np.asarray(p, dtype=float)]):
            return
        if self._close_with_others(last, np.asarray(p, dtype=float)):
            return
        self._append_line(p)
        self._pts.append(np.asarray(p, dtype=float).copy())
        self._end = None
        self.viewport.clear_overlays()
        wall = imprint.host_face(self.doc, last, p, self.viewport.is_shown)
        if wall:                                    # on a wall's face, but it did not divide it: say why
            self.host.message(t("info.line_on_wall", wall=wall), warning=True)
        else:
            self.host.message(t("info.line", l=_fmt(float(np.linalg.norm(p - last)))))
        self.host.set_vcb(_fmt(float(np.linalg.norm(p - last))))
        self._chain_off()

    def _add_arc(self, p):
        """(0.151) An arc to p, kept as its pieces (one undo step each, as lines); back at the first point, the
        outline closes into a face."""
        pts = self._arc_to(np.asarray(p, dtype=float))
        if not pts:
            return
        closing = len(self._pts) >= 2 and np.linalg.norm(pts[-1] - self._pts[0]) < 1e-6
        if not closing and self._close_loops(self._pts + [np.asarray(q, dtype=float) for q in pts]):
            return                                  # (0.372: the arc closed the chain elsewhere)
        for q in (pts[:-1] if closing else pts):
            self._append_line(q)
            self._pts.append(np.asarray(q, dtype=float).copy())
        self._end = None
        self.viewport.clear_overlays()
        if closing:
            self._close()
            return
        self.host.message(t("info.arc", n=len(pts)))
        self._chain_off()

    def _chain_off(self):
        """(0.453) Revit's «Chain» off: the piece just drawn stands alone, the next starts with a click."""
        if not self.chain:
            self._reset()
            self.host.set_hint(self.hint())

    def _append_line(self, p, to_first=False):
        """Keep one more segment of the chain (one undo step)."""
        obj = self.doc.get(self._obj_id) if self._obj_id is not None else None
        if obj is None:
            mesh = PolyMesh([self._pts[-1], p], lines=[(0, 1)])
            obj = SketchObject(t("obj.lines", n=self.doc.next_number()), np.eye(4), mesh)
            self.doc.execute(AddObject(obj, t("cmd.line")))
            self._obj_id = obj.id
            return
        mesh = obj.mesh.copy()
        last = len(mesh.verts) - 1                  # the chain's last point is the last vertex
        mesh.lines.append((last, 0 if to_first else mesh.add_vert(p)))
        self.doc.execute(ReplaceMesh(obj.id, obj.mesh, mesh, t("cmd.line")))

    def _close(self):
        """Back at the first point: the outline becomes a face (one undo step)."""
        pts = drop_collinear(self._pts)
        frame = polygon_frame(pts, view_dir=self.viewport.view_direction()) if len(pts) >= 3 else None
        if frame is None:
            # not on one plane: the outline stays as lines
            self._append_line(self._pts[0], to_first=True)
            self.host.message(t("warn.not_planar"), warning=True)
            self.cancel()
            return
        matrix, local = frame
        face = SketchObject(t("obj.name", n=self.doc.next_number()), matrix,
                            PolyMesh(local, [list(range(len(local)))]))
        lines = self.doc.get(self._obj_id)
        self.doc.execute(ReplaceObjects([lines] if lines is not None else [], [face], t("cmd.face")))
        area = face.mesh.face_area(0)
        self.cancel()
        self.host.message(t("info.face", n=len(local), a=_area(area)))

    def _close_loops(self, chain):
        """(0.372) The chain — with what is about to be added — closed on itself somewhere else than at its first
        point: ending on one of its points or along one of its lines, or crossing it (core/lines.chain_loops). Each
        loop becomes a face (those on one plane one object, sharing their edges), the lines on no loop stay lines
        — one undo step, in place of the chain's lines. Ending on a loop ends the chain; past a crossing, it goes on
        from the end. Returns True when faces were made."""
        if len(chain) < 4:
            return False
        loops, loose = chain_loops(chain)
        if not loops:
            return False
        made, area, corners = [], 0.0, 0
        for matrix, rings in self._planes(loops):
            verts, faces = [], []
            for ring in rings:
                face = []
                for q in ring:
                    k = next((i for i, v in enumerate(verts) if np.linalg.norm(v - q) <= LOOP_TOL), None)
                    if k is None:
                        verts.append(q)
                        k = len(verts) - 1
                    face.append(k)
                faces.append(face)
            mesh = PolyMesh(verts, faces)
            made.append(SketchObject(t("obj.name", n=self.doc.next_number()), matrix, mesh))
            area += sum(mesh.face_area(k) for k in range(len(faces)))
            corners = len(rings[0])
        if not made:
            return False                            # (not on one plane: it stays as lines)
        if loose:
            ends = []
            for a, b in loose:
                for q in (a, b):
                    if not any(np.linalg.norm(q - e) <= LOOP_TOL for e in ends):
                        ends.append(q)
            index = [[next(i for i, e in enumerate(ends) if np.linalg.norm(e - q) <= LOOP_TOL) for q in pair]
                     for pair in loose]
            made.append(SketchObject(t("obj.lines", n=self.doc.next_number()), np.eye(4),
                                     PolyMesh(ends, lines=[tuple(pair) for pair in index])))
        lines = self.doc.get(self._obj_id) if self._obj_id is not None else None
        self.doc.execute(ReplaceObjects([lines] if lines is not None else [], made, t("cmd.face")))
        end = np.asarray(chain[-1], dtype=float)
        faces_made = sum(len(o.mesh.faces) for o in made)
        text = (t("info.face_closed", n=corners, a=_area(area)) if faces_made == 1
                else t("info.faces_closed", n=faces_made, a=_area(area)))
        if any(np.linalg.norm(q - end) <= LOOP_TOL for loop in loops for q in loop):
            self.cancel()                           # (ended on a loop: the outline is closed)
        else:
            self._pts, self._obj_id, self._end = [end.copy()], None, None     # (past a crossing: it goes on)
            self.viewport.clear_overlays()
        self.host.message(text)
        return True

    def _close_with_others(self, a, b):
        """(0.373) The segment a-b closes an outline with loose lines drawn before — another chain, an arc, a curve —
        as SketchUp's (model/line_faces): the face made, one undo step. Ending on the loop ends the chain; else it
        goes on from b. True when a face was made."""
        seg = SketchObject(None, np.eye(4), PolyMesh([a, b], lines=[(0, 1)]))       # (named if it stays)
        closed = line_faces.close_with(self.doc, seg, (a, self._normal), t("cmd.face"),
                                       view_dir=self.viewport.view_direction())
        if closed is None:
            return False
        ended = any(np.linalg.norm(q - b) <= LOOP_TOL for f in closed.faces
                    for q in (f.matrix[:3, :3] @ np.asarray(v) + f.matrix[:3, 3] for v in f.mesh.verts))
        if ended:
            self.cancel()
        else:
            self._pts, self._obj_id, self._end = [b.copy()], None, None
            self.viewport.clear_overlays()
        self.host.message(t("info.face_closed", n=closed.corners, a=_area(closed.area)))
        return True

    def _planes(self, loops):
        """(0.372) The loops by plane: [(matrix, [local rings])] — each ring in the frame of the first on its plane
        (polygon_frame: its normal up, else towards the viewer), counter-clockwise there, without corners along a
        straight side."""
        out = []
        for loop in loops:
            ring = np.asarray(drop_collinear(loop), dtype=float)
            for matrix, rings in out:
                local = (np.linalg.inv(matrix) @ np.column_stack((ring, np.ones(len(ring)))).T).T[:, :3]
                if np.all(np.abs(local[:, 2]) <= LOOP_TOL * 10):
                    local[:, 2] = 0.0
                    x, y = local[:, 0], local[:, 1]
                    signed = float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))
                    rings.append(local[::-1].copy() if signed < 0 else local)
                    break
            else:
                frame = polygon_frame(ring, view_dir=self.viewport.view_direction())
                if frame is not None:
                    out.append((frame[0], [frame[1]]))
        return out

    def _preview(self, tip, marker, line):
        last, end = self._pts[-1], self._end
        if self.arc:                                # (0.151) the arc as it would be
            pts = [last] + self._arc_to(end)
            segs = [q for a, b in zip(pts, pts[1:]) for q in (a, b)]
            self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))
            self.viewport.show_marker(end, marker)
            self.viewport.show_tip(tip, end if tip else None)
            self.host.set_vcb(_fmt(float(np.linalg.norm(end - last))))
            return
        if self._closing:
            ring = self._pts
            segs = []
            for i in range(len(ring)):
                segs += [ring[i], ring[(i + 1) % len(ring)]]
            self.viewport.show_polygon(ring, segments=segs, colors=[PREVIEW] * len(segs))
        else:
            self.viewport.show_polygon([], segments=[last, end], colors=[line, line])
        length = float(np.linalg.norm(end - last))
        drawing_dims(self.viewport, last, end, self._normal)          # (its length and angle, as Revit)
        if revit_look():                                  # (0.448: Revit's glyph — put by point_from — not a dot)
            self.viewport.show_marker(None)
            if self._closing:
                self.viewport.show_glyph("endpoint", end)
        else:
            self.viewport.show_marker(end, marker)
        self.viewport.show_tip(tip, end if tip else None)
        self.host.set_vcb(_fmt(length))
