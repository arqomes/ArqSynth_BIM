"""Base class for interactive tools, plus shared inference helpers.

A tool receives pointer events in logical pixels and typed measurements
(SketchUp's "Measurements" box), and talks to the app through `host`:
    host.doc        Document
    host.viewport   Viewport
    host.set_hint(text), host.set_vcb(text), host.message(text, warning=False)
"""

import math
from dataclasses import dataclass

import numpy as np

from ..core.inference import ON_EDGE, ON_FACE, ON_GUIDE, POINT_KINDS
from ..core.sketch_geometry import face_world_normal, plane_axes, ray_plane
from ..core.temp_dims import TempAngle, TempDim, across, level_angle
from ..core.temp_dims import revit as revit_look
from ..core.tracking import CROSSING, FOOT, LOCKED, infer, inference_lines
from ..i18n import t

Z_UP = np.array((0.0, 0.0, 1.0))

DRAG_THRESHOLD_PX = 8
LEFT, RIGHT, MIDDLE = 1, 2, 3
SNAPPABLE = POINT_KINDS + (ON_EDGE, ON_GUIDE)   # kinds that give an exact point

# SketchUp's inference colours
SNAP_COLORS = {
    "endpoint": (0.07, 0.63, 0.05, 1.0),
    "intersection": (0.55, 0.10, 0.10, 1.0),
    "midpoint": (0.00, 0.72, 0.80, 1.0),
    "origin": (0.89, 0.64, 0.10, 1.0),
    "on_edge": (0.91, 0.07, 0.14, 1.0),
    "on_guide": (0.35, 0.35, 0.35, 1.0),
    "on_face": (0.17, 0.37, 0.85, 1.0),
}
SQUARE_COLOR = (0.85, 0.10, 0.75, 1.0)


@dataclass
class Option:
    """One of a tool's settings on the contextual bar (0.85), as Revit's Options Bar: its type, a height, the
    wall's reference line…"""
    key: str
    label: str
    kind: str                       # "choice" | "length" | "toggle"
    value: object
    choices: tuple = ()             # a choice's ((value, text), …)


COMMON_KEYS = ("r", "shift+r", "space", "shift+space", "f", "x", "y", "n")


class Tool:
    name = ""
    title = ""                      # i18n key of its name on the contextual bar, for a tool with no button (0.100)
    accepts_typing = False
    on_storey = False               # it draws on the active storey (the contextual bar offers to change it)
    # the placement keys (0.86), as the ArqSynth Modeler's — R / Shift+R turn ±90°, Space / Shift+Space the
    # insertion point, F flips, X / Y lock the red / green axis and N lets go: the ones this tool uses (in it
    # they are not the window's shortcuts: R is not Rectangle, Space not Select)
    common_keys = frozenset()
    placement = False               # a placement tool: Esc goes back to Select (Space no longer does)
    keys_help = ""                  # i18n key of the line on the contextual bar saying its keys

    def __init__(self, host):
        self.host = host

    @property
    def doc(self):
        return self.host.doc

    @property
    def viewport(self):
        return self.host.viewport

    def activate(self):
        self.viewport.tracking.clear()          # (another tool: the points acquired are let go)
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    def deactivate(self):
        self.cancel()

    def hint(self):
        return ""

    def vcb_title(self):
        return ""

    def options(self):
        """The settings shown on the contextual bar while the tool is in use (0.85): [Option]."""
        return []

    def set_option(self, key, value):
        """One of them changed on the contextual bar."""

    def common_key(self, name):
        """One of the placement keys it uses (common_keys) pressed. True if used."""
        return False

    def pointer_down(self, x, y, button, modifiers):
        pass

    def pointer_move(self, x, y, modifiers):
        pass

    def pointer_up(self, x, y, button, modifiers):
        pass

    def typed(self, text):
        """Enter pressed with `text` in the Measurements box."""

    def enter(self):
        """Enter pressed with nothing typed (e.g. a selection polygon closed, 0.75)."""

    def arrow(self, key):
        """An arrow key ("up" / "down" / "left" / "right"); True if the tool used it (Walk, 0.80)."""
        return False

    def tab(self):
        """Tab pressed. Returns True if the tool used it (e.g. the wall's reference line)."""
        return False

    def ctrl_tap(self):
        """Ctrl pressed and released alone (Move / Rotate: copy on / off)."""

    def cancel(self):
        pass

    def delete(self):
        pass


