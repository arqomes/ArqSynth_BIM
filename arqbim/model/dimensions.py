"""Dimensions (Phase 3, step 14): a dimension is drawn in a view — the plan of a storey, a
section, an elevation — and shown there only (on screen and on paper), like Revit's. It
measures the distance between two points as seen in its view (in a plan: across the floor),
its line passing through a third point. An end taken on an element (a wall's corner…) hangs
on it: it follows when the element is moved or turned.

Not IFC: kept with the views in the .arqbim file (the owner's decision, 2026-10-21).
"""

import uuid
from dataclasses import dataclass, field

import numpy as np

from ..core import dim_layout


CHAIN_OFFSET, TOTAL_OFFSET = 0.8, 1.4      # m out from a wall's face: its chain of dimensions, its overall one
CORNER = 0.6                               # m: a wall this near a wall's end, flush with its face, makes its corner


@dataclass(eq=False)
class Dimension:
    view: tuple                    # ("plan", storey GlobalId) | ("section", name) | ("elevation", side)
    a: np.ndarray                  # the ends (world, program coordinates) as drawn
    b: np.ndarray
    at: np.ndarray                 # a point the dimension line goes through
    refs: list = field(default_factory=lambda: [None, None])   # per end: (GlobalId, point in its frame, anchor) or None
    tag: str = None                # "wall:<GlobalId>" for the ones made by "Dimension the walls" (made again)
    at_ref: tuple = None           # (GlobalId, point in its frame): the line goes with that element
    # (0.122) an angular dimension: the corner of the angle (a and b on its two sides, `at` where its arc goes)
    vertex: np.ndarray = None
    vertex_ref: tuple = None       # (GlobalId, point in its frame, anchor) as refs, or None
    # (0.123) measured along this direction (world), its line parallel to it — a façade's, horizontal — not
    # from a to b (aligned)
    direction: np.ndarray = None
    style: str = None              # (0.193) its dimension type's name (the project's style's "types"); None: that style
    # (0.398) the string it is a piece of (Revit's dimension string: the pieces side by side on one line, drawn and
    # chosen as one), or None (alone)
    chain: str = None
    # (0.398) its own words — {"override": text written over its value, "prefix", "suffix", "above", "below"} —,
    # or None; eq: it says the type's «IG» (its string made equal)
    note: dict = None
    eq: bool = False


def new_chain():
    """(0.398) A new string's id."""
    return uuid.uuid4().hex[:12]


class ReplaceDimensions:
    """Some dimensions out, others in (Dimension the walls: again replaces), one undo step."""

    def __init__(self, remove, add, label):
        self.remove, self.add, self.label = list(remove), list(add), label
        self._where = []

    def do(self, doc):
        self._where = [(doc.dimensions.index(d), d) for d in self.remove if d in doc.dimensions]
        for _k, d in self._where:
            doc.dimensions.remove(d)
        doc.dimensions.extend(self.add)
        doc.dimensions_changed()

    def undo(self, doc):
        for d in self.add:
            doc.dimensions.remove(d)
        for k, d in sorted(self._where, key=lambda item: item[0]):
            doc.dimensions.insert(k, d)
        doc.dimensions_changed()


def _joined(doc, guid):
    """The walls joined to this one that are on screen (ArqBIM's joints; none for other files)."""
    try:
        return [g for g in doc.ifc.joined_walls([guid]) if doc.get(g) is not None]
    except Exception:
        return []


