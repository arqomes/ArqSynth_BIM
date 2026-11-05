"""A roof's tiles (0.279), from the ArqSynth Modeler add-on's phase R3 — its «telhado realístico» (roof_tile_library,
roof_tiling): pure geometry. The add-on's tiles — Marselha, colonial (its cover), plain — each a profile across it
run along it, with its cover width, gauge, size and weight; and its ridge tile. Laid on each water of a roof as the
add-on lays them:

  rows      from the eave up, a gauge apart (along the slope);
  columns   along the eave, a cover width apart — every other row half a tile across where the tile is laid so;
  kept      the tiles whose exposed part's middle is in the water (the add-on's mask);
  cut       those over a ridge, hip, valley or gable (one of the water's edges but its eaves, where they overhang),
            along the edge's upright plane, closed where cut (the add-on cut them with a boolean);
  ridge     ridge tiles along the ridges and the hips, a ridge tile's gauge apart (as many as fill the edge).

Two things are not the add-on's: each tile lies as on a roof — its tail on its batten, its head on the tile below —
so that the rows overlap without meeting; and a tile's waves repeat at its cover width, so that two tiles side by
side overlap shape on shape.

(0.280) The add-on's corrugated sheet, laid as its tiles are (a sheet a row), and its sandwich panel, laid as panels
(its «modo painel»): one a column, from the eave to the top of the water, in lengths up to the longest made (6 m);
over a hip or a valley, cut as the tiles are (the add-on stopped them square at the column's middle).

Coordinates: the roof's own frame, its waters' planes z = a·x + b·y + c (the cover's top, as core/roof_carpentry). A
tile in its own frame: x across it (0 to its width), y up it (0 at its head, its length at its tail), z out of the
roof; placed by (origin, axes): a point p of it at origin + p @ axes."""

import math
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

from .roof_carpentry import _near, _Water

LIFT = 0.002                                       # m: over the cover's top (the add-on's), against flicker
BORDER_KINDS = ("ridge", "hip", "valley", "gable", "top")    # the edges tiles are cut along (not the eaves:
#                                                              they overhang the eave's edge)
CAP_KINDS = ("ridge", "hip")                       # the edges ridge tiles go along
_EPS = 1e-9


@dataclass(frozen=True)
class TileSpec:
    """A tile as laid (the add-on's TileSpec): its cover width (a column's step), its gauge (a row's, along the
    slope), its own width and length, thickness, weight (kg; a panel's: a length of it as long as the spec's), whether
    every other row is half a tile across, and the shape across it. (0.280) mode "unit" (a grid of them) or "panel"
    (the add-on's sandwich panel: one a column, as long as the water, in lengths up to max_length); its material
    (a catalogue key) and what its pieces are called (noun)."""
    key: str
    name_pt: str
    name_en: str
    cover_width: float
    gauge: float
    width: float
    length: float
    thickness: float
    weight: float
    stagger: bool
    shape: str                       # "marselha" | "colonial" | "plana" | "ondulada" | "sanduiche" | "cumeeira"
    per_wave: int = 8                # the profile's points a wave
    mode: str = "unit"
    material: str = "telha"
    max_length: float = 0.0
    noun: str = "tiles"              # "tiles" | "sheets" | "panels"
    custom: tuple = None             # (0.281) a tile of the user's own: its mesh ((x, y, z)…), ((i, j, k)…), as laid

    def sections(self):
        """Across it: [(x, its underside's z, its top's z)], from 0 to its width, a wave every cover width (a
        corrugated sheet's: three; a ridge tile: one arch over its width) — the points a step apart from 0, so that
        a tile's over its neighbour's are the same. A sandwich panel: flat under, its ribs on top."""
        if self.shape == "plana":
            return [(0.0, 0.0, self.thickness), (self.width, 0.0, self.thickness)]
        waves = 3 if self.shape in ("ondulada", "sanduiche") else 1
        period = (self.width if self.shape == "cumeeira" else self.cover_width) / waves
        if self.shape == "sanduiche":                # (the add-on's trapezoid ribs, 3,8 cm high, three a panel)
            rib = ((0.0, 0.0), (0.45, 0.0), (0.55, 0.038), (0.75, 0.038), (0.85, 0.0))
            xs = sorted({round(k * period + f * period, 9) for k in range(int(self.width / period) + 1)
                         for f, _z in rib if k * period + f * period < self.width - 1e-9} | {round(self.width, 9)})
        else:
            step = period / self.per_wave
            xs = [k * step for k in range(int(self.width / step + 1e-9) + 1)]
            if self.width - xs[-1] > 1e-6:
                xs.append(self.width)

        def z(x):
            f = (x % period) / period
            if self.shape == "marselha":           # (the add-on's: a wave 3,2 cm deep)
                return 0.016 * (1.0 - math.cos(2.0 * math.pi * f))
            if self.shape == "colonial":           # (its cover: a half round 5,5 cm high)
                return 0.055 * math.sin(math.pi * f)
            if self.shape == "ondulada":           # (the add-on's: waves 1,8 cm deep)
                return 0.009 * (1.0 - math.cos(2.0 * math.pi * f))
            if self.shape == "sanduiche":
                return float(np.interp(f, (0.0, 0.45, 0.55, 0.75, 0.85, 1.0), (0.0, 0.0, 0.038, 0.038, 0.0, 0.0)))
            return 0.088 * math.sin(math.pi * f)   # (the ridge tile: the colonial's, higher — the add-on's × 1,6)
        if self.shape == "sanduiche":
            return [(x, 0.0, self.thickness + z(x)) for x in xs]
        return [(x, z(x), z(x) + self.thickness) for x in xs]

    @property
    def top(self):
        """How high it stands over what it lies on (its highest top)."""
        if self.custom is not None:
            return max(p[2] for p in self.custom[0])
        return max(top for _x, _b, top in self.sections())


