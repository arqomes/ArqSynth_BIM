"""(0.288) The door and window generator: a joinery design — a frame round rows of cells, each cell a leaf that opens
one way or a fixed light, glazed or solid — and what is made of it: its pieces for the 3D body (the frame with its
mullions and transoms, the leaves, the glass, the solid panels, each in its material), a door's plan symbol (its
leaves open, their swing) and IFC's names for how it opens (IfcDoorTypeOperationEnum, IfcWindowTypePartitioningEnum,
the panels' IfcDoorPanelOperationEnum / IfcWindowPanelOperationEnum).

Sizes: the rows from the bottom up, the cells of each row from the left, each its size between the middles of the
bars on either side of it (the outer ones from the frame's outer edge) — a size of 0 shares what the others leave. Two
leaves that close on each other (a pair of casements, double doors, two sliding leaves) have no mullion between them.

A door's or window's own frame of reference: x along the wall from its left edge (seen from the face it was placed
on), y across the wall from that face, z up from its bottom. The leaves open to +y, as IFC's door symbols do: a
left-hand leaf is hinged on its left seen along +y."""

import functools
import json
import math
from dataclasses import dataclass, fields, replace

import numpy as np

from .mesh import planar_union


@dataclass(frozen=True)
class Operation:
    """How a cell opens: its IFC names as a window's panel and as a door's leaf ("": not a door's), its mirror image,
    the side it is hinged on (or opens to: a sliding / folding one), seen along +y."""
    key: str
    window: str        # IfcWindowPanelOperationEnum
    door: str          # IfcDoorPanelOperationEnum; "": a window's way of opening, not a door's leaf
    mirror: str
    hand: str          # "LEFT" / "RIGHT" / ""
    name_pt: str
    name_en: str


OPERATIONS = {o.key: o for o in (
    Operation("fixed", "FIXEDCASEMENT", "FIXEDPANEL", "fixed", "", "Fixo", "Fixed"),
    Operation("left", "SIDEHUNGLEFTHAND", "SWINGING", "right", "LEFT",
              "De batente (dobradiças à esquerda)", "Side-hung (hinged left)"),
    Operation("right", "SIDEHUNGRIGHTHAND", "SWINGING", "left", "RIGHT",
              "De batente (dobradiças à direita)", "Side-hung (hinged right)"),
    Operation("tilt_left", "TILTANDTURNLEFTHAND", "", "tilt_right", "LEFT",
              "Oscilobatente (dobradiças à esquerda)", "Tilt and turn (hinged left)"),
    Operation("tilt_right", "TILTANDTURNRIGHTHAND", "", "tilt_left", "RIGHT",
              "Oscilobatente (dobradiças à direita)", "Tilt and turn (hinged right)"),
    Operation("top", "TOPHUNG", "", "top", "", "Projetante (dobradiças em cima)", "Top-hung"),
    Operation("bottom", "BOTTOMHUNG", "", "bottom", "", "Basculante (dobradiças em baixo)", "Bottom-hung"),
    Operation("pivot_h", "PIVOTHORIZONTAL", "", "pivot_h", "", "Pivotante horizontal", "Horizontal pivot"),
    Operation("pivot_v", "PIVOTVERTICAL", "", "pivot_v", "", "Pivotante vertical", "Vertical pivot"),
    Operation("slide_left", "SLIDINGHORIZONTAL", "SLIDING", "slide_right", "LEFT",
              "De correr (abre para a esquerda)", "Sliding (opens to the left)"),
    Operation("slide_right", "SLIDINGHORIZONTAL", "SLIDING", "slide_left", "RIGHT",
              "De correr (abre para a direita)", "Sliding (opens to the right)"),
    Operation("slide_up", "SLIDINGVERTICAL", "", "slide_up", "", "Guilhotina", "Vertical sliding (sash)"),
    Operation("swing_left", "OTHEROPERATION", "DOUBLE_ACTING", "swing_right", "LEFT",
              "Vaivém (dobradiças à esquerda)", "Double-acting (hinged left)"),
    Operation("swing_right", "OTHEROPERATION", "DOUBLE_ACTING", "swing_left", "RIGHT",
              "Vaivém (dobradiças à direita)", "Double-acting (hinged right)"),
    Operation("fold_left", "OTHEROPERATION", "FOLDING", "fold_right", "LEFT",
              "Harmónio (recolhe à esquerda)", "Folding (folds to the left)"),
    Operation("fold_right", "OTHEROPERATION", "FOLDING", "fold_left", "RIGHT",
              "Harmónio (recolhe à direita)", "Folding (folds to the right)"),
)}
FILLS = {"glass": ("Vidro", "Glass"), "panel": ("Painel cego", "Solid panel"),
         "frosted": ("Vidro fosco", "Frosted glass"), "wood": ("Madeira", "Wood"),                        # (0.306)
         "louvre": ("Veneziana", "Louvres")}
GLAZED = ("glass", "frosted")              # (0.306) the fills that are glass
FRAMED = ("glass", "frosted", "louvre")    # (0.306) the fills a leaf holds in its own frame (stiles and rails)
FILL_ROLE = {"glass": "glass", "frosted": "frosted", "panel": "panel", "wood": "wood", "louvre": "vent"}
SWINGING = ("left", "right", "tilt_left", "tilt_right", "swing_left", "swing_right")
SLIDING = ("slide_left", "slide_right")
ARC_STEPS = 16                     # a quarter of a swing, in straight pieces
ARROW = 0.10                       # m: a sliding leaf's arrow, this far beyond the frame (and its head this long)


@dataclass(frozen=True)
class Cell:
    """A cell of a row: how it opens, what fills it, its width (0: a share of what the others leave). (0.306) In a
    design by columns: a cell of a column, its `width` its height."""
    operation: str = "fixed"
    fill: str = "glass"            # FILLS: "glass" | "panel" | (0.306) "frosted" | "wood" | "louvre"
    width: float = 0.0


@dataclass(frozen=True)
class Row:
    """A row of cells from the left, its height (0: a share of what the others leave)."""
    cells: tuple = (Cell(),)
    height: float = 0.0


@dataclass(frozen=True)
class Design:
    """A door's or window's joinery. Sizes in meters: the frame's face width and its depth across the wall (0: the
    wall's — a door's lining), a leaf's frame (a glazed leaf's stiles and rails) and its thickness, the mullions and
    transoms, the glazing's thickness; bottom: a frame member under the bottom row (a window's; a door has none — its
    fixed lights at the floor stand on a rail); casing: a lining's casings (guarnições) on both faces of the wall (or
    one), over its jambs and head and this far onto the wall; stone: (0.290) a door's soleira — between its jambs,
    across the wall and out of its outer face, its leaves over it — or a window's peitoril — under its frame, from its
    inner face to out of the wall's outer face, with its pingadeira; hardware: its handles and hinges; louvres: (0.295)
    its portadas de lâminas outside, shut or open."""
    kind: str = "window"
    rows: tuple = (Row(),)
    frame: float = 0.05
    depth: float = 0.07
    sash: float = 0.06
    sash_depth: float = 0.06
    mullion: float = 0.06
    glass: float = 0.024
    bottom: bool = True
    casing: float = 0.0            # guarnições: how far onto the wall they go beyond the opening (0: none)
    casing_depth: float = 0.015    # their thickness, on both faces of the wall
    casing_sides: str = "both"     # (0.290) "both" | "open" (the face it opens to) | "push" (the other)
    stone: float = 0.0             # (0.290) a door's soleira / a window's peitoril: its thickness (0: none)
    stone_out: float = 0.03        # how far it stands out of the wall's outer face (the one it is pushed from)
    drip: bool = True              # a peitoril's pingadeira: a groove under its nose
    hardware: bool = False         # (0.290) handles and hinges drawn
    shutter: float = 0.0           # (0.291) an estore: its box's height, at the top of the opening (0: none)
    shutter_closed: float = 0.0    # how far it is let down: 0 rolled up … 1 shut
    screen: bool = False           # (0.291) a mosquiteiro: a fixed insect screen outside the frame
    grille: bool = False           # (0.291) a grade: upright bars outside the frame, in the reveal
    arch: str = ""                 # (0.294) its head: "" square, "round" (volta inteira), "segmental" (abatido),
    #                                "pointed" (ogival, equilateral)
    arch_rise: float = 0.0         # a segmental arch's rise (0: a sixth of the width)
    louvres: str = ""              # (0.295) portadas de lâminas outside: "" none, "left" / "right" one leaf hinged on
    #                                that side (seen along +y), "pair" two
    louvres_open: bool = False     # opened: turned back flat on the wall's outer face (else shut over the opening)
    columns: bool = False          # (0.306) by columns: the mullions run its whole height, each `rows` a column from the
    #                                left (its `height` its width), its cells from the top down (their `width` their
    #                                height) with the transoms between them — the Caixilho Studio's way
    frame_material: str = "aluminio"
    panel_material: str = "aluminio"
    glass_material: str = "vidro"
    stone_material: str = "pedra"
    hardware_material: str = "inox"
    shutter_material: str = "aluminio"
    screen_material: str = "rede"
    grille_material: str = "aco_preto"
    louvres_material: str = "madeira"
    frosted_material: str = "vidro_fosco"      # (0.306) the fills «frosted» and «wood»
    wood_material: str = "madeira"
    plan_open: bool = True         # (0.359) a door in plan: its leaves drawn open with their swing — else closed in the
    #                                frame, the swing shown by its line alone (the arc and a thin line where it opens to)
    swing_style: str = "solid"     # (0.359) the swing's lines: "solid" | "dashed"


def _cell(c, fill):
    return c if isinstance(c, Cell) else Cell(c, fill)


def door(*leaves, transom=0.0, fill="panel", **sizes):
    """A door's design: its leaves from the left (operations or Cells; solid unless said), with a fixed glazed
    fanlight `transom` high over them (0: none). A wooden door: its lining the wall's depth with casings 5 cm onto the
    wall, leaves 4 cm thick, (0.290) its handles and hinges."""
    values = dict(kind="door", frame=0.05, depth=0.0, sash=0.10, sash_depth=0.04, mullion=0.05, glass=0.008,
                  bottom=False, casing=0.05, hardware=True, frame_material="madeira", panel_material="madeira")
    values.update(sizes)
    design = Design(rows=(Row(tuple(_cell(c, fill) for c in leaves or ("left",))),), **values)
    return with_transom(design, transom)


def window(*rows, fill="glass", **sizes):
    """A window's design: its rows from the bottom up, each its cells from the left (operations or Cells; glazed unless
    said) or a Row. An aluminium window: a frame 7 cm deep, leaves 6 cm, (0.290) its handles and hinges."""
    values = dict(kind="window", hardware=True)
    values.update(sizes)
    made = tuple(r if isinstance(r, Row) else Row(tuple(_cell(c, fill) for c in r)) for r in rows or (("fixed",),))
    return Design(rows=made, **values)


