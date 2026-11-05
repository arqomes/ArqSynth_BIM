"""Eurocode 2 verification of a concrete structure's members (0.166, Phase 9, step 4) — NP EN 1992-1-1, for
pre-design, with the forces of the analysis (0.165): a beam's bending in its span and over its supports, its shear
(its stirrups), its slenderness and deflection; a column's compression with bending (its N–M interaction diagram,
the minimum eccentricity, the second-order effects of a slender one) and its ties; a footing's pressure on the soil
(its effective area), its rigidity, its bending both ways and its punching; a slab's bending both ways (Marcus) and
its slenderness. Each gives the reinforcement it needs in bars that fit (the diameter chosen, the clear spacing
kept), and how it stands: OK, attention, failure — with its notes (a code and its numbers: the window words them).
Taken over from the ArqSynth Modeler's calc_eurocode; pure Python (kN, m; bar diameters in mm).

What it gives is a pre-design: a project's calculations are a structural engineer's, signed by them."""

import math
from dataclasses import dataclass, field

import numpy as np

from .actions import CONCRETE_KN_M3, GAMMA_C, GAMMA_G, GAMMA_Q, GAMMA_S

OK, WARN, FAIL = "ok", "atencao", "falha"
_RANK = {OK: 0, WARN: 1, FAIL: 2}

STEEL_KG_M3 = 7850.0
ES = 200e6                      # kPa: the steel's modulus
EPS_CU = 0.0035
AGGREGATE = 0.020               # m: the largest aggregate (dg)
COVER = 0.030                   # m: nominal cover to the links (beams, columns: XC1–XC3)
COVER_SLAB = 0.025
COVER_FOOTING = 0.050           # (cast against blinding)
MU_DUCTILE = 0.295              # μ at x/d = 0,45: beyond it the section is little ductile
MU_MAX = 0.372                  # …at the steel's yield (A500): beyond it, compression reinforcement — not designed here
BEAM_BARS = (12, 16, 20, 25)
COLUMN_BARS = (12, 16, 20, 25)
MESH_BARS = (8, 10, 12, 16)
SKIN_DEPTH = 1.0                # (0.225) m: a beam this deep or more wants skin bars on its sides (EC2 7.3.3(3))
TOP_SHARE = 0.25                # (0.224) a slab's top bars over its supports: at least this part of its span's moment
TOP_REACH = 0.2                 # …from the support's face this part of the span beside it (EC2 9.3.1.2(2))
FOOTING_BARS = (12, 16, 20)
LINK_BARS = (8, 10, 12)
STEP = 0.025                    # m: spacings rounded down to this


@dataclass
class Note:
    code: str
    status: str = OK
    values: dict = field(default_factory=dict)


@dataclass
class Design:
    """A member's verification and the reinforcement adopted: bars as (number, diameter mm); links and meshes as
    (diameter mm, spacing m); required areas in m² (meshes: m²/m)."""
    kind: str                   # "beam" | "column" | "footing" | "slab" | "wall" (0.337: masonry, EC6; 0.342: concrete)
    status: str = OK
    ratio: float = 0.0          # the largest utilisation (demand / capacity)
    notes: list = field(default_factory=list)
    bottom: tuple = None        # a beam's bottom bars
    top: tuple = None           # …its top bars
    bars: tuple = None          # a column's bars
    links: tuple = None         # a beam's stirrups, a column's ties
    mesh_x: tuple = None        # a footing's / slab's bottom mesh, bars along its x
    mesh_y: tuple = None
    top_x: tuple = None         # (0.224) a slab's top bars over its supports, along its x
    top_y: tuple = None
    vertical: tuple = None      # (0.342) a concrete wall's vertical bars on each face (φ, s)
    horizontal: tuple = None    # …its horizontal ones
    bottom2: int = 0            # (0.225) of a beam's bottom bars, those in a second layer (over the first's)
    top2: int = 0               # …of its top bars (under the first's)
    bottom_cont: int = 0        # (0.229) of a beam's bottom bars, those that run its whole length (0: all)…
    bottom_zones: list = None   # …the others' [(from, to)] m along it
    top_cont: int = 0
    top_zones: list = None
    as_bottom: float = 0.0
    as_top: float = 0.0
    cover: float = COVER

    def add(self, code, status=OK, **values):
        self.notes.append(Note(code, status, values))
        if _RANK[status] > _RANK[self.status]:
            self.status = status

    def bump(self, ratio):
        self.ratio = max(self.ratio, float(ratio))

    def worst(self):
        """The note that tells most: the first of the worst status."""
        rank = max((_RANK[n.status] for n in self.notes), default=0)
        return next((n for n in self.notes if _RANK[n.status] == rank), None)


# ------------------------------------------------------------ materials and bars

def fcd(fck):
    return fck / GAMMA_C * 1000.0              # kPa (αcc = 1,0)


def fyd(fyk):
    return fyk / GAMMA_S * 1000.0


def fctm(fck):
    """MPa (EC2 3.1.2, fck ≤ 50)."""
    return 0.30 * fck ** (2.0 / 3.0)


def bar_area(d):
    return math.pi * (d / 1000.0) ** 2 / 4.0   # m²


def bar_mass(d):
    return bar_area(d) * STEEL_KG_M3            # kg/m


def bond_length(d, fck, fyk, good=True):
    """The basic anchorage length lb,rqd (m) of a bar stressed to fyd (EC2 8.4.3): (φ/4) fyd / fbd, fbd = 2,25 η1
    fctd — η1 = 0,7 for bars in poor bond (a beam's top)."""
    fctd = 0.7 * fctm(fck) / GAMMA_C           # (fctk,0.05 = 0,7 fctm)
    fbd = 2.25 * (1.0 if good else 0.7) * fctd
    return d / 1000.0 / 4.0 * (fyk / GAMMA_S) / fbd


def _down(s, step=STEP):
    return round(math.floor(s / step + 1e-9) * step, 4)


def clear_gap(n, d, width, cover, link):
    """The clear gap (m) between n bars of φ d in one layer across `width`."""
    inner = width - 2.0 * (cover + link / 1000.0) - n * d / 1000.0
    return inner / (n - 1) if n > 1 else inner


def min_gap(d):
    """EC2 8.2(2): max(k1 φ, dg + k2, 20 mm)."""
    return max(d / 1000.0, AGGREGATE + 0.005, 0.020)


def fit_bars(area, width, cover, link, choices=BEAM_BARS, least=2):
    """(n, φ, fits): the fewest bars of the smallest diameter that give `area` in one layer across `width`."""
    for d in choices:
        n = max(least, math.ceil(area / bar_area(d) - 1e-9))
        if clear_gap(n, d, width, cover, link) >= min_gap(d):
            return n, d, True
    d = choices[-1]
    return max(least, math.ceil(area / bar_area(d) - 1e-9)), d, False


def beam_bars(area, width, cover, link, choices=BEAM_BARS, least=2):
    """(0.225) (n, φ, n2, fits): a beam's bars for `area` — in one layer when any diameter fits (fit_bars), else in
    two (EC2 8.2(3): the second's bars over the first's, the gaps kept): of the smallest diameter whose bars fit so,
    the most in the first layer and the rest (n2, no more than those) over them."""
    n, d, fits = fit_bars(area, width, cover, link, choices, least)
    if fits:
        return n, d, 0, True
    for d in choices:
        n = max(least, math.ceil(area / bar_area(d) - 1e-9))
        n1 = n
        while n1 > least and clear_gap(n1, d, width, cover, link) < min_gap(d):
            n1 -= 1
        if clear_gap(n1, d, width, cover, link) >= min_gap(d) and n - n1 <= n1:
            return n, d, n - n1, True
    d = choices[-1]
    return max(least, math.ceil(area / bar_area(d) - 1e-9)), d, 0, False


def layer_offset(d):
    """(0.225) m from a layer's bars to the second's over them (centre to centre): φ and the clear gap."""
    return d / 1000.0 + min_gap(d)


def _flexure(m, b, d, fcd_, fyd_):
    """(As m², μ) of a rectangular section b × d under the moment m (kNm, ≥ 0) — the rectangular stress block."""
    if m <= 0.0:
        return 0.0, 0.0
    mu = m / (b * d * d * fcd_)
    if mu >= 0.5:
        return float("inf"), mu
    omega = 1.0 - math.sqrt(1.0 - 2.0 * mu)
    return omega * b * d * fcd_ / fyd_, mu


