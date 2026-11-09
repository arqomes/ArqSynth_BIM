"""The project's own types (0.87, the type editor), read from its IFC: every IfcWallType, IfcSlabType, IfcRoofType,
IfcColumnType, IfcBeamType, IfcFootingType, IfcPipeSegmentType and IfcDuctSegmentType this program can draw
with — its layers (IfcMaterialLayerSet) or its section (IfcMaterialProfileSet) — as catalogue entries
(ifc.catalog.TypeSpec). And the project's materials (IfcMaterial, with their style's colour).

A type named as a catalogue entry keeps that entry's key ("parede_alv_20"); if the project changed it, the
project's version takes its place. The others get a key from their GlobalId ("t:…"), which stays the same when
they are edited. A footing's plan size is not in IFC's type: it is kept in the type's ArqSynth_Parametros.

Doors and windows (0.88): IfcDoorType / IfcWindowType, their sizes (width, height, sill when placed, frame
depth) in the type's ArqSynth_Parametros; the door types made for right-hand doors follow their own type."""

import ifcopenshell.util.element

from ..core import joinery
from ..ifc import catalog
from ..ifc.edit import PARAM_PSET, VARIANTS

CLASSES = {"wall": "IfcWallType", "slab": "IfcSlabType", "column": "IfcColumnType", "beam": "IfcBeamType",
           "footing": "IfcFootingType", "pipe": "IfcPipeSegmentType", "duct": "IfcDuctSegmentType",
           "pile": "IfcPileType", "door": "IfcDoorType", "window": "IfcWindowType",
           "conduit": "IfcCableCarrierSegmentType",                       # (0.146)
           "roof": "IfcRoofType"}                                         # (0.278)
SPECIAL = ("PILE_CAP", "BASESLAB", "BORED", "DRIVEN")    # PredefinedTypes kept with a type (0.94)
GREY = (0.75, 0.75, 0.75)


def material_key(name):
    """The catalogue key of a material by its name (in either language), else "m:" + its name."""
    for m in catalog._STARTER_MATERIALS.values():
        if name in (m.name_pt, m.name_en):
            return m.key
    return "m:" + (name or "")


def _colour(material):
    """The surface colour of a material's style (RGB 0..1), or None."""
    try:
        for rep in material.HasRepresentation or ():
            for r in rep.Representations or ():
                for item in r.Items or ():
                    for style in item.Styles or ():
                        for s in getattr(style, "Styles", None) or ():
                            colour = getattr(s, "SurfaceColour", None)
                            if colour is not None:
                                return float(colour.Red), float(colour.Green), float(colour.Blue)
    except (AttributeError, TypeError):
        pass
    return None


def read_material(m):
    """A MaterialSpec of an IfcMaterial: its category (its hatch), its style's colour, its density and thermal
    conductivity (0.89)."""
    from ..ifc import material_graphics
    key = material_key(m.Name)
    start = catalog._STARTER_MATERIALS.get(key)
    psets = ifcopenshell.util.element.get_psets(m)
    density = psets.get("Pset_MaterialCommon", {}).get("MassDensity")
    conductivity = psets.get("Pset_MaterialThermal", {}).get("ThermalConductivity")
    # (0.314) its graphics: as kept by this program, else as another program's fill styles say, else the catalogue's
    patterns = material_graphics.read_patterns(m) or material_graphics.read_foreign(m) or \
        {k: getattr(start, k) if start is not None else None for k in material_graphics.FIELDS}
    clear = material_graphics.transparency(m)
    finish = material_graphics.read_finish(m)                  # (0.343)
    look = material_graphics.read_look(m)                      # (0.468)
    graphics = dict(patterns, transparency=clear if clear is not None else (start.transparency if start else 0.0),
                    finish=finish if finish is not None else (start.finish if start else ""),
                    look=look if look is not None else (start.look if start else None))
    if start is not None:                          # (a catalogue material keeps its names in both languages)
        return catalog.MaterialSpec(key, start.name_pt, start.name_en, m.Category or "",
                                    _colour(m) or start.color, density, conductivity, **graphics)
    return catalog.MaterialSpec(key, m.Name or "", m.Name or "", m.Category or "", _colour(m) or GREY, density,
                                conductivity, **graphics)


def materials(ifc):
    """The project's materials that are not the catalogue's, or that the project changed: [MaterialSpec]."""
    out = []
    for m in ifc.file.by_type("IfcMaterial"):
        spec = read_material(m)
        start = catalog._STARTER_MATERIALS.get(spec.key)
        if start is not None and spec.category == start.category and spec.density is None and \
                spec.conductivity is None and all(abs(a - b) < 1e-3 for a, b in zip(spec.color, start.color)) \
                and spec.graphics() == start.graphics():
            continue
        out.append(spec)
    return out


