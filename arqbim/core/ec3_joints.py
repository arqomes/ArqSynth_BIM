"""(0.520) Steel connections checked by Eurocode 3, part 1-8 — NP EN 1993-1-8 and its National Annex (γM2 = 1,25):
bolts of class 8.8 in shear (the shear plane through the thread), in bearing on the thinner part, in tension and in
shear with tension (Table 3.4); fillet welds by the simplified method (4.5.3.3). For pre-design: the forces a
connection takes come from its pieces' ends (model/steel_connection_check), shared by its bolts. Pure Python: N, mm
(the forces in kN)."""

import math

GAMMA_M2 = 1.25
FUB, FYB = 800.0, 640.0                   # N/mm²: class 8.8
STRESS_AREA = {12: 84.3, 16: 157.0, 20: 245.0, 24: 353.0, 27: 459.0, 30: 561.0, 36: 817.0, 42: 1120.0, 48: 1470.0}
BETA_W = {"S235": 0.80, "S275": 0.85, "S355": 0.90, "S460": 1.00}
FU = {"S235": 360.0, "S275": 430.0, "S355": 490.0, "S460": 540.0}


def stress_area(d):
    """A bolt's tensile stress area (mm²) — the nearest size's (ISO 898-1)."""
    size = min(STRESS_AREA, key=lambda k: abs(k - d))
    return STRESS_AREA[size]


def shear_rd(d):
    """Fv,Rd (kN) a bolt in single shear, the plane through its thread: 0,6 fub As / γM2."""
    return 0.6 * FUB * stress_area(d) / GAMMA_M2 / 1000.0


def tension_rd(d):
    """Ft,Rd (kN): 0,9 fub As / γM2."""
    return 0.9 * FUB * stress_area(d) / GAMMA_M2 / 1000.0


def bearing_rd(d, d0, t, grade, e1):
    """Fb,Rd (kN) on a part `t` mm thick of `grade`: k1 αb fu d t / γM2 — k1 2,5 (the edges across at least 1,5 d0),
    αb the least of e1 / 3 d0, fub / fu and 1."""
    fu = FU.get(grade, 430.0)
    ab = min(e1 / (3.0 * d0), FUB / fu, 1.0)
    return 2.5 * ab * fu * d * t / GAMMA_M2 / 1000.0


def weld_rd(a, grade):
    """Fw,Rd (kN/mm) of a fillet weld of throat `a` mm along its length: fu / (√3 βw γM2) × a."""
    fu = FU.get(grade, 430.0)
    return fu / (math.sqrt(3.0) * BETA_W.get(grade, 0.85) * GAMMA_M2) * a / 1000.0


def check_bolts(d, d0, t, grade, e1, shear, tension=0.0):
    """One bolt's checks: its shear force and its tension (kN) against its resistances — {"util", "check",
    "ratios"}: shear «Fv», bearing «Fb», tension «Ft», both «FvFt» (Table 3.4: Fv/Fv,Rd + Ft/1,4 Ft,Rd)."""
    fv, fb, ft = shear_rd(d), bearing_rd(d, d0, t, grade, e1), tension_rd(d)
    ratios = {"Fv": shear / fv, "Fb": shear / fb}
    if tension > 0.0:
        ratios["Ft"] = tension / ft
        ratios["FvFt"] = shear / fv + tension / (1.4 * ft)
    name, util = max(ratios.items(), key=lambda kv: kv[1])
    return {"util": util, "check": name, "ratios": ratios, "fv_rd": fv, "fb_rd": fb, "ft_rd": ft}


def check_weld(force, length, a, grade):
    """A fillet weld carrying `force` kN along `length` mm, throat `a` mm: {"util", "check": "Fw"}."""
    if length <= 0.0 or a <= 0.0:
        return {"util": 0.0, "check": "Fw"}
    return {"util": force / (weld_rd(a, grade) * length), "check": "Fw"}
