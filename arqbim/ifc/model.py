"""The IFC side of the project. This is the ONLY module that imports IfcOpenShell.

Keeping every IFC call here (a thin, isolated data layer) makes the rest of the
program independent from the schema version, which eases a future move to IFC5.

The model lives in memory as an ifcopenshell.file. Every change runs inside
one IfcOpenShell transaction, so file.undo()/redo() stay in step with the
program's own undo stack.
"""

import contextlib
import importlib
import logging
import math
import os
import re
import time

import numpy as np

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.representation
import ifcopenshell.util.unit

import ifcopenshell.util.placement

for _m in ("project", "root", "unit", "context", "aggregate", "spatial", "type", "material",
           "profile", "geometry", "pset", "style", "feature", "grid"):
    importlib.import_module("ifcopenshell.api." + _m)
api = ifcopenshell.api

from ..core import classify  # noqa: E402
from ..core import roof_tiles as core_tiles  # noqa: E402
from ..core.mesh import planar_union  # noqa: E402
from . import catalog  # noqa: E402
from .edit import LEGACY_PARAM_PSET, PARAM_PSET, EditMixin, profile_size  # noqa: E402
from .groups import GroupMixin  # noqa: E402
from .typical import TypicalMixin  # noqa: E402
from .spaces import SpaceMixin  # noqa: E402
from .slabs import SlabMixin  # noqa: E402
from .ramps import RampMixin  # noqa: E402
from .curved_walls import CurvedWallMixin  # noqa: E402
from .wall_edit import WallEditMixin  # noqa: E402
from .mirror import MirrorMixin  # noqa: E402
from .roofs import RoofMixin  # noqa: E402
from .stairs import StairMixin  # noqa: E402
from .railings import RailingMixin  # noqa: E402
from .curtain_walls import CurtainWallMixin  # noqa: E402
from .coverings import CoveringMixin  # noqa: E402
from .architecture import ArchitectureMixin  # noqa: E402
from .organic_roofs import OrganicRoofMixin  # noqa: E402
from .param_surfaces import ParamSurfaceMixin  # noqa: E402
from .element_types import ElementTypeMixin  # noqa: E402
from .services import ServicesMixin  # noqa: E402
from .terminals import TerminalMixin  # noqa: E402
from .equipment import EquipmentMixin  # noqa: E402
from .sanitary import SanitaryMixin  # noqa: E402
from .systems import SystemMixin  # noqa: E402
from .branches import BranchMixin  # noqa: E402
from .electrical import ElectricalMixin  # noqa: E402
from .circuits import CircuitMixin  # noqa: E402
from .conduits import ConduitMixin  # noqa: E402
from .terrain import TerrainMixin  # noqa: E402
from .structural import StructuralMixin  # noqa: E402
from .rebar import RebarMixin  # noqa: E402
from .cabinets import CabinetMixin  # noqa: E402
from .appliances import ApplianceMixin  # noqa: E402
from .profiles import ProfileMixin  # noqa: E402
from .keynotes import KeynoteMixin  # noqa: E402
from .ifc_data import IfcDataMixin  # noqa: E402
from .carpentry import CarpentryMixin  # noqa: E402
from .roof_tiles import RoofTilesMixin  # noqa: E402
from .joinery import JoineryMixin  # noqa: E402
from .dwellings import DwellingMixin  # noqa: E402
from .lot import LotMixin  # noqa: E402
from .wall_framing import WallFramingMixin  # noqa: E402
from .loose_furniture import LooseFurnitureMixin  # noqa: E402
from .tiled_coverings import TiledCoveringMixin  # noqa: E402  (0.563)
from .ripado_screen import RipadoScreenMixin  # noqa: E402
from .steel_members import SteelMemberMixin  # noqa: E402
from .steel_connections import SteelConnectionMixin  # noqa: E402
from .steel_stairs import SteelStairMixin  # noqa: E402
from .structure_cuts import StructureCutMixin  # noqa: E402

HISTORY_SIZE = 100000          # keep IFC undo history as long as the program's
FEW_ELEMENTS = 12              # up to this many, triangulate one by one (no thread pool to start)
_VOID_NAME = {"pt": "vão", "en": "opening"}
_PILE_NAME = {"pt": "estaca", "en": "pile"}


def pile_spots(count, length, width, diameter):
    """Where a pile cap's piles go (0.94), from its middle along its own x / y: one in the middle; two along
    its length; three in a triangle; four at the corners — each pile's axis half a diameter and 15 cm in from
    the cap's sides."""
    ex = max(length / 2 - diameter / 2 - 0.15, 0.0)
    ey = max(width / 2 - diameter / 2 - 0.15, 0.0)
    if count <= 1:
        return [(0.0, 0.0)]
    if count == 2:
        return [(-ex, 0.0), (ex, 0.0)]
    if count == 3:
        return [(-ex, -ey), (ex, -ey), (0.0, ey)]
    return [(-ex, -ey), (ex, -ey), (ex, ey), (-ex, ey)]


def _unit3(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / n, v[1] / n, v[2] / n)


def _axis2placement(p):
    """(0.225) An IfcAxis2Placement3D / 2D as a 4 × 4 matrix — ifcopenshell.util.placement's a2p (x and z made unit,
    y = z × x) in plain arithmetic: numpy's cross and norm cost more than the sums on three numbers. None for
    what it does not read (IfcOpenShell then does)."""
    if p.is_a("IfcAxis2Placement3D"):
        loc = getattr(p.Location, "Coordinates", None)
        if loc is None:
            return None
        z = tuple(p.Axis.DirectionRatios) if p.Axis else (0.0, 0.0, 1.0)
        x = tuple(p.RefDirection.DirectionRatios) if p.RefDirection else (1.0, 0.0, 0.0)
        o = tuple(loc)
    elif p.is_a("IfcAxis2Placement2D"):
        z = (0.0, 0.0, 1.0)
        x = (tuple(p.RefDirection.DirectionRatios)[:2] + (0.0,)) if p.RefDirection else (1.0, 0.0, 0.0)
        o = tuple(p.Location.Coordinates)[:2] + (0.0,)
    else:
        return None
    x, z = _unit3(x), _unit3(z)
    y = _unit3((z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0]))
    return np.array(((x[0], y[0], z[0], o[0]), (x[1], y[1], z[1], o[1]), (x[2], y[2], z[2], o[2]),
                     (0.0, 0.0, 0.0, 1.0)), dtype=float)


def _quantities(element, name):
    """(0.225) {quantity: value} of an element's own quantity set `name`, read straight from it (get_psets makes
    them all), or None when it has none."""
    for rel in getattr(element, "IsDefinedBy", None) or ():
        if rel.is_a("IfcRelDefinesByProperties"):
            qto = rel.RelatingPropertyDefinition
            if qto.is_a("IfcElementQuantity") and qto.Name == name:
                return {q.Name: q[3] for q in qto.Quantities or () if q.is_a("IfcPhysicalSimpleQuantity")}
    return None


COMPONENT_CLASSES = {                   # category -> (instance class, type class)
    "furniture": ("IfcFurniture", "IfcFurnitureType"),
    "sanitary": ("IfcSanitaryTerminal", "IfcSanitaryTerminalType"),
    "generic": ("IfcBuildingElementProxy", "IfcBuildingElementProxyType"),
}
_COPY_PREFIX = {"wall": ("Parede", "Wall"), "slab": ("Laje", "Slab"), "column": ("Pilar", "Column"),
                "beam": ("Viga", "Beam"), "footing": ("Sapata", "Footing"), "pipe": ("Tubo", "Pipe"),
                "conduit": ("Tubo VD", "Conduit"),
                "duct": ("Conduta", "Duct"), "ramp": ("Rampa", "Ramp"), "curved_wall": ("Parede", "Wall"),
                "roof": ("Cobertura", "Roof"), "stair": ("Escada", "Stair"), "railing": ("Guarda", "Railing"),
                "curtain_wall": ("Fachada", "Curtain wall"), "ceiling": ("Teto", "Ceiling"),
                "cladding": ("Revestimento", "Wall finish"), "light": ("Luminária", "Light"),
                "profile": ("Perfil", "Profile"),
                "door": ("Porta", "Door"), "window": ("Janela", "Window")}
TAG = "ArqSynth BIM"           # ApplicationIdentifier-like marker for our own types
MARK_PREFIX = {"door": "P", "window": "J"}      # (0.110) the marks of doors and windows (IfcElement.Tag)


def rename_legacy(f):
    """A file made before 0.77 (when the program was ArqBIM): its parameters' property set takes the new name
    (in memory: the file on disk changes when it is saved). Returns the file."""
    for pset in f.by_type("IfcPropertySet"):
        if pset.Name == LEGACY_PARAM_PSET:
            pset.Name = PARAM_PSET
    return f
DISPLAY_EXCLUDE = ("IfcOpeningElement", "IfcSpace", "IfcVirtualElement", "IfcAnnotation", "IfcGrid")
FAR_FROM_ORIGIN = 1000.0       # m; beyond this a model is brought near the origin for the program (see origin)
SYMBOL_TYPES = ("Curve2D", "GeometricCurveSet", "GeometricSet", "Annotation2D")   # plan symbols: 2D lines
HATCH_WORDS = (                # what a material is drawn with when cut, from its category, else its name
    ("masonry", ("masonry", "brick", "block", "stone", "clay", "alvenaria", "tijolo", "bloco", "pedra",
                 "cerâmic", "ceramic")),             # (first: a concrete block is masonry)
    ("concrete", ("concrete", "betão", "betao", "concreto", "cimento", "cement")),
    ("wood", ("wood", "timber", "madeira")),
    ("insulation", ("insulation", "isolamento", "wool", "lã", "xps", "eps")),
    ("gypsum", ("gypsum", "plaster", "gesso", "reboco", "estuque")),
    ("earth", ("earth", "soil", "solo", "terreno")),       # (the terrain, 0.155)
)


def _occurrence_class(type_):
    """The class of an instance of a component type (IfcFurnitureType -> IfcFurniture), or None
    when it is not placed on its own (doors and windows go in walls)."""
    for o, t in COMPONENT_CLASSES.values():
        if type_.is_a() == t:
            return o
    import ifcopenshell.util.type
    schema = type_.is_a(True).split(".")[0]                       # ("IFC4.IfcFurnitureType")
    for cls in ifcopenshell.util.type.get_applicable_entities(type_.is_a(), schema) or ():
        if cls in ("IfcDoor", "IfcWindow") or cls.endswith("StandardCase"):
            continue
        return cls
    return None


STATUSES = ("EXISTING", "NEW", "DEMOLISH", "TEMPORARY")     # PEnum_ElementStatus, the ones that mean a phase
_STATUS_PSETS = {}


def _status(value):
    """A Status as read (a list for an enumerated value, a label…) -> one of STATUSES or None."""
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
    value = str(value).strip().upper() if value is not None else None
    return value if value in STATUSES else None


def _status_pset(ifc_class):
    """The Pset_…Common of a class that has a Status (Pset_WallCommon…), from IFC4's templates."""
    if ifc_class not in _STATUS_PSETS:
        import ifcopenshell.util.pset
        templates = ifcopenshell.util.pset.PsetQto("IFC4")
        found = None
        for name in templates.get_applicable_names(ifc_class, pset_only=True):
            template = templates.get_by_name(name)
            if name.endswith("Common") and any(p.Name == "Status" for p in template.HasPropertyTemplates or ()):
                found = name
                break
        _STATUS_PSETS[ifc_class] = found
    return _STATUS_PSETS[ifc_class]


def _own_psets(e):
    """The property sets defined on the element itself (not inherited from its type)."""
    return [rel.RelatingPropertyDefinition for rel in getattr(e, "IsDefinedBy", None) or ()
            if rel.is_a("IfcRelDefinesByProperties")]


def _main_material(e):
    """An element's main material (of layers, the thickest; of profiles or parts, the first), or None."""
    material = ifcopenshell.util.element.get_material(e, should_skip_usage=True) if e is not None else None
    if material is None:
        return None
    if material.is_a("IfcMaterialLayerSet"):
        layers = [l for l in material.MaterialLayers if l.Material is not None]
        return max(layers, key=lambda l: l.LayerThickness or 0).Material if layers else None
    if material.is_a("IfcMaterialProfileSet"):
        return next((p.Material for p in material.MaterialProfiles if p.Material is not None), None)
    if material.is_a("IfcMaterialConstituentSet"):
        return next((c.Material for c in material.MaterialConstituents or () if c.Material is not None), None)
    if material.is_a("IfcMaterialList"):
        return next(iter(material.Materials or ()), None)
    return material if material.is_a("IfcMaterial") else None


def _hatch_of(material):
    """A material's hatch (see HATCH_WORDS): its IFC category says it, else words in its name."""
    if material is None:
        return None
    for text in (getattr(material, "Category", None), material.Name):
        text = (text or "").lower()
        for hatch, words in HATCH_WORDS:
            if any(w in text for w in words):
                return hatch
    return None


MATERIAL_CUT = "mat:"          # (0.314) a cut drawn with its material's own patterns: "mat:" + the IfcMaterial's name


def _own_cut(material):
    """(0.314) The cut patterns of a material's own — (background, foreground), each (pattern, colour) or None — or
    None when it is cut with its category's (the project's graphic style)."""
    from . import material_graphics
    found = material_graphics.read_patterns(material) or material_graphics.read_foreign(material)
    if found is None:                                  # (a catalogue material as it is: the catalogue's)
        start = next((m for m in catalog._STARTER_MATERIALS.values() if material.Name in (m.name_pt, m.name_en)), None)
        found = {"cut_fg": start.cut_fg, "cut_bg": start.cut_bg} if start is not None else {}
    bg, fg = found.get("cut_bg"), found.get("cut_fg")
    return (bg, fg) if bg is not None or fg is not None else None


def _cut_key(material, known):
    """(0.314) What a material is drawn with where cut: MATERIAL_CUT + its name when it has patterns of its own, else
    its hatch (_hatch_of). known: {material id: key}, filled (a drawing asks for each material once)."""
    if material is None:
        return None
    key = known.get(material.id())
    if key is None:
        key = known[material.id()] = MATERIAL_CUT + (material.Name or "") if _own_cut(material) is not None \
            else (_hatch_of(material) or "")
    return key or None
CHUNK_FIRST, CHUNK_MAX = 0.3, 2.0   # s; shapes handed over while a file opens: the first soon, then less often
# (0.259) the elements shown in their parts' own colours (each piece styled with its material: a railing's wooden
# rail, steel posts, glass); the others in their class's colour, as before
COLOURED = ("IfcRailing", "IfcMember",      # (0.276: the carpentry's pieces, in their wood)
            "IfcDoor", "IfcWindow")         # (0.288: their frame, leaves and glass)
UNSTYLED = (0.70, 0.71, 0.72)       # a piece with no colour of its own
# (0.351) the components' classes: in their pieces' colours when these are styled (a 3D file's), else their category's
COMPONENT_OCCURRENCES = ("IfcFurniture", "IfcSanitaryTerminal", "IfcBuildingElementProxy")
# (0.395) the classes a parametric surface may be (by what it is used for): in its pieces' colours
SURFACE_CLASSES = ("IfcBuildingElementProxy", "IfcRoof", "IfcCurtainWall", "IfcShadingDevice")


def _item_colour(item):
    """(0.288) The surface colour (RGB 0..1) of a representation item's own style, or None."""
    for styled in getattr(item, "StyledByItem", None) or ():
        for style in styled.Styles or ():
            for s in getattr(style, "Styles", None) or ():
                colour = getattr(s, "SurfaceColour", None)
                if colour is not None:
                    return float(colour.Red), float(colour.Green), float(colour.Blue)
    return None


def _base_axes(axis1, axis2, axis3):
    """(0.279) The axes (rows x, y, z) of an IfcCartesianTransformationOperator3D, as IFC's IfcBaseAxis makes them:
    z its Axis3 (else up), x its Axis1 square to z (else east), y its Axis2 square to both (else z × x)."""
    def ratios(d, default):
        return np.array(d.DirectionRatios, dtype=float) if d is not None else np.array(default, dtype=float)
    z = ratios(axis3, (0.0, 0.0, 1.0))
    z /= np.linalg.norm(z)
    x = ratios(axis1, (1.0, 0.0, 0.0) if abs(z[0]) < 0.9 else (0.0, 1.0, 0.0))
    x -= (x @ z) * z
    x /= np.linalg.norm(x)
    y = ratios(axis2, np.cross(z, x))
    y -= (y @ z) * z + (y @ x) * x
    y /= np.linalg.norm(y)
    return np.vstack((x, y, z))


def _material_colour(element):
    """(0.276) The surface colour (RGB 0..1) of an element's material's style (a single material), or None."""
    material = ifcopenshell.util.element.get_material(element, should_skip_usage=True)
    if material is None or not material.is_a("IfcMaterial"):
        return None
    for rep in material.HasRepresentation or ():
        for representation in rep.Representations or ():
            for item in representation.Items or ():
                for style in item.Styles or ():
                    for s in getattr(style, "Styles", None) or ():
                        colour = getattr(s, "SurfaceColour", None)
                        if colour is not None:
                            return float(colour.Red), float(colour.Green), float(colour.Blue)
    return None


