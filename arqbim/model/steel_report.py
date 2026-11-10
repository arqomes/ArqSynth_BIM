"""(0.521) The steel structure's calculation report — «Memória de cálculo da estrutura metálica», the plan's step 8 as
the concrete's (model/structure_report): one HTML page, self-contained and printable to PDF, of what the program
worked out — the project, the codes and materials, the actions (the roof's loads, the snow, the wind), the model (its
pieces, its nodes, its supports, how it was made), the Eurocode 3 verification of each piece (its forces, its use, the
check that governs) and of each connection (EN 1993-1-8), the bill of materials — and what it is: a pre-design, the
structural design the engineer's, who signs it. The same look as the concrete's."""

import datetime

from .. import __version__
from ..core import ec3_joints, steel
from ..i18n import t
from . import design_text as dt
from .structure_report import _CSS, _e, _list, _table


def report_data(doc, settings=None):
    """What the report is made of: the project, the settings, the analysis (model/steel_analysis.Result), the
    connections checked, the bill of materials."""
    from . import schedules, steel_analysis, steel_connection_check
    settings = settings or doc.ifc.structural_settings()
    projects = doc.ifc.file.by_type("IfcProject")
    project = {k: v for k, v in (doc.title_block or {}).items() if isinstance(v, str) and v}
    project.setdefault("project", (projects[0].Name if projects else "") or "")
    analysis = steel_analysis.analyse(doc, settings)
    joints = steel_connection_check.check(doc, analysis) if not analysis.error else []
    names = {o.id: o.name for o in doc.objects.values() if o.is_bim}
    return {"project": project, "date": datetime.date.today().strftime("%d-%m-%Y"), "version": __version__,
            "settings": settings, "analysis": analysis, "joints": joints, "names": names,
            "bill": schedules.rows(doc, "steel")}


def _status(ok):
    return (t("ec3.ok"), "ok") if ok else (t("ec3.fails"), "falha")


