"""(0.485) A label of the Presentation tab put on the model — its «Etiquetas» › Piso / Parede / Em pé / Chamada, then a
click on a surface (the Presentation's: «Clique numa superfície do modelo para colocar a etiqueta. Esc cancela.»).

Where the cursor is, the label's outline is shown as it will be (on the face under it, turned towards the viewer;
off the model, on the ground); the click puts it there — one undo step — and goes back to Select, the new label chosen
in the right column. Esc or the right button: none put."""

import numpy as np

from ..core.sketch_geometry import face_world_normal, ray_plane
from ..i18n import t
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Tool


class LabelPlaceTool(Tool):
    name = "pres_label"
    title = "tool.pres_label"
    placement = True                     # (Esc: back to Select)

    def hint(self):
        return t("pmode.tag_place_hint")

    @property
    def mode(self):
        return getattr(self.host, "presentation_mode", None)

    def activate(self):
        super().activate()
        if self.mode is not None:
            self.mode.show_placing()

    def deactivate(self):
        super().deactivate()
        self.viewport.clear_overlays()
        if self.mode is not None:
            self.mode.show_placing(False)              # (the window's tool is still this one while it is put away)

    def spot(self, x, y):
        """(point, normal) where a label goes for the pixel: the face under it (its normal turned towards the
        viewer), else the ground (its normal up); None when the ray misses both."""
        vp = self.viewport
        hit = vp.pick_point(x, y)
        if hit is not None and hit[0] in vp._meshes:
            mesh, matrix = vp._meshes[hit[0]]
            n = np.asarray(face_world_normal(matrix, mesh, hit[1]), dtype=float)
            if float(n @ vp.view_direction()) > 0:
                n = -n
            return np.asarray(hit[2], dtype=float), n
        origin, direction = vp.ray(x, y)
        level = 0.0
        try:
            levels = [z for _g, _n, z in self.doc.storeys()]
            level = float(min(levels)) if levels else 0.0
        except AttributeError:
            pass
        p = ray_plane(origin, direction, np.array((0.0, 0.0, level)), np.array((0.0, 0.0, 1.0)))
        return (np.asarray(p, dtype=float), np.array((0.0, 0.0, 1.0))) if p is not None else None

    def pointer_move(self, x, y, modifiers):
        found = self.spot(x, y) if self.mode is not None else None
        if found is None:
            self.viewport.clear_overlays()
            return
        frame = self.mode.label_preview(*found)
        corners = frame["corners"]
        segs = [q for a, b in zip(corners, corners[1:] + corners[:1]) for q in (a, b)]
        segs += [q for line in frame["lines"] for q in line]
        self.viewport.show_polygon(corners, segments=segs, colors=[PREVIEW] * len(segs))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT or self.mode is None:
            return
        found = self.spot(x, y)
        if found is None:
            self.host.message(t("pmode.tag_nowhere"), warning=True)
            return
        self.viewport.clear_overlays()
        self.mode.place_label(*found)
        self.host.set_tool("select")

    def cancel(self):
        self.viewport.clear_overlays()
