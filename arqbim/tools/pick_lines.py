"""(0.451) Revit's «Pick Lines» (the owner: «criar por seleção»): the line or edge under the mouse — a loose line, a CAD
line drawn as one, any element's level edge (a wall's face in a plan, a slab's side), a grid axis — as a level segment,
the side of it the mouse is on, and that segment moved by an offset to that side (Revit's «Offset» on the options
bar). Shared by the Wall and the Line tools."""

from collections import namedtuple

import numpy as np

from ..core import arc_runs
from ..core.inference import ON_EDGE, ON_GUIDE
from .align import level_edges, nearest_edge

INSIDE_PX = 15.0     # a click inside an element takes its edge this near (pixels), not a far one

# (0.459) an arc drawn in pieces, picked whole: its centre (x, y, z), radius, start angle and sweep (radians), points
Arc = namedtuple("Arc", "centre radius start sweep points")


def edge_at(viewport, doc, x, y):
    """The level segment (a, b) under (x, y) — a grid axis, an edge or a line snapped to, or the edge of the element
    under the mouse within INSIDE_PX —, or None."""
    found = edge_and_owner(viewport, doc, x, y)
    return None if found is None else found[:2]


def edge_and_owner(viewport, doc, x, y):
    """edge_at's (a, b) and the element or sketch it is an edge of (its id; None: a grid axis, a guide)."""
    k = viewport.grid_axis_at(x, y) if hasattr(viewport, "grid_axis_at") else None
    if k is not None and "grid" not in getattr(viewport, "unselectable", ()):
        axis = doc.grids[k]
        z = float(viewport.grid_level())
        return np.array((*axis.start[:2], z)), np.array((*axis.end[:2], z)), None
    snap, _hit = viewport.snap(x, y)
    if snap is not None:
        if snap.kind in (ON_EDGE, ON_GUIDE) and snap.edge is not None:
            a, b = (np.asarray(p, dtype=float) for p in snap.edge)
            if abs(float(b[2] - a[2])) < 1e-6 and float(np.linalg.norm((b - a)[:2])) > 1e-4:
                return a, b, snap.obj_id
        if snap.obj_id is not None:                      # (a point snapped — an end, a middle: its element's edge)
            edges = level_edges(doc.get(snap.obj_id))
            found = nearest_edge(edges, snap.point)
            if found is not None and found[1] <= 1e-3:
                return (*edges[found[0]], snap.obj_id)
    hit = viewport.pick_point(x, y)
    if hit is not None:
        edges = level_edges(doc.get(hit[0]))
        found = nearest_edge(edges, hit[2])
        if found is not None and found[1] <= INSIDE_PX * viewport.world_per_pixel(np.asarray(hit[2], dtype=float)):
            return (*edges[found[0]], hit[0])
    return None


def arc_at(viewport, doc, x, y):
    """(0.459, the owner: «Ao desenhar a parede por seleção de aresta, no arco ele só seleciona segmentos em vez de arco
    inteiro») The arc drawn in pieces whose piece is under (x, y) — a polygon's rounded corner, a circle, an arc of
    lines, a curved wall's face —, level: an Arc, or None when the edge there is straight."""
    if not hasattr(viewport, "snap"):
        return None
    found = edge_and_owner(viewport, doc, x, y)
    if found is None or found[2] is None:
        return None
    a, b, obj_id = found
    edges = level_edges(doc.get(obj_id))
    near = nearest_edge(edges, (np.asarray(a, dtype=float) + np.asarray(b, dtype=float)) / 2)
    if near is None or near[1] > 1e-3 + 0.02 * float(np.linalg.norm((np.asarray(b) - np.asarray(a))[:2])):
        return None
    a, b = edges[near[0]]                           # (the element's own edge: its ends shared with the next ones)
    chain = arc_runs.chain_through(edges, a, b)
    if chain is None:
        return None
    points, closed, k = chain
    run = arc_runs.run_around(points, k, closed)
    if run is None:
        return None
    z = float(a[2])
    return Arc(np.array((float(run.centre[0]), float(run.centre[1]), z)), run.radius, run.start, run.sweep,
               [np.asarray(points[i % len(points)], dtype=float) for i in run.indices])


def arc_points(arc, radius, z, step_deg=6.0):
    """An Arc's points at another radius (about its centre), level at z."""
    import math
    n = max(2, int(math.ceil(abs(math.degrees(arc.sweep)) / step_deg)))
    angles = arc.start + np.linspace(0.0, arc.sweep, n + 1)
    return [np.array((arc.centre[0] + radius * math.cos(t), arc.centre[1] + radius * math.sin(t), z)) for t in angles]


def arc_offset(arc, mouse, distance):
    """The radius of the arc moved `distance` across to the mouse's side (out of the circle or into it), and that side
    (+1 out, -1 in)."""
    out = 1.0 if mouse is None or float(np.linalg.norm(np.asarray(mouse, dtype=float)[:2] - arc.centre[:2])) >= \
        arc.radius else -1.0
    return arc.radius + out * abs(distance), out


def side_of(a, b, point):
    """+1 when `point` is to the left of a→b (seen from above), -1 to the right (on it: the left)."""
    d = np.asarray(b, dtype=float)[:2] - np.asarray(a, dtype=float)[:2]
    w = np.asarray(point, dtype=float)[:2] - np.asarray(a, dtype=float)[:2]
    return -1.0 if float(d[0] * w[1] - d[1] * w[0]) < 0 else 1.0


def offset_segment(a, b, distance, side):
    """a→b moved `distance` across, to `side` (+1 its left)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    d = (b - a)[:2]
    n = float(np.linalg.norm(d))
    if n < 1e-12 or not distance:
        return a.copy(), b.copy()
    left = np.array((-d[1] / n, d[0] / n, 0.0))
    return a + left * distance * side, b + left * distance * side