def _triangle_colours(geometry, n):
    """Each triangle's colour (n, 3), sRGB 0–1, from the kernel's materials of a shape (its pieces' styles)."""
    try:
        palette = [tuple(m.diffuse.components) if m.diffuse is not None else UNSTYLED for m in geometry.materials]
        ids = np.asarray(geometry.material_ids, dtype=np.int64)
    except (AttributeError, TypeError):
        return None
    if not palette or len(ids) != n:
        return None
    table = np.array(palette + [UNSTYLED], dtype=np.float32)
    return table[np.where((ids >= 0) & (ids < len(palette)), ids, len(palette))]


def type_shape(type_, unit_scale):
    """(0.466) A type's shape kept once (its first RepresentationMap) in its own frame, metres: (triangles' corners
    (T, 3, 3), their sRGB (T, 3) — its pieces' colours, grey where they have none). Of any file (a library's too)."""
    shape_map = type_.RepresentationMaps[0]
    settings = ifcopenshell.geom.settings()
    shape = ifcopenshell.geom.create_shape(settings, shape_map.MappedRepresentation)
    geometry = getattr(shape, "geometry", shape)
    verts = np.array(geometry.verts, dtype=float).reshape(-1, 3)
    faces = np.array(geometry.faces, dtype=np.int64).reshape(-1, 3)
    if not len(verts) or not len(faces):
        return np.zeros((0, 3, 3)), np.zeros((0, 3))
    origin = ifcopenshell.util.placement.get_axis2placement(shape_map.MappingOrigin)
    origin[:3, 3] *= unit_scale
    verts = verts @ origin[:3, :3].T + origin[:3, 3]
    colours = _triangle_colours(geometry, len(faces))
    if colours is None:
        colours = np.tile(np.array(UNSTYLED[:3], dtype=float), (len(faces), 1))
    return verts[faces], np.asarray(colours, dtype=float)[:, :3]


class Cancelled(Exception):
    """The user stopped a long operation (opening a file)."""