# (0.450) the drawing tools of lines, side by side on the contextual bar as Revit's «Draw» panel: a click on one goes to
# it (straight lines, lines with arcs, a rectangle, a circle, an arc, a Bézier curve, by hand)
SKETCH_DRAW = ("line", "line_arc", "rectangle", "poly_in", "poly_out", "circle", "arc", "fillet", "bezier", "ellipse",
               "ellipse_part", "freehand", "pick")
#               (0.451: pick lines; 0.452: a fillet arc between two lines; 0.458: Revit's inscribed and circumscribed
#               polygons, ellipse and partial ellipse — in Revit's order)
DRAW_TOOL = {"line_arc": "line", "pick": "line", "fillet": "line",          # (0.458) which tool draws each
             "poly_in": "circle", "poly_out": "circle", "ellipse": "circle", "ellipse_part": "circle"}


def draw_option(current):
    """(0.450) The contextual bar's row of the drawing tools, `current` lit."""
    return Option("draw", t("ctx.draw"), "choice", current, tuple((k, t("draw." + k)) for k in SKETCH_DRAW))


def switch_draw(tool, value):
    """(0.450) Another of the drawing tools chosen on the bar: the window goes to it (a line's arcs: the Line tool
    with its arcs on; 0.458: a polygon or an ellipse, the Circle tool drawing it). True when it did."""
    if value not in SKETCH_DRAW:
        return False
    target = DRAW_TOOL.get(value, value)
    if target != tool.name and hasattr(tool.host, "set_tool"):
        tool.host.set_tool(target)
    now = getattr(tool.host, "tool", None)
    if now is not None and getattr(now, "name", None) == target and hasattr(now, "take_draw"):
        now.take_draw(value)
    return True


def moved_enough(a, b):
    return np.hypot(a[0] - b[0], a[1] - b[1]) > DRAG_THRESHOLD_PX


def show_snap(viewport, snap, point=None):
    """Coloured marker + tooltip for an inference — a snap or a point found on an alignment
    (tracking.Inferred) — or a plain marker at `point`. (0.446) As Revit's: its glyph in magenta (□ an end, △ a
    middle, ⊥ a foot…) and the edge snapped to lit, no marker."""
    if revit_look() and hasattr(viewport, "show_glyph"):
        viewport.show_marker(None)
        if snap is None:
            viewport.show_glyph()
            viewport.show_tip("", None)
            return
        viewport.show_glyph(glyph_of(snap), snap.point, snapped_edge(snap))
        viewport.show_tip(inferred_style(snap)[0], snap.point)
        return
    if snap is None:
        viewport.show_marker(point)
        viewport.show_tip("", None)
        return
    tip, marker, _line = inferred_style(snap)
    viewport.show_marker(snap.point, marker)
    viewport.show_tip(tip, snap.point)


def glyph_of(found):
    """(0.446) The Revit glyph of a snap or a point found (render/viewport.glyph_of)."""
    from ..render.viewport import glyph_of as of
    return of(found)


def snapped_edge(found):
    """(0.446) The edge a point found lies on — the nearest point on it, or the foot on it —, to be lit: (a, b) or None."""
    if found is None:
        return None
    snap = getattr(found, "snap", None) or found
    if getattr(snap, "kind", None) in (ON_EDGE, ON_GUIDE) and getattr(snap, "edge", None) is not None:
        return snap.edge
    if getattr(found, "kind", None) == FOOT:
        for line in getattr(found, "lines", None) or ():
            if getattr(line, "edge", None) is not None:
                return line.edge
    return None


def _line_colour(line):
    from ..render.viewport import AXIS_COLORS, EXTENSION_COLOR, PARALLEL_COLOR
    if line.kind.startswith(("axis_", "align_")):
        return AXIS_COLORS[line.kind[-1]]
    return EXTENSION_COLOR if line.kind == "extension" else PARALLEL_COLOR


