"""(0.487) The ArqSynth Presentation's «Diagramas» — its «Volumes para diagramas» (lib/editor3d/diagrams: types.ts,
model.ts, geometry.ts): shapes put by a scene to explain the project — a box, a cylinder, a sphere, a cone or a plane —,
each with its measures (width, height, depth), where the middle of its base is, its turn and scale, its colour, opacity
and lines, shown or not, locked or not, and a description. Each scene keeps its own (Scene.diagrams).

Kept here as the Presentation keeps them, but the base's middle in the model's axes (Z up): the measures, the turn
(three.js's Euler «XYZ», degrees: about X, about the vertical, about the Presentation's Z — the model's −Y) and the scale
are the Presentation's own numbers, so that the same are seen in both programs. The shapes are made as three.js makes
them (a unit shape on its base, scaled by the measures, then by the scale, turned, moved). Pure Python and NumPy.

(0.493) Two volumes combined — the Presentation's «Combinar e recortar» (lib/editor3d/diagrams: boolean-engine.ts,
boolean-result.ts, boolean-data.ts): União, Subtração A − B and B − A, Interseção, Diferença, calculated with the same
engine (manifold, here its Python package `manifold3d`). The result is a volume of its own («source»: "boolean"): its
mesh kept on a unit box as the Presentation keeps it (X and Z about the middle, Y from 0, in the Presentation's axes),
its measures, turn and scale as any volume's; its two origins kept (hidden or not) and, here, calculated again by
themselves when one of them changes (`refreshed`)."""

import functools
import hashlib
import math
import uuid

import numpy as np

TYPES = ("box", "cylinder", "sphere", "cone", "plane")
OPERATIONS = ("union", "subtract", "reverse_subtract", "intersect", "difference")   # (the Presentation's BOOLEAN_NAMES)
MAX_TRIANGLES = 50000           # a volume's triangles at most (its MAX_BOOLEAN_TRIANGLES)
MAX_CHAIN = 8                   # operations one upon another at most
CREASE = math.radians(32.0)     # a result's faces drawn smooth across a smaller fold, sharp across a bigger one
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
    return round(min(max(v, lo), hi), 6) + 0.0 if v == v and abs(v) != math.inf else fallback     # (no −0)


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
    b = _clean_boolean(d.get("boolean")) if d.get("source") == "boolean" else None
    if b is not None:                                  # (0.493) a result of two (a primitive has neither key)
        out["source"], out["boolean"] = "boolean", b
    return out


_CHECKED = {}                   # (id of a mesh's positions → the positions: found good once, not checked again)


def _clean_boolean(b):
    """(0.493) A result's own fields as they may be kept (the Presentation's cleanBoolean), or None: the operation, its
    two origins (ids), the origins' geometry when it was calculated (keys), the origins it hides and how they were
    shown before, its box when calculated (base: the middle of its bottom in the model's axes, its measures), its mesh
    on the unit box (positions, indices — at most MAX_TRIANGLES, each coordinate within ±2), the part of the unit
    box it fills (unit_volume)."""
    if not isinstance(b, dict) or b.get("operation") not in OPERATIONS:
        return None
    first, second = str(b.get("a") or "").strip(), str(b.get("b") or "").strip()
    if not first or not second or first == second:
        return None
    positions, indices = b.get("positions"), b.get("indices")
    good = isinstance(positions, tuple) and _CHECKED.get(id(positions)) is positions and isinstance(indices, tuple)
    if not good:
        try:
            p = np.asarray(positions, dtype=float).reshape(-1)
            tri = np.asarray(indices, dtype=np.int64).reshape(-1)
        except (TypeError, ValueError):
            return None
        if not (12 <= len(p) <= MAX_TRIANGLES * 9 and len(p) % 3 == 0 and 12 <= len(tri) <= MAX_TRIANGLES * 3
                and len(tri) % 3 == 0) or not np.all(np.isfinite(p)) or float(np.abs(p).max()) > 2.0 \
                or int(tri.min()) < 0 or int(tri.max()) >= len(p) // 3:
            return None
        positions, indices = tuple(float(v) for v in p), tuple(int(i) for i in tri)
        if len(_CHECKED) > 512:
            _CHECKED.clear()
        _CHECKED[id(positions)] = positions
    unit_volume = _number(b.get("unit_volume"), 0.0, 0.0, 1.0001)
    if unit_volume <= 0.0:
        return None
    keys = [str(k)[:80] for k in (b.get("keys") or ())][:2]
    shown = list(b.get("visibility") or ())[:2]
    return {"operation": b["operation"], "a": first, "b": second, "keys": tuple(keys + [""] * (2 - len(keys))),
            "hidden": tuple(i for i in dict.fromkeys(str(h) for h in (b.get("hidden") or ())) if i in (first, second)),
            "visibility": tuple(bool(v) for v in shown + [True] * (2 - len(shown))),
            "base_position": _vector(b.get("base_position"), (0.0, 0.0, 0.0), *RANGES["position"]),
            "base_dimensions": _vector(b.get("base_dimensions"), (1.0, 1.0, 1.0), *RANGES["dimensions"]),
            "positions": positions, "indices": indices, "unit_volume": unit_volume}


