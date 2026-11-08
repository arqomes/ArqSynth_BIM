"""(0.456, the owner: «Sim, põe» — Revit's «Draw» panel on a floor, a ceiling, a slab) The outlines drawn beyond the
rectangle, the polygon and the circle: a regular polygon inscribed in a circle or circumscribed about it, an ellipse
(four Bézier quarters), the loop of the lines picked one after another (each corner where one meets the next); an
outline moved out or in by an offset (Revit's «Offset»), its corners rounded by a radius (Revit's «Radius»).

Loops as core/outline_loops' — [corners [(x, y)], sides] (a side None straight, an arc through a point, a Bézier) —,
counter-clockwise. Pure geometry: no IFC, no Qt."""

import math

import numpy as np

from . import curves

KAPPA = 4.0 * (math.sqrt(2.0) - 1.0) / 3.0     # a quarter of a circle as a cubic Bézier: its handles this long
MIN_SIZE = 0.01                                # m
SIDES = (3, 4, 5, 6, 7, 8, 9, 10, 12, 16)      # a regular polygon's sides offered


def _xy(p):
    return np.array((float(p[0]), float(p[1])))


def _area(corners):
    p = np.asarray(corners, dtype=float)
    return 0.5 * float(np.dot(p[:, 0], np.roll(p[:, 1], -1)) - np.dot(p[:, 1], np.roll(p[:, 0], -1)))


def straight(loop):
    """The loop has no curved side."""
    return loop is not None and not any(loop[1])


def regular(centre, through, sides, inscribed=True):
    """A regular polygon's loop about `centre`: inscribed in the circle through `through` (a corner there) or
    circumscribed about it (`through` the middle of a side). None when too small."""
    c = _xy(centre)
    v = _xy(through) - c
    d = float(np.linalg.norm(v))
    n = int(sides)
    if d < MIN_SIZE or n < 3:
        return None
    a0 = math.atan2(v[1], v[0])
    r, start = (d, a0) if inscribed else (d / math.cos(math.pi / n), a0 + math.pi / n)
    corners = [(float(c[0] + r * math.cos(start + 2 * math.pi * k / n)),
                float(c[1] + r * math.sin(start + 2 * math.pi * k / n))) for k in range(n)]
    return [corners, [None] * n]


def ellipse(centre, axis_end, minor):
    """An ellipse's loop: its centre, the end of one of its axes (that half-axis) and the other half-axis `minor` —
    its four axis ends as corners, each quarter a Bézier (its grips as any outline's). None when too small."""
    c = _xy(centre)
    a = _xy(axis_end) - c
    major = float(np.linalg.norm(a))
    if major < MIN_SIZE or minor < MIN_SIZE:
        return None
    b = np.array((-a[1], a[0])) / major * float(minor)
    ends = [c + a, c + b, c - a, c - b]                    # (counter-clockwise)
    ways = [b, -a, -b, a]                                  # (where the curve goes at each end)
    corners = [tuple(map(float, p)) for p in ends]
    sides = []
    for k in range(4):
        p, q = ends[k], ends[(k + 1) % 4]
        sides.append({"kind": "bezier", "h1": tuple(map(float, p + ways[k] * KAPPA)),
                      "h2": tuple(map(float, q - ways[(k + 1) % 4] * KAPPA))})
    return [corners, sides]


def axis_distance(centre, axis_end, point):
    """How far `point` is from the line through the centre and the axis' end (the other half-axis, by the mouse)."""
    c, a, p = _xy(centre), _xy(axis_end), _xy(point)
    d = a - c
    n = float(np.linalg.norm(d))
    if n < 1e-12:
        return 0.0
    return abs(float(d[0] * (p - c)[1] - d[1] * (p - c)[0])) / n


def crossing(p, d, q, e):
    """Where the line through p along d meets the one through q along e (plan), or None (parallel)."""
    p, d, q, e = _xy(p), _xy(d), _xy(q), _xy(e)
    den = d[0] * e[1] - d[1] * e[0]
    if abs(den) < 1e-9 * max(1.0, float(np.linalg.norm(d)) * float(np.linalg.norm(e))):
        return None
    w = q - p
    return p + d * ((w[0] * e[1] - w[1] * e[0]) / den)


