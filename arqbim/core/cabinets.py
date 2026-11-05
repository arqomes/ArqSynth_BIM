"""Parametric cabinets (0.169, Phase 10, step 1): the modules of a kitchen or a storage wall — a base unit (on a
plinth, under the worktop), a wall unit (hung over it), a tall unit (a larder, an oven housing) — each made of its
panels as a joiner cuts them: two sides, a bottom, a top (a base unit: two rails), a back, its shelves, the plinth
recessed under it, its fronts (doors, drawers, a drawer over a door, or open) with their gaps, and its handles. What
it is made of is listed: the cut list (each panel's length × width × thickness, its material, its edges banded) and
the hardware (hinges, runners, handles, feet). (0.239) A blind corner unit: part of its front a fixed panel;
(0.240) an L corner unit, two arms round the corner, its doors folding at the inner corner, a carousel in it.

Pure Python: the cabinet's own frame — x along its width (from its left side, seen from the front), y out of the
wall (its back at 0), z up from the floor; metres."""

import math
from dataclasses import dataclass, field

KINDS = ("base", "wall", "tall", "wardrobe")
FRONTS = ("doors", "drawers", "door_drawer", "open", "sliding", "oven")   # (0.241: sliding doors; 0.242: a tall`n#                                                                         unit's oven housing)
HANDLES = ("bar", "knob", "none")
FILLS = ("shelves", "rail", "drawers", "empty", "carousel")   # (0.172) what a compartment holds (0.240: a carousel,
#                                                               in an L corner unit)
SIDES = ("left", "right")                     # (0.239) a corner unit's corner: its x = 0 end, its x = width end
FINISHES = ("melamine", "lacquer_white", "lacquer_grey", "lacquer_black", "oak", "walnut")   # (0.243) the fronts'

BOARD = 0.018                   # m: carcass panels (melamine-faced particleboard)
BACK = 0.003                    # m: the back (HDF)
FRONT = 0.018                   # m: fronts (doors, drawer fronts)
GAP = 0.003                     # m: between fronts, and round them
RAIL = 0.10                     # m: a base unit's top rails
PLINTH_SET_BACK = 0.05          # m: the plinth this far behind the fronts
TOP_DRAWER = 0.15               # m: the drawer over a door
HAT_SHELF = 0.30                # m: a wardrobe's hat shelf under its top (its rail under it), 0.172
INNER_DRAWERS, INNER_DRAWER_H = 3, 0.18          # a compartment's inner drawers
WIDTHS = (0.30, 0.40, 0.45, 0.50, 0.60, 0.80, 0.90, 1.00, 1.20)      # the usual module widths
MIN_DOOR = 0.25                 # m: the narrowest door (doors at least 25 cm wide)
MIN_COMPARTMENT = 0.15          # m: the narrowest compartment (0.172; 0.244: its divisions dragged)
CORNER_CLEAR = 0.05             # (0.239) m: a blind corner's panel past the other run's fronts (their handles: 3 cm)
CORNER_DOOR = 0.35              # m: …and the door it leaves at least, in a kitchen made in one go
L_ARMS = {"base": 0.90, "wall": 0.65}    # (0.240) m: an L corner unit's two arms, in a kitchen made in one go
CAROUSEL_TRAYS = 2              # (0.240) a carousel's trays: three quarters of a disc, its doors on the cut quarter
CAROUSEL_CLEAR = 0.02           # m: round its trays
SLIDE_TRACK = 0.06              # (0.241) m: sliding doors' two-track profile, out of the carcass (each door in
#                                 its own half)
SLIDE_OVERLAP = 0.03            # m: two sliding doors one over the other where they meet
SLIDE_DOOR = 0.30               # m: the narrowest sliding door
SLIDE_RAIL = 0.04               # m: the top track's height (the doors under it)
OVEN_SILL = 0.86                # (0.242) m over the floor: an oven's underside in a tall unit (at eye level), on a
#                                 fixed shelf
OVEN_NICHE = 0.60               # m: its opening's height (an oven of 59,5 cm)
OVEN_DRAWERS = 2                # the drawers under it

