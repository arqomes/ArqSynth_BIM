"""(0.320) What a plan or a section cuts, joined by material as Revit cleans up its joins — only the drawing: each
element keeps its own shape in the IFC.

- Where two elements overlap, the stronger layer stays: the core (an element's thickest layer) over the finishes; of
  two equally strong, a column over a beam, a slab, a wall.
- Where a wall with layers ends at another one: at a corner (L) their layers turn it in a mitre — the outer plaster
  round the outside, block on block, the inner plaster round the inside —; against its side (T) its core goes in up
  to the other's core, through its plaster.
- Then the same material is one: a thin line only where the material changes, the thick one round all that is cut
  (`merged`, `outline`).
Pure shapely (no Qt, no GPU): the PDF, the DXF and the screen draw the same."""

import numpy as np

from ..core import drawing2d

AREA = 1e-8          # m²: less is no area (a hair's sliver a difference leaves)
GRID = 1e-6          # m: every corner snapped to it, so that two parts worked out apart meet without a hair between
TOUCH = 1e-4         # m: two outlines this close touch
# (0.442) m: a crack this narrow (or narrower than twice it) between the parts of what is cut, closed when they are
# joined at the end (`_closed`): two walls' parts worked out apart meet along a slanted joint — a mitre of walls a
# little out of square — whose ends the grid rounds to two points a step apart, and the thick line went in and out
# along the crack (one line across the corner)
CLOSE = 2e-5
MITRE = 20.0         # a closing's corners kept sharp (bevelled only when sharper than ~6°)
PARALLEL = 0.9       # |cos| over it: two elements' layers run the same way (walls in a row), not across each other
SAME = 1e-3          # m: two bands this close are one (walls in a row, of one thickness)
CORE, FINISH = 1, 5  # a layer's strength (as Revit's priorities): an element's core, its other layers
# (of two equally strong layers where they overlap, the element first here wins)
RANK = {"IfcColumn": 0, "IfcBeam": 1, "IfcMember": 1, "IfcSlab": 2, "IfcFooting": 2, "IfcRoof": 3, "IfcWall": 4,
        "IfcWallStandardCase": 4}
WALLS = ("IfcWall", "IfcWallStandardCase", "IfcWallElementedCase")


class _Element:
    """One element cut: its parts [[key, strength, region]], its class, its order among them, and — when its layers
    lie across the drawing — its band (direction (2,), offset, lowest, highest: e = n·p + c across it) and its layers
    [(key, e0, e1, strength)]."""

    def __init__(self, owner, cls, order):
        self.owner, self.cls, self.order = owner, cls, order
        self.parts = []
        self.band = None
        self.layers = []
        self._whole = None

    def whole(self):
        """All its parts as one (kept until they change)."""
        if self._whole is None:
            self._whole = _union([g for _k, _s, g in self.parts])
        return self._whole

    def take(self, region):
        """Its parts less `region`."""
        if region is None or region.is_empty:
            return
        for part in self.parts:
            if part[2].intersects(region):
                part[2] = _minus(part[2], region)
                self._whole = None

    def give(self, key, strength, region):
        """`region` added to its part of `key`."""
        region = _clean(region)
        if region.is_empty:
            return
        self._whole = None
        for part in self.parts:
            if part[0] == key:
                part[2] = _clean(_union([part[2], region]))
                part[1] = min(part[1], strength)
                return
        self.parts.append([key, strength, region])


class Fills(list):
    """(fills of `join`) [(outline, key)] that know their material's regions, each one already joined (`merged`),
    and each element's part of each ({(element, key): region}); (0.333) the lines between elements unjoined by hand
    ((K, 2, 2): drawn as the outline of what is cut is)."""
    regions = None
    parts = None
    breaks = None


def bands(layers, origin, u, v, strengths=None):
    """{element: (direction (2,), offset, [(key, e0, e1, strength or None)])} of elements' layers (IfcModel.layers:
    [(key, normal, d0, d1)], 3D) on a drawing's plane (origin, u, v) — those whose layers lie across it (a wall cut
    by a plan; not one a section cuts along its length). strengths (0.334): {element: [each layer's strength or
    None]} (IfcModel.layer_strengths: its function in its type)."""
    origin, u, v = (np.asarray(a, dtype=float) for a in (origin, u, v))
    strengths = strengths or {}
    out = {}
    for owner, parts in layers.items():
        if not parts:
            continue
        n = np.asarray(parts[0][1], dtype=float)
        n2 = np.array((n @ u, n @ v))
        k = float(np.linalg.norm(n2))
        if k < 0.5:
            continue
        given = list(strengths.get(owner) or ())
        given += [None] * (len(parts) - len(given))
        out[owner] = (n2 / k, float(n @ origin) / k,
                      [(key, d0 / k, d1 / k, s) for (key, _n, d0, d1), s in zip(parts, given)])
    return out


