"""(0.315) An element seen by its materials, as a view style asks — the same for the 3D view (render/viewport.py) and
for the drawings on paper (model/drawings.py): each triangle's material (a layered wall's: the layer it lies in, its
top and ends cut along its layers — (0.352) an end lying in a joined wall's face that face's material, its plaster
going round the corner —; an element in its parts' own colours: by those colours), its colour, how clear
it is, and its materials' surface patterns laid on its faces. Pure data (NumPy), no GPU nor Qt."""

import contextlib
import threading
from dataclasses import dataclass

import numpy as np

from ..core.mesh import slice_triangles
from ..ifc import catalog

# each category's colour (the 3D view's usual colours, until 0.314 in render/viewport.py)
CATEGORY_COLOURS = {"IfcWall": "#f6f3ec", "IfcSlab": "#c9c7c1", "IfcRamp": "#c9c7c1", "IfcRoof": "#b9775f",
                    "IfcWasteTerminal": "#6f7d8a", "IfcStair": "#cfccc5", "IfcRailing": "#8a959e",
                    "IfcCurtainWall": "#9cc3d9", "IfcCovering": "#f2f1ec", "IfcLightFixture": "#ffe9a8",
                    "IfcColumn": "#b8c4cc",
                    "IfcBeam": "#a9b6bf",
                    "IfcFooting": "#a19e97", "IfcPile": "#8f8a80", "IfcPipeSegment": "#5b8fc9",
                    "IfcDuctSegment": "#b8bfc6",
                    "IfcPipeFitting": "#5b8fc9", "IfcDuctFitting": "#b8bfc6", "IfcAirTerminal": "#e3e8ed",
                    "IfcUnitaryEquipment": "#cfd6dc", "IfcOutlet": "#f4f4ef", "IfcSwitchingDevice": "#f4f4ef",
                    "IfcElectricDistributionBoard": "#c9ced4", "IfcJunctionBox": "#e8e6df",
                    "IfcCableCarrierSegment": "#9b7fc9", "IfcCableCarrierFitting": "#9b7fc9",
                    "IfcDoor": "#a8794f", "IfcWindow": "#9cc3d9", "IfcFurniture": "#c9a27a",
                    "IfcSanitaryTerminal": "#f4f6f8", "IfcBuildingElementProxy": "#d8cbb8",
                    "IfcGeographicElement": "#b7c394"}
CATEGORY_DEFAULT = "#dcd8cf"
LIGHT = np.array((0.45, -0.75, 1.0)) / np.linalg.norm((0.45, -0.75, 1.0))   # (the 3D view's fixed sun)
FLUSH = 1e-3                    # m: (0.352) a wall's end this close to a joined wall's face lies in it
_PASS = threading.local()       # (0.352) while one_pass: {GlobalId: its layer spans}


@contextlib.contextmanager
def one_pass():
    """(0.352) Many elements looked at in a row with the model unchanged meanwhile (a file written, a drawing, the
    view dressed for a style): each wall's layers read once, however many of its neighbours turn a corner to it."""
    outer = getattr(_PASS, "spans", None)
    _PASS.spans = {} if outer is None else outer
    try:
        yield
    finally:
        _PASS.spans = outer


def _spans(ifc, guid):
    """An element's layer spans (IfcModel._layer_spans) — once a pass."""
    kept = getattr(_PASS, "spans", None)
    if kept is not None and guid in kept:
        return kept[guid]
    spans = ifc._layer_spans(ifc.by_guid(guid))
    if kept is not None:
        kept[guid] = spans
    return spans


def _bands(ifc, guid):
    """IfcModel.layer_bands (an element of 2+ layers: [(name, normal, d0, d1)], else None), read once a pass."""
    if not hasattr(ifc, "_layer_spans"):
        return ifc.layer_bands(guid)
    spans = _spans(ifc, guid)
    if not spans or len(spans) < 2:
        return None
    return [(m.Name if m is not None else None, n, d0, d1) for m, n, d0, d1 in spans]


_PATTERNED = [None, frozenset(), ()]           # (materials' generation, their names, their colours)


