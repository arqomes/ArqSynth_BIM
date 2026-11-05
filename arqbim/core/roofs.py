"""Roofs (0.111): flat, or pitched over a convex outline — one, two or four slopes (shed, gable, hip); (0.179) a hip
roof also over an orthogonal outline with corners turned in (an L, a T, a U); (0.190) and over any outline, its sides
at any angle (the straight skeleton, core/skeleton). Pure geometry (shapely, as core/rooms and core/slabs).

Each sloping side of the outline (counter-clockwise, plan) carries a plane rising inwards at the roof's slope from
the eave; over a convex outline the roof's surface is the lowest of those planes (a hip roof's hips and ridge come
out where two planes meet), so each slope is the part of the outline where its plane is the lowest. A side that
does not slope is a gable end: no plane, it only bounds the roof."""

import math

from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

FORMS = ("flat", "shed", "gable", "hip", "butterfly", "barrel", "custom")
EXTRUDED = ("butterfly", "barrel", "custom")     # (0.180) a profile across a rectangle, run along its length —
#                                                  (0.251) "custom": one drawn by the user (its section, real size)
MIN_SECTION = 0.50                     # (0.251) m: a drawn roof section at least this wide…
MIN_THICK = 0.02                       # …and this thick somewhere
SEAT_MIN = 0.01                        # (0.278) m: a thin cover's top at least this far over its walls' outer edge
HUGE = 1e4


def seat(slope, thickness, wall):
    """(0.275) How much higher than its walls' top a roof's top is over their outer line, its underside resting on
    their inner top edge (Revit's «Rafter»: the plate measured on the inside of the wall): t / cos a − w · tan a —
    flat, its thickness. slope in degrees, thickness of the roof, wall: the walls' thickness (m). (0.278) Never
    less than SEAT_MIN: a cover thinner than that (tiles, 3 cm, on a 20 cm wall) would let the wall's outer top
    edge through it; it rests over that edge instead, and the gap left over the wall's inner part is the wall
    plate's place (its carpentry)."""
    a = math.radians(slope)
    return max(thickness / math.cos(a) - wall * math.tan(a), SEAT_MIN)


def seat_gap(slope, thickness, wall):
    """(0.278) How far above its walls' inner top edge a roof's underside is: 0 but for a cover too thin (seat)."""
    a = math.radians(slope)
    return seat(slope, thickness, wall) - (thickness / math.cos(a) - wall * math.tan(a))


def is_convex(polygon):
    return polygon.convex_hull.area - polygon.area <= 1e-9 * max(polygon.area, 1.0)


def _turned(pts, angle):
    c, s = math.cos(angle), math.sin(angle)
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


def is_orthogonal(polygon, tol=1e-6):
    """(0.179) Every side along or square to the first (an L, a T, a U… however turned)."""
    pts = list(orient(polygon, 1.0).exterior.coords)[:-1]
    ax, ay = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
    n = math.hypot(ax, ay)
    for k in range(len(pts)):
        bx, by = pts[(k + 1) % len(pts)][0] - pts[k][0], pts[(k + 1) % len(pts)][1] - pts[k][1]
        m = math.hypot(bx, by)
        if m > 1e-9 and min(abs(ax * bx + ay * by), abs(ax * by - ay * bx)) > tol * n * m:
            return False
    return True


def can_slope(polygon, form):
    """A roof of this form can be made over the outline: flat always; pitched over a convex one; (0.179) a hip roof
    over one with corners turned in too, when its sides are square to each other — (0.190) or at any angle, when its
    skeleton comes out; (0.180) a butterfly or a barrel roof over a rectangle."""
    if form in EXTRUDED:
        return rect_frame(list(orient(polygon, 1.0).exterior.coords)[:-1]) is not None
    if form == "flat" or is_convex(polygon) or (form in ("hip", "gable") and is_orthogonal(polygon)):
        return True                                     # (0.246: two slopes over each wing of an L, a T, a U)
    return form == "hip" and _skeleton_faces(list(orient(polygon, 1.0).exterior.coords)[:-1]) is not None


