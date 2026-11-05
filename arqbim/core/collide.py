"""Walking through the model without going through it (0.83): a step forward is cut short in front of what is
in the way — a wall, a column, a window, furniture —, as SketchUp's Walk. The body is a few horizontal rays (at
the eyes and lower, at the waist), each stopping BODY_RADIUS before the face it meets. Doors are walked through
(they open), and so are spaces and openings.

Pure numpy (no window): the objects near the step are found by their boxes first (SnapIndex.along), then their
triangles are cut by the rays (Möller–Trumbore, all at once)."""

import numpy as np

BODY_RADIUS = 0.25              # m kept from a face in the way
BODY_HEIGHTS = (0.0, -0.9)      # m from the eyes: the rays cast (the eyes, the waist)
WALK_THROUGH = frozenset(("IfcDoor", "IfcSpace", "IfcOpeningElement", "IfcVirtualElement", "IfcAnnotation",
                          "IfcGrid", "IfcZone"))


def world_triangles(obj):
    """(N, 3, 3) the object's triangles in world coordinates (an IFC element's mesh is already there)."""
    mesh = obj.mesh
    tris, _owner = mesh.triangulate()
    verts = np.asarray(mesh.verts, dtype=float).reshape(-1, 3)
    if not len(tris) or not len(verts):
        return np.zeros((0, 3, 3))
    m = np.asarray(getattr(obj, "matrix", np.eye(4)), dtype=float)
    if not np.allclose(m, np.eye(4)):
        verts = verts @ m[:3, :3].T + m[:3, 3]
    return verts[np.asarray(tris, dtype=np.int64)]


def ray_triangles(origin, direction, triangles):
    """Distance along the ray to the nearest triangle it meets (either side), or None."""
    if not len(triangles):
        return None
    o, d = np.asarray(origin, dtype=float), np.asarray(direction, dtype=float)
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    e1, e2 = b - a, c - a
    p = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, p)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    s = o - a
    u = np.einsum("ij,ij->i", s, p) * inv
    q = np.cross(s, e1)
    v = (q @ d) * inv
    t = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 1e-9)
    return float(t[hit].min()) if hit.any() else None


def free_step(eye, direction, length, objects):
    """How far (≤ length) one can walk from `eye` along the level unit `direction` before something is in
    the way; `objects`: the ones near the step (with .mesh, .matrix, .ifc_class / .is_bim)."""
    eye, d = np.asarray(eye, dtype=float), np.asarray(direction, dtype=float)
    reach = length + BODY_RADIUS
    nearest = None
    for obj in objects:
        if getattr(obj, "is_bim", False) and getattr(obj, "ifc_class", None) in WALK_THROUGH:
            continue
        triangles = world_triangles(obj)
        for dz in BODY_HEIGHTS:
            t = ray_triangles(eye + np.array((0.0, 0.0, dz)), d, triangles)
            if t is not None and t <= reach and (nearest is None or t < nearest):
                nearest = t
    if nearest is None:
        return length
    return max(0.0, min(length, nearest - BODY_RADIUS))
