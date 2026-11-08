"""(0.351) 3D from other programs, to bring into the project — SketchUp's SKP, Rhino's 3DM, glTF (GLB or glTF), OBJ and
STL —, read as triangles by material (read), then put in metres with Z up (Model3D.parts_m): made a component (an
IFC type that keeps the shape once, each piece in its material's colour — model/bim.import_model_component) or a
sketch (sketch_mesh: the triangles joined into whole faces, to edit with Push/Pull).

- **SKP** (OpenSKP): every group's and component's faces where they are placed, in their materials (an unpainted face
  its group's material, else its tag's colour, as OpenSKP resolves them); each face's front only — a face painted
  otherwise at the back would else lie twice on itself.
- **3DM** (rhino3dm): the meshes; the surfaces and extrusions by the render meshes Rhino keeps in the file (one saved
  without them is left out and counted); blocks by their transforms, nested too; each object's material (its own or
  its layer's), else its colour (its own or its layer's); the file's unit.
- **glTF / GLB** (metres, Y up), **OBJ** (Y up) and **STL** (Z up), by trimesh: the scene's meshes as placed, each
  material's colour (glTF's base colour, linear in the file; OBJ's from its MTL; STL none). OBJ and STL say no unit:
  guess_unit gives one from the size, for the user to confirm."""

import os
from dataclasses import dataclass, field

import numpy as np

UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001, "in": 0.0254, "ft": 0.3048}
DEFAULT_RGB = (0.82, 0.82, 0.80)            # a face with no colour of its own
KINDS = ("skp", "3dm", "glb", "gltf", "obj", "stl")
RHINO_UNITS = {"Millimeters": 0.001, "Centimeters": 0.01, "Decimeters": 0.1, "Meters": 1.0, "Kilometers": 1000.0,
               "Microns": 1e-6, "Inches": 0.0254, "Feet": 0.3048, "Yards": 0.9144, "Mils": 2.54e-5}
NESTING = 16                                # blocks inside blocks: deeper than this, left out


@dataclass
class Model3D:
    """A 3D file read: its parts {(material name, rgb (sRGB 0–1), alpha): corners (T, 3, 3)} in the file's own unit
    and axes; unit (a key of UNITS) and up ("y" or "z") — said by the file (known) or guessed; skipped: its objects
    with no triangles to read (a 3DM surface saved without its mesh)."""
    name: str
    parts: dict = field(default_factory=dict)
    unit: str = "m"
    up: str = "z"
    known: bool = True
    skipped: int = 0

    def add(self, name, rgb, alpha, corners):
        corners = np.asarray(corners, dtype=float).reshape(-1, 3, 3)
        if not len(corners):
            return
        rgb = tuple(round(min(1.0, max(0.0, float(v))) * 255.0) / 255.0 for v in rgb)
        key = (name or "#{:02x}{:02x}{:02x}".format(*(int(round(v * 255)) for v in rgb)), rgb,
               round(float(alpha), 2))
        self.parts[key] = np.concatenate((self.parts[key], corners)) if key in self.parts else corners

    def triangles(self):
        return sum(len(c) for c in self.parts.values())

    def parts_m(self, unit=None, up=None):
        """The parts in metres, Z up: {key: corners}."""
        scale = UNITS[unit or self.unit]
        y_up = (up or self.up) == "y"
        out = {}
        for key, c in self.parts.items():
            c = c * scale
            out[key] = np.stack((c[..., 0], -c[..., 2], c[..., 1]), axis=-1) if y_up else c
        return out

    def size(self, unit=None, up=None):
        """Its box's (width, depth, height) in metres."""
        parts = list(self.parts_m(unit, up).values())
        if not parts:
            return np.zeros(3)
        pts = np.concatenate([c.reshape(-1, 3) for c in parts])
        return pts.max(axis=0) - pts.min(axis=0)


def guess_unit(size):
    """The unit of a file that says none, from its largest size in its own numbers: millimetres past 400 (a chair in
    metres is about 1, a building some tens), else metres."""
    return "mm" if float(np.max(size)) > 400.0 else "m"


def read(path):
    """A 3D file → Model3D (ValueError: a file this cannot read, or with nothing in it)."""
    kind = os.path.splitext(path)[1].lower().lstrip(".")
    name = os.path.splitext(os.path.basename(path))[0]
    if kind == "skp":
        model = _read_skp(path, name)
    elif kind == "3dm":
        model = _read_3dm(path, name)
    elif kind in ("glb", "gltf", "obj", "stl"):
        model = _read_trimesh(path, name, kind)
    else:
        raise ValueError("kind")
    if not model.parts:
        raise ValueError("empty")
    return model


# ---------------------------------------------------------------------------------------------------- SKP

