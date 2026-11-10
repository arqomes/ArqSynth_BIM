"""Reinforcement in the IFC (0.166, Phase 9, step 4): each set of a member's bars of one diameter, shape and length an
IfcReinforcingBar (IFC4: one may stand for a row of bars) — MAIN, SHEAR for a beam's stirrups, LIGATURE for a
column's ties —, each bar an IfcSweptDiskSolid along its centreline (Body, AdvancedSweptSolid); its nominal diameter,
cross-section and cut length, ribbed (TEXTURED); Pset_ReinforcingBarCommon (its position, diameter, length, spacing,
shape code) and Qto_ReinforcingElementBaseQuantities (how many, their weight); the steel as its material ("Aço A500
NR"), in its member's storey. Tied to its member (the program's pset: the member, and the design its bars were laid
out from): removed with it, laid out again on it when its shape changes — as Revit's hosted rebar. (0.285, the
owner's choice) Its member aggregates it too (IfcRelAggregates — as Tekla's cast unit: the concrete and its bars
one thing to a structural program); being a part, it is no more in the storey itself, but in its member's. The member gets
Pset_ConcreteElementGeneral (its concrete and steel classes, its cover) and its bars' pitch (Pset_ReinforcementBarPitch
OfBeam / OfColumn) or count (Pset_ReinforcementBarCountOfIndependentFooting). The positions are numbered over the
project: equal bars (diameter, shape, length) one position, as a bar schedule lists them."""

import json
import re

import numpy as np

import ifcopenshell.api as api
import ifcopenshell.util.element

from ..core import actions as act
from ..core import ec2
from ..core import rebar as rb

ROLE_NAMES = {"bottom": ("armadura inferior", "bottom bars"), "top": ("armadura superior", "top bars"),
              "stirrups": ("estribos", "stirrups"), "main": ("armadura longitudinal", "main bars"),
              "ties": ("cintas", "ties"), "mesh_x": ("malha inferior X", "bottom mesh X"),
              "mesh_y": ("malha inferior Y", "bottom mesh Y"),
              "top_x": ("armadura superior X sobre os apoios", "top bars X over the supports"),       # (0.224)
              "top_y": ("armadura superior Y sobre os apoios", "top bars Y over the supports"),
              "wall_v": ("armadura vertical", "vertical bars"),                                       # (0.342)
              "wall_h": ("armadura horizontal", "horizontal bars"),
              "wall_trim": ("reforço dos vãos", "bars round the openings")}
ROLE_ORDER = {r: k for k, r in enumerate(rb.ROLES)}
HOST_ORDER = {"IfcColumn": 0, "IfcBeam": 1, "IfcSlab": 2, "IfcFooting": 3, "IfcWall": 4}
STEEL_MATERIAL = {"A400": "a400", "A500": "a500"}


def _natural(text):
    return [(0, int(p), "") if p.isdigit() else (1, 0, p.lower()) for p in re.split(r"(\d+)", text)]


