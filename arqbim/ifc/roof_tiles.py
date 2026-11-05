"""A roof's tiles in the IFC (0.279), mixed into IfcModel: an IfcCovering over the roof (IfcRelCoversBldgElements),
typed by an IfcCoveringType ROOFING named after its tile, of ceramic tile. Its body a MappedRepresentation: the tile's
shape kept once (an IfcRepresentationMap, an IfcTriangulatedFaceSet) mapped onto each whole tile's place, the ridge
tile's onto each of its places, and the cut tiles one mesh of their own mapped once — a thousand tiles, a thousand
IfcMappedItems of one shape (as the add-on instanced them). Read straight from the file for the screen (model's
_mapped_mesh), not through the kernel.

Its quantities: Qto_CoveringBaseQuantities.GrossArea (its roof's waters, along their slope) and the program's
ArqSynth_Telhado — the tiles (Telhas), how many of them cut (Cortadas), the ridge tiles (Cumeeiras), their weight.

ArqSynth_Parametros: Elemento "roof_tiles", Cobertura (its roof's GlobalId), Telha (the tile's key), Desfasado
(every other row half a tile across). Its roof changed (made again, given carpentry…), it is laid again
(follow_tiles); its roof removed, it goes with it."""

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.guid
import ifcopenshell.util.element

from ..core import roof_tiles as core_tiles
from .edit import EditRefused

api = ifcopenshell.api
TILES_QTO = "ArqSynth_Telhado"


