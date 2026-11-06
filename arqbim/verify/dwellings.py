"""(0.416) The dwellings (fogos) the rooms make, and their type (T0, T1, T2… — the number of bedrooms, as the law
counts it: Cabo Verde's CTE art. 40.º n.º 1, Portugal's RGEU).

The rooms joined by doors are one dwelling; the building's common areas (a landing, the common hall, the stairwell)
are in none — a door from one of them, or from outside, is a dwelling's entrance. A building with no common areas is
a house: its storeys, one over the other, are one dwelling (the stairs join them, not a door). A room the architect
put in a dwelling by its name stays in it (a duplex, two houses side by side…).

Pure geometry (shapely) on what ifc/dwellings.py reads from the model."""

from dataclasses import dataclass, field

import numpy as np

from . import uses

PROBE = 0.20                # m past a door's wall faces where the rooms on its two sides are looked for
OVERLAP = 1.0               # m²: storeys of a house overlapping this much in plan are one dwelling


@dataclass
class Room:
    guid: str
    storey: str
    level: float
    outline: list
    holes: list = field(default_factory=list)
    name: str = ""
    use: str = "outro"
    external: bool = False
    manual: str = None          # the dwelling the architect put it in (its name), or None
    area: float = 0.0


@dataclass
class Door:
    guid: str
    storey: str
    middle: tuple               # (x, y) its middle in plan
    normal: tuple               # (x, y) across its wall
    depth: float                # its wall's thickness (m)
    width: float = 0.0


@dataclass
class Dwelling:
    name: str
    rooms: list                 # GlobalIds of its rooms
    bedrooms: int = 0
    storeys: list = field(default_factory=list)
    entrances: list = field(default_factory=list)   # GlobalIds of the doors into it (from outside or a common area)
    manual: bool = False
    useful_area: float = 0.0    # m²: the sum of its interior rooms' areas

    @property
    def typology(self):
        return "T{}".format(self.bedrooms)


def _polygon(room):
    from shapely.geometry import Polygon
    poly = Polygon(room.outline, room.holes)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly


def _letters(k):
    """A, B, … Z, AA, AB…"""
    out = ""
    k += 1
    while k:
        k, r = divmod(k - 1, 26)
        out = chr(65 + r) + out
    return out