def _patterned():
    """(0.317) The names and the colours of the materials with surface patterns (lines: not a solid fill), kept until
    the materials change."""
    from ..core import patterns as core_patterns
    if _PATTERNED[0] != catalog.GENERATION:
        specs = [s for s in catalog.MATERIALS.values()
                 if any(v and v[0] != core_patterns.SOLID for v in (s.surface_fg, s.surface_bg))]
        _PATTERNED[:] = [catalog.GENERATION, frozenset(n for s in specs for n in (s.name_pt, s.name_en)),
                         tuple(np.round(np.asarray(s.color, dtype=float), 3) for s in specs)]
    return _PATTERNED[1], _PATTERNED[2]


def may_have_patterns(ifc, obj):
    """(0.317) Quickly: could an element show surface patterns (one of its materials has them)?"""
    names, _colours = _patterned()
    if not names or getattr(obj.mesh, "colors", None) is not None:
        return False                    # (an element made of its pieces — tiles, a door, a railing — shows them)
    try:
        return bool(set(ifc.material_names(obj.id)) & names) if ifc is not None else False
    except (AttributeError, RuntimeError):
        return False


def category_rgb(ifc_class):
    return _rgb(CATEGORY_COLOURS.get(ifc_class, CATEGORY_DEFAULT))


SHADOW = 0.56                     # (0.316) a face out of the sun, on paper: its colour so much
SUN_FACING = 0.02                 # (a face turned less than this to the sun is out of it)


def shade(rgb, normals, light=None, shaded=True):
    """Colours lit as on paper: a face turned to the sun at full colour, one turned away a little darker. light
    (0.316): a view style's sun with its shadows — a face turned away from it in shadow (SHADOW), the others lit
    (shaded: the more the more they face it; else at their colour, consistent)."""
    normals = np.asarray(normals, dtype=float)
    rgb = np.asarray(rgb, dtype=float)
    if light is None:
        lit = 0.66 + 0.34 * np.clip(normals @ LIGHT, 0.0, 1.0) if shaded else np.ones(len(normals))
    else:
        facing = normals @ np.asarray(light, dtype=float)
        lit = np.where(facing > SUN_FACING, 0.80 + 0.20 * np.clip(facing, 0.0, 1.0) if shaded else 1.0, SHADOW)
    return np.clip(rgb * np.asarray(lit, dtype=float).reshape(-1, 1), 0.0, 1.0)


@dataclass
class Look:
    corners: np.ndarray       # (T, 3, 3) its triangles (a layered one's cut along its layers), world
    normals: np.ndarray       # (T, 3)
    faces: np.ndarray         # (T,) each one's face of the mesh (for picking)
    rgb: np.ndarray           # (T, 3) sRGB 0–1: its materials' (or its own / the given) colours
    alpha: np.ndarray         # (T,) 1 opaque … 0 clear
    patterns: list            # [(segments (K, 2, 3), "#rrggbb")] its surface patterns on its faces
    split: bool = False       # cut along its layers (other triangles than its mesh's)
    see_through: bool = False
    categories: np.ndarray = None   # (0.343) (T,) each one's material's category ("concrete", "glass"…; "": none)…
    finishes: np.ndarray = None     # …and its finish in the render ("": its category's)…
    materials: np.ndarray = None    # …and (0.348) its material's key ("": none)
    painted: bool = False           # (0.391) some of its faces painted (their colours shown whatever the style)


def _by_name():
    out = {}
    for spec in catalog.MATERIALS.values():
        out.setdefault(spec.name_pt, spec)
        out.setdefault(spec.name_en, spec)
    return out


