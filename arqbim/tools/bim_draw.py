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
from ..core.walls import REFERENCES, axis_lock, axis_offset, find_joint, horizontal_dir, left_normal, offset_axis
from ..i18n import decimal_sep, lang, refusal, t
from ..ifc import catalog
from ..ifc import systems as systems_model
from ..model import bim
from ..render.viewport import AXIS_U, AXIS_V, PARALLEL_COLOR, PREVIEW
from .base import (
    LEFT, RIGHT, SNAP_COLORS, Option, Tool, direction_snap, drawing_dims, glyph_of, infer_point, inferred_style,
    level_plane, outside_dim, show_snap, show_start_reference, snap_tip, snapped_edge, start_reference,
)
from . import pick_lines

Z = np.array((0.0, 0.0, 1.0))
ANGLES = (0, 90, 180, 270)
AXES = {"x": np.array((1.0, 0.0, 0.0)), "y": np.array((0.0, 1.0, 0.0))}
CLOSE_PX = 14
AXIS_END_PX = 12
MIN_LENGTH = 0.05
PARALLEL_REACH = 20.0   # (0.447) m: the walls this near the one being drawn are looked at for its parallel neighbours
WALL_SHAPES = ("line", "rect", "poly_in", "poly_out", "arc", "arc_center", "arc_tangent", "circle", "fillet", "pick",
               "face", "wand")                          # (0.102, 0.103) the Wall tool: point by point, a
#                                                          (0.457: Revit's «Inscribed / Circumscribed Polygon»)
#                                                          (0.454: Revit's «Center-ends Arc» and «Tangent End Arc»)
#                                                          (0.452: a fillet arc between two walls picked)
#                                                          (0.451: on a line or an edge picked, Revit's «Pick Lines»)
#                                                          rectangle, an arc, a circle, a face's outline; (0.374) the
#                                                          magic wand (a window over two parallel lines of a drawing)
ARCS = ("arc", "arc_center", "arc_tangent")             # (0.454) the shapes drawn as one curved wall


def _fmt(v):
    return format_length(v, decimal_sep())


def _name(spec):
    return spec.name_pt if lang() == "pt" else spec.name_en


