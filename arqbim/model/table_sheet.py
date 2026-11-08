"""(0.478, the owner: «A tela, deve ser em células como no excel e ter as ferramentas de união de células alinhamento,
desenho de bordas, cálculo como no excel, a ideia é criar algo poderoso para criar tabelas com mais liberdade») A table
of the project's own (model/schedules.ScheduleDef) as a spreadsheet: its grid is made of zones, top to bottom —

    T  free rows above (titles, notes): any text, number or formula, merged, formatted
    H  the headings' row (a heading can be renamed, formatted, merged)
    D  the elements' rows, from the model (as many as there are; formatted by column)
    S  the totals' row (its own sums, or a formula of the user's)
    N  free rows below (notes, sums, prices…)

and the columns are the table's (A, B, C…). Every cell is kept by its zone, its row in the zone and its column's field
(«length»), so that it follows its column when the columns are put in another order, or one is added or taken away, in
the table's Properties or with Inserir ▸ Coluna — as a column's cells do in Excel (a column taken away: its cells too).

A formula is written as in Excel — «=SOMA(D:D)», «=D12*1,23», «=ARRED(MÉDIA(E3:E9);2)» — and kept tied to its zone, row
and field («[D3@length]», «[N1@area]», «[S@length]», «[*@area]» the elements' column), so that it still points at the
same cell when the model has more or fewer elements, rows are put over it, or the columns change; «D:D» is a column's
elements, however many. Functions: SOMA/SUM, MÉDIA/AVERAGE, MÍNIMO/MIN, MÁXIMO/MAX, CONTAR/COUNT (numbers),
CONTAR.VAL/COUNTA (not empty), ARRED/ROUND, ABS, SE/IF; + - * / ^ and the comparisons; the decimal comma and «;» between
arguments, as in a Portuguese Excel. Nothing else is run (the expression is checked node by node). Errors as Excel's:
#REF!, #VALOR!, #DIV/0!, #NOME?, #CIRC!. A text may hold the project's data: {projeto}, {data}, {tabela}, {n} (how many
elements)."""

import ast
import math
import re
from dataclasses import dataclass, field

ZONES = ("T", "H", "D", "S", "N")
FREE = ("T", "N")                       # (rows added and taken away by the user)
MERGEABLE = ("T", "H", "S", "N")        # (the elements' rows change with the model: not merged)
ALIGNS = ("left", "center", "right")
FILLS = ("#fff2cc", "#e2efda", "#ddebf7", "#fce4d6", "#ededed", "#d9d9d9")     # (light: the text stays black)
SIDES = "ltrb"                          # a cell's borders: its sides (as Excel keeps them, cell by cell)
BORDERS = ("all", "outer", "thick_outer", "bottom", "top_bottom", "none")
TOKENS = ("projeto", "data", "tabela", "n")
MAX_FREE = 200                          # rows above / below at most
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def col_letter(k):
    """0 -> A, 25 -> Z, 26 -> AA."""
    out, k = "", int(k) + 1
    while k:
        k, r = divmod(k - 1, 26)
        out = chr(65 + r) + out
    return out


def col_index(letters):
    k = 0
    for ch in letters.upper():
        k = k * 26 + ord(ch) - 64
    return k - 1


@dataclass
class Layout:
    """The spreadsheet of a table: how many free rows above (top) and below (bottom), whether it has its totals' row,
    its cells (key() -> {"v": text or formula as kept, "b": bold, "i": italic, "a": align, "f": fill, "bd": its
    bordered sides «ltrb», "bw": thick}), its merged blocks ([zone, row, its first column's field, rows, cols]) and its
    columns' widths (px, by field)."""
    top: int = 0
    bottom: int = 0
    totals: bool = True
    cells: dict = field(default_factory=dict)
    merges: list = field(default_factory=list)
    widths: dict = field(default_factory=dict)

    def is_plain(self):
        return not (self.top or self.bottom or self.cells or self.merges or self.widths) and self.totals


def key(zone, row, col):
    """A cell's key in a layout, by its column's field: «T:0:name» (a title row's), «H:0:length», «S:0:length»,
    «N:2:area», «D:*:length» (the elements' rows: a whole column)."""
    if zone == "D":
        return "D:*:{}".format(col)
    if zone in ("H", "S"):
        return "{}:0:{}".format(zone, col)
    return "{}:{}:{}".format(zone, int(row), col)


