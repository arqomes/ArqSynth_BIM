"""(0.357) The project's programme (programa de necessidades): the rooms it asks for — each its name, the area wanted,
how many and whether it is interior or exterior —, read from a file (CSV, as a spreadsheet saves it, or a text with one
room a line), kept in the IFC (the project's ArqSynth_Parametros «Programa», JSON), listed in the Programme panel
(ui/room_program.py), from where a name is dragged into a space of the plan to make that room. Beside each, how many
are made and their area (the rooms of that name in the model).

A line of a file: «Quarto 1; 12,5; 1; interior» (name; area in m²; how many; interior / exterior) — all but the name
may be left out; a first line of headings (Ambiente, Área, Quantidade, Tipo…) is skipped; «;» (a spreadsheet's in
Portuguese, the decimal comma inside a number), a tab or «,» (the decimals then with a point) between them.

(0.475, the owner: «No painel, o utilizador pode criar a lista (programa de necessidade) por piso, e colocar a área
pretendida (opcional)… Na criação de lista deve ter o uso ou categoria. Deve admitir importação de lista feita com IA
em json») Each line also its use (model/program_rules.USES), its storey (a storey's GlobalId, or a name — a storey
made later with that name takes it) and an id the rooms placed from it keep («Programa» on the IfcSpace): their area
against the one wanted makes the line green (reached) or orange (to look at). The programme keeps its type of building
(the rules of conflicting zones are that type's). A JSON list — as an AI writes it — is read with its keys in
Portuguese or English (see parse_json)."""

import csv
import json
import re
import uuid
from dataclasses import dataclass, field

EXTERNAL_WORDS = ("exterior", "externo", "external", "ext")
HEADINGS = ("ambiente", "nome", "name", "room", "compartimento", "espaço", "espaco", "divisão", "divisao")


@dataclass
class Need:
    name: str
    area: float = 0.0           # m² wanted (0: not said)
    count: int = 1
    external: bool = False
    use: str = ""               # (0.475) program_rules.USES key ("" not said)
    storey: str = ""            # (0.475) a storey's GlobalId, or its name; "" any storey
    uid: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


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
    """The needs written in a text (a CSV's or a list's): [Need]. (0.475) A JSON text: parse_json's."""
    if text.lstrip()[:1] in ("{", "["):
        try:
            return parse_json(text)[1]
        except ValueError:
            pass
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
    """The needs in a file (CSV / TXT / JSON, UTF-8 or the Windows encoding a spreadsheet uses)."""
    return read_program(path)[1]


