"""Loose furniture (0.440, the owner: «Sim, peças próprias»): the catalogue's piece chosen on the bar — a bed, a sofa,
a table, a chair, a bookcase, a plant… (core/loose_furniture) —, its width, depth and height there too (its own to
start); under the mouse its footprint and its box, with the snaps and alignments; R / Shift+R turn it a quarter, Space /
Shift+Space choose which of its footprint's nine points goes on the point (its middle, its front's middle, a
corner…), as a column (0.86); a click puts it there. Esc: Select."""

import numpy as np

from ..core import loose_furniture as core_loose
from ..core import placement
from ..core.units import format_length
from ..i18n import decimal_sep, lang, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, show_snap
from .bim_draw import _PointTool, box_edges, length_option

Z = np.array((0.0, 0.0, 1.0))
ANGLES = (0, 90, 180, 270)


def _fmt(v):
    return format_length(v, decimal_sep())


def piece_name(key):
    return core_loose.PIECES[key][2][0 if lang() == "pt" else 1]


class LooseFurnitureTool(_PointTool):
    name = "loose_furniture"
    common_keys = frozenset(("r", "shift+r", "space", "shift+space"))
    placement = True
    keys_help = "keys.loose_furniture"

    def __init__(self, host):
        super().__init__(host)
        self.piece = "sofa_3"
        self.width, self.depth, self.height = core_loose.defaults(self.piece)
        self.angle = 0
        self.insertion = 0

    # ------------------------------------------------------------ the bar

    def options(self):
        pieces = tuple((k, "{} ▸ {}".format(t("loosegroup." + core_loose.PIECES[k][0]), piece_name(k)))
                       for g in core_loose.GROUPS for k in core_loose.PIECES if core_loose.PIECES[k][0] == g)
        return [Option("piece", t("ctx.loose_piece"), "choice", self.piece, pieces),
                length_option("width", "props.width", self.width),
                length_option("depth", "props.depth", self.depth),
                length_option("height", "ctx.height", self.height),
                Option("angle", t("ctx.angle"), "choice", self.angle, tuple((a, "{}°".format(a)) for a in ANGLES)),
                Option("insertion", t("ctx.insertion"), "choice", self.insertion,
                       tuple((k, t("ins.{}".format(k))) for k in range(len(placement.INSERTION))))]

    def set_option(self, key, value):
        if key == "piece" and value in core_loose.PIECES:
            self.piece = value
            self.width, self.depth, self.height = core_loose.defaults(value)     # (its own sizes)
        elif key in ("width", "depth", "height") and core_loose.LEAST <= value <= core_loose.MOST:
            setattr(self, key, float(value))
        elif key == "angle":
            self.angle = int(value) % 360
        elif key == "insertion":
            self.insertion = int(value)
        self._again()

    def common_key(self, name):
        if name in ("r", "shift+r"):
            self.angle = placement.turn(self.angle, 1 if name == "r" else -1)
            self.host.message(t("info.turned", a=self.angle))
        else:
            self.insertion = placement.next_insertion(self.insertion, 1 if name == "space" else -1)
            self.host.message(t("info.insertion", p=t("ins.{}".format(self.insertion))))
        self._again()
        return True

    def _again(self):
        self.host.set_hint(self.hint())
        if self._hover is not None:
            self._show(*self._hover)

    def hint(self):
        return t("hint.loose_furniture", name=piece_name(self.piece), w=_fmt(self.width), d=_fmt(self.depth),
                 h=_fmt(self.height))

    # ------------------------------------------------------------ the mouse

    def _placed(self, p):
        return placement.place_box(p, self.width, self.depth, self.angle, self.insertion)

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        self._show(p, snap)

    def _show(self, p, snap):
        centre, x_dir, foot = self._placed(p)
        segs = box_edges(foot, [c + Z * self.height for c in foot])
        y_dir = np.cross(Z, x_dir)                          # (its front: a line across it, a little in)
        front = [centre - y_dir * (self.depth / 2 - 0.05) + x_dir * s * (self.width / 2 - 0.05) for s in (-1, 1)]
        segs += front
        self.viewport.show_polygon(foot, segments=segs, colors=[PREVIEW] * len(segs))
        show_snap(self.viewport, snap, p)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        p, _snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
        if p is None:
            return
        centre, _x, _foot = self._placed(p)
        try:
            bim.add_loose(self.doc, self.piece, centre, self.angle, storey=self.doc.active_storey, width=self.width,
                          depth=self.depth, height=self.height)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self.host.message(t("info.loose", name=piece_name(self.piece), w=_fmt(self.width), d=_fmt(self.depth)))

    def cancel(self):
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
