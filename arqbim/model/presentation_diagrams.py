"""(0.487) The ArqSynth Presentation's «Diagramas» — its «Volumes para diagramas» (lib/editor3d/diagrams: types.ts,
model.ts, geometry.ts): shapes put by a scene to explain the project — a box, a cylinder, a sphere, a cone or a plane —,
each with its measures (width, height, depth), where the middle of its base is, its turn and scale, its colour, opacity
and lines, shown or not, locked or not, and a description. Each scene keeps its own (Scene.diagrams).

Kept here as the Presentation keeps them, but the base's middle in the model's axes (Z up): the measures, the turn
(three.js's Euler «XYZ», degrees: about X, about the vertical, about the Presentation's Z — the model's −Y) and the scale
are the Presentation's own numbers, so that the same are seen in both programs. The shapes are made as three.js makes
them (a unit shape on its base, scaled by the measures, then by the scale, turned, moved). Pure Python and NumPy."""

import copy
import math
import uuid

import numpy as np

TYPES = ("box", "cylinder", "sphere", "cone", "plane")
COLOURS = ("#38bdf8", "#f59e0b", "#34d399", "#a78bfa", "#fb7185")      # (the Presentation's DIAGRAM_COLORS)
MAX = 100                       # a scene's volumes at most
SEGMENTS, RINGS = 32, 20        # (three.js's: CylinderGeometry / ConeGeometry 32, SphereGeometry 32 × 20)
DEFAULT = {"name": "", "type": "box", "dimensions": (2.0, 2.0, 2.0), "position": (0.0, 0.0, 0.0),
           "rotation": (0.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0), "color": COLOURS[0], "opacity": 1.0,
           "wireframe": False, "visible": True, "locked": False, "description": ""}
RANGES = {"dimensions": (0.01, 10000.0), "position": (-100000.0, 100000.0), "rotation": (-36000.0, 36000.0),
          "scale": (0.01, 100.0)}
# the Presentation's axes (Y up, −Z north) from the model's (Z up): gl = (x, z, −y); and back: model = TO_MODEL @ gl
TO_MODEL = np.array(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)))


def _number(value, fallback, lo, hi):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return fallback
    return round(min(max(v, lo), hi), 6) if v == v and abs(v) != math.inf else fallback


def _vector(value, fallback, lo, hi):
    items = list(value) if isinstance(value, (list, tuple)) else []
    return tuple(_number(items[k] if k < len(items) else None, fallback[k], lo, hi) for k in range(3))


def clean(d):
    """A volume as it may be kept (the Presentation's normalizeDiagram), or None when it is not one."""
    if not isinstance(d, dict) or not str(d.get("id") or "").strip() or d.get("type") not in TYPES:
        return None
    out = {"id": str(d["id"]).strip()[:160], "type": d["type"]}
    out["name"] = str(d.get("name") or "").strip()[:120] or d["type"]
    for name in ("dimensions", "position", "rotation", "scale"):
        lo, hi = RANGES[name]
        out[name] = _vector(d.get(name), DEFAULT[name], lo, hi)
    colour = str(d.get("color") or "")
    ok = len(colour) == 7 and colour.startswith("#") and all(c in "0123456789abcdefABCDEF" for c in colour[1:])
    out["color"] = colour.lower() if ok else COLOURS[0]
    out["opacity"] = _number(d.get("opacity"), 1.0, 0.0, 1.0)
    out["wireframe"] = bool(d.get("wireframe", False))
    out["visible"] = bool(d.get("visible", True))
    out["locked"] = bool(d.get("locked", False))
    out["description"] = str(d.get("description") or "")[:2000]
    return out


def clean_all(items):
    """A scene's volumes as they may be kept: each id once, at most MAX."""
    out, seen = [], set()
    for d in items if isinstance(items, (list, tuple)) else ():
        d = clean(d)
        if d is not None and d["id"] not in seen:
            seen.add(d["id"])
            out.append(d)
    return tuple(out[:MAX])


def free_name(items, base):
    """«Caixa N», N the lowest not taken (the Presentation's createDiagram)."""
    names = {d.get("name") for d in items}
    n = 1
    while "{} {}".format(base, n) in names:
        n += 1
    return "{} {}".format(base, n)