DEFAULTS = {                    # carcass height, depth, plinth, elevation (its underside over the floor)
    "base": {"height": 0.72, "depth": 0.56, "plinth": 0.15, "elevation": 0.0},
    "wall": {"height": 0.72, "depth": 0.33, "plinth": 0.0, "elevation": 1.45},
    "tall": {"height": 2.02, "depth": 0.56, "plinth": 0.15, "elevation": 0.0},
    "wardrobe": {"height": 2.30, "depth": 0.58, "plinth": 0.10, "elevation": 0.0, "width": 1.00, "doors": 2,
                 "interior": "rail,shelves", "shelves": 4},                  # (0.172)
}


@dataclass
class Cabinet:
    kind: str = "base"
    width: float = 0.60
    height: float = 0.72        # the carcass's (without its plinth)
    depth: float = 0.56         # the carcass's (without its fronts)
    plinth: float = 0.15
    elevation: float = 0.0      # a wall unit's underside over the floor
    fronts: str = "doors"
    doors: int = 1
    drawers: int = 3
    shelves: int = 1
    handle: str = "bar"
    interior: str = ""          # (0.172) its compartments' fills, "rail,shelves,…" (none: one, of shelves)
    blind: float = 0.0          # (0.239) a blind corner unit: this much of its front, on corner_side, a fixed panel
    corner_side: str = "right"
    arm: float = 0.0            # (0.240) an L corner unit: its second arm, along the wall round the corner on
    #                             corner_side — m from the first wall's face (0: a straight unit)
    finish: str = "melamine"     # (0.243) its fronts' finish (FINISHES): their material and colour
    splits: str = ""            # (0.244) its divisions' middles, m from its left side, "0.45,1.20" (none: even)

    @classmethod
    def of(cls, kind="base", **values):
        d = dict(DEFAULTS[kind], kind=kind)
        d.update({k: v for k, v in values.items() if v is not None})
        return cls(**d)

    @property
    def bottom(self):
        """The carcass's underside over the floor."""
        return self.elevation + (self.plinth if self.kind != "wall" else 0.0)

    @property
    def top(self):
        return self.bottom + self.height

    @property
    def compartments(self):
        """Its compartments' fills, left to right (0.172): one of shelves when it has no divisions."""
        found = [f.strip() for f in (self.interior or "").split(",") if f.strip()]
        return found or ["shelves"]

    @property
    def divisions(self):
        """(0.244) Its divisions' middles (m from its left side), left to right: as placed (splits), else evenly
        between its sides — one fewer than its compartments (none for a drawer unit)."""
        n = len(self.compartments) if self.fronts != "drawers" else 1
        if n < 2:
            return []
        try:
            placed = [float(v) for v in (self.splits or "").split(",") if v.strip()]
        except ValueError:
            placed = []
        if len(placed) == n - 1:
            return placed
        cw = (self.width - 2 * BOARD - (n - 1) * BOARD) / n
        return [BOARD + k * cw + (k - 1) * BOARD + BOARD / 2 for k in range(1, n)]

    def compartment_spans(self):
        """(0.244) (left, right) of each compartment between its sides and divisions (m from its left side)."""
        edges = [BOARD] + [x for m in self.divisions for x in (m - BOARD / 2, m + BOARD / 2)] + [self.width - BOARD]
        return list(zip(edges[0::2], edges[1::2]))

    @property
    def front_depth(self):
        """How far its fronts stand out of its carcass: none (open), a door's (0.241: sliding doors' tracks)."""
        return {"open": 0.0, "sliding": SLIDE_TRACK}.get(self.fronts, FRONT)

    @property
    def overall_depth(self):
        return BACK + self.depth + self.front_depth


@dataclass
class Panel:
    role: str                   # "side" | "bottom" | "top" | "rail" | "back" | "shelf" | "plinth" | "door" | "drawer"
    #                             | "division" | "hanger" | "inner_drawer" (0.172)
    box: tuple                  # (x0, y0, z0, x1, y1, z1)
    material: str = "carcass"   # "carcass" | "back" | "front" (0.243: "front_<finish>") | "handle" | "fitting"
    edges: int = 0              # how many of its edges are banded

    @property
    def sizes(self):
        x0, y0, z0, x1, y1, z1 = self.box
        return abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)

    def cut(self):
        """(length, width, thickness) as a cut list gives it: its two larger sizes, the larger first."""
        a, b, c = sorted(self.sizes, reverse=True)
        return a, b, c