def span_depth_limit(rho, rho_c, fck, k=1.0):
    """The basic span / effective depth ratio (EC2 7.4.2, expressions 7.16a/b): ρ tension, ρ' compression
    reinforcement ratios; k for the support (1,0 simply supported, 1,3 an end span, 1,5 an inner one)."""
    rho = max(rho, 1e-6)
    rho0 = math.sqrt(fck) * 1e-3
    if rho <= rho0:
        ratio = 11.0 + 1.5 * math.sqrt(fck) * rho0 / rho + 3.2 * math.sqrt(fck) * (rho0 / rho - 1.0) ** 1.5
    else:
        ratio = 11.0 + 1.5 * math.sqrt(fck) * rho0 / max(rho - rho_c, 1e-6) \
            + math.sqrt(fck) * math.sqrt(max(rho_c, 0.0) / rho0) / 12.0
    return k * ratio


def _shear_concrete(k, rho, fck, b, d):
    """VRd,c (kN), EC2 6.2.2 (CRd,c = 0,18/γc)."""
    v = max(0.18 / GAMMA_C * k * (100.0 * min(rho, 0.02) * fck) ** (1.0 / 3.0), 0.035 * k ** 1.5 * math.sqrt(fck))
    return v * 1000.0 * b * d


# ------------------------------------------------------------ beams

def bars_moment(n, dia, b, d, fck, fyk):
    """(0.229) The moment (kNm) n bars of φ dia resist in a b × d section (the rectangular block)."""
    fcd_, fyd_ = fcd(fck), fyd(fyk)
    omega = min(n * bar_area(dia) * fyd_ / (b * d * fcd_), 1.0)
    return omega * (1.0 - omega / 2.0) * b * d * d * fcd_


def _zones(xs, need, length):
    """(0.229) [(x0, x1)] along a beam where `need` (at the points xs) is True, merged."""
    out = []
    for x, on in zip(xs, need):
        if on:
            if out and x - out[-1][1] <= (xs[1] - xs[0]) * 1.01:
                out[-1][1] = x
            else:
                out.append([x, x])
    return [(max(a, 0.0), min(c, length)) for a, c in out]


def _curtail(out, envelope, b, d, al, fck, fyk):
    """(0.229) A beam's bars more than those kept the whole length — the corners' (two), and of the bottom's at least
    a quarter (EC2 9.2.1.4(1), 9.2.1.5(1)) — only where its moment envelope, moved al = z cot θ / 2 each way (EC2
    9.2.1.3(2)), asks more than those kept resist, and an anchorage length lb,rqd past (9.2.1.3(3); the top's in
    poor bond). envelope: (its length, the points along it, the largest moments, the least). In two layers: all
    kept (none stopped)."""
    length, xs, m_max, m_min = envelope
    xs = np.asarray(xs, dtype=float)
    if len(xs) < 2 or length <= 0.0:
        return
    for face, bars, second, values in (("bottom", out.bottom, out.bottom2, np.maximum(m_max, 0.0)),
                                       ("top", out.top, out.top2, np.maximum(-np.asarray(m_min), 0.0))):
        n, dia = bars
        keep = max(2, math.ceil(n / 4.0)) if face == "bottom" else 2
        if second or n <= keep:
            continue
        moved = np.array([values[np.abs(xs - x) <= al + 1e-9].max() for x in xs])   # (the shift rule)
        kept = bars_moment(keep, dia, b, d, fck, fyk)
        lbd = bond_length(dia, fck, fyk, good=face == "bottom")
        zones = [(max(x0 - lbd, 0.0), min(x1 + lbd, length)) for x0, x1 in _zones(xs, moved > kept, length)]
        merged = []
        for z0, z1 in zones:
            if merged and z0 <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], z1))
            else:
                merged.append((z0, z1))
        if not merged or (merged[0][0] <= 1e-6 and merged[-1][1] >= length - 1e-6 and len(merged) == 1):
            continue                                    # (needed the whole length: all run through)
        setattr(out, face + "_cont", keep)
        setattr(out, face + "_zones", [(round(z0, 3), round(z1, 3)) for z0, z1 in merged])
        out.add("curtail", face=face, kept=keep, extra=n - keep, d=dia, zones=_zones_text(merged), al=al, lbd=lbd)


def _zones_text(zones):
    return "; ".join("{:.2f}–{:.2f}".format(a, b) for a, b in zones)


def beam(b, h, span, fck, fyk, m_pos, m_neg, v, deflection=0.0, cover=COVER, envelope=None):
    """A beam b × h (m) of `span` (m) with the envelope of its forces: m_pos (kNm, sagging), m_neg (≤ 0, hogging),
    v (kN), deflection (m, quasi-permanent, elastic). (0.229) envelope: (its length, points along it, the moments'
    envelope there) — where its bars more than those kept stop (_curtail)."""
    out = Design("beam", cover=cover)
    fcd_, fyd_, fct = fcd(fck), fyd(fyk), fctm(fck)
    link = LINK_BARS[0]
    d = h - cover - link / 1000.0 - 0.008              # (bars of φ16 for a start)
    if d <= 0.05:
        out.add("no_depth", FAIL, h=h)
        return out
    as_min = max(0.26 * fct / fyk, 0.0013) * b * d
    as_max = 0.04 * b * h
    out.add("forces", m_pos=m_pos, m_neg=abs(min(m_neg, 0.0)), v=abs(v))
    adopted = {}
    for face, m in (("bottom", max(m_pos, 0.0)), ("top", abs(min(m_neg, 0.0)))):
        depth = d
        for _again in range(4):                         # (0.225: in two layers the depth is less — worked again)
            need, mu = _flexure(m, b, depth, fcd_, fyd_)
            if mu > MU_MAX:
                break
            area = max(need, as_min) if m > 0.0 else 0.0
            n, dia, second, fits = beam_bars(area, b, cover, link)
            centre = h - cover - link / 1000.0 - dia / 2000.0 - (second / n * layer_offset(dia) if n else 0.0)
            if not second or abs(centre - depth) < 1e-4:
                break
            depth = centre
        out.bump(mu / MU_MAX)
        if mu > MU_MAX:
            out.add("bending_fail", FAIL, face=face, mu=mu)
            return out
        if mu > MU_DUCTILE:
            out.add("bending_ductility", WARN, face=face, mu=mu)
        if area > as_max:
            out.bump(area / as_max)
            out.add("bending_too_much", FAIL, face=face, area=area, limit=as_max)
            return out
        if not fits:
            out.add("bars_do_not_fit", WARN, face=face, n=n, d=dia)
        elif second:
            out.add("two_layers", face=face, n1=n - second, n2=second, d=dia, depth=depth)
        adopted[face] = (n, dia, need, area, second, depth)
        out.add("bending", face=face, m=m, mu=mu, need=need, area=area, n=n, d=dia)
    n, dia, need, area, out.bottom2, depth_bottom = adopted["bottom"]
    out.bottom, out.as_bottom = (n, dia), area
    tn, tdia, _tneed, tarea, out.top2, _depth_top = adopted["top"]
    out.top, out.as_top = (tn, tdia), tarea
    d = min(h - cover - link / 1000.0 - max(dia, tdia) / 2000.0, depth_bottom if out.bottom2 else h)
    if h >= SKIN_DEPTH:                                 # (0.225) EC2 7.3.3(3): its sides' bars
        out.add("skin", WARN, h=h)
    # shear (EC2 6.2): the concrete alone, else stirrups with θ from cot 2,5 down to 1,0
    v = abs(v)
    k = min(1.0 + math.sqrt(0.2 / d), 2.0)
    rho = n * bar_area(dia) / (b * d)
    vrdc = _shear_concrete(k, rho, fck, b, d)
    z = 0.9 * d
    nu1 = 0.6 * (1.0 - fck / 250.0)
    cot = next((c for c in (2.5, 2.0, 1.5, 1.0) if b * z * nu1 * fcd_ / (c + 1.0 / c) >= v), None)
    if cot is None:
        vmax = b * z * nu1 * fcd_ / 2.0
        out.bump(v / vmax)
        out.add("shear_crushing", FAIL, v=v, limit=vmax)
        return out
    out.bump(v / (b * z * nu1 * fcd_ / (cot + 1.0 / cot)))
    s_max = min(0.75 * d, 0.30)                        # EC2 9.2.2(6), and a practical 30 cm
    rho_w = 0.08 * math.sqrt(fck) / fyk                # 9.2.2(5)
    chosen = None
    for link in LINK_BARS:
        asw = 2.0 * bar_area(link)                     # (two legs)
        s = min(s_max, asw / (rho_w * b))
        if v > vrdc:
            s = min(s, asw * z * fyd_ * cot / v)
        s = _down(s)
        if s >= 0.075:
            chosen = (link, s)
            break
    if chosen is None:
        out.add("shear_links", FAIL, v=v)
        return out
    out.links = chosen
    out.add("shear", v=v, vrdc=vrdc, cot=cot, d=chosen[0], s=chosen[1], needed=v > vrdc)
    if envelope is not None:                            # (0.229) where the bars more than the corners' stop
        _curtail(out, envelope, b, d, z * cot / 2.0, fck, fyk)
    # slenderness (EC2 7.4.2) and the deflection of the analysis (quasi-permanent, elastic) against L/250
    kk = 1.3 if abs(min(m_neg, 0.0)) > 0.1 * max(m_pos, 1e-9) else 1.0
    rho_t = n * bar_area(dia) / (b * d)
    rho_c = tn * bar_area(tdia) / (b * d) if m_pos > 0 else 0.0
    factor = min(1.5, 500.0 / fyk * (n * bar_area(dia) / max(need, 1e-9)) if need > 0 else 1.5)
    limit = span_depth_limit(rho_t, rho_c, fck, kk) * factor
    ratio = span / d
    out.bump(ratio / limit)
    out.add("slenderness", WARN if ratio > limit else OK, ratio=ratio, limit=limit)
    if deflection > 0.0:
        allowed = span / 250.0
        out.add("deflection", WARN if deflection > allowed else OK, f=deflection, allowed=allowed)
    return out


