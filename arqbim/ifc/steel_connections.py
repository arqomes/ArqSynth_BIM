"""(0.497) Steel connections, mixed into IfcModel — as DetailCraft's (each kept only as its kind, the pieces it joins
and its parameters; its plates, bolts and welds made again from them whenever those pieces change) and Tekla's
components. The first: the column's base plate — a plate under the column's foot, its anchor bolts (washer, nut, the
rod down into the concrete), the column welded all round to it.

In the IFC: an IfcElementAssembly (USERDEFINED «Ligação») aggregating its parts — IfcPlate (its holes in its outline),
IfcMechanicalFastener ANCHORBOLT / BOLT (rod, washer and nut, round and hexagonal extrusions), IfcFastener WELD
(Pset_FastenerWeld: its throat «a», its length «l») — all of the column's grade. ArqSynth_Parametros of the assembly:
Elemento "steel_connection", Ligacao (its kind), Pecas (the GlobalIds it joins, JSON), Parametros (JSON, mm); of each
part: Elemento "steel_part", Ligacao (the assembly's GlobalId).

Checks as EN 1993-1-8 Table 3.3 for the bolts (e ≥ 1,2 d0, p ≥ 2,2 d0), and that the plate is bigger than the column
and its bolts clear of it — warnings only (no strength design: that is the EC3's, later)."""

import json
import math

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from .edit import EditRefused

api = ifcopenshell.api
KINDS = ("base_plate", "end_plate", "fin_plate", "gusset")
NAMES = {"base_plate": ("Chapa de base", "Base plate"), "end_plate": ("Chapa de topo", "End plate"),
         "fin_plate": ("Cutelo", "Fin plate"), "gusset": ("Gousset", "Gusset plate")}
ANGLE_FAMILIES = ("L", "LU")
# (mm) A × B its plate (0: the column's size + 2 × MARGIN), tp its thickness, n its anchor bolts (2, 4, 6, 8), d their
# diameter, e their distance to the plate's edges, proj how far they stand over the plate, embed how deep in the
# concrete, grout under the plate, a the weld's throat
DEFAULTS = {"base_plate": {"A": 0.0, "B": 0.0, "tp": 20.0, "n": 4, "d": 20.0, "e": 50.0, "proj": 80.0, "embed": 400.0,
                           "grout": 30.0, "a": 6.0},
            # (0.498) the beam's end plate, bolted to the column: its width (0: the beam's), how far it goes over and
            # under the beam (flush: 0), rows of two bolts, their pitch and gauge (0: the beam's width − 2 e)
            "end_plate": {"end": 1, "tp": 20.0, "W": 0.0, "top": 0.0, "bottom": 0.0, "rows": 4, "p": 75.0, "g": 0.0,
                          "d": 20.0, "e": 40.0, "a": 6.0},
            # …the fin plate welded to the column, the beam's web bolted to it: its width along the beam, its rows,
            # their pitch, the edges, the bolts' distance from the column
            "fin_plate": {"end": 1, "tp": 10.0, "w": 115.0, "rows": 3, "p": 75.0, "e": 38.0, "eh": 65.0, "d": 20.0,
                          "a": 6.0},
            # (0.503) a brace's end (an angle's leg) bolted to a gusset welded to the column: the plate's thickness,
            # the bolts along the brace (rows), their pitch, the end distance, the brace's end clear of the column
            # (gap), the bolts' gauge from the angle's heel (0: about half its leg), the plate past the leg (edge)
            "gusset": {"end": 1, "tp": 10.0, "rows": 2, "p": 60.0, "e": 35.0, "d": 16.0, "gap": 20.0, "g": 0.0,
                       "edge": 25.0, "a": 5.0}}
LIMITS = {"A": (100.0, 3000.0), "B": (100.0, 3000.0), "tp": (5.0, 100.0), "n": (2, 8), "d": (12.0, 48.0),
          "e": (20.0, 300.0), "proj": (20.0, 300.0), "embed": (100.0, 2000.0), "grout": (0.0, 100.0), "a": (3.0, 20.0),
          "end": (0, 1), "W": (0.0, 1000.0), "top": (0.0, 300.0), "bottom": (0.0, 300.0), "rows": (1, 12),
          "p": (40.0, 300.0), "g": (0.0, 600.0), "w": (60.0, 400.0), "eh": (30.0, 300.0), "gap": (0.0, 200.0),
          "edge": (15.0, 150.0)}
MARGIN = 100.0                # mm round the column, its plate's default
BOLT_SIZES = (12.0, 16.0, 20.0, 24.0, 27.0, 30.0, 36.0, 42.0, 48.0)


def hole(d):
    """A bolt's hole (mm): d + 2 up to M24, d + 3 above (EN 1090-2, normal clearance)."""
    return d + (2.0 if d <= 24.0 else 3.0)


def bolt_spots(n, sx, sy):
    """Where n bolts go on a plate (mm, from its middle): its corners, and the middles of its long sides (6) or of
    all of them (8); 2: on its long axis."""
    corners = [(sx / 2 * i, sy / 2 * j) for i in (-1, 1) for j in (-1, 1)]
    if n <= 2:
        return [(0.0, -sy / 2), (0.0, sy / 2)] if sy >= sx else [(-sx / 2, 0.0), (sx / 2, 0.0)]
    if n <= 4:
        return corners
    middles = [(0.0, -sy / 2), (0.0, sy / 2)] if sx >= sy else [(-sx / 2, 0.0), (sx / 2, 0.0)]
    if n <= 6:
        return corners + middles
    return corners + [(0.0, -sy / 2), (0.0, sy / 2), (-sx / 2, 0.0), (sx / 2, 0.0)]


