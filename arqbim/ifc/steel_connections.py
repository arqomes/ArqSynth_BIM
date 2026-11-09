"""(0.497) Steel connections, mixed into IfcModel — as DetailCraft's (each kept only as its kind, the pieces it joins
and its parameters; its plates, bolts and welds made again from them whenever those pieces change) and Tekla's
components. The first: the column's base plate — a plate under the column's foot, its anchor bolts (washer, nut, the
rod down into the concrete), the column welded all round to it.

In the IFC: an IfcElementAssembly (USERDEFINED «Ligação») aggregating its parts — IfcPlate (its holes in its outline),
IfcMechanicalFastener ANCHORBOLT / BOLT (rod, washer and nut, round and hexagonal extrusions), IfcFastener WELD
(Pset_FastenerWeld: its throat «a», its length «l») — all of the column's grade. ArqSynth_Parametros of the assembly:
Elemento "steel_connection", Ligacao (its kind), Pecas (the GlobalIds it joins, JSON), Parametros (JSON, mm); of each
part: Elemento "steel_part", Ligacao (the assembly's GlobalId).

Checks as EN 1993-1-8 Table 3.3 for the bolts (e ≥ 1,2 d0, p ≥ 2,2 d0), and that the plate is bigger than the column
and its bolts clear of it — warnings only (no strength design: that is the EC3's, later)."""

import json
import math

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from .edit import EditRefused

api = ifcopenshell.api
KINDS = ("base_plate",)
NAMES = {"base_plate": ("Chapa de base", "Base plate")}
# (mm) A × B its plate (0: the column's size + 2 × MARGIN), tp its thickness, n its anchor bolts (2, 4, 6, 8), d their
# diameter, e their distance to the plate's edges, proj how far they stand over the plate, embed how deep in the
# concrete, grout under the plate, a the weld's throat
DEFAULTS = {"base_plate": {"A": 0.0, "B": 0.0, "tp": 20.0, "n": 4, "d": 20.0, "e": 50.0, "proj": 80.0, "embed": 400.0,
                           "grout": 30.0, "a": 6.0}}
LIMITS = {"A": (100.0, 3000.0), "B": (100.0, 3000.0), "tp": (5.0, 100.0), "n": (2, 8), "d": (12.0, 48.0),
          "e": (20.0, 300.0), "proj": (20.0, 300.0), "embed": (100.0, 2000.0), "grout": (0.0, 100.0), "a": (3.0, 20.0)}
MARGIN = 100.0                # mm round the column, its plate's default
BOLT_SIZES = (12.0, 16.0, 20.0, 24.0, 27.0, 30.0, 36.0, 42.0, 48.0)


def hole(d):
    """A bolt's hole (mm): d + 2 up to M24, d + 3 above (EN 1090-2, normal clearance)."""
    return d + (2.0 if d <= 24.0 else 3.0)


def bolt_spots(n, sx, sy):
    """Where n bolts go on a plate (mm, from its middle): its corners, and the middles of its long sides (6) or of
    all of them (8); 2: on its long axis."""
    corners = [(sx / 2 * i, sy / 2 * j) for i in (-1, 1) for j in (-1, 1)]
    if n <= 2:
        return [(0.0, -sy / 2), (0.0, sy / 2)] if sy >= sx else [(-sx / 2, 0.0), (sx / 2, 0.0)]
    if n <= 4:
        return corners
    middles = [(0.0, -sy / 2), (0.0, sy / 2)] if sx >= sy else [(-sx / 2, 0.0), (sx / 2, 0.0)]
    if n <= 6:
        return corners + middles
    return corners + [(0.0, -sy / 2), (0.0, sy / 2), (-sx / 2, 0.0), (sx / 2, 0.0)]


def clean(kind, params):
    """A connection's parameters as they may be kept: its kind's defaults, each in its range."""
    out = dict(DEFAULTS[kind])
    for k, v in (params or {}).items():
        if k not in out:
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        lo, hi = LIMITS[k]
        if k in ("A", "B") and v == 0.0:
            out[k] = 0.0
            continue
        v = min(max(v, lo), hi)
        out[k] = int(round(v)) if k == "n" else round(v, 1)
    return out


