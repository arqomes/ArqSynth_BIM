"""(0.562, PLANO.md «Gerador de revestimentos 3D em IFC», step 1) The layout of a finish's pieces — tiles, stones,
boards, bricks, panels — over a polygon (with holes) in its own plane, as a fitter sets them out: the bond (a eito,
desencontrado, espinha, cestaria, diagonal, opus, réguas, hexágono, escama, tijolo, livre), the piece's size and
joints, where it starts (a corner, the middle — a joint or a piece on it —, a point, or the start that leaves no
narrow cut), the angle; each piece whole or cut, with its mark, and the counts. Pure geometry (shapely 2, numpy).

Coordinates: the plane's 2D (x, y) — on a wall x along it and y up (`face_frame`), on a floor x east and y north.
A layout is a plain dict (`Layout` fills in what is left out), kept as it is in the model."""

import math
from dataclasses import dataclass, field

import numpy as np
import shapely
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient

# key: (pt, en, what it is laid as)
PATTERNS = {
    "eito": ("A eito (juntas alinhadas)", "Stack bond"),
    "desencontrado": ("Juntas desencontradas", "Running bond"),
    "vertical": ("Desencontrado vertical", "Vertical running bond"),
    "espinha": ("Espinha de peixe (45°)", "Herringbone (45°)"),
    "espinha_reta": ("Espinha de peixe (90°)", "Herringbone (90°)"),
    "cestaria": ("Cestaria", "Basket weave"),
    "diagonal": ("Diagonal (45°)", "Diagonal (45°)"),
    "opus": ("Opus romano (3 tamanhos)", "Opus romanum (3 sizes)"),
    "reguas": ("Réguas de comprimento variável", "Random-length boards"),
    "hexagono": ("Hexágono", "Hexagon"),
    "escama": ("Escama", "Fish scale"),
    "flamengo": ("Tijolo — aparelho flamengo", "Brick — Flemish bond"),
    "ingles": ("Tijolo — aparelho inglês", "Brick — English bond"),
    "livre": ("Padrão livre (peças desenhadas)", "Free pattern (pieces drawn)"),
}
ORIGINS = ("canto", "centro", "ponto", "auto")
ALIGNS = ("junta", "peca")          # at the origin: a joint, or a piece's middle
MIN_AREA = 1e-6                     # m²: a scrap smaller than this is left out
WHOLE = 0.999                       # a piece with this much of its own area is whole
MAX_PIECES = 60000                  # the most laid at once (a mistake in the size would hang the program)


class LayoutError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


DEFAULTS = {"pattern": "eito", "w": 0.60, "h": 0.30, "joint": 0.003, "joint_v": None, "bond": 0.5, "angle": 0.0,
            "origin": "canto", "point": (0.0, 0.0), "align": "junta", "dx": 0.0, "dy": 0.0, "min_cut": 0.05,
            "seed": 1, "lengths": None, "unit": None, "thickness": 0.01}


def layout(data=None, **kw):
    """The layout `data` (a dict, maybe partial) with every key filled in and checked."""
    d = dict(DEFAULTS)
    d.update(data or {})
    d.update(kw)
    if d["pattern"] not in PATTERNS:
        raise LayoutError("tiling_pattern")
    if d["origin"] not in ORIGINS or d["align"] not in ALIGNS:
        raise LayoutError("tiling_origin")
    for k in ("w", "h"):
        d[k] = float(d[k])
        if not 0.005 <= d[k] <= 20.0:
            raise LayoutError("tiling_size")
    d["joint"] = float(d["joint"])
    if not 0.0 <= d["joint"] < min(d["w"], d["h"]) / 2:
        raise LayoutError("tiling_joint")
    if d["joint_v"] is not None:
        d["joint_v"] = float(d["joint_v"])
        if not 0.0 <= d["joint_v"] < min(d["w"], d["h"]) / 2:
            raise LayoutError("tiling_joint")
    d["bond"] = float(d["bond"]) % 1.0
    for k in ("angle", "dx", "dy", "min_cut", "thickness"):
        d[k] = float(d[k])
    d["point"] = tuple(float(v) for v in d["point"])[:2]
    d["seed"] = int(d["seed"])
    if d["pattern"] == "livre" and not d.get("unit"):
        raise LayoutError("tiling_unit")
    return d


