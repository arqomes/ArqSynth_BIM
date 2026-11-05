"""(0.307) The Caixilho Studio's model — the owner's prototype (2026-10-29): a door's or window's opening by columns, in
millimetres — each column its width and its panels from the top down, each panel its height, how it opens and what
fills it —, its kind, its reference, its system and the colour of its profiles, its frame (aro) and its sill; and what
the studio does to it: mullions and transoms put in where they are dropped, moved (the transoms at one height moving
together when they are linked), taken out; its sizes typed, with sums ("2400/3"); its columns made equal, each column's
panels too — once, or kept so as parameters of its type (0.309: whatever is changed after); a panel split,
its way of opening and fill copied along its row; its whole size changed. It is made into a joinery design by columns
(core/joinery: the mullions its whole height) and read back from one — a design by rows too, made a grid.

Pure data, no Qt: the studio's window (ui/caixilho_studio) draws it and calls these."""

import ast
import copy
import operator
from dataclasses import dataclass, field, fields, replace

from . import joinery

MIN = 200                       # mm: the narrowest column, the lowest panel
STEP = 10                       # mm: what a drag or an arrow key moves by (Shift: 100)

# the ways a panel opens, as the studio's panel shows them: the prototype's eight first
WINDOW_OPS = ("fixed", "left", "right", "bottom", "top", "tilt_left", "slide_right", "pivot_v",
              "tilt_right", "slide_left", "slide_up", "pivot_h")
DOOR_LEAF_OPS = ("fixed", "left", "right", "slide_right", "slide_left", "swing_left", "swing_right", "fold_left",
                 "fold_right")
FILLS = ("glass", "frosted", "panel", "wood", "louvre")
SYSTEMS = ("aluminio", "pvc", "madeira", "aco")
COLOURS = ("grafite", "branco", "bronze", "natural")
COLOUR_HEX = {"grafite": "#2f3337", "branco": "#ecebe6", "bronze": "#6b4f3a", "natural": "#9a6b42"}

# each way's sign in a 100 × 100 panel, seen from outside (the lines meet at its hinges): (solid, dashed, solid)
SIGNS = {
    "fixed": ("", "", ""),
    "left": ("100,0 0,50 100,100", "", ""),
    "right": ("0,0 100,50 0,100", "", ""),
    "bottom": ("0,0 50,100 100,0", "", ""),
    "top": ("0,100 50,0 100,100", "", ""),
    "tilt_left": ("100,0 0,50 100,100", "0,0 50,100 100,0", ""),
    "tilt_right": ("0,0 100,50 0,100", "0,0 50,100 100,0", ""),
    "slide_right": ("12,50 88,50", "", "74,38 88,50 74,62"),
    "slide_left": ("12,50 88,50", "", "26,38 12,50 26,62"),
    "slide_up": ("50,88 50,12", "", "38,26 50,12 62,26"),
    "pivot_v": ("50,12 84,50 50,88 16,50 50,12", "50,0 50,100", ""),
    "pivot_h": ("50,12 84,50 50,88 16,50 50,12", "0,50 100,50", ""),
    "swing_left": ("100,0 0,50 100,100", "100,14 14,50 100,86", ""),
    "swing_right": ("0,0 100,50 0,100", "0,14 86,50 0,86", ""),
    "fold_left": ("0,12 25,88 50,12 75,88 100,12", "", "14,40 2,50 14,60"),
    "fold_right": ("0,12 25,88 50,12 75,88 100,12", "", "86,40 98,50 86,60"),
}


@dataclass
class Panel:
    h: int                      # mm, from the top of its column down
    op: str = "fixed"           # core/joinery.OPERATIONS
    fill: str = "glass"         # FILLS


@dataclass
class Column:
    w: int
    panels: list = field(default_factory=list)


