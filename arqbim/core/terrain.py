"""Terrain geometry (0.155, Phase 7, step 3): survey points to a triangulated surface (Delaunay, shapely), the
solid under it (as Revit's toposolid: down to a base, its sides upright — so it is cut in plans and sections like
any solid), its contour lines, the height at a point, each triangle's slope; and the points read from a survey's
text file. Pure numpy (and shapely): no Qt, no IFC."""

import math
import re

import numpy as np

UP = 0.05                  # a face facing up at least this much (its normal's z) is the terrain's surface
DEFAULT_INTERVAL = 1.0     # m between contour lines…
MAJOR_EVERY = 5            # …every fifth a major one (thicker, its height written)
DEFAULT_DEPTH = 1.0        # m from the lowest point down to the solid's base
MIN_POINTS = 3
MAX_LEVELS = 2000          # (contour lines: never more levels than this, whatever the interval)


def unique_points(points, tol=1e-6):
    """The points (x, y, z) with one per plan position (the last given wins) — (N, 3)."""
    pts = np.asarray(points, dtype=float).reshape(-1, 3)
    if not len(pts):
        return pts
    keys = np.round(pts[:, :2] / tol).astype(np.int64)
    _u, last = np.unique(keys[::-1], axis=0, return_index=True)
    return pts[::-1][np.sort(last)][::-1] if len(last) else pts


def tin(points):
    """The surface through the points: (verts (N, 3), triangles (M, 3) counter-clockwise seen from above) — or
    None when they do not make one (fewer than three, all in a line)."""
    import shapely
    from shapely.geometry import MultiPoint
    verts = unique_points(points)
    if len(verts) < MIN_POINTS:
        return None
    index = {(round(float(x), 6), round(float(y), 6)): k for k, (x, y, _z) in enumerate(verts)}
    found = shapely.delaunay_triangles(MultiPoint([(float(x), float(y)) for x, y, _z in verts]))
    tris = []
    for tri in getattr(found, "geoms", ()):
        corners = [index.get((round(x, 6), round(y, 6))) for x, y in list(tri.exterior.coords)[:3]]
        if None in corners or len(set(corners)) < 3:
            continue
        a, b, c = (verts[k] for k in corners)
        cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(cross) < 1e-12:
            continue
        tris.append(corners if cross > 0 else [corners[0], corners[2], corners[1]])
    if not tris:
        return None
    return verts, np.array(tris, dtype=np.int64)


def boundary_edges(tris):
    """The surface's border: its edges (a, b) of one triangle only, each the way its triangle goes round
    (counter-clockwise: the surface on the left)."""
    directed = np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    keys = np.sort(directed, axis=1)
    _u, inverse, counts = np.unique(keys, axis=0, return_inverse=True, return_counts=True)
    return directed[counts[inverse.reshape(-1)] == 1]


def solid(verts, tris, base):
    """The closed solid under the surface down to the height `base`: (verts, triangles) — the surface on top, the
    same triangles (turned over) at the base, an upright side along each border edge; every face outwards."""
    verts = np.asarray(verts, dtype=float)
    tris = np.asarray(tris, dtype=np.int64)
    n = len(verts)
    bottom = verts.copy()
    bottom[:, 2] = float(base)
    out = [tris, tris[:, ::-1] + n]
    border = boundary_edges(tris)
    if len(border):
        a, b = border[:, 0], border[:, 1]
        out += [np.column_stack((a, a + n, b + n)), np.column_stack((a, b + n, b))]
    return np.vstack((verts, bottom)), np.vstack(out)


def surface_of(verts, tris, normals=None):
    """Of a terrain solid's mesh, the triangles of its surface (those facing up)."""
    verts, tris = np.asarray(verts, dtype=float), np.asarray(tris, dtype=np.int64)
    if normals is None:
        p = verts[tris]
        normals = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
        normals /= np.maximum(np.linalg.norm(normals, axis=1), 1e-12)[:, None]
    return tris[np.asarray(normals)[:, 2] > UP]


def drawn_edges(mesh, direction=None):
    """(K, 2) vertex pairs of a terrain solid's (TriMesh) edges as they are drawn: its edges but those between two
    triangles of its surface (a terrain shows its contour lines, not its triangles) — and, seen along `direction`,
    the surface's outline (a hill's skyline in an elevation)."""
    pairs, faces = mesh.edge_array()
    up = np.asarray(mesh.normals)[:, 2] > UP
    if len(pairs):
        both = (faces[:, 1] >= 0) & up[faces[:, 0]] & up[np.maximum(faces[:, 1], 0)]
        pairs = pairs[~both]
    if direction is None or not len(mesh.tris):
        return pairs
    uniq, counts, first, second, _cos = mesh._edge_table()
    second = np.maximum(second, 0)
    s = np.sign(np.where(np.abs(np.asarray(mesh.normals) @ np.asarray(direction, dtype=float)) < 1e-9, 0.0,
                         np.asarray(mesh.normals) @ np.asarray(direction, dtype=float)))
    turns = (counts == 2) & up[first] & up[second] & (s[first] != s[second])
    return np.concatenate((pairs, uniq[turns])) if np.any(turns) else pairs


