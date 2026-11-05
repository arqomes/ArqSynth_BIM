"""(0.393) ArqSynth BIM's templates («Arquivo Modelo», arqsynth_templates): its factory template «ArqSynth Padrão»
made from what the program starts a project with — so that a project begun from it is as one begun before there were
templates —, and the manager it uses (program «arqsynth-bim», the suite's shared folder).

The factory template, section by section (the format: arqsynth_templates/schema.json):
  units        the lengths' unit (m), 2 decimals, the comma
  project      the IFC's names (Projeto, Terreno, Edifício), IFC4 in millimetres
  storeys      Térreo at 0,00 m, 3,00 m high
  materials    the catalogue's (colour, category, density, conductivity, transparency, finish, patterns)
  types        the catalogue's walls, slabs, roofs, columns, beams, footings, piles, pipes, ducts — by layers or
               section — and doors and windows with their joinery design
  ifc_classes  the class each kind of element is made as
  annotation, dimensions, lines, sheets   the drawings' (texts 2,5 mm; the dimension style; the pens, hatches and
               symbols; A3, the full title block)
  interface    the light theme, the start page, the 3D view
  extensions.arqsynth-bim   what only this program uses (the structural grid's settings)"""

import json

from arqsynth_templates import FACTORY_ID, FACTORY_NAME, SCHEMA_VERSION, TemplateManager

PROGRAM = "arqsynth-bim"
TYPE_CLASSES = {"wall": "IfcWallType", "slab": "IfcSlabType", "roof": "IfcRoofType", "column": "IfcColumnType",
                "beam": "IfcBeamType", "footing": "IfcFootingType", "pile": "IfcPileType",
                "pipe": "IfcPipeSegmentType", "duct": "IfcDuctSegmentType", "conduit": "IfcCableCarrierSegmentType",
                "door": "IfcDoorType", "window": "IfcWindowType"}
IFC_CLASSES = {"wall": "IfcWall", "slab": "IfcSlab", "roof": "IfcRoof", "column": "IfcColumn", "beam": "IfcBeam",
               "footing": "IfcFooting", "pile": "IfcPile", "door": "IfcDoor", "window": "IfcWindow",
               "stair": "IfcStair", "ramp": "IfcRamp", "railing": "IfcRailing", "curtain_wall": "IfcCurtainWall",
               "ceiling": "IfcCovering", "cladding": "IfcCovering", "flooring": "IfcCovering", "room": "IfcSpace",
               "furniture": "IfcFurniture", "pipe": "IfcPipeSegment", "duct": "IfcDuctSegment",
               "conduit": "IfcCableCarrierSegment", "light": "IfcLightFixture", "terrain": "IfcGeographicElement"}


def _hex(rgb):
    r, g, b = (min(max(float(c), 0.0), 1.0) for c in tuple(rgb)[:3])
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def _number(v):
    return None if v is None else round(float(v), 6)


def material(spec):
    """A catalogue material (ifc/catalog.MaterialSpec) as a template's."""
    graphics = {k: (list(v) if v else None) for k, v in (("surface_fg", spec.surface_fg),
                                                          ("surface_bg", spec.surface_bg),
                                                          ("cut_fg", spec.cut_fg), ("cut_bg", spec.cut_bg))}
    return {"key": spec.key, "name": spec.name_pt, "name_en": spec.name_en, "category": spec.category or "",
            "color": _hex(spec.color), "transparency": float(spec.transparency or 0.0), "finish": spec.finish or "",
            "texture": None,
            "thermal": {"conductivity": _number(spec.conductivity), "density": _number(spec.density),
                        "specific_heat": None},
            "acoustic": {"absorption": None, "sound_reduction": None},
            "graphics": graphics}