def is_boolean(d):
    """(0.493) Whether the volume is a result of two."""
    return d is not None and d.get("source") == "boolean" and d.get("boolean") is not None


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
    out = clean(d)                      # (a new dict: its values tuples, strings, numbers)
    names = {o.get("name") for o in items}
    suffix, n = " " + copy_word, 2
    while d["name"] + suffix in names:
        suffix, n = " {} {}".format(copy_word, n), n + 1
    out.update(id=uuid.uuid4().hex[:12], name=d["name"] + suffix, locked=False)
    step = out["dimensions"][0] * out["scale"][0] * 1.2
    out["position"] = (out["position"][0] + step, out["position"][1], out["position"][2])
    return out


def volume(d):
    """Its volume, m³ (a plane: 0; (0.493) a result: the part of its box it fills)."""
    w, h, dep = (d["dimensions"][k] * d["scale"][k] for k in range(3))
    if is_boolean(d):
        return w * h * dep * d["boolean"]["unit_volume"]
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


@functools.lru_cache(maxsize=64)
def _drawn_mesh(positions, indices):
    """(0.493) A result's unit mesh to be drawn: (points, normals, triangles) — each triangle's corners its own, the
    normal of a corner the mean of the faces round its point that fold less than CREASE from its face (smooth on a
    curve, sharp at an edge)."""
    p = np.asarray(positions, dtype=float).reshape(-1, 3)
    tri = np.asarray(indices, dtype=np.int64).reshape(-1, 3)
    face = np.cross(p[tri[:, 1]] - p[tri[:, 0]], p[tri[:, 2]] - p[tri[:, 0]])    # (as long as twice its area)
    length = np.linalg.norm(face, axis=1)
    unit = face / np.where(length > 1e-15, length, 1.0)[:, None]
    corners = tri.reshape(-1)
    faces = np.repeat(np.arange(len(tri)), 3)
    order = np.argsort(corners, kind="stable")
    normals = np.zeros((len(corners), 3))
    limit = math.cos(CREASE)
    for group in np.split(order, np.flatnonzero(np.diff(corners[order])) + 1):
        f = faces[group]
        near = (unit[f] @ unit[f].T > limit).astype(float)
        normals[group] = near @ face[f]
    length = np.linalg.norm(normals, axis=1)
    normals = normals / np.where(length > 1e-15, length, 1.0)[:, None]
    return p[corners], normals, np.arange(len(corners)).reshape(-1, 3)


def shape(d):
    """(points (N, 3), normals (N, 3), triangles (M, 3)) of the volume in the model's axes."""
    if is_boolean(d):
        p, n, tri = _drawn_mesh(d["boolean"]["positions"], d["boolean"]["indices"])
    else:
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


# ------------------------------------------------------------ (0.493) two volumes combined


