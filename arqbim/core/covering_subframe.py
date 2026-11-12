"""(0.571, PLANO.md «Gerador de revestimentos 3D em IFC», step 7) What holds a Revestimento's pieces off its face — a
ventilated façade's insulation, air gap, rails and brackets; ETICS' insulation boards; a raised floor's pedestals; a
floating floor's underlay; a false ceiling's hangers and profiles; battens under boards — each a system with its own
measures. Laid in the face's own plane (x, y), its depth z out of the face: [(polygons, z0, z1, material)] and how far
the pieces are lifted, with its quantities. Pure geometry."""

import math

import numpy as np
from shapely.geometry import box

SYSTEMS = {
    "nenhuma": ("Nenhuma (colado à face)", "None (bonded to the face)"),
    "ventilada": ("Fachada ventilada", "Ventilated façade"),
    "etics": ("ETICS / capoto", "ETICS"),
    "sobrelevado": ("Pavimento sobrelevado (apoios)", "Raised floor (pedestals)"),
    "flutuante": ("Flutuante (manta)", "Floating (underlay)"),
    "teto_falso": ("Teto falso (tirantes e perfis)", "False ceiling (hangers and profiles)"),
    "ripado": ("Sobre ripas / barrotes", "On battens / joists"),
}
DEFAULTS = {
    "ventilada": {"insulation": 0.06, "cavity": 0.04, "spacing": 0.60, "bracket_every": 0.80},
    "etics": {"insulation": 0.08},
    "sobrelevado": {"height": 0.15},
    "flutuante": {"underlay": 0.003},
    "teto_falso": {"drop": 0.30, "spacing": 0.60, "primary": 1.20},
    "ripado": {"spacing": 0.40, "batten": 0.03},
}
RAIL_W = 0.04            # m: an aluminium T rail's face
BRACKET = 0.08           # m: a bracket's side
PEDESTAL = 0.10          # m: a pedestal's head
PROFILE_W = 0.025        # m: a ceiling profile's width
HANGER = 0.008           # m: a hanger rod
BATTEN_W = 0.05          # m


def check(sub):
    """The subframe {system, …measures} filled and checked (None/{}: none)."""
    sub = dict(sub or {})
    system = sub.get("system") or "nenhuma"
    if system not in SYSTEMS:
        raise ValueError("tiling_subframe")
    out = {"system": system}
    out.update(DEFAULTS.get(system, {}))
    for k in DEFAULTS.get(system, {}):
        if sub.get(k) is not None:
            v = float(sub[k])
            if not 0.0 <= v <= 3.0:
                raise ValueError("tiling_subframe")
            out[k] = v
    return out


def depth(sub):
    """How far a subframe lifts the pieces off the face (m)."""
    sub = check(sub)
    s = sub["system"]
    return {"ventilada": lambda: sub["insulation"] + sub["cavity"], "etics": lambda: sub["insulation"],
            "flutuante": lambda: sub["underlay"], "sobrelevado": lambda: sub["height"],
            "teto_falso": lambda: sub["drop"], "ripado": lambda: sub["batten"]}.get(s, lambda: 0.0)()


def _lines(face, along, spacing, width):
    """Strips `width` wide every `spacing` across the face, running along x («x») or y («y»), on the face."""
    x0, y0, x1, y1 = face.bounds
    out = []
    if along == "y":
        for x in np.arange(x0 + spacing / 2.0, x1, spacing):
            out.append(box(x - width / 2.0, y0, x + width / 2.0, y1).intersection(face))
    else:
        for y in np.arange(y0 + spacing / 2.0, y1, spacing):
            out.append(box(x0, y - width / 2.0, x1, y + width / 2.0).intersection(face))
    return [g for g in out if not g.is_empty]


def _polys(geoms):
    out = []
    for g in geoms:
        for part in getattr(g, "geoms", [g]):
            if part.geom_type == "Polygon" and part.area > 1e-8:
                out.append((list(part.exterior.coords)[:-1], [list(h.coords)[:-1] for h in part.interiors]))
    return out


