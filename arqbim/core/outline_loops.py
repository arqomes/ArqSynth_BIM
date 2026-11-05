"""(0.410) An outline with holes as it is drawn: a list of loops — the first the outline, the others its holes —, each
[corners, sides]: corners [(u, v)], sides[i] running from corner i to corner i + 1, straight (None), an arc through a
point or a Bézier (core/curves, as a wall's profile, 0.375).

An element keeps the polygon it is made of (a slab's body, a floor's or a ceiling's «Contorno» / «Furos») and, beside
it, the loops as drawn (`text`). They are read back only while they still draw that polygon: an element moved,
mirrored or changed some other way (by its beams, by another program) has the polygon's corners for its loops, with
straight sides — nothing is lost, the curves only become corners.

Pure geometry: no IFC, no Qt."""

import math

import numpy as np

from . import curves

TOL = 1e-4                  # m: the drawn loops still match the polygon (written from them, read back)
CLOSE = 1e-6


def rings(loops):
    """The polygon's rings [(u, v)] — the outline first, then the holes — with the curved sides in pieces."""
    return [curves.profile_outline(corners, sides) for corners, sides in loops]


def plain(polygon_rings):
    """Loops of straight sides from the polygon's rings."""
    out = []
    for ring in polygon_rings:
        pts = [(float(p[0]), float(p[1])) for p in ring]
        if len(pts) > 1 and math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < CLOSE:
            pts.pop()
        out.append([pts, [None] * len(pts)])
    return out


def copy(loops):
    return [[[tuple(p) for p in corners], [dict(s) if s else None for s in sides]] for corners, sides in loops]


def text(loops):
    """The loops as kept in the IFC: «u,v;u,v;…#side|side|…» per loop, the loops joined by «/» (the sides as a wall
    profile's, core/curves.side_text)."""
    return "/".join(";".join("{:.6f},{:.6f}".format(float(p[0]), float(p[1])) for p in corners) + "#" +
                    "|".join(curves.side_text(s) for s in sides) for corners, sides in loops)


def parse(value):
    """`text` read back — None when empty or not understood."""
    value = (value or "").strip()
    if not value:
        return None
    loops = []
    try:
        for part in value.split("/"):
            pts_text, _hash, sides_text = part.partition("#")
            corners = [tuple(float(v) for v in pair.split(",")) for pair in pts_text.split(";") if pair]
            if len(corners) < 3 or any(len(p) != 2 for p in corners):
                return None
            texts = sides_text.split("|") if sides_text else []
            sides = [curves.side_of(texts[k]) if k < len(texts) else None for k in range(len(corners))]
            loops.append([corners, sides])
    except ValueError:
        return None
    return loops or None


def rounded(loops):
    """The loops as they will read back from the IFC (their numbers kept to the micrometre)."""
    return parse(text(loops)) or copy(loops)


def matches(loops, polygon_rings, tol=TOL):
    """These loops draw exactly these rings (same count, same points in the same order)."""
    drawn = rings(loops)
    polygon_rings = plain(polygon_rings)
    if len(drawn) != len(polygon_rings):
        return False
    for a, (b, _sides) in zip(drawn, polygon_rings):
        if len(a) != len(b) or not np.allclose(np.asarray(a, float), np.asarray(b, float), atol=tol):
            return False
    return True


def drawn(polygon_rings, value):
    """The loops kept (`value`, the text) while they still draw the polygon's rings — else the rings' corners, with
    straight sides."""
    loops = parse(value)
    return loops if loops is not None and matches(loops, polygon_rings) else plain(polygon_rings)


def mapped(loops, fn):
    """The loops with every point (corners, arcs' points, Bézier handles) taken through fn((u, v)) -> (u', v')."""
    def go(p):
        q = fn((float(p[0]), float(p[1])))
        return float(q[0]), float(q[1])

    out = []
    for corners, sides in loops:
        new_sides = []
        for s in sides:
            if not s:
                new_sides.append(None)
            elif s.get("kind") == "arc":
                new_sides.append({"kind": "arc", "through": go(s["through"])})
            else:
                new_sides.append({"kind": "bezier", "h1": go(s["h1"]), "h2": go(s["h2"])})
        out.append([[go(p) for p in corners], new_sides])
    return out


def moved(loop, d):
    """A loop moved by d = (du, dv)."""
    return mapped([loop], lambda p: (p[0] + d[0], p[1] + d[1]))[0]


def curved(loops):
    return any(s for _corners, sides in loops for s in sides)


def polygon(loops):
    """The shapely polygon the loops draw (holes inside the outline, none crossing) — or None."""
    from .slabs import outline_polygon
    drawn_rings = rings(loops)
    if not drawn_rings:
        return None
    return outline_polygon(drawn_rings[0], drawn_rings[1:])


def area(loops):
    poly = polygon(loops)
    return float(poly.area) if poly is not None else 0.0


# ---------------------------------------------------------------- holes drawn

def rectangle(a, b):
    """A rectangle's loop from two opposite corners (along u and v) — None when it has no area."""
    (u0, v0), (u1, v1) = a, b
    if abs(u1 - u0) < 0.01 or abs(v1 - v0) < 0.01:
        return None
    lo_u, hi_u, lo_v, hi_v = min(u0, u1), max(u0, u1), min(v0, v1), max(v0, v1)
    return [[(lo_u, lo_v), (hi_u, lo_v), (hi_u, hi_v), (lo_u, hi_v)], [None] * 4]


def circle(centre, radius):
    """A circle's loop: four corners a quarter apart, each side an arc through the point between them — its grips
    as any outline's (a corner dragged, an arc's point pulled). None when it is too small."""
    if radius < 0.01:
        return None
    cu, cv = float(centre[0]), float(centre[1])
    corners = [(cu + radius * math.cos(k * math.pi / 2), cv + radius * math.sin(k * math.pi / 2)) for k in range(4)]
    sides = [{"kind": "arc", "through": (cu + radius * math.cos((k + 0.5) * math.pi / 2),
                                         cv + radius * math.sin((k + 0.5) * math.pi / 2))} for k in range(4)]
    return [corners, sides]


def polygon_loop(points):
    """A loop of straight sides through the points clicked — None with fewer than three (or none apart)."""
    pts = []
    for p in points:
        q = (float(p[0]), float(p[1]))
        if not pts or math.hypot(q[0] - pts[-1][0], q[1] - pts[-1][1]) > 1e-6:
            pts.append(q)
    if len(pts) > 1 and math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) <= 1e-6:
        pts.pop()
    return [pts, [None] * len(pts)] if len(pts) >= 3 else None


def contains(loop, point):
    """The point lies inside the loop (its curves in pieces)."""
    from shapely.geometry import Point, Polygon
    ring = curves.profile_outline(*loop)
    if len(ring) < 3:
        return False
    poly = Polygon(ring)
    return poly.is_valid and poly.contains(Point(float(point[0]), float(point[1])))
