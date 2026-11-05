"""Gaussian splats for presentation (0.176, Phase 8, step 3; 0.216: the linked point clouds too, straight from their
points): the model as a cloud of flat gaussians — the 3D
Gaussian Splatting file the web viewers read (SuperSplat, PlayCanvas, …) — laid on every surface it shows, a
few centimetres apart, each one a small disc lying on its face, coloured by the element's material (its style's
colour; by its class, as on the screen, when it has none), the light of a sun from the south-west baked in (a splat
keeps its colour whatever the side it is seen from), glass see-through.

The file: a binary little-endian PLY with the usual properties — x y z, nx ny nz, f_dc_0..2 (the colour as
degree-0 spherical harmonics), opacity (through a logit), scale_0..2 (logarithms), rot_0..3 (a quaternion w x y z)
— with Y up, as those viewers have it. Pure numpy."""

import ifcopenshell.util.element
import numpy as np

SH_C0 = 0.28209479177387814             # the degree-0 spherical harmonic
QUALITY = {"low": 0.08, "medium": 0.05, "high": 0.03}       # m between splats
MAX_SPLATS = 4000000                    # (more is refused: a file of over ~270 MB)
SUN = np.array((-0.4, -0.6, 0.7)) / np.linalg.norm((-0.4, -0.6, 0.7))     # (from the south-west, high)
AMBIENT = 0.55                          # the light everywhere; the sun's the rest
SOLID, GLASS = 0.98, 0.35               # opacities
GLASS_CLASSES = ("IfcWindow", "IfcCurtainWall")
SKIP = ("IfcOpeningElement", "IfcSpace", "IfcVirtualElement", "IfcAnnotation", "IfcGrid")
PROPS = ("x", "y", "z", "nx", "ny", "nz", "f_dc_0", "f_dc_1", "f_dc_2", "opacity", "scale_0", "scale_1", "scale_2",
         "rot_0", "rot_1", "rot_2", "rot_3")
Y_UP = np.array(((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0)))     # (x, y, z) → (x, z, −y)


def _hex(text):
    text = text.lstrip("#")
    return tuple(int(text[k:k + 2], 16) / 255.0 for k in (0, 2, 4))


def colour(doc, obj):
    """The colour (RGB 0..1) an object is shown with: its material's style colour (the first layer's, the first
    profile's…), else its class's on the screen; a sketch, the screen's default."""
    from ..model.project_types import _colour
    from ..render.viewport import BIM_COLORS, BIM_DEFAULT
    if obj.is_bim and obj.ifc_class not in GLASS_CLASSES:
        e = doc.ifc.by_guid(obj.id)
        for m in (ifcopenshell.util.element.get_materials(e) if e is not None else []):
            rgb = _colour(m)
            if rgb is not None:
                return rgb
    return _hex(BIM_COLORS.get(obj.ifc_class, BIM_DEFAULT) if obj.is_bim else BIM_DEFAULT)


def sample(verts, tris, spacing, rng):
    """(points (n, 3), normals (n, 3)) spread over the triangles about `spacing` apart: as many in each as its area
    holds (the fraction left decided by chance), at random inside it; each with its triangle's normal."""
    a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    cross = np.cross(b - a, c - a)
    double = np.linalg.norm(cross, axis=1)
    keep = double > 1e-12
    a, b, c, cross, double = a[keep], b[keep], c[keep], cross[keep], double[keep]
    expected = double / 2.0 / (spacing * spacing)
    count = np.floor(expected).astype(np.int64) + (rng.random(len(expected)) < expected % 1.0)
    idx = np.repeat(np.arange(len(count)), count)
    r1, r2 = np.sqrt(rng.random(len(idx))), rng.random(len(idx))
    points = (a[idx] * (1.0 - r1)[:, None] + b[idx] * (r1 * (1.0 - r2))[:, None] + c[idx] * (r1 * r2)[:, None])
    return points, (cross / double[:, None])[idx]


def quaternions(normals):
    """(n, 4) w x y z: the rotations that turn the z axis onto each normal (a disc's flat side onto its face)."""
    w = 1.0 + normals[:, 2]
    q = np.column_stack((w, -normals[:, 1], normals[:, 0], np.zeros(len(normals))))
    down = w < 1e-9                                         # (facing straight down: half a turn about x)
    q[down] = (0.0, 1.0, 0.0, 0.0)
    return q / np.linalg.norm(q, axis=1)[:, None]