def clean(kind, params):
    """A connection's parameters as they may be kept: its kind's defaults, each in its range."""
    out = dict(DEFAULTS[kind])
    for k, v in (params or {}).items():
        if k not in out:
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        lo, hi = LIMITS[k]
        if k in ("A", "B", "W", "g") and v == 0.0:
            out[k] = 0.0
            continue
        v = min(max(v, lo), hi)
        out[k] = int(round(v)) if k in ("n", "rows", "end") else round(v, 1)
    return out


def end_plate_layout(params, beam, column, onto_flange):
    """A beam's end plate on a column (sections, mm): (W, H, middle of its height from the beam's, bolt spots [(x, y)],
    the column's thickness the bolts go through, warnings)."""
    W = params["W"] or beam.b
    H = beam.h + params["top"] + params["bottom"]
    middle = (params["top"] - params["bottom"]) / 2.0
    e, d = params["e"], params["d"]
    g = params["g"] or W - 2 * e
    rows, p = int(params["rows"]), params["p"]
    spots = [(sx * g / 2, middle + (j - (rows - 1) / 2.0) * p) for j in range(rows) for sx in (-1, 1)]
    d0 = hole(d)
    warnings = []
    if (W - g) / 2 < 1.2 * d0 or H / 2 - (rows - 1) * p / 2 < 1.2 * d0:
        warnings.append(("edge", round(1.2 * d0, 1)))
    if rows > 1 and p < 2.2 * d0:
        warnings.append(("pitch", round(2.2 * d0, 1)))
    if g < 2.4 * d0:
        warnings.append(("gauge", round(2.4 * d0, 1)))
    from ..core import steel
    i_column = column.family in steel.I_FAMILIES
    if i_column and onto_flange and g / 2 - d0 / 2 < column.tw / 2 + column.r:
        warnings.append(("web", round(column.tw + 2 * column.r + d0, 1)))
    if onto_flange and W > steel.size(column)[0]:
        warnings.append(("wide", steel.size(column)[0]))
    thickness = column.tf if onto_flange else column.tw
    return W, H, middle, spots, thickness, warnings


def fin_plate_layout(params, beam):
    """A fin plate on a beam's web (sections, mm): (its height, bolt spots [(along the beam from the column, up)],
    warnings)."""
    rows, p, e, d = int(params["rows"]), params["p"], params["e"], params["d"]
    H = (rows - 1) * p + 2 * e
    spots = [(params["eh"], (j - (rows - 1) / 2.0) * p) for j in range(rows)]
    d0 = hole(d)
    warnings = []
    if e < 1.2 * d0 or params["w"] - params["eh"] < 1.2 * d0:
        warnings.append(("edge", round(1.2 * d0, 1)))
    if rows > 1 and p < 2.2 * d0:
        warnings.append(("pitch", round(2.2 * d0, 1)))
    clear = beam.h - 2 * beam.tf - 2 * beam.r
    if H > clear:
        warnings.append(("tall", round(clear, 1)))
    return H, spots, warnings


def gusset_layout(params, brace):
    """(0.503) A brace's end bolted to a gusset through its angle's leg (sections, mm): (the bolts' gauge from the
    angle's heel, their distances from the brace's end, warnings) — EN 1993-1-8 Table 3.3, and the hole clear of the
    angle's root (else no washer seats)."""
    leg = brace.h
    g = params["g"] or round(leg * 0.55 / 5.0) * 5.0
    rows, p, e, d = int(params["rows"]), params["p"], params["e"], params["d"]
    along = [e + k * p for k in range(rows)]
    d0 = hole(d)
    warnings = []
    if e < 1.2 * d0 or leg - g < 1.2 * d0:
        warnings.append(("edge", round(1.2 * d0, 1)))
    if rows > 1 and p < 2.2 * d0:
        warnings.append(("pitch", round(2.2 * d0, 1)))
    if g - d0 / 2.0 < brace.tw + brace.r:
        warnings.append(("root", round(brace.tw + brace.r + d0 / 2.0, 1)))
    return g, along, warnings


def base_plate_layout(params, b, h):
    """The base plate of a column of section b × h (mm): its size, its bolts' spots — (A, B, spots, warnings)."""
    A = params["A"] or math.ceil((b + 2 * MARGIN) / 10.0) * 10.0
    B = params["B"] or math.ceil((h + 2 * MARGIN) / 10.0) * 10.0
    e, d = params["e"], params["d"]
    sx, sy = A - 2 * e, B - 2 * e
    spots = bolt_spots(int(params["n"]), sx, sy)
    d0 = hole(d)
    warnings = []
    if e < 1.2 * d0:
        warnings.append(("edge", round(1.2 * d0, 1)))
    gaps = [math.dist(p, q) for i, p in enumerate(spots) for q in spots[i + 1:]]
    if gaps and min(gaps) < 2.2 * d0:
        warnings.append(("pitch", round(2.2 * d0, 1)))
    if A <= b or B <= h:
        warnings.append(("small", 0.0))
    if any(abs(x) < b / 2 + d and abs(y) < h / 2 + d for x, y in spots):
        warnings.append(("clash", 0.0))
    return A, B, spots, warnings


