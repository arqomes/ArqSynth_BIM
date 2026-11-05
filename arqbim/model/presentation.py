"""(0.363) The presentation prepared here for the ArqSynth Presentation (PLANO, the Presentation's step 3). The owner,
2026-11-02: «cenas 3D, cortes, animações, efeitos etc. podia ser preparada aqui no BIM e depois migrada para a
plataforma de apresentação».

Its scenes are the project's views — the general view, each named 3D view, each storey's plan, each section — and
what is chosen for them here: their order, the one it opens on, those kept out of the sequence (still sent, the
Presentation keeps them aside), and per scene how it is reached (a smooth flight or a cut, how long), what moves in
it (the sun over the day, the building put up piece by piece, pulled apart), its caption and how long it stays in the
tour. A scene is known by a key that stays when its view is renamed: «geral», «vista_<uid>», «planta_<storey
GlobalId>», «corte_<uid>». (0.364) And its camera move: one of the Presentation's (model/camera_moves.py), its time,
and for the moves inside a room the room (an IfcSpace; none chosen: the one the scene looks into, else the largest).

Kept with the views (Document.presentation, in the .arqsynthbim file) as only what differs from the usual:
{"order": [key…], "initial": key | None, "scenes": {key: {field: value}}}; one undo step a change. Scenes not in the
order (new views) come after the others, in the views' own order. Pure Python."""

import copy
from dataclasses import dataclass, replace

from . import camera_moves

TRANSITIONS = ("smooth", "cut")
EFFECTS = ("none", "sun", "construction", "explode")
DEFAULTS = {"hidden": False, "transition": "smooth", "transition_s": 1.2, "effect": "none", "effect_s": 6.0,
            "seconds": 0.0, "caption": "", "move": "", "move_s": 0.0, "room": "",
            "sun_day": 172, "sun_minutes": 720, "sun_animate": "none", "exposure": 1.0, "sky": False}
LIMITS = {"transition_s": (0.0, 10.0), "effect_s": (1.0, 60.0), "seconds": (0.0, 600.0), "move_s": (0.0, 120.0),
          "sun_day": (1, 365), "sun_minutes": (0, 1439), "exposure": (0.3, 1.6)}
SUN_ANIMATIONS = ("none", "day", "year")
OVERVIEW = "geral"


@dataclass(frozen=True)
class Scene:
    """A scene of the presentation: its key, kind ("overview" | "view3d" | "plan" | "section"), name, the view it is
    in the program (a view key: ("3d",), ("3d", uid), ("plan", GlobalId), ("section", name)) and what was chosen for
    it. seconds: how long it stays in the tour (0: the Presentation's usual time). move: a camera move's id ("": none),
    move_s its time (0: the move's own), room the IfcSpace an interior move is made in ("": found)."""
    key: str
    kind: str
    name: str
    view: tuple
    hidden: bool = False
    transition: str = "smooth"
    transition_s: float = 1.2
    effect: str = "none"
    effect_s: float = 6.0
    seconds: float = 0.0
    caption: str = ""
    move: str = ""
    move_s: float = 0.0
    room: str = ""
    sun_day: int = 172          # (0.365) the sun's day of the year (21 June)…
    sun_minutes: int = 720      # …and time of day (local standard clock): the Presentation's own sun from the site
    sun_animate: str = "none"   # its animation: "none" | "day" (sunrise to sunset) | "year" (the months at that hour)
    exposure: float = 1.0       # the picture's exposure (the Presentation's 0,3–1,6)
    sky: bool = False           # its sky behind the model (else the Presentation's plain background)


def empty():
    """(0.366) labels / walk: the rooms go as labels and as the Virtual Walk's zones (linked by their doors)."""
    return {"order": [], "initial": None, "scenes": {}, "labels": True, "walk": True}


# (0.366) a room's kind for the Presentation's Virtual Walk, by the words of its name (Portuguese and English)
ROOM_KINDS = (("bathroom", ("wc", "i.s", "instalação sanitária", "instalacao sanitaria", "casa de banho", "banho",
                            "lavabo", "bathroom", "toilet")),
              ("kitchen", ("cozinha", "kitchenette", "kitchen", "copa")),
              ("bedroom", ("quarto", "suite", "suíte", "dormitório", "dormitorio", "bedroom")),
              ("corridor", ("corredor", "circulação", "circulacao", "corridor")),
              ("entry", ("entrada", "vestíbulo", "vestibulo", "entry")),
              ("hall", ("hall", "átrio", "atrio", "foyer")),
              ("balcony", ("varanda", "sacada", "balcony")),
              ("terrace", ("terraço", "terraco", "terrace")),
              ("garage", ("garagem", "estacionamento", "garage", "parking")),
              ("technical", ("técnic", "tecnic", "arrumos", "despensa", "lavandaria", "storage", "plant room")))


