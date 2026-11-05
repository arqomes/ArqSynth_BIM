"""Align (0.107), as Revit's AL: a click on a reference — a grid axis, an edge, or a face of a wall — then on a
face of a wall or a column parallel to it: the element moves across until that face lies on the reference (the
walls joined to it follow). (0.332) Or, the second click on a line of a surface pattern (a tile's joint, a brick
course — lit under the mouse, as Revit's): the pattern moves on its face until that line lies on the reference, or
turns about where the two meet when they are not parallel; kept in the element (ifc/pattern_align.py). The reference
stays for the next ones; the right button or Esc lets it go."""

import math

import numpy as np

from ..core.inference import ON_EDGE
from ..core.units import format_angle, format_length
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, SNAP_COLORS, Tool

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
        if snap is not None and snap.kind == ON_EDGE and snap.edge is not None:
            a, b = (np.asarray(p, dtype=float) for p in snap.edge)
            along = _unit(b - a)
            if along is not None:
                level = abs(float(b[2] - a[2])) < 1e-6
                return a[:2], _unit2(b - a) if level else None, float(a[2]), t("align.edge"), a, along
        face = self._face_at(x, y)
        if face is not None:
            _g, (p, d, _n), z = face
            return p, d, z, t("align.face"), np.array((*p, z)), np.array((*d, 0.0))
        return None

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

    def _show_reference(self, ref, colour=PREVIEW, line=None):
        a3, d3 = ref[4], ref[5]
        segs, colours = [a3 - d3 * REACH, a3 + d3 * REACH], [colour, colour]
        if line is not None:                                        # (0.332: the pattern's line picked, lit)
            sp, sd = line
            segs += [sp - sd * PATTERN_REACH, sp + sd * PATTERN_REACH]
            colours += [PATTERN_COLOUR, PATTERN_COLOUR]
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
        face = self._face_at(x, y)
        self._show_reference(self._ref, SNAP_COLORS["on_edge"])
        if face is None:
            self.viewport.show_tip("", None)
            return
        guid, (fp, fd, _fn), z = face
        rp, rd, _rz, _label = self._ref[:4]
        if rd is None or abs(float(fd[0] * rd[1] - fd[1] * rd[0])) > PARALLEL:
            self.viewport.show_tip(t("align.not_parallel"), np.array((*fp, z)))
            return
        n = np.array((-rd[1], rd[0]))
        dist = float((rp - fp) @ n)
        self._move = (guid, n * dist)
        self.viewport.show_tip(t("align.move", d=_fmt(abs(dist))), np.array((*fp, z)))

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
        guid, move = self._move
        m = np.eye(4)
        m[:2, 3] = move
        name = self.doc.get(guid).name
        try:
            bim.transform_objects(self.doc, [guid], m, t("cmd.align"))
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self._move = None
        self.host.message(t("info.aligned", name=name, d=_fmt(float(np.linalg.norm(move)))))

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
