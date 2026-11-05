"""(0.350) The model in Rhino's 3DM and in SketchUp's SKP — besides the GLB, OBJ and STL — from the same gathering
(model/gltf_export.gather: each element's faces by material):

- **3DM** (rhino3dm, McNeel's openNURBS): each element a mesh per material, named after it, on its category's layer
  inside its storey's («Térreo::Paredes», the category's colour), grouped when it has several materials; its data —
  GlobalId, IFC class, type, storey, category — as the object's user text (Rhino's Properties ▸ Attribute User Text);
  the materials named, with their colour, transparency and finish (shine, reflectivity), the objects shown in them.
  Flat faces (a vertex shared only within a plane), metres, Z up, at the model's own coordinates (Rhino keeps
  doubles). Version 6 of the format, which Rhino 6, 7 and 8 open.
- **SKP** (OpenSKP: the format of SketchUp 2013–2020, which every SketchUp opens): each element a group named after
  it, tagged with its storey and its category («Térreo - Paredes»: that format has no tag folders), its faces whole —
  the triangles in one plane and touching joined into one face with its holes, so SketchUp draws the edges an
  architect would and not the triangulation —, each its material on both sides; the element's data in the group's
  attribute dictionary «ArqSynth». Inches inside (SketchUp's), Z up, at the model's own coordinates."""

import numpy as np

from . import material_looks
from .gltf_export import FINISH_PBR, SKETCH_RGB

INCH = 1.0 / 0.0254                     # metres → inches
WELD = 1e-6                             # m: two corners closer than this one vertex
NORMAL_STEP = 1e-5                      # two triangles one plane: their normals and their distances from the origin
PLANE_STEP = 1e-6                       # (m) equal to these steps
COLLINEAR = 1e-9                        # a loop's point on the straight line of its neighbours (sine of the angle)
DICT = "ArqSynth"                       # the SKP groups' attribute dictionary
RHINO_VERSION = 6


def _byte(rgb, alpha=1.0):
    return tuple(int(round(min(1.0, max(0.0, float(v))) * 255)) for v in (*rgb, alpha))


def _unique_names(materials):
    """Each material key its name, two of one name told apart."""
    names, used = {}, set()
    for k, m in materials.items():
        name = str(m["name"]) or "material"
        n = 2
        while name in used:
            name = "{} ({})".format(m["name"], n)
            n += 1
        used.add(name)
        names[k] = name
    return names


def _layer_of(e):
    return e["storey"], (None if e["category"] == e["storey"] else e["category"])


def _category_rgb(e):
    cls = e["extras"].get("ifcClass")
    return material_looks.category_rgb(cls) if cls else SKETCH_RGB


# ---------------------------------------------------------------------------------------------------- flat faces

def _welded(corners):
    """Corners (T, 3, 3) → (points (V, 3), the triangles' vertices (T, 3)): one point for corners closer than WELD
    (the first one's, so that faces sharing a vertex share it exactly)."""
    pts = corners.reshape(-1, 3)
    _u, first, vid = np.unique(np.round(pts / WELD), axis=0, return_index=True, return_inverse=True)
    return pts[first], vid.reshape(-1, 3)


def _sub(a, b):
    return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


def _loops(sides):
    """Directed sides [(u, v)] → their closed loops of vertices, or None when they cannot be told apart (a vertex
    starting two sides: two corners on one point)."""
    nxt = {}
    for u, v in sides:
        if u in nxt:
            return None
        nxt[u] = v
    loops = []
    while nxt:
        start = next(iter(nxt))
        loop, v = [], start
        while v in nxt:
            loop.append(v)
            v = nxt.pop(v)
        if v != start or len(loop) < 3:
            return None
        loops.append(loop)
    return loops


def _clean(loop, pts):
    """A loop without its points on the straight line of their neighbours; None when it turns back on itself
    somewhere (two of its sides along one line: a slit)."""
    out, n = [], len(loop)
    for i, v in enumerate(loop):
        p = pts[v]
        a, b = _sub(pts[loop[i - 1]], p), _sub(pts[loop[(i + 1) % n]], p)
        c = _cross(a, b)
        if _dot(c, c) <= COLLINEAR * COLLINEAR * _dot(a, a) * _dot(b, b):
            if _dot(a, b) > 0:
                return None
            continue
        out.append(v)
    return out if len(out) >= 3 else None


def _area(loop, pts, normal):
    sx = sy = sz = 0.0
    for i, v in enumerate(loop):
        c = _cross(pts[loop[i - 1]], pts[v])
        sx, sy, sz = sx + c[0], sy + c[1], sz + c[2]
    return 0.5 * (sx * normal[0] + sy * normal[1] + sz * normal[2])


def _face(sides, normal, pts):
    """A face's directed outline sides → (outer loop, [holes]), or None when they make no one face."""
    loops = _loops(sides)
    if loops is None:
        return None
    loops = [_clean(loop, pts) for loop in loops]
    if any(loop is None for loop in loops):
        return None
    areas = [_area(loop, pts, normal) for loop in loops]
    outer = max(range(len(loops)), key=areas.__getitem__)
    if areas[outer] <= 0 or any(a >= 0 for i, a in enumerate(areas) if i != outer):
        return None
    return loops[outer], [loop for i, loop in enumerate(loops) if i != outer]


