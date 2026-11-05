"""The reinforcement of a concrete member laid out (0.166, Phase 9, step 4): from its verification (core.ec2.Design —
how many bars, which diameters, the links' spacing) and its shape, each set of bars as their centrelines — a
beam's bottom and top bars, run into its supports and bent at their ends, its stirrups closed with 135° hooks; a
column's bars from its footing (bent there) to its top (lapped with the column above, else bent into the floor),
its ties; a footing's bottom mesh both ways, bent up at its ends; a slab's bottom mesh both ways, cut by its outline
less the cover. The bars' cut lengths, their shape codes (BS 8666: 00 straight, 11 one bend, 21 two, 51 a closed
link), their masses: what the bar schedule lists. (0.224) A slab's top bars over the beams it rests on.

Pure numpy and shapely; program coordinates in metres, diameters in mm."""

import math
from dataclasses import dataclass, field

import numpy as np

from . import ec2

ROLES = ("bottom", "top", "stirrups", "main", "ties", "mesh_x", "mesh_y", "top_x", "top_y", "wall_v", "wall_h",
         "wall_trim")
IFC_KIND = {"bottom": "MAIN", "top": "MAIN", "main": "MAIN", "mesh_x": "MAIN", "mesh_y": "MAIN",
            "top_x": "MAIN", "top_y": "MAIN", "stirrups": "SHEAR", "ties": "LIGATURE",
            "wall_v": "MAIN", "wall_h": "MAIN", "wall_trim": "MAIN"}   # (IfcReinforcingBarTypeEnum; 0.342: walls')
TRIM_BAR = 12                   # (0.342) mm: the bars round a wall's openings
MIN_PIECE = 0.30                # (0.342) m: a wall's bar shorter than this (between an opening and an end) left out
END_GAP = 0.05                  # m: the first and last link this far from the member's ends
HOOP_SEGMENTS = 24              # (0.227) a round column's hoop drawn with this many straight pieces
LAP_FACTOR = 1.5                # α6 for laps with more than half of the bars lapped at a section (EC2 8.7.3)
STOCK = 12.0                    # (0.230) m: the bars as they are sold — a longer one spliced


@dataclass
class BarSet:
    role: str
    diameter: int               # mm
    bars: list = field(default_factory=list)    # [[(x, y, z), …]] centrelines
    spacing: float = 0.0        # m (links, meshes)

    @property
    def kind(self):
        return IFC_KIND[self.role]

    @staticmethod
    def length_of(bar):
        p = np.asarray(bar, dtype=float)
        return float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum())

    def shape_of(self, bar):
        if self.role in ("stirrups", "ties"):
            return "51"
        bends = max(len(bar) - 2, 0)
        return {0: "00", 1: "11"}.get(bends, "21")

    @staticmethod
    def bends_of(bar):
        """Its segments' lengths (m, to the cm), "a;b;c": how it is bent — two bars of one length and shape code
        but bent otherwise (a column's tie, a beam's stirrup) are not one position."""
        p = np.asarray(bar, dtype=float)
        return ";".join("{:.2f}".format(v) for v in np.linalg.norm(np.diff(p, axis=0), axis=1))

    def groups(self):
        """[(shape code, cut length m, bends, [bars])]: the set's bars of one shape, length (to the cm) and bending
        together — each a position of the bar schedule."""
        out = {}
        for bar in self.bars:
            key = (self.shape_of(bar), round(self.length_of(bar) + 0.004, 2), self.bends_of(bar))
            out.setdefault(key, []).append(bar)
        return [(shape, length, bends, bars) for (shape, length, bends), bars in
                sorted(out.items(), key=lambda kv: -kv[0][1])]


def design_from(stored):
    """The ec2.Design (its bars only) of a member's design as kept with its bars (model.structure_design
    ElementDesign.stored())."""
    d = ec2.Design(stored.get("kind", ""), cover=float(stored.get("cover", ec2.COVER)))
    for key in ("bottom", "top", "bars", "links", "mesh_x", "mesh_y", "top_x", "top_y", "vertical", "horizontal"):
        if stored.get(key) is not None:
            a, b = stored[key]
            setattr(d, key, (int(a), int(b)) if key in ("bottom", "top", "bars") else (int(a), float(b)))
    d.bottom2, d.top2 = (int(v) for v in stored.get("layers", (0, 0)))
    for face in ("bottom", "top"):                      # (0.229) the bars that stop, and where
        if stored.get(face + "_zones"):
            setattr(d, face + "_cont", int(stored.get(face + "_cont", 2)))
            setattr(d, face + "_zones", [tuple(float(v) for v in z) for z in stored[face + "_zones"]])
    return d


