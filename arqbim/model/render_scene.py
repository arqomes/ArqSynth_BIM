"""(0.343) The scene of a realistic render (render/path_tracer.py, Mitsuba 3): the model as the 3D view shows it —
its elements' and sketches' triangles in world coordinates (metres, Z up), gathered by finish and colour: each face
its material's colour (or its category's), its material's finish (matte, satin, glossy, metal, glass, frosted glass:
the one chosen in the material editor, else its category's); the lights (IfcLightFixture) with the faces that shine
down and how bright (their flux over that area); the camera of the view, the sun, the lighting (the sun; the sun and
the lights; the lights at nightfall), a ground under it all. Pure NumPy, saved in one file (npz) the render's own
process reads."""

import json
import math
from dataclasses import dataclass, field

import numpy as np

from . import controls, material_looks

# each material category's finish (catalog.MaterialSpec.category)
CATEGORY_FINISH = {"plaster": "matte", "gypsum": "matte", "insulation": "matte", "concrete": "matte",
                   "block": "matte", "brick": "matte", "earth": "matte", "stone": "satin", "wood": "satin",
                   "plastic": "satin", "ceramic": "glossy", "steel": "metal", "aluminium": "metal", "zinc": "metal",
                   "copper": "metal", "glass": "glass", "water": "water",
                   "fabric": "matte", "plant": "satin"}                     # (0.440: the loose furniture's)
FINISHES = ("matte", "satin", "glossy", "metal", "glass", "frosted", "water")    # (0.365: water)
FROSTED_ALPHA = 0.5             # a see-through face less clear than this: frosted glass
SKETCH_RGB = (0.92, 0.91, 0.87)
GROUND_RGB = (0.42, 0.44, 0.38)
GROUND_SIZE = 40.0              # the ground this many times the model's size round it…
GROUND_LEAST = 20000.0          # …and at least so many metres: out to the horizon (under it the sky is black)
LIGHTINGS = ("sun", "sun_lights", "night")    # the sun and the sky; the lights on too; the lights at nightfall
LUMENS = {"panel": 3600.0, "downlight": 800.0}    # a light's flux by its kind (its "Luminaria"), lm…
LUMENS_OTHER = 1500.0           # …another program's
LIGHT_DROP = 0.003              # m: the faces that shine this far under the ceiling they are flush with


@dataclass
class RenderScene:
    groups: list = field(default_factory=list)   # [(finish, (r, g, b) sRGB 0–1, triangles (T, 3, 3) float32)]
    eye: tuple = (10.0, -10.0, 8.0)
    target: tuple = (0.0, 0.0, 0.0)
    up: tuple = (0.0, 0.0, 1.0)
    fov: float = 45.0           # degrees, top to bottom; 0: seen without perspective…
    height: float = 0.0         # …this many metres top to bottom
    sun: tuple = (0.0, 0.0, 1.0)  # unit, towards the sun
    ground: tuple = None        # (z, half size) of a ground under the model, or None
    lights: list = field(default_factory=list)   # [(luminance cd/m², triangles)]: the lights' faces that shine
    lighting: str = "sun_lights"                 # LIGHTINGS
    exposure: float = 0.0       # EV, over the automatic one
    clean: bool = True          # its grain filtered out (render/path_tracer.clean)
    # (0.470) the groups of a material's own realistic look (their finish "look:" + its key): {group: its look
    # (look_dict)} and {group: its pictures' coordinates (T, 3, 2)} when it has pictures
    looks: dict = field(default_factory=dict)
    uvs: dict = field(default_factory=dict)

    @property
    def triangles(self):
        return sum(len(t) for _f, _c, t in self.groups) + sum(len(t) for _l, t in self.lights)

    def save(self, path):
        meta = {"groups": [[f, list(map(float, c))] for f, c, _t in self.groups], "eye": list(map(float, self.eye)),
                "target": list(map(float, self.target)), "up": list(map(float, self.up)), "fov": float(self.fov),
                "height": float(self.height), "sun": list(map(float, self.sun)),
                "ground": list(map(float, self.ground)) if self.ground is not None else None,
                "lights": [float(lum) for lum, _t in self.lights], "lighting": self.lighting,
                "exposure": float(self.exposure), "clean": bool(self.clean),
                "looks": {str(k): v for k, v in self.looks.items()}}                   # (0.470)
        arrays = {"t{}".format(k): np.asarray(t, dtype=np.float32) for k, (_f, _c, t) in enumerate(self.groups)}
        arrays.update({"l{}".format(k): np.asarray(t, dtype=np.float32) for k, (_l, t) in enumerate(self.lights)})
        arrays.update({"u{}".format(k): np.asarray(uv, dtype=np.float32) for k, uv in self.uvs.items()})
        np.savez_compressed(path, meta=np.array(json.dumps(meta)), **arrays)

    @staticmethod
    def load(path):
        data = np.load(path, allow_pickle=False)
        meta = json.loads(str(data["meta"]))
        groups = [(f, tuple(c), data["t{}".format(k)]) for k, (f, c) in enumerate(meta["groups"])]
        lights = [(lum, data["l{}".format(k)]) for k, lum in enumerate(meta.get("lights", ()))]
        looks = {int(k): v for k, v in (meta.get("looks") or {}).items()}
        uvs = {k: data["u{}".format(k)] for k in looks if "u{}".format(k) in data.files}
        return RenderScene(groups, tuple(meta["eye"]), tuple(meta["target"]), tuple(meta["up"]), meta["fov"],
                           meta["height"], tuple(meta["sun"]), tuple(meta["ground"]) if meta["ground"] else None,
                           lights, meta.get("lighting", "sun_lights"), float(meta.get("exposure", 0.0)),
                           bool(meta.get("clean", True)), looks, uvs)


