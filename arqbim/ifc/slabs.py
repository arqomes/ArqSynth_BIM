"""Slabs by their outline (0.100), mixed into IfcModel: a polygon (with holes, round the columns a magic wand
found) or a true circle, extruded up by the type's thickness — IfcSlab with IfcArbitraryClosedProfileDef (or
…WithVoids) / IfcCircleProfileDef, Qto_SlabBaseQuantities.

ArqSynth_Parametros keeps its shape (Forma: retangulo — the rectangles drawn before, edited by their sides —,
poligono or circulo) and its function (Funcao: estrutural, acabamento, excluida — Pset_SlabCommon.LoadBearing
follows). The outline is read back from the body itself: there is no other copy to keep in step."""

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import slabs as core_slabs
from .edit import EditRefused

api = ifcopenshell.api
LOAD_BEARING = {"estrutural": True, "acabamento": False, "excluida": False}


class SlabMixin:
    # ------------------------------------------------------------ reading

    def slab_shape(self, guid):
        """"retangulo" | "poligono" | "circulo"."""
        e = self.by_guid(guid)
        return (self._params(e).get("Forma") or "retangulo") if e is not None else None

    def slab_function(self, guid):
        e = self.by_guid(guid)
        return (self._params(e).get("Funcao") or "estrutural") if e is not None else None

    def slab_use(self, guid):
        """(0.218) A slab's own use for its imposed load (core.actions.USES: "A", "C3"…), or "" — the project's."""
        e = self.by_guid(guid)
        return str(self._params(e).get("Uso") or "") if e is not None else ""

    def set_slab_use(self, guid, use):
        """(0.218) A slab's own use for its imposed load ("": the project's, for its floors or its roof)."""
        from ..core import actions
        slab, _ = self._require(guid, "slab")
        if use and use not in actions.USES:
            raise EditRefused("not_editable")
        self._set_params(slab, {"Uso": use or ""})

    def _slab_solid(self, slab):
        for rep in (slab.Representation.Representations if slab.Representation else ()):
            for item in rep.Items:
                if item.is_a("IfcExtrudedAreaSolid"):
                    return item
        return None

    def _local_rings(self, slab):
        """(outside, holes, radius) of a slab's plan in its own frame (m): a circle gives ([], [], radius)."""
        solid = self._slab_solid(slab)
        if solid is None:
            return None
        s = self.unit_scale
        # the solid's own position (a rectangle drawn before is at 0, 0 of its slab)
        at = np.array(solid.Position.Location.Coordinates[:2], dtype=float) * s if solid.Position else np.zeros(2)
        profile = solid.SweptArea
        if profile.is_a("IfcCircleProfileDef"):
            return [], [], float(profile.Radius) * s

        def ring(curve):
            if curve.is_a("IfcIndexedPolyCurve"):
                pts = curve.Points.CoordList
            else:
                pts = [p.Coordinates for p in curve.Points]
            pts = [(float(x) * s + at[0], float(y) * s + at[1]) for x, y in pts]
            return pts[:-1] if len(pts) > 1 and np.allclose(pts[0], pts[-1]) else pts

        if not profile.is_a("IfcArbitraryClosedProfileDef"):
            return None
        return ring(profile.OuterCurve), [ring(c) for c in getattr(profile, "InnerCurves", None) or ()], None

    def slab_outline(self, guid):
        """{shape, function, outline [(x, y)], holes, centre, radius, bottom, top, thickness, area, perimeter} of a
        slab made by this program (plan in the program's coordinates), or None."""
        slab = self.by_guid(guid)
        if slab is None or self.kind_of(guid) != "slab":
            return None
        rings = self._local_rings(slab)
        solid = self._slab_solid(slab)
        if rings is None or solid is None:
            return None
        outside, holes, radius = rings
        m = self._placement_si(slab)

        def world(pts):
            return [tuple(float(c) for c in (m @ np.array((x, y, 0.0, 1.0)))[:2]) for x, y in pts]

        thickness = float(solid.Depth) * self.unit_scale
        info = {"shape": self.slab_shape(guid), "function": self.slab_function(guid), "radius": radius,
                "bottom": float(m[2, 3]), "top": float(m[2, 3]) + thickness, "thickness": thickness,
                "centre": None}
        if radius is not None:
            info["centre"] = (float(m[0, 3]), float(m[1, 3]))
            info["outline"], info["holes"] = core_slabs.circle_ring(info["centre"], radius), []
            info["area"], info["perimeter"] = float(np.pi * radius ** 2), float(2 * np.pi * radius)
            return info
        info["outline"], info["holes"] = world(outside), [world(h) for h in holes]
        poly = core_slabs.outline_polygon(info["outline"], info["holes"])
        info["area"] = float(poly.area) if poly is not None else core_slabs.ring_area(info["outline"])
        info["perimeter"] = float(poly.exterior.length) if poly is not None else 0.0
        return info

    # ------------------------------------------------------------ the body

    def _ring_curve(self, ring):
        f, u = self.file, 1.0 / self.unit_scale
        coords = [(float(x) * u, float(y) * u) for x, y in ring]
        coords.append(coords[0])
        if f.schema == "IFC2X3":
            return f.createIfcPolyline([f.createIfcCartesianPoint(p) for p in coords])
        return f.createIfcIndexedPolyCurve(f.createIfcCartesianPointList2D(coords), None, False)

    def _set_slab_shape(self, slab, thickness, outside=None, holes=(), radius=None):
        """A slab's body: its plan (in its own frame, m) — a ring with holes, or a circle round its 0, 0 —
        extruded up `thickness`; and its quantities."""
        f, u = self.file, 1.0 / self.unit_scale
        usage = ifcopenshell.util.element.get_material(slab, should_skip_usage=False)
        if usage is not None and usage.is_a("IfcMaterialLayerSetUsage"):
            usage.LayerSetDirection = "AXIS3"
        self._clear_representations(slab)
        if radius is not None:
            profile = f.createIfcCircleProfileDef("AREA", None, f.createIfcAxis2Placement2D(
                f.createIfcCartesianPoint((0.0, 0.0)), None), float(radius * u))
            area, perimeter = float(np.pi * radius ** 2), float(2 * np.pi * radius)
        else:
            poly = core_slabs.outline_polygon(outside, holes)
            if poly is None:
                raise EditRefused("slab_outline")
            if holes:
                profile = f.createIfcArbitraryProfileDefWithVoids("AREA", None, self._ring_curve(outside),
                                                                  [self._ring_curve(h) for h in holes])
            else:
                profile = f.createIfcArbitraryClosedProfileDef("AREA", None, self._ring_curve(outside))
            area, perimeter = float(poly.area), float(poly.exterior.length)
        solid = f.createIfcExtrudedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)),
                                                 f.createIfcDirection((0.0, 0.0, 1.0)),
                                                 f.createIfcDirection((1.0, 0.0, 0.0))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(thickness * u))
        body = f.createIfcShapeRepresentation(self.body, self.body.ContextIdentifier, "SweptSolid", [solid])
        api.geometry.assign_representation(f, product=slab, representation=body)
        self._set_qto(slab, "Qto_SlabBaseQuantities", {"Width": thickness * u, "GrossArea": area, "NetArea": area,
                                                       "GrossVolume": area * thickness, "Perimeter": perimeter * u})

    # ------------------------------------------------------------ making and changing

    def add_slab_outline(self, spec, outline, bottom, name, lang="pt", storey=None, holes=(), centre=None,
                         radius=None, function="estrutural"):
        """A slab over a plan outline [(x, y)…] (with holes) — or a circle (centre, radius) —, its underside at
        `bottom`, its thickness its type's. In the storey `storey` (GlobalId), else the one its top is at."""
        f = self.file
        type_ = self.ensure_type(spec, lang)
        slab = api.root.create_entity(f, ifc_class="IfcSlab", name=name)
        api.type.assign_type(f, related_objects=[slab], relating_type=type_)
        m = np.eye(4)
        if radius is not None:
            m[:3, 3] = (float(centre[0]), float(centre[1]), float(bottom))
            local, local_holes = None, ()
        else:
            x0 = min(float(p[0]) for p in outline)
            y0 = min(float(p[1]) for p in outline)
            m[:3, 3] = (x0, y0, float(bottom))
            local = [(float(x) - x0, float(y) - y0) for x, y in outline]
            local_holes = [[(float(x) - x0, float(y) - y0) for x, y in h] for h in holes]
        self._place(slab, m)
        container = self.storey(storey) if storey is not None else self.storey_at(float(bottom) + spec.thickness)
        api.spatial.assign_container(f, products=[slab], relating_structure=container)
        self._set_slab_shape(slab, spec.thickness, local, local_holes, radius)
        common = api.pset.add_pset(f, product=slab, name="Pset_SlabCommon")
        api.pset.edit_pset(f, pset=common, properties={"IsExternal": False,
                                                       "LoadBearing": LOAD_BEARING.get(function, True)})
        self._mark(slab, "slab")
        self._set_params(slab, {"Forma": "circulo" if radius is not None else "poligono", "Funcao": function})
        return slab

    def _openings_fit(self, slab, outline_local=None, radius=None):
        """Every opening of the slab still inside the new plan (its own frame)."""
        bounds = self.opening_bounds(slab.GlobalId)
        if bounds is None:
            return True
        lo, hi = bounds
        corners = [(lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1])]
        if radius is not None:
            return all(np.hypot(x, y) <= radius + 1e-6 for x, y in corners)
        poly = core_slabs.outline_polygon(outline_local)
        if poly is None:
            return False
        grown = poly.buffer(1e-6)
        from shapely.geometry import Point
        return all(grown.contains(Point(x, y)) for x, y in corners)

    def set_slab_outline(self, guid, outline, holes=None):
        """A slab's plan made the outline [(x, y)…] (program's coordinates): edited by its corners (0.100). Its
        holes stay (or `holes`); its level, thickness and placement stay, so its openings stay where they are.
        A rectangle becomes a polygon; tied to beams, it no longer follows them (drawn by hand now)."""
        slab, _ = self._require(guid, "slab")
        if self.slab_shape(guid) == "circulo":
            raise EditRefused("slab_circle")
        rings = self._local_rings(slab)
        solid = self._slab_solid(slab)
        if rings is None or solid is None:
            raise EditRefused("not_editable")
        m = self._placement_si(slab)
        inv = np.linalg.inv(m)

        def local(pts):
            return [tuple(float(c) for c in (inv @ np.array((x, y, m[2, 3], 1.0)))[:2]) for x, y in pts]

        outside = local(outline)
        inner = rings[1] if holes is None else [local(h) for h in holes]
        poly = core_slabs.outline_polygon(outside, inner)
        if poly is None:
            inner = [h for h in inner if core_slabs.outline_polygon(outside).contains(
                core_slabs.outline_polygon(h))] if core_slabs.outline_polygon(outside) is not None else []
            poly = core_slabs.outline_polygon(outside, inner)
            if poly is None:
                raise EditRefused("slab_outline")
        if not self._openings_fit(slab, outside):
            raise EditRefused("opening_outside")
        thickness = float(solid.Depth) * self.unit_scale
        self._set_slab_shape(slab, thickness, outside, inner)
        params = {"Forma": "poligono"}
        if self._params(slab).get("Vigas"):
            params["Vigas"] = ""                     # (drawn by hand: it no longer follows the beams)
        self._set_params(slab, params)

    def set_slab_radius(self, guid, radius):
        slab, _ = self._require(guid, "slab")
        if self.slab_shape(guid) != "circulo":
            raise EditRefused("not_editable")
        if radius < 0.05:
            raise EditRefused("too_small")
        if not self._openings_fit(slab, radius=radius):
            raise EditRefused("opening_outside")
        solid = self._slab_solid(slab)
        self._set_slab_shape(slab, float(solid.Depth) * self.unit_scale, radius=float(radius))

    def set_slab_function(self, guid, function):
        """A slab's function: estrutural / acabamento / excluida (Pset_SlabCommon.LoadBearing follows). Its place
        stays (the tool puts a finish on the level, a structural slab under it)."""
        slab, _ = self._require(guid, "slab")
        if function not in core_slabs.FUNCTIONS:
            raise EditRefused("not_editable")
        self._set_params(slab, {"Funcao": function})
        existing = ifcopenshell.util.element.get_psets(slab).get("Pset_SlabCommon")
        pset = self.file.by_id(existing["id"]) if existing else api.pset.add_pset(self.file, product=slab,
                                                                                    name="Pset_SlabCommon")
        api.pset.edit_pset(self.file, pset=pset, properties={"LoadBearing": LOAD_BEARING[function]})

    def reshape_slab_thickness(self, slab, thickness):
        """A polygon / circle slab's body again with another thickness (its type changed): same plan."""
        outside, holes, radius = self._local_rings(slab)
        self._set_slab_shape(slab, thickness, outside or None, holes, radius)
