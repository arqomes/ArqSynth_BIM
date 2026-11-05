"""Organic roofs (0.390), mixed into IfcModel: an IfcRoof (FREEFORM) over an outline drawn in plan, its form found from
the outline (core/organic_roof.py) — a shell, a gridshell, a glazed gridshell or a curved pergola —, with a ring beam
under its edge and supports if asked. One element, its pieces items of its body each in its material (IfcStyledItem,
as the railings'): the shell concrete, the bars black steel (the pergola's ribs timber), the glass, the ring beam and
the supports as the bars. Placed at the outline's middle, at the level of its edge (the eave); the outline kept in
its own coordinates, so that moving or turning it carries the outline along.

ArqSynth_Parametros: Elemento "organic_roof", Contorno (JSON [[x, y]…], m, its own), Flecha (the rise), Forma,
Sistema, Angulo (degrees, the grid's way), Espacamento, Espessura (the shell's), Diametro (the bars'), Material,
Aro (1/0), AroLargura, AroAltura, Apoios, ApoiosEspacamento, ApoiosDiametro."""

import json

import numpy as np

import ifcopenshell.api
import ifcopenshell.api.material
import ifcopenshell.api.root
import ifcopenshell.util.element

from ..core import organic_roof as core_or
from .edit import EditRefused

api = ifcopenshell.api
DEFAULTS = {"rise": 2.5, "form": "cupula", "system": "gridshell", "angle": 0.0, "spacing": 1.2, "thickness": 0.12,
            "diameter": 0.08, "material": "", "ring": True, "ring_width": 0.25, "ring_height": 0.30,
            "supports": "espacados", "support_spacing": 4.0, "support_diameter": 0.20}
NAMES = {"rise": "Flecha", "form": "Forma", "system": "Sistema", "angle": "Angulo", "spacing": "Espacamento",
         "thickness": "Espessura", "diameter": "Diametro", "material": "Material", "ring": "Aro",
         "ring_width": "AroLargura", "ring_height": "AroAltura", "supports": "Apoios",
         "support_spacing": "ApoiosEspacamento", "support_diameter": "ApoiosDiametro"}
TEXTS = {"form", "system", "material", "supports"}
MATERIALS = ("aco_preto", "aco", "inox", "madeira", "concreto", "aluminio")
OWN_MATERIAL = {"casca": "concreto", "gridshell": "aco_preto", "envidracada": "aco_preto", "pergola": "madeira"}
GLASS = 0.012                       # m: a glass pane's thickness


def system_material(p):
    """The structure's material key: the one chosen, or the system's own."""
    return p["material"] if p.get("material") in MATERIALS else OWN_MATERIAL.get(p["system"], "aco_preto")


