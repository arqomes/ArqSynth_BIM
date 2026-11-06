"""(0.417) The project's verification settings: the country (its laws), the laws checked, the building's use, the kind
of work and its height — kept in the IFC (IfcProject, «Verificacao»: ifc/dwellings.py).

A country's packs are checked together; a pack may name others as supplementary («fallback»: Cabo Verde's CTE, art.
4.º — where it says nothing, the Portuguese law): their rules count only on the topics the country's own say nothing
of."""

from . import rules as rules_mod

COUNTRIES = {"CV": ("Cabo Verde", "Cape Verde"), "PT": ("Portugal", "Portugal")}
BUILDING_USES = {"habitacao": ("Habitação", "Housing"), "servicos": ("Serviços", "Offices"),
                 "comercio": ("Comércio", "Shops"), "misto": ("Misto (habitação e comércio)", "Mixed (housing and shops)")}
WORKS = {"nova": ("Obra nova", "New building"),
         "I": ("Intervenção — nível I (Q ≤ 5 %)", "Intervention — level I (Q ≤ 5 %)"),
         "II": ("Intervenção — nível II (5 % < Q ≤ 25 %)", "Intervention — level II"),
         "III": ("Intervenção — nível III (25 % < Q ≤ 50 %)", "Intervention — level III"),
         "IV": ("Intervenção — nível IV (Q > 50 %)", "Intervention — level IV")}
DEFAULTS = {"country": None, "packs": None, "building_use": "habitacao", "work": "nova", "height": None, "on": True}


def settings(doc, default_country=None):
    """The project's settings, with the defaults (a project never set: the country last chosen in this computer)."""
    try:
        own = doc.ifc.verify_settings()
    except Exception:                                   # noqa: BLE001 (the IFC still being read)
        own = {}
    out = dict(DEFAULTS)
    out.update({k: v for k, v in own.items() if v is not None or k == "country"})
    if out.get("country") is None and default_country in COUNTRIES and not own:
        out["country"] = default_country
    return out


def active(settings_, all_packs=None):
    """[(Pack, its own: True | supplementary: False)] the project checks: those chosen, else the country's own and those
    they name as supplementary — and (0.423) the town plan's values for this project."""
    all_packs = all_packs if all_packs is not None else rules_mod.packs()
    if not settings_.get("on", True):
        return []
    return _laws(settings_, all_packs) + [(plan_pack(settings_), True)]


# (0.423) the town plan's values for this project — what the municipality sets for the lot (a PDM, a «plano de
# pormenor», an allotment's permit): settings["pdm"] = {"name": "PDM da Praia", "ios_max": 0.5, …}
PLAN_PACK = "PLANO"
PLAN_FIELDS = (                         # (its key, the lot's measure, min | max, unit)
    ("lote_min", "area_lote", "min", "m2"),
    ("ios_max", "indice_ocupacao", "max", ""),
    ("iu_max", "indice_utilizacao", "max", ""),
    ("implantacao_max", "area_implantacao", "max", "m2"),
    ("construcao_max", "area_construcao", "max", "m2"),
    ("pisos_max", "pisos_acima_solo", "max", ""),
    ("caves_max", "pisos_abaixo_solo", "max", ""),
    ("cercea_max", "cercea", "max", "m"),
    ("altura_max", "altura_edificio", "max", "m"),
    ("frontal_min", "afastamento_frontal", "min", "m"),
    ("lateral_min", "afastamento_lateral", "min", "m"),
    ("posterior_min", "afastamento_posterior", "min", "m"),
    ("impermeabilizacao_max", "impermeabilizacao", "max", ""),
)
SIDE_FLAG = {"afastamento_frontal": "tem_frente", "afastamento_lateral": "tem_lateral",
             "afastamento_posterior": "tem_posterior"}


def plan_pack(settings_):
    """The rules of the town plan's values set for this project — and, always, the building inside the lot."""
    from ..i18n import t
    values = settings_.get("pdm") or {}
    name = (values.get("name") or "").strip() or t("verify.plan.short")
    pack = rules_mod.Pack(id=PLAN_PACK, country=settings_.get("country") or "*", short=name,
                          title=t("verify.plan.title"), instrument=name, source=t("verify.plan.source"))
    pack.rules = [rules_mod.Rule(
        id="PLANO-dentro", pack=PLAN_PACK, article=t("verify.plan.article_lot"), title=t("verify.plan.inside"),
        subject="lot", measure="fora_do_lote", text=t("verify.plan.inside_text"), where={"tem_lote": True},
        limit={"max": 0.0}, severity="error", confirmed=True, unit="m2", topic="urbanismo.dentro_do_lote")]
    for key, measure, side, unit in PLAN_FIELDS:
        value = values.get(key)
        if value is None:
            continue
        where = {SIDE_FLAG[measure]: True} if measure in SIDE_FLAG else {}
        pack.rules.append(rules_mod.Rule(
            id="PLANO-" + key, pack=PLAN_PACK, article=t("verify.plan.article"), title=t("verify.plan.f." + key),
            subject="lot", measure=measure, text=t("verify.plan.text", name=name), where=where,
            limit={side: float(value)}, severity="error", confirmed=True, unit=unit, topic="urbanismo." + key))
    rules_mod.GENERATED[PLAN_PACK] = pack
    return pack


def plan_values(settings_):
    """The town plan's values set ({key: value}), without its name."""
    return {k: v for k, v in (settings_.get("pdm") or {}).items() if k != "name" and v is not None}


def _laws(settings_, all_packs):
    chosen = settings_.get("packs")
    if chosen:
        return [(all_packs[p], True) for p in chosen if p in all_packs]
    country = settings_.get("country")
    own = [p for p in all_packs.values() if p.country == country]
    out = [(p, True) for p in own]
    seen = {p.id for p in own}
    for p in own:
        for f in p.fallback:
            if f in all_packs and f not in seen:
                out.append((all_packs[f], False))
                seen.add(f)
    if own and settings_.get("good_practice", True):     # (0.422: good practice, any country — where the law is silent)
        out += [(p, False) for p in all_packs.values() if p.country == "*" and p.id not in seen]
    return out


def active_rules(settings_, all_packs=None):
    """The rules checked: the own packs' all; a supplementary pack's only on topics the own ones do not cover."""
    chosen = active(settings_, all_packs)
    covered = {r.topic or r.id for p, own in chosen if own for r in p.rules}
    out = []
    for p, own in chosen:
        out += [r for r in p.rules if own or (r.topic or r.id) not in covered]
    return out


def label(table, key, language="pt"):
    entry = table.get(key)
    return "" if entry is None else entry[0 if language == "pt" else 1]