# ------------------------------------------------------------ columns

def interaction_diagram(b, h, fck, fyk, area, cover_bars, points=24):
    """[(N kN, M kNm)] of the N–M interaction diagram of a section b × h bent about the axis across h, its bars
    `area` (m²) half on each face at `cover_bars` (m, to their middles); compression positive."""
    fcd_, fyd_ = fcd(fck), fyd(fyk)
    d1 = max(cover_bars, 0.01)
    d = h - d1
    half = max(area, 0.0) / 2.0
    out = [(b * h * fcd_ + area * fyd_, 0.0)]
    for i in range(points):
        x = h * (1.5 - i * 1.45 / (points - 1))       # (x / h from 1,5 to 0,05)
        block = min(0.8 * x, h)
        fc = block * b * fcd_
        s1 = max(min(EPS_CU * (x - d1) / x * ES, fyd_), -fyd_)
        s2 = max(min(EPS_CU * (x - d) / x * ES, fyd_), -fyd_)
        n = fc + (s1 + s2) * half
        m = fc * (h / 2.0 - block / 2.0) + s1 * half * (h / 2.0 - d1) + s2 * half * (h / 2.0 - d)
        out.append((n, max(m, 0.0)))
    out.append((-area * fyd_, 0.0))
    out.sort(key=lambda p: -p[0])
    return out


def section_fibres(shape, sx, sy, web=0.0, cells=40):
    """(0.227) A column's section as fibres (N, 3): (x, y, area) of small squares inside it, in its own axes centred
    on its bounding box (core.space_frame.shape_rects; a circle of diameter sx) — `cells` across its smaller side."""
    from .space_frame import shape_rects
    step = max(min(sx, sy), 0.01) / cells
    xs = np.arange(-sx / 2.0 + step / 2.0, sx / 2.0, step)
    ys = np.arange(-sy / 2.0 + step / 2.0, sy / 2.0, step)
    gx, gy = np.meshgrid(xs, ys)
    gx, gy = gx.ravel(), gy.ravel()
    if shape == "circle":
        inside = gx * gx + gy * gy <= (sx / 2.0) ** 2
    else:
        inside = np.zeros(len(gx), dtype=bool)
        for x0, y0, x1, y1 in shape_rects(shape, sx, sy, web):
            inside |= (gx >= x0) & (gx <= x1) & (gy >= y0) & (gy <= y1)
    return np.column_stack((gx[inside], gy[inside], np.full(int(inside.sum()), step * step)))


def fibre_diagram(fibres, bars, fck, fyk, direction, points=24):
    """(0.227) [(N kN, M kNm)] of the N–M interaction diagram of any section (its fibres, section_fibres) and its bars
    [(x, y, area m²)], bent so that its side towards `direction` (a unit (x, y)) is compressed — the moment about the
    axis through its centroid square to it; the rectangular block over 0,8 x, εcu 3,5 ‰ (as interaction_diagram);
    compression positive."""
    fcd_, fyd_ = fcd(fck), fyd(fyk)
    u = np.asarray(direction, dtype=float)
    u = u / np.linalg.norm(u)
    f = np.asarray(fibres, dtype=float)
    b = np.asarray(bars, dtype=float).reshape(-1, 3)
    ac, area = float(f[:, 2].sum()), float(b[:, 2].sum())
    centre = float((f[:, 0] * u[0] + f[:, 1] * u[1]) @ f[:, 2]) / ac
    s_c = f[:, 0] * u[0] + f[:, 1] * u[1] - centre          # (along u from the centroid: the compressed side +)
    s_b = b[:, 0] * u[0] + b[:, 1] * u[1] - centre
    top, depth = float(s_c.max()), float(s_c.max() - s_c.min())
    out = [(ac * fcd_ + area * fyd_, 0.0)]
    for i in range(points):
        x = depth * (1.5 - i * 1.45 / (points - 1))
        block = (top - s_c) <= 0.8 * x
        fc = float(f[block, 2].sum()) * fcd_
        mc = float((f[block, 2] * s_c[block]).sum()) * fcd_
        strain = EPS_CU * (x - (top - s_b)) / x
        stress = np.clip(strain * ES, -fyd_, fyd_)
        n = fc + float(stress @ b[:, 2])
        m = mc + float((stress * b[:, 2]) @ s_b)
        out.append((n, max(m, 0.0)))
    out.append((-area * fyd_, 0.0))
    out.sort(key=lambda p: -p[0])
    return out


def column_spots(shape, sx, sy, web, n, dia, cover, tie):
    """(0.227) Where n bars of φ dia go in a column's section (own axes, its bars' middles), or None when they do not
    fit (the clear gaps, EC2 8.2(2)): a circle's evenly round it; an L's at its six corners, a T's at its eight (EC2
    9.5.2(4): one at each corner), the rest in pairs along its longest faces."""
    inset = cover + tie / 1000.0 + dia / 2000.0
    gap = min_gap(dia) + dia / 1000.0                   # (centre to centre)
    if shape == "circle":
        r = sx / 2.0 - inset
        if n < 4 or r <= 0 or 2.0 * r * math.sin(math.pi / n) < gap:
            return None
        return [(r * math.cos(2.0 * math.pi * k / n), r * math.sin(2.0 * math.pi * k / n)) for k in range(n)]
    from .space_frame import shape_rects
    corners, faces = [], []
    rects = shape_rects(shape, sx, sy, web)
    if shape == "L":
        (ax0, ay0, ax1, ay1), (bx0, by0, bx1, by1) = rects
        x0, y0, xt, yt = ax0 + inset, ay0 + inset, ax1 - inset, by1 - inset
        corners = [(x0, y0), (x0, ay1 - inset), (xt, ay1 - inset), (bx1 - inset, y0), (bx1 - inset, yt), (xt, yt)]
        groups = [[((x0, y0), (x0, ay1 - inset)), ((x0, y0), (bx1 - inset, y0))]]     # (its two outer faces, alike)
    elif shape == "T":
        (fx0, fy0, fx1, fy1), (wx0, wy0, wx1, wy1) = rects
        top, under, low = fy1 - inset, fy0 + inset, wy0 + inset
        left, right, wl, wr = fx0 + inset, fx1 - inset, wx0 + inset, wx1 - inset
        corners = [(left, top), (right, top), (left, under), (right, under), (wl, low), (wr, low), (wl, under),
                   (wr, under)]
        groups = [[((left, top), (right, top))], [((wl, under), (wl, low)), ((wr, under), (wr, low))]]
    if len(corners) > n:
        return None
    extra = n - len(corners)
    counts = [0] * len(groups)                          # (each face of a group as many: the section kept symmetric)
    while extra > 0:
        fit = [i for i in range(len(groups)) if len(groups[i]) <= extra]
        if not fit:
            return None
        best = max(fit, key=lambda i: math.dist(*groups[i][0]) / (counts[i] + 1))
        counts[best] += 1
        extra -= len(groups[best])
    spots = list(corners)
    for faces, c in zip(groups, counts):
        for p, q in faces:
            if math.dist(p, q) / (c + 1) < gap:
                return None
            spots += [(p[0] + (q[0] - p[0]) * k / (c + 1), p[1] + (q[1] - p[1]) * k / (c + 1))
                      for k in range(1, c + 1)]
    pts = np.array(spots)
    d = np.hypot(pts[:, None, 0] - pts[None, :, 0], pts[:, None, 1] - pts[None, :, 1])
    np.fill_diagonal(d, np.inf)
    return spots if float(d.min()) >= gap - 1e-9 else None


