"""Wall opening (0.303), as Revit's: a click on a straight wall's face starts a rectangle in its plane, a second click
— or its width and height typed, "1,20;2,10" — ends it: an opening right through the wall, with no door or window (an
IfcOpeningElement), that goes with the wall. Its corners go by the centimetre; the temporary dimensions show its
width, its height and how high it starts. (0.305) Wall reveal: a groove in a wall's face, level or vertical."""

import numpy as np

from ..core.sketch_geometry import ray_plane
from ..core.temp_dims import TempDim
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, SNAP_COLORS, Option, Tool
from .bim_draw import length_option
from .wall_edit import _wall_at

Z = np.array((0.0, 0.0, 1.0))
FACE_GAP = 0.005                    # m: the rectangle a hair off the face (seen in front of it)


def _fmt(v):
    return format_length(v, decimal_sep())


class WallOpeningTool(Tool):
    name = "wall_opening"
    accepts_typing = True
    placement = True                # (Esc: back to Select)
    keys_help = "keys.wall_opening"

    def __init__(self, host):
        super().__init__(host)
        self._wall = None           # (guid, a point of the face at its base's start, along, out of the face, length, height)
        self._first = None          # (x along the wall, z over its base) of the first corner
        self._last = None           # the corner under the mouse

    def hint(self):
        return t("hint.wall_opening_2") if self._first is not None else t("hint.wall_opening")

    def vcb_title(self):
        return t("vcb.opening_size")

    def _frame(self, guid, hit):
        s, e, thickness = self.doc.ifc.wall_axis(guid)
        length, height, _t = self.doc.ifc.wall_params(guid)
        along = (e - s) * np.array((1.0, 1.0, 0.0))
        along /= np.linalg.norm(along)
        out = np.array((-along[1], along[0], 0.0))
        if float((np.asarray(hit) - s) @ out) < 0:
            out = -out                                  # (the face clicked)
        return guid, s + out * thickness / 2, along, out, length, height

    def _local(self, x, y):
        """(x along, z up) in the wall's face plane under the mouse, by the centimetre, kept within the wall."""
        _g, base, along, out, length, height = self._wall
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, base, out)
        if p is None:
            p = ray_plane(origin, direction, base, -out)
        if p is None:
            return None
        return (round(float(np.clip((p - base) @ along, 0.0, length)), 2),
                round(float(np.clip((p - base) @ Z, 0.0, height)), 2))

    def _world(self, lx, lz):
        _g, base, along, out, _l, _h = self._wall
        return base + along * lx + Z * lz + out * FACE_GAP

    def pointer_move(self, x, y, modifiers):
        if self._first is None:
            found = _wall_at(self, x, y)
            if found is None:
                self.viewport.clear_overlays()
                return
            self.viewport.show_marker(found[1], SNAP_COLORS["endpoint"])
            self.viewport.show_tip(self.doc.get(found[0]).name, found[1])
            return
        corner = self._local(x, y)
        if corner is None:
            return
        self._last = corner
        (x0, z0), (x1, z1) = self._first, corner
        pts = [self._world(*q) for q in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]
        self.viewport.show_lines([p for k in range(4) for p in (pts[k], pts[(k + 1) % 4])], [PREVIEW] * 4)
        lo, hi = min(z0, z1), max(z0, z1)
        _g, _b, along, _o, _l, _h = self._wall
        self.viewport.show_temp_dims([TempDim(self._world(x0, lo), self._world(x1, lo), -Z),
                                      TempDim(self._world(max(x0, x1), lo), self._world(max(x0, x1), hi), along),
                                      TempDim(self._world(min(x0, x1), 0.0), self._world(min(x0, x1), lo), -along)])
        self.host.set_vcb("{};{}".format(_fmt(abs(x1 - x0)), _fmt(abs(z1 - z0))))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._first is not None:
                self.cancel()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT:
            return
        if self._first is None:
            found = _wall_at(self, x, y)
            if found is None:
                self.host.message(t("err.split_no_wall"), warning=True)
                return
            self._wall = self._frame(*found)
            self._first = self._local(x, y)
            self.host.set_hint(self.hint())
            return
        corner = self._local(x, y)
        if corner is not None:
            self._make(self._first, corner)

    def typed(self, text):
        values = parse_lengths(text, 2)
        if self._first is None or values is None or None in values:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        width, height = values
        x0, z0 = self._first
        x1, z1 = self._last if self._last is not None else (x0 + width, z0 + height)
        self._make(self._first, (x0 + (width if x1 >= x0 else -width), z0 + (height if z1 >= z0 else -height)))

    def _make(self, a, b):
        guid = self._wall[0]
        x0, x1 = sorted((a[0], b[0]))
        z0, z1 = sorted((a[1], b[1]))
        try:
            bim.add_wall_opening(self.doc, guid, x0, x1 - x0, z1 - z0, z0)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self.host.message(t("info.wall_opening", w=_fmt(x1 - x0), h=_fmt(z1 - z0), z=_fmt(z0),
                            wall=self.doc.get(guid).name))
        self.cancel()

    def cancel(self):
        self._wall = self._first = self._last = None
        self.viewport.clear_overlays()
        self.host.set_vcb("")
        self.host.set_hint(self.hint())


