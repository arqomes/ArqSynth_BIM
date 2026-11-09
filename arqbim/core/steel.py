"""(0.494) Steel sections and grades — the European catalogues an architect and an engineer in Portugal use: hot-rolled
I and H sections (IPE, HEA, HEB, HEM — EN 10365), channels (UPN with sloped flanges, UPE with parallel ones — EN 10365),
equal and unequal angles (EN 10056-1), cold-formed square, rectangular and round hollow sections (EN 10219) and
cold-formed purlins and battens (lipped C and Z, omega). Each section by the dimensions of its standard (mm); its
outline drawn as the standard draws it (root and toe radii, a UPN's 8 % flange slope with the thickness at half the
flange width, a tube's corner radii); its properties worked out from that outline (area, mass, second moments, elastic
and plastic moduli, radii of gyration, torsion and warping constants — the catalogues' formulas where the outline is not
enough: ArcelorMittal's for an I's torsion constant, EN 10219-2's for a tube's). The published mass per metre is kept for
the hot-rolled sections (the tests check the outline against it).

The grades of EN 10025-2 (S235, S275, S355) and EN 10025-3 (S460), fy and fu by thickness as EC3-1-1 Table 3.1.

Names: a section's key is written without spaces, as IFC files and the other programs name them («IPE300», «HEB200»,
«L100x10», «SHS100x100x5», «CHS114.3x5»); shown with them («IPE 300», «L 100×10», «CHS Ø114,3×5»). Pure Python."""

import functools
import math
import re
from dataclasses import dataclass

DENSITY = 7850.0                # kg/m³
E = 210000.0                    # N/mm² (EC3-1-1 3.2.6)
G = 81000.0
ARC = 12                        # segments of a quarter of a fillet


@dataclass(frozen=True)
class Section:
    """A section's dimensions, mm. h its depth (a round tube: its diameter), b its width; tw the web (a tube, a
    cold-formed section: its wall) and tf the flange thickness; r the root radius (a tube: its outer corner radius),
    r2 the toe radius (a tube: its inner corner radius); c a lip's (an omega's foot's) length; slope a flange's (a UPN's:
    0.08); mass the published kg/m (None: from the area)."""
    name: str
    family: str
    h: float
    b: float
    tw: float = 0.0
    tf: float = 0.0
    r: float = 0.0
    r2: float = 0.0
    c: float = 0.0
    slope: float = 0.0
    mass: float = None


# the families, in the order they are offered: (key, its IFC profile class, its standard)
FAMILIES = (("IPE", "IfcIShapeProfileDef", "EN 10365"), ("HEA", "IfcIShapeProfileDef", "EN 10365"),
            ("HEB", "IfcIShapeProfileDef", "EN 10365"), ("HEM", "IfcIShapeProfileDef", "EN 10365"),
            ("UPN", "IfcUShapeProfileDef", "EN 10365"), ("UPE", "IfcUShapeProfileDef", "EN 10365"),
            ("L", "IfcLShapeProfileDef", "EN 10056-1"), ("LU", "IfcLShapeProfileDef", "EN 10056-1"),
            ("SHS", "IfcRectangleHollowProfileDef", "EN 10219"), ("RHS", "IfcRectangleHollowProfileDef", "EN 10219"),
            ("CHS", "IfcCircleHollowProfileDef", "EN 10219"), ("C", "IfcCShapeProfileDef", ""),
            ("Z", "IfcArbitraryClosedProfileDef", ""), ("OMEGA", "IfcArbitraryClosedProfileDef", ""))
IFC_CLASS = {key: ifc for key, ifc, _std in FAMILIES}
STANDARD = {key: std for key, _ifc, std in FAMILIES}
I_FAMILIES, U_FAMILIES = ("IPE", "HEA", "HEB", "HEM"), ("UPN", "UPE")

# ------------------------------------------------------------ the catalogues (mm; kg/m as published)

# I and H: (size, h, b, tw, tf, r, kg/m)
_IPE = ((80, 80, 46, 3.8, 5.2, 5, 6.0), (100, 100, 55, 4.1, 5.7, 7, 8.1), (120, 120, 64, 4.4, 6.3, 7, 10.4),
        (140, 140, 73, 4.7, 6.9, 7, 12.9), (160, 160, 82, 5.0, 7.4, 9, 15.8), (180, 180, 91, 5.3, 8.0, 9, 18.8),
        (200, 200, 100, 5.6, 8.5, 12, 22.4), (220, 220, 110, 5.9, 9.2, 12, 26.2), (240, 240, 120, 6.2, 9.8, 15, 30.7),
        (270, 270, 135, 6.6, 10.2, 15, 36.1), (300, 300, 150, 7.1, 10.7, 15, 42.2), (330, 330, 160, 7.5, 11.5, 18, 49.1),
        (360, 360, 170, 8.0, 12.7, 18, 57.1), (400, 400, 180, 8.6, 13.5, 21, 66.3), (450, 450, 190, 9.4, 14.6, 21, 77.6),
        (500, 500, 200, 10.2, 16.0, 21, 90.7), (550, 550, 210, 11.1, 17.2, 24, 106.0),
        (600, 600, 220, 12.0, 19.0, 24, 122.0))
