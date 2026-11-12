"""Schedules ("Tabelas", Phase 3, step 3): the elements of a category with their
quantities, read from the model whenever it changes — so a schedule is never out of
date. Lengths come from the elements' base quantities (see IfcModel.schedule_info);
volumes from the shapes on screen (exact: openings taken off); a wall's area is its
volume over its thickness (one face, openings taken off), a slab's the same in plan.

Editing a cell goes through the same commands as the Properties panel (one undo step).
Exported as CSV or (0.370) as an Excel workbook (XLSX: openpyxl, the owner's go-ahead).
"""

import ast
import csv
import math
import os
import re
import uuid
from dataclasses import dataclass, field

# key -> (IFC classes or None for "the rest", columns shown)
CATEGORIES = {
    "walls": (("IfcWall", "IfcWallStandardCase"), ("name", "type", "storey", "length", "height", "thickness", "area",
                                                  "volume")),
    "slabs": (("IfcSlab",), ("name", "type", "storey", "thickness", "area", "volume")),
    # (0.265) the roofs: their sloped and plan areas; a roof by blocks' edges' lengths, by kind
    "roofs": (("IfcRoof",), ("name", "type", "storey", "area", "projected", "eaves", "ridges", "hips", "valleys",
                             "gables", "tops", "volume")),
    # (0.277) the roofs' carpentry: a line a kind of piece a roof (its section, pieces, metres, m³ of timber)
    "carpentry": ((), ("roof", "piece", "section", "pieces", "metres", "volume")),
    # (0.279) the roofs' tiles: a line a roof (its tile, the tiles and those cut, the ridge tiles, kg, m²)
    "tiles": ((), ("roof", "tile", "tiles", "cut", "caps", "weight", "area")),
    # (0.544) the perforated panels (the Visual Graph's and the others): a line a finish — its wall, its boards, its
    # holes, its open area, its area
    "perforated": ((), ("name", "host", "panels", "holes", "open_area", "area")),
    "columns": (("IfcColumn",), ("name", "type", "storey", "height", "volume")),
    # (0.500) the steel structure: a line a mark (its pieces, their section, grade, cut length, kg/m, kg, paint m²); the
    # bolts and anchor bolts: a line a kind and size
    "steel": ((), ("mark", "piece", "section", "grade", "pieces", "cut_length", "metres", "kg_m", "weight", "paint")),
    "bolts": ((), ("bolt", "bolt_kind", "count")),
    # (0.501) the bars to buy: a line a section (bars of 12 m, metres bought, metres of pieces, waste)
    "cutting": ((), ("section", "grade", "bars", "bought", "used", "waste")),
    # (0.514) the erection: a line an assembly (a piece and the plates welded to it), in the order it goes up — its
    # phase, its mark, what it is, its plates, its weight to lift, its centre of gravity
    "erection": ((), ("order", "phase", "mark", "piece", "parts", "weight", "cog")),
    # (0.516) Eurocode 3: a line a piece — its design forces, its deflection, how much of its resistance it uses, the
    # check that governs, OK or not
    "steel_check": ((), ("mark", "piece", "section", "grade", "n_ed", "m_ed", "v_ed", "deflection", "utilisation",
                         "governing", "status")),
    # (0.520) EN 1993-1-8: a line a connection — its bolts, a bolt's shear and tension, its welds' use, its use
    "steel_joints": ((), ("connection", "connection_kind", "bolts", "bolt_shear", "bolt_tension", "weld_use",
                          "utilisation", "governing", "status")),
    "doors": (("IfcDoor",), ("name", "type", "storey", "width", "height", "host")),
    "windows": (("IfcWindow",), ("name", "type", "storey", "width", "height", "host")),
    # (0.125) the rooms: their areas, their finishes (read from the IFC's spaces, not from the shapes on screen)
    "rooms": (("IfcSpace",), ("number", "name", "storey", "area", "perimeter", "height")),
    "finishes": (("IfcSpace",), ("number", "name", "storey", "floor", "walls", "ceiling", "area")),
    # (0.144) the load schedule: the circuits (not elements: groups of them)
    "circuits": ((), ("name", "circuit_type", "board", "points", "power", "current", "breaker", "section", "conduit",
                      "check")),
    # (0.147) the electrical quantities: the points of each kind, the conduits' metres of each type, the circuits
    "electrical": ((), ("item", "count", "metres")),
    # (0.194) the keynotes used (the legend for the sheets): their code, text, how many elements carry each
    "keynotes": ((), ("code", "keynote_text", "count")),
    "other": (None, ("name", "class", "type", "storey", "volume")),
}
ORDER = ("walls", "slabs", "roofs", "carpentry", "tiles", "perforated", "columns", "steel", "bolts", "cutting", "erection",
         "steel_check", "steel_joints", "doors", "windows",
         "rooms", "finishes", "circuits", "electrical", "keynotes", "other")
ROOMS = ("rooms", "finishes")
EDGES = ("eaves", "ridges", "hips", "valleys", "gables", "tops")         # (0.265) a roof's edges, by kind
NUMBERS = {"length", "height", "thickness", "width", "area", "volume", "perimeter", "projected", "cut_length", *EDGES}
SUMMED = {"length", "area", "volume", "power", "conduit", "metres", "projected", "pieces", "tiles", "cut", "caps",
          "panels", "holes",                                                                   # (0.544)
          "weight", "paint", *EDGES}
UNITS = {"power": "{:.0f} W", "current": "{:.2f} A", "breaker": "{:.0f} A", "section": "{:g} mm²",   # (0.144)
         "conduit": "{:.2f} m", "metres": "{:.2f} m",                                        # (its conduits, 0.146)
         "weight": "{:.0f} kg",                                                              # (tiles, 0.279)
         "kg_m": "{:.1f} kg/m", "paint": "{:.2f} m²",                                       # (0.500: steel)
         "bought": "{:.2f} m", "used": "{:.2f} m", "waste": "{:.1f} %",                     # (0.501: the bars)
         "n_ed": "{:.1f} kN", "m_ed": "{:.1f} kN·m", "v_ed": "{:.1f} kN",                   # (0.516: EC3)
         "deflection": "{:.0f} %", "utilisation": "{:.0f} %",
         "bolt_shear": "{:.1f} kN", "bolt_tension": "{:.1f} kN", "weld_use": "{:.0f} %",       # (0.520)
         "open_area": "{:.0f} %"}                                                            # (0.544)
COUNTS = ("count", "points", "pieces", "tiles", "cut", "caps", "panels", "holes")
# column -> (Properties panel action, element kinds it applies to) for the cells one can edit
EDITABLE = {"name": ("name", None), "length": ("length", ("wall",)), "height": ("height", ("wall",))}
COLUMN_HEIGHT = ("column_height", ("column",))     # a column's height
# a room's cells (0.125): its Properties panel actions ("room_finish:<its Pset_SpaceCoveringRequirements key>")
ROOM_EDITABLE = {"number": "room_number", "name": "room_name", "floor": "room_finish:FloorCovering",
                 "walls": "room_finish:WallCovering", "ceiling": "room_finish:CeilingCovering"}
