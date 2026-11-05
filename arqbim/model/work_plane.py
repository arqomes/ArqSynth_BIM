"""(0.412) The work plane, as Revit's «Set work plane» (the owner: «até agora não introduzimos o conceito de planos de
trabalho… podemos criar de acordo com eixos e inserir na tela onde vai ficar; pode ser também por seleção de
faces»): the plane the drawing tools — Line, Arc, Rectangle, Circle, Freehand, Bézier — start on in the 3D view where
nothing else is under the mouse (no face, no point snapped), instead of the active storey's level; Move's free point
keeps to it too. Horizontal (XY), vertical along X (XZ) or along Y (YZ) through a point clicked, or a face's plane.

One per document, for the session (the storey's level again on opening or making a project). Walls, slabs and the
other BIM elements keep to their storeys. Pure geometry."""

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


def describe(plane):
    """The key of its kind's name (i18n «workplane.<kind>»)."""
    return "workplane." + (plane.kind if plane is not None else "none")
