"""Architecture pieces of the addon's inventory (0.374), mixed into IfcModel:

- a gutter (the study's «Calha»): an IfcPipeSegment GUTTER (IFC2X3: IfcFlowSegment) along a roof's eave, outside it,
  its top at the eave's level — a U section swept along it, aluminium;
- an elevator (the study's «Elevador»): an IfcTransportElement ELEVATOR — its shaft (a ring of walls 15 cm thick, open
  at the front for the landing doors) from a storey up to the top one, and its car at the bottom;
- a room separator (the study's «Separador»): an IfcVirtualElement, a line on a storey's floor that bounds rooms where
  there is no wall (Revit's Room Separation): it counts in storey_obstacles as a hairline.

ArqSynth_Parametros keep what made them: Elemento "gutter" / "elevator" / "separator", the points, the sizes."""

import numpy as np

import ifcopenshell.api
import ifcopenshell.api.geometry
import ifcopenshell.api.material
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.spatial

api = ifcopenshell.api
GUTTER = (0.15, 0.10, 0.006)        # m: a gutter's width (out from the eave), depth, sheet
GUTTER_DROP = 0.02                  # m: (0.384) its top under the eave's upper edge — the water falls in
GUTTER_JOIN = 0.03                  # m: (0.384) two gutters' ends this near (in plan) meet at a corner
SHAFT_WALL = 0.15                   # m: an elevator shaft's walls
CAR_HEIGHT = 2.20                   # m
SEPARATOR = 0.005                   # m: how thick a room separator counts in the rooms' outlines


def _axes(x, y, z):
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2] = x, y, z
    return m


def _xy_text(v):
    """A plan way as kept in the parameters ("x,y"; "" for none)."""
    return "" if v is None else "{:.6f},{:.6f}".format(float(v[0]), float(v[1]))


def _xy_of(text):
    """The plan way kept as "x,y" (None for none)."""
    try:
        x, y = (float(c) for c in str(text or "").split(","))
    except ValueError:
        return None
    return np.array((x, y, 0.0))


