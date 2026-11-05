"""Slab (until 0.99 in bim_draw: two corners) and Edit outline (0.100).

Slab draws by its shape — Tab changes it, or the contextual bar:
    rectangle   two corners (or the size typed, "6;4");
    polygon     its corners one by one (a length typed goes on towards the mouse); a click on the first corner,
                or Enter, closes it; Delete takes the last corner back;
    circle      its centre, then a point of its edge (or the radius typed): a true circle in the IFC;
    magic wand  a click inside closed walls: the slab between their inner faces, or out to their outer faces.
Its function (structural / finish / excluded from the calculation) is on the contextual bar: a structural slab
at a storey's level is that storey's floor (its top at the level); a finish rests on the level.

Edit outline: the corners of a slab as grips — a click picks a corner up and the next puts it down (snaps,
alignments, X / Y, a typed distance); a click on a side's middle adds a corner there; with a corner picked up,
Delete takes it away. Each change is one undo step."""

import numpy as np

from ..core import roof_blocks as core_blocks
from ..core import roofs as core_roofs
from ..core import slabs as core_slabs
from ..core.sketch_geometry import ray_plane
from ..core.temp_dims import TempDim
from ..core.units import parse_lengths
from ..i18n import decimal_sep, t
from ..ifc import catalog
from ..model import bim
from ..render.viewport import PREVIEW
from .base import (LEFT, RIGHT, Option, drawing_dims, inferred_style, moved_enough, outside_dim, show_snap,
                   show_start_reference, start_reference)
from .bim_draw import CLOSE_PX, MIN_LENGTH, _fmt, _name, _PointTool, length_option, type_option

Z = np.array((0.0, 0.0, 1.0))
SHAPES = ("rect", "poly", "circle", "wand")


def _area(a):
    return "{:.2f} m²".format(a).replace(".", decimal_sep())


def _ring_segments(ring):
    return [q for a, b in zip(ring, ring[1:] + ring[:1]) for q in (a, b)]


