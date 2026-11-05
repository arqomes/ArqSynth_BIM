"""Platform (0.157, Phase 7, step 3 — as Revit's building pad, with slopes): on a terrain (the one selected, or the
only one), a flat area — a rectangle (two corners) or a polygon (its corners; Enter or a click on the first one
closes it) — at a height: the ground's where the first corner was clicked, or the one typed ("1,20", Enter). Its
slopes round it, cut and fill (batters chosen on the contextual bar), down or up to the ground. The volumes of earth
taken away and brought are told."""

import numpy as np

from ..core import earthworks
from ..core import terrain as terrain_geo
from ..core.units import format_length, parse_length
from ..i18n import decimal_sep, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, Tool, infer_point, show_snap
from .slab import SlabOutlineTool

TERRAIN_CLASS = "IfcGeographicElement"
CLOSE_PX = 10


def volume_text(v):
    return "{:.1f} m³".format(v).replace(".", decimal_sep())


class PlatformTool(Tool):
    name = "platform"
    accepts_typing = True
    on_storey = True

    def __init__(self, host):
        super().__init__(host)
        self.shape = "rectangle"
        self.cut = "1:1"
        self.fill = "2:3"
        self._points = []
        self._z = None
        self._end = None

    # ------------------------------------------------------------ which terrain

    def terrain(self):
        """The terrain the platform goes on: the one selected, else the only one — or None."""
        sel = [self.doc.get(i) for i in self.viewport.selection]
        chosen = [o.id for o in sel if o is not None and o.is_bim and o.ifc_class == TERRAIN_CLASS]
        if len(chosen) == 1:
            return chosen[0]
        every = [o.id for o in self.doc.objects.values() if o.is_bim and o.ifc_class == TERRAIN_CLASS]
        return every[0] if len(every) == 1 else None

    def _ground(self, xy):
        guid = self.terrain()
        if guid is None:
            return None
        made = self.doc.ifc.terrain_surface(guid)
        survey = terrain_geo.tin(self.doc.ifc.terrain_survey(guid))
        made = survey or made
        return terrain_geo.height_at(*made, xy) if made is not None else None

    # ------------------------------------------------------------ the contextual bar

    def options(self):
        slopes = tuple((k, t("slope." + k)) for k in earthworks.SLOPES)
        return [Option("shape", t("ctx.platform_shape"), "choice", self.shape,
                       (("rectangle", t("draft.rectangle")), ("polygon", t("draft.polyline")))),
                Option("cut", t("ctx.platform_cut"), "choice", self.cut, slopes),
                Option("fill", t("ctx.platform_fill"), "choice", self.fill, slopes)]

    def set_option(self, key, value):
        if key == "shape" and value in ("rectangle", "polygon"):
            self.shape = value
            self.cancel()
        elif key in ("cut", "fill") and value in earthworks.SLOPES:
            setattr(self, key, value)

    # ------------------------------------------------------------ hints

    def hint(self):
        if self.terrain() is None:
            return t("hint.platform.none")
        if not self._points:
            return t("hint.platform." + self.shape)
        z = format_length(self._height(), decimal_sep())
        return t("hint.platform.end_rectangle" if self.shape == "rectangle" else "hint.platform.more", z=z)

    def vcb_title(self):
        return t("vcb.height_point")

    def _height(self):
        if self._z is not None:
            return self._z
        if self._points:
            h = self._ground(self._points[0][:2])
            if h is not None:
                return h
        return float(self.doc.work_level())

    # ------------------------------------------------------------ points

    def _plan_point(self, x, y, modifiers):
        found, snap, _hit = infer_point(self.viewport, x, y, self._points[-1] if self._points else None,
                                        modifiers, flat=True)
        if found is not None:
            return found.point.copy(), snap
        origin, direction = self.viewport.ray(x, y)
        if abs(direction[2]) < 1e-9:
            return None, None
        level = float(self.doc.work_level())
        s = (level - origin[2]) / direction[2]
        return (origin + direction * s, None) if s > 0 else (None, None)

    def _outline(self, end=None):
        pts = [np.asarray(p, dtype=float)[:2] for p in self._points]
        if end is not None:
            pts.append(np.asarray(end, dtype=float)[:2])
        if self.shape == "rectangle" and len(pts) >= 2:
            (x0, y0), (x1, y1) = pts[0], pts[1]
            return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        return [tuple(p) for p in pts]

    def _preview(self, end=None):
        ring = self._outline(end)
        z = self._height() + 0.02
        segs = []
        closed = self.shape == "rectangle" or (end is None and len(ring) > 2)
        for k in range(len(ring) - (0 if closed else 1)):
            a, b = ring[k], ring[(k + 1) % len(ring)]
            segs += [np.array((a[0], a[1], z)), np.array((b[0], b[1], z))]
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))

    def pointer_move(self, x, y, modifiers):
        p, snap = self._plan_point(x, y, modifiers)
        if p is None:
            return
        show_snap(self.viewport, snap, p)
        self._end = p
        if self._points:
            self._preview(p)
            self.host.set_hint(self.hint())

    def _near_first(self, x, y):
        if self.shape != "polygon" or len(self._points) < 3:
            return False
        sx, sy = self.viewport.project(self._points[0])
        return float(np.hypot(sx - x, sy - y)) <= CLOSE_PX

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self.terrain() is None:
            self.host.message(t("hint.platform.none"), warning=True)
            return
        if self._near_first(x, y):
            self.finish()
            return
        p, _snap = self._plan_point(x, y, modifiers)
        if p is None:
            return
        self._points.append(p)
        if self.shape == "rectangle" and len(self._points) == 2:
            self.finish()
            return
        self._preview()
        self.host.set_hint(self.hint())

    def typed(self, text):
        z = parse_length(text)
        if z is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        self._z = float(z)
        if self._points:
            self._preview(self._end)
        self.host.set_hint(self.hint())

    def enter(self):
        if self.shape == "polygon":
            self.finish()

    def finish(self):
        """The platform on the terrain. Returns (cut, fill) m³, or None."""
        ring = self._outline()
        guid = self.terrain()
        if guid is None or len(ring) < 3:
            return None
        from shapely.geometry import Polygon
        if Polygon(ring).area < 0.01:
            self.host.message(t("err.platform_small"), warning=True)
            return None
        z = self._height()
        try:
            cut, fill = bim.add_platform(self.doc, guid, ring, z, earthworks.SLOPES[self.cut],
                                         earthworks.SLOPES[self.fill])
        except ValueError:
            self.host.message(t("err.terrain_few"), warning=True)
            return None
        self.host.message(t("info.platform", z=format_length(z, decimal_sep()), c=volume_text(cut),
                            f=volume_text(fill)))
        self._points, self._z = [], None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        return cut, fill

    def cancel(self):
        self._points = []
        self._z = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")


