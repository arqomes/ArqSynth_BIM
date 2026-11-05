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
    "columns": (("IfcColumn",), ("name", "type", "storey", "height", "volume")),
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
ORDER = ("walls", "slabs", "roofs", "carpentry", "tiles", "columns", "doors", "windows", "rooms", "finishes",
         "circuits", "electrical", "keynotes", "other")
ROOMS = ("rooms", "finishes")
EDGES = ("eaves", "ridges", "hips", "valleys", "gables", "tops")         # (0.265) a roof's edges, by kind
NUMBERS = {"length", "height", "thickness", "width", "area", "volume", "perimeter", "projected", *EDGES}
SUMMED = {"length", "area", "volume", "power", "conduit", "metres", "projected", "pieces", "tiles", "cut", "caps",
          "weight", *EDGES}
UNITS = {"power": "{:.0f} W", "current": "{:.2f} A", "breaker": "{:.0f} A", "section": "{:g} mm²",   # (0.144)
         "conduit": "{:.2f} m", "metres": "{:.2f} m",                                        # (its conduits, 0.146)
         "weight": "{:.0f} kg"}                                                              # (tiles, 0.279)
COUNTS = ("count", "points", "pieces", "tiles", "cut", "caps")
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
    return {"name": defn.name, "category": defn.category, "fields": list(defn.fields),
            "formulas": [list(f) for f in defn.formulas], "filters": [list(f) for f in defn.filters],
            "sort": defn.sort, "descending": bool(defn.descending), "group": defn.group, "uid": defn.uid}


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
        return defn
    except (KeyError, TypeError, ValueError):
        return None


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


TABLE_FORMATS = (".xlsx", ".csv")


def write_table(path, header, table, decimal=",", title=None):
    """(0.370) A table to `path` by its extension: an Excel workbook (.xlsx, write_xlsx), else a CSV (write_csv)."""
    if os.path.splitext(path)[1].lower() == ".xlsx":
        write_xlsx(path, header, table, decimal, title)
    else:
        write_csv(path, header, table, decimal)
