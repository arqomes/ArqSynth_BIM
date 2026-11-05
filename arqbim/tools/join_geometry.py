"""(0.333) Unjoin and Join Geometry, as Revit's: a click on one element, then on another. Unjoin: their cut and their
faces are no longer cleaned up together — the line between them drawn where they meet, a wall's layers no longer
turning the other's corner, an overlap left as it is. Join: cleaned up again, as every two elements are unless
unjoined. Only the drawing changes (ifc/unjoin.py). The right button lets the first one go; Esc: Select."""

from ..i18n import refusal, t
from ..model import bim
from .base import LEFT, RIGHT, Tool


class UnjoinGeometryTool(Tool):
    name = "unjoin_geometry"
    placement = True                      # (Esc: back to Select)
    keys_help = "keys.unjoin_geometry"
    apart = True

    def __init__(self, host):
        super().__init__(host)
        self._first = None                # the element clicked first

    def hint(self):
        if self._first is None:
            return t("hint.{}".format(self.name))
        return t("hint.{}_2".format(self.name), name=self.doc.get(self._first).name)

    def _element_at(self, x, y):
        """The model element under the mouse (a wall, a slab, a column…), or None."""
        hit = self.viewport.pick(x, y)
        obj = self.doc.get(hit[0]) if hit is not None else None
        return obj.id if obj is not None and obj.is_bim else None

    def pointer_move(self, x, y, modifiers):
        guid = self._element_at(x, y)
        hit = self.viewport.pick_point(x, y) if guid is not None else None
        if guid is None or hit is None:
            self.viewport.show_tip("", None)
            return
        name = self.doc.get(guid).name
        if self._first is None or guid == self._first:
            self.viewport.show_tip(name, hit[2])
            return
        self.viewport.show_tip(t("tip.{}".format(self.name), a=self.doc.get(self._first).name, b=name), hit[2])

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._first is not None:
                self.cancel()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT:
            return
        guid = self._element_at(x, y)
        if guid is None:
            self.host.message(t("err.join_geometry_pick"), warning=True)
            return
        if self._first is None:
            self._first = guid
            self.viewport.set_selection({guid})
            self.host.set_hint(self.hint())
            return
        if guid == self._first:
            return
        a, b = self._first, guid
        names = (self.doc.get(a).name, self.doc.get(b).name)
        try:
            changed = bim.unjoin(self.doc, a, b, self.apart)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self.cancel()
            return
        self.cancel()
        what = "info.{}".format(self.name) if changed else "info.{}_same".format(self.name)
        self.host.message(t(what, a=names[0], b=names[1]))

    def cancel(self):
        self._first = None
        self.viewport.set_selection(set())
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())


class JoinGeometryTool(UnjoinGeometryTool):
    name = "join_geometry"
    keys_help = "keys.join_geometry"
    apart = False
