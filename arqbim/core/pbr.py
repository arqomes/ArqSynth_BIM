"""(0.468) A material's realistic look, as D5 Render's material editor has it (the owner: «Na criação do material, deve
ter opção de como vai aparecer na vista, em corte, e na vista realista, colocar suporte a textura, e todos os controlos
de um material realista, e nesse caso devemos inspirar no D5 Render»):

- its kind — standard, glass, water, light (emissive), cloth — and how it takes the light: how rough (0 a mirror, 1 a
  chalk), how metallic, how much a non-metal reflects (specular), a clear coat over it (a lacquer, a car's paint), a
  cloth's sheen, how much a clear one bends the light (its refraction index), how bright a light one is (cd/m²) and in
  what colour;
- its pictures (textures), each a file: the base colour's, the normal map's (relief seen in the light), the
  roughness', the metallic's, the height's (relief that moves the surface), the ambient occlusion's, the opacity's and
  the emission's — the normal's, the height's and the occlusion's with how strong; a picture turned over (white for
  black: a glossiness map read as roughness);
- how the pictures lie on the faces, in the model's metres: one picture this wide and this high, turned and shifted.

The base colour: the material's shading colour unless one of its own is given (with a picture: the picture times it).

Pure data, no Qt: kept as one JSON text in the material's ArqSynth_Parametros («Realista»). The pictures are copied to
the textures' folder (Documents/ArqSynth/Texturas) when chosen, so that they stay when the original is moved; a
picture not found where it was is looked for beside the project and in that folder."""

import json
import math
import os
import shutil
from dataclasses import asdict, dataclass, replace

KINDS = ("standard", "glass", "water", "emissive", "cloth")
SLOTS = ("base", "normal", "roughness", "metallic", "height", "ao", "opacity", "emission")
PICTURES = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp", ".exr", ".hdr")
FOLDER_NAME = os.path.join("ArqSynth", "Texturas")
# (each realistic preset, as D5's templates: its kind, roughness, metallic, specular, clear coat, sheen, refraction)
PRESETS = {
    "matte": ("standard", 0.9, 0.0, 0.3, 0.0, 0.0, 1.5),
    "satin": ("standard", 0.5, 0.0, 0.5, 0.0, 0.0, 1.5),
    "glossy": ("standard", 0.15, 0.0, 0.6, 0.0, 0.0, 1.5),
    "lacquer": ("standard", 0.4, 0.0, 0.5, 1.0, 0.0, 1.5),
    "metal": ("standard", 0.25, 1.0, 0.5, 0.0, 0.0, 1.5),
    "brushed": ("standard", 0.55, 1.0, 0.5, 0.0, 0.0, 1.5),
    "glass": ("glass", 0.0, 0.0, 0.5, 0.0, 0.0, 1.52),
    "frosted": ("glass", 0.45, 0.0, 0.5, 0.0, 0.0, 1.52),
    "water": ("water", 0.02, 0.0, 0.5, 0.0, 0.0, 1.33),
    "cloth": ("cloth", 0.85, 0.0, 0.3, 0.0, 0.8, 1.5),
    "emissive": ("emissive", 0.6, 0.0, 0.3, 0.0, 0.0, 1.5),
}
LIMITS = {"roughness": (0.0, 1.0), "metallic": (0.0, 1.0), "specular": (0.0, 1.0), "clearcoat": (0.0, 1.0),
          "sheen": (0.0, 1.0), "ior": (1.0, 3.0), "emission": (0.0, 1.0e6), "normal": (0.0, 5.0),
          "height": (0.0, 0.5), "ao": (0.0, 1.0), "width": (0.001, 1000.0), "height_m": (0.001, 1000.0),
          "rotation": (-360.0, 360.0), "offset_x": (-1000.0, 1000.0), "offset_y": (-1000.0, 1000.0)}