TEXT_ACTIONS = ("name", "room_name", "room_number", "room_finish", "circuit_name")   # (typed as text, not a length)
# a circuit's cells (0.144): its name, its breaker (A), its cable's section (mm²)
CIRCUIT_EDITABLE = {"name": "circuit_name", "breaker": "circuit_breaker", "section": "circuit_section"}


def _natural(text):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", text or "")]


def category_of(ifc_class):
    for key in ORDER[:-1]:
        if ifc_class in CATEGORIES[key][0]:
            return key
    return "other"


def _spaces(doc):
    try:
        return doc.ifc.spaces()
    except Exception:                                  # (the IFC still being read, or a file without them)
        return []


def counts(doc):
    """{category: number of elements} (for the category list)."""
    out = dict.fromkeys(ORDER, 0)
    for o in doc.objects.values():
        if o.is_bim:
            out[category_of(o.ifc_class)] += 1
    out["rooms"] = out["finishes"] = len(_spaces(doc))
    out["circuits"] = len(circuit_rows(doc))
    out["carpentry"] = len(carpentry_rows(doc))
    out["tiles"] = len(tiles_rows(doc))
    out["perforated"] = len(_perforated_finishes(doc))   # (0.544)
    out["steel"] = len(steel_rows(doc))                # (0.500)
    out["bolts"] = len(bolt_rows(doc))
    out["cutting"] = len(cutting_rows(doc))            # (0.501)
    out["erection"] = len(erection_rows(doc))          # (0.514)
    out["steel_check"] = out["erection"]               # (0.516: a line a piece — not analysed just to count)
    out["steel_joints"] = _connections_count(doc)      # (0.520)
    out["electrical"] = len(electrical_rows(doc))
    out["keynotes"] = len(keynote_rows(doc))
    return out


def keynote_rows(doc):
    """(0.194) The keynotes used, as the schedule "Notas-chave" lists them (model/keynotes.legend_rows)."""
    from ..i18n import lang
    from .keynotes import legend_rows
    try:
        return legend_rows(doc, lang())
    except Exception:                                  # (the IFC still being read)
        return []


def electrical_rows(doc):
    """(0.147) The electrical quantities: dicts with "guid" (None), "kind" "quantity", "item", "count", "metres"."""
    from .electrical_check import quantities
    try:
        found = quantities(doc)
    except Exception:                                  # (the IFC still being read)
        return []
    return [{"guid": None, "kind": "quantity", "item": item, "name": item, "type": item, "storey": "", "count": n,
             "metres": metres} for item, n, metres in found if n]


def carpentry_rows(doc):
    """(0.277) The roofs' carpentry: dicts with "guid" (the roof's), "kind" "carpentry", "roof", "piece", "section"
    (its width × height), "pieces", "metres", "volume" (m³) — a kind of piece of a roof each."""
    from ..i18n import t
    try:
        roofs = [r for r in doc.ifc.file.by_type("IfcRoof") if doc.ifc.carpentry_of(r.GlobalId) is not None]
    except Exception:                                  # (the IFC still being read)
        return []
    from ..ifc.carpentry import settings_from
    out = []
    for roof in roofs:
        settings = settings_from(doc.ifc._params(doc.ifc.carpentry_of(roof.GlobalId)).get("Madeiramento"))
        for role, (n, length, volume) in (doc.ifc.carpentry_summary(roof.GlobalId) or {}).items():
            w, h = settings.section(role)
            out.append({"guid": roof.GlobalId, "kind": "carpentry", "roof": roof.Name or "", "name": roof.Name or "",
                        "type": t("carp." + role), "storey": "", "piece": t("carp." + role),
                        "section": "{:g} × {:g} cm".format(round(w * 100, 1), round(h * 100, 1)).replace(".", ","),
                        "pieces": n, "metres": length, "volume": volume})
    return out


def steel_rows(doc):
    """(0.500) The steel structure: a line a mark — dicts with "guid" (its first piece's), "kind" "steel", "mark",
    "piece" (what it is), "section", "grade", "pieces", "cut_length" (m, each), "metres" (all), "kg_m", "weight" (kg,
    all), "paint" (m², all) —, in the marks' order. The marks the pieces get (kept where they can be: see
    core/steel_marks), whether or not they are written on them yet (Numerar peças)."""
    from ..core import steel_marks
    from ..i18n import t
    try:
        marks, pieces = doc.ifc.steel_marks()
    except Exception:                                  # (the IFC still being read)
        return []
    words = {"P": "steel_piece.column", "V": "steel_piece.beam", "CV": "steel_piece.brace", "M": "steel_piece.purlin",
             "E": "steel_piece.member", "Ch": "steel_piece.plate"}
    from ..core import steel
    rows_ = {}
    for p in pieces:
        mark = marks.get(p["guid"], "")
        obj = doc.get(p["guid"])
        if p["kg_m"] and obj is not None and obj.mesh is not None and obj.mesh.is_closed():
            volume = abs(obj.mesh.volume())               # (its real body: the mitres' and copes' offcuts left out)
            area = p["kg_m"] / steel.DENSITY             # (m²)
            if volume > 0 and area > 0:
                ratio = (volume / area) / max(p["length"], 1e-9)
                p = dict(p, length=volume / area, weight=volume * steel.DENSITY, paint=p["paint"] * ratio)
        r = rows_.get(mark)
        if r is None:
            r = rows_[mark] = {"guid": p["guid"], "guids": [], "kind": "steel", "mark": mark, "name": mark,
                               "type": p["section"], "storey": "", "piece": t(words.get(p["prefix"], words["E"])),
                               "section": p["section"], "grade": p["grade"], "pieces": 0,
                               "cut_length": p["length"] or None, "metres": 0.0, "kg_m": p["kg_m"], "weight": 0.0,
                               "paint": 0.0}
        r["guids"].append(p["guid"])
        r["pieces"] += 1
        r["metres"] += p["length"]
        r["weight"] += p["weight"]
        r["paint"] += p["paint"]
    for r in rows_.values():
        if not r["metres"]:
            r["metres"] = None
    return sorted(rows_.values(), key=lambda r: steel_marks.sort_key(r["mark"]))


