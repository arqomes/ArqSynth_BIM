"""Select tool (SketchUp 'Space'): click a volume, element or line to select it; Delete removes it.

A sketch's face (0.310, as SketchUp's): a click picks just that face — with the strips joined to it across hidden
edges, an offset's frame is one face —; two clicks in a row, the face and its edges; three, the whole sketch.
Delete takes the face out (its outline stays as lines), Move / Rotate move just it (model/parts.py).

An element of a group selects its whole group copy; a second click picks just
that element (its edits are repeated in every copy of the group).
If a "Classify as…" type was chosen with nothing selected, the next click on a
sketch volume classifies it (pick-to-classify).
With the section box on (3D), dragging one of its handles (the blue dots in the
middle of its faces) moves that face of the box.

Temporary dimensions (0.61, as Revit's): an element selected alone shows blue
dimensions — a wall its length and its distances to the walls beside it, a door
or window its distances to the wall's ends, a line each segment's length. Click
a value (it turns orange), type the new one, Enter: the element moves or
changes to it (one undo step).

Grips (0.62, parametric lines): lines selected show a square on each end and a
diamond in each segment's middle. Drag one — or click it, then click where it
goes; or type how far — with the snaps and alignments: an end moves (a middle
moves its segment) and the lines joined there follow (model/line_edit.py).

A wall's «+» (0.353): a straight wall selected alone shows a «+» on each end of its axis; a click on one takes the
Wall tool, of that wall's type and height, drawing on from that end (the new wall joined to it there). TAB (0.354):
the quick edit of what is selected, beside it. A double click on a wall (0.355): its profile edited.

Grid axes (0.72): a click on an axis's bubble, or on its line where nothing else
is, selects it (Shift: more). Its end grips slide it along itself — the ends of
the parallel axes lined up with it go too, as Revit keeps bubbles aligned (Ctrl:
this one only); its middle grip moves it across; its temporary dimensions give
the distance to the axes beside it; Delete removes it."""

import time
from dataclasses import dataclass

import numpy as np

from ..core import curves as core_curves
from ..core import region_select as rs
from ..core import roof_blocks as core_blocks
from ..core import sketch_geometry as sg
from ..core import temp_dims
from ..core.inference import ENDPOINT, MIDPOINT, ON_EDGE
from ..core.sketch_geometry import closest_on_line_to_ray, ray_plane, transform_point
from ..core.transform import translation
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, lang, refusal, t
from ..model import bim, curve_edit, line_edit, parts
from ..model import annotations as notes2d
from ..model import dimensions as dims_model
from ..render.viewport import PREVIEW
from .base import (
    LEFT, RIGHT, Z_UP, Tool, default_normal, infer_point, inferred_style, level_plane, moved_enough, outside_dim,
)

MAX_LINE_DIMS = 12          # a line of more segments shows the first ones
WALL_LENGTH_PX = 50         # a wall's length is drawn this far off its face (0.361: 34; 0.372: the addon's 50, as in the
#                             owner's picture — its value's box between the line and the wall)


def _later(fn):
    """(0.356) Run `fn` once the click is over (a dialog opened from inside the pointer's event would hold it)."""
    try:
        from PySide6 import QtCore
    except ImportError:                     # (no Qt: at once)
        fn()
        return
    QtCore.QTimer.singleShot(0, fn)
CLOSE_PX = 10               # a polygon's point clicked this near its first one: closed (0.75)
LINE_PX = 7                 # (0.373) a click this near a loose line on the screen picks it
DOUBLE_CLICK_S = 0.6        # two clicks on a view's mark this close in time: a double click (0.121)


@dataclass
class _GripMove:
    base: np.ndarray            # the grip's point when it was taken
    points: list                # the line ends that move with it (an end: itself; a middle: its segment's two)
    press: tuple                # where it was pressed (screen)
    plane: tuple                # (point, normal) of the level it moves on, or None (lines not level)
    target: np.ndarray = None   # where it goes
    dragging: bool = True       # held down (dragged) — or clicked: it follows the mouse to the next click
    middle: bool = False        # (0.373) a line's middle: clicked (not dragged), it picks that line, as SketchUp's


@dataclass
class _CurveMove:
    """(0.373) A curve's grip being moved: an arc's end or middle, a Bézier curve's point or tangent — on its plane."""
    obj_id: int
    what: object                # curve_edit.grips' (what it is)
    base: np.ndarray
    press: tuple
    plane: tuple                # (point, normal) of the curve's plane (world)
    target: np.ndarray = None
    dragging: bool = True


@dataclass
class _AnnMove:
    """(0.191) A point of a drawing in the view (a line's end, a corner, a circle's centre, a text's start…) being
    moved by its grip, on the view's paper."""
    ann: object
    index: int
    base: np.ndarray
    press: tuple
    plane: tuple                # (point, normal) of the view's paper
    target: np.ndarray = None
    dragging: bool = True


@dataclass
class _DimMove:
    """(0.402) A grip of a dimension string being moved, on its view's paper: "line" (the string's line, across
    itself), "text" (a value's text, apart), "witness" (a witness line, to another reference)."""
    kind: str
    dims: list                  # the string's pieces (or the one whose text moves)
    index: int                  # the witness's index (dim_edit.witness_points), else -1
    base: np.ndarray
    press: tuple
    plane: tuple                # (point, normal) of the view's paper
    target: np.ndarray = None
    ref: object = None          # (a witness) the reference under the mouse: the dimension tool's Ref
    dragging: bool = True
    # (0.405) what it is snapped to: a value — the other values' middles (2D), its line's middle (2D); a line — its
    # across vector (3D) and the other parallel lines' places across it
    others: list = None
    mid2: np.ndarray = None
    across: np.ndarray = None


@dataclass
class _AxisMove:
    """A grid axis's grip being moved (0.72): an end slides along the axis (the ends lined up with it on
    the parallel axes go too, unless Ctrl is held); the middle moves the axis across."""
    index: int
    which: str                  # "start" | "end" | "middle"
    base: np.ndarray            # the grip's point when it was taken
    press: tuple
    alone: bool = False
    target: np.ndarray = None
    dragging: bool = True


@dataclass
class _DivisionMove:
    """(0.244) A cabinet's division dragged by its grip: along the cabinet's width, between its neighbours (each
    compartment 15 cm at least)."""
    guid: str
    index: int
    base: np.ndarray            # the grip's point when it was taken (the middle of the division's front edge)
    x_dir: np.ndarray           # the cabinet's width's way
    lo: float                   # how far it may go each way along x_dir (m; lo ≤ 0 ≤ hi)
    hi: float
    height: float               # its carcass's (the preview's line)
    press: tuple
    target: np.ndarray = None
    dragging: bool = True


@dataclass
class _BlockMove:
    """(0.264) A roof block's grip taken: a side's — it goes out or in along the block, the opposite side staying (as
    the add-on's roof block stretch) — or its middle's: the whole block moves on its level."""
    guid: str
    index: int                  # the block
    side: int                   # 0..3 (N, E, S, W); -1: the whole block
    base: np.ndarray            # the grip's point when it was taken
    way: np.ndarray             # a side's outward way (3,), None for the whole block
    shortest: float             # how far in a side may go (the block 20 cm at least; ≤ 0)
    level: float                # the roof's level (the preview's height)
    press: tuple
    target: np.ndarray = None
    dragging: bool = True


@dataclass
class _SectionMove:
    """(0.358) A section line's end dragged by its grip: along its line, in the plan."""
    index: int                  # the section (doc.sections)
    end: int                    # 0: its start, 1: its end (as drawn)
    a: np.ndarray               # its line's two ends when taken (world, on the view's paper)
    b: np.ndarray
    base: np.ndarray            # the grip's point when it was taken
    press: tuple
    target: np.ndarray = None
    dragging: bool = True


def section_grips(doc, viewport, name):
    """(0.358) A section chosen in a plan: (its index, its line's ends (world, on the plan's paper), the point of its
    «turn» grip — a diamond a little out from its middle, the way it looks) — or None."""
    from ..model import symbols as marks_model
    index = next((k for k, s in enumerate(doc.sections) if s.name == name), None)
    plane = viewport.view_plane()
    if index is None or plane is None or not viewport.plan:
        return None
    origin, u, v, _n = plane
    try:
        scale = doc.view_settings(viewport.current_view()).scale or 100
    except Exception:                                     # (no view settings yet)
        scale = 100
    mm = scale / 1000.0
    mark = next((m for m in marks_model.section_marks(doc, None, mm) if m.ref == name), None)
    if mark is None:
        return None
    a, b = origin + u * mark.a[0] + v * mark.a[1], origin + u * mark.b[0] + v * mark.b[1]
    look = u * mark.look[0] + v * mark.look[1]
    return index, a, b, (a + b) / 2 + look * marks_model.HEAD * mm * 2.5


FLIP_LONG = 0.30            # m: (0.359; 0.404: inside the door) a door's flip arrows this long…
FLIP_HEAD = 0.06            # m: …their heads this long
FLIP_PICK_PX = 14           # (0.404) a click this near an arrow (anywhere along it) flips
DIM_SNAP_PX = 8             # (0.405) a value / a dimension line dragged this near an alignment snaps to it
DIM_GUIDE = (0.85, 0.10, 0.75, 1.0)   # (0.405) its guide lines (as the alignments' colour)


def _double_arrow(a, b, head):
    """Segments (pairs of points) of a double-headed arrow from a to b."""
    d = (b - a) / max(float(np.linalg.norm(b - a)), 1e-12)
    across = np.array((-d[1], d[0], 0.0))
    out = [a, b]
    for tip, back in ((a, d), (b, -d)):
        out += [tip, tip + (back + across * 0.6) * head, tip, tip + (back - across * 0.6) * head]
    return out


def door_flips(doc, ids):
    """(0.359) A door or window chosen alone, as Revit's flip controls: (its GlobalId, [(what, the middle of its arrow)],
    the arrows' segments) — a door's «hinge» arrow along the wall in front of the side it opens to (its hinges to the
    other jamb) and its «side» arrow across the wall beside it (opening to the other side); a window's «side» only —
    else None."""
    if len(ids) != 1 or doc.loading:
        return None
    guid = next(iter(ids))
    obj = doc.get(guid)
    if obj is None or not obj.is_bim or obj.ifc_class not in ("IfcDoor", "IfcWindow"):
        return None
    e = doc.ifc.by_guid(guid)
    wall = doc.ifc.host_wall(guid)
    if e is None or not e.OverallWidth or wall is None or doc.ifc.kind_of(wall) != "wall":
        return None
    width = e.OverallWidth * doc.ifc.unit_scale
    thickness = doc.ifc.wall_params(wall)[2]
    m = doc.ifc.placement(guid)
    at = lambda x, y: m[:3, :3] @ np.array((x, y, 0.0)) + m[:3, 3]           # noqa: E731
    flips, segs = [], []
    # (0.404, the owner's drawing: inside the door, smaller) the hinges' arrow in the opening, along the wall; the
    # side's in the swing, across it (a window's across its middle)
    long = min(FLIP_LONG, width * 0.45)
    if obj.ifc_class == "IfcDoor":
        a, b = at(width / 2 - long / 2, thickness / 2), at(width / 2 + long / 2, thickness / 2)
        flips.append(("hinge", (a + b) / 2, a, b))
        segs += _double_arrow(a, b, FLIP_HEAD)
        middle = thickness + width * 0.45
        a, b = at(width / 2, middle - long / 2), at(width / 2, middle + long / 2)
    else:
        a, b = at(width / 2, thickness / 2 - long / 2), at(width / 2, thickness / 2 + long / 2)
    flips.append(("side", (a + b) / 2, a, b))
    segs += _double_arrow(a, b, FLIP_HEAD)
    return guid, flips, segs


