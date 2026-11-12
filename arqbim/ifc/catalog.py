"""Starter catalogue of construction types (pure data, no IfcOpenShell).

Each type becomes an IFC type object (IfcWallType, IfcSlabType, IfcRoofType, IfcColumnType,
IfcBeamType, IfcFootingType, IfcPipeSegmentType, IfcDuctSegmentType) with its
material layers or profile, created in the project the first time it is used.
Thicknesses in meters.
"""

from dataclasses import dataclass, field, replace

from ..core import joinery


@dataclass(frozen=True)
class MaterialSpec:
    key: str
    name_pt: str
    name_en: str
    category: str          # IFC material category (concrete, brick, gypsum, ...): its hatch where cut
    color: tuple           # RGB 0..1, used for the IFC surface style and the viewport (0.314: its shading colour)
    density: float = None        # kg/m³ (Pset_MaterialCommon.MassDensity), 0.89
    conductivity: float = None   # W/(m·K) (Pset_MaterialThermal.ThermalConductivity), 0.89
    # (0.314) its graphics, as Revit's: each pattern (core.patterns key, "#rrggbb") or None. Its surface: a foreground
    # and a background pattern (tiles, bricks…) and how clear it is (0 opaque … 1 clear); its cut: a foreground and a
    # background pattern — both None: the project's graphic style's, by its category (as until 0.313)
    surface_fg: tuple = None
    surface_bg: tuple = None
    transparency: float = 0.0
    cut_fg: tuple = None
    cut_bg: tuple = None
    # (0.343) its finish in the realistic render (model/render_scene.FINISHES: matte, satin, glossy, metal, glass,
    # frosted); "": its category's
    finish: str = ""
    # (0.468) its realistic look (core/pbr.Look: its kind, roughness, metallic…, its pictures) — None: its finish's
    look: object = None

    @property
    def own_cut(self):
        """(0.314) Is it cut with patterns of its own (not its category's in the project's graphic style)?"""
        return self.cut_fg is not None or self.cut_bg is not None

    def graphics(self):
        """(0.314) Its graphics as one value (to compare two materials')."""
        from ..core import pbr
        return (self.surface_fg, self.surface_bg, round(float(self.transparency or 0.0), 3), self.cut_fg, self.cut_bg,
                self.finish or "", pbr.encode(self.look) if self.look is not None else "")


@dataclass(frozen=True)
class TypeSpec:
    key: str
    kind: str              # "wall" | "slab" | "roof" | "column" | "beam" | "footing" | "pipe" | "duct"…
    name_pt: str
    name_en: str
    layers: tuple = field(default_factory=tuple)   # ((material_key, thickness_m), ...) outside -> inside / bottom -> top
    profile: tuple = None  # (x_dim, y_dim) in meters, for columns and beams (a beam: width, height; a pipe: (Ø, Ø))
    material: str = None   # profile material, for columns, beams, pipes and ducts
    predefined: str = None     # the IFC PredefinedType when not the kind's usual one (0.94: PILE_CAP, BASESLAB, BORED)
    piles: int = 0             # a pile cap (0.94): how many piles under it (1, 2, 3 or 4)…
    pile: str = None           # …of which pile type (its key)…
    pile_length: float = 0.0   # …how long (m)
    shape: str = None          # a column's / beam's section (0.97): None a rectangle, "circle", "L", "T"…
    web: float = None          # …an L's / a T's legs' thickness (m)
    # (0.334) each layer's function (LAYER_FUNCTIONS), as Revit's — its priority where elements meet; () or None for
    # a layer: chosen by the program (the thickest is the structure)
    functions: tuple = ()
    # (0.346) a wall type's own masonry for Eurocode 6 — (units, group, fb N/mm², mortar), core/ec6's — or None: the
    # project's (its structural settings)
    masonry: tuple = None
    # (0.494) a steel column's / beam's section from the catalogue (core/steel: «IPE300», «HEB200»…; shape "steel",
    # profile its box in metres, material its grade's — «aco_s275»), or None
    section: str = None

    @property
    def thickness(self):
        return sum(t for _, t in self.layers)

    @property
    def strip(self):
        """A strip footing (along a wall), not a pad (under a column)."""
        return self.kind == "footing" and not (self.profile and self.profile[1])

    @property
    def round(self):
        """A round section (a pipe, a pile, a round column: its diameter), not a rectangle."""
        return self.kind in ("pipe", "pile") or self.shape == "circle"


# the kinds a sketch box can be classified as (pipes and ducts are only drawn)
CLASSIFIABLE = ("wall", "slab", "column", "beam", "footing")

# (0.334) a layer's function in its type, as Revit's (Structure [1], Substrate [2], Thermal / air layer [3], Finish 1
# [4], Finish 2 [5]): where two elements meet, a stronger layer goes on through the weaker ones of the other —
# {function: (its strength in the joins of what is cut, 1 strongest — model/cut_joins.py —, IFC4's
# IfcMaterialLayer.Priority, 0–100 higher stronger, and its Category)}
LAYER_FUNCTIONS = {"structure": (1, 90, "LoadBearing"), "substrate": (2, 70, "Substrate"),
                   "thermal": (3, 50, "Insulation"), "finish1": (4, 30, "Finish"), "finish2": (5, 10, "Finish")}


def function_of_priority(priority):
    """(0.334) The function of an IfcMaterialLayer's Priority (the nearest of LAYER_FUNCTIONS'), None for none."""
    if priority is None:
        return None
    return min(LAYER_FUNCTIONS, key=lambda f: abs(LAYER_FUNCTIONS[f][1] - float(priority)))


def layer_function(spec, k):
    """(0.334) The function given to a type's k-th layer, or None (the program's)."""
    return spec.functions[k] if k < len(spec.functions or ()) and spec.functions[k] in LAYER_FUNCTIONS else None

def load_bearing_wall(spec):
    """(0.342) A wall of this type load-bearing as it is made (Pset_WallCommon.LoadBearing): its structure layer —
    else its thickest — of concrete (a masonry one is marked by hand, 0.335)."""
    if spec.kind != "wall" or not spec.layers:
        return False
    k = next((i for i, f in enumerate(spec.functions or ()) if f == "structure"), None)
    if k is None:
        k = max(range(len(spec.layers)), key=lambda i: spec.layers[i][1])
    material = MATERIALS.get(spec.layers[k][0])
    return material is not None and material.category == "concrete"


