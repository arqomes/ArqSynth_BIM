"""(0.362) The model for the ArqSynth Presentation — the owner's platform of presentations (its code in C:\\BIM\\arqsynth;
the owner, 2026-11-02: «cenas 3D, cortes, animações, efeitos etc. podia ser preparada aqui no BIM e depois migrada para
a plataforma de apresentação»): one GLB, the model and what its presentation is made of together.

- The layers: an element each, as the Presentation makes its own, with its storey and category for its folders; its
  id from the element's GlobalId («bim_…»), the same in every export — a model sent again keeps the scenes and the
  sheets made over there.
- The scenes: a general view; each named 3D view (its camera, the categories it hides, its section box); each storey's
  plan (seen from above, cut at its cut height, the other storeys hidden); each section (its plane, seen along it).
- The sun: the view style's, or the site's place.
- (0.363) What was chosen in the Presentation panel (model/presentation.py): the scenes' order, the one it opens on,
  those kept out of the sequence, per scene its transition, effect, caption and time — and its thumbnail (a small
  JPEG of its view, made by the window).

The description goes in the GLB's asset extras («arqsynth»): the brand's handoff envelope 1.0, the ArqSynth Concept's
(`lib/concept/integration.ts`), its target the Presentation, its source the BIM. It says what was meant (a camera, a
cut, a hidden category), not how the Presentation keeps it: its importer makes its own scenes with its own functions,
so a newer Presentation still reads an older file. Coordinates as the GLB's (gltf_export): metres, Y up, the model's
offset taken off. Node names as three.js will give them (PropertyBinding.sanitizeNodeName), each one unique here — on a
name met twice three.js adds «_1», and the layers name the nodes — and the meshes and the scene left without one (three
names a mesh «mesh_N»). Pure NumPy and json."""

import base64
import datetime
import json
import math
import os
import re

import numpy as np

from ..i18n import t
from . import camera_moves
from . import gltf_export
from . import presentation as presentation_model

KEY = "arqsynth"                        # the GLB's asset.extras key
FORMAT, FORMAT_VERSION = "arqsynth-ecosystem-handoff", "1.0"
SCHEMA = 1                              # of the "model3d" payload
LAYER_ID, SCENE_ID = "bim_", "bim_scene_"
FOV = 50.0                              # degrees, vertical (three.js's): the general view's
PLAN_FOV = 35.0                         # a plan's, a section's (a long lens: little perspective)
NEAR, FAR = 0.05, 2000.0
OVERVIEW = np.array((-1.0, -1.2, 0.9))  # where the general view's eye is from the model's middle: south-west, above
#                                         (the model's axes)
FRAME = 1.12                            # a scene framed with this much room round what it shows
_SPACES = re.compile(r"\s")
_RESERVED = re.compile(r"[\[\].:/]")
_MESH = re.compile(r"mesh_\d+(_\d+)?")


def three_name(name):
    """A node's name as three.js keeps it (PropertyBinding.sanitizeNodeName): blanks as «_», «[ ] . : /» left out."""
    return _RESERVED.sub("", _SPACES.sub("_", str(name)))


def _unique(base, used):
    """A name whose three.js form no other node has (used: those forms, this one added) — «Parede 1 (2)»."""
    base = str(base).strip() or "Elemento"
    name, n = base, 1
    while three_name(name) in used or _MESH.fullmatch(three_name(name)) or not three_name(name):
        n += 1
        name = "{} ({})".format(base, n)
    used.add(three_name(name))
    return name


def checksum(text):
    """The envelope's checksum, as the Concept's (FNV-1a over the text's UTF-16 code units, as JavaScript reads it)."""
    h = 0x811C9DC5
    data = text.encode("utf-16-le")
    for k in range(0, len(data), 2):
        h ^= data[k] | (data[k + 1] << 8)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return "fnv1a-{:08x}".format(h)


def _gl(point, offset):
    """A point of the model (Z up) in the GLB's coordinates (Y up, the offset taken off)."""
    return gltf_export._y_up(np.asarray(point, dtype=float) - offset)[0]


def _gl_dir(vector):
    return gltf_export._y_up(np.asarray(vector, dtype=float))[0]


