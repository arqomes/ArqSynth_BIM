"""Each element's IFC data (0.266), as the owner asked: «ao desenhar, cada elemento devia trazer uma categoria de
dados de IFC e parâmetros correspondentes». The standard property set of its class — IFC4's Pset_…Common (or, for
the distribution elements and furniture, Pset_…TypeCommon), from the buildingSMART templates IfcOpenShell carries:
no name is made up — every property of it, set or not, for the Properties to show and fill in place. What the
program knows is written by itself when an element is made or changed (its type's name as its Reference…); what
the user wrote by hand is never overwritten (the program's parameter DadosManuais: "Pset_…Common.Property;…"); a
value cleared by hand gives the automatic one back.

Mixed into IfcModel. The templates of IFC4 ADD2 give the LoadBearing of Pset_RoofCommon, Pset_StairCommon and
Pset_RampCommon with its fields one place on — its definition ("Indicates whether the object is intended to carry
loads…") as its name, its measure (IfcBoolean) as its kind: read as LoadBearing, a single boolean, as IFC4 has it
everywhere else."""

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element
import ifcopenshell.util.pset
import numpy as np

from .edit import PARAM_PSET, _MISSING, _own_param

api = ifcopenshell.api
MANUAL = "DadosManuais"
SHOWN_ELSEWHERE = {"Status"}        # (the phase: its own editor in the Properties)
WALL_LIKE = ("wall", "curved_wall", "curtain_wall")
SIDE_GAP = 0.05                     # m beyond a wall's face: which side is in a room (0.267)
SIDE_BY_HAND = "LadoManual"         # (0.297) a window turned to the other side by hand: not turned by the program
# (0.272) the surface resistances Rsi, Rse (m²·K/W) of EN ISO 6946 (its table 7: the conventional values) by the way
# the heat flows: across a wall, up through a roof, down through a floor
SURFACE = {"horizontal": (0.13, 0.04), "up": (0.10, 0.04), "down": (0.17, 0.04)}
FLOW = (("IfcWall", "horizontal"), ("IfcRoof", "up"), ("IfcSlab", "down"))
_LOAD_BEARING_TEXT = "Indicates whether the object is intended to carry loads"
_COMMON, _TEMPLATES = {}, {}


def common_pset(ifc_class):
    """The standard property set of an IFC class — Pset_<Class>Common, else Pset_<Class>TypeCommon — from IFC4's
    templates; a subclass without one of its own: its parent's (IfcWallStandardCase: the wall's). None if none."""
    if ifc_class not in _COMMON:
        templates = ifcopenshell.util.pset.get_template("IFC4")
        found = None
        try:
            decl = ifcopenshell.ifcopenshell_wrapper.schema_by_name("IFC4").declaration_by_name(ifc_class)
        except (RuntimeError, ValueError):
            decl = None
        while decl is not None and found is None:
            names = templates.get_applicable_names(decl.name(), pset_only=True)
            stem = decl.name()[3:]
            found = next((n for n in ("Pset_%sCommon" % stem, "Pset_%sTypeCommon" % stem) if n in names), None)
            decl = decl.supertype()
        _COMMON[ifc_class] = found
    return _COMMON[ifc_class]


def property_kind(prop):
    """(kind, choices) of a property template as the Properties edit it — kind "bool" | "text" | "integer" |
    "number" | "length" (metres here, the project's unit in the IFC) | "choice" (choices: the enumeration's) — or
    None (bounded values, lists, tables: not edited here)."""
    measure, kind = prop.PrimaryMeasureType or "", prop.TemplateType or ""
    if kind.startswith("Ifc"):                     # (IFC4 ADD2's LoadBearing of roofs…: its fields one place on)
        measure, kind = kind, "P_SINGLEVALUE"
    if kind == "P_ENUMERATEDVALUE" and prop.Enumerators:
        return "choice", tuple(v.wrappedValue for v in prop.Enumerators.EnumerationValues)
    if kind != "P_SINGLEVALUE":
        return None
    if measure in ("IfcBoolean", "IfcLogical"):
        return "bool", None
    if measure in ("IfcLabel", "IfcText", "IfcIdentifier"):
        return "text", None
    if measure in ("IfcInteger", "IfcCountMeasure"):
        return "integer", None
    if measure in ("IfcLengthMeasure", "IfcPositiveLengthMeasure"):
        return "length", None
    return "number", None


