"""Background images (0.154, Phase 7, step 2): a scanned plan, an aerial photo, a sketch — a picture laid flat on a
storey, to draw over. Imported, calibrated with a measure one knows (two points on it and their real distance),
placed (that first point where it goes in the model, turned towards the second) and locked.

A view, not IFC: kept in the file beside the IFC (.arqsynthbim), the picture itself where it was (its path
relative to the project, and the full one). Pure data and geometry here (no Qt): the window loads the pixels,
the viewport draws them.

An image's frame: its lower-left corner `origin` (x, y on its storey's level), turned `angle` degrees
(counter-clockwise from X) about it; `width` metres across, its height in the picture's proportions. (0.208) A
vertical one (a photo of a facade, put on a wall's face) stands on that lower edge, its foot `base` metres over its
storey's level, read from the side its front faces (across × up)."""

import dataclasses
import math
import os
import uuid
from dataclasses import dataclass, field

import numpy as np

METRES_PER_PIXEL = 0.01          # at import, before calibrating: one pixel a centimetre…
WIDTH_RANGE = (5.0, 500.0)       # …but never smaller / bigger than this across (m)
DEFAULT_OPACITY = 0.7
EXTENSIONS = ("png", "jpg", "jpeg", "bmp", "gif", "tif", "tiff", "webp")