def material_users(ifc, key):
    """The types (TypeSpec) that use a material, in layers or as their section's."""
    return [s for s in catalog.types() if s.material == key or any(k == key for k, _t in s.layers)]


def find_material(ifc, spec):
    names = {spec.name_pt, spec.name_en}
    return next((m for m in ifc.file.by_type("IfcMaterial") if m.Name in names), None)


def _starter_key(kind, name):
    for s in catalog._STARTER.values():
        if s.kind == kind and name in (s.name_pt, s.name_en):
            return s.key
    return None


def _same(a, b):
    """Two entries with the same layers / section / material (the names aside)."""
    def rounded(spec):
        return (tuple((k, round(t, 6)) for k, t in spec.layers),
                tuple(round(v, 6) for v in spec.profile) if spec.profile else None, spec.material,
                spec.predefined, spec.piles, spec.pile, round(spec.pile_length, 6), spec.shape,
                round(spec.web, 6) if spec.web else None,
                tuple(catalog.layer_function(spec, k) for k in range(len(spec.layers))),   # (0.334)
                spec.masonry, spec.section)                                                # (0.346, 0.494)
    return a.kind == b.kind and rounded(a) == rounded(b)


def read_type(ifc, type_, kind):
    """A TypeSpec of an IFC type, or None if it is not one this program can draw with."""
    s = ifc.unit_scale
    name = type_.Name or ""
    key = _starter_key(kind, name) or "t:" + type_.GlobalId
    mat = ifcopenshell.util.element.get_material(type_)
    predefined = getattr(type_, "PredefinedType", None)
    predefined = predefined if predefined in SPECIAL else None
    if kind in catalog.LAYERED:
        if mat is None or not mat.is_a("IfcMaterialLayerSet") or not mat.MaterialLayers:
            return None
        layers = tuple((material_key(layer.Material.Name if layer.Material else ""), float(layer.LayerThickness) * s)
                       for layer in mat.MaterialLayers)
        # (0.334) each layer's function, from its Priority (IFC4)
        functions = tuple(catalog.function_of_priority(getattr(layer, "Priority", None)) for layer in mat.MaterialLayers)
        functions = functions if any(functions) else ()
        profile, piles = None, {}
        if kind == "footing":
            params = ifcopenshell.util.element.get_psets(type_).get(PARAM_PSET, {})
            start = catalog._STARTER.get(key)
            if "PlantaX" in params:
                profile = (float(params["PlantaX"]), float(params.get("PlantaY", 0.0)))
            elif start is not None:
                profile = start.profile
            else:
                return None
            if params.get("Estacas"):                     # a pile cap's piles (0.94)
                piles = {"piles": int(params["Estacas"]), "pile": str(params.get("EstacaTipo") or "estaca_30"),
                         "pile_length": float(params.get("EstacaComprimento") or 8.0)}
            elif start is not None and start.piles:
                piles = {"piles": start.piles, "pile": start.pile, "pile_length": start.pile_length}
        masonry = None
        if kind == "wall":                                # (0.346) its own masonry, for Eurocode 6
            from ..core import ec6
            masonry = ec6.decode(ifcopenshell.util.element.get_psets(type_).get(PARAM_PSET, {}).get("Alvenaria"))
        return catalog.TypeSpec(key, kind, name, name, layers=layers, profile=profile, predefined=predefined,
                                functions=functions, masonry=masonry, **piles)
    if mat is None or not mat.is_a("IfcMaterialProfileSet") or not mat.MaterialProfiles:
        return None
    entry = mat.MaterialProfiles[0]
    profile = entry.Profile
    shape, web = None, None
    material = material_key(entry.Material.Name) if entry.Material else None
    from ..core import steel
    if kind in ("column", "beam") and steel.is_steel_profile(profile):      # (0.494) a steel section
        from ifcopenshell.util import unit as ifc_unit
        angle = ifc_unit.calculate_unit_scale(ifc.file, "PLANEANGLEUNIT") or 1.0
        sec = steel.from_ifc(profile, ifc.unit_scale, angle)
        if sec is not None:
            w, h = steel.size(sec)
            return catalog.TypeSpec(key, kind, name, name, profile=(w / 1000.0, h / 1000.0), material=material,
                                    predefined=predefined, shape="steel", section=sec.name)
    if profile.is_a("IfcCircleProfileDef"):
        size = (2 * float(profile.Radius) * s,) * 2
        shape = None if kind in ("pipe", "pile") else "circle"
    elif profile.is_a("IfcRectangleProfileDef"):
        size = (float(profile.XDim) * s, float(profile.YDim) * s)
    elif profile.is_a("IfcLShapeProfileDef"):                     # (0.97)
        size = (float(profile.Width or profile.Depth) * s, float(profile.Depth) * s)
        shape, web = "L", float(profile.Thickness) * s
    elif profile.is_a("IfcTShapeProfileDef"):
        size = (float(profile.FlangeWidth) * s, float(profile.Depth) * s)
        shape, web = "T", float(profile.WebThickness) * s
    else:
        return None
    material = material_key(entry.Material.Name) if entry.Material else None
    return catalog.TypeSpec(key, kind, name, name, profile=size, material=material, predefined=predefined,
                            shape=shape, web=web)