@dataclass
class Piece:
    points: list                     # [(x, y)…] counter-clockwise (the piece as laid: joints taken off)
    whole: bool
    kind: str                        # the piece's size, its mark's letter ("A": the main one)
    area: float
    holes: list = field(default_factory=list)


@dataclass
class Result:
    pieces: list
    kinds: dict                      # kind → (w, h) nominal (or its own area for odd shapes)
    origin: tuple                    # where the layout started (plane x, y)
    narrowest: float                 # the narrowest cut piece (m; inf without cuts)

    def counts(self):
        """{kind: (whole, cut)}."""
        out = {}
        for p in self.pieces:
            w, c = out.get(p.kind, (0, 0))
            out[p.kind] = (w + 1, c) if p.whole else (w, c + 1)
        return out

    def summary(self, min_cut=0.0):
        whole = sum(1 for p in self.pieces if p.whole)
        cut = len(self.pieces) - whole
        narrow = sum(1 for p in self.pieces if not p.whole and _narrow_one(p) < min_cut)
        return {"pieces": len(self.pieces), "whole": whole, "cut": cut, "narrow": narrow,
                "area": sum(p.area for p in self.pieces), "narrowest": self.narrowest}


# ---------------------------------------------------------------------------------------------------- the bonds
# Each bond: the nominal pieces (joints not yet off) covering the box [x0, x1] × [y0, y1] of the pattern's own frame
# (its origin a joint corner), as (polygons, kinds).

def _rects(xs0, ys0, ws, hs):
    return [box(x, y, x + w, y + h) for x, y, w, h in zip(xs0, ys0, ws, hs)]


def _grid(bx, w, h, shift):
    """Rows of pieces w × h, row j shifted by j·shift (along x)."""
    x0, y0, x1, y1 = bx
    j0, j1 = math.floor(y0 / h) - 1, math.ceil(y1 / h) + 1
    xs, ys = [], []
    for j in range(j0, j1):
        s = (j * shift) % w
        i0, i1 = math.floor((x0 - s) / w) - 1, math.ceil((x1 - s) / w) + 1
        for i in range(i0, i1):
            xs.append(i * w + s)
            ys.append(j * h)
    return xs, ys


def _eito(bx, d):
    xs, ys = _grid(bx, d["w"], d["h"], 0.0)
    return _rects(xs, ys, [d["w"]] * len(xs), [d["h"]] * len(xs)), ["A"] * len(xs)


def _desencontrado(bx, d):
    xs, ys = _grid(bx, d["w"], d["h"], d["bond"] * d["w"])
    return _rects(xs, ys, [d["w"]] * len(xs), [d["h"]] * len(xs)), ["A"] * len(xs)


def _vertical(bx, d):
    """Columns of pieces h wide, w tall, each column shifted by bond·w (upright boards, a vertical cladding)."""
    x0, y0, x1, y1 = bx
    xs, ys = _grid((y0, x0, y1, x1), d["w"], d["h"], d["bond"] * d["w"])
    return _rects(ys, xs, [d["h"]] * len(xs), [d["w"]] * len(xs)), ["A"] * len(xs)


def _espinha(bx, d):
    """Herringbone: chains of a piece along x and one up, a step (h, h) apart; the chains (L, −L) apart."""
    L, W = d["w"], d["h"]
    if L < W:
        L, W = W, L
    x0, y0, x1, y1 = bx
    polys = []
    # a point (x, y) is in chain c = round(((x − y) / 2L)) about; walk the chains and the steps that reach the box
    c0 = math.floor((x0 - y1) / (2 * L)) - 2
    c1 = math.ceil((x1 - y0) / (2 * L)) + 2
    for c in range(c0, c1):
        ox, oy = c * L, -c * L
        k0 = math.floor(min(x0 - ox, y0 - oy) / W) - int(math.ceil(L / W)) - 2
        k1 = math.ceil(max(x1 - ox, y1 - oy) / W) + 2
        for k in range(k0, k1):
            bxk, byk = ox + k * W, oy + k * W
            polys.append(box(bxk, byk, bxk + L, byk + W))
            polys.append(box(bxk, byk + W, bxk + W, byk + W + L))
    return polys, ["A"] * len(polys)