def bolt_rows(doc):
    """(0.500) The bolts and anchor bolts of the connections: a line a kind and size — dicts with "guid" (the first's),
    "kind" "bolt", "bolt" («M20 × 80»), "bolt_kind", "count"."""
    import ifcopenshell.util.element
    from ..i18n import t
    try:
        fasteners = [e for e in doc.ifc.file.by_type("IfcMechanicalFastener") if doc.ifc.kind_of(e.GlobalId) ==
                     "steel_part"]
    except Exception:
        return []
    s = doc.ifc.unit_scale
    groups = {}
    for e in fasteners:
        predefined = ifcopenshell.util.element.get_predefined_type(e) or ""
        psets = ifcopenshell.util.element.get_psets(e)
        if predefined == "ANCHORBOLT":
            p = psets.get("Pset_MechanicalFastenerAnchorBolt", {})
            d, length = p.get("AnchorBoltDiameter"), p.get("AnchorBoltLength")
        else:
            p = psets.get("Pset_MechanicalFastenerBolt", {})
            d, length = p.get("ThreadDiameter"), p.get("ThreadLength")
        d_mm = round(float(d or 0.0) * s * 1000.0)
        l_mm = int(5 * round(float(length or 0.0) * s * 1000.0 / 5.0))          # (to 5 mm)
        key = (predefined, d_mm, l_mm)
        g = groups.get(key)
        if g is None:
            words = t("steel_piece.anchor" if predefined == "ANCHORBOLT" else "steel_piece.bolt")
            g = groups[key] = {"guid": e.GlobalId, "guids": [], "kind": "bolt", "bolt": "M{} × {}".format(d_mm, l_mm),
                               "bolt_kind": words, "name": "M{} × {}".format(d_mm, l_mm), "type": words, "storey": "",
                               "count": 0}
        g["guids"].append(e.GlobalId)
        g["count"] += 1
    return sorted(groups.values(), key=lambda g: (g["bolt_kind"], _natural(g["bolt"])))


def cutting_rows(doc):
    """(0.501) The bars to buy (model/steel_fabrication.cutting): dicts with "guid" (None), "kind" "cutting",
    "section", "grade", "bars", "bought", "used" (m), "waste" (%)."""
    from . import steel_fabrication
    try:
        found = steel_fabrication.cutting(doc)
    except Exception:                                  # (the IFC still being read)
        return []
    return [{"guid": None, "kind": "cutting", "name": r["section"], "type": r["section"], "storey": "",
             **{k: r[k] for k in ("section", "grade", "bars", "bought", "used", "waste")}} for r in found]


PHASES = {"P": 1, "V": 2, "CV": 3, "M": 4, "E": 5}     # (0.514) the erection's order: columns, beams, bracing, purlins


def _solid(mesh):
    """(volume m³, centre of gravity (3,)) of a closed mesh — its tetrahedra from the origin, signed."""
    import numpy as np
    v = np.asarray(mesh.verts, dtype=float)
    t = np.asarray(mesh.tris, dtype=int)
    if not len(t):
        return 0.0, v.mean(axis=0) if len(v) else np.zeros(3)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    vols = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
    total = float(vols.sum())
    if abs(total) < 1e-12:
        return 0.0, v.mean(axis=0)
    centre = ((a + b + c) / 4.0 * vols[:, None]).sum(axis=0) / total
    return abs(total), centre


def erection_rows(doc):
    """(0.514) The steel's erection — the plan's step 10: a line an assembly (each steel piece with the plates welded to
    it: a column's base plate and gussets, a beam's end plates, a rafter's cleats…) — dicts with "guid" (the piece's),
    "kind" "erection", "order" (1, 2…), "phase" («1 — Pilares»…), "mark", "piece" (its name), "parts" (its plates'
    marks), "weight" (kg, to lift), "cog" («x; y; z» m) — in the order they go up: by phase, then from the first
    corner on (x, then y)."""
    import json
    import numpy as np
    from ..core import steel
    from ..i18n import decimal_sep, t
    try:
        marks, pieces = doc.ifc.steel_marks()
    except Exception:                                  # (the IFC still being read)
        return []
    welded = {}
    for p in pieces:
        if p["prefix"] != "Ch":
            continue
        record = json.loads(doc.ifc._params(doc.ifc.by_guid(p["guid"])).get("Chapa") or "{}")
        if record.get("peca"):
            welded.setdefault(record["peca"], []).append(p)
    out = []
    for p in pieces:
        if p["prefix"] == "Ch":
            continue
        obj = doc.get(p["guid"])
        if obj is None or obj.mesh is None or not len(obj.mesh.verts):
            continue
        volume, centre = _solid(obj.mesh)
        weight = volume * steel.DENSITY if obj.mesh.is_closed() and volume > 0 else p["weight"]
        moment = centre * weight
        names = []
        for q in welded.get(p["guid"], []):
            plate = doc.get(q["guid"])
            if plate is None or plate.mesh is None or not len(plate.mesh.verts):
                continue
            _v, c = _solid(plate.mesh)
            weight += q["weight"]
            moment = moment + c * q["weight"]
            names.append(marks.get(q["guid"], ""))
        cog = moment / weight if weight > 0 else centre
        phase = PHASES.get(p["prefix"], 5)
        sep = decimal_sep()
        out.append({"guid": p["guid"], "guids": [p["guid"]] + [q["guid"] for q in welded.get(p["guid"], [])],
                    "kind": "erection", "phase_n": phase, "phase": t("erection.phase{}".format(phase)),
                    "mark": marks.get(p["guid"], ""), "piece": obj.name, "name": obj.name, "type": p["section"],
                    "storey": "", "parts": ", ".join(sorted(n for n in set(names) if n)) or "—",
                    "parts_n": len(names), "weight": weight, "x": float(cog[0]), "y": float(cog[1]),
                    "cog": "; ".join("{:.2f}".format(float(c)).replace(".", sep) for c in cog)})
    out.sort(key=lambda r: (r["phase_n"], round(r["x"], 1), round(r["y"], 1)))
    for k, r in enumerate(out, 1):
        r["order"] = k
    return out


def steel_check_rows(doc):
    """(0.516) The steel pieces checked by Eurocode 3 (model/steel_analysis): dicts with "guid", "kind" "steel_check",
    "mark", "piece", "section", "grade", "n_ed" (kN, compression −), "m_ed" (kN·m), "v_ed" (kN), "deflection" and
    "utilisation" (% of L/200, of the resistance), "governing" (the check), "status" — the most used first."""
    from ..i18n import t
    from . import steel_analysis
    try:
        found = steel_analysis.analyse(doc)
    except Exception:                                  # (the IFC still being read)
        return []
    if found.error:
        return [{"guid": None, "kind": "steel_check", "mark": "", "piece": t("ec3.unstable"), "name": "", "type": "",
                 "storey": "", "section": "", "grade": "", "n_ed": None, "m_ed": None, "v_ed": None,
                 "deflection": None, "utilisation": None, "governing": found.error, "status": "—"}]
    out = []
    for r in found.rows:
        obj = doc.get(r["guid"])
        name = obj.name if obj is not None else ""
        out.append({"guid": r["guid"], "kind": "steel_check", "mark": r["mark"], "piece": name, "name": name,
                    "type": r["section"], "storey": "", "section": r["section"], "grade": r["grade"],
                    "n_ed": r["n_ed"], "m_ed": r["m_ed"], "v_ed": r["v_ed"], "deflection": r["deflection"] * 100.0,
                    "utilisation": r["utilisation"] * 100.0, "governing": t("ec3.check." + r["governing"]),
                    "status": t("ec3.ok") if r["ok"] else t("ec3.fails")})
    out.sort(key=lambda r: -r["utilisation"])
    if out:                                            # (what this pre-design leaves out, said under it)
        out.append({"guid": None, "kind": "steel_check", "mark": "", "piece": t("ec3.notes"), "name": "", "type": "",
                    "storey": "", "section": "", "grade": "", "n_ed": None, "m_ed": None, "v_ed": None,
                    "deflection": None, "utilisation": None,
                    "governing": t("ec3.notes_text", g=_num(found.loads.get("dead")), q=_num(found.loads.get("imposed")),
                                   w=_num(found.loads.get("wind"))),
                    "status": ""})
    return out


