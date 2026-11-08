"""Drawings of the model's views (Phase 3, step 4): a plan of a storey or a section,
as 2D linework in metres — what the plane cuts (closed outlines, filled when printed)
and the edges seen beyond it — ready to be printed to a vector PDF (ui/pdf.py).
Made from the shapes on screen, so a drawing is always the model as it is.
"""

from dataclasses import dataclass, field

import numpy as np

from ..core import drawing2d
from ..core import terrain as terrain_geo
from ..i18n import decimal_sep, t
from . import annotations as notes2d
from . import cut_joins
from . import dimensions as dims_model
from . import graphic_rules as rules_model
from . import graphic_styles as styles_model
from . import material_looks
from . import seen_joins
from . import symbols as marks_model

MATERIAL_CUT = "mat:"  # (0.314) a fill's hatch for a material cut with its own patterns (as ifc.model.MATERIAL_CUT)
EMPTY_CUT = "colour:#ffffff"   # (0.315) what is cut, empty: white, its outline only (a view style's)
CATEGORY_CUT = "cat:"          # (0.318) a fill's hatch from the view style's hatches by category: "cat:" + its class
ELEMENT_CUT = "el:"            # (0.331) …from the view's hatches by element: "el:" + the hatch (one key for the same one:
#                                two elements given it are joined as one material is)
PATTERN_LIFT = 0.001   # m: a surface pattern's lines off their face (what is in front of them hides them, not it)
CUT_HEIGHT = 1.20      # m above the storey level (as the live plan, render.viewport.CUT_HEIGHT)
TERRAIN_CLASS = "IfcGeographicElement"      # (0.155) a terrain: drawn with its contour lines, not its triangles
# (0.254) what is cut over what, as Revit joins them: a column's cut takes the place of the walls' it stands in
CUTS_THROUGH = {"IfcColumn": ("IfcWall", "IfcWallStandardCase")}
GRID_MARGIN = 1.0      # m beyond an axis's ends kept in a drawing's extent (its bubbles)


@dataclass
class Drawing:
    title: str
    cut: list = field(default_factory=list)                     # closed outlines: (N, 2) arrays, metres
    lines: np.ndarray = field(default_factory=lambda: np.zeros((0, 2, 2)))   # seen edges: (K, 2, 2)
    hatch: list = field(default_factory=list)      # per outline: its material's hatch (ifc HATCH_WORDS) or None
    symbols: np.ndarray = field(default_factory=lambda: np.zeros((0, 2, 2)))  # plan symbols (door swings…)
    fills: list = field(default_factory=list)      # what is cut, by material: (outline, hatch) — a layered
    #                                                wall gives one per layer (plaster | block | plaster)
    # dimensions: (point measured at each end, the line's two ends, text), metres (0.123: a line square to its
    # direction, the points maybe at different depths)
    dims: list = field(default_factory=list)
    underlay: np.ndarray = field(default_factory=lambda: np.zeros((0, 2, 2)))   # another storey, in grey (0.65)
    grids: list = field(default_factory=list)      # the structural grid's axes: (end a, end b, tag), metres (0.67)
    # drawn in the view (0.120): (kind, [(points (N, 2), closed)], hatch, text, where (2,), size mm, line type,
    # pen width mm or None — 0.126), metres
    annotations: list = field(default_factory=list)
    # angular dimensions (0.122): (corner (2,), radius, start, sweep (radians, counter-clockwise), text, a, b)
    angles: list = field(default_factory=list)
    marks: list = field(default_factory=list)      # a plan's section and elevation marks (symbols.Mark, 0.121)
    levels: list = field(default_factory=list)     # a section's / elevation's level marks: (z, storey name)
    level_ends: tuple = None                       # (0.464) where their lines end, dragged in its view: (x0, x1)
    north: bool = False                            # a plan: its north arrow
    dim_style: dict = None                         # the project's dimension style (0.124; None: the usual one)
    graphic_style: dict = None                     # its hatches and pens on paper (0.126; None: the usual ones)
    rooms: list = field(default_factory=list)      # a plan's rooms' labels (0.125): (where (2,), name, number, area)
    callouts: list = field(default_factory=list)   # its detail views' callouts (0.133): ((x0, y0, x1, y1), tag)
    frame: tuple = None                            # a detail view's rectangle: its extent, whatever is drawn in it
    above: list = field(default_factory=list)      # a plan's pipes and ducts above its cut (0.135): outlines, dashed
    # a plan's pipes that fall (0.136): (their middle (2,), the way down (2,), the slope as written, radius) — an
    # arrow and "1 %" beside each (they never make the drawing bigger)
    slopes: list = field(default_factory=list)
    zones: list = field(default_factory=list)      # the free zones in front of a plan's fixtures (0.140): (N, 2) rings
    points: list = field(default_factory=list)     # a plan's electrical points (0.143): (kind, back (3,), angle)
    contours: list = field(default_factory=list)   # a plan's terrain contour lines (0.155): (segments (K, 2, 2), major,
    #                                                height)
    platforms: list = field(default_factory=list)  # its platforms (0.157): (outline (N, 2), its height as written)
    # (0.201) its terrains coloured by slope, when its view says so: (band — terrain.SLOPE_BANDS —, [(outline (N, 2),
    # [holes (M, 2)])])
    slope_fills: list = field(default_factory=list)
    # (0.203) its platforms' slopes: where they meet the ground (crest, toe) and their batter ticks, (K, 2, 2)
    batters: np.ndarray = field(default_factory=lambda: np.zeros((0, 2, 2)))
    # (0.207) its storey's background images, under all: (corners (4, 2) — lower-left, lower-right, upper-right,
    # upper-left —, the picture's path, opacity, the corners of the part kept (0.209)); they never make the drawing
    # bigger
    images: list = field(default_factory=list)
    # (0.238) its labels a hand may move: (index in annotations, key — what it tells, not where it stands)
    movable: list = field(default_factory=list)
    # (0.314) the cuts drawn with their material's own patterns: {MATERIAL_CUT + name: (background, foreground)}, each
    # (core.patterns key, "#rrggbb") or None — the other fills' hatches are the project's graphic style's
    cut_patterns: dict = field(default_factory=dict)
    # (0.315) its view style's: the faces seen, painted — (outline (N, 2), sRGB colour, alpha, depth), the farthest
    # first — and the surface patterns seen on them, ((K, 2, 2), "#rrggbb")
    faces: list = field(default_factory=list)
    surface_lines: list = field(default_factory=list)
    # (0.320) the outline round all that is cut, joined (cut_joins.outline: outer rings counter-clockwise, holes
    # clockwise) — its thick line; None: the union of `cut` (a drawing made otherwise)
    outline: list = None

    def bounds(self, with_levels=True):
        """(lowest, highest) corner of everything drawn, or None (a detail view's: its rectangle). (0.464) with_levels
        False: the levels' ends dragged by hand left out (the drawing's own span)."""
        if self.frame is not None:
            x0, y0, x1, y1 = self.frame
            return np.array((x0, y0), dtype=float), np.array((x1, y1), dtype=float)
        parts = [p for p in self.cut] + [a.reshape(-1, 2) for a in (self.lines, self.symbols) if len(a)]
        parts += [pts for a in self.annotations for pts, _closed in a[1]]
        parts += [np.asarray(r, dtype=float) for r in self.above]             # (0.135)
        parts += [a[4].reshape(1, 2) for a in self.annotations if a[0] == "text"]
        if parts and self.levels:                   # (a level counts for its height; its line's length never…)
            x = float(np.vstack(parts)[0, 0])
            parts += [np.array(((x, z), (x, z))) for z, _name in self.levels]
            if self.level_ends and with_levels:     # (…but where a hand put its ends, 0.464: its marks on the sheet)
                z = float(self.levels[0][0])
                parts.append(np.array(((self.level_ends[0], z), (self.level_ends[1], z))))
        if parts:                                   # (dimensions alone do not make a drawing; marks never count)
            for p1, p2, l1, l2, _text, *_own in self.dims:
                parts.append(np.array((p1 + (l1 - p1) * 1.15, p2 + (l2 - p2) * 1.15)))
            for v2, r, start, sweep, _text, _a, _b in self.angles:
                turns = [start + sweep * k / 2 for k in range(3)]
                parts.append(np.array([v2 + r * np.array((np.cos(a), np.sin(a))) for a in turns]))
            for a2, b2, _tag in self.grids:          # (nor axes alone; their bubbles count)
                d = (b2 - a2) / max(np.linalg.norm(b2 - a2), 1e-12)
                parts.append(np.array((a2 - d * GRID_MARGIN, b2 + d * GRID_MARGIN)))
        if not parts:
            return None
        pts = np.vstack(parts)
        return pts.min(axis=0), pts.max(axis=0)


TABLE_TEXT = 2.0           # mm on paper: a schedule's text on a sheet (0.132)
TABLE_ROW = 5.0            # mm: a row
TABLE_CHAR = 1.15          # mm: about how wide a letter of it is (a column fits its longest text)