def _skeleton_faces(pts):
    """(0.190) A hip roof over any outline: its straight skeleton's faces, as faces gives them — [(plane, polygon)]
    — or None."""
    from .skeleton import roof_faces
    found = roof_faces(pts)
    if found is None:
        return None
    return [(((float(a[0]), float(a[1])), (float(e[0]), float(e[1])), (float(n[0]), float(n[1]))), _clean(face))
            for (a, _b, e, n), face in found]


# ------------------------------------------------------------ roofs by extrusion (0.180)

def rect_frame(pts, tol=1e-6):
    """(a corner, the long sides' direction, the inward direction across, length, span) of a counter-clockwise
    rectangle — its profile goes across the span, run along the length —, or None when it is not one."""
    pts = _clean([tuple(p) for p in pts])
    if len(pts) != 4 or not is_orthogonal(Polygon(pts)):
        return None
    sides = [math.hypot(pts[(k + 1) % 4][0] - pts[k][0], pts[(k + 1) % 4][1] - pts[k][1]) for k in range(4)]
    k = 0 if sides[0] >= sides[1] - tol else 1
    a, e, n = side_frame(pts, k)
    return a, e, n, sides[k], sides[(k + 1) % 4]


def arch(span, slope):
    """A barrel roof's arc over a span between the walls, springing from them at the slope: (radius, the height of
    its centre under the walls' line — its rise is radius − that)."""
    alpha = math.radians(min(max(slope, 5.0), 85.0))
    radius = span / 2 / math.sin(alpha)
    return radius, radius * math.cos(alpha)


def profile_z(form, span, overhang, slope, v, thickness=0.0):
    """How high a butterfly or barrel roof's top is over the walls' line, `v` across from its (grown) edge — its
    underside, `thickness` lower (along the arc's radius, or square to the slope)."""
    c = span / 2 + overhang
    if form == "barrel":
        radius, below = arch(span, slope)
        r = radius - thickness
        return math.sqrt(max(r * r - (v - c) ** 2, 0.0)) - below
    t = math.tan(math.radians(slope))
    return (abs(v - c) - span / 2) * t - thickness / math.cos(math.radians(slope))


def extruded_height_at(outline, form, overhang, slope, eave, point, thickness=0.0, section=None):
    """The top (or the underside, `thickness` in) of a butterfly / barrel roof over a plan point; `outline` the
    walls' line (counter-clockwise rectangle) at the eave's height. (0.251) A drawn one ("custom", its `section`):
    its section's top or (thickness given) its underside there — over its middle, its lowest point at the eave."""
    frame = rect_frame(grown(outline, overhang))
    if frame is None:
        return eave
    a, _e, n, _length, span = frame
    v = (point[0] - a[0]) * n[0] + (point[1] - a[1]) * n[1]
    if form == "custom":
        found = section_heights(section or [], span, v)
        return eave + (found[0] if thickness else found[1]) if found else eave
    return eave + profile_z(form, span - 2 * overhang, overhang, slope, min(max(v, 0.0), span), thickness)


def custom_section(points):
    """(0.251) A drawn roof section [(a across, b up)…] m: its points from its lowest and leftmost (0, 0),
    counter-clockwise — ValueError when it is no area, narrower than MIN_SECTION or thinner than MIN_THICK."""
    poly = orient(Polygon([tuple(p[:2]) for p in points]), 1.0)
    if not poly.is_valid or poly.area < 1e-6:
        raise ValueError("roof_section")
    x0, y0, x1, y1 = poly.bounds
    if x1 - x0 < MIN_SECTION or y1 - y0 < MIN_THICK:
        raise ValueError("roof_section")
    return [(float(x - x0), float(y - y0)) for x, y in list(poly.exterior.coords)[:-1]]


