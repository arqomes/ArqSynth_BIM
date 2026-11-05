"""A roof's carpentry (0.276), from the ArqSynth Modeler add-on's phase R2 (roof_carpentry): pure geometry. Its
pieces from the roof's waters (each a plane over a plan polygon) and its classified edges (core/roof_blocks.edges),
in the roof's own frame, as the add-on makes them —

  ripas (battens)     along the eaves, at the tile's gauge (0,35 m), 5 × 1,5 cm, right under the cover;
  caibros (rafters)   down the slope, 0,50 m apart, 5 × 6 cm, under the battens;
  terças (purlins)    along the eaves, so that no rafter spans more than 1,50 m, 8 × 16 cm, under the rafters;
  fileira (ridge)     along the ridges, varas de rincão / laró along the hips / valleys: 8 × 16 cm, upright, their
                      top where the rafters' is;

— each cut by its water's outline: a rafter's or batten's two sides cut apart, so that by a hip or a valley it ends
cut as the line it meets runs. One thing is not the add-on's: its wall plate (frechal, 8 × 16 cm) lies on the walls'
top under the waters (the add-on put it under the eave's edge), the rafters resting on it. Each piece: its 8 corners
(the 4 at its foot, then the 4 at its top), its axis and section."""

import math
from dataclasses import dataclass, field

ROLES = ("frechal", "fileira", "rincao", "laro", "terca", "caibro", "ripa")
SECTIONS = {"frechal": (0.08, 0.16), "fileira": (0.08, 0.16), "rincao": (0.08, 0.16), "laro": (0.08, 0.16),
            "terca": (0.08, 0.16), "caibro": (0.05, 0.06), "ripa": (0.05, 0.015)}     # (width, height) m
EDGE_ROLES = {"ridge": "fileira", "hip": "rincao", "valley": "laro"}


@dataclass(frozen=True)
class Settings:
    rafter_spacing: float = 0.50        # caibros, axis to axis
    purlin_span: float = 1.50           # the most a rafter spans between purlins (along the slope)
    gauge: float = 0.35                 # ripas: the tile's gauge
    first_batten: float = 0.05          # the first batten over the eave's edge (along the slope)
    min_length: float = 0.15            # pieces shorter than this left out
    sections: tuple = tuple(sorted(SECTIONS.items()))

    def section(self, role):
        return dict(self.sections)[role]

    @property
    def depth(self):
        """How deep the carpentry is under the cover, square to it, down to the rafters' foot."""
        return self.section("ripa")[1] + self.section("caibro")[1]


@dataclass
class Piece:
    role: str
    corners: list                       # 8 (x, y, z): its foot's 4, then its top's 4 (the same order)
    start: tuple                        # its axis (the middle of its section)
    end: tuple
    width: float
    height: float

    @property
    def length(self):
        return math.dist(self.start, self.end)

    @property
    def volume(self):
        return self.length * self.width * self.height


def summary(pieces):
    """{role: (count, length m, volume m³)} of the roles there are."""
    out = {}
    for p in pieces:
        n, length, volume = out.get(p.role, (0, 0.0, 0.0))
        out[p.role] = (n + 1, length + p.length, volume + p.volume)
    return out


# ---------------------------------------------------------------- a water

