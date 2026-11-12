"""(0.567, PLANO.md «Gerador de revestimentos 3D em IFC», step 4) Finishing rules kept in the project — «every
bathroom: 30 × 60 wall tile up to 2,10 m, porcelain floor» —: each a name, the rooms it is for (words of their name
or number, «|» between: «WC|banho|sanitária»), and its floor, walls (up to a height), skirting and ceiling finishes.
Applied to every room they match, the Revestimentos a rule made before in those rooms taken away first (applied again
after the plan changed, they are as the rule says). Kept as JSON in the project's ArqSynth_Parametros."""

import json
import re

from ..i18n import lang, t
from .document import IfcCommand

KEY = "RegrasRevestimento"
FIELDS = ("name", "rooms", "floor", "walls", "wall_height", "skirting", "ceiling")


def rules(ifc):
    project = ifc.file.by_type("IfcProject")
    if not project:
        return []
    try:
        data = json.loads(ifc._params(project[0]).get(KEY) or "[]")
    except ValueError:
        return []
    return [r for r in data if isinstance(r, dict) and r.get("name")]


def matches(rule, info):
    """Does the rule's rooms («WC|banho») match the room (its name or number, any case, accents as written)?"""
    words = [w.strip().lower() for w in str(rule.get("rooms") or "").split("|") if w.strip()]
    if not words:
        return False
    text = "{} {}".format(info.get("name") or "", info.get("number") or "").lower()
    return any(re.search(re.escape(w), text) for w in words)


def save_rules(doc, data):
    """The project's rules replaced by `data` ([{name, rooms, floor, walls, wall_height, skirting, ceiling}]). One
    undo step."""
    clean = [{k: r.get(k) for k in FIELDS} for r in data if r.get("name")]

    def action(ifc):
        project = ifc.file.by_type("IfcProject")[0]
        ifc._set_params(project, {KEY: json.dumps(clean, ensure_ascii=False)})

    doc.execute(IfcCommand(t("cmd.covering_rules"), action))


def apply_rules(doc, names=None, storey=None):
    """Every rule (or those named) laid in the rooms it matches (of one storey, or all): what a rule made there before
    taken away, made again. One undo step. {rule name: [GlobalIds made]}."""
    from . import bim
    from ..core import covering_finishes as cf
    from . import covering_targets as ct
    import numpy as np
    chosen = [r for r in rules(doc.ifc) if names is None or r["name"] in names]
    rooms = doc.ifc.spaces(storey)
    plan = []
    for r in chosen:
        for info in rooms:
            if matches(r, info):
                plan.append((r, info))
    if not plan:
        raise ValueError("tiling_no_rooms")
    language = lang()
    up, down = np.array((0.0, 0.0, 1.0)), np.array((0.0, 0.0, -1.0))
    jobs_by_rule = {}
    for r, info in plan:
        jobs = jobs_by_rule.setdefault(r["name"], [])
        if r.get("floor"):
            ol, hs = ct.room_floor(info)
            jobs.append((r["floor"], None, None, None, up, ol, hs, None, info["guid"]))
        if r.get("walls"):
            for g, p, n, ol, hs, stretch in ct.room_walls(doc.ifc, info, float(r.get("wall_height") or 2.1)):
                jobs.append((r["walls"], None, g, p, n, ol, hs, stretch, None))
        elif r.get("skirting"):
            for g, p, n, ol, hs, stretch in ct.room_walls(doc.ifc, info, cf.finish(r["skirting"]).h):
                jobs.append((r["skirting"], None, g, p, n, ol, hs, stretch, None))
        if r.get("ceiling"):
            ol, hs = ct.room_ceiling(info)
            jobs.append((r["ceiling"], None, None, None, down, ol, hs, None, info["guid"]))
    room_ids = {info["guid"] for _r, info in plan}

    def action(ifc):
        old = [e.GlobalId for e in ifc.file.by_type("IfcCovering")
               if ifc._params(e).get("Elemento") == "tiled_covering" and ifc._params(e).get("Regra") in jobs_by_rule
               and ifc._params(e).get("RegraAmbiente") in room_ids]
        if old:
            ifc.remove(old)
        out = {}
        for name, jobs in jobs_by_rule.items():
            made = bim._lay_many(ifc, jobs, language)
            out[name] = made
        for name, made in out.items():            # (each marked with its rule and room: found again next time)
            for g in made:
                e = ifc.by_guid(g)
                p = ifc._params(e)
                room = p.get("Ambiente") or _room_of(ifc, p, rooms)
                ifc._set_params(e, {"Regra": name, "RegraAmbiente": room or ""})
        return out

    return doc.execute(IfcCommand(t("cmd.covering_rules"), action)).result


def _room_of(ifc, p, rooms):
    """The room a wall's Revestimento was laid for: the one whose outline its stretch runs along."""
    from shapely.geometry import Point, Polygon
    import numpy as np
    if not p.get("Recorte") or not p.get("Origem"):
        return None
    host = ifc.by_guid(p["Origem"])
    if host is None:
        return None
    m = ifc._placement_si(host)
    qa, qb, _h = p["Recorte"].split(";")
    a, b = ((m @ np.append([float(v) for v in q.split(",")], 1.0))[:3] for q in (qa, qb))
    mid = Point(float((a[0] + b[0]) / 2), float((a[1] + b[1]) / 2))
    best = min(rooms, key=lambda s: Polygon(s["outline"]).exterior.distance(mid), default=None)
    return best["guid"] if best is not None else None