def _cestaria(bx, d):
    """Basket weave: squares of n pieces side by side (n = L / W, rounded), along x and up in turn."""
    L, W = max(d["w"], d["h"]), min(d["w"], d["h"])
    n = max(1, int(round(L / W)))
    s = n * W
    x0, y0, x1, y1 = bx
    polys = []
    for i in range(math.floor(x0 / s) - 1, math.ceil(x1 / s) + 1):
        for j in range(math.floor(y0 / s) - 1, math.ceil(y1 / s) + 1):
            for k in range(n):
                if (i + j) % 2 == 0:
                    polys.append(box(i * s, j * s + k * W, i * s + s, j * s + (k + 1) * W))
                else:
                    polys.append(box(i * s + k * W, j * s, i * s + (k + 1) * W, j * s + s))
    return polys, ["A"] * len(polys)


# opus: a 3 × 3 module unit (module m = h) of four pieces, each row of units a module along
_OPUS = (((0, 0, 2, 2), "A"), ((2, 0, 1, 2), "B"), ((0, 2, 1, 1), "C"), ((1, 2, 2, 1), "D"))


def _opus(bx, d):
    m = d["h"]
    u = 3 * m
    x0, y0, x1, y1 = bx
    polys, kinds = [], []
    for j in range(math.floor(y0 / u) - 1, math.ceil(y1 / u) + 1):
        s = (j * m) % u
        for i in range(math.floor((x0 - s) / u) - 1, math.ceil((x1 - s) / u) + 1):
            for (a, b, w, h), k in _OPUS:
                X, Y = i * u + s + a * m, j * u + b * m
                polys.append(box(X, Y, X + w * m, Y + h * m))
                kinds.append(k)
    return polys, kinds


def _reguas(bx, d):
    """Boards h wide in rows, each of a length drawn from `lengths` (or between ½ and 1 of w), each row starting
    where the drawing leaves it — the joints of two rows never in line (at least ⅕ of w apart)."""
    rng = np.random.default_rng(d["seed"])
    lengths = [float(v) for v in (d["lengths"] or ())] or None
    w, h = d["w"], d["h"]
    x0, y0, x1, y1 = bx
    polys, kinds = [], []
    letters = {}
    last_joints = np.array([])
    for j in range(math.floor(y0 / h) - 1, math.ceil(y1 / h) + 1):
        x = x0 - w * (0.2 + rng.random())
        joints = []
        while x < x1 + w:
            ln = float(rng.choice(lengths)) if lengths else round(w * (0.5 + 0.5 * rng.random()), 3)
            end = x + ln
            for _t in range(6):          # (no joint within w/5 of one of the row below)
                if len(last_joints) and np.min(np.abs(last_joints - end)) < w / 5:
                    ln = float(rng.choice(lengths)) if lengths else round(w * (0.5 + 0.5 * rng.random()), 3)
                    end = x + ln
                else:
                    break
            polys.append(box(x, j * h, end, (j + 1) * h))
            key = round(ln, 3)
            if key not in letters:
                letters[key] = _letter(len(letters)) if lengths else "A"
            kinds.append(letters[key])
            joints.append(end)
            x = end
        last_joints = np.array(joints)
    return polys, kinds


def _hexagono(bx, d):
    """Pointy hexagons w across the flats (side w/√3), in rows 1.5 sides apart, every other row half a piece along."""
    a = d["w"] / math.sqrt(3.0)
    dx, dy = d["w"], 1.5 * a
    x0, y0, x1, y1 = bx
    ang = np.radians(np.arange(6) * 60.0 + 30.0)
    shape = np.column_stack((a * np.cos(ang), a * np.sin(ang)))
    polys = []
    for j in range(math.floor(y0 / dy) - 1, math.ceil(y1 / dy) + 2):
        s = dx / 2 if j % 2 else 0.0
        for i in range(math.floor((x0 - s) / dx) - 1, math.ceil((x1 - s) / dx) + 2):
            polys.append(Polygon(shape + (i * dx + s, j * dy)))
    return polys, ["A"] * len(polys)


