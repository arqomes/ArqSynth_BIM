"""(0.425) The verification sheet («ficha de verificação»): what the Verifier found, for the licensing file —

- the project: its name, the country and the laws checked, the building's use, the kind of work, the date;
- the lot and the town plan's values, with what the project has (when there is a lot or a plan);
- the table of areas («quadro de áreas»): each dwelling, its type, its rooms with their use and area, its useful and
  gross areas;
- every rule checked, by law and article: what it asks, what the project has, ✓ / ✗ / ⚠ / not measured — and the
  exceptions with their reasons and dates;
- the values still to be checked against the published texts, said so.

Made as data first (sheet()), then written as an HTML page (printed to PDF by ui/report_pdf) or an Excel workbook."""

import datetime
import html
import os

from ..i18n import lang, t
from . import check as check_mod
from . import measures as ms
from . import project
from . import reader
from . import rules as rules_mod
from . import urban
from . import uses

MARK = {"ok": "✓", "fail": "✗", "warn": "⚠", "unknown": "—", "excepted": "✓*"}


def _project_name(doc):
    try:
        projects = doc.ifc.file.by_type("IfcProject")
        name = projects[0].Name if projects else ""
    except AttributeError:
        name = ""
    path = getattr(doc, "path", None)
    return name or (os.path.splitext(os.path.basename(path))[0] if path else "") or t("sheet.untitled")


def state(finding):
    """"ok" | "fail" (an error) | "warn" | "unknown" | "excepted"."""
    if finding.excepted:
        return "excepted"
    if finding.status == "fail":
        return "fail" if finding.rule.severity == "error" else "warn"
    return finding.status


def sheet(doc, settings, result=None):
    """The sheet's data: {"project", "date", "country", "use", "work", "height", "laws": [(short, title,
    instrument)], "lot": {...} | None, "plan": [(title, asked, has, state)], "dwellings": [...], "rows": [...],
    "exceptions": [...], "counts": {...}, "unconfirmed": n}."""
    language = lang()
    result = result if result is not None else check_mod.check(doc, settings)
    facts = reader.read(doc)
    ctx = ms.Context(doc, facts, settings)
    used = {f.rule.pack for f in result.findings}
    laws = [(p.short, p.title if own else "{} ({})".format(p.title, t("verify.settings.supplementary")), p.instrument)
            for p, own in result.packs                  # (the country's own; a supplementary one only when used)
            if (own or p.id in used) and (p.id != project.PLAN_PACK or project.plan_values(settings))]
    out = {"project": _project_name(doc), "date": datetime.date.today().strftime("%d/%m/%Y"),
           "country": project.country_name(settings.get("country"), language) or "—",
           "use": project.label(project.BUILDING_USES, settings.get("building_use"), language),
           "work": project.label(project.WORKS, settings.get("work"), language),
           "height": check_mod.number(settings.get("height"), "m") if settings.get("height") is not None else
           t("sheet.auto"), "laws": laws}
    lot = urban.lot_info(ctx)
    if lot is not None:
        values = urban.summary(ctx)
        out["lot"] = {"area": check_mod.number(lot["area"], "m2"), "sides": len(lot["outline"]),
                      "values": [(t("verify.m." + k), check_mod.number(v, _unit(k))) for k, v in values.items()
                                 if v is not None]}
    else:
        out["lot"] = None
    plan = []
    for f in result.findings:
        if f.rule.pack == project.PLAN_PACK:
            plan.append((f.rule.title, _required(f), check_mod.number(f.value, f.rule.unit), state(f)))
    out["plan"] = plan
    dwellings = []
    for d in facts.dwellings:
        rooms = []
        here = [facts.rooms[g] for g in d.rooms if g in facts.rooms]
        for r in sorted(here, key=lambda r: (uses.ORDER.index(r.use) if r.use in uses.ORDER else 99, r.name or "")):
            rooms.append((r.name or uses.label(r.use, language), uses.label(r.use, language),
                          check_mod.number(r.area, "m2")))
        gross = ms.measure(ctx, ms.Subject("dwelling", d.name, d.name), "area_bruta")
        dwellings.append({"name": d.name, "typology": d.typology, "rooms": rooms,
                          "useful": check_mod.number(d.useful_area, "m2"), "gross": check_mod.number(gross, "m2")})
    out["dwellings"] = dwellings
    order = {p.id: k for k, (p, _own) in enumerate(result.packs)}      # (the country's law first, as checked)
    rows, exceptions, short = [], [], []
    by_rule = {}
    for f in sorted(result.findings, key=lambda f: (order.get(f.rule.pack, 99), _article_key(f.rule.article),
                                                    f.rule.id, f.subject.name)):
        if f.rule.severity == "info" or f.rule.pack == project.PLAN_PACK:
            continue
        pack = rules_mod.find(f.rule.pack)
        row = {"law": pack.short if pack else f.rule.pack, "article": f.rule.article, "title": f.rule.title,
               "subject": f.subject.name, "has": _number(f.value, f.rule.unit), "asked": _required(f),
               "state": state(f), "confirmed": f.rule.confirmed}
        rows.append(row)
        by_rule.setdefault(f.rule.id, []).append(row)
        if f.excepted:
            exceptions.append(dict(row, why=f.excepted.get("why", ""), when=f.excepted.get("when", "")))
    for group in by_rule.values():                      # (the PDF's: a rule of many places — every wall… — says its
        absent = [r for r in group if r["state"] == "ok" and r["has"] == "—"]     # problems one by one and the rest
        group = [r for r in group if r not in absent]                              # in one line)
        if len(group) <= MANY:
            short += group
        else:
            passing = [r for r in group if r["state"] == "ok"]
            short += [r for r in group if r["state"] != "ok"]
            if passing:
                short.append(dict(passing[0], subject=t("sheet.others_ok", n=len(passing)), has="", asked=""))
        if absent:                                      # (nothing there to measure: nothing in front of it…)
            short.append(dict(absent[0], subject=t("sheet.absent", n=len(absent)), has="", asked=""))
    out["rows"], out["short_rows"], out["exceptions"] = rows, short, exceptions
    out["counts"] = result.counts()
    out["unconfirmed"] = sum(1 for r in rows if not r["confirmed"])
    return out