def _untangled(sides, pts):
    """The outline's sides with their T-junctions undone — a triangle's side along two of its neighbours', a vertex
    between them: each side split where a vertex of the outline lies on it, then the pieces met by their reverse
    (inside the face) dropped."""
    verts = sorted({u for side in sides for u in side})
    p = np.array([pts[v] for v in verts])
    pieces = {}
    for u, v in sides:
        a, d = np.array(pts[u]), np.subtract(pts[v], pts[u])
        s = (p - a) @ d / float(d @ d)
        off = np.linalg.norm(p - a - np.outer(s, d), axis=1)
        on = np.flatnonzero((s > 1e-9) & (s < 1.0 - 1e-9) & (off < 10.0 * WELD))
        chain = [u] + [verts[i] for i in on[np.argsort(s[on])]] + [v]
        for piece in zip(chain[:-1], chain[1:]):
            pieces[piece] = pieces.get(piece, 0) + 1
    out = []
    for (u, v), k in pieces.items():
        out.extend([(u, v)] * (k - pieces.get((v, u), 0)))
    return out


def _join(tris, normal, pts):
    """The triangles of one plane (their vertices, [(a, b, c)]) → [(outer loop, [holes], its triangles)]: those touching
    along their sides one face, its loops of vertices in order (the outer one counter-clockwise seen from the front,
    as the triangles); where they make no one face (two corners on one point), its triangles alone."""
    if len(tris) == 1:
        return [(list(tris[0]), [], [list(tris[0])])]
    sides = {}
    for t, (a, b, c) in enumerate(tris):
        for u, v in ((a, b), (b, c), (c, a)):
            sides.setdefault((u, v) if u < v else (v, u), []).append(t)
    if any(len(ts) > 2 for ts in sides.values()):
        return [(list(tri), [], [list(tri)]) for tri in tris]
    parent = list(range(len(tris)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for ts in sides.values():
        if len(ts) == 2:
            parent[root(ts[0])] = root(ts[1])
    pieces = {}
    for t in range(len(tris)):
        pieces.setdefault(root(t), []).append(t)
    out = []
    for members in pieces.values():
        outline = [(u, v) for t in members for u, v in ((tris[t][0], tris[t][1]), (tris[t][1], tris[t][2]),
                                                       (tris[t][2], tris[t][0]))
                   if len(sides[(u, v) if u < v else (v, u)]) == 1]
        face = _face(outline, normal, pts)
        if face is None:
            face = _face(_untangled(outline, pts), normal, pts)
        if face is None:
            out.extend((list(tris[t]), [], [list(tris[t])]) for t in members)
        else:
            out.append(face + ([list(tris[t]) for t in members],))
    return out


def planar_faces(corners, welded=None, triangles=False):
    """Triangles (T, 3, 3) joined into flat faces: (points (V, 3), [(outer loop, [hole loops])]), each loop the
    indices of its points in order — the triangles in one plane and touching along their sides one face. welded:
    (points, the triangles' vertices) when they are already (an element's, shared by its materials' faces).
    triangles (0.351): each face (outer, holes, its triangles' vertices) — a face with holes drawn as they are."""
    c = np.asarray(corners, dtype=float).reshape(-1, 3, 3)
    points, vid = welded if welded is not None else _welded(c)
    n = np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0])
    length = np.linalg.norm(n, axis=1)
    keep = (length > 1e-12) & (vid[:, 0] != vid[:, 1]) & (vid[:, 1] != vid[:, 2]) & (vid[:, 2] != vid[:, 0])
    n, vid, c = n[keep] / length[keep][:, None], vid[keep], c[keep]
    if not len(c):
        return points, []
    d = np.einsum("ij,ij->i", n, c[:, 0])
    _u, plane = np.unique(np.column_stack((np.round(n / NORMAL_STEP), np.round(d / PLANE_STEP))), axis=0,
                          return_inverse=True)
    plane = plane.reshape(-1)
    order = np.argsort(plane, kind="stable")
    pts = points.tolist()
    faces = []
    for group in np.split(order, np.flatnonzero(np.diff(plane[order])) + 1):
        faces.extend(_join(vid[group].tolist(), n[group[0]].tolist(), pts))
    return points, (faces if triangles else [f[:2] for f in faces])


# ---------------------------------------------------------------------------------------------------- 3DM

