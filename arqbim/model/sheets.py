"""Sheets (Phase 3, step 8): a sheet of paper with several views of the model — plans,
sections, elevations — each at its scale, where the user put it (or laid out on its own).
A sheet is a view, not IFC: saved with the sketches (.arqbim). The drawings themselves are
made when the sheet is shown or printed, so a sheet is always the model as it is.

Sizes on the sheet in millimetres, from the sheet's top-left corner (y down, as on paper).
"""

import math
import os
import re
import uuid
from dataclasses import dataclass, field

PAPERS = {"A4": (297.0, 210.0), "A3": (420.0, 297.0), "A2": (594.0, 420.0), "A1": (841.0, 594.0),   # landscape
          "A0": (1189.0, 841.0)}                     # (0.470, the owner: «deve incluir tamanho A4»)


def paper_size(paper, portrait=False):
    """(w, h) mm of a paper — (0.470) stood up (portrait: its short side across)."""
    w, h = PAPERS.get(paper, PAPERS["A3"])
    return (h, w) if portrait else (w, h)
SCALES = (20, 50, 100, 200, 500, 1000)
MARGIN = 10.0                  # mm: the border's distance from the paper's edge
TITLE_W, TITLE_H = 120.0, 40.0     # mm: the title block, bottom right inside the border
TITLE_FIELDS = ("project", "client", "site", "author", "stage")    # the project's, the same on every sheet
GAP = 12.0                     # mm between two views laid out
LABEL_H = 8.0                  # mm under a view: its name and scale
KINDS = ("plan", "section", "elevation", "schedule", "detail", "3d",       # (0.132–0.134)
         "rebar", "structure", "rebar_cut",    # (0.234: kept in the file too — a member's reinforcement, its section)
         "structure_below",                    # (0.235: a storey's formwork seen from below)
         "rebar_details",                      # (0.237: the project's typical reinforcement details)
         "openings",                           # (0.293: the project's mapa de vãos)
         "steel_parts",                        # (0.502: the steel pieces' fabrication drawing)
         "steel_erection",                     # (0.510: the steel's erection plan)
         "steel_assemblies")                   # (0.515: the steel assemblies with their welds)
# (0.234) the scale a kind of view takes when it has none of its own and fits the sheet so: a member's reinforcement
# at 1:50, its section at 1:20 (their labels and dimensions spaced for it) — (0.237) the typical details at 1:20 —
# (0.293) the mapa de vãos at 1:50
USUAL_SCALES = {"rebar": 50, "rebar_cut": 20, "rebar_details": 20, "openings": 50, "steel_parts": 50,
                "steel_erection": 100, "steel_assemblies": 50}


@dataclass
class Placed:
    """A view on a sheet. kind: "plan" (ref: the storey's GlobalId), "section" (ref: its name),
    "elevation" (ref: "N", "S", "E", "W"). scale: N of 1:N, None = chosen with the layout.
    at: its centre on the sheet (mm), None = laid out with the others."""
    kind: str
    ref: str
    scale: int = None
    at: tuple = None


IMPORT_KINDS = ("cad", "image", "svg")     # (0.472) what a sheet takes from outside: a DWG/DXF, a picture, an SVG
IMPORT_SCALES = (1, 2, 5, 10, 20, 25, 50, 75, 100, 200, 500, 1000)     # a CAD drawing's (a detail's to a site plan's)
IMPORT_WIDTHS = (30, 50, 75, 100, 150, 200, 250, 300, 400)             # mm across: a picture's, an SVG's
IMAGE_EXTENSIONS = ("png", "jpg", "jpeg", "bmp", "gif", "tif", "tiff", "webp")


def import_kind(path):
    """(0.472) "cad" / "image" / "svg" for a file by its extension, or None."""
    ext = os.path.splitext(str(path))[1].lower().lstrip(".")
    if ext in ("dwg", "dxf"):
        return "cad"
    if ext == "svg":
        return "svg"
    return "image" if ext in IMAGE_EXTENSIONS else None