def room_kind(name, external=False):
    """The Virtual Walk's kind of a room (WalkZoneType) by its name: «Cozinha» kitchen, «Quarto 2» bedroom…; an
    exterior one with no other word, "exterior"; else "room"."""
    text = " {} ".format(str(name or "").lower())
    for kind, words in ROOM_KINDS:
        if any(w in text for w in words):
            return kind
    return "exterior" if external else "room"


def with_options(data, **options):
    """The presentation with its options changed: labels, walk (booleans)."""
    out = clean(copy.deepcopy(data))
    for name in ("labels", "walk"):
        if name in options:
            out[name] = bool(options[name])
    return out


def _value(name, value):
    """A setting as it may be kept: its kind and range — None when it is not one."""
    default = DEFAULTS[name]
    try:
        if isinstance(default, bool):
            return bool(value)
        if isinstance(default, int):
            lo, hi = LIMITS[name]
            return int(min(max(round(float(value)), lo), hi))
        if isinstance(default, float):
            lo, hi = LIMITS[name]
            return round(min(max(float(value), lo), hi), 2)
        value = str(value)
    except (TypeError, ValueError):
        return None
    if name == "transition":
        return value if value in TRANSITIONS else None
    if name == "effect":
        return value if value in EFFECTS else None
    if name == "move":
        return value if value == "" or value in camera_moves.MOVES else None
    if name == "sun_animate":
        return value if value in SUN_ANIMATIONS else None
    return value.strip()


def clean(data):
    """The presentation as it is kept (only what differs from the usual), from whatever was read."""
    out = empty()
    if not isinstance(data, dict):
        return out
    order = data.get("order")
    if isinstance(order, (list, tuple)):
        seen = set()
        out["order"] = [k for k in (str(k) for k in order) if not (k in seen or seen.add(k))]
    if data.get("initial"):
        out["initial"] = str(data["initial"])
    for name in ("labels", "walk"):                    # (0.366)
        if isinstance(data.get(name), bool):
            out[name] = data[name]
    scenes = data.get("scenes")
    if isinstance(scenes, dict):
        for key, fields in scenes.items():
            if not isinstance(fields, dict):
                continue
            kept = {}
            for name, value in fields.items():
                if name in DEFAULTS:
                    value = _value(name, value)
                    if value is not None and value != DEFAULTS[name]:
                        kept[name] = value
            if kept:
                out["scenes"][str(key)] = kept
    return out


def natural(doc):
    """[Scene] of the project's views, in their own order and without what was chosen: the general view, the named
    3D views (with a camera), the plans of the storeys with elements, the sections."""
    from ..i18n import t
    out = [Scene(OVERVIEW, "overview", t("present.overview"), ("3d",))]
    for view in getattr(doc, "views3d", ()):
        if view.camera:
            out.append(Scene("vista_" + view.uid, "view3d", view.name, ("3d", view.uid)))
    with_elements = {getattr(o, "storey", None) for o in getattr(doc, "objects", {}).values()
                     if getattr(o, "is_bim", False)}
    for guid, name, _z in doc.storeys():
        if guid in with_elements:
            out.append(Scene("planta_" + guid, "plan", t("present.plan", name=name), ("plan", guid)))
    for section in getattr(doc, "sections", ()):
        if abs(float(section.normal[0])) + abs(float(section.normal[1])) > 1e-9:
            out.append(Scene("corte_" + section.uid, "section", t("present.section", name=section.name),
                             ("section", section.name)))
    return out


def scenes(doc):
    """[Scene] in the presentation's order, each with what was chosen for it."""
    data = getattr(doc, "presentation", None) or empty()
    found = {s.key: s for s in natural(doc)}
    keys = [k for k in data["order"] if k in found] + [s.key for s in natural(doc) if s.key not in data["order"]]
    return [replace(found[k], **data["scenes"].get(k, {})) for k in keys]


def initial(doc, found=None):
    """The key of the scene the presentation opens on: the one chosen, unless it is gone or kept out of it — then
    the first one in it (None: no scene)."""
    found = scenes(doc) if found is None else found
    chosen = (getattr(doc, "presentation", None) or empty()).get("initial")
    shown = [s.key for s in found if not s.hidden]
    if chosen in shown:
        return chosen
    return shown[0] if shown else (found[0].key if found else None)


def _area(outline):
    pts = list(outline)
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2.0


def _holds(space, point):
    """Is the point (the model's axes) inside the room — over its outline, between its floor and its top?"""
    x, y, z = (float(c) for c in point)
    level, height = float(space["level"]), float(space["height"])
    return level - 0.5 <= z <= level + height + 0.5 and camera_moves.inside(x, y, space["outline"])


def spaces(doc):
    """The project's rooms (IfcModel.spaces: space_info), [] without any."""
    try:
        return list(doc.ifc.spaces())
    except AttributeError:
        return []