def base_plate_layout(params, b, h):
    """The base plate of a column of section b × h (mm): its size, its bolts' spots — (A, B, spots, warnings)."""
    A = params["A"] or math.ceil((b + 2 * MARGIN) / 10.0) * 10.0
    B = params["B"] or math.ceil((h + 2 * MARGIN) / 10.0) * 10.0
    e, d = params["e"], params["d"]
    sx, sy = A - 2 * e, B - 2 * e
    spots = bolt_spots(int(params["n"]), sx, sy)
    d0 = hole(d)
    warnings = []
    if e < 1.2 * d0:
        warnings.append(("edge", round(1.2 * d0, 1)))
    gaps = [math.dist(p, q) for i, p in enumerate(spots) for q in spots[i + 1:]]
    if gaps and min(gaps) < 2.2 * d0:
        warnings.append(("pitch", round(2.2 * d0, 1)))
    if A <= b or B <= h:
        warnings.append(("small", 0.0))
    if any(abs(x) < b / 2 + d and abs(y) < h / 2 + d for x, y in spots):
        warnings.append(("clash", 0.0))
    return A, B, spots, warnings


class SteelConnectionMixin:
    # ------------------------------------------------------------ what there is

    def connection_of(self, part_guid):
        """The connection (IfcElementAssembly) a part belongs to — or the connection itself —, or None."""
        e = self.by_guid(part_guid)
        if e is None:
            return None
        if self.kind_of(part_guid) == "steel_connection":
            return e
        found = self._params(e).get("Ligacao") if self.kind_of(part_guid) == "steel_part" else None
        return self.by_guid(found) if found else None

    def connection_params(self, guid):
        """(kind, the GlobalIds it joins, its parameters) of a connection (or of one of its parts)."""
        assembly = self.connection_of(guid)
        if assembly is None:
            return None
        p = self._params(assembly)
        kind = p.get("Ligacao") if p.get("Ligacao") in KINDS else "base_plate"
        try:
            members = json.loads(p.get("Pecas") or "[]")
            params = json.loads(p.get("Parametros") or "{}")
        except ValueError:
            members, params = [], {}
        return kind, members, clean(kind, params)

    def connections_on(self, guids):
        """The connections that join any of these elements (their assemblies)."""
        wanted = set(guids)
        out = []
        for a in self.file.by_type("IfcElementAssembly"):
            if self.kind_of(a.GlobalId) != "steel_connection":
                continue
            try:
                members = json.loads(self._params(a).get("Pecas") or "[]")
            except ValueError:
                continue
            if wanted & set(members):
                out.append(a)
        return out

    def connection_parts(self, assembly):
        return [p for rel in assembly.IsDecomposedBy or () for p in rel.RelatedObjects]

    # ------------------------------------------------------------ made, changed, removed

    def add_connection(self, kind, members, params=None, lang="pt"):
        """A connection of `kind` joining `members` (GlobalIds: a base plate, its column), with `params` (mm; missing:
        its defaults). Returns the assembly."""
        if kind not in KINDS:
            raise EditRefused("connection_kind")
        if kind == "base_plate" and self.steel_section(members[0]) is None:
            raise EditRefused("connection_not_steel")
        f = self.file
        label = NAMES[kind][0 if lang == "pt" else 1]
        column = self.by_guid(members[0])
        assembly = api.root.create_entity(f, ifc_class="IfcElementAssembly", predefined_type="USERDEFINED",
                                          name="{} — {}".format(label, column.Name or ""))
        assembly.ObjectType = "Ligação"
        storey = self.storey_of(members[0])
        if storey:
            api.spatial.assign_container(f, products=[assembly], relating_structure=self.storey(storey))
        self._mark(assembly, "steel_connection")
        self._set_params(assembly, {"Ligacao": kind, "Pecas": json.dumps(list(members)),
                                    "Parametros": json.dumps(clean(kind, params))})
        self._build_connection(assembly, lang)
        return assembly

    def set_connection(self, guid, lang="pt", **values):
        """A connection's parameters changed (any of them; the others kept): made again. Returns the assembly."""
        found = self.connection_params(guid)
        if found is None:
            raise EditRefused("connection_none")
        kind, members, params = found
        params.update(values)
        assembly = self.connection_of(guid)
        self._set_params(assembly, {"Parametros": json.dumps(clean(kind, params))})
        self._build_connection(assembly, lang)
        return assembly

    def remove_connection(self, guid):
        """A connection and all its parts taken away."""
        assembly = self.connection_of(guid)
        if assembly is None:
            return False
        for part in self.connection_parts(assembly):
            api.root.remove_product(self.file, product=part)
        api.root.remove_product(self.file, product=assembly)
        return True

    def connections_to_remove(self, guids):
        """What goes with elements being deleted: the whole connection of a part of one, and the connections of a
        piece they joined — their assemblies' and parts' GlobalIds."""
        out = []
        for g in guids:
            kind = self.kind_of(g)
            if kind in ("steel_part", "steel_connection"):
                assembly = self.connection_of(g)
                found = [assembly] if assembly is not None else []
            else:
                found = self.connections_on([g])
            for a in found:
                for x in [a] + self.connection_parts(a):
                    if x.GlobalId not in out and x.GlobalId not in guids:
                        out.append(x.GlobalId)
        return out

    def follow_connections(self, changed):
        """The connections on the pieces changed made again (their column moved, given another section…); a
        connection whose piece is gone, removed. Returns the parts made."""
        out = []
        made = set(getattr(self, "made", None) or ())
        for assembly in self.connections_on(changed):
            if assembly.GlobalId in made:
                continue
            _kind, members, _params = self.connection_params(assembly.GlobalId)
            if any(self.by_guid(m) is None for m in members):
                self.remove_connection(assembly.GlobalId)
                continue
            self._build_connection(assembly)
            out += [p.GlobalId for p in self.connection_parts(assembly)]
        return out

    def connection_warnings(self, guid):
        """What its checks find: [(code, value)] (value: the least it should be, mm)."""
        found = self.connection_params(guid)
        if found is None:
            return []
        kind, members, params = found
        from ..core import steel
        sec = steel.get(self.steel_section(members[0]) or "")
        if sec is None:
            return []
        b, h = steel.size(sec)
        return base_plate_layout(params, b, h)[3]

    # ------------------------------------------------------------ its parts

    def _column_foot(self, guid):
        """(a frame at the column's foot — its section's axes, z up —, its section) of a steel column: an ArqSynth
        column (its placement at its foot) or a steel piece standing up (its lower end)."""
        from ..core import steel
        m = self._placement_si(self.by_guid(guid))
        sec = steel.get(self.steel_section(guid) or "")
        if self.kind_of(guid) == "steel_member":
            p = self.steel_member_params(guid)
            if p["end"][2] < p["start"][2]:          # (drawn from the top down: its foot is its end, turned over)
                m = m.copy()
                m[:3, 3] = p["end"]
                m[:3, 1] *= -1.0
                m[:3, 2] *= -1.0
        return m, sec

    def _build_connection(self, assembly, lang="pt"):
        kind, members, params = self.connection_params(assembly.GlobalId)
        for part in self.connection_parts(assembly):
            api.root.remove_product(self.file, product=part)
        if kind == "base_plate":
            parts = self._base_plate_parts(members[0], params, lang)
        else:
            parts = []
        if parts:
            api.aggregate.assign_object(self.file, products=parts, relating_object=assembly)
            for part in parts:
                self._mark(part, "steel_part")
                self._set_params(part, {"Ligacao": assembly.GlobalId})

    def _base_plate_parts(self, column, params, lang):
        from ..core import steel
        f = self.file
        m, sec = self._column_foot(column)
        if sec is None:
            return []
        b, h = steel.size(sec)
        A, B, spots, _warnings = base_plate_layout(params, b, h)
        tp, d, a = params["tp"], params["d"], params["a"]
        material = self._column_material(column, lang)
        storey = self.storey_of(column)
        parts = []
        # the plate: its outline, its holes
        d0 = hole(d)
        four_x3 = self.file.schema.upper().startswith("IFC4X3")
        plate = api.root.create_entity(f, ifc_class="IfcPlate", name="{} {}×{}×{}".format(
            "Chapa" if lang == "pt" else "Plate", _mm(A), _mm(B), _mm(tp)),
            predefined_type="BASE_PLATE" if four_x3 else "USERDEFINED")       # (IFC4 has no BASE_PLATE yet)
        if not four_x3:
            plate.ObjectType = "BASE_PLATE"
        self._place(plate, m)
        self._extrusion_body(plate, [self._plate_profile(A, B, spots, d0)], [(0.0, 0.0, -tp / 1000.0)],
                             [tp / 1000.0])
        net = (A * B - len(spots) * math.pi * d0 * d0 / 4) * tp * 1e-9                    # (m³)
        self._set_qto(plate, "Qto_PlateBaseQuantities", {"Width": tp / 1000.0 / self.unit_scale, "NetVolume": net,
                                                         "NetWeight": net * steel.DENSITY,
                                                         "GrossArea": A * B * 1e-6})
        parts.append(plate)
        # the anchor bolts: rod, washer, nut
        washer, wt = 2.5 * d, max(4.0, round(0.15 * d))
        nut_s, nut_h = 1.5 * d, 0.8 * d
        rod_low = -(tp + params["grout"] + params["embed"])
        for k, (x, y) in enumerate(spots, 1):
            bolt = api.root.create_entity(f, ifc_class="IfcMechanicalFastener", predefined_type="ANCHORBOLT",
                                          name="{} M{} {}".format("Chumbadouro" if lang == "pt" else "Anchor bolt",
                                                                  _mm(d), k))
            self._place(bolt, m)
            profiles = [f.createIfcCircleProfileDef("AREA", None, self._axis2d(x, y), d / 2000.0 / self.unit_scale),
                        f.createIfcRectangleProfileDef("AREA", None, self._axis2d(x, y), washer / 1000.0 /
                                                       self.unit_scale, washer / 1000.0 / self.unit_scale),
                        self._hexagon(x, y, nut_s)]
            self._extrusion_body(bolt, profiles, [(0.0, 0.0, rod_low / 1000.0), (0.0, 0.0, 0.0),
                                                   (0.0, 0.0, wt / 1000.0)],
                                 [(params["proj"] - rod_low) / 1000.0, wt / 1000.0, nut_h / 1000.0])
            pset = api.pset.add_pset(f, product=bolt, name="Pset_MechanicalFastenerAnchorBolt")
            api.pset.edit_pset(f, pset=pset, properties={"AnchorBoltDiameter": d / 1000.0 / self.unit_scale,
                                                         "AnchorBoltLength": (params["proj"] - rod_low) / 1000.0
                                                         / self.unit_scale,
                                                         "AnchorBoltProtrusionLength": params["proj"] / 1000.0
                                                         / self.unit_scale})
            parts.append(bolt)
        # the weld all round the column's foot
        weld = api.root.create_entity(f, ifc_class="IfcFastener", predefined_type="WELD",
                                      name="{} a{}".format("Soldadura" if lang == "pt" else "Weld", _mm(a)))
        self._place(weld, m)
        pset = api.pset.add_pset(f, product=weld, name="Pset_FastenerWeld")
        api.pset.edit_pset(f, pset=pset, properties={"a": a / 1000.0 / self.unit_scale,
                                                     "l": steel.properties(sec.name)["paint"] / self.unit_scale})
        parts.append(weld)
        api.material.assign_material(f, products=parts, type="IfcMaterial", material=material)
        if storey:
            api.spatial.assign_container(f, products=parts, relating_structure=self.storey(storey))
        return parts

    def _column_material(self, column, lang):
        material = ifcopenshell.util.element.get_material(self.by_guid(column), should_skip_usage=True)
        if material is not None and material.is_a("IfcMaterialProfileSet") and material.MaterialProfiles:
            found = material.MaterialProfiles[0].Material
            if found is not None:
                return found
        return self._material("aco_s275", lang)

    # ------------------------------------------------------------ geometry helpers (file units)

    def _axis2d(self, x, y):
        u = 0.001 / self.unit_scale
        return self.file.createIfcAxis2Placement2D(self.file.createIfcCartesianPoint((float(x * u), float(y * u))))

    def _hexagon(self, x, y, across):
        """A hexagonal profile (a nut) `across` mm across its flats, its middle at (x, y) mm."""
        u = 0.001 / self.unit_scale
        r = across / math.sqrt(3.0)
        pts = [self.file.createIfcCartesianPoint((float((x + r * math.cos(math.pi / 3 * k)) * u),
                                                  float((y + r * math.sin(math.pi / 3 * k)) * u))) for k in range(7)]
        return self.file.createIfcArbitraryClosedProfileDef("AREA", None, self.file.createIfcPolyline(pts))

    def _plate_profile(self, A, B, spots, d0):
        """A plate's outline A × B mm round its middle, with its holes."""
        f = self.file
        u = 0.001 / self.unit_scale
        corners = [(-A / 2, -B / 2), (A / 2, -B / 2), (A / 2, B / 2), (-A / 2, B / 2), (-A / 2, -B / 2)]
        outer = f.createIfcPolyline([f.createIfcCartesianPoint((float(x * u), float(y * u))) for x, y in corners])
        holes = [f.createIfcCircle(self._axis2d(x, y), float(d0 / 2 * u)) for x, y in spots]
        if not holes:
            return f.createIfcArbitraryClosedProfileDef("AREA", None, outer)
        return f.createIfcArbitraryProfileDefWithVoids("AREA", None, outer, holes)

    def _extrusion_body(self, product, profiles, origins, depths):
        """A body of extrusions up its own z: each profile from its origin (m), its depth (m)."""
        f = self.file
        u = 1.0 / self.unit_scale
        items = [f.createIfcExtrudedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint(tuple(float(c * u) for c in o))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(depth * u))
            for profile, o, depth in zip(profiles, origins, depths)]
        rep = f.createIfcShapeRepresentation(self.body, self.body.ContextIdentifier, "SweptSolid", items)
        api.geometry.assign_representation(f, product=product, representation=rep)


def _mm(v):
    return "{:g}".format(float(v))
