"""(0.314) Fill patterns, as Revit's and AutoCAD's: each a few families of parallel lines, whole, dashed or dotted.
Two kinds:

- drafting patterns, measured on paper in mm, the same at any scale: what is cut (concrete, sand, insulation, earth…);
- model patterns, measured on the building in m, bigger at a bigger scale: what a surface is made of (tiles, bricks,
  stone courses, boards, roof tiles).

A family: (angle in degrees, x0, y0, shift, step, dashes) — its lines at `angle` through (x0, y0), each next one `step`
across them and `shift` along them; dashes: (drawn, -gap, …) with 0 a dot, () a continuous line. "solid" fills all
(no lines). Pure data and NumPy: segments() covers a box, on_triangles() the faces of a mesh."""

import math
from dataclasses import dataclass

import numpy as np

SOLID = "solid"
LIMIT = 250000                 # segments a family may give at most (a pattern far too fine for its box gives none)


@dataclass(frozen=True)
class Pattern:
    key: str
    model: bool                # measured on the building (m); else on paper (mm)
    families: tuple = ()
    name: str = ""             # (0.318) a project's pattern's name (the program's are named in the language)

    @property
    def solid(self):
        return self.key == SOLID

    @property
    def builtin(self):
        return self.key in _BUILTIN


def _grid(across, up):
    """Lines along and up: a grid of `across` × `up` (tiles, panels)."""
    return ((0.0, 0.0, 0.0, 0.0, up, ()), (90.0, 0.0, 0.0, 0.0, across, ()))


def _bond(length, height):
    """Courses `height` high of units `length` long, each course's joints halfway along the one below's (running
    bond: bricks, blocks, stone, roof tiles)."""
    return ((0.0, 0.0, 0.0, 0.0, height, ()),
            (90.0, 0.0, 0.0, height, -length / 2.0, (height, -height)))


def _zigzag(width, height):
    """Zigzags `width` apart, `height` high, a row every two heights (insulation, as batting)."""
    a = math.atan2(height, width / 2.0)
    side = math.hypot(width / 2.0, height)
    c, s = width * math.cos(a), width * math.sin(a)
    deg = math.degrees(a)
    return ((deg, 0.0, 0.0, -c, s, (side, -side)), (-deg, width / 2.0, height, c, s, (side, -side)))


_DRAFTING = (
    Pattern(SOLID, False),
    Pattern("diagonal", False, ((45.0, 0.0, 0.0, 0.0, 1.0, ()),)),
    Pattern("diagonal_wide", False, ((45.0, 0.0, 0.0, 0.0, 2.0, ()),)),
    Pattern("diagonal_back", False, ((135.0, 0.0, 0.0, 0.0, 1.0, ()),)),
    Pattern("cross", False, ((45.0, 0.0, 0.0, 0.0, 1.5, ()), (135.0, 0.0, 0.0, 0.0, 1.5, ()))),
    Pattern("horizontal", False, ((0.0, 0.0, 0.0, 0.0, 1.0, ()),)),
    Pattern("vertical", False, ((90.0, 0.0, 0.0, 0.0, 1.0, ()),)),
    Pattern("square", False, _grid(2.0, 2.0)),
    # aggregate: dots in staggered rows and short strokes three ways
    Pattern("concrete", False, ((0.0, 0.0, 0.0, 0.9, 1.1, (0.0, -1.8)),
                                (50.0, 0.3, 0.4, 1.3, 2.3, (0.45, -3.6)),
                                (170.0, 0.9, 0.2, 1.7, 2.1, (0.4, -3.9)),
                                (290.0, 0.5, 0.9, 1.1, 2.7, (0.35, -4.2)))),
    Pattern("sand", False, ((0.0, 0.0, 0.0, 0.35, 0.5, (0.0, -0.7)),)),
    Pattern("insulation", False, _zigzag(1.6, 1.2)),
    Pattern("earth", False, ((45.0, 0.0, 0.0, 0.0, 2.4, (2.5, -1.0)),
                             (45.0, -0.85, 0.85, 1.75, 2.4, (0.0, -1.75)))),
    Pattern("wood", False, ((0.0, 0.0, 0.0, 2.2, 0.9, (3.5, -0.9)),)),
    Pattern("steel", False, ((45.0, 0.0, 0.0, 0.0, 2.4, ()), (45.0, -0.354, 0.354, 0.0, 2.4, ()))),
)
_MODEL = (
    Pattern("tile_10", True, _grid(0.10, 0.10)),
    Pattern("tile_15", True, _grid(0.15, 0.15)),
    Pattern("tile_20", True, _grid(0.20, 0.20)),
    Pattern("tile_30", True, _grid(0.30, 0.30)),
    Pattern("tile_30x60", True, _grid(0.60, 0.30)),
    Pattern("brick", True, _bond(0.25, 0.065)),
    Pattern("block", True, _bond(0.50, 0.20)),
    Pattern("stone", True, _bond(0.60, 0.30)),
    Pattern("boards_v", True, ((90.0, 0.0, 0.0, 0.0, 0.15, ()),)),
    Pattern("boards_h", True, ((0.0, 0.0, 0.0, 0.0, 0.15, ()),)),
    Pattern("roof_tiles", True, _bond(0.21, 0.33)),
    Pattern("panels", True, _grid(1.20, 2.40)),
)
PATTERNS = {p.key: p for p in _DRAFTING + _MODEL}
DRAFTING = tuple(p.key for p in _DRAFTING)          # (in the lists: drafting first, then model)
MODEL = (SOLID,) + tuple(p.key for p in _MODEL)
_BUILTIN = dict(PATTERNS)
PROJECT = "p:"                                      # (0.318) a project's pattern's key: "p:" + its uid