def _connections_count(doc):
    try:
        return sum(1 for a in doc.ifc.file.by_type("IfcElementAssembly")
                   if doc.ifc.kind_of(a.GlobalId) == "steel_connection")
    except Exception:                                  # (the IFC still being read)
        return 0


def steel_joint_rows(doc):
    """(0.520) The steel connections checked by EN 1993-1-8 (model/steel_connection_check): dicts with "guid" (the
    connection's), "kind" "steel_joint", "connection", "connection_kind", "bolts", "bolt_shear" and "bolt_tension" (kN a
    bolt), "weld_use" and "utilisation" (%), "governing", "status" — the most used first, a line of notes under."""
    from ..i18n import t
    from . import steel_analysis, steel_connection_check
    try:
        found = steel_analysis.analyse(doc)
        checked = steel_connection_check.check(doc, found) if not found.error else []
    except Exception:                                  # (the IFC still being read)
        return []
    out = []
    for r in checked:
        out.append({"guid": r["guid"], "kind": "steel_joint", "connection": r["name"], "name": r["name"],
                    "type": t("connection." + r["kind"]), "storey": "", "connection_kind": t("connection." + r["kind"]),
                    "bolts": r["bolts"], "bolt_shear": r["shear"], "bolt_tension": r["tension"] or None,
                    "weld_use": r["weld"] * 100.0, "utilisation": r["utilisation"] * 100.0,
                    "governing": t("ec3j.check." + r["governing"]),
                    "status": t("ec3.ok") if r["ok"] else t("ec3.fails")})
    if out:
        out.append({"guid": None, "kind": "steel_joint", "connection": t("ec3.notes"), "name": "", "type": "",
                    "storey": "", "connection_kind": "", "bolts": "", "bolt_shear": None, "bolt_tension": None,
                    "weld_use": None, "utilisation": None, "governing": t("ec3j.notes_text"), "status": ""})
    return out


def _num(v):
    from ..i18n import decimal_sep
    return "{:.2f}".format(float(v or 0.0)).replace(".", decimal_sep())


def tiles_rows(doc):
    """(0.279) The roofs' tiles: dicts with "guid" (the roof's), "kind" "tiles", "roof", "tile", "tiles", "cut",
    "caps", "weight" (kg), "area" (m², along the slope) — a roof each."""
    from ..i18n import lang
    try:
        roofs = [r for r in doc.ifc.file.by_type("IfcRoof") if doc.ifc.tiles_of(r.GlobalId) is not None]
    except Exception:                                  # (the IFC still being read)
        return []
    out = []
    for roof in roofs:
        found = doc.ifc.tiles_summary(roof.GlobalId)
        spec = doc.ifc.tile_spec(found["tile"])        # (0.281: the project's own too)
        tile = (spec.name_pt if lang() == "pt" else spec.name_en) if spec else found["tile"] or ""
        out.append({"guid": roof.GlobalId, "kind": "tiles", "roof": roof.Name or "", "name": roof.Name or "",
                    "type": tile, "storey": "", "tile": tile, "tiles": found["tiles"], "cut": found["cut"],
                    "caps": found["caps"], "weight": found["weight"], "area": found["area"]})
    return out


def _perforated_finishes(doc):
    """The perforated wall finishes — (0.551) and the ceilings and parametric surfaces a Visual Graph operator
    perforated."""
    try:
        out = [e for e in doc.ifc.file.by_type("IfcCovering")
               if doc.ifc._params(e).get("Acabamento") == "perfurado"
               or (doc.ifc._params(e).get("Elemento") == "ceiling" and doc.ifc._params(e).get("FurosLivres"))]
        from ..ifc.param_surfaces import USAGES
        for cls in sorted({c for c, _p in USAGES.values()}):
            out += [e for e in doc.ifc.file.by_type(cls) if doc.ifc._params(e).get("Elemento") == "param_surface"
                    and doc.ifc._params(e).get("FurosLivres")]
        return out
    except Exception:                                  # (the IFC still being read)
        return []


def perforated_rows(doc):
    """(0.544) The perforated panels: dicts with "guid", "kind" "perforated", "name", "host" (its wall), "panels",
    "holes", "open_area" (%), "area" (m², its face)."""
    out = []
    for e in _perforated_finishes(doc):
        kind = doc.ifc._params(e).get("Elemento")
        if kind in ("ceiling", "param_surface"):       # (0.551) a ceiling, a surface: itself the host
            try:
                if kind == "ceiling":
                    got, face = doc.ifc.ceiling_perforation(e.GlobalId), doc.ifc.ceiling_face(e.GlobalId)
                else:
                    got, face = doc.ifc.surface_perforation(e.GlobalId), doc.ifc.surface_sheet_face(e.GlobalId)
            except Exception:                          # (not worked out: left out)
                continue
            if got is None:
                continue
            out.append({"guid": e.GlobalId, "kind": "perforated", "name": e.Name or "", "type": "", "storey": "",
                        "host": "teto" if kind == "ceiling" else "superfície paramétrica", "panels": 1,
                        "holes": got["count"], "open_area": 100.0 * got["open_area"], "area": float(face.area)})
            continue
        try:
            d = doc.ifc.pattern_params(e.GlobalId)
        except Exception:                              # (its wall gone: left out)
            continue
        wall = doc.get(doc.ifc._params(e).get("Parede") or "")
        out.append({"guid": e.GlobalId, "kind": "perforated", "name": e.Name or "", "type": "", "storey": "",
                    "host": wall.name if wall is not None else "", "panels": len(d.get("panels") or []),
                    "holes": d.get("count", 0), "open_area": 100.0 * d.get("open_area", 0.0),
                    "area": float(d["face"].area) if d.get("face") is not None else None})
    out.sort(key=lambda r: (_natural(r["host"]), _natural(r["name"])))
    return out


def circuit_rows(doc):
    """The circuits (0.144, the load schedule): dicts with "guid", "kind" "circuit", "name", "circuit_type",
    "board", "points", "power" (W), "current" (A), "breaker" (A), "section" (mm²), "check" — in name order."""
    from ..i18n import t
    try:
        circuits = doc.ifc.circuits()
        reports = [(g, doc.ifc.circuit_report(g)) for g, _n in circuits]
    except Exception:                                  # (the IFC still being read)
        return []
    out = []
    for g, r in reports:
        board = doc.get(r["board"]) if r["board"] else None
        check = t("circuit.ok") if r["ok"] else "; ".join(t("circuit.why." + w) for w in r["why"])
        out.append({"guid": g, "kind": "circuit", "name": r["name"], "circuit_type": t("circuit." + r["kind"]),
                    "type": t("circuit." + r["kind"]), "board": board.name if board is not None else "",
                    "storey": "", "points": r["points"], "power": r["power"], "current": r["current"],
                    "breaker": r["breaker"], "section": r["section"], "conduit": r.get("conduit") or None,
                    "check": check})
    return out