@dataclass
class SheetImport:
    """(0.472, the owner: «importação de desenhos em cad, dxf, imagem, svg») A drawing from outside put on a sheet: a
    DWG / DXF at a scale (1:`scale`, `units` metres a drawing unit), a picture or an SVG `width` mm across; its centre
    `at` (mm on the sheet). The file stays where it is (its path relative to the project too, as an image's)."""
    kind: str
    path: str
    name: str = ""
    at: tuple = (0.0, 0.0)
    width: float = 100.0
    scale: int = 50
    units: float = 0.001
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass
class Sheet:
    name: str
    paper: str = "A3"
    views: list = field(default_factory=list)
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)    # the same sheet after undo / redo (copies), saved
    number: str = ""               # its number in the title block ("" = its place among the sheets: 01, 02…)
    revisions: list = field(default_factory=list)   # (0.127) [{"code", "date", "text"}], oldest first
    sets: list = field(default_factory=list)        # (0.128) the sets it is in ("Licenciamento", "Execução"…)
    template: str = "full"                          # (0.129) its title block's template (TEMPLATES)
    portrait: bool = False                          # (0.470) its paper stood up
    imports: list = field(default_factory=list)     # (0.472) SheetImport: drawings from outside

    def size(self):
        return paper_size(self.paper, self.portrait)

    @property
    def kind(self):
        """(0.470) Its type, as Revit's title block types: its paper, how it stands, its title block's template."""
        return self.paper, bool(self.portrait), self.template


# (0.127) beside TITLE_FIELDS in the project's title block: its own fields ("extra": [[label, text]…], printed
# over the title block) and how sheets are numbered ("prefix" before the number, "digits" of it)
EXTRA_KEY = "extra"
NUMBERING_KEYS = ("prefix", "digits")
REVISION_ROW = 4.5             # mm: a row of the revisions' table / the project's own fields, over the title block


def number_of(sheets, sheet, fields=None):
    """The number a sheet shows: its own, else its place among the sheets ("01", "02"… — or as the project
    numbers them, 0.127: "A-01", "A-001"…)."""
    if sheet.number:
        return sheet.number
    k = next((k for k, s in enumerate(sheets) if s is sheet), None)
    if k is None:
        return ""
    fields = fields or {}
    digits = int(fields.get("digits") or 2)
    return "{}{:0{}d}".format(fields.get("prefix") or "", k + 1, max(1, min(digits, 4)))


def title_texts(fields, title, number="", project="", revisions=(), count=0):
    """What a title block shows ({field: text}): the project's fields (TITLE_FIELDS; `project`
    when the project's name is not given), the drawing's title and its number — and (0.127) the project's own
    fields ("extra": [(label, text)]) and the sheet's revisions ("revisions": [{code, date, text}]); (0.473) its last
    revision's code ("revision") and how many sheets there are ("count")."""
    out = {k: str(fields.get(k) or "").strip() for k in TITLE_FIELDS}
    out["project"] = out["project"] or project
    out["title"], out["number"] = title, number
    out[EXTRA_KEY] = [tuple(pair) for pair in fields.get(EXTRA_KEY) or ()]
    out["revisions"] = [dict(r) for r in revisions]
    out["revision"] = str(out["revisions"][-1].get("code") or "") if out["revisions"] else ""
    out["count"] = str(count) if count else ""
    use_company(fields.get(COMPANY_KEY))             # (0.472) the company's title block, drawn by «custom»
    return out


def read_title_fields(data):
    """The project's title block fields as saved ({field: text}, only the known ones): TITLE_FIELDS, its own
    fields (EXTRA_KEY: [[label, text]…], 0.127) and the numbering (NUMBERING_KEYS)."""
    if not isinstance(data, dict):
        return {}
    out = {k: str(v).strip() for k, v in data.items() if k in TITLE_FIELDS and isinstance(v, str) and v.strip()}
    extra = [[str(p[0]).strip(), str(p[1]).strip()] for p in data.get(EXTRA_KEY) or ()
             if isinstance(p, (list, tuple)) and len(p) == 2 and str(p[0]).strip()]
    if extra:
        out[EXTRA_KEY] = extra
    prefix = data.get("prefix")
    if isinstance(prefix, str) and prefix.strip():
        out["prefix"] = prefix.strip()
    try:
        digits = int(data.get("digits") or 2)
    except (TypeError, ValueError):
        digits = 2
    if digits != 2:
        out["digits"] = str(max(1, min(digits, 4)))
    company = clean_company(data.get(COMPANY_KEY))   # (0.472) the company's title block
    if company is not None:
        out[COMPANY_KEY] = company
    return out


