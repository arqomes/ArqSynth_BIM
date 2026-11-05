"""Actions on a structure (0.164, Phase 9, step 2) — the Eurocodes with Portugal's National Annexes, for
pre-design: materials (NP EN 1992-1-1), imposed loads by use and their ψ (NP EN 1991-1-1, EN 1990 A1.1), wind's peak
pressure (NP EN 1991-1-4), the seismic action's lateral forces (NP EN 1998-1: zones, ground types, the lateral force
method), the snow on the roof (0.217: NP EN 1991-1-3) and the combinations (EN 1990 6.10, 6.14b, 6.12b). Built on the ArqSynth Modeler's calc_eurocode; pure
Python (numbers in kN, m, kPa).

What it gives is a pre-design: a project's calculations are a structural engineer's, signed by them."""

import math
from dataclasses import dataclass

GAMMA_G, GAMMA_Q = 1.35, 1.50
GAMMA_C, GAMMA_S = 1.5, 1.15
CONCRETE_KN_M3 = 25.0
GRAVITY = 9.81
AIR_DENSITY = 1.25              # kg/m³

CONCRETE = {"C20/25": 20, "C25/30": 25, "C30/37": 30, "C35/45": 35, "C40/50": 40, "C45/55": 45, "C50/60": 50}
STEEL = {"A400": 400, "A500": 500}

# imposed loads (kN/m²) and their ψ0, ψ1, ψ2 — NP EN 1991-1-1 (NA) and EN 1990 Table A1.1
USES = {
    "A": (2.0, 0.7, 0.5, 0.3),          # housing
    "B": (3.0, 0.7, 0.5, 0.3),          # offices
    "C1": (3.0, 0.7, 0.7, 0.6),         # with tables (cafés, schools)
    "C2": (4.0, 0.7, 0.7, 0.6),         # with fixed seats (churches, theatres)
    "C3": (5.0, 0.7, 0.7, 0.6),         # free to move (museums, halls)
    "D1": (4.0, 0.7, 0.7, 0.6),         # shops
    "E1": (7.5, 1.0, 0.9, 0.8),         # storage
    "H": (0.4, 0.0, 0.0, 0.0),          # roofs not accessible
}
WIND_PSI = (0.6, 0.2, 0.0)

# (0.217) snow (NP EN 1991-1-3, NA): on the ground sk = Cz [1 + (H/500)²], Cz of the zone (Z3: the islands); on a
# roof s = μ1 Ce Ct sk (Ce = Ct = 1), μ1 by the roof's slope (Table 5.2); its ψ (EN 1990 Table A1.1)
SNOW_ZONES = {"Z1": 0.30, "Z2": 0.20, "Z3": 0.10}
SNOW_PSI = (0.5, 0.2, 0.0)                  # (sites up to 1000 m)
SNOW_PSI_HIGH = (0.7, 0.5, 0.2)             # (over 1000 m)

# wind: the basic velocity by zone (NP EN 1991-1-4, NA: zone A 27 m/s, B 30 m/s); the terrain categories' roughness
# length and minimum height — the National Annex's (0.219: confirmed): four categories, none 0 (Quadro NA-4.1:
# I coast exposed to the sea's winds 0,005 m / 1 m, II 0,05 / 3, III 0,3 / 8, IV 1,0 / 15)
WIND_ZONES = {"A": 27.0, "B": 30.0}
TERRAIN = {"I": (0.005, 1.0), "II": (0.05, 3.0), "III": (0.3, 8.0), "IV": (1.0, 15.0)}
TERRAIN_OLD = {"0": "I"}        # (a project of before 0.219 with the EN's category 0: the NA's I, its sea coast)

# earthquake (NP EN 1998-1, NA): the reference peak ground acceleration (m/s²) of each zone, for the action of type 1
# (far) and type 2 (near); the ground types' S max (the same for both, NA Table NA-3.2 / 3.3)
SEISMIC_ZONES = {"1.1": 2.5, "1.2": 2.0, "1.3": 1.5, "1.4": 1.0, "1.5": 0.6, "1.6": 0.35,
                 "2.1": 2.5, "2.2": 2.0, "2.3": 1.7, "2.4": 1.1, "2.5": 0.8}