class ArchitectureMixin:
    # ------------------------------------------------------------ helpers

    def _profile_solid(self, ring, depth, axis=(0.0, 0.0, 1.0), ref=(1.0, 0.0, 0.0), holes=(), at=(0.0, 0.0, 0.0)):
        """An extruded solid of the polygon `ring` [(x, y)] (m) `depth` along `axis` (the profile's x along `ref`),
        (0.384) from `at` (m, the element's own coordinates)."""
        f, u = self.file, 1.0 / self.unit_scale
        outer = self._ring_curve(list(ring))
        if holes:
            profile = f.createIfcArbitraryProfileDefWithVoids("AREA", None, outer, [self._ring_curve(list(h))
                                                                                   for h in holes])
        else:
            profile = f.createIfcArbitraryClosedProfileDef("AREA", None, outer)
        return f.createIfcExtrudedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint(tuple(float(c) * u for c in at)),
                                                 f.createIfcDirection(tuple(float(c) for c in axis)),
                                                 f.createIfcDirection(tuple(float(c) for c in ref))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(depth * u))

    def _body(self, product, items, kind="SweptSolid"):
        f = self.file
        api.geometry.assign_representation(f, product=product, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, kind, list(items)))

    def _contain(self, product, storey, z):
        container = self.storey(storey) if storey is not None else self.storey_at(float(z))
        api.spatial.assign_container(self.file, products=[product], relating_structure=container)

    # ------------------------------------------------------------ gutter

    @staticmethod
    def _gutter_frame(a, b, outward):
        """(x along it, out, its start, its length, run the other way) — its frame's up must be up."""
        x = (b - a) * np.array((1.0, 1.0, 0.0))
        length = float(np.linalg.norm(x))
        x /= length
        out = np.asarray(outward, dtype=float).copy()
        out[2] = 0.0
        out = out - float(out @ x) * x
        out /= np.linalg.norm(out)
        if float(np.cross(x, out)[2]) < 0:
            return -x, out, b, length, True
        return x, out, a, length, False

    def _gutter_items(self, a, b, outward, cut_a=None, cut_b=None):
        """(its placement, its body's items, the body's kind): a U section swept from a to b, its top GUTTER_DROP under
        the eave line, outside it; (0.384) an end meeting another gutter at a corner (cut_a / cut_b: that gutter's
        outward way) carried on to the corner's outer point and mitred there, as the two halves of one gutter."""
        f, u = self.file, 1.0 / self.unit_scale
        x, out, start, length, flipped = self._gutter_frame(a, b, outward)
        w, h, s = GUTTER
        ring = [(0.0, -h), (w, -h), (w, 0.0), (w - s, 0.0), (w - s, -h + s), (s, -h + s), (s, 0.0), (0.0, 0.0)]
        cuts = (cut_b, cut_a) if flipped else (cut_a, cut_b)    # (at its own start, at its own end)
        reach, planes = [0.0, 0.0], []
        for k, cut in enumerate(cuts):
            if cut is None:
                continue
            other = np.asarray(cut, dtype=float).copy()
            other[2] = 0.0
            if np.linalg.norm(other) < 1e-9:
                continue
            other /= np.linalg.norm(other)
            cos = float(out @ other)
            if cos > 0.999:                                     # (the same way: in line, nothing to mitre)
                continue
            corner = (out + other) * w / max(1.0 + cos, 0.1)    # (the outer corner, from the eave's corner)
            along = float(corner @ x)
            if k == 0:
                reach[0] = max(0.0, -along)
                normal, origin = np.array((w, -along, 0.0)), (0.0, 0.0, 0.0)
            else:
                reach[1] = max(0.0, along)
                normal, origin = np.array((-w, along, 0.0)), (length, 0.0, 0.0)
            normal /= np.linalg.norm(normal)                    # (towards what is kept)
            planes.append(f.createIfcHalfSpaceSolid(f.createIfcPlane(f.createIfcAxis2Placement3D(
                f.createIfcCartesianPoint(tuple(float(c) * u for c in origin)),
                f.createIfcDirection(tuple(float(c) for c in normal)),
                f.createIfcDirection((0.0, 0.0, 1.0)))), True))        # (axis and ref. both: the IFC's rule)
        solid = self._profile_solid(ring, length + reach[0] + reach[1] + (0.01 if planes else 0.0),
                                    axis=(1.0, 0.0, 0.0), ref=(0.0, 1.0, 0.0),
                                    at=(-reach[0] - (0.005 if planes else 0.0), 0.0, 0.0))
        for plane in planes:                                    # (the part past each mitre taken away)
            solid = f.createIfcBooleanClippingResult("DIFFERENCE", solid, plane)
        m = _axes(x, out, np.cross(x, out))
        m[:3, 3] = np.asarray(start, dtype=float) - np.array((0.0, 0.0, GUTTER_DROP))
        return m, [solid], ("Clipping" if planes else "SweptSolid")

    def add_gutter(self, a, b, outward, name, storey=None, lang="pt", cut_a=None, cut_b=None):
        """A gutter from a to b (world, the eave's line — (0.384) its upper edge), hanging outside it towards `outward`
        (horizontal); cut_a / cut_b: the outward way of a gutter its end meets at a corner (mitred to it)."""
        f = self.file
        a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        ifc_class = "IfcFlowSegment" if f.schema == "IFC2X3" else "IfcPipeSegment"
        gutter = api.root.create_entity(f, ifc_class=ifc_class, name=name,
                                        **({} if ifc_class == "IfcFlowSegment" else {"predefined_type": "GUTTER"}))
        m, items, kind = self._gutter_items(a, b, outward, cut_a, cut_b)
        self._place(gutter, m)
        self._body(gutter, items, kind)
        self._contain(gutter, storey, a[2])
        api.material.assign_material(f, products=[gutter], type="IfcMaterial", material=self._material("aluminio",
                                                                                                          lang))
        self._mark(gutter, "gutter")
        w, h, _s = GUTTER
        self._set_params(gutter, {"Inicio": "{:.6f},{:.6f},{:.6f}".format(*a),
                                  "Fim": "{:.6f},{:.6f},{:.6f}".format(*b), "Largura": w, "Altura": h,
                                  "Fora": _xy_text(outward), "CorteInicio": _xy_text(cut_a),
                                  "CorteFim": _xy_text(cut_b)})
        return gutter

    def gutter_lines(self):
        """(0.384) The gutters: [(GlobalId, a, b, outward, cut_a, cut_b)] — their eave lines (world) and ways."""
        found = []
        for e in self.file.by_type("IfcFlowSegment"):
            if self.kind_of(e.GlobalId) != "gutter":
                continue
            p = self._params(e)
            try:
                a, b = (np.array([float(v) for v in str(p[k]).split(",")]) for k in ("Inicio", "Fim"))
            except (KeyError, ValueError):
                continue
            out = _xy_of(p.get("Fora"))
            if out is None:                                     # (before 0.384: its placement's y)
                y = self.placement(e.GlobalId)[:3, 1]
                out = np.array((y[0], y[1], 0.0))
            found.append((e.GlobalId, a, b, out, _xy_of(p.get("CorteInicio")), _xy_of(p.get("CorteFim"))))
        return found

    def set_gutter_cuts(self, guid, cut_a=None, cut_b=None):
        """(0.384) A gutter's ends mitred to the gutters they meet (None: a plain end) — its body made again."""
        line = next((g for g in self.gutter_lines() if g[0] == guid), None)
        if line is None:
            return
        gutter = self.by_guid(guid)
        _g, a, b, out, _ca, _cb = line
        _m, items, kind = self._gutter_items(a, b, out, cut_a, cut_b)
        for rep in list(gutter.Representation.Representations if gutter.Representation else ()):
            api.geometry.unassign_representation(self.file, product=gutter, representation=rep)
            api.geometry.remove_representation(self.file, representation=rep)
        self._body(gutter, items, kind)
        self._set_params(gutter, {"CorteInicio": _xy_text(cut_a), "CorteFim": _xy_text(cut_b)})

    # ------------------------------------------------------------ elevator

    def add_elevator(self, corner, width, depth, angle, z0, z1, name, storey=None, lang="pt"):
        """An elevator: its shaft `width` × `depth` (inside) from its corner (plan, the front left one seen from the
        landing) turned `angle` degrees, from z0 up to z1, its front open; the car at z0."""
        f = self.file
        c, s_ = np.cos(np.radians(angle)), np.sin(np.radians(angle))
        x, y, z = np.array((c, s_, 0.0)), np.array((-s_, c, 0.0)), np.array((0.0, 0.0, 1.0))
        m = _axes(x, y, z)
        m[:3, 3] = (float(corner[0]), float(corner[1]), float(z0))
        t = SHAFT_WALL
        w, d = float(width), float(depth)
        # the shaft: a U of walls (left, back, right), the front open; the car inside, a gap of 5 cm round it
        u_ring = [(-t, 0.0), (0.0, 0.0), (0.0, d), (w, d), (w, 0.0), (w + t, 0.0), (w + t, d + t), (-t, d + t)]
        car = [(0.05, 0.05), (w - 0.05, 0.05), (w - 0.05, d - 0.05), (0.05, d - 0.05)]
        items = [self._profile_solid(u_ring, float(z1 - z0)), self._profile_solid(car, CAR_HEIGHT)]
        ifc_class = "IfcTransportElement"
        lift = api.root.create_entity(f, ifc_class=ifc_class, name=name, predefined_type="ELEVATOR")
        self._place(lift, m)
        self._body(lift, items)
        self._contain(lift, storey, z0)
        api.material.assign_material(f, products=[lift], type="IfcMaterial", material=self._material("concreto",
                                                                                                        lang))
        self._mark(lift, "elevator")
        self._set_params(lift, {"Largura": w, "Profundidade": d, "Angulo": float(angle),
                                "Altura": float(z1 - z0)})
        common = api.pset.add_pset(f, product=lift, name="Pset_TransportElementCommon")
        api.pset.edit_pset(f, pset=common, properties={"CapacityPeople": 8})
        return lift

    # ------------------------------------------------------------ room separators

    def add_separator(self, a, b, name, storey):
        """A room separation line from a to b (plan, on the storey's floor)."""
        f = self.file
        z = self._elevation(self.storey(storey))
        a, b = np.asarray(a, dtype=float)[:2], np.asarray(b, dtype=float)[:2]
        sep = api.root.create_entity(f, ifc_class="IfcVirtualElement", name=name)
        m = np.eye(4)
        m[2, 3] = z
        self._place(sep, m)
        d = b - a
        n = np.array((-d[1], d[0])) / max(float(np.linalg.norm(d)), 1e-9) * 0.005
        ring = [tuple(a - n), tuple(b - n), tuple(b + n), tuple(a + n)]      # (a hairline 1 cm wide, seen and picked)
        self._body(sep, [self._profile_solid(ring, 0.02)])
        self._contain(sep, storey, z)
        self._mark(sep, "separator")
        self._set_params(sep, {"Inicio": "{:.6f},{:.6f}".format(*a), "Fim": "{:.6f},{:.6f}".format(*b)})
        return sep

    def separators(self, storey):
        """The room separators of a storey: [(a (2,), b (2,))]."""
        out = []
        st = self.storey(storey)
        for rel in st.ContainsElements or ():
            for e in rel.RelatedElements:
                if e.is_a("IfcVirtualElement") and self.kind_of(e.GlobalId) == "separator":
                    p = self._params(e)
                    try:
                        a = np.array([float(v) for v in str(p.get("Inicio")).split(",")])
                        b = np.array([float(v) for v in str(p.get("Fim")).split(",")])
                    except ValueError:
                        continue
                    out.append((a, b))
        return out

    def separator_obstacles(self, storey):
        """The room separators as hairline polygons, for the rooms' outlines."""
        out = []
        for a, b in self.separators(storey):
            d = b - a
            n = np.linalg.norm(d)
            if n < 1e-6:
                continue
            e = d / n * SEPARATOR
            p = np.array((-d[1], d[0])) / n * SEPARATOR
            out.append([tuple(a - e - p), tuple(b + e - p), tuple(b + e + p), tuple(a - e + p)])
        return out
