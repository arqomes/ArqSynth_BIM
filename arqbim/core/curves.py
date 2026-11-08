"""Curves of loose lines (0.373, the free drawing as SketchUp's): arcs, freehand lines and Bézier curves, each kept as
a chain of straight pieces in a sketch, with what it was drawn from (a sketch's `curve`) so that it is picked whole and
can be changed again. Pure numpy, on any plane (its `normal`).

An arc: {"kind": "arc", "centre", "normal", "start" (its first point), "angle" (degrees turned about the normal,
counter-clockwise seen from where it points; negative: the other way), "segments", "pie" (a sector: the two radii
too)}. A Bézier curve: {"kind": "bezier", "anchors": [[point, handle in, handle out]…] (a corner point has its handles
on itself), "closed", "normal", "steps" (pieces between two anchors)}. A freehand line: {"kind": "freehand"}. What is
left of one whose points no longer follow it (its end dragged…): {"kind": "curve"}."""

import math

import numpy as np

STEP_DEG = 15.0             # an arc's pieces at most this many degrees each (as the Line tool's tangent arcs, 0.151)
MIN_SEGMENTS = 2
BEZIER_STEPS = 12           # pieces of a Bézier curve between two of its points
FREEHAND_PX = 2.0           # a freehand line keeps a point where it bends more than this (pixels, on the screen)


def _unit(v):
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else v


def _rotate(v, axis, angle):
    """v turned `angle` radians about the unit `axis` (Rodrigues)."""
    c, s = math.cos(angle), math.sin(angle)
    return v * c + np.cross(axis, v) * s + axis * float(axis @ v) * (1 - c)


# ---------------------------------------------------------------- arcs

def segments_for(angle_deg, step=STEP_DEG):
    """How many pieces an arc turning `angle_deg` has by default (at most `step` degrees each)."""
    return max(MIN_SEGMENTS, int(math.ceil(abs(angle_deg) / step - 1e-9)))


def arc_points(centre, normal, start, angle_deg, segments=None):
    """The arc's points, both ends included (a whole circle: without repeating the first)."""
    centre, n = np.asarray(centre, dtype=float), _unit(normal)
    u = np.asarray(start, dtype=float) - centre
    count = int(segments) if segments else segments_for(angle_deg)
    whole = abs(abs(angle_deg) - 360.0) < 1e-9
    a = math.radians(angle_deg)
    pts = [centre + _rotate(u, n, a * k / count) for k in range(count + (0 if whole else 1))]
    if not whole:
        pts[0] = np.asarray(start, dtype=float).copy()
    return pts


def arc_end(curve):
    c = curve
    return np.asarray(c["centre"], float) + _rotate(np.asarray(c["start"], float) - np.asarray(c["centre"], float),
                                                     _unit(c["normal"]), math.radians(c["angle"]))


def arc_radius(curve):
    return float(np.linalg.norm(np.asarray(curve["start"], float) - np.asarray(curve["centre"], float)))


def arc_by_bulge(a, b, bulge, normal):
    """(0.373) SketchUp's 2-point arc: from a to b, its middle `bulge` off the chord (positive: to the left of a -> b
    seen from where `normal` points). (centre, start, angle) — None when a and b are one point or bulge is 0."""
    a, b, n = np.asarray(a, float), np.asarray(b, float), _unit(normal)
    chord = b - a
    chord = chord - float(chord @ n) * n
    half = float(np.linalg.norm(chord)) / 2
    if half < 1e-9 or abs(bulge) < 1e-9:
        return None
    left = _unit(np.cross(n, chord))
    radius = (half * half + bulge * bulge) / (2 * abs(bulge))
    mid = a + chord / 2
    centre = mid + left * (bulge - math.copysign(radius, bulge))
    sweep = 2 * math.atan2(half, radius - abs(bulge))          # (more than half a circle when the bulge is over r)
    return centre, a.copy(), math.degrees(sweep) * (-1.0 if bulge > 0 else 1.0)