_HEA = ((100, 96, 100, 5, 8, 12, 16.7), (120, 114, 120, 5, 8, 12, 19.9), (140, 133, 140, 5.5, 8.5, 12, 24.7),
        (160, 152, 160, 6, 9, 15, 30.4), (180, 171, 180, 6, 9.5, 15, 35.5), (200, 190, 200, 6.5, 10, 18, 42.3),
        (220, 210, 220, 7, 11, 18, 50.5), (240, 230, 240, 7.5, 12, 21, 60.3), (260, 250, 260, 7.5, 12.5, 24, 68.2),
        (280, 270, 280, 8, 13, 24, 76.4), (300, 290, 300, 8.5, 14, 27, 88.3), (320, 310, 300, 9, 15.5, 27, 97.6),
        (340, 330, 300, 9.5, 16.5, 27, 105.0), (360, 350, 300, 10, 17.5, 27, 112.0), (400, 390, 300, 11, 19, 27, 125.0),
        (450, 440, 300, 11.5, 21, 27, 140.0), (500, 490, 300, 12, 23, 27, 155.0), (550, 540, 300, 12.5, 24, 27, 166.0),
        (600, 590, 300, 13, 25, 27, 178.0), (650, 640, 300, 13.5, 26, 27, 190.0), (700, 690, 300, 14.5, 27, 27, 204.0),
        (800, 790, 300, 15, 28, 30, 224.0), (900, 890, 300, 16, 30, 30, 252.0), (1000, 990, 300, 16.5, 31, 30, 272.0))
_HEB = ((100, 100, 100, 6, 10, 12, 20.4), (120, 120, 120, 6.5, 11, 12, 26.7), (140, 140, 140, 7, 12, 12, 33.7),
        (160, 160, 160, 8, 13, 15, 42.6), (180, 180, 180, 8.5, 14, 15, 51.2), (200, 200, 200, 9, 15, 18, 61.3),
        (220, 220, 220, 9.5, 16, 18, 71.5), (240, 240, 240, 10, 17, 21, 83.2), (260, 260, 260, 10, 17.5, 24, 93.0),
        (280, 280, 280, 10.5, 18, 24, 103.0), (300, 300, 300, 11, 19, 27, 117.0), (320, 320, 300, 11.5, 20.5, 27, 127.0),
        (340, 340, 300, 12, 21.5, 27, 134.0), (360, 360, 300, 12.5, 22.5, 27, 142.0), (400, 400, 300, 13.5, 24, 27, 155.0),
        (450, 450, 300, 14, 26, 27, 171.0), (500, 500, 300, 14.5, 28, 27, 187.0), (550, 550, 300, 15, 29, 27, 199.0),
        (600, 600, 300, 15.5, 30, 27, 212.0), (650, 650, 300, 16, 31, 27, 225.0), (700, 700, 300, 17, 32, 27, 241.0),
        (800, 800, 300, 17.5, 33, 30, 262.0), (900, 900, 300, 18.5, 35, 30, 291.0), (1000, 1000, 300, 19, 36, 30, 314.0))
_HEM = ((100, 120, 106, 12, 20, 12, 41.8), (120, 140, 126, 12.5, 21, 12, 52.1), (140, 160, 146, 13, 22, 12, 63.2),
        (160, 180, 166, 14, 23, 15, 76.2), (180, 200, 186, 14.5, 24, 15, 88.9), (200, 220, 206, 15, 25, 18, 103.0),
        (220, 240, 226, 15.5, 26, 18, 117.0), (240, 270, 248, 18, 32, 21, 157.0), (260, 290, 268, 18, 32.5, 24, 172.0),
        (280, 310, 288, 18.5, 33, 24, 189.0), (300, 340, 310, 21, 39, 27, 238.0), (320, 359, 309, 21, 40, 27, 245.0),
        (340, 377, 309, 21, 40, 27, 248.0), (360, 395, 308, 21, 40, 27, 250.0), (400, 432, 307, 21, 40, 27, 256.0),
        (450, 478, 307, 21, 40, 27, 263.0), (500, 524, 306, 21, 40, 27, 270.0), (550, 572, 306, 21, 40, 27, 278.0),
        (600, 620, 305, 21, 40, 27, 285.0), (650, 668, 305, 21, 40, 27, 293.0), (700, 716, 304, 21, 40, 27, 301.0),
        (800, 814, 303, 21, 40, 30, 317.0), (900, 910, 302, 21, 40, 30, 333.0), (1000, 1008, 302, 21, 40, 30, 349.0))
# channels: (size, h, b, tw, tf, r1, r2, kg/m) — a UPN's flanges sloped 8 %, tf at half the flange width
_UPN = ((80, 80, 45, 6, 8, 8, 4, 8.64), (100, 100, 50, 6, 8.5, 8.5, 4.5, 10.6), (120, 120, 55, 7, 9, 9, 4.5, 13.4),
        (140, 140, 60, 7, 10, 10, 5, 16.0), (160, 160, 65, 7.5, 10.5, 10.5, 5.5, 18.8),
        (180, 180, 70, 8, 11, 11, 5.5, 22.0), (200, 200, 75, 8.5, 11.5, 11.5, 6, 25.3),
        (220, 220, 80, 9, 12.5, 12.5, 6.5, 29.4), (240, 240, 85, 9.5, 13, 13, 6.5, 33.2),
        (260, 260, 90, 10, 14, 14, 7, 37.9), (280, 280, 95, 10, 15, 15, 7.5, 41.8), (300, 300, 100, 10, 16, 16, 8, 46.2),
        (320, 320, 100, 14, 17.5, 17.5, 8.75, 59.5), (350, 350, 100, 14, 16, 16, 8, 60.6),
        (380, 380, 102, 13.5, 16, 16, 8, 63.1), (400, 400, 110, 14, 18, 18, 9, 71.8))