def property_name(prop):
    """A template's property name — IFC4 ADD2's LoadBearing named by its definition read as LoadBearing; None
    for any other name that is not one (with spaces)."""
    if " " not in prop.Name:
        return prop.Name
    return "LoadBearing" if prop.Name.startswith(_LOAD_BEARING_TEXT) else None


def template(pset_name):
    """[(property, kind, choices)] of a standard property set, in the templates' order (what can be edited)."""
    if pset_name not in _TEMPLATES:
        found = ifcopenshell.util.pset.get_template("IFC4").get_by_name(pset_name)
        out = []
        for prop in (found.HasPropertyTemplates or ()) if found is not None else ():
            name = property_name(prop) if prop.is_a("IfcSimplePropertyTemplate") else None
            kind = property_kind(prop) if name else None
            if kind is not None and all(name != n for n, _k, _c in out):
                out.append((name, kind[0], kind[1]))
        _TEMPLATES[pset_name] = out
    return _TEMPLATES[pset_name]


def _value(prop):
    """A property's value as read: a single value's, an enumeration's first, else None."""
    if prop.is_a("IfcPropertySingleValue"):
        return prop.NominalValue.wrappedValue if prop.NominalValue is not None else None
    if prop.is_a("IfcPropertyEnumeratedValue"):
        values = prop.EnumerationValues or ()
        return values[0].wrappedValue if values else None
    return None


def own_pset(element, pset_name):
    """The element's own property set of that name (not its type's) — (0.271) a type's: in its HasPropertySets —
    or None."""
    if element.is_a("IfcTypeObject"):
        return next((p for p in element.HasPropertySets or () if p.is_a("IfcPropertySet") and p.Name == pset_name),
                    None)
    for rel in getattr(element, "IsDefinedBy", None) or ():
        if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.is_a("IfcPropertySet") and \
                rel.RelatingPropertyDefinition.Name == pset_name:
            return rel.RelatingPropertyDefinition
    return None


def own_values(element, pset_name):
    """{property: value} of the element's own property set of that name (not its type's)."""
    pset = own_pset(element, pset_name)
    return {p.Name: _value(p) for p in pset.HasProperties or ()} if pset is not None else {}


def _conductivity(material):
    """A material's thermal conductivity λ (W/(m·K), Pset_MaterialThermal), or None."""
    if material is None:
        return None
    value = ifcopenshell.util.element.get_psets(material).get("Pset_MaterialThermal", {}).get("ThermalConductivity")
    return float(value) if isinstance(value, (int, float)) and value > 0 else None


def _occurrence_class(type_class):
    """IfcWallType -> IfcWall (a type's elements' class, whose standard set it shares)."""
    return type_class[:-4] if type_class.endswith("Type") else type_class


def _type_of(element):
    for rel in getattr(element, "IsTypedBy", None) or ():
        return rel.RelatingType
    return None


