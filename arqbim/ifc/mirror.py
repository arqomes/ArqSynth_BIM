"""Mirror (0.108), mixed into IfcModel: an element reflected about a vertical plane (a line in plan).

An IFC placement cannot be a mirror image (its axes are right-handed), so each kind is reflected through what
defines it:
    a straight wall    drawn the other way round from the reflected end: its layers stay on their side of it,
                       its end cuts change ends; its doors and windows go to the reflected place along it and
                       a door's hinges change hands;
    a curved wall      its centre reflected, its arc turning the other way;
    a column, a pile,  their placement reflected (its x reflected, z up): a symmetric section is its own mirror
    a ramp, a footing  image;
    a beam             its two ends reflected;
    a slab             its outline reflected (no openings in it).
Other elements are not mirrored (mirrorable says which are)."""

import numpy as np

import ifcopenshell
import ifcopenshell.util.element

from ..core import arcs
from .edit import MARGIN, EditRefused, _hand, _with_hand

MIRRORABLE = ("wall", "curved_wall", "column", "pile", "ramp", "footing", "beam", "slab", "roof", "drain", "stair",
              "railing", "curtain_wall", "ceiling", "cladding", "light", "profile")
Z = np.array((0.0, 0.0, 1.0))


def reflection(a, b):
    """The 4x4 reflection about the vertical plane through the plan line a -> b."""
    a = np.array((float(a[0]), float(a[1])))
    d = np.array((float(b[0]), float(b[1]))) - a
    d /= np.linalg.norm(d)
    r = 2 * np.outer(d, d) - np.eye(2)
    m = np.eye(4)
    m[:2, :2] = r
    m[:2, 3] = a - r @ a
    return m


def _frame(origin, x):
    """A right-handed placement: origin, x (horizontal), z up."""
    x = np.array((float(x[0]), float(x[1]), 0.0))
    x /= np.linalg.norm(x)
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, np.cross(Z, x), Z, np.asarray(origin, dtype=float)
    return m