def _read_skp(path, name):
    import openskp
    try:
        from openskp import _face_groups as sides
    except ImportError:                         # (another OpenSKP: both sides kept)
        sides = None
    original = getattr(sides, "_add_face_side", None)

    def front_only(*args, **kwargs):
        reverse = kwargs.get("reverse", args[6] if len(args) > 6 else False)
        if not reverse:
            original(*args, **kwargs)

    if original is not None:
        sides._add_face_side = front_only
    try:
        scene = openskp.SkpFile(path).build_scene()
    except openskp.SkpParseError as exc:
        raise ValueError(str(exc)) from exc
    finally:
        if original is not None:
            sides._add_face_side = original
    model = Model3D(name, unit="m", up="y")
    for p in scene.glb_primitives:
        pos = np.asarray(p.positions, dtype=float).reshape(-1, 3)
        idx = np.asarray(p.indices, dtype=np.int64).reshape(-1, 3)
        mat = scene.gltf_materials[p.material_index] if 0 <= p.material_index < len(scene.gltf_materials) else {}
        rgba = (mat.get("pbrMetallicRoughness") or {}).get("baseColorFactor") or DEFAULT_RGB + (1.0,)
        model.add(mat.get("name"), rgba[:3], rgba[3] if len(rgba) > 3 else 1.0, pos[idx])
    return model


# ---------------------------------------------------------------------------------------------------- 3DM

def _read_3dm(path, name):
    import rhino3dm as rh
    f = rh.File3dm.Read(path)
    if f is None:
        raise ValueError("3dm")
    unit = str(f.Settings.ModelUnitSystem).split(".")[-1]
    model = Model3D(name, unit="m", up="z")
    scale = RHINO_UNITS.get(unit, 1.0)
    materials, layers = list(f.Materials), list(f.Layers)
    objects = {str(o.Attributes.Id): o for o in f.Objects}
    definitions = {str(d.Id): d for d in f.InstanceDefinitions}

    def look(attr):
        """(name, rgb, alpha) of an object: its material, else its colour."""
        index = attr.MaterialIndex if attr.MaterialSource == rh.ObjectMaterialSource.MaterialFromObject else \
            (layers[attr.LayerIndex].RenderMaterialIndex if 0 <= attr.LayerIndex < len(layers) else -1)
        if 0 <= index < len(materials):
            m = materials[index]
            return m.Name, [v / 255.0 for v in m.DiffuseColor[:3]], 1.0 - float(m.Transparency)
        colour = attr.ObjectColor if attr.ColorSource == rh.ObjectColorSource.ColorFromObject else \
            (layers[attr.LayerIndex].Color if 0 <= attr.LayerIndex < len(layers) else None)
        if colour is None or tuple(colour[:3]) == (0, 0, 0):      # (black: Rhino's default layer, not a colour)
            return "", DEFAULT_RGB, 1.0
        return "", [v / 255.0 for v in colour[:3]], 1.0

    def meshes(geometry):
        if isinstance(geometry, rh.Mesh):
            return [geometry]
        if isinstance(geometry, rh.Brep):
            return [face.GetMesh(rh.MeshType.Render) for face in geometry.Faces]
        if isinstance(geometry, rh.Extrusion):
            return [geometry.GetMesh(rh.MeshType.Render)]
        return None

    def triangles(mesh, matrix):
        v = np.array([(p.X, p.Y, p.Z) for p in mesh.Vertices], dtype=float).reshape(-1, 3)
        q = np.array([mesh.Faces[i] for i in range(len(mesh.Faces))], dtype=np.int64).reshape(-1, 4)
        if not len(v) or not len(q):
            return np.zeros((0, 3, 3))
        quads = q[:, 2] != q[:, 3]
        tris = np.concatenate((q[:, :3], q[quads][:, [0, 2, 3]]))
        v = v @ matrix[:3, :3].T + matrix[:3, 3]
        return v[tris]

    def take(obj, matrix, depth):
        geometry = obj.Geometry
        if isinstance(geometry, rh.InstanceReference):
            d = definitions.get(str(geometry.ParentIdefId))
            if d is None or depth >= NESTING:
                model.skipped += 1
                return
            x = geometry.Xform
            m = matrix @ np.array([[getattr(x, "M{}{}".format(i, j)) for j in range(4)] for i in range(4)])
            for oid in d.GetObjectIds():
                inner = objects.get(str(oid))
                if inner is not None:
                    take(inner, m, depth + 1)
            return
        found = meshes(geometry)
        if found is None:                       # (curves, points, texts…: nothing to bring)
            return
        found = [m for m in found if m is not None]
        if not found:
            model.skipped += 1
            return
        mat_name, rgb, alpha = look(obj.Attributes)
        model.add(mat_name, rgb, alpha, np.concatenate([triangles(m, matrix) for m in found]))

    top = np.diag((scale, scale, scale, 1.0))
    for obj in f.Objects:
        if not obj.Attributes.IsInstanceDefinitionObject and obj.Attributes.Visible:
            take(obj, top, 0)
    return model


# ---------------------------------------------------------------------------------------------------- glTF, OBJ, STL

def _srgb(linear):
    c = np.clip(np.asarray(linear, dtype=float), 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1.0 / 2.4) - 0.055)


