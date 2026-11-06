"""A wall's light frame in the IFC (0.437, the addon's «Steel Frame / Wood Frame»), mixed into IfcModel: an
IfcElementAssembly (USERDEFINED «Estrutura leve») aggregating its pieces (core/wall_framing), IfcMember each — the
plates PLATE, the studs, jambs and cripples STUD, the headers, sills and blocking USERDEFINED («Verga», «Peitoril»,
«Travamento») —, each a closed IfcTriangulatedFaceSet (a box) inside the wall's core, of galvanised steel or wood. The
wall itself stays as it is (its layers: the boards, the insulation, the frame's zone); its frame is made again
whenever it changes — longer, higher, a door or window put in or moved (follow_framing).

ArqSynth_Parametros of the assembly: Elemento "framing", Parede (the wall's GlobalId), Estrutura (its settings,
JSON: kind, spacing, blocking); of the wall: Estrutura (the assembly's GlobalId)."""

import json

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import wall_framing as core_framing
from .carpentry import _triangles
from .edit import EditRefused

api = ifcopenshell.api
KIND = {"plate": ("PLATE", None), "stud": ("STUD", None), "jamb": ("STUD", None), "cripple": ("STUD", None),
        "header": ("USERDEFINED", "Verga"), "sill": ("USERDEFINED", "Peitoril"),
        "blocking": ("USERDEFINED", "Travamento")}
NAMES = {"plate": ("Guia", "Plate"), "stud": ("Montante", "Stud"), "jamb": ("Ombreira", "Jamb stud"),
         "cripple": ("Montante curto", "Cripple stud"), "header": ("Verga", "Header"), "sill": ("Peitoril", "Sill"),
         "blocking": ("Travamento", "Blocking")}
MATERIAL = {"steel": "aco", "wood": "madeira"}


def settings_text(kind, spacing, blocking):
    return json.dumps({"tipo": kind, "espacamento": float(spacing), "travamentos": int(blocking)})


def settings_from(text):
    try:
        data = json.loads(text or "{}")
    except ValueError:
        data = {}
    kind = data.get("tipo") if data.get("tipo") in core_framing.KINDS else "steel"
    d = core_framing.DEFAULTS[kind]
    return kind, float(data.get("espacamento") or d["spacing"]), int(data.get("travamentos", d["blocking"]))