def picked(lines):
    """Revit's «Pick Lines» on a floor: the loop of the lines picked one after another — [(a point, its direction)] —,
    its corners where each meets the next (the last the first). None with fewer than three, two in a row parallel, or
    a loop that crosses itself."""
    from shapely.geometry import Polygon
    if len(lines) < 3:
        return None
    corners = []
    for k in range(len(lines)):
        (p, d), (q, e) = lines[k - 1], lines[k]
        x = crossing(p, d, q, e)
        if x is None:
            return None
        corners.append(tuple(map(float, x)))
    poly = Polygon(corners)
    if not poly.is_valid or poly.area < MIN_SIZE ** 2:
        return None
    if _area(corners) < 0:
        corners = corners[::-1]
    return [corners, [None] * len(corners)]


def ccw(loop):
    """The loop going round counter-clockwise (straight ones: its corners turned about)."""
    if loop is None or not straight(loop) or _area(loop[0]) >= 0:
        return loop
    return [list(loop[0])[::-1], [None] * len(loop[0])]


def offset(loop, distance):
    """A straight loop moved out (distance > 0) or in, its corners mitred (Revit's «Offset»). None when it does not
    stay one polygon (moved in too far) or has curved sides."""
    from shapely.geometry import Polygon
    from shapely.geometry.polygon import orient
    if not straight(loop):
        return None
    if abs(distance) < 1e-9:
        return loop
    poly = Polygon(loop[0])
    if not poly.is_valid:
        return None
    grown = poly.buffer(float(distance), join_style=2, mitre_limit=10.0)
    if grown.is_empty or grown.geom_type != "Polygon":
        return None
    ring = [tuple(map(float, c)) for c in list(orient(grown, 1.0).exterior.coords)[:-1]]
    ring = _clean(ring)
    return [ring, [None] * len(ring)] if len(ring) >= 3 else None


def _clean(ring, tol=1e-7):
    """The corners with the ones in a straight line (or on top of another) taken away."""
    pts = [np.asarray(p, dtype=float) for p in ring]
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for k in range(len(pts)):
            a, b, c = pts[k - 1], pts[k], pts[(k + 1) % len(pts)]
            if float(np.linalg.norm(b - a)) < tol or abs(float((b - a)[0] * (c - b)[1] - (b - a)[1] * (c - b)[0])) < \
                    tol * max(float(np.linalg.norm(b - a)) * float(np.linalg.norm(c - b)), 1e-12):
                del pts[k]
                changed = True
                break
    return [tuple(map(float, p)) for p in pts]


def rounded(loop, radius):
    """Every corner between two straight sides rounded by an arc of `radius` (Revit's «Radius») — kept, at each, to
    what half of its shorter side allows, so that neighbours never overlap."""
    if loop is None or radius <= 0:
        return loop
    corners, sides = [tuple(map(float, p)) for p in loop[0]], list(loop[1])
    n = len(corners)
    # the radius each corner may have, from the outline as drawn
    allowed = []
    for k in range(n):
        p, a, b = (np.asarray(corners[i], dtype=float) for i in (k, k - 1, (k + 1) % n))
        la, lb = float(np.linalg.norm(a - p)), float(np.linalg.norm(b - p))
        if la < 1e-9 or lb < 1e-9:
            allowed.append(0.0)
            continue
        u1, u2 = (a - p) / la, (b - p) / lb
        half = math.acos(float(np.clip(u1 @ u2, -1.0, 1.0))) / 2
        allowed.append(0.0 if half < 1e-3 or math.pi / 2 - half < 1e-3 else 0.49 * min(la, lb) * math.tan(half))
    out_c, out_s = corners, sides
    k, done = 0, 0
    while done < n:
        r = min(float(radius), allowed[done])
        made = curves.fillet(out_c, out_s, k, r) if r > 1e-6 else None
        if made is None:
            k += 1
        else:
            out_c, out_s, _r = made
            k += 2
        done += 1
    return [list(out_c), list(out_s)]
