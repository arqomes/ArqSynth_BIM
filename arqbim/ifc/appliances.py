"""Appliances (0.171, Phase 10, step 1), mixed into IfcModel: a kitchen's or a laundry's — an IfcElectricAppliance
(ELECTRICCOOKER: a hob, an oven; DISHWASHER, WASHINGMACHINE, FRIDGE_FREEZER, MICROWAVE; USERDEFINED COOKERHOOD) or
an IfcBurner (USERDEFINED GASHOB: a gas hob) — put as a fixture is (its back's middle, its angle), its body from
core/appliances.boxes, its connections as IfcDistributionPorts (cold water, waste water, gas) so that pipes start
from them. A hob set in a worktop cuts it (the worktop's body is made again with the hole, core/appliances).

ArqSynth_Parametros: Elemento "appliance", Aparelho (its key), Angulo."""

import math

import numpy as np

import ifcopenshell.api as api
import ifcopenshell.api.system  # noqa: F401

from ..core import appliances as core_app


def appliance_frame(back, angle):
    a = math.radians(float(angle))
    x = np.array((math.cos(a), math.sin(a), 0.0))
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, np.cross((0.0, 0.0, 1.0), x), (0.0, 0.0, 1.0), back
    return m


class ApplianceMixin:
    def add_appliance(self, back, angle, kind, name, lang="pt", storey=None):
        """An appliance of this kind (core/appliances.APPLIANCES), the middle of its back at `back` (3,: at its
        floor), its width along `angle` degrees. Returns it."""
        f, u = self.file, 1.0 / self.unit_scale
        ifc_class, predefined, object_type, (w, _d, _h), _z0, _cut, ports = core_app.APPLIANCES[kind]
        element = api.root.create_entity(f, ifc_class=ifc_class, name=name, predefined_type=predefined)
        if object_type:
            element.ObjectType = object_type
        m = appliance_frame(np.asarray(back, dtype=float), angle)
        self._place(element, m)
        items = []
        for x0, y0, z0, x1, y1, z1 in core_app.boxes(kind):
            x0, x1 = x0 - w / 2, x1 - w / 2                      # (its frame at its back's middle)
            profile = f.createIfcRectangleProfileDef("AREA", None, f.createIfcAxis2Placement2D(
                f.createIfcCartesianPoint((float((x0 + x1) / 2 * u), float((y0 + y1) / 2 * u))), None),
                float((x1 - x0) * u), float((y1 - y0) * u))
            items.append(f.createIfcExtrudedAreaSolid(
                profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, float(z0 * u))), None, None),
                f.createIfcDirection((0.0, 0.0, 1.0)), float((z1 - z0) * u)))
        api.geometry.assign_representation(f, product=element, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))
        container = self.storey(storey) if storey is not None else self.storey_at(float(back[2]))
        api.spatial.assign_container(f, products=[element], relating_structure=container)
        api.material.assign_material(f, products=[element], type="IfcMaterial", material=self._material("aco", lang))
        self._mark(element, "appliance")
        self._set_params(element, {"Aparelho": kind, "Angulo": float(angle)})
        for port_name, at, system in ports:
            port = api.system.add_port(f, element=element)
            port.Name, port.PredefinedType, port.SystemType = port_name, "PIPE", system
            port.FlowDirection = "SOURCE" if port_name == "drain" else "SINK"
            p = m[:3, 3] + m[:3, :3] @ (np.asarray(at, dtype=float) - np.array((w / 2, 0.0, 0.0)))
            self._place(port, self._port_frame(p, m[:3, :3] @ np.array((0.0, -1.0, 0.0)), None))
        if ifc_class == "IfcElectricAppliance":         # (0.198) its supply: a conduit and its circuit come to it
            port = api.system.add_port(f, element=element)
            port.Name, port.PredefinedType, port.SystemType, port.FlowDirection = "power", "CABLE", "ELECTRICAL", "SINK"
            p = m[:3, 3] + m[:3, :3] @ np.array((0.0, 0.0, _z0 + core_app.POWER_PORT_UP))
            self._place(port, self._port_frame(p, m[:3, :3] @ np.array((0.0, -1.0, 0.0)), None))
        return element

    def appliance_params(self, guid):
        """{kind, the middle of its back (3,), its angle} of an appliance made by this program."""
        e = self.by_guid(guid)
        p = self._params(e)
        m = self._placement_si(e)
        return {"kind": p.get("Aparelho") or "hob", "back": m[:3, 3].copy(), "angle": float(p.get("Angulo") or 0.0)}

    def worktop_cutouts(self):
        """[plan rings (4 corners)] of what is set in a worktop: hobs (0.171) and kitchen sinks."""
        out = []
        for cls in ("IfcElectricAppliance", "IfcBurner"):
            for e in self.file.by_type(cls):
                p = self._params(e)
                if p.get("Elemento") == "appliance" and p.get("Aparelho") in core_app.SET_IN_WORKTOP:
                    a = self.appliance_params(e.GlobalId)
                    out.append(core_app.cutout_ring(a["kind"], a["back"][:2], a["angle"]))
        for e in self.file.by_type("IfcSanitaryTerminal"):
            p = self._params(e)
            if p.get("Louca") == "kitchen_sink":
                fp = self.fixture_params(e.GlobalId)
                out.append(core_app.sink_ring(fp["back"][:2], fp["angle"]))
        return [r for r in out if r is not None]
