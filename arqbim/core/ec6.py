"""Eurocode 6 verification of load-bearing masonry walls (0.337, step 3 of «Paredes resistentes no cálculo») —
NP EN 1996-1-1, for pre-design, with the loads of model/wall_loads.py:

- the masonry's strength from its units and mortar: fk = K fb^0,7 fm^0,3 (3.6.1.2, general purpose mortar; K of
  table 3.3 by the units' material and group), fd = fk / γM; its initial shear strength fvk0 (table 3.4);
- each wall's slenderness hef / tef ≤ 27 (5.5.1.4), hef = ρ2 h with ρ2 = 0,75 — held at its top and its base by
  concrete floors (5.5.1.2);
- its compression on each metre at its top, at mid-height and at its base, NRd = Φ t fd (6.1.2.1): at the top and
  the base Φ = 1 − 2 e/t (6.1.2.2), e the floors' eccentricity (their load at a third of their bearing from the face,
  as unbalanced as they are on its two sides) plus the initial one hef/450, at least 0,05 t; at mid-height Φm of
  annex G, with half the top's moment and the creep's ek (6.1.2.2(2): none up to a slenderness of 15);
- its shear in its plane, VRd = fvd t lc (6.2), fvk = fvk0 + 0,4 σd ≤ 0,065 fb (3.6.2), σd from its own and the
  permanent loads alone, lc its length less its openings;
- (0.345) a façade wall's bending out of its plane under the wind (6.3.1, annex E): its panel's moment per metre by
  the yield lines annex E's coefficients come from — its edges held (simply, on the safe side) or free, the
  orthogonal ratio μ = fxd1 / fxd2 — against MRd = fxd Z, Z = t²/6; fxk1 and fxk2 the recommended values of table 3.4
  (by the units and the mortar), fxd1 raised by the permanent vertical stress (6.3.1(3): fxd1,app = fxd1 + σd). When
  that is not enough and the wall is held at its top (built tight under a slab or a beam), the arch in its thickness
  between its base and its top (6.3.2): qlat = fd (t/h)², up to h/t = 25.

Each a note (core.ec2.Note: a code and its numbers), the status OK / attention / failure as core.ec2's. Pure Python
(kN, m; strengths in N/mm²). What it gives is a pre-design: the structural design is the engineer's, who signs it."""

import math

from . import ec2

UNITS = ("clay", "concrete", "calcium_silicate", "aac")
GROUPS = ("1", "2", "3", "4")
MORTARS = {"M2.5": 2.5, "M5": 5.0, "M7.5": 7.5, "M10": 10.0, "M15": 15.0, "M20": 20.0}
# K of table 3.3 (general purpose mortar), by the units' material and group
K = {("clay", "1"): 0.55, ("clay", "2"): 0.45, ("clay", "3"): 0.35, ("clay", "4"): 0.35,
     ("concrete", "1"): 0.55, ("concrete", "2"): 0.52, ("concrete", "3"): 0.45, ("concrete", "4"): 0.45,
     ("calcium_silicate", "1"): 0.55, ("calcium_silicate", "2"): 0.45, ("aac", "1"): 0.55}
ALPHA, BETA = 0.7, 0.3
K_E = 1000.0                    # E = KE fk (3.7.2)
RHO_2 = 0.75                    # hef = ρ2 h: held at top and base by concrete floors (5.5.1.2)
SLENDER_MAX = 27.0              # hef / tef (5.5.1.4)
SLENDER_NO_CREEP = 15.0         # up to it, ek = 0 (6.1.2.2(2))
E_INIT = 450.0                  # einit = hef / 450 (5.5.1.1(4))
CREEP = {"clay": 1.0, "concrete": 1.5, "calcium_silicate": 1.5, "aac": 1.0}    # φ∞ (table 3.8, a middle value)
FVLT = 0.065                    # fvk ≤ 0,065 fb (3.6.2(3), recommended)
NEAR = 0.9                      # a utilisation beyond this: «attention»
# (0.345) the flexural strengths (N/mm², general purpose mortar; table 3.4, recommended): fxk1 — the plane of failure
# parallel to the bed joints — and fxk2 — perpendicular to them —, with a mortar weaker than M5 and from M5 on
FLEXURAL = {"clay": ((0.10, 0.20), (0.10, 0.40)), "concrete": ((0.05, 0.20), (0.10, 0.40)),
            "calcium_silicate": ((0.05, 0.20), (0.10, 0.40)), "aac": ((0.05, 0.20), (0.10, 0.40))}
