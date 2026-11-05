"""Roofs by blocks (0.262), as the ArqSynth Modeler add-on's "telhado por blocos": a roof put together from
rectangular blocks — each its own size, place and turn, each of its four sides (N, E, S, W: its local +y, +x, −y,
−x) a slope (a "water") or a gable, with its own slope and eave height, and an overhang. Pure geometry.

One block: each sloping side a plane rising inwards from its eave — the eave being the roof's top over the walls'
line (the block's rectangle), as the program's other roofs: z = eave_s + tan(slope_s) · (distance in from the
side). Its waters: the rectangle grown by the overhang, each side's plane where it is the lowest of them (so hips
and ridges come out of the planes, whatever their slopes and eaves). A block with no water: flat, at its highest
eave.

Blocks together: their upper envelope — at each point the highest of the blocks over it — so valleys come out
where blocks meet, whatever their sizes, turns and heights. A higher block's overhang passes over a lower block's
own rectangle without cutting it (the add-on's rule); two overhangs over each other, out of both rectangles, leave
the higher. The result: the regions of the roof's top, each on one plane (merged when two blocks share a plane) —
and (0.265) its edges classified as the add-on's roof frame model does: eaves, ridges, hips, valleys, gables."""

import json
import math
from dataclasses import dataclass, replace

import numpy as np

SIDES = ("N", "E", "S", "W")
FORMS = ("hip", "gable", "gable_across", "shed", "flat")
MIN_SIZE = 0.20             # m: a block at least this wide and deep
_GRID = 1e-7


@dataclass(frozen=True)
class Block:
    cx: float                   # its middle (plan, in the roof's frame)
    cy: float
    angle: float                # degrees: its local x from the roof's x, counter-clockwise
    width: float                # along its local x
    depth: float                # along its local y
    overhang: float = 0.5
    water: tuple = (True, True, True, True)            # N, E, S, W: a slope, or a gable
    slope: tuple = (30.0, 30.0, 30.0, 30.0)            # degrees
    eave: tuple = (0.0, 0.0, 0.0, 0.0)                 # its top over the walls' line on that side, over the roof's level

    def side(self, name):
        k = SIDES.index(name)
        return self.water[k], self.slope[k], self.eave[k]

    @property
    def flat(self):
        return not any(self.water)


def make(cx, cy, angle, width, depth, form="hip", slope=30.0, overhang=0.5, eave=0.0):
    """A block of a form: four waters (hip), two (gable: its ridge along its longer side; gable_across: along its
    shorter), one (shed: falling to its −y side) or none (flat)."""
    long_x = width >= depth
    water = {"hip": (True, True, True, True),
             "gable": (True, False, True, False) if long_x else (False, True, False, True),
             "gable_across": (False, True, False, True) if long_x else (True, False, True, False),
             "shed": (False, False, True, False),
             "flat": (False, False, False, False)}[form]
    return Block(float(cx), float(cy), float(angle), float(width), float(depth), float(overhang), water,
                 (float(slope),) * 4, (float(eave),) * 4)


def form_of(block):
    """The block's form, as `make` names them (any other mix of waters: "custom")."""
    for form in FORMS:
        if make(0, 0, 0, block.width, block.depth, form).water == tuple(block.water):
            return form
    return "custom"


def problem(block):
    """What makes a block unusable, or None (a refusal key)."""
    if block.width < MIN_SIZE or block.depth < MIN_SIZE:
        return "block_too_small"
    if block.overhang < 0 or any(not 0.0 <= s < 80.0 for s, w in zip(block.slope, block.water) if w):
        return "roof_slope"
    return None


# ---------------------------------------------------------------- text (the IFC's ArqSynth_Parametros.Blocos)

def to_text(blocks):
    return json.dumps([{"c": [round(b.cx, 6), round(b.cy, 6)], "a": round(b.angle, 6), "w": round(b.width, 6),
                        "d": round(b.depth, 6), "o": round(b.overhang, 6), "agua": [int(x) for x in b.water],
                        "incl": [round(x, 4) for x in b.slope], "beirado": [round(x, 6) for x in b.eave]}
                       for b in blocks], separators=(",", ":"))


def from_text(text):
    out = []
    try:
        items = json.loads(text or "[]")
    except ValueError:
        return out
    for it in items:
        try:
            out.append(Block(float(it["c"][0]), float(it["c"][1]), float(it.get("a", 0.0)), float(it["w"]),
                             float(it["d"]), float(it.get("o", 0.0)), tuple(bool(x) for x in it["agua"]),
                             tuple(float(x) for x in it["incl"]), tuple(float(x) for x in it["beirado"])))
        except (KeyError, TypeError, ValueError, IndexError):
            continue
    return out


# ---------------------------------------------------------------- one block