def new(kind, items, low, high, base="Caixa"):
    """A new volume beside the model (the Presentation's createDiagram): as big as a fifth of the model's radius (1 to
    10 m), its base's middle past the model's east side, at the model's lowest level, half across; its colour the next
    of COLOURS, a little see-through. low / high: the model's box (None: none)."""
    if low is None or high is None:
        low, high = (-1.0, -1.0, 0.0), (1.0, 1.0, 2.0)
    low, high = np.asarray(low, dtype=float), np.asarray(high, dtype=float)
    centre, size = (low + high) / 2.0, high - low
    radius = float(np.linalg.norm(size)) / 2.0
    unit = max(1.0, min(10.0, radius * 0.2))
    return clean({"id": uuid.uuid4().hex[:12], "type": kind, "name": free_name(items, base),
                  "dimensions": (unit, unit, unit),
                  "position": (float(centre[0] + size[0] / 2.0 + unit), float(centre[1]), float(low[2])),
                  "color": COLOURS[len(items) % len(COLOURS)], "opacity": 0.85})


def duplicate(d, items, copy_word="cópia"):
    """A copy beside it (the Presentation's duplicateDiagram): «<name> cópia» (or «cópia 2»…), unlocked, moved its
    width × 1,2 along X."""
    out = copy.deepcopy(clean(d))
    names = {o.get("name") for o in items}
    suffix, n = " " + copy_word, 2
    while d["name"] + suffix in names:
        suffix, n = " {} {}".format(copy_word, n), n + 1
    out.update(id=uuid.uuid4().hex[:12], name=d["name"] + suffix, locked=False)
    step = out["dimensions"][0] * out["scale"][0] * 1.2
    out["position"] = (out["position"][0] + step, out["position"][1], out["position"][2])
    return out


def volume(d):
    """Its volume, m³ (a plane: 0)."""
    w, h, dep = (d["dimensions"][k] * d["scale"][k] for k in range(3))
    return w * h * dep * {"box": 1.0, "cylinder": math.pi / 4, "sphere": math.pi / 6, "cone": math.pi / 12,
                          "plane": 0.0}[d["type"]]


def _euler(degrees):
    """three.js's rotation matrix of an Euler «XYZ» (Rx · Ry · Rz)."""
    x, y, z = (math.radians(a) for a in degrees)
    rx = np.array(((1, 0, 0), (0, math.cos(x), -math.sin(x)), (0, math.sin(x), math.cos(x))))
    ry = np.array(((math.cos(y), 0, math.sin(y)), (0, 1, 0), (-math.sin(y), 0, math.cos(y))))
    rz = np.array(((math.cos(z), -math.sin(z), 0), (math.sin(z), math.cos(z), 0), (0, 0, 1)))
    return rx @ ry @ rz


def linear(d):
    """The 3 × 3 part that takes the unit shape (the Presentation's axes) to the model's: TO_MODEL · R · S · measures."""
    return TO_MODEL @ _euler(d["rotation"]) @ np.diag(d["scale"]) @ np.diag(d["dimensions"])


def euler_of(r):
    """(0.492) three.js's Euler «XYZ» (degrees) of a rotation matrix (its setFromRotationMatrix)."""
    m13 = min(max(float(r[0][2]), -1.0), 1.0)
    y = math.asin(m13)
    if abs(m13) < 0.9999999:
        x, z = math.atan2(-float(r[1][2]), float(r[2][2])), math.atan2(-float(r[0][1]), float(r[0][0]))
    else:
        x, z = math.atan2(float(r[2][1]), float(r[1][1])), 0.0
    return tuple(round(math.degrees(a), 6) + 0.0 for a in (x, y, z))


def transformed(d, matrix):
    """(0.492) The volume moved, turned or scaled by a 4 × 4 matrix of the model's axes (the BIM's Mover, Rodar,
    Escala): the middle of its base taken by it; its turn and its scale the Presentation's numbers again (the shape's
    own axes kept: a scale along the model's axes of a turned volume is taken along its own)."""
    m = np.asarray(matrix, dtype=float)
    p = m[:3, :3] @ np.asarray(d["position"], dtype=float) + m[:3, 3]
    a = TO_MODEL.T @ m[:3, :3] @ TO_MODEL @ _euler(d["rotation"]) @ np.diag(d["scale"])
    scale = np.linalg.norm(a, axis=0)
    r = a / np.where(scale > 1e-12, scale, 1.0)
    u, _s, vt = np.linalg.svd(r)                      # (the nearest rotation)
    r = u @ vt
    if np.linalg.det(r) < 0:                          # (a mirror: not a turn — the shape's last axis turned back)
        u[:, -1] *= -1
        r = u @ vt
    return clean(dict(d, position=tuple(float(c) for c in p), rotation=euler_of(r),
                      scale=tuple(float(s) for s in scale)))


