"""Sanitary fixtures with their connections (0.140, Phase 6, step 3): a WC, a washbasin, a bidet, a shower tray, a
bath, a kitchen sink (IfcSanitaryTerminal), made by the program — a simple solid of their size, their back
against a wall — with their ports: the drain (SEWAGE for a WC, WASTEWATER for the others: a SOURCE, the water
leaves) and the cold and hot water (DOMESTICCOLDWATER / DOMESTICHOTWATER: a SINK), each port's Z pointing the
way its pipe goes (into the wall, or down through the floor). And the free zone in front of each (its use
needs it), kept with it and drawn dashed in the plans.

Their frame: the middle of the back at the floor; X along the wall, Y out into the room, Z up."""

import math

import numpy as np

import ifcopenshell.api as api
import ifcopenshell.api.system  # noqa: F401

BACK = (0.0, -1.0, 0.0)             # (a port's way: into the wall behind)
DOWN = (0.0, 0.0, -1.0)             # (…down through the floor)
# kind -> (PredefinedType, (width along the wall, depth, height),
#          parts: [("box", (cx, cy), (sx, sy), z0, height) | ("ellipse", (cx, cy), (a, b), z0, height)],
#          ports: [(name, (x, y, z), way, SystemType)], free zone in front (width, depth))
FIXTURES = {
    "wc": ("TOILETPAN", (0.38, 0.70, 0.80),
           [("ellipse", (0.0, 0.43), (0.18, 0.25), 0.0, 0.40), ("box", (0.0, 0.09), (0.38, 0.18), 0.35, 0.45)],
           [("drain", (0.0, 0.0, 0.18), BACK, "SEWAGE"), ("cold", (0.12, 0.0, 0.65), BACK, "DOMESTICCOLDWATER")],
           (0.80, 0.70)),
    "basin": ("WASHHANDBASIN", (0.60, 0.45, 0.85),
              [("box", (0.0, 0.225), (0.60, 0.45), 0.67, 0.18)],
              [("drain", (0.0, 0.0, 0.55), BACK, "WASTEWATER"), ("cold", (-0.10, 0.0, 0.55), BACK, "DOMESTICCOLDWATER"),
               ("hot", (0.10, 0.0, 0.55), BACK, "DOMESTICHOTWATER")],
              (0.80, 0.70)),
    "bidet": ("BIDET", (0.38, 0.55, 0.40),
              [("ellipse", (0.0, 0.30), (0.18, 0.25), 0.0, 0.40)],
              [("drain", (0.0, 0.0, 0.18), BACK, "WASTEWATER"), ("cold", (-0.08, 0.0, 0.30), BACK, "DOMESTICCOLDWATER"),
               ("hot", (0.08, 0.0, 0.30), BACK, "DOMESTICHOTWATER")],
              (0.80, 0.70)),
    "shower": ("SHOWER", (0.80, 0.80, 0.05),
               [("box", (0.0, 0.40), (0.80, 0.80), 0.0, 0.05)],
               [("drain", (0.0, 0.40, 0.0), DOWN, "WASTEWATER"), ("cold", (-0.08, 0.0, 1.10), BACK, "DOMESTICCOLDWATER"),
                ("hot", (0.08, 0.0, 1.10), BACK, "DOMESTICHOTWATER")],
               (0.80, 0.70)),
    "bath": ("BATH", (1.70, 0.75, 0.55),
             [("box", (0.0, 0.375), (1.70, 0.75), 0.0, 0.55)],
             [("drain", (-0.70, 0.375, 0.0), DOWN, "WASTEWATER"),
              ("cold", (-0.70, 0.0, 0.65), BACK, "DOMESTICCOLDWATER"),
              ("hot", (-0.55, 0.0, 0.65), BACK, "DOMESTICHOTWATER")],
             (1.70, 0.70)),
    "kitchen_sink": ("SINK", (0.80, 0.60, 0.90),
                     [("box", (0.0, 0.30), (0.80, 0.50), 0.70, 0.20)],
                     [("drain", (0.0, 0.0, 0.50), BACK, "WASTEWATER"),
                      ("cold", (-0.10, 0.0, 0.55), BACK, "DOMESTICCOLDWATER"),
                      ("hot", (0.10, 0.0, 0.55), BACK, "DOMESTICHOTWATER")],
                     (0.80, 0.90)),
}