def interaction_ratio(points, n, m):
    """How far (N, M) is to the diagram's edge along the ray from the origin: > 1 outside it."""
    n, m = max(n, 0.0), abs(m)
    if n < 1e-9 and m < 1e-9:
        return 0.0
    best = None
    for (n1, m1), (n2, m2) in zip(points, points[1:]):
        dn, dm = n2 - n1, m2 - m1
        det = dn * m - dm * n
        if abs(det) < 1e-12:
            continue
        u = (m1 * n - n1 * m) / det
        if not 0.0 <= u <= 1.0:
            continue
        px, py = n1 + u * dn, m1 + u * dm
        s = (px * n + py * m) / (n * n + m * m)
        if s > 1e-9 and (best is None or s < best):
            best = s
    return 10.0 if best is None else 1.0 / best


def _column_layout(n, b, h):
    """(bars along the faces of width b, along those of width h) of n bars round a b × h section: the four corners,
    the rest in pairs on the longer faces first."""
    nb = nh = 2
    extra = (n - 4) // 2
    for _ in range(extra):
        if (b / max(nb - 1, 1)) >= (h / max(nh - 1, 1)):
            nb += 1
        else:
            nh += 1
    return nb, nh


def column(b, h, height, fck, fyk, n_ed, m_ed, cover=COVER, shape="rect", web=0.0):
    """A column b × h (m), `height` tall, under the compression n_ed (kN, > 0) and the moment m_ed (kNm) of the
    analysis — bent about its weaker axis (on the safe side): the minimum eccentricity (EC2 6.1(4)), the second-order
    effects of a slender one (nominal curvature, 5.8.8; l0 = L), then the bars its N–M diagram needs. (0.227) A
    round one (b its diameter), an L or a T (b × h outside, its legs `web` thick): shaped_column."""
    if shape in ("circle", "L", "T"):
        return shaped_column(shape, b, h, web, height, fck, fyk, n_ed, m_ed, cover)
    out = Design("column", cover=cover)
    fcd_, fyd_ = fcd(fck), fyd(fyk)
    t, w = min(b, h), max(b, h)                        # (the depth bent: the smaller side)
    ac = b * h
    n_ed = max(n_ed, 0.0)
    e0 = max(t / 30.0, 0.02)
    m = max(abs(m_ed), n_ed * e0)
    out.add("column_forces", n=n_ed, m=abs(m_ed), e0=e0)
    l0 = max(height, 0.01)
    lam = l0 / (t / math.sqrt(12.0))
    nrel = n_ed / max(ac * fcd_, 1e-9)
    lam_lim = 20.0 * 0.7 * 1.1 * 0.7 / math.sqrt(max(nrel, 1e-6))
    if lam > lam_lim:
        curvature = (fyd_ / ES) / (0.45 * 0.9 * t)
        m2 = n_ed * curvature * l0 ** 2 / 10.0
        m += m2
        out.add("second_order", WARN, lam=lam, limit=lam_lim, m2=m2)
    else:
        out.add("column_slenderness", lam=lam, limit=lam_lim)
    as_min = max(0.10 * n_ed / fyd_, 0.002 * ac)
    as_max = 0.04 * ac
    link = 8
    chosen = None
    candidates = sorted(((nb, dia) for dia in COLUMN_BARS for nb in range(4, 41, 2)),
                        key=lambda c: (c[0] * bar_area(c[1]), c[1]))
    for nb, dia in candidates:
        area = nb * bar_area(dia)
        if area < as_min - 1e-12:
            continue
        if area > as_max:
            break
        along_b, along_h = _column_layout(nb, b, h)
        if clear_gap(along_b, dia, b, cover, link) < min_gap(dia) or \
                clear_gap(along_h, dia, h, cover, link) < min_gap(dia):
            continue
        # (the bars on the two faces across the bending: those along the longer side)
        cover_bars = cover + link / 1000.0 + dia / 2000.0
        on_faces = 2 * (along_b if b >= h else along_h) * bar_area(dia)
        ratio = interaction_ratio(interaction_diagram(w, t, fck, fyk, on_faces, cover_bars), n_ed, m)
        if ratio <= 1.0:
            chosen = (nb, dia, ratio, area)
            break
    if chosen is None:
        out.bump(1.5)
        out.add("column_fail", FAIL, n=n_ed, m=m)
        return out
    nb, dia, ratio, area = chosen
    out.bump(ratio)
    out.bars, out.as_bottom = (nb, dia), area
    out.add("interaction", n=n_ed, m=m, n_bars=nb, d=dia, ratio=ratio, as_min=as_min)
    tie = max(8, int(math.ceil(dia / 4.0)))            # EC2 9.5.3(1): ≥ 6 mm and ≥ φ/4
    s = _down(min(20.0 * dia / 1000.0, t, 0.40))       # 9.5.3(3)
    out.links = (tie, s)
    out.add("ties", d=tie, s=s)
    return out


CIRCLE_MIN_BARS = 6             # (0.227) a round column's bars at least (the practice; EC2 9.5.2(4) asks four)
DIRECTIONS = ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0))


def shaped_column(shape, sx, sy, web, height, fck, fyk, n_ed, m_ed, cover=COVER):
    """(0.227) A round column (sx its diameter), an L or a T (sx × sy outside, `web` its legs' thickness): as
    column — its least radius of gyration for its slenderness, its smaller side for the minimum eccentricity and the
    curvature —, its bars where column_spots puts them, its N–M diagram by fibres (fibre_diagram), the moment taken
    each way along its sides (an L and a T are not symmetric: the worst)."""
    from .space_frame import section
    out = Design("column", cover=cover)
    fcd_, fyd_ = fcd(fck), fyd(fyk)
    ac, i_y, i_x, _j, _c = section(shape, sx, sy, web)
    t = min(sx, sy)
    n_ed = max(n_ed, 0.0)
    e0 = max(t / 30.0, 0.02)
    m = max(abs(m_ed), n_ed * e0)
    out.add("column_forces", n=n_ed, m=abs(m_ed), e0=e0)
    l0 = max(height, 0.01)
    lam = l0 / math.sqrt(min(i_y, i_x) / ac)
    nrel = n_ed / max(ac * fcd_, 1e-9)
    lam_lim = 20.0 * 0.7 * 1.1 * 0.7 / math.sqrt(max(nrel, 1e-6))
    if lam > lam_lim:
        m2 = n_ed * (fyd_ / ES) / (0.45 * 0.9 * t) * l0 ** 2 / 10.0
        m += m2
        out.add("second_order", WARN, lam=lam, limit=lam_lim, m2=m2)
    else:
        out.add("column_slenderness", lam=lam, limit=lam_lim)
    as_min = max(0.10 * n_ed / fyd_, 0.002 * ac)
    as_max = 0.04 * ac
    fibres = section_fibres(shape, sx, sy, web)
    ways = DIRECTIONS[:1] if shape == "circle" else DIRECTIONS
    least = CIRCLE_MIN_BARS if shape == "circle" else {"L": 6, "T": 8}[shape]
    link = 8
    chosen = None
    for nb, dia in sorted(((nb, dia) for dia in COLUMN_BARS for nb in range(least, 41)),
                          key=lambda c: (c[0] * bar_area(c[1]), c[1])):
        area = nb * bar_area(dia)
        if area < as_min - 1e-12:
            continue
        if area > as_max:
            break
        spots = column_spots(shape, sx, sy, web, nb, dia, cover, link)
        if spots is None:
            continue
        bars = [(x, y, bar_area(dia)) for x, y in spots]
        ratio = max(interaction_ratio(fibre_diagram(fibres, bars, fck, fyk, way), n_ed, m) for way in ways)
        if ratio <= 1.0:
            chosen = (nb, dia, ratio, area)
            break
    if chosen is None:
        out.bump(1.5)
        out.add("column_fail", FAIL, n=n_ed, m=m)
        return out
    nb, dia, ratio, area = chosen
    out.bump(ratio)
    out.bars, out.as_bottom = (nb, dia), area
    out.add("interaction", n=n_ed, m=m, n_bars=nb, d=dia, ratio=ratio, as_min=as_min)
    tie = max(8, int(math.ceil(dia / 4.0)))            # EC2 9.5.3(1)
    s = _down(min(20.0 * dia / 1000.0, min(t, web) if shape in ("L", "T") else t, 0.40))     # 9.5.3(3)
    out.links = (tie, s)
    out.add("ties", d=tie, s=s)
    out.add("column_shape", shape=shape)
    return out