def write_3dm(path, elements, materials):
    """A Rhino 3DM file: (elements, triangles)."""
    import rhino3dm as rh
    if not any(len(c) for e in elements for c in e["parts"].values()):
        raise ValueError("empty")
    f = rh.File3dm()
    f.Settings.ModelUnitSystem = rh.UnitSystem.Meters
    f.Settings.ModelAbsoluteTolerance = 0.001
    names = _unique_names(materials)
    mindex = {}
    for k, m in materials.items():
        mat = rh.Material()
        mat.Name = names[k]
        mat.DiffuseColor = _byte(m["rgb"])
        mat.Transparency = 1.0 - float(m["alpha"])
        metal, rough = FINISH_PBR.get(m["finish"], FINISH_PBR["matte"])
        mat.Shine = (1.0 - rough) * 255.0                   # (openNURBS' MaxShine)
        mat.Reflectivity = 0.6 * metal + (0.1 if m["finish"] == "glass" else 0.0)
        mindex[k] = f.Materials.Add(mat)
    layers = {}

    def layer(name, parent=None, rgb=None):
        key = (parent, name)
        if key not in layers:
            lay = rh.Layer()
            lay.Name = str(name)
            if parent is not None:
                lay.ParentLayerId = f.Layers[layers[(None, parent)]].Id
            if rgb is not None:
                lay.Color = _byte(rgb)
            layers[key] = f.Layers.Add(lay)
        return layers[key]

    count = triangles = 0
    for e in elements:
        parts = [(k, np.asarray(c, dtype=float).reshape(-1, 3, 3)) for k, c in e["parts"].items() if len(c)]
        if not parts:
            continue
        storey, category = _layer_of(e)
        at = layer(storey, rgb=None if category else _category_rgb(e))
        if category:
            at = layer(category, storey, _category_rgb(e))
        group = None
        if len(parts) > 1:
            g = rh.Group()
            g.Name = str(e["name"])
            f.Groups.Add(g)
            group = f.Groups[len(f.Groups) - 1].Index
        for k, c in parts:
            n = np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0])
            length = np.linalg.norm(n, axis=1)
            c, n = c[length > 1e-12], n[length > 1e-12] / length[length > 1e-12][:, None]
            if not len(c):
                continue
            key = np.column_stack((np.round(c.reshape(-1, 3) / WELD), np.round(np.repeat(n, 3, axis=0) / 1e-4)))
            _u, first, vid = np.unique(key, axis=0, return_index=True, return_inverse=True)
            mesh = rh.Mesh()
            for p in c.reshape(-1, 3)[first].tolist():
                mesh.Vertices.Add(*p)
            for a, b, d in vid.reshape(-1, 3).tolist():
                mesh.Faces.AddFace(a, b, d)
            mesh.Normals.ComputeNormals()
            mesh.Compact()
            attr = rh.ObjectAttributes()
            attr.Name = str(e["name"])
            attr.LayerIndex = at
            attr.MaterialIndex = mindex[k]
            attr.MaterialSource = rh.ObjectMaterialSource.MaterialFromObject
            attr.ColorSource = rh.ObjectColorSource.ColorFromMaterial
            for name, value in e["extras"].items():
                attr.SetUserString(str(name), str(value))
            if group is not None:
                attr.AddToGroup(group)
            f.Objects.AddMesh(mesh, attr)
            triangles += len(c)
        count += 1
    if not f.Write(path, RHINO_VERSION):
        raise OSError(path)
    return count, triangles


# ---------------------------------------------------------------------------------------------------- SKP

def write_skp(path, elements, materials):
    """A SketchUp SKP file: (elements, triangles)."""
    import openskp
    if not any(len(c) for e in elements for c in e["parts"].values()):
        raise ValueError("empty")
    b = openskp.create()
    names = _unique_names(materials)
    handles = {k: b.add_material(names[k], _byte(m["rgb"])[:3], float(m["alpha"]) if m["alpha"] < 1.0 else None)
               for k, m in materials.items()}
    tags, tag_of = {}, []
    for e in elements:
        storey, category = _layer_of(e)
        name = "{} - {}".format(storey, category) if category else str(storey)
        if name not in tags:
            tags[name] = b.add_layer(name, _byte(_category_rgb(e))[:3])
        tag_of.append(tags[name])
    count = triangles = 0
    for e, tag in zip(elements, tag_of):
        parts = [(k, np.asarray(c, dtype=float).reshape(-1, 3, 3)) for k, c in e["parts"].items() if len(c)]
        if not parts:
            continue
        points, at = _welded(np.concatenate([c for _k, c in parts]))
        inches = [tuple(p) for p in (points * INCH).tolist()]
        extras = {str(k): (v if isinstance(v, (int, float)) else str(v)) for k, v in e["extras"].items()}
        with b.add_group(str(e["name"]), layer=tag, attribute_dict_name=DICT, attributes=extras) as g:
            start = 0
            for k, c in parts:
                mine = at[start:start + len(c)]
                start += len(c)
                _p, faces = planar_faces(c, (points, mine))
                for outer, holes in faces:
                    try:
                        g.add_face([inches[v] for v in outer], material=handles[k], back_material=handles[k],
                                   holes=[[inches[v] for v in h] for h in holes])
                    except openskp.SkpWriteError:              # (not flat enough for SketchUp: its triangles)
                        g.add_face([inches[v] for v in outer], material=handles[k], back_material=handles[k],
                                   auto_triangulate=True)
                triangles += len(c)
        count += 1
    b.save(path)
    return count, triangles