@dataclass
class BackgroundImage:
    name: str
    path: str                     # the picture file (full path)
    pixels: tuple                 # (width, height) of the picture, in pixels
    origin: tuple = (0.0, 0.0)    # its lower-left corner (x, y), program coordinates
    width: float = 10.0           # m across
    angle: float = 0.0            # degrees, about its lower-left corner
    storey: str = None            # GlobalId of the storey it lies on (None: level 0)
    opacity: float = DEFAULT_OPACITY
    visible: bool = True
    locked: bool = False
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)
    vertical: bool = False        # (0.208) standing on its lower edge (a facade's photo), not laid flat
    base: float = 0.0             # (0.208) a vertical one's foot over its storey's level (m)
    # (0.209) the part of it kept: (across from, up from, across to, up to), fractions of its width and height from its
    # lower-left corner — None: all of it
    crop: tuple = None

    @property
    def height(self):
        w, h = self.pixels
        return self.width * float(h) / float(w) if w else self.width

    def axes(self):
        """Its across (u) and up (v) directions in the plan (unit vectors)."""
        a = math.radians(self.angle)
        return np.array((math.cos(a), math.sin(a))), np.array((-math.sin(a), math.cos(a)))

    def corners(self):
        """Its four corners (x, y): lower-left, lower-right, upper-right, upper-left."""
        o = np.asarray(self.origin, dtype=float)
        u, v = self.axes()
        return [o, o + u * self.width, o + u * self.width + v * self.height, o + v * self.height]

    def corners3d(self, level):
        """(0.208) Its four corners in the model (x, y, z), its storey at `level`: laid at that height, or standing
        up from its foot (lower-left, lower-right, upper-right, upper-left)."""
        if not self.vertical:
            return [np.array((x, y, float(level))) for x, y in self.corners()]
        u, _v = self.axes()
        o = np.array((float(self.origin[0]), float(self.origin[1]), float(level) + float(self.base)))
        across, up = np.array((u[0], u[1], 0.0)) * self.width, np.array((0.0, 0.0, self.height))
        return [o, o + across, o + across + up, o + up]

    def front(self):
        """(0.208) The side a vertical image is read from (x, y, z): its across × up."""
        u, _v = self.axes()
        return np.array((u[1], -u[0], 0.0))

    def stood(self, a, b, facing, level):
        """(0.208) Standing on a facade: its lower-left at the model point a, its lower-right towards b (its width
        their distance across), read from the side `facing` (a face's normal: a and b swapped when they were
        clicked the other way), its storey at `level`. None when a and b are (nearly) one point."""
        a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        d = (b - a)[:2]
        width = float(np.linalg.norm(d))
        if width < 1e-6:
            return None
        if float(np.dot((d[1], -d[0]), np.asarray(facing, dtype=float)[:2])) < 0:   # (read from behind: swapped)
            a, b, d = b, a, -d
        return dataclasses.replace(self, vertical=True, origin=(float(a[0]), float(a[1])), width=width,
                                   angle=math.degrees(math.atan2(d[1], d[0])) % 360.0,
                                   base=float(min(a[2], b[2])) - float(level))

    def local(self, point):
        """A plan point (x, y) in the image's frame: (across, up) in metres from its lower-left corner."""
        u, v = self.axes()
        d = np.asarray(point, dtype=float)[:2] - np.asarray(self.origin, dtype=float)
        return float(d @ u), float(d @ v)

    def contains(self, point):
        s, r = self.local(point)
        s0, r0, s1, r1 = self.kept()
        return s0 * self.width - 1e-9 <= s <= s1 * self.width + 1e-9 and r0 * self.height - 1e-9 <= r <= \
            r1 * self.height + 1e-9

    def kept(self):
        """(0.209) The part of it shown: (across from, up from, across to, up to), fractions — all: (0, 0, 1, 1)."""
        return tuple(self.crop) if self.crop else (0.0, 0.0, 1.0, 1.0)

    def kept_corners(self, level):
        """(0.209) The corners (x, y, z) of the part of it shown (lower-left, lower-right, upper-right, upper-left)."""
        ll, lr, _ur, ul = self.corners3d(level)
        across, up = lr - ll, ul - ll
        s0, r0, s1, r1 = self.kept()
        return [ll + across * s0 + up * r0, ll + across * s1 + up * r0, ll + across * s1 + up * r1,
                ll + across * s0 + up * r1]

    def texcoords(self):
        """(0.209) The picture's coordinates (0 at its top) of kept_corners' four corners."""
        s0, r0, s1, r1 = self.kept()
        return ((s0, 1.0 - r0), (s1, 1.0 - r0), (s1, 1.0 - r1), (s0, 1.0 - r1))

    def fraction(self, point, level):
        """(0.209) A model point on it (x, y, z) as fractions of its width and height from its lower-left corner."""
        ll, lr, _ur, ul = self.corners3d(level)
        across, up = lr - ll, ul - ll
        d = np.asarray(point, dtype=float) - ll
        return float(d @ across) / float(across @ across), float(d @ up) / float(up @ up)

    def cropped(self, a, b):
        """(0.209) Cut to the rectangle between the fractions a and b (across, up) — None when too thin."""
        s0, s1 = sorted((min(max(float(a[0]), 0.0), 1.0), min(max(float(b[0]), 0.0), 1.0)))
        r0, r1 = sorted((min(max(float(a[1]), 0.0), 1.0), min(max(float(b[1]), 0.0), 1.0)))
        if s1 - s0 < 1e-3 or r1 - r0 < 1e-3:
            return None
        return dataclasses.replace(self, crop=(s0, r0, s1, r1))

    def scaled(self, about, factor):
        """Bigger / smaller by `factor` about the plan point `about` (it stays where it is)."""
        about = np.asarray(about, dtype=float)[:2]
        o = about + (np.asarray(self.origin, dtype=float) - about) * float(factor)
        return dataclasses.replace(self, origin=(float(o[0]), float(o[1])), width=self.width * float(factor))

    def moved(self, delta):
        o = np.asarray(self.origin, dtype=float) + np.asarray(delta, dtype=float)[:2]
        return dataclasses.replace(self, origin=(float(o[0]), float(o[1])))

    def turned(self, about, degrees):
        """Turned `degrees` (counter-clockwise) about the plan point `about`."""
        about = np.asarray(about, dtype=float)[:2]
        a = math.radians(degrees)
        rot = np.array(((math.cos(a), -math.sin(a)), (math.sin(a), math.cos(a))))
        o = about + rot @ (np.asarray(self.origin, dtype=float) - about)
        return dataclasses.replace(self, origin=(float(o[0]), float(o[1])), angle=(self.angle + degrees) % 360.0)


