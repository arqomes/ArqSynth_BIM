"""(0.348) The model in glTF 2.0 binary (GLB) — the 3D format of the ArqSynth Presentation, the web viewers, Blender,
Twinmotion, SketchUp…: the objects asked for (those shown, the whole model, the selection), each element a node of
its own under its storey's and its category's (Storey ▸ Category ▸ element, named as the program shows them — what
the Presentation lists as its layers and folders), its faces by material: each glTF material its colour, its
transparency and its finish in the realistic render (PBR metallic-roughness: matte, satin, glossy, metal, glass,
frosted), named after the material (else its colour). Flat faces: each triangle its own three corners and its
normal. Each element's data in its node's extras — its GlobalId, IFC class, type, storey —, for whoever reads them.
Y up (glTF's) in metres; the model moved near the origin (a model far from it, in a survey's coordinates, would lose
its millimetres in single floats): the offset in the scene's extras. Pure NumPy and json."""

import json
import struct

import ifcopenshell.util.element
import numpy as np

from ..i18n import has, t
from . import material_looks
from .render_scene import finish_of

SKIP = ("IfcOpeningElement", "IfcSpace", "IfcVirtualElement", "IfcAnnotation", "IfcGrid")
# a finish -> (metallic, roughness) of glTF's PBR, as the realistic render's (render/path_tracer.SURFACES)
FINISH_PBR = {"matte": (0.0, 0.85), "satin": (0.0, 0.45), "glossy": (0.0, 0.15), "metal": (1.0, 0.30),
              "glass": (0.0, 0.05), "frosted": (0.0, 0.35), "water": (0.0, 0.05)}
SKETCH_RGB = (0.92, 0.91, 0.87)
GLB_MAGIC, GLB_JSON, GLB_BIN = 0x46546C67, 0x4E4F534A, 0x004E4942
ARRAY_BUFFER = 34962
FLOAT = 5126


def _linear(rgb):
    c = np.clip(np.asarray(rgb, dtype=float), 0.0, 1.0)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _y_up(points):
    """(x, y, z) of the model (Z up) → glTF's (x, z, −y)."""
    p = np.asarray(points, dtype=float).reshape(-1, 3)
    return np.column_stack((p[:, 0], p[:, 2], -p[:, 1]))


def _category(ifc_class):
    key = "tree.cat." + str(ifc_class)
    return t(key) if has(key) else str(ifc_class)


@material_looks.one_pass()                      # (0.352: each wall's layers read once)
def gather(doc, objects):
    """What goes into the file: ([element], {material key: material}) — each element {name, storey, category,
    extras, parts: {material key: corners (T, 3, 3) in the model's metres}}; each material {name, rgb (sRGB),
    alpha, finish}."""
    from ..ifc import catalog
    ifc = getattr(doc, "ifc", None)
    storeys = {g: n for g, n, _z in doc.storeys()} if hasattr(doc, "storeys") else {}
    materials, out = {}, []
    sketches = t("gltf.sketches")
    for obj in objects:
        if obj is None or getattr(obj, "mesh", None) is None or getattr(obj, "ifc_class", None) in SKIP:
            continue
        parts = {}
        if getattr(obj, "is_bim", False):
            try:
                seen = material_looks.look(ifc, obj, material_looks.category_rgb(obj.ifc_class), colours=True,
                                           patterns=False, clear=True)
            except (AttributeError, RuntimeError, ValueError, TypeError):
                continue
            corners = np.asarray(seen.corners, dtype=float)
            if not len(corners):
                continue
            none = np.full(len(corners), "", dtype=object)
            cats = seen.categories if seen.categories is not None else none
            own = seen.finishes if seen.finishes is not None else none
            keys = seen.materials if seen.materials is not None else none
            rgb = np.round(np.clip(np.asarray(seen.rgb, dtype=float), 0.0, 1.0) * 255.0) / 255.0
            alpha = np.round(np.asarray(seen.alpha, dtype=float), 2)
            codes, index = {}, []
            for c, a, r, o, k in zip(cats, alpha, rgb, own, keys):
                finish = finish_of(c, a, o)
                mkey = (str(k), tuple(r), float(a), finish)
                if mkey not in materials:
                    spec = catalog.MATERIALS.get(k) if k else None
                    name = (spec.name_pt if spec is not None else "") or \
                        "#{:02x}{:02x}{:02x}".format(*(int(round(v * 255)) for v in r))
                    materials[mkey] = {"name": name, "rgb": tuple(r), "alpha": float(a), "finish": finish}
                index.append(codes.setdefault(mkey, len(codes)))
            index = np.asarray(index)
            for mkey, n in codes.items():
                parts[mkey] = corners[index == n]
            e = ifc.by_guid(obj.id) if ifc is not None else None
            type_ = ifcopenshell.util.element.get_type(e) if e is not None else None
            storey = storeys.get(getattr(obj, "storey", None)) or t("gltf.no_storey")
            category = _category(obj.ifc_class)
            extras = {"GlobalId": obj.id, "ifcClass": obj.ifc_class, "type": (type_.Name or "") if type_ else "",
                      "storey": storey, "category": category}
        else:
            tris, _owner = obj.mesh.triangulate()
            if not len(tris):
                continue
            verts = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
            m = np.asarray(getattr(obj, "matrix", np.eye(4)), dtype=float)
            world = verts @ m[:3, :3].T + m[:3, 3]
            mkey = ("", SKETCH_RGB, 1.0, "matte")
            materials.setdefault(mkey, {"name": t("gltf.sketch_material"), "rgb": SKETCH_RGB, "alpha": 1.0,
                                        "finish": "matte"})
            parts[mkey] = world[np.asarray(tris)]
            storey, category, extras = sketches, sketches, {"category": sketches}
        out.append({"name": getattr(obj, "name", "") or obj.id, "storey": storey, "category": category,
                    "extras": extras, "parts": parts})
    return out, materials


