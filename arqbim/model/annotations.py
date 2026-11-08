"""Drawing in the views (Phase 5, step 1): lines, polylines, rectangles, circles, arcs, filled regions with a
hatch and texts drawn in a view — the plan of a storey, a section, an elevation — and shown there only, on screen
and on paper, as its dimensions are (model/dimensions.py).

Not IFC: kept with the views and the dimensions in the file beside it (as the owner decided for the dimensions,
2026-10-21; IfcAnnotation may come later, as an export).

Each one keeps the points it was drawn with, in the program's coordinates (on the view's paper); what is drawn
is worked out in the view's 2D frame (origin, u, v): a line [a, b]; a polyline [p…] (open); a rectangle [two
opposite corners]; a circle [centre, a point on it]; an arc [start, end, a point it passes through]; a region
[p…] (closed); a text [where it starts]."""

import math
from dataclasses import dataclass, field

import numpy as np

from ..core import arcs

KINDS = ("line", "polyline", "rectangle", "circle", "arc", "region", "text", "spot", "level",   # (spot: 0.156;
         "keynote")                                                    # level: 0.192; keynote: 0.194)
SPOT_MARK = 0.12            # m: half a spot height's cross (its text worked out when drawn: model/spots.py)
LEVEL_MARK = 0.15           # m: (0.192) a level mark's radius — a circle quartered, two quarters filled
MARKS = ("spot", "level")   # the ones whose text is the model's height there
HATCHES = ("diagonal", "cross", "solid", "none")      # a region on paper: lines at 45°, crossed, filled grey, empty
# (0.450) …and Revit's masking region: filled white, its outline not on paper — what is under it is hidden
HATCHES += ("mask",)
TEXT_SIZE = 2.5             # mm on paper: a text's height (as an architect's lettering)
HATCH_SPACING = 1.5         # mm on paper between a hatch's lines
MIN_SIZE = 0.005            # m


@dataclass(eq=False)
class Annotation:
    view: tuple                    # ("plan", storey GlobalId) | ("section", name) | ("elevation", side)
    kind: str                      # one of KINDS
    points: list                   # np.ndarray (3,) each, as drawn (see the module's docstring)
    text: str = ""                 # a text's words
    hatch: str = "diagonal"        # a region's (HATCHES)
    size: float = TEXT_SIZE        # a text's height, mm on paper
    extra: dict = field(default_factory=dict)   # (room for what comes later: line types, colours…)


def to2(points, origin, u, v):
    """Points (3D, program coordinates) in the view's 2D frame: (N, 2) metres along u, v."""
    p = np.asarray(points, dtype=float).reshape(-1, 3) - np.asarray(origin, dtype=float)
    return np.column_stack((p @ np.asarray(u, dtype=float), p @ np.asarray(v, dtype=float)))


def shape(ann, origin, u, v):
    """What an annotation draws, in the view's 2D frame: ([(N, 2) array, closed?]…), or [] (a text, or too
    small). A circle and an arc as many short segments (3° each)."""
    p = to2(ann.points, origin, u, v)
    if ann.kind == "spot" and len(p):                  # (0.156) a cross on the point
        c, d = p[0], SPOT_MARK
        return [(np.array((c - (d, 0.0), c + (d, 0.0))), False), (np.array((c - (0.0, d), c + (0.0, d))), False)]
    if ann.kind == "level" and len(p):                 # (0.192) a circle on the point, quartered
        c, r = p[0], LEVEL_MARK
        return [(np.array(arcs.arc_points(c, r, 0.0, arcs.FULL)), True),
                (np.array((c - (r, 0.0), c + (r, 0.0))), False), (np.array((c - (0.0, r), c + (0.0, r))), False)]
    if ann.kind == "text" or len(p) < 2:
        return []
    if ann.kind == "keynote":                          # (0.194) its leader (its box: keynote_box, its text's size)
        return [(p[:2], False)] if np.linalg.norm(p[1] - p[0]) >= MIN_SIZE else []
    if ann.kind == "line":
        return [(p[:2], False)] if np.linalg.norm(p[1] - p[0]) >= MIN_SIZE else []
    if ann.kind == "polyline":
        return [(bulged(p, bulges_of(ann), False), False)]
    if ann.kind == "region":
        return [(bulged(p, bulges_of(ann), True), True)] if len(p) >= 3 else []
    if ann.kind == "rectangle":
        (x0, y0), (x1, y1) = p[0], p[1]
        if abs(x1 - x0) < MIN_SIZE or abs(y1 - y0) < MIN_SIZE:
            return []
        return [(np.array(((x0, y0), (x1, y0), (x1, y1), (x0, y1))), True)]
    if ann.kind == "circle":
        r = float(np.linalg.norm(p[1] - p[0]))
        if r < MIN_SIZE:
            return []
        return [(np.array(arcs.arc_points(p[0], r, 0.0, arcs.FULL)), True)]
    if ann.kind == "arc" and len(p) >= 3:
        found = arcs.arc_through(p[0], p[1], p[2])
        if found is None:
            return [(p[:2], False)]                    # (three points in a line: the straight line)
        centre, r, start, sweep = found
        return [(np.array(arcs.arc_points(centre, r, start, sweep)), False)]
    return []