def set_names(sheets):
    """The sheet sets there are (0.128): the names in any sheet's sets, in alphabetical order."""
    return sorted({name for s in sheets for name in s.sets}, key=str.lower)


def in_set(sheets, name):
    """The sheets of a set, in their order."""
    return [s for s in sheets if name in s.sets]


def clean_sets(names):
    out = []
    for name in names or ():
        name = str(name).strip()
        if name and name not in out:
            out.append(name)
    return out


def clean_revisions(revisions):
    """A sheet's revisions as typed or read: [{"code", "date", "text"}] with a code or a text."""
    out = []
    for r in revisions or ():
        if not isinstance(r, dict):
            continue
        row = {k: str(r.get(k) or "").strip() for k in ("code", "date", "text")}
        if row["code"] or row["text"]:
            out.append(row)
    return out


# (0.129) the title block's templates: "full" (the usual one, bottom right), "compact" (smaller, the essentials),
# "strip" (a column down the right side, its boxes at the bottom — more room for long drawings)
TEMPLATES = ("full", "compact", "strip")
STRIP_W = 50.0                 # mm: the strip's width
# the boxes: (x, y, w, h) mm from the block's top-left corner, what it shows, text size (points), bold
CELLS = {
    "full": ((0.0, 0.0, 120.0, 10.0, "project", 11, True), (0.0, 10.0, 70.0, 7.5, "client", 7, False),
             (70.0, 10.0, 50.0, 7.5, "site", 7, False), (0.0, 17.5, 70.0, 7.5, "author", 7, False),
             (70.0, 17.5, 50.0, 7.5, "stage", 7, False), (0.0, 25.0, 120.0, 8.0, "title", 9, True),
             (0.0, 33.0, 35.0, 7.0, "scale", 7, False), (35.0, 33.0, 35.0, 7.0, "date", 7, False),
             (70.0, 33.0, 50.0, 7.0, "number", 10, True)),
    "compact": ((0.0, 0.0, 100.0, 8.0, "project", 9, True), (0.0, 8.0, 100.0, 7.0, "title", 8, True),
                (0.0, 15.0, 33.0, 7.0, "scale", 7, False), (33.0, 15.0, 33.0, 7.0, "date", 7, False),
                (66.0, 15.0, 34.0, 7.0, "number", 9, True)),
    "strip": ((0.0, 0.0, 50.0, 12.0, "project", 9, True), (0.0, 12.0, 50.0, 8.0, "client", 7, False),
              (0.0, 20.0, 50.0, 8.0, "site", 7, False), (0.0, 28.0, 50.0, 8.0, "author", 7, False),
              (0.0, 36.0, 50.0, 8.0, "stage", 7, False), (0.0, 44.0, 50.0, 12.0, "title", 8, True),
              (0.0, 56.0, 25.0, 7.0, "scale", 7, False), (25.0, 56.0, 25.0, 7.0, "date", 7, False),
              (0.0, 63.0, 50.0, 9.0, "number", 10, True)),
}