_UPE = ((80, 80, 50, 4, 7, 10, 0, 7.90), (100, 100, 55, 4.5, 7.5, 10, 0, 9.82), (120, 120, 60, 5, 8, 12, 0, 12.1),
        (140, 140, 65, 5, 9, 12, 0, 14.5), (160, 160, 70, 5.5, 9.5, 12, 0, 17.0), (180, 180, 75, 5.5, 10.5, 12, 0, 19.7),
        (200, 200, 80, 6, 11, 13, 0, 22.8), (220, 220, 85, 6.5, 12, 13, 0, 26.6), (240, 240, 90, 7, 12.5, 15, 0, 30.2),
        (270, 270, 95, 7.5, 13.5, 15, 0, 35.2), (300, 300, 100, 9.5, 15, 15, 0, 44.4),
        (330, 330, 105, 11, 16, 18, 0, 53.2), (360, 360, 110, 12, 17, 18, 0, 61.2), (400, 400, 115, 13.5, 18, 18, 0, 72.2))
# equal angles: (leg, t, r1, r2, kg/m); unequal: (long leg, short leg, t, r1, r2)
_L = ((20, 3, 3.5, 2, 0.882), (25, 3, 3.5, 2, 1.12), (25, 4, 3.5, 2, 1.45), (30, 3, 5, 2.5, 1.36), (30, 4, 5, 2.5, 1.78),
      (35, 4, 5, 2.5, 2.09), (40, 4, 6, 3, 2.42), (40, 5, 6, 3, 2.97), (45, 5, 7, 3.5, 3.38), (50, 5, 7, 3.5, 3.77),
      (50, 6, 7, 3.5, 4.47), (60, 6, 8, 4, 5.42), (60, 8, 8, 4, 7.09), (70, 7, 9, 4.5, 7.38), (80, 8, 10, 5, 9.63),
      (90, 9, 11, 5.5, 12.2), (100, 10, 12, 6, 15.0), (120, 12, 13, 6.5, 21.6), (150, 15, 16, 8, 33.8),
      (200, 20, 18, 9, 59.9))
_LU = ((60, 40, 6, 6, 3), (80, 40, 6, 7, 3.5), (80, 60, 7, 8, 4), (100, 50, 8, 9, 4.5), (100, 65, 8, 10, 5),
       (100, 75, 8, 10, 5), (120, 80, 10, 11, 5.5), (150, 75, 9, 12, 6), (150, 90, 10, 12, 6), (200, 100, 10, 15, 7.5))
# cold-formed hollow sections, EN 10219: (h, b, (t…)); round: (D, (t…))
_SHS = ((40, (2, 3, 4)), (50, (3, 4, 5)), (60, (3, 4, 5)), (70, (3, 4, 5)), (80, (3, 4, 5, 6)), (90, (4, 5, 6)),
        (100, (4, 5, 6, 8)), (120, (5, 6, 8, 10)), (140, (5, 6, 8, 10)), (150, (6, 8, 10)), (160, (6, 8, 10)),
        (180, (6, 8, 10)), (200, (6, 8, 10, 12)), (250, (8, 10, 12)), (300, (10, 12)))
_RHS = ((60, 40, (3, 4)), (80, 40, (3, 4)), (100, 50, (3, 4, 5)), (100, 60, (4, 5)), (120, 60, (4, 5)),
        (120, 80, (4, 5, 6)), (150, 100, (5, 6, 8)), (160, 80, (5, 6)), (200, 100, (6, 8, 10)), (200, 120, (6, 8)),
        (250, 150, (8, 10)), (300, 200, (8, 10, 12)))
_CHS = ((33.7, (2.6, 3.2)), (42.4, (2.6, 3.2, 4)), (48.3, (2.6, 3.2, 4)), (60.3, (3.2, 4, 5)), (76.1, (3.2, 4, 5)),
        (88.9, (3.2, 4, 5, 6.3)), (101.6, (4, 5, 6.3)), (114.3, (4, 5, 6.3)), (139.7, (5, 6.3, 8)),
        (168.3, (5, 6.3, 8, 10)), (193.7, (6.3, 8, 10)), (219.1, (6.3, 8, 10, 12.5)), (273.0, (6.3, 8, 10, 12.5)),
        (323.9, (8, 10, 12.5)))
# cold-formed purlins (lipped C and Z) and battens (omega): (h, b, lip — an omega's foot —, (t…))
_C = ((100, 50, 15, (1.5, 2)), (120, 50, 15, (1.5, 2, 2.5)), (140, 60, 20, (2, 2.5)), (160, 60, 20, (2, 2.5, 3)),
      (180, 70, 20, (2, 2.5, 3)), (200, 70, 20, (2, 2.5, 3)), (250, 80, 25, (2.5, 3)))
_OMEGA = ((30, 40, 20, (1, 1.5)), (40, 50, 20, (1.5, 2)), (50, 60, 25, (2,)))


def _number(v):
    """3 → «3», 2.5 → «2.5» (a key's numbers)."""
    return ("%g" % float(v))