def get(key):
    """The pattern of a key, or None (none, or not known)."""
    return PATTERNS.get(key)


def set_project(patterns):
    """(0.318) The open project's own patterns (read from its IFC) beside the program's; () : the program's alone."""
    for key in [k for k in PATTERNS if k not in _BUILTIN]:
        del PATTERNS[key]
    for p in patterns:
        if p.key not in _BUILTIN:
            PATTERNS[p.key] = p


def project_patterns():
    """(0.318) The project's own patterns, by name."""
    return sorted((p for p in PATTERNS.values() if not p.builtin), key=lambda p: p.name.lower())


def drafting_keys():
    """(0.318) The drafting patterns to choose from: the program's, then the project's."""
    return DRAFTING + tuple(p.key for p in project_patterns() if not p.model)


def model_keys():
    """(0.318) The model patterns to choose from: the program's, then the project's."""
    return MODEL + tuple(p.key for p in project_patterns() if p.model)


def label(key, translate):
    """(0.318) A pattern's name as shown: a project's its own, the program's in the language (translate(key))."""
    pattern = PATTERNS.get(key)
    if pattern is not None and pattern.name:
        return pattern.name
    return translate("pat." + key) if key else translate("pat.none")


def simple(key, name, model, angle, spacing, crossed=False):
    """(0.318) A pattern of parallel lines `spacing` apart at `angle` (crossed: and the same at a right angle to them)."""
    families = ((float(angle), 0.0, 0.0, 0.0, float(spacing), ()),)
    if crossed:
        families += ((float(angle) + 90.0, 0.0, 0.0, 0.0, float(spacing), ()),)
    return Pattern(key, bool(model), families, name)


def shape_of(pattern):
    """(0.318) How the pattern editor shows a pattern: ("lines" | "cross", angle, spacing) when it is that simple, else
    ("custom", None, None)."""
    fam = pattern.families
    if len(fam) in (1, 2) and all(not f[5] and abs(f[1]) < 1e-12 and abs(f[2]) < 1e-12 and abs(f[3]) < 1e-12
                                  for f in fam):
        if len(fam) == 1:
            return "lines", fam[0][0], fam[0][4]
        if abs(fam[0][4] - fam[1][4]) < 1e-12 and abs((fam[1][0] - fam[0][0]) % 180.0 - 90.0) < 1e-9:
            return "cross", fam[0][0], fam[0][4]
    return "custom", None, None