def join(fills, whose, classes=None, banded=None, apart=None):
    """fills [(outline (N, 2), key)] and each one's element (drawings._fills) joined: overlaps left to the stronger
    layer, the walls' corners and tees cleaned up. classes: {element: IFC class}; banded: bands(); apart (0.333):
    {frozenset((a, b))} of elements unjoined by hand — not cleaned up together, the line between them kept
    (Fills.breaks). The same (fills, whose) back — an element's outlines its parts' (rings_of: outer ones
    counter-clockwise, holes clockwise)."""
    if len(set(whose)) < 2:
        return fills, whose
    apart = apart or set()
    elements = _elements(fills, whose, classes or {}, banded or {})
    _butt_joins(elements, apart)
    _overlaps(elements, apart)
    out, owners, by = Fills(), [], {}
    out.parts = {}
    for e in elements:
        for key, _s, region in e.parts:
            by.setdefault(key, []).append(region)
            out.parts[(e.owner, key)] = region
            for ring in drawing2d.rings_of(region):
                out.append((ring, key))
                owners.append(e.owner)
    out.regions = {key: _union(regions, GRID) for key, regions in by.items()}
    out.breaks = _breaks(elements, apart) if apart else np.zeros((0, 2, 2))
    return out, owners


def _breaks(elements, apart):
    """(0.333) The lines between elements unjoined by hand: where one's outline lies on or in the other (their common
    side; one's outline over the other where they overlap) — (K, 2, 2)."""
    by = {e.owner: e for e in elements}
    segs = []
    for pair in apart:
        a, b = (by.get(g) for g in pair)
        if a is None or b is None:
            continue
        wa, wb = a.whole(), b.whole()
        if wa.is_empty or wb.is_empty or wa.distance(wb) > TOUCH:
            continue
        for line in (wa.boundary.intersection(wb.buffer(TOUCH)), wb.boundary.intersection(wa.buffer(TOUCH))):
            for part in _lines(line):
                c = np.asarray(part.coords, dtype=float)
                if len(c) >= 2:
                    segs.append(np.stack((c[:-1], c[1:]), axis=1))
    if not segs:
        return np.zeros((0, 2, 2))
    segs = np.concatenate(segs)
    # (not the slivers of one's sides just inside the other's edge: a corner's hair)
    return segs[np.linalg.norm(segs[:, 1] - segs[:, 0], axis=1) > 3 * TOUCH]


def _lines(geometry):
    """The line strings of a geometry (a point where two only touch: none)."""
    if geometry.is_empty:
        return []
    if geometry.geom_type in ("LineString", "LinearRing"):
        return [geometry]
    return [g for part in getattr(geometry, "geoms", ()) for g in _lines(part)]


def merged(fills, whose=None):
    """{key: region} of fills [(outline, key)] (and each one's element): each material's parts as one, so nothing
    is drawn between them (those of `join` know them already)."""
    if getattr(fills, "regions", None) is not None:
        return fills.regions
    by = {}
    for k, (ring, key) in enumerate(fills):
        by.setdefault(key, {}).setdefault(whose[k] if whose is not None else None, []).append(ring)
    return {key: _union([_region(rings) for rings in mine.values()], GRID) for key, mine in by.items()}


def outline(regions):
    """The outlines (rings_of) round all of `merged`'s regions: what is cut, one (its thick line)."""
    return drawing2d.rings_of(whole(regions).simplify(0.0))


def whole(regions):
    """(0.442) All of `merged`'s regions as one — what is cut, its materials together (the cracks between them closed):
    round it the thick line, on paper (`outline`) and on the screen (cut_hatches)."""
    return _union(list(regions), GRID)