@dataclass
class Layout:
    panels: list = field(default_factory=list)
    hardware: dict = field(default_factory=dict)      # "hinge" | "runner" | "handle" | "foot" -> how many


def validate(c):
    """What is wrong with a cabinet's sizes, or None."""
    if c.kind not in KINDS or c.fronts not in FRONTS or c.handle not in HANDLES or c.finish not in FINISHES:
        return "cabinet_bad"
    widest = 2.70 if c.kind == "wardrobe" else 1.50     # (0.241: a wardrobe as wide as a board is long, 2,80 m)
    if c.width < 0.15 or c.width > widest or c.height < 0.20 or c.height > 2.60 or c.depth < 0.20 or c.depth > 0.90:
        return "cabinet_size"
    if c.fronts in ("drawers",) and not 1 <= c.drawers <= 6:
        return "cabinet_drawers"
    if c.fronts == "door_drawer" and c.height < TOP_DRAWER + 0.20:
        return "cabinet_size"
    fills = [f.strip() for f in (c.interior or "").split(",") if f.strip()]
    if any(f not in FILLS for f in fills) or len(fills) > 5:
        return "cabinet_bad"
    if fills and (c.width - 2 * BOARD - (len(fills) - 1) * BOARD) / len(fills) < MIN_COMPARTMENT:
        return "cabinet_size"                            # (compartments under 15 cm)
    if any(b - a < MIN_COMPARTMENT - 1e-9 for a, b in c.compartment_spans()):
        return "cabinet_size"                            # (0.244: placed divisions too: none under 15 cm)
    if c.fronts == "oven" and (c.kind != "tall" or c.width < 0.60 - 1e-9 or c.bottom > OVEN_SILL - 0.20
                               or c.top < OVEN_SILL + OVEN_NICHE + 0.25):
        return "cabinet_oven"                            # (0.242: a tall unit, 60 cm wide, round the oven's height)
    if c.fronts == "sliding" and ((c.width + (sliding_doors(c) - 1) * SLIDE_OVERLAP) / sliding_doors(c)
                                  < SLIDE_DOOR - 1e-9 or c.height < 0.40):
        return "cabinet_sliding"                         # (0.241: doors of 30 cm at least)
    if c.blind and (c.blind < 0.0 or c.kind not in ("base", "wall") or c.fronts != "doors"
                    or c.corner_side not in SIDES or c.width - c.blind < MIN_DOOR - 1e-9):
        return "cabinet_blind"                           # (0.239: a door beside it, 25 cm at least)
    if c.arm:                                            # (0.240) an L corner unit: a door of 25 cm on each arm
        inner = BACK + c.depth + FRONT + MIN_DOOR
        if (c.arm < 0.0 or c.kind not in ("base", "wall") or c.fronts != "doors" or c.blind
                or c.corner_side not in SIDES or min(c.width, c.arm) < inner - 1e-9 or c.arm > 1.50
                or len(fills) > 1):
            return "cabinet_corner"
    elif "carousel" in fills:
        return "cabinet_corner"                          # (a carousel only in an L corner unit)
    return None


def front_material(c):
    """(0.243) Its fronts' material in its layout and the cut list: "front", or "front_<finish>" when they are not of
    melamine."""
    return "front" if c.finish == "melamine" else "front_" + c.finish


def sliding_doors(c):
    """(0.241) How many sliding doors a cabinet has: its doors, 2 at least, 4 at most."""
    return max(2, min(int(c.doors), 4))


def corner_blind(other_depth):
    """(0.239) How much of a blind corner unit's front is closed: the run round the corner's depth (its fronts
    included) and its handles' room."""
    return float(other_depth) + CORNER_CLEAR


def corner_width(blind, door=CORNER_DOOR):
    """(0.239) The narrowest usual width of a blind corner unit with `blind` closed that leaves a door of `door`
    beside it (the widest there is when none does)."""
    return next((w for w in WIDTHS if w - blind >= door - 1e-9), WIDTHS[-1])