def _escama(bx, d):
    """Fish scales: discs w across in rows w/2 apart, every other row half a scale along; each scale what of its
    disc the rows above leave."""
    r = d["w"] / 2.0
    dy = r
    x0, y0, x1, y1 = bx
    rows = {}
    for j in range(math.floor(y0 / dy) - 2, math.ceil(y1 / dy) + 3):
        s = r if j % 2 else 0.0
        rows[j] = [shapely.Point(i * d["w"] + s, j * dy).buffer(r, 16)
                   for i in range(math.floor((x0 - s) / d["w"]) - 2, math.ceil((x1 - s) / d["w"]) + 3)]
    polys = []
    js = sorted(rows)
    for j in js[:-2]:
        above = shapely.union_all(rows[j + 1] + rows[j + 2])
        for disc in rows[j]:
            g = disc.difference(above)
            for part in getattr(g, "geoms", [g]):
                if part.geom_type == "Polygon" and part.area > MIN_AREA:
                    polys.append(part)
    return polys, ["A"] * len(polys)


def _flamengo(bx, d):
    """Flemish bond: in each row a stretcher (w) and a header (w/2) in turn, the rows ¾ w apart along."""
    w, h, hd = d["w"], d["h"], d["w"] / 2.0
    p = w + hd
    x0, y0, x1, y1 = bx
    polys, kinds = [], []
    for j in range(math.floor(y0 / h) - 1, math.ceil(y1 / h) + 1):
        s = (j * 0.75 * w) % p
        for i in range(math.floor((x0 - s) / p) - 1, math.ceil((x1 - s) / p) + 1):
            X = i * p + s
            polys += [box(X, j * h, X + w, (j + 1) * h), box(X + w, j * h, X + p, (j + 1) * h)]
            kinds += ["A", "B"]
    return polys, kinds


def _ingles(bx, d):
    """English bond: a row of stretchers (w), a row of headers (w/2), the headers on the stretchers' middles."""
    w, h, hd = d["w"], d["h"], d["w"] / 2.0
    x0, y0, x1, y1 = bx
    polys, kinds = [], []
    for j in range(math.floor(y0 / h) - 1, math.ceil(y1 / h) + 1):
        step, s, k = (w, 0.0, "A") if j % 2 == 0 else (hd, hd / 2.0, "B")
        for i in range(math.floor((x0 - s) / step) - 1, math.ceil((x1 - s) / step) + 1):
            polys.append(box(i * step + s, j * h, (i + 1) * step + s, (j + 1) * h))
            kinds.append(k)
    return polys, kinds


def _livre(bx, d):
    """The pieces drawn in a w × h cell (`unit`: [[(x, y)…]…] in the cell, 0–w × 0–h), the cell repeated, each row
    of cells bond·w along."""
    unit = [np.asarray(u, float) for u in d["unit"]]
    w, h = d["w"], d["h"]
    xs, ys = _grid(bx, w, h, d["bond"] * w)
    polys, kinds = [], []
    for x, y in zip(xs, ys):
        for k, u in enumerate(unit):
            polys.append(Polygon(u + (x, y)))
            kinds.append(_letter(k))
    return polys, kinds


def _letter(k):
    s = ""
    k += 1
    while k:
        k, r = divmod(k - 1, 26)
        s = chr(65 + r) + s
    return s


BONDS = {"eito": _eito, "desencontrado": _desencontrado, "vertical": _vertical, "espinha": _espinha,
         "espinha_reta": _espinha, "cestaria": _cestaria, "diagonal": _eito, "opus": _opus, "reguas": _reguas,
         "hexagono": _hexagono, "escama": _escama, "flamengo": _flamengo, "ingles": _ingles, "livre": _livre}
EXTRA_ANGLE = {"espinha": 45.0, "diagonal": 45.0}


def repeat(d):
    """The pattern's repeat (along x, up y) — a shift of either leaves it as it was."""
    p, w, h = d["pattern"], d["w"], d["h"]
    L, W = max(w, h), min(w, h)
    if p in ("espinha", "espinha_reta"):
        return (2 * L, 2 * L)
    if p == "cestaria":
        n = max(1, int(round(L / W)))
        return (2 * n * W, 2 * n * W)
    if p == "opus":
        return (3 * h, 3 * h)
    if p == "hexagono":
        return (w, w * math.sqrt(3.0))
    if p == "escama":
        return (w, w)
    if p == "flamengo":
        return (1.5 * w, h)
    if p == "vertical":
        return (h, w)
    return (w, h)


