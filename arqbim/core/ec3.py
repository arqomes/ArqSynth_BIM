"""(0.516) Steel members checked by Eurocode 3 — NP EN 1993-1-1 and its National Annex (γM0 = γM1 = 1,00), for
pre-design, the plan's step 8: a cross-section's class (Table 5.2), its resistances (6.2: tension or compression,
bending about both axes, shear, and their interaction — the linear one of 6.2.1(7), on the safe side), a member's
flexural buckling (6.3.1: the curves a0 to d of Table 6.1, chosen by Table 6.2) and a member in compression and
bending (6.3.3, Annex B's interaction factors with Cm = 1). Lateral-torsional buckling is not checked here: the
purlins and the bracing are taken to restrain the compression flange — said with the result. Cold-formed sections (C,
Z, Ω) are checked with their elastic modulus as class 3: EN 1993-1-3 is not applied — said too.

What it gives is a pre-design: a project's calculations are a structural engineer's, signed by them. Pure Python:
N, mm (the results in kN, kN·m)."""

import math

from . import steel

GAMMA_M0 = 1.0
GAMMA_M1 = 1.0
ALPHA = {"a0": 0.13, "a": 0.21, "b": 0.34, "c": 0.49, "d": 0.76}
COLD = ("C", "Z", "OMEGA")
HOLLOW = ("SHS", "RHS")


def epsilon(fy):
    return math.sqrt(235.0 / fy)


def _band(ratio, limits):
    """The class (1–4) a part's c/t gives against its limits (class 1, 2, 3)."""
    for k, limit in enumerate(limits, 1):
        if ratio <= limit:
            return k
    return 4


def section_class(sec, fy):
    """(its class in bending about y, its class in compression) — EN 1993-1-1 Table 5.2."""
    e = epsilon(fy)
    f = sec.family
    if f in steel.I_FAMILIES:
        flange = _band((sec.b - sec.tw - 2.0 * sec.r) / 2.0 / sec.tf, (9 * e, 10 * e, 14 * e))
        c_w = (sec.h - 2.0 * sec.tf - 2.0 * sec.r) / sec.tw
        return max(flange, _band(c_w, (72 * e, 83 * e, 124 * e))), max(flange, _band(c_w, (33 * e, 38 * e, 42 * e)))
    if f in steel.U_FAMILIES:
        flange = _band((sec.b - sec.tw - sec.r) / sec.tf, (9 * e, 10 * e, 14 * e))
        c_w = (sec.h - 2.0 * sec.tf - 2.0 * sec.r) / sec.tw
        return max(flange, _band(c_w, (72 * e, 83 * e, 124 * e))), max(flange, _band(c_w, (33 * e, 38 * e, 42 * e)))
    if f in HOLLOW:
        c_b = (sec.b - 3.0 * sec.tw) / sec.tw
        c_h = (sec.h - 3.0 * sec.tw) / sec.tw
        comp = (33 * e, 38 * e, 42 * e)
        return max(_band(c_b, comp), _band(c_h, (72 * e, 83 * e, 124 * e))), max(_band(c_b, comp), _band(c_h, comp))
    if f == "CHS":
        k = _band(sec.h / sec.tw, (50 * e * e, 70 * e * e, 90 * e * e))
        return k, k
    if f in ("L", "LU"):
        outstand = _band(sec.h / sec.tw, (9 * e, 10 * e, 14 * e))
        comp = 3 if sec.h / sec.tw <= 15 * e and (sec.b + sec.h) / 2.0 / sec.tw <= 11.5 * e else 4
        return outstand, comp
    return 3, 3                                         # (cold formed: as class 3, its elastic modulus)


def curves(sec):
    """(the buckling curve about y, about z) — EN 1993-1-1 Table 6.2 (the hollow sections of EN 10219: cold
    formed, «c»)."""
    f = sec.family
    if f in steel.I_FAMILIES:
        if sec.h / sec.b > 1.2:
            return ("a", "b") if sec.tf <= 40.0 else ("b", "c")
        return ("b", "c") if sec.tf <= 100.0 else ("d", "d")
    return "c", "c"


def chi(slenderness, curve):
    """The reduction for flexural buckling (6.3.1.2) at a non-dimensional slenderness."""
    if slenderness <= 0.2:
        return 1.0
    phi = 0.5 * (1.0 + ALPHA[curve] * (slenderness - 0.2) + slenderness ** 2)
    return min(1.0, 1.0 / (phi + math.sqrt(max(phi * phi - slenderness ** 2, 0.0))))


