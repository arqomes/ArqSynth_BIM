"""Cabinets (0.169, Phase 10, step 1), mixed into IfcModel: a kitchen or storage module as an IfcFurniture
(USERDEFINED: «Móvel inferior», «Móvel superior», «Coluna») built in (Pset_FurnitureTypeCommon: its nominal sizes,
IsBuiltIn), with its own body — one IfcExtrudedAreaSolid per panel (core/cabinets.layout: sides, bottom, top or
rails, back, shelves, plinth, fronts, handles), made again from its parameters when they change, as a stair's. Its
material: the carcass's board.

ArqSynth_Parametros: Elemento "cabinet", Modulo (base / wall / tall), Largura, Altura, Profundidade, Rodape, Elevacao,
Frentes, Portas, Gavetas, Prateleiras, Puxador. Its placement: its back's left corner at the floor, x along its width,
y out of the wall.

A worktop (0.170): an IfcSystemFurnitureElement WORKSURFACE over base units (core/kitchens.worktop: their footprints
out past their fronts, joined at the corners), extruded up its thickness from their top. Tied to them (Elemento
"worktop", Hospedeiros, Beirado, Espessura): made again when they change, removed with the last of them."""

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import cabinets as core_cab
from ..core import kitchens
from . import catalog
from .edit import EditRefused

api = ifcopenshell.api
NAMES = {"Modulo": "kind", "Largura": "width", "Altura": "height", "Profundidade": "depth", "Rodape": "plinth",
         "Elevacao": "elevation", "Frentes": "fronts", "Portas": "doors", "Gavetas": "drawers",
         "Prateleiras": "shelves", "Puxador": "handle", "Interior": "interior",
         "Cego": "blind", "LadoCanto": "corner_side",                       # (0.239: a blind corner unit)
         "Braco": "arm",                                                   # (0.240: an L corner unit)
         "Acabamento": "finish",                                           # (0.243: the fronts' finish)
         "Divisoes": "splits"}                                             # (0.244: its divisions' places)
KIND_TYPE = {"base": ("Móvel inferior", "Base unit"), "wall": ("Móvel superior", "Wall unit"),
             "tall": ("Coluna", "Tall unit"), "wardrobe": ("Roupeiro", "Wardrobe")}
TEXTS = ("kind", "fronts", "handle", "interior", "corner_side", "finish", "splits")
COUNTS = ("doors", "drawers", "shelves")


