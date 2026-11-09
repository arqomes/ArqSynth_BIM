"""(0.495) The «Peça metálica» tool, as Tekla's Beam and Revit's structural framing: a steel section of the catalogue
between two points — level, sloped or upright — as a beam, a column, a brace, a purlin or another member, by its
insertion point and turned about its line; point by point (each piece goes on from the last), Esc ends. Or bracing
between two columns: a click on each — in X, or one diagonal either way.

Its heights: «pelas cotas» — the start and the end at their own heights above the storey (a level beam: both the same;
a rafter: the end higher) —, or «pelos pontos» — where the points are found in 3D (a column's top, a beam's end), the
work level where none is."""

import numpy as np

from ..core.units import parse_lengths
from ..i18n import t
from ..ifc import catalog
from ..ifc.steel_members import CARDINALS, DEFAULT_CARDINAL, FUNCTIONS
from ..model import bim
from .base import LEFT, RIGHT, Option
from .bim_draw import MIN_LENGTH, PREVIEW, _fmt, _name, _PointTool, drawing_dims, inferred_style, length_option, \
    show_snap

MODES = ("line", "x", "slash", "backslash")
SHAPES = {"x": "x", "slash": "/", "backslash": "\\"}
ROTATIONS = (0, 90, 180, 270)


def steel_types():
    """The steel types to draw with (every kind's: a beam's section may be a brace)."""
    return [s for s in catalog.types() if getattr(s, "section", None)]


