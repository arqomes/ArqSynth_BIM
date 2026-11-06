"""(0.416) The reader («o leitor»): what the Verifier knows of the project — each room's use (and why), what is inside
it, the doors between rooms, the dwellings and their type — read from the open document, kept until it changes
(Document.revision).

What the architect chose (a room's use, the dwelling a room is in) is in the IFC (ifc/dwellings.py); the rest is
found here each time the model changes, and written to the IFC file when it is saved (the use in IfcSpace.ObjectType,
each dwelling an IfcZone with its type)."""

import weakref
from dataclasses import dataclass, field

import numpy as np

from ..i18n import lang
from . import dwellings as dw
from . import uses

DOOR_DEPTH = 0.80           # m: a door's wall taken this thick: its rooms are looked for 0,60 m each side of its middle


@dataclass
class Facts:
    revision: int = -1
    rooms: dict = field(default_factory=dict)        # GlobalId -> dw.Room (its use deduced)
    why: dict = field(default_factory=dict)          # GlobalId -> "chosen" | "contents" | "name" | "none"
    contents: dict = field(default_factory=dict)     # GlobalId -> {kind: count}
    doors: list = field(default_factory=list)        # dw.Door
    dwellings: list = field(default_factory=list)    # dw.Dwelling
    of_room: dict = field(default_factory=dict)      # room GlobalId -> its dwelling's name
    infos: dict = field(default_factory=dict)        # GlobalId -> ifc.space_info(…)
    inside: dict = field(default_factory=dict)       # (0.419) room GlobalId -> [(object id, its kind)] inside it
    windows: list = field(default_factory=list)      # (0.420) dw.Door of the windows (and glazed doors)
    window_sides: dict = field(default_factory=dict)  # (0.420) window GlobalId -> (room / «~place» / None, the same)
    sides: dict = field(default_factory=dict)        # door GlobalId -> (room or «~place» or None, the same)

    def dwelling(self, name):
        return next((d for d in self.dwellings if d.name == name), None)

    def dwelling_of(self, room):
        return self.dwelling(self.of_room.get(room))


_KEPT = weakref.WeakKeyDictionary()     # document -> (its IFC, Facts): the last read (0.424: by the document itself
#                                         and its IFC — an id is used again by a new one, its revision may be the same)


def _kept(doc, revision):
    found = _KEPT.get(doc)
    if found is None:
        return None
    ifc, facts = found
    return facts if ifc() is getattr(doc, "ifc", None) and facts.revision == revision else None


def _keep(doc, facts):
    ifc = getattr(doc, "ifc", None)
    try:
        _KEPT[doc] = (weakref.ref(ifc) if ifc is not None else (lambda: None), facts)
    except TypeError:                                   # (an object that cannot be weakly referred to: not kept)
        pass

# an IFC class (and PredefinedType) -> what the reader calls it inside a room
SANITARY = {"TOILETPAN": "toilet", "WCSEAT": "toilet", "URINAL": "toilet", "SHOWER": "shower", "BATH": "bath",
            "WASHHANDBASIN": "basin", "BIDET": "bidet", "SINK": "sink"}
APPLIANCES = {"ELECTRICCOOKER": "cooker", "DISHWASHER": "cooker", "WASHINGMACHINE": "washer",
              "TUMBLEDRYER": "washer"}
FURNITURE_WORDS = (("double_bed", ("cama de casal", "double bed", "cama casal")), ("bed", ("cama", "bed")),
                   ("sofa", ("sofa", "sofá", "couch")), ("toilet", ("sanita", "toilet", "wc")),
                   ("sink", ("lava-loica", "lava-loiça", "lava loiça", "kitchen sink")))


def _kind_of(ifc, obj):
    """What a fitting or piece of furniture is, for a room's use: "toilet", "sink", "bed"… or None."""
    cls = obj.ifc_class
    e = ifc.by_guid(obj.id)
    if e is None:
        return None
    if cls == "IfcSanitaryTerminal":
        found = SANITARY.get(getattr(e, "PredefinedType", None) or "")
        if found:
            return found
    elif cls == "IfcElectricAppliance":
        ptype = getattr(e, "PredefinedType", None) or ""
        if ptype == "USERDEFINED" and "hood" in (getattr(e, "ObjectType", "") or "").lower():
            return "cooker"
        return APPLIANCES.get(ptype)
    elif cls == "IfcSystemFurnitureElement":            # (a worktop: a kitchen's)
        return "kitchen_cabinet"
    elif cls == "IfcFurniture":
        params = ifc._params(e)
        if params.get("Elemento") == "cabinet":
            return "kitchen_cabinet" if params.get("Modulo") in ("base", "wall", "tall") else \
                ("wardrobe" if params.get("Modulo") == "wardrobe" else None)
        if getattr(e, "PredefinedType", None) == "BED":
            return "bed"
        if getattr(e, "PredefinedType", None) == "SOFA":
            return "sofa"
    name = " {} ".format((obj.name or "").lower())
    for kind, words in FURNITURE_WORDS:
        if any(w in name for w in words):
            return kind
    return None


INSIDE = ("IfcSanitaryTerminal", "IfcElectricAppliance", "IfcFurniture", "IfcSystemFurnitureElement",
          "IfcBuildingElementProxy")


