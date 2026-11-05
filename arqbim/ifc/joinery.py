"""(0.288) Doors and windows made by the generator (core/joinery): a type's design kept in its ArqSynth_Parametros
(«Desenho»), with IFC's own description of it on the type — its OperationType / PartitioningType, its lining and panel
properties (IfcDoorLiningProperties and IfcDoorPanelProperties, IfcWindowLiningProperties and
IfcWindowPanelProperties) and its materials as IFC names them for doors and windows (a constituent set: «Lining»,
«Framing», «Glazing») —; each door's / window's body made of its pieces in their materials (IfcTriangulatedFaceSets,
each styled: read straight from the file to be shown, in their colours) and a door's plan symbol."""

import re

import ifcopenshell
import ifcopenshell.api as api
import ifcopenshell.guid
import ifcopenshell.util.element

from ..core import joinery as core
from . import catalog
from .edit import MIRRORED, PARAM_PSET, VARIANTS, _single_values

DESIGN_PARAM = "Desenho"
SIGN_GAP = 0.002                   # m: the elevation signs out of the frame's faces
PREDEFINED_SETS = ("IfcDoorLiningProperties", "IfcDoorPanelProperties", "IfcWindowLiningProperties",
                   "IfcWindowPanelProperties")


def _natural(text):
    """A key sorting "P2" before "P10"."""
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", text or "")]


def base_name(name):
    """A type's name without a variant's ending: a door's right-hand one ("… (à direita)"), a window's mirror image
    ("… (espelhada)")."""
    for suffix in VARIANTS:
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return name