WEIGHT = {"clay": 13.0, "concrete": 20.0, "calcium_silicate": 18.0, "aac": 6.0}   # kN/m³ of the masonry (its own)
# the edges a panel is held on beside its base (always): (its top, how many of its sides) -> its key
EDGES = {(True, 2): "all", (True, 1): "top_side", (True, 0): "top", (False, 2): "sides", (False, 1): "side",
         (False, 0): "base"}
STEPS = 400                     # the yield lines' positions tried
ARCHED = ("all", "top_side", "top")     # (0.345) held at its top: a vertical arch in its thickness (6.3.2)…
ARCH_SLENDER = 25.0             # …up to h/t so much (its deflection small)


def strength(settings):
    """(fk, fd, fvk0, fb) in N/mm² of the project's masonry (core.actions.Settings: its units, group, fb, mortar,
    γM)."""
    unit, group = settings.masonry_unit, str(settings.masonry_group)
    k = K.get((unit, group), K.get((unit, "1"), 0.45))
    fb = float(settings.masonry_fb)
    fm = min(MORTARS.get(settings.masonry_mortar, 5.0), 20.0, 2.0 * fb)
    fk = k * fb ** ALPHA * fm ** BETA
    if unit == "clay":
        fvk0 = 0.30 if fm >= 10.0 else 0.20 if fm >= 2.5 else 0.10
    else:
        fvk0 = 0.20 if fm >= 10.0 else 0.15 if fm >= 2.5 else 0.10
    return fk, fk / float(settings.masonry_gamma), fvk0, fb


def encode(masonry):
    """(0.346) A wall type's own masonry (units, group, fb, mortar) as its parameter keeps it: "unit=clay;group=2;fb=10;
    mortar=M5" ("" none: the project's)."""
    if not masonry:
        return ""
    unit, group, fb, mortar = masonry
    return "unit={};group={};fb={:g};mortar={}".format(unit, group, float(fb), mortar)


def decode(text):
    """(0.346) (units, group, fb, mortar) from a wall type's parameter, or None (none, or not understood)."""
    values = dict(part.partition("=")[::2] for part in str(text or "").split(";") if "=" in part)
    try:
        masonry = (values["unit"], values["group"], float(values["fb"]), values["mortar"])
    except (KeyError, ValueError):
        return None
    if masonry[0] not in UNITS or masonry[1] not in GROUPS or masonry[3] not in MORTARS or masonry[2] <= 0:
        return None
    return masonry


def with_masonry(settings, masonry):
    """(0.346) The project's settings with a wall type's own masonry (units, group, fb, mortar) — its γM the
    project's (its execution class); None: as they are."""
    if not masonry:
        return settings
    from dataclasses import replace
    unit, group, fb, mortar = masonry
    return replace(settings, masonry_unit=unit, masonry_group=str(group), masonry_fb=float(fb), masonry_mortar=mortar)


def flexural(settings):
    """(0.345) (fxk1, fxk2) in N/mm² of the project's masonry (table 3.4, recommended values)."""
    fm = MORTARS.get(settings.masonry_mortar, 5.0)
    weak, strong = FLEXURAL.get(settings.masonry_unit, FLEXURAL["clay"])
    return strong if fm >= 5.0 else weak


def edges_key(top, left, right):
    """(0.345) The key (EDGES) of a panel held at its base and so at its top and sides."""
    return EDGES[(bool(top), int(bool(left)) + int(bool(right)))]


def _four_sides(a, b):
    """m / q of an isotropic panel a × b simply supported on its four edges (Johansen)."""
    s, l = min(a, b), max(a, b)
    r = s / l
    return s * s / 24.0 * (math.sqrt(3.0 + r * r) - r) ** 2


def _three_sides(free, depth):
    """m / q of an isotropic panel simply supported on three edges, its fourth (`free` long) free, `depth` from it to
    the edge across: the greater of two yield-line patterns — two lines from the held corners meeting inside, a third
    on to the free edge (Y), or the two reaching the free edge (the middle part turning on the edge across)."""
    best = 0.0
    for k in range(1, STEPS + 1):
        y = depth * k / STEPS                        # (Y: where the lines meet, from the edge across)
        best = max(best, free * (depth / 2.0 - y / 6.0) / (free / y + 4.0 * depth / free))
        c = free / 2.0 * k / STEPS                   # (where they reach the free edge, from its ends)
        best = max(best, (free * depth / 2.0 - c * depth / 3.0) / (free / depth + 2.0 * depth / c))
    return best