def build(elements, materials, name="ArqSynth BIM", generator="ArqSynth BIM"):
    """(the glTF JSON as a dict, the binary buffer as bytes) of these elements and materials (gather's). (0.483) An
    element given a «clear_name» (the Presentation's export) has its see-through parts (glass, water) in a child node of
    that name — a viewer that sorts a part by its own material (the Presentation's layers: glass is «Window») finds it
    by name, as one of the element's."""
    pts = [c.reshape(-1, 3) for e in elements for c in e["parts"].values() if len(c)]
    if not pts:
        raise ValueError("empty")
    every = np.concatenate(pts)
    lo, hi = every.min(axis=0), every.max(axis=0)
    offset = np.array(((lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, lo[2]))
    order = list(materials)
    mat_index = {k: n for n, k in enumerate(order)}
    gl_materials = []
    for k in order:
        m = materials[k]
        metallic, rough = FINISH_PBR.get(m["finish"], FINISH_PBR["matte"])
        base = list(map(float, _linear(m["rgb"]))) + [float(m["alpha"])]
        entry = {"name": m["name"], "pbrMetallicRoughness": {"baseColorFactor": base, "metallicFactor": metallic,
                                                             "roughnessFactor": rough},
                 "doubleSided": True, "extras": {"finish": m["finish"]}}
        if m["alpha"] < 0.999:
            entry["alphaMode"] = "BLEND"
        gl_materials.append(entry)
    positions, normals, accessors, meshes, nodes = [], [], [], [], []
    count_p = 0
    tree = {}                                           # storey -> category -> [node index]
    for e in elements:
        prims, clear = [], []
        for k, corners in e["parts"].items():
            if not len(corners):
                continue
            c = corners.reshape(-1, 3, 3) - offset
            n = np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0])
            length = np.linalg.norm(n, axis=1)
            keep = length > 1e-12
            if not keep.any():
                continue
            c, n = c[keep], n[keep] / length[keep][:, None]
            p = _y_up(c.reshape(-1, 3)).astype(np.float32)
            nn = _y_up(np.repeat(n, 3, axis=0)).astype(np.float32)
            base = count_p
            positions.append(p)
            normals.append(nn)
            count_p += len(p)
            accessors.append({"bufferView": 0, "byteOffset": base * 12, "componentType": FLOAT, "count": len(p),
                              "type": "VEC3", "min": p.min(axis=0).tolist(), "max": p.max(axis=0).tolist()})
            accessors.append({"bufferView": 1, "byteOffset": base * 12, "componentType": FLOAT, "count": len(p),
                              "type": "VEC3"})
            prim = {"attributes": {"POSITION": len(accessors) - 2, "NORMAL": len(accessors) - 1},
                    "material": mat_index[k]}
            (clear if e.get("clear_name") and materials[k]["alpha"] < 0.999 else prims).append(prim)
        if clear and not prims:                         # (all of it see-through: one node, as before)
            prims, clear = clear, []
        if not prims:
            continue
        node = {"name": e["name"], "extras": e["extras"]}
        if clear:                                       # (0.483) its glass, its water: a child node of its own
            meshes.append({"name": e["clear_name"], "primitives": clear})
            nodes.append({"name": e["clear_name"], "mesh": len(meshes) - 1, "extras": {"part": "clear"}})
            node["children"] = [len(nodes) - 1]
        meshes.append({"name": e["name"], "primitives": prims})
        node["mesh"] = len(meshes) - 1
        nodes.append(node)
        tree.setdefault(e["storey"], {}).setdefault(e["category"], []).append(len(nodes) - 1)
    storey_nodes = []
    for storey, categories in tree.items():
        children = []
        for category, members in categories.items():
            nodes.append({"name": category, "children": members})
            children.append(len(nodes) - 1)
        nodes.append({"name": storey, "children": children})
        storey_nodes.append(len(nodes) - 1)
    nodes.append({"name": name, "children": storey_nodes})
    root = len(nodes) - 1
    pos = np.concatenate(positions).tobytes()
    nor = np.concatenate(normals).tobytes()
    gltf = {"asset": {"version": "2.0", "generator": generator},
            "scene": 0,
            "scenes": [{"name": name, "nodes": [root],
                        "extras": {"offset": [float(v) for v in offset], "up": "Y", "units": "m",
                                   "from": "the model's (x, y, z) Z up: glTF (x, z, -y) + offset"}}],
            "nodes": nodes, "meshes": meshes, "materials": gl_materials, "accessors": accessors,
            "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos), "target": ARRAY_BUFFER},
                            {"buffer": 0, "byteOffset": len(pos), "byteLength": len(nor), "target": ARRAY_BUFFER}],
            "buffers": [{"byteLength": len(pos) + len(nor)}]}
    return gltf, pos + nor