def bulge_of(a, b, point, normal):
    """How far `point` is off the chord a-b, to its left (positive) or right, seen from where `normal` points."""
    a, b, n = np.asarray(a, float), np.asarray(b, float), _unit(normal)
    left = _unit(np.cross(n, b - a))
    return float((np.asarray(point, float) - a) @ left)


def tangent_bulge(a, b, tangent, normal):
    """The bulge of the 2-point arc from a to b that leaves a along `tangent` (SketchUp's tangent arc: on from the
    line it starts at), or None when b is straight ahead."""
    n = _unit(normal)
    tg = np.asarray(tangent, float)
    tg = _unit(tg - float(tg @ n) * n)
    d = np.asarray(b, float) - np.asarray(a, float)
    d = d - float(d @ n) * n
    side = np.cross(n, tg)
    h = float(d @ side)
    if abs(h) < 1e-9 * max(float(np.linalg.norm(d)), 1.0) or np.linalg.norm(tg) < 1e-12:
        return None
    radius = float(d @ d) / (2 * h)
    centre = np.asarray(a, float) + side * radius
    u0, u1 = np.asarray(a, float) - centre, np.asarray(a, float) + d - centre
    axis = _unit(np.cross(u0, tg))
    sweep = math.atan2(float(np.cross(u0, u1) @ axis), float(u0 @ u1)) % (2 * math.pi)
    return bulge_of(a, b, centre + _rotate(u0, axis, sweep / 2), n)


def bulge_for_radius(a, b, radius, side):
    """The bulge of the 2-point arc from a to b of this radius, the shorter one, bulging the way `side` says (its
    sign as bulge_of's) — or None when the radius is under half the chord."""
    half = float(np.linalg.norm(np.asarray(b, float) - np.asarray(a, float))) / 2
    if radius < half - 1e-9:
        return None
    return math.copysign(radius - math.sqrt(max(radius * radius - half * half, 0.0)), side or 1.0)


def arc_through(a, m, b):
    """The arc from a through m to b (3D): (centre, normal, angle) — the angle positive about that normal — or None
    when the three are in a line."""
    a, m, b = (np.asarray(p, float) for p in (a, m, b))
    n = np.cross(m - a, b - a)
    if np.linalg.norm(n) < 1e-12 * max(1.0, float(np.linalg.norm(b - a)) ** 2):
        return None
    n = _unit(n)
    u, v = m - a, b - a                                           # (the circumcentre, in the plane of the three)
    uu, vv, uv = float(u @ u), float(v @ v), float(u @ v)
    den = 2 * (uu * vv - uv * uv)
    s, t = vv * (uu - uv) / den, uu * (vv - uv) / den
    centre = a + u * s + v * t
    r0, r2 = a - centre, b - centre
    sweep = math.atan2(float(np.cross(r0, r2) @ n), float(r0 @ r2)) % (2 * math.pi)
    return centre, n, math.degrees(sweep)                        # (a -> m -> b turns about n: m is on the way)


def arc_curve(centre, normal, start, angle_deg, segments=None, pie=False):
    return {"kind": "arc", "centre": [float(c) for c in centre], "normal": [float(c) for c in _unit(normal)],
            "start": [float(c) for c in start], "angle": float(angle_deg),
            "segments": int(segments) if segments else segments_for(angle_deg), "pie": bool(pie)}


def arc_with(curve, radius=None, angle=None, segments=None):
    """(0.373) The arc changed in its Properties: another radius (about the same centre, from the same direction),
    another angle (from the same start), another number of pieces."""
    c = dict(curve)
    centre, start = np.asarray(c["centre"], float), np.asarray(c["start"], float)
    if radius is not None:
        c["start"] = [float(x) for x in centre + _unit(start - centre) * float(radius)]
    if angle is not None:
        c["angle"] = float(angle)
    if segments is not None:
        c["segments"] = int(segments)
    return c


# ---------------------------------------------------------------- ellipses (0.458, Revit's «Ellipse», «Partial Ellipse»)

ELLIPSE_SEGMENTS = 48


