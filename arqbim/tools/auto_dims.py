"""(0.399) The dimensions made with one click (the owner, 2026-11-05: «quero cotas automáticas, para cotar o interior com
um clique; a mesma coisa para a cotação externa»), in a plan:

- Outside dimensions (Anotar ▸ Cotas exteriores): the rows round the building (model/auto_dims.exterior) shown in blue
  while the mouse moves — all its sides, or the side nearest the mouse —, placed with a click; again, they are made
  again (one undo step each time). On the contextual bar: what is taken on the walls (finish faces, core faces, axes,
  the core's axis — Revit's «Preferência»), the openings (jambs, middles, none), which rows, all sides or one, the
  dimension type.

The tool stays: its settings changed, a click places the dimensions again in their place."""

import numpy as np

from ..core import dim_layout
from ..i18n import decimal_sep, t
from ..model import auto_dims, dim_refs
from ..model import dimensions as dims_model
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, Tool


class _AutoDims(Tool):
    """What the one-click dimension tools share: the plan they work in, the preview of what a click places, the
    contextual bar's preference and dimension type."""

    preference = "faces"
    style = None

    def __init__(self, host):
        super().__init__(host)
        self._cache = None              # (key, the dimensions a click would place)
        self._shown = None

    def _view(self):
        view = self.viewport.current_view()
        return view if view is not None and view[0] == "plan" else None

    def _scale(self, view):
        try:
            return self.doc.view_settings(view).scale or 100
        except Exception:
            return 100

    def _type_option(self):
        names = dims_model.type_names(getattr(self.doc, "dim_style", None))
        if not names:
            return []
        if self.style not in names:
            self.style = None
        return [Option("style", t("ctx.dim_type"), "choice", self.style or "",
                       (("", t("dimtype.project")),) + tuple((n, n) for n in names))]

    def _ref_option(self):
        return Option("preference", t("ctx.dim_ref"), "choice", self.preference,
                      tuple((p, t("dimref." + p)) for p in dim_refs.PREFERENCES))

    def set_option(self, key, value):
        if key == "preference" and value in dim_refs.PREFERENCES:
            self.preference = value
        elif key == "style":
            self.style = value or None
        else:
            self._set(key, value)
        self._cache = None
        self._shown = None
        self.host.set_hint(self.hint())

    def _set(self, key, value):
        """A setting of its own changed."""

    def activate(self):
        super().activate()
        self._cache = None
        self._shown = None

    def _preview(self, dims, area=None):
        """The dimensions a click would place, drawn in blue (their lines, as their type draws them) — (0.400) over the
        room `area` (a shapely polygon) lit in blue."""
        plane = self.viewport.view_plane()
        if plane is None or (not dims and area is None):
            self.viewport.clear_overlays()
            return
        origin, u, v, _n = plane
        project = dims_model.clean_style(getattr(self.doc, "dim_style", None))
        pieces = [p for p in (dims_model.piece_of(self.doc, d, origin, u, v, project, decimal_sep()) for d in dims)
                  if p is not None]
        layout = dim_layout.of_drawing(pieces, project, self._scale(self._view()) / 1000.0)
        segs = [origin + u * q[0] + v * q[1] for a, b, *_r in layout.lines for q in (a, b)]
        if area is not None:
            ring = [origin + u * (x - origin @ u) + v * (y - origin @ v) for x, y in list(area.exterior.coords)[:-1]]
            self.viewport.show_polygon(ring, segs, [PREVIEW] * len(segs))
            return
        self.viewport.show_lines(segs, [PREVIEW] * len(segs))

    def cancel(self):
        self.viewport.clear_overlays()
        self._shown = None

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        view = self._view()
        if view is None:
            self.host.message(t("hint.auto_dims.view"), warning=True)
            return
        # (0.408) Ctrl: the dimensions added to those already there (another pair in an L-shaped room)
        self.place(view, self._point(x, y), adding=bool(set(modifiers or ()) & {"Control", "Ctrl", "Meta"}))

    def _point(self, x, y):
        plane = self.viewport.view_plane()
        if plane is None:
            return None
        from ..core.sketch_geometry import ray_plane
        origin, _u, _v, n = plane
        ray_o, ray_d = self.viewport.ray(x, y)
        p = ray_plane(ray_o, ray_d, origin, n)
        return p if p is not None else ray_plane(ray_o, ray_d, origin, -n)


