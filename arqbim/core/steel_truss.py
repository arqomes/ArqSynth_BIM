"""(0.507) A steel truss — the «treliça» of the plan's step 4 (DetailCraft's Pratt, Warren, Howe): two chords, level
and parallel, between two points, `height` apart, cut into panels about `panel` m long (an even number, so that it is
the same both ways from its middle), and its web — verticals and diagonals — between them:

- Pratt: verticals at every panel point, the diagonals going down towards the middle (in tension under gravity);
- Howe: verticals too, the diagonals going up towards the middle (in compression);
- Warren: no verticals but at its ends, the diagonals turning one way and the other (a zigzag).

Pure geometry, as core/steel_shed: each piece a line in space (its role — chord, vertical, diagonal —, the Peça
metálica's function); lines through the sections' middles, meeting at the nodes. The model (model/bim.steel_truss)
makes them."""

from dataclasses import dataclass, field

import numpy as np

Z = np.array((0.0, 0.0, 1.0))
KINDS = ("pratt", "howe", "warren")
DEFAULTS = {"kind": "pratt", "height": 1.2, "panel": 1.5, "elevation": 3.0}


@dataclass
class Piece:
    role: str                   # "chord" | "vertical" | "diagonal"
    function: str               # the Peça metálica's
    start: np.ndarray
    end: np.ndarray
    cardinal: int = 5
    rotation: float = 0.0


@dataclass
class Truss:
    pieces: list = field(default_factory=list)
    panels: int = 0
    span: float = 0.0
    height: float = 0.0


def panels_for(span, panel):
    """How many panels a span takes, about `panel` m each: an even number, at least 2."""
    n = max(2, int(round(span / max(panel, 0.1))))
    return n + (n % 2)


def layout(start, end, kind="pratt", height=1.2, panel=1.5, elevation=3.0):
    """The truss from `start` to `end` (seen from above; their height: the level it stands on), its bottom chord
    `elevation` m over it, its top chord `height` m over that."""
    if kind not in KINDS:
        raise ValueError(kind)
    a = np.asarray(start, dtype=float).copy()
    b = np.asarray(end, dtype=float).copy()
    b[2] = a[2]
    span = float(np.linalg.norm(b - a))
    if span < 1e-6 or height <= 0.0:
        raise ValueError("a truss needs a span and a height")
    u = (b - a) / span
    n = panels_for(span, panel)
    bottom = [a + u * (span * i / n) + Z * elevation for i in range(n + 1)]
    top = [p + Z * height for p in bottom]
    out = Truss(panels=n, span=span, height=height)
    out.pieces += [Piece("chord", "member", bottom[0], bottom[-1]), Piece("chord", "member", top[0], top[-1])]
    verticals = range(n + 1) if kind in ("pratt", "howe") else (0, n)
    out.pieces += [Piece("vertical", "member", bottom[i], top[i]) for i in verticals]
    half = n // 2
    for i in range(n):
        if kind == "warren":
            down = i % 2 == 0                       # (from the top at i down to the bottom at i + 1, then back up)
        else:
            towards_middle_down = i < half          # (the left half's diagonals fall towards the middle — Pratt)
            down = towards_middle_down if kind == "pratt" else not towards_middle_down
        p, q = (top[i], bottom[i + 1]) if down else (bottom[i], top[i + 1])
        out.pieces.append(Piece("diagonal", "member", p, q))
    return out
