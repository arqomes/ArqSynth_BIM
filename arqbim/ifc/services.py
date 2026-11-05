"""Pipes and ducts joined (0.74): their ports (IfcDistributionPort, one at each end) and the bends
(IfcPipeFitting / IfcDuctFitting, BEND) made where one segment goes on from another at an angle.

A bend is the segment's own section swept round a centre line of radius R (one diameter, or the duct's
width) — an IfcRevolvedAreaSolid — and the two segments stop where it starts and ends (R·tan(θ/2)
before the corner). Its ports are connected to theirs (IfcRelConnectsPorts); two segments in line are
connected port to port, with no fitting.

0.137: a branch that ends on (or starts from) the middle of another — a pipe, a stack — splits it there and a
tee (JUNCTION) is put in: a short piece of the main, in line with it, and a stub along the branch, three ports.
Two segments in line of different sizes get a reducer (TRANSITION) between them: a cone (an
IfcExtrudedAreaSolidTapered) for pipes, a faceted solid for ducts."""

import math

import numpy as np

import ifcopenshell.api as api
import ifcopenshell.api.system  # noqa: F401
import ifcopenshell.util.element

from ..core import classify

FITTING = {"pipe": ("IfcPipeFitting", "IfcPipeFittingType", "Qto_PipeFittingBaseQuantities", "PIPE"),
           "duct": ("IfcDuctFitting", "IfcDuctFittingType", "Qto_DuctFittingBaseQuantities", "DUCT"),
           # (0.146) the electrical conduits: their fittings' quantities hold only a weight (none written)
           "conduit": ("IfcCableCarrierFitting", "IfcCableCarrierFittingType", None, "CABLECARRIER")}
SEGMENT = {"pipe": ("IfcPipeSegment", "Qto_PipeSegmentBaseQuantities"),
           "duct": ("IfcDuctSegment", "Qto_DuctSegmentBaseQuantities"),
           "conduit": ("IfcCableCarrierSegment", "Qto_CableCarrierSegmentBaseQuantities")}


def segment_qto(element):
    """The base quantities' name of a pipe's, a duct's or a conduit's class."""
    return next((q for cls, q in SEGMENT.values() if element.is_a(cls)), "Qto_PipeSegmentBaseQuantities")
IN_LINE_DEG = 1.0           # a turn smaller than this: the two segments simply go on, port to port
MAX_TURN_DEG = 170.0        # sharper than this: no bend can be made (left as two segments, connected)
_BEND_NAME = ("Curva", "Bend")
_TEE_NAME = ("Tê", "Tee")
_WYE_NAME = ("Forquilha", "Wye")                 # (0.200) a tee with its branch at 45° or so: a Y
WYE_DEG = 60.0              # a branch nearer the main's line than this: a wye (its own name and type)
_REDUCER_NAME = ("Redução", "Reducer")
COLLAR = 0.025              # m (0.137): a tee's main piece runs this far past the branch on each side, its stub
#                             this far past the main's side; a reducer is this long and more, by the sizes
MIN_PIECE = 0.05            # m: the shortest piece of pipe left beside a fitting
MIN_BRANCH_DEG = 15.0       # a branch nearer the main's line than this: no tee


def _unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


