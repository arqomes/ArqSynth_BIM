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
the fillet waits for a second click (or the radius typed)."""

import numpy as np

from ..core import curves as core_curves
from ..core import slabs as core_slabs
from ..core.sketch_geometry import ray_plane
from ..core.units import format_length, parse_length
from ..i18n import decimal_sep, refusal, t
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, Tool, moved_enough

Z = np.array((0.0, 0.0, 1.0))
FACE_GAP = 0.01                     # m: the grips a hair off the face (seen in front of it)
FRAME_MARGIN = 1.0                  # m: (0.378) room round the wall seen square on (for the arcs drawn above it)


def _fmt(v):
    return format_length(v, decimal_sep())


def side_kind(modifiers):
    """(0.380) What a straight side pulled by its middle becomes, by the keys held: Shift an arc, Alt a curve, else
    a new corner."""
    mods = modifiers or ()
    return "arc" if "Shift" in mods else "bezier" if "Alt" in mods else "corner"


class WallProfileTool(Tool):
    name = "wall_profile"
    title = "tool.wall_profile"
    placement = True                # (Esc: back to Select)
    keys_help = "keys.wall_profile"

    def __init__(self, host):
        super().__init__(host)
        self.guid = None
        self._pts = []              # its profile's corners [(x, z)] in the wall's frame
        self._sides = []            # (0.375) side i, from corner i to i + 1: None (straight), an arc or a Bézier
        self._frame = None          # (base point of its start, along, across towards the face seen, length)
        # ("corner", k) | ("side", side: a straight one pulled by its middle) | ("through" | "h1" | "h2", side) |
        # ("fillet", k)
        self._picked = None
        self._end = None
        self._press = None          # (0.378) where the grip was pressed: let go elsewhere, it is put down there
        self._chosen = None         # (0.381) a grip clicked (not dragged): what Delete takes away / straightens
        self._mods = ()             # (0.380) Shift / Alt held, as last seen
        self._radius = None         # (0.380) the fillet's radius, as last shown
        self._camera = None         # (0.378) the camera before it turned to the wall (put back on leaving)
        self._mids = []             # what each middle grip is: (side, "mid" | "through" | "h1" | "h2")
        host.doc.subscribe(self._changed)

    @property
    def accepts_typing(self):
        """(0.380) A fillet's radius is typed (Measurements box, Enter)."""
        return self._picked is not None and self._picked[0] == "fillet"

    def vcb_title(self):
        return t("vcb.radius") if self.accepts_typing else None

    def edit(self, guid):
        self.guid = guid
        self.host.set_tool(self.name)

    def activate(self):
        super().activate()
        self._camera = None
        self._mods = ()
        self._load()
        self._face_the_wall()

    def deactivate(self):
        self._pick(None)
        self._press = None
        self.viewport.show_grips()
        self.viewport.clear_overlays()
        camera, self._camera = self._camera, None
        if camera is not None and self.viewport.current_view() is None:
            self.viewport.restore_camera(camera)     # (0.378) the 3D view as it was before the wall was edited

    def _pick(self, picked):
        """What is picked up now (None: nothing) — the Measurements box asks for a radius while it is a fillet."""
        typing = self.accepts_typing
        self._picked, self._end, self._radius, self._chosen = picked, None, None, None
        if typing != self.accepts_typing and hasattr(self.host, "vcb_title_changed"):
            self.host.vcb_title_changed()

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
        return [Option("plain", t("ctx.wall_plain"), "toggle", False)]

    def set_option(self, key, value):
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
            self._pts, self._sides = [], []
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
            self._pts = [(0.0, 0.0), (length, 0.0), (length, height), (0.0, height)]
            self._sides = [None] * 4
        else:
            self._pts, self._sides = list(parts[0]), list(parts[1])
        self.viewport.clear_overlays()
        self._show()

    def _world(self, pts):
        base, along, _across, _l = self._frame
        return [base + along * x + Z * z for x, z in pts]

    def _show(self, pts=None, sides=None):
        """The profile — its curved sides in pieces — with its grips: squares on the corners; diamonds in the straight
        sides' middles, on the arcs' points they pass through and on the Bézier curves' tangents (their lines). Only
        its outline, while something moves too (0.378: a translucent fill of the new profile over the wall left the
        part to be cut in the wall's grey, as if it were what stays)."""
        pts = self._pts if pts is None else pts
        sides = self._sides if sides is None else sides
        w = self._world(pts)
        middles, arrows, self._mids = [], [], []
        for i, side in enumerate(sides):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            if not side:
                middles.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
                self._mids.append((i, "mid"))
            elif side["kind"] == "arc":
                middles.append(side["through"])
                self._mids.append((i, "through"))
            else:
                for name, corner in (("h1", a), ("h2", b)):
                    middles.append(side[name])
                    self._mids.append((i, name))
                    arrows += self._world([corner, side[name]])
        ring = self._world(core_curves.profile_outline(pts, sides))
        self.viewport.show_grips(w, self._world(middles), (), arrows)
        segs = [q for a, b in zip(ring, ring[1:] + ring[:1]) for q in (a, b)]
        self.viewport.show_lines(segs, [PREVIEW] * len(segs))
        self.host.set_hint(self.hint())

    def hint(self):
        if not self._pts:
            return t("hint.wall_profile_none")
        if self._picked is None:
            return t("hint.wall_profile")
        what = self._picked[0]
        return t({"corner": "hint.wall_profile_move", "side": "hint.wall_profile_side",
                  "fillet": "hint.wall_profile_fillet"}.get(what, "hint.wall_profile_curve"))

    def _local(self, x, y):
        """(x along, z up) of the point under the mouse in the wall's plane, kept within its length."""
        base, along, across, length = self._frame
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, base, across)
        if p is None:
            p = ray_plane(origin, direction, base, -across)
        if p is None:
            return None
        lx = float(np.clip((p - base) @ along, 0.0, length))
        lz = max(float((p - base) @ Z), 0.0)
        for q in self._pts:                          # (lined up with the other corners, as the snaps would)
            if abs(lx - q[0]) < 0.05:
                lx = q[0]
            if abs(lz - q[1]) < 0.05:
                lz = q[1]
        return lx, lz

    def _moved(self, q):
        """(corners, sides) with the grip picked up taken to q: a corner takes its tangents along; a straight side
        pulled by its middle — by the keys held — a new corner, an arc or a curve through q; a fillet of the radius
        the distance from its corner to q (or the one typed)."""
        pts, sides = list(self._pts), [dict(s) if s else None for s in self._sides]
        what, k = self._picked
        if what == "corner":
            d = (q[0] - pts[k][0], q[1] - pts[k][1])
            pts[k] = q
            for i, name in ((k, "h1"), ((k - 1) % len(pts), "h2")):
                side = sides[i]
                if side and side["kind"] == "bezier":
                    side[name] = (side[name][0] + d[0], side[name][1] + d[1])
        elif what == "side":
            kind = side_kind(self._mods)
            a, b = pts[k], pts[(k + 1) % len(pts)]
            if kind == "corner":
                pts.insert(k + 1, q)
                sides.insert(k + 1, None)
            elif kind == "arc":
                sides[k] = {"kind": "arc", "through": q}
            else:                                    # both tangents moved alike, 4/3 of the pull: its middle on q
                dx = (q[0] - (a[0] + b[0]) / 2) * 4.0 / 3.0
                dz = (q[1] - (a[1] + b[1]) / 2) * 4.0 / 3.0
                sides[k] = {"kind": "bezier",
                            "h1": (a[0] + (b[0] - a[0]) / 3 + dx, a[1] + (b[1] - a[1]) / 3 + dz),
                            "h2": (a[0] + (b[0] - a[0]) * 2 / 3 + dx, a[1] + (b[1] - a[1]) * 2 / 3 + dz)}
        elif what == "fillet":
            radius = self._radius if q is None else float(np.hypot(q[0] - pts[k][0], q[1] - pts[k][1]))
            done = core_curves.fillet(pts, sides, k, radius)
            if done is not None:
                pts, sides, self._radius = done
        else:
            sides[k][what] = q
        return pts, sides

    def _tip(self, q):
        """What is said beside the grip picked up: the radius of a fillet; what a pulled side becomes; where."""
        where = "{} ; {}".format(_fmt(q[0]), _fmt(q[1]))
        what, k = self._picked
        if what == "fillet":
            return t("tip.profile_fillet", r=_fmt(self._radius or 0.0)), self._world([self._pts[k]])[0]
        if what == "side":
            return t("tip.profile_side_drop", m=t("profkind." + side_kind(self._mods)), p=where), self._world([q])[0]
        return t("tip.profile_drop", p=where), self._world([q])[0]

    def _preview(self, q):
        self._end = q
        self._show(*self._moved(q))
        self.viewport.show_tip(*self._tip(q))

    def modifiers_changed(self, modifiers):
        """(0.380) Shift / Alt pressed or let go: a side pulled shows at once what it becomes."""
        self._mods = tuple(modifiers or ())
        if self._picked is not None and self._picked[0] == "side" and self._end is not None:
            self._preview(self._end)

    def pointer_move(self, x, y, modifiers):
        if not self._pts:
            return
        self._mods = tuple(modifiers or ())
        if self._picked is None:
            grip = self.viewport.grip_at(x, y)
            if grip is None:
                self.viewport.show_tip("", None)
            else:
                kind, k = grip
                at = self.viewport.grips[0][k] if kind == "end" else self.viewport.grips[1][k]
                tip = "tip.profile_corner" if kind == "end" else (
                    "tip.profile_side" if self._mids[k][1] == "mid" else "tip.profile_curve")
                self.viewport.show_tip(t(tip), at)
            return
        q = self._local(x, y)
        if q is not None:
            self._preview(q)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._picked is not None:
                self.cancel()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT or not self._pts:
            return
        self._mods = tuple(modifiers or ())
        if self._picked is not None:                 # (0.381: only a fillet waits for this second click)
            if self._end is not None:
                self._apply(*self._moved(self._end))
            return
        grip = self.viewport.grip_at(x, y)
        if grip is None:
            self._chosen = None                      # (a click beside the grips: none chosen)
            return
        self._press = (float(x), float(y))           # (0.378: let go elsewhere — a drag — it is put down there)
        kind, k = grip
        if kind == "end":
            if "Alt" in self._mods:                  # (0.380) Alt and a click on a corner: a fillet
                if core_curves.fillet(self._pts, self._sides, k, 0.01) is None:
                    self.host.message(t("err.profile_fillet"), warning=True)
                    return
                self._pick(("fillet", k))
                self.host.set_hint(self.hint())
                return
            self._pick(("corner", k))
            self._show()
            return
        side, what = self._mids[k]
        self._pick(("side", side) if what == "mid" else (what, side))
        self._show()

    def pointer_up(self, x, y, button, modifiers):
        """(0.378) A grip pressed, dragged and let go: put down there. (0.381) Pressed and let go in place — a click —:
        nothing moves; the grip is chosen (Delete takes the corner away, straightens the curve). Only a fillet (Alt and
        a click on a corner) stays, its radius following the mouse until a second click or Enter."""
        press, self._press = self._press, None
        if button != LEFT or press is None or self._picked is None:
            return
        self._mods = tuple(modifiers or ())
        if moved_enough(press, (x, y)):
            if self._end is not None:
                self._apply(*self._moved(self._end))
            return
        if self._picked[0] == "fillet":
            return
        chosen = self._picked
        self._pick(None)
        self._chosen = chosen
        self._show()
        what = chosen[0]
        if what != "side":
            self.viewport.show_tip(t("tip.profile_chosen_corner" if what == "corner" else "tip.profile_chosen_curve"),
                                   self._world([self._grip_point(chosen)])[0])

    def _grip_point(self, which):
        """(x, z) of a grip: a corner, an arc's point, a tangent."""
        what, k = which
        if what == "corner":
            return self._pts[k]
        return self._sides[k][what]

    def typed(self, text):
        """(0.380) A fillet's radius typed, Enter: the corner rounded by it."""
        if not self.accepts_typing:
            return
        radius = parse_length(text)
        if radius is None or radius <= 0:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        self._radius = radius
        self._apply(*self._moved(None))

    def delete(self):
        target = self._picked or self._chosen        # (0.381: a grip moving, or one clicked)
        if target is None or (target[0] == "side" and self._picked is None):
            self.host.message(t("info.profile_pick_first"), warning=True)
            return
        what, k = target
        if what in ("fillet", "side"):               # (nothing made yet: given up)
            self.cancel()
            return
        if what != "corner":                         # (a curve's grip: the side straight again)
            sides = list(self._sides)
            sides[k] = None
            self._apply(self._pts, sides)
            return
        if len(self._pts) <= 3:
            self.host.message(t("err.slab_three_corners"), warning=True)
            return
        sides = list(self._sides)
        sides[(k - 1) % len(sides)] = None           # (the two sides meeting there are one straight side now)
        del sides[k]
        self._apply([p for i, p in enumerate(self._pts) if i != k], sides)

    def _apply(self, pts, sides=None):
        self._pick(None)
        if core_slabs.outline_polygon(core_curves.profile_outline(pts, sides)) is None:
            self.host.message(t("err.profile_bad"), warning=True)
            self._load()
            return
        try:
            bim.set_wall_profile(self.doc, self.guid, pts, sides)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self._load()
            return
        curved = sum(1 for s in (sides or []) if s)
        self.host.message(t("info.wall_profile_curves", n=curved) if curved else t("info.wall_profile"))

    def cancel(self):
        self._pick(None)
        self.viewport.clear_overlays()
        self._load()