def shear_area(sec, area):
    """(Av for a shear along z — the depth —, along y) mm² — EN 1993-1-1 6.2.6(3), the rolled sections' cases."""
    f = sec.family
    if f in steel.I_FAMILIES:
        avz = max(area - 2.0 * sec.b * sec.tf + (sec.tw + 2.0 * sec.r) * sec.tf, (sec.h - 2.0 * sec.tf) * sec.tw)
        return avz, 2.0 * sec.b * sec.tf
    if f in steel.U_FAMILIES:
        avz = area - 2.0 * sec.b * sec.tf + (sec.tw + sec.r) * sec.tf
        return avz, 2.0 * sec.b * sec.tf
    if f in HOLLOW:
        return area * sec.h / (sec.b + sec.h), area * sec.b / (sec.b + sec.h)
    if f == "CHS":
        return 2.0 * area / math.pi, 2.0 * area / math.pi
    return sec.h * sec.tw, sec.b * sec.tw


def check(section, grade, n, my, mz, vz, vy, ly, lz):
    """A steel piece checked: its section (catalogue name), its grade; its design forces — n kN (tension +,
    compression −), my mz kN·m (about its strong and weak axes), vz vy kN —, its buckling lengths ly lz m (about y,
    about z). {"util": the greatest ratio, "check": which, the ratios {name: ratio}, "class", "notes": [code]}."""
    sec = steel.get(section)
    props = steel.properties(sec.name)
    fy = steel.strength(grade, steel.thickest(sec))[0]
    area = props["A"] * 100.0                              # mm²
    iy, iz = props["Iy"] * 1e4, props["Iz"] * 1e4          # mm⁴
    k_bend, k_comp = section_class(sec, fy)
    elastic = k_bend >= 3 or sec.family in COLD
    wy = (props["Wel_y"] if elastic else props["Wpl_y"]) * 1e3
    wz = (props["Wel_z"] if elastic else props["Wpl_z"]) * 1e3
    n_rd = area * fy / GAMMA_M0 / 1000.0                   # kN
    my_rd = wy * fy / GAMMA_M0 / 1e6                       # kN·m
    mz_rd = wz * fy / GAMMA_M0 / 1e6
    avz, avy = shear_area(sec, area)
    vz_rd = avz * fy / math.sqrt(3.0) / GAMMA_M0 / 1000.0
    vy_rd = avy * fy / math.sqrt(3.0) / GAMMA_M0 / 1000.0
    ratios = {"N": abs(n) / n_rd, "M": abs(my) / my_rd + abs(mz) / mz_rd,
              "NM": abs(n) / n_rd + abs(my) / my_rd + abs(mz) / mz_rd,
              "V": max(abs(vz) / vz_rd, abs(vy) / vy_rd if vy_rd > 0 else 0.0)}
    notes = []
    if n < 0.0:                                            # (compression: flexural buckling, and with bending)
        cy, cz = curves(sec)
        lam_y = math.sqrt(area * fy / (math.pi ** 2 * steel.E * iy / (ly * 1000.0) ** 2)) if ly > 0 else 0.0
        lam_z = math.sqrt(area * fy / (math.pi ** 2 * steel.E * iz / (lz * 1000.0) ** 2)) if lz > 0 else 0.0
        chi_y, chi_z = chi(lam_y, cy), chi(lam_z, cz)
        nb_y, nb_z = chi_y * n_rd * GAMMA_M0 / GAMMA_M1, chi_z * n_rd * GAMMA_M0 / GAMMA_M1
        ratios["Nb"] = abs(n) / min(nb_y, nb_z)
        ny, nz = abs(n) / nb_y, abs(n) / nb_z              # (Annex B, Table B.1, Cm = 1)
        if elastic:
            kyy = min(1.0 + 0.6 * lam_y * ny, 1.0 + 0.6 * ny)
            kzz = min(1.0 + 0.6 * lam_z * nz, 1.0 + 0.6 * nz)
            kyz, kzy = kzz, 0.8 * kyy
        else:
            kyy = min(1.0 + (lam_y - 0.2) * ny, 1.0 + 0.8 * ny) if lam_y > 0.2 else 1.0
            kzz = min(1.0 + (2.0 * lam_z - 0.6) * nz, 1.0 + 1.4 * nz) if lam_z > 0.3 else 1.0
            kyz, kzy = 0.6 * kzz, 0.6 * kyy
        my_rk, mz_rk = my_rd * GAMMA_M0 / GAMMA_M1, mz_rd * GAMMA_M0 / GAMMA_M1
        ratios["NMb_y"] = ny + kyy * abs(my) / my_rk + kyz * abs(mz) / mz_rk
        ratios["NMb_z"] = nz + kzy * abs(my) / my_rk + kzz * abs(mz) / mz_rk
        if max(lam_y, lam_z) > 2.0:
            notes.append("slender")
    if abs(my) > 1e-6:
        notes.append("ltb")                                # (lateral-torsional buckling not checked)
    if sec.family in COLD:
        notes.append("cold")
    if max(k_bend, k_comp) == 4:
        notes.append("class4")
    name, util = max(ratios.items(), key=lambda kv: kv[1])
    return {"util": util, "check": name, "ratios": ratios, "class": max(k_bend, k_comp if n < 0 else 1),
            "notes": notes, "fy": fy}