class SteelConnectionMixin:
    # ------------------------------------------------------------ what there is

    def connection_of(self, part_guid):
        """The connection (IfcElementAssembly) a part belongs to — or the connection itself —, or None."""
        e = self.by_guid(part_guid)
        if e is None:
            return None
        if self.kind_of(part_guid) == "steel_connection":
            return e
        found = self._params(e).get("Ligacao") if self.kind_of(part_guid) == "steel_part" else None
        return self.by_guid(found) if found else None

    def connection_params(self, guid):
        """(kind, the GlobalIds it joins, its parameters) of a connection (or of one of its parts)."""
        assembly = self.connection_of(guid)
        if assembly is None:
            return None
        p = self._params(assembly)
        kind = p.get("Ligacao") if p.get("Ligacao") in KINDS else "base_plate"
        try:
            members = json.loads(p.get("Pecas") or "[]")
            params = json.loads(p.get("Parametros") or "{}")
        except ValueError:
            members, params = [], {}
        return kind, members, clean(kind, params)

    def connections_on(self, guids):
        """The connections that join any of these elements (their assemblies)."""
        wanted = set(guids)
        out = []
        for a in self.file.by_type("IfcElementAssembly"):
            if self.kind_of(a.GlobalId) != "steel_connection":
                continue
            try:
                members = json.loads(self._params(a).get("Pecas") or "[]")
            except ValueError:
                continue
            if wanted & set(members):
                out.append(a)
        return out

    def connection_parts(self, assembly):
        return [p for rel in assembly.IsDecomposedBy or () for p in rel.RelatedObjects]

    # ------------------------------------------------------------ made, changed, removed

    def add_connection(self, kind, members, params=None, lang="pt"):
        """A connection of `kind` joining `members` (GlobalIds: a base plate, its column), with `params` (mm; missing:
        its defaults). Returns the assembly."""
        if kind not in KINDS:
            raise EditRefused("connection_kind")
        if any(self.steel_section(m) is None for m in members):
            raise EditRefused("connection_not_steel")
        if kind == "gusset":                             # (0.503: an angle's leg bolted to it — a tube needs a slot)
            from ..core import steel
            if steel.get(self.steel_section(members[0])).family not in ANGLE_FAMILIES:
                raise EditRefused("connection_brace_angle")
        f = self.file
        label = NAMES[kind][0 if lang == "pt" else 1]
        column = self.by_guid(members[0])
        assembly = api.root.create_entity(f, ifc_class="IfcElementAssembly", predefined_type="USERDEFINED",
                                          name="{} — {}".format(label, " / ".join(self.by_guid(m).Name or ""
                                                                                for m in members)))
        assembly.ObjectType = "Ligação"
        storey = self.storey_of(members[0])
        if storey:
            api.spatial.assign_container(f, products=[assembly], relating_structure=self.storey(storey))
        self._mark(assembly, "steel_connection")
        self._set_params(assembly, {"Ligacao": kind, "Pecas": json.dumps(list(members)),
                                    "Parametros": json.dumps(clean(kind, params))})
        self._build_connection(assembly, lang)
        return assembly

    def set_connection(self, guid, lang="pt", **values):
        """A connection's parameters changed (any of them; the others kept): made again. Returns the assembly."""
        found = self.connection_params(guid)
        if found is None:
            raise EditRefused("connection_none")
        kind, members, params = found
        params.update(values)
        assembly = self.connection_of(guid)
        self._set_params(assembly, {"Parametros": json.dumps(clean(kind, params))})
        self._build_connection(assembly, lang)
        return assembly

    def remove_connection(self, guid):
        """A connection and all its parts taken away."""
        assembly = self.connection_of(guid)
        if assembly is None:
            return False
        self.release_connection(assembly)
        for part in self.connection_parts(assembly):
            api.root.remove_product(self.file, product=part)
        api.root.remove_product(self.file, product=assembly)
        return True

    def release_connection(self, assembly):
        """What a connection did to its pieces undone, before it goes: an end plate's beam back to its line's end."""
        kind, members, params = self.connection_params(assembly.GlobalId)
        if kind in ("end_plate", "gusset") and self.by_guid(members[0]) is not None:     # (0.503: a brace too)
            self._beam_end_drawn(members[0], int(params["end"]), 0.0)

    def release_connections(self, guids):
        """The connections among elements about to be deleted released (an end plate's beam lengthened back)."""
        for g in guids:
            if self.by_guid(g) is not None and self.kind_of(g) == "steel_connection":
                self.release_connection(self.by_guid(g))

    def beam_end_column(self, beam, end):
        """(0.498) The steel column a beam's end reaches (its line's end over the column, seen from above, within
        its faces and a few centimetres), or None."""
        p = self._beam_line(beam)[end]
        for col in self.file.by_type("IfcColumn"):
            if self.steel_section(col.GlobalId) is None:
                continue
            try:
                centre, x_dir, (a, b), base, top = self.column_box(col.GlobalId)
            except Exception:
                continue
            rel = np.asarray(p[:2], dtype=float) - centre
            x = np.asarray(x_dir, dtype=float)
            y = np.array((-x[1], x[0]))
            reach = 0.05
            if abs(float(rel @ x)) <= a + reach and abs(float(rel @ y)) <= b + reach and base - 1e-6 <= p[2] <= top + 0.05:
                return col.GlobalId
        return None

    def _beam_line(self, beam):
        """(start, end) of a beam's line (its section's middle), m."""
        if self.kind_of(beam) == "steel_member":            # (its line by its insertion point: to its middle)
            q = self.steel_member_params(beam)
            m = self.placement(beam)
            cx, cy = self.section_middle(self.by_guid(beam))
            shift = m[:3, 0] / np.linalg.norm(m[:3, 0]) * cx + m[:3, 1] / np.linalg.norm(m[:3, 1]) * cy
            return q["start"] + shift, q["end"] + shift
        start, end, _top, _w, _h = self.beam_params(beam)
        return np.asarray(start, dtype=float), np.asarray(end, dtype=float)

    def _beam_end_drawn(self, beam, end, amount):
        """A beam drawn out (+) or held back (−) `amount` m past its line's end `end`, made again."""
        e = self.by_guid(beam)
        cuts, copes, ext = self.steel_cuts(e)
        ext = list(ext)
        if abs(ext[end] - amount) < 1e-9:
            return
        ext[end] = amount
        if self.kind_of(beam) == "steel_member":
            line = self.steel_member_params(beam)          # (0.503: its line read before — its length is the body's
            self.set_steel_cuts(e, ext=ext)                # less what it is drawn out, the new amount not yet in it)
            self.set_steel_member(beam, start=line["start"], end=line["end"])
        else:
            self.set_steel_cuts(e, ext=ext)
            self.rebuild_beam(beam)

    def connections_to_remove(self, guids):
        """What goes with elements being deleted: the whole connection of a part of one, and the connections of a
        piece they joined — their assemblies' and parts' GlobalIds."""
        out = []
        for g in guids:
            kind = self.kind_of(g)
            if kind in ("steel_part", "steel_connection"):
                assembly = self.connection_of(g)
                found = [assembly] if assembly is not None else []
            else:
                found = self.connections_on([g])
            for a in found:
                for x in [a] + self.connection_parts(a):
                    if x.GlobalId not in out and x.GlobalId not in guids:
                        out.append(x.GlobalId)
        return out

    def follow_connections(self, changed):
        """The connections on the pieces changed made again (their column moved, given another section…); a
        connection whose piece is gone, removed. Returns the parts made."""
        out = []
        made = set(getattr(self, "made", None) or ())
        for assembly in self.connections_on(changed):
            if assembly.GlobalId in made:
                continue
            _kind, members, _params = self.connection_params(assembly.GlobalId)
            if any(self.by_guid(m) is None for m in members):
                self.remove_connection(assembly.GlobalId)
                continue
            self._build_connection(assembly)
            out += [p.GlobalId for p in self.connection_parts(assembly)]
            if _kind in ("end_plate", "gusset"):         # (its beam / brace held back: drawn again too)
                out.append(members[0])
        return out

    def connection_warnings(self, guid):
        """What its checks find: [(code, value)] (value: the least it should be, mm)."""
        found = self.connection_params(guid)
        if found is None:
            return []
        kind, members, params = found
        from ..core import steel
        secs = [steel.get(self.steel_section(m) or "") for m in members]
        if any(s is None for s in secs):
            return []
        if kind == "base_plate":
            b, h = steel.size(secs[0])
            return base_plate_layout(params, b, h)[3]
        if kind == "end_plate":
            frame = self._beam_end_frame(members[0], int(params["end"]))
            return end_plate_layout(params, secs[0], secs[1], self._onto_flange(members[1], frame[1]))[5]
        if kind == "gusset":
            return gusset_layout(params, secs[0])[2]
        return fin_plate_layout(params, secs[0])[2]

    # ------------------------------------------------------------ its parts

    def _column_foot(self, guid):
        """(a frame at the column's foot — its section's axes, z up —, its section) of a steel column: an ArqSynth
        column (its placement at its foot) or a steel piece standing up (its lower end)."""
        from ..core import steel
        m = self._placement_si(self.by_guid(guid))
        sec = steel.get(self.steel_section(guid) or "")
        if self.kind_of(guid) == "steel_member":
            p = self.steel_member_params(guid)
            if p["end"][2] < p["start"][2]:          # (drawn from the top down: its foot is its end, turned over)
                m = m.copy()
                m[:3, 3] = p["end"]
                m[:3, 1] *= -1.0
                m[:3, 2] *= -1.0
        return m, sec

    def _build_connection(self, assembly, lang="pt"):
        kind, members, params = self.connection_params(assembly.GlobalId)
        for part in self.connection_parts(assembly):
            api.root.remove_product(self.file, product=part)
        if kind == "base_plate":
            parts = self._base_plate_parts(members[0], params, lang)
        elif kind == "end_plate":
            parts = self._end_plate_parts(members[0], members[1], params, lang)
        elif kind == "fin_plate":
            parts = self._fin_plate_parts(members[0], members[1], params, lang)
        elif kind == "gusset":
            parts = self._gusset_parts(members[0], members[1], params, lang)
        else:
            parts = []
        if parts:
            api.aggregate.assign_object(self.file, products=parts, relating_object=assembly)
            for part in parts:
                if self._params(part):                  # (a plate keeps its sizes already: its set made once)
                    self._set_params(part, {"Elemento": "steel_part", "Ligacao": assembly.GlobalId})
                    for listed in (self.created, getattr(self, "made", None)):
                        if listed is not None:
                            listed.append(part.GlobalId)
                else:
                    self._mark(part, "steel_part")
                    self._set_params(part, {"Ligacao": assembly.GlobalId})

    def _base_plate_parts(self, column, params, lang):
        from ..core import steel
        f = self.file
        m, sec = self._column_foot(column)
        if sec is None:
            return []
        b, h = steel.size(sec)
        A, B, spots, _warnings = base_plate_layout(params, b, h)
        tp, d, a = params["tp"], params["d"], params["a"]
        material = self._column_material(column, lang)
        storey = self.storey_of(column)
        parts = []
        # the plate: its outline, its holes
        d0 = hole(d)
        four_x3 = self.file.schema.upper().startswith("IFC4X3")
        plate = api.root.create_entity(f, ifc_class="IfcPlate", name="{} {}×{}×{}".format(
            "Chapa" if lang == "pt" else "Plate", _mm(A), _mm(B), _mm(tp)),
            predefined_type="BASE_PLATE" if four_x3 else "USERDEFINED")       # (IFC4 has no BASE_PLATE yet)
        if not four_x3:
            plate.ObjectType = "BASE_PLATE"
        self._place(plate, m)
        self._extrusion_body(plate, [self._plate_profile(A, B, spots, d0)], [(0.0, 0.0, -tp / 1000.0)],
                             [tp / 1000.0])
        self._plate_record(plate, A, B, tp, [(x, y, d0) for x, y in spots], column)        # (0.501: for the NC1)
        net = (A * B - len(spots) * math.pi * d0 * d0 / 4) * tp * 1e-9                    # (m³)
        self._set_qto(plate, "Qto_PlateBaseQuantities", {"Width": tp / 1000.0 / self.unit_scale, "NetVolume": net,
                                                         "NetWeight": net * steel.DENSITY,
                                                         "GrossArea": A * B * 1e-6})
        parts.append(plate)
        # the anchor bolts: rod, washer, nut
        washer, wt = 2.5 * d, max(4.0, round(0.15 * d))
        nut_s, nut_h = 1.5 * d, 0.8 * d
        rod_low = -(tp + params["grout"] + params["embed"])
        for k, (x, y) in enumerate(spots, 1):
            bolt = api.root.create_entity(f, ifc_class="IfcMechanicalFastener", predefined_type="ANCHORBOLT",
                                          name="{} M{} {}".format("Chumbadouro" if lang == "pt" else "Anchor bolt",
                                                                  _mm(d), k))
            self._place(bolt, m)
            profiles = [f.createIfcCircleProfileDef("AREA", None, self._axis2d(x, y), d / 2000.0 / self.unit_scale),
                        f.createIfcRectangleProfileDef("AREA", None, self._axis2d(x, y), washer / 1000.0 /
                                                       self.unit_scale, washer / 1000.0 / self.unit_scale),
                        self._hexagon(x, y, nut_s)]
            self._extrusion_body(bolt, profiles, [(0.0, 0.0, rod_low / 1000.0), (0.0, 0.0, 0.0),
                                                   (0.0, 0.0, wt / 1000.0)],
                                 [(params["proj"] - rod_low) / 1000.0, wt / 1000.0, nut_h / 1000.0])
            pset = api.pset.add_pset(f, product=bolt, name="Pset_MechanicalFastenerAnchorBolt")
            api.pset.edit_pset(f, pset=pset, properties={"AnchorBoltDiameter": d / 1000.0 / self.unit_scale,
                                                         "AnchorBoltLength": (params["proj"] - rod_low) / 1000.0
                                                         / self.unit_scale,
                                                         "AnchorBoltProtrusionLength": params["proj"] / 1000.0
                                                         / self.unit_scale})
            parts.append(bolt)
        # the weld all round the column's foot
        weld = api.root.create_entity(f, ifc_class="IfcFastener", predefined_type="WELD",
                                      name="{} a{}".format("Soldadura" if lang == "pt" else "Weld", _mm(a)))
        self._place(weld, m)
        pset = api.pset.add_pset(f, product=weld, name="Pset_FastenerWeld")
        api.pset.edit_pset(f, pset=pset, properties={"a": a / 1000.0 / self.unit_scale,
                                                     "l": steel.properties(sec.name)["paint"] / self.unit_scale})
        parts.append(weld)
        api.material.assign_material(f, products=parts, type="IfcMaterial", material=material)
        if storey:
            api.spatial.assign_container(f, products=parts, relating_structure=self.storey(storey))
        return parts

    # ------------------------------------------------------------ (0.498) beam to column

    def _beam_end_frame(self, beam, end):
        """At a beam's end: (its line's end point, out — the way along the beam out of it, level —, across, up)."""
        start, stop = self._beam_line(beam)
        d = np.asarray(stop, dtype=float) - np.asarray(start, dtype=float)
        d[2] = 0.0
        d /= max(float(np.linalg.norm(d)), 1e-12)
        out = d if end == 1 else -d
        up = np.array((0.0, 0.0, 1.0))
        across = np.cross(up, out)
        return (np.asarray(stop if end == 1 else start, dtype=float), out, across, up)

    def _onto_flange(self, column, out):
        """Whether a beam coming along `out` meets an I column's flange (else its web)."""
        _c, x_dir, _half, _b, _t = self.column_box(column)
        x = np.asarray(x_dir, dtype=float)
        y = np.array((-x[1], x[0]))
        return abs(float(out[:2] @ y)) >= abs(float(out[:2] @ x))

    def _column_face(self, column, point, out, width=0.0):
        """How far along `out` from `point` the face of the column the beam meets is (m): its flange's outside, or
        its web (between the flanges, when what comes — `width` mm — fits between them; else its flanges' tips), or a
        tube's side."""
        from ..core import steel
        centre, x_dir, (a, b), _base, _top = self.column_box(column)
        sec = steel.get(self.steel_section(column) or "")
        x = np.asarray(x_dir, dtype=float)
        y = np.array((-x[1], x[0]))
        u = np.asarray(out[:2], dtype=float)
        fits = sec is not None and width <= sec.h - 2.0 * sec.tf - 2.0 * sec.r
        if sec is not None and sec.family in steel.I_FAMILIES and not self._onto_flange(column, out) and fits:
            half = sec.tw / 2000.0 / max(abs(float(u @ x)), 1e-9)
        else:
            ux, uy = abs(float(u @ x)), abs(float(u @ y))
            half = min(a / ux if ux > 1e-9 else np.inf, b / uy if uy > 1e-9 else np.inf)
        along = float((centre - np.asarray(point[:2], dtype=float)) @ u)    # (the column's middle, from the point)
        return along - half

    def _frame(self, origin, x, y, z):
        m = np.eye(4)
        m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, y, z, origin
        return m

    def _end_plate_parts(self, beam, column, params, lang):
        from ..core import steel
        f = self.file
        end = int(params["end"])
        bsec, csec = steel.get(self.steel_section(beam)), steel.get(self.steel_section(column))
        point, out, across, up = self._beam_end_frame(beam, end)
        onto_flange = self._onto_flange(column, out)
        W, H, middle, spots, through, _w = end_plate_layout(params, bsec, csec, onto_flange)
        tp = params["tp"]
        face = self._column_face(column, point, out, max(W, bsec.b))
        back = face - tp / 1000.0                              # (the plate's beam side, from the line's end)
        self._beam_end_drawn(beam, end, back)                  # (the beam ends against the plate)
        m = self._frame(point + out * back, across, up, out)
        material = self._column_material(beam, lang)
        parts = []
        plate = api.root.create_entity(f, ifc_class="IfcPlate", name="{} {}×{}×{}".format(
            "Chapa de topo" if lang == "pt" else "End plate", _mm(W), _mm(H), _mm(tp)), predefined_type="USERDEFINED")
        plate.ObjectType = "END_PLATE"
        self._place(plate, m)
        d0 = hole(params["d"])
        self._extrusion_body(plate, [self._plate_profile(W, H, spots, d0, centre=(0.0, middle))], [(0.0, 0.0, 0.0)],
                             [tp / 1000.0])
        net = (W * H - len(spots) * math.pi * d0 * d0 / 4) * tp * 1e-9
        self._plate_record(plate, W, H, tp, [(x, y - middle, d0) for x, y in spots], beam)    # (0.501)
        self._set_qto(plate, "Qto_PlateBaseQuantities", {"Width": tp / 1000.0 / self.unit_scale, "NetVolume": net,
                                                         "NetWeight": net * steel.DENSITY, "GrossArea": W * H * 1e-6})
        parts.append(plate)
        for k, (x, y) in enumerate(spots, 1):
            parts.append(self._bolt(m, x, y, 0.0, tp + through, params["d"], k, lang))
        parts.append(self._weld(m, params["a"], steel.properties(bsec.name)["paint"], lang))
        api.material.assign_material(f, products=parts, type="IfcMaterial", material=material)
        storey = self.storey_of(beam)
        if storey:
            api.spatial.assign_container(f, products=parts, relating_structure=self.storey(storey))
        return parts

    def _fin_plate_parts(self, beam, column, params, lang):
        from ..core import steel
        f = self.file
        end = int(params["end"])
        bsec = steel.get(self.steel_section(beam))
        point, out, across, up = self._beam_end_frame(beam, end)
        H, spots, _w = fin_plate_layout(params, bsec)
        tp, w = params["tp"], params["w"]
        face = self._column_face(column, point, out, bsec.b)
        inward = -out
        m = self._frame(point + out * face, inward, up, np.cross(inward, up))    # (x into the beam, z across)
        material = self._column_material(column, lang)
        parts = []
        plate = api.root.create_entity(f, ifc_class="IfcPlate", name="{} {}×{}×{}".format(
            "Cutelo" if lang == "pt" else "Fin plate", _mm(w), _mm(H), _mm(tp)), predefined_type="USERDEFINED")
        plate.ObjectType = "FIN_PLATE"
        self._place(plate, m)
        d0 = hole(params["d"])
        z0 = bsec.tw / 2.0                                       # (beside the beam's web)
        self._extrusion_body(plate, [self._plate_profile(w, H, spots, d0, centre=(w / 2.0, 0.0))],
                             [(0.0, 0.0, z0 / 1000.0)], [tp / 1000.0])
        net = (w * H - len(spots) * math.pi * d0 * d0 / 4) * tp * 1e-9
        self._plate_record(plate, w, H, tp, [(x - w / 2.0, y, d0) for x, y in spots], column)   # (0.501)
        self._set_qto(plate, "Qto_PlateBaseQuantities", {"Width": tp / 1000.0 / self.unit_scale, "NetVolume": net,
                                                         "NetWeight": net * steel.DENSITY, "GrossArea": w * H * 1e-6})
        parts.append(plate)
        for k, (x, y) in enumerate(spots, 1):
            parts.append(self._bolt(m, x, y, z0 + tp, -z0, params["d"], k, lang))
        parts.append(self._weld(m, params["a"], 2.0 * H / 1000.0, lang))
        api.material.assign_material(f, products=parts, type="IfcMaterial", material=material)
        storey = self.storey_of(beam)
        if storey:
            api.spatial.assign_container(f, products=parts, relating_structure=self.storey(storey))
        return parts

    # ------------------------------------------------------------ (0.503) a brace's gusset

    def brace_frame(self, brace):
        """A steel piece's frame: (its line's start, end, along, its section's x and y — unit vectors —, the middle
        of its section from its line (x, y) mm)."""
        start, end = self._beam_line(brace) if self.kind_of(brace) != "steel_member" else \
            (self.steel_member_params(brace)["start"], self.steel_member_params(brace)["end"])
        m = self.placement(brace)
        xl = m[:3, 0] / np.linalg.norm(m[:3, 0])
        yl = m[:3, 1] / np.linalg.norm(m[:3, 1])
        cx, cy = self.section_middle(self.by_guid(brace))
        along = np.asarray(end, dtype=float) - np.asarray(start, dtype=float)
        along /= max(float(np.linalg.norm(along)), 1e-12)
        return np.asarray(start, dtype=float), np.asarray(end, dtype=float), along, xl, yl, (cx * 1000.0, cy * 1000.0)

    def _gusset_parts(self, brace, column, params, lang):
        """The gusset in the brace's plane against the back of the angle's leg that lies in it (the angle's own y), its
        edge welded to the column's face — its web between the flanges, when it fits there —, the brace held back
        clear of the column (`gap`), its leg bolted to the plate (a row of bolts along it)."""
        from shapely.geometry import MultiPoint, Point, Polygon, box
        from ..core import steel
        f = self.file
        end = int(params["end"])
        bsec = steel.get(self.steel_section(brace))
        start, stop, along, xl, yl, (cx, cy) = self.brace_frame(brace)
        point = stop if end == 1 else start
        u = -along if end == 1 else along                       # (into the brace from its end)
        out = -np.array((u[0], u[1], 0.0))                     # (level, into the column)
        if float(np.linalg.norm(out)) < 1e-6:
            return []
        out /= np.linalg.norm(out)
        b, h, tp = bsec.b, bsec.h, params["tp"]
        g, distances, _w = gusset_layout(params, bsec)
        # the brace's end clear of the column's outside (its flanges' tips), every corner of its section
        face_box = self._column_face(column, point, out, 1e9)
        reach = float(u @ -out)
        if reach < 0.05:
            return []
        corners = [(x, y) for x in (cx - b / 2, cx + b / 2) for y in (cy - h / 2, cy + h / 2)]
        hold = max((-face_box + params["gap"] / 1000.0 - (x * float(xl @ -out) + y * float(yl @ -out)) / 1000.0)
                   / reach for x, y in corners)
        self._beam_end_drawn(brace, end, -hold)
        # the plate's frame: in the plane of the leg's back, x level towards the brace, z through the leg
        back = (cx - b / 2.0 - tp) / 1000.0                    # (its far face from the brace's line, along x)
        z2 = xl
        x2 = -out - float(-out @ z2) * z2
        x2 /= np.linalg.norm(x2)
        y2 = np.cross(z2, x2)
        origin = point + xl * back
        m = self._frame(origin, x2, y2, z2)

        def flat(w):
            r = (np.asarray(w, dtype=float) - origin) * 1000.0
            return float(r @ x2), float(r @ y2)

        def on_brace(dist_mm, y_mm):
            return point + u * (hold + dist_mm / 1000.0) + yl * (y_mm / 1000.0)
        last = distances[-1] + params["e"]
        lo_y, hi_y = cy - h / 2.0 - params["edge"], cy + h / 2.0 + params["edge"]
        region = [flat(on_brace(s, y)) for s in (-params["gap"] / 2.0, last) for y in (lo_y, hi_y)]
        width = 2.0 * (abs(back * 1000.0) + tp)
        face = self._column_face(column, point, out, width)
        weld_x = flat(point + out * face)[0]
        ys = [p[1] for p in region]
        outline = MultiPoint(region + [(weld_x, min(ys)), (weld_x, max(ys))]).convex_hull
        _c, _x, _half, base, top = self.column_box(column)
        clear = abs(back * 1000.0) + 10.0                      # (under a mitred top, clear of the rafter)
        level = [flat(np.array((point[0], point[1], z)))[1] for z in (base, top - clear / 1000.0)]
        outline = outline.intersection(box(weld_x, min(level), 1e6, max(level)))
        if outline.is_empty or outline.geom_type != "Polygon":
            return []
        outline = Polygon([(round(x, 1), round(y, 1)) for x, y in outline.exterior.coords]).buffer(0)
        spots = [flat(on_brace(s, cy - h / 2.0 + g)) for s in distances]
        d0 = hole(params["d"])
        spots = [s for s in spots if outline.contains(Point(s).buffer(d0 / 2.0))]
        # the plate
        x0, y0, x1, y1 = outline.bounds
        L, W = x1 - x0, y1 - y0
        mid = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
        material = self._column_material(column, lang)
        plate = api.root.create_entity(f, ifc_class="IfcPlate", name="{} {}×{}×{}".format(
            "Gousset" if lang == "pt" else "Gusset", _mm(round(L)), _mm(round(W)), _mm(tp)),
            predefined_type="USERDEFINED")
        plate.ObjectType = "GUSSET_PLATE"
        self._place(plate, m)
        ring = list(outline.exterior.coords)
        self._extrusion_body(plate, [self._polygon_profile(ring, spots, d0)], [(0.0, 0.0, 0.0)], [tp / 1000.0])
        area = outline.area - len(spots) * math.pi * d0 * d0 / 4.0
        net = area * tp * 1e-9
        self._plate_record(plate, L, W, tp, [(x - mid[0], y - mid[1], d0) for x, y in spots], column,
                           contour=[(x - mid[0], y - mid[1]) for x, y in ring[:-1]])
        self._set_qto(plate, "Qto_PlateBaseQuantities", {"Width": tp / 1000.0 / self.unit_scale, "NetVolume": net,
                                                         "NetWeight": net * steel.DENSITY,
                                                         "GrossArea": outline.area * 1e-6})
        parts = [plate]
        for k, (x, y) in enumerate(spots, 1):
            parts.append(self._bolt(m, x, y, 0.0, tp + bsec.tw, params["d"], k, lang))
        edge = outline.intersection(box(weld_x - 0.5, -1e6, weld_x + 0.5, 1e6))
        weld_len = (edge.bounds[3] - edge.bounds[1]) if not edge.is_empty else 0.0
        parts.append(self._weld(m, params["a"], 2.0 * weld_len / 1000.0, lang))
        api.material.assign_material(f, products=parts, type="IfcMaterial", material=material)
        storey = self.storey_of(column)
        if storey:
            api.spatial.assign_container(f, products=parts, relating_structure=self.storey(storey))
        return parts

    def brace_end_columns(self, brace):
        """(0.503) {end: column} — the steel columns a brace's ends reach."""
        out = {}
        for end in (0, 1):
            found = self.beam_end_column(brace, end)
            if found is not None:
                out[end] = found
        return out

    def _bolt(self, m, x, y, head_face, nut_face, d, k, lang):
        """A bolt (IfcMechanicalFastener BOLT) along the frame's z at (x, y) mm: its head against `head_face`, its
        washer and nut against `nut_face` (mm), its rod a little past the nut."""
        f = self.file
        s = 1.0 if nut_face >= head_face else -1.0
        kh, wt, nh = 0.65 * d, max(3.0, round(0.15 * d)), 0.8 * d
        ranges = [(head_face, nut_face + s * (wt + nh + 3.0)),          # (its rod)
                  (head_face - s * kh, head_face),                       # (its head)
                  (nut_face, nut_face + s * wt),                         # (its washer)
                  (nut_face + s * wt, nut_face + s * (wt + nh))]         # (its nut)
        profiles = [f.createIfcCircleProfileDef("AREA", None, self._axis2d(x, y), d / 2000.0 / self.unit_scale),
                    self._hexagon(x, y, 1.5 * d),
                    f.createIfcCircleProfileDef("AREA", None, self._axis2d(x, y), 1.0 * d / self.unit_scale / 1000.0),
                    self._hexagon(x, y, 1.5 * d)]
        bolt = api.root.create_entity(f, ifc_class="IfcMechanicalFastener", predefined_type="BOLT",
                                      name="{} M{} {}".format("Parafuso" if lang == "pt" else "Bolt", _mm(d), k))
        self._place(bolt, m)
        self._extrusion_body(bolt, profiles, [(0.0, 0.0, min(a, b) / 1000.0) for a, b in ranges],
                             [abs(b - a) / 1000.0 for a, b in ranges])
        pset = api.pset.add_pset(f, product=bolt, name="Pset_MechanicalFastenerBolt")
        api.pset.edit_pset(f, pset=pset, properties={"ThreadDiameter": d / 1000.0 / self.unit_scale,
                                                     "ThreadLength": abs(ranges[0][1] - ranges[0][0]) / 1000.0
                                                     / self.unit_scale})
        return bolt

    def _weld(self, m, a, length, lang):
        """A fillet weld (IfcFastener WELD, no body): its throat a (mm), its length (m)."""
        f = self.file
        weld = api.root.create_entity(f, ifc_class="IfcFastener", predefined_type="WELD",
                                      name="{} a{}".format("Soldadura" if lang == "pt" else "Weld", _mm(a)))
        self._place(weld, m)
        pset = api.pset.add_pset(f, product=weld, name="Pset_FastenerWeld")
        api.pset.edit_pset(f, pset=pset, properties={"a": a / 1000.0 / self.unit_scale, "l": length / self.unit_scale})
        return weld

    def _plate_record(self, plate, length, width, thickness, holes, piece, contour=None):
        """(0.501) A plate's sizes and holes kept on it (mm; holes [(x, y, d0)] from its middle) — its NC1's; (0.503)
        an outline that is not its rectangle (a gusset's): its corners from its middle too."""
        import re
        material = ifcopenshell.util.element.get_material(self.by_guid(piece), should_skip_usage=True)
        name = material.MaterialProfiles[0].Material.Name if material is not None and \
            material.is_a("IfcMaterialProfileSet") and material.MaterialProfiles[0].Material else ""
        found = re.search(r"S\d{3}", name or "")
        record = {"L": float(length), "W": float(width), "t": float(thickness), "grade": found.group(0) if found else "",
                  "furos": [[float(x), float(y), float(d)] for x, y, d in holes]}
        if contour:
            record["contorno"] = [[round(float(x), 1), round(float(y), 1)] for x, y in contour]
        self._set_params(plate, {"Chapa": json.dumps(record)})

    def _column_material(self, column, lang):
        material = ifcopenshell.util.element.get_material(self.by_guid(column), should_skip_usage=True)
        if material is not None and material.is_a("IfcMaterialProfileSet") and material.MaterialProfiles:
            found = material.MaterialProfiles[0].Material
            if found is not None:
                return found
        return self._material("aco_s275", lang)

    # ------------------------------------------------------------ geometry helpers (file units)

    def _axis2d(self, x, y):
        u = 0.001 / self.unit_scale
        return self.file.createIfcAxis2Placement2D(self.file.createIfcCartesianPoint((float(x * u), float(y * u))))

    def _hexagon(self, x, y, across):
        """A hexagonal profile (a nut) `across` mm across its flats, its middle at (x, y) mm."""
        u = 0.001 / self.unit_scale
        r = across / math.sqrt(3.0)
        pts = [self.file.createIfcCartesianPoint((float((x + r * math.cos(math.pi / 3 * k)) * u),
                                                  float((y + r * math.sin(math.pi / 3 * k)) * u))) for k in range(7)]
        return self.file.createIfcArbitraryClosedProfileDef("AREA", None, self.file.createIfcPolyline(pts))

    def _plate_profile(self, A, B, spots, d0, centre=(0.0, 0.0)):
        """A plate's outline A × B mm round `centre`, with its holes."""
        f = self.file
        u = 0.001 / self.unit_scale
        cx, cy = centre
        corners = [(cx - A / 2, cy - B / 2), (cx + A / 2, cy - B / 2), (cx + A / 2, cy + B / 2),
                   (cx - A / 2, cy + B / 2), (cx - A / 2, cy - B / 2)]
        outer = f.createIfcPolyline([f.createIfcCartesianPoint((float(x * u), float(y * u))) for x, y in corners])
        holes = [f.createIfcCircle(self._axis2d(x, y), float(d0 / 2 * u)) for x, y in spots]
        if not holes:
            return f.createIfcArbitraryClosedProfileDef("AREA", None, outer)
        return f.createIfcArbitraryProfileDefWithVoids("AREA", None, outer, holes)

    def _polygon_profile(self, ring, spots, d0):
        """(0.503) A plate's outline of any shape (its corners mm, closed), with its holes."""
        f = self.file
        u = 0.001 / self.unit_scale
        pts = [(float(x), float(y)) for x, y in ring]
        if pts[0] != pts[-1]:
            pts.append(pts[0])
        outer = f.createIfcPolyline([f.createIfcCartesianPoint((x * u, y * u)) for x, y in pts])
        holes = [f.createIfcCircle(self._axis2d(x, y), float(d0 / 2 * u)) for x, y in spots]
        if not holes:
            return f.createIfcArbitraryClosedProfileDef("AREA", None, outer)
        return f.createIfcArbitraryProfileDefWithVoids("AREA", None, outer, holes)

    def _extrusion_body(self, product, profiles, origins, depths):
        """A body of extrusions up its own z: each profile from its origin (m), its depth (m)."""
        f = self.file
        u = 1.0 / self.unit_scale
        items = [f.createIfcExtrudedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint(tuple(float(c * u) for c in o))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(depth * u))
            for profile, o, depth in zip(profiles, origins, depths)]
        rep = f.createIfcShapeRepresentation(self.body, self.body.ContextIdentifier, "SweptSolid", items)
        api.geometry.assign_representation(f, product=product, representation=rep)


def _mm(v):
    return "{:g}".format(float(v))