def _build():
    out = {}
    for family, rows in (("IPE", _IPE), ("HEA", _HEA), ("HEB", _HEB), ("HEM", _HEM)):
        for size, h, b, tw, tf, r, mass in rows:
            name = "{}{}".format(family, size)
            out[name] = Section(name, family, h, b, tw, tf, r, mass=mass)
    for family, rows in (("UPN", _UPN), ("UPE", _UPE)):
        for size, h, b, tw, tf, r1, r2, mass in rows:
            name = "{}{}".format(family, size)
            out[name] = Section(name, family, h, b, tw, tf, r1, r2, slope=0.08 if family == "UPN" else 0.0, mass=mass)
    for leg, t, r1, r2, mass in _L:
        name = "L{}x{}".format(_number(leg), _number(t))
        out[name] = Section(name, "L", leg, leg, t, t, r1, r2, mass=mass)
    for long_, short, t, r1, r2 in _LU:
        name = "L{}x{}x{}".format(_number(long_), _number(short), _number(t))
        out[name] = Section(name, "LU", long_, short, t, t, r1, r2)
    for side, ts in _SHS:
        for t in ts:
            name = "SHS{0}x{0}x{1}".format(_number(side), _number(t))
            ro = _tube_radius(t)
            out[name] = Section(name, "SHS", side, side, t, t, ro, ro - t)
    for h, b, ts in _RHS:
        for t in ts:
            name = "RHS{}x{}x{}".format(_number(h), _number(b), _number(t))
            ro = _tube_radius(t)
            out[name] = Section(name, "RHS", h, b, t, t, ro, ro - t)
    for d, ts in _CHS:
        for t in ts:
            name = "CHS{}x{}".format(_number(d), _number(t))
            out[name] = Section(name, "CHS", d, d, t, t)
    for family in ("C", "Z"):
        for h, b, lip, ts in _C:
            for t in ts:
                name = "{}{}x{}x{}x{}".format(family, _number(h), _number(b), _number(lip), _number(t))
                out[name] = Section(name, family, h, b, t, t, t, 0.0, lip)        # (inner bend radius = t)
    for h, b, foot, ts in _OMEGA:
        for t in ts:
            name = "OMEGA{}x{}x{}x{}".format(_number(h), _number(b), _number(foot), _number(t))
            out[name] = Section(name, "OMEGA", h, b, t, t, t, 0.0, foot)
    return out


def _tube_radius(t):
    """EN 10219-2's outer corner radius of a cold-formed tube: 2t (t ≤ 6), 2,5t (≤ 10), 3t."""
    return 2.0 * t if t <= 6 else 2.5 * t if t <= 10 else 3.0 * t


SECTIONS = {}
CUSTOM = {}                     # sections read from other programs' files (not in the catalogue), by name


def _key(text):
    """A section's key as written in any way («IPE 300», «ipe300», «L100×10», «SHS 100x100x5», «CHS 114,3x5»)."""
    s = str(text or "").upper().replace("×", "X").replace("Ø", "").replace(",", ".").replace("Ω", "OMEGA")
    s = re.sub(r"\s+", "", s)
    return s


def get(name):
    """The section of a name (the catalogue's, else one read from a file), or None."""
    key = _key(name)
    return SECTIONS.get(key) or CUSTOM.get(key)


def family(name):
    sec = get(name)
    return sec.family if sec is not None else None


def sections(family_key):
    """The catalogue's sections of a family, in its order."""
    return [s for s in SECTIONS.values() if s.family == family_key]


def _comma(v):
    return _number(v).replace(".", ",")


def display(name):
    """A section as written on drawings and in names: «IPE 300», «L 100×10», «SHS 100×100×5», «CHS Ø114,3×5», «C
    150×50×20×2», «Ω 40×50×20×1,5»."""
    sec = get(name)
    if sec is None:
        return str(name or "")
    f = sec.family
    if f in I_FAMILIES + U_FAMILIES:
        return "{} {}".format(f, sec.name[len(f):]) if sec.name.startswith(f) else sec.name
    if f == "L":
        return "L {}×{}".format(_comma(sec.h), _comma(sec.tw))
    if f == "LU":
        return "L {}×{}×{}".format(_comma(sec.h), _comma(sec.b), _comma(sec.tw))
    if f in ("SHS", "RHS"):
        return "{} {}×{}×{}".format(f, _comma(sec.h), _comma(sec.b), _comma(sec.tw))
    if f == "CHS":
        return "CHS Ø{}×{}".format(_comma(sec.h), _comma(sec.tw))
    if f in ("C", "Z", "OMEGA"):
        return "{} {}×{}×{}×{}".format("Ω" if f == "OMEGA" else f, _comma(sec.h), _comma(sec.b), _comma(sec.c),
                                      _comma(sec.tw))
    return sec.name


# ------------------------------------------------------------ the outline

def _rounded(corners, radii, n=ARC):
    """A polygon's corners with each rounded by its radius (0: sharp) — a fillet tangent to both sides, whether the
    corner goes in or out; [(x, y)]."""
    out = []
    m = len(corners)
    for i in range(m):
        px, py = corners[i]
        r = radii[i]
        if r <= 0:
            out.append((px, py))
            continue
        ax, ay = corners[i - 1][0] - px, corners[i - 1][1] - py
        cx, cy = corners[(i + 1) % m][0] - px, corners[(i + 1) % m][1] - py
        la, lc = math.hypot(ax, ay), math.hypot(cx, cy)
        ax, ay, cx, cy = ax / la, ay / la, cx / lc, cy / lc
        angle = math.acos(max(-1.0, min(1.0, ax * cx + ay * cy)))
        if angle < 1e-6 or abs(angle - math.pi) < 1e-6:
            out.append((px, py))
            continue
        d = min(r / math.tan(angle / 2.0), la * 0.999, lc * 0.999)
        r = d * math.tan(angle / 2.0)
        bx, by = ax + cx, ay + cy
        lb = math.hypot(bx, by)
        ox, oy = px + bx / lb * r / math.sin(angle / 2.0), py + by / lb * r / math.sin(angle / 2.0)
        t1 = (px + ax * d - ox, py + ay * d - oy)
        t2 = (px + cx * d - ox, py + cy * d - oy)
        a1, a2 = math.atan2(t1[1], t1[0]), math.atan2(t2[1], t2[0])
        sweep = (a2 - a1 + math.pi) % (2.0 * math.pi) - math.pi
        steps = max(2, int(math.ceil(n * abs(sweep) / (math.pi / 2.0))))
        for k in range(steps + 1):
            a = a1 + sweep * k / steps
            out.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return out


