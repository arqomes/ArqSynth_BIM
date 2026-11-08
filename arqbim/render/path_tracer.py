"""(0.343) The realistic render: Mitsuba 3's path tracing on the processor (the light bounced off every face, soft
shadows, glass, the physical sky with its sun, the model's lights), in a process of its own — the program goes on
answering, and a render can be stopped at once (the process ended). It renders in passes, each more samples per pixel
with a seed of its own, their sum written after each one as the picture so far (PNG, exposed and tone-mapped), with
how far it got (JSON): the window shows the picture getting finer.

    python -m arqbim.render.path_tracer <scene.npz> <picture.png> <width> <height> <samples>

The scene: model/render_scene.RenderScene. Mitsuba's own scene: each group of faces a PLY file (flat faces) with its
finish's material (principled: matte, satin, glossy, metal; thin glass; frosted: rough see-through); the lights' faces
that shine, area emitters as bright as their flux over their area makes them (in the units of Mitsuba's sky: NITS),
or white diffusers when off; the sky with its sun by day, a dim blue one at nightfall. Its integrator the volumetric
path tracer: its shadow rays go through thin glass (the sun shines in through the windows without stray white
pixels), and more bounces seen from inside (under a roof). The picture so far, its grain filtered out (clean: guided
by each face's own colour, normal and depth, rendered once at the start) unless the scene says not to."""

import json
import math
import os
import sys
import tempfile
import time

import numpy as np

QUALITIES = {"draft": 32, "normal": 128, "high": 512}      # samples per pixel
PASSES = 8                       # the picture written so many times while it renders
MAX_DEPTH = 8                    # light bounces outside…
MAX_DEPTH_INSIDE = 12            # …and seen from inside (an interior lit through its windows needs more)
FIREFLY = 6.0                    # a pixel this many times lighter than those round it (and bright): a stray one
VARIANT = "scalar_rgb"
NITS = 76000.0                   # cd/m² in one unit of Mitsuba's radiance (its sky at 45°: 1.12 units of light on
                                 # the ground, some 85 000 lux — measured 2026-11-01)
LIGHT_RGB = (1.139, 0.979, 0.797)    # the lights' warm white (some 3000 K), linear, its luminance 1
LIGHT_OFF_RGB = (0.95, 0.95, 0.93)   # a light off: its white diffuser
NIGHT_SKY = 3.0                  # cd/m²: the sky at nightfall…
NIGHT_RGB = (0.45, 0.62, 1.32)   # …deep blue (linear, luminance 0.65)
NIGHT_KEY = 8.0                  # cd/m²: at night, what is lit no less than this a mid grey (a dark outside stays
                                 # dark, its windows bright — the automatic exposure would make it day)
GUIDE_SPP = 8                    # samples per pixel of the filter's guides (each face's colour, normal, depth)
CLEAN_ROUNDS = 5                 # the filter's rounds (it reaches 2⁵ pixels round each)
SIGMA_L = 4.0                    # how unlike in light two neighbours may be, in their noise
KERNEL = {-1: 0.25, 0: 0.5, 1: 0.25}
CLEAN_LIVE = 2_100_000           # pixels: the picture so far cleaned too up to Full HD (larger: only the last)
# finish -> the principled material's (roughness, specular, metallic)
SURFACES = {"matte": (0.85, 0.25, 0.0), "satin": (0.45, 0.45, 0.0), "glossy": (0.15, 0.6, 0.0),
            "metal": (0.30, 0.5, 1.0)}


def linear(rgb):
    """sRGB 0–1 → linear (what Mitsuba's rgb values are)."""
    c = np.asarray(rgb, dtype=float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _luminance(rgb):
    return 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]


def _key(lum):
    """The picture's log-average luminance, of what is lit in it (the near black — a night sky — left out)."""
    top = float(np.percentile(lum, 98)) if lum.size else 0.0
    if top <= 0.0:
        return 1.0
    lit = lum > top * 1e-4
    return float(np.exp(np.mean(np.log(lum[lit] + top * 1e-5))))


