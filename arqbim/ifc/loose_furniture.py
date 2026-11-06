"""Loose furniture of the program's own (0.440), mixed into IfcModel: an IfcFurniture of its kind (BED, SOFA, CHAIR,
TABLE, DESK, SHELF, or USERDEFINED with its ObjectType: «Mesa de cabeceira», «Móvel de TV», «Planta em vaso»), not
built in, its body its parts (core/loose_furniture) — an IfcExtrudedAreaSolid each, a box or a cylinder, coloured by
its material's style —, made again from its parameters when they change. Its material: the parts' materials, a
constituent set when there are several (Pset_FurnitureTypeCommon: its nominal sizes, IsBuiltIn false).

ArqSynth_Parametros: Elemento "loose", Peca (the catalogue's key), Largura, Profundidade, Altura. Its placement: the
middle of its footprint on the floor, x across its width, y towards its back."""

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import loose_furniture as core_loose
from .edit import EditRefused

api = ifcopenshell.api


class LooseFurnitureMixin:
    def loose_params(self, guid):
        """{piece, width, depth, height} of a piece of loose furniture."""
        p = self._params(self.by_guid(guid))
        key = p.get("Peca") if p.get("Peca") in core_loose.PIECES else "cadeira"
        w0, d0, h0 = core_loose.defaults(key)
        return {"piece": key, "width": float(p.get("Largura") or w0), "depth": float(p.get("Profundidade") or d0),
                "height": float(p.get("Altura") or h0)}

    def _set_loose_body(self, element, lang="pt"):
        f, u = self.file, 1.0 / self.unit_scale
        p = self.loose_params(element.GlobalId)
        items, styled, used = [], [], []
        for part in core_loose.parts(p["piece"], p["width"], p["depth"], p["height"]):
            x0, y0, z0, x1, y1, z1 = part.box
            dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
            if min(dx, dy, dz) <= 1e-6:
                continue
            centre = f.createIfcAxis2Placement2D(f.createIfcCartesianPoint((float((x0 + x1) / 2 * u),
                                                                             float((y0 + y1) / 2 * u))), None)
            if part.round:
                profile = f.createIfcCircleProfileDef("AREA", None, centre, float(min(dx, dy) / 2 * u))
            else:
                profile = f.createIfcRectangleProfileDef("AREA", None, centre, float(dx * u), float(dy * u))
            items.append(f.createIfcExtrudedAreaSolid(
                profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, float(z0 * u))), None, None),
                f.createIfcDirection((0.0, 0.0, 1.0)), float(dz * u)))
            styled.append((items[-1], part.material))
            if part.material not in used:
                used.append(part.material)
        if not items:
            raise EditRefused("loose_size")
        self._clear_representations(element)
        api.geometry.assign_representation(f, product=element, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))
        materials = {key: self._material(key, lang) for key in used}
        for item, key in styled:                       # (each part in its material's colour)
            f.createIfcStyledItem(item, [self._material_style(materials[key])], None)
        self._loose_material(element, [materials[k] for k in used], lang)
        common = ifcopenshell.util.element.get_psets(element).get("Pset_FurnitureTypeCommon")
        pset = f.by_id(common["id"]) if common else api.pset.add_pset(f, product=element,
                                                                        name="Pset_FurnitureTypeCommon")
        api.pset.edit_pset(f, pset=pset, properties={"NominalLength": p["width"] * u, "NominalDepth": p["depth"] * u,
                                                     "NominalHeight": p["height"] * u, "IsBuiltIn": False})

    def _loose_material(self, element, materials, lang):
        """Its material: the one of its parts, or a constituent set of them (shared by the pieces with the same)."""
        f = self.file
        if len(materials) == 1:
            wanted = materials[0]
        else:
            name = " + ".join(m.Name for m in materials)
            wanted = next((s for s in f.by_type("IfcMaterialConstituentSet") if s.Name == name), None)
            if wanted is None:
                wanted = api.material.add_material_set(f, name=name, set_type="IfcMaterialConstituentSet")
                for m in materials:
                    api.material.add_constituent(f, constituent_set=wanted, material=m).Name = m.Name
        if ifcopenshell.util.element.get_material(element, should_skip_usage=True) != wanted:
            api.material.unassign_material(f, products=[element])
            api.material.assign_material(f, products=[element], type=wanted.is_a(), material=wanted)

    def add_loose(self, key, centre, angle, name, lang="pt", storey=None, width=None, depth=None, height=None):
        """(0.440) A piece of loose furniture (the catalogue's `key`) with the middle of its footprint at `centre`
        (its floor's height in centre[2]), its width along `angle` degrees, its front towards −y turned so. Returns the
        IfcFurniture."""
        if key not in core_loose.PIECES:
            raise EditRefused("loose_bad")
        w0, d0, h0 = core_loose.defaults(key)
        w, d, h = (float(v) if v else v0 for v, v0 in ((width, w0), (depth, d0), (height, h0)))
        problem = core_loose.check(key, w, d, h)
        if problem:
            raise EditRefused(problem)
        f = self.file
        _group, ptype, names, _sizes = core_loose.PIECES[key]
        element = api.root.create_entity(f, ifc_class="IfcFurniture", name=name, predefined_type=ptype)
        element.ObjectType = names[0 if lang == "pt" else 1]
        a = np.radians(float(angle))
        x = np.array((np.cos(a), np.sin(a), 0.0))
        m = np.eye(4)
        m[:3, 0], m[:3, 1], m[:3, 3] = x, np.cross((0.0, 0.0, 1.0), x), np.asarray(centre, dtype=float)
        self._place(element, m)
        container = self.storey(storey) if storey is not None else self.storey_at(float(centre[2]))
        api.spatial.assign_container(f, products=[element], relating_structure=container)
        self._mark(element, "loose")
        self._set_params(element, {"Peca": key, "Largura": w, "Profundidade": d, "Altura": h})
        self._set_loose_body(element, lang)
        return element

    def set_loose(self, guid, piece=None, width=None, depth=None, height=None, lang="pt"):
        """(0.440) Another piece (its own sizes, unless given), or its width, depth or height: made again, its
        footprint's middle staying where it is."""
        element, _ = self._require(guid, "loose")
        p = self.loose_params(guid)
        if piece is not None and piece != p["piece"]:
            if piece not in core_loose.PIECES:
                raise EditRefused("loose_bad")
            w0, d0, h0 = core_loose.defaults(piece)
            p.update(piece=piece, width=w0, depth=d0, height=h0)
            _group, ptype, names, _sizes = core_loose.PIECES[piece]
            element.PredefinedType = ptype
            element.ObjectType = names[0 if lang == "pt" else 1]
        for key, value in (("width", width), ("depth", depth), ("height", height)):
            if value is not None:
                p[key] = float(value)
        problem = core_loose.check(p["piece"], p["width"], p["depth"], p["height"])
        if problem:
            raise EditRefused(problem)
        self._set_params(element, {"Peca": p["piece"], "Largura": p["width"], "Profundidade": p["depth"],
                                   "Altura": p["height"]})
        self._set_loose_body(element, lang)