def layout(c):
    """The Layout of a cabinet: its panels (boxes in its own frame) and its hardware."""
    if c.arm > 0.0:
        return _layout_l(c)
    out = Layout()
    t, w, b0, h = BOARD, c.width, c.bottom, c.height
    y0, y1 = BACK, BACK + c.depth                       # (the carcass, in front of its back)
    p = out.panels
    p.append(Panel("side", (0.0, y0, b0, t, y1, b0 + h), edges=1))
    p.append(Panel("side", (w - t, y0, b0, w, y1, b0 + h), edges=1))
    p.append(Panel("bottom", (t, y0, b0, w - t, y1, b0 + t), edges=1))
    if c.kind == "base":                                # (rails: the worktop goes on them)
        p.append(Panel("rail", (t, y1 - RAIL, b0 + h - t, w - t, y1, b0 + h), edges=1))
        p.append(Panel("rail", (t, y0, b0 + h - t, w - t, y0 + RAIL, b0 + h)))
    else:
        p.append(Panel("top", (t, y0, b0 + h - t, w - t, y1, b0 + h), edges=1))
    p.append(Panel("back", (0.0, 0.0, b0, w, BACK, b0 + h), material="back"))
    inner_lo, inner_hi = b0 + t, b0 + h - t
    if c.fronts == "door_drawer":
        inner_hi -= TOP_DRAWER
    if c.fronts == "oven":                              # (0.242) its housing: a fixed shelf under the oven and one
        for z in (OVEN_SILL - t, OVEN_SILL + OVEN_NICHE):   # over it; its shelves above, behind the door
            p.append(Panel("shelf", (t, y0, z, w - t, y1, z + t), edges=1))
        inner_lo = OVEN_SILL + OVEN_NICHE + t
    # (0.172) its compartments, side by side between its divisions; each its shelves, a hanging rail, drawers
    fills = c.compartments if c.fronts != "drawers" else ["empty"]
    for m in c.divisions:                               # (0.244: where they were put, else evenly)
        p.append(Panel("division", (m - t / 2, y0 + 0.002, inner_lo, m + t / 2, y1 - 0.02, inner_hi), edges=1))
    for fill, (xa, xb) in zip(fills, c.compartment_spans()):
        if fill == "shelves":
            shelves = max(int(c.shelves), 0)
            for j in range(shelves):
                z = inner_lo + (inner_hi - inner_lo) * (j + 1) / (shelves + 1) - t / 2
                p.append(Panel("shelf", (xa + 0.001, y0 + 0.002, z, xb - 0.001, y1 - 0.02, z + t), edges=1))
        elif fill == "rail":                             # (a hat shelf, the rail under it)
            z = inner_hi - HAT_SHELF
            p.append(Panel("shelf", (xa + 0.001, y0 + 0.002, z, xb - 0.001, y1 - 0.02, z + t), edges=1))
            ym = (y0 + y1) / 2
            p.append(Panel("hanger", (xa, ym - 0.008, z - 0.07, xb, ym + 0.008, z - 0.04), "handle"))
            out.hardware["hanger"] = out.hardware.get("hanger", 0) + 1
        elif fill == "drawers":                          # (inner drawers, at the bottom: their fronts of board)
            for j in range(INNER_DRAWERS):
                z = inner_lo + j * INNER_DRAWER_H
                p.append(Panel("inner_drawer", (xa + 0.012, y1 - 0.04 - t, z + 0.005, xb - 0.012, y1 - 0.04,
                                                z + INNER_DRAWER_H - 0.005), edges=4))
            out.hardware["runner"] = out.hardware.get("runner", 0) + INNER_DRAWERS
    if c.kind != "wall" and c.plinth > 0.0:
        py = y1 + c.front_depth - PLINTH_SET_BACK
        p.append(Panel("plinth", (0.0, py - t, c.elevation, w, py, c.elevation + c.plinth - 0.002), edges=1))
        out.hardware["foot"] = 4 if w <= 0.9 else 6
    # the fronts, with their gaps; and their handles
    fy0, fy1 = y1, y1 + FRONT
    handles = 0
    hinges = 0
    runners = 0

    def front(role, x0, z0, x1, z1):
        p.append(Panel(role, (x0 + GAP / 2, fy0, z0 + GAP / 2, x1 - GAP / 2, fy1, z1 - GAP / 2), front_material(c),
                       edges=4))

    lo, hi = 0.0, w                                     # (the doors' part of its front)
    if c.fronts == "doors" and c.blind > 0.0:           # (0.239) a blind corner: its corner side a fixed panel
        if c.corner_side == "left":
            front("blind", 0.0, b0, c.blind, b0 + h)
            lo = c.blind
        else:
            front("blind", w - c.blind, b0, w, b0 + h)
            hi = w - c.blind
    if c.fronts == "doors":
        span = hi - lo
        n = max(1, min(int(c.doors), int(span / MIN_DOOR + 1e-9), 4))  # (doors at least 25 cm wide, 4 at most)
        for k in range(n):
            front("door", lo + span * k / n, b0, lo + span * (k + 1) / n, b0 + h)
        hinges += n * (3 if h > 0.90 else 2)
        handles += n
    elif c.fronts == "drawers":
        n = max(int(c.drawers), 1)
        for k in range(n):
            front("drawer", 0.0, b0 + h * k / n, w, b0 + h * (k + 1) / n)
        runners += n
        handles += n
    elif c.fronts == "door_drawer":
        front("drawer", 0.0, b0 + h - TOP_DRAWER, w, b0 + h)
        front("door", 0.0, b0, w, b0 + h - TOP_DRAWER)
        runners += 1
        hinges += 3 if h - TOP_DRAWER > 0.90 else 2
        handles += 2
    elif c.fronts == "oven":                            # (0.242) drawers under the oven, its opening, a door over it
        sill, lintel = OVEN_SILL - t, OVEN_SILL + OVEN_NICHE + t
        for k in range(OVEN_DRAWERS):
            front("drawer", 0.0, b0 + (sill - b0) * k / OVEN_DRAWERS, w, b0 + (sill - b0) * (k + 1) / OVEN_DRAWERS)
        front("door", 0.0, lintel, w, b0 + h)
        runners += OVEN_DRAWERS
        hinges += 3 if b0 + h - lintel > 0.90 else 2
        handles += OVEN_DRAWERS + 1
    elif c.fronts == "sliding":                         # (0.241) on two tracks, every other one in front, a little
        n = sliding_doors(c)                            # over its neighbours where they meet; a track over, one under
        dw = (w + (n - 1) * SLIDE_OVERLAP) / n
        half = SLIDE_TRACK / 2
        for k in range(n):
            x0 = k * (dw - SLIDE_OVERLAP)
            ya = y1 + (half if k % 2 else 0.0) + (half - FRONT) / 2
            p.append(Panel("sliding_door", (x0, ya, b0 + 0.01, x0 + dw, ya + FRONT, b0 + h - SLIDE_RAIL),
                           front_material(c), edges=4))
            if c.handle != "none":                      # (a pull by its free edge: the outer ones', the middle's)
                xe = x0 + 0.04 if k == 0 else x0 + dw - 0.04 if k == n - 1 else x0 + dw / 2
                zc = b0 + min(h / 2, 1.05)
                size = (0.012, 0.16) if c.handle == "bar" else (0.03, 0.03)
                p.append(Panel("handle", (xe - size[0] / 2, ya + FRONT, zc - size[1] / 2, xe + size[0] / 2,
                                          ya + FRONT + 0.005, zc + size[1] / 2), "handle"))
        p.append(Panel("track", (0.0, y1, b0 + h - SLIDE_RAIL, w, y1 + SLIDE_TRACK, b0 + h), "fitting"))
        p.append(Panel("track", (0.0, y1, b0, w, y1 + SLIDE_TRACK, b0 + 0.01), "fitting"))
        out.hardware["slide"] = 1
        if c.handle != "none":
            out.hardware["handle"] = n
    if c.handle != "none" and handles:
        out.hardware["handle"] = handles
        for panel in [q for q in p if q.role in ("door", "drawer")]:
            p.append(_handle(c, panel, lo, hi))
    if hinges:
        out.hardware["hinge"] = hinges
    if runners:
        out.hardware["runner"] = runners
    return out