GROUND_S_MAX = {"A": 1.0, "B": 1.35, "C": 1.6, "D": 2.0, "E": 1.8}
GROUND_PERIODS = {        # (TB, TC, TD) s — action type 1 / type 2 (NA Quadros NA-3.2, NA-3.3)
    1: {"A": (0.1, 0.6, 2.0), "B": (0.1, 0.6, 2.0), "C": (0.1, 0.6, 2.0), "D": (0.1, 0.8, 2.0),
        "E": (0.1, 0.6, 2.0)},
    2: {"A": (0.1, 0.25, 2.0), "B": (0.1, 0.25, 2.0), "C": (0.1, 0.25, 2.0), "D": (0.1, 0.3, 2.0),
        "E": (0.1, 0.25, 2.0)},
}
IMPORTANCE = {"I": 0.65, "II": 1.0, "III": 1.45, "IV": 1.95}    # γI for the action of type 1 (NA)
IMPORTANCE_2 = {"I": 0.75, "II": 1.0, "III": 1.25, "IV": 1.50}  # …of type 2
BEHAVIOUR_Q = 2.0               # q of a concrete frame of medium ductility, regular — kept low (on the safe side)
LAMBDA = 0.85                   # the lateral force method's correction (T1 <= 2 TC, more than two storeys)
SLAB_MODELS = ("shells", "areas")   # (0.223) the slabs as shells, or their loads carried to the beams by areas


@dataclass
class Settings:
    """A project's structural settings (kept with its building in the IFC)."""
    concrete: str = "C25/30"
    steel: str = "A500"
    use: str = "A"
    finishes: float = 1.5           # kN/m²: floor finishes, ceilings
    partitions: float = 1.0         # kN/m²: light partitions (spread)
    roof_use: str = "H"
    wind_zone: str = "A"
    terrain: str = "III"
    seismic_zone_1: str = "1.4"
    seismic_zone_2: str = "2.4"
    ground: str = "B"
    importance: str = "II"
    soil_kpa: float = 200.0          # allowable bearing pressure
    snow_zone: str = "Z1"            # (0.217) NP EN 1991-1-3 NA
    altitude: float = 0.0            # m: the site's height over the sea (for the snow)
    slabs: str = "shells"            # (0.223) the slabs in the analysis: "shells" (finite elements) or "areas"
    # (0.337) the load-bearing walls' masonry (core/ec6.py): its units (clay, concrete, calcium silicate, aerated
    # concrete) and their group (EN 1996-1-1 table 3.1), their normalised strength fb (N/mm²), the mortar, γM
    masonry_unit: str = "clay"
    masonry_group: str = "2"
    masonry_fb: float = 10.0
    masonry_mortar: str = "M5"
    masonry_gamma: float = 2.5

    def fcd(self):
        return CONCRETE[self.concrete] / GAMMA_C * 1000.0          # kPa

    def fyd(self):
        return STEEL[self.steel] / GAMMA_S * 1000.0

    def ecm(self):
        """The concrete's secant modulus (EC2 3.1.3), kPa."""
        fck = CONCRETE[self.concrete]
        return 22000.0 * ((fck + 8.0) / 10.0) ** 0.3 * 1000.0

    def snow(self):
        """(0.217) The snow on a flat roof (kN/m²)."""
        return snow_roof(snow_ground(self.snow_zone, self.altitude))

    def imposed(self, roof=False):
        """The imposed load (kN/m²) of a floor by its use — of the roof (0.217), the greater of its use's and the
        snow on it (NP EN 1991-1-1 3.3.2: a roof's imposed load is not taken with the snow)."""
        if roof:
            return max(USES[self.roof_use][0], self.snow())
        return USES[self.use][0]

    def psi(self, roof=False):
        """ψ0, ψ1, ψ2 of that load (the roof's: of the one that governs)."""
        if roof and self.snow() > USES[self.roof_use][0]:
            return SNOW_PSI_HIGH if self.altitude > 1000.0 else SNOW_PSI
        return USES[self.roof_use if roof else self.use][1:]


def snow_ground(zone="Z1", altitude=0.0):
    """(0.217) The snow's characteristic load on the ground sk (kN/m²): Cz [1 + (H/500)²] (NP EN 1991-1-3, NA)."""
    return SNOW_ZONES[zone] * (1.0 + (max(float(altitude), 0.0) / 500.0) ** 2)


def snow_shape(slope=0.0):
    """(0.217) μ1 of a monopitch / duopitch roof sloping `slope` degrees (EN 1991-1-3 Table 5.2): 0,8 to 30°, then
    down to 0 at 60°."""
    a = abs(float(slope))
    if a <= 30.0:
        return 0.8
    return 0.0 if a >= 60.0 else 0.8 * (60.0 - a) / 30.0


def snow_roof(sk, slope=0.0, ce=1.0, ct=1.0):
    """(0.217) The snow on a roof (kN/m²): μ1 Ce Ct sk."""
    return snow_shape(slope) * ce * ct * sk


def peak_pressure(z, zone="A", terrain="III", c0=1.0):
    """The wind's peak velocity pressure qp(z) (kPa) at the height z over the ground (EN 1991-1-4 4.5)."""
    z0, zmin = TERRAIN[TERRAIN_OLD.get(terrain, terrain)]
    vb = WIND_ZONES[zone]
    kr = 0.19 * (z0 / 0.05) ** 0.07
    ze = max(float(z), zmin)
    cr = kr * math.log(ze / z0)
    vm = cr * c0 * vb
    iv = 1.0 / (c0 * math.log(ze / z0))
    return (1.0 + 7.0 * iv) * 0.5 * AIR_DENSITY * vm * vm / 1000.0


