"""(0.336) The loads on the load-bearing walls (step 2 of «Paredes resistentes no cálculo»), as EN 1996-3's
simplified ways have them — not as shells in the space frame:

- at each wall's top: the slabs' area nearest to it (shared with the beams, as theirs: structure_analysis.tributary),
  the reactions of the beams and columns resting on it (the frame's supports there), and what the walls above it
  bring down — each wall's load, with its own weight, passed to the walls under it by how long they run together;
- each storey's horizontal forces (the wind's, the earthquake's, each way) shared among its walls along that way by
  their in-plane stiffness (a cantilever's: bending and shear), the walls across taking none.

Characteristic loads (kN); the verification (step 3, core/ec6.py) combines them. Pure Python and NumPy."""

import math
from dataclasses import dataclass, field

import numpy as np

MASONRY_KN_M3 = 15.0            # kN/m³: a masonry wall's weight, plastered (structure_loads.WALL_KN_M3)
CONCRETE_KN_M3 = 25.0
SHEAR_MODULUS = 0.4             # G / E of masonry (EN 1996-1-1 3.7.3)
ALONG = math.cos(math.radians(45.0))    # a wall this near a way's direction (|cos|) takes its horizontal forces
NEAR_LEVEL = 0.50               # m: a wall's top this near a storey's level is that storey's
NET_LEAST = 0.10                # the least of a wall's length left for its load (its openings taken out)


@dataclass
class WallLoad:
    """A load-bearing wall's loads: its size, what comes down on it (characteristic, kN) and the horizontal forces it
    takes (characteristic, kN, each action)."""
    guid: str
    length: float               # m along its axis
    net: float                  # m: less its openings (what carries its load down)
    height: float
    t: float                    # m: its load-bearing thickness
    along: tuple = (1.0, 0.0)   # unit direction in plan
    top_g: float = 0.0          # kN at its top: slabs, beams and columns on it, the walls above
    top_q: float = 0.0
    slab_g: float = 0.0         # …of which the slabs' (their bearing's eccentricity)
    slab_q: float = 0.0
    one_side: float = 0.0       # 0 the slabs alike on both sides … 1 on one side only
    span: float = 0.0           # m: the longest of the spans of the slabs it carries
    self_g: float = 0.0         # kN: its own weight
    shear: dict = field(default_factory=dict)          # action (WX, WY, EX, EY) -> kN it takes
    base: tuple = None          # what it stands on (core.structural.AnalyticalModel.wall_bases)
    material: str = "masonry"
    storey: float = 0.0         # m: its storey's level over the foundations
    masonry: tuple = None       # (0.346) its type's own masonry (core/ec6); None: the project's

    @property
    def base_g(self):
        return self.top_g + self.self_g

    @property
    def base_q(self):
        return self.top_q


def net_length(wall):
    """A wall's length less its openings' widths (at least NET_LEAST of it)."""
    taken = sum(max(0.0, min(s1, wall.length) - max(s0, 0.0)) for s0, s1, _z0, _z1 in wall.openings)
    return max(wall.length - taken, NET_LEAST * wall.length)


def own_weight(wall):
    """kN: a wall's weight — its whole thickness, less its openings."""
    holes = sum(max(0.0, min(s1, wall.length) - max(s0, 0.0)) * max(0.0, min(z1, wall.top) - max(z0, wall.base))
                for s0, s1, z0, z1 in wall.openings)
    volume = max(0.0, wall.length * (wall.top - wall.base) - holes) * wall.thickness
    return volume * (CONCRETE_KN_M3 if wall.material == "concrete" else MASONRY_KN_M3)


def stiffness(wall, height=None):
    """A wall's in-plane stiffness as a cantilever (bending and shear), for its share of a storey's force — E taken
    as 1 (only the ratios count)."""
    h = float(height if height is not None else wall.top - wall.base)
    length, t = net_length(wall), wall.t
    if h <= 1e-6 or length <= 1e-6 or t <= 1e-6:
        return 0.0
    bending = h ** 3 / (3.0 * t * length ** 3 / 12.0)
    shear = 1.2 * h / (SHEAR_MODULUS * t * length)
    return 1.0 / (bending + shear)


def wall_loads(model, loads, slabs, reactions, lateral, low=None):
    """[WallLoad] of the model's load-bearing walls. slabs: {wall GlobalId: {"G", "Q": kN, "left", "right": m²,
    "span": m}} of the slabs at its top; reactions: {wall GlobalId: {"G", "Q": kN}} of the frame's members resting
    on it; lateral(storey, action) -> kN, its horizontal force (structure_analysis.lateral_force); low: the
    foundations' level."""
    from ..core import structural as st
    walls = list(getattr(model, "walls", ()))
    if not walls:
        return []
    low = min(w.base for w in walls) if low is None else low
    out = {}
    for w in walls:
        along = np.subtract(w.end, w.start) / max(w.length, 1e-9)
        s = slabs.get(w.guid, {})
        r = reactions.get(w.guid, {})
        left, right = s.get("left", 0.0), s.get("right", 0.0)
        out[w.guid] = WallLoad(w.guid, w.length, net_length(w), w.top - w.base, w.t, (float(along[0]), float(along[1])),
                               s.get("G", 0.0) + r.get("G", 0.0), s.get("Q", 0.0) + r.get("Q", 0.0),
                               s.get("G", 0.0), s.get("Q", 0.0),
                               abs(left - right) / (left + right) if left + right > 1e-9 else 0.0,
                               s.get("span", 0.0), own_weight(w), base=model.wall_bases.get(w.guid),
                               material=w.material, storey=w.top - low, masonry=getattr(w, "masonry", None))
    # from the top down: each wall's load to the walls under it, by how long they run together
    for w in sorted(walls, key=lambda w: -w.top):
        under = st.walls_under(w, walls)
        if not under:
            continue
        total = sum(run for _o, run in under)
        mine = out[w.guid]
        for o, run in under:
            share = run / total
            out[o.guid].top_g += mine.base_g * share
            out[o.guid].top_q += mine.base_q * share
    # each storey's horizontal forces: to its walls along each way, by their stiffness
    for st_ in loads.storeys:
        level = low + st_.level
        mine = [w for w in walls if abs(w.top - level) <= NEAR_LEVEL or w.base < level - NEAR_LEVEL < w.top]
        mine = [w for w in mine if w.base < level]
        for case, axis in (("WX", 0), ("WY", 1), ("EX", 0), ("EY", 1)):
            force = sum(lateral(s, case) for s in loads.storeys if s.level >= st_.level - 1e-6)
            if force <= 1e-9:
                continue
            ways = [w for w in mine if abs(out[w.guid].along[axis]) >= ALONG]
            ks = {w.guid: stiffness(w) for w in ways}
            total = sum(ks.values())
            for w in ways:
                if total > 1e-12:
                    out[w.guid].shear[case] = force * ks[w.guid] / total
    return [out[w.guid] for w in walls]


def ways_without_walls(walls_out):
    """The ways (X, Y) no load-bearing wall runs along — their horizontal forces left to the frame, or to none."""
    found = set()
    for w in walls_out:
        if abs(w.along[0]) >= ALONG:
            found.add("X")
        if abs(w.along[1]) >= ALONG:
            found.add("Y")
    return [way for way in ("X", "Y") if way not in found]