def parse_key(text):
    """(zone, row, its column's field) of a cell's key, or None."""
    parts = str(text).split(":", 2)
    if len(parts) != 3 or parts[0] not in ZONES or not parts[2]:
        return None
    zone, row, col = parts
    if zone in FREE:
        try:
            return zone, int(row), col
        except ValueError:
            return None
    return zone, ("*" if zone == "D" else 0), col


def clean_cell(data):
    if not isinstance(data, dict):
        return None
    out = {}
    v = data.get("v")
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        out["v"] = v
    elif isinstance(v, str) and v != "":
        out["v"] = v[:2000]
    for k in ("b", "i"):
        if isinstance(data.get(k), bool):           # (False too: a heading not in bold, as it is by default)
            out[k] = data[k]
    if data.get("a") in ALIGNS:
        out["a"] = data["a"]
    if isinstance(data.get("f"), str) and _HEX.match(data["f"]):
        out["f"] = data["f"].lower()
    sides = "".join(s for s in SIDES if s in str(data.get("bd") or ""))
    if sides:
        out["bd"] = sides
        if data.get("bw"):
            out["bw"] = True                # (thick)
    return out or None


def layout_from_dict(data):
    if not isinstance(data, dict):
        return Layout()
    try:
        top, bottom = int(data.get("top", 0) or 0), int(data.get("bottom", 0) or 0)
    except (TypeError, ValueError):
        top, bottom = 0, 0
    out = Layout(min(max(top, 0), MAX_FREE), min(max(bottom, 0), MAX_FREE), bool(data.get("totals", True)))
    for k, cell in (data.get("cells") or {}).items():
        parsed, found = parse_key(k), clean_cell(cell)
        if parsed is not None and found is not None:
            out.cells[key(*parsed)] = found
    for m in data.get("merges") or ():
        try:
            zone, r, c, rows, cols = m[0], int(m[1]), str(m[2]), int(m[3]), int(m[4])
        except (TypeError, ValueError, IndexError):
            continue
        if zone in MERGEABLE and rows >= 1 and cols >= 1 and (rows > 1 or cols > 1):
            out.merges.append([zone, r if zone in FREE else 0, c, rows if zone in FREE else 1, cols])
    for k, w in (data.get("widths") or {}).items():
        try:
            out.widths[str(k)] = min(max(int(w), 20), 1200)
        except (TypeError, ValueError):
            continue
    return out


def layout_to_dict(layout):
    if layout is None or layout.is_plain():
        return {}
    return {"top": layout.top, "bottom": layout.bottom, "totals": layout.totals, "cells": dict(layout.cells),
            "merges": [list(m) for m in layout.merges], "widths": dict(layout.widths)}


def copy_layout(layout):
    return layout_from_dict(layout_to_dict(layout)) if layout is not None and not layout.is_plain() else Layout()


@dataclass
class Geometry:
    """Where each zone is in the grid shown: rows top to bottom (0-based); its columns' fields (`keys`)."""
    top: int
    n: int                  # the elements' rows
    totals: bool
    bottom: int
    keys: list

    @property
    def width(self):
        return len(self.keys)

    @property
    def rows(self):
        return self.top + 1 + self.n + (1 if self.totals else 0) + self.bottom

    def zone_of(self, row):
        """(zone, its row in the zone — 0-based; the headings' and totals': 0) of a grid row, or None."""
        if row < 0:
            return None
        if row < self.top:
            return "T", row
        row -= self.top
        if row == 0:
            return "H", 0
        row -= 1
        if row < self.n:
            return "D", row
        row -= self.n
        if self.totals:
            if row == 0:
                return "S", 0
            row -= 1
        if row < self.bottom:
            return "N", row
        return None

    def grid_row(self, zone, row):
        """The grid row (0-based) of a zone's row, or None (not there)."""
        if zone == "T":
            return row if 0 <= row < self.top else None
        if zone == "H":
            return self.top
        if zone == "D":
            return self.top + 1 + row if 0 <= row < self.n else None
        if zone == "S":
            return self.top + 1 + self.n if self.totals else None
        if zone == "N":
            return self.top + 1 + self.n + (1 if self.totals else 0) + row if 0 <= row < self.bottom else None
        return None

    def column_id(self, zone, c):
        """How a layout keeps column `c` (0-based): its field."""
        return self.keys[c] if 0 <= c < len(self.keys) else None

    def column_at(self, zone, col):
        """The column (0-based) a layout's column (its field) is shown at, or None (that field is not there)."""
        try:
            return self.keys.index(col)
        except ValueError:
            return None

    def cell_key(self, g, c):
        """A grid cell's key in a layout, or None."""
        found = self.zone_of(g)
        if found is None or not 0 <= c < self.width:
            return None
        return key(found[0], found[1], self.column_id(found[0], c))