def with_transom(design, transom):
    """A door's design with a fanlight `transom` high over its leaves (its top row's height; a fixed glazed one made if
    it had none); 0: no fanlight (its bottom row alone)."""
    if design.columns:                           # (0.306: a design by columns keeps its own transoms)
        return design
    if transom <= 1e-9:
        return replace(design, rows=design.rows[:1])
    if len(design.rows) == 1:
        return replace(design, rows=design.rows + (Row((Cell("fixed", "glass"),), float(transom)),))
    return replace(design, rows=design.rows[:-1] + (replace(design.rows[-1], height=float(transom)),))


def transom_of(design, height):
    """A door's fanlight: the height of the rows over its leaves (0: none)."""
    if design.columns or len(design.rows) < 2:
        return 0.0
    return float(height - _sizes([r.height for r in design.rows], height)[0])


def mirrored(design):
    """The design seen in a mirror: each row's cells the other way round, each opening the other hand — (0.295) a
    single portada too; (0.306) by columns, the columns the other way round."""
    if design.columns:
        return replace(design, rows=tuple(replace(r, cells=tuple(replace(c, operation=OPERATIONS[c.operation].mirror)
                                                                  for c in r.cells)) for r in reversed(design.rows)),
                       louvres={"left": "right", "right": "left"}.get(design.louvres, design.louvres))
    return replace(design, rows=tuple(replace(r, cells=tuple(replace(c, operation=OPERATIONS[c.operation].mirror)
                                                              for c in reversed(r.cells))) for r in design.rows),
                   louvres={"left": "right", "right": "left"}.get(design.louvres, design.louvres))


def _sizes(wanted, total):
    """The sizes of a row of them `total` long: those given as they are, the zeros sharing equally what is left — all
    scaled alike if they do not fit, or leave nothing to the zeros, or there are no zeros."""
    wanted = [max(float(w), 0.0) for w in wanted]
    given = sum(wanted)
    free = wanted.count(0.0)
    if free and total - given > 1e-6:
        share = (total - given) / free
        return [w if w > 0 else share for w in wanted]
    if given <= 1e-9:
        return [total / len(wanted)] * len(wanted)
    mean = given / (len(wanted) - free)
    weights = [w if w > 0 else mean for w in wanted]
    k = total / sum(weights)
    return [w * k for w in weights]


def _family(op):
    return "swing" if op in SWINGING else "slide" if op in SLIDING else "fold" if op.startswith("fold") else op


def meets(a, b):
    """Do two leaves side by side close on each other, with no mullion between them: hinged on their outer sides (a
    pair of casements, double doors), both sliding, or folding away from each other."""
    fa, fb = _family(a), _family(b)
    if fa == fb == "slide":
        return True
    return fa == fb and fa in ("swing", "fold") and OPERATIONS[a].hand == "LEFT" and OPERATIONS[b].hand == "RIGHT"


def door_leaf(op):
    """Is it a way a door's leaf opens (not a fixed light, nor a window's way)?"""
    return OPERATIONS[op].door not in ("", "FIXEDPANEL")


@dataclass(frozen=True)
class Light:
    """A cell where it is: its row and place in it, its clear rectangle (inside the bars round it) in the elevation —
    x along, z up —, and rail: it stands on a rail (a fixed light at the foot of a door, which has no frame there)."""
    row: int
    index: int
    cell: Cell
    x0: float
    x1: float
    z0: float
    z1: float
    rail: bool = False


def _base(design):
    """(0.290) Where a window's frame stands: on its peitoril (a door's frame stands on the floor)."""
    return max(design.stone, 0.0) if design.kind == "window" else 0.0


def _top(design):
    """(0.291) How far under the opening's top the frame stops: under its estore's box (an arched one has none)."""
    return 0.0 if design.arch else max(design.shutter, 0.0)


# ------------------------------------------------------------ arches (0.294)

ARCH_STEPS = 24                    # an arch's curve, in straight pieces
ARCHES = ("", "round", "segmental", "pointed")


def arch_rise(design, width):
    """(0.294) How high a door's / window's arch rises over its springing: a round one half its width, a pointed
    (equilateral) one √3/2 of it, a segmental one as given (a sixth of its width if not); a square head none."""
    if design.arch == "round":
        return width / 2
    if design.arch == "pointed":
        return width * math.sqrt(3) / 2
    if design.arch == "segmental":
        return design.arch_rise if design.arch_rise > 0 else width / 6
    return 0.0