@dataclass
class TableDrawing:
    """A schedule on a sheet (0.132): its headings, its rows (texts), its totals — sized in mm on paper, whatever
    the scale (sheets.extent gives its size so)."""
    title: str
    header: list
    rows: list
    totals: str = ""

    def widths(self):
        """Each column's width in mm: its longest text, and a little room."""
        cols = len(self.header)
        return [max([len(str(self.header[c]))] + [len(str(r[c])) for r in self.rows if c < len(r)]) * TABLE_CHAR + 3.0
                for c in range(cols)]

    def paper_size(self):
        """(w, h) mm: its columns, its heading row and its rows (and its totals' row)."""
        return (max(sum(self.widths()), 40.0),
                TABLE_ROW * (len(self.rows) + 1 + (1 if self.totals else 0)))

    def bounds(self):
        w, h = self.paper_size()
        return np.zeros(2), np.array((w, h)) / 1000.0     # (as if at 1:1: sheets.extent knows better)


def schedule_drawing(doc, ref, title):
    """The table of a schedule (a category key, or "def:<uid>" for the project's own) for a sheet, or None."""
    from ..i18n import t
    from . import schedules as schedules_model
    found = schedules_model.table_of(doc, ref, lambda c: t("sched.col." + c), decimal_sep())
    if found is None:
        return None
    own_title, header, rows, totals = found
    return TableDrawing(own_title or title, header, rows, totals)


def _unjoined(doc, guids):
    """(0.333) {frozenset((a, b))} of the elements among `guids` unjoined by hand (ifc/unjoin.py); none while the IFC is
    still being read."""
    from ..ifc import unjoin
    try:
        return unjoin.pairs(getattr(doc, "ifc", None), guids)
    except (AttributeError, RuntimeError):
        return set()


def _ask_ifc(doc, method, guids, **options):
    """{GlobalId: …} from the IFC, or {} while it is still being read (shown from the cache)."""
    try:
        return getattr(doc.ifc, method)(guids, **options)
    except RuntimeError:
        return {}


def _shown(doc, obj, settings):
    """Is this element in a view with these settings (its template: classes and phases hidden)?"""
    if obj.ifc_class in settings.hidden:
        return False
    return not settings.hidden_phases or (doc.status_of(obj.id) or "") not in settings.hidden_phases


@material_looks.one_pass()                      # (0.352: each wall's layers read once)
def _draw(doc, objects, normal, offset, origin, u, v, title, hidden=True, rule=None, detail="fine", look=None,
          elements=None, covers=()):
    """hidden: leave out the edges that something in front hides (the drawing is seen along `normal`).
    covers (0.444): outlines of what covers the walls' jambs but is not among `objects` (a plan's doors drawn by their
    symbols: their linings' pieces) — no finish turned round them.
    rule: the view's graphic rule — what is cut is then filled with its colours (graphic_rules.cut_colours).
    detail (0.65): what is cut filled solid ("coarse"), with its material's hatch ("medium"), or by
    layers ("fine"). look (0.315): the view's style (view_styles.ViewStyle) — the faces seen painted (shaded or in
    consistent colours, by category or by material), the materials' surface patterns on them, what is cut (each
    material's patterns, the category's, solid, empty); None: lines, as always. elements (0.331): the view's hatches
    by element (view_templates.Settings.elements), over all those."""
    cut, edges, triangles, owners, cut3d = [], [], [], [], []
    n = np.asarray(normal, dtype=float)
    painted = look is not None and look.faces in ("shaded", "consistent")
    faces, surface = [], []
    sunlit, casters = ([], []) if painted and look.shadows else (None, None)     # (0.316: its shadows on paper)
    if look is not None and look.cut == "solid":
        detail = "coarse"
    # (0.320) the seams between elements of one material in one plane (two walls of a type in a row): not drawn
    joined = seen_joins.all_seams(objects, getattr(doc, "ifc", None))
    for obj in objects:
        mesh = obj.mesh                                             # IFC elements: world coordinates
        box = mesh.bounds()
        if box is None:
            continue
        corners = np.array([(x, y, z) for x in (box[0][0], box[1][0]) for y in (box[0][1], box[1][1])
                            for z in (box[0][2], box[1][2])])
        depths = corners @ n
        if depths.max() < offset:
            continue                                                # wholly on the side taken away
        rings = []
        if depths.min() < offset and not _drawn_by_pieces(doc, obj, n):     # the plane goes through its box
            rings = drawing2d.loops(drawing2d.cut_segments(mesh.verts, mesh.tris, n, offset))
            # (0.253: its outer outlines one way round, its holes the other — the outline on paper is their union)
            cut += drawing2d.oriented([drawing2d.flatten(ring, origin, u, v) for ring in rings])
            owners += [obj.id] * len(rings)
            cut3d += rings
        if obj.ifc_class == TERRAIN_CLASS and hasattr(mesh, "normals"):
            pairs = terrain_geo.drawn_edges(mesh, n)            # (not its triangles; a hill's outline, 0.155)
            ends = np.stack((mesh.verts[pairs[:, 0]], mesh.verts[pairs[:, 1]]), axis=1) if len(pairs) else ()
        else:
            ends = seen_joins.edges(mesh, joined.get(obj.id))      # (0.320: its seams with its neighbours left out)
            contour = mesh.contour_edges(n) if hasattr(mesh, "contour_edges") else ()     # (a pipe's sides, 0.136)
            if len(contour):
                more = np.stack((mesh.verts[contour[:, 0]], mesh.verts[contour[:, 1]]), axis=1)
                ends = np.concatenate((ends, more)) if len(ends) else more
        if len(ends):
            kept = drawing2d.kept_edges(ends[:, 0], ends[:, 1], n, offset)
            if len(kept):
                edges.append(kept)
        if hidden:
            # what can hide: of a solid not cut, only the faces turned to the viewer (the others are
            # behind them); of a cut one, all — through the cut one sees its inside, which hides
            tris = mesh.tris if rings else mesh.tris[mesh.normals @ n < -1e-9]
            triangles.append(mesh.verts[tris])
        if painted and obj.ifc_class != TERRAIN_CLASS and hasattr(mesh, "normals"):      # (0.315)
            _paint_faces(doc, obj, look, n, offset, origin, u, v, faces, surface, sunlit, elements)
            if casters is not None:
                casters.append(_beyond(mesh.verts[mesh.tris], n, offset))
        elif obj.ifc_class != TERRAIN_CLASS and hasattr(mesh, "normals") and (
                _element_surface(elements, obj) is not None       # (0.331: its own in this view, whatever the style)
                or ((look is None or look.patterns) and (surface_override(look, obj) is not None
                                                         or material_looks.may_have_patterns(getattr(doc, "ifc", None),
                                                                                             obj)))):
            # (0.317) a drawing in lines: the surface patterns of its faces seen too (the tiles on a floor)
            seen = material_looks.look(getattr(doc, "ifc", None), obj, (0.0, 0.0, 0.0), colours=False, patterns=True,
                                       clear=False, lift=PATTERN_LIFT, surface=surface_override(look, obj, elements))
            _surface_of(seen, n, offset, surface)
    edges = np.concatenate(edges) if edges else np.zeros((0, 2, 3))
    occluders = np.concatenate(triangles) if triangles else np.zeros((0, 3, 3))
    if hidden and len(edges):
        lines = drawing2d.hidden_lines_removed(occluders, edges, n, offset, origin, u, v)
    else:
        lines = drawing2d.flatten(edges, origin, u, v) if len(edges) else np.zeros((0, 2, 2))
    seen_patterns = []
    for segs, colour in surface:                     # (0.315: the surface patterns seen, what is in front hides)
        kept = drawing2d.hidden_lines_removed(occluders, segs, n, offset, origin, u, v) if hidden \
            else drawing2d.flatten(segs, origin, u, v)
        if len(kept):
            seen_patterns.append((kept, colour))
    # (0.359) a plan's doors by their pieces, each its own outline and hatch — not merged into one mass; (0.444) their
    # linings cover the jambs (no finish turned round them)
    pieces, _piece_owners = door_pieces(doc, objects, n, origin, u, v, detail)
    fills, hatches, cut_patterns, whose = _fills(doc, cut, cut3d, owners, origin, u, v, rule, detail, look, elements,
                                                 [ring for ring, _h in pieces] + list(covers))
    # (0.320) each material's parts as one (a thin line only where the material changes), and one thick line round
    # all that is cut (model/cut_joins.py)
    regions = cut_joins.merged(fills, whose)
    joined = [(ring, key) for key, region in regions.items() for ring in drawing2d.rings_of(region)]
    cut_patterns = _with_own_patterns(doc, cut_patterns, pieces)
    drawing = Drawing(title, cut + [ring for ring, _h in pieces], lines,
                      [hatches.get(i) for i in owners] + [h for _r, h in pieces], fills=joined + pieces)
    drawing.outline = (cut_joins.outline(regions.values()) if regions else []) + [ring for ring, _h in pieces]
    found = getattr(fills, "breaks", None)                        # (0.333: between those unjoined by hand)
    drawing.breaks = found if found is not None and len(found) else np.zeros((0, 2, 2))
    drawing._occluders = occluders if hidden else None            # (what hides: for the terrains' contours, 0.155)
    drawing.cut_patterns = cut_patterns                           # (0.314: their materials' own)
    drawing.surface_lines = seen_patterns                         # (0.317: in any drawing, painted or not)
    if painted:                                      # (0.315) the faces seen, the farthest first; their patterns
        if sunlit:                                   # (0.316) and the shadows the sun casts on them
            faces += cast_shadows(sunlit, np.concatenate(casters) if casters else np.zeros((0, 3, 3)), look.sun(),
                                  origin, u, v)
        faces.sort(key=lambda f: -f[3])
        drawing.faces = faces
    return drawing