def fixture_frame(back, angle):
    """The placement of a fixture: the middle of its back at `back` (3,), its X along `angle` degrees (Y, out
    into the room, to its left)."""
    a = math.radians(float(angle))
    x = np.array((math.cos(a), math.sin(a), 0.0))
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, np.cross((0.0, 0.0, 1.0), x), (0.0, 0.0, 1.0), back
    return m


def outline(back, angle, kind):
    """Its outline at the floor (plan, 3D): the four corners of its width × depth."""
    w, d, _h = FIXTURES[kind][1]
    m = fixture_frame(np.asarray(back, dtype=float), angle)
    return [m[:3, 3] + m[:3, 0] * x + m[:3, 1] * y for x, y in ((-w / 2, 0.0), (w / 2, 0.0), (w / 2, d), (-w / 2, d))]


def free_zone(back, angle, kind):
    """The free zone in front of it (plan, 3D at its floor): the four corners, or [] if it has none."""
    _p, (_w, d, _h), _parts, _ports, zone = FIXTURES[kind]
    if not zone:
        return []
    zw, zd = zone
    m = fixture_frame(np.asarray(back, dtype=float), angle)
    return [m[:3, 3] + m[:3, 0] * x + m[:3, 1] * y for x, y in ((-zw / 2, d), (zw / 2, d), (zw / 2, d + zd),
                                                               (-zw / 2, d + zd))]


class SanitaryMixin:
    def add_fixture(self, back, angle, kind, name, storey=None):
        """A sanitary fixture of this kind, the middle of its back at `back` (3,: at its floor), its X along `angle`
        degrees: its solid and its ports (drain, cold, hot). Returns it."""
        f, u = self.file, 1.0 / self.unit_scale
        predefined, _size, parts, ports, _zone = FIXTURES[kind]
        fixture = api.root.create_entity(f, ifc_class="IfcSanitaryTerminal", name=name, predefined_type=predefined)
        m = fixture_frame(np.asarray(back, dtype=float), angle)
        self._place(fixture, m)
        items = []
        for shape, (cx, cy), size, z0, height in parts:
            centre = f.createIfcAxis2Placement2D(f.createIfcCartesianPoint((float(cx * u), float(cy * u))), None)
            if shape == "ellipse":
                profile = f.createIfcEllipseProfileDef("AREA", None, centre, float(size[0] * u), float(size[1] * u))
            else:
                profile = f.createIfcRectangleProfileDef("AREA", None, centre, float(size[0] * u), float(size[1] * u))
            items.append(f.createIfcExtrudedAreaSolid(
                profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, float(z0 * u))), None, None),
                f.createIfcDirection((0.0, 0.0, 1.0)), float(height * u)))
        api.geometry.assign_representation(f, product=fixture, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))
        container = self.storey(storey) if storey is not None else self.storey_at(float(back[2]))
        api.spatial.assign_container(f, products=[fixture], relating_structure=container)
        self._mark(fixture, "fixture")
        self._set_params(fixture, {"Louca": kind, "Angulo": float(angle)})
        for port_name, at, way, system in ports:
            port = api.system.add_port(f, element=fixture)
            port.Name, port.PredefinedType, port.SystemType = port_name, "PIPE", system
            port.FlowDirection = "SOURCE" if port_name == "drain" else "SINK"
            p = m[:3, 3] + m[:3, :3] @ np.asarray(at, dtype=float)
            w = m[:3, :3] @ np.asarray(way, dtype=float)
            self._place(port, self._port_frame(p, w, m[:3, 0] if abs(w[2]) > 0.7 else None))
        return fixture

    def fixture_params(self, guid):
        """{kind, the middle of its back (3,), its angle (degrees)} of a fixture made by this program."""
        e = self.by_guid(guid)
        p = self._params(e)
        m = self._placement_si(e)
        return {"kind": p.get("Louca") or "wc", "back": m[:3, 3].copy(), "angle": float(p.get("Angulo") or 0.0)}

    def free_zones(self, guids):
        """{GlobalId: the free zone in front of it (4 corners, plan 3D)} of the fixtures among `guids` (0.140)."""
        out = {}
        for g in guids:
            if self.kind_of(g) != "fixture":
                continue
            fp = self.fixture_params(g)
            zone = free_zone(fp["back"], fp["angle"], fp["kind"]) if fp["kind"] in FIXTURES else []
            if zone:
                out[g] = zone
        return out