def _translation(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def _rot_z_180():
    return np.diag((-1.0, -1.0, 1.0, 1.0))


class IfcModel(EditMixin, GroupMixin, ServicesMixin, TypicalMixin, SpaceMixin, SlabMixin, RampMixin,
               CurvedWallMixin, WallEditMixin, MirrorMixin, RoofMixin, StairMixin, RailingMixin, CurtainWallMixin,
               CoveringMixin, TerminalMixin, EquipmentMixin, SanitaryMixin, SystemMixin, BranchMixin,
               ElectricalMixin, CircuitMixin, ConduitMixin, TerrainMixin, StructuralMixin, RebarMixin,
               CabinetMixin, ApplianceMixin, ProfileMixin, KeynoteMixin, IfcDataMixin, CarpentryMixin,
               RoofTilesMixin, JoineryMixin, ArchitectureMixin, OrganicRoofMixin, ParamSurfaceMixin,
               ElementTypeMixin, DwellingMixin, LotMixin, WallFramingMixin,
               LooseFurnitureMixin, RipadoScreenMixin, SteelMemberMixin, SteelConnectionMixin, SteelStairMixin, StructureCutMixin,
               TiledCoveringMixin):
    def __init__(self, file):
        self.file = file
        self.file.set_history_size(HISTORY_SIZE)
        self.path = None
        self.copy_map = {}          # original GlobalId -> copy GlobalId, filled by the copy methods
        # Where the program's (0, 0, 0) is in the IFC's coordinates (m): the rest of the
        # program works near the origin (see _display_origin); the IFC keeps its own.
        self.origin = np.zeros(3)
        self._setup_contexts()

    # ------------------------------------------------------------ create / open / save

    @classmethod
    def new(cls, name="Projeto", lang="pt"):
        f = api.project.create_file(version="IFC4")
        project = api.root.create_entity(f, ifc_class="IfcProject", name=name)
        units = [api.unit.add_si_unit(f, unit_type="LENGTHUNIT", prefix="MILLI"),
                 api.unit.add_si_unit(f, unit_type="AREAUNIT"),
                 api.unit.add_si_unit(f, unit_type="VOLUMEUNIT"),
                 api.unit.add_si_unit(f, unit_type="PLANEANGLEUNIT")]     # (radians; 0.70: certification)
        api.unit.assign_unit(f, units=units)
        model = cls(f)
        names = ("Terreno", "Edifício", "Térreo") if lang == "pt" else ("Site", "Building", "Ground floor")
        site = api.root.create_entity(f, ifc_class="IfcSite", name=names[0])
        building = api.root.create_entity(f, ifc_class="IfcBuilding", name=names[1])
        storey = api.root.create_entity(f, ifc_class="IfcBuildingStorey", name=names[2])
        api.aggregate.assign_object(f, products=[site], relating_object=project)
        api.aggregate.assign_object(f, products=[building], relating_object=site)
        api.aggregate.assign_object(f, products=[storey], relating_object=building)
        for e in (site, building, storey):
            api.geometry.edit_object_placement(f, product=e)
        storey.Elevation = 0.0
        return model

    @classmethod
    def open(cls, path):
        model = cls(rename_legacy(ifcopenshell.open(path)))
        model.path = path
        model.origin = model._display_origin()
        return model

    def _display_origin(self):
        """The program's origin for a model placed far from the IFC's (0, 0) — georeferenced,
        e.g. Revit's shared coordinates, hundreds of km away: the building's position (else the
        site's, else the elements'), rounded to the metre, in plan only. The GPU works in 32-bit
        numbers, which at 500 km are ~3 cm apart: edges would shake. (0, 0, 0) when near."""
        s = self.unit_scale

        def world(e):
            if e.ObjectPlacement is None or not e.ObjectPlacement.is_a("IfcLocalPlacement"):
                return None
            return ifcopenshell.util.placement.get_local_placement(e.ObjectPlacement)[:3, 3] * s

        def far(p):
            return p is not None and max(abs(p[0]), abs(p[1])) > FAR_FROM_ORIGIN

        for cls in ("IfcBuilding", "IfcSite"):
            for e in self.file.by_type(cls):
                p = world(e)
                if far(p):
                    return np.array((round(p[0]), round(p[1]), 0.0))
        points = [p for p in (world(e) for e in self.file.by_type("IfcElement")[:200]) if p is not None]
        if points:
            p = np.median(points, axis=0)
            if far(p):
                return np.array((round(p[0]), round(p[1]), 0.0))
        return np.zeros(3)

    def save(self, path):
        from .certify import stamp_header
        stamp_header(self, path)                   # (the program and the file's name in its header: 0.70)
        self.file.write(path)
        self.path = path

    def validate(self, express_rules=False):
        """Schema validation with IfcOpenShell. Returns a list of error messages (empty = valid).
        express_rules=True also checks the schema's WHERE rules (slower; needs pytest)."""
        import ifcopenshell.validate
        errors = []

        class _Collect(logging.Handler):
            def emit(self, record):
                errors.append(record.getMessage())

        log = logging.getLogger("arqbim.ifc.validate")
        log.propagate = False
        handler = _Collect()
        log.addHandler(handler)
        try:
            ifcopenshell.validate.validate(self.file, log, express_rules=express_rules)
        finally:
            log.removeHandler(handler)
        return errors

    # ------------------------------------------------------------ transactions

    def begin(self):
        self.file.begin_transaction()
        self.created = []             # (the elements made in it: typical floors copy them, 0.90)
        self.made = []                # (all made in it, the copies too, and the storeys things went from: the
        self.removed_storeys = set()  #  rooms there are found again, 0.99)

    def end(self):
        self.file.end_transaction()
        self.created = self.made = self.removed_storeys = None

    def discard(self):
        self.file.discard_transaction()
        self.created = self.made = self.removed_storeys = None

    def touched_storeys(self, changed=()):
        """The storeys where this transaction changed, made or removed something (0.99)."""
        out = set(self.removed_storeys or ())
        for g in list(changed) + list(self.made or ()):
            if self.by_guid(g) is not None:
                storey = self.storey_of(g)
                if storey:
                    out.add(storey)
        return out

    def undo(self):
        self.file.undo()

    def redo(self):
        self.file.redo()

    # ------------------------------------------------------------ structure

    def _setup_contexts(self):
        get = ifcopenshell.util.representation.get_context
        f = self.file
        self.body = get(f, "Model", "Body", "MODEL_VIEW")
        self.axis = get(f, "Model", "Axis", "GRAPH_VIEW")
        if self.body is None or self.axis is None:
            model = get(f, "Model") or api.context.add_context(f, context_type="Model")
            if self.body is None:
                self.body = api.context.add_context(f, context_type="Model", context_identifier="Body",
                                                    target_view="MODEL_VIEW", parent=model)
            if self.axis is None:
                self.axis = api.context.add_context(f, context_type="Model", context_identifier="Axis",
                                                    target_view="GRAPH_VIEW", parent=model)

    def plan_context(self):
        """Plan / Body / PLAN_VIEW: where doors keep their plan symbol (made the first time one is)."""
        get = ifcopenshell.util.representation.get_context
        context = get(self.file, "Plan", "Body", "PLAN_VIEW")
        if context is None:
            plan = get(self.file, "Plan") or api.context.add_context(self.file, context_type="Plan")
            context = api.context.add_context(self.file, context_type="Plan", context_identifier="Body",
                                              target_view="PLAN_VIEW", parent=plan)
        return context

    def elevation_context(self):
        """(0.292) Model / Annotation / ELEVATION_VIEW: where doors and windows keep the signs of how they open, seen in
        elevations and sections (made the first time one is)."""
        get = ifcopenshell.util.representation.get_context
        context = get(self.file, "Model", "Annotation", "ELEVATION_VIEW")
        if context is None:
            model = get(self.file, "Model") or api.context.add_context(self.file, context_type="Model")
            context = api.context.add_context(self.file, context_type="Model", context_identifier="Annotation",
                                              target_view="ELEVATION_VIEW", parent=model)
        return context

    def elevation_signs(self, guids):
        """(0.292) {GlobalId: (K, 2, 3) segments} of the doors' and windows' opening signs (their Curve3D in the
        ELEVATION_VIEW context: on both faces of their leaves), in the program's coordinates — read from the file.
        Elements without them are left out."""
        s = self.unit_scale
        out = {}
        for guid in guids:
            e = self.by_guid(guid)
            shape = getattr(e, "Representation", None) if e is not None else None
            rep = next((r for r in (shape.Representations if shape is not None else ())
                        if r.RepresentationType == "Curve3D"
                        and getattr(r.ContextOfItems, "TargetView", None) == "ELEVATION_VIEW"), None)
            if rep is None:
                continue
            m = self._placement_si(e)
            segments = []
            for item in rep.Items:
                if not item.is_a("IfcPolyline"):
                    continue
                pts = np.array([p.Coordinates for p in item.Points], dtype=float) * s @ m[:3, :3].T + m[:3, 3]
                segments += [(a, b) for a, b in zip(pts, pts[1:])]
            if segments:
                out[guid] = np.array(segments, dtype=float)
        return out

    @property
    def unit_scale(self):
        """Meters per project length unit (0.001 for millimetres) — (0.287) worked out once per file and unit
        assignment (IfcOpenShell looks it up anew each time: ~0,2 ms, asked thousands of times in one edit)."""
        units = self.file.by_type("IfcUnitAssignment")
        key = (id(self.file), tuple(u.id() for a in units for u in a.Units or ()))
        cached = getattr(self, "_unit_scale", None)
        if cached is None or cached[0] != key:
            cached = self._unit_scale = (key, ifcopenshell.util.unit.calculate_unit_scale(self.file))
        return cached[1]

    def storey(self, guid=None):
        """The storey `guid`, or the lowest one (created if the file has none)."""
        if guid is not None:
            found = self.by_guid(guid)
            if found is not None and found.is_a("IfcBuildingStorey"):
                return found
        storeys = self.file.by_type("IfcBuildingStorey")
        if storeys:
            return min(storeys, key=self._elevation)
        return self.add_storey("Térreo", 0.0)

    # ------------------------------------------------------------ storeys (levels)

    def _elevation(self, storey):
        """Storey level in meters: from its placement (what the geometry uses), else its Elevation — (0.225) inside
        remembering() worked out once until the file changes."""
        scope = getattr(self, "_remember", None)
        if scope is not None:
            key = (storey.id(), self._change_key())
            levels = scope.setdefault("levels", {})
            if key in levels:
                return levels[key]
        if storey.ObjectPlacement is not None and storey.ObjectPlacement.is_a("IfcLocalPlacement"):
            level = float(self._placement_si(storey)[2, 3])
        else:
            level = float(storey.Elevation or 0.0) * self.unit_scale
        if scope is not None:
            levels[key] = level
        return level

    def storeys(self):
        """[(GlobalId, name, level in meters)] of the building storeys, lowest first — (0.225) inside remembering()
        worked out once until the file changes (an edit asks for them a few times: the storey a wall's top is
        tied to, the work level, the images and drawings on each storey…)."""
        scope = getattr(self, "_remember", None)
        key = self._change_key() if scope is not None else None
        if scope is not None and scope.get("storeys", (None,))[0] == key:
            return list(scope["storeys"][1])
        out = sorted(((s.GlobalId, s.Name or "", self._elevation(s))
                      for s in self.file.by_type("IfcBuildingStorey")), key=lambda r: r[2])
        if scope is not None:
            scope["storeys"] = (key, out)
        return list(out)

    def _change_key(self):
        """(0.225) What changes whenever the file does: its undo history (each edit a transaction) and, during one,
        the operations recorded in it so far."""
        f = self.file
        t = getattr(f, "transaction", None)
        history, future = getattr(f, "history", []), getattr(f, "future", [])
        return (len(history), id(history[-1]) if history else 0, len(future), id(t) if t else 0,
                len(t.operations) if t else 0)

    @contextlib.contextmanager
    def remembering(self):
        """(0.225) What is asked again and again in one edit (the storeys) worked out once while the file stays as
        it is — the document wraps each edit, its undoing and redoing, and what its listeners do then."""
        outer = getattr(self, "_remember", None)
        if outer is None:
            self._remember = {}
        try:
            yield
        finally:
            if outer is None:
                self._remember = None

    def spatial_tree(self):
        """The spatial structure, from the project down to the storeys (spaces left out):
        nested (GlobalId, IFC class, name, level in m or None, [children]); storeys highest
        first (as in a section), other levels by name. None if the file has no project."""
        projects = self.file.by_type("IfcProject")
        if not projects:
            return None

        def node(e, depth=0):
            children = []
            for rel in (getattr(e, "IsDecomposedBy", None) or ()) if depth < 12 else ():
                for c in rel.RelatedObjects:
                    if c.is_a("IfcSpatialStructureElement") and not c.is_a("IfcSpace"):
                        children.append(node(c, depth + 1))
            children.sort(key=lambda n: (n[3] is None, -(n[3] or 0.0), n[2]))
            level = self._elevation(e) if e.is_a("IfcBuildingStorey") else None
            return (e.GlobalId, e.is_a(), e.Name or "", level, children)

        return node(projects[0])

    def add_storey(self, name, elevation):
        """New storey at `elevation` (m) in the building. Returns it."""
        f = self.file
        building = (f.by_type("IfcBuilding") or [None])[0]
        storey = api.root.create_entity(f, ifc_class="IfcBuildingStorey", name=name)
        if building is not None:
            api.aggregate.assign_object(f, products=[storey], relating_object=building)
        self._place(storey, _translation(0.0, 0.0, elevation))
        storey.Elevation = elevation / self.unit_scale
        return storey

    def set_storey_elevation(self, guid, elevation):
        """Move a storey to a new level; everything placed in it moves along
        (walls, slabs, columns, their openings, doors and windows)."""
        storey = self.storey(guid)
        m = self._placement_si(storey) if storey.ObjectPlacement is not None else np.eye(4)
        m[2, 3] = elevation
        self._place(storey, m, should_transform_children=True)
        storey.Elevation = elevation / self.unit_scale
        self.refresh_constraints(guid)        # walls / columns tied to it by their top keep it (0.73)

    def storey_elements(self, guid):
        """GlobalIds of the elements contained in a storey (doors and windows included)."""
        storey = self.by_guid(guid)
        return [e.GlobalId for rel in (getattr(storey, "ContainsElements", None) or ())
                for e in rel.RelatedElements]

    def remove_storey(self, guid):
        from .edit import EditRefused
        if len(self.file.by_type("IfcBuildingStorey")) <= 1:
            raise EditRefused("last_storey")
        if self.storey_elements(guid):
            raise EditRefused("storey_not_empty")
        for other in self.constrained_to(guid):    # their top was this storey: not connected now, as tall
            self._set_params(self.by_guid(other), {"TopoPavimento": None, "TopoDesvio": None})
        api.root.remove_product(self.file, product=self.by_guid(guid))

    def storey_of(self, guid):
        """GlobalId of the storey an element is in, or None."""
        e = self.by_guid(guid)
        container = (ifcopenshell.util.element.get_container(e, ifc_class="IfcBuildingStorey")
                     if e is not None else None)
        return container.GlobalId if container is not None else None

    def storeys_of(self, elements):
        """{GlobalId: storey GlobalId or None} for many elements at once (opening a file):
        one pass over the containment relations; the others (inside an aggregate...) one by one."""
        direct = {}
        for rel in self.file.by_type("IfcRelContainedInSpatialStructure"):
            if rel.RelatingStructure.is_a("IfcBuildingStorey"):
                storey = rel.RelatingStructure.GlobalId
                for e in rel.RelatedElements:
                    direct.setdefault(e.id(), storey)
        return {e.GlobalId: direct[e.id()] if e.id() in direct else self.storey_of(e.GlobalId) for e in elements}

    def transform(self, guid, matrix):
        """Move / rotate an element: the 4x4 `matrix` (meters, world) is applied to
        its placement. What is placed relative to it goes along (a wall's openings,
        doors and windows); its geometry itself is not touched."""
        from .edit import EditRefused
        e = self.by_guid(guid)
        if e is None or e.ObjectPlacement is None or not e.ObjectPlacement.is_a("IfcLocalPlacement"):
            raise EditRefused("not_movable")
        m = np.asarray(matrix, dtype=float) @ self._placement_si(e)
        self._place(e, m, should_transform_children=True)
        if abs(float(np.asarray(matrix)[2, 3])) > 1e-9:
            self._retie_top(guid)                 # moved up / down: its top offset follows (0.73)

    # ------------------------------------------------------------ components (types with shared geometry)

    def create_component(self, name, category, verts, faces, matrix, storey=None):
        """A new component: an IFC type that holds the geometry once (an
        IfcRepresentationMap; verts in meters, in the component's own frame)
        and its first instance placed at `matrix`. Returns the instance."""
        f = self.file
        occurrence_class, type_class = COMPONENT_CLASSES[category]
        type_ = api.root.create_entity(f, ifc_class=type_class, name=name, predefined_type="NOTDEFINED")
        if type_.is_a("IfcFurnitureType"):
            type_.AssemblyPlace = "NOTDEFINED"
        rep = api.geometry.add_mesh_representation(f, context=self.body, vertices=[[tuple(map(float, v)) for v in verts]],
                                                  faces=[[tuple(int(i) for i in face) for face in faces]])
        api.geometry.assign_representation(f, product=type_, representation=rep)
        self._mark(type_, "component")
        return self.add_component_instance(type_.GlobalId, matrix, storey)

    def create_imported_component(self, name, category, parts, matrix=None, storey=None):
        """(0.351) A component brought from a 3D file (model/mesh_import): an IFC type that keeps its shape once — a
        triangulated face set a material, styled in its colour (see-through when it is) — and, given a `matrix`, its
        first copy placed there. parts: [(material name, rgb, alpha, vertices (V, 3) in metres in its own frame,
        triangles (T, 3))]. Returns the type."""
        f, u = self.file, 1.0 / self.unit_scale
        _occurrence, type_class = COMPONENT_CLASSES[category]
        type_ = api.root.create_entity(f, ifc_class=type_class, name=name, predefined_type="NOTDEFINED")
        if type_.is_a("IfcFurnitureType"):
            type_.AssemblyPlace = "NOTDEFINED"
        items = []
        for part_name, rgb, alpha, verts, tris in parts:
            item = f.createIfcTriangulatedFaceSet(
                f.createIfcCartesianPointList3D((np.asarray(verts, dtype=float) * u).tolist()), None, None,
                (np.asarray(tris, dtype=np.int64) + 1).tolist(), None)
            f.createIfcStyledItem(item, [self._imported_style(part_name, rgb, alpha)], None)
            items.append(item)
        api.geometry.assign_representation(f, product=type_, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "Tessellation", items))
        origin = type_.RepresentationMaps[0].MappingOrigin   # (its axes the default ones, left out: the copies are
        origin.Axis = origin.RefDirection = None             # then read as they are, in their pieces' colours)
        self._mark(type_, "component")
        if matrix is not None:
            self.add_component_instance(type_.GlobalId, matrix, storey)
        return type_

    def _imported_style(self, name, rgb, alpha):
        """(0.351) The surface style of a material brought from a 3D file: the one already there of its name, colour
        and transparency, else a new one."""
        transparency = round(1.0 - float(alpha), 2)
        for s in self.file.by_type("IfcSurfaceStyle"):
            shading = next((x for x in s.Styles or () if x.is_a("IfcSurfaceStyleShading")), None)
            if s.Name == name and shading is not None and shading.SurfaceColour is not None and \
                    all(abs(a - b) < 1e-3 for a, b in zip((shading.SurfaceColour.Red, shading.SurfaceColour.Green,
                                                           shading.SurfaceColour.Blue), rgb)) and \
                    abs((getattr(shading, "Transparency", None) or 0.0) - transparency) < 1e-3:
                return s
        style = api.style.add_style(self.file, name=name)
        attributes = {"SurfaceColour": {"Name": None, "Red": float(rgb[0]), "Green": float(rgb[1]),
                                        "Blue": float(rgb[2])}}
        if transparency > 0.0:
            attributes["Transparency"] = transparency
        api.style.add_surface_style(self.file, style=style, ifc_class="IfcSurfaceStyleShading", attributes=attributes)
        return style

    def add_component_instance(self, type_guid, matrix, storey=None, name=None, guid=None):
        """Place one more instance of a component (it shares the type's geometry): one made
        by ArqBIM or any type with a shape kept once (furniture brought from another project…)."""
        f = self.file
        type_ = self.by_guid(type_guid)
        inst = api.root.create_entity(f, ifc_class=_occurrence_class(type_), name=name or type_.Name)
        if guid is not None:
            inst.GlobalId = guid                    # an instance brought back keeps its identity
        api.type.assign_type(f, related_objects=[inst], relating_type=type_)   # -> mapped representation
        self._place(inst, matrix)
        container = self.storey(storey) if storey is not None else self.storey_at(float(np.asarray(matrix)[2, 3]))
        api.spatial.assign_container(f, products=[inst], relating_structure=container)
        if self.kind_of(type_guid) == "component":
            self._mark(inst, "component")
        return inst

    def component_box(self, type_guid):
        """(lowest, highest) corner in metres of a component's shape in its own frame (the
        placement of its instances), from the type's kept shape — no instance needed."""
        shape_map = self.by_guid(type_guid).RepresentationMaps[0]
        settings = ifcopenshell.geom.settings()
        geometry = ifcopenshell.geom.create_shape(settings, shape_map.MappedRepresentation)
        verts = np.array(getattr(geometry, "geometry", geometry).verts, dtype=float).reshape(-1, 3)
        if not len(verts):
            return np.zeros(3), np.zeros(3)
        origin = ifcopenshell.util.placement.get_axis2placement(shape_map.MappingOrigin)
        origin[:3, 3] *= self.unit_scale
        verts = verts @ origin[:3, :3].T + origin[:3, 3]
        return verts.min(axis=0), verts.max(axis=0)

    def component_shape(self, type_guid):
        """(0.466) A component's shape in its own frame, metres — (triangles' corners (T, 3, 3), their sRGB (T, 3)) —,
        for its miniature in the Library panel."""
        return type_shape(self.by_guid(type_guid), self.unit_scale)

    @staticmethod
    def read_library(path):
        """Another IFC file's components, to bring into this project: (its file, [(type entity
        id, name, IFC class, its copies there)]) — types with a shape kept once that can be
        placed on their own (not doors or windows, which go in walls)."""
        library = rename_legacy(ifcopenshell.open(path))
        found = []
        for type_ in library.by_type("IfcTypeProduct"):
            if getattr(type_, "RepresentationMaps", None) and _occurrence_class(type_) is not None:
                copies = len(ifcopenshell.util.element.get_types(type_))
                found.append((type_.id(), type_.Name or type_.is_a(), type_.is_a(), copies))
        return library, sorted(found, key=lambda item: item[1].lower())

    def append_components(self, library, type_ids):
        """Bring components from another IFC file (read_library) into this one: the type with
        its shape, materials and properties (IfcOpenShell's append_asset), in this project's
        length unit. Returns their GlobalIds (one already here is not brought twice)."""
        if abs(ifcopenshell.util.unit.calculate_unit_scale(library) - self.unit_scale) > 1e-12:
            unit = ifcopenshell.util.unit.get_project_unit(self.file, "LENGTHUNIT")
            name = ((unit.Prefix or "") + "METER") if unit.is_a("IfcSIUnit") else unit.Name
            ids = {i: library.by_id(i).GlobalId for i in type_ids}
            library = ifcopenshell.util.unit.convert_file_length_units(library, name)
            type_ids = [library.by_guid(g).id() for g in ids.values()]
        out, reuse = [], {}
        for i in type_ids:
            type_ = library.by_id(i)
            if self.by_guid(type_.GlobalId) is None:
                api.project.append_asset(self.file, library=library, element=type_, reuse_identities=reuse)
            out.append(type_.GlobalId)
        return out

    def component_type(self, guid):
        """GlobalId of the component an instance belongs to, or None."""
        e = self.by_guid(guid)
        type_ = ifcopenshell.util.element.get_type(e) if e is not None else None
        return type_.GlobalId if type_ is not None and self.kind_of(type_.GlobalId) == "component" else None

    def library(self):
        """The project's reusable things, for the Project panel: {"components": [(type GlobalId, name,
        [instance GlobalIds], placeable)], "groups": [(model id, name, [[member GlobalIds] per copy])]}.
        Components: types whose shape is kept once (RepresentationMaps) with instances — ArqBIM's,
        which can be placed again, and those of other programs (furniture from Revit…)."""
        components = []
        for type_ in self.file.by_type("IfcTypeProduct"):
            if not getattr(type_, "RepresentationMaps", None) or self.kind_of(type_.GlobalId) == "tile_type":
                continue                                    # (0.281: a tile of the user's own is not placed alone)
            instances = [e.GlobalId for e in ifcopenshell.util.element.get_types(type_)]
            placeable = _occurrence_class(type_) is not None
            if instances or placeable:
                components.append((type_.GlobalId, type_.Name or type_.is_a(), instances, placeable))
        models = {}
        for g in self.file.by_type("IfcGroup"):
            params = self._params(g)
            if params.get("Elemento") == "group":
                model = params.get("Modelo") or g.GlobalId
                name, copies = models.setdefault(model, (g.Name or "", []))
                copies.append(self.group_members(g))
        groups = [(model, name, copies) for model, (name, copies) in models.items()]
        key = lambda item: item[1].lower()                                   # noqa: E731
        return {"components": sorted(components, key=key), "groups": sorted(groups, key=key)}

    def component_instances(self, type_guid):
        return [e.GlobalId for e in ifcopenshell.util.element.get_types(self.by_guid(type_guid))]

    def component_mesh(self, type_guid):
        """(verts in meters, faces) of a component's geometry, in its own frame."""
        rep = self.by_guid(type_guid).RepresentationMaps[0].MappedRepresentation
        s = self.unit_scale
        verts, faces = [], []
        for item in rep.Items:
            base = len(verts)
            if item.is_a("IfcPolygonalFaceSet"):
                verts += [np.array(p, dtype=float) * s for p in item.Coordinates.CoordList]
                faces += [[base + i - 1 for i in face.CoordIndex] for face in item.Faces]
            elif item.is_a("IfcFacetedBrep"):
                for face in item.Outer.CfsFaces:
                    pts = face.Bounds[0].Bound.Polygon
                    faces.append(list(range(len(verts), len(verts) + len(pts))))
                    verts += [np.array(p.Coordinates, dtype=float) * s for p in pts]
        return verts, faces

    def set_component_mesh(self, type_guid, verts, faces):
        """New geometry for a component: every instance changes with it (they map the same geometry)."""
        rep_map = self.by_guid(type_guid).RepresentationMaps[0]
        old = rep_map.MappedRepresentation
        rep_map.MappedRepresentation = api.geometry.add_mesh_representation(
            self.file, context=self.body, vertices=[[tuple(map(float, v)) for v in verts]],
            faces=[[tuple(int(i) for i in face) for face in faces]])
        ifcopenshell.util.element.remove_deep2(self.file, old)

    # ------------------------------------------------------------ copies

    def _copy_product(self, product):
        """A copy in the same place: type, materials, properties and quantities
        (copy_class), plus its own copy of the geometry (copy_class leaves it out)."""
        new = api.root.copy_class(self.file, product=product)
        if product.Representation is not None:
            new.Representation = ifcopenshell.util.element.copy_deep(
                self.file, product.Representation, exclude=["IfcGeometricRepresentationContext", "IfcRepresentationMap"])
        self._leave_copied_groups(new)
        self.copy_map[product.GlobalId] = new.GlobalId
        return new

    def _copy_name(self, original, new):
        """ArqBIM elements get the next number ("Parede 5"); others keep their name."""
        kind = self.kind_of(original.GlobalId)
        prefix = _COPY_PREFIX.get(kind)
        if prefix is not None:
            pt, en = prefix
            word = en if (original.Name or "").startswith(en) else pt     # the language the model was made in
            new.Name = "{} {}".format(word, self.count(original.is_a()))

    def _copy_filled_opening(self, opening, host, placement_parent):
        """Copy an opening with its door/window into `host` (placed relative to `placement_parent`)."""
        new_op = self._copy_product(opening)
        for rel in new_op.VoidsElements or ():
            rel.RelatingBuildingElement = host
        new_op.ObjectPlacement.PlacementRelTo = placement_parent
        fillings = []
        for rel in opening.HasFillings or ():
            original = rel.RelatedBuildingElement
            fill = self._copy_product(original)
            fill.ObjectPlacement.PlacementRelTo = new_op.ObjectPlacement
            api.feature.add_filling(self.file, opening=new_op, element=fill)
            self._copy_name(original, fill)
            kind = self.kind_of(original.GlobalId)
            if kind in MARK_PREFIX:
                fill.Tag = self.next_mark(kind)            # (0.110) a copy: the next mark
            fillings.append(fill)
        return new_op, fillings

    def copy_element(self, guid):
        """A copy of an element in the same place (move it afterwards with
        transform). A wall's openings, doors and windows are copied with it.
        Returns the new element."""
        from .edit import EditRefused
        e = self.by_guid(guid)
        if e is None or e.ObjectPlacement is None or not e.ObjectPlacement.is_a("IfcLocalPlacement"):
            raise EditRefused("not_movable")
        new = self._copy_product(e)                 # empty openings come along (copy_class)
        for rel in list(e.HasOpenings or ()):
            opening = rel.RelatedOpeningElement
            if opening.HasFillings:
                self._copy_filled_opening(opening, new, new.ObjectPlacement)
        self._copy_name(e, new)
        if self.created is not None:
            self.created.append(new.GlobalId)       # (a typical floor copies it too, 0.90)
        if getattr(self, "made", None) is not None:
            self.made.append(new.GlobalId)
        return new

    def copy_filling(self, guid):
        """A second door/window just like this one, in the same wall and place
        (slide it afterwards with move_filling). Returns the new door/window."""
        e = self.by_guid(guid)
        opening = e.FillsVoids[0].RelatingOpeningElement
        wall = opening.VoidsElements[0].RelatingBuildingElement
        _new_op, fillings = self._copy_filled_opening(opening, wall, opening.ObjectPlacement.PlacementRelTo)
        return [f for f in fillings if f.is_a() == e.is_a()][0]

    def storey_at(self, z):
        """The storey an element at level z belongs to: the highest one at or below z (1 cm tolerance)."""
        storeys = self.file.by_type("IfcBuildingStorey")
        if not storeys:
            return self.storey()
        below = [s for s in storeys if self._elevation(s) <= z + 0.01]
        return max(below, key=self._elevation) if below else min(storeys, key=self._elevation)

    # ------------------------------------------------------------ catalogue types

    def _material(self, key, lang):
        spec = catalog.MATERIALS[key]
        name = spec.name_pt if lang == "pt" else spec.name_en
        for m in self.file.by_type("IfcMaterial"):
            if m.Name == name:
                return m
        mat = api.material.add_material(self.file, name=name, category=spec.category)
        style = api.style.add_style(self.file, name=name)
        r, g, b = spec.color
        api.style.add_surface_style(self.file, style=style, ifc_class="IfcSurfaceStyleShading",
                                    attributes={"SurfaceColour": {"Name": None, "Red": r, "Green": g, "Blue": b}})
        api.style.assign_material_style(self.file, material=mat, style=style, context=self.body)
        if spec.density is not None or spec.conductivity is not None:      # (a material of the project, 0.89)
            self.set_material_properties(mat, spec)
        self.set_material_graphics(mat, spec, always=False)               # (0.314: its patterns, its transparency)
        return mat

    def ensure_type(self, spec, lang="pt"):
        """The IFC type for a catalogue entry (created the first time it is used)."""
        ifc_class = {"wall": "IfcWallType", "slab": "IfcSlabType", "column": "IfcColumnType",
                     "beam": "IfcBeamType", "footing": "IfcFootingType", "pipe": "IfcPipeSegmentType",
                     "duct": "IfcDuctSegmentType", "pile": "IfcPileType",
                     "conduit": "IfcCableCarrierSegmentType", "roof": "IfcRoofType",
                     "member": "IfcMemberType"}[spec.kind]                       # (0.495: braces, purlins)
        name = spec.name_pt if lang == "pt" else spec.name_en
        for t in self.file.by_type(ifc_class):
            if t.Name == name:
                return t
        predefined = spec.predefined or {"wall": "STANDARD", "slab": "FLOOR", "column": "COLUMN", "beam": "BEAM",
                                         "footing": "STRIP_FOOTING" if spec.strip else "PAD_FOOTING",
                                         "pipe": "RIGIDSEGMENT", "duct": "RIGIDSEGMENT", "pile": "BORED",
                                         "conduit": "CONDUITSEGMENT",
                                         # (0.278) a roof's form is its own (HIP_ROOF…), not its type's
                                         "roof": "NOTDEFINED", "member": "MEMBER"}[spec.kind]
        type_ = api.root.create_entity(self.file, ifc_class=ifc_class, name=name, predefined_type=predefined)
        to_units = 1.0 / self.unit_scale
        if spec.kind in catalog.LAYERED:
            layer_set = api.material.add_material_set(self.file, name=name, set_type="IfcMaterialLayerSet")
            for k, (key, thickness) in enumerate(spec.layers):
                layer = api.material.add_layer(self.file, layer_set=layer_set, material=self._material(key, lang))
                attributes = {"LayerThickness": thickness * to_units}
                function = catalog.layer_function(spec, k)
                if function is not None and hasattr(layer, "Priority"):    # (0.334: IFC4's; not in IFC2X3)
                    _strength, priority, category = catalog.LAYER_FUNCTIONS[function]
                    attributes.update({"Priority": priority, "Category": category})
                api.material.edit_layer(self.file, layer=layer, attributes=attributes)
            api.material.assign_material(self.file, products=[type_], type="IfcMaterialLayerSet", material=layer_set)
        else:
            x, y = spec.profile
            if spec.section:                     # (0.494) a steel section of the catalogue, named as it is
                profile = self._steel_profile(spec.section)
            elif spec.round:                     # a pipe, a pile, a round column: a circle of its diameter
                profile = api.profile.add_parameterized_profile(self.file, ifc_class="IfcCircleProfileDef")
                profile.Radius = x / 2 * to_units
            elif spec.shape == "L":              # (0.97) an L: its outer sizes, its legs' thickness
                profile = api.profile.add_parameterized_profile(self.file, ifc_class="IfcLShapeProfileDef")
                profile.Width, profile.Depth, profile.Thickness = x * to_units, y * to_units, spec.web * to_units
            elif spec.shape == "T":              # (0.97) a T: its flange's width, its depth, both thicknesses
                profile = api.profile.add_parameterized_profile(self.file, ifc_class="IfcTShapeProfileDef")
                profile.FlangeWidth, profile.Depth = x * to_units, y * to_units
                profile.FlangeThickness = profile.WebThickness = spec.web * to_units
            else:
                profile = api.profile.add_parameterized_profile(self.file, ifc_class="IfcRectangleProfileDef")
                profile.XDim, profile.YDim = x * to_units, y * to_units
            if not spec.section:                 # (a steel section keeps its own name: «IPE300»)
                profile.ProfileName = name
            profile_set = api.material.add_material_set(self.file, name=name, set_type="IfcMaterialProfileSet")
            api.material.add_profile(self.file, profile_set=profile_set,
                                     material=self._material(spec.material, lang), profile=profile)
            api.material.assign_material(self.file, products=[type_], type="IfcMaterialProfileSet",
                                         material=profile_set)
            common = {"pipe": ("Pset_PipeSegmentTypeCommon", {"NominalDiameter": x * to_units,
                                                              "OuterDiameter": x * to_units}),
                      "duct": ("Pset_DuctSegmentTypeCommon", {"Shape": "ROUND", "NominalDiameterOrWidth": x * to_units}
                               if spec.round else {"Shape": "RECTANGULAR", "NominalDiameterOrWidth": x * to_units,
                                                   "NominalHeight": y * to_units})}.get(spec.kind)   # (round: 0.138)
            if common:
                pset = api.pset.add_pset(self.file, product=type_, name=common[0])
                api.pset.edit_pset(self.file, pset=pset, properties=common[1])
        return type_

    def _steel_profile(self, section):
        """(0.494) A steel section of the catalogue (core/steel) as its IFC profile — IfcIShapeProfileDef,
        IfcUShapeProfileDef (a UPN's flange slope in the file's angle unit), IfcLShapeProfileDef, the hollow ones,
        IfcCShapeProfileDef; a Z and an omega by their outline —, named as the other programs name it («IPE300»)."""
        import ifcopenshell.util.unit
        from ..core import steel
        sec = steel.get(section)
        if sec is None:
            raise ValueError("unknown steel section: {}".format(section))
        angle = ifcopenshell.util.unit.calculate_unit_scale(self.file, "PLANEANGLEUNIT") or 1.0
        ifc_class, values = steel.ifc_profile(sec, 0.001 / self.unit_scale, angle)
        if ifc_class == "IfcArbitraryClosedProfileDef":       # (IfcOpenShell takes the outline in metres)
            points = [(x * self.unit_scale, y * self.unit_scale) for x, y in values["points"]]
            profile = api.profile.add_arbitrary_profile(self.file, profile=points + [points[0]], name=sec.name)
        else:
            profile = api.profile.add_parameterized_profile(self.file, ifc_class=ifc_class)
            for attribute, value in values.items():
                setattr(profile, attribute, value)
        profile.ProfileName = sec.name
        return profile

    # ------------------------------------------------------------ elements

    def create_from_box(self, spec, box, name, lang="pt", storey=None):
        """Create a parametric wall / slab / column from an upright sketch box, in
        the storey `storey` (GlobalId), or else the storey it stands on (slabs: the
        storey their top is at). Returns the new element."""
        f = self.file
        type_ = self.ensure_type(spec, lang)
        to_units = 1.0 / self.unit_scale
        if spec.kind == "footing":                 # (a block classified as a footing: its plan size, the type's depth)
            return self.add_footing(spec, box.center()[:2], box.x_dir, box.length, box.width, box.top, name, lang,
                                    storey)
        ifc_class = {"wall": "IfcWall", "slab": "IfcSlab", "column": "IfcColumn", "beam": "IfcBeam"}[spec.kind]
        element = api.root.create_entity(f, ifc_class=ifc_class, name=name)
        api.type.assign_type(f, related_objects=[element], relating_type=type_)

        if spec.kind == "wall":
            matrix, length, height = classify.wall_from_box(box)
            t = spec.thickness
            usage = ifcopenshell.util.element.get_material(element, should_skip_usage=False)
            usage.OffsetFromReferenceLine = -t / 2 * to_units      # layers centred on the axis line
            self._set_wall_body(element, length, height, t)
            pset = ("Pset_WallCommon", {"IsExternal": False,
                                        "LoadBearing": catalog.load_bearing_wall(spec)})   # (0.342: concrete)
        elif spec.kind == "slab":
            t = spec.thickness
            matrix, polyline = classify.slab_from_box(box, t)
            self._set_slab_body(element, 0.0, 0.0, box.length, box.width, t)
            pset = ("Pset_SlabCommon", {"IsExternal": False, "LoadBearing": True})
        elif spec.kind == "beam":
            matrix, length = classify.beam_from_box(box, spec.profile[1])
            profile = ifcopenshell.util.element.get_material(type_).MaterialProfiles[0].Profile
            self._set_profile_body(element, profile, length, "Qto_BeamBaseQuantities")
            pset = ("Pset_BeamCommon", {"IsExternal": False, "LoadBearing": True})
        else:
            matrix, height = classify.column_from_box(box)
            profile = ifcopenshell.util.element.get_material(type_).MaterialProfiles[0].Profile
            self._set_column_body(element, profile, height)
            pset = ("Pset_ColumnCommon", {"IsExternal": False, "LoadBearing": True})

        self._place(element, matrix)
        if storey is not None:
            container = self.storey(storey)
        else:
            container = self.storey_at(box.top if spec.kind == "slab" else box.bottom)
        # placed relative to the storey from here on: moving the storey moves the element
        api.spatial.assign_container(f, products=[element], relating_structure=container)
        # Holes punched in the sketch (Push/Pull through) become real IFC openings.
        if box.voids:
            if spec.kind == "wall":
                boxes = classify.void_boxes(matrix, box.voids, 1, -spec.thickness / 2, spec.thickness / 2)
            elif spec.kind == "slab":
                boxes = classify.void_boxes(matrix, box.voids, 2, 0.0, spec.thickness)
            else:
                boxes = None
            if boxes is None:
                raise ValueError("void not supported for this element")
            for k, (lo, hi) in enumerate(boxes, 1):
                self.add_void(element, matrix, lo, hi, "{} - {} {}".format(name, _VOID_NAME[lang], k))
        common = api.pset.add_pset(f, product=element, name=pset[0])
        api.pset.edit_pset(f, pset=common, properties=pset[1])
        self._mark(element, spec.kind)                         # (a raft's BASESLAB is its type's, 0.94)
        return element

    def add_pile(self, spec, top, length, name, lang="pt", storey=None, x_dir=(1.0, 0.0, 0.0)):
        """A pile (0.94): its round section from `top` (the middle of its head) down `length` m."""
        top = np.asarray(top, dtype=float)
        foot = top - np.array((0.0, 0.0, float(length)))
        return self._new_profiled(spec, classify.placement(foot, np.asarray(x_dir, float)), float(length), name,
                                  lang, storey, float(foot[2]))

    def add_column(self, spec, base, height, name, lang="pt", storey=None, x_dir=(1.0, 0.0, 0.0)):
        """A column (0.66) standing at `base` (the middle of its foot), `height` tall, its section turned
        along x_dir (horizontal), in the storey `storey` (GlobalId) or the one it stands on."""
        return self._new_profiled(spec, classify.placement(np.asarray(base, dtype=float), np.asarray(x_dir, float)),
                                  float(height), name, lang, storey, float(base[2]))

    def add_beam(self, spec, start, end, top, name, lang="pt", storey=None):
        """A beam (0.66) from `start` to `end` (made level), its top at the height `top`, in the storey
        `storey` (GlobalId) or the one its underside is in."""
        matrix, length = classify.beam_placement(start, end, top, spec.profile[1])
        return self._new_profiled(spec, matrix, length, name, lang, storey, top - spec.profile[1])

    def add_segment(self, spec, start, end, z, name, lang="pt", storey=None, end_z=None, x_dir=None):
        """A pipe or a duct (0.69) from `start` to `end` (plan), its axis at the height `z` — at its end at
        `end_z` (0.136: sloped; at the same plan point: vertical, its section turned along x_dir), level when
        None — in the storey `storey` (GlobalId) or the one its lower end is in."""
        end_z = float(z) if end_z is None else float(end_z)
        a = np.array((float(start[0]), float(start[1]), float(z)))
        b = np.array((float(end[0]), float(end[1]), end_z))
        matrix, length = classify.segment_placement(a, b, x_dir)
        return self._new_profiled(spec, matrix, length, name, lang, storey, min(float(z), end_z))

    def _new_profiled(self, spec, matrix, length, name, lang, storey, z):
        """A column, a beam, a pipe or a duct: its type's section extruded `length` along the placement's Z."""
        f = self.file
        type_ = self.ensure_type(spec, lang)
        ifc_class, qto, pset = {"column": ("IfcColumn", "Qto_ColumnBaseQuantities", "Pset_ColumnCommon"),
                                "beam": ("IfcBeam", "Qto_BeamBaseQuantities", "Pset_BeamCommon"),
                                "pipe": ("IfcPipeSegment", "Qto_PipeSegmentBaseQuantities", None),
                                "duct": ("IfcDuctSegment", "Qto_DuctSegmentBaseQuantities", None),
                                "conduit": ("IfcCableCarrierSegment", "Qto_CableCarrierSegmentBaseQuantities", None),
                                "pile": ("IfcPile", "Qto_PileBaseQuantities", "Pset_PileCommon")}[spec.kind]
        element = api.root.create_entity(f, ifc_class=ifc_class, name=name)
        api.type.assign_type(f, related_objects=[element], relating_type=type_)
        profile = ifcopenshell.util.element.get_material(type_).MaterialProfiles[0].Profile
        self._set_profile_body(element, profile, length, qto)
        self._place(element, matrix)
        container = self.storey(storey) if storey is not None else self.storey_at(z)
        api.spatial.assign_container(f, products=[element], relating_structure=container)
        if pset:
            common = api.pset.add_pset(f, product=element, name=pset)
            api.pset.edit_pset(f, pset=common, properties={"IsExternal": False, "LoadBearing": True})
        self._mark(element, spec.kind)
        if spec.kind in ("pipe", "duct", "conduit"):
            self.add_segment_ports(element, spec.kind)          # one at each end (0.74)
        return element

    def add_footing(self, spec, center, x_dir, length, width, top, name, lang="pt", storey=None):
        """A footing (0.68): a level block length × width (along x_dir × across it) centred on `center`
        (plan), its top at the height `top`, as deep as its type; a pad (under a column) or a strip
        (along a wall)."""
        f = self.file
        type_ = self.ensure_type(spec, lang)
        element = api.root.create_entity(f, ifc_class="IfcFooting", name=name, predefined_type=spec.predefined or (
            "STRIP_FOOTING" if spec.strip else "PAD_FOOTING"))
        api.type.assign_type(f, related_objects=[element], relating_type=type_)
        x = classify.normalize(np.array((x_dir[0], x_dir[1], 0.0)))
        y = np.cross(classify.Z, x)
        depth = spec.thickness
        corner = np.array((center[0], center[1], top - depth)) - x * length / 2 - y * width / 2
        self._set_footing_body(element, length, width, depth)
        self._place(element, classify.placement(corner, x))
        container = self.storey(storey) if storey is not None else self.storey_at(top)
        api.spatial.assign_container(f, products=[element], relating_structure=container)
        common = api.pset.add_pset(f, product=element, name="Pset_FootingCommon")
        api.pset.edit_pset(f, pset=common, properties={"LoadBearing": True})
        self._mark(element, "footing")
        if spec.piles and spec.pile in catalog.BY_KEY:        # a pile cap (0.94): its piles under it, tied to it
            pile = catalog.BY_KEY[spec.pile]
            head = np.array((center[0], center[1], top - depth))
            for k, (dx, dy) in enumerate(pile_spots(spec.piles, length, width, pile.profile[0])):
                p = self.add_pile(pile, head + x * dx + y * dy, spec.pile_length,
                                  "{} - {} {}".format(name, _PILE_NAME[lang], k + 1), lang, storey=container.GlobalId,
                                  x_dir=x)
                self.tie_footing(p.GlobalId, element.GlobalId)
        return element

    def footing_params(self, guid):
        """(centre (plan), x direction, length, width, top height) of a footing made by this program."""
        e = self.by_guid(guid)
        q = ifcopenshell.util.element.get_psets(e).get("Qto_FootingBaseQuantities", {})
        s = self.unit_scale
        length, width, depth = q["Length"] * s, q["Width"] * s, q["Height"] * s
        m = self.placement(guid)
        x, y = m[:3, 0] / np.linalg.norm(m[:3, 0]), m[:3, 1] / np.linalg.norm(m[:3, 1])
        centre = m[:3, 3] + x * length / 2 + y * width / 2
        return centre[:2], x, length, width, float(m[2, 3] + depth)

    def read_grids(self):
        """[(tag, (x, y), (x, y))] of every IfcGrid's axes, in the program's coordinates — a grid made by
        another program, shown and taken over as the project's structural grid (0.67)."""
        out, s = [], self.unit_scale
        for grid in self.file.by_type("IfcGrid"):
            m = self._placement_si(grid)
            for attr in ("UAxes", "VAxes", "WAxes"):
                for axis in getattr(grid, attr, None) or ():
                    pts = getattr(axis.AxisCurve, "Points", None)
                    if not pts or len(pts) < 2:
                        continue
                    ends = []
                    for p in (pts[0], pts[-1]):
                        c = np.array(list(p.Coordinates) + [0.0] * (3 - len(p.Coordinates)), dtype=float) * s
                        ends.append(tuple(float(v) for v in (m @ np.append(c, 1.0))[:2]))
                    out.append((axis.AxisTag or "", ends[0], ends[1]))
        return out

    def write_grid(self, axes, level=0.0, name="Eixos"):
        """The structural grid (0.67) as the project's one IfcGrid, from its axes [(tag, (x, y), (x, y),
        numbered)]: the numbered ones (running along Y) its UAxes, the others its VAxes — kept, changed,
        or taken out while one of the two ways has none (an IfcGrid needs both: the IFC stays valid).
        Its GlobalId stays while it is there. Returns it, or None."""
        f = self.file
        grids = f.by_type("IfcGrid")
        for extra in grids[1:]:
            self._remove_grid(extra)
        grid = grids[0] if grids else None
        numbered = [a for a in axes if a[3]]
        lettered = [a for a in axes if not a[3]]
        if not numbered or not lettered:
            if grid is not None:
                self._remove_grid(grid)
            return None
        if grid is None:
            grid = api.root.create_entity(f, ifc_class="IfcGrid", name=name)
            m = np.eye(4)
            m[2, 3] = level
            self._place(grid, m)
            api.spatial.assign_container(f, products=[grid], relating_structure=self.storey_at(level))
        else:
            for attr in ("UAxes", "VAxes", "WAxes"):
                for axis in list(getattr(grid, attr, None) or ()):
                    api.grid.remove_grid_axis(f, axis=axis)
        z = self._placement_si(grid)[2, 3]
        for uvw, family in (("UAxes", numbered), ("VAxes", lettered)):
            for tag, a, b, _n in family:
                axis = api.grid.create_grid_axis(f, grid=grid, axis_tag=str(tag), uvw_axes=uvw)
                api.grid.create_axis_curve(f, p1=np.array((a[0], a[1], z)) + self.origin,
                                           p2=np.array((b[0], b[1], z)) + self.origin, grid_axis=axis)
        return grid

    def _remove_grid(self, grid):
        for attr in ("UAxes", "VAxes", "WAxes"):
            for axis in list(getattr(grid, attr, None) or ()):
                api.grid.remove_grid_axis(self.file, axis=axis)
        api.root.remove_product(self.file, product=grid)

    def beam_params(self, guid):
        """(start, end, top, width, height) in metres of a beam made by this program: its axis ends at
        the height of its section's middle, its top's height, its section."""
        e = self.by_guid(guid)
        length = ifcopenshell.util.element.get_psets(e).get("Qto_BeamBaseQuantities", {})["Length"] * self.unit_scale
        prof = ifcopenshell.util.element.get_material(e, should_skip_usage=True).MaterialProfiles[0].Profile
        w, h, _area, _p = profile_size(prof)
        width, height = w * self.unit_scale, h * self.unit_scale
        m = self.placement(guid)
        d = m[:3, 2] / np.linalg.norm(m[:3, 2])
        start = m[:3, 3].copy()
        return start, start + d * length, float(start[2] + height / 2), width, height

    def site_location(self):
        """(latitude, longitude, elevation above sea level) of the site (0.70): decimal degrees and metres,
        or None for what is not given."""
        import ifcopenshell.util.geolocation as geo
        sites = self.file.by_type("IfcSite")
        if not sites:
            return None, None, None
        s = sites[0]
        lat = geo.dms2dd(*s.RefLatitude) if s.RefLatitude else None
        lon = geo.dms2dd(*s.RefLongitude) if s.RefLongitude else None
        return lat, lon, (s.RefElevation * self.unit_scale if s.RefElevation is not None else None)

    def set_site_location(self, latitude, longitude, elevation=0.0):
        """Georeference the model by its site (0.70): latitude and longitude (decimal degrees, as on a map),
        elevation above sea level (m)."""
        import ifcopenshell.util.geolocation as geo
        sites = self.file.by_type("IfcSite")
        site = sites[0] if sites else None
        if site is None:
            return
        site.RefLatitude = geo.dd2dms(float(latitude), use_us=True)
        site.RefLongitude = geo.dd2dms(float(longitude), use_us=True)
        site.RefElevation = float(elevation or 0.0) / self.unit_scale

    def segment_params(self, guid):
        """(start, end, axis height) in metres of a pipe or a duct made by this program."""
        e = self.by_guid(guid)
        q = ifcopenshell.util.element.get_psets(e)
        q = q.get("Qto_PipeSegmentBaseQuantities") or q.get("Qto_DuctSegmentBaseQuantities") or \
            q.get("Qto_CableCarrierSegmentBaseQuantities") or {}
        length = q["Length"] * self.unit_scale
        m = self.placement(guid)
        d = m[:3, 2] / np.linalg.norm(m[:3, 2])
        start = m[:3, 3].copy()
        return start, start + d * length, float(start[2])

    def count(self, ifc_class):
        return len(self.file.by_type(ifc_class))

    def placement(self, guid):
        """Object placement as a 4x4 matrix in meters."""
        return self._placement_si(self.by_guid(guid))

    def _placement_si(self, element):
        """An element's placement in meters, in the program's coordinates (near the origin)."""
        m = self._local_placement(element.ObjectPlacement).copy()
        m[:3, 3] *= self.unit_scale
        m[:3, 3] -= self.origin
        return m

    def _local_placement(self, placement):
        """(0.225) ifcopenshell.util.placement.get_local_placement — its axes worked out without numpy's small
        calls, and inside remembering() each placement once while the file stays as it is (an element's goes up
        through its storey's, its building's, its site's: those are shared by all)."""
        if placement is None:
            return np.eye(4)
        scope = getattr(self, "_remember", None)
        memo = None
        if scope is not None:
            key = self._change_key()
            kept = scope.get("placements")
            if kept is None or kept[0] != key:
                kept = scope["placements"] = (key, {})
            memo = kept[1]
            hit = memo.get(placement.id())
            if hit is not None:
                return hit
        rel = placement.RelativePlacement if placement.is_a("IfcLocalPlacement") else None
        own = _axis2placement(rel) if rel is not None else None
        if own is None:                                 # (a grid placement, a point not Cartesian…: as IfcOpenShell)
            m = ifcopenshell.util.placement.get_local_placement(placement)
        else:
            rel_to = placement.PlacementRelTo
            m = own if rel_to is None else self._local_placement(rel_to) @ own
        if memo is not None:
            memo[placement.id()] = m
        return m

    def _place(self, product, matrix, **options):
        """Set a placement given in meters in the program's coordinates (the IFC gets its own)."""
        m = np.array(matrix, dtype=float)
        m[:3, 3] += self.origin
        api.geometry.edit_object_placement(self.file, product=product, matrix=m, is_si=True, **options)

    def wall_params(self, guid):
        """(length, height, thickness) in meters of a wall made by this program (from its quantities)."""
        e = self.by_guid(guid)
        q = _quantities(e, "Qto_WallBaseQuantities")            # (0.225: straight, not all its psets)
        if q is None or not {"Length", "Height", "Width"} <= set(q):
            q = ifcopenshell.util.element.get_psets(e).get("Qto_WallBaseQuantities", {})
        s = self.unit_scale
        return q["Length"] * s, q["Height"] * s, q["Width"] * s

    def wall_axis(self, guid):
        """(axis start, axis end, thickness) in meters of a wall made by this
        program: its axis line at the base (the placement is on the axis start)."""
        length, _height, thickness = self.wall_params(guid)
        m = self.placement(guid)
        x = m[:3, 0] / np.linalg.norm(m[:3, 0])
        return m[:3, 3].copy(), m[:3, 3] + x * length, thickness

    # ------------------------------------------------------------ doors and windows

    def next_mark(self, kind):
        """The next free mark of a door ("P7") or window ("J3") (0.110): one more than the highest there is."""
        prefix = MARK_PREFIX[kind]
        used = [int(m.group(1)) for e in self.file.by_type("IfcDoor" if kind == "door" else "IfcWindow")
                for m in [re.match(r"^{}(\d+)$".format(prefix), e.Tag or "")] if m]
        return "{}{}".format(prefix, max(used, default=0) + 1)

    def renumber_openings(self):
        """Every door and window numbered again (0.110): storey by storey (from the lowest), in a plan's reading
        order (from the top, left to right) — P1, P2… and J1, J2…. Returns how many."""
        levels = {g: z for g, _n, z in self.storeys()}
        n = 0
        for kind, cls in (("door", "IfcDoor"), ("window", "IfcWindow")):
            items = []
            for e in self.file.by_type(cls):
                m = self._placement_si(e)
                storey = self.storey_of(e.GlobalId)
                items.append((levels.get(storey, 0.0), -round(float(m[1, 3]), 2), round(float(m[0, 3]), 2), e))
            for k, (*_key, e) in enumerate(sorted(items, key=lambda i: i[:3]), 1):
                e.Tag = "{}{}".format(MARK_PREFIX[kind], k)
                n += 1
        return n

    def add_bare_opening(self, wall_guid, frame, s, width, height, sill, name):
        """An opening with no frame (0.110): the hole a door or window would make, left empty
        (IfcOpeningElement OPENING) — s along the wall to its left edge, its sill above the wall's base."""
        lo = (s, frame.y0 - 0.01, frame.z0 + sill)
        hi = (s + width, frame.y1 + 0.01, frame.z0 + sill + height)
        return self.add_void(wall_guid, frame.matrix, lo, hi, name)

    def add_niche(self, wall_guid, frame, s, width, height, sill, depth, side, name):
        """(0.374) A niche in a wall's face (IfcOpeningElement RECESS): s along the wall to its left edge, its sill
        above the wall's base, `depth` into the wall from its face at y1 (side +1) or y0 (side -1)."""
        if side > 0:
            y_lo, y_hi = frame.y1 - depth, frame.y1 + 0.01
        else:
            y_lo, y_hi = frame.y0 - 0.01, frame.y0 + depth
        lo, hi = (s, y_lo, frame.z0 + sill), (s + width, y_hi, frame.z0 + sill + height)
        return self.add_void(wall_guid, frame.matrix, lo, hi, name, recess=True)

    def ensure_opening_type(self, spec, lang="pt"):
        ifc_class = "IfcDoorType" if spec.kind == "door" else "IfcWindowType"
        name = spec.name_pt if lang == "pt" else spec.name_en
        for t in self.file.by_type(ifc_class):
            if t.Name == name:
                return t
        type_ = api.root.create_entity(self.file, ifc_class=ifc_class, name=name,
                                       predefined_type="DOOR" if spec.kind == "door" else "WINDOW")
        # (0.288) made by its design: how it opens, its fanlight («Bandeira», 0.110), its lining and panel properties,
        # its materials (0.70: a certifier expects them) — the frame, the leaves, the glass
        self.set_opening_design(type_, catalog.design_of(spec), spec.width, spec.height, lang)
        return type_

    def add_opening(self, wall_guid, spec, frame, s, side, name, lang="pt", cut=None):
        """Cut an opening in a wall and fill it with a door or window.

        frame: core.openings.WallFrame of the wall; s: distance along the wall to
        the opening's left edge; side: -1/+1, the face the user clicked (the
        door/window is oriented from that face). cut: (y_lo, y_hi) across the wall the
        opening goes from and to (0.177: a curved wall's, deeper than its thickness),
        else its two faces and a centimetre more. Returns the new door/window.
        """
        f = self.file
        wall = self.by_guid(wall_guid)
        width, height, thickness = spec.width, spec.height, frame.thickness
        margin = 0.01
        z = frame.z0 + spec.sill
        y_lo, y_hi = cut if cut is not None else (frame.y0 - margin, frame.y1 + margin)

        opening = api.root.create_entity(f, ifc_class="IfcOpeningElement", name=name)
        body = api.geometry.add_wall_representation(f, context=self.body, length=width, height=height,
                                                    thickness=y_hi - y_lo, offset=0.0)
        api.geometry.assign_representation(f, product=opening, representation=body)
        self._place(opening, frame.matrix @ _translation(s, y_lo, z))
        api.feature.add_feature(f, feature=opening, element=wall)

        # The filling is placed on the clicked face, its Y axis pointing into the wall.
        if side < 0:
            local = _translation(s, frame.y0, z)
        else:
            local = _translation(s + width, frame.y1, z) @ _rot_z_180()
        type_ = self.ensure_opening_type(spec, lang)
        if spec.kind == "door":
            filling = api.root.create_entity(f, ifc_class="IfcDoor", name=name, predefined_type="DOOR")
            filling.OperationType, filling.UserDefinedOperationType = \
                type_.OperationType, type_.UserDefinedOperationType                  # (0.288: its type's)
            pset = ("Pset_DoorCommon", {"IsExternal": False})
        else:
            filling = api.root.create_entity(f, ifc_class="IfcWindow", name=name, predefined_type="WINDOW")
            filling.PartitioningType, filling.UserDefinedPartitioningType = \
                type_.PartitioningType, type_.UserDefinedPartitioningType
            pset = ("Pset_WindowCommon", {"IsExternal": False})
        api.type.assign_type(f, related_objects=[filling], relating_type=type_)
        filling.Tag = self.next_mark(spec.kind)            # (0.110) its mark: P1, P2… / J1, J2…
        # its type's design: a door's lining the wall's thickness, a window's frame in the wall's middle
        self._set_filling_body(filling, spec.kind, width, height, thickness)
        self._place(filling, frame.matrix @ local)
        api.feature.add_filling(f, opening=opening, element=filling)
        if self._arched(opening) is not None:          # (0.294) an arched door / window: its opening so
            self._set_box_body(opening, frame.matrix, (s, y_lo, z), (s + width, y_hi, z + height))
        container = ifcopenshell.util.element.get_container(wall) or self.storey()
        api.spatial.assign_container(f, products=[filling], relating_structure=container)
        common = api.pset.add_pset(f, product=filling, name=pset[0])
        api.pset.edit_pset(f, pset=common, properties=pset[1])
        self._mark(filling, spec.kind)
        return filling

    def add_void(self, element_guid, matrix, box_lo, box_hi, name, recess=False):
        """An empty opening (IfcOpeningElement, no door/window) cut into a wall or
        slab: an axis-aligned box in the element's frame `matrix` (meters).
        recess=True makes a niche that does not go through (PredefinedType RECESS)."""
        f = self.file
        element = self.by_guid(element_guid) if isinstance(element_guid, str) else element_guid
        lo, hi = np.asarray(box_lo, dtype=float), np.asarray(box_hi, dtype=float)
        size = hi - lo
        opening = api.root.create_entity(f, ifc_class="IfcOpeningElement", name=name,
                                         predefined_type="RECESS" if recess else "OPENING")
        body = api.geometry.add_wall_representation(f, context=self.body, length=size[0], height=size[2],
                                                    thickness=size[1], offset=0.0)
        api.geometry.assign_representation(f, product=opening, representation=body)
        self._place(opening, matrix @ _translation(*lo))
        api.feature.add_feature(f, feature=opening, element=element)
        return opening

    def add_void_profile(self, element_guid, matrix, axis, side, face, ring, depth, name, recess=False):
        """An empty opening or niche of any outline (a line drew it on the face, 0.58): the polygon
        `ring` — [(i, j)] points in order, i and j the two axes of the element's frame `matrix`
        other than `axis` — on the element's face at `face` across `axis` (side: +1 the face at its
        high end, -1 at its low end), cut `depth` (m) into it. It starts 1 cm outside the face."""
        f, margin = self.file, 0.01
        element = self.by_guid(element_guid) if isinstance(element_guid, str) else element_guid
        i, j = [k for k in range(3) if k != axis]
        e = np.eye(3)
        inward = -side * e[axis]
        x_axis, y_axis, pts = e[i], e[j], [(float(p[0]), float(p[1])) for p in ring]
        if float(np.cross(x_axis, y_axis) @ inward) < 0:                # (a right-handed frame: swap i and j)
            x_axis, y_axis, pts = e[j], e[i], [(b, a) for a, b in pts]
        local = np.eye(4)
        local[:3, 0], local[:3, 1], local[:3, 2] = x_axis, y_axis, inward
        local[axis, 3] = face + side * margin
        u = 1.0 / self.unit_scale
        coords = [(a * u, b * u) for a, b in pts] + [(pts[0][0] * u, pts[0][1] * u)]
        if f.schema == "IFC2X3":
            curve = f.createIfcPolyline([f.createIfcCartesianPoint(p) for p in coords])
        else:
            curve = f.createIfcIndexedPolyCurve(f.createIfcCartesianPointList2D(coords), None, False)
        solid = f.createIfcExtrudedAreaSolid(
            f.createIfcArbitraryClosedProfileDef("AREA", None, curve),
            f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)),
                                        f.createIfcDirection((0.0, 0.0, 1.0)), f.createIfcDirection((1.0, 0.0, 0.0))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float((depth + margin) * u))
        body = f.createIfcShapeRepresentation(self.body, self.body.ContextIdentifier, "SweptSolid", [solid])
        opening = api.root.create_entity(f, ifc_class="IfcOpeningElement", name=name,
                                         predefined_type="RECESS" if recess else "OPENING")
        api.geometry.assign_representation(f, product=opening, representation=body)
        self._place(opening, matrix @ local)
        api.feature.add_feature(f, feature=opening, element=element)
        return opening

    def host_wall(self, guid):
        """The wall a door/window sits in (via its opening), or None."""
        e = self.by_guid(guid)
        for rel in getattr(e, "FillsVoids", None) or ():
            opening = rel.RelatingOpeningElement
            for void in opening.VoidsElements or ():
                return void.RelatingBuildingElement.GlobalId
        return None

    def affected_walls(self, guids):
        """Walls whose shape changes when these elements are removed (their doors/windows)."""
        walls = {self.host_wall(g) for g in guids} - {None}
        for g in guids:                                     # (0.531) the walls a piece cuts get whole again
            if self._is_structure(self.by_guid(g)):
                walls |= set(self._walls_cut_by(g))
        return sorted(walls - set(guids))

    def remove(self, guids):
        """Remove elements. A door/window takes its opening with it; a wall takes
        its openings and the doors/windows in them."""
        f = self.file
        if self.file.by_type("IfcReinforcingBar"):                         # (a member takes its bars, 0.166)
            self.remove_rebars(guids)
        self.drop_structure_cuts(guids)                                     # (0.531) its cuts in the walls
        for guid in guids:
            element = self.by_guid(guid)
            if element is None:
                continue
            if getattr(self, "removed_storeys", None) is not None:
                storey = self.storey_of(guid) or (self.space_storey(guid) if element.is_a("IfcSpace") else None)
                if storey:
                    self.removed_storeys.add(storey)          # (its rooms are found again, 0.99)
            for rel in list(getattr(element, "FillsVoids", None) or ()):
                api.root.remove_product(f, product=rel.RelatingOpeningElement)
            for rel in list(getattr(element, "HasOpenings", None) or ()):
                opening = rel.RelatedOpeningElement
                for fill in list(opening.HasFillings or ()):
                    api.root.remove_product(f, product=fill.RelatedBuildingElement)
                api.root.remove_product(f, product=opening)
            for rel in list(getattr(element, "IsNestedBy", None) or ()):      # a pipe's / bend's ports (0.74)
                for port in [o for o in rel.RelatedObjects if o.is_a("IfcDistributionPort")]:
                    api.root.remove_product(f, product=port)
            if self.kind_of(guid) == "gutter":
                self.drop_downpipes(guid)                                   # (its downpipes with it, 0.438)
            if element.is_a("IfcWall"):
                self.drop_framing(guid)                                     # (its light frame with it, 0.437)
            if element.is_a("IfcRoof"):
                self.drop_carpentry(guid)                                   # (its carpentry with it, 0.276)
                self.drop_tiles(guid)                                       # (its tiles, 0.279: while tied to it)
            hosted = [c for rel in (getattr(element, "HasCoverings", None) or ()) for c in rel.RelatedCoverings
                      if self._params(c).get("Elemento") == "tiled_covering"]      # (0.564: its Revestimentos go
            self.uncover(element)                                           # with it, as Revit's hosted ones)
            for c in hosted:                                                # (a wall's finishes' ties, 0.119)
                if self.by_guid(c.GlobalId) is not None:
                    self.uncover(c)
                    api.root.remove_product(f, product=c)
            if self.by_guid(guid) is not None:
                api.root.remove_product(f, product=element)
        self.remove_empty_groups()

    def by_guid(self, guid):
        try:
            return self.file.by_guid(guid)
        except RuntimeError:
            return None

    def _element_types(self):
        """Names of the displayable element classes of this schema (IfcElement and subtypes,
        openings and the like excluded), computed once."""
        if getattr(self, "_element_type_names", None) is None:
            schema = ifcopenshell.ifcopenshell_wrapper.schema_by_name(self.file.schema)

            def below(name):
                try:
                    stack = [schema.declaration_by_name(name)]
                except Exception:
                    return set()
                names = set()
                while stack:
                    d = stack.pop()
                    names.add(d.name())
                    stack += list(d.subtypes())
                return names

            excluded = set().union(*(below(c) for c in DISPLAY_EXCLUDE))
            self._element_type_names = below("IfcElement") - excluded
        return self._element_type_names

    def last_changes(self, undone=False):
        """(created, deleted): GlobalIds of displayable elements the last transaction
        made and removed (the transaction just undone, reversed, if undone=True);
        None if the IFC library did not record it. Lets the document update only
        what an action touched instead of scanning the whole model."""
        try:
            transaction = self.file.future[-1] if undone else self.file.history[-1]
            operations = list(transaction.operations)
        except (AttributeError, IndexError, TypeError):
            return None
        types = self._element_types()
        kind = {}                 # entity id -> class, for the entities the transaction made or removed
        before, now = {}, {}      # entity id -> GlobalId before / after the transaction
        born, died = set(), set()
        for op in operations:
            if not isinstance(op, dict):
                return None
            action = op.get("action")
            if action in ("create", "delete"):
                value = op.get("value") or {}
                eid = value.get("id")
                kind[eid] = value.get("type")
                if action == "create":
                    born.add(eid)
                    now[eid] = value.get("GlobalId")          # often still empty: set by a later edit
                else:
                    died.add(eid)
                    before.setdefault(eid, value.get("GlobalId"))
                    now.pop(eid, None)
            elif action == "edit" and op.get("index") == 0:     # attribute 0 of an IfcRoot: its GlobalId
                eid = op.get("id")
                if eid not in kind:
                    e = self._by_id(eid)
                    kind[eid] = e.is_a() if e is not None else None
                    before.setdefault(eid, op.get("old"))
                now[eid] = op.get("new")
        made, gone = set(), set()
        for eid, cls in kind.items():
            if cls not in types:
                continue
            old, new = (before.get(eid) if eid not in born else None), (now.get(eid) if eid not in died else None)
            if old != new:
                if new:
                    made.add(new)
                if old:
                    gone.add(old)
        return (gone, made) if undone else (made, gone)

    def _by_id(self, eid):
        try:
            return self.file.by_id(eid)
        except RuntimeError:
            return None

    def displayable_elements(self):
        """Elements that may have a 3D body (walls, slabs, columns, doors... from any program).

        Run after every change, so kept cheap: classes are excluded by entity id
        (no per-element questions to the IFC library, ~3 ms instead of ~9 ms for
        3 000 elements). Elements that turn out to have no geometry are simply
        absent from triangulate()'s result (the document remembers them)."""
        skip = set()
        for cls in DISPLAY_EXCLUDE:
            try:
                skip.update(e.id() for e in self.file.by_type(cls))
            except RuntimeError:
                pass                                   # a class this schema does not have
        return [e for e in self.file.by_type("IfcElement") if e.id() not in skip]

    # ------------------------------------------------------------ geometry for display

    @staticmethod
    def kernel_key():
        """What the shapes depend on besides the file and the origin: the kernel version and our
        settings (a geometry cache made with something else is not used). Known before the
        file is read, so a cache can be checked — and shown — first."""
        return "ifcopenshell {}; use-world-coords; weld-vertices; 2".format(ifcopenshell.version)

    def geometry_key(self):
        return self.kernel_key()

    def _settings(self):
        s = ifcopenshell.geom.settings()
        s.set("use-world-coords", True)
        s.set("weld-vertices", True)
        return s

    def triangulate(self, guids=None, elements=None, progress=None, cancelled=None, chunk=None, colours=None):
        """{guid: (vertices (N, 3) in meters in the program's coordinates, triangles (T, 3))}.

        Many elements are triangulated in parallel (one thread per CPU core), as
        required for large models; a few (an edit) one by one, which avoids the
        cost of starting the threads (~40 ms against 2–8 ms per wall).
        `elements`: the displayable elements, when the caller already has them.
        Opening a file in the background: progress(percent) is called now and then,
        and when cancelled() says yes, Cancelled is raised; chunk({guid: (verts, tris)})
        gets the shapes made so far, the first after 0,3 s then less and less often
        (so a big model can be shown as it comes).
        colours (0.259): a dict given to be filled with {guid: each triangle's colour (T, 3)} of the elements made
        of parts of several materials (COLOURED: a railing), from their pieces' styles.
        """
        if guids is not None and elements is None:
            # straight to the elements asked for (no scan of the whole model)
            types = self._element_types()
            elements = [e for e in (self.by_guid(g) for g in guids) if e is not None and e.is_a() in types]
        else:
            if elements is None:
                elements = self.displayable_elements()
            if guids is not None:
                wanted = set(guids)
                elements = [e for e in elements if e.GlobalId in wanted]
        out = {}
        if not elements:
            return out
        # (0.173) a body that is already triangles (a terrain, a perforated sheet): read as it is, not through the
        # kernel — which makes a face of each triangle (45 s for 150 000)
        kernel = []
        for e in elements:
            mesh = self._direct_mesh(e)
            if mesh is None:
                kernel.append(e)
            elif len(mesh[1]):
                out[e.GlobalId] = mesh
                # (0.276: a carpentry piece, its wood; 0.279: a roof's tiles, their clay)
                if colours is not None and (e.is_a() in COLOURED or (
                        e.is_a("IfcCovering") and (ifcopenshell.util.element.get_predefined_type(e) == "ROOFING"
                                                   or self._params(e).get("Elemento") == "tiled_covering"))):
                    # (0.563: a Revestimento's pieces, bed and grout, each its own)
                    painted = self._styled_colours(e, len(mesh[1]))         # (0.288: a door's pieces, each its own)
                    rgb = _material_colour(e) if painted is None else None
                    if painted is not None:
                        colours[e.GlobalId] = painted
                    elif rgb is not None:
                        colours[e.GlobalId] = np.tile(np.asarray(rgb, dtype=float), (len(mesh[1]), 1))
                elif colours is not None and (e.is_a() in COMPONENT_OCCURRENCES or (    # (0.351: a 3D file's, its
                        e.is_a() in SURFACE_CLASSES and self.kind_of(e.GlobalId) == "param_surface")):  # colours;
                    painted = self._styled_colours(e, len(mesh[1]))           # 0.395: a parametric surface's pieces)
                    if painted is not None:
                        colours[e.GlobalId] = painted
        if chunk is not None and out:
            chunk(dict(out))
        elements = kernel
        if not elements:
            return out
        # (0.257) a stair's flights and landings: one surface, no seams where they meet (core/mesh.planar_union)
        joined = {e.GlobalId for e in elements if e.is_a("IfcStair")       # (0.262: and a roof by blocks)
                  or (e.is_a("IfcRoof") and self._params(e).get("Forma") == "blocks")}
        painted = {e.GlobalId for e in elements if e.is_a() in COLOURED or (           # (0.390: an organic roof's
            e.is_a("IfcRoof") and self._params(e).get("Elemento") == "organic_roof") or (  # bars, glass, supports;
            e.is_a("IfcFurniture") and self._params(e).get("Elemento") == "loose")} \
            if colours is not None else set()                                          # 0.440: loose furniture)
        if len(elements) <= FEW_ELEMENTS:
            settings = self._settings()
            for e in elements:
                try:
                    shape = ifcopenshell.geom.create_shape(settings, e)
                except RuntimeError:
                    continue                    # no geometry the kernel can make (as the iterator skips it)
                verts = np.array(shape.geometry.verts, dtype=float).reshape(-1, 3) - self.origin
                tris = np.array(shape.geometry.faces, dtype=np.int64).reshape(-1, 3)
                if len(tris):
                    out[e.GlobalId] = planar_union(verts, tris) if e.GlobalId in joined else (verts, tris)
                    if e.GlobalId in painted:
                        colours[e.GlobalId] = _triangle_colours(shape.geometry, len(tris))
            return out
        it = ifcopenshell.geom.iterator(self._settings(), self.file, max(1, os.cpu_count() or 1), include=elements)
        if it.initialize():
            count = 0
            pending, interval, last = {}, CHUNK_FIRST, time.perf_counter()
            while True:
                shape = it.get()
                verts = np.array(shape.geometry.verts, dtype=float).reshape(-1, 3) - self.origin
                tris = np.array(shape.geometry.faces, dtype=np.int64).reshape(-1, 3)
                if len(tris):
                    out[shape.guid] = planar_union(verts, tris) if shape.guid in joined else (verts, tris)
                    if shape.guid in painted:
                        colours[shape.guid] = _triangle_colours(shape.geometry, len(tris))
                    if chunk is not None:
                        pending[shape.guid] = out[shape.guid]
                count += 1
                if count % 50 == 0:
                    if cancelled is not None and cancelled():
                        raise Cancelled()
                    if progress is not None:
                        progress(it.progress())
                    if chunk is not None and pending and time.perf_counter() - last > interval:
                        chunk(pending)
                        pending, last, interval = {}, time.perf_counter(), min(interval * 2, CHUNK_MAX)
                if not it.next():
                    break
            if chunk is not None and pending:
                chunk(pending)
        return out

    def _direct_mesh(self, e):
        """(vertices, triangles) of an element whose body is only IfcTriangulatedFaceSets placed as they are (no
        openings cut in it, no mapped items) — read from the file (program coordinates); None for any other."""
        if getattr(e, "HasOpenings", None) or not e.Representation:
            return None
        body = [r for r in e.Representation.Representations if r.RepresentationIdentifier == "Body"]
        if len(body) == 1 and body[0].Items and all(i.is_a("IfcMappedItem") for i in body[0].Items):
            return self._mapped_mesh(e, body[0].Items)
        if len(body) != 1 or not body[0].Items or not all(i.is_a("IfcTriangulatedFaceSet") for i in body[0].Items):
            return None
        m = self._placement_si(e)
        s = self.unit_scale
        verts, tris, count = [], [], 0
        for item in body[0].Items:
            pts = np.array(item.Coordinates.CoordList, dtype=float) * s
            if item.PnIndex:
                pts = pts[np.array(item.PnIndex, dtype=np.int64) - 1]
            idx = np.array(item.CoordIndex, dtype=np.int64).reshape(-1, 3) - 1
            verts.append(pts @ m[:3, :3].T + m[:3, 3])
            tris.append(idx + count)
            count += len(pts)
        return np.concatenate(verts), np.concatenate(tris)

    def _styled_colours(self, e, n):
        """(0.288) Each triangle's colour (n, 3) of a body of IfcTriangulatedFaceSets read as it is (_direct_mesh)
        from each one's own style (a door's frame, leaves, glass) — None if none is styled. (0.351) A component's copy
        (one mapped item): its type's face sets'."""
        body = next((r for r in e.Representation.Representations if r.RepresentationIdentifier == "Body"), None)
        items = body.Items if body is not None else ()
        if len(items) == 1 and items[0].is_a("IfcMappedItem"):
            items = items[0].MappingSource.MappedRepresentation.Items
        if not items or not all(i.is_a("IfcTriangulatedFaceSet") for i in items):
            return None
        found = [_item_colour(i) for i in items]
        if all(c is None for c in found):
            return None
        fallback = _material_colour(e) or UNSTYLED
        out = np.concatenate([np.tile(np.asarray(c or fallback, dtype=float), (len(i.CoordIndex), 1))
                              for c, i in zip(found, items)])
        return out if len(out) == n else None

    def _mapped_mesh(self, e, items):
        """(0.279) (vertices, triangles) of a body of mapped items — a roof's tiles: one tile's shape, a thousand
        places — whose maps are IfcTriangulatedFaceSets at their origin, mapped without scaling; None for any other
        (the kernel's)."""
        s = self.unit_scale
        shapes, places, axes_of = {}, {}, {}
        for item in items:
            source, target = item.MappingSource, item.MappingTarget
            key = source.id()
            if key not in shapes:
                origin = source.MappingOrigin
                if not origin.is_a("IfcAxis2Placement3D") or origin.Axis is not None or \
                        origin.RefDirection is not None or any(abs(c) > 1e-12 for c in origin.Location.Coordinates):
                    return None
                faces = source.MappedRepresentation.Items
                if not faces or not all(i.is_a("IfcTriangulatedFaceSet") for i in faces):
                    return None
                pv, pt, n = [], [], 0
                for face in faces:
                    pts = np.array(face.Coordinates.CoordList, dtype=float) * s
                    if face.PnIndex:
                        pts = pts[np.array(face.PnIndex, dtype=np.int64) - 1]
                    pv.append(pts)
                    pt.append(np.array(face.CoordIndex, dtype=np.int64).reshape(-1, 3) - 1 + n)
                    n += len(pts)
                shapes[key] = (np.concatenate(pv), np.concatenate(pt))
                places[key] = ([], [])
            if not target.is_a("IfcCartesianTransformationOperator3D") or \
                    target.is_a("IfcCartesianTransformationOperator3DnonUniform") or \
                    abs((target.Scale if target.Scale is not None else 1.0) - 1.0) > 1e-9:
                return None
            directions = (target.Axis1, target.Axis2, target.Axis3)
            ids = tuple(d.id() if d is not None else 0 for d in directions)
            if ids not in axes_of:
                axes_of[ids] = _base_axes(*directions)
            places[key][0].append(axes_of[ids])
            places[key][1].append(np.array(target.LocalOrigin.Coordinates, dtype=float) * s)
        m = self._placement_si(e)
        verts, tris, count = [], [], 0
        for key, (pts, idx) in shapes.items():
            axes, origins = np.array(places[key][0]), np.array(places[key][1])
            local = np.einsum("vi,nij->nvj", pts, axes) + origins[:, None, :]
            verts.append(local.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3])
            tris.append((idx[None, :, :] + (np.arange(len(origins)) * len(pts))[:, None, None]).reshape(-1, 3)
                        + count)
            count += len(origins) * len(pts)
        return np.concatenate(verts), np.concatenate(tris)

    # ------------------------------------------------------------ information (properties panel, schedules)

    def plan_symbols(self, guids):
        """{GlobalId: (K, 2, 3) segments} of the elements that have a plan symbol (a 2D
        representation in a Plan context — a door's linings, open leaf and swing arc), in the
        program's coordinates. Elements without one are left out (they are drawn by their cut)."""
        settings = ifcopenshell.geom.settings()
        settings.set("use-world-coords", True)
        settings.set("dimensionality", ifcopenshell.ifcopenshell_wrapper.CURVES)
        out = {}
        for guid in guids:
            e = self.by_guid(guid)
            rep = self._symbol_rep(e)
            if rep is None:
                continue
            try:
                geometry = ifcopenshell.geom.create_shape(settings, e, rep).geometry
            except Exception:   # a curve the kernel cannot make: the element is drawn by its cut
                continue
            verts = np.array(geometry.verts, dtype=float).reshape(-1, 3) - self.origin
            edges = np.array(geometry.edges, dtype=np.int64).reshape(-1, 2)
            if len(edges):
                out[guid] = verts[edges]
        return out

    def has_plan_symbol(self, guid):
        """Quick (no geometry): does the element have a plan symbol (see plan_symbols)?"""
        return self._symbol_rep(self.by_guid(guid)) is not None

    @staticmethod
    def _symbol_rep(e):
        shape = getattr(e, "Representation", None) if e is not None else None
        for rep in (shape.Representations if shape is not None else ()):
            context = rep.ContextOfItems
            kind = context.ContextType or (getattr(context, "ParentContext", None) and
                                           context.ParentContext.ContextType)
            if kind == "Plan" and rep.RepresentationType in SYMBOL_TYPES:
                return rep
        return None

    def hatches(self, guids, own=True):
        """{GlobalId: "concrete" | "masonry" | "wood" | "insulation" | "gypsum" | None}: what each
        element is drawn with where it is cut, from its main material (of layers, the thickest) — (0.314) or
        MATERIAL_CUT + its name when that material has cut patterns of its own (cut_patterns); own False (0.315: a
        view style's): its category's always."""
        known = {}
        return {guid: (_cut_key(m, known) if own else _hatch_of(m))
                for guid, m in ((g, _main_material(self.by_guid(g))) for g in guids)}

    def cut_patterns(self, keys):
        """(0.314) {MATERIAL_CUT + name: (background, foreground)} — each (pattern, colour) or None — of the materials
        cut with patterns of their own."""
        names = {k[len(MATERIAL_CUT):]: k for k in keys if isinstance(k, str) and k.startswith(MATERIAL_CUT)}
        out = {}
        for m in self.file.by_type("IfcMaterial") if names else ():
            if m.Name in names and names[m.Name] not in out:
                own = _own_cut(m)
                if own is not None:
                    out[names[m.Name]] = own
        return out

    def property_keys(self):
        """The properties found in the file, to colour by: [(property set, property)], sorted —
        of the elements and of their types (ArqBIM's own parameters and quantities left out)."""
        found = set()
        for pset in self.file.by_type("IfcPropertySet"):
            if pset.Name and pset.Name != PARAM_PSET:
                found.update((pset.Name, p.Name) for p in pset.HasProperties or () if p.Name)
        return sorted(found, key=lambda k: (k[0].lower(), k[1].lower()))

    def property_values(self, guids, key):
        """{GlobalId: value or None} of what the elements are coloured by. key: ("class",),
        ("type",), ("storey",), ("material",), ("external",) / ("fire",) (IsExternal / FireRating of
        their Pset_…Common), ("pset", property set, property)."""
        out = {}
        for guid in guids:
            e = self.by_guid(guid)
            if e is None:
                continue
            kind = key[0]
            if kind == "class":
                value = e.is_a()
            elif kind == "type":
                type_ = ifcopenshell.util.element.get_type(e)
                value = (type_.Name or type_.is_a()) if type_ is not None else None
            elif kind == "storey":
                container = ifcopenshell.util.element.get_container(e)
                value = (container.Name or "") if container is not None else None
            elif kind == "material":
                material = _main_material(e)
                value = material.Name if material is not None else None
            elif kind == "ec3":                            # (0.517: an analysis's, not the file's — the window's)
                value = None
            else:
                psets = ifcopenshell.util.element.get_psets(e)
                if kind == "pset":
                    value = psets.get(key[1], {}).get(key[2])
                else:
                    prop = {"external": "IsExternal", "fire": "FireRating", "status": "Status"}[kind]
                    value = next((p[prop] for name, p in sorted(psets.items())
                                  if name.startswith("Pset_") and name.endswith("Common") and p.get(prop) is not None),
                                 None)
                    if kind == "status":
                        value = _status(value)
            out[guid] = value
        return out

    def property_templates(self, guid):
        """What can be added to an element: the properties of IFC4's standard property sets for its
        class that it does not have yet — [(property set, property, kind, choices)], kind "bool" |
        "text" | "integer" | "number" | "length" (metres here, the project's unit in the IFC) |
        "choice" (choices: the enumeration's values)."""
        import ifcopenshell.util.pset
        from .ifc_data import property_kind, property_name
        e = self.by_guid(guid)
        if e is None:
            return []
        templates = ifcopenshell.util.pset.get_template("IFC4")
        have = ifcopenshell.util.element.get_psets(e, psets_only=True)
        out = []
        for name in templates.get_applicable_names(e.is_a(), pset_only=True):
            template = templates.get_by_name(name)
            for prop in template.HasPropertyTemplates or ():
                prop_name = property_name(prop) if prop.is_a("IfcSimplePropertyTemplate") else None
                found = property_kind(prop) if prop_name else None      # (bounded values, tables…: not here)
                if found is None or prop_name in have.get(name, {}):
                    continue
                kind, choices = found
                out.append((name, prop_name, kind, list(choices) if choices else None))
        return out

    def set_status(self, guids, status):
        """The phase of elements — "EXISTING", "NEW", "DEMOLISH", "TEMPORARY", None to clear — as the
        IFC says it: the Status (PEnum_ElementStatus) of the element's Pset_…Common. Elements whose
        class has no such property set are left as they are; returns how many got it."""
        done = 0
        for guid in guids:
            e = self.by_guid(guid)
            name = _status_pset(e.is_a()) if e is not None else None
            if name is None:
                continue
            existing = ifcopenshell.util.element.get_psets(e, psets_only=True).get(name)
            if existing and existing.get("id") and self.file.by_id(existing["id"]) in _own_psets(e):
                pset = self.file.by_id(existing["id"])
            else:
                pset = api.pset.add_pset(self.file, product=e, name=name)
            old = next((p for p in pset.HasProperties or () if p.Name == "Status"), None)
            if not status:                                  # no phase: the property goes (its set too if emptied)
                if old is not None:
                    rest = [p for p in pset.HasProperties if p != old]
                    if rest:
                        pset.HasProperties = rest
                        self.file.remove(old)
                    else:
                        api.pset.remove_pset(self.file, product=e, pset=pset)
            else:                                           # enumerated, as IFC4 says (or as it was)
                value = status if old is not None and old.is_a("IfcPropertySingleValue") else [status]
                api.pset.edit_pset(self.file, pset=pset, properties={"Status": value})
            done += 1
        return done

    # (0.524) the Project navigator's controls (as Blender's Outliner): flags kept in the pset «ArqSynth_Controlo»,
    # only those switched on (a pset with none is taken away)
    CONTROL_PSET = "ArqSynth_Controlo"
    CONTROL_PROPS = {"locked": "Bloqueado", "hidden": "Oculto", "no_render": "NaoRenderizar",
                     "no_print": "NaoImprimir"}

    def controls_of(self, guid):
        """The flags switched on of one element (a set of CONTROL_PROPS' keys)."""
        e = self.by_guid(guid)
        if e is None:
            return set()
        found = ifcopenshell.util.element.get_psets(e, psets_only=True).get(self.CONTROL_PSET) or {}
        return {k for k, prop in self.CONTROL_PROPS.items() if found.get(prop)}

    def all_controls(self):
        """{GlobalId: set of flags} of every element that has one (read from the psets themselves, not element by
        element)."""
        names = {v: k for k, v in self.CONTROL_PROPS.items()}
        out = {}
        for pset in self.file.by_type("IfcPropertySet"):
            if pset.Name != self.CONTROL_PSET:
                continue
            flags = {names[p.Name] for p in pset.HasProperties or ()
                     if p.Name in names and p.is_a("IfcPropertySingleValue") and p.NominalValue is not None
                     and bool(p.NominalValue.wrappedValue)}
            if not flags:
                continue
            for rel in getattr(pset, "DefinesOccurrence", None) or ():
                for obj in rel.RelatedObjects or ():
                    out.setdefault(obj.GlobalId, set()).update(flags)
        return out

    def set_control(self, guids, flag, on):
        """A flag switched on / off on these elements; returns how many changed."""
        prop = self.CONTROL_PROPS[flag]
        done = 0
        for guid in guids:
            e = self.by_guid(guid)
            if e is None or bool(on) == (flag in self.controls_of(guid)):
                continue
            existing = ifcopenshell.util.element.get_psets(e, psets_only=True).get(self.CONTROL_PSET)
            if existing and existing.get("id"):
                pset = self.file.by_id(existing["id"])
            else:
                pset = api.pset.add_pset(self.file, product=e, name=self.CONTROL_PSET)
            api.pset.edit_pset(self.file, pset=pset, properties={prop: bool(on)})
            rest = {k for k, v in self.CONTROL_PROPS.items() if v != prop} & self.controls_of(guid)
            if not on and not rest:
                api.pset.remove_pset(self.file, product=e, pset=pset)
            elif not on:
                old = next((p for p in pset.HasProperties or () if p.Name == prop), None)
                if old is not None:
                    pset.HasProperties = [p for p in pset.HasProperties if p != old]
                    self.file.remove(old)
            done += 1
        return done

    def layers(self, guids, own=True, single=False):
        """{GlobalId: [(hatch, normal, d0, d1)]} of the elements made of 2+ material layers (a
        wall's plaster | block | plaster): each layer is the space d0 <= normal·p <= d1, in the
        program's coordinates, from the IfcMaterialLayerSetUsage (direction, sense, offset). single (0.320): those
        of one layer too (a concrete wall's thickness, for the joins of what is cut)."""
        out = {}
        known = {}                                 # (0.314: each material's cut asked for once)
        for guid in guids:
            spans = self._layer_spans(self.by_guid(guid))
            if spans is not None and len(spans) >= (1 if single else 2):
                out[guid] = [(_cut_key(material, known) if own else _hatch_of(material), n, d0, d1)
                             for material, n, d0, d1 in spans]
        return out

    def curved_layers(self, guids, own=True):
        """(0.460, the owner: «a parede curva não tem camadas de reboco. devia ter já que são mesmo tipo») {GlobalId:
        (centre (x, y), [(hatch, r0, r1)])} of the curved walls made of 2+ material layers: each layer the ring
        r0 <= |p - centre| <= r1 in the plan, from its IfcMaterialLayerSetUsage as a straight wall's (layers()) — its
        offsets along the left of the way it was drawn (turning counter-clockwise: towards the centre)."""
        out, known = {}, {}
        for guid in guids:
            try:
                if self.kind_of(guid) != "curved_wall":
                    continue
                e = self.by_guid(guid)
                usage = ifcopenshell.util.element.get_material(e, should_skip_usage=False)
                if usage is None or not usage.is_a("IfcMaterialLayerSetUsage"):
                    continue
                layers = usage.ForLayerSet.MaterialLayers or ()
                if len(layers) < 2:
                    continue
                centre, radius, _start, sweep, _h, _t = self.curved_wall_params(guid)
            except (KeyError, ValueError, TypeError, AttributeError):
                continue
            way = 1.0 if sweep >= 0 else -1.0
            s = self.unit_scale
            sense = -1.0 if usage.DirectionSense == "NEGATIVE" else 1.0
            at = (usage.OffsetFromReferenceLine or 0.0) * s
            rings = []
            for one in layers:
                step = sense * (one.LayerThickness or 0.0) * s
                r0, r1 = sorted((radius - way * at, radius - way * (at + step)))
                if r1 - r0 > 1e-6 and r0 >= 0.0:
                    rings.append((_cut_key(one.Material, known) if own else _hatch_of(one.Material), r0, r1))
                at += step
            if len(rings) >= 2:
                out[guid] = ((float(centre[0]), float(centre[1])), rings)
        return out

    def layer_strengths(self, guids):
        """(0.334) {GlobalId: [strength or None]} of the elements' layers, as layers() gives them: each one's function
        in its type (IfcMaterialLayer.Priority, catalog.LAYER_FUNCTIONS) as its strength where elements meet — 1 the
        structure … 5 the second finish —, None when not given (the program's: the thickest is the structure). Only
        the elements with a function given to some layer."""
        out = {}
        for guid in guids:
            spans = self._layer_spans(self.by_guid(guid), layer=True)
            if not spans:
                continue
            found = [catalog.function_of_priority(getattr(layer, "Priority", None)) for *_s, layer in spans]
            if any(found):
                out[guid] = [catalog.LAYER_FUNCTIONS[f][0] if f else None for f in found]
        return out

    def _layer_spans(self, e, layer=False):
        """[(IfcMaterial, normal, d0, d1)] of an element's material layers (d0 <= normal·p <= d1, the program's
        coordinates) from its IfcMaterialLayerSetUsage, or None (no layers). layer (0.334): each one's
        IfcMaterialLayer too, last."""
        usage = ifcopenshell.util.element.get_material(e, should_skip_usage=False) if e is not None else None
        if usage is None or not usage.is_a("IfcMaterialLayerSetUsage"):
            return None
        layers = usage.ForLayerSet.MaterialLayers or ()
        axis = {"AXIS1": 0, "AXIS2": 1, "AXIS3": 2}.get(usage.LayerSetDirection)
        if not layers or axis is None:
            return None
        s = self.unit_scale
        m = self._placement_si(e)
        n = m[:3, axis] / np.linalg.norm(m[:3, axis])
        sense = -1.0 if usage.DirectionSense == "NEGATIVE" else 1.0
        at = float(n @ m[:3, 3]) + (usage.OffsetFromReferenceLine or 0.0) * s
        spans = []
        for one in layers:
            step = sense * (one.LayerThickness or 0.0) * s
            d0, d1 = sorted((at, at + step))
            if d1 - d0 > 1e-6:
                spans.append((one.Material, n, d0, d1, one) if layer else (one.Material, n, d0, d1))
            at += step
        return spans

    def material_names(self, guid):
        """(0.317) The names of all an element's materials (its layers', its profile's, its parts', its own), quickly."""
        e = self.by_guid(guid)
        material = ifcopenshell.util.element.get_material(e, should_skip_usage=True) if e is not None else None
        if material is None:
            return []
        if material.is_a("IfcMaterialLayerSet"):
            found = [l.Material for l in material.MaterialLayers or ()]
        elif material.is_a("IfcMaterialProfileSet"):
            found = [p.Material for p in material.MaterialProfiles or ()]
        elif material.is_a("IfcMaterialConstituentSet"):
            found = [c.Material for c in material.MaterialConstituents or ()]
        elif material.is_a("IfcMaterialList"):
            found = list(material.Materials or ())
        else:
            found = [material] if material.is_a("IfcMaterial") else []
        return [m.Name for m in found if m is not None and m.Name]

    def layer_bands(self, guid):
        """(0.315) [(material name or None, normal, d0, d1)] of an element made of 2+ layers, or None."""
        spans = self._layer_spans(self.by_guid(guid))
        if not spans or len(spans) < 2:
            return None
        return [(m.Name if m is not None else None, n, d0, d1) for m, n, d0, d1 in spans]

    def face_materials(self, guid, centres, normals):
        """(0.315) Each triangle's material of an element — given its triangles' middles and normals (T, 3): (the
        materials' names, each triangle's index in them, -1 for none). Of layers, the layer the triangle lies on, a
        hair inside its face (a wall's outer face: its plaster; its top: the layer under its middle); else its one
        material (of a profile, its first; of parts, the first)."""
        e = self.by_guid(guid)
        count = len(centres)
        if e is None:
            return [], np.full(count, -1, dtype=np.int64)
        spans = self._layer_spans(e)
        if spans:
            n = spans[0][1]
            depth = (np.asarray(centres, dtype=float) - np.asarray(normals, dtype=float) * 1e-4) @ n
            lows = np.array([d0 for _m, _n, d0, _d1 in spans])
            highs = np.array([d1 for _m, _n, _d0, d1 in spans])
            gap = np.maximum(lows[None, :] - depth[:, None], depth[:, None] - highs[None, :])   # (inside: <= 0)
            which = np.argmin(gap, axis=1)
            names = []
            index = np.empty(count, dtype=np.int64)
            for k, (material, *_r) in enumerate(spans):
                name = material.Name if material is not None else None
                if name is None:
                    index[which == k] = -1
                    continue
                if name not in names:
                    names.append(name)
                index[which == k] = names.index(name)
            return names, index
        material = _main_material(e)
        if material is None or not material.Name:
            return [], np.full(count, -1, dtype=np.int64)
        return [material.Name], np.zeros(count, dtype=np.int64)

    def schedule_info(self, guids):
        """What a schedule lists of these elements, quickly (no geometry worked out):
        {GlobalId: {"name", "type", "storey", "kind", "length", "height", "thickness", "width",
        "host"}} — lengths in metres from the base quantities (ArqBIM writes them; so do Revit
        and ArchiCAD), None where the file does not say."""
        s = self.unit_scale
        out = {}
        for guid in guids:
            e = self.by_guid(guid)
            if e is None:
                continue
            psets = ifcopenshell.util.element.get_psets(e)
            qto = next((v for k, v in psets.items() if k.startswith("Qto_") and k.endswith("BaseQuantities")), {})

            def q(*names):
                for n in names:
                    if isinstance(qto.get(n), (int, float)):
                        return float(qto[n]) * s
                return None

            type_ = ifcopenshell.util.element.get_type(e)
            container = ifcopenshell.util.element.get_container(e)
            kind = psets.get(PARAM_PSET, {}).get("Elemento")
            row = {"name": e.Name or "", "type": type_.Name if type_ else "",
                   "storey": container.Name if container else "", "kind": kind,
                   "length": q("Length"), "height": q("Height"), "thickness": q("Width", "Depth"),
                   "width": None, "host": ""}
            if e.is_a("IfcColumn"):
                row["height"], row["length"] = row["length"], None      # a column's "Length" is its height
            if e.is_a("IfcRoof"):                                       # (0.265) its areas; by blocks: its edges
                from .roofs import EDGE_COLUMNS, EDGE_NAMES, EDGE_QTO
                for column, name in (("area", "GrossArea"), ("projected", "ProjectedArea")):    # (in m², as written)
                    row[column] = float(qto[name]) if isinstance(qto.get(name), (int, float)) else None
                thickness = psets.get(PARAM_PSET, {}).get("Espessura")
                if row["area"] is not None and isinstance(thickness, (int, float)):
                    row["volume"] = row["area"] * float(thickness)  # (each water upright t/cos: t × its sloped area)
                lengths = psets.get(EDGE_QTO, {})
                for k, n in EDGE_NAMES.items():
                    row[EDGE_COLUMNS[k]] = float(lengths[n]) * s if n in lengths else None
            if getattr(e, "OverallWidth", None) and getattr(e, "OverallHeight", None):
                row["width"], row["height"] = e.OverallWidth * s, e.OverallHeight * s
                row["thickness"] = None
                host = self.host_wall(guid)
                row["host"] = (self.by_guid(host).Name or "") if host else ""
            out[guid] = row
        return out

    def describe(self, guid):
        """Plain dict with what the properties panel shows."""
        e = self.by_guid(guid)
        if e is None:
            return None
        type_ = ifcopenshell.util.element.get_type(e)
        info = {"class": e.is_a(), "name": e.Name or "", "guid": e.GlobalId,
                "type": type_.Name if type_ else "", "layers": [], "profile": None, "psets": {}}
        # skip the *Usage wrapper (occurrence) to reach the layer / profile set itself
        material = ifcopenshell.util.element.get_material(e, should_skip_usage=True)
        scale = self.unit_scale
        if material is not None and material.is_a("IfcMaterialLayerSet"):
            info["layers"] = [(l.Material.Name if l.Material else "?", l.LayerThickness * scale)
                              for l in material.MaterialLayers]
        elif material is not None and material.is_a("IfcMaterialProfileSet"):
            p = material.MaterialProfiles[0]
            prof = p.Profile
            from ..core import steel
            if steel.is_steel_profile(prof):                            # (0.494) a steel piece: its section, its weight
                sec = steel.from_ifc(prof, scale)
                weight = ifcopenshell.util.element.get_psets(e).get(
                    {"IfcBeam": "Qto_BeamBaseQuantities", "IfcColumn": "Qto_ColumnBaseQuantities",
                     "IfcMember": "Qto_MemberBaseQuantities"}.get(e.is_a(), ""), {}).get("NetWeight")
                if sec is not None:
                    info["steel"] = (steel.display(sec.name), p.Material.Name if p.Material else "?",
                                     steel.properties(sec.name)["mass"], weight)
                    info["steel_mark"] = getattr(e, "Tag", None) or ""          # (0.500: its part mark)
            elif prof.is_a("IfcCircleProfileDef"):                      # (a pipe, a round column: its diameter)
                info["profile"] = (p.Material.Name if p.Material else "?", 2 * prof.Radius * scale, None)
            elif prof.is_a() in ("IfcRectangleProfileDef", "IfcLShapeProfileDef", "IfcTShapeProfileDef"):
                w, d, _area, _p = profile_size(prof)                    # (an L, a T: their outer sizes, 0.97)
                info["profile"] = (p.Material.Name if p.Material else "?", w * scale, d * scale)
        container = ifcopenshell.util.element.get_container(e)
        info["storey"] = container.Name if container else ""
        info["status"] = self.property_values([guid], ("status",)).get(guid)     # its phase
        info["can_status"] = _status_pset(e.is_a()) is not None
        width, height = getattr(e, "OverallWidth", None), getattr(e, "OverallHeight", None)
        info["size"] = (width * scale, height * scale) if width and height else None
        host = self.host_wall(guid)
        info["host"] = self.by_guid(host).Name if host else ""
        info["keynote"] = self.keynote_of(guid)                         # (0.194) (code, text) or None
        # parameters the properties panel can edit (elements made by ArqBIM only)
        kind = self.kind_of(guid)
        info["kind"], info["params"] = kind, {}
        if kind == "component":
            type_guid = self.component_type(guid)
            info["instances"] = len(self.component_instances(type_guid)) if type_guid else 1
        try:
            if kind == "wall":
                length, h, t = self.wall_params(guid)
                info["params"] = {"length": length, "height": h, "thickness": t,
                                  "profiled": self.wall_profile(e) is not None}             # (0.109)
                if self.framing_of(guid) is not None:                   # (0.437) its light frame
                    info["params"].update(framing=self.framing_settings(guid),
                                          framing_summary=self.framing_summary(guid))
                info["constraints"] = self.constraints(guid)            # (0.73)
            elif kind == "slab":
                x0, y0, x1, y1, t = self.slab_extents(guid)
                info["params"] = {"lx": x1 - x0, "ly": y1 - y0, "thickness": t, "shape": self.slab_shape(guid),
                                  "function": self.slab_function(guid),
                                  "use": self.slab_use(guid)}                        # (0.218)
                outline = self.slab_outline(guid)                       # (0.100: a polygon, a circle)
                if outline is not None:
                    info["params"].update(area=outline["area"], perimeter=outline["perimeter"],
                                          radius=outline["radius"], thickness=outline["thickness"],
                                          corners=len(outline["outline"]) if outline["radius"] is None else 0,
                                          heights=outline.get("heights"))           # (0.433: its slope)
            elif kind == "ceiling":                                     # (0.118)
                cp = self.ceiling_params(guid)
                storey = self.storey_of(guid)
                level = next((z for g, _n, z in self.storeys() if g == storey), 0.0)
                q = ifcopenshell.util.element.get_psets(e).get("Qto_CoveringBaseQuantities", {})
                pp = self._params(e)
                info["params"] = {"style": cp["style"], "height": cp["z"] - level,
                                  "area": float(q.get("GrossArea") or 0.0),
                                  "gap": float(pp.get("Rasgo") or 0.0),                 # (0.119)
                                  "bulkhead": float(pp.get("SancaLargura") or 0.0),
                                  "drop": float(pp.get("SancaAltura") or 0.0)}
            elif kind == "ripado_screen":                               # (0.441) a free-standing slatted screen
                sp = self.screen_params(guid)
                info["params"] = {k: v for k, v in sp.items() if k not in ("start", "end")}
            elif kind == "loose":                                       # (0.440) a piece of loose furniture
                info["params"] = self.loose_params(guid)
            elif kind == "tiled_covering":                              # (0.563) a Revestimento: its finish, layout
                tp = self.tiled_params(guid)
                pg = ifcopenshell.util.element.get_psets(e).get("ArqSynth_Paginacao", {})
                q = ifcopenshell.util.element.get_psets(e).get("Qto_CoveringBaseQuantities", {})
                info["params"] = dict(tp, layout=dict(tp["layout"]), extras=self.tiled_extras(guid),
                                      extend=self.tiled_extend(guid), subframe=self.tiled_subframe(guid),
                                      area=float(q.get("NetArea") or 0.0),
                                      gross=float(q.get("GrossArea") or 0.0),       # (m², as written)
                                      pieces=int(pg.get("Pecas") or 0), whole=int(pg.get("PecasInteiras") or 0),
                                      cut=int(pg.get("PecasCortadas") or 0), narrow=int(pg.get("CortesEstreitos") or 0),
                                      narrowest=float(pg.get("CorteMaisEstreito") or 0.0))
            elif kind == "gutter":                                      # (0.438) its section, its downpipes
                info["params"] = {"shape": self.gutter_shape(guid), "downpipes": self.gutter_downpipes(guid)}
            elif kind == "flooring":                                    # (0.415) a floor finish: its finish
                pp = self._params(e)
                q = ifcopenshell.util.element.get_psets(e).get("Qto_CoveringBaseQuantities", {})
                info["params"] = {"finish": pp.get("Acabamento") or "ceramico",
                                  "thickness": float(pp.get("Espessura") or 0.0),
                                  "area": float(q.get("GrossArea") or 0.0) * scale * scale}
            elif kind == "roof_tiles":                                  # (0.279) a roof's tiles
                roof = self._params(e).get("Cobertura")
                info["params"] = dict(self.tiles_summary(roof) or {}, roof=roof,
                                      roof_name=(self.by_guid(roof).Name or "") if roof and self.by_guid(roof) else "")
            elif kind == "cladding":                                    # (0.119) a wall's finish
                pp = self._params(e)
                q = ifcopenshell.util.element.get_psets(e).get("Qto_CoveringBaseQuantities", {})
                wall = self.by_guid(pp["Parede"]) if pp.get("Parede") else None
                info["params"] = {"finish": pp.get("Acabamento") or "azulejo", "height": float(pp.get("Altura") or 0.0),
                                  "area": float(q.get("NetArea") or 0.0),
                                  "wall": wall.Name if wall is not None else ""}
                layer, under = self.cladding_layer(guid)                 # (0.178) its layer on the face
                info["params"].update(layer=layer, under=[self.by_guid(g).Name or "" for g in under])
                if wall is not None:                                     # (0.389) the rectangle it covers
                    frame = self.element_frame(wall.GlobalId)
                    x0, z0, x1, z1 = self.cladding_box(pp, frame)
                    info["params"].update(start=x0 - frame.x0, end=x1 - frame.x0, base=z0, top=z1,
                                          whole=pp.get("Inicio") is None and pp.get("Fim") is None
                                          and not pp.get("Base"))
                if info["params"]["finish"] in ("ripado", "canelado", "perfurado", "ondulado"):   # (0.173) its pattern
                    info["params"]["pattern"] = self.pattern_params(guid)
            elif kind == "organic_roof":                                # (0.390) its form, its pieces, how much
                info["params"] = dict(self.organic_params(guid))
                info["params"].pop("outline", None)
                info["params"]["base"] = float(self._placement_si(e)[2, 3])
                from .edit import EditRefused
                try:
                    info["params"].update(self.organic_summary(guid))
                except EditRefused:
                    pass
            elif kind == "param_surface":                               # (0.395) its definition and what it made
                info["params"] = {"definition": self.surface_definition(guid), "usage": self.surface_usage(guid),
                                  "summary": self.surface_summary(guid)}
            elif kind in ("steel_part", "steel_connection"):            # (0.497) a part of a steel connection
                found = self.connection_params(guid)
                if found is not None:
                    connection, members, values = found
                    info["params"] = dict(values, connection=connection,
                                          members=[self.by_guid(m).Name if self.by_guid(m) else "?" for m in members],
                                          warnings=self.connection_warnings(guid))
            elif kind == "steel_member":                                # (0.495) a steel piece between two points
                sp = self.steel_member_params(guid)
                info["params"] = {"length": sp["length"], "function": sp["function"], "cardinal": sp["cardinal"],
                                  "rotation": sp["rotation"], "start_z": float(sp["start"][2]),
                                  "end_z": float(sp["end"][2])}
            elif kind == "light":                                       # (0.119)
                info["params"] = {"light": self._params(e).get("Luminaria") or "panel"}
            elif kind == "profile":                                     # (0.174) a skirting, a cornice…
                pp = self.profile_params(guid)
                info["params"] = {k: pp[k] for k in ("profile", "width", "height", "foot", "side", "length")}
                info["params"]["room"] = pp["room"] is not None
                info["params"]["own"] = sorted(self.custom_profiles())          # (0.245: the project's own)
            elif kind == "curtain_wall":                                # (0.117)
                cp = self.curtain_params(guid)
                info["params"] = {k: cp[k] for k in ("length", "height", "mullions", "transoms")}
                kinds = list(cp["panels"].values())                     # (0.181) the cells that are not glass
                info["params"]["panels"] = {k: kinds.count(k) for k in ("solid", "door", "empty") if k in kinds}
                info["params"]["embed"] = self.embeds(guid)              # (0.188) into the wall it lies in
                if e.FillsVoids:                                          # …and where it is in it
                    st = self.curtain_filling_state(guid)
                    f = st["frame"]
                    info["params"].update(from_start=st["s"] - f.x0, to_end=f.x0 + f.length - st["s"] - st["width"])
            elif kind == "railing":                                     # (0.115)
                rp = self.railing_params(guid)
                q = ifcopenshell.util.element.get_psets(e).get("Qto_RailingBaseQuantities", {})
                info["params"] = {"height": rp["height"], "style": rp["style"], "closed": rp["closed"],
                                  "length": float(q.get("Length") or 0.0) * self.unit_scale,
                                  "type": rp["type"], "type_name": rp["rtype"].name,          # (0.258)
                                  "types": self.railing_type_choices(),
                                  "extend": rp["extend"]}                                     # (0.282)
            elif kind == "stair":                                       # (0.114)
                from ..core import stairs as core_stairs
                sp = self.stair_params(guid)
                n, h = core_stairs.risers(sp["rise"])
                info["params"] = dict(sp, risers=n, riser=h, treads=core_stairs.treads(sp["form"], sp["rise"]))
            elif kind == "roof":                                        # (0.111)
                from .roofs import EDGE_NAMES, EDGE_QTO
                rp = self.roof_params(guid)
                psets = ifcopenshell.util.element.get_psets(e)
                q = psets.get("Qto_RoofBaseQuantities", {})
                lengths = psets.get(EDGE_QTO, {})                       # (0.265) a roof by blocks' edges
                info["params"] = {"form": rp["form"], "slope": rp["slope"], "overhang": rp["overhang"],
                                  "eave": rp["eave"], "thickness": rp["thickness"], "spec": rp["spec"],
                                  "area": float(q.get("GrossArea") or 0.0),
                                  "projected": float(q.get("ProjectedArea") or 0.0),
                                  "blocks": len(rp["blocks"]),                              # (0.262)
                                  "carpentry": self.carpentry_summary(guid),                # (0.276)
                                  "tiles": self.tiles_summary(guid),                        # (0.279)
                                  "tile_specs": list(core_tiles.TILES.values()) + list(self.tile_types().values()),
                                  "pitched": rp["form"] == "blocks" or (rp["form"] not in ("flat", "butterfly",
                                                                                          "barrel", "custom")
                                                                        and any(rp["sloping"])),
                                  "edges": {k: float(lengths[n]) * self.unit_scale for k, n in EDGE_NAMES.items()
                                            if n in lengths}}
            elif kind == "curved_wall":                                 # (0.103)
                _c, radius, _s, sweep, h, t = self.curved_wall_params(guid)
                info["params"] = {"radius": radius, "sweep": math.degrees(sweep), "length": radius * abs(sweep),
                                  "height": h, "thickness": t}
            elif kind == "ramp":                                        # (0.101)
                start, end, width, rise, thickness = self.ramp_params(guid)
                length = float(np.linalg.norm((end - start)[:2]))
                info["params"] = {"length": length, "width": width, "rise": rise, "thickness": thickness,
                                  "slope": rise / length if length > 0 else 0.0, "spec": self.ramp_spec(guid)}
            elif kind == "column":
                info["constraints"] = self.constraints(guid)
                info["params"] = {"height": info["constraints"]["height"]}
            elif kind == "beam":
                start, end, top, _w, _h = self.beam_params(guid)
                info["params"] = {"length": float(np.linalg.norm((end - start)[:2])), "top": top}
            elif kind in ("pipe", "duct", "conduit"):
                start, end, z = self.segment_params(guid)
                run = float(np.linalg.norm((end - start)[:2]))
                info["params"] = {"length": float(np.linalg.norm(end - start)), "z": z, "end_z": float(end[2]),
                                  "vertical": run < 1e-6,                    # (0.136: a stack, a riser)
                                  "slope": (z - float(end[2])) / run if run >= 1e-6 else 0.0}
                info["connections"] = self.connections(guid)            # (0.74)
                info["system"] = self.system_of(guid)                   # (0.141)
            elif kind == "fitting":
                info["connections"] = self.connections(guid)
                info["system"] = self.system_of(guid)
            elif kind == "air_terminal":                                # (0.138) a diffuser, a grille
                tp = self.terminal_params(guid)
                info["params"] = {"terminal": tp["kind"], "z": tp["z"], "air": tp["air"]}
                info["connections"] = self.connections(guid)
            elif kind == "equipment":                                   # (0.139) an HVAC unit
                ep = self.equipment_params(guid)
                info["params"] = {"equipment": ep["kind"], "base": float(ep["base"][2]), "angle": ep["angle"]}
                info["connections"] = self.connections(guid)
            elif kind == "electrical":                                  # (0.143) an outlet, a switch…
                pp = self.point_params(guid)
                info["params"] = {"point": pp["kind"], "height": pp["height"]}
                info["connections"] = self.connections(guid)
            elif kind == "terrain":                                     # (0.155) the terrain
                info["params"] = self.terrain_info(guid)
            elif kind == "appliance":                                   # (0.171) a kitchen's / laundry's
                info["params"] = self.appliance_params(guid)
                info["connections"] = self.connections(guid)
            elif kind == "cabinet":                                     # (0.169) a kitchen / storage module
                import dataclasses
                c = self.cabinet_params(guid)
                info["params"] = dict(dataclasses.asdict(c), overall_depth=c.overall_depth, top=c.top)
            elif kind == "rebar":                                       # (0.166) a set of bars: of which member
                row = next(r for r in self.rebar_rows() if r["guid"] == guid)
                info["params"] = row
            elif kind == "fixture":                                     # (0.140) a sanitary fixture
                fp = self.fixture_params(guid)
                info["params"] = {"fixture": fp["kind"], "angle": fp["angle"],
                                  "ports": [(p.Name, self.connected(p) is not None) for p in self.ports(guid)]}
            elif kind == "footing":
                _c, _x, length, width, top = self.footing_params(guid)
                info["params"] = {"length": length, "width": width, "top": top,      # (pad / strip: on its type)
                                  "strip": ifcopenshell.util.element.get_predefined_type(e) == "STRIP_FOOTING"}
            elif kind in ("door", "window"):
                st = self.filling_state(guid)
                f = st["frame"]
                info["params"] = {"from_start": st["s"] - f.x0, "sill": st["sill"],
                                  "to_end": f.x0 + f.length - st["s"] - st["width"], "mark": e.Tag or ""}
        except Exception:   # unusual geometry: show it read-only
            info["kind"], info["params"] = None, {}
        info["psets"] = ifcopenshell.util.element.get_psets(e)
        info["ifc_data"] = self.ifc_data(guid)                         # (0.266) its standard set, all of it
        info["ifc_type_data"] = self.ifc_type_data(guid)               # (0.430) …and its type's, to go back to
        return info
