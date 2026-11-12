"""(0.556, PLANO.md «Gerador de formas orgânicas», step 3) «Mastros e apoios»: on an organic form selected, a click
puts a mast (a high point), a support (a low point, down to the outline's plane) or — two clicks — a ridge or a
valley; dragging a mast's head up or down changes its height, the form found again as it moves; the right button on
one takes it away. The bar: what the click puts, its height, a mast's head, the edges held or free (a sail)."""

import time

import numpy as np

from ..core import param_surface as ps
from ..core.units import format_length
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, Tool
from .bim_draw import length_option

KINDS = ("mastro", "apoio", "cumeeira", "vale")
KIND_TEXT = {"mastro": "Mastro (ponto alto)", "apoio": "Apoio (ponto baixo)", "cumeeira": "Cumeeira (2 cliques)",
             "vale": "Vale (2 cliques)"}
MAST = (0.95, 0.45, 0.10, 1.0)          # the masts and ridges (orange), the supports and valleys (blue)
SUPPORT = (0.15, 0.45, 0.90, 1.0)
GRAB_PX = 14
PREVIEW_EVERY = 0.12                    # s: the form found again at most this often while a head is dragged


def _fmt(v):
    return format_length(v, decimal_sep())


class OrganicPointsTool(Tool):
    name = "organic_points"
    title = "act.organic_points"
    placement = True

    def __init__(self, host):
        super().__init__(host)
        self.kind, self.height, self.radius = "mastro", 4.0, 0.3
        self.guid = None
        self.first = None                 # a ridge's / valley's first click (u, v)
        self.drag = None                  # ("point" | "line", index) being dragged
        self.data = None                  # the definition being changed (a copy)
        self._shown_at = 0.0

    # ------------------------------------------------------------ the bar
    def options(self):
        s = (self.data or {}).get("surface") or {}
        return [Option("kind", "Clique põe", "choice", self.kind, tuple((k, KIND_TEXT[k]) for k in KINDS)),
                length_option("height", "ctx.organic_height", self.height),
                length_option("radius", "ctx.organic_radius", self.radius),
                Option("edges", "Bordos", "choice", "livres" if s.get("free_edges") else "presos",
                       (("presos", "Presos ao contorno"), ("livres", "Livres (vela)")))]

    def set_option(self, key, value):
        if key == "kind" and value in KINDS:
            self.kind, self.first = value, None
            if value == "apoio" and self.height > 0:
                self.height = 0.0
        elif key == "height":
            self.height = float(value)
        elif key == "radius" and value > 0:
            self.radius = float(value)
        elif key == "edges" and self.data is not None:
            self.data["surface"]["free_edges"] = value == "livres"
            self._commit()
        self.host.set_hint(self.hint())

    def hint(self):
        if self.guid is None:
            return "Escolha primeiro uma forma orgânica (Massa e Estudos ▸ Forma orgânica)."
        if self.kind in ("cumeeira", "vale"):
            return ("Clique no fim da {} (ou botão direito para largar)." if self.first is not None else
                    "Clique no início da {}.").format(self.kind)
        return ("Clique para pôr um {}; arraste a cabeça de um para mudar a altura; botão direito num deles "
                "tira-o.").format(self.kind)

    # ------------------------------------------------------------ the form selected
    def activate(self):
        super().activate()
        self.guid, self.data, self.first, self.drag = None, None, None, None
        for guid in sorted(self.viewport.selection, key=str):
            try:
                if self.doc.ifc.kind_of(guid) == "param_surface":
                    data = self.doc.ifc.surface_definition(guid)
                    if (data.get("surface") or {}).get("op") == "organic":
                        self.guid, self.data = guid, data
                        break
            except Exception:  # (not of the IFC)
                continue
        if self.guid is None:
            self.host.message(self.hint(), warning=True)
        self.host.set_hint(self.hint())
        self._show()

    def _frame(self):
        """(placement (4, 4), o, x, y, n) — the outline's plane in the element's coordinates."""
        m = self.doc.ifc._placement_si(self.doc.ifc.by_guid(self.guid))
        s = self.data["surface"]
        curve = next(c for c in self.data["curves"] if c["id"] == s["boundary"])
        pts, _closed = ps.sample_curve(curve, {})
        o, x, y, n = ps.outline_frame(pts)
        return m, o, x, y, n

    def _world(self, u, v, h):
        m, o, x, y, n = self._frame()
        local = o + x * u + y * v + n * h
        return (m @ np.append(local, 1.0))[:3]

    def _plane_at(self, sx, sy):
        """(u, v) of the outline's plane under the mouse, or None."""
        if self.guid is None:
            return None
        m, o, x, y, n = self._frame()
        origin, direction = self.viewport.ray(sx, sy)
        inv = np.linalg.inv(m)
        lo = (inv @ np.append(origin, 1.0))[:3]
        ld = inv[:3, :3] @ direction
        den = float(ld @ n)
        if abs(den) < 1e-9:
            return None
        k = float((o - lo) @ n) / den
        if k <= 0:
            return None
        p = lo + ld * k - o
        return float(p @ x), float(p @ y)

    def _height_at(self, sx, sy, u, v):
        """The height along the plane's normal of the point of the upright through (u, v) nearest the mouse's ray."""
        base = self._world(u, v, 0.0)
        top = self._world(u, v, 1.0)
        axis = top - base
        origin, direction = self.viewport.ray(sx, sy)
        w0 = base - origin
        a, b, c = axis @ axis, axis @ direction, direction @ direction
        d, e = axis @ w0, direction @ w0
        den = a * c - b * b
        if abs(den) < 1e-12:
            return None
        return float((b * e - c * d) / den)

    def _heads(self):
        """[(("point" | "line", index, end), world point of its head)]."""
        s = self.data["surface"]
        out = []
        for k, q in enumerate(s.get("points") or ()):
            out.append((("point", k, None), self._world(q["u"], q["v"], q["h"])))
        for k, q in enumerate(s.get("lines") or ()):
            for end in ("a", "b"):
                out.append((("line", k, end), self._world(q[end][0], q[end][1], q["h"])))
        return out

    def _head_at(self, sx, sy):
        best = None
        for key, p in self._heads():
            px = self.viewport.project(p)
            if np.all(np.isfinite(px)):
                d = float(np.hypot(px[0] - sx, px[1] - sy))
                if d <= GRAB_PX and (best is None or d < best[0]):
                    best = (d, key)
        return None if best is None else best[1]

    # ------------------------------------------------------------ the picture
    def _show(self, cursor=None, form=True):
        vp = self.viewport
        if self.guid is None:
            vp.show_volume([], segments=[], colors=[])
            return
        segs, colors = [], []
        s = self.data["surface"]
        for q in s.get("points") or ():
            col = MAST if q.get("kind", "mastro") == "mastro" else SUPPORT
            segs += [tuple(self._world(q["u"], q["v"], 0.0)), tuple(self._world(q["u"], q["v"], q["h"]))]
            colors += [col, col]
        for q in s.get("lines") or ():
            col = MAST if q.get("kind") == "cumeeira" else SUPPORT
            segs += [tuple(self._world(q["a"][0], q["a"][1], q["h"])), tuple(self._world(q["b"][0], q["b"][1], q["h"]))]
            colors += [col, col]
        if cursor is not None:
            u, v = cursor
            h = self.height
            col = MAST if self.kind in ("mastro", "cumeeira") else SUPPORT
            if self.first is not None:
                segs += [tuple(self._world(self.first[0], self.first[1], h)), tuple(self._world(u, v, h))]
            else:
                segs += [tuple(self._world(u, v, 0.0)), tuple(self._world(u, v, h))]
            colors += [col, col]
        tris = []
        if form:
            try:
                m = self.doc.ifc._placement_si(self.doc.ifc.by_guid(self.guid))
                verts, tr = ps.Surface(self.data).triangles()
                verts = (m @ np.column_stack((verts, np.ones(len(verts)))).T).T[:, :3]
                tris = verts[tr] if len(tr) else []
            except ValueError as exc:
                self.host.set_vcb(str(exc)[:80])
        vp.show_volume(tris, segments=segs, colors=[c for c in colors] or [PREVIEW])

    # ------------------------------------------------------------ the mouse
    def pointer_move(self, x, y, modifiers):
        if self.guid is None:
            return
        if self.drag is not None:
            kind, k, end = self.drag
            s = self.data["surface"]
            q = s["points"][k] if kind == "point" else s["lines"][k]
            u, v = (q["u"], q["v"]) if kind == "point" else q[end]
            h = self._height_at(x, y, u, v)
            if h is not None:
                q["h"] = round(h, 3)
                self.host.set_vcb("altura " + _fmt(q["h"]))
                now = time.monotonic()
                if now - self._shown_at >= PREVIEW_EVERY:      # (the form found again: not at every pixel)
                    self._shown_at = now
                    self._show()
            return
        uv = self._plane_at(x, y)
        if uv is not None:
            self.host.set_vcb("{} · {}".format(_fmt(uv[0]), _fmt(uv[1])))
        self._show(cursor=uv, form=False)

    def pointer_down(self, x, y, button, modifiers):
        if self.guid is None:
            return
        head = self._head_at(x, y)
        s = self.data["surface"]
        if button == RIGHT:
            if head is not None:                              # (that one taken away)
                kind, k, _end = head
                (s["points"] if kind == "point" else s["lines"]).pop(k)
                self._commit()
            elif self.first is not None:
                self.first = None
                self._show()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT:
            return
        if head is not None:
            self.drag = head
            self._shown_at = 0.0
            return
        uv = self._plane_at(x, y)
        if uv is None:
            return
        if not s.get("points") and not s.get("lines"):        # (a membrane's own mast kept: joined, not replaced)
            s["points"] = ps.implicit_points(self.data)
        if self.kind in ("mastro", "apoio"):
            s.setdefault("points", []).append({"u": round(uv[0], 3), "v": round(uv[1], 3), "h": round(self.height, 3),
                                               "r": round(self.radius, 3), "kind": self.kind})
            self._commit()
        elif self.first is None:
            self.first = uv
            self.host.set_hint(self.hint())
        else:
            s.setdefault("lines", []).append({"a": [round(self.first[0], 3), round(self.first[1], 3)],
                                              "b": [round(uv[0], 3), round(uv[1], 3)], "h": round(self.height, 3),
                                              "kind": "cumeeira" if self.kind == "cumeeira" else "vale"})
            self.first = None
            self._commit()

    def pointer_up(self, x, y, button, modifiers):
        if self.drag is not None:
            self.drag = None
            self._commit()

    def _commit(self):
        """The definition as changed now put in the model (one undo step) — refused: as it was."""
        try:
            bim.set_param_surface(self.doc, self.guid, self.data)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
        self.data = self.doc.ifc.surface_definition(self.guid)
        self.host.set_hint(self.hint())
        self._show(form=False)                              # (the form itself is the model's now)

    def delete(self):
        """Backspace / Delete: the last mast, support or line put taken away."""
        if self.guid is None:
            return False
        s = self.data["surface"]
        if s.get("lines"):
            s["lines"].pop()
        elif s.get("points"):
            s["points"].pop()
        else:
            return False
        self._commit()
        return True

    def cancel(self):
        self.first, self.drag = None, None
        self.viewport.clear_overlays()
        self.host.set_vcb("")
