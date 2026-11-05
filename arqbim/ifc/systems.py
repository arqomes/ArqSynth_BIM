"""Systems (0.141, Phase 6): which network a pipe, a duct, their fittings and the terminals belong to — cold or hot
water, sewage, waste water, rainwater; supply, return, exhaust or fresh air — as the IFC says it: one
IfcDistributionSystem per system used in the project (its PredefinedType and its name), the elements assigned to
it (IfcRelAssignsToGroup), and their ports' SystemType."""

import ifcopenshell.api as api
import ifcopenshell.api.system  # noqa: F401

# key -> (the kind it is for, IfcDistributionSystemEnum, (name pt, name en), colour on screen, a drain: it falls)
SYSTEMS = {
    "cold": ("pipe", "DOMESTICCOLDWATER", ("Água fria", "Cold water"), "#3b7fd9", False),
    "hot": ("pipe", "DOMESTICHOTWATER", ("Água quente", "Hot water"), "#d9483b", False),
    "sewage": ("pipe", "SEWAGE", ("Águas negras", "Sewage"), "#7a5233", True),
    "waste": ("pipe", "WASTEWATER", ("Águas saponáceas", "Waste water"), "#a88a5c", True),
    "rain": ("pipe", "RAINWATER", ("Águas pluviais", "Rainwater"), "#2fb0c2", True),
    "gas": ("pipe", "GAS", ("Gás", "Gas"), "#e0b81a", False),                  # (0.171: a gas hob's)
    # (0.196) a split system's two refrigerant lines, between its indoor and outdoor units
    "refrigerant_liquid": ("pipe", "REFRIGERATION", ("Refrigerante — líquido", "Refrigerant — liquid"), "#b5622a",
                           False),
    "refrigerant_gas": ("pipe", "REFRIGERATION", ("Refrigerante — gás", "Refrigerant — gas"), "#e39545", False),
    "supply_air": ("duct", "VENTILATION", ("Insuflação", "Supply air"), "#7fb2e5", False),
    "return_air": ("duct", "VENTILATION", ("Retorno", "Return air"), "#8fc98f", False),
    "exhaust": ("duct", "EXHAUST", ("Extração", "Exhaust"), "#d9b54a", False),
    "fresh_air": ("duct", "VENTILATION", ("Ar novo", "Fresh air"), "#b5d9e8", False),
}
DEFAULT = {"pipe": "cold", "duct": "supply_air"}
# a port's SystemType (a fixture's, a unit's) -> the system a pipe started from it takes
FROM_PORT = {"DOMESTICCOLDWATER": "cold", "DOMESTICHOTWATER": "hot", "SEWAGE": "sewage", "WASTEWATER": "waste",
             "RAINWATER": "rain", "EXHAUST": "exhaust", "GAS": "gas"}


def of_kind(kind):
    """The systems a pipe / a duct can be in, in order."""
    return [k for k, v in SYSTEMS.items() if v[0] == kind]


class SystemMixin:
    def _system_entity(self, key, lang="pt"):
        """The project's IfcDistributionSystem for this key (made the first time), found by its name."""
        _kind, predefined, names, _colour, _drain = SYSTEMS[key]
        for s in self.file.by_type("IfcDistributionSystem"):
            if (s.Name or "") in names and s.PredefinedType == predefined and not s.is_a("IfcDistributionCircuit"):
                return s
        system = api.system.add_system(self.file, ifc_class="IfcDistributionSystem")
        system.Name, system.PredefinedType = names[0 if lang == "pt" else 1], predefined
        return system

    def system_of(self, guid):
        """The key of the system an element belongs to (one made by this program, or one whose name and type are
        those of ours), or None."""
        e = self.by_guid(guid)
        if e is None:
            return None
        for rel in getattr(e, "HasAssignments", None) or ():
            group = getattr(rel, "RelatingGroup", None)
            if group is not None and group.is_a("IfcDistributionSystem") and not group.is_a("IfcDistributionCircuit"):
                for key, (_k, predefined, names, _c, _d) in SYSTEMS.items():
                    if (group.Name or "") in names and group.PredefinedType == predefined:
                        return key
        return None

    def systems_of(self, guids):
        """{GlobalId: system key} of those among `guids` that are in one."""
        out = {}
        for g in guids:
            key = self.system_of(g)
            if key is not None:
                out[g] = key
        return out

    def set_system(self, guids, key, lang="pt"):
        """These elements (pipes, ducts, fittings, terminals) into the system `key` — out of any other — and their
        ports' SystemType its type."""
        system = self._system_entity(key, lang)
        predefined = SYSTEMS[key][1]
        for g in guids:
            e = self.by_guid(g)
            if e is None or not e.is_a("IfcDistributionElement"):
                continue
            for rel in list(getattr(e, "HasAssignments", None) or ()):
                group = getattr(rel, "RelatingGroup", None)
                if group is not None and group.is_a("IfcDistributionSystem") and group != system \
                        and not group.is_a("IfcDistributionCircuit"):          # (its circuit stays, 0.144)
                    api.system.unassign_system(self.file, products=[e], system=group)
            if not any(getattr(rel, "RelatingGroup", None) == system for rel in getattr(e, "HasAssignments", None) or ()):
                api.system.assign_system(self.file, products=[e], system=system)
            if e.is_a("IfcFlowSegment") or e.is_a("IfcFlowFitting"):
                for port in self.ports(g):
                    port.SystemType = predefined
        self._drop_empty_systems()

    def _drop_empty_systems(self):
        """A system with nothing left in it goes (the IFC keeps no empty groups of ours)."""
        for s in list(self.file.by_type("IfcDistributionSystem")):
            if s.is_a("IfcDistributionCircuit"):
                continue
            if not any(rel.RelatedObjects for rel in getattr(s, "IsGroupedBy", None) or ()):
                if any(s.Name in v[2] for v in SYSTEMS.values()):
                    api.system.remove_system(self.file, system=s)

    def run_of(self, guid):
        """The element and all those connected to it through pipes and fittings (not through terminals / units /
        fixtures: another network can start there)."""
        out, stack, seen = [], [guid], {guid}
        while stack:
            g = stack.pop()
            out.append(g)
            e = self.by_guid(g)
            if e is None or not (e.is_a("IfcFlowSegment") or e.is_a("IfcFlowFitting")):
                continue
            for port in self.ports(g):
                other = self.connected(port)
                owner = self.owner_of(other) if other is not None else None
                if owner is not None and owner.GlobalId not in seen and (owner.is_a("IfcFlowSegment")
                                                                          or owner.is_a("IfcFlowFitting")):
                    seen.add(owner.GlobalId)
                    stack.append(owner.GlobalId)
        return out

    def port_system(self, port):
        """The system key a port's SystemType stands for (a fixture's drain: sewage / waste…), or None — (0.196) a
        unit's refrigerant port: its liquid or its gas line, by its name."""
        if getattr(port, "SystemType", None) == "REFRIGERATION":
            return "refrigerant_liquid" if (port.Name or "") == "liquid" else "refrigerant_gas"
        return FROM_PORT.get(getattr(port, "SystemType", None) or "")
