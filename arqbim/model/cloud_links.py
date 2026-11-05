"""Point clouds linked to a project (0.161, Phase 8, step 2): a laser scan or a photogrammetry laid in the model, to
see the building as it is and, then, to make its walls and floors from it. A view, not IFC — kept in the file
beside the IFC (the key "clouds"), the scan itself where it is (its path relative to the project too), read again
each time the project opens, thinned to what the screen can show.

A link: where the scan's (0, 0, 0) is in the model (`origin`, x y z — its height too: a scan's floor is seldom at
0), `units` metres a scan unit, its storey (its plan shows it), shown or not, how big its points are drawn."""

import os
import struct
import uuid
from dataclasses import dataclass, field

import numpy as np

SHOWN_MOST = 1_500_000          # points drawn at most (thinned evenly: a scan of 50 million still turns smoothly)
SHARED_REACH = 5000.0
NEAR_ORIGIN = 1000.0


@dataclass
class CloudLink:
    name: str
    path: str
    units: float = 1.0
    origin: tuple = (0.0, 0.0, 0.0)
    storey: str = None
    visible: bool = True
    size: float = 2.0           # pixels
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)

    def place(self, points):
        return np.asarray(points, dtype=float) * float(self.units) + np.asarray(self.origin, dtype=float)


_CACHE = {}                      # (path, most) -> (modified time, PointCloud)


def cloud_of(path, most=SHOWN_MOST):
    """The PointCloud of a file (at most `most` points) — read once while it is unchanged — or None."""
    from ..core import pointcloud
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        return None
    key = (path, most)
    found = _CACHE.get(key)
    if found is None or found[0] != stamp:
        try:
            cloud = pointcloud.read_file(path, most)
        except (OSError, ValueError, KeyError, struct.error):  # (not a cloud, damaged, a property missing)
            return None
        found = _CACHE[key] = (stamp, cloud)
    return found[1]


def placement(cloud, units, project_origin, view_centre):
    """Where a new link goes: (origin (x, y, z), how) — in the project's survey coordinates when near them, as it is
    when near (0, 0), else its middle in the middle of the view (its floor, the lowest of its points, at 0)."""
    box = cloud.bounds()
    if box is None:
        return (0.0, 0.0, 0.0), "origin"
    lo, hi = np.asarray(box[0]) * units, np.asarray(box[1]) * units
    centre = (lo + hi) / 2
    shared = np.asarray(project_origin, dtype=float)
    if np.any(shared[:2]) and float(np.linalg.norm(centre[:2] - shared[:2])) < SHARED_REACH:
        return (float(-shared[0]), float(-shared[1]), float(-shared[2])), "shared"
    if float(np.linalg.norm(centre[:2])) < NEAR_ORIGIN:
        return (0.0, 0.0, 0.0), "origin"
    return (float(view_centre[0] - centre[0]), float(view_centre[1] - centre[1]), float(-lo[2])), "centre"


def to_dict(link, base_dir=None):
    data = {"name": link.name, "path": link.path, "units": float(link.units),
            "origin": [float(c) for c in link.origin], "storey": link.storey, "visible": bool(link.visible),
            "size": float(link.size), "uid": link.uid}
    if base_dir:
        try:
            data["relative"] = os.path.relpath(link.path, base_dir)
        except ValueError:
            pass
    return data


def from_dict(data, shift=(0.0, 0.0, 0.0), base_dir=None):
    try:
        path = str(data["path"])
        if base_dir and data.get("relative"):
            near = os.path.normpath(os.path.join(base_dir, str(data["relative"])))
            if os.path.exists(near) or not os.path.exists(path):
                path = near
        o = list(data["origin"]) + [0.0] * (3 - len(data["origin"]))
        origin = tuple(float(c) + float(s) for c, s in zip(o[:3], list(shift) + [0.0] * (3 - len(shift))))
        link = CloudLink(str(data.get("name") or os.path.basename(path)), path, float(data.get("units", 1.0)),
                         origin, data.get("storey"), bool(data.get("visible", True)), float(data.get("size", 2.0)))
        if data.get("uid"):
            link.uid = str(data["uid"])
        return link if link.units > 0 else None
    except (KeyError, TypeError, ValueError, IndexError):
        return None