# (0.472, the owner: «um botão editar o carimbo… de forma personalizada de acordo com a sua empresa») the company's own
# title block («custom»); (0.473, the owner: «se o carimbo pudesse abrir na tela e o utilizador usar as ferramentas de
# desenhos e inserir os campos… maior liberdade criativa») drawn by hand on the sheet itself, as Revit's title block
# family in its editor: lines, rectangles, texts, pictures (the logo) and fields — a field a box that shows one of each
# sheet's texts (the project, the drawing, its number, the scale, the date…). Each item's two points ("pts") are mm from
# the border's inside corner, bottom right (to the left and up: negative), so the title block keeps to that corner on
# any paper. What it takes from the corner is kept clear of the views — above it, or beside it when it goes up the side
# (a strip). The project keeps it (its title block's «company»), the suite's folder the office's (carimbo.json). 0.472's
# rows of boxes become such a drawing when read.
TEMPLATES = TEMPLATES + ("custom",)
COMPANY_KEY = "company"
ITEM_KINDS = ("line", "rect", "text", "field", "image")
FIELDS = ("project", "client", "site", "author", "stage", "title", "number", "scale", "date", "revision", "count")
EXTRA_FIELD = "extra:"                 # a field of the project's own: "extra:<its name>"
PENS = (0.13, 0.18, 0.25, 0.35, 0.5, 0.7, 1.0)                                      # mm
TEXT_SIZES = (4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 14.0, 18.0, 24.0)    # points
FILLS = ("", "#e6e6e6", "#b3b3b3", "#000000")
COLOURS = ("#000000", "#6b6b6b")
ALIGNS = ("left", "center", "right")
LABEL_SIZE = 4.5                       # points: the small grey name over a box's text («Obra», «Escala»…)
FAR = 2000.0                           # mm: no point further from the corner
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
# (0.472's boxes: what each showed — the company's logo, name and contacts besides the fields — and its rows; the
# program's company title block, a new project's when the office has none)
LEGACY_FIELDS = ("logo", "company", "contacts", "project", "client", "site", "author", "stage", "title", "scale",
                 "date", "number", "blank")
BIG = ("project", "title", "number", "company")      # (their text bold and larger)
DEFAULT_ROWS = {
    "name": "", "contacts": "", "logo": "", "width": 170.0,
    "rows": [{"h": 16.0, "cells": [["logo", 1.0], ["company", 2.0], ["contacts", 2.0]]},
             {"h": 10.0, "cells": [["project", 1.0]]},
             {"h": 7.5, "cells": [["client", 1.0], ["site", 1.0]]},
             {"h": 7.5, "cells": [["author", 1.0], ["stage", 1.0]]},
             {"h": 9.0, "cells": [["title", 1.0]]},
             {"h": 7.5, "cells": [["scale", 1.0], ["date", 1.0], ["number", 1.0]]}],
    "labels": {}}
_COMPANY = {"data": None}                             # the company title block in use (use_company)


def is_field(name):
    return name in FIELDS or (isinstance(name, str) and name.startswith(EXTRA_FIELD) and len(name) > len(EXTRA_FIELD))


def _point(p):
    x, y = float(p[0]), float(p[1])
    if not (math.isfinite(x) and math.isfinite(y)):
        raise ValueError(p)
    return [round(min(max(x, -FAR), FAR), 3), round(min(max(y, -FAR), FAR), 3)]


def clean_item(data):
    """(0.473) An item of a drawn title block as made or read, or None: {"kind", "pts": [[x, y], [x, y]]} and — a line
    or a rectangle — its "pen" (mm) and a rectangle's "fill" ("" or a colour); a text or a field its "size" (points),
    "bold", "align", "colour" and its "text" / "field"; a picture its file ("path")."""
    try:
        kind = data["kind"]
        if kind not in ITEM_KINDS or len(data["pts"]) != 2:
            return None
        item = {"kind": kind, "pts": [_point(p) for p in data["pts"]]}
        if kind in ("line", "rect"):
            item["pen"] = round(min(max(float(data.get("pen", 0.25)), 0.05), 3.0), 3)
            if kind == "rect":
                fill = str(data.get("fill") or "")
                item["fill"] = fill if _HEX.match(fill) else ""
        elif kind in ("text", "field"):
            item["size"] = round(min(max(float(data.get("size", 7.0)), 2.0), 72.0), 2)
            item["bold"] = bool(data.get("bold", False))
            item["align"] = data.get("align") if data.get("align") in ALIGNS else "left"
            colour = str(data.get("colour") or "#000000")
            item["colour"] = colour if _HEX.match(colour) else "#000000"
            if kind == "text":
                item["text"] = str(data.get("text") or "")
            else:
                if not is_field(data.get("field")):
                    return None
                item["field"] = str(data["field"])
        else:
            item["path"] = str(data.get("path") or "")
        return item
    except (KeyError, TypeError, ValueError, IndexError, AttributeError):
        return None


