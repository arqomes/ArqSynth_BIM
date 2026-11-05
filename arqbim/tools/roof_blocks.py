"""(0.385) A roof by blocks edited in the 3D view — the owner: «gostaria que a edição do bloco de telhado se desse no
ambiente 3D sem ser pela janela extra… no ambiente 3D ele abre a edição com 2 cliques, e podemos selecionar os blocos
individualmente ou em grupo e editamos. Deve aparecer botões de edição acoplado nos blocos que permite remover ou
adicionar águas, aumentar a cota de um beiral, e do bloco inteiro».

Two clicks on a roof by blocks start it (the block under the mouse chosen). Then, in the view:

- a click on a block chooses it; with Shift (or Ctrl) it joins the ones chosen, or leaves them; a click beside the
  roof: none chosen. All the blocks' outlines are drawn at their eaves, the chosen ones strong;
- on each chosen block: a square in the middle of each side — a click turns that side from a water to a gable and
  back; dragged, the side goes out or in (the opposite side staying; on a wall, out to its outer face) —, a diamond
  in its middle — dragged, the chosen blocks move —, a «+» outside each side (one block chosen) — a click puts a block
  of the same size against that side, the two sides that touch turned to gables (the roof carried on);
- temporary dimensions, their values clicked and typed over (Enter): the height of each water's eave (from the
  storey's floor) and of the whole block (its lowest eave: all its eaves go up or down together); a number typed with
  no dimension clicked: the chosen blocks' height;
- Delete: the chosen blocks taken away (one stays at least). Each change is one undo step; Esc: Select.

The block editor window stays, for the numbers (Properties ▸ Edit blocks…).

(0.386, the owner: «tem como melhorar a aparência, principalmente da cota: não precisa de linhas de cota e chamada,
somente um retângulo paralelo ao lado do beiral, e no meio entende-se como a cota geral. Em vez de + para adicionar
blocos, devia ficar alças para escalar o bloco; o + e − poderiam ficar para adicionar e remover água»)
- the heights are boxes alone (temp_dims «label»): each water's laid along its eave's edge, the block's in its middle;
- squares are handles that scale the block: in a side's middle that side goes out or in; on a corner its two sides;
- outside each side a «−» (a water: taken away, a gable there) or a «+» (a gable: made a water) — a click;
- the block put against a side is gone (the Roof tool «Por blocos» adds blocks)."""

import numpy as np

from ..core import roof_blocks as core_blocks
from ..core import temp_dims
from ..core.sketch_geometry import ray_plane
from ..core.units import format_length, parse_length
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Tool, moved_enough

Z_UP = np.array((0.0, 0.0, 1.0))
OTHER = (0.55, 0.62, 0.72, 1.0)         # the blocks not chosen: their outlines, quiet
SIGN_OUT = 0.6                          # m: (0.386) a side's «+» / «−» this far out of its eave…
SIGN_ALONG = 1.2                        # …and this far along it from its middle (at most a quarter of the side)
GRIP_FIRST_PX = 5                       # (0.386) inside a height's box, a grip wins only this near its centre
CORNER_SIDES = ((2, 3), (2, 1), (0, 1), (0, 3))   # (0.386) the two sides of each corner of core_blocks.rect


def _fmt(v):
    return format_length(v, decimal_sep())


