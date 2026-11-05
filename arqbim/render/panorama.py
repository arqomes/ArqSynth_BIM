"""(0.368) A 360° panorama from six renders: Mitsuba 3 has no spherical camera, so the panorama is six square views of
90° from the same eye — ahead, to the right, behind, to the left, up and down — sampled into one equirectangular
picture (2:1: its middle straight ahead, the horizon across its middle; what 360° viewers take, the ArqSynth
Presentation's among them).

A face is (its direction, its right, its up): seen as Mitsuba's look_at makes a camera from (eye, eye + direction, up)
— its picture's right is direction × up, its top up —, a pixel (i, j) of an N × N face looks along direction +
x·right + y·up with x = 2(i + ½)/N − 1, y = 1 − 2(j + ½)/N. Each face is rendered a little wider than its 90° (a
margin of pixels round it, margin()) and only its middle used: the edges of a render — where its grain filter and the
sampling have nothing beyond — never meet at a seam. Pure NumPy."""

import math

import numpy as np

FACES = ("front", "right", "back", "left", "up", "down")
MARGIN = 1.0 / 32.0             # a face's margin: this much of its size each side (and at least 2 pixels)


def frame(forward):
    """(forward, right, up) of a panorama looking along `forward` (made level): up is the model's Z."""
    f = np.asarray(forward, dtype=float).copy()
    f[2] = 0.0
    if np.linalg.norm(f) < 1e-9:
        f = np.array((0.0, 1.0, 0.0))
    f /= np.linalg.norm(f)
    z = np.array((0.0, 0.0, 1.0))
    return f, np.cross(f, z), z


def faces(forward):
    """{face: (direction, right, up)} of the six faces round a panorama looking along `forward`."""
    f, r, z = frame(forward)
    out = {}
    for name, direction, up in (("front", f, z), ("right", r, z), ("back", -f, z), ("left", -r, z),
                                ("up", z, -f), ("down", -z, f)):
        right = np.cross(direction, up)
        out[name] = (direction, right / np.linalg.norm(right), np.cross(right, direction))
    return out


def directions(width, height, forward):
    """(height, width, 3): the direction each pixel of the equirectangular picture looks along — its column the
    longitude (−180° at the left, 0 in the middle: forward, +90° to the right), its row the latitude (+90° at the top)."""
    f, r, z = frame(forward)
    lon = (np.arange(width) + 0.5) / width * 2.0 * np.pi - np.pi
    lat = np.pi / 2.0 - (np.arange(height) + 0.5) / height * np.pi
    lon, lat = np.meshgrid(lon, lat)
    c = np.cos(lat)
    return (c * np.sin(lon))[..., None] * r + (c * np.cos(lon))[..., None] * f + np.sin(lat)[..., None] * z


def equirect(pictures, forward, width, height, inner=None):
    """The equirectangular picture (height, width, C) of six square face pictures ({face: (N, N, C)}, as faces()
    says how each was taken), each pixel from the face it looks into (bilinear). inner: the pixels of a face's 90° —
    the face rendered with a margin round them (face_fov) —; None: the whole face is its 90°."""
    bases = faces(forward)
    d = directions(width, height, forward)
    first = next(iter(pictures.values()))
    size, channels = first.shape[0], first.shape[2]
    n = float(inner or size)
    out = np.zeros((height, width, channels), dtype=np.float64)
    along = np.stack([d @ bases[name][0] for name in FACES], axis=-1)
    best = np.argmax(along, axis=-1)
    for k, name in enumerate(FACES):
        mask = best == k
        if not mask.any():
            continue
        direction, right, up = bases[name]
        dd = d[mask]
        depth = dd @ direction
        x = (dd @ right) / depth
        y = (dd @ up) / depth
        i = x * n / 2.0 + size / 2.0 - 0.5
        j = -y * n / 2.0 + size / 2.0 - 0.5
        out[mask] = _bilinear(np.asarray(pictures[name], dtype=np.float64), i, j)
    return out


def _bilinear(picture, i, j):
    n_rows, n_cols = picture.shape[:2]
    i = np.clip(i, 0.0, n_cols - 1.0)
    j = np.clip(j, 0.0, n_rows - 1.0)
    i0, j0 = np.floor(i).astype(int), np.floor(j).astype(int)
    i1, j1 = np.minimum(i0 + 1, n_cols - 1), np.minimum(j0 + 1, n_rows - 1)
    a, b = (i - i0)[:, None], (j - j0)[:, None]
    return (picture[j0, i0] * (1 - a) * (1 - b) + picture[j0, i1] * a * (1 - b)
            + picture[j1, i0] * (1 - a) * b + picture[j1, i1] * a * b)


def face_size(width):
    """The faces' size for an equirectangular picture `width` wide: a quarter of it (the same detail ahead)."""
    return max(16, int(round(width / 4.0)))


def margin(n):
    """The pixels each side round a face's `n` of 90°."""
    return max(2, int(math.ceil(n * MARGIN)))


def face_fov(n):
    """The field of view (degrees, across) of a face of `n` pixels of 90° rendered with its margin round them."""
    return math.degrees(2.0 * math.atan((n + 2.0 * margin(n)) / float(n)))
