"""The MCP server's tools (0.268): few and general, their descriptions short and their answers short tables — what
an AI pays for in tokens is what it reads. An element is named by its number in the file ("#123": a few tokens,
not a 22-character GlobalId; a GlobalId is taken too). Lengths in metres, angles in degrees, plan points [x, y].

The work is done by the program's own commands (model/bim), so every change is the same as in the window: one undo
step, the walls joined, the IFC kept valid, the IFC data filled in."""

import os

import numpy as np

from ..ifc import catalog
from ..ifc.ifc_data import common_pset
from ..model import bim
from ..model.document import Document
from .protocol import ToolError

LIMIT = 40                  # rows a query gives when not told
MISSING_SHOWN = 8           # (0.274) properties a class's missing line names at most
SKIPPED_CLASSES = ("IfcOpeningElement", "IfcVirtualElement")
DEFAULT_TYPE = {"wall": "parede_alv_20", "walls": "parede_alv_20", "slab": "laje_15", "roof": "cobertura_15",
                "door": "porta_80", "window": "janela_120", "column": "pilar_20", "beam": "viga_20x40"}
BASE_FIELDS = ("id", "class", "name", "type", "storey")


def _n(v):
    """A number as short as it reads: 2.8, 0.15, 12."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return "" if v is None else str(v)
    text = "{:.3f}".format(float(v)).rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def _point(value, name, z=0.0):
    try:
        values = [float(v) for v in value]
    except (TypeError, ValueError):
        raise ToolError("{} must be [x, y]".format(name))
    if len(values) not in (2, 3):
        raise ToolError("{} must be [x, y]".format(name))
    return np.array(values + [z] if len(values) == 2 else values)


class Session:
    """The model the tools work on: a Document without a window."""

    def __init__(self, path=None):
        self.doc = Document()
        if path:
            self.doc.open(path)

    # ------------------------------------------------------------ names

    @property
    def ifc(self):
        return self.doc.ifc

    def element(self, ref):
        text = str(ref).strip()
        e = None
        if text.lstrip("#").isdigit():
            try:
                e = self.ifc.file.by_id(int(text.lstrip("#")))
            except RuntimeError:
                e = None
        else:
            e = self.ifc.by_guid(text)
        if e is None or not e.is_a("IfcRoot"):
            raise ToolError("no element {}".format(text))
        return e

    def guids(self, refs):
        if isinstance(refs, (str, int)):
            refs = [refs]
        if not refs:
            raise ToolError("ids needed")
        return [self.element(r).GlobalId for r in refs]

    def spec(self, kind, value):
        """A type by its key or name (catalogue and project's); none given: the kind's usual one."""
        value = value or DEFAULT_TYPE.get(kind)
        known = catalog.OPENING_BY_KEY if kind in ("door", "window") else catalog.BY_KEY
        found = known.get(value) or next((s for s in known.values()
                                          if str(value).lower() in (s.name_pt.lower(), s.name_en.lower())), None)
        if found is None:
            raise ToolError("no type {!r} (summary types=true lists them)".format(value))
        return found

    def storey(self, value):
        if value is None:
            return self.doc.active_storey
        for g, name, z in self.ifc.storeys():
            if str(value).lower() in (str(name).lower(), g.lower()) or _n(z) == str(value):
                return g
        raise ToolError("no storey {!r}".format(value))

    def level(self, storey):
        return next((z for g, _n2, z in self.ifc.storeys() if g == storey), 0.0)

    def ref(self, guid):
        e = self.ifc.by_guid(guid)
        return "#{}".format(e.id()) if e is not None else "?"

    # ------------------------------------------------------------ the file (the window's own, linked: 0.269)

    def new_model(self):
        self.doc = Document()

    def open_model(self, path):
        doc = Document()
        doc.open(path)
        self.doc = doc

    def save_model(self, path):
        self.doc.save(path)

    def show(self, guids):
        raise ToolError("only with the window linked (Ligação à IA)")


# ---------------------------------------------------------------- the tools

def summary(session, args):
    ifc = session.ifc
    lines = ["file: {}  units: m, °".format(session.doc.path or "(new, not saved)")]
    active = session.doc.active_storey
    lines.append("storeys: " + " | ".join("{} {}{}".format(name, _n(z), " (active)" if g == active else "")
                                         for g, name, z in ifc.storeys()))
    counts, types = {}, {}
    for e in ifc.file.by_type("IfcElement"):
        if e.is_a() in SKIPPED_CLASSES:
            continue
        counts[e.is_a()] = counts.get(e.is_a(), 0) + 1
        for rel in getattr(e, "IsTypedBy", None) or ():
            types[rel.RelatingType.Name] = types.get(rel.RelatingType.Name, 0) + 1
    lines.append("elements: " + (", ".join("{} {}".format(c, k) for c, k in sorted(counts.items())) or "none"))
    if types:
        lines.append("types used: " + "; ".join("{} ×{}".format(n, k) for n, k in sorted(types.items())))
    if args.get("types"):
        by_kind = {}
        for s in list(catalog.BY_KEY.values()) + list(catalog.OPENING_BY_KEY.values()):
            by_kind.setdefault(s.kind, []).append(s.key)
        lines += ["types {}: {}".format(k, " ".join(v)) for k, v in sorted(by_kind.items())]
    if args.get("missing"):                                 # (0.274) the IFC data still missing, by class
        for cls, pset, rows in ifc.missing_data():
            gaps = sorted(((p, len(w)) for p, w, _n in rows if w), key=lambda r: -r[1])
            total = rows[0][2] if rows else 0
            if gaps:
                shown = ", ".join("{} {}".format(p, k) for p, k in gaps[:MISSING_SHOWN])
                more = " +{} more".format(len(gaps) - MISSING_SHOWN) if len(gaps) > MISSING_SHOWN else ""
                lines.append("missing in {} of {} ({}): {}{}".format(cls, total, pset, shown, more))
    return "\n".join(lines)


def _value(session, e, field, info):
    """A field of an element for a table: its id, class, name, type, storey, a size (schedule info), an IFC
    standard property (IsExternal, FireRating…) or Pset.Property."""
    if field == "id":
        return "#{}".format(e.id())
    if field == "class":
        return e.is_a()
    if field in ("name", "type", "storey", "length", "height", "thickness", "width", "area", "projected"):
        return _n(info.get(field)) if field not in ("name", "type", "storey") else (info.get(field) or "")
    if field == "guid":
        return e.GlobalId
    if e.is_a("IfcTypeObject"):                            # (0.274) a type: its name, how many are of it
        if field == "name":
            return e.Name or ""
        if field == "count":
            return str(sum(len(rel.RelatedObjects) for rel in getattr(e, "Types", None) or ()))
    import ifcopenshell.util.element
    psets = ifcopenshell.util.element.get_psets(e)
    pset, _, prop = field.rpartition(".")
    pset = pset or common_pset(e.is_a()[:-4] if e.is_a("IfcTypeObject") and e.is_a().endswith("Type")
                               else e.is_a())
    value = psets.get(pset, {}).get(prop) if pset else None
    if isinstance(value, list):
        value = value[0] if value else None
    return _n(value) if not isinstance(value, bool) else ("true" if value else "false")


def query(session, args):
    ifc = session.ifc
    wanted = args.get("class")
    if wanted and not str(wanted).startswith("Ifc"):
        wanted = "Ifc" + str(wanted)[:1].upper() + str(wanted)[1:]
    storey = session.storey(args["storey"]) if args.get("storey") else None
    type_filter, text = (args.get("type") or "").lower(), (args.get("text") or "").lower()
    if wanted and wanted.endswith("Type"):                # (0.274) the types: their name, count, IFC data
        try:
            types = [e for e in ifc.file.by_type(wanted) if not text or text in (e.Name or "").lower()]
        except RuntimeError:
            raise ToolError("no class {}".format(wanted))
        fields = list(args.get("fields") or ("id", "name", "count"))
        offset, limit = int(args.get("offset") or 0), int(args.get("limit") or LIMIT)
        page = types[offset:offset + limit]
        rows = ["\t".join(fields)] + ["\t".join(_value(session, e, f, {}) for f in fields) for e in page]
        return "\n".join(rows) if page else "none"
    found = []
    for e in ifc.file.by_type("IfcElement"):
        if e.is_a() in SKIPPED_CLASSES or (wanted and not e.is_a(wanted)):
            continue
        if text and text not in (e.Name or "").lower():
            continue
        found.append(e)
    info = ifc.schedule_info([e.GlobalId for e in found])
    if storey is not None:
        name = next((n for g, n, _z in ifc.storeys() if g == storey), None)
        found = [e for e in found if (info.get(e.GlobalId) or {}).get("storey") == name]
    if type_filter:
        found = [e for e in found if type_filter in ((info.get(e.GlobalId) or {}).get("type") or "").lower()]
    fields = list(args.get("fields") or BASE_FIELDS)
    offset, limit = int(args.get("offset") or 0), int(args.get("limit") or LIMIT)
    page = found[offset:offset + limit]
    rows = ["\t".join(fields)]
    for e in page:
        rows.append("\t".join(_value(session, e, f, info.get(e.GlobalId) or {}) for f in fields))
    if len(found) > offset + len(page) or offset:
        rows.append("({}-{} of {})".format(offset + 1 if page else offset, offset + len(page), len(found)))
    return "\n".join(rows) if page else "none"


def get(session, args):
    import ifcopenshell.util.element
    e = session.element(args.get("id"))
    ifc = session.ifc
    guid = e.GlobalId
    info = ifc.schedule_info([guid]).get(guid) or {}
    head = '#{} {} "{}"'.format(e.id(), e.is_a(), e.Name or "")
    if info.get("type"):
        head += " type: " + info["type"]
    if info.get("storey"):
        head += " storey: " + info["storey"]
    lines = [head]
    sizes = ["{} {}".format(k, _n(info[k])) for k in ("length", "height", "thickness", "width", "area", "projected")
             if isinstance(info.get(k), (int, float))]
    if sizes:
        lines.append("sizes: " + " ".join(sizes))
    host = ifc.host_wall(guid) if e.is_a("IfcDoor") or e.is_a("IfcWindow") else None
    if host:
        lines.append("in wall: " + session.ref(host))
    if e.is_a("IfcTypeObject"):                             # (0.274) a type: how many are of it, its IFC data
        data = ifc.type_data(e)
        lines.append("elements of it: " + _value(session, e, "count", {}))
        if data is not None:
            set_ = ["{}={}".format(p, _n(v) if not isinstance(v, bool) else str(v).lower())
                    for p, _k, _c, v in data[1] if v is not None]
            lines.append("{}: {}".format(data[0], "; ".join(set_) or "-"))
            if args.get("full"):
                lines.append("  not set: " + " ".join(p for p, _k, _c, v in data[1] if v is None))
        return "\n".join(lines)
    standard = ifc.ifc_data(guid)
    if standard is not None:
        name, rows = standard
        set_ = ["{}={}".format(p, _n(v) if not isinstance(v, bool) else str(v).lower())
                for p, _k, _c, v, _h in rows if v is not None]
        empty = [p for p, _k, _c, v, _h in rows if v is None]
        lines.append("{}: {}".format(name, "; ".join(set_) or "-"))
        if args.get("full"):
            lines.append("  not set: " + " ".join(empty))
    if args.get("full"):
        for pset, props in sorted(ifcopenshell.util.element.get_psets(e).items()):
            if pset in ("ArqSynth_Parametros", "ArqBIM_Parametros") or (standard and pset == standard[0]):
                continue
            values = ["{}={}".format(k, _n(v)) for k, v in props.items() if k != "id" and not isinstance(v, dict)]
            lines.append("{}: {}".format(pset, "; ".join(values)))
    return "\n".join(lines)


def create(session, args):
    kind = args.get("kind")
    p = args.get("params") or {}
    doc = session.doc
    storey = session.storey(p.get("storey"))
    z = session.level(storey)
    if kind == "wall":
        guid = bim.add_wall(doc, _point(p.get("a"), "a", z), _point(p.get("b"), "b", z), session.spec(kind, p.get("type")),
                            height=float(p.get("height") or bim.WALL_HEIGHT), storey=storey)
        made = [guid]
    elif kind == "walls":
        points = [_point(q, "points", z) for q in p.get("points") or ()]
        if len(points) < 2:
            raise ToolError("points: two at least")
        made = bim.add_wall_loop(doc, points, session.spec(kind, p.get("type")),
                                 height=float(p.get("height") or bim.WALL_HEIGHT), storey=storey,
                                 closed=bool(p.get("closed", True)))
    elif kind == "slab":
        outline = [tuple(_point(q, "outline")[:2]) for q in p.get("outline") or ()]
        if len(outline) < 3:
            raise ToolError("outline: three points at least")
        made = [bim.add_slab_outline(doc, outline, float(p.get("z", z)), session.spec(kind, p.get("type")),
                                     storey=storey)]
        if p.get("heights"):                      # (0.433) each corner's height over its top (m): its slope
            bim.set_slab_heights(doc, made[0], [float(v) for v in p["heights"]])
    elif kind == "roof":
        outline = [tuple(_point(q, "outline")[:2]) for q in p.get("outline") or ()]
        if len(outline) < 3:
            raise ToolError("outline: three points at least (the walls' outer line)")
        made = [bim.add_roof(doc, outline, session.spec(kind, p.get("type")), p.get("form") or "hip",
                             float(p.get("slope", 30.0)), float(p.get("overhang", 0.5)), storey=storey)]
    elif kind in ("door", "window"):
        wall = session.element(p.get("wall")).GlobalId
        frame = bim.wall_frame(doc, wall)
        if frame is None:
            raise ToolError("wall: not a wall of this program")
        made = [bim.add_opening(doc, wall, session.spec(kind, p.get("type")), frame, float(p.get("at", 0.5)),
                                -1 if p.get("side", -1) in (-1, "-1", None) else 1)]
    elif kind == "column":
        made = [bim.add_column(doc, _point(p.get("at"), "at", z), session.spec(kind, p.get("type")),
                               height=float(p.get("height") or bim.WALL_HEIGHT), storey=storey)]
    elif kind == "beam":
        made = [bim.add_beam(doc, _point(p.get("a"), "a", z), _point(p.get("b"), "b", z),
                             session.spec(kind, p.get("type")), float(p.get("top", z + bim.WALL_HEIGHT)),
                             storey=storey)]
    elif kind == "room":
        guid = bim.add_room(doc, tuple(_point(p.get("at"), "at")[:2]), p.get("name"), storey=storey)
        if guid is None:
            raise ToolError("no room there: the walls do not close round that point")
        made = [guid]
    elif kind == "storey":
        made = [bim.add_storey(doc, str(p.get("name") or "Piso"), float(p.get("z", 0.0)))]
    else:
        raise ToolError("kind: wall walls slab roof door window column beam room storey")
    made = [g for g in made if g]
    names = ['{} "{}"'.format(session.ref(g), session.ifc.by_guid(g).Name or "") for g in made]
    return "created " + ", ".join(names)


def edit(session, args):
    doc = session.doc
    guids = session.guids(args.get("ids"))
    changes = args.get("set") or {}
    done = []
    for key, value in changes.items():
        if key == "name":
            for g in guids:
                bim.rename(doc, g, str(value))
        elif key == "type":
            for g in guids:
                kind = doc.ifc.kind_of(g)
                bim.set_type(doc, g, session.spec(kind, value))
        elif key == "height":
            for g in guids:
                kind = doc.ifc.kind_of(g)
                if kind == "wall":
                    bim.resize_wall(doc, g, height=float(value))
                elif kind == "column":
                    bim.resize_column(doc, g, float(value))
                else:
                    raise ToolError("height: walls and columns")
        else:
            pset, _, prop = key.rpartition(".")
            for g in guids:
                if doc.ifc.by_guid(g).is_a("IfcTypeObject"):          # (0.274) a type: all its elements have it
                    bim.set_type_entity_property(doc, g, prop, value, pset or None)
                    continue
                name = pset or common_pset(doc.ifc.by_guid(g).is_a())
                if not name:
                    raise ToolError("{}: give it as Pset_….{}".format(key, key))
                bim.set_property(doc, g, name, prop, value)
        done.append(key)
    move = args.get("move")
    if move is not None:
        d = [float(v) for v in move] + [0.0] * (3 - len(move))
        m = np.eye(4)
        m[:3, 3] = d[:3]
        bim.transform_objects(doc, guids, m, "MCP")
        done.append("move")
    if not done:
        raise ToolError("nothing to do: give set or move")
    return "ok: {} on {} element(s)".format(", ".join(done), len(guids))


def delete(session, args):
    guids = session.guids(args.get("ids"))
    bim.delete(session.doc, guids)
    return "deleted {}".format(len(guids))


def undo(session, args):
    steps = max(1, int(args.get("steps") or 1))
    labels = []
    for _ in range(steps):
        cmd = session.doc.undo()
        if cmd is None:
            break
        labels.append(getattr(cmd, "label", "?"))
    return "undone: " + (", ".join(labels) if labels else "nothing")


def file_(session, args):
    action = args.get("action")
    path = args.get("path")
    if action == "new":
        session.new_model()
        return "new model"
    if action == "open":
        if not path or not os.path.exists(path):
            raise ToolError("no file {!r}".format(path))
        session.open_model(path)
        return "opened {}".format(path)
    if action == "save":
        path = path or session.doc.path
        if not path:
            raise ToolError("path needed (the model was never saved)")
        session.save_model(path)
        return "saved {}".format(path)
    raise ToolError("action: new open save")


def show(session, args):
    """(0.269) The elements selected in the window and the view brought to them."""
    guids = session.guids(args.get("ids"))
    session.show(guids)
    return "shown {}".format(len(guids))


# ---------------------------------------------------------------- how they are offered

def _schema(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required)}


_IDS = {"type": "array", "items": {"type": ["string", "integer"]}, "description": "#n or GlobalId"}
INSTRUCTIONS = ("ArqSynth BIM model (IFC4). Metres, degrees, plan points [x,y]. Elements are #n. Start with "
                "summary; query with fields and limit; changes are undoable.")


def tools(session):
    """[(name, description, input schema, handler, read only)] for protocol.Server: each tool run on `session`."""
    return [(name, description, schema, (lambda args, fn=fn: fn(session, args)), read_only)
            for name, description, schema, fn, read_only in definitions()]


def linked_tools():
    """(0.269) The same tools — and show — each sent to the window linked (link.call; the link read at every call:
    the window may be opened, or its link turned on, after the server started)."""
    from . import link

    def send(name):
        def handler(args):
            found = link.read()
            if found is None:
                raise ToolError("ArqSynth BIM is not open with «Ligação à IA» on (Gerenciar tab)")
            try:
                text, error = link.call(found, name, args)
            except (OSError, ConnectionError) as exc:
                raise ToolError("the window does not answer ({}): is ArqSynth BIM open, «Ligação à IA» on?"
                                .format(exc))
            if error:
                raise ToolError(text[len("error: "):] if text.startswith("error: ") else text)
            return text
        return handler
    return [(name, description, schema, send(name), read_only)
            for name, description, schema, _fn, read_only in definitions(live=True)]


def run(session, name, args):
    """(0.269) One tool run on a session by its name — what the window does for an MCP server linked to it."""
    found = next((fn for n, _d, _s, fn, _r in definitions(live=True) if n == name), None)
    if found is None:
        raise ToolError("unknown tool: {}".format(name))
    return found(session, args or {})


def definitions(live=False):
    """[(name, description, input schema, fn(session, args) -> text, read only)]; live: show too (the window's)."""
    extra = [("show", "Select elements in the user's window and bring the view to them.", _schema({"ids": _IDS},
                                                                                                   ["ids"]),
              show, True)] if live else []
    return extra + [
        ("summary", "The model in a few lines: storeys, elements per class, types used. types=true: the type keys; "
                    "missing=true: IFC data still missing, by class.",
         _schema({"types": {"type": "boolean"}, "missing": {"type": "boolean"}}), summary, True),
        ("query", "Elements as a table. Filters: class (IfcWall or wall; IfcWallType: the types, with count), storey, "
                  "type, text (in the name). fields: id class name type storey length height thickness width area "
                  "guid, a standard property (IsExternal, FireRating…) or Pset_X.Prop. limit (40), offset.",
         _schema({"class": {"type": "string"}, "storey": {"type": "string"}, "type": {"type": "string"},
                  "text": {"type": "string"}, "fields": {"type": "array", "items": {"type": "string"}},
                  "limit": {"type": "integer"}, "offset": {"type": "integer"}}), query, True),
        ("get", "One element: class, name, type, storey, sizes, its standard IFC properties set. full=true: the empty "
                "ones and every other property set.",
         _schema({"id": {"type": ["string", "integer"]}, "full": {"type": "boolean"}}, ["id"]), get, True),
        ("create", "Make an element. kind + params: wall{a,b,type?,height?} walls{points,closed?} slab{outline,z?,heights?} "
                   "roof{outline,form?(hip gable shed flat),slope?,overhang?} door|window{wall,at(m from its start)} "
                   "column{at,height?} beam{a,b,top} room{at,name?} storey{name,z}; type?, storey? in any.",
         _schema({"kind": {"type": "string"}, "params": {"type": "object"}}, ["kind", "params"]), create, False),
        ("edit", "Change elements: set {name|type|height|IsExternal|FireRating|Pset_X.Prop: value (null clears)}, "
                 "move [dx,dy,dz]. A type's id: its property for all its elements.",
         _schema({"ids": _IDS, "set": {"type": "object"}, "move": {"type": "array", "items": {"type": "number"}}},
                 ["ids"]), edit, False),
        ("delete", "Delete elements (a wall takes its doors and windows).", _schema({"ids": _IDS}, ["ids"]),
         delete, False),
        ("undo", "Undo the last changes (steps, default 1).", _schema({"steps": {"type": "integer"}}), undo,
         False),
        ("file", "action new|open|save; path (save: the same file if none).",
         _schema({"action": {"type": "string"}, "path": {"type": "string"}}, ["action"]), file_, False),
    ]