def handles(d):
    """(0.492) Its faces' grips, as the Presentation's: [(axis of the shape — 0 width, 1 height, 2 depth —, side ±1,
    the face's middle in the model's axes)] — a plane's four sides only."""
    m, p = linear(d), np.asarray(d["position"], dtype=float)
    faces = [(0, -1, (-0.5, 0.5, 0.0)), (0, 1, (0.5, 0.5, 0.0)), (2, -1, (0.0, 0.5, -0.5)), (2, 1, (0.0, 0.5, 0.5)),
             (1, -1, (0.0, 0.0, 0.0)), (1, 1, (0.0, 1.0, 0.0))]
    if d["type"] == "plane":
        faces = [(k, side, (c[0], 0.0, c[2])) for k, side, c in faces[:4]]
    return [(k, side, tuple(float(v) for v in m @ np.array(c) + p)) for k, side, c in faces]


def face_axis(d, k):
    """(0.492) The way the shape's axis `k` goes, in the model's axes (unit)."""
    v = TO_MODEL @ _euler(d["rotation"]) @ np.eye(3)[k]
    return v / np.linalg.norm(v)


def resized(d, k, side, delta):
    """(0.492) A face dragged `delta` m out (in: negative) along its axis, the opposite one kept where it is (the
    Presentation's face grips): the measure along it changed, the base's middle moved as much as it must."""
    dims = list(d["dimensions"])
    s = float(d["scale"][k])
    extent = dims[k] * s
    new = max(extent + float(delta), RANGES["dimensions"][0] * s)
    moved = new - extent
    dims[k] = new / s
    p = np.asarray(d["position"], dtype=float)
    axis = face_axis(d, k)
    if k == 1:                                         # (the height: the base is the bottom face)
        if side < 0:
            p = p - axis * moved
    else:
        p = p + axis * (moved / 2.0) * side
    return clean(dict(d, dimensions=tuple(dims), position=tuple(float(c) for c in p)))


def unit_shape(kind):
    """(points (N, 3), normals (N, 3), triangles (M, 3)) of the unit shape in the Presentation's axes — on its base
    (y from 0), its middle on the axis, 1 × 1 × 1; the plane flat at y = 0 — as three.js's geometries."""
    if kind == "plane":
        p = np.array(((-0.5, 0, 0.5), (0.5, 0, 0.5), (0.5, 0, -0.5), (-0.5, 0, -0.5)), dtype=float)
        return p, np.tile((0.0, 1.0, 0.0), (4, 1)), np.array(((0, 1, 2), (0, 2, 3)))
    if kind == "box":
        pts, nrm, tri = [], [], []
        for axis in range(3):
            for sign in (-1.0, 1.0):
                n = np.zeros(3)
                n[axis] = sign
                u, v = [k for k in range(3) if k != axis]
                corners = []
                for a, b in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
                    c = np.zeros(3)
                    c[axis], c[u], c[v] = 0.5 * sign, a, b
                    corners.append(c)
                k0 = len(pts)
                pts += corners
                nrm += [n] * 4
                first = ((0, 1, 2), (0, 2, 3)) if np.dot(np.cross(corners[1] - corners[0], corners[2] - corners[0]),
                                                         n) > 0 else ((0, 2, 1), (0, 3, 2))
                tri += [tuple(k0 + i for i in t) for t in first]
        p = np.array(pts) + np.array((0.0, 0.5, 0.0))
        return p, np.array(nrm), np.array(tri)
    if kind == "sphere":
        pts, nrm = [], []
        for i in range(RINGS + 1):
            theta = math.pi * i / RINGS
            for j in range(SEGMENTS + 1):
                phi = 2 * math.pi * j / SEGMENTS
                n = np.array((-math.cos(phi) * math.sin(theta), math.cos(theta), math.sin(phi) * math.sin(theta)))
                pts.append(n * 0.5 + np.array((0.0, 0.5, 0.0)))
                nrm.append(n)
        tri, row = [], SEGMENTS + 1
        for i in range(RINGS):
            for j in range(SEGMENTS):
                a, b, c, e = i * row + j, i * row + j + 1, (i + 1) * row + j, (i + 1) * row + j + 1
                if i:
                    tri.append((a, c, b))
                if i < RINGS - 1:
                    tri.append((b, c, e))
        return np.array(pts), np.array(nrm), np.array(tri)
    top = 0.0 if kind == "cone" else 0.5                     # a cylinder or a cone (its top a point)
    pts, nrm, tri = [], [], []
    slope = 0.5 if kind == "cone" else 0.0                   # (the side's normal leans up on a cone)
    for j in range(SEGMENTS + 1):
        phi = 2 * math.pi * j / SEGMENTS
        s, c = math.sin(phi), math.cos(phi)
        n = np.array((s, slope, c))
        n /= np.linalg.norm(n)
        pts += [(0.5 * s, 0.0, 0.5 * c), (top * s, 1.0, top * c)]
        nrm += [n, n]
    for j in range(SEGMENTS):
        a, b, c, e = 2 * j, 2 * j + 1, 2 * j + 2, 2 * j + 3
        tri += [(a, c, b), (b, c, e)]
    for y, r, sign in ((0.0, 0.5, -1.0), (1.0, top, 1.0)):    # its caps (none at a cone's point)
        if r <= 0:
            continue
        k0 = len(pts)
        pts.append((0.0, y, 0.0))
        nrm.append((0.0, sign, 0.0))
        for j in range(SEGMENTS + 1):
            phi = 2 * math.pi * j / SEGMENTS
            pts.append((r * math.sin(phi), y, r * math.cos(phi)))
            nrm.append((0.0, sign, 0.0))
        for j in range(SEGMENTS):
            tri.append((k0, k0 + 1 + j, k0 + 2 + j) if sign > 0 else (k0, k0 + 2 + j, k0 + 1 + j))
    return np.array(pts, dtype=float), np.array(nrm, dtype=float), np.array(tri)


