"""CAD drawings linked to a project (0.158, Phase 8, step 1): a plan's DXF laid on a storey as linework, to draw
over and, later, to make walls, openings and furniture from (as Revit's Link CAD). A view, not IFC — kept in the
file beside the IFC (the key "cad"), the DXF itself where it is (its path relative to the project too), read
again each time the project opens: a drawing changed in the CAD program is seen as it is now.

A link: where the drawing's (0, 0) is in the plan (`origin`), turned `angle` degrees about it, `units` metres a
drawing unit; its layers not shown (`hidden`); shown or not; locked or not."""

import dataclasses
import math
import os
import uuid
from dataclasses import dataclass, field

import numpy as np

SHARED_REACH = 5000.0          # m: a drawing this near the project's survey origin is in its coordinates
NEAR_ORIGIN = 1000.0           # m: a drawing this near (0, 0) is placed origin to origin
UNIT_CHOICES = (("mm", 0.001), ("cm", 0.01), ("m", 1.0))


@dataclass
class CadLink:
    name: str
    path: str
    units: float = 1.0
    origin: tuple = (0.0, 0.0)
    angle: float = 0.0
    storey: str = None
    hidden: list = field(default_factory=list)
    visible: bool = True
    locked: bool = False
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)

    def place(self, segments):
        """Segments of the drawing (K, 2, 2: drawing units) where they are in the plan (m)."""
        s = np.asarray(segments, dtype=float) * float(self.units)
        a = math.radians(self.angle)
        rot = np.array(((math.cos(a), -math.sin(a)), (math.sin(a), math.cos(a))))
        return s @ rot.T + np.asarray(self.origin, dtype=float)

    def moved(self, delta):
        o = np.asarray(self.origin, dtype=float) + np.asarray(delta, dtype=float)[:2]
        return dataclasses.replace(self, origin=(float(o[0]), float(o[1])))


_CACHE = {}                    # path -> (modified time, cad.Drawing, {layer: segments in drawing units})


def drawing_of(path):
    """(cad.Drawing, {layer: (K, 2, 2) segments in drawing units}) of a DXF — read once while it is unchanged —
    or None when it cannot be read."""
    from ..core import cad
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        return None
    found = _CACHE.get(path)
    if found is None or found[0] != stamp:
        try:
            drawing = cad.read_file(path)
        except (OSError, ValueError):
            return None
        raw = cad.segments(cad.Drawing(drawing.entities, drawing.blocks, 1.0))
        found = _CACHE[path] = (stamp, drawing, raw)
    return found[1], found[2]


_LINES = {}                    # (0.210) path -> (modified time, {layer: straight segments}, {layer: arcs}), drawing units


def wall_lines_of(path):
    """(0.210) ({layer: (K, 2, 2) straight segments}, {layer: [arcs (centre, radius, start, end)]}) of a DXF, in
    drawing units — what its walls are found in, the straight ones and the curved ones apart — or None."""
    from ..core import cad
    found = drawing_of(path)
    if found is None:
        return None
    stamp = os.path.getmtime(path)
    cached = _LINES.get(path)
    if cached is None or cached[0] != stamp:
        drawing = cad.Drawing(found[0].entities, found[0].blocks, 1.0)
        cached = _LINES[path] = (stamp, cad.segments(drawing, straight=True), cad.arcs(drawing))
    return cached[1], cached[2]


_SHAPES = {}                   # (0.211) path -> (modified time, {layer: (polygons, circles)}), drawing units


def column_shapes_of(path):
    """(0.211) {layer: ([polygon corners], [(centre, radius)])} of a DXF's closed shapes, in drawing units — what its
    columns are found in — or None."""
    from ..core import cad
    found = drawing_of(path)
    if found is None:
        return None
    stamp = os.path.getmtime(path)
    cached = _SHAPES.get(path)
    if cached is None or cached[0] != stamp:
        cached = _SHAPES[path] = (stamp, cad.closed_shapes(cad.Drawing(found[0].entities, found[0].blocks, 1.0)))
    return cached[1]


def placed_shapes(link, layers):
    """(0.211) ([polygon corners (N, 2) m], [(centre (2,), radius m)]) of these layers' closed shapes, where they
    are in the plan."""
    shapes = column_shapes_of(link.path) or {}
    polygons, circles = [], []
    for layer in layers:
        found = shapes.get(layer)
        if found is None:
            continue
        polygons += [link.place(np.asarray(p, dtype=float)) for p in found[0]]
        circles += [(link.place(np.asarray([c], dtype=float))[0], float(r) * float(link.units)) for c, r in found[1]]
    return polygons, circles


def place_arc(link, arc):
    """(0.210) An arc of the drawing (centre, radius, start, end: drawing units, degrees) where it is in the plan:
    (centre (2,), radius m, start, end degrees)."""
    centre, radius, a0, a1 = arc
    c = link.place(np.array([centre], dtype=float))[0]
    return c, float(radius) * float(link.units), float(a0) + float(link.angle), float(a1) + float(link.angle)


def placed_segments(link):
    """{layer: (K, 2, 2) plan segments (m)} of a link's layers shown — {} when its file is missing."""
    found = drawing_of(link.path)
    if found is None:
        return {}
    _drawing, raw = found
    return {k: link.place(v) for k, v in raw.items() if k not in link.hidden}


def placement(raw, units, project_origin, view_centre):
    """Where a new link goes: (origin, how — "shared" | "origin" | "centre"). In the project's survey coordinates
    when it is near them; origin to origin when the drawing is near (0, 0); else its middle in the middle of what is
    seen."""
    every = np.concatenate(list(raw.values())) if raw else np.zeros((0, 2, 2))
    if not len(every):
        return (0.0, 0.0), "origin"
    pts = every.reshape(-1, 2) * float(units)
    centre = (pts.min(axis=0) + pts.max(axis=0)) / 2
    shared = np.asarray(project_origin, dtype=float)[:2]
    if np.any(shared) and float(np.linalg.norm(centre - shared)) < SHARED_REACH:
        return (float(-shared[0]), float(-shared[1])), "shared"
    if float(np.linalg.norm(centre)) < NEAR_ORIGIN:
        return (0.0, 0.0), "origin"
    o = np.asarray(view_centre, dtype=float)[:2] - centre
    return (float(o[0]), float(o[1])), "centre"


def to_dict(link, base_dir=None):
    data = {"name": link.name, "path": link.path, "units": float(link.units),
            "origin": [float(c) for c in link.origin], "angle": float(link.angle), "storey": link.storey,
            "hidden": list(link.hidden), "visible": bool(link.visible), "locked": bool(link.locked), "uid": link.uid}
    if base_dir:
        try:
            data["relative"] = os.path.relpath(link.path, base_dir)
        except ValueError:
            pass
    return data


def from_dict(data, shift=(0.0, 0.0), base_dir=None):
    try:
        path = str(data["path"])
        if base_dir and data.get("relative"):
            near = os.path.normpath(os.path.join(base_dir, str(data["relative"])))
            if os.path.exists(near) or not os.path.exists(path):
                path = near
        origin = tuple(float(c) + float(s) for c, s in zip(data["origin"][:2], shift[:2]))
        link = CadLink(str(data.get("name") or os.path.basename(path)), path, float(data.get("units", 1.0)), origin,
                       float(data.get("angle", 0.0)), data.get("storey"), [str(k) for k in data.get("hidden", ())],
                       bool(data.get("visible", True)), bool(data.get("locked", False)))
        if data.get("uid"):
            link.uid = str(data["uid"])
        return link if link.units > 0 else None
    except (KeyError, TypeError, ValueError, IndexError):
        return None
