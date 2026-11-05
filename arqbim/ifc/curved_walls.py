"""Curved walls (0.103), mixed into IfcModel: an IfcWall along an arc or a whole circle, with the wall type's
layers (IfcMaterialLayerSetUsage centred on its axis) — its body the plan between the two arcs extruded up (an
IfcIndexedPolyCurve with IfcArcIndex: true arcs) or, a whole circle, an IfcCircleHollowProfileDef; its Axis an
IfcTrimmedCurve on an IfcCircle (or the IfcCircle). Qto_WallBaseQuantities (its length along the axis).

Its placement is the circle's centre at its base, its x towards its start; ArqSynth_Parametros: Elemento
"curved_wall", Raio (the axis), Abertura (degrees, positive counter-clockwise; 360: a circle). Moving and turning
it is moving its placement. It is a kind of its own: what straight walls do (corners, Push/Pull on their ends) is
left out of it for now. (0.177) Its doors and windows: straight, in the frame tangent to its axis at their middle,
their openings deep enough to go through; they keep their distance along it when it changes."""

import math

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import arcs
from ..core.curved_joints import arc_cut, arc_end, corner, cut_band, cut_ends, straight_end, tee
from ..core.walls import cut_angle
from .edit import EditRefused, MIN_SIZE

api = ifcopenshell.api