def inferred_style(found):
    """(tip, marker colour, colour of the line drawn to it) of a snap or a point found
    (tracking.Inferred): the axis colour along an axis, magenta parallel / perpendicular…"""
    from ..render.viewport import PREVIEW
    kind = found.kind
    lines = getattr(found, "lines", None) or []
    if kind == LOCKED:
        line = lines[0]
        colour = _line_colour(line)
        return t("snap.locked", what=t("snap." + line.kind)), colour, colour
    if kind.startswith("axis_") or kind in ("parallel", "perpendicular"):
        colour = _line_colour(lines[0]) if lines else PREVIEW
        return t("snap." + kind), colour, colour
    if kind.startswith("align_") or kind == "extension":
        return t("snap." + kind), _line_colour(lines[0]), PREVIEW
    if kind == FOOT:
        from ..render.viewport import PARALLEL_COLOR
        return t("snap." + kind), PARALLEL_COLOR, PARALLEL_COLOR
    # a snap, or where lines cross; one of them may be an axis drawn along (its colour for the line)
    axis = next((ln for ln in lines if ln.kind.startswith("axis_")), None)
    line = _line_colour(axis) if axis is not None else PREVIEW
    if kind == CROSSING:
        return t("snap.crossing"), SNAP_COLORS["intersection"], line
    return t("snap." + kind), SNAP_COLORS[kind], line


AUTO_PLANE = object()      # infer_point: the plane drawn on is worked out (see _start_plane)


def level_plane(z):
    return np.array((0.0, 0.0, float(z))), Z_UP


def work_plane_of(viewport):
    """(0.412) The document's work plane (model/work_plane), in the 3D view — plans, sections and elevations keep
    their own planes —, or None (the active storey's level)."""
    plane = getattr(viewport.doc, "work_plane", None)
    if plane is None or viewport.current_view() is not None:
        return None
    return plane


def free_normal(viewport, direction):
    """The plane a point is taken on where nothing is snapped (Move's): (0.412) the work plane's, else
    default_normal."""
    plane = work_plane_of(viewport)
    return plane.normal if plane is not None else default_normal(direction)


def _start_plane(viewport, hit):
    """Starting a shape: the plane it starts on — the face under the cursor, or the active
    storey's level where there is none ((0.412) the work plane): (point, normal)."""
    if hit is not None:
        obj = viewport.doc.get(hit[0])
        if obj is not None:
            return np.asarray(hit[2], dtype=float), face_world_normal(obj.matrix, obj.mesh, hit[1])
    plane = work_plane_of(viewport)
    if plane is not None:
        return plane.origin, plane.normal
    return level_plane(viewport.doc.work_level())


def infer_point(viewport, x, y, last=None, modifiers=(), flat=False, plane=AUTO_PLANE):
    """The point for the mouse with the snaps and the alignments (core/tracking.py), drawing on
    from `last` (or starting: None). The corners near the cursor line it up by themselves (as
    Revit's); what the cursor rests on is acquired; Shift locks the line in use. flat: only level
    lines (walls and slabs: no blue). plane: (point, normal) of the plane drawn on — the
    alignments stay on it (None: anywhere; AUTO_PLANE: the face under the cursor or the storey's
    level when starting, the level through `last` in a plan). Returns (tracking.Inferred or None,
    snap, face hit)."""
    snap, hit = viewport.snap(x, y)
    tracking = viewport.tracking
    tracking.rest(snap)
    if "Shift" not in (modifiers or ()):
        tracking.lock = None
    elif tracking.lock is None and tracking.current is not None:
        tracking.lock = tracking.current
    if plane is AUTO_PLANE:
        if last is None:
            plane = _start_plane(viewport, hit)
        else:
            plane = level_plane(last[2]) if (flat or viewport.plan) else None
    origin, direction = viewport.ray(x, y)
    lines = inference_lines(tracking, last, plan=viewport.plan or flat, auto=viewport.nearby_points(x, y),
                            plane=plane)
    found = infer(snap, lines, origin, direction, (x, y), viewport.project_many, last=last, lock=tracking.lock)
    tracking.current = found.lines[0] if found is not None and found.lines else None
    return found, snap, hit


def default_normal(direction):
    """Ground plane, unless the view is (almost) horizontal: then a vertical plane facing the view."""
    if abs(direction[2]) >= 0.1:
        return np.array((0.0, 0.0, 1.0))
    if abs(direction[0]) > abs(direction[1]):
        return np.array((-1.0 if direction[0] > 0 else 1.0, 0.0, 0.0))
    return np.array((0.0, -1.0 if direction[1] > 0 else 1.0, 0.0))


