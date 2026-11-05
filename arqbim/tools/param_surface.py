"""Parametric surface (0.395), the addon's «Superfícies Paramétricas»: a curved surface made of curves of the model —
lines, arcs, Bézier curves, freehand lines, a face's outline — picked one by one (those selected when the tool starts
are taken at once), shown as it will be at each pick; Enter makes it. Which surface they make: the one asked for on the
bar (loft through sections, 4 edges, revolution, extrusion, sweep, cap over an outline) or, «Automática», the one they
make (1 closed: a cap; 1 open: an extrusion; 2 or more: a loft; 4 that touch at their ends: 4 edges). «Fórmula» needs
no curve: two corners on the floor, its heights a formula of u and v.

What it is used for («Uso»: a structure, a roof, a façade, a canopy) sets its IFC class; a first construction can be
chosen here (casca, gridshell, painéis…) — the rest, its modifiers and its numbers, in the Properties. The surface
follows its curves when they are edited later (model/document.Document._follow_curves)."""

import numpy as np

from ..core import param_surface as ps
from ..core import surface_build as sb
from ..core.units import format_length
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import AXIS_V, PREVIEW
from .base import LEFT, RIGHT, Option, Tool, infer_point, level_plane, show_snap
from .bim_draw import length_option

OPS = ("auto", "loft", "coons", "revolve", "extrude", "sweep", "patch", "grid")
USAGES = ("estrutura", "cobertura", "fachada", "pala")
BUILDS = ("none", "shell", "gridshell", "ribs", "slats", "weave", "panels", "spider")
DIVISIONS = ("12x8", "16x12", "24x16", "32x20", "48x32", "64x40")
ANGLES = ("90", "180", "270", "360")
PICKED = (0.95, 0.45, 0.10, 1.0)          # the curves picked (orange), the one under the mouse in green


def _fmt(v):
    return format_length(v, decimal_sep())


