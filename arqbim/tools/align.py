"""Align (0.107), as Revit's AL: a click on a reference — a grid axis, an edge, or a face of a wall — then on a
face of a wall or a column parallel to it: the element moves across until that face lies on the reference (the
walls joined to it follow). (0.332) Or, the second click on a line of a surface pattern (a tile's joint, a brick
course — lit under the mouse, as Revit's): the pattern moves on its face until that line lies on the reference, or
turns about where the two meet when they are not parallel; kept in the element (ifc/pattern_align.py). The reference
stays for the next ones; the right button or Esc lets it go.

(0.449, the owner: «o comando alinhar precisa melhorar e deve funcionar com linhas, pisos, e qualquer elementos no
projeto») Any element: the reference and what is aligned may be any edge or line under the mouse — a loose line, a
slab's or a floor's edge, a roof's, a piece of furniture's… — or, a click inside an element, its edge nearest the
mouse (for what is aligned: the nearest one parallel to the reference, lit). A loose line moves alone (the lines
joined to it stretch, as Revit's); a door or a window slides along its wall; any other element moves whole."""

import math

import numpy as np

from ..core.inference import ON_EDGE, ON_GUIDE
from ..core.sketch_geometry import transform_point
from ..core.units import format_angle, format_length
from ..i18n import decimal_sep, refusal, t
from ..model import bim, line_edit
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, SNAP_COLORS, Tool

TARGET_COLOUR = (0.93, 0.42, 0.05, 1.0)   # (0.449) the edge to be aligned, lit in orange
EDGE_PICK_PX = 12.0                       # (0.449) inside an element: its edge within this many pixels, else the nearest

Z = np.array((0.0, 0.0, 1.0))
PARALLEL = np.sin(np.radians(1.0))        # (the faces aligned: within 1°)
REACH = 30.0                              # m: how long the reference is drawn each way
PATTERN_REACH = 3.0                       # (0.332) m: how long the pattern's line picked is drawn each way…
PATTERN_COLOUR = (0.93, 0.42, 0.05, 1.0)  # …in orange
TURNED = 1e-3                             # degrees: less than this, the pattern's line is parallel to the reference


def _fmt(v):
    return format_length(v, decimal_sep())


def _unit2(v):
    v = np.array((float(v[0]), float(v[1])))
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-9 else None


def _unit(v):
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else None


def level_edges(obj):
    """(0.449) An element's or a sketch's edges lying level (world): (K, 2, 3) — an IFC element's visible edges, a
    loose line's pieces, a sketch's faces' sides."""
    if obj is None:
        return np.zeros((0, 2, 3))
    mesh = obj.mesh
    if obj.is_bim:
        if not hasattr(mesh, "edge_array"):
            return np.zeros((0, 2, 3))
        pairs, _faces = mesh.edge_array()
        v = np.asarray(mesh.verts, dtype=float).reshape(-1, 3)
        edges = np.stack((v[pairs[:, 0]], v[pairs[:, 1]]), axis=1) if len(pairs) else np.zeros((0, 2, 3))
    elif line_edit.is_lines(obj):
        edges = np.array([(a, b) for _i, _j, a, b in line_edit.segments(obj)], dtype=float).reshape(-1, 2, 3)
    else:
        world = [transform_point(obj.matrix, p) for p in mesh.verts]
        pairs = {tuple(sorted((int(f[k]), int(f[(k + 1) % len(f)])))) for f in mesh.faces for k in range(len(f))}
        pairs |= {tuple(sorted((int(i), int(j)))) for i, j in (mesh.lines or ())}
        edges = np.array([(world[i], world[j]) for i, j in sorted(pairs)], dtype=float).reshape(-1, 2, 3)
    if not len(edges):
        return edges
    flat = np.abs(edges[:, 1, 2] - edges[:, 0, 2]) < 1e-6
    long = np.linalg.norm(edges[:, 1, :2] - edges[:, 0, :2], axis=1) > 1e-4
    return edges[flat & long]


def nearest_edge(edges, point, along=None):
    """(0.449) Of `edges` (K, 2, 3), the one nearest `point` in the plan — (its index, its distance) — among those
    parallel to `along` (2,) within 1° when given; None when there is none."""
    if not len(edges):
        return None
    a, b = edges[:, 0, :2], edges[:, 1, :2]
    d = b - a
    length = np.linalg.norm(d, axis=1)
    u = d / np.maximum(length, 1e-12)[:, None]
    keep = np.ones(len(edges), dtype=bool)
    if along is not None:
        keep = np.abs(u[:, 0] * along[1] - u[:, 1] * along[0]) <= PARALLEL
    if not keep.any():
        return None
    p = np.asarray(point, dtype=float)[:2]
    s = np.clip(np.einsum("ij,ij->i", p - a, u), 0.0, length)
    dist = np.linalg.norm(a + u * s[:, None] - p, axis=1)
    dist[~keep] = np.inf
    k = int(np.argmin(dist))
    return k, float(dist[k])


