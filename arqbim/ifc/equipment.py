"""HVAC equipment (0.139, Phase 6, step 2): a unit placed by a click (IfcUnitaryEquipment) — a ducted unit in the
ceiling void, a wall split, an outdoor unit, an air handling unit —, a box of its size turned as asked, with its
ports (IfcDistributionPort) where its ducts (and its condensate drain) are connected: each one's Z pointing out
of the unit, the way a duct leaves it."""

import math

import numpy as np

import ifcopenshell.api as api
import ifcopenshell.api.system  # noqa: F401

# kind -> (PredefinedType, (length, depth, height) m, its base over the storey by default,
#          ports: [(name, (x, y, z) from the middle of its base, the way out (x, y, z), "DUCT" | "PIPE", flow,
#                   (0.196) its SystemType, or none)])
_REFRIGERANT = "REFRIGERATION"
EQUIPMENT = {
    "ducted_unit": ("AIRCONDITIONINGUNIT", (1.00, 0.70, 0.27), 2.60,
                    [("supply", (0.50, 0.0, 0.135), (1.0, 0.0, 0.0), "DUCT", "SOURCE"),
                     ("return", (-0.50, 0.0, 0.135), (-1.0, 0.0, 0.0), "DUCT", "SINK"),
                     ("condensate", (-0.40, -0.35, 0.04), (0.0, -1.0, 0.0), "PIPE", "SOURCE"),
                     ("liquid", (-0.25, -0.35, 0.10), (0.0, -1.0, 0.0), "PIPE", "SOURCEANDSINK", _REFRIGERANT),
                     ("gas", (-0.15, -0.35, 0.10), (0.0, -1.0, 0.0), "PIPE", "SOURCEANDSINK", _REFRIGERANT)]),
    "split_wall": ("SPLITSYSTEM", (0.90, 0.22, 0.30), 2.10,
                   [("condensate", (-0.40, 0.11, 0.03), (0.0, 1.0, 0.0), "PIPE", "SOURCE"),
                    ("liquid", (-0.30, 0.11, 0.08), (0.0, 1.0, 0.0), "PIPE", "SOURCEANDSINK", _REFRIGERANT),
                    ("gas", (-0.20, 0.11, 0.08), (0.0, 1.0, 0.0), "PIPE", "SOURCEANDSINK", _REFRIGERANT)]),
    "outdoor_unit": ("SPLITSYSTEM", (0.85, 0.33, 0.60), 0.0,
                     [("liquid", (0.425, 0.04, 0.10), (1.0, 0.0, 0.0), "PIPE", "SOURCEANDSINK", _REFRIGERANT),
                      ("gas", (0.425, 0.10, 0.18), (1.0, 0.0, 0.0), "PIPE", "SOURCEANDSINK", _REFRIGERANT)]),
    "ahu": ("AIRHANDLER", (2.00, 1.00, 1.20), 0.0,
            [("supply", (0.60, 0.0, 1.20), (0.0, 0.0, 1.0), "DUCT", "SOURCE"),
             ("return", (-0.60, 0.0, 1.20), (0.0, 0.0, 1.0), "DUCT", "SINK")]),
}


def frame(base, angle):
    """The placement of a unit: the middle of its base at `base` (3,), its length along `angle` degrees from the
    red axis."""
    a = math.radians(float(angle))
    x = np.array((math.cos(a), math.sin(a), 0.0))
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, np.cross((0.0, 0.0, 1.0), x), (0.0, 0.0, 1.0), base
    return m


def footprint(base, angle, kind):
    """Its four corners at its base (plan, 3D) — the outline the tool shows."""
    length, depth, _h = EQUIPMENT[kind][1]
    m = frame(np.asarray(base, dtype=float), angle)
    return [m[:3, 3] + m[:3, 0] * sx * length / 2 + m[:3, 1] * sy * depth / 2
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


class EquipmentMixin:
    def add_equipment(self, base, angle, kind, name, storey=None):
        """A unit of this kind, the middle of its base at `base` (3,), its length along `angle` degrees: a box
        of its size and its ports, each placed with its Z out of the unit. Returns it."""
        f, u = self.file, 1.0 / self.unit_scale
        predefined, (length, depth, height), _base, ports = EQUIPMENT[kind]
        unit = api.root.create_entity(f, ifc_class="IfcUnitaryEquipment", name=name, predefined_type=predefined)
        m = frame(np.asarray(base, dtype=float), angle)
        self._place(unit, m)
        origin2 = f.createIfcAxis2Placement2D(f.createIfcCartesianPoint((0.0, 0.0)), None)
        box = f.createIfcExtrudedAreaSolid(
            f.createIfcRectangleProfileDef("AREA", None, origin2, float(length * u), float(depth * u)),
            f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)), None, None),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(height * u))
        api.geometry.assign_representation(f, product=unit, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", [box]))
        container = self.storey(storey) if storey is not None else self.storey_at(float(base[2]))
        api.spatial.assign_container(f, products=[unit], relating_structure=container)
        self._mark(unit, "equipment")
        self._set_params(unit, {"Equipamento": kind, "Angulo": float(angle)})
        for port_name, at, way, system, flow, *system_type in ports:
            port = api.system.add_port(f, element=unit)
            port.Name, port.PredefinedType, port.FlowDirection = port_name, system, flow
            if system_type:                                  # (0.196) a refrigerant line's: REFRIGERATION
                port.SystemType = system_type[0]
            p = m[:3, 3] + m[:3, :3] @ np.asarray(at, dtype=float)
            w = m[:3, :3] @ np.asarray(way, dtype=float)
            self._place(port, self._port_frame(p, w, m[:3, 0] if abs(w[2]) > 0.7 else None))
        return unit

    def equipment_params(self, guid):
        """{kind, the middle of its base (3,), its angle (degrees)} of a unit made by this program."""
        e = self.by_guid(guid)
        p = self._params(e)
        m = self._placement_si(e)
        return {"kind": p.get("Equipamento") or "ducted_unit", "base": m[:3, 3].copy(),
                "angle": float(p.get("Angulo") or 0.0)}
