"""Kitchen (0.170, Phase 10, step 1): a run of modules along the walls — straight, in L, in U. Click where it starts
on a wall's inner face, then at each corner, then where it ends; Enter (or a right click) makes it: each leg filled
with base units of 60 cm (the rest in a smaller usual width), the wall units over them, the worktop over the base
units, in one undo step. The room is on the side of the face first clicked (F turns it round); the modules are
shown as they will be while the mouse moves. (0.239, 0.240) Its inside corners: blind units, or L units (a
carousel in the base one), as chosen in its bar."""

import math

import numpy as np

from ..core import cabinets as core_cab
from ..core import kitchens
from ..i18n import t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, show_snap
from .bim_draw import _PointTool


class KitchenTool(_PointTool):
    name = "kitchen"
    common_keys = frozenset(("f",))
    keys_help = "keys.kitchen"

    def __init__(self, host):
        super().__init__(host)
        self.wall_units = True
        self.worktop = True
        self.fronts = "doors"
        self.corner = "blind"               # (0.240) its inside corners' units: kitchens.CORNERS
        self.finish = "melamine"            # (0.243) its fronts' finish (core.cabinets.FINISHES)
        self._points = []
        self._out = None                    # the way into the room, from the face first clicked
        self._flip = False
        self._frames = {}

    def options(self):
        yes_no = ((True, t("opt.yes")), (False, t("opt.no")))
        return [Option("wall_units", t("ctx.wall_units"), "choice", self.wall_units, yes_no),
                Option("worktop", t("ctx.worktop"), "choice", self.worktop, yes_no),
                Option("fronts", t("ctx.fronts"), "choice", self.fronts,
                       tuple((k, t("cabinet.fronts." + k)) for k in ("doors", "drawers", "door_drawer"))),
                Option("corner", t("ctx.corner"), "choice", self.corner,
                       tuple((k, t("kitchen.corner." + k)) for k in kitchens.CORNERS)),
                Option("finish", t("ctx.finish"), "choice", self.finish,
                       tuple((k, t("cabinet.finish." + k)) for k in core_cab.FINISHES))]

    def set_option(self, key, value):
        if key in ("wall_units", "worktop"):
            setattr(self, key, bool(value))
        elif key in ("fronts", "corner", "finish"):
            setattr(self, key, value)
        self._again()

    def common_key(self, name):
        self._flip = not self._flip
        self.host.message(t("info.kitchen_flipped"))
        self._again()
        return True

    def hint(self):
        return t("hint.kitchen_first" if not self._points else "hint.kitchen_next")

    def _again(self):
        self.host.set_hint(self.hint())
        if self._hover is not None:
            self._show(*self._hover)

    def _wall_out(self, x, y):
        """(the point on a wall's face under the mouse, the way into the room from it) — or (None, None)."""
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None, None
        obj = self.doc.get(hit[0])
        try:
            wall = obj is not None and obj.is_bim and self.doc.ifc.kind_of(obj.id) == "wall"
        except RuntimeError:
            wall = False
        if not wall:
            return None, None
        cached = self._frames.get(obj.id)
        if cached is None or cached[0] != id(obj.mesh):
            cached = (id(obj.mesh), bim.wall_frame(self.doc, obj.id))
            self._frames[obj.id] = cached
        frame = cached[1]
        if frame is None:
            return None, None
        local = frame.to_local(np.asarray(hit[2], dtype=float))
        side = frame.face_side(obj.mesh.face_normal(hit[1]))
        if side == 0:
            side = -1 if local[1] < (frame.y0 + frame.y1) / 2 else 1
        on_face = frame.to_world((round(float(local[0]), 2), frame.y1 if side > 0 else frame.y0, 0.0))
        out = frame.matrix[:3, 1] / np.linalg.norm(frame.matrix[:3, 1]) * side
        return on_face, out

    def _at(self, x, y, modifiers):
        level = self.doc.work_level()
        face, out = self._wall_out(x, y)
        if face is not None:
            p = np.array((face[0], face[1], level))
            if self._points:                          # (along the leg or square to it, as drawn on the faces)
                p = self._squared(p)
            return p, out, None
        p, snap = self._point(x, y, level, modifiers=modifiers)
        if p is None:
            return None, None, snap
        p = np.array((p[0], p[1], level))
        return (self._squared(p) if self._points else p), None, snap

    def _squared(self, p):
        """The point put square to the last one (along X or Y of the leg before), as kitchens are."""
        last = self._points[-1]
        d = p - last
        if abs(d[0]) >= abs(d[1]):
            return np.array((p[0], last[1], p[2]))
        return np.array((last[0], p[1], p[2]))

    def _side(self, points):
        if len(points) < 2:
            return 1
        side = 1
        if self._out is not None:
            d = np.asarray(points[1], dtype=float) - np.asarray(points[0], dtype=float)
            side = 1 if float(d[0] * self._out[1] - d[1] * self._out[0]) > 0 else -1
        return -side if self._flip else side

    def _show(self, x, y, modifiers):
        p, _out, snap = self._at(x, y, modifiers)
        if p is None:
            return
        pts = self._points + [p]
        segs = [q for a, b in zip(pts, pts[1:]) for q in (a, b)]
        colors = [PREVIEW] * len(segs)
        if len(pts) >= 2:
            side = self._side(pts)
            from ..core import cabinets as core_cab
            depth = core_cab.Cabinet.of("base").overall_depth
            z = float(p[2])
            for mid, angle, width, _blind, corner_side, arm in kitchens.run_modules(
                    [q[:2] for q in pts], side, corners=self.corner):          # (0.239, 0.240: as it will be made)
                rects = [kitchens.footprint(mid, angle, width, depth)]
                if arm:
                    rects.append(kitchens.arm_footprint(mid, angle, width, depth, arm, corner_side))
                for rect in rects:
                    foot = [np.array((c[0], c[1], z)) for c in rect]
                    segs += [q for a, b in zip(foot, foot[1:] + foot[:1]) for q in (a, b)]
            colors = [PREVIEW] * len(segs)
        self.viewport.show_polygon([], segments=segs, colors=colors)
        show_snap(self.viewport, snap, p)

    def pointer_move(self, x, y, modifiers):
        self._hover = (x, y, modifiers)
        self._show(x, y, modifiers)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if len(self._points) >= 2:
                self._make()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT:
            return
        p, out, _snap = self._at(x, y, modifiers)
        if p is None:
            return
        if not self._points:
            self._out = out
        if self._points and np.linalg.norm((p - self._points[-1])[:2]) < 0.30:
            return                                    # (the same point again)
        self._points.append(p)
        self.host.set_hint(self.hint())

    def enter(self):
        if len(self._points) >= 2:
            self._make()

    def _make(self):
        side = self._side(self._points)
        made = bim.make_kitchen(self.doc, [q[:2] for q in self._points], side, self.wall_units, self.worktop,
                                self.fronts, corner=self.corner, finish=self.finish)
        self.viewport.clear_overlays()
        self._points, self._out, self._flip = [], None, False
        if made:
            self.host.message(t("info.kitchen", b=len(made["base"]), w=len(made["wall"]),
                                m=t("info.kitchen_worktop") if made["worktop"] else ""))
        self.host.set_hint(self.hint())

    def cancel(self):
        self._points, self._out, self._flip = [], None, False
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