class InteriorDimsTool(_AutoDims):
    """(0.400) Anotar ▸ Cotas interiores: one click in a room (closed by walls, with an «Ambiente» or not) — its width
    and depth through the point clicked, a run across the building, or along its walls with their openings."""

    name = "dim_interior"

    def __init__(self, host):
        super().__init__(host)
        self.mode = "size"
        self.directions = "both"
        self.openings = "jambs"
        self.which = "one"

    def options(self):
        opts = [self._ref_option(),
                Option("mode", t("ctx.dim_mode"), "choice", self.mode,
                       tuple((k, t("dimmode." + k)) for k in auto_dims.MODES))]
        if self.mode in ("size", "run"):
            opts.append(Option("directions", t("ctx.dim_directions"), "choice", self.directions,
                               tuple((k, t("dimdir." + k)) for k in auto_dims.DIRECTIONS)))
        else:
            opts.append(Option("openings", t("ctx.dim_openings"), "choice", self.openings,
                               tuple((k, t("dimopen." + k)) for k in auto_dims.OPENINGS)))
        if self.mode != "run":
            opts.append(Option("which", t("ctx.dim_rooms"), "choice", self.which,
                               (("one", t("dimrooms.one")), ("all", t("dimrooms.all")))))
        return opts + self._type_option()

    def _set(self, key, value):
        if key == "mode" and value in auto_dims.MODES:
            self.mode = value
        elif key == "directions" and value in auto_dims.DIRECTIONS:
            self.directions = value
        elif key == "openings" and value in auto_dims.OPENINGS:
            self.openings = value
        elif key == "which" and value in ("one", "all"):
            self.which = value

    def hint(self):
        if self._view() is None:
            return t("hint.auto_dims.view")
        if self.which == "all" and self.mode != "run":
            return t("hint.dim_interior.all")
        return t("hint.dim_interior." + self.mode)

    def _every(self):
        return self.which == "all" and self.mode != "run"

    def _dims(self, view, point):
        try:
            return auto_dims.interior(self.doc, view[1], point, self.preference, self.mode, self.directions,
                                      self.openings, self._scale(view), self.style, every=self._every())
        except Exception:                               # (the IFC still being read…)
            return []

    def _room(self, view, point):
        """(the room under the point — None: none —, the storey's rooms), the rooms kept until the model changes."""
        key = (view, self.doc.revision)
        if self._cache is None or self._cache[0] != key:
            try:
                found = auto_dims.rooms(self.doc, view[1])
            except Exception:
                found = []
            self._cache = (key, found)
        rooms = self._cache[1]
        return (auto_dims.room_at(rooms, point) if point is not None else None), rooms

    def pointer_move(self, x, y, modifiers):
        view = self._view()
        point = self._point(x, y)
        if view is None or point is None:
            return
        room, rooms = self._room(view, point)
        if self._every():
            shown = ("all", self._cache[0])
        elif room is None:
            shown = None
        elif self.mode == "walls":
            shown = (room.wkt, self._cache[0])
        else:
            shown = (room.wkt, self._cache[0], round(float(point[0]), 2), round(float(point[1]), 2))
        if shown == self._shown:
            return
        self._shown = shown
        if shown is None:
            self.viewport.clear_overlays()
            return
        self._preview(self._dims(view, point), None if self._every() else room)

    def place(self, view, point, adding=False):
        """The dimensions of the click placed — in place of this room's (or every room's) placed before; (0.408) with
        Ctrl (`adding`) beside them: an L-shaped room measured in each of its wings. A click without Ctrl after that
        takes all of them away again for its own."""
        room, rooms = self._room(view, point)
        if not rooms:
            self.host.message(t("info.no_rooms_walls"), warning=True, action=self.host.tool_actions.get("wall"))
            return
        if room is None and not self._every():
            self.host.message(t("info.dim_interior_outside"), warning=True)
            return
        dims = self._dims(view, point)
        if not dims:
            self.host.message(t("info.dim_interior_none"), warning=True)
            return
        tags = {d.tag for d in dims}
        if self.mode == "run" or (adding and self.mode == "size" and not self._every()):
            old = []
        elif self._every():
            prefix = "int:{}:".format(self.mode)
            old = [d for d in self.doc.dimensions if d.view in self.doc.twin_views(view) and ((d.tag or "").startswith(prefix)
                                                                         or (d.tag or "").startswith("room:"))]
        else:
            old = [d for d in self.doc.dimensions if d.view in self.doc.twin_views(view) and d.tag in tags]
        self.doc.execute(dims_model.ReplaceDimensions(old, dims, t("cmd.dim_interior")))
        self._shown = None
        self.viewport.clear_overlays()
        self.host.message(t("info.dim_interior", d=len(dims), n=len({tag.split(":")[-1] for tag in tags})))


