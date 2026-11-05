"""(0.410) An outline with holes edited by its grips — one way for the wall's profile (its elevation, 0.109, 0.375–0.381)
and for the outline of a slab, a floor finish or a ceiling (their plan, 0.100, 0.382). The owner: «assim como
editamos o perfil da parede com Shift, Alt, quero que faça também o mesmo com o piso. E vamos adicionar tanto na
parede como no piso a possibilidade de desenhar (em edição) polígonos no meio para fazer buracos personalizados».

The outline and its holes are loops (core/outline_loops), each with the same grips: squares on the corners; diamonds
in the straight sides' middles, on the arcs' points and on the Bézier curves' tangents. No modes (0.380):

- a square dragged moves its corner (the tangents of the curves meeting there go along);
- a straight side's diamond dragged makes a new corner there — with Shift held, the side an arc through the mouse;
  with Alt, a curve (Shift and Alt can be pressed or let go while it moves: the drawing follows at once);
- an arc's or a curve's diamond dragged changes that curve;
- Alt and a click on a corner between two straight sides: a fillet, its radius the mouse's distance (or typed);
- a grip moves only while the button is held (0.381): a click chooses it, for Delete — a corner taken away, a curve
  straightened;
- inside a hole: dragged, the hole moves; clicked, it is chosen — Delete takes it away (so does Delete on a corner
  of a hole of three).

Holes are drawn with «Furo» on the contextual bar — polygon (its corners clicked; a click on the first one, or
Enter, closes it), rectangle (two corners, clicked or dragged, or its size typed «1,2;0,8») or circle (its centre,
then its edge, or the radius typed). Their mode stays on to draw the next; Esc, the lit button again or the right
button lets it go. A hole must lie inside the outline, touching neither it nor another hole.

The tool using this mixin gives: _load() (fills self._loops and calls _show), _world(pts) (2D -> 3D), _local_at(x, y,
origin) (the point under the mouse, snapped; origin: where it is dragged from), _raw_local(x, y) (unsnapped) and
_save(loops, text) (one undo step)."""

import math

import numpy as np

from ..core import curves as core_curves
from ..core import outline_loops
from ..core.units import format_length, parse_length, parse_lengths
from ..i18n import decimal_sep, t
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option, moved_enough

HOLE_SHAPES = ("poly", "rect", "circle")
CLOSE_PX = 12                       # px: a polygon's hole closes on a click this near its first corner
CHOSEN = (0.95, 0.45, 0.10, 1.0)    # a hole clicked (chosen, for Delete)
DRAFT = (0.85, 0.15, 0.55, 1.0)     # a hole being drawn


def _fmt(v):
    return format_length(v, decimal_sep())


def side_kind(modifiers):
    """(0.380) What a straight side pulled by its middle becomes, by the keys held: Shift an arc, Alt a curve, else
    a new corner."""
    mods = modifiers or ()
    return "arc" if "Shift" in mods else "bezier" if "Alt" in mods else "corner"


