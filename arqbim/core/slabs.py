"""Slabs drawn by their outline (0.100): a polygon clicked point by point, a circle, or the region a click inside
walls finds (the magic wand, as the rooms'). Pure geometry (shapely, as core/rooms).

A slab's function, as the ArqSynth Modeler's floor layers: structure (it carries: its top at the storey's level),
finish (a floor covering: it rests on the level) or excluded (left out of the structural calculation)."""

import math

from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from . import rooms

FUNCTIONS = ("estrutural", "acabamento", "excluida")
SHAPES = ("retangulo", "poligono", "circulo")
MIN_AREA = 0.01            # m²: smaller is not a slab
CIRCLE_SIDES = 64          # a circle drawn on the screen (the IFC keeps a true circle)
REACHES = ("interior", "exterior")


def outline_polygon(points, holes=()):
    """A slab's plan from its corners [(x, y)…] (and holes): a valid shapely Polygon, or None — fewer than three
    corners, its sides crossing, or too small."""
    pts = []
    for p in points:
        q = (float(p[0]), float(p[1]))
        if not pts or math.hypot(q[0] - pts[-1][0], q[1] - pts[-1][1]) > 1e-6:
            pts.append(q)
    if len(pts) > 1 and math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) <= 1e-6:
        pts.pop()
    if len(pts) < 3:
        return None
    poly = Polygon(pts, [[(float(x), float(y)) for x, y in h] for h in holes])
    if not poly.is_valid or poly.area < MIN_AREA:
        return None
    return orient(poly, 1.0)


def circle_ring(centre, radius, sides=CIRCLE_SIDES):
    """The corners of a circle drawn as a polygon (previews, plans)."""
    cx, cy = float(centre[0]), float(centre[1])
    return [(cx + radius * math.cos(2 * math.pi * k / sides), cy + radius * math.sin(2 * math.pi * k / sides))
            for k in range(sides)]


MAX_REACH = 1.0            # m: the most a side goes out under a wall (the magic wand, to the outer faces)


def _depth(blocked, a, b, gap):
    """How far the walls go out from the side a -> b of a counter-clockwise ring: along its outward normal,
    from its middle, through what is blocked (a wall: its thickness)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    if n < 1e-9:
        return 0.0
    nx, ny = dy / n, -dx / n
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    ray = LineString([(mx, my), (mx + nx * MAX_REACH, my + ny * MAX_REACH)])
    hit = ray.intersection(blocked)
    pieces = [g for g in getattr(hit, "geoms", [hit]) if g.geom_type == "LineString" and not g.is_empty]
    for piece in sorted(pieces, key=lambda g: Point(mx, my).distance(g)):
        if Point(mx, my).distance(piece) <= gap:
            far = max(Point(mx, my).distance(Point(c)) for c in piece.coords)
            return min(far, MAX_REACH)
    return 0.0


STEP = 0.25                # m: sides shorter than this at a corner are what walls not joined leave (0.179)


def _drop_steps(ring, short=STEP):
    """(0.179) A counter-clockwise ring without the little steps two walls not joined leave at a corner: a run of
    short sides between two long ones that are not parallel becomes the corner where those two meet (a step
    between parallel sides — a real jog — stays)."""
    pts = [tuple(p) for p in ring]
    changed = True
    while changed and len(pts) > 3:
        changed = False
        n = len(pts)
        length = [math.hypot(pts[(k + 1) % n][0] - pts[k][0], pts[(k + 1) % n][1] - pts[k][1]) for k in range(n)]
        for k in range(n):
            if length[k] >= short or length[k - 1] < short:
                continue                                    # (k: the first short side after a long one)
            j = k
            while length[j % n] < short and j - k < n - 2:
                j += 1
            a0, a1 = pts[(k - 1) % n], pts[k]                # the long side before…
            b0, b1 = pts[j % n], pts[(j + 1) % n]            # …and after the short ones
            da, db = (a1[0] - a0[0], a1[1] - a0[1]), (b1[0] - b0[0], b1[1] - b0[1])
            cross = da[0] * db[1] - da[1] * db[0]
            if abs(cross) < 1e-6 * math.hypot(*da) * math.hypot(*db):
                continue
            s = ((b0[0] - a0[0]) * db[1] - (b0[1] - a0[1]) * db[0]) / cross
            corner = (a0[0] + da[0] * s, a0[1] + da[1] * s)
            if math.hypot(corner[0] - a1[0], corner[1] - a1[1]) > 2 * short:
                continue
            drop = {(k + i) % n for i in range(j - k + 1)}
            pts = [corner if i == k else p for i, p in enumerate(pts) if i == k or i not in drop]
            changed = True
            break
    return pts


def _offset_ring(ring, depths):
    """A counter-clockwise ring with each side moved out by its own distance; consecutive sides on one line
    that move out by different distances get a step between them."""
    n = len(ring)
    lines = []
    for k in range(n):
        (ax, ay), (bx, by) = ring[k], ring[(k + 1) % n]
        length = math.hypot(bx - ax, by - ay)
        nx, ny = (by - ay) / length, -(bx - ax) / length
        d = depths[k]
        lines.append(((ax + nx * d, ay + ny * d), (bx + nx * d, by + ny * d)))
    out = []
    for k in range(n):
        (a0, a1), (b0, b1) = lines[k - 1], lines[k]
        da = (a1[0] - a0[0], a1[1] - a0[1])
        db = (b1[0] - b0[0], b1[1] - b0[1])
        cross = da[0] * db[1] - da[1] * db[0]
        if abs(cross) < 1e-9 * math.hypot(*da) * math.hypot(*db):
            out += [a1, b0]                         # (in line: a step if they moved out differently)
            continue
        s = ((b0[0] - a0[0]) * db[1] - (b0[1] - a0[1]) * db[0]) / cross
        out.append((a0[0] + da[0] * s, a0[1] + da[1] * s))
    return out


def wand(obstacles, point, reach="interior", gap=rooms.GAP):
    """The magic wand: the outline of a slab where `point` is, between the walls and columns (their plans).

    interior: between the walls' inner faces (as the room; a column inside leaves a hole);
    exterior: each side out to the outer face of the wall along it (under the walls round it, as Revit's floor
    by picked walls at their outer faces — the wall across to the next room: under its whole thickness), no
    holes. A shapely Polygon, or None when the point is not inside closed walls."""
    region = rooms.region(obstacles, point, gap)
    if region is None:
        return None
    region = orient(region, 1.0)
    if reach != "exterior":
        return region
    polys = [p for p in (Polygon(o).buffer(0) for o in obstacles if len(o) >= 3) if not p.is_empty]
    blocked = unary_union(polys).buffer(gap / 2, join_style="mitre").buffer(-gap / 2, join_style="mitre")
    ring = _drop_steps(list(region.exterior.coords)[:-1])         # (0.179) clean corners where walls meet unjoined
    depths = [_depth(blocked, ring[k], ring[(k + 1) % len(ring)], gap) for k in range(len(ring))]
    grown = outline_polygon(_offset_ring(ring, depths))
    if grown is None or not grown.contains(region.representative_point()):
        return orient(Polygon(region.exterior.coords), 1.0)       # (an odd outline: to the inner faces)
    return orient(grown.simplify(1e-6), 1.0)


def ring_area(points):
    """The area of a ring of plan points (shoelace)."""
    n = len(points)
    return abs(sum(points[k][0] * points[(k + 1) % n][1] - points[(k + 1) % n][0] * points[k][1]
                   for k in range(n))) / 2
