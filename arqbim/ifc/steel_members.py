"""(0.495) Steel pieces between two points, mixed into IfcModel — the «Peça metálica» tool, as Tekla's and Revit's
structural framing: any steel section of the catalogue (core/steel) along a line in space — level, sloped or upright —
as a beam (IfcBeam), a column (IfcColumn), a brace (IfcMember BRACE), a purlin (IfcMember PURLIN) or another member
(IfcMember MEMBER); its section on the line by one of IFC's nine cardinal points (top middle by default: a beam's top
on the line drawn, as the Beam tool's) and turned about the line.

Its placement is the line's own frame (classify.segment_placement: Z along the line, X level across it), turned about
Z by its rotation; its body its type's profile extruded along Z, its length, by its cardinal point (IfcOpenShell's
add_profile_representation): so the line's start is the placement's origin and its end the origin + Z × the length —
moving or turning the piece moves its line.

ArqSynth_Parametros: Elemento "steel_member", Funcao (FUNCTIONS' key), Insercao (1–9), Rotacao (degrees)."""

import math

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import classify
from . import catalog

api = ifcopenshell.api

# function: (IFC class, its type's kind, PredefinedType, quantities, common set)
FUNCTIONS = {"beam": ("IfcBeam", "beam", "BEAM", "Qto_BeamBaseQuantities", "Pset_BeamCommon"),
             "column": ("IfcColumn", "column", "COLUMN", "Qto_ColumnBaseQuantities", "Pset_ColumnCommon"),
             "brace": ("IfcMember", "member", "BRACE", "Qto_MemberBaseQuantities", "Pset_MemberCommon"),
             "purlin": ("IfcMember", "member", "PURLIN", "Qto_MemberBaseQuantities", "Pset_MemberCommon"),
             "member": ("IfcMember", "member", "MEMBER", "Qto_MemberBaseQuantities", "Pset_MemberCommon")}
CARDINALS = tuple(range(1, 10))   # IFC's: 1 bottom left … 5 the middle … 8 top middle, 9 top right (seen from the start)
DEFAULT_CARDINAL = {"beam": 8, "purlin": 8, "column": 5, "brace": 5, "member": 5}


def function_spec(spec, function):
    """The type a steel section is drawn with as this function: the type itself when it is of that kind (a beam
    type as a beam), else one named for the function («Contraventamento L 80×8 — S275»), an IfcMemberType of its
    PredefinedType for a brace, a purlin, a member."""
    from ..core import steel
    _cls, kind, predefined, _q, _p = FUNCTIONS[function]
    special = predefined if kind == "member" and predefined != "MEMBER" else None
    if spec.kind == kind and (kind != "member" or spec.predefined == special):
        return spec
    grade = steel.grade_of(spec.material) or "S275"
    key = "aco_{}_{}_{}".format(function, spec.section, grade).lower()
    found = catalog.BY_KEY.get(key)
    if found is not None:
        return found
    named = catalog.steel_spec(spec, spec.section, grade)
    from dataclasses import replace
    return replace(named, key=key, kind=kind, predefined=special,
                   name_pt=catalog.steel_name(function, spec.section, grade, "pt"),
                   name_en=catalog.steel_name(function, spec.section, grade, "en"))


def frame(start, end, rotation=0.0):
    """(placement 4×4, length) of a piece from start to end, its section turned `rotation` degrees about its line."""
    m, length = classify.segment_placement(np.asarray(start, dtype=float), np.asarray(end, dtype=float))
    a = math.radians(float(rotation))
    turn = np.array(((math.cos(a), -math.sin(a), 0.0), (math.sin(a), math.cos(a), 0.0), (0.0, 0.0, 1.0)))
    m[:3, :3] = m[:3, :3] @ turn
    return m, length


GAP = 0.010                        # m: a steel beam's end short of the column it reaches (Tekla's clearance)


def _reach(column_section, half, x_dir, u, beam_width):
    """How far from a column's middle a beam coming along u (2D, unit) stops: an I column's flange face — or its web,
    between the flanges, when the beam fits between them —, a tube's or a concrete column's side; then the gap (a
    steel column's)."""
    from ..core import steel
    x = np.asarray(x_dir, dtype=float)
    y = np.array((-x[1], x[0]))
    ux, uy = abs(float(u @ x)), abs(float(u @ y))
    a, b = half                                         # (half its size along its own x and y)
    sec = steel.get(column_section) if column_section else None
    gap = GAP if sec is not None else 0.0
    if sec is not None and sec.family in steel.I_FAMILIES:
        clear = (sec.h - 2.0 * sec.tf - 2.0 * sec.r) / 1000.0
        if ux > uy and beam_width <= clear:            # (onto its web, between its flanges)
            return sec.tw / 2000.0 / ux + gap
    # (its side: the nearer of the two faces the line crosses)
    return min(a / ux if ux > 1e-9 else np.inf, b / uy if uy > 1e-9 else np.inf) + gap


