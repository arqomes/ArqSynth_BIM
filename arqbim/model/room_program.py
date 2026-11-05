"""(0.357) The project's programme (programa de necessidades): the rooms it asks for — each its name, the area wanted,
how many and whether it is interior or exterior —, read from a file (CSV, as a spreadsheet saves it, or a text with one
room a line), kept in the IFC (the project's ArqSynth_Parametros «Programa», JSON), listed in the Programme panel
(ui/room_program.py), from where a name is dragged into a space of the plan to make that room. Beside each, how many
are made and their area (the rooms of that name in the model).

A line of a file: «Quarto 1; 12,5; 1; interior» (name; area in m²; how many; interior / exterior) — all but the name
may be left out; a first line of headings (Ambiente, Área, Quantidade, Tipo…) is skipped; «;» (a spreadsheet's in
Portuguese, the decimal comma inside a number), a tab or «,» (the decimals then with a point) between them."""

import csv
import json
import re
from dataclasses import dataclass

EXTERNAL_WORDS = ("exterior", "externo", "external", "ext")
HEADINGS = ("ambiente", "nome", "name", "room", "compartimento", "espaço", "espaco", "divisão", "divisao")


@dataclass
class Need:
    name: str
    area: float = 0.0           # m² wanted (0: not said)
    count: int = 1
    external: bool = False


def _number(text):
    text = str(text or "").strip().replace("m²", "").replace("m2", "").strip()
    if not text:
        return None
    text = text.replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def parse(text):
    """The needs written in a text (a CSV's or a list's): [Need]."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    sample = "\n".join(lines[:20])
    delimiter = ";" if ";" in sample else ("\t" if "\t" in sample else ",")
    rows = list(csv.reader(lines, delimiter=delimiter))
    out = []
    for k, row in enumerate(rows):
        cells = [c.strip() for c in row]
        if not cells or not cells[0]:
            continue
        if k == 0 and cells[0].lower() in HEADINGS:
            continue                                     # (the headings)
        name = cells[0]
        area = _number(cells[1]) if len(cells) > 1 else None
        count = _number(cells[2]) if len(cells) > 2 else None
        kind = cells[3].lower() if len(cells) > 3 else ""
        out.append(Need(name, float(area or 0.0), max(1, int(count or 1)),
                        any(re.search(r"\b" + w + r"\b", kind) for w in EXTERNAL_WORDS)))
    return out


def read(path):
    """The needs in a file (CSV / TXT, UTF-8 or the Windows encoding a spreadsheet uses)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return parse(raw.decode(encoding))
        except UnicodeDecodeError:
            continue
    return []


def to_text(needs):
    return json.dumps([{"n": d.name, "a": round(float(d.area), 4), "q": int(d.count), "e": bool(d.external)}
                       for d in needs], ensure_ascii=False, separators=(",", ":"))


def from_text(text):
    out = []
    try:
        items = json.loads(text or "[]")
    except ValueError:
        return out
    for it in items:
        try:
            out.append(Need(str(it["n"]), float(it.get("a", 0.0)), int(it.get("q", 1)), bool(it.get("e", False))))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def progress(needs, spaces):
    """[(need, how many rooms of its name are made, their area)] — spaces: IfcModel.spaces() (the names compared
    without case nor spaces at the ends)."""
    made = {}
    for s in spaces:
        key = (s.get("name") or "").strip().lower()
        n, a = made.get(key, (0, 0.0))
        made[key] = (n + 1, a + float(s.get("area") or 0.0))
    return [(d,) + made.get(d.name.strip().lower(), (0, 0.0)) for d in needs]