def room_rows(doc):
    """The rooms (0.125): dicts with "guid", "number", "name", "storey", "area", "perimeter", "height" and
    their finishes ("floor", "walls", "ceiling"), "kind" "space" — by storey (lowest first) and number."""
    storeys = {g: (name, z) for g, name, z in doc.storeys()}
    out = []
    for info in _spaces(doc):
        name, _z = storeys.get(info["storey"], ("", 0.0))
        finishes = info.get("finishes") or {}
        out.append({"guid": info["guid"], "kind": "space", "number": info["number"], "name": info["name"],
                    "storey": name, "area": info["area"], "perimeter": info["perimeter"], "height": info["height"],
                    "floor": finishes.get("FloorCovering", ""), "walls": finishes.get("WallCovering", ""),
                    "ceiling": finishes.get("CeilingCovering", ""), "type": name})
    levels = {name: z for name, z in storeys.values()}
    out.sort(key=lambda r: (levels.get(r["storey"], 0.0), _natural(r["number"]), _natural(r["name"])))
    return out


def rows(doc, category):
    """The category's elements: dicts with "guid", the columns and "kind", ordered by storey
    (lowest first), type and name."""
    if category in ROOMS:
        return room_rows(doc)
    if category == "circuits":
        return circuit_rows(doc)
    if category == "electrical":
        return electrical_rows(doc)
    if category == "keynotes":
        return keynote_rows(doc)
    if category == "carpentry":                        # (0.277)
        return carpentry_rows(doc)
    if category == "tiles":                            # (0.279)
        return tiles_rows(doc)
    if category == "perforated":                       # (0.544)
        return perforated_rows(doc)
    if category == "steel":                            # (0.500)
        return steel_rows(doc)
    if category == "bolts":
        return bolt_rows(doc)
    if category == "cutting":                          # (0.501)
        return cutting_rows(doc)
    if category == "erection":                         # (0.514)
        return erection_rows(doc)
    if category == "steel_check":                      # (0.516)
        return steel_check_rows(doc)
    if category == "steel_joints":                     # (0.520)
        return steel_joint_rows(doc)
    objs =[o for o in doc.objects.values() if o.is_bim and category_of(o.ifc_class) == category]
    info = doc.ifc.schedule_info([o.id for o in objs])
    levels = {name: z for _g, name, z in doc.storeys()}
    out = []
    for o in objs:
        r = dict(info.get(o.id) or {"name": o.name, "type": "", "storey": "", "kind": None, "length": None,
                                    "height": None, "thickness": None, "width": None, "host": ""})
        r["guid"], r["class"] = o.id, o.ifc_class
        closed = o.mesh.is_closed()
        r["volume"] = abs(o.mesh.volume()) if closed else r.get("volume")      # (a roof: its own, 0.265)
        t = r.get("thickness")
        r["area"] = r["volume"] / t if (closed and t) else r.get("area")      # (a roof: its own, sloped)
        out.append(r)
    out.sort(key=lambda r: (levels.get(r["storey"], 0.0), r["type"], _natural(r["name"])))
    return out


def editable(category, column, row):
    """The Properties panel action for editing this cell, or None (read-only)."""
    if category in ROOMS:
        return ROOM_EDITABLE.get(column)
    if category == "circuits":
        return CIRCUIT_EDITABLE.get(column)
    action, kinds = COLUMN_HEIGHT if (category == "columns" and column == "height") else \
        EDITABLE.get(column, (None, None))
    if action is None or (kinds is not None and row.get("kind") not in kinds):
        return None
    return action


def by_type(rows_, category):
    """One line per type: "type", "count" and the summed columns of the category (the rooms: per storey)."""
    columns = [c for c in CATEGORIES[category][1] if c in SUMMED]
    groups = {}
    for r in rows_:
        g = groups.setdefault(r["type"] or "—", {"type": r["type"] or "—", "count": 0, **{c: None for c in columns}})
        g["count"] += 1
        for c in columns:
            if r.get(c) is not None:
                g[c] = (g[c] or 0.0) + r[c]
    return sorted(groups.values(), key=lambda g: _natural(g["type"]))


def totals(rows_, category):
    """"count" and the sums of the summed columns."""
    out = {"count": len(rows_)}
    for c in CATEGORIES[category][1]:
        if c in SUMMED:
            values = [r[c] for r in rows_ if r.get(c) is not None]
            out[c] = sum(values) if values else None
    return out


# ---------------------------------------------------------------- the project's own schedules (0.131)

OPERATORS = ("=", "≠", ">", "<", "≥", "≤", "contém")
FUNCTIONS = {"round": round, "min": min, "max": max, "abs": abs}


@dataclass
class ScheduleDef:
    """A schedule of the project's own: a category's elements (or rooms), the columns chosen (in order), its
    formula columns ((label, expression) — "length * height", "area * 1.10"), its filters ((column, operator,
    value)), the column it is sorted by and the one it is grouped by ("" none). Kept beside the IFC."""
    name: str
    category: str
    fields: list
    formulas: list = field(default_factory=list)
    filters: list = field(default_factory=list)
    sort: str = ""
    descending: bool = False
    group: str = ""
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)
    grid: dict = field(default_factory=dict)        # (0.478) its cells as a spreadsheet's (model/table_sheet.Layout)


def formula_key(k):
    """The column key of a schedule's k-th formula."""
    return "formula:{}".format(k)


def evaluate(expression, row):
    """A formula's value for a row (a float), or None: numbers (a decimal comma too: "1,10"), the row's number
    columns by their key (length, height, area…), + - * / ** and brackets, round / min / max / abs (their
    arguments separated by ";", as in a Portuguese spreadsheet) — nothing else is run."""
    text = re.sub(r"(\d),(\d)", r"\1.\2", str(expression)).replace(";", ",")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError:
        return None

    def value(node):
        if isinstance(node, ast.Expression):
            return value(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name):
            v = row.get(node.id)
            if not isinstance(v, (int, float)):
                raise ValueError(node.id)
            return float(v)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            v = value(node.operand)
            return v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            a, b = value(node.left), value(node.right)
            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            if isinstance(node.op, ast.Mult):
                return a * b
            if isinstance(node.op, ast.Div):
                return a / b
            if abs(b) > 10:
                raise ValueError("power")
            return a ** b
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS \
                and not node.keywords and node.args:
            args = [value(a) for a in node.args]
            if node.func.id == "round" and len(args) == 2:       # (its decimals: a whole number)
                args[1] = int(args[1])
            return float(FUNCTIONS[node.func.id](*args))
        raise ValueError("not allowed")

    try:
        return value(tree)
    except (ValueError, ZeroDivisionError, OverflowError, TypeError):
        return None


def _matches(row, flt):
    key, op, wanted = flt
    v = row.get(key)
    if op == "contém":
        return str(wanted).lower() in str(v or "").lower()
    if isinstance(v, (int, float)):
        try:
            w = float(str(wanted).replace(",", "."))
        except ValueError:
            return False
        return {"=": abs(v - w) < 1e-9, "≠": abs(v - w) >= 1e-9, ">": v > w, "<": v < w, "≥": v >= w - 1e-9,
                "≤": v <= w + 1e-9}.get(op, True)
    text, w = str(v or "").lower(), str(wanted).lower()
    return {"=": text == w, "≠": text != w}.get(op, True)