# (the add-on's presets, with its measures)
TILES = {s.key: s for s in (
    TileSpec("marselha", "Telha marselha", "Marseille tile", 0.21, 0.34, 0.235, 0.41, 0.012, 2.8, False, "marselha"),
    TileSpec("colonial", "Telha colonial (capa)", "Colonial tile (cover)", 0.17, 0.33, 0.19, 0.45, 0.012, 2.2, False,
             "colonial"),
    TileSpec("plana", "Telha plana", "Plain tile", 0.20, 0.32, 0.22, 0.40, 0.014, 2.5, True, "plana"),
    # (0.280) a corrugated sheet (laid as tiles, a sheet a row) and a sandwich panel (laid as panels)
    TileSpec("ondulada", "Chapa ondulada", "Corrugated sheet", 0.85, 1.80, 0.92, 2.00, 0.006, 12.0, False,
             "ondulada", material="fibrocimento", noun="sheets"),
    TileSpec("sanduiche", "Painel sanduíche", "Sandwich panel", 1.00, 3.00, 1.06, 3.00, 0.040, 11.0, False,
             "sanduiche", mode="panel", material="aco", max_length=6.0, noun="panels"),
)}
CAP = TileSpec("cumeeira", "Telha de cumeeira", "Ridge tile", 0.22, 0.33, 0.22, 0.40, 0.014, 2.6, False, "cumeeira")
DEFAULT = "marselha"


@lru_cache(maxsize=None)
def tile_mesh(spec):
    """A tile's closed mesh in its own frame: (vertices (N, 3), triangles (T, 3)), each turned out of it — its
    section run from y 0 to its length (one of the user's own: its mesh)."""
    if spec.custom is not None:
        return np.asarray(spec.custom[0], dtype=float), np.asarray(spec.custom[1], dtype=np.int64)
    return _mesh(spec, spec.length)


def measure(verts):
    """(0.281) A tile of the user's own, as the add-on's «Registar telha» measures it: (its width, length, height in
    metres; the cover width and gauge it proposes — 90 % and 80 % of them; its warnings: "size" (not 2 cm to 3 m: is
    it in metres?))."""
    v = np.asarray(verts, dtype=float)
    width, length, height = (float(x) for x in v.max(axis=0) - v.min(axis=0))
    warnings = [] if 0.02 <= width <= 3.0 and 0.02 <= length <= 3.0 else ["size"]
    return width, length, height, max(width * 0.9, 0.02), max(length * 0.8, 0.02), warnings


