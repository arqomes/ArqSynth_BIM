"""The calculation report (0.167, Phase 9, step 5, «memória de cálculo»): one HTML page, self-contained (its style
in it, printable to PDF), of the structure as the program worked it out — the project (from the title block), the
codes and materials, the actions storey by storey (loads, wind, earthquake), the model's check, the analysis (the load
path, the drift, (0.222) the second order storey by storey, each member's forces), the Eurocode 2 verification of each member with all its notes, the
quantities, the reinforcement — and what it is: a pre-design, the structural design the engineer's, who signs it.
Taken over from the ArqSynth Modeler's calc_report; its words in the program's language."""

import html

from ..core import actions as act
from ..core import ec2
from ..i18n import t
from . import design_text as dt
from . import structure_quantities as sq

_CSS = ("body{font-family:'Segoe UI',Arial,sans-serif;color:#222;margin:0;background:#fff}"
        ".page{max-width:980px;margin:0 auto;background:#fff;padding:28px 40px}"
        "h1{font-size:1.45em;border-bottom:3px solid #222;padding-bottom:8px}"
        "h2{font-size:1.12em;margin-top:26px;border-bottom:1px solid #bbb;padding-bottom:4px}"
        "h3{font-size:1em;margin:14px 0 4px}"
        "table{border-collapse:collapse;width:100%;margin:8px 0;font-size:.85em}"
        "th,td{border:1px solid #ccc;padding:3px 7px;text-align:left;vertical-align:top}"
        "th{background:#eee}td.n{text-align:right;font-variant-numeric:tabular-nums}"
        ".meta td{border:none;padding:2px 10px 2px 0}.ok{color:#2e7d32;font-weight:600}"
        ".atencao{color:#b26a00;font-weight:600}.falha{color:#b0302a;font-weight:600}"
        ".note{color:#555;font-size:.85em}ul{margin:4px 0}li{margin:2px 0}"
        ".sign{margin-top:30px;padding:10px;border:1px solid #b0302a;color:#7a1f1a}"
        "figure{margin:12px 0;page-break-inside:avoid}figure svg{max-width:100%;height:auto;"
        "vertical-align:top;margin-right:8mm}"
        "figcaption{font-size:.85em;color:#555}"
        "@media print{body{background:#fff}.page{padding:0}}")


def _e(v):
    return html.escape(str(v if v is not None else ""))


def _table(head, rows, numeric=()):
    out = ["<table><tr>", "".join("<th>{}</th>".format(_e(h)) for h in head), "</tr>"]
    for row in rows:
        out.append("<tr>")
        for k, cell in enumerate(row):
            if isinstance(cell, tuple):                        # (text, css class)
                out.append("<td class='{}'>{}</td>".format(cell[1], _e(cell[0])))
            else:
                out.append("<td{}>{}</td>".format(" class='n'" if k in numeric else "", _e(cell)))
        out.append("</tr>")
    out.append("</table>")
    return "".join(out)


def _list(lines):
    return "<ul>{}</ul>".format("".join("<li>{}</li>".format(_e(x)) for x in lines))


