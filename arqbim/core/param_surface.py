"""Parametric surfaces (0.395, as the ArqSynth addon's «Superfícies Paramétricas»): form first, construction after.

A surface is a definition (a dict, the addon's `.arqsurf` JSON, schema 1) — the only truth; the geometry is always
worked out again from it, so changing a number never loses anything:

    inputs {name: number}                 named numbers the formulas use (sliders in the Properties)
    curves [ {id, points [[x, y, z]…], closed, source?} | {id, type "expression", x, y, z, domain, n} ]
    surface {op, …}                       how the curves make a grid of points (rows × columns, maybe closed in u)
    modifiers [ {op, enabled, …} ]        that grid bent, twisted, waved… in order
    build {section: {…}}                  the construction made on it (core/surface_build.py)

The ops: «grid» (z = formula of u, v, x, y over a rectangle), «loft» (through 2+ sections, smooth across them, each
section turned and shifted to match the one before: no twist), «coons» (4 edges), «revolve» (a profile round a
vertical axis), «extrude» (a profile along a direction), «sweep» (a profile along a path, carried without
flipping) and «patch» (over a closed outline: its rings toward the middle or a grid of its four sides, raised as a
cosine cap, the membrane dome, a vault or a wave of core/organic_roof.py — or flat).

The modifiers: displace, attractor (to a point or a curve), taper, twist, shear, wave, relax, bend, trim (a closed
curve in plan: the faces kept inside or outside it).

Pure numpy (and shapely for the plan tests), metres, the element's own coordinates."""

import copy
import json
import math

import numpy as np

from . import surface_expr as expr

SCHEMA = 1
OPS = ("grid", "loft", "coons", "revolve", "extrude", "sweep", "patch",
       "organic",                     # (0.555) a form found over a closed outline (core/form_finding)
       "blobs")                       # (0.560) masses melted together (metaballs), a closed volume
VOLUMES = ("aberta", "assente", "lente")   # (0.560) an organic form open, or closed: on a flat base, or a lens
CLOSED = ("assente", "lente")
ORGANIC_KINDS = ("membrana", "almofada", "catenaria", "suavizar")
POINT_KINDS = ("mastro", "apoio")
LINE_KINDS = ("cumeeira", "vale")       # (0.556) a line held at a height: a ridge (up) or a valley (down)
EDGE_CABLE = 4.0                        # (0.556) a free edge's cable: this many times the membrane's pull
PATCH_FORMS = ("cosseno", "cupula", "abobada", "onda", "plano")
PATCH_GRIDS = ("quadras", "aneis")
MODIFIERS = ("displace", "attractor", "taper", "twist", "shear", "wave", "relax", "bend", "trim")
ALONG = ("normal", "x", "y", "z")
FALLOFFS = ("gauss", "linear", "inverse")
MAX_INPUTS = 32
MAX_CURVES = 16
MAX_CURVE_SAMPLES = 2048
MAX_DIVISIONS = 512
MAX_CELLS = 65536
POLE_EPS = 1e-6
COONS_GAP = 0.05            # m: four edges that do not meet closer than this do not make a patch
TRIM_SAMPLES = 96
ATTRACTOR_SAMPLES = 64

# what each op needs of its curves, and its default fields
OP_DEFAULTS = {
    "grid": {"u": 32, "v": 20, "width": "L", "depth": "W", "z": "H*sin(pi*u)*sin(pi*v)"},
    "loft": {"sections": [], "u": 32, "v": 8, "smooth": True},
    "coons": {"edges": [], "u": 24, "v": 24},
    "revolve": {"profile": "", "u": 32, "v": 16, "angle": 360.0, "origin": [0.0, 0.0]},
    "extrude": {"profile": "", "u": 32, "v": 8, "direction": [0.0, 0.0, 3.0]},
    "sweep": {"path": "", "profile": "", "u": 16, "v": 32},
    "patch": {"boundary": "", "u": 24, "v": 16, "rise": 2.0, "form": "cupula", "grid": "quadras"},
    # (0.555) «behaviour» the forces (form_finding); «height» how high it rises (negative: hangs); «points» masts
    # and supports — {"u", "v" (m, in the outline's plane), "h" (m off it), "r" (m, the head's radius), "kind"}
    "organic": {"boundary": "", "u": 28, "v": 28, "grid": "quadras", "behaviour": "catenaria", "height": 2.0,
                "points": []},
    # (0.560) balls {"x", "y", "z", "r"} (m) melted into one volume; «fusion» how much they melt (1: barely)
    "blobs": {"balls": [], "u": 40, "v": 24, "fusion": 2.0},
}
OP_CURVES = {"grid": (0, 0), "loft": (2, MAX_CURVES), "coons": (4, 4), "revolve": (1, 1), "extrude": (1, 1),
             "sweep": (2, 2), "patch": (1, 1), "organic": (1, 1), "blobs": (0, 0)}

MODIFIER_TEMPLATES = {
    "displace": {"along": "normal", "amount": "0.3*sin(2*pi*u)"},
    "attractor": {"point": [0.0, 0.0, 0.0], "curve": "", "falloff": "gauss", "radius": 3.0, "amount": 1.0,
                  "along": "normal"},
    "taper": {"axis": "v", "factor": "1 - 0.4*v"},
    "twist": {"axis": "z", "angle": "45*v"},
    "shear": {"axis": "x", "by": "z", "amount": 1.0},
    "wave": {"along": "normal", "amplitude": 0.3, "u_waves": 2.0, "v_waves": 0.0, "phase": 0.0},
    "relax": {"iterations": 5, "factor": 0.5},
    "bend": {"axis": "x", "toward": "z", "angle": 60.0},
    "trim": {"curve": "", "keep": "inside"},
}
XYZ = ("x", "y", "z")
# each modifier's fields that are a choice, and their choices
MODIFIER_FIELDS = {"displace": {"along": ALONG}, "attractor": {"along": ALONG, "falloff": FALLOFFS},
                   "taper": {"axis": ("u", "v") + XYZ}, "twist": {"axis": XYZ}, "shear": {"axis": XYZ, "by": XYZ},
                   "wave": {"along": ALONG}, "relax": {}, "bend": {"axis": XYZ, "toward": XYZ},
                   "trim": {"keep": ("inside", "outside")}}


class SurfaceError(ValueError):
    """A definition that cannot make a surface: its message says why, in words (the addon's)."""


# ---------------------------------------------------------------- the definition

def default_definition(op="grid", name="Superfície"):
    data = {"arqsurf": SCHEMA, "name": name, "units": "m", "inputs": {}, "curves": [],
            "surface": dict({"op": op}, **copy.deepcopy(OP_DEFAULTS[op])), "modifiers": [], "build": {}}
    if op == "grid":
        data["inputs"] = {"L": 12.0, "W": 8.0, "H": 1.2}
    return data


def blob_balls_text(data):
    return ", ".join("r {:.2f}".format(float(q["r"])) for q in (data.get("surface") or {}).get("balls") or ())