def clean_company(data):
    """The company's title block as drawn or read ({"items": [...]}), or None. (0.472's rows of boxes: turned into a
    drawing.)"""
    if not isinstance(data, dict):
        return None
    if isinstance(data.get("items"), (list, tuple)):
        return {"items": [i for i in (clean_item(d) for d in data["items"] if isinstance(d, dict)) if i is not None]}
    items = rows_to_items(data)
    return {"items": items} if items is not None else None


def rows_to_items(data):
    """(0.472's) rows of boxes — each row its height, each box what it shows and its share of the width — as a drawing
    (cells_to_items), the company's name, contacts and logo in it; None if there are none."""
    rows = []
    for row in data.get("rows") or ():
        try:
            h = min(max(float(row.get("h", 7.0)), 3.0), 80.0)
            cells = [[str(c[0]), min(max(float(c[1]), 0.1), 20.0)] for c in row.get("cells") or ()
                     if isinstance(c, (list, tuple)) and len(c) == 2 and str(c[0]) in LEGACY_FIELDS]
        except (TypeError, ValueError, AttributeError):
            continue
        if cells:
            rows.append((h, cells))
    if not rows:
        return None
    try:
        width = min(max(float(data.get("width", 170.0)), 40.0), 400.0)
    except (TypeError, ValueError):
        width = 170.0
    boxes, y = [], 0.0
    for h, cells in rows:
        total = sum(share for _f, share in cells) or 1.0
        x = 0.0
        for key, share in cells:
            w = width * share / total
            big = key in BIG
            boxes.append((round(x, 3), round(y, 3), round(w, 3), h, key, max(5, min(14, int(h * (0.95 if big else 0.8)))),
                          big))
            x += w
        y += h
    labels = {str(k): str(v).strip() for k, v in (data.get("labels") or {}).items() if str(v).strip()}
    return cells_to_items(boxes, labels, str(data.get("name") or "").strip(), str(data.get("contacts") or "").strip(),
                          str(data.get("logo") or ""))


def cells_to_items(cells, labels=None, name="", contacts="", logo=""):
    """(0.473) A template's boxes (CELLS': x, y, w, h mm from its top-left, what it shows, text size, bold) drawn as
    items from the corner: the outline, each box, its name small and grey at its top, its field under it — the
    company's name and contacts as texts, its logo as a picture."""
    from ..i18n import t
    labels = labels or {}
    bw = max(x + w for x, _y, w, _h, *_r in cells)
    bh = max(y + h for _x, y, _w, h, *_r in cells)

    def at(x, y):
        return [round(x - bw, 3), round(y - bh, 3)]
    items = [{"kind": "rect", "pts": [at(0.0, 0.0), at(bw, bh)], "pen": 0.35, "fill": ""}]
    label_h = LABEL_SIZE * 0.3528 * 1.3
    for x, y, w, h, key, size, bold in cells:
        items.append({"kind": "rect", "pts": [at(x, y), at(x + w, y + h)], "pen": 0.18, "fill": ""})
        if key == "blank":
            continue
        if key == "logo":
            items.append({"kind": "image", "pts": [at(x + 1.0, y + 1.0), at(x + w - 1.0, y + h - 1.0)], "path": logo})
            continue
        if key == "company":
            items.append({"kind": "text", "pts": [at(x + 1.5, y + 1.0), at(x + w - 1.5, y + h - 1.0)],
                          "text": name or t("tbe.company_name"), "size": float(min(size, 11)), "bold": True,
                          "align": "left", "colour": "#000000"})
            continue
        items.append({"kind": "text", "pts": [at(x + 1.2, y + 0.5), at(x + w - 1.2, y + 0.5 + label_h)],
                      "text": labels.get(key) or t("tb." + key), "size": LABEL_SIZE, "bold": False, "align": "left",
                      "colour": "#6b6b6b"})
        if key == "contacts":
            items.append({"kind": "text", "pts": [at(x + 1.2, y + 0.5 + label_h), at(x + w - 1.2, y + h - 0.5)],
                          "text": contacts or t("tbe.contacts"), "size": float(min(size, 6)), "bold": False,
                          "align": "left", "colour": "#000000"})
            continue
        items.append({"kind": "field", "pts": [at(x + 1.2, y + 0.5 + label_h), at(x + w - 1.2, y + h - 0.3)],
                      "field": key, "size": float(size), "bold": bool(bold), "align": "left", "colour": "#000000"})
    return [clean_item(i) for i in items]