def read_program(path, storeys=()):
    """(0.475) (type of building or None, [Need]) of a file — a JSON's type and storeys (`storeys`: the project's
    [(GlobalId, name, level)], to find them by name)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        if text.lstrip()[:1] in ("{", "["):
            return parse_json(text, storeys)
        return None, parse(text)
    return None, []


# (0.475) the keys a JSON list may use (an AI's, in Portuguese or English)
NAME_KEYS = ("nome", "name", "ambiente", "room", "espaco", "espaço", "compartimento", "divisao", "divisão")
AREA_KEYS = ("area", "área", "area_m2", "área_m2", "area_pretendida", "área_pretendida", "target_area", "m2", "sqm")
COUNT_KEYS = ("quantidade", "qtd", "count", "quantity", "numero", "número", "n")
USE_KEYS = ("uso", "use", "categoria", "category", "tipo", "type", "funcao", "função", "function", "zona", "zone")
STOREY_KEYS = ("piso", "pavimento", "andar", "storey", "floor", "level", "nivel", "nível")
EXTERNAL_KEYS = ("exterior", "externo", "external", "outdoor")
LIST_KEYS = ("ambientes", "rooms", "espacos", "espaços", "programa", "program", "programme", "needs", "lista", "items")
FLOORS_KEYS = ("pisos", "pavimentos", "andares", "storeys", "floors", "levels")
TYPE_KEYS = ("tipo_edificio", "tipo_de_edificio", "tipo", "building_type", "building", "edificio", "edifício", "uso",
             "use", "type")


def _get(item, keys):
    for k in keys:
        for key in item:
            if str(key).strip().lower() == k:
                return item[key]
    return None


def parse_json(text, storeys=()):
    """(0.475) A programme written as JSON — as an AI makes it, keys in Portuguese or English:

        {"tipo": "habitação", "pisos": [{"nome": "Piso 0", "ambientes": [
            {"nome": "Sala", "uso": "estar", "area": 25}, {"nome": "Quarto", "uso": "quarto", "area": 12,
            "quantidade": 2}]}]}

    or a list of rooms each with its «piso». Returns (type of building or None, [Need]); a storey matched by name to
    the project's (`storeys`: [(GlobalId, name, level)]) keeps its GlobalId, another keeps its name. ValueError: not
    JSON."""
    from . import program_rules
    data = json.loads(text)
    building = None
    floors = []
    if isinstance(data, dict):
        found = _get(data, TYPE_KEYS)
        building = program_rules.type_from_text(found) if isinstance(found, str) else None
        levels = _get(data, FLOORS_KEYS)
        if isinstance(levels, list):
            for level in levels:
                if isinstance(level, dict):
                    rooms = _get(level, LIST_KEYS)
                    name = _get(level, ("nome", "name", "piso", "storey", "floor", "level"))
                    floors.append((str(name) if name is not None else "", rooms if isinstance(rooms, list) else []))
        rooms = _get(data, LIST_KEYS)
        if isinstance(rooms, list):
            floors.append(("", rooms))
    elif isinstance(data, list):
        floors.append(("", data))
    out = []
    for floor, rooms in floors:
        for item in rooms:
            if isinstance(item, str):
                item = {"nome": item}
            if not isinstance(item, dict):
                continue
            name = str(_get(item, NAME_KEYS) or "").strip()
            if not name:
                continue
            area = _number(_get(item, AREA_KEYS))
            count = _number(_get(item, COUNT_KEYS))
            use_text = _get(item, USE_KEYS)
            use = program_rules.use_from_text(use_text if isinstance(use_text, str) else "", name) or ""
            said = _get(item, EXTERNAL_KEYS)
            if isinstance(said, (bool, int, float)):
                external = bool(said)
            elif said is not None:
                external = str(said).strip().lower() in ("sim", "yes", "true", "s", "y")
            else:
                external = use in ("exterior", "recreio")
            storey = _get(item, STOREY_KEYS)
            storey = str(storey).strip() if storey is not None else floor
            out.append(Need(name, float(area or 0.0), max(1, int(count or 1)), bool(external), use,
                            storey_key(storey, storeys)))
    return building, out


def storey_key(text, storeys):
    """A storey said by name (or by its level: «0», «1») as the project's GlobalId when there is one, else the text."""
    text = str(text or "").strip()
    if not text:
        return ""
    plain = text.lower()
    for guid, name, _z in storeys:
        if guid == text or str(name).strip().lower() == plain:
            return guid
    number = re.fullmatch(r"(?:piso|andar|floor|level|pavimento)?\s*(-?\d+)", plain)
    if number is not None:
        ordered = sorted(storeys, key=lambda s: s[2])
        ground = next((k for k, s in enumerate(ordered) if abs(s[2]) < 1e-6), 0)
        k = ground + int(number.group(1))
        if 0 <= k < len(ordered):
            return ordered[k][0]
    if plain in ("r/c", "rc", "res-do-chao", "rés-do-chão", "terreo", "térreo", "ground", "ground floor"):
        ordered = sorted(storeys, key=lambda s: abs(s[2]))
        return ordered[0][0] if ordered else text
    return text


def storey_of(need, storeys):
    """The GlobalId of the storey a need is on (by its GlobalId, or the storey of its name), or None."""
    if need is None or not need.storey:
        return None
    for guid, name, _z in storeys:
        if guid == need.storey or str(name).strip().lower() == need.storey.strip().lower():
            return guid
    return None


def to_text(needs, building=None, rules=None):
    """The programme as kept: a list of its needs — (0.475) with a type of building or rules of its own, {"t", "r",
    "n"}."""
    items = []
    for d in needs:
        item = {"n": d.name, "a": round(float(d.area), 4), "q": int(d.count), "e": bool(d.external), "i": d.uid}
        if d.use:
            item["u"] = d.use
        if d.storey:
            item["s"] = d.storey
        items.append(item)
    if building is None and not rules:
        return json.dumps(items, ensure_ascii=False, separators=(",", ":"))
    data = {"n": items}
    if building:
        data["t"] = building
    if rules:
        data["r"] = [list(p) for p in rules]
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def from_text(text):
    return program_from_text(text)[1]