def segments(key, box, scale=1.0):
    """(segments (K, 2, 2), dots (M, 2)) of a pattern covering a box (x0, y0, x1, y1) — its sizes times `scale` (its
    mm or m to the box's units), its lines through (0, 0) so that neighbouring boxes meet. A solid pattern, none or
    one not known: nothing."""
    pattern = PATTERNS.get(key)
    if pattern is None:
        return np.zeros((0, 2, 2)), np.zeros((0, 2))
    return families_segments(pattern.families, box, scale)


def families_segments(families, box, scale=1.0):
    """(0.317) segments() of families of lines given as they are (a pattern made on the spot: a category's lines at an
    angle and a spacing)."""
    empty = np.zeros((0, 2, 2)), np.zeros((0, 2))
    if not families or scale <= 0:
        return empty
    x0, y0, x1, y1 = (float(v) for v in box)
    if not (x1 > x0 and y1 > y0):
        return empty
    corners = np.array(((x0, y0), (x1, y0), (x1, y1), (x0, y1)))
    segs, dots = [], []
    for family in families:
        s, d = _family(family, corners, scale)
        segs.append(s)
        dots.append(d)
    return np.concatenate(segs), np.concatenate(dots)


def _family(family, corners, scale):
    angle, ox, oy, shift, step, dashes = family
    empty = np.zeros((0, 2, 2)), np.zeros((0, 2))
    step, shift = step * scale, shift * scale
    if abs(step) < 1e-12:
        return empty
    a = math.radians(angle)
    d, n = np.array((math.cos(a), math.sin(a))), np.array((-math.sin(a), math.cos(a)))
    o = np.array((ox, oy)) * scale
    along, across = corners @ d, corners @ n
    lo, hi = sorted(((across.min() - o @ n) / step, (across.max() - o @ n) / step))
    ks = np.arange(math.ceil(lo), math.floor(hi) + 1, dtype=float)
    if not len(ks):
        return empty
    w0, w1 = float(along.min()), float(along.max())          # (the box along the lines: the same for each)
    offsets = o @ n + ks * step                               # (each line across)
    if not dashes:
        if len(ks) > LIMIT:
            return empty
        a0 = offsets[:, None] * n + w0 * d
        a1 = offsets[:, None] * n + w1 * d
        return np.stack((a0, a1), axis=1), np.zeros((0, 2))
    period = float(sum(abs(v) for v in dashes)) * scale
    if period < 1e-12:
        return empty
    phases = o @ d + ks * shift                               # (where each line's pattern starts, along)
    segs, dots = [], []
    at = 0.0
    for dash in dashes:
        length = abs(dash) * scale
        if dash >= 0:
            first = np.mod(phases + at, period)               # (in 0…period)
            m = np.arange(math.floor((w0 - length) / period) - 1, math.ceil(w1 / period) + 2, dtype=float)
            if len(ks) * len(m) > LIMIT:
                return empty
            start = first[:, None] + m[None, :] * period      # (K, M)
            keep = (start + length >= w0) & (start <= w1)
            rows = np.broadcast_to(offsets[:, None], start.shape)[keep]
            start = start[keep]
            if dash == 0:
                dots.append(rows[:, None] * n + start[:, None] * d)
            else:
                end = np.minimum(start + length, w1)
                start = np.maximum(start, w0)
                real = end - start > 1e-12
                rows, start, end = rows[real], start[real], end[real]
                segs.append(np.stack((rows[:, None] * n + start[:, None] * d,
                                      rows[:, None] * n + end[:, None] * d), axis=1))
        at += length
    return (np.concatenate(segs) if segs else np.zeros((0, 2, 2)),
            np.concatenate(dots) if dots else np.zeros((0, 2)))