RAMP_WIDTHS = (2.5, 3.0, 3.5, 4.0, 5.0, 6.0)        # m: a ramp of access's widths offered (0.205)


class TerrainRampTool(PlatformTool):
    """Rampa de acesso (0.205): on a terrain, a ramp from one platform to another (or to the ground) — two clicks,
    its start and its end (the middle of its ends), its width chosen on the contextual bar —, its height going from
    the ground's (a platform's) at its start to that at its end, its slopes round it as a platform's. Its slope is
    told while drawing."""

    name = "terrain_ramp"
    accepts_typing = False

    def __init__(self, host):
        super().__init__(host)
        self.width = 3.0

    def options(self):
        slopes = tuple((k, t("slope." + k)) for k in earthworks.SLOPES)
        return [Option("width", t("ctx.ramp_width"), "choice", self.width,
                       tuple((w, format_length(w, decimal_sep())) for w in RAMP_WIDTHS)),
                Option("cut", t("ctx.platform_cut"), "choice", self.cut, slopes),
                Option("fill", t("ctx.platform_fill"), "choice", self.fill, slopes)]

    def set_option(self, key, value):
        if key == "width" and float(value) in RAMP_WIDTHS:
            self.width = float(value)
        else:
            super().set_option(key, value)

    def _heights(self, end):
        """Its heights at its start and at `end` (the ground's there, platforms and all) — None off the terrain."""
        guid = self.terrain()
        if guid is None or not self._points:
            return None
        verts, tris = self.doc.ifc.terrain_surface(guid)
        z0 = terrain_geo.height_at(verts, tris, np.asarray(self._points[0], dtype=float)[:2])
        z1 = terrain_geo.height_at(verts, tris, np.asarray(end, dtype=float)[:2])
        return None if z0 is None or z1 is None else (z0, z1)

    def hint(self):
        if self.terrain() is None:
            return t("hint.terrain_ramp.none")          # (0.325: it said «Plataforma»)
        if not self._points:
            return t("hint.terrain_ramp")
        found = self._heights(self._end) if self._end is not None else None
        if found is None:
            return t("hint.terrain_ramp_end", text="")
        return t("hint.terrain_ramp_end", text=self._describe(self._points[0], self._end, *found))

    def _describe(self, start, end, z0, z1):
        run = float(np.linalg.norm((np.asarray(end, dtype=float) - np.asarray(start, dtype=float))[:2]))
        slope = abs(z1 - z0) / run * 100.0 if run > 1e-9 else 0.0
        sep = decimal_sep()
        return t("info.terrain_ramp_shape", a=format_length(z0, sep), b=format_length(z1, sep),
                 l=format_length(run, sep), s="{:.1f}".format(slope).replace(".", sep))

    def _preview(self, end=None):
        if end is None or not self._points:
            self.viewport.clear_overlays()
            return
        ring = earthworks.ramp_outline(self._points[0], end, self.width)
        found = self._heights(end)
        if ring is None or found is None:
            return
        plat = earthworks.Platform(ring, found[0], axis=[tuple(np.asarray(self._points[0])[:2]),
                                                          tuple(np.asarray(end)[:2])], z_end=found[1])
        z = plat.heights(np.array(ring)) + 0.02
        pts = [np.array((x, y, h)) for (x, y), h in zip(ring, z)]
        segs = []
        for a, b in zip(pts, pts[1:] + pts[:1]):
            segs += [a, b]
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self.terrain() is None:
            self.host.message(t("hint.terrain_ramp.none"), warning=True)
            return
        p, _snap = self._plan_point(x, y, modifiers)
        if p is None:
            return
        if not self._points:
            self._points = [p]
            self.host.set_hint(self.hint())
            return
        self.finish(p)

    def enter(self):
        pass

    def finish(self, end=None):
        """The ramp on the terrain, to `end`. Returns (cut, fill) m³, or None."""
        guid = self.terrain()
        if guid is None or not self._points or end is None:
            return None
        start = self._points[0]
        found = self._heights(end)
        try:
            if found is None:
                raise ValueError("off the terrain")
            cut, fill = bim.add_terrain_ramp(self.doc, guid, start, end, self.width, earthworks.SLOPES[self.cut],
                                             earthworks.SLOPES[self.fill])
        except ValueError:
            self.host.message(t("err.terrain_ramp"), warning=True)
            return None
        self.host.message(t("info.terrain_ramp", text=self._describe(start, end, *found), c=volume_text(cut),
                            f=volume_text(fill)))
        self._points, self._end = [], None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        return cut, fill


