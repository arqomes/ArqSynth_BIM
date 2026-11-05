"""Edit profile (0.109), as Revit's Edit Profile of a wall: the wall's elevation outline — at first its
rectangle — with grips on its corners, on the face seen: a corner is picked up and put down (in the wall's plane; its
ends and base stay within the wall); with a corner picked up, Delete takes it away. Each change is one undo step: a
gable, a stepped top, a cut-out. "Plain wall" on the contextual bar draws it as a rectangle again.

(0.375) Sides as arcs — through a point — or Bézier curves — two tangents, drawn with their lines from the corners —;
their grips move as the corners do, a corner moved takes its tangents along.

(0.378) In the 3D view the camera turns to look at the wall square on, framed (back where it was on leaving). A grip is
dragged (pressed, moved, let go) or clicked twice (picked up, put down). Only the new outline is drawn while it moves.

(0.380, the owner: «clico 2x abre a edição e ao pegar os pontos ele cria vértices. Mas se pegar e clicar em Shift ele
faz arco. Se clicar no ponto e clicar na tecla Alt ele ativa a curva Bézier. Se clicar em Alt e clicar no ponto do
canto, ele faz um fillet com controlo do raio.») No modes: a straight side's middle diamond pulled makes a new corner
there; with Shift held, the side an arc through the mouse; with Alt, a Bézier curve through it (both tangents moved
alike) — Shift and Alt can be pressed or let go while it moves, the drawing following at once. Alt and a click on a
corner: a fillet — the corner rounded by an arc tangent to its two straight sides, its radius the mouse's distance
from the corner, or typed (Enter).

(0.381, the owner: «porque não está funcionando para as curvas?») A grip moves only while the button is held: a
plain click no longer picks it up to follow the mouse until the next click. That sticky pick undid the curves — an
arc passes through the mouse, so its grip lay right under it, and the next click there (to take the balloon down, to
see) picked the arc up and dragged it across the wall. A click (no drag) on a grip now chooses it, for Delete. Only
the fillet waits for a second click (or the radius typed).

(0.410, the owner: «adicionar tanto na parede como no piso a possibilidade de desenhar (em edição) polígonos no meio
para fazer buracos personalizados») «Furo» on the contextual bar draws holes in the profile — a polygon, a rectangle,
a circle —, each with the profile's own grips (its corners, its sides made arcs or curves); a hole dragged moves,
clicked and Delete goes. The gestures are those of tools/outline_grips, shared with the slabs' and floors' outline."""

import numpy as np

from ..core import curves as core_curves
from ..core.sketch_geometry import ray_plane
from ..i18n import refusal, t
from ..model import bim
from .base import Option, Tool
from .outline_grips import OutlineGrips, side_kind  # noqa: F401  (side_kind: as before 0.410)

Z = np.array((0.0, 0.0, 1.0))
FACE_GAP = 0.01                     # m: the grips a hair off the face (seen in front of it)
FRAME_MARGIN = 1.0                  # m: (0.378) room round the wall seen square on (for the arcs drawn above it)


