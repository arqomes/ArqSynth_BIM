"""Welded meshes (0.522, steel plan step 9): a slab's mesh drawn by hand, not from a design — named by its wires'
diameter and spacing ("Ø6 // 0,15"), not by a maker's catalogue (the owner's choice: the commercial names to confirm).
Its wires both ways cut by the slab's outline less the cover, at the bottom face, the top or both; the sheets it takes
(standard 6,00 × 2,40 m, lapped) and its weight; the checks a mesh must pass (cover, spacing, the minimum steel of
EC2 9.3.1.1 and 9.2.1.1).

Pure numpy and shapely; program coordinates in metres, diameters in mm."""

import math
from dataclasses import dataclass

import numpy as np

from . import ec2

DIAMETERS = (5, 6, 7, 8, 10, 12)          # mm: the wires of welded meshes
SPACINGS = (0.10, 0.15, 0.20, 0.25, 0.30)  # m
FACES = ("bottom", "top", "both")
SHEET = (6.00, 2.40)                       # m: the standard sheet
LAP = 0.30                                 # m: the sheets lapped this much each way (≥ 2 meshes' pitches as a rule)
MIN_COVER = 0.015                          # m: EC2 4.4.1.2 cmin,b of a 12 mm wire, XC1 — less is a fault
MAX_SPACING = 0.25                         # m: EC2 9.3.1.1(3) for a slab's main bars (≤ 2h and 250 mm)
MIN_PIECE = 0.10                           # m


@dataclass
class Mesh:
    diameter: int = 6                      # mm, both ways
    spacing: float = 0.15                  # m, both ways
    face: str = "bottom"
    cover: float = 0.025                   # m
    angle: float = 0.0                     # degrees: its longitudinal wires from X

    def name(self, dec=","):
        return "Ø{} // {}".format(self.diameter, "{:.2f}".format(self.spacing).replace(".", dec))

    def stored(self):
        return {"diameter": int(self.diameter), "spacing": float(self.spacing), "face": self.face,
                "cover": float(self.cover), "angle": float(self.angle)}

    @classmethod
    def from_stored(cls, d):
        return cls(int(d.get("diameter", 6)), float(d.get("spacing", 0.15)), d.get("face", "bottom"),
                   float(d.get("cover", 0.025)), float(d.get("angle", 0.0)))

    def area_per_m(self):
        """cm²/m each way."""
        return ec2.bar_area(self.diameter) * 1e4 / self.spacing

    def mass_per_m2(self):
        """kg/m² of one layer (both ways)."""
        return 2.0 * ec2.bar_mass(self.diameter) / self.spacing


def layers(mesh, outline, top, thickness):
    """[(face, z of its lower wires, z of its upper wires)] of a slab's mesh — the bottom one on its cover, the top
    one under the slab's top less its cover."""
    r = mesh.diameter / 2000.0
    out = []
    if mesh.face in ("bottom", "both"):
        z = top - thickness + mesh.cover + r
        out.append(("bottom", z, z + 2.0 * r))
    if mesh.face in ("top", "both"):
        z = top - mesh.cover - r
        out.append(("top", z - 2.0 * r, z))
    return out


def wires(mesh, outline, top, thickness):
    """{face: (longitudinal wires, transverse wires)}: each [(x, y, z), (x, y, z)] — cut by the outline less the
    cover."""
    from shapely.geometry import LineString, Polygon
    poly = Polygon(outline)
    inner = poly.buffer(-mesh.cover, join_style=2)
    if inner.is_empty:
        return {}
    a = math.radians(mesh.angle)
    x = np.array((math.cos(a), math.sin(a)))
    y = np.array((-x[1], x[0]))
    pts = np.asarray(poly.exterior.coords, dtype=float)
    out = {}
    for face, z_low, z_high in layers(mesh, outline, top, thickness):
        both = []
        for ax, ay, z in ((x, y, z_low), (y, x, z_high)):
            along, across = pts @ ax, pts @ ay
            lo, hi = float(across.min()) + mesh.cover, float(across.max()) - mesh.cover
            n = max(int(math.floor((hi - lo) / mesh.spacing + 1e-9)) + 1, 1)
            start = lo + ((hi - lo) - (n - 1) * mesh.spacing) / 2.0
            a0, a1 = float(along.min()) - 1.0, float(along.max()) + 1.0
            bars = []
            for k in range(n):
                v = start + k * mesh.spacing
                cut = LineString([tuple(ax * a0 + ay * v), tuple(ax * a1 + ay * v)]).intersection(inner)
                for piece in getattr(cut, "geoms", [cut]):
                    if piece.is_empty or piece.geom_type != "LineString" or piece.length < MIN_PIECE:
                        continue
                    p0, p1 = list(piece.coords)[0], list(piece.coords)[-1]
                    bars.append([(p0[0], p0[1], z), (p1[0], p1[1], z)])
            both.append(bars)
        out[face] = tuple(both)
    return out


def sheets(mesh, outline):
    """How many standard sheets one layer takes: the slab's area less the cover over a sheet's lapped area,
    rounded up."""
    from shapely.geometry import Polygon
    area = Polygon(outline).buffer(-mesh.cover, join_style=2).area
    if area <= 0.0:
        return 0
    useful = (SHEET[0] - LAP) * (SHEET[1] - LAP)
    return int(math.ceil(area / useful - 1e-9))


def weight(mesh, outline):
    """kg of the mesh in the slab (all its layers), its laps counted: the sheets' weight."""
    n = sheets(mesh, outline) * (2 if mesh.face == "both" else 1)
    return n * SHEET[0] * SHEET[1] * mesh.mass_per_m2()


def checks(mesh, thickness, fck=25.0, fyk=500.0):
    """[(key, ok, values)] of the mesh in a slab this thick: its cover, its spacing (≤ 2h and 250 mm), the minimum
    steel (EC2 9.2.1.1: 0,26 fctm/fyk b d, ≥ 0,0013 b d), two layers fitting in the slab."""
    out = [("cover", mesh.cover >= MIN_COVER - 1e-9, {"c": mesh.cover * 1000.0, "min": MIN_COVER * 1000.0})]
    smax = min(2.0 * thickness, MAX_SPACING)
    out.append(("spacing", mesh.spacing <= smax + 1e-9, {"s": mesh.spacing * 1000.0, "max": smax * 1000.0}))
    d = thickness - mesh.cover - mesh.diameter / 1000.0
    fctm = 0.30 * fck ** (2.0 / 3.0)
    need = max(0.26 * fctm / fyk, 0.0013) * 1.0 * max(d, 0.0) * 1e4       # cm²/m
    out.append(("minimum", mesh.area_per_m() >= need - 1e-9, {"as": mesh.area_per_m(), "min": need}))
    room = thickness - 2.0 * mesh.cover - (4 if mesh.face == "both" else 2) * mesh.diameter / 1000.0
    out.append(("fits", room > 0.0, {"t": thickness * 1000.0}))
    return out