def _bent(corners, bends, t, ri):
    """A cold-formed section's outline: its bends rounded — ri inside, ri + t outside (by the way the corner turns)."""
    radii = []
    m = len(corners)
    for i in range(m):
        if i not in bends:
            radii.append(0.0)
            continue
        ax, ay = corners[i][0] - corners[i - 1][0], corners[i][1] - corners[i - 1][1]
        cx, cy = corners[(i + 1) % m][0] - corners[i][0], corners[(i + 1) % m][1] - corners[i][1]
        radii.append(ri + t if ax * cy - ay * cx > 0 else ri)        # (a left turn of the outline, going round: out)
    return _rounded(corners, radii)


def outline(sec):
    """The section's outline, mm, its bounding box's middle at the origin as IFC's profiles have it — (outer ring
    anticlockwise, [holes clockwise]). An I: its web up y; a channel, an angle, a C: their web on the left (−x), their
    flanges / legs to the right (+x), an angle's other leg along the bottom; a Z: its upper flange to the right."""
    h, b, tw, tf, r, r2 = sec.h, sec.b, sec.tw, sec.tf, sec.r, sec.r2
    f = sec.family
    if f in I_FAMILIES:
        y0, y1, w = -h / 2.0, h / 2.0, tw / 2.0
        corners = [(-b / 2, y0), (b / 2, y0), (b / 2, y0 + tf), (w, y0 + tf), (w, y1 - tf), (b / 2, y1 - tf),
                   (b / 2, y1), (-b / 2, y1), (-b / 2, y1 - tf), (-w, y1 - tf), (-w, y0 + tf), (-b / 2, y0 + tf)]
        radii = [0, 0, 0, r, r, 0, 0, 0, 0, r, r, 0]
        return _rounded(corners, radii), []
    if f in U_FAMILIES:
        x0, x1, y0, y1 = -b / 2.0, b / 2.0, -h / 2.0, h / 2.0
        s = sec.slope
        xm = x0 + b / 2.0                              # (DIN 1026: the flange's thickness at half its width)
        root, tip = tf + s * (xm - (x0 + tw)), tf - s * (x1 - xm)
        corners = [(x0, y0), (x1, y0), (x1, y0 + tip), (x0 + tw, y0 + root), (x0 + tw, y1 - root), (x1, y1 - tip),
                   (x1, y1), (x0, y1)]
        radii = [0, 0, r2, r, r, r2, 0, 0]
        return _rounded(corners, radii), []
    if f in ("L", "LU"):
        t = tw
        x0, x1, y0, y1 = -b / 2.0, b / 2.0, -h / 2.0, h / 2.0
        corners = [(x0, y0), (x1, y0), (x1, y0 + t), (x0 + t, y0 + t), (x0 + t, y1), (x0, y1)]
        radii = [0, 0, r2, r, r2, 0]
        return _rounded(corners, radii), []
    if f in ("SHS", "RHS"):
        t, ro, ri = tw, r, r2
        outer = _rounded([(-b / 2, -h / 2), (b / 2, -h / 2), (b / 2, h / 2), (-b / 2, h / 2)], [ro] * 4)
        inner = _rounded([(-b / 2 + t, -h / 2 + t), (-b / 2 + t, h / 2 - t), (b / 2 - t, h / 2 - t),
                          (b / 2 - t, -h / 2 + t)], [ri] * 4)
        return outer, [inner]
    if f == "CHS":
        n = 4 * ARC * 2
        ro, ri = h / 2.0, h / 2.0 - tw
        outer = [(ro * math.cos(2 * math.pi * k / n), ro * math.sin(2 * math.pi * k / n)) for k in range(n)]
        inner = [(ri * math.cos(-2 * math.pi * k / n), ri * math.sin(-2 * math.pi * k / n)) for k in range(n)]
        return outer, [inner]
    t, c, ri = tw, sec.c, r
    if f == "C":                                       # (lipped: its lips turned in)
        x0, x1, y0, y1 = -b / 2.0, b / 2.0, -h / 2.0, h / 2.0
        corners = [(x0, y0), (x1, y0), (x1, y0 + c), (x1 - t, y0 + c), (x1 - t, y0 + t), (x0 + t, y0 + t),
                   (x0 + t, y1 - t), (x1 - t, y1 - t), (x1 - t, y1 - c), (x1, y1 - c), (x1, y1), (x0, y1)]
        return _bent(corners, {0, 1, 4, 5, 6, 7, 10, 11}, t, ri), []
    if f == "Z":                                       # (lipped: its upper flange to the right, its lower to the left)
        y0, y1, w = -h / 2.0, h / 2.0, t / 2.0
        e = b - w                                      # (each flange b wide from the web's far face)
        corners = [(w, y0), (w, y1 - t), (e - t, y1 - t), (e - t, y1 - c), (e, y1 - c), (e, y1), (-w, y1),
                   (-w, y0 + t), (-e + t, y0 + t), (-e + t, y0 + c), (-e, y0 + c), (-e, y0)]
        return _bent(corners, {0, 1, 2, 5, 6, 7, 8, 11}, t, ri), []
    if f == "OMEGA":                                   # (its top up, its feet out at the bottom)
        y0, y1, wf = -h / 2.0, h / 2.0, b / 2.0 + c
        corners = [(-wf, y0), (-b / 2 + t, y0), (-b / 2 + t, y1 - t), (b / 2 - t, y1 - t), (b / 2 - t, y0), (wf, y0),
                   (wf, y0 + t), (b / 2, y0 + t), (b / 2, y1), (-b / 2, y1), (-b / 2, y0 + t), (-wf, y0 + t)]
        return _bent(corners, {1, 2, 3, 4, 7, 8, 9, 10}, t, ri), []
    return [(-b / 2, -h / 2), (b / 2, -h / 2), (b / 2, h / 2), (-b / 2, h / 2)], []