class ExteriorDimsTool(_AutoDims):
    """Anotar ▸ Cotas exteriores: one click, the rows round the building."""

    name = "dim_exterior"

    def __init__(self, host):
        super().__init__(host)
        self.openings = "jambs"
        self.rows = {"walls": True, "corners": True, "overall": True}
        self.which = "all"

    def options(self):
        return [self._ref_option(),
                Option("openings", t("ctx.dim_openings"), "choice", self.openings,
                       tuple((k, t("dimopen." + k)) for k in auto_dims.OPENINGS)),
                Option("row_walls", t("ctx.dim_row_walls"), "toggle", self.rows["walls"]),
                Option("row_corners", t("ctx.dim_row_corners"), "toggle", self.rows["corners"]),
                Option("row_overall", t("ctx.dim_row_overall"), "toggle", self.rows["overall"]),
                Option("which", t("ctx.dim_which"), "choice", self.which,
                       (("all", t("dimwhich.all")), ("near", t("dimwhich.near"))))] + self._type_option()

    def _set(self, key, value):
        if key == "openings" and value in auto_dims.OPENINGS:
            self.openings = value
        elif key.startswith("row_") and key[4:] in self.rows:
            self.rows[key[4:]] = bool(value)
        elif key == "which" and value in ("all", "near"):
            self.which = value

    def hint(self):
        if self._view() is None:
            return t("hint.auto_dims.view")
        return t("hint.dim_exterior.near" if self.which == "near" else "hint.dim_exterior")

    def _rows(self):
        return ("openings",) + tuple(k for k in ("walls", "corners", "overall") if self.rows[k])

    def _all(self, view):
        """Every side's dimensions (kept until the model, the view or a setting changes)."""
        key = (view, self.doc.revision, self.preference, self.openings, tuple(sorted(self.rows.items())), self.style,
               self._scale(view))
        if self._cache is None or self._cache[0] != key:
            try:
                dims = auto_dims.exterior(self.doc, view[1], self.preference, self._rows(), self.openings,
                                          self._scale(view), style=self.style)
            except Exception:                           # (the IFC still being read…)
                dims = []
            self._cache = (key, dims)
        return self._cache[1]

    def _chosen(self, view, point):
        dims = self._all(view)
        if self.which != "near" or point is None or not dims:
            return dims
        from shapely.geometry import LineString, Point
        q = Point(float(point[0]), float(point[1]))
        tags = {}
        for d in dims:                                  # (the side whose dimension lines pass nearest the mouse)
            a, b = dims_model.ends(self.doc, d)
            dist = LineString([tuple(a[:2]), tuple(b[:2])]).distance(q)
            tags[d.tag] = min(tags.get(d.tag, np.inf), dist)
        near = min(tags, key=tags.get)
        return [d for d in dims if d.tag == near]

    def pointer_move(self, x, y, modifiers):
        view = self._view()
        if view is None:
            return
        dims = self._chosen(view, self._point(x, y))
        shown = (self._cache[0] if self._cache else None, tuple(sorted({d.tag for d in dims})))
        if shown != self._shown:
            self._shown = shown
            self._preview(dims)

    def place(self, view, point, adding=False):
        dims = self._chosen(view, point)
        if not dims:
            self.host.message(t("info.no_walls"), warning=True, action=self.host.tool_actions.get("wall"))
            return
        tags = {d.tag for d in dims}
        if self.which == "near":
            old = [d for d in self.doc.dimensions if d.view in self.doc.twin_views(view) and d.tag in tags]
        else:
            old = [d for d in self.doc.dimensions if d.view in self.doc.twin_views(view) and (d.tag or "").startswith(("ext:", "facade:"))]
        fresh = [dims_model.Dimension(**{k: getattr(d, k) for k in d.__dataclass_fields__}) for d in dims]
        self.doc.execute(dims_model.ReplaceDimensions(old, fresh, t("cmd.dim_exterior")))
        self._cache = None
        self._shown = None
        self.viewport.clear_overlays()
        self.host.message(t("info.dim_exterior", d=len(fresh), n=len(tags)))