class SteelMemberMixin:
    def beam_to_faces(self, start, end, top, spec):
        """(0.495) A steel beam's ends brought back to the faces of the columns they are in (seen from above, at the
        beam's height): (start, end)."""
        start, end = np.array(start, dtype=float), np.array(end, dtype=float)
        d = (end - start)[:2]
        n = float(np.linalg.norm(d))
        if n < 1e-9:
            return start, end
        u = d / n
        width, depth = spec.profile
        out = [start, end]
        for k, (p, sign) in enumerate(((start, 1.0), (end, -1.0))):
            for col in self.file.by_type("IfcColumn"):
                try:
                    centre, x_dir, half, base, col_top = self.column_box(col.GlobalId)
                except Exception:                       # (a column of another program, no section of ours)
                    continue
                if top - depth > col_top + 1e-6 or top < base - 1e-6:
                    continue
                rel = np.asarray(p[:2], dtype=float) - centre
                x = np.asarray(x_dir, dtype=float)
                y = np.array((-x[1], x[0]))
                if abs(float(rel @ x)) > half[0] + 1e-6 or abs(float(rel @ y)) > half[1] + 1e-6:
                    continue
                reach = _reach(self.steel_section(col.GlobalId), half, x, u, width)
                along = float(rel @ (u * sign))         # (where the end is, from the middle, out along the beam)
                moved = np.array(p, dtype=float)
                moved[:2] = p[:2] + u * sign * (reach - along)
                out[k] = moved
                break
        return out[0], out[1]


    def add_steel_member(self, spec, start, end, name, lang="pt", storey=None, function="beam", cardinal=None,
                         rotation=0.0):
        """A steel piece of the section of `spec` (a steel type) from `start` to `end` (m), as `function`, by its
        cardinal point (None: the function's), turned `rotation` degrees about its line; in `storey` (GlobalId) or
        the one its lower end is in. Returns the element."""
        f = self.file
        if not spec.section:
            raise ValueError("not a steel section: {}".format(spec.key))
        cls, _kind, predefined, _qto, common = FUNCTIONS[function]
        type_spec = function_spec(spec, function)
        type_ = self.ensure_type(type_spec, lang)
        element = api.root.create_entity(f, ifc_class=cls, name=name, predefined_type=predefined)
        api.type.assign_type(f, related_objects=[element], relating_type=type_)
        cardinal = int(cardinal or DEFAULT_CARDINAL[function])
        self._steel_body(element, start, end, cardinal, rotation, function)
        low = min(float(start[2]), float(end[2]))
        container = self.storey(storey) if storey is not None else self.storey_at(low)
        api.spatial.assign_container(f, products=[element], relating_structure=container)
        pset = api.pset.add_pset(f, product=element, name=common)
        api.pset.edit_pset(f, pset=pset, properties={"IsExternal": False, "LoadBearing": True})
        self._mark(element, "steel_member")
        self._set_params(element, {"Funcao": function, "Insercao": cardinal, "Rotacao": float(rotation)})
        return element

    def _steel_body(self, element, start, end, cardinal, rotation, function):
        """The piece's placement (its line's frame, turned) and body (its type's section along it)."""
        m, length = frame(start, end, rotation)
        if length < 1e-6:
            raise ValueError("a piece needs two points apart")
        profile = ifcopenshell.util.element.get_material(ifcopenshell.util.element.get_type(element)) \
            .MaterialProfiles[0].Profile
        self._set_profile_body(element, profile, length, FUNCTIONS[function][3], cardinal=cardinal)
        self._place(element, m)

    def steel_member_params(self, guid):
        """{start, end (m, the model's), length, function, cardinal, rotation, section} of a steel piece."""
        e = self.by_guid(guid)
        m = self.placement(guid)
        p = self._params(e)
        length = float(self.steel_length(e))
        z = m[:3, 2] / np.linalg.norm(m[:3, 2])
        start = m[:3, 3].copy()
        return {"start": start, "end": start + z * length, "length": length, "function": p.get("Funcao") or "beam",
                "cardinal": int(p.get("Insercao") or 5), "rotation": float(p.get("Rotacao") or 0.0),
                "section": self.steel_section(guid)}

    def steel_length(self, e):
        """A piece's length (m): its extrusion's depth."""
        for rep in e.Representation.Representations if e.Representation else ():
            for item in rep.Items:
                solid = item
                while solid.is_a("IfcBooleanResult"):
                    solid = solid.FirstOperand
                if solid.is_a("IfcExtrudedAreaSolid"):
                    return float(solid.Depth) * self.unit_scale
        return 0.0

    def set_steel_member(self, guid, spec=None, start=None, end=None, cardinal=None, rotation=None, lang="pt"):
        """A steel piece changed: another section (spec), other ends, cardinal point or rotation — made again."""
        e = self.by_guid(guid)
        p = self.steel_member_params(guid)
        function = p["function"] if p["function"] in FUNCTIONS else "beam"
        if spec is not None and spec.section:
            type_ = self.ensure_type(function_spec(spec, function), lang)
            api.type.assign_type(self.file, related_objects=[e], relating_type=type_)
        start = p["start"] if start is None else np.asarray(start, dtype=float)
        end = p["end"] if end is None else np.asarray(end, dtype=float)
        cardinal = p["cardinal"] if cardinal is None else int(cardinal)
        rotation = p["rotation"] if rotation is None else float(rotation)
        self._steel_body(e, start, end, cardinal, rotation, function)
        self._set_params(e, {"Insercao": cardinal, "Rotacao": rotation})
