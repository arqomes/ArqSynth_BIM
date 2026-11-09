"""(0.501) The steel structure for the workshop: a DSTV NC1 file per piece mark (core/dstv) — a section's: its length
over all, its sizes, kg/m, the angles its ends are cut at (a mitre's); a plate's: its outline and its holes — and the
cutting of the bars (core/bar_cutting): for each section, the bars to buy and how the pieces come out of them."""

import json
import math
import os

import numpy as np

from ..core import bar_cutting, dstv, steel


def _overall(doc, guid):
    """A piece's length over all along its own axis (mm), from its body as drawn."""
    obj = doc.get(guid)
    m = doc.ifc.placement(guid)
    axis = m[:3, 2] / np.linalg.norm(m[:3, 2])
    if obj is None or obj.mesh is None or not len(obj.mesh.verts):
        return 0.0
    along = obj.mesh.verts @ axis
    return float(along.max() - along.min()) * 1000.0


def _angles(cuts):
    """(web at the start, web at the end, flanges at the start, flanges at the end) — the cut angles (degrees) of a
    piece's ends: 0 square."""
    web, flange = [0.0, 0.0], [0.0, 0.0]
    for c in cuts:
        k = int(c.get("end", 0))
        nx, ny, nz = (float(v) for v in c["n"])
        nz = nz if k == 1 else -nz
        web[k] = round(math.degrees(math.atan2(ny, nz)), 2)
        flange[k] = round(math.degrees(math.atan2(nx, nz)), 2)
    return web[0], web[1], flange[0], flange[1]


def nc1_files(doc):
    """{mark: NC1 text} of every steel piece mark (the marks as Numerar would give them)."""
    marks, pieces = doc.ifc.steel_marks()
    groups = {}
    for p in pieces:
        groups.setdefault(marks.get(p["guid"], ""), []).append(p)
    out = {}
    for mark, members in groups.items():
        p = members[0]
        e = doc.ifc.by_guid(p["guid"])
        if p["prefix"] == "Ch":
            plate = json.loads(doc.ifc._params(e).get("Chapa") or "{}")
            if not plate:
                continue
            L, W, t = float(plate["L"]), float(plate["W"]), float(plate["t"])
            holes = [("v", x + L / 2.0, y + W / 2.0, d) for x, y, d in plate.get("furos", [])]
            header = dict(order="1", drawing=mark, phase="1", mark=mark, grade=plate.get("grade") or "S275",
                          quantity=len(members), profile="PL{:g}*{:g}".format(t, W), code="B", length=L, h=W, b=0.0,
                          tf=0.0, tw=t, r=0.0, kg_m=t * W * 1e-6 * steel.DENSITY, paint_m=2.0 * W / 1000.0)
            contour = [(x + L / 2.0, y + W / 2.0) for x, y in plate.get("contorno") or ()] or \
                [(0.0, 0.0), (L, 0.0), (L, W), (0.0, W)]                         # (0.503: a gusset's own outline)
            out[mark] = dstv.nc1(header, holes, contour, ("v",) + _mark_spot(contour, holes) + (mark,))
            continue
        sec = steel.get(p["signature"][0])
        if sec is None:
            continue
        props = steel.properties(sec.name)
        cuts = doc.ifc.steel_cuts(e)[0]
        header = dict(order="1", drawing=mark, phase="1", mark=mark, grade=p["grade"] or "S275",
                      quantity=len(members), profile=sec.name, code=dstv.CODES.get(sec.family, "SO"),
                      length=_overall(doc, p["guid"]) or p["length"] * 1000.0, h=sec.h, b=sec.b, tf=sec.tf,
                      tw=sec.tw, r=sec.r, kg_m=props["mass"], paint_m=props["paint"], cuts=_angles(cuts))
        holes = [(f, x, y, d) for f, x, y, d, _w in doc.ifc.member_holes(p["guid"])]   # (0.512: its own holes)
        out[mark] = dstv.nc1(header, holes, marking=("v", MARK_FROM_END, sec.h / 2.0, mark))   # (0.511: on the web,
    return out                                                                                  # near its start)


MARK_FROM_END = 100.0           # mm: (0.511) a section's marking this far from its start, on its web (face v)


def _mark_spot(contour, holes):
    """(0.511) Where a plate's marking goes (mm, its NC1's x, y): its middle, or else a point inside it clear of its
    holes (twice a hole's diameter off it, its letters' height off its edge)."""
    from shapely.geometry import Point, Polygon
    shape = Polygon(contour)
    if not shape.is_valid or shape.area <= 0.0:
        return 0.0, 0.0
    x0, y0, x1, y1 = shape.bounds
    tries = [((x0 + x1) / 2, (y0 + y1) / 2)] + [(x0 + (x1 - x0) * fx, y0 + (y1 - y0) * fy)
                                                for fy in (0.5, 0.3, 0.7, 0.15, 0.85) for fx in (0.3, 0.5, 0.7, 0.15)]
    inner = shape.buffer(-dstv.MARK_HEIGHT)
    for x, y in tries:
        if inner.contains(Point(x, y)) and all(math.hypot(x - hx, y - hy) >= 2.0 * d for _f, hx, hy, d in holes):
            return round(x, 1), round(y, 1)
    c = shape.representative_point()
    return round(c.x, 1), round(c.y, 1)