def _fills(doc, cut, cut3d, owners, origin, u, v, rule=None, detail="fine", look=None, elements=None, covers=None):
    """What is cut, filled by material — (fills [(outline (N, 2), hatch)], {element: its main hatch}, {hatch: the
    material's own (background, foreground)}): each layer its own (detail "fine"), a column through a wall taken out
    of it, a graphic rule's colours, the view style's cut (0.315), (0.331) the view's own hatch for an element — over
    its category's and its materials', one hatch for all of it. (0.444) In a plan, the walls' finishes turned round
    their free ends and their openings' jambs (cut_joins._wrap_ends) — covers: the doors drawn by their pieces
    (door_pieces' outlines), which cover the jambs they line."""
    cut_ids = sorted(set(owners))                                   # (of what is cut only)
    category = {} if look is None or look.cut == "material" else {"own": False}   # (0.315: the category's hatches)
    hatches = _ask_ifc(doc, "hatches", cut_ids, **category) if owners else {}
    # (0.320: of one layer too — a concrete wall's thickness —, for the joins)
    across = _layers_inside(doc, _ask_ifc(doc, "layers", cut_ids, single=True, **category) if owners else {})
    # (0.460) a curved wall's layers, rings about its centre — in a plan (a section cuts it as one)
    flat = abs(float(np.cross(np.asarray(u, dtype=float), np.asarray(v, dtype=float))[2])) > 0.99
    curved = _ask_ifc(doc, "curved_layers", cut_ids, **category) \
        if owners and flat and detail == "fine" and hasattr(getattr(doc, "ifc", None), "curved_layers") else {}
    across = {owner: parts for owner, parts in across.items() if owner not in curved}   # (not flat layers)
    layered = {owner: parts for owner, parts in across.items() if len(parts) >= 2}
    coloured = {}
    if rule and owners:
        try:
            values = doc.ifc.property_values(cut_ids, rule)
        except RuntimeError:
            values = {}
        coloured = rules_model.cut_colours(values, tuple(rule))
    overrides = {}                                  # (0.318) the view style's hatches by category: its cut
    for owner in cut_ids if look is not None and getattr(look, "categories", ()) else ():
        cls = getattr(doc.get(owner), "ifc_class", None)
        found = look.category(cls)
        if found is not None and (found[0] or found[1]):
            overrides[owner] = (CATEGORY_CUT + cls, (found[1], found[0]))
    for owner in cut_ids if elements else ():       # (0.331) …and the view's by element, over them
        mine = elements.get(owner)
        if mine is not None and (mine[0] or mine[1]):
            overrides[owner] = (ELEMENT_CUT + repr((mine[1], mine[0])), (mine[1], mine[0]))
    fills, mine, rounds = [], {}, {}
    for ring, ring2d, owner in zip(cut3d, cut, owners):
        if owner in coloured:
            mine.setdefault(owner, []).append((ring2d, "colour:" + coloured[owner]))
        elif owner in overrides:
            mine.setdefault(owner, []).append((ring2d, overrides[owner][0]))
        elif look is not None and look.cut == "empty":
            mine.setdefault(owner, []).append((ring2d, EMPTY_CUT))   # (0.315: only its outline)
        elif detail == "coarse":
            mine.setdefault(owner, []).append((ring2d, None))       # (solid: the poché)
        elif owner in layered and detail == "fine":
            for hatch, ln, d0, d1 in layered[owner]:
                part = drawing2d.clip_between(ring, ln, d0, d1)
                if part is not None:                                # (its layers' parts turned as its cut, 0.253)
                    mine.setdefault(owner, []).append((drawing2d.flatten(part, origin, u, v), hatch))
        elif owner in curved:                                       # (0.460: all its outlines first — a circle's
            rounds.setdefault(owner, []).append((ring, ring2d))     # hole)
        else:
            mine.setdefault(owner, []).append((ring2d, hatches.get(owner)))
    for owner, pairs in rounds.items():
        z = float(np.mean([np.asarray(r, dtype=float)[:, 2].mean() for r, _r2 in pairs]))
        made = _ring_layers(drawing2d.region([r2 for _r, r2 in pairs]), z, curved[owner], origin, u, v)
        mine.setdefault(owner, []).extend(made or [(r2, hatches.get(owner)) for _r, r2 in pairs])
    over = _cutting(doc, cut, owners)
    whose = []                                                      # (0.317: each fill's element, for the screen)
    for owner, parts in mine.items():
        parts = list(zip(drawing2d.oriented([p for p, _h in parts]), [h for _p, h in parts]))
        cls = getattr(doc.get(owner), "ifc_class", None)
        cutter = over.get(cls)
        made = _less(parts, cutter) if cutter is not None and not cutter.is_empty else parts
        fills += made
        whose += [owner] * len(made)
    # (0.320) joined by material as Revit cleans up joins: overlaps to the stronger layer, the walls' corners mitred
    # and their tees' cores in through the plaster (model/cut_joins.py)
    classes = {owner: getattr(doc.get(owner), "ifc_class", None) for owner in cut_ids}
    strengths = _ask_ifc(doc, "layer_strengths", cut_ids) if across else {}     # (0.334: each layer's, by its type)
    plan = abs(float(np.cross(np.asarray(u, dtype=float), np.asarray(v, dtype=float))[2])) > 0.99
    fills, whose = cut_joins.join(fills, whose, classes, cut_joins.bands(across, origin, u, v, strengths),
                                  _unjoined(doc, cut_ids),                  # (0.333: not those unjoined by hand)
                                  covers=covers, wrap=plan and detail == "fine")
    own_cuts = sorted({h for _r, h in fills if isinstance(h, str) and h.startswith(MATERIAL_CUT)})
    patterns = dict(_ask_ifc(doc, "cut_patterns", own_cuts)) if own_cuts else {}
    patterns.update(dict(overrides.values()))
    return fills, hatches, patterns, whose


def door_pieces(doc, objects, normal, origin, u, v, detail="fine"):
    """(0.359) In a plan, the doors with a plan symbol drawn by their pieces — their lining's jambs, casings, soleira,
    a leaf drawn closed (IfcModel.door_plan_pieces) —, each outlined and hatched apart, not by their body's cut (which
    would join them into one mass): ([(outline (N, 2), hatch)], each one's door) — empty in any other drawing. (Coarse
    detail: solid, as the rest of what is cut.)"""
    n = np.asarray(normal, dtype=float)
    ifc = getattr(doc, "ifc", None)
    if abs(float(n[2])) < 0.99 or ifc is None or not hasattr(ifc, "door_plan_pieces"):
        return [], []
    fills, whose = [], []
    for obj in objects:
        if getattr(obj, "ifc_class", None) != "IfcDoor" or not doc.has_plan_symbol(obj.id):
            continue
        try:
            pieces = ifc.door_plan_pieces(obj.id)
        except (RuntimeError, AttributeError, ValueError, TypeError, KeyError):
            continue
        for _role, ring, hatch in pieces:
            flat = drawing2d.oriented([drawing2d.flatten(np.array([(x, y, 0.0) for x, y in ring]), origin, u, v)])[0]
            fills.append((flat, None if detail == "coarse" else hatch))
            whose.append(obj.id)
    return fills, whose


def _drawn_by_pieces(doc, obj, normal):
    """(0.359) Is it a door a plan draws by its pieces (door_pieces), its body's cut left out?"""
    return abs(float(np.asarray(normal, dtype=float)[2])) >= 0.99 and getattr(obj, "ifc_class", None) == "IfcDoor" \
        and hasattr(getattr(doc, "ifc", None), "door_plan_pieces") and doc.has_plan_symbol(obj.id)


def cut_fills(doc, objects, normal, offset, origin, u, v, rule=None, detail="fine", look=None, elements=None):
    """(0.317) What a plane cuts of some elements, filled as a drawing fills it (_fills) — for the plans and sections on
    screen: (fills [(outline (N, 2), hatch)], {hatch: the material's own (background, foreground)}, each fill's
    element). (0.359) A plan's doors by their pieces (door_pieces)."""
    n = np.asarray(normal, dtype=float)
    if look is not None and look.cut == "solid":
        detail = "coarse"
    cut, owners, cut3d = [], [], []
    for obj in objects:
        if _drawn_by_pieces(doc, obj, n):
            continue
        mesh = obj.mesh
        box = mesh.bounds()
        if box is None:
            continue
        corners = np.array([(x, y, z) for x in (box[0][0], box[1][0]) for y in (box[0][1], box[1][1])
                            for z in (box[0][2], box[1][2])])
        depths = corners @ n
        if depths.max() < offset or depths.min() >= offset:
            continue
        rings = drawing2d.loops(drawing2d.cut_segments(mesh.verts, mesh.tris, n, offset))
        cut += drawing2d.oriented([drawing2d.flatten(ring, origin, u, v) for ring in rings])
        owners += [obj.id] * len(rings)
        cut3d += rings
    pieces, piece_owners = door_pieces(doc, objects, n, origin, u, v, detail)
    fills, _hatches, patterns, whose = _fills(doc, cut, cut3d, owners, origin, u, v, rule, detail, look, elements,
                                              [ring for ring, _h in pieces])
    if pieces:
        fills, whose = list(fills) + pieces, list(whose) + piece_owners
        patterns = _with_own_patterns(doc, patterns, pieces)
    return fills, patterns, whose