@dataclass
class Opening:
    """A door or window as the studio has it (sizes in mm)."""
    name: str
    kind: str                   # "window" | "door"
    W: int
    H: int
    sill: int
    aro: int
    system: str
    colour: str                 # COLOURS, or "" (its profile's material none of them)
    cols: list
    base: object = None         # the joinery design it came from: what the studio does not show is kept from it
    key: str = None             # the door / window type it came from (an OpeningSpec's key), None: a new one
    material: str = ""          # its profiles' material when not a system in a colour of the studio's (kept as it was
    #                             until a system or colour is chosen)
    eq_cols: bool = False       # (0.309) its columns kept as wide as each other (a parameter: kept with its type)
    eq_rows: bool = False       # (0.309) each column's panels kept as high as each other


def cum(sizes):
    out = [0]
    for s in sizes:
        out.append(out[-1] + s)
    return out


def widths(op):
    return [c.w for c in op.cols]


def heights(col):
    return [p.h for p in col.panels]


def clone(op):
    return copy.deepcopy(op)


# ------------------------------------------------------------ sums typed into a size

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def evaluate(text):
    """A size typed, with sums allowed — "2400/3", "1200 + 2*150" (a comma for the decimal point) —, or None."""
    text = str(text).replace(",", ".").strip()
    if not text or any(ch not in "0123456789.+-*/() " for ch in text):
        return None

    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            v = walk(node.operand)
            return -v if isinstance(node.op, ast.USub) else v
        raise ValueError(text)

    try:
        value = walk(ast.parse(text, mode="eval"))
    except (SyntaxError, ValueError, ZeroDivisionError):
        return None
    return value if value == value and abs(value) != float("inf") else None


# ------------------------------------------------------------ mullions and transoms

def boundary_cols(op, c, y, linked):
    """The transoms at height y (from the top) that move with column c's: [(column, the panel above it)]."""
    out = []
    for k, col in enumerate(op.cols):
        if k != c and not linked:
            continue
        cy = cum(heights(col))
        for b in range(1, len(cy) - 1):
            if abs(cy[b] - y) < 1:
                out.append((k, b - 1))
                break
    return out


def move_boundary(op, c, old_y, new_y, linked, snap=0.0):
    """A transom of column c from old_y to new_y (mm from the top) — and those linked to it —, kept MIN from the
    transoms either side; within `snap` mm of the middle of its two panels (one column only), on it. False: it cannot."""
    found = boundary_cols(op, c, old_y, linked)
    if not found:
        return False
    lo, hi = -float("inf"), float("inf")
    for k, b in found:
        cy = cum(heights(op.cols[k]))
        lo, hi = max(lo, cy[b] + MIN), min(hi, cy[b + 2] - MIN)
    if lo > hi:
        return False
    op.eq_rows = False                  # (0.309) a panel made its own height: its column's no longer kept equal
    if len(found) == 1:
        k, b = found[0]
        cy = cum(heights(op.cols[k]))
        mid = (cy[b] + cy[b + 2]) / 2
        if abs(new_y - mid) <= snap:
            new_y = round(mid)
    new_y = min(max(new_y, lo), hi)
    for k, b in found:
        panels = op.cols[k].panels
        cy = cum(heights(op.cols[k]))
        panels[b].h = int(round(new_y - cy[b]))
        panels[b + 1].h = int(round(cy[b + 2] - new_y))
    return True


def move_mullion(op, i, new_w, snap=0.0):
    """The mullion after column i: column i `new_w` wide, the next one what is left of the two (each MIN at least);
    within `snap` mm of their middle, on it."""
    total = op.cols[i].w + op.cols[i + 1].w
    if abs(new_w - total / 2) <= snap:
        new_w = round(total / 2)
    new_w = int(round(min(max(new_w, MIN), total - MIN)))
    op.cols[i].w, op.cols[i + 1].w = new_w, total - new_w
    op.eq_cols = False                  # (0.309) a column made its own width: the columns no longer kept equal


