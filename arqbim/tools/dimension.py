"""Dimension tool (Phase 3, step 14), in a plan, a section or an elevation; kept with that view (shown there only, on
screen and on paper); an end taken on an element follows it when the element is moved.

(0.401) As Revit's Aligned dimension (the owner, 2026-11-05: «vamos ter também cotação manual — mas como no Revit»):
click the references one after another and then, in an empty place, where the dimension line goes — the string is
placed, one dimension between each two references side by side.
- A reference is a line — a wall's finish face, its core's face, its axis, its core's axis (the bar's «Nas paredes»
  says which comes first), a door's or window's jamb or middle, a structural grid's axis — or a point (a corner, an
  end, the middle of an edge…: a point taken alone measures from point to point, as before).
- The one under the mouse is lit (orange) and named beside it; Tab goes to the next one in the same place (a face → the
  core's → the axis…). Once a line is taken, only the lines parallel to it (and points) are offered: the string
  measures across them.
- «Paredes inteiras» (Revit's «Entire walls»): a click on a wall takes, along it, its ends, its doors and windows (jambs
  or middles) and the walls that cross or reach it.
- Linear: two points measured level or upright (as the mouse goes), not along them.
- «Continuar a cadeia» (off, as Revit): once placed, each click on a reference adds a dimension to the same line.
Esc / the right button: the string started is given up. Angular (0.122): the corner, a point on each side, then where
the arc goes."""

from dataclasses import dataclass

import numpy as np

from ..core.inference import ENDPOINT, INTERSECTION
from ..core.sketch_geometry import ray_plane
from ..i18n import decimal_sep, t
from ..model import annotations as notes2d
from ..model import auto_dims, dim_refs
from ..model import dimensions as dims_model
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, SNAPPABLE, Option, show_snap
from .bim_draw import _PointTool

MIN_LENGTH = 0.01        # m
KINDS = ("aligned", "linear", "angular")
PICKS = ("single", "walls")
PICK_PX = 7              # a reference this near the mouse (pixels) is offered
PARALLEL = 0.9995        # (cos of about 2°)
CORNER_KINDS = (ENDPOINT, INTERSECTION)   # points offered before the lines
HOVER = (0.96, 0.52, 0.08, 1.0)       # the reference under the mouse
TAKEN = (0.10, 0.45, 0.95, 1.0)       # those taken


@dataclass
class Ref:
    """A reference of a dimension string: a line (its direction `along`, in the view's plane) or a point (None)."""
    point: np.ndarray
    along: np.ndarray = None
    guid: str = None
    kind: str = None          # the wall's line it is (model/dim_refs.KINDS), or None
    seg: tuple = None         # where it is drawn lit: (a, b), 3D
    what: str = ""            # its name, beside the mouse


