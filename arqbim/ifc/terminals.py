"""Air terminals (0.138, Phase 6, step 2 — HVAC): a diffuser or a grille set in the ceiling (IfcAirTerminal), its
face at the ceiling, its neck above it and, on top of the neck, its port (an IfcDistributionPort, DUCT) where a
duct comes down to it. A supply diffuser takes the air in from the duct (its port a SINK); a return grille gives
it to the duct (a SOURCE)."""

import numpy as np

import ifcopenshell.api as api
import ifcopenshell.api.system  # noqa: F401

# kind -> (PredefinedType, the face: (w, d) or a diameter, the neck: (w, d) or a diameter, the air: "supply" | "return")
TERMINALS = {
    "diffuser_60": ("DIFFUSER", (0.595, 0.595), (0.25, 0.25), "supply"),
    "diffuser_30": ("DIFFUSER", (0.295, 0.295), (0.15, 0.15), "supply"),
    "round_diffuser": ("DIFFUSER", 0.30, 0.20, "supply"),
    "grille_60x30": ("GRILLE", (0.595, 0.295), (0.40, 0.20), "return"),
}
FACE = 0.04                 # m: the face's thickness, from the ceiling up
NECK = 0.15                 # m: the neck above it, up to its port
UNIT_REACH = 0.25           # m (0.139): how near a unit's port a click takes it


