"""Kitchens (0.170, Phase 10, step 1): a run of modules along the walls — straight, in L or in U — and the
worktop over its base units.

A run is the line the cabinets' backs go on (the walls' inner faces, in order: its legs) and the side the room is on.
Each leg is filled with modules (core.cabinets.fill: of 60 cm, the rest in a smaller usual width); a leg after a
corner starts clear of the first one's depth (its modules butt against the corner one's front). The worktop: over
the base units, a piece per leg (its modules' footprints, out to the overhang over their fronts), joined at the
corners — its outline, and its pieces as the cut list gives them.

Pure numpy and shapely; plan coordinates in metres, angles in degrees."""

import math

import numpy as np

from . import cabinets as core_cab

OVERHANG = 0.02                 # m: the worktop past the fronts
WORKTOP = 0.03                  # m: its thickness


def _unit(v):
    v = np.asarray(v, dtype=float)[:2]
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else v


def legs(points, side=1):
    """[(start (2,), direction (2,), length, out (2,))] of a run's legs: `points` its back line in order, `side`
    +1 with the room on the left of the first leg (looking along it), −1 on its right."""
    pts = [np.asarray(p, dtype=float)[:2] for p in points]
    out = []
    for a, b in zip(pts, pts[1:]):
        d = _unit(b - a)
        length = float(np.linalg.norm(b - a))
        if length < 1e-6:
            continue
        left = np.array((-d[1], d[0]))
        out.append((a, d, length, left * side))
    return out


def _inside(d0, d1, side):
    """Whether a run turns from d0 to d1 round an inside corner (the room inside it)."""
    return float(d0[0] * d1[1] - d0[1] * d1[0]) * side > 1e-6


CORNERS = ("blind", "l", "carousel")    # (0.239, 0.240) a kitchen's inside corners: blind units, L units (with a
#                                         carousel)


def run_modules(points, side=1, depth=None, kind="base", widths=None, corners=False):
    """[(back's middle (2,), angle, width)] of the modules of a run along `points` — for its base units (kind
    "base") or its wall units ("wall": their own, shallower depth for the corners). widths: [[w…] per leg] when
    given, else each leg filled (core.cabinets.fill). (0.239) corners: [(…, blind, corner side, (0.240) arm)] —
    each leg that ends in an inside corner ending in a corner unit flush in it, its other modules against it (what
    is left by the leg's start): a blind one (True or "blind": core.cabinets.corner_blind, corner_width; the next
    leg starts clear of it as before) or an L one ("l", "carousel": arms of core.cabinets.L_ARMS; the next leg
    starts past its second arm)."""
    c = core_cab.Cabinet.of(kind)
    depth = c.overall_depth if depth is None else depth
    shaped = corners in ("l", "carousel")
    out = []
    lg = legs(points, side)
    after = 0.0                                         # (the L unit's arm round the corner before this leg)
    for k, (a, d, length, _out) in enumerate(lg):
        start = 0.0
        if k > 0 and _inside(lg[k - 1][1], d, side):
            start = after or depth                      # (an inside corner: clear of the modules of the leg before)
        blind = corner = arm = after = 0.0
        if corners and widths is None and k + 1 < len(lg) and _inside(d, lg[k + 1][1], side):
            if shaped:
                corner = arm = core_cab.L_ARMS.get(kind, 0.0)
            else:
                blind = core_cab.corner_blind(depth)
                corner = core_cab.corner_width(blind)
            if not corner or corner > length - start + 1e-9 or arm > lg[k + 1][2]:
                blind = corner = arm = 0.0              # (too short a leg for one: as before)
            after = arm
        if widths is not None and k < len(widths):
            row = widths[k]
        elif corner:
            row = core_cab.fill(length - start - corner) + [corner]
        else:
            row = core_cab.fill(length - start)
        # (its width along the leg, its front to the room: with the room on the right it is turned round)
        angle = math.degrees(math.atan2(d[1], d[0])) + (0.0 if side > 0 else 180.0)
        x = length - sum(row) if corner else start     # (against the corner unit, flush in the corner)
        for j, w in enumerate(row):
            spot = (a + d * (x + w / 2), angle % 360.0, w)
            if corners:                                 # (the corner at the leg's end: its cabinet's x end, or 0)
                last = corner and j == len(row) - 1
                spot += (blind if last else 0.0, ("right" if side > 0 else "left") if last else "right",
                         arm if last else 0.0)
            out.append(spot)
            x += w
    return out


def footprint(back_mid, angle, width, depth, overhang=0.0):
    """The plan rectangle of a cabinet (4 corners) — out to `overhang` past its front."""
    a = math.radians(angle)
    x = np.array((math.cos(a), math.sin(a)))
    y = np.array((-x[1], x[0]))
    o = np.asarray(back_mid, dtype=float)[:2] - x * width / 2
    d = depth + overhang
    return [o, o + x * width, o + x * width + y * d, o + y * d]


def arm_footprint(back_mid, angle, width, depth, arm, corner_side="right", overhang=0.0):
    """(0.240) The plan rectangle of an L corner unit's second arm past its first's front (4 corners) — out to
    `overhang` past its own."""
    a = math.radians(angle)
    x = np.array((math.cos(a), math.sin(a)))
    y = np.array((-x[1], x[0]))
    o = np.asarray(back_mid, dtype=float)[:2] - x * width / 2
    d = depth + overhang
    u0, u1 = (width - d, width) if corner_side == "right" else (0.0, d)
    return [o + x * u0 + y * d, o + x * u1 + y * d, o + x * u1 + y * arm, o + x * u0 + y * arm]


def worktop(cabinets, overhang=OVERHANG):
    """(outline [(x, y)] or None, [(length, width)] its pieces) of the worktop over these base units: [(back's
    middle, angle, width, depth[, arm, corner side])] — a piece per direction (a leg) from its first module to its
    last (over a gap left for a machine too), joined at the corners; (0.240) an L corner unit's second arm with the
    leg round the corner."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    if not cabinets:
        return None, []
    by_way = {}
    for spot in cabinets:
        mid, angle, width, depth = spot[:4]
        key = round(angle % 360.0, 1)
        by_way.setdefault(key, []).append(Polygon(footprint(mid, angle, width, depth, overhang)))
        arm, corner_side = (spot[4], spot[5]) if len(spot) > 5 else (0.0, "right")
        if arm:
            turn = 90.0 if corner_side == "right" else -90.0
            by_way.setdefault(round((angle + turn) % 360.0, 1), []).append(
                Polygon(arm_footprint(mid, angle, width, depth, arm, corner_side, overhang)))
    pieces, polys = [], []
    for angle, rects in sorted(by_way.items()):
        u = unary_union(rects).convex_hull            # (a leg's piece spans its modules, a gap between them too)
        polys.append(u)
        a = math.radians(angle)
        x = np.array((math.cos(a), math.sin(a)))
        y = np.array((-x[1], x[0]))
        pts = np.array(u.convex_hull.exterior.coords)
        pieces.append((float(np.ptp(pts @ x)), float(np.ptp(pts @ y))))
    whole = unary_union(polys).buffer(1e-6, join_style=2).buffer(-1e-6, join_style=2)
    if whole.geom_type != "Polygon":
        whole = max(getattr(whole, "geoms", [whole]), key=lambda g: g.area)
    whole = whole.simplify(1e-5, preserve_topology=True)      # (0.240: no corner where two pieces only meet)
    ring = [tuple(float(v) for v in p) for p in list(whole.exterior.coords)[:-1]]
    return ring, pieces