def apply(defn, rows_):
    """A schedule of the project's own on the category's rows: (its columns' keys — the fields, then the
    formulas' —, the rows with the formulas' values, filtered and sorted)."""
    out = []
    for r in rows_:
        line = dict(r)
        for k, (_label, expression) in enumerate(defn.formulas):
            line[formula_key(k)] = evaluate(expression, r)
        if all(_matches(line, f) for f in defn.filters):
            out.append(line)
    if defn.sort:
        def key(line):
            v = line.get(defn.sort)
            return (0, float(v)) if isinstance(v, (int, float)) else (1, _natural(str(v or "")))
        out.sort(key=key, reverse=bool(defn.descending))
    columns = list(defn.fields) + [formula_key(k) for k in range(len(defn.formulas))]
    return columns, out


def grouped(defn, lines):
    """One line per value of the schedule's group column: that value, "count", and the sums of its number
    columns (the fields that are summed and its formulas)."""
    summed = [c for c in defn.fields if c in SUMMED] + [formula_key(k) for k in range(len(defn.formulas))]
    groups = {}
    for line in lines:
        value = line.get(defn.group)
        g = groups.setdefault(str(value if value is not None else "—"),
                              {defn.group: value if value is not None else "—", "count": 0,
                               **{c: None for c in summed}})
        g["count"] += 1
        for c in summed:
            if isinstance(line.get(c), (int, float)):
                g[c] = (g[c] or 0.0) + line[c]
    return [groups[k] for k in sorted(groups, key=_natural)], [defn.group, "count"] + summed


def available(category):
    """The columns a schedule of this category can show (its category's)."""
    return list(CATEGORIES.get(category, CATEGORIES["other"])[1])


def def_to_dict(defn):
    from . import table_sheet
    out = {"name": defn.name, "category": defn.category, "fields": list(defn.fields),
           "formulas": [list(f) for f in defn.formulas], "filters": [list(f) for f in defn.filters],
           "sort": defn.sort, "descending": bool(defn.descending), "group": defn.group, "uid": defn.uid}
    grid = table_sheet.layout_to_dict(table_sheet.layout_from_dict(getattr(defn, "grid", None) or {}))
    if grid:
        out["grid"] = grid                              # (0.478; none: as before, the file read by older versions)
    return out


def def_from_dict(data):
    try:
        category = str(data["category"])
        if category not in CATEGORIES:
            return None
        known = set(available(category))
        defn = ScheduleDef(str(data["name"]), category, [f for f in data.get("fields", ()) if f in known],
                           [(str(a), str(b)) for a, b in data.get("formulas", ())],
                           [(str(a), str(b), str(c)) for a, b, c in data.get("filters", ()) if b in OPERATORS],
                           str(data.get("sort") or ""), bool(data.get("descending")), str(data.get("group") or ""))
        if data.get("uid"):
            defn.uid = str(data["uid"])
        if data.get("grid"):
            from . import table_sheet
            defn.grid = table_sheet.layout_to_dict(table_sheet.layout_from_dict(data["grid"]))
        return defn
    except (KeyError, TypeError, ValueError):
        return None


def layout_of(defn):
    """(0.478) A table of the project's own as a spreadsheet (model/table_sheet.Layout)."""
    from . import table_sheet
    return table_sheet.layout_from_dict(getattr(defn, "grid", None) or {})


def with_layout(defn, layout):
    """(0.478) A copy of a table of the project's own with these cells."""
    from . import table_sheet
    data = def_to_dict(defn)
    data["grid"] = table_sheet.layout_to_dict(layout)
    out = def_from_dict(data)
    out.grid = table_sheet.layout_to_dict(layout)
    return out


def project_tokens(doc):
    """(0.478) The project's data a table's text may hold: {projeto} (its IfcProject's name, else its file's) and
    {data} (today)."""
    import datetime
    name = ""
    try:
        projects = doc.ifc.file.by_type("IfcProject")
        name = (projects[0].Name or "") if projects else ""
    except (AttributeError, RuntimeError):
        name = ""
    path = getattr(doc, "path", None)
    name = name or (os.path.splitext(os.path.basename(path))[0] if path else "")
    return {"projeto": name, "data": datetime.date.today().strftime("%d/%m/%Y")}


def grid_of(doc, defn, label_of, decimal=",", total_label=None, tokens=None):
    """(0.478) A table of the project's own as its grid is shown (model/table_sheet.build): (grid, geometry, its
    columns' keys, its elements' lines, its layout). label_of(column key) -> its heading; total_label(n) -> the totals'
    row's first cell («Total: 3»), when that column is not summed; tokens: the project's data its texts may hold
    ({"projeto": …, "data": …}; {tabela} and {n} put in here)."""
    from . import table_sheet
    columns, lines = apply(defn, rows(doc, defn.category))
    if defn.group:
        lines, columns = grouped(defn, lines)
    columns = list(columns)

    def heading(c):
        if c.startswith("formula:"):
            k = int(c.split(":")[1])
            return defn.formulas[k][0] if k < len(defn.formulas) else c
        return label_of(c)
    data = [[line.get(c) for c in columns] for line in lines]
    texts = [[text_of(c, line.get(c), decimal) for c in columns] for line in lines]
    totals, totals_texts = [], []
    for k, c in enumerate(columns):
        values = [line[c] for line in lines if isinstance(line.get(c), (int, float)) and not isinstance(line[c], bool)]
        if (c in SUMMED or c.startswith("formula:") or c == "count") and values:
            totals.append(sum(values))
            totals_texts.append(text_of(c, sum(values), decimal))
        elif k == 0 and total_label is not None:
            totals.append(total_label(len(lines)))
            totals_texts.append(total_label(len(lines)))
        else:
            totals.append(None)
            totals_texts.append("")
    layout = layout_of(defn)
    count = sum(line.get("count") or 0 for line in lines) if defn.group else len(lines)
    tokens = dict(tokens or {}, tabela=defn.name, n=count)
    grid, geom = table_sheet.build(layout, columns, [heading(c) for c in columns], data, totals, texts, totals_texts,
                                   decimal, tokens)
    return grid, geom, columns, lines, layout


class SetScheduleDefs:
    """The project's own schedules changed (one made, changed or deleted): one undo step."""

    def __init__(self, before, after, label):
        self.before = [def_from_dict(def_to_dict(d)) for d in before]
        self.after = [def_from_dict(def_to_dict(d)) for d in after]
        self.label = label

    def do(self, doc):
        doc.schedule_defs = [def_from_dict(def_to_dict(d)) for d in self.after]
        doc.schedules_changed()

    def undo(self, doc):
        doc.schedule_defs = [def_from_dict(def_to_dict(d)) for d in self.before]
        doc.schedules_changed()


