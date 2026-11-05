"""Electrical points (0.143, Phase 6, step 4): outlets, switches, a data outlet, the distribution board and junction
boxes (IfcOutlet, IfcSwitchingDevice, IfcElectricDistributionBoard, IfcJunctionBox) made by the program, their back
against a wall at their usual height, each with its port (IfcDistributionPort CABLE) at its back where its cable
comes, and its symbol on a plan (sized on paper, as drawn by hand: the boxes themselves are a few centimetres).

Their frame, as the fixtures': the middle of the back at the floor; X along the wall, Y out into the room, Z up."""

import math

import numpy as np

import ifcopenshell.api as api
import ifcopenshell.api.system  # noqa: F401

from .sanitary import fixture_frame

# kind -> (IFC class, PredefinedType, (width, depth, height) m, its middle's height over the floor, SystemType)
POINTS = {
    "outlet": ("IfcOutlet", "POWEROUTLET", (0.08, 0.045, 0.08), 0.30, "ELECTRICAL"),
    "outlet_double": ("IfcOutlet", "POWEROUTLET", (0.15, 0.045, 0.08), 0.30, "ELECTRICAL"),
    "outlet_counter": ("IfcOutlet", "POWEROUTLET", (0.08, 0.045, 0.08), 1.10, "ELECTRICAL"),
    "data_outlet": ("IfcOutlet", "DATAOUTLET", (0.08, 0.045, 0.08), 0.30, "DATA"),
    "switch": ("IfcSwitchingDevice", "TOGGLESWITCH", (0.08, 0.04, 0.08), 1.10, "LIGHTING"),
    "switch_two_way": ("IfcSwitchingDevice", "TOGGLESWITCH", (0.08, 0.04, 0.08), 1.10, "LIGHTING"),
    "board": ("IfcElectricDistributionBoard", "DISTRIBUTIONBOARD", (0.40, 0.12, 0.50), 1.50, "ELECTRICAL"),
    "junction_box": ("IfcJunctionBox", "POWER", (0.10, 0.05, 0.10), 2.30, "ELECTRICAL"),
}
SYMBOL = 2.0                # mm on paper: a point's symbol's size (its radius)


def point_symbol(kind, back, angle, mm):
    """(0.143) A point's plan symbol, in front of the wall where it is: ([(a, b) lines (2,)], [filled polygons]) —
    mm: metres in the model per mm on paper. An outlet: a half circle against the wall, a stroke out (two for a
    double, a bar for one over the counter); a data outlet: a triangle; a switch: a small circle and a slanted
    stroke (two strokes: two-way); the board: a filled rectangle; a junction box: a square with a cross."""
    m = fixture_frame(np.asarray(back, dtype=float), angle)
    o, x, y = m[:2, 3], m[:2, 0], m[:2, 1]
    r = SYMBOL * mm
    p = lambda u, v: o + x * u + y * v           # noqa: E731  (u along the wall, v out of it)
    lines, solids = [], []
    if kind.startswith("outlet"):
        arc = [p(r * math.cos(a), r * math.sin(a)) for a in np.linspace(0.0, math.pi, 13)]
        lines += list(zip(arc, arc[1:])) + [(p(-r, 0.0), p(r, 0.0))]
        strokes = (-0.35, 0.35) if kind == "outlet_double" else (0.0,)
        lines += [(p(r * s, r * math.sqrt(1 - s * s)), p(r * s * 1.6, r * 1.9)) for s in strokes]
        if kind == "outlet_counter":
            lines.append((p(-r * 0.7, r * 1.9), p(r * 0.7, r * 1.9)))
    elif kind == "data_outlet":
        tri = [p(-r, 0.0), p(r, 0.0), p(0.0, r * 1.6)]
        lines += list(zip(tri, tri[1:] + tri[:1]))
    elif kind.startswith("switch"):
        c, k = p(0.0, r * 0.6), r * 0.45
        ring = [c + (x * math.cos(a) + y * math.sin(a)) * k for a in np.linspace(0.0, 2 * math.pi, 17)]
        lines += list(zip(ring, ring[1:]))
        tip = c + (x * 0.6 + y * 0.8) * r * 2.0
        lines.append((c + (x * 0.6 + y * 0.8) * k, tip))
        lines.append((tip, tip + x * r * 0.5))
        if kind == "switch_two_way":
            other = c + (-x * 0.6 + y * 0.8) * r * 2.0
            lines += [(c + (-x * 0.6 + y * 0.8) * k, other), (other, other - x * r * 0.5)]
    elif kind == "board":
        w = POINTS["board"][2][0] / 2
        solids.append([p(-w, 0.0), p(w, 0.0), p(w, r), p(-w, r)])
    elif kind == "junction_box":
        q = [p(-r * 0.6, 0.0), p(r * 0.6, 0.0), p(r * 0.6, r * 1.2), p(-r * 0.6, r * 1.2)]
        lines += list(zip(q, q[1:] + q[:1])) + [(q[0], q[2]), (q[1], q[3])]
    return lines, solids


