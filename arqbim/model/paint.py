"""(0.391) Paint, as SketchUp's Paint Bucket (and the ArqSynth Modeler's «Pintura»): a material laid on a face of an
element — its colour in the views, on paper and in the render —, or on all its faces, without changing what it is
made of (its type, its layers). Kept on the element (ArqSynth_Parametros «Pintura»: JSON [[nx, ny, nz, d, key]…]
— each painted face's plane in the element's own coordinates, so that moving it or turning it carries its paint;
["*", key]: all its faces); the triangles of its mesh lying in a painted plane take the material's colour. The
last one given wins. None = «Sem pintura» (SketchUp's Default material): the face back to its own."""

import json

import numpy as np

from ..ifc import catalog

PARAM = "Pintura"
ALL = "*"
ON_PLANE = 0.003                    # m: a triangle this near a painted plane (and facing its way) is on that face
FACING = 0.999


def _raw(ifc, guid):
    from ..ifc.edit import _MISSING, _own_param
    try:
        e = ifc.by_guid(guid)
    except (AttributeError, RuntimeError):         # (a file still being read: its IFC not there yet)
        return ""
    if e is None:
        return ""
    value = _own_param(e, PARAM)
    return "" if value is _MISSING or not value else str(value)


def entries(ifc, guid):
    """The element's paint as kept: [[nx, ny, nz, d, key]] (its own coordinates) or [["*", key]]."""
    raw = _raw(ifc, guid)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except ValueError:
        return []
    return [d for d in data if isinstance(d, list) and d and (d[0] == ALL and len(d) == 2 or len(d) == 5)]


def signature(ifc, guid):
    """Something that changes when its paint does (for the views' caches)."""
    return _raw(ifc, guid) if ifc is not None else ""


def world_planes(ifc, guid):
    """[(normal (3,) or None for all, d, material key)] the painted planes in the world (program coordinates)."""
    data = entries(ifc, guid)
    if not data:
        return []
    m = ifc._placement_si(ifc.by_guid(guid))
    r, t = m[:3, :3], m[:3, 3]
    out = []
    for d in data:
        if d[0] == ALL:
            out.append((None, 0.0, d[1]))
            continue
        n_local = np.asarray(d[:3], dtype=float)
        n = r @ n_local
        n /= max(np.linalg.norm(n), 1e-12)
        point = r @ (n_local * float(d[3])) + t
        out.append((n, float(n @ point), d[4]))
    return out


def colour(key):
    """A material's colour (sRGB 0–1), or None (not a material)."""
    spec = catalog.MATERIALS.get(key) if key else None
    return None if spec is None else np.asarray(spec.color, dtype=float)[:3]


def painted(planes, corners, normals):
    """(T,) each triangle's paint (its material key, "" none): corners (T, 3, 3), normals (T, 3), world."""
    keys = np.full(len(corners), "", dtype=object)
    if not planes or not len(corners):
        return keys
    centres = np.asarray(corners, dtype=float).mean(axis=1)
    normals = np.asarray(normals, dtype=float)
    for n, d, key in planes:
        if n is None:
            keys[:] = key or ""
            continue
        on = (normals @ n > FACING) & (np.abs(centres @ n - d) < ON_PLANE)
        keys[on] = key or ""
    return keys


def to_local(ifc, guid, normal, point):
    """A world plane (its normal, a point on it) in the element's own coordinates: (n (3,), d)."""
    m = ifc._placement_si(ifc.by_guid(guid))
    r, t = m[:3, :3], m[:3, 3]
    n = r.T @ np.asarray(normal, dtype=float)
    n /= max(np.linalg.norm(n), 1e-12)
    p = r.T @ (np.asarray(point, dtype=float) - t)
    return n, float(n @ p)


def with_face(data, n, d, key):
    """The paint with one face's changed: that plane's old paint taken off, the new laid on (key None: none)."""
    out = [e for e in data if e[0] == ALL or not (np.dot(np.asarray(e[:3], dtype=float), n) > FACING and
                                                     abs(float(e[3]) - d) < ON_PLANE)]
    if key:
        out.append([round(float(c), 6) for c in n] + [round(d, 6), key])
    return out