def text_of(column, value, decimal=","):
    """A cell as written in a schedule (on a sheet too, 0.132): a length "4,50 m", an area "12,34 m²", a volume
    "1,234 m³", a formula's value "22,40", a count "3"; text as it is."""
    from ..core.units import format_length
    if value is None:
        return ""
    if column.startswith("formula:"):
        return "{:.2f}".format(value).replace(".", decimal)
    if column in COUNTS:
        return str(value)
    if column in UNITS and isinstance(value, (int, float)):                 # (a circuit's: W, A, mm², 0.144)
        return UNITS[column].format(value).replace(".", decimal)
    if column in NUMBERS and isinstance(value, (int, float)):
        if column in ("area", "projected"):
            return "{:.2f} m²".format(value).replace(".", decimal)
        if column == "volume":
            return "{:.3f} m³".format(value).replace(".", decimal)
        return format_length(value, decimal, unit="m").replace("~ ", "")    # (a document's: m, as its areas)
    return str(value)


def table_of(doc, ref, label_of, decimal=","):
    """A schedule as a table to print (0.132): ref a category key or "def:<uid>" (the project's own); label_of(
    column key) -> its heading. Returns (title, headings, rows of texts, totals text) or None (no such schedule)."""
    defn = None
    if str(ref).startswith("def:"):
        defn = next((d for d in getattr(doc, "schedule_defs", ()) if "def:" + d.uid == ref), None)
        if defn is None:
            return None
        columns, lines = apply(defn, rows(doc, defn.category))
        if defn.group:
            lines, columns = grouped(defn, lines)
        title = defn.name
    elif ref in CATEGORIES:
        lines = rows(doc, ref)
        columns = list(CATEGORIES[ref][1])
        title = None
    else:
        return None

    def heading(column):
        if column.startswith("formula:") and defn is not None:
            k = int(column.split(":")[1])
            return defn.formulas[k][0] if k < len(defn.formulas) else column
        return label_of(column)
    texts = [[text_of(c, line.get(c), decimal) for c in columns] for line in lines]
    sums = []
    for c in columns:
        values = [line[c] for line in lines if isinstance(line.get(c), (int, float))]
        if (c in SUMMED or c.startswith("formula:")) and values:
            sums.append("{}: {}".format(heading(c), text_of(c, sum(values), decimal)))
    return title, [heading(c) for c in columns], texts, "   ".join(sums)


def write_csv(path, header, table, decimal=","):
    """A table (list of lists of str / numbers) to a CSV file Excel opens as it is: ';' between
    columns, `decimal` in numbers, UTF-8 with BOM (so accents survive)."""
    def cell(v):
        if v is None:
            return ""
        if isinstance(v, float):
            return "{:.3f}".format(v).replace(".", decimal)
        return str(v)

    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(header)
        for line in table:
            w.writerow([cell(v) for v in line])


XLSX_DECIMALS = 3          # (0.370) a number's decimals at most in the workbook (as in the CSV)
XLSX_WIDTH = (6, 60)       # characters: a column's narrowest and widest
XLSX_HEAD = "E8ECF2"       # the heading row's fill (the sheets' light grey-blue)


def xlsx_value(value, decimal=","):
    """(0.370) A cell as the workbook keeps it: (value, decimals or None) — a number as a number (Excel adds and
    sorts it), also one already written as text with `decimal` ("4,00", "1 234,5", "12"), its decimals as shown;
    anything else as text ("—", "Ø12", a name), nothing as an empty cell."""
    if value is None:
        return None, None
    if isinstance(value, bool):
        return str(value), None
    if isinstance(value, int):
        return value, 0
    if isinstance(value, float):
        if not math.isfinite(value):
            return "", None
        shown = "{:.{}f}".format(value, XLSX_DECIMALS).rstrip("0").split(".")
        return round(value, XLSX_DECIMALS), len(shown[1]) if len(shown) > 1 else 0
    text = str(value).strip()
    plain = text.replace(" ", "").replace(" ", "")
    if re.fullmatch(r"-?\d+(" + re.escape(decimal) + r"\d+)?", plain) and not re.match(r"-?0\d", plain):
        whole, _, part = plain.partition(decimal)            # (not "01", "007": a code, kept as written)
        return (float(plain.replace(decimal, ".")) if part else int(whole)), len(part)
    return text, None


def write_xlsx(path, header, table, decimal=",", title=None, author="ArqSynth BIM"):
    """(0.370) A table to an Excel workbook (XLSX, openpyxl): one sheet named after it (`title`), the headings in bold
    on a light fill with a filter, kept on top when it scrolls; numbers as numbers (xlsx_value), each column with the
    decimals its values were shown with (a measure given as a number: at least 2), whole counts without; the columns
    as wide as what they hold. A row with one cell (a total, a summary) and an empty one as they are. ImportError:
    openpyxl missing."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    book = Workbook()
    sheet = book.active
    sheet.title = (re.sub(r"[\[\]:*?/\\]+", "-", str(title or "")).strip() or "Tabela")[:31]
    book.properties.creator = author
    book.properties.title = str(title or "")
    sheet.append([str(h) for h in header])
    cells = [[xlsx_value(v, decimal) for v in line] for line in table]
    width = len(header)
    rows = [line for line in cells if len(line) > 1]                 # (the table's; a total's line has one cell)
    decimals = []           # (a column's: those it was shown with; a measure given as a number, 2 at least: 5,00 not 5)
    for k in range(width):
        floats = [(line[k][1] or 0) if isinstance(given[k], str) else max(2, line[k][1] or 0)
                  for line, given in zip(cells, table) if len(line) > 1 and k < len(line)
                  and isinstance(line[k][0], float)]
        decimals.append(max(floats) if floats else 0)
    for r, line in enumerate(cells, start=2):
        sheet.append([v for v, _d in line])
        for k, (v, d) in enumerate(line):
            if isinstance(v, (int, float)):
                places = decimals[k] if len(line) > 1 and k < width and isinstance(v, float) else (d or 0)
                sheet.cell(row=r, column=k + 1).number_format = "0." + "0" * places if places else "0"
    bold, fill = Font(bold=True), PatternFill("solid", fgColor=XLSX_HEAD)
    for cell in sheet[1]:
        cell.font, cell.fill = bold, fill
        cell.alignment = Alignment(vertical="center")
    sheet.freeze_panes = "A2"
    leading = next((i for i, line in enumerate(cells) if len(line) <= 1), len(cells))   # (the rows before a total)
    if width and leading:
        sheet.auto_filter.ref = "A1:{}{}".format(get_column_letter(width), 1 + leading)
    for k in range(width):
        texts = [str(header[k])] + [str(line[k][0]) for line in rows if k < len(line) and line[k][0] is not None]
        letter = get_column_letter(k + 1)
        sheet.column_dimensions[letter].width = min(max(XLSX_WIDTH[0], max(map(len, texts)) + 2), XLSX_WIDTH[1])
    book.save(path)


TABLE_FORMATS = (".xlsx", ".csv", ".json")


def unit_of(column):
    """(0.477) A column's unit as other programs take it: "m", "m2", "m3", "un", "kg", "W", "A", "mm2" or ""."""
    if column in ("area", "projected"):
        return "m2"
    if column == "volume":
        return "m3"
    if column in COUNTS or column == "count":
        return "un"
    if column in ("length", "height", "thickness", "width", "perimeter", "metres", "conduit", *EDGES):
        return "m"
    return {"weight": "kg", "power": "W", "current": "A", "breaker": "A", "section": "mm2"}.get(column, "")