def _short_angle(centre, a, b):
    """(0.454) The angle (radians, -π…π) from a to b about the centre, the shorter way."""
    u = math.atan2(a[1] - centre[1], a[0] - centre[0])
    v = math.atan2(b[1] - centre[1], b[0] - centre[0])
    return (v - u + math.pi) % (2 * math.pi) - math.pi


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
        self.offset = 0.0           # (0.451) Revit's «Offset»: the wall this far from the line drawn / picked
        self.chain = True           # (0.453) Revit's «Chain»: off, each wall starts with a click of its own…
        self.radius = 0.0           # …and «Radius»: the chain's corners rounded (0: sharp)
        self.sides = 6              # (0.457) a regular polygon's sides
        self._axes = None           # axis lines of the existing walls (cache)
        self._ends = None           # …their ends as one array (0.225)
        self._way_out = None        # (0.454) every wall's ends with the way out of each, for a tangent arc
        host.doc.subscribe(self._forget_axes)
        self._reset_chain()

    def _forget_axes(self, changed, removed):
        self._axes = None
        self._ends = None
        self._way_out = None

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
        self._turn = 0              # (0.454) a centre-ends arc: which way it turns (+1 counter-clockwise)
        self._tangent = None        # (0.454) a tangent arc: (where it starts, on the drawn line; the way it leaves)
        self._fillet = []           # (0.452) the walls picked for a fillet arc: [(GlobalId, the point clicked)]
        self._fillet_now = None     # …and the fillet under the mouse

    def set_spec(self, spec):
        self.spec = spec
        self.host.set_hint(self.hint())

    def _ref_text(self, reference=None):
        """The drawn line's name: along an outline (a rectangle, a circle, a face) its faces are inner and
        outer."""
        return t(("ref." if self.shape in ("line",) + ARCS else "refloop.") + (reference or self.reference))

    def options(self):
        opts = [type_option(self.spec, "wall"),
                Option("shape", t("ctx.wall_shape"), "choice", self.shape,
                       tuple((s, t("wallshape." + s)) for s in WALL_SHAPES)),
                length_option("height", "ctx.height", self.height),
                Option("reference", t("ctx.reference"), "choice", self.reference,
                       tuple((r, self._ref_text(r)) for r in REFERENCES))]
        if self.shape in ("line", "pick"):                  # (0.451) Revit's «Offset»
            opts.append(length_option("offset", "ctx.offset", self.offset))
        if self.shape in ("line", "arc_tangent"):           # (0.453) Revit's «Chain»…
            opts.append(Option("chain", t("ctx.chain"), "toggle", self.chain))
        if self.shape == "line":                            # …and «Radius»
            opts.append(length_option("radius", "ctx.corner_radius", self.radius))
        if self.shape in ("poly_in", "poly_out"):           # (0.457) a regular polygon's sides
            from ..core.outline_shapes import SIDES
            opts.append(Option("sides", t("ctx.sides"), "choice", self.sides, tuple((s, str(s)) for s in SIDES)))
        return opts

    def set_option(self, key, value):
        if key == "type":
            self.set_spec(catalog.BY_KEY[value])
        elif key == "height" and value > 0.1:
            self.height = value
        elif key == "offset":
            self.offset = float(value)
        elif key == "chain":
            self.chain = bool(value)
        elif key == "radius" and float(value) >= 0.0:
            self.radius = float(value)
        elif key == "sides" and int(value) >= 3:
            self.sides = int(value)
        elif key == "reference" and value in REFERENCES:
            self.reference = value
        elif key == "shape" and value in WALL_SHAPES and value != self.shape:
            # (0.454) from straight walls to tangent arcs and back, as Revit's: the chain goes on where it stands
            carry = self._chain_end() if {self.shape, value} == {"line", "arc_tangent"} else None
            self.shape = value
            self.cancel()
            if carry is not None:
                self._go_on(carry)
        self.host.set_hint(self.hint())
        if self.shape == "line" and self._start is not None and self._end is not None:
            self._preview(None, PREVIEW)

    def hint(self):
        ref = self._ref_text()
        if self.shape in ("poly_in", "poly_out"):            # (0.457)
            return t("hint.outline.{}_{}".format(self.shape, 1 if self._corner is not None else 0), n=self.sides) + \
                " " + t("hint.wall.loop_ref", type=_name(self.spec), ref=ref)
        if self.shape == "rect":
            if self._corner is not None:
                return t("hint.wall.rect_end", ref=ref)
            return t("hint.wall.rect_start", type=_name(self.spec), ref=ref)
        if self.shape == "face":
            return t("hint.wall.face", type=_name(self.spec), ref=ref)
        if self.shape == "wand":
            return t("hint.wall.wand", type=_name(self.spec), ref=ref)
        if self.shape == "pick":
            return t("hint.wall.pick", type=_name(self.spec), ref=ref)
        if self.shape == "fillet":
            return t("hint.wall.fillet_" + str(min(len(self._fillet), 2)), type=_name(self.spec))
        if self.shape == "arc":
            return t(("hint.wall.arc_start", "hint.wall.arc_end", "hint.wall.arc_bulge")[len(self._arc)],
                     type=_name(self.spec), ref=ref)
        if self.shape == "arc_center":                       # (0.454)
            return t("hint.wall.centre_" + str(min(len(self._arc), 2)), type=_name(self.spec), ref=ref)
        if self.shape == "arc_tangent":
            return t("hint.wall.tangent_" + ("1" if self._tangent is not None else "0"), type=_name(self.spec),
                     ref=ref)
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

    # ------------------------------------------------------------ (0.457) a regular polygon of walls

    def _polygon_ring(self, end):
        """The polygon's corners [(x, y)] — inscribed: `end` a corner; circumscribed: the middle of a side —, or
        None."""
        from ..core import outline_shapes
        if self._corner is None or end is None:
            return None
        loop = outline_shapes.regular(self._corner, end, self.sides, inscribed=self.shape == "poly_in")
        return None if loop is None else [tuple(c) for c in loop[0]]

    def _polygon_move(self, x, y, modifiers):
        p, snap = self._point(x, y, self._corner[2], self._corner, modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        self._end = p
        ring = self._polygon_ring(p)
        if ring is None:
            return
        z = float(self._corner[2])
        self._show_band(ring, z, np.array((float(self._corner[0]), float(self._corner[1]), z)))
        edge = np.array((p[0], p[1], z))
        self.viewport.show_temp_dims([temp_dims.TempDim(np.asarray(self._corner, dtype=float), edge, Z)])
        show_snap(self.viewport, snap, edge)
        self.host.set_vcb(_fmt(float(np.linalg.norm((p - self._corner)[:2]))))

    def _polygon_finish(self, end):
        ring = self._polygon_ring(end)
        if ring is None:
            return
        z = float(self._corner[2])
        made = bim.add_wall_loop(self.doc, [(x, y, z) for x, y in ring], self.spec, self.height, self.reference,
                                 storey=self.doc.active_storey)
        self.host.message(t("info.wall_polygon", n=len(made), type=_name(self.spec), ref=self._ref_text()))
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

    def _curve_finish(self, curve, z, keep=False):
        """The curved wall for the arc / circle drawn; the tool starts again, unless `keep` (0.454: a chain of tangent
        arcs goes on). True when made."""
        if curve is None:
            return False
        centre, radius, start, sweep = self._curve_axis(curve)
        if radius - self.spec.thickness / 2 < 0.05 or radius * abs(sweep) < MIN_LENGTH:
            self.host.message(t("err.wall_curve_small"), warning=True)
            return False
        bim.add_curved_wall(self.doc, (centre[0], centre[1], z), radius, start, sweep, self.spec, self.height,
                            storey=self.doc.active_storey)
        key = "info.wall_circle" if arcs.is_full(sweep) else "info.wall_arc"
        self.host.message(t(key, r=_fmt(curve[1]), a="{:.0f}".format(abs(math.degrees(sweep))),
                            l=_fmt(radius * abs(sweep)), type=_name(self.spec), ref=self._ref_text()))
        if not keep:
            self.cancel()
        return True

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

    # ------------------------------------------------------------ Revit's other arcs (0.454)

    def _hover_at(self, x, y, modifiers):
        """Before the first click: the point under the mouse, its snap shown (as for the arc and the circle)."""
        p, snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
        if p is None:
            return None
        self._hover = (p, snap)
        show_snap(self.viewport, snap, p)
        self._start_ref = start_reference(snap)
        show_start_reference(self.viewport, self._start_ref, p)
        return p

    def _centre_move(self, x, y, modifiers):
        """Revit's «Center-ends Arc»: its centre, its start (the radius), then its end — turning the way the mouse
        goes from the start (decided again while near it, kept past a right angle)."""
        if not self._arc:
            self._hover_at(x, y, modifiers)
            return
        c = self._arc[0]
        p, snap = self._point(x, y, c[2], self._arc[-1], modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        self._end = p
        if len(self._arc) == 1:                              # the radius, centre -> start
            self._curve = None
            self.viewport.show_lines([c, p], [PREVIEW, PREVIEW])
            drawing_dims(self.viewport, c, p)
            show_snap(self.viewport, snap, p)
            self.host.set_vcb(_fmt(float(np.linalg.norm((p - c)[:2]))))
            return
        a = self._arc[1]
        if self._turn == 0 or abs(_short_angle(c, a, p)) < math.pi / 2:
            self._turn = arcs.turn_of(c, a, p)
        self._curve = arcs.arc_from_centre(c, a, p, self._turn)
        if self._curve is None:
            return
        self.viewport.show_lines([c, a, c, np.array((*arcs.point_at(c, self._curve[1], sum(self._curve[2:])), c[2]))],
                                 [PREVIEW] * 4)
        self._show_curve(self._curve, c[2])
        show_snap(self.viewport, snap, p)
        self.host.set_vcb("{:.0f}°".format(abs(math.degrees(self._curve[3]))))

    def _centre_down(self, x, y, modifiers):
        if not self._arc:
            p, _snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
            if p is not None:
                self._arc.append(p)
                self.host.set_hint(self.hint())
            return
        if len(self._arc) == 1:
            p = self._end
            if p is not None and np.linalg.norm((p - self._arc[0])[:2]) >= MIN_LENGTH:
                self._arc.append(np.array((p[0], p[1], self._arc[0][2])))
                self._turn = 0
                self.host.set_hint(self.hint())
            return
        self._curve_finish(self._curve, self._arc[0][2])

    def _centre_typed(self, text):
        """The radius typed (after the centre), then the angle in degrees (after the start)."""
        if len(self._arc) == 2:
            try:
                degrees = float(text.replace("°", "").replace(",", ".").strip())
            except ValueError:
                self.host.message(t("err.bad_value", t=text), warning=True)
                return
            c, a = self._arc
            turn = self._turn or 1
            if abs(degrees) < 1e-6 or abs(degrees) > 360.0:
                return
            start = math.atan2(a[1] - c[1], a[0] - c[0])
            sweep = math.copysign(math.radians(abs(degrees)), turn * (1 if degrees > 0 else -1))
            self._curve_finish((c[:2], float(np.linalg.norm((a - c)[:2])), start, sweep), c[2])
            return
        values = parse_lengths(text, 1)
        if values is None or values[0] is None or values[0] <= 0:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        if not self._arc:
            if self._hover is None:
                return
            self._arc.append(self._hover[0].copy())
        c = self._arc[0]
        d = (self._end - c) if self._end is not None else np.array((1.0, 0.0, 0.0))
        d = np.array((d[0], d[1], 0.0))
        d = d / np.linalg.norm(d) if np.linalg.norm(d) > 1e-9 else np.array((1.0, 0.0, 0.0))
        self._arc.append(c + d * values[0])
        self._turn = 0
        self.host.set_hint(self.hint())

    def _wall_ends(self):
        """(0.454) Every wall's axis ends and the way out of the wall at each — (points (N, 3), directions (N, 2)) —
        the straight walls' and the curved ones' (along the arc), kept until the model changes."""
        if self._way_out is None:
            pts, dirs = [], []
            for _g, s, e, _t in self._wall_axes():
                d = horizontal_dir(s, e)
                if d is not None:
                    pts += [e, s]
                    dirs += [d[:2], -d[:2]]
            with self.doc.ifc.remembering():
                for obj in self.doc.objects.values():
                    if not obj.is_bim or obj.ifc_class not in ("IfcWall", "IfcWallStandardCase") or \
                            self.doc.ifc.kind_of(obj.id) != "curved_wall":
                        continue
                    centre, radius, start, sweep, _h, _th = self.doc.ifc.curved_wall_params(obj.id)
                    if arcs.is_full(sweep):
                        continue
                    for angle, way in ((start + sweep, 1.0), (start, -1.0)):
                        pts.append(np.array((*arcs.point_at(centre, radius, angle), float(centre[2]))))
                        dirs.append(arcs.along(angle, sweep) * way)
            self._way_out = (np.asarray(pts, dtype=float).reshape(-1, 3), np.asarray(dirs, dtype=float).reshape(-1, 2))
        return self._way_out

    def _way_out_at(self, x, y, level):
        """The wall end nearest the mouse on the screen, at this level, and the way out of the wall there —
        (point, direction (2,)) — or None."""
        pts, dirs = self._wall_ends()
        on = np.flatnonzero(np.abs(pts[:, 2] - level) <= 1e-4)
        if not len(on):
            return None
        xy = np.asarray(self.viewport.project_many(pts[on]), dtype=float)
        dist = np.hypot(xy[:, 0] - x, xy[:, 1] - y)
        dist[np.isnan(dist)] = np.inf
        k = int(np.argmin(dist))
        if dist[k] > 2 * AXIS_END_PX:
            return None
        return pts[on[k]].copy(), dirs[on[k]].copy()

    def _tangent_move(self, x, y, modifiers):
        """Revit's «Tangent End Arc»: from a wall's end (or where the chain stands), leaving it along it, to the
        point clicked."""
        if self._tangent is None:
            found = self._way_out_at(x, y, self.doc.work_level())
            self._hover = None
            self.viewport.show_alignments()
            if found is None:
                p, _snap = self._point(x, y, self.doc.work_level())
                self.viewport.show_marker(None)
                self.viewport.show_glyph(None)
                self.viewport.show_tip(t("tip.wall_tangent_none"), p)
                return
            p = found[0]
            if revit_look():
                self.viewport.show_marker(None)
                self.viewport.show_glyph("endpoint", p)
            else:
                self.viewport.show_marker(p, SNAP_COLORS["endpoint"])
            self.viewport.show_tip(t("snap.wall_axis"), p)
            return
        a, way = self._tangent
        p, snap = self._point(x, y, a[2], a, modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        self._end = p
        self._curve = arcs.arc_tangent(a, way, p)
        if self._curve is None:                              # straight ahead: no arc turns there
            self.viewport.show_volume([])
            self.viewport.show_label("", None)
            self.viewport.show_lines([a, p], [PREVIEW, PREVIEW])
            return
        self.viewport.show_lines()
        self._show_curve(self._curve, a[2])
        show_snap(self.viewport, snap, p)

    def _tangent_down(self, x, y, modifiers):
        if self._tangent is not None:
            self._tangent_finish(self._curve)
            return
        found = self._way_out_at(x, y, self.doc.work_level())
        if found is None:
            self.host.message(t("tip.wall_tangent_none"), warning=True)
            return
        point, way = found
        # the arc drawn as the bar's reference line, its axis starting on the wall's axis
        drawn = point - left_normal(np.array((*way, 0.0))) * axis_offset(self.reference, self.spec.thickness)
        self._tangent = (drawn, way)
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())

    def _tangent_typed(self, text):
        """The distance to the arc's end, towards the mouse."""
        values = parse_lengths(text, 1)
        if values is None or values[0] is None or values[0] <= 0:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        if self._tangent is None or self._end is None:
            return
        a, way = self._tangent
        d = (self._end - a)[:2]
        if float(np.linalg.norm(d)) < 1e-9:
            return
        b = a[:2] + d / float(np.linalg.norm(d)) * values[0]
        self._tangent_finish(arcs.arc_tangent(a, way, b))

    def _tangent_finish(self, curve):
        a, _way = self._tangent
        if curve is None or not self._curve_finish(curve, a[2], keep=True):
            return
        centre, radius, start, sweep = curve
        self._count += 1
        if not self.chain:
            self.cancel()
            return
        end = start + sweep                                  # the next arc leaves this one's end, tangent
        self._tangent = (np.array((*arcs.point_at(centre, radius, end), a[2])), arcs.along(end, sweep))
        self._curve = None
        self._end = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())

    def _chain_end(self):
        """(0.454) Where the chain stands and the way it goes — (point on the drawn line, direction (2,), its first
        wall, how many) — for it to go on as a tangent arc / a straight wall when the shape changes; or None."""
        if self.shape == "line" and self._start is not None and self._prev is not None:
            return self._start.copy(), np.asarray(self._prev[1][:2], dtype=float), self._first, self._count
        if self.shape == "arc_tangent" and self._tangent is not None:
            return self._tangent[0].copy(), self._tangent[1].copy(), self._first, self._count
        return None

    def _go_on(self, carry):
        point, way, first, count = carry
        self._first, self._count = first, count
        if self.shape == "arc_tangent":
            self._tangent = (point, way)
        else:
            self._start = point                              # (no corner to join: wall and arc meet tangent)

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

    # ------------------------------------------------------------ (0.451) Revit's «Pick Lines»

    def _picked_wall(self, x, y):
        """The wall a click would make on the line or edge under the mouse: (axis start, axis end, the edge picked),
        or None — its location line on the edge moved by the offset to the mouse's side, its body on that side when
        drawn by a face."""
        edge = pick_lines.edge_at(self.viewport, self.doc, x, y)
        if edge is None:
            return None
        level = self.doc.work_level()
        a, b = (np.array((p[0], p[1], level)) for p in edge)
        origin, direction = self.viewport.ray(x, y)
        mouse = ray_plane(origin, direction, np.array((0.0, 0.0, level)), Z)
        side = pick_lines.side_of(a, b, mouse if mouse is not None else (a + b) / 2)
        a, b = pick_lines.offset_segment(a, b, abs(self.offset), side)
        # (the body on the mouse's side: drawn as the left face it lies to the right, as the right face to the left)
        if (self.reference == "left" and side > 0) or (self.reference == "right" and side < 0):
            a, b = b, a
        axis_a, axis_b = offset_axis(a, b, self.reference, self.spec.thickness)
        return axis_a, axis_b, edge

    def _picked_arc(self, x, y):
        """(0.459, the owner: «no arco ele só seleciona segmentos em vez de arco inteiro») The curved wall a click would
        make on an arc drawn in pieces under the mouse — a polygon's rounded corner, a circle, an arc of lines, a curved
        wall's face: (centre (x, y, level), its axis' radius, start, sweep, the arc) — moved by the offset to the
        mouse's side, its body on that side when drawn by a face — or None (a straight edge there)."""
        arc = pick_lines.arc_at(self.viewport, self.doc, x, y)
        if arc is None:
            return None
        level = self.doc.work_level()
        origin, direction = self.viewport.ray(x, y)
        mouse = ray_plane(origin, direction, np.array((0.0, 0.0, level)), Z)
        radius, side = pick_lines.arc_offset(arc, mouse, self.offset)
        if self.reference != "axis":
            radius += side * self.spec.thickness / 2
        return np.array((arc.centre[0], arc.centre[1], level)), radius, arc.start, arc.sweep, arc

    def _pick_arc_move(self, found):
        centre, radius, start, sweep, arc = found
        t_ = self.spec.thickness
        if radius - t_ / 2 <= 0.05:
            self.viewport.clear_overlays()
            self.viewport.show_tip(t("err.wall_curve_small"), arc.points[len(arc.points) // 2])
            return
        z = float(centre[2])
        full = arcs.is_full(sweep)
        outer, inner = (arcs.arc_points(centre, r, start, sweep) for r in (radius + t_ / 2, radius - t_ / 2))
        if revit_look() and self.viewport.plan:
            loops = [outer, inner] if full else [list(outer) + list(inner[::-1])]
            segs = [np.array((*p, z)) for loop in loops for k in range(len(loop))
                    for p in (loop[k], loop[(k + 1) % len(loop)])]
            self.viewport.show_drawn(segs)
            self.viewport.show_glyph()
        else:
            tris, segs = band_solid.band_solid(outer, inner, z, self.height, closed=full,
                                               verticals=() if full else None)
            self.viewport.show_volume(tris, segs, [PREVIEW] * len(segs))
        length = radius * abs(sweep)
        self.viewport.show_tip(t("tip.wall_pick_arc", r=_fmt(radius), l=_fmt(length)),
                               np.array((*arcs.point_at(centre, radius, start + sweep / 2), z)))
        self.host.set_vcb(_fmt(radius))

    def _pick_move(self, x, y):
        arc = self._picked_arc(x, y)
        if arc is not None:                                  # (0.459) an arc drawn in pieces: a curved wall on it
            self._pick_arc_move(arc)
            return
        found = self._picked_wall(x, y)
        if found is None:
            self.viewport.clear_overlays()
            self.viewport.show_tip(t("tip.wall_pick_none"), self._point(x, y, self.doc.work_level())[0])
            return
        axis_a, axis_b, edge = found
        way = (axis_b - axis_a)[:2]
        side = np.array((-way[1], way[0])) / max(float(np.linalg.norm(way)), 1e-12) * self.spec.thickness / 2
        z = float(axis_a[2])
        corners = [np.array((*c, z)) for c in (axis_a[:2] + side, axis_b[:2] + side, axis_b[:2] - side,
                                                axis_a[:2] - side)]
        if revit_look() and self.viewport.plan:
            self.viewport.show_drawn([p for k in range(4) for p in (corners[k], corners[(k + 1) % 4])])
            self.viewport.show_glyph(None, None, edge)
        else:
            tris, segs = band_solid.band_solid([c[:2] for c in corners[:2]], [c[:2] for c in corners[:1:-1]],
                                               z, self.height, closed=False)
            self.viewport.show_volume(tris, segs, [PREVIEW] * len(segs))
        length = float(np.linalg.norm(way))
        self.viewport.show_tip(t("tip.wall_pick", l=_fmt(length)), (axis_a + axis_b) / 2)
        self.host.set_vcb(_fmt(length))

    def _pick_down(self, x, y):
        arc = self._picked_arc(x, y)
        if arc is not None:                                  # (0.459) the whole arc: a curved wall
            centre, radius, start, sweep, _arc = arc
            if radius - self.spec.thickness / 2 < 0.05 or radius * abs(sweep) < MIN_LENGTH:
                self.host.message(t("err.wall_curve_small"), warning=True)
                return
            bim.add_curved_wall(self.doc, centre, radius, start, sweep, self.spec, self.height,
                                storey=self.doc.active_storey)
            self.viewport.clear_overlays()
            self.host.message(t("info.wall_picked_arc", r=_fmt(radius), l=_fmt(radius * abs(sweep)),
                                type=_name(self.spec)))
            return
        found = self._picked_wall(x, y)
        if found is None:
            self.host.message(t("tip.wall_pick_none"), warning=True)
            return
        a, b, _edge = found
        if float(np.linalg.norm((b - a)[:2])) < MIN_LENGTH:
            return
        direction = horizontal_dir(a, b)
        axes = self._wall_axes()
        start_join = find_joint(a, direction, axes, self.spec.thickness)
        end_join = find_joint(b, direction, axes, self.spec.thickness)
        bim.add_wall(self.doc, a, b, self.spec, self.height, start_join=start_join and start_join[:3],
                     end_join=end_join and end_join[:3], storey=self.doc.active_storey)
        self.viewport.clear_overlays()
        self.host.message(t("info.wall_picked", l=_fmt(float(np.linalg.norm((b - a)[:2]))), type=_name(self.spec)))

    # ------------------------------------------------------------ (0.452) Revit's «Fillet Arc»

    def _wall_at(self, x, y):
        """(a straight wall's GlobalId, the point clicked on it) under the mouse, or None."""
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None
        obj = self.doc.get(hit[0])
        if obj is None or not obj.is_bim:
            return None
        try:
            if self.doc.ifc.kind_of(obj.id) != "wall":
                return None
        except (RuntimeError, AttributeError):
            return None
        return obj.id, np.asarray(hit[2], dtype=float)

    def _fillet_of(self, radius=None, through=None):
        """The fillet (core/fillet) of the two walls picked, of `radius` or through the point `through`, or None."""
        from ..core.fillet import fillet
        (a, keep_a), (b, keep_b) = self._fillet[:2]
        sa, ea, _t = self.doc.ifc.wall_axis(a)
        sb, eb, _t = self.doc.ifc.wall_axis(b)
        return fillet((sa, ea), keep_a, (sb, eb), keep_b, radius=radius, through=through)

    def _fillet_move(self, x, y):
        if len(self._fillet) < 2:
            found = self._wall_at(x, y)
            if found is None:
                self.viewport.clear_overlays()
                self.viewport.show_tip(t("tip.fillet_pick", n=len(self._fillet) + 1),
                                       self._point(x, y, self.doc.work_level())[0])
                return
            s, e, _t = self.doc.ifc.wall_axis(found[0])
            self.viewport.show_glyph(None, None, (s, e))
            self.viewport.show_tip(t("tip.fillet_pick", n=len(self._fillet) + 1), found[1])
            return
        from ..core.fillet import arc_points
        level = float(self.doc.ifc.wall_axis(self._fillet[0][0])[0][2])
        origin, direction = self.viewport.ray(x, y)
        mouse = ray_plane(origin, direction, np.array((0.0, 0.0, level)), Z)
        f = self._fillet_of(through=mouse) if mouse is not None else None
        self._fillet_now = f
        self.viewport.show_glyph()                          # (the wall lit while it was picked: no longer)
        if f is None:
            self.viewport.clear_overlays()
            return
        pts = arc_points(f)
        half = self.spec.thickness / 2
        out = [f.centre + (p - f.centre) * ((f.radius + half) / f.radius) for p in pts]
        inn = [f.centre + (p - f.centre) * (max(f.radius - half, 1e-3) / f.radius) for p in pts]
        ring = out + inn[::-1]
        segs = [np.array((*q, level)) for k in range(len(ring)) for q in (ring[k], ring[(k + 1) % len(ring)])]
        if revit_look() and self.viewport.plan:
            self.viewport.show_drawn(segs)
        else:
            self.viewport.show_lines(segs, [PREVIEW] * len(segs))
        self.viewport.show_tip(t("tip.fillet_radius", r=_fmt(f.radius)), np.array((*pts[len(pts) // 2], level)))
        self.host.set_vcb(_fmt(f.radius))

    def _fillet_down(self, x, y, radius=None):
        if len(self._fillet) < 2:
            found = self._wall_at(x, y)
            if found is None:
                self.host.message(t("tip.fillet_pick", n=len(self._fillet) + 1), warning=True)
                return
            if self._fillet and self._fillet[0][0] == found[0]:
                return                                       # (the same wall again: another one)
            self._fillet.append(found)
            self.host.set_hint(self.hint())
            return
        f = self._fillet_of(radius=radius) if radius is not None else getattr(self, "_fillet_now", None)
        if f is None:
            self.host.message(t("err.fillet_none"), warning=True)
            return
        (a, keep_a), (b, keep_b) = self._fillet[:2]
        try:
            bim.fillet_walls(self.doc, a, keep_a, b, keep_b, f.radius, self.spec, self.height,
                             storey=self.doc.active_storey)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self.host.message(t("info.fillet", r=_fmt(f.radius), type=_name(self.spec)))
        self._fillet = []
        self._fillet_now = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())

    def _shape_move(self, x, y, modifiers):
        if self.shape == "fillet":
            self._fillet_move(x, y)
            return
        if self.shape == "pick":
            self._pick_move(x, y)
            return
        if self.shape == "wand":
            if self._wand is not None:
                (x0, y0) = self._wand
                self.viewport.show_region([(x0, y0), (x, y0), (x, y), (x0, y)], "window")
            return
        if self.shape == "arc_center":                 # (0.454) Revit's «Center-ends Arc»…
            self._centre_move(x, y, modifiers)
            return
        if self.shape == "arc_tangent":                # …and «Tangent End Arc»
            self._tangent_move(x, y, modifiers)
            return
        if self.shape in ("arc", "circle"):
            self._curve_move(x, y, modifiers)
            return
        if self.shape in ("poly_in", "poly_out") and self._corner is not None:     # (0.457)
            self._polygon_move(x, y, modifiers)
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
        if self.shape == "fillet":                     # (0.452) two walls, then the arc between them
            self._fillet_down(x, y)
            return
        if self.shape == "pick":                       # (0.451) a wall on the line or edge clicked
            self._pick_down(x, y)
            return
        if self.shape == "wand":                       # (0.374) the window starts where pressed
            self._wand = (float(x), float(y))
            return
        if self.shape == "arc_center":                 # (0.454)
            self._centre_down(x, y, modifiers)
            return
        if self.shape == "arc_tangent":
            self._tangent_down(x, y, modifiers)
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
        if self.shape in ("poly_in", "poly_out"):            # (0.457) a regular polygon of walls
            self._polygon_finish(self._end)
            return
        self._rect_finish()

    def _shape_typed(self, text):
        if self.shape == "arc_center":                 # (0.454) a radius, then an angle in degrees
            self._centre_typed(text)
            return
        if self.shape == "arc_tangent":
            self._tangent_typed(text)
            return
        values = parse_lengths(text, 2)
        if values is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        if self.shape == "fillet":                     # (0.452) the arc's radius typed
            if len(self._fillet) >= 2 and values[0] is not None and values[0] > 0:
                self._fillet_down(0, 0, radius=values[0])
            return
        if self.shape in ("arc", "circle"):
            if values[0] is not None:
                self._curve_typed(values[0])
            return
        if self.shape in ("poly_in", "poly_out"):            # (0.457) its radius typed, towards the mouse
            if values[0] is None or values[0] <= 0:
                return
            if self._corner is None:
                if self._hover is None:
                    return
                self._corner = self._hover[0].copy()
            towards = (self._end - self._corner) if self._end is not None else np.array((1.0, 0.0, 0.0))
            towards = np.array((towards[0], towards[1], 0.0))
            n = float(np.linalg.norm(towards))
            towards = towards / n if n > 1e-9 else np.array((1.0, 0.0, 0.0))
            self._polygon_finish(self._corner + towards * values[0])
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
        a, b = self._drawn_axis(start, end)                                   # the wall's axis
        # Corners with walls drawn before, separately (the chain's own corners come from prev / first).
        axes = [w for w in self._wall_axes() if self._prev is None or w[0] != self._prev[0]]
        start_join = None if self._prev is not None else find_joint(a, direction, axes, self.spec.thickness)
        end_join = None if closing else find_joint(b, direction, axes, self.spec.thickness)
        guid = bim.add_wall(self.doc, a, b, self.spec, self.height, prev=self._prev,
                            first=(self._first[0], self._first[1]) if closing else None,
                            start_join=start_join and start_join[:3], end_join=end_join and end_join[:3],
                            storey=self.doc.active_storey)
        self._count += 1
        rounded = []
        if self.radius > 0 and self._prev is not None:     # (0.453) Revit's «Radius»: the corner rounded
            rounded.append(self._round_corner(self._prev[0], guid))
            if closing:
                rounded.append(self._round_corner(guid, self._first[0]))
        if self._first is None:
            self._first = (guid, direction, start.copy())
        self._prev = (guid, direction)
        text = t("info.wall", l=_fmt(float(np.linalg.norm((end - start)[:2]))), type=_name(self.spec))
        if start_join or end_join:
            text += " " + t("info.wall_joined")
        if rounded and not all(rounded):
            text += " " + t("info.corner_not_rounded", r=_fmt(self.radius))
        self.host.message(text)
        if closing:
            self.host.message(t("info.closed", n=self._count))
            self.cancel()
            return
        if not self.chain:                                  # (0.453) Revit's «Chain» off: the next one apart
            self._reset_chain()
            self.viewport.clear_overlays()
            self.host.set_hint(self.hint())
            return
        self._start = end.copy()
        self._end = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())

    def _round_corner(self, a, b):
        """(0.453) The corner between walls a and b of the chain rounded with the bar's Radius (a fillet arc, each
        kept on its middle's side). False when it could not be (too big a radius)."""
        try:
            keep_a = np.mean(self.doc.ifc.wall_axis(a)[:2], axis=0)
            keep_b = np.mean(self.doc.ifc.wall_axis(b)[:2], axis=0)
            bim.fillet_walls(self.doc, a, keep_a, b, keep_b, self.radius, self.spec, self.height,
                             storey=self.doc.active_storey)
            return True
        except (ValueError, RuntimeError):
            return False

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

    def _drawn_axis(self, start, end):
        """The wall's axis for the line drawn start → end: as its reference says, and (0.451) moved by the offset to
        the left of the way it is drawn (a negative one: to the right), as Revit's «Offset»."""
        a, b = offset_axis(start, end, self.reference, self.spec.thickness)
        d = horizontal_dir(start, end)
        if self.offset and d is not None:
            shift = left_normal(d) * self.offset
            a, b = a + shift, b + shift
        return a, b

    def _preview(self, tip, color, glyph=None, edge=None):
        a, b = self._drawn_axis(self._start, self._end)
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