def with_all(key):
    """All its faces one material (None: no paint at all)."""
    return [[ALL, key]] if key else []


def text(data):
    return json.dumps(data) if data else ""


def material_at(ifc, obj, face, normal, point):
    """The material seen on a face of an element (the eyedropper): its paint there, else its own material on that
    face (a layered wall's: the layer it shows), else None."""
    planes = world_planes(ifc, obj.id)
    if planes:
        keys = painted(planes, np.asarray(point, dtype=float).reshape(1, 1, 3).repeat(3, axis=1),
                       np.asarray(normal, dtype=float).reshape(1, 3))
        if keys[0]:
            return keys[0]
    from . import material_looks
    try:
        seen = material_looks.look(ifc, obj, (0.8, 0.8, 0.8), True, False, False)
    except (AttributeError, RuntimeError, ValueError):
        return None
    if seen.materials is None or not len(seen.faces):
        return None
    rows = np.flatnonzero(np.asarray(seen.faces) == face)
    if not len(rows):
        return None
    if len(rows) > 1:                         # (cut along its layers: the piece nearest the point)
        centres = seen.corners[rows].mean(axis=1)
        rows = rows[[int(np.argmin(np.linalg.norm(centres - np.asarray(point, dtype=float), axis=1)))]]
    key = seen.materials[rows[0]]
    return key or None


# ---------------------------------------------------------------- (0.392) the sketches' faces

def sketch_face(mesh, fi):
    """The faces a click on face `fi` of a sketch paints: the face as SketchUp shows it — its polygons joined across
    hidden edges (a circle drawn on a face, an offset's frame)."""
    from ..core import sketch_geometry as sg
    return sorted(sg.surface_faces(mesh, fi))


def sketch_connected(mesh, fi):
    """SketchUp's Ctrl + click: the faces joined to `fi` by an edge that have the same paint as it (none too)."""
    paint = mesh.painted()
    same = paint[fi] if fi < len(paint) else None
    by_edge = {}
    for _e, fis in mesh.edge_faces().items():
        for g in fis:
            by_edge.setdefault(g, set()).update(fis)
    seen, todo = {fi}, [fi]
    while todo:
        for g in by_edge.get(todo.pop(), ()):
            if g not in seen and (paint[g] if g < len(paint) else None) == same:
                seen.add(g)
                todo.append(g)
    return sorted(seen)


def paint_sketch(doc, changes, label=None):
    """Sketch faces painted — changes: [(sketch, [face indices], key or None)] —, one undo step."""
    from ..i18n import t
    from .document import ReplaceMeshes
    out = []
    for obj, faces, key in changes:
        new = obj.mesh.copy()
        paint = new.painted()
        for g in faces:
            if 0 <= g < len(paint):
                paint[g] = key or None
        if paint != obj.mesh.painted():
            out.append((obj.id, obj.mesh, new))
    if out:
        doc.execute(ReplaceMeshes(out, label or t("cmd.paint")))
    return len(out)


def replace_in_sketches(doc, old, new):
    """[(sketch, faces, new)] of the sketches' faces painted `old` (SketchUp's Shift + click)."""
    found = []
    for obj in doc.sketches():
        faces = [g for g, p in enumerate(obj.mesh.painted()) if p == old]
        if faces:
            found.append((obj, faces, new))
    return found


def area_by_material(ifc, obj):
    """{material key: m²} of an element's painted faces (its mesh's triangles lying in them)."""
    planes = world_planes(ifc, obj.id)
    if not planes:
        return {}
    mesh = obj.mesh
    tris, _owner = mesh.triangulate()
    verts = np.asarray(mesh.verts, dtype=float).reshape(-1, 3)
    corners = verts[tris]
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    areas = np.linalg.norm(normals, axis=1) / 2.0
    normals = normals / np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    keys = painted(planes, corners, normals)
    out = {}
    for key in set(keys) - {""}:
        out[key] = float(areas[keys == key].sum())
    return out