def glb(gltf, binary):
    """The bytes of a GLB file: its header, its JSON chunk (padded with spaces), its binary chunk (with zeros)."""
    text = json.dumps(gltf, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    text += b" " * (-len(text) % 4)
    binary = binary + b"\0" * (-len(binary) % 4)
    total = 12 + 8 + len(text) + 8 + len(binary)
    return (struct.pack("<III", GLB_MAGIC, 2, total) + struct.pack("<II", len(text), GLB_JSON) + text
            + struct.pack("<II", len(binary), GLB_BIN) + binary)


def read(path):
    """(the glTF JSON, the binary chunk) of a GLB file — to check one, or to bring one in."""
    with open(path, "rb") as fh:
        data = fh.read()
    magic, version, total = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC or version != 2 or total != len(data):
        raise ValueError("not a GLB 2.0 file")
    length, kind = struct.unpack_from("<II", data, 12)
    if kind != GLB_JSON:
        raise ValueError("no JSON chunk")
    gltf = json.loads(data[20:20 + length].decode("utf-8"))
    binary = b""
    at = 20 + length
    if at < len(data):
        blength, bkind = struct.unpack_from("<II", data, at)
        if bkind == GLB_BIN:
            binary = data[at + 8:at + 8 + blength]
    return gltf, binary


def export(doc, objects, path, name=None):
    """The objects in a GLB file at `path`: (how many elements, how many triangles). ValueError("empty") with
    nothing to write."""
    from .. import __version__
    elements, materials = gather(doc, objects)
    gltf, binary = build(elements, materials, name or t("gltf.model"), "ArqSynth BIM " + __version__)
    with open(path, "wb") as fh:
        fh.write(glb(gltf, binary))
    triangles = sum(a["count"] for a in gltf["accessors"][::2]) // 3
    return len(gltf["meshes"]), triangles
