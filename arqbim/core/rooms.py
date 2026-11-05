"""Rooms (0.99), as Revit's: a click inside walls finds the room — the free part of the plan, between the walls
and columns of a storey, that holds the point ("magic wand"). Pure geometry (shapely, which IfcOpenShell already
needs: BSD-3).

A gap of up to GAP between two walls is closed (a wall drawn a hair short still bounds the room); a region that
reaches out of the walls' extent is not a room (not enclosed)."""

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

GAP = 0.02                 # m: walls this near each other close the room
MARGIN = 1.0               # m round the walls: what is outside them


def region(obstacles, point, gap=GAP):
    """The free region holding `point`, between the obstacles (plan polygons [(x, y)…] of walls and columns):
    a shapely Polygon (holes where a column stands inside), or None — the point in a wall, or not enclosed."""
    polys = [Polygon(p).buffer(0) for p in obstacles if len(p) >= 3]
    polys = [p for p in polys if not p.is_empty]
    if not polys:
        return None
    blocked = unary_union(polys)
    if gap > 0:                                   # (closed: gaps narrower than `gap` filled)
        blocked = blocked.buffer(gap / 2, join_style="mitre").buffer(-gap / 2, join_style="mitre")
    x0, y0, x1, y1 = blocked.bounds
    domain = box(x0 - MARGIN, y0 - MARGIN, x1 + MARGIN, y1 + MARGIN)
    free = domain.difference(blocked)
    here = Point(point)
    for part in getattr(free, "geoms", [free]):
        if part.contains(here):
            if part.exterior.distance(domain.exterior) < 1e-9:
                return None                       # (it reaches the outside: not a room)
            return Polygon(part.exterior.coords, [h.coords for h in part.interiors]).simplify(1e-4)
    return None


def outline(polygon):
    """([(x, y)] round its outside, counter-clockwise, without the repeated last point; [[(x, y)]] each hole)."""
    from shapely.geometry.polygon import orient
    p = orient(polygon, 1.0)
    return [tuple(c) for c in p.exterior.coords[:-1]], [[tuple(c) for c in h.coords[:-1]] for h in p.interiors]


def label_point(polygon):
    """Where a room's label goes: a point well inside it."""
    p = polygon.representative_point()
    return float(p.x), float(p.y)
