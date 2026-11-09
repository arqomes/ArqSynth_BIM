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
# (0.479) the Presentation's own: the visual modes of its «Renderizado · Auto» menu (VisualStyle.mode, in its order),
# its qualities, its two cameras
STYLES = ("rendered", "material", "no_texture", "no_material", "clay", "white_concept", "technical_lines", "xray",
          "diagrammatic")
QUALITIES = ("auto", "high", "medium", "low")
PROJECTIONS = ("perspective", "orthographic")
FOV_MIN, FOV_MAX, FOV_DEFAULT = 20.0, 65.0, 35.0      # (its FOV slider: CAMERA_FOV_MIN / _MAX, a new camera's)
# (0.484) the Presentation's «Cortes»: a plane across the model — «Horizontal» (at a height), «Vertical X» (across the
# model's x), «Vertical Z» (its z, the model's y) — at a position (m, the model's axes), its side turned or not
CUT_TYPES = ("horizontal", "transversal", "longitudinal")
MAX_CUTS = 6
TRANSITION_MIN, TRANSITION_MAX = 0.3, 5.0             # (its «Transição» slider of the scenes, in seconds)
DEFAULTS = {"hidden": False, "transition": "smooth", "transition_s": 1.2, "effect": "none", "effect_s": 6.0,
            "seconds": 0.0, "caption": "", "move": "", "move_s": 0.0, "room": "",
            "sun_day": 172, "sun_minutes": 720, "sun_animate": "none", "exposure": 1.0, "sky": False,
            # (0.479) the ArqSynth Presentation tab: what «Criar cena» / «Atualizar» keep of the view
            "name": "", "projection": "", "fov": 0.0, "locked": False, "style": "", "quality": "auto", "ao": True,
            "ao_intensity": 1.0, "hidden_layers": (), "eye": (), "target": (), "omit": False,
            "cuts": (),                                   # (0.484) ((type, position, flipped), …)
            "hidden_tags": (),                            # (0.485) the labels it hides (their ids)
            # (0.486) its effect as the Presentation's: played when the scene is entered, how far an explosion starts
            # (× the model's radius), the elements left out of a construction (GlobalIds: they stay where they are)
            "effect_auto": True, "effect_spread": 1.2, "effect_static": ()}
LIMITS = {"transition_s": (0.0, 10.0), "effect_s": (1.0, 60.0), "seconds": (0.0, 600.0), "move_s": (0.0, 120.0),
          "sun_day": (1, 365), "sun_minutes": (0, 1439), "exposure": (0.3, 1.6), "fov": (0.0, FOV_MAX),
          "ao_intensity": (0.0, 2.0), "effect_spread": (0.3, 3.0)}
SUN_ANIMATIONS = ("none", "day", "year")
OVERVIEW = "geral"
# (0.479) a Presentation mode seen in the BIM's 3D view: the view style that looks most like it
STYLE_VIEW = {"rendered": "realistic", "material": "consistent", "no_texture": "consistent", "no_material": "shaded",
              "clay": "hidden", "white_concept": "hidden", "technical_lines": "wire", "xray": "xray",
              "diagrammatic": "shaded"}


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
    # (0.479) as the ArqSynth Presentation tab kept it («Criar cena», «Atualizar»): its camera's projection ("": the
    # view's own), lens (0: the view's own; else the Presentation's vertical FOV, 20–65°), locked; its visual mode ("":
    # the view style's), quality and ambient occlusion; the elements it hides (GlobalIds: the layers' eyes); where its
    # eye and target are (the model's axes; (): the view's own — a scene that is not a named 3D view); left out of what
    # is sent (a view's scene «apagada» — the view itself stays)
    projection: str = ""
    fov: float = 0.0
    locked: bool = False
    style: str = ""
    quality: str = "auto"
    ao: bool = True
    ao_intensity: float = 1.0
    hidden_layers: tuple = ()
    eye: tuple = ()
    target: tuple = ()
    omit: bool = False
    cuts: tuple = ()            # (0.484) its section planes: ((type of CUT_TYPES, position m, side turned), …)
    hidden_tags: tuple = ()     # (0.485) the labels (model/presentation_tags) it hides: their ids
    effect_auto: bool = True    # (0.486) its effect played when the scene is entered (the Presentation's autoPlay)…
    effect_spread: float = 1.2  # …an explosion's distance (× the model's radius)…
    effect_static: tuple = ()   # …the elements left out of a construction (GlobalIds): seen still from the start


def empty():
    """(0.366) labels / walk: the rooms go as labels and as the Virtual Walk's zones (linked by their doors).
    (0.485) tags: the labels put on the model in the Presentation tab (model/presentation_tags)."""
    return {"order": [], "initial": None, "scenes": {}, "labels": True, "walk": True, "tags": []}


def with_tags(data, tags):
    """(0.485) The presentation with the model's labels these (presentation_tags' dicts)."""
    from . import presentation_tags
    out = clean(copy.deepcopy(data))
    out["tags"] = presentation_tags.clean_tags(tags)
    return out


