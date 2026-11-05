"""Terrain from points (0.155, Phase 7, step 3 — as Revit's toposurface by placing points): the height typed
("12,50", Enter), then clicks where the points at that height are (snaps: a wall's corner, a guide); another
height typed changes the last point's and the next ones'. Enter makes the terrain through them (at least three,
not in a line). With a terrain selected, the points are added to it and Enter makes it again."""

import numpy as np

from ..core.units import format_length, parse_length
from ..i18n import decimal_sep, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Tool, infer_point, show_snap

TERRAIN_CLASS = "IfcGeographicElement"
MARK = 0.25                   # m: half a point's cross


class TerrainTool(Tool):
    name = "terrain"
    accepts_typing = True
    on_storey = True

    def __init__(self, host):
        super().__init__(host)
        self._points = []
        self._z = None
        self._target = None       # the terrain the points are added to (selected when the tool started), or None

    def activate(self):
        sel = [self.doc.get(i) for i in self.viewport.selection]
        terrains = [o for o in sel if o is not None and o.is_bim and o.ifc_class == TERRAIN_CLASS]
        self._target = terrains[0].id if len(terrains) == 1 else None
        super().activate()

    def _height(self):
        return self._z if self._z is not None else float(self.doc.work_level())

    def hint(self):
        if not self._points:
            if self._target is not None and self.doc.get(self._target) is not None:
                return t("hint.terrain.add", name=self.doc.get(self._target).name)
            return t("hint.terrain.first")
        return t("hint.terrain.more", n=len(self._points), z=format_length(self._height(), decimal_sep()))

    def vcb_title(self):
        return t("vcb.height_point")

    def _plan_point(self, x, y, modifiers):
        found, snap, _hit = infer_point(self.viewport, x, y, None, modifiers)
        if found is not None:
            return found.point.copy(), snap
        origin, direction = self.viewport.ray(x, y)
        if abs(direction[2]) < 1e-9:
            return None, None
        level = float(self.doc.work_level())
        s = (level - origin[2]) / direction[2]
        return (origin + direction * s, None) if s > 0 else (None, None)

    def _preview(self, extra=None):
        segs = []
        for p in self._points + ([extra] if extra is not None else []):
            p = np.asarray(p, dtype=float)
            for d in ((MARK, 0.0, 0.0), (0.0, MARK, 0.0)):
                segs += [p - d, p + d]
        if len(self._points) > 1:                           # (the order they were given in, faintly)
            for a, b in zip(self._points, self._points[1:]):
                segs += [np.asarray(a, float), np.asarray(b, float)]
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))

    def pointer_move(self, x, y, modifiers):
        p, snap = self._plan_point(x, y, modifiers)
        if p is None:
            return
        show_snap(self.viewport, snap, p)
        self._preview(np.array((p[0], p[1], self._height())))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        p, _snap = self._plan_point(x, y, modifiers)
        if p is None:
            return
        self._points.append((float(p[0]), float(p[1]), self._height()))
        self._preview()
        self.host.set_hint(self.hint())

    def typed(self, text):
        z = parse_length(text)
        if z is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        self._z = float(z)
        if self._points:                                    # (the last point's too)
            x, y, _z = self._points[-1]
            self._points[-1] = (x, y, self._z)
        self._preview()
        self.host.set_hint(self.hint())

    def enter(self):
        self.finish()

    def finish(self):
        """The terrain through the points (or the selected one made again with them). Returns its GlobalId."""
        if not self._points:
            return None
        points = list(self._points)
        target = self._target if self._target is not None and self.doc.get(self._target) is not None else None
        try:
            if target is not None:
                every = np.vstack((self.doc.ifc.terrain_survey(target), np.array(points)))     # (its survey: 0.157)
                bim.set_terrain_points(self.doc, target, every)
                guid = target
            else:
                guid = bim.add_terrain(self.doc, points)
        except ValueError:
            self.host.message(t("err.terrain_few"), warning=True)
            return None
        info = self.doc.ifc.terrain_info(guid)
        self.host.message(t("info.terrain_made", n=info["points"], lo=format_length(info["low"], decimal_sep()),
                            hi=format_length(info["high"], decimal_sep()),
                            i=format_length(info["interval"], decimal_sep())))
        self._points = []
        self._target = guid
        self.viewport.clear_overlays()
        self.viewport.set_selection({guid})
        self.host.set_hint(self.hint())
        return guid

    def cancel(self):
        self._points = []
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
