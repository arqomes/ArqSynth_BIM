"""Geometry cache on disk (principle 2: "the GPU draws from a binary cache").

Working out the 3D shape of every element (the IfcOpenShell geometry kernel,
with the openings cut) is most of the time spent opening a file. The shapes
are kept in a binary file — vertices, triangles and visible edges of every
element — and read back next time instead of being worked out again.

Where: %LOCALAPPDATA%\\ArqSynth BIM\\geometria (until 0.76: ArqBIM; not beside the project, so the
user's folders get no extra files; deleting it only makes the next opening
slower). One file per IFC path. It is used only if the IFC file is exactly the
one it was made from (same size and modification time) and with the same
kernel version and settings; otherwise everything is worked out again (e.g.
the file was changed by another program).

Format: one uncompressed numpy .npz (fast to read): the GlobalIds, the counts
per element and the concatenated arrays; and (format 3) each element's class,
name and storey, the storeys, the spatial tree and the origin — enough to show
the model before its IFC is read (document.read_preview).
"""

import hashlib
import json
import os

import numpy as np

from ..core.mesh import triangle_normals

FORMAT = 3                      # 2: also the elements without a shape; 3: what shows the model before its IFC is read
KEEP = 40                       # cache files kept (the most recently written); older ones are deleted


def cache_dir():
    override = os.environ.get("ARQBIM_CACHE_DIR")          # tests point it to a temporary folder
    if override:
        return override
    from ..paths import user_dir
    base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".cache")
    return user_dir(base, "geometria")                    # (0.77: "ArqSynth BIM", once "ArqBIM")


def _prune():
    folder = cache_dir()
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".npz")]
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    for old in files[KEEP:]:
        try:
            os.remove(old)
        except OSError:
            pass


def cache_path(ifc_path):
    name = hashlib.sha1(os.path.normcase(os.path.abspath(ifc_path)).encode("utf-8")).hexdigest()
    return os.path.join(cache_dir(), name + ".npz")


def _key(ifc_path, kernel):
    st = os.stat(ifc_path)
    return json.dumps({"format": FORMAT, "size": st.st_size, "mtime_ns": st.st_mtime_ns, "kernel": kernel},
                      sort_keys=True)


def save(ifc_path, meshes, kernel, empty=(), info=None):
    """Write the shapes of the elements of a just saved / opened IFC file.
    meshes: {GlobalId: TriMesh}; empty: GlobalIds the kernel makes no shape for (not
    tried again next time). info: what is needed to show the model before its IFC is
    read (see load_all): {"classes", "names", "storeys": {GlobalId: …}, "levels",
    "spatial", "origin"}. Never fails the caller (a cache is optional)."""
    try:
        guids = list(meshes)
        items = [meshes[g] for g in guids]
        pairs = [m.edge_array() for m in items]
        info = info or {}
        classes, names, storeys = (info.get(k) or {} for k in ("classes", "names", "storeys"))
        meta = {"levels": info.get("levels"), "spatial": info.get("spatial"),
                "origin": [float(c) for c in info.get("origin", (0.0, 0.0, 0.0))]}
        data = {
            "key": np.array(_key(ifc_path, kernel)),
            "meta": np.array(json.dumps(meta, ensure_ascii=False)),
            "guids": np.array(guids, dtype="U22"),
            "classes": np.array([classes.get(g, "") for g in guids], dtype=str),
            "names": np.array([names.get(g, "") for g in guids], dtype=str),
            "storey_of": np.array([storeys.get(g) or "" for g in guids], dtype="U22"),
            "empty": np.array(sorted(empty), dtype="U22"),
            "nverts": np.array([len(m.verts) for m in items], np.int64),
            "ntris": np.array([len(m.tris) for m in items], np.int64),
            "nedges": np.array([len(p[0]) for p in pairs], np.int64),
            "closed": np.array([bool(m.is_closed()) for m in items]),
            "verts": np.concatenate([m.verts for m in items]) if items else np.zeros((0, 3)),
            "tris": np.concatenate([m.tris for m in items]).astype(np.int32) if items else np.zeros((0, 3), np.int32),
            "pairs": np.concatenate([p[0] for p in pairs]).astype(np.int32) if items else np.zeros((0, 2), np.int32),
            "faces": np.concatenate([p[1] for p in pairs]).astype(np.int32) if items else np.zeros((0, 2), np.int32),
            # (0.259) the triangles' own colours of the elements that have them (a railing's parts)
            "ncolors": np.array([0 if getattr(m, "colors", None) is None else len(m.tris) for m in items], np.int64),
            "colors": np.concatenate([m.colors for m in items if getattr(m, "colors", None) is not None]
                                     or [np.zeros((0, 3), np.float32)]).astype(np.float32),
        }
        os.makedirs(cache_dir(), exist_ok=True)
        target = cache_path(ifc_path)
        tmp = target + ".tmp.npz"
        np.savez(tmp, **data)
        os.replace(tmp, target)                  # never a half-written cache
        _prune()
        return True
    except Exception:
        return False