def dumps(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def loads(text):
    """(definition, errors) of a JSON text — never raises."""
    try:
        data = json.loads(text)
    except (TypeError, ValueError) as exc:
        return None, ["JSON inválido: {}".format(exc)]
    errors = validate(data)
    return (data if not errors else None), errors


def curve_ids(data):
    return [c.get("id") for c in data.get("curves") or () if isinstance(c, dict)]


def used_curves(data):
    """The ids of the curves the surface's op uses, in their order."""
    s = data.get("surface") or {}
    op = s.get("op")
    if op == "loft":
        return list(s.get("sections") or ())
    if op == "coons":
        return list(s.get("edges") or ())
    if op in ("revolve", "extrude"):
        return [s.get("profile")] if s.get("profile") else []
    if op == "sweep":
        return [x for x in (s.get("path"), s.get("profile")) if x]
    if op in ("patch", "organic"):
        return [s.get("boundary")] if s.get("boundary") else []
    return []


def validate(data):
    """Every problem of a definition, in words with where it is ([] when it can be made)."""
    errors = []
    if not isinstance(data, dict):
        return ["a definição tem de ser um objeto JSON"]
    version = data.get("arqsurf")
    if not isinstance(version, int) or isinstance(version, bool):
        errors.append("arqsurf: falta a versão (número inteiro)")
    elif version > SCHEMA:
        errors.append("arqsurf: a versão {} é mais recente do que este programa ({})".format(version, SCHEMA))
    inputs = data.get("inputs") or {}
    if not isinstance(inputs, dict):
        errors.append("inputs: tem de ser {nome: número}")
        inputs = {}
    if len(inputs) > MAX_INPUTS:
        errors.append("inputs: no máximo {}".format(MAX_INPUTS))
    for k, v in inputs.items():
        if not isinstance(k, str) or not k.isidentifier() or k in expr.RESERVED:
            errors.append("inputs.{}: nome inválido ou reservado".format(k))
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
            errors.append("inputs.{}: tem de ser um número".format(k))
    env = {k: float(v) for k, v in inputs.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
    curves = data.get("curves") or []
    ids = []
    if not isinstance(curves, list):
        errors.append("curves: tem de ser uma lista")
        curves = []
    if len(curves) > MAX_CURVES:
        errors.append("curves: no máximo {}".format(MAX_CURVES))
    for k, c in enumerate(curves):
        where = "curves[{}]".format(k)
        if not isinstance(c, dict) or not isinstance(c.get("id"), str) or not c.get("id"):
            errors.append("{}: falta o id".format(where))
            continue
        if c["id"] in ids:
            errors.append("{}: id repetido '{}'".format(where, c["id"]))
        ids.append(c["id"])
        if c.get("type") == "expression":
            n = c.get("n", 96)
            if not isinstance(n, int) or not 2 <= n <= MAX_CURVE_SAMPLES:
                errors.append("{}.n: inteiro de 2 a {}".format(where, MAX_CURVE_SAMPLES))
            for axis in ("x", "y", "z"):
                try:
                    expr.field(c.get(axis, 0.0), env, ("t",), "{}.{}".format(where, axis))
                except expr.ExprError as exc:
                    errors.append(str(exc))
        else:
            pts = c.get("points")
            try:
                arr = np.asarray(pts, dtype=float)
                if arr.ndim != 2 or arr.shape[1] != 3 or len(arr) < 2 or not np.all(np.isfinite(arr)):
                    raise ValueError
            except (TypeError, ValueError):
                errors.append("{}: precisa de 'points' [[x, y, z]…] (2 ou mais) ou type='expression'".format(where))
    s = data.get("surface")
    if not isinstance(s, dict) or s.get("op") not in OPS:
        errors.append("surface.op: um de {}".format(", ".join(OPS)))
        return errors
    op = s["op"]
    for key in ("u", "v"):
        n = s.get(key, OP_DEFAULTS[op][key])
        if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= MAX_DIVISIONS:
            errors.append("surface.{}: inteiro de 1 a {}".format(key, MAX_DIVISIONS))
    if op == "grid":
        for key in ("width", "depth"):
            try:
                if expr.number(s.get(key, OP_DEFAULTS["grid"][key]), env, "surface." + key) <= 0:
                    errors.append("surface.{}: tem de ser positivo".format(key))
            except expr.ExprError as exc:
                errors.append(str(exc))
        try:
            expr.field(s.get("z", 0.0), env, ("u", "v", "x", "y", "i", "j", "nu", "nv"), "surface.z")
        except expr.ExprError as exc:
            errors.append(str(exc))
    used = used_curves(data)
    lo, hi = OP_CURVES[op]
    if not lo <= len(used) <= hi:
        errors.append("surface ({}): precisa de {} curva(s), tem {}".format(
            op, lo if lo == hi else "{} ou mais".format(lo), len(used)))
    for cid in used:
        if cid not in ids:
            errors.append("surface: a curva '{}' não existe (há: {})".format(cid, ", ".join(ids) or "nenhuma"))
    if op == "patch":
        if s.get("form", "cupula") not in PATCH_FORMS:
            errors.append("surface.form: um de {}".format(", ".join(PATCH_FORMS)))
        if s.get("grid", "quadras") not in PATCH_GRIDS:
            errors.append("surface.grid: um de {}".format(", ".join(PATCH_GRIDS)))
    if op == "organic":                               # (0.555)
        if s.get("behaviour", "catenaria") not in ORGANIC_KINDS:
            errors.append("surface.behaviour: um de {}".format(", ".join(ORGANIC_KINDS)))
        if s.get("grid", "quadras") not in PATCH_GRIDS:
            errors.append("surface.grid: um de {}".format(", ".join(PATCH_GRIDS)))
        points = s.get("points") or []
        if not isinstance(points, list):
            errors.append("surface.points: tem de ser uma lista")
            points = []
        for k, q in enumerate(points):
            try:
                ok = isinstance(q, dict) and q.get("kind", "mastro") in POINT_KINDS and all(
                    math.isfinite(float(q.get(key, 0.0))) for key in ("u", "v", "h", "r"))
            except (TypeError, ValueError):
                ok = False
            if not ok:
                errors.append("surface.points[{}]: {{u, v, h, r, kind: {}}}".format(k, "|".join(POINT_KINDS)))
        lines = s.get("lines") or []
        if not isinstance(lines, list):
            errors.append("surface.lines: tem de ser uma lista")
            lines = []
        for k, q in enumerate(lines):                 # (0.556)
            try:
                ok = isinstance(q, dict) and q.get("kind", "cumeeira") in LINE_KINDS and \
                    len(q.get("a") or ()) == 2 and len(q.get("b") or ()) == 2 and math.isfinite(float(q.get("h", 0)))
                ok = ok and all(math.isfinite(float(c)) for c in list(q["a"]) + list(q["b"]))
            except (TypeError, ValueError):
                ok = False
            if not ok:
                errors.append("surface.lines[{}]: {{a: [u, v], b: [u, v], h, kind: {}}}".format(
                    k, "|".join(LINE_KINDS)))
        for k, q in enumerate(s.get("holes") or []):  # (0.557) oculi
            try:
                ok = isinstance(q, dict) and float(q.get("r", 0)) > 0 and all(
                    math.isfinite(float(q.get(key, 0.0))) for key in ("u", "v", "h"))
            except (TypeError, ValueError):
                ok = False
            if not ok:
                errors.append("surface.holes[{}]: {{u, v, r (> 0), h}}".format(k))
        if s.get("volume", "") not in VOLUMES + ("",):   # (0.560)
            errors.append("surface.volume: um de {}".format(", ".join(VOLUMES)))
        if not isinstance(s.get("free_edges", False), bool):
            errors.append("surface.free_edges: verdadeiro ou falso")
    if op == "blobs":                                 # (0.560)
        balls = s.get("balls") or []
        if not isinstance(balls, list) or not balls:
            errors.append("surface.balls: pelo menos uma massa {x, y, z, r}")
            balls = []
        for k, q in enumerate(balls):
            try:
                ok = isinstance(q, dict) and float(q.get("r", 0)) > 0 and all(
                    math.isfinite(float(q.get(key, 0.0))) for key in ("x", "y", "z"))
            except (TypeError, ValueError):
                ok = False
            if not ok:
                errors.append("surface.balls[{}]: {{x, y, z, r (> 0)}}".format(k))
    for key in ("angle", "rise", "height", "fusion"):
        if key in s:
            try:
                expr.number(s[key], env, "surface." + key)
            except expr.ExprError as exc:
                errors.append(str(exc))
    mods = data.get("modifiers") or []
    if not isinstance(mods, list):
        errors.append("modifiers: tem de ser uma lista")
        mods = []
    for k, m in enumerate(mods):
        where = "modifiers[{}]".format(k)
        if not isinstance(m, dict) or m.get("op") not in MODIFIERS:
            errors.append("{}: op um de {}".format(where, ", ".join(MODIFIERS)))
            continue
        for key, choices in MODIFIER_FIELDS.get(m["op"], {}).items():
            if key in m and m[key] not in choices:
                errors.append("{} ({}).{}: um de {}".format(where, m["op"], key, ", ".join(choices)))
        if m["op"] in ("shear",) and m.get("axis") == m.get("by"):
            errors.append("{} (shear): axis e by têm de ser diferentes".format(where))
        if m["op"] in ("bend",) and m.get("axis") == m.get("toward"):
            errors.append("{} (bend): axis e toward têm de ser diferentes".format(where))
        if m["op"] in ("trim",) and m.get("curve") not in ids:
            errors.append("{} (trim): escolha uma curva fechada".format(where))
        if m["op"] == "attractor" and m.get("curve") and m.get("curve") not in ids:
            errors.append("{} (attractor): a curva '{}' não existe".format(where, m.get("curve")))
    build = data.get("build") or {}
    if not isinstance(build, dict):
        errors.append("build: tem de ser um objeto")
    else:
        from .surface_build import SECTIONS
        for key in build:
            if key not in SECTIONS:
                errors.append("build.{}: secção desconhecida".format(key))
    return errors


# ---------------------------------------------------------------- curves

def resample(points, count, closed):
    """`count` points evenly along the polyline (both ends included; closed: round it, the first not repeated)."""
    p = np.asarray(points, dtype=float).reshape(-1, 3)
    if closed:
        p = np.vstack((p, p[:1]))
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    cum = np.concatenate(([0.0], np.cumsum(seg)))
    total = float(cum[-1])
    if total < 1e-12:
        raise SurfaceError("curva degenerada (comprimento zero)")
    keep = np.concatenate(([True], seg > 1e-12))
    p, cum = p[keep], cum[keep]
    targets = total * np.arange(count) / (count if closed else max(count - 1, 1))
    return np.column_stack([np.interp(targets, cum, p[:, k]) for k in range(3)])


def sample_curve(curve, env):
    """(points (k, 3), closed) of a curve of the definition."""
    if curve.get("type") == "expression":
        n = int(curve.get("n", 96))
        t0, t1 = (float(x) for x in (curve.get("domain") or (0.0, 1.0)))
        fns = [expr.field(curve.get(a, 0.0), env, ("t",), "curva {}.{}".format(curve.get("id"), a))
               for a in ("x", "y", "z")]
        t = t0 + (t1 - t0) * np.arange(n) / (n - 1)
        pts = np.column_stack([np.broadcast_to(np.asarray(fn(t=t), dtype=float), t.shape) for fn in fns])
        closed = float(np.linalg.norm(pts[0] - pts[-1])) < 1e-6
        if closed:
            t = t0 + (t1 - t0) * np.arange(n) / n
            pts = np.column_stack([np.broadcast_to(np.asarray(fn(t=t), dtype=float), t.shape) for fn in fns])
        return pts, closed
    pts = np.asarray(curve["points"], dtype=float).reshape(-1, 3)
    closed = bool(curve.get("closed"))
    if closed and len(pts) > 2 and np.linalg.norm(pts[0] - pts[-1]) < 1e-9:
        pts = pts[:-1]
    if len(pts) < 2:
        raise SurfaceError("a curva '{}' tem menos de 2 pontos".format(curve.get("id")))
    return pts, closed


def _curves(data, env):
    out = {}
    for c in data.get("curves") or ():
        out[c["id"]] = sample_curve(c, env)
    return out


def align_section(previous, current, closed):
    """`current` turned (its direction) and shifted (its start) to lie as `previous` does: no twist in a loft."""
    prev, cur = np.asarray(previous, float), np.asarray(current, float)
    if not closed:
        rev = cur[::-1]
        a = np.linalg.norm(prev[0] - cur[0]) + np.linalg.norm(prev[-1] - cur[-1])
        b = np.linalg.norm(prev[0] - rev[0]) + np.linalg.norm(prev[-1] - rev[-1])
        return cur if a <= b else rev
    n = len(cur)
    best, out = None, cur
    for cand in (cur, cur[::-1]):
        idx = (np.arange(n)[None, :] + np.arange(n)[:, None]) % n        # (shift, i)
        cost = np.linalg.norm(cand[idx] - prev[None, :, :], axis=2).sum(axis=1)
        k = int(np.argmin(cost))
        if best is None or cost[k] < best:
            best, out = float(cost[k]), cand[idx[k]]
    return out


def _catmull(p0, p1, p2, p3, t):
    return 0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3)


def _need(curves, cid, closed=None, what=""):
    if cid not in curves:
        raise SurfaceError("a curva '{}' não existe".format(cid))
    pts, is_closed = curves[cid]
    if closed is True and not is_closed:
        raise SurfaceError("{}: a curva '{}' tem de ser fechada".format(what or "superfície", cid))
    return pts, is_closed


# ---------------------------------------------------------------- the ops: a grid of points (rows (v) × columns (u))

def _rows_grid(data, env, curves):
    s = data["surface"]
    nu, nv = int(s.get("u", 32)), int(s.get("v", 20))
    if (nu + 1) * (nv + 1) > MAX_CELLS:
        raise SurfaceError("grelha grande demais (no máximo {} pontos)".format(MAX_CELLS))
    width = expr.number(s.get("width", 12.0), env, "surface.width")
    depth = expr.number(s.get("depth", 8.0), env, "surface.depth")
    if width <= 0 or depth <= 0:
        raise SurfaceError("surface: largura e profundidade têm de ser positivas")
    j, i = np.meshgrid(np.arange(nv + 1, dtype=float), np.arange(nu + 1, dtype=float), indexing="ij")
    u, v = i / nu, j / nv
    x, y = u * width, v * depth
    fn = expr.field(s.get("z", 0.0), env, ("u", "v", "x", "y", "i", "j", "nu", "nv"), "surface.z")
    z = np.broadcast_to(np.asarray(fn(u=u, v=v, x=x, y=y, i=i, j=j, nu=float(nu), nv=float(nv)), dtype=float),
                        u.shape)
    return np.stack((x, y, z), axis=-1), False


def _rows_loft(data, env, curves):
    s = data["surface"]
    ids = list(s.get("sections") or ())
    if len(ids) < 2:
        raise SurfaceError("o loft precisa de 2 ou mais secções")
    secs = [_need(curves, cid) for cid in ids]
    closed = all(c for _p, c in secs)
    nu = int(s.get("u", 32))
    sections = [resample(p, nu if closed else nu + 1, closed) for p, _c in secs]
    for k in range(1, len(sections)):
        sections[k] = align_section(sections[k - 1], sections[k], closed)
    steps = max(1, int(s.get("v", 8)))
    smooth = bool(s.get("smooth", True)) and len(sections) >= 3
    rows, count = [], len(sections)
    for g in range(count - 1):
        p1, p2 = sections[g], sections[g + 1]
        p0 = sections[g - 1] if g > 0 else 2 * p1 - p2
        p3 = sections[g + 2] if g + 2 < count else 2 * p2 - p1
        for step in range(steps + (1 if g == count - 2 else 0)):
            t = step / steps
            rows.append(_catmull(p0, p1, p2, p3, t) if smooth else p1 + (p2 - p1) * t)
    return np.asarray(rows), closed


def _rows_coons(data, env, curves):
    s = data["surface"]
    ids = list(s.get("edges") or ())
    if len(ids) != 4:
        raise SurfaceError("a superfície por 4 bordos precisa de 4 curvas")
    nu, nv = int(s.get("u", 24)), int(s.get("v", 24))
    c0, c1, c2, c3 = (resample(_need(curves, cid)[0], n, False) for cid, n in zip(ids, (nu + 1, nv + 1, nu + 1,
                                                                                         nv + 1)))
    ends = [c0[0], c0[-1]]
    # the four in a chain: each turned to start where the one before ends (the addon's, and any order of drawing)
    if np.linalg.norm(c0[-1] - c1[0]) > np.linalg.norm(c0[-1] - c1[-1]):
        c1 = c1[::-1]
    if np.linalg.norm(c1[-1] - c2[-1]) > np.linalg.norm(c1[-1] - c2[0]):
        c2 = c2[::-1]
    if np.linalg.norm(c0[0] - c3[0]) > np.linalg.norm(c0[0] - c3[-1]):
        c3 = c3[::-1]
    gap = max(np.linalg.norm(c0[-1] - c1[0]), np.linalg.norm(c1[-1] - c2[-1]), np.linalg.norm(c0[0] - c3[0]),
              np.linalg.norm(c3[-1] - c2[0]))
    if gap > COONS_GAP:
        raise SurfaceError("os 4 bordos não fecham (folga {:.2f} m) — as curvas têm de se tocar nas pontas".format(
            gap))
    del ends
    u = (np.arange(nu + 1) / nu)[None, :, None]
    v = (np.arange(nv + 1) / nv)[:, None, None]
    p00, p10, p01, p11 = c0[0], c0[-1], c2[0], c2[-1]
    rows = ((1 - v) * c0[None, :, :] + v * c2[None, :, :] + (1 - u) * c3[:, None, :] + u * c1[:, None, :]
            - ((1 - u) * (1 - v) * p00 + u * (1 - v) * p10 + (1 - u) * v * p01 + u * v * p11))
    return rows, False


def _rot_z(points, angle, pivot):
    c, s_ = math.cos(angle), math.sin(angle)
    d = points - pivot
    return pivot + np.column_stack((d[:, 0] * c - d[:, 1] * s_, d[:, 0] * s_ + d[:, 1] * c, d[:, 2]))


def _rows_revolve(data, env, curves):
    s = data["surface"]
    pts, _closed = _need(curves, s.get("profile"))
    nu, nv = int(s.get("u", 32)), int(s.get("v", 16))
    profile = resample(pts, nv + 1, False)
    angle = expr.number(s.get("angle", 360.0), env, "surface.angle")
    full = abs(abs(angle) - 360.0) < 1e-6
    ox, oy = (float(c) for c in (s.get("origin") or (0.0, 0.0))[:2])
    pivot = np.array((ox, oy, 0.0))
    steps = nu if full else nu + 1
    rows = np.stack([_rot_z(profile, math.radians(angle) * i / nu, pivot) for i in range(steps)], axis=1)
    return rows, full


def _rows_extrude(data, env, curves):
    s = data["surface"]
    pts, closed = _need(curves, s.get("profile"))
    nu, nv = int(s.get("u", 32)), int(s.get("v", 8))
    d = np.array([expr.number(c, env, "surface.direction") for c in (s.get("direction") or (0, 0, 3))[:3]])
    if np.linalg.norm(d) < 1e-9:
        raise SurfaceError("surface.direction: a direção não pode ser nula")
    profile = resample(pts, nu if closed else nu + 1, closed)
    rows = np.stack([profile + d * (j / nv) for j in range(nv + 1)])
    return rows, closed


def _rotate(v, axis, angle):
    c, s_ = math.cos(angle), math.sin(angle)
    return v * c + np.cross(axis, v) * s_ + axis * float(axis @ v) * (1 - c)


def _rows_sweep(data, env, curves):
    s = data["surface"]
    path, _pc = _need(curves, s.get("path"))
    prof, closed = _need(curves, s.get("profile"))
    nu, nv = int(s.get("u", 16)), int(s.get("v", 32))
    path = resample(path, nv + 1, False)
    profile = resample(prof, nu if closed else nu + 1, closed)
    local = profile - profile.mean(axis=0)
    tangents = np.gradient(path, axis=0)
    norms = np.linalg.norm(tangents, axis=1)
    tangents = np.where(norms[:, None] > 1e-12, tangents / np.maximum(norms, 1e-12)[:, None], (0.0, 0.0, 1.0))
    up = np.array((0.0, 0.0, 1.0)) if abs(tangents[0][2]) <= 0.9 else np.array((0.0, 1.0, 0.0))
    normal = up - tangents[0] * float(up @ tangents[0])
    normal /= np.linalg.norm(normal)
    rows = []
    for j in range(nv + 1):
        t = tangents[j]
        if j:
            axis = np.cross(tangents[j - 1], t)
            if np.linalg.norm(axis) > 1e-9:
                ang = math.acos(max(-1.0, min(1.0, float(tangents[j - 1] @ t))))
                normal = _rotate(normal, axis / np.linalg.norm(axis), ang)
            normal = normal - t * float(normal @ t)
            normal /= max(np.linalg.norm(normal), 1e-12)
        binormal = np.cross(t, normal)
        binormal /= max(np.linalg.norm(binormal), 1e-12)
        rows.append(path[j] + local[:, :1] * normal + local[:, 1:2] * binormal + local[:, 2:3] * t)
    return np.asarray(rows), closed


def _four_sides(ring):
    """The closed outline cut in four at its extremes (bottom-left, bottom-right, top-right, top-left of its plan,
    diagonally): its sides (bottom, right, top, left), each as it runs for a Coons patch."""
    k = len(ring)
    xy = ring[:, :2] - ring[:, :2].mean(axis=0)
    s, d = xy.sum(axis=1), xy[:, 0] - xy[:, 1]
    bl, tr, br, tl = int(s.argmin()), int(s.argmax()), int(d.argmax()), int(d.argmin())
    if len({bl, tr, br, tl}) < 4:
        raise SurfaceError("o contorno é pequeno ou estreito demais para uma grelha de quatro lados")

    def path(i, j, score):
        f = ring[np.arange(i, i + ((j - i) % k) + 1) % k]
        b = ring[np.arange(i, i - ((i - j) % k) - 1, -1) % k]
        return f if score(f) <= score(b) else b

    bottom = path(bl, br, lambda p: p[:, 1].mean())
    top = path(tl, tr, lambda p: -p[:, 1].mean())
    left = path(bl, tl, lambda p: p[:, 0].mean())
    right = path(br, tr, lambda p: -p[:, 0].mean())
    return bottom, right, top, left


def outline_frame(points):
    """(0.555) (origin, x, y, normal) of a closed outline's plane: x level where the plane allows it, the normal up
    for a lying outline (otherwise the way its points run round)."""
    from .mesh import polygon_normal
    p = np.asarray(points, dtype=float)
    n = polygon_normal(p)
    if np.linalg.norm(n) < 1e-9:
        raise SurfaceError("o contorno não tem área (pontos em linha)")
    if n[2] < -0.7:                                    # (a lying outline: its form rises up)
        n = -n
    x = np.cross((0.0, 0.0, 1.0), n)
    if np.linalg.norm(x) < 1e-6:
        x = np.array((1.0, 0.0, 0.0))
    x = x / np.linalg.norm(x)
    return p.mean(axis=0), x, np.cross(n, x), n


def _boundary_grid(pts, nu, nv, grid):
    """(rows, close_u) of a closed outline (its points as given, any plane of z = 0): four sides (Coons) or rings
    to its middle."""
    if grid == "quadras":
        ring = resample(pts, max(4 * (nu + nv), 64), True)
        b, r, t, l_ = _four_sides(ring)
        c0, c2 = resample(b, nu + 1, False), resample(t, nu + 1, False)
        c3, c1 = resample(l_, nv + 1, False), resample(r, nv + 1, False)
        u = (np.arange(nu + 1) / nu)[None, :, None]
        v = (np.arange(nv + 1) / nv)[:, None, None]
        rows = ((1 - v) * c0[None] + v * c2[None] + (1 - u) * c3[:, None] + u * c1[:, None]
                - ((1 - u) * (1 - v) * c0[0] + u * (1 - v) * c0[-1] + (1 - u) * v * c2[0] + u * v * c2[-1]))
        return np.array(rows), False
    ring = resample(pts, nu, True)
    c = ring.mean(axis=0)
    tt = (np.arange(nv + 1) / nv)[:, None, None]
    return np.array(ring[None] + (c - ring)[None] * tt), True


def _beside(mask, close_u):
    """The points with a neighbour in `mask` — along the grid's lines or across a cell (its diagonals: every point
    a kept cell shares with an outside point)."""
    rows_near = mask.copy()
    rows_near[1:] |= mask[:-1]
    rows_near[:-1] |= mask[1:]
    out = rows_near.copy()
    if close_u:
        out |= np.roll(rows_near, 1, axis=1) | np.roll(rows_near, -1, axis=1)
    else:
        out[:, 1:] |= rows_near[:, :-1]
        out[:, :-1] |= rows_near[:, 1:]
    return out


def organic_cut(data, rows):
    """(0.557) The grid's points inside an organic form's oculi ((nr, nc) bool; None: no oculus) — a cell with all
    its corners inside is left out of the surface."""
    s = data.get("surface") or {}
    holes = s.get("holes") or []
    if s.get("op") != "organic" or not holes:
        return None
    curve = next((c for c in data.get("curves") or () if c.get("id") == s.get("boundary")), None)
    if curve is None:
        return None
    pts, _closed = sample_curve(curve, {k: float(v) for k, v in (data.get("inputs") or {}).items()})
    o, x, y, _n = outline_frame(pts)
    uv = (np.asarray(rows, float) - o) @ np.stack((x, y)).T
    cut = np.zeros(uv.shape[:2], dtype=bool)
    cell = float(np.median(np.linalg.norm(np.diff(uv, axis=1), axis=-1)))
    for q in holes:                                   # (as the form was found: a ring at least half a cell wide)
        r = max(float(q["r"]), cell * 0.5)
        d = np.hypot(uv[..., 0] - float(q["u"]), uv[..., 1] - float(q["v"]))
        cut |= d <= r * (1 + 1e-6) + 1e-9
    return cut


def centre_mast(local, height):
    """(0.556) The mast a membrane with none stands on: in its outline's middle, `height` high."""
    size = float(np.ptp(np.asarray(local)[:, :2], axis=0).max())
    return [{"u": round(float(np.mean(local[:, 0])), 3), "v": round(float(np.mean(local[:, 1])), 3),
             "h": float(height), "r": round(0.06 * size, 3), "kind": "mastro"}]


def implicit_points(data):
    """(0.556) The masts an organic form stands on without any given: a membrane's mast in its middle — so that the
    first one put by hand joins it instead of taking its place."""
    s = data.get("surface") or {}
    if s.get("behaviour") != "membrana" or s.get("points") or s.get("lines"):
        return []
    curve = next((c for c in data.get("curves") or () if c.get("id") == s.get("boundary")), None)
    if curve is None:
        return []
    pts, _closed = sample_curve(curve, {k: float(v) for k, v in (data.get("inputs") or {}).items()})
    o, x, y, n = outline_frame(pts)
    local = (pts - o) @ np.stack((x, y, n)).T
    return centre_mast(local, expr.number(s.get("height", 2.0), {}, "surface.height"))


def _rows_organic(data, env, curves):
    """(0.555) A form found over a closed outline in any plane (a floor's, a wall's face, a polygon drawn): its grid
    laid in the outline's plane, its edge held, masts and supports held at their heights, the forces of its
    behaviour (form_finding) — then put back in the element's coordinates."""
    from . import form_finding as ff
    s = data["surface"]
    pts, _closed = _need(curves, s.get("boundary"), closed=True, what="a forma orgânica")
    nu, nv = int(s.get("u", 28)), int(s.get("v", 28))
    grid = "aneis" if s.get("volume") in CLOSED else s.get("grid", "quadras")    # (0.560: a volume closes round)
    behaviour = s.get("behaviour", "catenaria")
    height = expr.number(s.get("height", 2.0), env, "surface.height")
    o, x, y, n = outline_frame(pts)
    axes = np.stack((x, y, n))
    local = (pts - o) @ axes.T
    local[:, 2] = 0.0
    rows, close_u = _boundary_grid(local, nu, nv, grid)
    rows[..., 2] = 0.0
    edge = ff.boundary_mask(rows.shape, close_u)
    if close_u:                                         # (rings: only the outer one is the edge)
        edge[-1] = False
    free_edges = bool(s.get("free_edges", False))
    if free_edges:                                      # (0.556) only the outline's corners held: its edges sag in
        fixed = np.zeros_like(edge)
        for c in local[:, :2]:
            d = np.where(edge, np.hypot(rows[..., 0] - c[0], rows[..., 1] - c[1]), np.inf)
            fixed[np.unravel_index(int(np.argmin(d)), d.shape)] = True
    else:
        fixed = edge.copy()
    held_edge = fixed.copy()                            # (0.557: the edge alone — the load is found on it)
    points = list(s.get("points") or ())
    lines = list(s.get("lines") or ())
    if behaviour == "membrana" and not points and not lines:   # (a membrane needs something to lift it: a mast)
        points = centre_mast(local, height)
    k = EDGE_CABLE if free_edges else 1.0
    flat = ff.plan_grid(rows, edge, close_u)            # (the plan spread with its whole edge — then let go)
    cell = float(np.median(np.linalg.norm(np.diff(flat[..., :2], axis=1), axis=-1)))
    for q in points:                                    # (each mast's head — or support's foot — held at its height)
        r = max(float(q.get("r", 0.0)), 1e-9)
        d = np.hypot(flat[..., 0] - float(q.get("u", 0.0)), flat[..., 1] - float(q.get("v", 0.0)))
        near = d <= r
        if not near.any():
            near = d == d.min()
        flat[..., 2] = np.where(near, float(q.get("h", 0.0)), flat[..., 2])
        fixed |= near
    rings = []
    for q in s.get("holes") or ():                     # (0.557) an oculus: a rigid ring, nothing inside
        c, r = np.array((float(q["u"]), float(q["v"]))), max(float(q["r"]), cell * 0.5)
        rel = flat[..., :2] - c
        d = np.linalg.norm(rel, axis=-1)
        inside = d < r
        out = ~inside
        rim = inside & _beside(out, close_u)            # (the points just inside: put on the ring itself)
        safe = np.where(d > 1e-9, d, 1.0)[..., None]
        flat[..., :2] = np.where(rim[..., None], c + rel / safe * r, flat[..., :2])
        flat[..., 2] = np.where(inside, float(q.get("h", 0.0)), flat[..., 2])
        if q.get("held"):                               # (held at its height: on a mast, on a wall)
            fixed |= inside
        else:                                           # (free: it rises or sinks with the form, as one)
            rings.append(inside)
    for q in lines:                                     # (0.556) a ridge or a valley: its points held at its height
        a, b = np.asarray(q["a"], float), np.asarray(q["b"], float)
        ab = b - a
        t = np.clip(((flat[..., :2] - a) @ ab) / max(float(ab @ ab), 1e-12), 0.0, 1.0)
        d = np.linalg.norm(flat[..., :2] - (a + t[..., None] * ab), axis=-1)
        near = d <= cell * 0.55
        flat[..., 2] = np.where(near, float(q.get("h", 0.0)), flat[..., 2])
        fixed |= near
    try:
        form = ff.find(flat, behaviour, height, fixed, close_u, plan=free_edges, edge_k=k, edge=held_edge,
                       groups=rings)
    except ff.FormError as exc:
        raise SurfaceError(str(exc)) from None
    volume = s.get("volume", "")
    if volume in CLOSED and close_u:                              # (0.560) closed: its underside, then the form over it
        under = form.copy()
        if volume == "assente":
            under[..., 2] = 0.0                         # (a flat base on its outline's plane)
        else:
            under[..., 2] = -form[..., 2] * 0.5         # (a lens: its underside half as deep)
        form = np.concatenate((under[::-1], form[1:]), axis=0)
    return o + form @ axes, close_u


def _rows_blobs(data, env, curves):
    """(0.560) Masses melted together — balls whose fields add up (a metaball volume): its surface, where the field is
    1, found along rays from the masses' middle (rows from its bottom pole to its top one, columns round it). A form
    that a ray crosses twice (a ring, an arch) is not one: its outermost crossing is taken."""
    s = data["surface"]
    balls = np.array([(float(q["x"]), float(q["y"]), float(q["z"]), float(q["r"])) for q in s.get("balls") or ()])
    if not len(balls):
        raise SurfaceError("ponha pelo menos uma massa")
    nu, nv = max(int(s.get("u", 40)), 8), max(int(s.get("v", 24)), 4)
    k = max(expr.number(s.get("fusion", 2.0), env, "surface.fusion"), 0.5)
    centre = (balls[:, :3] * balls[:, 3:] ** 3).sum(axis=0) / (balls[:, 3] ** 3).sum()
    reach = float((np.linalg.norm(balls[:, :3] - centre, axis=1) + balls[:, 3] * 2.5).max())
    lon = 2 * math.pi * np.arange(nu) / nu
    lat = math.pi * np.arange(nv + 1) / nv - math.pi / 2
    LON, LAT = np.meshgrid(lon, lat)
    dirs = np.stack((np.cos(LAT) * np.cos(LON), np.cos(LAT) * np.sin(LON), np.sin(LAT)), axis=-1).reshape(-1, 3)
    samples = 240
    t = np.linspace(0.0, reach, samples)

    def field(p):                                    # (each ball 1 on its sphere; their sum — the power: the melt)
        d2 = ((p[..., None, :] - balls[:, :3]) ** 2).sum(-1)
        return ((balls[:, 3] ** 2 / np.maximum(d2, 1e-12)) ** (2.0 / k)).sum(-1)
    pts = centre + dirs[:, None, :] * t[None, :, None]
    f = field(pts)
    inside = f >= 1.0
    last = np.where(inside.any(axis=1), samples - 1 - np.argmax(inside[:, ::-1], axis=1), 0)
    lo, hi = t[last], t[np.minimum(last + 1, samples - 1)]
    for _ in range(24):                              # (the crossing refined)
        mid = (lo + hi) / 2
        ok = field(centre + dirs * mid[:, None]) >= 1.0
        lo, hi = np.where(ok, mid, lo), np.where(ok, hi, mid)
    rows = (centre + dirs * lo[:, None]).reshape(nv + 1, nu, 3)
    return rows, True


def _rows_patch(data, env, curves):
    s = data["surface"]
    pts, _closed = _need(curves, s.get("boundary"), closed=True, what="a tampa")
    nu, nv = int(s.get("u", 24)), int(s.get("v", 16))
    rise = expr.number(s.get("rise", 0.0), env, "surface.rise")
    form = s.get("form", "cupula")
    if s.get("grid", "quadras") == "quadras":
        ring = resample(pts, max(4 * (nu + nv), 64), True)
        b, r, t, l_ = _four_sides(ring)
        c0, c2 = resample(b, nu + 1, False), resample(t, nu + 1, False)
        c3, c1 = resample(l_, nv + 1, False), resample(r, nv + 1, False)
        u = (np.arange(nu + 1) / nu)[None, :, None]
        v = (np.arange(nv + 1) / nv)[:, None, None]
        rows = ((1 - v) * c0[None] + v * c2[None] + (1 - u) * c3[:, None] + u * c1[:, None]
                - ((1 - u) * (1 - v) * c0[0] + u * (1 - v) * c0[-1] + (1 - u) * v * c2[0] + u * v * c2[-1]))
        close_u = False
        tt = None
    else:
        ring = resample(pts, nu, True)
        c = ring.mean(axis=0)
        tt = (np.arange(nv + 1) / nv)[:, None, None]
        rows = ring[None] + (c - ring)[None] * tt
        close_u = True
    rows = np.array(rows)
    if form != "plano" and abs(rise) > 1e-12:
        if form == "cosseno":
            if tt is not None:
                h = (0.5 - 0.5 * np.cos(np.pi * tt[..., 0])) * np.ones(rows.shape[:2])
            else:
                h = _cosine_cap(rows, pts)
        else:
            from .organic_roof import Shape
            try:
                shape = Shape([tuple(p) for p in pts[:, :2]], 1.0, form)
            except ValueError:
                raise SurfaceError("o contorno não serve para esta forma (pequeno, aberto ou a cruzar-se)") from None
            h = shape.unit(rows[..., :2].reshape(-1, 2)).reshape(rows.shape[:2])
        rows[..., 2] += rise * h
    return rows, close_u


def _cosine_cap(rows, outline):
    """The cosine cap over a grid of four sides: from the edge (0) to the farthest inside point (1), by distance."""
    from shapely.geometry import LineString, Point
    edge = LineString(np.vstack((outline[:, :2], outline[:1, :2])))
    d = np.array([edge.distance(Point(p)) for p in rows[..., :2].reshape(-1, 2)]).reshape(rows.shape[:2])
    top = float(d.max())
    t = d / top if top > 1e-12 else d
    return 0.5 - 0.5 * np.cos(np.pi * t)


ROW_BUILDERS = {"grid": _rows_grid, "loft": _rows_loft, "coons": _rows_coons, "revolve": _rows_revolve,
                "extrude": _rows_extrude, "sweep": _rows_sweep, "patch": _rows_patch,
                "organic": _rows_organic,                        # (0.555)
                "blobs": _rows_blobs}                            # (0.560)


# ---------------------------------------------------------------- the modifiers

def grid_normals(rows, close_u):
    """Each point's normal (rows' shape): across its neighbours (wrapped round if closed in u)."""
    P = np.asarray(rows, dtype=float)
    if close_u:
        tu = np.roll(P, -1, axis=1) - np.roll(P, 1, axis=1)
    else:
        tu = np.empty_like(P)
        tu[:, 1:-1] = P[:, 2:] - P[:, :-2]
        tu[:, 0] = P[:, 1] - P[:, 0]
        tu[:, -1] = P[:, -1] - P[:, -2]
    tv = np.empty_like(P)
    if len(P) > 2:
        tv[1:-1] = P[2:] - P[:-2]
    tv[0] = P[1] - P[0]
    tv[-1] = P[-1] - P[-2]
    n = np.cross(tu, tv)
    ln = np.linalg.norm(n, axis=-1, keepdims=True)
    return np.where(ln > 1e-12, n / np.maximum(ln, 1e-12), (0.0, 0.0, 1.0))


def _vars(rows, close_u):
    nr, nc = rows.shape[:2]
    j, i = np.meshgrid(np.arange(nr, dtype=float), np.arange(nc, dtype=float), indexing="ij")
    u = i / (nc if close_u else max(nc - 1, 1))
    v = j / max(nr - 1, 1)
    return {"u": u, "v": v, "x": rows[..., 0], "y": rows[..., 1], "z": rows[..., 2], "i": i, "j": j,
            "nu": float(nc if close_u else nc - 1), "nv": float(nr - 1)}


POINT_VARS = ("u", "v", "x", "y", "z", "i", "j", "nu", "nv")
AXIS = {"x": 0, "y": 1, "z": 2}


def _direction(m, rows, close_u):
    along = m.get("along", "normal")
    if along == "normal":
        return grid_normals(rows, close_u)
    d = np.zeros(rows.shape)
    d[..., AXIS[along]] = 1.0
    return d


def _value(m, key, env, rows, close_u, where, default=0.0):
    fn = expr.field(m.get(key, default), env, POINT_VARS, "{}.{}".format(where, key))
    return np.broadcast_to(np.asarray(fn(**_vars(rows, close_u)), dtype=float), rows.shape[:2])


def _rotation(axis, theta):
    """(…, 3, 3) right-handed rotations about a world axis by angles theta (…)."""
    c, s_ = np.cos(theta), np.sin(theta)
    one, zero = np.ones_like(theta), np.zeros_like(theta)
    if axis == "x":
        rows = [[one, zero, zero], [zero, c, -s_], [zero, s_, c]]
    elif axis == "y":
        rows = [[c, zero, s_], [zero, one, zero], [-s_, zero, c]]
    else:
        rows = [[c, -s_, zero], [s_, c, zero], [zero, zero, one]]
    return np.stack([np.stack(r, axis=-1) for r in rows], axis=-2)


def apply_modifiers(rows, close_u, data, env, curves):
    """The grid after the modifiers (in order; those not enabled skipped), and the trims [(polygon (k, 2), keep)]."""
    rows = np.array(rows, dtype=float)
    trims = []
    for k, m in enumerate(data.get("modifiers") or ()):
        if not isinstance(m, dict) or m.get("enabled", True) is False:
            continue
        op, where = m.get("op"), "modifiers[{}] ({})".format(k, m.get("op"))
        if op == "displace":
            rows = rows + _direction(m, rows, close_u) * _value(m, "amount", env, rows, close_u, where)[..., None]
        elif op == "attractor":
            if m.get("curve"):
                pts, cl = _need(curves, m["curve"])
                targets = resample(pts, ATTRACTOR_SAMPLES, cl)
            else:
                targets = np.array([[expr.number(c, env, where + ".point") for c in (m.get("point") or (0, 0, 0))[:3]]])
            radius = expr.number(m.get("radius", 3.0), env, where + ".radius")
            if radius <= 0:
                raise SurfaceError("{}.radius: tem de ser positivo".format(where))
            flat = rows.reshape(-1, 3)
            d = np.min(np.linalg.norm(flat[:, None, :] - targets[None, :, :], axis=2), axis=1).reshape(rows.shape[:2])
            r = d / radius
            fall = m.get("falloff", "gauss")
            w = np.maximum(0.0, 1.0 - r) if fall == "linear" else 1.0 / (1.0 + r * r) if fall == "inverse" \
                else np.exp(-4.0 * r * r)
            amount = _value(m, "amount", env, rows, close_u, where, 1.0)
            rows = rows + _direction(m, rows, close_u) * (amount * np.where(w > 1e-9, w, 0.0))[..., None]
        elif op == "taper":
            axis = m.get("axis", "v")
            fn = expr.field(m.get("factor", 1.0), env, POINT_VARS, where + ".factor")
            nr, nc = rows.shape[:2]
            if axis in ("u", "v"):
                out = rows.copy()
                if axis == "v":
                    for j in range(nr):
                        c = rows[j].mean(axis=0)
                        f = float(np.asarray(fn(u=0.5, v=j / max(nr - 1, 1), x=c[0], y=c[1], z=c[2], i=0.0,
                                                j=float(j), nu=float(nc - 1), nv=float(nr - 1)), dtype=float))
                        out[j] = c + (rows[j] - c) * f
                else:
                    for i in range(nc):
                        c = rows[:, i].mean(axis=0)
                        f = float(np.asarray(fn(u=i / (nc if close_u else max(nc - 1, 1)), v=0.5, x=c[0], y=c[1],
                                                z=c[2], i=float(i), j=0.0, nu=float(nc - 1), nv=float(nr - 1)),
                                             dtype=float))
                        out[:, i] = c + (rows[:, i] - c) * f
                rows = out
            else:
                a = AXIS[axis]
                lo, hi = rows.reshape(-1, 3).min(axis=0), rows.reshape(-1, 3).max(axis=0)
                span = max(hi[a] - lo[a], 1e-12)
                centre = (lo + hi) / 2.0
                vs = _vars(rows, close_u)
                vs["u"] = (rows[..., a] - lo[a]) / span
                f = np.broadcast_to(np.asarray(fn(**vs), dtype=float), rows.shape[:2])
                out = rows.copy()
                for b in range(3):
                    if b != a:
                        out[..., b] = centre[b] + (rows[..., b] - centre[b]) * f
                rows = out
        elif op == "twist":
            axis = m.get("axis", "z")
            theta = np.radians(_value(m, "angle", env, rows, close_u, where))
            lo, hi = rows.reshape(-1, 3).min(axis=0), rows.reshape(-1, 3).max(axis=0)
            pivot = np.broadcast_to((lo + hi) / 2.0, rows.shape).copy()
            pivot[..., AXIS[axis]] = rows[..., AXIS[axis]]
            rows = pivot + np.einsum("...ij,...j->...i", _rotation(axis, theta), rows - pivot)
        elif op == "shear":
            a, b = AXIS[m.get("axis", "x")], AXIS[m.get("by", "z")]
            lo, hi = rows[..., b].min(), rows[..., b].max()
            s_ = (rows[..., b] - lo) / max(hi - lo, 1e-12)
            rows = rows.copy()
            rows[..., a] += _value(m, "amount", env, rows, close_u, where, 1.0) * s_
        elif op == "wave":
            uw = expr.number(m.get("u_waves", 2.0), env, where + ".u_waves")
            vw = expr.number(m.get("v_waves", 0.0), env, where + ".v_waves")
            ph = expr.number(m.get("phase", 0.0), env, where + ".phase")
            vs = _vars(rows, close_u)
            f = np.ones(rows.shape[:2])
            if uw > 0:
                f = f * np.sin(math.tau * (vs["u"] * uw + ph))
            if vw > 0:
                f = f * np.sin(math.tau * (vs["v"] * vw + ph))
            amp = _value(m, "amplitude", env, rows, close_u, where, 0.3)
            rows = rows + _direction(m, rows, close_u) * (amp * f)[..., None]
        elif op == "relax":
            its = int(max(1, min(50, int(m.get("iterations", 5)))))
            fac = max(0.0, min(1.0, float(expr.number(m.get("factor", 0.5), env, where + ".factor"))))
            for _ in range(its):
                if len(rows) < 3:
                    break
                avg = rows.copy()
                left = np.roll(rows, 1, axis=1)
                right = np.roll(rows, -1, axis=1)
                avg[1:-1] = (rows[:-2] + rows[2:] + left[1:-1] + right[1:-1]) / 4.0
                new = rows + (avg - rows) * fac
                new[0], new[-1] = rows[0], rows[-1]
                if not close_u:
                    new[:, 0], new[:, -1] = rows[:, 0], rows[:, -1]
                rows = new
        elif op == "bend":
            theta = math.radians(expr.number(m.get("angle", 60.0), env, where + ".angle"))
            if abs(theta) < 1e-9:
                continue
            a, b = AXIS[m.get("axis", "x")], AXIS[m.get("toward", "z")]
            lo, hi = rows.reshape(-1, 3).min(axis=0), rows.reshape(-1, 3).max(axis=0)
            span = max(hi[a] - lo[a], 1e-9)
            radius = span / theta
            c = (lo[b] + hi[b]) / 2.0
            phi = (rows[..., a] - lo[a]) / radius
            t = rows[..., b] - c
            out = rows.copy()
            out[..., a] = lo[a] + np.sin(phi) * (radius - t)
            out[..., b] = c + radius - np.cos(phi) * (radius - t)
            rows = out
        elif op == "trim":
            pts, cl = _need(curves, m.get("curve"))
            if not cl:
                raise SurfaceError("{}: a curva do recorte tem de ser fechada".format(where))
            trims.append((resample(pts, TRIM_SAMPLES, True)[:, :2], m.get("keep", "inside")))
        if not np.all(np.isfinite(rows)):
            raise SurfaceError("{}: resultado não finito".format(where))
    return rows, trims


def kept(xy, trims):
    """Which plan points (…, 2) pass every trim."""
    xy = np.asarray(xy, dtype=float)
    ok = np.ones(xy.shape[:-1], dtype=bool)
    if not trims:
        return ok
    import shapely
    from shapely.geometry import Polygon
    for poly, keep in trims:
        shape = Polygon(poly)
        if not shape.is_valid:
            shape = shape.buffer(0)
        inside = shapely.contains_xy(shape, xy[..., 0], xy[..., 1])
        ok &= inside if keep == "inside" else ~inside
    return ok


# ---------------------------------------------------------------- the surface

class Surface:
    """A definition worked out: its grid of points (rows (nr, nc, 3)), whether it closes round in u, its trims, its
    inputs' values, its curves sampled."""

    def __init__(self, data):
        errors = validate(data)
        if errors:
            raise SurfaceError(" | ".join(errors[:4]))
        self.data = data
        self.env = {k: float(v) for k, v in (data.get("inputs") or {}).items()}
        try:
            self.curves = _curves(data, self.env)
            rows, close_u = ROW_BUILDERS[data["surface"]["op"]](data, self.env, self.curves)
            rows = np.asarray(rows, dtype=float)
            if rows.ndim != 3 or rows.shape[0] < 2 or rows.shape[1] < 2:
                raise SurfaceError("a grelha da superfície saiu vazia")
            if rows.shape[0] * rows.shape[1] > MAX_CELLS:
                raise SurfaceError("superfície densa demais (no máximo {} pontos)".format(MAX_CELLS))
            self.rows, self.trims = apply_modifiers(rows, close_u, data, self.env, self.curves)
        except expr.ExprError as exc:
            raise SurfaceError(str(exc)) from None
        self.close_u = close_u

    @property
    def shape(self):
        return self.rows.shape[:2]

    def mesh(self):
        """(vertices (N, 3), faces [[i…] quads or triangles]) — a row of points all at one place (a pole: a revolved
        profile on the axis, a cap's top) made one vertex; the faces whose middle a trim takes away left out."""
        rows, close_u = self.rows, self.close_u
        nr, nc = rows.shape[:2]
        index = np.arange(nr * nc).reshape(nr, nc)
        verts = rows.reshape(-1, 3).copy()
        for j in range(nr):
            if np.all(np.linalg.norm(rows[j] - rows[j, 0], axis=1) < POLE_EPS):
                index[j, :] = index[j, 0]
        faces = []
        cols = nc if close_u else nc - 1
        cut = organic_cut(self.data, rows)                 # (0.557) an organic form's oculi left open
        for j in range(nr - 1):
            for i in range(cols):
                i1 = (i + 1) % nc
                if cut is not None and cut[j, i] and cut[j, i1] and cut[j + 1, i1] and cut[j + 1, i]:
                    continue
                q = [int(index[j, i]), int(index[j, i1]), int(index[j + 1, i1]), int(index[j + 1, i])]
                out = []
                for k in q:
                    if k not in out:
                        out.append(k)
                if len(out) >= 3:
                    faces.append(out)
        if self.trims and faces:
            mids = np.array([verts[f].mean(axis=0)[:2] for f in faces])
            ok = kept(mids, self.trims)
            faces = [f for f, k in zip(faces, ok) if k]
            if not faces:
                raise SurfaceError("o recorte tirou todas as faces — veja a curva e o lado a manter")
        used = sorted({k for f in faces for k in f})
        remap = {k: n for n, k in enumerate(used)}
        return verts[used], [[remap[k] for k in f] for f in faces]

    def triangles(self):
        """(vertices, triangles (T, 3)) of the surface: each quad cut along its shorter diagonal."""
        verts, faces = self.mesh()
        return verts, triangulate(verts, faces)

    def area(self):
        verts, tris = self.triangles()
        if not len(tris):
            return 0.0
        a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
        return float(0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum())

    def bounds(self):
        flat = self.rows.reshape(-1, 3)
        return flat.min(axis=0), flat.max(axis=0)


def triangulate(verts, faces):
    tris = []
    for f in faces:
        if len(f) == 3:
            tris.append(f)
        elif len(f) == 4:
            a, b, c, d = f
            if np.sum((verts[a] - verts[c]) ** 2) <= np.sum((verts[b] - verts[d]) ** 2):
                tris += [[a, b, c], [a, c, d]]
            else:
                tris += [[a, b, d], [b, c, d]]
        else:
            tris += [[f[0], f[k], f[k + 1]] for k in range(1, len(f) - 1)]
    return np.asarray(tris, dtype=np.int64).reshape(-1, 3)


# ---------------------------------------------------------------- made from curves picked in the model

def guess_op(curves):
    """The op a set of picked curves [(points, closed)] makes when none is asked for (the addon's): 4 that close a
    loop → 4 edges; 2 or more → a loft; one closed → a patch over it; one open → an extrusion."""
    n = len(curves)
    if n == 4 and _loop_of_four(curves):
        return "coons"
    if n >= 2:
        return "loft"
    if n == 1:
        return "patch" if curves[0][1] else "extrude"
    return "grid"


def _loop_of_four(curves):
    if any(c for _p, c in curves):
        return False
    ends = [np.asarray(p, float)[[0, -1]] for p, _c in curves]
    pts = np.vstack(ends)
    for k, e in enumerate(ends):
        for q in e:
            d = np.linalg.norm(pts - q, axis=1)
            d[2 * k:2 * k + 2] = np.inf
            if float(d.min()) > COONS_GAP:
                return False
    return True


def order_sections(curves):
    """A loft's sections in order: along the line between the two farthest middles (stacked rings: by height)."""
    mids = np.array([np.asarray(p, float).mean(axis=0) for p, _c in curves])
    if len(mids) < 3:
        return list(range(len(mids)))
    d = np.linalg.norm(mids[:, None] - mids[None], axis=2)
    a, b = np.unravel_index(int(np.argmax(d)), d.shape)
    axis = mids[b] - mids[a]
    return list(np.argsort((mids - mids[a]) @ axis, kind="stable"))


def order_edges(curves):
    """Four edges in a chain (each starting where the one before ends), for «coons»."""
    order = [0]
    left = [1, 2, 3]
    end = np.asarray(curves[0][0], float)[-1]
    while left:
        best = min(left, key=lambda k: min(np.linalg.norm(np.asarray(curves[k][0], float)[0] - end),
                                           np.linalg.norm(np.asarray(curves[k][0], float)[-1] - end)))
        p = np.asarray(curves[best][0], float)
        end = p[-1] if np.linalg.norm(p[0] - end) <= np.linalg.norm(p[-1] - end) else p[0]
        order.append(best)
        left.remove(best)
    return order


def from_curves(curves, op=None, name="Superfície", divisions=None, **fields):
    """A definition made of picked curves [(points (k, 3) in the element's coordinates, closed, source)] — the op
    asked for, or the one they make (guess_op); `fields` the op's own (rise, angle, direction…)."""
    curves = [(np.asarray(p, float), bool(c), s) for p, c, s in curves]
    op = op or guess_op([(p, c) for p, c, _s in curves])
    lo, hi = OP_CURVES[op]
    if not lo <= len(curves) <= hi:
        raise SurfaceError("esta forma precisa de {} curva(s); escolheu {}".format(
            lo if lo == hi else "{} ou mais".format(lo), len(curves)))
    data = default_definition(op, name)
    data["inputs"] = {}
    if op == "loft":
        curves = [curves[k] for k in order_sections([(p, c) for p, c, _s in curves])]
    elif op == "coons":
        curves = [curves[k] for k in order_edges([(p, c) for p, c, _s in curves])]
    elif op == "sweep" and len(curves) == 2:            # (the longer the path)
        a, b = (float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum()) for p, _c, _s in curves)
        if b > a:
            curves = curves[::-1]
    for k, (p, c, src) in enumerate(curves):
        entry = {"id": "c{}".format(k + 1), "points": [[round(float(x), 6) for x in q] for q in p], "closed": c}
        if src:
            entry["source"] = src
        data["curves"].append(entry)
    ids = curve_ids(data)
    s = data["surface"]
    if op == "loft":
        s["sections"] = ids
    elif op == "coons":
        s["edges"] = ids
    elif op in ("revolve", "extrude"):
        s["profile"] = ids[0]
    elif op == "sweep":
        s["path"], s["profile"] = ids[0], ids[1]
    elif op in ("patch", "organic"):
        s["boundary"] = ids[0]
    if divisions:
        s["u"], s["v"] = int(divisions[0]), int(divisions[1])
    s.update({k: v for k, v in fields.items() if v is not None and k in OP_DEFAULTS[op]})
    return data


def translated(data, offset):
    """The definition with its curves' points moved by `offset` (x, y, z) — a definition made in one frame put in
    another."""
    out = copy.deepcopy(data)
    d = np.asarray(offset, float)
    for c in out.get("curves") or ():
        if "points" in c:
            c["points"] = [[round(float(x), 6) for x in (np.asarray(q, float) + d)] for q in c["points"]]
    m = out.get("surface") or {}
    if m.get("op") == "revolve":
        o = list(m.get("origin") or (0.0, 0.0))
        m["origin"] = [round(float(o[0]) + float(d[0]), 6), round(float(o[1]) + float(d[1]), 6)]
    for mod in out.get("modifiers") or ():
        if mod.get("op") == "attractor" and not mod.get("curve") and isinstance(mod.get("point"), list):
            mod["point"] = [(float(v) + float(d[k])) if isinstance(v, (int, float)) else v
                            for k, v in enumerate(mod["point"][:3])]
    return out