def wall_chains(doc, walls, storey):
    """Dimensions of walls on the plan of `storey`, as an architect puts them: on the outer side
    of each wall (away from the middle of the walls), a chain from end to end through the jambs
    of its doors and windows, and the overall length further out. Each end hangs on its wall."""
    from . import bim
    frames = {}
    for guid in walls:
        obj = doc.get(guid)
        if obj is None or not obj.is_bim:
            continue
        m = doc.ifc.placement(guid)
        local = (obj.mesh.verts - m[:3, 3]) @ m[:3, :3]                 # (rotation: columns are the axes)
        frames[guid] = (m, local)
    if not frames:
        return []
    middle = np.mean([np.mean(doc.get(g).mesh.verts, axis=0) for g in frames], axis=0)
    out = []
    for guid, (m, local) in frames.items():
        y_lo, y_hi = float(local[:, 1].min()), float(local[:, 1].max())
        centre = np.mean(doc.get(guid).mesh.verts, axis=0)
        outward = 1.0 if float((centre - middle) @ m[:3, 1]) > 1e-6 else -1.0
        face = y_hi if outward > 0 else y_lo
        # from end to end of the face — on to the outer corner of the walls at its ends (joined to it,
        # or among those dimensioned, flush with the face and within CORNER of its end): a side wall
        # between two others measures the whole house, as one would
        own = local[np.abs(local[:, 1] - face) < 1e-3, 0]
        x_lo, x_hi = float(own.min()), float(own.max())
        others = set(_joined(doc, guid)) | (set(frames) - {guid})
        for g in others:
            pts = (doc.get(g).mesh.verts - m[:3, 3]) @ m[:3, :3]
            pts = pts[(np.abs(pts[:, 1] - face) < 1e-3) & (pts[:, 0] > x_lo - CORNER) & (pts[:, 0] < x_hi + CORNER)]
            if len(pts):
                x_lo, x_hi = min(x_lo, float(pts[:, 0].min())), max(x_hi, float(pts[:, 0].max()))
        xs = [(x_lo, guid), (x_hi, guid)]              # (x, the element the point hangs on)
        for filling in bim._fillings(doc, guid):       # the jambs go with their door / window
            st = doc.ifc.filling_state(filling)
            xs += [(st["s"], filling), (st["s"] + st["width"], filling)]
        xs = sorted(p for p in xs if x_lo - 1e-6 <= p[0] <= x_hi + 1e-6)
        xs = [p for k, p in enumerate(xs) if k == 0 or p[0] - xs[k - 1][0] > 1e-3]
        world = lambda p: m[:3, :3] @ p + m[:3, 3]                      # noqa: E731
        z = float(local[:, 2].min())

        def dim(p0, p1, offset, chain):
            (x0, o0), (x1, o1) = p0, p1
            a, b = world(np.array((x0, face, z))), world(np.array((x1, face, z)))
            at = world(np.array(((x0 + x1) / 2, face + outward * offset, z)))
            refs = [hang(doc, o0, a), hang(doc, o1, b)]
            return Dimension(("plan", storey), a, b, at, refs, "wall:" + guid, hang_line(doc, [(guid,)], at),
                             chain=chain)
        row = new_chain()
        out += [dim(p0, p1, CHAIN_OFFSET, row) for p0, p1 in zip(xs, xs[1:])]
        if len(xs) > 2:
            out.append(dim(xs[0], xs[-1], TOTAL_OFFSET, new_chain()))
    return out


FACADE_ROWS = (0.8, 1.4, 2.0)   # m out from a façade's outermost face: openings and corners, corners, overall
SIDES = {"S": ((1.0, 0.0), (0.0, -1.0)), "N": ((1.0, 0.0), (0.0, 1.0)),       # side -> (along it, out of it)
         "W": ((0.0, 1.0), (-1.0, 0.0)), "E": ((0.0, 1.0), (1.0, 0.0))}


def _walls_of(doc, storey):
    """The straight walls of a storey (ArqBIM's) shown: [(GlobalId, its plan outline as a shapely polygon)]."""
    from shapely.geometry import MultiPoint
    out = []
    for o in doc.objects.values():
        if not o.is_bim or o.storey != storey or o.ifc_class not in ("IfcWall", "IfcWallStandardCase"):
            continue
        try:
            if doc.ifc.kind_of(o.id) != "wall":
                continue
        except Exception:
            continue
        hull = MultiPoint([(float(p[0]), float(p[1])) for p in o.mesh.verts]).convex_hull
        if hull.geom_type == "Polygon":
            out.append((o.id, hull))
    return out


def _nearest_wall(walls, point):
    from shapely.geometry import Point
    q = Point(float(point[0]), float(point[1]))
    guid, poly = min(walls, key=lambda w: w[1].distance(q))
    return guid if poly.distance(q) < 1e-3 else None