def kinds_of(d):
    """kind → (w, h) nominal."""
    p, w, h = d["pattern"], d["w"], d["h"]
    if p == "opus":
        return {k: (a[2] * h, a[3] * h) for a, k in _OPUS}
    if p in ("flamengo", "ingles"):
        return {"A": (w, h), "B": (w / 2.0, h)}
    if p == "vertical":
        return {"A": (h, w)}
    return {"A": (w, h)}


# ---------------------------------------------------------------------------------------------------- the laying

def _joint_off(polys, d):
    """The pieces as laid: each the joint's half smaller all round (a rectangle: joint_v off its sides, joint off its
    top and bottom)."""
    jh = d["joint"]
    jv = d["joint_v"] if d["joint_v"] is not None else jh
    if jh <= 0 and jv <= 0:
        return polys
    out = []
    arr = np.array(polys, dtype=object)
    rect = d["pattern"] not in ("hexagono", "escama", "livre")
    if rect and abs(jh - jv) > 1e-12:
        for g in arr:
            x0, y0, x1, y1 = g.bounds
            out.append(box(x0 + jv / 2, y0 + jh / 2, x1 - jv / 2, y1 - jh / 2))
        return out
    return list(shapely.buffer(arr, -max(jh, jv) / 2.0, join_style="mitre"))


def _frame(d, origin):
    """(cos, sin, ox, oy): the pattern's frame in the plane."""
    a = math.radians(d["angle"] + EXTRA_ANGLE.get(d["pattern"], 0.0))
    return math.cos(a), math.sin(a), origin[0], origin[1]


def _to_pattern(xy, fr):
    c, s, ox, oy = fr
    p = np.asarray(xy, float) - (ox, oy)
    return np.column_stack((p[:, 0] * c + p[:, 1] * s, -p[:, 0] * s + p[:, 1] * c))


def _start(poly, d):
    """Where the pattern's origin is for origin canto / centro / ponto (plane coordinates), with dx, dy."""
    fr = _frame(d, (0.0, 0.0))
    pts = _to_pattern(np.asarray(poly.exterior.coords), fr)
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    c, s = fr[0], fr[1]

    def back(u, v):
        return (u * c - v * s, u * s + v * c)

    if d["origin"] == "ponto":
        x, y = d["point"]
        if d["align"] == "peca":
            rw, rh = kinds_of(d)["A"]
            u, v = -rw / 2.0, -rh / 2.0
            bx, by = back(u, v)
            x, y = x + bx, y + by
    elif d["origin"] == "centro":
        u, v = (lo + hi) / 2.0
        if d["align"] == "peca":
            rw, rh = kinds_of(d)["A"]
            u, v = u - rw / 2.0, v - rh / 2.0
        x, y = back(u, v)
    else:                                  # canto (and auto's first try): the lower left corner, in the pattern's frame
        x, y = back(lo[0], lo[1])
    bx_, by_ = back(d["dx"], d["dy"])
    return (x + bx_, y + by_)