def lay(face, sub, pieces=()):
    """(lift, items [(polys, z0, z1, material)], quantities {…}) of the subframe on `face` (shapely, the plane's
    x, y); `pieces` (core/tiling Pieces) for a raised floor's pedestals at their corners."""
    sub = check(sub)
    s = sub["system"]
    items, q = [], {}
    if s == "nenhuma":
        return 0.0, items, q
    if s == "ventilada":
        ins, cav = sub["insulation"], sub["cavity"]
        if ins > 0:
            items.append((_polys([face]), 0.0, ins, "la_rocha"))
            q["isolamento_m2"] = face.area
        rails = _lines(face, "y", sub["spacing"], RAIL_W)
        items.append((_polys(rails), ins, ins + cav, "aluminio_natural"))
        q["montantes_m"] = sum(r.bounds[3] - r.bounds[1] for r in rails)
        brackets = []
        for r in rails:
            x = (r.bounds[0] + r.bounds[2]) / 2.0
            for y in np.arange(r.bounds[1] + 0.2, r.bounds[3], sub["bracket_every"]):
                b = box(x - BRACKET / 2.0, y, x + BRACKET / 2.0, y + 0.05).intersection(face)
                if not b.is_empty:
                    brackets.append(b)
        items.append((_polys(brackets), 0.0, ins + cav, "aluminio_natural"))
        q["esquadros"] = len(brackets)
        q["fixacoes"] = len(brackets) * 2
        return ins + cav, items, q
    if s == "etics":
        items.append((_polys([face]), 0.0, sub["insulation"], "eps"))
        q["isolamento_m2"] = face.area
        q["buchas"] = int(math.ceil(face.area * 6))
        return sub["insulation"], items, q
    if s == "flutuante":
        items.append((_polys([face]), 0.0, sub["underlay"], "eps"))
        q["manta_m2"] = face.area
        return sub["underlay"], items, q
    if s == "sobrelevado":
        h = sub["height"]
        corners = set()
        for p in pieces:
            if p.whole:
                for x, y in p.points:
                    corners.add((round(x, 2), round(y, 2)))
        heads = [box(x - PEDESTAL / 2, y - PEDESTAL / 2, x + PEDESTAL / 2, y + PEDESTAL / 2).intersection(face)
                 for x, y in corners]
        heads = [g for g in heads if not g.is_empty]
        items.append((_polys(heads), 0.0, h, "pvc"))
        q["apoios"] = len(heads)
        return h, items, q
    if s == "teto_falso":
        drop = sub["drop"]
        primary = _lines(face, "x", sub["primary"], PROFILE_W)
        secondary = _lines(face, "y", sub["spacing"], PROFILE_W)
        items.append((_polys(primary), drop - 0.054, drop - 0.027, "aco_natural"))
        items.append((_polys(secondary), drop - 0.027, drop, "aco_natural"))
        hangers = []
        for r in primary:
            y = (r.bounds[1] + r.bounds[3]) / 2.0
            for x in np.arange(r.bounds[0] + 0.3, r.bounds[2], 1.2):
                hangers.append(box(x - HANGER / 2, y - HANGER / 2, x + HANGER / 2, y + HANGER / 2))
        items.append((_polys(hangers), 0.0, drop - 0.054, "aco_natural"))
        q["perfis_primarios_m"] = sum(r.bounds[2] - r.bounds[0] for r in primary)
        q["perfis_secundarios_m"] = sum(r.bounds[3] - r.bounds[1] for r in secondary)
        q["tirantes"] = len(hangers)
        return drop, items, q
    if s == "ripado":
        battens = _lines(face, "x", sub["spacing"], BATTEN_W)
        items.append((_polys(battens), 0.0, sub["batten"], "pinho"))
        q["ripas_m"] = sum(r.bounds[2] - r.bounds[0] for r in battens)
        return sub["batten"], items, q
    return 0.0, items, q