def report_html(data):
    """The page of a ReportData-like dict: project {name, client, site, author, stage}, date, version, settings
    (core.actions.Settings), model (core.structural.AnalyticalModel), loads (BuildingActions), analysis, designs
    ([ElementDesign]), names {GlobalId: name}, quantities ([QuantityRow]), rebars (rows, totals)."""
    s = data["settings"]
    names = data.get("names", {})
    name = lambda g: names.get(g, g)          # noqa: E731
    parts = ["<!doctype html><html><head><meta charset='utf-8'><title>{}</title><style>{}</style></head><body>"
             "<div class='page'><h1>{}</h1>".format(_e(t("report.title")), _CSS, _e(t("report.title")))]
    # 1. the project
    p = data.get("project", {})
    rows = [(t("tb." + k), p.get(k)) for k in ("project", "client", "site", "author", "stage") if p.get(k)]
    rows += [(t("report.date"), data.get("date", "")), (t("report.program"), "ArqSynth BIM " + data.get("version", ""))]
    parts.append("<h2>1. {}</h2><table class='meta'>{}</table>".format(_e(t("report.s.project")), "".join(
        "<tr><td><b>{}</b></td><td>{}</td></tr>".format(_e(k), _e(v)) for k, v in rows)))
    # 2. codes and materials
    fck, fyk = act.CONCRETE[s.concrete], act.STEEL[s.steel]
    lines = [t("report.codes"),
             t("report.concrete", c=s.concrete, fck=fck, fcd=dt.num(fck / act.GAMMA_C, 1),
               fctm=dt.num(ec2.fctm(fck), 2), ecm=dt.num(s.ecm() / 1e6, 1)),
             t("report.steel", s=s.steel, fyk=fyk, fyd=dt.num(fyk / act.GAMMA_S, 0)),
             t("report.covers"),
             t("report.soil", kpa=dt.num(s.soil_kpa, 0))]
    analysis = data.get("analysis")
    walls = list(getattr(analysis, "walls", ()) or ())
    every = data.get("designs", [])
    if any(w.material == "masonry" for w in walls) or any(dt.masonry(e) for e in every):
        from ..core import ec6                          # (0.337) the walls' masonry (EC6; 0.345: the façades' too)
        fk, fd, fvk0, fb = ec6.strength(s)
        lines.append(t("report.masonry", unit=t("actions.masonry_unit." + s.masonry_unit), group=s.masonry_group,
                       fb=dt.num(fb, 1), mortar=s.masonry_mortar, fk=dt.num(fk, 2), gm=dt.num(s.masonry_gamma, 1),
                       fd=dt.num(fd, 2), fvk0=dt.num(fvk0, 2)))
        for type_name, own in data.get("masonry_types", ()):     # (0.346) the wall types with their own
            ts = ec6.with_masonry(s, own)
            tk, td, _v, tb = ec6.strength(ts)
            lines.append(t("report.masonry_type", type=type_name, unit=t("ec6.unit." + ts.masonry_unit),
                           group=ts.masonry_group, fb=dt.num(tb, 1), mortar=ts.masonry_mortar, fk=dt.num(tk, 2),
                           fd=dt.num(td, 2)))
        if any(n.code == "ec6_lateral" for e in every for n in e.design.notes):
            from . import wall_lateral
            fx1, fx2 = ec6.flexural(s)
            lines.append(t("report.masonry_flex", f1=dt.num(fx1, 2), f2=dt.num(fx2, 2),
                           mid=dt.num(wall_lateral.MIDDLE_C, 1), corner=dt.num(wall_lateral.CORNER_C, 1)))
    parts.append("<h2>2. {}</h2>{}".format(_e(t("report.s.materials")), _list(lines)))
    # 3. actions
    loads = data["loads"]
    psi0, psi1, psi2 = s.psi()
    lines = [t("report.uses", use=t("actions.use." + s.use), roof=t("actions.use." + s.roof_use),
               psi0=dt.num(psi0, 1), psi1=dt.num(psi1, 1), psi2=dt.num(psi2, 1)),
             t("report.dead", f=dt.num(s.finishes, 2), p=dt.num(s.partitions, 2)),
             t("report.wind", zone=s.wind_zone, vb=dt.num(act.WIND_ZONES[s.wind_zone], 0), terrain=s.terrain),
             t("report.snow", zone=s.snow_zone, h=dt.num(s.altitude, 0), sk=dt.num(act.snow_ground(s.snow_zone, s.altitude), 2),
               s=dt.num(s.snow(), 2), q=dt.num(s.imposed(roof=True), 2)),                    # (0.217)
             t("report.quake", z1=s.seismic_zone_1, a1=dt.num(act.SEISMIC_ZONES[s.seismic_zone_1], 2),
               z2=s.seismic_zone_2, a2=dt.num(act.SEISMIC_ZONES[s.seismic_zone_2], 2), ground=s.ground,
               imp=s.importance, q=dt.num(act.BEHAVIOUR_Q, 1))]
    parts.append("<h2>3. {}</h2>{}".format(_e(t("report.s.actions")), _list(lines)))
    if loads is not None and loads.storeys:
        parts.append(_table([t("actions.col." + c) for c in ("level", "area", "g", "q", "weight", "wind_x", "wind_y",
                                                               "quake_1", "quake_2")],
                            [(dt.num(st.level, 2), dt.num(st.area, 1), dt.num(st.g, 1), dt.num(st.q, 1),
                              dt.num(st.weight, 1), dt.num(st.wind_x, 1), dt.num(st.wind_y, 1), dt.num(st.quake_1, 1),
                              dt.num(st.quake_2, 1)) for st in loads.storeys], numeric=range(9)))
        parts.append("<p>{}</p>".format(_e(t("actions.summary", t1=dt.num(loads.period, 3), sd1=dt.num(loads.sd_1, 2),
                                                 sd2=dt.num(loads.sd_2, 2), b1=dt.num(loads.base_1, 1),
                                                 b2=dt.num(loads.base_2, 1)))))
    # 4. the model checked
    model = data["model"]
    issues = list(model.issues) if model is not None else []
    nc = sum(1 for m in model.members if m.kind == "column") if model is not None else 0
    nb = sum(1 for m in model.members if m.kind == "beam") if model is not None else 0
    text = t("report.model", nodes=len(model.nodes) if model else 0, c=nc, b=nb, s=len(model.supports) if model else 0,
             p=len(model.panels) if model else 0)
    if model is not None and model.walls:           # (0.335) the load-bearing walls
        text += " " + t("report.model_walls", w=len(model.walls))
    parts.append("<h2>4. {}</h2><p>{}</p>".format(_e(t("report.s.model")), _e(text)))
    if issues:
        parts.append(_table([t("report.col.severity"), t("report.col.element"), t("report.col.issue")],
                            [(t("struct.sev." + i.severity), ", ".join(name(g) for g in i.guids),
                              t("struct.issue." + i.code)) for i in issues]))
    else:
        parts.append("<p>{}</p>".format(_e(t("report.no_issues"))))
    # 5. the analysis
    parts.append("<h2>5. {}</h2>".format(_e(t("report.s.analysis"))))
    if analysis is None or analysis.error:
        parts.append("<p>{}</p>".format(_e(t("analysis.error", e=dt.error_text(analysis.error) if analysis else "—"))))
    elif not analysis.members:                      # (0.336) only load-bearing walls: no frame
        parts.append("<p>{}</p>".format(_e(t("analysis.walls_only", w=len(walls)))))
    else:
        drift = "1/{:.0f}".format(1 / analysis.drift_wind) if analysis.drift_wind > 1e-12 else "—"
        parts.append("<p>{}</p><p class='note'>{}</p>".format(
            _e(t("analysis.summary", n=len(analysis.members), put=dt.num(analysis.loads_in),
                 up=dt.num(analysis.reactions_up), drift=drift)
               + (" " + t("analysis.walls_too", w=len(walls)) if walls else "")), _e(t("analysis.note"))))
    if analysis is not None and not analysis.error:
        if analysis.sways:                                  # (0.222) the second order, storey by storey
            css = {"ignored": "ok", "amplified": "atencao"}
            parts.append("<p>{}</p>".format(_e(dt.second_order_text(analysis))))
            parts.append(_table([t("analysis.sway.col." + c) for c in ("case", "level", "height", "p", "v", "drift",
                                                                         "theta", "verdict")],
                                [values[:7] + ((values[7], css.get(verdict, "falha")),)
                                 for values, verdict in dt.sway_rows(analysis)], numeric=range(1, 7)))
            parts.append("<p class='note'>{}</p>".format(_e(t("analysis.sway_note"))))
        order = sorted(analysis.members, key=lambda m: (m.kind != "column", dt.natural(name(m.guid)), m.id))
        rows = [dt.wall_values(w, name(w.guid)) for w in sorted(walls, key=lambda w: dt.natural(name(w.guid)))]
        for m in order:
            label = name(m.guid) + (" ({})".format(m.id.split("/")[-1]) if "/" in m.id else "")
            defl = "{} mm".format(dt.num(m.deflection * 1000, 1)) if m.kind == "beam" and m.deflection > 0 else ""
            rows.append((label, dt.num(m.length, 2), dt.num(m.n_min), dt.num(m.n_max), dt.num(m.v),
                         dt.num(m.m_pos if m.kind == "beam" else m.m_column),
                         dt.num(m.m_neg if m.kind == "beam" else 0.0), defl, m.combo))
        for p in sorted(analysis.panels, key=lambda p: dt.natural(name(p.guid))):     # (0.223: the slabs, shells)
            rows.append(dt.panel_values(p, name(p.guid)))
        parts.append(_table([t("analysis.col." + c) for c in ("element", "length", "n_min", "n_max", "v", "m_pos",
                                                                "m_neg", "deflection", "combo")], rows,
                            numeric=range(1, 8)))
        if analysis.panels:
            parts.append("<p class='note'>{}</p>".format(_e(t("analysis.slab_note",
                                                               size=dt.num(analysis.shell_size, 2)))))
        if walls:
            parts.append("<p class='note'>{}</p>".format(_e(t("analysis.wall_note"))))
    # 6. the Eurocode 2 (and 6) verification
    designs = dt.ordered(data.get("designs", []), names)
    counts = {k: sum(1 for e in designs if e.design.status == k) for k in (ec2.OK, ec2.WARN, ec2.FAIL)}
    text = t("ec2.summary", n=len(designs), ok=counts[ec2.OK], w=counts[ec2.WARN], f=counts[ec2.FAIL], c=s.concrete,
             s=s.steel)
    masonry = sum(1 for e in designs if dt.masonry(e))
    if masonry:                                     # (0.337) the walls by EC6 (0.346: their types' fk)
        text += " " + t("ec6.summary", n=masonry, fk=dt.masonry_fk(designs, s))
    parts.append("<h2>6. {}</h2><p>{}</p>".format(_e(t("report.s.design")), _e(text)))
    parts.append(_table([t("ec2.col.element"), t("ec2.col.status"), t("ec2.col.ratio"), t("ec2.col.bars"),
                         t("ec2.col.note")],
                        [(name(e.guid), (t("ec2.status." + e.design.status), e.design.status),
                          "{:.0f} %".format(100 * e.design.ratio), dt.bars_text(e.kind, e.design),
                          dt.note_text(dt.main_note(e.design)) if dt.main_note(e.design) else "")
                         for e in designs], numeric=(2,)))
    for e in designs:
        parts.append("<h3>{} — <span class='{}'>{}</span></h3>{}".format(
            _e(name(e.guid)), e.design.status, _e(t("ec2.status." + e.design.status)),
            _list(dt.note_text(n) for n in e.design.notes)))
    # 7. quantities
    rows_q = data.get("quantities", [])
    parts.append("<h2>7. {}</h2>".format(_e(t("report.s.quantities"))))
    if rows_q:
        by_kind, whole = sq.totals(rows_q)
        parts.append(_table([t("qty.col." + c) for c in ("element", "storey", "concrete", "formwork", "steel",
                                                           "rate")],
                            [(name(r.guid), r.storey, dt.num(r.concrete, 3), dt.num(r.formwork, 2),
                              dt.num(r.steel, 1) if r.has_bars else "—",
                              (dt.num(r.rate, 0), "falha") if r.implausible else (dt.num(r.rate, 0) if r.has_bars
                                                                                  else "—"))
                             for r in rows_q], numeric=(2, 3, 4, 5)))
        parts.append(_table([t("qty.col.kind"), t("qty.col.concrete"), t("qty.col.formwork"), t("qty.col.steel")],
                            [(t("qty.kind." + k), dt.num(v[0], 3), dt.num(v[1], 2), dt.num(v[2], 1))
                             for k, v in sorted(by_kind.items(), key=lambda kv: dt.KIND_ORDER.get(kv[0], 9))]
                            + [(t("qty.total"), dt.num(whole[0], 3), dt.num(whole[1], 2), dt.num(whole[2], 1))],
                            numeric=(1, 2, 3)))
    # 8. the reinforcement
    rows_r, totals_r = data.get("rebars", ([], {}))
    parts.append("<h2>8. {}</h2>".format(_e(t("report.s.rebars"))))
    if rows_r:
        parts.append(_table([t("rsched.col." + c) for c in ("mark", "element", "role", "diameter", "count", "length",
                                                              "shape", "weight")],
                            [(r["mark"], r["host_name"], t("rsched.role." + r["role"]) if r["role"] else "",
                              r["diameter"], r["count"], dt.num(r["length"], 2), r["shape"], dt.num(r["weight"], 1))
                             for r in rows_r], numeric=(0, 3, 4, 5, 7)))
        parts.append(_table([t("rsched.col.diameter"), t("report.col.total_length"), t("rsched.col.weight")],
                            [("Ø{}".format(d), dt.num(m, 1), dt.num(kg, 1)) for d, (m, kg) in totals_r.items()]
                            + [(t("qty.total"), "", dt.num(sum(kg for _m, kg in totals_r.values()), 1))],
                            numeric=(1, 2)))
    else:
        parts.append("<p>{}</p>".format(_e(t("rsched.empty"))))
    drawings = data.get("drawings", [])           # (0.233) each member's reinforcement drawing, 1:50 (0.234: its cut)
    if drawings:
        parts.append("<h3>{}</h3>".format(_e(t("report.drawings"))))
        for label, picture in drawings:
            parts.append("<figure>{}<figcaption>{}</figcaption></figure>".format(picture, _e(label)))
    # 9. methods, limits — and who signs
    parts.append("<h2>9. {}</h2>{}".format(_e(t("report.s.notes")), _list(t("report.notes").split("|"))))
    parts.append("<div class='sign'>{}</div>".format(_e(t("report.sign"))))
    parts.append("</div></body></html>")
    return "".join(parts)