class MirrorMixin:
    def mirrorable(self, guid):
        return self.kind_of(guid) in MIRRORABLE

    def mirror_element(self, guid, mat, lang="pt"):
        """Reflect an element in place by the reflection `mat` (see reflection)."""
        kind = self.kind_of(guid)
        if kind not in MIRRORABLE:
            raise EditRefused("not_mirrorable")
        r = mat[:3, :3]
        point = lambda p: (mat @ np.append(np.asarray(p, dtype=float)[:3], 1.0))[:3]    # noqa: E731
        e = self.by_guid(guid)
        if kind == "wall":
            self._mirror_wall(guid, mat, lang)
        elif kind == "curved_wall":
            centre, radius, start, sweep, height, thickness = self.curved_wall_params(guid)
            a = r @ np.array((np.cos(start), np.sin(start), 0.0))
            self._place(e, _frame(point(centre), a))
            start_cut, end_cut = self.wall_cuts(e)               # (0.189) its corners' cuts: a mirror image
            self._set_params(e, {"Abertura": float(np.degrees(-sweep)), "CorteInicio": -start_cut,
                                 "CorteFim": -end_cut})
            self._set_curved_body(e, radius, -sweep, height, thickness)
            self.follow_curved_openings(guid)
        elif kind == "ceiling":                        # (0.118) its outline and holes reflected
            p = self.ceiling_params(guid)
            ring = [tuple(point((x, y, 0.0))[:2]) for x, y in p["outline"]][::-1]
            holes = [[tuple(point((x, y, 0.0))[:2]) for x, y in h][::-1] for h in p["holes"]]
            x0, y0 = min(x for x, _y in ring), min(y for _x, y in ring)
            m = np.eye(4)
            m[:3, 3] = (x0, y0, p["z"])
            self._place(e, m)
            text = lambda pts: ";".join("{:.6f},{:.6f}".format(x - x0, y - y0) for x, y in pts)   # noqa: E731
            self._set_params(e, {"Contorno": text(ring), "Furos": "|".join(text(h) for h in holes)})
            self._set_ceiling_body(e)
        elif kind == "curtain_wall":                   # (0.117) along its line the other way (symmetric)
            p = self.curtain_params(guid)
            if p["radius"] is not None:                # (0.252) on an arc: its centre reflected, turning the other way
                self._place(e, _frame(point(p["centre"]), r @ (p["start"] - p["centre"])))
                self._set_params(e, {"Abertura": float(np.degrees(-p["sweep"]))})
                self._set_curtain_body(e)
            else:
                self._place(e, _frame(point(p["end"]), -(r @ (p["end"] - p["start"]))))
        elif kind == "cladding":                       # (0.119) it follows its wall (made again on it after)
            pass
        elif kind in ("column", "pile", "ramp", "drain", "light"):
            m = self._placement_si(e)
            self._place(e, _frame(point(m[:3, 3]), r @ m[:3, 0]))
        elif kind == "railing":                        # (0.115) its path reflected
            world = [point(q) for q in self.railing_params(guid)["path"]]
            m = np.eye(4)
            m[:3, 3] = world[0]
            self._place(e, m)
            self._set_params(e, {"Caminho": ";".join("{:.6f},{:.6f},{:.6f}".format(*(q - world[0])) for q in world)})
            self._set_railing_body(e)
        elif kind == "profile":                        # (0.174) its path reflected — the other way, its side kept
            from .profiles import _ring_text
            p = self.profile_params(guid)
            rings = [[tuple(point((x, y, 0.0))[:2]) for x, y in r][::-1] for r in p["rings"]]
            x0, y0 = rings[0][0]
            m = np.eye(4)
            m[:3, 3] = (x0, y0, p["level"])
            self._place(e, m)
            changes = {"Caminho": "|".join(_ring_text([(x - x0, y - y0) for x, y in r]) for r in rings)}
            if p["room"] is not None:
                q = point((p["room"][0], p["room"][1], 0.0))
                changes.update(SalaX=float(q[0]) - x0, SalaY=float(q[1]) - y0)
            self._set_params(e, changes)
            self._set_run_body(e)
        elif kind == "stair":                          # (0.114) reflected: an L / a U turns the other way
            m = self._placement_si(e)
            self._place(e, _frame(point(m[:3, 3]), r @ m[:3, 0]))
            p = self.stair_params(guid)
            self.set_stair(guid, turn="right" if p["turn"] == "left" else "left")
        elif kind == "footing":
            centre, x, length, width, top = self.footing_params(guid)
            depth = top - float(self._placement_si(e)[2, 3])
            c = point((centre[0], centre[1], top - depth))
            frame = _frame(c, r @ x)
            frame[:3, 3] = c - frame[:3, 0] * length / 2 - frame[:3, 1] * width / 2
            self._place(e, frame)
        elif kind == "beam":
            start, end, _top, _w, _h = self.beam_params(guid)
            self.set_beam_ends(guid, point(start), point(end))
        elif kind == "roof" and self.roof_params(guid)["form"] == "blocks":     # (0.262) each block reflected
            from ..core import roof_blocks as core_blocks
            p = self.roof_params(guid)
            m = self._placement_si(e)
            turn = np.degrees(np.arctan2(m[1, 0], m[0, 0]))
            world = []
            for b in p["blocks"]:
                c = m @ np.array((b.cx, b.cy, 0.0, 1.0))
                world.append(core_blocks.mirrored(core_blocks.replace(b, cx=float(c[0]), cy=float(c[1]),
                                                                      angle=b.angle + turn), mat))
            origin = point(m[:3, 3])
            frame = np.eye(4)
            frame[:3, 3] = origin
            self._place(e, frame)
            local = [core_blocks.replace(b, cx=b.cx - float(origin[0]), cy=b.cy - float(origin[1])) for b in world]
            self._set_params(e, {"Blocos": core_blocks.to_text(local)})
            self._set_roof_body(e)
        elif kind == "roof":                           # (0.111) its outline reflected, the other way round
            p = self.roof_params(guid)
            world = [tuple(point((x, y, 0.0))[:2]) for x, y in p["outline"]][::-1]
            n = len(world)
            sloping = [p["sloping"][(n - 2 - j) % n] for j in range(n)] if p["sloping"] else []
            m = np.eye(4)
            m[:3, 3] = (world[0][0], world[0][1], p["eave"])
            self._place(e, m)
            self._set_params(e, {"Contorno": ";".join("{:.6f},{:.6f}".format(x - world[0][0], y - world[0][1])
                                                      for x, y in world),
                                 "Aguas": ";".join("1" if s else "0" for s in sloping)})
            self._set_roof_body(e)
        elif kind == "slab":
            if e.HasOpenings:
                raise EditRefused("mirror_openings")
            info = self.slab_outline(guid)
            m = self._placement_si(e)
            self._place(e, _frame(point(m[:3, 3]), r @ m[:3, 0]))
            if info["shape"] != "circulo":
                ring = [tuple(point((x, y, 0.0))[:2]) for x, y in info["outline"]][::-1]
                self.set_slab_outline(guid, ring, holes=[[tuple(point((x, y, 0.0))[:2]) for x, y in h][::-1]
                                                          for h in info["holes"]])

    def _mirror_wall(self, guid, mat, lang="pt"):
        """A straight wall reflected: drawn from the reflected end towards the reflected start (see the module's
        docstring)."""
        wall = self.by_guid(guid)
        start, end, _t = self.wall_axis(guid)
        old = self._placement_si(wall)
        before = []                                   # (opening, lo, hi in the wall's frame, [(filling, its side)])
        ends = {}                                     # (0.188) an embedded curtain wall's ends, before
        for rel in wall.HasOpenings or ():
            opening = rel.RelatedOpeningElement
            lo, hi = self._local_aabb(opening, old)
            fillings = [(f.RelatedBuildingElement, self._filling_side(f.RelatedBuildingElement, old))
                        for f in opening.HasFillings or ()]
            for filling, _side in fillings:
                if filling.is_a("IfcCurtainWall"):
                    p = self.curtain_params(filling.GlobalId)
                    ends[filling.GlobalId] = (p["start"], p["end"])
            before.append((opening, lo, hi, fillings))
        start_cut, end_cut = self.wall_cuts(wall)
        r = mat[:3, :3]
        new = _frame((mat @ np.append(end, 1.0))[:3], -(r @ (end - start)))
        new[2, 3] = old[2, 3]                         # (its base stays at its level)
        self._place(wall, new)
        self._set_params(wall, {"CorteInicio": 180.0 - end_cut, "CorteFim": 180.0 - start_cut})
        length, height, thickness = self.wall_params(guid)
        self._set_wall_body(wall, length, height, thickness)
        for opening, lo, hi, fillings in before:      # along the wall the other way: x -> length - x
            if not fillings:
                self._set_box_body(opening, new, (length - hi[0], lo[1], lo[2]), (length - lo[0], hi[1], hi[2]))
                continue
            for filling, side in fillings:            # (the same face of the wall: its y is kept)
                s0, s1 = length - hi[0], length - lo[0]
                self._set_box_body(opening, new, (s0, lo[1], lo[2]), (s1, hi[1], hi[2]))
                if filling.GlobalId in ends:          # (0.188) an embedded curtain wall: reflected as one alone
                    a, b = ends[filling.GlobalId]
                    point = lambda p: (mat @ np.append(np.asarray(p, dtype=float)[:3], 1.0))[:3]    # noqa: E731
                    self._place(filling, _frame(point(b), -(r @ (b - a))))
                    continue
                if filling.is_a("IfcDoor") and _hand(filling) is not None:      # a mirror image: the other hand
                    other = "RIGHT" if _hand(filling) == "LEFT" else "LEFT"
                    type_ = ifcopenshell.util.element.get_type(filling)
                    if type_ is not None:
                        type_ = self._door_type_with_hand(type_, other, lang)
                        ifcopenshell.api.type.assign_type(self.file, related_objects=[filling], relating_type=type_)
                    filling.OperationType = _with_hand(filling.OperationType or "SINGLE_SWING_LEFT", other)
                elif filling.is_a("IfcWindow") and ifcopenshell.util.element.get_type(filling) is not None:
                    type_ = ifcopenshell.util.element.get_type(filling)         # (0.289) a window not symmetric:
                    other = self.mirrored_window_type(type_, lang)              # its mirror image's type
                    if other is not type_:
                        ifcopenshell.api.type.assign_type(self.file, related_objects=[filling], relating_type=other)
                        filling.PartitioningType = other.PartitioningType
                        filling.UserDefinedPartitioningType = other.UserDefinedPartitioningType
                faces = (lo[1] + MARGIN, hi[1] - MARGIN)
                self._place_filling(filling, new, s0, s1, lo[2], faces, side)
        for rel, through, through_end, butt, butt_end in self.wall_joints(guid):   # its start is where its end was
            swap = {"ATSTART": "ATEND", "ATEND": "ATSTART"}
            if through == guid:
                rel.RelatingConnectionType = swap.get(rel.RelatingConnectionType, rel.RelatingConnectionType)
            if butt == guid:
                rel.RelatedConnectionType = swap.get(rel.RelatedConnectionType, rel.RelatedConnectionType)