class SteelMemberTool(_PointTool):
    name = "steel_member"
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.chain"

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.spec = catalog.BY_KEY["viga_ipe300"]
        self.function = "beam"
        self.mode = "line"
        self.cardinal = 0               # (0: the function's own — a beam's top middle, a brace's middle)
        self.rotation = 0
        self.heights = "levels"         # "levels": z0 / z1 above the storey; "points": where the points are found
        self.z0 = self.z1 = bim.WALL_HEIGHT
        self._start = self._end = None
        self._column = None             # (bracing) the first column clicked

    # ------------------------------------------------------------ the contextual bar

    def options(self):
        types = steel_types()
        opts = [Option("type", t("ctx.type"), "choice", self.spec.key, tuple((s.key, _name(s)) for s in types)),
                Option("mode", t("ctx.steel_mode"), "choice", self.mode,
                       tuple((m, t("steel_mode." + m)) for m in MODES))]
        if self.mode == "line":
            opts += [Option("function", t("ctx.steel_function"), "choice", self.function,
                            tuple((f, t("steel_function." + f)) for f in FUNCTIONS)),
                     Option("cardinal", t("ctx.steel_cardinal"), "choice", self.cardinal,
                            ((0, t("steel_cardinal.auto")),) + tuple((c, t("steel_cardinal.{}".format(c)))
                                                                    for c in CARDINALS)),
                     Option("rotation", t("ctx.steel_rotation"), "choice", self.rotation,
                            tuple((r, "{}°".format(r)) for r in ROTATIONS)),
                     Option("heights", t("ctx.steel_heights"), "choice", self.heights,
                            (("levels", t("steel_heights.levels")), ("points", t("steel_heights.points"))))]
            if self.heights == "levels":
                opts += [length_option("z0", "ctx.steel_z0", self.z0), length_option("z1", "ctx.steel_z1", self.z1)]
        return opts

    def set_option(self, key, value):
        if key == "type" and value in catalog.BY_KEY:
            self.spec = catalog.BY_KEY[value]
        elif key == "mode" and value in MODES:
            self.cancel()
            self.mode = value
            if value != "line":
                self.function = "brace"
        elif key == "function" and value in FUNCTIONS:
            self.function = value
        elif key == "cardinal":
            self.cardinal = int(value)
        elif key == "rotation":
            self.rotation = int(value)
        elif key == "heights" and value in ("levels", "points"):
            self.heights = value
        elif key == "z0":
            self.z0 = float(value)
        elif key == "z1":
            self.z1 = float(value)
        self.host.set_hint(self.hint())
        if hasattr(self.host, "refresh_options"):
            self.host.refresh_options()

    def hint(self):
        if self.mode != "line":
            return t("hint.steel_brace_2" if self._column else "hint.steel_brace", type=_name(self.spec))
        if self._start is not None:
            return t("hint.steel_next")
        return t("hint.steel_start", type=_name(self.spec), what=t("steel_function." + self.function))

    def vcb_title(self):
        return t("vcb.length")

    # ------------------------------------------------------------ the points

    def _level(self, end=False):
        if self.heights == "points":
            return None
        return self.doc.work_level() + (self.z1 if end else self.z0)

    def pointer_move(self, x, y, modifiers):
        if self.mode != "line":
            guid = self._column_at(x, y)
            hit = self.viewport.pick_point(x, y) if guid is not None else None
            self.viewport.show_tip(self.doc.get(guid).name if guid is not None else "",
                                   hit[2] if hit is not None else None)
            return
        p, snap = self._point(x, y, self._level(end=self._start is not None), self._start, modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        if self._start is None:
            show_snap(self.viewport, snap, p)
            return
        self._end = p
        self.viewport.show_lines([self._start, self._end], [PREVIEW])
        drawing_dims(self.viewport, self._start, self._end)
        tip, color, _line = inferred_style(snap) if snap is not None else ("", PREVIEW, PREVIEW)
        self.viewport.show_marker(self._end, color)
        self.viewport.show_tip(tip, self._end if tip else None)
        self.host.set_vcb(_fmt(float(np.linalg.norm(self._end - self._start))))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self.mode != "line":
            self._brace_click(x, y)
            return
        if self._start is None:
            p, _snap = self._point(x, y, self._level(), modifiers=modifiers)
            if p is not None:
                self._start = p
                self.host.set_hint(self.hint())
            return
        if self._end is not None:
            self._add(self._end)

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None or values[0] is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        if self._start is None or self._end is None:
            return
        d = self._end - self._start
        n = float(np.linalg.norm(d))
        if n > 1e-9:
            self._add(self._start + d / n * values[0])

    def _add(self, end):
        end = np.asarray(end, dtype=float)
        if float(np.linalg.norm(end - self._start)) < MIN_LENGTH:
            return
        bim.add_steel_member(self.doc, self._start, end, self.spec, self.function, cardinal=self.cardinal or None,
                             rotation=self.rotation, storey=self.doc.active_storey)
        length = float(np.linalg.norm(end - self._start))
        self.host.message(t("info.steel_member", what=t("steel_function." + self.function), l=_fmt(length),
                            type=_name(self.spec)))
        self._start, self._end = end, None
        self.viewport.clear_overlays()

    # ------------------------------------------------------------ bracing between two columns

    def _column_at(self, x, y):
        hit = self.viewport.pick(x, y)
        obj = self.doc.get(hit[0]) if hit is not None else None
        return obj.id if obj is not None and obj.is_bim and obj.ifc_class == "IfcColumn" else None

    def _brace_click(self, x, y):
        guid = self._column_at(x, y)
        if guid is None:
            self.host.message(t("info.steel_pick_column"), warning=True)
            return
        if self._column is None or guid == self._column:
            self._column = guid
            self.host.set_hint(self.hint())
            return
        made = bim.x_brace(self.doc, self._column, guid, self.spec, SHAPES[self.mode])
        self.host.message(t("info.steel_braced", n=len(made), a=self.doc.get(self._column).name,
                            b=self.doc.get(guid).name))
        self._column = None
        self.host.set_hint(self.hint())

    def cancel(self):
        self._start = self._end = self._column = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    def deactivate(self):
        self.cancel()
        super().deactivate()


_DEFAULTS = DEFAULT_CARDINAL                      # (re-exported for the bar's «automatic»)