def _clip(poly, d, origin):
    fr = _frame(d, origin)
    pts = _to_pattern(np.asarray(poly.exterior.coords), fr)
    bx = (*pts.min(axis=0), *pts.max(axis=0))
    rw, rh = repeat(d)
    if (bx[2] - bx[0]) * (bx[3] - bx[1]) / max(rw * rh, 1e-12) > MAX_PIECES / 4:
        raise LayoutError("tiling_too_many")
    polys, kinds = BONDS[d["pattern"]](bx, d)
    laid = _joint_off(polys, d)
    c, s, ox, oy = fr
    rot = np.array(((c, s), (-s, c)))              # (row vectors: p @ rot = the pattern's p in the plane)
    arr = shapely.transform(np.array(laid, dtype=object), lambda q: q @ rot + (ox, oy))
    shapely.prepare(poly)
    keep = shapely.intersects(poly, arr)
    arr, kinds = arr[keep], [k for k, on in zip(kinds, keep) if on]
    own = shapely.area(arr)
    inside = shapely.contains_properly(poly, arr)
    cut = np.array(arr, dtype=object)
    todo = ~inside
    if todo.any():
        cut[todo] = shapely.intersection(arr[todo], poly)
    area = shapely.area(cut)
    pieces = []
    for g, k, a, a0, whole in zip(cut, kinds, area, own, inside):
        if a <= MIN_AREA:
            continue
        for part in getattr(g, "geoms", [g]):
            if part.geom_type != "Polygon" or part.area <= MIN_AREA:
                continue
            part = orient(part, 1.0)
            pieces.append(Piece([tuple(c) for c in list(part.exterior.coords)[:-1]],
                                bool(whole or a >= a0 * WHOLE), k, float(part.area),
                                [[tuple(c) for c in list(r.coords)[:-1]] for r in part.interiors]))
    narrow = min((_narrow_one(p) for p in pieces if not p.whole), default=math.inf)
    return Result(pieces, kinds_of(d), tuple(origin), narrow)


def _narrow_one(p):
    """A cut piece's narrowest width: its smallest enclosing rectangle's short side."""
    env = shapely.oriented_envelope(Polygon(p.points))
    c = np.asarray(env.exterior.coords) if env.geom_type == "Polygon" else np.zeros((2, 2))
    if len(c) < 4:
        return 0.0
    return float(min(np.linalg.norm(c[1] - c[0]), np.linalg.norm(c[2] - c[1])))


def lay(outline, d=None, holes=()):
    """The pieces of layout `d` over `outline` [(x, y)…] (with `holes`) — a Result. Origin «auto»: of the starts a
    quarter of the repeat apart, the one whose narrowest cut is widest (fewest pieces when it ties)."""
    d = layout(d)
    poly = Polygon(outline, [list(h) for h in holes]).buffer(0)
    if poly.is_empty or poly.area < MIN_AREA:
        raise LayoutError("tiling_empty")
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda g: g.area)
    if d["origin"] != "auto":
        return _clip(poly, d, _start(poly, d))
    base = _start(poly, dict(d, origin="canto"))
    rw, rh = repeat(d)
    c, s, _x, _y = _frame(d, (0.0, 0.0))
    best = None
    for i in range(4):
        for j in range(4):
            u, v = rw * i / 4.0, rh * j / 4.0
            o = (base[0] + u * c - v * s, base[1] + u * s + v * c)
            r = _clip(poly, d, o)
            score = (min(r.narrowest, 1e9), -len(r.pieces))
            if best is None or score > best[0]:
                best = (score, r)
    return best[1]


# ---------------------------------------------------------------------------------------------------- zones

ZONE_KINDS = ("faixa", "cercadura")


def check_zones(zones):
    """The zones (bands across the face, a border round it) checked: [{kind, y0, y1 | width, material, w, h,
    pattern, joint}]."""
    out = []
    for z in zones or ():
        z = dict(z)
        if z.get("kind") not in ZONE_KINDS:
            raise LayoutError("tiling_zone")
        if z["kind"] == "faixa":
            z["y0"], z["y1"] = sorted((float(z.get("y0", 0.0)), float(z.get("y1", 0.1))))
            if z["y1"] - z["y0"] < 0.005:
                raise LayoutError("tiling_zone")
        else:
            z["width"] = float(z.get("width", 0.1))
            if not 0.005 <= z["width"] <= 5.0:
                raise LayoutError("tiling_zone")
        out.append(z)
    return out


def zone_areas(face, zones):
    """[(zone, its polygon on the face)] — a band: the face between its two heights (the plane's y); a border: the
    face's rim as wide as it — and what is left for the main layout."""
    rest = face
    out = []
    for z in zones:
        if z["kind"] == "cercadura":
            area = face.difference(face.buffer(-z["width"], join_style="mitre"))
        else:
            x0, _y0, x1, _y1 = face.bounds
            area = face.intersection(box(x0 - 1.0, z["y0"], x1 + 1.0, z["y1"]))
        area = area.intersection(rest)
        rest = rest.difference(area)
        out.append((z, area))
    return out, rest