def load(ifc_path, kernel):
    """{GlobalId: (verts, tris, (pairs, faces), closed, normals)} if a valid cache exists, else {}.
    Elements known to have no shape map to None."""
    return load_all(ifc_path, kernel)[0]


def load_all(ifc_path, kernel):
    """(shapes as load() gives them, info as save() got it — or None if the cache does not
    have it). ({}, None) if there is no valid cache."""
    path = cache_path(ifc_path)
    if not os.path.exists(path):
        return {}, None
    try:
        with np.load(path, allow_pickle=False) as data:
            if str(data["key"]) != _key(ifc_path, kernel):
                return {}, None
            guids, closed, empty = data["guids"], data["closed"], data["empty"]
            verts, tris, pairs, faces = data["verts"], data["tris"], data["pairs"], data["faces"]
            nverts, ntris = data["nverts"], data["ntris"]
            v_end, t_end, e_end = (np.cumsum(data[k]) for k in ("nverts", "ntris", "nedges"))
            meta = json.loads(str(data["meta"]))
            classes, names, storey_of = data["classes"], data["names"], data["storey_of"]
            if "ncolors" in data.files:                  # (0.259; a cache made before has none)
                ncolors, colors = data["ncolors"], data["colors"]
            else:
                ncolors, colors = np.zeros(len(guids), np.int64), np.zeros((0, 3), np.float32)
        # the normals of all the triangles at once (one numpy call, not one per element)
        tris = tris.astype(np.int64)
        normals = triangle_normals(verts, tris + np.repeat(v_end - nverts, ntris)[:, None])
    except Exception:
        return {}, None                          # unreadable: work everything out again
    out = {str(guid): None for guid in empty}
    v0 = t0 = e0 = c0 = 0
    for k, guid in enumerate(guids):
        v1, t1, e1 = int(v_end[k]), int(t_end[k]), int(e_end[k])
        c1 = c0 + int(ncolors[k])
        out[str(guid)] = (verts[v0:v1], tris[t0:t1], (pairs[e0:e1], faces[e0:e1]), bool(closed[k]),
                          normals[t0:t1], colors[c0:c1] if c1 > c0 else None)
        v0, t0, e0, c0 = v1, t1, e1, c1
    info = None
    if meta.get("levels") is not None and all(str(c) for c in classes):
        guids = [str(g) for g in guids]
        info = {"classes": dict(zip(guids, map(str, classes))), "names": dict(zip(guids, map(str, names))),
                "storeys": {g: (str(s) or None) for g, s in zip(guids, storey_of)},
                "levels": meta["levels"], "spatial": meta["spatial"], "origin": meta["origin"]}
    return out, info


def forget(ifc_path):
    """Delete the cache of a file (the benchmark measures a first opening this way)."""
    try:
        os.remove(cache_path(ifc_path))
    except OSError:
        pass
