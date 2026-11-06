"""(0.423) Lot: the lot's outline in plan, as Revit's property line — a rectangle (two corners, or its size typed
"20;30"), a polygon (its corners one by one; a click on the first, or Enter, closes it; Delete takes the last back),
or the terrain's outline (a click). One lot per project: drawn again, it replaces the one there. Its sides facing the
street are chosen in the Project regulations (none chosen: the side nearest the entrance)."""

import numpy as np

from ..core import lot as core_lot
from ..i18n import decimal_sep, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option
from .bim_draw import MIN_LENGTH
from .slab import SlabTool, _ring_segments

SHAPES = ("rect", "poly", "terrain")


def area_text(a):
    return "{:.2f} m²".format(a).replace(".", decimal_sep())


class LotTool(SlabTool):
    name = "lot"
    shapes = SHAPES

    def __init__(self, host):
        super().__init__(host)
        self.shape = "rect"

    def options(self):
        return [Option("shape", t("ctx.lot_shape"), "choice", self.shape,
                       tuple((s, t("lotshape." + s)) for s in SHAPES))]

    def set_option(self, key, value):
        if key == "shape" and value in SHAPES:
            self.set_shape(value)
        self.host.set_hint(self.hint())

    def tab(self):
        self.set_shape(SHAPES[(SHAPES.index(self.shape) + 1) % len(SHAPES)])
        self.host.message(t("info.lot_shape", shape=t("lotshape." + self.shape)))
        return True

    def hint(self):
        if self.shape == "terrain":
            return t("hint.lot.terrain") if bim.lot_from_terrain(self.doc) is not None else t("hint.lot.no_terrain")
        if self.shape == "poly":
            return t("hint.lot.poly_next") if self._points else t("hint.lot.poly_start")
        return t("hint.lot.end") if self._corner is not None else t("hint.lot.start")

    # ------------------------------------------------------------ the terrain's outline

    def pointer_move(self, x, y, modifiers):
        if self.shape != "terrain":
            super().pointer_move(x, y, modifiers)
            return
        outline = bim.lot_from_terrain(self.doc)
        if outline is None:
            return
        z = self.doc.work_level() + 0.01
        ring = [np.array((px, py, z)) for px, py in outline]
        segs = _ring_segments(ring)
        self.viewport.show_polygon(ring, segments=segs, colors=[PREVIEW] * len(segs))
        self.viewport.show_label(area_text(core_lot.area(outline)), np.mean(ring, axis=0))

    def pointer_down(self, x, y, button, modifiers):
        if self.shape != "terrain" or button == RIGHT:
            super().pointer_down(x, y, button, modifiers)
            return
        if button != LEFT:
            return
        outline = bim.lot_from_terrain(self.doc)
        if outline is None:
            self.host.message(t("hint.lot.no_terrain"), warning=True)
            return
        self._make(outline)

    def typed(self, text):
        if self.shape != "terrain":
            super().typed(text)

    # ------------------------------------------------------------ made

    def _finish(self):
        if abs(self._du) < MIN_LENGTH or abs(self._dv) < MIN_LENGTH:
            return
        x, y = float(self._corner[0]), float(self._corner[1])
        self._make([(x, y), (x + self._du, y), (x + self._du, y + self._dv), (x, y + self._dv)])

    def _finish_poly(self):
        self._make([(float(p[0]), float(p[1])) for p in self._points])

    def _finish_circle(self, radius):
        return

    def _make(self, outline):
        if core_lot.ring(outline) is None or core_lot.area(outline) < MIN_LENGTH:
            self.host.message(t("err.lot_bad"), warning=True)
            return
        bim.set_lot(self.doc, outline)
        lot = self.doc.ifc.lot()
        self.host.message(t("info.lot", a=area_text(lot["area"]), n=len(lot["outline"])))
        self.cancel()