def size(sec):
    """(width, depth) of its bounding box, mm — a Z's both flanges, an omega's feet."""
    if sec.family == "Z":
        return 2.0 * sec.b - sec.tw, sec.h
    if sec.family == "OMEGA":
        return sec.b + 2.0 * sec.c, sec.h
    return sec.b, sec.h


# ------------------------------------------------------------ properties

def _ring_moments(ring):
    """(signed area, ∫x, ∫y, ∫x², ∫y²) of a closed ring (Green's theorem)."""
    a = sx = sy = sxx = syy = 0.0
    m = len(ring)
    for i in range(m):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % m]
        cross = x0 * y1 - x1 * y0
        a += cross
        sx += (x0 + x1) * cross
        sy += (y0 + y1) * cross
        sxx += (x0 * x0 + x0 * x1 + x1 * x1) * cross
        syy += (y0 * y0 + y0 * y1 + y1 * y1) * cross
    return a / 2.0, sx / 6.0, sy / 6.0, sxx / 12.0, syy / 12.0


def _moments(rings):
    total = [0.0] * 5
    for ring in rings:
        for k, v in enumerate(_ring_moments(ring)):
            total[k] += v
    return total


def _clip(ring, level, axis, below=True):
    """A ring cut by the line x or y = level (axis 0 / 1): the part below (or above) — Sutherland–Hodgman (the area
    and moments right for any ring, whatever its shape)."""
    out = []
    m = len(ring)
    inside = (lambda p: p[axis] <= level) if below else (lambda p: p[axis] >= level)
    for i in range(m):
        p, q = ring[i - 1], ring[i]
        if inside(q):
            if not inside(p):
                out.append(_cross_at(p, q, level, axis))
            out.append(q)
        elif inside(p):
            out.append(_cross_at(p, q, level, axis))
    return out


def _cross_at(p, q, level, axis):
    k = (level - p[axis]) / (q[axis] - p[axis])
    return (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k)


def _plastic(rings, area, axis):
    """The plastic modulus about the axis that halves the area, perpendicular to `axis` (1: a horizontal line —
    bending about y-y)."""
    lo = min(p[axis] for ring in rings for p in ring)
    hi = max(p[axis] for ring in rings for p in ring)
    for _ in range(60):                                # (the line that halves it)
        mid = (lo + hi) / 2.0
        part = sum(_ring_moments(_clip(ring, mid, axis))[0] for ring in rings if len(ring) > 2)
        lo, hi = (mid, hi) if part < area / 2.0 else (lo, mid)
    level = (lo + hi) / 2.0
    w = 0.0
    for below in (True, False):
        parts = [_clip(ring, level, axis, below) for ring in rings]
        m = _moments([p for p in parts if len(p) > 2])
        first = m[1 + axis]                            # (∫ x or ∫ y)
        w += abs(first - m[0] * level)
    return w


@functools.lru_cache(maxsize=None)
def properties(name):
    """A section's properties (EC3's names; mm, cm and kg as the catalogues give them): A cm², mass kg/m (published,
    else from the area), Iy Iz cm⁴ (y-y the strong axis: horizontal), Wel_y Wel_z Wpl_y Wpl_z cm³, iy iz cm, It cm⁴,
    Iw cm⁶ (I and channels), paint m²/m (its outer outline), centroid (x, y) mm from the bounding box's middle."""
    sec = get(name)
    if sec is None:
        raise KeyError(name)
    outer, holes = outline(sec)
    rings = [outer] + holes
    a, sx, sy, sxx, syy = _moments(rings)
    cx, cy = sx / a, sy / a
    iy = syy - a * cy * cy                             # (about the horizontal axis through the centroid)
    iz = sxx - a * cx * cx
    ys = [p[1] for p in outer]
    xs = [p[0] for p in outer]
    wel_y = iy / max(max(ys) - cy, cy - min(ys))
    wel_z = iz / max(max(xs) - cx, cx - min(xs))
    wpl_y = _plastic(rings, a, 1)
    wpl_z = _plastic(rings, a, 0)
    perimeter = sum(math.dist(outer[i - 1], outer[i]) for i in range(len(outer)))
    it, iw = _torsion(sec, a, iz)
    mass = sec.mass if sec.mass else a * 1e-6 * DENSITY
    return {"A": a / 100.0, "mass": mass, "Iy": iy / 1e4, "Iz": iz / 1e4, "Wel_y": wel_y / 1e3, "Wel_z": wel_z / 1e3,
            "Wpl_y": wpl_y / 1e3, "Wpl_z": wpl_z / 1e3, "iy": math.sqrt(iy / a) / 10.0, "iz": math.sqrt(iz / a) / 10.0,
            "It": it / 1e4, "Iw": iw / 1e6 if iw is not None else None, "paint": perimeter / 1000.0,
            "centroid": (cx, cy)}