def room_of(doc, scene, rooms=None):
    """The room (space_info) a scene's interior move is made in: the one chosen, else the one the scene looks into (a
    named 3D view's focus inside it: the smallest that holds it), else the largest of its storey (a plan) or of the
    project. None: no rooms (the Presentation's assumed room is used)."""
    rooms = spaces(doc) if rooms is None else rooms
    if not rooms:
        return None
    chosen = next((s for s in rooms if s["guid"] == scene.room), None)
    if chosen is not None:
        return chosen
    if scene.kind == "view3d":
        view = doc.view3d(scene.view[1]) if hasattr(doc, "view3d") else None
        focus = (view.camera or {}).get("focus") if view is not None else None
        holding = [s for s in rooms if focus is not None and _holds(s, focus)]
        if holding:
            return min(holding, key=lambda s: _area(s["outline"]))
    pool = [s for s in rooms if scene.kind == "plan" and s.get("storey") == scene.view[1]] or rooms
    return max(pool, key=lambda s: _area(s["outline"]))


def room_measures(space, offset=(0.0, 0.0, 0.0)):
    """A room (space_info) as the camera moves take it (camera_moves.Room, the GLB's axes), or None."""
    if space is None:
        return None
    ox, oy, oz = (float(c) for c in offset)
    poly = [(float(x) - ox, -(float(y) - oy)) for x, y in space["outline"]]
    return camera_moves.room_from_polygon(poly, float(space["level"]) - oz, float(space["height"]))


def building_measures(doc):
    """The building's measures for the camera moves (camera_moves.Building), from the elements that go to the
    Presentation (as the GLB has them: gltf_export's), in the GLB's axes without its offset; None: no elements."""
    from . import gltf_export
    corners = []
    for o in getattr(doc, "objects", {}).values():
        if not getattr(o, "is_bim", False) or getattr(o, "mesh", None) is None \
                or getattr(o, "ifc_class", None) in gltf_export.SKIP or not hasattr(o.mesh, "bounds"):
            continue
        box = o.mesh.bounds()
        if box is not None:
            corners += [camera_moves.to_gl(c, (0.0, 0.0, 0.0)) for c in box]
    if not corners:
        return None
    pts = [list(c) for c in corners]
    lo = [min(p[k] for p in pts) for k in range(3)]
    hi = [max(p[k] for p in pts) for k in range(3)]
    return camera_moves.Building.of_box(lo, hi)


def move_frames(doc, scene, fps=30):
    """A scene's camera move played, in the model's axes: [(eye, target)] a frame each ([] without a move or
    elements) — the BIM's preview of what the Presentation will play."""
    building = building_measures(doc) if scene.move else None
    if building is None:
        return []
    room = room_measures(room_of(doc, scene)) if camera_moves.interior(scene.move) else None
    zero = (0.0, 0.0, 0.0)
    return [(camera_moves.to_model(eye, zero), camera_moves.to_model(look, zero))
            for eye, look in camera_moves.frames(scene.move, building, room, scene.move_s or None, fps)]


def site(doc):
    """(latitude, longitude) of the site, None when it has no place (the Presentation's sun then the view style's)."""
    try:
        lat, lon, _elevation = doc.ifc.site_location()
    except (AttributeError, TypeError, ValueError):
        return None
    return (float(lat), float(lon)) if lat is not None and lon is not None else None


def sun_frames(doc, scene, frames=240):
    """(0.365) A scene's sun played as the Presentation will place it: [(towards the sun in the model's axes, day,
    minutes)] — through the day or the year when it is animated, else that moment alone; [] with no site."""
    from . import presentation_sun
    place = site(doc)
    if place is None:
        return []
    return [(presentation_sun.direction(place[0], place[1], day, minutes), day, minutes)
            for day, minutes in presentation_sun.sweep(place[0], place[1], scene.sun_day, scene.sun_minutes,
                                                      scene.sun_animate, frames)]


def move_seconds(scene):
    """How long a scene's move lasts: its own time, or the move's."""
    if not scene.move:
        return 0.0
    return scene.move_s or camera_moves.MOVES[scene.move][2]


def changed(data, key, **fields):
    """The presentation with these settings of a scene changed (back to the usual: not kept)."""
    out = clean(copy.deepcopy(data))
    mine = dict(out["scenes"].get(key, {}))
    for name, value in fields.items():
        value = _value(name, value)
        if value is None:
            continue
        if value == DEFAULTS[name]:
            mine.pop(name, None)
        else:
            mine[name] = value
    if mine:
        out["scenes"][key] = mine
    else:
        out["scenes"].pop(key, None)
    return out


def ordered(data, keys):
    """The presentation with its scenes in this order."""
    out = clean(copy.deepcopy(data))
    out["order"] = [str(k) for k in keys]
    return out


def with_initial(data, key):
    out = clean(copy.deepcopy(data))
    out["initial"] = str(key) if key else None
    return out
