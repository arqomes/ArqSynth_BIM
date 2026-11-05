"""Split wall and Trim / extend to corner (0.104), as Revit's Split Element and Trim/Extend to Corner.

Split wall: over a straight wall the point where it would be split is shown, with the two lengths (its middle
snaps); a click splits it there — or the distance from the nearer end typed. Trim / extend to corner: a click on
a wall, on the side to keep, then on a second one: both go to where their axes meet and are joined there."""

import numpy as np

from ..core.temp_dims import TempDim
from ..core.units import format_length, parse_lengths
from ..core.walls import axis_crossing
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, SNAP_COLORS, Option, Tool

Z = np.array((0.0, 0.0, 1.0))
MIDDLE_PX = 12


def _fmt(v):
    return format_length(v, decimal_sep())


def _wall_at(tool, x, y):
    """(wall GlobalId, the point on its face under the mouse) of a straight wall made here, or None."""
    hit = tool.viewport.pick_point(x, y)
    if hit is None:
        return None
    obj = tool.doc.get(hit[0])
    if obj is None or not obj.is_bim or tool.doc.ifc.kind_of(obj.id) != "wall":
        return None
    return obj.id, np.asarray(hit[2], dtype=float)


class SplitWallTool(Tool):
    name = "split_wall"
    accepts_typing = True
    placement = True                  # (Esc: back to Select)
    keys_help = "keys.split_wall"
    GAP = 0.0                         # (0.300) the gap left at the split (Split with gap: its own default)

    def __init__(self, host):
        super().__init__(host)
        self._target = None           # (wall, s along its axis, its length, axis start, direction, height)
        self.gap = self.GAP

    def options(self):
        """(0.300) The gap on the contextual bar: 0 splits end to end (as Revit's Split Element)."""
        return [Option("gap", t("ctx.split_gap"), "length", self.gap)]

    def set_option(self, key, value):
        if key == "gap":
            self.gap = max(float(value), 0.0)
        self.host.set_hint(self.hint())

    def hint(self):
        return t("hint.split_gap", g=_fmt(self.gap)) if self.gap > 1e-9 else t("hint.split_wall")

    def vcb_title(self):
        return t("vcb.to_end")

    def _target_at(self, x, y):
        found = _wall_at(self, x, y)
        if found is None:
            return None
        guid, point = found
        start, end, _t = self.doc.ifc.wall_axis(guid)
        length, height, _th = self.doc.ifc.wall_params(guid)
        d = (end - start) * np.array((1.0, 1.0, 0.0))
        d /= np.linalg.norm(d)
        s = float(np.clip((point - start)[:2] @ d[:2], 0.0, length))
        middle = start + d * length / 2
        mx, my = self.viewport.project(middle + Z * height / 2)
        on_middle = bool(np.hypot(mx - x, my - y) <= MIDDLE_PX)
        if on_middle:
            s = length / 2
        return guid, s, length, start, d, height, on_middle

    def pointer_move(self, x, y, modifiers):
        self._target = self._target_at(x, y)
        if self._target is None:
            self.viewport.clear_overlays()
            self.host.set_vcb("")
            return
        guid, s, length, start, d, height, on_middle = self._target
        p = start + d * s
        a, b = p - d * self.gap / 2, p + d * self.gap / 2         # (0.300: the gap's sides; one line without)
        lines = [a, a + Z * height] + ([b, b + Z * height] if self.gap > 1e-9 else [])
        self.viewport.show_lines(lines, [PREVIEW] * (len(lines) // 2))
        self.viewport.show_marker(p + Z * height / 2, SNAP_COLORS["midpoint"] if on_middle else PREVIEW)
        self.viewport.show_temp_dims([TempDim(start, a, Z), TempDim(b, start + d * length, Z)])
        key = "tip.split_middle" if on_middle else "tip.split_here"
        self.viewport.show_tip(t(key, a=_fmt(s), b=_fmt(length - s)), p + Z * height / 2)
        self.host.set_vcb(_fmt(min(s, length - s)))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        target = self._target_at(x, y)
        if target is None:
            self.host.message(t("err.split_no_wall"), warning=True)
            return
        self._split(target, target[1])

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None or values[0] is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        if self._target is None:
            self.host.message(t("err.split_no_wall"), warning=True)
            return
        _g, s, length, *_rest = self._target
        self._split(self._target, values[0] if s <= length / 2 else length - values[0])

    def _split(self, target, s):
        guid, _s, length, *_rest = target
        name = self.doc.get(guid).name
        try:
            bim.split_wall(self.doc, guid, s, self.gap)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self._target = None
        self.viewport.clear_overlays()
        if self.gap > 1e-9:
            half = self.gap / 2
            self.host.message(t("info.split_gap", name=name, a=_fmt(s - half), b=_fmt(length - s - half),
                                g=_fmt(self.gap)))
        else:
            self.host.message(t("info.split_wall", name=name, a=_fmt(s), b=_fmt(length - s)))

    def cancel(self):
        self._target = None
        self.viewport.clear_overlays()
        self.host.set_vcb("")


class SplitGapTool(SplitWallTool):
    """(0.300) Split with gap, as Revit's: the split tool with a gap from the start (changed on the contextual bar)."""
    name = "split_gap"
    GAP = 0.02


class TrimExtendTool(Tool):
    """(0.300) Trim / extend to a boundary, as Revit's Trim/Extend Multiple Elements: a click on the wall that is the
    boundary, then a click on each wall to bring to it — on the side that stays. Esc: another boundary; Esc again:
    Select."""
    name = "trim_extend"
    placement = True
    keys_help = "keys.trim_extend"

    def __init__(self, host):
        super().__init__(host)
        self._boundary = None

    def hint(self):
        return t("hint.trim_extend_2") if self._boundary is not None else t("hint.trim_extend")

    def pointer_move(self, x, y, modifiers):
        found = _wall_at(self, x, y)
        if self._boundary is None or found is None or found[0] == self._boundary:
            self.viewport.show_marker(None)
            self.viewport.show_tip("", None)
            return
        s, e, _t = self.doc.ifc.wall_axis(found[0])
        bs, be, _bt = self.doc.ifc.wall_axis(self._boundary)
        d, db = (e - s) * np.array((1, 1, 0)), (be - bs) * np.array((1, 1, 0))
        cross = axis_crossing(s, d / np.linalg.norm(d), bs, db / np.linalg.norm(db))
        if cross is None:
            self.viewport.show_tip(t("refuse.parallel"), found[1])
            return
        self.viewport.show_marker(cross, SNAP_COLORS["intersection"])
        self.viewport.show_tip("", None)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._boundary is not None:
                self.cancel()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT:
            return
        found = _wall_at(self, x, y)
        if found is None:
            self.host.message(t("err.split_no_wall"), warning=True)
            return
        if self._boundary is None:
            self._boundary = found[0]
            self.viewport.set_selection({found[0]})
            self.host.message(t("info.trim_extend_first", name=self.doc.get(found[0]).name))
            self.host.set_hint(self.hint())
            return
        if found[0] == self._boundary:
            return
        name, limit = self.doc.get(found[0]).name, self.doc.get(self._boundary).name
        try:
            bim.trim_extend_wall(self.doc, found[0], self._boundary, found[1][:2])
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self.viewport.set_selection({self._boundary})
        self.host.message(t("info.trim_extend", name=name, b=limit))

    def cancel(self):
        self._boundary = None
        self.viewport.set_selection(set())
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())


class WallJoinsTool(Tool):
    """(0.301) Wall joins, as Revit's: with «Topo a topo» (Tab or the bar changes it) a click on a wall near one of its
    corners makes it run through, the other stopping at its face; with «Meia-esquadria», the corner is mitred. Only
    right-angle corners: at the other angles walls are mitred anyway."""
    name = "wall_joins"
    placement = True
    keys_help = "keys.wall_joins"

    def __init__(self, host):
        super().__init__(host)
        self.style = "butt"

    def options(self):
        return [Option("style", t("ctx.join_style"), "choice", self.style,
                       (("butt", t("joinstyle.butt")), ("mitre", t("joinstyle.mitre"))))]

    def set_option(self, key, value):
        if key == "style" and value in ("butt", "mitre"):
            self.style = value
        self.host.set_hint(self.hint())

    def hint(self):
        return t("hint.wall_joins." + self.style)

    def _corner_at(self, x, y):
        """(wall, its end, the end's point) of the corner nearest the mouse on the wall under it, or None."""
        found = _wall_at(self, x, y)
        if found is None:
            return None
        guid, point = found
        start, end, _t = self.doc.ifc.wall_axis(guid)
        length = float(np.linalg.norm((end - start)[:2]))
        along = float((point - start)[:2] @ ((end - start)[:2] / length))
        which = "start" if along < length / 2 else "end"
        if self.doc.ifc.corner_joint(guid, which) is None:
            return None
        return guid, which, start if which == "start" else end

    def pointer_move(self, x, y, modifiers):
        corner = self._corner_at(x, y)
        if corner is None:
            self.viewport.show_marker(None)
            self.viewport.show_tip("", None)
            return
        self.viewport.show_marker(corner[2], SNAP_COLORS["endpoint"])
        self.viewport.show_tip(t("joinstyle." + self.style), corner[2])

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        corner = self._corner_at(x, y)
        if corner is None:
            self.host.message(t("err.no_corner"), warning=True)
            return
        guid, which, _p = corner
        try:
            other = bim.set_wall_corner(self.doc, guid, which, self.style)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self.host.message(t("info.wall_joins." + self.style, name=self.doc.get(guid).name,
                            other=self.doc.get(other).name))

    def tab(self):
        """Tab: the other way."""
        self.set_option("style", "mitre" if self.style == "butt" else "butt")
        self.host.message(t("joinstyle." + self.style))
        return True

    def cancel(self):
        self.viewport.clear_overlays()


class CornerWallsTool(Tool):
    name = "corner_walls"
    placement = True
    keys_help = "keys.corner_walls"

    def __init__(self, host):
        super().__init__(host)
        self._first = None            # (wall, the point clicked on it)

    def hint(self):
        return t("hint.corner_walls_2") if self._first is not None else t("hint.corner_walls")

    def pointer_move(self, x, y, modifiers):
        found = _wall_at(self, x, y)
        if self._first is None or found is None or found[0] == self._first[0]:
            self.viewport.show_marker(None)
            self.viewport.show_tip("", None)
            return
        sa, ea, _ta = self.doc.ifc.wall_axis(self._first[0])
        sb, eb, _tb = self.doc.ifc.wall_axis(found[0])
        da, db = (ea - sa) * np.array((1, 1, 0)), (eb - sb) * np.array((1, 1, 0))
        cross = axis_crossing(sa, da / np.linalg.norm(da), sb, db / np.linalg.norm(db))
        if cross is None:
            self.viewport.show_tip(t("refuse.parallel"), found[1])
            return
        self.viewport.show_marker(cross, SNAP_COLORS["intersection"])
        self.viewport.show_tip("", None)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._first is not None:
                self.cancel()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT:
            return
        found = _wall_at(self, x, y)
        if found is None:
            self.host.message(t("err.split_no_wall"), warning=True)
            return
        if self._first is None:
            self._first = found
            self.viewport.set_selection({found[0]})
            self.host.message(t("info.corner_first", name=self.doc.get(found[0]).name))
            self.host.set_hint(self.hint())
            return
        if found[0] == self._first[0]:
            return
        a, b = self._first[0], found[0]
        names = (self.doc.get(a).name, self.doc.get(b).name)
        try:
            bim.corner_walls(self.doc, a, self._first[1][:2], b, found[1][:2])
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self.cancel()
            return
        self.cancel()
        self.host.message(t("info.corner_walls", a=names[0], b=names[1]))

    def cancel(self):
        self._first = None
        self.viewport.set_selection(set())
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
