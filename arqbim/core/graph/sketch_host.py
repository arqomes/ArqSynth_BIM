"""(0.553, the owner: «se criar um polígono e tentar aplicar o painel perfurado o App não aceita. Gostaria que
funcionasse com qualquer superfície») Any flat face drawn in the model — a polygon, a rectangle, a circle, a face on a
wall or a roof, at any angle — as the surface a Visual Graph operator works on.

A sketch's faces are grouped by their plane; the plane with the most area is the surface: its faces joined into one
shape (a face with a hole: its ring around), seen from the side its normal points to, in that plane's own measures —
x along its longest straight run (level where the plane allows it), y across, its corner at (0, 0)."""

import numpy as np

PLANE_TOL = 1e-4             # m: faces this near one plane are one surface


def _level_axes(normal):
    """(x, y) in the plane of `normal`: x level (along the ground) when the plane is not itself level, else the
    world's x; y = normal × x — right-handed, seen from the normal's side."""
    n = normal / np.linalg.norm(normal)
    x = np.cross((0.0, 0.0, 1.0), n)
    if np.linalg.norm(x) < 1e-6:                     # (a level face: as a plan, x east)
        x = np.array((1.0, 0.0, 0.0)) if n[2] > 0 else np.array((-1.0, 0.0, 0.0))
    x = x / np.linalg.norm(x)
    return x, np.cross(n, x)


def plane_of(obj):
    """(frame (4, 4) world — x, y in the plane, z its normal, origin at the face's corner —, face (shapely, in the
    frame's x, y)) of a sketch's largest flat surface, or None (no faces)."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    mesh = getattr(obj, "mesh", None)
    if mesh is None or not mesh.faces:
        return None
    m = np.asarray(obj.matrix, dtype=float)
    world = [(m @ np.append(v, 1.0))[:3] for v in mesh.verts]
    groups = []                                      # [(normal, offset, [faces' points], area)]
    for f in mesh.faces:
        pts = np.array([world[i] for i in f])
        if len(pts) < 3:
            continue
        total = np.zeros(3)
        for k in range(1, len(pts) - 1):
            total += np.cross(pts[k] - pts[0], pts[k + 1] - pts[0])
        area = 0.5 * float(np.linalg.norm(total))
        if area < 1e-8:
            continue
        n = total / np.linalg.norm(total)
        d = float(n @ pts[0])
        for g in groups:
            if float(g[0] @ n) > 1 - 1e-6 and abs(g[1] - d) < PLANE_TOL:
                g[2].append(pts)
                g[3] += area
                break
        else:
            groups.append([n, d, [pts], area])
    if not groups:
        return None
    n, d, faces, _area = max(groups, key=lambda g: g[3])
    x, y = _level_axes(n)
    origin = n * d
    shape = unary_union([Polygon([((p - origin) @ x, (p - origin) @ y) for p in pts]).buffer(0) for pts in faces])
    if shape.is_empty or shape.area < 1e-6:
        return None
    x0, y0 = shape.bounds[:2]
    origin = origin + x * x0 + y * y0
    from shapely import affinity
    shape = affinity.translate(shape, -x0, -y0)
    frame = np.eye(4)
    frame[:3, 0], frame[:3, 1], frame[:3, 2], frame[:3, 3] = x, y, n, origin
    return frame, shape


def sketch_obj(doc, key):
    """The sketch of the model `key` names (its id — or that id as text, as a graph's measure keeps it), or None."""
    if doc is None or key in (None, ""):
        return None
    try:
        obj = doc.get(key)
        if obj is None and isinstance(key, str) and key.lstrip("-").isdigit():
            obj = doc.get(int(key))
    except Exception:  # (an id of nothing)
        return None
    if obj is None or getattr(obj, "is_bim", True) or not getattr(getattr(obj, "mesh", None), "faces", None):
        return None
    return obj


def is_sketch_surface(doc, guid):
    """Whether `guid` is a sketch of the model with a flat face (not of the IFC)."""
    return sketch_obj(doc, guid) is not None