def bulges_of(ann):
    """(0.455) A polyline's / region's sides' bulges — side k from point k to the next: 0 straight, else an arc, DXF's
    bulge (tan of a quarter of its angle, positive turning counter-clockwise on the view's paper). Kept in `extra`,
    unchanged when it is moved or turned; [0…] when there are none (or no longer one per side)."""
    n = len(ann.points)
    sides = n if ann.kind == "region" else n - 1
    kept = list(ann.extra.get("bulges") or []) if isinstance(ann.extra, dict) else []
    return [float(b) for b in kept] if len(kept) == max(sides, 0) else [0.0] * max(sides, 0)


def bulged(p, bulges, closed):
    """(0.455) The points (N, 2) with the sides that are arcs (their bulges) in pieces."""
    p = np.asarray(p, dtype=float)
    if not any(abs(b) > 1e-12 for b in bulges):
        return p
    out = []
    n = len(p)
    for k in range(n if closed else n - 1):
        a, b = p[k], p[(k + 1) % n]
        out.append(a)
        bulge = bulges[k] if k < len(bulges) else 0.0
        chord = float(np.linalg.norm(b - a))
        if abs(bulge) < 1e-12 or chord < 1e-12:
            continue
        right = np.array(((b - a)[1], -(b - a)[0])) / chord
        through = (a + b) / 2 + right * (bulge * chord / 2)          # (its middle, the sagitta off the chord)
        found = arcs.arc_through(a, b, through)
        if found is None:
            continue
        centre, r, start, sweep = found
        out += [np.asarray(q, dtype=float) for q in arcs.arc_points(centre, r, start, sweep)[1:-1]]
    if not closed:
        out.append(p[-1])
    return np.array(out, dtype=float)


def region_from_loop(loop):
    """(0.456) A region's points (2D) and bulges from an outline drawn (core/outline_loops: a circle's arcs, rounded
    corners — bulges; an ellipse's Bézier quarters — in pieces)."""
    from ..core import curves
    corners, sides = loop
    pts, bulges = [], []
    n = len(corners)
    for k in range(n):
        p, q = np.asarray(corners[k], dtype=float), np.asarray(corners[(k + 1) % n], dtype=float)
        side = sides[k] if k < len(sides) else None
        pts.append(p)
        if side and side.get("kind") == "arc":
            chord = float(np.linalg.norm(q - p))
            m = np.asarray(side["through"], dtype=float)
            right = np.array(((q - p)[1], -(q - p)[0])) / max(chord, 1e-12)
            sag = float((m - (p + q) / 2) @ right)                  # (positive: to the right, counter-clockwise)
            bulges.append(2.0 * sag / chord if chord > 1e-12 else 0.0)
        elif side:
            pieces = curves.side_points(p, q, side)[:-1]           # (a curve: in pieces, straight)
            bulges.append(0.0)
            for r in pieces:
                pts.append(np.asarray(r, dtype=float))
                bulges.append(0.0)
        else:
            bulges.append(0.0)
    return pts, bulges


