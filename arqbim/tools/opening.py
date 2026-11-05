"""Door and Window tools: hover a wall, click to place (or type the distance to
the nearest wall end + Enter). The door/window cuts a real opening in the wall
(IfcOpeningElement) and fills it. A value typed right after placing moves the
last door/window. (0.359) A door: the side it opens to is the wall's face the
mouse is on (F: the other), its hinges its type's jamb (Space: the other, as
Revit's) — its leaf and swing previewed so —, as the owner asked («já na
pré-visualização escolher o lado e a direção e clicar para fixar»)."""

import math
from dataclasses import dataclass

import numpy as np

from ..core.openings import (
    distance_to_end, face_rectangle, fits, nearest_end, s_from_typed, snap_s,
)
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, lang, refusal, t
from ..ifc import catalog
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, Tool

WARN = (0.90, 0.20, 0.15, 1.0)


@dataclass
class _Target:
    wall: str
    frame: object
    side: int
    s: float
    near_start: bool
    centred: bool
    ok: bool
    arc: object = None          # (0.177) a curved wall: (its middle m along it, its length)
    hinge: object = None        # (0.359) a door: its hinges at this end of the opening (along the wall, local x)
    snap: object = ""           # (0.409) what it snapped to: "", "middle" (of the room's side), 0.10 / 0.20 (a jamb
    #                             that far from the wall across)


@dataclass
class _Last:
    cmd: object
    wall: str
    frame: object
    side: int
    near_start: bool
    arc: object = None


def _fmt(value):
    return format_length(value, decimal_sep())


