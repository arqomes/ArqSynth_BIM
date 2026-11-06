"""Ripado (0.434), the addon's «Ripado» as a command of its own, as the perforated panel's (0.389): over a wall's face
the panel shows (its slats); a click covers the whole face (all its height, following the wall), a drag from one corner
to the other a rectangle of it; a click on a slatted panel already there chooses it (its measures in the Properties).
The panel is a slatted finish (IfcCovering CLADDING «ripado»): slats upright or level, of a width and a thickness, at
a pitch (axis to axis), centred on it; a frame round it; battens behind the slats and across them, which stand them
off the wall (core/surfaces.ripado_parts)."""

from ..core import surfaces
from ..i18n import t
from .bim_draw import length_option
from .base import Option
from .perforated import PerforatedPanelTool, _fmt

MAX_SHOWN = 400                         # slats drawn while the mouse moves over a face (more: only the outline)


class RipadoTool(PerforatedPanelTool):
    name = "ripado_panel"
    keys_help = "keys.ripado_panel"
    FINISH = "ripado"
    PICK_TIP, PICKED = "tip.ripado_pick", "info.ripado_picked"

    def __init__(self, host):
        super().__init__(host)
        d = surfaces.DEFAULTS["ripado"]
        self.direction = d["direction"]
        self.width, self.depth, self.pitch = 0.04, 0.04, 0.08          # (the addon's: 4 × 4 cm at 8 cm)
        self.frame, self.battens = 0.0, 0
        self.batten_w, self.batten_d = d["batten_w"], d["batten_d"]

    # ------------------------------------------------------------ the bar

    def options(self):
        return [Option("direction", t("props.slat_direction"), "choice", self.direction,
                       (("vertical", t("slat.vertical")), ("horizontal", t("slat.horizontal")))),
                length_option("width", "props.slat_width", self.width),
                length_option("depth", "props.slat_depth", self.depth),
                length_option("pitch", "props.slat_pitch", self.pitch),
                length_option("frame", "props.ripado_frame", self.frame),
                Option("battens", t("props.ripado_battens"), "choice", str(self.battens),
                       tuple((str(n), t("ripado.no_battens") if n == 0 else str(n)) for n in range(0, 7)))]

    def set_option(self, key, value):
        if key == "direction" and value in ("vertical", "horizontal"):
            self.direction = value
        elif key == "battens":
            try:
                self.battens = max(0, min(surfaces.MAX_BATTENS, int(value)))
            except (TypeError, ValueError):
                pass
        elif key in ("width", "depth") and 0.003 <= value <= 0.30:
            setattr(self, key, float(value))
        elif key == "pitch" and value > 0.005:
            self.pitch = float(value)
        elif key == "frame" and 0.0 <= value < 1.0:
            self.frame = float(value)
        if self.pitch < self.width + 1e-6:
            self.host.message(t("warn.slat_pitch", w=_fmt(self.width), p=_fmt(self.pitch)), warning=True)
        self.host.set_hint(self.hint())

    def hint(self):
        return t("hint.ripado_panel", w=_fmt(self.width), d=_fmt(self.depth), p=_fmt(self.pitch))

    def pattern(self):
        """The panel's measures, as set_cladding takes them (the gap: the pitch less the slat)."""
        return {"direction": self.direction, "width": self.width, "gap": max(0.0, self.pitch - self.width),
                "thickness": self.depth, "frame": self.frame, "battens": self.battens,
                "batten_w": self.batten_w, "batten_d": self.batten_d}

    # ------------------------------------------------------------ what is shown

    def _inside(self, frame, side, x0, z0, x1, z1, normal):
        """Its slats' edges (inside its frame), as they will be — the outline alone if there are too many."""
        from shapely.geometry import box
        d = dict(self.pattern())
        try:
            band, _battens, slats, _inner = surfaces.ripado_parts(box(x0, z0, x1, z1), d)
        except ValueError:
            return []
        if len(slats) > MAX_SHOWN:
            return []
        y = frame.y1 if side > 0 else frame.y0
        segs = []

        def at(u, v):
            return frame.to_world((frame.x0 + u, y, frame.z0 + v)) + normal

        if band is not None:                     # (the frame's inner edge)
            f = self.frame
            ring = [(x0 + f, z0 + f), (x1 - f, z0 + f), (x1 - f, z1 - f), (x0 + f, z1 - f)]
            for a, b in zip(ring, ring[1:] + ring[:1]):
                segs += [at(*a), at(*b)]
        level = self.direction == "horizontal"
        for u0, v0, u1, v1 in slats:             # (each slat's two long edges)
            if level:
                segs += [at(u0, v0), at(u1, v0), at(u0, v1), at(u1, v1)]
            else:
                segs += [at(u0, v0), at(u0, v1), at(u1, v0), at(u1, v1)]
        return segs

    def _made(self, guid, wall):
        d = self.doc.ifc.pattern_params(guid)
        self.host.message(t("info.ripado", name=self.doc.get(guid).name, n=d["count"], wall=self.doc.get(wall).name))