def clip_to_triangle(segs, dots, tri):
    """The parts of segments (K, 2, 2) and the dots (M, 2) inside a triangle (3, 2)."""
    tri = np.asarray(tri, dtype=float)
    if (tri[1, 0] - tri[0, 0]) * (tri[2, 1] - tri[0, 1]) - (tri[1, 1] - tri[0, 1]) * (tri[2, 0] - tri[0, 0]) < 0:
        tri = tri[::-1]                                       # (counter-clockwise: each edge's inside on its left)
    t0, t1 = np.zeros(len(segs)), np.ones(len(segs))
    inside = np.ones(len(dots), dtype=bool)
    p0 = segs[:, 0] if len(segs) else np.zeros((0, 2))
    dirs = segs[:, 1] - segs[:, 0] if len(segs) else np.zeros((0, 2))
    out = np.zeros(len(segs), dtype=bool)
    for k in range(3):
        a, b = tri[k], tri[(k + 1) % 3]
        inward = np.array((a[1] - b[1], b[0] - a[0]))         # (left of a → b)
        num = (a - p0) @ inward
        den = dirs @ inward
        with np.errstate(divide="ignore", invalid="ignore"):
            t = num / den
        entering, leaving = den > 1e-15, den < -1e-15
        t0 = np.where(entering, np.maximum(t0, t), t0)
        t1 = np.where(leaving, np.minimum(t1, t), t1)
        out |= (~entering & ~leaving) & (num > 1e-12)
        if len(dots):
            inside &= (dots - a) @ inward >= -1e-12
    keep = ~out & (t1 - t0 > 1e-9)
    clipped = np.stack((p0[keep] + dirs[keep] * t0[keep, None], p0[keep] + dirs[keep] * t1[keep, None]), axis=1) \
        if keep.any() else np.zeros((0, 2, 2))
    return clipped, dots[inside] if len(dots) else np.zeros((0, 2))


def face_axes(normal):
    """(u, v) unit axes on a face to lay a model pattern on it: on a wall, along it and up; on a floor or a ceiling,
    east and north; on a slope, along it level and up the slope."""
    nrm = np.asarray(normal, dtype=float)
    nrm = nrm / max(float(np.linalg.norm(nrm)), 1e-12)
    if abs(nrm[2]) > 0.999:
        return np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0))
    u = np.cross((0.0, 0.0, 1.0), nrm)
    u /= np.linalg.norm(u)
    return u, np.cross(nrm, u)


def turned_axes(normal, angle):
    """(0.332) A face's pattern axes (face_axes) turned `angle` degrees about its normal (u towards v)."""
    u, v = face_axes(normal)
    a = math.radians(angle)
    return u * math.cos(a) + v * math.sin(a), v * math.cos(a) - u * math.sin(a)


def on_triangles(key, verts, normals, scale=1.0, lift=0.0, frame=None):
    """A model pattern laid on triangles (T, 3, 3) with their normals (T, 3), in metres: its lines' segments in 3D
    (K, 2, 3), a hair (`lift`) off each face; dots as short segments. Each face's pattern starts where the others'
    do (a wall's tiles meet at a corner's height). frame (0.332): (normal) -> (origin, u, v) of a face's pattern
    aligned by hand, or None (as always: from the world's origin, face_axes)."""
    pattern = PATTERNS.get(key)
    verts = np.asarray(verts, dtype=float).reshape(-1, 3, 3)
    if pattern is None or not pattern.families or not len(verts):
        return np.zeros((0, 2, 3))
    out = []
    for tri, nrm in zip(verts, np.asarray(normals, dtype=float).reshape(-1, 3)):
        aligned = frame(nrm) if frame is not None else None
        if aligned is None:
            origin = np.zeros(3)
            u, v = face_axes(nrm)
        else:
            origin, u, v = aligned
        flat = np.stack(((tri - origin) @ u, (tri - origin) @ v), axis=1)
        lo, hi = flat.min(axis=0), flat.max(axis=0)
        if np.any(hi - lo < 1e-9):
            continue
        segs, dots = segments(key, (lo[0], lo[1], hi[0], hi[1]), scale)
        segs, dots = clip_to_triangle(segs, dots, flat)
        if len(dots):                                      # (a dot: a stroke a millimetre long)
            segs = np.concatenate((segs, np.stack((dots, dots + (0.001, 0.0)), axis=1)))
        if not len(segs):
            continue
        w = nrm / max(np.linalg.norm(nrm), 1e-12)
        depth = float((tri[0] - origin) @ w)
        out.append(origin + segs[..., :1] * u + segs[..., 1:] * v + (depth + lift) * w)
    return np.concatenate(out) if out else np.zeros((0, 2, 3))
