"""(0.371) The model as USDZ — Pixar's Universal Scene Description in its zipped package: what an iPhone or an iPad
opens on its own (AR Quick Look: the model on the table, or in the room at its true size; pinched, smaller) and what
Apple's Reality Composer, NVIDIA's Omniverse, Blender, Houdini… read. The same elements and materials as the GLB
(gltf_export.gather): the model ▸ storey ▸ category ▸ element prims, named as the program shows them (their display
names; their prim names made valid identifiers), each element's data in its customData — GlobalId, IFC class, type,
storey —; a mesh an element's material, flat (each triangle its own three corners and its normal), never subdivided;
each material a UsdPreviewSurface with its colour (linear), its transparency and its finish (metallic and roughness
as the GLB's; glass and water with their index of refraction). Y up, in metres, moved as the GLB (its middle over the
origin, standing on it — so in AR it lands on the floor): the offset in the layer's customLayerData. Written as a
binary USDC by usd-core (the owner's go-ahead) and packed by USD's own ARKit packer (UsdUtils)."""

import os
import tempfile

import numpy as np

from .gltf_export import FINISH_PBR, _linear, _y_up

MODEL = "Modelo"
MATERIALS = "Materiais"
IOR = {"glass": 1.5, "frosted": 1.5, "water": 1.333}


def _namer():
    """name(parent, text): a valid prim name for `text`, once under each parent (Parede_1, Parede_1_2…)."""
    from pxr import Tf
    used = {}

    def name(parent, text):
        base = Tf.MakeValidIdentifier(str(text or "").strip() or "_")
        taken = used.setdefault(str(parent), set())
        candidate, k = base, 1
        while candidate in taken:
            k += 1
            candidate = "{}_{}".format(base, k)
        taken.add(candidate)
        return candidate
    return name


def _shown(prim, text):
    """The name a viewer shows for a prim: the program's, accents and spaces kept (USD's displayName)."""
    if text and hasattr(prim, "SetDisplayName"):
        prim.SetDisplayName(str(text))


def write_usdz(path, elements, materials, name="ArqSynth BIM"):
    """A USDZ file of these elements and materials (gltf_export.gather's): (elements, triangles). ValueError("empty")
    when there is nothing to draw; ImportError without usd-core; OSError when the package cannot be written."""
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, UsdUtils, Vt
    pts = [np.asarray(c, dtype=float).reshape(-1, 3) for e in elements for c in e["parts"].values() if len(c)]
    if not pts:
        raise ValueError("empty")
    every = np.concatenate(pts)
    lo, hi = every.min(axis=0), every.max(axis=0)
    offset = np.array(((lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, lo[2]))
    unique = _namer()
    floats = Sdf.ValueTypeNames.Float
    with tempfile.TemporaryDirectory(prefix="arqsynth_usd_", ignore_cleanup_errors=True) as folder:   # (the USDC
        #                                                 may stay mapped by USD's layer cache: on Windows, not deleted)
        layer = os.path.join(folder, "modelo.usdc")
        stage = Usd.Stage.CreateNew(layer)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
        UsdGeom.SetStageMetersPerUnit(stage, UsdGeom.LinearUnits.meters)
        root = UsdGeom.Xform.Define(stage, Sdf.Path("/" + MODEL)).GetPrim()
        stage.SetDefaultPrim(root)
        _shown(root, name)
        stage.GetRootLayer().customLayerData = {
            "creator": "ArqSynth BIM", "offset": Gf.Vec3d(*(float(v) for v in offset)),
            "from": "the model's (x, y, z) Z up: USD (x, z, -y) + offset"}
        looks = UsdGeom.Scope.Define(stage, root.GetPath().AppendChild(MATERIALS)).GetPrim()
        bound = {}
        for k, m in materials.items():
            where = looks.GetPath().AppendChild(unique(looks.GetPath(), m["name"]))
            material = UsdShade.Material.Define(stage, where)
            _shown(material.GetPrim(), m["name"])
            shader = UsdShade.Shader.Define(stage, where.AppendChild("Superficie"))
            shader.CreateIdAttr("UsdPreviewSurface")
            metallic, rough = FINISH_PBR.get(m["finish"], FINISH_PBR["matte"])
            shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
                Gf.Vec3f(*(float(v) for v in _linear(m["rgb"]))))
            shader.CreateInput("metallic", floats).Set(float(metallic))
            shader.CreateInput("roughness", floats).Set(float(rough))
            if m["alpha"] < 0.999:
                shader.CreateInput("opacity", floats).Set(float(m["alpha"]))
            if m["finish"] in IOR:
                shader.CreateInput("ior", floats).Set(IOR[m["finish"]])
            material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
            bound[k] = material
        groups = {}

        def group(parent, text):
            key = (str(parent), text)
            if key not in groups:
                prim = UsdGeom.Xform.Define(stage, parent.AppendChild(unique(parent, text))).GetPrim()
                _shown(prim, text)
                groups[key] = prim.GetPath()
            return groups[key]

        count = triangles = 0
        for e in elements:
            parts = []
            for k, c in e["parts"].items():
                c = np.asarray(c, dtype=float).reshape(-1, 3, 3)
                n = np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0])
                length = np.linalg.norm(n, axis=1)
                keep = length > 1e-12
                if keep.any():
                    parts.append((k, c[keep], n[keep] / length[keep][:, None]))
            if not parts:
                continue
            under = group(group(root.GetPath(), e["storey"]), e["category"])
            element = UsdGeom.Xform.Define(stage, under.AppendChild(unique(under, e["name"]))).GetPrim()
            _shown(element, e["name"])
            for key, value in (e.get("extras") or {}).items():
                element.SetCustomDataByKey(str(key), str(value))
            for k, c, n in parts:
                mesh = UsdGeom.Mesh.Define(stage, element.GetPath().AppendChild(
                    unique(element.GetPath(), materials[k]["name"])))
                p = _y_up(c.reshape(-1, 3) - offset).astype(np.float32)
                normals = _y_up(np.repeat(n, 3, axis=0)).astype(np.float32)
                mesh.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(p))
                mesh.CreateFaceVertexCountsAttr(Vt.IntArray.FromNumpy(np.full(len(c), 3, dtype=np.int32)))
                mesh.CreateFaceVertexIndicesAttr(Vt.IntArray.FromNumpy(np.arange(len(p), dtype=np.int32)))
                mesh.CreateNormalsAttr(Vt.Vec3fArray.FromNumpy(normals))
                mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
                mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)       # (flat faces, never smoothed)
                mesh.CreateDoubleSidedAttr(True)
                mesh.CreateExtentAttr(Vt.Vec3fArray([Gf.Vec3f(*(float(v) for v in p.min(axis=0))),
                                                     Gf.Vec3f(*(float(v) for v in p.max(axis=0)))]))
                UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(bound[k])
                triangles += len(c)
            count += 1
        stage.GetRootLayer().Save()
        if not UsdUtils.CreateNewARKitUsdzPackage(Sdf.AssetPath(layer), path):
            raise OSError("usdz")
    return count, triangles
