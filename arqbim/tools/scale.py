"""Scale tool (0.153, Phase 7, step 1 — as Revit's Scale): with sketches selected, a click gives the base point (it
stays where it is); then the factor typed — "2", "0,5", or one per axis "1;1;2" — and Enter, or two clicks: a
point of the selection and where it goes (the factor their distances' ratio from the base). The selection's
outline is shown scaled meanwhile. BIM elements are parametric: they are left out (their types, sizes and
heights say how big they are). (0.206) About the centre, as SketchUp's Ctrl: Ctrl tapped (or the bar's box) — the base
is the selection's middle, a click a point of it and the next where it goes; Ctrl held on the first click does
the same for that once."""

import numpy as np

from ..core.units import parse_lengths
from ..i18n import decimal_sep, t
from ..model.document import ReplaceObjects
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, Tool, infer_point, show_snap

MIN_FACTOR = 1e-3


def scaled_copy(obj, base, factors):
    """A copy of a sketch object scaled about the world point `base` by `factors` (sx, sy, sz, along the world
    axes): its matrix kept, its points (and its holes) moved."""
    new = obj.copy()
    m = np.asarray(obj.matrix, dtype=float)
    inv = np.linalg.inv(m)
    s = np.asarray(factors, dtype=float)
    base = np.asarray(base, dtype=float)

    def move(p):
        w = m[:3, :3] @ np.asarray(p, dtype=float) + m[:3, 3]
        w = base + (w - base) * s
        return inv[:3, :3] @ w + inv[:3, 3]

    mesh = new.mesh.copy()
    mesh.verts = [move(v) for v in mesh.verts]
    mesh.voids = [([move(p) for p in pts], inv[:3, :3] @ ((m[:3, :3] @ np.asarray(vec, float)) * s))
                  for pts, vec in mesh.voids]
    new.mesh = mesh
    return new


