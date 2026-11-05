"""(0.412) The work plane, as Revit's «Set work plane» (the owner: «até agora não introduzimos o conceito de planos de
trabalho… podemos criar de acordo com eixos e inserir na tela onde vai ficar; pode ser também por seleção de
faces»): the plane the drawing tools — Line, Arc, Rectangle, Circle, Freehand, Bézier — start on in the 3D view where
nothing else is under the mouse (no face, no point snapped), instead of the active storey's level; Move's free point
keeps to it too. Horizontal (XY), vertical along X (XZ) or along Y (YZ) through a point clicked, or a face's plane.

One per document, (0.413, the owner: «Sim, guardar») kept with the project in its side file and set again on opening
it (a new project: the storey's level). Walls, slabs and the other BIM elements keep to their storeys. Pure
geometry."""

from dataclasses import dataclass

import numpy as np

from ..core.sketch_geometry import plane_axes

KINDS = ("xy", "xz", "yz", "face")
NORMALS = {"xy": (0.0, 0.0, 1.0), "xz": (0.0, -1.0, 0.0), "yz": (1.0, 0.0, 0.0)}


@dataclass
class WorkPlane:
    origin: np.ndarray
    normal: np.ndarray
    u: np.ndarray
    v: np.ndarray
    kind: str               # "xy" | "xz" | "yz" | "face"

    def matrix(self):
        """4x4: its u, v, normal as the local x, y, z, its origin as the local origin."""
        m = np.eye(4)
        m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = self.u, self.v, self.normal, self.origin
        return m

    def contains(self, point, tol=1e-6):
        return abs(float((np.asarray(point, dtype=float) - self.origin) @ self.normal)) <= tol


def by_axes(kind, point):
    """The plane XY (horizontal), XZ (vertical, along X) or YZ (vertical, along Y) through `point`."""
    n = np.array(NORMALS[kind])
    u, v = plane_axes(n)
    return WorkPlane(np.asarray(point, dtype=float).copy(), n, u, v, kind)


def by_face(point, normal):
    """The plane of a face: through `point`, square to its `normal`."""
    n = np.asarray(normal, dtype=float)
    n = n / np.linalg.norm(n)
    u, v = plane_axes(n)
    return WorkPlane(np.asarray(point, dtype=float).copy(), n, u, v, "face")


def ray_point(plane, origin, direction):
    """Where the ray meets the plane (either side), or None (along it)."""
    d = np.asarray(direction, dtype=float)
    denom = float(d @ plane.normal)
    if abs(denom) < 1e-9:
        return None
    s = float((plane.origin - np.asarray(origin, dtype=float)) @ plane.normal) / denom
    return None if s < 0 else np.asarray(origin, dtype=float) + d * s


def to_dict(plane):
    """(0.413) As kept in the side file (program's coordinates)."""
    return {"kind": plane.kind, "origin": [float(c) for c in plane.origin],
            "normal": [float(c) for c in plane.normal], "u": [float(c) for c in plane.u],
            "v": [float(c) for c in plane.v]}


def from_dict(data, shift=(0.0, 0.0, 0.0)):
    """(0.413) A plane read back, moved by `shift` (the model's origin then and now) — None when not understood."""
    try:
        kind = str(data["kind"])
        origin = np.asarray(data["origin"], dtype=float).reshape(3) + np.asarray(shift, dtype=float)
        normal, u, v = (np.asarray(data[k], dtype=float).reshape(3) for k in ("normal", "u", "v"))
    except (KeyError, TypeError, ValueError):
        return None
    if kind not in KINDS or not np.all(np.isfinite(np.concatenate((origin, normal, u, v)))):
        return None
    if abs(float(np.linalg.norm(normal)) - 1.0) > 1e-6 or abs(float(np.cross(u, v) @ normal) - 1.0) > 1e-6:
        return by_face(origin, normal) if kind == "face" and np.linalg.norm(normal) > 1e-9 else \
            (by_axes(kind, origin) if kind in NORMALS else None)
    return WorkPlane(origin, normal, u, v, kind)


def describe(plane):
    """The key of its kind's name (i18n «workplane.<kind>»)."""
    return "workplane." + (plane.kind if plane is not None else "none")
