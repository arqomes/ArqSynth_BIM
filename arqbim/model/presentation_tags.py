"""(0.485) The labels placed in the Presentation tab — the ArqSynth Presentation's «Etiquetas» (its SpaceLabel,
lib/editor3d/space-labels.ts and components/editor3d/SpaceLabels.tsx): a name, a note (an area…), a number, a
rectangle or a circle, its colours, size and turn, and where it is — lying on a floor, on a wall, standing on its
posts, or beside a wall at the end of a leader line —, at the point of the model it was put on and that surface's
normal. The model's labels are one list (Document.presentation["tags"]); each scene keeps those it hides.

Kept in the model's axes (Z up); sent in the GLB's (Y up) as the Presentation's own fields. The quad of each label
is worked out here as the Presentation's (labelBasis, standingYaw): its four corners and its lines (posts, leader) —
the BIM's 3D view draws the picture of the label there. Pure Python and NumPy."""

import copy
import math
import uuid

import numpy as np

PLACEMENTS = ("floor", "wall", "standing", "wall_leader")
SHAPES = ("rect", "circle")
LIFT = 0.015                    # m: the quad over the surface it lies on (the Presentation's)
MAX_TAGS = 200
DEFAULT = {"title": "", "note": "", "number": "", "shape": "rect", "placement": "floor", "position": (0.0, 0.0, 0.0),
           "normal": (0.0, 0.0, 1.0), "rotation": 0.0, "scale": 1.0, "title_scale": 1.0, "note_scale": 1.0,
           "background": "#9ec8a0", "opacity": 1.0, "text_color": "#111111", "leader": 0.8, "face_camera": False,
           "hide_occluded": True}
LIMITS = {"rotation": (-360.0, 360.0), "scale": (0.2, 5.0), "title_scale": (0.4, 3.0), "note_scale": (0.4, 3.0),
          "opacity": (0.0, 1.0), "leader": (0.1, 5.0)}


def _colour(value, fallback):
    text = str(value or "").strip()
    if len(text) == 7 and text.startswith("#"):
        try:
            int(text[1:], 16)
            return text.lower()
        except ValueError:
            pass
    return fallback


def _point(value, fallback):
    try:
        p = tuple(round(float(c), 4) for c in value)
    except (TypeError, ValueError):
        return fallback
    return p if len(p) == 3 and all(c == c and abs(c) < 1e7 for c in p) else fallback


def clean_tag(tag):
    """A label as it may be kept (its id kept; every field in its kind and range), or None when it is not one."""
    if not isinstance(tag, dict) or not str(tag.get("id") or "").strip():
        return None
    out = {"id": str(tag["id"]).strip()}
    for name, default in DEFAULT.items():
        value = tag.get(name, default)
        if name in ("position", "normal"):
            value = _point(value, default)
        elif name in ("background", "text_color"):
            value = _colour(value, default)
        elif name == "shape":
            value = value if value in SHAPES else default
        elif name == "placement":
            value = value if value in PLACEMENTS else default
        elif isinstance(default, bool):
            value = bool(value)
        elif isinstance(default, float):
            try:
                lo, hi = LIMITS[name]
                value = round(min(max(float(value), lo), hi), 3)
            except (TypeError, ValueError):
                value = default
        else:
            value = str(value or "").strip()
        out[name] = value
    n = np.asarray(out["normal"], dtype=float)
    out["normal"] = tuple(round(float(c), 6) for c in n / np.linalg.norm(n)) if np.linalg.norm(n) > 1e-9 \
        else DEFAULT["normal"]
    return out


def clean_tags(tags):
    """The model's labels as they may be kept (each id once)."""
    out, seen = [], set()
    for tag in tags if isinstance(tags, (list, tuple)) else ():
        tag = clean_tag(tag)
        if tag is not None and tag["id"] not in seen:
            seen.add(tag["id"])
            out.append(tag)
    return out[:MAX_TAGS]


def free_number(tags, base):
    """The lowest number not taken by a label «<base> N» (the Presentation's nextSceneNumber)."""
    taken = {str(t.get("title", "")).strip().lower() for t in tags}
    n = 1
    while "{} {}".format(base, n).lower() in taken:
        n += 1
    return n


LOOK = ("shape", "background", "opacity", "text_color", "scale", "rotation", "title_scale", "note_scale", "leader",
        "face_camera", "hide_occluded")


def look_of(tag):
    """What a new label takes of another (the Presentation's spaceLabelStyleOf: its look, not where it is, the
    surface's normal, its name nor its note)."""
    return {name: tag[name] for name in LOOK if name in tag} if tag else None


def new_tag(placement, position, normal, tags=(), base="Ambiente", style=None):
    """A label put on the model (the Presentation's createSpaceLabel): «Ambiente N», N the lowest free; its look the
    one given (the label chosen, or the last one put: «o aspecto que uma etiqueta nova herda da anterior»)."""
    number = free_number(tags, base)
    tag = dict(DEFAULT, id=uuid.uuid4().hex[:12], title="{} {}".format(base, number),
               number="{:02d}".format(number), placement=placement if placement in PLACEMENTS else "floor",
               position=tuple(position), normal=tuple(normal),
               leader=1.1 if placement == "standing" else 0.8)
    for name in LOOK:
        if style and name in style:
            tag[name] = style[name]
    return clean_tag(tag)


