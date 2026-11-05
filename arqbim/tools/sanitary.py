"""Sanitary fixture (0.140, Phase 6, step 3): a WC, a washbasin, a bidet, a shower tray, a bath, a kitchen sink
(IfcSanitaryTerminal) with its connections (drain, cold and hot water) and the free zone in front of it. Over a
wall's face the fixture is put with its back against it, facing the room, where the mouse is along it; away from
walls, at the point, turned with R."""

import math

import numpy as np

from ..i18n import t
from ..ifc.sanitary import FIXTURES, free_zone, outline
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, show_snap
from .bim_draw import ANGLES, _PointTool

ZONE = (0.20, 0.55, 0.30, 1.0)        # the free zone's colour while placing


class SanitaryTool(_PointTool):
    name = "fixture"
    placement = True
    accepts_typing = False
    common_keys = frozenset(("r", "shift+r"))
    keys_help = "keys.fixture"

    def __init__(self, host):
        super().__init__(host)
        self.kind = "wc"
        self.angle = 0
        self._frames = {}

    def options(self):
        return [Option("kind", t("ctx.fixture"), "choice", self.kind, tuple((k, t("fixture." + k)) for k in FIXTURES)),
                Option("angle", t("ctx.angle"), "choice", self.angle, tuple((a, "{}°".format(a)) for a in ANGLES))]

    def set_option(self, key, value):
        if key == "kind" and value in FIXTURES:
            self.kind = value
        elif key == "angle":
            self.angle = int(value)
        self._again()

    def common_key(self, name):
        self.angle = (self.angle + (90 if name == "r" else -90)) % 360
        self.host.message(t("info.turned", a=self.angle))
        self._again()
        return True

    def _again(self):
        self.host.set_hint(self.hint())
        if self._hover is not None:
            self._show(*self._hover)

    def hint(self):
        return t("hint.fixture", k=t("fixture." + self.kind).lower())

    def _width(self):
        """Its width along the wall (it stays on the wall)."""
        return FIXTURES[self.kind][1][0]

    def _wall_frame(self, wall):
        obj = self.doc.get(wall)
        cached = self._frames.get(wall)
        if cached is None or cached[0] != id(obj.mesh):
            cached = (id(obj.mesh), bim.wall_frame(self.doc, wall))
            self._frames[wall] = cached
        return cached[1]

    def _place(self, x, y, modifiers):
        """(the middle of its back (3,), its angle, the wall it is against or None, the snap) under the mouse."""
        level = self.doc.work_level()
        hit = self.viewport.pick_point(x, y)
        if hit is not None:
            obj = self.doc.get(hit[0])
            try:
                wall = obj is not None and obj.is_bim and self.doc.ifc.kind_of(obj.id) == "wall"
            except RuntimeError:
                wall = False
            frame = self._wall_frame(obj.id) if wall else None
            if frame is not None:
                local = frame.to_local(np.asarray(hit[2], dtype=float))
                side = frame.face_side(obj.mesh.face_normal(hit[1]))
                if side == 0:
                    side = -1 if local[1] < (frame.y0 + frame.y1) / 2 else 1
                width = self._width()
                lo, hi = frame.x0 + width / 2, frame.x0 + frame.length - width / 2
                along = min(max(round(float(local[0]), 2), lo), hi) if hi >= lo else frame.x0 + frame.length / 2
                back = frame.to_world((along, frame.y1 if side > 0 else frame.y0, 0.0))
                back[2] = level
                out = frame.matrix[:3, 1] / np.linalg.norm(frame.matrix[:3, 1]) * side
                x_dir = np.cross(out, (0.0, 0.0, 1.0))
                return back, math.degrees(math.atan2(x_dir[1], x_dir[0])), obj.id, None
        p, snap = self._point(x, y, level, modifiers=modifiers)
        return (None if p is None else np.array((p[0], p[1], level))), float(self.angle), None, snap

    def _show(self, x, y, modifiers):
        back, angle, _wall, snap = self._place(x, y, modifiers)
        if back is None:
            return
        foot = outline(back, angle, self.kind)
        zone = free_zone(back, angle, self.kind)
        segs = [q for a, b in zip(foot, foot[1:] + foot[:1]) for q in (a, b)]
        zsegs = [q for a, b in zip(zone, zone[1:] + zone[:1]) for q in (a, b)]
        self.viewport.show_polygon(foot, segments=segs + zsegs, colors=[PREVIEW] * len(segs) + [ZONE] * len(zsegs))
        show_snap(self.viewport, snap, back)

    def pointer_move(self, x, y, modifiers):
        self._hover = (x, y, modifiers)
        self._show(x, y, modifiers)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        back, angle, wall, _snap = self._place(x, y, modifiers)
        if back is None:
            return
        bim.add_fixture(self.doc, back, self.kind, angle)
        self.viewport.clear_overlays()
        self.host.message(t("info.fixture_wall" if wall else "info.fixture", k=t("fixture." + self.kind)))

    def cancel(self):
        self.viewport.clear_overlays()