class DimensionTool(_PointTool):
    name = "dimension"
    accepts_typing = False

    def __init__(self, host):
        super().__init__(host)
        self.kind = "aligned"
        self.chain = False
        self.style = None            # (0.193) the dimension type the new ones get (None: the project's style)
        self.preference = "faces"    # (0.401) what is offered first on a wall (Revit's «Preferência»)
        self.pick = "single"         # (0.401) «Referências individuais» / «Paredes inteiras»
        self.openings = "jambs"
        self._refs = []              # (0.401) the string's references taken so far
        self._cands, self._k = [], 0  # the references under the mouse, the one chosen among them (Tab)
        self._mouse = None
        self._a = self._b = None     # (an angular one's sides)
        self._vertex = None
        self._ang_refs = [None, None]
        self._vertex_ref = None
        self._last = None            # the string placed last (continued, when «Continuar a cadeia»)
        self._walls = None           # (the storey's walls' lines, kept while the model is the same)
        self._replacing, self._replacing_style = [], None    # (0.402) a string being edited: put back in its place

    # ------------------------------------------------------------ settings

    def options(self):
        opts = [Option("kind", t("ctx.dim_kind"), "choice", self.kind, tuple((k, t("dimkind." + k)) for k in KINDS))]
        if self.kind != "angular":
            opts.append(Option("preference", t("ctx.dim_ref"), "choice", self.preference,
                               tuple((p, t("dimref." + p)) for p in dim_refs.PREFERENCES)))
            opts.append(Option("pick", t("ctx.dim_pick"), "choice", self.pick,
                               tuple((p, t("dimpick." + p)) for p in PICKS)))
            if self.pick == "walls":
                opts.append(Option("openings", t("ctx.dim_openings"), "choice", self.openings,
                                   tuple((k, t("dimopen." + k)) for k in auto_dims.OPENINGS)))
            opts.append(Option("chain", t("ctx.dim_chain"), "toggle", self.chain))
        names = dims_model.type_names(getattr(self.doc, "dim_style", None))
        if names:                                            # (0.193) which dimension type the new ones are
            if self.style not in names:
                self.style = None
            opts.append(Option("style", t("ctx.dim_type"), "choice", self.style or "",
                               (("", t("dimtype.project")),) + tuple((n, n) for n in names)))
        return opts

    def set_option(self, key, value):
        if key == "kind" and value in KINDS:
            self.kind = value
            self.cancel()
        elif key == "chain":
            self.chain = bool(value)
            self._last = None
        elif key == "style":
            self.style = value or None
            self._last = None
        elif key == "preference" and value in dim_refs.PREFERENCES:
            self.preference = value
        elif key == "pick" and value in PICKS:
            self.pick = value
        elif key == "openings" and value in auto_dims.OPENINGS:
            self.openings = value
        self.host.set_hint(self.hint())

    def tab(self):
        """Tab: the next reference under the mouse (as Revit's); with none to go to, the next kind (aligned, linear,
        angular)."""
        if self.kind != "angular" and len(self._cands) > 1:
            self._k = (self._k + 1) % len(self._cands)
            self._show()
            return True
        self.set_option("kind", KINDS[(KINDS.index(self.kind) + 1) % len(KINDS)])
        self.host.message(t("info.dim_kind", k=t("dimkind." + self.kind)))
        return True

    def hint(self):
        if self.viewport.current_view() is None:
            return t("hint.dimension.view")
        if self.kind == "angular":
            step = 0 if self._vertex is None else 1 if self._a is None else 2 if self._b is None else 3
            return t("hint.dimension.angle_{}".format(step))
        if self._last is not None and not self._refs:
            return t("hint.dimension.chain")
        if not self._refs:
            return t("hint.dimension.walls" if self.pick == "walls" else "hint.dimension.start")
        return t("hint.dimension.end") if len(self._refs) < 2 else t("hint.dimension.place")

    # ------------------------------------------------------------ what is under the mouse

    def _plane_point(self, x, y):
        plane = self.viewport.view_plane()
        if plane is None:
            return None
        origin, _u, _v, n = plane
        ray_o, ray_d = self.viewport.ray(x, y)
        p = ray_plane(ray_o, ray_d, origin, n)
        return p if p is not None else ray_plane(ray_o, ray_d, origin, -n)

    def _pick(self, x, y):
        """(point, snap) under the mouse: an inference, else on the view's paper; (None, None) in 3D."""
        if self.viewport.view_plane() is None:
            return None, None
        snap, _hit = self.viewport.snap(x, y)
        if snap is not None and snap.kind in SNAPPABLE:
            return snap.point.copy(), snap
        return self._plane_point(x, y), None

    def _wall_lines(self):
        view = self.viewport.current_view()
        if view is None or view[0] != "plan":
            return {}
        key = (view, self.doc.revision)
        if self._walls is None or self._walls[0] != key:
            try:
                found = dim_refs.walls_of(self.doc, view[1])
            except Exception:
                found = {}
            self._walls = (key, found)
        return self._walls[1]

    def _candidates(self, x, y):
        """The references under the mouse, the most likely first: a corner or an end (a point snap) when the mouse is
        on one; else the walls' lines (those the preference takes first, then the others), the jambs, the grid's
        axes; then a point on an edge. Only the lines parallel to the string's (and points) once a line is taken."""
        p, snap = self._pick(x, y)
        if p is None:
            return [], None
        plane = self.viewport.view_plane()
        origin, u, v, n = plane
        reach = PICK_PX * self.viewport.world_per_pixel(p)
        on = self._plane_point(x, y)
        on = p if on is None else on
        level = float(origin @ n) if abs(n[2]) > 0.9 else None
        points, lines, others, edges = [], [], [], []
        # (a corner or an end before the lines; a middle — of every edge, everywhere — after them, unless the string
        # is of points so far: then from point to point, as the tool always measured)
        by_points = bool(self._refs) and all(r.along is None for r in self._refs)
        if snap is not None and self.pick != "walls" and (snap.kind in CORNER_KINDS or by_points):
            points.append(Ref(p, None, snap.obj_id, None, None, t("dimref.point")))
        elif snap is not None:
            edges.append(Ref(p, None, snap.obj_id, None, None, t("dimref.point")))
        walls = self._wall_lines()
        for guid, w in walls.items():
            local = w.local(np.array((on[0], on[1], w.m[2, 3])))
            if not -reach <= local[0] <= w.length + reach:
                continue
            seen = []
            preferred = [k for _y, k in w.ys(self.preference)]
            for kind in preferred + [k for k in dim_refs.KINDS if k not in preferred]:
                y = w.y_of(kind)
                if abs(local[1] - y) > reach or any(abs(y - s) < 1e-3 for s in seen):
                    continue
                seen.append(y)
                a, b = w.world(0.0, y), w.world(w.length, y)
                if level is not None:
                    a[2] = b[2] = level
                q = w.world(local[0], y)
                q[2] = p[2]
                ref = Ref(q, w.axis_dir.copy(), guid, kind, (a, b), t("dimref.kind." + kind))
                (lines if kind in preferred else others).append((abs(local[1] - y), ref))
            # its doors' and windows' jambs and middles, across it
            if w.lo - reach <= local[1] <= w.hi + reach:
                lines += self._jambs(guid, w, local, reach, p, level)
        for axis in getattr(self.doc, "grids", ()):              # the structural grid's axes
            a, b = np.array((*axis.start, 0.0), dtype=float), np.array((*axis.end, 0.0), dtype=float)
            d = b - a
            length = float(np.linalg.norm(d[:2]))
            if length < 1e-9 or level is None:
                continue
            d /= length
            s = float((on - a)[:2] @ d[:2])
            foot = a + d * s
            if -reach <= s <= length + reach and float(np.linalg.norm((on - foot)[:2])) <= reach:
                q = np.array((foot[0], foot[1], p[2]))
                a[2] = b[2] = level
                lines.append((float(np.linalg.norm((on - foot)[:2])), Ref(q, d, None, None, (a, b),
                                                                           t("dimref.grid", g=axis.tag))))
        found = points + [r for _d, r in sorted(lines, key=lambda c: c[0])] + \
            [r for _d, r in sorted(others, key=lambda c: c[0])] + edges
        return [r for r in found if self._fits(r)], p

    def _jambs(self, guid, w, local, reach, p, level):
        from ..model import bim
        out = []
        try:
            fillings = bim._fillings(self.doc, guid)
        except Exception:
            return out
        for filling in fillings:
            try:
                st = self.doc.ifc.filling_state(filling)
            except Exception:
                continue
            for x, what in ((st["s"], "dimref.jamb"), (st["s"] + st["width"], "dimref.jamb"),
                            (st["s"] + st["width"] / 2, "dimref.opening_axis")):
                if abs(local[0] - x) > reach:
                    continue
                a, b = w.world(x, w.lo), w.world(x, w.hi)
                if level is not None:
                    a[2] = b[2] = level
                q = w.world(x, float(np.clip(local[1], w.lo, w.hi)))
                q[2] = p[2]
                out.append((abs(local[0] - x), Ref(q, w.across.copy(), filling, None, (a, b), t(what))))
        return out

    def _fits(self, ref):
        """A reference the string can take: a point, or a line parallel to its lines (not one already taken)."""
        lines = [r for r in self._refs if r.along is not None]
        if ref.along is not None and lines:
            if abs(float(ref.along[:2] @ lines[0].along[:2])) < PARALLEL:
                return False
            d = np.array((-lines[0].along[1], lines[0].along[0], 0.0))
            if any(abs(float((ref.point - r.point)[:2] @ d[:2])) < 1e-4 for r in lines):
                return False
        if ref.along is None and any(r.along is None and np.linalg.norm(r.point - ref.point) < 1e-4
                                     for r in self._refs):
            return False
        return True

    def references_at(self, x, y):
        """(0.402) The references under the mouse, whatever string is being made (the Select tool's witness grips)."""
        kept, self._refs = self._refs, []
        try:
            return self._candidates(x, y)[0]
        finally:
            self._refs = kept

    def add_to(self, dims):
        """(0.402, Revit's «Editar linhas de chamada») A string's references taken again: each click on a reference adds
        one, a click in an empty place puts the string back (its line where clicked) — one undo step."""
        from ..model import dim_edit
        plane = self.viewport.view_plane()
        if plane is None or not dims:
            return False
        _along, across = dim_edit.line_normal(self.doc, dims[0], plane)
        self._restart()
        self._last = None
        self.kind = "aligned"
        for point, users in dim_edit.witness_points(self.doc, dims):
            d, k = users[0]
            ref = d.refs[k]
            self._refs.append(Ref(np.asarray(point, dtype=float), across.copy(), ref[0] if ref else None,
                                  ref[3] if ref is not None and len(ref) > 3 else None, None, ""))
        self._replacing = list(dims)
        self._replacing_style = dims[0].style
        self.host.set_hint(t("hint.dimension.add_refs"))
        return True

    # ------------------------------------------------------------ the string

    def _direction(self, refs, mouse):
        """(the direction measured along (3D, unit), aligned with the points?) of a string — square to its lines, else
        from its first point to its second (linear: level or upright in the view, as the mouse is), or None."""
        origin, u, v, _n = self.viewport.view_plane()
        line = next((r for r in refs if r.along is not None), None)
        if line is not None:
            d = np.cross(np.cross(u, v), line.along)
            return d / max(float(np.linalg.norm(d)), 1e-12), False
        if len(refs) < 2:
            return None, False
        a, b = refs[0].point, refs[1].point
        if self.kind == "linear" and mouse is not None:
            lo = np.minimum.reduce([np.array((float((r.point - origin) @ u), float((r.point - origin) @ v)))
                                    for r in refs])
            hi = np.maximum.reduce([np.array((float((r.point - origin) @ u), float((r.point - origin) @ v)))
                                    for r in refs])
            m = np.array((float((mouse - origin) @ u), float((mouse - origin) @ v)))
            out_x = max(lo[0] - m[0], m[0] - hi[0], 0.0)
            out_y = max(lo[1] - m[1], m[1] - hi[1], 0.0)
            return (u if out_y >= out_x else v), False
        d = b - a
        norm = float(np.linalg.norm(d))
        return (d / norm if norm > 1e-9 else None), True

    def _string(self, refs, mouse, view):
        """The dimensions of a string of references, its line through `mouse`: [Dimension] (one chain)."""
        d, aligned = self._direction(refs, mouse)
        if d is None:
            return []
        order = sorted(refs, key=lambda r: float(r.point @ d))
        kept = []
        for r in order:                                       # (two references at the same place: one)
            if kept and abs(float((r.point - kept[-1].point) @ d)) < MIN_LENGTH:
                continue
            kept.append(r)
        if len(kept) < 2:
            return []
        chain = dims_model.new_chain()
        out = []
        for r0, r1 in zip(kept, kept[1:]):
            refs_ = [self._hang(r0), self._hang(r1)]
            out.append(dims_model.Dimension(view, np.asarray(r0.point, dtype=float), np.asarray(r1.point, dtype=float),
                                            np.asarray(mouse, dtype=float), refs_,
                                            at_ref=dims_model.hang_line(self.doc, refs_, mouse),
                                            direction=None if aligned else np.asarray(d, dtype=float),
                                            style=self.style, chain=chain))
        return out

    def _hang(self, ref):
        if ref.guid is None:
            return None
        return dim_refs.hang(self.doc, ref.guid, ref.point, ref.kind)

    def _whole_wall(self, ref):
        """(0.401) «Paredes inteiras»: the references along the wall of `ref` (its face nearest the mouse)."""
        walls = self._wall_lines()
        w = walls.get(ref.guid) if ref.guid else None
        if w is None:
            return [ref]
        local = w.local(ref.point)
        side = 1 if local[1] >= (w.lo + w.hi) / 2 else -1
        out = []
        for _s, c, guid, kind in auto_dims.wall_points(self.doc, walls, ref.guid, side, self.preference,
                                                       self.openings):
            q = np.array((c[0], c[1], ref.point[2]))
            out.append(Ref(q, w.across.copy(), guid, kind, None, ""))
        return out

    # ------------------------------------------------------------ the mouse

    def _show(self):
        """The references taken (blue), the one under the mouse (orange, named), the string as it would be placed."""
        if self._mouse is None:
            return
        segs, colours = [], []
        for r in self._refs:
            if r.seg is not None:
                segs += list(r.seg)
                colours += [TAKEN, TAKEN]
        cand = self._cands[self._k] if self._cands else None
        if cand is not None and cand.seg is not None:
            segs += list(cand.seg)
            colours += [HOVER, HOVER]
        view = self.viewport.current_view()
        refs = list(self._refs)
        values = ""
        if len(refs) >= 2 or (refs and cand is not None and self.kind != "angular"):
            trial = refs + ([cand] if cand is not None and len(refs) < 2 else [])
            dims = self._string(trial, self._mouse, view)
            if dims:
                lines, values = self._preview_lines(dims)
                segs += lines
                colours += [PREVIEW] * len(lines)
        self.viewport.show_lines(segs, colours)
        if cand is not None:
            tip = cand.what + ("   (Tab)" if len(self._cands) > 1 else "")
            self.viewport.show_marker(cand.point)
            self.viewport.show_tip(tip, cand.point)
        else:
            self.viewport.show_marker(self._mouse)
            self.viewport.show_tip("", None)
        self.viewport.show_label(values, self._mouse if values else None)

    def _preview_lines(self, dims):
        from ..core import dim_layout
        origin, u, v, _n = self.viewport.view_plane()
        project = dims_model.clean_style(getattr(self.doc, "dim_style", None))
        pieces = [p for p in (dims_model.piece_of(self.doc, d, origin, u, v, project, decimal_sep()) for d in dims)
                  if p is not None]
        try:
            scale = self.doc.view_settings(self.viewport.current_view()).scale or 100
        except Exception:
            scale = 100
        layout = dim_layout.of_drawing(pieces, project, scale / 1000.0)
        segs = [origin + u * q[0] + v * q[1] for a, b, *_r in layout.lines for q in (a, b)]
        return segs, " | ".join(p[4] for p in pieces)

    def pointer_move(self, x, y, modifiers):
        if self.kind == "angular":
            p, snap = self._pick(x, y)
            if p is None:
                return
            self._hover = (p, snap)
            origin, u, v, _n = self.viewport.view_plane()
            to3 = lambda q: origin + u * q[0] + v * q[1]           # noqa: E731
            self._show_angle(p, origin, u, v, to3)
            show_snap(self.viewport, snap, p)
            return
        cands, p = self._candidates(x, y)
        if p is None:
            return
        before = self._cands[self._k] if self._cands else None
        self._cands = cands
        self._k = 0
        if before is not None:                      # (Tab's choice kept while the same references are there)
            same = [k for k, r in enumerate(cands) if r.what == before.what and r.guid == before.guid
                    and r.kind == before.kind]
            if same:
                self._k = same[0]
        self._mouse = self._plane_point(x, y)
        if self._mouse is None:
            self._mouse = p
        if self._last is not None and not self._refs and self.chain and self._cands:
            self._show_chained()
            return
        self._show()

    def _show_chained(self):
        cand = self._cands[self._k]
        dims = self._chained(cand)
        segs, colours = [], []
        if dims is not None:
            lines, values = self._preview_lines([dims])
            segs, colours = lines, [PREVIEW] * len(lines)
            self.viewport.show_label(values, cand.point)
        if cand.seg is not None:
            segs += list(cand.seg)
            colours += [HOVER, HOVER]
        self.viewport.show_lines(segs, colours)
        self.viewport.show_marker(cand.point)
        self.viewport.show_tip(cand.what, cand.point)

    def _chained(self, ref):
        """The next dimension of the string placed last: from its far end to `ref`, on its line (or None)."""
        last = self._last
        origin, u, v, _n = self.viewport.view_plane()
        a2, b2, off = dims_model.flat(last.a, last.b, last.at, origin, u, v)
        if last.direction is not None:
            d3 = np.asarray(last.direction, dtype=float)
            if abs(float((ref.point - last.b) @ d3)) < MIN_LENGTH:
                return None
        elif float(np.linalg.norm(ref.point - last.b)) < MIN_LENGTH:
            return None
        d = b2 - a2
        n = np.array((-d[1], d[0])) / max(np.linalg.norm(d), 1e-12)
        at2 = b2 + n * off
        at = origin + u * at2[0] + v * at2[1]
        refs = [last.refs[1], self._hang(ref)]
        return dims_model.Dimension(last.view, np.asarray(last.b, dtype=float), np.asarray(ref.point, dtype=float),
                                    at, refs, at_ref=dims_model.hang_line(self.doc, refs, at), style=last.style,
                                    direction=last.direction, chain=last.chain)

    def _value(self, length, unit=False):
        """A length as the project's dimension style writes it (0.124) — with its unit, for the status bar."""
        style = dims_model.style_of(getattr(self.doc, "dim_style", None),
                                    dims_model.Dimension(None, None, None, None, style=self.style))   # (0.193)
        text = dims_model.text(length, decimal_sep(), style)
        return "{} {}".format(text, style.get("unit", "m")) if unit else text

    def _show_angle(self, p, origin, u, v, to3):
        if self._vertex is None:
            return
        if self._a is None or self._b is None:               # its sides so far
            ends = [q for q in (self._a, self._b, p) if q is not None][:2 if self._a is not None else 1]
            segs = [q for e in ends for q in (self._vertex, e)]
            self.viewport.show_lines(segs, [PREVIEW] * len(segs))
            return
        a2, b2, v2, at2 = notes2d.to2([self._a, self._b, self._vertex, p], origin, u, v)
        arc = dims_model.angle_arc(a2, b2, v2, at2)
        if arc is None:
            return
        r, start, sweep, value = arc
        k = max(int(np.degrees(sweep) / 3.0), 2)
        pts = [to3(v2 + r * np.array((np.cos(start + sweep * j / k), np.sin(start + sweep * j / k))))
               for j in range(k + 1)]
        segs = [q for pair in zip(pts, pts[1:]) for q in pair] + [self._vertex, self._a, self._vertex, self._b]
        self.viewport.show_lines(segs, [PREVIEW] * len(segs))
        self.viewport.show_label(dims_model.angle_text(value, decimal_sep()), pts[len(pts) // 2])

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        view = self.viewport.current_view()
        if view is None or self.viewport.view_plane() is None:
            self.host.message(t("hint.dimension.view"))
            return
        if self.kind == "angular":
            p, snap = self._pick(x, y)
            ref = dims_model.hang(self.doc, snap.obj_id, p) if snap is not None else None
            self._angle_click(view, p, ref)
            return
        if not self._cands or self._mouse is None:
            self.pointer_move(x, y, modifiers)
        cand = self._cands[self._k] if self._cands else None
        if cand is not None and self._last is not None and not self._refs and self.chain:
            dim = self._chained(cand)                      # the next dimension of the string placed last
            if dim is not None:
                self.doc.execute(dims_model.AddDimension(dim, t("cmd.dimension")))
                o, u, v = self.viewport.view_plane()[:3]
                length = dims_model.placed(dim.a, dim.b, dim.at, o, u, v, dim.direction)[4]
                self.host.message(t("info.dimension_chain", v=self._value(length, unit=True)))
                self._last = dim
            return
        if cand is not None:                               # a reference: taken
            taken = self._whole_wall(cand) if self.pick == "walls" and cand.kind is not None else [cand]
            for r in taken:
                if self._fits(r):
                    self._refs.append(r)
            self._last = None
            self.host.set_hint(self.hint())
            self.host.message(t("info.dim_refs", n=len(self._refs)) if len(self._refs) >= 2 else cand.what)
            self._show()
            return
        if len(self._refs) < 2:                            # (nothing there: a point on the paper)
            if self._mouse is not None:
                self._refs.append(Ref(self._mouse.copy(), None, None, None, None, ""))
                self.host.set_hint(self.hint())
            return
        dims = self._string(self._refs, self._mouse, view)   # an empty place: the string placed there
        if not dims:
            return
        old = [d for d in self._replacing if d in self.doc.dimensions]    # (0.402: a string edited: in its place)
        if old:
            for d in dims:
                d.style = self._replacing_style
        self._replacing, self._replacing_style = [], None
        self.doc.execute(dims_model.ReplaceDimensions(old, dims, t("cmd.dimension")))
        o, u, v = self.viewport.view_plane()[:3]
        total = sum(dims_model.placed(d.a, d.b, d.at, o, u, v, d.direction)[4] for d in dims)
        self.host.message(t("info.dimension_placed_chain" if self.chain else "info.dimension",
                            v=self._value(total, unit=True)) if len(dims) == 1 else
                          t("info.dimension_string", n=len(dims), v=self._value(total, unit=True)))
        self._last = dims[-1] if self.chain else None
        self._refs = []
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())

    def _angle_click(self, view, p, ref):
        if p is None:
            return
        if self._vertex is None:
            self._vertex, self._vertex_ref = p, ref
        elif self._a is None:
            if np.linalg.norm(p - self._vertex) < MIN_LENGTH:
                return
            self._a, self._ang_refs = p, [ref, None]
        elif self._b is None:
            if np.linalg.norm(p - self._vertex) < MIN_LENGTH:
                return
            self._b, self._ang_refs[1] = p, ref
        else:
            origin, u, v, _n = self.viewport.view_plane()
            a2, b2, v2, at2 = notes2d.to2([self._a, self._b, self._vertex, p], origin, u, v)
            arc = dims_model.angle_arc(a2, b2, v2, at2)
            if arc is None:
                self.host.message(t("err.dimension_angle"), warning=True)
                return
            refs = list(self._ang_refs)
            dim = dims_model.Dimension(view, self._a, self._b, p, refs,
                                       at_ref=dims_model.hang_line(self.doc, [self._vertex_ref] + refs, p),
                                       vertex=self._vertex, vertex_ref=self._vertex_ref, style=self.style)
            self.doc.execute(dims_model.AddDimension(dim, t("cmd.dimension")))
            self.host.message(t("info.dimension_angle", v=dims_model.angle_text(arc[3], decimal_sep())))
            self.cancel()
            return
        self.host.set_hint(self.hint())

    def _restart(self):
        self._a = self._b = self._vertex = None
        self._ang_refs, self._vertex_ref = [None, None], None
        self._refs = []
        self.viewport.clear_overlays()

    def cancel(self):
        self._restart()
        self._last = None
        self._replacing, self._replacing_style = [], None
        self.host.set_hint(self.hint())
