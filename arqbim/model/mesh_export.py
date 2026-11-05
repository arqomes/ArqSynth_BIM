"""(0.349) The model in OBJ and STL — besides the GLB (model/gltf_export.py), from the same gathering (its elements'
faces by material):

- **OBJ + MTL**, which nearly every 3D program reads: each element an object of its own, named «Storey / Category /
  element», its faces by material (usemtl); the materials in the MTL beside it — their colour, transparency and
  shininess (Kd, d, Ns from the finish). Y up and moved near the origin, as the GLB (the programs that read OBJ take
  Y up); flat faces, each with its normal.
- **STL** (binary) to print a model in 3D: the whole of it one solid, at a scale (1:100…) in millimetres — what
  slicers take —, Z up, its lowest point on the plate (z = 0) and centred on it.

Pure NumPy."""

import os
import struct

import numpy as np

from . import gltf_export
from .gltf_export import FINISH_PBR

SCALES = (50, 100, 200, 500)            # the STL's scales offered (1:N)


def _offset(elements):
    pts = np.concatenate([c.reshape(-1, 3) for e in elements for c in e["parts"].values() if len(c)])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    return lo, hi, np.array(((lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, lo[2]))


def _flat(corners):
    """Corners (T, 3, 3) and each one's unit normal, the degenerate ones left out."""
    c = np.asarray(corners, dtype=float).reshape(-1, 3, 3)
    n = np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0])
    length = np.linalg.norm(n, axis=1)
    keep = length > 1e-12
    return c[keep], n[keep] / length[keep][:, None]


def _name(text):
    """A name as OBJ / MTL take it: one word (no spaces)."""
    return "_".join(str(text).split()) or "_"


def write_obj(path, elements, materials):
    """An OBJ file and its MTL beside it (same name): (objects, triangles)."""
    if not any(len(c) for e in elements for c in e["parts"].values()):
        raise ValueError("empty")
    _lo, _hi, offset = _offset(elements)
    mtl_path = os.path.splitext(path)[0] + ".mtl"
    names = {}
    with open(mtl_path, "w", encoding="utf-8") as fh:
        fh.write("# ArqSynth BIM\n")
        for k, m in materials.items():
            name = _name(m["name"])
            if name in names.values():                  # (two of one name: the colour or the finish tells them apart)
                name = "{}_{}".format(name, len(names))
            names[k] = name
            r, g, b = m["rgb"]
            _metal, rough = FINISH_PBR.get(m["finish"], FINISH_PBR["matte"])
            fh.write("\nnewmtl {}\nKa 0 0 0\nKd {:.4f} {:.4f} {:.4f}\nKs {s:.3f} {s:.3f} {s:.3f}\nNs {:.1f}\n"
                     "d {:.3f}\nillum 2\n".format(name, r, g, b, (1.0 - rough) * 900.0 + 10.0, m["alpha"],
                                                  s=0.04 + 0.5 * (1.0 - rough)))
    objects = triangles = 0
    v_at = n_at = 1                                     # (OBJ numbers its vertices and its normals from 1, file-wide)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# ArqSynth BIM: Y up, metres; the model moved by {:.3f} {:.3f} {:.3f} (x y z, Z up)\n"
                 "mtllib {}\n".format(*offset, os.path.basename(mtl_path)))
        for e in elements:
            parts = [(k, _flat(c - offset)) for k, c in e["parts"].items() if len(c)]
            parts = [(k, cn) for k, cn in parts if len(cn[0])]
            if not parts:
                continue
            objects += 1
            fh.write("o {}\n".format(_name("{}/{}/{}".format(e["storey"], e["category"], e["name"]))))
            for k, (c, n) in parts:
                count = len(c)
                fh.write("usemtl {}\n".format(names[k]))
                fh.write("".join("v {:.5f} {:.5f} {:.5f}\n".format(*v) for v in gltf_export._y_up(c.reshape(-1, 3))))
                fh.write("".join("vn {:.4f} {:.4f} {:.4f}\n".format(*v) for v in gltf_export._y_up(n)))
                fh.write("".join("f {0}//{3} {1}//{3} {2}//{3}\n".format(v_at + 3 * t, v_at + 3 * t + 1,
                                                                        v_at + 3 * t + 2, n_at + t)
                                 for t in range(count)))
                v_at += 3 * count                       # (three corners a triangle, one normal)
                n_at += count
                triangles += count
    return objects, triangles


def write_stl(path, elements, scale=100):
    """A binary STL of the whole model at 1:scale, in millimetres, Z up, on the plate: its triangles."""
    corners = [c for e in elements for c in e["parts"].values() if len(c)]
    if not corners:
        raise ValueError("empty")
    c, n = _flat(np.concatenate([x.reshape(-1, 3, 3) for x in corners]))
    lo, hi = c.reshape(-1, 3).min(axis=0), c.reshape(-1, 3).max(axis=0)
    centre = np.array(((lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, lo[2]))
    mm = (c - centre) * (1000.0 / float(scale))
    record = np.zeros(len(c), dtype=[("normal", "<f4", 3), ("corners", "<f4", (3, 3)), ("attr", "<u2")])
    record["normal"] = n
    record["corners"] = mm
    with open(path, "wb") as fh:
        fh.write("ArqSynth BIM - 1:{} - mm".format(int(scale)).encode("ascii").ljust(80, b" "))   # (80 bytes)
        fh.write(struct.pack("<I", len(c)))
        fh.write(record.tobytes())
    return len(c)


def read_stl(path):
    """(normals (T, 3), corners (T, 3, 3)) of a binary STL — to check one."""
    with open(path, "rb") as fh:
        data = fh.read()
    (count,) = struct.unpack_from("<I", data, 80)
    record = np.frombuffer(data, dtype=[("normal", "<f4", 3), ("corners", "<f4", (3, 3)), ("attr", "<u2")],
                           count=count, offset=84)
    return record["normal"].astype(float), record["corners"].astype(float)