def facade_chains(doc, storey):
    """The façades' dimensions on the plan of `storey` (0.123), as an architect puts them round a building: on
    each of its four sides, out from its outermost face, up to three rows — every corner of that side and the
    jambs of its doors and windows; its corners only (when it has openings); the overall length. Measured
    along the side (horizontal / vertical), each end on its corner or jamb, which it hangs on (tag
    "facade:<side>")."""
    from shapely.geometry import LineString, Point
    from shapely.geometry.polygon import orient
    from shapely.ops import unary_union
    from . import bim
    walls = _walls_of(doc, storey)
    if not walls:
        return []
    union = unary_union([p for _g, p in walls]).buffer(1e-4, join_style="mitre").buffer(-1e-4, join_style="mitre")
    building = max(getattr(union, "geoms", [union]), key=lambda g: g.area).simplify(1e-4)   # (no corner in a line)
    ring = list(orient(building, 1.0).exterior.coords)
    z = next((level for g, _n, level in doc.ifc.storeys() if g == storey), 0.0)
    view = ("plan", storey)
    out = []
    for side, (along, outward) in SIDES.items():
        along, outward = np.array(along), np.array(outward)
        faces = []                                       # the ring's edges on this side (looking out of it)
        for p, q in zip(ring, ring[1:]):
            p, q = np.array(p), np.array(q)
            d = q - p
            length = float(np.linalg.norm(d))
            if length > 1e-6 and float(np.array((d[1], -d[0])) / length @ outward) > 0.999:
                faces.append((p, q))
        if not faces:
            continue
        points = []                                      # (along, plan point, element it hangs on, a corner?)
        for p, q in faces:
            for c in (p, q):
                points.append((float(c @ along), c, _nearest_wall(walls, c), True))
        lines = [LineString([tuple(p), tuple(q)]) for p, q in faces]
        for guid, _poly in walls:
            for filling in bim._fillings(doc, guid):
                st = doc.ifc.filling_state(filling)
                f = st["frame"]
                for y in (f.y0, f.y1):
                    for s in (st["s"], st["s"] + st["width"]):
                        c = f.to_world((s, y, f.z0))[:2]
                        if any(line.distance(Point(float(c[0]), float(c[1]))) < 1e-3 for line in lines):
                            points.append((float(c @ along), np.asarray(c, dtype=float), filling, False))
        points.sort(key=lambda item: item[0])
        points = [p for k, p in enumerate(points) if k == 0 or p[0] - points[k - 1][0] > 1e-3]
        if len(points) < 2:
            continue
        depth = max(float(c @ outward) for _s, c, _g, _k in points)
        corners = [p for p in points if p[3]]

        def row(chain, offset):
            dims, string_id = [], new_chain()
            for (s0, c0, g0, _k0), (s1, c1, g1, _k1) in zip(chain, chain[1:]):
                a, b = np.array((c0[0], c0[1], z)), np.array((c1[0], c1[1], z))
                mid = along * (s0 + s1) / 2 + outward * (depth + offset)
                at = np.array((mid[0], mid[1], z))
                dims.append(Dimension(view, a, b, at, [hang(doc, g0, a), hang(doc, g1, b)], "facade:" + side,
                                      direction=np.array((along[0], along[1], 0.0)), chain=string_id))
            return dims
        out += row(points, FACADE_ROWS[0])
        if len(corners) < len(points) and len(corners) > 2:
            out += row(corners, FACADE_ROWS[1])
        if len(points) > 2:
            out += row([points[0], points[-1]], FACADE_ROWS[2])
    return out