TEMPLATE_STARTS = ("full", "compact", "strip", "company", "blank")    # (0.473) what the editor may start from


def template_items(template, inner_h=None):
    """(0.473) A template drawn as a company title block's items: "full", "compact", "strip" (its column's line up to
    the border's top, `inner_h` mm above the corner), "company" (the program's own) or "blank"."""
    if template == "blank":
        return []
    if template not in ("full", "compact", "strip"):
        return rows_to_items(DEFAULT_ROWS)
    cells = CELLS[template]
    items = cells_to_items(cells)
    if template == "strip" and inner_h:
        bh = max(y + h for _x, y, _w, h, *_r in cells)
        items.insert(1, clean_item({"kind": "line", "pts": [[-STRIP_W, -float(inner_h)], [-STRIP_W, -bh]],
                                    "pen": 0.35}))
    return items


def default_company():
    return {"items": template_items("company")}


def use_company(data):
    """The company title block the «custom» template draws (the project's; the program's when it has none)."""
    company = clean_company(data) or default_company()
    _COMPANY["data"] = company
    return company


def company():
    return _COMPANY["data"] or use_company(None)


def drawn_size(items):
    """(0.473) (w, h) mm a drawn title block takes from the corner (how far left and up it goes)."""
    xs = [p[0] for i in items for p in i["pts"]]
    ys = [p[1] for i in items for p in i["pts"]]
    if not xs:
        return 0.0, 0.0
    return max(0.0, -min(xs)), max(0.0, -min(ys))


def field_text(texts, field):
    """(0.473) What a field shows on a sheet (texts: title_texts', with the scale and the date)."""
    if field.startswith(EXTRA_FIELD):
        name = field[len(EXTRA_FIELD):]
        return next((str(v) for k, v in texts.get(EXTRA_KEY) or () if k == name), "")
    return str(texts.get(field) or "")


def cells_of(template):
    """The boxes of a title block template (none for «custom»: it is drawn, company())."""
    if template == "custom":
        return ()
    return CELLS.get(template, CELLS["full"])


def block_size(template):
    """(w, h) mm of a template's boxes (0.473: what the company's drawing takes)."""
    if template == "custom":
        return drawn_size(company()["items"])
    cells = cells_of(template)
    return max(x + w for x, _y, w, _h, *_r in cells), max(y + h for _x, y, _w, h, *_r in cells)


def title_box(size, template="full"):
    """(x, y, w, h) mm of a sheet's title block boxes on its paper (size: (w, h) mm): bottom right inside the
    border (the strip's at the bottom of its column)."""
    w, h = size
    bw, bh = block_size(template)
    return w - MARGIN - bw, h - MARGIN - bh, bw, bh


def block_beside(size, template="full"):
    """(0.473) Are the views beside the title block (it goes up the side, as the strip) rather than above it? For the
    company's drawing, whichever leaves them more room."""
    if template == "strip":
        return True
    if template != "custom":
        return False
    bw, bh = block_size(template)
    if not (bw and bh):
        return False
    iw, ih = size[0] - 2 * MARGIN - 8, size[1] - 2 * MARGIN - 8
    return max(iw - bw - 4, 0.0) * ih > iw * max(ih - bh - 4, 0.0)


def drawing_area(paper, template="full", portrait=False):
    """(left, top, width, height) in mm where views are laid out: inside the border, above the
    title block (0.129: beside the strip; 0.473: the company's drawing, above or beside it)."""
    w, h = paper_size(paper, portrait)
    if template == "strip":
        return MARGIN + 4, MARGIN + 4, w - 2 * MARGIN - STRIP_W - 12, h - 2 * MARGIN - 8
    bw, bh = block_size(template)
    if template == "custom" and not (bw and bh):
        return MARGIN + 4, MARGIN + 4, w - 2 * MARGIN - 8, h - 2 * MARGIN - 8
    if block_beside((w, h), template):
        return MARGIN + 4, MARGIN + 4, w - 2 * MARGIN - bw - 12, h - 2 * MARGIN - 8
    return MARGIN + 4, MARGIN + 4, w - 2 * MARGIN - 8, h - 2 * MARGIN - bh - 12