def height_at(verts, tris, xy):
    """The surface's height over the plan point xy, or None outside it."""
    p = np.asarray(verts, dtype=float)[np.asarray(tris, dtype=np.int64)]
    x, y = float(xy[0]), float(xy[1])
    a, b, c = p[:, 0], p[:, 1], p[:, 2]
    det = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    ok = np.abs(det) > 1e-15
    det = np.where(ok, det, 1.0)
    l1 = ((b[:, 1] - c[:, 1]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (y - c[:, 1])) / det
    l2 = ((c[:, 1] - a[:, 1]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (y - c[:, 1])) / det
    l3 = 1.0 - l1 - l2
    inside = ok & (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
    k = np.flatnonzero(inside)
    if not len(k):
        return None
    k = k[0]
    return float(l1[k] * a[k, 2] + l2[k] * b[k, 2] + l3[k] * c[k, 2])


def levels(lo, hi, interval=DEFAULT_INTERVAL):
    """The contour heights between lo and hi: the multiples of `interval`."""
    interval = max(float(interval), 1e-3)
    first, last = math.ceil(lo / interval - 1e-9), math.floor(hi / interval + 1e-9)
    if last - first > MAX_LEVELS:
        return []
    return [k * interval for k in range(first, last + 1)]


def is_major(level, interval=DEFAULT_INTERVAL, every=MAJOR_EVERY):
    return every > 0 and round(level / max(interval, 1e-3)) % every == 0


def contours(verts, tris, interval=DEFAULT_INTERVAL, top=None):
    """The contour lines of the surface (its triangles `tris`), every `interval` metres (those up to `top` only,
    when given): [(height, segments (K, 2, 3))], lowest first."""
    verts, tris = np.asarray(verts, dtype=float), np.asarray(tris, dtype=np.int64)
    if not len(tris):
        return []
    p = verts[tris]                                         # (M, 3, 3)
    z = p[:, :, 2]
    hi = float(z.max()) if top is None else min(float(z.max()), float(top))
    out = []
    for level in levels(float(z.min()), hi, interval):
        h = level + 1e-9 * max(1.0, abs(level))             # (a point exactly at the height: just under it)
        above = z > h
        n_above = above.sum(axis=1)
        cross = (n_above == 1) | (n_above == 2)
        if not np.any(cross):
            continue
        q, qa = p[cross], above[cross]
        changes, points = [], []
        for i, j in ((0, 1), (1, 2), (2, 0)):              # (each edge: where the height is crossed on it)
            ch = qa[:, i] != qa[:, j]
            zi, zj = q[:, i, 2], q[:, j, 2]
            t = np.where(ch, (h - zi) / np.where(np.abs(zj - zi) > 1e-15, zj - zi, 1.0), 0.0)
            point = q[:, i] + (q[:, j] - q[:, i]) * t[:, None]
            point[:, 2] = level
            changes.append(ch)
            points.append(point)
        changes, points = np.stack(changes, axis=1), np.stack(points, axis=1)      # (K, 3), (K, 3, 3)
        two = np.argsort(~changes, axis=1, kind="stable")[:, :2]                   # (the two edges crossed)
        segs = np.take_along_axis(points, two[:, :, None], axis=1)[changes.sum(axis=1) == 2]
        if len(segs):
            out.append((float(level), segs))
    return out


# (0.202) a major contour line's height written along it: this often, and on a piece at least this long (m on paper)
LABEL_EVERY = 0.12
LABEL_SHORTEST = 0.025


def contour_text(height, sep=","):
    """A contour line's height as written on it: "12", "12,5", "-3,25"."""
    text = "{:.2f}".format(float(height)).rstrip("0").rstrip(".")
    return ("0" if text in ("-0", "") else text).replace(".", sep)


def chains(segs, digits=6):
    """A contour line's segments (K, 2, d), as they come out of `contours` (in no order), joined end to end:
    [(N, d) polylines] — a closed one ends where it starts."""
    from collections import defaultdict, deque
    segs = np.asarray(segs, dtype=float)
    key = lambda p: (round(float(p[0]), digits), round(float(p[1]), digits))        # noqa: E731
    ends = defaultdict(list)
    for k, (a, b) in enumerate(segs):
        ends[key(a)].append((k, 0))
        ends[key(b)].append((k, 1))
    used = np.zeros(len(segs), dtype=bool)
    out = []
    for k in range(len(segs)):
        if used[k]:
            continue
        used[k] = True
        line = deque((segs[k][0], segs[k][1]))
        for forward in (True, False):
            while True:
                tip = line[-1] if forward else line[0]
                step = next(((j, e) for j, e in ends[key(tip)] if not used[j]), None)
                if step is None:
                    break
                used[step[0]] = True
                other = segs[step[0]][1 - step[1]]
                if forward:
                    line.append(other)
                else:
                    line.appendleft(other)
        out.append(np.array(line))
    return out


def label_spots(line, every, shortest):
    """Where a polyline's label goes: spread along it, one for each `every` metres of it (one at least, in its
    middle), none on a piece shorter than `shortest` — [(point (2,), angle in degrees along it, turned to read
    from below or from the right: -90 to 90)]."""
    p = np.asarray(line, dtype=float)[:, :2]
    d = np.diff(p, axis=0)
    lengths = np.hypot(d[:, 0], d[:, 1])
    total = float(lengths.sum())
    if total < shortest or total < 1e-9:
        return []
    count = max(1, int(total // max(every, 1e-9)))
    run = np.concatenate(([0.0], np.cumsum(lengths)))

    def at(s):
        s = min(max(s, 0.0), total)
        i = int(min(max(np.searchsorted(run, s, side="right") - 1, 0), len(d) - 1))
        return p[i] + d[i] * ((s - run[i]) / max(lengths[i], 1e-12))

    half = min(shortest, total) / 2                 # (its way: across the label's length, not one small piece's)
    out = []
    for k in range(count):
        s = (k + 0.5) * total / count
        point, way = at(s), at(s + half) - at(s - half)
        angle = math.degrees(math.atan2(way[1], way[0]))
        if angle > 90.0:
            angle -= 180.0
        elif angle <= -90.0:
            angle += 180.0
        out.append((point, angle))
    return out


def slopes(verts, tris):
    """Each triangle's slope (%): how much it rises for a metre across."""
    p = np.asarray(verts, dtype=float)[np.asarray(tris, dtype=np.int64)]
    n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    horizontal = np.hypot(n[:, 0], n[:, 1])
    return np.where(np.abs(n[:, 2]) > 1e-12, horizontal / np.maximum(np.abs(n[:, 2]), 1e-12) * 100.0, np.inf)


# (0.156) slope bands, as the urban plans' analysis of a site: up to each slope (%), its colour
SLOPE_BANDS = ((5.0, "#5fae5f"), (10.0, "#c9d65a"), (15.0, "#f2c14e"), (25.0, "#e8833a"), (math.inf, "#c8443a"))


def slope_bands(verts, tris):
    """Each triangle's band (index into SLOPE_BANDS) by its slope."""
    s = slopes(verts, tris)
    limits = np.array([b for b, _c in SLOPE_BANDS[:-1]])
    return np.searchsorted(limits, s, side="left")


def plan_area(verts, tris):
    p = np.asarray(verts, dtype=float)[np.asarray(tris, dtype=np.int64)]
    a, b = p[:, 1, :2] - p[:, 0, :2], p[:, 2, :2] - p[:, 0, :2]
    return float(np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]).sum() / 2.0)


_NUMBER = re.compile(r"^[+-]?(\d+([.,]\d*)?|[.,]\d+)([eE][+-]?\d+)?$")


def parse_points(text):
    """The points (x, y, z) of a survey's text file — "x y z", "x;y;z", "x,y,z", "x<tab>y<tab>z", with a point's
    number before them and a code after them or not, a header line or not; decimals with "." (or with "," when
    the values are split by ";", tabs or spaces). Returns ((N, 3) points, lines skipped)."""
    out, skipped = [], 0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ";" in line or "\t" in line:
            parts, comma_decimal = re.split(r"[;\t]", line), True
        elif "," in line:
            spaced = line.split()                           # "100,5 200,3 12,1": commas are decimals
            numeric = [p for p in spaced if _NUMBER.match(p)]
            if len(numeric) >= 3 and len(numeric) >= len(spaced) - 1:
                parts, comma_decimal = spaced, True
            else:                                           # "100.5,200.3,12.1" / "1, 100.5, 200.3, 12.1"
                parts, comma_decimal = line.split(","), False
        else:
            parts, comma_decimal = line.split(), True
        values, written = [], []
        for part in parts:
            part = part.strip()
            if _NUMBER.match(part) and ("," not in part or comma_decimal):
                values.append(float(part.replace(",", ".")))
                written.append(part)
        if len(values) < 3:
            skipped += 1
            continue
        if len(values) >= 4 and not any(c in written[0] for c in ".,eE"):
            values = values[1:]                             # (the point's number first: a whole number)
        out.append(values[:3])
    return np.array(out, dtype=float).reshape(-1, 3), skipped