class NicheTool(WallOpeningTool):
    """(0.374, the addon's «Nicho», the study's Aberturas) As the wall opening, but a niche: a rectangle on the face
    clicked, `depth` into the wall (the contextual bar), not through it — an IfcOpeningElement RECESS that goes with
    the wall."""
    name = "niche"
    keys_help = "keys.wall_opening"

    def __init__(self, host):
        super().__init__(host)
        self.depth = 0.10

    def options(self):
        return [length_option("depth", "ctx.niche_depth", self.depth)]

    def set_option(self, key, value):
        if key == "depth" and value > 0.004:
            self.depth = float(value)
        self.host.set_hint(self.hint())

    def hint(self):
        return t("hint.niche_2") if self._first is not None else t("hint.niche", d=_fmt(self.depth))

    def _make(self, a, b):
        guid, _base, _along, out = self._wall[:4]
        x0, x1 = sorted((a[0], b[0]))
        z0, z1 = sorted((a[1], b[1]))
        try:
            bim.add_wall_niche(self.doc, guid, x0, x1 - x0, z1 - z0, z0, self.depth, out)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self.host.message(t("info.niche_made", w=_fmt(x1 - x0), h=_fmt(z1 - z0), d=_fmt(self.depth),
                            wall=self.doc.get(guid).name))
        self.cancel()


class WallRevealTool(Tool):
    """(0.305) Wall reveal, as Revit's: a click on a straight wall's face cuts a groove in it — level, at the height
    clicked, along the whole wall; or vertical (Tab), where it is clicked, up the whole wall —, its width and depth on
    the contextual bar; «Tirar ranhuras» on, a click takes away the one under it. Heights and places go by the
    centimetre."""
    name = "wall_reveal"
    placement = True
    keys_help = "keys.wall_reveal"

    def __init__(self, host):
        super().__init__(host)
        self.vertical = False
        self.width = 0.02
        self.depth = 0.01
        self.remove = False

    def options(self):
        return [Option("direction", t("ctx.reveal_direction"), "choice", "v" if self.vertical else "h",
                       (("h", t("revealdir.h")), ("v", t("revealdir.v")))),
                length_option("width", "ctx.reveal_width", self.width),
                length_option("depth", "ctx.reveal_depth", self.depth),
                Option("remove", t("ctx.reveal_remove"), "toggle", self.remove)]

    def set_option(self, key, value):
        if key == "direction":
            self.vertical = value == "v"
        elif key == "width" and 0.005 <= float(value) <= 0.5:
            self.width = float(value)
        elif key == "depth" and 0.002 <= float(value) <= 0.2:
            self.depth = float(value)
        elif key == "remove":
            self.remove = bool(value)
        self.host.set_hint(self.hint())

    def tab(self):
        self.set_option("direction", "h" if self.vertical else "v")
        return True

    def hint(self):
        return t("hint.wall_reveal.remove") if self.remove else \
            t("hint.wall_reveal." + ("v" if self.vertical else "h"))

    def _target(self, x, y):
        """(wall, side, at, its axis start, along, out of the face clicked, length, height, thickness) under the
        mouse, or None."""
        found = _wall_at(self, x, y)
        if found is None:
            return None
        guid, hit = found
        s, e, thickness = self.doc.ifc.wall_axis(guid)
        length, height, _t = self.doc.ifc.wall_params(guid)
        along = (e - s) * np.array((1.0, 1.0, 0.0))
        along /= np.linalg.norm(along)
        left = np.array((-along[1], along[0], 0.0))
        side = 1 if float((np.asarray(hit) - s) @ left) > 0 else -1
        at = float((np.asarray(hit) - s) @ along) if self.vertical else float(hit[2] - s[2])
        at = round(float(np.clip(at, self.width / 2, (length if self.vertical else height) - self.width / 2)), 2)
        return guid, side, at, s, along, left * side, length, height, thickness

    def pointer_move(self, x, y, modifiers):
        target = self._target(x, y)
        if target is None:
            self.viewport.clear_overlays()
            return
        _g, _side, at, s, along, out, length, height, thickness = target
        face = s + out * (thickness / 2 + 0.005)
        if self.vertical:
            a, b = face + along * at, face + along * at + Z * height
        else:
            a, b = face + Z * at, face + along * length + Z * at
        self.viewport.show_lines([a, b], [PREVIEW])
        self.viewport.show_tip(_fmt(at), (a + b) / 2)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        target = self._target(x, y)
        if target is None:
            self.host.message(t("err.split_no_wall"), warning=True)
            return
        guid, side, at = target[:3]
        name = self.doc.get(guid).name
        try:
            if self.remove:
                near = [(abs(r["at"] - at), g) for g, r in self.doc.ifc.wall_reveals(guid)
                        if r["side"] == side and r["vertical"] == self.vertical
                        and abs(r["at"] - at) <= r["width"] / 2 + 0.05]
                if not near:
                    self.host.message(t("err.no_reveal"), warning=True)
                    return
                bim.remove_wall_reveal(self.doc, guid, min(near)[1])
                self.host.message(t("info.wall_reveal_removed", wall=name))
                return
            bim.add_wall_reveal(self.doc, guid, side, self.vertical, at, self.width, self.depth)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self.host.message(t("info.wall_reveal." + ("v" if self.vertical else "h"), w=_fmt(self.width),
                            d=_fmt(self.depth), at=_fmt(at), wall=name))

    def cancel(self):
        self.viewport.clear_overlays()
