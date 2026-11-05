"""Detail view (0.133, Phase 5 step 8): in a plan or a section, two opposite corners of the piece to show bigger
— a detail view of it ("Pormenor 1") at its own scale (1:20 by default), for the sheets; the view keeps its
callout (a dashed rectangle and its number). The inferences work, as for a dimension."""

import numpy as np

from ..core.sketch_geometry import ray_plane
from ..i18n import t
from ..model import annotations as notes2d
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, SNAPPABLE, Option, show_snap
from .bim_draw import _PointTool

SCALES = (5, 10, 20, 50)


class DetailTool(_PointTool):
    name = "detail"
    accepts_typing = False
    keys_help = "keys.detail"

    def __init__(self, host):
        super().__init__(host)
        self.scale = 20
        self._first = None

    def options(self):
        return [Option("scale", t("ctx.detail_scale"), "choice", self.scale,
                       tuple((s, "1:{}".format(s)) for s in SCALES))]

    def set_option(self, key, value):
        if key == "scale" and int(value) in SCALES:
            self.scale = int(value)
        self.host.set_hint(self.hint())

    def hint(self):
        view = self.viewport.current_view()
        if view is None or view[0] not in ("plan", "section", "elevation"):
            return t("hint.detail_view")
        return t("hint.detail_2" if self._first is not None else "hint.detail", s=self.scale)

    def _pick(self, x, y):
        plane = self.viewport.view_plane()
        if plane is None:
            return None, None
        snap, _hit = self.viewport.snap(x, y)
        if snap is not None and snap.kind in SNAPPABLE:
            return snap.point.copy(), snap
        origin, _u, _v, n = plane
        ray_o, ray_d = self.viewport.ray(x, y)
        p = ray_plane(ray_o, ray_d, origin, n)
        return (p if p is not None else ray_plane(ray_o, ray_d, origin, -n)), None

    def pointer_move(self, x, y, modifiers):
        p, snap = self._pick(x, y)
        if p is None:
            return
        show_snap(self.viewport, snap, p)
        if self._first is None:
            return
        origin, u, v, _n = self.viewport.view_plane()
        (x0, y0), (x1, y1) = notes2d.to2([self._first, p], origin, u, v)
        ring = [origin + u * a + v * b for a, b in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        segs = [q for a, b in zip(ring, ring[1:] + ring[:1]) for q in (a, b)]
        self.viewport.show_lines(segs, [PREVIEW] * len(segs))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._first is not None:
                self.cancel()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT:
            return
        view = self.viewport.current_view()
        p, _snap = self._pick(x, y)
        if p is None or view is None or view[0] not in ("plan", "section", "elevation"):
            self.host.message(t("hint.detail_view"))
            return
        if self._first is None:
            self._first = p
            self.host.set_hint(self.hint())
            return
        origin, u, v, _n = self.viewport.view_plane()
        (x0, y0), (x1, y1) = notes2d.to2([self._first, p], origin, u, v)
        if abs(x1 - x0) < 0.1 or abs(y1 - y0) < 0.1:
            return
        index = self.doc.add_detail(view, (x0, y0, x1, y1), self.scale)
        self.host.message(t("info.detail", name=self.doc.details[index].name, s=self.scale))
        self.cancel()

    def cancel(self):
        self._first = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