def section_heights(section, span, v):
    """(0.251) (underside, top) of a drawn roof section across a span `span` (its middle on the span's), at v across
    from the span's edge — over its lowest point; None where it is not."""
    from shapely.geometry import LineString
    if len(section) < 3:
        return None
    width = max(x for x, _y in section)
    s = v - (span - width) / 2.0
    cut = Polygon(section).intersection(LineString([(s, -HUGE), (s, HUGE)]))
    if cut.is_empty:
        return None
    _x0, y0, _x1, y1 = cut.bounds
    return float(y0), float(y1)


def max_rectangles(pts):
    """(0.179) The largest rectangles that fit in an outline whose sides are along x and y — none inside another —
    as (x0, y0, x1, y1): the grid of its corners' xs and ys, every block of whole cells inside it."""
    poly = Polygon(pts)
    xs, ys = sorted({round(x, 9) for x, _y in pts}), sorted({round(y, 9) for _x, y in pts})
    inside = [[poly.contains(Polygon([(xs[i], ys[j]), (xs[i + 1], ys[j]), (xs[i + 1], ys[j + 1]),
                                      (xs[i], ys[j + 1])]).representative_point())
               for j in range(len(ys) - 1)] for i in range(len(xs) - 1)]
    found = []
    for i0 in range(len(xs) - 1):
        for j0 in range(len(ys) - 1):
            for i1 in range(i0 + 1, len(xs)):
                for j1 in range(j0 + 1, len(ys)):
                    if all(inside[i][j] for i in range(i0, i1) for j in range(j0, j1)):
                        found.append((i0, j0, i1, j1))
    maximal = [r for r in found if not any(o != r and o[0] <= r[0] and o[1] <= r[1] and o[2] >= r[2] and o[3] >= r[3]
                                           for o in found)]
    return [(xs[i0], ys[j0], xs[i1], ys[j1]) for i0, j0, i1, j1 in maximal]


def _hip_rectangles(pts):
    """(angle the outline is turned by, its largest rectangles in that turned frame, each as a counter-clockwise
    ring)."""
    angle = math.atan2(pts[1][1] - pts[0][1], pts[1][0] - pts[0][0])
    flat = _turned(pts, -angle)
    rings = [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)] for x0, y0, x1, y1 in max_rectangles(flat)]
    return angle, rings


def _orthogonal_hip_faces(pts, gable=False):
    """(0.179) A hip roof over an orthogonal outline with corners turned in: the roof of each largest rectangle in
    it, and of all of them the highest at each point (eroding an orthogonal outline square by square is what its
    eaves rising inwards do — the straight skeleton): [(plane, polygon)]. (0.246) gable: each rectangle's roof of
    two slopes, its ridge along its length — the wings' ridges meeting, valleys in the corners turned in, a gable at
    each wing's end."""
    angle, rings = _hip_rectangles(pts)
    pieces = []                                         # (rectangle, plane (start, e, n) turned back, its polygon)
    for r, ring in enumerate(rings):
        for plane, polygon in faces(ring, sloping_sides(ring, "gable") if gable else [True] * 4):
            pieces.append((r, plane, Polygon(polygon)))
    out = []
    for r, (a, e, n), region in pieces:
        for s, (b, _f, m), other in pieces:
            if s == r:
                continue
            overlap = region.intersection(other)
            if overlap.is_empty or overlap.area < 1e-12:
                continue
            w = (n[0] - m[0], n[1] - m[1])               # (the other higher: p · (n − m) <= a · n − b · m)
            c = a[0] * n[0] + a[1] * n[1] - b[0] * m[0] - b[1] * m[1]
            if math.hypot(*w) < 1e-12:                   # (parallel planes: one higher everywhere, or the same)
                if c > 1e-9 or (abs(c) <= 1e-9 and s < r):
                    region = region.difference(overlap)
                continue
            region = region.difference(overlap.intersection(_half_plane(w, c)))
        for part in getattr(region, "geoms", [region]):
            if part.geom_type == "Polygon" and part.area > 1e-9:
                ring = _clean(list(orient(part.simplify(1e-7), 1.0).exterior.coords)[:-1])
                (ta,), (te,), (tn,) = _turned([a], angle), _turned([e], angle), _turned([n], angle)
                out.append(((ta, te, tn), _turned(ring, angle)))
    return out


