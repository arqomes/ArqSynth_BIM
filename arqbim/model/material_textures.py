"""(0.469) The textured faces of the model as the Realistic view style shows them: an element's triangles whose
material's realistic look has pictures (core/pbr.Look), gathered by material — their corners a hair off the faces,
their normals and where their pictures lie on them (core/pbr.uv: as SketchUp and Revit lay a picture on a box, in the
model's metres). Pure NumPy; the 3D view makes one mesh a material of each batch of them (render/batches.py)."""

import numpy as np

from ..core import pbr

LIFT = 0.0006          # m: the textured faces this far off the faces (the edges, 2 mm off, stay over them)


def textured(key):
    """A material's realistic look when it has pictures, else None."""
    from ..ifc import catalog
    spec = catalog.MATERIALS.get(key) if key else None
    look = getattr(spec, "look", None)
    return look if look is not None and look.textured else None


def groups(corners, normals, keys, lift=LIFT):
    """[(material key, corners (3K, 3), normals (3K, 3), pictures' coordinates (3K, 2))] of an element's triangles
    (corners (T, 3, 3), normals (T, 3), keys (T,) — each its material's key, "": none) — those of materials with
    pictures; [] for none."""
    keys = np.asarray(keys if keys is not None else (), dtype=object)
    if not len(keys):
        return []
    corners = np.asarray(corners, dtype=float).reshape(-1, 3, 3)
    normals = np.asarray(normals, dtype=float).reshape(-1, 3)
    out = []
    for key in sorted({k for k in keys if k}):
        look = textured(key)
        if look is None:
            continue
        pick = keys == key
        tri, n = corners[pick], normals[pick]
        length = np.linalg.norm(n, axis=1, keepdims=True)
        n = n / np.where(length > 1e-12, length, 1.0)
        points = tri.reshape(-1, 3)
        each = np.repeat(n, 3, axis=0)
        uv = pbr.uv(points, each, look)
        out.append((key, np.ascontiguousarray(points + each * lift, dtype=np.float32),
                    np.ascontiguousarray(each, dtype=np.float32), np.ascontiguousarray(uv, dtype=np.float32)))
    return out