def snap_angle(value, step=45.0, tolerance=6.0):
    """The turn near a multiple of `step` (by `tolerance` degrees) put on it, 0–359 (the Presentation's snapAngleDeg:
    «uma etiqueta torta um grau lê-se como um erro de desenho»); else as it is."""
    value = float(value)
    nearest = round(value / step) * step
    if abs(value - nearest) > tolerance:
        return value
    return float(nearest % 360)


def turns(tag):
    """Is its turn its own (on a floor, on a wall, standing not facing the camera)? (the Presentation's `rotates`)"""
    return tag["placement"] in ("floor", "wall") or (tag["placement"] == "standing" and not tag["face_camera"])


def size(tag, aspect):
    """(width, height) of the label's quad in m: the Presentation's (a rectangle 0,55 m high, a circle 0,95 m)."""
    h = (0.95 if tag["shape"] == "circle" else 0.55) * float(tag["scale"])
    return h * float(aspect), h


def _turn(v, axis, degrees):
    """v turned `degrees` about the unit `axis` (Rodrigues)."""
    a = math.radians(degrees)
    v, k = np.asarray(v, dtype=float), np.asarray(axis, dtype=float)
    return v * math.cos(a) + np.cross(k, v) * math.sin(a) + k * float(k @ v) * (1 - math.cos(a))


def frame(tag, aspect, toward=None):
    """Where the label is drawn, in the model's axes: {"corners": 4 points (bottom left, bottom right, top right, top
    left — the picture's), "lines": [(a, b)] its posts or its leader}. As the Presentation's: on a floor or a wall the
    quad lies on the surface (its up the north on a floor, the vertical on a wall), turned by «rotation»; standing it
    faces the surface's normal turned by «rotation» — or, «face_camera», `toward` (the way to the viewer) —, high on
    its posts; beside a wall it goes along the wall at the end of its leader."""
    w, h = size(tag, aspect)
    p = np.asarray(tag["position"], dtype=float)
    n = np.asarray(tag["normal"], dtype=float)
    lines = []
    if tag["placement"] == "standing":
        if tag["face_camera"] and toward is not None and np.hypot(toward[0], toward[1]) > 1e-9:
            face = np.array((toward[0], toward[1], 0.0))
        else:
            gl_x, gl_z = n[0], -n[1]                      # (the Presentation's yaw: atan2(n.x, n.z) in its axes)
            yaw = (math.atan2(gl_x, gl_z) if gl_x * gl_x + gl_z * gl_z > 1e-6 else 0.0) + math.radians(tag["rotation"])
            face = np.array((math.sin(yaw), -math.cos(yaw), 0.0))
        face /= np.linalg.norm(face)
        x = np.cross((0.0, 0.0, 1.0), face)
        y = np.array((0.0, 0.0, 1.0))
        post = max(float(tag["leader"]), 0.1)
        centre = p + y * (post + h / 2.0)
        offsets = (0.0,) if tag["shape"] == "circle" else (-w * 0.33, w * 0.33)
        lines = [(p + x * o, p + x * o + y * post) for o in offsets]
    else:
        seed = np.array((0.0, 1.0, 0.0)) if abs(n[2]) > 0.9 else np.array((0.0, 0.0, 1.0))  # (north on a floor)
        x = np.cross(seed, n)
        x /= np.linalg.norm(x)
        y = np.cross(n, x)
        x, y = _turn(x, n, tag["rotation"]), _turn(y, n, tag["rotation"])
        centre = p + n * LIFT
        if tag["placement"] == "wall_leader":
            reach = max(float(tag["leader"]), 0.1)
            lines = [(p + n * 0.02, p + n * 0.02 + x * reach)]
            centre = p + n * 0.02 + x * (reach + w / 2.0)
    hx, hy = x * (w / 2.0), y * (h / 2.0)
    corners = [centre - hx - hy, centre + hx - hy, centre + hx + hy, centre - hx + hy]
    return {"corners": [tuple(float(c) for c in q) for q in corners],
            "lines": [(tuple(float(c) for c in a), tuple(float(c) for c in b)) for a, b in lines]}


def to_presentation(tag, gl_point, gl_dir):
    """A label as the Presentation's SpaceLabel (gl_point / gl_dir: the GLB's axes) — its id «bim_tag_<id>»."""
    return {"id": "bim_tag_" + tag["id"], "title": tag["title"], "note": tag["note"], "number": tag["number"],
            "shape": tag["shape"], "placement": tag["placement"],
            "position": [round(float(c), 4) for c in gl_point(tag["position"])],
            "normal": [round(float(c), 6) for c in gl_dir(tag["normal"])], "rotationDeg": tag["rotation"],
            "scale": tag["scale"], "titleScale": tag["title_scale"], "noteScale": tag["note_scale"],
            "background": tag["background"], "opacity": tag["opacity"], "textColor": tag["text_color"],
            "leaderLength": tag["leader"], "faceCamera": tag["face_camera"], "hideWhenOccluded": tag["hide_occluded"]}


def with_tag(tags, tag):
    """The labels with this one put (in its place when it was there, else at the end)."""
    out = [copy.deepcopy(t) for t in clean_tags(tags)]
    tag = clean_tag(tag)
    if tag is None:
        return out
    for k, t in enumerate(out):
        if t["id"] == tag["id"]:
            out[k] = tag
            return out
    return (out + [tag])[:MAX_TAGS]


def without(tags, tag_id):
    return [copy.deepcopy(t) for t in clean_tags(tags) if t["id"] != tag_id]