def wind_storey_forces(levels, widths, zone="A", terrain="III", cf=1.3):
    """The wind's force on each storey (kN), one way: its pressure at the storey's top times its facade's strip
    (half the heights to the storeys below and above) times its width across the wind. levels: the storeys' heights
    over the ground (lowest first, the roof last); widths: the building's width across the wind at each."""
    out = []
    for k, z in enumerate(levels):
        below = (z - levels[k - 1]) / 2 if k > 0 else z / 2
        above = (levels[k + 1] - z) / 2 if k + 1 < len(levels) else 0.0
        strip = max(below + above, 0.0)
        out.append(peak_pressure(z, zone, terrain) * cf * widths[k] * strip)
    return out


def ground_s(ag, ground):
    """S of the ground type for the design acceleration ag (NA: Smax up to 1 m/s², 1 from 4 m/s², linear between)."""
    smax = GROUND_S_MAX[ground]
    if ag <= 1.0:
        return smax
    if ag >= 4.0:
        return 1.0
    return smax - (smax - 1.0) * (ag - 1.0) / 3.0


def design_spectrum(t, ag, ground, action=1, q=BEHAVIOUR_Q):
    """Sd(T) (m/s²) of the design spectrum (EN 1998-1 3.2.2.5), β = 0.2."""
    tb, tc, td = GROUND_PERIODS[action][ground]
    s = ground_s(ag, ground)
    if t <= tb:
        sd = ag * s * (2.0 / 3.0 + t / tb * (2.5 / q - 2.0 / 3.0))
    elif t <= tc:
        sd = ag * s * 2.5 / q
    elif t <= td:
        sd = ag * s * 2.5 / q * tc / t
    else:
        sd = ag * s * 2.5 / q * tc * td / (t * t)
    return max(sd, 0.2 * ag)


def period_estimate(height):
    """The building's first period (s): T1 = Ct H^(3/4), Ct = 0.075 for concrete frames (EN 1998-1 4.6)."""
    return 0.075 * max(height, 0.1) ** 0.75


def seismic_storey_forces(levels, weights, settings, action=1):
    """The lateral forces on each storey (kN) of the seismic action of type 1 or 2 (the lateral force method, EN
    1998-1 4.3.3.2): Fb = Sd(T1) m λ, spread by height (Fi = Fb zi mi / Σ zj mj). levels: the storeys' heights over the
    foundations; weights: their seismic weights (kN: G + ψ2 Q). Returns (Fb, [Fi], T1, Sd)."""
    zone = settings.seismic_zone_1 if action == 1 else settings.seismic_zone_2
    gamma = (IMPORTANCE if action == 1 else IMPORTANCE_2)[settings.importance]
    ag = SEISMIC_ZONES[zone] * gamma
    height = max(levels) if levels else 0.0
    t1 = period_estimate(height)
    sd = design_spectrum(t1, ag, settings.ground, action)
    total = sum(weights)
    lam = LAMBDA if len(levels) > 2 else 1.0
    fb = sd * total / GRAVITY * lam
    sz = sum(z * w for z, w in zip(levels, weights)) or 1.0
    return fb, [fb * z * w / sz for z, w in zip(levels, weights)], t1, sd


def combinations(settings, wind=True, seismic=True):
    """The ultimate combinations (EN 1990 6.10, PT NA; seismic 6.12b): [(name, {case: factor})] — G, Q, W (±), E
    (±). And the quasi-permanent one (6.16b) for deflections, last."""
    psi0, _psi1, psi2 = settings.psi()
    out = [("1,35G+1,50Q", {"G": GAMMA_G, "Q": GAMMA_Q})]
    if wind:
        for sign, tag in ((1.0, "+"), (-1.0, "−")):
            out.append(("1,35G+1,50Q{}{:g}W".format(tag, 1.5 * WIND_PSI[0]).replace(".", ","),
                        {"G": GAMMA_G, "Q": GAMMA_Q, "W": 1.5 * WIND_PSI[0] * sign}))
            out.append(("1,35G+{:g}Q{}1,50W".format(1.5 * psi0, tag).replace(".", ","),
                        {"G": GAMMA_G, "Q": 1.5 * psi0, "W": 1.5 * sign}))
    if seismic:
        for sign, tag in ((1.0, "+"), (-1.0, "−")):
            out.append(("G+{:g}Q{}E".format(psi2, tag).replace(".", ","), {"G": 1.0, "Q": psi2, "E": sign}))
    out.append(("G+{:g}Q (qp)".format(psi2).replace(".", ","), {"G": 1.0, "Q": psi2}))
    return out