def custom_spec(key, name, verts, tris, cover_width, gauge, weight, stagger):
    """(0.281) A TileSpec of a tile of the user's own, its mesh given as the add-on takes it — in metres, its corner
    at the origin, x its width, y the way the water runs (down the slope), z up — turned about z to this program's
    tile frame (y up the slope from its head): laid as the add-on lays it, not tilted on the one below."""
    v = np.asarray(verts, dtype=float)
    v = v - v.min(axis=0)
    width, length = float(v[:, 0].max()), float(v[:, 1].max())
    v = np.column_stack((width - v[:, 0], length - v[:, 1], v[:, 2]))
    mesh = (tuple(tuple(round(float(c), 9) for c in p) for p in v), tuple(tuple(int(i) for i in t) for t in tris))
    return TileSpec(key, name, name, float(cover_width), float(gauge), width, length, float(v[:, 2].max()),
                    float(weight), bool(stagger), "custom", custom=mesh)


def _mesh(spec, length):
    """A piece of this section, `length` long (a tile: its own; a panel: as long as it is laid)."""
    prof = spec.sections()
    n = len(prof)
    verts = []
    for y in (0.0, length):
        verts += [(x, y, top) for x, _b, top in prof] + [(x, y, bottom) for x, bottom, _t in prof]

    def top(end, j):
        return end * 2 * n + j

    def bottom(end, j):
        return end * 2 * n + n + j

    tris = []
    for j in range(n - 1):
        tris += [(top(0, j), top(0, j + 1), top(1, j + 1)), (top(0, j), top(1, j + 1), top(1, j)),
                 (bottom(0, j), bottom(1, j + 1), bottom(0, j + 1)), (bottom(0, j), bottom(1, j), bottom(1, j + 1)),
                 (top(0, j), bottom(0, j + 1), top(0, j + 1)), (top(0, j), bottom(0, j), bottom(0, j + 1)),
                 (top(1, j), top(1, j + 1), bottom(1, j + 1)), (top(1, j), bottom(1, j + 1), bottom(1, j))]
    last = n - 1
    tris += [(bottom(0, 0), top(0, 0), top(1, 0)), (bottom(0, 0), top(1, 0), bottom(1, 0)),
             (top(0, last), bottom(0, last), bottom(1, last)), (top(0, last), bottom(1, last), top(1, last))]
    return np.asarray(verts, dtype=float), np.asarray(tris, dtype=np.int64)


# ---------------------------------------------------------------- a closed mesh cut by a plane

