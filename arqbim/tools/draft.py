"""2D drawing in the views (0.120, Phase 5 step 1): in a plan, a section or an elevation, a line, a polyline, a
rectangle, a circle, an arc, a region with a hatch or a text — drawn on the view's paper (the inferences work:
a wall's corner, the end of a line drawn before…) and kept with that view only, as its dimensions are. Tab
changes what is drawn.

  line       two clicks (or the length typed after the first)
  polyline   clicks; Enter ends it (a click on its first point closes it)
  rectangle  two opposite corners (or "a;b" typed after the first)
  circle     its centre, then a point on it (or the radius typed)
  arc        its start, its end, then a point it passes through
  region     its corners; Enter or a click on the first one closes it — hatched on paper
  text       a click where it starts, then the words typed and Enter
  spot       a click: the height there, always the model's (0.156)"""

import numpy as np

from ..core.sketch_geometry import ray_plane
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, t
from ..model import annotations as notes2d
from ..model import graphic_styles as styles_model
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, SNAPPABLE, Option, show_snap
from .bim_draw import _PointTool

CLOSE_PX = 10                    # pixels: a click this near the first point closes a polyline / region
TEXT_SIZES = (1.8, 2.5, 3.5, 5.0)   # mm on paper
NEEDED = {"line": 2, "rectangle": 2, "circle": 2, "arc": 3, "text": 1, "spot": 1, "level": 1,   # points that end it
          "keynote": 2}


def _fmt(v):
    return format_length(v, decimal_sep())