class TerminalMixin:
    def add_air_terminal(self, point, z, kind, name, storey=None):
        """An air terminal of this kind at `point` (plan), its face at the level z (the ceiling's underside):
        the face, the neck over it and its port on top (DUCT). Returns it."""
        f, u = self.file, 1.0 / self.unit_scale
        predefined, face, neck, air = TERMINALS[kind]
        terminal = api.root.create_entity(f, ifc_class="IfcAirTerminal", name=name, predefined_type=predefined)
        m = np.eye(4)
        m[:3, 3] = (float(point[0]), float(point[1]), float(z))
        self._place(terminal, m)
        origin2 = f.createIfcAxis2Placement2D(f.createIfcCartesianPoint((0.0, 0.0)), None)

        def profile(size):
            if isinstance(size, tuple):
                return f.createIfcRectangleProfileDef("AREA", None, origin2, float(size[0] * u), float(size[1] * u))
            return f.createIfcCircleProfileDef("AREA", None, origin2, float(size / 2 * u))

        items = [f.createIfcExtrudedAreaSolid(profile(size), f.createIfcAxis2Placement3D(
            f.createIfcCartesianPoint((0.0, 0.0, float(z0 * u))), None, None), f.createIfcDirection((0.0, 0.0, 1.0)),
            float(height * u)) for size, z0, height in ((face, 0.0, FACE), (neck, FACE, NECK))]
        api.geometry.assign_representation(f, product=terminal, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))
        container = self.storey(storey) if storey is not None else self.storey_at(float(z))
        api.spatial.assign_container(f, products=[terminal], relating_structure=container)
        self._mark(terminal, "air_terminal")
        self._set_params(terminal, {"Terminal": kind})
        port = api.system.add_port(f, element=terminal)
        port.Name, port.PredefinedType = "1", "DUCT"
        port.FlowDirection = "SINK" if air == "supply" else "SOURCE"
        top = np.eye(4)
        top[:3, 3] = (float(point[0]), float(point[1]), float(z) + FACE + NECK)
        self._place(port, top)
        return terminal

    def terminal_params(self, guid):
        """{kind, face's level, the port's point (3,), its air ("supply" | "return")} of an air terminal."""
        e = self.by_guid(guid)
        kind = self._params(e).get("Terminal") or "diffuser_60"
        m = self._placement_si(e)
        ports = self.ports(guid)
        at = self._placement_si(ports[0])[:3, 3].copy() if ports else m[:3, 3] + np.array((0.0, 0.0, FACE + NECK))
        return {"kind": kind, "z": float(m[2, 3]), "port": at, "air": TERMINALS.get(kind, TERMINALS["diffuser_60"])[3]}

    def free_port_near(self, point, reach, classes=("IfcAirTerminal", "IfcUnitaryEquipment"), system="DUCT",
                       prefer=None):
        """(0.138) An element of these classes with a free port of this system (DUCT, PIPE — 0.139) whose face is
        under `point` in plan (or the port within `reach`): (its GlobalId, the port, the port's point (3,)), or
        None — a duct ends on it (or starts from it). prefer (0.141): the key of the system being drawn — of the
        ports there, one of that system first, then one of its family (a drain, a supply), then the nearest."""
        from .systems import SYSTEMS
        p = np.asarray(point, dtype=float)[:2]
        best = None

        def rank(port):
            key = self.port_system(port)                        # (0.196: a refrigerant port's line, by its name)
            cold = lambda k: (k or "").startswith("refrigerant")    # noqa: E731
            if cold(key) != cold(prefer):                       # (0.196) a refrigerant line only to its ports
                return 3
            if prefer is None or key is None or prefer not in SYSTEMS:
                return 1
            return 0 if key == prefer else (1 if SYSTEMS[key][4] == SYSTEMS[prefer][4] else 2)
        for cls in classes:
            for e in self.file.by_type(cls):
                for port in self.ports(e.GlobalId):
                    if self.connected(port) is not None or (port.PredefinedType or "DUCT") != system:
                        continue
                    at = self._placement_si(port)[:3, 3]
                    gap = float(np.linalg.norm(at[:2] - p))
                    kind = self._params(e).get("Terminal")
                    face = TERMINALS[kind][1] if kind in TERMINALS else None
                    half = (max(face) if isinstance(face, tuple) else face) / 2 if face else UNIT_REACH
                    over = self._over_element(e, p)         # (0.141) anywhere over a fixture / a unit: all its ports
                    order = (rank(port), gap)
                    if (over or gap <= max(reach, half)) and (best is None or order < best[0]):
                        best = (order, e.GlobalId, port, at.copy())
        return None if best is None else best[1:]

    def _over_element(self, e, p):
        """(0.141) Is the plan point p over this fixture's / unit's outline?"""
        from .equipment import EQUIPMENT
        from .sanitary import FIXTURES
        params = self._params(e)
        if params.get("Louca") in FIXTURES:
            w, d, _h = FIXTURES[params["Louca"]][1]
            box = (-w / 2, w / 2, 0.0, d)
        elif params.get("Equipamento") in EQUIPMENT:
            length, depth, _h = EQUIPMENT[params["Equipamento"]][1]
            box = (-length / 2, length / 2, -depth / 2, depth / 2)
        else:
            return False
        m = self._placement_si(e)
        local = np.linalg.inv(m) @ np.array((float(p[0]), float(p[1]), float(m[2, 3]), 1.0))
        return box[0] - 1e-6 <= local[0] <= box[1] + 1e-6 and box[2] - 1e-6 <= local[1] <= box[3] + 1e-6

    def free_port(self, guid, near=None, system=None):
        """(0.138) A free port of an element (a terminal's, a unit's): the one nearest `near` (plan; else the
        first) of this system (any when None): (the port, its point (3,)), or None."""
        found = []
        for port in self.ports(guid):
            if self.connected(port) is None and (system is None or (port.PredefinedType or "DUCT") == system):
                at = self._placement_si(port)[:3, 3].copy()
                gap = 0.0 if near is None else float(np.linalg.norm(at[:2] - np.asarray(near, dtype=float)[:2]))
                found.append((gap, len(found), port, at))
        return min(found)[2:] if found else None

    def port_way(self, port):
        """(0.139) The way out of an element through this port (its Z): a unit vector (3,)."""
        z = self._placement_si(port)[:3, 2]
        return z / np.linalg.norm(z)

    def connect_to_port(self, segment, port, at_end=True):
        """(0.138) A pipe's / duct's end (or start) connected to another element's port (a terminal's)."""
        ports = self.ports(segment)
        if len(ports) == 2:
            if at_end:
                self._connect(ports[1], port)
            else:
                self._connect(port, ports[0])