def clip(verts, tris, normal, point):
    """A closed mesh cut by a plane — what is on its normal's side kept, closed where cut: (vertices, triangles)."""
    import shapely
    from shapely.geometry import LineString
    normal = np.asarray(normal, dtype=float)
    point = np.asarray(point, dtype=float)
    d = (np.asarray(verts, dtype=float) - point) @ normal
    if (d >= -_EPS).all():
        return verts, tris
    if (d < _EPS).all():
        return np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64)
    pts = [tuple(v) for v in verts]
    cuts, out, segments = {}, [], []

    def cut(i, j):
        key = (min(i, j), max(i, j))
        if key not in cuts:
            s = d[i] / (d[i] - d[j])
            pts.append(tuple(np.asarray(pts[i]) + (np.asarray(pts[j]) - np.asarray(pts[i])) * s))
            cuts[key] = len(pts) - 1
        return cuts[key]

    for tri in tris:
        inside = [d[k] >= -_EPS for k in tri]
        if all(inside):
            out.append(tuple(tri))
            continue
        if not any(inside):
            continue
        poly, made = [], []
        for k in range(3):
            a, b = tri[k], tri[(k + 1) % 3]
            if inside[k]:
                poly.append(a)
            if inside[k] != inside[(k + 1) % 3]:
                c = cut(a, b)
                poly.append(c)
                made.append(c)
        out += [(poly[0], poly[k], poly[k + 1]) for k in range(1, len(poly) - 1)]
        if len(made) == 2:
            segments.append(made)
    # the cut closed: its outline in the plane, triangulated
    u = np.cross(normal, (0.0, 0.0, 1.0) if abs(normal[2]) < 0.9 else (1.0, 0.0, 0.0))
    u /= np.linalg.norm(u)
    v = np.cross(normal, u)
    flat = {}
    for seg in segments:
        for k in seg:
            q = np.asarray(pts[k]) - point
            flat[k] = (round(float(q @ u), 9), round(float(q @ v), 9))
    lines = [LineString([flat[a], flat[b]]) for a, b in segments if flat[a] != flat[b]]
    back = {xy: k for k, xy in flat.items()}

    def index(x, y):
        key = (round(x, 9), round(y, 9))
        if key not in back:
            pts.append(tuple(point + u * x + v * y))
            back[key] = len(pts) - 1
        return back[key]

    for polygon in shapely.get_parts(shapely.polygonize(lines)):
        for tri in shapely.get_parts(shapely.constrained_delaunay_triangles(polygon)):
            corners = list(tri.exterior.coords)[:3]
            (x0, y0), (x1, y1), (x2, y2) = corners
            if (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0) > 0:     # (turned towards what was cut away)
                corners = [corners[0], corners[2], corners[1]]
            out.append(tuple(index(x, y) for x, y in corners))
    used = sorted({k for tri in out for k in tri})
    index = {k: i for i, k in enumerate(used)}
    return (np.asarray([pts[k] for k in used], dtype=float),
            np.asarray([[index[k] for k in tri] for tri in out], dtype=np.int64).reshape(-1, 3))


# ---------------------------------------------------------------- laid

@dataclass
class Tiling:
    """A roof's tiles: the whole ones [(origin, axes)] (each its tile's mesh placed so), the cut ones as one mesh
    (vertices, triangles) and how many, the ridge tiles [(origin, axes)] (CAP's mesh), the waters' area (m², along
    their slope). (0.280) Panels: each of its own length, all in the one mesh — `panels` those not cut; `mass` the
    tiles' or panels' weight (kg)."""
    spec: TileSpec
    whole: list = field(default_factory=list)
    cut: tuple = (np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64))
    cut_count: int = 0
    caps: list = field(default_factory=list)
    area: float = 0.0
    panels: int = 0
    mass: float = 0.0

    @property
    def tiles(self):
        return len(self.whole) + self.cut_count + self.panels

    @property
    def weight(self):
        return self.mass + len(self.caps) * CAP.weight


def _inside(water, u, r):
    """(u, r) in the water's polygon (not in a hole of it)."""
    def ray(ring):
        inside = False
        for i in range(len(ring)):
            (u0, r0), (u1, r1) = ring[i], ring[(i + 1) % len(ring)]
            if (r0 > r) != (r1 > r) and u0 + (r - r0) / (r1 - r0) * (u1 - u0) > u:
                inside = not inside
        return inside
    return ray(water.ring) and not any(ray(h) for h in water.holes)


def _touches(water, u0, r0, u1, r1):
    """(0.280) A tile's exposed part (u0..u1 × r0..r1) reaching into the water at all — its middle, a corner of it in
    the water or a corner of the water in it (the add-on kept only those whose middle is: with a sheet 1,80 m long a
    triangle was left bare by each hip; now the tile is kept and cut along it)."""
    if _inside(water, (u0 + u1) / 2, (r0 + r1) / 2):
        return True
    if any(_inside(water, u, r) for u in (u0 + 1e-6, u1 - 1e-6) for r in (r0 + 1e-6, r1 - 1e-6)):
        return True
    return any(u0 < u < u1 and r0 < r < r1 for u, r in water.ring)


def _plan(water, u, r):
    return (u * water.e[0] + r * water.g[0], u * water.e[1] + r * water.g[1])