GAP_DXF = 50.0                  # mm: (0.511) between the plates laid side by side in their DXF
TEXT_DXF = 10.0                 # mm: their texts' height


def plates_dxf(doc):
    """(0.511) The plates for the laser or the plasma, as DXF (mm, R12): each plate mark once, side by side — its
    outline (layer CONTORNO), its holes (FUROS), its mark, how many, its thickness and grade (TEXTOS) under it. None when
    the model has no plate."""
    from . import dxf
    marks, pieces = doc.ifc.steel_marks()
    groups = {}
    for p in pieces:
        if p["prefix"] == "Ch":
            groups.setdefault(marks.get(p["guid"], ""), []).append(p)
    if not groups:
        return None
    from ..core import steel_marks
    w = dxf._Writer()
    x = 0.0
    for mark in sorted(groups, key=steel_marks.sort_key):
        members = groups[mark]
        plate = json.loads(doc.ifc._params(doc.ifc.by_guid(members[0]["guid"])).get("Chapa") or "{}")
        if not plate:
            continue
        L, W, t = float(plate["L"]), float(plate["W"]), float(plate["t"])
        ring = [(x + cx + L / 2.0, cy + W / 2.0) for cx, cy in plate.get("contorno") or ()] or \
            [(x, 0.0), (x + L, 0.0), (x + L, W), (x, W)]
        w.polyline("CONTORNO", ring, closed=True)
        for hx, hy, d in plate.get("furos", []):
            w.circle("FUROS", (x + hx + L / 2.0, hy + W / 2.0), d / 2.0)
        w.text("TEXTOS", (x, -2.0 * TEXT_DXF), TEXT_DXF, mark)
        w.text("TEXTOS", (x, -3.6 * TEXT_DXF), TEXT_DXF * 0.7, "{} x PL{:g} {}".format(        # (ASCII: R12)
            len(members), t, plate.get("grade") or "S275"))
        x += L + GAP_DXF
    return w.document({"CONTORNO": 7, "FUROS": 1, "TEXTOS": 3})


def cutting(doc, stock=bar_cutting.STOCK):
    """The bars to buy, a section and grade each: [{"section", "grade", "bars", "bought" m, "used" m, "waste" %,
    "plan": [[(mark, mm)…] a bar each]}]."""
    marks, pieces = doc.ifc.steel_marks()
    by_section = {}
    for p in pieces:
        if p["prefix"] == "Ch":
            continue
        length = _overall(doc, p["guid"]) or p["length"] * 1000.0
        by_section.setdefault((p["section"], p["grade"]), []).append((marks.get(p["guid"], ""), round(length, 1)))
    out = []
    for (section, grade), items in sorted(by_section.items()):
        bars = bar_cutting.plan(items, stock)
        n, bought, used, waste, _offcuts = bar_cutting.summary(bars, stock)
        out.append({"section": section, "grade": grade, "bars": n, "bought": bought, "used": used, "waste": waste,
                    "plan": [b["pieces"] for b in bars]})
    return out


def write(doc, folder):
    """The NC1 files (<mark>.nc1) and the cutting plan (corte_de_barras.csv) written in `folder`. Their paths."""
    os.makedirs(folder, exist_ok=True)
    paths = []
    for mark, text in nc1_files(doc).items():
        path = os.path.join(folder, "{}.nc1".format(mark or "sem_marca"))
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        paths.append(path)
    path = os.path.join(folder, "corte_de_barras.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write("Secção;Aço;Barras de {:g} m;Comprados (m);Peças (m);Desperdício (%);Plano de corte\n".format(
            bar_cutting.STOCK / 1000.0))
        for r in cutting(doc):                          # (decimal commas, as the Portuguese Excel reads them)
            plan = " | ".join(" + ".join("{} {:g}".format(m, l) for m, l in bar) for bar in r["plan"])
            numbers = ["{:.2f}".format(r["bought"]), "{:.2f}".format(r["used"]), "{:.1f}".format(r["waste"])]
            f.write("{};{};{};{};{}\n".format(r["section"], r["grade"], r["bars"],
                                              ";".join(n.replace(".", ",") for n in numbers), plan))
    paths.append(path)
    text = plates_dxf(doc)                              # (0.511) the plates for the laser / the plasma
    if text:
        path = os.path.join(folder, "chapas.dxf")
        with open(path, "w", encoding="ascii", errors="replace", newline="\n") as f:
            f.write(text)
        paths.append(path)
    return paths
