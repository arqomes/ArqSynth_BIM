"""(0.564, PLANO.md «Gerador de revestimentos 3D em IFC», step 3) Revestimento: a finish laid in pieces on any flat
face clicked — a wall's (round its doors and windows), a slab's top or edge, a column's or beam's side, a stair's
tread, a drawing's face. The face under the mouse is shown, the finish and its bond chosen in the bar; a click lays
it (one undo step) and selects it, its layout then all in its Properties. On an element it follows it (a door put in,
the wall longer); the element gone, it goes too. Right click or Esc: Select."""

import numpy as np

from ..core import covering_finishes as cf
from ..core import tiling as tl
from ..core.sketch_geometry import face_world_normal
from ..i18n import lang, refusal, t
from ..model import bim
from .base import LEFT, RIGHT, SNAP_COLORS, Option, Tool

OWN = "do_revestimento"          # the bond of the finish chosen


class CoveringTool(Tool):
    name = "covering"
    keys_help = "keys.covering"

    def __init__(self, host):
        super().__init__(host)
        self.finish = "porcelanico_60x60"
        self.pattern = OWN
        self.origin = "auto"
        self._face = None            # (key, (outline, holes, normal)) of the face under the mouse

    # ------------------------------------------------------------ the bar

    def options(self):
        pt = lang() == "pt"
        finishes = tuple((k, "{} ▸ {}".format(cf.GROUPS[f.group][0 if pt else 1], f.name_pt if pt else f.name_en))
                         for g in cf.GROUPS for k, f in cf.FINISHES.items() if f.group == g)
        patterns = ((OWN, t("covering.own_pattern")),) + tuple((k, v[0 if pt else 1]) for k, v in tl.PATTERNS.items()
                                                               if k != "livre")
        return [Option("finish", t("ctx.covering_finish"), "choice", self.finish, finishes),
                Option("pattern", t("props.cov_pattern"), "choice", self.pattern, patterns),
                Option("origin", t("props.cov_origin"), "choice", self.origin,
                       tuple((k, t("cov.origin." + k)) for k in tl.ORIGINS if k != "ponto"))]

    def set_option(self, key, value):
        if key == "finish" and value in cf.FINISHES:
            self.finish = value
        elif key == "pattern" and (value == OWN or value in tl.PATTERNS):
            self.pattern = value
        elif key == "origin" and value in tl.ORIGINS:
            self.origin = value
        self.host.set_hint(self.hint())

    def layout(self):
        d = {"origin": self.origin}
        if self.pattern != OWN:
            d["pattern"] = self.pattern
        return d

    def hint(self):
        f = cf.finish(self.finish)
        return t("hint.covering", f=f.name_pt if lang() == "pt" else f.name_en)

    def activate(self):
        super().activate()
        chosen = [g for g in self.viewport.selection if self.doc.get(g) is not None and not self.doc.get(g).is_bim]
        if chosen:                                     # (drawings chosen first: covered at once)
            self.cover_chosen(chosen)

    def cover_chosen(self, sketches):
        try:
            made = bim.cover_drawings(self.doc, sketches, self.finish, self.layout())
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return []
        self.viewport.set_selection(set(made))
        self.host.message(t("info.covering_made", n=len(made)))
        return made

    # ------------------------------------------------------------ the mouse

    def _hit(self, x, y):
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None
        obj = self.doc.get(hit[0])
        if obj is None:
            return None
        if obj.is_bim and self.doc.ifc.kind_of(obj.id) == "tiled_covering":
            return None
        n = np.asarray(face_world_normal(obj.matrix, obj.mesh, hit[1]), dtype=float)
        n /= max(np.linalg.norm(n), 1e-12)
        return obj, n, np.asarray(hit[2], dtype=float)

    def _clear(self):
        self._face = None
        self.viewport.show_polygon([])
        self.viewport.show_marker(None)
        self.viewport.show_tip("", None)

    def pointer_move(self, x, y, modifiers):
        found = self._hit(x, y)
        if found is None:
            self._clear()
            return
        obj, n, point = found
        key = (obj.id, tuple(np.round(n, 3)), round(float(n @ point), 3))
        if self._face is None or self._face[0] != key:
            face = bim.covering_face(self.doc, obj.id, point, n)
            self._face = (key, face)
        face = self._face[1]
        if face is None:
            self.viewport.show_polygon([])
            self.viewport.show_marker(point, SNAP_COLORS["on_face"])
            self.viewport.show_tip(t("tip.covering_no_face"), point)
            return
        outline, holes, fn = face
        lift = np.asarray(fn, float) * 0.004
        loops = [np.asarray(outline) + lift] + [np.asarray(h) + lift for h in holes]
        segs = [p for loop in loops for i in range(len(loop)) for p in (loop[i], loop[(i + 1) % len(loop)])]
        self.viewport.show_polygon(loops[0], segments=segs, colors=[SNAP_COLORS["on_face"]] * (len(segs) // 2))
        self.viewport.show_marker(point, SNAP_COLORS["on_face"])
        f = cf.finish(self.finish)
        self.viewport.show_tip(t("tip.covering_here", f=f.name_pt if lang() == "pt" else f.name_en), point)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        found = self._hit(x, y)
        if found is None:
            return
        obj, n, point = found
        try:
            made = bim.cover_face(self.doc, obj.id, point, n, self.finish, self.layout())
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        if made is None:
            self.host.message(t("tip.covering_no_face"), warning=True)
            return
        self._clear()
        self.viewport.set_selection({made})
        p = self.doc.ifc.describe(made)["params"] if hasattr(self.doc.ifc, "describe") else {}
        self.host.message(t("info.covering_one", n=p.get("pieces", 0), c=p.get("cut", 0)))

    def cancel(self):
        self._clear()
