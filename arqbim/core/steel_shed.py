"""(0.499) A steel shed — the «pórtico de nave», the industrial building an architect draws first in steel: portal
frames along its length (two columns, two rafters to the ridge), purlins over the rafters, X bracing in the end bays
(in both walls and both slopes of the roof). Pure geometry: each piece as a line in space (its function, its section
by role, its insertion point, its turn), which knees and ridges are mitred, which columns get a base plate. The model
(model/bim.steel_shed) makes them.

Lines run through the sections' middles (insertion point 5), so that a column and its rafter meet at the knee on their
axes and the mitre falls right; the columns are turned so that their depth lies in their frame's plane (their strong
axis resists the frame's bending); the purlins sit on the rafters (their bottom middle on the rafter's top) and lean
with the roof."""

import math
from dataclasses import dataclass, field

import numpy as np

Z = np.array((0.0, 0.0, 1.0))


@dataclass
class Piece:
    role: str                   # "column" | "rafter" | "purlin" | "brace"
    function: str               # the Peça metálica's: column, beam, purlin, brace
    start: np.ndarray
    end: np.ndarray
    cardinal: int = 5
    rotation: float = 0.0


@dataclass
class Shed:
    pieces: list = field(default_factory=list)
    mitres: list = field(default_factory=list)          # [(index, index)] of pieces cut to a mitre
    plates: list = field(default_factory=list)          # [index] of columns given a base plate
    frames: int = 0
    span: float = 0.0
    length: float = 0.0


DEFAULTS = {"span": 12.0, "eave": 6.0, "slope": 10.0, "spacing": 6.0, "purlins": 1.5, "bracing": True,
            "plates": True}


def _turn_for(depth_dir, axis):
    """The Peça metálica's rotation (degrees) that lays a section's depth (its own y) along `depth_dir`, for a piece
    along `axis` (classify.segment_placement's frame: x level across — for an upright one, the red axis —, y = z × x)."""
    axis = axis / np.linalg.norm(axis)
    x = np.cross(Z, axis)
    if np.linalg.norm(x) < 1e-9:
        x = np.array((1.0, 0.0, 0.0))
    x /= np.linalg.norm(x)
    y = np.cross(axis, x)
    nx, ny = float(depth_dir @ x), float(depth_dir @ y)
    return math.degrees(math.atan2(-nx, ny))


def layout(origin, direction, length, span=12.0, eave=6.0, slope=10.0, spacing=6.0, purlins=1.5, bracing=True,
           plates=True, rafter_depth=0.36, purlin_lift=0.0):
    """The shed along `direction` (level) from `origin` (its first column line's foot), `length` m long, `span` m
    wide to the left of it, its eaves `eave` m high, its roof at `slope` degrees to a ridge in the middle, frames about
    every `spacing` m (the same between all of them), purlins about every `purlins` m along each slope; bracing in the
    end bays; base plates. rafter_depth: the rafters' depth (m) — the purlins sit on their tops."""
    origin = np.asarray(origin, dtype=float)
    a = np.asarray(direction, dtype=float).copy()
    a[2] = 0.0
    a /= np.linalg.norm(a)
    s = np.cross(Z, a)                                   # (the span: to the left of the length)
    n = max(2, int(round(length / spacing)) + 1)
    step = length / (n - 1)
    rise = math.tan(math.radians(slope)) * span / 2.0
    out = Shed(frames=n, span=span, length=length)
    column_turn = _turn_for(s, Z)
    frames = []
    for i in range(n):
        base = origin + a * (step * i)
        left, right = base, base + s * span
        eave_l, eave_r = left + Z * eave, right + Z * eave
        apex = base + s * (span / 2.0) + Z * (eave + rise)
        k = len(out.pieces)
        out.pieces += [Piece("column", "column", left, eave_l, 5, column_turn),
                       Piece("rafter", "beam", eave_l, apex, 5, _turn_for(_up_normal(apex - eave_l, a), apex - eave_l)),
                       Piece("rafter", "beam", apex, eave_r, 5, _turn_for(_up_normal(eave_r - apex, a), eave_r - apex)),
                       Piece("column", "column", right, eave_r, 5, column_turn)]
        out.mitres += [(k, k + 1), (k + 1, k + 2), (k + 2, k + 3)]
        if plates:
            out.plates += [k, k + 3]
        frames.append((left, right, eave_l, eave_r, apex))
    # the purlins: on the rafters' tops, the length of the shed, about every `purlins` m from each eave to the ridge
    slope_len = math.hypot(span / 2.0, rise)
    count = max(2, int(math.ceil((slope_len - 0.2) / purlins)) + 1)
    first, last = frames[0], frames[-1]
    for side in (0, 1):
        eave_pt, apex = (first[2], first[4]) if side == 0 else (first[3], first[4])
        down = eave_pt - apex
        up_normal = _up_normal(apex - eave_pt, a)
        lift = up_normal * (rafter_depth / 2.0 + purlin_lift)
        for j in range(count):
            t = 0.1 + (slope_len - 0.2) * j / (count - 1)
            point = apex + down / np.linalg.norm(down) * (slope_len - t) + lift
            out.pieces.append(Piece("purlin", "purlin", point, point + a * length, 2, _turn_for(up_normal, a)))
    if bracing and n >= 2:
        for bay in sorted({0, n - 2}):
            f0, f1 = frames[bay], frames[bay + 1]
            for foot, head in ((0, 2), (1, 3)):                       # (the walls: left and right)
                out.pieces += [Piece("brace", "brace", f0[foot], f1[head]), Piece("brace", "brace", f0[head], f1[foot])]
            for eave_i in (2, 3):                                     # (the roof: each slope, over the rafters)
                lift = _up_normal(f0[4] - f0[eave_i], a) * (rafter_depth / 2.0 + 0.03)
                out.pieces += [Piece("brace", "brace", f0[eave_i] + lift, f1[4] + lift),
                               Piece("brace", "brace", f0[4] + lift, f1[eave_i] + lift)]
    return out


def _up_normal(along, a):
    """The normal of a roof slope that rises along `along` (in its frame's plane) and runs along `a`: up."""
    n = np.cross(a, along)
    n /= np.linalg.norm(n)
    return n if n[2] >= 0 else -n