def _arch_points(design, width, height, inset):
    """The arch's curve `inset` in from the outline (negative: out), from the right jamb over to the left one, in
    ARCH_STEPS pieces: a round arch a half circle; a segmental one an arc of the circle through its springings and
    its crown; a pointed one two arcs, each centred at the other springing, meeting at the crown."""
    half = width / 2
    rise = arch_rise(design, width)
    spring = height - rise
    n = ARCH_STEPS
    if design.arch == "round":
        r = half - inset
        return [(half + r * math.cos(a), spring + r * math.sin(a)) for a in np.linspace(0.0, math.pi, n + 1)]
    if design.arch == "segmental":
        big = (half * half + rise * rise) / (2 * rise)
        r = big - inset
        a0 = math.acos(min(max((half - inset) / r, -1.0), 1.0))
        return [(half + r * math.cos(a), height - big + r * math.sin(a))
                for a in np.linspace(a0, math.pi - a0, n + 1)]
    r = width - inset
    crown = math.acos(min(half / r, 1.0))
    right = [(r * math.cos(a), spring + r * math.sin(a)) for a in np.linspace(0.0, crown, n // 2 + 1)]
    left = [(width + r * math.cos(a), spring + r * math.sin(a)) for a in np.linspace(math.pi - crown, math.pi,
                                                                                     n // 2 + 1)]
    return right + left[1:]


# (0.296) the ways a leaf cannot open under an arch: hung from its top, sliding, folding
ARCH_REFUSED = ("top", "slide_left", "slide_right", "slide_up", "fold_left", "fold_right")


def with_arch(design, arch, width, rise=0.0):
    """(0.294) A design with this arch (rise: a segmental one's): its top row the arch's, as tall as its rise — one
    fixed light made over the others when it has a single row; (0.296) its cells kept, those that cannot open under an
    arch made fixed —; a square head: its rows as they were."""
    design = replace(design, arch=arch, arch_rise=float(rise) if arch == "segmental" else 0.0)
    if not arch:
        return design
    if design.columns:                  # (0.306) by columns: each column's top cell under the arch, made to open there
        return replace(design, rows=tuple(replace(col, cells=(replace(col.cells[0], operation="fixed")
                                                               if col.cells[0].operation in ARCH_REFUSED
                                                               else col.cells[0],) + col.cells[1:])
                                          for col in design.rows))
    h = arch_rise(design, width)
    if len(design.rows) == 1:
        return replace(design, rows=design.rows + (Row((Cell("fixed", "glass"),), h),))
    top = design.rows[-1]
    cells = tuple(replace(c, operation="fixed") if c.operation in ARCH_REFUSED else c for c in top.cells)
    return replace(design, rows=design.rows[:-1] + (replace(top, height=h, cells=cells),))


def head_at(design, width, height, x, inset):
    """(0.296) How high the opening's head is at x along, `inset` in from its outline: under an arch the curve's height
    there (its ends' beyond them), else its top's."""
    if not design.arch:
        return height - inset
    pts = _arch_points(design, width, height, inset)[::-1]                  # (from the left)
    return float(np.interp(x, [p[0] for p in pts], [p[1] for p in pts]))


def in_arch(design, width, height, light):
    """(0.296) Does a light reach into the arch: its rectangle cut by the frame's inner curve?"""
    if not design.arch:
        return False
    whole = _quad(light.x0, light.x1, light.z0, light.z1)
    cut = clip_convex(whole, outline(design, width, height, design.frame, bottom=light.z0 - 1.0))
    return not cut or abs(_area(cut) - _area(whole)) > 1e-9


def light_outline(design, width, height, light):
    """(0.296) A light's outline in elevation [(x, z)…]: its rectangle, cut by the arch where it reaches into it."""
    whole = _quad(light.x0, light.x1, light.z0, light.z1)
    if not in_arch(design, width, height, light):
        return whole
    return clip_convex(whole, outline(design, width, height, design.frame, bottom=light.z0 - 1.0)) or whole


def _top_of(design, width, height, light):
    """(0.296) A light's top as a function of x: under an arch the frame's inner curve where it is lower."""
    if not in_arch(design, width, height, light):
        return lambda x: light.z1
    return lambda x: min(light.z1, head_at(design, width, height, x, design.frame))


def outline(design, width, height, inset=0.0, bottom=0.0):
    """(0.294) The door's / window's outline in elevation, `inset` in from its own (negative: out), from `bottom` up:
    [(x, z)] counter-clockwise from its bottom left — with a square head a rectangle; else its jambs and its arch."""
    x0, x1 = inset, width - inset
    if not design.arch:
        return [(x0, bottom), (x1, bottom), (x1, height - inset), (x0, height - inset)]
    return [(x0, bottom), (x1, bottom)] + [(float(x), float(z)) for x, z in _arch_points(design, width, height, inset)]


def clip_convex(polygon, region):
    """(0.294) The part of a polygon [(x, z)] inside a convex one, both counter-clockwise (Sutherland–Hodgman): [] when
    nothing of it is."""
    out = [tuple(p) for p in polygon]
    m = len(region)
    for k in range(m):
        if not out:
            break
        (ax, az), (bx, bz) = region[k], region[(k + 1) % m]

        def side(p):
            return (bx - ax) * (p[1] - az) - (bz - az) * (p[0] - ax)

        src, out = out, []
        for j, p in enumerate(src):
            q = src[(j + 1) % len(src)]
            sp, sq = side(p), side(q)
            if sp >= -1e-12:
                out.append(p)
            if (sp >= -1e-12) != (sq >= -1e-12):
                t = sp / (sp - sq)
                out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    out = _distinct(out)
    return out if len(out) >= 3 and abs(_area(out)) > 1e-12 else []


def _distinct(polygon, tolerance=1e-9):
    """A polygon without its repeated points (one after another, and its last on its first)."""
    out = []
    for p in polygon:
        if not out or abs(p[0] - out[-1][0]) > tolerance or abs(p[1] - out[-1][1]) > tolerance:
            out.append(p)
    while len(out) > 1 and abs(out[0][0] - out[-1][0]) <= tolerance and abs(out[0][1] - out[-1][1]) <= tolerance:
        out.pop()
    return out


def _triangulate(polygon):
    """(0.294) The triangles [(i, j, k)] of a simple polygon, counter-clockwise (an arch's band is not convex), by
    clipping its ears; none of no area (points in a line)."""
    pts = [tuple(map(float, p)) for p in polygon]
    idx = list(range(len(pts)))

    def turn(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def inside(p, a, b, c):
        return turn(a, b, p) >= -1e-12 and turn(b, c, p) >= -1e-12 and turn(c, a, p) >= -1e-12

    out = []
    while len(idx) > 3:
        m = len(idx)
        for k in range(m):
            i, j, l = idx[k - 1], idx[k], idx[(k + 1) % m]
            a, b, c = pts[i], pts[j], pts[l]
            area = turn(a, b, c)
            if area < -1e-14:
                continue                                         # (a corner turning in: not an ear)
            if abs(area) <= 1e-14:
                idx.pop(k)                                       # (on a line: no triangle)
                break
            if any(inside(pts[q], a, b, c) for q in idx if q not in (i, j, l) and pts[q] not in (a, b, c)):
                continue
            out.append((i, j, l))
            idx.pop(k)
            break
        else:
            break                                                # (nothing left to clip: a fan of the rest)
    if len(idx) >= 3:
        out += [(idx[0], idx[k], idx[k + 1]) for k in range(1, len(idx) - 1)
                if abs(turn(pts[idx[0]], pts[idx[k]], pts[idx[k + 1]])) > 1e-14]
    return out


def _area(polygon):
    pts = np.asarray(polygon, dtype=float)
    x, z = pts[:, 0], pts[:, 1]
    return float(np.dot(x, np.roll(z, -1)) - np.dot(np.roll(x, -1), z)) / 2


def _band(design, width, height, outer, inner):
    """An arch's band between its curves `outer` and `inner` in from the outline, as one outline counter-clockwise
    (the outer curve over from the right, the inner one back): one piece, no joints."""
    a = _arch_points(design, width, height, outer)
    b = _arch_points(design, width, height, inner)
    return _distinct([(float(x), float(z)) for x, z in list(a) + list(reversed(b))])


def _rows_meet(lower, upper):
    """Two rows of one vertically sliding sash each (a sash window): no transom between them."""
    return len(lower.cells) == len(upper.cells) == 1 and \
        lower.cells[0].operation == upper.cells[0].operation == "slide_up"


def layout(design, width, height):
    """The lights (Light) and the bars between them [(x0, x1, z0, z1)] — the transoms between the rows across the
    frame, the mullions between the cells of a row — of a door / window `width` × `height`. (0.306) By columns: the
    mullions between the columns its whole height, the transoms between the cells of a column."""
    if design.columns:
        return _layout_columns(design, width, height)
    f, m, s = design.frame, design.mullion, design.sash
    rows = design.rows
    base = _base(design)                       # (0.290) a window on its peitoril
    floor = design.stone if design.kind == "door" else 0.0      # (and a door's leaves over its soleira)
    heights = _sizes([r.height for r in rows], height - base - _top(design))
    lights, bars = [], []
    z = base
    for i, (row, h) in enumerate(zip(rows, heights)):
        below = i > 0 and _rows_meet(rows[i - 1], row)
        above = i < len(rows) - 1 and _rows_meet(row, rows[i + 1])
        z0 = z + ((-s / 2 if below else m / 2) if i else (f if design.bottom else floor))
        z1 = z + h - ((-s / 2 if above else m / 2) if i < len(rows) - 1 else f)
        if i < len(rows) - 1 and not above:
            bars.append((f, width - f, z + h - m / 2, z + h + m / 2))
        widths = _sizes([c.width for c in row.cells], width)
        x, k = 0.0, len(row.cells)
        for j, (cell, w) in enumerate(zip(row.cells, widths)):
            left = j > 0 and meets(row.cells[j - 1].operation, cell.operation)
            right = j < k - 1 and meets(cell.operation, row.cells[j + 1].operation)
            # (two sliding leaves overlap by a stile; leaves hinged apart meet at the middle)
            slide = _family(cell.operation) == "slide"
            x0 = x + (f if j == 0 else (-s / 2 if slide else 0.0) if left else m / 2)
            x1 = x + w - (f if j == k - 1 else (-s / 2 if slide else 0.0) if right else m / 2)
            if j < k - 1 and not right:
                bars.append((x + w - m / 2, x + w + m / 2, z0, z1))
            rail = i == 0 and not design.bottom and not door_leaf(cell.operation)
            lights.append(Light(i, j, cell, x0, x1, z0 + (f if rail else 0.0), z1, rail))
            x += w
        z += h
    return lights, bars


def _layout_columns(design, width, height):
    """(0.306) layout() of a design by columns: each column from the left between the mullions, its cells from the top
    down between its transoms. Its lights (Light) numbered as a design by rows' are: `row` from the bottom of their
    column, `index` the column. Two columns of one leaf each that close on each other (a pair of casements, two
    sliding leaves) have no mullion between them; two sashes one over the other in a column, no transom."""
    f, m, s = design.frame, design.mullion, design.sash
    cols = design.rows
    base = _base(design)
    floor = design.stone if design.kind == "door" else 0.0
    top = height - _top(design)
    widths = _sizes([c.height for c in cols], width)
    k = len(cols)
    lights, bars = [], []
    x = 0.0
    for j, (col, w) in enumerate(zip(cols, widths)):
        alone = len(col.cells) == 1
        left = j > 0 and alone and len(cols[j - 1].cells) == 1 and \
            meets(cols[j - 1].cells[0].operation, col.cells[0].operation)
        right = j < k - 1 and alone and len(cols[j + 1].cells) == 1 and \
            meets(col.cells[0].operation, cols[j + 1].cells[0].operation)
        slide = alone and _family(col.cells[0].operation) == "slide"
        x0 = x + (f if j == 0 else (-s / 2 if slide else 0.0) if left else m / 2)
        x1 = x + w - (f if j == k - 1 else (-s / 2 if slide else 0.0) if right else m / 2)
        if j < k - 1 and not right:
            bars.append((x + w - m / 2, x + w + m / 2, base + (f if design.bottom else floor), top - f))
        n = len(col.cells)
        heights = _sizes([c.width for c in col.cells], top - base)
        z = top
        for i, (cell, h) in enumerate(zip(col.cells, heights)):
            last = i == n - 1
            sash_above = i > 0 and cell.operation == col.cells[i - 1].operation == "slide_up"
            sash_below = not last and cell.operation == col.cells[i + 1].operation == "slide_up"
            z1 = z - (f if i == 0 else -s / 2 if sash_above else m / 2)
            z0 = z - h + ((-s / 2 if sash_below else m / 2) if not last else (f if design.bottom else floor))
            if not last and not sash_below:
                bars.append((x0, x1, z - h - m / 2, z - h + m / 2))
            rail = last and not design.bottom and not door_leaf(cell.operation)
            lights.append(Light(n - 1 - i, j, cell, x0, x1, z0 + (f if rail else 0.0), z1, rail))
            z -= h
        x += w
    return lights, bars


def column_heights(design, height):
    """(0.306) A design by columns: each column's cells' heights from the top down."""
    room = height - _base(design) - _top(design)
    return [_sizes([c.width for c in col.cells], room) for col in design.rows]


def bottom_cells(design):
    """(0.306) The cells at the foot of the door / window: its bottom row's — by columns, each column's last."""
    if design.columns:
        return tuple(col.cells[-1] for col in design.rows)
    return design.rows[0].cells


def _across(design, light, y0, y1):
    """Where a light's leaf (or fill) is across the wall: (ya, yb). A leaf at the frame's face it opens to (+y); two
    sliding ones each on its own track (every other one a track further in); a fixed light in the frame's middle."""
    depth = y1 - y0
    op = light.cell.operation
    if op == "fixed":
        t = min(design.glass if light.cell.fill == "glass" else design.sash_depth, depth)
        mid = (y0 + y1) / 2
        return mid - t / 2, mid + t / 2
    if _family(op) == "slide" or op == "slide_up":
        t = min(design.sash_depth, depth / 2)
        track = (light.index if op != "slide_up" else light.row) % 2
        return y1 - (track + 1) * t, y1 - track * t
    return y1 - min(design.sash_depth, depth), y1


def casings(design, width, height, y0, y1):
    """A lining's casings (guarnições): on both faces of the wall (the frame's from y0 to y1, face to face: a frame of
    no depth of its own), over its jambs and head and `casing` onto the wall — [(x0, x1, z0, z1, ya, yb)]; the jambs'
    up to the head's."""
    c, t, f = design.casing, design.casing_depth, design.frame
    if c <= 0 or t <= 0 or design.depth > 0:
        return []
    faces = {"both": ((y0 - t, y0), (y1, y1 + t)), "push": ((y0 - t, y0),), "open": ((y1, y1 + t),)}
    out = []
    for ya, yb in faces.get(design.casing_sides, faces["both"]):
        out += [(-c, f, 0.0, height - f, ya, yb), (width - f, width + c, 0.0, height - f, ya, yb),
                (-c, width + c, height - f, height + c, ya, yb)]
    return out


DRIP = (0.015, 0.010, 0.008)       # m: a pingadeira's groove — in from the nose, wide, deep


def stones(design, width, y0, y1, faces=None):
    """(0.290) A door's soleira — between its jambs, from out of the wall's outer face (the one it is pushed from:
    faces[0]) to its inner face — or a window's peitoril — under its frame, from out of the outer face to the frame's
    inner face, with its pingadeira (a groove under the nose) —: [(lo, hi)] boxes, `stone` thick from the opening's
    bottom. faces: the wall's two faces across (None: the frame's)."""
    t = design.stone
    if t <= 0:
        return []
    outer, inner = faces if faces is not None else (y0, y1)
    out = max(design.stone_out, 0.0)
    nose = outer - out
    x0, x1, back = (design.frame, width - design.frame, inner) if design.kind == "door" else (0.0, width, y1)
    in_, wide, deep = DRIP
    if design.kind == "window" and design.drip and out >= in_ + wide and t > deep + 0.004:
        g0, g1 = nose + in_, nose + in_ + wide
        return [((x0, nose, 0.0), (x1, g0, t)), ((x0, g0, deep), (x1, g1, t)), ((x0, g1, 0.0), (x1, back, t))]
    return [((x0, nose, 0.0), (x1, back, t))]


def hardware(design, width, height, y0, y1):
    """(0.290) The handles and hinges of a door's / window's leaves, as small upright boxes [(lo, hi)]: a leaf hinged on
    a side its hinges there (a door's three, a window's two) out of the face it opens to; its handle at its free side
    — a door's lever on both faces 1 m up, pointing to its hinges; a window's on its inner face (+y), half way up,
    pointing down; a top- or bottom-hung one's on its free rail —; a sliding or folding leaf's pull at its edge; a
    double-acting one's push plates."""
    if not design.hardware:
        return []
    out = []

    def box(x0, x1, ya, yb, z0, z1):
        out.append(((min(x0, x1), min(ya, yb), min(z0, z1)), (max(x0, x1), max(ya, yb), max(z0, z1))))

    lights, _bars = layout(design, width, height)
    for lt in lights:
        op = lt.cell.operation
        if op == "fixed":
            continue
        ya, yb = _across(design, lt, y0, y1)
        hand = OPERATIONS[op].hand
        is_door = design.kind == "door" and lt.row == 0 and door_leaf(op)
        sides = ((1, yb), (-1, ya)) if is_door else ((1, yb),)
        top = _top_of(design, width, height, lt)                 # (0.296: under an arch, its curve)
        middle = (lt.z0 + lt.z1) / 2
        zc = min(max(1.0, lt.z0 + 0.1), lt.z1 - 0.1) if is_door else middle
        if op in ("left", "right", "tilt_left", "tilt_right"):
            hinge = lt.x0 if hand == "LEFT" else lt.x1
            high = top(hinge)                                    # (its hinged stile's top)
            k = 0.2 if high - lt.z0 > 0.8 else (high - lt.z0) / 4
            for z in [lt.z0 + k, high - k] + ([(lt.z0 + high) / 2] if is_door else []):
                box(hinge - 0.007, hinge + 0.007, yb, yb + 0.012, z - 0.05, z + 0.05)
            inward = -1.0 if hand == "LEFT" else 1.0             # from the free side towards the hinges
            fx = (lt.x1 if hand == "LEFT" else lt.x0) + inward * (0.06 if is_door else design.sash / 2)
            zc = min(max(1.0, lt.z0 + 0.1), top(fx) - 0.1) if is_door else (lt.z0 + top(fx)) / 2
            rw, rh = (0.025, 0.075) if is_door else (0.016, 0.04)
            for side, face in sides:
                box(fx - rw, fx + rw, face, face + side * 0.008, zc - rh, zc + rh)                   # its rose,
                box(fx - 0.009, fx + 0.009, face, face + side * 0.05, zc - 0.009, zc + 0.009)        # its neck,
                if is_door:                                                                           # its lever
                    box(fx, fx + inward * 0.13, face + side * 0.04, face + side * 0.058, zc - 0.009, zc + 0.009)
                else:
                    box(fx - 0.01, fx + 0.01, face + side * 0.035, face + side * 0.053, zc - 0.11, zc)
        elif op in ("top", "bottom", "pivot_h", "pivot_v"):
            xm = (lt.x0 + lt.x1) / 2
            z = top(xm) - design.sash / 2 if op == "bottom" else lt.z0 + design.sash / 2
            box(xm - 0.04, xm + 0.04, yb, yb + 0.008, z - 0.016, z + 0.016)
            box(xm - 0.009, xm + 0.009, yb, yb + 0.05, z - 0.009, z + 0.009)
            box(xm, xm + 0.11, yb + 0.035, yb + 0.053, z - 0.01, z + 0.01)
        elif op in ("swing_left", "swing_right"):
            fx = lt.x1 - 0.08 if hand == "LEFT" else lt.x0 + 0.08
            for side, face in sides:
                box(fx - 0.05, fx + 0.05, face, face + side * 0.003, zc + 0.05, zc + 0.35)       # its push plates
        elif op == "slide_up":
            if lt.row == 0:
                xm = (lt.x0 + lt.x1) / 2
                box(xm - 0.05, xm + 0.05, yb, yb + 0.015, lt.z0 + design.sash / 2 - 0.01, lt.z0 + design.sash / 2 + 0.01)
        else:                                       # sliding, folding: a pull at the edge it is pulled by
            ex = lt.x1 - design.sash / 2 if hand == "LEFT" else lt.x0 + design.sash / 2
            for side, face in sides:
                box(ex - 0.012, ex + 0.012, face, face + side * 0.012, zc - 0.08, zc + 0.08)
    return out


SCREEN = (0.020, 0.015, 0.002)     # m: a mosquiteiro's frame — its face, its depth — and its mesh's thickness
GUIDE = (0.025, 0.025)             # m: an estore's guides — across the opening, across the wall
BAR, BAR_GAP = 0.016, 0.12         # m: a grade's square bars, at most this far apart (their middles)


def outside(design, width, height, y0, y1, faces=None):
    """(0.291) What a door / window has outside its frame (on its outer side, y0): [(role, lo, hi)] — its mosquiteiro
    against the frame (a thin frame and its mesh, over the frame's clear opening); further out its estore's guides
    on the jambs and its slats let down `shutter_closed` of the way, its box at the top of the opening across the whole
    wall (faces: the wall's two faces; None: the frame's); further out its grade (upright bars and two flats)."""
    out = []
    f = design.frame
    base, top = _base(design), height - _top(design)
    outer, inner = faces if faces is not None else (y0, y1)
    y = y0                                       # (each one's outer face: the next goes beyond it)
    lo_z, hi_z = base + (f if design.bottom else 0.0), top - f
    if design.screen:
        sf, sd, mesh = SCREEN
        ya, y = y - sd, y - sd
        for x0, x1, z0, z1 in ((f, f + sf, lo_z, hi_z), (width - f - sf, width - f, lo_z, hi_z),
                               (f + sf, width - f - sf, lo_z, lo_z + sf), (f + sf, width - f - sf, hi_z - sf, hi_z)):
            out.append(("screen_frame", (x0, ya, z0), (x1, ya + sd, z1)))
        mid = ya + sd / 2
        out.append(("screen", (f + sf, mid - mesh / 2, lo_z + sf), (width - f - sf, mid + mesh / 2, hi_z - sf)))
    if design.shutter > 0:
        across, deep = GUIDE
        ya, y = y - deep, y - deep
        out.append(("shutter", (0.0, ya, base), (across, ya + deep, top)))
        out.append(("shutter", (width - across, ya, base), (width, ya + deep, top)))
        out.append(("shutter", (0.0, outer, top), (width, inner, height)))                        # its box
        closed = min(max(design.shutter_closed, 0.0), 1.0) * (top - base)
        if closed > 1e-6:                                                                         # its slats
            out.append(("shutter", (across / 2, ya + deep / 3, top - closed), (width - across / 2, ya + 2 * deep / 3,
                                                                              top)))
    if design.grille:
        ya, y = y - BAR - 0.008, y - BAR - 0.008
        n = max(int(math.ceil((width - 2 * f) / BAR_GAP)) - 1, 1)
        for k in range(1, n + 1):
            xm = f + (width - 2 * f) * k / (n + 1)
            out.append(("grille", (xm - BAR / 2, ya, lo_z), (xm + BAR / 2, ya + BAR, hi_z)))
        for zm in (lo_z + 0.15, hi_z - 0.15):
            if hi_z - lo_z > 0.4:
                out.append(("grille", (f, ya - 0.008, zm - 0.02), (width - f, ya, zm + 0.02)))
    return out


def _outermost(design, y0):
    """(0.295) The outer face of what `outside` puts outside the frame (its outer face y0 when nothing)."""
    y = y0
    if design.screen:
        y -= SCREEN[1]
    if design.shutter > 0:
        y -= GUIDE[1]
    if design.grille:
        y -= BAR + 0.016                         # (its bars and, out of them, its flats)
    return y


LOUVRE_LEAF = (0.06, 0.10, 0.06, 0.035)   # m: a portada's stiles, its bottom rail, its top rail, its thickness
LOUVRE_PITCH, LOUVRE_SLAT = 0.045, 0.010  # m: its lâminas one every …, each this thick
LOUVRE_MID = (1.40, 0.08)                 # m: lâminas taller than this get a middle rail this high
LOUVRE_GAP = 0.004                        # m: between the two leaves of a pair


def _quad(x0, x1, z0, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


def _leaf(design, width, height, x0, x1, z0, z1, inset, stile, rail, head, mid=(0.0, 0.0)):
    """(0.295) A leaf x0…x1 × z0…z1 — under an arch, what of it is within the curve `inset` in from the outline —:
    (its frame, its clear openings), polygons [(x, z)…] counter-clockwise. Its frame: its stiles, its bottom rail
    `rail` high, its head `head` high — under an arch one piece along the curve, no joints —, a middle rail mid[1]
    high when its opening is taller than mid[0]; its opening inside (the middle rail's two)."""
    region = outline(design, width, height, inset, bottom=z0 - 1.0) if design.arch else None
    whole = _quad(x0, x1, z0, z1)
    cut = clip_convex(whole, region) if region is not None else whole
    if not cut:
        return [], []
    a, b = x0 + stile, x1 - stile
    if region is None or abs(_area(cut) - _area(whole)) < 1e-9:
        frame = [_quad(x0, a, z0, z1), _quad(b, x1, z0, z1), _quad(a, b, z0, z0 + rail), _quad(a, b, z1 - head, z1)]
        inner = _quad(a, b, z0 + rail, z1 - head)
    else:
        from shapely.geometry import Polygon
        from shapely.geometry.polygon import orient
        frame = [p for p in (clip_convex(_quad(x0, a, z0, z1), region), clip_convex(_quad(b, x1, z0, z1), region),
                             clip_convex(_quad(a, b, z0, z0 + rail), region)) if p]
        inner = clip_convex(_quad(a, b, z0 + rail, z1 - head),
                            outline(design, width, height, inset + head, bottom=z0 - 1.0))
        top = clip_convex(_quad(a, b, z0 + rail, z1), region)
        if top:
            rest = Polygon(top).difference(Polygon(inner)) if inner else Polygon(top)
            for part in getattr(rest, "geoms", [rest]):
                if part.geom_type == "Polygon" and part.area > 1e-9:
                    frame.append(_distinct([tuple(map(float, c))
                                            for c in list(orient(part.simplify(1e-9), 1.0).exterior.coords)[:-1]]))
    if not inner or len(inner) < 3:
        return frame, []
    zs = [z for _x, z in inner]
    lo, hi = min(zs), max(zs)
    tall, thick = mid
    if thick <= 0 or hi - lo <= tall:
        return frame, [inner]
    zm = (lo + hi) / 2 if region is None else (lo + min(hi, z1 - head)) / 2
    bar = clip_convex(inner, _quad(x0 - 1.0, x1 + 1.0, zm - thick / 2, zm + thick / 2))
    halves = [clip_convex(inner, _quad(x0 - 1.0, x1 + 1.0, lo - 1.0, zm - thick / 2)),
              clip_convex(inner, _quad(x0 - 1.0, x1 + 1.0, zm + thick / 2, hi + 1.0))]
    return frame + ([bar] if bar else []), [h for h in halves if h]


def _strips(polygon, pitch):
    """(0.295) A convex polygon in horizontal strips about `pitch` high (its height shared evenly), from the bottom."""
    zs = [z for _x, z in polygon]
    xs = [x for x, _z in polygon]
    lo, hi = min(zs), max(zs)
    n = max(int(round((hi - lo) / pitch)), 1)
    step = (hi - lo) / n
    out = []
    for k in range(n):
        strip = clip_convex(polygon, _quad(min(xs) - 1.0, max(xs) + 1.0, lo + k * step, lo + (k + 1) * step))
        if strip:
            out.append(strip)
    return out


def _louvre_leaves(design, width, y0, faces):
    """(0.295) Where a door's / window's portadas are shut: ([(x0, x1, its hinges' x)] its leaves, ya, yb across)."""
    t = LOUVRE_LEAF[3]
    outer = faces[0] if faces is not None else y0
    yb = min(outer + t, _outermost(design, y0))
    if design.louvres == "pair":
        leaves = [(0.0, width / 2 - LOUVRE_GAP / 2, 0.0), (width / 2 + LOUVRE_GAP / 2, width, width)]
    else:
        leaves = [(0.0, width, 0.0 if design.louvres == "left" else width)]
    return leaves, yb - t, yb


def louvres(design, width, height, y0, faces=None):
    """(0.295) A door's / window's portadas de lâminas, outside all else (y0: the frame's outer face; faces: the wall's
    two faces across, None: the frame's): [(role, polygon [(x, z)…] counter-clockwise, ya, yb)] — each leaf's frame
    («portada»: its stiles, its rails, a middle one if it is tall, under an arch its head along the curve), its lâminas
    («louvre»: each the strip it takes in elevation, the slat falling outwards — to ya), its hinges («hardware»).
    Shut: in the opening flush with the wall's outer face (out of it, if what is outside the frame leaves no room),
    over the sill or the threshold, under the arch; each leaf hinged at a jamb. Open: each leaf turned half round on
    its hinges, flat on the wall beside the opening — its lâminas then falling to the wall («louvre_in»)."""
    if design.louvres not in ("left", "right", "pair"):
        return []
    stile, rail, head, t = LOUVRE_LEAF
    leaves, ya, yb = _louvre_leaves(design, width, y0, faces)
    z0 = _base(design) if design.kind == "window" else max(design.stone, 0.0)
    z1 = height - _top(design)
    out = []
    for x0, x1, hinge in leaves:
        frame, clear = _leaf(design, width, height, x0, x1, z0, z1, 0.0, stile, rail, head, LOUVRE_MID)
        made = [("portada", p) for p in frame]
        made += [("louvre", s) for region in clear for s in _strips(region, LOUVRE_PITCH)]
        if design.hardware:                      # its hinges, on their axis: the jamb's edge at its outer face
            zs = [z for p in frame if min(abs(x - hinge) for x, _z in p) < 1e-6 for _x, z in p]
            top = max(zs) if zs else z1          # (its stile's top there: under an arch, where the curve springs)
            heights = [z0 + 0.15, top - 0.15] + ([(z0 + top) / 2] if top - z0 > 1.5 else [])
            for z in heights:
                out.append(("hardware", _quad(hinge - 0.008, hinge + 0.008, z - 0.04, z + 0.04), ya - 0.008,
                            ya + 0.008))
        for role, p in made:
            if design.louvres_open:              # turned half round on the axis (hinge, ya): mirrored, still CCW
                out.append(("louvre_in" if role == "louvre" else role,
                            [(2 * hinge - x, z) for x, z in reversed(p)], ya - t, ya))
            else:
                out.append((role, p, ya, yb))
    return out


def slat_mesh(polygon, ya, yb, outwards=True):
    """(0.295) (vertices, triangles) of a lâmina: in the strip `polygon` it takes in elevation [(x, z)…], a slat
    LOUVRE_SLAT thick from ya to yb across (a hair in from its leaf's faces), falling to ya (outwards: the rain off it)
    or to yb."""
    zs = [z for _x, z in polygon]
    lo, hi = min(zs), max(zs)
    t = min(LOUVRE_SLAT, (hi - lo) / 2)
    plate = clip_convex(polygon, _quad(-1e3, 1e3, lo, lo + t))
    if not plate:
        return np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64)
    m = min(0.002, (yb - ya) / 4)
    verts, tris = prism_mesh(plate, ya + m, yb - m)
    n = len(plate)
    verts[n:, 2] += (hi - lo - t) if outwards else 0.0          # its back up: it falls to its front
    verts[:n, 2] += 0.0 if outwards else (hi - lo - t)
    return verts, tris


def glazing_fraction(design, width, height):
    """(0.291) How much of the door / window is glass, seen in elevation: its glass's area over its own (IFC's
    GlazingAreaFraction) — (0.294) an arched one's over its outline's."""
    area = sum(_area(poly) for role, poly, _ya, _yb in pieces(design, width, height, 0.0, 0.1)
               if role in ("glass", "frosted"))
    whole = _area(outline(design, width, height)) if width > 0 and height > 0 else 0.0
    return area / whole if whole > 0 else 0.0


def pieces(design, width, height, y0, y1, faces=None):
    """(0.294) The door's / window's pieces as prisms across the wall: [(role, outline [(x, z)…] counter-clockwise,
    ya, yb)] — parts' boxes; with an arch: the frame's head an arched band (one piece), its jambs and their casings
    up to the springing, the casings' head a band round the arch, all within the frame cut by the arch — (0.296) a
    glazed leaf reaching into it with its head along the curve (one piece), its glass cut by it —; (0.295) its
    portadas."""
    out = _pieces(design, width, height, y0, y1, faces)
    # (0.306) a fill of louvres (veneziana): its strips, each a slat
    return [(role, p, ya, yb) for role, poly, ya, yb in out
            for p in (_strips(poly, LOUVRE_PITCH) if role == "vent" else [poly])]


def _pieces(design, width, height, y0, y1, faces=None):
    s = design.sash
    arched = [lt for lt in layout(design, width, height)[0] if lt.cell.operation != "fixed"
              and lt.cell.fill in GLAZED and lt.x1 - lt.x0 > 2 * s + 0.02 and lt.z1 - lt.z0 > 2 * s + 0.02
              and in_arch(design, width, height, lt)] if design.arch else []
    boxes = parts(design, width, height, y0, y1, faces, skip={(lt.row, lt.index) for lt in arched})

    def rect(lo, hi):
        return [(lo[0], lo[2]), (hi[0], lo[2]), (hi[0], hi[2]), (lo[0], hi[2])]

    if not design.arch:
        return [(role, rect(lo, hi), lo[1], hi[1]) for role, lo, hi in boxes] + louvres(design, width, height, y0,
                                                                                         faces)
    f, c = design.frame, design.casing
    leaves = []
    for lt in arched:                                   # (0.296) a leaf under the arch: its frame, its glass
        ya, yb = _across(design, lt, y0, y1)
        frame, clear = _leaf(design, width, height, lt.x0, lt.x1, lt.z0, lt.z1, f, s, s, s)
        t = min(design.glass, yb - ya)
        mid = (ya + yb) / 2
        leaves += [("leaf", p, ya, yb) for p in frame] + [(FILL_ROLE[lt.cell.fill], p, mid - t / 2, mid + t / 2)
                                                          for p in clear]
    spring = height - arch_rise(design, width)
    inner = outline(design, width, height, f, bottom=-1.0)
    under = [(-9.0, -9.0), (width + 9.0, -9.0), (width + 9.0, spring), (-9.0, spring)]     # (under the springing)
    out, casing_faces = [], []
    for role, lo, hi in boxes:
        poly = rect(lo, hi)
        casing = role == "frame" and (lo[1] < y0 - 1e-9 or hi[1] > y1 + 1e-9)
        if casing:
            if hi[0] - lo[0] > width:                   # its head: a band round the arch, below
                casing_faces.append((lo[1], hi[1]))
                continue
            poly = clip_convex(poly, under)
        elif role == "frame" and lo[2] >= height - f - 1e-9 and hi[0] - lo[0] > 2 * f:
            continue                                    # the frame's head: the arched band, below
        elif role == "frame" and (hi[0] <= f + 1e-9 or lo[0] >= width - f - 1e-9):
            poly = clip_convex(poly, under)             # its jambs, up to the springing
        elif role not in ("stone", "hardware"):
            poly = clip_convex(poly, inner)
        if poly:
            out.append((role, poly, lo[1], hi[1]))
    out.append(("frame", _band(design, width, height, 0.0, f), y0, y1))
    for ya, yb in casing_faces:
        out.append(("frame", _band(design, width, height, -c, 0.0), ya, yb))
    return out + leaves + louvres(design, width, height, y0, faces)


def prism_mesh(polygon, ya, yb):
    """(0.294) (vertices, triangles) of a polygon [(x, z)…] (counter-clockwise; an arch's band not convex) from ya to
    yb across, its faces outwards — an upright box's 8 and 12 for a rectangle."""
    pts = np.asarray(polygon, dtype=float)
    n = len(pts)
    front = np.column_stack((pts[:, 0], np.full(n, ya), pts[:, 1]))
    back = np.column_stack((pts[:, 0], np.full(n, yb), pts[:, 1]))
    cap = _triangulate(pts)
    tris = [(i, j, k) for i, j, k in cap]                                  # its face towards −y,
    tris += [(n + i, n + k, n + j) for i, j, k in cap]                     # towards +y,
    for k in range(n):                                                      # and its sides
        j = (k + 1) % n
        tris += [(k, n + k, n + j), (k, n + j, j)]
    return np.vstack((front, back)), np.array(tris, dtype=np.int64)


def parts(design, width, height, y0, y1, faces=None, skip=()):
    """The pieces of a door / window `width` × `height` whose frame is from y0 to y1 across the wall, each an upright
    box: [(role, (x0, y0, z0), (x1, y1, z1))] — role "frame" (the frame, its mullions and transoms, a door's rails),
    "leaf" (a glazed leaf's stiles and rails), "panel" (a solid leaf, a solid fill), "glass", (0.290) "stone" (a
    soleira, a peitoril: faces, the wall's two faces across, None: the frame's), "hardware", (0.291) "shutter",
    "screen_frame", "screen", "grille" (outside). skip: (0.296) the lights (row, index) left out (made by `pieces`:
    leaves under an arch)."""
    out = []

    def box(role, x0, x1, ya, yb, z0, z1):
        if x1 - x0 > 1e-6 and yb - ya > 1e-6 and z1 - z0 > 1e-6:
            out.append((role, (float(x0), float(ya), float(z0)), (float(x1), float(yb), float(z1))))

    f, s = design.frame, design.sash
    base, top = _base(design), height - _top(design)
    box("frame", 0.0, f, y0, y1, base, top)
    box("frame", width - f, width, y0, y1, base, top)
    box("frame", f, width - f, y0, y1, top - f, top)
    if design.bottom:
        box("frame", f, width - f, y0, y1, base, base + f)
    for x0, x1, z0, z1, ya, yb in casings(design, width, height, y0, y1):
        box("frame", x0, x1, ya, yb, z0, z1)
    for lo, hi in stones(design, width, y0, y1, faces):
        box("stone", lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    for lo, hi in hardware(design, width, height, y0, y1):
        box("hardware", lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    for role, lo, hi in outside(design, width, height, y0, y1, faces):
        box(role, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    lights, bars = layout(design, width, height)
    for x0, x1, z0, z1 in bars:
        box("frame", x0, x1, y0, y1, z0, z1)
    for light in lights:
        cell, (x0, x1, z0, z1) = light.cell, (light.x0, light.x1, light.z0, light.z1)
        if (light.row, light.index) in skip:
            continue
        if light.rail:
            box("frame", x0, x1, y0, y1, z0 - f, z0)
        ya, yb = _across(design, light, y0, y1)
        role = FILL_ROLE.get(cell.fill, "glass")          # (0.306: glass, frosted glass, a panel, wood, louvres)
        if cell.operation == "fixed" or cell.fill not in FRAMED or x1 - x0 <= 2 * s + 0.02 or z1 - z0 <= 2 * s + 0.02:
            box(role, x0, x1, ya, yb, z0, z1)                                   # a light, or a solid leaf
            continue
        box("leaf", x0, x0 + s, ya, yb, z0, z1)                                 # a glazed leaf: its stiles,
        box("leaf", x1 - s, x1, ya, yb, z0, z1)
        box("leaf", x0 + s, x1 - s, ya, yb, z0, z0 + s)                         # its rails
        box("leaf", x0 + s, x1 - s, ya, yb, z1 - s, z1)
        t = min(design.glass, yb - ya) if cell.fill in GLAZED else yb - ya
        mid = (ya + yb) / 2
        box(role, x0 + s, x1 - s, mid - t / 2, mid + t / 2, z0 + s, z1 - s)   # and its glass (or its louvres)
    return out


ROLE_MATERIAL = {"frame": "frame_material", "leaf": "frame_material", "panel": "panel_material",
                 "glass": "glass_material", "stone": "stone_material", "hardware": "hardware_material",
                 "shutter": "shutter_material", "screen_frame": "shutter_material", "screen": "screen_material",
                 "grille": "grille_material", "portada": "louvres_material", "louvre": "louvres_material",
                 "louvre_in": "louvres_material",
                 "frosted": "frosted_material", "wood": "wood_material", "vent": "frame_material"}     # (0.306)


def constituents(design):
    """The materials a door / window is made of as IFC4 names them: [(«Lining», «Framing», «Glazing», material key)] —
    the frame; the leaves (their solid panels', else their frames'), if it has any; the glass, if it has any."""
    roles = {p[0] for p in parts(design, 2.0, 2.4 + arch_rise(design, 2.0), 0.0, max(design.depth, 0.1))}
    out = [("Lining", design.frame_material)]
    if "panel" in roles:
        out.append(("Framing", design.panel_material))
    elif "wood" in roles:                                       # (0.306)
        out.append(("Framing", design.wood_material))
    elif "leaf" in roles:
        out.append(("Framing", design.frame_material))
    if "glass" in roles:
        out.append(("Glazing", design.glass_material))
    elif "frosted" in roles:
        out.append(("Glazing", design.frosted_material))
    return out


JOINED = ("frame", "leaf", "portada", "screen_frame", "stone")    # (0.312) the roles whose pieces are joined


def _assembly(design, role, poly, ya, yb, lights, y0, y1):
    """(0.312) What a piece is joined with into one surface (meshes): the frame with its mullions, transoms, rails and
    casings; a leaf's frame — its stiles and rails: the light it is in, on its track (two sliding leaves overlap); the
    portadas; the screen's frame; the stone (a peitoril's three pieces round its pingadeira) — or None: left as it is (a
    pane, a panel, a handle)."""
    if role not in JOINED:
        return None
    if role != "leaf":
        return role
    cx, cz = np.mean(np.asarray(poly, dtype=float), axis=0)
    for lt in lights:
        if lt.x0 - 1e-9 <= cx <= lt.x1 + 1e-9 and lt.z0 - 1e-9 <= cz <= lt.z1 + 1e-9 and \
                np.allclose(_across(design, lt, y0, y1), (ya, yb), atol=1e-9):
            return "leaf", lt.row, lt.index
    return None


def _joined(made):
    """Meshes [(vertices, triangles)] as one."""
    counts = np.cumsum([0] + [len(v) for v, _t in made[:-1]])
    return (np.concatenate([v for v, _t in made]),
            np.concatenate([t + int(k) for k, (_v, t) in zip(counts, made)]))


def meshes(design, width, height, y0, y1, faces=None):
    """The pieces joined by material: {material key: (vertices, triangles)} (the frame and the leaves' frames in the
    frame's material, the solid leaves and fills in the panels', the glass in the glass'; (0.290) a soleira or a
    peitoril in its stone, the handles and hinges in theirs). (0.312) The pieces of one assembly (_assembly) one
    surface (core.mesh.planar_union): no seam where a jamb meets the head, a stile a rail, a casing the next — as a
    joiner's frame is seen; the line round a leaf, between it and the frame or the leaf beside it, stays. Kept for the
    next of the same type, size and wall (read-only arrays): joining costs some 15 ms."""
    return dict(_meshes(design, float(width), float(height), float(y0), float(y1),
                        None if faces is None else tuple(float(y) for y in faces)))


@functools.lru_cache(maxsize=64)
def _meshes(design, width, height, y0, y1, faces):
    lights = layout(design, width, height)[0]
    grouped = {}
    for role, poly, ya, yb in pieces(design, width, height, y0, y1, faces):     # (0.294: an arch's in pieces)
        made = slat_mesh(poly, ya, yb, role != "louvre_in") if role in ("louvre", "louvre_in", "vent") else \
            prism_mesh(poly, ya, yb)                            # (0.295: a portada's lâminas; 0.306: a veneziana's)
        if len(made[0]):
            together = _assembly(design, role, poly, ya, yb, lights, y0, y1)
            grouped.setdefault(getattr(design, ROLE_MATERIAL[role]), {}).setdefault(together, []).append(made)
    out = {}
    for key, assemblies in grouped.items():
        made = []
        for together, its in assemblies.items():
            made += [planar_union(*_joined(its))] if together is not None and len(its) > 1 else its
        out[key] = _joined(made)
        for a in out[key]:
            a.flags.writeable = False
    return out


SIGN_HEAD = 0.06                   # m: an arrow's head in an elevation sign


def elevation_signs(design, width, height):
    """(0.292) How each leaf opens, drawn on it in elevation as European drawings do (seen along +y): [polyline
    [(x, z)…]] — the lines from its free side's corners meeting at its hinges (a side-hung, tilt-and-turn,
    double-acting or door leaf; a tilt-and-turn one's also meeting at its foot), at its top (top-hung) or foot
    (bottom-hung); a pivot's axis; a sliding (or sash) leaf's arrow the way it opens; a folding one's arrow and folds.
    A fixed light: none."""
    out = []
    for lt in layout(design, width, height)[0]:
        op = lt.cell.operation
        x0, x1, z0, z1 = lt.x0, lt.x1, lt.z0, lt.z1
        xm, zm = (x0 + x1) / 2, (z0 + z1) / 2
        hand = OPERATIONS[op].hand
        if op == "fixed":
            continue
        top = _top_of(design, width, height, lt)                 # (0.296: a leaf under an arch: to its curve)
        if op in SWINGING:
            out.append([(x1, top(x1)), (x0, (z0 + top(x0)) / 2), (x1, z0)] if hand == "LEFT" else
                       [(x0, top(x0)), (x1, (z0 + top(x1)) / 2), (x0, z0)])
            if op.startswith("tilt"):
                out.append([(x0, top(x0)), (xm, z0), (x1, top(x1))])
        elif op == "top":
            out.append([(x0, z0), (xm, top(xm)), (x1, z0)])
        elif op == "bottom":
            out.append([(x0, top(x0)), (xm, z0), (x1, top(x1))])
        elif op == "pivot_h":
            level = (z0 + min(top(x0), top(x1))) / 2
            out.append([(x0, level), (x1, level)])
        elif op == "pivot_v":
            out.append([(xm, z0), (xm, top(xm))])
        else:                                       # sliding, sash, folding: an arrow the way it opens
            if op == "slide_up":
                tail, head, d = (xm, z0 + 0.3 * (z1 - z0)), (xm, z0 + 0.7 * (z1 - z0)), (0.0, 1.0)
            else:
                d = (-1.0, 0.0) if hand == "LEFT" else (1.0, 0.0)
                tail = (xm - d[0] * 0.2 * (x1 - x0), zm)
                head = (xm + d[0] * 0.2 * (x1 - x0), zm)
            out.append([tail, head])
            h = SIGN_HEAD
            out.append([(head[0] - d[0] * h - d[1] * h / 2, head[1] - d[1] * h + d[0] * h / 2), head,
                        (head[0] - d[0] * h + d[1] * h / 2, head[1] - d[1] * h - d[0] * h / 2)])
            if op.startswith("fold"):
                for k in range(1, 4):
                    x = x0 + (x1 - x0) * k / 4
                    out.append([(x, z0), (x, z0 + 0.15 * (z1 - z0))])
    return out


def _arc(cx, cy, r, a0, a1):
    return [(cx + r * math.cos(a), cy + r * math.sin(a))
            for a in np.linspace(math.radians(a0), math.radians(a1), ARC_STEPS + 1)]


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


SWING_DASH = (0.06, 0.04)          # m: (0.359) a dashed swing's dashes and gaps


def _dashed(line, dash=SWING_DASH[0], gap=SWING_DASH[1]):
    """(0.359) A polyline as its dashes: [polyline], each `dash` long along it, `gap` between them."""
    pts = np.asarray(line, dtype=float).reshape(-1, 2)
    lengths = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    run = np.concatenate(([0.0], np.cumsum(lengths)))
    total = float(run[-1])

    def at(s):
        k = min(max(int(np.searchsorted(run, s, side="right")) - 1, 0), len(lengths) - 1)
        return tuple(pts[k] + (pts[k + 1] - pts[k]) * ((s - run[k]) / max(float(lengths[k]), 1e-12)))

    out, s = [], 0.0
    while s < total - 1e-9:
        e = min(s + dash, total)
        out.append([at(s)] + [tuple(p) for p, r in zip(pts, run) if s < r < e] + [at(e)])
        s += dash + gap
    return out


def plan_pieces(design, width, height, y0, y1, faces=None):
    """(0.359) A door's pieces cut by a plan, each a piece of its own — not one mass —: [(role, ring [(x, y)…],
    material key)]: its lining's jambs («aro»), its casings («remate», the jambs': the head's is above the cut), its
    soleira («soleira») and, drawn closed (plan_open off), its leaves in the frame («folha»). In the door's own frame
    (x along the wall from its left jamb, y across it), as plan_symbol."""
    f = design.frame
    out = [("aro", _rect(0.0, y0, f, y1)[:-1], design.frame_material),
           ("aro", _rect(width - f, y0, width, y1)[:-1], design.frame_material)]
    out += [("remate", _rect(x0, ya, x1, yb)[:-1], design.frame_material)
            for x0, x1, _z0, _z1, ya, yb in casings(design, width, height, y0, y1) if x1 - x0 < width]
    if design.kind == "door":
        out += [("soleira", _rect(lo[0], lo[1], hi[0], hi[1])[:-1], design.stone_material)
                for lo, hi in stones(design, width, y0, y1, faces)]
        if not design.plan_open:
            lights, _bars = layout(design, width, height)
            for light in (lt for lt in lights if lt.row == 0 and door_leaf(lt.cell.operation)):
                ya, yb = _across(design, light, y0, y1)
                out.append(("folha", _rect(light.x0, ya, light.x1, yb)[:-1], design.panel_material))
    return out


def plan_symbol(design, width, height, y0, y1, faces=None):
    """A door's plan symbol: [polyline [(x, y)…]] — the jambs of its frame cut; each leaf of its bottom row open square
    to the wall on the side it opens to (+y), with its swing (a double-acting one's to both sides); a sliding one
    closed on its track with an arrow the way it opens; a folding one folded; a fixed light (or a window's kind of leaf)
    closed; (0.290) its soleira's outline. (0.359) Drawn closed (plan_open off): a swinging leaf closed in the frame,
    its swing the arc and a thin line where it opens to; the swing's lines dashed (swing_style "dashed")."""
    f = design.frame
    lines = [_rect(0.0, y0, f, y1), _rect(width - f, y0, width, y1)]
    lines += [_rect(x0, ya, x1, yb) for x0, x1, _z0, _z1, ya, yb in casings(design, width, height, y0, y1)
              if x1 - x0 < width]                                     # (the jambs' casings: the head's is above)
    if design.kind == "door":
        for lo, hi in stones(design, width, y0, y1, faces):
            lines.append(_rect(lo[0], lo[1], hi[0], hi[1]))
    if design.louvres in ("left", "right", "pair"):             # (0.295) its portadas, shut or turned back
        leaves, ya, yb = _louvre_leaves(design, width, y0, faces)
        t = yb - ya
        for x0, x1, hinge in leaves:
            if design.louvres_open:
                lines.append(_rect(min(2 * hinge - x0, 2 * hinge - x1), ya - t, max(2 * hinge - x0, 2 * hinge - x1),
                                   ya))
            else:
                lines.append(_rect(x0, ya, x1, yb))
    lights, _bars = layout(design, width, height)
    for light in (lt for lt in lights if lt.row == 0):
        op, x0, x1 = light.cell.operation, light.x0, light.x1
        w = x1 - x0
        ya, yb = _across(design, light, y0, y1)
        if not door_leaf(op):
            lines.append(_rect(x0, ya, x1, yb))
            continue
        hand = OPERATIONS[op].hand
        family = _family(op)
        if family == "swing":
            t = yb - ya
            swing = []
            if hand == "LEFT":
                swing.append([(x0, y1), (x0, y1 + w)] if not design.plan_open else None)
                lines.append(_rect(x0, y1, x0 + t, y1 + w) if design.plan_open else _rect(x0, ya, x1, yb))
                swing.append(_arc(x0, y1, w, 0.0, 90.0))
                if op == "swing_left":
                    swing.append(_arc(x0, y0, w, 0.0, -90.0))
            else:
                swing.append([(x1, y1), (x1, y1 + w)] if not design.plan_open else None)
                lines.append(_rect(x1 - t, y1, x1, y1 + w) if design.plan_open else _rect(x0, ya, x1, yb))
                swing.append(_arc(x1, y1, w, 180.0, 90.0))
                if op == "swing_right":
                    swing.append(_arc(x1, y0, w, 180.0, 270.0))
            for line in (s for s in swing if s is not None):
                lines += _dashed(line) if design.swing_style == "dashed" else [line]
        elif family == "slide":
            lines.append(_rect(x0, ya, x1, yb))
            y = y1 + ARROW
            tail, head = (x1 - 0.2 * w, x0 + 0.2 * w) if hand == "LEFT" else (x0 + 0.2 * w, x1 - 0.2 * w)
            back = ARROW / 2 if hand == "LEFT" else -ARROW / 2
            lines.append([(tail, y), (head, y)])
            lines.append([(head + back, y + ARROW / 3), (head, y), (head + back, y - ARROW / 3)])
        else:                                    # folding: four panels folded half open, gathered at its hand's side
            p = w / 4
            dx, dy = p * math.cos(math.radians(60)), p * math.sin(math.radians(60))
            start, step = (x0, 1.0) if hand == "LEFT" else (x1, -1.0)
            lines.append([(start + step * dx * k, y1 + (dy if k % 2 else 0.0)) for k in range(5)])
    return lines


# ------------------------------------------------------------ editing (0.289: the generator's window)

def _rows_of(*rows):
    return tuple(r if isinstance(r, Row) else Row(tuple(_cell(c, "glass") for c in r)) for r in rows)


# Ready-made layouts, the generator's library: (key, Portuguese, English, rows from the bottom up). Choosing one
# keeps the door's / window's sizes of its frame and leaves and its materials.
MODELS = {
    "window": (
        ("fixo", "Fixo", "Fixed light", _rows_of(("fixed",))),
        ("batente_1", "De batente, 1 folha", "Side-hung, 1 leaf", _rows_of(("left",))),
        ("batente_2", "De batente, 2 folhas", "Side-hung, 2 leaves", _rows_of(("left", "right"))),
        ("oscilo_1", "Oscilobatente, 1 folha", "Tilt and turn, 1 leaf", _rows_of(("tilt_left",))),
        ("oscilo_2", "Batente + oscilobatente", "Side-hung + tilt and turn", _rows_of(("left", "tilt_right"))),
        ("correr_2", "De correr, 2 folhas", "Sliding, 2 leaves", _rows_of(("slide_right", "slide_left"))),
        ("fixo_batente", "Fixo + batente", "Fixed + side-hung", _rows_of(("fixed", "right"))),
        ("basculante", "Basculante", "Bottom-hung", _rows_of(("bottom",))),
        ("projetante", "Projetante", "Top-hung", _rows_of(("top",))),
        ("pivotante", "Pivotante horizontal", "Horizontal pivot", _rows_of(("pivot_h",))),
        ("guilhotina", "Guilhotina", "Sash window", _rows_of(("slide_up",), ("slide_up",))),
        ("batente_bandeira", "2 folhas + bandeira basculante", "2 leaves + bottom-hung fanlight",
         _rows_of(("left", "right"), Row((Cell("bottom"),), 0.40))),
    ),
    "door": (
        ("cega_1", "1 folha cega", "1 solid leaf", (Row((Cell("left", "panel"),)),)),
        ("vidro_1", "1 folha envidraçada", "1 glazed leaf", (Row((Cell("left", "glass"),)),)),
        ("cega_2", "2 folhas cegas", "2 solid leaves", (Row((Cell("left", "panel"), Cell("right", "panel"))),)),
        ("vidro_2", "2 folhas envidraçadas", "2 glazed leaves", _rows_of(("left", "right"))),
        ("bandeira", "1 folha + bandeira", "1 leaf + fanlight",
         (Row((Cell("left", "panel"),)), Row((Cell("fixed", "glass"),), 0.50))),
        ("lateral", "1 folha + fixo lateral", "1 leaf + side light",
         (Row((Cell("left", "panel"), Cell("fixed", "glass", 0.40))),)),
        ("correr_1", "De correr, 1 folha", "Sliding, 1 leaf", (Row((Cell("slide_left", "panel"),)),)),
        ("correr_2", "De correr, 2 folhas", "Sliding, 2 leaves",
         (Row((Cell("slide_left", "panel"), Cell("slide_right", "panel"))),)),
        ("vaivem_1", "Vaivém, 1 folha", "Double-acting, 1 leaf", (Row((Cell("swing_left", "panel"),)),)),
        ("vaivem_2", "Vaivém, 2 folhas", "Double-acting, 2 leaves",
         (Row((Cell("swing_left", "panel"), Cell("swing_right", "panel"))),)),
        ("harmonio", "Harmónio", "Folding", (Row((Cell("fold_left", "panel"),)),)),
    ),
}


def model(kind, key):
    """The rows of a ready-made layout of the library (MODELS)."""
    return next(rows for k, _pt, _en, rows in MODELS[kind] if k == key)


def matching_model(design):
    """The library's layout a design has (its cells' ways of opening and fills, its rows' sizes), or None."""
    return next((k for k, _pt, _en, rows in MODELS[design.kind] if rows == design.rows), None)


def _with_row(design, i, row):
    return replace(design, rows=design.rows[:i] + (row,) + design.rows[i + 1:])


def set_cell(design, i, j, **changes):
    """The cell j of row i changed (operation, fill, width)."""
    row = design.rows[i]
    return _with_row(design, i, replace(row, cells=row.cells[:j] + (replace(row.cells[j], **changes),)
                                        + row.cells[j + 1:]))


def set_row(design, i, height):
    """Row i `height` high (0: a share of what the others leave)."""
    return _with_row(design, i, replace(design.rows[i], height=max(float(height), 0.0)))


def split(design, i, j):
    """The cell j of row i in two side by side, each half its width — the new one, on its right, fixed and of the
    same fill."""
    row = design.rows[i]
    cell = row.cells[j]
    half = cell.width / 2
    cells = row.cells[:j] + (replace(cell, width=half), Cell("fixed", cell.fill, half)) + row.cells[j + 1:]
    return _with_row(design, i, replace(row, cells=cells))


def join(design, i, j):
    """The cell j of row i and the one on its right made one (opening as the left one did; their widths added, or
    shared if either shared)."""
    row = design.rows[i]
    if j + 1 >= len(row.cells):
        return design
    a, b = row.cells[j], row.cells[j + 1]
    merged = replace(a, width=a.width + b.width if a.width > 0 and b.width > 0 else 0.0)
    return _with_row(design, i, replace(row, cells=row.cells[:j] + (merged,) + row.cells[j + 2:]))


def add_row(design, i, height=0.40):
    """A row over row i: one fixed glazed light `height` high (a fanlight)."""
    rows = design.rows[:i + 1] + (Row((Cell("fixed", "glass"),), float(height)),) + design.rows[i + 1:]
    return replace(design, rows=rows)


def remove_row(design, i):
    """Row i taken away (not the last one left)."""
    if len(design.rows) < 2:
        return design
    return replace(design, rows=design.rows[:i] + design.rows[i + 1:])


MIN_LIGHT = 0.05                   # m: the narrowest light, and a glazed leaf's room for its glass


def problems(design, width, height):
    """What is wrong with a design at this size: [(i18n key, values)] — a frame wider than half the door / window,
    a light too narrow or too low (under 5 cm; a glazed leaf's under its two stiles and 5 cm), sizes that do not fit."""
    out = []
    f = design.frame
    if f <= 0 or 2 * f >= min(width, height) or design.mullion <= 0 or design.sash <= 0 or design.sash_depth <= 0 \
            or design.glass <= 0 or design.depth < 0:
        out.append(("joinery.err_profiles", {}))
        return out
    # (0.306) by columns: the columns' widths along the width, each column's cells' heights up the height
    across, along = (width, height - _base(design) - _top(design)) if design.columns else (height, width)
    given_h = sum(r.height for r in design.rows)
    if given_h > across + 1e-9 or (all(r.height > 0 for r in design.rows) and abs(given_h - across) > 1e-6):
        out.append(("joinery.err_widths" if design.columns else "joinery.err_heights", {}))
    for r in design.rows:
        given_w = sum(c.width for c in r.cells)
        if given_w > along + 1e-9 or (all(c.width > 0 for c in r.cells) and abs(given_w - along) > 1e-6):
            out.append(("joinery.err_heights" if design.columns else "joinery.err_widths", {}))
            break
    lights, _bars = layout(design, width, height)
    for lt in lights:
        need = MIN_LIGHT + (2 * design.sash if lt.cell.operation != "fixed" and lt.cell.fill in FRAMED else 0.0)
        if lt.x1 - lt.x0 < need - 1e-9 or lt.z1 - lt.z0 < need - 1e-9:
            out.append(("joinery.err_small", {"row": lt.row + 1, "cell": lt.index + 1}))
    if design.louvres in ("left", "right", "pair"):             # (0.295) portadas: not with an estore; room for them
        if design.shutter > 0:
            out.append(("joinery.err_louvres_shutter", {}))
        stile, rail, head, _t = LOUVRE_LEAF
        leaf = width / 2 if design.louvres == "pair" else width
        bottom = _base(design) if design.kind == "window" else max(design.stone, 0.0)
        if leaf - 2 * stile < MIN_LIGHT - 1e-9 or height - _top(design) - bottom - rail - head < MIN_LIGHT - 1e-9:
            out.append(("joinery.err_louvres_small", {}))
    if design.arch:                                 # (0.294) an arch: it fits; under it, (0.296) leaves that can open
        rise = arch_rise(design, width)              # there (not hung from their top, sliding nor folding)
        if (design.arch == "segmental" and rise > width / 2 + 1e-9) or height - rise < _base(design) + 0.3:
            out.append(("joinery.err_arch", {}))
        else:
            for lt in lights:
                if lt.cell.operation in ARCH_REFUSED and in_arch(design, width, height, lt):
                    out.append(("joinery.err_arch_leaf", {"row": lt.row + 1, "cell": lt.index + 1}))
    return out


# ------------------------------------------------------------ IFC's names

_DOOR_SINGLE = {"left": "SINGLE_SWING_LEFT", "right": "SINGLE_SWING_RIGHT", "swing_left": "DOUBLE_SWING_LEFT",
                "swing_right": "DOUBLE_SWING_RIGHT", "slide_left": "SLIDING_TO_LEFT", "slide_right": "SLIDING_TO_RIGHT",
                "fold_left": "FOLDING_TO_LEFT", "fold_right": "FOLDING_TO_RIGHT"}
_DOOR_PAIRS = {("left", "right"): "DOUBLE_DOOR_SINGLE_SWING", ("swing_left", "swing_right"): "DOUBLE_DOOR_DOUBLE_SWING",
               ("slide_left", "slide_right"): "DOUBLE_DOOR_SLIDING", ("fold_left", "fold_right"): "DOUBLE_DOOR_FOLDING",
               ("left", "fixed"): "SWING_FIXED_LEFT", ("fixed", "right"): "SWING_FIXED_RIGHT"}
_WINDOW_ROWS = {(1,): "SINGLE_PANEL", (2,): "DOUBLE_PANEL_VERTICAL", (1, 1): "DOUBLE_PANEL_HORIZONTAL",
                (3,): "TRIPLE_PANEL_VERTICAL", (1, 1, 1): "TRIPLE_PANEL_HORIZONTAL", (2, 1): "TRIPLE_PANEL_TOP",
                (1, 2): "TRIPLE_PANEL_BOTTOM"}
# the panels' positions (IfcWindowPanelPositionEnum) in the order of the cells, the rows from the bottom up
_WINDOW_POSITIONS = {"SINGLE_PANEL": ("MIDDLE",), "DOUBLE_PANEL_VERTICAL": ("LEFT", "RIGHT"),
                     "DOUBLE_PANEL_HORIZONTAL": ("BOTTOM", "TOP"), "TRIPLE_PANEL_VERTICAL": ("LEFT", "MIDDLE", "RIGHT"),
                     "TRIPLE_PANEL_HORIZONTAL": ("BOTTOM", "MIDDLE", "TOP"), "TRIPLE_PANEL_TOP": ("LEFT", "RIGHT", "TOP"),
                     "TRIPLE_PANEL_BOTTOM": ("BOTTOM", "LEFT", "RIGHT")}
_DOOR_POSITIONS = {1: ("MIDDLE",), 2: ("LEFT", "RIGHT"), 3: ("LEFT", "MIDDLE", "RIGHT")}


def door_operation(design):
    """(IfcDoorTypeOperationEnum, its UserDefinedOperationType or None) of a door's design — from its leaves (its
    bottom row): one leaf, two (double doors, a leaf and a fixed light); any other USERDEFINED, its cells' ways."""
    ops = tuple(c.operation for c in bottom_cells(design))
    found = _DOOR_SINGLE.get(ops[0]) if len(ops) == 1 else _DOOR_PAIRS.get(ops)
    return (found, None) if found else ("USERDEFINED", "+".join(ops))


def window_partitioning(design):
    """(IfcWindowTypePartitioningEnum, its UserDefinedPartitioningType or None) of a window's design: from how many
    cells each row has; any other USERDEFINED ("2×2"…)."""
    counts = tuple(len(r.cells) for r in design.rows)
    if design.columns:                  # (0.306) by columns: a single column's cells as rows of one, or one row
        cells = [len(r.cells) for r in design.rows]
        if len(cells) > 1 and max(cells) > 1:
            return "USERDEFINED", "+".join(str(c) for c in cells)
        counts = (1,) * cells[0] if len(cells) == 1 else (len(cells),)
    found = _WINDOW_ROWS.get(counts)
    return (found, None) if found else ("USERDEFINED", "×".join(str(c) for c in counts))


def hand(design):
    """A door's hand — "LEFT" / "RIGHT" — as its IFC operation says it (…_LEFT / …_RIGHT); None for no one side."""
    operation = door_operation(design)[0]
    if operation.startswith("DOUBLE_DOOR"):
        return None
    return "RIGHT" if operation.endswith("RIGHT") else "LEFT" if operation.endswith("LEFT") else None


def panels(design, width, height):
    """The panels IFC's panel properties describe, in order: [(cell, position, its share of the clear width)] — a
    door's leaves (its bottom row), a window's lights; [] where IFC's names stop (more than three)."""
    lights, _bars = layout(design, width, height)
    clear = max(width - 2 * design.frame, 1e-9)
    if design.kind == "door":
        row = [lt for lt in lights if lt.row == 0]
        positions = _DOOR_POSITIONS.get(len(row), ())
        return [(lt.cell, p, min(max((lt.x1 - lt.x0) / clear, 0.0), 1.0)) for lt, p in zip(row, positions)]
    positions = _WINDOW_POSITIONS.get(window_partitioning(design)[0], ())
    return [(lt.cell, p, min(max((lt.x1 - lt.x0) / clear, 0.0), 1.0)) for lt, p in zip(lights, positions)]


def bars_offsets(design, width, height):
    """Where the transoms are (each its middle's height over the height) and the mullions (each its middle along,
    over the width, of the row with most of them): IFC's lining offsets, ratios; and whether there are any. (0.306) By
    columns: the mullions between the columns, the transoms of the column with most of them."""
    if design.columns:
        cols = design.rows
        widths = _sizes([c.height for c in cols], width)
        mullions = [sum(widths[:j + 1]) / width for j in range(len(widths) - 1)
                    if not (len(cols[j].cells) == len(cols[j + 1].cells) == 1
                            and meets(cols[j].cells[0].operation, cols[j + 1].cells[0].operation))]
        best = max(range(len(design.rows)), key=lambda j: len(design.rows[j].cells))
        cells = design.rows[best].cells
        heights = column_heights(design, height)[best]
        top = height - _top(design)
        transoms = [(top - sum(heights[:i + 1])) / height for i in range(len(heights) - 1)
                    if not cells[i].operation == cells[i + 1].operation == "slide_up"]
        return sorted(transoms), mullions
    heights = _sizes([r.height for r in design.rows], height)
    transoms = [sum(heights[:i + 1]) / height for i in range(len(heights) - 1)
                if not _rows_meet(design.rows[i], design.rows[i + 1])]
    best = max(design.rows, key=lambda r: len(r.cells))
    widths = _sizes([c.width for c in best.cells], width)
    mullions = [sum(widths[:j + 1]) / width for j in range(len(widths) - 1)
                if not meets(best.cells[j].operation, best.cells[j + 1].operation)]
    return transoms, mullions


_IFC_WINDOW_OPS = {"SIDEHUNGLEFTHAND": "left", "SIDEHUNGRIGHTHAND": "right", "TILTANDTURNLEFTHAND": "tilt_left",
                   "TILTANDTURNRIGHTHAND": "tilt_right", "TOPHUNG": "top", "BOTTOMHUNG": "bottom",
                   "PIVOTHORIZONTAL": "pivot_h", "PIVOTVERTICAL": "pivot_v", "SLIDINGHORIZONTAL": "slide_right",
                   "SLIDINGVERTICAL": "slide_up"}
_DOOR_FROM_IFC = {v: (k,) for k, v in _DOOR_SINGLE.items()}
_DOOR_FROM_IFC.update({v: k for k, v in _DOOR_PAIRS.items()})
_ROWS_FROM_IFC = {v: k for k, v in _WINDOW_ROWS.items()}


def standard(kind, operation, transom=0.0, depth=None, window_ops=()):
    """A design made from IFC's description of a door / window that has none of its own (one from before 0.288, or
    another program's): a door's leaves from its OperationType (one left-hand leaf for the others), with its fanlight;
    a window's lights from its PartitioningType, fixed — or opening as its panel properties say (window_ops, IFC's
    names in order)."""
    if kind == "door":
        design = door(*_DOOR_FROM_IFC.get(operation, ("left",)), transom=transom)
    else:
        counts = _ROWS_FROM_IFC.get(operation, (1,))
        ops = [_IFC_WINDOW_OPS.get(o, "fixed") for o in window_ops] if len(window_ops) == sum(counts) else \
            ["fixed"] * sum(counts)
        rows, k = [], 0
        for n in counts:
            rows.append(tuple(ops[k:k + n]))
            k += n
        design = window(*rows)
    return replace(design, depth=float(depth)) if depth else design


# ------------------------------------------------------------ kept in the IFC (the type's «Desenho»)

_SCALARS = [fl.name for fl in fields(Design) if fl.name not in ("kind", "rows")]


def to_json(design):
    """The design as text (kept in its type's parameters)."""
    data = {"v": 1, "kind": design.kind,
            "rows": [{"h": r.height, "cells": [{"op": c.operation, "fill": c.fill, "w": c.width} for c in r.cells]}
                     for r in design.rows]}
    data.update({name: getattr(design, name) for name in _SCALARS})
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def from_json(text):
    """The design kept as text (to_json); ValueError if it is not one."""
    try:
        data = json.loads(text)
        rows = tuple(Row(tuple(Cell(c["op"] if c["op"] in OPERATIONS else "fixed",
                                    c.get("fill") if c.get("fill") in FILLS else "glass", max(float(c.get("w", 0)), 0.0))
                               for c in r["cells"]), max(float(r.get("h", 0)), 0.0)) for r in data["rows"])
        if not rows or any(not r.cells for r in rows):
            raise ValueError("no cells")
        values = {}
        for name in _SCALARS:
            if name in data:
                default = getattr(Design, name)
                values[name] = type(default)(data[name])
        design = Design(kind=data.get("kind", "window"), rows=rows, **values)
    except (TypeError, KeyError, AttributeError, json.JSONDecodeError) as exc:
        raise ValueError(str(exc)) from exc
    if design.kind not in ("door", "window"):
        raise ValueError(design.kind)
    return design
