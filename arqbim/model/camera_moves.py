"""(0.364) The ArqSynth Presentation's camera moves, here (PLANO, the Presentation's step 4): the same list as its
library (lib/editor3d/camera-fx/presets.ts), made from the same measures (room.ts) by the same two generators
(generators/orbit.ts, dolly.ts) — so a move chosen for a scene in the BIM is seen here as the Presentation will play it,
and only its name and the measures it was made from need to travel.

A move is made from the building's measures — its middle, the radius of the sphere round it and its size (the
Presentation's `live3DBounds`: three.js's Box3 of the model) — and, for the moves inside a room, from that room (its
floor's middle, half its size along X and Z, the largest circle that fits from its middle, its height). Everything in
the GLB's axes (metres, Y up, −Z north), as the Presentation's; `to_model` brings a point back to the model's (Z up).

`frames` plays one as the Presentation does, near enough to judge it: the points through a centripetal Catmull-Rom
curve, walked at an even speed with the move's easing, the camera looking at the move's target (the building's middle,
or the room's at eye height). The Presentation also rounds the corners and damps the turns: a little smoother there.
Pure NumPy."""

import math
from dataclasses import dataclass

import numpy as np

EYE = 1.6                       # the eye's height above the ground (m), for the moves that end on it
DEFAULT_ROOM_SIZE, DEFAULT_ROOM_HEIGHT = 4.0, 2.7    # a room assumed when none is known
WALL_CLEARANCE = 0.45
MAX_INTERIOR_RADIUS = 6.0
CATEGORIES = ("exterior", "aereo", "cinematografico", "interior")

# id -> (category, generator, duration s, easing), in the Presentation's order inside each category
MOVES = {
    "orbit_90": ("exterior", "orbit", 8.0, "ease_in_out"),
    "orbit_180": ("exterior", "orbit", 12.0, "ease_in_out"),
    "orbit_360": ("exterior", "orbit", 20.0, "linear"),
    "orbit_rising": ("exterior", "orbit", 14.0, "ease_in_out"),
    "orbit_descending": ("exterior", "orbit", 14.0, "ease_out"),
    "facade_wrap": ("exterior", "orbit", 7.0, "ease_in_out"),
    "aerial_orbit": ("aereo", "orbit", 16.0, "linear"),
    "aerial_descent": ("aereo", "dolly", 10.0, "ease_out"),
    "dolly_in": ("cinematografico", "dolly", 7.0, "ease_in_out"),
    "pull_back": ("cinematografico", "dolly", 9.0, "ease_out"),
    "lateral_travel": ("cinematografico", "dolly", 9.0, "ease_in_out"),
    "facade_rise": ("cinematografico", "dolly", 8.0, "ease_in_out"),
    "hero_shot": ("cinematografico", "orbit", 6.0, "ease_out"),
    "int_spiral_up": ("interior", "orbit", 9.0, "ease_in_out"),
    "int_spiral_down": ("interior", "orbit", 9.0, "ease_out"),
    "int_orbit_full": ("interior", "orbit", 14.0, "linear"),
    "int_wrap": ("interior", "orbit", 8.0, "ease_in_out"),
    "int_dolly_in": ("interior", "dolly", 6.0, "ease_in_out"),
    "int_pull_back": ("interior", "dolly", 7.0, "ease_out"),
    "int_lateral": ("interior", "dolly", 8.0, "ease_in_out"),
    "int_vertical": ("interior", "dolly", 6.0, "ease_in_out"),
}


def interior(move):
    return MOVES.get(move, ("",))[0] == "interior"


@dataclass(frozen=True)
class Building:
    """The building's measures (GLB axes): its middle, the radius of the sphere round it, its size."""
    center: tuple
    radius: float
    size: tuple

    @classmethod
    def of_box(cls, lo, hi):
        """From the lowest and highest corners of the model in the GLB (three.js's Box3)."""
        lo, hi = np.asarray(lo, dtype=float), np.asarray(hi, dtype=float)
        size = hi - lo
        return cls(tuple(map(float, (lo + hi) / 2.0)), max(float(np.linalg.norm(size)) / 2.0, 0.5),
                   tuple(map(float, size)))


@dataclass(frozen=True)
class Room:
    """A room (GLB axes): the middle of its floor, half its size along X and Z, the largest circle that fits from
    its middle (its distance to the nearest wall), its height."""
    center: tuple
    half: tuple
    inradius: float
    height: float

    def as_dict(self):
        return {"center": [round(c, 4) for c in self.center], "half": [round(h, 4) for h in self.half],
                "inradius": round(self.inradius, 4), "height": round(self.height, 4)}


