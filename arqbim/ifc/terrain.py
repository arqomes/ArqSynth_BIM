"""The terrain in the IFC (0.155, Phase 7, step 3): an IfcGeographicElement TERRAIN in the site — not in a storey —
whose body is a closed IfcTriangulatedFaceSet: the surface through the survey points on top, upright sides along
its border, a flat base a little under its lowest point (as Revit's toposolid). Its material "Solo natural"
(category "earth": hatched so when cut). The survey points are its surface's corners; the contour lines' interval
and the base are its parameters (the program's pset), so it is made again when they change."""

import numpy as np

import ifcopenshell.api as api
import ifcopenshell.util.element

from ..core import earthworks
from ..core import terrain as geo


class TerrainMixin:
    def _site(self):
        sites = self.file.by_type("IfcSite")
        if sites:
            return sites[0]
        site = api.root.create_entity(self.file, ifc_class="IfcSite", name="Terreno")
        projects = self.file.by_type("IfcProject")
        if projects:
            api.aggregate.assign_object(self.file, products=[site], relating_object=projects[0])
        api.geometry.edit_object_placement(self.file, product=site)
        return site

    def add_terrain(self, points, name, lang="pt", interval=geo.DEFAULT_INTERVAL, depth=geo.DEFAULT_DEPTH):
        """A terrain through the points (x, y, z: program coordinates, m) — or ValueError when they make no surface
        (fewer than three, all in a line). Returns it."""
        made = geo.tin(points)
        if made is None:
            raise ValueError("no surface")
        f = self.file
        terrain = api.root.create_entity(f, ifc_class="IfcGeographicElement", name=name, predefined_type="TERRAIN")
        api.spatial.assign_container(f, products=[terrain], relating_structure=self._site())
        self._mark(terrain, "terrain")
        verts, _tris = made
        base = float(verts[:, 2].min()) - float(depth)
        self._set_params(terrain, {"Equidistancia": float(interval), "Base": base})
        self._terrain_body(terrain, made)
        api.material.assign_material(f, products=[terrain], type="IfcMaterial", material=self._material("solo", lang))
        return terrain

    def _terrain_body(self, terrain, made):
        """Its placement at its lowest corner (plan) and its solid there, from (verts, triangles) of the surface."""
        f, u = self.file, 1.0 / self.unit_scale
        verts, tris = made
        base = float(self._params(terrain).get("Base", float(verts[:, 2].min()) - geo.DEFAULT_DEPTH))
        base = min(base, float(verts[:, 2].min()) - 0.01)          # (never above its lowest point)
        corner = np.array((float(verts[:, 0].min()), float(verts[:, 1].min()), 0.0))
        m = np.eye(4)
        m[:3, 3] = corner
        self._place(terrain, m)
        sv, st = geo.solid(verts - corner, tris, base)
        coords = f.createIfcCartesianPointList3D([tuple(float(c * u) for c in p) for p in sv])
        faces = f.createIfcTriangulatedFaceSet(coords, None, True, [tuple(int(k) + 1 for k in t) for t in st], None)
        old = [r for r in (terrain.Representation.Representations if terrain.Representation else ())
               if r.RepresentationIdentifier == "Body"]
        for rep in old:
            api.geometry.unassign_representation(f, product=terrain, representation=rep)
            api.geometry.remove_representation(f, representation=rep)
        api.geometry.assign_representation(f, product=terrain, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "Tessellation", [faces]))
        self._set_params(terrain, {"Base": base})

    def _terrain_faces(self, e):
        rep = next((r for r in (e.Representation.Representations if e.Representation else ())
                    if r.RepresentationIdentifier == "Body"), None)
        if rep is None:
            return None
        return next((i for i in rep.Items if i.is_a("IfcTriangulatedFaceSet")), None)

    def terrain_points(self, guid):
        """The survey points of a terrain made by this program — its surface's corners (program coordinates, m):
        (N, 3)."""
        e = self.by_guid(guid)
        faces = self._terrain_faces(e)
        if faces is None:
            return np.zeros((0, 3))
        pts = np.array(faces.Coordinates.CoordList, dtype=float) * self.unit_scale
        m = self._placement_si(e)
        world = pts @ m[:3, :3].T + m[:3, 3]
        base = float(self._params(e).get("Base", world[:, 2].min()))
        return world[world[:, 2] > base + 1e-6]

    def terrain_surface(self, guid):
        """(verts, triangles) of a terrain's surface, program coordinates — or None."""
        made = geo.tin(self.terrain_points(guid))
        return made

    def set_terrain_points(self, guid, points):
        """Made again through other survey points (some added, moved, taken away) — with its platforms on them, if
        it has any (0.157). ValueError when they make no surface."""
        made = geo.tin(points)
        if made is None:
            raise ValueError("no surface")
        e = self.by_guid(guid)
        depth = self.terrain_params(guid)["depth"]
        platforms = self.terrain_platforms(guid)
        if platforms:
            self._keep_survey(e, made[0])
            made = geo.tin(earthworks.proposed(made[0], platforms)) or made
        self._set_params(e, {"Base": float(made[0][:, 2].min()) - depth})
        self._terrain_body(e, made)

    # ------------------------------------------------------------ platforms, cut and fill (0.157)

    def _keep_survey(self, e, points):
        """The survey's points kept with the terrain (its body is then the proposed ground): "x,y,z;…", in the
        IFC's coordinates (m), so that a move of the program's origin leaves them right."""
        world = np.asarray(points, dtype=float) + np.asarray(self.origin, dtype=float)
        text = ";".join("{:.4f},{:.4f},{:.4f}".format(*p) for p in world)
        self._set_params(e, {"Levantamento": self.file.create_entity("IfcText", text)})     # (IfcLabel: 255 at most)

    def terrain_survey(self, guid):
        """The survey's points of a terrain (program coordinates): those kept when it got platforms, else its
        surface's corners."""
        e = self.by_guid(guid)
        text = self._params(e).get("Levantamento")
        if not text:
            return self.terrain_points(guid)
        pts = np.array([[float(c) for c in p.split(",")] for p in str(text).split(";") if p], dtype=float)
        return pts.reshape(-1, 3) - np.asarray(self.origin, dtype=float)

    def terrain_platforms(self, guid):
        """Its platforms ([earthworks.Platform], program coordinates)."""
        import json
        e = self.by_guid(guid)
        text = self._params(e).get("Plataformas") if e is not None else None
        if not text:
            return []
        shift = np.asarray(self.origin, dtype=float)[:2]
        out = []
        for item in json.loads(text):
            plat = earthworks.Platform.from_dict(item)
            plat.outline = [(x - shift[0], y - shift[1]) for x, y in plat.outline]
            out.append(plat)
        return out

    def set_terrain_platforms(self, guid, platforms):
        """The terrain with these platforms (none: back to its survey): its body the proposed ground."""
        import json
        e = self.by_guid(guid)
        survey = self.terrain_survey(guid)
        if platforms:
            self._keep_survey(e, survey)
        shift = np.asarray(self.origin, dtype=float)[:2]
        stored = []
        for plat in platforms:
            d = plat.to_dict()
            d["outline"] = [[round(x + float(shift[0]), 4), round(y + float(shift[1]), 4)] for x, y in d["outline"]]
            stored.append(d)
        self._set_params(e, {"Plataformas": self.file.create_entity("IfcText", json.dumps(stored, ensure_ascii=False))})
        made = geo.tin(earthworks.proposed(survey, platforms))
        if made is None:
            raise ValueError("no surface")
        depth = self.terrain_params(guid)["depth"]
        low = min(float(made[0][:, 2].min()), float(survey[:, 2].min()))
        self._set_params(e, {"Base": low - depth})
        self._terrain_body(e, made)

    def terrain_volumes(self, guid):
        """(cut, fill) m³ of a terrain's platforms: between its survey and its proposed ground."""
        if not self.terrain_platforms(guid):
            return 0.0, 0.0
        return earthworks.volumes(self.terrain_survey(guid), self.terrain_points(guid))

    def terrain_params(self, guid):
        """{interval of its contour lines, depth of its base under its lowest point, base} (m)."""
        e = self.by_guid(guid)
        p = self._params(e)
        pts = self.terrain_points(guid)
        low = float(pts[:, 2].min()) if len(pts) else 0.0
        base = float(p.get("Base", low - geo.DEFAULT_DEPTH))
        return {"interval": float(p.get("Equidistancia") or geo.DEFAULT_INTERVAL), "depth": max(low - base, 0.01),
                "base": base}

    def terrain_interval(self, guid):
        """The interval of a terrain's contour lines (m) — quick: its parameter only."""
        e = self.by_guid(guid)
        return float((self._params(e) if e is not None else {}).get("Equidistancia") or geo.DEFAULT_INTERVAL)

    def set_terrain_params(self, guid, interval=None, depth=None):
        e = self.by_guid(guid)
        if interval is not None:
            self._set_params(e, {"Equidistancia": float(max(interval, 0.05))})
        if depth is not None:
            made = geo.tin(self.terrain_points(guid))
            if made is not None:
                self._set_params(e, {"Base": float(made[0][:, 2].min()) - float(max(depth, 0.05))})
                self._terrain_body(e, made)

    def terrain_info(self, guid):
        """What the properties panel shows of a terrain: its points, plan area, lowest and highest point, interval."""
        made = self.terrain_surface(guid)
        params = self.terrain_params(guid)
        platforms = self.terrain_platforms(guid)
        cut, fill = self.terrain_volumes(guid) if platforms else (0.0, 0.0)
        params.update(platforms=len(platforms), cut=cut, fill=fill)
        if made is None:
            return dict(params, points=0, area=0.0, low=0.0, high=0.0)
        verts, tris = made
        survey = len(self.terrain_survey(guid)) if platforms else len(verts)
        return dict(params, points=survey, area=geo.plan_area(verts, tris), low=float(verts[:, 2].min()),
                    high=float(verts[:, 2].max()))

    def terrains(self):
        """The GlobalIds of the terrains (made by this program or not: any IfcGeographicElement TERRAIN)."""
        return [e.GlobalId for e in self.file.by_type("IfcGeographicElement")
                if ifcopenshell.util.element.get_predefined_type(e) == "TERRAIN"]