def _torsion(sec, area, iz):
    """(It mm⁴, Iw mm⁶ or None): an I by ArcelorMittal's catalogue formula (with its root fillets), Iw = Iz (h − tf)²/4;
    a channel's open-section sum and Iw by the thin-walled formula; a tube's by EN 10219-2; others Σ b t³/3."""
    h, b, tw, tf, r = sec.h, sec.b, sec.tw, sec.tf, sec.r
    f = sec.family
    if f in I_FAMILIES:
        alpha = ((r + tw / 2.0) ** 2 + (r + tf) ** 2 - r * r) / (2.0 * r + tf)
        it = (2.0 / 3.0) * (b - 0.63 * tf) * tf ** 3 + (1.0 / 3.0) * (h - 2.0 * tf) * tw ** 3 \
            + 2.0 * (tw / tf) * (0.145 + 0.1 * r / tf) * alpha ** 4
        return it, iz * (h - tf) ** 2 / 4.0
    if f in U_FAMILIES:
        it = (2.0 * (b - 0.63 * tf) * tf ** 3 + (h - 2.0 * tf) * tw ** 3) / 3.0
        hs, bs = h - tf, b - tw / 2.0                  # (the middle lines)
        iw = tf * bs ** 3 * hs ** 2 / 12.0 * (3.0 * bs * tf + 2.0 * hs * tw) / (6.0 * bs * tf + hs * tw)
        return it, iw
    if f in ("SHS", "RHS"):
        t = tw
        rc = (sec.r + sec.r2) / 2.0
        hp = 2.0 * ((b - t) + (h - t)) - 2.0 * rc * (4.0 - math.pi)
        ap = (b - t) * (h - t) - rc * rc * (4.0 - math.pi)
        k = 2.0 * ap * t / hp
        return t ** 3 * hp / 3.0 + 2.0 * k * ap, None
    if f == "CHS":
        return math.pi * (h ** 4 - (h - 2.0 * tw) ** 4) / 32.0, None
    if f in ("L", "LU"):
        return (h + b - tw) * tw ** 3 / 3.0, None
    developed = area / tw if tw else 0.0               # (a thin wall: its length × t³ / 3)
    return developed * tw ** 3 / 3.0, None


# ------------------------------------------------------------ grades

# EC3-1-1 Table 3.1: (fy, fu) N/mm² for t ≤ 40 mm, then 40 < t ≤ 80 mm
GRADES = {"S235": ((235.0, 360.0), (215.0, 360.0)), "S275": ((275.0, 430.0), (255.0, 410.0)),
          "S355": ((355.0, 490.0), (335.0, 470.0)), "S460": ((460.0, 540.0), (430.0, 540.0))}
GRADE_MATERIAL = {"S235": "aco_s235", "S275": "aco_s275", "S355": "aco_s355", "S460": "aco_s460"}
MATERIAL_GRADE = {v: k for k, v in GRADE_MATERIAL.items()}


def strength(grade, t):
    """(fy, fu) N/mm² of a grade for a thickness t mm (its section's thickest part)."""
    thin, thick = GRADES[grade]
    return thin if t <= 40.0 else thick


def thickest(sec):
    return max(sec.tw, sec.tf)


def grade_of(material):
    """The grade of a material key («aco_s355» → «S355»), or None."""
    return MATERIAL_GRADE.get(material)


# ------------------------------------------------------------ IFC

def ifc_profile(sec, to_units, angle_unit=1.0):
    """The IFC profile of a section: (its class, {attribute: value in the file's units}) — a parameterized one, or
    for a Z and an omega (no IFC class fits them) IfcArbitraryClosedProfileDef with («points»: its outline). to_units:
    file units per mm; angle_unit: radians per the file's angle unit."""
    f = sec.family
    u = to_units
    if f in I_FAMILIES:
        return "IfcIShapeProfileDef", {"OverallWidth": sec.b * u, "OverallDepth": sec.h * u, "WebThickness": sec.tw * u,
                                       "FlangeThickness": sec.tf * u, "FilletRadius": sec.r * u}
    if f in U_FAMILIES:
        values = {"Depth": sec.h * u, "FlangeWidth": sec.b * u, "WebThickness": sec.tw * u,
                  "FlangeThickness": sec.tf * u, "FilletRadius": sec.r * u}
        if sec.r2:
            values["EdgeRadius"] = sec.r2 * u
        if sec.slope:
            values["FlangeSlope"] = math.atan(sec.slope) / angle_unit
        return "IfcUShapeProfileDef", values
    if f in ("L", "LU"):
        return "IfcLShapeProfileDef", {"Depth": sec.h * u, "Width": sec.b * u, "Thickness": sec.tw * u,
                                       "FilletRadius": sec.r * u, "EdgeRadius": sec.r2 * u}
    if f in ("SHS", "RHS"):
        return "IfcRectangleHollowProfileDef", {"XDim": sec.b * u, "YDim": sec.h * u, "WallThickness": sec.tw * u,
                                                "OuterFilletRadius": sec.r * u, "InnerFilletRadius": sec.r2 * u}
    if f == "CHS":
        return "IfcCircleHollowProfileDef", {"Radius": sec.h / 2.0 * u, "WallThickness": sec.tw * u}
    if f == "C":
        return "IfcCShapeProfileDef", {"Depth": sec.h * u, "Width": sec.b * u, "WallThickness": sec.tw * u,
                                       "Girth": sec.c * u, "InternalFilletRadius": sec.r * u}
    outer, _holes = outline(sec)
    return "IfcArbitraryClosedProfileDef", {"points": [(x * u, y * u) for x, y in outer]}