class RoofTilesMixin:
    # ------------------------------------------------------------ the tiles to lay (0.281: the user's own too)

    def tile_types(self):
        """The project's own tiles (registered from a component): {"t:<GlobalId>": TileSpec} — each an
        IfcCoveringType ROOFING (kind "tile_type") holding its shape (a RepresentationMap) and its measures."""
        out = {}
        for type_ in self.file.by_type("IfcCoveringType"):
            if self.kind_of(type_.GlobalId) != "tile_type" or not type_.RepresentationMaps:
                continue
            p = self._params(type_)
            faces = [i for i in type_.RepresentationMaps[0].MappedRepresentation.Items
                     if i.is_a("IfcTriangulatedFaceSet")]
            if not faces:
                continue
            s, verts, tris = self.unit_scale, [], []
            for face in faces:
                base = len(verts)
                verts += [tuple(float(c) * s for c in pt) for pt in face.Coordinates.CoordList]
                tris += [tuple(base + int(i) - 1 for i in t) for t in face.CoordIndex]
            spec = core_tiles.TileSpec(
                "t:" + type_.GlobalId, type_.Name or "", type_.Name or "", float(p.get("LarguraUtil") or 0.2),
                float(p.get("Galga") or 0.3), float(p.get("Largura") or 0.2), float(p.get("Comprimento") or 0.3),
                max(v[2] for v in verts), float(p.get("Peso") or 0.0), bool(p.get("Desfasado")), "custom",
                custom=(tuple(verts), tuple(tris)))
            out[spec.key] = spec
        return out

    def tile_spec(self, key):
        """A tile by its key: the add-on's, or one of the project's own; None."""
        return core_tiles.TILES.get(key) or (self.tile_types().get(key) if str(key).startswith("t:") else None)

    def tile_choices(self, lang="pt"):
        """[(key, name)] of the tiles to choose from: the add-on's, then the project's own."""
        specs = list(core_tiles.TILES.values()) + list(self.tile_types().values())
        return [(s.key, s.name_pt if lang == "pt" else s.name_en) for s in specs]

    def register_tile(self, verts, tris, name, cover_width, gauge, weight, stagger, lang="pt"):
        """(0.281) A tile of the user's own (the add-on's «Registar telha»): its mesh (metres, as the add-on takes it:
        its corner at the origin, x its width, y down the slope, z up), its cover width, gauge, weight (kg) and
        whether its rows are staggered — an IfcCoveringType ROOFING keeping its shape, as laid. Returns its key."""
        spec = core_tiles.custom_spec("t:new", name, verts, tris, cover_width, gauge, weight, stagger)
        if not 0.02 <= spec.cover_width <= 3.0 or not 0.02 <= spec.gauge <= 3.0:
            raise EditRefused("tile_measures")
        f = self.file
        type_ = api.root.create_entity(f, ifc_class="IfcCoveringType", name=name, predefined_type="ROOFING")
        api.material.assign_material(f, products=[type_], type="IfcMaterial", material=self._material("telha", lang))
        type_.RepresentationMaps = [self._shape_map(*core_tiles.tile_mesh(spec), True)]
        self._mark(type_, "tile_type")
        self._set_params(type_, {"LarguraUtil": spec.cover_width, "Galga": spec.gauge, "Largura": spec.width,
                                 "Comprimento": spec.length, "Peso": spec.weight, "Desfasado": spec.stagger})
        return "t:" + type_.GlobalId

    # ------------------------------------------------------------ a roof's

    def tiles_of(self, roof_guid):
        """The roof's tiles (its IfcCovering), or None."""
        roof = self.by_guid(roof_guid)
        for rel in getattr(roof, "HasCoverings", None) or ():
            for covering in rel.RelatedCoverings:
                if self.kind_of(covering.GlobalId) == "roof_tiles":
                    return covering
        return None

    def tiles_summary(self, roof_guid):
        """{tile (its key), stagger, tiles, cut, caps, weight (kg), area (m²)} of the roof's tiles, or None."""
        covering = self.tiles_of(roof_guid)
        if covering is None:
            return None
        psets = ifcopenshell.util.element.get_psets(covering)
        q, p = psets.get(TILES_QTO, {}), psets.get("ArqSynth_Parametros", {})
        return {"tile": p.get("Telha"), "stagger": bool(p.get("Desfasado")), "tiles": int(q.get("Telhas") or 0),
                "cut": int(q.get("Cortadas") or 0), "caps": int(q.get("Cumeeiras") or 0),
                "weight": float(q.get("Peso") or 0.0),
                "area": float(psets.get("Qto_CoveringBaseQuantities", {}).get("GrossArea") or 0.0)}

    def set_roof_tiles(self, guid, key=None, stagger=None, lang="pt"):
        """(0.279) A pitched roof's tiles laid (again): key, the tile (None: the one it has, else the add-on's
        Marselha); stagger: every other row half a tile across (None: as it was, else as the tile is laid).
        EditRefused for a flat or extruded roof. Returns the IfcCovering."""
        roof, _ = self._require(guid, "roof")
        old = self.tiles_of(guid)
        params = self._params(old) if old is not None else {}
        key = key or params.get("Telha") or core_tiles.DEFAULT
        spec = self.tile_spec(key)
        if spec is None:
            raise EditRefused("not_editable")
        if stagger is None and "Desfasado" in params and params.get("Telha") == key:     # (another tile: its own)
            stagger = bool(params["Desfasado"])
        stagger = spec.stagger if stagger is None else bool(stagger)
        try:
            waters, edges, _sides = self.roof_waters(guid)
        except EditRefused:
            raise EditRefused("roof_tiles_form") from None
        tiling = core_tiles.lay(waters, edges, spec, stagger)
        if old is not None:
            self.remove_tiles(old)
        return self._make_tiles(roof, spec, stagger, tiling, lang)

    def remove_roof_tiles(self, guid):
        """(0.279) A roof's tiles taken away."""
        covering = self.tiles_of(guid)
        if covering is None:
            return False
        self.remove_tiles(covering)
        return True

    def remove_tiles(self, covering):
        """A roof's tiles gone: the covering, its ties, its maps and their shapes — its body taken apart here, entity
        by entity (all of it is its own: IfcOpenShell's remove_product searched the thousands of them, 4 s)."""
        f = self.file
        shape = covering.Representation
        doomed, maps = [], {}
        if shape is not None:
            covering.Representation = None
            doomed.append(shape)
            for rep in shape.Representations:
                doomed.append(rep)
                directions = {}
                for item in rep.Items:
                    if not item.is_a("IfcMappedItem"):
                        continue
                    target = item.MappingTarget
                    doomed += [item, target, target.LocalOrigin]
                    directions.update({d.id(): d for d in (target.Axis1, target.Axis2, target.Axis3) if d is not None})
                    maps[item.MappingSource.id()] = item.MappingSource
                doomed += list(directions.values())
            for shape_map in maps.values():
                origin, rep = shape_map.MappingOrigin, shape_map.MappedRepresentation
                doomed += [shape_map, origin, origin.Location, rep]
                for item in rep.Items:
                    doomed += [item, item.Coordinates] if item.is_a("IfcTessellatedFaceSet") else [item]
        for entity in doomed:
            f.remove(entity)
        self.uncover(covering)
        api.root.remove_product(f, product=covering)

    def follow_tiles(self, changed):
        """The tiles of the roofs changed laid again on them (a roof removed takes its tiles: drop_tiles). Returns
        what it made."""
        out = []
        made = set(getattr(self, "made", None) or ())
        for g in dict.fromkeys(changed):
            e = self.by_guid(g)
            if e is None or not e.is_a("IfcRoof"):
                continue
            covering = self.tiles_of(g)
            if covering is None or covering.GlobalId in made:          # (made in this very step: as asked)
                continue
            try:
                out.append(self.set_roof_tiles(g).GlobalId)
            except EditRefused:                         # (made flat: no tiles on it)
                self.remove_roof_tiles(g)
        return out

    def drop_tiles(self, roof_guid):
        """A roof being removed: its tiles with it."""
        covering = self.tiles_of(roof_guid)
        if covering is not None:
            self.remove_tiles(covering)

    # ------------------------------------------------------------ made

    def _tile_type(self, spec, lang):
        if spec.key.startswith("t:"):                    # (0.281: one of the project's own: its own type)
            return self.by_guid(spec.key[2:])
        name = spec.name_pt if lang == "pt" else spec.name_en
        for type_ in self.file.by_type("IfcCoveringType"):
            if type_.Name == name and type_.PredefinedType == "ROOFING" and self.kind_of(type_.GlobalId) is None:
                return type_
        type_ = api.root.create_entity(self.file, ifc_class="IfcCoveringType", name=name, predefined_type="ROOFING")
        api.material.assign_material(self.file, products=[type_], type="IfcMaterial",
                                     material=self._material(spec.material, lang))
        return type_

    def _shape_map(self, verts, tris, closed):
        """An IfcRepresentationMap at its origin holding one IfcTriangulatedFaceSet (vertices in metres)."""
        f, u = self.file, 1.0 / self.unit_scale
        points = f.createIfcCartesianPointList3D([tuple(float(c) * u for c in p) for p in verts])
        faces = f.createIfcTriangulatedFaceSet(points, None, closed, [tuple(int(i) + 1 for i in t) for t in tris],
                                               None)
        origin = f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)), None, None)
        return f.createIfcRepresentationMap(origin, f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "Tessellation", [faces]))

    def _mapped(self, shape_map, placements):
        """IfcMappedItems of a map onto [(origin, axes)] (axes shared by those that share them)."""
        f, u = self.file, 1.0 / self.unit_scale
        directions, items = {}, []
        for origin, axes in placements:
            key = tuple(round(float(c), 12) for c in axes.ravel())
            if key not in directions:
                directions[key] = [f.createIfcDirection(tuple(float(c) for c in row)) for row in axes]
            x, y, z = directions[key]
            target = f.createIfcCartesianTransformationOperator3D(
                x, y, f.createIfcCartesianPoint(tuple(float(c) * u for c in origin)), None, z)
            items.append(f.createIfcMappedItem(shape_map, target))
        return items

    def _make_tiles(self, roof, spec, stagger, tiling, lang):
        f = self.file
        covering = api.root.create_entity(f, ifc_class="IfcCovering", name="{} — {}".format(
            "Telhado" if lang == "pt" else "Tiles", roof.Name or ""))
        type_ = self._tile_type(spec, lang)
        api.type.assign_type(f, related_objects=[covering], relating_type=type_, should_map_representations=False)
        self._place(covering, self._placement_si(roof))
        storey = self.storey_of(roof.GlobalId)
        if storey:
            api.spatial.assign_container(f, products=[covering], relating_structure=self.storey(storey))
        self._mark(covering, "roof_tiles")
        self._set_params(covering, {"Cobertura": roof.GlobalId, "Telha": spec.key, "Desfasado": bool(stagger)})
        items = []
        if tiling.whole:
            items += self._mapped(self._shape_map(*core_tiles.tile_mesh(spec), True), tiling.whole)
        if tiling.caps:
            items += self._mapped(self._shape_map(*core_tiles.tile_mesh(core_tiles.CAP), True), tiling.caps)
        if len(tiling.cut[1]):
            import numpy as np
            items += self._mapped(self._shape_map(*tiling.cut, False), [(np.zeros(3), np.eye(3))])
        if items:
            api.geometry.assign_representation(f, product=covering, representation=f.createIfcShapeRepresentation(
                self.body, self.body.ContextIdentifier, "MappedRepresentation", items))
        self._set_qto(covering, "Qto_CoveringBaseQuantities", {"GrossArea": tiling.area, "NetArea": tiling.area})
        self._set_qto(covering, TILES_QTO, {
            "Telhas": int(tiling.tiles), "Cortadas": int(tiling.cut_count), "Cumeeiras": int(len(tiling.caps)),
            "Peso": f.createIfcMassMeasure(float(tiling.weight))})                 # (an IfcQuantityWeight)
        self.file.create_entity("IfcRelCoversBldgElements", GlobalId=ifcopenshell.guid.new(),
                                OwnerHistory=api.owner.create_owner_history(f),
                                RelatingBuildingElement=roof, RelatedCoverings=[covering])
        return covering
