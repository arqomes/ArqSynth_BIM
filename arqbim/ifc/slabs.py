"""Slabs by their outline (0.100), mixed into IfcModel: a polygon (with holes, round the columns a magic wand
found) or a true circle, extruded up by the type's thickness — IfcSlab with IfcArbitraryClosedProfileDef (or
…WithVoids) / IfcCircleProfileDef, Qto_SlabBaseQuantities.

ArqSynth_Parametros keeps its shape (Forma: retangulo — the rectangles drawn before, edited by their sides —,
poligono or circulo) and its function (Funcao: estrutural, acabamento, excluida — Pset_SlabCommon.LoadBearing
follows). The outline is read back from the body itself: there is no other copy to keep in step.

(0.433, the addon's «piso com declive por vértice») A slab with a height of its own at each corner of its outline
(«Cotas», m over its flat top, in its outline's order): its body a closed IfcTriangulatedFaceSet (core/sloped_slab) —
its top through its corners at their heights, its underside a thickness lower —, its plan then kept beside it
(«Planta»: outside, holes, thickness, in its own frame), as there is no extrusion to read it back from."""

import json

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import outline_loops
from ..core import sloped_slab
from ..core import slabs as core_slabs
from .edit import EditRefused

api = ifcopenshell.api
LOAD_BEARING = {"estrutural": True, "acabamento": False, "excluida": False}
KEEP = object()             # (0.433) _set_slab_shape: its corners' heights as they are (by corner, or on its surface)
MAX_HEIGHT = 20.0           # m: a corner's height over (or under) the slab's top, at most


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

    def _slab_plan(self, slab):
        """(0.433) A sloped slab's plan kept beside its body: (outside, holes, thickness) in its own frame, or None."""
        text = self._params(slab).get("Planta")
        if not text:
            return None
        try:
            d = json.loads(text)
            return ([(float(x), float(y)) for x, y in d["o"]],
                    [[(float(x), float(y)) for x, y in h] for h in d.get("h") or ()], float(d["t"]))
        except (ValueError, KeyError, TypeError):
            return None

    def slab_heights(self, slab):
        """(0.433) Each outline corner's height over the slab's flat top (m, its outline's order), or None — flat."""
        if isinstance(slab, str):
            slab = self.by_guid(slab)
        text = self._params(slab).get("Cotas") if slab is not None else None
        try:
            values = [float(v) for v in json.loads(text)] if text else None
        except (ValueError, TypeError):
            return None
        return None if values is None or sloped_slab.is_flat(values) else values

    def _slab_thickness(self, slab):
        """Its thickness (m): its extrusion's depth — (0.433) a sloped slab's, its plan's —, or None."""
        solid = self._slab_solid(slab)
        if solid is not None:
            return float(solid.Depth) * self.unit_scale
        plan = self._slab_plan(slab)
        return plan[2] if plan is not None else None

    def _local_rings(self, slab):
        """(outside, holes, radius) of a slab's plan in its own frame (m): a circle gives ([], [], radius)."""
        solid = self._slab_solid(slab)
        if solid is None:
            plan = self._slab_plan(slab)            # (0.433: a sloped slab's, kept beside its body)
            return (plan[0], plan[1], None) if plan is not None else None
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
        thickness = self._slab_thickness(slab)
        if rings is None or thickness is None:
            return None
        outside, holes, radius = rings
        m = self._placement_si(slab)

        def world(pts):
            return [tuple(float(c) for c in (m @ np.array((x, y, 0.0, 1.0)))[:2]) for x, y in pts]

        heights = self.slab_heights(slab) if radius is None else None
        info = {"shape": self.slab_shape(guid), "function": self.slab_function(guid), "radius": radius,
                "bottom": float(m[2, 3]), "top": float(m[2, 3]) + thickness, "thickness": thickness,
                "centre": None,
                # (0.433) its corners' heights over its top (its outline's order), or None: flat
                "heights": heights if heights is not None and len(heights) == len(outside) else None}
        if radius is not None:
            info["centre"] = (float(m[0, 3]), float(m[1, 3]))
            info["outline"], info["holes"] = core_slabs.circle_ring(info["centre"], radius), []
            info["area"], info["perimeter"] = float(np.pi * radius ** 2), float(2 * np.pi * radius)
            return info
        info["outline"], info["holes"] = world(outside), [world(h) for h in holes]
        # (0.410) as drawn — the outline and its holes, their sides arcs or curves — while it is still this body
        info["loops"] = outline_loops.mapped(outline_loops.drawn([outside] + holes, self._params(slab).get("Desenho")),
                                             lambda p: world([p])[0])
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

    def _kept_heights(self, slab, outside):
        """(0.433) The heights its corners keep when its outline changes: the same corners, the same heights; other
        corners, the height of its top's surface where they are now."""
        old = self.slab_heights(slab)
        rings = self._local_rings(slab) if old is not None else None
        if old is None or rings is None or not outside:
            return None
        before = rings[0]
        if len(before) != len(old):
            return None
        if len(before) == len(outside):
            return list(old)
        height = sloped_slab.surface(before, old)
        return [height(float(x), float(y)) for x, y in outside]

    def _set_slab_shape(self, slab, thickness, outside=None, holes=(), radius=None, heights=KEEP):
        """A slab's body: its plan (in its own frame, m) — a ring with holes, or a circle round its 0, 0 —
        extruded up `thickness`; and its quantities. (0.433) `heights`: its outline's corners' over its top (KEEP:
        as they are; None: flat) — not all 0, its body a closed triangulated face set, its plan kept beside it."""
        f, u = self.file, 1.0 / self.unit_scale
        if heights is KEEP:
            heights = self._kept_heights(slab, outside) if radius is None else None
        if radius is not None or heights is None or len(heights) != len(outside or ()) or sloped_slab.is_flat(heights):
            heights = None
        usage = ifcopenshell.util.element.get_material(slab, should_skip_usage=False)
        if usage is not None and usage.is_a("IfcMaterialLayerSetUsage"):
            usage.LayerSetDirection = "AXIS3"
        self._clear_representations(slab)
        params = self._params(slab)
        if heights is not None:
            poly = core_slabs.outline_polygon(outside, holes)
            if poly is None:
                raise EditRefused("slab_outline")
            verts, tris = sloped_slab.body(outside, holes, heights, thickness)
            if not len(tris):
                raise EditRefused("slab_outline")
            item = f.createIfcTriangulatedFaceSet(f.createIfcCartesianPointList3D((verts * u).tolist()), None, True,
                                                  [tuple(int(i) + 1 for i in tri) for tri in tris], None)
            body = f.createIfcShapeRepresentation(self.body, self.body.ContextIdentifier, "Tessellation", [item])
            api.geometry.assign_representation(f, product=slab, representation=body)
            area, perimeter = float(poly.area), float(poly.exterior.length)
            self._set_qto(slab, "Qto_SlabBaseQuantities", {"Width": thickness * u, "GrossArea": area,
                                                           "NetArea": area, "GrossVolume": area * thickness,
                                                           "Perimeter": perimeter * u})
            plan = {"o": [[round(float(x), 6), round(float(y), 6)] for x, y in outside],
                    "h": [[[round(float(x), 6), round(float(y), 6)] for x, y in h] for h in holes],
                    "t": round(float(thickness), 6)}
            self._set_params(slab, {"Cotas": json.dumps([round(float(z), 6) for z in heights]),
                                    "Planta": json.dumps(plan, separators=(",", ":"))})
            return
        if params.get("Cotas") or params.get("Planta"):          # (flat again: no more of them)
            self._set_params(slab, {"Cotas": None, "Planta": None})
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

    def set_slab_outline(self, guid, outline, holes=None, loops=None, heights=KEEP):
        """A slab's plan made the outline [(x, y)…] (program's coordinates): edited by its corners (0.100). Its
        holes stay (or `holes`); its level, thickness and placement stay, so its openings stay where they are.
        A rectangle becomes a polygon; tied to beams, it no longer follows them (drawn by hand now).

        (0.410) Or `loops` (core/outline_loops, program's coordinates): the outline and its holes as drawn, their
        sides arcs or Bézier curves — the body made of them in pieces, the drawing kept beside it («Desenho»).

        (0.433) A sloped slab's corners keep their heights (`heights`: the new corners' own)."""
        slab, _ = self._require(guid, "slab")
        if self.slab_shape(guid) == "circulo":
            raise EditRefused("slab_circle")
        rings = self._local_rings(slab)
        thickness = self._slab_thickness(slab)
        if rings is None or thickness is None:
            raise EditRefused("not_editable")
        m = self._placement_si(slab)
        inv = np.linalg.inv(m)

        def local(pts):
            return [tuple(float(c) for c in (inv @ np.array((x, y, m[2, 3], 1.0)))[:2]) for x, y in pts]

        drawing = None
        if loops is not None:
            drawing = outline_loops.rounded(outline_loops.mapped(loops, lambda p: local([p])[0]))
            drawn_rings = outline_loops.rings(drawing)
            if not drawn_rings or outline_loops.polygon(drawing) is None:
                raise EditRefused("slab_outline")
            outline, holes = drawn_rings[0], drawn_rings[1:]
            outside, inner = outline, holes
        else:
            outside = local(outline)
            inner = rings[1] if holes is None else [local(h) for h in holes]
        poly = core_slabs.outline_polygon(outside, inner)
        if poly is None and drawing is None:
            inner = [h for h in inner if core_slabs.outline_polygon(outside).contains(
                core_slabs.outline_polygon(h))] if core_slabs.outline_polygon(outside) is not None else []
            poly = core_slabs.outline_polygon(outside, inner)
        if poly is None:
            raise EditRefused("slab_outline")
        if not self._openings_fit(slab, outside):
            raise EditRefused("opening_outside")
        self._set_slab_shape(slab, thickness, outside, inner, heights=heights)
        params = {"Forma": "poligono",
                  "Desenho": outline_loops.text(drawing) if drawing and outline_loops.curved(drawing) else None}
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
        self._set_slab_shape(slab, self._slab_thickness(slab), radius=float(radius))

    def set_slab_heights(self, guid, heights):
        """(0.433, the addon's «piso com declive por vértice») Each corner of a slab's outline at a height of its own
        over its top (m, its outline's order: a balcony falling to its drain, a ramp) — all 0: flat again, its
        extrusion. Its underside follows a thickness lower; its holes' corners lie on its top. A rectangle becomes a
        polygon (its corners its own now); a round slab has no corners."""
        slab, _ = self._require(guid, "slab")
        if self.slab_shape(guid) == "circulo":
            raise EditRefused("slab_circle")
        rings = self._local_rings(slab)
        thickness = self._slab_thickness(slab)
        if rings is None or thickness is None:
            raise EditRefused("not_editable")
        outside, holes, _radius = rings
        heights = [float(z) for z in heights]
        if len(heights) != len(outside):
            raise EditRefused("not_editable")
        if any(abs(z) > MAX_HEIGHT for z in heights):
            raise EditRefused("slab_height")
        self._set_slab_shape(slab, thickness, outside, holes, heights=heights)
        if self.slab_shape(guid) == "retangulo":
            self._set_params(slab, {"Forma": "poligono"})

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