def _borders(water, polygon, edges):
    """The upright planes the water's tiles are cut along: [(normal, point, a, b)] (plan a → b; normal into the
    water)."""
    inner = polygon.representative_point()
    out = []
    for kind, a, b in edges:
        if kind not in BORDER_KINDS or math.dist(a[:2], b[:2]) < 1e-6:
            continue
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if not (_near(water, a[:2]) and _near(water, b[:2]) and _near(water, mid)):
            continue
        n = np.array((-(b[1] - a[1]), b[0] - a[0], 0.0))
        n /= np.linalg.norm(n)
        if n[0] * (inner.x - a[0]) + n[1] * (inner.y - a[1]) < 0:
            n = -n
        out.append((n, np.array((a[0], a[1], 0.0)), a, b))
    return out


def _frame(water, u, r, spec, tilt=True):
    """(origin, axes) of a tile whose head's corner at the u's end is over plan (u, r): x along −e (so that x, y, z
    turn as the roof's), y up the slope, its head raised on the tile below — by its thickness over the rows' overlap,
    so that tile lies on tile (a panel, not tilt: lying on the slope)."""
    x = np.array((-water.e[0], -water.e[1], 0.0))
    a, b, _c = water.coeff
    up = np.array((water.g[0], water.g[1], a * water.g[0] + b * water.g[1]))
    up /= np.linalg.norm(up)
    n = np.asarray(water.n, dtype=float)
    head = spec.thickness * spec.length / spec.gauge if tilt and spec.custom is None else 0.0
    y = spec.length * up - head * n
    y /= np.linalg.norm(y)
    z = np.cross(x, y)
    origin = np.asarray(water.at(u, r, 0.0), dtype=float) + n * (head + LIFT)
    return origin, np.vstack((x, y, z))


def lay(waters, edges, spec, stagger=None):
    """A roof's tiles: its waters [((a, b, c), shapely Polygon)] (the cover's top), its edges [(kind, (x, y, z),
    (x, y, z))] on that top (core/roof_blocks.edges). stagger: every other row half a tile across (None: as the tile
    is laid). (0.280) A panel: one a column, from the eave to the top of the water, in lengths of up to its
    max_length — cut as the tiles are. Tiling."""
    stagger = spec.stagger if stagger is None else stagger
    out = Tiling(spec)
    cut_v, cut_t = [], []

    def piece(mesh, origin, axes, corners, planes, whole_ok):
        """A piece placed: whole (a tile's place kept) or, crossing an edge, cut and added to the one mesh."""
        crossing = [(n, p) for n, p, a, b in planes
                    if any((cx - p[0]) * n[0] + (cy - p[1]) * n[1] < -1e-6 for cx, cy in corners)
                    and _reaches(corners, a, b)]
        if not crossing and whole_ok:
            out.whole.append((origin, axes))
            return True
        v, tris = mesh[0] @ axes + origin, mesh[1]
        for n, p in crossing:
            v, tris = clip(v, tris, n, p)
            if not len(tris):
                return False
        cut_t.append(tris + sum(len(x) for x in cut_v))
        cut_v.append(v)
        if crossing:
            out.cut_count += 1
        else:
            out.panels += 1
        return True

    waters = [(coeff, polygon, _Water(coeff, polygon)) for coeff, polygon in waters]
    for coeff, polygon, w in waters:
        if w.flat:
            continue
        out.area += polygon.area * w.k
        planes = _borders(w, polygon, edges)
        if spec.mode == "panel":
            u = w.u0
            while u < w.u1 - 1e-9:
                mid = min(u + spec.cover_width / 2, (u + w.u1) / 2)
                found = [s for s in w.spans(0, mid)]
                for lo, hi in found:          # (as far as the column's sides reach: the hip's side cut by it)
                    for side in (u + 1e-6, min(u + spec.cover_width, w.u1) - 1e-6):
                        for a, b in w.spans(0, side):
                            if a < hi and b > lo:
                                lo, hi = min(lo, a), max(hi, b)
                    run = (hi - lo) * w.k
                    if run < 0.05:
                        continue
                    count = max(1, math.ceil(run / spec.max_length - 1e-9))
                    for k in range(count):
                        r = lo + (hi - lo) * k / count
                        length = run / count
                        origin, axes = _frame(w, u + spec.width, r, spec, tilt=False)
                        corners = [_plan(w, cu, cr) for cu, cr in ((u, r), (u + spec.width, r),
                                                                  (u + spec.width, r + (hi - lo) / count),
                                                                  (u, r + (hi - lo) / count))]
                        if piece(_mesh(spec, length), origin, axes, corners, planes, False):
                            out.mass += spec.weight * length / spec.length
                u += spec.cover_width
            continue
        mesh = tile_mesh(spec)
        step_r = spec.gauge / w.k
        span_r = spec.length / w.k
        row, r = 0, w.r0
        while r < w.r1 - 1e-9:
            u = w.u0 - (spec.cover_width / 2 if stagger and row % 2 else 0.0)
            while u < w.u1 - 1e-9:
                if _touches(w, u, r, u + spec.cover_width, r + step_r):
                    origin, axes = _frame(w, u + spec.width, r, spec)
                    corners = [_plan(w, cu, cr) for cu, cr in ((u, r), (u + spec.width, r),
                                                              (u + spec.width, r + span_r), (u, r + span_r))]
                    if piece(mesh, origin, axes, corners, planes, True):
                        out.mass += spec.weight
                u += spec.cover_width
            r += step_r
            row += 1
    if cut_v:
        out.cut = (np.concatenate(cut_v), np.concatenate(cut_t))
    out.caps = _caps(waters, edges, spec)
    return out