def _elements(fills, whose, classes, banded):
    by, order = {}, []
    for (ring, key), owner in zip(fills, whose):
        if owner not in by:
            by[owner] = {}
            order.append(owner)
        by[owner].setdefault(key, []).append(ring)
    out = []
    for k, owner in enumerate(order):
        e = _Element(owner, classes.get(owner), k)
        keys = by[owner]
        band = banded.get(owner)
        if band is not None:
            n, c, layers = band
            layers = [layer if len(layer) == 4 else (*layer, None) for layer in layers]
            lo, hi = min(min(e0, e1) for _k, e0, e1, _s in layers), max(max(e0, e1) for _k, e0, e1, _s in layers)
            e.band = (np.asarray(n, dtype=float), float(c), lo, hi)
            if len(keys) == 1:                     # (drawn with one key — its main hatch, a colour…: one layer)
                layers = [(next(iter(keys)), lo, hi, min((s for *_r, s in layers if s is not None), default=None))]
            if any(s is not None for *_r, s in layers):
                # (0.334) each layer's function in its type (structure 1 … second finish 5); one not given: a finish
                strengths = [s if s is not None else FINISH for *_r, s in layers]
            else:                                  # (as always: the thickest is the core, the others finishes)
                core = max(layers, key=lambda layer: abs(layer[2] - layer[1]))[0]
                strengths = [CORE if key == core else FINISH for key, *_r in layers]
            e.layers = sorted(((key, min(e0, e1), max(e0, e1), s) for (key, e0, e1, _g), s in zip(layers, strengths)),
                              key=lambda layer: layer[1])
            strength = {}
            for (key, *_r), s in zip(layers, strengths):            # (a material in two layers: the stronger)
                strength[key] = min(strength.get(key, s), s)
        else:
            strength = {}
        for key, rings in keys.items():
            region = _region(rings)
            if not region.is_empty:
                e.parts.append([key, strength.get(key, CORE), region])
        out.append(e)
    return out


def _region(rings):
    """What one element's outlines of one key fill (drawing2d.region), snapped to the grid — one outline (most
    often) made so at once."""
    from shapely.geometry import Polygon
    if len(rings) == 1 and len(rings[0]) >= 3 and drawing2d._signed_area(rings[0]) > 0:
        return _clean(_snap(Polygon(rings[0])))
    return _clean(_snap(drawing2d.region(rings)))


def _butt_joins(elements, apart=()):
    """The walls (and slabs, in a section) whose layers lie across the drawing, where one ends at another — (0.333) not
    two unjoined by hand."""
    banded = [e for e in elements if e.band is not None and e.layers and e.parts]
    if len(banded) < 2:
        return
    from shapely.strtree import STRtree
    lo = np.min([e.whole().bounds[:2] for e in banded], axis=0) - 1.0
    hi = np.max([e.whole().bounds[2:] for e in banded], axis=0) + 1.0
    box = (float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1]))
    tree = STRtree([e.whole() for e in banded])
    for y in banded:
        mine = y.whole()
        if mine.is_empty:
            continue
        near = [banded[i] for i in tree.query(mine, predicate="dwithin", distance=TOUCH * 10)]
        others = [x for x in near if x is not y and abs(float(x.band[0] @ y.band[0])) < PARALLEL
                  and frozenset((x.owner, y.owner)) not in apart]
        if not others:
            continue
        row = [m for m in near if m is y or _same_band(m.band, y.band)]       # (y and the walls it goes on as)
        row_points = np.concatenate([_points(m.whole()) for m in row])
        for group in _rows(others):
            _butt(y, row_points, group, box)


def _rows(elements):
    """Elements in groups of one band (walls in a row, of one thickness): one 'through' wall for the one ending."""
    groups = []
    for e in elements:
        for g in groups:
            if _same_band(e.band, g[0].band):
                g.append(e)
                break
        else:
            groups.append([e])
    return groups


def _same_band(a, b):
    n, _c, lo, hi = _forward(a)
    m, _d, glo, ghi = _forward(b)
    return bool(np.allclose(n, m, atol=1e-3)) and abs(lo - glo) < SAME and abs(hi - ghi) < SAME


def _forward(band):
    """A band one way round (its direction's first clear component positive), so that two of one row compare."""
    n, c, lo, hi = band
    lead = int(np.argmax(np.abs(n) > 1e-6))
    if n[lead] < 0:
        return -n, -c, -hi, -lo
    return n, c, lo, hi