def _with_own_patterns(doc, patterns, fills):
    """(0.359) The cut patterns of the materials with their own (MATERIAL_CUT) among some fills, added."""
    own = sorted({h for _r, h in fills if isinstance(h, str) and h.startswith(MATERIAL_CUT)} - set(patterns))
    if not own:
        return patterns
    patterns = dict(patterns)
    patterns.update(dict(_ask_ifc(doc, "cut_patterns", own)))
    return patterns


def _paint_faces(doc, obj, look, n, offset, origin, u, v, faces, surface, sunlit=None, elements=None):
    """(0.315) An element's faces turned to the viewer, beyond the plane (one it cuts: the part beyond), as painted on
    paper — (outline (N, 2), sRGB colour, alpha, depth) into `faces` — and its materials' surface patterns' lines in
    3D, (segments, colour), into `surface`. sunlit (0.316): a list for the faces the style's sun shines on — (their
    outline in 3D, normal, colour in shadow, alpha, depth) —, where the shadows will be cast (cast_shadows)."""
    from ..core.mesh import _clip_side
    mine = _element_surface(elements, obj) is not None              # (0.331: its own in this view: always drawn)
    seen = material_looks.look(getattr(doc, "ifc", None), obj, material_looks.category_rgb(obj.ifc_class),
                               colours=look.colours == "material", patterns=look.patterns or mine,
                               clear=look.transparency, lift=PATTERN_LIFT, surface=surface_override(look, obj, elements))
    if not len(seen.corners):
        return
    front = seen.normals @ n < -1e-9
    depth = seen.corners @ n                                      # (T, 3)
    beyond = front & (depth.max(axis=1) > offset + 1e-9)
    light = look.sun() if sunlit is not None else None
    rgb = material_looks.shade(seen.rgb, seen.normals, light, shaded=look.faces == "shaded")
    dark = np.clip(seen.rgb * material_looks.SHADOW, 0.0, 1.0)
    for k in np.flatnonzero(beyond):
        tri = seen.corners[k]
        poly = tri if depth[k].min() >= offset else np.array(_clip_side(list(tri), n, offset, 1.0))
        if len(poly) < 3:
            continue
        at = float(np.mean(np.asarray(poly) @ n))
        faces.append((drawing2d.flatten(np.asarray(poly), origin, u, v), tuple(float(c) for c in rgb[k]),
                      float(seen.alpha[k]), at))
        if light is not None and float(seen.normals[k] @ light) > material_looks.SUN_FACING:
            sunlit.append((np.asarray(poly, dtype=float), seen.normals[k], tuple(float(c) for c in dark[k]),
                           float(seen.alpha[k]), at))
    _surface_of(seen, n, offset, surface)


def surface_override(look, obj, elements=None):
    """(0.318) A view style's surface hatches for an element's category — (foreground, background) — or None; (0.331)
    the view's own for that element first (elements: view_templates.Settings.elements)."""
    mine = _element_surface(elements, obj)
    if mine is not None:
        return mine
    found = look.category(obj.ifc_class) if look is not None and getattr(look, "categories", ()) else None
    return (found[2], found[3]) if found is not None and (found[2] or found[3]) else None


def _element_surface(elements, obj):
    """(0.331) The view's own surface hatches for an element — (foreground, background) — or None."""
    mine = elements.get(obj.id) if elements else None
    return (mine[2], mine[3]) if mine is not None and (mine[2] or mine[3]) else None


def _surface_of(seen, n, offset, surface):
    """An element's surface patterns' lines (material_looks.Look) beyond a drawing's plane, into `surface`."""
    for segs, colour in seen.patterns:
        mid = segs.mean(axis=1) @ n
        segs = segs[mid > offset]
        if len(segs):
            surface.append((segs, colour))


def _beyond(tris, n, offset):
    """(0.316) The triangles (T, 3, 3) as far as a drawing's plane leaves them: those wholly before it gone, those it
    cuts cut (what is drawn is what casts shadows)."""
    from ..core.mesh import _clip_side
    tris = np.asarray(tris, dtype=float).reshape(-1, 3, 3)
    depth = tris @ n
    whole = depth.min(axis=1) >= offset
    out = [tris[whole]]
    for k in np.flatnonzero(~whole & (depth.max(axis=1) > offset + 1e-9)):
        poly = _clip_side(list(tris[k]), n, offset, 1.0)
        if len(poly) >= 3:
            out.append(np.array([(poly[0], poly[i], poly[i + 1]) for i in range(1, len(poly) - 1)]))
    return np.concatenate(out) if out else np.zeros((0, 3, 3))


SHADOW_BIAS = 1e-4     # m: what touches a face does not shadow it (a window's frame on its wall: only what stands out)


def cast_shadows(sunlit, casters, sun, origin, u, v):
    """(0.316) The shadows the sun (`sun`: towards it) casts on the faces it shines on — sunlit: [(outline in 3D (N, 3),
    normal, colour in shadow, alpha, depth)] — by the triangles `casters` (T, 3, 3): each face's part in shadow, as
    more faces to paint just over it (its rings on paper, its shadow's colour, its alpha, a hair nearer). Face by
    plane: what stands on the sun's side of the plane is cast onto it along the sun's rays and joined (shapely)."""
    import shapely
    sun = np.asarray(sun, dtype=float)
    sun = sun / np.linalg.norm(sun)
    planes = {}
    for item in sunlit:
        poly, normal = item[0], np.asarray(item[1], dtype=float)
        key = (tuple(np.round(normal, 3)), round(float(normal @ poly[0]), 3))
        planes.setdefault(key, []).append(item)
    out = []
    for (normal, level), items in planes.items():
        nn = np.asarray(normal, dtype=float)
        nn = nn / np.linalg.norm(nn)
        towards = float(nn @ sun)
        if towards <= 1e-6 or not len(casters):
            continue
        above = casters @ nn - level                              # (T, 3) how far each corner stands out of it
        mine = casters[above.max(axis=1) > SHADOW_BIAS]
        if not len(mine):
            continue
        e1 = np.cross(nn, (0.0, 0.0, 1.0) if abs(nn[2]) < 0.9 else (1.0, 0.0, 0.0))
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(nn, e1)
        # what stands out cut at the plane (a part behind it casts nothing), then along the rays onto it
        parts = _beyond(mine, nn, level)
        lift = (parts @ nn - level) / towards                     # (T, 3)
        flat = parts - lift[..., None] * sun
        flat2 = np.stack((flat @ e1, flat @ e2), axis=-1)         # (T, 3, 2)
        rings = [np.stack((np.asarray(p, dtype=float) @ e1, np.asarray(p, dtype=float) @ e2), axis=1)
                 for p, *_r in items]
        lo = np.min([r.min(axis=0) for r in rings], axis=0)
        hi = np.max([r.max(axis=0) for r in rings], axis=0)
        keep = (flat2[..., 0].max(axis=1) >= lo[0]) & (flat2[..., 0].min(axis=1) <= hi[0]) & \
               (flat2[..., 1].max(axis=1) >= lo[1]) & (flat2[..., 1].min(axis=1) <= hi[1])
        flat2 = flat2[keep]
        if not len(flat2):
            continue
        a, b = flat2[:, 1] - flat2[:, 0], flat2[:, 2] - flat2[:, 0]
        area = np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0])
        flat2 = flat2[area > 1e-10]
        if not len(flat2):
            continue
        shade = shapely.union_all(shapely.polygons(np.concatenate((flat2, flat2[:, :1]), axis=1)))
        if shade.is_empty:
            continue
        for ring2, (_poly, _n, colour, alpha, depth) in zip(rings, items):
            face = shapely.Polygon(ring2)
            if not face.is_valid or face.area < 1e-12:
                continue
            part = face.intersection(shade)
            for piece in getattr(part, "geoms", [part]):
                if piece.geom_type != "Polygon" or piece.is_empty or piece.area < 1e-10:
                    continue
                back = [np.asarray(r.coords, dtype=float)[:-1] for r in (piece.exterior, *piece.interiors)]
                back = [drawing2d.flatten(r[:, :1] * e1 + r[:, 1:] * e2 + level * nn, origin, u, v) for r in back]
                out.append((back, colour, alpha, depth - 1e-7))
    return out


def _cutting(doc, cut, owners):
    """(0.254) {class cut through: the region of what cuts through it (CUTS_THROUGH)} from the outlines cut."""
    by = {}
    for ring, owner in zip(cut, owners):
        for victim in CUTS_THROUGH.get(getattr(doc.get(owner), "ifc_class", None), ()):
            by.setdefault(victim, []).append(ring)
    return {victim: drawing2d.region(rings) for victim, rings in by.items()}


