"""Rooms (0.99) in the IFC, mixed into IfcModel: IfcSpace — its number (Name), its name (LongName), aggregated to
its storey; its body the room's plan extruded to its height; Qto_SpaceBaseQuantities (net floor area, perimeter,
height, volume); its finishes in Pset_SpaceCoveringRequirements (floor, walls, ceiling).

A room keeps the point it was made from (ArqSynth_Parametros: SalaX, SalaY): when the walls or columns of its
storey change, its plan is found again from that point (update_spaces, at the end of the same command) — as
Revit's rooms follow their bounding walls."""

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import rooms
from ..core.walls import footprint

api = ifcopenshell.api
DEFAULT_HEIGHT = 2.80
FINISHES = ("FloorCovering", "WallCovering", "CeilingCovering")


class SpaceMixin:
    # ------------------------------------------------------------ what bounds a room

    def storey_obstacles(self, storey_guid, separators=False):
        """Plan polygons of the walls and columns (made by this program) in a storey — (0.374) separators: the room
        separators too (they bound rooms, not slabs or roofs)."""
        out = []
        storey = self.storey(storey_guid)
        for rel in storey.ContainsElements or ():
            for e in rel.RelatedElements:
                kind = self.kind_of(e.GlobalId)
                if kind == "wall":
                    length, _h, thickness = self.wall_params(e.GlobalId)
                    start_cut, end_cut = self.wall_cuts(e)
                    m = self.placement(e.GlobalId)
                    pts = footprint(length, thickness, start_cut, end_cut)
                    out.append([tuple((m @ np.array((x, y, 0.0, 1.0)))[:2]) for x, y in pts])
                elif kind == "curved_wall":                         # (0.103: its band, a circle in two halves)
                    out += self.curved_wall_band(e.GlobalId)
                elif kind == "column":
                    centre, x, (a, b), _base, _top = self.column_box(e.GlobalId)
                    y = np.array((-x[1], x[0]))
                    out.append([tuple(centre + x * sx * a + y * sy * b) for sx, sy in ((-1, -1), (1, -1), (1, 1),
                                                                                       (-1, 1))])
        if separators and hasattr(self, "separator_obstacles"):  # (0.374) the room separators bound rooms too
            out += self.separator_obstacles(storey_guid)
        return out

    def room_region(self, storey_guid, point):
        return rooms.region(self.storey_obstacles(storey_guid, separators=True), point)

    # ------------------------------------------------------------ making and changing

    def _level(self, storey_guid):
        return self._elevation(self.storey(storey_guid))

    def _space_height(self, storey_guid):
        """A room's height: up to the next storey, else the usual 2,80."""
        z = self._level(storey_guid)
        above = sorted(level for _g, _n, level in self.storeys() if level > z + 1e-6)
        return (above[0] - z) if above else DEFAULT_HEIGHT

    def add_space(self, storey_guid, point, name, number, lang="pt"):
        """A room where `point` (plan) is, between the storey's walls; None if it is not enclosed there."""
        polygon = self.room_region(storey_guid, point)
        if polygon is None:
            return None
        f = self.file
        space = api.root.create_entity(f, ifc_class="IfcSpace", name=str(number), predefined_type="INTERNAL")
        space.LongName = name
        api.aggregate.assign_object(f, products=[space], relating_object=self.storey(storey_guid))
        self._mark(space, "space")
        self._set_params(space, {"SalaX": float(point[0]), "SalaY": float(point[1])})
        common = api.pset.add_pset(f, product=space, name="Pset_SpaceCommon")
        api.pset.edit_pset(f, pset=common, properties={"IsExternal": False})
        self._set_space_shape(space, storey_guid, polygon)
        return space

    def _set_space_shape(self, space, storey_guid, polygon):
        """A room's body (its plan extruded to its height, at its storey's level) and quantities."""
        f, u = self.file, 1.0 / self.unit_scale
        level, height = self._level(storey_guid), self._space_height(storey_guid)
        m = np.eye(4)
        m[2, 3] = level
        self._place(space, m)
        self._clear_representations(space)
        outside, holes = rooms.outline(polygon)

        def curve(ring):
            coords = [(float(x) * u, float(y) * u) for x, y in ring] + [(float(ring[0][0]) * u, float(ring[0][1]) * u)]
            if f.schema == "IFC2X3":
                return f.createIfcPolyline([f.createIfcCartesianPoint(p) for p in coords])
            return f.createIfcIndexedPolyCurve(f.createIfcCartesianPointList2D(coords), None, False)

        if holes:
            profile = f.createIfcArbitraryProfileDefWithVoids("AREA", None, curve(outside), [curve(h) for h in holes])
        else:
            profile = f.createIfcArbitraryClosedProfileDef("AREA", None, curve(outside))
        solid = f.createIfcExtrudedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)),
                                                 f.createIfcDirection((0.0, 0.0, 1.0)),
                                                 f.createIfcDirection((1.0, 0.0, 0.0))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(height * u))
        body = f.createIfcShapeRepresentation(self.body, self.body.ContextIdentifier, "SweptSolid", [solid])
        api.geometry.assign_representation(f, product=space, representation=body)
        area, perimeter = float(polygon.area), float(polygon.exterior.length)
        self._set_qto(space, "Qto_SpaceBaseQuantities", {
            "NetFloorArea": area, "GrossFloorArea": area, "NetPerimeter": perimeter * u, "Height": height * u,
            "NetVolume": area * height})

    def update_space(self, guid):
        """A room's plan found again from its point (its walls changed); left as it was if no longer enclosed.
        True if it changed."""
        space = self.by_guid(guid)
        params = self._params(space)
        storey = self.space_storey(guid)
        if storey is None or "SalaX" not in params:
            return False
        polygon = self.room_region(storey, (float(params["SalaX"]), float(params["SalaY"])))
        if polygon is None:
            return False
        before = self.space_info(guid)
        if before is not None and abs(before["area"] - polygon.area) < 1e-9 and \
                abs(before["level"] - self._level(storey)) < 1e-9:
            return False
        self._set_space_shape(space, storey, polygon)
        return True

    def update_spaces(self, storeys):
        """The rooms of these storeys found again (their walls changed). Returns those that changed."""
        wanted = set(storeys)
        return [s.GlobalId for s in self.file.by_type("IfcSpace")
                if self.space_storey(s.GlobalId) in wanted and self.update_space(s.GlobalId)]

    def set_space_data(self, guid, name=None, number=None, finishes=None, external=None):
        """A room's name, number and finishes ({"FloorCovering": …, "WallCovering": …, "CeilingCovering": …});
        (0.357) external: an exterior room (a terrace, a porch, a yard — IFC's EXTERNAL, Pset_SpaceCommon.IsExternal)
        or an interior one."""
        space = self.by_guid(guid)
        if name is not None:
            space.LongName = name
        if number is not None:
            space.Name = str(number)
        if external is not None:
            space.PredefinedType = "EXTERNAL" if external else "INTERNAL"
            existing = ifcopenshell.util.element.get_psets(space).get("Pset_SpaceCommon")
            common = self.file.by_id(existing["id"]) if existing else api.pset.add_pset(
                self.file, product=space, name="Pset_SpaceCommon")
            api.pset.edit_pset(self.file, pset=common, properties={"IsExternal": bool(external)})
        if finishes:
            existing = ifcopenshell.util.element.get_psets(space).get("Pset_SpaceCoveringRequirements")
            pset = self.file.by_id(existing["id"]) if existing else api.pset.add_pset(
                self.file, product=space, name="Pset_SpaceCoveringRequirements")
            api.pset.edit_pset(self.file, pset=pset, properties={k: (v or None) for k, v in finishes.items()})

    def room_program(self):
        """(0.357) The project's programme (model/room_program: [Need]) kept in it (IfcProject's «Programa»)."""
        return self._program()[1]

    def _program(self):
        from ..model import room_program
        projects = self.file.by_type("IfcProject")
        return room_program.program_from_text(self._params(projects[0]).get("Programa")) if projects else \
            (None, [], [])

    def room_program_type(self):
        """(0.475) The programme's type of building (model/program_rules.BUILDING_TYPES), or None."""
        return self._program()[0]

    def room_program_rules(self):
        """(0.475) The project's own pairs of conflicting uses [(use, use)], besides its type's."""
        return self._program()[2]

    def set_room_program(self, needs, building=None, rules=None):
        """The programme kept — (0.475) its type of building and own rules as they were when not given."""
        from ..model import room_program
        projects = self.file.by_type("IfcProject")
        if projects:
            old_type, _old, old_rules = self._program()
            building = old_type if building is None else (building or None)
            rules = old_rules if rules is None else rules
            self._set_params(projects[0], {"Programa": room_program.to_text(needs, building, rules)})

    def room_program_links(self):
        """(0.475) {room GlobalId: the programme line's id it was placed from} (its «Programa»)."""
        out = {}
        for space in self.file.by_type("IfcSpace"):
            uid = self._params(space).get("Programa")
            if uid:
                out[space.GlobalId] = str(uid)
        return out

    def set_room_need(self, guid, need):
        """(0.475) A room placed from a programme line: its name, interior / exterior, the line's id and use — and the
        Verifier's use when the line's is one of its (it is then the architect's choice, never guessed)."""
        from ..model import program_rules
        self.set_space_data(guid, name=need.name, external=need.external)
        values = {"Programa": need.uid, "UsoPrograma": need.use or ""}
        verifier = program_rules.verifier_use(need.use) if need.use else None
        if verifier and verifier != "outro":
            values["Uso"] = verifier
        self._set_params(self.by_guid(guid), values)

    # ------------------------------------------------------------ reading

    def space_storey(self, guid):
        space = self.by_guid(guid)
        for rel in getattr(space, "Decomposes", None) or ():
            if rel.RelatingObject.is_a("IfcBuildingStorey"):
                return rel.RelatingObject.GlobalId
        return None

    def space_info(self, guid):
        """{guid, number, name, area, perimeter, level, height, outline [(x, y)], holes, storey, finishes, external}
        of a room made by this program (from its body), or None."""
        space = self.by_guid(guid)
        if space is None or not space.Representation:
            return None
        solid = next((i for r in space.Representation.Representations for i in r.Items
                      if i.is_a("IfcExtrudedAreaSolid")), None)
        if solid is None:
            return None
        s = self.unit_scale
        m = self.placement(guid)

        def ring(curve):
            if curve.is_a("IfcIndexedPolyCurve"):
                pts = curve.Points.CoordList
            else:
                pts = [p.Coordinates for p in curve.Points]
            return [tuple((m @ np.array((x * s, y * s, 0.0, 1.0)))[:2]) for x, y in pts[:-1]]

        profile = solid.SweptArea
        outline = ring(profile.OuterCurve)
        holes = [ring(c) for c in getattr(profile, "InnerCurves", None) or ()]
        psets = ifcopenshell.util.element.get_psets(space)
        q = psets.get("Qto_SpaceBaseQuantities", {})
        finishes = psets.get("Pset_SpaceCoveringRequirements", {})
        external = space.PredefinedType == "EXTERNAL" or bool(psets.get("Pset_SpaceCommon", {}).get("IsExternal"))
        return {"guid": guid, "number": space.Name or "", "name": space.LongName or "",
                "area": float(q.get("NetFloorArea") or 0.0), "perimeter": float(q.get("NetPerimeter") or 0.0) * s,
                "height": float(solid.Depth) * s, "level": float(m[2, 3]), "outline": outline, "holes": holes,
                "storey": self.space_storey(guid), "finishes": {k: finishes.get(k) or "" for k in FINISHES},
                "external": external}

    def spaces(self, storey=None):
        """[space_info] of the rooms (of one storey, or all)."""
        out = []
        for s in self.file.by_type("IfcSpace"):
            if storey is not None and self.space_storey(s.GlobalId) != storey:
                continue
            info = self.space_info(s.GlobalId)
            if info is not None:
                out.append(info)
        return out

    def next_space_number(self, storey_guid):
        """The next room number on a storey: 1, 2, 3… (by the numbers there are)."""
        used = []
        for info in self.spaces(storey_guid):
            try:
                used.append(int(info["number"]))
            except ValueError:
                continue
        return str(max(used, default=0) + 1)