class BooleanError(ValueError):
    """A combination that cannot be made: its code — the Presentation's message, in i18n «pmode.dia_bool_err.<code>»."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def input_key(d):
    """The geometry of a volume as an origin (the Presentation's booleanInputKey: not its look, its eye, its lock):
    a result whose origins' keys are not the ones it was calculated with must be calculated again."""
    h = hashlib.sha1(repr((d.get("source", "primitive"), d["type"], d["dimensions"], d["position"], d["rotation"],
                           d["scale"])).encode())
    if is_boolean(d):
        h.update(np.asarray(d["boolean"]["positions"], dtype=float).tobytes())
        h.update(np.asarray(d["boolean"]["indices"], dtype=np.int64).tobytes())
    return h.hexdigest()[:20]


def dependents(items, d_id):
    """The results that have this volume as an origin."""
    return [o for o in items if is_boolean(o) and d_id in (o["boolean"]["a"], o["boolean"]["b"])]


def graph_error(items, a_id, b_id, target=None):
    """Why these two may not be combined (the Presentation's booleanGraphError), as a code, or None: the same volume
    twice, a cycle (a result made of itself), more than MAX_CHAIN operations, an origin gone, a plane (no thickness)."""
    if not a_id or not b_id or a_id == b_id:
        return "pick_different"
    by_id = {o["id"]: o for o in items}

    def visit(d_id, seen, depth):
        if d_id == target or d_id in seen:
            return "cycle"
        if depth > MAX_CHAIN:
            return "chain_limit"
        o = by_id.get(d_id)
        if o is None:
            return "source_gone"
        if o["type"] == "plane" and not is_boolean(o):
            return "plane_thin"
        if is_boolean(o):
            nxt = seen | {d_id}
            return visit(o["boolean"]["a"], nxt, depth + 1) or visit(o["boolean"]["b"], nxt, depth + 1)
        return None

    return visit(a_id, frozenset(), 1) or visit(b_id, frozenset(), 1)


def _solid(d):
    """A volume as a solid in the Presentation's axes: (points (N, 3), triangles (M, 3))."""
    if d["type"] == "plane" and not is_boolean(d):
        raise BooleanError("plane_not_solid")
    if is_boolean(d):
        p = np.asarray(d["boolean"]["positions"], dtype=float).reshape(-1, 3)
        tri = np.asarray(d["boolean"]["indices"], dtype=np.int64).reshape(-1, 3)
    else:
        p, _n, tri = unit_shape(d["type"])
    if len(tri) > MAX_TRIANGLES:
        raise BooleanError("triangle_limit")
    m = _euler(d["rotation"]) @ np.diag(d["scale"]) @ np.diag(d["dimensions"])
    return p @ m.T + TO_MODEL.T @ np.asarray(d["position"], dtype=float), np.asarray(tri, dtype=np.int64)


def _closed(points, tri, origin, extent, engine):
    """A solid for manifold (the Presentation's closedMesh): its points brought to the unit about `origin`, the seams
    of the shapes welded, the triangles fallen to a line or a point (a sphere's poles, a cone's point) left out, its
    faces outward."""
    q = (points - origin) / extent
    if not np.all(np.isfinite(q)):
        raise BooleanError("bad_coords")
    _keys, first, inverse = np.unique(np.round(q * 1e7).astype(np.int64), axis=0, return_index=True,
                                      return_inverse=True)
    t = np.asarray(inverse).reshape(-1)[tri]
    keep = (t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2])
    v = q[first]
    t = t[keep]
    area = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
    t = t[np.einsum("ij,ij->i", area, area) >= 1e-20]
    if len(t) < 4:
        raise BooleanError("not_closed")
    if float(np.einsum("ij,ij->i", v[t[:, 0]], np.cross(v[t[:, 1]], v[t[:, 2]])).sum()) < 0.0:
        t = t[:, ::-1]
    solid = engine.Manifold(engine.Mesh(vert_properties=np.array(v, dtype=np.float32, order="C"),
                                        tri_verts=np.array(t, dtype=np.uint32, order="C")))
    if solid.status() != engine.Error.NoError:
        raise BooleanError("not_closed")
    if solid.volume() <= 0.0:
        raise BooleanError("source_validation")
    return solid


