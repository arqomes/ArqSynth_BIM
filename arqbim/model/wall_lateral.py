"""(0.345) The façade walls' bending out of their plane under the wind (core/ec6.lateral), for the structure's
verification: each masonry wall outside (model.bim.facade_walls) under 1,5 qp(z) at its top (NP EN 1991-1-4) times
the walls' net pressure coefficient — in the middle of a façade +0,8 outside and −0,3 inside (zone D), near the
building's corners −1,2 (zone A, e/5 from them, e = min(b, 2h)) and +0,2 inside —, its openings' wind coming to it;
its permanent vertical stress at mid-height raising its strength (a load-bearing wall's loads, model.wall_loads; else
its own weight). A load-bearing wall's check is added to its own (EC6); an enclosing or infill wall gets a line of its
own. A pre-design: the structural design is the engineer's."""

import numpy as np

from ..core import actions as act
from ..core import ec6

MIDDLE_C = 0.8 + 0.3            # the walls' net coefficient in the middle of a façade (cpe zone D, cpi −0,3)…
CORNER_C = 1.2 + 0.2            # …near the corners (cpe zone A, cpi +0,2)
MOST_OPEN = 3.0                 # a wall's wind at most so many times its own (its openings' share)


def corner_zone(wall, extent, height):
    """Is a wall (start, end in plan) within e/5 of the ends of its façade — the building's box `extent` ((x0, y0),
    (x1, y1)) along its direction — e = min(the box across it, 2 × the building's height)?"""
    (x0, y0), (x1, y1) = extent
    s, e = np.asarray(wall["start"], dtype=float), np.asarray(wall["end"], dtype=float)
    along_x = abs(e[0] - s[0]) >= abs(e[1] - s[1])
    lo, hi, low, high, across = (min(s[0], e[0]), max(s[0], e[0]), x0, x1, y1 - y0) if along_x else \
        (min(s[1], e[1]), max(s[1], e[1]), y0, y1, x1 - x0)
    zone = min(across, 2.0 * height) / 5.0
    return lo < low + zone - 1e-6 or hi > high - zone + 1e-6


def check(walls, settings, designs, wall_loads=()):
    """The façade walls (model.bim.facade_walls) verified out of their plane: the load-bearing ones' added to their
    designs (`designs`: [model.structure_design.ElementDesign]), the others' new ElementDesign — returned (the
    designs, more)."""
    from .structure_design import ElementDesign
    if not walls:
        return list(designs)
    loads = {w.guid: w for w in wall_loads or ()}
    by_guid = {e.guid: e for e in designs if e.kind == "wall"}
    pts = np.array([p for w in walls for p in (w["start"], w["end"])], dtype=float)
    extent = (tuple(pts.min(axis=0)), tuple(pts.max(axis=0)))
    ground = min(w["base"] for w in walls)
    height = max(w["top"] for w in walls) - ground
    out = list(designs)
    for w in walls:
        masonry = w.get("masonry")                       # (0.346: its type's, else the project's)
        own_settings = ec6.with_masonry(settings, masonry)
        weight = ec6.WEIGHT.get(own_settings.masonry_unit, 13.0)
        length = float(np.hypot(w["end"][0] - w["start"][0], w["end"][1] - w["start"][1]))
        h = w["top"] - w["base"]
        if length < 0.1 or h < 0.1 or w["t"] <= 0.0:
            continue
        z = w["top"] - ground
        qp = act.peak_pressure(z, settings.wind_zone, settings.terrain)
        c = CORNER_C if corner_zone(w, extent, height) else MIDDLE_C
        solid = w["whole"] - w["openings"]
        factor = min(w["whole"] / solid, MOST_OPEN) if solid > 1e-6 else MOST_OPEN
        load = loads.get(w["guid"])
        if load is not None and load.net > 1e-9:         # (its permanent loads at mid-height, on each metre)
            sigma = (load.top_g + load.self_g / 2.0) / load.net / w["t"] / 1000.0
        else:
            sigma = weight * h / 2.0 / 1000.0            # (its own weight above mid-height)
        edges = ec6.edges_key(*w["held"])
        own = by_guid.get(w["guid"]) if w["bearing"] else None
        if own is not None and ec6_wall(own):
            ec6.lateral(w["t"], length, h, qp, c, z, factor, sigma, edges, own_settings, design=own.design,
                        own=bool(masonry))
        elif own is None:
            d = ec6.lateral(w["t"], length, h, qp, c, z, factor, sigma, edges, own_settings, own=bool(masonry))
            out.append(ElementDesign(w["guid"], "wall", d, length, {"facade": True}))
    return out


def ec6_wall(e):
    """A design of a masonry wall's (its notes by EC6)?"""
    return any(n.code.startswith("ec6") for n in e.design.notes)