def _rotate(q, v):
    """A vector turned by a quaternion (x, y, z, w) — pygfx's."""
    u, w = np.asarray(q[:3], dtype=float), float(q[3])
    v = np.asarray(v, dtype=float)
    return v + 2.0 * np.cross(u, np.cross(u, v) + w * v)


def _list(v, digits=4):
    return [round(float(c), digits) for c in v]


def _camera(position, target, up, fov, aspect=None):
    """A camera as the Presentation's CameraState says it (GLB coordinates)."""
    cam = {"projection": "perspective", "position": _list(position), "target": _list(target), "up": _list(up, 6),
           "fov": round(float(fov), 3), "orthographicZoom": None, "near": NEAR, "far": FAR, "locked": False}
    if aspect:
        cam["viewportAspect"] = round(float(aspect), 4)
    return cam


def _framed(target, forward, up, half_width, half_height, fov=PLAN_FOV, aspect=16 / 9):
    """A camera looking along `forward` at `target`, far enough to show half_width × half_height round it."""
    t_v = math.tan(math.radians(fov) / 2.0)
    distance = FRAME * max(half_height / t_v, half_width / (t_v * aspect), 0.5)
    forward = forward / np.linalg.norm(forward)
    return _camera(target - forward * distance, target, up, fov, aspect)


def _view_camera(snapshot, offset):
    """A named 3D view's camera (Viewport.camera_snapshot: pygfx's) as the Presentation's — always in perspective
    (a view without one seen with a long lens from as far as shows the same)."""
    q = snapshot.get("rotation") or (0.0, 0.0, 0.0, 1.0)
    forward, up = _rotate(q, (0.0, 0.0, -1.0)), _rotate(q, (0.0, 1.0, 0.0))
    position = np.asarray(snapshot.get("position", (0.0, 0.0, 0.0)), dtype=float)
    focus = snapshot.get("focus")
    target = np.asarray(focus, dtype=float) if focus is not None else position + forward * 10.0
    width, height = float(snapshot.get("width") or 1.0), float(snapshot.get("height") or 1.0)
    zoom = float(snapshot.get("zoom") or 1.0)
    aspect = width / height if height > 1e-9 else 16 / 9
    fov = float(snapshot.get("fov") or 0.0)
    if fov > 0:                         # (pygfx shares the fov out between width and height: its vertical one)
        fov = math.degrees(2.0 * math.atan(math.tan(math.radians(fov) / 2.0) / zoom * 2.0 / (1.0 + aspect)))
    else:
        half = height / zoom / 2.0
        fov = PLAN_FOV
        position = target - forward * (half / math.tan(math.radians(fov) / 2.0))
    return _camera(_gl(position, offset), _gl(target, offset), _gl_dir(up), fov, aspect)


def _plane(name, kind, normal, point, offset):
    """A cutting plane as THREE.Plane keeps it (what is kept: normal · p + constant ≥ 0), from the model's normal
    (towards what stays) and a point of it."""
    n = _gl_dir(np.asarray(normal, dtype=float) / np.linalg.norm(normal))
    return {"id": name, "type": kind, "normal": _list(n, 6), "constant": round(-float(n @ _gl(point, offset)), 4)}


def _box_planes(box, offset, name):
    """A section box's six planes (what is inside is kept)."""
    lo, hi = (np.asarray(c, dtype=float) for c in box)
    planes = []
    for k, axis in enumerate("xyz"):
        n = np.zeros(3)
        n[k] = 1.0
        planes.append(_plane("{}_{}_min".format(name, axis), "box", n, lo, offset))
        planes.append(_plane("{}_{}_max".format(name, axis), "box", -n, hi, offset))
    return planes


def _style(doc, key):
    """A view style (model/view_styles) as the Presentation's visual style: its mode, edges and shadows."""
    vstyle = doc.view_style(key) if hasattr(doc, "view_style") else None
    if vstyle is None:
        return {"mode": "material", "edges": True, "shadows": False}
    faces, colours = getattr(vstyle, "faces", "shaded"), getattr(vstyle, "colours", "category")
    mode = {"white": "white_concept", "none": "technical_lines", "xray": "xray"}.get(faces)
    if mode is None:
        mode = "rendered" if colours == "material" and getattr(vstyle, "shadows", False) else "material"
    return {"mode": mode, "edges": bool(getattr(vstyle, "edges", True)),
            "shadows": bool(getattr(vstyle, "shadows", False))}


