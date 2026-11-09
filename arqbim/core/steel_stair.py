"""(0.509) A steel stair — the plan's step 4: a straight flight of open treads between two stringers of channel
(UPN), as the workshops make them: the treads of grating («grelha», 30 mm) or of folded chequered plate («chapa
xadrez», 6 mm with a 40 mm lip down its nosing), each over the one below by a nosing; the stringers' webs facing the
treads (their inner faces at the stair's sides), their top edges a little over the treads' nosings, parallel to
them; each stringer cut level at its foot (standing on the floor) and plumb at its head (against the edge of the
floor above, the last riser's line), its top flush with that floor.

Pure geometry in the stair's own frame — its foot (the middle of its first riser, at the floor) at 0, 0, 0, going
along +x, +y to its left —, as core/stairs. The model (ifc/steel_stairs) makes it."""

import math

from .stairs import MAX_RISER, risers

TREADS = ("grelha", "chapa")
TREAD_T = {"grelha": 0.030, "chapa": 0.006}
LIP = 0.040                     # m: a chequered plate tread's lip folded down its nosing
NOSING = 0.030                  # m: a tread over the one below
OVER = 0.030                    # m: the stringers' top edges over the line of the nosings (square to it)
STRINGERS = ("UPN160", "UPN180", "UPN200", "UPN220", "UPN240")


def treads(rise, going, tread="grelha", max_riser=MAX_RISER):
    """The treads: [(x front, x back, top z, its outline in x-z — counter-clockwise)] — n − 1 of them for n risers
    (the last riser lands on the floor above)."""
    n, h = risers(rise, max_riser)
    t = TREAD_T[tread]
    out = []
    for k in range(n - 1):
        x0, x1, top = k * going - NOSING, (k + 1) * going, (k + 1) * h
        if tread == "chapa":
            ring = [(x0, top - LIP), (x0 + t, top - LIP), (x0 + t, top - t), (x1, top - t), (x1, top), (x0, top)]
        else:
            ring = [(x0, top - t), (x1, top - t), (x1, top), (x0, top)]
        out.append((x0, x1, top, ring))
    return out


def stringer(rise, going, depth, max_riser=MAX_RISER):
    """A stringer's line in x-z — (start, end), drawn out past its cuts — and its cuts: [(end, point, normal)]
    (x-z-…: the side the normal points to taken away): level at the floor (its foot), plumb at the last riser's line and
    level at the floor above (its head). depth: the channel's (m)."""
    n, h = risers(rise, max_riser)
    s = h / going
    k = math.sqrt(1.0 + s * s)
    tx, tz = 1.0 / k, s / k                               # (along it, up the slope)
    nx, nz = -s / k, 1.0 / k                              # (square to it, up)
    off = OVER - depth / 2.0                              # (its middle from the nosings' line, square to it)
    cx, cz = 0.0 + nx * off, h + nz * off                 # (a point of its middle line)
    low = -depth / 2.0 * k - 0.02                         # (its whole section under the floor there)
    head_x = (n - 1) * going
    a = (low - cz) / tz
    b = (head_x + depth - cx) / tx                        # (its whole section past the plumb cut)
    start = (cx + tx * a, cz + tz * a)
    end = (cx + tx * b, cz + tz * b)
    cuts = [(0, (0.0, 0.0), (0.0, -1.0)), (1, (head_x, 0.0), (1.0, 0.0)), (1, (0.0, rise), (0.0, 1.0))]
    return start, end, cuts


def side(width, flange):
    """(m) A stringer's line from the stair's axis: its section's middle half its flange's width out of the side."""
    return width / 2.0 + flange / 2.0