def _butt(y, row_points, group, box):
    """Wall y ending at the walls `group` (one band): at a corner, a mitre; against their side, y's layers in up to
    as strong a layer of theirs. row_points: the corners of y and of the walls in a row with it (it ends there only
    if they all do)."""
    ny, cy, ylo, yhi = y.band
    nx, cx, xlo, xhi = group[0].band
    # y ends at x: its row, across x's band, all on one side of it
    t = _one_side(row_points @ nx + cx, xlo, xhi)
    if t == 0:
        return
    x_whole = group[0].whole() if len(group) == 1 else _union([x.whole() for x in group])
    y_whole = y.whole()
    if x_whole.is_empty or y_whole.distance(x_whole) > TOUCH:
        return
    across_y = _slab(ny, cy, ylo, yhi, box)                       # y's band, on through x
    # where y's band goes through x, next to y
    corner = _union([p for p in _polys(_and(x_whole, across_y)) if p.area > AREA and p.distance(y_whole) <= TOUCH])
    if corner.is_empty:
        return
    # a corner (L) when x is on one side of y's band only; against its side (T) when on both
    s = _one_side(_points(x_whole) @ ny + cy, ylo, yhi)
    walls = y.cls in WALLS and all(x.cls in WALLS for x in group)
    if s != 0 and walls:
        # each one's depth from its face on the corner's outside: y's away from the rest of x, x's away from y
        wy, ky = (ny, cy - ylo) if s > 0 else (-ny, yhi - cy)
        wx, kx = (nx, cx - xlo) if t > 0 else (-nx, xhi - cx)
        mitre = _and(corner, _half(wy - wx, ky - kx, box))              # (y's half: nearer its own outside)
        for x in group:
            x.take(mitre)
        y.take(_minus(corner, mitre))
        for key, e0, e1, strength in y.layers:
            y.give(key, strength, _and(mitre, _slab(ny, cy, e0, e1, box)))
        return
    # against x's side (or a corner with what is not a wall): y's layers in, each through x's weaker ones
    order = sorted(group[0].layers, key=lambda layer: -layer[2]) if t > 0 else sorted(group[0].layers,
                                                                                         key=lambda layer: layer[1])
    face = xhi if t > 0 else xlo
    y.take(corner)
    for key, e0, e1, strength in y.layers:
        reach = None
        for _kx, f0, f1, other in order:
            if other <= strength:
                reach = f1 if t > 0 else f0
                break
        if reach is None:
            reach = xlo if t > 0 else xhi
        if abs(reach - face) < 1e-9:
            continue
        piece = _and(_and(corner, _slab(ny, cy, e0, e1, box)), _slab(nx, cx, min(reach, face), max(reach, face), box))
        if piece.area > AREA:
            for x in group:
                x.take(piece)
            y.give(key, strength, piece)


def _overlaps(elements, apart=()):
    """Where two elements' parts of different materials overlap, the stronger keeps it — (0.333) not between two
    unjoined by hand (each drawn whole)."""
    from shapely.strtree import STRtree
    items = [(e, part) for e in elements for part in e.parts if not part[2].is_empty]
    if len(items) < 2:
        return
    geometries = [part[2] for _e, part in items]
    tree = STRtree(geometries)
    pairs = tree.query(geometries, predicate="intersects")
    box = np.array([g.bounds for g in geometries])
    for i, j in sorted({(int(a), int(b)) for a, b in zip(*pairs) if a < b}):
        (ea, a), (eb, b) = items[i], items[j]
        if ea is eb or a[0] == b[0] or a[2].is_empty or b[2].is_empty or frozenset((ea.owner, eb.owner)) in apart:
            continue
        if min(box[i, 2], box[j, 2]) - max(box[i, 0], box[j, 0]) < TOUCH or \
                min(box[i, 3], box[j, 3]) - max(box[i, 1], box[j, 1]) < TOUCH:
            continue                                             # (side by side, not over each other)
        both = _and(a[2], b[2])
        if both.area < AREA:
            continue
        first = (a[1], RANK.get(ea.cls, 9), ea.order) <= (b[1], RANK.get(eb.cls, 9), eb.order)
        loser = b if first else a
        loser[2] = _minus(loser[2], both)
    for e in elements:
        e.parts = [part for part in e.parts if not part[2].is_empty]


def _slab(n, c, e0, e1, box):
    """The part of the box (x0, y0, x1, y1) where e0 <= n·p + c <= e1."""
    from shapely.geometry import Polygon
    x0, y0, x1, y1 = box
    ring = drawing2d.clip_between(np.array(((x0, y0), (x1, y0), (x1, y1), (x0, y1)), dtype=float),
                                  np.asarray(n, dtype=float), e0 - c, e1 - c)
    return Polygon(ring) if ring is not None else Polygon()


