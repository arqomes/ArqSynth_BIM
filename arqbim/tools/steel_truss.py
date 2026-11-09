"""(0.507) The «Treliça» tool: a steel truss with two clicks — its two supports, seen from above — and its chords,
verticals and diagonals made at once (core/steel_truss). On the contextual bar: its kind (Pratt, Howe, Warren), its
height, its panels' length, its bottom chord's height over the level, the chords' and the web's types."""

import numpy as np

from ..core import steel_truss as core_truss
from ..i18n import t
from ..ifc import catalog
from ..model import bim
from .base import LEFT, RIGHT, Option
from .bim_draw import MIN_LENGTH, PREVIEW, _fmt, _name, _PointTool, drawing_dims, length_option, show_snap
from .steel_shed import _steel


class SteelTrussTool(_PointTool):
    name = "steel_truss"
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.chain"

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.types = {"chord": "pilar_shs150", "web": "contrav_chs76"}
        self.kind = "pratt"
        self.height, self.panel, self.elevation = 1.2, 1.5, 3.0
        self._start = self._end = None

    def options(self):
        steel = _steel()
        opts = [Option("kind", t("ctx.truss_kind"), "choice", self.kind,
                       tuple((k, t("truss." + k)) for k in core_truss.KINDS))]
        for role in ("chord", "web"):
            key = self.types[role] if self.types[role] in catalog.BY_KEY else (steel[0].key if steel else "")
            opts.append(Option("type_" + role, t("ctx.truss_" + role), "choice", key,
                               tuple((s.key, _name(s)) for s in steel)))
        opts += [length_option("height", "ctx.truss_height", self.height),
                 length_option("panel", "ctx.truss_panel", self.panel),
                 length_option("elevation", "ctx.truss_elevation", self.elevation)]
        return opts

    def set_option(self, key, value):
        if key.startswith("type_") and value in catalog.BY_KEY:
            self.types[key[5:]] = value
        elif key == "kind" and value in core_truss.KINDS:
            self.kind = value
        elif key in ("height", "panel") and float(value) > 0.1:
            setattr(self, key, float(value))
        elif key == "elevation" and float(value) >= 0.0:
            self.elevation = float(value)
        self.host.set_hint(self.hint())

    def hint(self):
        return t("hint.truss_end") if self._start is not None else t("hint.truss_start")

    def vcb_title(self):
        return t("vcb.length")

    def _lines(self, end):
        """The truss's lines as it would be made to `end` (its preview), or []."""
        try:
            truss = core_truss.layout(self._start, end, self.kind, self.height, self.panel, self.elevation)
        except ValueError:
            return []
        return [(p.start, p.end) for p in truss.pieces]

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, self.doc.work_level(), self._start, modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        if self._start is None:
            show_snap(self.viewport, snap, p)
            return
        self._end = p
        lines = self._lines(p)
        if not lines:
            return
        segs = [c for a, b in lines for c in (a, b)]
        self.viewport.show_lines(segments=segs, colors=[PREVIEW] * len(segs))
        drawing_dims(self.viewport, self._start, p)
        d = p - self._start
        d[2] = 0.0
        self.host.set_vcb(_fmt(float(np.linalg.norm(d))))

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
        span = float(np.linalg.norm(d))
        if span < max(MIN_LENGTH, 1.0):
            return
        specs = {role: catalog.BY_KEY.get(key) for role, key in self.types.items()}
        if any(spec is None or not getattr(spec, "section", None) for spec in specs.values()):
            self.host.message(t("info.shed_types"), warning=True)
            return
        made = bim.steel_truss(self.doc, self._start, self._start + d, specs["chord"], specs["web"],
                               storey=self.doc.active_storey, kind=self.kind, height=self.height, panel=self.panel,
                               elevation=self.elevation)
        self.host.message(t("info.truss", what=t("truss." + self.kind), l=_fmt(span),
                            n=core_truss.panels_for(span, self.panel), pieces=len(made)))
        self.cancel()

    def cancel(self):
        self._start = self._end = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    def deactivate(self):
        self.cancel()
        super().deactivate()