# ---------------------------------------------------------------- formulas: as written (A1) <-> as kept

_STRING = re.compile(r'"[^"]*"')
_A1 = re.compile(r"(?<![A-Za-z_\]\[@\d$.])\$?([A-Z]{1,3})\$?(\d+)(?::\$?([A-Z]{1,3})\$?(\d+))?(?![A-Za-z_(\d])"
                 r"|(?<![A-Za-z_\]\[@\d$.])([A-Z]{1,3}):([A-Z]{1,3})(?![A-Za-z_\d(])")
_KEPT = re.compile(r"\[([THDSN])(\d*)@([^\]]+)\]|\[\*@([^\]]+)\](?::\[\*@([^\]]+)\])?")
_FUNCTION = re.compile(r"[A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ_0-9.]*(?=\s*\()")


def _outside_strings(text, fn):
    """fn applied to the parts of a formula outside "…" strings."""
    out, last = [], 0
    for m in _STRING.finditer(text):
        out.append(fn(text[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(fn(text[last:]))
    return "".join(out)


def to_internal(text, geom):
    """A formula as written («=SOMA(B3:B9)*1,23») as kept: its cells by zone, row and field
    («[D1@length]:[D7@length]», «[N2@area]», «[S@length]»); a cell out of the grid: #REF!."""
    text = str(text)
    if not text.startswith("="):
        return text

    def ref(col, row):
        g, c = int(row) - 1, col_index(col)
        found = geom.zone_of(g)
        if found is None or c >= geom.width:
            return "#REF!"
        zone, r = found
        return "[{}{}@{}]".format(zone, "" if zone in ("H", "S") else r + 1, geom.keys[c])

    def one(m):
        if m.group(5):                                          # «B:D» — the elements' rows of those columns
            a, b = col_index(m.group(5)), col_index(m.group(6))
            if max(a, b) >= geom.width:
                return "#REF!"
            if a == b:
                return "[*@{}]".format(geom.keys[a])
            return "[*@{}]:[*@{}]".format(geom.keys[a], geom.keys[b])
        first = ref(m.group(1), m.group(2))
        return first if not m.group(3) else "{}:{}".format(first, ref(m.group(3), m.group(4)))

    def part(chunk):
        return _A1.sub(one, chunk.upper())                      # («=soma(b3:b9)» as «=SOMA(B3:B9)»)
    return _outside_strings(text, part)


def to_display(text, geom):
    """A formula as kept, written as in Excel for the grid as it is now («[D1@length]» -> «B4»); a field no longer
    there, or a row taken away: #REF!."""
    text = str(text)
    if not text.startswith("="):
        return text

    def one(m):
        if m.group(1):                                          # a cell, by its zone, row and field
            row = geom.grid_row(m.group(1), int(m.group(2)) - 1 if m.group(2) else 0)
            c = geom.column_at(m.group(1), m.group(3))
            return "#REF!" if row is None or c is None else "{}{}".format(col_letter(c), row + 1)
        a = geom.column_at("D", m.group(4))                     # the elements' rows of a column (of columns)
        b = geom.column_at("D", m.group(5)) if m.group(5) else a
        return "#REF!" if a is None or b is None else "{}:{}".format(col_letter(a), col_letter(b))
    return _outside_strings(text, lambda chunk: _KEPT.sub(one, chunk))


def shift_rows(text, zone, at, step):
    """A formula kept, after `step` free rows were put (> 0) or taken away (< 0) in zone T or N at its row `at`
    (0-based): its references to the rows after moved; to a row taken away: #REF!."""
    text = str(text)
    if not text.startswith("="):
        return text

    def one(m):
        if m.group(1) != zone or not m.group(2):
            return m.group(0)
        r = int(m.group(2)) - 1
        if step < 0 and at <= r < at - step:
            return "#REF!"
        if r >= at:
            r += step
        return "[{}{}@{}]".format(zone, r + 1, m.group(3))
    return _outside_strings(text, lambda chunk: _KEPT.sub(one, chunk))


EXCEL_NAMES = {"SOMA": "SUM", "MÉDIA": "AVERAGE", "MEDIA": "AVERAGE", "MÍNIMO": "MIN", "MINIMO": "MIN",
               "MÁXIMO": "MAX", "MAXIMO": "MAX", "CONTAR": "COUNT", "CONTAR.VAL": "COUNTA", "CONT.VALORES": "COUNTA",
               "ARRED": "ROUND", "ARREDONDAR": "ROUND", "SE": "IF"}


def to_excel(text, geom):
    """A formula as kept, as an Excel workbook keeps it (its functions' English names, «,» between arguments, «.»
    in numbers, «D:D» the elements' rows: «D4:D9») for the grid exported as it is shown — None: not one Excel takes
    (a #REF!, a column with no elements)."""
    text = str(text)
    if not text.startswith("="):
        return None
    written = to_display(text, geom)
    if "#REF!" in written:
        return None
    first, last = geom.grid_row("D", 0), geom.grid_row("D", geom.n - 1)

    def one(m):
        if not m.group(5):
            return m.group(0)
        if first is None:
            raise ValueError("no elements")
        return "{}{}:{}{}".format(m.group(5), first + 1, m.group(6), last + 1)

    def part(chunk):
        chunk = _A1.sub(one, chunk)
        chunk = _FUNCTION.sub(lambda m: EXCEL_NAMES.get(m.group(0).upper(), m.group(0).upper()), chunk)
        return re.sub(r"(\d),(\d)", r"\1.\2", chunk).replace(";", ",")
    try:
        return _outside_strings(written, part)
    except ValueError:
        return None


# ---------------------------------------------------------------- evaluation

class FormulaError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


FUNCTIONS = {"SOMA": "_sum", "SUM": "_sum", "MÉDIA": "_avg", "MEDIA": "_avg", "AVERAGE": "_avg", "MÍNIMO": "_min",
             "MINIMO": "_min", "MIN": "_min", "MÁXIMO": "_max", "MAXIMO": "_max", "MAX": "_max", "CONTAR": "_count",
             "COUNT": "_count", "CONTAR.VAL": "_counta", "CONT.VALORES": "_counta", "COUNTA": "_counta",
             "ARRED": "_round", "ARREDONDAR": "_round", "ROUND": "_round", "ABS": "_abs", "SE": "_if", "IF": "_if"}
_ALLOWED_NODES = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Compare, ast.Call, ast.Name, ast.Constant, ast.Load,
                  ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd, ast.Eq, ast.NotEq,
                  ast.Lt, ast.LtE, ast.Gt, ast.GtE)


def _flat(values):
    for v in values:
        if isinstance(v, (list, tuple)):
            yield from _flat(v)
        else:
            yield v


def _numbers(values):
    return [float(v) for v in _flat(values) if isinstance(v, (int, float)) and not isinstance(v, bool)]


def number_of(text):
    """A value written in a cell («12», «1 234,5», «-0,25»): the number, or None (a text)."""
    plain = str(text).strip().replace(" ", "").replace(" ", "")
    if re.fullmatch(r"-?\d+([.,]\d+)?", plain):
        return float(plain.replace(",", "."))
    return None


def _python(formula):
    """A formula as written (A1, without its «=») as a Python expression of the evaluator's names; FormulaError(#NOME?)
    for a function it does not know."""
    def name(m):
        mapped = FUNCTIONS.get(m.group(0).upper())
        if mapped is None:                                  # (one it does not know — or «_…»: none of the user's)
            raise FormulaError("#NOME?")
        return mapped

    def cell(m):
        if m.group(5):
            return "_col({},{})".format(col_index(m.group(5)), col_index(m.group(6)))
        g, c = int(m.group(2)) - 1, col_index(m.group(1))
        if not m.group(3):
            return "_cell({},{})".format(g, c)
        return "_range({},{},{},{})".format(g, c, int(m.group(4)) - 1, col_index(m.group(3)))

    def part(chunk):
        chunk = _FUNCTION.sub(name, chunk.upper())          # (the functions first: «_…» from here on is the program's)
        chunk = re.sub(r"(\d),(\d)", r"\1.\2", chunk).replace(";", ",")      # (before the cells' «_cell(2,1)»)
        chunk = _A1.sub(cell, chunk)
        chunk = chunk.replace("#REF!", "_ref_error()")
        chunk = chunk.replace("<>", "!=").replace("^", "**")
        return re.sub(r"(?<![<>!=])=(?!=)", "==", chunk)
    return _outside_strings(formula, part)


def evaluate(formula, cell, block, column):
    """A formula's value (a number or a text), or FormulaError; the formula as written (A1). cell(grid row, col) ->
    its value; block(row1, col1, row2, col2) -> the values of a block; column(col1, col2) -> the elements' values of
    those columns."""
    text = str(formula)[1:] if str(formula).startswith("=") else str(formula)
    expression = _python(text)
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        raise FormulaError("#VALOR!") from None
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise FormulaError("#VALOR!")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float, str)):
            raise FormulaError("#VALOR!")
        if isinstance(node, ast.Call) and (not isinstance(node.func, ast.Name) or node.keywords):
            raise FormulaError("#VALOR!")

    def ref_error():
        raise FormulaError("#REF!")

    def one(v):
        if isinstance(v, (list, tuple)):
            raise FormulaError("#VALOR!")
        return 0.0 if v is None or v == "" else v

    def rnd(v, places=0):
        return round(float(one(v)), int(one(places)))

    names = {"_cell": lambda g, c: one(cell(g, c)), "_range": block, "_col": column, "_ref_error": ref_error,
             "_sum": lambda *a: sum(_numbers(a)), "_avg": lambda *a: _avg(_numbers(a)),
             "_min": lambda *a: min(_numbers(a)) if _numbers(a) else 0.0,
             "_max": lambda *a: max(_numbers(a)) if _numbers(a) else 0.0,
             "_count": lambda *a: float(len(_numbers(a))),
             "_counta": lambda *a: float(len([v for v in _flat(a) if v is not None and v != ""])),
             "_round": rnd, "_abs": lambda v: abs(float(one(v))),
             "_if": lambda c, a=True, b=False: a if c else b}
    try:
        value = eval(compile(tree, "<formula>", "eval"), {"__builtins__": {}}, names)    # noqa: S307 (checked above)
    except FormulaError:
        raise
    except ZeroDivisionError:
        raise FormulaError("#DIV/0!") from None
    except (TypeError, ValueError, OverflowError, NameError, RecursionError):
        raise FormulaError("#VALOR!") from None
    if isinstance(value, bool):
        return "VERDADEIRO" if value else "FALSO"
    if isinstance(value, float) and not math.isfinite(value):
        raise FormulaError("#VALOR!")
    return value