# ------------------------------------------------------------ footings

def footing(length, width, depth, col_x, col_y, fck, fyk, n_ed, n_serv, mx=0.0, my=0.0, soil=200.0,
            cover=COVER_FOOTING):
    """A pad footing length × width × depth (m) under a column col_x × col_y (along the footing's length / width):
    the column's force n_ed (kN, ULS) and n_serv (service, G + Q), its moments mx, my (kNm, service: about the axes
    across its length / width); the soil's allowable pressure `soil` (kPa)."""
    out = Design("footing", cover=cover)
    a, bw = max(length, 0.05), max(width, 0.05)
    own = a * bw * depth * CONCRETE_KN_M3
    n = max(n_serv, 0.0) + own
    ex, ey = abs(mx) / max(n, 1e-9), abs(my) / max(n, 1e-9)
    eff_a, eff_b = a - 2.0 * ex, bw - 2.0 * ey          # (the effective area, EC7 Annex D)
    if eff_a <= 0.0 or eff_b <= 0.0:
        out.bump(2.0)
        out.add("overturning", FAIL, ex=ex, ey=ey)
        return out
    sigma = n / (eff_a * eff_b)
    out.bump(sigma / max(soil, 1e-9))
    if sigma > soil:
        side = math.ceil(math.sqrt(n / soil) / 0.05) * 0.05
        out.add("bearing_fail", FAIL, sigma=sigma, soil=soil, side=side)
        return out
    out.add("bearing", sigma=sigma, soil=soil, n=n, ex=ex, ey=ey)
    over = max(a - col_x, bw - col_y) / 2.0
    out.add("rigid" if depth >= over / 2.0 else "flexible", OK if depth >= over / 2.0 else WARN, h=depth,
            limit=over / 2.0)
    d = depth - cover - 0.016
    if d <= 0.05:
        out.add("no_depth", FAIL, h=depth)
        return out
    fcd_, fyd_ = fcd(fck), fyd(fyk)
    s_uls = max(n_ed, 0.0) / (a * bw)                  # (the net pressure under the column's ULS force)
    as_min = max(0.26 * fctm(fck) / fyk, 0.0013) * d
    meshes = []
    for axis, cant, dd in (("x", (a - col_x) / 2.0, d), ("y", (bw - col_y) / 2.0, d - 0.016)):
        m = s_uls * max(cant, 0.0) ** 2 / 2.0          # kNm/m at the column's face
        need, mu = _flexure(m, 1.0, dd, fcd_, fyd_)
        out.bump(mu / MU_MAX)
        if mu > MU_MAX:
            out.add("bending_fail", FAIL, face=axis, mu=mu)
            return out
        area = max(need, as_min)
        dia, s = _mesh(area, FOOTING_BARS, 0.25)
        meshes.append((dia, s))
        out.add("mesh", face=axis, m=m, need=need, area=area, d=dia, s=s)
    out.mesh_x, out.mesh_y = meshes
    out.as_bottom = max(bar_area(meshes[0][0]) / meshes[0][1], 0.0)
    # punching (EC2 6.4): at the column's face (the struts), then at 2d (out of the footing: not critical)
    nu = 0.6 * (1.0 - fck / 250.0)
    u0 = 2.0 * (col_x + col_y)
    v0 = max(n_ed, 0.0) / (u0 * d) / 1000.0           # MPa
    vmax = 0.4 * nu * fcd_ / 1000.0
    out.bump(v0 / vmax)
    if v0 > vmax:
        out.add("punching_face", FAIL, v=v0, limit=vmax)
        return out
    if col_x + 4.0 * d < a and col_y + 4.0 * d < bw:
        u1 = 2.0 * (col_x + col_y) + 4.0 * math.pi * d
        inside = col_x * col_y + 2.0 * (col_x + col_y) * 2.0 * d + math.pi * (2.0 * d) ** 2
        ved = max(max(n_ed, 0.0) - s_uls * inside, 0.0)
        v1 = ved / (u1 * d) / 1000.0
        k = min(1.0 + math.sqrt(0.2 / d), 2.0)
        rho = min(math.sqrt((bar_area(meshes[0][0]) / meshes[0][1]) * (bar_area(meshes[1][0]) / meshes[1][1]))
                  / d, 0.02)
        vrd = _shear_concrete(k, rho, fck, 1.0, 1.0) / 1000.0
        out.bump(v1 / vrd)
        out.add("punching", FAIL if v1 > vrd else OK, v=v1, limit=vrd)
    else:
        out.add("punching_out")
    return out


COMBINED_STEPS = 400            # (0.250) stations along a combined footing for its shear and moments


