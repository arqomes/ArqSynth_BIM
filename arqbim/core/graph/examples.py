"""(0.544) Each node shown at work (PLANO.md, «Gráfico Visual», step 7): a small graph with the node fed by the usual
ones (a panel, a favo of points, an attractor, holes), and one of its measures swept from its lowest to its highest
use — the loop the palette plays while the node is chosen."""

from .graph import Graph

# Nodes that cannot be shown without a model or that write files: shown on their input's result, unmoving
STILL = {"fachada_bim", "exportar_dxf", "aplicar_parede"}
SWEEP = {           # (the measure that shows the node best; else its first number), and its range for the loop
    "painel_plano": ("largura", 1.0, 4.0), "grelha": ("passo", 0.04, 0.14), "hexagono": ("passo", 0.04, 0.14),
    "voronoi": ("quantidade", 40, 500), "atrator": ("raio", 0.3, 2.5), "gradiente": ("angulo", -180.0, 180.0),
    "imagem": None, "ruido": ("escala", 0.15, 1.5), "perfurar": ("d_max", 0.02, 0.09),
    "verificar_fabrico": ("ponte_min", 0.002, 0.03), "subdividir": ("colunas", 1, 6),
    "extrudir": ("espessura", 0.005, 0.06), "relevo": ("altura", -0.15, 0.15), "dobrar": ("angulo", 0.0, 120.0),
}


def _feed(g, kind, cache):
    """A node giving `kind` (made once per example)."""
    if kind in cache:
        return cache[kind]
    if kind == "panel":
        out = (g.add_node("painel_plano", {"largura": 2.4, "altura": 1.2}), "painel")
    elif kind == "points":
        p = _feed(g, "panel", cache)
        n = g.add_node("hexagono", {"passo": 0.08})
        g.connect(p[0], p[1], n, "painel")
        out = (n, "pontos")
    elif kind == "field":
        out = (g.add_node("atrator", {"x": 0.8, "y": 0.6, "raio": 1.2}), "campo")
    elif kind == "holes":
        pts, fld = _feed(g, "points", cache), _feed(g, "field", cache)
        n = g.add_node("perfurar", {"d_min": 0.006, "d_max": 0.07})
        g.connect(pts[0], pts[1], n, "pontos")
        g.connect(fld[0], fld[1], n, "campo")
        out = (n, "furos")
    elif kind == "mesh":
        h = _feed(g, "holes", cache)
        n = g.add_node("extrudir", {"espessura": 0.02})
        g.connect(h[0], h[1], n, "furos")
        out = (n, "malha")
    else:
        return None
    cache[kind] = out
    return out


def example(key):
    """(graph, node id shown, (measure, lo, hi) or None)."""
    g = Graph()
    if key in STILL:
        spec = g.registry.get(key)
        kind = spec.inputs[0].kind if spec.inputs else "panel"
        shown = _feed(g, kind, {})
        return g, shown[0], None
    nid = g.add_node(key)
    spec = g.registry.get(key)
    cache = {}
    for port in spec.inputs:
        if port.optional and port.kind == "field" and key not in ("perfurar", "voronoi"):
            continue
        src = _feed(g, port.kind, cache)
        if src is not None:
            g.connect(src[0], src[1], nid, port.name)
    return g, nid, SWEEP.get(key)


def frame_value(sweep, k, frames):
    """The swept measure at frame k (there and back: the loop has no jump)."""
    _name, lo, hi = sweep
    half = frames // 2
    f = k % frames
    t = f / half if f <= half else (frames - f) / half
    v = lo + (hi - lo) * t
    return int(round(v)) if isinstance(lo, int) else v