MANY = 6                    # a rule checked in more places than this: its passing ones in one line, in the PDF


def _number(value, unit):
    """As check.number — a count (no unit, a whole number) without decimals."""
    if unit == "" and isinstance(value, (int, float)) and float(value).is_integer():
        return "{:d}".format(int(value))
    return check_mod.number(value, unit)


def _unit(measure):
    if measure.startswith("indice") or measure.startswith("impermeabil") or measure.startswith("pisos"):
        return ""
    return "m2" if measure.startswith("area") or measure == "fora_do_lote" else "m"


def _required(f):
    side = "min" if any(k.startswith("min") for k in f.rule.limit) else "max"
    if f.limit is None:
        return "—"
    return "{} {}".format(t("verify.side." + side), _number(f.limit, f.rule.unit))


def _article_key(article):
    import re
    numbers = [int(n) for n in re.findall(r"\d+", article or "")]
    return numbers or [10 ** 6]


# ------------------------------------------------------------------ as an HTML page (for the PDF)

STYLE = """
body { font-family: Arial; font-size: 9pt; color: #1d1d1b; }
h1 { font-size: 15pt; margin: 0 0 4px 0; } h2 { font-size: 11pt; margin: 14px 0 4px 0; border-bottom: 1px solid #888; }
table { border-collapse: collapse; width: 100%; } td, th { border: 1px solid #b8b8b8; padding: 2px 4px; }
th { background: #e8e8e4; text-align: left; } .ok { color: #2e7d32; } .fail { color: #c62828; font-weight: bold; }
.warn { color: #b26a00; } .unknown { color: #777777; } .excepted { color: #1565c0; } .note { color: #555555; }
"""


def _e(text):
    return html.escape(str(text))