def _layout_l(c):
    """(0.240) An L corner unit: its first arm along its width, its second along the wall round the corner — laid
    with that corner on the right (x = width), then turned over for one on the left. A side at each arm's open end;
    the bottom, the top (or rails) and the back in two pieces; its shelves as Ls, or a carousel's trays round the
    inner corner; the plinth along both fronts; a door on each arm's front, meeting at the inner corner (folding:
    hinged to each other and to the second arm's end), one handle by the first's free edge."""
    out = Layout()
    p = out.panels
    t, w, a, b0 = BOARD, c.width, c.arm, c.bottom
    top = b0 + c.height
    y0, y1 = BACK, BACK + c.depth                       # (the first arm's carcass, out of its wall)
    x0, x1 = w - BACK - c.depth, w - BACK               # (the second's, out of the other)
    p.append(Panel("side", (0.0, y0, b0, t, y1, top), edges=1))
    p.append(Panel("side", (x0, a - t, b0, x1, a, top), edges=1))
    p.append(Panel("bottom", (t, y0, b0, x1, y1, b0 + t), edges=1))
    p.append(Panel("bottom", (x0, y1, b0, x1, a - t, b0 + t), edges=1))
    if c.kind == "base":                                # (rails: the worktop goes on them)
        p.append(Panel("rail", (t, y1 - RAIL, top - t, x0 + RAIL, y1, top), edges=1))
        p.append(Panel("rail", (x0, y1, top - t, x0 + RAIL, a - t, top), edges=1))
        p.append(Panel("rail", (t, y0, top - t, x1, y0 + RAIL, top)))
        p.append(Panel("rail", (x1 - RAIL, y0 + RAIL, top - t, x1, a - t, top)))
    else:
        p.append(Panel("top", (t, y0, top - t, x1, y1, top), edges=1))
        p.append(Panel("top", (x0, y1, top - t, x1, a - t, top), edges=1))
    p.append(Panel("back", (0.0, 0.0, b0, w, BACK, top), material="back"))
    p.append(Panel("back", (x1, BACK, b0, w, a, top), material="back"))
    lo, hi = b0 + t, top - t
    fill = c.compartments[0]
    if fill == "carousel":                              # (its trays round the inner corner, their doors on them)
        r = min(x0 - t, a - t - y1, c.depth) - CAROUSEL_CLEAR
        for j in range(CAROUSEL_TRAYS):
            z = lo + (hi - lo) * (j + 0.5) / CAROUSEL_TRAYS - 0.01
            p.append(Panel("carousel", (x0 - r, y1 - r, z, x0 + r, y1 + r, z + 0.02), "fitting"))
        out.hardware["carousel"] = 1
    elif fill == "shelves":
        shelves = max(int(c.shelves), 0)
        for j in range(shelves):
            z = lo + (hi - lo) * (j + 1) / (shelves + 1) - t / 2
            p.append(Panel("shelf", (t + 0.001, y0 + 0.002, z, x1 - 0.002, y1 - 0.02, z + t), edges=1))
            p.append(Panel("shelf", (x0 + 0.02, y1 - 0.02, z, x1 - 0.002, a - t - 0.001, z + t), edges=1))
    if c.kind != "wall" and c.plinth > 0.0:             # (behind each arm's fronts)
        py, px = y1 + FRONT - PLINTH_SET_BACK, x0 - FRONT + PLINTH_SET_BACK
        e, ph = c.elevation, c.elevation + c.plinth - 0.002
        p.append(Panel("plinth", (0.0, py - t, e, px + t, py, ph), edges=1))
        p.append(Panel("plinth", (px, py, e, px + t, a, ph), edges=1))
        out.hardware["foot"] = 6
    fy = y1 + FRONT                                     # (the first arm's doors' face; the second's at x0 − FRONT)
    p.append(Panel("door", (GAP / 2, y1, b0 + GAP / 2, x0 - GAP / 2, fy, top - GAP / 2), front_material(c), edges=4))
    p.append(Panel("door", (x0 - FRONT, fy + GAP / 2, b0 + GAP / 2, x0, a - GAP / 2, top - GAP / 2), front_material(c),
                   edges=4))
    out.hardware["hinge"] = 4 if c.height <= 0.90 else 6
    if c.handle != "none":
        bar = c.handle == "bar"
        length, size = (0.16, 0.012) if bar else (0.03, 0.03)
        tall = length if bar else size
        zc = (b0 + 0.06 + tall / 2) if c.kind == "wall" else (top - 0.06 - tall / 2)
        p.append(Panel("handle", (0.04 - size / 2, fy, zc - tall / 2, 0.04 + size / 2, fy + 0.03, zc + tall / 2),
                       "handle"))
        out.hardware["handle"] = 1
    if c.corner_side == "left":                         # (turned over: the corner at x = 0)
        for panel in p:
            bx0, by0, bz0, bx1, by1, bz1 = panel.box
            panel.box = (w - bx1, by0, bz0, w - bx0, by1, bz1)
    return out