def _sun(doc):
    """The sun: the site's place when it is known (the Presentation works it out by the day and the hour), else the
    usual view style's direction. North is the model's +Y, as the Presentation's −Z."""
    from . import view_styles
    style = view_styles.BUILTIN.get("shaded")
    sun = {"azimuth": round(float(getattr(style, "sun_azimuth", 213.0)), 2),
           "elevation": round(float(getattr(style, "sun_altitude", 47.0)), 2), "northOffset": 0.0}
    try:
        lat, lon, _elevation = doc.ifc.site_location()
    except (AttributeError, TypeError, ValueError):
        lat = lon = None
    if lat is not None and lon is not None:
        sun.update(useRealSun=True, latitude=round(float(lat), 6), longitude=round(float(lon), 6))
    else:
        sun["useRealSun"] = False
    return sun


def package(doc, name=None, thumbnails=None):
    """(the glTF JSON with the description in its asset extras, the binary buffer, the description) of the whole
    model for the Presentation. thumbnails: {scene key: JPEG bytes} (0.363). ValueError("empty") with no element to
    send."""
    from .. import __version__
    objects = [o for o in doc.objects.values()
               if getattr(o, "is_bim", False) and getattr(o, "mesh", None) is not None]
    elements, materials = gltf_export.gather(doc, objects)
    if not elements:
        raise ValueError("empty")
    project = _project(doc, name)
    by_guid = {o.id: o for o in objects}
    storey_of = {g: s for g, s in ((e["extras"].get("GlobalId"), getattr(by_guid.get(e["extras"].get("GlobalId")),
                                                                         "storey", None)) for e in elements)}
    used = set()
    root = _unique(project, used)
    storeys, folders = {}, {}
    for e in elements:                                  # the storeys' and the folders' names first
        if e["storey"] not in storeys:
            storeys[e["storey"]] = _unique(e["storey"], used)
    for e in elements:
        key = (e["storey"], e["category"])
        if key not in folders:
            folders[key] = _unique("{} · {}".format(e["category"], e["storey"]), used)
    named = []
    for e in elements:
        named.append(dict(e, name=_unique(e["name"], used), storey=storeys[e["storey"]],
                          category=folders[(e["storey"], e["category"])],
                          extras=dict(e["extras"], name=e["name"])))
    for e in named:                                     # (0.483) its glass / water in a node of its own, its layer's
        see = [k for k in e["parts"] if materials[k]["alpha"] < 0.999]
        if see and len(see) < len(e["parts"]):
            word = t("gltf.water_part" if any(materials[k]["finish"] == "water" for k in see) else "gltf.glass_part")
            e["clear_name"] = _unique("{} {}".format(e["extras"]["name"], word), used)
    gltf, binary = gltf_export.build(named, materials, root, "ArqSynth BIM " + __version__)
    for mesh in gltf["meshes"]:
        mesh.pop("name", None)
    gltf["scenes"][0].pop("name", None)
    offset = np.asarray(gltf["scenes"][0]["extras"]["offset"], dtype=float)
    layers = _layers(gltf)
    model3d = {"schema": SCHEMA, "units": "meters", "up": "Y", "northOffset": 0.0, "offset": _list(offset, 6),
               "bounds": _bounds(gltf), "layers": layers}
    chosen = presentation_model.scenes(doc)
    model3d["scenes"] = _scenes(doc, gltf, layers, storey_of, offset, chosen, thumbnails or {})
    sent = {s["id"] for s in model3d["scenes"]}
    first = presentation_model.initial(doc, [s for s in chosen if SCENE_ID + s.key in sent])
    model3d["initialSceneId"] = SCENE_ID + first if first else None
    model3d["sun"] = _sun(doc)
    model3d["materials"] = _materials(gltf)                 # (0.365) the glass, the water…
    model3d["lights"] = _lights(doc, gltf)                  # …and the lights, by their finishes and fixtures
    options = getattr(doc, "presentation", None) or presentation_model.empty()
    if options.get("labels", True) or options.get("walk", True):
        model3d["spaces"] = spaces(doc, offset, options.get("labels", True), options.get("walk", True))   # (0.366)
    description = {
        "format": FORMAT, "formatVersion": FORMAT_VERSION,
        "target": {"product": "ArqSynth Presentation", "code": "presentation"},
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "source": {"product": "ArqSynth BIM", "version": __version__, "projectName": project,
                   "scenarioId": _project_guid(doc), "scenarioName": _file_name(doc) or project},
        "presentation": {"model3d": model3d},
        "disclaimer": t("present.disclaimer"),
    }
    description["checksum"] = checksum(json.dumps(description, ensure_ascii=False, separators=(",", ":")))
    gltf["asset"]["extras"] = {KEY: description}
    return gltf, binary, description


