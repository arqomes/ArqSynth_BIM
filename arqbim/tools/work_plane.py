"""(0.412) Plano de trabalho — the plane the drawing tools start on in the 3D view (model/work_plane). The owner: «até
agora não introduzimos o conceito de planos de trabalho… podemos criar de acordo com eixos e inserir na tela onde vai
ficar. Pode ser também por seleção de faces».

On the contextual bar: XY (horizontal), XZ (vertical, along the red axis), YZ (vertical, along the green axis) — a
click puts it through that point (a point snapped, a face's point, or where the mouse meets the plane in use) —, or
«Face»: a click on a face, its plane. Shown before the click as a square where it would go; put, it is the work
plane (a blue grid) and the tool gives way to Select. «Nível do piso» lets it go: the storey's level again."""

import numpy as np

from ..core.inference import ON_FACE
from ..core.sketch_geometry import face_world_normal
from ..core.units import format_length
from ..i18n import decimal_sep, t
from ..model import work_plane as wp
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, Tool, infer_point, show_snap, start_plane

PREVIEW_SIZE = 4.0          # m: the square shown where the plane would go


class WorkPlaneTool(Tool):
    name = "work_plane"
    title = "tool.work_plane"
    placement = True                # (Esc: back to Select)
    keys_help = "keys.work_plane"

    def __init__(self, host):
        super().__init__(host)
        self.kind = "xz"            # (the owner's case: drawing upright, along the red axis)

    def options(self):
        return [Option("kind", t("ctx.work_plane"), "buttons", self.kind,
                       tuple((k, t("workplane.short." + k)) for k in wp.KINDS)),
                Option("level", t("ctx.work_plane_level"), "toggle", False)]

    def set_option(self, key, value):
        if key == "kind" and value in wp.KINDS:
            self.kind = value
            self.viewport.clear_overlays()
            self.host.set_hint(self.hint())
        elif key == "level" and value:
            self.host.set_work_plane(None)
            self.host.set_tool("select")

    def activate(self):
        super().activate()
        self.host.set_hint(self.hint())

    def deactivate(self):
        self.viewport.clear_overlays()

    def hint(self):
        return t("hint.work_plane." + self.kind)

    def _plane_at(self, x, y):
        """(the plane a click there would set, the snap shown) — None where there is none (no face, for «Face»)."""
        if self.kind == "face":
            found, _snap, hit = infer_point(self.viewport, x, y, None, ())
            obj = self.doc.get(hit[0]) if hit is not None else None
            if obj is None:
                return None, None
            return wp.by_face(hit[2], face_world_normal(obj.matrix, obj.mesh, hit[1])), None
        plane = start_plane(self.host, x, y)
        if plane is None:
            return None, None
        snap = plane.snap if plane.snap is not None and getattr(plane.snap, "kind", None) != ON_FACE else None
        return wp.by_axes(self.kind, plane.point), snap

    def _preview(self, plane):
        """A square where the plane would go, its two axes through the point."""
        h = PREVIEW_SIZE / 2
        c, u, v = plane.origin, plane.u, plane.v
        corners = [c + u * a + v * b for a, b in ((-h, -h), (h, -h), (h, h), (-h, h))]
        segs = [q for a, b in zip(corners, corners[1:] + corners[:1]) for q in (a, b)]
        segs += [c - u * h, c + u * h, c - v * h, c + v * h]
        self.viewport.show_lines(segs, [PREVIEW] * len(segs))

    def pointer_move(self, x, y, modifiers):
        plane, snap = self._plane_at(x, y)
        if plane is None:
            self.viewport.clear_overlays()
            if self.kind == "face":
                self.viewport.show_tip(t("tip.work_plane_no_face"), None)
            return
        self._preview(plane)
        if snap is not None:
            show_snap(self.viewport, snap, plane.origin)
        self.viewport.show_tip(t(wp.describe(plane)), plane.origin)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        plane, _snap = self._plane_at(x, y)
        if plane is None:
            self.host.message(t("err.work_plane_no_face"), warning=True)
            return
        self.viewport.clear_overlays()
        self.host.set_work_plane(plane)
        self.host.set_tool("select")


def where(plane):
    """Where a plane by the axes is, said: «z = 1,20 m», «y = 2,00 m», «x = …» — a face's: ""."""
    axis = {"xy": 2, "xz": 1, "yz": 0}.get(plane.kind)
    if axis is None:
        return ""
    return "{} = {}".format("xyz"[axis], format_length(float(np.asarray(plane.origin)[axis]), decimal_sep()))
