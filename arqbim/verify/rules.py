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
                fallback=list(data.get("fallback") or ()), notes=data.get("notes", ""), path=path)
    pack.rules = [_rule(r, pack) for r in data.get("rules", ()) if r.get("measure")]
    return pack


_READ = {}


def packs(folders=None, again=False):
    """{pack id: Pack} of the folders (the program's, then the user's: a pack of the same id there wins); read once
    (again: read anew — a pack changed)."""
    folders = tuple(folders or (BUILTIN,))
    if folders in _READ and not again:
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