def combined_footing(length, width, depth, columns, fck, fyk, soil=200.0, cover=COVER_FOOTING):
    """(0.250) A combined footing length × width × depth (m) under two columns — columns: [(u: its middle from the
    footing's, along its length; its size along; its size across; n_ed kN, ULS; n_serv, service)]:
    the soil's pressure on the effective area (EC7 Annex D: the loads' eccentricity along it); along it, a beam on
    the soil's net pressure — linear, as the columns' resultant puts it — carrying the two columns: its sagging
    moments by them (bottom bars, mesh_x), its hogging between them (top bars, top_x), its shear at d from each
    column's face (no links: VRd,c, EC2 6.2.2); across it, under each column, a band (its size + d each side)
    cantilevering from the column's faces (bottom bars, mesh_y); punching at each column (EC2 6.4) as a pad's."""
    out = Design("footing", cover=cover)
    a, bw = max(length, 0.05), max(width, 0.05)
    cols = [(float(u), float(cx), float(cy), max(float(ne), 0.0), max(float(ns), 0.0)) for u, cx, cy, ne, ns in columns]
    own = a * bw * depth * CONCRETE_KN_M3
    n_serv = sum(c[4] for c in cols) + own
    e = sum(c[4] * c[0] for c in cols) / max(n_serv, 1e-9)
    out.add("combined", span=abs(cols[1][0] - cols[0][0]), n1=cols[0][3], n2=cols[1][3])
    eff = a - 2.0 * abs(e)
    if eff <= 0.0:
        out.bump(2.0)
        out.add("overturning", FAIL, ex=abs(e), ey=0.0)
        return out
    sigma = n_serv / (eff * bw)
    out.bump(sigma / max(soil, 1e-9))
    if sigma > soil:
        out.add("combined_bearing_fail", FAIL, sigma=sigma, soil=soil,
                width=math.ceil(n_serv / (eff * soil) / 0.05) * 0.05)
        return out
    out.add("bearing", sigma=sigma, soil=soil, n=n_serv, ex=abs(e), ey=0.0)
    d = depth - cover - 0.016
    if d <= 0.05:
        out.add("no_depth", FAIL, h=depth)
        return out
    fcd_, fyd_ = fcd(fck), fyd(fyk)
    # along it: the shear and moments of the beam on the soil (net ULS pressure, linear: its resultant the columns')
    total = sum(c[3] for c in cols)
    eu = sum(c[3] * c[0] for c in cols) / max(total, 1e-9)
    xs = sorted({-a / 2.0 + a * k / COMBINED_STEPS for k in range(COMBINED_STEPS + 1)}       # (the columns on it,
                | {c[0] for c in cols if -a / 2.0 < c[0] < a / 2.0})                         # their loads there)
    q = [total / a * (1.0 + 12.0 * eu * x / (a * a)) for x in xs]
    shear, moment = [0.0], [0.0]
    for k in range(1, len(xs)):
        dx = xs[k] - xs[k - 1]
        v = shear[-1] + (q[k - 1] + q[k]) / 2.0 * dx
        moment.append(moment[-1] + (shear[-1] + v) / 2.0 * dx)
        v -= sum(c[3] for c in cols if xs[k - 1] < c[0] <= xs[k])
        shear.append(v)
    m_pos, m_neg = max(max(moment), 0.0), max(-min(moment), 0.0)
    middle = (cols[0][0] + cols[1][0]) / 2.0
    checks = []                                          # (|V| at d from a face, between the columns: its bars on top)
    for u, cx, _cy, _ne, _ns in cols:
        for x in (u - cx / 2.0 - d, u + cx / 2.0 + d):
            if -a / 2.0 <= x <= a / 2.0:
                k = min(int(np.searchsorted(xs, x)), len(xs) - 1)
                checks.append((abs(shear[k]), abs(x - middle) < abs(u - middle)))
    v_max = max((v for v, _top in checks), default=0.0)
    out.add("combined_moments", m_pos=m_pos, m_neg=m_neg, v=v_max)
    as_min = max(0.26 * fctm(fck) / fyk, 0.0013) * d
    meshes = {}
    for key, m, dd in (("mesh_x", m_pos / bw, d), ("top_x", m_neg / bw, d)):
        need, mu = _flexure(m, 1.0, dd, fcd_, fyd_)
        out.bump(mu / MU_MAX)
        if mu > MU_MAX:
            out.add("bending_fail", FAIL, face="x", mu=mu)
            return out
        area = max(need, as_min)
        meshes[key] = _mesh(area, FOOTING_BARS, 0.25)
        out.add("mesh" if key == "mesh_x" else "combined_top", face="x", m=m, need=need, area=area,
                d=meshes[key][0], s=meshes[key][1])
    m_y = 0.0                                            # (across: the band under each column)
    for _u, cx, cy, ne, _ns in cols:
        band = min(cx + 2.0 * d, a)
        m_y = max(m_y, ne / (bw * band) * max((bw - cy) / 2.0, 0.0) ** 2 / 2.0)
    need, mu = _flexure(m_y, 1.0, d - 0.016, fcd_, fyd_)
    out.bump(mu / MU_MAX)
    if mu > MU_MAX:
        out.add("bending_fail", FAIL, face="y", mu=mu)
        return out
    area = max(need, as_min)
    meshes["mesh_y"] = _mesh(area, FOOTING_BARS, 0.25)
    out.add("mesh", face="y", m=m_y, need=need, area=area, d=meshes["mesh_y"][0], s=meshes["mesh_y"][1])
    out.mesh_x, out.mesh_y, out.top_x = meshes["mesh_x"], meshes["mesh_y"], meshes["top_x"]
    out.as_bottom = bar_area(out.mesh_x[0]) / out.mesh_x[1]
    out.as_top = bar_area(out.top_x[0]) / out.top_x[1]
    # the shear along it, no links (EC2 6.2.2): its tension bars there — on top between the columns, under outside
    k = min(1.0 + math.sqrt(0.2 / d), 2.0)
    worst = (0.0, 1.0, 1.0)
    for v, inner in checks:
        vrd = _shear_concrete(k, (out.as_top if inner else out.as_bottom) / d, fck, 1.0, 1.0) / 1000.0
        v_ed = v / (bw * d) / 1000.0
        if v_ed / vrd > worst[0]:
            worst = (v_ed / vrd, v_ed, vrd)
    out.bump(worst[0])
    out.add("combined_shear", FAIL if worst[0] > 1.0 else OK, v=worst[1], limit=worst[2])
    # punching at each column (EC2 6.4): at its face, then at 2d when that perimeter is in the footing
    nu = 0.6 * (1.0 - fck / 250.0)
    s_avg = total / (a * bw)
    for u, cx, cy, ne, _ns in cols:
        v0 = ne / (2.0 * (cx + cy) * d) / 1000.0
        vmax = 0.4 * nu * fcd_ / 1000.0
        out.bump(v0 / vmax)
        if v0 > vmax:
            out.add("punching_face", FAIL, v=v0, limit=vmax)
            return out
        if abs(u) + cx / 2.0 + 2.0 * d < a / 2.0 and cy + 4.0 * d < bw:
            u1 = 2.0 * (cx + cy) + 4.0 * math.pi * d
            inside = cx * cy + 2.0 * (cx + cy) * 2.0 * d + math.pi * (2.0 * d) ** 2
            v1 = max(ne - s_avg * inside, 0.0) / (u1 * d) / 1000.0
            rho_p = min(math.sqrt(out.as_bottom * bar_area(out.mesh_y[0]) / out.mesh_y[1]) / d, 0.02)
            vrd_p = _shear_concrete(k, rho_p, fck, 1.0, 1.0) / 1000.0
            out.bump(v1 / vrd_p)
            out.add("punching", FAIL if v1 > vrd_p else OK, v=v1, limit=vrd_p)
        else:
            out.add("punching_out")
    return out


STRUT_RANGE = (45.0, 55.0)      # (0.228) degrees: a pile cap's struts kept in this range (Blévot's)
NODE_K1, NODE_K2 = 1.0, 0.85    # (0.228) EC2 6.5.4(4): a node's stress ≤ k ν' fcd — compression only / a tie in it
DISTRIBUTION = 0.20             # (0.228) a strip footing's bars along it: this part of those across (EC2 9.3.1.1(2))