class OrganicRoofMixin:
    def organic_params(self, guid):
        """{outline (own coordinates), rise, form, system, angle, spacing, thickness, diameter, material, ring,
        ring_width, ring_height, supports, support_spacing, support_diameter}."""
        p = self._params(self.by_guid(guid))
        out = dict(DEFAULTS)
        for key, name in NAMES.items():
            value = p.get(name)
            if value is None:
                continue
            if key in TEXTS:
                out[key] = str(value)
            elif key == "ring":
                out[key] = bool(int(value)) if not isinstance(value, bool) else value
            else:
                out[key] = float(value)
        try:
            out["outline"] = [tuple(map(float, q)) for q in json.loads(p.get("Contorno") or "[]")]
        except (TypeError, ValueError):
            out["outline"] = []
        return out

    def add_organic_roof(self, outline, base, name, storey=None, lang="pt", **params):
        """An organic roof over `outline` [(x, y)] (world plan), its edge at the level `base` (m). Returns it."""
        pts = np.asarray(outline, dtype=float).reshape(-1, 2)
        if len(pts) < 3:
            raise EditRefused("organic_outline")
        from shapely.geometry import Polygon
        centre = np.asarray(Polygon(pts).centroid.coords[0]) if Polygon(pts).is_valid else pts.mean(axis=0)
        f = self.file
        roof = api.root.create_entity(f, ifc_class="IfcRoof", name=name, predefined_type="FREEFORM")
        self._contain(roof, storey, base)
        m = np.eye(4)
        m[:3, 3] = (centre[0], centre[1], base)
        self._place(roof, m)
        self._mark(roof, "organic_roof")
        own = [[round(float(x - centre[0]), 6), round(float(y - centre[1]), 6)] for x, y in pts]
        self._set_params(roof, {"Contorno": json.dumps(own)})
        self._set_params(roof, self._organic_changes(dict(DEFAULTS, **params)))
        self._organic_body(roof, lang)
        return roof

    def set_organic_roof(self, guid, lang="pt", base=None, **changes):
        """Its measures changed (any of DEFAULTS'; `base`: its edge's level) — its body made again."""
        roof, _ = self._require(guid, "organic_roof")
        if base is not None:
            m = self._placement_si(roof)
            m[:3, 3][2] = float(base)
            self._place(roof, m)
        if changes:
            self._set_params(roof, self._organic_changes(changes))
        self._organic_body(roof, lang)

    @staticmethod
    def _organic_changes(changes):
        out = {}
        for key, value in changes.items():
            if key not in NAMES or value is None:
                continue
            if key == "form" and value not in core_or.FORMS or key == "system" and value not in core_or.SYSTEMS \
                    or key == "supports" and value not in core_or.SUPPORTS \
                    or key == "material" and value not in MATERIALS + ("",):
                raise EditRefused("not_editable")
            if key in TEXTS:
                out[NAMES[key]] = str(value)
            elif key == "ring":
                out[NAMES[key]] = 1 if value else 0
            elif key == "angle":
                out[NAMES[key]] = float(value)
            else:
                v = float(value)
                least = {"rise": 0.1, "spacing": 0.3, "thickness": 0.02, "diameter": 0.01, "ring_width": 0.05,
                         "ring_height": 0.05, "support_spacing": 1.0, "support_diameter": 0.05}.get(key, 0.0)
                if v < least:
                    raise EditRefused("organic_small")
                out[NAMES[key]] = v
        return out

    def organic_shape(self, guid):
        """(core Shape, params) of an organic roof (its own coordinates; z 0 at its edge)."""
        p = self.organic_params(guid)
        try:
            return core_or.Shape(p["outline"], p["rise"], p["form"], p["angle"]), p
        except ValueError as exc:
            raise EditRefused(str(exc)) from None

    def _organic_body(self, roof, lang="pt"):
        f, u = self.file, 1.0 / self.unit_scale
        shape, p = self.organic_shape(roof.GlobalId)
        styles = {}

        def style(key):
            if key not in styles:
                styles[key] = self._material_style(self._material(key, lang))
            return styles[key]

        items = []
        structure = system_material(p)
        report = {"area": 0.0, "bars": 0, "bars_length": 0.0, "glass": 0.0, "support_count": 0}
        try:
            surface_v, surface_t, _edge = shape.surface(p["spacing"])
            report["area"] = core_or.area(surface_v, surface_t)
            if p["system"] == "casca":                    # (a faceted solid: one shape may not mix meshes and solids)
                v, tr = shape.shell(p["spacing"], p["thickness"])
                item = self._brep(v, tr)
                f.createIfcStyledItem(item, [style(structure)], None)
                items.append(item)
            else:
                for line in shape.bars(p["spacing"], both=p["system"] != "pergola", bent=p["system"] == "pergola"):
                    item = f.createIfcSweptDiskSolid(f.createIfcPolyline(
                        [f.createIfcCartesianPoint(tuple(float(c * u) for c in q)) for q in line]),
                        float(p["diameter"] / 2.0 * u), None, None, None)
                    f.createIfcStyledItem(item, [style(structure)], None)
                    items.append(item)
                    report["bars"] += 1
                    report["bars_length"] += float(np.linalg.norm(np.diff(line, axis=0), axis=1).sum())
                if p["system"] == "envidracada":         # (each pane a flat triangle, a thin extruded plate)
                    v, tr = shape.panes(p["spacing"])
                    report["glass"] = core_or.area(v, tr) if len(tr) else 0.0
                    glass = style("vidro")
                    for a, b, c in v[tr] if len(tr) else ():
                        item = self._pane_solid(a, b, c, GLASS)
                        if item is not None:
                            f.createIfcStyledItem(item, [glass], None)
                            items.append(item)
        except ValueError as exc:
            raise EditRefused(str(exc)) from None
        ring_h = p["ring_height"] if p["ring"] else 0.0
        if p["ring"]:
            outer, inner = shape.ring(p["ring_width"])
            item = self._profile_solid(outer, ring_h, holes=[inner] if inner else (), at=(0.0, 0.0, -ring_h))
            f.createIfcStyledItem(item, [style("concreto" if p["system"] == "casca" else structure)], None)
            items.append(item)
        storey = self.storey_of(roof.GlobalId)
        floor = next((z for g, _n, z in self.storeys() if g == storey), None)
        base = float(self._placement_si(roof)[2, 3])
        height = base - ring_h - (floor if floor is not None else base)
        if p["supports"] != "nenhum" and height > 0.1:
            at = shape.supports(p["supports"], p["support_spacing"], p["ring_width"] / 2.0 if p["ring"] else
                                p["support_diameter"])
            for x, y in at:
                profile = f.createIfcCircleProfileDef("AREA", None, f.createIfcAxis2Placement2D(
                    f.createIfcCartesianPoint((0.0, 0.0)), None), float(p["support_diameter"] / 2.0 * u))
                item = f.createIfcExtrudedAreaSolid(profile, f.createIfcAxis2Placement3D(
                    f.createIfcCartesianPoint((float(x * u), float(y * u), float(-(ring_h + height) * u))), None, None),
                    f.createIfcDirection((0.0, 0.0, 1.0)), float(height * u))
                f.createIfcStyledItem(item, [style("concreto" if p["system"] == "casca" else structure)], None)
                items.append(item)
            report["support_count"] = len(at)
        if not items:
            raise EditRefused("organic_outline")
        self._clear_representations(roof)
        classes = {i.is_a() for i in items}
        kind = "SweptSolid" if classes == {"IfcExtrudedAreaSolid"} else "Brep" if classes == {"IfcFacetedBrep"} \
            else "AdvancedSweptSolid" if classes <= {"IfcExtrudedAreaSolid", "IfcSweptDiskSolid"} else "SolidModel"
        self._body(roof, items, kind)
        wanted = self._material(structure, lang)                # (the system changed: its structure's material too)
        if ifcopenshell.util.element.get_material(roof) != wanted:
            if ifcopenshell.util.element.get_material(roof) is not None:
                api.material.unassign_material(f, products=[roof])
            api.material.assign_material(f, products=[roof], type="IfcMaterial", material=wanted)
        self._set_qto(roof, "Qto_RoofBaseQuantities", {"GrossArea": report["area"] * u * u})
        self._organic_report = report
        return report

    def _brep(self, verts, tris):
        """A closed faceted solid of these triangles (IfcFacetedBrep: a solid, as the other pieces)."""
        f, u = self.file, 1.0 / self.unit_scale
        points = [f.createIfcCartesianPoint(tuple(float(c * u) for c in row)) for row in verts]
        faces = [f.createIfcFace([f.createIfcFaceOuterBound(f.createIfcPolyLoop([points[i] for i in row]), True)])
                 for row in tris]
        return f.createIfcFacetedBrep(f.createIfcClosedShell(faces))

    def _pane_solid(self, a, b, c, thickness):
        """A flat triangle a b c (m) as a plate `thickness` thick, up from it (IfcExtrudedAreaSolid)."""
        f, u = self.file, 1.0 / self.unit_scale
        x = b - a
        n = np.cross(b - a, c - a)
        if np.linalg.norm(n) < 1e-9 or np.linalg.norm(x) < 1e-9:
            return None
        n = n / np.linalg.norm(n)
        if n[2] < 0:
            n = -n
        x = x / np.linalg.norm(x)
        y = np.cross(n, x)
        local = [(0.0, 0.0), (float(np.dot(b - a, x)), float(np.dot(b - a, y))),
                 (float(np.dot(c - a, x)), float(np.dot(c - a, y)))]
        if (local[1][0] * local[2][1] - local[1][1] * local[2][0]) < 0:
            local = [local[0], local[2], local[1]]
        profile = f.createIfcArbitraryClosedProfileDef("AREA", None, self._ring_curve(local))
        return f.createIfcExtrudedAreaSolid(profile, f.createIfcAxis2Placement3D(
            f.createIfcCartesianPoint(tuple(float(q * u) for q in a)), f.createIfcDirection(tuple(map(float, n))),
            f.createIfcDirection(tuple(map(float, x)))), f.createIfcDirection((0.0, 0.0, 1.0)), float(thickness * u))

    def organic_summary(self, guid):
        """{area, bars, bars_length, glass, support_count} of an organic roof (worked out again)."""
        shape, p = self.organic_shape(guid)
        out = {"area": 0.0, "bars": 0, "bars_length": 0.0, "glass": 0.0, "support_count": 0}
        v, tr, _e = shape.surface(p["spacing"])
        out["area"] = core_or.area(v, tr)
        if p["system"] != "casca":
            lines = shape.bars(p["spacing"], both=p["system"] != "pergola", bent=p["system"] == "pergola")
            out["bars"] = len(lines)
            out["bars_length"] = float(sum(np.linalg.norm(np.diff(q, axis=0), axis=1).sum() for q in lines))
            if p["system"] == "envidracada":
                pv, pt = shape.panes(p["spacing"])
                out["glass"] = core_or.area(pv, pt)
        if p["supports"] != "nenhum":                      # (as its body places them)
            out["support_count"] = len(shape.supports(p["supports"], p["support_spacing"], p["ring_width"] / 2.0
                                                      if p["ring"] else p["support_diameter"]))
        return out