def look(ifc, obj, base_rgb, colours=True, patterns=True, clear=True, lift=0.0, surface=None):
    """An element's Look: colours True — its materials' colours (else base_rgb, or its parts' own); patterns — its
    materials' surface patterns (lift: m off the faces); clear — its materials' transparency. ifc: the IfcModel (None
    or one still being read: by its own colours only). surface (0.318): a view style's surface hatches for its
    category — (foreground, background), each (pattern, colour) or None — instead of its materials'."""
    from ..core import patterns as core_patterns
    mesh = obj.mesh
    tris, owner = mesh.triangulate()
    verts = np.asarray(mesh.verts, dtype=float).reshape(-1, 3)
    normals = np.asarray(mesh.normals, dtype=float)[owner] if hasattr(mesh, "normals") else \
        np.array([mesh.face_normal(fi) for fi in owner]).reshape(-1, 3)
    corners = verts[tris] if len(tris) else np.zeros((0, 3, 3))
    faces = np.asarray(owner, dtype=np.int64)
    own = getattr(mesh, "colors", None)
    own = np.asarray(own, dtype=float)[owner] if own is not None and len(own) == len(owner) else None
    bands = None
    if own is None and colours and ifc is not None:
        try:
            bands = _bands(ifc, obj.id)
        except (AttributeError, RuntimeError):
            bands = None
    split = False
    if bands:
        n = np.asarray(bands[0][1], dtype=float)
        inner = sorted({d for _m, _n, d0, d1 in bands for d in (d0, d1)})[1:-1]
        cut, parent = slice_triangles(corners, n, inner)
        split = len(parent) != len(corners)
        corners, normals, faces = cut, normals[parent], faces[parent]
        specs = _wrapped_ends(ifc, obj, corners, normals, n, _band_materials(bands, corners, normals))
    else:
        specs = _own_materials(own) if own is not None else _ifc_materials(ifc, obj, corners, normals)
    paint_keys = _painted(ifc, obj, corners, normals)       # (0.391) faces painted: their paint's material instead
    if paint_keys is not None:
        on = paint_keys != ""
        specs = [(spec, which & ~on) for spec, which in specs if np.any(which & ~on)]
        specs += [(catalog.MATERIALS[key], paint_keys == key) for key in sorted(set(paint_keys[on]))
                  if key in catalog.MATERIALS]
    count = len(corners)
    rgb = own.copy() if own is not None and not split else np.tile(np.asarray(base_rgb, dtype=float), (count, 1))
    alpha = np.ones(count)
    categories = np.full(count, "", dtype=object)
    finishes = np.full(count, "", dtype=object)
    keys = np.full(count, "", dtype=object)
    laid = []
    see_through = False
    faced = np.abs(normals @ np.asarray(bands[0][1], dtype=float)) > 0.5 if bands else np.ones(count, dtype=bool)
    frame = _aligned(ifc, obj) if patterns else None          # (0.332: its faces' patterns aligned by hand)
    for spec, which in specs:
        categories[which] = spec.category
        finishes[which] = getattr(spec, "finish", "") or ""
        keys[which] = getattr(spec, "key", "") or ""
        if colours:
            rgb[which] = spec.color
            for value in (spec.surface_bg, spec.surface_fg):        # (a solid one covers the shading colour)
                if value and value[0] == core_patterns.SOLID:
                    rgb[which] = _rgb(value[1])
        if clear and spec.transparency > 0.0:
            alpha[which] = 1.0 - float(spec.transparency)
            see_through = True
        if patterns and own is None and surface is None and np.any(which & faced):   # (pieces one by one: none)
            for value in (spec.surface_bg, spec.surface_fg):
                if value and value[0] != core_patterns.SOLID:
                    lines = core_patterns.on_triangles(value[0], corners[which & faced], normals[which & faced],
                                                       lift=lift, frame=frame)
                    if len(lines):
                        laid.append((lines, value[1]))
    if surface is not None and count:                  # (0.318) the view style's for its category, on all its faces
        everywhere = faced if own is None else np.ones(count, dtype=bool)
        for value in (surface[1], surface[0]):
            if not value:
                continue
            if value[0] == core_patterns.SOLID:
                if colours:
                    rgb[everywhere] = _rgb(value[1])
            elif patterns and np.any(everywhere):
                lines = core_patterns.on_triangles(value[0], corners[everywhere], normals[everywhere], lift=lift,
                                                   frame=frame)
                if len(lines):
                    laid.append((lines, value[1]))
    if paint_keys is not None:                         # (0.391) the paint shows whatever the colours asked
        for key in set(paint_keys) - {""}:
            spec = catalog.MATERIALS.get(key)
            if spec is not None:
                where = paint_keys == key
                rgb[where] = spec.color
                # (0.469) …and it is the faces' material: its textures, its look in the render
                keys[where], categories[where] = key, spec.category
                finishes[where] = getattr(spec, "finish", "") or ""
    return Look(corners, normals, faces, rgb, alpha, laid, split, see_through, categories, finishes, keys,
                painted=paint_keys is not None and bool(np.any(paint_keys != "")))