class _Water:
    """A water's frame: its plane z = a·x + b·y + c (the cover's top), its fall's way in the plan (g: uphill), the
    eave's way (e), its normal; a plan point by (u along e, r along g) and back; its plan polygon in (u, r)."""

    def __init__(self, coeff, polygon):
        a, b, c = coeff
        self.coeff = (float(a), float(b), float(c))
        slope = math.hypot(a, b)
        self.k = math.sqrt(1.0 + a * a + b * b)                     # (1 / cos of its slope)
        self.g = (a / slope, b / slope) if slope > 1e-9 else (0.0, 1.0)
        self.e = (-self.g[1], self.g[0])
        self.n = (-a / self.k, -b / self.k, 1.0 / self.k)
        self.flat = slope < 1e-9
        self.ring = [self.to_ur(x, y) for x, y in list(polygon.exterior.coords)[:-1]]
        self.holes = [[self.to_ur(x, y) for x, y in list(h.coords)[:-1]] for h in polygon.interiors]
        us, rs = [p[0] for p in self.ring], [p[1] for p in self.ring]
        self.u0, self.u1, self.r0, self.r1 = min(us), max(us), min(rs), max(rs)

    def to_ur(self, x, y):
        return (x * self.e[0] + y * self.e[1], x * self.g[0] + y * self.g[1])

    def at(self, u, r, depth):
        """The 3D point over plan (u, r) on the plane `depth` under the cover's top, square to it."""
        x = u * self.e[0] + r * self.g[0]
        y = u * self.e[1] + r * self.g[1]
        a, b, c = self.coeff
        z = a * x + b * y + c
        return (x - self.n[0] * depth, y - self.n[1] * depth, z - self.n[2] * depth)

    def spans(self, axis, value):
        """Where the line (u = value: axis 0; r = value: axis 1) runs inside the polygon: [(lo, hi)] along the
        other coordinate."""
        for ring in [self.ring] + self.holes:
            for p in ring:
                if abs(p[axis] - value) < 1e-7:
                    value += 3e-7                                     # (off a corner)
        cuts = []
        for ring in [self.ring] + self.holes:
            n = len(ring)
            for i in range(n):
                p, q = ring[i], ring[(i + 1) % n]
                if abs(p[axis] - q[axis]) < 1e-12 or (p[axis] - value) * (q[axis] - value) > 0:
                    continue
                s = (value - p[axis]) / (q[axis] - p[axis])
                cuts.append(p[1 - axis] + s * (q[1 - axis] - p[1 - axis]))
        cuts.sort()
        return [(cuts[j], cuts[j + 1]) for j in range(0, len(cuts) - 1, 2) if cuts[j + 1] - cuts[j] > 1e-9]


def _along(water, role, axis, value, half, top, height, min_length):
    """A water's pieces on the line (axis 0: down the slope at u = value; 1: along the eave at r = value), half
    wide (in the plan) each side, their top `top` under the cover and `height` deep: one a stretch of the line in
    the polygon, its two sides cut by it apart (a bevelled end by a hip or valley)."""
    out = []
    for lo, hi in water.spans(axis, value):
        if (hi - lo) * (water.k if axis == 0 else 1.0) < min_length:
            continue
        mid = (lo + hi) / 2
        sides = []
        for off in (-half, half):
            found = next(((a, b) for a, b in water.spans(axis, value + off) if a - 1e-9 <= mid <= b + 1e-9),
                         (lo, hi))
            sides.append(found)
        (m0, m1), (p0, p1) = sides

        def pt(along, across, depth):
            return water.at(across, along, depth) if axis == 0 else water.at(along, across, depth)

        plan = [(m0, value - half), (m1, value - half), (p1, value + half), (p0, value + half)]
        corners = [pt(a, c, top + height) for a, c in plan] + [pt(a, c, top) for a, c in plan]
        width = 2 * half * (1.0 if axis == 0 else water.k)          # (across: in the plane)
        out.append(Piece(role, corners, pt(lo, value, top + height / 2), pt(hi, value, top + height / 2),
                         width, height))
    return out


def _upright(role, a, b, top_drop, section):
    """An upright piece along a 3D line a → b (a ridge, a hip): its top `top_drop` under it, straight down."""
    width, height = section
    d = (b[0] - a[0], b[1] - a[1])
    length = math.hypot(*d)
    side = (-d[1] / length * width / 2, d[0] / length * width / 2) if length > 1e-9 else (width / 2, 0.0)
    plan = [(a, -1), (b, -1), (b, 1), (a, 1)]
    corners = [(p[0] + side[0] * s, p[1] + side[1] * s, p[2] - top_drop - height) for p, s in plan] + \
              [(p[0] + side[0] * s, p[1] + side[1] * s, p[2] - top_drop) for p, s in plan]
    mid = top_drop + height / 2
    return Piece(role, corners, (a[0], a[1], a[2] - mid), (b[0], b[1], b[2] - mid), width, height)