def engine():
    """The manifold3d package, or None when it is not there (the combinations are then refused)."""
    try:
        import manifold3d
    except ImportError:
        return None
    return manifold3d


def calculate(a, b, operation):
    """The Presentation's calculateBoolean, here: A and B as solids, combined by `operation` — {"positions", "indices",
    "unit_volume"} (the mesh on its unit box), "position" (the middle of its box's bottom, the model's axes),
    "dimensions" (its box, the Presentation's axes), "volume" (m³). Raises BooleanError."""
    lib = engine()
    if lib is None:
        raise BooleanError("no_engine")
    if operation not in OPERATIONS:
        raise BooleanError("unknown_op")
    if a["id"] == b["id"]:
        raise BooleanError("pick_different")
    pa, ta = _solid(a)
    pb, tb = _solid(b)
    every = np.vstack((pa, pb))
    low, high = every.min(axis=0), every.max(axis=0)
    origin, extent = (low + high) / 2.0, float((high - low).max())
    if not math.isfinite(extent) or extent <= 0.0:
        raise BooleanError("bad_dimensions")
    sa, sb = _closed(pa, ta, origin, extent, lib), _closed(pb, tb, origin, extent, lib)
    result = {"union": lambda: sa + sb, "subtract": lambda: sa - sb, "reverse_subtract": lambda: sb - sa,
              "intersect": lambda: sa ^ sb, "difference": lambda: (sa - sb) + (sb - sa)}[operation]()
    if result.status() != lib.Error.NoError:
        raise BooleanError("invalid_result")
    if result.is_empty() or result.volume() <= 1e-15:
        raise BooleanError("empty_result")
    mesh = result.to_mesh()
    tri = np.array(mesh.tri_verts, dtype=np.int64).reshape(-1, 3)
    if len(tri) > MAX_TRIANGLES:
        raise BooleanError("result_triangle_limit")
    world = np.array(mesh.vert_properties, dtype=float)[:, :3] * extent + origin
    low, high = world.min(axis=0), world.max(axis=0)
    dims = high - low
    if float(dims.min()) < 0.01 or float(dims.max()) > 10000.0:
        raise BooleanError("result_range")
    base = np.array(((low[0] + high[0]) / 2.0, low[1], (low[2] + high[2]) / 2.0))
    unit = np.round((world - base) / dims, 7) + 0.0
    size = float(result.volume()) * extent ** 3
    mesh_data = {"positions": tuple(float(v) for v in unit.reshape(-1)), "indices": tuple(int(i) for i in tri.reshape(-1)),
                 "unit_volume": size / float(dims[0] * dims[1] * dims[2])}
    return dict(mesh_data, position=tuple(float(c) for c in TO_MODEL @ base),
                dimensions=tuple(float(v) for v in dims), volume=size)


def _owner_shown(items, d_id):
    """How an origin was shown before any result hid it (the Presentation's inputVisibility)."""
    owner = next((o["boolean"] for o in items if is_boolean(o) and d_id in o["boolean"]["hidden"]), None)
    if owner is not None:
        return owner["visibility"][0 if d_id == owner["a"] else 1]
    return next((o["visible"] for o in items if o["id"] == d_id), True)