def sloping_sides(outline, form):
    """Which sides slope ([bool] per side, side k from corner k to k + 1): none (flat), the first (shed: it rises
    from there), the longest and the one most opposite it (gable), all (hip)."""
    n = len(outline)
    if form == "hip":
        return [True] * n
    if form in ("flat",) + EXTRUDED:                # (0.180: a profile run along, no planes)
        return [False] * n
    if form == "shed":
        return [k == 0 for k in range(n)]
    sides = [(outline[(k + 1) % n][0] - outline[k][0], outline[(k + 1) % n][1] - outline[k][1]) for k in range(n)]
    lengths = [math.hypot(*s) for s in sides]
    first = max(range(n), key=lambda k: lengths[k])
    ux, uy = sides[first][0] / lengths[first], sides[first][1] / lengths[first]
    second = min((k for k in range(n) if k != first and lengths[k] > 1e-9),
                 key=lambda k: (sides[k][0] * ux + sides[k][1] * uy) / lengths[k])     # (the most opposite)
    return [k in (first, second) for k in range(n)]


def side_frame(outline, k):
    """(start corner, unit direction, unit inward normal) of side k of a counter-clockwise outline."""
    ax, ay = outline[k]
    bx, by = outline[(k + 1) % len(outline)]
    length = math.hypot(bx - ax, by - ay)
    ex, ey = (bx - ax) / length, (by - ay) / length
    return (ax, ay), (ex, ey), (-ey, ex)


def _half_plane(w, c):
    """The (huge) polygon of the points p with p · w <= c."""
    n = math.hypot(*w)
    wx, wy = w[0] / n, w[1] / n
    px, py = wx * c / n, wy * c / n                    # (a point on the line)
    tx, ty = -wy, wx
    return Polygon([(px + tx * HUGE, py + ty * HUGE), (px - tx * HUGE, py - ty * HUGE),
                    (px - tx * HUGE - wx * HUGE, py - ty * HUGE - wy * HUGE),
                    (px + tx * HUGE - wx * HUGE, py + ty * HUGE - wy * HUGE)])


def faces(outline, sloping):
    """The roof's slopes: [(its plane — (a point of its eave, the eave's direction, the inward normal) —, its plan
    polygon [(x, y)] counter-clockwise)] — over a convex outline, the parts where each sloping side's plane is the
    lowest (all the planes at the same slope); a flat roof: [(None, the outline)]; (0.179) a hip roof over an
    orthogonal outline with corners turned in: _orthogonal_hip_faces. None when it cannot be made."""
    poly = orient(Polygon(outline), 1.0)
    pts = list(poly.exterior.coords)[:-1]
    if not any(sloping):
        return [(None, pts)]
    if not is_convex(poly):
        if not all(sloping):                            # (0.246) two slopes over each wing of an orthogonal one
            return _orthogonal_hip_faces(pts, gable=True) if sum(sloping) >= 2 and is_orthogonal(poly) else None
        return _orthogonal_hip_faces(pts) if is_orthogonal(poly) else _skeleton_faces(pts)    # (0.190: any angle)
    planes = [(k, *side_frame(pts, k)) for k in range(len(pts)) if sloping[k]]
    out = []
    for k, a, e, n in planes:
        region = poly
        for j, b, _f, m in planes:
            if j == k:
                continue
            w = (n[0] - m[0], n[1] - m[1])                 # (h_k <= h_j: p · (n - m) <= a · n - b · m)
            if math.hypot(*w) < 1e-12:
                continue
            region = region.intersection(_half_plane(w, a[0] * n[0] + a[1] * n[1] - b[0] * m[0] - b[1] * m[1]))
        if region.geom_type == "Polygon" and region.area > 1e-9:
            out.append(((a, e, n), _clean(list(orient(region.simplify(1e-7), 1.0).exterior.coords)[:-1])))
    return out