def calm(hdr, least=0.0):
    """A rendered picture (H, W, 3 linear) with its stray bright pixels calmed: each lone one (no more than one bright
    neighbour — a lamp's face is bright with its neighbours: kept) many times lighter than the middle of its
    neighbours, and not dark, brought to that middle."""
    rgb = np.nan_to_num(np.asarray(hdr, dtype=np.float32)[:, :, :3], nan=0.0, posinf=0.0, neginf=0.0)
    lum = _luminance(rgb)
    pad = np.pad(lum, 1, mode="edge")
    h, w = lum.shape
    near = np.stack([pad[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx])
    around = np.median(near, axis=0)
    alone = (near > lum / FIREFLY).sum(axis=0) <= 1
    stray = (lum > FIREFLY * (around + 1e-9)) & alone & (lum > 0.25 * max(_key(lum), float(least)))
    if stray.any():
        rgb = rgb * np.where(stray, (around + 1e-9) / (lum + 1e-9), 1.0)[:, :, None]
    return rgb


def clean(rgb, variance, albedo, normal, depth, rounds=CLEAN_ROUNDS):
    """(0.343) The grain of a rendered picture filtered out, its edges kept: the light on each face (the picture over
    the faces' own colours, `albedo`) averaged with its neighbours' — further each round (the à-trous wavelet,
    Dammertz et al. 2010) — as much as they are on the same face (alike `normal`s, `depth` along its slope) and alike
    in light, by the noise of each (`variance`: of the luminance of the mean of the passes, as SVGF does); then over
    their colours again. What shows the sky (depth 0) and what has no colour of its own (glass: what is seen
    through it) left as rendered."""
    f4 = np.float32
    rgb = np.asarray(rgb, dtype=f4)
    depth = np.asarray(depth, dtype=f4)
    normal = np.asarray(normal, dtype=f4)
    albedo = np.asarray(albedo, dtype=f4)
    hit = (depth > 0.0) & (albedo.max(axis=-1) >= 0.005)
    alb = np.where(hit[..., None], np.maximum(albedo, f4(0.02)), f4(1.0))
    c = rgb / alb
    v = np.asarray(variance, dtype=f4) / np.maximum(_luminance(alb), f4(0.02)) ** 2
    dzy, dzx = np.gradient(depth)
    near = 0.002 * depth + f4(1e-4)
    h, w = depth.shape
    for i in range(int(rounds)):
        s = 1 << i
        pc, pv = np.pad(c, ((s, s), (s, s), (0, 0)), mode="edge"), np.pad(v, s, mode="edge")
        pn, pz = np.pad(normal, ((s, s), (s, s), (0, 0)), mode="edge"), np.pad(depth, s, mode="edge")
        ph = np.pad(hit, s, mode="edge").astype(f4)
        lp = _luminance(c)
        pl = np.pad(lp, s, mode="edge")
        spread = 1.0 / (np.sqrt(_box3(v)) * f4(SIGMA_L) + f4(1e-12))
        num, den, vnum = np.zeros_like(c), np.zeros_like(depth), np.zeros_like(depth)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                at = (slice(s + dy * s, s + dy * s + h), slice(s + dx * s, s + dx * s + w))
                facing = np.clip(np.einsum("ijk,ijk->ij", normal, pn[at]), 0.0, 1.0)
                for _k in range(7):                                       # (its 128th power)
                    facing *= facing
                weight = (f4(KERNEL[dy] * KERNEL[dx]) * ph[at] * facing
                          * np.exp(-np.abs(depth - pz[at]) / (np.abs(dzx * (dx * s) + dzy * (dy * s)) + near)
                                   - np.abs(lp - pl[at]) * spread))
                num += weight[..., None] * pc[at]
                den += weight
                vnum += weight * weight * pv[at]
        ok = hit & (den > 1e-12)
        safe = np.maximum(den, f4(1e-12))
        c = np.where(ok[..., None], num / safe[..., None], c)
        v = np.where(ok, vnum / safe ** 2, v)
    return np.where(hit[..., None], c * alb, rgb)


def _box3(a):
    p = np.pad(a, 1, mode="edge")
    h, w = a.shape
    return sum(p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9.0


def tone(hdr, exposure=0.0, least=0.0):
    """A rendered picture (H, W, 3 linear) as 8-bit sRGB: its stray bright pixels calmed (calm), exposed so that the
    log-average of what is lit — no less than `least` — is a mid grey (`exposure` EV over that), ACES's filmic
    curve."""
    rgb = calm(hdr, least)
    x = rgb * (0.18 * 2.0 ** float(exposure) / max(_key(_luminance(rgb)), float(least), 1e-12))
    aces = np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0)
    srgb = np.where(aces <= 0.0031308, 12.92 * aces, 1.055 * np.power(aces, 1.0 / 2.4) - 0.055)
    return (np.clip(srgb, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def write_ply(path, triangles, uv=None):
    """Flat triangles (T, 3, 3) as a binary PLY (each its own three corners) — (0.470) with their pictures'
    coordinates (T, 3, 2), when given."""
    tri = np.asarray(triangles, dtype="<f4").reshape(-1, 3, 3)
    n = len(tri)
    faces = np.zeros(n, dtype=[("count", "u1"), ("index", "<i4", (3,))])
    faces["count"] = 3
    faces["index"] = np.arange(n * 3, dtype="<i4").reshape(-1, 3)
    texcoords = "" if uv is None else "property float u\nproperty float v\n"
    head = ("ply\nformat binary_little_endian 1.0\nelement vertex {}\nproperty float x\nproperty float y\n"
            "property float z\n{}element face {}\nproperty list uchar int vertex_indices\nend_header\n").format(
        n * 3, texcoords, n)
    with open(path, "wb") as fh:
        fh.write(head.encode("ascii"))
        if uv is None:
            fh.write(tri.reshape(-1, 3).tobytes())
        else:
            fh.write(np.column_stack((tri.reshape(-1, 3), np.asarray(uv, dtype="<f4").reshape(-1, 2)))
                     .astype("<f4").tobytes())
        fh.write(faces.tobytes())


def _picture(mi, path, inverted=False):
    """(0.470) A picture file as an (H, W, 3) array 0–1 as stored (sRGB for a colour), its top row first — None when
    it cannot be read."""
    try:
        bitmap = mi.Bitmap(path)
    except Exception:                      # (Mitsuba says why in many kinds: a picture it cannot read)
        return None
    data = np.array(bitmap, dtype=np.float32)
    if data.ndim == 2:
        data = data[:, :, None]
    if bitmap.component_format() in (mi.Struct.Type.UInt8,):
        data = data / 255.0
    elif bitmap.component_format() in (mi.Struct.Type.UInt16,):
        data = data / 65535.0
    data = data[:, :, :3] if data.shape[2] >= 3 else np.repeat(data[:, :, :1], 3, axis=2)
    return 1.0 - data if inverted else data


def _texture(mi, data):
    """A picture's values (H, W, C), its top row first, as Mitsuba's bitmap — taken as they are, repeated; turned
    upside down: a face's pictures' coordinates go up (render_scene: core/pbr.uv), Mitsuba's rows down."""
    return {"type": "bitmap", "data": mi.TensorXf(np.ascontiguousarray(np.flipud(data), dtype=np.float32)),
            "raw": True, "filter_type": "bilinear", "wrap_mode": "repeat"}


def look_material(mi, look, rgb):
    """(0.470) Mitsuba's material of a realistic look (core/pbr's, as render_scene keeps it: its pictures' files found)
    in a colour (sRGB 0–1), as D5 Render's: principled — its base colour (its picture times its own colour, its
    occlusion in it), roughness and metallic (their pictures, 50 % as they are), reflection, clear coat, sheen —; a
    glass (thin, or frosted when rough) or water (refracting); its relief (normal map, else its height map's); its
    opacity (a mask). Returns (bsdf, emitter or None: a light one shines)."""
    maps = look.get("maps") or {}

    def got(slot):
        found = maps.get(slot)
        return _picture(mi, found[0], found[1]) if found else None
    base = got("base")
    tint = linear(look.get("tint_rgb") or ((1.0, 1.0, 1.0) if base is not None else rgb))
    if base is not None:
        colour = linear(base) * tint
        ao = got("ao")
        if ao is not None and ao.shape == base.shape:
            strength = float(look.get("ao", 1.0))
            colour = colour * (1.0 - strength * (1.0 - ao.mean(axis=2, keepdims=True)))
        base_colour = _texture(mi, np.clip(colour, 0.0, 1.0))
    else:
        base_colour = {"type": "rgb", "value": [float(v) for v in tint]}
    kind = look.get("kind", "standard")
    roughness = float(look.get("roughness", 0.6))
    if kind == "glass":
        if roughness < 0.3:
            shade = [float(v) for v in 0.5 + 0.5 * tint]                       # (a pale tint of its colour)
            bsdf = {"type": "thindielectric", "specular_transmittance": {"type": "rgb", "value": shade}}
        else:
            bsdf = {"type": "principled", "base_color": base_colour, "roughness": roughness, "spec_trans": 0.9}
    elif kind == "water":
        shade = [float(v) for v in 0.35 + 0.65 * tint]
        bsdf = {"type": "dielectric", "int_ior": float(look.get("ior", 1.333)), "ext_ior": 1.0,
                "specular_transmittance": {"type": "rgb", "value": shade}}
    else:
        bsdf = {"type": "principled", "base_color": base_colour, "roughness": roughness,
                "metallic": float(look.get("metallic", 0.0)), "specular": float(look.get("specular", 0.5)),
                "clearcoat": float(look.get("clearcoat", 0.0)), "sheen": float(look.get("sheen", 0.0))}
        for slot in ("roughness", "metallic"):
            picture = got(slot)
            if picture is not None:
                value = picture.mean(axis=2, keepdims=True) * (float(look.get(slot, 0.5)) / 0.5)
                bsdf[slot] = _texture(mi, np.clip(value, 0.0, 1.0))
    normal = got("normal")
    if normal is None and maps.get("height"):                  # (its height map's relief, as a normal map)
        height = got("height")
        if height is not None:
            h = height.mean(axis=2)
            step = float(look.get("width", 1.0)) / max(h.shape[1], 1)
            gy, gx = np.gradient(h * float(look.get("height", 0.01)) * 4.0 / max(step, 1e-9))
            n = np.stack((-gx, gy, np.ones_like(h)), axis=-1)
            normal = n / np.linalg.norm(n, axis=-1, keepdims=True) * 0.5 + 0.5
    elif normal is not None:
        n = normal * 2.0 - 1.0
        n[:, :, :2] *= float(look.get("normal", 1.0))
        n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
        normal = n * 0.5 + 0.5
    if normal is not None:
        bsdf = {"type": "normalmap", "normalmap": _texture(mi, normal), "bsdf": bsdf}
    opacity = got("opacity")
    if opacity is not None:
        bsdf = {"type": "mask", "opacity": _texture(mi, opacity.mean(axis=2, keepdims=True)), "bsdf": bsdf}
    emitter = None
    nits = float(look.get("emission", 0.0))
    if kind == "emissive" or nits > 0.0:
        glow = linear(look.get("emission_rgb") or (1.0, 1.0, 1.0)) * max(nits, 1.0) / NITS
        picture = got("emission")
        radiance = _texture(mi, linear(picture) * glow) if picture is not None else \
            {"type": "rgb", "value": [float(v) for v in glow]}
        emitter = {"type": "area", "radiance": radiance}
    return bsdf, emitter


def material(finish, rgb):
    """Mitsuba's material of a finish in a colour (sRGB 0–1)."""
    colour = {"type": "rgb", "value": [float(v) for v in linear(rgb)]}
    if finish == "glass":
        tint = [float(v) for v in 0.5 + 0.5 * linear(rgb)]                  # (a pale tint of its colour)
        return {"type": "thindielectric", "specular_transmittance": {"type": "rgb", "value": tint}}
    if finish == "frosted":
        return {"type": "principled", "base_color": colour, "roughness": 0.35, "spec_trans": 0.9}
    if finish == "water":                                                   # (0.365) its surface: clear, refracting
        tint = [float(v) for v in 0.35 + 0.65 * linear(rgb)]
        return {"type": "dielectric", "int_ior": 1.333, "ext_ior": 1.0,
                "specular_transmittance": {"type": "rgb", "value": tint}}
    roughness, specular, metallic = SURFACES.get(finish, SURFACES["matte"])
    return {"type": "principled", "base_color": colour, "roughness": roughness, "specular": specular,
            "metallic": metallic}


def night(scene):
    """Lit by its lights at nightfall: so chosen, or its sun under the horizon."""
    return scene.lighting == "night" or float(scene.sun[2]) <= 0.0


def mitsuba_scene(mi, scene, width, height, folder):
    """Mitsuba's scene dict of a RenderScene, its faces written as PLY files in `folder` (no integrator: see
    integrator())."""
    eye, target, up = (np.asarray(v, dtype=float) for v in (scene.eye, scene.target, scene.up))
    to_world = mi.ScalarTransform4f().look_at(origin=eye.tolist(), target=target.tolist(), up=up.tolist())
    film = {"type": "hdrfilm", "width": int(width), "height": int(height), "rfilter": {"type": "box"}}
    if scene.fov > 0.0:
        sensor = {"type": "perspective", "fov_axis": "y", "fov": float(scene.fov), "to_world": to_world,
                  "film": film}
    else:
        half = max(float(scene.height), 0.01) / 2.0
        sensor = {"type": "orthographic", "film": film,
                  "to_world": to_world @ mi.ScalarTransform4f().scale([half * width / height, half, 1.0])}
    sensor["sampler"] = {"type": "independent"}
    out = {"type": "scene", "sensor": sensor}
    dark = night(scene)
    if dark:
        out["sky"] = {"type": "constant", "sampling_weight": 0.05,
                      "radiance": {"type": "rgb", "value": [v * NIGHT_SKY / NITS for v in NIGHT_RGB]}}
    else:
        out["sky"] = {"type": "sunsky", "sun_direction": [float(v) for v in scene.sun]}
    looks, uvs = getattr(scene, "looks", None) or {}, getattr(scene, "uvs", None) or {}
    for k, (finish, rgb, triangles) in enumerate(scene.groups):
        if not len(triangles):
            continue
        path = os.path.join(folder, "g{}.ply".format(k))
        look = looks.get(k)                                # (0.470) a material's own realistic look, its pictures
        write_ply(path, triangles, uvs.get(k) if look is not None else None)
        shape = {"type": "ply", "filename": path, "face_normals": True, "bsdf": material(finish, rgb)}
        if look is not None:
            shape["bsdf"], emitter = look_material(mi, look, rgb)
            if emitter is not None:
                shape["emitter"] = emitter
        out["g{}".format(k)] = shape
    on = dark or scene.lighting == "sun_lights"
    power = sum(nits * _area(t) for nits, t in scene.lights) or 1.0
    for k, (nits, triangles) in enumerate(scene.lights):
        if not len(triangles):
            continue
        path = os.path.join(folder, "l{}.ply".format(k))
        write_ply(path, triangles)
        shape = {"type": "ply", "filename": path, "face_normals": True, "bsdf": material("matte", LIGHT_OFF_RGB)}
        if on:
            shape["emitter"] = {"type": "area", "sampling_weight": max(nits * _area(triangles) / power, 1e-3),
                                "radiance": {"type": "rgb", "value": [v * nits / NITS for v in LIGHT_RGB]}}
        out["l{}".format(k)] = shape
    return out


def _area(triangles):
    t = np.asarray(triangles, dtype=float).reshape(-1, 3, 3)
    return float(np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1).sum() / 2.0)


def inside(mi, loaded, scene):
    """Is the camera under a roof (something over its eye)?"""
    ray = mi.Ray3f(mi.Point3f(*[float(v) for v in scene.eye]), mi.Vector3f(0.0, 0.0, 1.0))
    return bool(loaded.ray_test(ray))


def integrator(mi, loaded, scene):
    """The volumetric path tracer (its shadow rays through thin glass), more bounces seen from inside."""
    depth = MAX_DEPTH_INSIDE if inside(mi, loaded, scene) else MAX_DEPTH
    return mi.load_dict({"type": "volpath", "max_depth": depth})


def render(scene_path, picture, width, height, samples, passes=PASSES):
    """Render a scene file into `picture` (PNG), in passes; after each, the picture so far and `picture`.json —
    {"done", "of", "seconds", "finished", "samples"}."""
    import mitsuba as mi
    from PySide6 import QtGui
    from ..model.render_scene import RenderScene
    mi.set_variant(VARIANT)
    scene = RenderScene.load(scene_path)
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="arqsynth_ply_") as folder:
        loaded = mi.load_dict(mitsuba_scene(mi, scene, width, height, folder))
    tracer = integrator(mi, loaded, scene)
    least = NIGHT_KEY / NITS if night(scene) else 0.0
    guide = None
    if scene.clean:                          # (each face's colour, normal and depth: what the filter keeps apart)
        guide = np.array(mi.render(loaded, integrator=mi.load_dict(
            {"type": "aov", "aovs": "aa:albedo,nn:sh_normal,dd:depth"}), spp=GUIDE_SPP), dtype=np.float64)
    passes = max(1, min(int(passes), int(samples)))
    each = max(1, int(math.ceil(samples / passes)))
    total = squares = None
    for k in range(passes):
        img = np.array(mi.render(loaded, integrator=tracer, spp=each, seed=k + 1), dtype=np.float64)[:, :, :3]
        total = img if total is None else total + img
        squares = _luminance(img) ** 2 if squares is None else squares + _luminance(img) ** 2
        shown = total / (k + 1)
        if guide is not None and k and (k + 1 == passes or width * height <= CLEAN_LIVE):
            variance = np.maximum(squares / (k + 1) - _luminance(shown) ** 2, 0.0) / k
            shown = clean(calm(shown, least), variance, guide[..., 0:3], guide[..., 3:6], guide[..., 6])
        pixels = tone(shown, scene.exposure, least)
        h, w = pixels.shape[:2]
        rgba = np.dstack([pixels, np.full((h, w), 255, np.uint8)])
        image = QtGui.QImage(np.ascontiguousarray(rgba).tobytes(), w, h, w * 4, QtGui.QImage.Format.Format_RGBA8888)
        part = picture + ".part.png"
        image.copy().save(part)
        os.replace(part, picture)
        state = {"done": k + 1, "of": passes, "seconds": round(time.time() - started, 1),
                 "finished": k + 1 == passes, "samples": each * (k + 1)}
        with open(picture + ".part.json", "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        os.replace(picture + ".part.json", picture + ".json")


def render_panorama(scene_path, picture, width, height, samples, passes=PASSES):
    """(0.368) A 360° panorama of a scene file into `picture` (PNG, equirectangular width × height): from its eye,
    looking (level) towards its target in its middle — six square faces of 90° (render/panorama.py) rendered with
    Mitsuba's scene loaded once, in passes as render(), each pass all six; after each, the panorama so far (each face
    cleaned of its grain, then sampled into the picture) and its progress (`picture`.json, a face of a pass a step)."""
    import mitsuba as mi
    from PySide6 import QtGui
    from ..model.render_scene import RenderScene
    from . import panorama
    mi.set_variant(VARIANT)
    scene = RenderScene.load(scene_path)
    started = time.time()
    n = panorama.face_size(width)
    size = n + 2 * panorama.margin(n)                   # (each face with its margin: render/panorama.py)
    forward = np.asarray(scene.target, dtype=float) - np.asarray(scene.eye, dtype=float)
    bases = panorama.faces(forward)
    eye = [float(v) for v in scene.eye]
    with tempfile.TemporaryDirectory(prefix="arqsynth_ply_") as folder:
        loaded = mi.load_dict(mitsuba_scene(mi, scene, size, size, folder))
    tracer = integrator(mi, loaded, scene)
    least = NIGHT_KEY / NITS if night(scene) else 0.0
    sensors = {}
    for name, (direction, _right, up) in bases.items():
        to_world = mi.ScalarTransform4f().look_at(origin=eye, target=(np.asarray(eye) + direction).tolist(),
                                                  up=up.tolist())
        sensors[name] = mi.load_dict({"type": "perspective", "fov": panorama.face_fov(n), "fov_axis": "x",
                                      "to_world": to_world, "sampler": {"type": "independent"},
                                      "film": {"type": "hdrfilm", "width": size, "height": size,
                                               "rfilter": {"type": "box"}}})
    guides = {}
    if scene.clean:
        aov = mi.load_dict({"type": "aov", "aovs": "aa:albedo,nn:sh_normal,dd:depth"})
        guides = {name: np.array(mi.render(loaded, sensor=s, integrator=aov, spp=GUIDE_SPP), dtype=np.float64)
                  for name, s in sensors.items()}
    passes = max(1, min(int(passes), int(samples)))
    each = max(1, int(math.ceil(samples / passes)))
    totals, squares = {}, {}
    steps = passes * len(sensors)
    for k in range(passes):
        for f, (name, sensor) in enumerate(sensors.items()):
            img = np.array(mi.render(loaded, sensor=sensor, integrator=tracer, spp=each, seed=k * 6 + f + 1),
                           dtype=np.float64)[:, :, :3]
            totals[name] = img if name not in totals else totals[name] + img
            squares[name] = _luminance(img) ** 2 if name not in squares else squares[name] + _luminance(img) ** 2
            state = {"done": k * len(sensors) + f + 1, "of": steps, "seconds": round(time.time() - started, 1),
                     "finished": False, "samples": each * (k + 1) if f + 1 == len(sensors) else each * k}
            with open(picture + ".part.json", "w", encoding="utf-8") as fh:
                json.dump(state, fh)
            os.replace(picture + ".part.json", picture + ".json")
        shown = {}
        for name in sensors:
            mean = totals[name] / (k + 1)
            if name in guides and k:
                variance = np.maximum(squares[name] / (k + 1) - _luminance(mean) ** 2, 0.0) / k
                g = guides[name]
                mean = clean(calm(mean, least), variance, g[..., 0:3], g[..., 3:6], g[..., 6])
            shown[name] = mean
        hdr = panorama.equirect(shown, forward, int(width), int(height), inner=n)
        pixels = tone(hdr, scene.exposure, least)
        h, w = pixels.shape[:2]
        rgba = np.dstack([pixels, np.full((h, w), 255, np.uint8)])
        image = QtGui.QImage(np.ascontiguousarray(rgba).tobytes(), w, h, w * 4, QtGui.QImage.Format.Format_RGBA8888)
        part = picture + ".part.png"
        image.copy().save(part)
        os.replace(part, picture)
        state = {"done": (k + 1) * len(sensors), "of": steps, "seconds": round(time.time() - started, 1),
                 "finished": k + 1 == passes, "samples": each * (k + 1)}
        with open(picture + ".part.json", "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        os.replace(picture + ".part.json", picture + ".json")


def command(scene_path, picture, width, height, samples, panorama=False):
    """The command line of a render's process (this module run by the program's Python); (0.368) panorama: a 360°
    panorama from the scene's eye (render_panorama)."""
    return [sys.executable, "-m", "arqbim.render.path_tracer", scene_path, picture, str(int(width)),
            str(int(height)), str(int(samples))] + (["--panorama"] if panorama else [])


if __name__ == "__main__":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    run = render_panorama if "--panorama" in sys.argv[6:] else render
    run(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
