"""The parametric surfaces' formulas (0.395, as the ArqSynth addon's «Superfícies Paramétricas»): a number or a short
formula of named inputs and, where the place asks for it, of the point (u, v, x, y, z, i, j, nu, nv, t) — read
without ever running code: the formula is parsed (Python's own grammar) and only numbers, names, + − × ÷ // % **
and the functions below are let through; it is then worked out over whole numpy arrays at once (every point of a
surface in one go).

Functions: sin cos tan asin acos atan atan2 sqrt abs exp log floor ceil round min max pow clamp lerp smoothstep step
noise dist length; constants pi, tau, e. A formula longer than MAX_SOURCE characters or of more than MAX_NODES pieces,
a power over MAX_POW_EXPONENT, a result not finite or larger than MAX_ABS_RESULT: refused with a readable message.
`noise(x[, y[, z[, seed]]])` is a value noise in [−1, 1], the same on every machine (an integer hash)."""

import ast
import math

import numpy as np

MAX_SOURCE = 400
MAX_NODES = 240
MAX_ABS_RESULT = 1e12
MAX_POW_EXPONENT = 16
CONSTANTS = {"pi": math.pi, "tau": math.tau, "e": math.e}
POINT_VARIABLES = ("u", "v", "x", "y", "z", "t", "i", "j", "nu", "nv")


class ExprError(ValueError):
    """A formula that cannot be read or worked out: its message says why, in words."""


def _clamp(x, lo, hi):
    return np.minimum(np.maximum(x, lo), hi)


def _smoothstep(a, b, x):
    a, b, x = np.broadcast_arrays(np.asarray(a, float), np.asarray(b, float), np.asarray(x, float))
    span = b - a
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(np.abs(span) > 1e-300, (x - a) / np.where(np.abs(span) > 1e-300, span, 1.0), np.where(x < a, 0.0,
                                                                                                          1.0))
    t = _clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _hash_unit(ix, iy, iz, seed):
    """An integer cell's value in [0, 1] (the addon's hash, the same bits: 32-bit wrap-around)."""
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647 + seed * 144665) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return h.astype(float) / float(0xFFFFFFFF)


def _noise(x, y=0.0, z=0.0, seed=0.0):
    x, y, z, seed = np.broadcast_arrays(*(np.asarray(a, dtype=float) for a in (x, y, z, seed)))
    s = np.round(seed).astype(np.int64)
    cx, cy, cz = (np.floor(a).astype(np.int64) for a in (x, y, z))
    fx, fy, fz = x - cx, y - cy, z - cz
    sx, sy, sz = (f * f * (3.0 - 2.0 * f) for f in (fx, fy, fz))
    out = np.zeros(x.shape)
    for dx in (0, 1):
        wx = sx if dx else 1.0 - sx
        for dy in (0, 1):
            wy = sy if dy else 1.0 - sy
            for dz in (0, 1):
                wz = sz if dz else 1.0 - sz
                out = out + wx * wy * wz * _hash_unit(cx + dx, cy + dy, cz + dz, s)
    return out * 2.0 - 1.0


def _domain(name, ok, src):
    if not np.all(ok):
        raise ExprError("{}(...) inválido em '{}' (fora do domínio)".format(name, src))


def _dist(*a):
    if len(a) == 4:
        return np.hypot(np.asarray(a[2], float) - a[0], np.asarray(a[3], float) - a[1])
    return np.sqrt((np.asarray(a[3], float) - a[0]) ** 2 + (np.asarray(a[4], float) - a[1]) ** 2 +
                   (np.asarray(a[5], float) - a[2]) ** 2)


def _length(*a):
    return np.sqrt(sum(np.asarray(c, float) ** 2 for c in a))