class OpeningTool(Tool):
    kind = ""
    default_key = ""
    accepts_typing = True
    common_keys = frozenset(("f",))
    placement = True
    keys_help = "keys.opening"

    def __init__(self, host):
        super().__init__(host)
        self.spec = catalog.OPENING_BY_KEY[self.default_key]
        self._target = None
        self._last = None
        self._frames = {}       # wall guid -> (id(mesh), WallFrame)
        self.flipped = False    # F (0.86): to the other face of the wall than the one under the mouse
        self.bare = False       # (0.110) only the opening, no frame: the hole of this size left empty
        self.hinge_flip = False  # (0.359) Space: a door's hinges at the other jamb than its type's

    def common_key(self, name):
        if name == "space":                            # (0.359) a door: its hinges to the other jamb
            self.hinge_flip = not self.hinge_flip
            self.host.message(t("info.door_hinge_other" if self.hinge_flip else "info.door_hinge_type"))
            if self._target is not None and self._target.hinge is not None:
                t_ = self._target
                t_.hinge = t_.s + self.spec.width if abs(t_.hinge - t_.s) < 1e-9 else t_.s
                self._feedback()
            return True
        self.flipped = not self.flipped
        self.host.message(t("info.flipped" if self.flipped else "info.unflipped"))
        self.host.set_hint(self.hint())
        if self._target is not None:
            self._target.side = -self._target.side
            self._feedback()
        return True

    def spec_name(self):
        return self.spec.name_pt if lang() == "pt" else self.spec.name_en

    def set_spec(self, spec):
        self.spec = spec
        self.host.set_hint(self.hint())

    def options(self):
        specs = [s for s in catalog.openings() if s.kind == self.kind]
        return [Option("type", t("ctx.type"), "choice", self.spec.key,
                       tuple((s.key, s.name_pt if lang() == "pt" else s.name_en) for s in specs)),
                Option("flip", t("ctx.flip"), "toggle", self.flipped),
                Option("bare", t("ctx.bare_opening"), "toggle", self.bare)]

    def set_option(self, key, value):
        if key == "type" and value in catalog.OPENING_BY_KEY:
            self.set_spec(catalog.OPENING_BY_KEY[value])
        elif key == "flip" and bool(value) != self.flipped:
            self.common_key("f")
        elif key == "bare":
            self.bare = bool(value)
            self.host.set_hint(self.hint())

    def hint(self):
        if self.bare:
            return t("hint.bare_opening", type=self.spec_name())
        return t("hint.opening", type=self.spec_name())

    def vcb_title(self):
        return t("vcb.to_end")

    # ------------------------------------------------------------ mouse

    def pointer_move(self, x, y, modifiers):
        self._target = self._target_at(x, y)
        self._feedback()
        if self._target is None:
            # Explain why nothing happens over a sketch volume (it is not a wall yet).
            hit = self.viewport.pick_point(x, y)
            obj = self.doc.get(hit[0]) if hit else None
            if obj is not None and not obj.is_bim:
                self.viewport.show_label(t("err.classify_first"), hit[2])

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        target = self._target_at(x, y)
        if target is None:
            hit = self.viewport.pick_point(x, y)
            obj = self.doc.get(hit[0]) if hit else None
            self.host.message(t("err.classify_first" if obj is not None and not obj.is_bim else "err.no_wall"),
                              warning=True)
        elif not target.ok:
            self.host.message(t("err.wall_small", type=self.spec_name()), warning=True)
        elif target.arc is not None:                   # (0.177) a curved wall
            self._place_curved(target.wall, target.arc[0], target.side, target.near_start)
        else:
            self._place(target.wall, target.frame, target.s, target.side, target.near_start, target.hinge)

    # ------------------------------------------------------------ keyboard

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        w = self.spec.width
        target = self._target
        if target is not None and target.ok:
            if target.arc is not None:                 # (0.177) along the curved wall from its nearer end
                self._place_curved(target.wall, self._typed_along(target, values[0]), target.side, target.near_start)
                return
            s = s_from_typed(target.frame, values[0], w, target.near_start)
            self._place(target.wall, target.frame, s, target.side, target.near_start)
            return
        last = self._last
        if last is not None and self.doc.last_command() is last.cmd:
            self.doc.undo()   # SketchUp: a value typed right after placing moves it
            if last.arc is not None:
                self._place_curved(last.wall, self._typed_along(last, values[0]), last.side, last.near_start)
                return
            s = s_from_typed(last.frame, values[0], w, last.near_start)
            self._place(last.wall, last.frame, s, last.side, last.near_start)
            return
        self.host.message(t("err.no_wall"), warning=True)

    def _typed_along(self, target, distance):
        """(0.177) The middle of the opening whose near edge is `distance` from the curved wall's nearer end."""
        from ..core.openings import EDGE_CLEARANCE
        w, length = self.spec.width, target.arc[1]
        along = distance + w / 2 if target.near_start else length - distance - w / 2
        return min(max(along, w / 2 + EDGE_CLEARANCE), length - w / 2 - EDGE_CLEARANCE)

    def cancel(self):
        self._target = None
        self.viewport.clear_overlays()
        self.viewport.clear_temp_dims()
        self.host.set_vcb("")

    # ------------------------------------------------------------ internals

    def _frame(self, wall_guid):
        obj = self.doc.get(wall_guid)
        cached = self._frames.get(wall_guid)
        if cached is None or cached[0] != id(obj.mesh):
            cached = (id(obj.mesh), bim.wall_frame(self.doc, wall_guid))
            self._frames[wall_guid] = cached
        return cached[1]

    def _target_at(self, x, y):
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None
        obj = self.doc.get(hit[0])
        if obj is None or not obj.is_bim or obj.ifc_class not in ("IfcWall", "IfcWallStandardCase"):
            return None
        if self.doc.ifc.kind_of(obj.id) == "curved_wall":       # (0.177)
            return self._curved_target(obj.id, hit[2])
        frame = self._frame(obj.id)
        if frame is None:
            return None
        side = frame.face_side(obj.mesh.face_normal(hit[1]))
        if side == 0 and self.viewport.plan:
            # in a plan the wall is seen cut, from above: the face is the one on the cursor's side
            y = frame.to_local(hit[2])[1]
            side = -1 if y < (frame.y0 + frame.y1) / 2 else 1
        if side == 0:
            return None
        if self.flipped:
            side = -side
        w, h, sill = self.spec.width, self.spec.height, self.spec.sill
        ok = fits(frame, w, h, sill)
        # (0.409) snapped to the middle of the room's side, or a jamb 10 / 20 cm from the wall across, on its face
        s, snap = snap_s(frame, hit[2], w, self._faces_across(obj.id, frame, side)) if ok else (frame.x0, "")
        hinge = None
        hand = self._type_hand() if ok else None
        if hand is not None:                           # (0.359) its type's hinges as it goes in on that side; Space: the other
            hinge = s if ((hand == "LEFT") == (side < 0)) != self.hinge_flip else s + w
        return _Target(obj.id, frame, side, s, nearest_end(frame, hit[2]), snap in ("middle", "centre"), ok,
                       hinge=hinge, snap=snap)

    def _snap_tip(self, target):
        """(0.409) What the opening snapped to, said beside it."""
        if target.snap == "middle":
            return t("snap.room_middle")
        if target.snap == "centre":
            return t("snap.wall_center")
        if target.snap:
            return t("snap.from_wall", d=_fmt(target.snap))
        return ""

    def _type_hand(self):
        """(0.359) A door type with one leaf that swings: the jamb of its hinges seen from the side it opens to
        ("LEFT" / "RIGHT"); else None (and for a window)."""
        if self.kind != "door":
            return None
        from ..core import joinery as core_joinery
        try:
            design = catalog.design_of(self.spec)
        except (AttributeError, KeyError, ValueError):
            return None
        width, height = self.spec.width, self.spec.height
        lights, _bars = core_joinery.layout(design, width, height)
        leaves = [lt for lt in lights if lt.row == 0 and core_joinery.door_leaf(lt.cell.operation)]
        if len(leaves) != 1:
            return None
        hand = core_joinery.OPERATIONS[leaves[0].cell.operation].hand
        return hand if hand in ("LEFT", "RIGHT") and core_joinery._family(leaves[0].cell.operation) == "swing" \
            else None

    def _curved_target(self, guid, point):
        """(0.177) The opening in a curved wall under the mouse: its middle at the cursor's angle (to the cm, kept
        clear of the ends), the face by the cursor's side of the axis; in the frame tangent there."""
        from ..core import arcs
        centre, radius, start, sweep, height, thickness = self.doc.ifc.curved_wall_params(guid)
        w, h, sill = self.spec.width, self.spec.height, self.spec.sill
        angle = math.atan2(point[1] - centre[1], point[0] - centre[0])
        along = arcs.opening_along(start, sweep, radius, w, angle)
        ok = along is not None and arcs.opening_depth(radius, thickness, w) is not None and sill + h <= height
        length = radius * abs(sweep)
        along = length / 2 if along is None else along
        frame = self.doc.ifc.curved_frame(guid, along, w)
        side = 1 if math.hypot(point[0] - centre[0], point[1] - centre[1]) < radius else -1
        if self.flipped:
            side = -side
        near = arcs.is_full(sweep) or along <= length / 2
        return _Target(guid, frame, side, -w / 2, near, False, ok, arc=(along, length))

    def _plan_feedback(self, target):
        """(0.404) In a plan, as Revit's: the opening drawn through the wall where it will go — a door its leaf open and
        its swing, a window its frame and glass —, and temporary dimensions from its jambs to the nearest walls (or the
        wall's ends) on each side, instead of a line along the face (the owner: «essa linha azul me confundiu… no 2D
        ficaria melhor uma cota melhor representada»)."""
        from ..core import temp_dims
        spec, frame = self.spec, target.frame
        width = spec.width if target.ok else min(spec.width, frame.length)
        floor = frame.z0 + 0.01
        y0, y1 = frame.y0, frame.y1
        s0, s1 = target.s, target.s + width
        world = lambda x, y: np.asarray(frame.to_world((x, y, floor)), dtype=float)       # noqa: E731
        corners = [world(x, y) for x, y in ((s0, y0), (s1, y0), (s1, y1), (s0, y1))]
        segs = []
        for i in range(4):
            segs += [corners[i], corners[(i + 1) % 4]]
        color = PREVIEW if target.ok else WARN
        if self.kind == "window":                       # (its frame's middle and its glass, as on the plan)
            mid = (y0 + y1) / 2
            for y in (mid - 0.02, mid + 0.02):
                segs += [world(s0, y), world(s1, y)]
        if target.hinge is not None and target.ok:      # (a door: the leaf open and its swing, to the mouse's side)
            y = y0 if target.side < 0 else y1
            other = s1 if abs(target.hinge - s0) < 1e-9 else s0
            out = 1.0 if target.side > 0 else -1.0
            arc = [world(target.hinge + (other - target.hinge) * math.cos(k * math.pi / 24),
                         y + out * width * math.sin(k * math.pi / 24)) for k in range(13)]
            segs += [p for pair in zip(arc, arc[1:]) for p in pair]
            segs += [world(target.hinge, y), arc[-1]]
        self.viewport.show_polygon(corners, segments=segs, colors=[color] * len(segs))
        if not target.ok:
            self.viewport.clear_temp_dims()
            self.viewport.show_label(t("err.wall_small", type=self.spec_name()), corners[2])
            return
        self.viewport.show_label("", None)
        left, right = self._neighbours(target, width)
        y = y0 if target.side < 0 else y1
        out = world(0.0, y + (1.0 if target.side > 0 else -1.0)) - world(0.0, y)
        normal = np.array((0.0, 0.0, 1.0))
        dims = []
        for a_x, b_x in ((left, s0), (s1, right)):
            if b_x - a_x < 1e-3:
                continue
            a, b = world(a_x, y), world(b_x, y)
            d = b - a
            lft = np.cross(normal, d / max(float(np.linalg.norm(d)), 1e-12))
            dims.append(temp_dims.TempDim(a, b, normal, side=1.0 if float(lft @ out) > 0 else -1.0))
        self.viewport.show_temp_dims(dims)
        self.viewport.show_tip(self._snap_tip(target), corners[2])
        self.host.set_vcb(_fmt(distance_to_end(frame, target.s, width, target.near_start)))

    def _neighbours(self, target, width):
        """(0.404) Along the wall, on the face the opening is seen from, how far the nearest wall across it (its face)
        or else the wall's end is on each side of the opening: (x of the left one, x of the right one), local x."""
        frame = target.frame
        xs = self._faces_across(target.wall, frame, target.side)
        s0, s1 = target.s, target.s + width
        left = max([x for x in xs if x <= s0 + 1e-6], default=frame.x0)
        right = min([x for x in xs if x >= s1 - 1e-6], default=frame.x0 + frame.length)
        return left, right

    def _faces_across(self, wall, frame, side):
        """The faces of the walls that cross the wall or reach its face `side` (just off it, on that side): their local
        x along it — kept while the mouse stays on that face and the model does not change (0.409: asked at each
        move, for the snaps)."""
        from ..model import dim_refs
        obj = self.doc.get(wall)
        key = (self.doc.revision, obj.storey if obj is not None else None)
        if getattr(self, "_walls_key", None) != key:
            try:
                self._walls = dim_refs.walls_of(self.doc, key[1])
            except Exception:
                self._walls = {}
            self._walls_key = key
            self._faces = {}
        faces_key = (wall, side, id(frame))
        if faces_key in self._faces:
            return self._faces[faces_key]
        y = frame.y0 if side < 0 else frame.y1
        y += (0.03 if side > 0 else -0.03)              # (just off the face, on its side: the walls that reach it)
        z = frame.z0
        start = np.asarray(frame.to_world((frame.x0, y, z)), dtype=float)
        ahead = np.asarray(frame.to_world((frame.x0 + 1.0, y, z)), dtype=float) - start
        try:
            found = dim_refs.crossings(self._walls, start, ahead, frame.length, "faces", skip={wall})
        except Exception:                               # (the IFC still being read…)
            found = []
        xs = sorted(frame.x0 + float(c[0]) for c in found)
        self._faces[faces_key] = xs
        return xs

    def _feedback(self):
        target = self._target
        if target is None:
            self.viewport.clear_overlays()
            self.viewport.clear_temp_dims()
            self.host.set_vcb("")
            return
        if self.viewport.plan and target.arc is None:  # (0.404) in a plan: the opening and Revit's dimensions
            self._plan_feedback(target)
            return
        spec, frame = self.spec, target.frame
        width = spec.width if target.ok else min(spec.width, frame.length)
        rect = face_rectangle(frame, target.s, width, spec.sill, spec.height, target.side)
        color = PREVIEW if target.ok else WARN
        segs = []
        for i in range(4):
            segs += [rect[i], rect[(i + 1) % 4]]
        if target.arc is not None:                     # (0.177) a curved wall: the distance along it to its end
            along, length = target.arc
            dist = (along - width / 2) if target.near_start else (length - along - width / 2)
            self.viewport.show_polygon(rect, segments=segs, colors=[color] * len(segs))
            if not target.ok:
                self.viewport.show_label(t("err.wall_small", type=self.spec_name()), rect[3])
                return
            self.viewport.show_label(_fmt(dist), rect[0])
            self.host.set_vcb(_fmt(dist))
            return
        # temporary dimension: from the nearest wall end to the opening's near edge
        y = frame.y0 if target.side < 0 else frame.y1
        z = frame.z0 + spec.sill + spec.height / 2
        end_x = frame.x0 if target.near_start else frame.x0 + frame.length
        edge_x = target.s if target.near_start else target.s + width
        a, b = frame.to_world((end_x, y, z)), frame.to_world((edge_x, y, z))
        segs += [a, b]
        if target.hinge is not None and target.ok:      # (0.359) where it will swing: the leaf open and its arc
            other =target.s + width if abs(target.hinge - target.s) < 1e-9 else target.s
            out = 1.0 if target.side > 0 else -1.0
            floor = frame.z0 + 0.01
            arc = [frame.to_world((target.hinge + (other - target.hinge) * math.cos(k * math.pi / 24),
                                   y + out * width * math.sin(k * math.pi / 24), floor)) for k in range(13)]
            segs += [p for pair in zip(arc, arc[1:]) for p in pair]
            segs += [frame.to_world((target.hinge, y, floor)), arc[-1]]
        self.viewport.show_polygon(rect, segments=segs, colors=[color] * len(segs))
        if not target.ok:
            self.viewport.show_label(t("err.wall_small", type=self.spec_name()), rect[3])
            self.viewport.show_tip("", None)
            return
        dist = distance_to_end(frame, target.s, width, target.near_start)
        self.viewport.show_label(_fmt(dist), (a + b) / 2)
        self.viewport.show_tip(self._snap_tip(target), rect[3])
        self.host.set_vcb(_fmt(dist))

    def _place(self, wall_guid, frame, s, side, near_start, hinge=None):
        if self.bare:                                  # (0.110) the hole only
            bim.add_bare_opening(self.doc, wall_guid, self.spec, frame, s)
        else:
            hinge_at = frame.to_world((hinge, (frame.y0 + frame.y1) / 2, frame.z0)) if hinge is not None else None
            # (0.404) a door is set from the wall's other face: it swings away from the face it is set on — to the
            # side the mouse was, as previewed (the owner: «a prévia mostra a porta para dentro, mas quando clico
            # para fixar, ela fica com abertura para fora»)
            bim.add_opening(self.doc, wall_guid, self.spec, frame, s, -side if self.kind == "door" else side,
                            hinge_at=hinge_at)
        cmd = self.doc.last_command()
        self._last = _Last(cmd, wall_guid, frame, side, near_start)
        self._target = None
        self.viewport.clear_overlays()
        self.viewport.clear_temp_dims()
        wall = self.doc.get(wall_guid)
        key = "info.placed_bare" if self.bare else "info.placed"
        self.host.message(t(key, type=self.spec_name(), wall=wall.name if wall else ""))
        self.host.set_vcb(_fmt(distance_to_end(frame, s, self.spec.width, near_start)))

    def _place_curved(self, wall_guid, along, side, near_start):
        """(0.177) The door / window (or its hole) in a curved wall, its middle `along` m from its start."""
        try:
            bim.add_curved_opening(self.doc, wall_guid, self.spec, along, side, bare=self.bare)
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return
        _c, radius, _start, sweep, _h, _t = self.doc.ifc.curved_wall_params(wall_guid)
        length = radius * abs(sweep)
        self._last = _Last(self.doc.last_command(), wall_guid, None, side, near_start, arc=(along, length))
        self._target = None
        self.viewport.clear_overlays()
        wall = self.doc.get(wall_guid)
        w = self.spec.width
        self.host.message(t("info.placed_bare" if self.bare else "info.placed", type=self.spec_name(),
                            wall=wall.name if wall else ""))
        self.host.set_vcb(_fmt((along - w / 2) if near_start else (length - along - w / 2)))


class DoorTool(OpeningTool):
    name = "door"
    kind = "door"
    default_key = "porta_80"
    common_keys = frozenset(("f", "space"))         # (0.359: Space, its hinges to the other jamb)
    keys_help = "keys.door"


class WindowTool(OpeningTool):
    name = "window"
    kind = "window"
    default_key = "janela_120"