@dataclass
class Frame:
    """Where a view goes on the sheet: its scale, its drawing's centre (mm) and the frame
    it takes (drawing + label, mm) — for printing and for picking it with the mouse."""
    scale: int
    centre: tuple
    width: float
    height: float

    def rect(self):
        """(left, top, width, height) in mm: the drawing and its label below."""
        return (self.centre[0] - self.width / 2, self.centre[1] - (self.height - LABEL_H) / 2,
                self.width, self.height)

    def contains(self, x, y):
        left, top, w, h = self.rect()
        return left <= x <= left + w and top <= y <= top + h


def extent(drawing):
    """(w, h) in metres of what a drawing (model/drawings.Drawing) shows, None if nothing — a schedule's table
    (0.132): ("mm", w, h), its size on paper whatever the scale."""
    if drawing is not None and hasattr(drawing, "paper_size"):
        w, h = drawing.paper_size()
        return ("mm", float(w), float(h))
    box = drawing.bounds() if drawing is not None else None
    if box is None:
        return None
    lo, hi = box
    return float(hi[0] - lo[0]), float(hi[1] - lo[1])


def _size_at(extent, scale):
    """mm taken by a drawing `extent` (w, h) metres at 1:scale, label included (a table's: its own size)."""
    if extent[0] == "mm":
        return extent[1], extent[2] + LABEL_H
    return extent[0] * 1000.0 / scale, extent[1] * 1000.0 / scale + LABEL_H


def _shelves(sizes, width):
    """Rows of (index, w, h), left to right, a new row when one is full. Returns the rows and
    the size of the whole (w, h)."""
    rows, row, row_w = [], [], 0.0
    for k, (w, h) in sizes:
        if row and row_w + GAP + w > width:
            rows.append(row)
            row, row_w = [], 0.0
        row_w += (GAP if row else 0.0) + w
        row.append((k, w, h))
    if row:
        rows.append(row)
    total_w = max((sum(w for _k, w, _h in r) + GAP * (len(r) - 1) for r in rows), default=0.0)
    total_h = sum(max(h for _k, _w, h in r) for r in rows) + GAP * max(len(rows) - 1, 0)
    return rows, (total_w, total_h)


def layout(sheet, extents, defaults=None, extra_rows=0):
    """Frames for the sheet's views. extents: per view, the (w, h) in metres of its drawing, or
    None when there is nothing to draw (that view gets no frame: None). Views with a scale keep
    it (their own on the sheet, else `defaults[k]`: their view template's); the others get the
    largest usual scale at which all the views laid out fit (all of them the same, as an
    architect would). Views with a place keep it. (0.127) The rows over the title block — the
    sheet's revisions and the project's `extra_rows` own fields — are kept clear."""
    left, top, width, height = drawing_area(sheet.paper, sheet.template, getattr(sheet, "portrait", False))
    if not block_beside(sheet.size(), sheet.template):   # (in a strip, the rows are in its column)
        rows = (len(sheet.revisions) + 1 if sheet.revisions else 0) + int(extra_rows)
        height -= rows * REVISION_ROW
    fixed = [v.scale or (defaults[k] if defaults else None) for k, v in enumerate(sheet.views)]
    for k, v in enumerate(sheet.views):              # (0.234) its kind's usual scale, when it fits the sheet so
        usual = USUAL_SCALES.get(v.kind)
        if fixed[k] is None and usual and extents[k] is not None:
            w, h = _size_at(extents[k], usual)
            if w <= width and h <= height:
                fixed[k] = usual
    frames = [None] * len(sheet.views)
    free = [k for k, v in enumerate(sheet.views) if extents[k] is not None and v.at is None]
    chosen = SCALES[-1]
    for scale in SCALES:
        sizes = [(k, _size_at(extents[k], fixed[k] or scale)) for k in free]
        _rows, (w, h) = _shelves(sizes, width)
        if w <= width and h <= height:
            chosen = scale
            break
    rows, (_w, total_h) = _shelves([(k, _size_at(extents[k], fixed[k] or chosen)) for k in free], width)
    y = top + max(0.0, (height - total_h) / 2)
    for row in rows:
        row_w = sum(w for _k, w, _h in row) + GAP * (len(row) - 1)
        row_h = max(h for _k, _w, h in row)
        x = left + max(0.0, (width - row_w) / 2)
        for k, w, h in row:
            centre = (x + w / 2, y + (row_h - LABEL_H) / 2)
            frames[k] = Frame(fixed[k] or chosen, centre, w, h)
            x += w + GAP
        y += row_h + GAP
    for k, view in enumerate(sheet.views):
        if extents[k] is not None and view.at is not None:
            scale = fixed[k] or chosen
            w, h = _size_at(extents[k], scale)
            frames[k] = Frame(scale, tuple(view.at), w, h)
    return frames


