"""(0.570, PLANO.md «Gerador de revestimentos 3D em IFC», step 10) What a Revestimento takes and how it is set out:

- quantities: the pieces whole and cut of each mark, the area laid and the pieces to buy (every cut one a whole one,
  and the waste that makes), the joints' length, the glue and the grout by weight;
- the layout drawing (DXF, mm): the face in its own plane, the pieces whole and cut on their layers, each cut one's
  mark, the face's outline and its size — the tiler's setting-out plan.

Pure geometry and figures (no window)."""

import math

import numpy as np
from shapely.geometry import Polygon

GLUE_KG_M2_MM = 1.4       # kg per m² per mm of a cement adhesive bed (a supplier's figure)
GROUT_KG_DM3 = 1.7        # kg per dm³ of grout


def quantities(result, mats, p):
    """{rows: [{mark, material, w, h, whole, cut, buy, area}], area, buy_area, waste, joints_m, glue_kg, grout_kg,
    pieces, whole, cut} of a Revestimento: `result`/`mats` its pieces (tiled_pieces), `p` its tiled_params."""
    d = p["layout"]
    groups = {}
    for piece, m in zip(result.pieces, mats):
        key = (piece.kind, m or p["material"])
        g = groups.setdefault(key, {"whole": 0, "cut": 0, "area": 0.0})
        g["whole" if piece.whole else "cut"] += 1
        g["area"] += piece.area
    rows = []
    buy_area = 0.0
    for (kind, mat), g in sorted(groups.items()):
        w, h = result.kinds.get(kind, (d["w"], d["h"]))
        buy = g["whole"] + g["cut"]                       # (a cut piece is a whole one bought)
        one = w * h if d["pattern"] not in ("hexagono", "escama", "continuo") else \
            (g["area"] / max(g["whole"] + 0.5 * g["cut"], 1))
        if d["pattern"] == "continuo":
            one, buy = g["area"], 1
        buy_area += buy * one
        rows.append({"mark": kind, "material": mat, "w": w, "h": h, "whole": g["whole"], "cut": g["cut"],
                     "buy": buy, "area": g["area"]})
    area = sum(piece.area for piece in result.pieces)
    perim = sum(Polygon(piece.points).length for piece in result.pieces)
    joints_m = perim / 2.0                                # (each joint between two pieces)
    jw = max(d["joint"], d.get("joint_v") or 0.0)
    depth = max(p["thickness"] - p["recess"], 0.0)
    grout = joints_m * jw * depth * 1000.0 * GROUT_KG_DM3 if p.get("grout") else 0.0
    glue = area * p["bed"] * 1000.0 * GLUE_KG_M2_MM if p["bed"] > 0 else 0.0
    return {"rows": rows, "area": area, "buy_area": buy_area,
            "waste": (buy_area - area) / area if area > 1e-9 else 0.0, "joints_m": joints_m, "glue_kg": glue,
            "grout_kg": grout, "pieces": len(result.pieces), "whole": sum(r["whole"] for r in rows),
            "cut": sum(r["cut"] for r in rows)}


def layout_dxf(result, face, name="Revestimento", marks=True):
    """The DXF text (mm) of the layout: the face (layer FACE), its openings (VAOS), the whole pieces (PECAS), the cut
    ones (CORTES) with their mark and size (MARCAS), and the face's size (COTAS). Returns (text, how many pieces)."""
    from ..model import dxf
    w = dxf._Writer()
    s = 1000.0
    w.polyline("FACE", [tuple(np.asarray(c) * s) for c in list(face.exterior.coords)[:-1]], closed=True)
    for ring in face.interiors:
        w.polyline("VAOS", [tuple(np.asarray(c) * s) for c in list(ring.coords)[:-1]], closed=True)
    for piece in result.pieces:
        layer = "PECAS" if piece.whole else "CORTES"
        w.polyline(layer, [tuple(np.asarray(c) * s) for c in piece.points], closed=True)
        for h in piece.holes:
            w.polyline(layer, [tuple(np.asarray(c) * s) for c in h], closed=True)
        if marks and not piece.whole:
            g = Polygon(piece.points)
            c = g.representative_point()
            x0, y0, x1, y1 = g.bounds
            size = min(x1 - x0, y1 - y0)
            w.text("MARCAS", (c.x * s, c.y * s), max(8.0, min(40.0, size * s / 4.0)),
                   "{}{}".format(piece.kind, "" if size > 0.15 else ""))
    x0, y0, x1, y1 = face.bounds
    w.text("COTAS", (x0 * s, (y0 - 0.25) * s), 80.0,
           "{} — {:.2f} × {:.2f} m — {} peças ({} cortadas)".format(
               name, x1 - x0, y1 - y0, len(result.pieces), sum(1 for q in result.pieces if not q.whole)))
    return w.document({"FACE": 7, "VAOS": 1, "PECAS": 8, "CORTES": 30, "MARCAS": 3, "COTAS": 7}), \
        len(result.pieces)


def table(q, names=None):
    """(header, rows) of the quantities as a table (for XLSX / CSV): one row a mark and material, then the totals."""
    names = names or {}
    header = ["Marca", "Material", "Peça (cm)", "Inteiras", "Cortadas", "A comprar", "Área assente (m²)"]
    rows = [[r["mark"], names.get(r["material"], r["material"]),
             "{:.0f} × {:.0f}".format(r["w"] * 100, r["h"] * 100), r["whole"], r["cut"], r["buy"],
             round(r["area"], 2)] for r in q["rows"]]
    rows += [[], ["Total assente (m²)", round(q["area"], 2)], ["A comprar (m²)", round(q["buy_area"], 2)],
             ["Desperdício (%)", round(q["waste"] * 100.0, 1)], ["Juntas (m)", round(q["joints_m"], 1)],
             ["Cola (kg)", round(q["glue_kg"], 1)], ["Betume (kg)", round(q["grout_kg"], 1)]]
    return header, rows
