"""Section tool (Phase 3, step 2): draw the section line on the storey with two clicks
(inferences work as for walls), then click on the side to look at — as in ArchiCAD. The
view becomes that section: everything on the near side is taken away, what the plane cuts
is filled dark, all storeys are shown. F8 (or another view) goes back to 3D; View ▸ Last
section (F5) comes back to it."""

import numpy as np

from ..core.units import format_length
from ..i18n import decimal_sep, t
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, show_snap
from .bim_draw import MIN_LENGTH, _PointTool

ARROW = 1.0          # m: the section's arrows, pointing to where it looks


class SectionTool(_PointTool):
    name = "section"
    accepts_typing = False

    def __init__(self, host):
        super().__init__(host)
        self._a = self._b = None

    def hint(self):
        if self._a is None:
            return t("hint.section.start")
        return t("hint.section.end") if self._b is None else t("hint.section.side")

    def _side(self, p):
        """Unit normal of the line, towards the side of p (where the section looks)."""
        d = self._b - self._a
        n = np.array((-d[1], d[0], 0.0)) / np.linalg.norm(d[:2])
        return n if float((p - self._a) @ n) >= 0 else -n

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, self.doc.work_level())
        if p is None:
            return
        self._hover = (p, snap)
        if self._a is None:
            show_snap(self.viewport, snap, p)
            return
        if self._b is None:
            self.viewport.show_lines([self._a, p], [PREVIEW, PREVIEW])
            self.viewport.show_label(format_length(float(np.linalg.norm(p - self._a)), decimal_sep()), p)
            show_snap(self.viewport, snap, p)
            return
        n = self._side(p)
        segs = [self._a, self._b]
        for end in (self._a, self._b):                   # an arrow at each end, as on a drawn section
            tip = end + n * ARROW
            back = n * ARROW * 0.35
            along = (self._b - self._a) / np.linalg.norm(self._b - self._a) * ARROW * 0.2
            segs += [end, tip, tip, tip - back + along, tip, tip - back - along]
        self.viewport.show_lines(segs, [PREVIEW] * len(segs))
        self.viewport.show_label(t("label.section_looks"), (self._a + self._b) / 2 + n * ARROW)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        p, _snap = self._point(x, y, self.doc.work_level())
        if p is None:
            return
        if self._a is None:
            self._a = p
        elif self._b is None:
            if np.linalg.norm((p - self._a)[:2]) < MIN_LENGTH:
                return
            self._b = p
        else:
            a, b, n = self._a, self._b, self._side(p)
            self.cancel()
            self.host.show_section(a, b, n)
            return
        self.host.set_hint(self.hint())

    def cancel(self):
        self._a = self._b = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
