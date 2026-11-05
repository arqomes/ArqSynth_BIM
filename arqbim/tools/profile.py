"""Profile Pen (0.174): a profile — a skirting board, a cornice, a dado rail, an outside cornice — round a room (a
click inside it: along its walls' faces, broken at its doors) or along a path clicked point by point (Enter ends
it; a click on its first point closes it; Delete takes the last point back) — Tab changes which; the profile, its
side and its height over the floor on the contextual bar."""

import numpy as np

from ..core import profiles as core_profiles
from ..core.units import format_length
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, show_snap
from .bim_draw import MIN_LENGTH, _PointTool, length_option
from .wall_edit import _wall_at

SHAPES = ("room", "path")
CLOSE = 0.05                # m: a click this near the path's first point closes it


def _fmt(v):
    return format_length(v, decimal_sep())


class ProfileTool(_PointTool):
    name = "profile"
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.profile"

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.shape = "room"
        self.profile = "rodape"
        self.side = 1
        self.foot = core_profiles.PROFILES["rodape"][3]
        self._points = []

    def activate(self):
        if self.profile not in dict(bim.profile_choices(self.doc)):      # (an own profile of another project)
            self.profile, self.foot = "rodape", core_profiles.PROFILES["rodape"][3]
        super().activate()

    def options(self):
        out = [Option("shape", t("ctx.profile_shape"), "choice", self.shape,
                      tuple((s, t("profshape." + s)) for s in SHAPES)),
               Option("profile", t("ctx.profile"), "choice", self.profile,
                      tuple(bim.profile_choices(self.doc)))]          # (0.245: the project's own too)
        if self.shape == "path":
            out.append(Option("side", t("ctx.profile_side"), "choice", str(self.side),
                              (("1", t("profside.left")), ("-1", t("profside.right")))))
        if self.foot is not None:                       # (a cornice goes under the walls' top: no height asked)
            out.append(length_option("foot", "ctx.profile_foot", self.foot))
        return out

    def set_option(self, key, value):
        if key == "shape" and value in SHAPES:
            self.shape = value
            self.cancel()
        elif key == "profile" and value in dict(bim.profile_choices(self.doc)):
            self.profile = value
            self.foot = core_profiles.foot(value, 0.0, 0.0) if core_profiles.is_custom(value) else \
                core_profiles.PROFILES[value][3]
        elif key == "side":
            self.side = 1 if int(value) > 0 else -1
        elif key == "foot" and 0.0 <= value <= 10.0:
            self.foot = float(value)
        self.host.set_hint(self.hint())

    def tab(self):
        self.set_option("shape", SHAPES[(SHAPES.index(self.shape) + 1) % len(SHAPES)])
        return True

    def hint(self):
        return t("hint.profile." + self.shape, p=bim.profile_label(self.profile).lower())

    def pointer_move(self, x, y, modifiers):
        if self.shape != "path":
            return
        last = self._points[-1] if self._points else None
        p, snap = self._point(x, y, None if last is None else last[2], last, modifiers)
        if p is None:
            return
        pts = self._points + [p]
        segs = [q for a, b in zip(pts, pts[1:]) for q in (a, b)]
        if segs:
            self.viewport.show_lines(segs, [PREVIEW] * len(segs))
        show_snap(self.viewport, snap, p)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._points:
                self.enter()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT:
            return
        if self.shape == "room":
            p, _snap = self._point(x, y, self.doc.work_level(), None, modifiers)
            guid = None if p is None else self._make(lambda: bim.room_profile(self.doc, p[:2], self.profile,
                                                                               self.foot, storey=self.doc.active_storey))
            if p is not None and guid is None:
                self.host.message(t("err.profile_room"), warning=True)
            return
        last = self._points[-1] if self._points else None
        p, _snap = self._point(x, y, None if last is None else last[2], last, modifiers)
        if p is None:
            return
        if len(self._points) > 2 and np.linalg.norm((p - self._points[0])[:2]) < CLOSE:
            self._finish(True)                          # (back on its first point: round and closed)
            return
        if last is not None and np.linalg.norm((p - last)[:2]) < MIN_LENGTH:
            return
        self._points.append(p)

    def enter(self):
        if self.shape == "path" and len(self._points) >= 2:
            self._finish(False)

    def _finish(self, closed):
        pts = [tuple(q) for q in self._points]
        self.cancel()
        self._make(lambda: bim.add_profile(self.doc, pts, self.profile, closed, self.side, self.foot,
                                           storey=self.doc.active_storey))

    def _make(self, make):
        try:
            guid = make()
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return None
        if guid is not None:
            p = self.doc.ifc.describe(guid)["params"]
            self.host.message(t("info.profile", p=bim.profile_label(p["profile"]), l=_fmt(p["length"]),
                                h=_fmt(p["foot"])))
        return guid

    def delete(self):
        if self._points:
            self._points.pop()
            self.viewport.clear_overlays()

    def cancel(self):
        self._points = []
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())


class WallSweepTool(ProfileTool):
    """(0.304) A skirting board, a cornice, a dado rail or an outside cornice on a wall, as Revit's Wall Sweep: a click
    on a wall's face — the profile runs along it and along the faces of the walls joined to it on that side (its
    corners mitred) up to a free end, or all round; broken at the doors; it follows the walls when they change. The
    profile and its height over the floor on the contextual bar."""
    name = "wall_sweep"
    keys_help = "keys.wall_sweep"
    on_storey = False                   # (it goes on its wall's storey)

    def options(self):
        out = [Option("profile", t("ctx.profile"), "choice", self.profile, tuple(bim.profile_choices(self.doc)))]
        if self.foot is not None:
            out.append(length_option("foot", "ctx.profile_foot", self.foot))
        return out

    def tab(self):
        return False

    def hint(self):
        return t("hint.wall_sweep", p=bim.profile_label(self.profile).lower())

    def activate(self):
        self._runs = {}
        super().activate()

    def _run(self, guid, point):
        """The run from a wall's face, kept per wall and side while the tool is on (not worked out at every move)."""
        s, e, _t = self.doc.ifc.wall_axis(guid)
        side = (e - s)[0] * (point[1] - s[1]) - (e - s)[1] * (point[0] - s[0]) > 0
        runs = getattr(self, "_runs", {})
        if (guid, side) not in runs:
            runs[(guid, side)] = self.doc.ifc.wall_face_run(guid, point)
            self._runs = runs
        return runs[(guid, side)]

    def pointer_move(self, x, y, modifiers):
        found = _wall_at(self, x, y)
        if found is None:
            self.viewport.clear_overlays()
            return
        run = self._run(found[0], found[1][:2])
        if run is None:
            self.viewport.clear_overlays()
            return
        pts, closed = run
        z = self.doc.ifc.placement(found[0])[2, 3] + (self.foot or 0.0) + 0.01
        ring = [np.array((q[0], q[1], z)) for q in pts] + ([np.array((pts[0][0], pts[0][1], z))] if closed else [])
        segs = [q for a, b in zip(ring, ring[1:]) for q in (a, b)]
        self.viewport.show_lines(segs, [PREVIEW] * (len(segs) // 2))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        found = _wall_at(self, x, y)
        guid = None if found is None else self._make(lambda: bim.wall_sweep(self.doc, found[0], found[1][:2],
                                                                            self.profile, self.foot))
        self._runs = {}
        if found is not None and guid is None:
            self.host.message(t("err.wall_sweep"), warning=True)

    def enter(self):
        pass