class ScaleTool(Tool):
    name = "scale"
    accepts_typing = True
    placement = True

    def __init__(self, host):
        super().__init__(host)
        self._base = None
        self._ref = None
        self.centre = False                        # (0.206) about the selection's middle

    def activate(self):
        self.centre = False
        super().activate()

    def options(self):
        return [Option("centre", t("ctx.scale_centre"), "toggle", self.centre)]

    def set_option(self, key, value):
        if key == "centre" and bool(value) != self.centre:
            self.ctrl_tap()

    def ctrl_tap(self):
        """Ctrl tapped: about the selection's middle, or not (a base point chosen but no point of it yet: chosen
        again)."""
        self.centre = not self.centre
        if self._ref is None:
            self._base = None
            self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.message(t("info.scale_centre_on" if self.centre else "info.scale_centre_off"))

    def _centre(self):
        """The middle of the selected sketches' box (world) — (0.492) or of the volume's."""
        if not self._sketches() and self._volume() is not None:
            lo, hi = self._volume_box()
            return (lo + hi) / 2
        corners = [np.asarray(o.matrix, float)[:3, :3] @ np.asarray(v, float) + np.asarray(o.matrix, float)[:3, 3]
                   for o in self._sketches() for v in o.mesh.verts]
        return (np.min(corners, axis=0) + np.max(corners, axis=0)) / 2 if corners else np.zeros(3)

    def _sketches(self):
        return [self.doc.get(i) for i in sorted(self.viewport.selection)
                if self.doc.get(i) is not None and not self.doc.get(i).is_bim]

    def _volume(self):
        """(0.492) In the Presentation tab, nothing of the model selected: the volume chosen (it is what scales)."""
        mode = getattr(self.host, "presentation_mode", None)
        if mode is None or not mode.active or self.viewport.selection:
            return None
        return mode.chosen_volume()

    def _volume_box(self):
        from ..model import presentation_diagrams as dia
        pts = dia.shape(self._volume())[0]
        return pts.min(axis=0), pts.max(axis=0)

    def hint(self):
        if not self._sketches() and self._volume() is None:
            return t("hint.scale.select")
        if self._base is None:
            return t("hint.scale.centre") if self.centre else t("hint.scale.base")
        return t("hint.scale.target") if self._ref is not None else t("hint.scale.factor")

    def vcb_title(self):
        return t("vcb.factor")

    def _point(self, x, y, modifiers):
        found, _snap, _hit = infer_point(self.viewport, x, y, self._base, modifiers)
        if found is not None:
            return found.point.copy(), found
        origin, direction = self.viewport.ray(x, y)
        if abs(direction[2]) < 1e-9:
            return None, None
        z = 0.0 if self._base is None else float(self._base[2])
        s = (z - origin[2]) / direction[2]
        return (origin + direction * s, None) if s > 0 else (None, None)

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, modifiers)
        if p is None:
            return
        show_snap(self.viewport, snap, p)
        if self._base is not None and self._ref is not None:
            r0 = float(np.linalg.norm(self._ref - self._base))
            if r0 > 1e-9:
                f = float(np.linalg.norm(p - self._base)) / r0
                self._preview((f, f, f))
                self.host.set_vcb("{:.3f}".format(f).replace(".", decimal_sep()))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if not self._sketches() and self._volume() is None:
            self.host.message(t("hint.scale.select"), warning=True)
            return
        p, _snap = self._point(x, y, modifiers)
        if p is None:
            return
        if self._base is None and (self.centre or "Control" in (modifiers or ()) or "Ctrl" in (modifiers or ())):
            self._base = self._centre()            # (0.206: about the middle — the click, a point of it)
            if np.linalg.norm(p - self._base) < 1e-6:
                self._base = None
                return
            self._ref = p
        elif self._base is None:
            self._base = p
        elif self._ref is None:
            if np.linalg.norm(p - self._base) < 1e-6:
                return
            self._ref = p
        else:
            f = float(np.linalg.norm(p - self._base)) / float(np.linalg.norm(self._ref - self._base))
            self._apply((f, f, f))
            return
        self.host.set_hint(self.hint())

    def typed(self, text):
        values = parse_lengths(text, 3)
        if values is None or values[0] is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        if not self._sketches() and self._volume() is None:
            self.host.message(t("hint.scale.select"), warning=True)
            return
        if values[1] is None:
            factors = (values[0],) * 3
        else:
            factors = tuple(v if v is not None else 1.0 for v in values)
        if self._base is None and self.centre:     # (0.206: about its middle)
            self._base = self._centre()
        if self._base is None:                     # (typed first: about the selection's lowest corner)
            corners = [np.asarray(o.matrix, float)[:3, :3] @ np.asarray(v, float) + np.asarray(o.matrix, float)[:3, 3]
                       for o in self._sketches() for v in o.mesh.verts]
            if not corners and self._volume() is not None:      # (0.492: the volume's middle of its base)
                self._base = np.asarray(self._volume()["position"], dtype=float)
            else:
                self._base = np.min(corners, axis=0) if corners else np.zeros(3)
        self._apply(factors)

    def _preview(self, factors):
        volume = self._volume() if not self._sketches() else None
        if volume is not None:                     # (0.492) the volume scaled, its edges
            from ..model import presentation_diagrams as dia
            b, f = np.asarray(self._base, dtype=float), np.asarray(factors, dtype=float)
            m = np.eye(4)
            m[:3, :3], m[:3, 3] = np.diag(f), b - f * b
            segs = [p for edge in dia.outline(dia.transformed(volume, m)) for p in edge]
            self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))
            return
        segs = []
        for o in self._sketches():
            copy = scaled_copy(o, self._base, factors)
            m = copy.matrix
            for a, b in copy.mesh.visible_edges():
                pa = m[:3, :3] @ copy.mesh.verts[a] + m[:3, 3]
                pb = m[:3, :3] @ copy.mesh.verts[b] + m[:3, 3]
                segs += [pa, pb]
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))

    def _apply(self, factors):
        if any(abs(f) < MIN_FACTOR for f in factors):
            self.host.message(t("err.scale_zero"), warning=True)
            return
        volume = self._volume() if not self._sketches() else None
        if volume is not None:                     # (0.492) the Presentation tab's volume
            if self.host.presentation_mode.scale_diagram(volume["id"], self._base, factors):
                self.host.message(t("pmode.dia_scaled", f=" × ".join(
                    "{:g}".format(round(f, 4)).replace(".", decimal_sep())
                    for f in (factors if len(set(factors)) > 1 else factors[:1]))))
            self.cancel()
            return
        sketches = self._sketches()
        scaled = [scaled_copy(o, self._base, factors) for o in sketches]
        self.doc.execute(ReplaceObjects(sketches, scaled, t("cmd.scale")))
        left_out = [i for i in self.viewport.selection if self.doc.get(i) is not None and self.doc.get(i).is_bim]
        text = t("info.scale", f=" × ".join("{:g}".format(round(f, 4)).replace(".", decimal_sep())
                                             for f in (factors if len(set(factors)) > 1 else factors[:1])),
                 n=len(scaled))
        if left_out:
            text += " " + t("info.scale_bim", n=len(left_out))
        self.host.message(text, warning=bool(left_out))
        self.cancel()

    def cancel(self):
        self._base = self._ref = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