# name: (fewest arguments, most arguments, function(src, *args))
FUNCTIONS = {
    "sin": (1, 1, lambda s, a: np.sin(a)),
    "cos": (1, 1, lambda s, a: np.cos(a)),
    "tan": (1, 1, lambda s, a: np.tan(a)),
    "asin": (1, 1, lambda s, a: (_domain("asin", np.abs(a) <= 1.0, s), np.arcsin(a))[1]),
    "acos": (1, 1, lambda s, a: (_domain("acos", np.abs(a) <= 1.0, s), np.arccos(a))[1]),
    "atan": (1, 1, lambda s, a: np.arctan(a)),
    "atan2": (2, 2, lambda s, a, b: np.arctan2(a, b)),
    "sqrt": (1, 1, lambda s, a: (_domain("sqrt", np.asarray(a) >= 0.0, s), np.sqrt(a))[1]),
    "abs": (1, 1, lambda s, a: np.abs(a)),
    "exp": (1, 1, lambda s, a: (_domain("exp", np.asarray(a) <= 700.0, s), np.exp(a))[1]),
    "log": (1, 2, lambda s, a, b=None: _log(s, a, b)),
    "floor": (1, 1, lambda s, a: np.floor(a)),
    "ceil": (1, 1, lambda s, a: np.ceil(a)),
    "round": (1, 1, lambda s, a: np.round(a)),
    "min": (2, 8, lambda s, *a: _reduce(np.minimum, a)),
    "max": (2, 8, lambda s, *a: _reduce(np.maximum, a)),
    "pow": (2, 2, lambda s, a, b: _pow(s, a, b)),
    "clamp": (3, 3, lambda s, x, lo, hi: _clamp(x, lo, hi)),
    "lerp": (3, 3, lambda s, a, b, t: a + (b - a) * t),
    "smoothstep": (3, 3, lambda s, a, b, x: _smoothstep(a, b, x)),
    "step": (2, 2, lambda s, edge, x: np.where(np.asarray(x) < edge, 0.0, 1.0)),
    "noise": (1, 4, lambda s, *a: _noise(*a)),
    "dist": (4, 6, lambda s, *a: (_arity_dist(s, a), _dist(*a))[1]),
    "length": (2, 3, lambda s, *a: _length(*a)),
}
RESERVED = set(FUNCTIONS) | set(CONSTANTS) | set(POINT_VARIABLES)


def _arity_dist(src, a):
    if len(a) not in (4, 6):
        raise ExprError("dist(...) leva 4 (2D) ou 6 (3D) números em '{}'".format(src))


def _reduce(fn, args):
    out = args[0]
    for a in args[1:]:
        out = fn(out, a)
    return out


def _log(src, a, b):
    _domain("log", np.asarray(a) > 0.0, src)
    if b is None:
        return np.log(a)
    _domain("log", (np.asarray(b) > 0.0) & (np.asarray(b) != 1.0), src)
    return np.log(a) / np.log(b)


def _pow(src, a, b):
    b_arr = np.asarray(b, dtype=float)
    if np.any(np.abs(b_arr) > MAX_POW_EXPONENT):
        raise ExprError("expoente acima de {} em '{}'".format(MAX_POW_EXPONENT, src))
    a_arr = np.asarray(a, dtype=float)
    bad = (a_arr < 0.0) & (np.floor(b_arr) != b_arr)
    if np.any(bad):
        raise ExprError("base negativa com expoente fracionário em '{}'".format(src))
    if np.any((a_arr == 0.0) & (b_arr < 0.0)):
        raise ExprError("divisão por zero em '{}'".format(src))
    return np.power(a_arr, b_arr)


_BINOPS = {ast.Add: np.add, ast.Sub: np.subtract, ast.Mult: np.multiply}


class Compiled:
    """A formula read once, worked out many times: evaluate(**values) — each value a number or an array (all of
    one shape, or numbers): the result a number or an array of that shape."""

    def __init__(self, source, tree, names):
        self.source, self.tree, self.names = source, tree, names

    def uses(self, name):
        return name in self.names

    def evaluate(self, **values):
        out = _evaluate(self.tree, values, self.source)
        _check(out, self.source)
        return out


def _check(value, src):
    arr = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(arr)):
        raise ExprError("resultado não finito em '{}'".format(src))
    if arr.size and float(np.max(np.abs(arr))) > MAX_ABS_RESULT:
        raise ExprError("resultado demasiado grande em '{}'".format(src))