class ServicesMixin:
    # ------------------------------------------------------------ ports

    def _port_frame(self, at, direction, x_hint=None):
        """A port's placement: at a segment's end, its Z along the flow (0.136: in any direction)."""
        at = np.asarray(at, dtype=float)
        return classify.segment_placement(at, at + _unit(direction), x_hint)[0]

    def _across(self, guid):
        """A segment's (or bend's) X: across it, level — for a vertical one, the way its section is turned."""
        m = self._placement_si(self.by_guid(guid))
        return m[:3, 0] / np.linalg.norm(m[:3, 0])

    def add_segment_ports(self, element, kind):
        """A segment's two ports (0.74): the first at its start (flow in), the second at its end (out)."""
        start, end, _z = self.segment_params(element.GlobalId)
        d, x = end - start, self._across(element.GlobalId)
        for name, at, flow in (("1", start, "SINK"), ("2", end, "SOURCE")):
            port = api.system.add_port(self.file, element=element)
            port.Name, port.FlowDirection = name, flow
            port.PredefinedType = FITTING[kind][3]
            self._place(port, self._port_frame(at, d, x))

    def ports(self, guid):
        """The ports of a distribution element, the one nearest its start (its placement's origin) first."""
        e = self.by_guid(guid)
        found = [o for rel in (getattr(e, "IsNestedBy", None) or ()) for o in rel.RelatedObjects
                 if o.is_a("IfcDistributionPort")]
        origin = self._placement_si(e)[:3, 3]
        return sorted(found, key=lambda p: float(np.linalg.norm(self._placement_si(p)[:3, 3] - origin)))

    def update_segment_ports(self, guid):
        """After a segment changed length or place: its ports at its two ends again."""
        ports = self.ports(guid)
        if len(ports) != 2:
            return
        start, end, _z = self.segment_params(guid)
        x = self._across(guid)
        for port, at in zip(ports, (start, end)):
            self._place(port, self._port_frame(at, end - start, x))

    def connected(self, port):
        """The port this one is connected to, or None."""
        for rel in list(getattr(port, "ConnectedTo", None) or ()) + list(getattr(port, "ConnectedFrom", None) or ()):
            other = rel.RelatedPort if rel.RelatingPort == port else rel.RelatingPort
            return other
        return None

    def connections(self, guid):
        """What each port of a pipe / duct / bend is connected to: [name of that element, or None (free)],
        start first (0.74, the Properties panel)."""
        out = []
        for port in self.ports(guid):
            other = self.connected(port)
            owner = None
            if other is not None:
                for rel in getattr(other, "Nests", None) or ():
                    owner = rel.RelatingObject
            out.append((owner.Name or owner.is_a()) if owner is not None else None)
        return out

    def owner_of(self, port):
        for rel in getattr(port, "Nests", None) or ():
            return rel.RelatingObject
        return None

    def run(self, guid, through=None):
        """The pipes / ducts / bends connected to `guid` (itself excluded): all of them, or only those
        reached through its port `through` (0: its start, 1: its end) — what goes along when it moves."""
        seen, out = {guid}, []
        ports = self.ports(guid)
        stack = [p for k, p in enumerate(ports) if through is None or k == through]
        while stack:
            other = self.connected(stack.pop())
            owner = self.owner_of(other) if other is not None else None
            if owner is None or owner.GlobalId in seen:
                continue
            seen.add(owner.GlobalId)
            out.append(owner.GlobalId)
            stack += [p for p in self.ports(owner.GlobalId) if p != other]
        return out

    def _connect(self, port1, port2):
        api.system.connect_port(self.file, port1=port1, port2=port2, direction="SOURCE")

    # ------------------------------------------------------------ bends

    def _fitting_type(self, segment, kind, lang, predefined="BEND", word=_BEND_NAME):
        """The bend's type for a segment's type ("Curva — Tubo PVC Ø50"), made once, with its material — or
        a tee's, a reducer's (0.137: predefined JUNCTION / TRANSITION)."""
        seg_type = ifcopenshell.util.element.get_type(segment)
        name = "{} — {}".format(word[0 if lang == "pt" else 1], seg_type.Name if seg_type else "")
        _cls, type_class, _qto, _port = FITTING[kind]
        for t in self.file.by_type(type_class):
            if t.Name == name:
                return t
        type_ = api.root.create_entity(self.file, ifc_class=type_class, name=name, predefined_type=predefined)
        material = ifcopenshell.util.element.get_material(segment, should_skip_usage=True)
        if material is not None and material.is_a("IfcMaterialProfileSet"):
            material = material.MaterialProfiles[0].Material
        if material is not None:
            api.material.assign_material(self.file, products=[type_], type="IfcMaterial", material=material)
        return type_

    def join_segments(self, first, second, lang="pt"):
        """`second` goes on from where `first` ends (0.74): in line, their ports are connected; at an angle, a
        bend is put in the corner (both made shorter to meet it) and connected to both — in any direction
        (0.136: up or down a riser, along a slope). Returns the bend's GlobalId, or None."""
        kind = self.kind_of(first)
        if kind not in FITTING or self.kind_of(second) != kind:
            return None
        e1, e2 = self.by_guid(first), self.by_guid(second)
        s1, end1, _z = self.segment_params(first)
        s2, end2, _z2 = self.segment_params(second)
        d1, d2 = _unit(end1 - s1), _unit(end2 - s2)
        ports1, ports2 = self.ports(first), self.ports(second)
        turn = math.degrees(math.acos(float(np.clip(np.dot(d1, d2), -1.0, 1.0))))
        same = ifcopenshell.util.element.get_type(e1) == ifcopenshell.util.element.get_type(e2)
        if turn < IN_LINE_DEG and not same:                         # (0.137) in line, another size: a reducer
            made = self.add_reducer(first, second, lang)
            if made is not None:
                return made
        if turn < IN_LINE_DEG or turn > MAX_TURN_DEG or not same:   # (another size: no bend of ours fits)
            if len(ports1) == 2 and len(ports2) == 2:
                self._connect(ports1[1], ports2[0])
            return None
        profile = ifcopenshell.util.element.get_material(e1, should_skip_usage=True).MaterialProfiles[0].Profile
        s = self.unit_scale
        size = 2 * profile.Radius * s if profile.is_a("IfcCircleProfileDef") else profile.XDim * s
        theta = math.radians(turn)
        radius = size                              # the bend's centre line: one diameter / the duct's width
        len1, len2 = float(np.linalg.norm(end1 - s1)), float(np.linalg.norm(end2 - s2))
        room = min(len1, len2) - MIN_PIECE
        if radius * math.tan(theta / 2) > room:
            radius = room / math.tan(theta / 2)
        if radius < size / 2:                      # too short for a bend: connected as they are
            if len(ports1) == 2 and len(ports2) == 2:
                self._connect(ports1[1], ports2[0])
            return None
        cut = radius * math.tan(theta / 2)
        corner = end1
        # the segments stop where the bend starts / ends (nothing is connected there yet: nothing else moves;
        # 0.138: a piece may be shorter than an edit may leave — a short riser's)
        self._set_length(first, len1 - cut)
        m2 = self._placement_si(e2)
        m2[:3, 3] += d2 * cut
        self._place(e2, m2)
        self._set_length(second, len2 - cut)
        # the bend: the section swept round its centre, from the end of `first`, in its frame (X across, Y "up"
        # of its section, Z along it): the centre is toward where `second` goes, square to `first`
        cls, _type_class, qto, _port = FITTING[kind]
        f, u = self.file, 1.0 / s
        x1 = self._across(first)
        y1 = np.cross(d1, x1)
        toward = _unit(d2 - float(np.dot(d2, d1)) * d1)
        nx, ny = float(np.dot(toward, x1)), float(np.dot(toward, y1))     # (level, turning left: (1, 0))
        solid = f.createIfcRevolvedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)), None, None),
            f.createIfcAxis1Placement(f.createIfcCartesianPoint((nx * radius * u, ny * radius * u, 0.0)),
                                      f.createIfcDirection((-ny, nx, 0.0))),
            theta)
        name = "{} {}".format(_BEND_NAME[0 if lang == "pt" else 1], len(f.by_type(cls)) + 1)
        bend = api.root.create_entity(f, ifc_class=cls, name=name, predefined_type="BEND")
        api.type.assign_type(f, related_objects=[bend], relating_type=self._fitting_type(e1, kind, lang))
        body = f.createIfcShapeRepresentation(self.body, "Body", "SweptSolid", [solid])
        api.geometry.assign_representation(f, product=bend, representation=body)
        start = corner - d1 * cut
        self._place(bend, self._port_frame(start, d1, x1))
        api.spatial.assign_container(f, products=[bend], relating_structure=self.storey(self.storey_of(first)))
        area = math.pi * (size / 2) ** 2 if profile.is_a("IfcCircleProfileDef") else profile.XDim * s * profile.YDim * s
        if qto:                                    # (a conduit's bend: none, 0.146)
            self._set_qto(bend, qto, {"Length": radius * theta * u, "GrossCrossSectionArea": area})
        self._mark(bend, "fitting")
        # its ports, at its two ends, connected to the segments'
        ends = ((start, d1, "SINK"), (corner + d2 * cut, d2, "SOURCE"))
        bend_ports = []
        for k, (at, d, flow) in enumerate(ends, 1):
            port = api.system.add_port(f, element=bend)
            port.Name, port.FlowDirection, port.PredefinedType = str(k), flow, FITTING[kind][3]
            self._place(port, self._port_frame(at, d, x1))
            bend_ports.append(port)
        if len(ports1) == 2 and len(ports2) == 2:
            self._connect(ports1[1], bend_ports[0])
            self._connect(bend_ports[1], ports2[0])
        return bend.GlobalId

    # ------------------------------------------------------------ tees and reducers (0.137)

    def _profile(self, element):
        return ifcopenshell.util.element.get_material(element, should_skip_usage=True).MaterialProfiles[0].Profile

    def _size(self, element):
        """(across, up) of a pipe's / duct's section in metres (a pipe: its diameter both)."""
        profile, s = self._profile(element), self.unit_scale
        if profile.is_a("IfcCircleProfileDef"):
            return 2 * profile.Radius * s, 2 * profile.Radius * s
        return profile.XDim * s, profile.YDim * s

    def _set_length(self, guid, length):
        """A segment at this length, its start where it is — its body, quantities and ports; nothing else moves."""
        element = self.by_guid(guid)
        qto = segment_qto(element)
        self._set_profile_body(element, self._profile(element), float(length), qto)
        self.update_segment_ports(guid)

    def _segment_like(self, model, start, end, lang):
        """A new segment of the same type, storey and kind as `model`, from start to end (3D), with its ports."""
        f, e = self.file, self.by_guid(model)
        kind = self.kind_of(model)
        type_ = ifcopenshell.util.element.get_type(e)
        cls = e.is_a()
        word = {"pipe": ("Tubo", "Pipe"), "duct": ("Conduta", "Duct"), "conduit": ("Tubo VD", "Conduit")}[kind]
        new = api.root.create_entity(f, ifc_class=cls, name="{} {}".format(word[0 if lang == "pt" else 1],
                                                                          len(f.by_type(cls)) + 1))
        api.type.assign_type(f, related_objects=[new], relating_type=type_)
        qto = segment_qto(e)
        matrix, length = classify.segment_placement(start, end, self._across(model))
        self._set_profile_body(new, self._profile(e), length, qto)
        self._place(new, matrix)
        api.spatial.assign_container(f, products=[new], relating_structure=self.storey(self.storey_of(model)))
        self._mark(new, kind)
        self.add_segment_ports(new, kind)
        from .edit import PARAM_PSET
        for name, props in ifcopenshell.util.element.get_psets(e, psets_only=True, should_inherit=False).items():
            values = {k: v for k, v in props.items() if k != "id"}
            if name != PARAM_PSET and values:      # (what it had of its own: its phase, what was written on it)
                api.pset.edit_pset(f, pset=api.pset.add_pset(f, product=new, name=name), properties=values)
        return new

    def _new_fitting(self, model, kind, lang, predefined, word, items, rep_type, frame, ports, qto_values):
        """A fitting (a tee, a reducer) of `model`'s storey: its body (items, in its frame), its ports [(at, way,
        flow)], its quantities. Returns (it, its ports)."""
        f = self.file
        cls, _type_class, qto, port_type = FITTING[kind]
        label = word[0 if lang == "pt" else 1]
        fitting = api.root.create_entity(f, ifc_class=cls, name="{} {}".format(
            label, len([e for e in f.by_type(cls) if ifcopenshell.util.element.get_predefined_type(e) == predefined
                        and (e.Name or "").startswith(label + " ")]) + 1),     # (0.200: tees and wyes each numbered)
            predefined_type=predefined)
        api.type.assign_type(f, related_objects=[fitting],
                             relating_type=self._fitting_type(self.by_guid(model), kind, lang, predefined, word))
        body = f.createIfcShapeRepresentation(self.body, "Body", rep_type, items)
        api.geometry.assign_representation(f, product=fitting, representation=body)
        self._place(fitting, frame)
        api.spatial.assign_container(f, products=[fitting], relating_structure=self.storey(self.storey_of(model)))
        if qto:
            self._set_qto(fitting, qto, qto_values)
        self._mark(fitting, "fitting")
        made = []
        x = frame[:3, 0]
        for k, (at, way, flow) in enumerate(ports, 1):
            port = api.system.add_port(f, element=fitting)
            port.Name, port.FlowDirection, port.PredefinedType = str(k), flow, port_type
            self._place(port, self._port_frame(at, way, x))
            made.append(port)
        return fitting, made

    def on_axis(self, point, kind, reach, z=None, leave=()):
        """(0.137) A pipe / duct of this kind whose axis passes within `reach` of `point` in plan, with room for a
        tee there (away from its ends): (its GlobalId, the point on its axis (3,): where a level or sloped one
        passes, at its height there; a vertical one at the height z, inside it) — or None. leave: GlobalIds not
        to take (the one being drawn from)."""
        cls = SEGMENT[kind][0]
        p = np.asarray(point, dtype=float)[:2]
        best = None
        for e in self.file.by_type(cls):
            g = e.GlobalId
            if g in leave or self.kind_of(g) != kind:
                continue
            s, end, _z = self.segment_params(g)
            d = end - s
            length, run = float(np.linalg.norm(d)), float(np.linalg.norm(d[:2]))
            margin = max(self._size(e)) + 2 * COLLAR + MIN_PIECE
            if run < 1e-6:                                         # a stack: at the height asked
                gap = float(np.linalg.norm(s[:2] - p))
                lo, hi = sorted((float(s[2]), float(end[2])))
                if z is None or gap > reach or not lo + margin <= z <= hi - margin:
                    continue
                q = np.array((s[0], s[1], float(z)))
            else:
                k = float(np.dot(p - s[:2], d[:2])) / run ** 2       # (how far along, 0 → 1)
                if k * length < margin or (1.0 - k) * length < margin:
                    continue
                q = s + d * k
                gap = float(np.linalg.norm(q[:2] - p))
                if gap > reach:
                    continue
            if best is None or gap < best[0]:
                best = (gap, g, q)
        return None if best is None else (best[1], best[2])

    def add_tee(self, main, branch, lang="pt"):
        """(0.137) `branch` ends on `main`'s axis (or starts from it): `main` is split there and a tee put in —
        a piece in line with it and a stub along the branch —, the branch made shorter to meet it, all connected:
        flowing from the branch into the main when it ends on it (drainage), out of it when it starts on it
        (supply). Returns the tee's GlobalId, or None (no room, or nearly in line)."""
        kind = self.kind_of(main)
        if kind not in FITTING or self.kind_of(branch) != kind:
            return None
        em, eb = self.by_guid(main), self.by_guid(branch)
        sm, endm, _z = self.segment_params(main)
        sb, endb, _z = self.segment_params(branch)
        dm = _unit(endm - sm)
        length = float(np.linalg.norm(endm - sm))
        feet = [(float(np.dot(q - sm, dm)), q) for q in (endb, sb)]
        gaps = [float(np.linalg.norm(sm + dm * k - q)) for k, q in feet]
        into = gaps[0] <= gaps[1]                                   # (the branch ends on it)
        k = feet[0][0] if into else feet[1][0]
        at = sm + dm * k
        out = _unit((sb - endb) if into else (endb - sb))           # from the main out along the branch
        sine = float(np.linalg.norm(np.cross(out, dm)))
        if sine < math.sin(math.radians(MIN_BRANCH_DEG)):
            return None
        half = max(self._size(eb)) / 2 / sine + COLLAR              # half the tee's main piece
        stub = max(self._size(em)) / 2 / sine + COLLAR              # its stub, from the main's axis
        branch_length = float(np.linalg.norm(endb - sb))
        if k - half < MIN_PIECE or length - k - half < MIN_PIECE or branch_length - stub < MIN_PIECE:
            return None
        ports_m = self.ports(main)
        after = self.connected(ports_m[1]) if len(ports_m) == 2 else None
        if after is not None:
            api.system.disconnect_port(self.file, port=ports_m[1])
        # the main: up to the tee, and a new piece after it to where it ended (its connection there kept)
        self._set_length(main, k - half)
        rest = self._segment_like(main, at + dm * half, endm, lang)
        if after is not None:
            self._connect(self.ports(rest.GlobalId)[1], after)
        # the branch: up to the stub's end
        if into:
            self._set_length(branch, branch_length - stub)
        else:
            m = self._placement_si(eb)
            m[:3, 3] += out * stub
            self._place(eb, m)
            self._set_length(branch, branch_length - stub)
        # the tee: its frame the main's at that point; a piece of the main, a stub of the branch
        f, u = self.file, 1.0 / self.unit_scale
        x = self._across(main)
        frame = self._port_frame(at, dm, x)
        rot = frame[:3, :3]
        piece = f.createIfcExtrudedAreaSolid(
            self._profile(em), f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, -half * u)), None, None),
            f.createIfcDirection((0.0, 0.0, 1.0)), 2 * half * u)
        stub_frame = self._port_frame(at, out, self._across(branch))
        z_local, x_local = rot.T @ stub_frame[:3, 2], rot.T @ stub_frame[:3, 0]
        arm = f.createIfcExtrudedAreaSolid(
            self._profile(eb), f.createIfcAxis2Placement3D(
                f.createIfcCartesianPoint((0.0, 0.0, 0.0)), f.createIfcDirection(tuple(float(c) for c in z_local)),
                f.createIfcDirection(tuple(float(c) for c in x_local))),
            f.createIfcDirection((0.0, 0.0, 1.0)), stub * u)
        w, h = self._size(em)
        area = math.pi * w * w / 4 if self._profile(em).is_a("IfcCircleProfileDef") else w * h
        word = _WYE_NAME if sine < math.sin(math.radians(WYE_DEG)) else _TEE_NAME
        tee, (p1, p2, p3) = self._new_fitting(
            main, kind, lang, "JUNCTION", word, [piece, arm], "SweptSolid", frame,
            [(at - dm * half, dm, "SINK"), (at + dm * half, dm, "SOURCE"),
             (at + out * stub, out, "SINK" if into else "SOURCE")],
            {"Length": 2 * half * u, "GrossCrossSectionArea": area})          # (areas: m², as the bends')
        self._connect(self.ports(main)[1], p1)
        self._connect(p2, self.ports(rest.GlobalId)[0])
        ports_b = self.ports(branch)
        if len(ports_b) == 2 and into:
            self._connect(ports_b[1], p3)
        elif len(ports_b) == 2:
            self._connect(p3, ports_b[0])
        system = self.system_of(main)                               # (0.141) the main's piece and its tee: its
        if system is not None:                                      # system (the branch keeps its own)
            self.set_system([rest.GlobalId, tee.GlobalId], system, lang)
        self._last_rest = rest.GlobalId                             # (0.148: what it split off the main)
        return tee.GlobalId

    def add_reducer(self, first, second, lang="pt"):
        """(0.137) `second` goes on in line from `first` but is another size: a reducer between them — a cone for
        pipes, a faceted solid for ducts (both rectangular) —, the two made shorter to meet it, connected.
        Returns its GlobalId, or None (no room; a round and a rectangular duct)."""
        kind = self.kind_of(first)
        e1, e2 = self.by_guid(first), self.by_guid(second)
        p1, p2 = self._profile(e1), self._profile(e2)
        if p1.is_a() != p2.is_a():
            return None
        s1, end1, _z = self.segment_params(first)
        s2, end2, _z = self.segment_params(second)
        d = _unit(end1 - s1)
        (w1, h1), (w2, h2) = self._size(e1), self._size(e2)
        length = 1.5 * max(abs(w1 - w2), abs(h1 - h2)) + 2 * COLLAR
        len1, len2 = float(np.linalg.norm(end1 - s1)), float(np.linalg.norm(end2 - s2))
        if len1 - length / 2 < MIN_PIECE or len2 - length / 2 < MIN_PIECE:
            return None
        corner = end1.copy()
        self._set_length(first, len1 - length / 2)
        m2 = self._placement_si(e2)
        m2[:3, 3] += d * (length / 2)
        self._place(e2, m2)
        self._set_length(second, len2 - length / 2)
        start = corner - d * (length / 2)
        f, u = self.file, 1.0 / self.unit_scale
        frame = self._port_frame(start, d, self._across(first))
        origin = f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)), None, None)
        if p1.is_a("IfcCircleProfileDef"):
            items = [f.createIfcExtrudedAreaSolidTapered(p1, origin, f.createIfcDirection((0.0, 0.0, 1.0)),
                                                         length * u, p2)]
            rep_type = "AdvancedSweptSolid"
        else:                                    # (a tapered rectangle: the kernel doubles a face — faceted instead)
            rings = [[(sx * w / 2 * u, sy * h / 2 * u, z * u) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                     for w, h, z in ((w1, h1, 0.0), (w2, h2, length))]
            pts = [[f.createIfcCartesianPoint(p) for p in ring] for ring in rings]
            faces = [pts[0][::-1], pts[1]] + [[pts[0][i], pts[0][(i + 1) % 4], pts[1][(i + 1) % 4], pts[1][i]]
                                              for i in range(4)]
            shell = f.createIfcClosedShell([f.createIfcFace([f.createIfcFaceOuterBound(f.createIfcPolyLoop(face), True)])
                                            for face in faces])
            items, rep_type = [f.createIfcFacetedBrep(shell)], "Brep"
        area = math.pi * w1 * w1 / 4 if p1.is_a("IfcCircleProfileDef") else w1 * h1
        reducer, (q1, q2) = self._new_fitting(
            first, kind, lang, "TRANSITION", _REDUCER_NAME, items, rep_type, frame,
            [(start, d, "SINK"), (start + d * length, d, "SOURCE")],
            {"Length": length * u, "GrossCrossSectionArea": area})
        ports1, ports2 = self.ports(first), self.ports(second)
        if len(ports1) == 2 and len(ports2) == 2:
            self._connect(ports1[1], q1)
            self._connect(q2, ports2[0])
        return reducer.GlobalId

    def slopes(self, guids):
        """(0.136) {GlobalId: (its middle (3,), the way it falls in plan (2,), its slope, its radius)} of the pipes
        among `guids` that fall along them — a plan writes their slope (level and vertical ones: none)."""
        out = {}
        for g in guids:
            if self.kind_of(g) != "pipe":
                continue
            s, e, _z = self.segment_params(g)
            run = float(np.linalg.norm((e - s)[:2]))
            if run < 1e-6 or abs(float(s[2] - e[2])) / run < 1e-4:
                continue
            down = (e - s)[:2] / run * (1.0 if s[2] > e[2] else -1.0)
            profile = ifcopenshell.util.element.get_material(self.by_guid(g), should_skip_usage=True)
            profile = profile.MaterialProfiles[0].Profile
            r = (profile.Radius if profile.is_a("IfcCircleProfileDef") else profile.YDim / 2) * self.unit_scale
            out[g] = ((s + e) / 2, down, abs(float(s[2] - e[2])) / run, float(r))
        return out

    def free_end_near(self, point, kind, z_hint, reach):
        """(0.136) The free end of a pipe / duct of this kind within `reach` of `point` in plan, at whatever
        height (the one nearest `z_hint`): (its GlobalId, the end (3,)) — a run goes on from there, at its
        height, as in Revit — or None."""
        cls = SEGMENT[kind][0]
        p = np.asarray(point, dtype=float)[:2]
        best = None
        for e in self.file.by_type(cls):
            if self.kind_of(e.GlobalId) != kind:
                continue
            _s, end, _z = self.segment_params(e.GlobalId)
            gap = float(np.linalg.norm(end[:2] - p))
            if gap > reach:
                continue
            ports = self.ports(e.GlobalId)
            if len(ports) != 2 or self.connected(ports[1]) is not None:
                continue
            key = (abs(float(end[2]) - float(z_hint)), gap)
            if best is None or key < best[0]:
                best = (key, e.GlobalId, end)
        return None if best is None else (best[1], best[2])

    def segment_ending_at(self, point, kind, tol=1e-3):
        """A pipe / duct of this kind whose end is at `point` and whose end port is free — to go on from it."""
        cls = SEGMENT[kind][0]
        p = np.asarray(point, dtype=float)
        for e in self.file.by_type(cls):
            if self.kind_of(e.GlobalId) != kind:
                continue
            _s, end, _z = self.segment_params(e.GlobalId)
            if np.linalg.norm(end - p) < tol:
                ports = self.ports(e.GlobalId)
                if len(ports) == 2 and self.connected(ports[1]) is None:
                    return e.GlobalId
        return None