class RebarMixin:
    # ------------------------------------------------------------ what there is

    def rebars_of(self, hosts):
        """{member GlobalId: [the GlobalIds of its IfcReinforcingBars]} for these members."""
        wanted, out = set(hosts), {}
        for e in self.file.by_type("IfcReinforcingBar"):
            host = self._params(e).get("Armadura")
            if host in wanted:
                out.setdefault(host, []).append(e.GlobalId)
        return out

    def rebar_design(self, host):
        """The design a member's bars were laid out from (ElementDesign.stored()), or None."""
        for g in self.rebars_of([host]).get(host, ()):
            text = self._params(self.by_guid(g)).get("Projeto")
            if text:
                return json.loads(text)
        return None

    def remove_rebars(self, hosts):
        for guids in self.rebars_of(hosts).values():
            for g in guids:
                e = self.by_guid(g)
                if e is not None:
                    api.root.remove_product(self.file, product=e)

    # ------------------------------------------------------------ laying them out

    def write_rebars(self, stored, lang="pt"):
        """Each member's bars from its design (stored: {member GlobalId: ElementDesign.stored()}), those it had
        removed first; the positions numbered again. Returns the GlobalIds made."""
        self.remove_rebars(list(stored))
        made = []
        for host, info in stored.items():
            made += self._lay_rebars(host, dict(info, lang=lang))
        self.number_rebars()
        return made

    def follow_rebars(self, changed):
        """The bars of the members among `changed` (their shape changed) laid out again on them, as designed."""
        if not changed:
            return []
        bars = self.file.by_type("IfcReinforcingBar")
        if not bars:
            return []
        wanted = {g for g in changed if (e := self.by_guid(g)) is not None and e.is_a() in HOST_ORDER}
        if not wanted:
            return []                                   # (nothing that holds bars changed: no pset read)
        stored = {}
        for e in bars:
            p = self._params(e)
            if p.get("Armadura") in wanted and p.get("Projeto"):
                stored.setdefault(p["Armadura"], json.loads(p["Projeto"]))
        if not stored:
            return []
        self.remove_rebars(list(stored))
        made = []
        for host, info in stored.items():
            if self.by_guid(host) is not None:
                made += self._lay_rebars(host, info)
        self.number_rebars()
        return made

    def _host_sets(self, host, info):
        """[core.rebar.BarSet] of a member laid out from its design on its shape now — (0.230) its bars longer than
        those sold spliced (a column's lap at each floor already)."""
        kind = info["kind"]
        sets = self._laid_sets(host, info)
        if kind in ("beam", "slab", "footing", "wall"):
            sets = rb.spliced(sets, act.CONCRETE[info["concrete"]], act.STEEL[info["steel"]])
        return sets

    def _laid_sets(self, host, info):
        design = rb.design_from(info)
        fck, fyk = act.CONCRETE[info["concrete"]], act.STEEL[info["steel"]]
        kind = info["kind"]
        if kind == "beam":
            start, end, top, width, height = self.beam_params(host)
            return rb.beam_sets(start[:2], end[:2], top, width, height, design, fck, fyk,
                                tuple(info.get("ext", (0.0, 0.0))))
        if kind == "column":
            centre, x, half, base, top = self.column_box(host)
            return rb.column_sets(centre, x, half, base, top, design, fck, fyk, float(info.get("into", 0.0)),
                                  bool(info.get("lap", False)), info.get("shape", "rect"),
                                  float(info.get("web", 0.0)))             # (0.227: round, L, T)
        if kind == "footing":
            centre, x, length, width, top = self.footing_params(host)
            depth = top - float(self.placement(host)[2, 3])
            return rb.footing_sets(centre, x[:2], length, width, top, depth, design)
        if kind == "slab":
            s = self.slab_outline(host)
            if s is None:
                return []
            x_dir = tuple(info.get("x_dir", (1.0, 0.0)))
            return rb.slab_sets(s["outline"], float(s["top"]), float(s["thickness"]), design, x_dir) \
                + rb.slab_top_sets(s["outline"], float(s["top"]), float(s["thickness"]), design, x_dir,
                                   info.get("supports", []))                  # (0.224: over its beams)
        if kind == "wall":                                                      # (0.342) a concrete wall
            start, end, thickness = self.wall_axis(host)
            _length, height, _t = self.wall_params(host)
            base = float(start[2])
            openings = []
            for rel in (self.by_guid(host).HasOpenings or ()):
                for fill in (rel.RelatedOpeningElement.HasFillings or ()):
                    try:
                        st = self.filling_state(fill.RelatedBuildingElement.GlobalId)
                    except Exception:                   # (a filling this program does not edit: no hole left)
                        continue
                    sill = float(st.get("sill") or 0.0)
                    openings.append((float(st["s"]), float(st["s"]) + float(st["width"]), base + sill,
                                     base + sill + float(st["height"])))
            return rb.wall_sets(start[:2], end[:2], base, base + height, thickness, openings, design, fck, fyk,
                                float(info.get("into", 0.0)), bool(info.get("lap", False)))
        return []

    def _lay_rebars(self, host, info):
        f, u = self.file, 1.0 / self.unit_scale
        lang = info.get("lang", "pt")
        member = self.by_guid(host)
        sets = self._host_sets(host, info)
        if not sets:
            return []
        self._ensure_mass_unit()
        material =self._material(STEEL_MATERIAL.get(info["steel"], "a500"), lang)
        text = f.create_entity("IfcText", json.dumps(info, ensure_ascii=False))
        made, parts = [], []
        for st in sets:
            for shape, length, bends, bars in st.groups():
                name = "{} — {}".format(member.Name or member.is_a(), ROLE_NAMES[st.role][0 if lang == "pt" else 1])
                e = api.root.create_entity(f, ifc_class="IfcReinforcingBar", name=name, predefined_type=st.kind)
                d = st.diameter / 1000.0
                e.NominalDiameter = d * u
                e.CrossSectionArea = ec2.bar_area(st.diameter) * u * u
                e.BarLength = length * u
                e.BarSurface = "TEXTURED"
                first = np.asarray(bars[0][0], dtype=float)
                m = np.eye(4)
                m[:3, 3] = first
                self._place(e, m)
                items = []
                for bar in bars:
                    pts = [f.createIfcCartesianPoint(tuple(float(c) for c in (np.asarray(p, dtype=float) - first) * u))
                           for p in bar]
                    items.append(f.createIfcSweptDiskSolid(f.createIfcPolyline(pts), d / 2.0 * u, None, None, None))
                api.geometry.assign_representation(f, product=e, representation=f.createIfcShapeRepresentation(
                    self.body, self.body.ContextIdentifier, "AdvancedSweptSolid", items))
                api.material.assign_material(f, products=[e], type="IfcMaterial", material=material)
                common = {"NominalDiameter": d * u, "BarLength": length * u, "BarSurface": "TEXTURED",
                          "BendingShapeCode": shape}
                if st.spacing:
                    common["BarSpacing"] = st.spacing * u
                pset = api.pset.add_pset(f, product=e, name="Pset_ReinforcingBarCommon")
                api.pset.edit_pset(f, pset=pset, properties=common)
                self._set_qto(e, "Qto_ReinforcingElementBaseQuantities",
                              {"Count": len(bars), "Weight": round(len(bars) * length * ec2.bar_mass(st.diameter), 3)})
                self._set_params(e, {"Elemento": "rebar", "Armadura": host, "Funcao": st.role, "Dobragem": bends,
                                     "Projeto": text})
                made.append(e.GlobalId)
                parts.append(e)
        if parts:          # (0.285, the owner's choice) its member aggregates them — the bars its parts, in its storey
            api.aggregate.assign_object(f, products=parts, relating_object=member)
        self._host_psets(member, info, sets)
        return made

    def _host_psets(self, member, info, sets):
        """The member's concrete properties and its bars' pitch, as IFC4 has them."""
        u = 1.0 / self.unit_scale
        common = api.pset.add_pset(self.file, product=member, name="Pset_ConcreteElementGeneral")
        api.pset.edit_pset(self.file, pset=common, properties={
            "StrengthClass": info["concrete"], "ReinforcementStrengthClass": info["steel"],
            "ConcreteCover": float(info.get("cover", ec2.COVER)) * u})
        by_role = {st.role: st for st in sets}
        kind = info["kind"]
        if kind == "beam" and "stirrups" in by_role:
            pset = api.pset.add_pset(self.file, product=member, name="Pset_ReinforcementBarPitchOfBeam")
            api.pset.edit_pset(self.file, pset=pset, properties={"StirrupBarPitch": by_role["stirrups"].spacing * u})
        elif kind == "column" and "ties" in by_role:
            pset = api.pset.add_pset(self.file, product=member, name="Pset_ReinforcementBarPitchOfColumn")
            api.pset.edit_pset(self.file, pset=pset, properties={"HoopBarPitch": by_role["ties"].spacing * u})
        elif kind == "footing" and "mesh_x" in by_role and "mesh_y" in by_role:
            pset = api.pset.add_pset(self.file, product=member, name="Pset_ReinforcementBarCountOfIndependentFooting")
            api.pset.edit_pset(self.file, pset=pset, properties={
                "XDirectionLowerBarCount": len(by_role["mesh_x"].bars),
                "YDirectionLowerBarCount": len(by_role["mesh_y"].bars)})

    def _ensure_mass_unit(self):
        """The project's mass unit (kg), for the bars' weights — added the first time."""
        assignment = next(iter(self.file.by_type("IfcUnitAssignment")), None)
        if assignment is None:
            return
        if any(getattr(unit, "UnitType", None) == "MASSUNIT" for unit in assignment.Units):
            return
        unit = api.unit.add_si_unit(self.file, unit_type="MASSUNIT", prefix="KILO")
        assignment.Units = list(assignment.Units) + [unit]

    def number_rebars(self):
        """The positions numbered over the project: the bars of one diameter, shape and length one position — the
        members by storey and name, their sets in order (bottom, top, stirrups…)."""
        levels = {g: z for g, _n, z in self.storeys()}
        items = []
        for e in self.file.by_type("IfcReinforcingBar"):
            p = self._params(e)
            host = self.by_guid(p.get("Armadura") or "")
            if host is None:
                continue
            common = ifcopenshell.util.element.get_psets(e).get("Pset_ReinforcingBarCommon", {})
            key = (round(float(e.NominalDiameter or 0.0), 3), common.get("BendingShapeCode", ""),
                   round(float(e.BarLength or 0.0) * self.unit_scale, 2), p.get("Dobragem", ""))
            items.append(((levels.get(self.storey_of(host.GlobalId), 0.0), HOST_ORDER.get(host.is_a(), 9),
                           _natural(host.Name or ""), ROLE_ORDER.get(p.get("Funcao"), 9)), key, e, common))
        marks = {}
        for _order, key, e, common in sorted(items, key=lambda i: i[0]):
            mark = marks.setdefault(key, str(len(marks) + 1))
            e.Tag = mark
            pset = self.file.by_id(common["id"]) if common.get("id") else None
            if pset is not None:
                api.pset.edit_pset(self.file, pset=pset, properties={"Reference": mark})

    def rebar_bars(self, guid):
        """The centrelines of an IfcReinforcingBar's bars (program coordinates, m): [(N, 3)] — those its body sweeps
        along polylines (any program's)."""
        e = self.by_guid(guid)
        if e is None or not e.Representation:
            return []
        m = self._placement_si(e)
        out = []
        for rep in e.Representation.Representations:
            if rep.RepresentationIdentifier != "Body":
                continue
            for item in rep.Items:
                if item.is_a("IfcSweptDiskSolid") and item.Directrix.is_a("IfcPolyline"):
                    pts = np.array([tuple(p.Coordinates) + (0.0,) * (3 - len(p.Coordinates))
                                    for p in item.Directrix.Points], dtype=float) * self.unit_scale
                    out.append(pts @ m[:3, :3].T + m[:3, 3])
        return out

    # ------------------------------------------------------------ (0.522) welded meshes drawn by hand

    def meshes_of(self, hosts=None):
        """{slab GlobalId: [the GlobalIds of its IfcReinforcingMeshes]} (hosts None: all)."""
        wanted, out = (set(hosts) if hosts is not None else None), {}
        for e in self.file.by_type("IfcReinforcingMesh"):
            host = self._params(e).get("Armadura")
            if host and (wanted is None or host in wanted):
                out.setdefault(host, []).append(e.GlobalId)
        return out

    def mesh_of(self, host):
        """The core.rebar_mesh.Mesh on a slab, or None."""
        from ..core import rebar_mesh as rm
        for g in self.meshes_of([host]).get(host, ()):
            text = self._params(self.by_guid(g)).get("Malha")
            if text:
                return rm.Mesh.from_stored(json.loads(text))
        return None

    def remove_meshes(self, hosts):
        for guids in self.meshes_of(hosts).values():
            for g in guids:
                e = self.by_guid(g)
                if e is not None:
                    api.root.remove_product(self.file, product=e)

    def write_meshes(self, hosts, mesh, lang="pt"):
        """A welded mesh (core.rebar_mesh.Mesh) on each of these slabs, the one each had replaced: one
        IfcReinforcingMesh per face, its wires IfcSweptDiskSolids. Returns the GlobalIds made."""
        self.remove_meshes(hosts)
        made = []
        for host in hosts:
            made += self._lay_mesh(host, mesh, lang)
        return made

    def _lay_mesh(self, host, mesh, lang="pt"):
        from ..core import rebar_mesh as rm
        f, u = self.file, 1.0 / self.unit_scale
        member = self.by_guid(host)
        s = self.slab_outline(host) if member is not None else None
        if s is None:
            return []
        laid = rm.wires(mesh, s["outline"], float(s["top"]), float(s["thickness"]))
        if not laid:
            return []
        self._ensure_mass_unit()
        material = self._material("a500", lang)
        d = mesh.diameter / 1000.0
        sheet_n = rm.sheets(mesh, s["outline"])
        made = []
        for face, (along, across) in laid.items():
            bars = along + across
            if not bars:
                continue
            label = {"bottom": ("malha inferior", "bottom mesh"), "top": ("malha superior", "top mesh")}[face]
            e = api.root.create_entity(f, ifc_class="IfcReinforcingMesh",
                                       name="{} — {} {}".format(member.Name or "", label[0 if lang == "pt" else 1],
                                                                mesh.name("," if lang == "pt" else ".")))
            for attr, value in (("MeshLength", rm.SHEET[0] * u), ("MeshWidth", rm.SHEET[1] * u),
                                ("LongitudinalBarNominalDiameter", d * u), ("TransverseBarNominalDiameter", d * u),
                                ("LongitudinalBarCrossSectionArea", ec2.bar_area(mesh.diameter) * u * u),
                                ("TransverseBarCrossSectionArea", ec2.bar_area(mesh.diameter) * u * u),
                                ("LongitudinalBarSpacing", mesh.spacing * u), ("TransverseBarSpacing", mesh.spacing * u),
                                ("SteelGrade", "A500 EL")):
                try:
                    setattr(e, attr, value)
                except (AttributeError, TypeError):     # (an older schema without it)
                    pass
            first = np.asarray(bars[0][0], dtype=float)
            m = np.eye(4)
            m[:3, 3] = first
            self._place(e, m)
            items = [f.createIfcSweptDiskSolid(f.createIfcPolyline(
                [f.createIfcCartesianPoint(tuple(float(c) for c in (np.asarray(p, dtype=float) - first) * u))
                 for p in bar]), d / 2.0 * u, None, None, None) for bar in bars]
            api.geometry.assign_representation(f, product=e, representation=f.createIfcShapeRepresentation(
                self.body, self.body.ContextIdentifier, "AdvancedSweptSolid", items))
            api.material.assign_material(f, products=[e], type="IfcMaterial", material=material)
            length = sum(rb.BarSet.length_of(b) for b in bars)
            self._set_qto(e, "Qto_ReinforcingElementBaseQuantities",
                          {"Count": sheet_n, "Length": round(length * u, 3),
                           "Weight": round(sheet_n * rm.SHEET[0] * rm.SHEET[1] * mesh.mass_per_m2(), 2)})
            self._set_params(e, {"Elemento": "mesh", "Armadura": host, "Funcao": face,
                                 "Malha": json.dumps(mesh.stored())})
            api.aggregate.assign_object(f, products=[e], relating_object=member)
            made.append(e.GlobalId)
        return made

    def follow_meshes(self, changed):
        """The meshes of the slabs among `changed` laid out again on their new outline."""
        meshes = self.file.by_type("IfcReinforcingMesh")
        if not changed or not meshes:
            return []
        from ..core import rebar_mesh as rm
        wanted = set(changed)
        again = {}
        for e in meshes:
            p = self._params(e)
            if p.get("Armadura") in wanted and p.get("Malha"):
                again.setdefault(p["Armadura"], rm.Mesh.from_stored(json.loads(p["Malha"])))
        made = []
        for host, mesh in again.items():
            self.remove_meshes([host])
            if self.by_guid(host) is not None:
                made += self._lay_mesh(host, mesh)
        return made

    def mesh_rows(self):
        """[{guid, host, host_name, name, face, diameter mm, spacing m, sheets, weight kg}] of the welded meshes."""
        out = []
        for e in self.file.by_type("IfcReinforcingMesh"):
            p = self._params(e)
            qto = ifcopenshell.util.element.get_psets(e).get("Qto_ReinforcingElementBaseQuantities", {})
            host = self.by_guid(p.get("Armadura") or "")
            stored = json.loads(p["Malha"]) if p.get("Malha") else {}
            diameter = float(e.LongitudinalBarNominalDiameter or 0.0) * self.unit_scale * 1000.0 \
                if hasattr(e, "LongitudinalBarNominalDiameter") else float(stored.get("diameter", 0))
            spacing = float(e.LongitudinalBarSpacing or 0.0) * self.unit_scale \
                if hasattr(e, "LongitudinalBarSpacing") else float(stored.get("spacing", 0.0))
            out.append({"guid": e.GlobalId, "host": host.GlobalId if host else None,
                        "host_name": (host.Name if host else "") or "", "name": e.Name or "",
                        "face": p.get("Funcao") or "", "diameter": round(diameter), "spacing": spacing,
                        "sheets": int(qto.get("Count") or 0), "weight": float(qto.get("Weight") or 0.0)})
        return sorted(out, key=lambda r: (_natural(r["host_name"]), r["face"]))

    # ------------------------------------------------------------ the bar schedule

    def rebar_rows(self):
        """[{mark, host, host_name, role, diameter (mm), count, length (m, each), shape, spacing (m), weight (kg)}] of
        every IfcReinforcingBar (made by this program or not), by position."""
        out = []
        for e in self.file.by_type("IfcReinforcingBar"):
            psets = ifcopenshell.util.element.get_psets(e)
            p = self._params(e)
            common = psets.get("Pset_ReinforcingBarCommon", {})
            qto = psets.get("Qto_ReinforcingElementBaseQuantities", {})
            host = self.by_guid(p.get("Armadura") or "")
            diameter = float(e.NominalDiameter or common.get("NominalDiameter") or 0.0) * self.unit_scale * 1000.0
            length = float(e.BarLength or common.get("BarLength") or 0.0) * self.unit_scale
            count = int(qto.get("Count") or 1)
            weight = qto.get("Weight")
            if weight is None:
                weight = count * length * ec2.bar_mass(diameter)
            out.append({"mark": e.Tag or "", "guid": e.GlobalId, "host": host.GlobalId if host else None,
                        "host_name": (host.Name if host else e.Name) or "", "role": p.get("Funcao") or "",
                        "diameter": round(diameter), "count": count, "length": length,
                        "shape": common.get("BendingShapeCode") or "", "bends": p.get("Dobragem") or "",
                        "spacing": float(common.get("BarSpacing") or 0.0) * self.unit_scale, "weight": float(weight)})

        def order(row):
            try:
                return (0, int(row["mark"]), row["host_name"])
            except ValueError:
                return (1, row["mark"], row["host_name"])
        return sorted(out, key=order)