MATERIALS = {m.key: m for m in (
    MaterialSpec("reboco", "Reboco", "Plaster", "plaster", (0.93, 0.91, 0.86)),
    MaterialSpec("bloco", "Bloco cerâmico", "Clay block", "brick", (0.78, 0.47, 0.36)),
    MaterialSpec("gesso", "Placa de gesso", "Gypsum board", "gypsum", (0.95, 0.95, 0.93)),
    MaterialSpec("la", "Lã mineral", "Mineral wool", "insulation", (0.94, 0.85, 0.45)),
    MaterialSpec("concreto", "Concreto", "Concrete", "concrete", (0.72, 0.72, 0.70)),
    MaterialSpec("pvc", "PVC", "PVC", "plastic", (0.36, 0.56, 0.79)),
    MaterialSpec("aco", "Aço galvanizado", "Galvanised steel", "steel", (0.72, 0.75, 0.78)),
    MaterialSpec("inox", "Aço inoxidável", "Stainless steel", "steel", (0.80, 0.81, 0.82)),          # (0.258)
    MaterialSpec("aco_preto", "Aço lacado preto", "Black powder-coated steel", "steel", (0.14, 0.14, 0.15)),
    MaterialSpec("madeira", "Madeira", "Wood", "wood", (0.66, 0.47, 0.31)),         # doors (0.70)
    MaterialSpec("aluminio", "Alumínio", "Aluminium", "aluminium", (0.80, 0.82, 0.84)),   # windows (0.70)
    MaterialSpec("vidro", "Vidro", "Glass", "glass", (0.62, 0.78, 0.88)),            # curtain walls (0.117)
    MaterialSpec("azulejo", "Azulejo cerâmico", "Ceramic tile", "ceramic", (0.90, 0.92, 0.93)),   # (0.119)
    MaterialSpec("pedra", "Pedra natural", "Natural stone", "stone", (0.80, 0.76, 0.68)),         # (0.119)
    MaterialSpec("argamassa_junta", "Argamassa de juntas", "Tile grout", "plaster", (0.70, 0.69, 0.66),   # (0.563)
                 density=1700.0),
    MaterialSpec("cola_cimenticia", "Cola cimentícia", "Cement tile adhesive", "plaster", (0.78, 0.77, 0.74),
                 density=1500.0),
    MaterialSpec("solo", "Solo natural", "Natural soil", "earth", (0.62, 0.55, 0.42)),            # (0.155)
    MaterialSpec("a400", "Aço A400 NR", "Reinforcing steel A400 NR", "steel", (0.62, 0.24, 0.16)),   # (0.166)
    MaterialSpec("a500", "Aço A500 NR", "Reinforcing steel A500 NR", "steel", (0.62, 0.24, 0.16)),
    MaterialSpec("melamina", "Aglomerado melamínico", "Melamine-faced board", "wood", (0.93, 0.92, 0.89)),  # (0.169)
    MaterialSpec("bancada", "Tampo de bancada", "Worktop", "stone", (0.36, 0.36, 0.38)),                     # (0.170)
    # (0.243) the cabinets' fronts' finishes (core.cabinets.FINISHES — FRONT_MATERIALS below)
    MaterialSpec("lacado_branco", "MDF lacado branco", "White lacquered MDF", "wood", (0.96, 0.96, 0.94)),
    MaterialSpec("lacado_cinza", "MDF lacado cinzento", "Grey lacquered MDF", "wood", (0.54, 0.55, 0.57)),
    MaterialSpec("lacado_preto", "MDF lacado preto", "Black lacquered MDF", "wood", (0.15, 0.15, 0.15)),
    MaterialSpec("carvalho", "Folheado de carvalho", "Oak veneer", "wood", (0.76, 0.60, 0.42)),
    MaterialSpec("nogueira", "Folheado de nogueira", "Walnut veneer", "wood", (0.42, 0.29, 0.20)),
    MaterialSpec("cobre", "Cobre isolado", "Insulated copper", "copper", (0.72, 0.45, 0.20)),               # (0.196)
    MaterialSpec("telha", "Telha cerâmica", "Clay roof tile", "ceramic", (0.71, 0.36, 0.24)),               # (0.278)
    MaterialSpec("fibrocimento", "Fibrocimento", "Fibre cement", "concrete", (0.74, 0.75, 0.73)),          # (0.280)
    MaterialSpec("rede", "Rede mosquiteira", "Insect mesh", "plastic", (0.30, 0.31, 0.33)),                # (0.291)
    # (0.440) the loose furniture's: its upholstery, a light fabric (mattresses, cushions), a plant's foliage
    MaterialSpec("tecido", "Tecido de estofo", "Upholstery fabric", "fabric", (0.55, 0.57, 0.60)),
    MaterialSpec("tecido_claro", "Tecido claro", "Light fabric", "fabric", (0.92, 0.91, 0.88)),
    MaterialSpec("folhagem", "Folhagem", "Foliage", "plant", (0.33, 0.52, 0.30)),
)}
MATERIALS["vidro_fosco"] = MaterialSpec("vidro_fosco", "Vidro fosco", "Frosted glass", "glass",
                                        (0.84, 0.89, 0.92))                                          # (0.306)
