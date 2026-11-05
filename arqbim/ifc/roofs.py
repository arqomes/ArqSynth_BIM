"""Roofs (0.111), mixed into IfcModel: an IfcRoof (FLAT_ROOF, SHED_ROOF, GABLE_ROOF, HIP_ROOF; 0.180: BUTTERFLY_ROOF
and BARREL_ROOF, by extrusion — a profile across a rectangle run along it, _set_extruded_roof_body) with its own body —
IFC4 lets a roof that is not made of slabs carry its shape, and one element is selected, moved, copied and
mirrored as one. Its body: one IfcExtrudedAreaSolid per slope — the slope's plan outline laid on its inclined
plane and extruded straight down (world −Z) by the roof's vertical thickness, so that two slopes meet exactly at
their hip or ridge, top and bottom alike. Its type (0.278): an IfcRoofType with its layer set (before 0.278, a
slab type's layer set and no type); Qto_RoofBaseQuantities, Pset_RoofCommon.IsExternal.

ArqSynth_Parametros: Elemento "roof"; Contorno — the walls' outer line, in the roof's own frame (its placement is
at that line's first corner, at the eave's height: the top of the roof over the walls' line); Forma (flat / shed
/ gable / hip), Aguas (which sides slope, "1;0;…"), Inclinacao (degrees), Beirado (the overhang, m), Espessura,
Tipo (its type's key)."""

import math

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from ..core import roof_blocks as core_blocks
from ..core import roofs as core_roofs
from . import catalog
from .edit import EditRefused

api = ifcopenshell.api
PREDEFINED = {"flat": "FLAT_ROOF", "shed": "SHED_ROOF", "gable": "GABLE_ROOF", "hip": "HIP_ROOF",
              "butterfly": "BUTTERFLY_ROOF", "barrel": "BARREL_ROOF",               # (0.180: by extrusion)
              "custom": "FREEFORM",                     # (0.251: its section drawn — "a roof with a free-form shape")
              "blocks": "FREEFORM"}                     # (0.262: by blocks — one block: its own form's, see _block_kind)
BLOCK_KIND = {"hip": "HIP_ROOF", "gable": "GABLE_ROOF", "gable_across": "GABLE_ROOF", "shed": "SHED_ROOF",
              "flat": "FLAT_ROOF"}
# (0.265) a roof by blocks' edges' true lengths, by kind (core/roof_blocks.edges): a quantity set of the program's
EDGE_QTO = "ArqSynth_ArestasCobertura"
EDGE_NAMES = {"eave": "Beirados", "ridge": "Cumeeiras", "hip": "Rincoes", "valley": "Laros", "gable": "Empenas",
              "top": "Remates"}
EDGE_COLUMNS = {"eave": "eaves", "ridge": "ridges", "hip": "hips", "valley": "valleys", "gable": "gables",
                "top": "tops"}                              # (the schedules' columns, model/schedules.EDGES)


def _pts(text):
    return [tuple(float(v) for v in pair.split(",")) for pair in (text or "").split(";") if pair]


def _text(pts):
    return ";".join("{:.6f},{:.6f}".format(x, y) for x, y in pts)