def _axes(block):
    a = math.radians(block.angle)
    return np.array((math.cos(a), math.sin(a))), np.array((-math.sin(a), math.cos(a)))


def rect(block, grow=0.0):
    """Its rectangle (grown by `grow`) in the roof's frame: [(x, y)…] counter-clockwise."""
    ex, ey = _axes(block)
    c = np.array((block.cx, block.cy))
    hw, hd = block.width / 2 + grow, block.depth / 2 + grow
    return [tuple(c + ex * sx * hw + ey * sy * hd) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def planes(block):
    """{side: (a, b, c)} its sloping sides' planes z = a·x + b·y + c (the roof's frame; z over the roof's level).
    A flat block: {"top": (0, 0, its highest eave)}."""
    if block.flat:
        return {"top": (0.0, 0.0, max(block.eave))}
    ex, ey = _axes(block)
    c = np.array((block.cx, block.cy))
    out = {}
    for name, inward, half in (("N", -ey, block.depth / 2), ("S", ey, block.depth / 2),
                               ("E", -ex, block.width / 2), ("W", ex, block.width / 2)):
        water, slope, eave = block.side(name)
        if not water:
            continue
        t = math.tan(math.radians(slope))
        edge = c - inward * half                             # (a point of that side's line)
        # z = eave + t · (p − edge)·inward
        out[name] = (float(t * inward[0]), float(t * inward[1]), float(eave - t * float(edge @ inward)))
    return out


def _value(coeff, x, y):
    return coeff[0] * x + coeff[1] * y + coeff[2]


def _clip(poly, a, b, c):
    """The convex polygon's part where a·x + b·y + c ≥ 0 (Sutherland–Hodgman)."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] + c, a * q[0] + b * q[1] + c
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            s = fp / (fp - fq)
            out.append((p[0] + (q[0] - p[0]) * s, p[1] + (q[1] - p[1]) * s))
    clean = []                                                   # (no corner twice: a cut through a corner)
    for p in out:
        if not clean or math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 1e-9:
            clean.append(p)
    while len(clean) > 1 and math.hypot(clean[0][0] - clean[-1][0], clean[0][1] - clean[-1][1]) <= 1e-9:
        clean.pop()
    return clean


def facets(block):
    """Its waters: [(side, (a, b, c), [(x, y)…] convex)] — each side's plane over the grown rectangle where it is
    the lowest of its planes."""
    pl = planes(block)
    outline = rect(block, block.overhang)
    out = []
    for name, coeff in pl.items():
        poly = list(outline)
        for other, oc in pl.items():
            if other != name:                                    # (where coeff ≤ other's)
                poly = _clip(poly, oc[0] - coeff[0], oc[1] - coeff[1], oc[2] - coeff[2])
                if len(poly) < 3:
                    break
        if len(poly) >= 3 and abs(_area(poly)) > 1e-8:
            out.append((name, coeff, poly))
    return out


def _area(poly):
    return 0.5 * sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1]))


def block_top(block, x, y):
    """Its top over a plan point, or None outside its grown rectangle."""
    from shapely.geometry import Point, Polygon
    if not Polygon(rect(block, block.overhang)).buffer(1e-9).contains(Point(x, y)):
        return None
    return min(_value(c, x, y) for c in planes(block).values())


# ---------------------------------------------------------------- blocks together

def regions(blocks):
    """The roof's top: [((a, b, c), shapely (Multi)Polygon)] — each plane's visible part (what no other block's
    water is higher than: its overhang passing over a lower block's own rectangle, not hiding it), the parts of one
    plane merged."""
    import shapely
    from shapely.geometry import Polygon
    all_facets = [(k, f) for k, b in enumerate(blocks) for f in facets(b)]
    cores = [Polygon(rect(b)) for b in blocks]
    by_plane = {}
    for k, (_side, coeff, poly) in all_facets:
        hidden = []
        for j, (_s2, oc, other) in all_facets:
            if j == k:
                continue
            if all(abs(u - v) < 1e-9 for u, v in zip(oc, coeff)):
                if j > k:                                       # (one plane: the first block's part kept)
                    continue
                higher = other
            else:                                               # (where it is higher: up to the valley exactly)
                higher = _clip(other, oc[0] - coeff[0], oc[1] - coeff[1], oc[2] - coeff[2])
            if len(higher) < 3 or abs(_area(higher)) <= 1e-10:
                continue
            shape = Polygon(higher)
            if blocks[j].overhang > 1e-9:                       # (its overhang over this block's own rectangle)
                shape = shapely.difference(shape, shapely.difference(cores[k], cores[j], grid_size=_GRID),
                                           grid_size=_GRID)
            if not shape.is_empty and shape.area > 1e-10:
                hidden.append(shape)
        mine = Polygon(poly)
        if hidden:
            mine = shapely.difference(mine, shapely.union_all(hidden, grid_size=_GRID), grid_size=_GRID)
        if mine.is_empty or mine.area < 1e-8:
            continue
        key = tuple(round(v, 6) for v in coeff)
        by_plane.setdefault(key, (coeff, []))[1].append(mine)
    out = []
    for coeff, parts in by_plane.values():
        merged = shapely.union_all(parts, grid_size=_GRID)
        merged = shapely.remove_repeated_points(merged, 1e-9).simplify(0.0)
        if not merged.is_empty and merged.area > 1e-8:
            out.append((coeff, merged))
    return out


def polygons(geometry):
    """A shapely geometry's polygons."""
    return [g for g in getattr(geometry, "geoms", [geometry]) if g.geom_type == "Polygon" and not g.is_empty]


def top_plane_at(blocks, x, y):
    """The plane of the roof's top over a plan point (the highest of the blocks over it), or None."""
    best = None
    for b in blocks:
        z = block_top(b, x, y)
        if z is None:
            continue
        coeff = min(planes(b).values(), key=lambda c: _value(c, x, y))
        if best is None or z > best[0] + 1e-9:
            best = (z, coeff)
    return None if best is None else best[1]


def height_at(blocks, x, y):
    """The roof's top over a plan point (over the roof's level), or None outside it."""
    coeff = top_plane_at(blocks, x, y)
    return None if coeff is None else _value(coeff, x, y)


def underside_at(blocks, x, y, thickness):
    """Its underside over a plan point: its top less its thickness, upright (thickness / cos(slope))."""
    coeff = top_plane_at(blocks, x, y)
    if coeff is None:
        return None
    return _value(coeff, x, y) - thickness * math.sqrt(1.0 + coeff[0] ** 2 + coeff[1] ** 2)


def breaks(blocks, a, b):
    """Where along a → b (plan) the roof's top changes plane: [0…1], the ends included — where the line crosses a
    region's edge (an eave, a hip, a ridge, a valley)."""
    a, b = np.asarray(a, dtype=float)[:2], np.asarray(b, dtype=float)[:2]
    d = b - a
    out = {0.0, 1.0}
    for _coeff, geometry in regions(blocks):
        for poly in polygons(geometry):
            for ring in [poly.exterior] + list(poly.interiors):
                pts = np.asarray(ring.coords, dtype=float)
                for q, r in zip(pts, pts[1:]):
                    e = r - q
                    den = d[0] * e[1] - d[1] * e[0]
                    if abs(den) < 1e-12:
                        continue
                    w = q - a
                    s = (w[0] * e[1] - w[1] * e[0]) / den
                    u = (w[0] * d[1] - w[1] * d[0]) / den
                    if 1e-9 < s < 1 - 1e-9 and -1e-9 <= u <= 1 + 1e-9:
                        out.add(round(float(s), 9))
    return sorted(out)


def footprint(blocks, grow=False):
    """The plan the blocks cover (their rectangles; grown by their overhangs) — a shapely geometry."""
    import shapely
    from shapely.geometry import Polygon
    return shapely.union_all([Polygon(rect(b, b.overhang if grow else 0.0)) for b in blocks])


def moved(blocks, dx, dy):
    return [replace(b, cx=b.cx + dx, cy=b.cy + dy) for b in blocks]


def side_way(block, k):
    """(0.264) Side k's (0..3: N, E, S, W) outward way (unit, in the block's frame's plan) and its distance from the
    block's middle."""
    ex, ey = _axes(block)
    return [(ey, block.depth / 2), (ex, block.width / 2), (-ey, block.depth / 2), (-ex, block.width / 2)][k]


def stretched(block, k, s):
    """(0.264) The block with its side k taken `s` out (in, if negative) — the opposite side where it was, as the
    add-on's roof block stretch."""
    out, _half = side_way(block, k)
    c = np.array((block.cx, block.cy)) + out * s / 2
    size = {"depth": block.depth + s} if k in (0, 2) else {"width": block.width + s}
    return replace(block, cx=float(c[0]), cy=float(c[1]), **size)


def with_all(blocks, slope=None, overhang=None):
    """The blocks with one slope for all their waters / one overhang (the roof's Properties)."""
    out = []
    for b in blocks:
        if slope is not None:
            b = replace(b, slope=(float(slope),) * 4)
        if overhang is not None:
            b = replace(b, overhang=float(overhang))
        out.append(b)
    return out


def mirrored(block, mat):
    """The block reflected by a plan reflection 4x4 `mat` (ifc/mirror.reflection): its middle reflected, its x
    reflected; its local y would turn round — so its N and S sides change places."""
    c = mat @ np.array((block.cx, block.cy, 0.0, 1.0))
    ex, _ey = _axes(block)
    x = mat[:3, :3] @ np.array((ex[0], ex[1], 0.0))
    swap = lambda v: (v[2], v[1], v[0], v[3])                # noqa: E731  (N <-> S)
    return replace(block, cx=float(c[0]), cy=float(c[1]), angle=math.degrees(math.atan2(x[1], x[0])),
                   water=swap(block.water), slope=swap(block.slope), eave=swap(block.eave))


# ---------------------------------------------------------------- its edges (0.265)

EDGE_KINDS = ("eave", "ridge", "hip", "valley", "gable", "top")
LEVEL_DEG = 5.0             # an edge rising less than this: level (the add-on's HORIZONTAL_TOL_DEG)
_EDGE_GRID = 1e-6           # (the regions' edges met on this grid: a T-junction's corner lies on its neighbour's edge)


def _pieces(geometry):
    """The straight pieces [((x, y), (x, y))] of the lines in a shapely geometry (its points left out)."""
    out = []
    for g in getattr(geometry, "geoms", [geometry]):
        if g.is_empty:
            continue
        if g.geom_type in ("MultiLineString", "GeometryCollection"):
            out += _pieces(g)
        elif g.geom_type in ("LineString", "LinearRing"):
            pts = list(g.coords)
            out += [(tuple(p), tuple(q)) for p, q in zip(pts, pts[1:]) if math.dist(p, q) > 1e-7]
    return out


def _level(za, zb, a, b):
    run = math.dist(a, b)
    return abs(zb - za) <= math.hypot(run, zb - za) * math.sin(math.radians(LEVEL_DEG))


def _joint(ci, cj, polygon, a, b, za, zb):
    """Two waters meeting along a → b: over (convex — a ridge if level, else a hip) or under (a valley)."""
    from shapely.geometry import Point
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    d = np.array((b[0] - a[0], b[1] - a[1]))
    n = np.array((-d[1], d[0])) / max(float(np.hypot(*d)), 1e-12)
    if not polygon.contains(Point(m[0] + n[0] * 1e-4, m[1] + n[1] * 1e-4)):
        n = -n                                              # (n into the first water)
    q = (m[0] - n[0] * 0.01, m[1] - n[1] * 0.01)            # (a point of the other's side)
    if _value(ci, *q) < _value(cj, *q):                     # (the first's plane under the other's there: a valley)
        return "valley"
    return "ridge" if _level(za, zb, a, b) else "hip"


def edges(blocks, found=None):
    """The roof's edges, classified as the add-on's roof frame model: [(kind, (x, y, z), (x, y, z))] in the blocks'
    frame (z over the roof's level). Two waters meeting at the same height: over — "ridge" (level) or "hip"
    (sloping) — or under, "valley". An edge of one water only: "gable" if it slopes; level, "eave" at its foot or
    "top" at its head (a shed's high edge, a lower roof's under a higher one). Where two waters meet at different
    heights (a step), each has its own edge there. `found`: their regions, if already worked out."""
    import shapely
    regs = [(c, p) for c, g in (regions(blocks) if found is None else found) for p in polygons(g)]
    out, shared = [], [[] for _ in regs]
    for i in range(len(regs)):
        ci, pi = regs[i]
        for j in range(i + 1, len(regs)):
            cj, pj = regs[j]
            if not pi.buffer(_EDGE_GRID).intersects(pj):
                continue
            common = shapely.intersection(pi.boundary, pj.boundary, grid_size=_EDGE_GRID)
            for a, b in _pieces(common):
                za, zb = _value(ci, *a), _value(ci, *b)
                if abs(za - _value(cj, *a)) > 1e-5 or abs(zb - _value(cj, *b)) > 1e-5:
                    continue
                shared[i].append((a, b))
                shared[j].append((a, b))
                out.append((_joint(ci, cj, pi, a, b, za, zb), (a[0], a[1], za), (b[0], b[1], zb)))
    from shapely.geometry import LineString
    for i, (c, p) in enumerate(regs):
        free = p.boundary
        if shared[i]:
            free = shapely.difference(free, shapely.union_all([LineString(s) for s in shared[i]]),
                                      grid_size=_EDGE_GRID)
        zs = [_value(c, x, y) for x, y in p.exterior.coords]
        middle = (min(zs) + max(zs)) / 2
        flat = abs(c[0]) < 1e-12 and abs(c[1]) < 1e-12
        for a, b in _pieces(free):
            za, zb = _value(c, *a), _value(c, *b)
            if not _level(za, zb, a, b):
                kind = "gable"
            else:
                kind = "eave" if flat or (za + zb) / 2 <= middle + 1e-9 else "top"
            out.append((kind, (a[0], a[1], za), (b[0], b[1], zb)))
    return out


def edge_lengths(blocks, found=None):
    """{kind: its edges' true length (m)} for every kind of EDGE_KINDS."""
    total = {k: 0.0 for k in EDGE_KINDS}
    for kind, a, b in edges(blocks, found):
        total[kind] += math.dist(a, b)
    return total


