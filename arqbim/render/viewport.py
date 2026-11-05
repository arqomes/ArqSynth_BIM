"""GPU viewport (wgpu through pygfx).

This is the ONLY module that talks to the renderer. The rest of the app sees
plain numpy points, rays, pick results and snaps, so pygfx can later be
replaced by our own wgpu engine (batching, instancing, LOD) without touching
the tools.

Display geometry is a cache per object: only objects that changed in the
Document are rebuilt.

Navigation (SketchUp-like, done here rather than with a pygfx controller):
    middle drag            orbit around the point under the cursor (a plan / section: pan)
    Shift + middle drag    pan
    wheel                  zoom towards the point under the cursor

Plans and sections are seen without perspective (an orthographic camera: pygfx's camera with a
field of view of 0) and never orbit: they stay drawings. The 3D view is a perspective one.
"""

import contextlib
import functools
import math
import os
import time

import numpy as np
import pygfx as gfx
import pylinalg as la

from ..core import dim_layout, temp_dims
from ..core.inference import GUIDE_HALF_LENGTH, SnapIndex, find_snap
from ..core.tracking import Tracking
from ..core.units import format_angle, format_length
from ..core.mesh import TriMesh, is_convex_polygon, triangulate_polygon
from ..core.sketch_geometry import face_world_normal, normalize, ray_plane, transform_point
from ..i18n import decimal_sep, t
from ..model import annotations as notes2d
from ..model import dimensions as dims_model
from ..model import graphic_styles as styles_model
from ..model import material_looks
from ..model import seen_joins
from ..model import symbols as marks_model
from ..model import view_styles as view_styles_model
from ..model.document import GUIDES_CHANGED, STOREY_CHANGED
from . import canvas as views_canvas
from .batches import CLEAR, GROUND, POCHE_LIFT, BatchedElements, Piece, physical, plain_pieces

# (0.315) a view style's faces as the batches draw them
FACE_LOOKS = {"shaded": "shaded", "consistent": "consistent", "white": "hidden", "none": "wire", "xray": "xray"}
SHADOW_GROUND = "#f4f3ef"         # what the shadows fall on, under the model
SUN = (0.45, -0.75, 1.0)          # where the fixed sun shines from (as in SketchUp: every face reads differently)
HATCH_SCALE = 50                  # (0.317) a plan's / section's hatches on screen: drawn at its scale, else at 1:50
HATCH_DEPTH = 0.003               # m: …a hair beyond the cutting plane (kept by its clipping)
HATCH_QUEUE = 2700                # …drawn after the batches and their poché (theirs is 2600), not hiding it from a click
SEAMS_AT_ONCE = 300               # (0.320) more elements than this to look at for seams: a few after each image…
SEAMS_BUDGET = 0.01               # s: …for so long each time…
FLUSH_BUDGET = 0.03               # s (0.328): the batches made again for one image when many changed (a file opened)
SEAMS_SHOW_EVERY = 2.0            # s: …those changed shown again so often until all are done
HATCHES_LATER = 60                # (0.320) more elements cut than this: an edit's image first, the cut's hatches after
# (0.315) …and when it casts shadows: the view style's (0.316: its azimuth and altitude — by default from the south-
# south-west, high, view_styles.SUN_AZIMUTH / SUN_ALTITUDE)

BACKGROUND = views_canvas.BACKGROUNDS[False]   # the view's: light at the bottom, a pale sky at the top (0.341: render/canvas)
GROUND_GRID = "#c3c8cc"                  # the ground grid's lines
WORK_PLANE_COLOR = (0.24, 0.50, 0.84, 0.45)   # (0.412) the work plane's grid (model/work_plane), in the 3D view:
WORK_PLANE_SIZE = 12.0                         # a line a metre, this many metres square round where it was put
# (0.329) an image of the view (render_image): its backgrounds, and the most pixels drawn for it inside the GPU (twice
# as wide and high, then made smaller: smoother edges — when that stays under this; else as many as the image's)
IMAGE_BACKGROUNDS = ("view", "white", "transparent")
IMAGE_SMOOTH_MOST = 4_200_000
IMAGE_WIDTH_MOST = 7680           # px (the GPU's largest picture is 8192)

FACE_COLOR = "#ebe7df"            # sketch
FACE_SELECTED = "#bcd3f5"
BIM_COLORS = material_looks.CATEGORY_COLOURS     # (0.315: kept with the materials' looks, for paper too)
TERRAIN_CLASS = "IfcGeographicElement"     # (0.155) the terrain: its contour lines drawn, not its triangles
CONTOUR_COLOR = "#7d6a4f"                  # its contour lines (the major ones thicker)
CONTOUR_LIFT = 0.01                        # m over its surface
BIM_DEFAULT = material_looks.CATEGORY_DEFAULT
SYSTEM_CLASSES = ("IfcPipeSegment", "IfcPipeFitting", "IfcDuctSegment", "IfcDuctFitting")   # (their system's, 0.141)
EDGE_COLOR = "#202020"
EDGE_SELECTED = "#1f5fd6"
PREVIEW = (0.10, 0.45, 0.95, 1.0)
PREVIEW_FILL = (0.10, 0.45, 0.95, 0.22)
# a selection region being drawn (0.75): window (wholly inside) blue, crossing (touching) green — as AutoCAD's
REGION_COLORS = {"window": ((0.12, 0.37, 0.84, 1.0), (0.12, 0.37, 0.84, 0.12)),
                 "crossing": ((0.18, 0.55, 0.34, 1.0), (0.18, 0.55, 0.34, 0.12)),
                 "fence": ((0.85, 0.45, 0.10, 1.0), (0.85, 0.45, 0.10, 0.0))}
AXIS_U = (0.85, 0.15, 0.15, 1.0)   # red
AXIS_V = (0.10, 0.62, 0.20, 1.0)   # green
AXIS_W = (0.15, 0.30, 0.90, 1.0)   # blue
AXIS_COLORS = {"x": AXIS_U, "y": AXIS_V, "z": AXIS_W}
AUTO_ALIGN_PX = 400                        # corners this near the cursor (pixels) line it up by themselves…
AUTO_ALIGN_MOST = 60                       # …the nearest of them
UNDERLAY_COLOR = (0.62, 0.62, 0.62, 1.0)   # a plan's underlay storey
GRID_COLOR = "#4a6a8a"                     # the structural grid's axes and bubbles
MARK_COLOR = "#2a2a2a"                     # the sections' and elevations' marks, the levels (0.121)
GRID_BUBBLE = 0.35                         # m: the radius of an axis's bubble
# rooms in a plan (0.99): a light fill just over the floor, their outline, the selection's tint
ROOM_FILL = (0.98, 0.96, 0.84, 0.55)
ROOM_FILL_DARK = (0.25, 0.24, 0.20, 0.55)  # (0.341) …on the dark views: a warm grey a little lighter than the ground
ROOM_SELECTED = (0.31, 0.55, 0.95, 0.40)
ROOM_LINE = "#b9a96a"
ROOM_LIFT = 0.003
ROOM_AREA = "{:.2f} m²"
UNDERLAY_LIFT = 0.005                      # m above the floor it is drawn on
IMAGE_LIFT = 0.002                         # m: a background image over its floor (under the rooms' fill, 0.154)
CAD_LIFT = 0.004                           # m: a CAD drawing linked over its floor (0.158)…
CAD_COLOR = "#4d6a94"                      # …its lines
TEMP_DIM_COLOR = (0.12, 0.37, 0.84, 1.0)   # the grips (Revit's blue; the temporary dimensions' until 0.360)
# (0.372) the temporary dimensions as the owner's Blender addon draws them now (ArqSynth Modeler «wall_dimensions»
# v3.5, and the owner's picture): thin light-blue lines with their arrows — an element's own measures a little stronger
# than its relations to the others, deeper on the light canvas to be seen there —; each value white on a dark box laid
# on its line (a relation's with «↔»); the one under the mouse or typed over strong: its line deeper (white on the dark
# canvas), its box blue
TEMP_DIM_LOOK = {False: {"measure": "#2f86dc", "relation": "#5aa6e6", "strong": "#0a5bc4", "box": "#1b1f24",
                         "box_strong": "#0a5bc4", "text": "#ffffff"},
                 True: {"measure": "#59b3ff", "relation": "#80d1ff", "strong": "#ffffff", "box": "#15181c",
                        "box_strong": "#2f7fd8", "text": "#ffffff"}}
TEMP_DIM_FONT = {"measure": 12, "relation": 11, "strong": 12}   # px
TEMP_DIM_PAD = 6.0                          # px of the box each side of its value…
TEMP_DIM_BOX_H = 1.6                        # …and its height, in the value's heights
TEMP_DIM_RAISE = 0.12                       # the value raised in its box (digits have nothing below the line), in heights
RELATION_MARK = "↔ "                   # (0.372) «↔ 0,63 m»: a relation's value, as the addon's
# (0.372) the letters' widths of the font the values are drawn in (Noto Sans), in its heights: the box round a value
GLYPH_EM = {**{c: 0.572 for c in "0123456789"}, ",": 0.26, ".": 0.26, " ": 0.26, "m": 0.925, "c": 0.48, "°": 0.40,
            "[": 0.30, "]": 0.30, "↔": 1.0, "-": 0.32, "²": 0.38}
TEMP_DIM_LINE_PX = 5                       # a click this near a relation's line: it, not what is under it…
TEMP_DIM_HIDDEN = 0.15                     # m: …unless something there is this much nearer than the line (in front)
PARALLEL_COLOR = (0.85, 0.10, 0.75, 1.0)   # magenta, as SketchUp's parallel / perpendicular
EXTENSION_COLOR = (0.45, 0.45, 0.45, 1.0)
ACQUIRED_COLOR = (0.35, 0.35, 0.35, 1.0)
GUIDE_COLOR = "#5a5a5a"
EDGE_LIFT = 0.002                  # m; keeps edge lines visible on top of their faces
SHEET_LIFT = 0.001                 # m; flat sketches lying on a face are drawn just above it
OVERLAY_QUEUE = 4000
MIDDLE = 3
ORBIT_SPEED = 0.006                # radians per pixel
ZOOM_SPEED = 0.0015                # per wheel unit (one notch = 120)
VIEW_HISTORY = 50                  # Previous view: how many camera positions are kept (0.78)
WHEEL_PAUSE_S = 0.6                # the wheel still this long: its next turns are a new step of that history
DOUBLE_CLICK_S = 0.35              # two middle-button presses this close: zoom all
TURN_S = 0.35                      # a click on the view cube turns the camera this smoothly (0.79)

ORTHO_MIN, ORTHO_MAX = 0.05, 1e5   # m: the least / most a plan or section shows from bottom to top (zoom)
CUT_HEIGHT = 1.20                  # m above the storey level: where a plan cuts (walls, doors, windows)
SYMBOL = "symbol"                  # batch key mark: doors drawn in a plan by their symbol, not their cut
SYMBOL_DEPTH = 0.05                # m under the cut: where plan symbols are drawn (over all that is below)
SYMBOL_PICK_PX = 6                 # clicking this near a door's symbol picks the door
DIM_DEPTH = 0.04                   # m towards the viewer from the cut: where dimensions are drawn
BOX_COLOR = "#1f74d1"              # the section box: its outline and its handles
BOX_HANDLE_PX = 9                  # a click this near a handle (the middle of a face of the box) drags it
BOX_MIN = 0.10                     # m: the least between two opposite faces of the box
BOX_MARGIN = 0.30                  # m round what the box is put round
PATTERN_PICK_PX = 6                # (0.332) a surface pattern's line this near the mouse is picked (Align)…
PATTERN_ON_FACE = 0.01             # m: …among the lines this near the face picked (they are a hair off it)

VIEW_DIRS = {
    "iso": (-0.55, 0.75, -0.45),    # looking from front-right, above
    "top": (0.0, 1e-4, -1.0),
    "front": (0.0, 1.0, 0.0),
    # (0.186, the footer's Orientation) the other sides, and the isometrics from the other corners
    "back": (0.0, -1.0, 0.0),
    "left": (1.0, 0.0, 0.0),
    "right": (-1.0, 0.0, 0.0),
    "iso_sw": (0.55, 0.75, -0.45),
    "iso_ne": (-0.55, -0.75, -0.45),
    "iso_nw": (0.55, -0.75, -0.45),
}


