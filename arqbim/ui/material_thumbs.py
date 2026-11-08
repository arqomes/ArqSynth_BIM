"""(0.468) A material's picture as the Materials panel shows it — a cube, as SketchUp's Materials panel, or a sphere, as
D5 Render's — lit by a sun and a sky: its base colour or picture (else its surface pattern over its shading colour),
its relief (normal map, or height map), how rough and how metallic, its clear coat, a cloth's sheen, a clear one over a
chequer, a light one shining. NumPy: each a few milliseconds; the pictures read once each (made smaller).

Seen from the south-west, above, as the 3D view's first look: the cube 1 m wide (its faces' pictures as they lie on
the model's faces: model.pbr.uv), the sphere 1 m across."""

import math
import os

import numpy as np
from PySide6 import QtCore, QtGui

from ..core import pbr

SHAPES = ("cube", "sphere")
SUN = np.array((-0.55, -0.35, 0.76))            # towards the sun (object space: X east, Y north, Z up)
SUN = SUN / np.linalg.norm(SUN)
EYE = np.array((-1.0, -1.25, 0.95))             # towards the viewer
EYE = EYE / np.linalg.norm(EYE)
SKY_TOP = np.array((0.42, 0.55, 0.80))          # linear
SKY_LOW = np.array((0.85, 0.87, 0.90))
GROUND = np.array((0.16, 0.15, 0.13))
CHEQUER = ("#ffffff", "#d9dde2")
_pictures = {}                                  # (path, mtime, size) -> (H, W, 3) linear 0–1
_heights = {}                                   # (path, mtime, size) -> its relief's normals (H, W, 3)
_made = {}                                      # (what makes it) -> QImage
MADE_KEPT = 800


def linear(rgb):
    c = np.asarray(rgb, dtype=np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1.0 / 2.4) - 0.055)


def _hex_rgb(text, default=(1.0, 1.0, 1.0)):
    q = QtGui.QColor(text) if text else None
    return (q.redF(), q.greenF(), q.blueF()) if q is not None and q.isValid() else default


def _array(image):
    """A QImage as an (H, W, 3) array 0–1 (sRGB)."""
    image = image.convertToFormat(QtGui.QImage.Format.Format_RGB888)
    w, h, line = image.width(), image.height(), image.bytesPerLine()
    raw = np.frombuffer(bytes(image.constBits()), dtype=np.uint8)[:line * h].reshape(h, line)
    return raw[:, :w * 3].reshape(h, w, 3).astype(np.float32) / 255.0


def picture(path, size=128):
    """A picture file read (made at most `size` px wide), linear 0–1 — None when it cannot be read."""
    if not path:
        return None
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return None
    key = (path, mtime, size)
    if key not in _pictures:
        image = QtGui.QImage(path)
        if image.isNull():
            _pictures[key] = None
        else:
            if max(image.width(), image.height()) > size:
                image = image.scaled(size, size, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                     QtCore.Qt.TransformationMode.SmoothTransformation)
            _pictures[key] = linear(_array(image))
    return _pictures[key]


def _relief(path, size, depth, width):
    """The normals (tangent space, (H, W, 3)) of a height map's relief — `depth` m high, the picture `width` m wide."""
    try:
        key = (path, os.path.getmtime(path), size, round(depth, 5), round(width, 5))
    except OSError:
        return None
    if key not in _heights:
        image = picture(path, size)
        if image is None:
            _heights[key] = None
        else:
            h = srgb(image).mean(axis=2)
            step = width / max(h.shape[1], 1)
            gy, gx = np.gradient(h * depth / max(step, 1e-9))
            n = np.stack((-gx, gy, np.ones_like(h)), axis=-1)
            _heights[key] = n / np.linalg.norm(n, axis=-1, keepdims=True)
    return _heights[key]


def _sample(image, u, v):
    """An image read at pictures' coordinates (repeated), nearest."""
    h, w = image.shape[:2]
    x = np.floor(np.mod(u, 1.0) * w).astype(np.int64) % w
    y = np.floor(np.mod(-v, 1.0) * h).astype(np.int64) % h
    return image[y, x]


