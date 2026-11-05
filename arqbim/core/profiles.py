"""Profiles run along a path (0.174, Phase 10, step 2: the Profile Pen): a skirting board, a cornice (sanca), a dado
rail (friso), an outside cornice (cimalha) — a section swept along a path drawn point by point or round a room, its
corners mitred (each run cut at the bisector of the turn, as a joiner cuts them), broken where a door or a window
crosses it.

A section is a closed polygon in (a, b): a out of the path to its side (into the room), b up from its foot; the
catalogue's in a unit square, scaled to the profile's width (a) and height (b). Pure numpy: the mesh of the swept
solid (its runs' sides, its open ends' caps), every face turned out; the runs' lengths for the cut list."""

import math

import numpy as np

# key -> (IfcCovering PredefinedType, material, (width, height) m, its foot over the floor m, section in a unit
# square — counter-clockwise, (0, 0) at the wall's foot)
PROFILES = {
    "rodape": ("SKIRTINGBOARD", "madeira", (0.015, 0.08), 0.0,
               ((0.0, 0.0), (1.0, 0.0), (1.0, 0.85), (0.6, 1.0), (0.0, 1.0))),
    "sanca": ("MOLDING", "gesso", (0.10, 0.10), None,             # (its foot under the ceiling: see foot)
              ((0.0, 0.0),) + tuple((1.0 - math.cos(math.radians(a)), math.sin(math.radians(a)))
                                    for a in range(10, 90, 10)) + ((1.0, 1.0), (0.0, 1.0))),
    "friso": ("MOLDING", "madeira", (0.02, 0.06), 0.90,
              ((0.0, 0.0), (0.6, 0.0), (1.0, 0.25), (1.0, 0.75), (0.6, 1.0), (0.0, 1.0))),
    "cimalha": ("MOLDING", "pedra", (0.12, 0.15), None,
                ((0.0, 0.0), (0.3, 0.0), (0.3, 0.3), (0.6, 0.3), (0.6, 0.6), (1.0, 0.6), (1.0, 1.0), (0.0, 1.0))),
}
MIN_SIZE, MAX_SIZE = 0.005, 0.60          # m: a section's width and height
STRAIGHT = 1e-6                           # (a turn smaller than this: no joint)
SHARP = 0.10                              # (1 + cos of the turn under this — a turn of over ~154°: the run broken there)
CUSTOM = "custom:"                        # (0.245) a project's own profile's key: "custom:" + its name


def is_custom(key):
    return str(key).startswith(CUSTOM)


def spec(key):
    """(0.245) (IfcCovering PredefinedType, material) of a profile — a project's own: a moulding of wood."""
    if is_custom(key):
        return "MOLDING", "madeira"
    return PROFILES[key][0], PROFILES[key][1]


def unit_section(points):
    """(0.245) A section drawn [(a, b)] (m: a out of the wall, b up) as the catalogue's are: in a unit square,
    counter-clockwise, (0, 0) at its lowest corner by the wall — and its width and height. ValueError when it is
    no area, or too small or too big for a profile."""
    pts = np.asarray([p[:2] for p in points], dtype=float)
    if len(pts) > 3 and np.linalg.norm(pts[0] - pts[-1]) < 1e-9:
        pts = pts[:-1]
    if len(pts) < 3:
        raise ValueError("profile_section")
    lo = pts.min(axis=0)
    size = pts.max(axis=0) - lo
    if not (MIN_SIZE <= size[0] <= MAX_SIZE and MIN_SIZE <= size[1] <= MAX_SIZE):
        raise ValueError("profile_size")
    unit = (pts - lo) / size
    x, y = unit[:, 0], unit[:, 1]
    area = 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))
    if abs(area) < 1e-4:
        raise ValueError("profile_section")
    if area < 0:
        unit = unit[::-1]
    return [(float(a), float(b)) for a, b in unit], float(size[0]), float(size[1])


def section(key, width, height, side=1, custom=None):
    """[(a, b)] the profile's section at its size, counter-clockwise; side −1: to the path's right (mirrored).
    custom (0.245): a project's own profile's section in its unit square (unit_section)."""
    pts = [(x * width, y * height) for x, y in (custom if custom is not None else PROFILES[key][4])]
    if side < 0:
        pts = [(-a, b) for a, b in pts][::-1]          # (mirrored, and turned back counter-clockwise)
    return pts


def foot(key, height, top):
    """The level of a profile's foot over the floor: its own (a skirting at 0, a dado rail at 0,90), or — a
    cornice — under the top (the ceiling, the walls' top) by its height. (0.245) A project's own: on the floor."""
    usual = 0.0 if is_custom(key) else PROFILES[key][3]
    return float(usual) if usual is not None else max(0.0, float(top) - float(height))


def clean(path, closed):
    """The path's points without repeats nor points on a straight line (no joint there)."""
    pts = [np.asarray(p, dtype=float)[:2] for p in path]
    out = []
    for p in pts:
        if not out or np.linalg.norm(p - out[-1]) > 1e-6:
            out.append(p)
    if closed and len(out) > 2 and np.linalg.norm(out[0] - out[-1]) < 1e-6:
        out.pop()
    changed = True
    while changed and len(out) > 2:
        changed = False
        n = len(out)
        for i in range(n) if closed else range(1, n - 1):
            a, p, b = out[i - 1], out[i], out[(i + 1) % n]
            d1, d2 = p - a, b - p
            if abs(d1[0] * d2[1] - d1[1] * d2[0]) <= STRAIGHT * np.linalg.norm(d1) * np.linalg.norm(d2) and \
                    float(d1 @ d2) > 0:
                out.pop(i)
                changed = True
                break
    return out