def _result(items, calc, a, b, operation, label, r_id, previous, hide):
    """The result as a volume (the Presentation's makeBooleanResult): a new one named after the operation («União»,
    «União 2»…), with A's colour, solid, where its box is, not turned; one calculated again keeps its own name, look,
    turn and scale, moved as much as its box moved and sized as it was against its box. hide None: the origins it
    hides as they were."""
    names = {o["name"] for o in items if o["id"] != r_id}
    name, n = label, 2
    while name in names:
        name, n = "{} {}".format(label, n), n + 1
    base = previous["boolean"] if is_boolean(previous) else None
    out = {"id": r_id, "type": "box", "source": "boolean", "name": previous["name"] if previous else name}
    if base is not None:
        delta = np.asarray(calc["position"]) - np.asarray(base["base_position"])
        out.update(position=tuple(float(c) for c in np.asarray(previous["position"]) + delta),
                   rotation=previous["rotation"], scale=previous["scale"],
                   dimensions=tuple(calc["dimensions"][k] * previous["dimensions"][k] / base["base_dimensions"][k]
                                    for k in range(3)))
    else:
        out.update(position=calc["position"], rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0),
                   dimensions=calc["dimensions"])
    look = previous if previous is not None else dict(a, opacity=1.0, visible=True, description="")
    out.update(color=look["color"], opacity=look["opacity"], wireframe=look["wireframe"], visible=look["visible"],
               locked=False, description=look["description"])
    if hide is None and base is not None:
        hidden, shown = base["hidden"], base["visibility"]
    else:
        hidden = tuple(o["id"] for o in (a, b) if hide and not o["locked"])
        shown = (_owner_shown(items, a["id"]), _owner_shown(items, b["id"]))
    out["boolean"] = {"operation": operation, "a": a["id"], "b": b["id"], "keys": (input_key(a), input_key(b)),
                      "hidden": hidden, "visibility": shown, "base_position": calc["position"],
                      "base_dimensions": calc["dimensions"], "positions": calc["positions"],
                      "indices": calc["indices"], "unit_volume": calc["unit_volume"]}
    d = clean(out)
    if not is_boolean(d):
        raise BooleanError("save_validation")
    return d


def _committed(items, result, previous):
    """The volumes with the result put (in its place, or at the end), the origins it hides hidden, and those an
    earlier version of it hid and it no longer does shown as they were (the Presentation's commitBooleanResult)."""
    out = [result if o["id"] == result["id"] else o for o in items]
    if previous is None:
        out.append(result)
    hides = result["boolean"]["hidden"]
    before = previous["boolean"] if is_boolean(previous) else None
    for k, o in enumerate(out):
        if o["id"] == result["id"] or o["locked"]:
            continue
        if o["id"] in hides:
            out[k] = dict(o, visible=False)
        elif before is not None and o["id"] in before["hidden"] and not o["visible"] and not any(
                is_boolean(r) and o["id"] in r["boolean"]["hidden"] for r in out):
            out[k] = dict(o, visible=before["visibility"][0 if o["id"] == before["a"] else 1])
    return tuple(out[:MAX])


def combine(items, a_id, b_id, operation, label, hide=True, target=None):
    """A and B combined into a new result (or, target: that result calculated again with these): (the volumes, the
    result's id). label: the operation's name (a new result's). Raises BooleanError."""
    items = list(clean_all(items))
    error = graph_error(items, a_id, b_id, target)
    if error:
        raise BooleanError(error)
    previous = next((o for o in items if o["id"] == target), None) if target else None
    if previous is not None and previous["locked"]:
        raise BooleanError("unlock_first")
    if previous is None and len(items) >= MAX:
        raise BooleanError("full")
    a = next(o for o in items if o["id"] == a_id)
    b = next(o for o in items if o["id"] == b_id)
    calc = calculate(a, b, operation)
    r_id = previous["id"] if previous is not None else uuid.uuid4().hex[:12]
    result = _result(items, calc, a, b, operation, label, r_id, previous, hide)
    return _committed(items, result, previous), r_id


def stale(d, items, seen=frozenset()):
    """Whether a result is no longer what its origins make (the Presentation's booleanIsStale)."""
    if not is_boolean(d):
        return False
    if d["id"] in seen:
        return True
    b, by_id = d["boolean"], {o["id"]: o for o in items}
    a, c = by_id.get(b["a"]), by_id.get(b["b"])
    if a is None or c is None or (input_key(a), input_key(c)) != tuple(b["keys"]):
        return True
    return stale(a, items, seen | {d["id"]}) or stale(c, items, seen | {d["id"]})


