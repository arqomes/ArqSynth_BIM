"""Platforms, cut and fill (0.157, Phase 7, step 3): a platform is a flat area at a height on the terrain (a
building's pad, a yard, a road's widening) with its slopes round it — cut where the ground is higher (1:1 by
default), fill where it is lower (2:3: one up for one and a half across) — down or up to where they meet the
ground. The proposed surface is the survey's with the platforms on it:

    proposed(x, y) = min(max(ground(x, y), z − fill · d), z + cut · d)

d being the distance from (x, y) to the platform (0 on it): on it, its height; far away, the ground. Several
platforms one after another. Made as points (the survey's at their new heights, each platform's outline and rings
round it every STEP metres) triangulated again.

The volumes of cut and fill: between the two surfaces, cell by cell on a grid fine enough (VOLUME_CELLS across).
Pure numpy and shapely."""

import math
import re
from dataclasses import dataclass

import numpy as np

from . import terrain as geo

CUT_SLOPE = 1.0              # a cut's batter, height over width (1:1)
FILL_SLOPE = 2.0 / 3.0       # a fill's (2:3)
STEP = 0.5                   # m between the points along a platform's outline and its slopes' rings
VOLUME_CELLS = 600           # cells across the longer side when the volumes are worked out
SLOPES = {"1:1": 1.0, "2:3": 2.0 / 3.0, "1:2": 0.5, "1:3": 1.0 / 3.0, "vertical": 1000.0}   # (the choices, V:H)


@dataclass
class Platform:
    outline: list                       # its corners (x, y), program coordinates
    z: float                            # its height (m) — a ramp's at the start of its axis
    cut: float = CUT_SLOPE              # its slopes' batters (height over width)
    fill: float = FILL_SLOPE
    name: str = ""
    # (0.205) a ramp between two platforms: its axis [(x, y) start, (x, y) end] and its height at the end — its height
    # going evenly from z to z_end along the axis (a plane); None: flat
    axis: list = None
    z_end: float = None

    def to_dict(self):
        data = {"outline": [[round(float(x), 4), round(float(y), 4)] for x, y in self.outline],
                "z": round(float(self.z), 4), "cut": round(float(self.cut), 4), "fill": round(float(self.fill), 4),
                "name": self.name}
        if self.is_ramp():
            data["axis"] = [[round(float(x), 4), round(float(y), 4)] for x, y in self.axis]
            data["z_end"] = round(float(self.z_end), 4)
        return data

    @classmethod
    def from_dict(cls, data):
        axis = data.get("axis")
        return cls([(float(x), float(y)) for x, y in data["outline"]], float(data["z"]),
                   float(data.get("cut", CUT_SLOPE)), float(data.get("fill", FILL_SLOPE)), str(data.get("name", "")),
                   [(float(x), float(y)) for x, y in axis] if axis and len(axis) == 2 else None,
                   float(data["z_end"]) if axis and data.get("z_end") is not None else None)

    def polygon(self):
        from shapely.geometry import Polygon
        poly = Polygon(self.outline)
        return poly if poly.is_valid else poly.buffer(0)

    def is_ramp(self):
        return self.axis is not None and self.z_end is not None and \
            float(np.hypot(*(np.subtract(self.axis[1], self.axis[0])))) > 1e-9

    def heights(self, xy):
        """Its height at the plan points (N, 2) on it (a ramp's along its axis, held at its ends)."""
        xy = np.asarray(xy, dtype=float).reshape(-1, 2)
        if not self.is_ramp():
            return np.full(len(xy), float(self.z))
        a, b = np.asarray(self.axis[0], dtype=float), np.asarray(self.axis[1], dtype=float)
        k = np.clip((xy - a) @ (b - a) / float((b - a) @ (b - a)), 0.0, 1.0)
        return float(self.z) + (float(self.z_end) - float(self.z)) * k

    def low_high(self):
        """Its lowest and highest heights."""
        ends = (float(self.z), float(self.z_end)) if self.is_ramp() else (float(self.z),)
        return min(ends), max(ends)

    def slope(self):
        """A ramp's slope (rise over run, along its axis); 0 for a flat one."""
        if not self.is_ramp():
            return 0.0
        run = float(np.hypot(*(np.subtract(self.axis[1], self.axis[0]))))
        return abs(float(self.z_end) - float(self.z)) / run