JSON_FORMAT = "arqsynth-tabela"      # (0.477) what the JSON says it is (KazaFix Cost and the suite read it by this)
JSON_VERSION = 1


def write_json(path, header, table, title=None, columns=None, project=None, decimal=","):
    """(0.477, the owner: «exportar essas quantidades para os outros aplicativos, especialmente o app de geração de preço
    que estou desenvolvendo KazaFix Cost») A table as JSON for another program to read:

        {"formato": "arqsynth-tabela", "versao": 1, "titulo": "Paredes", "projeto": "Moradia",
         "colunas": [{"chave": "length", "nome": "Comprimento", "unidade": "m"}, …],
         "linhas": [{"length": 4.5, "name": "Parede 1", …}, …],
         "totais": {"length": 19.2, …}}

    numbers as numbers (in metres, m², m³), texts as they are shown; "chave" is the program's own name of the column
    (stable between versions), "nome" the heading as shown. The rows are dicts by "chave"; a column without a key
    (columns None) keyed by its heading."""
    import json
    keys = list(columns) if columns else list(header)
    cols = [{"chave": k, "nome": str(h), "unidade": unit_of(k)} for k, h in zip(keys, header)]
    rows_out, sums = [], {}
    for line in table:
        if len(line) <= 1:                                  # (a total's line, as the CSV's)
            continue
        row = {}
        for k, v in zip(keys, line):
            value, _decimals = xlsx_value(v, decimal)
            row[k] = value
            if isinstance(value, (int, float)) and not isinstance(value, bool) and unit_of(k) not in ("", "A") and \
                    (k in SUMMED or k.startswith("formula:") or k == "count"):
                sums[k] = round(sums.get(k, 0) + value, 6)
        rows_out.append(row)
    data = {"formato": JSON_FORMAT, "versao": JSON_VERSION, "titulo": str(title or ""), "projeto": str(project or ""),
            "colunas": cols, "linhas": rows_out, "totais": sums}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def write_grid_xlsx(path, grid, geom, layout, columns, decimal=",", title=None, author="ArqSynth BIM"):
    """(0.478) A table of the project's to an Excel workbook as its grid is shown (model/table_sheet): its title and
    note rows, its headings (bold, on a light fill, with a filter, kept on top when it scrolls), its elements (numbers
    as numbers, with their decimals), its totals; its cells' bold, italic, alignment, fill and borders, its merged
    cells; its formulas as Excel formulas (SOMA -> SUM, «;» -> «,», «D:D» -> the elements' rows), so that Excel works
    them out again when a value is changed there — one it would not take (#REF!), its value. ImportError: openpyxl
    missing."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from . import table_sheet
    book = Workbook()
    sheet = book.active
    sheet.title = (re.sub(r"[\[\]:*?/\\]+", "-", str(title or "")).strip() or "Tabela")[:31]
    book.properties.creator = author
    book.properties.title = str(title or "")
    sides = {False: Side(style="thin", color="000000"), True: Side(style="medium", color="000000")}
    for g, line in enumerate(grid):
        for c, cell in enumerate(line):
            target = sheet.cell(row=g + 1, column=c + 1)
            formula = table_sheet.to_excel(cell.raw, geom) if cell.raw.startswith("=") and not cell.error else None
            number = isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool)
            if formula is not None:
                target.value = formula
                if number and abs(cell.value - round(cell.value)) > 1e-9:
                    target.number_format = "0.00"
            elif cell.zone in ("D", "S") and number:
                target.value = round(float(cell.value), XLSX_DECIMALS) if isinstance(cell.value, float) else cell.value
                key = columns[c] if c < len(columns) else ""
                places = 3 if key == "volume" else 0 if key in COUNTS or key == "count" else 2
                target.number_format = "0." + "0" * places if places else "0"
            else:
                value, places = xlsx_value(cell.text, decimal)
                target.value = value
                if isinstance(value, float) and places:
                    target.number_format = "0." + "0" * places
            fmt = cell.fmt
            bold, italic = fmt.get("b", cell.zone in ("H", "S")), fmt.get("i", False)
            if bold or italic:
                target.font = Font(bold=bold, italic=italic)
            how = fmt.get("a") or ("center" if cell.zone == "H" else None)
            if how:
                target.alignment = Alignment(horizontal=how, vertical="center")
            fill = fmt.get("f") or ("#" + XLSX_HEAD if cell.zone == "H" else None)
            if fill:
                target.fill = PatternFill("solid", fgColor=fill.lstrip("#").upper())
            if fmt.get("bd"):
                line_ = sides[bool(fmt.get("bw"))]
                target.border = Border(**{name: line_ if s in fmt["bd"] else Side()
                                          for s, name in zip("ltrb", ("left", "top", "right", "bottom"))})
    for g, c, rows, cols in table_sheet.merges_in_grid(layout, geom):
        sheet.merge_cells(start_row=g + 1, start_column=c + 1, end_row=g + rows, end_column=c + cols)
    head = geom.top + 1                                          # (the headings' row, counted from 1)
    sheet.freeze_panes = "A{}".format(head + 1)
    if geom.n and geom.width:
        sheet.auto_filter.ref = "A{}:{}{}".format(head, get_column_letter(geom.width), head + geom.n)
    spanned = {(g + i, c + j) for g, c, rows, cols in table_sheet.merges_in_grid(layout, geom)
               for i in range(rows) for j in range(cols)}
    for c, key in enumerate(columns):
        if key in layout.widths:
            width = layout.widths[key] / 7.0                     # (px: about 7 a character)
        else:
            texts = [grid[g][c].text for g in range(len(grid)) if (g, c) not in spanned]
            width = max([len(x) for x in texts] + [0]) + 2
        sheet.column_dimensions[get_column_letter(c + 1)].width = min(max(XLSX_WIDTH[0], width), XLSX_WIDTH[1])
    book.save(path)


def write_table(path, header, table, decimal=",", title=None, columns=None, project=None, grid=None):
    """(0.370) A table to `path` by its extension: an Excel workbook (.xlsx, write_xlsx), (0.477) JSON for other
    programs (.json, write_json), else a CSV (write_csv). (0.478) grid: a table of the project's cells as shown —
    (grid, geometry, layout, columns' keys): the workbook and the CSV as the grid is (its title and note rows, its
    formats, formulas), the JSON its elements' rows as ever."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xlsx":
        if grid is not None:
            write_grid_xlsx(path, grid[0], grid[1], grid[2], grid[3], decimal, title)
        else:
            write_xlsx(path, header, table, decimal, title)
    elif ext == ".json":
        write_json(path, header, table, title, columns, project, decimal)
    elif grid is not None:
        rows_ = [[cell.text for cell in line] for line in grid[0]]
        write_csv(path, rows_[0] if rows_ else header, rows_[1:], decimal)
    else:
        write_csv(path, header, table, decimal)
