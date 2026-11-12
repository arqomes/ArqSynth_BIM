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


def load(slug):
    """(name, about, Graph) of an operator. GraphError where it cannot be read."""
    try:
        with open(_path(slug), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise GraphError("não foi possível ler o operador: {}".format(e)) from None
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        raise GraphError("não é um operador do ArqSynth")
    if data.get("version", 0) > VERSION:
        raise GraphError("operador feito por uma versão mais nova do ArqSynth")
    return str(data.get("name") or slug), str(data.get("about") or ""), Graph.from_dict(data["graph"])


def save(name, graph, slug=None, about="", png=None):
    """An operator kept in the library (a new one: its file named after it; `slug`: that one written over).
    `png`: its thumbnail's bytes. The walls it was drawn on are not kept: it serves any. Returns its slug."""
    name = str(name).strip()
    if not name:
        raise GraphError("dê um nome ao operador")
    seed()
    slug = slug or _free_slug(name)
    data = graph.to_dict()
    for node in data["nodes"]:
        if node["type"] in ("fachada_bim", "aplicar_parede"):
            node["params"] = dict(node["params"], parede="")
    with open(_path(slug), "w", encoding="utf-8") as f:
        json.dump({"format": FORMAT, "version": VERSION, "name": name, "about": about, "graph": data}, f,
                  ensure_ascii=False, indent=1)
    if png:
        with open(thumbnail_path(slug), "wb") as f:
            f.write(png)
    return slug


def delete(slug):
    for ext in (".json", ".png"):
        try:
            os.remove(_path(slug, ext))
        except OSError:
            pass


def duplicate(slug):
    name, about, graph = load(slug)
    new = save(name + " (cópia)", graph, about=about)
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
                    about=str(data.get("about") or ""))
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


def apply_to(doc, slug_or_graph, wall, side="frente"):
    """An operator (its slug, or a graph) applied to a wall's face: its perforated finishes made. Returns their
    GlobalIds. GraphError where it has nothing to apply or a node failed."""
    from ...model import bim
    from . import nodes_3d
    graph = load(slug_or_graph)[2] if isinstance(slug_or_graph, str) else slug_or_graph
    nodes_3d.MODEL["doc"] = doc
    retarget(graph, wall, side)
    results = graph.evaluate()
    found = applied(graph, results)
    if not found:
        failed = next(iter(graph.errors.values()), "")
        raise GraphError(failed or "o operador não tem «Aplicar à parede/fachada»")
    return [bim.add_cladding(doc, w or wall, s, "perfurado", 0.0, pattern) for w, s, pattern in found]