def wall_ends(doc, ids):
    """(0.353) A straight wall chosen alone: (its GlobalId, [its axis's start, its end] at its base) — where its «+»
    are, to go on drawing it — else None."""
    if len(ids) != 1 or doc.loading:
        return None
    guid = next(iter(ids))
    obj = doc.get(guid)
    if obj is None or not obj.is_bim or doc.ifc.kind_of(guid) != "wall":
        return None
    a, b, _t = doc.ifc.wall_axis(guid)
    return guid, [a, b]


def block_grips(doc, ids):
    """(0.264) A roof by blocks selected alone: (its GlobalId, its blocks in the plan, its level, [(block, side,
    point)] a grip in the middle of each block's sides — on the block's top there —, [each block's middle on its
    top]) — else None."""
    if len(ids) != 1 or doc.loading:
        return None
    guid = next(iter(ids))
    obj = doc.get(guid)
    if obj is None or not obj.is_bim or doc.ifc.kind_of(guid) != "roof":
        return None
    p = doc.ifc.roof_params(guid)
    if p["form"] != "blocks":
        return None
    level, blocks = float(p["eave"]), doc.ifc.roof_blocks_world(guid)
    top = lambda b, x, y: level + (core_blocks.block_top(b, x, y) or 0.0)      # noqa: E731
    sides = []
    for i, b in enumerate(blocks):
        for k in range(4):
            out, half = core_blocks.side_way(b, k)
            x, y = b.cx + out[0] * half, b.cy + out[1] * half
            sides.append((i, k, np.array((x, y, top(b, x, y)))))
    middles = [np.array((b.cx, b.cy, top(b, b.cx, b.cy))) for b in blocks]
    return guid, blocks, level, sides, middles


def division_grips(doc, ids):
    """(0.244) A cabinet selected alone with divisions: (its GlobalId, [the middle of each division's front edge
    (3,)], its x way (3,), its core.cabinets.Cabinet) — else None."""
    from ..core import cabinets as core_cab
    if len(ids) != 1 or doc.loading:
        return None
    guid = next(iter(ids))
    obj = doc.get(guid)
    if obj is None or not obj.is_bim or obj.ifc_class != "IfcFurniture":
        return None
    found = doc.ifc.cabinets({guid})
    c = found.get(guid)
    if c is None or not c.divisions:
        return None
    m = doc.ifc.placement(guid)
    x = m[:3, 0] / np.linalg.norm(m[:3, 0])
    y = m[:3, 1] / np.linalg.norm(m[:3, 1])
    front = core_cab.BACK + c.depth
    mid = c.bottom + c.height / 2
    points = [m[:3, 3] + x * d + y * front + Z_UP * mid for d in c.divisions]
    return guid, points, x, c


def grid_dims(doc, index, z):
    """A grid axis selected alone: its distances to the nearest parallel axis on each side (0.72)."""
    axis = doc.grids[index]
    d = bim.grid_direction(axis)
    n = np.array((-d[1], d[0], 0.0))
    mid = np.array(((axis.start[0] + axis.end[0]) / 2, (axis.start[1] + axis.end[1]) / 2, z))
    return [temp_dims.TempDim(mid, mid + n * off, Z_UP, key=("grid_offset", index, k))
            for k, off in bim.grid_neighbours(doc.grids, index)]


def selection_dims(doc, ids, faces=False):
    """The temporary dimensions of what is selected — one element alone: [TempDim] (core/temp_dims). faces: (0.361)
    a wall's relations from face to face, else from axis to axis."""
    if len(ids) != 1 or doc.loading:
        return []
    obj = doc.get(next(iter(ids)))
    if obj is None:
        return []
    try:
        if obj.is_bim:
            kind = doc.ifc.kind_of(obj.id)
            if kind == "wall":
                return _wall_dims(doc, obj.id, faces)
            if kind in ("door", "window") or kind == "curtain_wall" and doc.ifc.host_wall(obj.id):   # (0.188)
                return _filling_dims(doc, obj.id)
            return []
    except (ValueError, KeyError, IndexError, AttributeError):
        return []                                    # (an element read from another program: no dimensions)
    if obj.mesh.lines and not obj.mesh.faces and not obj.curve:      # (0.373: a curve's pieces have none)
        world = [transform_point(obj.matrix, v) for v in obj.mesh.verts]
        return [temp_dims.TempDim(world[i], world[j], Z_UP, key=("line", obj.id, i, j))
                for i, j in obj.mesh.lines[:MAX_LINE_DIMS]]
    return []


def _wall_dims(doc, guid, faces=False):
    """A wall's length, on the face away from its nearest neighbour, and (0.361) its relations to the walls round it
    (temp_dims.wall_relations): across to the nearest parallel wall on each side, and beyond each free end to the
    first wall there — from axis to axis, or (faces) from face to face."""
    a, b, thickness = doc.ifc.wall_axis(guid)
    others = [(g, s, e, w) for g, s, e, w in bim.wall_axes(doc)
              if g != guid and abs(s[2] - a[2]) < temp_dims.SAME_FLOOR]
    relations = temp_dims.wall_relations((a, b), thickness, others, faces=faces)
    sides = {r.which for r in relations if r.kind == "side"}
    side = -1.0 if 1 in sides and -1 not in sides else 1.0
    left = temp_dims.across(a, b, Z_UP)
    face = left * side * thickness / 2
    dims = [temp_dims.TempDim(a + face, b + face, Z_UP, side=side, key=("wall_length", guid),
                              offset_px=WALL_LENGTH_PX)]
    for r in relations:
        key = ("wall_offset", guid) if r.kind == "side" else ("wall_end", guid, r.which)
        dims.append(temp_dims.TempDim(r.a, r.b, Z_UP, key=key, offset_px=0.0, kind="relation"))
    return dims


def _filling_dims(doc, guid):
    """A door's or window's distances to its wall's ends, along the face it opens to."""
    st = doc.ifc.filling_state(guid)
    if st.get("curved"):                              # (0.177) in a curved wall: in its Properties, along the arc
        return []
    f = st["frame"]
    s, w = st["s"], st["width"]
    y = f.y0 if st.get("side", -1) < 0 else f.y1
    at = lambda x: f.to_world((x, y, f.z0))           # noqa: E731
    inside = f.to_world((f.x0 + f.length / 2, (f.y0 + f.y1) / 2, f.z0))
    return [outside_dim(at(f.x0), at(s), inside, key=("from_start", guid)),
            outside_dim(at(s + w), at(f.x0 + f.length), inside, key=("to_end", guid))]


def apply_dim(doc, dim, value):
    """A temporary dimension typed over: the element moves or changes so that it measures `value`."""
    kind, target = dim.key[0], dim.key[1]
    if kind == "wall_length":
        bim.resize_wall(doc, target, at_end=value - dim.value)
    elif kind == "wall_offset":
        towards = (np.asarray(dim.b) - np.asarray(dim.a)) / dim.value       # from the wall to its neighbour
        if not bim.transform_objects(doc, [target], translation(towards * (dim.value - value)), t("cmd.move")):
            raise ValueError("not moved")
    elif kind == "wall_end":                              # (0.361) a free end to the wall beyond it: that end moves
        grow = dim.value - value
        bim.resize_wall(doc, target, **({"at_start": grow} if dim.key[2] == 0 else {"at_end": grow}))
    elif kind in ("from_start", "to_end"):
        st = doc.ifc.filling_state(target)
        f = st["frame"]
        s = f.x0 + value if kind == "from_start" else f.x0 + f.length - value - st["width"]
        bim.move_filling(doc, target, s=s)
    elif kind == "line":                                  # its end moves along it; the lines joined there follow
        _, i, j = dim.key[1:]
        line_edit.set_length(doc, target, i, j, value)
    elif kind == "grid_offset":                           # the axis selected moves across, its neighbour stays
        axis = doc.grids[target]
        away = (np.asarray(dim.a) - np.asarray(dim.b))[:2] / dim.value          # from the neighbour to it
        shift = away * (value - dim.value)
        bim.move_grid_axes(doc, {target: (np.array(axis.start) + shift, np.array(axis.end) + shift)})


