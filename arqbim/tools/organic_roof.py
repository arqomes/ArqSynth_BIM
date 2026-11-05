"""Organic roof (0.390), the ArqSynth Modeler's «Cobertura orgânica»: its outline drawn on the active storey's floor
— a curve through the points clicked («Curvo»: smooth, the organic one), a polygon, a rectangle (two corners) or a
circle (its centre, then a point on it) —, the roof over it at the eave's height: its form found from the outline
(dome, vault, wave), as a shell, a gridshell, a glazed gridshell or a curved pergola, with a ring beam and supports
(model/bim.add_organic_roof). The roof shows as it will be while the outline is drawn; a click on the first point
(or Enter) closes it; Backspace takes the last point back."""

import math

import numpy as np

from ..core import organic_roof as core_or
from ..core.units import format_length
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, Tool, infer_point, level_plane, show_snap
from .bim_draw import length_option

MODES = ("curvo", "poligono", "retangulo", "circulo")
CLOSE_PX = 12                       # px: a click this near the first point closes the outline
PREVIEW_PIECES = 14                 # the preview's grid: about this many cells across (light enough to follow the mouse)


def _fmt(v):
    return format_length(v, decimal_sep())


class OrganicRoofTool(Tool):
    name = "organic_roof"
    on_storey = True
    placement = True
    keys_help = "keys.organic_roof"

    def __init__(self, host):
        super().__init__(host)
        self.mode = "curvo"
        self.form, self.system = "cupula", "gridshell"
        self.eave = 3.0                       # m above the storey's floor
        self.rise = 2.5
        self.spacing = 1.2
        self.points = []

    # ------------------------------------------------------------ the bar

    def options(self):
        return [Option("mode", t("ctx.organic_mode"), "choice", self.mode,
                       tuple((k, t("organic.mode." + k)) for k in MODES)),
                Option("form", t("ctx.organic_form"), "choice", self.form,
                       tuple((k, t("organic.form." + k)) for k in core_or.FORMS)),
                Option("system", t("ctx.organic_system"), "choice", self.system,
                       tuple((k, t("organic.system." + k)) for k in core_or.SYSTEMS)),
                length_option("eave", "ctx.organic_eave", self.eave),
                length_option("rise", "ctx.organic_rise", self.rise),
                length_option("spacing", "ctx.organic_spacing", self.spacing)]

    def set_option(self, key, value):
        if key == "mode" and value in MODES:
            self.mode = value
            self.points = []
            self.viewport.clear_overlays()
        elif key == "form" and value in core_or.FORMS:
            self.form = value
        elif key == "system" and value in core_or.SYSTEMS:
            self.system = value
        elif key == "eave" and value >= 0.0:
            self.eave = float(value)
        elif key == "rise" and value >= 0.1:
            self.rise = float(value)
        elif key == "spacing" and value >= 0.3:
            self.spacing = float(value)
        self.host.set_hint(self.hint())

    def hint(self):
        return t("hint.organic_roof." + self.mode, f=t("organic.form." + self.form).lower(),
                 s=t("organic.system." + self.system).lower())

    # ------------------------------------------------------------ where

    def _level(self):
        return self.doc.work_level()

    def _point(self, x, y, modifiers=()):
        """The point on the storey's floor under the mouse (snapped), or None."""
        level = self._level()
        last = np.array(self.points[-1] + (level,)) if self.points else None
        found, snap, _hit = infer_point(self.viewport, x, y, last, modifiers, flat=True, plane=level_plane(level))
        if found is not None:
            p = np.asarray(found.point, dtype=float)
            show_snap(self.viewport, found)
            return np.array((p[0], p[1], level))
        origin, direction = self.viewport.ray(x, y)
        if abs(direction[2]) < 1e-9:
            return None
        s = (level - origin[2]) / direction[2]
        if s <= 0:
            return None
        self.viewport.show_marker(None)
        p = origin + direction * s
        return np.array((p[0], p[1], level))

    def _outline(self, cursor=None):
        """The outline [(x, y)] as drawn so far (with the mouse's point), as the mode makes it."""
        pts = list(self.points) + ([tuple(cursor[:2])] if cursor is not None else [])
        if self.mode == "retangulo":
            if len(pts) < 2:
                return []
            (x0, y0), (x1, y1) = pts[0], pts[1]
            return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        if self.mode == "circulo":
            if len(pts) < 2:
                return []
            c = np.asarray(pts[0])
            r = float(np.linalg.norm(np.asarray(pts[1]) - c))
            n = max(24, int(math.ceil(2 * math.pi * r / 0.3)))
            return [(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, n,
                                                                                        endpoint=False)]
        if len(pts) < 3:
            return pts
        return core_or.smooth_outline(pts, 0.25) if self.mode == "curvo" else pts

    # ------------------------------------------------------------ the preview

    def _show(self, cursor):
        level = self._level()
        outline = self._outline(cursor)
        segs = []
        if self.mode in ("curvo", "poligono"):
            drawn = list(self.points) + ([tuple(cursor[:2])] if cursor is not None else [])
            for a, b in zip(drawn, drawn[1:]):
                segs += [(a[0], a[1], level), (b[0], b[1], level)]
        ring = outline + outline[:1] if len(outline) >= 3 else []
        for a, b in zip(ring, ring[1:]):
            segs += [(a[0], a[1], level), (b[0], b[1], level)]
        tris = []
        if len(outline) >= 3:
            try:
                size = math.sqrt(max(abs(_area(outline)), 1e-6))
                shape = core_or.Shape(outline, self.rise, self.form)
                v, tr, _edge = shape.surface(max(self.spacing, size / PREVIEW_PIECES))
                if len(tr):
                    v = v + np.array((0.0, 0.0, level + self.eave))
                    tris = v[tr]
                    edge = v[_edge]
                    if len(edge):
                        loop = np.vstack((edge, edge[:1]))
                        for a, b in zip(loop, loop[1:]):
                            segs += [tuple(a), tuple(b)]
            except ValueError:
                tris = []
        self.viewport.show_volume(tris, segments=segs, colors=[PREVIEW] * len(segs))
        if len(outline) >= 3:
            self.host.set_vcb(t("vcb.organic_area", a="{:.1f}".format(abs(_area(outline))).replace(".", decimal_sep())))

    # ------------------------------------------------------------ the mouse

    def pointer_move(self, x, y, modifiers):
        p = self._point(x, y, modifiers)
        if p is None:
            return
        if self.points and self.mode in ("curvo", "poligono") and len(self.points) >= 3 and self._near_first(x, y):
            p = np.array(self.points[0] + (self._level(),))
            self.viewport.show_tip(t("tip.organic_close"), p)
        self._show(p if self.points else None)

    def _near_first(self, x, y):
        sx, sy = self.viewport.project(np.array(self.points[0] + (self._level(),)))
        return math.hypot(sx - x, sy - y) <= CLOSE_PX

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self.points:
                self.points = []
                self.viewport.clear_overlays()
                return
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        p = self._point(x, y, modifiers)
        if p is None:
            return
        if self.mode in ("curvo", "poligono"):
            if len(self.points) >= 3 and self._near_first(x, y):
                self._make(self._outline())
                return
            self.points.append((float(p[0]), float(p[1])))
            self._show(None)
            return
        self.points.append((float(p[0]), float(p[1])))
        if len(self.points) == 2:
            self._make(self._outline())

    def enter(self):
        if self.mode in ("curvo", "poligono") and len(self.points) >= 3:
            self._make(self._outline())

    def delete(self):
        """Backspace / Delete: the last point taken back."""
        if self.points:
            self.points.pop()
            self._show(None)
            return True
        return False

    def _make(self, outline):
        self.points = []
        self.viewport.clear_overlays()
        self.host.set_vcb("")
        if len(outline) < 3:
            return
        level = self._level()
        try:
            guid = bim.add_organic_roof(self.doc, outline, level + self.eave, storey=self.doc.active_storey,
                                        form=self.form, system=self.system, rise=self.rise, spacing=self.spacing)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        info = self.doc.ifc.describe(guid)["params"]
        self.host.message(t("info.organic_roof", name=self.doc.get(guid).name,
                            s=t("organic.system." + self.system).lower(),
                            a="{:.1f}".format(info.get("area", 0.0)).replace(".", decimal_sep()),
                            h=_fmt(self.rise)))

    def cancel(self):
        self.points = []
        self.viewport.clear_overlays()
        self.host.set_vcb("")


def _area(outline):
    p = np.asarray(outline, dtype=float)
    return 0.5 * float(np.dot(p[:, 0], np.roll(p[:, 1], -1)) - np.dot(p[:, 1], np.roll(p[:, 0], -1)))