class _Union:
    def __init__(self, items):
        self.up = {i: i for i in items}

    def find(self, i):
        while self.up[i] != i:
            self.up[i] = self.up[self.up[i]]
            i = self.up[i]
        return i

    def join(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.up[b] = a


def door_sides(rooms, doors, enclosure=None):
    """{door GlobalId: (room on one side or None, room on the other or None)} — None: outside (no room there).
    enclosure(storey, x, y): for a place in no room, the key («~…») of the place the walls close round it (a corridor
    left without a room is inside, not outside), or None (outside)."""
    from shapely.geometry import Point
    by_storey = {}
    for r in rooms:
        by_storey.setdefault(r.storey, []).append((r.guid, _polygon(r)))
    out = {}
    for d in doors:
        m, n = np.asarray(d.middle, dtype=float), np.asarray(d.normal, dtype=float)
        length = float(np.linalg.norm(n))
        if length < 1e-9:
            continue
        n = n / length
        reach = d.depth / 2 + PROBE
        sides = []
        for p in (m + n * reach, m - n * reach):
            here = Point(float(p[0]), float(p[1]))
            found = next((g for g, poly in by_storey.get(d.storey, ()) if poly.contains(here)), None)
            if found is None and enclosure is not None:
                found = enclosure(d.storey, float(p[0]), float(p[1]))
            sides.append(found)
        out[d.guid] = tuple(sides)
    return out


def find(rooms, doors, language="pt", enclosure=None):
    """The dwellings: [Dwelling], named «Fogo A», «Fogo B»… (or the names given) from the lowest storey up, left to
    right; and {room GlobalId: dwelling name} (common areas in none). A place inside the walls with no room (a corridor
    not made a room) joins the rooms whose doors open to it, but counts in no area."""
    rooms = list(rooms)
    if not rooms:
        return [], {}
    by_guid = {r.guid: r for r in rooms}
    common = {r.guid for r in rooms if uses.is_common(r.use)}
    sides = door_sides(rooms, doors, enclosure)
    places = sorted({x for pair in sides.values() for x in pair if x is not None and x not in by_guid})
    members = [r.guid for r in rooms if r.guid not in common]
    union = _Union(members + places)
    entrances = {}
    for door, (a, b) in sides.items():
        if a is not None and b is not None and a not in common and b not in common:
            union.join(a, b)
        else:
            for inside, other in ((a, b), (b, a)):
                if inside is not None and inside not in common and (other is None or other in common):
                    entrances.setdefault(inside, []).append(door)
    # A house (no common areas): its storeys one over the other are one dwelling. In a building with common areas, a
    # storey of rooms with no entrance of its own (no door from outside or from a common area) is the upper floor of
    # the dwelling under it (a duplex): the stairs join them, not a door.
    from shapely.ops import unary_union
    polys = {g: _polygon(by_guid[g]) for g in members}
    groups = {}
    for g in members + places:
        groups.setdefault(union.find(g), []).append(g)
    shapes = {}
    for root, gs in groups.items():
        real = [g for g in gs if g in by_guid]
        if real:
            shapes[root] = (unary_union([polys[g] for g in real]), {by_guid[g].storey for g in real},
                            any(g in entrances for g in gs), min(by_guid[g].level for g in real))
    roots = sorted(shapes, key=lambda r: shapes[r][3])
    for i, a in enumerate(roots):
        for b in roots[i + 1:]:
            (pa, sa, ea, _la), (pb, sb, eb, _lb) = shapes[a], shapes[b]
            if not sa.isdisjoint(sb) or (common and eb):
                continue
            if pa.intersection(pb).area >= OVERLAP:
                union.join(a, b)
                if common:
                    break
    groups, doors_in = {}, {}
    for g in members + places:
        root = union.find(g)
        if g in by_guid:
            groups.setdefault(root, []).append(g)
        doors_in.setdefault(root, set()).update(entrances.get(g, ()))
    entrances = {}                                   # (a group's entrances, the places' too: on its first room)
    for root, gs in groups.items():
        entrances[gs[0]] = sorted(doors_in.get(root, ()))
    named = {}                                       # a name given -> its rooms
    auto = []
    for gs in groups.values():
        manual = [by_guid[g].manual for g in gs if by_guid[g].manual]
        if manual:
            main = max(set(manual), key=manual.count)
            for g in gs:
                named.setdefault(by_guid[g].manual or main, []).append(g)
        else:
            auto.append(gs)

    def place(gs):
        rs = [by_guid[g] for g in gs]
        low = min(r.level for r in rs)
        centre = np.mean([np.mean(np.asarray(r.outline, dtype=float), axis=0) for r in rs], axis=0)
        return (round(low, 3), round(float(centre[0]), 2), round(float(centre[1]), 2))

    word = "Fogo" if language == "pt" else "Dwelling"
    used = set(named)
    out = []
    k = 0
    for gs in sorted(auto, key=place):
        while "{} {}".format(word, _letters(k)) in used:
            k += 1
        name = "{} {}".format(word, _letters(k))
        used.add(name)
        named[name] = gs
        k += 1
    for name, gs in sorted(named.items(), key=lambda item: place(item[1])):
        rs = [by_guid[g] for g in gs]
        out.append(Dwelling(
            name=name, rooms=sorted(gs, key=lambda g: (by_guid[g].level, by_guid[g].guid)),
            bedrooms=sum(1 for r in rs if uses.is_bedroom(r.use) and not r.external),
            storeys=sorted({r.storey for r in rs}, key=lambda s: min(r.level for r in rs if r.storey == s)),
            entrances=sorted({d for g in gs for d in entrances.get(g, ())}),
            manual=any(r.manual for r in rs),
            useful_area=sum(r.area for r in rs if not r.external)))
    of_room = {g: d.name for d in out for g in d.rooms}
    return out, of_room