# (0.391) paints, for the Paint bucket (model/paint.py): an architect's usual colours
for _key, _pt, _en, _rgb in (("tinta_branca", "Tinta branca", "White paint", (0.96, 0.96, 0.94)),
                             ("tinta_marfim", "Tinta marfim", "Ivory paint", (0.95, 0.91, 0.82)),
                             ("tinta_areia", "Tinta areia", "Sand paint", (0.86, 0.79, 0.66)),
                             ("tinta_cinza", "Tinta cinzento claro", "Light grey paint", (0.78, 0.79, 0.79)),
                             ("tinta_grafite", "Tinta grafite", "Graphite paint", (0.25, 0.27, 0.29)),
                             ("tinta_terracota", "Tinta terracota", "Terracotta paint", (0.74, 0.39, 0.27)),
                             ("tinta_ocre", "Tinta ocre", "Ochre paint", (0.83, 0.62, 0.27)),
                             ("tinta_verde", "Tinta verde-salva", "Sage green paint", (0.58, 0.66, 0.55)),
                             ("tinta_azul", "Tinta azul-acinzentado", "Grey-blue paint", (0.47, 0.58, 0.68)),
                             ("tinta_vermelha", "Tinta vermelho-escuro", "Dark red paint", (0.62, 0.17, 0.16))):
    MATERIALS[_key] = MaterialSpec(_key, _pt, _en, "paint", _rgb)
# (0.314) the graphics the catalogue's materials start with: the tiles' joints, the stone's courses, the roof tiles'
# rows on their surface; the glass clear
for _key, _changes in (("azulejo", {"surface_fg": ("tile_15", "#8d979d")}),
                       ("pedra", {"surface_fg": ("stone", "#8a8072")}),
                       ("telha", {"surface_fg": ("roof_tiles", "#5e3222")}),
                       ("vidro", {"transparency": 0.6}),
                       ("vidro_fosco", {"transparency": 0.3})):
    MATERIALS[_key] = replace(MATERIALS[_key], **_changes)


def _library(key, pt, en, category, rgb, density, conductivity, cut=None, surface=None, transparency=0.0):
    """(0.318) A material of the library: its cut — (foreground, background colour) on a solid background —, its
    surface's pattern — (pattern, colour) —, its data."""
    cut_fg = cut_bg = None
    if cut is not None:
        pattern, background = cut
        cut_fg = (pattern, "#202020") if pattern else None
        cut_bg = ("solid", background) if background else None
    return MaterialSpec(key, pt, en, category, rgb, density, conductivity, surface_fg=surface, transparency=transparency,
                        cut_fg=cut_fg, cut_bg=cut_bg)