def splats(doc, spacing=QUALITY["medium"], seed=0):
    """{property: (n,) float32} the model's splats (PROPS), in Y-up coordinates."""
    rng = np.random.default_rng(seed)
    parts = []
    for obj in doc.objects.values():
        mesh = getattr(obj, "mesh", None)
        if mesh is None or (obj.is_bim and obj.ifc_class in SKIP) or not hasattr(mesh, "triangulate"):
            continue
        verts = np.asarray(mesh.verts, dtype=float).reshape(-1, 3)
        if not len(verts):
            continue
        m = np.asarray(obj.matrix, dtype=float)
        verts = verts @ m[:3, :3].T + m[:3, 3]
        tris, _owner = mesh.triangulate()
        tris = np.asarray(tris, dtype=np.int64).reshape(-1, 3)
        if not len(tris):
            continue
        points, normals = sample(verts, tris, spacing, rng)
        if not len(points):
            continue
        lit = AMBIENT + (1.0 - AMBIENT) * np.clip(normals @ SUN, 0.0, 1.0)
        rgb = np.clip(np.asarray(colour(doc, obj))[None, :] * lit[:, None], 0.0, 1.0)
        alpha = GLASS if obj.is_bim and obj.ifc_class in GLASS_CLASSES else SOLID
        parts.append((points, normals, rgb, np.full(len(points), alpha)))
    if not parts:
        return {}
    points, normals, rgb, alpha = (np.concatenate([p[k] for p in parts]) for k in range(4))
    if len(points) > MAX_SPLATS:
        raise ValueError("splat_many")
    points, normals = points @ Y_UP.T, normals @ Y_UP.T
    q = quaternions(normals)
    dc = (rgb - 0.5) / SH_C0
    flat = np.log(spacing * 0.6)                            # (a disc: wide on its face, thin across it)
    out = {"x": points[:, 0], "y": points[:, 1], "z": points[:, 2], "nx": normals[:, 0], "ny": normals[:, 1],
           "nz": normals[:, 2], "f_dc_0": dc[:, 0], "f_dc_1": dc[:, 1], "f_dc_2": dc[:, 2],
           "opacity": np.log(alpha / (1.0 - alpha)), "scale_0": np.full(len(points), flat),
           "scale_1": np.full(len(points), flat), "scale_2": np.full(len(points), np.log(spacing * 0.03)),
           "rot_0": q[:, 0], "rot_1": q[:, 1], "rot_2": q[:, 2], "rot_3": q[:, 3]}
    return {k: np.ascontiguousarray(v, dtype=np.float32) for k, v in out.items()}


def write_ply(path, data):
    """The splats to a binary little-endian PLY file. Returns how many."""
    n = len(data["x"]) if data else 0
    header = "ply\nformat binary_little_endian 1.0\nelement vertex {}\n".format(n) + \
        "".join("property float {}\n".format(p) for p in PROPS) + "end_header\n"
    table = np.zeros((n, len(PROPS)), dtype="<f4")
    for k, p in enumerate(PROPS):
        if n:
            table[:, k] = data[p]
    with open(path, "wb") as f:
        f.write(header.encode("ascii"))
        f.write(table.tobytes())
    return n


def read_ply(path):
    """{property: (n,) float32} of a PLY written by write_ply (to check it)."""
    with open(path, "rb") as f:
        names, n = [], 0
        while True:
            line = f.readline().decode("ascii").strip()
            if line.startswith("element vertex"):
                n = int(line.split()[-1])
            elif line.startswith("property float"):
                names.append(line.split()[-1])
            elif line == "end_header":
                break
        table = np.frombuffer(f.read(), dtype="<f4").reshape(n, len(names))
    return {name: table[:, k] for k, name in enumerate(names)}


def cloud_splats(points, colours=None, spacing=QUALITY["medium"]):
    """(0.216) A point cloud as splats — straight from its points, no training: thinned to one point a `spacing`
    cell, each a small round gaussian (a scan has no faces: a ball as wide as the spacing) of its point's colour
    (grey without), Y up. {property: (n,) float32}."""
    p = np.asarray(points, dtype=float).reshape(-1, 3)
    if not len(p):
        return {}
    _cells, first = np.unique(np.floor(p / spacing).astype(np.int64), axis=0, return_index=True)
    first.sort()
    if len(first) > MAX_SPLATS:
        raise ValueError("splat_many")
    p = p[first] @ Y_UP.T
    rgb = np.full((len(p), 3), 0.7) if colours is None else np.clip(np.asarray(colours, dtype=float)
                                                                       .reshape(-1, 3)[first], 0.0, 1.0)
    dc = (rgb - 0.5) / SH_C0
    ball = np.full(len(p), np.log(spacing * 0.6))
    zero, one = np.zeros(len(p)), np.ones(len(p))
    out = {"x": p[:, 0], "y": p[:, 1], "z": p[:, 2], "nx": zero, "ny": zero, "nz": zero, "f_dc_0": dc[:, 0],
           "f_dc_1": dc[:, 1], "f_dc_2": dc[:, 2], "opacity": np.full(len(p), np.log(SOLID / (1.0 - SOLID))),
           "scale_0": ball, "scale_1": ball, "scale_2": ball, "rot_0": one, "rot_1": zero, "rot_2": zero, "rot_3": zero}
    return {k: np.ascontiguousarray(v, dtype=np.float32) for k, v in out.items()}


def merged(parts):
    """(0.216) Several sets of splats as one."""
    parts = [p for p in parts if p]
    if not parts:
        return {}
    data = {k: np.concatenate([p[k] for p in parts]) for k in PROPS}
    if len(data["x"]) > MAX_SPLATS:
        raise ValueError("splat_many")
    return data


def export(doc, path, quality="medium", clouds=(), model=True):
    """The model as Gaussian splats in a PLY file, at a quality (QUALITY: how far apart) — and (0.216) the point
    clouds `clouds` [(points (N, 3) in the model, colours (N, 3) 0…1 or None)], as they are; model False: those
    alone. Returns how many."""
    spacing = QUALITY[quality]
    parts = [splats(doc, spacing)] if model else []
    parts += [cloud_splats(points, colours, spacing) for points, colours in clouds]
    return write_ply(path, merged(parts))