def _reaches(corners, a, b):
    """A tile's plan corners within reach of the edge a → b (its plane cuts only the tiles by it)."""
    d = np.array((b[0] - a[0], b[1] - a[1]))
    length = float(np.linalg.norm(d))
    d /= length
    ts = [(cx - a[0]) * d[0] + (cy - a[1]) * d[1] for cx, cy in corners]
    return max(ts) > -1e-6 and min(ts) < length + 1e-6


def _caps(waters, edges, spec):
    """The ridge tiles along the ridges and hips: [(origin, axes)] of CAP's mesh — centred on the edge, resting on
    the tiles each side."""
    out = []
    for kind, a, b in edges:
        if kind not in CAP_KINDS:
            continue
        a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        length = float(np.linalg.norm(b - a))
        if length < 1e-6:
            continue
        d = (b - a) / length
        side = np.array((-d[1], d[0], 0.0))
        if np.linalg.norm(side) < 1e-9:
            continue
        side /= np.linalg.norm(side)
        up = np.cross(d, side)
        mid = (a + b) / 2
        drops = []
        for _coeff, _polygon, w in waters:
            for s in (1.0, -1.0):
                x, y = mid[0] + side[0] * s * CAP.width / 2, mid[1] + side[1] * s * CAP.width / 2
                if _inside(w, *w.to_ur(x, y)):
                    ca, cb, cc = w.coeff
                    drops.append(mid[2] - (ca * x + cb * y + cc))
        lower = (np.mean(drops) if drops else 0.0) - spec.top - LIFT
        # (from end to end of the edge, none past them: the first and the last flush with its ends)
        n = 1 if length <= CAP.length else math.ceil((length - CAP.length) / CAP.gauge - 1e-9) + 1
        for i in range(n):
            along = length / 2 if n == 1 else CAP.length / 2 + i * (length - CAP.length) / (n - 1)
            centre = a + d * along                             # (x along −side, so that x, y, z turn as the roof's)
            origin = centre + side * CAP.width / 2 - d * CAP.length / 2 - np.array((0.0, 0.0, lower))
            out.append((origin, np.vstack((-side, d, up))))
    return out


def merged(tiling):
    """Every tile of a tiling as one mesh (vertices, triangles): the whole ones, the cut ones, the ridge tiles."""
    parts_v, parts_t, count = [], [], 0
    for mesh, placements in ((tile_mesh(tiling.spec), tiling.whole), (tile_mesh(CAP), tiling.caps)):
        v, t = mesh
        for origin, axes in placements:
            parts_v.append(v @ axes + origin)
            parts_t.append(t + count)
            count += len(v)
    if len(tiling.cut[1]):
        parts_v.append(tiling.cut[0])
        parts_t.append(tiling.cut[1] + count)
    if not parts_v:
        return np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64)
    return np.concatenate(parts_v), np.concatenate(parts_t)
