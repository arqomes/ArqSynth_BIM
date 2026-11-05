"""The analytical model of a structure (0.163, Phase 9, step 1), from the physical one — as Revit's analytical
model: each column its axis from its base to its top, each beam its axis at its top (the floor's level, where it
meets the columns and the slab), their ends joined in nodes (a beam's end on a column's axis; a beam resting on
another — it splits it there); the column bases on footings fixed supports; the slabs panels on their level. Then
the model checked, its problems listed (taken over from the ArqSynth Modeler's validation, its rules and
tolerances): what is missing or wrong before any calculation.

Pure numpy: plan points and heights in metres. The IFC (IfcStructuralAnalysisModel) is ifc/structural.py's."""

import math
from dataclasses import dataclass, field

import numpy as np

TOL_NODE = 0.02                 # m: points this near are one node
TOL_XY_SUPPORT = 0.40           # m: a beam's end this near a column's axis (in plan) rests on it
TOL_XY_FOOTING = 0.60           # m: a column's base this near a footing's middle stands on it
TOL_Z_SUPPORT = 0.50            # m: …at heights this near
TOL_ON_BEAM = 0.30              # m: a beam's end this near another beam's axis rests on it
TOL_Z_LEVEL = 0.15              # m: a column's base this near a storey's level is on it
TOL_GROUND = 0.30               # m: a base this near the lowest level is at the foundations
TOL_DUPLICATE = 0.05

ERROR, WARNING, INFO = "erro", "aviso", "info"


@dataclass
class Column:
    guid: str
    centre: tuple               # (x, y)
    base: float
    top: float
    size: tuple                 # (b, h) m — or (d, d) round
    material: str = "concrete"
    shape: str = "rect"         # (0.227) "rect" | "circle" | "L" | "T" (b × h outside, IFC's profiles)
    web: float = 0.0            # …an L's or a T's legs' thickness (m)
    x_dir: tuple = (1.0, 0.0)   # …its own x in plan (b along it)


@dataclass
class Beam:
    guid: str
    start: tuple                # (x, y)
    end: tuple
    top: float
    size: tuple                 # (b, h) m
    material: str = "concrete"


@dataclass
class Footing:
    guid: str
    centre: tuple
    top: float
    size: tuple                 # (length, width) m
    depth: float = 0.5
    kind: str = "pad"           # (0.228) "pad" | "strip" (under a wall) | "cap" (on piles) | (0.250) "combined"
    x_dir: tuple = (1.0, 0.0)   # …its length's direction in plan
    piles: tuple = ()           # …a cap's piles: ((x, y) from its middle along its x / y, …)
    pile_d: float = 0.0         # …their diameter (m)
    wall: str = ""              # …a strip's wall (its GlobalId)
    wall_t: float = 0.0         # …its thickness (m)
    line_load: float = 0.0      # …kN/m on a strip: its wall's weight (characteristic)
    columns: tuple = ()         # (0.250) …a combined footing's two columns: ((x, y) plan, …)


@dataclass
class Panel:
    guid: str
    outline: list               # [(x, y)]
    level: float                # its top
    thickness: float


@dataclass
class Wall:
    """(0.335) A load-bearing wall (Pset_WallCommon.LoadBearing): one storey of it, its plane — its axis in plan, its
    base and top —, its thickness all told and its load-bearing layer's (EC6's t: the block, not the plaster), its
    material, its openings ((from, to) along its axis from its start, (bottom, top) heights)."""
    guid: str
    start: tuple                # (x, y)
    end: tuple
    base: float
    top: float
    thickness: float            # m, all its layers
    core: float = 0.0           # m, its load-bearing layer (0: all of it)
    material: str = "masonry"   # "masonry" | "concrete"
    openings: tuple = ()        # ((s0, s1, z0, z1), …) m
    masonry: tuple = None       # (0.346) its type's own masonry (core/ec6: units, group, fb, mortar); None: the project's

    @property
    def length(self):
        return math.hypot(self.end[0] - self.start[0], self.end[1] - self.start[1])

    @property
    def t(self):
        """Its load-bearing thickness."""
        return self.core if self.core > 0 else self.thickness