def _avg(values):
    if not values:
        raise FormulaError("#DIV/0!")
    return sum(values) / len(values)


def shown(value, decimal=","):
    """A cell's value as the grid shows it: a whole number without decimals, else two; a text as it is."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "VERDADEIRO" if value else "FALSO"
    if isinstance(value, (int, float)):
        if abs(value - round(value)) < 1e-9:
            return str(int(round(value)))
        return "{:.2f}".format(value).replace(".", decimal)
    return str(value)


def fill_tokens(text, tokens):
    """A text with the project's data put in («{projeto}», «{data}», «{tabela}», «{n}»)."""
    if not tokens or "{" not in str(text):
        return text
    return re.sub(r"\{(\w+)\}", lambda m: str(tokens.get(m.group(1).lower(), m.group(0))), str(text))


# ---------------------------------------------------------------- the grid

@dataclass
class GridCell:
    text: str = ""
    value: object = None            # a number, a text, or None
    zone: str = "T"
    row: int = 0                    # in its zone
    col: int = 0
    raw: str = ""                   # what is written in it, as written (a formula in A1) — "" none
    error: bool = False
    fmt: dict = field(default_factory=dict)


def build(layout, keys, headings, data, totals, data_texts=None, totals_texts=None, decimal=",", tokens=None):
    """The grid of a table: ([[GridCell]] rows top to bottom, its Geometry). keys: its columns' fields; headings: their
    headings; data: the elements' rows ([values] per row, numbers as numbers); totals: the totals' row's own values
    ([value or None]); data_texts / totals_texts: those cells as written («4,50 m»), else shown(). Formulas worked
    out (a cell's value may use another's: in turn, a loop -> #CIRC!)."""
    width = len(keys)
    geom = Geometry(layout.top, len(data), layout.totals, layout.bottom, list(keys))
    raw, fmt = {}, {}
    for k, cell in layout.cells.items():
        parsed = parse_key(k)
        if parsed is None:
            continue
        zone, row, col = parsed
        c = geom.column_at(zone, col)
        if c is None:
            continue
        f = {x: y for x, y in cell.items() if x != "v"}
        if f:
            fmt[(zone, row, c)] = f
        if "v" in cell and zone != "D":
            raw[(zone, row, c)] = cell["v"]

    def base(zone, row, col):
        """The value a cell has without what the user wrote in it."""
        if zone == "H":
            return headings[col] if col < len(headings) else ""
        if zone == "D":
            return data[row][col] if 0 <= row < len(data) and col < len(data[row]) else None
        if zone == "S":
            return totals[col] if col < len(totals) else None
        return None

    values, busy, written_as = {}, set(), {}

    def value(zone, row, col):
        here = (zone, row, col)
        if here in values:
            return values[here]
        if here in busy:
            raise FormulaError("#CIRC!")
        written = raw.get(here)
        if written is None:
            return base(zone, row, col)
        if isinstance(written, (int, float)):
            return written
        if not str(written).startswith("="):
            text = fill_tokens(written, tokens)
            found = number_of(text)
            return found if found is not None else text
        busy.add(here)
        try:
            result = evaluate(written_as.setdefault(here, to_display(written, geom)), cell_at, block, column)
        finally:
            busy.discard(here)
        values[here] = result
        return result

    def cell_at(g, c):
        found = geom.zone_of(g)
        if found is None or not 0 <= c < width:
            raise FormulaError("#REF!")
        return value(found[0], found[1], c)

    def block(g1, c1, g2, c2):
        out = []
        for g in range(min(g1, g2), max(g1, g2) + 1):
            for c in range(min(c1, c2), max(c1, c2) + 1):
                out.append(cell_at(g, c))
        return out

    def column(c1, c2):
        a, b = sorted((c1, c2))
        if b >= width:
            raise FormulaError("#REF!")
        return [value("D", r, c) for r in range(len(data)) for c in range(a, b + 1)]

    grid = []
    for g in range(geom.rows):
        zone, row = geom.zone_of(g)
        line = []
        for c in range(width):
            written = raw.get((zone, row, c), "")
            gc = GridCell(zone=zone, row=row, col=c, fmt=dict(fmt.get((zone, "*" if zone == "D" else row, c)) or {}))
            if isinstance(written, str) and written.startswith("="):
                gc.raw = written_as.setdefault((zone, row, c), to_display(written, geom))
            else:
                gc.raw = written if isinstance(written, str) else shown(written, decimal)
            try:
                gc.value = value(zone, row, c)
                if zone == "D" and data_texts is not None:
                    gc.text = data_texts[row][c]
                elif zone == "S" and written == "" and totals_texts is not None and c < len(totals_texts):
                    gc.text = totals_texts[c]
                else:
                    gc.text = shown(gc.value, decimal)
            except FormulaError as exc:
                gc.value, gc.text, gc.error = None, exc.code, True
            line.append(gc)
        grid.append(line)
    return grid, geom