def _texture_colours(path):
    """(0.467) A glTF's materials painted by a picture (its base colour texture, a file beside it): {material name:
    the picture's average colour (sRGB 0–1) times the material's factor} — what a component of one colour a piece can
    keep of it. {} when there is none (or no way to read pictures)."""
    import json
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        from PySide6 import QtCore, QtGui
    except (OSError, ValueError, ImportError):
        return {}
    images, textures = data.get("images") or [], data.get("textures") or []
    out = {}
    for material in data.get("materials") or ():
        pbr = material.get("pbrMetallicRoughness") or {}
        texture = (pbr.get("baseColorTexture") or {}).get("index")
        if texture is None or not 0 <= texture < len(textures):
            continue
        source = textures[texture].get("source")
        uri = images[source].get("uri") if source is not None and 0 <= source < len(images) else None
        if not uri or uri.startswith("data:"):
            continue
        from urllib.parse import unquote
        picture = QtGui.QImage(os.path.join(os.path.dirname(path), unquote(uri)))
        if picture.isNull():
            continue
        small = picture.scaled(32, 32, QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
                               QtCore.Qt.TransformationMode.SmoothTransformation)
        small = small.convertToFormat(QtGui.QImage.Format.Format_RGB888)
        pixels = np.frombuffer(bytes(small.constBits()), dtype=np.uint8)[:32 * 32 * 3]
        if small.bytesPerLine() != 32 * 3:                     # (rows padded: read them one by one)
            raw = np.frombuffer(bytes(small.constBits()), dtype=np.uint8)
            pixels = np.concatenate([raw[r * small.bytesPerLine():r * small.bytesPerLine() + 96] for r in range(32)])
        rgb = pixels.reshape(-1, 3).mean(axis=0) / 255.0
        factor = pbr.get("baseColorFactor") or (1.0, 1.0, 1.0, 1.0)
        out[material.get("name") or ""] = np.clip(rgb * _srgb(np.asarray(factor[:3], dtype=float)), 0.0, 1.0)
    return out


def _read_trimesh(path, name, kind):
    import trimesh
    try:
        scene = trimesh.load(path, force="scene", process=False)
    except Exception as exc:                  # (trimesh raises many kinds for a file it cannot read)
        raise ValueError(str(exc)) from exc
    gltf = kind in ("glb", "gltf")
    model = Model3D(name, unit="m", up="z" if kind == "stl" else "y", known=gltf)
    pictured = _texture_colours(path) if kind == "gltf" else {}
    for mesh in scene.dump():
        corners = np.asarray(mesh.triangles, dtype=float)
        if not len(corners):
            continue
        visual = mesh.visual
        material = getattr(visual, "material", None)
        if material is not None and pictured.get(getattr(material, "name", "") or "") is not None:
            # (0.467) a material painted by a picture (a Poly Haven model's): the picture's own colour, on average
            model.add(material.name, pictured[material.name], 1.0, corners)
        elif material is not None:
            factor = getattr(material, "baseColorFactor", None)
            if factor is not None and getattr(material, "baseColorTexture", None) is None:
                rgba = np.asarray(factor, dtype=float) / 255.0
                rgb = _srgb(rgba[:3]) if gltf else rgba[:3]
            else:
                rgba = np.asarray(material.main_color, dtype=float) / 255.0
                rgb = rgba[:3]
            model.add(getattr(material, "name", "") or "", rgb, rgba[3] if len(rgba) > 3 else 1.0, corners)
        elif getattr(visual, "kind", None) == "face":         # (a colour a triangle: grouped by colour)
            colours = np.asarray(visual.face_colors, dtype=np.int64)
            keys, which = np.unique(colours, axis=0, return_inverse=True)
            for k, rgba in enumerate(keys):
                model.add("", rgba[:3] / 255.0, rgba[3] / 255.0, corners[which.reshape(-1) == k])
        else:
            model.add("", DEFAULT_RGB, 1.0, corners)
    if not gltf:
        model.unit = guess_unit(model.size("m", model.up))
    return model


# ---------------------------------------------------------------------------------------------------- sketch

def sketch_mesh(parts):
    """The parts (in metres, Z up) as one sketch: (PolyMesh in its own frame, its origin — the lowest corner): the
    triangles joined into whole faces (model/cad3d_export.planar_faces); a face with holes, which a sketch face cannot
    have, by its triangles, the lines between them hidden."""
    from ..core.mesh import PolyMesh, edge_key
    from .cad3d_export import planar_faces
    corners = np.concatenate([c.reshape(-1, 3, 3) for c in parts.values() if len(c)])
    origin = corners.reshape(-1, 3).min(axis=0)
    points, faces = planar_faces(corners - origin, triangles=True)
    out, hidden = [], set()
    for outer, holes, tris in faces:
        if not holes:
            out.append(outer)
            continue
        ring = {edge_key(*side) for loop in [outer] + holes for side in zip(loop, loop[1:] + loop[:1])}
        for tri in tris:
            out.append(tri)
            hidden |= {edge_key(*side) for side in zip(tri, tri[1:] + tri[:1])} - ring
    return PolyMesh(points, out, hidden=hidden), origin