def program_from_text(text):
    """(0.475) (type of building or None, [Need], [(use, use)] the project's own conflicting pairs) as kept."""
    try:
        data = json.loads(text or "[]")
    except ValueError:
        return None, [], []
    building, rules = None, []
    if isinstance(data, dict):
        building = data.get("t") if isinstance(data.get("t"), str) else None
        rules = [tuple(map(str, p[:2])) for p in data.get("r") or () if isinstance(p, (list, tuple)) and len(p) >= 2]
        items = data.get("n") or []
    else:
        items = data
    out = []
    for it in items if isinstance(items, list) else ():
        try:
            need = Need(str(it["n"]), float(it.get("a", 0.0)), int(it.get("q", 1)), bool(it.get("e", False)),
                        str(it.get("u") or ""), str(it.get("s") or ""))
            if it.get("i"):
                need.uid = str(it["i"])
            out.append(need)
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    return building, out, rules


def progress(needs, spaces):
    """[(need, how many rooms of its name are made, their area)] — spaces: IfcModel.spaces() (the names compared
    without case nor spaces at the ends)."""
    made = {}
    for s in spaces:
        key = (s.get("name") or "").strip().lower()
        n, a = made.get(key, (0, 0.0))
        made[key] = (n + 1, a + float(s.get("area") or 0.0))
    return [(d,) + made.get(d.name.strip().lower(), (0, 0.0)) for d in needs]


AREA_TOL = 0.005                # m²: an area this short of the one wanted still reaches it (its rounding)


@dataclass
class State:
    """(0.475) A need against the model: its rooms (GlobalIds), their areas, and how it stands — "todo" (none placed),
    "ok" (as many as asked for, each as large as wanted: green), "short" (placed, but fewer or smaller: orange)."""
    need: Need
    rooms: list
    areas: list
    status: str

    @property
    def made(self):
        return len(self.rooms)

    @property
    def area(self):
        return float(sum(self.areas))


def states(needs, spaces, links, storeys=()):
    """Each need's State. spaces: IfcModel.spaces(); links: {room GlobalId: the need's uid it was placed from} — a room
    not placed from one counts for a need of its name on its storey (or any storey). A room counts once."""
    taken = set()
    by_uid = {}
    for guid, uid in links.items():
        by_uid.setdefault(uid, []).append(guid)
    info = {s["guid"]: s for s in spaces}
    out = []
    for need in needs:
        mine = [g for g in by_uid.get(need.uid, ()) if g in info]
        taken.update(mine)
        out.append([need, mine])
    for row in out:
        need, mine = row
        if len(mine) >= need.count:
            continue
        floor = storey_of(need, storeys)
        name = need.name.strip().lower()
        for s in spaces:
            g = s["guid"]
            if g in taken or links.get(g) or (s.get("name") or "").strip().lower() != name:
                continue
            if floor is not None and s.get("storey") != floor:
                continue
            mine.append(g)
            taken.add(g)
            if len(mine) >= need.count:
                break
    result = []
    for need, mine in out:
        areas = [float(info[g].get("area") or 0.0) for g in mine]
        if not mine:
            status = "todo"
        elif len(mine) >= need.count and (not need.area or min(areas) >= need.area - AREA_TOL):
            status = "ok"
        else:
            status = "short"
        result.append(State(need, mine, areas, status))
    return result


AI_PROMPT = (
    "Faz o programa de necessidades de {what} em JSON, só o JSON, neste formato:\n"
    '{{"tipo": "{type}", "pisos": [{{"nome": "Piso 0", "ambientes": [\n'
    '  {{"nome": "Sala", "uso": "estar", "area": 25, "quantidade": 1}},\n'
    '  {{"nome": "Quarto", "uso": "quarto", "area": 12, "quantidade": 2}}]}}]}}\n'
    "A área em m² (pode faltar). Os usos possíveis: {uses}.\n"
    "Os tipos de edifício possíveis: {types}.")
