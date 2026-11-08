"""Editing straight walls (0.104), mixed into IfcModel: split a wall in two, and trim / extend two walls to the
corner where their axes meet (Revit's Split Element and Trim/Extend to Corner).

Split: the part after the point is a copy of the wall (its type, properties, base and top), so both keep what
the wall was; each door, window or opening stays with the part it is in (none may be cut by the split); the
joints at the wall's end and those of the walls met on its side after the point go to the new part; the cut
ends are square. Corner: both walls' ends nearest the crossing go to it and are joined there as a corner drawn
point by point would be (one runs through, the other stops at its face; mitred at other angles)."""

import math

import numpy as np

import ifcopenshell
import ifcopenshell.guid
import ifcopenshell.util.element

from ..core.walls import axis_crossing, find_joint, horizontal_dir, joint, perpendicular
from .edit import MIN_SIZE, MITRE_NAME, EditRefused


class WallEditMixin:
    def _openings_along(self, wall):
        """[(opening, x0, x1)] of a wall's openings along its axis (m from its start). ((0.305) Its level reveals left
        out: they run all along, on every part, made again to fit.)"""
        m = self._placement_si(wall)
        out = []
        for rel in wall.HasOpenings or ():
            opening = rel.RelatedOpeningElement
            reveal = self.reveal_params(opening)
            if reveal is not None and not reveal["vertical"]:
                continue
            lo, hi = self._local_aabb(opening, m)
            out.append((opening, float(lo[0]), float(hi[0])))
        return out

    def _remove_opening(self, opening):
        """An opening of a wall taken away with the door / window in it (as remove does for a wall's)."""
        for fill in list(opening.HasFillings or ()):
            ifcopenshell.api.root.remove_product(self.file, product=fill.RelatedBuildingElement)
        ifcopenshell.api.root.remove_product(self.file, product=opening)

    def split_wall(self, guid, s):
        """The wall split `s` m from its start: it ends there, a new wall goes on from there to its old end.
        Returns the new wall's GlobalId."""
        wall, _ = self._require(guid, "wall")
        length, _h, _t = self.wall_params(guid)
        s = float(s)
        if s < MIN_SIZE - 1e-9 or length - s < MIN_SIZE - 1e-9:
            raise EditRefused("too_small")
        for _o, x0, x1 in self._openings_along(wall):
            if x0 < s - 1e-6 and x1 > s + 1e-6:
                raise EditRefused("split_opening")
        start, end, _t = self.wall_axis(guid)
        d = (end - start) * np.array((1.0, 1.0, 0.0))
        d /= np.linalg.norm(d)
        # the joints that go to the new part: at the wall's end, and those met on its side after the point
        moving = []
        for rel, through, through_end, butt, butt_end in self.wall_joints(guid):
            if through == guid and through_end == "end" or butt == guid and butt_end == "end":
                moving.append(rel)
            elif through == guid and through_end == "path" and self.kind_of(butt) == "wall":
                bs, be, _bt = self.wall_axis(butt)
                at = bs if butt_end == "start" else be
                if float((at - start)[:2] @ d[:2]) > s:
                    moving.append(rel)
        new = self.copy_element(guid)                       # (its doors / windows / openings copied too)
        if self.created is not None and new.GlobalId in self.created:
            self.created.remove(new.GlobalId)               # (not repeated on equal storeys: only this one)
        for opening, x0, _x1 in self._openings_along(new):
            if x0 < s - 1e-6:
                self._remove_opening(opening)               # (before the point: the first part's)
        for opening, x0, _x1 in self._openings_along(wall):
            if x0 >= s - 1e-6:
                self._remove_opening(opening)               # (after it: the new part's)
        for rel in moving:
            if rel.RelatingElement == wall:
                rel.RelatingElement = new
            else:
                rel.RelatedElement = new
        self.resize_wall(guid, at_end=-(length - s), detach=False)
        self.resize_wall(new.GlobalId, at_start=-s, detach=False)
        self.carry_claddings(guid, new.GlobalId, copy=True)     # (its finishes on both parts, 0.119)
        return new.GlobalId

    def split_wall_gap(self, guid, s, gap):
        """(0.300, Revit's Split with Gap) The wall split `s` m from its start with a gap `gap` m wide centred there:
        both parts end square at the gap's sides, not joined to each other. Refused when a door, a window or an
        opening would be in the gap, or a part would be too short. Returns the new part's GlobalId."""
        wall, _ = self._require(guid, "wall")
        length, _h, _t = self.wall_params(guid)
        gap = max(float(gap), 0.0)
        a, b = float(s) - gap / 2, float(s) + gap / 2
        if a < MIN_SIZE - 1e-9 or length - b < MIN_SIZE - 1e-9:
            raise EditRefused("too_small")
        for _o, x0, x1 in self._openings_along(wall):
            if x0 < b - 1e-6 and x1 > a + 1e-6:
                raise EditRefused("split_opening")
        new = self.split_wall(guid, s)
        if gap > 1e-9:
            self.resize_wall(guid, at_end=-gap / 2, detach=False)
            self.resize_wall(new, at_start=-gap / 2, detach=False)
        return new

    def trim_extend_wall(self, guid, boundary, keep):
        """(0.300, Revit's Trim/Extend to a boundary) A straight wall trimmed or extended to where its axis crosses the
        boundary wall's axis line, keeping the side of the point clicked on it (plan): its end on the other side goes
        to the crossing (its joint there let go). Met on the boundary's side: a T, stopped at its face; at its end: a
        corner (unless that end is another corner's); past its ends: on its line, not joined. Returns True when
        joined to the boundary."""
        self._require(guid, "wall")
        self._require(boundary, "wall")
        if guid == boundary:
            raise EditRefused("joint")
        s, e, t = self.wall_axis(guid)
        bs, be, bt = self.wall_axis(boundary)
        d, db = horizontal_dir(s, e), horizontal_dir(bs, be)
        cross = axis_crossing(s, d, bs, db)
        if cross is None:
            raise EditRefused("parallel")
        length = float(np.linalg.norm((e - s)[:2]))
        at = float((cross - s)[:2] @ d[:2])
        kept = float((np.asarray(keep, dtype=float)[:2] - s[:2]) @ d[:2])
        end = "end" if kept < at else "start"           # (the end on the far side of the crossing moves to it)
        if end == "end" and at < MIN_SIZE or end == "start" and length - at < MIN_SIZE:
            raise EditRefused("too_small")
        change = at - length if end == "end" else -at
        if abs(change) > 1e-9:
            self.resize_wall(guid, **{"at_" + end: change})          # (it leaves its joint there)
        else:
            ifcopenshell.api.geometry.disconnect_path(self.file, element=self.by_guid(guid),
                                                      connection_type="ATEND" if end == "end" else "ATSTART")
        along, b_length = float((cross - bs)[:2] @ db[:2]), float(np.linalg.norm((be - bs)[:2]))
        reach = max(t, bt) / 2 + 1e-4
        if abs(along) <= reach:
            where = "start"
        elif abs(along - b_length) <= reach:
            where = "end"
        elif 0 < along < b_length:
            where = "path"
        else:
            return False                                # (past its ends: on its line)
        if where != "path" and self._end_joined(boundary, where):
            return False
        s, e, t = self.wall_axis(guid)
        result = joint((bs, be), bt, where, (s, e), t, end)
        if result is None:
            return False
        if result["through"] is not None:
            self.set_wall_end(boundary, where, *result["through"])
        self.set_wall_end(guid, end, *result["butt"])
        self.connect_walls(boundary, where, guid, end)
        return True

    def merge_walls(self, a, b):
        """Two walls in line, end to end, made one (0.105: the inverse of split): `a` reaches over `b`, takes its
        doors, windows and openings and its joint at its far end; `b` goes. Same type, base and height only."""
        wa, _ = self._require(a, "wall")
        wb, _ = self._require(b, "wall")
        sa, ea, ta = self.wall_axis(a)
        sb, eb, tb = self.wall_axis(b)
        la, ha, _ = self.wall_params(a)
        _lb, hb, _ = self.wall_params(b)
        type_a = ifcopenshell.util.element.get_type(wa)
        if type_a != ifcopenshell.util.element.get_type(wb) or abs(ha - hb) > 1e-6 or abs(sa[2] - sb[2]) > 1e-6:
            raise EditRefused("merge_different")
        d = (ea - sa) * np.array((1.0, 1.0, 0.0))
        d /= np.linalg.norm(d)
        db = (eb - sb) * np.array((1.0, 1.0, 0.0))
        db /= np.linalg.norm(db)
        off = (sb - sa) * np.array((1.0, 1.0, 0.0))
        if abs(d[0] * db[1] - d[1] * db[0]) > 1e-6 or abs(d[0] * off[1] - d[1] * off[0]) > 1e-4:
            raise EditRefused("merge_not_in_line")
        # where b lies along a's axis; it must touch a's start or end
        tb0, tb1 = sorted((float((sb - sa)[:2] @ d[:2]), float((eb - sa)[:2] @ d[:2])))
        if abs(tb0 - la) <= max(ta, tb) + 1e-6:
            a_end, change = "end", tb1 - la
        elif abs(tb1) <= max(ta, tb) + 1e-6:
            a_end, change = "start", -tb0
        else:
            raise EditRefused("merge_apart")
        b_far = "end" if (float((eb - sa)[:2] @ d[:2]) > float((sb - sa)[:2] @ d[:2])) == (a_end == "end") \
            else "start"
        joints = [j for j in self.wall_joints(b)]
        mine = [r for _g, r in self.wall_reveals(a) if not r["vertical"]]
        for g, r in self.wall_reveals(b):               # (0.305) a level reveal both have: a's goes on over b
            if not r["vertical"] and any(q["side"] * r["side"] > 0 and abs(q["at"] - r["at"]) < 1e-6 for q in mine):
                ifcopenshell.api.root.remove_product(self.file, product=self.by_guid(g))
        openings = [(rel.RelatedOpeningElement, self._placement_si(rel.RelatedOpeningElement))
                    for rel in wb.HasOpenings or ()]
        far_cut = self.wall_cuts(wb)[0 if b_far == "start" else 1]
        api_geometry = ifcopenshell.api.geometry
        api_geometry.disconnect_path(self.file, element=wa, connection_type="ATEND" if a_end == "end" else "ATSTART")
        self.resize_wall(a, **({"at_end": change} if a_end == "end" else {"at_start": change}), detach=False)
        for opening, matrix in openings:                    # b's openings go into a, where they are
            for rel in opening.VoidsElements or ():
                rel.RelatingBuildingElement = wa
            opening.ObjectPlacement.PlacementRelTo = wa.ObjectPlacement
            self._place(opening, matrix)
        for rel, through, through_end, butt, butt_end in joints:   # b's joints: its far end's and its side's go to a
            mine = through_end if through == b else butt_end
            other = butt if through == b else through
            if other == a or mine not in (b_far, "path"):
                self.file.remove(rel)
                continue
            kind = "ATPATH" if mine == "path" else ("ATEND" if a_end == "end" else "ATSTART")
            if rel.RelatingElement == wb:
                rel.RelatingElement, rel.RelatingConnectionType = wa, kind
            else:
                rel.RelatedElement, rel.RelatedConnectionType = wa, kind
        # b's far end cut, in a's frame (a cut start turned round is a cut end: 180° less)
        if a_end == "end":
            self.set_wall_cuts(a, end=far_cut if b_far == "end" else far_cut - 180.0)
        else:
            self.set_wall_cuts(a, start=far_cut if b_far == "start" else far_cut + 180.0)
        self.carry_claddings(b, a, flip=float(d[:2] @ db[:2]) < 0)     # (b's finishes go to a, 0.119)
        self.remove([b])
        return a

    def orthogonalize(self, guids, tolerance_deg=5.0):
        """The walls among these that are nearly along the red or green axis (within `tolerance_deg`) turned
        round their middle to be exactly along it (0.105); the walls joined to them meet them again. Returns
        those turned."""
        turned = []
        for guid, off in self.off_square(guids, tolerance_deg):
            s, e, _t = self.wall_axis(guid)
            mid = (s + e) / 2
            c, si = math.cos(math.radians(-off)), math.sin(math.radians(-off))
            m = np.eye(4)
            m[:2, :2] = ((c, -si), (si, c))
            m[:2, 3] = mid[:2] - m[:2, :2] @ mid[:2]
            self.transform(guid, m)
            turned.append(guid)
        if turned:
            self.rejoin(turned)
        return turned

    def off_square(self, guids, tolerance_deg=5.0):
        """(0.325) The straight walls among these nearly along the red or green axis (within `tolerance_deg`) but not
        exactly: [(GlobalId, degrees off)] — what orthogonalize turns."""
        found = []
        for guid in guids:
            if self.kind_of(guid) != "wall":
                continue
            s, e, _t = self.wall_axis(guid)
            angle = math.degrees(math.atan2(e[1] - s[1], e[0] - s[0]))
            off = (angle + 45.0) % 90.0 - 45.0              # how far from the nearest of X / Y
            if 1e-6 <= abs(off) <= tolerance_deg:
                found.append((guid, off))
        return found

    def unjoin_end(self, guid, end):
        """A wall's joint at its "start" / "end" let go (0.105, as Revit's Disallow Join): it stays where it is,
        but no longer follows the wall it met. Returns how many joints went."""
        wall, _ = self._require(guid, "wall")
        gone = 0
        for rel, through, through_end, butt, butt_end in self.wall_joints(guid):
            if (through == guid and through_end == end) or (butt == guid and butt_end == end):
                self.file.remove(rel)
                gone += 1
        del wall
        return gone

    def flip_wall(self, guid):
        """(0.299, Revit's flip arrows) A wall turned inside out about its axis: its layers in the other order — what
        was on one face is on the other (an insulation outside comes inside) —, its body, joints, finishes, doors and
        windows as they are. Its layer set usage's sense and offset change (its own: one shared is made its own
        first). Refused for a wall with no layers."""
        wall, _kind = self._require(guid, "wall", "curved_wall")
        usage = ifcopenshell.util.element.get_material(wall, should_skip_usage=False)
        if usage is None or not usage.is_a("IfcMaterialLayerSetUsage"):
            raise EditRefused("no_layers")
        users = [o for rel in self.file.get_inverse(usage) if rel.is_a("IfcRelAssociatesMaterial")
                 for o in rel.RelatedObjects]
        if len(users) > 1:                                  # (another wall's too: this one gets its own)
            own = ifcopenshell.util.element.copy(self.file, usage)
            for rel in self.file.get_inverse(usage):
                if rel.is_a("IfcRelAssociatesMaterial") and wall in rel.RelatedObjects:
                    rel.RelatedObjects = [o for o in rel.RelatedObjects if o != wall]
            self.file.createIfcRelAssociatesMaterial(ifcopenshell.guid.new(), None, None, None, [wall], own)
            usage = own
        total = sum(float(layer.LayerThickness or 0.0) for layer in usage.ForLayerSet.MaterialLayers or ())
        negative = usage.DirectionSense == "NEGATIVE"
        usage.OffsetFromReferenceLine = float(usage.OffsetFromReferenceLine or 0.0) + (-total if negative else total)
        usage.DirectionSense = "POSITIVE" if negative else "NEGATIVE"

    @staticmethod
    def _past_crossing(axis_a, end_a, axis_b, end_b):
        """(0.299) How far each wall's end reaches past the crossing of the two axes (m, outwards; − short of it)."""
        out = []
        for (s, e), end in ((axis_a, end_a), (axis_b, end_b)):
            d = horizontal_dir(s, e)
            out.append(d * (1.0 if end == "end" else -1.0))
        sa, ea = axis_a
        sb, eb = axis_b
        cross = axis_crossing(sa, horizontal_dir(sa, ea), sb, horizontal_dir(sb, eb))
        if cross is None:
            return 0.0, 0.0
        pa = ea if end_a == "end" else sa
        pb = eb if end_b == "end" else sb
        return float((pa - cross)[:2] @ out[0][:2]), float((pb - cross)[:2] @ out[1][:2])

    def join_free_ends(self, guids):
        """(0.299, Revit's Allow Join) The ends of these walls joined to nothing joined again to the wall they reach,
        as drawing them there would (core/walls.find_joint: within half a thickness) — at its end, a corner; at its
        side, a T — and the corner made. The walls looked at are their storey's. Returns the walls changed."""
        changed = []
        for guid in guids:
            if self.kind_of(guid) not in ("wall", "curved_wall"):
                continue
            if self.kind_of(guid) == "wall":
                storey = self.storey_of(guid)
                others = [g for g in (self.storey_elements(storey) if storey else ())
                          if g != guid and self.kind_of(g) == "wall"]
                for end in ("start", "end"):
                    if self._end_joined(guid, end):
                        continue
                    s, e, t = self.wall_axis(guid)
                    axes = [(g,) + tuple(self.wall_axis(g)) for g in others]
                    found = find_joint(s if end == "start" else e, horizontal_dir(s, e), axes, t)
                    if found is None:
                        continue
                    other, where = found[0], found[1]
                    other_end = "path" if where == "mid" else where
                    if other_end != "path" and self._end_joined(other, other_end):
                        continue                            # (its end is another corner's)
                    os_, oe, ot = self.wall_axis(other)
                    through, through_end, butt, butt_end, mitred = other, other_end, guid, end, False
                    if other_end != "path":                 # (a corner made again as it is: who runs on, a mitre)
                        mine, theirs = self._past_crossing((s, e), end, (os_, oe), other_end)
                        if mine > theirs + 1e-6:
                            through, through_end, butt, butt_end = guid, end, other, other_end
                        mitred = (perpendicular(horizontal_dir(s, e), horizontal_dir(os_, oe))
                                  and abs(mine) < 1e-6 and abs(theirs) < 1e-6)
                    ts, te, tt = self.wall_axis(through)
                    bs, be, tb = self.wall_axis(butt)
                    result = joint((ts, te), tt, through_end, (bs, be), tb, butt_end, mitred=mitred)
                    if result is None:
                        continue
                    if result["through"] is not None:
                        self.set_wall_end(through, through_end, *result["through"])
                    self.set_wall_end(butt, butt_end, *result["butt"])
                    self.connect_walls(through, through_end, butt, butt_end, mitred=mitred)
                    changed += [g for g in (guid, other) if g not in changed]
            for g in self.join_ends(guid):                  # (a corner or a T with a curved wall, 0.189 / 0.246)
                changed += [h for h in (guid, g) if h not in changed]
        return changed

    def corner_joint(self, guid, end):
        """(0.301) The corner (not a T) at a wall's "start" / "end": (relation, through, its end, butt, its end), or
        None."""
        for rel, through, through_end, butt, butt_end in self.wall_joints(guid):
            if "path" in (through_end, butt_end):
                continue
            if (through == guid and through_end == end) or (butt == guid and butt_end == end):
                return rel, through, through_end, butt, butt_end
        return None

    def set_corner(self, guid, end, style):
        """(0.301, Revit's Wall Joins) The corner at a wall's end made another way: "butt" — this wall runs through, the
        other stops at its face — or "mitre". Right-angle corners of straight walls only (at other angles they are
        mitred anyway). The way is kept on the joint (a mitre: its Name), so that it stays when the walls move.
        Returns the corner's other wall."""
        found = self.corner_joint(guid, end)
        if found is None:
            raise EditRefused("no_corner")
        rel, through, through_end, butt, butt_end = found
        if self.kind_of(through) != "wall" or self.kind_of(butt) != "wall":
            raise EditRefused("no_corner")              # (a corner with a curved wall: its exact mitre, 0.189)
        ts, te, _tt = self.wall_axis(through)
        bs, be, _tb = self.wall_axis(butt)
        if not perpendicular(horizontal_dir(ts, te), horizontal_dir(bs, be)):
            raise EditRefused("corner_angle")
        other, other_end = (butt, butt_end) if through == guid else (through, through_end)
        mitred = style == "mitre"
        if not mitred and through != guid:              # (the roles change: this wall runs through now)
            self.file.remove(rel)
            rel = self.connect_walls(guid, end, other, other_end)
            through, through_end, butt, butt_end = guid, end, other, other_end
        rel.Name = MITRE_NAME if mitred else None
        ts, te, t_through = self.wall_axis(through)
        bs, be, t_butt = self.wall_axis(butt)
        result = joint((ts, te), t_through, through_end, (bs, be), t_butt, butt_end, mitred=mitred)
        if result is None:
            raise EditRefused("joint")
        if result["through"] is not None:
            self.set_wall_end(through, through_end, *result["through"])
        self.set_wall_end(butt, butt_end, *result["butt"])
        return other

    def fillet_walls(self, a, keep_a, b, keep_b, radius, spec, height, name, lang="pt", storey=None):
        """(0.452, Revit's «Fillet Arc») Walls a and b trimmed / extended to where an arc of `radius`, tangent to their
        axes on the side of each where it was picked (`keep_*`, plan points), touches them — their joints at those
        ends let go — and a curved wall of the type `spec` along that arc, joined to both. Returns the new wall."""
        from ..core.fillet import fillet
        for g in (a, b):
            self._require(g, "wall")
        sa, ea, _ta = self.wall_axis(a)
        sb, eb, _tb = self.wall_axis(b)
        f = fillet((sa, ea), keep_a, (sb, eb), keep_b, radius=radius)
        if f is None:
            raise EditRefused("parallel")
        reach = float(np.linalg.norm(f.tangents[0] - f.cross))
        if any(reach > room - MIN_SIZE for room in f.room):
            raise EditRefused("too_big")                     # (the radius: further than a wall's other end)
        for g, s, e, end, at in ((a, sa, ea, f.ends[0], f.tangents[0]), (b, sb, eb, f.ends[1], f.tangents[1])):
            d = (e - s) * np.array((1.0, 1.0, 0.0))
            length = float(np.linalg.norm(d))
            pos = float((np.asarray(at, dtype=float) - s[:2]) @ (d[:2] / length))
            change = pos - length if end == "end" else -pos
            if abs(change) > 1e-9:
                self.resize_wall(g, **({"at_end": change} if end == "end" else {"at_start": change}))
            else:
                ifcopenshell.api.geometry.disconnect_path(self.file, element=self.by_guid(g),
                                                          connection_type="ATEND" if end == "end" else "ATSTART")
        z = float(sa[2])
        wall = self.add_curved_wall(spec, (float(f.centre[0]), float(f.centre[1]), z), f.radius, f.start, f.sweep,
                                    height, name, lang, storey=storey)
        self.join_ends(wall.GlobalId)
        return wall

    def fillet_ends(self, guid):
        """(0.459) The straight walls going on from a curved wall's two ends along it — as a fillet's, tangent there:
        [(their GlobalId, their other end (axis point)) at its start, the same at its end] — or None when it is not
        so at both (a circle, an arc standing alone)."""
        from ..core import arcs
        centre, radius, start, sweep, _h, _t = self.curved_wall_params(guid)
        if arcs.is_full(sweep):
            return None
        out = []
        for angle in (start, start + sweep):
            p = np.asarray(arcs.point_at(centre, radius, angle), dtype=float)
            radial = (p - np.asarray(centre, dtype=float)[:2]) / radius
            found = None
            for w in self.file.by_type("IfcWall"):
                g = w.GlobalId
                if g == guid or self.kind_of(g) != "wall":
                    continue
                try:
                    s, e, _th = self.wall_axis(g)
                except (KeyError, ValueError, TypeError, AttributeError):
                    continue
                for near, far in ((s, e), (e, s)):
                    d = (far - near)[:2]
                    n = float(np.linalg.norm(d))
                    if n > MIN_SIZE and float(np.linalg.norm(near[:2] - p)) <= 2e-3 and abs(float(d @ radial)) / n <= 5e-3:
                        found = (g, far.copy())
                        break
                if found:
                    break
            if found is None:
                return None
            out.append(found)
        return out if out[0][0] != out[1][0] else None

    def refillet_wall(self, guid, radius):
        """(0.459, the owner: «Selecionei um arco na parede, mas não tem cota temporária para ajustar») A fillet's
        curved wall made again with `radius`, as Revit's: still tangent to the two straight walls at its ends — they are
        trimmed or extended to where the new arc touches them, its centre along their corner's bisector —, joined to
        them again; its doors and windows kept on it. False when it is not a fillet's (fillet_ends)."""
        from ..core.fillet import fillet
        ends = self.fillet_ends(guid)
        if ends is None:
            return False
        wall, _ = self._require(guid, "curved_wall")
        centre0, _r, _s, _sw, height, thickness = self.curved_wall_params(guid)
        (a, far_a), (b, far_b) = ends
        sa, ea, _ta = self.wall_axis(a)
        sb, eb, _tb = self.wall_axis(b)
        f = fillet((sa, ea), far_a, (sb, eb), far_b, radius=float(radius))
        if f is None:
            raise EditRefused("parallel")
        reach = float(np.linalg.norm(f.tangents[0] - f.cross))
        if any(reach > room - MIN_SIZE for room in f.room):
            raise EditRefused("too_big")
        if f.radius - thickness / 2 < MIN_SIZE:
            raise EditRefused("too_small")
        for rel, *_rest in self.wall_joints(guid):           # (its corners let go: made again at its new ends)
            self.file.remove(rel)
        for g, s, e, end, at in ((a, sa, ea, f.ends[0], f.tangents[0]), (b, sb, eb, f.ends[1], f.tangents[1])):
            d = (e - s) * np.array((1.0, 1.0, 0.0))
            length = float(np.linalg.norm(d))
            pos = float((np.asarray(at, dtype=float) - s[:2]) @ (d[:2] / length))
            change = pos - length if end == "end" else -pos
            if abs(change) > 1e-9:
                self.resize_wall(g, **({"at_end": change} if end == "end" else {"at_start": change}))
        m = np.eye(4)
        m[:3, 0] = (math.cos(f.start), math.sin(f.start), 0.0)
        m[:3, 1] = (-math.sin(f.start), math.cos(f.start), 0.0)
        m[:3, 3] = (float(f.centre[0]), float(f.centre[1]), float(centre0[2]))
        self._place(wall, m)
        self._set_params(wall, {"CorteInicio": 180.0, "CorteFim": 0.0})
        self._set_curved_body(wall, float(f.radius), float(f.sweep), height, thickness)
        self._set_params(wall, {"Raio": float(f.radius), "Abertura": math.degrees(f.sweep)})
        self.follow_curved_openings(guid)
        self.join_ends(guid)
        return True

    def corner_walls(self, a, keep_a, b, keep_b):
        """Trim / extend walls a and b to the corner where their axes cross, keeping the side of each where
        the point clicked on it is (plan points). Their other joints at those ends are let go."""
        for g in (a, b):
            self._require(g, "wall")
        sa, ea, ta = self.wall_axis(a)
        sb, eb, tb = self.wall_axis(b)
        da = (ea - sa) * np.array((1.0, 1.0, 0.0))
        db = (eb - sb) * np.array((1.0, 1.0, 0.0))
        cross = axis_crossing(sa, da / np.linalg.norm(da), sb, db / np.linalg.norm(db))
        if cross is None:
            raise EditRefused("parallel")
        ends = {}
        for g, s, e, keep in ((a, sa, ea, keep_a), (b, sb, eb, keep_b)):
            d = (e - s) * np.array((1.0, 1.0, 0.0))
            length = float(np.linalg.norm(d))
            d /= length
            at = float((cross - s)[:2] @ d[:2])
            kept = float((np.asarray(keep, dtype=float)[:2] - s[:2]) @ d[:2])
            end = "end" if kept < at else "start"          # (the end on the crossing's side moves to it)
            if end == "end":
                change, side = at - length, {"at_end": at - length}
            else:
                change, side = -at, {"at_start": -at}
            if end == "end" and at < MIN_SIZE or end == "start" and length - at < MIN_SIZE:
                raise EditRefused("too_small")
            if abs(change) > 1e-9:
                self.resize_wall(g, **side)                 # (it leaves its joint there: detach)
            else:
                ifcopenshell.api.geometry.disconnect_path(self.file, element=self.by_guid(g),
                                                          connection_type="ATEND" if end == "end" else "ATSTART")
            ends[g] = end
        sa, ea, ta = self.wall_axis(a)
        sb, eb, tb = self.wall_axis(b)
        result = joint((sa, ea), ta, ends[a], (sb, eb), tb, ends[b])
        if result is None:
            raise EditRefused("joint")
        if result["through"] is not None:
            self.set_wall_end(a, ends[a], *result["through"])
        self.set_wall_end(b, ends[b], *result["butt"])
        self.connect_walls(a, ends[a], b, ends[b])
