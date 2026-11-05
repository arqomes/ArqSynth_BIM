"""Parametric surfaces (0.395, the addon's «Superfícies Paramétricas»), mixed into IfcModel: one element whose
definition (core/param_surface.py — curves, op, modifiers, construction) is kept whole in its parameters, its body
made again from it at every change: the construction's pieces as triangle sets, one for each material, each styled
(the bars black steel, the glass, the timber slats…); without construction, the bare surface.

Not only a roof: what it is used for («Uso») sets its class — «estrutura» an IfcBuildingElementProxy (a curved
structure, a pavilion, a canopy), «cobertura» an IfcRoof (FREEFORM), «fachada» an IfcCurtainWall, «pala» an
IfcShadingDevice. Placed where its first curve was drawn, on its storey's floor: its curves kept in its own
coordinates, so that moving or turning it carries them along.

ArqSynth_Parametros: Elemento "param_surface", Definicao (the definition, JSON), Uso, Resumo (JSON: area, the
parts by family, the warnings — what the Properties show without working it out again)."""

import json

import numpy as np

import ifcopenshell.api
import ifcopenshell.api.material
import ifcopenshell.api.root
import ifcopenshell.util.element

from ..core import param_surface as ps
from ..core import surface_build as sb
from .edit import EditRefused

api = ifcopenshell.api
USAGES = {"estrutura": ("IfcBuildingElementProxy", "NOTDEFINED"), "cobertura": ("IfcRoof", "FREEFORM"),
          "fachada": ("IfcCurtainWall", "NOTDEFINED"), "pala": ("IfcShadingDevice", "AWNING")}
KIND = "param_surface"
BARE = "concreto"                   # the bare surface's material (no construction)


def _mask_loader(path):
    from ..model import image_masks
    dark = image_masks.load(path)
    return None if dark is None else 1.0 - np.asarray(dark, dtype=float)


def work_out(data):
    """(Surface, pieces {material: (verts, tris)}, parts, warnings) of a definition — SurfaceError if it cannot."""
    surface = ps.Surface(data)
    if data.get("build"):
        pieces, parts, warnings = sb.build(surface, mask_loader=_mask_loader)
    else:
        verts, tris = surface.triangles()
        pieces, parts, warnings = {BARE: (verts, tris)}, [], []
    return surface, pieces, parts, warnings