def _round_up(v, step=0.05):
    return math.ceil(v / step - 1e-9) * step


def lap_length(d, fck, fyk):
    return _round_up(LAP_FACTOR * ec2.bond_length(d, fck, fyk))


def spliced(sets, fck, fyk, stock=STOCK):
    """(0.230) The sets with each bar longer than `stock` (its developed length: the bars as they are sold) cut into
    pieces lapped l0 = lap_length (α6 1,5, all of them lapped in one section: EC2 8.7.3) along its longest straight
    part, evenly, each piece no longer than stock — every other piece a diameter beside (lapped bars lie side by
    side). Links and ties kept as they are."""
    out = []
    for st in sets:
        if st.role in ("stirrups", "ties"):
            out.append(st)
            continue
        l0 = lap_length(st.diameter, fck, fyk)
        bars = []
        for bar in st.bars:
            bars += _splice(bar, l0, st.diameter / 1000.0, stock)
        out.append(BarSet(st.role, st.diameter, bars, st.spacing))
    return out


def _splice(bar, l0, dia, stock):
    """(0.230) A bar as its pieces (spliced)."""
    p = np.asarray(bar, dtype=float)
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    if float(seg.sum()) <= stock + 1e-9 or l0 >= stock / 2.0:
        return [bar]
    k = int(np.argmax(seg))                             # (cut along its longest straight part)
    a, b, span = p[k], p[k + 1], float(seg[k])
    before, after = float(seg[:k].sum()), float(seg[k + 1:].sum())
    u = (b - a) / span
    side = np.cross(u, (0.0, 0.0, 1.0)) if abs(u[2]) < 0.9 else np.array((1.0, 0.0, 0.0))
    side /= np.linalg.norm(side)
    for n in range(2, 100):
        cuts = [span * j / n for j in range(1, n)]
        lows, highs = [0.0] + [c - l0 / 2.0 for c in cuts], [c + l0 / 2.0 for c in cuts] + [span]
        lengths = [hi - lo + (before if j == 0 else 0.0) + (after if j == n - 1 else 0.0)
                   for j, (lo, hi) in enumerate(zip(lows, highs))]
        if max(lengths) <= stock:
            break
    pieces = []
    for j, (lo, hi) in enumerate(zip(lows, highs)):
        shift = side * dia * (j % 2)
        pts = [q for q in p[:k + 1]] if j == 0 else [a + u * lo]
        pts.append(a + u * hi)
        if j == n - 1:
            pts += [q for q in p[k + 2:]]
        pieces.append([tuple(float(c) for c in q + shift) for q in pts])
    return pieces


def _spread(span, n):
    """n positions evenly over [-span/2, span/2]."""
    if n <= 1:
        return [0.0]
    return [-span / 2.0 + span * k / (n - 1) for k in range(n)]


def _hooked_loop(a, b, d):
    """A closed link's centreline in its own plane (u across, v up): a rectangle 2a × 2b closed by two 135° hooks
    at its top left corner, max(10 φ, 70 mm) long — (u, v, w) with w the small shift along the member between its two
    ends (so that they lie side by side)."""
    hook = max(10.0 * d / 1000.0, 0.07) / math.sqrt(2.0)
    s = d / 1000.0 / 2.0
    return [(-a + hook, b - hook, -s), (-a, b, -s), (-a, -b, 0.0), (a, -b, 0.0), (a, b, 0.0), (-a + 2 * s, b, s),
            (-a + 2 * s + hook, b - hook, s)]


# ------------------------------------------------------------ beams

