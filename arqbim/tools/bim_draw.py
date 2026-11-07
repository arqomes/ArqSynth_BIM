"""Direct BIM tools: Wall (point by point, like Revit / ArchiCAD), Column, Beam, Footing, Pipe, Duct, Grid (the
Slab is in slab.py since 0.100).

They create IFC elements straight away, with the chosen catalogue type, using
the same inferences as the sketch tools (snap points, red/green axis lock).
"""

import math

import numpy as np

from ..core import arcs, band_solid, placement, temp_dims
from ..core.classify import box_from_axis
from ..core.inference import ON_FACE
from ..core.sketch_geometry import ray_plane
from ..core.temp_dims import revit as revit_look
from ..core.units import format_length, format_slope, parse_lengths
from ..core.walls import REFERENCES, axis_lock, find_joint, horizontal_dir, offset_axis
from ..i18n import decimal_sep, lang, t
from ..ifc import catalog
from ..ifc import systems as systems_model
from ..model import bim
from ..render.viewport import AXIS_U, AXIS_V, PARALLEL_COLOR, PREVIEW
from .base import (
    LEFT, RIGHT, SNAP_COLORS, Option, Tool, direction_snap, drawing_dims, glyph_of, infer_point, inferred_style,
    level_plane, outside_dim, show_snap, show_start_reference, snap_tip, snapped_edge, start_reference,
)

Z = np.array((0.0, 0.0, 1.0))
ANGLES = (0, 90, 180, 270)
AXES = {"x": np.array((1.0, 0.0, 0.0)), "y": np.array((0.0, 1.0, 0.0))}
CLOSE_PX = 14
AXIS_END_PX = 12
MIN_LENGTH = 0.05
PARALLEL_REACH = 20.0   # (0.447) m: the walls this near the one being drawn are looked at for its parallel neighbours
WALL_SHAPES = ("line", "rect", "arc", "circle", "face", "wand")   # (0.102, 0.103) the Wall tool: point by point, a
#                                                          rectangle, an arc, a circle, a face's outline; (0.374) the
#                                                          magic wand (a window over two parallel lines of a drawing)


def _fmt(v):
    return format_length(v, decimal_sep())


def _name(spec):
    return spec.name_pt if lang() == "pt" else spec.name_en


def type_option(spec, kind, key="type", label="ctx.type", keep=None):
    """The contextual bar's choice of a catalogue type of this kind (0.85); keep(spec): which of them."""
    specs = [s for s in catalog.types() if s.kind == kind and (keep is None or keep(s))]
    return Option(key, t(label), "choice", spec.key, tuple((s.key, _name(s)) for s in specs))


def length_option(key, label, value):
    return Option(key, t(label), "length", float(value))


def box_edges(corners_bottom, corners_top):
    segs = []
    for ring in (corners_bottom, corners_top):
        for i in range(4):
            segs += [ring[i], ring[(i + 1) % 4]]
    for a, b in zip(corners_bottom, corners_top):
        segs += [a, b]
    return segs


class _PointTool(Tool):
    """Shared: a point on a level plane under the mouse, using inferences."""

    accepts_typing = True
    on_storey = True

    def __init__(self, host):
        super().__init__(host)
        self._hover = None          # last (point, snap) under the mouse
        self.locked = None          # X / Y (0.86): the next points along the red / green axis; N lets go

    def activate(self):
        self.locked = None
        super().activate()

    def lock_key(self, name):
        """X / Y / N (the tools drawn point by point): lock the red or green axis through the last point."""
        self.locked = None if name == "n" else name
        self.host.message(t("info.axis_free") if self.locked is None else t("info.axis_locked_" + self.locked))
        return True

    def _locked(self, p, last):
        """p brought onto the locked axis through `last` (same level)."""
        axis = AXES[self.locked]
        q = np.asarray(last, dtype=float) + axis * float(np.dot(np.asarray(p, dtype=float) - last, axis))
        q[2] = p[2]
        return q

    def _point(self, x, y, level=None, last=None, modifiers=()):
        """Point under the mouse on the level `level` (z), or on the ground / the
        inferred point's own level when level is None — a snap, or a point lined up
        with the points acquired, along the red / green axis through `last`,
        parallel / perpendicular to an edge acquired (0.60). Returns (point, the
        inference: a tracking.Inferred, or None). An axis locked (X / Y, 0.86) keeps
        it on that axis through `last`."""
        if self.locked is not None and last is not None:
            origin, direction = self.viewport.ray(x, y)
            z = self.doc.work_level() if level is None else level
            p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), Z)
            if p is None:
                p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), -Z)
            self.viewport.show_alignments()
            return (None if p is None else self._locked(p, last)), None
        found, _snap, _hit = infer_point(self.viewport, x, y, last, modifiers, flat=True,
                                         plane=level_plane(self.doc.work_level() if level is None else level))
        if found is not None and found.kind != ON_FACE:
            p = found.point.copy()
            if level is not None:
                p[2] = level
            self.viewport.show_alignments(found.lines, p)
            return p, found
        self.viewport.show_alignments()
        origin, direction = self.viewport.ray(x, y)
        z = self.doc.work_level() if level is None else level
        p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), Z)
        if p is None:
            p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), -Z)
        return p, None