def start_reference(found):
    """Where a distance typed before the first click is measured from (0.61): the point the
    alignment followed comes from — or the nearer end of the edge under the cursor — and the
    direction from it to the cursor. Returns (point, unit direction) or None."""
    if found is None:
        return None
    point = np.asarray(found.point, dtype=float)
    for line in getattr(found, "lines", None) or ():
        if line.kind.startswith("axis_"):
            continue
        src = line.point if line.kind != "extension" else min(
            line.edge, key=lambda e: float(np.linalg.norm(np.asarray(e) - point)))
        d = point - np.asarray(src, dtype=float)
        if np.linalg.norm(d) > 1e-6:
            return np.asarray(src, dtype=float), d / np.linalg.norm(d)
    snap = getattr(found, "snap", found)
    if found.kind == ON_EDGE and snap is not None and getattr(snap, "edge", None) is not None:
        a, b = (np.asarray(e, dtype=float) for e in snap.edge)
        src = a if np.linalg.norm(point - a) <= np.linalg.norm(point - b) else b
        d = point - src
        if np.linalg.norm(d) > 1e-6:
            return src, d / np.linalg.norm(d)
    return None


def show_start_reference(viewport, ref, point, normal=None):
    """The distance from where a typed start is measured to the cursor, as a temporary dimension."""
    if ref is None or point is None:
        viewport.clear_temp_dims()
        return
    viewport.show_temp_dims([TempDim(ref[0], np.asarray(point, dtype=float), Z_UP if normal is None else normal)])


