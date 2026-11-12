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
    # (0.542) the logic nodes
    "distancia_vaos": ("alcance", 0.1, 1.0), "distancia_contorno": ("alcance", 0.1, 0.6),
    "distancia_linha": ("alcance", 0.1, 1.2), "ondas": ("comprimento", 0.2, 1.2), "mascara": ("largura", 0.3, 2.0),
    "aleatorio": ("tamanho", 0.05, 0.4), "misturar": ("fator", 0.0, 1.0), "remapear": ("degraus", 0, 5),
    "radial": ("passo", 0.05, 0.16), "contorno_pontos": ("filas", 1, 4), "escolher_pontos": ("limiar", 0.1, 0.9),
    "desalinhar": ("quanto", 0.0, 1.0), "juntar_pontos": ("folga", 0.0, 1.5), "escalar_furos": ("fator", 0.3, 1.6),
    "juntar_furos": None, "area_aberta": ("alvo", 5.0, 45.0), "corrigir_fabrico": ("ponte_min", 0.002, 0.04),
    "rodar_furos": ("angulo", 0.0, 180.0), "alongar_furos": ("alongar", 1.0, 4.0),            # (0.545)
    "matriz": ("desvio", 0.0, 1.0),                                                            # (0.553)
    "forma_organica": ("altura", 0.2, 1.2), "furos_na_forma": None,                            # (0.558)
    "contorno_organico": ("passos", 10, 120),                                                  # (0.561)
    "paginacao": ("w", 0.10, 0.40),                                                            # (0.570)
}
# (0.542) nodes shown on a surface with a window (they read its openings); those whose modulator must be linked
WITH_WINDOW = {"distancia_vaos", "distancia_contorno", "contorno_pontos"}
NEEDS_FIELD = {"perfurar", "voronoi", "escolher_pontos", "escalar_furos", "desalinhar"}


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
        p = _feed(g, "panel", cache)                     # (0.558: an organic form — the 3D nodes take any solid)
        n = g.add_node("forma_organica", {"altura": 0.6, "divisoes": 16})
        g.connect(p[0], p[1], n, "painel")
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
    if key in WITH_WINDOW:
        cache["panel"] = (g.add_node("fachada_bim"), "painel")       # (no wall: the example face, with its window)
    for k, port in enumerate(spec.inputs):
        if port.optional and port.kind == "field" and key not in NEEDS_FIELD:
            continue
        if k and port.kind == spec.inputs[0].kind:                  # (a second of the same kind: something else)
            src = _second(g, port.kind, cache)
        else:
            src = _feed(g, port.kind, cache)
        if src is not None:
            g.connect(src[0], src[1], nid, port.name)
    return g, nid, SWEEP.get(key)


def _second(g, kind, cache):
    """Another node giving `kind`, unlike _feed's (for the nodes that join two things)."""
    if kind == "field":
        return (g.add_node("ondas", {"comprimento": 0.5}), "campo")
    if kind == "points":
        p = _feed(g, "panel", cache)
        n = g.add_node("radial", {"x": 1.2, "y": 0.6, "passo": 0.11})
        g.connect(p[0], p[1], n, "painel")
        return (n, "pontos")
    if kind == "holes":
        pts = _second(g, "points", cache)
        n = g.add_node("perfurar", {"d_max": 0.03})
        g.connect(pts[0], pts[1], n, "pontos")
        return (n, "furos")
    return _feed(g, kind, cache)


def frame_value(sweep, k, frames):
    """The swept measure at frame k (there and back: the loop has no jump)."""
    _name, lo, hi = sweep
    half = frames // 2
    f = k % frames
    t = f / half if f <= half else (frames - f) / half
    v = lo + (hi - lo) * t
    return int(round(v)) if isinstance(lo, int) else v