def beam_sets(start, end, top, width, height, design, fck, fyk, ext=(0.0, 0.0)):
    """The bar sets of a beam start → end (plan; its axis), its top at `top`, width × height: ext — how far its
    bars may run into its support at each end (m, 0: a free end). (0.229) Its bars more than those kept the whole
    length only along their zones (design.bottom_zones / top_zones, m from its start)."""
    start, end = np.asarray(start, dtype=float)[:2], np.asarray(end, dtype=float)[:2]
    axis = end - start
    length = float(np.linalg.norm(axis))
    if length < 1e-6 or design.bottom is None or design.links is None:
        return []
    x = np.array((axis[0] / length, axis[1] / length, 0.0))
    y = np.array((-x[1], x[0], 0.0))
    z = np.array((0.0, 0.0, 1.0))
    origin = np.array((start[0], start[1], top))
    c = design.cover
    link, s = design.links
    t = link / 1000.0
    out = []
    for role, (n, d), second in (("bottom", design.bottom, design.bottom2), ("top", design.top, design.top2)):
        r = d / 2000.0
        level = -height + c + t + r if role == "bottom" else -c - t - r
        across = width - 2.0 * (c + t + r)
        leg = min(max(12.0 * d / 1000.0, 0.15), height - 2.0 * (c + t) - 2.0 * r)
        up = 1.0 if role == "bottom" else -1.0
        first = _spread(across, n - second)
        # (0.225) a second layer: over (under, at the top) some of the first's bars — evenly from its corners —, its
        # legs the shorter by the gap
        spots = [(v, level, leg) for v in first]
        if second:
            shift = ec2.layer_offset(d)
            picks = sorted({int(round(k)) for k in np.linspace(0, len(first) - 1, second)}) if second > 1 \
                else [len(first) // 2]
            spots += [(first[k], level + up * shift, leg - shift) for k in picks]
        # (0.229) the bars that stop: those kept the whole length its corners' (and evenly between them), the others
        # only along their zones — into the support (and bent there) when a zone reaches an end
        keep = getattr(design, role + "_cont", 0)
        zones = getattr(design, role + "_zones", None) or [(0.0, length)]
        kept = set(range(len(spots)))
        if zones != [(0.0, length)] and 2 <= keep < len(spots) and not second:
            kept = {int(round(k)) for k in np.linspace(0, len(spots) - 1, keep)}
        bars = []
        for k, (v, lv, lg) in enumerate(spots):
            for z0, z1 in ([(0.0, length)] if k in kept else zones):
                at_start, at_end = z0 <= 1e-6, z1 >= length - 1e-6
                a = (-ext[0] if ext[0] > 0.0 else c) if at_start else z0     # (into the support, else to the cover)
                e = (length + ext[1] if ext[1] > 0.0 else length - c) if at_end else z1
                pts = [(a, v, lv), (e, v, lv)]
                if lg > 0.05:
                    pts = ([(a, v, lv + up * lg)] if at_start else []) + pts + ([(e, v, lv + up * lg)] if at_end
                                                                                  else [])
                bars.append([tuple(origin + x * p[0] + y * p[1] + z * p[2]) for p in pts])
        out.append(BarSet(role, d, bars))
    # stirrups
    a2, b2 = (width - 2.0 * c - t) / 2.0, (height - 2.0 * c - t) / 2.0
    loop = _hooked_loop(a2, b2, link)
    count = max(int(math.floor((length - 2.0 * END_GAP) / s + 1e-9)) + 1, 2)
    bars = []
    for xs in np.linspace(END_GAP, length - END_GAP, count):
        bars.append([tuple(origin + x * (xs + w) + y * u + z * (-height / 2.0 + v)) for u, v, w in loop])
    out.append(BarSet("stirrups", link, bars, s))
    return out


# ------------------------------------------------------------ columns

def column_sets(centre, x_dir, half, base, top, design, fck, fyk, into=0.0, lap=True, shape="rect", web=0.0):
    """The bar sets of a column centred on `centre` (plan), its section 2·half[0] × 2·half[1] along x_dir and across
    it, from base to top: into — how deep its bars go down into the footing under it (0: none; bent outwards there,
    on its mesh); lap — a column goes on above it (the bars lapped with its own), else they stop under the floor's
    top (anchored in its beams and slab). (0.227) A round one (its diameter 2·half[0]), an L or a T (`web` its legs'
    thickness): its bars where its verification put them (ec2.column_spots), its ties round hoops or one closed tie
    round each leg."""
    if design.bars is None or design.links is None:
        return []
    x = np.array((x_dir[0], x_dir[1], 0.0), dtype=float)
    x /= np.linalg.norm(x)
    y = np.array((-x[1], x[0], 0.0))
    z = np.array((0.0, 0.0, 1.0))
    ha, hb = float(half[0]), float(half[1])
    c = design.cover
    n, d = design.bars
    tie, s = design.links
    t, r = tie / 1000.0, d / 2000.0
    spots = ec2.column_spots(shape, 2.0 * ha, 2.0 * hb, web, n, d, c, tie) if shape in ("circle", "L", "T") \
        else None
    if spots is None:
        shape = "rect"
        along_a, along_b = ec2._column_layout(n, 2.0 * ha, 2.0 * hb)
        ia, ib = ha - c - t - r, hb - c - t - r
        spots = []
        for u in _spread(2.0 * ia, along_a):
            spots += [(u, -ib), (u, ib)]
        for v in _spread(2.0 * ib, along_b)[1:-1]:
            spots += [(-ia, v), (ia, v)]
    o = np.array((centre[0], centre[1], 0.0))
    foot = max(12.0 * d / 1000.0, 0.20)
    low = base - into if into > 0.0 else base + c
    high = top + lap_length(d, fck, fyk) if lap else top - c - t
    bars = []
    for u, v in spots:
        out_dir = np.array((u, v)) / max(math.hypot(u, v), 1e-9)
        p = o + x * u + y * v
        pts = [p + z * low, p + z * high]
        if into > 0.0:                                       # (bent outwards on the footing's mesh)
            pts.insert(0, p + z * low + (x * out_dir[0] + y * out_dir[1]) * foot)
        bars.append([tuple(q) for q in pts])
    out = [BarSet("main", d, bars)]
    # each tie a loop in the section's plane (u across, v across, w a small shift along the column): round a
    # rectangle closed by its hooks — (0.227) a round column's a hoop lapped 10 φ past its start, an L's or a T's
    # one round each leg
    if shape == "circle":
        rt = ha - c - t / 2.0
        lap_a = 10.0 * tie / 1000.0 / max(rt, 1e-6)
        angles = np.linspace(0.0, 2.0 * math.pi + lap_a, HOOP_SEGMENTS + 2)
        loops = [[(rt * math.cos(a), rt * math.sin(a), t * a / (2.0 * math.pi)) for a in angles]]
    elif shape in ("L", "T"):
        from .space_frame import shape_rects
        loops = []
        for x0, y0, x1, y1 in shape_rects(shape, 2.0 * ha, 2.0 * hb, web):
            cu, cv = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            loops.append([(cu + u, cv + v, w) for u, v, w in _hooked_loop((x1 - x0) / 2.0 - c - t / 2.0,
                                                                          (y1 - y0) / 2.0 - c - t / 2.0, tie)])
    else:
        loops = [_hooked_loop(ha - c - t / 2.0, hb - c - t / 2.0, tie)]
    height = top - base
    count = max(int(math.floor((height - 2.0 * END_GAP) / s + 1e-9)) + 1, 2)
    ties = []
    for zs in np.linspace(base + END_GAP, top - END_GAP, count):
        for loop in loops:
            ties.append([tuple(o + x * u + y * v + z * (zs + w)) for u, v, w in loop])
    out.append(BarSet("ties", tie, ties, s))
    return out


# ------------------------------------------------------------ walls (0.342)

def _open_spans(lo, hi, cuts, gap):
    """The pieces of [lo, hi] left between the cuts [(a, b)] (each widened by gap), those MIN_PIECE long or more."""
    pieces, at = [], lo
    for a, b in sorted(cuts):
        if b + gap <= at or a - gap >= hi:
            continue
        if a - gap - at >= MIN_PIECE:
            pieces.append((at, a - gap))
        at = max(at, b + gap)
    if hi - at >= MIN_PIECE:
        pieces.append((at, hi))
    return pieces


def wall_sets(start, end, base, top, thickness, openings, design, fck, fyk, into=0.0, lap=False):
    """(0.342) The bars of a reinforced concrete wall along start → end (plan, its axis), from base to top, its
    openings [(s0, s1, z0, z1)] (along it from its start; heights): on each face its horizontal bars (outside) and
    its vertical ones (inside), stopped a cover short of each opening; one bar of φ12 on each face beside each side of
    an opening, over and under it, run an anchorage past its corners. Its vertical bars from the footing under it (into:
    how deep — bent there, out towards their face; 0: from its base) to its top — lapped with the wall above it (lap),
    else stopping a cover under its top (in the floor)."""
    if design.vertical is None or design.horizontal is None:
        return []
    a, b = np.asarray(start, dtype=float)[:2], np.asarray(end, dtype=float)[:2]
    length = float(np.linalg.norm(b - a))
    if length < 0.10 or top - base < 0.10:
        return []
    ux = np.array(((b - a)[0] / length, (b - a)[1] / length, 0.0))
    nx = np.array((-ux[1], ux[0], 0.0))
    z = np.array((0.0, 0.0, 1.0))
    o = np.array((a[0], a[1], 0.0))
    c = design.cover
    dv, sv = design.vertical
    dh, sh = design.horizontal
    rv, rh = dv / 2000.0, dh / 2000.0
    t = max(thickness, 0.05)
    face_h = t / 2.0 - c - rh
    face_v = t / 2.0 - c - 2.0 * rh - rv
    holes = [(float(s0), float(s1), float(z0), float(z1)) for s0, s1, z0, z1 in openings]

    def at(s, side, offset, height):
        return tuple(o + ux * s + nx * side * offset + z * height)

    out = []
    # vertical bars
    foot = max(12.0 * dv / 1000.0, 0.20)
    low = base - into if into > 0.0 else base + c
    high = top + lap_length(dv, fck, fyk) if lap else top - c
    n = max(int(math.floor((length - 2.0 * c - 2.0 * rv) / sv + 1e-9)) + 1, 2)
    bars = []
    for s in np.linspace(c + rv, length - c - rv, n):
        cuts = [(z0, z1) for s0, s1, z0, z1 in holes if s0 - c <= s <= s1 + c]
        for side in (1.0, -1.0):
            for z0, z1 in _open_spans(low, high, cuts, c):
                pts = [at(s, side, face_v, z0), at(s, side, face_v, z1)]
                if into > 0.0 and abs(z0 - low) < 1e-9:              # (bent out on the footing's mesh)
                    pts.insert(0, at(s, side, face_v + foot, z0))
                bars.append(pts)
    out.append(BarSet("wall_v", dv, bars, sv))
    # horizontal bars
    n = max(int(math.floor((top - base - 2.0 * c - 2.0 * rh) / sh + 1e-9)) + 1, 2)
    bars = []
    for h in np.linspace(base + c + rh, top - c - rh, n):
        cuts = [(s0, s1) for s0, s1, z0, z1 in holes if z0 - c <= h <= z1 + c]
        for side in (1.0, -1.0):
            for s0, s1 in _open_spans(c + rh, length - c - rh, cuts, c):
                bars.append([at(s0, side, face_h, h), at(s1, side, face_h, h)])
    out.append(BarSet("wall_h", dh, bars, sh))
    # round each opening: one bar on each face beside each of its sides, over and under it
    reach = lap_length(TRIM_BAR, fck, fyk)
    r = TRIM_BAR / 2000.0
    bars = []
    for s0, s1, z0, z1 in holes:
        for side in (1.0, -1.0):
            lo, hi = max(z0 - reach, base + c), min(z1 + reach, top - c)
            for s in (s0 - c - r, s1 + c + r):
                if c <= s <= length - c and hi - lo >= MIN_PIECE:
                    bars.append([at(s, side, face_v - rv - r, lo), at(s, side, face_v - rv - r, hi)])
            left, right = max(s0 - reach, c), min(s1 + reach, length - c)
            for h in (z0 - c - r, z1 + c + r):
                if base + c <= h <= top - c and right - left >= MIN_PIECE:
                    bars.append([at(left, side, face_h - rh - r, h), at(right, side, face_h - rh - r, h)])
    if bars:
        out.append(BarSet("wall_trim", TRIM_BAR, bars))
    return out


# ------------------------------------------------------------ footings

def footing_sets(centre, x_dir, length, width, top, depth, design):
    """The bottom mesh of a pad footing: bars along its length (x_dir) and across it, bent up at their ends —
    (0.250) a combined footing's top bars along it too (design.top_x)."""
    if design.mesh_x is None or design.mesh_y is None:
        return []
    x = np.array((x_dir[0], x_dir[1], 0.0), dtype=float)
    x /= np.linalg.norm(x)
    y = np.array((-x[1], x[0], 0.0))
    z = np.array((0.0, 0.0, 1.0))
    o = np.array((centre[0], centre[1], top - depth))
    c = design.cover
    out = []
    lift = 0.0
    for role, (d, s), along, across, ax, ay in (("mesh_x", design.mesh_x, length, width, x, y),
                                                ("mesh_y", design.mesh_y, width, length, y, x)):
        r = d / 2000.0
        level = c + lift + r
        lift += 2.0 * r
        n = max(int(math.floor((across - 2.0 * c - 2.0 * r) / s + 1e-9)) + 1, 2)
        leg = min(max(12.0 * d / 1000.0, 0.15), depth - 2.0 * c - 4.0 * r)
        half = along / 2.0 - c - r
        bars = []
        for v in _spread(across - 2.0 * c - 2.0 * r, n):
            pts = [(-half, v, level), (half, v, level)]
            if leg > 0.05:
                pts = [(-half, v, level + leg)] + pts + [(half, v, level + leg)]
            bars.append([tuple(o + ax * p[0] + ay * p[1] + z * p[2]) for p in pts])
        out.append(BarSet(role, d, bars, s))
    if design.top_x is not None:                       # (0.250) a combined footing's top bars, along it, bent down
        d, s = design.top_x
        r = d / 2000.0
        level = depth - c - r
        n = max(int(math.floor((width - 2.0 * c - 2.0 * r) / s + 1e-9)) + 1, 2)
        leg = min(max(12.0 * d / 1000.0, 0.15), depth - 2.0 * c - 4.0 * r)
        half = length / 2.0 - c - r
        bars = []
        for v in _spread(width - 2.0 * c - 2.0 * r, n):
            pts = [(-half, v, level), (half, v, level)]
            if leg > 0.05:
                pts = [(-half, v, level - leg)] + pts + [(half, v, level - leg)]
            bars.append([tuple(o + x * p[0] + y * p[1] + z * p[2]) for p in pts])
        out.append(BarSet("top_x", d, bars, s))
    return out


# ------------------------------------------------------------ slabs

def slab_axes(outline):
    """(x direction, lx, ly): a slab's main direction (along its least rectangle's first side) and its spans."""
    from shapely.geometry import Polygon
    poly = Polygon(outline)
    rect = np.array(poly.minimum_rotated_rectangle.exterior.coords)[:4]
    e1, e2 = rect[1] - rect[0], rect[2] - rect[1]
    l1, l2 = float(np.linalg.norm(e1)), float(np.linalg.norm(e2))
    if l1 < 1e-9:
        return (1.0, 0.0), l2, l1
    ax = e1 / l1
    if abs(ax[0]) < abs(ax[1]):                        # (the one nearer X first)
        ax, l1, l2 = e2 / max(l2, 1e-9), l2, l1
    if ax[0] < 0:
        ax = -ax
    return (float(ax[0]), float(ax[1])), l1, l2


def slab_sets(outline, top, thickness, design, x_dir):
    """The bottom mesh of a slab: straight bars along x_dir and across it, cut by its outline less the cover."""
    from shapely.geometry import LineString, Polygon
    if design.mesh_x is None or design.mesh_y is None:
        return []
    poly = Polygon(outline)
    c = design.cover
    inner = poly.buffer(-c, join_style=2)
    if inner.is_empty:
        return []
    x = np.array((x_dir[0], x_dir[1]), dtype=float)
    x /= np.linalg.norm(x)
    y = np.array((-x[1], x[0]))
    pts = np.asarray(poly.exterior.coords, dtype=float)
    out = []
    lift = 0.0
    for role, (d, s), ax, ay in (("mesh_x", design.mesh_x, x, y), ("mesh_y", design.mesh_y, y, x)):
        r = d / 2000.0
        z = top - thickness + c + lift + r
        lift += 2.0 * r
        along, across = pts @ ax, pts @ ay
        lo, hi = float(across.min()) + c + r, float(across.max()) - c - r
        n = max(int(math.floor((hi - lo) / s + 1e-9)) + 1, 2)
        a0, a1 = float(along.min()) - 1.0, float(along.max()) + 1.0
        bars = []
        for v in np.linspace(lo, hi, n):
            line = LineString([tuple(ax * a0 + ay * v), tuple(ax * a1 + ay * v)])
            cut = line.intersection(inner)
            for piece in getattr(cut, "geoms", [cut]):
                if piece.is_empty or piece.geom_type != "LineString" or piece.length < 0.10:
                    continue
                (p0, p1) = list(piece.coords)[0], list(piece.coords)[-1]
                bars.append([(p0[0], p0[1], z), (p1[0], p1[1], z)])
        if bars:
            out.append(BarSet(role, d, bars, s))
    return out


def slab_top_sets(outline, top, thickness, design, x_dir, supports):
    """(0.224) A slab's top bars over the beams it rests on (EC2 9.3.1.2(2)): across each support (supports: the
    model.structure_design.slab_supports of the slab), spaced as its top mesh, from the support's face 0,2 of the
    span on each side where there is slab — to its edge less the cover where there is none, bent down there into the
    beam —; the bars along x_dir of the top_x mesh, those across it of top_y's (a support askew: the nearer), these a
    layer under those."""
    from shapely.geometry import LineString, Point, Polygon
    if design.top_x is None or design.top_y is None or not supports:
        return []
    poly = Polygon(outline)
    if not poly.is_valid:
        poly = poly.buffer(0)
    c = design.cover
    inner = poly.buffer(-c, join_style=2)
    if inner.is_empty:
        return []
    x = np.array((x_dir[0], x_dir[1]), dtype=float)
    x /= np.linalg.norm(x)
    y = np.array((-x[1], x[0]))
    rx = design.top_x[0] / 2000.0
    sets = {"top_x": [], "top_y": []}
    for x1, y1, x2, y2, half, left, right in supports:
        a, b = np.array((x1, y1), dtype=float), np.array((x2, y2), dtype=float)
        length = float(np.linalg.norm(b - a))
        if length < 0.10:
            continue
        d = (b - a) / length
        n = np.array((-d[1], d[0]))                     # (its left: the side `left` spans)
        role = "top_x" if abs(n @ x) >= abs(n @ y) else "top_y"
        dia, s = getattr(design, role)
        r = dia / 2000.0
        z = top - c - r if role == "top_x" else top - c - 2.0 * rx - r
        leg = min(max(12.0 * dia / 1000.0, 0.10), thickness - 2.0 * c - 4.0 * r)
        reach = [(ec2.TOP_REACH * span + half) if span > 0.0 else 10.0 for span in (left, right)]
        count = max(int(math.floor((length - 2.0 * c) / s + 1e-9)) + 1, 1)
        for u in _spread(length - 2.0 * c, count):
            p = a + d * (length / 2.0 + u)
            cut = LineString((tuple(p - n * reach[1]), tuple(p + n * reach[0]))).intersection(inner)
            pieces = [g for g in getattr(cut, "geoms", [cut]) if g.geom_type == "LineString" and g.length > 0.10]
            if not pieces:
                continue
            piece = min(pieces, key=lambda g: g.distance(Point(tuple(p))))
            q0, q1 = np.asarray(piece.coords[0], dtype=float), np.asarray(piece.coords[-1], dtype=float)
            if (q1 - q0) @ n < 0:
                q0, q1 = q1, q0
            pts = [(q0[0], q0[1], z), (q1[0], q1[1], z)]
            if leg > 0.05:                              # (an end at the slab's edge: bent down into the beam)
                if right <= 0.0:
                    pts.insert(0, (q0[0], q0[1], z - leg))
                if left <= 0.0:
                    pts.append((q1[0], q1[1], z - leg))
            sets[role].append(pts)
    return [BarSet(role, getattr(design, role)[0], bars, getattr(design, role)[1])
            for role, bars in sets.items() if bars]


def mass(sets):
    """kg of steel of these sets."""
    return sum(ec2.bar_mass(st.diameter) * BarSet.length_of(b) for st in sets for b in st.bars)