def default_width(pixels):
    """How wide a picture is laid at import (m), before it is calibrated."""
    lo, hi = WIDTH_RANGE
    return float(min(max(pixels[0] * METRES_PER_PIXEL, lo), hi))


def placed(name, path, pixels, centre, storey=None):
    """A new image of `pixels`, centred on the plan point `centre`."""
    image = BackgroundImage(name, os.path.abspath(path), (int(pixels[0]), int(pixels[1])), storey=storey,
                            width=default_width(pixels))
    c = np.asarray(centre, dtype=float)[:2]
    return image.moved(c - (image.width / 2, image.height / 2))


def calibration(a, b, real):
    """The factor that makes the distance between the plan points a and b `real` metres — or None."""
    measured = float(np.linalg.norm(np.asarray(b, dtype=float)[:2] - np.asarray(a, dtype=float)[:2]))
    if measured < 1e-9 or real is None or real <= 0:
        return None
    return float(real) / measured


def turn_towards(about, point, target):
    """The angle (degrees) that turns the direction about→point to about→target."""
    d0 = np.asarray(point, dtype=float)[:2] - np.asarray(about, dtype=float)[:2]
    d1 = np.asarray(target, dtype=float)[:2] - np.asarray(about, dtype=float)[:2]
    if np.linalg.norm(d0) < 1e-9 or np.linalg.norm(d1) < 1e-9:
        return 0.0
    return math.degrees(math.atan2(d1[1], d1[0]) - math.atan2(d0[1], d0[0]))


def to_dict(image, base_dir=None):
    data = {"name": image.name, "path": image.path, "pixels": [int(c) for c in image.pixels],
            "origin": [float(c) for c in image.origin], "width": float(image.width), "angle": float(image.angle),
            "storey": image.storey, "opacity": float(image.opacity), "visible": bool(image.visible),
            "locked": bool(image.locked), "uid": image.uid}
    if image.vertical:
        data["vertical"], data["base"] = True, float(image.base)
    if image.crop:
        data["crop"] = [float(c) for c in image.crop]
    if base_dir:
        try:
            data["relative"] = os.path.relpath(image.path, base_dir)
        except ValueError:                              # (another drive)
            pass
    return data


def from_dict(data, shift=(0.0, 0.0), base_dir=None):
    """An image saved beside an IFC file — its picture looked for beside the project first (the folder may have
    moved), then where it was. None if the data is not an image's."""
    try:
        path = str(data["path"])
        if base_dir and data.get("relative"):
            near = os.path.normpath(os.path.join(base_dir, str(data["relative"])))
            if os.path.exists(near) or not os.path.exists(path):
                path = near
        origin = tuple(float(c) + float(s) for c, s in zip(data["origin"][:2], shift[:2]))
        image = BackgroundImage(str(data.get("name") or os.path.basename(path)), path,
                                (int(data["pixels"][0]), int(data["pixels"][1])), origin, float(data["width"]),
                                float(data.get("angle", 0.0)), data.get("storey"),
                                min(max(float(data.get("opacity", DEFAULT_OPACITY)), 0.05), 1.0),
                                bool(data.get("visible", True)), bool(data.get("locked", False)))
        if data.get("uid"):
            image.uid = str(data["uid"])
        if data.get("vertical"):                        # (0.208)
            image.vertical, image.base = True, float(data.get("base", 0.0))
        crop = data.get("crop")
        if crop and len(crop) == 4:                     # (0.209)
            image.crop = tuple(min(max(float(c), 0.0), 1.0) for c in crop)
        return image if image.pixels[0] > 0 and image.pixels[1] > 0 and image.width > 0 else None
    except (KeyError, TypeError, ValueError, IndexError):
        return None