def room_chains(doc, storey):
    """The rooms' inner dimensions on the plan of `storey` (0.123): across each room, from wall to wall, its
    width and its depth through a point well inside it (horizontal and vertical), each end on the wall it
    touches (tag "room:<GlobalId>")."""
    from shapely.geometry import LineString, Point, Polygon
    walls = _walls_of(doc, storey)
    try:
        rooms = doc.ifc.spaces(storey)
    except Exception:
        return []
    view, out = ("plan", storey), []
    for room in rooms:
        poly = Polygon(room["outline"], room.get("holes") or []).buffer(0)
        if poly.is_empty or poly.area < 0.5:
            continue
        inside = poly.representative_point()
        x0, y0, x1, y1 = poly.bounds
        z = float(room.get("level") or 0.0)
        for direction in ((1.0, 0.0), (0.0, 1.0)):
            # (the line a quarter of the room off its middle — clear of its name and area — if it is still in it)
            normal = np.array((-direction[1], direction[0]))
            reach = abs(float(normal @ np.array((x1 - x0, y1 - y0))))
            through = next((q for q in (np.array((inside.x, inside.y)) + normal * reach * k for k in (0.25, -0.25, 0.0))
                            if poly.contains(Point(float(q[0]), float(q[1])))), None)
            if through is None:
                continue
            d = np.array(direction) * (x1 - x0 + y1 - y0 + 2)
            cut = poly.intersection(LineString([tuple(through - d), tuple(through + d)]))
            q = Point(float(through[0]), float(through[1]))
            piece = next((g for g in getattr(cut, "geoms", [cut]) if g.geom_type == "LineString"
                          and g.distance(q) < 1e-6), None)
            if piece is None or piece.length < 0.1:
                continue
            (ax, ay), (bx, by) = piece.coords[0], piece.coords[-1]
            a, b = np.array((ax, ay, z)), np.array((bx, by, z))
            at = np.array((through[0], through[1], z))                      # (on the line itself, wall to wall)
            refs = [hang(doc, _nearest_wall(walls, p) if walls else None, p) for p in (a, b)]
            out.append(Dimension(view, a, b, at, refs, "room:" + room["guid"],
                                 direction=np.array((direction[0], direction[1], 0.0))))
    return out


GRID_CHAIN_IN, GRID_TOTAL_IN = 0.65, 0.3  # of the way in from the axes' ends to the grid: its chain, its overall


def grid_chains(axes, z, view, bubble=0.35):
    """The structural grid's dimensions in a plan (0.91): for each family of parallel axes, between the grid and
    the bubbles at their lower ends (as drawn by hand), a chain between neighbouring axes and, further out, the
    overall one (3 axes or more) — Dimension, tag "grid"."""
    families = []
    for axis in axes:
        d = np.array(axis.end, dtype=float) - np.array(axis.start, dtype=float)
        length = float(np.linalg.norm(d))
        if length < 1e-9:
            continue
        d /= length
        if d[0] < -1e-9 or (abs(d[0]) <= 1e-9 and d[1] < 0):
            d = -d                                         # (one way for a family: +x, else +y)
        for fam in families:
            if abs(fam[0][0] * d[1] - fam[0][1] * d[0]) < 1e-6:
                fam[1].append(axis)
                break
        else:
            families.append((d, [axis]))
    out = []
    for d, members in families:
        if len(members) < 2:
            continue
        n = np.array((-d[1], d[0]))
        ends = [float(np.array(p, dtype=float) @ d) for a in members for p in (a.start, a.end)]
        s0 = min(ends)
        offsets = sorted({round(float(np.array(a.start, dtype=float) @ n), 9) for a in members})
        # where the grid begins along d: the first axis crossing these (else 1,5 m in)
        crossing = [float(np.array(a.start, dtype=float) @ d) for fam_d, others in families
                    if abs(fam_d[0] * d[1] - fam_d[1] * d[0]) > 1e-6 for a in others]
        inner = (min(crossing) - s0) if crossing and min(crossing) > s0 + 1e-6 else 1.5

        def point(o, s):
            p = n * o + d * s
            return np.array((p[0], p[1], z))

        s = s0 + inner * GRID_CHAIN_IN
        row = new_chain()
        for o0, o1 in zip(offsets, offsets[1:]):
            a, b = point(o0, s), point(o1, s)
            out.append(Dimension(view, a, b, (a + b) / 2, tag="grid", chain=row))
        if len(offsets) > 2:
            a, b = point(offsets[0], s), point(offsets[-1], s)
            at = (a + b) / 2 - np.array((d[0], d[1], 0.0)) * inner * (GRID_CHAIN_IN - GRID_TOTAL_IN)
            out.append(Dimension(view, a, b, at, tag="grid"))
    return out