def default_room(center):
    h = DEFAULT_ROOM_SIZE / 2.0
    return Room(tuple(map(float, center)), (h, h), h, DEFAULT_ROOM_HEIGHT)


def _edge_distance(x, z, poly):
    best = math.inf
    for k in range(len(poly)):
        (ax, az), (bx, bz) = poly[k - 1], poly[k]
        dx, dz = bx - ax, bz - az
        length = dx * dx + dz * dz
        t = 0.0 if length < 1e-12 else min(max(((x - ax) * dx + (z - az) * dz) / length, 0.0), 1.0)
        best = min(best, math.hypot(x - (ax + dx * t), z - (az + dz * t)))
    return best


def inside(x, z, poly):
    """Is (x, z) inside the outline [(x, z)]? (a ray cast, as room.ts's)"""
    poly = [(float(a), float(b)) for a, b in poly]
    within = False
    for k in range(len(poly)):
        (xj, zj), (xi, zi) = poly[k - 1], poly[k]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi) + xi:
            within = not within
    return within


def room_from_polygon(poly, floor_y, height):
    """A room from its outline [(x, z)] in the GLB (room.ts's roomFromPolygon): its middle the area's centroid when
    that is inside — in an L or a U it is not, and the farthest point from the walls is taken —, or None."""
    poly = [(float(x), float(z)) for x, z in poly]
    if len(poly) < 3:
        return None
    xs, zs = [p[0] for p in poly], [p[1] for p in poly]
    if not (max(xs) > min(xs) and max(zs) > min(zs)):
        return None
    a = cx = cz = 0.0
    for k in range(len(poly)):
        (xj, zj), (xi, zi) = poly[k - 1], poly[k]
        cross = xj * zi - xi * zj
        a += cross
        cx += (xj + xi) * cross
        cz += (zj + zi) * cross
    if abs(a) < 1e-9:
        cx, cz = sum(xs) / len(xs), sum(zs) / len(zs)
    else:
        cx, cz = cx / (3.0 * a), cz / (3.0 * a)
    if not inside(cx, cz, poly):
        best, n = -1.0, 16
        for i in range(1, n):
            for j in range(1, n):
                x = min(xs) + (max(xs) - min(xs)) * i / n
                z = min(zs) + (max(zs) - min(zs)) * j / n
                if inside(x, z, poly):
                    d = _edge_distance(x, z, poly)
                    if d > best:
                        best, cx, cz = d, x, z
        if best < 0:
            return None
    return Room((cx, float(floor_y), cz), ((max(xs) - min(xs)) / 2.0, (max(zs) - min(zs)) / 2.0),
                _edge_distance(cx, cz, poly), float(height) if height > 0.5 else DEFAULT_ROOM_HEIGHT)


def _interior_radius(room, k=1.0):
    return max(0.5, min(room.inradius - WALL_CLEARANCE, room.inradius * k, MAX_INTERIOR_RADIUS))


def _long_axis(room):
    return (0, room.half[0]) if room.half[0] >= room.half[1] else (2, room.half[1])


def _usable_half(room):
    return max(0.6, min(_long_axis(room)[1], room.inradius - WALL_CLEARANCE * 0.5))


def _eye_y(room, above):
    return room.center[1] + above


def _ceiling_eye_y(room):
    return room.center[1] + max(1.8, room.height - 0.45)


def _along(room, offset, y):
    axis, _half = _long_axis(room)
    c = room.center
    return (c[0] + offset, y, c[2]) if axis == 0 else (c[0], y, c[2] + offset)


def _framing(radius):
    return max(6.0, radius * 2.2)


def _base_y(b):
    return b.center[1] - (b.size[1] if b.size else b.radius) / 2.0


def _top_y(b):
    return b.center[1] + (b.size[1] if b.size else b.radius) / 2.0


def _orbit(centre, frm, to, r_start, r_end, y_start, y_end):
    return {"kind": "orbit", "center": tuple(centre), "radiusStart": r_start, "radiusEnd": r_end,
            "heightStart": y_start, "heightEnd": y_end, "angleStart": float(frm), "angleEnd": float(to)}


def _dolly(frm, to, arc):
    return {"kind": "dolly", "from": tuple(map(float, frm)), "to": tuple(map(float, to)), "arc": float(arc)}


