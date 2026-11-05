"""Organic roofs (0.390), the ArqSynth Modeler's «Cobertura orgânica»: a curved roof over any outline drawn in plan —
its form found from the outline itself, not drawn by hand:

- «cupula» (dome): a membrane pushed up by an even pressure, held at the outline (Poisson: ∇²φ = −1, φ = 0 at the
  edge), made fuller (φ^0.6) — round over a circle, a cushion over a square, a long dome over an oval;
- «abobada» (vault): across the main way (the angle) an arch over each chord of the outline, as high as the chord is
  wide (the widest the rise) — a barrel over a rectangle, a vault that narrows and lowers with the outline;
- «onda» (wave): the vault with its crest rising and falling along the main way.

Its systems, each a set of pieces: «casca» (a shell `thickness` thick), «gridshell» (bars on a square grid of `spacing`
at the angle, straight from node to node — facets, as glass needs), «envidracada» (the gridshell with a glass pane in
each cell, flat triangles), «pergola» (ribs one way only, bent with the surface). Around it, if asked, a ring beam
under the edge and supports (at the outline's corners or every so often along it).

Pure numpy and shapely, metres; the outline in plan (x, y), heights from the edge's level (z = 0 at the outline)."""

import math

import numpy as np

FORMS = ("cupula", "abobada", "onda")
SYSTEMS = ("casca", "gridshell", "envidracada", "pergola")
SUPPORTS = ("nenhum", "cantos", "espacados")
MAX_CELLS = 140                 # the height field's grid: at most this many cells a side
DOME_POWER = 0.6                # the membrane made fuller
WAVES = 2.0                     # «onda»: crests along the main way
CORNER_TURN = 35.0              # degrees: an outline's vertex turning more than this is a corner (supports)
MAX_BARS = 4000                 # pieces: more is refused (too heavy)


def _polygon(outline):
    from shapely.geometry import Polygon
    from shapely.geometry.polygon import orient
    poly = Polygon([(float(x), float(y)) for x, y in outline])
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.geom_type != "Polygon" or poly.area < 1.0:
        raise ValueError("organic_outline")
    return orient(poly, 1.0)


def _turn(points, degrees):
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    p = np.asarray(points, dtype=float).reshape(-1, 2)
    return np.column_stack((c * p[:, 0] - s * p[:, 1], s * p[:, 0] + c * p[:, 1]))


