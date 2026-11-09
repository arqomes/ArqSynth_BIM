"""(0.509) Steel stairs, mixed into IfcModel (core/steel_stair's geometry): an IfcStair (STRAIGHT_RUN_STAIR, of steel)
whose body is its treads — grating or folded chequered plate —, its two stringers steel pieces of their own (the
Peça metálica's: marks, lists, NC1, cutting of the bars), cut by their planes as a mitre is (Cortes). The stair keeps
its values (ArqSynth_Parametros: Elemento "steel_stair", Desnivel, Largura, Cobertor, Degrau, Perfil, Vigas — its
stringers' GlobalIds, JSON); deleting it takes its stringers."""

import json

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import stairs as core_stairs
from ..core import steel_stair as core_steel_stair
from . import catalog
from .edit import EditRefused

api = ifcopenshell.api
Z = np.array((0.0, 0.0, 1.0))


class SteelStairMixin:
    def add_steel_stair(self, foot, direction, rise, width, going, section="UPN200", tread="grelha", grade="S275",
                        name="", lang="pt", storey=None):
        """A straight steel stair from `foot` (the middle of its first riser, at the floor) along `direction` (plan),
        rising `rise` (m), `width` between its stringers' webs, its treads `going` deep, of `tread` («grelha» /
        «chapa»), its stringers of the channel `section`. Returns the IfcStair."""
        from ..core import steel
        if width < 0.5 or going < 0.15 or rise < 0.30:
            raise EditRefused("stair_small")
        if tread not in core_steel_stair.TREADS or steel.get(section) is None:
            raise EditRefused("not_editable")
        f = self.file
        d = np.array((float(direction[0]), float(direction[1]), 0.0))
        d /= np.linalg.norm(d)
        left = np.cross(Z, d)
        foot = np.asarray(foot, dtype=float)
        stair = api.root.create_entity(f, ifc_class="IfcStair", name=name, predefined_type="STRAIGHT_RUN_STAIR")
        m = np.eye(4)
        m[:3, 0], m[:3, 1], m[:3, 3] = d, left, foot
        self._place(stair, m)
        container = self.storey(storey) if storey is not None else self.storey_at(float(foot[2]))
        api.spatial.assign_container(f, products=[stair], relating_structure=container)
        api.material.assign_material(f, products=[stair], type="IfcMaterial",
                                     material=self._material(steel.GRADE_MATERIAL.get(grade, "aco_s275"), lang))
        self._mark(stair, "steel_stair")
        self._set_params(stair, {"Desnivel": float(rise), "Largura": float(width), "Cobertor": float(going),
                                 "Degrau": tread, "Perfil": steel.get(section).name, "Classe": grade})
        self._set_steel_stair_body(stair)
        sec = steel.get(section)
        base = catalog.BY_KEY["viga_ipe200"]
        spec = catalog.steel_spec(base, sec.name, grade)
        (sx, sz), (ex, ez), cuts = core_steel_stair.stringer(rise, going, sec.h / 1000.0)
        word = "Viga de escada" if lang == "pt" else "Stringer"
        made = []
        for k, sign in enumerate((1.0, -1.0)):             # (its left, then its right — their webs to the treads)
            y = core_steel_stair.side(width, sec.b / 1000.0) * sign
            start = foot + d * sx + left * y + Z * sz
            end = foot + d * ex + left * y + Z * ez
            e = self.add_steel_member(spec, start, end, "{} {}".format(word, k + 1), lang, storey=storey,
                                      function="member", cardinal=5, rotation=0.0 if sign > 0 else 180.0)
            pm = self.placement(e.GlobalId)
            rot = pm[:3, :3] / np.linalg.norm(pm[:3, :3], axis=0)
            stored = []
            for end_k, (px, pz), (nx, nz) in cuts:
                point = foot + d * px + left * y + Z * pz
                normal = d * nx + Z * nz
                rel = point - (start if end_k == 0 else end)
                stored.append({"end": end_k, "p": [float(v) for v in rot.T @ rel],
                               "n": [float(v) for v in rot.T @ normal]})
            self.set_steel_cuts(e, cuts=stored)
            self.set_steel_member(e.GlobalId, lang=lang)
            self._set_params(e, {"Escada": stair.GlobalId})
            made.append(e.GlobalId)
        self._set_params(stair, {"Vigas": json.dumps(made)})
        return stair

    def steel_stair_params(self, guid):
        p = self._params(self.by_guid(guid))
        return {"rise": float(p["Desnivel"]), "width": float(p["Largura"]), "going": float(p["Cobertor"]),
                "tread": p.get("Degrau") or "grelha", "section": p.get("Perfil") or "UPN200",
                "grade": p.get("Classe") or "S275", "stringers": json.loads(p.get("Vigas") or "[]")}

    def steel_stair_parts(self, guids):
        """(0.509) The stringers of the steel stairs among these elements (not among them already)."""
        out = []
        for g in guids:
            if self.by_guid(g) is not None and self.kind_of(g) == "steel_stair":
                out += [s for s in self.steel_stair_params(g)["stringers"]
                        if self.by_guid(s) is not None and s not in guids and s not in out]
        return out

    def _set_steel_stair_body(self, stair):
        """Its treads, each extruded across its width (from its left side to its right)."""
        f, u = self.file, 1.0 / self.unit_scale
        p = self.steel_stair_params(stair.GlobalId)
        w = p["width"]
        items = []
        for _x0, _x1, _top, ring in core_steel_stair.treads(p["rise"], p["going"], p["tread"]):
            coords = [(float(x * u), float(z * u)) for x, z in ring + ring[:1]]
            items.append(f.createIfcExtrudedAreaSolid(
                f.createIfcArbitraryClosedProfileDef("AREA", None, f.createIfcIndexedPolyCurve(
                    f.createIfcCartesianPointList2D(coords), None, False)),
                f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, float(w / 2 * u), 0.0)),
                                            f.createIfcDirection((0.0, -1.0, 0.0)), f.createIfcDirection((1.0, 0.0, 0.0))),
                f.createIfcDirection((0.0, 0.0, 1.0)), float(w * u)))
        self._clear_representations(stair)
        api.geometry.assign_representation(f, product=stair, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))
        n, h = core_stairs.risers(p["rise"])
        common = ifcopenshell.util.element.get_psets(stair).get("Pset_StairCommon")
        pset = f.by_id(common["id"]) if common else api.pset.add_pset(f, product=stair, name="Pset_StairCommon")
        api.pset.edit_pset(f, pset=pset, properties={
            "NumberOfRiser": n, "NumberOfTreads": n - 1, "RiserHeight": h * u, "TreadLength": p["going"] * u,
            "IsExternal": False})