class AlignTool(Tool):
    name = "align"
    placement = True                      # (Esc: back to Select)
    keys_help = "keys.align"

    def __init__(self, host):
        super().__init__(host)
        # the reference: (a point and the unit direction in plan — None when not level —, its level, what it is, a
        # point and the unit direction in 3D)
        self._ref = None
        self._move = None                 # (element, the move) under the mouse
        self._pattern = None              # (0.332) (element, face normal, pivot, angle, shift) under the mouse

    def hint(self):
        return t("hint.align_2") if self._ref is not None else t("hint.align")

    # ------------------------------------------------------------ what is under the mouse

    def _faces(self, guid):
        """[(a point, unit direction, outward normal)] (plan) of the faces of a straight wall (its two sides) or a
        column (its four)."""
        ifc = self.doc.ifc
        kind = ifc.kind_of(guid)
        if kind == "wall":
            s, e, th = ifc.wall_axis(guid)
            d = _unit2(e - s)
            n = np.array((-d[1], d[0]))
            return [(s[:2] + n * th / 2, d, n), (s[:2] - n * th / 2, d, -n)]
        if kind == "column":
            centre, x, (a, b), _base, _top = ifc.column_box(guid)
            x = _unit2(x)
            y = np.array((-x[1], x[0]))
            return [(centre[:2] + x * a, y, x), (centre[:2] - x * a, y, -x), (centre[:2] + y * b, x, y),
                    (centre[:2] - y * b, x, -y)]
        return []

    def _face_at(self, x, y):
        """(element, face) of the wall / column face nearest the point under the mouse, or None."""
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None
        obj = self.doc.get(hit[0])
        if obj is None or not obj.is_bim:
            return None
        faces = self._faces(obj.id)
        if not faces:
            return None
        p = np.asarray(hit[2], dtype=float)[:2]
        best = min(faces, key=lambda f: abs(float((p - f[0]) @ f[2])))
        return obj.id, best, float(hit[2][2])

    def _reference_at(self, x, y):
        """(point, direction, level, label, point 3D, direction 3D) of a reference under the mouse: a grid axis, an
        edge (0.332: a sloping or upright one too — for a pattern; direction None), a face."""
        k = self.viewport.grid_axis_at(x, y)
        if k is not None and "grid" not in self.viewport.unselectable:
            axis = self.doc.grids[k]
            d = _unit2(np.asarray(axis.end) - np.asarray(axis.start))
            if d is not None:
                p, z = np.asarray(axis.start, dtype=float)[:2], float(self.viewport.grid_level())
                return p, d, z, t("align.grid", tag=axis.tag), np.array((*p, z)), np.array((*d, 0.0))
        snap, _hit = self.viewport.snap(x, y)
        edge = self._edge_of(snap)
        if edge is not None:
            a, b = (np.asarray(p, dtype=float) for p in edge)
            along = _unit(b - a)
            if along is not None:
                level = abs(float(b[2] - a[2])) < 1e-6
                label = t("align.line") if line_edit.is_lines(self.doc.get(snap.obj_id)) else t("align.edge")
                return a[:2], _unit2(b - a) if level else None, float(a[2]), label, a, along
        face = self._face_at(x, y)
        if face is not None:
            _g, (p, d, _n), z = face
            return p, d, z, t("align.face"), np.array((*p, z)), np.array((*d, 0.0))
        hit = self.viewport.pick_point(x, y)                # (0.449) inside any element: its nearest edge
        if hit is not None:
            edges = level_edges(self.doc.get(hit[0]))
            found = nearest_edge(edges, hit[2])
            if found is not None:
                a, b = edges[found[0]]
                return a[:2], _unit2(b - a), float(a[2]), t("align.edge"), a, _unit(b - a)
        return None

    def _target_at(self, x, y):
        """(0.449) What the second click aligns to the reference: (element id, the edge (a, b) in the plan, how it
        moves — "element" / "line" / "filling" —, the move (2,)), or (…, None) when that edge is not parallel to it,
        or None when nothing is there. A wall's or a column's face; an edge or a line under the mouse; inside an
        element, its edge parallel to the reference nearest the mouse."""
        rp, rd = self._ref[0], self._ref[1]
        if rd is None:
            return None
        n = np.array((-rd[1], rd[0]))
        face = self._face_at(x, y)
        if face is not None:
            guid, (fp, fd, _fn), z = face
            edge = (np.array((*fp, z)), np.array((*(fp + fd), z)))
            if abs(float(fd[0] * rd[1] - fd[1] * rd[0])) > PARALLEL:
                return guid, edge, "element", None
            return guid, edge, self._how(guid), n * float((rp - fp) @ n)
        snap, _hit = self.viewport.snap(x, y)
        edge = self._edge_of(snap, along=rd) if snap is not None and snap.obj_id is not None else None
        if edge is not None:
            a, b = (np.asarray(p, dtype=float) for p in edge)
            d = _unit2(b - a)
            if d is not None and abs(float(b[2] - a[2])) < 1e-6:
                if abs(float(d[0] * rd[1] - d[1] * rd[0])) > PARALLEL:
                    return snap.obj_id, (a, b), "element", None
                return snap.obj_id, (a, b), self._how(snap.obj_id), n * float((rp - a[:2]) @ n)
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None
        obj = self.doc.get(hit[0])
        edges = level_edges(obj)
        found = nearest_edge(edges, hit[2], along=rd)
        if found is None:
            near = nearest_edge(edges, hit[2])
            return (obj.id, tuple(edges[near[0]]), "element", None) if near is not None else None
        a, b = edges[found[0]]
        return obj.id, (a, b), self._how(obj.id), n * float((rp - a[:2]) @ n)

    def _edge_of(self, snap, along=None):
        """(0.449) The edge a snap is on: an edge's or a guide's own, or — a point snapped (an end, a middle) on an
        element or a line — that element's level edge through it (the one parallel to `along` when given); None."""
        if snap is None:
            return None
        if snap.kind in (ON_EDGE, ON_GUIDE) and snap.edge is not None:
            return snap.edge
        if snap.obj_id is None:
            return None
        edges = level_edges(self.doc.get(snap.obj_id))
        found = nearest_edge(edges, snap.point, along=along)
        if found is None and along is not None:
            found = nearest_edge(edges, snap.point)
        if found is None or found[1] > 1e-3:
            return None
        return tuple(edges[found[0]])

    def _how(self, obj_id):
        """(0.449) How an element is aligned: a loose line alone ("line"), a door or window along its wall
        ("filling"), anything else whole ("element")."""
        obj = self.doc.get(obj_id)
        if obj is None:
            return "element"
        if not obj.is_bim:
            return "line" if line_edit.is_lines(obj) else "element"
        try:
            return "filling" if obj.ifc_class in ("IfcDoor", "IfcWindow") and bim.is_filling(self.doc, obj_id) \
                else "element"
        except (AttributeError, KeyError, RuntimeError):
            return "element"

    def _pattern_at(self, x, y):
        """(0.332) What aligning the surface pattern's line under the mouse to the reference does: (element, face
        normal, pivot, angle, shift, the line (point, direction)), or (…, None…) when the reference crosses that face;
        None when no pattern's line is there."""
        line = self.viewport.pattern_line_at(x, y)
        if line is None:
            return None
        guid, n, sp, sd = line
        a3, d3 = self._ref[4], self._ref[5]
        rd = _unit(d3 - float(d3 @ n) * n)
        if rd is None:
            return guid, n, None, None, None, (sp, sd)              # (the reference goes through the face)
        r0 = a3 - float((a3 - sp) @ n) * n
        across = np.cross(n, sd)
        angle = math.degrees(math.atan2(float(np.cross(sd, rd) @ n), float(sd @ rd)))
        if angle > 90.0:                                            # (a line has no way: the nearer turn)
            angle -= 180.0
        elif angle <= -90.0:
            angle += 180.0
        if abs(angle) < TURNED:
            return guid, n, sp, 0.0, float((r0 - sp) @ across) * across, (sp, sd)
        s = -float((r0 - sp) @ across) / float(rd @ across)         # (where the two lines meet: turned about it)
        return guid, n, r0 + s * rd, angle, np.zeros(3), (sp, sd)

    # ------------------------------------------------------------ mouse

    def _show_reference(self, ref, colour=PREVIEW, line=None, edge=None):
        a3, d3 = ref[4], ref[5]
        segs, colours = [a3 - d3 * REACH, a3 + d3 * REACH], [colour, colour]
        if line is not None:                                        # (0.332: the pattern's line picked, lit)
            sp, sd = line
            segs += [sp - sd * PATTERN_REACH, sp + sd * PATTERN_REACH]
            colours += [PATTERN_COLOUR, PATTERN_COLOUR]
        if edge is not None:                                        # (0.449) the edge to be aligned, lit
            segs += [np.asarray(edge[0], dtype=float), np.asarray(edge[1], dtype=float)]
            colours += [TARGET_COLOUR, TARGET_COLOUR]
        self.viewport.show_lines(segs, colours)

    def pointer_move(self, x, y, modifiers):
        if self._ref is None:
            ref = self._reference_at(x, y)
            if ref is None:
                self.viewport.clear_overlays()
                return
            self._show_reference(ref)
            self.viewport.show_tip(ref[3], ref[4])
            return
        self._move = self._pattern = None
        found = self._pattern_at(x, y)
        if found is not None:                                       # (0.332) a pattern's line under the mouse
            guid, n, pivot, angle, shift, line = found
            self._show_reference(self._ref, SNAP_COLORS["on_edge"], line)
            if pivot is None:
                self.viewport.show_tip(t("align.pattern_across"), line[0])
                return
            self._pattern = (guid, n, pivot, angle, shift)
            if angle:
                tip = t("align.pattern_turn", a=format_angle(abs(angle), decimal_sep()))
            elif float(np.linalg.norm(shift)) > 1e-6:
                tip = t("align.pattern_move", d=_fmt(float(np.linalg.norm(shift))))
            else:
                tip = t("align.pattern_there")
            self.viewport.show_tip(tip, line[0])
            return
        target = self._target_at(x, y)                              # (0.449) any element's edge, any line
        if target is None:
            self._show_reference(self._ref, SNAP_COLORS["on_edge"])
            self.viewport.show_tip("", None)
            return
        obj_id, (a, b), how, move = target
        self._show_reference(self._ref, SNAP_COLORS["on_edge"], edge=(a, b))
        at = (np.asarray(a, dtype=float) + np.asarray(b, dtype=float)) / 2
        if move is None:
            self.viewport.show_tip(t("align.not_parallel"), at)
            return
        self._move = (obj_id, move, how, (np.asarray(a, dtype=float), np.asarray(b, dtype=float)))
        self.viewport.show_tip(t("align.move", d=_fmt(float(np.linalg.norm(move)))), at)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._ref is not None:
                self.cancel()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT:
            return
        if self._ref is None:
            ref = self._reference_at(x, y)
            if ref is None:
                self.host.message(t("err.align_reference"), warning=True)
                return
            self._ref = ref
            self.host.set_hint(self.hint())
            self.host.message(t("info.align_reference", what=ref[3]))
            return
        self.pointer_move(x, y, modifiers)
        if self._pattern is not None:
            self._align_pattern(*self._pattern)
            return
        if self._move is None:
            self.host.message(t("err.align_face"), warning=True)
            return
        obj_id, move, how, edge = self._move
        name = self.doc.get(obj_id).name
        if float(np.linalg.norm(move)) < 1e-9:
            self._move = None
            self.host.message(t("info.align_there", name=name))
            return
        try:
            self._align(obj_id, move, how, edge)
        except (ValueError, line_edit.LineRefused) as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self._move = None
        self.host.message(t("info.aligned", name=name, d=_fmt(float(np.linalg.norm(move)))))

    def _align(self, obj_id, move, how, edge):
        """(0.449) The element moved by `move` (2,) in the plan: a loose line alone — its two ends, the lines joined
        there following —; a door or a window along its wall; anything else whole. One undo step."""
        shift = np.array((float(move[0]), float(move[1]), 0.0))
        if how == "line":
            a, b = edge
            line_edit.move_points(self.doc, [(a, a + shift), (b, b + shift)], t("cmd.align"))
            return
        if how == "filling":
            st = self.doc.ifc.filling_state(obj_id)
            f = st["frame"]
            u = np.asarray(f.to_world((1.0, 0.0, 0.0)), dtype=float) - np.asarray(f.to_world((0.0, 0.0, 0.0)),
                                                                                  dtype=float)
            u = _unit(u * (1.0, 1.0, 0.0))
            along = float(shift @ u) if u is not None else 0.0
            if abs(along) < 0.999 * float(np.linalg.norm(shift)):
                raise line_edit.LineRefused("align_across_wall")    # (the reference along the wall: it cannot)
            bim.move_filling(self.doc, obj_id, s=float(st["s"]) + along)
            return
        m = np.eye(4)
        m[:3, 3] = shift
        if not bim.transform_objects(self.doc, [obj_id], m, t("cmd.align")):
            raise line_edit.LineRefused("align_not_moved")

    def _align_pattern(self, guid, normal, pivot, angle, shift):
        """(0.332) The pattern's line picked laid on the reference: its pattern moved or turned on that face."""
        name = self.doc.get(guid).name
        self._pattern = None
        if not angle and float(np.linalg.norm(shift)) <= 1e-6:
            self.host.message(t("info.pattern_there", name=name))
            return
        try:
            bim.align_pattern(self.doc, guid, normal, pivot, angle, shift)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        how = format_angle(abs(angle), decimal_sep()) if angle else _fmt(float(np.linalg.norm(shift)))
        self.host.message(t("info.pattern_aligned", name=name, how=how))

    def cancel(self):
        self._ref = self._move = self._pattern = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
