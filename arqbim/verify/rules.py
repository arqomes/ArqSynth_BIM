"""(0.417) The rules: data, not code. One pack (a JSON file) per law, in a folder per country (arqbim/regulamentos/CV,
…/PT, and the user's own: see project.py); each rule says where it applies, what it measures and its limit:

    {"id": "CV-CTE-27-1", "article": "art. 27.º, n.º 1", "title": "Pé-direito da habitação",
     "text": "Nos espaços destinados a habitação, o pé-direito mínimo é de 2,70 m…",
     "subject": "room", "where": {"use": ["sala", "quarto", …], "building_use": ["habitacao"]},
     "measure": "pe_direito_80", "min": 2.70, "severity": "error"}

A limit is "min" / "max" — a number or a formula of the subject's measures («area_util / 8») —, "min_table" (by a
property of the subject: {"by": "typology", "values": {"T0": 12, …}, "else": …}) or "min_rank" (a dwelling's bedrooms
from the largest: {"by": "typology", "values": {"T2": [10.5, 7], …}, "rest": 7}). «where» filters the subjects by
their properties (a list: any of them; true/false: a flag). Nothing here measures: measures.py does."""

import glob
import json
import os
from dataclasses import dataclass, field

from . import expr
from . import measures as ms

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILTIN = os.path.join(HERE, "regulamentos")
SEVERITIES = ("error", "warning", "info")


@dataclass
class Rule:
    id: str
    pack: str
    article: str
    title: str
    subject: str
    measure: str
    text: str = ""
    where: dict = field(default_factory=dict)
    limit: dict = field(default_factory=dict)    # {"min": …} | {"max": …} | {"min_table": …} | {"min_rank": …}
    severity: str = "error"
    confirmed: bool = False
    fix: str = ""
    unit: str = "m"
    topic: str = ""             # what it is about («pe_direito.habitacao»): a supplementary law's rule on a topic the
    #                             project's own law covers is not checked
    absent_ok: bool = False     # (0.420) its measure None means nothing there (no obstacle in front): it passes


@dataclass
class Pack:
    id: str
    country: str
    short: str
    title: str
    instrument: str = ""
    published: str = ""
    source: str = ""
    status: str = "em_vigor"
    fallback: list = field(default_factory=list)
    notes: str = ""
    path: str = ""
    rules: list = field(default_factory=list)
    country_name: str = ""      # (0.426) a country the architect added: its name («Angola»)


@dataclass
class Finding:
    rule: Rule
    subject: ms.Subject
    status: str                 # "ok" | "fail" | "unknown"
    value: object = None
    limit: object = None
    excepted: dict = None       # (0.418) the architect's exception for it ({"why", "when"}), or None

    @property
    def key(self):
        return "{}|{}".format(self.rule.id, self.subject.id)

    @property
    def failed(self):
        """Failing — and not accepted as an exception."""
        return self.status == "fail" and not self.excepted


LIMIT_KEYS = ("min", "max", "min_table", "max_table", "min_rank")


def _rule(data, pack):
    limit = {k: data[k] for k in LIMIT_KEYS if k in data}
    return Rule(id=data["id"], pack=pack.id, article=data.get("article", ""), title=data.get("title", ""),
                subject=data.get("subject", "room"), measure=data["measure"], text=data.get("text", ""),
                where=dict(data.get("where") or {}), limit=limit,
                severity=data.get("severity", "error") if data.get("severity") in SEVERITIES else "error",
                confirmed=bool(data.get("confirmed", False)), fix=data.get("fix", ""), unit=data.get("unit", "m"),
                topic=data.get("topic", ""), absent_ok=bool(data.get("absent_ok", False)))


def load_pack(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    pack = Pack(id=data["id"], country=data.get("country", ""), short=data.get("short", data["id"]),
                title=data.get("title", ""), instrument=data.get("instrument", ""), published=data.get("published", ""),
                source=data.get("source", ""), status=data.get("status", "em_vigor"),
                fallback=list(data.get("fallback") or ()), notes=data.get("notes", ""), path=path,
                country_name=data.get("country_name", ""))
    pack.rules = [_rule(r, pack) for r in data.get("rules", ())          # (0.426: «off»: switched off by the architect)
                  if r.get("measure") and not r.get("off")]
    return pack


_READ = {}
GENERATED = {}              # (0.423) packs made from the project's own values (the town plan's: project.plan_pack)


def find(pack_id):
    """A pack by its id: the program's (or the user's), else one made for the project — or None."""
    return packs().get(pack_id) or GENERATED.get(pack_id)


GENERATION = [0]            # (0.426) one more each time the packs are read anew: a check kept is made again


def packs(folders=None, again=False):
    """{pack id: Pack} of the folders (the program's, then the user's: a pack of the same id there wins); read once
    (again: read anew — a pack changed)."""
    folders = tuple(folders or (BUILTIN, user_folder()))
    if again:
        _READ.clear()
        GENERATION[0] += 1
    if folders in _READ:
        return _READ[folders]
    out = {}
    for folder in folders:
        for path in sorted(glob.glob(os.path.join(folder, "*", "*.json"))):
            try:
                pack = load_pack(path)
            except (OSError, ValueError, KeyError):
                continue
            out[pack.id] = pack
    _READ[folders] = out
    return out


# ------------------------------------------------------------------ (0.426) the architect's own packs

def user_folder():
    """Where the architect's own packs are kept: «ArqSynth BIM/regulamentos» in the user's application data
    (ARQBIM_RULES_DIR, when set: the tests')."""
    from ..paths import local_base, user_dir
    return os.environ.get("ARQBIM_RULES_DIR") or user_dir(local_base(), "regulamentos")


def is_users(pack):
    """Whether a pack is one of the architect's (in their folder) — not the program's."""
    if not pack.path:
        return False
    folder = os.path.abspath(user_folder())
    return os.path.abspath(pack.path).startswith(folder + os.sep)


def has_builtin(pack_id):
    return pack_id in packs((BUILTIN,))


def _file_name(text):
    import re
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text)).strip("_") or "pacote"