def corner_fillet(ann, side_a, keep_a, side_b, keep_b, radius, origin, u, v):
    """(0.455, the owner: «isso também deve ser colocado na região, máscara etc») Revit's «Fillet Arc» on a drawing:
    the corner between the sides side_a and side_b (next to each other, both straight) of a region, a mask, a
    polyline — or a rectangle, made a region with no hatch — rounded by an arc of `radius` tangent to both (each kept
    on the side of its keep_* point, 2D). (kind, points (3D), bulges) — ValueError("not_corner" | "parallel" |
    "too_big")."""
    from ..core.fillet import fillet
    kind, pts3 = ann.kind, [np.asarray(q, dtype=float) for q in ann.points]
    if kind == "rectangle":                              # (its four corners, as a region's)
        (x0, y0), (x1, y1) = to2(pts3[:2], origin, u, v)
        o, uu, vv = (np.asarray(x, dtype=float) for x in (origin, u, v))
        pts3 = [o + uu * x + vv * y for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        kind = "region"
        bulges = [0.0] * 4
    elif kind in ("region", "polyline"):
        bulges = bulges_of(ann)
    else:
        raise ValueError("not_corner")
    n = len(pts3)
    closed = kind == "region"
    if side_a == side_b:
        raise ValueError("not_corner")
    if (side_a + 1) % n == side_b:                       # (a's end is b's start: the corner between them)
        first, second, corner = side_a, side_b, side_b
    elif (side_b + 1) % n == side_a:
        first, second, corner = side_b, side_a, side_a
        keep_a, keep_b = keep_b, keep_a
    else:
        raise ValueError("not_corner")
    if not closed and corner == 0:
        raise ValueError("not_corner")
    if bulges[first] or bulges[second]:
        raise ValueError("not_corner")                   # (a side already an arc there)
    p = to2(pts3, origin, u, v)
    f = fillet((p[first], p[corner]), keep_a, (p[(second + 1) % n], p[corner]), keep_b, radius=float(radius))
    if f is None:
        raise ValueError("parallel")
    reach = float(np.linalg.norm(f.tangents[0] - f.cross))
    if any(reach > room - 1e-6 for room in f.room):
        raise ValueError("too_big")
    o, uu, vv = (np.asarray(x, dtype=float) for x in (origin, u, v))
    to3 = lambda q: o + uu * float(q[0]) + vv * float(q[1])     # noqa: E731
    new_pts = pts3[:corner] + [to3(f.tangents[0]), to3(f.tangents[1])] + pts3[corner + 1:]
    new_bulges = bulges[:corner] + [math.tan(f.sweep / 4.0)] + bulges[corner:]
    return kind, new_pts, new_bulges


def lines_fillet(ann_a, keep_a, ann_b, keep_b, radius, origin, u, v):
    """(0.455) The fillet arc between two lines drawn in a view: each trimmed / stretched to where the arc touches it
    (kept on the side of its keep_* point, 2D), and the arc an arc of its own ([start, end, a point on it], 3D).
    (points of a, points of b, the arc's points) — ValueError("parallel" | "too_big")."""
    from ..core.fillet import fillet
    pa, pb = to2(ann_a.points[:2], origin, u, v), to2(ann_b.points[:2], origin, u, v)
    f = fillet((pa[0], pa[1]), keep_a, (pb[0], pb[1]), keep_b, radius=float(radius))
    if f is None:
        raise ValueError("parallel")
    reach = float(np.linalg.norm(f.tangents[0] - f.cross))
    if any(reach > room - 1e-6 for room in f.room):
        raise ValueError("too_big")
    o, uu, vv = (np.asarray(x, dtype=float) for x in (origin, u, v))
    to3 = lambda q: o + uu * float(q[0]) + vv * float(q[1])     # noqa: E731
    out = []
    for ann, end, tangent in ((ann_a, f.ends[0], f.tangents[0]), (ann_b, f.ends[1], f.tangents[1])):
        pts = [np.asarray(q, dtype=float) for q in ann.points[:2]]
        pts[1 if end == "end" else 0] = to3(tangent)
        out.append(pts)
    middle = arcs.point_at(f.centre, f.radius, f.start + f.sweep / 2)
    return out[0], out[1], [to3(f.tangents[0]), to3(f.tangents[1]), to3(middle)]


def level_fills(ann, origin, u, v):
    """(0.192) A level mark's two filled quarters — the upper right and the lower left, as drawn in Portugal — as
    polygons in the view's 2D frame; [] for the other kinds."""
    if ann.kind != "level" or not ann.points:
        return []
    c = to2(ann.points[:1], origin, u, v)[0]
    out = []
    for start in (0.0, math.pi):
        arc = arcs.arc_points(c, LEVEL_MARK, start, math.pi / 2)
        out.append(np.array([tuple(c)] + [tuple(q) for q in arc]))
    return out


def keynote_box(start, tip, text, size, m_per_mm):
    """(0.194) A keynote tag's box round its code written `size` mm high, `m_per_mm` metres of the drawing per
    millimetre of paper: hung by the middle of a side on the leader's tip (2D), on the side the leader goes to (from
    its start). Its four corners and its middle (where the code is written)."""
    h = size * 2.0 * m_per_mm
    w = (max(len(text), 1) * 0.62 * size + size * 1.4) * m_per_mm
    way = 1.0 if float(tip[0]) >= float(start[0]) else -1.0
    cx, cy = float(tip[0]) + way * w / 2, float(tip[1])
    corners = np.array(((cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2),
                        (cx - w / 2, cy + h / 2)))
    return corners, np.array((cx, cy))


def mark_text_at(ann, origin, u, v):
    """Where a spot's / level mark's height is written: beside its symbol, up and to the right."""
    c = to2(ann.points[:1], origin, u, v)[0]
    return c + (LEVEL_MARK * 1.25 if ann.kind == "level" else SPOT_MARK * 1.2)


def segments(ann, origin, u, v):
    """The annotation's lines as (K, 2, 2) in the view's 2D frame."""
    out = []
    for pts, closed in shape(ann, origin, u, v):
        ring = np.vstack((pts, pts[:1])) if closed else pts
        out += [(ring[k], ring[k + 1]) for k in range(len(ring) - 1)]
    return np.array(out, dtype=float).reshape(-1, 2, 2)


def hatch_lines(ring, hatch, spacing):
    """A region's hatch inside `ring` (2D), `spacing` apart (metres in the model): (K, 2, 2); [] for solid
    / none (those are filled, or not, on paper)."""
    from shapely.geometry import LineString, Polygon
    angles = {"diagonal": (45.0,), "cross": (45.0, -45.0)}.get(hatch, ())
    poly = Polygon(ring).buffer(0)
    if poly.is_empty or not angles or spacing <= 0:
        return np.zeros((0, 2, 2))
    x0, y0, x1, y1 = poly.bounds
    c = np.array(((x0 + x1) / 2, (y0 + y1) / 2))
    half = math.hypot(x1 - x0, y1 - y0) / 2 + spacing
    out = []
    for a in angles:
        d = np.array((math.cos(math.radians(a)), math.sin(math.radians(a))))
        n = np.array((-d[1], d[0]))
        for k in range(-int(half / spacing), int(half / spacing) + 1):
            q = c + n * (k * spacing)
            cut = poly.intersection(LineString([q - d * half, q + d * half]))
            for g in getattr(cut, "geoms", [cut]):
                if g.geom_type == "LineString" and g.length > 1e-9:
                    xy = np.array(g.coords)
                    out += [(xy[i], xy[i + 1]) for i in range(len(xy) - 1)]
    return np.array(out, dtype=float).reshape(-1, 2, 2)


def area(ann, origin, u, v):
    """A closed one's area (m²), else 0."""
    found = shape(ann, origin, u, v)
    if not found or not found[0][1]:
        return 0.0
    x, y = found[0][0][:, 0], found[0][0][:, 1]
    return abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))) / 2