@dataclass(frozen=True)
class Look:
    kind: str = "standard"        # KINDS
    roughness: float = 0.6
    metallic: float = 0.0
    specular: float = 0.5
    clearcoat: float = 0.0
    sheen: float = 0.0
    ior: float = 1.5              # a clear one's refraction index (glass 1,52, water 1,33)
    emission: float = 0.0         # cd/m²: how bright a light one shines
    emission_colour: str = "#ffffff"
    tint: str = ""                # its base colour ("#rrggbb"); "": the material's shading colour (with a picture: white)
    maps: tuple = ()              # ((slot, path, turned over), …) — SLOTS
    normal: float = 1.0           # the normal map's strength
    height: float = 0.01          # m: the height map's relief
    ao: float = 1.0               # the occlusion map's strength
    width: float = 1.0            # m: one picture's size in the model…
    height_m: float = 1.0
    rotation: float = 0.0         # …degrees, counter-clockwise…
    offset_x: float = 0.0         # …and shifted (m)
    offset_y: float = 0.0

    def map(self, slot):
        """(path, turned over) of a slot's picture, or None."""
        for s, path, inverted in self.maps:
            if s == slot and path:
                return path, bool(inverted)
        return None

    def with_map(self, slot, path, inverted=False):
        """This look with a slot's picture (None or "": without it)."""
        maps = tuple(m for m in self.maps if m[0] != slot)
        if path:
            maps = tuple(sorted(maps + ((slot, str(path), bool(inverted)),), key=lambda m: SLOTS.index(m[0])))
        return replace(self, maps=maps)

    @property
    def textured(self):
        return any(path for _s, path, _i in self.maps)

    @property
    def clear(self):
        """A see-through kind (glass, water)."""
        return self.kind in ("glass", "water")


DEFAULT = Look()
AS_PICTURE = 0.5          # a roughness or metallic value with a picture: the picture as it is (more: rougher…)


def scaled(picture, value):
    """A roughness or metallic picture's values (0–1, any shape) as the look's value makes them: 0,5 as they are, 1
    twice as much, 0 none."""
    import numpy as np
    return np.clip(np.asarray(picture, dtype=np.float32) * (float(value) / AS_PICTURE), 0.0, 1.0)


def _clamp(name, value, default):
    low, high = LIMITS.get(name, (-math.inf, math.inf))
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(value):
        return default
    return min(max(value, low), high)


def _hex(text, default):
    text = str(text or "")
    if len(text) == 7 and text.startswith("#"):
        try:
            int(text[1:], 16)
            return text.lower()
        except ValueError:
            pass
    return default


def encode(look):
    """The look as kept in the IFC: one JSON text (only what differs from the usual)."""
    data = {k: v for k, v in asdict(look).items() if v != getattr(DEFAULT, k)}
    if "maps" in data:
        data["maps"] = [list(m) for m in look.maps]
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def decode(text):
    """A look from its JSON text (what is not understood: the usual), or None for no text."""
    if not text:
        return None
    try:
        data = json.loads(str(text))
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    out = {}
    for name in ("roughness", "metallic", "specular", "clearcoat", "sheen", "ior", "emission", "normal", "height",
                 "ao", "width", "height_m", "rotation", "offset_x", "offset_y"):
        if name in data:
            out[name] = _clamp(name, data[name], getattr(DEFAULT, name))
    if data.get("kind") in KINDS:
        out["kind"] = data["kind"]
    if "emission_colour" in data:
        out["emission_colour"] = _hex(data["emission_colour"], DEFAULT.emission_colour)
    if "tint" in data:
        out["tint"] = _hex(data["tint"], "")
    maps = []
    for m in data.get("maps") or ():
        if isinstance(m, (list, tuple)) and len(m) >= 2 and m[0] in SLOTS and m[1] and \
                all(m[0] != k for k, _p, _i in maps):
            maps.append((m[0], str(m[1]), bool(m[2]) if len(m) > 2 else False))
    if maps:
        out["maps"] = tuple(sorted(maps, key=lambda m: SLOTS.index(m[0])))
    return Look(**out)


def preset(name, look=None):
    """A look with a preset's values (its pictures, its size and its colours kept)."""
    kind, roughness, metallic, specular, clearcoat, sheen, ior = PRESETS[name]
    base = look or DEFAULT
    emission = base.emission or (1000.0 if kind == "emissive" else 0.0)
    return replace(base, kind=kind, roughness=roughness, metallic=metallic, specular=specular, clearcoat=clearcoat,
                   sheen=sheen, ior=ior, emission=emission if kind == "emissive" else 0.0)