def report_html(data):
    """The page of report_data's dict."""
    s = data["settings"]
    analysis = data["analysis"]
    names = data.get("names", {})
    parts = ["<!doctype html><html><head><meta charset='utf-8'><title>{}</title><style>{}</style></head><body>"
             "<div class='page'><h1>{}</h1>".format(_e(t("sreport.title")), _CSS, _e(t("sreport.title")))]
    # 1. the project
    p = data.get("project", {})
    rows = [(t("tb." + k), p.get(k)) for k in ("project", "client", "site", "author", "stage") if p.get(k)]
    rows += [(t("report.date"), data.get("date", "")), (t("report.program"), "ArqSynth BIM " + data.get("version", ""))]
    parts.append("<h2>1. {}</h2><table class='meta'>{}</table>".format(_e(t("report.s.project")), "".join(
        "<tr><td><b>{}</b></td><td>{}</td></tr>".format(_e(k), _e(v)) for k, v in rows)))
    # 2. codes and materials
    grades = sorted({r["grade"] for r in analysis.rows if r.get("grade")}) or ["S275"]
    lines = [t("sreport.codes")]
    for g in grades:
        (fy, fu), (fy40, fu40) = steel.GRADES[g]
        lines.append(t("sreport.grade", g=g, fy=dt.num(fy, 0), fu=dt.num(fu, 0), fy40=dt.num(fy40, 0)))
    lines.append(t("sreport.bolts", fub=dt.num(ec3_joints.FUB, 0), g2=dt.num(ec3_joints.GAMMA_M2, 2)))
    parts.append("<h2>2. {}</h2>{}".format(_e(t("report.s.materials")), _list(lines)))
    # 3. actions
    loads = analysis.loads or {}
    lines = [t("sreport.dead", g=dt.num(loads.get("dead", 0.0), 2)),
             t("sreport.imposed", use=t("actions.use." + s.roof_use), q=dt.num(loads.get("imposed", 0.0), 2),
               snow=dt.num(loads.get("snow", 0.0), 2)),
             t("sreport.wind", zone=s.wind_zone, terrain=s.terrain, qp=dt.num(loads.get("wind", 0.0), 2)),
             t("sreport.combos")]
    parts.append("<h2>3. {}</h2>{}".format(_e(t("report.s.actions")), _list(lines)))
    # 4. the model
    parts.append("<h2>4. {}</h2>".format(_e(t("report.s.model"))))
    if analysis.error:
        parts.append("<p class='falha'>{}</p>".format(_e(t("ec3.unstable") + " — " + analysis.error)))
    else:
        ctx = analysis.context or {}
        frame = ctx.get("frame")
        bars = sum(1 for m in frame.members if not m.id.startswith("link/")) if frame else 0
        links = sum(1 for m in frame.members if m.id.startswith("link/")) if frame else 0
        parts.append("<p>{}</p>".format(_e(t("sreport.model", pieces=len(analysis.rows), bars=bars, links=links,
                                               nodes=len(frame.nodes) if frame else 0,
                                               supports=len(frame.supports) if frame else 0))))
        parts.append("<p class='note'>{}</p>".format(_e(t("sreport.model_note"))))
    # 5. the members (EN 1993-1-1)
    rows = analysis.rows
    failing = sum(1 for r in rows if not r["ok"])
    parts.append("<h2>5. {}</h2><p>{}</p>".format(_e(t("sreport.s.members")), _e(t("sreport.members_summary",
                                                                                     n=len(rows), f=failing))))
    order = sorted(rows, key=lambda r: (-r["utilisation"], dt.natural(names.get(r["guid"], r["guid"]))))
    parts.append(_table([t("sched.col." + c) for c in ("mark", "piece", "section", "grade", "n_ed", "m_ed", "v_ed",
                                                         "deflection", "utilisation", "governing", "status")],
                        [(r["mark"], names.get(r["guid"], ""), r["section"], r["grade"], dt.num(r["n_ed"], 1),
                          dt.num(r["m_ed"], 1), dt.num(r["v_ed"], 1), "{:.0f} %".format(100 * r["deflection"]),
                          "{:.0f} %".format(100 * r["utilisation"]), t("ec3.check." + r["governing"]),
                          _status(r["ok"])) for r in order], numeric=(4, 5, 6, 7, 8)))
    # 6. the connections (EN 1993-1-8)
    joints = data.get("joints", [])
    parts.append("<h2>6. {}</h2><p>{}</p>".format(_e(t("sreport.s.joints")), _e(t(
        "sreport.joints_summary", n=len(joints), f=sum(1 for r in joints if not r["ok"])))))
    if joints:
        parts.append(_table([t("sched.col." + c) for c in ("connection", "connection_kind", "bolts", "bolt_shear",
                                                             "bolt_tension", "weld_use", "utilisation", "governing",
                                                             "status")],
                            [(r["name"], t("connection." + r["kind"]), r["bolts"], dt.num(r["shear"], 1),
                              dt.num(r["tension"], 1), "{:.0f} %".format(100 * r["weld"]),
                              "{:.0f} %".format(100 * r["utilisation"]), t("ec3j.check." + r["governing"]),
                              _status(r["ok"])) for r in joints], numeric=(3, 4, 5, 6)))
    # 7. the bill of materials
    bill = data.get("bill", [])
    parts.append("<h2>7. {}</h2>".format(_e(t("sreport.s.bill"))))
    if bill:
        total = sum(r["weight"] or 0.0 for r in bill)
        parts.append(_table([t("sched.col." + c) for c in ("mark", "piece", "section", "grade", "pieces", "weight")],
                            [(r["mark"], r["piece"], r["section"], r["grade"], r["pieces"], dt.num(r["weight"], 0))
                             for r in bill] + [(t("qty.total"), "", "", "", "", dt.num(total, 0))],
                            numeric=(4, 5)))
    # 8. methods, limits — and who signs
    parts.append("<h2>8. {}</h2>{}".format(_e(t("report.s.notes")), _list(t("sreport.notes").split("|"))))
    parts.append("<div class='sign'>{}</div>".format(_e(t("report.sign"))))
    parts.append("</div></body></html>")
    return "".join(parts)