def _painted(ifc, obj, corners, normals):
    """(0.391) Each triangle's paint (model/paint.py): its material key or "" — None when the element has none."""
    if ifc is None or not getattr(obj, "is_bim", False) or not hasattr(ifc, "_placement_si") or not len(corners):
        return None
    from . import paint
    try:
        planes = paint.world_planes(ifc, obj.id)
    except (AttributeError, RuntimeError, TypeError, ValueError):
        return None
    return paint.painted(planes, corners, normals) if planes else None


def _aligned(ifc, obj):
    """(0.332) An element's faces' patterns as aligned by hand (ifc/pattern_align.py), or None."""
    if ifc is None or not getattr(obj, "is_bim", False) or not hasattr(ifc, "placement"):
        return None
    from ..ifc import pattern_align
    try:
        return pattern_align.frames(ifc, obj.id)
    except (AttributeError, RuntimeError, TypeError, ValueError):
        return None


def _rgb(text):
    text = str(text or "#000000")
    try:
        return tuple(int(text[k:k + 2], 16) / 255.0 for k in (1, 3, 5))
    except ValueError:
        return 0.0, 0.0, 0.0


def _band_materials(bands, corners, normals):
    """[(MaterialSpec, which triangles)] of a layered element: each triangle the layer it lies in, a hair inside its
    face (its outer face: the outer layer)."""
    by_name = _by_name()
    n = np.asarray(bands[0][1], dtype=float)
    depth = (corners.mean(axis=1) - normals * 1e-4) @ n
    lows = np.array([b[2] for b in bands])
    highs = np.array([b[3] for b in bands])
    which = np.argmin(np.maximum(lows[None, :] - depth[:, None], depth[:, None] - highs[None, :]), axis=1)
    return [(by_name[name], which == k) for k, (name, *_r) in enumerate(bands)
            if name in by_name and np.any(which == k)]


def _wrapped_ends(ifc, obj, corners, normals, n, specs):
    """(0.352) A layered wall's ends lying in the face of a wall joined to it — at an outside corner, the end of the
    one running through shows in the other's face — in that face's material (its plaster going round the corner, as
    built and as Revit cleans a join), not cut along its own layers."""
    ends = (np.abs(normals @ n) < 0.5) & (np.abs(normals[:, 2]) < 0.5)
    if not ends.any() or not hasattr(ifc, "joined_walls"):
        return specs
    try:
        joined = ifc.joined_walls([obj.id])
    except (AttributeError, RuntimeError, TypeError):
        return specs
    by_name = _by_name()
    centres = corners.mean(axis=1)
    taken = np.zeros(len(corners), dtype=bool)
    wrapped = []
    for guid in joined:
        spans = _spans(ifc, guid)
        if not spans:
            continue
        m = np.asarray(spans[0][1], dtype=float)
        along = ends & ~taken & (np.abs(normals @ m) > 0.99)
        if not along.any():
            continue
        depth = centres @ m
        low, high = min(spans, key=lambda s: s[2]), max(spans, key=lambda s: s[3])
        for edge, material in ((low[2], low[0]), (high[3], high[0])):
            spec = by_name.get(material.Name) if material is not None else None
            hit = along & (np.abs(depth - edge) < FLUSH)
            if spec is not None and hit.any():
                wrapped.append((spec, hit))
                taken |= hit
                along &= ~hit
    if not taken.any():
        return specs
    return [(spec, which & ~taken) for spec, which in specs if np.any(which & ~taken)] + wrapped


def _own_materials(rgb):
    """[(MaterialSpec, which triangles)] of an element in its parts' own colours (a window's frame and glass): each
    colour's material."""
    rgb = np.round(np.asarray(rgb, dtype=float), 3)
    out = []
    for spec in catalog.MATERIALS.values():
        which = np.all(np.abs(rgb - np.round(np.asarray(spec.color, dtype=float), 3)) < 2e-3, axis=1)
        if which.any():
            out.append((spec, which))
            rgb[which] = -1.0                                   # (each triangle one material)
    return out


def _ifc_materials(ifc, obj, corners, normals):
    if ifc is None or not len(corners):
        return []
    try:
        names, index = ifc.face_materials(obj.id, corners.mean(axis=1), normals)
    except (AttributeError, RuntimeError):                     # (a file still being read: shown from the cache)
        return []
    by_name = _by_name()
    return [(by_name[name], index == k) for k, name in enumerate(names) if name in by_name]