def ramp_outline(start, end, width):
    """(0.205) A ramp's outline: the rectangle along start → end (x, y), `width` across — its four corners."""
    a, b = np.asarray(start, dtype=float)[:2], np.asarray(end, dtype=float)[:2]
    d = b - a
    length = float(np.hypot(*d))
    if length < 1e-9:
        return None
    side = np.array((-d[1], d[0])) / length * (float(width) / 2)
    return [tuple(map(float, p)) for p in (a - side, b - side, b + side, a + side)]


class _Locator:
    """Which triangle of a surface a plan point is on — triangles bucketed by grid cells."""

    def __init__(self, verts, tris):
        self.verts, self.tris = np.asarray(verts, dtype=float), np.asarray(tris, dtype=np.int64)
        p = self.verts[self.tris]
        self.lo, self.hi = p[:, :, :2].min(axis=1), p[:, :, :2].max(axis=1)
        span = self.hi.max(axis=0) - self.lo.min(axis=0) if len(p) else np.ones(2)
        self.origin = self.lo.min(axis=0) if len(p) else np.zeros(2)
        self.size = max(float(max(span)) / max(math.sqrt(len(p)), 1.0), 1e-3)
        self.cells = {}
        a = np.floor((self.lo - self.origin) / self.size).astype(np.int64)
        b = np.floor((self.hi - self.origin) / self.size).astype(np.int64)
        for k in range(len(p)):
            for i in range(a[k, 0], b[k, 0] + 1):
                for j in range(a[k, 1], b[k, 1] + 1):
                    self.cells.setdefault((i, j), []).append(k)

    def heights(self, xy):
        """The surface's height at each plan point (N, 2): NaN outside it."""
        xy = np.asarray(xy, dtype=float).reshape(-1, 2)
        out = np.full(len(xy), np.nan)
        keys = np.floor((xy - self.origin) / self.size).astype(np.int64)
        for n, (x, y) in enumerate(xy):
            near = self.cells.get((int(keys[n, 0]), int(keys[n, 1])))
            if not near:
                continue
            p = self.verts[self.tris[near]]
            a, b, c = p[:, 0], p[:, 1], p[:, 2]
            det = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
            ok = np.abs(det) > 1e-15
            det = np.where(ok, det, 1.0)
            l1 = ((b[:, 1] - c[:, 1]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (y - c[:, 1])) / det
            l2 = ((c[:, 1] - a[:, 1]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (y - c[:, 1])) / det
            l3 = 1.0 - l1 - l2
            inside = np.flatnonzero(ok & (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9))
            if len(inside):
                k = inside[0]
                out[n] = l1[k] * a[k, 2] + l2[k] * b[k, 2] + l3[k] * c[k, 2]
        return out


def _ring_points(poly, d):
    """Points every STEP metres along the outline of the polygon grown by d (mitred corners)."""
    grown = poly.buffer(d, join_style=2, mitre_limit=10.0) if d > 0 else poly
    out = []
    for geom in getattr(grown, "geoms", [grown]):
        if geom.is_empty:
            continue
        ring = geom.exterior
        n = max(int(math.ceil(ring.length / STEP)), 3)
        out += [ring.interpolate(k * ring.length / n).coords[0] for k in range(n)]
        out += list(ring.coords)[:-1]                       # (its corners exactly)
    return out


def _reach(platform, xy):
    """(distance to the platform, its height at its nearest point) of each plan point (N, 2) — a ramp's height
    there along it (0.205)."""
    from shapely import distance, get_coordinates, points, shortest_line
    poly = platform.polygon()
    pts = points(np.asarray(xy, dtype=float).reshape(-1, 2))
    d = np.asarray(distance(pts, poly), dtype=float)
    if not platform.is_ramp():
        return d, np.full(len(d), float(platform.z))
    near = get_coordinates(shortest_line(pts, poly)).reshape(-1, 2, 2)[:, 1]
    return d, platform.heights(near)


def _apply(platform, xy, h):
    """Heights h at the plan points xy with this platform on the ground (NaN stays NaN)."""
    d, z = _reach(platform, xy)
    return np.minimum(np.maximum(h, z - platform.fill * d), z + platform.cut * d)


def proposed(survey, platforms):
    """The proposed surface's points (N, 3): the survey's at their heights with the platforms, each platform's
    outline at its height and rings round it where its slopes are — or the survey's when there are none."""
    survey = geo.unique_points(survey)
    if not platforms:
        return survey
    made = geo.tin(survey)
    if made is None:
        return survey
    locator = _Locator(*made)
    low, high = float(survey[:, 2].min()), float(survey[:, 2].max())
    xy = [tuple(p) for p in survey[:, :2]]
    for plat in platforms:
        poly = plat.polygon()
        if poly.is_empty:
            continue
        bottom, top = plat.low_high()
        reach = (max(high - bottom, top - low, 0.0) / max(min(plat.cut, plat.fill), 1e-3)) + STEP
        d = 0.0
        while d <= reach + 1e-9:
            xy += _ring_points(poly, d)
            d += STEP
    from shapely import contains_xy
    xy = np.array(xy, dtype=float)
    h = locator.heights(xy)
    on_platform = np.zeros(len(xy), dtype=bool)
    for plat in platforms:
        on_platform |= contains_xy(plat.polygon().buffer(1e-6), xy[:, 0], xy[:, 1])
    keep = ~np.isnan(h) | on_platform                       # (a platform beyond the survey: its own corners)
    xy, h = xy[keep], h[keep]
    for plat in platforms:
        h = np.where(np.isnan(h), plat.heights(xy), h)
        h = _apply(plat, xy, h)
    return geo.unique_points(np.column_stack((xy, h)))


TICK_EVERY = 1.0             # m between a slope's batter ticks along its platform (0.203)
SHORTEST_TICK = 0.05         # m: a slope narrower than this (a vertical one) gets none


def batters(survey, platform, every=TICK_EVERY):
    """(0.203) A platform's slopes as a plan draws them: where they meet the ground — the top of a cut (its crest),
    the foot of a fill (its toe) — and the batter ticks across them from their top, one long, one short, every
    `every` m along the platform's sides. Returns (the lines (K, 2, 3), the ticks (M, 2, 3)), at the ground's / the
    slope's heights; empty where the platform sits on the ground. The ground: the survey's, without the platforms.

    The meeting lines are the level 0 of ground − z − cut·d (the crest: the ground over the cut's slope) and of
    ground − z + fill·d (the toe), d the distance to the platform — worked out on rings round it."""
    from shapely import contains_xy, distance, points
    empty = (np.zeros((0, 2, 3)), np.zeros((0, 2, 3)))
    survey = geo.unique_points(survey)
    made = geo.tin(survey)
    poly = platform.polygon()
    if made is None or poly.is_empty:
        return empty
    locator = _Locator(*made)
    low, high = float(survey[:, 2].min()), float(survey[:, 2].max())
    bottom, top = platform.low_high()
    reach = (max(high - bottom, top - low, 0.0) / max(min(platform.cut, platform.fill), 1e-3)) + STEP
    xy, d = [], 0.0
    while d <= reach + 1e-9:
        xy += _ring_points(poly, d)
        d += STEP / 2
    xy = np.array(xy, dtype=float)
    ground = locator.heights(xy)
    keep = ~np.isnan(ground)
    xy, ground = xy[keep], ground[keep]
    dist, z = _reach(platform, xy)                  # (a ramp: its height at the nearest point, 0.205)
    lines = []
    for value in (ground - z - platform.cut * dist, ground - z + platform.fill * dist):
        made = geo.tin(np.column_stack((xy, value)))
        if made is None:
            continue
        verts, tris = made
        middle = verts[tris][:, :, :2].mean(axis=1)
        tris = tris[~contains_xy(poly, middle[:, 0], middle[:, 1])]          # (not on the platform)
        for level, segs in geo.contours(verts, tris, interval=1e6):
            if abs(level) < 1e-9:
                lines.append(segs)
    if lines:
        segs = np.concatenate(lines)
        segs[:, :, 2] = locator.heights(segs[:, :, :2].reshape(-1, 2)).reshape(-1, 2)
        away = np.asarray(distance(points(segs[:, :, :2].reshape(-1, 2)), poly), dtype=float).reshape(-1, 2)
        segs = segs[~np.isnan(segs[:, :, 2]).any(axis=1) & (away.max(axis=1) >= SHORTEST_TICK / 2)]  # (not on the
        #                                                                       edge: where it sits on the ground)
    else:
        segs = np.zeros((0, 2, 3))
    return segs, _ticks(platform, locator, reach, every)


def _ticks(platform, locator, reach, every):
    """The batter ticks of a platform's slopes (see batters): along each side, square to it, from the slope's top
    — the crest of a cut, the platform's edge over a fill — to its foot, every other one half as long."""
    ring = list(platform.polygon().exterior.coords)[:-1]
    if len(ring) < 3:
        return np.zeros((0, 2, 3))
    from shapely.geometry import Polygon
    ccw = Polygon(ring).exterior.is_ccw
    out, count = [], 0
    for a, b in zip(ring, ring[1:] + ring[:1]):
        a, b = np.array(a, dtype=float), np.array(b, dtype=float)
        length = float(np.linalg.norm(b - a))
        if length < 1e-6:
            continue
        along = (b - a) / length
        out_way = np.array((along[1], -along[0])) if ccw else np.array((-along[1], along[0]))
        n = int(length // every)
        for k in range(n):
            p = a + along * ((k + 0.5) * length / n)
            z = float(platform.heights(p)[0])            # (a ramp's height there, 0.205)
            here = locator.heights(p[None, :])[0]
            if np.isnan(here) or abs(here - z) < 1e-3:
                continue
            cutting = here > z
            batter = platform.cut if cutting else platform.fill
            sign = 1.0 if cutting else -1.0

            def gap(d):                                  # (> 0 while the slope is still in the ground / over it)
                g = locator.heights((p + out_way * d)[None, :])[0]
                return np.nan if np.isnan(g) else sign * (g - (z + sign * batter * d))

            lo, hi, step = 0.0, None, STEP / 2
            d = step
            while d <= reach + 1e-9:
                v = gap(d)
                if np.isnan(v):
                    break
                if v <= 0.0:
                    hi = d
                    break
                lo, d = d, d + step
            if hi is None:
                continue
            for _ in range(12):
                mid = (lo + hi) / 2
                v = gap(mid)
                if np.isnan(v) or v <= 0.0:
                    hi = mid
                else:
                    lo = mid
            width = (lo + hi) / 2
            if width < SHORTEST_TICK:
                continue
            foot = p + out_way * width
            top, bottom = ((foot, z + batter * width), (p, z)) if cutting else ((p, z), (foot, z - batter * width))
            share = 1.0 if count % 2 == 0 else 0.5
            end = top[0] + (bottom[0] - top[0]) * share
            out.append(((top[0][0], top[0][1], top[1]), (end[0], end[1], top[1] + (bottom[1] - top[1]) * share)))
            count += 1
    return np.array(out, dtype=float).reshape(-1, 2, 3)


def volumes(existing, proposed_points, cells=VOLUME_CELLS):
    """(cut, fill) in m³ between the existing surface (its points) and the proposed one: where the proposed is
    lower, the earth taken away; higher, the earth brought."""
    from .drawing2d import depth_image
    a, b = geo.tin(existing), geo.tin(proposed_points)
    if a is None or b is None:
        return 0.0, 0.0
    both = np.vstack((a[0][:, :2], b[0][:, :2]))
    lo, hi = both.min(axis=0), both.max(axis=0)
    cell = max(float((hi - lo).max()) / cells, 1e-3)
    shape = (int((hi[1] - lo[1]) / cell) + 2, int((hi[0] - lo[0]) / cell) + 2)

    def raster(verts, tris):
        p = verts[tris]
        tri2d = (p[:, :, :2] - lo) / cell
        return depth_image(tri2d, p[:, :, 2], shape, -np.inf)

    ground, design = raster(*a), raster(*b)
    ok = np.isfinite(ground) & np.isfinite(design)
    diff = design[ok].astype(float) - ground[ok].astype(float)
    area = cell * cell
    return float(np.clip(-diff, 0.0, None).sum() * area), float(np.clip(diff, 0.0, None).sum() * area)


def parse_slope(text):
    """A batter typed as V:H ("1:1", "2:3", "1:1,5") — height over width — or None."""
    m = re.match(r"^\s*(\d+(?:[.,]\d+)?)\s*[:/]\s*(\d+(?:[.,]\d+)?)\s*$", text or "")
    if not m:
        return None
    v, h = float(m.group(1).replace(",", ".")), float(m.group(2).replace(",", "."))
    return v / h if h > 0 and v > 0 else None