def runs(path, closed):
    """[(points, closed)] the path in runs that can be mitred: broken where it turns back on itself (sharper than
    ~154°) — a closed path broken there opens."""
    pts = clean(path, closed)
    if len(pts) < 2:
        return []
    n = len(pts)

    def sharp(i):
        a, p, b = pts[i - 1], pts[i], pts[(i + 1) % n]
        d1, d2 = (p - a) / np.linalg.norm(p - a), (b - p) / np.linalg.norm(b - p)
        return 1.0 + float(d1 @ d2) < SHARP

    breaks = [i for i in (range(n) if closed and n > 2 else range(1, n - 1)) if sharp(i)]
    if not breaks:
        return [(pts, closed and n > 2)]
    if closed:                                          # (from one break round to the same)
        k = breaks[0]
        pts = pts[k:] + pts[:k + 1]
        breaks = [(i - k) % n for i in breaks[1:]] + [n]
        out, start = [], 0
        for i in breaks:
            out.append((pts[start:i + 1], False))
            start = i
        return out
    out, start = [], 0
    for i in breaks + [n - 1]:
        out.append((pts[start:i + 1], False))
        start = i
    return out


def _offsets(pts, closed):
    """Per point of a run: (its point, the mitre vector — the offset of a = 1 to the left, (l1 + l2) / (1 + l1·l2)
    at a joint, the segment's left at an open end)."""
    n = len(pts)
    seg = [pts[(i + 1) % n] - pts[i] for i in range(n if closed else n - 1)]
    lefts = [np.array((-d[1], d[0])) / np.linalg.norm(d) for d in seg]
    out = []
    for i in range(n):
        if closed:
            l1, l2 = lefts[i - 1], lefts[i]
        else:
            l1 = lefts[i - 1] if i > 0 else lefts[0]
            l2 = lefts[i] if i < n - 1 else lefts[-1]
        out.append(((l1 + l2) / (1.0 + float(l1 @ l2))))
    return out


def sweep(path, closed, sec, z0=0.0):
    """(vertices (N, 3), triangles (M, 3)) of the section `sec` [(a, b)] swept along the plan path [(x, y)…] at the
    level z0 — its corners mitred, its open ends capped; every face turned out (counter-clockwise seen from
    outside)."""
    from shapely.geometry import Polygon
    import shapely
    sec = np.asarray(sec, dtype=float)
    k = len(sec)
    caps = []                                           # (the section's triangles, by its points' indices)
    for g in shapely.constrained_delaunay_triangles(Polygon(sec)).geoms:
        tri = [int(np.argmin(np.sum((sec - c) ** 2, axis=1))) for c in list(g.exterior.coords)[:3]]
        a, b, c = sec[tri[0]], sec[tri[1]], sec[tri[2]]
        if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) < 0:
            tri = tri[::-1]
        caps.append(tri)
    verts, tris, count = [], [], 0
    for pts, ring in runs(path, closed):
        n = len(pts)
        miters = _offsets(pts, ring)
        block = np.zeros((n, k, 3))
        for i, (p, m) in enumerate(zip(pts, miters)):
            block[i, :, 0] = p[0] + m[0] * sec[:, 0]
            block[i, :, 1] = p[1] + m[1] * sec[:, 0]
            block[i, :, 2] = z0 + sec[:, 1]
        verts.append(block.reshape(-1, 3))
        idx = lambda i, j: count + (i % n) * k + (j % k)        # noqa: E731
        for i in range(n if ring else n - 1):
            for j in range(k):
                tris.append((idx(i, j), idx(i + 1, j + 1), idx(i + 1, j)))
                tris.append((idx(i, j), idx(i, j + 1), idx(i + 1, j + 1)))
        if not ring:                                    # (the end cap facing on, the start's back)
            tris += [tuple(idx(n - 1, j) for j in c) for c in caps]
            tris += [tuple(idx(0, j) for j in c[::-1]) for c in caps]
        count += n * k
    if not verts:
        return np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64)
    return np.concatenate(verts), np.array(tris, dtype=np.int64)


def pieces(path, closed, width, side=1):
    """[(length, angle at its start, angle at its end)] the straight pieces a joiner cuts: each one's long point —
    its back (along the path, against the wall) or its front (`width` out, longer round an outside corner) —, the
    mitre at each end in degrees (0: a square cut; + its front shorter there — an inside corner —, − longer)."""
    out = []
    for pts, ring in runs(path, closed):
        n = len(pts)

        def half_turn(j):                               # (half the turn at a point, + to the left)
            if not ring and j in (0, n - 1):
                return 0.0
            p, q = pts[j - 1], pts[(j + 1) % n]
            d1 = (pts[j] - p) / np.linalg.norm(pts[j] - p)
            d2 = (q - pts[j]) / np.linalg.norm(q - pts[j])
            return math.atan2(d1[0] * d2[1] - d1[1] * d2[0], float(d1 @ d2)) / 2.0

        for i in range(n if ring else n - 1):
            back = float(np.linalg.norm(pts[(i + 1) % n] - pts[i]))
            t0, t1 = half_turn(i), half_turn((i + 1) % n)
            t0, t1 = side * t0, side * t1                   # (+: towards its side — the front on the inside)
            front = back - width * (math.tan(t0) + math.tan(t1))
            out.append((max(back, front), math.degrees(t0), math.degrees(t1)))
    return out


def length(path, closed):
    """The path's length (its runs')."""
    total = 0.0
    for pts, ring in runs(path, closed):
        n = len(pts)
        total += sum(float(np.linalg.norm(pts[(i + 1) % n] - pts[i])) for i in range(n if ring else n - 1))
    return total