@dataclass
class Member:
    id: str                     # "<physical GlobalId>" or "<GlobalId>/2"… when split
    guid: str                   # the physical element's
    kind: str                   # "column" | "beam"
    n1: int
    n2: int
    size: tuple
    material: str
    shape: str = "rect"         # (0.227) a column's section (Column.shape), its legs, its own x in plan
    web: float = 0.0
    x_dir: tuple = (1.0, 0.0)


@dataclass
class Issue:
    code: str
    severity: str               # ERROR / WARNING / INFO
    guids: tuple                # the elements it is about


@dataclass
class AnalyticalModel:
    nodes: list = field(default_factory=list)          # [(x, y, z)]
    members: list = field(default_factory=list)        # [Member]
    supports: dict = field(default_factory=dict)       # node -> "fixed" | "pinned" | (0.335) "wall" (pinned on one)
    panels: list = field(default_factory=list)         # [Panel]
    issues: list = field(default_factory=list)         # [Issue]
    walls: list = field(default_factory=list)          # (0.335) [Wall] load-bearing
    # (0.335) what each wall stands on: guid -> ("footing", its GlobalId) | ("wall", [the walls under it]) |
    # ("ground", None) | ("slab", its GlobalId)
    wall_bases: dict = field(default_factory=dict)
    on_walls: dict = field(default_factory=dict)       # (0.335) node -> the wall (GlobalId) it rests on

    def node(self, p, tol=TOL_NODE):
        p = (float(p[0]), float(p[1]), float(p[2]))
        for k, q in enumerate(self.nodes):
            if abs(q[0] - p[0]) < tol and abs(q[1] - p[1]) < tol and abs(q[2] - p[2]) < tol:
                return k
        self.nodes.append(p)
        return len(self.nodes) - 1

    def length(self, member):
        return float(np.linalg.norm(np.subtract(self.nodes[member.n2], self.nodes[member.n1])))


