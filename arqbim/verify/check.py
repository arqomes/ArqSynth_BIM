"""(0.417) The whole check: the reader's facts, the subjects (rooms, dwellings, doors, the building) with what the
rules filter on, the rules of the project's laws evaluated on them — a Result: what fails, what passes, what could not
be measured; and each finding said in words («Sala (Fogo A): área 12,40 m² — CTE, art. 40.º e Anexo I: mínimo
14,00 m²»)."""

from dataclasses import dataclass, field

import numpy as np

from ..i18n import decimal_sep, lang, t
from . import dwellings as dw
from . import measures as ms
from . import project
from . import reader
from . import rules as rules_mod
from . import uses


@dataclass
class Result:
    revision: int = -1
    findings: list = field(default_factory=list)
    packs: list = field(default_factory=list)       # [(Pack, own)]
    settings: dict = field(default_factory=dict)

    @property
    def failures(self):
        return [f for f in self.findings if f.failed]

    def count(self, severity):
        return sum(1 for f in self.findings if f.failed and f.rule.severity == severity)

    def counts(self):
        """{"error", "warning", "excepted", "ok", "unknown"}: how many of each."""
        return {"error": self.count("error"), "warning": self.count("warning"),
                "excepted": sum(1 for f in self.findings if f.excepted),
                "ok": sum(1 for f in self.findings if f.status == "ok"),
                "unknown": sum(1 for f in self.findings if f.status == "unknown")}

    def dwelling_of(self, finding, facts):
        """The dwelling a finding is about (its name), or None: a room's, a door's (of the room inside), its own."""
        s = finding.subject
        if s.kind == "dwelling":
            return s.id
        for g in s.elements:
            if g in facts.of_room:
                return facts.of_room[g]
        if s.kind == "door":
            for side in facts.sides.get(s.id, ()):
                if side in facts.of_room:
                    return facts.of_room[side]
        return None

    def of(self, element):
        """The findings about one room / door (its GlobalId) or dwelling (its name)."""
        return [f for f in self.findings if f.subject.id == element or element in f.subject.elements]


def _building_height(doc):
    try:
        levels = sorted(z for _g, _n, z in doc.storeys())
    except Exception:                                   # noqa: BLE001
        return None, 0
    if not levels:
        return None, 0
    top = levels[-1] + 3.0                               # (the top storey's own height, roughly, until a roof says)
    return round(top - levels[0], 2), len(levels)