def finish_of(category, alpha, own=""):
    """A face's finish: its material's own (chosen in the material editor), else by its category; see-through —
    glass, frosted when little clear."""
    if own in FINISHES:
        return own
    if alpha < 0.999:
        return "glass" if alpha <= FROSTED_ALPHA else "frosted"
    return CATEGORY_FINISH.get(category or "", "matte")


def look_of(spec):
    """(0.468) A material's realistic look (core/pbr.Look): its own, else its finish's — the one chosen before 0.468,
    else its category's."""
    from ..core import pbr
    if getattr(spec, "look", None) is not None:
        return spec.look
    alpha = 1.0 - float(getattr(spec, "transparency", 0.0) or 0.0)
    return pbr.from_finish(finish_of(getattr(spec, "category", ""), alpha, getattr(spec, "finish", "") or ""))


def own_look(key):
    """(0.470) A material's own realistic look (chosen in the Materials panel), or None (its finish's)."""
    from ..ifc import catalog
    spec = catalog.MATERIALS.get(key) if key else None
    return getattr(spec, "look", None)


def look_dict(look, beside=None):
    """(0.470) A realistic look as the render's process takes it: its values, its colours as sRGB 0–1 (tint_rgb: None
    for the face's own), its pictures {slot: [file found, turned over]} — those not found left out (beside: the
    project's folder, where a moved one is looked for)."""
    from dataclasses import asdict
    from ..core import pbr
    out = {k: v for k, v in asdict(look).items() if k not in ("maps", "tint", "emission_colour")}

    def rgb(text):
        text = str(text or "")
        return [int(text[k:k + 2], 16) / 255.0 for k in (1, 3, 5)] if len(text) == 7 else None
    out["tint_rgb"] = rgb(look.tint)
    out["emission_rgb"] = rgb(look.emission_colour) or [1.0, 1.0, 1.0]
    maps = {}
    for slot, path, inverted in look.maps:
        found = pbr.find(path, beside)
        if found:
            maps[slot] = [found, bool(inverted)]
    out["maps"] = maps
    return out


def light_flux(ifc, obj):
    """A light's flux (lm): by its kind (a panel, a downlight), another program's LUMENS_OTHER."""
    try:
        kind = ifc._params(ifc.by_guid(obj.id)).get("Luminaria")
    except (AttributeError, RuntimeError, TypeError, KeyError):
        kind = None
    return LUMENS.get(kind or "", LUMENS_OTHER)


def _shining(corners, normals):
    """Which of a light's faces shine: those facing down (none: all of them)."""
    down = np.asarray(normals, dtype=float).reshape(-1, 3)[:, 2] < -0.5
    return down if down.any() else np.ones(len(corners), dtype=bool)


def _area(triangles):
    t = np.asarray(triangles, dtype=float).reshape(-1, 3, 3)
    return float(np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1).sum() / 2.0)