def _hand_variant(name):
    """A door type made for doors hinged on the right ("… (à direita)") — (0.289) or a window type's mirror image ("…
    (espelhada)"): it follows its own type."""
    return any(name.endswith(suffix) for suffix in VARIANTS)


def read_opening(ifc, type_, kind):
    """An OpeningSpec of an IfcDoorType / IfcWindowType: its sizes from its ArqSynth_Parametros (a type made
    in the type editor), else the catalogue entry of its name; None for the others."""
    name = type_.Name or ""
    if _hand_variant(name):
        return None
    key = next((o.key for o in catalog._STARTER_OPENINGS.values() if o.kind == kind and name in (o.name_pt, o.name_en)),
               None) or "t:" + type_.GlobalId
    params = ifcopenshell.util.element.get_psets(type_).get(PARAM_PSET, {})
    operation = (type_.OperationType if kind == "door" else type_.PartitioningType) or ""
    design = None
    if params.get("Desenho"):                       # (0.288) its joinery, as the generator made it
        try:
            design = joinery.from_json(params["Desenho"])
        except ValueError:
            design = None
    if "Largura" in params:
        lining = float(params.get("Aro") or 0.0)
        return catalog.OpeningSpec(key, kind, name, name, float(params["Largura"]), float(params["Altura"]),
                                   float(params.get("Peitoril") or 0.0), operation, lining or None,
                                   float(params.get("Bandeira") or 0.0), design)
    return catalog._STARTER_OPENINGS.get(key)


def read_openings(ifc):
    """The project's door and window types that differ from the catalogue, or are not in it."""
    out = []
    for kind in ("door", "window"):
        for type_ in ifc.file.by_type(CLASSES[kind]):
            spec = read_opening(ifc, type_, kind)
            if spec is None:
                continue
            start = catalog._STARTER_OPENINGS.get(spec.key)
            if start is not None and (round(spec.width, 6), round(spec.height, 6), round(spec.sill, 6)) == \
                    (round(start.width, 6), round(start.height, 6), round(start.sill, 6)) and \
                    (spec.design is None or spec.design == start.design):          # (0.288: its design too)
                continue
            out.append(spec)
    return out


def read(ifc):
    """The project's types: [TypeSpec] — those that differ from the catalogue, or are not in it."""
    out = []
    for kind, ifc_class in CLASSES.items():
        if kind in ("door", "window"):
            continue
        for type_ in ifc.file.by_type(ifc_class):
            spec = read_type(ifc, type_, kind)
            if spec is None:
                continue
            start = catalog._STARTER.get(spec.key)
            if start is not None and _same(spec, start):
                continue                                  # (the catalogue's, as it is: kept in both languages)
            out.append(spec)
    return out


def find_type(ifc, spec, lang="pt"):
    """The IFC type of an entry in the project (by its key's GlobalId, else by its name), or None."""
    if spec.key.startswith("t:"):
        found = ifc.by_guid(spec.key[2:])
        if found is not None:
            return found
    names = {spec.name_pt, spec.name_en}
    return next((t for t in ifc.file.by_type(CLASSES[spec.kind]) if t.Name in names), None)


def hand_variants(ifc, type_):
    """The door types made from this one for doors hinged on the right ("… (à direita)") — (0.289) the window types
    made from it as its mirror image ("… (espelhada)")."""
    if not type_.is_a("IfcDoorType") and not type_.is_a("IfcWindowType"):
        return []
    names = {(type_.Name or "") + suffix for suffix in VARIANTS}
    return [t for t in ifc.file.by_type(type_.is_a()) if t.Name in names]


def instances(ifc, spec, lang="pt"):
    """GlobalIds of the project's elements of this type (a door type: hinged on either side)."""
    type_ = find_type(ifc, spec, lang)
    if type_ is None:
        return []
    return [e.GlobalId for t in [type_] + hand_variants(ifc, type_) for e in ifcopenshell.util.element.get_types(t)]