class AddDimension:
    def __init__(self, dim, label):
        self.dim, self.label = dim, label

    def do(self, doc):
        doc.dimensions.append(self.dim)
        doc.dimensions_changed()

    def undo(self, doc):
        doc.dimensions.remove(self.dim)
        doc.dimensions_changed()


class RemoveDimensions:
    def __init__(self, dims, label):
        self.dims, self.label = list(dims), label
        self._where = []

    def do(self, doc):
        self._where = [(doc.dimensions.index(d), d) for d in self.dims if d in doc.dimensions]
        for _k, d in self._where:
            doc.dimensions.remove(d)
        doc.dimensions_changed()

    def undo(self, doc):
        for k, d in sorted(self._where, key=lambda item: item[0]):
            doc.dimensions.insert(k, d)
        doc.dimensions_changed()


def _wall_length(doc, guid):
    try:
        return float(doc.ifc.wall_params(guid)[0])
    except Exception:           # not one of ArqBIM's walls
        return None


def _placed(doc, guid):
    """(0.402) An element's placement and (a wall's) length, read once while the model is the same — a plan's
    dimensions ask for the same few walls hundreds of times each time they are drawn. (None, None): gone, or the IFC
    still being read."""
    revision = getattr(doc, "revision", None)
    memo = getattr(doc, "_dim_placed", None)
    if memo is None or memo.get("_rev") != revision or memo.get("_file") is not getattr(doc, "ifc", None):
        memo = doc._dim_placed = {"_rev": revision, "_file": getattr(doc, "ifc", None)}
    if guid not in memo:
        try:
            m = doc.ifc.placement(guid)
        except Exception:
            m = None
        memo[guid] = (m, _wall_length(doc, guid) if m is not None else None)
    return memo[guid]


def ends(doc, dim):
    """The dimension's ends now: an end hanging on an element follows its placement; on a wall,
    it keeps to the end of the wall it was near (a wall made longer takes it along)."""
    out = []
    for point, ref in zip((dim.a, dim.b), dim.refs):
        p = np.asarray(point, dtype=float)
        if ref is not None:
            m, length = _placed(doc, ref[0])    # (gone, or the IFC still being read: where it was drawn)
            if m is not None:
                local = np.array(ref[1], dtype=float)
                anchor = ref[2] if len(ref) > 2 else None
                if anchor is not None:
                    if length is not None:
                        local[0] = anchor[1] if anchor[0] == "start" else length + anchor[1]
                if len(ref) > 3 and ref[3]:                 # (0.399) on a wall's face, core or axis: still on it
                    from . import dim_refs
                    found = dim_refs.lines(doc, [ref[0]]).get(ref[0])
                    y = found.y_of(ref[3]) if found is not None else None
                    if y is not None:
                        local[1] = y
                p = m[:3, :3] @ local + m[:3, 3]
        out.append(p)
    return out


def vertex_point(doc, dim):
    """An angular dimension's corner now (it follows the element it hangs on), or None (a linear one)."""
    if dim.vertex is None:
        return None
    return ends(doc, Dimension(dim.view, dim.vertex, dim.vertex, dim.vertex, [dim.vertex_ref, None]))[0]


def angle_arc(a2, b2, v2, at2):
    """An angular dimension in the view's 2D frame: the angle between the line v→a and the line v→b on the
    side where `at` is (of the four the two lines make), as (radius, start angle, sweep — counter-clockwise,
    radians —, the angle in degrees), or None (the lines are parallel, or a point on the corner)."""
    da, db, dp = a2 - v2, b2 - v2, at2 - v2
    if min(np.linalg.norm(da), np.linalg.norm(db), np.linalg.norm(dp)) < 1e-9:
        return None
    da, db = da / np.linalg.norm(da), db / np.linalg.norm(db)
    if abs(float(da[0] * db[1] - da[1] * db[0])) < 1e-9:
        return None
    full = 2 * np.pi
    theta = lambda d: float(np.arctan2(d[1], d[0])) % full                 # noqa: E731
    tp = theta(dp)
    for r1 in (da, -da):
        for r2 in (db, -db):
            t1, t2 = theta(r1), theta(r2)
            sweep = (t2 - t1) % full
            if sweep > np.pi:                        # (the sector between them: the smaller way round)
                t1, sweep = t2, full - sweep
            if (tp - t1) % full <= sweep + 1e-12:
                return float(np.linalg.norm(dp)), t1, sweep, float(np.degrees(sweep))
    return None