def _xy(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _stands_on(c, f):
    """A column stands on a footing: its middle near the footing's (TOL_XY_FOOTING) — (0.249) or within its plan
    (a combined footing under two columns, its middle between them)."""
    if _xy(c.centre, f.centre) < TOL_XY_FOOTING:
        return True
    x = f.x_dir
    n = math.hypot(x[0], x[1]) or 1.0
    ux, uy = x[0] / n, x[1] / n
    dx, dy = c.centre[0] - f.centre[0], c.centre[1] - f.centre[1]
    u, v = dx * ux + dy * uy, -dx * uy + dy * ux
    return abs(u) <= f.size[0] / 2 + 1e-6 and abs(v) <= f.size[1] / 2 + 1e-6


def _along(p, a, b):
    """(distance in plan from p to the segment a–b, where along it 0…1)."""
    ab = np.subtract(b, a)[:2]
    l2 = float(ab @ ab)
    if l2 < 1e-12:
        return _xy(p, a), 0.0
    t = float(np.clip(np.subtract(p, a)[:2] @ ab / l2, 0.0, 1.0))
    q = np.asarray(a, dtype=float)[:2] + ab * t
    return float(np.hypot(*(np.asarray(p, dtype=float)[:2] - q))), t


def _wall_near(p, z, walls, reach=TOL_XY_SUPPORT):
    """(0.335) The load-bearing wall whose top is at height z (within TOL_Z_SUPPORT) and whose axis passes within
    `reach` of the plan point p (the nearest), or None."""
    best = None
    for w in walls:
        if abs(w.top - z) > TOL_Z_SUPPORT:
            continue
        d, _t = _along(tuple(p[:2]), w.start, w.end)
        if d < max(reach, w.thickness / 2.0) and (best is None or d < best[0]):
            best = (d, w)
    return best[1] if best is not None else None


def _in_line(a, b, slack=0.05):
    """(0.335) Two walls along one line in plan (parallel within 5°, their axes within half the thicker one), and how
    long they run together (m)."""
    da = np.subtract(a.end, a.start)
    db = np.subtract(b.end, b.start)
    la, lb = float(np.hypot(*da)), float(np.hypot(*db))
    if la < 1e-6 or lb < 1e-6:
        return 0.0
    ua, ub = da / la, db / lb
    if abs(float(ua[0] * ub[1] - ua[1] * ub[0])) > math.sin(math.radians(5.0)):
        return 0.0
    off = abs(float(np.subtract(b.start, a.start) @ np.array((-ua[1], ua[0]))))
    if off > max(a.thickness, b.thickness) / 2.0 + slack:
        return 0.0
    s0, s1 = sorted((float(np.subtract(b.start, a.start) @ ua), float(np.subtract(b.end, a.start) @ ua)))
    return max(0.0, min(s1, la) - max(s0, 0.0))


def walls_under(wall, walls, least=0.10):
    """(0.335) The walls a load-bearing wall stands on: in line with it, their top at its base, running together
    `least` or more — [(the wall under, how long they share)]."""
    return [(o, run) for o in walls if o is not wall and abs(o.top - wall.base) <= TOL_Z_SUPPORT
            for run in [_in_line(wall, o)] if run >= least]


def _wall_bases(model, walls, footings, panels, low):
    """(0.335) What each wall stands on (model.wall_bases), its problems told."""
    from shapely.geometry import LineString, Polygon
    for w in walls:
        foot = next((f for f in footings if f.kind == "strip" and -0.10 <= w.base - f.top <= TOL_Z_SUPPORT
                     and (f.wall == w.guid or _strip_under(f, w))), None)
        under = walls_under(w, walls)
        if foot is not None:
            model.wall_bases[w.guid] = ("footing", foot.guid)
        elif under:
            model.wall_bases[w.guid] = ("wall", [o.guid for o, _run in under])
        elif w.base <= low + TOL_GROUND:
            model.wall_bases[w.guid] = ("ground", None)
            model.issues.append(Issue("wall_no_footing", WARNING, (w.guid,)))
        else:
            line = LineString((w.start, w.end))
            slab = next((p for p in panels if abs(p.level - w.base) <= TOL_Z_SUPPORT
                         and Polygon(p.outline).buffer(0.30).intersects(line)), None)
            if slab is not None:
                model.wall_bases[w.guid] = ("slab", slab.guid)
                model.issues.append(Issue("wall_on_slab", WARNING, (w.guid, slab.guid)))
            else:
                model.issues.append(Issue("wall_hanging", ERROR, (w.guid,)))


def _strip_under(footing, wall):
    """(0.335) A strip footing along a wall: its middle on the wall's axis (in plan), its length along it."""
    d, t = _along(tuple(footing.centre[:2]), wall.start, wall.end)
    if d > max(wall.thickness, 0.30) or not 0.0 <= t <= 1.0:
        return False
    x = np.asarray(footing.x_dir, dtype=float)
    along = np.subtract(wall.end, wall.start)
    n = float(np.linalg.norm(along)) * float(np.linalg.norm(x))
    return n > 1e-9 and abs(float(along @ x)) / n > math.cos(math.radians(10.0))


def build(columns=(), beams=(), footings=(), panels=(), levels=(), walls=()):
    """The analytical model of these elements, checked — (0.335) with the load-bearing walls (Wall)."""
    model = AnalyticalModel(panels=list(panels))
    issues = model.issues
    columns, beams, footings = list(columns), list(beams), list(footings)
    for w in walls:                                     # (0.335) the load-bearing walls: a size each
        if w.length <= 1e-6 or w.top - w.base <= 1e-6 or w.t <= 0:
            issues.append(Issue("wall_no_size", ERROR, (w.guid,)))
        elif w.material != "masonry":
            issues.append(Issue("wall_concrete", INFO, (w.guid,)))
    walls = [w for w in walls if w.length > 1e-6 and w.top - w.base > 1e-6 and w.t > 0]
    model.walls = walls
    # sizes and materials first (an element with none is left out of the model)
    for c in columns:
        if c.top - c.base <= 1e-6:
            issues.append(Issue("column_no_height", ERROR, (c.guid,)))
        elif min(c.size) <= 0:
            issues.append(Issue("column_no_section", ERROR, (c.guid,)))
    for b in beams:
        if _xy(b.start, b.end) <= 1e-6:
            issues.append(Issue("beam_no_length", ERROR, (b.guid,)))
        elif min(b.size) <= 0:
            issues.append(Issue("beam_no_section", ERROR, (b.guid,)))
    for e in columns + beams:
        if e.material not in ("concrete",):
            issues.append(Issue("not_concrete", WARNING, (e.guid,)))
    columns = [c for c in columns if c.top - c.base > 1e-6 and min(c.size) > 0]
    beams = [b for b in beams if _xy(b.start, b.end) > 1e-6 and min(b.size) > 0]
    low = min(levels) if levels else min([c.base for c in columns] + [w.base for w in walls] + [0.0])
    # beams: each end on a column's axis (it takes the column's x, y), (0.335) on a load-bearing wall's top, or on
    # another beam (a node on it)
    ends, on_wall = [], {}
    for i, b in enumerate(beams):
        pts = []
        for k, p in enumerate((b.start, b.end)):
            col = min(columns, key=lambda c: _xy(p, c.centre), default=None)
            wall = _wall_near(p, b.top, walls) if walls else None
            if col is not None and _xy(p, col.centre) < TOL_XY_SUPPORT \
                    and col.base - TOL_Z_SUPPORT <= b.top <= col.top + TOL_Z_SUPPORT:
                pts.append(((col.centre[0], col.centre[1], b.top), "column"))
            elif wall is not None:
                pts.append(((float(p[0]), float(p[1]), b.top), "wall"))
                on_wall[(i, k)] = wall.guid
            else:
                pts.append(((float(p[0]), float(p[1]), b.top), None))
        ends.append(pts)
    # where beams rest on other beams: the points that split those
    splits = {k: [] for k in range(len(beams))}
    for i, pts in enumerate(ends):
        for k, (p, on) in enumerate(pts):
            if on is not None:
                continue
            for j, other in enumerate(beams):
                if j == i or abs(other.top - p[2]) > TOL_Z_SUPPORT:
                    continue
                d, t = _along(p, (*other.start, other.top), (*other.end, other.top))
                if d < TOL_ON_BEAM and 0.0 < t < 1.0:
                    q = np.asarray(other.start, dtype=float) + (np.subtract(other.end, other.start)) * t
                    ends[i][k] = ((float(q[0]), float(q[1]), other.top), "beam")
                    splits[j].append((t, (float(q[0]), float(q[1]), other.top)))
                    break
    # the columns, split at each level a beam meets them
    for c in columns:
        cuts = sorted({round(p[2], 4) for pts in ends for p, on in pts if on == "column"
                       and _xy(p, c.centre) < 1e-6 and c.base + 1e-6 < p[2] < c.top - 1e-6})
        zs = [c.base] + list(cuts) + [c.top]
        for k, (z0, z1) in enumerate(zip(zs[:-1], zs[1:])):
            n1, n2 = model.node((c.centre[0], c.centre[1], z0)), model.node((c.centre[0], c.centre[1], z1))
            model.members.append(Member(c.guid if k == 0 else "{}/{}".format(c.guid, k + 1), c.guid, "column", n1, n2,
                                        tuple(c.size), c.material, c.shape, c.web, tuple(c.x_dir)))
    for i, b in enumerate(beams):
        a, z = ends[i][0][0], ends[i][1][0]
        stops = [a] + [p for _t, p in sorted(splits[i])] + [z]
        for k, (p, q) in enumerate(zip(stops[:-1], stops[1:])):
            n1, n2 = model.node(p), model.node(q)
            if n1 != n2:
                model.members.append(Member(b.guid if k == 0 else "{}/{}".format(b.guid, k + 1), b.guid, "beam", n1,
                                            n2, tuple(b.size), b.material))
        for k, p in ((0, a), (1, z)):                     # (0.335) an end on a wall: held there (pinned)
            if (i, k) in on_wall:
                node = model.node(p)
                model.supports[node] = "wall"
                model.on_walls[node] = on_wall[(i, k)]
    # supports: a column's base on a footing (fixed) — at its top, not a storey or more over it (0.222: the upper
    # floors' columns were held by the footing under them too) —; at the foundations without one: told
    for c in columns:
        base = model.node((c.centre[0], c.centre[1], c.base))
        foot = next((f for f in footings if f.kind != "strip" and _stands_on(c, f)
                     and -0.10 <= c.base - f.top <= TOL_Z_SUPPORT), None)
        below = _supported_below(c, columns, beams)
        wall = _wall_near(c.centre, c.base, walls, 0.30) if walls and foot is None and not below else None
        if foot is not None:
            model.supports[base] = "fixed"
        elif wall is not None:                            # (0.335) on a load-bearing wall: held by it (pinned)
            model.supports[base] = "wall"
            model.on_walls[base] = wall.guid
        elif not below:
            if c.base <= low + TOL_GROUND:
                model.supports[base] = "fixed"
                issues.append(Issue("no_footing", WARNING, (c.guid,)))
            else:
                issues.append(Issue("column_hanging", ERROR, (c.guid,)))
        if levels and not any(abs(c.base - z) < TOL_Z_LEVEL for z in levels):
            issues.append(Issue("off_level", WARNING, (c.guid,)))
    # beams with free ends
    for i, b in enumerate(beams):
        held = sum(1 for _p, on in ends[i] if on is not None)
        if held == 0:
            issues.append(Issue("beam_loose", ERROR, (b.guid,)))
        elif held == 1:
            issues.append(Issue("beam_free_end", WARNING, (b.guid,)))
    for f in footings:
        if f.kind != "strip" and not any(_stands_on(c, f) for c in columns):
            issues.append(Issue("footing_alone", WARNING, (f.guid,)))
    for i, a in enumerate(columns):
        for c in columns[i + 1:]:
            if _xy(a.centre, c.centre) < TOL_DUPLICATE and abs(a.base - c.base) < TOL_DUPLICATE:
                issues.append(Issue("duplicate", WARNING, (a.guid, c.guid)))
    _wall_bases(model, walls, footings, panels, low)                   # (0.335)
    for p in panels:
        if p.thickness <= 0:
            issues.append(Issue("panel_no_thickness", ERROR, (p.guid,)))
        elif not _panel_held(p, model):
            issues.append(Issue("panel_unsupported", WARNING, (p.guid,)))
    if not model.supports and model.members:
        issues.append(Issue("no_supports", ERROR, tuple(sorted({m.guid for m in model.members}))))
    return model


def _supported_below(col, columns, beams):
    """A column standing on another column, or on a beam (a transfer beam)."""
    for other in columns:
        if other is not col and _xy(col.centre, other.centre) < 0.30 and abs(other.top - col.base) < 0.30:
            return True
    for b in beams:
        d, _t = _along((*col.centre, col.base), (*b.start, b.top), (*b.end, b.top))
        if d < 0.30 and abs(b.top - col.base) < 0.30:
            return True
    return False


def _panel_held(panel, model):
    """A slab with a member (a beam, or a column's top) along or under its outline at its level — (0.335) or a
    load-bearing wall under it."""
    from shapely.geometry import LineString, Point, Polygon
    poly = Polygon(panel.outline).buffer(0.30)
    for m in model.members:
        a, b = model.nodes[m.n1], model.nodes[m.n2]
        for p in (a, b):
            if abs(p[2] - panel.level) < TOL_Z_SUPPORT and poly.contains(Point(p[0], p[1])):
                return True
    return any(abs(w.top - panel.level) < TOL_Z_SUPPORT and poly.intersects(LineString((w.start, w.end)))
               for w in model.walls)


def counts(issues):
    out = {ERROR: 0, WARNING: 0, INFO: 0}
    for issue in issues:
        out[issue.severity] = out.get(issue.severity, 0) + 1
    return out