class WallProfileTool(OutlineGrips, Tool):
    name = "wall_profile"
    title = "tool.wall_profile"
    placement = True                # (Esc: back to Select — a hole being drawn first given up, 0.410)
    keys_help = "keys.wall_profile"
    three_corners = "err.slab_three_corners"

    def __init__(self, host):
        super().__init__(host)
        self.guid = None
        self._frame = None          # (base point of its start, along, across towards the face seen, length)
        self._camera = None         # (0.378) the camera before it turned to the wall (put back on leaving)
        host.doc.subscribe(self._changed)

    def edit(self, guid):
        self.guid = guid
        self.host.set_tool(self.name)

    def activate(self):
        super().activate()
        self._camera = None
        self._mods = ()
        self.hole_shape = ""
        self._load()
        self._face_the_wall()

    def deactivate(self):
        self._drop_all()
        self.hole_shape = ""
        self.viewport.show_grips()
        self.viewport.clear_overlays()
        camera, self._camera = self._camera, None
        if camera is not None and self.viewport.current_view() is None:
            self.viewport.restore_camera(camera)     # (0.378) the 3D view as it was before the wall was edited

    def _face_the_wall(self):
        """(0.378) In the 3D view: the camera square on to the face being edited, the wall (and room above it for
        arcs) filling the view — no F3, no turning the view by hand."""
        if not self._pts or self.viewport.current_view() is not None:
            return
        base, along, across, _length = self._frame
        outline = core_curves.profile_outline(self._pts, self._sides)
        xs, zs = [x for x, _z in outline], [z for _x, z in outline]
        centre = base + along * (min(xs) + max(xs)) / 2 + Z * (min(zs) + max(zs)) / 2
        half_w, half_h = (max(xs) - min(xs)) / 2 + FRAME_MARGIN, (max(zs) - min(zs)) / 2 + FRAME_MARGIN
        self._camera = self.viewport.camera_snapshot()
        self.viewport.view_along(-across, centre, float(np.hypot(half_w, half_h)))
        self._load()                                 # (the grips again, on the face now seen)

    def _changed(self, changed, removed):
        if self.host.tool is self:
            self._pick(None)
            self._load()

    def options(self):
        return [Option("plain", t("ctx.wall_plain"), "toggle", False), self.hole_option()]

    def set_option(self, key, value):
        if key == "hole":
            self.set_hole_shape(value)
            return
        if key == "plain" and value and self.guid is not None:
            try:
                bim.set_wall_profile(self.doc, self.guid, None)
            except ValueError as exc:
                self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
                return
            self.host.message(t("info.wall_plain"))

    def _load(self):
        ifc = self.doc.ifc
        if not self.guid or self.doc.loading or ifc.by_guid(self.guid) is None or ifc.kind_of(self.guid) != "wall":
            self._loops = []
            self.viewport.show_grips()
            self.viewport.clear_overlays()
            return
        s, e, thickness = ifc.wall_axis(self.guid)
        length, height, _t = ifc.wall_params(self.guid)
        along = (e - s) * np.array((1.0, 1.0, 0.0))
        along /= np.linalg.norm(along)
        across = np.array((-along[1], along[0], 0.0))
        _origin, direction = self.viewport.ray(*self.viewport.project((s + e) / 2 + Z * height / 2))
        if float(direction @ across) > 0:
            across = -across                        # (the face towards the eye)
        self._frame = (s + across * (thickness / 2 + FACE_GAP), along, across, length)
        parts = ifc.wall_profile_parts(self.guid)
        if parts is None:
            outline = [[(0.0, 0.0), (length, 0.0), (length, height), (0.0, height)], [None] * 4]
        else:
            outline = [list(parts[0]), list(parts[1])]
        self._loops = [outline] + [[list(c), list(s)] for c, s in ifc.wall_profile_holes(self.guid)]
        self.viewport.clear_overlays()
        self._show()

    def _world(self, pts):
        base, along, _across, _l = self._frame
        return [base + along * x + Z * z for x, z in pts]

    def _raw_local(self, x, y):
        """(x along, z up) of the point under the mouse in the wall's plane."""
        base, along, across, _length = self._frame
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, base, across)
        if p is None:
            p = ray_plane(origin, direction, base, -across)
        if p is None:
            return None
        return float((p - base) @ along), float((p - base) @ Z)

    def _local_at(self, x, y, origin=None):
        """(x along, z up) of the point under the mouse in the wall's plane, kept within its length, lined up with
        the other corners (the holes' too) as the snaps would."""
        q = self._raw_local(x, y)
        if q is None:
            return None
        length = self._frame[3]
        lx, lz = float(np.clip(q[0], 0.0, length)), max(q[1], 0.0)
        for pts, _sides in self._loops:
            for c in pts:
                if abs(lx - c[0]) < 0.05:
                    lx = c[0]
                if abs(lz - c[1]) < 0.05:
                    lz = c[1]
        return lx, lz

    def _save(self, loops, text=None):
        (pts, sides), holes = loops[0], loops[1:]
        try:
            bim.set_wall_profile(self.doc, self.guid, pts, sides, holes=holes)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self._load()
            return False
        if text:
            self.host.message(text)
            return True
        curved = sum(1 for _c, ss in loops for s in ss if s)
        self.host.message(t("info.wall_profile_curves", n=curved) if curved else t("info.wall_profile"))
        return True