def lay_all(face, d, zones=(), mix=None, picks=()):
    """Every piece of a finish over `face` (shapely): the zones' first (each its own layout — its piece, bond and
    material over the main one's), then the main layout on what is left. Each piece's material: a zone's own, a
    piece picked one by one (`picks` [(x, y, material)]: the piece under that point), else the mix (`mix`
    {"materials": [...], "seed"}: one of them at random each), else None (the finish's). Returns (Result of them all,
    [material or None per piece])."""
    zones = check_zones(zones)
    areas, rest = zone_areas(face, zones)
    pieces, mats, kinds = [], [], dict(kinds_of(d))
    origin, narrow = None, math.inf

    def run(poly, dd, material):
        nonlocal origin, narrow
        for part in getattr(poly, "geoms", [poly]):
            if part.geom_type != "Polygon" or part.area < MIN_AREA:
                continue
            q = orient(part, 1.0)
            r = lay(list(q.exterior.coords)[:-1], dd, [list(h.coords)[:-1] for h in q.interiors])
            pieces.extend(r.pieces)
            mats.extend([material] * len(r.pieces))
            narrow = min(narrow, r.narrowest)
            if origin is None and material is None:
                origin = r.origin

    for k, (z, area) in enumerate(areas):
        dd = dict(d, **{key: z[key] for key in ("w", "h", "pattern", "joint", "angle") if key in z})
        if z["kind"] == "faixa":
            dd.update(origin="ponto", point=(face.bounds[0], z["y0"]), align="junta", dx=0.0, dy=0.0)
        letter = "F{}".format(k + 1)
        before = len(pieces)
        run(area, dd, z.get("material"))
        for p in pieces[before:]:
            p.kind = letter
        kinds[letter] = (dd["w"], dd["h"])
    if areas and not rest.is_empty:                  # (the main layout one over the whole face: its joints go on
        q = orient(face, 1.0)                        # across a band — its start found on the whole face)
        whole = lay(list(q.exterior.coords)[:-1], d, [list(h.coords)[:-1] for h in q.interiors])
        main = dict(d, origin="ponto", point=whole.origin, align="junta", dx=0.0, dy=0.0)
        origin = whole.origin
        run(rest, main, None)
    else:
        run(rest, d, None)
    if mix and mix.get("materials"):
        rng = np.random.default_rng(int(mix.get("seed", 1)))
        choice = list(mix["materials"])
        mats = [m if m is not None else str(rng.choice(choice)) for m in mats]
    if picks:
        polys = [Polygon(p.points, p.holes) for p in pieces]
        for x, y, m in picks:
            pt = shapely.Point(float(x), float(y))
            for i, g in enumerate(polys):
                if g.covers(pt):
                    mats[i] = m
                    break
    return Result(pieces, kinds, origin or (0.0, 0.0), narrow), mats


# ---------------------------------------------------------------------------------------------------- solids

def _cap(points, holes):
    """Triangles (index triples into points + the holes' points, in that order) of a polygon's face, counter-
    clockwise: a fan when it is convex and has no holes, else shapely's constrained Delaunay."""
    n = len(points)
    if not holes and n <= 12 and Polygon(points).convex_hull.area <= Polygon(points).area * (1 + 1e-9):
        return [(0, k, k + 1) for k in range(1, n - 1)]
    allp = np.asarray(list(points) + [q for h in holes for q in h], float)
    tris = []
    for tri in shapely.constrained_delaunay_triangles(Polygon(points, holes)).geoms:
        c = np.asarray(tri.exterior.coords)[:3]
        ids = [int(np.argmin(((allp - q) ** 2).sum(axis=1))) for q in c]   # (each corner: the point it is)
        if len(set(ids)) < 3:
            continue
        a, b, cc = allp[ids[0]], allp[ids[1]], allp[ids[2]]
        if (b[0] - a[0]) * (cc[1] - a[1]) - (b[1] - a[1]) * (cc[0] - a[0]) < 0:
            ids = [ids[0], ids[2], ids[1]]
        tris.append(tuple(ids))
    return tris