class IfcDataMixin:
    def manual_data(self, element):
        """The standard properties written by hand on an element: {"Pset_…Common.Property"}."""
        value = _own_param(element, MANUAL)
        return set(value.split(";")) - {""} if isinstance(value, str) else set()

    def mark_manual(self, guid, pset_name, prop, on=True):
        """A property written by hand (on), or given back to the program (off)."""
        e = self.by_guid(guid)
        marks = self.manual_data(e)
        key = "{}.{}".format(pset_name, prop)
        if (key in marks) == bool(on):
            return
        marks = (marks | {key}) if on else (marks - {key})
        self.set_property(guid, PARAM_PSET, MANUAL, ";".join(sorted(marks)) if marks else None)

    def derived_data(self, element):
        """What the program knows of an element's standard set: {property: value} — its type's name as its
        Reference (as Revit writes it)."""
        out = {}
        type_ = _type_of(element)
        if type_ is not None and type_.Name:
            out["Reference"] = type_.Name
        if element.is_a("IfcDoor") or element.is_a("IfcWindow"):     # (0.267) outside if its wall is
            host = self.host_wall(element.GlobalId)
            wall = self.by_guid(host) if host else None
            name = common_pset(wall.is_a()) if wall is not None else None
            outside = own_values(wall, name).get("IsExternal") if name else None
            if isinstance(outside, bool):
                out["IsExternal"] = outside
        if any(element.is_a(cls) for cls, _flow in FLOW):                # (0.272) U by its layers, if it can be
            out["ThermalTransmittance"] = self.thermal_transmittance(element)
        return out

    def thermal_transmittance(self, element):
        """(0.272) U (W/m²·K) of a wall, roof or slab of layers, as EN ISO 6946 has it for plane layers:
        1 / (Rsi + Σ thickness / λ + Rse) — its surface resistances by the way heat flows through it (FLOW); None
        when it is not of layers or a layer's material has no thermal conductivity (Pset_MaterialThermal)."""
        flow = next((f for cls, f in FLOW if element.is_a(cls)), None)
        material = ifcopenshell.util.element.get_material(element, should_skip_usage=True) if flow else None
        if material is None or not material.is_a("IfcMaterialLayerSet") or not material.MaterialLayers:
            return None
        resistance = sum(SURFACE[flow])
        for layer in material.MaterialLayers:
            conductivity = _conductivity(layer.Material)
            if not conductivity or not layer.LayerThickness:
                return None
            resistance += float(layer.LayerThickness) * self.unit_scale / conductivity
        return round(1.0 / resistance, 3)

    def _derive(self, e, wanted):
        """Values the program knows written into an element's standard set where they are not so already — what
        the user wrote by hand kept. Returns how many were written."""
        name = common_pset(e.is_a())
        if name is None or not wanted:
            return 0
        manual = self.manual_data(e)
        own = own_values(e, name)
        changes = {k: v for k, v in wanted.items() if "{}.{}".format(name, k) not in manual
                   and own.get(k, _MISSING) != v and not (v is None and k not in own)}     # (None: taken away)
        if not changes:
            return 0
        pset = own_pset(e, name) or api.pset.add_pset(self.file, product=e, name=name)
        api.pset.edit_pset(self.file, pset=pset, properties=changes)
        if not pset.HasProperties:
            api.pset.remove_pset(self.file, product=e, pset=pset)
        return len(changes)

    # ------------------------------------------------------------ the type's (0.271)

    def type_data(self, type_):
        """A type's standard set, every property of it: (its name, [(property, kind, choices, value)]) — None when
        its class has none (an IfcWallType: Pset_WallCommon, as its walls')."""
        name = common_pset(_occurrence_class(type_.is_a())) if type_ is not None else None
        if name is None:
            return None
        own = own_values(type_, name)
        rows = []
        for prop, kind, choices in template(name):
            if prop in SHOWN_ELSEWHERE or prop in ("Reference", "IsExternal"):
                continue                                    # (an element's own: its type's name, where it stands)
            value = own.get(prop)
            if kind == "length" and isinstance(value, (int, float)):
                value = float(value) * self.unit_scale
            rows.append((prop, kind, choices, value))
        return name, rows

    def set_type_property(self, type_, pset_name, prop, value):
        """A property of a type (None: taken away) — its elements have it unless they say otherwise by hand; the
        value an element was made with (not written by hand, not the program's) gives way to the type's."""
        pset = own_pset(type_, pset_name)
        if pset is None and value is None:
            return []
        pset = pset or api.pset.add_pset(self.file, product=type_, name=pset_name)
        old = next((p for p in pset.HasProperties or () if p.Name == prop), None)
        from .edit import _template_type
        enumerated = old.is_a("IfcPropertyEnumeratedValue") if old is not None else \
            _template_type(pset_name, prop) == "P_ENUMERATEDVALUE"
        api.pset.edit_pset(self.file, pset=pset, properties={prop: [value] if enumerated and value is not None
                                                             else value})
        if value is None and not pset.HasProperties:
            api.pset.remove_pset(self.file, product=type_, pset=pset)
        changed = []
        for rel in getattr(type_, "Types", None) or ():
            for e in rel.RelatedObjects:
                key = "{}.{}".format(pset_name, prop)
                if prop in own_values(e, pset_name) and key not in self.manual_data(e) and \
                        prop not in self.auto_properties(e):
                    self.set_property(e.GlobalId, pset_name, prop, None)
                changed.append(e.GlobalId)
        return changed

    def fill_ifc_data(self, guids):
        """The derived values (derived_data) written into the elements' standard sets. Returns how many."""
        written = 0
        for guid in dict.fromkeys(guids):
            e = self.by_guid(guid)
            if e is not None and e.is_a("IfcElement"):
                written += self._derive(e, self.derived_data(e))
        return written

    # ------------------------------------------------------------ outside or inside (0.267)

    def wall_sides(self, guid):
        """Points just beyond a wall's two faces, at a quarter, a half and three quarters along it: [(a, b)] (plan)
        — a straight, curved or curtain wall; [] for anything else."""
        kind = self.kind_of(guid)
        fractions = (0.25, 0.5, 0.75)
        if kind == "wall":
            length, _h, thickness = self.wall_params(guid)
            m = self.placement(guid)
            return [tuple(tuple((m @ np.array((length * f, s * (thickness / 2 + SIDE_GAP), 0.0, 1.0)))[:2])
                          for s in (1, -1)) for f in fractions]
        if kind == "curved_wall":
            centre, radius, start, sweep, _h, thickness = self.curved_wall_params(guid)
            out = []
            for f in fractions:
                d = np.array((np.cos(start + sweep * f), np.sin(start + sweep * f)))
                out.append(tuple(tuple(centre[:2] + d * (radius + s * (thickness / 2 + SIDE_GAP))) for s in (1, -1)))
            return out
        if kind == "curtain_wall":
            p = self.curtain_params(guid)
            out = []
            for f in fractions:
                if p["radius"] is None:
                    a, b = np.asarray(p["start"][:2]), np.asarray(p["end"][:2])
                    d = (b - a) / max(float(np.linalg.norm(b - a)), 1e-9)
                    at, n = a + (b - a) * f, np.array((-d[1], d[0]))
                else:
                    angle = p["angle"] + p["sweep"] * f
                    n = np.array((np.cos(angle), np.sin(angle)))
                    at = np.asarray(p["centre"][:2]) + n * p["radius"]
                out.append(tuple(tuple(at + n * s * 2 * SIDE_GAP) for s in (1, -1)))
            return out
        return []

    def _curtain_bands(self, storey):
        """The curtain walls of a storey as thin bands along their line (they close rooms as walls do)."""
        from shapely.geometry import LineString
        out = []
        for g in self.storey_elements(storey):
            if self.kind_of(g) != "curtain_wall":
                continue
            p = self.curtain_params(g)
            if p["radius"] is None:
                line = [tuple(p["start"][:2]), tuple(p["end"][:2])]
            else:
                line = [tuple(np.asarray(p["centre"][:2]) + p["radius"] * np.array(
                    (np.cos(p["angle"] + p["sweep"] * k / 16), np.sin(p["angle"] + p["sweep"] * k / 16))))
                        for k in range(17)]
            out.append(LineString(line).buffer(SIDE_GAP / 2, cap_style="flat"))
        return out

    def _plan_key(self, guid, kind):
        """Where a wall or column stands in the plan, rounded — what rings rooms (not its height)."""
        r = lambda v: tuple(round(float(x), 4) for x in np.ravel(v))           # noqa: E731
        if kind == "wall":
            length, _h, thickness = self.wall_params(guid)
            m = self.placement(guid)
            return r((*m[:2, :2].ravel(), *m[:2, 3], length, thickness, *self.wall_cuts(self.by_guid(guid))))
        if kind == "curved_wall":
            centre, radius, start, sweep, _h, thickness = self.curved_wall_params(guid)
            return r((*centre[:2], radius, start, sweep, thickness))
        if kind == "curtain_wall":
            p = self.curtain_params(guid)
            return r((*p["start"][:2], *p["end"][:2], p["radius"] or 0.0, p["sweep"] or 0.0))
        centre, x, size, _base, _top = self.column_box(guid)
        return r((*centre, *x[:2], *size))

    def external_storeys(self, changed):
        """The storeys where this transaction made a wall or a column (what rings the rooms), moved one in the
        plan (not only made it taller…), or removed something."""
        keys = self.__dict__.setdefault("_plan_keys", {})
        out = set(self.removed_storeys or ())
        made = set(self.made or ())
        for g in list(changed) + list(made):
            kind = self.kind_of(g) if self.by_guid(g) is not None else None
            if kind not in WALL_LIKE + ("column",):
                continue
            key = self._plan_key(g, kind)
            if g in made or keys.get(g) != key:
                keys[g] = key
                storey = self.storey_of(g)
                if storey:
                    out.add(storey)
        return out

    def _storey_rooms(self, storey):
        """(rooms, walls) of a storey, in one pass over it: what its walls, columns (as its rooms', storey_obstacles)
        and curtain walls ring — a shapely geometry, prepared; None if nothing — and, for each of its walls, the
        points beside its faces."""
        import shapely
        from shapely.geometry import Polygon
        from ..core.roof_blocks import polygons
        from ..core.walls import footprint
        bodies, walls = [], {}
        for g in self.storey_elements(storey):
            kind = self.kind_of(g)
            if kind == "wall":
                length, _h, thickness = self.wall_params(g)
                m = self.placement(g)
                start_cut, end_cut = self.wall_cuts(self.by_guid(g))
                bodies.append(Polygon([tuple((m @ np.array((x, y, 0.0, 1.0)))[:2])
                                       for x, y in footprint(length, thickness, start_cut, end_cut)]))
                walls[g] = [tuple(tuple((m @ np.array((length * f, s * (thickness / 2 + SIDE_GAP), 0.0, 1.0)))
                                        [:2]) for s in (1, -1)) for f in (0.25, 0.5, 0.75)]
            elif kind == "curved_wall":
                bodies += [Polygon(p) for p in self.curved_wall_band(g) if len(p) >= 3]
                walls[g] = self.wall_sides(g)
            elif kind == "curtain_wall":
                walls[g] = self.wall_sides(g)
            elif kind == "column":
                centre, x, (a, b), _base, _top = self.column_box(g)
                y = np.array((-x[1], x[0]))
                bodies.append(Polygon([tuple(centre + x * sx * a + y * sy * b)
                                       for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]))
        if not walls:
            return None, walls
        if any(self.kind_of(g) == "curtain_wall" for g in walls):
            bodies += self._curtain_bands(storey)
        try:
            union = shapely.union_all(bodies) if bodies else None
        except shapely.errors.GEOSException:                # (a footprint not quite simple: made valid first)
            union = shapely.union_all([shapely.make_valid(b) for b in bodies])
        rooms = shapely.union_all([Polygon(ring) for poly in polygons(union) for ring in poly.interiors]) \
            if union is not None else None
        if rooms is None or rooms.is_empty:
            return None, walls
        shapely.prepare(rooms)
        return rooms, walls

    def update_external(self, storeys, rooms_of=None):
        """IsExternal of the walls (straight, curved, curtain) of these storeys: outside when, somewhere along it,
        one of its sides is not in a room the storey's walls and columns ring (a garden wall alone: outside) — and
        of their doors and windows, their wall's. What the user wrote by hand kept. Returns how many changed.
        rooms_of: (0.297) a dict given the storeys' rooms found."""
        import shapely
        changed = 0
        for storey in storeys:
            if self.by_guid(storey) is None:
                continue
            rooms, walls = self._storey_rooms(storey)
            if rooms_of is not None:
                rooms_of[storey] = rooms
            if not walls:
                continue

            def inside(p):
                return rooms is not None and bool(shapely.contains_xy(rooms, p[0], p[1]))

            for g, sides in walls.items():
                outside = not sides or any(not (inside(a) and inside(b)) for a, b in sides)
                e = self.by_guid(g)
                changed += self._derive(e, {"IsExternal": outside})
                for rel in getattr(e, "HasOpenings", None) or ():
                    for fill in rel.RelatedOpeningElement.HasFillings or ():
                        changed += self._derive(fill.RelatedBuildingElement, {"IsExternal": outside})
        return changed

    def orient_windows(self, guids, lang="pt", rooms_of=None):
        """(0.297) These windows, where their wall is outside (its IsExternal), turned with their outer side — where
        their peitoril, estore and portadas go — to the outside: the side of the wall not in a room the storey's walls
        ring, its other side in one (the storey's rooms in rooms_of, found if not); one turned by hand («LadoManual»)
        left as it is. Returns the GlobalIds turned."""
        import shapely
        rooms_of = {} if rooms_of is None else rooms_of
        turned = []
        for g in guids:
            e = self.by_guid(g)
            if e is None or not e.is_a("IfcWindow") or _own_param(e, SIDE_BY_HAND) is True or not e.FillsVoids:
                continue
            host = self.host_wall(g)
            kind = self.kind_of(host) if host else None
            if kind not in ("wall", "curved_wall"):
                continue
            wall = self.by_guid(host)
            if own_values(wall, common_pset(wall.is_a())).get("IsExternal") is not True:
                continue
            storey = self.storey_of(host)
            if storey not in rooms_of:
                rooms_of[storey] = self._storey_rooms(storey)[0] if storey else None
            rooms = rooms_of[storey]
            if rooms is None:
                continue
            thickness = self.wall_params(host)[2] if kind == "wall" else self.curved_wall_params(host)[5]
            m = self._placement_si(e)
            half = float(e.OverallWidth or 0.0) * self.unit_scale / 2
            # beside its outer face (y0) and beyond the wall's other face, at its middle
            out_side, in_side = [tuple((m @ np.array((half, y, 0.0, 1.0)))[:2])
                                 for y in (-SIDE_GAP, thickness + SIDE_GAP)]
            if shapely.contains_xy(rooms, *out_side) and not shapely.contains_xy(rooms, *in_side):
                self.turn_window(g, lang)
                turned.append(g)
        return turned

    def auto_properties(self, element):
        """The standard properties the program keeps up to date on this element (shown as its own: in blue)."""
        out = {"Reference"}
        kind = self.kind_of(element.GlobalId)
        if kind in WALL_LIKE or element.is_a("IfcDoor") or element.is_a("IfcWindow"):
            out.add("IsExternal")
        if any(element.is_a(cls) for cls, _flow in FLOW):
            out.add("ThermalTransmittance")                         # (0.272)
        return out

    # ------------------------------------------------------------ what is missing (0.273)

    def missing_data(self):
        """Before delivering: for each class of element in the model, each property of its standard set (the phase
        apart), the elements with no value for it (theirs or their type's) — [(class, set, [(property, [GlobalIds
        without], how many in all)])], the classes by name, their properties in the templates' order."""
        by_class = {}
        for e in self.file.by_type("IfcElement"):
            if e.is_a() in ("IfcOpeningElement", "IfcVirtualElement") or common_pset(e.is_a()) is None:
                continue
            by_class.setdefault(e.is_a(), []).append(e)
        out = []
        for cls in sorted(by_class):
            elements = by_class[cls]
            name = common_pset(cls)
            values = []
            for e in elements:
                type_ = _type_of(e)
                merged = dict(own_values(type_, name)) if type_ is not None else {}
                merged.update({k: v for k, v in own_values(e, name).items() if v is not None})
                values.append((e.GlobalId, merged))
            rows = [(prop, [g for g, v in values if v.get(prop) is None], len(elements))
                    for prop, _k, _c in template(name) if prop not in SHOWN_ELSEWHERE]
            out.append((cls, name, rows))
        return out

    def fill_known_data(self):
        """Everything the program knows written into every element (a file made before 0.266, or another
        program's): its type's name, outside or inside, its U. Returns how many properties were written."""
        storeys = {g for g, _n, _z in self.storeys()}
        written = self.update_external(storeys)
        return written + self.fill_ifc_data([e.GlobalId for e in self.file.by_type("IfcElement")])

    def ifc_type_data(self, guid):
        """(0.430) {property: value} an element's type gives in its standard set (a length in metres) — what «usar o
        valor do tipo» brings back when the element has its own."""
        e = self.by_guid(guid)
        name = common_pset(e.is_a()) if e is not None else None
        type_ = _type_of(e) if name is not None else None
        if type_ is None:
            return {}
        kinds = {prop: kind for prop, kind, _choices in template(name)}
        out = {}
        for prop, value in own_values(type_, name).items():
            if kinds.get(prop) == "length" and isinstance(value, (int, float)):
                value = float(value) * self.unit_scale
            out[prop] = value
        return out

    def ifc_data(self, guid):
        """An element's standard property set, every property of it: (its name, [(property, kind, choices, value,
        how)]) — value None if not set (a length in metres); how "manual" (written by hand), "auto" (the
        program's), "type" (its type's) or "" (written so). None when its class has none."""
        e = self.by_guid(guid)
        name = common_pset(e.is_a()) if e is not None else None
        if name is None:
            return None
        own = own_values(e, name)
        type_ = _type_of(e)
        inherited = own_values(type_, name) if type_ is not None else {}
        manual, auto = self.manual_data(e), self.auto_properties(e)
        rows = []
        for prop, kind, choices in template(name):
            if prop in SHOWN_ELSEWHERE:
                continue
            if prop in own:
                value = own[prop]
                how = "manual" if "{}.{}".format(name, prop) in manual else "auto" if prop in auto else ""
            elif prop in inherited:
                value, how = inherited[prop], "type"
            else:
                value, how = None, ""
            if kind == "length" and isinstance(value, (int, float)):
                value = float(value) * self.unit_scale
            rows.append((prop, kind, choices, value, how))
        return name, rows