class WallTool(_PointTool):
    name = "wall"
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.chain"

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.spec = catalog.BY_KEY["parede_alv_20"]
        self.height = bim.WALL_HEIGHT
        self.reference = "axis"     # the drawn line: "axis", "left" face or "right" face (Tab changes it)
        self.shape = "line"         # (0.102) point by point, a rectangle, or along a face's outline
        self._axes = None           # axis lines of the existing walls (cache)
        self._ends = None           # …their ends as one array (0.225)
        host.doc.subscribe(self._forget_axes)
        self._reset_chain()

    def _forget_axes(self, changed, removed):
        self._axes = None
        self._ends = None

    def _wall_axes(self):
        if self._axes is None:
            self._axes = bim.wall_axes(self.doc)
        return self._axes

    def _axis_ends(self):
        """(0.225) Every wall's axis ends as one array (N, 3), kept with their axes."""
        if getattr(self, "_ends", None) is None:
            self._ends = np.asarray([p for _g, s, e, _t in self._wall_axes() for p in (s, e)],
                                    dtype=float).reshape(-1, 3)
        return self._ends

    def _axis_end(self, x, y, level):
        """Axis end of an existing wall near the mouse, at this level, or None.
        Starting / ending a wall there makes a clean corner with it. (0.225) All projected at once — one by one
        they cost a mouse move ~1800 projections on a building."""
        ends = self._axis_ends()
        at = ends[np.abs(ends[:, 2] - level) <= 1e-4]
        if not len(at):
            return None
        xy = self.viewport.project_many(at)
        dist = np.hypot(xy[:, 0] - x, xy[:, 1] - y)
        dist[np.isnan(dist)] = np.inf                   # (behind the camera)
        k = int(np.argmin(dist))
        return at[k].copy() if dist[k] <= AXIS_END_PX else None

    def _wall_point(self, x, y, level, modifiers=()):
        """(point, inference, on a wall axis end) under the mouse, at the wall base level.
        Axis ends are offered when drawing by the axis (by a face, the corners of
        the walls are the points to click)."""
        free = self.locked is None or self._start is None
        p = self._axis_end(x, y, level) if self.reference == "axis" and free else None
        if p is not None:
            return p, None, True
        p, snap = self._point(x, y, level, self._start, modifiers)
        return p, snap, False

    def _reset_chain(self):
        self._start = None          # current segment start (on the drawn reference line, base level)
        self._start_ref = None      # before the first click: where a typed distance starts from
        self._end = None
        self._prev = None           # (guid, direction) of the previous wall
        self._first = None          # (guid, direction, start point) of the chain's first wall
        self._count = 0
        self._corner = None         # (0.102) a rectangle's first corner; (0.103) a circle's centre
        self._du = self._dv = 0.0
        self._outline = None        # (0.102) the face outline under the mouse: ([(x, y)], z)
        self._arc = []              # (0.103) an arc's start and end clicked so far
        self._curve = None          # (0.103) the arc / circle under the mouse: (centre, radius, start, sweep)
        self._wand = None           # (0.374) the magic wand's window: where it was pressed (screen)

    def set_spec(self, spec):
        self.spec = spec
        self.host.set_hint(self.hint())

    def _ref_text(self, reference=None):
        """The drawn line's name: along an outline (a rectangle, a circle, a face) its faces are inner and
        outer."""
        return t(("ref." if self.shape in ("line", "arc") else "refloop.") + (reference or self.reference))

    def options(self):
        return [type_option(self.spec, "wall"),
                Option("shape", t("ctx.wall_shape"), "choice", self.shape,
                       tuple((s, t("wallshape." + s)) for s in WALL_SHAPES)),
                length_option("height", "ctx.height", self.height),
                Option("reference", t("ctx.reference"), "choice", self.reference,
                       tuple((r, self._ref_text(r)) for r in REFERENCES))]

    def set_option(self, key, value):
        if key == "type":
            self.set_spec(catalog.BY_KEY[value])
        elif key == "height" and value > 0.1:
            self.height = value
        elif key == "reference" and value in REFERENCES:
            self.reference = value
        elif key == "shape" and value in WALL_SHAPES and value != self.shape:
            self.shape = value
            self.cancel()
        self.host.set_hint(self.hint())
        if self.shape == "line" and self._start is not None and self._end is not None:
            self._preview(None, PREVIEW)

    def hint(self):
        ref = self._ref_text()
        if self.shape == "rect":
            if self._corner is not None:
                return t("hint.wall.rect_end", ref=ref)
            return t("hint.wall.rect_start", type=_name(self.spec), ref=ref)
        if self.shape == "face":
            return t("hint.wall.face", type=_name(self.spec), ref=ref)
        if self.shape == "wand":
            return t("hint.wall.wand", type=_name(self.spec), ref=ref)
        if self.shape == "arc":
            return t(("hint.wall.arc_start", "hint.wall.arc_end", "hint.wall.arc_bulge")[len(self._arc)],
                     type=_name(self.spec), ref=ref)
        if self.shape == "circle":
            if self._corner is not None:
                return t("hint.wall.circle_end", ref=ref)
            return t("hint.wall.circle_start", type=_name(self.spec), ref=ref)
        if self._start is not None:
            return t("hint.wall.next", ref=ref)
        return t("hint.wall.start", type=_name(self.spec), ref=ref)

    def vcb_title(self):
        return t("vcb.dims") if self.shape == "rect" else t("vcb.length")

    def tab(self):
        """Tab: the line being drawn is the axis -> the left face -> the right face (along an outline: the inner
        face, the outer face)."""
        refs = REFERENCES
        self.reference = refs[(refs.index(self.reference) + 1) % len(refs)]
        self.host.set_hint(self.hint())
        self.host.message(t("info.wall_reference", ref=self._ref_text()))
        if self.shape == "line" and self._start is not None and self._end is not None:
            self._preview(None, PREVIEW)
        return True

    # ------------------------------------------------------------ a rectangle, a face (0.102)

    def _ring_band(self, ring):
        """The walls' band along a ring drawn as the reference: its outer and inner outlines [(x, y)], corner for
        corner (0.383: core/band_solid — they make its solid)."""
        t_ = self.spec.thickness
        inside, outside = {"axis": (-t_ / 2, t_ / 2), "left": (0.0, t_), "right": (-t_, 0.0)}[self.reference]
        ring = band_solid.ccw(ring)
        return band_solid.offset_ring(ring, outside), band_solid.offset_ring(ring, inside)

    def _show_band(self, ring, z, label_at=None):
        """(0.383) The walls round a ring as a solid — their faces, top and upright edges —, not two outlines."""
        if len(ring) < 3:
            return
        outer, inner = self._ring_band(ring)
        tris, segs = band_solid.band_solid(outer, inner, z, self.height, closed=True)
        self.viewport.show_volume(tris, segs, [PREVIEW] * len(segs))
        if label_at is not None:
            self.viewport.show_label(t("tip.wall_loop", n=len(ring)), label_at)

    def _rect_ring(self):
        c = self._corner
        ring = [(c[0], c[1]), (c[0] + self._du, c[1]), (c[0] + self._du, c[1] + self._dv), (c[0], c[1] + self._dv)]
        return ring if self._du * self._dv > 0 else ring[::-1]          # (counter-clockwise)

    def _rect_finish(self):
        if abs(self._du) < MIN_LENGTH or abs(self._dv) < MIN_LENGTH:
            return
        z = float(self._corner[2])
        made = bim.add_wall_loop(self.doc, [(x, y, z) for x, y in self._rect_ring()], self.spec, self.height,
                                 self.reference, storey=self.doc.active_storey)
        self.host.message(t("info.wall_rect", a=_fmt(abs(self._du)), b=_fmt(abs(self._dv)), n=len(made),
                            type=_name(self.spec), ref=self._ref_text()))
        self.cancel()

    def _face_at(self, x, y):
        hit = self.viewport.pick_point(x, y)
        return bim.face_outline(self.doc, hit[0], hit[1], hit[2]) if hit is not None else None

    # ------------------------------------------------------------ an arc, a circle (0.103)

    def _curve_axis(self, curve):
        """The axis of the curved wall for the arc / circle drawn as the reference line."""
        centre, radius, start, sweep = curve
        return centre, arcs.axis_radius(radius, sweep, self.reference, self.spec.thickness), start, sweep

    def _show_curve(self, curve, z):
        centre, radius, start, sweep = self._curve_axis(curve)
        if radius - self.spec.thickness / 2 <= 0:
            return
        t_ = self.spec.thickness
        # (0.383) the curved wall as a solid — its two faces, its top, its ends —, not two outlines one over the other
        full = arcs.is_full(sweep)
        outer, inner = (arcs.arc_points(centre, r, start, sweep) for r in (radius + t_ / 2, radius - t_ / 2))
        tris, segs = band_solid.band_solid(outer, inner, z, self.height, closed=full, verticals=() if full else None)
        self.viewport.show_volume(tris, segs, [PREVIEW] * len(segs))
        drawn = curve[1]
        self.viewport.show_label(t("tip.wall_radius", r=_fmt(drawn)), np.array((*arcs.point_at(
            curve[0], drawn, curve[2] + curve[3] / 2), z)))
        self.host.set_vcb(_fmt(drawn))

    def _curve_finish(self, curve, z):
        if curve is None:
            return
        centre, radius, start, sweep = self._curve_axis(curve)
        if radius - self.spec.thickness / 2 < 0.05 or radius * abs(sweep) < MIN_LENGTH:
            self.host.message(t("err.wall_curve_small"), warning=True)
            return
        bim.add_curved_wall(self.doc, (centre[0], centre[1], z), radius, start, sweep, self.spec, self.height,
                            storey=self.doc.active_storey)
        key = "info.wall_circle" if arcs.is_full(sweep) else "info.wall_arc"
        self.host.message(t(key, r=_fmt(curve[1]), a="{:.0f}".format(abs(math.degrees(sweep))),
                            l=_fmt(radius * abs(sweep)), type=_name(self.spec), ref=self._ref_text()))
        self.cancel()

    def _curve_move(self, x, y, modifiers):
        first = self._arc[0] if self._arc else self._corner
        # (0.189) an arc, a circle, a rectangle stand on the storey as the walls point by point do: their first point
        # brought down to the base level (an arc started on another wall's end: joined to it, not on its top)
        if first is None:
            p, snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
            if p is None:
                return
            self._hover = (p, snap)
            show_snap(self.viewport, snap, p)
            self._start_ref = start_reference(snap)
            show_start_reference(self.viewport, self._start_ref, p)
            return
        last = self._arc[-1] if self._arc else self._corner
        p, snap = self._point(x, y, first[2], last, modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        self._end = p
        if self.shape == "circle":
            r = float(np.linalg.norm((p - self._corner)[:2]))
            self._curve = (self._corner[:2], r, math.atan2(p[1] - self._corner[1], p[0] - self._corner[0]),
                           arcs.FULL) if r > 1e-6 else None
        elif len(self._arc) == 1:                        # the chord, start -> end
            self._curve = None
            self.viewport.show_lines([self._arc[0], p], [PREVIEW, PREVIEW])
            drawing_dims(self.viewport, self._arc[0], p)
            show_snap(self.viewport, snap, p)
            self.host.set_vcb(_fmt(float(np.linalg.norm((p - self._arc[0])[:2]))))
            return
        else:
            self._curve = arcs.arc_through(self._arc[0], self._arc[1], p)
        if self._curve is not None:
            self._show_curve(self._curve, first[2])
            show_snap(self.viewport, snap, p)

    def _curve_down(self, x, y, modifiers):
        if self.shape == "circle":
            if self._corner is None:
                p, _snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
                if p is not None:
                    self._corner = p
                    self.host.set_hint(self.hint())
                return
            self._curve_finish(self._curve, self._corner[2])
            return
        if len(self._arc) < 2:
            if self._arc:
                p = self._end
            else:
                p, _snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
            if p is not None and (not self._arc or np.linalg.norm((p - self._arc[0])[:2]) >= MIN_LENGTH):
                self._arc.append(np.array((p[0], p[1], self._arc[0][2] if self._arc else p[2])))
                self.host.set_hint(self.hint())
            return
        self._curve_finish(self._curve, self._arc[0][2])

    def _curve_typed(self, value):
        """A length typed: the circle's radius; an arc's chord (after its start) or its radius (after its end)."""
        if self.shape == "circle":
            if self._corner is None and self._hover is not None:
                self._corner = self._hover[0].copy()
            if self._corner is None:
                return
            self._curve_finish((self._corner[:2], abs(value), 0.0, arcs.FULL), self._corner[2])
            return
        if not self._arc:
            if self._hover is None:
                return
            self._arc.append(self._hover[0].copy())
        if len(self._arc) == 1:
            a = self._arc[0]
            d = (self._end - a) if self._end is not None else np.array((1.0, 0.0, 0.0))
            d = np.array((d[0], d[1], 0.0))
            d = d / np.linalg.norm(d) if np.linalg.norm(d) > 1e-9 else np.array((1.0, 0.0, 0.0))
            self._arc.append(a + d * abs(value))
            self.host.set_hint(self.hint())
            return
        side = self._end if self._end is not None else self._arc[1]
        curve = arcs.arc_with_radius(self._arc[0], self._arc[1], abs(value), side)
        if curve is None:
            self.host.message(t("err.wall_arc_radius", c=_fmt(float(np.linalg.norm(
                (self._arc[1] - self._arc[0])[:2])) / 2)), warning=True)
            return
        self._curve_finish(curve, self._arc[0][2])

    # ------------------------------------------------------------ the magic wand (0.374, the addon's wall_magic_wand)

    def _wand_lines(self):
        """The plan's lines the wand looks at — the CAD drawings linked and shown (their layers shown) and the loose
        sketch lines at the active storey's level — (K, 2, 2) in metres."""
        from ..model import cad_links as cad_model
        from ..model import line_edit
        level = self.doc.work_level()
        out = []
        for link in getattr(self.doc, "cad_links", ()):
            if not link.visible or (link.storey is not None and link.storey != self.doc.active_storey):
                continue
            found = cad_model.drawing_of(link.path)
            segs = [v for k, v in (found[1] if found is not None else {}).items() if k not in link.hidden]
            if segs:
                out.append(np.asarray(link.place(np.concatenate(segs)), dtype=float).reshape(-1, 2, 2))
        for obj in self.doc.objects.values():
            if not line_edit.is_lines(obj):
                continue
            w = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3) @ obj.matrix[:3, :3].T + obj.matrix[:3, 3]
            ends = np.asarray(obj.mesh.lines, dtype=np.int64).reshape(-1, 2)
            flat = (np.abs(w[ends[:, 0], 2] - level) < 0.05) & (np.abs(w[ends[:, 1], 2] - level) < 0.05)
            if flat.any():
                out.append(np.stack((w[ends[flat, 0], :2], w[ends[flat, 1], :2]), axis=1))
        return np.concatenate(out) if out else np.zeros((0, 2, 2))

    def _wand_pick(self, x0, y0, x1, y1):
        """The lines the window (screen corners) touches: (K, 2, 2)."""
        segs = self._wand_lines()
        if not len(segs):
            return segs
        level = self.doc.work_level()
        flat = segs.reshape(-1, 2)
        xy = self.viewport.project_many(np.column_stack((flat, np.full(len(flat), level)))).reshape(-1, 2, 2)
        lo, hi = np.minimum((x0, y0), (x1, y1)), np.maximum((x0, y0), (x1, y1))
        a, d = xy[:, 0], xy[:, 1] - xy[:, 0]
        t0, t1 = np.zeros(len(xy)), np.ones(len(xy))
        ok = ~np.isnan(xy).any(axis=(1, 2))
        for k in range(2):                              # (Liang–Barsky: the part of each line inside the window)
            for p, q in ((-d[:, k], a[:, k] - lo[k]), (d[:, k], hi[k] - a[:, k])):
                with np.errstate(divide="ignore", invalid="ignore"):
                    r = q / p
                parallel = np.abs(p) < 1e-12
                ok &= ~(parallel & (q < 0))
                t0 = np.where(~parallel & (p < 0), np.maximum(t0, r), t0)
                t1 = np.where(~parallel & (p > 0), np.minimum(t1, r), t1)
        return segs[ok & (t0 <= t1)]

    def _wand_finish(self, x0, y0, x1, y1):
        from ..core import cad_walls
        if np.hypot(x1 - x0, y1 - y0) < 4:
            self.host.message(t("hint.wall.wand", type=_name(self.spec), ref=self._ref_text()), warning=True)
            return
        axes = cad_walls.wall_axes(self._wand_pick(x0, y0, x1, y1))
        if not axes:
            self.host.message(t("err.wall_wand_none"), warning=True)
            return
        report = bim.model_from_cad(self.doc, axes, [], [], self.height, storey=self.doc.active_storey)
        cm = sorted({round(th * 100, 1) for _a, _b, th in axes})
        self.host.message(t("info.wall_wand", n=len(report["walls"]),
                            t=", ".join("{:g} cm".format(c).replace(".", ",") for c in cm)))

    def pointer_up(self, x, y, button, modifiers):
        if self.shape == "wand" and button == LEFT and self._wand is not None:
            (x0, y0), self._wand = self._wand, None
            self.viewport.show_region()
            self._wand_finish(x0, y0, x, y)

    def _shape_move(self, x, y, modifiers):
        if self.shape == "wand":
            if self._wand is not None:
                (x0, y0) = self._wand
                self.viewport.show_region([(x0, y0), (x, y0), (x, y), (x0, y)], "window")
            return
        if self.shape in ("arc", "circle"):
            self._curve_move(x, y, modifiers)
            return
        if self.shape == "face":
            self._outline = self._face_at(x, y)
            if self._outline is None:
                self.viewport.clear_overlays()
                self.viewport.show_tip(t("tip.wall_face_none"), self._point(x, y)[0])
                return
            ring, z = self._outline
            self.viewport.show_tip("", None)
            self._show_band(ring, z, np.array((*np.mean(ring, axis=0), z)))
            return
        if self._corner is None:
            p, snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
            if p is None:
                return
            self._hover = (p, snap)
            show_snap(self.viewport, snap, p)
            self._start_ref = start_reference(snap)
            show_start_reference(self.viewport, self._start_ref, p)
            return
        p, snap = self._point(x, y, self._corner[2], modifiers=modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        self._du, self._dv = float(p[0] - self._corner[0]), float(p[1] - self._corner[1])
        if abs(self._du) < 1e-6 or abs(self._dv) < 1e-6:
            return
        self._show_band(self._rect_ring(), self._corner[2])
        c = self._corner
        pts = [c, c + (self._du, 0, 0), c + (self._du, self._dv, 0)]
        self.viewport.show_temp_dims([outside_dim(pts[0], pts[1], (pts[0] + pts[2]) / 2),
                                      outside_dim(pts[1], pts[2], (pts[0] + pts[2]) / 2)])
        show_snap(self.viewport, snap, p)
        self.host.set_vcb("{} × {}".format(_fmt(abs(self._du)), _fmt(abs(self._dv))))

    def _shape_down(self, x, y, modifiers):
        if self.shape == "wand":                       # (0.374) the window starts where pressed
            self._wand = (float(x), float(y))
            return
        if self.shape in ("arc", "circle"):
            self._curve_down(x, y, modifiers)
            return
        if self.shape == "face":
            found = self._face_at(x, y)
            if found is None:
                self.host.message(t("err.wall_face_none"), warning=True)
                return
            ring, z = found
            made = bim.add_wall_loop(self.doc, [(px, py, z) for px, py in ring], self.spec, self.height,
                                     self.reference, storey=self.doc.active_storey)
            self.viewport.clear_overlays()
            self.host.message(t("info.wall_face", n=len(made), type=_name(self.spec), ref=self._ref_text()))
            return
        if self._corner is None:
            p, _snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
            if p is not None:
                self._corner = p
                self.host.set_hint(self.hint())
            return
        self._rect_finish()

    def _shape_typed(self, text):
        values = parse_lengths(text, 2)
        if values is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        if self.shape in ("arc", "circle"):
            if values[0] is not None:
                self._curve_typed(values[0])
            return
        if self.shape != "rect":
            return
        a, b = values
        if self._corner is None and self._start_ref is not None and a is not None and b is None:
            src, direction = self._start_ref            # before the first click: its first corner that far
            self._corner = src + direction * a
            self.viewport.clear_overlays()
            self.host.set_hint(self.hint())
            self.host.message(t("info.start_typed", l=_fmt(a)))
            return
        if self._corner is None:
            if self._hover is None:
                return
            self._corner = self._hover[0].copy()
        if a is not None:
            self._du = (-1.0 if self._du < 0 else 1.0) * a
        if b is not None:
            self._dv = (-1.0 if self._dv < 0 else 1.0) * b
        self._rect_finish()

    # ------------------------------------------------------------ mouse

    def pointer_move(self, x, y, modifiers):
        if self.shape != "line":
            self._shape_move(x, y, modifiers)
            return
        # walls stand on the storey: inferred points are brought down to the base level
        level = self.doc.work_level() if self._start is None else self._start[2]
        p, snap, on_axis = self._wall_point(x, y, level, modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        if self._start is None:
            if on_axis:
                if revit_look():                          # (0.446: Revit's glyph, an end's square)
                    self.viewport.show_marker(None)
                    self.viewport.show_glyph("endpoint", p)
                else:
                    self.viewport.show_marker(p, SNAP_COLORS["endpoint"])
                self.viewport.show_tip(t("snap.wall_axis"), p)
            else:
                show_snap(self.viewport, snap, p)
            self._start_ref = None if on_axis else start_reference(snap)
            show_start_reference(self.viewport, self._start_ref, p)
            return
        tip, color, glyph, edge = None, PREVIEW, None, None
        if self._first is not None and self._count >= 2 and self._near_screen(self._first[2], x, y):
            end, tip, glyph = self._first[2].copy(), t("snap.close"), "endpoint"
        elif on_axis:
            end, tip, color, glyph = p, t("snap.wall_axis"), SNAP_COLORS["endpoint"], "endpoint"
        elif snap is not None:
            tip, color, _line = inferred_style(snap)
            end, glyph, edge = p, glyph_of(snap), snapped_edge(snap)
        else:
            # (0.448, the owner) every 45° and parallel to the walls and lines there, as Revit's; Shift lets go
            found = direction_snap(self.doc, self._start, p) if "Shift" not in (modifiers or ()) else None
            if found is not None:
                end, kind, edge, degrees = found
                tip, glyph = snap_tip(kind, degrees), kind
                color = AXIS_U if kind == "axis_x" else AXIS_V if kind == "axis_y" else PARALLEL_COLOR
            else:
                end, axis = (p.copy(), None) if "Shift" in (modifiers or ()) else axis_lock(self._start, p)
                end[2] = self._start[2]
                if axis:
                    tip = t("snap.axis_" + axis)
                    color = AXIS_U if axis == "x" else AXIS_V
                    glyph = "axis_" + axis
        self._end = end
        self._preview(tip, color, glyph, edge)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self.shape != "line":
            self._shape_down(x, y, modifiers)
            return
        if self._start is None:
            p, _snap, _on_axis = self._wall_point(x, y, self.doc.work_level())
            if p is not None:
                self._start = p
                self.host.set_hint(self.hint())
            return
        if self._end is not None:
            self._add(self._end)

    # ------------------------------------------------------------ keyboard

    def typed(self, text):
        if self.shape != "line":
            self._shape_typed(text)
            return
        values = parse_lengths(text, 2)
        if values is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        length, height = values
        if height is not None and height > 0.1:
            self.height = height
        if length is None:
            self.host.message(t("info.wall", l=_fmt(self.height), type=_name(self.spec)))
            return
        if self._start is None and self._start_ref is not None and height is None:
            # before the first click, on an alignment or an edge: the wall starts that far from its point
            src, direction = self._start_ref
            self._start = src + direction * length
            self._start[2] = self.doc.work_level()
            self.viewport.clear_overlays()
            self.host.set_hint(self.hint())
            self.host.message(t("info.start_typed", l=_fmt(length)))
            return
        if self._start is None:
            if self._hover is None:
                return
            self._start = self._hover[0].copy()      # forgiving: typed before clicking
        direction = horizontal_dir(self._start, self._end) if self._end is not None else None
        if direction is None:
            direction = np.array((1.0, 0.0, 0.0))
        self._add(self._start + direction * abs(length) * (1 if length > 0 else -1))

    def cancel(self):
        self._reset_chain()
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    # ------------------------------------------------------------ internals

    def _near_screen(self, point, x, y):
        px, py = self.viewport.project(point)
        return np.hypot(px - x, py - y) <= CLOSE_PX

    def _add(self, end):
        start = self._start
        if np.linalg.norm((end - start)[:2]) < MIN_LENGTH:
            return
        closing = self._first is not None and self._count >= 2 and np.linalg.norm((end - self._first[2])[:2]) < 1e-6
        direction = horizontal_dir(start, end)
        a, b = offset_axis(start, end, self.reference, self.spec.thickness)   # the wall's axis
        # Corners with walls drawn before, separately (the chain's own corners come from prev / first).
        axes = [w for w in self._wall_axes() if self._prev is None or w[0] != self._prev[0]]
        start_join = None if self._prev is not None else find_joint(a, direction, axes, self.spec.thickness)
        end_join = None if closing else find_joint(b, direction, axes, self.spec.thickness)
        guid = bim.add_wall(self.doc, a, b, self.spec, self.height, prev=self._prev,
                            first=(self._first[0], self._first[1]) if closing else None,
                            start_join=start_join and start_join[:3], end_join=end_join and end_join[:3],
                            storey=self.doc.active_storey)
        self._count += 1
        if self._first is None:
            self._first = (guid, direction, start.copy())
        self._prev = (guid, direction)
        text = t("info.wall", l=_fmt(float(np.linalg.norm((end - start)[:2]))), type=_name(self.spec))
        if start_join or end_join:
            text += " " + t("info.wall_joined")
        self.host.message(text)
        if closing:
            self.host.message(t("info.closed", n=self._count))
            self.cancel()
            return
        self._start = end.copy()
        self._end = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())

    def _parallel_dims(self, a, b):
        """(0.447) As Revit's while a wall is drawn: its distance to the nearest parallel wall on each side (overlapping
        it), from axis to axis or from face to face as the walls' temporary dimensions (`host.dim_faces`) — relations
        on what they measure. a, b: the axis being drawn."""
        if float(np.linalg.norm((np.asarray(b) - np.asarray(a))[:2])) < MIN_LENGTH:
            return []
        ends = self._axis_ends().reshape(-1, 2, 3)          # (the walls near it only: one look at all of them)
        if not len(ends):
            return []
        lo = np.minimum(a, b)[:2] - PARALLEL_REACH
        hi = np.maximum(a, b)[:2] + PARALLEL_REACH
        near = np.flatnonzero((ends[:, :, :2].max(axis=1) >= lo).all(axis=1) &
                              (ends[:, :, :2].min(axis=1) <= hi).all(axis=1) &
                              (np.abs(ends[:, 0, 2] - float(a[2])) < temp_dims.SAME_FLOOR))
        axes = self._wall_axes()
        others = [axes[k] for k in near]
        if not others:
            return []
        faces = bool(getattr(self.host, "dim_faces", False))
        found = temp_dims.wall_relations((a, b), self.spec.thickness, others, faces=faces)
        return [temp_dims.TempDim(r.a, r.b, Z, offset_px=0.0, kind="relation") for r in found if r.kind == "side"]

    def _preview(self, tip, color, glyph=None, edge=None):
        a, b = offset_axis(self._start, self._end, self.reference, self.spec.thickness)
        way = (b - a)[:2]
        if float(np.linalg.norm(way)) < 1e-6:
            return
        side = np.array((-way[1], way[0])) / float(np.linalg.norm(way)) * self.spec.thickness / 2
        if revit_look() and self.viewport.plan:
            # (0.446) as Revit's in a plan: the wall's outline, and the line being drawn as its location line, dashed,
            # going on past both ends
            z = float(a[2])
            corners = [np.array((*c, z)) for c in (a[:2] + side, b[:2] + side, b[:2] - side, a[:2] - side)]
            outline = [p for k in range(4) for p in (corners[k], corners[(k + 1) % 4])]
            self.viewport.show_drawn(outline, (self._start, self._end))
        else:
            # (0.383) the wall as a solid — its faces shaded, its edges —, as the rectangle, the circle and the arc
            self.viewport.show_drawn()
            tris, segs = band_solid.band_solid([a[:2] + side, b[:2] + side], [a[:2] - side, b[:2] - side],
                                               float(a[2]), self.height, closed=False)
            segs = segs + [self._start, self._end]                    # + the line being drawn
            self.viewport.show_volume(tris, segs, [color] * len(segs))
        length = float(np.linalg.norm((self._end - self._start)[:2]))
        drawing_dims(self.viewport, self._start, self._end,          # (its length and angle, as Revit)
                     extra=self._parallel_dims(a, b))                # (0.447: and to the parallel walls beside it)
        if revit_look():                                  # (0.446) Revit's glyph, magenta; the edge snapped to, lit
            self.viewport.show_marker(None)
            self.viewport.show_glyph(glyph, self._end, edge)
        else:
            self.viewport.show_marker(self._end, color)
        self.viewport.show_tip(tip or "", self._end)
        self.host.set_vcb(_fmt(length))


class ColumnTool(_PointTool):
    """Column (0.66): a click where it stands (the middle of its foot, on the active storey), with the
    snaps and alignments; its section square to the red axis; the height typed."""

    name = "column"
    common_keys = frozenset(("r", "shift+r", "space", "shift+space"))
    placement = True
    keys_help = "keys.column"

    def __init__(self, host):
        super().__init__(host)
        self.spec = catalog.BY_KEY["pilar_30"]
        self.height = bim.WALL_HEIGHT
        self.angle = 0              # degrees from the red axis: R / Shift+R (0.86)
        self.insertion = 0          # which of its section's 9 points goes on the point clicked: Space (0.86)

    def set_spec(self, spec):
        self.spec = spec
        self.host.set_hint(self.hint())

    def options(self):
        return [type_option(self.spec, "column"), length_option("height", "ctx.height", self.height),
                Option("angle", t("ctx.angle"), "choice", self.angle, tuple((a, "{}°".format(a)) for a in ANGLES)),
                Option("insertion", t("ctx.insertion"), "choice", self.insertion,
                       tuple((k, t("ins.{}".format(k))) for k in range(len(placement.INSERTION))))]

    def set_option(self, key, value):
        if key == "type":
            self.set_spec(catalog.BY_KEY[value])
        elif key == "height" and value >= 0.1:
            self.height = value
        elif key == "angle":
            self.angle = int(value)
        elif key == "insertion":
            self.insertion = int(value)
        self._again()

    def common_key(self, name):
        if name in ("r", "shift+r"):
            self.angle = placement.turn(self.angle, 1 if name == "r" else -1)
            self.host.message(t("info.turned", a=self.angle))
        else:
            self.insertion = placement.next_insertion(self.insertion, 1 if name == "space" else -1)
            self.host.message(t("info.insertion", p=t("ins.{}".format(self.insertion))))
        self._again()
        return True

    def _again(self):
        """The hint, the contextual bar and the outline under the mouse as the settings are now."""
        self.host.set_hint(self.hint())
        if self._hover is not None:
            self._show(*self._hover)

    def hint(self):
        return t("hint.column", type=_name(self.spec), h=_fmt(self.height))

    def vcb_title(self):
        return t("vcb.height")

    def _placed(self, p):
        """(the foot's middle, the section's x direction, the foot's corners) with the insertion point at p."""
        w, d = self.spec.profile
        return placement.place_box(p, w, d, self.angle, self.insertion)

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        self._show(p, snap)

    def _show(self, p, snap):
        _base, _x, foot = self._placed(p)
        segs = box_edges(foot, [c + Z * self.height for c in foot])
        self.viewport.show_polygon(foot, segments=segs, colors=[PREVIEW] * len(segs))
        show_snap(self.viewport, snap, p)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        p, _snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
        if p is None:
            return
        base, x_dir, _foot = self._placed(p)
        # on a crossing of the grid: tied to its two axes (0.92), it goes with them
        ties = next((uids for uids, (x, y) in bim.grid_crossings(self.doc.grids).items()
                     if np.hypot(p[0] - x, p[1] - y) < 1e-3), None)
        bim.add_column(self.doc, base, self.spec, self.height, storey=self.doc.active_storey, x_dir=x_dir, ties=ties)
        self.viewport.clear_overlays()
        self.host.message(t("info.column", type=_name(self.spec), h=_fmt(self.height)))

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None or values[0] is None or values[0] < 0.1:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        self.height = values[0]
        self.host.set_hint(self.hint())
        self.host.message(t("info.column_height", h=_fmt(self.height)))

    def cancel(self):
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")


class BeamTool(_PointTool):
    """Beam (0.66): point by point like the Wall tool — its axis, its top at a height above the active
    storey (2,80 by default; typed before the first click to change it); the snaps and alignments (a
    column's top, a wall's end…) give the points, seen from above or in 3D."""

    name = "beam"
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.chain"

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.spec = catalog.BY_KEY["viga_20x40"]
        self.top = bim.WALL_HEIGHT            # the top's height above the active storey's level
        self._start = self._end = None

    def set_spec(self, spec):
        self.spec = spec
        self.host.set_hint(self.hint())

    top_label = "ctx.beam_top"

    def options(self):
        return [type_option(self.spec, self.name), length_option("top", self.top_label, self.top)]

    def set_option(self, key, value):
        if key == "type":
            self.set_spec(catalog.BY_KEY[value])
        elif key == "top":
            self.top = value
        self.host.set_hint(self.hint())

    def hint(self):
        if self._start is not None:
            return t("hint.beam.next")
        return t("hint.beam.start", type=_name(self.spec), h=_fmt(self.top))

    def vcb_title(self):
        return t("vcb.length") if self._start is not None else t("vcb.height")

    def _level(self):
        return self.doc.work_level() + self.top

    def _below(self):
        """How far the section's underside is below the level clicked on (a beam: all of it — its top is there)."""
        return self.spec.profile[1]

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, self._level(), self._start, modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        if self._start is None:
            show_snap(self.viewport, snap, p)
            return
        self._end = p
        width, height = self.spec.profile
        drop = Z * self._below()
        box = box_from_axis(self._start - drop, self._end - drop, width, height)
        if box.length < 1e-6:
            return
        bottom = box.footprint()
        segs = box_edges(bottom, [c + Z * height for c in bottom]) + [self._start, self._end]
        self.viewport.show_polygon(bottom, segments=segs, colors=[PREVIEW] * len(segs))
        drawing_dims(self.viewport, self._start, self._end)
        tip, color, _line = inferred_style(snap) if snap is not None else ("", PREVIEW, PREVIEW)
        self.viewport.show_marker(self._end, color)
        self.viewport.show_tip(tip, self._end if tip else None)
        self.host.set_vcb(_fmt(float(np.linalg.norm((self._end - self._start)[:2]))))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self._start is None:
            p, _snap = self._point(x, y, self._level(), modifiers=modifiers)
            if p is not None:
                self._start = p
                self.host.set_hint(self.hint())
                if hasattr(self.host, "vcb_title_changed"):
                    self.host.vcb_title_changed()          # (now its length)
            return
        if self._end is not None:
            self._add(self._end)

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None or values[0] is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        if self._start is None:                     # before the first click: the top's height
            self.top = values[0]
            self.host.set_hint(self.hint())
            self.host.message(t(self.level_info, h=_fmt(self.top)))
            return
        direction = horizontal_dir(self._start, self._end) if self._end is not None else None
        if direction is None:
            direction = np.array((1.0, 0.0, 0.0))
        self._add(self._start + direction * values[0])

    level_info = "info.beam_top"
    above_key = "warn.above_cut"                 # (made above the plan's cut: not seen in it)

    def _create(self, end):
        bim.add_beam(self.doc, self._start, end, self.spec, self._level(), storey=self.doc.active_storey)

    def _add(self, end):
        if np.linalg.norm((end - self._start)[:2]) < MIN_LENGTH:
            return
        self._create(end)
        length = float(np.linalg.norm((end - self._start)[:2]))
        done = t("info." + self.name, l=_fmt(length), type=_name(self.spec), h=_fmt(self.top))
        if self.viewport.plan and self._level() - self._below() > self.viewport.cut_level() - 1e-9:
            self.host.message(t(self.above_key, done=done, h=_fmt(self.viewport.cut_height)), warning=True)
        else:
            self.host.message(done)
        self._start, self._end = np.array(end, dtype=float), None      # (the next one goes on from here)
        self.viewport.clear_overlays()

    def cancel(self):
        self._start = self._end = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
        if hasattr(self.host, "vcb_title_changed") and getattr(self.host, "tool", None) is self:
            self.host.vcb_title_changed()              # (its top's height again)


SLOPES = (0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05)     # a pipe's fall (0.136): 0 to 5 %
STACK_BOTTOM = -0.30        # a stack's foot under the storey's floor, where the collector takes it (0.136)


def slope_text(slope):
    return format_slope(slope, decimal_sep())


class _SegmentTool(BeamTool):
    """Pipe / Duct (0.69): drawn like a beam — point by point, its axis at a height above the active storey
    (typed before the first click to change it); each one goes on from where the last one ended. 0.136: a
    pipe falls along it by its slope (drainage); a new axis height while drawing makes a riser there (up or
    down, a bend at each end, as in Revit); a pipe can be a stack (vertical, one click); a click on a free end
    goes on from it, at its height."""

    default_key = ""
    default_z = 0.0
    level_info = "info.segment_z"
    top_label = "ctx.axis_z"
    above_key = "info.above_cut_dashed"          # (0.135: above the plan's cut it is shown dashed)
    slopes = ()                                  # (0.136) the falls it offers (a pipe's)
    forms = ("run",)                             # (0.136) "run": point by point; "stack": vertical, one click

    def __init__(self, host):
        super().__init__(host)
        self.spec = catalog.BY_KEY[self.default_key]
        self.top = self.default_z                  # (here: the axis's height above the active storey)
        self.slope = 0.0                           # fall per metre along it (0.01: 1 %)
        self.form = "run"
        self.system = systems_model.DEFAULT.get(self.name)  # (0.141) the system what it draws is in (a conduit: none)
        self.stack_top = None                      # a stack's top above the storey (None: the building's top)
        self.stack_bottom = STACK_BOTTOM
        self._z = None                             # the axis's height (absolute) where the run goes on
        self._last = None                          # (the last one drawn, its end): the next one joins it
        self._tee_from = None                      # (0.137) the pipe it started on, in its middle: a tee there
        self._ended_on = False                     # (0.137) the last one ended on a pipe (a tee): the run ends
        self._to_terminal = False                  # (0.138) …on an air terminal
        self._from_port = None                     # (0.138) the terminal it starts on, at its port's height

    def options(self):
        out = [type_option(self.spec, self.name)]
        if systems_model.of_kind(self.name):
            out.append(Option("system", t("ctx.system"), "choice", self.system,
                              tuple((k, t("system." + k)) for k in systems_model.of_kind(self.name))))
        if self.form == "stack":
            out += [length_option("stack_top", "ctx.stack_top", self._stack_top()),
                    length_option("stack_bottom", "ctx.stack_bottom", self.stack_bottom)]
        else:
            out.append(length_option("top", self.top_label, self.top))
            if self.slopes:
                out.append(Option("slope", t("ctx.slope"), "choice", self.slope,
                                  tuple((s, slope_text(s)) for s in self.slopes)))
        if len(self.forms) > 1:
            out.append(Option("form", t("ctx.segment_form"), "choice", self.form,
                              tuple((f, t("segform." + f)) for f in self.forms)))
        return out

    def set_option(self, key, value):
        if key == "top" and self._start is not None and self.form == "run":
            self.top = value                       # (while drawing: a riser to that height, then on from it)
            self._rise(self.doc.work_level() + value)
        elif key == "slope":
            self.slope = float(value)
        elif key == "system" and value in systems_model.SYSTEMS:
            self._take_system(value)
        elif key == "form" and value in self.forms:
            self.cancel()
            self.form = value
        elif key == "stack_top":
            self.stack_top = value
        elif key == "stack_bottom":
            self.stack_bottom = value
        else:
            super().set_option(key, value)
            return
        self.host.set_hint(self.hint())

    def _take_system(self, key):
        """(0.141) Draw in this system from now on: a drain falls (2 %, if it was level), water and air are level."""
        if key not in systems_model.SYSTEMS or systems_model.SYSTEMS[key][0] != self.spec.kind:
            return
        self.system = key
        if self.slopes:
            drain = systems_model.SYSTEMS[key][4]
            if drain and self.slope <= 0:
                self.slope = 0.02
                self.host.message(t("info.system_drain", s=t("system." + key), p=slope_text(self.slope)))
            elif not drain:
                self.slope = 0.0

    def _adopt(self, key, guid):
        """(0.141) Starting on a pipe, a fixture's outlet…: the run is in its system (as in Revit)."""
        if key is None or key == self.system or key not in systems_model.SYSTEMS \
                or systems_model.SYSTEMS[key][0] != self.spec.kind:
            return
        self._take_system(key)
        obj = self.doc.get(guid)
        self.host.message(t("info.system_from_port", name=obj.name if obj is not None else "",
                            s=t("system." + key)))
        self.host.set_hint(self.hint())

    def _stack_top(self):
        """A stack's top above the active storey: as set, or up to the highest storey's ceiling."""
        if self.stack_top is not None:
            return self.stack_top
        levels = [z for _g, _n, z in self.doc.storeys()] or [0.0]
        return max(levels) - self.doc.work_level() + bim.WALL_HEIGHT

    def hint(self):
        if self.form == "stack":
            return t("hint.segment.stack", type=_name(self.spec), a=_fmt(self._stack_top()), b=_fmt(self.stack_bottom))
        if self._start is not None:
            return t("hint.segment.next")
        return t("hint.segment.start", type=_name(self.spec), h=_fmt(self.top))

    def _level(self):
        return self._z if self._z is not None else self.doc.work_level() + self.top

    def _below(self):
        return self.spec.profile[1] / 2            # the axis is the section's middle

    def _free_end(self, p):
        """(0.136) A free end of this kind near p (plan), at any height: (GlobalId, end), or None."""
        try:
            return self.doc.ifc.free_end_near(p, self.spec.kind, self._level(), max(self.spec.profile[0], 0.10))
        except RuntimeError:                       # (the IFC still being read)
            return None

    def _on_axis(self, p, z):
        """(0.137) A pipe / duct of this kind whose axis is under p (plan), with room for a tee — a stack's at the
        height z: (GlobalId, the point on it), or None."""
        leave = {g for g in ((self._last[0] if self._last else None), self._tee_from) if g}
        try:
            return self.doc.ifc.on_axis(p, self.spec.kind, max(self.spec.profile[0], 0.10), z=z, leave=leave)
        except RuntimeError:
            return None

    def _terminal(self, p):
        """(0.138) An air terminal — or (0.139) a unit — with a free port of this kind's system (a duct's, a pipe's:
        a unit's drain) under p (plan): (GlobalId, its port, the port's point), or None."""
        classes, port_kind = {
            "duct": (("IfcAirTerminal", "IfcUnitaryEquipment"), "DUCT"),
            "conduit": (("IfcOutlet", "IfcSwitchingDevice", "IfcElectricDistributionBoard", "IfcJunctionBox",
                         "IfcElectricAppliance"), "CABLE"),                 # (an electrical point's, 0.146; 0.198:
            #                                                                 an appliance's supply)
        }.get(self.spec.kind, (("IfcUnitaryEquipment", "IfcSanitaryTerminal", "IfcElectricAppliance", "IfcBurner"),
                               "PIPE"))                         # (a fixture's: 0.140; 0.198: an appliance's water, gas)
        try:
            return self.doc.ifc.free_port_near(p, max(self.spec.profile[0], 0.10), classes=classes, system=port_kind,
                                               prefer=self.system)           # (its system's outlet first, 0.141)
        except RuntimeError:
            return None

    def _port_tip(self, terminal, start):
        """The tip over a terminal's / a unit's port: start on it, or join it."""
        port = terminal[1]
        owner = self.doc.get(terminal[0])
        if owner is not None and owner.ifc_class in ("IfcUnitaryEquipment", "IfcSanitaryTerminal"):
            if port.Name in ("supply", "return", "condensate"):
                name = t("port." + port.Name)
            else:
                name = t("conn." + port.Name) if port.Name in ("drain", "cold", "hot") else port.Name
            return t("tip.segment_from_port" if start else "tip.segment_to_port", port=name)
        return t("tip.segment_from_terminal" if start else "tip.segment_to_terminal")

    def _drop_min(self):
        """(0.195) A pipe ended on this much higher or lower than the run is joined by a piece straight down (or up)
        to it, not by making the run slope to it."""
        return max(float(self.spec.profile[0]), 0.10)

    def _end_z(self, end):
        """The axis's height at `end` if the run goes there (its slope)."""
        start = np.array((self._start[0], self._start[1]), dtype=float)
        return self._z - self.slope * float(np.linalg.norm(np.asarray(end, dtype=float)[:2] - start))

    def pointer_move(self, x, y, modifiers):
        if self.form == "stack":
            p, snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
            if p is None:
                return
            self._hover = (p, snap)
            w, d = self.spec.profile
            lo, hi = self.doc.work_level() + self.stack_bottom, self.doc.work_level() + self._stack_top()
            foot = [np.array((p[0] + sx * w / 2, p[1] + sy * d / 2, lo)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            segs = box_edges(foot, [c + Z * (hi - lo) for c in foot])
            self.viewport.show_polygon(foot, segments=segs, colors=[PREVIEW] * len(segs))
            show_snap(self.viewport, snap, p)
            return
        if self._start is None:
            p, snap = self._point(x, y, self._level(), modifiers=modifiers)
            if p is None:
                return
            self._hover = (p, snap)
            found = self._free_end(p)
            if found is not None:                  # (a click here goes on from that end, at its height)
                self.viewport.show_marker(found[1], SNAP_COLORS["endpoint"])
                self.viewport.show_tip(t("tip.segment_go_on", h=_fmt(float(found[1][2]) - self.doc.work_level())),
                                       found[1])
                return
            terminal = self._terminal(p)
            if terminal is not None:               # (0.138: it starts on that terminal, up from it)
                self.viewport.show_marker(terminal[2], SNAP_COLORS["endpoint"])
                self.viewport.show_tip(self._port_tip(terminal, True), terminal[2])
                return
            on = self._on_axis(p, self._level())
            if on is not None:                     # (0.137: it starts on that pipe, a tee there)
                self.viewport.show_marker(on[1], SNAP_COLORS["on_edge"])
                self.viewport.show_tip(t("tip.segment_tee_from", h=_fmt(float(on[1][2]) - self.doc.work_level())),
                                       on[1])
                return
            show_snap(self.viewport, snap, p)
            return
        super().pointer_move(x, y, modifiers)
        if self._end is not None:
            terminal = self._terminal(self._end)
            on = self._on_axis(self._end, self._end_z(self._end)) if terminal is None else None
            if terminal is not None:               # (0.138: it ends over that terminal, down to it)
                self.viewport.show_marker(terminal[2], SNAP_COLORS["endpoint"])
                self.viewport.show_tip(self._port_tip(terminal, False), terminal[2])
            elif on is not None:                   # (0.137: it ends on that pipe, a tee there)
                self.viewport.show_marker(on[1], SNAP_COLORS["on_edge"])
                drop = float(on[1][2]) - self._end_z(self._end)
                if abs(drop) > self._drop_min():   # (0.195) at another height: down (or up) to it
                    self.viewport.show_tip(t("tip.segment_tee_down" if drop < 0 else "tip.segment_tee_up",
                                             d=_fmt(abs(drop))), on[1])
                else:
                    self.viewport.show_tip(t("tip.segment_tee_to"), on[1])

    def pointer_down(self, x, y, button, modifiers):
        if button == LEFT and self.form == "stack":
            p, _snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
            if p is not None:
                self._add_stack(p)
            return
        if button == LEFT and self._start is None:
            p, _snap = self._point(x, y, self._level(), modifiers=modifiers)
            if p is None:
                return
            found = self._free_end(p)
            terminal = self._terminal(p) if found is None else None
            if terminal is not None:               # (0.138) from a terminal: up from its port to the axis's height
                self._adopt(self.doc.ifc.port_system(terminal[1]), terminal[0])
                self._from_terminal(terminal)
                return
            on = self._on_axis(p, self._level()) if found is None else None
            if found is not None:                  # on from a free end: its point, its height
                self._last = (found[0], np.array(found[1], dtype=float))
                p = np.array(found[1], dtype=float)
                self._adopt(self.doc.system_of(found[0]), found[0])
            elif on is not None:                   # (0.137) from the middle of a pipe: a tee there, its height
                self._tee_from = on[0]
                p = np.array(on[1], dtype=float)
                self._adopt(self.doc.system_of(on[0]), on[0])
            self._z = float(p[2]) if found is not None or on is not None else self._level()
            self._start = np.array((p[0], p[1], self._z))
            self.host.set_hint(self.hint())
            if hasattr(self.host, "vcb_title_changed"):
                self.host.vcb_title_changed()
            return
        super().pointer_down(x, y, button, modifiers)

    def _from_terminal(self, terminal):
        """(0.138) The run starts on an air terminal: a vertical piece up from its port to the axis's height (at
        it already: from the port itself), connected to it; the run goes on from its top. A port on a unit's side
        (0.139): the run starts at it, at its height."""
        guid, port, at = terminal
        level = self._level()
        at = np.asarray(at, dtype=float)
        try:                                       # (a conduit always rises from a point: up the wall, 0.146)
            side = abs(float(self.doc.ifc.port_way(port)[2])) <= 0.7 and self.spec.kind != "conduit"
        except RuntimeError:
            side = False
        if not side and abs(level - float(at[2])) >= MIN_LENGTH:
            rise = bim.add_segment(self.doc, at[:2], at[:2], self.spec, float(at[2]), storey=self.doc.active_storey,
                                   end_z=level, from_port=guid, system=self.system)
            self._last = (rise, np.array((at[0], at[1], level)))
            self._z = level
        else:
            self._from_port = guid
            self._z = float(at[2])
        self._start = np.array((at[0], at[1], self._z))
        self.host.set_hint(self.hint())
        if hasattr(self.host, "vcb_title_changed"):
            self.host.vcb_title_changed()

    def _joined_last(self, start):
        """The last one drawn if this one starts at its end — it is joined to it."""
        last = self._last
        if last is not None and not np.allclose(last[1], start, atol=1e-6):
            return None                            # (it starts somewhere else)
        return last[0] if last else None

    def _create(self, end):
        """The segment, joined to the one drawn just before (0.74: a bend in the corner, or connected in
        line) — or to one of the same kind ending where it starts. A pipe with a slope falls along it."""
        start = np.array((self._start[0], self._start[1], self._z), dtype=float)
        end_z = self._end_z(end)
        tees = [self._tee_from] if self._tee_from else []
        terminal = self._terminal(end)
        on = self._on_axis(end, end_z) if terminal is None else None
        if terminal is not None:                   # (0.138) over a terminal: it ends there and comes down to it
            end = np.array((terminal[2][0], terminal[2][1], 0.0))   # (a unit's side port: bim takes it from out)
            end_z = self._z
        elif on is not None and abs(float(on[1][2]) - end_z) > self._drop_min():
            # (0.195) a pipe at another height: on at its own height over (or under) it, then straight down (or up)
            # to it, a tee there — as Revit does; one undo step
            over = np.array((on[1][0], on[1][1], 0.0))
            mark = self.doc.undo_mark()
            guid = bim.add_segment(self.doc, start, over, self.spec, self._z, storey=self.doc.active_storey,
                                   after=self._joined_last(start), end_z=end_z, tee=tees or None,
                                   from_port=self._from_port, system=self.system)
            top = np.array((over[0], over[1], end_z))
            drop = bim.add_segment(self.doc, top, top, self.spec, end_z, storey=self.doc.active_storey, after=guid,
                                   end_z=float(on[1][2]), tee=[on[0]], system=self.system)
            self.doc.join_since(mark)
            self._tee_from = self._from_port = None
            self._ended_on, self._to_terminal = True, None
            self._dropped = float(on[1][2]) - end_z
            self._last = (drop, np.array((over[0], over[1], float(on[1][2]))))
            self._z = float(on[1][2])
            return over
        elif on is not None:                       # (0.137) it ends on a pipe: there, at its height; a tee
            end, end_z = np.array((on[1][0], on[1][1], 0.0)), float(on[1][2])
            tees.append(on[0])
        guid = bim.add_segment(self.doc, start, end, self.spec, self._z, storey=self.doc.active_storey,
                               after=self._joined_last(start), end_z=end_z, tee=tees or None,
                               to_port=terminal[0] if terminal is not None else None, from_port=self._from_port,
                               system=self.system)
        self._tee_from = self._from_port = None
        self._dropped = 0.0
        self._ended_on = on is not None or terminal is not None
        self._to_terminal = terminal[0] if terminal is not None else None
        self._last = (guid, np.array((end[0], end[1], end_z), dtype=float))
        self._z = end_z
        return end

    def _rise(self, z):
        """(0.136) Up or down where the run is now, to the height z: a vertical piece joined to the last one (a
        bend), the next one joined to it — as Revit does when the height changes while drawing."""
        if self._start is None or abs(z - self._z) < MIN_LENGTH:
            return
        start = np.array((self._start[0], self._start[1], self._z), dtype=float)
        guid = bim.add_segment(self.doc, start, start, self.spec, self._z, storey=self.doc.active_storey,
                               after=self._joined_last(start), end_z=z, tee=self._tee_from, from_port=self._from_port,
                               system=self.system)
        self._tee_from = self._from_port = None
        key = "info.riser_up" if z > self._z else "info.riser_down"
        self.host.message(t(key, d=_fmt(abs(z - self._z)), h=_fmt(z - self.doc.work_level())))
        self._z = float(z)
        self._start = np.array((start[0], start[1], self._z))
        self._last = (guid, self._start.copy())
        self.viewport.clear_overlays()

    def _add_stack(self, p):
        """(0.136) A stack at p: vertical, from its top down to its foot (the flow: downwards; a collector drawn
        from its foot goes on from it)."""
        level = self.doc.work_level()
        top, bottom = level + self._stack_top(), level + self.stack_bottom
        if top - bottom < MIN_LENGTH:
            self.host.message(t("err.stack_short"), warning=True)
            return
        bim.add_segment(self.doc, p, p, self.spec, top, storey=self.doc.active_storey, end_z=bottom,
                        system=self.system)
        self.viewport.clear_overlays()
        self.host.message(t("info.stack", l=_fmt(top - bottom), type=_name(self.spec), a=_fmt(top - level),
                            b=_fmt(bottom - level)))

    def _add(self, end):
        if np.linalg.norm((np.asarray(end, dtype=float) - self._start)[:2]) < MIN_LENGTH:
            return
        z0 = self._z
        end = self._create(end)
        dropped = getattr(self, "_dropped", 0.0)        # (0.195) down (or up) to a pipe at another height
        z1 = self._z - dropped                           # (where the run itself ended)
        length = float(np.linalg.norm((np.asarray(end, dtype=float) - self._start)[:2]))
        h = _fmt(z0 - self.doc.work_level())
        if abs(z0 - z1) > 1e-9 and length > 1e-9:
            done = t("info.segment_sloped", what=t("elem." + self.name), l=_fmt(length), type=_name(self.spec),
                     s=slope_text((z0 - z1) / length), h=h, h2=_fmt(z1 - self.doc.work_level()))
        else:
            done = t("info." + self.name, l=_fmt(length), type=_name(self.spec), h=h)
        if self._ended_on:                         # (0.137) on a pipe: joined by a tee, the run ends there
            key, name = "info.segment_tee", ""
            if self._to_terminal:
                unit = self.doc.get(self._to_terminal)
                key = "info.segment_port" if unit is not None and unit.ifc_class in (
                    "IfcUnitaryEquipment", "IfcSanitaryTerminal") else "info.segment_terminal"
                name = unit.name if unit is not None else ""
            elif abs(dropped) > 1e-9:
                key, name = "info.segment_tee_down" if dropped < 0 else "info.segment_tee_up", _fmt(abs(dropped))
            done = t(key, done=done, name=name)
        if self.viewport.plan and min(z0, self._z) - self._below() > self.viewport.cut_level() - 1e-9:
            self.host.message(t(self.above_key, done=done, h=_fmt(self.viewport.cut_height)), warning=True)
        else:
            self.host.message(done)
        if self._ended_on:
            self.cancel()
            return
        self._start, self._end = np.array((end[0], end[1], self._z), dtype=float), None
        self.viewport.clear_overlays()

    def typed(self, text):
        if self.form == "stack":                   # (a stack: its top)
            values = parse_lengths(text, 1)
            if values is None or values[0] is None:
                self.host.message(t("err.bad_value", t=text), warning=True)
                return
            self.stack_top = values[0]
            self.host.set_hint(self.hint())
            return
        super().typed(text)

    def cancel(self):
        self._last = None
        self._z = None
        self._tee_from = self._from_port = None
        super().cancel()


class PipeTool(_SegmentTool):
    name = "pipe"
    default_key = "tubo_50"
    default_z = 0.30                               # (low: seen in the plan, under its cut)
    slopes = SLOPES
    forms = ("run", "stack")


class DuctTool(_SegmentTool):
    name = "duct"
    default_key = "conduta_30x20"
    default_z = 2.50                               # (high, under the slab: seen in 3D)


class ConduitTool(_SegmentTool):
    """(0.146) The electrical conduits (IfcCableCarrierSegment): drawn as a pipe, high (over the ceiling); started on
    an electrical point it rises from it, drawn to one it comes down to it."""
    name = "conduit"
    default_key = "tubo_vd20"
    default_z = 2.75                               # (over a 2,60 m ceiling, in the slab's zone)


class GridTool(_PointTool):
    """Grid axis (0.67): two clicks — or a click and a typed length — make an axis of the structural
    grid, on the plan, tagged by itself: 1, 2, 3… running along Y, A, B, C… running along X. The snaps
    and alignments as for walls; its tag changes in the Project panel (Eixos)."""

    name = "grid"
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.chain"

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self._start = self._end = None

    def hint(self):
        return t("hint.grid.next") if self._start is not None else t("hint.grid.start")

    def vcb_title(self):
        return t("vcb.length")

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, self.doc.work_level(), self._start, modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        if self._start is None:
            show_snap(self.viewport, snap, p)
            return
        self._end = p
        self.viewport.show_polygon([], segments=[self._start, p], colors=[PREVIEW, PREVIEW])
        drawing_dims(self.viewport, self._start, p)
        tip, color, _line = inferred_style(snap) if snap is not None else ("", PREVIEW, PREVIEW)
        self.viewport.show_marker(p, color)
        self.viewport.show_tip(tip, p if tip else None)
        self.host.set_vcb(_fmt(float(np.linalg.norm((p - self._start)[:2]))))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self._start is None:
            p, _snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
            if p is not None:
                self._start = p
                self.host.set_hint(self.hint())
            return
        if self._end is not None:
            self._add(self._end)

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None or values[0] is None or self._start is None:
            self.host.message(t("err.bad_value", t=text) if values is None else t("hint.grid.start"), warning=True)
            return
        direction = horizontal_dir(self._start, self._end) if self._end is not None else None
        if direction is None:
            direction = np.array((0.0, 1.0, 0.0))
        self._add(self._start + direction * values[0])

    def _add(self, end):
        if np.linalg.norm((end - self._start)[:2]) < MIN_LENGTH:
            return
        tag = bim.add_grid_axis(self.doc, self._start, end)
        self.host.message(t("info.grid_axis", tag=tag, l=_fmt(float(np.linalg.norm((end - self._start)[:2])))))
        self.cancel()

    def cancel(self):
        self._start = self._end = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")


class FootingTool(_PointTool):
    """Footing (0.68), as Revit's foundations: a click on a column puts a pad under it (centred on its
    foot, its top at the column's base); a click on a wall puts a strip under its whole length; a click
    anywhere else, a pad there with its top at the active storey's level. The last pad type and the last
    strip type chosen are used — each where it belongs."""

    name = "footing"
    accepts_typing = False
    common_keys = frozenset(("r", "shift+r"))
    placement = True
    keys_help = "keys.footing"

    def __init__(self, host):
        super().__init__(host)
        self.pad = catalog.BY_KEY["sapata_80"]
        self.strip = catalog.BY_KEY["sapata_corrida_50"]
        self.spec = self.pad
        self.angle = 0              # a pad on its own (not under a column): R / Shift+R turn it (0.86)

    def common_key(self, name):
        self.angle = placement.turn(self.angle, 1 if name == "r" else -1)
        self.host.message(t("info.turned", a=self.angle))
        return True

    def set_spec(self, spec):
        self.spec = spec
        if spec.strip:
            self.strip = spec
        else:
            self.pad = spec
        self.host.set_hint(self.hint())

    def options(self):
        return [type_option(self.pad, "footing", "pad", "ctx.pad", lambda s: not s.strip),
                type_option(self.strip, "footing", "strip", "ctx.strip", lambda s: s.strip)]

    def set_option(self, key, value):
        if key in ("pad", "strip"):
            self.set_spec(catalog.BY_KEY[value])

    def hint(self):
        return t("hint.footing", pad=_name(self.pad), strip=_name(self.strip))

    def _target(self, x, y, modifiers):
        """(place, type, storey, what it goes under: "column" / "wall" / None, the snap of a free point)
        for the mouse at x, y."""
        hit = self.viewport.pick_point(x, y)
        obj = self.doc.get(hit[0]) if hit else None
        if obj is not None and obj.is_bim:
            kind = self.doc.ifc.kind_of(obj.id)
            spec = self.strip if kind == "wall" else self.pad
            place = bim.footing_place(self.doc, obj.id, spec) if kind in ("column", "wall") else None
            if place is not None:
                return place, spec, None, kind, None
        p, snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
        if p is None:
            return None
        w, d = self.pad.profile
        x_dir, _y = placement.axes(self.angle)
        return (p[:2], x_dir, w, d, float(p[2])), self.pad, self.doc.active_storey, None, snap

    def pointer_move(self, x, y, modifiers):
        target = self._target(x, y, modifiers)
        if target is None:
            return
        (centre, x_dir, length, width, top), spec, _storey, under, snap = target
        xd = np.array((x_dir[0], x_dir[1], 0.0))
        yd = np.cross(Z, xd)
        c = np.array((centre[0], centre[1], top))
        ring = [c + xd * sx * length / 2 + yd * sy * width / 2 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        segs = box_edges([p - Z * spec.thickness for p in ring], ring)
        if under is not None:                      # (no snap marker nor alignment left from a free point)
            self.viewport.clear_overlays()
        self.viewport.show_polygon(ring, segments=segs, colors=[PREVIEW] * len(segs))
        if snap is not None:
            show_snap(self.viewport, snap, c)
        else:
            self.viewport.show_marker(c)
            self.viewport.show_tip(t("tip.footing." + (under or "free"), type=_name(spec)), ring[2])

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        target = self._target(x, y, modifiers)
        if target is None:
            return
        place, spec, storey, under, _snap = target
        host = None
        if under is not None:                          # (0.93: tied to the column / wall it is under)
            hit = self.viewport.pick_point(x, y)
            host = hit[0] if hit else None
        bim.add_footing(self.doc, place, spec, storey=storey, under=host)
        self.viewport.clear_overlays()
        self.host.message(t("info.footing", type=_name(spec), a=_fmt(place[2]), b=_fmt(place[3]),
                            d=_fmt(spec.thickness)))

    def cancel(self):
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