class RoofBlocksTool(Tool):
    name = "roof_blocks"
    title = "tool.roof_blocks"
    placement = True                    # (Esc: back to Select)
    keys_help = "keys.roof_blocks"

    def __init__(self, host):
        super().__init__(host)
        self.guid = None
        self.blocks = []                # in the plan (world x, y), as roof_blocks_world gives them
        self.level = 0.0                # the roof's level (its eaves over it)
        self.floor = 0.0                # its storey's floor (the heights are from there)
        self.chosen = set()             # the blocks chosen (indices)
        # (handles [("side" | "corner", block, side | corner, point)], middles [(block, point)], «+» and «−»
        # [(block, side, point)])
        self._grips = None
        self._dims = []                 # the temporary dimensions shown
        self._active = None             # the one clicked, to type over
        self._drag = None               # {"kind": "side" | "move", "block", "side", "base", "press", "target"}
        host.doc.subscribe(self._changed)

    # ------------------------------------------------------------ starting, leaving

    def edit(self, guid, at=None):
        """Edit this roof's blocks — the one under `at` (a point of the roof, plan) chosen."""
        self.guid = guid
        self.chosen = set()
        self._load()
        if at is not None:
            k = self._block_at(float(at[0]), float(at[1]))
            if k is not None:
                self.chosen = {k}
        elif self.blocks:
            self.chosen = {0}
        self.host.set_tool(self.name)

    def activate(self):
        super().activate()
        self._load()
        self._show()

    def deactivate(self):
        self._drag = self._active = None
        self.viewport.show_grips()
        self.viewport.show_temp_dims()
        self.viewport.clear_overlays()

    def _changed(self, changed, removed):
        if self.host.tool is self and not self.doc.loading:
            self._drag = self._active = None
            self._load()
            self._show()

    def _load(self):
        ifc = self.doc.ifc
        e = ifc.by_guid(self.guid) if self.guid else None
        if e is None or ifc.kind_of(self.guid) != "roof" or ifc.roof_params(self.guid).get("form") != "blocks":
            self.blocks, self.chosen = [], set()
            return
        self.level = float(ifc.roof_params(self.guid)["eave"])
        self.blocks = list(ifc.roof_blocks_world(self.guid))
        storey = ifc.storey_of(self.guid)
        self.floor = next((float(z) for g, _n, z in ifc.storeys() if g == storey), 0.0)
        self.chosen = {k for k in self.chosen if k < len(self.blocks)}

    # ------------------------------------------------------------ what is shown

    def _top(self, b, x, y):
        return self.level + (core_blocks.block_top(b, x, y) or 0.0)

    def _show(self):
        """The blocks' outlines (the chosen ones strong), the chosen ones' grips and dimensions."""
        if not self.blocks:
            self.viewport.show_grips()
            self.viewport.show_temp_dims()
            self.viewport.clear_overlays()
            self.host.set_hint(t("hint.roof_blocks_none"))
            return
        segs, colors = [], []
        for i, b in enumerate(self.blocks):
            z = self.level + min(b.eave)
            ring = [np.array((x, y, z)) for x, y in core_blocks.rect(b)]
            color = PREVIEW if i in self.chosen else OTHER
            for p, q in zip(ring, ring[1:] + ring[:1]):
                segs += [p, q]
                colors += [color, color]
        self.viewport.show_lines(segs, colors)
        handles, middles, adds, subs = [], [], [], []
        for i in sorted(self.chosen):
            b = self.blocks[i]
            for k in range(4):
                out, half = core_blocks.side_way(b, k)
                x, y = b.cx + out[0] * half, b.cy + out[1] * half
                handles.append(("side", i, k, np.array((x, y, self._top(b, x, y)))))
                # (its «−» if a water, its «+» if a gable: out of the eave and along it, clear of the height's box in
                # the side's middle)
                reach = half + b.overhang + SIGN_OUT
                side_len = b.width if k in (0, 2) else b.depth
                slide = min(SIGN_ALONG, side_len / 4)
                sx = b.cx + out[0] * reach - out[1] * slide
                sy = b.cy + out[1] * reach + out[0] * slide
                (subs if b.water[k] else adds).append((i, k, np.array((sx, sy, self.level + b.eave[k]))))
            for c, (x, y) in enumerate(core_blocks.rect(b)):
                handles.append(("corner", i, c, np.array((x, y, self._top(b, x, y)))))
            middles.append((i, np.array((b.cx, b.cy, self._top(b, b.cx, b.cy)))))
        self._grips = (handles, middles, adds, subs)
        self.viewport.show_grips([h[3] for h in handles], [p for _i, p in middles], [p for _i, _k, p in adds],
                                 subs=[p for _i, _k, p in subs])
        self._dims = self._make_dims()
        self.viewport.show_temp_dims(self._dims, active=self._active)
        self.viewport.show_tip("", None)                 # (a grip's tip from before the change: gone)
        self.host.set_hint(self.hint())
        if hasattr(self.host, "vcb_title_changed"):
            self.host.vcb_title_changed()

    def _make_dims(self):
        """Each chosen block's water eaves (from the floor) — (0.386) a box alone laid along its eave's edge — and its
        height (its lowest eave) — a box in its middle, on its top —, their values typed over."""
        dims = []
        for i in sorted(self.chosen):
            b = self.blocks[i]
            for k in range(4):
                if not b.water[k]:
                    continue
                out, half = core_blocks.side_way(b, k)
                edge = np.array((b.cx + out[0] * (half + b.overhang), b.cy + out[1] * (half + b.overhang),
                                 self.level + b.eave[k]))
                along = np.array((-out[1], out[0], 0.0)) * 0.01
                dims.append(temp_dims.TempDim(edge - along, edge + along, Z_UP, key=("eave", i, k), kind="label",
                                              shown=self.level + b.eave[k] - self.floor))
            a = np.radians(b.angle)
            long_way = np.array((np.cos(a), np.sin(a), 0.0)) if b.width >= b.depth else \
                np.array((-np.sin(a), np.cos(a), 0.0))
            top = np.array((b.cx, b.cy, self._top(b, b.cx, b.cy)))
            dims.append(temp_dims.TempDim(top - long_way * 0.01, top + long_way * 0.01, Z_UP, key=("height", i),
                                          kind="label", shown=self.level + min(b.eave) - self.floor))
        return dims

    def hint(self):
        if not self.blocks:
            return t("hint.roof_blocks_none")
        if self._drag is not None:
            return t("hint.roof_blocks_drag_" + self._drag["kind"])
        if self._active is not None:
            return t("hint.roof_blocks_type")
        return t("hint.roof_blocks" if self.chosen else "hint.roof_blocks_pick")

    @property
    def accepts_typing(self):
        return bool(self.chosen)

    def vcb_title(self):
        if self._active is not None:
            return t("vcb.roof_eave" if self._active.key[0] == "eave" else "vcb.roof_block_height")
        return t("vcb.roof_block_height") if self.chosen else None

    def options(self):
        return []

    # ------------------------------------------------------------ the mouse

    def _block_at(self, x, y):
        """The block under a plan point (the smallest, where they overlap; their overhangs count), or None."""
        from shapely.geometry import Point, Polygon
        under = [k for k, b in enumerate(self.blocks)
                 if Polygon(core_blocks.rect(b, b.overhang)).buffer(1e-6).contains(Point(x, y))]
        return min(under, key=lambda k: self.blocks[k].width * self.blocks[k].depth) if under else None

    def _block_under_mouse(self, x, y):
        hit = self.viewport.pick_point(x, y)
        if hit is not None and hit[0] == self.guid:
            return self._block_at(float(hit[2][0]), float(hit[2][1]))
        origin, direction = self.viewport.ray(x, y)          # (beside the roof's faces: its eaves' level)
        p = ray_plane(origin, direction, np.array((0.0, 0.0, self.level)), Z_UP)
        return self._block_at(float(p[0]), float(p[1])) if p is not None else None

    def _grip(self, x, y):
        """What grip is under the mouse, and where: (("side" | "corner", block, side | corner) | ("move", block) |
        ("water" | "gable", block, side), its point) — or None."""
        if self._grips is None:
            return None
        found = self.viewport.grip_at(x, y)
        if found is None:
            return None
        kind, k = found
        handles, middles, adds, subs = self._grips
        if kind == "end" and k < len(handles):
            return handles[k][:3], handles[k][3]
        if kind == "middle" and k < len(middles):
            return ("move", middles[k][0]), middles[k][1]
        if kind == "add" and k < len(adds):                 # (a gable: «+» makes it a water)
            return ("water",) + adds[k][:2], adds[k][2]
        if kind == "sub" and k < len(subs):                 # (a water: «−» takes it away)
            return ("gable",) + subs[k][:2], subs[k][2]
        return None

    def pointer_move(self, x, y, modifiers):
        if not self.blocks:
            return
        if self._drag is not None:
            self._drag_to(x, y)
            return
        found = self._grip(x, y)
        if found is not None:
            grip, at = found
            side = t("blockside." + core_blocks.SIDES[grip[2]]) if grip[0] in ("side", "water", "gable") else ""
            self.viewport.show_tip(t("tip.roof_block_" + grip[0], s=side), at)
            return
        dim = self.viewport.temp_dim_at(x, y)
        self.viewport.show_temp_dims(self._dims, active=self._active, hover=dim)
        self.viewport.show_tip("", None)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._drag is not None:
                self._drag = None
                self._show()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT or not self.blocks:
            return
        found = self._grip(x, y)
        dim = self.viewport.temp_dim_at(x, y)
        if found is not None and dim is not None:          # (0.386) a box over a grip: the box, unless right on it
            gx, gy = self.viewport.project(found[1])
            if np.hypot(gx - x, gy - y) > GRIP_FIRST_PX:
                found = None
        if found is not None:
            grip, point = found
            if grip[0] in ("water", "gable"):              # (0.386) «+» / «−»: a water made, a water taken away
                self._set_water(grip[1], grip[2], grip[0] == "water")
                return
            self._drag = {"kind": grip[0], "block": grip[1], "side": grip[2] if grip[0] != "move" else None,
                          "base": point.copy(), "press": (float(x), float(y)), "target": None}
            self.host.set_hint(self.hint())
            return
        if dim is not None:
            self._active = dim
            self._show()
            return
        self._active = None
        k = self._block_under_mouse(x, y)
        mods = modifiers or ()
        if k is None:
            if not ("Shift" in mods or "Control" in mods):
                self.chosen = set()
        elif "Shift" in mods or "Control" in mods:
            self.chosen ^= {k}
        else:
            self.chosen = {k}
        self._show()
        if k is not None:
            self.host.message(t("info.roof_blocks_chosen", n=len(self.chosen),
                                b=", ".join(str(i + 1) for i in sorted(self.chosen))))

    def pointer_up(self, x, y, button, modifiers):
        drag, self._drag = self._drag, None
        if drag is None or button != LEFT:
            return
        if not moved_enough(drag["press"], (x, y)) or drag["target"] is None:
            self._show()                                # (a click on a handle: nothing moves)
            return
        self._drop(drag)

    def _drag_to(self, x, y):
        drag = self._drag
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, drag["base"], Z_UP)
        if p is None:
            p = ray_plane(origin, direction, drag["base"], -Z_UP)
        if p is None:
            return
        drag["target"] = p
        blocks = self._dragged(drag)
        segs = []
        for i, b in enumerate(blocks):
            if i not in self.chosen and i != drag["block"]:
                continue
            z = self.level + min(b.eave)
            ring = [np.array((cx, cy, z)) for cx, cy in core_blocks.rect(b)]
            for a, c in zip(ring, ring[1:] + ring[:1]):
                segs += [a, c]
        self.viewport.show_lines(segs, [PREVIEW] * len(segs))
        d = p - drag["base"]
        if drag["kind"] == "corner":                    # (0.386) its new size
            b = blocks[drag["block"]]
            text = "{} × {}".format(_fmt(b.width), _fmt(b.depth))
        elif drag["kind"] == "side":
            text = _fmt(abs(float(np.dot(d[:2], core_blocks.side_way(self.blocks[drag["block"]], drag["side"])[0]))))
        else:
            text = _fmt(float(np.linalg.norm(d[:2])))
        self.viewport.show_tip(text, p)
        self.host.set_vcb(text)

    def _dragged(self, drag):
        """The blocks as the drag puts them: a side stretched (that block), (0.386) a corner's two sides — the block
        scaled, the opposite corner staying —, or the chosen ones moved."""
        d = drag["target"] - drag["base"]
        blocks = list(self.blocks)
        if drag["kind"] in ("side", "corner"):
            i = drag["block"]
            for k in ((drag["side"],) if drag["kind"] == "side" else CORNER_SIDES[drag["side"]]):
                out, _half = core_blocks.side_way(blocks[i], k)
                size = blocks[i].depth if k in (0, 2) else blocks[i].width
                s = max(float(np.dot(d[:2], out)), core_blocks.MIN_SIZE - size)
                blocks[i] = core_blocks.stretched(blocks[i], k, s)
        else:
            group = self.chosen | {drag["block"]}
            for i in group:
                b = blocks[i]
                blocks[i] = core_blocks.replace(b, cx=b.cx + float(d[0]), cy=b.cy + float(d[1]))
        return blocks

    def _drop(self, drag):
        self.host.set_vcb("")                           # (the drag's distance, not a height to keep showing)
        blocks = self._dragged(drag)
        if drag["kind"] == "side":                      # (put on a wall: out to its outer face)
            blocks[drag["block"]] = bim.fit_block_to_walls(self.doc, blocks[drag["block"]], only=(drag["side"],))
            text = t("info.roof_block_side", d=self.viewport.tip_text, n=drag["block"] + 1)
        elif drag["kind"] == "corner":                  # (0.386: its two sides, on walls too)
            blocks[drag["block"]] = bim.fit_block_to_walls(self.doc, blocks[drag["block"]],
                                                           only=CORNER_SIDES[drag["side"]])
            b = blocks[drag["block"]]
            text = t("info.roof_block_scaled", n=drag["block"] + 1, w=_fmt(b.width), d=_fmt(b.depth))
        else:
            text = t("info.roof_blocks_moved", n=len(self.chosen | {drag["block"]}), d=self.viewport.tip_text)
        self._save(blocks, text)

    # ------------------------------------------------------------ the changes

    def _save(self, blocks, text):
        bad = next((core_blocks.problem(b) for b in blocks if core_blocks.problem(b)), None)
        if bad:
            self.host.message(t("err.edit_refused", e=t("refuse." + bad)), warning=True)
            self._show()
            return False
        try:
            bim.set_roof_blocks(self.doc, self.guid, blocks, world=True)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self._load()
            self._show()
            return False
        self.host.message(text)
        return True

    def _set_water(self, i, k, on):
        """(0.386) Side k of block i a water (the «+» of a gable) or a gable (the «−» of a water)."""
        b = self.blocks[i]
        water = list(b.water)
        water[k] = bool(on)
        blocks = list(self.blocks)
        blocks[i] = core_blocks.replace(b, water=tuple(water))
        side = t("blockside." + core_blocks.SIDES[k])
        self._save(blocks, t("info.roof_block_water" if on else "info.roof_block_gable", s=side, n=i + 1))

    def typed(self, text):
        """A height typed (Enter): over the dimension clicked — a water's eave, a block's height — or, none clicked,
        the chosen blocks' height (their lowest eave; all their eaves go up or down together)."""
        value = parse_length(text)
        if value is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        blocks = list(self.blocks)
        key = self._active.key if self._active is not None else ("height", None)
        if key[0] == "eave":
            _w, i, k = key
            eaves = list(blocks[i].eave)
            eaves[k] = float(value) + self.floor - self.level
            blocks[i] = core_blocks.replace(blocks[i], eave=tuple(eaves))
            text = t("info.roof_block_eave", s=t("blockside." + core_blocks.SIDES[k]), n=i + 1, h=_fmt(float(value)))
        else:
            group = [key[1]] if key[1] is not None else sorted(self.chosen)
            for i in group:
                b = blocks[i]
                shift = float(value) + self.floor - (self.level + min(b.eave))
                blocks[i] = core_blocks.replace(b, eave=tuple(e + shift for e in b.eave))
            text = t("info.roof_block_height", n=", ".join(str(i + 1) for i in group), h=_fmt(float(value)))
        self._active = None
        self._save(blocks, text)

    def delete(self):
        if not self.chosen:
            self.host.message(t("info.roof_blocks_pick_first"), warning=True)
            return
        if len(self.chosen) >= len(self.blocks):
            self.host.message(t("err.roof_blocks_last"), warning=True)
            return
        gone = sorted(self.chosen)
        blocks = [b for i, b in enumerate(self.blocks) if i not in self.chosen]
        self.chosen = set()
        self._save(blocks, t("info.roof_blocks_deleted", n=len(gone)))

    def cancel(self):
        self._drag = self._active = None
        self.viewport.clear_overlays()
        self._show()