def ellipse_curve(centre, normal, axis_end, minor, start=0.0, angle=360.0, segments=None):
    """An ellipse's data: {"kind": "ellipse", "centre", "normal", "axis" (the end of its first half-axis), "minor" (the
    other half-axis, about the normal: positive to the left of the first, seen from where the normal points), "start",
    "angle" (where it starts and how far it turns, in degrees of its parameter: p = centre + A cos θ + B sin θ),
    "segments"}."""
    return {"kind": "ellipse", "centre": [float(c) for c in centre], "normal": [float(c) for c in _unit(normal)],
            "axis": [float(c) for c in axis_end], "minor": float(minor), "start": float(start),
            "angle": float(angle), "segments": int(segments) if segments else ELLIPSE_SEGMENTS}


def half_ellipse(a, b, height, normal, segments=None):
    """(Revit's «Partial Ellipse») The half ellipse on the axis from a to b, `height` tall — positive to the left of
    a → b about the normal, negative to its right —, from a to b."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return ellipse_curve((a + b) / 2, normal, b, height, 180.0, -180.0, segments)


def ellipse_axes(curve):
    """(centre, A, B): the ellipse's centre and its two half-axes (vectors)."""
    centre = np.asarray(curve["centre"], float)
    a = np.asarray(curve["axis"], float) - centre
    return centre, a, _unit(np.cross(_unit(curve["normal"]), a)) * float(curve["minor"])


def ellipse_points(curve, segments=None):
    """The ellipse's points, both ends included (a whole one: without repeating the first)."""
    centre, a, b = ellipse_axes(curve)
    angle = float(curve.get("angle", 360.0))
    count = int(segments or curve.get("segments") or ELLIPSE_SEGMENTS)
    whole = abs(abs(angle) - 360.0) < 1e-9
    s, turn = math.radians(float(curve.get("start", 0.0))), math.radians(angle)
    return [centre + a * math.cos(s + turn * k / count) + b * math.sin(s + turn * k / count)
            for k in range(count + (0 if whole else 1))]


def is_half_ellipse(curve):
    return curve.get("kind") == "ellipse" and abs(abs(float(curve.get("angle", 360.0))) - 180.0) < 1e-9


def ellipse_with(curve, axis=None, minor=None, segments=None):
    """(0.458) The ellipse changed: its first half-axis `axis` long (the same centre and direction), the other `minor`
    (on the same side), another number of pieces."""
    c = dict(curve)
    centre = np.asarray(c["centre"], float)
    if axis is not None:
        c["axis"] = [float(x) for x in centre + _unit(np.asarray(c["axis"], float) - centre) * float(axis)]
    if minor is not None:
        c["minor"] = math.copysign(float(minor), float(c["minor"]) or 1.0)
    if segments is not None:
        c["segments"] = int(segments)
    return c


# ---------------------------------------------------------------- Bézier curves