def compile_expression(text, variables=()):
    """The formula `text` checked against the names it may use (`variables`, besides the constants): Compiled.
    ExprError if it cannot be read, uses something not allowed or a name it does not know."""
    src = str(text).strip()
    if not src:
        raise ExprError("expressão vazia")
    if len(src) > MAX_SOURCE:
        raise ExprError("expressão com mais de {} caracteres".format(MAX_SOURCE))
    try:
        tree = ast.parse(src, mode="eval").body
    except SyntaxError as exc:
        raise ExprError("não consigo ler '{}' ({})".format(src, exc.msg)) from None
    allowed, names, count = set(variables), set(), [0]

    def walk(node):
        count[0] += 1
        if count[0] > MAX_NODES:
            raise ExprError("expressão longa demais ('{}')".format(src))
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ExprError("constante não numérica em '{}'".format(src))
        elif isinstance(node, ast.Name):
            if node.id in FUNCTIONS:
                raise ExprError("'{0}' é uma função: use {0}(...)".format(node.id))
            if node.id not in allowed and node.id not in CONSTANTS:
                raise ExprError("nome desconhecido '{}' em '{}' — pode usar: {}".format(
                    node.id, src, ", ".join(sorted(allowed | set(CONSTANTS))) or "só números"))
            names.add(node.id)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            walk(node.operand)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
                                                                  ast.Mod, ast.Pow)):
            walk(node.left)
            walk(node.right)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS:
            if node.keywords:
                raise ExprError("argumentos com nome não são permitidos em '{}'".format(src))
            lo, hi, _fn = FUNCTIONS[node.func.id]
            if not lo <= len(node.args) <= hi:
                raise ExprError("{}(...) leva {} argumento(s) em '{}'".format(
                    node.func.id, lo if lo == hi else "{} a {}".format(lo, hi), src))
            for a in node.args:
                walk(a)
        else:
            raise ExprError("construção não permitida em '{}'".format(src))

    walk(tree)
    return Compiled(src, tree, names)


def _evaluate(node, values, src):
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id in values:
            return values[node.id]
        return CONSTANTS[node.id]
    if isinstance(node, ast.UnaryOp):
        v = _evaluate(node.operand, values, src)
        return -v if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.BinOp):
        a, b = _evaluate(node.left, values, src), _evaluate(node.right, values, src)
        op = type(node.op)
        if op in _BINOPS:
            out = _BINOPS[op](a, b)
        elif op is ast.Pow:
            out = _pow(src, a, b)
        else:
            if np.any(np.asarray(b) == 0.0):
                raise ExprError("divisão por zero em '{}'".format(src))
            with np.errstate(all="ignore"):
                out = np.true_divide(a, b) if op is ast.Div else np.floor_divide(a, b) if op is ast.FloorDiv \
                    else np.mod(a, b)
        _check(out, src)
        return out
    if isinstance(node, ast.Call):
        args = [_evaluate(a, values, src) for a in node.args]
        with np.errstate(all="ignore"):
            out = FUNCTIONS[node.func.id][2](src, *args)
        _check(out, src)
        return out
    raise ExprError("construção não permitida em '{}'".format(src))


def is_formula(value):
    return isinstance(value, str)


def number(value, env, field=""):
    """A field that is a number or a formula of the inputs `env` ({name: number}): its value (float)."""
    if isinstance(value, bool):
        raise ExprError("{}: esperava número ou expressão".format(field or "valor"))
    if isinstance(value, (int, float)):
        v = float(value)
        if not math.isfinite(v):
            raise ExprError("{}: número não finito".format(field or "valor"))
        return v
    if isinstance(value, str):
        try:
            out = compile_expression(value, tuple(env)).evaluate(**env)
        except ExprError as exc:
            raise ExprError("{}: {}".format(field, exc) if field else str(exc)) from None
        return float(np.asarray(out, dtype=float))
    raise ExprError("{}: esperava número ou expressão".format(field or "valor"))


def field(value, env, variables, field_name=""):
    """A field that may vary point by point: fn(**point values) -> number or array (the inputs `env` given too)."""
    if isinstance(value, bool):
        raise ExprError("{}: esperava número ou expressão".format(field_name or "valor"))
    if isinstance(value, (int, float)):
        v = float(value)
        return lambda **_values: v
    if isinstance(value, str):
        try:
            c = compile_expression(value, tuple(env) + tuple(variables))
        except ExprError as exc:
            raise ExprError("{}: {}".format(field_name, exc) if field_name else str(exc)) from None

        def run(**values):
            try:
                return c.evaluate(**dict(env, **values))
            except ExprError as exc:
                raise ExprError("{}: {}".format(field_name, exc) if field_name else str(exc)) from None
        return run
    raise ExprError("{}: esperava número ou expressão".format(field_name or "valor"))