def merges_in_grid(layout, geom):
    """The merged blocks as (grid row, col, rows, cols) for the grid as it is now (those out of it left out)."""
    out = []
    for zone, r, col, rows, cols in layout.merges:
        g, c = geom.grid_row(zone, r), geom.column_at(zone, col)
        if g is None or c is None:
            continue
        if rows > 1 and geom.grid_row(zone, r + rows - 1) is None:
            continue
        cols = min(cols, geom.width - c)
        if rows > 1 or cols > 1:
            out.append((g, c, rows, cols))
    return out


def merge_at(layout, geom, g, c):
    """The merged block (grid row, col, rows, cols) the grid cell is in, or None."""
    for block in merges_in_grid(layout, geom):
        if block[0] <= g < block[0] + block[2] and block[1] <= c < block[1] + block[3]:
            return block
    return None


# ---------------------------------------------------------------- changes (each returns a new Layout; None: refused)

def set_value(layout, geom, g, c, text):
    """What is written in a grid cell (a formula as written: kept by zone and field); "" clears it. The elements' rows:
    refused (None) — they are the model's."""
    found = geom.zone_of(g)
    if found is None or found[0] == "D" or not 0 <= c < geom.width:
        return None
    out = copy_layout(layout)
    k = geom.cell_key(g, c)
    cell = dict(out.cells.get(k) or {})
    text = str(text)
    if text.strip() == "":
        cell.pop("v", None)
    else:
        cell["v"] = to_internal(text.strip(), geom) if text.strip().startswith("=") else text
    found_cell = clean_cell(cell)
    if found_cell:
        out.cells[k] = found_cell
    else:
        out.cells.pop(k, None)
    return out