def _less(parts, cutter):
    """(0.254) An element's fills [(outline, hatch)] less the region `cutter` (what cuts through it): each hatch's
    region less it, as outlines again (drawing2d.rings_of) — those clear of it as they were."""
    x0, y0, x1, y1 = cutter.bounds
    by_hatch = {}
    for ring, hatch in parts:
        by_hatch.setdefault(hatch, []).append(ring)
    out = []
    for hatch, rings in by_hatch.items():
        lo, hi = np.min([r.min(axis=0) for r in rings], axis=0), np.max([r.max(axis=0) for r in rings], axis=0)
        mine = None if hi[0] < x0 or lo[0] > x1 or hi[1] < y0 or lo[1] > y1 else drawing2d.region(rings)
        if mine is None or not mine.intersects(cutter):
            out += [(r, hatch) for r in rings]
        else:
            out += [(r, hatch) for r in drawing2d.rings_of(mine.difference(cutter))]
    return out


RING_STEP_DEG = 2.0     # (0.460) a curved wall's layers' rings drawn in pieces of this many degrees


def _ring_layers(shape, z, layers, origin, u, v):
    """(0.460) A curved wall's cut (shape: on paper, a shapely region; z: its height) parted into its layers — rings
    about its centre: [(outline (N, 2), hatch)]. The outermost and innermost reach past the wall's faces, so that its
    own outline (its cut) bounds them — no hair between two drawings of one arc."""
    from shapely.geometry import Point
    (cx, cy), rings = layers
    c2 = drawing2d.flatten(np.array([(cx, cy, z)]), origin, u, v)[0]
    if not shape.is_valid:
        shape = shape.buffer(0)
    if shape.is_empty:
        return []
    lo, hi = min(r0 for _h, r0, _r1 in rings), max(r1 for _h, _r0, r1 in rings)
    segments = max(8, int(round(90.0 / RING_STEP_DEG)))
    out = []
    for hatch, r0, r1 in rings:
        r0 = max(r0 - 0.05, 0.0) if r0 <= lo + 1e-9 else r0
        r1 = r1 + 0.05 if r1 >= hi - 1e-9 else r1
        band = Point(c2).buffer(r1, quad_segs=segments)
        if r0 > 1e-9:
            band = band.difference(Point(c2).buffer(r0, quad_segs=segments))
        part = shape.intersection(band)
        for piece in getattr(part, "geoms", [part]):
            if piece.geom_type != "Polygon" or piece.is_empty or piece.area < 1e-8:
                continue
            halves = [piece]
            if piece.interiors:                 # (a whole circle's ring: in two halves — outlines with no hole)
                from shapely.geometry import box
                far = 2.0 * (hi + 1.0)
                halves = [piece.intersection(box(c2[0] - far, c2[1], c2[0] + far, c2[1] + far)),
                          piece.intersection(box(c2[0] - far, c2[1] - far, c2[0] + far, c2[1]))]
            for half in halves:
                for outline in drawing2d.rings_of(half):
                    out.append((np.asarray(outline, dtype=float), hatch))
    return out


def _layers_inside(doc, layers):
    """The layers (IfcModel.layers) that fill their element's shape across (to 2 mm): others are
    not trusted (an odd offset) and the element is drawn with its main hatch."""
    out = {}
    for guid, parts in layers.items():
        obj = doc.get(guid)
        if obj is None or not parts:
            continue
        depth = obj.mesh.verts @ parts[0][1]
        lo, hi = min(p[2] for p in parts), max(p[3] for p in parts)
        if abs(lo - depth.min()) < 0.002 and abs(hi - depth.max()) < 0.002:
            out[guid] = parts
    return out


def _add_dimensions(doc, drawing, view, origin, u, v):
    """The view's dimensions, in the project's dimension style (0.124) — and what is drawn in it (0.120)."""
    style = dims_model.clean_style(getattr(doc, "dim_style", None))
    drawing.dim_style = style
    drawing.callouts = [(tuple(d.rect), marks_model.short_tag(d.name)) for d in getattr(doc, "details", ())
                        if view is not None and tuple(d.parent) == tuple(view)]                # (0.133)
    drawing.graphic_style = styles_model.clean(getattr(doc, "graphic_style", None))     # (0.126)
    for dim in doc.dimensions_of(view):
        if dim.vertex is not None:                  # (an angular one, 0.122)
            a, b = dims_model.ends(doc, dim)
            a2, b2, v2, at2 = notes2d.to2([a, b, dims_model.vertex_point(doc, dim), dims_model.line_point(doc, dim)],
                                          origin, u, v)
            arc = dims_model.angle_arc(a2, b2, v2, at2)
            if arc is not None:
                drawing.angles.append((v2, arc[0], arc[1], arc[2], dims_model.angle_text(arc[3], decimal_sep()),
                                       a2, b2))
            continue
        # (0.193) its type's: its text, its marks — (0.398) all of it, its string and its words (core/dim_layout)
        piece = dims_model.piece_of(doc, dim, origin, u, v, style, decimal_sep())
        if piece is not None:
            drawing.dims.append(piece)
    for ann in getattr(doc, "annotations_of", lambda _v: [])(view):
        at = notes2d.to2(ann.points[:1], origin, u, v)[0]
        text = ann.text
        hatch = ann.hatch
        if ann.kind in notes2d.MARKS:                   # (0.156) its height now, beside its cross (0.192: or mark)
            from . import spots
            text = spots.text(spots.spot_height(doc, ann), decimal_sep())
            at = notes2d.mark_text_at(ann, origin, u, v)
        if ann.kind == "level":                         # (0.192) a level mark's filled quarters, in its hatch's place
            hatch = notes2d.level_fills(ann, origin, u, v)
        if ann.kind == "keynote" and len(ann.points) >= 2:     # (0.194) its element's code, at its leader's tip
            from . import keynotes
            text = keynotes.tag_text(doc, ann)
            at = notes2d.to2(ann.points[1:2], origin, u, v)[0]
        drawing.annotations.append((ann.kind, notes2d.shape(ann, origin, u, v), hatch, text, at, ann.size,
                                    ann.extra.get("line", "continuous"), ann.extra.get("width"),
                                    notes2d.angle(ann) if ann.kind == "text" else 0.0))     # (0.191) its angle
    return drawing