def _two_sides(a, b):
    """m / q of an isotropic panel a × b simply supported on two adjacent edges (the other two free): one yield line
    from their corner to a point of a free edge."""
    best = 0.0
    for k in range(1, STEPS + 1):
        c, e = a * k / STEPS, b * k / STEPS
        best = max(best, (a * b / 2.0 - c * b / 6.0) / (a / b + b / c), (a * b / 2.0 - e * a / 6.0) / (b / a + a / e))
    return best


def panel_moment(length, height, mu, edges):
    """(0.345) The moment (kNm/m per kPa) about a vertical axis — the plane of failure perpendicular to the bed joints,
    M2 — of a masonry panel `length` × `height` held at its base and on `edges` (EDGES' key), its orthogonal ratio μ =
    fxd1 / fxd2 (M1 = μ M2): by the yield lines, on the isotropic panel of the same moment whose height is height / √μ
    (Johansen's affinity) — annex E's coefficient α2 is this over length²."""
    h = height / math.sqrt(max(mu, 1e-6))
    l = length
    if edges == "all":
        return _four_sides(l, h)
    if edges == "sides":                             # (its top free)
        return _three_sides(l, h)
    if edges == "top_side":                          # (one side free: a free edge `h` long, `l` from the side held)
        return _three_sides(h, l)
    if edges == "top":                               # (spanning from its base to its top)
        return h * h / 8.0
    if edges == "side":                              # (its base and one side)
        return _two_sides(l, h)
    return h * h / 2.0                               # (only its base: standing out of it)


def _status(ratio):
    return ec2.OK if ratio <= NEAR else ec2.WARN if ratio <= 1.0 else ec2.FAIL


def _sign(ratio):
    """The note's comparison: «≤» when it holds, «>» when it fails."""
    return "≤" if ratio <= 1.0 else ">"


def phi_mid(e_mk, t, slenderness):
    """Φm at mid-height (annex G): A1 e^(−u²/2), A1 = 1 − 2 emk/t, u = (λ − 0,063) / (0,73 − 1,17 emk/t), λ =
    (hef/tef) √(fk/E)."""
    a1 = 1.0 - 2.0 * e_mk / t
    lam = slenderness / math.sqrt(K_E)
    u = (lam - 0.063) / (0.73 - 1.17 * e_mk / t)
    return max(0.0, a1 * math.exp(-u * u / 2.0))


def wall(t, h, length, n_top, n_mid, n_base, floors_top, one_side, v_ed, n_least, settings, hef=None, own=False):
    """A load-bearing masonry wall verified (core.ec2.Design, kind "wall"). t: its load-bearing thickness (m); h: its
    clear height; length: less its openings; n_top, n_mid, n_base: its compression on each metre (ULS, kN/m);
    floors_top: of n_top, the floors' at its top (their bearing's eccentricity); one_side: 0 the floors alike on its
    two sides … 1 on one side only; v_ed: the horizontal force in its plane (ULS, kN); n_least: its compression on
    each metre at its base under the permanent loads alone (the shear's). own (0.346): the masonry in `settings` its
    type's own (with_masonry), not the project's."""
    d = ec2.Design("wall")
    fk, fd, fvk0, fb = strength(settings)
    gamma = float(settings.masonry_gamma)
    d.add("ec6_material", unit=settings.masonry_unit, group=str(settings.masonry_group),
          src="type" if own else "project", fb=fb, mortar=settings.masonry_mortar, fk=fk, fd=fd, gm=gamma)
    hef = RHO_2 * h if hef is None else hef
    slender = hef / t if t > 0 else float("inf")
    d.add("ec6_slender", ec2.OK if slender <= SLENDER_MAX else ec2.FAIL, slender=slender, limit=SLENDER_MAX)
    e_init = hef / E_INIT
    m_top = floors_top * one_side * t / 6.0                     # kNm/m: the floors' load at a third of their bearing
    least = 0.05 * t
    e_top = max((m_top / n_top if n_top > 1e-9 else 0.0) + e_init, least)
    e_base = max(e_init, least)
    e_m = (m_top / 2.0 / n_mid if n_mid > 1e-9 else 0.0) + e_init
    e_k = 0.002 * CREEP.get(settings.masonry_unit, 1.0) * slender * math.sqrt(t * e_m) \
        if slender > SLENDER_NO_CREEP else 0.0
    e_mk = max(e_m + e_k, least)
    rows = (("top", max(0.0, 1.0 - 2.0 * e_top / t), n_top, e_top),
            ("mid", phi_mid(e_mk, t, slender), n_mid, e_mk),
            ("base", max(0.0, 1.0 - 2.0 * e_base / t), n_base, e_base))
    for spot, phi, n, e in rows:
        n_rd = phi * t * fd * 1000.0                             # kN/m (fd in N/mm² = MPa: × 1000 kPa)
        ratio = n / n_rd if n_rd > 1e-9 else (float("inf") if n > 0 else 0.0)
        d.bump(min(ratio, 9.99))
        d.add("ec6_compression", _status(ratio), spot=spot, n=n, nrd=n_rd, phi=phi, ecc=e, sign=_sign(ratio))
    if v_ed > 1e-9:
        sigma = max(n_least, 0.0) / t / 1000.0 if t > 0 else 0.0   # N/mm²
        fvk = min(fvk0 + 0.4 * sigma, FVLT * fb)
        v_rd = fvk / gamma * 1000.0 * t * length                    # kN
        ratio = v_ed / v_rd if v_rd > 1e-9 else float("inf")
        d.bump(min(ratio, 9.99))
        d.add("ec6_shear", _status(ratio), v=v_ed, vrd=v_rd, fvk=fvk, sig=sigma, len=length, sign=_sign(ratio))
    else:
        d.add("ec6_no_shear")
    return d