def angle_text(degrees, decimal=","):
    """'90°', '22,5°' — to a tenth of a degree, without a 0 after the comma."""
    value = round(float(degrees), 1)
    text = "{:.0f}".format(value) if abs(value - round(value)) < 1e-9 else "{:.1f}".format(value)
    return text.replace(".", decimal) + "°"


def line_point(doc, dim):
    """A point the dimension line goes through now (it follows the element it hangs on)."""
    if dim.at_ref is not None:
        m, _length = _placed(doc, dim.at_ref[0])
        if m is not None:
            return m[:3, :3] @ np.asarray(dim.at_ref[1], dtype=float) + m[:3, 3]
    return np.asarray(dim.at, dtype=float)


def hang_line(doc, refs, at):
    """The line's point hung on the element of the first end that hangs on one, or None."""
    ref = next((r for r in refs if r is not None), None)
    if ref is None:
        return None
    try:
        m = doc.ifc.placement(ref[0])
    except Exception:
        return None
    return ref[0], np.linalg.solve(m[:3, :3], np.asarray(at, dtype=float) - m[:3, 3])


def hang(doc, guid, point):
    """(GlobalId, point in the element's frame, anchor) for an end taken on an element, or None.
    anchor: on a wall, ("start" | "end", distance along it from that end) — the nearer end."""
    obj = doc.get(guid) if guid is not None else None
    if obj is None or not obj.is_bim:
        return None
    try:
        m = doc.ifc.placement(guid)
    except Exception:
        return None
    local = np.linalg.solve(m[:3, :3], np.asarray(point, dtype=float) - m[:3, 3])
    length = _wall_length(doc, guid)
    anchor = None
    if length is not None:
        anchor = ("start", float(local[0])) if local[0] <= length / 2 else ("end", float(local[0] - length))
    return guid, local, anchor


def flat(a, b, at, origin, u, v):
    """2D (metres along u, v from origin): the ends a2, b2 and the line's offset from them
    (along the left normal of a→b)."""
    def to2(p):
        p = np.asarray(p, dtype=float) - origin
        return np.array((p @ u, p @ v))
    a2, b2, at2 = to2(a), to2(b), to2(at)
    d = b2 - a2
    n = np.array((-d[1], d[0])) / max(np.linalg.norm(d), 1e-12)
    return a2, b2, float((at2 - a2) @ n)


def placed(a, b, at, origin, u, v, direction=None):
    """A linear dimension in the view's 2D frame: (the point measured at each end, the dimension line's ends,
    the length) — p1, p2, l1, l2 (2,) and a float. Aligned (direction None): along a→b, its line through `at`;
    else along `direction` (world), each end's extension line square to it."""
    def to2(p):
        p = np.asarray(p, dtype=float) - origin
        return np.array((p @ u, p @ v))
    a2, b2, at2 = to2(a), to2(b), to2(at)
    if direction is None:
        d = b2 - a2
    else:
        direction = np.asarray(direction, dtype=float)
        d = np.array((direction @ u, direction @ v))
    norm = float(np.linalg.norm(d))
    d = d / norm if norm > 1e-12 else np.array((1.0, 0.0))
    n = np.array((-d[1], d[0]))
    l1 = a2 + n * float((at2 - a2) @ n)
    l2 = b2 + n * float((at2 - b2) @ n)
    return a2, b2, l1, l2, abs(float((b2 - a2) @ d))