# (0.318) the library: the usual Portuguese building materials, by family, each with its hatches where cut and seen
for _m in (
    # masonry
    _library("tijolo_11", "Tijolo furado 11", "Hollow clay brick 11", "brick", (0.80, 0.50, 0.38), 900.0, 0.40,
             ("diagonal", "#f6dfd4")),
    _library("tijolo_macico", "Tijolo maciço", "Solid clay brick", "brick", (0.72, 0.38, 0.27), 1800.0, 0.80,
             ("cross", "#f2d3c4"), ("brick", "#e9e2d8")),
    _library("bloco_betao", "Bloco de betão", "Concrete block", "block", (0.70, 0.70, 0.68), 1200.0, 0.90,
             ("diagonal_wide", "#e3e3e0"), ("block", "#8f8f8c")),
    _library("bloco_termico", "Bloco térmico de argila expandida", "Lightweight clay aggregate block", "block",
             (0.62, 0.58, 0.52), 700.0, 0.25, ("diagonal_wide", "#eee6d8")),
    # concrete
    _library("betao_armado", "Betão armado", "Reinforced concrete", "concrete", (0.66, 0.66, 0.64), 2500.0, 2.50,
             ("concrete", "#d9d9d6")),
    _library("betao_leve", "Betão leve", "Lightweight concrete", "concrete", (0.78, 0.77, 0.73), 1200.0, 0.40,
             ("sand", "#ecebe6")),
    _library("betonilha", "Betonilha", "Screed", "concrete", (0.75, 0.74, 0.70), 2000.0, 1.30, ("sand", "#e6e5e0")),
    # insulation
    _library("xps", "Poliestireno extrudido (XPS)", "Extruded polystyrene (XPS)", "insulation", (0.55, 0.75, 0.90),
             35.0, 0.035, ("insulation", "#dbeaf5")),
    _library("eps", "Poliestireno expandido (EPS)", "Expanded polystyrene (EPS)", "insulation", (0.96, 0.96, 0.94),
             20.0, 0.037, ("insulation", "#ffffff")),
    _library("la_rocha", "Lã de rocha", "Rock wool", "insulation", (0.80, 0.70, 0.45), 70.0, 0.036,
             ("insulation", "#f6efd9")),
    _library("cortica", "Aglomerado de cortiça (ICB)", "Expanded cork board", "insulation", (0.55, 0.38, 0.24),
             110.0, 0.040, ("sand", "#e7d6c5")),
    _library("pur", "Espuma de poliuretano (PUR)", "Polyurethane foam", "insulation", (0.93, 0.88, 0.60), 35.0, 0.025,
             ("insulation", "#fbf4d6")),
    # wood
    _library("pinho", "Pinho", "Pine", "wood", (0.85, 0.70, 0.48), 520.0, 0.13, ("wood", "#f7ead4")),
    _library("carvalho_macico", "Carvalho maciço", "Solid oak", "wood", (0.70, 0.52, 0.33), 700.0, 0.18,
             ("wood", "#efdfcb")),
    _library("osb", "Painel OSB", "OSB board", "wood", (0.80, 0.66, 0.42), 650.0, 0.13, ("cross", "#f4e7cf")),
    _library("contraplacado", "Contraplacado", "Plywood", "wood", (0.82, 0.68, 0.48), 500.0, 0.13,
             ("horizontal", "#f5e9d4")),
    _library("mdf", "MDF", "MDF", "wood", (0.66, 0.52, 0.38), 750.0, 0.14, ("sand", "#eadfd2")),
    _library("deck", "Deck de madeira exótica", "Hardwood decking", "wood", (0.52, 0.34, 0.22), 900.0, 0.20,
             ("wood", "#e6d3c3"), ("boards_h", "#3b2516")),
    # stone
    _library("granito", "Granito", "Granite", "stone", (0.62, 0.60, 0.58), 2700.0, 2.80, ("diagonal_back", "#e6e4e1"),
             ("stone", "#6e6b67")),
    _library("calcario", "Calcário (lioz)", "Limestone", "stone", (0.88, 0.84, 0.74), 2600.0, 1.70,
             ("diagonal_back", "#f3efe5"), ("stone", "#a69e8a")),
    _library("marmore", "Mármore", "Marble", "stone", (0.94, 0.93, 0.90), 2700.0, 2.80, ("cross", "#f8f7f4"),
             ("tile_30x60", "#b6b3ab")),
    _library("xisto", "Xisto", "Schist", "stone", (0.42, 0.40, 0.38), 2600.0, 2.20, ("diagonal_back", "#d9d6d3"),
             ("stone", "#2c2a28")),
    _library("calcada", "Calçada portuguesa", "Portuguese stone pavement", "stone", (0.92, 0.90, 0.85), 2600.0, 2.00,
             ("diagonal_back", "#f5f3ee"), ("tile_10", "#9d988d")),
    # metals
    _library("aco_s275", "Aço estrutural S275", "Structural steel S275", "steel", (0.55, 0.57, 0.60), 7850.0, 50.0,
             ("steel", "#c9ccd0")),
    # (0.494) the other grades of the steel sections (core/steel.GRADES)
    _library("aco_s235", "Aço estrutural S235", "Structural steel S235", "steel", (0.55, 0.57, 0.60), 7850.0, 50.0,
             ("steel", "#c9ccd0")),
    _library("aco_s355", "Aço estrutural S355", "Structural steel S355", "steel", (0.55, 0.57, 0.60), 7850.0, 50.0,
             ("steel", "#c9ccd0")),
    _library("aco_s460", "Aço estrutural S460", "Structural steel S460", "steel", (0.55, 0.57, 0.60), 7850.0, 50.0,
             ("steel", "#c9ccd0")),
    _library("zinco", "Zinco (junta agrafada)", "Zinc (standing seam)", "zinc", (0.70, 0.72, 0.74), 7140.0, 110.0,
             (None, "#5d6166"), ("boards_v", "#55595e")),
    _library("cobre_chapa", "Chapa de cobre", "Copper sheet", "copper", (0.72, 0.45, 0.20), 8900.0, 380.0,
             (None, "#6b3d18")),
    # finishes
    _library("gesso_hidrofugo", "Gesso cartonado hidrófugo", "Moisture-resistant gypsum board", "gypsum",
             (0.85, 0.92, 0.85), 800.0, 0.21, ("sand", "#dfeedd")),
    _library("estuque", "Estuque", "Stucco", "plaster", (0.96, 0.95, 0.92), 1200.0, 0.57, ("sand", "#ffffff")),
    _library("monomassa", "Reboco monomassa", "One-coat render", "plaster", (0.90, 0.86, 0.78), 1500.0, 0.80,
             ("sand", "#f7f2e8")),
    _library("etics", "Reboco do ETICS (capoto)", "ETICS render", "plaster", (0.95, 0.94, 0.90), 1300.0, 0.70,
             ("sand", "#ffffff")),
    _library("ladrilho_30", "Ladrilho cerâmico 30×30", "Ceramic floor tile 30×30", "ceramic", (0.78, 0.70, 0.62),
             2300.0, 1.30, ("cross", "#f1e8e0"), ("tile_30", "#8f8378")),
    _library("porcelanico", "Porcelânico 60×30", "Porcelain tile 60×30", "ceramic", (0.84, 0.83, 0.80), 2400.0, 1.30,
             ("cross", "#f4f3f0"), ("tile_30x60", "#9c9a94")),
    _library("vinilico", "Pavimento vinílico", "Vinyl flooring", "plastic", (0.60, 0.58, 0.55), 1200.0, 0.17,
             (None, "#8a8782")),
    _library("tela", "Tela impermeabilizante", "Waterproofing membrane", "plastic", (0.20, 0.20, 0.22), 1100.0, 0.20,
             (None, "#202022")),
    # ground and glass
    _library("brita", "Brita", "Gravel", "earth", (0.70, 0.68, 0.64), 1800.0, 2.00, ("earth", "#ece9e3")),
    _library("areia", "Areia", "Sand", "earth", (0.86, 0.78, 0.60), 1600.0, 2.00, ("sand", "#f5ecd8")),
    _library("vidro_duplo", "Vidro duplo", "Double glazing", "glass", (0.62, 0.78, 0.88), 2500.0, 1.00,
             transparency=0.6),
    # (0.365) water: a pool's, a pond's (a slab or a sketch given it)
    _library("agua", "Água (piscina, lago)", "Water (pool, pond)", "water", (0.30, 0.62, 0.72), 1000.0, 0.60,
             (None, "#bfe3ec"), transparency=0.25),
):
    MATERIALS[_m.key] = _m

# (0.343) the finishes the catalogue's materials start with in the render, where not their category's: the lacquers,
# the worktop and the polished marble glossy, the roof tiles and the lacquered metals satin, the frosted glass frosted
for _key in ("lacado_branco", "lacado_cinza", "lacado_preto", "bancada", "marmore"):
    MATERIALS[_key] = replace(MATERIALS[_key], finish="glossy")
for _key in ("telha", "aco_preto"):
    MATERIALS[_key] = replace(MATERIALS[_key], finish="satin")
for _key in ("a400", "a500", "rede"):
    MATERIALS[_key] = replace(MATERIALS[_key], finish="matte")
MATERIALS["vidro_fosco"] = replace(MATERIALS["vidro_fosco"], finish="frosted")
MATERIALS["agua"] = replace(MATERIALS["agua"], finish="water")                # (0.365)

# (0.318) the families the materials window shows them by (the IFC categories in each)
FAMILIES = (("masonry", ("brick", "block", "masonry")), ("concrete", ("concrete",)), ("insulation", ("insulation",)),
            ("wood", ("wood",)), ("stone", ("stone",)), ("metal", ("steel", "aluminium", "copper", "zinc", "metal")),
            ("finish", ("plaster", "gypsum", "ceramic")), ("glass", ("glass",)), ("paint", ("paint",)),   # (0.391)
            ("other", ()))


def family_of(spec):
    """(0.318) A material's family (FAMILIES): by its IFC category."""
    category = (spec.category or "").lower()
    return next((name for name, categories in FAMILIES if category in categories), "other")
