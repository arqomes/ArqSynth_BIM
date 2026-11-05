"""Ceilings (0.118): a ceiling's outline — a room's, or drawn — continuous, or laid in square tiles on a grid
started at the outline's lower left corner (the cut tiles round the edges, as a fitter cuts them), each a hair
smaller than its cell so that the joints show. Pure geometry (shapely)."""

import math

from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient

STYLES = ("continuous", "tiles")
FINISHES = ("azulejo", "reboco", "pedra",     # (0.119) a wall's finishes: tiles, plaster, stone; (0.173) slats,
            "ripado", "canelado", "perfurado",  # flutes, a perforated sheet (core/surfaces); (0.175) a wavy
            "ondulado")                         # surface of ribs
LIGHTS = ("panel", "downlight")               # (0.119) a light set in a ceiling
TILE = 0.60                 # m
JOINT = 0.006               # m: the gap between two tiles
MIN_TILE = 1e-4             # m²: a scrap smaller than this is left out


def tiles(outline, size=TILE, joint=JOINT, holes=()):
    """The tiles of a ceiling over `outline` (plan, with holes): [[(x, y)…]] counter-clockwise, whole or cut."""
    poly = Polygon(outline, [list(h) for h in holes]).buffer(0)
    if poly.is_empty:
        return []
    x0, y0, x1, y1 = poly.bounds
    out = []
    nx = int(math.ceil((x1 - x0) / size - 1e-9))
    ny = int(math.ceil((y1 - y0) / size - 1e-9))
    for i in range(nx):
        for j in range(ny):
            cell = box(x0 + i * size + joint / 2, y0 + j * size + joint / 2,
                       x0 + (i + 1) * size - joint / 2, y0 + (j + 1) * size - joint / 2)
            piece = cell.intersection(poly)
            for part in getattr(piece, "geoms", [piece]):
                if part.geom_type == "Polygon" and part.area > MIN_TILE:
                    out.append([tuple(c) for c in list(orient(part, 1.0).exterior.coords)[:-1]])
    return out