def text(length, decimal=",", style=None):
    """'4,50' — metres with two decimals, as on an architect's plan; or as the project's dimension style says
    (0.124: in centimetres '450', in millimetres '4500', so many decimals; 0.398: rounded, with its unit, prefix and
    suffix, its millimetres raised — '2,47⁵')."""
    style = STYLE_DEFAULTS if style is None else style
    return dim_layout.label(length, style, decimal).plain


# (0.124) the project's dimension style — (0.398) every property of a dimension type: core/dim_layout's
STYLE_DEFAULTS = dim_layout.STYLE_DEFAULTS
STYLE_MARKS = dim_layout.MARKS
STYLE_UNITS = dim_layout.UNITS
STYLE_TEXTS = (1.8, 2.2, 2.5, 3.5)


def clean_style(style):
    """A dimension style read from a file or a dialog: its known keys, sensible values; the rest defaults — (0.193)
    and its dimension types, {name: their own style}, each made clean so (kept only when there are some)."""
    style = style or {}
    out = dim_layout.clean({k: v for k, v in style.items() if k != "types"})
    value = style.get("types")
    if isinstance(value, dict):
        types = {str(name).strip(): dim_layout.clean(s) for name, s in value.items()
                 if str(name).strip() and isinstance(s, dict)}
        if types:
            out["types"] = types
    return out


def piece_of(doc, dim, origin, u, v, project, decimal=","):
    """(0.398) A linear dimension as the drawings keep it: (point measured at each end, the line's two ends, its text,
    its type — a clean dict —, {"chain": its string, "label": core.dim_layout.Label}), the view's 2D frame; None for an
    angular one or one with no length."""
    if dim.vertex is not None:
        return None
    a, b = ends(doc, dim)
    p1, p2, l1, l2, length = placed(a, b, line_point(doc, dim), origin, u, v, dim.direction)
    if length < 1e-9:
        return None
    own = style_of(project, dim)
    note = dim.note or {}
    below = note.get("below", "")
    if not below and own.get("opening_height"):
        below = _opening_height(doc, dim, own, decimal)
    words = dim_layout.label(length, own, decimal, below=below, above=note.get("above", ""),
                             override=note.get("override"), eq=dim.eq, prefix=note.get("prefix", ""),
                             suffix=note.get("suffix", ""), shift=text_shift(dim))
    return p1, p2, l1, l2, words.plain, own, {"chain": dim.chain or "d{}".format(id(dim)), "label": words}


def text_shift(dim):
    """(0.402) Where its value was dragged to from its place: (dx, dy) in its view's 2D frame (m), or None."""
    raw = (dim.note or {}).get("shift")
    if not raw:
        return None
    try:
        dx, dy = (float(v) for v in str(raw).split(";"))
    except ValueError:
        return None
    return dx, dy


def _opening_height(doc, dim, style, decimal):
    """(0.398) The height of the door or window whose width a dimension measures (both its ends on it), as its type
    writes it — else ""."""
    refs = [r for r in dim.refs if r is not None]
    if len(refs) != 2 or refs[0][0] != refs[1][0]:
        return ""
    obj = doc.get(refs[0][0])
    if obj is None or getattr(obj, "ifc_class", None) not in ("IfcDoor", "IfcWindow"):
        return ""
    try:
        height = float(doc.ifc.filling_state(refs[0][0])["height"])
    except Exception:
        return ""
    return dim_layout.label(height, dict(style, prefix="", suffix="", unit_symbol=False), decimal).plain


def style_of(project, dim):
    """(0.193) The style a dimension is drawn with: its type's (a name among the project style's "types"), else
    the project's."""
    project = clean_style(project)
    found = (project.get("types") or {}).get(getattr(dim, "style", None))
    if found is not None:
        return dict(found)
    return {k: v for k, v in project.items() if k != "types"}


def type_names(project):
    """(0.193) The project's dimension types, by name."""
    return sorted((clean_style(project).get("types") or {}).keys(), key=str.lower)


