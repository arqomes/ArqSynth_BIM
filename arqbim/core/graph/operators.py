"""(0.541, the owner: «O aplicativo deve poder guardar os operadores que ficam no painel esquerdo para ser aplicado
noutros projetos») The library of operators: each a Visual Graph with a name, kept in the suite's folder
(`<suite>/operadores/<slug>.json`, its thumbnail `<slug>.png` beside it) — outside any project, so every project
(and every program of the suite) finds them.

An operator works on «the surface it is applied to»: `retarget` points its «Superfície do modelo» and «Aplicar à
parede/fachada» nodes at the wall and face chosen. A graph on a «Painel plano» is a module: it repeats along the
wall."""

import json
import os
import re
import shutil
import unicodedata

from .graph import Graph, GraphError

FORMAT = "arqsynth-operador"
VERSION = 1
FOLDER = "operadores"
SEEDED = ".de_origem"
_seeding = False
SIDES = ("frente", "trás")


def folder():
    from arqsynth_templates.paths import suite_dir
    return os.path.join(suite_dir(), FOLDER)


def slug_of(name):
    text = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "operador"


def _path(slug, ext=".json"):
    return os.path.join(folder(), slug + ext)


def thumbnail_path(slug):
    return _path(slug, ".png")


def _free_slug(name):
    base, slug, k = slug_of(name), slug_of(name), 2
    while os.path.exists(_path(slug)):
        slug, k = "{}_{}".format(base, k), k + 1
    return slug