class RoofMixin:
    def roof_params(self, guid):
        """{outline (world plan), local (its own frame), form, sloping, slope, overhang, eave, thickness, spec} of
        a roof made by this program."""
        e = self.by_guid(guid)
        p = self._params(e)
        m = self._placement_si(e)
        local = _pts(p.get("Contorno"))
        world = [tuple((m @ np.array((x, y, 0.0, 1.0)))[:2]) for x, y in local]
        form = p.get("Forma") or "flat"
        return {"outline": world, "local": local, "form": form,
                "sloping": [s == "1" for s in (p.get("Aguas") or "").split(";") if s],
                "slope": float(p.get("Inclinacao") or 0.0), "overhang": float(p.get("Beirado") or 0.0),
                "eave": float(m[2, 3]), "thickness": float(p.get("Espessura") or 0.15),
                "spec": catalog.BY_KEY.get(p.get("Tipo") or ""),
                "section": _pts(p.get("Seccao")),                  # (0.251: a drawn one's, real size)
                # (0.262) a roof by blocks: its blocks, in its own frame (their eaves over its placement's level)
                "blocks": core_blocks.from_text(p.get("Blocos")) if form == "blocks" else []}

    def _roof_faces(self, local, sloping, overhang):
        outline = core_roofs.grown(local, overhang)
        flags = core_roofs.carried_over(local, sloping, outline)
        return outline, flags, core_roofs.faces(outline, flags)

    def _set_roof_body(self, roof):
        """A roof's body and quantities from its parameters (see the module's docstring)."""
        f, u = self.file, 1.0 / self.unit_scale
        p = self.roof_params(roof.GlobalId)
        if p["form"] in core_roofs.EXTRUDED:              # (0.180) its profile run along it
            self._set_extruded_roof_body(roof, p)
            return
        if p["form"] == "blocks":                         # (0.262) its blocks' top, region by region
            self._set_block_roof_body(roof, p)
            return
        slope = p["slope"] if any(p["sloping"]) else 0.0
        outline, flags, faces = self._roof_faces(p["local"], p["sloping"], p["overhang"])
        if faces is None:
            raise EditRefused("roof_not_convex")
        a = math.radians(slope)
        tan, cos, sin = math.tan(a), math.cos(a), math.sin(a)
        depth = p["thickness"] / cos                       # (its thickness square to its slope)
        drop = tan * p["overhang"]                          # (the eave a little lower than over the walls)
        items, sloped_area = [], 0.0
        for plane, polygon in faces:
            if plane is None:                              # flat: its outline, down from its top
                start, e, n, z = (0.0, 0.0), (1.0, 0.0), (0.0, 1.0), 0.0
                local_dir = (0.0, 0.0, -1.0)
            else:
                start, e, n = plane                         # (its eave's point, direction, inward normal)
                z = -drop
                local_dir = (0.0, -sin, -cos)               # (world −Z in the slope's own frame)
            s = np.array((n[0] * cos, n[1] * cos, sin))     # (up the slope)
            ex = np.array((e[0], e[1], 0.0))
            normal = np.cross(ex, s)
            coords = []
            for x, y in polygon:
                dx, dy = x - start[0], y - start[1]
                coords.append((float((dx * e[0] + dy * e[1]) * u), float((dx * n[0] + dy * n[1]) / cos * u)))
            coords.append(coords[0])
            curve = f.createIfcIndexedPolyCurve(f.createIfcCartesianPointList2D(coords), None, False)
            sloped_area += Polygon(polygon).area / cos
            items.append(f.createIfcExtrudedAreaSolid(
                f.createIfcArbitraryClosedProfileDef("AREA", None, curve),
                f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((float(start[0] * u), float(start[1] * u),
                                                                       float(z * u))),
                                            f.createIfcDirection(tuple(float(c) for c in normal)),
                                            f.createIfcDirection((float(e[0]), float(e[1]), 0.0))),
                f.createIfcDirection(local_dir), float(depth * u)))
        self._clear_representations(roof)
        api.geometry.assign_representation(f, product=roof, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))
        projected = Polygon(outline).area
        self._set_qto(roof, "Qto_RoofBaseQuantities", {"GrossArea": sloped_area, "NetArea": sloped_area,
                                                       "ProjectedArea": projected})

    def _set_extruded_roof_body(self, roof, p):
        """(0.180) A butterfly or barrel roof: its profile across the (grown) rectangle — two slopes down to a
        valley in the middle, or an arc springing from the walls at the slope (true arcs: IfcArcIndex) — its
        thickness under it, run along the rectangle's length: one IfcExtrudedAreaSolid."""
        f, u = self.file, 1.0 / self.unit_scale
        outline = core_roofs.grown(p["local"], p["overhang"])
        frame = core_roofs.rect_frame(outline)
        if frame is None:
            raise EditRefused("roof_rect")
        a, e, n, length, span = frame
        walls_span, o, t = span - 2 * p["overhang"], p["overhang"], p["thickness"]
        z = lambda v, th=0.0: core_roofs.profile_z(p["form"], walls_span, o, p["slope"], v, th)    # noqa: E731
        c = span / 2
        if p["form"] == "custom":                         # (0.251) its section as drawn, over the span's middle
            section = p["section"]
            if len(section) < 3:
                raise EditRefused("roof_section")
            width = max(x for x, _y in section)
            pts = [(c - width / 2 + x, y) for x, y in section]
            segments = None
            run = Polygon(section).length / 2              # (about its top's length)
            span = width
        elif p["form"] == "barrel":
            radius, below = core_roofs.arch(walls_span, p["slope"])
            top = [(0.0, z(0.0)), (c, z(c)), (span, z(span))]
            centre = (c, -below)
            inner = [(centre[0] + (x - centre[0]) * (radius - t) / radius,
                      centre[1] + (y - centre[1]) * (radius - t) / radius) for x, y in reversed(top)]
            pts = top + inner
            segments = [f.createIfcArcIndex((1, 2, 3)), f.createIfcLineIndex((3, 4)), f.createIfcArcIndex((4, 5, 6)),
                        f.createIfcLineIndex((6, 1))]
            run = radius * 2 * math.asin(min(span / 2 / radius, 1.0))           # (its arc's length)
        else:
            top = [(0.0, z(0.0)), (c, z(c)), (span, z(span))]
            pts = top + [(x, y + z(x, t) - z(x)) for x, y in reversed(top)]
            segments = None
            run = 2 * math.hypot(c, z(0.0) - z(c))
        coords = [(float(x * u), float(y * u)) for x, y in pts]
        curve = f.createIfcIndexedPolyCurve(f.createIfcCartesianPointList2D(coords + ([] if segments else
                                                                                     [coords[0]])),
                                            segments, False)
        solid = f.createIfcExtrudedAreaSolid(
            f.createIfcArbitraryClosedProfileDef("AREA", None, curve),
            f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((float(a[0] * u), float(a[1] * u), 0.0)),
                                        f.createIfcDirection((float(e[0]), float(e[1]), 0.0)),
                                        f.createIfcDirection((float(n[0]), float(n[1]), 0.0))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(length * u))
        self._clear_representations(roof)
        api.geometry.assign_representation(f, product=roof, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", [solid]))
        self._set_qto(roof, "Qto_RoofBaseQuantities", {"GrossArea": run * length, "NetArea": run * length,
                                                       "ProjectedArea": span * length})

    # ------------------------------------------------------------ roofs by blocks (0.262)

    def _region_solid(self, coeff, polygon, thickness):
        """One region of a block roof's top — a plan polygon (holes too) on the plane z = a·x + b·y + c (its own
        frame) — laid on that plane and extruded straight down by the roof's upright thickness."""
        f, u = self.file, 1.0 / self.unit_scale
        a, b, c = coeff
        normal = np.array((-a, -b, 1.0))
        normal /= np.linalg.norm(normal)
        grad = math.hypot(a, b)
        along = np.array((-b / grad, a / grad, 0.0)) if grad > 1e-12 else np.array((1.0, 0.0, 0.0))
        up = np.cross(normal, along)
        x0, y0 = polygon.exterior.coords[0]
        origin = np.array((x0, y0, a * x0 + b * y0 + c))

        def curve(ring):
            coords = []
            for x, y in list(ring.coords)[:-1]:
                d = np.array((x, y, a * x + b * y + c)) - origin
                coords.append((float(d @ along * u), float(d @ up * u)))
            coords.append(coords[0])
            return f.createIfcIndexedPolyCurve(f.createIfcCartesianPointList2D(coords), None, False)

        if polygon.interiors:
            profile = f.createIfcArbitraryProfileDefWithVoids("AREA", None, curve(polygon.exterior),
                                                              [curve(r) for r in polygon.interiors])
        else:
            profile = f.createIfcArbitraryClosedProfileDef("AREA", None, curve(polygon.exterior))
        down = (0.0, float(-up[2]), float(-normal[2]))                     # (world −Z in its own frame)
        return f.createIfcExtrudedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint(tuple(float(v * u) for v in origin)),
                                                 f.createIfcDirection(tuple(float(v) for v in normal)),
                                                 f.createIfcDirection(tuple(float(v) for v in along))),
            f.createIfcDirection(down), float(thickness / normal[2] * u))

    def _set_block_roof_body(self, roof, p):
        """(0.262) A roof by blocks: its top's regions (core/roof_blocks.regions), each extruded down by its
        thickness — one IfcExtrudedAreaSolid each (its holes as voids); its quantities; its IFC kind (one block:
        its form's; several: FREEFORM); its outline (the blocks' plan) kept for what reads it."""
        blocks = p["blocks"]
        if not blocks:
            raise EditRefused("roof_blocks")
        items, true_area, projected = [], 0.0, 0.0
        found = core_blocks.regions(blocks)
        for coeff, geometry in found:
            for polygon in core_blocks.polygons(geometry):
                polygon = orient(polygon, 1.0)
                items.append(self._region_solid(coeff, polygon, p["thickness"]))
                projected += polygon.area
                true_area += polygon.area * math.sqrt(1.0 + coeff[0] ** 2 + coeff[1] ** 2)
        if not items:
            raise EditRefused("roof_blocks")
        f = self.file
        self._clear_representations(roof)
        api.geometry.assign_representation(f, product=roof, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))
        self._set_qto(roof, "Qto_RoofBaseQuantities", {"GrossArea": true_area, "NetArea": true_area,
                                                       "ProjectedArea": projected})
        lengths = core_blocks.edge_lengths(blocks, found)            # (0.265) its edges' lengths, by kind
        self._set_qto(roof, EDGE_QTO, {EDGE_NAMES[k]: float(v) / self.unit_scale for k, v in lengths.items()})
        roof.PredefinedType = BLOCK_KIND.get(core_blocks.form_of(blocks[0]), "FREEFORM") if len(blocks) == 1 \
            else "FREEFORM"
        plan = core_blocks.footprint(blocks)
        largest = max(core_blocks.polygons(plan), key=lambda g: g.area)
        self._set_params(roof, {"Contorno": _text([tuple(c) for c in orient(largest, 1.0).exterior.coords[:-1]])})

    def _block_to_local(self, roof, block):
        """A block given in the plan (world) put in the roof's own frame (its placement's turn and place)."""
        m = self._placement_si(roof)
        c = np.linalg.inv(m) @ np.array((block.cx, block.cy, m[2, 3], 1.0))
        turn = math.degrees(math.atan2(m[1, 0], m[0, 0]))
        return core_blocks.replace(block, cx=float(c[0]), cy=float(c[1]), angle=block.angle - turn)

    def _block_to_world(self, roof, block):
        """(0.263) A block of the roof's own frame put in the plan (world)."""
        m = self._placement_si(roof)
        c = m @ np.array((block.cx, block.cy, 0.0, 1.0))
        turn = math.degrees(math.atan2(m[1, 0], m[0, 0]))
        return core_blocks.replace(block, cx=float(c[0]), cy=float(c[1]), angle=block.angle + turn)

    def roof_blocks_world(self, guid):
        """(0.263) A roof by blocks' blocks in the plan (their eaves over the roof's level)."""
        roof = self.by_guid(guid)
        return [self._block_to_world(roof, b) for b in self.roof_params(guid)["blocks"]]

    def set_roof_blocks_world(self, guid, blocks):
        """(0.263) A roof by blocks' blocks made these, given in the plan."""
        roof, _ = self._require(guid, "roof")
        self.set_roof_blocks(guid, [self._block_to_local(roof, b) for b in blocks])

    def _set_roof_type(self, roof, spec, lang="pt"):
        """(0.278) A roof's type: a roof type's IfcRoofType (NOTDEFINED: the roof keeps its own form), its layer set
        on the roof too, as before; a slab's type (as roofs were made before) only its layer set."""
        f = self.file
        type_ = self.ensure_type(spec, lang)
        if spec.kind == "roof":
            api.type.assign_type(f, related_objects=[roof], relating_type=type_, should_map_representations=False)
        elif ifcopenshell.util.element.get_type(roof) is not None:
            api.type.unassign_type(f, related_objects=[roof])
        if ifcopenshell.util.element.get_material(roof, should_inherit=False) is not None:
            api.material.unassign_material(f, products=[roof])
        layers = ifcopenshell.util.element.get_material(type_)
        if layers is not None:
            api.material.assign_material(f, products=[roof], type="IfcMaterialLayerSet", material=layers)

    def set_roof_type(self, guid, spec, lang="pt"):
        """(0.278) A roof's type changed: its layers and thickness, its body (its height: bim.set_type)."""
        roof, _ = self._require(guid, "roof")
        if spec.kind not in ("roof", "slab") or not spec.layers:
            raise EditRefused("not_editable")
        self._set_roof_type(roof, spec, lang)
        self._set_params(roof, {"Espessura": spec.thickness, "Tipo": spec.key})
        self._set_roof_body(roof)

    def add_block_roof(self, spec, block, eave, name, lang="pt", storey=None):
        """(0.262) A roof by blocks, its first block `block` (plan; its eaves over the level `eave` — the roof's):
        its placement at the block's middle at that level. Returns the IfcRoof."""
        trouble = core_blocks.problem(block)
        if trouble:
            raise EditRefused(trouble)
        f = self.file
        roof = api.root.create_entity(f, ifc_class="IfcRoof", name=name, predefined_type="FREEFORM")
        m = np.eye(4)
        m[:3, 3] = (block.cx, block.cy, float(eave))
        self._place(roof, m)
        container = self.storey(storey) if storey is not None else self.storey_at(float(eave))
        api.spatial.assign_container(f, products=[roof], relating_structure=container)
        self._set_roof_type(roof, spec, lang)
        common = api.pset.add_pset(f, product=roof, name="Pset_RoofCommon")
        api.pset.edit_pset(f, pset=common, properties={"IsExternal": True})
        self._mark(roof, "roof")
        local = self._block_to_local(roof, block)
        self._set_params(roof, {"Forma": "blocks", "Blocos": core_blocks.to_text([local]), "Aguas": "",
                                "Inclinacao": float(max(block.slope)), "Beirado": float(block.overhang),
                                "Espessura": spec.thickness, "Tipo": spec.key})
        self._set_roof_body(roof)
        return roof

    def set_roof_blocks(self, guid, blocks):
        """(0.262) A roof by blocks' blocks (in its own frame) made these: refused when one is unusable or none
        is left."""
        roof, _ = self._require(guid, "roof")
        if self.roof_params(guid)["form"] != "blocks":
            raise EditRefused("not_editable")
        if not blocks:
            raise EditRefused("roof_blocks")
        for b in blocks:
            trouble = core_blocks.problem(b)
            if trouble:
                raise EditRefused(trouble)
        self._set_params(roof, {"Blocos": core_blocks.to_text(blocks)})
        self._set_roof_body(roof)

    def add_roof_block(self, guid, block):
        """(0.262) One more block (plan, world; its eaves over the roof's level) in a roof by blocks."""
        roof, _ = self._require(guid, "roof")
        blocks = self.roof_params(guid)["blocks"]
        self.set_roof_blocks(guid, blocks + [self._block_to_local(roof, block)])

    def add_roof(self, spec, outline, form, slope, overhang, eave, name, lang="pt", storey=None, sloping=None):
        """A roof over `outline` (the walls' outer line, plan, any order), its top there at `eave`: its form,
        slope (degrees), overhang (m) and its type `spec` (its layers and thickness). Returns the IfcRoof."""
        ring = orient(Polygon(outline), 1.0)
        pts = [tuple(c) for c in list(ring.exterior.coords)[:-1]]
        if not core_roofs.can_slope(ring, form):
            raise EditRefused("roof_rect" if form in core_roofs.EXTRUDED else "roof_not_convex")
        sloping = core_roofs.sloping_sides(pts, form) if sloping is None else list(sloping)
        f = self.file
        roof = api.root.create_entity(f, ifc_class="IfcRoof", name=name, predefined_type=PREDEFINED[form])
        m = np.eye(4)
        m[:3, 3] = (pts[0][0], pts[0][1], float(eave))
        self._place(roof, m)
        container = self.storey(storey) if storey is not None else self.storey_at(float(eave))
        api.spatial.assign_container(f, products=[roof], relating_structure=container)
        self._set_roof_type(roof, spec, lang)
        common = api.pset.add_pset(f, product=roof, name="Pset_RoofCommon")
        api.pset.edit_pset(f, pset=common, properties={"IsExternal": True})
        self._mark(roof, "roof")
        local = [(x - pts[0][0], y - pts[0][1]) for x, y in pts]
        self._set_params(roof, {"Contorno": _text(local), "Forma": form,
                                "Aguas": ";".join("1" if s else "0" for s in sloping),
                                "Inclinacao": float(slope), "Beirado": float(overhang),
                                "Espessura": spec.thickness, "Tipo": spec.key})
        self._set_roof_body(roof)
        return roof

    def set_roof(self, guid, form=None, slope=None, overhang=None, eave=None):
        """A roof's form (its sloping sides chosen again), slope, overhang or eave height changed."""
        roof, _ = self._require(guid, "roof")
        p = self.roof_params(guid)
        changes = {}
        if p["form"] == "blocks":                            # (0.262) all its blocks' waters / overhangs
            if form is not None and form != "blocks":
                raise EditRefused("roof_blocks_form")
            if slope is not None and not 0.0 <= float(slope) < 80.0:
                raise EditRefused("roof_slope")
            if overhang is not None and float(overhang) < 0.0:
                raise EditRefused("too_small")
            blocks = core_blocks.with_all(p["blocks"], slope, overhang)
            self._set_params(roof, {"Blocos": core_blocks.to_text(blocks),
                                    "Inclinacao": float(slope if slope is not None else p["slope"]),
                                    "Beirado": float(overhang if overhang is not None else p["overhang"])})
            if eave is not None:
                m = self._placement_si(roof)
                m[2, 3] = float(eave)
                self._place(roof, m)
            self._set_roof_body(roof)
            return
        if form is not None and form != p["form"]:
            if form == "custom" and not p["section"]:
                raise EditRefused("roof_section")              # (0.251: drawn first: set_roof_section)
            if not core_roofs.can_slope(Polygon(p["local"]), form):
                raise EditRefused("roof_rect" if form in core_roofs.EXTRUDED else "roof_not_convex")
            changes["Forma"] = form
            changes["Aguas"] = ";".join("1" if s else "0" for s in core_roofs.sloping_sides(p["local"], form))
            roof.PredefinedType = PREDEFINED[form]
        if slope is not None:
            if not 0.0 <= float(slope) < 80.0:
                raise EditRefused("roof_slope")
            changes["Inclinacao"] = float(slope)
        if overhang is not None:
            if float(overhang) < 0.0:
                raise EditRefused("too_small")
            changes["Beirado"] = float(overhang)
        if changes:
            self._set_params(roof, changes)
        if eave is not None:
            m = self._placement_si(roof)
            m[2, 3] = float(eave)
            self._place(roof, m)
        self._set_roof_body(roof)

    def set_roof_section(self, guid, points):
        """(0.251) A roof made one by extrusion of a section drawn (points [(a across, b up)…] m, real size): over
        its rectangle's middle, its lowest point at the eave's height, run along its length (an IfcRoof FREEFORM).
        Refused when its outline is not a rectangle or the section is no roof's (core.roofs.custom_section)."""
        roof, _ = self._require(guid, "roof")
        p = self.roof_params(guid)
        if not core_roofs.can_slope(Polygon(p["local"]), "custom"):
            raise EditRefused("roof_rect")
        try:
            section = core_roofs.custom_section(points)
        except ValueError as exc:
            raise EditRefused(str(exc)) from None
        self._set_params(roof, {"Forma": "custom", "Seccao": _text(section),
                                "Aguas": ";".join("0" for _s in p["local"])})
        roof.PredefinedType = PREDEFINED["custom"]
        self._set_roof_body(roof)

    def add_drain(self, roof, point, name, storey=None):
        """A roof drain (0.113): IfcWasteTerminal ROOFDRAIN, a 10 cm round grate on the roof's top at `point`
        (plan), in the roof's storey. Returns it."""
        f, u = self.file, 1.0 / self.unit_scale
        z = self.roof_height_at(roof, point)
        drain = api.root.create_entity(f, ifc_class="IfcWasteTerminal", name=name, predefined_type="ROOFDRAIN")
        m = np.eye(4)
        m[:3, 3] = (float(point[0]), float(point[1]), float(z))
        self._place(drain, m)
        solid = f.createIfcExtrudedAreaSolid(
            f.createIfcCircleProfileDef("AREA", None, f.createIfcAxis2Placement2D(
                f.createIfcCartesianPoint((0.0, 0.0)), None), float(0.05 * u)),
            f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, float(-0.06 * u))), None, None),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(0.08 * u))
        api.geometry.assign_representation(f, product=drain, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", [solid]))
        container = self.storey(storey) if storey is not None else (
            ifcopenshell.util.element.get_container(self.by_guid(roof)) or self.storey_at(float(z)))
        api.spatial.assign_container(f, products=[drain], relating_structure=container)
        self._mark(drain, "drain")
        self._set_params(drain, {"Cobertura": roof})
        return drain

    def add_vertical_opening(self, host, a, b, name):
        """A rectangular opening straight through a roof or a slab (0.113, a skylight's hole): the plan rectangle
        between corners a and b, from under its lowest to over its highest point. Returns it."""
        verts, _faces = self.triangulate([host])[host]
        zs = np.asarray(verts, dtype=float).reshape(-1, 3)[:, 2]
        lo = (min(a[0], b[0]), min(a[1], b[1]), float(zs.min()) - 0.05)
        hi = (max(a[0], b[0]), max(a[1], b[1]), float(zs.max()) + 0.05)
        if hi[0] - lo[0] < 0.05 or hi[1] - lo[1] < 0.05:
            raise EditRefused("too_small")
        return self.add_void(host, np.eye(4), lo, hi, name)

    def roof_underside_at(self, guid, point):
        """The roof's underside over a plan point (its top less its vertical thickness)."""
        p = self.roof_params(guid)
        if p["form"] in core_roofs.EXTRUDED:              # (0.180) under its arc / its two slopes
            return self._extruded_height(guid, p, point, p["thickness"])
        if p["form"] == "blocks":                         # (0.262) under the highest of its blocks there
            x, y, base = self._block_local(guid, point)
            z = core_blocks.underside_at(p["blocks"], x, y, p["thickness"])
            return base if z is None else base + z
        slope = p["slope"] if any(p["sloping"]) else 0.0
        return self.roof_height_at(guid, point) - p["thickness"] / math.cos(math.radians(slope))

    def _block_local(self, guid, point):
        """(0.262) A plan point in a roof's own frame: (x, y, the level of its placement)."""
        m = self._placement_si(self.by_guid(guid))
        local = np.linalg.inv(m) @ np.array((float(point[0]), float(point[1]), m[2, 3], 1.0))
        return float(local[0]), float(local[1]), float(m[2, 3])

    def _extruded_height(self, guid, p, point, thickness=0.0):
        m = self._placement_si(self.by_guid(guid))
        local = np.linalg.inv(m) @ np.array((float(point[0]), float(point[1]), m[2, 3], 1.0))
        ring = [tuple(c) for c in list(orient(Polygon(p["local"]), 1.0).exterior.coords)[:-1]]
        return core_roofs.extruded_height_at(ring, p["form"], p["overhang"], p["slope"], p["eave"], local[:2],
                                             thickness, section=p["section"])

    def _roof_breaks(self, guid, start, end):
        """Where along the line start -> end (plan) the roof's underside changes slope: [0..1] — where the line
        crosses a slope's outline (a hip, the ridge, an eave)."""
        p = self.roof_params(guid)
        m = self._placement_si(self.by_guid(guid))
        a, b = np.asarray(start, dtype=float)[:2], np.asarray(end, dtype=float)[:2]
        d = b - a
        out = {0.0, 1.0}
        if p["form"] == "blocks":                         # (0.262) where it crosses its regions' edges
            la, lb = self._block_local(guid, a)[:2], self._block_local(guid, b)[:2]
            return core_blocks.breaks(p["blocks"], la, lb)
        if p["form"] in core_roofs.EXTRUDED:              # (0.180) an arc: every 1/24; two slopes: the valley
            return sorted(out | ({k / 24 for k in range(1, 24)} if p["form"] in ("barrel", "custom") else
                                 set(self._valley_crossing(guid, p, a, b))))
        _outline, _flags, faces = self._roof_faces(p["local"], p["sloping"], p["overhang"])
        for _k, polygon in faces or ():
            world = [(m @ np.array((x, y, 0.0, 1.0)))[:2] for x, y in polygon]
            for q, r in zip(world, world[1:] + world[:1]):
                e = r - q
                den = d[0] * e[1] - d[1] * e[0]
                if abs(den) < 1e-12:
                    continue
                w = q - a
                s = (w[0] * e[1] - w[1] * e[0]) / den          # (along start -> end)
                u = (w[0] * d[1] - w[1] * d[0]) / den          # (along the slope's side)
                if 1e-9 < s < 1 - 1e-9 and -1e-9 <= u <= 1 + 1e-9:
                    out.add(float(s))
        return sorted(out)

    def _valley_crossing(self, guid, p, a, b):
        """(0.180) Where along a → b (plan) a butterfly roof's valley line is crossed: [s] (0..1), or none."""
        frame = core_roofs.rect_frame(core_roofs.grown(p["local"], p["overhang"]))
        if frame is None:
            return []
        m = np.linalg.inv(self._placement_si(self.by_guid(guid)))
        la, lb = (m @ np.array((a[0], a[1], 0.0, 1.0)))[:2], (m @ np.array((b[0], b[1], 0.0, 1.0)))[:2]
        corner, _e, n, _length, span = frame
        va = (la[0] - corner[0]) * n[0] + (la[1] - corner[1]) * n[1]
        vb = (lb[0] - corner[0]) * n[0] + (lb[1] - corner[1]) * n[1]
        if abs(vb - va) < 1e-12:
            return []
        s = (span / 2 - va) / (vb - va)
        return [float(s)] if 1e-9 < s < 1 - 1e-9 else []

    def attach_to_roof(self, guid, roof):
        """A wall's top made the roof's underside over it (its profile: gables come out under two slopes), or a
        column's top brought to it (0.112) — and tied, to follow the roof. A door / window must still fit."""
        self._require(roof, "roof")
        e, kind = self._require(guid, "wall", "column")
        if kind == "column":
            centre, _x, _ab, base, _top = self.column_box(guid)
            height = self.roof_underside_at(roof, centre) - base
            if height < 0.10:
                raise EditRefused("too_small")
            self.resize_column(guid, height)
        else:
            s, end, _t = self.wall_axis(guid)
            length, _h, _th = self.wall_params(guid)
            base = float(s[2])
            tops = [(t_ * length, self.roof_underside_at(roof, s + (end - s) * t_) - base)
                    for t_ in self._roof_breaks(roof, s, end)]
            if min(z for _x, z in tops) < 0.10:
                raise EditRefused("too_small")
            if all(abs(z - tops[0][1]) < 1e-6 for _x, z in tops):          # (level under it: a plain wall)
                if self.wall_profile(e) is not None:
                    self.set_wall_profile(guid, None)
                self.resize_wall(guid, height=tops[0][1])
            else:
                self.set_wall_profile(guid, [(0.0, 0.0), (length, 0.0)] + [(x, z) for x, z in reversed(tops)])
        self._set_params(e, {"TopoCobertura": roof, "TopoPavimento": None, "TopoLaje": None, "TopoDesvio": None})

    def roof_tops(self, roofs):
        """The walls and columns whose top is tied to any of these roofs (0.112)."""
        wanted, out = set(roofs), []
        if not wanted:                                  # (no roof changed: none read — every edit asks)
            return out
        for cls in ("IfcWall", "IfcColumn"):
            for e in self.file.by_type(cls):
                if self._params(e).get("TopoCobertura") in wanted:
                    out.append(e.GlobalId)
        return out

    def follow_roof_tops(self, changed):
        """After roofs changed: the walls and columns tied to them made to meet their underside again (0.112);
        a wall or column moved under a roof that stays meets it there too. Returns those that changed."""
        roofs = {g for g in changed if self.kind_of(g) == "roof"}
        tied = set(self.roof_tops(roofs))
        for g in changed:                               # (moved themselves)
            if self.kind_of(g) in ("wall", "column") and self._params(self.by_guid(g)).get("TopoCobertura"):
                tied.add(g)
        out = []
        for g in sorted(tied):
            roof = self._params(self.by_guid(g)).get("TopoCobertura")
            if self.by_guid(roof) is None:
                continue
            try:
                self.attach_to_roof(g, roof)
            except EditRefused:
                continue
            out.append(g)
        return out

    def roof_height_at(self, guid, point):
        """The roof's top over a plan point (its plane over there), from its parameters (0.111)."""
        p = self.roof_params(guid)
        if p["form"] in core_roofs.EXTRUDED:              # (0.180) on its arc / its two slopes
            return self._extruded_height(guid, p, point)
        if p["form"] == "blocks":                         # (0.262) the highest of its blocks there
            x, y, base = self._block_local(guid, point)
            z = core_blocks.height_at(p["blocks"], x, y)
            return base if z is None else base + z
        m = self._placement_si(self.by_guid(guid))
        local = np.linalg.inv(m) @ np.array((float(point[0]), float(point[1]), m[2, 3], 1.0))
        outline, flags, _faces = self._roof_faces(p["local"], p["sloping"], p["overhang"])
        drop = math.tan(math.radians(p["slope"])) * p["overhang"] if any(flags) else 0.0
        return core_roofs.height_at(outline, flags, p["slope"], p["eave"] - drop, local[:2])