def read(doc, force=False):
    """The project's Facts, read again only when the document changed since the last time."""
    revision = getattr(doc, "revision", 0)
    kept = _kept(doc, revision)
    if kept is not None and not force:
        return kept
    facts = Facts(revision=revision)
    try:
        infos = doc.ifc.spaces()
    except Exception:                                   # (the IFC still being read)
        infos = []
    if not infos:
        _keep(doc, facts)
        return facts
    from shapely.geometry import Point, Polygon
    polys = {}
    for info in infos:
        poly = Polygon(info["outline"], info["holes"])
        if not poly.is_valid:
            poly = poly.buffer(0)
        polys[info["guid"]] = (info["storey"], poly)
        facts.infos[info["guid"]] = info
    by_storey = {}
    for g, (storey, poly) in polys.items():
        by_storey.setdefault(storey, []).append((g, poly))

    def room_at(storey, x, y):
        here = Point(x, y)
        holding = [(poly.area, g) for g, poly in by_storey.get(storey, ()) if poly.contains(here)]
        return min(holding)[1] if holding else None

    contents = {g: {} for g in polys}
    doors = []
    for obj in list(doc.objects.values()):
        if not getattr(obj, "is_bim", False) or getattr(obj, "mesh", None) is None:
            continue
        if obj.ifc_class in ("IfcDoor", "IfcWindow") and obj.storey not in by_storey:
            continue                                        # (0.422: a storey with no rooms: nothing to join or light)
        if obj.ifc_class == "IfcDoor":
            door = _door(doc, obj)
            if door is not None:
                doors.append(door)
                facts.windows.append(door)                  # (0.420: a glazed door lights a room too)
            continue
        if obj.ifc_class == "IfcWindow":                    # (0.420)
            window = _door(doc, obj)
            if window is not None:
                facts.windows.append(window)
            continue
        if obj.ifc_class not in INSIDE or obj.storey not in by_storey:
            continue
        kind = _kind_of(doc.ifc, obj)
        if kind is None:
            continue
        lo, hi = (np.asarray(c, dtype=float) for c in obj.mesh.bounds())
        room = room_at(obj.storey, float(lo[0] + hi[0]) / 2, float(lo[1] + hi[1]) / 2)
        if room is not None:
            contents[room][kind] = contents[room].get(kind, 0) + 1
            facts.inside.setdefault(room, []).append((obj.id, kind))
    language = lang()
    for g, info in facts.infos.items():
        space = doc.ifc.by_guid(g)
        params = doc.ifc._params(space) if space is not None else {}
        chosen = params.get("Uso") or None
        if chosen is None and space is not None and params.get("Elemento") != "space":
            chosen = uses.from_label(getattr(space, "ObjectType", None))      # (another program's room: its type)
        use, why = uses.deduce(info["name"], contents[g], info.get("external"), chosen)
        facts.rooms[g] = dw.Room(guid=g, storey=info["storey"], level=info["level"], outline=info["outline"],
                                 holes=info["holes"], name=info["name"], use=use, external=bool(info.get("external")),
                                 manual=params.get("Fogo") or None, area=float(info["area"]))
        facts.why[g] = why
    facts.contents = contents
    facts.doors = doors
    enclosure = _enclosures(doc)
    facts.dwellings, facts.of_room = dw.find(facts.rooms.values(), doors, language, enclosure)
    facts.sides = dw.door_sides(facts.rooms.values(), doors, enclosure)
    facts.window_sides = dw.door_sides(facts.rooms.values(), facts.windows, enclosure)
    _keep(doc, facts)
    return facts


def _enclosures(doc):
    """enclosure(storey, x, y) for dwellings.door_sides: the place the walls close round a point in no room (its key,
    «~storey~n»), or None (outside the walls). (0.422) A storey's enclosed places found once, all together."""
    from shapely.geometry import Point
    from shapely.prepared import prep
    from ..core import rooms as core_rooms
    found = {}

    def enclosure(storey, x, y):
        if storey not in found:
            try:
                polys = core_rooms.regions(doc.ifc.storey_obstacles(storey, separators=True))
            except Exception:                           # noqa: BLE001
                polys = []
            found[storey] = [("~{}~{}".format(storey, k), prep(p), p.bounds) for k, p in enumerate(polys)]
        here = Point(x, y)
        for key, poly, (x0, y0, x1, y1) in found[storey]:
            if x0 <= x <= x1 and y0 <= y <= y1 and poly.contains(here):
                return key
        return None
    return enclosure


def _door(doc, obj):
    """A door as the dwellings need it: its middle and the way across it (its placement's own y, square to its
    wall), its storey."""
    from ..model.presentation_export import _across
    across = _across(obj, doc)
    if across is None:
        return None
    lo, hi = (np.asarray(c, dtype=float) for c in obj.mesh.bounds())
    middle = ((lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0)
    width = float(np.max(np.abs(np.asarray(hi[:2]) - np.asarray(lo[:2]))))
    return dw.Door(guid=obj.id, storey=obj.storey, middle=middle, normal=(float(across[0]), float(across[1])),
                   depth=DOOR_DEPTH, width=width)


def forget(doc):
    try:
        _KEPT.pop(doc, None)
    except TypeError:
        pass