def _project(doc, name=None):
    if name:
        return name
    try:
        projects = doc.ifc.file.by_type("IfcProject")
    except AttributeError:
        projects = []
    return (projects[0].Name if projects else "") or _file_name(doc) or t("gltf.model")


def _project_guid(doc):
    try:
        projects = doc.ifc.file.by_type("IfcProject")
        return projects[0].GlobalId if projects else "projeto"
    except AttributeError:
        return "projeto"


def _file_name(doc):
    path = getattr(doc, "path", None)
    return os.path.splitext(os.path.basename(path))[0] if path else ""


def _layers(gltf):
    """An element's layer each, by its node alone — the Presentation finds a mesh's layer going up its parents; the
    meshes' own names («mesh_N») change when it compresses the file (identical meshes made one):
    {id, name, globalId, ifcClass, type, storey, category, nodeIds}."""
    out = []
    nodes = gltf["nodes"]
    for node in nodes:
        extras = node.get("extras") or {}
        guid = extras.get("GlobalId")
        if "mesh" not in node or not guid:
            continue
        parts = [three_name(nodes[c]["name"]) for c in node.get("children", ())   # (0.483: its glass / water node —
                 if (nodes[c].get("extras") or {}).get("part") == "clear"]           #  the Presentation sorts a part by
        out.append({"id": LAYER_ID + guid, "name": extras.get("name") or node["name"], "globalId": guid,  # its own
                    "ifcClass": extras.get("ifcClass", ""), "type": extras.get("type", ""),        # material first)
                    "storey": extras.get("storey", ""), "category": extras.get("category", ""),
                    "nodeIds": [three_name(node["name"])] + parts})
    return out


def _meshes_of(gltf, node):
    """(0.483) An element's meshes: its node's and its glass / water child's."""
    nodes = gltf["nodes"]
    out = [gltf["meshes"][node["mesh"]]] if "mesh" in node else []
    for c in node.get("children", ()):
        if (nodes[c].get("extras") or {}).get("part") == "clear" and "mesh" in nodes[c]:
            out.append(gltf["meshes"][nodes[c]["mesh"]])
    return out


SPECIAL_FINISHES = ("glass", "frosted", "water")


def _materials(gltf):
    """(0.365) The materials the Presentation draws with a pipeline of its own — glass, frosted glass, water —, by
    their name in the GLB (its materials' key): [{name, finish, color "#rrggbb"}], each name once."""
    out, seen = [], set()
    for m in gltf.get("materials", ()):
        finish = (m.get("extras") or {}).get("finish")
        if finish not in SPECIAL_FINISHES or m.get("name") in seen:
            continue
        seen.add(m.get("name"))
        rgb = np.clip(np.asarray(m["pbrMetallicRoughness"]["baseColorFactor"][:3], dtype=float), 0.0, 1.0)
        srgb = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * rgb ** (1 / 2.4) - 0.055)
        out.append({"name": m.get("name", ""), "finish": finish,
                    "color": "#" + "".join("{:02x}".format(int(round(float(c) * 255))) for c in srgb)})
    return out


def _lights(doc, gltf):
    """(0.365) The light fixtures (IfcLightFixture): [{nodeId, name, lumens, materials}] — their node (three.js's
    name), their flux (render_scene.light_flux: by their kind), the materials of their faces — for the Presentation
    to make them shine."""
    from .render_scene import light_flux
    names = [m.get("name", "") for m in gltf.get("materials", ())]
    out = []
    for node in gltf["nodes"]:
        extras = node.get("extras") or {}
        if extras.get("ifcClass") != "IfcLightFixture" or "mesh" not in node:
            continue
        obj = doc.get(extras.get("GlobalId")) if hasattr(doc, "get") else None
        try:
            lumens = float(light_flux(doc.ifc, obj)) if obj is not None else 0.0
        except (AttributeError, TypeError, ValueError):
            lumens = 0.0
        used = []
        for prim in (p for mesh in _meshes_of(gltf, node) for p in mesh["primitives"]):   # (0.483: its glass too)
            name = names[prim["material"]] if "material" in prim else ""
            if name and name not in used:
                used.append(name)
        out.append({"nodeId": three_name(node["name"]), "name": extras.get("name") or node["name"],
                    "lumens": round(lumens, 1), "materials": used})
    return out


