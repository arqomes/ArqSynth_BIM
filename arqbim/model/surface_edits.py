"""(0.395) The changes the Properties make to a parametric surface's definition, as plain dict edits: apply(data,
action, value) → a new definition (the old one untouched). Each value given its field's kind: a whole number stays
whole, a number may be a formula (text), a choice one of its choices."""

import copy

from ..core import param_surface as ps
from ..core import surface_build as sb


def number_or_formula(text):
    """«0,35» → 0.35; «H/2» → "H/2" (a formula, checked when the surface is made); "" → None."""
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        return float(text)
    s = str(text).strip()
    if not s:
        return None
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return s.replace("−", "-")


def _typed(template, value):
    """The value in the kind of the template's field."""
    if isinstance(template, bool):
        return bool(value)
    if isinstance(template, int):
        v = number_or_formula(value)
        return int(round(v)) if isinstance(v, float) else template
    if isinstance(template, float) or template is None:
        v = number_or_formula(value)
        return template if v is None else v
    if isinstance(template, list):
        return value if isinstance(value, list) else template
    return str(value)


def apply(data, action, value):
    d = copy.deepcopy(data)
    s = d.setdefault("surface", {})
    op = s.get("op", "grid")
    if action in ("surface_u", "surface_v"):
        s[action[-1]] = max(1, min(ps.MAX_DIVISIONS, int(value)))
    elif action == "surface_field":                       # (key, value) of the op's own
        key, v = value
        default = ps.OP_DEFAULTS[op].get(key)
        if key == "height" and op == "extrude":           # (an extrusion's: its direction's z)
            dz = number_or_formula(v)
            direction = list(s.get("direction") or (0.0, 0.0, 3.0))
            direction[2] = dz if dz is not None else direction[2]
            s["direction"] = direction
        elif key in ("form", "grid", "behaviour"):        # (0.555: an organic form's behaviour)
            s[key] = str(v)
        elif isinstance(default, bool):
            s[key] = bool(v)
        else:
            nv = number_or_formula(v)
            if nv is not None:
                s[key] = nv
    elif action == "surface_input":                       # (name, value)
        name, v = value
        nv = number_or_formula(v)
        if isinstance(nv, float):
            d.setdefault("inputs", {})[name] = nv
    elif action == "surface_mod_add":
        m = dict({"op": value}, **copy.deepcopy(ps.MODIFIER_TEMPLATES[value]))
        if value in ("trim", "attractor"):
            closed = [c["id"] for c in d.get("curves") or () if c.get("closed")]
            if value == "trim":
                m["curve"] = closed[0] if closed else ""
        if value == "attractor":
            lo, hi = _bounds(d)
            m["point"] = [round((a + b) / 2.0, 3) for a, b in zip(lo, hi)]
        d.setdefault("modifiers", []).append(m)
    elif action == "surface_mod":                         # (index, field, value)
        k, key, v = value
        m = d["modifiers"][k]
        template = ps.MODIFIER_TEMPLATES[m["op"]].get(key)
        if key in ps.MODIFIER_FIELDS.get(m["op"], {}) or key == "curve":
            m[key] = str(v)
        elif key == "point":
            m[key] = v if isinstance(v, list) else m.get(key)
        else:
            m[key] = _typed(template, v)
    elif action == "surface_mod_toggle":
        k, on = value
        d["modifiers"][k]["enabled"] = bool(on)
    elif action == "surface_mod_move":
        k, step = value
        mods = d["modifiers"]
        j = k + step
        if 0 <= j < len(mods):
            mods[k], mods[j] = mods[j], mods[k]
    elif action == "surface_mod_remove":
        del d["modifiers"][int(value)]
    elif action == "surface_build_add":
        d.setdefault("build", {})[value] = copy.deepcopy(sb.TEMPLATES[value])
    elif action == "surface_build_only":                  # (the tool's quick choice: this one alone, or none)
        d["build"] = {} if not value or value == "none" else {value: copy.deepcopy(sb.TEMPLATES[value])}
    elif action == "surface_build":                       # (section, field, value)
        name, key, v = value
        sec = d.setdefault("build", {}).setdefault(name, copy.deepcopy(sb.TEMPLATES[name]))
        template = sb.TEMPLATES[name].get(key)
        if (name, key) in sb.CHOICES or key in ("material", "mask"):
            sec[key] = str(v)
        else:
            sec[key] = _typed(template, v)
    elif action == "surface_build_toggle":
        name, on = value
        d["build"][name]["enabled"] = bool(on)
    elif action == "surface_build_remove":
        d.get("build", {}).pop(value, None)
    elif action == "surface_definition":                  # (a whole one: imported, or edited as text)
        d = copy.deepcopy(value)
    else:
        raise ValueError("unknown surface edit: " + action)
    return d


def apply_action(data, action, value):
    """An edit as the Properties name it — "surface_mod:2:amount", "surface_build:panels:gap",
    "surface_input:H", "surface_field:rise", "surface_mod_move:1:-1", "surface_build_remove:ribs"… — applied."""
    parts = action.split(":")
    head = parts[0]
    if head in ("surface_mod", "surface_build"):
        key = int(parts[1]) if head == "surface_mod" else parts[1]
        return apply(data, head, (key, parts[2], value))
    if head in ("surface_input", "surface_field"):
        return apply(data, head, (parts[1], value))
    if head == "surface_mod_toggle":
        return apply(data, head, (int(parts[1]), value))
    if head == "surface_build_toggle":
        return apply(data, head, (parts[1], value))
    if head == "surface_mod_move":
        return apply(data, head, (int(parts[1]), int(parts[2])))
    if head == "surface_mod_remove":
        return apply(data, head, int(parts[1]))
    if head == "surface_build_remove":
        return apply(data, head, parts[1])
    return apply(data, head, value)


def _bounds(d):
    try:
        lo, hi = ps.Surface(d).bounds()
        return [float(x) for x in lo], [float(x) for x in hi]
    except (ps.SurfaceError, ValueError):
        return [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