@material_looks.one_pass()                      # (0.352: each wall's layers read once)
def gather(doc, objects, lights=None):
    """[(finish, rgb, triangles)] of these objects (the document's), their faces by finish and colour. lights: a list
    the lights' shining faces go to — [(luminance cd/m², triangles)], each light's flux spread over them —, the
    rest of them with the other faces (None: all their faces with the others)."""
    ifc = getattr(doc, "ifc", None)
    found = {}
    shining = {}
    try:
        left_out = controls.ids_with(doc, "no_render")       # (0.524: the navigator's camera off)
    except AttributeError:
        left_out = set()
    for obj in objects:
        if obj is None or obj.mesh is None or obj.id in left_out:
            continue
        if getattr(obj, "is_bim", False):
            try:
                seen = material_looks.look(ifc, obj, material_looks.category_rgb(obj.ifc_class), colours=True,
                                           patterns=False, clear=True)
            except (AttributeError, RuntimeError, ValueError, TypeError):
                continue
            corners = np.asarray(seen.corners, dtype=float)
            if not len(corners):
                continue
            none = np.full(len(corners), "", dtype=object)
            cats = seen.categories if seen.categories is not None else none
            own = seen.finishes if seen.finishes is not None else none
            rgb = np.round(np.clip(np.asarray(seen.rgb, dtype=float), 0.0, 1.0) * 255.0) / 255.0
            alpha = np.asarray(seen.alpha, dtype=float)
            keep = np.ones(len(corners), dtype=bool)
            if lights is not None and obj.ifc_class == "IfcLightFixture":
                keep = ~_shining(corners, seen.normals)
                lit = corners[~keep] - np.array((0.0, 0.0, LIGHT_DROP))
                area = _area(lit)
                if area > 1e-6:
                    nits = float("{:.3g}".format(light_flux(ifc, obj) / (math.pi * area)))
                    shining.setdefault(nits, []).append(lit)
                else:
                    keep[:] = True
            # (0.470) the faces of a material with a realistic look of its own: apart, by material ("look:" + key)
            keys = seen.materials if seen.materials is not None else none
            looked = {k for k in set(keys) if k and own_look(k) is not None}
            codes = {}
            index = np.array([codes.setdefault((("look:" + m) if m in looked else finish_of(c, a, o), tuple(r)),
                                               len(codes)) for c, a, r, o, m in zip(cats, alpha, rgb, own, keys)])
            for key, n in codes.items():
                found.setdefault(key, []).append(corners[(index == n) & keep])
        else:
            tris, _owner = obj.mesh.triangulate()
            if not len(tris):
                continue
            verts = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
            m = np.asarray(getattr(obj, "matrix", np.eye(4)), dtype=float)
            world = verts @ m[:3, :3].T + m[:3, 3]
            found.setdefault(("matte", SKETCH_RGB), []).append(world[np.asarray(tris)])
    if lights is not None:
        lights.extend((nits, np.concatenate(parts).astype(np.float32)) for nits, parts in sorted(shining.items()))
    groups = [(finish, rgb, np.concatenate(parts).astype(np.float32)) for (finish, rgb), parts in sorted(found.items())]
    return [g for g in groups if len(g[2])]


def scene_of(doc, objects, camera, sun, lighting="sun_lights", exposure=0.0, clean=True):
    """The RenderScene of these objects seen by `camera` ({eye, target, up, fov, height} — the view's) under `sun`
    (a unit vector towards it), lit so (LIGHTINGS), `exposure` EV over the automatic, its grain filtered out or not:
    a ground under the lowest of them, as wide as GROUND_SIZE times their size."""
    lights = []
    groups = gather(doc, objects, lights)
    ground = None
    if groups:
        pts = np.concatenate([t.reshape(-1, 3) for _f, _c, t in groups])
        lo, hi = pts.min(axis=0), pts.max(axis=0)
        size = float(max(hi[0] - lo[0], hi[1] - lo[1], 1.0))
        ground = (float(lo[2]) - 0.002, max(size * GROUND_SIZE, GROUND_LEAST))
        groups.append(("matte", GROUND_RGB, _square((lo + hi) / 2.0, ground[0], ground[1])))
    sun = np.asarray(sun, dtype=float)
    sun = sun / max(float(np.linalg.norm(sun)), 1e-9)
    # (0.470) the materials' own realistic looks: their values and pictures, their faces' pictures' coordinates
    from ..core import pbr
    import os
    beside = os.path.dirname(doc.path) if getattr(doc, "path", None) else None
    looks, uvs = {}, {}
    for k, (finish, _rgb, triangles) in enumerate(groups):
        look = own_look(finish[5:]) if finish.startswith("look:") else None
        if look is None:
            continue
        looks[k] = look_dict(look, beside)
        if looks[k]["maps"]:
            t = np.asarray(triangles, dtype=float).reshape(-1, 3, 3)
            normals = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
            uvs[k] = pbr.uv(t.reshape(-1, 3), np.repeat(normals, 3, axis=0), look).reshape(-1, 3, 2) \
                .astype(np.float32)
    return RenderScene(groups, tuple(map(float, camera["eye"])), tuple(map(float, camera["target"])),
                       tuple(map(float, camera.get("up", (0.0, 0.0, 1.0)))), float(camera.get("fov", 45.0)),
                       float(camera.get("height", 0.0)), tuple(map(float, sun)), ground, lights,
                       lighting if lighting in LIGHTINGS else "sun_lights", float(exposure), bool(clean), looks, uvs)


def _square(centre, z, half):
    a = np.array([(centre[0] - half, centre[1] - half, z), (centre[0] + half, centre[1] - half, z),
                  (centre[0] + half, centre[1] + half, z), (centre[0] - half, centre[1] + half, z)], dtype=float)
    return np.array([[a[0], a[1], a[2]], [a[0], a[2], a[3]]], dtype=np.float32)