class ParamSurfaceTool(Tool):
    name = "param_surface"
    on_storey = True
    placement = True
    keys_help = "keys.param_surface"

    def __init__(self, host):
        super().__init__(host)
        self.op, self.usage, self.build = "auto", "estrutura", "none"
        self.divisions = "24x16"
        self.rise, self.height, self.angle = 2.5, 3.0, "360"
        self.picks = []                   # [(sketch id, world point near the chain)]
        self.corner = None                # «grid»: its first corner

    # ------------------------------------------------------------ the bar

    def options(self):
        out = [Option("op", t("ctx.surface_op"), "choice", self.op, tuple((k, t("surface.op." + k)) for k in OPS)),
               Option("usage", t("ctx.surface_usage"), "choice", self.usage,
                      tuple((k, t("surface.usage." + k)) for k in USAGES)),
               Option("build", t("ctx.surface_build"), "choice", self.build,
                      tuple((k, t("surface.build." + k)) for k in BUILDS)),
               Option("divisions", t("ctx.surface_divisions"), "choice", self.divisions,
                      tuple((k, k.replace("x", " × ")) for k in DIVISIONS))]
        if self.op in ("auto", "patch", "grid"):
            out.append(length_option("rise", "ctx.surface_rise", self.rise))
        if self.op in ("auto", "extrude"):
            out.append(length_option("height", "ctx.surface_height", self.height))
        if self.op == "revolve":
            out.append(Option("angle", t("ctx.surface_angle"), "choice", self.angle,
                              tuple((a, a + "°") for a in ANGLES)))
        return out

    def set_option(self, key, value):
        if key == "op" and value in OPS:
            self.op = value
            self.corner = None
        elif key == "usage" and value in USAGES:
            self.usage = value
        elif key == "build" and value in BUILDS:
            self.build = value
        elif key == "divisions" and value in DIVISIONS:
            self.divisions = value
        elif key == "rise" and value >= 0.0:
            self.rise = float(value)
        elif key == "height" and value > 0.0:
            self.height = float(value)
        elif key == "angle" and value in ANGLES:
            self.angle = value
        self.host.set_hint(self.hint())
        self._show()

    def hint(self):
        if self.op == "grid":
            return t("hint.param_surface.grid")
        return t("hint.param_surface.pick", op=t("surface.op." + self.op).lower(), n=len(self.picks),
                 need=t("need.param_surface." + self.op))

    def activate(self):
        super().activate()
        vp = self.viewport
        chosen = [i for i in list(getattr(vp, "selection", ())) + list(getattr(vp, "line_selection", {}) or {})
                  if self.doc.get(i) is not None and not self.doc.get(i).is_bim]
        self.picks = [(i, None) for i in dict.fromkeys(chosen)]
        self.host.set_hint(self.hint())
        self._show()

    # ------------------------------------------------------------ the curves

    def _divisions(self):
        u, v = self.divisions.split("x")
        return int(u), int(v)

    def _fields(self):
        return {"rise": self.rise, "direction": [0.0, 0.0, self.height], "angle": float(self.angle)}

    def _chains(self):
        from ..model.surface_curves import chain_near, sketch_chains
        out = []
        for sid, near in self.picks:
            sk = self.doc.get(sid)
            if sk is None or sk.is_bim:
                continue
            chain = chain_near(sk, near) if near is not None else (sketch_chains(sk) or [None])[0]
            if chain is not None:
                out.append(chain)
        return out

    def _curve_at(self, x, y):
        """(sketch id, a world point on the chain under the mouse) or None."""
        hit = self.viewport.line_at(x, y)
        if hit is not None:
            sid, k = hit
            sk = self.doc.get(sid)
            a, b = sk.mesh.lines[k]
            m = np.asarray(sk.matrix, float)
            mid = (np.asarray(sk.mesh.verts[a], float) + np.asarray(sk.mesh.verts[b], float)) / 2.0
            return sid, m[:3, :3] @ mid + m[:3, 3]
        oid = self.viewport.pick_object(x, y)
        obj = self.doc.get(oid) if oid is not None else None
        if obj is None or obj.is_bim:
            return None
        found = self.viewport.pick_point(x, y)
        return oid, (found[2] if found is not None and found[0] == oid else None)

    def _definition(self):
        chains = self._chains()
        if not chains:
            return None
        op = None if self.op == "auto" else self.op
        data = ps.from_curves([(p, c, None) for p, c in chains], op=op, divisions=self._divisions(),
                              **self._fields())
        if data["surface"]["op"] == "revolve":
            p0 = data["curves"][0]["points"][0]
            data["surface"]["origin"] = [p0[0], p0[1]]
        return data

    # ------------------------------------------------------------ the preview

    @staticmethod
    def _segments(points, closed):
        p = np.asarray(points, float)
        if closed:
            p = np.vstack((p, p[:1]))
        segs = []
        for a, b in zip(p, p[1:]):
            segs += [tuple(a), tuple(b)]
        return segs

    def _show(self, hover=None, cursor=None):
        vp = self.viewport
        segs, colors, tris = [], [], []
        if self.op == "grid":
            if self.corner is not None and cursor is not None:
                (x0, y0, z), (x1, y1) = self.corner, cursor[:2]
                ring = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
                segs = self._segments(ring, True)
                colors = [PREVIEW] * len(segs)
                tris = self._grid_preview(x0, y0, x1, y1, z)
            vp.show_volume(tris, segments=segs, colors=colors)
            return
        for pts, closed in self._chains():
            s = self._segments(pts, closed)
            segs += s
            colors += [PICKED] * len(s)
        if hover is not None:
            from ..model.surface_curves import chain_near
            sk = self.doc.get(hover[0])
            chain = chain_near(sk, hover[1]) if sk is not None and hover[1] is not None else None
            if chain is not None:
                s = self._segments(*chain)
                segs += s
                colors += [AXIS_V] * len(s)
        message = ""
        try:
            data = self._definition()
            if data is not None:
                surface = ps.Surface(data)
                verts, tr = surface.triangles()
                tris = verts[tr] if len(tr) else []
                message = t("surface.op." + data["surface"]["op"]) + " · " + "{:.1f} m²".format(
                    surface.area()).replace(".", decimal_sep())
        except ValueError as exc:
            message = str(exc)[:80]
        vp.show_volume(tris, segments=segs, colors=colors)
        self.host.set_vcb(message)

    def _grid_preview(self, x0, y0, x1, y1, z):
        data = self._grid_definition(x0, y0, x1, y1)
        if data is None:
            return []
        try:
            verts, tr = ps.Surface(data).triangles()
        except ValueError:
            return []
        verts = verts + np.array((min(x0, x1), min(y0, y1), z))
        return verts[tr] if len(tr) else []

    def _grid_definition(self, x0, y0, x1, y1):
        w, d = abs(x1 - x0), abs(y1 - y0)
        if w < 0.1 or d < 0.1:
            return None
        data = ps.default_definition("grid", t("elem.param_surface"))
        data["inputs"] = {"L": round(w, 4), "W": round(d, 4), "H": round(self.rise, 4)}
        data["surface"]["u"], data["surface"]["v"] = self._divisions()
        return data

    # ------------------------------------------------------------ the mouse

    def _floor_point(self, x, y, modifiers=()):
        level = self.doc.work_level()
        found, _snap, _hit = infer_point(self.viewport, x, y, None, modifiers, flat=True, plane=level_plane(level))
        if found is not None:
            show_snap(self.viewport, found)
            p = np.asarray(found.point, float)
            return np.array((p[0], p[1], level))
        origin, direction = self.viewport.ray(x, y)
        if abs(direction[2]) < 1e-9:
            return None
        s = (level - origin[2]) / direction[2]
        return None if s <= 0 else np.array((origin[0] + direction[0] * s, origin[1] + direction[1] * s, level))

    def pointer_move(self, x, y, modifiers):
        if self.op == "grid":
            p = self._floor_point(x, y, modifiers)
            if p is not None:
                self._show(cursor=p)
            return
        hit = self._curve_at(x, y)
        if hit is not None:
            picked = any(sid == hit[0] for sid, _n in self.picks)
            self.viewport.show_tip(t("tip.surface_unpick" if picked else "tip.surface_pick"),
                                   hit[1] if hit[1] is not None else self.viewport.ray(x, y)[0])
        self._show(hover=hit)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self.picks or self.corner is not None:
                self.cancel()
                return
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        if self.op == "grid":
            p = self._floor_point(x, y, modifiers)
            if p is None:
                return
            if self.corner is None:
                self.corner = (float(p[0]), float(p[1]), float(p[2]))
                return
            x0, y0, z = self.corner
            self.corner = None
            data = self._grid_definition(x0, y0, p[0], p[1])
            if data is not None:
                self._finish(lambda: bim.add_param_surface(self.doc, self._with_build(data),
                                                           (min(x0, p[0]), min(y0, p[1]), z),
                                                           storey=self.doc.active_storey, usage=self.usage))
            return
        hit = self._curve_at(x, y)
        if hit is None:
            return
        before = len(self.picks)
        self.picks = [(sid, n) for sid, n in self.picks if sid != hit[0]]
        if len(self.picks) == before:
            self.picks.append(hit)
        self.host.set_hint(self.hint())
        self._show(hover=hit)

    def _with_build(self, data):
        if self.build != "none":
            data["build"] = {self.build: dict(sb.TEMPLATES[self.build])}
        return data

    def enter(self):
        if self.op == "grid" or not self.picks:
            return
        picks = list(self.picks)
        op = None if self.op == "auto" else self.op
        build = None if self.build == "none" else {self.build: dict(sb.TEMPLATES[self.build])}
        self._finish(lambda: bim.surface_from_sketches(self.doc, picks, op=op, usage=self.usage,
                                                       divisions=self._divisions(), build=build, **self._fields()))

    def _finish(self, make):
        try:
            guid = make()
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self.picks, self.corner = [], None
        self.viewport.clear_overlays()
        self.host.set_vcb("")
        info = self.doc.ifc.describe(guid)["params"]
        self.host.message(t("info.param_surface", name=self.doc.get(guid).name if self.doc.get(guid) else "",
                            op=t("surface.op." + info["definition"]["surface"]["op"]).lower(),
                            a="{:.1f}".format(info["summary"].get("area", 0.0)).replace(".", decimal_sep())))
        self.host.set_tool("select")
        self.viewport.set_selection({guid})

    def delete(self):
        """Backspace / Delete: the last curve picked taken back."""
        if self.picks:
            self.picks.pop()
            self.host.set_hint(self.hint())
            self._show()
            return True
        return False

    def cancel(self):
        self.picks, self.corner = [], None
        self.viewport.clear_overlays()
        self.host.set_vcb("")
        self.host.set_hint(self.hint())