def from_ifc(profile, unit_scale, angle_unit=1.0):
    """The section of an IFC profile (unit_scale: metres per file unit): the catalogue's by its ProfileName, else one
    made of its parameters (kept in CUSTOM under its name), or None (a profile no steel section is)."""
    found = get(getattr(profile, "ProfileName", None))
    if found is not None:
        return found
    sec = _from_params(profile, unit_scale * 1000.0, angle_unit)
    if sec is None:
        return None
    key = _key(sec.name)
    if CUSTOM.get(key) not in (None, sec):             # (the same name, other measures: worked out again)
        properties.cache_clear()
    CUSTOM[key] = sec
    return sec


STEEL_CLASSES = ("IfcIShapeProfileDef", "IfcUShapeProfileDef", "IfcRectangleHollowProfileDef",
                 "IfcCircleHollowProfileDef", "IfcCShapeProfileDef")


def is_steel_profile(profile):
    """Whether an IFC profile is a steel section's (a concrete L column of ArqSynth's has no root radius; an outline
    only when the catalogue names it)."""
    kind = profile.is_a()
    if kind in STEEL_CLASSES:
        return True
    if kind == "IfcLShapeProfileDef":
        return getattr(profile, "FilletRadius", None) is not None
    return kind == "IfcArbitraryClosedProfileDef" and get(getattr(profile, "ProfileName", None)) is not None


def ifc_outline(profile):
    """(outer ring, holes, width, depth) of a steel section's IFC profile in the file's own units (its parameters as
    they are, not the catalogue's), or None."""
    if profile.is_a("IfcArbitraryClosedProfileDef"):
        curve = profile.OuterCurve
        if curve.is_a("IfcIndexedPolyCurve"):
            pts = [(float(a), float(b)) for a, b in curve.Points.CoordList]
        elif curve.is_a("IfcPolyline"):
            pts = [(float(p.Coordinates[0]), float(p.Coordinates[1])) for p in curve.Points]
        else:
            return None
        if len(pts) > 3 and pts[0] == pts[-1]:
            pts = pts[:-1]
        if _ring_moments(pts)[0] < 0:
            pts = pts[::-1]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return pts, [], max(xs) - min(xs), max(ys) - min(ys)
    sec = _from_params(profile, 1.0)
    if sec is None:
        return None
    outer, holes = outline(sec)
    w, d = size(sec)
    return outer, holes, w, d


def area_and_perimeter(outer, holes):
    """(area, outer perimeter) of an outline, in its units."""
    return _moments([outer] + list(holes))[0], sum(math.dist(outer[i - 1], outer[i]) for i in range(len(outer)))


def _from_params(profile, mm, angle_unit=1.0):
    """A section made of an IFC profile's parameters (× mm: the file's units to mm), or None."""
    name = str(getattr(profile, "ProfileName", "") or "")

    def v(attr, default=0.0):
        value = getattr(profile, attr, None)
        return float(value) * mm if value is not None else default

    kind = profile.is_a()
    if kind == "IfcIShapeProfileDef":
        sec = Section(name or "I{:g}x{:g}".format(v("OverallDepth"), v("OverallWidth")), "IPE", v("OverallDepth"),
                      v("OverallWidth"), v("WebThickness"), v("FlangeThickness"), v("FilletRadius"))
    elif kind == "IfcUShapeProfileDef":
        slope = getattr(profile, "FlangeSlope", None)
        sec = Section(name or "U{:g}x{:g}".format(v("Depth"), v("FlangeWidth")), "UPN" if slope else "UPE", v("Depth"),
                      v("FlangeWidth"), v("WebThickness"), v("FlangeThickness"), v("FilletRadius"), v("EdgeRadius"),
                      slope=math.tan(float(slope) * angle_unit) if slope else 0.0)
    elif kind == "IfcRectangleHollowProfileDef":
        h, b = v("YDim"), v("XDim")
        sec = Section(name or "RHS{:g}x{:g}x{:g}".format(h, b, v("WallThickness")), "SHS" if abs(h - b) < 1e-6 else "RHS",
                      h, b, v("WallThickness"), v("WallThickness"), v("OuterFilletRadius"), v("InnerFilletRadius"))
    elif kind == "IfcCircleHollowProfileDef":
        d = 2.0 * v("Radius")
        sec = Section(name or "CHS{:g}x{:g}".format(d, v("WallThickness")), "CHS", d, d, v("WallThickness"),
                      v("WallThickness"))
    elif kind == "IfcCShapeProfileDef":
        sec = Section(name or "C{:g}x{:g}".format(v("Depth"), v("Width")), "C", v("Depth"), v("Width"),
                      v("WallThickness"), v("WallThickness"), v("InternalFilletRadius"), 0.0, v("Girth"))
    elif kind == "IfcLShapeProfileDef" and getattr(profile, "FilletRadius", None) is not None:
        # (an angle has its root radius; ArqSynth's own concrete L columns have none)
        d, w = v("Depth"), v("Width", v("Depth"))
        sec = Section(name or "L{:g}x{:g}x{:g}".format(d, w, v("Thickness")), "L" if abs(d - w) < 1e-6 else "LU",
                      d, w, v("Thickness"), v("Thickness"), v("FilletRadius"), v("EdgeRadius"))
    else:
        return None
    return sec


SECTIONS.update({_key(name): sec for name, sec in _build().items()})      # (by the key any writing of it gives)