DOOR_STEP = 0.6         # (0.366) m: a door's way through starts and ends this far from its middle, on each side


def _across(obj, doc=None):
    """(0.366) The horizontal direction across a door (through its wall): its placement's own (the IFC door's local y,
    square to its wall), else its plan's narrowest way (its outline's smallest spread); None without either."""
    try:
        m = np.asarray(doc.ifc.placement(obj.id), dtype=float)
        d = m[:2, :3] @ np.array((0.0, 1.0, 0.0))
        if np.linalg.norm(d) > 1e-6:
            return d / np.linalg.norm(d)
    except (AttributeError, TypeError, ValueError, KeyError):
        pass
    v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)[:, :2]
    if len(v) < 3:
        return None
    w, vec = np.linalg.eigh(np.cov((v - v.mean(axis=0)).T))
    d = vec[:, int(np.argmin(w))]
    return d / np.linalg.norm(d) if np.linalg.norm(d) > 1e-9 else None


def spaces(doc, offset, labels=True, walk=True):
    """(0.366) The rooms for the Presentation — as labels (their name, number and area) and as the Virtual Walk's zones
    (their outline at their floor, their storey) — with the storeys they are on, the doors between them (each door's
    middle at its floor, the way across it, the room on each side: None outside) and the stairs between storeys (from
    their foot to their head, the rooms there). In the GLB's axes. {labels, walk, floors, rooms, doors, stairs,
    start}: start the room one comes in by (behind a door from outside, on the lowest storey), else the largest there."""
    rooms = presentation_model.spaces(doc)
    storeys = {g: (n, z) for g, n, z in doc.storeys()}
    floors, out_rooms = [], []
    for k, (guid, (name, z)) in enumerate(sorted(storeys.items(), key=lambda item: item[1][1])):
        if any(r.get("storey") == guid for r in rooms):
            floors.append({"id": guid, "name": name, "elevation": round(float(z) - float(offset[2]), 4),
                           "order": len(floors)})
    for r in rooms:
        outline = [(float(x) - offset[0], -(float(y) - offset[1])) for x, y in r["outline"]]
        level = float(r["level"]) - float(offset[2])
        inner = camera_moves.room_from_polygon(outline, level, float(r["height"]))
        if inner is None:
            continue
        name = r.get("name") or r.get("number") or ""
        area = float(r.get("area") or 0.0) or presentation_model._area(r["outline"])
        out_rooms.append({"id": r["guid"], "name": name, "number": r.get("number", ""), "area": round(area, 2),
                          "storey": r.get("storey"), "external": bool(r.get("external")),
                          "kind": presentation_model.room_kind(name, r.get("external")),
                          "outline": [[round(x, 4), round(z, 4)] for x, z in outline], "level": round(level, 4),
                          "height": round(float(r["height"]), 4), "center": _list(inner.center)})
    known = {r["id"] for r in out_rooms}

    def room_at(point):
        holding = [r for r in rooms if r["guid"] in known and presentation_model._holds(r, point)]
        return min(holding, key=lambda r: presentation_model._area(r["outline"]))["guid"] if holding else None

    doors, stairs = [], []
    for obj in doc.objects.values():
        if not getattr(obj, "is_bim", False) or getattr(obj, "mesh", None) is None:
            continue
        if obj.ifc_class == "IfcDoor":
            across = _across(obj, doc)
            lo, hi = (np.asarray(c, dtype=float) for c in obj.mesh.bounds())
            if across is None:
                continue
            middle = np.array(((lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, lo[2]))
            probe = middle + np.array((0.0, 0.0, 1.0))
            a = room_at(probe + np.append(across, 0.0) * DOOR_STEP)
            b = room_at(probe - np.append(across, 0.0) * DOOR_STEP)
            if a is None and b is None or a == b:
                continue
            if a is None:                                   # (from inside: the room first)
                a, b, across = b, a, -across
            way = -across                                   # (a is on the +across side: one goes the other way)
            doors.append({"id": obj.id, "name": obj.name, "point": _list(_gl(middle, offset)),
                          "way": _list(_gl_dir((float(way[0]), float(way[1]), 0.0)), 6), "from": a, "to": b})
        elif obj.ifc_class == "IfcStair":
            v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
            if len(v) < 3 or np.ptp(v[:, 2]) < 0.5:
                continue
            foot = v[v[:, 2] <= v[:, 2].min() + 0.05].mean(axis=0)
            head = v[v[:, 2] >= v[:, 2].max() - 0.05].mean(axis=0)
            a, b = room_at(foot + (0.0, 0.0, 0.3)), room_at(head + (0.0, 0.0, 0.3))
            if a and b and a != b:
                stairs.append({"id": obj.id, "name": obj.name, "from": a, "to": b,
                               "points": [_list(_gl(foot, offset)), _list(_gl(head, offset))]})
    lowest = min((f["elevation"] for f in floors), default=None)
    ground = [r for r in out_rooms if lowest is not None and abs(r["level"] - lowest) < 0.5]
    entries = [d["from"] for d in doors if d["to"] is None and d["from"] in {r["id"] for r in ground}]
    start = entries[0] if entries else (max(ground, key=lambda r: r["area"])["id"] if ground else None)
    return {"labels": bool(labels), "walk": bool(walk), "floors": floors, "rooms": out_rooms, "doors": doors,
            "stairs": stairs, "start": start}


def _bounds(gltf):
    lo = np.min([a["min"] for a in gltf["accessors"] if "min" in a], axis=0)
    hi = np.max([a["max"] for a in gltf["accessors"] if "max" in a], axis=0)
    return {"min": _list(lo), "max": _list(hi)}


def _hidden(layers, classes=(), keep=None):
    """The layers a scene hides: those of the IFC classes hidden, and (keep given) those keep() says no to."""
    classes = set(classes or ())
    return [l["id"] for l in layers if l["ifcClass"] in classes or (keep is not None and not keep(l))]


def overview_eye(centre, radius):
    """Where the general view's eye is (the model's axes, Z up): south-west of the middle and above it, as far as
    shows the whole model with the three.js lens (FOV)."""
    eye = OVERVIEW / np.linalg.norm(OVERVIEW)
    return np.asarray(centre, dtype=float) + eye * FRAME * max(float(radius), 1.0) / math.sin(math.radians(FOV) / 2.0)


def _chosen(scene, thumbnails):
    """What was chosen for a scene in the Presentation panel, as the description says it (seconds, not the
    Presentation's milliseconds): {hidden, transition, effect?, narration?, thumbnail?}."""
    out = {"hidden": scene.hidden, "transition": {"type": scene.transition, "seconds": scene.transition_s},
           "environment": {"sun": {"day": scene.sun_day, "minutes": scene.sun_minutes, "animate": scene.sun_animate},
                           "exposure": scene.exposure, "sky": scene.sky}}           # (0.365)
    if scene.effect != "none":
        out["effect"] = {"type": scene.effect, "seconds": scene.effect_s}
    if scene.caption or scene.seconds:
        out["narration"] = {"caption": scene.caption, "seconds": scene.seconds}
    jpeg = thumbnails.get(scene.key)
    if jpeg:
        out["thumbnail"] = {"mimeType": "image/jpeg", "data": base64.b64encode(bytes(jpeg)).decode("ascii")}
    return out


def _move(doc, scene, building, rooms, offset):
    """(0.364) A scene's camera move as the description says it: the move's name (the Presentation's library), its
    time, and the measures it is made from — the building's, and inside a room the room's — so the Presentation makes
    it with its own library from the same numbers the BIM showed it with: {cameraMove: {preset, seconds, building,
    room?}} or {}."""
    if not scene.move:
        return {}
    out = {"preset": scene.move, "seconds": round(float(presentation_model.move_seconds(scene)), 2),
           "building": {"center": _list(building.center), "radius": round(float(building.radius), 4),
                        "size": _list(building.size)}}
    if camera_moves.interior(scene.move):
        room = presentation_model.room_measures(presentation_model.room_of(doc, scene, rooms), offset)
        if room is not None:
            out["room"] = room.as_dict()
    return {"cameraMove": out}


def _tuned_camera(scene, camera, offset):
    """(0.479) A scene's camera as the ArqSynth Presentation tab kept it: where its eye and target are (a scene that is
    not a named 3D view: the view's own camera otherwise), its lens (the Presentation's vertical FOV), its projection —
    orthographic: the Presentation's stored zoom, 2 / the height seen at the target —, locked or not."""
    cam = dict(camera)
    if scene.eye and scene.target and scene.kind != "view3d":
        eye, target = _gl(scene.eye, offset), _gl(scene.target, offset)
        d = target - eye
        straight = np.linalg.norm(d) > 1e-9 and abs(float(d[1])) / float(np.linalg.norm(d)) > 0.999
        cam = _camera(eye, target, (0.0, 0.0, -1.0) if straight else (0.0, 1.0, 0.0), cam["fov"],
                      cam.get("viewportAspect"))       # (seen from right above: north up)
    if scene.projection == "orthographic":            # (the height seen with the lens it was framed with)
        distance = float(np.linalg.norm(np.subtract(cam["target"], cam["position"])))
        height = 2.0 * max(distance, 1e-3) * math.tan(math.radians(float(cam["fov"])) / 2.0)
        cam["projection"] = "orthographic"
        cam["orthographicZoom"] = round(2.0 / max(height, 1e-9), 6)
    elif scene.projection == "perspective":
        cam["projection"], cam["orthographicZoom"] = "perspective", None
    if scene.fov > 0:
        cam["fov"] = round(float(scene.fov), 3)
    if scene.locked:
        cam["locked"] = True
    return cam


def _tuned_style(scene, style):
    """(0.479) A scene's visual style as the Presentation tab kept it: its mode («Renderizado», «Branco
    conceptual»…), and with it the quality and the ambient occlusion of the Presentation's «Renderizado · Auto» menu."""
    out = dict(style)
    if scene.style:
        out["mode"] = scene.style
    if scene.style or scene.quality != "auto" or not scene.ao or scene.ao_intensity != 1.0:
        out.update(qualityProfile=scene.quality, ambientOcclusion=bool(scene.ao),
                   ambientOcclusionIntensity=round(float(scene.ao_intensity), 2))
    return out


def _scenes(doc, gltf, layers, storey_of, offset, chosen, thumbnails):
    """The scenes in the order chosen (model/presentation.scenes): the general view, the named 3D views, the plans,
    the sections — as the description's scenes."""
    from .view_templates import CUT_HEIGHT
    b = _bounds(gltf)
    lo, hi = np.asarray(b["min"]), np.asarray(b["max"])
    centre, half = (lo + hi) / 2.0, (hi - lo) / 2.0
    views = {v.uid: v for v in getattr(doc, "views3d", ())}
    sections = {s.uid: s for s in getattr(doc, "sections", ())}
    storeys = {g: (n, z) for g, n, z in doc.storeys()}
    guid_storey = {l["id"]: storey_of.get(l["globalId"]) for l in layers}
    building = camera_moves.Building.of_box(lo, hi)
    rooms = presentation_model.spaces(doc) if any(camera_moves.interior(s.move) for s in chosen) else []
    scenes = []
    known = {l["id"] for l in layers}

    def add(scene, camera, hidden=(), planes=(), style=None):
        hidden = list(hidden)
        hidden += [i for i in (LAYER_ID + g for g in scene.hidden_layers) if i in known and i not in hidden]   # (0.479)
        scenes.append(dict({"id": SCENE_ID + scene.key, "name": scene.name, "order": len(scenes), "kind": scene.kind,
                            "camera": _tuned_camera(scene, camera, offset), "hiddenLayers": hidden,
                            "section": {"planes": list(planes)} if planes else None,
                            "style": _tuned_style(scene, style or {"mode": "material", "edges": True,
                                                                   "shadows": False})},
                           **_chosen(scene, thumbnails), **_move(doc, scene, building, rooms, offset)))

    for scene in chosen:
        ref = scene.key.split("_", 1)[1] if "_" in scene.key else ""
        if scene.kind == "overview":                    # from the south-west, above
            eye = centre + _gl_dir(overview_eye(np.zeros(3), np.linalg.norm(half)))
            add(scene, _camera(eye, centre, (0.0, 1.0, 0.0), FOV))
        elif scene.kind == "view3d" and ref in views:
            view = views[ref]
            settings = doc.view_settings(("3d", view.uid))
            planes = _box_planes(settings.box, offset, "box_" + view.uid) if settings.box else ()
            add(scene, _view_camera(view.camera, offset), _hidden(layers, settings.hidden), planes,
                _style(doc, settings.style))
        elif scene.kind == "plan" and ref in storeys:
            guid, (_name, z) = ref, storeys[ref]
            mine = [l for l in layers if guid_storey[l["id"]] == guid]
            if not mine:
                continue
            settings = doc.view_settings(("plan", guid))
            cut = z + float(settings.cut_height if settings.cut_height is not None else CUT_HEIGHT)
            nodes = _layer_bounds(gltf, {l["id"] for l in mine})
            p_lo, p_hi = nodes if nodes is not None else (lo, hi)
            target = np.array(((p_lo[0] + p_hi[0]) / 2.0, z - offset[2], (p_lo[2] + p_hi[2]) / 2.0))
            camera = _framed(target, np.array((0.0, -1.0, 0.0)), (0.0, 0.0, -1.0), (p_hi[0] - p_lo[0]) / 2.0,
                             (p_hi[2] - p_lo[2]) / 2.0)                 # (from above, north up)
            hide = _hidden(layers, settings.hidden, keep=lambda l, g=guid: guid_storey[l["id"]] in (g, None))
            add(scene, camera, hide,
                [_plane("planta_" + guid, "plan_cut", (0.0, 0.0, -1.0), (0.0, 0.0, cut), offset)])
        elif scene.kind == "section" and ref in sections:
            section = sections[ref]
            n = np.asarray(section.normal, dtype=float)
            n = np.array((n[0], n[1], 0.0))
            n /= np.linalg.norm(n)
            settings = doc.view_settings(("section", section.name))
            n_gl = _gl_dir(n)
            across = np.cross((0.0, 1.0, 0.0), n_gl)                     # (along the section line, in the GLB)
            on_plane = _gl(section.point, offset)
            target = centre + n_gl * float((on_plane - centre) @ n_gl)
            camera = _framed(target, n_gl, (0.0, 1.0, 0.0), float(np.abs(across) @ half), float(half[1]))
            add(scene, camera, _hidden(layers, settings.hidden),
                [_plane("corte_" + section.uid, "vertical", n, section.point, offset)])
    return scenes


def _layer_bounds(gltf, layer_ids):
    """(lowest, highest corner) in the GLB of the nodes of these layers, or None."""
    wanted = {i[len(LAYER_ID):] for i in layer_ids}
    found = []
    for node in gltf["nodes"]:
        if "mesh" in node and (node.get("extras") or {}).get("GlobalId") in wanted:
            for prim in (p for mesh in _meshes_of(gltf, node) for p in mesh["primitives"]):
                a = gltf["accessors"][prim["attributes"]["POSITION"]]
                found += [a["min"], a["max"]]
    if not found:
        return None
    return np.min(found, axis=0), np.max(found, axis=0)


def export(doc, path, name=None, thumbnails=None):
    """The model for the Presentation in a GLB at `path`: {elements, triangles, layers, scenes}. thumbnails: {scene
    key: JPEG bytes}. ValueError("empty") with nothing to send."""
    gltf, binary, description = package(doc, name, thumbnails)
    with open(path, "wb") as fh:
        fh.write(gltf_export.glb(gltf, binary))
    model3d = description["presentation"]["model3d"]
    return {"elements": len(model3d["layers"]), "triangles": sum(a["count"] for a in gltf["accessors"][::2]) // 3,
            "layers": len(model3d["layers"]), "scenes": len(model3d["scenes"])}


def read(path):
    """The description in a GLB written here, or None (a GLB from elsewhere)."""
    gltf, _binary = gltf_export.read(path)
    found = ((gltf.get("asset") or {}).get("extras") or {}).get(KEY)
    return found if isinstance(found, dict) and found.get("format") == FORMAT else None