def set_format(layout, geom, cells, **changes):
    """A format given to grid cells [(row, col)] — the elements' rows: their whole column. changes: b, i (True /
    False), a (an align), f (a fill): None and "" take it away (as it comes)."""
    out = copy_layout(layout)
    for g, c in cells:
        k = geom.cell_key(g, c)
        if k is None:
            continue
        cell = dict(out.cells.get(k) or {})
        for name, v in changes.items():
            if v is None or v == "":
                cell.pop(name, None)
            else:
                cell[name] = v
        found = clean_cell(cell)
        if found:
            out.cells[k] = found
        else:
            out.cells.pop(k, None)
    return out


def set_borders(layout, geom, r0, c0, r1, c1, kind):
    """Borders drawn on a block of the grid (grid rows r0..r1, columns c0..c1), as Excel's button: "all" every cell's
    sides, "outer" / "thick_outer" its outline, "bottom" its bottom, "top_bottom" its top and bottom, "none" none in
    it. The elements' rows keep a column's borders: a block's top or bottom there goes to the row beside it (the
    headings', the totals'), or is left out. A merged block: its outline on its first cell."""
    r0, r1, c0, c1 = min(r0, r1), max(r0, r1), min(c0, c1), max(c0, c1)
    out = copy_layout(layout)
    blocks = {(g, c): (rows, cols) for g, c, rows, cols in merges_in_grid(layout, geom)}
    covered = {(g + i, c + j) for (g, c), (rows, cols) in blocks.items() for i in range(rows) for j in range(cols)
               if i or j}
    if kind in ("none", "all"):                         # (started afresh in the block)
        for g in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                k = geom.cell_key(g, c)
                if k in out.cells:
                    cell = {x: y for x, y in out.cells[k].items() if x not in ("bd", "bw")}
                    if cell:
                        out.cells[k] = cell
                    else:
                        out.cells.pop(k)
    if kind == "none":
        return out
    adds = {}                                           # cell key -> sides to add

    def add(g, c, sides):
        found = geom.zone_of(g)
        if found is None or not sides:
            return
        if found[0] == "D" and kind != "all":
            sides = sides.replace("t", "").replace("b", "")
        if sides:
            adds.setdefault(geom.cell_key(g, c), set()).update(sides)

    for g in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (g, c) in covered:
                continue
            rows, cols = blocks.get((g, c), (1, 1))
            bottom, right = g + rows - 1, c + cols - 1
            if kind == "all":
                sides = "ltrb"
            elif kind in ("outer", "thick_outer"):
                sides = ("l" if c == c0 else "") + ("t" if g == r0 else "") + ("r" if right >= c1 else "") + \
                    ("b" if bottom >= r1 else "")
            elif kind == "bottom":
                sides = "b" if bottom >= r1 else ""
            else:                                       # top_bottom
                sides = ("t" if g == r0 else "") + ("b" if bottom >= r1 else "")
            if (geom.zone_of(g) or ("",))[0] == "D" and kind != "all":
                if "t" in sides and (geom.zone_of(g - 1) or ("D",))[0] != "D":
                    add(g - 1, c, "b")                  # (a block's top in the elements' rows: the row over them)
                if "b" in sides and (geom.zone_of(bottom + 1) or ("D",))[0] != "D":
                    add(bottom + 1, c, "t")
            add(g, c, sides)
    for k, sides in adds.items():
        cell = dict(out.cells.get(k) or {})
        cell["bd"] = "".join(s for s in SIDES if s in sides or s in str(cell.get("bd") or ""))
        if kind == "thick_outer":
            cell["bw"] = True
        found = clean_cell(cell)
        if found:
            out.cells[k] = found
    return out