class OutlineGrips:
    """The gestures (see the module's docstring), over a Tool."""

    typing_always = False           # (a slab's corner: its distance typed while it is dragged)
    three_corners = "err.slab_three_corners"

    def __init__(self, host):
        super().__init__(host)
        self._loops = []            # [[corners, sides]…]: the outline, then its holes
        # ("corner" | "side" | "through" | "h1" | "h2" | "fillet", loop, k) | ("hole", loop, where it was taken)
        self._picked = None
        self._end = None
        self._press = None          # where the button went down (let go elsewhere: a drag)
        self._chosen = None         # a grip / a hole clicked (not dragged): what Delete acts on
        self._mods = ()             # Shift / Alt held, as last seen
        self._radius = None         # a fillet's radius, as last shown
        self._ends = []             # (loop, corner) of each square
        self._mids = []             # (loop, side, "mid" | "through" | "h1" | "h2") of each diamond
        self.hole_shape = ""        # a hole being drawn: "poly" | "rect" | "circle" ("" none)
        self._draft = []            # its points so far
        self._draft_end = None      # the point under the mouse

    # ------------------------------------------------------------ what it is

    @property
    def _pts(self):
        """The outline's corners (the first loop)."""
        return self._loops[0][0] if self._loops else []

    @property
    def _sides(self):
        return self._loops[0][1] if self._loops else []

    @property
    def accepts_typing(self):
        """A fillet's radius, a hole's size (rectangle) or radius (circle) — typed, Enter."""
        if self.typing_always:
            return True
        if self._picked is not None and self._picked[0] == "fillet":
            return True
        return self.hole_shape in ("rect", "circle") and bool(self._draft)

    def vcb_title(self):
        if self._picked is not None and self._picked[0] == "fillet":
            return t("vcb.radius")
        if self._draft and self.hole_shape == "circle":
            return t("vcb.radius")
        if self._draft and self.hole_shape == "rect":
            return t("vcb.hole_size")
        return t("vcb.length") if self.typing_always else None

    def hole_option(self):
        return Option("hole", t("ctx.hole"), "buttons", self.hole_shape,
                      tuple((s, t("holeshape." + s)) for s in HOLE_SHAPES))

    def set_hole_shape(self, shape):
        """A hole's shape to draw ("" none): the mode on (or off), the bar and the hint following."""
        shape = shape if shape in HOLE_SHAPES else ""
        self._pick(None)
        self._chosen = None
        self.hole_shape = shape
        self._draft, self._draft_end = [], None
        self.viewport.show_tip("", None)
        if self._loops:
            self._show()
        if shape:
            self.host.message(t("info.hole_mode." + shape))
        if hasattr(self.host, "_sync_context_bar"):
            self.host._sync_context_bar()
        if hasattr(self.host, "vcb_title_changed"):
            self.host.vcb_title_changed()

    def _pick(self, picked):
        """What is picked up now (None: nothing) — the Measurements box asks for a radius while it is a fillet."""
        title = self.vcb_title()
        self._picked, self._end, self._radius, self._chosen = picked, None, None, None
        if title != self.vcb_title() and hasattr(self.host, "vcb_title_changed"):
            self.host.vcb_title_changed()

    def _drop_all(self):
        self._pick(None)
        self._press = None
        self._draft, self._draft_end = [], None

    # ------------------------------------------------------------ drawn

    def _show(self, loops=None):
        """The outline and its holes — their curved sides in pieces — with their grips; the hole chosen in orange;
        the hole being drawn, from its points to the mouse. Only lines (0.379: a translucent fill of the new shape
        over the element hid what is to be cut)."""
        loops = self._loops if loops is None else loops
        ends, middles, arrows, segs, colors = [], [], [], [], []
        self._ends, self._mids = [], []
        chosen = self._chosen[1] if self._chosen is not None and self._chosen[0] == "hole" else None
        for n, (pts, sides) in enumerate(loops):
            count = len(pts)
            ends += self._world(pts)
            self._ends += [(n, k) for k in range(count)]
            for i, side in enumerate(sides):
                a, b = pts[i], pts[(i + 1) % count]
                if not side:
                    middles.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
                    self._mids.append((n, i, "mid"))
                elif side["kind"] == "arc":
                    middles.append(side["through"])
                    self._mids.append((n, i, "through"))
                else:
                    for name, corner in (("h1", a), ("h2", b)):
                        middles.append(side[name])
                        self._mids.append((n, i, name))
                        arrows += self._world([corner, side[name]])
            ring = self._world(core_curves.profile_outline(pts, sides))
            colour = CHOSEN if n == chosen else PREVIEW
            for a, b in zip(ring, ring[1:] + ring[:1]):
                segs += [a, b]
                colors += [colour, colour]
        draft = self._draft_ring()
        if draft:
            pts = self._world(draft)
            pairs = list(zip(pts, pts[1:] + pts[:1])) if self.hole_shape != "poly" else list(zip(pts, pts[1:]))
            for a, b in pairs:
                segs += [a, b]
                colors += [DRAFT, DRAFT]
        self.viewport.show_grips(ends, self._world(middles), (), arrows)
        self.viewport.show_lines(segs, colors)
        self.host.set_hint(self.hint())

    def _draft_ring(self):
        """The hole being drawn, as it would be made with the mouse where it is: its points (a polygon's, open, to the
        mouse), a rectangle's corners, a circle's points."""
        if not self._draft:
            return []
        end = self._draft_end
        if self.hole_shape == "poly":
            return list(self._draft) + ([end] if end is not None else [])
        if end is None:
            return []
        loop = outline_loops.rectangle(self._draft[0], end) if self.hole_shape == "rect" else \
            outline_loops.circle(self._draft[0], math.hypot(end[0] - self._draft[0][0], end[1] - self._draft[0][1]))
        return core_curves.profile_outline(*loop) if loop else []

    def hint(self):
        if not self._loops:
            return self.none_hint()
        if self.hole_shape:
            return t("hint.hole." + self.hole_shape + ("_next" if self._draft else ""))
        if self._picked is None:
            return self.idle_hint()
        what = self._picked[0]
        return t({"corner": "hint.wall_profile_move", "side": "hint.wall_profile_side", "hole": "hint.hole_move",
                  "fillet": "hint.wall_profile_fillet"}.get(what, "hint.wall_profile_curve"))

    def none_hint(self):
        return t("hint.wall_profile_none")

    def idle_hint(self):
        return t("hint.wall_profile")

    # ------------------------------------------------------------ the change

    def _moved(self, q):
        """The loops with what is picked up taken to q: a corner takes its tangents along; a straight side pulled
        by its middle — by the keys held — a new corner, an arc or a curve through q; a fillet of the radius the
        distance from its corner to q (or the one typed); a hole moved by how far q is from where it was taken."""
        loops = outline_loops.copy(self._loops)
        what, n, k = self._picked
        if what == "hole":
            loops[n] = outline_loops.moved(loops[n], (q[0] - k[0], q[1] - k[1]))
            return loops
        pts, sides = loops[n]
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
                loops[n][0], loops[n][1], self._radius = done
        else:
            sides[k][what] = q
        return loops

    def _origin(self):
        """Where the grip picked up is dragged from (a corner: itself — distances, axes from there)."""
        if self._picked is None:
            return None
        what, n, k = self._picked
        if what == "corner":
            return self._loops[n][0][k]
        if what == "hole":
            return k
        return None

    def _tip(self, q):
        """What is said beside the grip picked up: the radius of a fillet; what a pulled side becomes; where."""
        where = "{} ; {}".format(_fmt(q[0]), _fmt(q[1]))
        what, n, k = self._picked
        if what == "fillet":
            return t("tip.profile_fillet", r=_fmt(self._radius or 0.0)), self._world([self._loops[n][0][k]])[0]
        if what == "side":
            return t("tip.profile_side_drop", m=t("profkind." + side_kind(self._mods)), p=where), self._world([q])[0]
        if what == "hole":
            d = math.hypot(q[0] - k[0], q[1] - k[1])
            return t("tip.hole_drop", d=_fmt(d)), self._world([q])[0]
        return t("tip.profile_drop", p=where), self._world([q])[0]

    def _preview(self, q):
        self._end = q
        self._show(self._moved(q))
        self.viewport.show_tip(*self._tip(q))
        self._preview_extra(q)

    def _preview_extra(self, q):
        """A tool's own marks while a grip moves (a slab's: the distance from where the corner was)."""

    def _apply(self, loops, text=None):
        self._pick(None)
        self._chosen = None
        if outline_loops.polygon(loops) is None:
            self.host.message(t(self.bad_outline), warning=True)
            self._load()
            return False
        return self._save(loops, text)

    bad_outline = "err.profile_bad"

    def _apply_moved(self):
        what = self._picked[0]
        text = {"hole": "info.hole_moved"}.get(what)
        self._apply(self._moved(self._end), t(text) if text else None)

    # ------------------------------------------------------------ the mouse

    def modifiers_changed(self, modifiers):
        """(0.380) Shift / Alt pressed or let go: a side pulled shows at once what it becomes."""
        self._mods = tuple(modifiers or ())
        if self._picked is not None and self._picked[0] == "side" and self._end is not None:
            self._preview(self._end)

    def _hole_at(self, x, y):
        """The hole under the mouse (its loop's index), or None."""
        if len(self._loops) < 2:
            return None
        q = self._raw_local(x, y)
        if q is None:
            return None
        for n in range(len(self._loops) - 1, 0, -1):
            if outline_loops.contains(self._loops[n], q):
                return n
        return None

    def _hover_grips(self, x, y):
        grip = self.viewport.grip_at(x, y)
        if grip is None:
            n = self._hole_at(x, y)
            q = self._raw_local(x, y) if n is not None else None
            self.viewport.show_tip(t("tip.hole") if q is not None else "",
                                   self._world([q])[0] if q is not None else None)
            return
        kind, k = grip
        at = self.viewport.grips[0][k] if kind == "end" else self.viewport.grips[1][k]
        tip = "tip.profile_corner" if kind == "end" else (
            "tip.profile_side" if self._mids[k][2] == "mid" else "tip.profile_curve")
        self.viewport.show_tip(t(tip), at)

    def pointer_move(self, x, y, modifiers):
        if not self._loops:
            return
        self._mods = tuple(modifiers or ())
        if self.hole_shape:
            q = self._local_at(x, y, self._draft[-1] if self._draft else None)
            if q is None:
                return
            self._draft_end = q
            self._show()
            self._draft_tip(x, y, q)
            return
        if self._picked is None:
            self._hover_grips(x, y)
            return
        q = self._local_at(x, y, self._origin())
        if q is not None:
            self._preview(q)

    def _draft_tip(self, x, y, q):
        if self.hole_shape == "poly":
            closing = len(self._draft) >= 3 and self._near_first(x, y)
            self.viewport.show_tip(t("tip.hole_close") if closing else "", self._world([self._draft[0] if closing
                                                                                          else q])[0])
            return
        if not self._draft:
            self.viewport.show_tip("", None)
            return
        a = self._draft[0]
        if self.hole_shape == "rect":
            text = "{} × {}".format(_fmt(abs(q[0] - a[0])), _fmt(abs(q[1] - a[1])))
        else:
            text = t("tip.hole_radius", r=_fmt(math.hypot(q[0] - a[0], q[1] - a[1])))
        self.viewport.show_tip(text, self._world([q])[0])

    def _near_first(self, x, y):
        if not self._draft:
            return False
        sx, sy = self.viewport.project(self._world([self._draft[0]])[0])[:2]
        return math.hypot(sx - x, sy - y) <= CLOSE_PX

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._draft:                          # (the hole being drawn given up)
                self._draft, self._draft_end = [], None
                self._show()
            elif self._picked is not None:
                self.cancel()
            elif self.hole_shape:
                self.set_hole_shape("")
            else:
                self.host.set_tool("select")
            return
        if button != LEFT or not self._loops:
            return
        self._mods = tuple(modifiers or ())
        if self.hole_shape:
            self._press = (float(x), float(y))
            q = self._local_at(x, y, self._draft[-1] if self._draft else None)
            if q is not None:
                self._draft_click(q, x, y)
            return
        if self._picked is not None:                 # (0.381: only a fillet waits for this second click)
            if self._end is not None:
                self._apply_moved()
            return
        grip = self.viewport.grip_at(x, y)
        if grip is None:
            n = self._hole_at(x, y)
            q = self._local_at(x, y) if n is not None else None
            self._chosen = None
            if q is not None:                        # (a hole: dragged it moves, clicked it is chosen)
                self._press = (float(x), float(y))
                self._pick(("hole", n, q))
            self._show()
            return
        self._press = (float(x), float(y))           # (0.378: let go elsewhere — a drag — it is put down there)
        kind, k = grip
        if kind == "end":
            n, c = self._ends[k]
            if "Alt" in self._mods:                  # (0.380) Alt and a click on a corner: a fillet
                if core_curves.fillet(self._loops[n][0], self._loops[n][1], c, 0.01) is None:
                    self.host.message(t("err.profile_fillet"), warning=True)
                    return
                self._pick(("fillet", n, c))
                self.host.set_hint(self.hint())
                return
            self._pick(("corner", n, c))
            self._show()
            return
        n, side, what = self._mids[k]
        self._pick(("side", n, side) if what == "mid" else (what, n, side))
        self._show()

    def pointer_up(self, x, y, button, modifiers):
        """(0.378) A grip pressed, dragged and let go: put down there. (0.381) Pressed and let go in place — a click —:
        nothing moves; the grip (or the hole) is chosen, for Delete. Only a fillet (Alt and a click on a corner) stays,
        its radius following the mouse until a second click or Enter. (0.410) A rectangle's or a circle's hole
        dragged from its first point: made where let go."""
        press, self._press = self._press, None
        if button != LEFT or press is None:
            return
        self._mods = tuple(modifiers or ())
        if self.hole_shape:
            if self.hole_shape in ("rect", "circle") and len(self._draft) == 1 and moved_enough(press, (x, y)) \
                    and self._draft_end is not None:
                self._finish_hole(self._draft_end)
            return
        if self._picked is None:
            return
        if moved_enough(press, (x, y)):
            if self._end is not None:
                self._apply_moved()
            elif self._picked[0] != "fillet":
                self.cancel()
            return
        if self._picked[0] == "fillet":
            return
        what, n, k = self._picked
        self._pick(None)
        self._chosen = None if what == "side" else (what, n, None if what == "hole" else k)
        self._show()
        if what == "hole":
            centre = outline_loops.polygon([self._loops[n]])
            at = (centre.centroid.x, centre.centroid.y) if centre is not None else self._loops[n][0][0]
            self.viewport.show_tip(t("tip.hole_chosen"), self._world([at])[0])
        elif what != "side":
            at = self._loops[n][0][k] if what == "corner" else self._loops[n][1][k][what]
            self.viewport.show_tip(t("tip.profile_chosen_corner" if what == "corner" else "tip.profile_chosen_curve"),
                                   self._world([at])[0])

    # ------------------------------------------------------------ holes drawn

    def _draft_click(self, q, x, y):
        if self.hole_shape == "poly":
            if len(self._draft) >= 3 and self._near_first(x, y):
                self._finish_hole(None)
                return
            self._draft.append(q)
            self._draft_end = q
            self._show()
            self._typing_changed()
            return
        if not self._draft:
            self._draft, self._draft_end = [q], q
            self._show()
            self._typing_changed()
            return
        self._finish_hole(q)

    def _typing_changed(self):
        if hasattr(self.host, "vcb_title_changed"):
            self.host.vcb_title_changed()

    def _finish_hole(self, q, size=None):
        """The hole drawn made — a polygon's corners; a rectangle's to q (or `size` (w, h) towards the mouse); a
        circle's to q (or `size` its radius) — if it lies inside the outline, apart from the other holes."""
        shape, draft = self.hole_shape, list(self._draft)
        end = self._draft_end
        self._draft, self._draft_end = [], None
        self._typing_changed()
        if shape == "poly":
            loop = outline_loops.polygon_loop(draft)
        elif shape == "rect":
            if size is not None:
                su = 1.0 if end is None or end[0] >= draft[0][0] else -1.0
                sv = 1.0 if end is None or end[1] >= draft[0][1] else -1.0
                q = (draft[0][0] + su * size[0], draft[0][1] + sv * size[1])
            loop = outline_loops.rectangle(draft[0], q)
        else:
            radius = size if size is not None else math.hypot(q[0] - draft[0][0], q[1] - draft[0][1])
            loop = outline_loops.circle(draft[0], radius)
        if loop is None:
            self.host.message(t("err.hole_small"), warning=True)
            self._show()
            return
        loops = outline_loops.copy(self._loops) + [loop]
        if outline_loops.polygon(loops) is None:
            self.host.message(t("err.hole_outside"), warning=True)
            self._show()
            return
        self._apply(loops, t("info.hole_added", a=_area(outline_loops.area([loop]))))

    def enter(self):
        """Enter: a polygon's hole closed (three corners at least)."""
        if self.hole_shape == "poly" and len(self._draft) >= 3:
            self._finish_hole(None)

    def escape(self):
        """(0.410) Esc: a hole being drawn given up; then its mode let go — only then does Esc leave the editor."""
        if self._draft:
            self._draft, self._draft_end = [], None
            self._typing_changed()
            self._show()
            return True
        if self.hole_shape:
            self.set_hole_shape("")
            return True
        return False

    # ------------------------------------------------------------ typed, deleted

    def typed(self, text):
        """A fillet's radius; a hole's size («1,2;0,8») or radius — typed, Enter."""
        if self._picked is not None and self._picked[0] == "fillet":
            radius = parse_length(text)
            if radius is None or radius <= 0:
                self.host.message(t("err.bad_value", t=text), warning=True)
                return
            self._radius = radius
            self._apply(self._moved(None))
            return
        if self.hole_shape == "rect" and self._draft:
            values = parse_lengths(text, 2)
            if values is None or values[0] is None or values[0] <= 0:
                self.host.message(t("err.bad_value", t=text), warning=True)
                return
            w = values[0]
            h = values[1] if len(values) > 1 and values[1] is not None else w
            self._finish_hole(None, (w, h))
            return
        if self.hole_shape == "circle" and self._draft:
            radius = parse_length(text)
            if radius is None or radius <= 0:
                self.host.message(t("err.bad_value", t=text), warning=True)
                return
            self._finish_hole(None, radius)
            return
        self._typed_other(text)

    def _typed_other(self, text):
        """What else a tool takes typed (a slab's corner: its distance)."""

    def delete(self):
        if self._draft:                              # (a polygon's last corner taken back)
            self._draft.pop()
            self._typing_changed()
            self._show()
            return
        target = self._picked or self._chosen
        if target is None or (target[0] == "side" and self._picked is None):
            self.host.message(t("info.outline_pick_first"), warning=True)
            return
        what, n, k = target
        loops = outline_loops.copy(self._loops)
        if what == "hole":
            del loops[n]
            self._apply(loops, t("info.hole_deleted"))
            return
        if what in ("fillet", "side"):               # (nothing made yet: given up)
            self.cancel()
            return
        pts, sides = loops[n]
        if what != "corner":                         # (a curve's grip: the side straight again)
            sides[k] = None
            self._apply(loops)
            return
        if len(pts) <= 3:
            if n > 0:                                # (a hole of three corners: the hole goes)
                del loops[n]
                self._apply(loops, t("info.hole_deleted"))
                return
            self.host.message(t(self.three_corners), warning=True)
            return
        sides[(k - 1) % len(sides)] = None           # (the two sides meeting there are one straight side now)
        del sides[k]
        del pts[k]
        self._apply(loops)

    def cancel(self):
        """What is picked up goes back; a hole being drawn is given up (Ctrl+Z also passes here)."""
        self._pick(None)
        self._draft, self._draft_end = [], None
        self.viewport.clear_overlays()
        self._load()


def _area(a):
    return "{:.2f} m²".format(a).replace(".", decimal_sep())