def subjects(ctx):
    """{"room": [Subject], "dwelling": […], "door": […], "building": […]}."""
    facts, settings = ctx.facts, ctx.settings
    building_use = settings.get("building_use", "habitacao")
    language = lang()
    out = {"room": [], "dwelling": [], "door": [], "building": [], "stair": [], "ramp": [], "railing": [],
           "window": []}
    ranks = {}
    for d in facts.dwellings:
        bedrooms = sorted((g for g in d.rooms if g in facts.rooms and uses.is_bedroom(facts.rooms[g].use)
                           and not facts.rooms[g].external), key=lambda g: -facts.rooms[g].area)
        for k, g in enumerate(bedrooms):
            ranks[g] = k + 1
        out["dwelling"].append(ms.Subject(
            "dwelling", d.name, "{} ({})".format(d.name, d.typology), list(d.rooms),
            props={"typology": d.typology, "building_use": building_use, "bedrooms": d.bedrooms,
                   "t3_ou_mais": "sim" if d.bedrooms >= 3 else "nao"}))
    for g, r in facts.rooms.items():
        d = facts.dwelling_of(g)
        name = r.name or uses.label(r.use, language)
        out["room"].append(ms.Subject(
            "room", g, "{} ({})".format(name, d.name) if d else name, [g], r.storey,
            props={"use": r.use, "external": r.external, "common": uses.is_common(r.use),
                   "typology": d.typology if d else None, "in_dwelling": d is not None,
                   "building_use": building_use, "bedroom_rank": ranks.get(g)}))
    sides = facts.sides or dw.door_sides(facts.rooms.values(), facts.doors)
    for door in facts.doors:
        a, b = sides.get(door.guid, (None, None))
        if a is None and b is None:
            continue
        ra, rb = facts.rooms.get(a), facts.rooms.get(b)
        role = "compartimento"
        if a is None or b is None:                       # (a «~place» in no room is inside: not an entrance)
            role = "entrada_edificio"
        elif uses.is_common(ra.use if ra else None) or uses.is_common(rb.use if rb else None):
            role = "acesso_comum"
        elif "arrumos" in (ra.use if ra else None, rb.use if rb else None):
            role = "secundaria"
        obj = ctx.doc.get(door.guid)
        inside = rb if ra is None else ra
        where = (inside.name or uses.label(inside.use, language)) if inside else ""
        name = "{} — {}".format(obj.name if obj is not None else t("verify.door"), where) if where else \
            (obj.name if obj is not None else t("verify.door"))
        out["door"].append(ms.Subject("door", door.guid, name, [door.guid], door.storey,
                                      props={"role": role, "building_use": building_use}))
    height, storeys = _building_height(ctx.doc)
    if settings.get("height") is not None:
        height = float(settings["height"])
    out["building"].append(ms.Subject("building", "building", t("verify.building"), [],
                                      props={"building_use": building_use, "height": height, "storeys": storeys,
                                             "work": settings.get("work", "nova")}))
    # (0.419) the corridors' length (a short one may be narrower: CTE art. 44.º n.º 2); a bedroom's area band (the
    # square it must hold: CTE art. 41.º c)
    for s in out["room"]:
        if s.props["use"] in ("corredor", "vestibulo"):
            length = ms.measure(ctx, s, "comprimento")
            s.props["curto"] = "sim" if length is not None and length <= 1.50 + 1e-6 else "nao"
        area = facts.rooms[s.id].area
        s.props["faixa_area"] = "menos_de_7" if area < 7.0 - 1e-6 else ("7_a_10.5" if area < 10.5 - 1e-6
                                                                        else "10.5_ou_mais")
    # (0.419) the stairs, ramps and railings: where they are — in a dwelling, or in common use
    band = "acima_28" if height is not None and height > 28.0 + 1e-6 else "ate_28"
    has_common = any(uses.is_common(r.use) for r in facts.rooms.values())
    locate = _locator(facts)
    for obj in list(ctx.doc.objects.values()):
        kind = {"IfcStair": "stair", "IfcRamp": "ramp", "IfcRailing": "railing"}.get(getattr(obj, "ifc_class", ""))
        if kind is None or getattr(obj, "mesh", None) is None:
            continue
        lo, hi = (np.asarray(c, dtype=float) for c in obj.mesh.bounds())
        room = locate(obj.storey, (lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0)
        in_dwelling = room is not None and room in facts.of_room
        common = (room is not None and uses.is_common(facts.rooms[room].use)) or (has_common and not in_dwelling)
        out[kind].append(ms.Subject(kind, obj.id, obj.name or t("verify.kind." + kind), [obj.id], obj.storey,
                                    props={"common": common, "in_dwelling": in_dwelling, "height_band": band,
                                           "building_use": building_use}))
    # (0.420) the windows (and glazed doors) to the outside, of the rooms they light
    from . import measures as _ms
    language_ = lang()
    for w in facts.windows:
        a, b = facts.window_sides.get(w.guid, (None, None))
        if (a is None) == (b is None) or _ms.glazing(ctx, w.guid) <= 1e-6:
            continue
        room = facts.rooms.get(a if b is None else b)
        if room is None:
            continue
        obj = ctx.doc.get(w.guid)
        name = "{} — {}".format(obj.name if obj is not None else "", room.name or uses.label(room.use, language_))
        out["window"].append(ms.Subject("window", w.guid, name, [w.guid], w.storey,
                                        props={"habitable": uses.is_habitable(room.use),
                                               "in_dwelling": room.guid in facts.of_room,
                                               "use": room.use, "building_use": building_use}))
    return out


def _locator(facts):
    """room_at(storey, x, y): the room there (its GlobalId), or None."""
    from shapely.geometry import Point
    polys = [(r.storey, g, dw._polygon(r)) for g, r in facts.rooms.items()]

    def room_at(storey, x, y):
        here = Point(float(x), float(y))
        found = [(poly.area, g) for s, g, poly in polys if s == storey and poly.contains(here)]
        return min(found)[1] if found else None
    return room_at


_KEPT = {}


def _elements(doc):
    """Whether there are stairs, ramps or railings to check (a project with no rooms yet may have them)."""
    return any(getattr(o, "ifc_class", "") in ("IfcStair", "IfcRamp", "IfcRailing") for o in doc.objects.values())


def check(doc, settings=None, all_packs=None, default_country=None, force=False):
    """The Result for the document as it is now (kept until it changes)."""
    revision = getattr(doc, "revision", 0)
    settings = settings if settings is not None else project.settings(doc, default_country)
    key = (revision, repr(sorted(settings.items())))
    kept = _KEPT.get(id(doc))
    if kept is not None and kept[0] == key and not force:
        return kept[1]
    facts = reader.read(doc)
    chosen = project.active(settings, all_packs)
    rules = project.active_rules(settings, all_packs)
    ctx = ms.Context(doc, facts, settings)
    result = Result(revision, rules_mod.run(ctx, rules, subjects(ctx)) if rules and (facts.rooms or _elements(doc))
                    else [], chosen, settings)
    exceptions = settings.get("exceptions") or {}
    for f in result.findings:                            # (0.418: what the architect accepted, with why)
        if f.status == "fail" and f.key in exceptions:
            f.excepted = dict(exceptions[f.key])
    _KEPT[id(doc)] = (key, result)
    return result


# ------------------------------------------------------------------ said in words

def number(value, unit):
    if value is None:
        return "—"
    text = "{:.2f}".format(float(value)).replace(".", decimal_sep())
    return {"m": text + " m", "m2": text + " m²", "%": text + " %"}.get(unit, text)


def message(finding, packs_by_id=None):
    """«Sala (Fogo A): área útil 12,40 m² — CTE, art. 40.º e Anexo I: mínimo 14,00 m²»."""
    rule, s = finding.rule, finding.subject
    pack = (packs_by_id if packs_by_id is not None else rules_mod.packs()).get(rule.pack)
    short = pack.short if pack is not None else rule.pack
    side = "min" if any(k.startswith("min") for k in rule.limit) else "max"
    text = t("verify.message", subject=s.name, measure=t("verify.m." + rule.measure),
             value=number(finding.value, rule.unit), law=short, article=rule.article,
             side=t("verify.side." + side), limit=number(finding.limit, rule.unit))
    if not rule.confirmed:
        text += t("verify.unconfirmed")
    return text
