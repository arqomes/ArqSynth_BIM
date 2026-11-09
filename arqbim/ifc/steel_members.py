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

import json
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


def _closest(p, d, q, e):
    """The nearest points of two lines (p + s d, q + t e; d, e unit), or None when they are parallel."""
    w = p - q
    b = float(d @ e)
    denom = 1.0 - b * b
    if denom < 1e-9:
        return None
    s = (b * float(e @ w) - float(d @ w)) / denom
    t = (float(e @ w) - b * float(d @ w)) / denom
    return p + d * s, q + e * t


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


COPE_CLEAR = 0.005                 # m: a cope this much past the girder's flange (its root radius) and its edge (×2)


class SteelMemberMixin:
    def beam_onto_beams(self, start, end, top, spec, skip=()):
        """(0.496) A steel beam's ends that lie on a steel girder (seen from above, at heights that overlap): brought
        back to its web (+ the gap) and coped where its flanges would go through the girder's — its top (and its
        bottom) cut away as far as the girder's flange and root radius, as long as the flange reaches. Returns (start,
        end, copes — as set_steel_cuts keeps them, in the beam's own frame)."""
        from ..core import steel
        start, end = np.array(start, dtype=float), np.array(end, dtype=float)
        d = (end - start)[:2]
        n = float(np.linalg.norm(d))
        sec = steel.get(spec.section) if spec.section else None
        if n < 1e-9 or sec is None:
            return start, end, []
        u = d / n
        width, depth = spec.profile
        bottom = top - depth
        out, copes = [start, end], []
        for k, p in enumerate((start, end)):
            for g in self.file.by_type("IfcBeam"):
                if g.GlobalId in skip or self.kind_of(g.GlobalId) != "beam":
                    continue
                gsec = steel.get(self.steel_section(g.GlobalId) or "")
                if gsec is None or gsec.family not in steel.I_FAMILIES + steel.U_FAMILIES:
                    continue
                try:
                    a, b, g_top, _gw, g_depth = self.beam_params(g.GlobalId)
                except Exception:
                    continue
                a, b = np.asarray(a, dtype=float)[:2], np.asarray(b, dtype=float)[:2]
                axis = b - a
                span = float(np.linalg.norm(axis))
                if span < 1e-9:
                    continue
                axis /= span
                normal = np.array((-axis[1], axis[0]))
                rel = np.asarray(p[:2], dtype=float) - a
                along, across = float(rel @ axis), float(rel @ normal)
                if not -1e-6 <= along <= span + 1e-6 or abs(across) > gsec.b / 2000.0 + 1e-6:
                    continue
                if top <= g_top - g_depth + 1e-6 or bottom >= g_top - 1e-6:
                    continue
                inward = u if k == 0 else -u               # (from this end into the beam)
                c = float(inward @ normal)
                if abs(c) < 0.2:                           # (along the girder, not onto it)
                    continue
                side = 1.0 if c > 0 else -1.0               # (the girder's side the beam is on)
                face = side * (gsec.tw / 2000.0 + GAP)
                moved = np.array(p, dtype=float)
                moved[:2] = p[:2] + inward * ((face - across) / c)
                out[k] = moved
                flange = (gsec.b - gsec.tw) / 2000.0 - GAP + 2 * COPE_CLEAR          # (how far back to cope)
                reach = flange / abs(c)
                zone = gsec.tf / 1000.0 + gsec.r / 1000.0 + COPE_CLEAR
                half_w = width / 2.0 + 0.001
                for low, high in ((g_top - zone, top + 0.001), (bottom - 0.001, g_top - g_depth + zone)):
                    if high - low < 1e-6 or low > top or high < bottom:
                        continue
                    y0, y1 = max(low, bottom - 0.001) - (top - depth / 2.0), min(high, top + 0.001) - (top - depth / 2.0)
                    z0, z1 = (-0.001, reach) if k == 0 else (-reach, 0.001)
                    copes.append({"end": k, "lo": [-half_w, y0, z0], "hi": [half_w, y1, z1]})
                break
        return out[0], out[1], copes

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
        """A piece's length (m): its extrusion's depth, less what it is drawn out past its ends to be cut (0.496)."""
        e0, e1 = self.steel_cuts(e)[2]
        for rep in e.Representation.Representations if e.Representation else ():
            for item in rep.Items:
                solid = item
                while solid.is_a("IfcBooleanResult"):
                    solid = solid.FirstOperand
                if solid.is_a("IfcExtrudedAreaSolid"):
                    return float(solid.Depth) * self.unit_scale - e0 - e1
        return 0.0

    # ------------------------------------------------------------ (0.496) its ends cut

    def steel_cuts(self, e):
        """(cuts, copes, (drawn out at the start, at the end)) of a profiled element — cuts [{"end": 0 | 1, "p": point,
        "n": normal}] (the side the normal points to taken away), copes [{"end", "lo", "hi"}] (boxes taken away) —,
        in its own frame, metres, each from its end: the start's from the start, the end's from the end (z − its
        length), so that they stay with their end when the piece gets longer."""
        p = self._params(e) if e is not None else {}
        try:
            cuts = json.loads(p.get("Cortes") or "[]")
            copes = json.loads(p.get("Recortes") or "[]")
            ext = json.loads(p.get("Prolongar") or "[0, 0]")
        except ValueError:
            return [], [], (0.0, 0.0)
        return cuts, copes, (float(ext[0]), float(ext[1]))

    def set_steel_cuts(self, e, cuts=None, copes=None, ext=None):
        """Its cuts, copes and drawing out kept (None: as they are); its body is made again by whoever calls."""
        values = {}
        if cuts is not None:
            values["Cortes"] = json.dumps(cuts)
        if copes is not None:
            values["Recortes"] = json.dumps(copes)
        if ext is not None:
            values["Prolongar"] = json.dumps([float(ext[0]), float(ext[1])])
        self._set_params(e, values)

    def _apply_cuts(self, element, body, length):
        """A profiled body (its extrusion `length` m long) drawn out past its ends, cut by its planes, its copes taken
        away — as its parameters say (nothing: as it is)."""
        cuts, copes, (e0, e1) = self.steel_cuts(element)
        if not cuts and not copes and not e0 and not e1:
            return
        from ifcopenshell.util.data import Clipping
        f, s = self.file, self.unit_scale
        u = 1.0 / s
        item = body.Items[0]
        if e0 or e1:
            x, y, z = (float(c) for c in item.Position.Location.Coordinates)
            item.Position.Location = f.createIfcCartesianPoint((x, y, z - e0 * u))
            item.Depth = float(item.Depth) + (e0 + e1) * u
        solid = item
        for c in cuts:
            at = np.array(c["p"], dtype=float) + (np.array((0.0, 0.0, length)) if c.get("end") else 0.0)
            solid = Clipping(location=tuple(float(v) for v in at), normal=tuple(float(v) for v in c["n"])) \
                .apply(f, solid, s)
        for box in copes:
            shift = np.array((0.0, 0.0, length)) if box.get("end") else np.zeros(3)
            lo, hi = np.array(box["lo"], dtype=float) + shift, np.array(box["hi"], dtype=float) + shift
            profile = f.createIfcRectangleProfileDef(
                "AREA", None, f.createIfcAxis2Placement2D(f.createIfcCartesianPoint(
                    (float((lo[0] + hi[0]) / 2 * u), float((lo[1] + hi[1]) / 2 * u)))),
                float((hi[0] - lo[0]) * u), float((hi[1] - lo[1]) * u))
            cutter = f.createIfcExtrudedAreaSolid(
                profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, float(lo[2] * u)))),
                f.createIfcDirection((0.0, 0.0, 1.0)), float((hi[2] - lo[2]) * u))
            solid = f.createIfcBooleanResult("DIFFERENCE", solid, cutter)
        body.Items = (solid,)
        if copes:                                          # (IFC's: a body with boxes taken away is a CSG one…)
            body.RepresentationType = "CSG"
        elif cuts:                                         # (…one only cut by planes, a Clipping one)
            body.RepresentationType = "Clipping"

    def section_middle(self, e):
        """Where the middle of its section is in its own frame (x, y, m) — its cardinal point's offset."""
        for rep in e.Representation.Representations if e.Representation else ():
            for item in rep.Items:
                solid = item
                while solid.is_a("IfcBooleanResult"):
                    solid = solid.FirstOperand
                if solid.is_a("IfcExtrudedAreaSolid"):
                    c = solid.Position.Location.Coordinates
                    return float(c[0]) * self.unit_scale, float(c[1]) * self.unit_scale
        return 0.0, 0.0

    def mitre(self, a, b, lang="pt", dry=False):
        """Two steel pieces cut to a mitre where their lines meet (a portal's knee): each line's nearer end brought
        to the meeting point, each piece drawn out past it by twice its section and cut by the plane that halves the
        angle between them. Returns False (and changes nothing) when their lines do not meet (parallel, or more than
        half a metre apart)."""
        pa, pb = self.steel_member_params(a), self.steel_member_params(b)
        ends_a, ends_b = (pa["start"], pa["end"]), (pb["start"], pb["end"])
        ka, kb = min(((i, j) for i in (0, 1) for j in (0, 1)),
                     key=lambda ij: float(np.linalg.norm(ends_a[ij[0]] - ends_b[ij[1]])))
        da = ends_a[ka] - ends_a[1 - ka]
        db = ends_b[kb] - ends_b[1 - kb]
        da, db = da / np.linalg.norm(da), db / np.linalg.norm(db)
        meet = _closest(ends_a[ka], da, ends_b[kb], db)
        if meet is None:
            return False
        ja, jb = meet
        if float(np.linalg.norm(ja - jb)) > 0.5 or float(np.linalg.norm(ja - ends_a[ka])) > 1.0 \
                or float(np.linalg.norm(jb - ends_b[kb])) > 1.0:
            return False
        joint = (ja + jb) / 2.0
        normal = da - db
        if float(np.linalg.norm(normal)) < 1e-9:
            return False
        if dry:                                            # (only whether it can be done)
            return True
        normal /= np.linalg.norm(normal)
        for guid, k, ends, p, n in ((a, ka, ends_a, pa, normal), (b, kb, ends_b, pb, -normal)):
            start, end = (joint, ends[1]) if k == 0 else (ends[0], joint)
            e = self.by_guid(guid)
            w, h = self.steel_box(guid)
            out = 2.0 * max(w, h)
            cuts, copes, ext = self.steel_cuts(e)
            ext = list(ext)
            ext[k] = out
            m, length = frame(start, end, p["rotation"])
            inv = np.linalg.inv(m)
            local = (inv @ np.append(joint, 1.0))[:3]
            local_n = inv[:3, :3] @ n
            if k == 1:
                local = local - np.array((0.0, 0.0, length))
            cuts = [c for c in cuts if c.get("end") != k] + [{"end": k, "p": [float(v) for v in local],
                                                               "n": [float(v) for v in local_n]}]
            self.set_steel_cuts(e, cuts=cuts, ext=ext)
            self.set_steel_member(guid, start=start, end=end, lang=lang)
        return True

    # ------------------------------------------------------------ (0.500) the pieces, their marks

    def steel_pieces(self):
        """Every steel piece — columns, beams and members of a steel section, the plates of the connections —, each
        a dict: guid, prefix (P V CV M E Ch), signature (what makes two pieces the same), mark (its IFC Tag), section
        (as written), grade, cut length (m), kg/m, weight (kg), paint (m²)."""
        import re
        from ..core import steel
        out = []
        for cls in ("IfcColumn", "IfcBeam", "IfcMember"):
            for e in self.file.by_type(cls):
                g = e.GlobalId
                kind = self.kind_of(g)
                if kind not in ("column", "beam", "steel_member"):
                    continue
                name = self.steel_section(g)
                if name is None:
                    continue
                sec = steel.get(name)
                material = ifcopenshell.util.element.get_material(e, should_skip_usage=True)
                matname = material.MaterialProfiles[0].Material.Name if material is not None and \
                    material.is_a("IfcMaterialProfileSet") and material.MaterialProfiles[0].Material else ""
                found = re.search(r"S\d{3}", matname or "")
                grade = found.group(0) if found else ""
                cuts, copes, (e0, e1) = self.steel_cuts(e)
                if kind == "steel_member":
                    length = self.steel_length(e) + e0 + e1
                else:
                    q = ifcopenshell.util.element.get_psets(e).get(
                        "Qto_BeamBaseQuantities" if cls == "IfcBeam" else "Qto_ColumnBaseQuantities", {})
                    length = float(q.get("Length") or 0.0) * self.unit_scale + e0 + e1
                if cls == "IfcColumn":
                    prefix = "P"
                elif cls == "IfcBeam":
                    prefix = "V"
                else:
                    predefined = ifcopenshell.util.element.get_predefined_type(e)
                    prefix = {"BRACE": "CV", "PURLIN": "M"}.get(predefined, "E")
                props = steel.properties(sec.name)
                from ..core import steel_marks
                symmetric = sec.family in steel.I_FAMILIES + ("SHS", "RHS", "CHS")
                shape = steel_marks.shape_signature(cuts, copes, (e0, e1), symmetric)
                holes = steel_marks.holes_signature(self.member_holes(g), length * 1000.0, steel.size(sec)[0])
                out.append({"guid": g, "prefix": prefix, "signature": (sec.name, grade, round(length * 1000.0), shape,
                                                                       holes),
                            "mark": e.Tag or "", "section": steel.display(sec.name), "grade": grade, "length": length,
                            "kg_m": props["mass"], "weight": props["mass"] * length, "paint": props["paint"] * length})
        for e in self.file.by_type("IfcPlate"):
            if self.kind_of(e.GlobalId) != "steel_part":
                continue
            q = ifcopenshell.util.element.get_psets(e).get("Qto_PlateBaseQuantities", {})
            weight = float(q.get("NetWeight") or 0.0)
            label = (e.Name or "").split(" ", 1)[-1] if e.Name else ""
            out.append({"guid": e.GlobalId, "prefix": "Ch", "signature": (e.Name or "", round(weight, 2)),
                        "mark": e.Tag or "", "section": label, "grade": "", "length": 0.0, "kg_m": None,
                        "weight": weight, "paint": 2.0 * float(q.get("GrossArea") or 0.0)})
        return out

    def steel_marks(self, renumber=False):
        """{guid: mark} the steel pieces get (core/steel_marks.assign): kept where they can be; renumber: all anew."""
        from ..core import steel_marks
        pieces = self.steel_pieces()
        return steel_marks.assign([(p["guid"], p["prefix"], p["signature"], "" if renumber else p["mark"])
                                   for p in pieces]), pieces

    def set_steel_marks(self, renumber=False):
        """The marks written on the pieces (their IFC Tag). Returns the GlobalIds whose mark changed."""
        marks, _pieces = self.steel_marks(renumber)
        changed = []
        for g, mark in marks.items():
            e = self.by_guid(g)
            if (e.Tag or "") != mark:
                e.Tag = mark
                changed.append(g)
        return changed

    def steel_system_fit(self, guid):
        """(0.508) A steel beam of a beam system (laid face to face in its bay) brought to the webs of the steel girders
        its ends are on — cut back to them (the gap) and coped (beam_onto_beams) —, its connections made again."""
        from types import SimpleNamespace
        name = self.steel_section(guid)
        if name is None or self.kind_of(guid) != "beam":
            return
        start, end, top, width, depth = self.beam_params(guid)
        spec = SimpleNamespace(section=name, profile=(width, depth))
        a, b, copes = self.beam_onto_beams(start, end, top, spec, skip=(guid,))
        e = self.by_guid(guid)
        self.set_steel_cuts(e, copes=copes)
        if float(np.linalg.norm((a - start)[:2])) > 1e-9 or float(np.linalg.norm((b - end)[:2])) > 1e-9:
            self.set_beam_ends(guid, a, b)
        else:
            self.rebuild_beam(guid)
        for c in self.connections_on([guid]):
            self._build_connection(c)

    def rebuild_beam(self, guid):
        """A beam's body made again as it is (its copes, after they are set)."""
        self.resize_beam(guid)

    def steel_box(self, guid):
        """(width, depth) of a profiled element's section, m."""
        from .edit import profile_size
        e = self.by_guid(guid)
        profile = ifcopenshell.util.element.get_material(e, should_skip_usage=True).MaterialProfiles[0].Profile
        w, d, _a, _p = profile_size(profile)
        return w * self.unit_scale, d * self.unit_scale

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