def prisms(polys, z0, z1):
    """One mesh (verts (N, 3), tris (M, 3), outwards) of the polygons [(points, holes)…] in their plane raised from
    z0 to z1 — a finish's pieces, or its grout bed."""
    verts, tris = [], []
    for points, holes in polys:
        loops = [list(points)] + [list(h) for h in holes]
        flat = [q for loop in loops for q in loop]
        m = len(flat)
        base = len(verts)
        verts += [(x, y, z0) for x, y in flat] + [(x, y, z1) for x, y in flat]
        for a, b, c in _cap(points, holes):
            tris.append((base + m + a, base + m + b, base + m + c))      # (the top, up)
            tris.append((base + a, base + c, base + b))                  # (the bottom, down)
        k = 0
        for loop in loops:                                               # (the sides: an outline counter-clockwise,
            n = len(loop)                                                # its holes clockwise — outwards both)
            for i in range(n):
                a, b = base + k + i, base + k + (i + 1) % n
                tris.append((a, b, b + m))
                tris.append((a, b + m, a + m))
            k += n
    return np.asarray(verts, float).reshape(-1, 3), np.asarray(tris, np.int64).reshape(-1, 3)


def top_triangles(result, z=0.0, most=8000):
    """(triangles (n, 3, 3) in the plane's x, y at height z, whole (n,)) of the pieces' faces — a preview of the
    layout (the first `most` pieces)."""
    tris, whole = [], []
    for p in result.pieces[:most]:
        pts = np.asarray(p.points, float)
        allp = np.vstack([pts] + [np.asarray(h, float) for h in p.holes]) if p.holes else pts
        for a, b, c in _cap(p.points, p.holes):
            tris.append(((allp[a][0], allp[a][1], z), (allp[b][0], allp[b][1], z), (allp[c][0], allp[c][1], z)))
            whole.append(p.whole)
    return np.asarray(tris, float).reshape(-1, 3, 3), np.asarray(whole, bool)


def joints(result, face, d):
    """The joints between the pieces, as polygons [(points, holes)…]: round each piece a ring as wide as half the
    joint (two neighbours' rings meet in the joint's middle), kept on the face."""
    half = max(d["joint"], d["joint_v"] or 0.0) / 2.0
    if half <= 1e-6 or not result.pieces:
        return []
    arr = np.array([Polygon(p.points, p.holes) for p in result.pieces], dtype=object)
    rings = shapely.intersection(shapely.difference(shapely.buffer(arr, half * 1.02, join_style="mitre"), arr), face)
    out = []
    for g in rings:
        for part in getattr(g, "geoms", [g]):
            if part.geom_type == "Polygon" and part.area > 1e-9:
                part = orient(part, 1.0)
                out.append(([tuple(c) for c in list(part.exterior.coords)[:-1]],
                            [[tuple(c) for c in list(r.coords)[:-1]] for r in part.interiors]))
    return out


# ---------------------------------------------------------------------------------------------------- a face in 3D

def face_frame(points):
    """(origin, x, y, normal) of a face's plane for laying: on an upright face (a wall) x level along it and y up; on
    a level one (a floor, a ceiling) x east, y north; else y up the slope."""
    from .mesh import polygon_normal
    p = np.asarray(points, float)
    n = np.asarray(polygon_normal(p), float)
    n = n / (np.linalg.norm(n) or 1.0)
    z = np.array((0.0, 0.0, 1.0))
    if abs(n[2]) > 0.999:
        x = np.array((1.0, 0.0, 0.0))
        y = np.cross(n, x)
        y = y / np.linalg.norm(y)
    else:
        x = np.cross(z, n)
        x = x / np.linalg.norm(x)
        y = np.cross(n, x)
    # (origin: the face's lowest, leftmost corner in its own x, y — so a wall's rows start at its foot)
    q = p - p[0]
    o = p[0] + (q @ x).min() * x + (q @ y).min() * y
    return o, x, y, n


def to_plane(points, frame):
    o, x, y, _n = frame
    p = np.asarray(points, float) - o
    return np.column_stack((p @ x, p @ y))


def to_space(xy, frame, lift=0.0):
    o, x, y, n = frame
    xy = np.asarray(xy, float)
    return o + xy[:, :1] * x + xy[:, 1:2] * y + lift * n