def refreshed(items):
    """(the BIM's own) The results whose origins changed calculated again — those made of results after these —, each
    keeping its name, look, turn and scale (moved as its box moved) and the origins it hides: (the volumes, [(the
    result, the code of why it could not be)])."""
    items = list(clean_all(items))
    failed, errors = set(), []
    for _turn in range(MAX_CHAIN + 1):
        changed = False
        for k, d in enumerate(items):
            if not is_boolean(d) or d["id"] in failed:
                continue
            by_id = {o["id"]: o for o in items}
            b = d["boolean"]
            a, c = by_id.get(b["a"]), by_id.get(b["b"])
            if a is None or c is None or (input_key(a), input_key(c)) == tuple(b["keys"]):
                continue
            if any(o["id"] not in failed and stale(o, items) for o in (a, c)):
                continue                               # (an origin that is a result: after it)
            try:
                calc = calculate(a, c, b["operation"])
                items[k] = _result(items, calc, a, c, b["operation"], d["name"], d["id"], d, None)
                changed = True
            except BooleanError as e:
                failed.add(d["id"])
                errors.append((d, e.code))
        if not changed:
            break
    return tuple(items), errors


def to_presentation(d, gl_point):
    """A volume as the Presentation's DiagramObject (gl_point: the GLB's axes) — its id «bim_dia_<id>»; (0.493) a
    result with its «boolean» (its origins' ids «bim_dia_…», its mesh on the unit box; the origins' keys left to the
    Presentation's importer, which works them out as the Presentation does)."""
    out = {"id": "bim_dia_" + d["id"], "name": d["name"], "source": "primitive", "type": d["type"],
           "dimensions": [round(float(v), 6) for v in d["dimensions"]],
           "transform": {"position": [round(float(c), 6) + 0.0 for c in gl_point(d["position"])],      # (no −0)
                         "rotation": [round(float(v), 6) for v in d["rotation"]],
                         "scale": [round(float(v), 6) for v in d["scale"]]},
           "material": {"color": d["color"], "opacity": d["opacity"], "wireframe": d["wireframe"]},
           "visible": d["visible"], "locked": d["locked"], "metadata": {"description": d["description"]}}
    if is_boolean(d):
        b = d["boolean"]
        out["source"] = "boolean"
        out["boolean"] = {"version": 1, "mode": "solid", "operation": b["operation"], "inputA": "bim_dia_" + b["a"],
                          "inputB": "bim_dia_" + b["b"], "inputKeys": ["", ""], "preserveInputs": True,
                          "hiddenInputs": ["bim_dia_" + i for i in b["hidden"]],
                          "inputVisibility": [bool(v) for v in b["visibility"]],
                          "base": {"position": [round(float(c), 6) + 0.0 for c in gl_point(b["base_position"])],
                                   "dimensions": [round(float(v), 6) for v in b["base_dimensions"]]},
                          "mesh": {"positions": list(b["positions"]), "indices": list(b["indices"]),
                                   "unitVolume": round(float(b["unit_volume"]), 9)}}
    return out


def with_one(items, d):
    """The volumes with this one put (in its place when it was there, else at the end)."""
    out = list(clean_all(items))
    d = clean(d)
    if d is None:
        return tuple(out)
    for k, o in enumerate(out):
        if o["id"] == d["id"]:
            out[k] = d
            return tuple(out)
    return tuple((out + [d])[:MAX])


def without(items, d_id):
    """The volumes without this one; (0.493) a result taken away gives back the origins it hid as they were shown
    (the Presentation's removeBooleanResult — a volume that is an origin of a result is not taken: see dependents)."""
    items = list(clean_all(items))
    gone = next((o for o in items if o["id"] == d_id), None)
    out = [o for o in items if o["id"] != d_id]
    if is_boolean(gone):
        b = gone["boolean"]
        for k, o in enumerate(out):
            if o["id"] in b["hidden"] and not o["visible"] and not o["locked"] and not any(
                    is_boolean(r) and o["id"] in r["boolean"]["hidden"] for r in out):
                out[k] = dict(o, visible=b["visibility"][0 if o["id"] == b["a"] else 1])
    return tuple(out)