def plan(doc, storey, title, cut_height=None, underlay=True):
    """The plan of `storey` (GlobalId), cut `cut_height` (default: its view's) above its level: its
    elements only — and those of the storeys down to its view depth (0.65) — but those of the
    classes its view hides. Doors with a plan symbol in the IFC (linings, the leaf open, the swing
    arc) are drawn by it, not by their cut. With the dimensions drawn in that plan; its underlay
    storey in grey; only its crop region; what is cut as its detail level says."""
    settings = doc.view_settings(("plan", storey))
    cut_height = settings.cut_height if cut_height is None else cut_height
    levels = [(g, z) for g, _n, z in doc.storeys()]
    level = next((z for g, z in levels if g == storey), 0.0)
    deep = {g for g, z in levels if level - settings.depth - 1e-9 <= z < level - 1e-9} if settings.depth > 0 else set()
    bottom = level - settings.depth - 1e-6                  # (a terrain wholly under the view's range: not in it)
    objects = [o for o in doc.objects.values() if o.is_bim and (o.storey in (storey, None) or o.storey in deep)
               and _shown(doc, o, settings)
               and not (o.ifc_class == TERRAIN_CLASS and o.mesh.bounds() is not None
                        and float(o.mesh.bounds()[1][2]) < bottom)]
    symbols = doc.plan_symbols([o.id for o in objects if o.ifc_class == "IfcDoor" and o.storey == storey])
    origin, u, v = np.array((0.0, 0.0, level)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
    # (0.444) the doors drawn by their symbols: their linings still cover the jambs (no plaster turned round them)
    lined = door_pieces(doc, [o for o in objects if o.id in symbols], np.array((0.0, 0.0, -1.0)), origin, u, v)[0] \
        if symbols else []
    drawing = _draw(doc, [o for o in objects if o.id not in symbols], np.array((0.0, 0.0, -1.0)),
                    -(level + cut_height), origin, u, v, title, rule=settings.rule, detail=settings.detail,
                    look=drawn_look(doc, settings), elements=settings.elements, covers=[r for r, _h in lined])
    if symbols:
        drawing.symbols = drawing2d.flatten(np.concatenate(list(symbols.values())), origin, u, v)
    drawing = _add_dimensions(doc, drawing, ("plan", storey), origin, u, v)
    drawing.grids = [(np.array(a.start, dtype=float), np.array(a.end, dtype=float), a.tag)
                     for a in getattr(doc, "grids", ())]
    # (0.121) the sections' lines and the elevations' marks, the north arrow
    letters = dict(zip(("N", "E", "S", "W"), t("cube.letters").split()))
    drawing.marks = marks_model.section_marks(doc) + marks_model.elevation_marks(doc, letters,
                                                                                 marks_model.plan_box(doc, storey))
    drawing.north = True
    drawing.rooms = room_labels(doc, storey)                         # (0.125)
    drawing.above = services_above(doc, storey, level + cut_height, settings)       # (0.135)
    drawing.slopes = slope_labels(doc, storey, settings)                            # (0.136)
    drawing.zones = free_zones(doc, storey, settings)                               # (0.140)
    drawing.points = electrical_points(doc, storey, settings)                       # (0.143)
    drawing.contours = terrain_contours(doc, [o for o in objects if o.ifc_class == TERRAIN_CLASS],
                                        level + cut_height, getattr(drawing, "_occluders", None),
                                        -(level + cut_height), origin, u, v)        # (0.155)
    drawing.platforms = platform_outlines(doc, [o for o in objects if o.ifc_class == TERRAIN_CLASS])    # (0.157)
    drawing.batters = platform_batters(doc, [o for o in objects if o.ifc_class == TERRAIN_CLASS])      # (0.203)
    drawing.images = background_images(doc, storey)                                                   # (0.207)
    if settings.slopes:                                                             # (0.201)
        drawing.slope_fills = terrain_slope_fills([o for o in objects if o.ifc_class == TERRAIN_CLASS],
                                                  level + cut_height)
    if settings.crop is not None:
        drawing = crop(drawing, settings.crop)
    if underlay and settings.underlay in ("below", "above"):
        other = underlay_storey(doc, storey, settings.underlay)
        if other is not None:
            drawing.underlay = underlay_lines(doc, other, drawing.bounds() if drawing.bounds() is not None else None)
    return drawing


SERVICES = ("IfcDuctSegment", "IfcDuctFitting", "IfcPipeSegment", "IfcPipeFitting", "IfcAirTerminal",
            "IfcCableCarrierSegment", "IfcCableCarrierFitting", "IfcUnitaryEquipment")      # (a unit: 0.139)


def services_above(doc, storey, cut, settings=None):
    """(0.135) The pipes and ducts of a storey wholly above its plan's cut, as drawn in a plan: their outline seen
    from above (dashed), so that what runs under the ceiling is there too — [(N, 2) rings]."""
    from shapely.geometry import MultiPoint
    out = []
    for o in doc.objects.values():
        if not o.is_bim or o.ifc_class not in SERVICES or o.storey != storey:
            continue
        if settings is not None and not _shown(doc, o, settings):
            continue
        box = o.mesh.bounds()
        if box is None or float(box[0][2]) <= cut + 1e-6:
            continue
        hull = MultiPoint([(float(p[0]), float(p[1])) for p in o.mesh.verts]).convex_hull
        if hull.geom_type == "Polygon":
            out.append(np.array(hull.exterior.coords)[:-1])
    return out


def slope_labels(doc, storey, settings=None):
    """(0.136) The pipes of a storey that fall along them (drainage), as a plan writes them: [(their middle (2,),
    the way down (2,), the slope ("1 %"), their radius)]."""
    from ..core.units import format_slope
    ids = [o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcPipeSegment" and o.storey == storey
           and (settings is None or _shown(doc, o, settings))]
    found = _ask_ifc(doc, "slopes", ids) if ids else {}
    return [(np.asarray(mid, dtype=float)[:2], np.asarray(down, dtype=float), format_slope(s, decimal_sep()), r)
            for _g, (mid, down, s, r) in sorted(found.items())]


def free_zones(doc, storey, settings=None):
    """(0.140) The free zones in front of a storey's sanitary fixtures, as a plan draws them (dashed): [(4, 2) rings]."""
    ids = [o.id for o in doc.objects.values() if o.is_bim and o.ifc_class == "IfcSanitaryTerminal" and o.storey == storey
           and (settings is None or _shown(doc, o, settings))]
    found = _ask_ifc(doc, "free_zones", ids) if ids else {}
    return [np.array([(float(p[0]), float(p[1])) for p in ring]) for _g, ring in sorted(found.items())]


def terrain_contours(doc, terrains, top=None, occluders=None, offset=None, origin=None, u=None, v=None):
    """(0.155) The contour lines of the terrains as a plan draws them — those under its cut (`top`), without what
    hides them (`occluders`: a slab over the terrain): [(segments (K, 2, 2), major, height)]."""
    found = []
    for obj in terrains:
        try:
            interval = float(doc.ifc.terrain_interval(obj.id))
        except Exception:                                   # (not made by this program; the IFC being read)
            interval = terrain_geo.DEFAULT_INTERVAL
        mesh = obj.mesh
        surface = terrain_geo.surface_of(mesh.verts, mesh.tris, getattr(mesh, "normals", None))
        found += [(segs, terrain_geo.is_major(h, interval), h)
                  for h, segs in terrain_geo.contours(mesh.verts, surface, interval, top=top)]
    if not found:
        return []
    if occluders is None or not len(occluders):
        return [(segs[:, :, :2].copy(), major, h) for segs, major, h in found]
    every = np.concatenate([segs for segs, _m, _h in found])
    level_of = np.concatenate([np.full(len(segs), k) for k, (segs, _m, _h) in enumerate(found)])
    seen, index = drawing2d.hidden_lines_removed(occluders, every, np.array((0.0, 0.0, -1.0)), offset, origin, u, v,
                                                 with_index=True)
    out = []
    for k, (_segs, major, h) in enumerate(found):
        mine = seen[level_of[index] == k]
        if len(mine):
            out.append((mine, major, h))
    return out


def background_images(doc, storey):
    """(0.207) The background images a storey's plan shows (as on screen: the visible ones laid on it, or on a storey
    no longer there): [(corners (4, 2), path, opacity)]."""
    storeys = {g for g, _n, _z in doc.storeys()}
    return [(np.array(i.corners(), dtype=float), i.path, float(i.opacity),
             np.array(i.kept_corners(0.0), dtype=float)[:, :2]) for i in getattr(doc, "images", ())
            if i.visible and not i.vertical and (i.storey == storey or i.storey not in storeys)]


def facade_images(doc, normal, offset, origin, u, v):
    """(0.208) The background images stood on a facade that a section / an elevation looking along `normal` sees
    head on — in front of its plane (`offset` along normal), read from its side —, as it draws them: [(corners (4, 2)
    in its 2D frame, path, opacity)]."""
    levels = {g: float(z) for g, _n, z in doc.storeys()}
    n = np.asarray(normal, dtype=float)
    out = []
    for image in getattr(doc, "images", ()):
        if not image.visible or not image.vertical or float(image.front() @ n) > -0.99:
            continue
        level = levels.get(image.storey, 0.0)
        corners = np.array(image.corners3d(level), dtype=float)
        if float(corners[0] @ n) < offset - 1e-6:
            continue                                     # (behind the section's plane)
        out.append((drawing2d.flatten(corners, origin, u, v), image.path, float(image.opacity),
                    drawing2d.flatten(np.array(image.kept_corners(level), dtype=float), origin, u, v)))
    return out


def platform_batters(doc, terrains):
    """(0.203) The terrains' platforms' slopes as a plan draws them (earthworks.batters): the lines where they meet
    the ground and their ticks, (K, 2, 2)."""
    segs = []
    for obj in terrains:
        for lines, ticks in terrain_batters(doc, obj.id):
            segs += [lines[:, :, :2], ticks[:, :, :2]]
    segs = [s for s in segs if len(s)]
    return np.concatenate(segs) if segs else np.zeros((0, 2, 2))


def terrain_batters(doc, guid):
    """[(lines (K, 2, 3), ticks (M, 2, 3))] of each platform of a terrain (earthworks.batters), [] when it has none
    (or the IFC is being read)."""
    from ..core import earthworks
    try:
        platforms = doc.ifc.terrain_platforms(guid)
        survey = doc.ifc.terrain_survey(guid) if platforms else None
    except Exception:
        return []
    return [earthworks.batters(survey, p) for p in platforms] if platforms else []


def terrain_slope_fills(terrains, top=None):
    """(0.201) The terrains' surfaces as a plan colours them by slope (terrain.SLOPE_BANDS) — the triangles under its
    cut (`top`), joined by band: [(band, [(outline (N, 2), [holes])])], lowest band first."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    by_band = {}
    for obj in terrains:
        mesh = obj.mesh
        surface = terrain_geo.surface_of(mesh.verts, mesh.tris, getattr(mesh, "normals", None))
        if not len(surface):
            continue
        p = mesh.verts[surface]
        keep = np.ones(len(p), dtype=bool) if top is None else p[:, :, 2].min(axis=1) <= top
        a, b = p[:, 1, :2] - p[:, 0, :2], p[:, 2, :2] - p[:, 0, :2]
        keep &= np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]) > 1e-10          # (not a sliver seen edge on)
        bands = terrain_geo.slope_bands(mesh.verts, surface[keep])
        for band, tri in zip(bands, p[keep][:, :, :2]):
            by_band.setdefault(int(band), []).append(Polygon(tri))
    return [(band, _shapes(unary_union(polys))) for band, polys in sorted(by_band.items())]


def _shapes(geom):
    """A shapely (multi)polygon as [(outline (N, 2), [holes (M, 2)])] (what is not a polygon in it left out)."""
    parts = getattr(geom, "geoms", None) or [geom]
    return [(np.array(g.exterior.coords)[:-1], [np.array(h.coords)[:-1] for h in g.interiors])
            for g in parts if g.geom_type == "Polygon" and not g.is_empty]


def platform_outlines(doc, terrains):
    """(0.157) The platforms of the terrains as a plan draws them: [(outline (N, 2), its height written)]."""
    from . import spots
    out = []
    for obj in terrains:
        try:
            platforms = doc.ifc.terrain_platforms(obj.id)
        except Exception:                                   # (the IFC being read)
            platforms = []
        out += [(np.array(p.outline, dtype=float), platform_text(p)) for p in platforms]
    return out


def platform_text(platform):
    """What a plan writes in a platform: its height ("+12,00"); a ramp's (0.205) at its two ends and its slope
    ("+11,00 / +12,50 · 8,3 %")."""
    from . import spots
    sep = decimal_sep()
    if not platform.is_ramp():
        return spots.text(platform.z, sep)
    return "{} / {} · {} %".format(spots.text(platform.z, sep), spots.text(platform.z_end, sep),
                                   "{:.1f}".format(platform.slope() * 100.0).replace(".", sep))


ELECTRICAL = ("IfcOutlet", "IfcSwitchingDevice", "IfcElectricDistributionBoard", "IfcJunctionBox")


def electrical_points(doc, storey, settings=None):
    """(0.143) A storey's electrical points, as a plan draws them (their symbols): [(kind, back (3,), angle)]."""
    ids = [o.id for o in doc.objects.values() if o.is_bim and o.ifc_class in ELECTRICAL and o.storey == storey
           and (settings is None or _shown(doc, o, settings))]
    found = _ask_ifc(doc, "point_symbols", ids) if ids else {}
    return [found[g] for g in sorted(found)]


def room_labels(doc, storey):
    """The labels of a storey's rooms on its plan (0.125): [(where (2,) — as on screen, inside the room —, its
    name, number, area as written)]."""
    from shapely.geometry import Polygon
    from ..core.rooms import label_point
    try:
        infos = doc.ifc.spaces(storey)
    except Exception:                                   # (the IFC still being read, a file without rooms)
        return []
    out = []
    for info in infos:
        poly = Polygon(info["outline"], info["holes"])
        if poly.is_empty or not poly.is_valid:
            continue
        area = "{:.2f} m²".format(info["area"]).replace(".", decimal_sep())
        out.append((np.array(label_point(poly), dtype=float), info["name"], info["number"], area))
    return out


def underlay_storey(doc, storey, which):
    """The storey just below / above `storey` (GlobalId), or None."""
    ordered = [g for g, _n, _z in sorted(doc.storeys(), key=lambda s: s[2])]
    if storey not in ordered:
        return None
    k = ordered.index(storey) + (-1 if which == "below" else 1)
    return ordered[k] if 0 <= k < len(ordered) else None


def underlay_lines(doc, storey, bounds=None):
    """The plan of `storey` as plain lines (its cut outlines and what it sees), for another plan's
    underlay — inside `bounds` (lowest, highest corner) when given."""
    other = plan(doc, storey, "", underlay=False)
    segs = [other.lines.reshape(-1, 2, 2)] if len(other.lines) else []
    for ring in other.cut if other.outline is None else other.outline:     # (0.320: joined, no line between walls)
        ring = np.asarray(ring, dtype=float)
        segs.append(np.stack((ring, np.roll(ring, -1, axis=0)), axis=1))
    lines = np.concatenate(segs) if segs else np.zeros((0, 2, 2))
    if bounds is not None and len(lines):
        (x0, y0), (x1, y1) = bounds
        lines = drawing2d.clip_segments_to_rect(lines, (x0, y0, x1, y1))
    return lines


def crop(drawing, rect):
    """Only what is inside the rectangle (x0, y0, x1, y1) of a drawing (its crop region, 0.65)."""
    clip = lambda ring: drawing2d.clip_ring_to_rect(ring, rect)        # noqa: E731
    kept = [(clip(ring), hatch) for ring, hatch in zip(drawing.cut, list(drawing.hatch) + [None] * len(drawing.cut))]
    drawing.cut = [ring for ring, _h in kept if ring is not None]
    drawing.hatch = [hatch for ring, hatch in kept if ring is not None]
    drawing.fills = [(r, hatch) for r, hatch in ((clip(ring), hatch) for ring, hatch in drawing.fills) if r is not None]
    if drawing.outline is not None:                                                     # (0.320)
        drawing.outline = [r for r in (clip(ring) for ring in drawing.outline) if r is not None]
    if len(getattr(drawing, "breaks", ())):                                             # (0.333)
        drawing.breaks = drawing2d.clip_segments_to_rect(drawing.breaks, rect)
    drawing.lines = drawing2d.clip_segments_to_rect(drawing.lines, rect)
    drawing.symbols = drawing2d.clip_segments_to_rect(drawing.symbols, rect)
    faces = []                                                                          # (0.315)
    for ring, rgb, alpha, depth in getattr(drawing, "faces", ()):
        if isinstance(ring, list):                  # (0.316: a shadow, with its holes: each ring cut)
            rings = [r for r in (clip(x) for x in ring) if r is not None]
            if rings and clip(ring[0]) is not None:
                faces.append((rings, rgb, alpha, depth))
        else:
            r = clip(ring)
            if r is not None:
                faces.append((r, rgb, alpha, depth))
    drawing.faces = faces
    drawing.surface_lines = [(part, colour) for part, colour in
                             ((drawing2d.clip_segments_to_rect(segs, rect), colour)
                              for segs, colour in getattr(drawing, "surface_lines", ())) if len(part)]
    grids = []
    for a2, b2, tag in drawing.grids:
        part = drawing2d.clip_segments_to_rect(np.array([[a2, b2]]), rect)
        if len(part):
            grids.append((part[0][0], part[0][1], tag))
    drawing.grids = grids
    marks = []                                      # (a section's line cut to it; an elevation's mark in it, 0.121)
    for m in drawing.marks:
        part = drawing2d.clip_segments_to_rect(np.array([[m.a, m.b]]), rect) if m.kind == "section" else None
        if part is not None and len(part):
            marks.append(marks_model.Mark(m.kind, m.tag, part[0][0], part[0][1], m.look, m.ref))
        elif m.kind != "section" and rect[0] <= m.a[0] <= rect[2] and rect[1] <= m.a[1] <= rect[3]:
            marks.append(m)
    drawing.marks = marks
    drawing.rooms = [r for r in drawing.rooms if rect[0] <= r[0][0] <= rect[2] and rect[1] <= r[0][1] <= rect[3]]
    drawing.above = [r for r in (clip(ring) for ring in drawing.above) if r is not None]      # (0.135)
    inside = lambda p: rect[0] - 1e-6 <= p[0] <= rect[2] + 1e-6 and rect[1] - 1e-6 <= p[1] <= rect[3] + 1e-6  # noqa
    drawing.slopes = [s for s in getattr(drawing, "slopes", ()) if inside(s[0])]               # (0.136)
    drawing.zones = [r for r in (clip(ring) for ring in getattr(drawing, "zones", ())) if r is not None]   # (0.140)
    drawing.points = [q for q in getattr(drawing, "points", ()) if inside(q[1][:2])]           # (0.143)
    drawing.contours = [(part, major, h) for part, major, h in
                        ((drawing2d.clip_segments_to_rect(segs, rect), major, h)
                         for segs, major, h in getattr(drawing, "contours", ())) if len(part)]     # (0.155)
    drawing.platforms = [(r, text) for r, text in ((clip(ring), text) for ring, text in getattr(drawing, "platforms", ()))
                         if r is not None]                                              # (0.157)
    drawing.callouts = [c for c in drawing.callouts if inside(c[0][:2]) and inside(c[0][2:])]
    if len(getattr(drawing, "batters", ())):                                             # (0.203)
        drawing.batters = drawing2d.clip_segments_to_rect(drawing.batters, rect)
    if getattr(drawing, "slope_fills", None):                                            # (0.201)
        from shapely.geometry import box
        frame = box(*rect)
        drawing.slope_fills = [(band, parts) for band, parts in
                               ((band, _shapes(frame.intersection(_union(shapes)))) for band, shapes in drawing.slope_fills)
                               if parts]
    drawing._qt_paths = None
    return drawing


def _union(shapes):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    return unary_union([Polygon(outline, holes) for outline, holes in shapes])


def detail_drawing(doc, uid, title):
    """A detail view's drawing (0.133): its parent view's, only what is inside its rectangle — the cut, what is
    seen, the dimensions and the drawing in the view whose ends are in it, its levels across it; no north arrow
    and no marks of the other views. None if it, or its view, is no longer there."""
    detail = doc.detail(uid) if hasattr(doc, "detail") else None
    if detail is None:
        return None
    kind, ref = detail.parent[0], detail.parent[1]
    base = of_view(doc, kind, ref, title)
    if base is None or isinstance(base, TableDrawing):
        return None
    x0, y0, x1, y1 = detail.rect
    out = crop(base, (x0, y0, x1, y1))
    inside = lambda p: x0 - 1e-6 <= p[0] <= x1 + 1e-6 and y0 - 1e-6 <= p[1] <= y1 + 1e-6      # noqa: E731
    out.dims = [d for d in out.dims if inside(d[0]) and inside(d[1])]
    out.angles = [a for a in out.angles if inside(a[0])]
    out.annotations = [a for a in out.annotations if all(inside(p) for pts, _c in a[1] for p in pts)
                       and (a[0] != "text" or inside(a[4]))]
    out.levels = [(z, name) for z, name in out.levels if y0 <= z <= y1]
    out.marks, out.north, out.callouts = [], False, []
    out.title = title
    out.frame = (x0, y0, x1, y1)
    return out


def section(doc, point, normal, title, view=None):
    """The section through `point` looking along `normal` (horizontal): every storey, heights
    as they are (the drawing's 0 is the model's 0). view: its key, for its dimensions."""
    n = np.asarray(normal, dtype=float)
    n = n / np.linalg.norm(n)
    right = np.cross(n, (0.0, 0.0, 1.0))                            # to the right when looking along n
    settings = doc.view_settings(view)
    objects = [o for o in doc.objects.values() if o.is_bim and _shown(doc, o, settings)]
    origin = np.array((point[0], point[1], 0.0))
    offset = float(n @ np.asarray(point, dtype=float))
    up = np.array((0.0, 0.0, 1.0))
    drawing = _draw(doc, objects, n, offset, origin, right, up, title, rule=settings.rule, detail=settings.detail,
                    look=drawn_look(doc, settings), elements=settings.elements)
    drawing.symbols = opening_signs(doc, objects, n, offset, origin, right, up, drawing._occluders)   # (0.292)
    drawing.levels = marks_model.level_marks(doc)                   # (its storeys' levels, 0.121)
    if settings.levels and len(settings.levels) == 2:               # (0.464: their ends where a hand put them)
        drawing.level_ends = tuple(float(c) for c in settings.levels)
    drawing.images = facade_images(doc, n, float(n @ np.asarray(point, dtype=float)), origin, right,
                                   np.array((0.0, 0.0, 1.0)))      # (the photos on its facades, 0.208)
    return _add_dimensions(doc, drawing, view, origin, right, np.array((0.0, 0.0, 1.0)))


def opening_signs(doc, objects, normal, offset, origin, u, v, occluders=None):
    """(0.292) The doors' and windows' signs of how they open (Document.elevation_signs) seen in a section or an
    elevation: of those wholly beyond its plane (one it cuts shows its cut), the lines something in front hides taken
    out — the signs on a leaf's far face too, behind its glass — as (K, 2, 2) on its paper."""
    n = np.asarray(normal, dtype=float)
    ids = []
    for o in objects:
        if o.ifc_class not in ("IfcDoor", "IfcWindow"):
            continue
        box = o.mesh.bounds()
        if box is not None and all(float(np.array((x, y, z)) @ n) > offset for x in (box[0][0], box[1][0])
                                   for y in (box[0][1], box[1][1]) for z in (box[0][2], box[1][2])):
            ids.append(o.id)
    found = doc.elevation_signs(ids) if ids else {}
    if not found:
        return np.zeros((0, 2, 2))
    edges = np.concatenate(list(found.values()))
    if occluders is not None and len(occluders):
        return drawing2d.hidden_lines_removed(occluders, edges, n, offset, origin, u, v)
    return drawing2d.flatten(edges, origin, u, v)


ELEVATION_LOOKS = {"N": (0.0, -1.0, 0.0), "S": (0.0, 1.0, 0.0), "E": (-1.0, 0.0, 0.0), "W": (1.0, 0.0, 0.0)}


def elevation_plane(doc, side):
    """(point, normal) of elevation N / S / E / W: a section whose plane is behind the whole
    model (nothing is cut), looking at its centre from that side. None if there is no model."""
    boxes = [o.mesh.bounds() for o in doc.objects.values() if o.is_bim]
    boxes = [b for b in boxes if b is not None]
    if not boxes:
        return None
    lo = np.min([b[0] for b in boxes], axis=0)
    hi = np.max([b[1] for b in boxes], axis=0)
    centre, radius = (lo + hi) / 2, float(np.linalg.norm(hi - lo)) / 2
    normal = np.array(ELEVATION_LOOKS[side])
    return centre - normal * (radius + 1.0), normal


def elevation(doc, side, title):
    plane = elevation_plane(doc, side)
    return section(doc, plane[0], plane[1], title, ("elevation", side)) if plane is not None else Drawing(title)


ISO = (1.0, 1.0, -0.9)      # the 3D view's look on a sheet when it has no camera: from the south-west, above


def view3d_drawing(doc, uid, title):
    """A 3D view on a sheet (0.134): the model drawn in lines as seen from its camera's direction — an
    axonometric (no perspective), the edges hidden by what is in front taken out, as an elevation is; the
    classes its view hides left out. uid: a named 3D view's, or None (the 3D view: from the south-west)."""
    view = doc.view3d(uid) if uid and hasattr(doc, "view3d") else None
    if uid and view is None:
        return None
    camera = view.camera if view is not None else None
    if camera:
        n = np.asarray(camera["focus"], dtype=float) - np.asarray(camera["position"], dtype=float)
    else:
        n = np.array(ISO)
    if np.linalg.norm(n) < 1e-9:
        n = np.array(ISO)
    n = n / np.linalg.norm(n)
    right = np.cross(n, (0.0, 0.0, 1.0))
    right = right / np.linalg.norm(right) if np.linalg.norm(right) > 1e-6 else np.array((1.0, 0.0, 0.0))
    up = np.cross(right, n)
    settings = doc.view_settings(("3d", uid) if uid else ("3d",))
    objects = [o for o in doc.objects.values() if o.is_bim and _shown(doc, o, settings)]
    boxes = [o.mesh.bounds() for o in objects if o.mesh.bounds() is not None]
    if not boxes:
        return Drawing(title)
    lo = np.min([b[0] for b in boxes], axis=0)
    hi = np.max([b[1] for b in boxes], axis=0)
    centre, radius = (lo + hi) / 2, float(np.linalg.norm(hi - lo)) / 2
    # (0.315) its view style painted on paper — the usual looks (shaded, hidden lines…) as always, in lines
    look = drawn_look(doc, settings, settings.style if settings.style not in PLAIN_LOOKS else "")
    drawing = _draw(doc, objects, n, float(n @ centre) - radius - 1.0, centre, right, up, title, detail="coarse",
                    look=look, elements=settings.elements)
    drawing.cut, drawing.fills, drawing.hatch, drawing.outline = [], [], [], []   # (nothing is cut: the plane is
    #                                                                               behind all)
    return drawing


PLAIN_LOOKS = ("shaded", "hidden", "wire", "xray")      # (0.315) a 3D view's looks drawn in lines on a sheet


def drawn_look(doc, settings, key=None):
    """(0.315) The view style a drawing is made with: its view's (given to it, or by its template), else None (as
    always: lines, the cut by material)."""
    key = key if key is not None else settings.drawn_style
    finder = getattr(doc, "view_style", None)
    return finder(key) if key and finder is not None else None


def of_view(doc, kind, ref, title):
    """The drawing of a view as kept on a sheet (sheets.Placed): a storey's plan, a named
    section, an elevation. None if that view is no longer there (storey or section deleted)."""
    if kind == "plan":
        return plan(doc, ref, title) if any(g == ref for g, _n, _z in doc.storeys()) else None
    if kind == "section":
        s = next((s for s in doc.sections if s.name == ref), None)
        return section(doc, s.point, s.normal, title, ("section", ref)) if s is not None else None
    if kind == "elevation" and ref in ELEVATION_LOOKS:
        return elevation(doc, ref, title)
    if kind == "schedule":                                          # (a schedule's table, 0.132)
        return schedule_drawing(doc, ref, title)
    if kind == "detail":                                            # (a detail view, 0.133)
        return detail_drawing(doc, ref, title)
    if kind == "3d":                                                # (a 3D view, in lines, 0.134)
        return view3d_drawing(doc, ref or None, title)
    if kind in ("rebar", "rebar_cut"):                    # (a member's reinforcement, 0.168; its section, 0.234)
        from .rebar_drawings import apply_moves, rebar_drawing     # (0.238: its labels where a hand put them)
        return apply_moves(doc, rebar_drawing(doc, ref, title, cut=kind == "rebar_cut"), (kind, ref))
    if kind == "structure":                                         # (a storey's structure plan, 0.168)
        from .rebar_drawings import apply_moves, structure_plan
        return apply_moves(doc, structure_plan(doc, ref, title), (kind, ref))
    if kind == "structure_below":                                   # (…its formwork seen from below, 0.235)
        from .rebar_drawings import apply_moves, structure_below
        return apply_moves(doc, structure_below(doc, ref, title), (kind, ref))
    if kind == "rebar_details":                                     # (the project's typical details, 0.237)
        from .rebar_details import details_drawing
        return details_drawing(doc, title)
    if kind == "openings":                                          # (the project's mapa de vãos, 0.293)
        from .openings_map import openings_map
        return openings_map(doc, title)
    return None