class SlabTool(_PointTool):
    name = "slab"
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.slab"
    shapes = SHAPES

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.spec = catalog.BY_KEY["laje_12"]
        self.shape = "rect"
        self.function = "estrutural"
        self.reach = "interior"         # the magic wand: to the walls' inner faces, or their outer ones
        self._corner = None             # a rectangle's first corner; a circle's centre
        self._points = []               # a polygon's corners so far
        self._end = None                # the point under the mouse (a polygon's next corner, a circle's edge)
        self._start_ref = None          # before the first click: where a typed distance starts from
        self._du = self._dv = 0.0

    def set_spec(self, spec):
        self.spec = spec
        self.host.set_hint(self.hint())

    def options(self):
        opts = [type_option(self.spec, "slab"),
                Option("shape", t("ctx.slab_shape"), "choice", self.shape,
                       tuple((s, t("slabshape." + s)) for s in SHAPES)),
                Option("function", t("ctx.slab_function"), "choice", self.function,
                       tuple((f, t("slabfn." + f)) for f in core_slabs.FUNCTIONS))]
        if self.shape == "wand":
            opts.append(Option("reach", t("ctx.slab_reach"), "choice", self.reach,
                               tuple((r, t("slabreach." + r)) for r in core_slabs.REACHES)))
        return opts

    def set_option(self, key, value):
        if key == "type":
            self.set_spec(catalog.BY_KEY[value])
        elif key == "shape" and value in self.shapes:
            self.set_shape(value)
        elif key == "function" and value in core_slabs.FUNCTIONS:
            self.function = value
        elif key == "reach" and value in core_slabs.REACHES:
            self.reach = value
        self.host.set_hint(self.hint())

    def set_shape(self, shape):
        if shape != self.shape:
            self.shape = shape
            self.cancel()

    def tab(self):
        """Tab: rectangle -> polygon -> circle -> magic wand."""
        self.set_shape(self.shapes[(self.shapes.index(self.shape) + 1) % len(self.shapes)])
        self.host.message(t("info.slab_shape", shape=t("slabshape." + self.shape)))
        return True

    def hint(self):
        name = _name(self.spec)
        if self.shape == "poly":
            return t("hint.slab.poly_next") if self._points else t("hint.slab.poly_start", type=name)
        if self.shape == "circle":
            return t("hint.slab.circle_end") if self._corner is not None else t("hint.slab.circle_start", type=name)
        if self.shape == "wand":
            return t("hint.slab.wand", type=name, reach=t("slabreach." + self.reach))
        return t("hint.slab.end") if self._corner is not None else t("hint.slab.start", type=name)

    def vcb_title(self):
        return t("vcb.dims")

    # ------------------------------------------------------------ mouse

    def _level_point(self, x, y):
        """The point under the mouse on the active storey's level (the magic wand)."""
        z = self.doc.work_level()
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), Z)
        return p if p is not None else ray_plane(origin, direction, np.array((0.0, 0.0, z)), -Z)

    def _first_point(self, x, y, modifiers):
        """Before the first click: the snap shown, and where a typed distance would start from."""
        p, snap = self._point(x, y, modifiers=modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        show_snap(self.viewport, snap, p)
        self._start_ref = start_reference(snap)
        show_start_reference(self.viewport, self._start_ref, p)

    def pointer_move(self, x, y, modifiers):
        if self.shape == "wand":
            self._wand_preview(x, y)
            return
        if self.shape == "poly":
            if not self._points:
                self._first_point(x, y, modifiers)
                return
            last = self._points[-1]
            p, snap = self._point(x, y, last[2], last, modifiers)
            if p is None:
                return
            tip = None
            if len(self._points) >= 3 and self._near_screen(self._points[0], x, y):
                p, tip = self._points[0].copy(), t("snap.close")
            self._hover = (p, snap)
            self._end = p
            self._poly_preview(snap, tip)
            return
        if self._corner is None:
            self._first_point(x, y, modifiers)
            return
        p, snap = self._point(x, y, self._corner[2], self._corner if self.shape == "circle" else None,
                              modifiers=modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        if self.shape == "circle":
            self._end = p
            self._circle_preview(snap)
            return
        self._du, self._dv = float(p[0] - self._corner[0]), float(p[1] - self._corner[1])
        self._preview(snap)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self.shape == "wand":
            self._wand_click(x, y)
            return
        if self.shape == "poly":
            if not self._points:
                p, _snap = self._point(x, y, modifiers=modifiers)
                if p is not None:
                    self._points.append(p)
                    self.host.set_hint(self.hint())
                return
            if len(self._points) >= 3 and self._near_screen(self._points[0], x, y):
                self._finish_poly()
            elif self._end is not None:
                self._add_corner(self._end)
            return
        if self._corner is None:
            p, _snap = self._point(x, y, modifiers=modifiers)
            if p is not None:
                self._corner = p
                self.host.set_hint(self.hint())
            return
        if self.shape == "circle":
            self._finish_circle(self._radius())
        else:
            self._finish()

    def _near_screen(self, point, x, y):
        px, py = self.viewport.project(point)
        return np.hypot(px - x, py - y) <= CLOSE_PX

    # ------------------------------------------------------------ keyboard

    def enter(self):
        """Enter with nothing typed: a polygon closes."""
        if self.shape == "poly" and len(self._points) >= 3:
            self._finish_poly()

    def delete(self):
        """Delete: a polygon's last corner taken back."""
        if self.shape == "poly" and self._points:
            self._points.pop()
            self.host.message(t("info.slab_corner_back", n=len(self._points)))
            self.host.set_hint(self.hint())
            if not self._points:
                self.viewport.clear_overlays()

    def typed(self, text):
        values = parse_lengths(text, 2)
        if values is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        a, b = values
        if self.shape == "wand":
            return
        if self.shape in ("poly", "circle") and a is None:
            return
        started = self._points if self.shape == "poly" else self._corner is not None
        if not started and self._start_ref is not None and a is not None and b is None:
            # before the first click, on an alignment or an edge: the first point that far from its point
            src, direction = self._start_ref
            first = src + direction * a
            if self.shape == "poly":
                self._points.append(first)
            else:
                self._corner = first
            self.viewport.clear_overlays()
            self.host.set_hint(self.hint())
            self.host.message(t("info.start_typed", l=_fmt(a)))
            return
        if not started:
            if self._hover is None:
                return
            if self.shape == "poly":                       # forgiving: typed before clicking
                self._points.append(self._hover[0].copy())
            else:
                self._corner = self._hover[0].copy()
        if self.shape == "poly":
            last = self._points[-1]
            d = (self._end - last) if self._end is not None else np.array((1.0, 0.0, 0.0))
            d = np.array((d[0], d[1], 0.0))
            d = d / np.linalg.norm(d) if np.linalg.norm(d) > 1e-9 else np.array((1.0, 0.0, 0.0))
            self._add_corner(last + d * abs(a) * (1 if a > 0 else -1))
            return
        if self.shape == "circle":
            self._finish_circle(abs(a))
            return
        if a is not None:
            self._du = (-1.0 if self._du < 0 else 1.0) * a
        if b is not None:
            self._dv = (-1.0 if self._dv < 0 else 1.0) * b
        self._finish()

    def cancel(self):
        self._corner = None
        self._points = []
        self._end = None
        self._start_ref = None
        self._du = self._dv = 0.0
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    # ------------------------------------------------------------ rectangle

    def _finish(self):
        if abs(self._du) < MIN_LENGTH or abs(self._dv) < MIN_LENGTH:
            return
        bim.add_slab(self.doc, self._corner, self._du, self._dv, self.spec, storey=self.doc.active_storey,
                     function=self.function)
        self.host.message(t("info.slab", a=_fmt(abs(self._du)), b=_fmt(abs(self._dv)), type=_name(self.spec)))
        self.cancel()

    def _preview(self, snap):
        c = self._corner
        pts = [c, c + (self._du, 0, 0), c + (self._du, self._dv, 0), c + (0, self._dv, 0)]
        segs = _ring_segments(pts)
        self.viewport.show_polygon(pts, segments=segs, colors=[PREVIEW] * len(segs))
        dims = "{} × {}".format(_fmt(abs(self._du)), _fmt(abs(self._dv)))
        middle = (pts[0] + pts[2]) / 2
        self.viewport.show_temp_dims([outside_dim(pts[0], pts[1], middle), outside_dim(pts[1], pts[2], middle)])
        if snap is not None:
            tip, marker, _line = inferred_style(snap)
            self.viewport.show_marker(pts[2], marker)
            self.viewport.show_tip(tip, pts[2])
        else:
            self.viewport.show_marker(None)
            self.viewport.show_tip("", None)
        self.host.set_vcb(dims)

    # ------------------------------------------------------------ polygon

    def _add_corner(self, p):
        if np.linalg.norm((p - self._points[-1])[:2]) < MIN_LENGTH:
            return
        p = np.array((p[0], p[1], self._points[0][2]))
        if len(self._points) >= 3 and np.linalg.norm((p - self._points[0])[:2]) < 1e-6:
            self._finish_poly()
            return
        self._points.append(p)
        self.host.set_hint(self.hint())

    def _poly_preview(self, snap, tip=None):
        ring = self._points + ([self._end] if self._end is not None else [])
        z = self._points[0][2]
        ring = [np.array((p[0], p[1], z)) for p in ring]
        chain = [q for a, b in zip(ring, ring[1:]) for q in (a, b)]
        closing = [ring[-1], ring[0]] if len(ring) >= 3 else []
        self.viewport.show_polygon(ring if len(ring) >= 3 else [], segments=chain + closing,
                                   colors=[PREVIEW] * (len(chain) + len(closing)))
        if self._end is not None:
            drawing_dims(self.viewport, self._points[-1], self._end)
            self.host.set_vcb(_fmt(float(np.linalg.norm((self._end - self._points[-1])[:2]))))
        if tip:
            self.viewport.show_marker(ring[0], PREVIEW)
            self.viewport.show_tip(tip, ring[0])
        elif snap is not None:
            show_snap(self.viewport, snap, self._end)
        else:
            self.viewport.show_marker(self._end)
            self.viewport.show_tip("", None)
        if len(ring) >= 3:
            self.viewport.show_label(_area(core_slabs.ring_area([(p[0], p[1]) for p in ring])),
                                     np.mean(ring, axis=0))

    def _finish_poly(self):
        outline = [(float(p[0]), float(p[1])) for p in self._points]
        if core_slabs.outline_polygon(outline) is None:
            self.host.message(t("err.slab_outline_bad"), warning=True)
            return
        guid = bim.add_slab_outline(self.doc, outline, self._points[0][2], self.spec, storey=self.doc.active_storey,
                                    function=self.function)
        info = self.doc.ifc.slab_outline(guid)
        self.host.message(t("info.slab_outline", a=_area(info["area"]), n=len(outline), type=_name(self.spec)))
        self.cancel()

    # ------------------------------------------------------------ circle

    def _radius(self):
        if self._end is None or self._corner is None:
            return 0.0
        return float(np.linalg.norm((self._end - self._corner)[:2]))

    def _circle_preview(self, snap):
        r = self._radius()
        if r < 1e-6:
            return
        z = self._corner[2]
        ring = [np.array((x, y, z)) for x, y in core_slabs.circle_ring(self._corner, r)]
        segs = _ring_segments(ring)
        edge = np.array((self._end[0], self._end[1], z))
        self.viewport.show_polygon(ring, segments=segs + [self._corner, edge], colors=[PREVIEW] * (len(segs) + 2))
        self.viewport.show_temp_dims([TempDim(np.asarray(self._corner, dtype=float), edge, Z)])
        show_snap(self.viewport, snap, edge)
        self.host.set_vcb(_fmt(r))

    def _finish_circle(self, radius):
        if radius < MIN_LENGTH:
            return
        bim.add_slab_circle(self.doc, self._corner[:2], radius, self._corner[2], self.spec,
                            storey=self.doc.active_storey, function=self.function)
        self.host.message(t("info.slab_circle", r=_fmt(radius), type=_name(self.spec)))
        self.cancel()

    # ------------------------------------------------------------ magic wand

    def _wand_preview(self, x, y):
        p = self._level_point(x, y)
        if p is None:
            return
        region = bim.slab_wand(self.doc, p, self.reach)
        if region is None:
            self.viewport.clear_overlays()
            self.viewport.show_label(t("err.slab_wand_open"), p)
            return
        z = self.doc.work_level() + 0.01
        rings = [list(region.exterior.coords)[:-1]] + [list(h.coords)[:-1] for h in region.interiors]
        segs = [q for ring in rings for q in _ring_segments([np.array((cx, cy, z)) for cx, cy in ring])]
        outside = [np.array((cx, cy, z)) for cx, cy in rings[0]]
        self.viewport.show_polygon(outside, segments=segs, colors=[PREVIEW] * len(segs))
        self.viewport.show_label(_area(region.area), p)

    def _wand_click(self, x, y):
        p = self._level_point(x, y)
        if p is None:
            return
        region = bim.slab_wand(self.doc, p, self.reach)
        self.viewport.clear_overlays()
        if region is None:
            self.host.message(t("err.slab_wand_open"), warning=True)
            return
        outline = [tuple(c) for c in list(region.exterior.coords)[:-1]]
        holes = [[tuple(c) for c in list(h.coords)[:-1]] for h in region.interiors]
        bim.add_slab_outline(self.doc, outline, self.doc.work_level(), self.spec, storey=self.doc.active_storey,
                             holes=holes, function=self.function)
        self.host.message(t("info.slab_wand", a=_area(region.area), type=_name(self.spec),
                            reach=t("slabreach." + self.reach)))


ROOF_SLOPES = (5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0)


class RoofTool(SlabTool):
    """Roof (0.111): its outline as the Slab's — by the walls (a click inside them: their outer line), a rectangle
    or a polygon (the walls' outer line drawn) — with its form (flat, one, two or four slopes), slope and overhang
    on the contextual bar; it sits on the top of the walls under it (IfcRoof)."""

    name = "roof"
    keys_help = "keys.roof"
    # (face: a slab's or a sketch face's outline, 0.113; blocks: a roof made of blocks, two corners each, 0.262)
    shapes = ("wand", "rect", "poly", "face", "blocks")

    def __init__(self, host):
        super().__init__(host)
        self.spec = catalog.BY_KEY["cobertura_15"]        # (0.278: a roof type; before, a slab's)
        self.shape = "wand"
        self.reach = "exterior"
        self.form = "hip"
        self.slope = 30.0
        self.overhang = 0.50
        self.block_form = "hip"         # (0.262) the next block's form
        self._target = None             # (0.262) the roof by blocks the next block goes into (None: a new one)

    def activate(self):
        """(0.262) A roof by blocks selected: the blocks drawn go into it."""
        self._target = None
        selected = list(self.viewport.selection)
        if len(selected) == 1 and self.doc.ifc.kind_of(selected[0]) == "roof" and \
                self.doc.ifc.roof_params(selected[0])["form"] == "blocks":
            self._target = selected[0]
        super().activate()

    def options(self):
        if self.shape == "blocks":
            form = Option("block_form", t("ctx.roof_form"), "choice", self.block_form,
                          tuple((f, t("roofform." + f)) for f in core_blocks.FORMS))
        else:
            form = Option("form", t("ctx.roof_form"), "choice", self.form,
                          tuple((f, t("roofform." + f)) for f in core_roofs.FORMS if f != "custom"))  # (0.251)
        return [type_option(self.spec, "roof"),
                Option("shape", t("ctx.roof_shape"), "choice", self.shape,
                       tuple((s, t("roofshape." + s)) for s in self.shapes)),
                form,
                Option("slope", t("ctx.roof_slope"), "choice", self.slope,
                       tuple((s, "{:.0f}°".format(s)) for s in ROOF_SLOPES)),
                length_option("overhang", "ctx.overhang", self.overhang)]

    def set_option(self, key, value):
        if key == "block_form" and value in core_blocks.FORMS:
            self.block_form = value
        elif key == "form" and value in core_roofs.FORMS and value != "custom":
            self.form = value
        elif key == "slope" and value in ROOF_SLOPES:
            self.slope = float(value)
        elif key == "overhang" and value >= 0.0:
            self.overhang = float(value)
        else:
            super().set_option(key, value)
            return
        self.host.set_hint(self.hint())

    def tab(self):
        self.set_shape(self.shapes[(self.shapes.index(self.shape) + 1) % len(self.shapes)])
        self.host.message(t("info.slab_shape", shape=t("roofshape." + self.shape)))
        return True

    def hint(self):
        if self.shape == "poly" and self._points:
            return t("hint.slab.poly_next")
        if self.shape in ("rect", "blocks") and self._corner is not None:
            return t("hint.slab.end")
        if self.shape == "blocks":                         # (0.262) into which roof
            target = self.doc.ifc.by_guid(self._target) if self._target else None
            where = t("hint.roof.blocks_into", roof=target.Name or "") if target is not None else \
                t("hint.roof.blocks_new")
            return t("hint.roof.blocks", form=t("roofform." + self.block_form).lower(),
                     slope="{:.0f}°".format(self.slope),
                     o=_fmt(self.overhang), where=where)
        return t("hint.roof." + self.shape, form=t("roofform." + self.form), slope="{:.0f}°".format(self.slope),
                 o=_fmt(self.overhang))

    def cancel(self):
        """Esc: the rectangle being drawn let go — (0.262) none: the next block starts a new roof."""
        if self.shape == "blocks" and self._corner is None and self._target is not None:
            self._target = None
            self.host.message(t("info.roof_blocks_new"))
        super().cancel()

    def _add_block(self):
        """(0.262) The rectangle drawn made a block: into the roof by blocks being made, or a new one."""
        c = self._corner
        block = core_blocks.make(c[0] + self._du / 2, c[1] + self._dv / 2, 0.0, abs(self._du), abs(self._dv),
                                 self.block_form, self.slope, self.overhang)
        block = bim.fit_block_to_walls(self.doc, block)
        target = self._target if self._target and self.doc.ifc.by_guid(self._target) is not None else None
        try:
            if target is not None:
                bim.add_roof_block(self.doc, target, block)
            else:
                target = bim.add_block_roof(self.doc, block, self.spec)
        except ValueError as exc:
            from ..i18n import refusal
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self._target = target
        n = self.doc.ifc.roof_params(target)["blocks"]
        self.host.message(t("info.roof_block", n=len(n), roof=self.doc.ifc.by_guid(target).Name or "",
                            form=t("roofform." + self.block_form).lower()))

    def _face_at(self, x, y):
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None
        obj = self.doc.get(hit[0])
        if obj is not None and obj.is_bim and self.doc.ifc.kind_of(obj.id) == "roof":
            return None
        return bim.face_outline(self.doc, hit[0], hit[1], hit[2])

    def pointer_move(self, x, y, modifiers):
        if self.shape != "face":
            super().pointer_move(x, y, modifiers)
            return
        found = self._face_at(x, y)
        if found is None:
            self.viewport.clear_overlays()
            return
        ring, z = found
        pts = [np.array((px, py, z + 0.01)) for px, py in ring]
        segs = _ring_segments(pts)
        self.viewport.show_polygon(pts, segments=segs, colors=[PREVIEW] * len(segs))
        from shapely.geometry import Polygon
        self.viewport.show_label(_area(Polygon(ring).area), np.mean(pts, axis=0))

    def pointer_down(self, x, y, button, modifiers):
        if self.shape != "face" or button != LEFT:
            super().pointer_down(x, y, button, modifiers)
            return
        found = self._face_at(x, y)
        if found is None:
            self.host.message(t("err.wall_face_none"), warning=True)
            return
        ring, z = found
        self.viewport.clear_overlays()
        self._make(ring, eave=z + self.spec.thickness)       # (a floor's roof: resting on its top)

    def _make(self, outline, eave=None):
        try:
            guid = bim.add_roof(self.doc, outline, self.spec, self.form, self.slope, self.overhang, eave=eave)
        except ValueError as exc:
            from ..i18n import refusal
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return None
        p = self.doc.ifc.roof_params(guid)
        from shapely.geometry import Polygon
        self.host.message(t("info.roof", form=t("roofform." + self.form).lower(), a=_area(Polygon(outline).area),
                            slope="{:.0f}°".format(self.slope), z=_fmt(p["eave"])))
        return guid

    def _finish(self):
        if abs(self._du) < MIN_LENGTH or abs(self._dv) < MIN_LENGTH:
            return
        c = self._corner
        if self.shape == "blocks":                         # (0.262) one more block (the roof being made kept)
            self._add_block()
            SlabTool.cancel(self)
            return
        self._make([(c[0], c[1]), (c[0] + self._du, c[1]), (c[0] + self._du, c[1] + self._dv), (c[0], c[1] + self._dv)])
        self.cancel()

    def _finish_poly(self):
        outline = [(float(p[0]), float(p[1])) for p in self._points]
        if core_slabs.outline_polygon(outline) is None:
            self.host.message(t("err.slab_outline_bad"), warning=True)
            return
        self._make(outline)
        self.cancel()

    def _wand_click(self, x, y):
        p = self._level_point(x, y)
        if p is None:
            return
        region = bim.slab_wand(self.doc, p, "exterior")
        self.viewport.clear_overlays()
        if region is None:
            self.host.message(t("err.roof_wand"), warning=True)
            return
        self._make([tuple(c) for c in list(region.exterior.coords)[:-1]])


class CeilingTool(SlabTool):
    """Ceiling (0.118): its outline as the Slab's — a room's (a click inside walls: their inner faces, a column a
    hole), a rectangle or a polygon — at its height over the storey, continuous or in tiles (IfcCovering CEILING)."""

    name = "ceiling"
    keys_help = "keys.ceiling"
    shapes = ("wand", "rect", "poly")

    def __init__(self, host):
        super().__init__(host)
        self.shape = "wand"
        self.reach = "interior"
        self.style = "continuous"
        self.height = bim.CEILING_HEIGHT
        self.gap = 0.0                    # (0.119) a shadow gap along the walls
        self.bulkhead = 0.0               # …a bulkhead round the edge, this wide
        self.drop = 0.30                  # …and this much lower

    def options(self):
        from ..core import ceilings as core_ceilings
        return [Option("shape", t("ctx.roof_shape"), "choice", self.shape,
                       tuple((s, t("ceilshape." + s)) for s in self.shapes)),
                Option("style", t("ctx.ceiling_style"), "choice", self.style,
                       tuple((s, t("ceilstyle." + s)) for s in core_ceilings.STYLES)),
                length_option("height", "ctx.ceiling_height", self.height),
                length_option("gap", "ctx.ceiling_gap", self.gap),
                length_option("bulkhead", "ctx.bulkhead", self.bulkhead),
                length_option("drop", "ctx.bulkhead_drop", self.drop)]

    def set_option(self, key, value):
        if key == "style":
            self.style = value
        elif key == "height" and value > 0.5:
            self.height = float(value)
        elif key == "gap" and 0.0 <= value <= 0.20:
            self.gap = float(value)
        elif key == "bulkhead" and value >= 0.0:
            self.bulkhead = float(value)
        elif key == "drop" and value > 0.0:
            self.drop = float(value)
        else:
            super().set_option(key, value)
            return
        self.host.set_hint(self.hint())

    def tab(self):
        self.set_shape(self.shapes[(self.shapes.index(self.shape) + 1) % len(self.shapes)])
        self.host.message(t("info.slab_shape", shape=t("ceilshape." + self.shape)))
        return True

    def hint(self):
        if self.shape == "poly" and self._points:
            return t("hint.slab.poly_next")
        if self.shape == "rect" and self._corner is not None:
            return t("hint.slab.end")
        return t("hint.ceiling." + self.shape, style=t("ceilstyle." + self.style).lower(), h=_fmt(self.height))

    def _make(self, outline, holes=()):
        try:
            guid = bim.add_ceiling(self.doc, outline, self.height, self.style, holes, gap=self.gap,
                                   bulkhead=(self.bulkhead, self.drop) if self.bulkhead > 0 else None)
        except ValueError as exc:
            from ..i18n import refusal
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return None
        from shapely.geometry import Polygon
        self.host.message(t("info.ceiling", a=_area(Polygon(outline).area), style=t("ceilstyle." + self.style).lower(),
                            h=_fmt(self.height)))
        return guid

    def _finish(self):
        if abs(self._du) < MIN_LENGTH or abs(self._dv) < MIN_LENGTH:
            return
        c = self._corner
        self._make([(c[0], c[1]), (c[0] + self._du, c[1]), (c[0] + self._du, c[1] + self._dv), (c[0], c[1] + self._dv)])
        self.cancel()

    def _finish_poly(self):
        outline = [(float(p[0]), float(p[1])) for p in self._points]
        if core_slabs.outline_polygon(outline) is None:
            self.host.message(t("err.slab_outline_bad"), warning=True)
            return
        self._make(outline)
        self.cancel()

    def _wand_click(self, x, y):
        p = self._level_point(x, y)
        if p is None:
            return
        region = bim.slab_wand(self.doc, p, "interior")
        self.viewport.clear_overlays()
        if region is None:
            self.host.message(t("err.slab_wand_open"), warning=True)
            return
        self._make([tuple(c) for c in list(region.exterior.coords)[:-1]],
                   [[tuple(c) for c in list(h.coords)[:-1]] for h in region.interiors])


class FlooringTool(CeilingTool):
    """(0.374, the study's «Piso», the addon's floor finishes) A floor finish — ceramic, wood, stone, vinyl, polished
    concrete — over a room (a click inside walls), a rectangle or a polygon, laid on the storey's level (IfcCovering
    FLOORING, with its thickness and material in the quantities)."""

    name = "flooring"
    keys_help = "keys.ceiling"

    def __init__(self, host):
        super().__init__(host)
        self.finish = "ceramico"

    def options(self):
        from ..ifc.coverings import FLOORINGS
        return [Option("shape", t("ctx.roof_shape"), "choice", self.shape,
                       tuple((s, t("ceilshape." + s)) for s in self.shapes)),
                Option("finish", t("ctx.flooring"), "choice", self.finish,
                       tuple((k, t("flooring." + k)) for k in FLOORINGS))]

    def set_option(self, key, value):
        if key == "finish":
            self.finish = value
            self.host.set_hint(self.hint())
            return
        super().set_option(key, value)

    def hint(self):
        if self.shape == "poly" and self._points:
            return t("hint.slab.poly_next")
        if self.shape == "rect" and self._corner is not None:
            return t("hint.slab.end")
        return t("hint.flooring." + self.shape, f=t("flooring." + self.finish).lower())

    def _make(self, outline, holes=()):
        try:
            guid = bim.add_flooring(self.doc, outline, self.finish, holes)
        except ValueError as exc:
            from ..i18n import refusal
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return None
        from shapely.geometry import Polygon
        self.host.message(t("info.flooring", a=_area(Polygon(outline).area), f=t("flooring." + self.finish).lower()))
        return guid

    def _wand_click(self, x, y):
        """A room's floor: inside its walls, columns and room separators (a room's own, not the slab's outline)."""
        p = self._level_point(x, y)
        if p is None:
            return
        region = self.doc.ifc.room_region(self.doc.active_storey, (float(p[0]), float(p[1])))
        self.viewport.clear_overlays()
        if region is None:
            self.host.message(t("err.slab_wand_open"), warning=True)
            return
        self._make([tuple(c) for c in list(region.exterior.coords)[:-1]],
                   [[tuple(c) for c in list(h.coords)[:-1]] for h in region.interiors])


class SlabOutlineTool(_PointTool):
    """Editar contorno (0.100): the corners of a slab as grips (see the module's docstring). (0.382, as the wall's
    profile in 0.381) A grip moves only while the button is held — dragged and let go; a distance can be typed
    meanwhile (Enter). A click (no drag) on a corner chooses it, for Delete; it no longer picks it up to follow the
    mouse until the next click (a click more, where the mouse was, picked it up again)."""

    name = "slab_outline"
    title = "tool.slab_outline"
    placement = True                    # (Esc: back to Select)
    on_storey = False
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.slab_outline"

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.guid = None
        self._ring = []                 # the slab's corners [(x, y)]
        self._z = 0.0                   # its top: where the grips are
        self._picked = None             # the index of the corner picked up (while the button is held)
        self._end = None
        self._press = None              # (0.382) where it was pressed
        self._chosen = None             # (0.382) the corner clicked (not dragged): what Delete takes away
        host.doc.subscribe(self._changed)

    def edit(self, guid):
        """Start editing this slab's outline."""
        self.guid = guid
        self.host.set_tool(self.name)

    def activate(self):
        super().activate()
        self._load()

    def _drop(self):
        """Nothing picked up, pressed or chosen."""
        self._picked = self._end = self._press = self._chosen = None

    def deactivate(self):
        self._drop()
        self.viewport.show_grips()
        self.viewport.clear_overlays()

    def _changed(self, changed, removed):
        if self.host.tool is self:      # (undone / redone, or changed elsewhere: the grips follow)
            self._drop()
            self._load()

    def _load(self):
        info = self.doc.ifc.slab_outline(self.guid) if self.guid and not self.doc.loading else None
        if info is None or info["shape"] == "circulo":
            self._ring = []
            self.viewport.show_grips()
            self.viewport.clear_overlays()
            self.host.set_hint(t("hint.slab_outline_none"))
            return
        self._ring = [(float(x), float(y)) for x, y in info["outline"]]
        self._z = info["top"]
        self.viewport.clear_overlays()                # (the preview, its dimensions: gone)
        self.viewport.show_alignments()
        self._show()

    def _world(self, ring):
        return [np.array((x, y, self._z)) for x, y in ring]

    def _show(self, ring=None):
        ring = self._ring if ring is None else ring
        pts = self._world(ring)
        mids = [(a + b) / 2 for a, b in zip(pts, pts[1:] + pts[:1])]
        self.viewport.show_grips(pts, mids)
        segs = _ring_segments(pts)
        if ring is self._ring:
            self.viewport.show_lines(segs, [PREVIEW] * len(segs))
        else:
            self.viewport.show_polygon(pts, segments=segs, colors=[PREVIEW] * len(segs))
        self.host.set_hint(self.hint())

    def hint(self):
        if not self._ring:
            return t("hint.slab_outline_none")
        return t("hint.slab_outline_move") if self._picked is not None else t("hint.slab_outline")

    def vcb_title(self):
        return t("vcb.length")

    def pointer_move(self, x, y, modifiers):
        if not self._ring:
            return
        if self._picked is None:
            grip = self.viewport.grip_at(x, y)
            if grip is None:
                self.viewport.show_tip("", None)
            else:
                kind, k = grip
                pts = self._world(self._ring)
                at = pts[k] if kind == "end" else (pts[k] + pts[(k + 1) % len(pts)]) / 2
                self.viewport.show_tip(t("tip.slab_corner" if kind == "end" else "tip.slab_add_corner"), at)
            return
        origin = self._world([self._ring[self._picked]])[0]
        p, snap = self._point(x, y, self._z, origin, modifiers)
        if p is None:
            return
        self._end = p
        ring = list(self._ring)
        ring[self._picked] = (float(p[0]), float(p[1]))
        self._show(ring)
        drawing_dims(self.viewport, origin, np.array((p[0], p[1], self._z)))
        show_snap(self.viewport, snap, p)
        self.host.set_vcb(_fmt(float(np.linalg.norm((p - origin)[:2]))))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._picked is not None:             # the corner put back where it was
                self.cancel()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT or not self._ring:
            return
        if self._picked is not None:
            if self._end is not None:
                ring = list(self._ring)
                ring[self._picked] = (float(self._end[0]), float(self._end[1]))
                self._apply(ring, t("info.slab_corner_moved"))
            return
        grip = self.viewport.grip_at(x, y)
        if grip is None:
            self._chosen = None                      # (a click beside the grips: none chosen)
            return
        kind, k = grip
        self._chosen = None
        self._press = (float(x), float(y), kind)     # (0.382: let go elsewhere — a drag — it is put down there)
        if kind == "middle":                         # a corner added in the middle of that side, picked up
            a, b = self._ring[k], self._ring[(k + 1) % len(self._ring)]
            self._ring.insert(k + 1, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
            k += 1
        self._picked = k
        self._end = None
        self._show()

    def pointer_up(self, x, y, button, modifiers):
        """(0.382) Dragged and let go: the corner put down there. Pressed and let go in place — a click —: nothing
        moves (a corner added in a side's middle goes away again); a corner clicked is chosen, for Delete."""
        press, self._press = self._press, None
        if button != LEFT or press is None or self._picked is None:
            return
        if moved_enough(press[:2], (x, y)):
            if self._end is not None:
                ring = list(self._ring)
                ring[self._picked] = (float(self._end[0]), float(self._end[1]))
                self._apply(ring, t("info.slab_corner_moved"))
            return
        chosen = self._picked if press[2] == "end" else None
        self.cancel()
        self._chosen = chosen
        if chosen is not None:
            self.viewport.show_tip(t("tip.slab_corner_chosen"), self._world([self._ring[chosen]])[0])

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None or values[0] is None or self._picked is None or self._end is None:
            if values is None:
                self.host.message(t("err.bad_value", t=text), warning=True)
            return
        x0, y0 = self._ring[self._picked]
        d = np.array((self._end[0] - x0, self._end[1] - y0))
        if np.linalg.norm(d) < 1e-9:
            return
        d = d / np.linalg.norm(d) * values[0]
        ring = list(self._ring)
        ring[self._picked] = (x0 + float(d[0]), y0 + float(d[1]))
        self._apply(ring, t("info.slab_corner_moved"))

    def delete(self):
        """Delete: the corner picked up — (0.382) or clicked — taken away (a slab keeps three at least)."""
        target = self._picked if self._picked is not None else self._chosen
        if target is None:
            self.host.message(t("info.slab_corner_pick_first"), warning=True)
            return
        if len(self._ring) <= 3:
            self.host.message(t("err.slab_three_corners"), warning=True)
            return
        ring = [p for k, p in enumerate(self._ring) if k != target]
        self._apply(ring, t("info.slab_corner_deleted"))

    def _apply(self, ring, text):
        self._drop()
        if core_slabs.outline_polygon(ring) is None:
            self.host.message(t("err.slab_outline_bad"), warning=True)
            self._load()
            return
        try:
            bim.set_slab_outline(self.doc, self.guid, ring)
        except ValueError as exc:
            from ..i18n import refusal
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self._load()
            return
        info = self.doc.ifc.slab_outline(self.guid)
        self.host.message("{} {}".format(text, t("info.slab_area", a=_area(info["area"]) if info else "")))

    def cancel(self):
        """A corner picked up goes back — a corner just added in a side's middle goes away (Ctrl+Z also passes
        here)."""
        self._drop()
        self.viewport.clear_overlays()
        self._load()
