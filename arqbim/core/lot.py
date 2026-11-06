"""(0.423) The lot («o lote»): its outline in plan, its sides («estremas») and which of them face the street («frente
para a via pública») — and what the Verifier's town-planning rules read from it: which side is the front, the sides,
the back; how far the building stands from each.

An outline is [(x, y)] in the program's coordinates, counter-clockwise; side k runs from corner k to corner k+1.
"""

import math

import numpy as np

FRONT, SIDE, BACK = "frente", "lateral", "posterior"


def ring(outline):
    """The outline as a counter-clockwise list of (x, y), without its closing repeat — or None (fewer than three
    corners, no area)."""
    pts = [(float(x), float(y)) for x, y in outline]
    if len(pts) > 1 and np.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1e-9:
        pts = pts[:-1]
    if len(pts) < 3:
        return None
    a = area_signed(pts)
    if abs(a) < 1e-6:
        return None
    return pts if a > 0 else pts[::-1]


def area_signed(pts):
    x = np.array([p[0] for p in pts])
    y = np.array([p[1] for p in pts])
    return float(0.5 * (np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def area(outline):
    r = ring(outline)
    return abs(area_signed(r)) if r else 0.0


def sides(outline):
    """[(a, b)] of its sides, each from a corner to the next (counter-clockwise)."""
    r = ring(outline) or []
    return [(r[k], r[(k + 1) % len(r)]) for k in range(len(r))]


def outward(a, b):
    """A side's outward normal (unit), the outline being counter-clockwise: to its right."""
    d = np.array((b[0] - a[0], b[1] - a[1]), dtype=float)
    n = np.array((d[1], -d[0]))
    length = np.linalg.norm(n)
    return n / length if length > 1e-12 else n


def side_length(a, b):
    return float(math.hypot(b[0] - a[0], b[1] - a[1]))


def auto_fronts(outline, entrance=None):
    """The sides taken as the front when the architect chose none: the one nearest the building's entrance (its
    middle point), else the longest side."""
    s = sides(outline)
    if not s:
        return []
    if entrance is not None:
        from shapely.geometry import LineString, Point
        here = Point(float(entrance[0]), float(entrance[1]))
        return [min(range(len(s)), key=lambda k: LineString(s[k]).distance(here))]
    return [max(range(len(s)), key=lambda k: side_length(*s[k]))]


def roles(outline, fronts):
    """{side index: FRONT | SIDE | BACK}: the fronts as given; a side facing away from them (its outward normal at
    more than 135° from theirs) the back; the rest the sides. No front: every side a side («lateral»)."""
    s = sides(outline)
    fronts = [k for k in fronts if 0 <= k < len(s)]
    if not fronts:
        return {k: SIDE for k in range(len(s))}
    facing = sum((outward(*s[k]) * side_length(*s[k]) for k in fronts), np.zeros(2))
    if np.linalg.norm(facing) < 1e-9:
        facing = outward(*s[fronts[0]])
    facing = facing / np.linalg.norm(facing)
    out = {}
    for k, (a, b) in enumerate(s):
        if k in fronts:
            out[k] = FRONT
        elif float(np.dot(outward(a, b), facing)) < -math.cos(math.radians(45.0)):
            out[k] = BACK
        else:
            out[k] = SIDE
    return out


def distance_to(shape, outline, indices):
    """The least distance (m) from a shapely shape (the building's footprint) to these sides of the lot — or None
    (no such side, nothing built)."""
    from shapely.geometry import LineString
    if shape is None or shape.is_empty:
        return None
    s = sides(outline)
    found = [LineString(s[k]).distance(shape) for k in indices if 0 <= k < len(s)]
    return round(float(min(found)), 4) if found else None


def polygon(outline):
    """The lot as a shapely Polygon (valid), or None."""
    from shapely.geometry import Polygon
    r = ring(outline)
    if r is None:
        return None
    p = Polygon(r)
    if not p.is_valid:
        p = p.buffer(0)
    return p if not p.is_empty else None


def from_terrain(verts):
    """(0.423) A lot from a terrain's corners (N, 3): the outline of its plan (the convex hull of its survey points:
    a terrain is surveyed over the lot and its edges)."""
    from shapely.geometry import MultiPoint
    pts = np.asarray(verts, dtype=float).reshape(-1, 3)[:, :2]
    if len(pts) < 3:
        return None
    hull = MultiPoint([tuple(p) for p in pts]).convex_hull
    if hull.geom_type != "Polygon":
        return None
    return ring(list(hull.exterior.coords))