def merge(layout, geom, r0, c0, r1, c1):
    """A block of the grid merged (its first cell's content kept) — refused (None) in the elements' rows, across zones,
    or over more than one row of the headings' / totals'."""
    r0, r1, c0, c1 = min(r0, r1), max(r0, r1), min(c0, c1), max(c0, c1)
    first, last = geom.zone_of(r0), geom.zone_of(r1)
    if first is None or last is None or first[0] != last[0] or first[0] not in MERGEABLE or \
            (r0 == r1 and c0 == c1) or c1 >= geom.width:
        return None
    zone = first[0]
    out = copy_layout(layout)
    covered = {(g, c) for g in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
    out.merges = [m for m in out.merges if not any(cell in covered for cell in _cells_of(m, geom))]
    out.merges.append([zone, first[1], geom.column_id(zone, c0), r1 - r0 + 1, c1 - c0 + 1])
    return out


def _cells_of(m, geom):
    zone, r, col, rows, cols = m
    g, c = geom.grid_row(zone, r), geom.column_at(zone, col)
    if g is None or c is None:
        return []
    return [(g + i, c + j) for i in range(rows) for j in range(cols)]


def unmerge(layout, geom, g, c):
    """The merged block the grid cell is in, separated."""
    out = copy_layout(layout)
    out.merges = [m for m in out.merges if (g, c) not in _cells_of(m, geom)]
    return out


def insert_rows(layout, zone, at, count=1):
    """`count` free rows put in zone T or N before its row `at` (its end: at = its rows): cells, merges and formulas
    moved."""
    if zone not in FREE:
        return None
    out = copy_layout(layout)
    size = out.top if zone == "T" else out.bottom
    at = min(max(int(at), 0), size)
    if size + count > MAX_FREE:
        return None
    cells = {}
    for k, cell in out.cells.items():
        z, r, c = parse_key(k)
        if z == zone and r >= at:
            r += count
        cell = dict(cell)
        if isinstance(cell.get("v"), str):
            cell["v"] = shift_rows(cell["v"], zone, at, count)
        cells[key(z, r, c)] = cell
    out.cells = cells
    out.merges = [[z, r + count if z == zone and r >= at else r, c, rr, cc] for z, r, c, rr, cc in out.merges]
    if zone == "T":
        out.top += count
    else:
        out.bottom += count
    return out


def delete_rows(layout, zone, at, count=1):
    """Free rows taken away (zone T or N): their cells and merges gone, the formulas pointing at them #REF!."""
    if zone not in FREE:
        return None
    out = copy_layout(layout)
    size = out.top if zone == "T" else out.bottom
    if not 0 <= at < size:
        return None
    count = min(count, size - at)
    cells = {}
    for k, cell in out.cells.items():
        z, r, c = parse_key(k)
        if z == zone and at <= r < at + count:
            continue
        if z == zone and r >= at + count:
            r -= count
        cell = dict(cell)
        if isinstance(cell.get("v"), str):
            cell["v"] = shift_rows(cell["v"], zone, at, -count)
        cells[key(z, r, c)] = cell
    out.cells = cells
    merges = []
    for z, r, c, rr, cc in out.merges:
        if z == zone and at <= r < at + count:
            continue
        merges.append([z, r - count if z == zone and r >= at + count else r, c, rr, cc])
    out.merges = merges
    if zone == "T":
        out.top -= count
    else:
        out.bottom -= count
    return out