# (0.306) the Caixilho Studio's systems and the colours of their profiles: a material for each pair, «aluminio_grafite»…
PROFILE_SYSTEMS = (("aluminio", "Alumínio", "Aluminium", "aluminium"), ("pvc", "PVC", "PVC", "plastic"),
                   ("madeira", "Madeira", "Wood", "wood"), ("aco", "Aço", "Steel", "steel"))
PROFILE_COLOURS = (("grafite", "grafite", "graphite", (0.18, 0.20, 0.22)),
                   ("branco", "branco", "white", (0.93, 0.92, 0.90)),
                   ("bronze", "bronze", "bronze", (0.42, 0.31, 0.23)),
                   ("natural", "cor madeira", "wood colour", (0.60, 0.42, 0.26)))
for _sys, _pt, _en, _category in PROFILE_SYSTEMS:
    for _colour, _cpt, _cen, _rgb in PROFILE_COLOURS:
        MATERIALS[_sys + "_" + _colour] = MaterialSpec(_sys + "_" + _colour, "{} {}".format(_pt, _cpt),
                                                       "{} {}".format(_en, _cen), _category, _rgb,
                                                       finish="satin")      # (0.343: lacquered profiles)


def profile_material(system, colour):
    """(0.306) The material key of a system's profile in a colour (PROFILE_SYSTEMS × PROFILE_COLOURS)."""
    return "{}_{}".format(system, colour)


def profile_of(material):
    """(0.306) (system, colour) of a profile material, or (its system, None) for a system's plain material ("aluminio"),
    or (None, None)."""
    for sys_key, *_r in PROFILE_SYSTEMS:
        if material == sys_key:
            return sys_key, None
        for colour, *_c in PROFILE_COLOURS:
            if material == "{}_{}".format(sys_key, colour):
                return sys_key, colour
    return None, None


FRONT_MATERIALS = {"melamine": "melamina", "lacquer_white": "lacado_branco", "lacquer_grey": "lacado_cinza",
                   "lacquer_black": "lacado_preto", "oak": "carvalho", "walnut": "nogueira"}      # (0.243)