def shape(d):
    """(points (N, 3), normals (N, 3), triangles (M, 3)) of the volume in the model's axes."""
    p, n, tri = unit_shape(d["type"])
    m = linear(d)
    points = p @ m.T + np.asarray(d["position"], dtype=float)
    try:
        normal_m = np.linalg.inv(m).T
    except np.linalg.LinAlgError:
        normal_m = m
    normals = n @ normal_m.T
    length = np.linalg.norm(normals, axis=1)
    normals = normals / np.where(length > 1e-12, length, 1.0)[:, None]
    return points, normals, tri


def outline(d):
    """The twelve edges of its box (the unit shape's box, as it is turned), in the model's axes: [(a, b)] — the
    volume chosen, drawn round."""
    m = linear(d)
    top = 0.0 if d["type"] == "plane" else 1.0
    corners = [np.array((x, y, z)) for y in (0.0, top) for x, z in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5),
                                                                       (-0.5, 0.5))]
    pts = [tuple(float(c) for c in (m @ q + np.asarray(d["position"], dtype=float))) for q in corners]
    edges = [(pts[k], pts[(k + 1) % 4]) for k in range(4)]
    if top:
        edges += [(pts[4 + k], pts[4 + (k + 1) % 4]) for k in range(4)] + [(pts[k], pts[4 + k]) for k in range(4)]
    return edges


def bounds(items):
    """(lowest, highest) corner of the volumes shown (not see-through to nothing), or None."""
    pts = [p for d in items if d["visible"] and d["opacity"] > 0 for p in shape(d)[0]]
    if not pts:
        return None
    pts = np.array(pts)
    return pts.min(axis=0), pts.max(axis=0)


def to_presentation(d, gl_point):
    """A volume as the Presentation's DiagramObject (gl_point: the GLB's axes) — its id «bim_dia_<id>»."""
    return {"id": "bim_dia_" + d["id"], "name": d["name"], "source": "primitive", "type": d["type"],
            "dimensions": [round(float(v), 6) for v in d["dimensions"]],
            "transform": {"position": [round(float(c), 6) for c in gl_point(d["position"])],
                          "rotation": [round(float(v), 6) for v in d["rotation"]],
                          "scale": [round(float(v), 6) for v in d["scale"]]},
            "material": {"color": d["color"], "opacity": d["opacity"], "wireframe": d["wireframe"]},
            "visible": d["visible"], "locked": d["locked"], "metadata": {"description": d["description"]}}


def with_one(items, d):
    """The volumes with this one put (in its place when it was there, else at the end)."""
    out = [copy.deepcopy(o) for o in clean_all(items)]
    d = clean(d)
    if d is None:
        return tuple(out)
    for k, o in enumerate(out):
        if o["id"] == d["id"]:
            out[k] = d
            return tuple(out)
    return tuple((out + [d])[:MAX])


def without(items, d_id):
    return tuple(copy.deepcopy(o) for o in clean_all(items) if o["id"] != d_id)