def bezier_span(p0, p1, p2, p3, steps=BEZIER_STEPS):
    """Points of a cubic Bézier span, both ends included."""
    t = np.linspace(0.0, 1.0, int(steps) + 1)[:, None]
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    return list((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3)


def bezier_points(anchors, closed=False, steps=BEZIER_STEPS):
    """The curve's points through its anchors [[point, handle in, handle out]…], in pieces (a straight span between
    two corners: one piece); closed: back to the first (not repeated)."""
    pts = [np.asarray(anchors[0][0], float)]
    pairs = list(zip(anchors, anchors[1:])) + ([(anchors[-1], anchors[0])] if closed and len(anchors) > 2 else [])
    for (p, _hi, ho), (q, hi, _ho) in pairs:
        p, ho, hi, q = (np.asarray(x, float) for x in (p, ho, hi, q))
        straight = np.linalg.norm(ho - p) < 1e-9 and np.linalg.norm(hi - q) < 1e-9
        pts += [q] if straight else bezier_span(p, ho, hi, q, steps)[1:]
    if closed and len(pts) > 2 and np.linalg.norm(pts[-1] - pts[0]) < 1e-9:
        pts.pop()
    return pts


def bezier_curve(anchors, normal, closed=False, steps=BEZIER_STEPS, auto=None):
    """The curve's data. (0.411) auto: which points have automatic tangents (kept: they are worked out again when a
    point moves — auto_handles)."""
    c = {"kind": "bezier", "anchors": [[[float(c) for c in x] for x in a] for a in anchors],
         "normal": [float(c) for c in _unit(normal)], "closed": bool(closed), "steps": int(steps)}
    if auto is not None and any(auto):
        c["auto"] = [bool(a) for a in list(auto)[:len(anchors)]] + [False] * max(0, len(anchors) - len(auto))
    return c


def smooth_anchor(point, handle_out):
    """A smooth anchor: its handles opposite each other (the one dragged out, the other mirrored)."""
    p, h = np.asarray(point, float), np.asarray(handle_out, float)
    return [p, 2 * p - h, h]


AUTO_HANDLE = 2.5614        # (0.411) Blender's automatic tangents: each about 0.39 of its span (its calchandleNurb)


def auto_handles(anchors, auto, closed=False):
    """(0.411, the owner: «esperava nós na linha que podem ser movidos criando a curva — faça como o Blender») The
    anchors [[point, handle in, handle out]] with the tangents of those marked `auto` worked out from their
    neighbours, as Blender's «Auto» handles: along the bisector of the two spans meeting there, each about 0.39 of its
    span — the curve passes smoothly through every point. An open curve's end: its one tangent towards the next
    point (the other none). Two points only: a straight span."""
    pts = [np.asarray(a[0], float) for a in anchors]
    out = [[np.asarray(x, float).copy() for x in a] for a in anchors]
    n = len(pts)
    if n < 2:
        return out
    for k in range(n):
        if not (auto and k < len(auto) and auto[k]):
            continue
        p = pts[k]
        first, last = not closed and k == 0, not closed and k == n - 1
        nxt = pts[(k + 1) % n] if not last else 2 * p - pts[k - 1]
        prev = pts[k - 1] if not first else 2 * p - nxt
        da, db = p - prev, nxt - p
        la, lb = float(np.linalg.norm(da)), float(np.linalg.norm(db))
        tvec = (da / la if la > 1e-12 else 0.0) + (db / lb if lb > 1e-12 else 0.0)
        lt = float(np.linalg.norm(tvec))
        if lt < 1e-9:                                # (it turns back on itself: a corner)
            out[k] = [p.copy(), p.copy(), p.copy()]
            continue
        d = tvec / lt
        out[k] = [p.copy(), p.copy() if first else p - d * la / AUTO_HANDLE,
                  p.copy() if last else p + d * lb / AUTO_HANDLE]
    return out


def split_span(anchors, k, t=0.5):
    """(0.411) The anchors with a new point on span k (from point k to the next) at `t` — the curve's shape kept (de
    Casteljau): (new anchors, the new point's index)."""
    out = [[np.asarray(x, float).copy() for x in a] for a in anchors]
    j = (k + 1) % len(out)
    p0, p1, p2, p3 = out[k][0], out[k][2], out[j][1], out[j][0]
    q0, q1, q2 = p0 + (p1 - p0) * t, p1 + (p2 - p1) * t, p2 + (p3 - p2) * t
    r0, r1 = q0 + (q1 - q0) * t, q1 + (q2 - q1) * t
    s = r0 + (r1 - r0) * t
    out[k][2], out[j][1] = q0, q2
    out.insert(k + 1, [s, r0, r1])
    return out, k + 1


def span_middles(anchors, closed=False):
    """(0.411) The curve's point halfway along each span (by its parameter) — where a point can be added."""
    n = len(anchors)
    spans = n if closed and n > 2 else n - 1
    return [split_span(anchors, k)[0][k + 1][0] for k in range(max(spans, 0))]


# ---------------------------------------------------------------- a profile's sides (0.375: a wall's elevation)

PROFILE_ARC_DEG = 5.0       # a profile's arc in pieces of at most this many degrees (an arch reads round)
PROFILE_BEZIER_STEPS = 16


def side_points(p, q, side):
    """The points of a profile's side from p to q (2D), after p, q the last: straight — [q]; {"kind": "arc",
    "through": m} — the arc from p through m to q; {"kind": "bezier", "h1", "h2"} — the cubic from p to q."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    if not side:
        return [q]
    if side.get("kind") == "arc":
        m = np.asarray(side["through"], float)
        found = arc_through((p[0], p[1], 0.0), (m[0], m[1], 0.0), (q[0], q[1], 0.0))
        if found is None:
            return [q]
        centre, normal, angle = found
        pts = arc_points(centre, normal, (p[0], p[1], 0.0), angle, segments_for(angle, PROFILE_ARC_DEG))
        out = [np.array((v[0], v[1])) for v in pts[1:]]
        out[-1] = q.copy()
        return out
    if side.get("kind") == "bezier":
        pts = bezier_span((p[0], p[1], 0.0), (*side["h1"], 0.0), (*side["h2"], 0.0), (q[0], q[1], 0.0),
                          PROFILE_BEZIER_STEPS)
        out = [np.array((v[0], v[1])) for v in pts[1:]]
        out[-1] = q.copy()
        return out
    return [q]


def profile_outline(corners, sides=None):
    """A closed profile's outline [(x, y)]: its corners, its curved sides in pieces (sides[i] runs from corner i to
    corner i + 1; None or missing: straight)."""
    pts = [np.asarray(c, float) for c in corners]
    sides = list(sides or [])
    out = []
    for i, p in enumerate(pts):
        out.append(p)
        side = sides[i] if i < len(sides) else None
        if side:
            out += side_points(p, pts[(i + 1) % len(pts)], side)[:-1]
    return [(float(x), float(y)) for x, y in out]


def fillet(corners, sides, k, radius):
    """(0.380) The profile (corners, sides) with its corner k rounded by an arc of `radius` tangent to its two sides,
    both straight — the corner becomes two, where the arc touches each side, and the side between them that arc
    (through its middle). The radius is kept to what the shorter of the two sides allows. (corners, sides, radius) —
    or None: a curved side there, a straight angle, no radius."""
    n = len(corners)
    if n < 3 or not radius or radius <= 0 or sides[(k - 1) % n] or sides[k]:
        return None
    p = np.asarray(corners[k], dtype=float)
    a, b = np.asarray(corners[(k - 1) % n], dtype=float), np.asarray(corners[(k + 1) % n], dtype=float)
    la, lb = float(np.linalg.norm(a - p)), float(np.linalg.norm(b - p))
    if la < 1e-9 or lb < 1e-9:
        return None
    u1, u2 = (a - p) / la, (b - p) / lb
    half = math.acos(float(np.clip(u1 @ u2, -1.0, 1.0))) / 2
    if half < 1e-3 or math.pi / 2 - half < 1e-3:
        return None
    reach = radius / math.tan(half)                  # from the corner to where the arc touches each side
    if reach > 0.98 * min(la, lb):
        reach = 0.98 * min(la, lb)
        radius = reach * math.tan(half)
    bisector = (u1 + u2) / np.linalg.norm(u1 + u2)
    middle = p + bisector * (radius / math.sin(half) - radius)
    new_corners = list(corners[:k]) + [tuple(map(float, p + u1 * reach)), tuple(map(float, p + u2 * reach))] + \
        list(corners[k + 1:])
    new_sides = list(sides[:k]) + [{"kind": "arc", "through": tuple(map(float, middle))}, None] + list(sides[k + 1:])
    return new_corners, new_sides, float(radius)


def side_text(side):
    """A side as kept in the IFC: "" straight, "a:x,z" an arc through (x, z), "b:x1,z1,x2,z2" a Bézier's handles."""
    if not side:
        return ""
    if side.get("kind") == "arc":
        return "a:{:.6f},{:.6f}".format(*side["through"])
    if side.get("kind") == "bezier":
        return "b:{:.6f},{:.6f},{:.6f},{:.6f}".format(*side["h1"], *side["h2"])
    return ""