def save_users(data):
    """A pack (its JSON) saved in the architect's folder, under its country (the program's of the same id: this one
    wins). Its path."""
    folder = os.path.join(user_folder(), _file_name(data.get("country") or "_geral"))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, _file_name(data["id"]) + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    packs(again=True)
    return path


def remove_users(pack_id):
    """The architect's copy of a pack taken away (the program's own comes back, if there is one). Whether there was
    one."""
    found = packs().get(pack_id)
    if found is None or not is_users(found):
        return False
    os.remove(found.path)
    packs(again=True)
    return True


def free_id(base):
    """An id no pack has: `base`, else `base-2`, `base-3`…"""
    taken = set(packs())
    out, k = base, 2
    while out in taken:
        out, k = "{}-{}".format(base, k), k + 1
    return out


def new_country(code, name, source):
    """Another country's packs, copied from those of `source` (its own; not those it takes as supplementary): new ids
    («AO-CTE»…), the country `code` with its name, no supplementary laws, every value «to be confirmed». The ids
    made."""
    code = (code or "").strip().upper()
    if not code or code == "*":
        return []
    made = []
    for pack in [p for p in packs().values() if p.country == source]:
        with open(pack.path, encoding="utf-8") as f:
            data = json.load(f)
        old = data["id"]
        new = free_id(code + "-" + (old.split("-", 1)[1] if "-" in old else old))
        data.update(id=new, country=code, country_name=(name or code).strip(), status="rascunho", fallback=[],
                    notes="Copiado de {} ({}). {}".format(old, source, data.get("notes", "")).strip())
        for rule in data.get("rules", []):
            rule["id"] = new + rule["id"][len(old):] if rule["id"].startswith(old) else "{}~{}".format(new, rule["id"])
            rule["confirmed"] = False
        save_users(data)
        made.append(new)
    return made


# ------------------------------------------------------------------ evaluating

def applies(rule, subject):
    """Whether `rule` is for this subject: its kind, and every «where» it says."""
    if rule.subject != subject.kind:
        return False
    for key, wanted in rule.where.items():
        have = subject.props.get(key)
        if isinstance(wanted, list):
            if have not in wanted:
                return False
        elif isinstance(wanted, bool):
            if bool(have) != wanted:
                return False
        elif have != wanted:
            return False
    return True


def _names(ctx, subject, formula):
    """The subject's measures a formula names, measured."""
    out = {}
    for kind, value in expr._tokens(formula):
        if kind == "name" and value.lower() not in expr.FUNCTIONS:
            out[value] = ms.measure(ctx, subject, value)
    return out


def _bound(ctx, subject, value):
    if isinstance(value, (int, float)):
        return float(value)
    return expr.try_evaluate(value, _names(ctx, subject, value))


def limit_of(ctx, rule, subject):
    """("min" | "max", the limit) for this subject, or (None, None) when the rule gives none for it."""
    lim = rule.limit
    for side in ("min", "max"):
        if side in lim:
            return side, _bound(ctx, subject, lim[side])
        table = lim.get(side + "_table")
        if table:
            key = subject.props.get(table.get("by", "typology"))
            value = (table.get("values") or {}).get(key, table.get("else"))
            return (side, _bound(ctx, subject, value)) if value is not None else (None, None)
    rank = lim.get("min_rank")
    if rank:
        key = subject.props.get(rank.get("by", "typology"))
        order = subject.props.get("bedroom_rank")
        values = (rank.get("values") or {}).get(key)
        if order is None:
            return None, None
        if values and order <= len(values):
            return "min", float(values[order - 1])
        if rank.get("rest") is not None:
            return "min", float(rank["rest"])
    return None, None


def evaluate(ctx, rule, subject):
    if rule.absent_ok and ms.measure(ctx, subject, rule.measure) is None:
        return Finding(rule, subject, "ok", None, None)    # (0.420: nothing there to fall short — nothing in front)
    side, bound = limit_of(ctx, rule, subject)
    if side is None:
        return None                                    # (nothing asked of this one)
    value = ms.measure(ctx, subject, rule.measure)
    if value is None or bound is None:
        return Finding(rule, subject, "unknown", value, bound)
    ok = value >= bound - 1e-6 if side == "min" else value <= bound + 1e-6
    return Finding(rule, subject, "ok" if ok else "fail", value, bound)


def run(ctx, rules, subjects):
    """[Finding] of every rule on every subject it applies to."""
    out = []
    for rule in rules:
        for subject in subjects.get(rule.subject, ()):
            if applies(rule, subject):
                found = evaluate(ctx, rule, subject)
                if found is not None:
                    out.append(found)
    return out