def preset_of(look):
    """The preset a look is (its values the same), or ""."""
    for name in PRESETS:
        p = preset(name, look)
        if all(abs(getattr(p, k) - getattr(look, k)) < 1e-6
               for k in ("roughness", "metallic", "specular", "clearcoat", "sheen", "ior")) and p.kind == look.kind:
            return name
    return ""


def from_finish(finish):
    """(The materials before 0.468) the look of a render finish (model/render_scene.FINISHES)."""
    return preset({"matte": "matte", "satin": "satin", "glossy": "glossy", "metal": "metal", "glass": "glass",
                   "frosted": "frosted", "water": "water"}.get(finish or "", "matte"))


def finish_of(look):
    """The render finish nearest a look (what the render of before reads)."""
    if look.kind == "water":
        return "water"
    if look.kind == "glass":
        return "frosted" if look.roughness > 0.3 else "glass"
    if look.metallic >= 0.5:
        return "metal"
    if look.roughness < 0.3 or look.clearcoat >= 0.5:
        return "glossy"
    return "satin" if look.roughness < 0.7 else "matte"


# ---------------------------------------------------------------------------------------------------- the pictures

def folder():
    """The textures' folder: Documents/ArqSynth/Texturas (made when first used)."""
    home = os.path.expanduser("~")
    docs = os.path.join(home, "Documents")
    if not os.path.isdir(docs):
        docs = os.path.join(home, "Documentos") if os.path.isdir(os.path.join(home, "Documentos")) else home
    return os.path.join(docs, FOLDER_NAME)


def is_picture(path):
    return os.path.splitext(str(path or ""))[1].lower() in PICTURES


def keep(path, where=None):
    """A picture chosen for a material, copied to the textures' folder (`where`, else folder()) — one there already, or
    in a folder of pictures the program keeps, as it is. Its path there."""
    where = where or folder()
    path = os.path.abspath(path)
    if os.path.normcase(os.path.dirname(path)).startswith(os.path.normcase(os.path.abspath(where))):
        return path
    os.makedirs(where, exist_ok=True)
    name = os.path.basename(path)
    target = os.path.join(where, name)
    stem, ext = os.path.splitext(name)
    n = 2
    while os.path.exists(target):
        try:
            if os.path.getsize(target) == os.path.getsize(path) and _same(target, path):
                return target                                  # (the same picture: kept once)
        except OSError:
            pass
        target = os.path.join(where, "{} ({}){}".format(stem, n, ext))
        n += 1
    shutil.copyfile(path, target)
    return target


def _same(a, b):
    with open(a, "rb") as fa, open(b, "rb") as fb:
        while True:
            x, y = fa.read(1 << 16), fb.read(1 << 16)
            if x != y:
                return False
            if not x:
                return True


def find(path, beside=None):
    """Where a material's picture is: its path, else a file of its name beside the project (`beside`: its folder; or in
    its «texturas» folder), else in the textures' folder. None when nowhere."""
    if not path:
        return None
    if os.path.isfile(path):
        return path
    name = os.path.basename(str(path).replace("\\", "/"))
    for place in ([beside, os.path.join(beside, "texturas"), os.path.join(beside, "Texturas")] if beside else []) + \
            [folder()]:
        candidate = os.path.join(place, name)
        if os.path.isfile(candidate):
            return candidate
    return None


def uv(points, normals, look):
    """The pictures' coordinates (N, 2) of points (N, 3) on faces (normals (N, 3)), in pictures: as SketchUp and Revit
    lay them on a box — each face by its main direction (a wall's along it and up, a floor's in plan) — then the
    look's size, turn and shift."""
    import numpy as np
    p = np.asarray(points, dtype=float).reshape(-1, 3)
    n = np.abs(np.asarray(normals, dtype=float).reshape(-1, 3))
    axis = np.argmax(n, axis=1)
    u = np.where(axis == 0, p[:, 1], p[:, 0])
    v = np.where(axis == 2, p[:, 1], p[:, 2])
    a = math.radians(look.rotation)
    c, s = math.cos(a), math.sin(a)
    u, v = u - look.offset_x, v - look.offset_y
    u, v = c * u + s * v, -s * u + c * v
    return np.column_stack((u / max(look.width, 1e-6), v / max(look.height_m, 1e-6)))