class Shape:
    """An organic roof's form over its outline: `height(points)` (m above the edge) anywhere in plan; its frame
    turned `angle` degrees (u along the main way, v across)."""

    def __init__(self, outline, rise, form="cupula", angle=0.0):
        from shapely import affinity
        self.poly = _polygon(outline)
        self.rise, self.form, self.angle = float(rise), form if form in FORMS else "cupula", float(angle)
        self.local = affinity.rotate(self.poly, -self.angle, origin=(0.0, 0.0))     # (in (u, v))
        u0, v0, u1, v1 = self.local.bounds
        ring = np.asarray(self.local.exterior.coords)
        self._a, self._b = ring[:-1], ring[1:]                                        # (its edges, for the chords)
        if self.form == "cupula":
            self.step = max((u1 - u0), (v1 - v0)) / MAX_CELLS
            self.step = max(self.step, math.sqrt(self.local.area) / 60.0, 0.02)
            nu = int(math.ceil((u1 - u0) / self.step)) + 3
            nv = int(math.ceil((v1 - v0) / self.step)) + 3
            self.origin = (u0 - self.step, v0 - self.step)                            # (cell (0, 0)'s centre)
            gu, gv = np.meshgrid(self.origin[0] + np.arange(nu) * self.step,
                                 self.origin[1] + np.arange(nv) * self.step, indexing="ij")
            import shapely
            self.field = self._cupula(shapely.contains_xy(self.local, gu, gv))
            if float(self.field.max()) <= 0.0:
                raise ValueError("organic_outline")
        else:                                       # (the vault: its widest chord across is its rise)
            import shapely
            gu, gv = np.meshgrid(np.linspace(u0, u1, 122)[1:-1], np.linspace(v0, v1, 62)[1:-1], indexing="ij")
            probe = np.column_stack((gu.ravel(), gv.ravel()))
            probe = probe[shapely.contains_xy(self.local, probe[:, 0], probe[:, 1])]
            lo, hi = self._chord(probe) if len(probe) else (np.zeros(0), np.zeros(0))
            widths = (hi - lo)[np.isfinite(hi - lo)]
            if not len(widths) or float(widths.max()) <= 1e-6:
                raise ValueError("organic_outline")
            self.half = float(widths.max()) / 2.0
            self.u0, self.length = u0, max(u1 - u0, 1e-9)

    def _crossings(self, p):
        """(N, E) the v where the line u = p.u crosses each edge of the outline (NaN where it does not)."""
        a, b = self._a, self._b
        du = b[:, 0] - a[:, 0]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (p[:, None, 0] - a[None, :, 0]) / du[None, :]
        ok = (np.abs(du)[None, :] > 1e-12) & (t >= -1e-12) & (t <= 1.0 + 1e-12)
        v = a[None, :, 1] + t * (b[None, :, 1] - a[None, :, 1])
        return np.where(ok, v, np.nan)

    def _chord(self, p):
        """(lo, hi) the chord across (along v) through each local point: the outline's crossings just below and
        just above it (±inf where there is none)."""
        v = self._crossings(p)
        y = p[:, 1:2]
        lo = np.max(np.where(np.isfinite(v) & (v <= y + 1e-9), v, -np.inf), axis=1)
        hi = np.min(np.where(np.isfinite(v) & (v >= y - 1e-9), v, np.inf), axis=1)
        return lo, hi

    def _vault(self, p):
        """The vault's height (0–1) at local points: the arch over the chord across through each."""
        lo, hi = self._chord(p)
        y = p[:, 1]
        ok = np.isfinite(lo) & np.isfinite(hi)
        z = np.where(ok, (y - np.where(ok, lo, 0.0)) * (np.where(ok, hi, 0.0) - y), 0.0) / (self.half * self.half)
        z = np.clip(z, 0.0, 1.0)
        if self.form == "onda":
            z = z * (0.6 + 0.4 * (0.5 + 0.5 * np.cos(2.0 * np.pi * WAVES * (p[:, 0] - self.u0) / self.length)))
        return z

    def _cupula(self, inside):
        """The membrane: red-black over-relaxation of ∇²φ = −1 (φ = 0 outside), made fuller."""
        phi = np.zeros(inside.shape)
        h2 = self.step * self.step
        ii, jj = np.indices(inside.shape)
        colours = [inside & ((ii + jj) % 2 == k) for k in (0, 1)]
        w = 2.0 / (1.0 + math.sin(math.pi / max(inside.shape)))       # (the best over-relaxation for the grid)
        for _ in range(3000):
            change = 0.0
            for mask in colours:
                around = np.zeros_like(phi)
                around[1:, :] += phi[:-1, :]
                around[:-1, :] += phi[1:, :]
                around[:, 1:] += phi[:, :-1]
                around[:, :-1] += phi[:, 1:]
                new = (around + h2) / 4.0
                delta = (new - phi)[mask]
                phi[mask] += w * delta
                change = max(change, float(np.abs(delta).max()) if delta.size else 0.0)
            if change < 1e-7 * max(float(phi.max()), 1e-12):
                break
        phi = np.where(inside, np.maximum(phi, 0.0), 0.0)
        top = float(phi.max())
        return (phi / top) ** DOME_POWER if top > 0.0 else phi

    def unit(self, points):
        """The form's height (0 at the edge, 1 at its top) at plan points (N, 2): the dome bilinear over its
        field, the vault exactly (its ends open arches)."""
        p = _turn(points, -self.angle)
        if self.form != "cupula":
            return self._vault(p)
        fu = (p[:, 0] - self.origin[0]) / self.step
        fv = (p[:, 1] - self.origin[1]) / self.step
        nu, nv = self.field.shape
        i0 = np.clip(np.floor(fu).astype(int), 0, nu - 2)
        j0 = np.clip(np.floor(fv).astype(int), 0, nv - 2)
        tu = np.clip(fu - i0, 0.0, 1.0)
        tv = np.clip(fv - j0, 0.0, 1.0)
        f = self.field
        z = (f[i0, j0] * (1 - tu) * (1 - tv) + f[i0 + 1, j0] * tu * (1 - tv) + f[i0, j0 + 1] * (1 - tu) * tv
             + f[i0 + 1, j0 + 1] * tu * tv)
        return np.clip(z, 0.0, 1.0)

    def height(self, points):
        return self.rise * self.unit(points)

    def lift(self, points, edge=None):
        """(N, 3) the plan points on the surface; those of `edge` (a bool mask) kept at 0 — the outline (the dome's:
        the vault's ends are arches, worked out exactly)."""
        p = np.asarray(points, dtype=float).reshape(-1, 2)
        z = self.height(p)
        if edge is not None and self.form == "cupula":
            z = np.where(edge, 0.0, z)
        return np.column_stack((p, z))

    # ------------------------------------------------------------ pieces

    def surface(self, spacing):
        """(vertices (N, 3), triangles (M, 3), edge (N,) bool) the surface as a fine mesh: the outline every
        spacing/2, a grid inside at the same step (turned with the form), Delaunay, those triangles inside kept."""
        import shapely
        from shapely.geometry import MultiPoint
        e = max(min(spacing / 2.0, self.rise / 3.0 if self.rise > 0 else spacing, 0.6), 0.1)
        ring = np.asarray(self.poly.exterior.segmentize(e).coords)[:-1]
        u0, v0, u1, v1 = self.local.bounds
        gu, gv = np.meshgrid(np.arange(u0 + e / 2, u1, e), np.arange(v0 + e / 2, v1, e), indexing="ij")
        inner = _turn(np.column_stack((gu.ravel(), gv.ravel())), self.angle)
        keep = shapely.contains_xy(self.poly.buffer(-e * 0.35), inner[:, 0], inner[:, 1]) if len(inner) else []
        inner = inner[keep] if len(inner) else inner.reshape(0, 2)
        pts = np.vstack((ring, inner))
        edge = np.zeros(len(pts), dtype=bool)
        edge[:len(ring)] = True
        index = {(round(x, 7), round(y, 7)): k for k, (x, y) in enumerate(pts)}
        tris = []
        for g in shapely.delaunay_triangles(MultiPoint([tuple(q) for q in pts])).geoms:
            c = np.asarray(g.exterior.coords)[:3]
            centre = c.mean(axis=0)
            if not shapely.contains_xy(self.poly, centre[0], centre[1]):
                continue
            ids = [index.get((round(x, 7), round(y, 7))) for x, y in c]
            if None in ids:
                continue
            a, b, d = c
            if (b[0] - a[0]) * (d[1] - a[1]) - (b[1] - a[1]) * (d[0] - a[0]) < 0:
                ids = ids[::-1]
            tris.append(ids)
        return self.lift(pts, edge), np.array(tris, dtype=np.int64).reshape(-1, 3), edge

    def shell(self, spacing, thickness):
        """(vertices, triangles) of the shell: the surface its underside, its top `thickness` above (upright),
        its edge closed — a solid."""
        verts, tris, _edge = self.surface(spacing)
        n = len(verts)
        top = verts + np.array((0.0, 0.0, thickness))
        out_v = np.vstack((top, verts))
        out_t = [tris, tris[:, ::-1] + n]
        edges = {}
        for a, b, c in tris:
            for e in ((a, b), (b, c), (c, a)):
                key = (min(e), max(e))
                edges[key] = None if key in edges else e
        sides = [e for e in edges.values() if e is not None]       # (used once: the outline, in the top's turn)
        if sides:
            s = np.array(sides)
            a, b = s[:, 0], s[:, 1]
            out_t += [np.column_stack((b, a, a + n)), np.column_stack((b, a + n, b + n))]
        return out_v, np.concatenate(out_t).astype(np.int64)

    def _lines(self, spacing, across):
        """[(fixed, [(lo, hi)…])] the grid's lines in (u, v): `across` False — lines along u at v = fixed — or True —
        along v at u = fixed —, each cut by the outline into pieces (lo, hi)."""
        from shapely.geometry import LineString
        u0, v0, u1, v1 = self.local.bounds
        a0, a1, b0, b1 = (u0, u1, v0, v1) if across else (v0, v1, u0, u1)
        n = int(math.floor((a1 - a0) / spacing))
        start = a0 + ((a1 - a0) - n * spacing) / 2.0
        out = []
        for k in range(n + 1):
            c = start + k * spacing
            if c <= a0 + 1e-6 or c >= a1 - 1e-6:
                continue
            line = LineString([(c, b0 - 1), (c, b1 + 1)] if across else [(b0 - 1, c), (b1 + 1, c)])
            cut = line.intersection(self.local)
            pieces = []
            for g in getattr(cut, "geoms", [cut]):
                if g.geom_type == "LineString" and g.length > 1e-3:
                    xs = np.asarray(g.coords)[:, 1 if across else 0]
                    pieces.append((float(xs.min()), float(xs.max())))
            if pieces:
                out.append((c, pieces))
        return out

    def bars(self, spacing, both=True, bent=False):
        """[(N, 3) points] the bars: along the main way (and across, `both`), each piece from the outline to the
        outline — straight from node to node (the other way's lines), or `bent` (ribs) through points every
        spacing/6 on the surface."""
        along, across = self._lines(spacing, False), self._lines(spacing, True) if both else []
        out = []
        for lines, others, turned in ((along, across, False), (across, along, True)):
            nodes = np.array(sorted(c for c, _p in others)) if others else np.zeros(0)
            for c, pieces in lines:
                for lo, hi in pieces:
                    if bent:
                        t = np.linspace(lo, hi, max(2, int(math.ceil((hi - lo) / (spacing / 6.0))) + 1))
                    else:
                        t = np.concatenate(([lo], nodes[(nodes > lo + 1e-6) & (nodes < hi - 1e-6)], [hi]))
                    local = np.column_stack((np.full(len(t), c), t)) if turned else np.column_stack((t, np.full(len(t), c)))
                    plan = _turn(local, self.angle)
                    edge = np.zeros(len(t), dtype=bool)
                    edge[0] = edge[-1] = True
                    out.append(self.lift(plan, edge))
        if len(out) > MAX_BARS:
            raise ValueError("organic_many")
        return out

    def panes(self, spacing):
        """(vertices (N, 3), triangles) the glass: each grid cell (cut by the outline) in flat triangles between
        its corners on the surface."""
        import shapely
        from shapely.geometry import box
        u0, v0, u1, v1 = self.local.bounds
        verts, tris = [], []
        count = 0
        across = [c for c, _p in self._lines(spacing, True)]
        along = [c for c, _p in self._lines(spacing, False)]
        us = [u0 - 1.0] + across + [u1 + 1.0]
        vs = [v0 - 1.0] + along + [v1 + 1.0]
        edge_ring = self.local.exterior
        for a, b in zip(us, us[1:]):
            for c, d in zip(vs, vs[1:]):
                cell = box(a, c, b, d).intersection(self.local)
                for q in getattr(cell, "geoms", [cell]):
                    if q.geom_type != "Polygon" or q.area < 1e-4:
                        continue
                    for g in shapely.constrained_delaunay_triangles(q).geoms:
                        p = np.asarray(g.exterior.coords)[:3]
                        if (p[1, 0] - p[0, 0]) * (p[2, 1] - p[0, 1]) - (p[1, 1] - p[0, 1]) * (p[2, 0] - p[0, 0]) < 0:
                            p = p[::-1]
                        on_edge = np.array([edge_ring.distance(shapely.Point(x, y)) < 1e-6 for x, y in p])
                        verts.append(self.lift(_turn(p, self.angle), on_edge))
                        tris.append(np.array([[count, count + 1, count + 2]]))
                        count += 3
        if not verts:
            return np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64)
        return np.vstack(verts), np.vstack(tris).astype(np.int64)

    def ring(self, width):
        """(outer [(x, y)], inner [(x, y)] or None) the ring beam's band under the edge, `width` in from it."""
        inner = self.poly.buffer(-width, join_style=2)
        outer = list(self.poly.exterior.coords)[:-1]
        if inner.is_empty or inner.geom_type != "Polygon":
            return outer, None
        return outer, list(inner.exterior.coords)[:-1]

    def supports(self, mode, spacing, inset):
        """[(x, y)] where the supports stand: at the outline's corners («cantos»: where it turns more than
        CORNER_TURN — none on a smooth curve: then spaced), or every `spacing` along it («espacados»); `inset` in
        from the edge (under the ring beam's middle)."""
        if mode not in ("cantos", "espacados"):
            return []
        line = self.poly.buffer(-inset, join_style=2) if inset > 0 else self.poly
        if line.is_empty or line.geom_type != "Polygon":
            line = self.poly
        ring = np.asarray(line.exterior.coords)[:-1]
        if mode == "cantos":
            prev, nxt = np.roll(ring, 1, axis=0), np.roll(ring, -1, axis=0)
            a, b = ring - prev, nxt - ring
            turn = np.degrees(np.abs(np.arctan2(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0], (a * b).sum(axis=1))))
            corners = ring[turn > CORNER_TURN]
            if len(corners) >= 3:
                return [tuple(map(float, c)) for c in corners]
        length = line.exterior.length
        n = max(3, int(round(length / max(spacing, 0.5))))
        return [tuple(map(float, line.exterior.interpolate(k * length / n).coords[0])) for k in range(n)]


def area(verts, tris):
    """The surface's area (m²)."""
    if not len(tris):
        return 0.0
    a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    return float(np.linalg.norm(np.cross(b - a, c - a), axis=1).sum() / 2.0)


def smooth_outline(points, step=0.25):
    """(0.390) A closed outline clicked point by point made a smooth curve through them (closed Catmull–Rom, a point
    every `step` m) — the «organic» outline. Fewer than 3 points: as given."""
    p = np.asarray(points, dtype=float).reshape(-1, 2)
    n = len(p)
    if n < 3:
        return [tuple(q) for q in p]
    out = []
    for k in range(n):
        p0, p1, p2, p3 = p[(k - 1) % n], p[k], p[(k + 1) % n], p[(k + 2) % n]
        m = max(2, int(math.ceil(float(np.linalg.norm(p2 - p1)) / step)))
        for t in np.arange(m) / m:
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                                    + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)))
    return out
