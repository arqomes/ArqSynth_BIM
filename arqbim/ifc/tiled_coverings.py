"""(0.563, PLANO.md «Gerador de revestimentos 3D em IFC», step 2) A Revestimento, mixed into IfcModel: an IfcCovering
(CLADDING on an upright face, FLOORING on a floor, CEILING under one) laid in pieces on a flat face — each piece its
own solid with the joints between, on its bed of glue or mortar, the grout set back in the joints. Its type an
IfcCoveringType of the finish's name; its material a layer set (bed, piece); its body two tessellated items, the
pieces in their material's colour and the bed and grout in theirs; Qto_CoveringBaseQuantities (Width, GrossArea,
NetArea) and ArqSynth_Paginacao (whole and cut pieces, narrow cuts, the narrowest).

ArqSynth_Parametros: Elemento "tiled_covering", Contorno and Furos (the face in its own frame — its placement: x, y
in the face, z out of it), Paginacao (core/tiling's layout, JSON), Acabamento (core/covering_finishes key), Material,
Espessura (the piece's), Cama, MaterialCama, Junta (the grout's material, «» none), Recuo, Origem (the element or
drawing it was laid on)."""

import json

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from ..core import covering_finishes as cf
from ..core import tiling as tl
from .edit import EditRefused

api = ifcopenshell.api
KIND = "tiled_covering"
MAX_PIECES = 20000          # the most pieces one Revestimento carries (a whole façade in 10 × 10 cm mosaic is not one)


def _pts(text):
    return [tuple(float(v) for v in q.split(",")) for q in (text or "").split(";") if q]


def _text(pts):
    return ";".join("{:.6f},{:.6f}".format(float(x), float(y)) for x, y in pts)


def predefined_for(normal):
    """CLADDING on an upright face, FLOORING on one facing up, CEILING on one facing down."""
    nz = float(normal[2])
    return "FLOORING" if nz > 0.7 else "CEILING" if nz < -0.7 else "CLADDING"