def insert_col(op, x):
    """A mullion put in at x (mm from the left): the column there split, both halves as it was. False: too near."""
    cw = cum(widths(op))
    for k, col in enumerate(op.cols):
        if cw[k] < x < cw[k + 1]:
            left, right = x - cw[k], col.w - (x - cw[k])
            if left < MIN or right < MIN:
                return False
            new = copy.deepcopy(col)
            new.w, col.w = int(round(right)), int(round(left))
            op.cols.insert(k + 1, new)
            return True
    return False


def insert_row(op, y, only_x=None):
    """A transom put in at y (mm from the top): in every column (linked), or only in the one at only_x. False: none."""
    cw = cum(widths(op))
    done = False
    for k, col in enumerate(op.cols):
        if only_x is not None and not cw[k] <= only_x <= cw[k + 1]:
            continue
        cy = cum(heights(col))
        for r, panel in enumerate(col.panels):
            if cy[r] < y < cy[r + 1]:
                top, bottom = y - cy[r], panel.h - (y - cy[r])
                if top >= MIN and bottom >= MIN:
                    new = copy.deepcopy(panel)
                    new.h, panel.h = int(round(bottom)), int(round(top))
                    col.panels.insert(r + 1, new)
                    done = True
                break
    return done


def merge_col(op, i):
    """The mullion after column i taken out: the two columns one (the first's panels)."""
    op.cols[i].w += op.cols[i + 1].w
    del op.cols[i + 1]


def merge_row(op, c, b, linked):
    """The transom under panel b of column c taken out (and those linked to it): the two panels one, the larger's way
    of opening and fill kept."""
    y = cum(heights(op.cols[c]))[b + 1]
    for k, bb in boundary_cols(op, c, y, linked):
        panels = op.cols[k].panels
        keep = panels[bb] if panels[bb].h >= panels[bb + 1].h else panels[bb + 1]
        panels[bb:bb + 2] = [Panel(panels[bb].h + panels[bb + 1].h, keep.op, keep.fill)]


def equalize(op):
    """Every column as wide (what does not divide going to the last)."""
    n = len(op.cols)
    each = op.W // n
    for i, col in enumerate(op.cols):
        col.w = each if i < n - 1 else op.W - each * (n - 1)


def equalize_rows(op):
    """(0.309) Each column's panels as high as each other (what does not divide going to the bottom one)."""
    for col in op.cols:
        n = len(col.panels)
        each = op.H // n
        for r, panel in enumerate(col.panels):
            panel.h = each if r < n - 1 else op.H - each * (n - 1)


def keep_equal(op):
    """(0.309) Its parameters kept: its columns made equal if they are to be, each column's panels too (after any
    change — a mullion or transom put in or taken out, its whole size changed)."""
    if op.eq_cols:
        equalize(op)
    if op.eq_rows:
        equalize_rows(op)


def set_equal(op, cols=None, rows=None):
    """(0.309) Its parameters «columns equal» / «panels equal» turned on or off (None: as they are), kept at once."""
    if cols is not None:
        op.eq_cols = cols
    if rows is not None:
        op.eq_rows = rows
    keep_equal(op)


def copy_along_row(op, c, r):
    """The way of opening and fill of panel r of column c given to the panels of the other columns at its height."""
    src = op.cols[c].panels[r]
    y = cum(heights(op.cols[c]))[r]
    for col in op.cols:
        cy = cum(heights(col))
        for k, panel in enumerate(col.panels):
            if abs(cy[k] - y) < 1:
                panel.op, panel.fill = src.op, src.fill


