"""(0.543) The Visual Graph for the AI (PLANO.md, «Gráfico Visual», step 6): four tools, short answers — the nodes'
list (from the same registry as the window's palette), the graph built and changed, worked out (each node's verdict,
the fabrication report and a picture to look at), and applied to the model's walls.

Node ids are n1, n2…; measures in metres (angles in degrees) as in the window."""

import os
import tempfile

from ..core.graph import REGISTRY, Graph, GraphError, nodes_3d, templates
from .protocol import ToolError


def _editor(session):
    """(0.544) The Visual Graph's window, open in the program the AI is linked to — or None."""
    win = getattr(getattr(session, "window", None), "graph_window", None)
    try:
        return win if win is not None and win.isVisible() else None
    except RuntimeError:                               # (closed and gone)
        return None


def _graph(session):
    """The graph the tools work on: the open editor's (the user sees each change) — else the session's own."""
    win = _editor(session)
    if win is not None:
        return win.graph
    g = getattr(session, "graph", None)
    if g is None:
        g = session.graph = templates.atrator_hexagono()
    return g


def _put(session, g):
    win = _editor(session)
    if win is not None:
        win.replace_graph(g)
        return win.graph
    session.graph = g
    return g


def _changed(session):
    win = _editor(session)
    if win is not None:
        win.graph_changed()


def _v(x):
    if isinstance(x, float):
        return "{:.4f}".format(x).rstrip("0").rstrip(".")
    return str(x)


def _port(p):
    if p.kind in ("number", "int"):
        return "{}={}[{}..{}]".format(p.name, _v(p.default), _v(p.min), _v(p.max))
    if p.kind == "choice":
        return "{}={}({})".format(p.name, p.default, "|".join(p.choices))
    return "{}={}:{}".format(p.name, _v(p.default) if p.default not in (None, "") else "''", p.kind)


def nodes(session, args):
    """The nodes, one line each (or one in full: key)."""
    key = args.get("key")
    if key:
        try:
            s = REGISTRY.get(key)
        except KeyError as e:
            raise ToolError(str(e))
        return "\n".join([
            "{} ({}): {}".format(s.key, s.family, s.description),
            "in: " + (", ".join("{}:{}{}".format(p.name, p.kind, "?" if p.optional else "") for p in s.inputs) or "-"),
            "out: " + (", ".join("{}:{}".format(p.name, p.kind) for p in s.outputs) or "-"),
            "params: " + (" ".join(_port(p) for p in s.params) or "-"),
            "e.g. " + s.example if s.example else ""]).strip()
    lines = ["key family in>out"]
    for c in REGISTRY.catalog():
        lines.append("{} {} {}>{}".format(c["key"], c["family"], ",".join(i["name"] for i in c["inputs"]) or "-",
                                          ",".join(o["name"] for o in c["outputs"]) or "-"))
    lines.append("templates: " + " ".join(templates.TEMPLATES))
    return "\n".join(lines)


def describe(g):
    """The graph in a few lines: each node with its changed measures, then the links."""
    out = []
    for nid, n in g.nodes.items():
        spec = g.registry.get(n["type"])
        changed = {k: v for k, v in n["params"].items() if v != spec.defaults().get(k)}
        out.append("{} {}{}".format(nid, n["type"], " " + " ".join("{}={}".format(k, _v(v)) for k, v in
                                                                      changed.items()) if changed else ""))
    out += ["{}.{}>{}.{}".format(*link) for link in g.links]
    return "\n".join(out) or "(empty)"


def graph(session, args):
    """Build or change the graph: action new|template|add|connect|disconnect|set|remove|load|save|show."""
    g = _graph(session)
    a = args.get("action") or "show"
    try:
        win = _editor(session)
        if win is not None and a in ("add", "connect", "disconnect", "set", "remove"):
            win.remember()                             # (one step of the editor's Ctrl+Z)
        if a == "new":
            g = _put(session, Graph())
        elif a == "template":
            key = args.get("key")
            if key not in templates.TEMPLATES:
                raise ToolError("templates: " + " ".join(templates.TEMPLATES))
            kw = {"ficheiro": args["file"]} if key == "imagem_painel" and args.get("file") else {}
            g = _put(session, templates.make(key, **kw))
        elif a == "add":
            nid = g.add_node(args["type"], args.get("params") or {},
                             pos=(80.0 * len(g.nodes), 40.0 * (len(g.nodes) % 4)))
            _changed(session)
            return "added " + nid
        elif a == "connect":                       # from "n1.painel" to "n2.painel"
            f, o = str(args["from"]).split(".", 1)
            t, i = str(args["to"]).split(".", 1)
            g.connect(f, o, t, i)
        elif a == "disconnect":
            t, i = str(args["to"]).split(".", 1)
            g.disconnect(t, i)
        elif a == "set":
            nid = args["id"]
            for k, v in (args.get("params") or {}).items():
                g.set_param(nid, k, v)
        elif a == "remove":
            g.remove_node(args["id"])
        elif a == "load":
            with open(args["path"], encoding="utf-8") as fh:
                g = _put(session, Graph.from_json(fh.read()))
        elif a == "save":
            with open(args["path"], "w", encoding="utf-8") as fh:
                fh.write(g.to_json())
            return "saved " + args["path"]
        elif a != "show":
            raise ToolError("action: new template add connect disconnect set remove load save show")
    except (GraphError, KeyError, ValueError) as e:
        raise ToolError(str(e).strip("'\""))
    if a in ("connect", "disconnect", "set", "remove"):
        _changed(session)
    return describe(g)