TYPES = (
    TypeSpec("parede_alv_15", "wall", "Parede alvenaria 15 cm", "Masonry wall 15 cm",
             layers=(("reboco", 0.015), ("bloco", 0.12), ("reboco", 0.015))),
    TypeSpec("parede_alv_20", "wall", "Parede alvenaria 20 cm", "Masonry wall 20 cm",
             layers=(("reboco", 0.02), ("bloco", 0.16), ("reboco", 0.02))),
    TypeSpec("parede_dry_10", "wall", "Parede drywall 10 cm", "Drywall 10 cm",
             layers=(("gesso", 0.0125), ("la", 0.075), ("gesso", 0.0125))),
    # (0.342) load-bearing reinforced concrete walls (core.ec2.wall): all their thickness the structure
    TypeSpec("parede_betao_15", "wall", "Parede de betão armado 15 cm", "Reinforced concrete wall 15 cm",
             layers=(("concreto", 0.15),), functions=("structure",)),
    TypeSpec("parede_betao_20", "wall", "Parede de betão armado 20 cm", "Reinforced concrete wall 20 cm",
             layers=(("concreto", 0.20),), functions=("structure",)),
    TypeSpec("parede_betao_25", "wall", "Parede de betão armado 25 cm", "Reinforced concrete wall 25 cm",
             layers=(("concreto", 0.25),), functions=("structure",)),
    TypeSpec("laje_12", "slab", "Laje de concreto 12 cm", "Concrete slab 12 cm",
             layers=(("concreto", 0.12),)),
    TypeSpec("laje_15", "slab", "Laje de concreto 15 cm", "Concrete slab 15 cm",
             layers=(("concreto", 0.15),)),
    TypeSpec("pilar_20", "column", "Pilar de concreto 20×20", "Concrete column 20×20",
             profile=(0.20, 0.20), material="concreto"),
    TypeSpec("pilar_30", "column", "Pilar de concreto 30×30", "Concrete column 30×30",
             profile=(0.30, 0.30), material="concreto"),
    TypeSpec("pilar_20x50", "column", "Pilar de concreto 20×50", "Concrete column 20×50",
             profile=(0.20, 0.50), material="concreto"),
    # other sections (0.97): round, L (a corner), T (a wall's end)
    TypeSpec("pilar_circ_30", "column", "Pilar circular Ø30", "Round column Ø30", profile=(0.30, 0.30),
             material="concreto", shape="circle"),
    TypeSpec("pilar_L_40", "column", "Pilar em L 40×40 (15)", "L column 40×40 (15)", profile=(0.40, 0.40),
             material="concreto", shape="L", web=0.15),
    TypeSpec("pilar_T_50", "column", "Pilar em T 50×40 (15)", "T column 50×40 (15)", profile=(0.50, 0.40),
             material="concreto", shape="T", web=0.15),
    # beams (0.66): profile = (width, height of the section)
    TypeSpec("viga_15x30", "beam", "Viga de concreto 15×30", "Concrete beam 15×30",
             profile=(0.15, 0.30), material="concreto"),
    TypeSpec("viga_20x40", "beam", "Viga de concreto 20×40", "Concrete beam 20×40",
             profile=(0.20, 0.40), material="concreto"),
    TypeSpec("viga_20x50", "beam", "Viga de concreto 20×50", "Concrete beam 20×50",
             profile=(0.20, 0.50), material="concreto"),
    TypeSpec("viga_T_60", "beam", "Viga em T 60×50 (12)", "T beam 60×50 (12)", profile=(0.60, 0.50),
             material="concreto", shape="T", web=0.12),
    # (0.494) steel: sections of the catalogue (core/steel), in a grade
    TypeSpec("pilar_heb200", "column", "Pilar HEB 200 — S275", "Column HEB 200 — S275", profile=(0.20, 0.20),
             material="aco_s275", shape="steel", section="HEB200"),
    TypeSpec("pilar_shs150", "column", "Pilar SHS 150×150×8 — S355", "Column SHS 150×150×8 — S355",
             profile=(0.15, 0.15), material="aco_s355", shape="steel", section="SHS150x150x8"),
    TypeSpec("viga_ipe200", "beam", "Viga IPE 200 — S275", "Beam IPE 200 — S275", profile=(0.10, 0.20),
             material="aco_s275", shape="steel", section="IPE200"),
    TypeSpec("viga_ipe300", "beam", "Viga IPE 300 — S275", "Beam IPE 300 — S275", profile=(0.15, 0.30),
             material="aco_s275", shape="steel", section="IPE300"),
    TypeSpec("viga_heb240", "beam", "Viga HEB 240 — S275", "Beam HEB 240 — S275", profile=(0.24, 0.24),
             material="aco_s275", shape="steel", section="HEB240"),
    # (0.495) braces and purlins (IfcMemberType, BRACE / PURLIN)
    TypeSpec("contrav_l80", "member", "Contraventamento L 80×8 — S275", "Brace L 80×8 — S275", profile=(0.08, 0.08),
             material="aco_s275", shape="steel", section="L80x8", predefined="BRACE"),
    TypeSpec("contrav_chs76", "member", "Contraventamento CHS Ø76,1×4 — S275", "Brace CHS Ø76,1×4 — S275",
             profile=(0.0761, 0.0761), material="aco_s275", shape="steel", section="CHS76.1x4", predefined="BRACE"),
    TypeSpec("madre_c160", "member", "Madre C 160×60×20×2,5 — S275", "Purlin C 160×60×20×2,5 — S275",
             profile=(0.06, 0.16), material="aco_s275", shape="steel", section="C160x60x20x2.5", predefined="PURLIN"),
    # footings (0.68): layers = their depth; profile = the plan size of a pad (x, y), of a strip (its width, 0)
    TypeSpec("sapata_80", "footing", "Sapata 80×80×40", "Pad footing 80×80×40",
             layers=(("concreto", 0.40),), profile=(0.80, 0.80)),
    TypeSpec("sapata_120", "footing", "Sapata 120×120×50", "Pad footing 120×120×50",
             layers=(("concreto", 0.50),), profile=(1.20, 1.20)),
    TypeSpec("sapata_corrida_50", "footing", "Sapata corrida 50×30", "Strip footing 50×30",
             layers=(("concreto", 0.30),), profile=(0.50, 0.0)),
    # pile caps (0.94): a footing (PILE_CAP) with its piles under it
    TypeSpec("bloco_1e", "footing", "Bloco de 1 estaca 60×60×50", "Pile cap, 1 pile 60×60×50",
             layers=(("concreto", 0.50),), profile=(0.60, 0.60), predefined="PILE_CAP", piles=1, pile="estaca_30",
             pile_length=8.0),
    TypeSpec("bloco_2e", "footing", "Bloco de 2 estacas 150×60×60", "Pile cap, 2 piles 150×60×60",
             layers=(("concreto", 0.60),), profile=(1.50, 0.60), predefined="PILE_CAP", piles=2, pile="estaca_30",
             pile_length=8.0),
    TypeSpec("bloco_4e", "footing", "Bloco de 4 estacas 150×150×70", "Pile cap, 4 piles 150×150×70",
             layers=(("concreto", 0.70),), profile=(1.50, 1.50), predefined="PILE_CAP", piles=4, pile="estaca_30",
             pile_length=8.0),
    # piles (0.94): a round section (its diameter), as long as their cap's type says
    TypeSpec("estaca_30", "pile", "Estaca de betão Ø30", "Concrete pile Ø30", profile=(0.30, 0.30),
             material="concreto", predefined="BORED"),
    TypeSpec("estaca_40", "pile", "Estaca de betão Ø40", "Concrete pile Ø40", profile=(0.40, 0.40),
             material="concreto", predefined="BORED"),
    # a raft (0.94): a slab at the foundation (BASESLAB), drawn with the Slab tool
    TypeSpec("radier_30", "slab", "Radier 30 cm", "Raft 30 cm", layers=(("concreto", 0.30),), predefined="BASESLAB"),
    # roofs (0.278): IfcRoofType, its layers from the bottom up (before, a roof took a slab's type)
    TypeSpec("cobertura_12", "roof", "Cobertura de concreto 12 cm", "Concrete roof 12 cm", layers=(("concreto", 0.12),)),
    TypeSpec("cobertura_15", "roof", "Cobertura de concreto 15 cm", "Concrete roof 15 cm", layers=(("concreto", 0.15),)),
    TypeSpec("telhado_ceramico", "roof", "Telhado de telha cerâmica", "Clay tile roof", layers=(("telha", 0.03),)),
    # building services (0.69): a pipe's profile = (outside diameter, the same); a duct's = (width, height)
    TypeSpec("tubo_25", "pipe", "Tubo PVC Ø25", "PVC pipe Ø25", profile=(0.025, 0.025), material="pvc"),
    TypeSpec("tubo_50", "pipe", "Tubo PVC Ø50", "PVC pipe Ø50", profile=(0.050, 0.050), material="pvc"),
    TypeSpec("tubo_100", "pipe", "Tubo PVC Ø100", "PVC pipe Ø100", profile=(0.100, 0.100), material="pvc"),
    # (0.196) refrigerant lines: copper, the size of their insulation (1/4" … 5/8")
    TypeSpec("cobre_14", "pipe", "Tubo de cobre 1/4\" isolado", "Insulated copper pipe 1/4\"", profile=(0.025, 0.025),
             material="cobre"),
    TypeSpec("cobre_38", "pipe", "Tubo de cobre 3/8\" isolado", "Insulated copper pipe 3/8\"", profile=(0.028, 0.028),
             material="cobre"),
    TypeSpec("cobre_12", "pipe", "Tubo de cobre 1/2\" isolado", "Insulated copper pipe 1/2\"", profile=(0.032, 0.032),
             material="cobre"),
    TypeSpec("cobre_58", "pipe", "Tubo de cobre 5/8\" isolado", "Insulated copper pipe 5/8\"", profile=(0.035, 0.035),
             material="cobre"),
    # (0.198) gas: copper Ø15 and Ø22
    TypeSpec("gas_cobre_15", "pipe", "Tubo de cobre Ø15 (gás)", "Copper pipe Ø15 (gas)", profile=(0.015, 0.015),
             material="cobre"),
    TypeSpec("gas_cobre_22", "pipe", "Tubo de cobre Ø22 (gás)", "Copper pipe Ø22 (gas)", profile=(0.022, 0.022),
             material="cobre"),
    TypeSpec("conduta_30x20", "duct", "Conduta 30×20", "Duct 30×20", profile=(0.30, 0.20), material="aco"),
    TypeSpec("conduta_50x30", "duct", "Conduta 50×30", "Duct 50×30", profile=(0.50, 0.30), material="aco"),
    # round ducts (0.138): spiral ducts, their diameter
    TypeSpec("conduta_d160", "duct", "Conduta circular Ø160", "Round duct Ø160", profile=(0.16, 0.16), material="aco",
             shape="circle"),
    TypeSpec("conduta_d200", "duct", "Conduta circular Ø200", "Round duct Ø200", profile=(0.20, 0.20), material="aco",
             shape="circle"),
    TypeSpec("conduta_d250", "duct", "Conduta circular Ø250", "Round duct Ø250", profile=(0.25, 0.25), material="aco",
             shape="circle"),
    # electrical conduits (0.146): the cables' tubes (IfcCableCarrierSegment CONDUITSEGMENT), their diameter
    TypeSpec("tubo_vd20", "conduit", "Tubo VD Ø20", "Conduit Ø20", profile=(0.020, 0.020), material="pvc",
             shape="circle"),
    TypeSpec("tubo_vd25", "conduit", "Tubo VD Ø25", "Conduit Ø25", profile=(0.025, 0.025), material="pvc",
             shape="circle"),
    TypeSpec("tubo_vd32", "conduit", "Tubo VD Ø32", "Conduit Ø32", profile=(0.032, 0.032), material="pvc",
             shape="circle"),
)