def page(d):
    """The sheet as an HTML page (Qt's text engine prints it to PDF)."""
    out = ["<html><head><style>{}</style></head><body>".format(STYLE)]
    out.append("<h1>{}</h1>".format(_e(t("sheet.title"))))
    out.append("<p><b>{}</b> — {}</p>".format(_e(d["project"]), _e(d["date"])))
    out.append("<table>")
    for key, value in (("sheet.country", d["country"]), ("sheet.use", d["use"]), ("sheet.work", d["work"]),
                       ("sheet.height", d["height"])):
        out.append("<tr><th width='30%'>{}</th><td>{}</td></tr>".format(_e(t(key)), _e(value)))
    out.append("<tr><th>{}</th><td>{}</td></tr>".format(
        _e(t("sheet.laws")), "<br>".join("{} — {} <span class='note'>({})</span>".format(_e(s), _e(ti), _e(i))
                                        for s, ti, i in d["laws"])))
    out.append("</table>")
    c = d["counts"]
    out.append("<p>{}</p>".format(_e(t("sheet.summary", e=c["error"], w=c["warning"], x=c["excepted"], ok=c["ok"],
                                       u=c["unknown"]))))
    if d["lot"] is not None or d["plan"]:
        out.append("<h2>{}</h2>".format(_e(t("sheet.lot_title"))))
        if d["lot"] is not None:
            out.append("<p>{}</p><table>".format(_e(t("sheet.lot", a=d["lot"]["area"], n=d["lot"]["sides"]))))
            for name, value in d["lot"]["values"]:
                out.append("<tr><td>{}</td><td>{}</td></tr>".format(_e(name), _e(value)))
            out.append("</table>")
        if d["plan"]:
            out.append("<table><tr><th>{}</th><th>{}</th><th>{}</th><th></th></tr>".format(
                _e(t("sheet.col.rule")), _e(t("sheet.col.asked")), _e(t("sheet.col.has"))))
            for title, asked, has, st in d["plan"]:
                out.append("<tr><td>{}</td><td>{}</td><td>{}</td><td class='{}'>{}</td></tr>".format(
                    _e(title), _e(asked), _e(has), st, MARK[st]))
            out.append("</table>")
    if d["dwellings"]:
        out.append("<h2>{}</h2>".format(_e(t("sheet.areas"))))
        out.append("<table><tr><th>{}</th><th>{}</th><th>{}</th><th>{}</th></tr>".format(
            _e(t("sheet.col.dwelling")), _e(t("sheet.col.room")), _e(t("sheet.col.use")), _e(t("sheet.col.area"))))
        for dw in d["dwellings"]:
            for k, (name, use, area) in enumerate(dw["rooms"]):
                head = "<b>{} ({})</b>".format(_e(dw["name"]), _e(dw["typology"])) if k == 0 else ""
                out.append("<tr><td>{}</td><td>{}</td><td>{}</td><td align='right'>{}</td></tr>".format(
                    head, _e(name), _e(use), _e(area)))
            out.append("<tr><td></td><td colspan='2'><i>{}</i></td><td align='right'><i>{}</i></td></tr>".format(
                _e(t("sheet.useful")), _e(dw["useful"])))
            out.append("<tr><td></td><td colspan='2'><i>{}</i></td><td align='right'><i>{}</i></td></tr>".format(
                _e(t("sheet.gross")), _e(dw["gross"])))
        out.append("</table>")
    out.append("<h2>{}</h2>".format(_e(t("sheet.rules"))))
    out.append("<table><tr><th>{}</th><th>{}</th><th>{}</th><th>{}</th><th>{}</th><th></th></tr>".format(
        _e(t("sheet.col.article")), _e(t("sheet.col.rule")), _e(t("sheet.col.subject")), _e(t("sheet.col.asked")),
        _e(t("sheet.col.has"))))
    law = None
    for r in d.get("short_rows", d["rows"]):
        if r["law"] != law:
            law = r["law"]
            out.append("<tr><th colspan='6'>{}</th></tr>".format(_e(law)))
        star = "" if r["confirmed"] or not r["asked"] else " ¹"
        out.append("<tr><td>{}</td><td>{}</td><td>{}</td><td>{}{}</td><td>{}</td><td class='{}'>{}</td></tr>".format(
            _e(r["article"]), _e(r["title"]), _e(r["subject"]), _e(r["asked"]), star, _e(r["has"]), r["state"],
            MARK[r["state"]]))
    out.append("</table>")
    if d["exceptions"]:
        out.append("<h2>{}</h2><table><tr><th>{}</th><th>{}</th><th>{}</th><th>{}</th></tr>".format(
            _e(t("sheet.exceptions")), _e(t("sheet.col.article")), _e(t("sheet.col.subject")), _e(t("sheet.col.why")),
            _e(t("sheet.col.when"))))
        for x in d["exceptions"]:
            out.append("<tr><td>{} {}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                _e(x["law"]), _e(x["article"]), _e(x["subject"]), _e(x["why"]), _e(x["when"])))
        out.append("</table>")
    out.append("<p class='note'>{}</p>".format(_e(t("sheet.legend"))))
    if d["unconfirmed"]:
        out.append("<p class='note'>{}</p>".format(_e(t("sheet.unconfirmed", n=d["unconfirmed"]))))
    out.append("</body></html>")
    return "".join(out)


# ------------------------------------------------------------------ as an Excel workbook

def write_xlsx(path, d):
    """The sheet as a workbook: «Resumo», «Quadro de áreas», «Verificação», «Exceções» (openpyxl)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
    book = Workbook()
    bold, head_fill = Font(bold=True), PatternFill("solid", fgColor="E8E8E4")

    def table(ws, header, rows, widths):
        ws.append(header)
        for cell in ws[ws.max_row]:
            cell.font, cell.fill = bold, head_fill
        for row in rows:
            ws.append(list(row))
        for k, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(k)].width = w
        ws.freeze_panes = "A2"

    ws = book.active
    ws.title = t("sheet.tab.summary")[:31]
    summary = [(t("sheet.title"), d["project"]), (t("sheet.date"), d["date"]), (t("sheet.country"), d["country"]),
               (t("sheet.use"), d["use"]), (t("sheet.work"), d["work"]), (t("sheet.height"), d["height"])]
    summary += [(t("sheet.laws"), "{} — {}".format(s, ti)) for s, ti, _i in d["laws"]]
    c = d["counts"]
    summary += [(t("sheet.col.result"), t("sheet.summary", e=c["error"], w=c["warning"], x=c["excepted"],
                                          ok=c["ok"], u=c["unknown"]))]
    if d["lot"] is not None:
        summary += [(t("verify.kind.lot"), t("sheet.lot", a=d["lot"]["area"], n=d["lot"]["sides"]))]
        summary += list(d["lot"]["values"])
    summary += [(title, "{} — {} {}".format(asked, has, MARK[st])) for title, asked, has, st in d["plan"]]
    table(ws, [t("sheet.col.what"), t("sheet.col.value")], summary, (42, 70))
    ws = book.create_sheet(t("sheet.tab.areas")[:31])
    rows = []
    for dw in d["dwellings"]:
        rows += [("{} ({})".format(dw["name"], dw["typology"]), name, use, area) for name, use, area in dw["rooms"]]
        rows += [("{} ({})".format(dw["name"], dw["typology"]), t("sheet.useful"), "", dw["useful"]),
                 ("{} ({})".format(dw["name"], dw["typology"]), t("sheet.gross"), "", dw["gross"])]
    table(ws, [t("sheet.col.dwelling"), t("sheet.col.room"), t("sheet.col.use"), t("sheet.col.area")], rows,
          (20, 28, 24, 14))
    ws = book.create_sheet(t("sheet.tab.rules")[:31])
    table(ws, [t("sheet.col.law"), t("sheet.col.article"), t("sheet.col.rule"), t("sheet.col.subject"),
               t("sheet.col.asked"), t("sheet.col.has"), t("sheet.col.result"), t("sheet.col.confirmed")],
          [(r["law"], r["article"], r["title"], r["subject"], r["asked"], r["has"], MARK[r["state"]],
            t("sheet.yes") if r["confirmed"] else t("sheet.no")) for r in d["rows"]],
          (16, 22, 48, 34, 18, 14, 8, 10))
    ws = book.create_sheet(t("sheet.tab.exceptions")[:31])
    table(ws, [t("sheet.col.law"), t("sheet.col.article"), t("sheet.col.rule"), t("sheet.col.subject"),
               t("sheet.col.why"), t("sheet.col.when")],
          [(x["law"], x["article"], x["title"], x["subject"], x["why"], x["when"]) for x in d["exceptions"]],
          (16, 22, 40, 30, 50, 14))
    book.properties.creator = "ArqSynth BIM"
    book.save(path)
    return path