def _report(g, results):
    lines = []
    for nid in g.nodes:
        if nid in g.errors:
            lines.append("{} ! {}".format(nid, g.errors[nid]))
            continue
        out = results.get(nid) or {}
        if "relatorio" in out:
            r = out["relatorio"]
            bridge = "" if r["min_bridge"] is None else " bridge_min={}mm".format(_v(r["min_bridge"] * 1000))
            lines.append("{} {} holes={} bad={} open={}%{}{}".format(
                nid, "OK" if r["ok"] else "FIX", r["holes"], r["bad"], _v(round(r["open_area"] * 100, 1)), bridge,
                (" | " + "; ".join(r["problems"])) if r["problems"] else ""))
        elif "furos" in out and g.nodes[nid]["type"] == "perfurar":
            d = out["furos"]["d"]
            lines.append("{} holes={} d={}..{}mm".format(nid, len(d), _v(float(d.min()) * 1000) if len(d) else 0,
                                                         _v(float(d.max()) * 1000) if len(d) else 0))
        elif "ficheiro" in out:
            lines.append("{} wrote {}".format(nid, out["ficheiro"]))
    return lines


def _picture(g, results, nid, path):
    """A PNG of a node's result (the last check, else the last node with a picture)."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6 import QtGui
    if QtGui.QGuiApplication.instance() is None:
        session_app = QtGui.QGuiApplication([])          # noqa: F841  (fonts for the report's words)
        _picture.app = session_app
    from ..ui import visual_graph as vg
    spec = g.registry.get(g.nodes[nid]["type"])
    port = spec.outputs[0]
    img = vg.picture(port.kind, results[nid].get(port.name), 900, 520, vg.domain_of(results, g))
    img.save(path)
    return path


def evaluate(session, args):
    """Work the graph out: one line per node that says something, and a picture (PNG) of a node's result."""
    g = _graph(session)
    nodes_3d.MODEL["doc"] = session.doc
    try:
        results = g.evaluate()
    except GraphError as e:
        raise ToolError(str(e))
    finally:
        nodes_3d.MODEL["doc"] = None
    lines = _report(g, results) or ["ok, nothing to say"]
    if args.get("picture", True):
        nid = args.get("id")
        if not nid:
            shown = [n for n in g.nodes if n in results and g.registry.get(g.nodes[n]["type"]).outputs and
                     g.registry.get(g.nodes[n]["type"]).outputs[0].kind in ("holes", "mesh")]
            nid = shown[-1] if shown else None
        if nid in results:
            path = args.get("path") or os.path.join(tempfile.gettempdir(), "arqsynth_grafo_{}.png".format(nid))
            lines.append("picture " + _picture(g, results, nid, path))
            return {"text": "\n".join(lines), "png": path}
    return "\n".join(lines)


def apply(session, args):
    """Every «aplicar_parede» node as a perforated finish on its wall (wall: #n or GlobalId, else the node's)."""
    from ..core.graph.nodes_panels import cladding_pattern
    from ..model import bim
    g = _graph(session)
    nodes_3d.MODEL["doc"] = session.doc
    try:
        results = g.evaluate()
    finally:
        nodes_3d.MODEL["doc"] = None
    made = []
    for nid, n in g.nodes.items():
        if n["type"] != "aplicar_parede":
            continue
        out = (results.get(nid) or {}).get("bim")
        if out is None:
            raise ToolError("{}: {}".format(nid, g.errors.get(nid, "not worked out")))
        wall = session.element(args["wall"]).GlobalId if args.get("wall") else out["wall"]
        if not wall:
            raise ToolError("wall needed (#n)")
        guid = bim.add_cladding(session.doc, wall, 1 if out["side"] == "frente" else -1, "perfurado", 0.0,
                                cladding_pattern(out))
        e = session.ifc.by_guid(guid)
        made.append("#{} holes={}".format(e.id(), session.ifc.pattern_params(guid)["count"]))
    if not made:
        raise ToolError("no aplicar_parede node")
    return "made " + ", ".join(made)


def definitions(schema):
    """[(name, description, input schema, fn, read only)] — joined to the model's tools."""
    s, str_, obj = schema, {"type": "string"}, {"type": "object"}
    return [
        ("graph_nodes", "Perforated-panel node types; key: one in full.", s({"key": str_}), nodes, True),
        ("graph", "Node graph: action new|template{key,file?}|add{type,params?}|connect{from:'n1.out',to:'n2.in'}|"
                  "disconnect{to}|set{id,params}|remove{id}|load|save{path}|show.",
         s({"action": str_, "key": str_, "file": str_, "type": str_, "params": obj, "from": str_, "to": str_,
            "id": str_, "path": str_}, ["action"]), graph, False),
        ("graph_eval", "Work the graph out: problems, fabrication check, a picture (id?).",
         s({"id": str_, "picture": {"type": "boolean"}, "path": str_}), evaluate, True),
        ("graph_apply", "Graph's panels onto a wall (#n) as perforated finish.",
         s({"wall": {"type": ["string", "integer"]}}), apply, False),
    ]