def _sky(d):
    """The sky's colour towards unit directions (N, 3); under the horizon the ground."""
    z = d[:, 2:3]
    sky = SKY_LOW + (SKY_TOP - SKY_LOW) * np.sqrt(np.clip(z, 0.0, 1.0))
    return np.where(z >= 0.0, sky, GROUND + (SKY_LOW - GROUND) * np.clip(1.0 + z * 6.0, 0.0, 1.0))


def _ambient(n):
    """What a rough face facing n gets of the sky and the ground."""
    up = 0.5 + 0.5 * n[:, 2:3]
    return (GROUND * 1.6) * (1.0 - up) + (SKY_LOW * 0.55 + SKY_TOP * 0.35) * up


def _hits(shape, size):
    """For each pixel of a size×size picture: whether the shape is seen there, and where (points, normals,
    tangents, bitangents, pictures' coordinates in m) — object space, Z up."""
    f = -EYE
    right = np.cross(f, (0.0, 0.0, 1.0))
    right /= np.linalg.norm(right)
    up = np.cross(right, f)
    k = 0.93 if shape == "cube" else 0.58
    s = (np.arange(size) + 0.5) / size * 2.0 - 1.0
    sx, sy = np.meshgrid(s * k, -s * k)
    o = EYE * 4.0 + sx.reshape(-1, 1) * right + sy.reshape(-1, 1) * up
    d = np.broadcast_to(f, o.shape)
    if shape == "sphere":
        b = (o * d).sum(axis=1)
        c = (o * o).sum(axis=1) - 0.25
        disc = b * b - c
        seen = disc >= 0.0
        t = -b - np.sqrt(np.maximum(disc, 0.0))
        p = o + t[:, None] * d
        n = p / 0.5
        phi = np.arctan2(n[:, 0], -n[:, 1])
        theta = np.arcsin(np.clip(n[:, 2], -1.0, 1.0))
        tan = np.column_stack((np.cos(phi), np.sin(phi), np.zeros_like(phi)))
        bit = np.cross(n, tan)
        uv = np.column_stack((phi * 0.5, theta * 0.5))
        return seen, p, n, tan, bit, uv
    with np.errstate(divide="ignore", invalid="ignore"):
        inv = 1.0 / np.where(np.abs(d) < 1e-12, 1e-12, d)
        t1, t2 = (-0.5 - o) * inv, (0.5 - o) * inv
    near, far = np.minimum(t1, t2), np.maximum(t1, t2)
    tmin, tmax = near.max(axis=1), far.min(axis=1)
    seen = tmax >= tmin
    axis = near.argmax(axis=1)
    p = o + tmin[:, None] * d
    n = np.zeros_like(p)
    n[np.arange(len(p)), axis] = -np.sign(d[np.arange(len(p)), axis])
    # (each face's pictures as on the model: a wall's along it and up, the top in plan)
    tan = np.where((axis == 0)[:, None], (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)).astype(float)
    bit = np.where((axis == 2)[:, None], (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)).astype(float)
    u = np.where(axis == 0, p[:, 1], p[:, 0]) + 0.5
    v = np.where(axis == 2, p[:, 1], p[:, 2]) + 0.5
    return seen, p, n, tan, bit, np.column_stack((u, v))


def _transformed(uv, look):
    a = math.radians(look.rotation)
    c, s = math.cos(a), math.sin(a)
    u, v = uv[:, 0] - look.offset_x, uv[:, 1] - look.offset_y
    u, v = c * u + s * v, -s * u + c * v
    return u / max(look.width, 1e-6), v / max(look.height_m, 1e-6)