def construction_type(spec):
    """A catalogue type (ifc/catalog.TypeSpec) as a template's: its layers or its section."""
    from ..ifc import catalog
    out = {"key": spec.key, "name": spec.name_pt, "name_en": spec.name_en,
           "ifc_class": TYPE_CLASSES.get(spec.kind, "")}
    if spec.layers:
        out["layers"] = [{"material": m, "thickness": round(float(t), 6), "function": catalog.layer_function(spec, k)}
                         for k, (m, t) in enumerate(spec.layers)]
    if spec.profile:
        out["profile"] = [_number(v) for v in spec.profile]
    for key in ("material", "predefined", "shape", "web"):
        value = getattr(spec, key)
        if value:
            out[key] = value
    if spec.piles:
        out.update(piles=int(spec.piles), pile=spec.pile, pile_length=float(spec.pile_length))
    if spec.masonry:
        out["masonry"] = list(spec.masonry)
    return out


def opening_type(spec):
    """A catalogue door / window (ifc/catalog.OpeningSpec) as a template's: its sizes and its joinery design."""
    from ..core import joinery
    from ..ifc import catalog
    return {"key": spec.key, "name": spec.name_pt, "name_en": spec.name_en,
            "ifc_class": TYPE_CLASSES[spec.kind], "width": float(spec.width), "height": float(spec.height),
            "sill": float(spec.sill or 0.0), "operation": spec.operation or "", "transom": float(spec.transom or 0.0),
            "lining_depth": _number(spec.lining_depth),
            "design": json.loads(joinery.to_json(catalog.design_of(spec)))}


def factory():
    """«ArqSynth Padrão»: what ArqSynth BIM starts a project with, as a template."""
    from .. import __version__
    from ..ifc import catalog
    from . import dimensions, graphic_styles, sheets
    from .annotations import TEXT_SIZE
    from .document import GRID_DEFAULTS
    types = {}
    for spec in catalog.TYPES:
        types.setdefault(spec.kind, []).append(construction_type(spec))
    for spec in catalog.OPENINGS:
        types.setdefault(spec.kind, []).append(opening_type(spec))
    return {
        "format": "arqsynth-template", "schema_version": SCHEMA_VERSION, "id": FACTORY_ID, "name": FACTORY_NAME,
        "version": 1,
        "description": "O modelo de fábrica do ArqSynth BIM: o que um projeto novo tem quando não se escolhe outro.",
        "author": "ArqSynth", "created": "2026-11-04T00:00:00Z", "modified": "2026-11-04T00:00:00Z",
        "programs": [PROGRAM], "generator": {"program": PROGRAM, "version": __version__},
        "units": {"system": "metric", "length": "m", "decimals": 2, "area_decimals": 2, "angle": "degree",
                  "angle_decimals": 1, "decimal_separator": ","},
        "project": {"name": "Projeto", "site": "Terreno", "building": "Edifício", "author": "", "organization": "",
                    "address": "", "ifc_schema": "IFC4", "ifc_length_unit": "MILLIMETRE"},
        "storeys": [{"name": "Térreo", "elevation": 0.0, "height": 3.0}],
        "materials": [material(m) for m in catalog.starter_materials()],
        "types": types,
        "ifc_classes": dict(IFC_CLASSES),
        "annotation": {"text_height": float(TEXT_SIZE), "font": ""},
        "dimensions": dict(dimensions.STYLE_DEFAULTS),
        "lines": graphic_styles.defaults(),
        "sheets": {"paper": "A3", "title_block": "full", "title_fields": {k: "" for k in sheets.TITLE_FIELDS}},
        "interface": {"theme": "light", "palette": "", "start_page": True, "start_view": "3d", "shortcuts": {}},
        "extensions": {PROGRAM: {"grid": dict(GRID_DEFAULTS)}},
    }


def manager(root=None):
    """The templates' manager of ArqSynth BIM (the suite's folder; `root` another, for tests)."""
    from .. import __version__
    from ..i18n import lang
    return TemplateManager(PROGRAM, factory(), root=root, lang=lang(), program_version=__version__)