class SelectTool(Tool):
    name = "select"

    def __init__(self, host):
        super().__init__(host)
        self._box_drag = None        # (axis, side, handle point at the start) while a box handle is dragged
        self._dims = []              # the temporary dimensions of the element selected alone
        self._active = None          # the one clicked, to be typed over
        self._hover = None           # (0.361) the one under the mouse (its value, or a relation's line): drawn strong
        self._grip_segments = []     # (a, b) of the lines selected, in the order of their middle grips
        self._axis_grips = None      # grid axes selected (0.72): ([(index, "start" | "end")], [index]) of the grips
        self._ann_grips = []         # (0.191) drawings in the view selected: (annotation, point index) per grip
        self._curve_grips = None     # (0.373) a curve selected alone: (its id, what each grip is, how many ends)
        self._cab_grips = None       # (0.244) a cabinet selected alone: division_grips
        self._block_grips = None     # (0.264) a roof by blocks selected alone: block_grips
        self._wall_ends = None       # (0.353) a wall selected alone: wall_ends (its «+»)
        self._door_flips = None      # (0.359) a door / window selected alone: door_flips (its arrows)
        self._section = None         # (0.358) the name of the section chosen in the plan (its head clicked)
        self._section_grips = None   # …and its section_grips
        self._move = None            # a grip being moved (_GripMove, _AxisMove, _AnnMove, _DivisionMove, _BlockMove)
        self.drag_shape = "box"      # what dragging draws (0.75): "box" | "lasso"
        self._press = None           # (x, y, modifiers) of the left button held down, to select on its release
        self._region = None          # the box (its two corners) / lasso (its path) being dragged, on the screen
        self._picking = None         # ("polygon" | "fence", [points clicked]) — Selecionar ▸ Polígono / Cerca
        self._part_click = None      # (0.310) ((obj_id, its faces), when, clicks in a row) of the face clicked last
        self._dim_click = None       # (0.402) (the dimension string clicked last, when): a second click is a double
        self._dim_grips = None       # (0.402) a dimension string chosen: (its pieces, witness count, middles' kinds)
        host.viewport.selection_listeners.append(lambda _ids: self._refresh_dims(keep=False))
        host.viewport.axes_listeners.append(lambda _axes: self._refresh_dims(keep=False))
        host.viewport.annotation_listeners.append(lambda _anns: self._refresh_dims(keep=False))
        host.doc.subscribe(lambda _changed, _removed: self._refresh_dims(keep=False))

    @property
    def accepts_typing(self):
        """Typing goes to the temporary dimension clicked, or is how far a grip moves."""
        return self._active is not None or self._move is not None

    def _refresh_dims(self, keep=True):
        """The selection's temporary dimensions and grips shown again (keep: the dimension clicked stays
        active)."""
        if getattr(self.host, "tool", None) is not self or self._move is not None:
            return
        if not keep:
            self._active = None
        self._hover = None
        relating = bool(self._dims) and any(d.kind == "relation" for d in self._dims)
        self._show_dims()
        if relating != any(d.kind == "relation" for d in self._dims) and hasattr(self.host, "set_hint"):
            self.host.set_hint(self.hint())               # (0.361: a wall's relations shown, or no longer)

    def _show_dims(self):
        """(The dimensions and grips of what is selected now.)"""
        axes = sorted(k for k in self.viewport.selected_axes if k < len(self.doc.grids))
        if axes and not self.viewport.selection:           # grid axes (0.72): their grips and dimensions
            z = self.viewport.grid_level()
            self._dims = grid_dims(self.doc, axes[0], z) if len(axes) == 1 else []
            self.viewport.show_temp_dims(self._dims, active=self._active)
            ends = [(k, w) for k in axes for w in ("start", "end")]
            self._axis_grips = (ends, axes)
            point = lambda k, w: np.array((*getattr(self.doc.grids[k], w), z))          # noqa: E731
            self.viewport.show_grips([point(k, w) for k, w in ends],
                                     [(point(k, "start") + point(k, "end")) / 2 for k in axes])
            return
        self._axis_grips = None
        self._section_grips = None
        if self._section is not None and not self.viewport.selection:   # (0.358) a section's line: its grips
            try:
                self._section_grips = section_grips(self.doc, self.viewport, self._section)
            except (KeyError, ValueError, TypeError, AttributeError, RuntimeError):
                self._section_grips = None
            if self._section_grips is not None:
                _i, a, b, turn = self._section_grips
                self._grip_segments, self._dims = [], []
                self.viewport.show_temp_dims([])
                self.viewport.show_grips([a, b], [turn])
                return
            self._section = None
        self._dim_grips = None
        dims = [d for d in self.viewport.selected_dims if d in self.doc.dimensions]
        if dims and not self.viewport.selection and self.viewport.view_plane() is not None:
            grips = self._string_grips(dims)                # (0.402) a dimension string: its grips, as Revit's
            if grips is not None:
                self._grip_segments, self._dims, self._ann_grips = [], [], []
                self.viewport.show_temp_dims([])
                string, ends, middles, kinds = grips
                self._dim_grips = (string, len(ends), kinds)
                self.viewport.show_grips(ends, middles)
                return
        anns = [a for a in self.viewport.selected_annotations if a in self.doc.annotations]
        if anns and not self.viewport.selection:           # (0.191) drawings in the view: a grip on each point
            self._grip_segments, self._dims = [], []
            self._ann_grips = [(a, k) for a in anns for k in range(len(a.points))]
            self.viewport.show_temp_dims([])
            self.viewport.show_grips([np.asarray(a.points[k], dtype=float) for a, k in self._ann_grips], [])
            return
        self._ann_grips = []
        lines = self.viewport.line_selection
        if lines and not self.viewport.selection:          # (0.373) lines picked alone: their grips (one: its length)
            self._grip_segments, self._cab_grips, self._block_grips = [], None, None
            self._wall_ends = self._door_flips = None
            ends, self._dims = [], []
            for obj_id, ks in lines.items():
                obj = self.doc.get(obj_id)
                if not line_edit.is_lines(obj):
                    continue
                world = [transform_point(obj.matrix, v) for v in obj.mesh.verts]
                for k in sorted(ks):
                    i, j = obj.mesh.lines[k]
                    self._grip_segments.append((world[i], world[j]))
                    ends += [p for p in (world[i], world[j])
                             if all(np.linalg.norm(p - q) > line_edit.TOL for q in ends)]
                    if sum(len(v) for v in lines.values()) == 1:
                        self._dims = [temp_dims.TempDim(world[i], world[j], Z_UP, key=("line", obj_id, i, j))]
            self.viewport.show_temp_dims(self._dims, active=self._active)
            self.viewport.show_grips(ends, [(a + b) / 2 for a, b in self._grip_segments])
            return
        self._curve_grips = None
        ids = self.viewport.selection
        obj = self.doc.get(next(iter(ids))) if len(ids) == 1 else None
        found = curve_edit.grips(obj) if obj is not None and not obj.is_bim and obj.curve else None
        if found is not None:                              # (0.373) a curve alone: its own grips, its tangents' lines
            ends, middles, arrows, what = found
            self._curve_grips = (obj.id, what, len(ends))
            self._grip_segments, self._dims = [], []
            self.viewport.show_temp_dims([])
            self.viewport.show_grips(ends, middles, (), arrows)
            return
        self._dims = selection_dims(self.doc, self.viewport.selection,
                                    faces=bool(getattr(self.host, "dim_faces", False)))
        self.viewport.show_temp_dims(self._dims, active=self._active)
        try:
            self._cab_grips = division_grips(self.doc, self.viewport.selection)
        except (KeyError, ValueError, TypeError, AttributeError, RuntimeError):
            self._cab_grips = None
        if self._cab_grips is not None:                    # (0.244) a cabinet's divisions: a grip on each
            self._grip_segments = []
            self.viewport.show_grips(self._cab_grips[1], [])
            return
        try:
            self._block_grips = block_grips(self.doc, self.viewport.selection)
        except (KeyError, ValueError, TypeError, AttributeError, RuntimeError):
            self._block_grips = None
        if self._block_grips is not None:                  # (0.264) a roof's blocks: its sides', its middles
            self._grip_segments = []
            self.viewport.show_grips([p for _i, _k, p in self._block_grips[3]], self._block_grips[4])
            return
        ends, self._grip_segments = [], []
        for obj in (self.doc.get(i) for i in self.viewport.selection):
            if line_edit.is_lines(obj) and not obj.curve:  # (0.373: a curve's grips are its own, curve_grips)
                for _i, _j, a, b in line_edit.segments(obj):
                    self._grip_segments.append((a, b))
                    ends += [p for p in (a, b) if all(np.linalg.norm(p - q) > line_edit.TOL for q in ends)]
        try:
            self._wall_ends = wall_ends(self.doc, self.viewport.selection)
        except (KeyError, ValueError, TypeError, AttributeError, RuntimeError):
            self._wall_ends = None
        try:
            self._door_flips = door_flips(self.doc, self.viewport.selection) if not self._grip_segments else None
        except (KeyError, ValueError, TypeError, AttributeError, RuntimeError):
            self._door_flips = None
        if self._door_flips is not None:                   # (0.359) a door's flips: their arrows, a grip in each
            self.viewport.show_grips([], [p for _w, p, *_ends in self._door_flips[1]], (), self._door_flips[2])
            return
        self.viewport.show_grips(ends, [(a + b) / 2 for a, b in self._grip_segments],
                                 self._wall_ends[1] if self._wall_ends is not None else ())

    def activate(self):
        super().activate()
        self._refresh_dims(keep=False)

    # ------------------------------------------------------------ grips (0.62): lines changed by their ends

    def _start_axis_move(self, grip, x, y, modifiers):
        kind, k = grip
        ends, middles = self._axis_grips
        if kind == "end":
            index, which = ends[k]
            base = self.viewport.grips[0][k]
        else:
            index, which = middles[k], "middle"
            base = self.viewport.grips[1][k]
        alone = "Ctrl" in (modifiers or ()) or "Control" in (modifiers or ())
        self._move = _AxisMove(index, which, base.copy(), (x, y), alone)
        self.viewport.clear_temp_dims()
        self.host.set_hint(t("hint.grid_grip" if which != "middle" else "hint.grid_move"))

    def _axis_frame(self, move):
        axis = self.doc.grids[move.index]
        d = bim.grid_direction(axis)
        return np.array((d[0], d[1], 0.0)), np.array((-d[1], d[0], 0.0))

    def _axis_to(self, x, y, modifiers=()):
        """Where an axis's grip goes for the mouse at (x, y): an end along the axis, the middle across it —
        from the point the snaps and alignments give."""
        move = self._move
        found, _snap, _hit = infer_point(self.viewport, x, y, move.base, modifiers, plane=level_plane(move.base[2]))
        if found is not None:
            point = found.point.copy()
            tip, marker, _line = inferred_style(found)
        else:
            origin, direction = self.viewport.ray(x, y)
            point = ray_plane(origin, direction, move.base, Z_UP)
            if point is None:
                point = ray_plane(origin, direction, move.base, -Z_UP)
            tip, marker = "", PREVIEW
        if point is None:
            return
        along, across = self._axis_frame(move)
        way = across if move.which == "middle" else along
        move.target = move.base + way * float(np.dot(point - move.base, way))
        self._axis_preview(tip, marker)

    def _axis_ends(self):
        """{index: (start, end)} the axes get from the grip moved to its target."""
        move = self._move
        delta = (move.target - move.base)[:2]
        axes = self.doc.grids
        shifted = lambda p: (p[0] + delta[0], p[1] + delta[1])        # noqa: E731
        if move.which == "middle":
            a = axes[move.index]
            return {move.index: (shifted(a.start), shifted(a.end))}
        out = {}
        moving = [(move.index, move.which)] + ([] if move.alone else bim.aligned_ends(axes, move.index, move.which))
        for k, which in moving:
            a = axes[k]
            out[k] = (shifted(a.start), a.end) if which == "start" else (a.start, shifted(a.end))
        return out

    def _axis_preview(self, tip="", marker=PREVIEW):
        move = self._move
        z = move.base[2]
        segs = [np.array((*p, z)) for start, end in self._axis_ends().values() for p in (start, end)]
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))
        self.viewport.show_temp_dims([temp_dims.TempDim(move.base, move.target, Z_UP)]
                                     if np.linalg.norm(move.target - move.base) > 1e-6 else [])
        self.viewport.show_marker(move.target, marker)
        self.viewport.show_tip(tip, move.target if tip else None)
        self.host.set_vcb(format_length(float(np.linalg.norm(move.target - move.base)), decimal_sep()))

    def _finish_axis_move(self):
        move = self._move
        ends = self._axis_ends() if move.target is not None else {}
        self._move = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
        if ends and np.linalg.norm(move.target - move.base) > 1e-9:
            try:
                bim.move_grid_axes(self.doc, ends)
                d = format_length(float(np.linalg.norm(move.target - move.base)), decimal_sep())
                self.host.message(t("info.grid_moved", d=d, n=len(ends)))
            except ValueError as exc:
                self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
        self._refresh_dims(keep=False)

    def _start_move(self, grip, x, y):
        kind, k = grip
        if kind == "end":
            base = self.viewport.grips[0][k]
            points = [base]
        else:
            a, b = self._grip_segments[k]
            base, points = (a + b) / 2, [a, b]
        flat = all(abs(p[2] - base[2]) < line_edit.TOL for p in points) and all(
            abs(a[2] - b[2]) < line_edit.TOL for a, b in self._grip_segments)
        self._move = _GripMove(base.copy(), [p.copy() for p in points], (x, y),
                               level_plane(base[2]) if flat else None, middle=kind == "middle")
        self.viewport.clear_temp_dims()
        self.host.set_hint(t("hint.grip"))

    def _start_curve_move(self, grip, x, y):
        """(0.373) A curve's grip taken: it follows the mouse on the curve's plane, the curve reshaped as it goes."""
        obj_id, what, n_ends = self._curve_grips
        obj = self.doc.get(obj_id)
        kind, k = grip
        index = k if kind == "end" else n_ends + k
        base = self.viewport.grips[0][k] if kind == "end" else self.viewport.grips[1][k]
        normal = obj.matrix[:3, :3] @ np.asarray(obj.curve["normal"], dtype=float)
        normal = normal / np.linalg.norm(normal)
        self._move = _CurveMove(obj_id, what[index], base.copy(), (x, y), (base.copy(), normal))
        self.viewport.clear_temp_dims()
        self.host.set_hint(t("hint.curve_grip"))

    def _curve_to(self, x, y, modifiers=()):
        move = self._move
        found, _snap, _hit = infer_point(self.viewport, x, y, move.base, modifiers, plane=move.plane)
        if found is not None:
            target = found.point.copy()
            self.viewport.show_alignments(found.lines, target)
            tip, marker, _line = inferred_style(found)
        else:
            self.viewport.show_alignments()
            origin, direction = self.viewport.ray(x, y)
            target = ray_plane(origin, direction, move.plane[0], move.plane[1])
            if target is None:
                target = ray_plane(origin, direction, move.plane[0], -move.plane[1])
            tip, marker = "", PREVIEW
        if target is None:
            return
        move.target = target - float((target - move.plane[0]) @ move.plane[1]) * move.plane[1]
        obj = self.doc.get(move.obj_id)
        curve = curve_edit.dragged(obj, move.what, move.target) if obj is not None else None
        if curve is None:
            return
        pts = [transform_point(obj.matrix, p) for p in core_curves.curve_points(curve)]
        segs = [q for a, b in zip(pts, pts[1:]) for q in (a, b)]
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))
        self.viewport.show_marker(move.target, marker)
        self.viewport.show_tip(tip or (t("info.arc_radius", r=format_length(core_curves.arc_radius(curve),
                                                                            decimal_sep()))
                                       if curve["kind"] == "arc" else ""), move.target)
        self.host.set_vcb(format_length(float(np.linalg.norm(move.target - move.base)), decimal_sep()))

    def _finish_curve_move(self):
        move, self._move = self._move, None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
        obj = self.doc.get(move.obj_id)
        if obj is not None and move.target is not None and np.linalg.norm(move.target - move.base) > 1e-9:
            curve = curve_edit.dragged(obj, move.what, move.target)
            if curve is not None:
                try:
                    curve_edit.reshape(self.doc, obj.id, curve)
                    self.host.message(t("info.curve_reshaped", k=t("curve." + curve["kind"])))
                except ValueError as exc:
                    self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
        self._refresh_dims(keep=False)

    def _flip_at(self, x, y):
        """(0.404) The door's flip arrow under (x, y) — within FLIP_PICK_PX of it on the screen, anywhere along it —:
        its index, or None."""
        best = None
        for k, (_what, _middle, a, b) in enumerate(self._door_flips[1]):
            pa, pb = (np.array(self.viewport.project(p), dtype=float) for p in (a, b))
            ab = pb - pa
            q = np.array((x, y), dtype=float)
            u = float(np.clip((q - pa) @ ab / max(float(ab @ ab), 1e-9), 0.0, 1.0))
            dist = float(np.linalg.norm(pa + ab * u - q))
            if dist <= FLIP_PICK_PX and (best is None or dist < best[0]):
                best = (dist, k)
        return best[1] if best is not None else None

    # ------------------------------------------------------------ (0.402) a dimension string's grips

    def _string_grips(self, dims):
        """(the string, its witness grips (squares), its middles (diamonds): its line's and each value's, what each
        middle is) of the string of the first dimension chosen (a linear one), or None."""
        from ..model import dim_edit
        first = next((d for d in dims if d.vertex is None), None)
        if first is None:
            return None
        string = [d for d in dim_edit.string_of(self.doc, first) if d.vertex is None]
        plane = self.viewport.view_plane()
        origin, u, v, _n = plane
        to3 = lambda q: origin + u * q[0] + v * q[1]           # noqa: E731
        ends = [p for p, _users in dim_edit.witness_points(self.doc, string)]
        lines = []
        for d in string:
            a, b = dims_model.ends(self.doc, d)
            _p1, _p2, l1, l2, _len = dims_model.placed(a, b, dims_model.line_point(self.doc, d), origin, u, v,
                                                       d.direction)
            lines += [l1, l2]
        if not lines:
            return None
        lines = np.array(lines)
        along, _across = dim_edit.line_normal(self.doc, string[0], plane)
        d2 = np.array((float(along @ u), float(along @ v)))
        s = lines @ d2
        lo, hi = lines[int(np.argmin(s))], lines[int(np.argmax(s))]
        # (the line's grip near its start: its middle is a value's)
        middles, kinds = [to3(lo + (hi - lo) * 0.12)], [("line", None)]
        texts = {}
        for centre, _along, _across, _half, owner in getattr(self.viewport, "_dim_texts", ()):
            if owner in string and owner not in texts:
                texts[owner] = centre
        for d in string:
            if d in texts:
                middles.append(texts[d])
                kinds.append(("text", d))
        return string, ends, middles, kinds

    def _start_dim_move(self, grip, x, y):
        string, n_ends, kinds = self._dim_grips
        plane = self.viewport.view_plane()
        paper = (plane[0], plane[3]) if plane is not None else (np.zeros(3), Z_UP)
        if grip[0] == "end":
            base = self.viewport.grips[0][grip[1]].copy()
            self._move = _DimMove("witness", string, grip[1], base, (x, y), paper)
        else:
            kind, dim = kinds[grip[1]]
            base = self.viewport.grips[1][grip[1]].copy()
            self._start_dim_drag(kind, string if kind == "line" else [dim], base, x, y)
            return
        self.host.set_hint(self.hint())

    def _start_dim_drag(self, kind, dims, base, x, y):
        """(0.405) A string's line or a value's text taken (by its grip, or by itself): what it will snap to — the
        other values' middles / the other parallel lines and the usual spacing between rows."""
        from ..model import dim_edit
        plane = self.viewport.view_plane()
        origin, u, v, n = plane
        move = _DimMove(kind, dims, -1, np.asarray(base, dtype=float), (x, y), (origin, n))
        flat = lambda p: np.array((float((p - origin) @ u), float((p - origin) @ v)))     # noqa: E731
        if kind == "text":
            move.mid2 = dim_edit.line_middle(self.doc, dims[0], plane)
            move.others = [flat(c) for c, _a, _b, _h, owner in getattr(self.viewport, "_dim_texts", ())
                           if owner is not dims[0]]
        else:
            along, across = dim_edit.line_normal(self.doc, dims[0], plane)
            move.across = across
            try:
                scale = self.doc.view_settings(self.viewport.current_view()).scale or 100
            except Exception:
                scale = 100
            step = 7.0 * scale / 1000.0                 # (the rows' usual spacing: 7 mm on paper)
            places = []
            mine = {id(d) for d in dims}
            for d in self.doc.dimensions_of(self.viewport.current_view()):
                if id(d) in mine or d.vertex is not None or d.tag == "grid":
                    continue
                o_along, _o_across = dim_edit.line_normal(self.doc, d, plane)
                if abs(float(o_along @ along)) < 0.999:
                    continue
                at = float((dims_model.line_point(self.doc, d) - origin) @ across)
                places += [at, at - step, at + step]
            move.others = places
        self._move = move
        self.host.set_hint(self.hint())

    def _dim_to(self, x, y):
        move = self._move
        base, normal = move.plane
        origin, direction = self.viewport.ray(x, y)
        target = ray_plane(origin, direction, base, normal)
        if target is None:
            target = ray_plane(origin, direction, base, -normal)
        if target is None:
            return
        move.target, move.ref = target, None
        if move.kind in ("text", "line"):
            self._dim_snap(move)
            return
        segs = [move.base, target]
        tip = ""
        if move.kind == "witness":                        # (to the reference under the mouse, parallel to the others)
            tool = self.host.tools.get("dimension") if hasattr(self.host, "tools") else None
            found = tool.references_at(x, y) if tool is not None else []
            from ..model import dim_edit
            plane = self.viewport.view_plane()
            along, _across = dim_edit.line_normal(self.doc, move.dims[0], plane)
            for ref in found:
                if ref.along is None or abs(float(ref.along @ along)) < 0.02:
                    move.ref, move.target = ref, ref.point.copy()
                    tip = ref.what
                    if ref.seg is not None:
                        segs += list(ref.seg)
                    break
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))
        self.viewport.show_marker(move.target)
        self.viewport.show_tip(tip, move.target if tip else None)

    def _chosen_dim_at(self, x, y):
        """(0.405) A part of the chosen string under (x, y): ("text", its dimension, its value's middle) or ("line",
        None, the point), or None."""
        string = self._dim_grips[0]
        plane = self.viewport.view_plane()
        if plane is None:
            return None
        origin, _u, _v, n = plane
        ray_o, ray_d = self.viewport.ray(x, y)
        p = ray_plane(ray_o, ray_d, origin, n)
        if p is None:
            p = ray_plane(ray_o, ray_d, origin, -n)
        if p is None:
            return None
        for centre, along, across, (hw, hh), owner in getattr(self.viewport, "_dim_texts", ()):
            if owner in string and abs(float((p - centre) @ along)) <= hw and abs(float((p - centre) @ across)) <= hh:
                return "text", owner, np.asarray(centre, dtype=float)
        if self.viewport.dimension_at(x, y) in string:
            return "line", None, p
        return None

    def _dim_snap(self, move):
        """(0.405) A value or a string's line where the mouse is, snapped — a value lined up with the other values
        (level or upright) or back over its line's middle; a line on another parallel line's place, or the usual
        spacing from it — with its guides drawn, and the value's box or the line where they will go."""
        plane = self.viewport.view_plane()
        origin, u, v, _n = plane
        to3 = lambda q: origin + u * q[0] + v * q[1]                # noqa: E731
        tol = DIM_SNAP_PX * self.viewport.world_per_pixel(move.target)
        segs, guides, tip = [], [], ""
        if move.kind == "text":
            p = np.array((float((move.target - origin) @ u), float((move.target - origin) @ v)))
            near_x = min(move.others + [move.mid2], key=lambda q: abs(q[0] - p[0]), default=None)
            near_y = min(move.others + [move.mid2], key=lambda q: abs(q[1] - p[1]), default=None)
            if near_x is not None and abs(near_x[0] - p[0]) < tol:
                p[0] = near_x[0]
                guides += [to3(near_x), to3(p)]
            if near_y is not None and abs(near_y[1] - p[1]) < tol:
                p[1] = near_y[1]
                guides += [to3(near_y), to3(p)]
            move.target = to3(p)
            tip = t("snap.dim_value") if guides else ""
            box = next(((a, b, h) for _c, a, b, h, owner in getattr(self.viewport, "_dim_texts", ())
                        if owner is move.dims[0]), None)
            if box is not None:                          # (the value's box where it will go)
                a, b, (hw, hh) = box
                c = move.target
                corners = [c - a * hw - b * hh, c + a * hw - b * hh, c + a * hw + b * hh, c - a * hw + b * hh]
                segs += [q for k in range(4) for q in (corners[k], corners[(k + 1) % 4])]
        else:
            at = float((move.target - origin) @ move.across)
            best = min(move.others, key=lambda o: abs(o - at), default=None)
            if best is not None and abs(best - at) < tol:
                move.target = move.target + move.across * (best - at)
                tip = t("snap.dim_line")
            shift = move.across * float((move.target - move.base) @ move.across)
            for d in move.dims:                          # (the string's line where it will go)
                a, b = dims_model.ends(self.doc, d)
                _p1, _p2, l1, l2, _len = dims_model.placed(a, b, dims_model.line_point(self.doc, d), origin, u, v,
                                                           d.direction)
                segs += [to3(l1) + shift, to3(l2) + shift]
        self.viewport.show_polygon([], segments=segs + guides,
                                   colors=[PREVIEW] * len(segs) + [DIM_GUIDE] * len(guides))
        self.viewport.show_marker(move.target)
        self.viewport.show_tip(tip, move.target if tip else None)

    def _finish_dim_move(self):
        from ..model import dim_edit, dim_refs
        move, self._move = self._move, None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        if move.target is None or np.linalg.norm(move.target - move.base) < 1e-6:
            self._refresh_dims(keep=False)
            return
        plane = self.viewport.view_plane()
        delta = move.target - move.base
        if move.kind == "line":
            dim_edit.move_line(self.doc, move.dims, delta, plane, t("cmd.dim_move_line"))
            self.host.message(t("info.dim_line_moved"))
        elif move.kind == "text":
            origin, u, v, _n = plane                     # (0.405: its middle where it was dropped, from its line's)
            p = np.array((float((move.target - origin) @ u), float((move.target - origin) @ v)))
            shift = p - move.mid2
            dim_edit.move_text(self.doc, move.dims[0], (float(shift[0]), float(shift[1])), t("cmd.dim_move_text"))
            self.host.message(t("info.dim_text_moved"))
        else:
            ref = move.ref
            hung = dim_refs.hang(self.doc, ref.guid, ref.point, ref.kind) if ref is not None and ref.guid else None
            if dim_edit.move_witness(self.doc, move.dims, move.index, move.target, hung, t("cmd.dim_move_witness")):
                self.host.message(t("info.dim_witness_moved", w=ref.what if ref is not None else t("dimref.point")))
        self.viewport.select_dimensions({d for d in self.viewport.selected_dims if d in self.doc.dimensions})
        self._refresh_dims(keep=False)

    def _edit_value(self, dim):
        """(0.402, as Revit's) A dimension hung on the element selected: its value, typed, moves that element."""
        ends = [r[0] if r is not None else None for r in dim.refs]
        chosen = [g for g in ends if g is not None and g in self.viewport.selection]
        if not chosen or not hasattr(self.host, "edit_dimension_value"):
            return False
        self.host.edit_dimension_value(dim, chosen[0])
        return True

    def witness_at(self, x, y):
        """(0.402) The witness grip of the dimension string chosen under (x, y): its index, or None."""
        if self._dim_grips is None:
            return None
        grip = self.viewport.grip_at(x, y, radius_px=12)
        return grip[1] if grip is not None and grip[0] == "end" else None

    def _start_ann_move(self, grip, x, y):
        """(0.191) A drawing's grip taken: its point follows the mouse on the view's paper."""
        ann, index = self._ann_grips[grip[1]]
        plane = self.viewport.view_plane()
        base = np.asarray(ann.points[index], dtype=float)
        self._move = _AnnMove(ann, index, base.copy(), (x, y), (base, plane[3] if plane is not None else Z_UP))
        self.viewport.clear_temp_dims()
        self.host.set_hint(t("hint.ann_grip"))

    def _ann_points(self):
        move = self._move
        points = [np.asarray(p, dtype=float) for p in move.ann.points]
        points[move.index] = move.target.copy()
        return points

    def _preview_ann(self, tip="", marker=PREVIEW):
        """The drawing as it would be, its point where the mouse is."""
        move = self._move
        plane = self.viewport.view_plane()
        if plane is None:
            return
        origin, u, v, _n = plane
        moved = notes2d.Annotation(move.ann.view, move.ann.kind, self._ann_points(), move.ann.text, move.ann.hatch,
                                   move.ann.size, dict(move.ann.extra))
        segs = [origin + u * q[0] + v * q[1] for s in notes2d.segments(moved, origin, u, v) for q in s]
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))
        self.viewport.show_temp_dims([temp_dims.TempDim(move.base, move.target, -move.plane[1])]
                                     if np.linalg.norm(move.target - move.base) > 1e-6 else [])
        self.viewport.show_marker(move.target, marker)
        self.viewport.show_tip(tip, move.target if tip else None)
        self.host.set_vcb(format_length(float(np.linalg.norm(move.target - move.base)), decimal_sep()))

    def _finish_ann_move(self):
        move, self._move = self._move, None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
        if move.target is not None and np.linalg.norm(move.target - move.base) > 1e-9 and \
                move.ann in self.doc.annotations:
            self._move = move                                 # (_ann_points reads it)
            points = self._ann_points()
            self._move = None
            self.doc.execute(notes2d.EditAnnotation(move.ann, t("cmd.draft_edit"), points=points))
            self.host.message(t("info.ann_grip", d=format_length(float(np.linalg.norm(move.target - move.base)),
                                                                 decimal_sep())))
        self._refresh_dims(keep=False)

    def _start_division_move(self, grip, x, y):
        """(0.244) A cabinet's division's grip taken: it slides along the cabinet's width, between its neighbours."""
        from ..core import cabinets as core_cab
        guid, points, x_dir, c = self._cab_grips
        k = grip[1]
        t_ = core_cab.BOARD
        mids = c.divisions
        left = (mids[k - 1] + t_ / 2) if k > 0 else t_
        right = (mids[k + 1] - t_ / 2) if k + 1 < len(mids) else c.width - t_
        lo = left + core_cab.MIN_COMPARTMENT + t_ / 2 - mids[k]
        hi = right - core_cab.MIN_COMPARTMENT - t_ / 2 - mids[k]
        self._move = _DivisionMove(guid, k, points[k].copy(), x_dir, min(lo, 0.0), max(hi, 0.0), c.height, (x, y))
        self.viewport.clear_temp_dims()
        self.host.set_hint(t("hint.cab_division"))

    def _division_to(self, x, y):
        move = self._move
        origin, ray = self.viewport.ray(x, y)
        s = closest_on_line_to_ray(origin, ray, move.base, move.x_dir)
        if s is None:
            return
        move.target = move.base + move.x_dir * min(max(float(s), move.lo), move.hi)
        half = Z_UP * move.height / 2
        self.viewport.show_polygon([], segments=[move.target - half, move.target + half], colors=[PREVIEW] * 2)
        self.viewport.show_temp_dims([temp_dims.TempDim(move.base, move.target, Z_UP)]
                                     if np.linalg.norm(move.target - move.base) > 1e-6 else [])
        self.host.set_vcb(format_length(float(np.linalg.norm(move.target - move.base)), decimal_sep()))

    def _finish_division_move(self):
        move, self._move = self._move, None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
        if move.target is not None:
            s = min(max(float(np.dot(move.target - move.base, move.x_dir)), move.lo), move.hi)
            if abs(s) > 1e-6:
                c = self._cab_grips[3]
                mids = list(c.divisions)
                mids[move.index] = round(mids[move.index] + s, 3)
                try:
                    bim.set_cabinet(self.doc, move.guid, splits=",".join("{:g}".format(v) for v in mids))
                    spans = self.doc.ifc.cabinet_params(move.guid).compartment_spans()
                    a, b = spans[move.index], spans[move.index + 1]
                    self.host.message(t("info.cab_division", a=format_length(a[1] - a[0], decimal_sep()),
                                        b=format_length(b[1] - b[0], decimal_sep())))
                except ValueError as exc:
                    self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
        self._refresh_dims(keep=False)

    def _start_block_move(self, grip, x, y):
        """(0.264) A roof block's grip taken: a side's goes out or in along the block, its middle's moves it."""
        guid, blocks, level, sides, middles = self._block_grips
        kind, k = grip
        if kind == "end":
            i, side, point = sides[k]
            out, _half = core_blocks.side_way(blocks[i], side)
            size = blocks[i].depth if side in (0, 2) else blocks[i].width
            self._move = _BlockMove(guid, i, side, point.copy(), np.array((out[0], out[1], 0.0)),
                                    min(core_blocks.MIN_SIZE - size, 0.0), level, (x, y))
        else:
            self._move = _BlockMove(guid, k, -1, middles[k].copy(), None, 0.0, level, (x, y))
        self.viewport.clear_temp_dims()
        self.host.set_hint(self.hint())

    def _block_to(self, x, y, modifiers=()):
        """Where a block's grip goes for the mouse at (x, y): the point the snaps and alignments give (a wall's
        face, another block's corner…) — for a side, along the block only."""
        move = self._move
        found, _snap, _hit = infer_point(self.viewport, x, y, move.base, modifiers, plane=level_plane(move.base[2]))
        if found is not None:
            point = found.point.copy()
            self.viewport.show_alignments(found.lines, point)
            tip, marker, _line = inferred_style(found)
        else:
            self.viewport.show_alignments()
            origin, direction = self.viewport.ray(x, y)
            point = ray_plane(origin, direction, move.base, Z_UP)
            if point is None:
                point = ray_plane(origin, direction, move.base, -Z_UP)
            tip, marker = "", PREVIEW
        if point is None:
            return
        if move.way is not None:
            move.target = move.base + move.way * max(float(np.dot(point - move.base, move.way)), move.shortest)
        else:
            move.target = np.array((point[0], point[1], move.base[2]))
        block = self._moved_block(move)
        corners = [np.array((cx, cy, move.level)) for cx, cy in core_blocks.rect(block)]
        segs = [p for k in range(4) for p in (corners[k], corners[(k + 1) % 4])]
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))
        self.viewport.show_temp_dims([temp_dims.TempDim(move.base, move.target, Z_UP)]
                                     if np.linalg.norm(move.target - move.base) > 1e-6 else [])
        self.viewport.show_marker(move.target, marker)
        self.viewport.show_tip(tip, move.target if tip else None)
        self.host.set_vcb(format_length(float(np.linalg.norm(move.target - move.base)), decimal_sep()))

    def _moved_block(self, move):
        """The block as the grip moved to its target puts it (in the plan)."""
        b = self._block_grips[1][move.index]
        d = move.target - move.base
        if move.side >= 0:
            return core_blocks.stretched(b, move.side, max(float(np.dot(d, move.way)), move.shortest))
        return core_blocks.replace(b, cx=b.cx + float(d[0]), cy=b.cy + float(d[1]))

    def _finish_block_move(self):
        move, self._move = self._move, None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
        if move.target is not None and np.linalg.norm(move.target - move.base) > 1e-9 and \
                self._block_grips is not None:
            block = self._moved_block(move)
            if move.side >= 0:                            # (put on a wall: out to its outer face, as drawn)
                block = bim.fit_block_to_walls(self.doc, block, only=(move.side,))
            blocks = list(self._block_grips[1])
            blocks[move.index] = block
            d = format_length(float(np.linalg.norm(move.target - move.base)), decimal_sep())
            try:
                bim.set_roof_blocks(self.doc, move.guid, blocks, world=True)
                self.host.message(t("info.roof_block_side" if move.side >= 0 else "info.roof_block_moved", d=d,
                                    n=move.index + 1))
            except ValueError as exc:
                self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
        self._refresh_dims(keep=False)

    def _section_to(self, x, y):
        """(0.358) A section's end where the mouse is, along its line (at least 20 cm from its other end)."""
        move = self._move
        plane = self.viewport.view_plane()
        if plane is None:
            return
        origin, _u, _v, normal = plane
        ray_o, ray_d = self.viewport.ray(x, y)
        p = ray_plane(ray_o, ray_d, origin, normal)
        if p is None:
            p = ray_plane(ray_o, ray_d, origin, -normal)
        if p is None:
            return
        line = move.b - move.a
        length = float(np.linalg.norm(line))
        d = line / max(length, 1e-12)
        s = float((p - move.a) @ d)
        s = min(s, length - 0.2) if move.end == 0 else max(s, 0.2)
        move.target = move.a + d * s
        a, b = (move.target, move.b) if move.end == 0 else (move.a, move.target)
        self.viewport.show_lines([a, b], [PREVIEW, PREVIEW])
        self.viewport.show_marker(move.target, PREVIEW)
        self.host.set_vcb(format_length(float(np.linalg.norm(b - a)), decimal_sep()))

    def _finish_section_move(self):
        move, self._move = self._move, None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
        if move.target is not None and np.linalg.norm(move.target - move.base) > 1e-6:
            origin, u, v, _n = self.viewport.view_plane()
            flat = lambda p: (float((p - origin) @ u), float((p - origin) @ v))      # noqa: E731
            a, b = (move.target, move.b) if move.end == 0 else (move.a, move.target)
            self.doc.set_section_ends(move.index, flat(a), flat(b))
            self.host.message(t("info.section_ends", l=format_length(float(np.linalg.norm(b - a)), decimal_sep())))
        self._refresh_dims(keep=False)

    def _move_to(self, x, y, modifiers=()):
        """Where the grip goes for the mouse at (x, y): the snaps and alignments from where it was."""
        if isinstance(self._move, _SectionMove):
            self._section_to(x, y)
            return
        if isinstance(self._move, _DivisionMove):
            self._division_to(x, y)
            return
        if isinstance(self._move, _BlockMove):
            self._block_to(x, y, modifiers)
            return
        if isinstance(self._move, _AxisMove):
            self._axis_to(x, y, modifiers)
            return
        if isinstance(self._move, _CurveMove):
            self._curve_to(x, y, modifiers)
            return
        if isinstance(self._move, _DimMove):             # (0.402)
            self._dim_to(x, y)
            return
        move = self._move
        found, _snap, _hit = infer_point(self.viewport, x, y, move.base, modifiers, plane=move.plane)
        if found is not None:
            target = found.point.copy()
            self.viewport.show_alignments(found.lines, target)
            tip, marker, _line = inferred_style(found)
        else:
            self.viewport.show_alignments()
            origin, direction = self.viewport.ray(x, y)
            normal = move.plane[1] if move.plane is not None else default_normal(direction)
            target = ray_plane(origin, direction, move.base, normal)
            if target is None:
                target = ray_plane(origin, direction, move.base, -normal)
            tip, marker = "", PREVIEW
        if target is None:
            return
        if isinstance(move, _AnnMove):                    # (0.191) kept on the view's paper
            base, normal = move.plane
            move.target = target - normal * float(np.dot(target - base, normal))
            self._preview_ann(tip, marker)
            return
        move.target = target
        self._preview_move(tip, marker)

    def _moves(self):
        move = self._move
        delta = move.target - move.base
        return [(p, p + delta) for p in move.points]

    def _preview_move(self, tip="", marker=PREVIEW):
        move = self._move
        _found, touched = line_edit.moved_lines(self.doc, self._moves())
        segs = [p for seg in touched for p in seg]
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))
        self.viewport.show_temp_dims([temp_dims.TempDim(a, b, Z_UP) for a, b in touched[:8]])
        self.viewport.show_marker(move.target, marker)
        self.viewport.show_tip(tip, move.target if tip else None)
        self.host.set_vcb(format_length(float(np.linalg.norm(move.target - move.base)), decimal_sep()))

    def _finish_move(self):
        if isinstance(self._move, _SectionMove):
            self._finish_section_move()
            return
        if isinstance(self._move, _DivisionMove):
            self._finish_division_move()
            return
        if isinstance(self._move, _BlockMove):
            self._finish_block_move()
            return
        if isinstance(self._move, _AxisMove):
            self._finish_axis_move()
            return
        if isinstance(self._move, _AnnMove):
            self._finish_ann_move()
            return
        if isinstance(self._move, _CurveMove):
            self._finish_curve_move()
            return
        if isinstance(self._move, _DimMove):             # (0.402)
            self._finish_dim_move()
            return
        move, self._move = self._move, None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")
        alone = dict(self.viewport.line_selection)       # (0.373: lines picked alone stay picked — their numbers hold)
        if move is not None and move.target is not None and np.linalg.norm(move.target - move.base) > 1e-9:
            try:
                n = line_edit.move_points(self.doc, [(p, p + move.target - move.base) for p in move.points])
                d = format_length(float(np.linalg.norm(move.target - move.base)), decimal_sep())
                self.host.message(t("info.grip_moved_joined" if n > 1 else "info.grip_moved", d=d))
            except ValueError as exc:
                self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
        if alone and alone != self.viewport.line_selection:
            self.viewport.select_lines({k: v for k, v in alone.items() if self.doc.get(k) is not None})
        self._refresh_dims(keep=False)

    def typed(self, text):
        if self._move is not None:                        # how far the grip goes, the way the mouse shows
            values = parse_lengths(text, 1)
            move = self._move
            d = (move.target - move.base) if move.target is not None else None
            if values is None or values[0] is None or d is None or np.linalg.norm(d) < 1e-9:
                self.host.message(t("err.bad_value", t=text) if values is None else t("hint.grip"), warning=True)
                return
            move.target = move.base + d / np.linalg.norm(d) * values[0]
            self._finish_move()
            return
        dim, self._active = self._active, None
        if dim is None:
            return
        values = parse_lengths(text, 1)
        if values is None or values[0] is None or values[0] <= 0:
            self.host.message(t("err.bad_value", t=text), warning=True)
            self._refresh_dims(keep=False)
            return
        alone = dict(self.viewport.line_selection)        # (0.373: a line picked alone stays picked)
        try:
            apply_dim(self.doc, dim, values[0])
            self.host.message(t("info.temp_dim", v=format_length(values[0], decimal_sep())))
        except ValueError as exc:
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
        if alone and alone != self.viewport.line_selection:
            self.viewport.select_lines({k: v for k, v in alone.items() if self.doc.get(k) is not None})
        self.host.set_vcb("")                             # (the old value no longer applies)
        self.host.set_hint(self.hint())
        self._refresh_dims(keep=False)

    def _drag_box(self, x, y):
        axis, side, start = self._box_drag
        direction = np.eye(3)[axis]
        origin, ray = self.viewport.ray(x, y)
        s = closest_on_line_to_ray(origin, ray, start, direction)
        if s is not None:
            self.viewport.move_box_face(axis, side, start[axis] + s)

    def pointer_move(self, x, y, modifiers):
        if self._box_drag is not None:
            self._drag_box(x, y)
        elif self._move is not None:
            self._move_to(x, y, modifiers)
        elif self._picking is not None:
            if self._picking[1]:
                self._show_picking(x, y)
        elif self._press is not None:                     # the button held: a box / lasso being drawn
            start = self._press[:2]
            if self._region is None and not moved_enough(start, (x, y)):
                return
            if self._region is None or self.drag_shape != "lasso":
                self._region = [start, (float(x), float(y))]
            else:
                self._region.append((float(x), float(y)))
            region, mode = self._region_points()
            self.viewport.show_region(region, mode)
        elif self._dims:
            self._hover_dim(x, y)

    def _hover_dim(self, x, y):
        """(0.361) The temporary dimension under the mouse — its value (click: type over it) or a relation's line
        (click: axes ⇄ faces) — drawn strong, as the addon does."""
        dim = self.viewport.temp_dim_at(x, y) or self.viewport.temp_dim_line_at(x, y)
        if dim is not self._hover:
            self._hover = dim
            self.viewport.show_temp_dims(self._dims, active=self._active, hover=dim)

    def typing(self, text):
        """(0.361) What is being typed (the measurements box), shown in the value of the dimension clicked."""
        if self._active is not None and self._move is None:
            self.viewport.show_temp_dims(self._dims, active=self._active, hover=self._hover, typed=text)

    def pointer_up(self, x, y, button, modifiers):
        if self._press is not None and button == LEFT:    # a click, or the end of a box / lasso (0.75)
            press, self._press = self._press, None
            if self._region is None:
                self._click_select(press[0], press[1], press[2])
                return
            if self.drag_shape == "lasso":
                self._region.append((float(x), float(y)))
            else:
                self._region[-1] = (float(x), float(y))
            region, mode = self._region_points()
            if self.drag_shape == "lasso":
                region = rs.thin_path(region)
            self._region = None
            self.viewport.show_region()
            self._apply_region(region, mode, press[2])
            return
        if self._move is not None and button == LEFT and self._move.dragging:
            if moved_enough(self._move.press, (x, y)):
                self._move_to(x, y, modifiers)
                self._finish_move()                       # dragged: done
            elif isinstance(self._move, _DimMove):
                # (0.405) a dimension's grips move only dragged; a click on a value chosen: twice — its words
                move, self._move = self._move, None
                self.viewport.clear_overlays()
                self.host.set_hint(self.hint())
                now = time.monotonic()
                again = self._dim_click is not None and now - self._dim_click[1] < 0.45 and \
                    bool(self._dim_click[0] & set(move.dims))
                self._dim_click = (set(self._dim_grips[0]) if self._dim_grips else set(move.dims), now)
                if again and move.kind == "text" and hasattr(self.host, "edit_dimension_text"):
                    self.host.edit_dimension_text(move.dims[0])
                self._refresh_dims(keep=False)
            elif isinstance(self._move, _GripMove) and self._move.middle:
                press, self._move = self._move.press, None   # (0.373) a line's middle clicked: that line picked
                self.viewport.clear_overlays()
                self.host.set_hint(self.hint())
                self._click_select(press[0], press[1], modifiers)
            elif isinstance(self._move, _BlockMove):
                # (0.382) a roof block's grip moves only dragged: a click moves nothing (a click more where the mouse
                # was used to pick it up, to follow the mouse until the next click — the owner's wall profile curves)
                self.cancel()
            else:
                self._move.dragging = False               # clicked: the grip follows the mouse to the next click
            return
        if self._box_drag is None or button != LEFT:
            return
        self._drag_box(x, y)
        lo, hi = self.viewport.box
        size = " × ".join(format_length(float(v), decimal_sep()) for v in hi - lo)
        self._box_drag = None
        if hasattr(self.host, "box_changed"):
            self.host.box_changed()                       # (the 3D view's box, kept with the project)
        self.host.message(t("info.box", size=size))

    def hint(self):
        spec = getattr(self.host, "pending_classify", None)
        if spec is not None:
            return t("hint.classify_pick", type=spec.name_pt if lang() == "pt" else spec.name_en)
        if self._asked() and self._picking is None and self._move is None:
            return self.host.pick_request.what                   # (0.322) what the command waiting asks for
        if isinstance(self._move, _AxisMove):
            return t("hint.grid_move" if self._move.which == "middle" else "hint.grid_grip")
        if isinstance(self._move, _AnnMove):
            return t("hint.ann_grip")
        if isinstance(self._move, _DimMove):
            return t("hint.dim_grip_" + self._move.kind)
        if self._dim_grips is not None and self._move is None:
            return t("hint.dim_chosen")
        if isinstance(self._move, _CurveMove):
            return t("hint.curve_grip")
        if isinstance(self._move, _DivisionMove):
            return t("hint.cab_division")
        if isinstance(self._move, _BlockMove):
            return t("hint.roof_block_side" if self._move.side >= 0 else "hint.roof_block_move")
        if self._move is not None:
            return t("hint.grip")
        if self._active is not None:
            return t("hint.temp_dim")
        if self._picking is None and any(d.kind == "relation" for d in self._dims):     # (0.361) a wall's relations
            return t("hint.wall_dims_faces" if getattr(self.host, "dim_faces", False) else "hint.wall_dims_axes")
        if self._picking is not None:
            return t("hint.select_" + self._picking[0])
        return t("hint.select_lasso" if self.drag_shape == "lasso" else "hint.select")

    def tab(self):
        """(0.354) TAB: the quick edit of what is chosen, beside it over the view (ui/quick_edit.py) — or closed."""
        quick = getattr(self.host, "quick_edit", None)
        return bool(quick()) if callable(quick) else False

    def _object_at(self, x, y):
        """A face under the cursor, else a line (or edge) the cursor is close to."""
        obj_id = self.viewport.pick_object(x, y)
        if obj_id is None:
            snap, _hit = self.viewport.snap(x, y)    # thin lines are hard to hit: use the inference
            if snap is not None and snap.kind in (ENDPOINT, MIDPOINT, ON_EDGE) and snap.obj_id is not None:
                obj_id = snap.obj_id
        if obj_id is None and self.viewport.plan:      # (a pipe / duct above the plan's cut: its dashed outline)
            obj_id = self.viewport.services_at(x, y)
        obj = self.doc.get(obj_id)
        return obj_id if obj is not None and self.viewport.selectable(obj) else None   # (0.76: its category may not be)

    def _clicked(self, obj_id):
        """What a click on `obj_id` selects: its whole group copy; clicking again
        inside the selected group picks just that element (to change it — in
        every copy of the group)."""
        obj = self.doc.get(obj_id)
        members = bim.group_members_of(self.doc, obj_id) if obj is not None and obj.is_bim else None
        if not members:
            return {obj_id}
        current = self.viewport.selection
        if current == set(members) or current == {obj_id}:
            return {obj_id}
        return set(members)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT and self._picking is not None:     # the right button ends a polygon / fence
            self.enter()
            return
        if button == RIGHT and self._asked() and self._move is None:    # (0.322) as Enter: the command goes on
            self.host.finish_pick()
            return
        if button == RIGHT and self._move is None and hasattr(self.host, "selection_menu"):
            self.host.selection_menu(x, y)                    # select alike, filters (0.76)
            return
        if button != LEFT:
            return
        if self._picking is not None:                     # a polygon / fence being clicked: one more point
            self._pick_point(x, y)
            return
        if self._move is not None:                        # a grip clicked before: this click puts it down
            self._move_to(x, y, modifiers)
            self._finish_move()
            return
        handle = self.viewport.box_handle_at(x, y)        # a handle of the section box: drag that face
        if handle is not None:
            self._box_drag = (*handle, self.viewport.box_handle_point(*handle).copy())
            return
        grip = self.viewport.grip_at(x, y)                # a grip of the lines / grid axes selected: move it
        if grip is None and self._door_flips is not None:
            k = self._flip_at(x, y)                       # (0.404) anywhere along a door's arrow, not its dot only
            grip = ("middle", k) if k is not None else None
        again = self._again_on_line(x, y)
        if grip is not None and again:
            grip = None                                   # (0.373: a double click on a line, not its middle's grip)
        if grip is not None:
            if grip[0] == "add":                          # (0.353) a wall's «+»: go on drawing it from that end
                if self._wall_ends is not None and hasattr(self.host, "continue_wall"):
                    self.host.continue_wall(self._wall_ends[0], grip[1])
            elif self._door_flips is not None and grip[0] == "middle":   # (0.359) a door's flip arrow
                guid, flips, _segs = self._door_flips
                what = flips[grip[1]][0]
                bim.flip_door(self.doc, guid, hinge=what == "hinge", side=what == "side")
                self.host.message(t("info.door_flipped_" + what))
            elif self._section_grips is not None:         # (0.358) a section's end, or its «turn»
                if grip[0] == "middle":
                    self.doc.flip_section(self._section_grips[0])
                    self.host.message(t("info.section_flipped", v=self._section))
                else:
                    index, a, b, _turn = self._section_grips
                    self._move = _SectionMove(index, grip[1], a.copy(), b.copy(), (a, b)[grip[1]].copy(), (x, y))
                    self.viewport.clear_temp_dims()
                    self.host.set_hint(self.hint())
            elif self._cab_grips is not None and grip[0] == "end":    # (0.244) a cabinet's division
                self._start_division_move(grip, x, y)
            elif self._block_grips is not None:                    # (0.264) a roof block's side or middle
                self._start_block_move(grip, x, y)
            elif self._axis_grips is not None:
                self._start_axis_move(grip, x, y, modifiers)
            elif self._dim_grips is not None:             # (0.402) a dimension string's line, value or witness
                self._start_dim_move(grip, x, y)
            elif self._ann_grips and grip[0] == "end":    # (0.191) a drawing's point
                self._start_ann_move(grip, x, y)
            elif self._curve_grips is not None:           # (0.373) a curve's end, middle, point or tangent
                self._start_curve_move(grip, x, y)
            else:
                self._start_move(grip, x, y)
            return
        part = self._chosen_dim_at(x, y) if self._dim_grips is not None and not again else None
        if part is not None:                              # (0.405) a chosen string's value or line, taken itself
            kind, owner, base = part
            self._start_dim_drag(kind, [owner] if kind == "text" else list(self._dim_grips[0]), base, x, y)
            return
        if self._section is not None:                     # (0.358) a click elsewhere: the section let go
            self._section = None
            self._refresh_dims(keep=False)
        # a temporary dimension's value: type over it — (0.392) not on a double click on a line, whose length's box,
        # laid toward it, can reach the point clicked
        dim = self.viewport.temp_dim_at(x, y) if not again else None
        if dim is not None:
            self._active = dim
            self.viewport.show_temp_dims(self._dims, active=dim)
            self.host.set_vcb(format_length(dim.value, decimal_sep()))
            self.host.set_hint(self.hint())
            return
        if not self._asked() and hasattr(self.host, "set_dim_faces") and \
                self.viewport.temp_dim_line_at(x, y) is not None:
            self._active = None                           # (0.361) a relation's line: from axes to faces, and back
            self.host.set_dim_faces(not self.host.dim_faces)
            return
        if self._active is not None:
            self._active = None
            self.host.set_hint(self.hint())
        if self._open_mark(x, y):                         # a section's / an elevation's head (0.121)
            return
        asked = self._asked()                             # (0.322: a command waiting picks elements only)
        dim = self.viewport.dimension_at(x, y) if not asked else None   # a dimension of the view shown
        if dim is not None and self.viewport.selection and self._edit_value(dim):
            return                                        # (0.402) an element's dimension: its value typed moves it
        if dim is not None:
            from ..model import dim_edit
            whole = set(dim_edit.string_of(self.doc, dim))    # (0.402: its whole string, as Revit's)
            now = time.monotonic()
            again = self._dim_click is not None and self._dim_click[0] & whole and now - self._dim_click[1] < 0.45
            self._dim_click = (whole, now)
            if again and hasattr(self.host, "edit_dimension_text"):
                self.host.edit_dimension_text(dim)       # (a double click on it: its words, its value)
                return
            self.viewport.set_selection(set())
            if self.viewport.selected_annotations:
                self.viewport.select_annotations(set())
            picked = self.viewport.selected_dims ^ whole if "Shift" in (modifiers or ()) else whole
            self.viewport.select_dimensions(picked)
            return
        ann = self.viewport.annotation_at(x, y) if not asked else None  # a line, region or text drawn (0.120)
        if ann is not None:
            self.viewport.set_selection(set())
            if self.viewport.selected_dims:
                self.viewport.select_dimensions(set())
            picked = self.viewport.selected_annotations ^ {ann} if "Shift" in (modifiers or ()) else {ann}
            self.viewport.select_annotations(picked)
            self.host.message(t("info.annotation_selected", k=t("draft." + ann.kind).lower(), n=len(picked)))
            return
        # a click selects when the button comes up; dragged, it draws a box / lasso (0.75)
        self._press = (float(x), float(y), tuple(modifiers or ()))
        self._region = None

    def _open_mark(self, x, y):
        """In a plan, a click on a section's or an elevation's head says what it is; a second one at once (a
        double click) opens that view, as Revit's. True if it was a head."""
        ref = self.viewport.mark_at(x, y) if self.viewport.current_view() is not None else None
        if ref is None:
            return False
        now = time.monotonic()
        last, self._mark_click = getattr(self, "_mark_click", None), (ref, now)
        kind, name = ref
        detail = self.doc.detail(name) if kind == "detail" else None
        label = name if kind == "section" else detail.name if detail is not None else \
            t("tree.elevation_title", side=t("tree.elevation." + name))
        if last is None or last[0] != ref or now - last[1] > DOUBLE_CLICK_S:
            if kind == "section" and self.viewport.plan:   # (0.358) chosen: its ends' grips and its «turn»
                self.viewport.set_selection(set())
                self._section = name
                self._refresh_dims(keep=False)
                self.host.message(t("info.section_chosen", v=label))
                return True
            self.host.message(t("info.detail_head" if detail is not None else "info.mark_head", v=label))
            return True
        self._mark_click = None
        if detail is not None:                            # (a detail's callout, 0.133: its piece fills the view)
            origin, u, v, _n = self.viewport.view_plane()
            x0, y0, x1, y1 = detail.rect
            a = self.viewport.project(origin + u * x0 + v * y0)
            b = self.viewport.project(origin + u * x1 + v * y1)
            self.viewport.zoom_to_region(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
        elif kind == "section":
            index = next((k for k, s in enumerate(self.doc.sections) if s.name == name), None)
            if index is not None:
                self.host.open_view("section", index)
        elif kind == "elevation":
            self.host.open_view("elevation", name)
        return True

    # ------------------------------------------------------------ clicks and regions (0.75)

    def _asked(self):
        """(0.322) A command is waiting for elements to be picked (the window's pick request)."""
        return getattr(self.host, "pick_request", None) is not None

    def _combine(self, current, picked, modifiers, region=False):
        """Shift: picked ones in / out; Ctrl: added; Ctrl+Shift: taken out; else: just those (SketchUp's keys).
        (0.322) While a command waits for elements, with no key: a click takes them in or out, a region adds them."""
        mods = set(modifiers or ())
        ctrl = bool(mods & {"Control", "Ctrl", "Meta"})
        if ctrl and "Shift" in mods:
            return set(current) - set(picked)
        if ctrl or (region and self._asked() and "Shift" not in mods):
            return set(current) | set(picked)
        if "Shift" in mods or self._asked():
            return set(current) ^ set(picked)
        return set(picked)

    def _click_select(self, x, y, modifiers):
        if self.viewport.selected_dims:
            self.viewport.select_dimensions(set())
        if self.viewport.selected_annotations:
            self.viewport.select_annotations(set())
        axis = self.viewport.grid_axis_at(x, y, bubbles_only=True)     # a grid axis's bubble (0.72)
        obj_id = self._object_at(x, y) if axis is None else None
        if axis is None and obj_id is None:
            axis = self.viewport.grid_axis_at(x, y)                     # its line, where nothing else is
        if axis is not None and "grid" in self.viewport.unselectable:
            axis = None
        mods = set(modifiers or ())
        keep = bool(mods & {"Shift", "Control", "Ctrl", "Meta"}) or self._asked()   # (adding to / taking from)
        room = self.viewport.room_at(x, y) if axis is None and obj_id is None else None    # a room (0.99)
        if self.viewport.selected_rooms and not keep and room is None:
            self.viewport.select_rooms(set())
        if room is not None:
            if not keep:
                self.viewport.set_selection(set())
                self.viewport.select_axes(set())
            self.viewport.select_rooms(self._combine(self.viewport.selected_rooms, {room}, modifiers))
            return
        if axis is not None:
            if not keep:
                self.viewport.set_selection(set())
            self.viewport.select_axes(self._combine(self.viewport.selected_axes, {axis}, modifiers))
            return
        if self.viewport.selected_axes and not keep:
            self.viewport.select_axes(set())
        line = self._line_part(x, y)
        if line is not None:                              # (0.373) a loose line: just it (its chain, all joined) —
            self._select_line(*line, modifiers)           # near it, before the face behind it, as SketchUp's edges
            return
        part = self._face_part(x, y, obj_id) if obj_id is not None else None
        if part is not None and part[1] < 3:              # (0.310) a sketch's face: just it (with its edges)
            self._select_part(obj_id, part[0], part[1] == 2, modifiers)
            return
        if obj_id is not None and not keep and self._double_click(obj_id, x, y):
            return                                        # (0.355) a wall clicked twice: its profile edited
        ids = self._clicked(obj_id) if obj_id is not None else set()
        self.viewport.set_selection(self._combine(self.viewport.selection, ids, modifiers), keep_faces=keep)
        spec = getattr(self.host, "pending_classify", None)
        if spec is not None and obj_id is not None and not self.doc.get(obj_id).is_bim:
            self.host.classify(spec)

    def _double_click(self, obj_id, x, y):
        """Two clicks in a row on an element, the first having chosen it alone (as a double click): (0.355) a straight
        wall's profile edited (the Wall profile tool, with it); (0.356) a roof by blocks' blocks, in the block editor,
        the one clicked chosen. True if it was. (An element of a group: the first click chose the group, the second
        picks the element, as before.)"""
        now, last = time.monotonic(), getattr(self, "_element_click", None)
        self._element_click = (obj_id, now)
        obj = self.doc.get(obj_id)
        if last is None or last[0] != obj_id or now - last[1] > DOUBLE_CLICK_S or obj is None or not obj.is_bim \
                or self.viewport.selection != {obj_id}:
            return False
        kind = self.doc.ifc.kind_of(obj_id)
        if kind == "wall" and hasattr(self.host, "edit_wall_profile"):
            self._element_click = None
            self.host.edit_wall_profile(obj_id)
            return True
        # (0.410, the owner: «2 clique no piso para abrir a edição do perfil») a slab's, a floor finish's or a
        # ceiling's outline (a round slab changes by its radius)
        if kind in ("slab", "flooring", "ceiling") and hasattr(self.host, "edit_slab_outline") and \
                not (kind == "slab" and self.doc.ifc.slab_shape(obj_id) == "circulo"):
            self._element_click = None
            self.host.edit_slab_outline(obj_id)
            return True
        if kind == "roof" and hasattr(self.host, "edit_roof_blocks") and \
                (self.doc.ifc.roof_params(obj_id) or {}).get("form") == "blocks":
            self._element_click = None
            hit = self.viewport.pick_point(x, y)
            at = hit[2] if hit is not None and hit[0] == obj_id else None
            # (0.385, the owner) in the 3D view itself, not the block editor window (still in Properties)
            edit = getattr(self.host, "edit_roof_blocks_3d", None) or self.host.edit_roof_blocks
            _later(lambda: edit(obj_id, at))
            return True
        return False

    def _face_part(self, x, y, obj_id):
        """(0.310) The face of a sketch clicked, as SketchUp's: (its faces, clicks in a row on it) — None when the
        click takes the whole object (an IFC element, a component being edited, a face that is all the sketch, a
        type to classify chosen)."""
        obj = self.doc.get(obj_id)
        if obj is None or obj.is_bim or obj.component or getattr(self.host, "pending_classify", None) is not None \
                or self._asked():                         # (0.322: a command asks for whole objects)
            return None
        hit = self.viewport.pick(x, y)
        if hit is None or hit[0] != obj_id or not 0 <= hit[1] < len(obj.mesh.faces):
            return None
        faces = sg.surface_faces(obj.mesh, hit[1])
        if len(faces) == len(obj.mesh.faces):
            return None
        now, last = time.monotonic(), self._part_click
        again = last is not None and last[0] == (obj_id, faces) and now - last[1] <= DOUBLE_CLICK_S
        self._part_click = ((obj_id, faces), now, last[2] + 1 if again else 1)
        return faces, self._part_click[2]

    def _line_part(self, x, y):
        """(0.373) The loose line clicked, as SketchUp's click on an edge: (obj_id, the line's index, clicks in a row
        on it) — or None when the click is not near a loose line, or whole objects are asked for (a command waiting,
        a type to classify chosen)."""
        if getattr(self.host, "pending_classify", None) is not None or self._asked():
            return None
        hit = self.viewport.line_at(x, y, radius_px=LINE_PX)
        if hit is None:
            return None
        now, last = time.monotonic(), getattr(self, "_line_click", None)
        again = last is not None and last[0] == hit and now - last[1] <= DOUBLE_CLICK_S
        self._line_click = (hit, now, last[2] + 1 if again else 1, (float(x), float(y)))
        return hit[0], hit[1], self._line_click[2]

    def _again_on_line(self, x, y):
        """(0.373) A click right after one on a line, where it was: the next of clicks in a row (two: its chain), not
        a grip taken."""
        last = getattr(self, "_line_click", None)
        return last is not None and time.monotonic() - last[1] <= DOUBLE_CLICK_S and \
            np.hypot(x - last[3][0], y - last[3][1]) <= LINE_PX

    def _select_line(self, obj_id, k, clicks, modifiers):
        """One click: the line alone (an arc, a curve: whole); two: its chain (the lines of its sketch joined to it);
        three or more: every loose line joined to it, whatever chain. Shift, Ctrl, Ctrl+Shift: in / out, as faces."""
        obj = self.doc.get(obj_id)
        mods = set(modifiers or ())
        keep = bool(mods & {"Shift", "Control", "Ctrl", "Meta"})
        if clicks >= 3 or (clicks == 2 and obj.curve):
            ids = parts.touching_lines(self.doc, [obj_id])
            self.viewport.set_selection(self._combine(self.viewport.selection, ids, modifiers), keep_faces=keep)
            n = len(self.viewport.selection)
            self.host.message(t("info.lines_joined", n=n))
            return
        picked = {k} if clicks == 1 else set(parts.joined_lines(obj.mesh, k))
        if obj.curve or len(picked) == len(obj.mesh.lines):   # (a curve, or all its sketch: the sketch itself)
            self.viewport.set_selection(self._combine(self.viewport.selection, {obj_id}, modifiers), keep_faces=keep)
            self._say_lines()
            return
        lines = dict(self.viewport.line_selection) if keep else {}
        now = self._combine(lines.get(obj_id, frozenset()), picked, modifiers)
        if now:
            lines[obj_id] = frozenset(now)
        else:
            lines.pop(obj_id, None)
        if not keep:
            self.viewport.set_selection(set())
        self.viewport.select_lines(lines)
        self._say_lines()

    def _say_lines(self):
        """What is picked, said: a line's length, a curve's kind, how many lines."""
        lines, ids = self.viewport.line_selection, self.viewport.selection
        n = parts.line_count(self.doc, lines)
        length = format_length(parts.line_length(self.doc, lines), decimal_sep())
        if n == 1 and not ids:
            self.host.message(t("info.line_picked", l=length))
        elif n and not ids:
            self.host.message(t("info.lines_picked", n=n, l=length))
        elif len(ids) == 1 and getattr(self.doc.get(next(iter(ids))), "curve", None):
            self.host.message(t("info.curve_picked", k=t("curve." + self.doc.get(next(iter(ids))).curve["kind"])))
        elif ids:
            self.host.message(t("info.selected", n=len(ids) + n))

    def _select_part(self, obj_id, faces, with_edges, modifiers):
        """The face clicked picked: alone, or (Shift, Ctrl, Ctrl+Shift) in / out of the faces picked."""
        keep = bool(set(modifiers or ()) & {"Shift", "Control", "Ctrl", "Meta"})
        picked = dict(self.viewport.face_selection) if keep else {}
        had, edges = picked.get(obj_id, (frozenset(), False))
        now = self._combine(had, faces, modifiers)
        if now:
            picked[obj_id] = (frozenset(now), with_edges or (keep and edges))
        else:
            picked.pop(obj_id, None)
        if not keep:
            self.viewport.set_selection(set())
        self.viewport.select_faces(picked)
        n = parts.count(self.doc, picked)
        a = format_length(parts.area(self.doc, picked), decimal_sep())
        if not picked:
            self.host.message(t("info.selected_none"))
        elif n > 1:
            self.host.message(t("info.parts_selected", n=n, a=a))
        else:
            self.host.message(t("info.part_edges" if with_edges else "info.part_selected", a=a))

    def _with_groups(self, ids):
        """An element of a group taken by a region brings its whole group copy (as a click does)."""
        out = set()
        for i in ids:
            obj = self.doc.get(i)
            members = bim.group_members_of(self.doc, i) if obj is not None and obj.is_bim else None
            out |= set(members) if members else {i}
        return out

    def _region_points(self):
        """The region drawn so far, as a polygon (a box: its four corners) — and how it picks."""
        pts = self._region
        if self._picking is not None:
            kind, clicked = self._picking
            return clicked, (rs.FENCE if kind == "fence" else rs.mode_of(clicked))
        if self.drag_shape == "lasso":
            return pts, rs.mode_of(pts)
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], (rs.WINDOW if x1 >= x0 else rs.CROSSING)

    def _apply_region(self, region, mode, modifiers):
        ids, axes = self.viewport.region_pick(region, mode)
        ids = self._with_groups(ids)
        if self.viewport.selected_dims:
            self.viewport.select_dimensions(set())
        if self.viewport.selected_annotations:
            self.viewport.select_annotations(set())
        self.viewport.set_selection(self._combine(self.viewport.selection, ids, modifiers, region=True))
        self.viewport.select_axes(self._combine(self.viewport.selected_axes, axes, modifiers))
        n = len(self.viewport.selection) + len(self.viewport.selected_axes)
        self.host.message(t("info.selected", n=n) if n else t("info.selected_none"))

    def start_picking(self, kind):
        """Selecionar ▸ Polígono / Cerca (0.75): the next clicks are its points; Enter (or a click on the first
        point of a polygon, or the right button) ends it."""
        self._picking = (kind, [])
        self._press = self._region = self._active = None
        self.viewport.clear_temp_dims()                   # (no dimension of the selection in the way)
        self.host.set_hint(self.hint())

    def _pick_point(self, x, y):
        kind, clicked = self._picking
        if kind == "polygon" and len(clicked) >= 3 and np.hypot(x - clicked[0][0], y - clicked[0][1]) <= CLOSE_PX:
            self.enter()                                  # back on the first point: closed
            return
        clicked.append((float(x), float(y)))
        self._show_picking(x, y)

    def _show_picking(self, x=None, y=None):
        kind, clicked = self._picking
        pts = clicked + ([(float(x), float(y))] if x is not None and clicked and
                         np.hypot(x - clicked[-1][0], y - clicked[-1][1]) > 1 else [])
        self.viewport.show_region(pts, rs.FENCE if kind == "fence" else rs.mode_of(pts), closed=kind == "polygon")

    def enter(self):
        if self._picking is None:
            return
        kind, clicked = self._picking
        if len(clicked) < (2 if kind == "fence" else 3):
            self.host.message(t("err.region_points"), warning=True)
            return
        region, mode = self._region_points()
        self._picking = None
        self.viewport.show_region()
        self._apply_region(region, mode, ())
        self.host.set_hint(self.hint())

    def delete(self):
        if self.viewport.selected_dims:
            dims = list(self.viewport.selected_dims)
            self.viewport.select_dimensions(set())
            self.doc.execute(dims_model.RemoveDimensions(dims, t("cmd.dimension_delete")))
            return
        if self.viewport.selected_annotations:            # lines, regions, texts drawn in the view (0.120)
            anns = list(self.viewport.selected_annotations)
            self.viewport.select_annotations(set())
            self.doc.execute(notes2d.RemoveAnnotations(anns, t("cmd.draft_delete")))
            return
        if self.viewport.selected_axes:                   # grid axes (0.72), with the rest selected or alone
            axes = sorted(self.viewport.selected_axes)
            self.viewport.select_axes(set())
            bim.remove_grid_axes(self.doc, axes)
        if self.viewport.selected_rooms:                  # rooms (0.99)
            rooms = sorted(self.viewport.selected_rooms)
            self.viewport.select_rooms(set())
            bim.remove_rooms(self.doc, rooms)
        if self.viewport.face_selection:                  # (0.310) faces of sketches picked alone
            picked = dict(self.viewport.face_selection)
            self.viewport.select_faces({})
            self.host.message(t("info.part_deleted", n=parts.delete(self.doc, picked)))
        if self.viewport.line_selection:                  # (0.373) loose lines picked alone
            picked = dict(self.viewport.line_selection)
            self.viewport.select_lines({})
            self.host.message(t("info.lines_deleted", n=parts.delete_lines(self.doc, picked)))
        ids = list(self.viewport.selection)
        if ids:
            self.viewport.set_selection(set())
            bim.delete(self.doc, ids)

    def deactivate(self):
        # switching to another tool keeps the selection (select first, then Move / Rotate)
        if getattr(self.host, "pending_classify", None) is not None:
            self.host.pending_classify = None
        self._active, self._dims, self._move = None, [], None
        self.viewport.clear_temp_dims()
        self.viewport.show_grips()

    def cancel(self):
        if self._picking is not None or self._region is not None:     # Esc: the region drawn goes, nothing else
            self._picking = self._region = self._press = None
            self.viewport.show_region()
            self.host.set_hint(self.hint())
            return
        if self._move is not None:                        # Esc: the grip goes back, the selection stays
            self._move = None
            self.viewport.clear_overlays()
            self.host.set_hint(self.hint())
            self.host.set_vcb("")
            self._refresh_dims(keep=False)
            return
        if self._active is not None:                      # Esc: leave the dimension clicked, keep the selection
            self._active = None
            self.host.set_hint(self.hint())
            self.host.set_vcb("")
            self.viewport.show_temp_dims(self._dims)
            return
        if getattr(self.host, "pending_classify", None) is not None:
            self.host.pending_classify = None
            self.host.set_hint(self.hint())
        self.viewport.set_selection(set())
        if self.viewport.selected_dims:
            self.viewport.select_dimensions(set())
        if self.viewport.selected_annotations:
            self.viewport.select_annotations(set())
        if self.viewport.selected_axes:
            self.viewport.select_axes(set())