def _plate(a, b, z, section):
    """A wall plate lying from a to b (plan) on the level z: its section across, square."""
    width, height = section
    d = (b[0] - a[0], b[1] - a[1])
    length = math.hypot(*d)
    side = (-d[1] / length * width / 2, d[0] / length * width / 2)
    plan = [(a, -1), (b, -1), (b, 1), (a, 1)]
    corners = [(p[0] + side[0] * s, p[1] + side[1] * s, z) for p, s in plan] + \
              [(p[0] + side[0] * s, p[1] + side[1] * s, z + height) for p, s in plan]
    return Piece("frechal", corners, (a[0], a[1], z + height / 2), (b[0], b[1], z + height / 2), width, height)


# ---------------------------------------------------------------- the whole roof

def pieces(waters, edges, cover, plates=(), settings=None):
    """The carpentry of a roof: waters [((a, b, c), shapely Polygon)] — its cover's top, plane by plane —, its
    edges [(kind, (x, y, z), (x, y, z))] on that top, the cover's thickness (square to it) and its wall plates
    [((x, y), (x, y), z)] (each lying on the walls' top z, along them). [Piece]."""
    s = settings or Settings()
    batten, rafter, purlin = s.section("ripa"), s.section("caibro"), s.section("terca")
    out = []
    planes = []
    for coeff, polygon in waters:
        w = _Water(coeff, polygon)
        planes.append(w)
        if w.flat:
            continue
        # caibros down the slope, from one side of the water to the other
        half = rafter[0] / 2
        count = max(1, math.ceil((w.u1 - w.u0) / max(s.rafter_spacing, 0.05)))
        for i in range(count + 1):
            u = min(max(w.u0 + i * (w.u1 - w.u0) / count, w.u0 + half + 1e-4), w.u1 - half - 1e-4)
            out += _along(w, "caibro", 0, u, half, cover + batten[1], rafter[1], s.min_length)
        # ripas along the eave, at the gauge (along the slope), from the eave's edge up
        half = batten[0] / 2 / w.k
        v = s.first_batten
        while w.r0 + v / w.k <= w.r1 + 1e-9:
            out += _along(w, "ripa", 1, w.r0 + v / w.k, half, cover, batten[1], s.min_length)
            v += max(s.gauge, 0.02)
        # terças: the slope's length split in stretches no rafter spans more than purlin_span
        run = (w.r1 - w.r0) * w.k
        stretches = math.ceil(run / max(s.purlin_span, 0.3))
        for k in range(1, stretches):
            out += _along(w, "terca", 1, w.r0 + (w.r1 - w.r0) * k / stretches, purlin[0] / 2 / w.k,
                          cover + batten[1] + rafter[1], purlin[1], s.min_length)
    for kind, a, b in edges:
        role = EDGE_ROLES.get(kind)
        if role is None or math.dist(a, b) < s.min_length:
            continue
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        k = max((w.k for w in planes if _near(w, mid)), default=1.0)
        out.append(_upright(role, a, b, (cover + batten[1]) * k, s.section(role)))
    for a, b, z in plates:
        if math.dist(a, b) >= s.min_length:
            out.append(_plate(a, b, z, s.section("frechal")))
    return out


def _near(water, point):
    u, r = water.to_ur(*point)
    n = len(water.ring)
    for i in range(n):                                   # (on its outline, or inside it)
        p, q = water.ring[i], water.ring[(i + 1) % n]
        d = (q[0] - p[0], q[1] - p[1])
        length2 = d[0] * d[0] + d[1] * d[1]
        t = 0.0 if length2 < 1e-18 else max(0.0, min(1.0, ((u - p[0]) * d[0] + (r - p[1]) * d[1]) / length2))
        if math.hypot(u - p[0] - t * d[0], r - p[1] - t * d[1]) < 1e-4:
            return True
    return False