class TiledCoveringMixin:
    def tiled_params(self, guid):
        """{finish, layout, material, thickness, bed, bed_material, grout, recess, source} of a Revestimento."""
        e, _ = self._require(guid, KIND)
        p = self._params(e)
        try:
            layout = json.loads(p.get("Paginacao") or "{}")
        except ValueError:
            layout = {}
        fin = cf.finish(p.get("Acabamento"))
        return {"finish": p.get("Acabamento") or fin.key, "layout": tl.layout(layout),
                "material": p.get("Material") or fin.material,
                "thickness": float(p.get("Espessura") if p.get("Espessura") is not None else fin.thickness),
                "bed": float(p.get("Cama") if p.get("Cama") is not None else fin.bed),
                "bed_material": p.get("MaterialCama") or fin.bed_material,
                "grout": p.get("Junta") if p.get("Junta") is not None else fin.grout,
                "recess": float(p.get("Recuo") if p.get("Recuo") is not None else fin.recess),
                "source": p.get("Origem") or ""}

    def tiled_face(self, guid):
        """(frame (4, 4), face shapely in it) of a Revestimento."""
        e, _ = self._require(guid, KIND)
        p = self._params(e)
        face = Polygon(_pts(p.get("Contorno")), [_pts(h) for h in (p.get("Furos") or "").split("|") if h]).buffer(0)
        return self._placement_si(e), face

    def tiled_layout(self, guid):
        """core/tiling's Result of a Revestimento's pieces as they are."""
        _m, face = self.tiled_face(guid)
        q = orient(face, 1.0)
        return tl.lay(list(q.exterior.coords)[:-1], self.tiled_params(guid)["layout"],
                      [list(h.coords)[:-1] for h in q.interiors])

    def add_tiled_covering(self, frame, face, finish, name, layout=None, source="", lang="pt", storey=None,
                           **changes):
        """A Revestimento on a flat face: `frame` (4, 4) its plane (x, y in it, z out of it, its origin on it),
        `face` (shapely, the frame's x, y) the part covered; `finish` a core/covering_finishes key — its layout
        (`layout` over it) and anything of it changed by `changes` (as set_tiled_covering's). Returns it."""
        if finish not in cf.FINISHES:
            raise EditRefused("tiling_finish")
        fin = cf.FINISHES[finish]
        frame = np.array(frame, dtype=float)
        f = self.file
        e = api.root.create_entity(f, ifc_class="IfcCovering", name=name,
                                   predefined_type=predefined_for(frame[:3, 2]))
        self._place(e, frame)
        container = self.storey(storey) if storey is not None else self.storey_at(float(frame[2, 3]) + 0.01)
        api.spatial.assign_container(f, products=[e], relating_structure=container)
        self._mark(e, KIND)
        d = fin.layout()
        d.update(layout or {})
        self._set_params(e, {"Acabamento": finish, "Origem": str(source or "")})
        self.set_tiled_covering(e.GlobalId, layout=d, face=face, lang=lang, **changes)
        return e

    def set_tiled_covering(self, guid, layout=None, face=None, frame=None, finish=None, material=None,
                           thickness=None, bed=None, bed_material=None, grout=None, recess=None, lang="pt"):
        """A Revestimento changed: its layout (all of it, or the keys given), its face or plane, another finish
        (its piece, layout, bed and grout — the layout's origin kept), or any one of these; its body made again."""
        e, _ = self._require(guid, KIND)
        p = self._params(e)
        old = json.loads(p.get("Paginacao") or "{}") if p.get("Paginacao") else {}
        changes = {}
        if finish is not None:
            if finish not in cf.FINISHES:
                raise EditRefused("tiling_finish")
            fin = cf.FINISHES[finish]
            keep = {k: old[k] for k in ("origin", "point", "align", "dx", "dy", "angle", "min_cut") if k in old}
            old = dict(fin.layout(), **keep)
            changes.update({"Acabamento": finish, "Material": fin.material, "Espessura": fin.thickness,
                            "Cama": fin.bed, "MaterialCama": fin.bed_material, "Junta": fin.grout,
                            "Recuo": fin.recess})
        if layout is not None:
            old.update(layout)
        try:
            d = tl.layout(old)
        except tl.LayoutError as exc:
            raise EditRefused(exc.code) from None
        changes["Paginacao"] = json.dumps({k: (list(v) if isinstance(v, tuple) else v) for k, v in d.items()},
                                          sort_keys=True)
        for key, value in (("Material", material), ("Espessura", thickness), ("Cama", bed),
                           ("MaterialCama", bed_material), ("Junta", grout), ("Recuo", recess)):
            if value is not None:
                changes[key] = value
        from . import catalog
        for key in ("Material", "MaterialCama"):
            if changes.get(key) is not None and changes[key] not in catalog.MATERIALS:
                raise EditRefused("tiling_material")
        if changes.get("Junta") and changes["Junta"] not in catalog.MATERIALS:
            raise EditRefused("tiling_material")
        for key in ("Espessura", "Cama", "Recuo"):
            if key in changes and not 0.0 <= float(changes[key]) <= 0.5:
                raise EditRefused("tiling_thickness")
        if frame is not None:
            self._place(e, np.array(frame, dtype=float))
        if face is not None:
            rings = [q for q in getattr(face, "geoms", [face]) if q.geom_type == "Polygon" and q.area > 1e-6]
            if not rings:
                raise EditRefused("tiling_empty")
            q = orient(max(rings, key=lambda r: r.area), 1.0)
            changes.update({"Contorno": _text(list(q.exterior.coords)[:-1]),
                            "Furos": "|".join(_text(list(h.coords)[:-1]) for h in q.interiors)})
        self._set_params(e, changes)
        self._tiled_body(e, lang)

    def _tiled_body(self, e, lang="pt"):
        f, u = self.file, 1.0 / self.unit_scale
        p = self.tiled_params(e.GlobalId)
        _m, face = self.tiled_face(e.GlobalId)
        if face.is_empty or face.area < 1e-6:
            raise EditRefused("tiling_empty")
        try:
            result = self.tiled_layout(e.GlobalId)
        except tl.LayoutError as exc:
            raise EditRefused(exc.code) from None
        if len(result.pieces) > MAX_PIECES:
            raise EditRefused("tiling_too_many")
        bed, t, recess = p["bed"], max(p["thickness"], 0.001), min(p["recess"], p["thickness"])
        items, styled = [], []

        def item(verts, tris, key):
            if not len(tris):
                return
            it = f.createIfcTriangulatedFaceSet(
                f.createIfcCartesianPointList3D([tuple(float(c) * u for c in row) for row in verts]), None, True,
                [tuple(int(i) + 1 for i in row) for row in tris], None)
            items.append(it)
            styled.append((it, key))

        verts, tris = tl.prisms([(pc.points, pc.holes) for pc in result.pieces], bed, bed + t)
        item(verts, tris, p["material"])
        q = orient(face, 1.0)
        outline = (list(q.exterior.coords)[:-1], [list(h.coords)[:-1] for h in q.interiors])
        if bed > 1e-6:                                   # (the bed under the pieces)
            verts, tris = tl.prisms([outline], 0.0, bed)
            item(verts, tris, p["bed_material"])
        if p["grout"] and recess > 1e-6 and t - recess > 1e-6:   # (the grout in the joints only, back from the
            verts, tris = tl.prisms(tl.joints(result, face, p["layout"]), bed, bed + t - recess)  # face — never
            item(verts, tris, p["grout"])                        # behind a piece, where it would show through)
        if not items:
            raise EditRefused("tiling_empty")
        self._clear_representations(e)
        api.geometry.assign_representation(f, product=e, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "Tessellation", items))
        materials = {}
        for it, key in styled:
            if key not in materials:
                materials[key] = self._material(key, lang)
            f.createIfcStyledItem(it, [self._material_style(materials[key])], None)
        self._tiled_material(e, p, lang)
        total = bed + t
        self._set_qto(e, "Qto_CoveringBaseQuantities", {"Width": total * u, "GrossArea": float(face.area),
                                                        "NetArea": float(sum(pc.area for pc in result.pieces))})
        s = result.summary(p["layout"]["min_cut"])
        own = ifcopenshell.util.element.get_psets(e).get("ArqSynth_Paginacao")
        pset = f.by_id(own["id"]) if own else api.pset.add_pset(f, product=e, name="ArqSynth_Paginacao")
        api.pset.edit_pset(f, pset=pset, properties={
            "Pecas": int(s["pieces"]), "PecasInteiras": int(s["whole"]), "PecasCortadas": int(s["cut"]),
            "CortesEstreitos": int(s["narrow"]),
            "CorteMaisEstreito": float(s["narrowest"]) if s["narrowest"] != float("inf") else 0.0,
            "Aparelho": p["layout"]["pattern"]})

    def _tiled_material(self, e, p, lang):
        """Its material: a layer set — the bed (if any), the piece — shared by those alike; its type: an
        IfcCoveringType of the finish's name."""
        f = self.file
        fin = cf.finish(p["finish"])
        layers = ([(p["bed_material"], p["bed"])] if p["bed"] > 1e-6 else []) + [(p["material"], p["thickness"])]
        mats = [(self._material(k, lang), t) for k, t in layers]
        name = " + ".join("{} {:.0f} mm".format(m.Name, t * 1000) for m, t in mats)
        wanted = next((s for s in f.by_type("IfcMaterialLayerSet") if s.LayerSetName == name), None)
        if wanted is None:
            wanted = api.material.add_material_set(f, name=name, set_type="IfcMaterialLayerSet")
            for m, t in mats:
                layer = api.material.add_layer(f, layer_set=wanted, material=m)
                layer.LayerThickness = float(t) / self.unit_scale
        if ifcopenshell.util.element.get_material(e, should_skip_usage=True) != wanted:
            api.material.unassign_material(f, products=[e])
            api.material.assign_material(f, products=[e], type="IfcMaterialLayerSet", material=wanted)
        tname = fin.name_pt if lang == "pt" else fin.name_en
        kind = predefined_for(self._placement_si(e)[:3, 2])   # (the occurrence's own goes when typed: the type's)
        ctype = next((ty for ty in f.by_type("IfcCoveringType") if ty.Name == tname
                      and ty.PredefinedType == kind), None)
        if ctype is None:
            ctype = api.root.create_entity(f, ifc_class="IfcCoveringType", name=tname, predefined_type=kind)
        if ifcopenshell.util.element.get_type(e) != ctype:
            api.type.assign_type(f, related_objects=[e], relating_type=ctype)