def params(move, building, room=None):
    """The generator's parameters of a move (presets.ts's build), from the building's measures and (inside) the
    room's — the default room in the building's middle when none is given."""
    b, r = building, building.radius
    d = _framing(r)
    base, top, c = _base_y(b), _top_y(b), b.center
    if interior(move):
        room = room or default_room((c[0], base, c[2]))
        rc = room.center
        k_orbit = {"int_spiral_up": (-30, 150, 0.55, 0.72), "int_spiral_down": (150, -30, 0.72, 0.55),
                   "int_orbit_full": (0, 360, 0.55, None), "int_wrap": (-40, 80, 0.8, None)}
        if move in k_orbit:
            frm, to, k, k_end = k_orbit[move]
            radius = _interior_radius(room, k)
            radius_end = _interior_radius(room, k_end) if k_end is not None else radius
            y_start, y_end = {"int_spiral_up": (_eye_y(room, 1.15), _ceiling_eye_y(room)),
                              "int_spiral_down": (_ceiling_eye_y(room), _eye_y(room, 1.15))}.get(
                move, (_eye_y(room, 1.55), _eye_y(room, 1.55)))
            return _orbit(rc, frm, to, radius, radius_end, y_start, y_end)
        y = _eye_y(room, 1.5)
        if move in ("int_dolly_in", "int_pull_back"):
            dd = max(0.9, _usable_half(room) - 0.35)
            near, far = _along(room, -0.15 * dd, y), _along(room, -dd, y)
            return _dolly(far, near, 0.0) if move == "int_dolly_in" else _dolly(near, far, 0.06)
        if move == "int_lateral":
            s = max(0.6, _usable_half(room) - 0.45)
            return _dolly(_along(room, -s, y), _along(room, s, y), 0.0)
        off = -0.5 * _usable_half(room)                                     # int_vertical
        return _dolly(_along(room, off, rc[1] + 0.9), _along(room, off, _ceiling_eye_y(room)), 0.0)
    if move == "orbit_90":
        return _orbit(c, -45, 45, d, d, base + EYE, base + EYE)
    if move == "orbit_180":
        return _orbit(c, -90, 90, d, d, base + EYE, base + EYE)
    if move == "orbit_360":
        return _orbit(c, 0, 360, d, d, base + EYE * 2, base + EYE * 2)
    if move == "orbit_rising":
        return _orbit(c, -60, 120, d, d * 0.85, base + EYE, top + r * 0.5)
    if move == "orbit_descending":
        return _orbit(c, 120, -30, d * 1.15, d * 0.7, top + r * 0.6, base + EYE)
    if move == "facade_wrap":
        return _orbit(c, -20, 70, d * 0.8, d * 0.8, base + EYE * 1.5, base + EYE * 1.5)
    if move == "aerial_orbit":
        return _orbit(c, 0, 270, d * 1.3, d * 1.3, top + r * 0.8, top + r * 0.8)
    if move == "hero_shot":
        return _orbit(c, 20, -35, d * 1.25, d * 0.95, base + r * 0.35, base + EYE * 1.6)
    if move == "aerial_descent":
        return _dolly((c[0], top + r * 1.2, c[2] + d * 1.4), (c[0], base + EYE, c[2] + d * 0.45), 0.15)
    if move == "dolly_in":
        return _dolly((c[0], base + EYE, c[2] + d * 1.5), (c[0], base + EYE, c[2] + d * 0.5), 0.0)
    if move == "pull_back":
        return _dolly((c[0], base + EYE, c[2] + d * 0.4), (c[0], base + r * 0.5, c[2] + d * 1.9), 0.1)
    if move == "lateral_travel":
        dd, span = d * 0.7, (b.size[0] if b.size else r * 2.0) * 0.9
        return _dolly((c[0] - span / 2.0, base + EYE, c[2] + dd), (c[0] + span / 2.0, base + EYE, c[2] + dd), 0.0)
    if move == "facade_rise":
        dd = d * 0.75
        return _dolly((c[0], base + EYE, c[2] + dd), (c[0], top + r * 0.25, c[2] + dd), 0.0)
    raise KeyError(move)


def target(move, building, room=None):
    """Where the camera looks during the move: the room's middle at eye height inside, else the building's middle."""
    if interior(move):
        room = room or default_room((building.center[0], _base_y(building), building.center[2]))
        return (room.center[0], _eye_y(room, 1.5), room.center[2])
    return tuple(building.center)