class CabinetMixin:
    def cabinet_params(self, guid):
        """core.cabinets.Cabinet of a cabinet made by this program."""
        p = self._params(self.by_guid(guid))
        values = {}
        for ifc_name, key in NAMES.items():
            if p.get(ifc_name) is None:
                continue
            v = p[ifc_name]
            values[key] = str(v) if key in TEXTS else int(v) if key in COUNTS else float(v)
        return core_cab.Cabinet.of(values.pop("kind", "base"), **values)

    def _set_cabinet_body(self, element):
        f, u = self.file, 1.0 / self.unit_scale
        c = self.cabinet_params(element.GlobalId)
        problem = core_cab.validate(c)
        if problem:
            raise EditRefused(problem)
        items, fronts = [], []
        for panel in core_cab.layout(c).panels:
            x0, y0, z0, x1, y1, z1 = panel.box
            dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
            if min(dx, dy, dz) <= 1e-6:
                continue
            if panel.role == "carousel":                # (0.240) a carousel's tray: three quarters of a disc
                ring = [(float(x * u), float(y * u)) for x, y in core_cab.carousel_ring(panel, c.corner_side)]
                profile = f.createIfcArbitraryClosedProfileDef("AREA", None, f.createIfcIndexedPolyCurve(
                    f.createIfcCartesianPointList2D(ring + ring[:1]), None, False))
            else:
                profile = f.createIfcRectangleProfileDef("AREA", None, f.createIfcAxis2Placement2D(
                    f.createIfcCartesianPoint((float((x0 + x1) / 2 * u), float((y0 + y1) / 2 * u))), None),
                    float(dx * u), float(dy * u))
            items.append(f.createIfcExtrudedAreaSolid(
                profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, float(z0 * u))), None, None),
                f.createIfcDirection((0.0, 0.0, 1.0)), float(dz * u)))
            if panel.material.startswith("front"):
                fronts.append(items[-1])
        self._clear_representations(element)
        api.geometry.assign_representation(f, product=element, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))
        lang = "en" if element.ObjectType in [n[1] for n in KIND_TYPE.values()] else "pt"
        self._cabinet_material(element, c, lang)
        if c.finish != "melamine":                   # (0.243) its fronts in their finish's colour
            style = self._material_style(self._material(catalog.FRONT_MATERIALS[c.finish], lang))
            for item in fronts:
                f.createIfcStyledItem(item, [style], None)
        common = ifcopenshell.util.element.get_psets(element).get("Pset_FurnitureTypeCommon")
        pset = f.by_id(common["id"]) if common else api.pset.add_pset(f, product=element, name="Pset_FurnitureTypeCommon")
        api.pset.edit_pset(f, pset=pset, properties={
            "NominalLength": c.width * u, "NominalDepth": c.overall_depth * u,
            "NominalHeight": (c.top - (c.elevation if c.kind == "wall" else 0.0)) * u, "IsBuiltIn": True})

    def _material_style(self, material):
        """(0.243) The surface style a material was made with (model._material: its own name)."""
        return next(s for s in self.file.by_type("IfcSurfaceStyle") if s.Name == material.Name)

    def _cabinet_material(self, element, c, lang):
        """(0.243) A cabinet's material: its carcass's board — with fronts of another finish, a constituent set of the
        two («Corpo», «Frentes»), one per finish, shared by the cabinets with it."""
        f = self.file
        board = self._material("melamina", lang)
        wanted = board
        if c.finish != "melamine":
            front = self._material(catalog.FRONT_MATERIALS[c.finish], lang)
            name = "{} + {}".format(board.Name, front.Name)
            wanted = next((s for s in f.by_type("IfcMaterialConstituentSet") if s.Name == name), None)
            if wanted is None:
                wanted = api.material.add_material_set(f, name=name, set_type="IfcMaterialConstituentSet")
                parts = ("Corpo", "Frentes") if lang == "pt" else ("Carcass", "Fronts")
                for part, material in zip(parts, (board, front)):
                    api.material.add_constituent(f, constituent_set=wanted, material=material).Name = part
        if ifcopenshell.util.element.get_material(element, should_skip_usage=True) != wanted:
            api.material.unassign_material(f, products=[element])
            api.material.assign_material(f, products=[element], type=wanted.is_a(), material=wanted)

    def cabinet_colour(self, guid):
        """(0.243) A cabinet's colour on screen: its fronts' finish's (#rrggbb), or None for fronts of melamine (its
        class's colour) and for anything else."""
        e = self.by_guid(guid)
        finish = self._params(e).get("Acabamento") if e is not None and e.is_a("IfcFurniture") else None
        if not finish or finish == "melamine" or finish not in catalog.FRONT_MATERIALS:
            return None
        r, g, b = catalog.MATERIALS[catalog.FRONT_MATERIALS[finish]].color
        return "#{:02x}{:02x}{:02x}".format(int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))

    def add_cabinet(self, back, angle, cabinet, name, lang="pt", storey=None):
        """A cabinet (core.cabinets.Cabinet) with the middle of its back at `back` (plan, its floor's height in
        back[2]), its width along `angle` degrees. Returns the IfcFurniture."""
        f = self.file
        problem = core_cab.validate(cabinet)
        if problem:
            raise EditRefused(problem)
        a = np.radians(float(angle))
        x = np.array((np.cos(a), np.sin(a), 0.0))
        y = np.cross((0.0, 0.0, 1.0), x)
        origin = np.asarray(back, dtype=float) - x * cabinet.width / 2
        element = api.root.create_entity(f, ifc_class="IfcFurniture", name=name, predefined_type="USERDEFINED")
        element.ObjectType = KIND_TYPE[cabinet.kind][0 if lang == "pt" else 1]
        m = np.eye(4)
        m[:3, 0], m[:3, 1], m[:3, 3] = x, y, origin
        self._place(element, m)
        container = self.storey(storey) if storey is not None else self.storey_at(float(origin[2]))
        api.spatial.assign_container(f, products=[element], relating_structure=container)
        api.material.assign_material(f, products=[element], type="IfcMaterial", material=self._material("melamina",
                                                                                                         lang))
        self._mark(element, "cabinet")
        self._set_params(element, {ifc_name: getattr(cabinet, key) for ifc_name, key in NAMES.items()})
        self._set_cabinet_body(element)
        return element

    def set_cabinet(self, guid, **changes):
        """A cabinet's parameters changed (core.cabinets.Cabinet's fields; its back's left corner stays — a wider
        one grows to its right)."""
        element, _ = self._require(guid, "cabinet")
        back = {key: ifc_name for ifc_name, key in NAMES.items()}
        values = {}
        for key, value in changes.items():
            if key not in back or value is None:
                continue
            values[back[key]] = str(value) if key in TEXTS else int(value) if key in COUNTS else float(value)
        if "Modulo" in values:                      # (another kind: its usual sizes, unless given)
            kind = values["Modulo"]
            if kind not in core_cab.KINDS:
                raise EditRefused("cabinet_bad")
            for key, v in core_cab.DEFAULTS[kind].items():
                values.setdefault(back[key], str(v) if key in TEXTS else int(v) if key in COUNTS else float(v))
            values.setdefault("Interior", "")              # (back to one compartment unless its kind has more)
            element.ObjectType = KIND_TYPE[kind][0]
        self._set_params(element, values)
        self._set_cabinet_body(element)           # (refused: the command's transaction is thrown away)

    # ------------------------------------------------------------ worktops (0.170)

    def _cabinet_spot(self, guid):
        """(back's middle (2,), angle, width, overall depth, top, (0.240) its second arm, its corner's side) of a
        cabinet."""
        c = self.cabinet_params(guid)
        m = self.placement(guid)
        x = m[:3, 0] / np.linalg.norm(m[:3, 0])
        back = m[:3, 3] + x * c.width / 2
        return back[:2], float(np.degrees(np.arctan2(x[1], x[0]))), c.width, c.overall_depth, c.top, c.arm, \
            c.corner_side

    def worktop_hosts(self, guid):
        p = self._params(self.by_guid(guid))
        return [g for g in (p.get("Hospedeiros") or "").split(";") if g]

    def add_worktop(self, hosts, name, lang="pt", overhang=kitchens.OVERHANG, thickness=kitchens.WORKTOP):
        """A worktop over these base units (their GlobalIds): an IfcSystemFurnitureElement WORKSURFACE, their
        footprints out to `overhang` past their fronts, `thickness` thick on their top. Tied to them. Returns it."""
        f = self.file
        element = api.root.create_entity(f, ifc_class="IfcSystemFurnitureElement", name=name,
                                         predefined_type="WORKSURFACE")
        container = self.storey(self.storey_of(hosts[0]))
        self._place(element, np.eye(4))                 # (its own place: on its cabinets, when its body is made)
        api.spatial.assign_container(f, products=[element], relating_structure=container)
        api.material.assign_material(f, products=[element], type="IfcMaterial", material=self._material("bancada",
                                                                                                         lang))
        self._mark(element, "worktop")
        self._set_params(element, {"Hospedeiros": ";".join(hosts), "Beirado": float(overhang),
                                   "Espessura": float(thickness)})
        self._set_worktop_body(element)
        return element

    def worktop_shape(self, guid):
        """(outline [(x, y)] plan, [(length, width)] its pieces, top, thickness) of a worktop, from its cabinets now."""
        p = self._params(self.by_guid(guid))
        hosts = [g for g in self.worktop_hosts(guid) if self.by_guid(g) is not None]
        spots = [self._cabinet_spot(g) for g in hosts]
        outline, pieces = kitchens.worktop([(s[0], s[1], s[2], s[3], s[5], s[6]) for s in spots],
                                           float(p.get("Beirado") or 0.0))
        top = max((s[4] for s in spots), default=0.0)
        return outline, pieces, top, float(p.get("Espessura") or kitchens.WORKTOP)

    def _worktop_holes(self, outline):
        """The cut-outs inside a worktop's outline (0.171: hobs, kitchen sinks): [rings], and their fingerprint."""
        from shapely.geometry import Polygon
        poly = Polygon(outline)
        holes = [ring for ring in self.worktop_cutouts() if poly.contains(Polygon(ring))]
        key = ";".join(",".join("{:.3f}".format(float(v)) for p in ring for v in p[:2]) for ring in holes)
        return holes, key

    def _set_worktop_body(self, element):
        f, u = self.file, 1.0 / self.unit_scale
        outline, _pieces, top, thickness = self.worktop_shape(element.GlobalId)
        if not outline:
            raise EditRefused("worktop_none")
        m = np.eye(4)
        m[:3, 3] = (outline[0][0], outline[0][1], top)
        self._place(element, m)
        o = outline[0]

        def curve(ring):
            coords = [(float((p[0] - o[0]) * u), float((p[1] - o[1]) * u)) for p in ring]
            coords.append(coords[0])
            return f.createIfcIndexedPolyCurve(f.createIfcCartesianPointList2D(coords), None, False)

        holes, key = self._worktop_holes(outline)
        if holes:
            profile = f.createIfcArbitraryProfileDefWithVoids("AREA", None, curve(outline), [curve(h) for h in holes])
        else:
            profile = f.createIfcArbitraryClosedProfileDef("AREA", None, curve(outline))
        self._set_params(element, {"Recortes": key})
        items = [f.createIfcExtrudedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)), None, None),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(thickness * u))]
        self._clear_representations(element)
        api.geometry.assign_representation(f, product=element, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))

    def follow_worktops(self, changed):
        """The worktops over the cabinets among `changed` (moved, made wider, removed) made again over them; one
        whose cabinets are all gone, removed."""
        tops = self.file.by_type("IfcSystemFurnitureElement")
        if not tops:
            return []
        wanted, made = set(changed), []
        for e in list(tops):
            if self._params(e).get("Elemento") != "worktop":
                continue
            hosts = self.worktop_hosts(e.GlobalId)
            alive = [g for g in hosts if self.by_guid(g) is not None]
            if not wanted & set(hosts) and len(alive) == len(hosts):
                outline = self.worktop_shape(e.GlobalId)[0]
                if not outline or self._worktop_holes(outline)[1] == (self._params(e).get("Recortes") or ""):
                    continue                             # (none of its cabinets changed nor went; its cut-outs
                    #                                      neither: a hob or a sink put, moved, taken away)
            if not alive:
                api.root.remove_product(self.file, product=e)
                continue
            if len(alive) != len(hosts):
                self._set_params(e, {"Hospedeiros": ";".join(alive)})
            self._set_worktop_body(e)
            made.append(e.GlobalId)
        return made

    def worktops(self):
        """{GlobalId: (outline, pieces, top, thickness)} of the worktops made by this program."""
        out = {}
        for e in self.file.by_type("IfcSystemFurnitureElement"):
            if self._params(e).get("Elemento") == "worktop":
                out[e.GlobalId] = self.worktop_shape(e.GlobalId)
        return out

    # ------------------------------------------------------------ ovens in tall units (0.242)

    def oven_spot(self, guid):
        """Where a tall unit's oven goes: (the middle of its back (3,), its angle) — in the middle of its width, its
        door over the unit's fronts' face."""
        from ..core import appliances as core_app
        c = self.cabinet_params(guid)
        m = self.placement(guid)
        x = m[:3, 0] / np.linalg.norm(m[:3, 0])
        y = m[:3, 1] / np.linalg.norm(m[:3, 1])
        depth = core_app.size("oven_column")[1]
        back = m[:3, 3] + x * c.width / 2 + y * (core_cab.BACK + c.depth + 0.02 - depth)
        return back, float(np.degrees(np.arctan2(x[1], x[0])))

    def follow_ovens(self, changed):
        """The oven in each tall unit with an oven housing among `changed` (made, moved, changed): put in its housing
        — made when it has none (core/appliances "oven_column", tied to it: Hospedeiro), placed again when the unit
        moved —; one whose unit is gone or has no housing now, removed. Returns the ovens moved."""
        from .appliances import appliance_frame
        wanted = set(changed)
        ovens = {}                                      # (a unit deleted: changed may not name it — every oven seen)
        for e in self.file.by_type("IfcElectricAppliance"):
            p = self._params(e)
            if p.get("Aparelho") == "oven_column" and p.get("Hospedeiro"):
                ovens[p["Hospedeiro"]] = e
        moved = []
        for host, e in list(ovens.items()):
            unit = self.by_guid(host)
            if unit is None or (host in wanted and self.cabinet_params(host).fronts != "oven"):
                api.root.remove_product(self.file, product=e)
                del ovens[host]
        for guid in wanted:
            unit = self.by_guid(guid)
            if unit is None or not unit.is_a("IfcFurniture") or self._params(unit).get("Elemento") != "cabinet" \
                    or self.cabinet_params(guid).fronts != "oven":
                continue
            back, angle = self.oven_spot(guid)
            e = ovens.get(guid)
            if e is None:
                pt = unit.ObjectType == KIND_TYPE["tall"][0]       # (named in its unit's language)
                name = "{} — {}".format(unit.Name, "forno" if pt else "oven")
                e = self.add_appliance(back, angle, "oven_column", name, "pt" if pt else "en",
                                       storey=self.storey_of(guid))
                self._set_params(e, {"Hospedeiro": guid})
                continue
            if not np.allclose(self._placement_si(e), appliance_frame(back, angle), atol=1e-6):
                self._place(e, appliance_frame(back, angle), should_transform_children=True)
                self._set_params(e, {"Angulo": float(angle)})
                moved.append(e.GlobalId)
        return moved

    def cabinets(self, guids=None):
        """{GlobalId: core.cabinets.Cabinet} of the cabinets made by this program (those of `guids`, or all)."""
        out = {}
        for e in self.file.by_type("IfcFurniture"):
            if (guids is None or e.GlobalId in guids) and self._params(e).get("Elemento") == "cabinet":
                out[e.GlobalId] = self.cabinet_params(e.GlobalId)
        return out
