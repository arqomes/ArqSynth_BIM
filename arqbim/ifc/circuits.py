"""Circuits (0.144, Phase 6, step 4): the electrical points (and lights) grouped into the circuits of a board — as the
IFC says it, an IfcDistributionCircuit each (a group: its points and its board assigned to it), named "C1", "C2"…
— with what the program needs to work them out kept on it (its type, its breaker, its cable's section, its board):
its power (the points' powers added up), its current (single-phase, 230 V) and a simple check.

The powers per point, the breakers and sections are the program's usual values, to be changed by the project: the
check is not the regulation's — an electrical project is checked by its engineer."""

import ifcopenshell.api as api
import ifcopenshell.api.system  # noqa: F401
import ifcopenshell.util.element

CIRCUIT_PSET = "ArqSynth_Circuito"
VOLTAGE = 230.0
# circuit type -> (its usual breaker (A), its cable's section (mm²), most points on it, IfcDistributionSystemEnum)
TYPES = {
    "lighting": (10, 1.5, 8, "LIGHTING"),
    "outlets": (16, 2.5, 8, "ELECTRICAL"),
    "kitchen": (20, 4.0, 4, "ELECTRICAL"),
    "appliance": (20, 4.0, 1, "ELECTRICAL"),
    "hvac": (16, 2.5, 2, "ELECTRICAL"),
}
# a point's power for the working out (W): (an electrical point's kind, or a light)
POWERS = {"light": 100.0, "outlet": 300.0, "outlet_double": 400.0, "outlet_counter": 1000.0, "data_outlet": 0.0,
          "switch": 0.0, "switch_two_way": 0.0, "junction_box": 0.0, "board": 0.0, "equipment": 2000.0}
LOADS = ("IfcOutlet", "IfcSwitchingDevice", "IfcLightFixture", "IfcJunctionBox", "IfcUnitaryEquipment",
         "IfcElectricAppliance")                                                    # (appliances: 0.198)