def render(colour, look, size, shape="cube", transparency=0.0, pattern=None, beside=None):
    """The picture (QImage, size×size, see-through round it) of a material: its shading colour (sRGB 0–1), its
    realistic look (pbr.Look), how clear it is in the views; pattern: its surface pattern over its colour, one metre of
    it ((H, W, 3) sRGB), drawn when it has no base picture."""
    look = look or pbr.DEFAULT
    seen, p, n, tan, bit, uv = _hits(shape, size)
    idx = np.flatnonzero(seen)
    p, n, tan, bit, uv = p[idx], n[idx], tan[idx], bit[idx], uv[idx]
    u, v = _transformed(uv, look)
    px = max(16, min(512, int(2 ** math.ceil(math.log2(max(size * look.width * 0.8, 16.0))))))

    def mapped(slot):
        found = look.map(slot)
        if found is None:
            return None, False
        return picture(pbr.find(found[0], beside), px), found[1]

    # the base colour: its picture times its own colour, else the shading colour (its surface pattern on it)
    base_pic, _inv = mapped("base")
    tint = linear(_hex_rgb(look.tint, (1.0, 1.0, 1.0) if base_pic is not None else tuple(colour)))
    if base_pic is not None:
        albedo = _sample(base_pic, u, v) * tint
    elif pattern is not None:
        pu, pv = (uv[:, 0], uv[:, 1])
        albedo = _sample(linear(pattern), pu, pv) * (tint / np.maximum(linear(colour), 1e-4)
                                                     if look.tint else 1.0)
    else:
        albedo = np.broadcast_to(tint, (len(idx), 3)).astype(np.float32)
    albedo = np.clip(albedo, 0.0, 1.0)
    # the relief: its normal map, else its height map's
    nm, nm_inv = mapped("normal")
    hm = look.map("height")
    if nm is not None:
        t = _sample(nm, u, v) if not nm_inv else 1.0 - _sample(nm, u, v)
        t = srgb(t) * 2.0 - 1.0
        t[:, :2] *= look.normal
    elif hm is not None:
        relief = _relief(pbr.find(hm[0], beside), px, look.height * 4.0, look.width)
        t = _sample(relief, u, v) if relief is not None else None
    else:
        t = None
    if t is not None:
        n = tan * t[:, 0:1] + bit * t[:, 1:2] + n * np.maximum(t[:, 2:3], 0.05)
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    rough = np.full(len(idx), look.roughness, np.float32)
    rm, r_inv = mapped("roughness")
    if rm is not None:                  # (with a picture, the value scales it: 0,5 the picture as it is — pbr.scaled)
        r = srgb(_sample(rm, u, v)).mean(axis=1)
        rough = pbr.scaled(1.0 - r if r_inv else r, look.roughness)
    metal = np.full(len(idx), look.metallic, np.float32)
    mm, m_inv = mapped("metallic")
    if mm is not None:
        m = srgb(_sample(mm, u, v)).mean(axis=1)
        metal = pbr.scaled(1.0 - m if m_inv else m, look.metallic)
    occlusion = np.ones(len(idx), np.float32)
    am, a_inv = mapped("ao")
    if am is not None:
        a = srgb(_sample(am, u, v)).mean(axis=1)
        occlusion = 1.0 - (1.0 - (1.0 - a if a_inv else a)) * look.ao

    view = np.broadcast_to(EYE, n.shape)
    nv = np.clip((n * view).sum(axis=1), 1e-3, 1.0)[:, None]
    nl = np.clip((n * SUN).sum(axis=1), 0.0, 1.0)[:, None]
    half = SUN + EYE
    half /= np.linalg.norm(half)
    nh = np.clip((n * half).sum(axis=1), 0.0, 1.0)[:, None]
    r = np.clip(rough, 0.03, 1.0)[:, None]
    alpha2 = (r * r) ** 2
    ggx = alpha2 / (math.pi * ((nh * nh) * (alpha2 - 1.0) + 1.0) ** 2)
    kk = (r + 1.0) ** 2 / 8.0
    geo = (nv / (nv * (1.0 - kk) + kk)) * (nl / (nl * (1.0 - kk) + kk))
    metal = metal[:, None]
    f0 = 0.08 * look.specular * (1.0 - metal) + albedo * metal
    fres = f0 + (1.0 - f0) * (1.0 - nv) ** 5
    sun = 2.6
    specular = ggx * geo * fres / np.maximum(4.0 * nv * np.maximum(nl, 1e-3), 1e-3) * nl * sun
    refl = 2.0 * nv * n - view
    env = _sky(refl) * (1.0 - r) + _ambient(n) * r
    env_f = f0 + (np.maximum(1.0 - r, f0) - f0) * (1.0 - nv) ** 5
    occ = occlusion[:, None]
    diffuse = albedo * (1.0 - metal) * (nl * sun * 0.42 + _ambient(n) * 0.95) * occ
    out = diffuse + specular + env * env_f * occ * 1.1
    if look.clearcoat > 0.0:
        cf = (0.04 + 0.96 * (1.0 - nv) ** 5) * look.clearcoat
        ch = 0.0025 / (math.pi * ((nh * nh) * (0.0025 - 1.0) + 1.0) ** 2)
        out = out * (1.0 - cf) + cf * (_sky(refl) * 1.1) + ch * nl * sun * 0.04 * look.clearcoat
    if look.sheen > 0.0:
        out = out + look.sheen * (1.0 - nv) ** 3 * (0.5 + 0.5 * albedo) * 0.6
    em = look.map("emission")
    if look.kind == "emissive" or look.emission > 0.0:
        glow = linear(_hex_rgb(look.emission_colour))
        strength = min(max(look.emission, 1.0) / 1000.0, 2.0)
        if em is not None:
            emp = picture(pbr.find(em[0], beside), px)
            glow = (_sample(emp, u, v) if emp is not None else glow) * glow
        out = out * 0.35 + glow * strength * 1.2
    # how clear: a glass, the opacity's picture, the views' transparency
    opacity = np.full(len(idx), 1.0 - float(transparency or 0.0), np.float32)
    om, o_inv = mapped("opacity")
    if om is not None:
        o = srgb(_sample(om, u, v)).mean(axis=1)
        opacity = opacity * (1.0 - o if o_inv else o)
    if look.clear:
        opacity = np.minimum(opacity, 0.18 + fres[:, 0] * 0.8 + specular.mean(axis=1) * 0.5)
        out = out + env * 0.25
    rgb = srgb(out / (1.0 + out * 0.18))          # (a soft roll-off of the brightest)
    # over a chequer (a clear one's)
    s = size // 8 or 1
    yy, xx = np.divmod(idx, size)
    light = ((xx // s + yy // s) % 2 == 0)[:, None]
    back = np.where(light, _hex_rgb(CHEQUER[0]), _hex_rgb(CHEQUER[1]))
    a = np.clip(opacity, 0.0, 1.0)[:, None]
    rgb = rgb * a + back * (1.0 - a)
    image = np.zeros((size * size, 4), np.uint8)
    image[idx, :3] = np.round(np.clip(rgb, 0.0, 1.0) * 255.0).astype(np.uint8)
    image[idx, 3] = 255
    _edge(image, seen, size)
    data = image.reshape(size, size, 4).copy()
    q = QtGui.QImage(data.data, size, size, size * 4, QtGui.QImage.Format.Format_RGBA8888)
    return q.copy()


def _edge(image, seen, size):
    """The shape's outline softened (its edge's pixels half see-through)."""
    m = seen.reshape(size, size)
    inner = m.copy()
    inner[1:, :] &= m[:-1, :]
    inner[:-1, :] &= m[1:, :]
    inner[:, 1:] &= m[:, :-1]
    inner[:, :-1] &= m[:, 1:]
    rim = (m & ~inner).reshape(-1)
    image[rim, 3] = 150


def pattern_of(spec, px):
    """A material's surface pattern over its shading colour, one metre of it (px×px, sRGB 0–1), or None."""
    if spec.surface_fg is None and spec.surface_bg is None:
        return None
    from . import pattern_paint
    base = QtGui.QColor.fromRgbF(*[min(max(float(c), 0.0), 1.0) for c in spec.color])
    pm = pattern_paint.sample(spec.surface_bg, spec.surface_fg, (px, px), base=base, mm=px / 50.0)
    return _array(pm.toImage())


def material_image(spec, size, shape="cube", beside=None):
    """A material's picture (QImage), kept: drawn once for its look and size."""
    from ..model import render_scene
    look = render_scene.look_of(spec)
    stamps = tuple(os.path.getmtime(f) if f and os.path.isfile(f) else 0.0
                   for f in (pbr.find(path, beside) for _s, path, _i in look.maps))
    key = (spec.color, spec.graphics(), pbr.encode(look), size, shape, stamps, beside)
    if key not in _made:
        if len(_made) > MADE_KEPT:
            _made.clear()
        pattern = pattern_of(spec, 128) if look.map("base") is None else None
        _made[key] = render(spec.color, look, size, shape, spec.transparency, pattern, beside)
    return _made[key]