class DraftTool(_PointTool):
    name = "draft"
    keys_help = "keys.draft"

    def __init__(self, host):
        super().__init__(host)
        self.shape = "line"
        self.hatch = "diagonal"
        self.size = notes2d.TEXT_SIZE
        self.line = "continuous"     # (0.126) its line type
        self.width = 0.0             # …and its pen (mm; 0: the project's pen for what is drawn)
        self._points = []            # clicked so far
        self._end = None             # the point under the mouse

    @property
    def accepts_typing(self):
        """A text's words; a line's length, a circle's radius, a rectangle's sides."""
        if self.shape == "text":
            return len(self._points) == 1
        return self.shape in ("line", "circle", "rectangle") and len(self._points) == 1

    @property
    def accepts_text(self):
        """Letters, capitals and spaces too (the window types them in the Measurements box): a text's words."""
        return self.shape == "text" and len(self._points) == 1

    def options(self):
        # (0.450) as icons on the bar, as Revit's «Draw» panel — a mask beside the region (a region filled white)
        shapes = [k for k in notes2d.KINDS]
        shapes.insert(shapes.index("region") + 1, "mask")
        shown = "mask" if self.shape == "region" and self.hatch == "mask" else self.shape
        opts = [Option("shape", t("ctx.draft_shape"), "choice", shown, tuple((k, t("draft." + k)) for k in shapes))]
        if self.shape == "region" and self.hatch != "mask":
            opts.append(Option("hatch", t("ctx.draft_hatch"), "choice", self.hatch,
                               tuple((h, t("drafthatch." + h)) for h in notes2d.HATCHES)))
        if self.shape == "text":
            opts.append(Option("size", t("ctx.text_size"), "choice", self.size,
                               tuple((s, "{} mm".format(str(s).replace(".", decimal_sep()))) for s in TEXT_SIZES)))
        else:
            opts.append(Option("line", t("ctx.line_type"), "choice", self.line,
                               tuple((k, t("linetype." + k)) for k in styles_model.LINE_TYPES)))
            opts.append(Option("width", t("ctx.line_width"), "choice", self.width,
                               ((0.0, t("linewidth.project")),) + tuple(
                                   (w, "{:.2f} mm".format(w).replace(".", decimal_sep()))
                                   for w in styles_model.LINE_WIDTHS)))
        return opts

    def set_option(self, key, value):
        if key == "shape" and value == "mask":           # (0.450) a masking region: a region filled white
            self.set_shape("region")
            self.hatch = "mask"
            return
        if key == "shape" and value in notes2d.KINDS:
            if value == "region" and self.hatch == "mask":
                self.hatch = "diagonal"
            self.set_shape(value)
            return
        if key == "hatch" and value in notes2d.HATCHES:
            self.hatch = value
        elif key == "size":
            self.size = float(value)
        elif key == "line" and value in styles_model.LINE_TYPES:
            self.line = value
        elif key == "width":
            self.width = float(value)
        self.host.set_hint(self.hint())

    def set_shape(self, shape):
        self.cancel()
        self.shape = shape
        self.host.set_hint(self.hint())             # (and the contextual bar shows its options)

    def tab(self):
        kinds = notes2d.KINDS
        self.set_shape(kinds[(kinds.index(self.shape) + 1) % len(kinds)])
        self.host.message(t("info.draft_shape", k=t("draft." + self.shape)))
        return True

    def hint(self):
        if self.viewport.current_view() is None:
            return t("hint.draft_view")
        n = len(self._points)
        if self.shape == "text":
            return t("hint.draft.text_2") if n else t("hint.draft.text")
        if n == 0:
            return t("hint.draft." + self.shape)
        if self.shape in ("polyline", "region"):
            return t("hint.draft.more")
        if self.shape == "arc" and n == 2:
            return t("hint.draft.arc_3")
        return t("hint.draft.end_" + self.shape)

    def vcb_title(self):
        return t("vcb.text") if self.shape == "text" else t("vcb.length")

    # ------------------------------------------------------------ points

    def _pick(self, x, y):
        """(point, snap) under the mouse: an inference, else on the view's paper; (None, None) in 3D."""
        plane = self.viewport.view_plane()
        if plane is None:
            return None, None
        snap, _hit = self.viewport.snap(x, y)
        if snap is not None and snap.kind in SNAPPABLE:
            return snap.point.copy(), snap
        origin, _u, _v, n = plane
        ray_o, ray_d = self.viewport.ray(x, y)
        p = ray_plane(ray_o, ray_d, origin, n)
        return (p if p is not None else ray_plane(ray_o, ray_d, origin, -n)), None

    def _on_paper(self, p):
        """p brought onto the view's paper (a snap on an element's corner may be off it)."""
        origin, u, v, _n = self.viewport.view_plane()
        q = notes2d.to2([p], origin, u, v)[0]
        return origin + u * q[0] + v * q[1]

    def _near_first(self, x, y):
        if len(self._points) < (3 if self.shape == "region" else 2) or self.shape not in ("polyline", "region"):
            return False
        sx, sy = self.viewport.project(self._points[0])
        return float(np.hypot(sx - x, sy - y)) <= CLOSE_PX

    def _draft(self, points):
        extra = {} if self.shape == "text" else {"line": self.line}
        if self.width and self.shape != "text":
            extra["width"] = self.width
        if self.shape == "keynote":                      # (0.194) the element it points at
            extra["element"] = getattr(self, "_element", None)
        return notes2d.Annotation(self.viewport.current_view(), self.shape, list(points), hatch=self.hatch,
                                  size=self.size, extra=extra)

    def pointer_move(self, x, y, modifiers):
        p, snap = self._pick(x, y)
        if p is None:
            return
        p = self._on_paper(p)
        self._hover = (p, snap)
        self._end = p
        if not self._points or self.shape == "text":
            show_snap(self.viewport, snap, p)
            return
        origin, u, v, _n = self.viewport.view_plane()
        to3 = lambda q: origin + u * q[0] + v * q[1]               # noqa: E731
        pts = self._points + [p]
        kind = "polyline" if self.shape == "arc" and len(pts) == 2 else ("region" if self.shape == "region"
                                                                          and len(pts) >= 3 else self.shape)
        if self.shape == "region" and len(pts) < 3:
            kind = "polyline"
        draft = notes2d.Annotation(self.viewport.current_view(), kind, pts)
        segs = [to3(q) for a, b in notes2d.segments(draft, origin, u, v) for q in (a, b)]
        self.viewport.show_lines(segs, [PREVIEW] * len(segs))
        a2, b2 = notes2d.to2([self._points[-1], p], origin, u, v)
        self.host.set_vcb(_fmt(float(np.linalg.norm(b2 - a2))))
        show_snap(self.viewport, snap, p)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._points:
                self.cancel()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT:
            return
        if self.viewport.current_view() is None:
            self.host.message(t("hint.draft_view"))
            return
        if self._near_first(x, y):
            self._finish(closed=True)
            return
        p, _snap = self._pick(x, y)
        if p is None:
            return
        p = self._on_paper(p)
        if self._points and np.linalg.norm(p - self._points[-1]) < notes2d.MIN_SIZE:
            return
        if self.shape == "keynote" and not self._points:  # (0.194) its leader starts on an element
            guid = self.viewport.pick_object(x, y)
            obj = self.doc.get(guid) if guid is not None else None
            if obj is None or not obj.is_bim:
                self.host.message(t("err.keynote_element"), warning=True)
                return
            self._element = guid
        self._points.append(p)
        if len(self._points) >= NEEDED.get(self.shape, 10 ** 6) and self.shape != "text":
            self._finish()
            return
        self.host.set_hint(self.hint())

    def enter(self):
        if self.shape in ("polyline", "region"):
            self._finish(closed=self.shape == "region")

    def typed(self, text):
        if self.shape == "text":
            if self._points and text.strip():
                self._make(self._points[:1], text=text.strip())
            return
        if len(self._points) != 1:
            return
        origin, u, v, _n = self.viewport.view_plane()
        a2 = notes2d.to2(self._points[:1], origin, u, v)[0]
        b2 = notes2d.to2([self._end if self._end is not None else self._points[0]], origin, u, v)[0]
        d = b2 - a2
        d = d / np.linalg.norm(d) if np.linalg.norm(d) > 1e-9 else np.array((1.0, 0.0))
        to3 = lambda q: origin + u * q[0] + v * q[1]               # noqa: E731
        values = parse_lengths(text, 2)
        if values is None or values[0] is None or values[0] <= 0:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        if self.shape == "rectangle":
            w = values[0]
            h = values[1] if values[1] is not None else values[0]
            sx = -1.0 if d[0] < 0 else 1.0
            sy = -1.0 if d[1] < 0 else 1.0
            self._points.append(to3(a2 + np.array((sx * w, sy * h))))
        else:                                                   # a line's length, a circle's radius
            self._points.append(to3(a2 + d * values[0]))
        self._finish()

    def delete(self):
        """Delete: the last point clicked taken back."""
        if self._points:
            self._points.pop()
            self.host.set_hint(self.hint())

    def _finish(self, closed=False):
        pts = list(self._points)
        if self.shape == "polyline" and closed:
            pts.append(pts[0])
        if self.shape in ("polyline",) and len(pts) < 2 or self.shape == "region" and len(pts) < 3:
            return
        self._make(pts)

    def _make(self, pts, text=""):
        ann = self._draft(pts)
        ann.text = text
        origin, u, v, _n = self.viewport.view_plane()
        if ann.kind != "text" and not notes2d.shape(ann, origin, u, v):
            self.cancel()
            return
        self.doc.execute(notes2d.AddAnnotation(ann, t("cmd.draft")))
        self.host.message(t("info.draft", k=t("draft." + ann.kind)))
        self.cancel()

    def cancel(self):
        self._points = []
        self._end = None
        self._element = None
        self.viewport.clear_overlays()
        self.host.set_vcb("")
        self.host.set_hint(self.hint())