def points(p):
    """The generator's points (generators/orbit.ts, dolly.ts): (N, 3)."""
    if p["kind"] == "orbit":
        sweep = p["angleEnd"] - p["angleStart"]
        count = min(24, max(5, math.ceil(abs(sweep) / 22.0) + 1))
        k = np.linspace(0.0, 1.0, count)
        angle = np.radians(p["angleStart"] + sweep * k)
        radius = p["radiusStart"] + (p["radiusEnd"] - p["radiusStart"]) * k
        y = p["heightStart"] + (p["heightEnd"] - p["heightStart"]) * k
        c = p["center"]
        return np.column_stack((c[0] + np.cos(angle) * radius, y, c[2] + np.sin(angle) * radius))
    frm, to = np.asarray(p["from"], dtype=float), np.asarray(p["to"], dtype=float)
    flat = np.array((to[0] - frm[0], 0.0, to[2] - frm[2]))
    if abs(p["arc"]) < 1e-3 or flat @ flat < 1e-6:
        return np.array((frm, to))
    side = np.array((-flat[2], 0.0, flat[0])) / np.linalg.norm(flat)
    k = np.linspace(0.0, 1.0, 5)
    return frm + np.outer(k, to - frm) + np.outer(np.sin(k * math.pi) * np.linalg.norm(flat) * p["arc"], side)


def ease(t, easing):
    """The Presentation's speed curves (path.ts's applyEasing)."""
    x = min(max(float(t), 0.0), 1.0)
    if easing == "linear":
        return x
    if easing == "ease_in":
        return x * x
    if easing == "ease_out":
        return 1.0 - (1.0 - x) * (1.0 - x)
    return x * x * (3.0 - 2.0 * x)


def track(pts, samples=160):
    """The points through a centripetal Catmull-Rom curve (three.js's CatmullRomCurve3, 'centripetal'), sampled at
    an even spacing along it: (samples + 1, 3)."""
    pts = np.asarray(pts, dtype=float)
    keep = [pts[0]]
    for p in pts[1:]:
        if np.linalg.norm(p - keep[-1]) > 1e-6:
            keep.append(p)
    pts = np.array(keep)
    if len(pts) < 2:
        return np.repeat(pts[:1], samples + 1, axis=0)
    ends = np.vstack((2 * pts[0] - pts[1], pts, 2 * pts[-1] - pts[-2]))
    dense = []
    for k in range(len(pts) - 1):
        p0, p1, p2, p3 = ends[k], ends[k + 1], ends[k + 2], ends[k + 3]
        t0 = 0.0
        t1 = t0 + max(np.linalg.norm(p1 - p0) ** 0.5, 1e-4)
        t2 = t1 + max(np.linalg.norm(p2 - p1) ** 0.5, 1e-4)
        t3 = t2 + max(np.linalg.norm(p3 - p2) ** 0.5, 1e-4)
        for t in np.linspace(t1, t2, 24, endpoint=k == len(pts) - 2):
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            dense.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    dense = np.array(dense)
    run = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(dense, axis=0), axis=1))))
    if run[-1] < 1e-9:
        return np.repeat(dense[:1], samples + 1, axis=0)
    at = np.linspace(0.0, run[-1], samples + 1)
    return np.column_stack([np.interp(at, run, dense[:, j]) for j in range(3)])


def frames(move, building, room=None, seconds=None, fps=30):
    """The move played: [(eye, target)] in the GLB, one per frame, `seconds` long (None: the move's own time)."""
    _category, _kind, own, easing = MOVES[move]
    seconds = float(seconds) if seconds else own
    path = track(points(params(move, building, room)))
    look = np.asarray(target(move, building, room), dtype=float)
    n = max(2, int(round(seconds * fps)) + 1)
    out = []
    for k in range(n):
        u = ease(k / (n - 1), easing) * (len(path) - 1)
        i = min(int(u), len(path) - 2)
        out.append((path[i] + (path[i + 1] - path[i]) * (u - i), look))
    return out


def to_model(point, offset):
    """A point of the GLB (Y up, the offset taken off) in the model's axes (Z up): gltf_export._y_up undone."""
    x, y, z = (float(c) for c in point)
    return np.array((x, -z, y)) + np.asarray(offset, dtype=float)


def to_gl(point, offset):
    """A point of the model in the GLB's axes (gltf_export._y_up, the offset taken off)."""
    p = np.asarray(point, dtype=float) - np.asarray(offset, dtype=float)
    return np.array((p[0], p[2], -p[1]))