def drawing_dims(viewport, a, b, normal=None, extra=()):
    """While drawing a→b: its length as a temporary dimension and, on a level plane, its angle
    from the red axis (when it is not along an axis)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    normal = Z_UP if normal is None else np.asarray(normal, dtype=float)
    dims = [TempDim(a, b, normal)] + list(extra)
    angles = []
    if abs(normal[2]) > 0.999 and np.linalg.norm((b - a)[:2]) > 1e-6:
        deg = level_angle(a, b)
        if revit_look():
            # (0.446) as Revit's: the angle from a grey reference line along the red axis, a wide arc (as long as
            # most of what is drawn, on the screen) — shown upright too (90°), not level (0°, 180°)
            if min(deg % 180.0, 180.0 - deg % 180.0) > 0.05:
                (x0, y0), (x1, y1) = viewport.project(a), viewport.project(b)
                length_px = float(np.hypot(x1 - x0, y1 - y0)) if np.all(np.isfinite((x0, y0, x1, y1))) else 120.0
                angles.append(TempAngle(a, np.array((1.0, 0.0, 0.0)), deg if deg <= 180 else deg - 360.0, Z_UP,
                                        radius_px=float(np.clip(0.85 * length_px, 40.0, 260.0))))
        elif min(deg % 90.0, 90.0 - deg % 90.0) > 0.05:
            angles.append(TempAngle(a, np.array((1.0, 0.0, 0.0)), deg if deg <= 180 else deg - 360.0, Z_UP))
    viewport.show_temp_dims(dims, angles)


def outside_dim(a, b, inside, normal=None, key=None):
    """A temporary dimension a→b drawn on the side away from `inside` (a rectangle's sides…)."""
    normal = Z_UP if normal is None else np.asarray(normal, dtype=float)
    dim = TempDim(np.asarray(a, dtype=float), np.asarray(b, dtype=float), normal, key=key)
    n = across(dim.a, dim.b, normal)
    if n is not None and float((np.asarray(inside, dtype=float) - dim.a) @ n) > 0:
        dim.side = -1.0
    return dim


ANGLE_STEP = 45.0           # (0.448) drawing on a level snaps every 45° (0°, 45°, 90°…), as Revit's…
ANGLE_SNAP_DEG = 2.5        # …and parallel to the walls and lines there, within this many degrees
PARALLEL_REACH = 20.0       # m: the walls and lines this near are looked at for it
_DIRECTIONS = {"key": None, "value": None}


def level_directions(doc):
    """(0.448) The walls' axes and the loose lines of the model lying level: (unit directions (K, 2), their edges
    (K, 2, 3)), worked out once per change of the model."""
    key = (id(doc), getattr(doc, "revision", None))
    if _DIRECTIONS["key"] == key and _DIRECTIONS["value"] is not None:
        return _DIRECTIONS["value"]
    from ..model import bim, line_edit
    edges = []
    try:
        edges += [(np.asarray(s, dtype=float), np.asarray(e, dtype=float)) for _g, s, e, _t in bim.wall_axes(doc)]
    except (RuntimeError, AttributeError, KeyError, ValueError, TypeError):
        pass                                            # (the IFC still being read)
    for obj in list(getattr(doc, "objects", {}).values()):
        if line_edit.is_lines(obj):
            edges += [(a, b) for _i, _j, a, b in line_edit.segments(obj)]
    edges = np.array([e for e in edges if abs(float(e[1][2] - e[0][2])) < 1e-6
                      and float(np.linalg.norm((e[1] - e[0])[:2])) > 0.05], dtype=float).reshape(-1, 2, 3)
    d = edges[:, 1, :2] - edges[:, 0, :2]
    dirs = d / np.maximum(np.linalg.norm(d, axis=1), 1e-12)[:, None] if len(edges) else np.zeros((0, 2))
    _DIRECTIONS["key"], _DIRECTIONS["value"] = key, (dirs, edges)
    return dirs, edges


def direction_snap(doc, last, p):
    """(0.448, the owner: «no desenho deve ter snap a 0, 45, 90 grau… ele faz o snap de paralelo assim a nova parede
    é desenhada com segurança na mesma direção») The point `p` drawn to from `last` on a level, brought onto the
    nearest snapping direction within ANGLE_SNAP_DEG: every 45° — the red and green axes, the diagonals — or parallel
    to a wall or a loose line within PARALLEL_REACH. Returns (point, kind — "axis_x" / "axis_y" / "angle" /
    "parallel" —, the edge it is parallel to or None, its angle in degrees) or None."""
    last, p = np.asarray(last, dtype=float), np.asarray(p, dtype=float)
    v = (p - last)[:2]
    length = float(np.linalg.norm(v))
    if length < 1e-6:
        return None
    heading = math.degrees(math.atan2(v[1], v[0]))
    best = None                                          # (deviation, kind, edge, unit direction)
    for k in range(int(round(360.0 / ANGLE_STEP))):
        a = k * ANGLE_STEP
        dev = abs((heading - a + 180.0) % 360.0 - 180.0)
        if dev <= ANGLE_SNAP_DEG and (best is None or dev < best[0]):
            kind = "axis_x" if a % 180.0 == 0 else "axis_y" if a % 180.0 == 90.0 else "angle"
            best = (dev, kind, None, np.array((math.cos(math.radians(a)), math.sin(math.radians(a)))))
    dirs, edges = level_directions(doc)
    if len(edges):
        mid = (edges[:, 0, :2] + edges[:, 1, :2]) / 2
        half = np.linalg.norm(edges[:, 1, :2] - edges[:, 0, :2], axis=1) / 2
        near = (np.linalg.norm(mid - last[:2], axis=1) - half <= PARALLEL_REACH) & \
            (np.abs(edges[:, 0, 2] - last[2]) < 1.0)
        u = v / length
        cos = np.abs(dirs @ u)
        for k in np.flatnonzero(near & (cos >= math.cos(math.radians(ANGLE_SNAP_DEG)))):
            d = dirs[k] if float(dirs[k] @ u) >= 0 else -dirs[k]
            dev = math.degrees(math.acos(min(1.0, float(cos[k]))))
            if best is None or dev < best[0] - 1e-6:
                best = (dev, "parallel", (edges[k, 0].copy(), edges[k, 1].copy()), d)
    if best is None:
        return None
    _dev, kind, edge, d = best
    q = last.copy()
    q[:2] = last[:2] + d * float(v @ d)
    q[2] = p[2]
    return q, kind, edge, math.degrees(math.atan2(d[1], d[0])) % 360.0


def snap_tip(kind, degrees):
    """(0.448) The tip of a direction snap."""
    if kind == "angle":
        return t("snap.angle", a="{:g}".format(round(degrees, 1)))
    return t("snap.parallel_to" if kind == "parallel" else "snap." + kind)


def point_from(viewport, last, normal, x, y, modifiers=()):
    """The point under the mouse when drawing on from `last` (Line, Move, Rotate), in SketchUp's
    order with the alignments (tracking.infer): Shift's locked line > points (endpoint,
    intersection, midpoint, origin) > where two lines cross (the axes through `last`, the
    alignments with the points acquired, parallel / perpendicular to an acquired edge, its
    extension) > edges and guides (where a line crosses them; the foot of the perpendicular from
    `last`) > the nearest line > a face > the plane through `last` with `normal`. The lines
    followed are shown dashed. Returns (point, tip, marker colour, line colour) or None."""
    from ..render.viewport import PREVIEW
    found, _snap, _hit = infer_point(viewport, x, y, last, modifiers, plane=(np.asarray(last, dtype=float), normal))
    glyphs = revit_look() and hasattr(viewport, "show_glyph")      # (0.446: Revit's glyph for what is found)
    if found is not None:
        viewport.show_alignments(found.lines, found.point)
        tip, marker, line = inferred_style(found)
        if glyphs:
            viewport.show_glyph(glyph_of(found), found.point, snapped_edge(found))
        return found.point.copy(), tip, marker, line
    if glyphs:
        viewport.show_glyph()
    viewport.show_alignments()
    origin, direction = viewport.ray(x, y)
    p = ray_plane(origin, direction, last, normal)
    if p is None:
        p = ray_plane(origin, direction, last, -normal)
    if p is None:
        return None
    if abs(float(np.asarray(normal, dtype=float)[2])) > 0.999 and "Shift" not in (modifiers or ()):
        found = direction_snap(viewport.doc, last, p)    # (0.448) on a level: every 45°, parallel to what is there
        if found is not None:
            q, kind, edge, degrees = found
            if glyphs:
                viewport.show_glyph(kind, q, edge)
            from ..render.viewport import AXIS_U, AXIS_V, PARALLEL_COLOR
            colour = AXIS_U if kind == "axis_x" else AXIS_V if kind == "axis_y" else PARALLEL_COLOR
            return q, snap_tip(kind, degrees), colour, colour
    return p, "", PREVIEW, PREVIEW


@dataclass
class StartPlane:
    point: np.ndarray
    normal: np.ndarray
    u: np.ndarray
    v: np.ndarray
    face: tuple          # (obj_id, face_index) when the plane is a face of a volume, else None
    snap: object         # the inference used, or None


def start_plane(host, x, y, modifiers=()):
    """Where a new shape starts under the mouse, using inferences:
    - a snapped point (endpoint, midpoint, origin, on edge), or a point lined up with the
      points acquired (alignments, 0.60): exactly there, on the face under the cursor if the
      point lies on it, else on a level plane;
    - else the face under the cursor;
    - else the level of the active storey (or a vertical plane in front/side views) — (0.412) or, in the 3D view,
      the work plane set (a point snapped starts on a plane parallel to it)."""
    viewport = host.viewport
    found, snap, hit = infer_point(viewport, x, y, None, modifiers)
    origin, direction = viewport.ray(x, y)
    face_normal = None
    if hit is not None:
        obj = host.doc.get(hit[0])
        face_normal = face_world_normal(obj.matrix, obj.mesh, hit[1])
    viewport.show_alignments(found.lines if found is not None else (), found.point if found is not None else None)
    work = work_plane_of(viewport)

    if found is not None and found.kind != ON_FACE:
        p = found.point
        if face_normal is not None and abs((p - hit[2]).dot(face_normal)) < 1e-5:
            return StartPlane(p, face_normal, *plane_axes(face_normal), (hit[0], hit[1]), found)
        if work is not None:
            return StartPlane(p, work.normal, work.u, work.v, None, found)
        n = default_normal(direction)
        return StartPlane(p, n, *plane_axes(n), None, found)

    if hit is not None:
        return StartPlane(hit[2], face_normal, *plane_axes(face_normal), (hit[0], hit[1]),
                          snap if snap is not None and snap.kind == ON_FACE else None)

    if work is not None:                             # (0.412) on the work plane
        from ..model.work_plane import ray_point
        p = ray_point(work, origin, direction)
        if p is None:
            p = ray_plane(origin, direction, work.origin, work.normal)
        if p is None:
            return None
        return StartPlane(p, work.normal, work.u, work.v, None, None)

    n = default_normal(direction)
    p = ray_plane(origin, direction, np.array((0.0, 0.0, host.doc.work_level())), n)
    if p is None:
        return None
    return StartPlane(p, n, *plane_axes(n), None, None)