def carousel_ring(panel, corner_side="right", n=18):
    """(0.240) A carousel tray's outline, plan in its cabinet's frame: three quarters of a disc round the inner
    corner, the quarter towards the room (its doors) cut away — [(x, y)], its centre first."""
    x0, y0, _z0, x1, y1, _z1 = panel.box
    cx, cy, r = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2
    start = math.pi if corner_side == "right" else math.pi / 2       # (round from the room's quarter's far edge)
    return [(cx, cy)] + [(cx + r * math.cos(start + 1.5 * math.pi * k / n),
                          cy + r * math.sin(start + 1.5 * math.pi * k / n)) for k in range(n + 1)]


def _handle(c, front, lo=0.0, hi=None):
    """A handle on a front: a bar (128 mm between holes, 160 long) or a knob — on a drawer, centred near its top; on a
    door, upright by its opening edge (near the top of a base unit's, the bottom of a wall unit's). lo, hi: the
    doors' part of the front (0.239: a blind corner's — its single door opening by the panel, away from the
    corner)."""
    hi = c.width if hi is None else hi
    x0, _y0, z0, x1, y1, z1 = front.box
    bar = c.handle == "bar"
    length, size = (0.16, 0.012) if bar else (0.03, 0.03)
    y = (y1, y1 + 0.03)
    if front.role == "drawer":
        xm, zt = (x0 + x1) / 2, z1 - min(0.05, (z1 - z0) / 3)
        return Panel("handle", (xm - length / 2, y[0], zt - size / 2, xm + length / 2, y[1], zt + size / 2), "handle")
    single = x0 < lo + 0.01 and x1 > hi - 0.01
    if single:                                           # (a single door opens on its right — a blind corner's, by
        opening_right = c.corner_side == "right" if c.blind > 0.0 else True      # its panel)
    else:
        opening_right = x1 < hi - 0.01
    xe = x1 - 0.04 if opening_right else x0 + 0.04
    if c.kind == "wall" or c.fronts == "oven":           # (0.242: an oven housing's door, over the oven: low too)
        zc = z0 + 0.06 + (length / 2 if bar else 0.0)
    else:
        zc = z1 - 0.06 - (length / 2 if bar else 0.0)
    if bar:
        return Panel("handle", (xe - size / 2, y[0], zc - length / 2, xe + size / 2, y[1], zc + length / 2), "handle")
    return Panel("handle", (xe - size / 2, y[0], zc - size / 2, xe + size / 2, y[1], zc + size / 2), "handle")