def lateral(t, length, height, qp, c, z, factor, sigma, edges, settings, design=None, gamma_q=1.5, own=False):
    """(0.345) A façade wall's bending out of its plane under the wind (6.3.1, annex E), verified: added to `design` (a
    load-bearing wall's), else a Design of its own (kind "wall": an enclosing or infill wall, this its only check). t:
    its masonry's thickness (m); length × height: its panel; qp: the wind's peak pressure at its top (kPa), `z` m over
    the ground; c: the walls' net pressure coefficient there (outside and inside); factor: its whole area over its
    area less its openings (their wind comes to it); sigma: its permanent vertical stress at mid-height (N/mm²); edges:
    the edges it is held on (EDGES' key); own (0.346): its type's masonry, not the project's."""
    d = design if design is not None else ec2.Design("wall")
    fxk1, fxk2 = flexural(settings)
    gamma = float(settings.masonry_gamma)
    sigma = max(float(sigma), 0.0)
    fxd1, fxd2 = fxk1 / gamma + sigma, fxk2 / gamma
    mu = fxd1 / fxd2
    d.add("ec6_flexural", unit=settings.masonry_unit, src="type" if own else "project", mortar=settings.masonry_mortar,
          f1=fxk1, f2=fxk2, gm=gamma, sig=sigma, fd1=fxd1, fd2=fxd2, ortho=mu, fk=strength(settings)[0])
    w_ed = gamma_q * qp * c * factor
    if factor > 1.0 + 1e-6:
        d.add("ec6_wind", qp=qp, c=c, z=z, open=factor, w=w_ed)
    else:                                                        # (no openings in it)
        d.add("ec6_wind_solid", qp=qp, c=c, z=z, w=w_ed)
    section = t * t / 6.0                                        # m³/m
    m2 = w_ed * panel_moment(length, height, mu, edges)          # kNm/m
    rd1, rd2 = fxd1 * 1000.0 * section, fxd2 * 1000.0 * section
    ratio = m2 / rd2 if rd2 > 1e-12 else float("inf")
    values = dict(edges=edges, len=length, h=height, me1=mu * m2, me2=m2, mr1=rd1, mr2=rd2,
                  alpha=m2 / (w_ed * length * length) if w_ed > 0 and length > 0 else 0.0, sign=_sign(ratio))
    arch = None
    if ratio > 1.0 and edges in ARCHED and height / t <= ARCH_SLENDER:
        q_lat = strength(settings)[1] * 1000.0 * (t / height) ** 2              # kPa (6.3.2(4))
        arch = w_ed / q_lat if q_lat > 1e-12 else float("inf")
    if arch is None or arch >= ratio:
        d.bump(min(ratio, 9.99))
        d.add("ec6_lateral", _status(ratio), **values)
    else:                               # (its bending not enough: the arch in its thickness, held at its top, takes it)
        d.add("ec6_lateral_over", **values)
        d.bump(min(arch, 9.99))
        d.add("ec6_arch", _status(arch), w=w_ed, q=q_lat, ht=height / t, limit=ARCH_SLENDER, sign=_sign(arch))
    return d