BY_KEY = {t.key: t for t in TYPES}

# the project's own types (0.87, the type editor): read from its IFC (model/project_types). A type with a
# catalogue entry's name that the project changed takes that entry's place; the others are added. BY_KEY and
# MATERIALS always hold what the open project uses.
_STARTER = dict(BY_KEY)
_STARTER_MATERIALS = dict(MATERIALS)
_PROJECT = []
GENERATION = 0                 # (0.315) counts each set_project: what was made from the materials is made again
LAYERED = ("wall", "slab", "footing", "roof")          # made of layers; the others of a section (a profile)
KINDS = ("wall", "slab", "roof", "column", "beam", "member", "footing", "pile", "pipe", "duct", "conduit")
# (0.495: member — a brace, a purlin, another steel member)


def types():
    """Every type to draw with: the catalogue's (as the project has them) and then the project's own."""
    return tuple(BY_KEY[t.key] for t in TYPES) + tuple(_PROJECT)


STEEL_WORDS = {"column": ("Pilar", "Column"), "beam": ("Viga", "Beam"), "member": ("Elemento", "Member"),
               "brace": ("Contraventamento", "Brace"), "purlin": ("Madre", "Purlin")}           # (0.495)


def steel_word(spec):
    """(0.495) What a steel type is called by: its kind's word, a member's by its PredefinedType (a brace, a purlin)."""
    return {"BRACE": "brace", "PURLIN": "purlin"}.get(spec.predefined, spec.kind) if spec.kind == "member" \
        else spec.kind


def steel_name(kind, section, grade, lang="pt"):
    """(0.494) A steel type's name: «Viga IPE 300 — S275»."""
    from ..core import steel
    word = STEEL_WORDS.get(kind, STEEL_WORDS["member"])[0 if lang == "pt" else 1]
    return "{} {} — {}".format(word, steel.display(section), grade)


def steel_spec(spec, section, grade, name=None):
    """(0.494) A column / beam type made of a steel section of the catalogue in a grade (from `spec`: its key and kind
    kept): its box, its grade's material, its name (given, else «Viga IPE 300 — S275»)."""
    from ..core import steel
    sec = steel.get(section)
    w, h = steel.size(sec)
    word = steel_word(spec)
    pt, en = (name, name) if name else (steel_name(word, sec.name, grade), steel_name(word, sec.name, grade, "en"))
    return replace(spec, name_pt=pt, name_en=en, layers=(), profile=(w / 1000.0, h / 1000.0),
                   material=steel.GRADE_MATERIAL[grade], shape="steel", web=None, section=sec.name)


def is_starter(key):
    return key in _STARTER or key in _STARTER_OPENINGS


def is_starter_material(key):
    return key in _STARTER_MATERIALS


def starter_materials():
    """(0.393) The catalogue's own materials, as the program has them (not as the open project changed them)."""
    return tuple(_STARTER_MATERIALS.values())


def starter(key):
    """The catalogue's own entry (before the project changed it), or None."""
    return _STARTER.get(key)


def add_project_type(spec):
    """(0.159) A type of the project's own made while working (a wall's thickness read from a drawing)."""
    BY_KEY[spec.key] = spec
    if spec.key not in _STARTER and all(s.key != spec.key for s in _PROJECT):
        _PROJECT.append(spec)


def set_project(specs, materials=()):
    """The open project's types and materials (read from its IFC); () goes back to the catalogue alone."""
    global GENERATION
    GENERATION += 1
    BY_KEY.clear()
    BY_KEY.update(_STARTER)
    MATERIALS.clear()
    MATERIALS.update(_STARTER_MATERIALS)
    for m in materials:
        MATERIALS[m.key] = m
    _PROJECT.clear()
    for s in specs:
        BY_KEY[s.key] = s
        if s.key not in _STARTER:
            _PROJECT.append(s)


@dataclass(frozen=True)
class OpeningSpec:
    """A door or window type. Sizes in meters; `sill` = height of the bottom above the wall base."""
    key: str
    kind: str              # "door" | "window"
    name_pt: str
    name_en: str
    width: float
    height: float
    sill: float = 0.0
    operation: str = ""    # IfcDoorTypeOperationEnum / IfcWindowTypePartitioningEnum
    lining_depth: float = None   # None: whole wall thickness (doors)
    transom: float = 0.0   # (0.110) a door's fanlight over its leaf: its height (m) within `height`; 0: none
    design: object = None  # (0.288) its joinery (core.joinery.Design); None: made from the above (design_of)