class CurvedWallMixin:
    def curved_wall_params(self, guid):
        """(centre (x, y, z), radius, start angle, sweep (radians), height, thickness) of a curved wall."""
        e = self.by_guid(guid)
        p = self._params(e)
        m = self._placement_si(e)
        q = ifcopenshell.util.element.get_psets(e).get("Qto_WallBaseQuantities", {})
        s = self.unit_scale
        start = math.atan2(m[1, 0], m[0, 0])
        return (m[:3, 3].copy(), float(p["Raio"]), start, math.radians(float(p["Abertura"])),
                float(q["Height"]) * s, float(q["Width"]) * s)

    def _set_curved_body(self, wall, radius, sweep, height, thickness):
        f, u = self.file, 1.0 / self.unit_scale
        if radius - thickness / 2 < MIN_SIZE / 2:
            raise EditRefused("too_small")
        self._clear_representations(wall)
        ro, ri = (radius + thickness / 2) * u, (radius - thickness / 2) * u
        origin2 = f.createIfcAxis2Placement2D(f.createIfcCartesianPoint((0.0, 0.0)), None)
        if arcs.is_full(sweep):
            profile = f.createIfcCircleHollowProfileDef("AREA", None, origin2, float(ro), float(thickness * u))
            axis_curve = f.createIfcCircle(origin2, float(radius * u))
        else:
            # (0.189) its ends cut for a corner: its outer and inner faces end where the cut line crosses them
            (o0, i0), (o1, i1) = cut_ends(radius, sweep, thickness, *self.wall_cuts(wall))
            pts = [(ro * math.cos(a), ro * math.sin(a)) for a in (o0, (o0 + o1) / 2, o1)] + \
                [(ri * math.cos(a), ri * math.sin(a)) for a in (i1, (i0 + i1) / 2, i0)]
            curve = f.createIfcIndexedPolyCurve(
                f.createIfcCartesianPointList2D([(float(x), float(y)) for x, y in pts]),
                [f.createIfcArcIndex((1, 2, 3)), f.createIfcLineIndex((3, 4)), f.createIfcArcIndex((4, 5, 6)),
                 f.createIfcLineIndex((6, 1))], False)
            profile = f.createIfcArbitraryClosedProfileDef("AREA", None, curve)
            # the axis: the circle trimmed by its angles (in the project's plane angle unit: radians)
            a0, a1 = (0.0, sweep) if sweep > 0 else (sweep, 0.0)
            axis_curve = f.createIfcTrimmedCurve(f.createIfcCircle(origin2, float(radius * u)),
                                                 [f.createIfcParameterValue(float(a0))],
                                                 [f.createIfcParameterValue(float(a1))], True, "PARAMETER")
        solid = f.createIfcExtrudedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)),
                                                 f.createIfcDirection((0.0, 0.0, 1.0)),
                                                 f.createIfcDirection((1.0, 0.0, 0.0))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(height * u))
        api.geometry.assign_representation(f, product=wall, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", [solid]))
        api.geometry.assign_representation(f, product=wall, representation=f.createIfcShapeRepresentation(
            self.axis, self.axis.ContextIdentifier, "Curve2D", [axis_curve]))
        length = radius * abs(sweep)
        area = abs(sweep) / 2 * ((radius + thickness / 2) ** 2 - (radius - thickness / 2) ** 2)
        self._set_qto(wall, "Qto_WallBaseQuantities", {"Length": length * u, "Height": height * u,
                                                       "Width": thickness * u, "GrossVolume": area * height})

    def add_curved_wall(self, spec, centre, radius, start, sweep, height, name, lang="pt", storey=None):
        """A curved wall of the wall type `spec`: its axis the arc (centre (x, y, z: its base), radius, start
        angle, sweep — radians; ±2π a circle). Returns the IfcWall."""
        f = self.file
        if radius * abs(sweep) < MIN_SIZE or height < MIN_SIZE:
            raise EditRefused("too_small")
        type_ = self.ensure_type(spec, lang)
        wall = api.root.create_entity(f, ifc_class="IfcWall", name=name)
        api.type.assign_type(f, related_objects=[wall], relating_type=type_)
        usage = ifcopenshell.util.element.get_material(wall, should_skip_usage=False)
        if usage is not None and usage.is_a("IfcMaterialLayerSetUsage"):
            usage.OffsetFromReferenceLine = -spec.thickness / 2 / self.unit_scale    # (centred on the axis)
        m = np.eye(4)
        m[:3, 0] = (math.cos(start), math.sin(start), 0.0)
        m[:3, 1] = (-math.sin(start), math.cos(start), 0.0)
        m[:3, 3] = (float(centre[0]), float(centre[1]), float(centre[2]))
        self._place(wall, m)
        container = self.storey(storey) if storey is not None else self.storey_at(float(centre[2]))
        api.spatial.assign_container(f, products=[wall], relating_structure=container)
        self._set_curved_body(wall, float(radius), float(sweep), float(height), spec.thickness)
        common = api.pset.add_pset(f, product=wall, name="Pset_WallCommon")
        api.pset.edit_pset(f, pset=common, properties={"IsExternal": False, "LoadBearing": False})
        self._mark(wall, "curved_wall")
        self._set_params(wall, {"Raio": float(radius), "Abertura": math.degrees(sweep)})
        return wall

    def set_curved_wall(self, guid, radius=None, sweep=None, height=None, thickness=None):
        """A curved wall's axis radius, sweep (radians; its start stays), height or thickness (its type) changed."""
        wall, _ = self._require(guid, "curved_wall")
        _c, r0, _start, s0, h0, t0 = self.curved_wall_params(guid)
        radius = r0 if radius is None else float(radius)
        sweep = s0 if sweep is None else float(sweep)
        height = h0 if height is None else float(height)
        thickness = t0 if thickness is None else float(thickness)
        if radius * abs(sweep) < MIN_SIZE or height < MIN_SIZE or abs(sweep) > arcs.FULL + 1e-9:
            raise EditRefused("too_small")
        # (0.189) an end that moves leaves its corner, square again (as a straight wall's, resize_wall)
        moved = {"start", "end"} if abs(radius - r0) > 1e-9 else ({"end"} if abs(sweep - s0) > 1e-9 else set())
        if moved:
            for rel, a, ea, b, eb in self.wall_joints(guid):
                if (a == guid and ea in moved) or (b == guid and eb in moved):
                    self.file.remove(rel)
            start_cut, end_cut = self.wall_cuts(wall)
            self._set_params(wall, {"CorteInicio": 180.0 if "start" in moved else start_cut,
                                    "CorteFim": 0.0 if "end" in moved else end_cut})
        self._set_curved_body(wall, radius, sweep, height, thickness)
        self._set_params(wall, {"Raio": radius, "Abertura": math.degrees(sweep)})
        self.follow_curved_openings(guid)                   # (0.177) its doors and windows kept on it
        if abs(thickness - t0) > 1e-9 or abs(radius - r0) > 1e-9:
            self.rejoin([guid])         # (0.189) thicker / thinner: its corners made again — (0.246) its Ts, its radius

    def curved_wall_band(self, guid):
        """A curved wall's plan as polygons (the rooms, the magic wand) — (0.189) its ends cut as its body's."""
        centre, radius, start, sweep, _h, thickness = self.curved_wall_params(guid)
        start_cut, end_cut = self.wall_cuts(guid)
        if arcs.is_full(sweep) or (start_cut, end_cut) == (180.0, 0.0):
            return arcs.band(centre, radius, start, sweep, thickness)
        return cut_band(centre, radius, start, sweep, thickness, start_cut, end_cut, arcs.SEGMENT_DEG)

    # ------------------------------------------------------------ corners (0.189)

    def joint_end(self, guid, end):
        """A wall's (straight or curved) "start" / "end" as a corner sees it (core/curved_joints.End), or None (a
        whole circle has no ends)."""
        kind = self.kind_of(guid)
        if kind == "wall":
            s, e, thickness = self.wall_axis(guid)
            d = (e - s) * np.array((1.0, 1.0, 0.0))
            d /= np.linalg.norm(d)
            return straight_end(s, d, thickness) if end == "start" else straight_end(e, -d, thickness)
        if kind != "curved_wall":
            return None
        centre, radius, start, sweep, _h, thickness = self.curved_wall_params(guid)
        if arcs.is_full(sweep):
            return None
        turn = math.copysign(1.0, sweep)
        if end == "start":
            return arc_end(centre[:2], radius, start, turn, thickness, float(centre[2]))
        return arc_end(centre[:2], radius, start + sweep, -turn, thickness, float(centre[2]))

    def set_curved_end(self, guid, end, angle, cut):
        """A curved wall's "start" / "end" brought to the axis point at `angle` (radians; the other end stays), cut
        at `cut` degrees (core/curved_joints.arc_cut). Its doors and windows stay where they are."""
        wall, _ = self._require(guid, "curved_wall")
        centre, radius, start, sweep, height, thickness = self.curved_wall_params(guid)
        start_cut, end_cut = self.wall_cuts(wall)
        at = start if end == "start" else start + sweep
        delta = (float(angle) - at + math.pi) % (2 * math.pi) - math.pi
        if end == "start":
            start, sweep, start_cut = start + delta, sweep - delta, float(cut)
            moved = delta * math.copysign(1.0, sweep) * radius       # (the start went this far along it)
            for opening in self._curved_openings(wall):
                p = self._params(opening)
                self._set_params(opening, {"AoLongo": float(p["AoLongo"]) - moved})
            m = self._placement_si(wall)
            m[:3, 0] = (math.cos(start), math.sin(start), 0.0)
            m[:3, 1] = (-math.sin(start), math.cos(start), 0.0)
            self._place(wall, m)
        else:
            sweep, end_cut = sweep + delta, float(cut)
        if radius * abs(sweep) < MIN_SIZE:
            raise EditRefused("too_small")
        self._set_params(wall, {"Abertura": math.degrees(sweep), "CorteInicio": start_cut, "CorteFim": end_cut})
        self._set_curved_body(wall, radius, sweep, height, thickness)
        self.follow_curved_openings(guid)

    def _curved_openings(self, wall):
        return [rel.RelatedOpeningElement for rel in wall.HasOpenings or ()
                if "AoLongo" in self._params(rel.RelatedOpeningElement)]

    def _end_joined(self, guid, end):
        return any((a == guid and ea == end) or (b == guid and eb == end)
                   for _r, a, ea, b, eb in self.wall_joints(guid))

    def join_ends(self, guid):
        """The ends of a wall that meet another wall's end — one of the two curved (straight walls join by
        themselves, core/walls) — joined to it in a corner (recorded as theirs are, and made). Returns the walls
        joined to."""
        joined = []
        walls = [w.GlobalId for w in self.file.by_type("IfcWall")
                 if w.GlobalId != guid and self.kind_of(w.GlobalId) in ("wall", "curved_wall")]
        mine_curved = self.kind_of(guid) == "curved_wall"
        for my_end in ("start", "end"):
            a = self.joint_end(guid, my_end)
            if a is None or self._end_joined(guid, my_end):
                continue
            found = None
            for other in walls:
                if not mine_curved and self.kind_of(other) != "curved_wall":
                    continue
                for other_end in ("start", "end"):
                    b = self.joint_end(other, other_end)
                    if b is None or abs(a.point[2] - b.point[2]) > 1e-4 or \
                            np.linalg.norm((a.point - b.point)[:2]) > max(a.thickness, b.thickness) / 2 + 1e-4:
                        continue
                    if not self._end_joined(other, other_end) and corner(a, b) is not None:
                        found = (other, other_end)
                        break
                if found:
                    break
            if found:
                self.connect_walls(found[0], found[1], guid, my_end)
                self.rejoin([guid])
                joined.append(found[0])
        joined += self._join_tees(guid, walls)
        return joined

    def _join_tees(self, guid, walls):
        """(0.246) The T junctions of a straight wall's free ends with a curved wall's side — those of this wall's
        ends, or (a curved wall) of the straight walls' ends at its side: joined (the curved wall runs on, "path";
        the straight one stops on its face) and made. Returns the walls joined to."""
        mine = self.kind_of(guid)
        if mine == "wall":
            pairs = [(other, guid, end) for other in walls if self.kind_of(other) == "curved_wall"
                     for end in ("start", "end")]
        elif mine == "curved_wall":
            pairs = [(guid, other, end) for other in walls if self.kind_of(other) == "wall" for end in ("start", "end")]
        else:
            return []
        joined = []
        for curved, straight, end in pairs:
            if self._end_joined(straight, end):
                continue
            a = self.joint_end(straight, end)
            centre, radius, start, sweep, _h, thickness = self.curved_wall_params(curved)
            if a is None or abs(a.point[2] - float(centre[2])) > 1e-4 or \
                    tee(a, centre[:2], radius, thickness, start, sweep) is None:
                continue
            self.connect_walls(curved, "path", straight, end)
            self.rejoin([straight])
            joined.append(straight if curved == guid else curved)
        return joined

    def _curved_tee(self, rel, curved, straight, end):
        """(0.246) A T with a curved wall made again (rejoin): the straight wall's end on its face; or let go."""
        a = self.joint_end(straight, end)
        centre, radius, start, sweep, _h, thickness = self.curved_wall_params(curved)
        result = tee(a, centre[:2], radius, thickness, start, sweep) if a is not None else None
        if result is None:
            self.file.remove(rel)                 # they no longer meet: the walls stay as they are
            return
        point, normal = result
        s, e, _t = self.wall_axis(straight)
        x = (e - s) * np.array((1.0, 1.0, 0.0))
        self.set_wall_end(straight, end, point, cut_angle(normal, x / np.linalg.norm(x)))

    def _curved_corner(self, rel, first, first_end, second, second_end):
        """A corner with a curved wall made again (rejoin): both cut on the exact mitre; or the joint let go."""
        a, b = self.joint_end(first, first_end), self.joint_end(second, second_end)
        result = corner(a, b) if a is not None and b is not None else None
        if result is None:
            self.file.remove(rel)                 # they no longer meet: the walls stay as they are
            return
        for guid, end, (point, normal) in ((first, first_end, result[0]), (second, second_end, result[1])):
            if self.kind_of(guid) == "wall":
                s, e, _t = self.wall_axis(guid)
                x = (e - s) * np.array((1.0, 1.0, 0.0))
                self.set_wall_end(guid, end, point, cut_angle(normal, x / np.linalg.norm(x)))
            else:
                centre, _r, start, sweep, _h, _t = self.curved_wall_params(guid)
                angle = math.atan2(point[1] - centre[1], point[0] - centre[0])
                self.set_curved_end(guid, end, angle, arc_cut(angle, sweep, normal))

    # ------------------------------------------------------------ doors and windows (0.177)

    def curved_frame(self, guid, along, width):
        """The WallFrame of a curved wall at an opening's middle, `along` m from its start: tangent to its axis
        there (core/arcs.tangent_frame), x0..length just round the opening, its faces at ±thickness/2."""
        from ..core.openings import EDGE_CLEARANCE, WallFrame
        centre, radius, start, sweep, height, thickness = self.curved_wall_params(guid)
        m = arcs.tangent_frame(centre, radius, arcs.angle_along(start, sweep, radius, along))
        return WallFrame(m, width + 2 * EDGE_CLEARANCE, -width / 2 - EDGE_CLEARANCE, -thickness / 2, thickness / 2,
                         0.0, height)

    def add_curved_opening(self, wall_guid, spec, along, side, name, lang="pt", bare=False):
        """A door or window (or, bare, only its hole) in a curved wall, its middle `along` m from the wall's start,
        turned to the face `side` (−1 the outer, +1 the inner): straight, in the frame tangent there, its opening
        cut deep enough to go through where the wall turns in at its edges. The opening keeps where it is
        (ArqSynth_Parametros: AoLongo, Lado, Largura, Altura, Peitoril), so that it follows the wall. Returns the
        door / window, or the opening when bare."""
        centre, radius, start, sweep, height, thickness = self.curved_wall_params(wall_guid)
        width = spec.width
        cut = arcs.opening_depth(radius, thickness, width)
        if cut is None or spec.sill + spec.height > height + 1e-9:
            raise EditRefused("too_small")
        frame = self.curved_frame(wall_guid, along, width)
        if bare:
            made = opening = self.add_void(wall_guid, frame.matrix, (-width / 2, cut[0], spec.sill),
                                           (width / 2, cut[1], spec.sill + spec.height), name)
        else:
            made = self.add_opening(wall_guid, spec, frame, -width / 2, side, name, lang, cut=cut)
            opening = made.FillsVoids[0].RelatingOpeningElement
        self._set_params(opening, {"AoLongo": float(along), "Lado": 1 if side > 0 else -1, "Largura": float(width),
                                   "Altura": float(spec.height), "Peitoril": float(spec.sill)})
        return made

    def follow_curved_openings(self, guid):
        """A curved wall changed (its radius, sweep, thickness): its doors and windows — (0.252) and curtain walls —
        put back at the same distance along it — refused when one would fall off its end."""
        wall = self.by_guid(guid)
        centre, radius, start, sweep, height, thickness = self.curved_wall_params(guid)
        length = radius * abs(sweep)
        for rel in wall.HasOpenings or ():
            opening = rel.RelatedOpeningElement
            p = self._params(opening)
            if p.get("AoLongo") is None:
                continue
            curtains = [fl.RelatedBuildingElement for fl in opening.HasFillings or ()
                        if fl.RelatedBuildingElement.is_a("IfcCurtainWall")]
            if curtains:            # (0.252) a curtain wall in it: as far along, as far off its axis, its own length
                self._refit_arc_curtain(curtains[0].GlobalId, guid, float(p["AoLongo"]), float(p["Peitoril"]),
                                        float(p.get("Desvio") or 0.0), int(p.get("Sentido") or 1) > 0)
                continue
            along, width = float(p["AoLongo"]), float(p["Largura"])
            h, sill, side = float(p["Altura"]), float(p["Peitoril"]), int(p.get("Lado") or -1)
            cut = arcs.opening_depth(radius, thickness, width)
            if cut is None or (not arcs.is_full(sweep) and not width / 2 <= along <= length - width / 2) or \
                    sill + h > height + 1e-9:
                raise EditRefused("opening_outside")
            frame = self.curved_frame(guid, along, width)
            # (0.294: as an arched door's / window's, its arch's outline)
            self._set_box_body(opening, frame.matrix, (-width / 2, cut[0], sill), (width / 2, cut[1], sill + h))
            for fill in opening.HasFillings or ():
                local = _shift(-width / 2, frame.y0, sill) if side < 0 else \
                    _shift(width / 2, frame.y1, sill) @ np.diag((-1.0, -1.0, 1.0, 1.0))
                self._place(fill.RelatedBuildingElement, frame.matrix @ local)


    def _refit_curved_filling(self, guid, st, s, sill, width, height):
        """A door / window of a curved wall put again — its left edge `s` m along the arc, its sill, its size (moved
        in its Properties, another type, flipped): in the frame tangent at its new middle."""
        wall = st["wall"]
        _c, radius, _start, _sweep, _h, thickness = self.curved_wall_params(wall)
        cut = arcs.opening_depth(radius, thickness, width)
        if cut is None:
            raise EditRefused("outside_wall")
        along = s + width / 2
        frame = self.curved_frame(wall, along, width)
        self._set_box_body(st["opening"], frame.matrix, (-width / 2, cut[0], sill), (width / 2, cut[1], sill + height))
        self._place_filling(self.by_guid(guid), frame.matrix, -width / 2, width / 2, sill, (frame.y0, frame.y1),
                            st["side"])
        self._set_params(st["opening"], {"AoLongo": float(along), "Largura": float(width), "Altura": float(height),
                                         "Peitoril": float(sill), "Lado": 1 if st["side"] > 0 else -1})


def unrolled_frame(centre, radius, start, sweep, height, thickness):
    """(0.177) A curved wall unrolled, for its doors' and windows' distances: x along its arc from its start (its
    length the arc's), its faces at ±thickness/2 — its matrix the frame tangent at its start."""
    from ..core.openings import WallFrame
    return WallFrame(arcs.tangent_frame(centre, radius, start), radius * abs(sweep), 0.0, -thickness / 2,
                     thickness / 2, 0.0, height)


def _shift(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m