class WallFramingMixin:
    def framing_of(self, wall_guid):
        """The wall's frame (IfcElementAssembly) — its own: one that names another wall (a copy's) is not —, or None."""
        wall = self.by_guid(wall_guid) if wall_guid else None
        found = self._params(wall).get("Estrutura") if wall is not None else None
        assembly = self.by_guid(found) if found else None
        if assembly is None or self._params(assembly).get("Parede") != wall_guid:
            return None
        return assembly

    def framing_settings(self, wall_guid):
        """(kind, spacing, blocking) of the wall's frame — those it has, or those its copy's names (a copy's)."""
        wall = self.by_guid(wall_guid)
        found = self._params(wall).get("Estrutura") if wall is not None else None
        assembly = self.by_guid(found) if found else None
        return settings_from(self._params(assembly).get("Estrutura")) if assembly is not None else None

    def _wall_core(self, guid, thickness):
        """(y0, y1) the core of a wall across it, in its frame: the layers of its strongest function (its type's
        «Estrutura»), else its thickest; all of it when it has no layers."""
        m = self._placement_si(self.by_guid(guid))
        y = m[:3, 1] / np.linalg.norm(m[:3, 1])
        origin = float(y @ m[:3, 3])
        spans = []
        for _hatch, n, d0, d1 in self.layers([guid], single=True).get(guid, ()):
            if float(np.asarray(n, dtype=float) @ y) >= 0:
                spans.append((d0 - origin, d1 - origin))
            else:
                spans.append((-d1 - origin, -d0 - origin))
        if not spans:
            return -thickness / 2, thickness / 2
        given = list(self.layer_strengths([guid]).get(guid) or ())
        if len(given) == len(spans) and any(v is not None for v in given):
            best = min(v for v in given if v is not None)
            chosen = [s for s, v in zip(spans, given) if v == best]
        else:
            chosen = [max(spans, key=lambda s: s[1] - s[0])]
        return min(s[0] for s in chosen), max(s[1] for s in chosen)

    def _wall_openings_box(self, wall, m):
        """[(x0, x1, z0, z1)] of the wall's openings (not its reveals) in its frame."""
        out = []
        for opening, lo, hi in self._openings_local(wall, m):
            if getattr(opening, "PredefinedType", None) == "RECESS":
                continue
            out.append((float(lo[0]), float(hi[0]), float(lo[2]), float(hi[2])))
        return out

    def set_wall_framing(self, guid, kind=None, spacing=None, blocking=None, lang="pt"):
        """(0.437) A straight wall's light frame made (or made again: what is not given, as it has it, else the
        kind's): steel or wood, its studs `spacing` apart, `blocking` rows. Returns the assembly."""
        wall, _ = self._require(guid, "wall")
        had = self.framing_settings(guid)
        k0, s0, b0 = had if had is not None else (kind or "steel", None, None)
        kind = kind if kind in core_framing.KINDS else k0
        d = core_framing.DEFAULTS[kind]
        if kind != k0 and spacing is None:
            spacing = d["spacing"]                   # (another kind: its own spacing)
        spacing = float(spacing if spacing is not None else (s0 if s0 is not None else d["spacing"]))
        blocking = int(blocking if blocking is not None else (b0 if b0 is not None else d["blocking"]))
        if not 0.10 <= spacing <= 1.50 or not 0 <= blocking <= core_framing.MAX_BLOCKING:
            raise EditRefused("framing_bad")
        self.remove_wall_framing(guid)
        length, height, thickness = self.wall_params(guid)
        m = self._placement_si(wall)
        y0, y1 = self._wall_core(guid, thickness)
        pieces = core_framing.layout(length, height, y0, y1, self._wall_openings_box(wall, m), kind, spacing,
                                     blocking)
        if not pieces:
            raise EditRefused("framing_small")
        assembly = self._make_framing(wall, pieces, kind, lang)
        self._set_params(assembly, {"Parede": guid, "Estrutura": settings_text(kind, spacing, blocking)})
        self._set_params(wall, {"Estrutura": assembly.GlobalId})
        return assembly

    def remove_wall_framing(self, guid):
        """(0.437) A wall's frame taken away. False if it had none."""
        assembly = self.framing_of(guid)
        if assembly is None:
            return False
        for rel in list(assembly.IsDecomposedBy or ()):
            for part in list(rel.RelatedObjects):
                api.root.remove_product(self.file, product=part)
        api.root.remove_product(self.file, product=assembly)
        wall = self.by_guid(guid)
        if wall is not None:
            self._set_params(wall, {"Estrutura": None})
        return True

    def drop_framing(self, guid):
        """A wall being removed: its frame with it."""
        assembly = self.framing_of(guid)
        if assembly is None:
            return
        for rel in list(assembly.IsDecomposedBy or ()):
            for part in list(rel.RelatedObjects):
                api.root.remove_product(self.file, product=part)
        api.root.remove_product(self.file, product=assembly)

    def framing_summary(self, guid):
        """{role: (count, length m)} of a wall's frame — None when it has none."""
        assembly = self.framing_of(guid)
        if assembly is None:
            return None
        by_name = {name: role for role, names in NAMES.items() for name in names}
        s = self.unit_scale
        out = {}
        for rel in assembly.IsDecomposedBy or ():
            for part in rel.RelatedObjects:
                role = by_name.get((part.Name or "").rsplit(" ", 1)[0])
                if role is None:
                    continue
                q = ifcopenshell.util.element.get_psets(part).get("Qto_MemberBaseQuantities", {})
                n, total = out.get(role, (0, 0.0))
                out[role] = (n + 1, total + float(q.get("Length") or 0.0) * s)
        return {r: out[r] for r in core_framing.ROLES if r in out}

    def follow_framing(self, changed):
        """The frames of the walls changed (longer, higher, an opening put in or moved…) made again; a wall copied
        (its Estrutura names its original's frame) gets its own. Returns what it made."""
        out = []
        made = set(getattr(self, "made", None) or ())
        for g in list(dict.fromkeys(changed)):
            e = self.by_guid(g)
            if e is None or not e.is_a("IfcWall") or not self._params(e).get("Estrutura"):
                continue
            own = self.framing_of(g)
            if own is not None and own.GlobalId in made:      # (made in this very step: as asked)
                continue
            settings = self.framing_settings(g)
            if settings is None:                          # (its frame gone some other way)
                self._set_params(e, {"Estrutura": None})
                continue
            if own is None:                               # (a copy: not its original's frame taken away)
                self._set_params(e, {"Estrutura": None})
            try:
                assembly = self.set_wall_framing(g, *settings)
            except EditRefused:
                self.remove_wall_framing(g)
                continue
            out += [assembly.GlobalId] + [p.GlobalId for rel in assembly.IsDecomposedBy or ()
                                          for p in rel.RelatedObjects]
        return out

    def _make_framing(self, wall, pieces, kind, lang):
        f, u = self.file, 1.0 / self.unit_scale
        m = self._placement_si(wall)
        storey = self.storey_of(wall.GlobalId)
        label = "Estrutura leve" if lang == "pt" else "Light frame"
        assembly = api.root.create_entity(f, ifc_class="IfcElementAssembly", predefined_type="USERDEFINED",
                                          name="{} — {}".format(label, wall.Name or ""))
        assembly.ObjectType = "Estrutura leve"
        self._place(assembly, m)
        if storey:
            api.spatial.assign_container(f, products=[assembly], relating_structure=self.storey(storey))
        self._mark(assembly, "framing")
        members, counts = [], {}
        for piece in pieces:
            predefined, object_type = KIND[piece.role]
            counts[piece.role] = counts.get(piece.role, 0) + 1
            member = api.root.create_entity(f, ifc_class="IfcMember", predefined_type=predefined,
                                            name="{} {}".format(NAMES[piece.role][0 if lang == "pt" else 1],
                                                                counts[piece.role]))
            if object_type:
                member.ObjectType = object_type
            self._place(member, m)
            (x0, y0, z0), (x1, y1, z1) = piece.lo, piece.hi
            corners = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                       (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
            coords = f.createIfcCartesianPointList3D([tuple(float(c * u) for c in corner) for corner in corners])
            body = f.createIfcTriangulatedFaceSet(coords, None, True, _triangles(corners), None)
            api.geometry.assign_representation(f, product=member, representation=f.createIfcShapeRepresentation(
                self.body, self.body.ContextIdentifier, "Tessellation", [body]))
            self._set_qto(member, "Qto_MemberBaseQuantities", {"Length": piece.length * u, "NetVolume": piece.volume})
            members.append(member)
        if members:
            api.aggregate.assign_object(f, products=members, relating_object=assembly)
            api.material.assign_material(f, products=members, type="IfcMaterial",
                                         material=self._material(MATERIAL[kind], lang))
        return assembly
