"""Perforated panel (0.389), the ArqSynth Modeler's «Painel perfurado» as a command of its own: over a wall's face
the panel shows (its boards' joints); a click covers the whole face (all its height, following the wall), a drag from
one corner to the other a rectangle of it; a click on a perforated panel already there chooses it (its measures in
the Properties). The panel is a perforated finish (IfcCovering CLADDING «perfurado»): round or square holes, on a
square grid or one turned 45°, boards of a size with a joint between them, and a picture that makes the holes as big
as it is dark (model/image_masks.py)."""

import os

import numpy as np

from ..core import surfaces
from ..core.openings import face_rectangle
from ..core.units import format_length
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import DRAG_THRESHOLD_PX, LEFT, RIGHT, Option, Tool
from .bim_draw import length_option

CHOOSE = "__escolher__"                 # the picture choice that opens the file dialog
OUT = 0.012                             # m: the preview just off the face


def _fmt(v):
    return format_length(v, decimal_sep())


class PerforatedPanelTool(Tool):
    name = "perforated_panel"
    placement = True
    keys_help = "keys.perforated_panel"

    def __init__(self, host):
        super().__init__(host)
        d = surfaces.DEFAULTS["perfurado"]
        self.hole, self.grid = d["hole"], d["grid"]
        self.diameter, self.pitch, self.margin = d["diameter"], d["pitch"], d["margin"]
        self.sheet_w, self.sheet_h = d["sheet_w"], d["sheet_h"]
        self.joint = 0.01                        # (a panel's boards a little apart, as they are hung: a shadow gap)
        self.mask = ""
        self._press = None                       # (wall, frame, side, (x, z) on the face, (sx, sy))
        self._frames = {}

    # ------------------------------------------------------------ the bar

    def options(self):
        masks = [("", t("mask.none"))]
        if self.mask:
            masks.append((self.mask, os.path.basename(self.mask)))
        masks.append((CHOOSE, t("mask.choose")))
        return [Option("hole", t("ctx.hole_shape"), "choice", self.hole,
                       tuple((k, t("hole." + k)) for k in surfaces.HOLE_SHAPES)),
                Option("grid", t("ctx.hole_grid"), "choice", self.grid,
                       tuple((k, t("grid." + k)) for k in surfaces.GRIDS)),
                length_option("diameter", "ctx.hole_size", self.diameter),
                length_option("pitch", "ctx.hole_pitch", self.pitch),
                length_option("margin", "ctx.hole_margin", self.margin),
                length_option("sheet_w", "ctx.sheet_w", self.sheet_w),
                length_option("sheet_h", "ctx.sheet_h", self.sheet_h),
                length_option("joint", "ctx.sheet_joint", self.joint),
                Option("mask", t("ctx.mask"), "choice", self.mask, tuple(masks))]

    def set_option(self, key, value):
        if key == "hole" and value in surfaces.HOLE_SHAPES:
            self.hole = value
        elif key == "grid" and value in surfaces.GRIDS:
            self.grid = value
        elif key == "mask":
            if value == CHOOSE:
                chosen = self.host.choose_image()
                if chosen:
                    self.mask = chosen
            else:
                self.mask = value or ""
        elif key in ("diameter", "pitch") and value > 0.001:
            setattr(self, key, float(value))
        elif key == "margin" and value >= 0.0:
            self.margin = float(value)
        elif key in ("sheet_w", "sheet_h") and value >= 0.1:
            setattr(self, key, float(value))
        elif key == "joint" and 0.0 <= value < 0.1:
            self.joint = float(value)
        if self.pitch <= self.diameter + 0.002:
            self.host.message(t("warn.hole_pitch", d=_fmt(self.diameter), p=_fmt(self.pitch)), warning=True)
        self.host.set_hint(self.hint())

    def hint(self):
        return t("hint.perforated_panel", h=t("hole." + self.hole).lower(), d=_fmt(self.diameter),
                 p=_fmt(self.pitch))

    def pattern(self):
        """The panel's measures, as set_cladding takes them."""
        return {"hole": self.hole, "grid": self.grid, "diameter": self.diameter, "pitch": self.pitch,
                "margin": self.margin, "sheet_w": self.sheet_w, "sheet_h": self.sheet_h, "joint": self.joint,
                "mask": self.mask}

    # ------------------------------------------------------------ where

    def _frame(self, wall):
        obj = self.doc.get(wall)
        cached = self._frames.get(wall)
        if cached is None or cached[0] != id(obj.mesh):
            cached = (id(obj.mesh), bim.wall_frame(self.doc, wall))
            self._frames[wall] = cached
        return cached[1]

    def _under(self, x, y):
        """("panel", its GlobalId) over a perforated panel; ("face", wall, frame, side, local point) over a wall's
        face (or another finish on it); None."""
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None
        obj = self.doc.get(hit[0])
        if obj is None or not obj.is_bim:
            return None
        kind = self.doc.ifc.kind_of(obj.id)
        if kind == "cladding":
            p = self.doc.ifc._params(self.doc.ifc.by_guid(obj.id))
            if p.get("Acabamento") == "perfurado":
                return ("panel", obj.id)
            wall = p.get("Parede")
            if self.doc.get(wall) is None:
                return None
            frame = self._frame(wall)
            side = 1 if int(p.get("Lado") or 1) > 0 else -1
            return ("face", wall, frame, side, frame.to_local(hit[2])) if frame is not None else None
        if kind != "wall":
            return None
        frame = self._frame(obj.id)
        if frame is None:
            return None
        side = frame.face_side(obj.mesh.face_normal(hit[1]))
        local = frame.to_local(hit[2])
        if side == 0 and self.viewport.plan:
            side = -1 if local[1] < (frame.y0 + frame.y1) / 2 else 1
        if not side:
            return None
        panel = self._panel_at(obj.id, frame, side, local)
        return ("panel", panel) if panel else ("face", obj.id, frame, side, local)

    def _panel_at(self, wall, frame, side, local):
        """A perforated panel on this face where the point is — the ray went through one of its holes to the wall."""
        ifc = self.doc.ifc
        x, z = self._on_face(frame, local)
        for guid in ifc.claddings_of([wall]):
            p = ifc._params(ifc.by_guid(guid))
            if p.get("Acabamento") != "perfurado" or (1 if int(p.get("Lado") or 1) > 0 else -1) != side:
                continue
            x0, z0, x1, z1 = ifc.cladding_box(p, frame)
            if x0 - frame.x0 - 1e-6 <= x <= x1 - frame.x0 + 1e-6 and z0 - 1e-6 <= z <= z1 + 1e-6:
                return guid
        return None

    @staticmethod
    def _on_face(frame, local):
        """(x, z) of a point on the face: along the wall from its start, up from its base — kept on it."""
        x = min(max(float(local[0]), frame.x0), frame.x0 + frame.length) - frame.x0
        z = min(max(float(local[2]) - frame.z0, 0.0), frame.height)
        return x, z

    def _show(self, frame, side, x0, z0, x1, z1, whole):
        """The panel's outline on the face and its boards' joints."""
        normal = frame.matrix[:3, 1] / np.linalg.norm(frame.matrix[:3, 1]) * side * OUT
        ring = [p + normal for p in face_rectangle(frame, frame.x0 + x0, x1 - x0, z0, z1 - z0, side)]
        segs = [q for a, b in zip(ring, ring[1:] + ring[:1]) for q in (a, b)]
        y = frame.y1 if side > 0 else frame.y0
        u = x0 + self.sheet_w
        while u < x1 - 1e-6:                     # (the boards' joints, from the panel's corner)
            segs += [frame.to_world((frame.x0 + u, y, frame.z0 + z0)) + normal,
                     frame.to_world((frame.x0 + u, y, frame.z0 + z1)) + normal]
            u += self.sheet_w
        v = z0 + self.sheet_h
        while v < z1 - 1e-6:
            segs += [frame.to_world((frame.x0 + x0, y, frame.z0 + v)) + normal,
                     frame.to_world((frame.x0 + x1, y, frame.z0 + v)) + normal]
            v += self.sheet_h
        self.viewport.show_polygon(ring, segments=segs, colors=[PREVIEW] * len(segs))
        tip = t("tip.perforated_whole") if whole else "{} × {}".format(_fmt(x1 - x0), _fmt(z1 - z0))
        self.viewport.show_tip(tip, ring[2])

    # ------------------------------------------------------------ the mouse

    def pointer_move(self, x, y, modifiers):
        if self._press is not None:
            wall, frame, side, (ax, az), _screen = self._press
            found = self._under(x, y)
            if found is not None and found[0] == "face" and found[1] == wall and found[3] == side:
                bx, bz = self._on_face(frame, found[4])
            else:                                # (off the face: where the ray meets its plane)
                point = self._on_plane(frame, side, x, y)
                if point is None:
                    return
                bx, bz = self._on_face(frame, frame.to_local(point))
            self._show(frame, side, min(ax, bx), min(az, bz), max(ax, bx), max(az, bz), False)
            self.host.set_vcb("{} × {}".format(_fmt(abs(bx - ax)), _fmt(abs(bz - az))))
            return
        found = self._under(x, y)
        if found is None:
            self.viewport.clear_overlays()
            return
        if found[0] == "panel":
            self.viewport.clear_overlays()
            self.viewport.show_tip(t("tip.perforated_pick"), self.viewport.pick_point(x, y)[2])
            return
        _kind, _wall, frame, side, _local = found
        self._show(frame, side, 0.0, 0.0, frame.length, frame.height, True)

    def _on_plane(self, frame, side, x, y):
        origin, direction = self.viewport.ray(x, y)
        n = frame.matrix[:3, 1] / np.linalg.norm(frame.matrix[:3, 1])
        point = frame.to_world((frame.x0, frame.y1 if side > 0 else frame.y0, frame.z0))
        d = float(np.dot(direction, n))
        if abs(d) < 1e-9:
            return None
        s = float(np.dot(point - origin, n)) / d
        return origin + direction * s if s > 0 else None

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        found = self._under(x, y)
        if found is None:
            self.host.message(t("err.no_wall"), warning=True)
            return
        if found[0] == "panel":                  # (as the addon: a panel already there is chosen, to edit it)
            self.viewport.set_selection({found[1]})
            self.host.message(t("info.perforated_picked", name=self.doc.get(found[1]).name))
            return
        _kind, wall, frame, side, local = found
        self._press = (wall, frame, side, self._on_face(frame, local), (x, y))

    def pointer_up(self, x, y, button, modifiers):
        if button != LEFT or self._press is None:
            return
        wall, frame, side, (ax, az), (sx, sy) = self._press
        self._press = None
        self.host.set_vcb("")
        region = None
        if max(abs(x - sx), abs(y - sy)) > DRAG_THRESHOLD_PX:      # (dragged: the rectangle drawn)
            point = self._on_plane(frame, side, x, y)
            if point is not None:
                bx, bz = self._on_face(frame, frame.to_local(point))
                if abs(bx - ax) < 0.05 or abs(bz - az) < 0.05:
                    self.viewport.clear_overlays()
                    self.host.message(t("err.perforated_small"), warning=True)
                    return
                region = {"start": min(ax, bx), "end": max(ax, bx), "base": min(az, bz)}
                top = max(az, bz)
        try:
            guid = bim.add_cladding(self.doc, wall, side, "perfurado", top if region else 0.0, self.pattern(),
                                    region)
        except ValueError as exc:
            self.viewport.clear_overlays()
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        self.viewport.clear_overlays()
        d = self.doc.ifc.pattern_params(guid)
        self.host.message(t("info.perforated", name=self.doc.get(guid).name, n=d["count"],
                            a="{:.0f}".format(100 * d["open_area"]), wall=self.doc.get(wall).name))

    def cancel(self):
        self._press = None
        self.viewport.clear_overlays()