class PlatformOutlineTool(SlabOutlineTool):
    """Editar plataforma (0.204): a platform's corners as grips, at its height — picked up and put down, one added
    in a side's middle, one taken away (Delete), a distance typed —, its slopes and the ground round it made again
    each time (one undo step), as a slab's outline (0.100). A terrain with several platforms: a click inside one
    picks it."""

    name = "platform_outline"
    title = "tool.platform_outline"

    def __init__(self, host):
        super().__init__(host)
        self.index = None

    def edit(self, guid, index=None):
        """Start editing this terrain's platform (its index; None: the only one, else the one clicked)."""
        self.guid, self.index = guid, index
        self.host.set_tool(self.name)

    def _platforms(self):
        try:
            return self.doc.ifc.terrain_platforms(self.guid) if self.guid and not self.doc.loading else []
        except Exception:                                   # (the terrain gone)
            return []

    def _load(self):
        platforms = self._platforms()
        if self.index is not None and self.index >= len(platforms):
            self.index = None
        if self.index is None and len(platforms) == 1:
            self.index = 0
        self.viewport.clear_overlays()
        if self.index is None:
            self._ring = []
            self.viewport.show_grips()
            segs = []                                        # (the platforms to choose from)
            for plat in platforms:
                pts = [np.array((x, y, plat.z + 0.02)) for x, y in plat.outline]
                for a, b in zip(pts, pts[1:] + pts[:1]):
                    segs += [a, b]
            if segs:
                self.viewport.show_lines(segs, [PREVIEW] * len(segs))
            self.host.set_hint(self.hint())
            return
        plat = platforms[self.index]
        self._ring = [(float(x), float(y)) for x, y in plat.outline]
        self._z = float(plat.z)
        self.viewport.show_alignments()
        self._show()

    def hint(self):
        if not self._ring:
            return t("hint.platform_pick") if self._platforms() else t("hint.platform_outline_none")
        return t("hint.slab_outline_move") if self._picked is not None else t("hint.platform_outline")

    def pointer_down(self, x, y, button, modifiers):
        if button == LEFT and not self._ring:
            from shapely.geometry import Point, Polygon
            origin, direction = self.viewport.ray(x, y)
            for k, plat in enumerate(self._platforms()):     # (the one under the mouse, at its height)
                if abs(direction[2]) < 1e-9:
                    break
                s = (plat.z - origin[2]) / direction[2]
                p = origin + direction * s
                if s > 0 and Polygon(plat.outline).buffer(1e-6).contains(Point(float(p[0]), float(p[1]))):
                    self.index = k
                    self._load()
                    return
            return
        super().pointer_down(x, y, button, modifiers)

    def delete(self):
        if (self._picked is not None or self._chosen is not None) and len(self._ring) <= 3:
            self.host.message(t("err.platform_three_corners"), warning=True)
            return
        super().delete()

    def _apply(self, ring, text):
        from shapely.geometry import Polygon
        self._drop()
        poly = Polygon(ring) if len(ring) >= 3 else None
        if poly is None or not poly.is_valid or poly.area < 0.01:
            self.host.message(t("err.platform_outline_bad"), warning=True)
            self._load()
            return
        try:
            cut, fill = bim.set_platform(self.doc, self.guid, self.index, outline=ring)
        except (ValueError, IndexError):
            self.host.message(t("err.platform_outline_bad"), warning=True)
            self._load()
            return
        self.host.message("{} {}".format(text, t("info.platform_volumes", c=volume_text(cut), f=volume_text(fill))))