def import_to_dict(item, base_dir=None):
    data = {"kind": item.kind, "path": item.path, "name": item.name, "at": [float(c) for c in item.at],
            "width": float(item.width), "scale": int(item.scale), "units": float(item.units), "uid": item.uid}
    if base_dir:
        try:
            data["relative"] = os.path.relpath(item.path, base_dir)
        except ValueError:                              # (another drive)
            pass
    return data


def import_from_dict(data, base_dir=None):
    """(0.472) A drawing put on a sheet, read back — its file looked for beside the project first (the folder may have
    moved), then where it was. None if it makes no sense."""
    try:
        path = str(data["path"])
        if base_dir and data.get("relative"):
            near = os.path.normpath(os.path.join(base_dir, str(data["relative"])))
            if os.path.exists(near) or not os.path.exists(path):
                path = near
        kind = str(data["kind"])
        if kind not in IMPORT_KINDS:
            return None
        item = SheetImport(kind, path, str(data.get("name") or os.path.basename(path)),
                           (float(data["at"][0]), float(data["at"][1])), float(data.get("width", 100.0)),
                           int(data.get("scale", 50)), float(data.get("units", 0.001)))
        if data.get("uid"):
            item.uid = str(data["uid"])
        return item
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def to_dict(sheet, base_dir=None):
    data = {"name": sheet.name, "paper": sheet.paper, "uid": sheet.uid,
            "views": [{"kind": v.kind, "ref": v.ref, "scale": v.scale,
                       "at": [float(c) for c in v.at] if v.at is not None else None} for v in sheet.views]}
    if sheet.imports:                                 # (0.472)
        data["imports"] = [import_to_dict(i, base_dir) for i in sheet.imports]
    if sheet.number:
        data["number"] = sheet.number
    if sheet.revisions:
        data["revisions"] = clean_revisions(sheet.revisions)
    if sheet.sets:
        data["sets"] = clean_sets(sheet.sets)
    if sheet.template != "full":
        data["template"] = sheet.template
    if sheet.portrait:                                # (0.470)
        data["portrait"] = True
    return data


def from_dict(data, base_dir=None):
    """A sheet read back from the .arqbim file (None if it makes no sense)."""
    try:
        views = []
        for v in data.get("views", ()):
            if v.get("kind") not in KINDS:
                continue
            scale = v.get("scale")
            at = v.get("at")
            views.append(Placed(str(v["kind"]), str(v["ref"]), int(scale) if scale else None,
                                (float(at[0]), float(at[1])) if at else None))
        paper = data.get("paper", "A3")
        number, uid = data.get("number"), data.get("uid")
        sheet = Sheet(str(data["name"]), paper if paper in PAPERS else "A3", views,
                      number=str(number) if isinstance(number, str) else "",
                      revisions=clean_revisions(data.get("revisions")), sets=clean_sets(data.get("sets")),
                      template=data.get("template") if data.get("template") in TEMPLATES else "full",
                      portrait=bool(data.get("portrait", False)))
        if isinstance(uid, str) and uid:
            sheet.uid = uid                          # (the same sheet when reopened: its tab finds it)
        sheet.imports = [i for i in (import_from_dict(d, base_dir) for d in data.get("imports") or ()
                                     if isinstance(d, dict)) if i is not None]       # (0.472)
        return sheet
    except (KeyError, TypeError, ValueError, IndexError, AttributeError):
        return None
