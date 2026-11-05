"""Kitchen and laundry appliances (0.171, Phase 10, step 1): a hob (electric or gas) and a sink set in the worktop,
an oven in a base unit, a dishwasher and a washing machine under the worktop, a fridge, a microwave, a hood over the
hob — their usual sizes (the ones the cabinets are made for), where they stand (on the floor, in the worktop, hung),
their IFC class and type, their connections (cold water, drain, gas, power) and the cut-out a worktop needs for
them.

Pure Python: an appliance's frame as a cabinet's — x along its width from its left side, y out of the wall (its back
at 0), z up from the floor; metres."""

import numpy as np

from . import cabinets as core_cab
from . import kitchens

WORKTOP_TOP = 0.90              # m: where a hob and a sink sit (the base units' worktop)

# key -> (IFC class, PredefinedType, ObjectType when USERDEFINED, (width, depth, height), its underside over the floor,
#         its cut-out in the worktop (w, d) or None, [(port, (x, y, z) in its frame, IfcDistributionSystemEnum)])
APPLIANCES = {
    "hob": ("IfcElectricAppliance", "ELECTRICCOOKER", None, (0.59, 0.52, 0.05), WORKTOP_TOP - 0.045, (0.56, 0.49),
            []),
    "gas_hob": ("IfcBurner", "USERDEFINED", "GASHOB", (0.59, 0.52, 0.06), WORKTOP_TOP - 0.045, (0.56, 0.49),
                [("gas", (0.10, 0.0, WORKTOP_TOP - 0.10), "GAS")]),
    "oven": ("IfcElectricAppliance", "ELECTRICCOOKER", None, (0.595, 0.55, 0.595), 0.22, None, []),
    # (0.242) an oven in a tall unit's housing, at eye level (put there with it: ifc/cabinets.follow_ovens)
    "oven_column": ("IfcElectricAppliance", "ELECTRICCOOKER", None, (0.595, 0.55, 0.595), core_cab.OVEN_SILL, None,
                    []),
    "dishwasher": ("IfcElectricAppliance", "DISHWASHER", None, (0.598, 0.55, 0.82), 0.03, None,
                   [("cold", (0.10, 0.0, 0.10), "DOMESTICCOLDWATER"), ("drain", (0.45, 0.0, 0.10), "WASTEWATER")]),
    "washing_machine": ("IfcElectricAppliance", "WASHINGMACHINE", None, (0.60, 0.58, 0.85), 0.0, None,
                        [("cold", (0.10, 0.0, 0.70), "DOMESTICCOLDWATER"),
                         ("drain", (0.45, 0.0, 0.60), "WASTEWATER")]),
    "fridge": ("IfcElectricAppliance", "FRIDGE_FREEZER", None, (0.60, 0.65, 1.85), 0.0, None, []),
    "microwave": ("IfcElectricAppliance", "MICROWAVE", None, (0.50, 0.38, 0.30), WORKTOP_TOP, None, []),
    "hood": ("IfcElectricAppliance", "USERDEFINED", "COOKERHOOD", (0.60, 0.50, 0.40), 1.55, None, []),
}
SET_IN_WORKTOP = ("hob", "gas_hob")
# (0.198) an electric appliance's power for the circuits' working out (W) — the program's usual values — and where
# its supply comes to it: its back's middle, this high over its own base
POWERS = {"hob": 7000.0, "oven": 3500.0, "oven_column": 3500.0, "dishwasher": 2200.0, "washing_machine": 2200.0,
          "fridge": 300.0, "microwave": 1200.0, "hood": 250.0}
HOUSED = ("oven_column",)       # (0.242) put in a cabinet by the program, not by hand
POWER_PORT_UP = 0.05


def size(kind):
    return APPLIANCES[kind][3]


def elevation(kind):
    return APPLIANCES[kind][4]


def cutout(kind):
    return APPLIANCES[kind][5]


def ports(kind):
    return APPLIANCES[kind][6]


def boxes(kind):
    """The appliance's body as boxes (x0, y0, z0, x1, y1, z1) in its frame: its casing, and what tells it at a
    glance — a hob's burners' plate, an oven's and a dishwasher's door, a fridge's two doors, a hood's chimney."""
    w, d, h = size(kind)
    z0 = elevation(kind)
    out = []
    if kind in ("hob", "gas_hob"):
        out.append((0.0, 0.0, z0 + 0.04, w, d, z0 + 0.045))                       # (the glass, flush on the top)
        out.append((0.015, 0.015, z0, w - 0.015, d - 0.015, z0 + 0.04))          # (the box, in the cut-out)
        if kind == "gas_hob":
            for cx, cy in ((0.15, 0.13), (0.44, 0.13), (0.15, 0.39), (0.44, 0.39)):
                out.append((cx - 0.04, cy - 0.04, z0 + 0.045, cx + 0.04, cy + 0.04, z0 + h))   # (the burners)
        return out
    if kind == "hood":
        out.append((0.0, 0.0, z0, w, d, z0 + 0.08))                              # (the canopy)
        out.append((w / 2 - 0.13, 0.0, z0 + 0.08, w / 2 + 0.13, 0.25, z0 + h + 0.60))   # (the chimney)
        return out
    inset = 0.02 if kind in HOUSED else 0.0             # (0.242: a housed one's casing between its unit's sides,
    out.append((inset, 0.0, z0, w - inset, d - 0.02, z0 + h))      # its door over them)            (the casing)
    if kind == "fridge":
        split = z0 + h * 0.62
        out.append((0.005, d - 0.02, z0 + 0.005, w - 0.005, d, split - 0.005))   # (the freezer's door below)
        out.append((0.005, d - 0.02, split + 0.005, w - 0.005, d, z0 + h - 0.005))
    else:
        out.append((0.005, d - 0.02, z0 + 0.005, w - 0.005, d, z0 + h - 0.005))  # (its door / front)
    return out


SINK = ((0.80, 0.60), (0.76, 0.46))        # a kitchen sink fixture's (0.140) plan, and its cut-out


def sink_ring(back_mid, angle):
    """The plan rectangle a worktop is cut by for a kitchen sink (ifc/sanitary "kitchen_sink")."""
    (w, d), cut = SINK
    return _ring(back_mid, angle, w, d, cut)


def cutout_ring(kind, back_mid, angle):
    """The plan rectangle a worktop is cut by for an appliance set in it (4 corners), or None."""
    cut = cutout(kind)
    if cut is None:
        return None
    w, d, _h = size(kind)
    return _ring(back_mid, angle, w, d, cut)


def _ring(back_mid, angle, w, d, cut):
    cw, cd = cut
    rect = kitchens.footprint(back_mid, angle, w, d)
    o, x_end, _far, y_end = (np.asarray(p, dtype=float) for p in rect)
    x = (x_end - o) / max(np.linalg.norm(x_end - o), 1e-12)
    y = (y_end - o) / max(np.linalg.norm(y_end - o), 1e-12)
    a = o + x * (w - cw) / 2 + y * (d - cd) / 2
    return [a, a + x * cw, a + x * cw + y * cd, a + y * cd]