class AddAnnotation:
    def __init__(self, ann, label):
        self.ann, self.label = ann, label

    def do(self, doc):
        doc.annotations.append(self.ann)
        doc.dimensions_changed()

    def undo(self, doc):
        doc.annotations.remove(self.ann)
        doc.dimensions_changed()


class AddAnnotations:
    """Several at once (copies), one undo step."""

    def __init__(self, anns, label):
        self.anns, self.label = list(anns), label

    def do(self, doc):
        doc.annotations.extend(self.anns)
        doc.dimensions_changed()

    def undo(self, doc):
        for a in self.anns:
            doc.annotations.remove(a)
        doc.dimensions_changed()


def moved_copy(ann, delta):
    """A copy of an annotation, moved by delta."""
    return Annotation(ann.view, ann.kind, [np.asarray(p, dtype=float) + np.asarray(delta, dtype=float)
                                           for p in ann.points], ann.text, ann.hatch, ann.size, dict(ann.extra))


class RemoveAnnotations:
    def __init__(self, anns, label):
        self.anns, self.label = list(anns), label
        self._where = []

    def do(self, doc):
        self._where = [(doc.annotations.index(a), a) for a in self.anns if a in doc.annotations]
        for _k, a in self._where:
            doc.annotations.remove(a)
        doc.dimensions_changed()

    def undo(self, doc):
        for k, a in sorted(self._where, key=lambda item: item[0]):
            doc.annotations.insert(k, a)
        doc.dimensions_changed()