def design_of(spec):
    """(0.288) The joinery design of a door / window type: its own — a door's fanlight as `transom` says, a window's
    frame as deep as `lining_depth` says —, else one made from its IFC operation, fanlight and frame depth."""
    if spec.design is None:
        return joinery.standard(spec.kind, spec.operation, spec.transom,
                                spec.lining_depth if spec.kind == "window" else None)
    design = spec.design
    if spec.kind == "door" and len(design.rows) <= 2 and \
            abs(joinery.transom_of(design, spec.height) - float(spec.transom or 0.0)) > 1e-9:
        design = joinery.with_transom(design, float(spec.transom or 0.0))
    if spec.kind == "window" and spec.lining_depth and abs(design.depth - spec.lining_depth) > 1e-9:
        design = replace(design, depth=float(spec.lining_depth))
    return design


def with_design(spec, design):
    """(0.289) A door / window type with another design: its IFC operation, fanlight and frame depth its."""
    return replace(spec, design=design,
                   operation=(joinery.door_operation(design) if spec.kind == "door"
                              else joinery.window_partitioning(design))[0],
                   transom=joinery.transom_of(design, spec.height) if spec.kind == "door" else 0.0,
                   lining_depth=design.depth if spec.kind == "window" else spec.lining_depth)


def opening(key, kind, name_pt, name_en, width, height, design, sill=0.0):
    """(0.288) A door / window type made by its design: its IFC operation, fanlight and frame depth read from it."""
    operation = (joinery.door_operation(design) if kind == "door" else joinery.window_partitioning(design))[0]
    return OpeningSpec(key, kind, name_pt, name_en, width, height, sill, operation,
                       design.depth if kind == "window" else None,
                       joinery.transom_of(design, height) if kind == "door" else 0.0, design)


OPENINGS = (
    opening("porta_80", "door", "Porta 80×210", "Door 80×210", 0.80, 2.10, joinery.door("left")),
    opening("porta_90", "door", "Porta 90×210", "Door 90×210", 0.90, 2.10, joinery.door("left")),
    opening("porta_80_bandeira", "door", "Porta 80×210 + bandeira 50", "Door 80×210 + fanlight 50", 0.80, 2.60,
            joinery.door("left", transom=0.50)),
    # (0.288) more of the generator's
    opening("porta_dupla_140", "door", "Porta de 2 folhas 140×210", "Double door 140×210", 1.40, 2.10,
            joinery.door("left", "right")),
    opening("porta_correr_90", "door", "Porta de correr 90×210", "Sliding door 90×210", 0.90, 2.10,
            joinery.door("slide_left")),
    opening("porta_sacada_140", "door", "Porta de sacada 140×220 (vidro)", "French door 140×220 (glazed)",
            1.40, 2.20, joinery.door("left", "right", fill="glass", frame_material="aluminio",
                                     panel_material="aluminio", depth=0.07, sash=0.08, sash_depth=0.06,
                                     glass=0.024)),
    # (0.290) an outside door: its stone threshold, 3 cm, out of the wall's face it is placed on
    opening("porta_exterior_90", "door", "Porta exterior 90×210 (soleira)", "Outside door 90×210 (threshold)",
            0.90, 2.10, joinery.door("left", stone=0.03)),
    # (0.290) the windows on a stone sill 3 cm thick, 3 cm out of the wall, with its drip groove
    opening("janela_120", "window", "Janela 120×120 (peitoril 1,00)", "Window 120×120 (sill 1.00)",
            1.20, 1.20, joinery.window(("left", "right"), stone=0.03), sill=1.00),
    opening("janela_150", "window", "Janela 150×120 (peitoril 1,00)", "Window 150×120 (sill 1.00)",
            1.50, 1.20, joinery.window(("slide_right", "slide_left"), stone=0.03), sill=1.00),
    opening("janela_60", "window", "Basculante 60×60 (peitoril 1,60)", "Hopper 60×60 (sill 1.60)",
            0.60, 0.60, joinery.window(("bottom",), stone=0.03), sill=1.60),
    opening("janela_oscilo_100", "window", "Janela oscilobatente 100×120 (peitoril 1,00)",
            "Tilt and turn window 100×120 (sill 1.00)", 1.00, 1.20, joinery.window(("tilt_left",), stone=0.03),
            sill=1.00),
    # (0.294) an arched window: two leaves under a round arch's fixed fanlight
    opening("janela_arco_100", "window", "Janela em arco 100×150 (peitoril 0,90)", "Arched window 100×150 (sill 0.90)",
            1.00, 1.50, joinery.with_arch(joinery.window(("left", "right"), stone=0.03), "round", 1.00), sill=0.90),
)

OPENING_BY_KEY = {o.key: o for o in OPENINGS}
_STARTER_OPENINGS = dict(OPENING_BY_KEY)
_PROJECT_OPENINGS = []


def add_project_opening(spec):
    """(0.160) A door / window type of the project's own made while working (a width read from a drawing)."""
    OPENING_BY_KEY[spec.key] = spec
    if spec.key not in _STARTER_OPENINGS and all(s.key != spec.key for s in _PROJECT_OPENINGS):
        _PROJECT_OPENINGS.append(spec)


def openings():
    """Every door and window type: the catalogue's (as the project has them) and then the project's own."""
    return tuple(OPENING_BY_KEY[o.key] for o in OPENINGS) + tuple(_PROJECT_OPENINGS)


def set_project_openings(specs):
    """The open project's door and window types (read from its IFC; () : the catalogue alone)."""
    OPENING_BY_KEY.clear()
    OPENING_BY_KEY.update(_STARTER_OPENINGS)
    _PROJECT_OPENINGS.clear()
    for s in specs:
        OPENING_BY_KEY[s.key] = s
        if s.key not in _STARTER_OPENINGS:
            _PROJECT_OPENINGS.append(s)