def split_v(op, c):
    """Column c split down its middle."""
    return insert_col(op, cum(widths(op))[c] + op.cols[c].w // 2)


def split_h(op, c, r):
    """Panel r of column c split across its middle (that column only)."""
    cy = cum(heights(op.cols[c]))
    return insert_row(op, cy[r] + op.cols[c].panels[r].h // 2, cum(widths(op))[c] + 1)


def resize(op, W=None, H=None, from_left=False):
    """The whole opening W wide / H high, from a drag of its edges: the last column (the first, seen from inside) and
    each column's bottom panel take what changes, kept MIN at least."""
    if W is not None:
        i = 0 if from_left else len(op.cols) - 1
        diff = max(int(round(W)) - op.W, MIN - op.cols[i].w)
        op.cols[i].w += diff
        op.W += diff
    if H is not None:
        dh = int(round(H)) - op.H
        for col in op.cols:
            dh = max(dh, MIN - col.panels[-1].h)
        for col in op.cols:
            col.panels[-1].h += dh
        op.H += dh


def set_size(op, key, text, linked):
    """A size typed (mm, sums allowed): "W", "H", "aro", "sill", "c<i>" a column's width, "r<c>_<b>" a panel's height.
    False: not a number."""
    v = evaluate(text)
    if v is None:
        return False
    v = int(round(v))
    n = len(op.cols)
    if key == "W":
        new = max(v, n * MIN)
        acc = 0
        for i, col in enumerate(op.cols[:-1]):
            col.w = max(MIN, int(round(col.w * new / op.W)))
            acc += col.w
        op.cols[-1].w = new - acc
        op.W = new
    elif key == "H":
        most = max(len(c.panels) for c in op.cols)
        new = max(v, most * MIN)
        for col in op.cols:
            acc = 0
            for panel in col.panels[:-1]:
                panel.h = max(MIN, int(round(panel.h * new / op.H)))
                acc += panel.h
            col.panels[-1].h = new - acc
        op.H = new
    elif key == "aro":
        op.aro = min(max(v, 30), 160)
    elif key == "sill":
        op.sill = min(max(v, 0), 3000)
    elif key.startswith("c"):
        i = int(key[1:])
        if n < 2:
            return set_size(op, "W", text, linked)
        j = i + 1 if i < n - 1 else i - 1
        total = op.cols[i].w + op.cols[j].w
        new = min(max(v, MIN), total - MIN)
        op.cols[i].w, op.cols[j].w = new, total - new
        op.eq_cols = False
    elif key.startswith("r"):
        c, b = (int(s) for s in key[1:].split("_"))
        panels = op.cols[c].panels
        if len(panels) < 2:
            return set_size(op, "H", text, linked)
        cy = cum(heights(op.cols[c]))
        if b < len(panels) - 1:
            move_boundary(op, c, cy[b + 1], cy[b] + v, linked)
        else:
            move_boundary(op, c, cy[b], cy[b + 1] - v, linked)
    return True


def ops_for(op, c, r):
    """The ways panel r of column c can open: a door's leaves (its bottom panels) as doors open; any other as windows."""
    return DOOR_LEAF_OPS if op.kind == "door" and r == len(op.cols[c].panels) - 1 else WINDOW_OPS


def set_kind(op, kind):
    """A window made a door or the other way: its sill (a door's none), its panels' ways of opening as the new kind
    allows, the profiles' sizes the new kind's own."""
    if kind == op.kind:
        return
    op.kind = kind
    op.sill = 0 if kind == "door" else (op.sill or 900)
    op.base = None
    for c, col in enumerate(op.cols):
        for r, panel in enumerate(col.panels):
            if panel.op not in ops_for(op, c, r):
                panel.op = "fixed"


# ------------------------------------------------------------ what it is

def profile_material(op):
    """The material of its profiles: its system in its colour ("aluminio_grafite"); with no colour, the one it had (if
    it is of that system or none of the studio's), else the plain system."""
    if op.colour:
        return "{}_{}".format(op.system, op.colour)
    if op.material and _profile_of(op.material)[0] in (None, op.system):
        return op.material
    return op.system


def to_design(op):
    """The joinery design by columns of the studio's opening (core/joinery), keeping from the design it came from what
    the studio does not show (its depth, its leaves' sizes, its sill stone, its casings, its arch…). Each column's
    bottom panel and the last column share what the others leave (the frame's own room under a sill stone). (0.309)
    Its columns kept equal: all of them 0 wide (sharing the width equally, whatever it is made); its panels kept equal:
    all of them 0 high."""
    base = op.base if op.base is not None and op.base.kind == op.kind else \
        (joinery.door() if op.kind == "door" else joinery.window())
    material = profile_material(op)
    cols = []
    for k, col in enumerate(op.cols):
        cells = tuple(joinery.Cell(p.op, p.fill, 0.0 if op.eq_rows or r == len(col.panels) - 1 else p.h / 1000.0)
                      for r, p in enumerate(col.panels))
        cols.append(joinery.Row(cells, 0.0 if op.eq_cols or k == len(op.cols) - 1 else col.w / 1000.0))
    return replace(base, kind=op.kind, rows=tuple(cols), columns=True, frame=op.aro / 1000.0,
                   frame_material=material, panel_material=material)


def from_design(design, width, height, sill=0.0, name="", key=None):
    """The studio's opening of a joinery design (`width` × `height` m): by columns as it is; by rows made a grid — the
    columns where any row has a mullion, each row's cells cut at them (a cell across two columns in both: a leaf only
    in the first, the others fixed)."""
    import math
    W, H = int(round(width * 1000)), int(round(height * 1000))
    system, colour = _profile_of(design.frame_material)
    lights_room = height - joinery._base(design) - joinery._top(design)
    if design.columns:
        ws = joinery._sizes([c.height for c in design.rows], width)
        cols = []
        for col, hs in zip(design.rows, joinery.column_heights(design, height)):
            mm = _fit([h * 1000 for h in hs], H)
            cols.append(Column(0, [Panel(h, c.operation, c.fill) for c, h in zip(col.cells, mm)]))
        for c, w in zip(cols, _fit([w * 1000 for w in ws], W)):
            c.w = w
    else:
        rows = list(reversed(design.rows))                       # (from the top down)
        hs = _fit([h * 1000 for h in reversed(joinery._sizes([r.height for r in design.rows], lights_room))], H)
        edges = set()
        bounds = []
        for row in rows:
            ws = joinery._sizes([c.width for c in row.cells], width)
            xs = [0.0]
            for w in ws:
                xs.append(xs[-1] + w)
            bounds.append(xs)
            edges.update(round(x * 1000) for x in xs[1:-1])
        cuts = [0] + sorted(edges) + [W]
        cols = []
        for a, b in zip(cuts, cuts[1:]):
            panels = []
            for row, xs, h in zip(rows, bounds, hs):
                mid = (a + b) / 2 / 1000.0
                j = next(i for i in range(len(row.cells)) if xs[i] <= mid <= xs[i + 1] + 1e-9)
                cell = row.cells[j]
                first = math.isclose(xs[j] * 1000, a, abs_tol=1) or a == 0
                panels.append(Panel(h, cell.operation if first else "fixed", cell.fill))
            cols.append(Column(b - a, panels))
    kind = design.kind
    op = Opening(name or ("P01" if kind == "door" else "J01"), kind, W, H,
                 0 if kind == "door" else int(round(sill * 1000)), int(round(design.frame * 1000)), system or "aluminio",
                 colour or "", cols, base=design, key=key, material=design.frame_material)
    if design.columns:                  # (0.309) its parameters: every column, every panel sharing equally (0)
        op.eq_cols = len(design.rows) > 1 and all(c.height <= 0 for c in design.rows)
        op.eq_rows = any(len(c.cells) > 1 for c in design.rows) and \
            all(cell.width <= 0 for c in design.rows for cell in c.cells)
        keep_equal(op)
    return op


def _fit(sizes, total):
    """Sizes in mm rounded to whole millimetres, their sum `total` (the last takes the rounding)."""
    out = [int(round(s)) for s in sizes]
    out[-1] += total - sum(out)
    return out


def _profile_of(material):
    for system in SYSTEMS:
        if material == system:
            return system, ""
        for colour in COLOURS:
            if material == "{}_{}".format(system, colour):
                return system, colour
    return None, ""


def ifc_class(op):
    """«IfcWindow · DOUBLE_PANEL_VERTICAL» / «IfcDoor · SINGLE_SWING_LEFT»: what the type will be in IFC."""
    design = to_design(op)
    if op.kind == "door":
        return "IfcDoor · " + joinery.door_operation(design)[0]
    return "IfcWindow · " + joinery.window_partitioning(design)[0]


def metrics(op):
    """{"area": m², "glass": m² of glass seen in elevation, "open": m² of the panels that open}."""
    area = op.W * op.H / 1e6
    glass = joinery.glazing_fraction(to_design(op), op.W / 1000.0, op.H / 1000.0) * area
    opening = sum(c.w * p.h for c in op.cols for p in c.panels if p.op != "fixed") / 1e6
    return {"area": area, "glass": glass, "open": opening}


def problems(op):
    """What is wrong with it as a joinery design (core/joinery.problems: [(i18n key, values)])."""
    return joinery.problems(to_design(op), op.W / 1000.0, op.H / 1000.0)


def next_name(items, kind):
    """The next reference of its kind: «J03», «P02»."""
    prefix = "P" if kind == "door" else "J"
    n = 0
    for it in items:
        if it.name[:1] == prefix and it.name[1:].isdigit():
            n = max(n, int(it.name[1:]))
    return "{}{:02d}".format(prefix, n + 1)


# ------------------------------------------------------------ to start from (the prototype's)

def _col(w, *panels):
    return Column(w, [Panel(h, o, f) for h, o, f in panels])


def default_window():
    return Opening("J01", "window", 2400, 1500, 900, 60, "aluminio", "grafite",
                   [_col(800, (400, "bottom", "glass"), (1100, "left", "glass")),
                    _col(800, (400, "bottom", "glass"), (1100, "fixed", "glass")),
                    _col(800, (400, "bottom", "glass"), (1100, "right", "glass"))])


PRESETS = (
    ("caixilho.preset_two_leaves", lambda: Opening("", "window", 1600, 1300, 900, 60, "aluminio", "grafite",
                                                   [_col(800, (1300, "left", "glass")),
                                                    _col(800, (1300, "right", "glass"))])),
    ("caixilho.preset_fanlight", lambda: Opening("", "window", 1000, 1600, 800, 60, "pvc", "branco",
                                                 [_col(1000, (450, "bottom", "glass"), (1150, "tilt_left", "glass"))])),
    ("caixilho.preset_door", lambda: Opening("", "door", 900, 2100, 0, 70, "madeira", "natural",
                                             [_col(900, (2100, "left", "wood"))])),
    ("caixilho.preset_door_side", lambda: Opening("", "door", 1500, 2650, 0, 70, "madeira", "bronze",
                                                  [_col(1000, (450, "fixed", "glass"), (2200, "left", "wood")),
                                                   _col(500, (450, "fixed", "glass"), (2200, "fixed", "frosted"))])),
    ("caixilho.preset_sliding", lambda: Opening("", "door", 2400, 2200, 0, 60, "aluminio", "grafite",
                                                [_col(1200, (2200, "slide_right", "glass")),
                                                 _col(1200, (2200, "fixed", "glass"))])),
    ("caixilho.preset_bare", lambda: Opening("", "window", 1000, 1000, 900, 60, "aluminio", "grafite",
                                             [_col(1000, (1000, "fixed", "glass"))])),
)


def same(a, b):
    """Do two openings say the same (the studio's fields; not where they came from)?"""
    names = [f.name for f in fields(Opening) if f.name not in ("base", "key", "material")]
    return all(getattr(a, n) == getattr(b, n) for n in names)
