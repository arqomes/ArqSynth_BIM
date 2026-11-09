"""(0.499) The «Pórtico de nave» tool: a steel shed with two clicks — the first line of columns (its start, its end:
the shed's length), its span to the left of it — and its frames, purlins, bracing, mitred knees and base plates made
at once (core/steel_shed). Its sizes and sections on the contextual bar: span, eaves' height, roof slope, frames'
spacing, purlins' spacing; the columns', rafters', purlins' and braces' types; bracing and base plates on or off."""

import numpy as np

from ..i18n import t
from ..ifc import catalog
from ..model import bim
from .base import LEFT, RIGHT, Option
from .bim_draw import MIN_LENGTH, PREVIEW, _fmt, _name, _PointTool, drawing_dims, length_option, show_snap

SLOPES = (3, 5, 6, 8, 10, 12, 15, 20, 25, 30)
Z = np.array((0.0, 0.0, 1.0))


def _steel(kind=None):
    return [s for s in catalog.types() if getattr(s, "section", None) and (kind is None or s.kind == kind)]


class SteelShedTool(_PointTool):
    name = "steel_shed"
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.chain"

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.types = {"column": "pilar_heb200", "rafter": "viga_ipe300", "purlin": "madre_c160",
                      "brace": "contrav_l80"}
        self.span, self.eave, self.slope, self.spacing, self.purlins = 12.0, 6.0, 10, 6.0, 1.5
        self.bracing = self.plates = True
        self.knees = "welded"                  # (0.513) or "bolted": an end plate on each side of the mitre
        self._start = self._end = None

    def options(self):
        steel = _steel()
        opts = []
        for role in ("column", "rafter", "purlin", "brace"):
            key = self.types[role] if self.types[role] in catalog.BY_KEY else (steel[0].key if steel else "")
            opts.append(Option("type_" + role, t("ctx.shed_" + role), "choice", key,
                               tuple((s.key, _name(s)) for s in steel)))
        opts += [length_option("span", "ctx.shed_span", self.span), length_option("eave", "ctx.shed_eave", self.eave),
                 Option("slope", t("ctx.shed_slope"), "choice", self.slope, tuple((a, "{}°".format(a)) for a in SLOPES)),
                 length_option("spacing", "ctx.shed_spacing", self.spacing),
                 length_option("purlins", "ctx.shed_purlins", self.purlins),
                 Option("bracing", t("ctx.shed_bracing"), "choice", self.bracing,
                        ((True, t("rules.yes")), (False, t("rules.no")))),
                 Option("plates", t("ctx.shed_plates"), "choice", self.plates,
                        ((True, t("rules.yes")), (False, t("rules.no")))),
                 Option("knees", t("ctx.shed_knees"), "choice", self.knees,
                        (("welded", t("shed.knees.welded")), ("bolted", t("shed.knees.bolted"))))]
        return opts

    def set_option(self, key, value):
        if key.startswith("type_") and value in catalog.BY_KEY:
            self.types[key[5:]] = value
        elif key in ("span", "eave", "spacing", "purlins") and float(value) > 0.5:
            setattr(self, key, float(value))
        elif key == "slope":
            self.slope = int(value)
        elif key in ("bracing", "plates"):
            setattr(self, key, bool(value))
        elif key == "knees" and value in ("welded", "bolted"):
            self.knees = value
        self.host.set_hint(self.hint())

    def hint(self):
        if self._start is not None:
            return t("hint.shed_end", span=_fmt(self.span))
        return t("hint.shed_start")

    def vcb_title(self):
        return t("vcb.length")

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, self.doc.work_level(), self._start, modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        if self._start is None:
            show_snap(self.viewport, snap, p)
            return
        self._end = p
        d = self._end - self._start
        d[2] = 0.0
        n = float(np.linalg.norm(d))
        if n < 1e-6:
            return
        s = np.cross(Z, d / n) * self.span
        corners = [self._start, self._end, self._end + s, self._start + s]
        segs = [c for i in range(4) for c in (corners[i], corners[(i + 1) % 4])]
        self.viewport.show_polygon(corners, segments=segs, colors=[PREVIEW] * len(segs))
        drawing_dims(self.viewport, self._start, self._end)
        self.host.set_vcb(_fmt(n))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self._start is None:
            p, _snap = self._point(x, y, self.doc.work_level(), modifiers=modifiers)
            if p is not None:
                self._start = p
                self.host.set_hint(self.hint())
            return
        if self._end is not None:
            self._make(self._end)

    def typed(self, text):
        from ..core.units import parse_lengths
        values = parse_lengths(text, 1)
        if values is None or values[0] is None or self._start is None or self._end is None:
            return
        d = self._end - self._start
        d[2] = 0.0
        n = float(np.linalg.norm(d))
        if n > 1e-9:
            self._make(self._start + d / n * values[0])

    def _make(self, end):
        d = np.asarray(end, dtype=float) - self._start
        d[2] = 0.0
        length = float(np.linalg.norm(d))
        if length < max(MIN_LENGTH, 1.0):
            return
        specs = {role: catalog.BY_KEY.get(key) for role, key in self.types.items()}
        if any(spec is None or not getattr(spec, "section", None) for spec in specs.values()):
            self.host.message(t("info.shed_types"), warning=True)
            return
        made = bim.steel_shed(self.doc, self._start, d / length, length, specs["column"], specs["rafter"],
                              specs["purlin"], specs["brace"], storey=self.doc.active_storey, span=self.span,
                              eave=self.eave, slope=float(self.slope), spacing=self.spacing, purlins=self.purlins,
                              bracing=self.bracing, plates=self.plates, knees=self.knees)
        frames = max(2, int(round(length / self.spacing)) + 1)
        self.host.message(t("info.shed", n=frames, l=_fmt(length), s=_fmt(self.span), pieces=len(made)))
        self.cancel()

    def cancel(self):
        self._start = self._end = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    def deactivate(self):
        self.cancel()
        super().deactivate()