def pile_cap(spots, pile_d, length, width, depth, col_x, col_y, fck, fyk, n_ed, n_serv, cover=COVER_FOOTING):
    """(0.228) A pile cap length × width × depth (m) on its piles (spots: their axes from its middle, along its own x
    and y; pile_d their diameter) under a column col_x × col_y: by struts and ties (EC2 6.5) — the column's force and
    the cap's weight shared by the piles; two piles: one tie along them, T = N (2l − a) / (8 d); four at the corners:
    a tie along each side, T = N (2l − a) / (16 d) (l the piles' spacing that way, a the column's side, d the depth to
    the ties: the struts from a quarter of the column to the piles' axes); the struts' angle against Blévot's 45–55°;
    the nodes (EC2 6.5.4), hydrostatic (one stress on all their faces): the column's force over its section ≤ k1 ν'
    fcd, a pile's over its own (a tie anchored there) ≤ k2 ν' fcd. One pile: the minimum mesh. Its bars: mesh_x along
    x, mesh_y along y (the ties spread so that the band over
    each pile line holds them)."""
    out = Design("footing", cover=cover)
    n = len(spots)
    own = length * width * depth * CONCRETE_KN_M3
    n_uls, n_sv = max(n_ed, 0.0) + GAMMA_G * own, max(n_serv, 0.0) + own
    fcd_, fyd_ = fcd(fck), fyd(fyk)
    d = depth - cover - 0.016
    if d <= 0.05:
        out.add("no_depth", FAIL, h=depth)
        return out
    as_min = max(0.26 * fctm(fck) / fyk, 0.0013) * d
    out.add("pile_cap", n=n, r=n_uls / max(n, 1), r_serv=n_sv / max(n, 1))
    pile_area = math.pi * pile_d ** 2 / 4.0
    nu = 1.0 - fck / 250.0
    xs = sorted({round(x, 6) for x, _y in spots})
    ys = sorted({round(y, 6) for _x, y in spots})
    ties = {"x": 0.0, "y": 0.0}
    if n == 1:
        out.add("pile_cap_one")
    elif n in (2, 4) and (n == 2 or (len(xs) == 2 and len(ys) == 2)):
        if n == 2:
            lx = abs(spots[1][0] - spots[0][0])
            reach = lx / 2.0 - col_x / 4.0              # (from a quarter of the column to a pile's axis)
            theta = math.degrees(math.atan2(d, max(reach, 1e-6)))
            ties["x"] = n_uls * (2.0 * lx - col_x) / (8.0 * d)
        else:
            lx, ly = xs[1] - xs[0], ys[1] - ys[0]
            reach = math.hypot(lx / 2.0 - col_x / 4.0, ly / 2.0 - col_y / 4.0)
            theta = math.degrees(math.atan2(d, max(reach, 1e-6)))
            ties["x"] = n_uls * (2.0 * lx - col_x) / (16.0 * d)
            ties["y"] = n_uls * (2.0 * ly - col_y) / (16.0 * d)
        lo, hi = STRUT_RANGE
        out.add("struts", OK if lo <= theta <= hi else WARN, theta=theta, low=lo, high=hi)
        # (hydrostatic nodes: the stress on the face loaded — the column's, the pile's — is the struts' too)
        s_col = n_uls / (col_x * col_y) / 1000.0                # MPa
        s_pile = n_uls / n / pile_area / 1000.0
        lim_col, lim_pile = NODE_K1 * nu * fcd_ / 1000.0, NODE_K2 * nu * fcd_ / 1000.0
        out.bump(max(s_col / lim_col, s_pile / lim_pile))
        out.add("node_column", FAIL if s_col > lim_col else OK, stress=s_col, limit=lim_col)
        out.add("node_pile", FAIL if s_pile > lim_pile else OK, stress=s_pile, limit=lim_pile)
        if s_col > lim_col or s_pile > lim_pile:
            return out
    else:
        out.add("pile_cap_other", WARN, n=n)
    meshes = []
    for axis, across in (("x", width), ("y", length)):
        tie = ties[axis]
        lines = 1 if n == 2 else 2                      # (the pile lines along that way: the bands the ties go in)
        band = min(across / lines, pile_d + 0.20)
        need = tie / fyd_ / band if tie > 0 else 0.0               # (m²/m: each band holds its tie; kN/kPa = m²)
        area = max(need, as_min)
        dia, s = _mesh(area, FOOTING_BARS, 0.25)
        meshes.append((dia, s))
        if tie > 0:
            out.add("cap_tie", face=axis, t=tie, need=need, area=area, d=dia, s=s)
            out.bump(need / max(bar_area(dia) / s, 1e-12))
        else:                                           # (no tie that way: the minimum mesh)
            out.add("cap_mesh", face=axis, area=area, d=dia, s=s)
    out.mesh_x, out.mesh_y = meshes
    out.as_bottom = bar_area(meshes[0][0]) / meshes[0][1]
    return out


def strip_footing(width, depth, wall, fck, fyk, q_ed, q_serv, soil=200.0, cover=COVER_FOOTING):
    """(0.228) A strip footing `width` × depth (m) under a wall `wall` thick, q_ed / q_serv (kN/m: ULS, service) on
    it: as a pad across it — the soil's pressure with its own weight, rigid or not, the bending of each side from the
    wall's face, its bars across (mesh_y: they span its width) — and the bars along it (mesh_x) a fifth of those (EC2
    9.3.1.1(2), as a one-way slab's)."""
    out = Design("footing", cover=cover)
    b = max(width, 0.05)
    own = b * depth * CONCRETE_KN_M3
    sigma = (max(q_serv, 0.0) + own) / b
    out.bump(sigma / max(soil, 1e-9))
    if sigma > soil:
        need = math.ceil((max(q_serv, 0.0) + own) / soil / 0.05) * 0.05
        out.add("bearing_fail", FAIL, sigma=sigma, soil=soil, side=need)
        return out
    out.add("strip_bearing", sigma=sigma, soil=soil, q=max(q_serv, 0.0) + own)
    over = max(b - wall, 0.0) / 2.0
    out.add("rigid" if depth >= over / 2.0 else "flexible", OK if depth >= over / 2.0 else WARN, h=depth,
            limit=over / 2.0)
    d = depth - cover - 0.008
    if d <= 0.05:
        out.add("no_depth", FAIL, h=depth)
        return out
    fcd_, fyd_ = fcd(fck), fyd(fyk)
    m = max(q_ed, 0.0) / b * over ** 2 / 2.0
    need, mu = _flexure(m, 1.0, d, fcd_, fyd_)
    out.bump(mu / MU_MAX)
    if mu > MU_MAX:
        out.add("bending_fail", FAIL, face="y", mu=mu)
        return out
    as_min = max(0.26 * fctm(fck) / fyk, 0.0013) * d
    area = max(need, as_min)
    across = _mesh(area, FOOTING_BARS, 0.25)
    out.add("mesh", face="y", m=m, need=need, area=area, d=across[0], s=across[1])
    along_area = DISTRIBUTION * bar_area(across[0]) / across[1]
    along = _mesh(along_area, MESH_BARS, 0.25)
    out.add("strip_along", area=along_area, d=along[0], s=along[1])
    out.mesh_x, out.mesh_y = along, across
    out.as_bottom = bar_area(across[0]) / across[1]
    return out


# ------------------------------------------------------------ walls (0.342)

WALL_BARS = (8, 10, 12, 16)
COVER_WALL = 0.030              # m: nominal cover to the outer bars (the horizontal ones, outside the vertical)
WALL_SPACINGS = (0.40, 0.35, 0.30, 0.25, 0.20, 0.175, 0.15, 0.125, 0.10)
WALL_SLENDER = 86.0             # a wall more slender than this: «attention» (EC2 12.6.5.1's limit for plain concrete)