def _quat_of(x, y, z):
    """(0.398) The rotation (pylinalg's quaternion, x y z w) that turns the axes into x, y, z (unit, square)."""
    m = np.column_stack((x, y, z)).astype(float)
    trace = m[0, 0] + m[1, 1] + m[2, 2]
    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2
        q = ((m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s)
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        q = (0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s)
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        q = ((m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s)
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        q = ((m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s)
    return tuple(float(c) for c in q)


def _f32(a):
    return np.ascontiguousarray(np.asarray(a, dtype=np.float32).reshape(-1, 3))


def _physical(hex_color):
    """RGBA in physical (linear) values for vertex colours (a few colours, worked out once each) — (0.341) in the
    canvas in use (render/canvas: a grey turned over on the dark one)."""
    return _physical_in(hex_color, views_canvas.DARK)


@functools.lru_cache(maxsize=None)
def _physical_in(hex_color, dark):
    return (*gfx.Color(views_canvas.ink(hex_color) if dark else hex_color).to_physical(), 1.0)


_INKED = ("color", "outline_color", "edge_color", "major_color", "minor_color")


def _mat(cls, turn=None, **kw):
    """(0.341) A material, its colours in the canvas in use (render/canvas) — a texture's tint as it is. turn: its
    greys turned over or not (None: as the canvas is — the model's in the 3D view are not, see Viewport._model_dark)."""
    if (views_canvas.DARK if turn is None else turn) and "map" not in kw:
        for key in _INKED:
            if kw.get(key) is not None:
                kw[key] = views_canvas.ink(kw[key])
    return cls(**kw)


_I4 = np.eye(4)
PLAIN_CHUNK = 2000              # (0.344) plain pieces made together so many at a time (prepare_pieces)
WARM_UP = "__warm_up__"         # id of the invisible piece drawn once at start-up (see Viewport.warm_up)


def prepare_pieces(shapes, classes, pause=None):
    """Display pieces of IFC elements just read, made outside the window's thread while a
    file opens in the background (numpy only, no GPU): {GlobalId: Piece}, not selected.
    shapes: {GlobalId: TriMesh}; classes: {GlobalId: IFC class}; pause(): called now and
    then (it may wait while the window is busy)."""
    edge = _physical_in(EDGE_COLOR, False)          # (0.341: as in the 3D view — light; a dark plan makes its own)
    pieces = {}
    plain = []                                       # (0.344: the plain ones — most — made together, plain_pieces)
    for k, (guid, mesh) in enumerate(shapes.items()):
        if pause is not None and k % 50 == 49:
            pause()
        own = getattr(mesh, "colors", None) is not None              # (0.259: in its parts' own colours)
        ground = classes.get(guid) == TERRAIN_CLASS
        if not ground and isinstance(mesh, TriMesh) and len(mesh.normals) == len(mesh.tris):
            plain.append(guid)
            continue
        mesh.bounds()                                # (for the inferences and framing, worked out here)
        pieces[guid] = Piece(mesh, _I4, None if own else _physical_in(BIM_COLORS.get(classes.get(guid), BIM_DEFAULT),
                                                                      False),
                             edge, ground=ground)
    colours = {}
    for cls in {classes.get(g) for g in plain}:
        colours[cls] = _physical_in(BIM_COLORS.get(cls, BIM_DEFAULT), False)
    for start in range(0, len(plain), PLAIN_CHUNK):  # (in chunks: the window may need the processor meanwhile)
        if pause is not None and start:
            pause()
        chunk = plain[start:start + PLAIN_CHUNK]
        made = plain_pieces([shapes[g] for g in chunk],
                            [None if shapes[g].colors is not None else colours[classes.get(g)] for g in chunk], edge)
        pieces.update(zip(chunk, made))
    return pieces


def _drawable(text):
    """Text for the 3D labels: the built-in font has no '▸' (menu paths like BIM ▸ Classificar)."""
    return text.replace("▸", ">")


def _same_view(a, b):
    """Two camera snapshots showing the same thing (the view history keeps one of them)."""
    return (np.allclose(a["position"], b["position"], atol=1e-6) and np.allclose(a["rotation"], b["rotation"], atol=1e-7)
            and abs(a["width"] - b["width"]) < 1e-9 and abs(a["zoom"] - b["zoom"]) < 1e-9 and a["fov"] == b["fov"])


def _same_seams(a, b):
    """(0.320) Two elements' seams the same (both none, or the same edges kept and left)?"""
    if a is None or b is None:
        return a is None and b is None
    return np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])


def _overlay_material(cls, **kw):
    return _mat(cls, depth_test=False, depth_write=False, render_queue=OVERLAY_QUEUE, **kw)


def label_width_px(text, size):
    """(0.372) A temporary dimension's value's width (px) at `size` px high, by its letters' widths (GLYPH_EM)."""
    return sum(GLYPH_EM.get(c, 0.56) for c in str(text)) * float(size)


def _kept_corners(corners, planes):
    """The corners a plan, a section or a section box keeps (n·p >= offset for each plane)."""
    ok = np.ones(len(corners), dtype=bool)
    for normal, offset in planes:
        ok &= corners @ np.asarray(normal, dtype=float) >= offset - 1e-9
    return corners[ok]


class _ObjectView:
    def __init__(self, group, faces, edges, tri_owner, mesh, matrix):
        self.group, self.faces, self.edges, self.tri_owner = group, faces, edges, tri_owner
        self.mesh, self.matrix = mesh, matrix   # what is displayed (may be a tool preview)


class Viewport:
    def __init__(self, canvas, document):
        self.canvas = canvas
        self.doc = document
        self.renderer = gfx.renderers.WgpuRenderer(canvas)
        self.scene = gfx.Scene()
        self.selection = set()
        self.face_selection = {}    # (0.310) obj_id -> (frozenset of a sketch's faces picked alone, with their edges)
        self.line_selection = {}    # (0.373) obj_id -> frozenset of the loose lines picked alone (their indices)
        self.selection_listeners = []
        self._views = {}            # obj_id -> _ObjectView (sketches: one GPU object each)
        self._by_wobj = {}          # id(face mesh world object) -> obj_id
        self._meshes = {}           # obj_id -> (mesh, matrix) on screen, for picking a point on a face
        self.snap_index = SnapIndex()   # inference candidates, looked up near the cursor only
        self._guides = None         # display of the guide lines
        self._symbols = None        # display of the doors' plan symbols (in a plan)
        self._symbol_segments = np.zeros((0, 2, 3))     # as shown, with the door of each
        self._symbol_owner = []
        self.section_view = None    # the section / elevation shown, as its dimensions name it (set by the window)
        self.colours = {}           # GlobalId -> colour of the graphic rule shown (see set_colours)
        self.hidden_classes = set() # IFC classes the view shown hides (its view template)
        self.hidden_phases = set()  # phases it hides ("NEW"…; "" for the elements without one)
        self._split = set()         # IFC classes batched apart (see _split_classes)
        self._split_phases = False  # elements batched by phase too (some template hides phases)
        self.cut_height = CUT_HEIGHT    # m above the storey: where a plan cuts (the view template's)
        self.selected_dims = set()  # dimensions picked (Delete removes them)
        self._dim_objects = []      # display of the view's dimensions: lines, values
        self._dim_lines = np.zeros((0, 2, 3))           # each dimension line as shown, with its dimension
        self._dim_owner = []
        self._dim_texts = []        # (0.398) their values' boxes: (middle, along, across (3,), half sizes, dimension)
        self.selected_annotations = set()   # drawings in the view picked (0.120; Delete removes them)
        self.annotation_listeners = []      # (0.191) called with them when they change: grips, Properties
        self._ann_objects, self._ann_owner, self._ann_texts = [], [], []
        self._ann_segments = np.zeros((0, 2, 3))
        self._mark_objects, self._mark_heads = [], []   # the view's symbols (0.121): sections, elevations, levels
        self._above_objects, self._above_shapes = [], []   # a plan's pipes and ducts above its cut (0.135)
        self._nav = None          # ("orbit" | "pan", last_xy) while the middle button is down
        self.on_host_face = None    # (sketch) -> does it lie on a wall's / slab's face? (set by the window)
        self.view_depth = 0.0       # a plan's view depth (m below its storey: the storeys down to there seen too)
        self.crop = None            # a plan's crop region (x0, y0, x1, y1), or None
        self._underlay = None       # a plan's underlay storey: grey lines
        self._grid_objects = []     # the structural grid's axes, bubbles and tags (0.67)
        self.selected_axes = set()  # grid axes picked (indices in Document.grids; 0.72)
        self.unselectable = set()   # categories that cannot be selected (0.76): IFC classes, "sketch", "grid"
        self.axes_listeners = []    # (indices) -> None, when they change
        self.selected_rooms = set()     # rooms picked in a plan (IfcSpace GlobalIds; 0.99)
        self.rooms_listeners = []       # (guids) -> None, when they change
        self._room_objects, self._room_shapes = [], []
        self._image_objects = []        # the background images on screen (0.154)
        self._cad_objects = {}          # link uid -> (what it was made from, its lines on screen) (0.158)
        self._cloud_objects = {}        # cloud uid -> (what it was made from, its points on screen) (0.161)
        self._contour_objects = []      # the terrains' contour lines on screen (0.155)
        self.show_slopes = False        # the terrains coloured by their slope (0.156; View ▸ Terrain slopes)
        self.show_analytical = False    # the analytical model over the model (0.163; View ▸ Analytical model)
        self._analytical_objects = []
        self._contour_cache = {}        # terrain GlobalId -> ((its shape, interval), its contour lines)
        self._label_cache = {}          # terrain GlobalId -> (its contour lines, their heights' spots) (0.202)
        self._batter_cache = {}         # terrain GlobalId -> (its shape, its platforms' slopes' lines) (0.203)
        self._pictures = {}             # picture path -> its texture (None: not found / not read), made once
        self.picture_loader = None      # (path) -> (H, W, 4) uint8 RGBA, or None: set by the window (Qt reads them)
        self.tracking = Tracking()  # points and edges acquired while drawing (alignments, core/tracking.py)
        self.look = ("shaded", True, True, False)   # the 3D view's (visual style, edges, ground grid, axonometric)
        # (0.315) the view style shown (model/view_styles) and what of it is in the batches' pieces: the colours (of
        # each category or each material), the surface patterns, the transparency; a plan's or section's own style
        self.vstyle = view_styles_model.BUILTIN["shaded"]
        self.cut_style = None
        self._dressing = ("category", False, False)
        self._overrides = ()              # (0.318) the view style's hatches by category the pieces were made with
        self.element_hatches = {}         # (0.331) the view's own by element (set_element_hatches)
        self._dressed = {}                # obj_id -> (its mesh, materials' generation, dressing, (colours, patterns, clear))
        self._shadow_ground = None        # (0.315) under the model when the sun casts shadows
        self._sun_preview = None          # (0.365) a scene's sun previewed: towards it (else the view style's)
        self._sun_box = None              # (0.365) …the model's (middle, radius, bottom), measured once for it
        # (0.317) a plan's / section's cut hatched on screen: what it was made from, each element's part, the objects
        self._hatch_key = None
        self._hatch_parts = {}
        self._hatch_objects = []
        self._hatch_later = False         # (0.320) made again after the next image (an edit, many elements cut)
        self._shown_dressed = set()       # (0.317) the elements shown dressed by their materials now
        # (0.320) the seams between elements of one material in one plane, left out of their edges: each element's
        # (its mesh, seen_joins.seams), the elements' boxes on a grid, their planes and materials as last read
        self._seams = {}
        self._neighbours = seen_joins.Neighbours()
        self._seam_planes = {}
        self._seam_infos = {}
        self._seam_apart = {}             # (0.333) each one's elements unjoined from it by hand, as last read
        self._seams_read = False          # (worked out once the file's IFC is read: its materials)
        self._seam_queue = set()          # (many at once: worked out a few after each image…
        self._seam_again = set()          # …those changed shown again together…
        self._seam_shown = 0.0            # …now and then)
        self._on_host = set()       # sketches shown so: only their outline
        self._focus = np.array((2.0, 2.0, 0.0))
        self._back, self._forward = [], []    # view history (0.78): camera snapshots for Previous / Next view
        self._last_wheel = 0.0                # when the wheel last turned (a burst is one history step)
        self._last_middle = (0.0, 0.0, 0.0)   # (when, x, y) of the last middle-button press: double click
        self.middle_drag = "orbit"            # what the middle button does: "orbit" (SketchUp) | "pan" (Revit)
        self.cube = None                      # the view cube (0.79; set by the window: its faces' pictures)
        self._anim = None                     # a smooth turn in progress: (start time, from, to) camera snapshots
        self._cube_press = None               # [x, y, part, dragged] of the left button pressed on the cube
        self.on_cube_menu = None              # (x, y) -> None: the cube's ▾ (the window's menu)
        self.home_view = None                 # the 3D view's starting view, {"eye", "target"} (None: the usual one)

        self.background = gfx.Background(None, gfx.BackgroundMaterial(*views_canvas.background()))
        self.scene.add(self.background)
        # (it writes no depth: a face lying on the ground is never hidden — nor made unpickable — by it, 0.76)
        self.grid = gfx.Grid(None, _mat(          # (0.393: its colour from the background in use — not turned again)
            gfx.GridMaterial, turn=False, major_step=1.0, minor_step=0.1, major_thickness=1.0, minor_thickness=0.0,
            major_color=views_canvas.ground_grid(GROUND_GRID), axis_thickness=0.0, infinite=True, depth_write=False),
            orientation="xy")
        self.scene.add(self.grid)          # drawn at the level of the active storey
        # (0.412) the work plane set (doc.work_plane): a square grid on it, in the 3D view only
        self.work_grid = gfx.Grid(None, _mat(
            gfx.GridMaterial, turn=False, major_step=1.0, minor_step=0.25, major_thickness=1.0, minor_thickness=0.0,
            major_color=WORK_PLANE_COLOR, axis_thickness=0.0, infinite=False, depth_write=False,
            alpha_mode="blend"), orientation="xy")
        self.work_grid.visible = False
        self.scene.add(self.work_grid)
        self._work_shown = None            # (the plane its grid shows, whether shown)
        self.only_active_storey = False    # True: hide what belongs to the other storeys
        self.plan = False                  # plan of the active storey (see set_plan)
        self.section = None                # (point, normal) of the section shown (see set_section)
        self.box = None                    # section box of the 3D view: (lowest, highest) corner (see set_box)
        self._box_view = None              # its outline and handles
        self._add_axes()

        self.objects = gfx.Group()
        self.scene.add(self.objects)
        self.bim = BatchedElements(self.objects)     # IFC elements: a few batches, not one object each
        self._ready = {}            # obj_id -> Piece made in advance (opening a file, see prepare_pieces)
        self._model_turned = (False, False)    # (0.341) shown: (the model's greys turned over, its edges light)
        self._after_draw = []       # called once after the next image (see after_next_draw)
        self._build_overlays()

        self.camera = gfx.PerspectiveCamera(45, 16 / 9)
        self.camera.world.reference_up = (0, 0, 1)
        # Fixed sun (as in SketchUp): top light, front mid-tone, side darker,
        # so every face of a volume reads differently while orbiting.
        self.scene.add(gfx.AmbientLight(intensity=1.0))
        sun = gfx.DirectionalLight(intensity=1.8)
        sun.local.position = SUN                 # shines towards the origin
        self.scene.add(sun)
        self.sun = sun                           # (0.315: its shadows, when the view style casts them)
        self.scene.add(self.camera)
        self.set_view("iso", center=(2.0, 2.0, 0.0), radius=8.0)

        self.renderer.add_event_handler(self._on_nav_event, "pointer_down", "pointer_move", "pointer_up", "wheel")
        document.subscribe(self._on_document_changed)
        canvas.request_draw(self._draw)

    # ------------------------------------------------------------ drawing

    def _sync_work_plane(self):
        """(0.412) The work plane's grid where the document's work plane is — in the 3D view (not in a plan, section
        or elevation, which keep their own planes)."""
        plane = getattr(self.doc, "work_plane", None)
        shown = plane is not None and self.current_view() is None
        key = (id(plane), shown)
        if key == self._work_shown:
            return
        self._work_shown = key
        self.work_grid.visible = shown
        if shown:
            size = WORK_PLANE_SIZE
            corner = np.eye(4)
            # (a plane standing up: its grid mostly above where it was put — not half under the ground)
            below = 2.0 if abs(float(np.asarray(plane.v)[2])) > 0.9 else size / 2
            corner[:3, 3] = (-size / 2, -below if float(np.asarray(plane.v)[2]) >= 0 else below - size, 0.0)
            scale = np.diag((size, size, 1.0, 1.0))
            self.work_grid.local.matrix = plane.matrix() @ corner @ scale

    def _draw(self):
        self._sync_work_plane()
        if self.box is not None and not self.cutting():
            # the section box's poché a hair towards the viewer, wherever they turned (see batches)
            lift = tuple(float(c) for c in np.round(-self.view_direction() * POCHE_LIFT, 4))
            if lift != self.bim.poche_lift:
                self.bim.set_poche_lift(lift)
        more = self.bim.flush(FLUSH_BUDGET)          # rebuild only the batches that changed (0.328: many — some)
        self._step_animation()
        self._follow_view()
        if self.cube is not None and not self.cutting():
            self.renderer.render(self.scene, self.camera, flush=False)
            self.cube.follow(self.camera.local.rotation)       # the view cube in its corner (0.79)
            self.cube.render(self.renderer, self.logical_size())
            self.renderer.flush()
        else:
            self.renderer.render(self.scene, self.camera)
        if WARM_UP in self.bim:
            self.bim.remove(WARM_UP)                 # drawn once: its job is done
        if more:
            self.redraw()                            # (0.328) the other batches at the next images
        done, self._after_draw = self._after_draw, []
        for fn in done:
            fn()

    def after_next_draw(self, fn):
        """Call fn() once the next image is drawn (and ask for one)."""
        self._after_draw.append(fn)
        self.redraw()

    def after_all_drawn(self, fn):
        """(0.328) Call fn() once every batch is drawn: after the next image, or — many changed at once — after the
        last of those that draw them a few at a time (see FLUSH_BUDGET)."""
        def check():
            if self.bim.pending():
                self.after_next_draw(check)
            else:
                fn()
        self.after_next_draw(check)

    def warm_up(self):
        """Have the GPU programs (shaders) of the batches made at start-up, before any file is
        opened: a batch with one zero-area triangle (nothing to see) is drawn once, then dropped.
        Otherwise the first opening pays for them (~0,3 s)."""
        piece = Piece(TriMesh(np.zeros((3, 3)), [[0, 1, 2]]), _I4, (0.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.0))
        self.bim.put(WARM_UP, piece, WARM_UP)
        self.redraw()

    def adopt_pieces(self, pieces):
        """Pieces made in advance by prepare_pieces for the elements about to arrive (opening a
        file): used instead of making them again here. {} drops the unused ones."""
        self._ready = pieces

    def redraw(self):
        self.canvas.request_draw()

    def _add_axes(self):
        L = 1000.0
        pos, col = [], []
        for axis, color in ((0, (0.85, 0.15, 0.15, 1)), (1, (0.10, 0.62, 0.20, 1)), (2, (0.15, 0.30, 0.90, 1))):
            a, b = np.zeros(3), np.zeros(3)
            b[axis] = L
            pos += [a, b]
            col += [color, color]
        geom = gfx.Geometry(positions=_f32(pos), colors=np.array(col, dtype=np.float32))
        self._axes = gfx.Line(geom, _mat(gfx.LineSegmentMaterial, thickness=1.5, color_mode="vertex"))
        self.scene.add(self._axes)

    # ------------------------------------------------------------ camera

    def camera_position(self):
        return np.array(self.camera.local.position, dtype=float)

    def view_direction(self):
        return normalize(np.asarray(self.camera.world.forward, dtype=float))

    def _set_focus(self, point):
        """Keep near/far clip planes sensible for what the user is looking at."""
        self._focus = np.asarray(point, dtype=float)
        d = max(np.linalg.norm(self._focus - self.camera_position()), 0.05)
        self.camera.depth_range = (min(max(d / 150, 0.005), 50.0), max(d * 3000, 500.0))

    def camera_state(self):
        """(position, direction, up, field of view in degrees) of the camera — for a note. A plan or
        section: the perspective camera of 45° that shows about the same."""
        up = normalize(np.asarray(self.camera.world.up, dtype=float))
        position, forward = self.camera_position(), self.view_direction()
        if self.is_ortho():
            target = position + forward * float((self._focus - position) @ forward)
            distance = self.ortho_height() / 2 / math.tan(math.radians(22.5))
            return target - forward * distance, forward, up, 45.0
        return position, forward, up, float(self.camera.fov)

    def render_camera(self):
        """(0.343) The camera as a realistic render (model/render_scene) takes it: {eye, target, up, fov — degrees top
        to bottom, 0 without perspective —, height — m top to bottom then} — what the view shows, read off its
        projection (whatever way pygfx shares its field of view between width and height)."""
        position, forward = self.camera_position(), normalize(np.asarray(self.view_direction(), dtype=float))
        up = normalize(np.asarray(self.camera.world.up, dtype=float))
        p = np.asarray(self.camera.projection_matrix, dtype=float)
        reach = max(float((self._focus - position) @ forward), 1.0)
        out = {"eye": tuple(map(float, position)), "target": tuple(map(float, position + forward * reach)),
               "up": tuple(map(float, up))}
        if self.is_ortho():
            out.update(fov=0.0, height=2.0 / max(abs(float(p[1, 1])), 1e-9))
        else:
            out.update(fov=math.degrees(2.0 * math.atan(1.0 / max(abs(float(p[1, 1])), 1e-9))), height=0.0)
        return out

    def camera_snapshot(self):
        """Where the camera is, to come back to it (a view's tab: see restore_camera)."""
        cam = self.camera
        return {"position": tuple(cam.local.position), "rotation": tuple(cam.local.rotation), "fov": cam.fov,
                "width": cam.width, "height": cam.height, "zoom": cam.zoom, "focus": self._focus.copy()}

    def restore_camera(self, state):
        """The camera as camera_snapshot left it (a view of the same kind: with or without perspective)."""
        cam = self.camera
        if (state["fov"] == 0) != self.is_ortho():
            return
        cam.local.position = state["position"]
        cam.local.rotation = state["rotation"]
        cam.width, cam.height, cam.zoom = state["width"], state["height"], state["zoom"]
        self._set_focus(state["focus"])
        self.redraw()

    def is_ortho(self):
        """Seen without perspective (a plan, a section, the 3D view as an axonometry)."""
        return self.camera.fov == 0

    def ortho_height(self):
        """World size (m) shown from the bottom of the view to its top, without perspective."""
        return self.world_per_pixel(self._focus) * self.logical_size()[1]

    def _set_ortho_height(self, height):
        height = float(min(max(height, ORTHO_MIN), ORTHO_MAX))
        self.camera.width = self.camera.height = height       # (pygfx widens it to the window's shape)
        self.camera.zoom = 1.0

    def _frame_ortho(self, center, radius, forward):
        """A plan / section: looking along `forward` without perspective, `radius` round `center` in view
        (the camera well outside the model, so its near plane cuts nothing)."""
        center = np.asarray(center, dtype=float)
        self.camera.local.position = tuple(center - forward * (radius * 4.0 + 10.0))
        self.camera.show_pos(tuple(center), up=(0, 0, 1))
        self._set_ortho_height(2.0 * radius * 1.15)
        self._set_focus(center)

    def set_camera(self, position, direction, up=(0.0, 0.0, 1.0), fov=None):
        """Look from `position` along `direction` (a note's camera); what is in front, about 10 m
        away or the model's middle, becomes the focus."""
        position, direction = np.asarray(position, dtype=float), normalize(np.asarray(direction, dtype=float))
        if fov:
            self.camera.fov = float(min(max(fov, 20.0), 90.0))
        center, radius = self.scene_bounds()
        ahead = max(float((center - position) @ direction), 1.0) if radius > 0 else 10.0
        target = position + direction * ahead
        self.camera.local.position = tuple(position)
        self.camera.show_pos(tuple(target), up=tuple(up))
        self._set_focus(target)
        self.redraw()

    def look_at(self, eye, target, up=(0.0, 0.0, 1.0)):
        """(0.364) The camera at `eye` looking at `target`, nothing else measured — a frame of a camera move played
        (set_camera measures the model each time)."""
        self.camera.local.position = tuple(float(c) for c in eye)
        self.camera.show_pos(tuple(float(c) for c in target), up=tuple(up))
        self._set_focus(target)
        self.redraw()

    def snapshot(self):
        """The last image drawn: (height, width, 4) RGBA bytes (a note's picture)."""
        return np.ascontiguousarray(self.renderer.snapshot())

    # ------------------------------------------------------------ the view cube and smooth turns (0.79)

    def set_cube(self, images):
        """The view cube, with its pictures ({name: RGBA}: the faces, the ring, the buttons — made by the window)."""
        from .viewcube import ViewCube
        self.cube = ViewCube(images)
        self.redraw()

    def cube_event(self, kind, x, y, button=None):
        """The mouse on the view cube (3D only): "down" / "move" / "up". True if the cube took it (the tool does
        not get it): a click there, a drag that started there, the mouse over it."""
        cube = self.cube
        if cube is None:
            return False
        size = self.logical_size()
        if self.cutting():
            self._cube_press = None
            return False
        if kind == "down":
            part = cube.hit(x, y, size) if button == 1 else None
            if part is None:
                return False
            self._cube_press = [float(x), float(y), part, False]
            return True
        if kind == "move":
            press = self._cube_press
            if press is not None:
                px, py, part, dragged = press
                if not dragged and abs(x - px) + abs(y - py) > 3 and part[0] in ("cube", "ring", "compass"):
                    press[3] = dragged = True
                    self._anim = None
                    self.remember_view()
                if dragged:
                    self._cube_drag(part, (px, py), (x, y))
                    press[0], press[1] = float(x), float(y)
                return True
            part = cube.hit(x, y, size)
            if cube.set_hover(part) | cube.set_active(cube.inside(x, y, size)):
                self.redraw()
            return part is not None
        if kind == "up":
            press, self._cube_press = self._cube_press, None
            if press is None:
                return False
            if not press[3]:
                self._cube_action(press[2], x, y)
            return True
        return False

    def _cube_drag(self, part, last, now):
        """Dragging the cube orbits round the model; dragging its ring turns the model round (a turntable)."""
        center, _radius = self.scene_bounds()
        if part[0] == "cube":
            self.orbit(now[0] - last[0], now[1] - last[1], center)
            return
        cx, cy = self.cube.center(self.logical_size())
        a0 = math.atan2(last[1] - cy, last[0] - cx)
        a1 = math.atan2(now[1] - cy, now[0] - cx)
        turn = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        # (the ring and the model follow the mouse round: seen from above, a clockwise drag turns the camera the
        # other way)
        self.turn_round(turn if self.view_direction()[2] < 0 else -turn, center)

    def turn_round(self, angle, pivot):
        """The camera turned `angle` radians round the vertical line through `pivot` (as the model on a turntable)."""
        cam = self.camera
        q = la.quat_from_axis_angle((0, 0, 1), angle)
        cam.local.rotation = la.quat_mul(q, np.asarray(cam.local.rotation, dtype=float))
        cam.local.position = tuple(np.asarray(pivot) + la.vec_transform_quat(self.camera_position() - pivot, q))
        self.redraw()

    def _cube_action(self, part, x, y):
        kind = part[0]
        if kind == "cube":
            self.look_from(part[1])
        elif kind == "compass":
            self.look_from_side(part[1])
        elif kind == "button":
            name = part[1]
            if name == "home":
                self.go_home()
            elif name == "menu":
                if self.on_cube_menu is not None:
                    self.on_cube_menu(x, y)
            elif name in ("roll_ccw", "roll_cw"):
                self.roll(math.pi / 2 if name == "roll_ccw" else -math.pi / 2)
            else:                                     # a triangle: the face next to the one seen
                up = np.asarray(self.camera.world.up, dtype=float)
                right = np.asarray(self.camera.world.right, dtype=float)
                way = {"up": up, "down": -up, "right": right, "left": -right}[name]
                axis = int(np.argmax(np.abs(way)))
                d = np.zeros(3)
                d[axis] = np.sign(way[axis])
                self.look_from(d, up=self._up_after(d))

    def _up_after(self, d):
        """Looking from above / below after a triangle: the side the camera came from stays at the bottom."""
        if abs(d[2]) < 0.5:
            return None
        f = self.view_direction()
        h = np.array((f[0], f[1], 0.0))
        return tuple(normalize(h)) if np.linalg.norm(h) > 1e-6 else None

    def _animate(self, change):
        """A camera change made smoothly: `change()` sets where the camera ends; it turns there in TURN_S."""
        self.remember_view()
        start = self.camera_snapshot()
        change()
        end = self.camera_snapshot()
        self.restore_camera(start)
        self._anim = (time.monotonic(), start, end)
        self.redraw()

    def look_from(self, direction, animate=True, up=None):
        """The camera on the side `direction` points to (from the model to the eye), framing the model;
        turning there smoothly. Seen from above / below, north is at the top unless `up` says otherwise."""
        d = normalize(np.asarray(direction, dtype=float))
        if up is None and abs(d[2]) > 0.999:          # straight from above / below: north stays up
            d = normalize(d + np.array((0.0, -1e-4, 0.0)))
            up = (0.0, 0.0, 1.0)
        center, radius = self.scene_bounds()

        def change():
            distance = radius / math.sin(math.radians(self.camera.fov or 45.0) / 2) * 1.15
            self.camera.local.position = tuple(center + d * distance)
            self.camera.show_pos(tuple(center), up=tuple(up or (0.0, 0.0, 1.0)))
            self._set_focus(center)

        if animate:
            self._animate(change)
        else:
            self.remember_view()
            change()
            self.redraw()

    def look_from_side(self, side):
        """A letter of the compass: looking from that side (N: from the north…), as high as before; seen from
        above, that side goes to the top of the view."""
        f = self.view_direction()
        eye = -f
        sx, sy = side
        if abs(eye[2]) > math.sin(math.radians(80)):
            self.look_from((0.0, 0.0, 1.0 if eye[2] > 0 else -1.0), up=(sx, sy, 0.0))
            return
        level = math.sqrt(max(1.0 - eye[2] ** 2, 0.0))
        self.look_from((sx * level, sy * level, eye[2]))

    def roll(self, angle):
        """The view turned `angle` radians round the line of sight (the roll arrows: 90°)."""
        forward = self.view_direction()

        def change():
            q = la.quat_from_axis_angle(tuple(forward), angle)
            self.camera.local.rotation = la.quat_mul(q, np.asarray(self.camera.local.rotation, dtype=float))

        self._animate(change)

    def go_home(self):
        """The house: the view set as the starting one (home_view: {"eye", "target"}), or the usual one."""
        home = self.home_view
        if not home:
            self.look_from(-normalize(VIEW_DIRS["iso"]))
            return
        eye, target = np.asarray(home["eye"], dtype=float), np.asarray(home["target"], dtype=float)

        def change():
            self.camera.local.position = tuple(eye)
            self.camera.show_pos(tuple(target), up=(0, 0, 1))
            if self.is_ortho():
                self._set_ortho_height(2.0 * float(np.linalg.norm(target - eye)) * math.tan(math.radians(22.5)))
            self._set_focus(target)

        self._animate(change)

    def home_from_here(self):
        """The view as it is now, as the starting one: {"eye", "target"} (the window keeps it with the 3D view)."""
        return {"eye": [float(c) for c in self.camera_position()], "target": [float(c) for c in self._focus]}

    def _step_animation(self):
        """A smooth turn in progress (look_from): the camera a step further, and another image asked for."""
        if self._anim is None:
            return
        t0, start, end = self._anim
        s = min((time.monotonic() - t0) / TURN_S, 1.0)
        s = s * s * (3 - 2 * s)                       # (eased at both ends)
        cam = self.camera
        cam.local.position = tuple(np.asarray(start["position"]) * (1 - s) + np.asarray(end["position"]) * s)
        q0, q1 = np.asarray(start["rotation"], float), np.asarray(end["rotation"], float)
        if q0 @ q1 < 0:
            q1 = -q1                                  # (the short way round)
        q = q0 * (1 - s) + q1 * s
        cam.local.rotation = tuple(q / np.linalg.norm(q))
        if s >= 1.0:
            self._anim = None
            self.restore_camera(end)
        else:
            self.redraw()

    # ------------------------------------------------------------ walking through (0.80)

    def _level_forward(self):
        f = self.view_direction()
        h = np.array((f[0], f[1], 0.0))
        return normalize(h) if np.linalg.norm(h) > 1e-6 else np.array((0.0, 1.0, 0.0))

    def place_eye(self, eye):
        """Position camera: the eye at `eye`, looking level the way the view looked."""
        self.remember_view()
        eye = np.asarray(eye, dtype=float)
        ahead = eye + self._level_forward() * 5.0
        self.camera.local.position = tuple(eye)
        self.camera.show_pos(tuple(ahead), up=(0, 0, 1))
        self._set_focus(ahead)
        self.redraw()

    def walk(self, forward, up, turn, collide=True):
        """Walk: `forward` m along the level direction looked at, `up` m up, then turn `turn` radians (right +),
        round the eye itself. With `collide` (0.83) the step stops in front of what is in the way (doors are
        walked through). True if it was stopped."""
        cam = self.camera
        eye = self.camera_position()
        way = self._level_forward() * (1.0 if forward >= 0 else -1.0)
        step = abs(forward)
        stopped = False
        if collide and step > 0:
            free = self.free_step(eye, way, step)
            stopped, step = free < step - 1e-9, free
        pos = eye + way * step + np.array((0.0, 0.0, up))
        cam.local.position = tuple(pos)
        if turn:
            q = la.quat_from_axis_angle((0, 0, 1), -turn)
            cam.local.rotation = la.quat_mul(q, np.asarray(cam.local.rotation, dtype=float))
        self._set_focus(pos + self.view_direction() * 5.0)
        self.redraw()
        return stopped

    def free_step(self, eye, way, length):
        """How far one can walk from `eye` along `way` (level, unit), up to `length`: what is shown in the way
        stops it (core/collide)."""
        from ..core import collide
        ids = set()
        for dz in collide.BODY_HEIGHTS:
            ids.update(self.snap_index.along(eye + np.array((0.0, 0.0, dz)), way, length + collide.BODY_RADIUS,
                                             collide.BODY_RADIUS))
        objects = [self.snap_index.objects[i] for i in ids if i in self.snap_index.objects]
        return collide.free_step(eye, way, length, [o for o in objects if self.is_shown(o)])

    # ------------------------------------------------------------ view history and zooms (0.78)

    def remember_view(self):
        """The camera as it is now goes on the Previous view list (a new move forgets the Next ones)."""
        snap = self.camera_snapshot()
        if self._back and _same_view(self._back[-1], snap):
            return
        self._back.append(snap)
        del self._back[:-VIEW_HISTORY]
        self._forward.clear()

    def _step_view(self, source, target):
        while source:
            snap = source.pop()
            if (snap["fov"] == 0) != self.is_ortho() or _same_view(snap, self.camera_snapshot()):
                continue                              # (another kind of view, or where it is already)
            target.append(self.camera_snapshot())
            self.restore_camera(snap)
            return True
        return False

    def view_back(self):
        """Vista anterior: the camera where it was before the last move. False if there is none."""
        return self._step_view(self._back, self._forward)

    def view_forward(self):
        """Vista seguinte: undoes a Vista anterior."""
        return self._step_view(self._forward, self._back)

    def zoom_to_region(self, x0, y0, x1, y1):
        """Zoom janela: what is inside the screen rectangle fills the view (the direction of view kept)."""
        w, h = self.logical_size()
        rw, rh = abs(x1 - x0), abs(y1 - y0)
        if rw < 4 and rh < 4:
            return False
        self.remember_view()
        p = self.point_under((x0 + x1) / 2, (y0 + y1) / 2)
        ratio = max(rw / max(w, 1), rh / max(h, 1))
        forward, pos = self.view_direction(), self.camera_position()
        along = float((p - pos) @ forward)
        if self.is_ortho():
            self.camera.local.position = tuple(p - forward * along)
            self._set_ortho_height(self.camera.height * ratio)
        else:
            self.camera.local.position = tuple(p - forward * max(along * ratio, 0.3))
        self._set_focus(p)
        self.redraw()
        return True

    def set_view(self, kind, center=None, radius=None):
        self.view_along(VIEW_DIRS[kind], center, radius)

    def view_along(self, forward, center=None, radius=None):
        """Looking along `forward` (set_view's directions, or (0.378) any level one: a wall seen square on, its profile
        edited), `radius` round `center` in view."""
        self.remember_view()
        if center is None or radius is None:
            center, radius = self.scene_bounds()
        forward = normalize(np.asarray(forward, dtype=float))
        if self.is_ortho():
            self._frame_ortho(center, radius, forward)
            self.redraw()
            return
        distance = radius / math.sin(math.radians(self.camera.fov) / 2) * 1.15
        self.camera.local.position = tuple(np.asarray(center) - forward * distance)
        self.camera.show_pos(tuple(center), up=(0, 0, 1))
        self._set_focus(center)
        self.redraw()

    def zoom_extents(self, ids=None):
        """Frame the whole model (or the objects `ids`), keeping the direction of view."""
        objects = None if ids is None else [o for o in (self.doc.get(i) for i in ids) if o is not None]
        box = self.bounds(objects or None)
        if ids is None:                                     # (the background images too, 0.154; CAD links, 0.158)
            pts = [(x, y, self.image_level(i)) for i in self.images_shown() for x, y in i.corners()]
            for _key, wobj in list(self._cad_objects.values()) + list(self._cloud_objects.values()):
                p = wobj.geometry.positions.data
                if len(p):
                    pts += [tuple(map(float, p.min(axis=0))), tuple(map(float, p.max(axis=0)))]
            if pts:
                pts = np.array(pts + ([] if box is None else [box[0], box[1]]), dtype=float)
                box = pts.min(axis=0), pts.max(axis=0)
        self.zoom_box(box)

    def zoom_box(self, box):
        """Frame the box (lowest, highest corner) — or the default view when None —, keeping the direction of
        view."""
        self.remember_view()
        forward = np.asarray(self.camera.world.forward, dtype=float)
        if box is None:
            center, radius = np.array((2.0, 2.0, 0.0)), 8.0
        else:
            lo, hi = np.asarray(box[0], dtype=float), np.asarray(box[1], dtype=float)
            center, radius = (lo + hi) / 2, max(np.linalg.norm(hi - lo) / 2, 1.0)
        if self.is_ortho():
            self._frame_ortho(center, radius, normalize(forward))
            self.redraw()
            return
        distance = radius / math.sin(math.radians(self.camera.fov) / 2) * 1.15
        self.camera.local.position = tuple(center - forward * distance)
        self._set_focus(center)
        self.redraw()

    def scene_bounds(self, objects=None):
        box = self.bounds(objects)
        if box is None:
            return np.array((2.0, 2.0, 0.0)), 8.0
        lo, hi = box
        return (lo + hi) / 2, max(np.linalg.norm(hi - lo) / 2, 1.0)

    def bounds(self, objects=None):
        """(lowest, highest) world corner of the objects (default: those shown), or None."""
        parts = []
        for obj in (self.shown_objects() if objects is None else objects):
            if obj.is_bim and hasattr(obj.mesh, "bounds"):
                box = obj.mesh.bounds()                  # kept with the mesh: no work per vertex here
                if box is not None:
                    parts += box
                continue
            v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
            if len(v):
                w = v @ obj.matrix[:3, :3].T + obj.matrix[:3, 3]
                parts += (w.min(axis=0), w.max(axis=0))
        if not parts:
            return None
        pts = np.array(parts)
        return pts.min(axis=0), pts.max(axis=0)

    def point_under(self, x, y):
        """World point under the cursor: a face, else the ground, else a point
        at the current viewing distance."""
        hit = self.pick_point(x, y)
        if hit is not None:
            return hit[2]
        origin, direction = self.ray(x, y)
        p = ray_plane(origin, direction, np.array((0.0, 0.0, self.doc.work_level())), np.array((0.0, 0.0, 1.0)))
        if p is not None and np.linalg.norm(p - origin) < 20000:
            return p
        return origin + direction * np.linalg.norm(self._focus - origin)

    def orbit(self, dx, dy, pivot):
        cam = self.camera
        rot = np.asarray(cam.local.rotation, dtype=float)
        right = la.vec_transform_quat((1, 0, 0), rot)
        q_az = la.quat_from_axis_angle((0, 0, 1), -dx * ORBIT_SPEED)
        q_el = la.quat_from_axis_angle(right, -dy * ORBIT_SPEED)
        q = la.quat_mul(q_az, q_el)
        forward = la.vec_transform_quat((0, 0, -1), la.quat_mul(q, rot))
        if abs(forward[2]) > 0.998:  # never flip over the top / under the ground
            q = q_az
        cam.local.rotation = la.quat_mul(q, rot)
        cam.local.position = tuple(pivot + la.vec_transform_quat(self.camera_position() - pivot, q))
        self.redraw()

    def pan(self, dx, dy):
        cam = self.camera
        wpp = self.world_per_pixel(self._focus)
        move = (-dx * np.asarray(cam.world.right) + dy * np.asarray(cam.world.up)) * wpp
        cam.local.position = tuple(self.camera_position() + move)
        self._focus = self._focus + move
        self.redraw()

    def zoom_at(self, x, y, wheel_dy):
        p = self.point_under(x, y)
        f = 2.0 ** (wheel_dy * ZOOM_SPEED)
        pos = self.camera_position()
        if self.is_ortho():
            # less (or more) of the drawing in view, the point under the cursor staying under it
            height = self.camera.height * f
            if not ORTHO_MIN <= height <= ORTHO_MAX:
                return
            forward = self.view_direction()
            rel = pos - p
            along = forward * float(rel @ forward)
            self.camera.local.position = tuple(p + along + (rel - along) * f)
            self._set_ortho_height(height)
            self._set_focus(p)
            self.redraw()
            return
        new_pos = p + (pos - p) * f
        if np.linalg.norm(new_pos - p) < 0.05:  # do not go through what we zoom into
            return
        self.camera.local.position = tuple(new_pos)
        self._set_focus(p)
        self.redraw()

    def _on_nav_event(self, event):
        if event.type == "wheel" or (event.type == "pointer_down" and event.button == MIDDLE):
            self._anim = None                             # (a smooth turn stops where it is)
        if event.type == "wheel":
            now = time.monotonic()
            if now - self._last_wheel > WHEEL_PAUSE_S:   # (a burst of turns is one step of the view history)
                self.remember_view()
            self._last_wheel = now
            self.zoom_at(event.x, event.y, event.dy)
        elif event.type == "pointer_down" and event.button == MIDDLE:
            now = time.monotonic()
            t0, x0, y0 = self._last_middle
            self._last_middle = (now, event.x, event.y)
            if now - t0 < DOUBLE_CLICK_S and abs(event.x - x0) + abs(event.y - y0) < 8:
                self._nav = None
                self._last_middle = (0.0, 0.0, 0.0)       # (a third press is not another double click)
                self.zoom_extents()                       # double click of the middle button: all (as AutoCAD)
                return
            self.remember_view()
            # the middle button orbits (SketchUp) or pans (Revit), Shift the other; a plan or section never
            # turns: it stays a drawing
            other = {"orbit": "pan", "pan": "orbit"}[self.middle_drag]
            mode = other if "Shift" in (event.modifiers or ()) else self.middle_drag
            if self.cutting():
                mode = "pan"
            pivot = self.point_under(event.x, event.y)
            self._set_focus(pivot)
            self._nav = (mode, (event.x, event.y), pivot)
        elif event.type == "pointer_move" and self._nav is not None:
            mode, (x0, y0), pivot = self._nav
            dx, dy = event.x - x0, event.y - y0
            self.orbit(dx, dy, pivot) if mode == "orbit" else self.pan(dx, dy)
            self._nav = (mode, (event.x, event.y), pivot)
        elif event.type == "pointer_up" and event.button == MIDDLE:
            self._nav = None

    # ------------------------------------------------------------ screen <-> world

    def logical_size(self):
        return self.canvas.get_logical_size()

    def _unproject(self, nx, ny, depth):
        """World point at normalised screen coordinates (nx, ny) and depth (0: near plane, 1: far)."""
        p = np.linalg.inv(self.camera.camera_matrix) @ np.array((nx, ny, depth, 1.0))
        return p[:3] / p[3]

    def ray(self, x, y):
        """World-space ray (origin, unit direction) under the pixel (x, y). Without perspective
        every ray is parallel: it starts on the near plane, under the pixel."""
        w, h = self.logical_size()
        nx, ny = 2.0 * x / w - 1.0, 1.0 - 2.0 * y / h
        if self.is_ortho():
            near = self._unproject(nx, ny, 0.0)
            return near, normalize(self._unproject(nx, ny, 1.0) - near)
        origin = np.array(self.camera.world.position, dtype=float)
        return origin, normalize(self._unproject(nx, ny, 0.5) - origin)

    def project(self, point):
        """World point -> (x, y) logical pixels."""
        return tuple(self.project_many(np.asarray(point, dtype=float).reshape(1, 3))[0])

    def project_many(self, points):
        """(N, 3) world points -> (N, 2) logical pixels; NaN for points behind the camera."""
        w, h = self.logical_size()
        pts = np.asarray(points, dtype=float).reshape(-1, 3)
        clip = np.column_stack((pts, np.ones(len(pts)))) @ np.asarray(self.camera.camera_matrix, dtype=float).T
        with np.errstate(divide="ignore", invalid="ignore"):
            ndc = clip[:, :2] / clip[:, 3:4]
        xy = np.column_stack(((ndc[:, 0] + 1) / 2 * w, (1 - ndc[:, 1]) / 2 * h))
        xy[clip[:, 3] <= 1e-9] = np.nan
        return xy

    def world_per_pixel(self, point):
        w, h = self.logical_size()
        if self.is_ortho():                   # (the same everywhere)
            return float(np.linalg.norm(self._unproject(0.0, 2.0 / max(h, 1), 0.5) - self._unproject(0.0, 0.0, 0.5)))
        dist = np.linalg.norm(np.asarray(point) - self.camera_position())
        return 2 * dist * math.tan(math.radians(self.camera.fov) / 2) / max(h, 1)

    def pick(self, x, y):
        """(obj_id, face_index) under the pixel, read from the GPU pick buffer."""
        info = self.renderer.get_pick_info((x, y))
        wobj = info.get("world_object") if info else None
        if wobj is None:
            return None
        hit = self.bim.pick(wobj, info.get("face_index"))    # an IFC element, in a batch
        if hit is not None:
            return hit
        obj_id = self._by_wobj.get(id(wobj))
        if obj_id is None or obj_id not in self._views:
            return None
        tri = info.get("face_index")
        owner = self._views[obj_id].tri_owner
        if tri is None or not 0 <= tri < len(owner):
            return None
        return obj_id, int(owner[tri])

    def pick_point(self, x, y):
        """(obj_id, face_index, world point) of the displayed face under the pixel, or None."""
        hit = self.pick(x, y)
        if hit is None or hit[0] not in self._meshes:
            return None
        mesh, matrix = self._meshes[hit[0]]
        n = face_world_normal(matrix, mesh, hit[1])
        p0 = transform_point(matrix, mesh.verts[mesh.faces[hit[1]][0]])
        origin, direction = self.ray(x, y)
        p = ray_plane(origin, direction, p0, n)
        if p is None:
            p = ray_plane(origin, direction, p0, -n)
        if p is None:
            return None
        return hit[0], hit[1], p

    def snap(self, x, y):
        """Inference under the cursor: (Snap or None, face hit (obj_id, face, point) or None).
        Only the objects near the view ray are looked at (SnapIndex)."""
        origin, direction = self.ray(x, y)
        if self.is_ortho():
            slope, pixel = 0.0, self.world_per_pixel(self._focus)
        else:
            slope, pixel = 2 * math.tan(math.radians(self.camera.fov) / 2) / max(self.logical_size()[1], 1), 0.0
        geom = self.snap_index.geometry(origin, direction, slope, shown=self.is_shown,
                                        guides=[(g.point, g.direction) for g in self.doc.guides.values()]
                                        + self.grid_guides(), keep=self.kept_planes(), pixel=pixel)
        hit = self.pick_point(x, y)
        face = None
        if hit is not None:
            mesh, matrix = self._meshes[hit[0]]
            face = (hit[0], hit[2], face_world_normal(matrix, mesh, hit[1]))
        snap = find_snap(geom, (x, y), self.project_many, origin, direction, hit=face)
        if snap is not None and self.plan:
            # in a plan one draws on the storey: what is found is brought down to its level
            level = self.doc.work_level()
            snap.point = np.array((snap.point[0], snap.point[1], level))
            if snap.edge is not None:
                snap.edge = tuple(np.array((p[0], p[1], level)) for p in snap.edge)
        return snap, hit

    def nearby_points(self, x, y, radius_px=AUTO_ALIGN_PX, most=AUTO_ALIGN_MOST):
        """The corners of what is drawn within `radius_px` of the cursor on screen (the nearest `most`):
        the points the cursor lines up with by itself (0.61, Revit's alignment lines). In a plan, on its level."""
        origin, direction = self.ray(x, y)
        if self.is_ortho():
            slope, pixel = 0.0, self.world_per_pixel(self._focus)
        else:
            slope, pixel = 2 * math.tan(math.radians(self.camera.fov) / 2) / max(self.logical_size()[1], 1), 0.0
        ids = [i for i in self.snap_index.near(origin, direction, slope, radius_px, pixel)
               if self.is_shown(self.snap_index.objects[i])]
        keep = self.kept_planes()
        corners = []
        for i in ids:
            block = self.snap_index.block(i)
            corners.append(block.corners if not keep else _kept_corners(block.corners, keep))
        pts = np.concatenate(corners) if corners else np.zeros((0, 3))
        if not len(pts):
            return pts
        if self.plan:
            pts = np.column_stack((pts[:, :2], np.full(len(pts), self.doc.work_level())))
        pts = np.unique(np.round(pts, 6), axis=0)
        xy = self.project_many(pts)
        dist = np.hypot(xy[:, 0] - x, xy[:, 1] - y)
        ok = np.flatnonzero(np.nan_to_num(dist, nan=np.inf) <= radius_px)
        return pts[ok[np.argsort(dist[ok])][:most]]

    # ------------------------------------------------------------ document objects

    def _on_document_changed(self, changed, removed):
        if GUIDES_CHANGED in changed:
            self._show_guides()
        if self.bim.shadows and (changed or removed):
            self._place_sun()                          # (0.315: the sun's shadows over the whole model, as it is now)
        split, by_phase = self._split_classes(), self._split_by_phase()
        if split != self._split or by_phase != self._split_phases:   # templates hide other things: batches change
            moved = split ^ self._split
            every = by_phase != self._split_phases
            self._split, self._split_phases = split, by_phase
            for obj_id in list(self.bim.where):
                obj = self.doc.get(obj_id)
                if obj is not None and (every or obj.ifc_class in moved):
                    self.show_object(obj_id, obj.mesh)
        if STOREY_CHANGED in changed:
            # (the IFC of a file shown from its kept shapes is read: its doors may have plan symbols)
            for obj_id, batch in list(self.bim.where.items()):
                obj = self.doc.get(obj_id)
                if obj is not None and obj.ifc_class == "IfcDoor" and batch.key != self._batch_key(obj):
                    self.show_object(obj_id, obj.mesh)
        for obj_id in [i for i in self.face_selection if i in removed or i in changed]:
            del self.face_selection[obj_id]        # (its faces numbered again: the faces picked alone let go)
        for obj_id in [i for i in self.line_selection if i in removed or i in changed]:
            del self.line_selection[obj_id]        # (0.373: its lines numbered again, as the faces)
        rejoined = self._update_seams(changed, removed)        # (0.320: before they are shown, with their seams)
        for obj_id in removed:
            self._remove_view(obj_id)
            self.snap_index.remove(obj_id)
        for obj_id in changed:
            obj = self.doc.get(obj_id)
            if obj is not None:
                self.show_object(obj_id, obj.mesh)
                self.snap_index.update(obj)        # only this object's candidates are made again
        for obj_id in rejoined - set(changed):     # (their neighbours whose seams changed with them)
            obj = self.doc.get(obj_id)
            if obj is not None and obj_id in self.bim.where:
                self.show_object(obj_id, obj.mesh)
        self._recheck_sheets(changed, removed)
        if len(changed) > 500:
            self.snap_index.prepare()              # a file was opened: ready before the first mouse move
        self.selection &= set(self.doc.objects)
        self.apply_storey_view()      # storey levels may have moved (cheap: no geometry rebuilt)
        self.redraw()

    # ------------------------------------------------------------ storeys

    def is_shown(self, obj):
        """False for objects of other storeys when only the active storey is shown (always
        in a plan), and for elements of the classes the view hides (its view template).
        Sketches belong to the storey band their lowest point is in."""
        if obj is not None and obj.is_bim and obj.ifc_class in self.hidden_classes:
            return False
        if obj is not None and obj.is_bim and self.hidden_phases and obj.ifc_class != "CAD" and \
                (self.doc.status_of(obj.id) or "") in self.hidden_phases:
            return False
        if not (self.only_active_storey or self.plan) or obj is None:
            return True
        active = self.doc.active_storey
        if obj.is_bim:
            return obj.storey is None or obj.storey == active or (self.plan and obj.storey in self._deep_storeys())
        v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
        if not len(v):
            return True
        zmin = float((v @ obj.matrix[:3, :3].T + obj.matrix[:3, 3])[:, 2].min())
        lo, hi = self.doc.storey_band(active)
        return lo - 1e-6 <= zmin < hi - 1e-6

    def shown_objects(self):
        return [o for o in self.doc.objects.values() if self.is_shown(o)]

    def cut_level(self):
        """Where a plan cuts: cut_height (CUT_HEIGHT, or the view template's) above the active storey's level."""
        return self.doc.work_level() + self.cut_height

    def set_view_settings(self, hidden_classes=(), cut_height=CUT_HEIGHT, hidden_phases=(), depth=0.0, crop=None):
        """A view template's settings for the view shown: IFC classes hidden, a plan's cut height,
        phases hidden ("" for the elements without one); a plan's view depth (m below its storey's
        level: the storeys down to there are seen too) and crop region (x0, y0, x1, y1) (0.65)."""
        self.hidden_classes = set(hidden_classes)
        self.hidden_phases = set(hidden_phases)
        self.cut_height = float(cut_height)
        self.view_depth = float(depth or 0.0)
        self.crop = tuple(float(c) for c in crop) if crop else None
        if self.cutting():
            self._cut_view()
        else:
            self.apply_storey_view()

    def _show_grid(self):
        """The structural grid (0.67): each axis a dash-dot line at the active storey's level, with a bubble
        and its tag at both ends — over everything in a plan (as on a drawing), under the walls in 3D. The
        axes selected (0.72) in the selection's colour, thicker."""
        for wobj in self._grid_objects:
            self.scene.remove(wobj)
        self._grid_objects = []
        axes = getattr(self.doc, "grids", [])
        self.selected_axes = {k for k in self.selected_axes if k < len(axes)}
        if not axes or self.section is not None:
            self.redraw()
            return
        z = self.grid_level()
        overlay = dict(depth_test=False, depth_write=False, render_queue=OVERLAY_QUEUE) if self.plan else {}
        drawn = {False: ([], []), True: ([], [])}          # selected? -> (segments, bubble rings)
        for k, axis in enumerate(axes):
            a, b = np.array((*axis.start, z)), np.array((*axis.end, z))
            d = b - a
            if np.linalg.norm(d) < 1e-9:
                continue
            d = d / np.linalg.norm(d)
            selected = k in self.selected_axes
            segs, rings = drawn[selected]
            segs += [a, b]
            r = self.grid_bubble()
            for end, out in ((a, -d), (b, d)):
                centre = end + out * r
                ring = [centre + r * np.array((math.cos(j * math.pi / 12), math.sin(j * math.pi / 12), 0.0))
                        for j in range(25)]
                rings += [p for pair in zip(ring, ring[1:]) for p in pair]
                label = gfx.Text(text=axis.tag, font_size=13, screen_space=True, anchor="middle-center",
                                 material=_mat(gfx.TextMaterial, color=EDGE_SELECTED if selected else GRID_COLOR, **overlay))
                label.local.position = tuple(float(c) for c in centre)
                self._grid_objects.append(label)
        for selected, (segs, rings) in drawn.items():
            if not segs:
                continue
            colour, width = (EDGE_SELECTED, 2.4) if selected else (GRID_COLOR, 1.2)
            self._grid_objects.append(gfx.Line(gfx.Geometry(positions=_f32(segs)), _mat(gfx.LineSegmentMaterial,
                thickness=width, color=colour, dash_pattern=(10, 3, 2, 3), aa=True, **overlay)))
            self._grid_objects.append(gfx.Line(gfx.Geometry(positions=_f32(rings)), _mat(gfx.LineSegmentMaterial,
                thickness=width, color=colour, aa=True, **overlay)))
        for wobj in self._grid_objects:
            self.scene.add(wobj)
        if self.plan:
            self._clip(*[w.material for w in self._grid_objects])
        self.redraw()

    # ------------------------------------------------------------ rooms (0.99)

    def _rooms_here(self):
        """The rooms of the active storey (space_info), when a plan is shown; [] otherwise."""
        if not self.plan or self.doc.loading or not hasattr(self.doc.ifc, "spaces"):
            return []                                       # (while a file is read its IFC is not there yet)
        try:
            return self.doc.ifc.spaces(self.doc.active_storey)
        except Exception:                                   # (a file whose spaces this program does not read)
            return []

    def _show_rooms(self):
        """A plan's rooms: a light fill on the floor (under the walls), the outline, and a label — its name, number
        and area — over everything; the rooms selected in the selection's colour."""
        for wobj in getattr(self, "_room_objects", []):
            self.scene.remove(wobj)
        self._room_objects = []
        self._room_shapes = []
        reading = self.doc.loading or not hasattr(self.doc.ifc, "by_guid")
        self.selected_rooms = set() if reading else {g for g in getattr(self, "selected_rooms", set())
                                                     if self.doc.ifc.by_guid(g) is not None}
        infos = self._rooms_here()
        if not infos:
            self.redraw()
            return
        import shapely
        from shapely.geometry import Polygon
        from ..core.rooms import label_point
        tris, colors, segs = [], [], []
        for info in infos:
            poly = Polygon(info["outline"], info["holes"])
            if poly.is_empty or not poly.is_valid:
                continue
            self._room_shapes.append((info["guid"], poly))
            selected = info["guid"] in self.selected_rooms
            if selected:
                colour = _physical(ROOM_SELECTED)
            elif views_canvas.DARK:
                colour = _physical_in(ROOM_FILL_DARK, False)       # (0.341: its own on the dark views)
            else:
                colour = _physical(ROOM_FILL)
            z = info["level"] + ROOM_LIFT
            for tri in shapely.constrained_delaunay_triangles(poly).geoms:
                pts = list(tri.exterior.coords)[:3]
                tris += [(x, y, z) for x, y in pts]
                colors += [colour] * 3
            for ring in [info["outline"]] + info["holes"]:
                for a, b in zip(ring, ring[1:] + ring[:1]):
                    segs += [(a[0], a[1], z), (b[0], b[1], z)]
            x, y = label_point(poly)
            text = "{} {}\n{}".format(info["name"], info["number"], ROOM_AREA.format(info["area"]).replace(".", ","))
            label = gfx.Text(text=text, font_size=12, screen_space=True, anchor="middle-center",
                             material=_mat(gfx.TextMaterial, color=EDGE_SELECTED if selected else "#2a3340",
                                                       outline_color="#ffffff", outline_thickness=0.3,
                                                       depth_test=False, depth_write=False,
                                                       render_queue=OVERLAY_QUEUE))
            label.local.position = (x, y, z)
            self._room_objects.append(label)
        if tris:
            fill = gfx.Mesh(gfx.Geometry(positions=_f32(tris), colors=np.array(colors, np.float32),
                                         indices=np.arange(len(tris), dtype=np.uint32).reshape(-1, 3)),
                            _mat(gfx.MeshBasicMaterial, color_mode="vertex", side="both", alpha_mode="blend",
                                                  depth_write=False))
            self._room_objects.append(fill)
        if segs:
            self._room_objects.append(gfx.Line(gfx.Geometry(positions=_f32(segs)), _mat(gfx.LineSegmentMaterial,
                thickness=1.0, color=ROOM_LINE, aa=True, depth_write=False)))
        for wobj in self._room_objects:
            self.scene.add(wobj)
        self._clip(*[w.material for w in self._room_objects])
        self.redraw()

    # ------------------------------------------------------------ CAD drawings linked (0.158)

    def cad_shown(self):
        """The CAD links drawn now: visible ones — in a plan (or showing only the active storey) those of its
        storey."""
        only = self.only_active_storey or self.plan
        storeys = {g for g, _n, _z in self.doc.storeys()}
        return [c for c in getattr(self.doc, "cad_links", ()) if c.visible
                and (not only or c.storey == self.doc.active_storey or c.storey not in storeys)]

    def _show_cad(self):
        """Each link's layers shown as thin lines just over its storey's floor — made again only when the link,
        its file or its level changed."""
        from ..model import cad_links as cad_model
        wanted = {}
        for link in self.cad_shown():
            level = self.image_level(link)
            try:
                stamp = os.path.getmtime(link.path)
            except OSError:
                stamp = None
            wanted[link.uid] = (link, (cad_model.to_dict(link).__repr__(), level, stamp))
        from .cad_snap import CadSnapObject
        for uid in list(self._cad_objects):
            key, wobj = self._cad_objects[uid]
            if uid not in wanted or wanted[uid][1] != key:
                self.scene.remove(wobj)
                self.snap_index.remove("cad:" + uid)
                del self._cad_objects[uid]
        for uid, (link, key) in wanted.items():
            if uid in self._cad_objects:
                continue
            segs = cad_model.placed_segments(link)
            if not segs:
                continue
            every = np.concatenate(list(segs.values()))
            pts = np.column_stack((every.reshape(-1, 2), np.full(len(every) * 2, key[1] + CAD_LIFT)))
            wobj = gfx.Line(gfx.Geometry(positions=_f32(pts)),
                            _mat(gfx.LineSegmentMaterial, thickness=1.0, color=CAD_COLOR, aa=True, depth_write=False))
            self._cad_objects[uid] = (key, wobj)
            self.scene.add(wobj)
            self.snap_index.update(CadSnapObject(uid, every, key[1], link.storey))   # (the tools snap to it)
        self._clip(*[w.material for _k, w in self._cad_objects.values()])

    # ------------------------------------------------------------ the analytical model (0.163)

    def set_show_analytical(self, on):
        self.show_analytical = bool(on)
        self._show_analytical()
        self.redraw()

    DIAGRAM_SIZE = 1.0              # m (0.220): the largest moment drawn this far from its member

    def show_diagrams(self, diagrams=None):
        """(0.220) The members' bending moment diagrams over the model — each moment drawn square to its member, on
        the side its tension is (a sagging moment below a beam), the largest DIAGRAM_SIZE out, closed to the member
        by lines; each member's largest value written. diagrams: Analysis.diagrams; None: none shown."""
        for wobj in getattr(self, "_diagram_objects", []):
            self.scene.remove(wobj)
        self._diagram_objects = []
        if diagrams:
            top = max((abs(m) for *_rest, ms in diagrams.values() for m in ms), default=0.0)
            scale = self.DIAGRAM_SIZE / top if top > 1e-9 else 0.0
            segs = []
            for p1, p2, zdir, ms in diagrams.values():
                p1, p2, zdir = np.asarray(p1, float), np.asarray(p2, float), np.asarray(zdir, float)
                pts = [p1 + (p2 - p1) * k / (len(ms) - 1) for k in range(len(ms))]
                curve = [p - zdir * m * scale for p, m in zip(pts, ms)]
                segs += [q for a, b in zip(curve[:-1], curve[1:]) for q in (a, b)]
                segs += [q for p, c in zip(pts, curve) for q in (p, c)]      # (the hatch: back to the member)
                k = int(np.argmax([abs(m) for m in ms]))
                if abs(ms[k]) > 1e-6:
                    label = gfx.Text(text="{:.1f}".format(ms[k]).replace(".", decimal_sep()), font_size=12,
                                     screen_space=True, anchor="middle-center",
                                     material=_mat(gfx.TextMaterial, color="#a8321e", outline_color="#ffffff",
                                                               outline_thickness=0.3))
                    label.local.position = tuple(float(c) for c in curve[k])
                    self._diagram_objects.append(label)
            if segs:
                line = gfx.Line(gfx.Geometry(positions=_f32(segs)),
                                _overlay_material(gfx.LineSegmentMaterial, thickness=1.6, color="#c0392b", aa=True))
                self._diagram_objects.append(line)
            for wobj in self._diagram_objects:
                self.scene.add(wobj)
        self.redraw()

    def _show_analytical(self):
        """The analytical model over everything, as Revit draws it: the columns' axes orange, the beams' blue, the
        slabs' outlines green, the supports a small square at their node — not hidden by the model."""
        for wobj in self._analytical_objects:
            self.scene.remove(wobj)
        self._analytical_objects = []
        if not self.show_analytical or self.doc.loading or not hasattr(self.doc.ifc, "analytical_lines"):
            return
        try:
            lines, supports, panels = self.doc.ifc.analytical_lines()
        except Exception:                                   # (an IFC whose analytical model this program cannot read)
            return
        groups = {"column": [], "beam": []}
        for kind, a, b in lines:
            groups.get(kind, groups["beam"]).extend([a, b])
        outline = []
        for ring in panels:
            for k in range(len(ring)):
                outline += [ring[k], ring[(k + 1) % len(ring)]]
        marks = []
        for p, kind in supports:
            r = 0.25 if kind == "fixed" else 0.18
            c = [p + (dx, dy, 0.0) for dx, dy in ((-r, -r), (r, -r), (r, r), (-r, r))]
            marks += [c[0], c[1], c[1], c[2], c[2], c[3], c[3], c[0]]
        for segs, colour, width in ((groups["column"], "#e07b1f", 3.0), (groups["beam"], "#1f6fe0", 3.0),
                                    (outline, "#3a9a4a", 1.5), (marks, "#b0302a", 2.5)):
            if not segs:
                continue
            wobj = gfx.Line(gfx.Geometry(positions=_f32(segs)),
                            _overlay_material(gfx.LineSegmentMaterial, thickness=width, color=colour, aa=True))
            self._analytical_objects.append(wobj)
            self.scene.add(wobj)

    # ------------------------------------------------------------ point clouds linked (0.161)

    def clouds_shown(self):
        only = self.only_active_storey or self.plan
        storeys = {g for g, _n, _z in self.doc.storeys()}
        return [c for c in getattr(self.doc, "cloud_links", ()) if c.visible
                and (not only or c.storey == self.doc.active_storey or c.storey not in storeys)]

    def _show_clouds(self):
        """Each cloud's points (thinned to what the screen shows), in their colours — or by their height when the
        scan has none —; in a plan only those under its cut (the clipping takes the rest: a slice of the scan)."""
        from ..model import cloud_links as cloud_model
        wanted = {}
        for link in self.clouds_shown():
            try:
                stamp = os.path.getmtime(link.path)
            except OSError:
                stamp = None
            wanted[link.uid] = (link, (repr(cloud_model.to_dict(link)), stamp))
        for uid in list(self._cloud_objects):
            key, wobj = self._cloud_objects[uid]
            if uid not in wanted or wanted[uid][1] != key:
                self.scene.remove(wobj)
                del self._cloud_objects[uid]
        for uid, (link, key) in wanted.items():
            if uid in self._cloud_objects:
                continue
            cloud = cloud_model.cloud_of(link.path)
            if cloud is None or not len(cloud):
                continue
            pts = link.place(cloud.points)
            if cloud.colours is not None:
                colours = np.column_stack((cloud.colours, np.ones(len(pts), np.float32)))
            else:                                           # (by height: blue low, then green, yellow, red high)
                z = pts[:, 2]
                f = (z - z.min()) / max(float(np.ptp(z)), 1e-9)
                colours = np.column_stack((np.clip(2 * f - 0.5, 0, 1), np.clip(1.5 - np.abs(2 * f - 1) * 1.5, 0, 1),
                                           np.clip(1 - 2 * f, 0, 1), np.ones(len(f))))
            wobj = gfx.Points(gfx.Geometry(positions=_f32(pts), colors=np.asarray(colours, np.float32)),
                              _mat(gfx.PointsMaterial, size=float(link.size), color_mode="vertex"))
            self._cloud_objects[uid] = (key, wobj)
            self.scene.add(wobj)
        self._clip(*[w.material for _k, w in self._cloud_objects.values()])

    # ------------------------------------------------------------ terrains (0.155)

    def terrain_contours(self, obj):
        """A terrain's contour lines: [(height, segments (K, 2, 3), major)] — made once for each shape and
        interval."""
        from ..core import terrain as terrain_geo
        try:
            interval = float(self.doc.ifc.terrain_interval(obj.id))
        except Exception:                                   # (the IFC still being read; not made by this program)
            interval = terrain_geo.DEFAULT_INTERVAL
        key = (id(obj.mesh), interval)
        found = self._contour_cache.get(obj.id)
        if found is None or found[0] != key:
            mesh = obj.mesh
            surface = terrain_geo.surface_of(mesh.verts, mesh.tris, mesh.normals)
            lines = [(h, segs, terrain_geo.is_major(h, interval))
                     for h, segs in terrain_geo.contours(mesh.verts, surface, interval)]
            self._contour_cache[obj.id] = found = (key, lines)
        return found[1]

    LABEL_EVERY, LABEL_SHORTEST = 20.0, 2.0          # m (0.202): the major contour lines' heights on screen

    def terrain_labels(self, obj):
        """(0.202) Its major contour lines' heights as written over them on screen: [(where (3,), text)] — made once
        for each shape and interval, as the lines."""
        from ..core import terrain as terrain_geo
        lines = self.terrain_contours(obj)
        found = self._label_cache.get(obj.id)
        if found is None or found[0] is not lines:
            spots = []
            for h, segs, big in lines:
                if big:
                    words = terrain_geo.contour_text(h, decimal_sep())
                    spots += [(np.array((p[0], p[1], h)), words) for line in terrain_geo.chains(segs)
                              for p, _a in terrain_geo.label_spots(line, self.LABEL_EVERY, self.LABEL_SHORTEST)]
            self._label_cache[obj.id] = found = (lines, spots)
        return found[1]

    def _show_contours(self):
        """The terrains' contour lines over their surface — the major ones (every fifth) thicker; in a plan only
        those under its cut (the clipping takes the rest)."""
        for wobj in self._contour_objects:
            self.scene.remove(wobj)
        self._contour_objects = []
        minor, major = [], []
        lift = np.array((0.0, 0.0, CONTOUR_LIFT))
        for obj in self.doc.objects.values():
            if not obj.is_bim or obj.ifc_class != TERRAIN_CLASS or not self.is_shown(obj):
                continue
            for _h, segs, big in self.terrain_contours(obj):
                (major if big else minor).append(segs.reshape(-1, 3) + lift)
            for where, words in self.terrain_labels(obj):                  # (their heights, 0.202)
                label = gfx.Text(text=words, font_size=11, screen_space=True, anchor="middle-center",
                                 material=_mat(gfx.TextMaterial, color=CONTOUR_COLOR, outline_color="#ffffff",
                                                           outline_thickness=0.35))
                label.local.position = tuple(float(c) for c in where + lift)
                self._contour_objects.append(label)
                self.scene.add(label)
        for parts, width in ((minor, 1.0), (major, 2.2)):
            if parts:
                line = gfx.Line(gfx.Geometry(positions=_f32(np.concatenate(parts))),
                                _mat(gfx.LineSegmentMaterial, thickness=width, color=CONTOUR_COLOR, aa=True))
                self._contour_objects.append(line)
                self.scene.add(line)
        if self.show_slopes:
            self._show_slope_colours()
        self._show_platforms()
        self._clip(*[w.material for w in self._contour_objects])

    def _show_platforms(self):
        """(0.157) The terrains' platforms: their outline at their height, and the height written in the middle."""
        segs = []
        for obj in self.doc.objects.values():
            if not obj.is_bim or obj.ifc_class != TERRAIN_CLASS or not self.is_shown(obj):
                continue
            try:
                platforms = self.doc.ifc.terrain_platforms(obj.id)
            except Exception:                               # (the IFC being read)
                platforms = []
            for plat in platforms:
                from ..model import drawings as drawings_model
                heights = plat.heights(np.array(plat.outline, dtype=float)) + CONTOUR_LIFT      # (a ramp's: 0.205)
                ring = [np.array((x, y, h)) for (x, y), h in zip(plat.outline, heights)]
                z = float(np.mean(heights))
                for k in range(len(ring)):
                    segs += [ring[k], ring[(k + 1) % len(ring)]]
                label = gfx.Text(text=drawings_model.platform_text(plat), font_size=13, screen_space=True,
                                 anchor="middle-center",
                                 material=_mat(gfx.TextMaterial, color="#3d3426", outline_color="#ffffff",
                                                           outline_thickness=0.3))
                centre = np.mean(np.array(plat.outline, dtype=float), axis=0)
                label.local.position = (float(centre[0]), float(centre[1]), z)
                self._contour_objects.append(label)
                self.scene.add(label)
        if segs:
            line = gfx.Line(gfx.Geometry(positions=_f32(segs)),
                            _mat(gfx.LineSegmentMaterial, thickness=2.0, color="#3d3426", aa=True))
            self._contour_objects.append(line)
            self.scene.add(line)
        slopes = [s for obj in self.doc.objects.values()                 # (their slopes' lines and ticks, 0.203)
                  if obj.is_bim and obj.ifc_class == TERRAIN_CLASS and self.is_shown(obj)
                  for s in self.terrain_batters(obj)]
        if slopes:
            line = gfx.Line(gfx.Geometry(positions=_f32(np.concatenate(slopes).reshape(-1, 3)
                                                         + (0.0, 0.0, CONTOUR_LIFT))),
                            _mat(gfx.LineSegmentMaterial, thickness=1.2, color="#3d3426", aa=True))
            self._contour_objects.append(line)
            self.scene.add(line)

    def terrain_batters(self, obj):
        """(0.203) A terrain's platforms' slopes — the lines where they meet the ground and their ticks, [(K, 2, 3)] —
        made once for each shape."""
        from ..model import drawings as drawings_model
        found = self._batter_cache.get(obj.id)
        if found is None or found[0] != id(obj.mesh):
            parts = [s for lines, ticks in drawings_model.terrain_batters(self.doc, obj.id)
                     for s in (lines, ticks) if len(s)]
            self._batter_cache[obj.id] = found = (id(obj.mesh), parts)
        return found[1]

    def _show_slope_colours(self):
        """(0.156) Each terrain's surface in the colours of its slope bands (terrain.SLOPE_BANDS), just over it."""
        from ..core import terrain as terrain_geo
        palette = np.array([_physical(c) for _b, c in terrain_geo.SLOPE_BANDS], dtype=np.float32)
        positions, colours = [], []
        for obj in self.doc.objects.values():
            if not obj.is_bim or obj.ifc_class != TERRAIN_CLASS or not self.is_shown(obj):
                continue
            mesh = obj.mesh
            surface = terrain_geo.surface_of(mesh.verts, mesh.tris, mesh.normals)
            if not len(surface):
                continue
            band = terrain_geo.slope_bands(mesh.verts, surface)
            positions.append(mesh.verts[surface].reshape(-1, 3) + (0.0, 0.0, CONTOUR_LIFT / 2))
            colours.append(np.repeat(palette[band], 3, axis=0))
        if positions:
            pts = np.concatenate(positions)
            fill = gfx.Mesh(gfx.Geometry(positions=_f32(pts), colors=np.concatenate(colours),
                                         indices=np.arange(len(pts), dtype=np.uint32).reshape(-1, 3)),
                            _mat(gfx.MeshBasicMaterial, color_mode="vertex", side="both"))
            self._contour_objects.append(fill)
            self.scene.add(fill)

    def set_show_slopes(self, on):
        self.show_slopes = bool(on)
        self._show_contours()
        self.redraw()

    # ------------------------------------------------------------ background images (0.154)

    def image_level(self, image):
        """The height its storey is at (m)."""
        if image.storey is not None:
            for guid, _name, z in self.doc.storeys():
                if guid == image.storey:
                    return float(z)
        return 0.0

    def images_shown(self):
        """The background images drawn now: visible ones — in a plan (or showing only the active storey) those of
        its storey."""
        only = self.only_active_storey or self.plan
        storeys = {g for g, _n, _z in self.doc.storeys()}
        return [i for i in getattr(self.doc, "images", ()) if i.visible
                and (not only or i.storey == self.doc.active_storey or i.storey not in storeys)]

    def _picture(self, path):
        if self.picture_loader is None:
            return None                                     # (nothing to read pictures with yet: asked again later)
        if path not in self._pictures:
            try:
                pixels = self.picture_loader(path)
            except Exception:                               # (a damaged file: not drawn, the dialog says so)
                pixels = None
            self._pictures[path] = (gfx.Texture(np.ascontiguousarray(pixels), dim=2, generate_mipmaps=True)
                                    if pixels is not None else None)
        return self._pictures[path]

    def picture_missing(self, image):
        """Its picture could not be read (moved, deleted, damaged)."""
        return self._picture(image.path) is None

    def _show_images(self):
        """Each image a flat picture just over its storey's floor (under the rooms' fill), half see-through."""
        for wobj in self._image_objects:
            self.scene.remove(wobj)
        self._image_objects = []
        for image in self.images_shown():
            texture = self._picture(image.path)
            if texture is None:
                continue
            # (0.208: a vertical one standing, just out of the face it is on; 0.209: only the part kept)
            lift = image.front() * IMAGE_LIFT if image.vertical else np.array((0.0, 0.0, IMAGE_LIFT))
            corners = [tuple(float(c) for c in p + lift) for p in image.kept_corners(self.image_level(image))]
            geometry = gfx.Geometry(positions=_f32(corners), indices=np.array([[0, 1, 2], [0, 2, 3]], np.uint32),
                                    texcoords=np.array(image.texcoords(), np.float32))
            material = _mat(gfx.MeshBasicMaterial, map=gfx.TextureMap(texture, filter="linear", mipmap_filter="linear",
                                                                wrap="clamp"),
                                             opacity=float(image.opacity), alpha_mode="blend", depth_write=False,
                                             side="both", pick_write=False)
            wobj = gfx.Mesh(geometry, material)
            self._image_objects.append(wobj)
            self.scene.add(wobj)
        self._clip(*[w.material for w in self._image_objects])

    def image_at(self, x, y, unlocked=True):
        """The background image under (x, y) — the last one laid, of those shown (unlocked only, by default) — and
        the point on it (x, y, z): (image, point) or (None, None)."""
        origin, direction = self.ray(x, y)
        for image in reversed(self.images_shown()):
            if unlocked and image.locked:
                continue
            z = self.image_level(image)
            if image.vertical:                              # (0.208: on its upright plane)
                corners = image.corners3d(z)
                p = ray_plane(origin, direction, corners[0], image.front())
                if p is None:
                    p = ray_plane(origin, direction, corners[0], -image.front())
                if p is not None and not self.picture_missing(image):
                    s, r = image.fraction(p, z)
                    s0, r0, s1, r1 = image.kept()                     # (0.209: its part kept)
                    if s0 - 1e-9 <= s <= s1 + 1e-9 and r0 - 1e-9 <= r <= r1 + 1e-9:
                        return image, p
                continue
            p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), np.array((0.0, 0.0, 1.0)))
            if p is not None and image.contains(p[:2]) and not self.picture_missing(image):
                return image, p
        return None, None

    def room_at(self, x, y):
        """The room (GlobalId) of the plan under (x, y), or None."""
        shapes = getattr(self, "_room_shapes", [])
        if not shapes:
            return None
        from shapely.geometry import Point
        z = self.doc.work_level()
        origin, direction = self.ray(x, y)
        p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), np.array((0.0, 0.0, 1.0)))
        if p is None:
            return None
        here = Point(float(p[0]), float(p[1]))
        return next((g for g, poly in shapes if poly.contains(here)), None)

    def select_rooms(self, guids):
        """Rooms picked (0.99): drawn in the selection's colour; the listeners (the window) told."""
        self.selected_rooms = set(guids)
        self._show_rooms()
        for fn in self.rooms_listeners:
            fn(self.selected_rooms)

    def grid_bubble(self):
        """The radius (m) of the grid's bubbles: the grid's settings (0.91)."""
        return float(getattr(self.doc, "grid_settings", {}).get("bubble", GRID_BUBBLE))

    def grid_level(self):
        """The height the grid's axes are drawn at (the active storey's level; a little up in 3D)."""
        return self.doc.work_level() + (0.0 if self.plan else EDGE_LIFT)

    def select_axes(self, indices):
        """Grid axes picked (0.72): drawn in the selection's colour; the listeners (the window) told."""
        self.selected_axes = set(indices)
        self._show_grid()
        for fn in self.axes_listeners:
            fn(self.selected_axes)

    def grid_axis_at(self, x, y, bubbles_only=False):
        """The grid axis whose bubble — or line, unless bubbles_only — is under (x, y), or None (0.72)."""
        axes = getattr(self.doc, "grids", [])
        if not axes or self.section is not None:
            return None
        z = self.grid_level()
        origin, direction = self.ray(x, y)
        p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), np.array((0.0, 0.0, 1.0)))
        if p is None:
            p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), np.array((0.0, 0.0, -1.0)))
        if p is None:
            return None
        reach = SYMBOL_PICK_PX * self.world_per_pixel(p)
        best, best_d = None, None
        for k, axis in enumerate(axes):
            a, b = np.array((*axis.start, z)), np.array((*axis.end, z))
            d = b - a
            length = np.linalg.norm(d)
            if length < 1e-9:
                continue
            d = d / length
            r = self.grid_bubble()
            for end, out in ((a, -d), (b, d)):              # inside a bubble
                gap = np.linalg.norm(p - (end + out * r)) - r
                if gap <= reach and (best_d is None or gap < best_d):
                    best, best_d = k, max(gap, -1.0)
            if bubbles_only:
                continue
            s = float(np.clip(np.dot(p - a, d), 0.0, length))
            gap = float(np.linalg.norm(a + d * s - p))
            if gap <= reach and (best_d is None or gap < best_d):
                best, best_d = k, gap
        return best

    def grid_guides(self):
        """The grid's axes as snapping lines [(point, direction)] at the active storey's level: along them,
        and where they cross (a column on a grid point)."""
        z = self.doc.work_level()
        out = []
        for axis in getattr(self.doc, "grids", []):
            a, b = np.array((*axis.start, z)), np.array((*axis.end, z))
            if np.linalg.norm(b - a) > 1e-9:
                out.append((a, (b - a) / np.linalg.norm(b - a)))
        return out

    def _deep_storeys(self):
        """The storeys a plan sees below its own (its view depth): GlobalIds."""
        if not self.plan or self.view_depth <= 0:
            return set()
        level = self.doc.work_level()
        return {g for g, _n, z in self.doc.storeys() if level - self.view_depth - 1e-9 <= z < level - 1e-9}

    def show_underlay(self, segments=(), z=0.0):
        """A plan's underlay (0.65): another storey's plan as grey lines (K, 2, 2), just above this floor
        (`z`) — under the walls standing on it, over the floor."""
        if self._underlay is not None:
            self.scene.remove(self._underlay)
            self._underlay = None
        segs = np.asarray(segments, dtype=float).reshape(-1, 2, 2)
        if len(segs):
            pts = np.concatenate((segs.reshape(-1, 2), np.full((len(segs) * 2, 1), z + UNDERLAY_LIFT)), axis=1)
            self._underlay = gfx.Line(gfx.Geometry(positions=_f32(pts)),
                                      _mat(gfx.LineSegmentMaterial, thickness=1.0, color=UNDERLAY_COLOR, aa=True,
                                                              depth_write=False))
            self._clip(self._underlay.material)         # (a plan's crop region)
            self.scene.add(self._underlay)
        self.redraw()

    def cutting(self):
        """A plan or a section is shown."""
        return self.plan or self.section is not None

    def kept_side(self):
        """(normal, offset): what a plan / section keeps is n·p >= offset; None in the 3D view."""
        if self.plan:
            return np.array((0.0, 0.0, -1.0)), -self.cut_level()      # below the cut
        if self.section is not None:
            point, normal = self.section
            return normal, float(normal @ point)                      # beyond the section line
        return None

    def kept_planes(self):
        """What the view keeps, as [(normal, offset)] — n·p >= offset for each — or None: a plan's
        or section's one side; in 3D, the inside of the section box."""
        kept = self.kept_side()
        if kept is not None:
            if self.plan and self.crop is not None:           # a plan's crop region (0.65): its four sides too
                x0, y0, x1, y1 = self.crop
                ex, ey = np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
                return [kept, (ex, x0), (-ex, -x1), (ey, y0), (-ey, -y1)]
            return [kept]
        if self.box is None:
            return None
        lo, hi = self.box
        axes = np.eye(3)
        return [(axes[k], float(lo[k])) for k in range(3)] + [(-axes[k], -float(hi[k])) for k in range(3)]

    def clipping_planes(self):
        """The pygfx clipping planes of the current view (pygfx keeps what has n·p >= d — read
        in its shader — so a plan's z <= cut is (0, 0, -1, -cut); what is clipped by any plane
        goes: a box keeps its inside)."""
        return [(float(n[0]), float(n[1]), float(n[2]), float(d)) for n, d in (self.kept_planes() or ())]

    # ------------------------------------------------------------ section box (3D)

    def set_box(self, lo, hi=None):
        """The section box of the 3D view (ArchiCAD's 3D cutaway): only what is inside the box
        (world corners lo, hi) is seen, what it cuts filled dark. None: the whole model again.
        In a plan or section their own cut is shown instead (the box comes back in 3D)."""
        self.box = None if lo is None else (np.minimum(lo, hi).astype(float), np.maximum(lo, hi).astype(float))
        self.apply_storey_view()

    def box_around(self, ids=None, margin=BOX_MARGIN):
        """(lo, hi) round the objects `ids` (default: all that is shown), `margin` beyond them, or None."""
        objects = None if ids is None else [o for o in (self.doc.get(i) for i in ids) if o is not None]
        box = self.bounds(objects or None)
        return None if box is None else (box[0] - margin, box[1] + margin)

    def _box_handles(self):
        """[(axis, 0 = low face / 1 = high face, its middle)] of the section box."""
        lo, hi = self.box
        out = []
        for axis in range(3):
            for side, value in ((0, lo[axis]), (1, hi[axis])):
                p = (lo + hi) / 2
                p[axis] = value
                out.append((axis, side, p))
        return out

    def box_handle_at(self, x, y):
        """(axis, side) of the section box's handle under the cursor, or None."""
        if self.box is None or self.cutting():
            return None
        handles = self._box_handles()
        xy = self.project_many(np.array([p for _a, _s, p in handles]))
        d = np.linalg.norm(xy - np.array((x, y)), axis=1)
        d = np.where(np.isnan(d), np.inf, d)
        k = int(np.argmin(d))
        return handles[k][:2] if d[k] <= BOX_HANDLE_PX else None

    def box_handle_point(self, axis, side):
        return next(p for a, s, p in self._box_handles() if (a, s) == (axis, side))

    def move_box_face(self, axis, side, value):
        """One face of the section box to `value` along its axis (kept BOX_MIN from the opposite one)."""
        lo, hi = (c.copy() for c in self.box)
        if side == 0:
            lo[axis] = min(float(value), hi[axis] - BOX_MIN)
        else:
            hi[axis] = max(float(value), lo[axis] + BOX_MIN)
        self.box = (lo, hi)
        self._show_box()
        self._apply_clipping()
        self.redraw()

    def _show_box(self):
        """The section box's outline and its 6 handles (in 3D only), over everything."""
        if self._box_view is not None:
            self.scene.remove(self._box_view)
            self._box_view = None
        if self.box is None or self.cutting():
            return
        lo, hi = self.box
        corners = [np.array((x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
        segs = [p for a in range(8) for b in range(a + 1, 8) if bin(a ^ b).count("1") == 1
                for p in (corners[a], corners[b])]
        group = gfx.Group()
        group.add(gfx.Line(gfx.Geometry(positions=_f32(segs)),
                           _overlay_material(gfx.LineSegmentMaterial, thickness=1.5, color=BOX_COLOR)))
        group.add(gfx.Points(gfx.Geometry(positions=_f32([p for _a, _s, p in self._box_handles()])),
                             _overlay_material(gfx.PointsMaterial, size=11, color=BOX_COLOR)))
        self._box_view = group
        self.scene.add(group)

    def _apply_clipping(self):
        """The current clipping planes on everything (and the poché with them; in a plan its symbols,
        dimensions and underlay too: its crop region)."""
        for view in self._views.values():
            self._clip(*[w.material for w in (view.faces, view.edges) if w is not None])
        extras = ([w for w in (self._symbols, self._underlay) if w is not None] + list(self._dim_objects)
                  + list(self._grid_objects))
        if self.plan:
            self._clip(*[w.material for w in extras])
        else:
            for w in extras:
                w.material.clipping_planes = []
        cut = self.cutting() or self.box is not None
        if self.bim.cutting or cut:
            kept = self.kept_side()
            # the poché a hair towards the viewer, who looks along the kept side's normal (see batches)
            lift = tuple(-kept[0] * POCHE_LIFT) if kept is not None else \
                tuple(float(c) for c in np.round(-self.view_direction() * POCHE_LIFT, 4)) if cut else (0.0, 0.0, 0.0)
            self.bim.set_cut(cut, self.clipping_planes(), lift)

    def set_plan(self, on):
        """Plan of the active storey (Phase 3, step 1): seen from above without perspective, cut
        CUT_HEIGHT above its level, only that storey shown; what the cut goes through is filled
        dark (poché), as in a drawn plan. It follows the active storey and does not turn (the
        middle button pans). Off: the 3D view again (iso), whole."""
        self.plan = bool(on)
        self.section = None
        self._cut_view()
        self.set_view("top" if self.plan else "iso")

    def set_section(self, point, normal, view=None):
        """Section (Phase 3, step 2): the vertical plane through `point` facing `normal`
        (horizontal); seen along `normal` without perspective, with everything on the near side
        taken away and what the plane goes through filled dark — all storeys.
        view: its key for its dimensions (("section", name) / ("elevation", side)).
        None: the 3D view again (iso)."""
        self.plan = False
        self.section = None if point is None else (np.asarray(point, dtype=float),
                                                   normalize(np.asarray(normal, dtype=float)))
        self.section_view = view if point is not None else None
        self._cut_view()
        if self.section is None:
            self.set_view("iso")
            return
        center, radius = self.scene_bounds()
        self._frame_ortho(center, radius, self.section[1])
        self.redraw()

    def _cut_view(self):
        self.camera.fov = 0 if self.cutting() or self.look[3] else 45
        self._apply_look()
        self.apply_storey_view()

    def _model_dark(self):
        """(0.341) The model's greys turned over: on the dark views, in a plan, a section or an elevation (a drawing:
        its lines light, its white and grey faces dark) — not in the 3D view, where the model keeps its colours and
        its light and only the background goes dark (as Revit's)."""
        return views_canvas.DARK and self.cutting()

    def _turn_model(self):
        """(0.341) The elements and sketches recoloured when whether the model's greys are turned over (or its edges
        light: _edges_light) changed: the undressed ones in place, those dressed by their materials or in their parts'
        own colours made again; the cut's hatches."""
        state = (self._model_dark(), self._edges_light())
        if state == self._model_turned:
            return
        self._model_turned = state
        dark = state[0]
        self.bim.set_canvas(dark)
        self._assemble_cut_hatches()
        self._dressed.clear()
        self._ready.clear()                             # (pieces made beforehand: in the light colours)
        for obj_id in list(self.bim.where):
            obj = self.doc.get(obj_id)
            if obj is None:
                continue
            if obj_id in self._shown_dressed or getattr(obj.mesh, "colors", None) is not None:
                self.show_object(obj_id, obj.mesh)      # (its patterns', its parts' own colours made again)
            else:
                self.bim.recolor(obj_id, *self._bim_colors(obj))
        for obj_id in list(self._views):
            obj = self.doc.get(obj_id)
            if obj is not None and not obj.is_bim:
                self.show_object(obj_id, obj.mesh)

    def set_look(self, style="shaded", edges=True, grid=True, axonometric=False):
        """The 3D view's look (0.63, its properties): visual style (batches.STYLES: shaded, hidden
        lines, wireframe, x-ray), its edges drawn or not, the ground grid, seen without perspective
        (an axonometry) or with it. A plan or a section keeps its own (shaded, cut, no grid)."""
        look = (style, bool(edges), bool(grid), bool(axonometric))
        cutting = self.cutting()
        shown = self._resolve_style((self.cut_style or "shaded") if cutting else style)
        if look != self.look or shown != self.vstyle:      # (0.315: or its style was changed)
            self.look = look
            self._apply_look()

    def _resolve_style(self, key):
        finder = getattr(self.doc, "view_style", None)
        return finder(key) if finder is not None else view_styles_model.BUILTIN.get(
            key, view_styles_model.BUILTIN["shaded"])

    def _apply_look(self):
        cutting = self.cutting()
        style, edges, grid, axonometric = ("shaded", True, False, True) if cutting else self.look
        if cutting and self.cut_style:            # (0.315: a plan's / section's own view style)
            style = self.cut_style
        vs = self.vstyle = self._resolve_style(style)
        face = FACE_LOOKS.get(vs.faces, "shaded")
        edges = bool(edges) and vs.edges
        # (its surface patterns shown: the materials', or its hatches by category's — 0.318)
        patterns = vs.patterns or any(c[3] or c[4] for c in vs.categories)
        self.grid.visible = grid and not cutting   # (a drawing has no grid; it would also cross the floor slabs)
        if (face, edges) != (self.bim.style, self.bim.edges) or patterns != self.bim.patterns or \
                abs(self.bim.line_material.thickness - vs.edge_width) > 1e-9:
            restyled = face != self.bim.style
            self.bim.set_look(face, edges, vs.edge_width, patterns)
            if restyled:
                for obj in self.doc.sketches():
                    if obj.id in self._views:
                        self.show_object(obj.id, obj.mesh)
        dressing = (vs.colours, vs.patterns, vs.transparency)
        if dressing != self._dressing or vs.categories != self._overrides:    # (0.315: colours, patterns, glass…)
            self._dressing = dressing
            self._overrides = vs.categories                                   # (0.318: …its hatches by category)
            self._redress()
        self._set_shadows(vs.shadows and not cutting and vs.faces in ("shaded", "consistent"))
        if not cutting:
            self._set_axonometric(axonometric)
        self._turn_model()                        # (0.341: on the dark views, a drawing's greys, edges on no faces)
        self.redraw()

    def _show_cut_hatches(self):
        """(0.317) In a plan or a section, what is cut as it is on paper: each layer's background and its pattern's
        lines — its material's own, else its category's in the project's graphic style; a graphic rule's colours; the
        view style's cut —, drafting patterns at the view's scale (1:50 when it has none), its outline. A hair beyond
        the cutting plane, drawn after the dark poché and not picked (a click still picks what is cut). Made again only
        when what is cut, or how, changes."""
        view = self.current_view() if self.cutting() else None
        kept = self.kept_side()
        if view is None or kept is None or getattr(self.doc, "loading", False):
            self._hatch_key = None
            self._hatch_parts = {}
            self._assemble_cut_hatches()
            return
        from ..ifc import catalog
        from ..model import cut_hatches, drawings
        n, offset = np.asarray(kept[0], dtype=float), float(kept[1])
        if self.plan:                                 # (a point of the cutting plane: its 2D drops its height)
            origin, u, v = np.array((0.0, 0.0, -offset)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
        else:
            point, normal = self.section
            origin = np.array((point[0], point[1], 0.0))
            u = np.cross(normal, (0.0, 0.0, 1.0))
            u = u / max(float(np.linalg.norm(u)), 1e-12)
            v = np.array((0.0, 0.0, 1.0))
        settings = self.doc.view_settings(view)
        look = self.doc.view_style(self.cut_style) if self.cut_style and hasattr(self.doc, "view_style") else None
        objects = [o for o in self.shown_objects() if o.is_bim]
        key = (tuple(view), tuple(np.round(n, 6)), round(offset, 6), settings.detail, settings.rule, look,
               settings.scale, catalog.GENERATION, repr(getattr(self.doc, "graphic_style", None)),
               tuple(sorted((settings.elements or {}).items())),             # (0.331: its hatches by element)
               frozenset((o.id, id(o.mesh)) for o in objects))
        if key != self._hatch_key:
            again = self._hatch_key is not None and self._hatch_key[:-1] == key[:-1]   # (the same view, edited)
            self._hatch_key = key
            if again and len(objects) > HATCHES_LATER:
                # (0.320) many elements cut: the edit's image first (the hatches as they were), then theirs again
                self._hatch_later = True
                self.after_next_draw(self._hatches_again)
                self._assemble_cut_hatches()
                return
            fills, own, whose = drawings.cut_fills(self.doc, objects, n, offset, origin, u, v, settings.rule,
                                                   settings.detail, look, settings.elements)
            gstyle = styles_model.clean(getattr(self.doc, "graphic_style", None))
            self._hatch_parts = cut_hatches.build(fills, whose, own, gstyle, settings.scale or HATCH_SCALE,
                                                  origin, u, v, n * HATCH_DEPTH)
        self._assemble_cut_hatches()

    def _hatches_again(self):
        """(0.320) The cut's hatches made again after an edit's image (_show_cut_hatches: many elements cut)."""
        if not self._hatch_later:
            return
        self._hatch_later = False
        self._hatch_key = None
        self._show_cut_hatches()
        self.redraw()

    def _assemble_cut_hatches(self):
        """(0.317) The cut's hatches on screen from each element's part (_show_cut_hatches): one mesh of fills, one set
        of lines — a selected element's in the selection's colours."""
        for wobj in self._hatch_objects:
            self.scene.remove(wobj)
        self._hatch_objects = []
        if not self._hatch_parts:
            return
        tris, tri_rgb, segs, seg_rgb = [], [], [], []
        picked = np.array(gfx.Color(FACE_SELECTED).rgb[:3])
        ink = np.array(gfx.Color(EDGE_SELECTED).rgb[:3])
        for owner, (t, c, s, sc) in self._hatch_parts.items():
            selected = owner in self.selection
            if len(t):
                tris.append(t)
                tri_rgb.append(np.tile(picked, (len(t), 1)) if selected else c)
            if len(s):
                segs.append(s)
                seg_rgb.append(np.tile(ink, (len(s), 1)) if selected else sc)
        planes = self.clipping_planes()
        turn = views_canvas.ink_array if self._model_dark() else (lambda rgb: rgb)    # (0.341: on the dark views)
        if tris:
            t = np.concatenate(tris)
            colours = np.repeat(np.column_stack((physical(turn(np.concatenate(tri_rgb))), np.ones(len(t)))), 3,
                                axis=0)
            fill = gfx.Mesh(gfx.Geometry(positions=_f32(t.reshape(-1, 3)), colors=colours.astype(np.float32),
                                         indices=np.arange(len(t) * 3, dtype=np.uint32).reshape(-1, 3)),
                            _mat(gfx.MeshBasicMaterial, color_mode="vertex", side="both", alpha_mode="blend",
                                                  depth_write=False, render_queue=HATCH_QUEUE, pick_write=False))
            self._hatch_objects.append(fill)
        if segs:
            s = np.concatenate(segs)
            colours = np.repeat(np.column_stack((physical(turn(np.concatenate(seg_rgb))), np.ones(len(s)))), 2, axis=0)
            lines = gfx.Line(gfx.Geometry(positions=_f32((s - (self._hatch_lift() * 0.5)).reshape(-1, 3)),
                                          colors=colours.astype(np.float32)),
                             _mat(gfx.LineSegmentMaterial, thickness=1.0, color_mode="vertex", aa=True, alpha_mode="blend",
                                                     depth_write=False, render_queue=HATCH_QUEUE + 1))
            self._hatch_objects.append(lines)
        for wobj in self._hatch_objects:
            wobj.material.clipping_planes = planes
            self.scene.add(wobj)

    def _hatch_lift(self):
        """A hair towards the viewer (the lines over their fills)."""
        kept = self.kept_side()
        return np.asarray(kept[0], dtype=float) * HATCH_DEPTH if kept is not None else np.zeros(3)

    def set_cut_style(self, key):
        """(0.315) The view style of the plan or section shown (its own; None: drawn as always — shaded, cut dark)."""
        if key != self.cut_style or (self.cutting() and self._resolve_style(key or "shaded") != self.vstyle):
            self.cut_style = key
            if self.cutting():
                self._apply_look()

    def materials_changed(self):
        """(0.315) The project's materials changed (their colours, patterns, transparency): the elements dressed by
        them are made again."""
        self._dressed.clear()
        if self._dressing != ("category", False, False) or self._overrides or self.element_hatches:
            self._redress()
            self.redraw()

    def set_element_hatches(self, elements):
        """(0.331) The view's own hatches for some elements, as Revit's «Override graphics in view ▸ by element»:
        {GlobalId: (cut foreground, cut background, surface foreground, surface background)}, each (pattern, colour)
        or None — over their category's (the view style's) and their materials'. Only the elements whose hatches
        changed are made again; a plan's or section's cut is hatched again."""
        elements = dict(elements or {})
        if elements == self.element_hatches:
            return
        changed = {g for g in set(elements) | set(self.element_hatches)
                   if elements.get(g) != self.element_hatches.get(g)}
        self.element_hatches = elements
        for guid in changed:
            obj = self.doc.get(guid)
            if obj is not None and obj.is_bim and guid in self.bim.where:
                self.show_object(guid, obj.mesh)
        if self.cutting():
            self._show_cut_hatches()
        self.redraw()

    @material_looks.one_pass()                  # (0.352: each wall's layers read once)
    def _redress(self):
        """(0.315) The elements shown made again for the view style's colours, patterns and transparency — (0.317) only
        those it changes: dressed now, or dressed before."""
        for obj_id in list(self.bim.where):
            obj = self.doc.get(obj_id)
            if obj is not None and obj.is_bim and (obj_id in self._shown_dressed or self._dress(obj) is not None):
                self.show_object(obj_id, obj.mesh)
        self.bim.set_poche_colours(bool(self.colours) or self._dressing[0] == "material")

    def set_canvas(self, dark):
        """(0.341) The views' canvas light or dark (render/canvas: on the dark one a grey turned over) — everything
        shown drawn again in it: the background, the ground grid, the elements' faces and edges, the sketches, the
        poché, the shadows' ground, and all drawn over the model (dimensions, texts, marks, axes, hatches, guides…).
        False if it was so already."""
        if not views_canvas.set_dark(dark):
            return False
        self.refresh_ground()
        if self._shadow_ground is not None:
            self._shadow_ground.material.color = views_canvas.ink(SHADOW_GROUND)
        self.bim.set_canvas(self._model_dark())
        self._turn_model()
        self._show_guides()
        self.apply_storey_view()
        if self._tdim_args is not None:                   # (0.361) the temporary dimensions in the canvas' colours
            self.show_temp_dims(*self._tdim_args[:-1])
        return True

    def refresh_ground(self):
        """(0.393) The background and the ground grid in the canvas in use (dark or light, the palette's drawing area):
        the grid's colour made from the background."""
        self.background.material.set_colors(*views_canvas.background())
        self.grid.material.major_color = views_canvas.ground_grid(GROUND_GRID)
        self.redraw()

    def _set_shadows(self, on):
        """(0.315) The sun casts shadows on the model and on a light ground under it."""
        on = bool(on)
        if on == self.bim.shadows and (not on or self._shadow_ground is not None):
            if on:
                self._place_sun()
            return
        self.bim.set_shadows(on)
        self.sun.cast_shadow = on
        if on and getattr(self, "_twin_sun", None) is None:
            # (OpenGL, WSL: with one light's shadows their texture has one layer, which OpenGL takes for a plain
            # picture — read so, all of it is in shadow; a second light, of no light at all, makes it two)
            self._twin_sun = gfx.DirectionalLight(intensity=0.0)
            self._twin_sun.local.position = (0.0, 0.0, 1.0)
            self.scene.add(self._twin_sun)
        if getattr(self, "_twin_sun", None) is not None:
            self._twin_sun.cast_shadow = on
        if on:
            if self._shadow_ground is None:
                ground = gfx.Mesh(gfx.plane_geometry(1.0, 1.0),
                                  _mat(gfx.MeshPhongMaterial, color=SHADOW_GROUND, specular="#000", pick_write=False))
                ground.receive_shadow = True
                self._shadow_ground = ground
                self.scene.add(ground)
            self._shadow_ground.visible = True
            self._place_sun()
        else:
            if self._shadow_ground is not None:
                self._shadow_ground.visible = False
            self.sun.local.position = SUN                 # (the usual light again)
            self.sun.target.local.position = (0.0, 0.0, 0.0)

    def _place_sun(self):
        """The sun's shadows over the whole model: from where the view style says (by default the south-south-west,
        high: the shadows fall to the north-east, seen beside what casts them), its shadow camera as wide as the
        model, the ground under it."""
        center, radius = self._sun_box[:2] if getattr(self, "_sun_box", None) else self.scene_bounds()
        center = np.asarray(center, dtype=float)
        radius = max(float(radius), 1.0)
        direction = normalize(np.asarray(self.vstyle.sun(), dtype=float))      # (0.316: the view style's sun)
        if getattr(self, "_sun_preview", None) is not None:
            direction = self._sun_preview                                       # (0.365: a scene's sun, previewed)
        self.sun.local.position = tuple(center + direction * radius * 3.0)
        self.sun.target.local.position = tuple(center)
        camera = self.sun.shadow.camera
        camera.width = camera.height = radius * 2.4
        camera.depth_range = (radius * 0.01, radius * 8.0)
        self.sun.shadow.bias = 0.001
        if self._shadow_ground is not None:
            if getattr(self, "_sun_box", None) and len(self._sun_box) > 2:
                bottom = self._sun_box[2]                                       # (0.365: measured once, previewing)
            else:
                bounds = [o.mesh.bounds() for o in self.doc.objects.values()
                          if o.is_bim and o.mesh.bounds() is not None]
                bottom = min((float(b[0][2]) for b in bounds), default=0.0)
                if getattr(self, "_sun_box", None):
                    self._sun_box = (*self._sun_box[:2], bottom)
            self._shadow_ground.local.position = (float(center[0]), float(center[1]), bottom - 0.002)
            self._shadow_ground.local.scale = (radius * 6.0, radius * 6.0, 1.0)

    def preview_sun(self, direction=None):
        """(0.365) The sun shining from `direction` (towards it, the model's axes), with its shadows — a scene's sun
        seen before it goes to the Presentation, and played through a day or a year (the model measured once for all
        of them); None: the view style's sun and shadows again."""
        if direction is None:
            self._sun_preview = self._sun_box = None
            vs = self.vstyle
            self._set_shadows(vs.shadows and not self.cutting() and vs.faces in ("shaded", "consistent"))
            if not self.bim.shadows:
                self.sun.local.position = SUN
                self.sun.target.local.position = (0.0, 0.0, 0.0)
        else:
            if getattr(self, "_sun_box", None) is None:
                self._sun_box = self.scene_bounds()
            self._sun_preview = normalize(np.asarray(direction, dtype=float))
            if self.bim.shadows and self._shadow_ground is not None:
                self._place_sun()
            else:
                self._set_shadows(True)
        self.redraw()

    def _set_axonometric(self, on):
        """The 3D view without perspective or with it again, what is in view staying (about) the same."""
        if on == self.is_ortho():
            return
        forward, focus = normalize(self.view_direction()), self._focus.copy()
        if on:
            height = 2.0 * float(np.linalg.norm(focus - self.camera_position())) * math.tan(
                math.radians(self.camera.fov) / 2)
            _center, radius = self.scene_bounds()
            self.camera.fov = 0
            self.camera.local.position = tuple(focus - forward * (radius * 4.0 + 10.0))
            self.camera.show_pos(tuple(focus), up=(0, 0, 1))
            self._set_ortho_height(height)
        else:
            height = self.ortho_height()
            self.camera.fov = 45
            self.camera.local.position = tuple(focus - forward * (height / 2 / math.tan(math.radians(22.5))))
            self.camera.show_pos(tuple(focus), up=(0, 0, 1))
        self._set_focus(focus)

    def _clip(self, *materials):
        planes = self.clipping_planes()
        for material in materials:
            material.clipping_planes = planes

    def apply_storey_view(self):
        """Grid at the active storey's level; hide / show the other storeys; the plan's cut."""
        self.grid.local.position = (0.0, 0.0, self.doc.work_level())
        for obj_id, view in self._views.items():
            view.group.visible = self.is_shown(self.doc.get(obj_id))
        active = self.doc.active_storey
        only = self.only_active_storey or self.plan
        deep = self._deep_storeys()                       # (a plan's view depth: the storeys below it seen)

        def shown(key):
            storey, cls, mark, phase = key[:4] if isinstance(key, tuple) else (key, None, None, None)
            return ((not only or storey is None or storey == active or storey in deep)
                    and not (mark == SYMBOL and self.plan)
                    and (cls is None or cls not in self.hidden_classes)
                    and (phase is None or phase not in self.hidden_phases))

        self.bim.set_visible(shown)
        self._show_plan_symbols()
        self._show_services_above()
        self._show_dimensions()
        self._show_view_marks()
        self._show_grid()
        self._show_rooms()
        self._show_images()
        self._show_cad()
        self._show_clouds()
        self._show_analytical()
        self._show_contours()
        self._apply_clipping()
        self._show_cut_hatches()                    # (0.317: what is cut, hatched as on paper)
        self._show_box()
        hidden = {i for i in self.selection if not self.is_shown(self.doc.get(i))}
        if hidden:
            self.set_selection(self.selection - hidden)   # nothing hidden stays selected
        self.redraw()

    def set_only_active_storey(self, on):
        self.only_active_storey = bool(on)
        self.apply_storey_view()

    def _split_classes(self):
        """The IFC classes some view template or view hides: their elements get batches of their own."""
        return ({cls for tpl in self.doc.templates for cls in tpl.hidden}
                | {cls for own in self.doc.view_props.values() for cls in own.get("hidden", ())})

    def _split_by_phase(self):
        return (any(tpl.phases != "all" for tpl in self.doc.templates)
                or any(own.get("phases", "all") != "all" for own in self.doc.view_props.values()))

    def _batch_key(self, obj):
        """IFC elements are batched by storey — and by class for the classes a view template can
        hide, by phase if a template hides phases (only then: fewer batches draw faster); doors
        drawn by a plan symbol in batches of their own, hidden in a plan (the symbol is shown)."""
        symbol = obj.ifc_class == "IfcDoor" and self.doc.has_plan_symbol(obj.id)
        cls = obj.ifc_class if obj.ifc_class in self._split else None
        phase = (self.doc.status_of(obj.id) or "") if self._split_phases else None
        mark = SYMBOL if symbol else (GROUND if obj.ifc_class == TERRAIN_CLASS else None)   # (its earth: 0.156)
        dressed = self._dress(obj) if self._dressing[2] else None
        if dressed is not None and dressed[2]:          # (0.315: with glass, drawn after the others)
            return (obj.storey, cls, mark, phase, CLEAR)
        return (obj.storey, cls, mark, phase)

    def _show_plan_symbols(self):
        """In a plan: the active storey's doors drawn as in a drawing — linings, the leaf open, the
        swing arc (from the IFC, Document.plan_symbols) — just under the cut, over what is below."""
        if self._symbols is not None:
            self.scene.remove(self._symbols)
            self._symbols = None
        self._symbol_segments, self._symbol_owner = np.zeros((0, 2, 3)), []
        if not self.plan:
            if self.section is not None:
                self._show_elevation_signs()
            return
        active = self.doc.active_storey
        doors = [i for i, batch in self.bim.where.items()
                 if isinstance(batch.key, tuple) and batch.key[2] == SYMBOL and batch.key[0] in (active, None)
                 and batch.key[1] not in self.hidden_classes]
        found = self.doc.plan_symbols(doors) if doors else {}
        if not found:
            return
        segs = np.concatenate(list(found.values()))
        segs[:, :, 2] = self.cut_level() - SYMBOL_DEPTH
        self._show_symbol_lines(segs, found)

    def _show_elevation_signs(self):
        """(0.292) In a section or an elevation: the doors' and windows' signs of how they open, on both faces of
        their leaves (Document.elevation_signs) — where they are, so that what is in front hides them as it hides the
        model."""
        ids = [o.id for o in self.doc.objects.values() if o.is_bim and o.ifc_class in ("IfcDoor", "IfcWindow")
               and o.ifc_class not in self.hidden_classes and self.is_shown(o)]
        found = self.doc.elevation_signs(ids) if ids else {}
        if found:
            self._show_symbol_lines(np.concatenate(list(found.values())), found)

    def _show_symbol_lines(self, segs, found):
        """The symbols' lines drawn, each in its element's colour (the selection's when it is selected)."""
        self._symbol_segments = segs
        self._symbol_owner = [g for g, s in found.items() for _ in range(len(s))]
        colors = np.array([_physical(EDGE_SELECTED if g in self.selection else EDGE_COLOR)
                           for g in self._symbol_owner], np.float32)
        self._symbols = gfx.Line(gfx.Geometry(positions=_f32(segs), colors=np.repeat(colors, 2, axis=0)),
                                 _mat(gfx.LineSegmentMaterial, thickness=1.3, color_mode="vertex", aa=True))
        self._clip(self._symbols.material)              # (a plan's crop region)
        self.scene.add(self._symbols)

    def current_view(self):
        """The view shown, as its dimensions are kept: ("plan", storey) in a plan, the section or
        elevation shown (section_view), None in 3D."""
        if self.plan:
            return ("plan", self.doc.active_storey)
        return self.section_view if self.section is not None else None

    def view_plane(self):
        """(origin, u, v, normal) of the paper of the view shown — dimensions are drawn on it, a
        hair towards the viewer — or None in 3D."""
        if self.plan:
            return (np.array((0.0, 0.0, self.cut_level() - DIM_DEPTH)), np.array((1.0, 0.0, 0.0)),
                    np.array((0.0, 1.0, 0.0)), np.array((0.0, 0.0, -1.0)))
        if self.section is None:
            return None
        point, normal = self.section
        right = np.cross(normal, (0.0, 0.0, 1.0))
        origin = np.array((point[0], point[1], 0.0)) - normal * DIM_DEPTH
        return origin, right, np.array((0.0, 0.0, 1.0)), normal

    def _show_annotations(self):
        """What is drawn in the view shown (0.120): its lines, its regions (hatched at the view's scale, or
        filled grey), its texts."""
        for wobj in self._ann_objects:
            self.scene.remove(wobj)
        self._ann_objects, self._ann_segments, self._ann_owner, self._ann_texts = [], np.zeros((0, 2, 3)), [], []
        self.selected_annotations &= set(self.doc.annotations)
        plane = self.view_plane()
        view = self.current_view()
        anns = self.doc.annotations_of(view) if plane is not None else []
        if not anns:
            return
        origin, u, v, _n = plane
        to3 = lambda p: origin + u * p[0] + v * p[1]               # noqa: E731
        try:
            scale = self.doc.view_settings(view).scale or 100
        except Exception:
            scale = 100
        segs, owned, hatch = [], [], []
        groups = {}                                      # (line type, pen mm) -> (segments, colours) (0.126)
        drawn = styles_model.pen(getattr(self.doc, "graphic_style", None), "drawn")
        for ann in anns:
            color = _physical(EDGE_SELECTED if ann in self.selected_annotations else EDGE_COLOR)
            group = groups.setdefault((ann.extra.get("line", "continuous"), float(ann.extra.get("width") or drawn)),
                                      ([], []))
            for a, b in notes2d.segments(ann, origin, u, v):
                segs += [to3(a), to3(b)]
                group[0].extend([to3(a), to3(b)])
                group[1].extend([color, color])
                owned.append(ann)
            if ann.kind == "region":
                ring = notes2d.shape(ann, origin, u, v)
                if ring and ann.hatch == "solid":
                    pts = np.array([to3(p) for p in ring[0][0]])
                    try:
                        tris = triangulate_polygon(pts)
                    except Exception:
                        tris = []
                    if tris:
                        fill = gfx.Mesh(gfx.Geometry(positions=_f32(pts), indices=np.array(tris, np.uint32)),
                                        _mat(gfx.MeshBasicMaterial, color="#9a9a9a", side="both"))
                        self._ann_objects.append(fill)
                elif ring:
                    for a, b in notes2d.hatch_lines(ring[0][0], ann.hatch, notes2d.HATCH_SPACING * scale / 1000.0):
                        hatch += [to3(a), to3(b)]
            if ann.kind == "keynote" and len(ann.points) >= 2:     # (0.194) its box, its element's code in it
                from ..model import keynotes
                words = keynotes.tag_text(self.doc, ann)
                start2, tip2 = notes2d.to2(ann.points[:2], origin, u, v)
                box, middle = notes2d.keynote_box(start2, tip2, words, float(ann.size), scale / 1000.0)
                corners = [to3(q) for q in box]
                for k in range(4):
                    segs += [corners[k], corners[(k + 1) % 4]]
                    group[0].extend([corners[k], corners[(k + 1) % 4]])
                    group[1].extend([color, color])
                    owned.append(ann)
                label = gfx.Text(text=words, font_size=float(ann.size) * scale / 1000.0, screen_space=False,
                                 anchor="middle-center", material=_mat(gfx.TextMaterial,
                                     color="#1f5fd6" if ann in self.selected_annotations else "#1e1e1e"))
                label.local.position = tuple(float(c) for c in to3(middle))
                self._ann_objects.append(label)
                self._ann_texts.append((to3(middle), ann))
            if ann.kind == "level":                         # (0.192) its two quarters filled
                for quarter in notes2d.level_fills(ann, origin, u, v):
                    pts = np.array([to3(p) for p in quarter])
                    tris = np.array([(0, k, k + 1) for k in range(1, len(pts) - 1)], np.uint32)
                    self._ann_objects.append(gfx.Mesh(gfx.Geometry(positions=_f32(pts), indices=tris),
                                                      _mat(gfx.MeshBasicMaterial, color="#1e1e1e", side="both")))
            if ann.kind == "text" and ann.text or ann.kind in notes2d.MARKS:
                at = to3(notes2d.to2(ann.points[:1], origin, u, v)[0])
                words = ann.text
                if ann.kind in notes2d.MARKS:               # (0.156) the height there now (0.192: a level mark too)
                    from ..model import spots
                    words = spots.text(spots.spot_height(self.doc, ann), decimal_sep())
                    at = to3(notes2d.mark_text_at(ann, origin, u, v))
                material = _mat(gfx.TextMaterial, color="#1f5fd6" if ann in self.selected_annotations else "#1e1e1e",
                                            outline_color="#ffffff", outline_thickness=0.3)
                turned = notes2d.angle(ann) if ann.kind == "text" else 0.0
                if abs(turned) > 1e-9 and self.plan:        # (0.191) turned, in a plan: its size on the paper there
                    label = gfx.Text(text=words, font_size=float(ann.size) * scale / 1000.0, screen_space=False,
                                     anchor="bottom-left", material=material)
                    label.local.rotation = la.quat_from_axis_angle((0.0, 0.0, 1.0), math.radians(turned))
                else:
                    label = gfx.Text(text=words, font_size=14, screen_space=True, anchor="bottom-left",
                                     material=material)
                label.local.position = tuple(float(c) for c in at)
                self._ann_objects.append(label)
                self._ann_texts.append((at, ann))
        for (line, width), (g_segs, g_colors) in groups.items():
            if not g_segs:
                continue
            dashes = styles_model.DASHES.get(line)              # (mm on paper: about 4 pixels each on screen)
            extra = {"dash_pattern": tuple(d * 4.0 for d in dashes)} if dashes else {}
            self._ann_objects.append(gfx.Line(
                gfx.Geometry(positions=_f32(g_segs), colors=np.array(g_colors, np.float32)),
                _mat(gfx.LineSegmentMaterial, thickness=max(1.0, width * 6.4), color_mode="vertex", aa=True, **extra)))
        if hatch:
            self._ann_objects.append(gfx.Line(gfx.Geometry(positions=_f32(hatch)),
                                              _mat(gfx.LineSegmentMaterial, thickness=0.8, color="#555555", aa=True)))
        self._ann_segments = np.array(segs, dtype=float).reshape(-1, 2, 3)
        self._ann_owner = owned
        if self.plan:                                   # (a plan's crop region)
            self._clip(*[w.material for w in self._ann_objects])
        for wobj in self._ann_objects:
            self.scene.add(wobj)
        self.redraw()

    def _show_view_marks(self):
        """The symbols of the view shown (0.121, model/symbols.py): in a plan, the sections' lines with their
        heads and the elevations' marks; in a section or an elevation, a level mark at each storey — as on
        paper, sized at the view's scale."""
        for wobj in self._mark_objects:
            self.scene.remove(wobj)
        self._mark_objects, self._mark_heads = [], []
        plane, view = self.view_plane(), self.current_view()
        if plane is None or self.doc.loading:
            return
        origin, u, v, _n = plane
        try:
            scale = self.doc.view_settings(view).scale or 100
        except Exception:
            scale = 100
        mm = scale / 1000.0                                # metres in the model per mm on paper
        overlay = dict(depth_test=False, depth_write=False, render_queue=OVERLAY_QUEUE)
        lines, dashed, solid = [], [], []                  # (segments; filled triangles as meshes)
        short_dashes = []                                  # (0.360: dashed, not dash-dot)
        texts = []
        gstyle = getattr(self.doc, "graphic_style", None)  # (0.360: the symbols' styles, the project's)
        styles = {k: styles_model.symbol(gstyle, k) for k in styles_model.SYMBOL_KINDS}

        def to3(q):
            return origin + u * q[0] + v * q[1]

        def head(c2, tag, look2, ref, kind):
            style = styles[kind]
            centre = to3(c2)
            shape, filled, hollow, r = marks_model.head_shape(style, look2, mm)
            c2 = np.asarray(c2, dtype=float)
            lines.extend(p for a, b in shape for p in (to3(c2 + a), to3(c2 + b)))
            for tri in filled:
                solid.append([to3(c2 + q) for q in tri])
            for tri in hollow:
                lines.extend(p for a, b in zip(tri, tri[1:] + tri[:1]) for p in (to3(c2 + a), to3(c2 + b)))
            texts.append((centre, tag, "middle-center", style["text"]))
            self._mark_heads.append((centre, max(r, marks_model.HEAD * 0.6 * mm), ref))

        def line(a2, b2, kind):
            pieces, dashes = marks_model.line_pieces(a2, b2, styles[kind], mm)
            target = lines if not dashes else (short_dashes if dashes == marks_model.DASHES["dashed"] else dashed)
            target.extend(p for a, b in pieces for p in (to3(a), to3(b)))

        if self.plan:
            letters = dict(zip(("N", "E", "S", "W"), t("cube.letters").split()))
            box = marks_model.extent(self.doc)
            marks = marks_model.section_marks(self.doc, box, mm) + marks_model.elevation_marks(
                self.doc, letters, marks_model.plan_box(self.doc, self.doc.active_storey), mm) if box is not None else []
            for m in marks:
                if m.kind == "section":
                    line(m.a, m.b, "section")
                    d = (m.b - m.a) / max(float(np.linalg.norm(m.b - m.a)), 1e-9)
                    out_by = styles["section"]["size"] * mm
                    for end, out in ((m.a, -d), (m.b, d)):
                        head(end + out * out_by, m.tag, m.look, ("section", m.ref), "section")
                else:
                    head(m.a, m.tag, m.look, ("elevation", m.ref), "elevation")
        else:
            boxes = [o.mesh.bounds() for o in self.doc.objects.values() if o.is_bim and o.mesh.bounds() is not None]
            if boxes:
                lo, hi = np.min([b[0] for b in boxes], axis=0), np.max([b[1] for b in boxes], axis=0)
                corners = [np.array((x, y, 0.0)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1])]
                along = [float((c - origin) @ u) for c in corners]
                x0, x1 = min(along) - marks_model.LEVEL_OVER * mm, max(along) + marks_model.LEVEL_OVER * mm
                level = styles["level"]
                for z, name in marks_model.level_marks(self.doc):
                    a3, b3 = origin + u * x0 + v * z, origin + u * x1 + v * z
                    line((x0, z), (x1, z), "level")
                    s = level["size"] * mm
                    if level["mark"] == "triangle":
                        solid.append([b3, b3 - u * s + v * s * 1.4, b3 + u * s + v * s * 1.4])
                    elif level["mark"] == "target":          # (a circle quartered, two quarters black)
                        pts = [b3 + (u * math.cos(j * math.pi / 8) + v * math.sin(j * math.pi / 8)) * s
                               for j in range(17)]
                        lines.extend(p for a, b in zip(pts, pts[1:]) for p in (a, b))
                        lines.extend((b3 - u * s, b3 + u * s, b3 - v * s, b3 + v * s))
                        solid.append([b3, b3 + u * s, b3 + v * s])
                        solid.append([b3, b3 - u * s, b3 - v * s])
                    texts.append((b3 + u * 2.5 * mm + v * 2.0 * mm,
                                  "{}  {}".format(marks_model.level_text(z, decimal_sep()), name), "bottom-left",
                                  level["text"]))
        for detail in getattr(self.doc, "details", ()):        # (its detail views' callouts, 0.133)
            if tuple(detail.parent) != tuple(view):
                continue
            x0, y0, x1, y1 = detail.rect
            corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
            for a2, b2 in zip(corners, corners[1:] + corners[:1]):
                line(a2, b2, "detail")
            r = styles["detail"]["size"] * mm
            c2 = np.array((x1 + r * 1.6, y1 + r * 1.6))
            lines += [to3((x1, y1)), to3(c2) - (u + v) * r * 0.7]
            head(c2, marks_model.short_tag(detail.name), None, ("detail", detail.uid), "detail")
        if lines:
            self._mark_objects.append(gfx.Line(gfx.Geometry(positions=_f32(lines)), _mat(gfx.LineSegmentMaterial,
                thickness=1.2, color=MARK_COLOR, aa=True, **overlay)))
        if dashed:
            self._mark_objects.append(gfx.Line(gfx.Geometry(positions=_f32(dashed)), _mat(gfx.LineSegmentMaterial,
                thickness=1.2, color=MARK_COLOR, dash_pattern=(10, 3, 2, 3), aa=True, **overlay)))
        if short_dashes:
            self._mark_objects.append(gfx.Line(gfx.Geometry(positions=_f32(short_dashes)),
                                               _mat(gfx.LineSegmentMaterial, thickness=1.2, color=MARK_COLOR,
                                                    dash_pattern=(6, 3), aa=True, **overlay)))
        for tri in solid:
            self._mark_objects.append(gfx.Mesh(gfx.Geometry(positions=_f32(tri), indices=np.array([[0, 1, 2]],
                                                                                                    np.uint32)),
                                               _mat(gfx.MeshBasicMaterial, color=MARK_COLOR, side="both", **overlay)))
        for item in texts:
            at, text = item[0], item[1]
            size = item[3] if len(item) > 3 else 4.8          # (0.360: its style's height, mm; 4,8 mm → 12 px)
            label = gfx.Text(text=text, font_size=max(7.0, 12.0 * size / 4.8), screen_space=True,
                             anchor=item[2] if len(item) > 2 else "middle-center",
                             material=_mat(gfx.TextMaterial, color=MARK_COLOR, outline_color="#ffffff",
                                                       outline_thickness=0.3, **overlay))
            label.local.position = tuple(float(c) for c in at)
            self._mark_objects.append(label)
        if self.plan:
            self._clip(*[w.material for w in self._mark_objects])
        for wobj in self._mark_objects:
            self.scene.add(wobj)

    def _show_services_above(self):
        """In a plan (0.135), the pipes and ducts of the storey above its cut — clipped away with the rest — drawn
        as their outline seen from above, dashed, as in a drawn plan (the selected ones in the selection's colour);
        a click on one picks it (services_at)."""
        for wobj in self._above_objects:
            self.scene.remove(wobj)
        self._above_objects, self._above_shapes = [], []
        if not self.plan or self.doc.loading:
            return
        from shapely.geometry import MultiPoint
        from ..model.drawings import SERVICES
        cut = self.cut_level()
        z = cut - DIM_DEPTH
        drawn = {False: [], True: []}
        for o in self.doc.objects.values():
            if not o.is_bim or o.ifc_class not in SERVICES or o.storey != self.doc.active_storey \
                    or o.ifc_class in self.hidden_classes:
                continue
            box = o.mesh.bounds()
            if box is None or float(box[0][2]) <= cut + 1e-6:
                continue
            hull = MultiPoint([(float(p[0]), float(p[1])) for p in o.mesh.verts]).convex_hull
            if hull.geom_type != "Polygon":
                continue
            self._above_shapes.append((o.id, hull))
            ring = [np.array((x, y, z)) for x, y in list(hull.exterior.coords)[:-1]]
            drawn[o.id in self.selection] += [p for a, b in zip(ring, ring[1:] + ring[:1]) for p in (a, b)]
        overlay = dict(depth_test=False, depth_write=False, render_queue=OVERLAY_QUEUE)
        for selected, segs in drawn.items():
            if segs:
                self._above_objects.append(gfx.Line(gfx.Geometry(positions=_f32(segs)), _mat(gfx.LineSegmentMaterial,
                    thickness=2.0 if selected else 1.3, color=EDGE_SELECTED if selected else "#3f6f9f",
                    dash_pattern=(8, 4), aa=True, **overlay)))
        # (0.140) the free zones in front of the fixtures, dashed green
        from ..model.drawings import free_zones
        zones = [np.array((x, y, z)) for ring in free_zones(self.doc, self.doc.active_storey)
                 for a, b in zip(ring, np.roll(ring, -1, axis=0)) for x, y in (a, b)]
        if zones:
            self._above_objects.append(gfx.Line(gfx.Geometry(positions=_f32(zones)), _mat(gfx.LineSegmentMaterial,
                thickness=1.2, color="#3c8c4d", dash_pattern=(6, 4), aa=True, **overlay)))
        # (0.136) the pipes that fall: an arrow beside each and its slope, as on paper (sized at the view's scale)
        from ..model.drawings import electrical_points, slope_labels
        from ..model.symbols import slope_mark
        try:
            mm = (self.doc.view_settings(self.current_view()).scale or 100) / 1000.0
        except Exception:
            mm = 0.1
        # (0.143) the electrical points' symbols, as on paper
        from ..ifc.electrical import point_symbol
        marks = []
        for kind, back, angle in electrical_points(self.doc, self.doc.active_storey):
            lines, solids = point_symbol(kind, back, angle, mm)
            marks += [np.array((p[0], p[1], z)) for a, b in lines for p in (a, b)]
            for poly in solids:
                ring = [np.array((p[0], p[1], z)) for p in poly]
                marks += [q for a, b in zip(ring, ring[1:] + ring[:1]) for q in (a, b)]
        if marks:
            self._above_objects.append(gfx.Line(gfx.Geometry(positions=_f32(marks)), _mat(gfx.LineSegmentMaterial,
                thickness=1.4, color="#7a2a8a", aa=True, **overlay)))
        arrows = []
        for mid, down, text, radius in slope_labels(self.doc, self.doc.active_storey):
            a, b, head, at, _angle = slope_mark(mid, down, radius, mm)
            arrows += [np.array((a[0], a[1], z)), np.array((b[0], b[1], z))]
            tri = [np.array((q[0], q[1], z)) for q in head]
            self._above_objects.append(gfx.Mesh(gfx.Geometry(positions=_f32(tri), indices=np.array([[0, 1, 2]], np.uint32)),
                                                _mat(gfx.MeshBasicMaterial, color="#3f6f9f", side="both", **overlay)))
            label = gfx.Text(text=text, font_size=11, screen_space=True, anchor="middle-center",
                             material=_mat(gfx.TextMaterial, color="#3f6f9f", outline_color="#ffffff", outline_thickness=0.3,
                                                       **overlay))
            label.local.position = (float(at[0]), float(at[1]), z)
            self._above_objects.append(label)
        if arrows:
            self._above_objects.append(gfx.Line(gfx.Geometry(positions=_f32(arrows)), _mat(gfx.LineSegmentMaterial,
                thickness=1.2, color="#3f6f9f", aa=True, **overlay)))
        self._clip(*[w.material for w in self._above_objects])
        for wobj in self._above_objects:
            self.scene.add(wobj)

    def services_at(self, x, y):
        """The pipe or duct above a plan's cut whose outline is under (x, y) (0.135), or None."""
        if not self._above_shapes:
            return None
        from shapely.geometry import Point
        origin, direction = self.ray(x, y)
        if abs(direction[2]) < 1e-9:
            return None
        z = self.cut_level()
        p = origin + direction * (z - origin[2]) / direction[2]
        q = Point(float(p[0]), float(p[1]))
        reach = SYMBOL_PICK_PX * self.world_per_pixel(p)
        for obj_id, poly in self._above_shapes:
            if poly.distance(q) <= reach:
                return obj_id
        return None

    def mark_at(self, x, y):
        """The view whose mark's head (a section's, an elevation's) is under (x, y) in a plan (0.121):
        ("section", name) | ("elevation", side) — or a detail view's callout (0.133): ("detail", uid) —, or
        None."""
        plane = self.view_plane()
        if plane is None or not self._mark_heads:
            return None
        origin, _u, _v, normal = plane
        ray_o, ray_d = self.ray(x, y)
        p = ray_plane(ray_o, ray_d, origin, normal)
        if p is None:
            p = ray_plane(ray_o, ray_d, origin, -normal)
        if p is None:
            return None
        for centre, r, ref in self._mark_heads:
            if float(np.linalg.norm(p - centre)) <= r * 1.15:
                return ref
        return None

    def annotation_at(self, x, y):
        """What is drawn in the view shown (0.120) within a few pixels of (x, y) — a line, a region's edge, a
        text (near where it starts) — or None."""
        plane = self.view_plane()
        if plane is None or (not len(self._ann_segments) and not self._ann_texts):
            return None
        origin, u, v, normal = plane
        ray_o, ray_d = self.ray(x, y)
        p = ray_plane(ray_o, ray_d, origin, normal)
        if p is None:
            p = ray_plane(ray_o, ray_d, origin, -normal)
        if p is None:
            return None
        pixel = self.world_per_pixel(p)
        reach = SYMBOL_PICK_PX * pixel
        for at, ann in self._ann_texts:                 # (a text: the box of its letters, from where it starts)
            du, dv = float((p - at) @ u), float((p - at) @ v)
            if -reach <= du <= len(ann.text) * 8.5 * pixel + reach and -reach <= dv <= 14 * pixel + reach:
                return ann
        if not len(self._ann_segments):
            return None
        a, b = self._ann_segments[:, 0], self._ann_segments[:, 1]
        ab = b - a
        t = np.clip(np.einsum("ij,ij->i", p - a, ab) / np.maximum(np.einsum("ij,ij->i", ab, ab), 1e-12), 0, 1)
        dist = np.linalg.norm(a + ab * t[:, None] - p, axis=1)
        k = int(np.argmin(dist))
        return self._ann_owner[k] if dist[k] <= reach else None

    def select_annotations(self, anns):
        before = set(self.selected_annotations)
        self.selected_annotations = set(anns)
        self._show_annotations()
        if self.selected_annotations != before:
            for fn in self.annotation_listeners:
                fn(self.selected_annotations)

    def _show_dimensions(self):
        """The dimensions of the view shown: extension lines, the line with 45° ticks, the value — and what is
        drawn in it (0.120)."""
        self._show_annotations()
        for wobj in self._dim_objects:
            self.scene.remove(wobj)
        self._dim_objects, self._dim_lines, self._dim_owner, self._dim_texts = [], np.zeros((0, 2, 3)), [], []
        self.selected_dims &= set(self.doc.dimensions)
        plane = self.view_plane()
        view = self.current_view()
        dims = self.doc.dimensions_of(view) if plane is not None else []
        if not dims:
            return
        origin, u, v, _n = plane
        to3 = lambda p: origin + u * p[0] + v * p[1]               # noqa: E731
        # (0.398) as on paper, at the view's scale: laid out by core/dim_layout as each one's type says
        project = dims_model.clean_style(getattr(self.doc, "dim_style", None))
        try:
            scale = self.doc.view_settings(view).scale or 100
        except Exception:
            scale = 100
        pen = styles_model.pen(getattr(self.doc, "graphic_style", None), "dimension")
        pieces, owners, angular, main = [], [], [], []
        for dim in dims:
            if dim.vertex is not None:
                angular.append(dim)
                continue
            piece = dims_model.piece_of(self.doc, dim, origin, u, v, project, decimal_sep())
            if piece is None:
                continue
            pieces.append(piece)
            owners.append(dim)
            if dim.tag != "grid":                        # (the grid's own, 0.91: drawn, not picked)
                main.append((to3(piece[2]), to3(piece[3])))
                self._dim_owner.append(dim)
        layout = dim_layout.of_drawing(pieces, project, scale / 1000.0, pen)
        for dim in angular:                             # (an angular one, 0.122: its arc, marks, the angle)
            a, b = dims_model.ends(self.doc, dim)
            a2, b2, v2, at2 = notes2d.to2([a, b, dims_model.vertex_point(self.doc, dim),
                                           dims_model.line_point(self.doc, dim)], origin, u, v)
            arc = dims_model.angle_arc(a2, b2, v2, at2)
            if arc is None:
                continue
            r, start, sweep, value = arc
            k = len(owners)
            owners.append(dim)
            drawn = dim_layout.angle_layout(v2, r, start, sweep, dims_model.angle_text(value, decimal_sep()), a2, b2,
                                            dims_model.style_of(project, dim), scale / 1000.0, pen, owner=k)
            layout.extend(drawn)
            for p, q, *_rest in drawn.lines[:max(int(math.degrees(sweep) / 3.0), 2)]:
                main.append((to3(p), to3(q)))
                self._dim_owner.append(dim)
        chains = {d.chain for d in self.selected_dims if d.chain}
        picked = [d in self.selected_dims or (d.chain is not None and d.chain in chains) for d in owners]
        self._dim_objects = self._layout_objects(layout, to3, u, v, picked)
        for item in layout.texts:                       # (a click on a value picks its dimension too)
            if 0 <= item.owner < len(owners) and owners[item.owner].tag != "grid":
                turn = math.radians(item.angle)
                along = u * math.cos(turn) + v * math.sin(turn)
                self._dim_texts.append((to3(item.at), along, np.cross(np.cross(u, v), along),
                                        (item.size[0] / 2, item.size[1] / 2), owners[item.owner]))
        self._dim_lines = np.array(main).reshape(-1, 2, 3)
        if self.plan:                                   # (a plan's crop region: its dimensions inside it only)
            self._clip(*[w.material for w in self._dim_objects])
        else:                                           # (0.402: texts are used again — not a plan's crop then)
            for w in self._dim_objects:
                w.material.clipping_planes = []
        for wobj in self._dim_objects:
            self.scene.add(wobj)
        self.redraw()

    def _layout_objects(self, layout, to3, u, v, picked=()):
        """(0.398) A core.dim_layout.Layout as scene objects in the view shown (its 2D frame to3, u, v): its lines by
        thickness, its filled marks, the boxes behind its texts in the canvas's paper, its texts laid in the view's
        plane (turned, their height in the model); the pieces `picked` (by owner) in the selection's blue."""
        def colour(c, owner):
            if 0 <= owner < len(picked) and picked[owner]:
                return EDGE_SELECTED
            return EDGE_COLOR if c.lower() in ("#000000", "#000") else c
        objects = []
        groups = {}
        for a, b, pen_mm, c, owner in layout.lines:
            px = 1.2 if pen_mm <= 0.26 else min(1.2 + (pen_mm - 0.26) * 6.0, 4.0)
            segs, cols = groups.setdefault(round(px, 1), ([], []))
            segs += [to3(a), to3(b)]
            rgba = _physical(colour(c, owner))
            cols += [rgba, rgba]
        for px, (segs, cols) in groups.items():
            objects.append(gfx.Line(gfx.Geometry(positions=_f32(segs), colors=np.array(cols, np.float32)),
                                    _mat(gfx.LineSegmentMaterial, thickness=px, color_mode="vertex", aa=True)))
        fills = {}
        for pts, c, owner in layout.fills:
            fills.setdefault(colour(c, owner), []).append(pts)
        backs = [corners for corners, _owner in layout.backs]
        for c, polys in list(fills.items()) + ([("#ffffff", backs)] if backs else []):
            pos, idx = [], []
            for pts in polys:
                base = len(pos)
                pos += [to3(p) for p in pts]
                idx += [(base, base + k, base + k + 1) for k in range(1, len(pts) - 1)]
            if idx:
                mesh = gfx.Mesh(gfx.Geometry(positions=_f32(pos), indices=np.array(idx, np.uint32)),
                                _mat(gfx.MeshBasicMaterial, color=c, side="both"))
                if c == "#ffffff":
                    mesh.render_order = 1               # (the paper behind a value: over its line, under its text)
                objects.append(mesh)
        z = np.cross(u, v)
        # (a text costs ~1 ms to make: those of the last time, the same words, size and colour, are used again)
        pool, kept = getattr(self, "_text_pool", {}), {}
        for item in layout.texts:
            c = colour(item.colour, item.owner)
            words = item.text.replace("*", "\\*").replace("_", "\\_")
            if item.bold or item.italic:
                mark = "***" if item.bold and item.italic else "**" if item.bold else "*"
                words = mark + words + mark
            ink = "#1e1e1e" if c == EDGE_COLOR else c
            key = (words, round(float(item.height), 6), ink, views_canvas.DARK)
            spare = pool.get(key)
            if spare:
                label = spare.pop()
            else:
                label = gfx.Text(markdown=words, font_size=float(item.height), screen_space=False,
                                 anchor="middle-center", material=_mat(gfx.TextMaterial, color=ink))
            kept.setdefault(key, []).append(label)
            turn = math.radians(item.angle)
            x = u * math.cos(turn) + v * math.sin(turn)
            label.local.rotation = _quat_of(x, np.cross(z, x), z)
            label.local.scale = (float(item.width or 1.0), 1.0, 1.0)
            label.local.position = tuple(float(q) for q in to3(item.at) + z * 1e-3)
            label.render_order = 2
            objects.append(label)
        self._text_pool = kept
        return objects

    def dimension_at(self, x, y):
        """The dimension whose line is within a few pixels of (x, y) in the view shown — (0.398) or whose value is
        under it —, or None."""
        if not len(self._dim_lines) and not self._dim_texts:
            return None
        origin, _u, _v, normal = self.view_plane()
        ray_o, ray_d = self.ray(x, y)
        p = ray_plane(ray_o, ray_d, origin, normal)
        if p is None:
            p = ray_plane(ray_o, ray_d, origin, -normal)
        if p is None:
            return None
        for centre, along, across, (hw, hh), dim in self._dim_texts:
            q = p - centre
            if abs(float(q @ along)) <= hw and abs(float(q @ across)) <= hh:
                return dim
        if not len(self._dim_lines):
            return None
        a, b = self._dim_lines[:, 0], self._dim_lines[:, 1]
        ab = b - a
        t = np.clip(np.einsum("ij,ij->i", p - a, ab) / np.maximum(np.einsum("ij,ij->i", ab, ab), 1e-12), 0, 1)
        dist = np.linalg.norm(a + ab * t[:, None] - p, axis=1)
        k = int(np.argmin(dist))
        return self._dim_owner[k] if dist[k] <= SYMBOL_PICK_PX * self.world_per_pixel(p) else None

    def select_dimensions(self, dims):
        before = set(self.selected_dims)
        self.selected_dims = set(dims)
        self._show_dimensions()
        if self.selected_dims != before:                 # (0.193: the Properties show them)
            for fn in self.annotation_listeners:
                fn(self.selected_annotations)

    def symbol_at(self, x, y):
        """The door whose plan symbol is within a few pixels of (x, y), in a plan, or None."""
        if not len(self._symbol_segments):
            return None
        origin, direction = self.ray(x, y)
        level = float(self._symbol_segments[0, 0, 2])
        if abs(direction[2]) < 1e-9:
            return None
        p = origin + direction * (level - origin[2]) / direction[2]
        a, b = self._symbol_segments[:, 0, :2], self._symbol_segments[:, 1, :2]
        ab = b - a
        t = np.clip(np.einsum("ij,ij->i", p[:2] - a, ab) / np.maximum(np.einsum("ij,ij->i", ab, ab), 1e-12), 0, 1)
        d = np.linalg.norm(a + ab * t[:, None] - p[:2], axis=1)
        k = int(np.argmin(d))
        return self._symbol_owner[k] if d[k] <= SYMBOL_PICK_PX * self.world_per_pixel(p) else None

    def _show_guides(self):
        if self._guides is not None:
            self.scene.remove(self._guides)
            self._guides = None
        segs = []
        lift = np.array((0.0, 0.0, EDGE_LIFT))     # not hidden by the ground grid's lines
        for g in self.doc.guides.values():
            segs += [g.point - g.direction * GUIDE_HALF_LENGTH + lift, g.point + g.direction * GUIDE_HALF_LENGTH + lift]
        if segs:
            self._guides = gfx.Line(gfx.Geometry(positions=_f32(segs)),
                                    _mat(gfx.LineSegmentMaterial, thickness=1.2, color=GUIDE_COLOR, dash_pattern=(5, 4)))
            self.scene.add(self._guides)
        self.redraw()

    def _remove_view(self, obj_id):
        self._on_host.discard(obj_id)
        self.bim.remove(obj_id)
        self._meshes.pop(obj_id, None)
        view = self._views.pop(obj_id, None)
        if view is not None:
            self.objects.remove(view.group)
            if view.faces is not None:
                self._by_wobj.pop(id(view.faces), None)
            self._by_wobj.pop(id(view.edges), None)

    def set_colours(self, colours):
        """Graphic rules: {GlobalId: colour} instead of the colours by class (an empty dict: back
        to them). The selection stays blue."""
        old, self.colours = self.colours, dict(colours)
        for obj_id in set(old) | set(self.colours):
            obj = self.doc.get(obj_id)
            if obj is not None and obj.is_bim and obj_id in self.bim:
                self.bim.recolor(obj_id, *self._bim_colors(obj))
        # (in a plan or section, the cut in those colours too — 0.315: or in its materials')
        self.bim.set_poche_colours(bool(self.colours) or self._dressing[0] == "material")
        self.redraw()

    def _own_colour(self, obj):
        """An element's own colour over its class's: a pipe's system's (0.141), a cabinet's fronts' finish's
        (0.243) — or None."""
        colour = self._system_colour(obj)
        if colour is None and obj.ifc_class == "IfcFurniture":
            try:
                colour = self.doc.ifc.cabinet_colour(obj.id)
            except (AttributeError, RuntimeError):        # (0.394: a file still being read — its class's colour
                colour = None                             # until it is, then drawn again; it stopped the preview)
        return colour

    def _system_colour(self, obj):
        """(0.141) A pipe's / duct's / fitting's colour: its system's (cold water blue, sewage brown…), or None."""
        if obj.ifc_class not in SYSTEM_CLASSES:
            return None
        from ..ifc.systems import SYSTEMS
        key = self.doc.system_of(obj.id) if hasattr(self.doc, "system_of") else None
        return SYSTEMS[key][3] if key in SYSTEMS else None

    def _bim_colors(self, obj):
        """Per-vertex colours for the batches. They are used as physical (linear) values,
        unlike a material's colour, which pygfx converts from sRGB: convert them the same way."""
        selected = obj.id in self.selection
        face = FACE_SELECTED if selected else (self.colours.get(obj.id) or self._own_colour(obj)
                                               or BIM_COLORS.get(obj.ifc_class, BIM_DEFAULT))
        edge = EDGE_SELECTED if selected else EDGE_COLOR
        dark = self._model_dark()                     # (0.341: a plan's / section's greys turned over, dark views)
        lit = self._edges_light()                     # (0.341: its edges against what is behind them)
        if not selected and obj.id not in self.colours and self._own_colour(obj) is None:
            dressed = self._dress(obj)
            if dressed is not None and dressed[0] is not None:
                # (0.315: its materials' colours, layer by layer — 0.341: kept on the dark views, and its edges dark
                # on them, unless no face is drawn behind)
                return dressed[0], _physical_in(edge, self._edges_light(materials=True))
        if not selected and obj.id not in self.colours and getattr(obj.mesh, "colors", None) is not None \
                and self._own_colour(obj) is None:
            return None, _physical_in(edge, lit)      # (0.259: its parts in their own colours, the Piece's)
        return _physical_in(face, dark), _physical_in(edge, lit)

    def _edges_light(self, materials=False):
        """(0.341) The elements' edges light on the dark views: in a plan, a section or an elevation, on their faces
        turned over (dark) — not on faces in their materials' colours (materials: the element's are, kept light); in
        the 3D view, where the faces keep their colours, only when no face is drawn behind them (wireframe: the dark
        ground is; x-ray's see-through faces, one over another, come out light)."""
        if not views_canvas.DARK:
            return False
        if self.bim.style == "wire":
            return True
        return self._model_dark() and not materials

    def _dress(self, obj):
        """(0.315) An element seen by its materials, as the view style says (_dressing): (each vertex's colour (3T, 4)
        or None — its category's —, its surface patterns (segments' ends (2M, 3), colours (2M, 4)) or None, has it
        see-through parts) — kept until its shape or the materials change. None when the style dresses nothing."""
        colours, patterns, clear = self._dressing
        override = self._surface_override(obj)
        if not obj.is_bim:
            return None
        from ..model import paint as paint_model
        painted = paint_model.signature(getattr(self.doc, "ifc", None), obj.id)     # (0.391: its paint, any style)
        if (colours, patterns, clear) == ("category", False, False) and override is None and not painted:
            return None
        from ..ifc import catalog
        mesh = obj.mesh
        kept = self._dressed.get(obj.id)
        key = (self._dressing, override, self._model_dark(), painted)  # (0.341: its patterns' colours turned over)
        if kept is not None and kept[0] is mesh and kept[1] == catalog.GENERATION and kept[2] == key:
            return kept[3]
        if colours == "category" and not clear and override is None and not painted and \
                not material_looks.may_have_patterns(getattr(self.doc, "ifc", None), obj):
            made = None                         # (0.317: only patterns asked, and none of its materials has any)
        else:
            made = self._dress_made(obj, override)
        self._dressed[obj.id] = (mesh, catalog.GENERATION, key, made)
        return made

    def pattern_line_at(self, x, y, radius_px=PATTERN_PICK_PX):
        """(0.332) The surface pattern's line (a tile's joint, a brick course) under the mouse, on the face of an
        element picked there: (element, the face's unit normal, a point of the line on the face, its unit direction)
        — the nearest within radius_px pixels — or None (no pattern shown on that face)."""
        hit = self.pick_point(x, y)
        if hit is None:
            return None
        obj = self.doc.get(hit[0])
        if obj is None or not obj.is_bim or hit[0] not in self.bim.where:
            return None
        dressed = self._dress(obj)
        if dressed is None or dressed[1] is None or not len(dressed[1][0]):
            return None
        mesh, matrix = self._meshes[hit[0]]
        n = normalize(np.asarray(face_world_normal(matrix, mesh, hit[1]), dtype=float))
        p = np.asarray(hit[2], dtype=float)
        ends = np.asarray(dressed[1][0], dtype=float).reshape(-1, 2, 3)
        along = ends[:, 1] - ends[:, 0]
        length = np.linalg.norm(along, axis=1)
        unit = along / np.maximum(length, 1e-12)[:, None]
        keep = (length > 1e-9) & (np.abs((ends.mean(axis=1) - p) @ n) < PATTERN_ON_FACE) \
            & (np.abs(unit @ n) < 1e-3)                                                # (lying on that face)
        if not keep.any():
            return None
        ends = ends[keep]
        xy = self.project_many(ends.reshape(-1, 3)).reshape(-1, 2, 2)
        a, ab = xy[:, 0], xy[:, 1] - xy[:, 0]
        at = np.array((float(x), float(y)))
        with np.errstate(divide="ignore", invalid="ignore"):
            s = np.clip(((at - a) * ab).sum(axis=1) / (ab * ab).sum(axis=1), 0.0, 1.0)
        dist = np.nan_to_num(np.linalg.norm(a + ab * s[:, None] - at, axis=1), nan=np.inf)
        k = int(np.argmin(dist))
        if dist[k] > radius_px:
            return None
        a3, b3 = ends[k]
        point = a3 - float((a3 - p) @ n) * n                 # (on the face: the lines are a hair off it)
        return obj.id, n, point, normalize(b3 - a3)

    def _surface_override(self, obj):
        """(0.318) The view style's surface hatches for an element's category, or None — (0.331) the view's own for that
        element first."""
        mine = self.element_hatches.get(obj.id)
        if mine is not None and (mine[2] or mine[3]):
            return mine[2], mine[3]
        if not self.vstyle.categories:
            return None
        found = self.vstyle.category(obj.ifc_class)
        return (found[2], found[3]) if found is not None and (found[2] or found[3]) else None

    def _dress_made(self, obj, override=None):
        """(model/material_looks.py) The element's colours by vertex (physical, with their alpha), its surface
        patterns' lines and their colours, see-through parts, its triangles cut along its layers — (0.318) the view
        style's surface hatches for its category instead of its materials' (override)."""
        colours, patterns, clear = self._dressing
        base = gfx.Color(BIM_COLORS.get(obj.ifc_class, BIM_DEFAULT)).rgb[:3]
        seen = material_looks.look(getattr(self.doc, "ifc", None), obj, base, colours == "material",
                                   patterns or override is not None, clear, lift=EDGE_LIFT * 0.6, surface=override)
        if not len(seen.corners):
            return None, None, False, None
        face = None
        if colours == "material" or seen.see_through or seen.painted:
            face = np.column_stack((physical(np.clip(seen.rgb, 0.0, 1.0)), seen.alpha)).astype(np.float32)
            face = np.repeat(face, 3, axis=0)
        pattern = None
        if seen.patterns:
            dark = self._model_dark()                   # (0.341: a plan's / section's on the dark views turned over)
            pattern = (np.concatenate([s.reshape(-1, 3) for s, _c in seen.patterns]),
                       np.concatenate([np.tile(np.append(_physical_in(c, dark)[:3], 1.0), (len(s) * 2, 1))
                                       for s, c in seen.patterns]))
        split = (seen.corners, seen.faces, seen.normals) if seen.split else None
        return face, pattern, seen.see_through, split

    def _update_seams(self, changed, removed):
        """(0.320) The seams of the elements that changed or went and of those round them (model/seen_joins.py) —
        all once the file's IFC is read (its materials). Returns those whose seams changed (to be shown again). Many
        at once (a file opened, a group's copies changed) are worked out a few at a time after each image
        (_seam_chunk), the window never held."""
        if getattr(self.doc, "loading", False):
            self._seams_read = False                   # (the materials not known yet: all of them once they are)
            self._seam_queue.clear()
            self._seam_again.clear()
            return set()
        every = not self._seams_read
        self._seams_read = True
        affected = set()
        for obj_id in removed:
            affected |= self._neighbours.near(self._neighbours.boxes.get(obj_id))
            self._neighbours.remove(obj_id)
            for kept in (self._seams, self._seam_planes, self._seam_infos, self._seam_apart):
                kept.pop(obj_id, None)
        objects = [self.doc.get(k) for k in (self.doc.objects if every else changed) if not isinstance(k, str)
                   or not k.startswith("__")]
        for obj in objects:
            if obj is None:
                continue
            if not every and obj.id in self._neighbours.boxes:
                affected |= self._neighbours.near(self._neighbours.boxes[obj.id])
            self._seam_infos.pop(obj.id, None)
            self._seam_apart.pop(obj.id, None)
            if seen_joins.joinable(obj) and obj.mesh.bounds() is not None:
                self._neighbours.update(obj.id, obj.mesh.bounds())
                affected |= {obj.id} if every else self._neighbours.near(obj.mesh.bounds())
            else:
                self._neighbours.remove(obj.id)
                self._seams.pop(obj.id, None)
        affected -= set(removed)
        if every or len(affected) > SEAMS_AT_ONCE:
            self._seam_queue |= affected
            self.after_next_draw(self._seam_chunk)
            return set()
        return {obj_id for obj_id in affected if self._reseam(obj_id)}

    def _seam_chunk(self):
        """(0.320) Some of the seams waiting worked out (for SEAMS_BUDGET), those changed shown again; the rest after
        the next image."""
        start = time.perf_counter()
        while self._seam_queue and time.perf_counter() - start < SEAMS_BUDGET:
            obj_id = self._seam_queue.pop()
            if self._reseam(obj_id):
                self._seam_again.add(obj_id)
        # (shown again together — each batch made again once — when all are done, or now and then till then)
        if not self._seam_queue or start - self._seam_shown > SEAMS_SHOW_EVERY:
            for obj_id in self._seam_again:
                obj = self.doc.get(obj_id)
                if obj is not None and obj_id in self.bim.where:
                    self.show_object(obj_id, obj.mesh)
            self._seam_again = set()
            self._seam_shown = start
        if self._seam_queue:
            self.after_next_draw(self._seam_chunk)

    def _reseam(self, obj_id):
        """(0.320) An element's seams worked out again: True when they changed (it is to be shown again)."""
        obj = self.doc.get(obj_id)
        if obj is None:
            return False
        found = self._seams_of(obj)
        old = self._seams.get(obj_id)
        if (old[1] if old is not None and old[0] is obj.mesh else None) is None and found is None:
            self._seams.pop(obj_id, None)
            return False
        changed = old is None or old[0] is not obj.mesh or not _same_seams(old[1], found)
        self._seams[obj_id] = (obj.mesh, found)
        return changed

    def _seams_of(self, obj):
        """(0.320) An element's seams with the elements round it (seen_joins.seams), or None."""
        near = [k for k in self._neighbours.near(obj.mesh.bounds()) if k != obj.id]
        if near:                                            # (0.333: not those unjoined from it by hand)
            apart = self._seam_apart.get(obj.id)
            if apart is None:
                apart = self._seam_apart[obj.id] = seen_joins.unjoined_from(getattr(self.doc, "ifc", None), obj.id)
            near = [k for k in near if k not in apart]
        mine = self._seam_planes_of(obj) if near else None
        if mine is None or self._seam_info(obj) is None:
            return None
        others = []
        for k in near:
            other = self.doc.get(k)
            planes = self._seam_planes_of(other) if other is not None else None
            if planes is not None and seen_joins.share_plane(mine, planes) and self._seam_info(other) is not None:
                others.append((other.mesh, planes, self._seam_info(other)))
        if not others:
            return None
        return seen_joins.seams(obj.mesh, mine, self._seam_info(obj), others)

    def _seam_planes_of(self, obj):
        if not seen_joins.joinable(obj):
            return None
        kept = self._seam_planes.get(obj.id)
        if kept is None or kept[0] is not obj.mesh:
            kept = self._seam_planes[obj.id] = (obj.mesh, seen_joins.Planes(obj.mesh))
        return kept[1]

    def _seam_info(self, obj):
        if obj.id not in self._seam_infos:
            self._seam_infos[obj.id] = seen_joins.material_info(getattr(self.doc, "ifc", None), obj.id)
        return self._seam_infos[obj.id]

    def _recheck_sheets(self, changed, removed):
        """A wall or slab changed, came or went: the flat sketches lying on it (shown as their outline
        only) or round it are looked at again. Every one when a file's IFC has been read."""
        if self.on_host_face is None:
            return
        boxes = [o.mesh.bounds() for o in map(self.doc.get, changed)
                 if o is not None and o.is_bim and o.mesh.bounds() is not None]
        every = STOREY_CHANGED in changed
        if not boxes and not every and not (removed and self._on_host):
            return
        for obj in list(self.doc.sketches()):
            if obj.id in changed or len(obj.mesh.faces) != 1 or obj.mesh.is_closed():
                continue
            if every or obj.id in self._on_host or self._near(obj, boxes):
                self.show_object(obj.id, obj.mesh)

    @staticmethod
    def _near(obj, boxes):
        pts = np.asarray(obj.mesh.verts, float) @ obj.matrix[:3, :3].T + obj.matrix[:3, 3]
        lo, hi = pts.min(axis=0), pts.max(axis=0)
        return any(np.all(lo >= b[0] - 1e-3) and np.all(hi <= b[1] + 1e-3) for b in boxes)

    def show_object(self, obj_id, mesh):
        """(Re)build the display of one object, from the document or from a preview mesh."""
        obj = self.doc.get(obj_id)
        if obj.is_bim:
            # IFC element: into its storey's batch (rebuilt once, just before the next image)
            view = self._views.pop(obj_id, None)
            if view is not None:
                self.objects.remove(view.group)
            piece = self._ready.pop(obj_id, None)
            dressed = self._dress(obj) if mesh is obj.mesh else None       # (0.315: by its materials)
            if dressed is not None:
                self._shown_dressed.add(obj_id)
            else:
                self._shown_dressed.discard(obj_id)
            seams = self._seams.get(obj_id)                                # (0.320: its seams left out)
            seams = seams[1] if seams is not None and seams[0] is mesh else None
            if piece is None or piece.source is not mesh or obj_id in self.selection or obj_id in self.colours \
                    or self._own_colour(obj) is not None or dressed is not None or seams is not None \
                    or piece.seams is not None or self._model_dark():     # (a system's colour, 0.141…; 0.341)
                face, edge = self._bim_colors(obj)
                split = dressed[3] if dressed is not None else None
                if split is not None and not (np.ndim(face) == 2 and len(face) == len(split[0]) * 3):
                    face = np.repeat(np.asarray(face if face is not None else (0.5, 0.5, 0.5, 1.0),
                                                dtype=np.float32).reshape(1, 4), len(split[0]) * 3, axis=0)
                piece = Piece(mesh, obj.matrix, face, edge, ground=obj.ifc_class == TERRAIN_CLASS,
                              pattern=dressed[1] if dressed is not None else None, split=split, seams=seams,
                              turned=self._model_dark())
            self.bim.put(obj_id, piece, self._batch_key(obj))
            self._meshes[obj_id] = (mesh, obj.matrix)
            self.redraw()
            return
        self._remove_view(obj_id)
        selected = obj_id in self.selection

        tris, owner = mesh.triangulate()
        verts = np.array(mesh.verts, dtype=float).reshape(-1, 3)
        if hasattr(mesh, "normals"):   # TriMesh (IFC element): normals already computed
            face_normals = mesh.normals
        else:
            face_normals = np.array([mesh.face_normal(fi) for fi in range(len(mesh.faces))]).reshape(-1, 3)
        if selected:
            color = FACE_SELECTED
        elif obj.is_bim:
            color = BIM_COLORS.get(obj.ifc_class, BIM_DEFAULT)
        else:
            color = FACE_COLOR
        # Open sheets (a rectangle not yet pulled) are lifted a hair so they never
        # flicker against the face they were drawn on, and are picked first.
        sheet_lift = 0.0 if mesh.is_closed() else SHEET_LIFT
        # A part of a wall's / slab's face (a line divided it, a rectangle drawn on it): only its outline is
        # seen on the face, as in SketchUp — its face, there to be picked, lets the wall, its doors and
        # windows and their holes show through (selected: a light tint)
        on_host = (not mesh.is_closed() and len(mesh.faces) == 1 and self.on_host_face is not None
                   and self.on_host_face(obj))
        if on_host:
            self._on_host.add(obj_id)
        else:
            self._on_host.discard(obj_id)
        faces = None                      # objects made only of loose lines have no faces
        dark = self._model_dark()         # (0.341: a plan's / section's greys turned over on the dark views)
        if len(tris):
            lift = np.repeat(face_normals[owner] * sheet_lift, 3, axis=0)
            positions = _f32(verts[tris.reshape(-1)] + lift)
            normals = _f32(np.repeat(face_normals[owner], 3, axis=0))
            indices = np.arange(len(positions), dtype=np.uint32).reshape(-1, 3)
            style = self.bim.style                 # (the 3D view's visual style: shaded in a plan or a section)
            if on_host or style == "wire":
                tint = (*gfx.Color(FACE_SELECTED).rgb, 0.45 if selected else 0.0)
                material = _mat(gfx.MeshBasicMaterial, color=tint, alpha_mode="blend", depth_write=False, side="both",
                                pick_write=True)
            elif style == "hidden":
                material = _mat(gfx.MeshBasicMaterial, turn=dark, color=FACE_SELECTED if selected else "#ffffff",
                                side="both", pick_write=True)
            elif style == "xray":
                material = _mat(gfx.MeshPhongMaterial, turn=dark, color=color, specular="#000", flat_shading=True,
                                side="both", opacity=0.3, alpha_mode="blend", depth_write=False, pick_write=True)
            else:
                material = _mat(gfx.MeshPhongMaterial, turn=dark, color=color, specular="#000", flat_shading=True,
                                side="both", pick_write=True)
            extra = {}
            part = self.face_selection.get(obj_id) if not selected and mesh is obj.mesh else None
            if part is not None and not on_host and style != "wire":
                # (0.310) faces picked alone: in the selection's colour, the rest of the sketch as it was
                picked = np.repeat(np.isin(owner, sorted(part[0])), 3)
                plain = gfx.Color(views_canvas.ink("#ffffff" if style == "hidden" else color) if dark
                                  else "#ffffff" if style == "hidden" else color).rgba
                extra["colors"] = np.where(picked[:, None], np.array(gfx.Color(FACE_SELECTED).rgba),
                                           np.array(plain)).astype(np.float32)
                material.color_mode = "vertex"
            paint = mesh.painted() if hasattr(mesh, "painted") else None
            if paint and any(paint) and not on_host and not selected and style not in ("wire", "hidden"):
                # (0.392) its faces painted (the Paint bucket): each in its paint's colour, as a painted element's
                from ..ifc import catalog
                rgb = np.tile(np.array(gfx.Color(views_canvas.ink(color) if dark else color).rgb[:3], dtype=float),
                              (len(owner), 1))
                keys = np.array([paint[fi] or "" if fi < len(paint) else "" for fi in owner], dtype=object)
                for key in set(keys) - {""}:
                    spec = catalog.MATERIALS.get(key)
                    if spec is not None:
                        rgb[keys == key] = spec.color
                if part is not None:
                    rgb[np.isin(owner, sorted(part[0]))] = gfx.Color(FACE_SELECTED).rgb[:3]
                alpha = 0.3 if style == "xray" else 1.0
                extra["colors"] = np.repeat(np.column_stack((physical(np.clip(rgb, 0.0, 1.0)),
                                                             np.full(len(rgb), alpha))), 3, axis=0).astype(np.float32)
                material.color_mode = "vertex"
            faces = gfx.Mesh(gfx.Geometry(positions=positions, normals=normals, indices=indices, **extra), material)

        def edge_segs(items):
            out = []
            for (a, b), fis in items:
                ns = [face_normals[fi] for fi in fis]
                if not ns:                     # a loose line (no face): a hair above the ground grid
                    lifts, base = [np.array((0.0, 0.0, 1.0))], np.zeros(3)
                else:
                    lifts = [normalize(sum(ns))] if len(ns) > 1 else [ns[0], -ns[0]]
                    base = sum(ns) / len(ns) * sheet_lift
                for lift in lifts:
                    out += [verts[a] + base + lift * EDGE_LIFT, verts[b] + base + lift * EDGE_LIFT]
            return out

        visible = mesh.visible_edges()
        segs = edge_segs(visible.items())
        lines_only = faces is None
        edges = gfx.Line(
            gfx.Geometry(positions=_f32(segs) if segs else np.zeros((2, 3), np.float32)),
            _mat(gfx.LineSegmentMaterial, turn=self._edges_light() or (lines_only and views_canvas.DARK),
                 thickness=(3.0 if selected else 2.0) if lines_only else (2.5 if selected else 1.5),
                 color=EDGE_SELECTED if selected else EDGE_COLOR, aa=True, pick_write=lines_only),
        )

        edges.visible = lines_only or self.bim.edges   # (the 3D view's style may leave out the faces' edges)
        group = gfx.Group()
        if lines_only:
            group.add(edges)
        else:
            group.add(faces, edges)
        part = self.face_selection.get(obj_id) if not selected and faces is not None and mesh is obj.mesh else None
        marks = []
        alone = self.line_selection.get(obj_id) if not selected and lines_only and mesh is obj.mesh else None
        if alone:                                         # (0.373) loose lines picked alone: in the selection's colour
            picked = edge_segs([(mesh.lines[k], []) for k in sorted(alone) if k < len(mesh.lines)])
            if picked:
                marks.append(gfx.Line(gfx.Geometry(positions=_f32(picked)),
                                      _mat(gfx.LineSegmentMaterial, thickness=3.5, color=EDGE_SELECTED, aa=True,
                                           pick_write=False)))
                group.add(*marks)
        if part is not None and part[1]:                  # (0.310) picked with their edges (a double click)
            picked = edge_segs([(e, fis) for e, fis in visible.items() if part[0].intersection(fis)])
            if picked:
                marks.append(gfx.Line(gfx.Geometry(positions=_f32(picked)),
                                      _mat(gfx.LineSegmentMaterial, thickness=3.0, color=EDGE_SELECTED, aa=True,
                                                              pick_write=False)))
                group.add(*marks)
        group.local.matrix = obj.matrix
        group.visible = self.is_shown(obj)
        if self.plan:
            self._clip(*[w.material for w in (faces, edges, *marks) if w is not None])
        self.objects.add(group)
        self._views[obj_id] = _ObjectView(group, faces, edges, owner, mesh, obj.matrix)
        self._meshes[obj_id] = (mesh, obj.matrix)
        if faces is not None:
            self._by_wobj[id(faces)] = obj_id
        self._by_wobj[id(edges)] = obj_id
        self.redraw()

    def pick_object(self, x, y):
        """Object under the pixel: a face or a loose line (for selection); in a plan, a door by
        its symbol (a click near its leaf or arc)."""
        door = self.symbol_at(x, y)
        if door is not None:
            return door
        info = self.renderer.get_pick_info((x, y))
        wobj = info.get("world_object") if info else None
        if wobj is None:
            return None
        hit = self.bim.pick(wobj, info.get("face_index"))
        return hit[0] if hit is not None else self._by_wobj.get(id(wobj))

    def refresh_object(self, obj_id):
        obj = self.doc.get(obj_id)
        if obj is None:
            return
        if obj.is_bim and obj_id in self.bim:
            self.bim.recolor(obj_id, *self._bim_colors(obj))   # selection: colours changed in place
            self.redraw()
        else:
            self.show_object(obj_id, obj.mesh)

    def is_visible(self, obj_id):
        """Whether an object is drawn (its storey may be hidden; in a plan, a door by its symbol)."""
        if obj_id in self._symbol_owner:
            return True
        if obj_id in self.bim:
            return self.bim.is_visible(obj_id)
        view = self._views.get(obj_id)
        return view is not None and view.group.visible

    def select_faces(self, parts):
        """(0.310) Faces of sketches picked alone, as SketchUp's click on a face: {obj_id: (frozenset of its face
        indices, with their edges)} — drawn in the selection's colour, the rest of the sketch as it was."""
        old, self.face_selection = self.face_selection, {k: (frozenset(f), bool(e)) for k, (f, e) in parts.items()}
        for obj_id in set(old) | set(self.face_selection):
            if old.get(obj_id) != self.face_selection.get(obj_id) and self.doc.get(obj_id) is not None:
                self.refresh_object(obj_id)
        for fn in self.selection_listeners:
            fn(self.selection)

    def select_lines(self, parts):
        """(0.373) Loose lines picked alone, as SketchUp's click on an edge: {obj_id: frozenset of their indices in the
        sketch's lines} — drawn in the selection's colour, the rest of the sketch as it was."""
        old, self.line_selection = self.line_selection, {k: frozenset(v) for k, v in parts.items() if v}
        for obj_id in set(old) | set(self.line_selection):
            if old.get(obj_id) != self.line_selection.get(obj_id) and self.doc.get(obj_id) is not None:
                self.refresh_object(obj_id)
        for fn in self.selection_listeners:
            fn(self.selection)

    def line_at(self, x, y, radius_px=8):
        """(0.373) The loose line nearest the cursor on the screen, within radius_px: (obj_id, its index in the
        sketch's lines), or None — of the lines-only sketches shown and selectable (thin lines are hard to hit on the
        GPU's pick: measured on the screen)."""
        best = None
        for obj_id, view in self._views.items():          # (the sketches on screen only: no IFC element looked at)
            obj = self.doc.get(obj_id)
            if obj is None or obj.is_bim or obj.mesh.faces or not obj.mesh.lines or not view.group.visible \
                    or not self.selectable(obj):
                continue
            m = obj.matrix
            verts = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
            xy = self.project_many(verts)
            ends = np.asarray(obj.mesh.lines, dtype=np.int64).reshape(-1, 2)
            a, b = xy[ends[:, 0]], xy[ends[:, 1]]
            d = b - a
            dd = np.einsum("ij,ij->i", d, d)
            with np.errstate(divide="ignore", invalid="ignore"):
                s = np.clip(((x - a[:, 0]) * d[:, 0] + (y - a[:, 1]) * d[:, 1]) / dd, 0.0, 1.0)
            s = np.nan_to_num(s)
            dist = np.hypot(a[:, 0] + s * d[:, 0] - x, a[:, 1] + s * d[:, 1] - y)
            dist = np.nan_to_num(dist, nan=np.inf)
            k = int(np.argmin(dist))
            if dist[k] <= radius_px and (best is None or dist[k] < best[0]):
                best = (float(dist[k]), obj.id, k)
        return (best[1], best[2]) if best is not None else None

    def objects_picked(self):
        """(0.310) The objects selected and those whose faces are picked alone: what a command for whole objects
        takes (Classificar como, Fazer componente) — a click on a face of a sketch volume is enough for it."""
        return set(self.selection) | set(self.face_selection)

    def set_selection(self, ids, keep_faces=False):
        if self.face_selection and not keep_faces:
            self.select_faces({})
        if self.line_selection and not keep_faces:
            self.select_lines({})
        old, self.selection = self.selection, set(ids)
        for obj_id in old ^ self.selection:
            self.refresh_object(obj_id)
        if set(self._symbol_owner) & (old ^ self.selection):
            self._show_plan_symbols()                # a door's symbol in the selection colour
        if {g for g, _p in self._above_shapes} & (old ^ self.selection):
            self._show_services_above()              # (a duct above the cut, in the selection colour, 0.135)
            self.redraw()
        if set(self._hatch_parts) & (old ^ self.selection):
            self._assemble_cut_hatches()             # (0.317: its cut in the selection's colour)
            self.redraw()
        for fn in self.selection_listeners:
            fn(self.selection)

    # ------------------------------------------------------------ overlays (tool feedback)

    def _build_overlays(self):
        self._fill = gfx.Mesh(gfx.Geometry(positions=np.zeros((3, 3), np.float32),
                                           indices=np.array([[0, 1, 2]], np.uint32)),
                              _overlay_material(gfx.MeshBasicMaterial, color=PREVIEW_FILL,
                                                alpha_mode="blend", side="both"))
        # (0.383) a solid being drawn (walls by a rectangle, a circle, an arc…): its faces, each shaded by its way
        self._volume = gfx.Mesh(gfx.Geometry(positions=np.zeros((3, 3), np.float32),
                                             indices=np.array([[0, 1, 2]], np.uint32),
                                             colors=np.zeros((3, 4), np.float32)),
                                _overlay_material(gfx.MeshBasicMaterial, color_mode="vertex",
                                                  alpha_mode="blend", side="both"))
        self._lines = gfx.Line(gfx.Geometry(positions=np.zeros((2, 3), np.float32),
                                            colors=np.zeros((2, 4), np.float32)),
                               _overlay_material(gfx.LineSegmentMaterial, thickness=2.5,
                                                 color_mode="vertex", aa=True))
        self._marker = gfx.Points(gfx.Geometry(positions=np.zeros((1, 3), np.float32)),
                                  _overlay_material(gfx.PointsMaterial, size=11, color=PREVIEW, aa=True))
        self._label = gfx.Text(text=" ", font_size=14, screen_space=True, anchor="bottom-left",
                               anchor_offset=14,
                               material=_overlay_material(gfx.TextMaterial, color="#111",
                                                          outline_color="#fff", outline_thickness=0.35))
        self._tip = gfx.Text(text=" ", font_size=12, screen_space=True, anchor="top-left",
                             anchor_offset=12,
                             material=_overlay_material(gfx.TextMaterial, color="#fff",
                                                        outline_color="#333", outline_thickness=0.45))
        # alignments (0.60): dashed lines from the points / edges followed, crosses on the points acquired
        self._align = gfx.Line(gfx.Geometry(positions=np.zeros((2, 3), np.float32),
                                            colors=np.zeros((2, 4), np.float32)),
                               _overlay_material(gfx.LineSegmentMaterial, thickness=1.4, color_mode="vertex",
                                                 dash_pattern=(5, 4), aa=True))
        self._acquired = gfx.Points(gfx.Geometry(positions=np.zeros((1, 3), np.float32)),
                                    _overlay_material(gfx.PointsMarkerMaterial, marker="plus", size=13,
                                                      color=ACQUIRED_COLOR, edge_width=0))
        # temporary dimensions (0.61, core/temp_dims.py): their lines, and a text for each value
        self._tdim_lines = gfx.Line(gfx.Geometry(positions=np.zeros((2, 3), np.float32),
                                                 colors=np.zeros((2, 4), np.float32)),
                                    _overlay_material(gfx.LineSegmentMaterial, thickness=1.3, color_mode="vertex",
                                                      aa=True))
        self._tdim_strong = gfx.Line(gfx.Geometry(positions=np.zeros((2, 3), np.float32),     # (0.361) hover / typed
                                                  colors=np.zeros((2, 4), np.float32)),
                                     _overlay_material(gfx.LineSegmentMaterial, thickness=2.0, color_mode="vertex",
                                                       aa=True))
        self._tdim_texts = []
        self._tdim_boxes = []         # (0.372) the dark box under each value…
        self._tdim_marks = gfx.Line(gfx.Geometry(positions=np.zeros((2, 3), np.float32)),   # …a relation's «↔» on it
                                    _overlay_material(gfx.LineSegmentMaterial, thickness=1.3, color="#ffffff",
                                                      aa=True))
        self._tdim_marks.render_order = 3
        self.temp_dims = []           # [(TempDim, where its value is (world), its text)] shown
        # grips of the lines selected (0.62): squares on their ends, diamonds in their middles
        self._grip_ends = gfx.Points(gfx.Geometry(positions=np.zeros((1, 3), np.float32)),
                                     _overlay_material(gfx.PointsMarkerMaterial, marker="square", size=10,
                                                       color=TEMP_DIM_COLOR, edge_color="#ffffff", edge_width=1.5))
        self._grip_mids = gfx.Points(gfx.Geometry(positions=np.zeros((1, 3), np.float32)),
                                     _overlay_material(gfx.PointsMarkerMaterial, marker="diamond", size=10,
                                                       color=TEMP_DIM_COLOR, edge_color="#ffffff", edge_width=1.5))
        # (0.353) a wall chosen alone: a «+» on each of its ends, to go on drawing it from there
        self._grip_adds = gfx.Points(gfx.Geometry(positions=np.zeros((1, 3), np.float32)),
                                     _overlay_material(gfx.PointsMarkerMaterial, marker="plus", size=17,
                                                       color=TEMP_DIM_COLOR, edge_color="#ffffff", edge_width=1.5))
        # (0.386) a «−» (a roof block's water taken away): the plus's bar alone
        self._grip_subs = gfx.Points(gfx.Geometry(positions=np.zeros((1, 3), np.float32)),
                                     _overlay_material(gfx.PointsMarkerMaterial, marker="custom", size=17,
                                                       custom_sdf="return max(abs(coord.x), abs(coord.y) + size / "
                                                                  "3.0) - size / 2.0;",
                                                       color=TEMP_DIM_COLOR, edge_color="#ffffff", edge_width=1.5))
        # (0.359) a door chosen alone: its flip arrows (their middles are grips to click)
        self._grip_arrows = gfx.Line(gfx.Geometry(positions=np.zeros((2, 3), np.float32)),
                                     _overlay_material(gfx.LineSegmentMaterial, thickness=2.2, color=TEMP_DIM_COLOR,
                                                       aa=True))
        self.grips = ([], [], [], [])  # (end points, middle points, «+» points, (0.386) «−» points) shown, world
        self.grip_arrows = []         # (0.359) the arrows' segments' ends shown with them
        # a selection region being drawn (0.75): its outline and a light fill, just in front of the camera
        self._region_fill = gfx.Mesh(gfx.Geometry(positions=np.zeros((3, 3), np.float32),
                                                  indices=np.array([[0, 1, 2]], np.uint32)),
                                     _overlay_material(gfx.MeshBasicMaterial, color=REGION_COLORS["window"][1],
                                                       alpha_mode="blend", side="both"))
        self._region_line = gfx.Line(gfx.Geometry(positions=np.zeros((2, 3), np.float32)),
                                     _overlay_material(gfx.LineMaterial, thickness=1.5,
                                                       color=REGION_COLORS["window"][0], aa=True))
        self.region_shown = None      # (screen points, mode) of the region shown (for tests)
        self._tdim_args = None        # (dims, angles, active, hover, typed, camera) as last shown: drawn again when the
        #                               view moves
        self.tip_text = ""
        self.label_text = ""
        self.alignment_kinds = []     # the kinds of the lines shown dashed (for tests)
        for wobj in (self._fill, self._volume, self._lines, self._marker, self._label, self._tip, self._align,
                     self._acquired, self._tdim_lines, self._tdim_strong, self._tdim_marks, self._grip_ends,
                     self._grip_mids, self._grip_adds, self._grip_subs, self._grip_arrows, self._region_fill,
                     self._region_line):
            wobj.visible = False
            self.scene.add(wobj)

    def show_polygon(self, points, segments=(), colors=()):
        """Translucent polygon (convex or not) plus coloured line segments (pairs of points)."""
        pts = _f32(points)
        if len(pts) > 3 and not is_convex_polygon(pts):
            tris = triangulate_polygon(pts)
        else:
            tris = [(0, i, i + 1) for i in range(1, len(pts) - 1)]
        if tris:
            self._fill.geometry = gfx.Geometry(positions=pts, indices=np.array(tris, np.uint32).reshape(-1, 3))
        self._fill.visible = len(tris) > 0
        self._volume.visible = False                    # (0.383: one preview at a time)
        self.show_lines(segments, colors)

    VOLUME_LIGHT = normalize(np.array((-0.35, -0.55, 0.76)))     # (0.383) where a solid being drawn is lit from

    def show_volume(self, triangles, segments=(), colors=(), color=PREVIEW_FILL):
        """(0.383) A solid being drawn — triangles (n, 3, 3), world — translucent, each face shaded by its way (its top
        light, its sides darker the more they turn from the light), so that it reads as a volume and not as two
        outlines, one over the other; and its edges (segments). An empty one hides it."""
        tris = np.asarray(triangles, dtype=np.float64).reshape(-1, 3, 3)
        if len(tris):
            normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
            lengths = np.linalg.norm(normals, axis=1)
            normals = normals / np.where(lengths > 1e-12, lengths, 1.0)[:, None]
            light = np.abs(normals @ self.VOLUME_LIGHT)[:, None]              # (both sides: either way round)
            base = np.asarray(color[:3], dtype=np.float64)[None, :]
            dark, bright = base * 0.6, base + (1.0 - base) * 0.45               # turned away / facing the light
            rgb = np.clip(dark + (bright - dark) * light, 0.0, 1.0)
            rgba = np.concatenate([rgb, np.full((len(tris), 1), min(color[3] + 0.16, 1.0))], axis=1)
            self._volume.geometry = gfx.Geometry(positions=_f32(tris.reshape(-1, 3)),
                                                 indices=np.arange(len(tris) * 3, dtype=np.uint32).reshape(-1, 3),
                                                 colors=np.repeat(rgba, 3, axis=0).astype(np.float32))
        self._volume.visible = bool(len(tris))
        self._fill.visible = False
        self.show_lines(segments, colors)

    def show_lines(self, segments=(), colors=()):
        if len(segments):
            self._lines.geometry = gfx.Geometry(positions=_f32(segments),
                                                colors=np.array(colors, dtype=np.float32).reshape(-1, 4))
            self._lines.visible = True
        else:
            self._lines.visible = False
        self.redraw()

    def show_marker(self, point, color=PREVIEW):
        if point is None:
            self._marker.visible = False
        else:
            self._marker.geometry = gfx.Geometry(positions=_f32([point]))
            self._marker.material.color = color
            self._marker.visible = True
        self.redraw()

    def show_tip(self, text, point):
        """Small inference tooltip ("Extremidade", "Na face"...) next to a point."""
        self.tip_text = text or ""
        if not text or point is None:
            self._tip.visible = False
        else:
            self._tip.set_text(_drawable(text))
            self._tip.local.position = tuple(float(c) for c in point)
            self._tip.visible = True
        self.redraw()

    def show_label(self, text, point):
        self.label_text = text if (text and point is not None) else ""
        if not text or point is None:
            self._label.visible = False
        else:
            self._label.set_text(_drawable(text))
            self._label.local.position = tuple(float(c) for c in point)
            self._label.visible = True
        self.redraw()

    def show_alignments(self, lines=(), point=None):
        """The inference lines a point found lies on, dashed from where they come from to it (the
        axes through the point drawn from are not: the tool's own line shows them), and a cross on
        each point acquired (self.tracking)."""
        segs, colors, kinds = [], [], []
        for line in lines if point is not None else ():
            if line.kind.startswith("axis_"):
                continue
            colour = (AXIS_COLORS[line.kind[-1]] if line.kind.startswith("align_")
                      else EXTENSION_COLOR if line.kind == "extension" else PARALLEL_COLOR)
            start = line.point if line.kind != "extension" else min(
                line.edge, key=lambda e: float(np.linalg.norm(np.asarray(e) - point)))
            segs += [start, point]
            colors += [colour, colour]
            kinds.append(line.kind)
        self.alignment_kinds = kinds
        if segs:
            self._align.geometry = gfx.Geometry(positions=_f32(segs), colors=np.array(colors, np.float32))
        self._align.visible = bool(segs)
        acquired = self.tracking.points
        if acquired:
            self._acquired.geometry = gfx.Geometry(positions=_f32(acquired))
        self._acquired.visible = bool(acquired)
        self.redraw()

    def show_temp_dims(self, dims=(), angles=(), active=None, hover=None, typed=""):
        """Temporary dimensions (core/temp_dims.TempDim / TempAngle) — (0.372) as the owner's Blender addon draws
        them now: thin light-blue lines with open arrows, an element's own measures a little stronger than its
        relations to the others; each value white on a dark box laid on its line, along it (a relation's «↔ 0,63
        m»); the one under the mouse (`hover`) strong — its line deeper, its box blue —, the one typed over
        (`active`) too, with what is `typed` for its value — offset and arrowed in screen pixels (drawn again when
        the view moves)."""
        self._tdim_args = ((list(dims), list(angles), active, hover, typed, self._camera_key())
                           if (dims or angles) else None)
        look = TEMP_DIM_LOOK[views_canvas.DARK]
        drawn = {False: ([], []), True: ([], [])}          # strong? → (segments' ends, their colours)
        texts, shown = [], []
        for dim in dims:
            s, at = temp_dims.dim_segments(dim, self.world_per_pixel((np.asarray(dim.a) + np.asarray(dim.b)) / 2))
            if not s and dim.kind != "label":            # (0.386: a label is its box alone)
                continue
            strong = dim is active or dim is hover
            name = "strong" if strong else "relation" if dim.kind == "relation" else "measure"
            segs, colors = drawn[strong]
            colour = _physical_in(look[name], False)
            for p, q in s:
                segs += [p, q]
                colors += [colour, colour]
            text = format_length(dim.value, decimal_sep())
            if dim.kind == "relation":
                text = RELATION_MARK + text
            if dim is active and typed:
                text = "[ {} ]".format(typed)
            texts.append((text, at, look["box_strong" if strong else "box"], self._dim_turn(dim),
                          TEMP_DIM_FONT[name]))
            shown.append((dim, at, text))
        for angle in angles:
            s, at = temp_dims.arc_segments(angle, self.world_per_pixel(angle.center))
            segs, colors = drawn[False]
            colour = _physical_in(look["measure"], False)
            for p, q in s:
                segs += [p, q]
                colors += [colour, colour]
            texts.append((format_angle(abs(angle.degrees), decimal_sep()), at, look["box"], self._dim_turn(None),
                          TEMP_DIM_FONT["measure"]))
        for line, (segs, colors) in ((self._tdim_lines, drawn[False]), (self._tdim_strong, drawn[True])):
            if segs:
                line.geometry = gfx.Geometry(positions=_f32(segs), colors=np.array(colors, np.float32))
            line.visible = bool(segs)
        while len(self._tdim_texts) < len(texts):
            # (0.361) drawn in the model, laid along its line and facing the camera, sized in pixels each time the
            # view moves: a text in screen space did not turn here); (0.372) on its box, over the lines
            label = gfx.Text(text=" ", font_size=0.1, screen_space=False, anchor="middle-center",
                             material=_overlay_material(gfx.TextMaterial, color=look["text"]), render_order=2)
            box = gfx.Mesh(gfx.plane_geometry(1.0, 1.0),
                           _overlay_material(gfx.MeshBasicMaterial, color=look["box"], side="both"))
            box.render_order = 1
            for w in (label, box):
                w.visible = False
                self.scene.add(w)
            self._tdim_texts.append(label)
            self._tdim_boxes.append(box)
        marks = []                                          # (0.372) the «↔» of the relations, drawn in strokes
        for k, (label, box) in enumerate(zip(self._tdim_texts, self._tdim_boxes)):
            if k < len(texts):
                text, at, colour, turn, size = texts[k]
                px = self.world_per_pixel(at)
                width, height = label_width_px(text, size) + 2 * TEMP_DIM_PAD, size * TEMP_DIM_BOX_H
                right = np.asarray(la.vec_transform_quat((1.0, 0.0, 0.0), turn), dtype=float)
                up = np.asarray(la.vec_transform_quat((0.0, 1.0, 0.0), turn), dtype=float)
                middle = np.asarray(at, dtype=float) + up * (height / 2.0 * px)    # (its bottom edge on the line)
                words, shift = text, 0.0
                if text.startswith(RELATION_MARK):          # (the letter's arrow is small and blurred at this size)
                    words = text[len(RELATION_MARK):]
                    lead = label_width_px(RELATION_MARK, size)
                    shift = lead / 2.0
                    x0 = -width / 2.0 + TEMP_DIM_PAD + 0.05 * size
                    x1, wing = x0 + 0.85 * size, 0.28 * size
                    y = TEMP_DIM_RAISE * size * 0.5
                    for a, b in (((x0, y), (x1, y)), ((x0, y), (x0 + wing, y + wing)), ((x0, y), (x0 + wing, y - wing)),
                                 ((x1, y), (x1 - wing, y + wing)), ((x1, y), (x1 - wing, y - wing))):
                        marks += [middle + (right * a[0] + up * a[1]) * px, middle + (right * b[0] + up * b[1]) * px]
                label.set_text(words)
                label.font_size = size * px
                label.material.color = look["text"]
                place = middle + (right * shift + up * TEMP_DIM_RAISE * size) * px
                label.local.position = tuple(float(c) for c in place)
                label.local.rotation = turn
                box.material.color = colour
                box.local.position = tuple(float(c) for c in middle)
                box.local.rotation = turn
                box.local.scale = (width * px, height * px, 1.0)
            label.visible = box.visible = k < len(texts)
        if marks:
            self._tdim_marks.geometry = gfx.Geometry(positions=_f32(marks))
        self._tdim_marks.visible = bool(marks)
        self.temp_dims = shown
        self.redraw()

    def _dim_angle(self, dim):
        """(0.361) The angle on the screen (radians, counter-clockwise, within ±90° so that it reads upright) of a
        temporary dimension's line — its value is written along it."""
        (x0, y0), (x1, y1) = self.project(dim.a), self.project(dim.b)
        if not all(math.isfinite(v) for v in (x0, y0, x1, y1)) or math.hypot(x1 - x0, y1 - y0) < 1e-6:
            return 0.0
        turn = math.atan2(-(y1 - y0), x1 - x0)           # (the screen's y goes down)
        if turn > math.pi / 2 + 1e-9:
            turn -= math.pi
        elif turn <= -math.pi / 2 + 1e-9:
            turn += math.pi
        return turn

    def _dim_turn(self, dim):
        """(0.361) The rotation (a quaternion) laying a temporary dimension's value along its line — upright, as
        _dim_angle reads it — in the plane facing the camera (None: level on the screen)."""
        m = np.asarray(self.camera.world.matrix, dtype=float)
        right, up, toward = (m[:3, k] / max(float(np.linalg.norm(m[:3, k])), 1e-12) for k in range(3))
        d = right if dim is None else np.asarray(dim.b, dtype=float) - np.asarray(dim.a, dtype=float)
        d = d - float(d @ toward) * toward
        if float(np.linalg.norm(d)) < 1e-9:
            d = right
        d = d / float(np.linalg.norm(d))
        turn = math.atan2(float(d @ up), float(d @ right))
        if turn > math.pi / 2 + 1e-9 or turn <= -math.pi / 2 + 1e-9:
            d = -d
        return tuple(float(q) for q in la.quat_from_mat(np.column_stack((d, np.cross(toward, d), toward))))

    def _dim_frame(self, dim):
        """(0.361) Along and up the value of a temporary dimension, on the screen (x right, y down)."""
        turn = self._dim_angle(dim)
        return (math.cos(turn), -math.sin(turn)), (-math.sin(turn), -math.cos(turn))

    def clear_temp_dims(self):
        self.show_temp_dims()

    # ------------------------------------------------------------ selection regions (0.75)

    def _screen_to_world(self, xy):
        """Screen points (pixels) as world points just in front of the camera (to draw over everything)."""
        w, h = self.logical_size()
        return [self._unproject(2.0 * x / w - 1.0, 1.0 - 2.0 * y / h, 1e-4) for x, y in xy]

    def show_region(self, points=(), mode="window", closed=True):
        """A selection region on the screen: a box, a lasso or a polygon (closed), or a fence (open) —
        blue for window, green and dashed for crossing, orange for a fence. No points: none."""
        pts = [tuple(map(float, p)) for p in points]
        self.region_shown = (pts, mode) if len(pts) >= 2 else None
        if len(pts) < 2:
            self._region_line.visible = self._region_fill.visible = False
            self.redraw()
            return
        line, fill = REGION_COLORS.get(mode, REGION_COLORS["window"])
        world = self._screen_to_world(pts + ([pts[0]] if closed else []))
        self._region_line.geometry = gfx.Geometry(positions=_f32(world))
        self._region_line.material.color = line
        self._region_line.material.dash_pattern = (6, 4) if mode == "crossing" else ()
        self._region_line.visible = True
        tris = []
        if closed and len(pts) >= 3:
            flat = np.array([(x, y, 0.0) for x, y in pts])
            try:
                tris = ([(0, i, i + 1) for i in range(1, len(pts) - 1)] if is_convex_polygon(flat)
                        else triangulate_polygon(flat))
            except Exception:                         # (a lasso crossing itself: its outline only)
                tris = []
        if tris:
            self._region_fill.geometry = gfx.Geometry(positions=_f32(world[:len(pts)]),
                                                      indices=np.array(tris, np.uint32).reshape(-1, 3))
            self._region_fill.material.color = fill
        self._region_fill.visible = bool(tris)
        self.redraw()

    @staticmethod
    def category(obj):
        """What kind of thing an object is, for the selection filter: its IFC class, or "sketch"."""
        return obj.ifc_class if obj.is_bim else "sketch"

    def selectable(self, obj):
        return obj is not None and self.category(obj) not in self.unselectable

    def _screen_shape(self, obj, planes):
        """(screen points (N, 2), triangles, segments) of what is seen of an object — its points cut away
        by the plan / section / box left out — or None if nothing of it is seen."""
        mesh = obj.mesh
        if obj.is_bim:
            verts = np.asarray(mesh.verts, dtype=float).reshape(-1, 3)
            tris, segs = np.asarray(mesh.tris, dtype=np.int64).reshape(-1, 3), None
        else:
            m = obj.matrix
            verts = np.asarray(mesh.verts, dtype=float).reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
            tris = np.asarray(mesh.triangulate()[0], dtype=np.int64).reshape(-1, 3) if mesh.faces else None
            segs = np.asarray(mesh.lines, dtype=np.int64).reshape(-1, 2) if mesh.lines else None
        if not len(verts):
            return None
        kept = np.ones(len(verts), dtype=bool)
        for normal, offset in planes:
            kept &= verts @ np.asarray(normal, dtype=float) >= offset - 1e-6
        if not kept.any():
            return None
        xy = self.project_many(verts)
        xy[~kept] = np.nan                            # (cut away: not seen, neither inside nor outside)
        if tris is not None and len(tris):
            tris = tris[kept[tris].any(axis=1)]
        if segs is not None and len(segs):
            segs = segs[kept[segs].any(axis=1)]
        return xy, tris, segs

    def region_pick(self, region, mode):
        """What a selection region takes (core/region_select): (object ids, grid axis indices) — of what is
        shown and can be selected. A box drawn rightwards: what is wholly inside; leftwards: what it touches;
        a fence: what it crosses."""
        from ..core import region_select as rs
        region = np.asarray(region, dtype=float).reshape(-1, 2)
        planes = self.kept_planes() or []
        ids = set()
        rlo, rhi = region.min(axis=0), region.max(axis=0)
        for obj in self.shown_objects():
            if not self.selectable(obj) or (obj.is_bim and obj.id in self.bim and not self.bim.is_visible(obj.id)):
                continue
            bounds = obj.mesh.bounds() if obj.is_bim else None
            if bounds is not None:                    # (quick: the box round it must meet the region's)
                lo, hi = np.asarray(bounds[0], float), np.asarray(bounds[1], float)
                corners = np.array([(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
                c = self.project_many(corners)
                if not np.isnan(c).any() and ((c.min(axis=0) > rhi).any() or (c.max(axis=0) < rlo).any()):
                    continue
            shape = self._screen_shape(obj, planes)
            if shape is None:
                continue
            xy, tris, segs = shape
            if mode == rs.WINDOW:                     # the parts cut away do not count
                seen = ~np.isnan(xy).any(axis=1)
                if seen.any() and rs.points_in_polygon(xy[seen], region).all():
                    ids.add(obj.id)
            elif rs.takes(xy, region, mode, tris, segs):
                ids.add(obj.id)
        axes = set()
        if "grid" not in self.unselectable and self.section is None:
            z = self.grid_level()
            for k, axis in enumerate(getattr(self.doc, "grids", [])):
                xy = self.project_many(np.array(((*axis.start, z), (*axis.end, z))))
                if rs.takes(xy, region, mode, segs=[(0, 1)]):
                    axes.add(k)
        return ids, axes

    def show_grips(self, ends=(), middles=(), adds=(), arrows=(), subs=()):
        """The grips of the lines selected: squares on their ends, diamonds in their middles (0.62); (0.353) a «+» on
        each end of a wall chosen alone; (0.359) arrows (segments' ends, in pairs) drawn with them — a door's flips;
        (0.386) «−» (a roof block's water taken away)."""
        self.grips = tuple([np.asarray(p, dtype=float) for p in pts] for pts in (ends, middles, adds, subs))
        for wobj, pts in zip((self._grip_ends, self._grip_mids, self._grip_adds, self._grip_subs), self.grips):
            if pts:
                wobj.geometry = gfx.Geometry(positions=_f32(pts))
            wobj.visible = bool(pts)
        self.grip_arrows = [np.asarray(p, dtype=float) for p in arrows]
        if self.grip_arrows:
            self._grip_arrows.geometry = gfx.Geometry(positions=_f32(self.grip_arrows))
        self._grip_arrows.visible = bool(self.grip_arrows)
        self.redraw()

    def grip_at(self, x, y, radius_px=9):
        """("add" | "sub" | "end" | "middle", index) of the grip under (x, y), or None (a «+» or «−» first, then an
        end, then a middle)."""
        subs = self.grips[3] if len(self.grips) > 3 else []
        for kind, pts in (("add", self.grips[2]), ("sub", subs), ("end", self.grips[0]), ("middle", self.grips[1])):
            if not pts:
                continue
            xy = self.project_many(np.array(pts))
            dist = np.hypot(xy[:, 0] - x, xy[:, 1] - y)
            k = int(np.nanargmin(np.nan_to_num(dist, nan=np.inf)))
            if dist[k] <= radius_px:
                return kind, k
        return None

    def _camera_key(self):
        cam = self.camera
        return (tuple(np.round(cam.local.position, 6)), tuple(np.round(cam.local.rotation, 6)),
                round(float(cam.zoom), 6), round(float(cam.width), 6), round(float(cam.height), 6),
                tuple(self.logical_size()))

    def _follow_view(self):
        """The temporary dimensions keep their offset and ticks in pixels: made again when the view moved."""
        if self._tdim_args is not None and self._tdim_args[-1] != self._camera_key():
            dims, angles, active, hover, typed, _key = self._tdim_args
            self.show_temp_dims(dims, angles, active, hover, typed)

    def temp_dim_at(self, x, y):
        """The temporary dimension whose value is under (x, y) — to type over it — or None. (0.361: the value is
        written along its line.)"""
        best = None
        for dim, at, text in self.temp_dims:
            if dim.key is None:
                continue
            sx, sy = self.project(at)
            (ex, ey), (nx, ny) = self._dim_frame(dim)
            along, up = (x - sx) * ex + (y - sy) * ey, (x - sx) * nx + (y - sy) * ny
            size = TEMP_DIM_FONT["relation" if dim.kind == "relation" else "measure"]
            half = label_width_px(text, size) / 2.0 + TEMP_DIM_PAD          # (0.372: its box, on its line)
            height = size * TEMP_DIM_BOX_H
            low = 2 if dim.kind == "relation" else -4      # (0.361: a relation's line itself is clicked apart)
            if abs(along) <= half and low <= up <= height + 2:
                d = abs(along) + abs(up - height / 2.0)
                if best is None or d < best[0]:
                    best = (d, dim)
        return best[1] if best else None

    def temp_dim_line_at(self, x, y):
        """(0.361) The relation (a temporary dimension to another element) whose line passes within TEMP_DIM_LINE_PX
        of (x, y), where it is seen — not behind an element there (a wall it runs under, in the 3D view: clicking that
        wall chooses it) —, or None. Clicked, it turns from axes to faces and back."""
        best = None
        for dim, at, _text in self.temp_dims:
            if dim.kind != "relation" or dim.key is None:
                continue
            half = (np.asarray(dim.b, dtype=float) - np.asarray(dim.a, dtype=float)) / 2
            p, q = np.array(self.project(at - half), dtype=float), np.array(self.project(at + half), dtype=float)
            if not (np.all(np.isfinite(p)) and np.all(np.isfinite(q))):
                continue
            d = q - p
            k = float(np.clip((np.array((x, y)) - p) @ d / max(float(d @ d), 1e-9), 0.0, 1.0))
            gap = float(np.linalg.norm(p + d * k - (x, y)))
            if gap <= TEMP_DIM_LINE_PX and (best is None or gap < best[0]):
                best = (gap, dim, at - half + 2 * half * k)
        if best is None:
            return None
        hit = self.pick_point(x, y)                       # (only near a line: one pick, not one each move)
        if hit is not None:
            origin, ray = self.ray(x, y)
            if float((np.asarray(hit[2]) - origin) @ ray) < float((best[2] - origin) @ ray) - TEMP_DIM_HIDDEN:
                return None
        return best[1]

    def clear_overlays(self):
        for wobj in (self._fill, self._volume, self._lines, self._marker, self._label, self._tip, self._align,
                     self._acquired):
            wobj.visible = False
        self.tip_text = ""
        self.label_text = ""
        self.alignment_kinds = []
        if self._tdim_args is not None or self.temp_dims:
            self.show_temp_dims()
        self.redraw()

    def snapshot(self):
        """Last rendered frame as an (H, W, 4) uint8 array (for tests and reports)."""
        return np.asarray(self.renderer.snapshot())

    # ------------------------------------------------------------ an image of the view (0.329)

    def image_size(self, width):
        """(width, height) in pixels of an image `width` wide (at most IMAGE_WIDTH_MOST) of the view: its proportion."""
        lw, lh = self.logical_size()
        width = int(min(max(int(width), 16), IMAGE_WIDTH_MOST))
        return width, max(1, round(lh * width / max(lw, 1)))

    def render_image(self, width, background="view"):
        """(0.329) The view as it is shown, as an image `width` pixels wide and of the view's proportion (Revit's
        Export ▸ Image): drawn again off screen, with the window's line weights and text sizes — a larger image is a
        sharper one, not one with thinner lines and smaller texts —, without what only the tools show (the selection,
        the previews and tips, the section box, the guides, the ground grid and axes, the view cube) and with what is
        still drawn a little at a time finished first. background: "view" (its light sky), "white" or "transparent".
        Returns (height, width, 4) uint8 RGBA."""
        from rendercanvas.offscreen import RenderCanvas
        width, height = self.image_size(width)
        lw, lh = self.logical_size()
        self.finish_pending()
        canvas = RenderCanvas(size=(lw, lh), pixel_ratio=width / max(lw, 1))
        canvas.set_physical_size(width, height)
        smooth = 2 if width * height <= IMAGE_SMOOTH_MOST else 1
        renderer = gfx.renderers.WgpuRenderer(canvas, pixel_scale=smooth, enable_events=False)
        with self._presented(background):
            self.bim.flush()
            canvas.request_draw(lambda: renderer.render(self.scene, self.camera))
            image = np.ascontiguousarray(np.asarray(canvas.draw(), dtype=np.uint8))
        canvas.close()
        return image

    def finish_pending(self):
        """(0.329) What is otherwise drawn a little at a time done now: the cut's hatches after an edit, the seams of
        many elements, the batches of a file just opened (an image of the view has all of it)."""
        if self._hatch_later:
            self._hatches_again()
        while self._seam_queue:
            obj_id = self._seam_queue.pop()
            if self._reseam(obj_id):
                self._seam_again.add(obj_id)
        for obj_id in self._seam_again:
            obj = self.doc.get(obj_id)
            if obj is not None and obj_id in self.bim.where:
                self.show_object(obj_id, obj.mesh)
        self._seam_again = set()
        self.bim.flush()

    def _tool_marks(self):
        """(0.329) What only the tools show over the model: the ground grid and axes, the guides, the section box, the
        previews, tips, alignments, temporary dimensions, grips and selection regions."""
        marks = [self.grid, self.work_grid, self._axes, self._guides, self._box_view, self._fill, self._volume,
                 self._lines,
                 self._marker,
                 self._label, self._tip, self._align, self._acquired, self._tdim_lines, self._tdim_strong,
                 self._grip_ends,
                 self._grip_mids, self._grip_adds, self._grip_subs, self._grip_arrows, self._region_fill,
                 self._region_line, self._tdim_marks, *self._tdim_texts, *self._tdim_boxes]
        return [w for w in marks if w is not None]

    @contextlib.contextmanager
    def _presented(self, background):
        """(0.329) The view for its image: the tools' marks hidden, nothing selected (no one told: the Properties, the
        grips stay), the background asked for — all as it was afterwards."""
        hidden = [w for w in self._tool_marks() if w.visible]
        for wobj in hidden:
            wobj.visible = False
        heard = (self.selection_listeners, self.rooms_listeners, self.axes_listeners, self.annotation_listeners)
        self.selection_listeners, self.rooms_listeners, self.axes_listeners, self.annotation_listeners = [], [], [], []
        picked = (set(self.selection), dict(self.face_selection), set(self.selected_rooms), set(self.selected_axes),
                  set(self.selected_dims), set(self.selected_annotations), dict(self.line_selection))
        paper = background in ("white", "transparent") and views_canvas.DARK     # (0.341: on paper, the light canvas)
        try:
            self._pick_again(set(), {}, set(), set(), set(), set(), {})
            if paper:
                self.set_canvas(False)
            if background == "white":
                self.background.material.set_colors("#ffffff")
            elif background == "transparent":
                self.background.visible = False
            yield
        finally:
            if paper:
                self.set_canvas(True)
            self.background.material.set_colors(*views_canvas.background())
            self.background.visible = True
            self._pick_again(*picked)
            (self.selection_listeners, self.rooms_listeners, self.axes_listeners,
             self.annotation_listeners) = heard
            for wobj in hidden:
                wobj.visible = True
            self.redraw()

    def _pick_again(self, ids, faces, rooms, axes, dims, anns, lines=None):
        """(0.329) The selection (elements, faces of sketches, rooms, grid axes, dimensions, drawings; 0.373 lines
        picked alone) put as given, only what differs drawn again."""
        if faces != self.face_selection:
            self.select_faces(faces)
        if lines is not None and lines != self.line_selection:
            self.select_lines(lines)
        if ids != self.selection:
            self.set_selection(ids, keep_faces=True)
        if rooms != self.selected_rooms:
            self.select_rooms(rooms)
        if axes != self.selected_axes:
            self.select_axes(axes)
        if dims != self.selected_dims:
            self.select_dimensions(dims)
        if anns != self.selected_annotations:
            self.select_annotations(anns)