def cut_list(layouts):
    """[(role, material, length, width, thickness, quantity, edges)] of these layouts' panels (handles left out):
    equal panels (role, material, sizes to the mm, edges) together, the longest first."""
    out = {}
    for lay in layouts:
        for panel in lay.panels:
            if panel.material in ("handle", "fitting"):      # (0.240: a carousel's trays come with it)
                continue
            a, b, c = panel.cut()
            key = (panel.role, panel.material, round(a, 3), round(b, 3), round(c, 3), panel.edges)
            out[key] = out.get(key, 0) + 1
    rows = [(role, mat, a, b, c, n, e) for (role, mat, a, b, c, e), n in out.items()]
    return sorted(rows, key=lambda r: (r[1], -r[2], -r[3], r[0]))


def hardware(layouts):
    out = {}
    for lay in layouts:
        for k, n in lay.hardware.items():
            out[k] = out.get(k, 0) + n
    return out


def area(rows):
    """m² of board of cut list rows, by material."""
    out = {}
    for _role, mat, a, b, _c, n, _e in rows:
        out[mat] = out.get(mat, 0.0) + a * b * n
    return out


def snap_width(w):
    """The usual module width nearest to w."""
    return min(WIDTHS, key=lambda x: abs(x - w))


def fill(length, module=0.60, least=0.30):
    """Module widths that fill `length` (a run between walls): modules of 60 cm, then the largest usual width that
    fits in what is left (under `least`, it is left for a filler)."""
    n = int(math.floor(float(length) / module + 1e-9))
    out = [module] * n
    left = float(length) - n * module
    rest = [w for w in WIDTHS if least - 1e-9 <= w <= left + 1e-9]
    if rest:
        out.append(rest[-1])
    return out


def angle_of(x_dir):
    return math.degrees(math.atan2(x_dir[1], x_dir[0]))