def _clean(pts, tol=1e-6):
    """A ring without the points a hair from the one before (what the cutting leaves)."""
    out = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > tol:
            out.append((float(p[0]), float(p[1])))
    if len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= tol:
        out.pop()
    return out


def height_at(outline, sloping, slope, eave, point):
    """The roof's top at a plan point: the eave's height plus the rise to it from the nearest sloping side's
    plane (the lowest plane); a flat roof: the eave."""
    poly = orient(Polygon(outline), 1.0)
    pts = list(poly.exterior.coords)[:-1]
    t = math.tan(math.radians(slope))
    gable = any(sloping) and not all(sloping) and sum(sloping) >= 2         # (0.246: over each wing, two slopes)
    if any(sloping) and (all(sloping) or gable) and not is_convex(poly) and is_orthogonal(poly):   # (0.179) the
        angle, rings = _hip_rectangles(pts)                                         # highest rectangle's roof
        (q,) = _turned([point], -angle)
        best = 0.0
        for ring in rings:
            (x0, y0), (x1, y1) = ring[0], ring[2]
            if x0 - 1e-9 <= q[0] <= x1 + 1e-9 and y0 - 1e-9 <= q[1] <= y1 + 1e-9:
                if not gable:
                    rise = min(q[0] - x0, x1 - q[0], q[1] - y0, y1 - q[1])
                elif x1 - x0 >= y1 - y0:                # (its ridge along its length)
                    rise = min(q[1] - y0, y1 - q[1])
                else:
                    rise = min(q[0] - x0, x1 - q[0])
                best = max(best, rise * t)
        return eave + best
    if any(sloping) and all(sloping) and not is_convex(poly):             # (0.190) its skeleton's face there
        from shapely.geometry import Point
        q = Point(float(point[0]), float(point[1]))
        found = _skeleton_faces(pts) or []
        for (a, _e, n), face in found:
            if Polygon(face).buffer(1e-9).contains(q):
                return eave + max((point[0] - a[0]) * n[0] + (point[1] - a[1]) * n[1], 0.0) * t
        near = min(found, key=lambda f: Polygon(f[1]).distance(q), default=None)    # (just outside: the nearest)
        if near is not None:
            (a, _e, n), _face = near
            return eave + max((point[0] - a[0]) * n[0] + (point[1] - a[1]) * n[1], 0.0) * t
        return eave
    rises = []
    for k in range(len(pts)):
        if sloping[k]:
            a, _e, n = side_frame(pts, k)
            rises.append(((point[0] - a[0]) * n[0] + (point[1] - a[1]) * n[1]) * t)
    return eave + (min(rises) if rises else 0.0)


def grown(outline, overhang):
    """The outline grown by the eaves' overhang (mitred corners), counter-clockwise."""
    poly = orient(Polygon(outline), 1.0)
    if overhang > 1e-9:
        poly = orient(poly.buffer(overhang, join_style="mitre"), 1.0)
    return [tuple(c) for c in list(poly.exterior.coords)[:-1]]


def carried_over(original, sloping, outline):
    """The sides of `outline` (the original grown, or turned round) that slope: those running the same way as a
    sloping side of `original`."""
    def directions(pts):
        out = []
        for k in range(len(pts)):
            _a, e, _n = side_frame(pts, k)
            out.append(e)
        return out
    src = list(zip(directions(original), sloping))
    return [any(s and e[0] * f[0] + e[1] * f[1] > 1 - 1e-6 for f, s in src) for e in directions(outline)]