class ParamSurfaceMixin:
    def surface_definition(self, guid):
        """The definition (dict) of a parametric surface."""
        e = self.by_guid(guid)
        try:
            data = json.loads(self._params(e).get("Definicao") or "{}")
        except (TypeError, ValueError):
            data = {}
        return data

    def surface_usage(self, guid):
        return self._params(self.by_guid(guid)).get("Uso") or "estrutura"

    def surface_summary(self, guid):
        """{area, parts (count), families {kind: quantities}, warnings} as last made (worked out again if missing)."""
        e = self.by_guid(guid)
        try:
            out = json.loads(self._params(e).get("Resumo") or "")
            if isinstance(out, dict):
                return out
        except (TypeError, ValueError):
            pass
        try:
            surface, _pieces, parts, warnings = work_out(self.surface_definition(guid))
        except ps.SurfaceError as exc:
            return {"area": 0.0, "parts": 0, "families": {}, "warnings": [str(exc)]}
        return self._summary(surface, parts, warnings)

    @staticmethod
    def _summary(surface, parts, warnings):
        return {"area": round(surface.area(), 3), "parts": int(sum(int(p.get("count", 1)) for p in parts)),
                "families": sb.quantities(parts), "warnings": list(warnings)[:6]}

    def surface_parts(self, guid):
        """The register of a surface's parts (the cut list), worked out from its definition."""
        try:
            _s, _p, parts, _w = work_out(self.surface_definition(guid))
        except ps.SurfaceError as exc:
            raise EditRefused(str(exc)) from None
        return parts

    def add_param_surface(self, data, origin, name, storey=None, usage="estrutura", lang="pt"):
        """A parametric surface of `data` (its curves in coordinates from `origin`, a world point on the storey's
        floor). Returns it."""
        cls, predefined = USAGES.get(usage, USAGES["estrutura"])
        f = self.file
        element = api.root.create_entity(f, ifc_class=cls, name=name, predefined_type=predefined)
        self._contain(element, storey, float(origin[2]))
        m = np.eye(4)
        m[:3, 3] = [float(c) for c in origin]
        self._place(element, m)
        self._mark(element, KIND)
        self._set_params(element, {"Uso": usage if usage in USAGES else "estrutura"})
        self._surface_store(element, data, lang)
        return element

    def set_param_surface(self, guid, data=None, lang="pt", usage=None):
        """Its definition changed (or only made again: data None) and/or what it is used for (its class): its body
        made again. Returns its GlobalId (the same)."""
        element, _ = self._require(guid, KIND)
        if usage is not None and usage in USAGES and usage != self.surface_usage(guid):
            cls, predefined = USAGES[usage]
            if not element.is_a(cls):
                if hasattr(self, "element_type_of") and self.element_type_of(guid) is not None:
                    self.tie_element_type(guid, None)    # (0.414: its type's class no longer its — IFC4 wants them alike)
                element = api.root.reassign_class(self.file, product=element, ifc_class=cls,
                                                  predefined_type=predefined)
            self._set_params(element, {"Uso": usage})
        self._surface_store(element, self.surface_definition(guid) if data is None else data, lang)
        return element.GlobalId

    def _surface_store(self, element, data, lang):
        try:
            surface, pieces, parts, warnings = work_out(data)
        except ps.SurfaceError as exc:
            raise EditRefused(str(exc)) from None
        f, u = self.file, 1.0 / self.unit_scale
        items, main = [], None
        for key, (verts, tris) in pieces.items():
            if not len(tris):
                continue
            points = f.createIfcCartesianPointList3D([tuple(float(c) * u for c in p) for p in verts])
            item = f.createIfcTriangulatedFaceSet(points, None, None, [tuple(int(i) + 1 for i in t) for t in tris],
                                                  None)
            f.createIfcStyledItem(item, [self._material_style(self._material(key, lang))], None)
            items.append(item)
            if main is None or len(tris) > len(pieces[main][1]):
                main = key
        if not items:
            raise EditRefused("surface_empty")
        self._clear_representations(element)
        self._body(element, items, "Tessellation")
        wanted = self._material(main, lang)
        current = ifcopenshell.util.element.get_material(element)
        if current != wanted:
            if current is not None:
                api.material.unassign_material(f, products=[element])
            api.material.assign_material(f, products=[element], type="IfcMaterial", material=wanted)
        area = surface.area()
        self._set_params(element, {"Definicao": ps.dumps(data),
                                   "Resumo": json.dumps(self._summary(surface, parts, warnings), ensure_ascii=False)})
        if element.is_a("IfcRoof"):
            self._set_qto(element, "Qto_RoofBaseQuantities", {"GrossArea": area * u * u})
        self._surface_links_add(element.GlobalId, data)
        self._surface_report = {"area": area, "parts": len(parts), "warnings": warnings}
        return self._surface_report

    # ------------------------------------------------------------ following the curves it was made of

    def _surface_links_add(self, guid, data):
        links = getattr(self, "_surface_links", None)
        if links is None:
            return
        for c in data.get("curves") or ():
            if c.get("source"):
                links.setdefault(c["source"], set()).add(guid)

    def surfaces_following(self, uids):
        """{GlobalId: [curve uids]} of the parametric surfaces made of these sketches' curves (the links known
        since the file was read: one look over its elements the first time)."""
        links = getattr(self, "_surface_links", None)
        if links is None:
            links = self._surface_links = {}
            for cls in {c for c, _p in USAGES.values()}:
                for e in self.file.by_type(cls):
                    if self.kind_of(e.GlobalId) == KIND:
                        self._surface_links_add(e.GlobalId, self.surface_definition(e.GlobalId))
        out = {}
        for uid in uids:
            for guid in links.get(uid, ()):
                e = self.by_guid(guid)
                if e is None or self.kind_of(guid) != KIND:
                    continue
                if any(c.get("source") == uid for c in self.surface_definition(guid).get("curves") or ()):
                    out.setdefault(guid, []).append(uid)
        return out

    def follow_curves(self, guid, curves, lang="pt"):
        """The surface's curves taken again from the sketches they came from: `curves` {uid: [(points (k, 3) world,
        closed)…]} (a sketch's chains) — each of its curves made of one of them takes the chain nearest to what it
        was. Its body made again."""
        element = self.by_guid(guid)
        data = self.surface_definition(guid)
        m = self._placement_si(element)
        inv = np.linalg.inv(m)
        changed = False
        for c in data.get("curves") or ():
            chains = curves.get(c.get("source"))
            if not chains or "points" not in c:
                continue
            old = np.asarray(c["points"], float)
            best, best_d = None, None
            for pts, closed in chains:
                local = np.asarray(pts, float) @ inv[:3, :3].T + inv[:3, 3]
                d = float(np.linalg.norm(local.mean(axis=0) - old.mean(axis=0)))
                if best_d is None or d < best_d:
                    best, best_d = (local, closed), d
            if best is not None:
                c["points"] = [[round(float(x), 6) for x in q] for q in best[0]]
                c["closed"] = bool(best[1])
                changed = True
        if changed:
            self._surface_store(element, data, lang)
        return changed