class ElectricalMixin:
    def add_point(self, back, angle, kind, name, storey=None, height=None):
        """An electrical point of this kind, the middle of its back at `back` (3,: at its floor), its X along
        `angle` degrees, its middle `height` over the floor (None: its usual): its box and its port. Returns it."""
        f, u = self.file, 1.0 / self.unit_scale
        cls, predefined, (w, d, h), usual, system = POINTS[kind]
        height = usual if height is None else float(height)
        point = api.root.create_entity(f, ifc_class=cls, name=name, predefined_type=predefined)
        m = fixture_frame(np.asarray(back, dtype=float), angle)
        self._place(point, m)
        centre = f.createIfcAxis2Placement2D(f.createIfcCartesianPoint((0.0, float(d / 2 * u))), None)
        box = f.createIfcExtrudedAreaSolid(
            f.createIfcRectangleProfileDef("AREA", None, centre, float(w * u), float(d * u)),
            f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, float((height - h / 2) * u))), None, None),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(h * u))
        api.geometry.assign_representation(f, product=point, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", [box]))
        container = self.storey(storey) if storey is not None else self.storey_at(float(back[2]))
        api.spatial.assign_container(f, products=[point], relating_structure=container)
        self._mark(point, "electrical")
        self._set_params(point, {"Ponto": kind, "Angulo": float(angle), "Altura": height})
        port = api.system.add_port(f, element=point)
        port.Name, port.PredefinedType, port.SystemType = "cable", "CABLE", system
        port.FlowDirection = "SOURCE" if kind == "board" else "SINK"
        at = m[:3, 3] + m[:3, 2] * height
        self._place(port, self._port_frame(at, -m[:3, 1], None))
        return point

    def point_params(self, guid):
        """{kind, the middle of its back (3,: at the floor), its angle (degrees), its height} of an electrical point."""
        e = self.by_guid(guid)
        p = self._params(e)
        m = self._placement_si(e)
        kind = p.get("Ponto") or "outlet"
        return {"kind": kind, "back": m[:3, 3].copy(), "angle": float(p.get("Angulo") or 0.0),
                "height": float(p.get("Altura") or POINTS.get(kind, POINTS["outlet"])[3])}

    def tagged(self, tag, storey=None, classes=("IfcOutlet", "IfcSwitchingDevice", "IfcLightFixture", "IfcJunctionBox")):
        """(0.145) The GlobalIds of the elements of these classes (the points and lights; 0.148: the pipes too)
        proposed with this tag (on a storey, or all)."""
        out = []
        for cls in classes:
            for e in self.file.by_type(cls):
                if self._params(e).get("Proposta") == tag and (storey is None or self.storey_of(e.GlobalId) == storey):
                    out.append(e.GlobalId)
        return out

    def point_symbols(self, guids):
        """{GlobalId: (kind, back (3,), angle)} of the electrical points among `guids` — their plan symbols."""
        out = {}
        for g in guids:
            if self.kind_of(g) == "electrical":
                pp = self.point_params(g)
                out[g] = (pp["kind"], pp["back"], pp["angle"])
        return out