def listing():
    """[{"slug", "name", "about", "thumbnail" (its path, or "")}], by name. The library seeded the first time."""
    seed()
    out = []
    try:
        names = sorted(os.listdir(folder()))
    except OSError:
        return out
    for file in names:
        if not file.endswith(".json"):
            continue
        slug = file[:-5]
        try:
            with open(_path(slug), encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or data.get("format") != FORMAT:
            continue
        png = thumbnail_path(slug)
        out.append({"slug": slug, "name": str(data.get("name") or slug), "about": str(data.get("about") or ""),
                    "thumbnail": png if os.path.exists(png) else ""})
    return sorted(out, key=lambda d: d["name"].lower())


def _read(slug):
    try:
        with open(_path(slug), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise GraphError("não foi possível ler o operador: {}".format(e)) from None
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        raise GraphError("não é um operador do ArqSynth")
    if data.get("version", 0) > VERSION:
        raise GraphError("operador feito por uma versão mais nova do ArqSynth")
    return data


def load(slug):
    """(name, about, Graph) of an operator. GraphError where it cannot be read."""
    data = _read(slug)
    return str(data.get("name") or slug), str(data.get("about") or ""), Graph.from_dict(data["graph"])


def clean_exposed(graph, exposed):
    """[(node id, measure)] of those that are in the graph and can stand in the side panel (numbers, ticks,
    choices), in order, each once."""
    out = []
    for pair in exposed or ():
        try:
            nid, name = str(pair[0]), str(pair[1])
            port = graph.registry.get(graph.nodes[nid]["type"]).port("params", name)
        except (KeyError, IndexError, TypeError):
            continue
        if port.kind in ("number", "int", "bool", "choice") and (nid, name) not in out:
            out.append((nid, name))
    return out


def exposed_of(slug):
    """(0.543) (graph, [(node id, measure)]) of an operator: the measures its maker put in sight, changed in the
    side panel without opening the editor."""
    data = _read(slug)
    graph = Graph.from_dict(data["graph"])
    return graph, clean_exposed(graph, data.get("exposed"))


def save(name, graph, slug=None, about="", png=None, exposed=None):
    """An operator kept in the library (a new one: its file named after it; `slug`: that one written over).
    `png`: its thumbnail's bytes. The walls it was drawn on are not kept: it serves any. (0.543) `exposed`:
    [(node id, measure)] in sight in the side panel (None: those it had, written over). Returns its slug."""
    name = str(name).strip()
    if not name:
        raise GraphError("dê um nome ao operador")
    seed()
    if exposed is None and slug and os.path.exists(_path(slug)):
        try:
            exposed = _read(slug).get("exposed")
        except GraphError:
            exposed = None
    slug = slug or _free_slug(name)
    data = _portable(graph)
    with open(_path(slug), "w", encoding="utf-8") as f:
        json.dump({"format": FORMAT, "version": VERSION, "name": name, "about": about, "graph": data,
                   "exposed": [list(p) for p in clean_exposed(graph, exposed)]}, f, ensure_ascii=False, indent=1)
    if png:
        with open(thumbnail_path(slug), "wb") as f:
            f.write(png)
    return slug


def _portable(graph):
    """The graph's data without the walls it was pointed at."""
    data = graph.to_dict()
    for node in data["nodes"]:
        if node["type"] in ("fachada_bim", "aplicar_parede"):
            node["params"] = dict(node["params"], parede="")
    return data


def delete(slug):
    for ext in (".json", ".png"):
        try:
            os.remove(_path(slug, ext))
        except OSError:
            pass


def duplicate(slug):
    name, about, graph = load(slug)
    new = save(name + " (cópia)", graph, about=about, exposed=exposed_of(slug)[1])
    if os.path.exists(thumbnail_path(slug)):
        shutil.copyfile(thumbnail_path(slug), thumbnail_path(new))
    return new


def rename(slug, name):
    _old, about, graph = load(slug)
    return save(name, graph, slug=slug, about=about)


def export_to(slug, path):
    shutil.copyfile(_path(slug), path)


def import_from(path):
    """An operator's file (or a plain graph's) brought into the library. Returns its slug."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise GraphError("não foi possível ler o ficheiro: {}".format(e)) from None
    if isinstance(data, dict) and data.get("format") == FORMAT:
        return save(data.get("name") or os.path.splitext(os.path.basename(path))[0], Graph.from_dict(data["graph"]),
                    about=str(data.get("about") or ""), exposed=data.get("exposed"))
    return save(os.path.splitext(os.path.basename(path))[0], Graph.from_dict(data))


def seed():
    """The program's ready graphs put in the library the first time (the folder not there yet): something to apply
    at once, and to open and learn from."""
    global _seeding
    if _seeding:
        return
    from . import templates
    mark = os.path.join(folder(), SEEDED)
    try:
        with open(mark, encoding="utf-8") as f:
            done = set(f.read().split())
    except OSError:
        done = set()
    if "ArqSynth" in done:                                 # (0.541's mark: its four were put then)
        done |= {"atrator_hexagono", "voronoi_centro", "gradiente_grelha", "ruido_folhagem"}
    new = [k for k in templates.TEMPLATES if k not in done and k != "imagem_painel"]   # (that one asks a picture)
    if not new:
        return
    os.makedirs(folder(), exist_ok=True)
    with open(mark, "w", encoding="utf-8") as f:           # (each once: one the owner deletes does not come back;
        f.write("\n".join(sorted(done | set(new))) + "\n")  # a later version's new ones are added)
    _seeding = True
    try:
        for key in new:
            name, about, maker = templates.TEMPLATES[key]
            save(name, maker(), about=about)
    finally:
        _seeding = False


# ------------------------------------------------------------------ on a surface
def starter():
    """«Criar novo»: the surface chosen, holes in a favo growing towards a point, checked, on the wall."""
    g = Graph()
    s = g.add_node("fachada_bim", pos=(0, 0))
    h = g.add_node("hexagono", {"passo": 0.08}, pos=(260, -40))
    a = g.add_node("atrator", {"x": 1.0, "y": 1.2, "raio": 2.0}, pos=(260, 260))
    f = g.add_node("perfurar", {"d_min": 0.008, "d_max": 0.06}, pos=(520, 60))
    c = g.add_node("verificar_fabrico", pos=(780, 60))
    b = g.add_node("aplicar_parede", {"repetir": False}, pos=(1040, 60))
    for link in ((s, "painel", h, "painel"), (h, "pontos", f, "pontos"), (a, "campo", f, "campo"),
                 (f, "furos", c, "furos"), (c, "furos", b, "furos")):
        g.connect(*link)
    return g


def retarget(graph, wall, side="frente"):
    """The graph pointed at a wall's face: its «Superfície do modelo» nodes take that wall, its «Aplicar» nodes that
    wall and side — those fed by the surface itself cover it whole (not repeated board by board)."""
    whole = set()
    for nid, node in graph.nodes.items():
        if node["type"] == "fachada_bim":
            graph.set_param(nid, "parede", wall or "")
            whole |= graph._downstream(nid)
    for nid, node in graph.nodes.items():
        if node["type"] == "aplicar_parede":
            graph.set_param(nid, "parede", wall or "")
            graph.set_param(nid, "lado", side if side in SIDES else SIDES[0])
            if nid in whole:
                graph.set_param(nid, "repetir", False)
    for nid in list(graph._cache):                     # (the wall may have changed since: worked out again)
        if graph.nodes[nid]["type"] == "fachada_bim" or nid in whole:
            del graph._cache[nid]
    return graph


def applied(graph, results):
    """[(wall, side ±1, pattern)] of each «Aplicar à parede/fachada» worked out, for bim.add_cladding."""
    from .nodes_panels import cladding_pattern
    out = []
    for nid, node in graph.nodes.items():
        if node["type"] == "aplicar_parede" and (results.get(nid) or {}).get("bim"):
            b = results[nid]["bim"]
            out.append((b["wall"], 1 if b["side"] == "frente" else -1, cladding_pattern(b)))
    return out


def _worked(doc, graph, wall, side):
    from . import nodes_3d
    nodes_3d.MODEL["doc"] = doc
    retarget(graph, wall, side)
    found = applied(graph, graph.evaluate())
    if not found:
        failed = next(iter(graph.errors.values()), "")
        raise GraphError(failed or "o operador não tem «Aplicar à parede/fachada»")
    return found


def record(graph, name="", slug=""):
    """(0.543) What a finish keeps of the operator that made it (its «Operador» text): its name, the library's
    slug and the graph itself with the measures used — so it is worked out again when the wall changes, and opened
    in the editor, even in another computer without that library."""
    return json.dumps({"name": name, "slug": slug, "graph": _portable(graph)}, ensure_ascii=False,
                      separators=(",", ":"))


def set_values(graph, values):
    """The measures changed in the side panel ({(node id, measure): value}) put in the graph."""
    for (nid, name), value in (values or {}).items():
        if nid in graph.nodes:
            graph.set_param(nid, name, value)
    return graph


def apply_to(doc, slug_or_graph, wall, side="frente", values=None, name="", slug=""):
    """An operator (its slug, or a graph) applied to a wall's face: its perforated finishes made, each keeping the
    operator (record). `values`: measures changed for this time. Returns their GlobalIds. GraphError where it has
    nothing to apply or a node failed."""
    from ...model import bim
    if isinstance(slug_or_graph, str):
        slug = slug_or_graph
        name, _about, graph = load(slug)
    else:
        graph = slug_or_graph
    set_values(graph, values)
    text = record(graph, name, slug)
    return [bim.add_cladding(doc, w or wall, s, "perfurado", 0.0, dict(pattern, operator=text))
            for w, s, pattern in _worked(doc, graph, wall, side)]


def operator_of(doc, guid):
    """(0.543) {"name", "slug", "graph": Graph, "wall", "side"} of the operator a finish keeps — None: it has none
    (or it is not a finish)."""
    try:
        p = doc.ifc._params(doc.ifc.by_guid(guid))
    except Exception:  # (not of the IFC: a sketch, a dimension)
        return None
    if p.get("Elemento") != "cladding" or not p.get("Operador"):
        return None
    try:
        data = json.loads(p["Operador"])
        graph = Graph.from_dict(data["graph"])
    except (ValueError, KeyError, TypeError):
        return None
    return {"name": str(data.get("name") or ""), "slug": str(data.get("slug") or ""), "graph": graph,
            "wall": p.get("Parede"), "side": SIDES[0] if int(p.get("Lado") or 1) > 0 else SIDES[1]}


def finishes_of(doc, guids):
    """(0.543) The finishes that keep an operator among `guids` — those chosen themselves, and those on the walls
    chosen. Asked for by the side panel (a look through the model's finishes: not done at every edit)."""
    guids = list(guids)
    out = [g for g in guids if operator_of(doc, g) is not None]
    walls = {g for g in guids if _kind(doc, g) == "wall"}
    if walls:
        for e in doc.ifc.file.by_type("IfcCovering"):
            p = doc.ifc._params(e)
            if p.get("Elemento") == "cladding" and p.get("Parede") in walls and p.get("Operador") \
                    and e.GlobalId not in out:
                out.append(e.GlobalId)
    return out


def _kind(doc, guid):
    try:
        return doc.ifc.kind_of(guid)
    except Exception:  # (not of the IFC)
        return None


def host_wall(doc, guid):
    """The wall a thing chosen stands for: itself, or — a wall's finish — the wall it is on (None: neither)."""
    kind = _kind(doc, guid)
    if kind == "wall":
        return guid
    if kind == "cladding":
        return doc.ifc._params(doc.ifc.by_guid(guid)).get("Parede") or None
    return None


def rework(ifc, covering):
    """(0.544) Called by the IFC when a wall changed (ifc.follow_claddings — inside the wall's own undo step): the
    finish's holes worked out again by the operator it keeps, on the wall's face as it is now. Its «Operador» text
    stays. Whatever fails (an operator of a newer version, a node's error on the new face), the finish keeps the
    holes it had: a wall's edit is never refused for it. Returns whether it was worked out."""
    import types

    from . import nodes_3d
    p = ifc._params(covering)
    before = nodes_3d.MODEL["doc"]
    try:
        graph = Graph.from_dict(json.loads(p["Operador"])["graph"])
        side = SIDES[0] if int(p.get("Lado") or 1) > 0 else SIDES[1]
        found = _worked(types.SimpleNamespace(ifc=ifc), graph, p.get("Parede"), side)
        ifc._set_params(covering, ifc._pattern_changes(found[0][2]))
    except Exception:  # noqa: BLE001 (see above)
        return False
    finally:
        nodes_3d.MODEL["doc"] = before
    return True


def update(doc, guid, graph=None, name=None, slug=None):
    """(0.543) A finish's holes worked out again on its wall as it is now (a window more, the wall longer) with
    the operator it keeps — or with `graph`, the editor's. One undo step. GraphError where it keeps none or a node
    failed."""
    from ...model import bim
    kept = operator_of(doc, guid)
    if kept is None:
        raise GraphError("este painel não guarda o operador que o fez")
    graph = graph or kept["graph"]
    found = _worked(doc, graph, kept["wall"], kept["side"])
    _wall, _side, pattern = found[0]
    text = record(graph, kept["name"] if name is None else name, kept["slug"] if slug is None else slug)
    bim.set_cladding(doc, guid, **dict(pattern, operator=text))
    return guid