def tags(doc):
    """(0.485) The model's labels (presentation_tags' dicts), [] without any."""
    return list((getattr(doc, "presentation", None) or empty()).get("tags") or [])


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
        if name in ("hidden_layers", "hidden_tags", "effect_static"):   # (0.479) GlobalIds, (0.485) labels' ids, (0.486)
            # the elements left out of the effect — each once, sorted
            if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple, set, frozenset)):
                return None
            return tuple(sorted({str(v) for v in value if str(v)}))
        if name in ("eye", "target"):                  # (0.479) a point, or () for the view's own
            if isinstance(value, (str, bytes, dict)) or not hasattr(value, "__len__"):
                return None
            if len(value) == 0:
                return ()
            point = tuple(round(float(c), 4) for c in value)
            return point if len(point) == 3 and all(c == c and abs(c) < 1e7 for c in point) else None
        if name == "cuts":                             # (0.484) the section planes, each (type, position, flipped)
            if isinstance(value, (str, bytes, dict)) or not hasattr(value, "__iter__"):
                return None
            out = []
            for cut in value:
                if isinstance(cut, dict):
                    cut = (cut.get("type"), cut.get("position"), cut.get("flip", False))
                kind, position, flip = (list(cut) + [False])[:3]
                position = float(position)
                if kind in CUT_TYPES and position == position and abs(position) < 1e6:
                    out.append((str(kind), round(position, 3), bool(flip)))
            return tuple(out[:MAX_CUTS])
        if name == "fov":                              # (0.479) 0: the view's own; else the Presentation's range
            v = float(value)
            return 0.0 if v <= 0 else round(min(max(v, FOV_MIN), FOV_MAX), 2)
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
    if name == "projection":                            # (0.479)
        return value if value == "" or value in PROJECTIONS else None
    if name == "style":
        return value if value == "" or value in STYLES else None
    if name == "quality":
        return value if value in QUALITIES else None
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
    if data.get("tags"):                               # (0.485) the labels put on the model
        from . import presentation_tags
        out["tags"] = presentation_tags.clean_tags(data["tags"])
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


def all_scenes(doc):
    """[Scene] in the presentation's order, each with what was chosen for it — (0.479) those left out too."""
    data = getattr(doc, "presentation", None) or empty()
    found = {s.key: s for s in natural(doc)}
    keys = [k for k in data["order"] if k in found] + [s.key for s in natural(doc) if s.key not in data["order"]]
    return [replace(found[k], **_fields(data["scenes"].get(k, {}))) for k in keys]


def _fields(kept):
    """A scene's settings as kept (JSON: lists) as the Scene takes them (tuples, also inside: the cuts)."""
    return {name: tuple(tuple(v) if isinstance(v, list) else v for v in value) if isinstance(value, list) else value
            for name, value in kept.items()}


def cut_plane(kind, position, flip=False):
    """(0.484) A section plane (the Presentation's «Cortes») as what it keeps, in the model's axes: (normal, a point of
    it) — what is on the normal's side stays. «Horizontal» keeps what is under its height, «Vertical X» what is on the
    low x side, «Vertical Z» (the Presentation's z: the model's y) what is on the high y side; turned, the other side."""
    axis = {"horizontal": 2, "transversal": 0, "longitudinal": 1}[kind]
    sign = (-1.0 if kind in ("horizontal", "transversal") else 1.0) * (-1.0 if flip else 1.0)
    normal, point = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    normal[axis], point[axis] = sign, float(position)
    return tuple(normal), tuple(point)


def scenes(doc):
    """[Scene] in the presentation's order, each with what was chosen for it — (0.479) not those left out (a view's
    scene «apagada» in the Presentation tab: not sent)."""
    return [s for s in all_scenes(doc) if not s.omit]


def omitted(doc):
    """(0.479) The scenes left out of what is sent («apagadas»; their views are still in the project)."""
    return [s for s in all_scenes(doc) if s.omit]


def changed_all(data, keys, **fields):
    """(0.479) The presentation with these settings changed for all these scenes (the «Transição» of the scenes:
    every scene's) — one change."""
    out = clean(copy.deepcopy(data))
    for key in keys:
        out = changed(out, key, **fields)
    return out


def free_name(names, base):
    """(0.479) «Cena N», N the lowest not taken (the Presentation's nextSceneName), names: those there are."""
    taken = {str(n).strip().lower() for n in names}
    n = 1
    while "{} {}".format(base, n).lower() in taken:
        n += 1
    return "{} {}".format(base, n)


def copy_name(name, names, word):
    """(0.479) A copy's name, as the Presentation's uniqueSceneName(«Nome cópia»): «Cena 1 cópia», «Cena 1 cópia 2»…"""
    taken = {str(n).strip().lower() for n in names}
    base = "{} {}".format(name, word)
    out, n = base, 1
    while out.lower() in taken:
        n += 1
        out = "{} {}".format(base, n)
    return out


def transition_of(found):
    """(0.479) The «Transição» slider's value: the first scene's arrival time (the Presentation's), else 1,2 s."""
    return float(found[0].transition_s) if found else float(DEFAULTS["transition_s"])


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