def side_of(text, sx=1.0, sz=1.0):
    """side_text read back, its points stretched by (sx, sz) — None when straight (or not understood)."""
    text = (text or "").strip()
    try:
        if text.startswith("a:"):
            x, z = (float(v) for v in text[2:].split(","))
            return {"kind": "arc", "through": (x * sx, z * sz)}
        if text.startswith("b:"):
            x1, z1, x2, z2 = (float(v) for v in text[2:].split(","))
            return {"kind": "bezier", "h1": (x1 * sx, z1 * sz), "h2": (x2 * sx, z2 * sz)}
    except ValueError:
        return None
    return None


# ---------------------------------------------------------------- freehand

def simplify(points, tol):
    """The points kept where the line bends more than `tol` (Douglas–Peucker), its ends always."""
    pts = [np.asarray(p, float) for p in points]
    if len(pts) < 3:
        return pts
    keep = np.zeros(len(pts), dtype=bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        a, b = pts[i], pts[j]
        d = b - a
        dd = float(d @ d)
        far, at = -1.0, None
        for k in range(i + 1, j):
            w = pts[k] - a
            dist = float(np.linalg.norm(w - d * (float(w @ d) / dd))) if dd > 1e-24 else float(np.linalg.norm(w))
            if dist > far:
                far, at = dist, k
        if at is not None and far > tol:
            keep[at] = True
            stack += [(i, at), (at, j)]
    return [p for p, k in zip(pts, keep) if k]


# ---------------------------------------------------------------- what a curve is made of

def curve_points(curve):
    """The points of an arc or a Bézier curve as it is drawn (a pie: the centre, then round), or None for the
    others (their points are the lines)."""
    kind = curve.get("kind")
    if kind == "arc":
        pts = arc_points(curve["centre"], curve["normal"], curve["start"], curve["angle"], curve.get("segments"))
        return ([np.asarray(curve["centre"], float)] + pts) if curve.get("pie") else pts
    if kind == "bezier":
        return bezier_points(curve["anchors"], curve.get("closed"), curve.get("steps", BEZIER_STEPS))
    if kind == "ellipse":                                         # (0.458)
        return ellipse_points(curve)
    return None


def is_closed(curve):
    return bool(curve.get("pie") or curve.get("closed") or
                (curve.get("kind") in ("arc", "ellipse") and abs(abs(curve.get("angle", 0.0)) - 360.0) < 1e-9))


def transform_curve(curve, matrix):
    """The curve's data moved by the 4x4 `matrix` (a move, a turn, a mirror: its points and its normal)."""
    if not curve:
        return curve
    m = np.asarray(matrix, dtype=float)
    pt = lambda p: [float(c) for c in m[:3, :3] @ np.asarray(p, float) + m[:3, 3]]     # noqa: E731
    out = dict(curve)
    flip = float(np.linalg.det(m[:3, :3])) < 0
    if "normal" in out:
        n = _unit(np.linalg.inv(m[:3, :3]).T @ np.asarray(out["normal"], float))
        out["normal"] = [float(c) for c in n]
    if curve.get("kind") == "arc":
        out["centre"], out["start"] = pt(curve["centre"]), pt(curve["start"])
        if flip:                                      # (a mirror turns it the other way round its new normal)
            out["angle"] = -float(curve["angle"])
    elif curve.get("kind") == "bezier":
        out["anchors"] = [[pt(x) for x in a] for a in curve["anchors"]]
    elif curve.get("kind") == "ellipse":                          # (0.458) its half-axes carried: the other one's
        _c, a, b = ellipse_axes(curve)                            # length and side on the new normal (a mirror: the
        out["centre"], out["axis"] = pt(curve["centre"]), pt(curve["axis"])      # other side)
        a, b = m[:3, :3] @ a, m[:3, :3] @ b
        out["minor"] = float(b @ _unit(np.cross(np.asarray(out["normal"], float), a)))
    return out