class JoineryMixin:

    def _type_params(self, type_):
        """A type's ArqSynth_Parametros, read straight from it."""
        for pset in getattr(type_, "HasPropertySets", None) or ():
            if pset.is_a("IfcPropertySet") and pset.Name == PARAM_PSET:
                values = _single_values(pset)
                return values if values is not None else \
                    ifcopenshell.util.element.get_psets(type_).get(PARAM_PSET, {})
        return {}

    def opening_design(self, element):
        """The design (core.joinery.Design) of a door / window or of its type: the type's own («Desenho»), else the
        catalogue's of its name when it opens as the type says, else one made from IFC's description of it (its
        operation / partitioning, its fanlight, its panels' ways of opening)."""
        is_type = element.is_a("IfcTypeObject")
        type_ = element if is_type else ifcopenshell.util.element.get_type(element)
        kind = "door" if element.is_a() in ("IfcDoor", "IfcDoorType") else "window"
        source = type_ if type_ is not None else element
        params = self._type_params(type_) if type_ is not None else {}
        text = params.get(DESIGN_PARAM)
        if text:
            try:
                return core.from_json(text)
            except ValueError:
                pass
        operation = (getattr(source, "OperationType", None) if kind == "door"
                     else getattr(source, "PartitioningType", None)) or ""
        name = base_name((type_.Name or "") if type_ is not None else "")
        spec = next((o for o in catalog.OPENING_BY_KEY.values()
                     if o.kind == kind and o.design is not None and name in (o.name_pt, o.name_en)), None)
        if spec is not None:
            for design in (spec.design, core.mirrored(spec.design)):
                found = core.door_operation(design) if kind == "door" else core.window_partitioning(design)
                if found[0] == operation:
                    return design
        ops = [p.OperationType for p in getattr(type_, "HasPropertySets", None) or ()
               if p.is_a("IfcWindowPanelProperties")] if type_ is not None and kind == "window" else []
        return core.standard(kind, operation, float(params.get("Bandeira") or 0.0),
                             float(params.get("Aro") or 0.0) if kind == "window" else None, ops)

    def opening_types_used(self):
        """(0.293) The door and window types the project's doors and windows are of — a right-hand door's and a
        mirrored window's counted with the type they come from —: [dict(name, kind, design, width, height, sill (a
        window's; None if unknown), count, marks)], the doors first, each kind by name."""
        groups = {}
        for cls, kind in (("IfcDoorType", "door"), ("IfcWindowType", "window")):
            for type_ in self.file.by_type(cls):
                elements = list(ifcopenshell.util.element.get_types(type_))
                if not elements:
                    continue
                name = base_name(type_.Name or "")
                group = groups.setdefault((kind, name), {"types": [], "elements": []})
                group["types"].append(type_)
                group["elements"] += elements
        out = []
        for (kind, name), group in sorted(groups.items(), key=lambda kv: (kv[0][0] != "door", _natural(kv[0][1]))):
            base = next((t for t in group["types"] if (t.Name or "") == name), group["types"][0])
            width, height = self._opening_type_size(base)
            params = self._type_params(base)
            sill = None
            if kind == "window":
                spec = next((o for o in catalog.OPENING_BY_KEY.values() if name in (o.name_pt, o.name_en)), None)
                sill = float(params["Peitoril"]) if params.get("Peitoril") is not None else \
                    (spec.sill if spec is not None else None)
            marks = sorted((e.Tag for e in group["elements"] if e.Tag), key=_natural)
            out.append({"name": name, "kind": kind, "design": self.opening_design(base), "width": width,
                        "height": height, "sill": sill, "count": len(group["elements"]), "marks": marks})
        return out

    def mirrored_window_type(self, type_, lang="pt"):
        """(0.289) The type of a window seen in a mirror: itself if its design is symmetric; the type it was made from
        if it is a mirror image already («… (espelhada)»); else that type, found or made — the mirror image of the
        design, with the parameters (its sizes) and materials."""
        design = self.opening_design(type_)
        mirror = core.mirrored(design)
        if mirror == design:
            return type_
        windows = self.file.by_type("IfcWindowType")
        name = type_.Name or ""
        base = base_name(name)
        if base != name:
            found = next((t for t in windows if t.Name == base and self.opening_design(t) == mirror), None)
            if found is not None:
                return found
        name = base + MIRRORED.get(lang, MIRRORED["en"])
        found = next((t for t in windows if t.Name == name and self.opening_design(t) == mirror), None)
        if found is not None:
            return found
        new = api.root.create_entity(self.file, ifc_class="IfcWindowType", name=name, predefined_type="WINDOW")
        params = {k: v for k, v in self._type_params(type_).items() if k not in ("id", DESIGN_PARAM)}
        if params:
            self._set_params(new, params)
        self.set_opening_design(new, mirror, *self._opening_type_size(type_), lang=lang)
        return new

    def set_opening_design(self, type_, design, width, height, lang="pt"):
        """A door / window type described by its design (`width` × `height`, its size): its OperationType /
        PartitioningType, the design in its parameters (with its fanlight, «Bandeira»), its lining and panel
        properties, its materials."""
        f, u = self.file, 1.0 / self.unit_scale
        if type_.is_a("IfcDoorType"):
            type_.OperationType, type_.UserDefinedOperationType = core.door_operation(design)
        else:
            type_.PartitioningType, type_.UserDefinedPartitioningType = core.window_partitioning(design)
        values = {DESIGN_PARAM: f.createIfcText(core.to_json(design))}
        transom = core.transom_of(design, height) if design.kind == "door" else 0.0
        if transom or "Bandeira" in self._type_params(type_):
            values["Bandeira"] = float(transom)
        self._set_params(type_, values)
        self._set_common(type_, design, width, height)
        self._set_predefined_sets(type_, design, width, height, u)
        self._set_joinery_material(type_, design, lang)

    def _set_common(self, type_, design, width, height):
        """(0.291) What the design tells of IFC4's common set of a door / window type: its GlazingAreaFraction (none:
        no glass — a ratio IFC wants over 0), a window's HasSillExternal (its peitoril)."""
        name = "Pset_DoorCommon" if type_.is_a("IfcDoorType") else "Pset_WindowCommon"
        fraction = core.glazing_fraction(design, width, height)
        values = {"GlazingAreaFraction": round(fraction, 4) if fraction > 1e-6 else None}
        if design.kind == "window":
            values["HasSillExternal"] = design.stone > 0
        pset = next((p for p in type_.HasPropertySets or () if p.is_a("IfcPropertySet") and p.Name == name), None)
        if pset is None:
            if all(v is None for v in values.values()):
                return
            pset = api.pset.add_pset(self.file, product=type_, name=name)
        api.pset.edit_pset(self.file, pset=pset, properties=values)
        if not pset.HasProperties:                   # (IFC wants a set to have one)
            api.pset.remove_pset(self.file, product=type_, pset=pset)

    def _set_predefined_sets(self, type_, design, width, height, u):
        """IFC's lining and panel properties of a door / window type, from its design (replacing those it had)."""
        f = self.file
        old = [p for p in type_.HasPropertySets or () if p.is_a() in PREDEFINED_SETS]
        keep = [p for p in type_.HasPropertySets or () if p.is_a() not in PREDEFINED_SETS]

        def new(ifc_class, position=None, **values):
            # (named after their class — and the panel's place —: property sets are found by their names)
            name = ifc_class[3:] + (" " + position if position else "")
            if position:
                values["PanelPosition"] = position
            return f.create_entity(ifc_class, GlobalId=ifcopenshell.guid.new(), Name=name,
                                   **{k: v for k, v in values.items() if v is not None})

        made = []
        transoms, mullions = core.bars_offsets(design, width, height)
        if design.kind == "door":
            heights = core._sizes([r.height for r in design.rows], height)
            lining = {"LiningThickness": design.frame * u,
                      # (none: a lining as deep as the wall it is in, as IFC reads an omitted depth)
                      "LiningDepth": design.depth * u if design.depth > 0 else None}
            if design.columns and transoms:             # (0.306) by columns: its lowest transom
                lining.update(TransomThickness=design.mullion * u, TransomOffset=transoms[0] * height * u)
            elif len(design.rows) > 1 and not design.columns:
                lining.update(TransomThickness=design.mullion * u, TransomOffset=heights[0] * u)
            if core.casings(design, width, height, 0.0, 0.1):        # its casings: their width, their thickness
                lining.update(CasingThickness=(design.casing + design.frame) * u, CasingDepth=design.casing_depth * u)
            if design.stone > 0:                                      # (0.290) its soleira (its depth: the wall's
                lining.update(ThresholdThickness=design.stone * u,   # and its nose, omitted when the lining's is)
                              ThresholdDepth=(design.depth + design.stone_out) * u if design.depth > 0 else None)
            made.append(new("IfcDoorLiningProperties", **lining))
            for cell, position, share in core.panels(design, width, height):
                made.append(new("IfcDoorPanelProperties", position, PanelDepth=design.sash_depth * u,
                                PanelOperation=core.OPERATIONS[cell.operation].door or "NOTDEFINED",
                                PanelWidth=float(share)))
        else:
            lining = {"LiningDepth": design.depth * u, "LiningThickness": design.frame * u}
            if transoms:
                lining.update(TransomThickness=design.mullion * u, FirstTransomOffset=float(transoms[0]),
                              SecondTransomOffset=float(transoms[1]) if len(transoms) > 1 else None)
            if mullions:
                lining.update(MullionThickness=design.mullion * u, FirstMullionOffset=float(mullions[0]),
                              SecondMullionOffset=float(mullions[1]) if len(mullions) > 1 else None)
            made.append(new("IfcWindowLiningProperties", **lining))
            for cell, position, _share in core.panels(design, width, height):
                made.append(new("IfcWindowPanelProperties", position,
                                OperationType=core.OPERATIONS[cell.operation].window,
                                FrameDepth=design.sash_depth * u, FrameThickness=design.sash * u))
        type_.HasPropertySets = keep + made or None
        for p in old:
            if not f.get_total_inverses(p):          # (one shared with another type, from another program, stays)
                f.remove(p)

    def _joinery_material(self, key, lang="pt"):
        """The IfcMaterial of a catalogue material, found by either of its names (made in `lang` if missing)."""
        spec = catalog.MATERIALS[key]
        for m in self.file.by_type("IfcMaterial"):
            if m.Name in (spec.name_pt, spec.name_en):
                return m
        return self._material(key, lang)

    def _set_joinery_material(self, type_, design, lang):
        """A door's / window's type material: a constituent set of its frame («Lining»), its leaves («Framing») and its
        glass («Glazing»), shared by the types of the same three."""
        f = self.file
        materials = [(part, self._joinery_material(key, lang)) for part, key in core.constituents(design)]
        name = " + ".join(dict.fromkeys(m.Name for _p, m in materials))
        wanted = next((s for s in f.by_type("IfcMaterialConstituentSet") if s.Name == name and
                       [(c.Name, c.Material) for c in s.MaterialConstituents or ()] == materials), None)
        if wanted is None:
            wanted = api.material.add_material_set(f, name=name, set_type="IfcMaterialConstituentSet")
            for part, material in materials:
                api.material.add_constituent(f, constituent_set=wanted, material=material).Name = part
        if ifcopenshell.util.element.get_material(type_, should_skip_usage=True) != wanted:
            api.material.unassign_material(f, products=[type_])
            api.material.assign_material(f, products=[type_], type=wanted.is_a(), material=wanted)

    def _joinery_style(self, key, cache):
        """The surface style of a catalogue material (its colour on the pieces made of it), or None."""
        if key not in cache:
            material = self._joinery_material(key)
            cache[key] = next((s for s in self.file.by_type("IfcSurfaceStyle") if s.Name == material.Name), None)
        return cache[key]

    def door_plan_pieces(self, guid):
        """(0.359) A door's pieces as a plan draws them, from its design (core.joinery.plan_pieces), not from its body's
        cut — each a piece of its own, outlined and hatched apart: [(role, ring [(x, y)…] in the plan (the program's
        coordinates), its cut's hatch (as hatches gives them))] — its lining's jambs, its casings, its soleira and,
        drawn closed, its leaves."""
        import numpy as np
        from .model import _cut_key
        filling = self.by_guid(guid)
        if filling is None or not filling.is_a("IfcDoor") or not filling.OverallWidth:
            return []
        s = self.unit_scale
        width, height = filling.OverallWidth * s, (filling.OverallHeight or 0.0) * s
        wall = self.host_wall(guid)
        thickness = self.wall_params(wall)[2] if wall is not None and self.kind_of(wall) == "wall" else None
        design = self.opening_design(filling)
        if thickness is None:                            # (another host: its frame's own depth, else 20 cm)
            thickness = design.depth if design.depth > 0 else 0.2
        depth = design.depth if 0 < design.depth < thickness else thickness
        y0 = (thickness - depth) / 2
        m = self._placement_si(filling)
        known, out = {}, []
        for role, ring, key in core.plan_pieces(design, width, height, y0, y0 + depth, (0.0, thickness)):
            local = np.array([(x, y, 0.0) for x, y in ring])
            world = local @ m[:3, :3].T + m[:3, 3]
            material = self._joinery_material(key) if key else None
            out.append((role, [(float(p[0]), float(p[1])) for p in world], _cut_key(material, known)))
        return out

    def door_hinge(self, guid):
        """(0.359) A door with one leaf that swings: (its hinges' jamb, the other jamb) as plan points (the program's
        coordinates, at the door's base) — else None (two leaves, sliding, folding…)."""
        import numpy as np
        filling = self.by_guid(guid)
        if filling is None or not filling.is_a("IfcDoor") or not filling.OverallWidth:
            return None
        s = self.unit_scale
        width, height = filling.OverallWidth * s, (filling.OverallHeight or 0.0) * s
        design = self.opening_design(filling)
        lights, _bars = core.layout(design, width, height)
        leaves = [lt for lt in lights if lt.row == 0 and core.door_leaf(lt.cell.operation)]
        if len(leaves) != 1 or core.OPERATIONS[leaves[0].cell.operation].hand not in ("LEFT", "RIGHT"):
            return None
        leaf = leaves[0]
        left = core.OPERATIONS[leaf.cell.operation].hand == "LEFT"
        m = self._placement_si(filling)
        at = lambda x: m[:3, :3] @ np.array((x, 0.0, 0.0)) + m[:3, 3]      # noqa: E731
        return (at(leaf.x0), at(leaf.x1)) if left else (at(leaf.x1), at(leaf.x0))

    def _set_joinery_body(self, filling, design, width, height, thickness):
        """A door's / window's body from its design — `width` × `height`, in a wall `thickness` thick: its frame from
        face to face (a frame of no depth of its own: a door's lining), else in the wall's middle — and a door's plan
        symbol."""
        f, u = self.file, 1.0 / self.unit_scale
        depth = design.depth if 0 < design.depth < thickness else thickness
        y0 = (thickness - depth) / 2
        y1 = y0 + depth
        items, styles = [], {}
        for key, (verts, tris) in core.meshes(design, width, height, y0, y1, (0.0, thickness)).items():
            item = f.createIfcTriangulatedFaceSet(f.createIfcCartesianPointList3D((verts * u).tolist()), None, True,
                                                  (tris + 1).tolist(), None)
            style = self._joinery_style(key, styles)
            if style is not None:
                f.createIfcStyledItem(item, [style], None)
            items.append(item)
        api.geometry.assign_representation(f, product=filling, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "Tessellation", items))
        if design.kind == "door":
            plan = self.plan_context()
            curves = [f.createIfcPolyline([f.createIfcCartesianPoint((float(x * u), float(y * u))) for x, y in line])
                      for line in core.plan_symbol(design, width, height, y0, y1, (0.0, thickness))]
            api.geometry.assign_representation(f, product=filling, representation=f.createIfcShapeRepresentation(
                plan, plan.ContextIdentifier, "Curve2D", curves))
        # (0.292) how its leaves open, drawn on both faces of its frame, a hair out: an elevation or a section shows
        # the one turned to it (what is in front hides the other)
        signs = core.elevation_signs(design, width, height)
        if signs:
            context = self.elevation_context()
            curves = [f.createIfcPolyline([f.createIfcCartesianPoint((float(x * u), float(y * u), float(z * u)))
                                           for x, z in line]) for y in (y0 - SIGN_GAP, y1 + SIGN_GAP) for line in signs]
            api.geometry.assign_representation(f, product=filling, representation=f.createIfcShapeRepresentation(
                context, context.ContextIdentifier, "Curve3D", curves))