class CircuitMixin:
    def circuits(self):
        """[(GlobalId, name)] of the project's circuits, in name order (C1, C2… C10)."""
        found = [(c.GlobalId, c.Name or "") for c in self.file.by_type("IfcDistributionCircuit")]

        def order(item):
            name = item[1]
            digits = "".join(ch for ch in name if ch.isdigit())
            return (int(digits) if digits else 10 ** 6, name)
        return sorted(found, key=order)

    def _circuit_params(self, circuit):
        return ifcopenshell.util.element.get_psets(circuit).get(CIRCUIT_PSET, {})

    def add_circuit(self, kind, points, board=None, name=None):
        """A new circuit of this type with these points (GlobalIds; out of any other circuit) and its board. Returns
        its GlobalId."""
        f = self.file
        taken = [int("".join(ch for ch in (n or "") if ch.isdigit()) or 0) for _g, n in self.circuits()]
        circuit = api.system.add_system(f, ifc_class="IfcDistributionCircuit")
        breaker, section, _most, predefined = TYPES[kind]
        circuit.Name = name or "C{}".format(max(taken, default=0) + 1)
        circuit.PredefinedType = predefined
        pset = api.pset.add_pset(f, product=circuit, name=CIRCUIT_PSET)
        api.pset.edit_pset(f, pset=pset, properties={"Tipo": kind, "Disjuntor": float(breaker),
                                                     "Seccao": float(section), "Quadro": board or ""})
        self.set_circuit_points(circuit.GlobalId, points)
        return circuit.GlobalId

    def set_circuit_points(self, guid, points, add=False):
        """These points into the circuit `guid` (out of any other circuit; add: kept with those it has)."""
        circuit = self.by_guid(guid)
        old = [] if add else [g for g in self.circuit_points(guid)]
        for g in old:
            api.system.unassign_system(self.file, products=[self.by_guid(g)], system=circuit)
        for g in points:
            e = self.by_guid(g)
            if e is None or not e.is_a("IfcDistributionElement"):
                continue
            for other_guid, _n in self.circuits():
                if other_guid != guid and g in self.circuit_points(other_guid):
                    api.system.unassign_system(self.file, products=[e], system=self.by_guid(other_guid))
            if g not in self.circuit_points(guid):
                api.system.assign_system(self.file, products=[e], system=circuit)

    def circuit_points(self, guid):
        """The GlobalIds of what is in the circuit `guid`."""
        c = self.by_guid(guid)
        return [o.GlobalId for rel in getattr(c, "IsGroupedBy", None) or () for o in rel.RelatedObjects]

    def circuit_of(self, guid):
        """The circuit a point is in: its GlobalId, or None."""
        e = self.by_guid(guid)
        for rel in getattr(e, "HasAssignments", None) or ():
            group = getattr(rel, "RelatingGroup", None)
            if group is not None and group.is_a("IfcDistributionCircuit"):
                return group.GlobalId
        return None

    def edit_circuit(self, guid, kind=None, breaker=None, section=None, name=None, board=None):
        """A circuit's type (its breaker and section take that type's usual ones, unless given), breaker (A),
        cable's section (mm²), name, board."""
        c = self.by_guid(guid)
        props = {}
        if kind is not None:
            props.update(Tipo=kind, Disjuntor=float(TYPES[kind][0]), Seccao=float(TYPES[kind][1]))
            c.PredefinedType = TYPES[kind][3]
        if breaker is not None:
            props["Disjuntor"] = float(breaker)
        if section is not None:
            props["Seccao"] = float(section)
        if board is not None:
            props["Quadro"] = board
        if name is not None:
            c.Name = name
        if props:
            pset = self.file.by_id(ifcopenshell.util.element.get_psets(c)[CIRCUIT_PSET]["id"])
            api.pset.edit_pset(self.file, pset=pset, properties=props)

    def remove_circuit(self, guid):
        """The circuit goes (its points stay, in no circuit)."""
        api.system.remove_system(self.file, system=self.by_guid(guid))

    def point_power(self, guid):
        """A point's power for the working out (W)."""
        e = self.by_guid(guid)
        if e.is_a("IfcLightFixture"):
            return POWERS["light"]
        if e.is_a("IfcUnitaryEquipment"):
            return POWERS["equipment"]
        if e.is_a("IfcElectricAppliance"):               # (0.198) an oven, a dishwasher…: its kind's
            from ..core.appliances import POWERS as APPLIANCE_POWERS
            return APPLIANCE_POWERS.get(self._params(e).get("Aparelho") or "", 2000.0)
        return POWERS.get(self._params(e).get("Ponto") or "", 0.0)

    def circuit_report(self, guid):
        """{name, kind, board, breaker, section, points (how many), power (W), current (A), ok, why} of a circuit:
        its power, its current at 230 V, and the check — its current within its breaker, not more points than its
        type takes, a section of at least its type's for its breaker."""
        c = self.by_guid(guid)
        p = self._circuit_params(c)
        kind = p.get("Tipo") or "outlets"
        points = self.circuit_points(guid)
        loads = [g for g in points if self.by_guid(g).is_a() in LOADS]
        power = sum(self.point_power(g) for g in loads)
        current = power / VOLTAGE
        breaker = float(p.get("Disjuntor") or TYPES[kind][0])
        section = float(p.get("Seccao") or TYPES[kind][1])
        most = TYPES.get(kind, TYPES["outlets"])[2]
        why = []
        if current > breaker + 1e-9:
            why.append("current")
        if len(loads) > most:
            why.append("points")
        if section + 1e-9 < min_section(breaker):
            why.append("section")
        conduit = self.conduit_length(guid) if hasattr(self, "conduit_length") else 0.0     # (0.146)
        return {"name": c.Name or "", "kind": kind, "board": p.get("Quadro") or "", "breaker": breaker,
                "section": section, "points": len(loads), "power": power, "current": current, "ok": not why,
                "why": why, "conduit": conduit}


def min_section(breaker):
    """The program's least cable section (mm²) for a breaker (A): 10 A 1,5; 16 A 2,5; 20 A 4; 25 / 32 A 6; more 10."""
    for top, section in ((10, 1.5), (16, 2.5), (20, 4.0), (32, 6.0)):
        if breaker <= top + 1e-9:
            return section
    return 10.0