def _half(w, k, box):
    """The part of the box where w·p + k <= 0."""
    from shapely.geometry import Polygon
    x0, y0, x1, y1 = box
    pts = np.array(((x0, y0), (x1, y0), (x1, y1), (x0, y1)), dtype=float)
    s = -(pts @ np.asarray(w, dtype=float) + k)                    # (kept: s >= 0)
    out = []
    for i in range(4):
        j = (i + 1) % 4
        if s[i] >= 0:
            out.append(pts[i])
        if (s[i] >= 0) != (s[j] >= 0):
            out.append(pts[i] + (pts[j] - pts[i]) * (s[i] / (s[i] - s[j])))
    return Polygon(out) if len(out) >= 3 else Polygon()


def _one_side(e, lo, hi):
    """Points' places across a band (e, against its faces lo, hi): +1 all on its far side (or in it), -1 all on its
    near side (or in it), 0 on both sides — or all in it."""
    below, above = float(e.min()) < lo - SAME, float(e.max()) > hi + SAME
    return 0 if below == above else (1 if above else -1)


def _points(geometry):
    """A region's corners (K, 2)."""
    import shapely
    return shapely.get_coordinates(geometry)


def _polys(geometry):
    if geometry is None or geometry.is_empty:
        return []
    if geometry.geom_type == "Polygon":
        return [geometry]
    return [p for g in getattr(geometry, "geoms", ()) for p in _polys(g)]


def _clean(geometry):
    """Only its polygons with some area (a difference leaves lines and slivers)."""
    from shapely.geometry import MultiPolygon, Polygon
    if geometry.geom_type == "Polygon":                     # (the most often: as it is)
        return geometry if geometry.area > AREA else Polygon()
    polys = [p for p in _polys(geometry) if p.area > AREA]
    if not polys:
        return Polygon()
    return polys[0] if len(polys) == 1 else MultiPolygon(polys)


def _union(geometries, grid=None):
    """Regions as one; grid: snapped to it (the materials' regions at the end: two parts worked out apart meet
    without a hair between them) — (0.442) and the cracks left between them closed (`_closed`)."""
    import shapely
    from shapely.geometry import Polygon
    geometries = [g for g in geometries if g is not None and not g.is_empty]
    if not geometries:
        return Polygon()
    if len(geometries) == 1 and grid is None:
        return geometries[0]
    if grid is None:
        return _clean(shapely.union_all(geometries))
    if len(geometries) < 8:
        return _closed(shapely.union_all(geometries, grid_size=grid), grid)
    # many (a material's parts over a storey): only those that touch joined — each group at once, much quicker
    from shapely.geometry import MultiPolygon
    from shapely.strtree import STRtree
    polys = [p for g in geometries for p in _polys(g)]
    tree = STRtree(polys)
    a, b = tree.query(polys, predicate="dwithin", distance=max(grid * 10, 2 * CLOSE))
    root = list(range(len(polys)))

    def find(i):
        while root[i] != i:
            root[i] = root[root[i]]
            i = root[i]
        return i

    for i, j in zip(a.tolist(), b.tolist()):
        if i != j:
            root[find(i)] = find(j)
    groups = {}
    for i in range(len(polys)):
        groups.setdefault(find(i), []).append(polys[i])
    out = []
    for members in groups.values():
        joined = _closed(shapely.union_all(members, grid_size=grid) if len(members) > 1 else members[0], grid)
        out += [p for p in _polys(joined) if p.area > AREA]
    return out[0] if len(out) == 1 else MultiPolygon(out)


def _closed(geometry, grid):
    """(0.442) A region joined with its cracks closed — out CLOSE and back in (a morphological closing, its corners
    mitred, so they stay where they are): two parts that meet along a slanted line, their ends rounded to the grid a
    step apart, as one (no thick line in and out along the crack); a hair-thin slit into a part, gone. Snapped to the
    grid again."""
    import shapely
    if geometry.is_empty:
        return _clean(geometry)
    grown = shapely.buffer(geometry, CLOSE, join_style="mitre", mitre_limit=MITRE)
    return _clean(shapely.set_precision(shapely.buffer(grown, -CLOSE, join_style="mitre", mitre_limit=MITRE), grid))


def _minus(a, b):
    import shapely
    return _clean(shapely.difference(a, b))


def _and(a, b):
    import shapely
    return _clean(shapely.intersection(a, b))


def _snap(geometry):
    import shapely
    return shapely.set_precision(geometry, GRID)