class MoveAnnotations:
    """Annotations moved by a vector (all their points), one undo step."""

    def __init__(self, anns, delta, label):
        self.anns, self.delta, self.label = list(anns), np.asarray(delta, dtype=float), label

    def _shift(self, doc, d):
        for a in self.anns:
            a.points = [np.asarray(p, dtype=float) + d for p in a.points]
        doc.dimensions_changed()

    def do(self, doc):
        self._shift(doc, self.delta)

    def undo(self, doc):
        self._shift(doc, -self.delta)


FIELDS = ("points", "text", "size", "hatch", "extra")


class EditAnnotation:
    """(0.191) One annotation changed — its points (a grip moved), its words, its size, its hatch, its extra (its
    angle, its line type and pen) —, one undo step."""

    def __init__(self, ann, label, **changes):
        unknown = set(changes) - set(FIELDS)
        if unknown:
            raise KeyError(sorted(unknown)[0])
        self.ann, self.label = ann, label
        self.after = {k: _copied(v) for k, v in changes.items()}
        self.before = {k: _copied(getattr(ann, k)) for k in changes}

    def _put(self, doc, values):
        for k, v in values.items():
            setattr(self.ann, k, _copied(v))
        doc.dimensions_changed()

    def do(self, doc):
        self._put(doc, self.after)

    def undo(self, doc):
        self._put(doc, self.before)


def _copied(value):
    if isinstance(value, list):
        return [np.array(p, dtype=float) for p in value]
    if isinstance(value, dict):
        return dict(value)
    return value


def angle(ann):
    """A text's angle (degrees, counter-clockwise in its view's paper; 0: level)."""
    return float(ann.extra.get("angle", 0.0) or 0.0)


def rotated_points(points, centre, normal, degrees):
    """Points turned `degrees` about the axis through `centre` along the view's `normal` (towards the viewer: the
    turn is counter-clockwise as seen on the paper)."""
    k = np.asarray(normal, dtype=float) / np.linalg.norm(normal)
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    out = []
    for p in points:
        w = np.asarray(p, dtype=float) - centre
        out.append(centre + w * c + np.cross(k, w) * s + k * float(np.dot(k, w)) * (1 - c))
    return out


class RotateAnnotations:
    """(0.191) Annotations turned about a point of their view's paper (the Rotate tool): their points; a text's
    angle too. One undo step."""

    def __init__(self, anns, centre, normal, degrees, label):
        self.anns, self.label = list(anns), label
        self.centre, self.normal, self.degrees = np.asarray(centre, dtype=float), np.asarray(normal, dtype=float), \
            float(degrees)

    def _turn(self, doc, degrees):
        for a in self.anns:
            a.points = rotated_points(a.points, self.centre, self.normal, degrees)
            if a.kind == "text":
                a.extra = dict(a.extra, angle=(angle(a) + degrees + 180.0) % 360.0 - 180.0)
        doc.dimensions_changed()

    def do(self, doc):
        self._turn(doc, self.degrees)

    def undo(self, doc):
        self._turn(doc, -self.degrees)


def to_dict(ann):
    """For the file beside the IFC (saved with the model origin the points are relative to)."""
    out = {"view": list(ann.view), "kind": ann.kind, "points": [[float(c) for c in p] for p in ann.points]}
    if ann.kind == "text":
        out.update(text=ann.text, size=float(ann.size))
    if ann.kind == "region":
        out["hatch"] = ann.hatch
    if ann.extra:
        out["extra"] = dict(ann.extra)
    return out


def from_dict(data, shift):
    """Read back; `shift` moves the points if the model origin is not the one they were saved with."""
    try:
        kind = str(data["kind"])
        if kind not in KINDS:
            return None
        return Annotation(tuple(data["view"]), kind,
                          [np.asarray(p, dtype=float) + shift for p in data["points"]],
                          str(data.get("text", "")), str(data.get("hatch", "diagonal")),
                          float(data.get("size", TEXT_SIZE)), dict(data.get("extra") or {}))
    except (KeyError, TypeError, ValueError):
        return None
