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
    they name as supplementary."""
    all_packs = all_packs if all_packs is not None else rules_mod.packs()
    if not settings_.get("on", True):
        return []
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