def wall(t, h, length, n_top, n_mid, n_base, floors_top, one_side, v_ed, n_least, fck, fyk, cover=COVER_WALL):
    """(0.342) A load-bearing reinforced concrete wall t thick (m), h high (clear), `length` long less its openings,
    by NP EN 1992-1-1, on each metre of it as a column of 1 m × t: n_top, n_mid, n_base its compression on each metre
    at its top, mid-height and base (ULS, kN/m); floors_top: of n_top, the floors' at its top — their bearing's
    eccentricity, as unbalanced as they are on its two sides (one_side: 0 alike … 1 on one side), at a third of its
    thickness from its face (t/6 from its middle); v_ed the horizontal force in its plane (ULS, kN); n_least its
    compression on each metre at its base under the permanent loads alone. Its vertical bars on both faces by its N–M
    diagram — the minimum eccentricity (6.1(4)), the second-order effects of a slender one (l0 = h: held at its top
    and base; nominal curvature, 5.8.8) —, between 0,002 Ac and 0,04 Ac, spaced at most 3t and 40 cm (9.6.2); its
    horizontal ones at least a quarter of those and 0,001 Ac, spaced at most 40 cm (9.6.3), more as shear bars when
    the concrete alone does not take its in-plane shear (6.2.2, 6.2.3 with cot θ = 1, VRd,max). Each face's bars as
    (φ mm, spacing m): design.vertical, design.horizontal."""
    out = Design("wall", cover=cover)
    fcd_, fyd_ = fcd(fck), fyd(fyk)
    t = max(t, 0.05)
    ac = t                                              # m² on each metre
    e0 = max(t / 30.0, 0.02)
    m_top = max(floors_top, 0.0) * one_side * t / 6.0  # kNm/m
    l0 = max(h, 0.01)
    lam = l0 * math.sqrt(12.0) / t
    nrel = max(n_mid, 0.0) / max(ac * fcd_, 1e-9)
    lam_lim = 20.0 * 0.7 * 1.1 * 0.7 / math.sqrt(max(nrel, 1e-6))
    m2 = 0.0
    if lam > lam_lim:                                   # (its second order designed for: as usual in a wall)
        m2 = max(n_mid, 0.0) * (fyd_ / ES) / (0.45 * 0.9 * t) * l0 ** 2 / 10.0
    out.add("wall_slender", WARN if lam > WALL_SLENDER else OK, lam=lam, limit=lam_lim, m2=m2)
    spots = (("top", max(n_top, 0.0), max(m_top, max(n_top, 0.0) * e0)),
             ("mid", max(n_mid, 0.0), max(m_top / 2.0, max(n_mid, 0.0) * e0) + m2),
             ("base", max(n_base, 0.0), max(n_base, 0.0) * e0))
    as_min, as_max = 0.002 * ac, 0.04 * ac
    s_max = min(3.0 * t, 0.40)
    candidates = sorted(((2.0 * bar_area(d) / s, d, s) for d in WALL_BARS for s in WALL_SPACINGS if s <= s_max + 1e-9),
                        key=lambda c: (c[0], c[1]))
    chosen = None
    for area, d, s in candidates:
        if area < as_min - 1e-12:
            continue
        if area > as_max:
            break
        cover_bars = cover + 0.008 + d / 2000.0         # (inside the horizontal bars)
        diagram = interaction_diagram(1.0, t, fck, fyk, area, cover_bars)
        ratios = [interaction_ratio(diagram, n, m) for _spot, n, m in spots]
        if max(ratios) <= 1.0:
            chosen = (d, s, area, ratios)
            break
    if chosen is None:
        out.bump(1.5)
        n, m = max((sp[1:] for sp in spots), key=lambda nm: nm[0])
        out.add("wall_fail", FAIL, n=n, m=m)
        return out
    dv, sv, area_v, ratios = chosen
    for (spot, n, m), ratio in zip(spots, ratios):
        out.bump(ratio)
        out.add("wall_compression", spot=spot, n=n, m=m, ratio=ratio)    # (its bars chosen for it: OK)
    out.vertical = (dv, sv)
    out.add("wall_vertical", d=dv, s=sv, area=area_v, as_min=as_min)
    as_h = max(0.25 * area_v, 0.001 * ac)               # m² on each metre of height, both faces
    if v_ed > 1e-9:
        lw = max(length, 0.10)
        dd = 0.8 * lw
        k = min(1.0 + math.sqrt(0.2 / dd), 2.0)
        sigma = min(max(n_least, 0.0) / ac / 1000.0, 0.2 * fcd_ / 1000.0)      # MPa
        v_rdc = _shear_concrete(k, area_v / ac, fck, t, dd) + 0.15 * sigma * 1000.0 * t * dd
        z = 0.9 * dd
        nu1 = 0.6 * (1.0 - fck / 250.0)
        v_max = t * z * nu1 * fcd_ / 2.0                # (cot θ = 1)
        if v_ed > v_max:
            out.bump(v_ed / v_max)
            out.add("wall_shear_fail", FAIL, v=v_ed, vmax=v_max)
            return out
        if v_ed <= v_rdc:
            out.bump(v_ed / v_rdc)
            out.add("wall_shear", v=v_ed, vrd=v_rdc, sig=sigma, len=lw)
        else:
            need = v_ed / (z * fyd_)                    # m² on each metre of height (cot θ = 1)
            as_h = max(as_h, need)
            out.bump(v_ed / v_max)
            out.add("wall_shear_bars", WARN if v_ed > 0.9 * v_max else OK, v=v_ed, vrd=v_rdc, need=need, vmax=v_max,
                    len=lw)
    else:
        out.add("wall_no_shear")
    dh, sh = _wall_mesh(as_h / 2.0, 0.40)
    out.horizontal = (dh, sh)
    out.add("wall_horizontal", d=dh, s=sh, area=2.0 * bar_area(dh) / sh)
    out.as_bottom = area_v
    return out


def _wall_mesh(area, s_max):
    """(φ, s) on one face of a wall giving `area` (m²/m): the smallest diameter at a spacing ≤ s_max (WALL_SPACINGS)."""
    for d in WALL_BARS:
        for s in WALL_SPACINGS:
            if s <= s_max + 1e-9 and bar_area(d) / s >= area - 1e-12:
                return d, s
    return WALL_BARS[-1], WALL_SPACINGS[-1]


def _mesh(area, choices, s_max):
    """(φ, s): the bars of the smallest diameter at a spacing (≥ 10 cm, ≤ s_max) that give `area` (m²/m)."""
    for dia in choices:
        s = _down(min(bar_area(dia) / max(area, 1e-9), s_max))
        if s >= 0.10:
            return dia, s
    dia = choices[-1]
    return dia, 0.10


# ------------------------------------------------------------ slabs

def slab(lx, ly, thickness, fck, fyk, g, q, cover=COVER_SLAB, moments=None, top=None):
    """A solid slab spanning lx × ly (m) both ways, simply supported on its edges (Marcus: the load shared by
    lx⁴ / ly⁴), under g (kN/m², permanent with its own weight) and q (imposed) — (0.223) or with the moments of
    the analysis (the slab as a shell: Wood–Armer's sagging, kNm/m, its bars along lx and along ly). (0.224) Its top
    bars over its supports, each way: for the analysis's hogging moment (top: (along lx, along ly), kNm/m ≤ 0) and
    at least a quarter of its span's (EC2 9.3.1.2(2): the fixity the beams give), never under the minimum."""
    out = Design("slab", cover=cover)
    short, long_ = max(min(lx, ly), 0.1), max(max(lx, ly), 0.1)
    h = max(thickness, 0.05)
    fcd_, fyd_ = fcd(fck), fyd(fyk)
    if moments is not None:
        mx, my = max(float(moments[0]), 0.0), max(float(moments[1]), 0.0)
        m_short, m_long = (mx, my) if lx <= ly else (my, mx)
        out.add("slab_shell", m_short=m_short, m_long=m_long)
    else:
        p = GAMMA_G * g + GAMMA_Q * q
        share = long_ ** 4 / (short ** 4 + long_ ** 4)     # (what the short span carries)
        m_short = share * p * short ** 2 / 8.0
        m_long = (1.0 - share) * p * long_ ** 2 / 8.0
        out.add("slab_load", p=p, m_short=m_short, m_long=m_long)
    d_short = h - cover - 0.005
    d_long = d_short - 0.010
    as_min = max(0.26 * fctm(fck) / fyk, 0.0013) * d_short
    s_max = min(2.0 * h, 0.25)
    meshes = {}
    for axis, m, d in (("short", m_short, d_short), ("long", m_long, d_long)):
        need, mu = _flexure(m, 1.0, max(d, 0.02), fcd_, fyd_)
        out.bump(mu / MU_MAX)
        if mu > MU_MAX:
            out.add("bending_fail", FAIL, face=axis, mu=mu)
            return out
        area = max(need, as_min)
        meshes[axis] = _mesh(area, MESH_BARS, s_max)
        out.add("mesh", face=axis, m=m, need=need, area=area, d=meshes[axis][0], s=meshes[axis][1])
    # mesh_x along lx (its bars span lx), mesh_y along ly
    out.mesh_x = meshes["short"] if lx <= ly else meshes["long"]
    out.mesh_y = meshes["long"] if lx <= ly else meshes["short"]
    out.as_bottom = bar_area(meshes["short"][0]) / meshes["short"][1]
    rho = out.as_bottom / d_short
    limit = span_depth_limit(rho, 0.0, fck, 1.0)
    ratio = short / d_short
    out.bump(ratio / limit)
    out.add("slenderness", WARN if ratio > limit else OK, ratio=ratio, limit=limit)
    # (0.224) the top bars over the supports, each way: bars along x for the moment along lx
    span_x, span_y = (m_short, m_long) if lx <= ly else (m_long, m_short)
    hog = (0.0, 0.0) if top is None else (abs(min(float(top[0]), 0.0)), abs(min(float(top[1]), 0.0)))
    d_top = h - cover - 0.005
    for axis, m_hog, m_span in (("x", hog[0], span_x), ("y", hog[1], span_y)):
        m = max(m_hog, TOP_SHARE * m_span)
        need, mu = _flexure(m, 1.0, max(d_top, 0.02), fcd_, fyd_)
        out.bump(mu / MU_MAX)
        if mu > MU_MAX:
            out.add("bending_fail", FAIL, face="top", mu=mu)
            return out
        area = max(need, as_min)
        mesh = _mesh(area, MESH_BARS, s_max)
        setattr(out, "top_" + axis, mesh)
        out.add("slab_top_mesh", face=axis, m=m, quarter=TOP_SHARE * m_span, need=need, area=area, d=mesh[0],
                s=mesh[1])
    out.as_top = bar_area(out.top_x[0]) / out.top_x[1]
    out.add("slab_top")
    return out
