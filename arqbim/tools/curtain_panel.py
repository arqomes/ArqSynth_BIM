"""Curtain wall panel (0.181): a click on a cell of a curtain wall gives it the panel chosen on the contextual bar —
glass, opaque (a spandrel), a glass door (the bottom row: the cell to the floor) or none; the cell under the mouse
shown."""

from ..i18n import refusal, t
from ..ifc.curtain_walls import PANELS
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, Tool


class CurtainPanelTool(Tool):
    name = "curtain_panel"
    placement = True                     # (Esc: back to Select)
    keys_help = "keys.curtain_panel"

    def __init__(self, host):
        super().__init__(host)
        self.kind = "solid"

    def options(self):
        return [Option("kind", t("ctx.cw_panel"), "choice", self.kind, tuple((k, t("cwpanel." + k)) for k in PANELS))]

    def set_option(self, key, value):
        if key == "kind" and value in PANELS:
            self.kind = value
        self.host.set_hint(self.hint())

    def hint(self):
        return t("hint.curtain_panel", k=t("cwpanel." + self.kind).lower())

    def _cell_at(self, x, y):
        """(curtain wall, cell) under the mouse, or None."""
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None
        obj = self.doc.get(hit[0])
        if obj is None or not obj.is_bim or self.doc.ifc.kind_of(obj.id) != "curtain_wall":
            return None
        cell = self.doc.ifc.curtain_cell_at(obj.id, hit[2])
        return (obj.id, cell) if cell is not None else None

    def pointer_move(self, x, y, modifiers):
        found = self._cell_at(x, y)
        if found is None:
            self.viewport.clear_overlays()
            return
        ring = self.doc.ifc.curtain_cell_box(*found)
        segs = [q for a, b in zip(ring, ring[1:] + ring[:1]) for q in (a, b)]
        self.viewport.show_polygon(ring, segments=segs, colors=[PREVIEW] * len(segs))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        found = self._cell_at(x, y)
        if found is None:
            self.host.message(t("err.cw_panel_none"), warning=True)
            return
        guid, (i, j) = found
        try:
            bim.set_curtain_panel(self.doc, guid, (i, j), self.kind)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self.viewport.clear_overlays()
        self.host.message(t("info.curtain_panel", k=t("cwpanel." + self.kind), c=i + 1, r=j + 1,
                            cw=self.doc.get(guid).name))

    def cancel(self):
        self.viewport.clear_overlays()