class SetDimensionTypeOf:
    """(0.193) Dimensions given a dimension type (None: the project's style), one undo step."""

    def __init__(self, dims, name, label):
        self.dims, self.name, self.label = list(dims), name, label
        self.before = [d.style for d in self.dims]

    def do(self, doc):
        for d in self.dims:
            d.style = self.name
        doc.dimensions_changed()

    def undo(self, doc):
        for d, s in zip(self.dims, self.before):
            d.style = s
        doc.dimensions_changed()


class SetDimensionStyle:
    """The project's dimension style changed, one undo step: every dimension is shown and printed again."""

    def __init__(self, before, after, label, renamed=None):
        self.before, self.after, self.label = dict(before), dict(after), label
        self.renamed = dict(renamed or {})          # (0.398) {old type name: new}: its dimensions keep their type
        self._moved = []

    def do(self, doc):
        doc.dim_style = dict(self.after)
        self._moved = []
        for old, new in self.renamed.items():
            for d in doc.dimensions:
                if d.style == old:
                    d.style = new
                    self._moved.append((d, old))
        doc.dimensions_changed()

    def undo(self, doc):
        doc.dim_style = dict(self.before)
        for d, old in self._moved:
            d.style = old
        doc.dimensions_changed()


def _ref_json(r):
    if r is None:
        return None
    out = [r[0], [float(c) for c in r[1]], list(r[2]) if len(r) > 2 and r[2] is not None else None]
    if len(r) > 3 and r[3]:                          # (0.399) the wall's line it is on
        out.append(str(r[3]))
    return out


def _ref_back(r):
    if r is None:
        return None
    back = (str(r[0]), np.asarray(r[1], dtype=float), (str(r[2][0]), float(r[2][1])) if len(r) > 2 and r[2] else None)
    return back + (str(r[3]),) if len(r) > 3 and r[3] else back


def to_dict(dim):
    """For the .arqbim file (saved with the model origin the points are relative to)."""
    out = {"view": list(dim.view), "a": [float(c) for c in dim.a], "b": [float(c) for c in dim.b],
           "at": [float(c) for c in dim.at], "refs": [_ref_json(r) for r in dim.refs], "tag": dim.tag,
           "at_ref": [dim.at_ref[0], [float(c) for c in dim.at_ref[1]]] if dim.at_ref is not None else None}
    if dim.vertex is not None:                       # (an angular one, 0.122)
        out["vertex"] = [float(c) for c in dim.vertex]
        out["vertex_ref"] = _ref_json(dim.vertex_ref)
    if dim.direction is not None:                    # (along a direction, 0.123)
        out["direction"] = [float(c) for c in dim.direction]
    if dim.style:                                    # (its dimension type, 0.193)
        out["style"] = dim.style
    if dim.chain:                                    # (0.398) its string, its own words, «IG»
        out["chain"] = dim.chain
    if dim.note:
        out["note"] = {k: str(v) for k, v in dim.note.items() if v}
    if dim.eq:
        out["eq"] = True
    return out


def from_dict(data, shift):
    """Read back; `shift` moves the points if the model origin is not the one they were saved with."""
    try:
        refs = [_ref_back(r) for r in data.get("refs", [None, None])]
        at_ref = data.get("at_ref")
        vertex = data.get("vertex")
        return Dimension(tuple(data["view"]), np.asarray(data["a"], dtype=float) + shift,
                         np.asarray(data["b"], dtype=float) + shift, np.asarray(data["at"], dtype=float) + shift,
                         (refs + [None, None])[:2], data.get("tag"),
                         (str(at_ref[0]), np.asarray(at_ref[1], dtype=float)) if at_ref else None,
                         np.asarray(vertex, dtype=float) + shift if vertex else None,
                         _ref_back(data.get("vertex_ref")),
                         np.asarray(data["direction"], dtype=float) if data.get("direction") else None,
                         str(data["style"]) if data.get("style") else None,
                         str(data["chain"]) if data.get("chain") else None,
                         {str(k): str(v) for k, v in data["note"].items() if v} if isinstance(data.get("note"), dict)
                         and data["note"] else None, bool(data.get("eq", False)))
    except (KeyError, TypeError, ValueError, IndexError, AttributeError):
        return None
