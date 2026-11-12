"""(0.541) Ready graphs — something to start from (PLANO.md, «Gráfico Visual», step 4: picture → perforated panel).
The window's «Modelos» menu and the AI (MCP) both take them from here."""

from .graph import Graph


def _chain(g, *pairs):
    for a, out, b, inp in pairs:
        g.connect(a, out, b, inp)


def atrator_hexagono():
    g = Graph()
    p = g.add_node("painel_plano", pos=(0, 0))
    h = g.add_node("hexagono", pos=(260, -40))
    a = g.add_node("atrator", {"x": 1.0, "y": 0.6, "raio": 1.4}, pos=(260, 260))
    f = g.add_node("perfurar", {"d_min": 0.004, "d_max": 0.05}, pos=(520, 60))
    c = g.add_node("verificar_fabrico", pos=(780, 0))
    b = g.add_node("aplicar_parede", pos=(1040, 60))
    _chain(g, (p, "painel", h, "painel"), (h, "pontos", f, "pontos"), (a, "campo", f, "campo"),
           (f, "furos", c, "furos"), (c, "furos", b, "furos"))
    return g


def imagem_painel(ficheiro=""):
    """The strong case: a photograph's dark parts as big holes, on a fine square grid, checked hole by hole, ready
    for the CNC (DXF) and for a wall."""
    g = Graph()
    p = g.add_node("painel_plano", {"largura": 2.4, "altura": 1.2}, pos=(0, 0))
    q = g.add_node("grelha", {"passo": 0.03}, pos=(260, -60))
    i = g.add_node("imagem", {"ficheiro": ficheiro, "contraste": 1.4}, pos=(260, 260))
    f = g.add_node("perfurar", {"d_min": 0.0, "d_max": 0.026, "sem_furo": 0.004}, pos=(520, 60))
    c = g.add_node("verificar_fabrico", {"furo_min": 0.004, "ponte_min": 0.003}, pos=(780, 0))
    x = g.add_node("exportar_dxf", pos=(1040, -80))
    b = g.add_node("aplicar_parede", pos=(1040, 200))
    _chain(g, (p, "painel", q, "painel"), (p, "painel", i, "painel"), (q, "pontos", f, "pontos"),
           (i, "campo", f, "campo"), (f, "furos", c, "furos"), (c, "furos", x, "furos"), (c, "furos", b, "furos"))
    return g


def voronoi_centro():
    g = Graph()
    p = g.add_node("painel_plano", {"largura": 3.0, "altura": 1.2}, pos=(0, 0))
    a = g.add_node("atrator", {"x": 1.5, "y": 0.6, "raio": 1.5}, pos=(0, 260))
    v = g.add_node("voronoi", {"quantidade": 900, "relaxar": 3}, pos=(260, 60))
    f = g.add_node("perfurar", {"d_min": 0.008, "d_max": 0.03}, pos=(520, 60))
    c = g.add_node("verificar_fabrico", pos=(780, 60))
    _chain(g, (p, "painel", v, "painel"), (a, "campo", v, "densidade"), (v, "pontos", f, "pontos"),
           (f, "furos", c, "furos"))
    return g


def gradiente_grelha():
    g = Graph()
    p = g.add_node("painel_plano", pos=(0, 0))
    q = g.add_node("grelha", {"passo": 0.05, "disposicao": "diagonal"}, pos=(260, -40))
    d = g.add_node("gradiente", {"angulo": 90.0}, pos=(260, 260))
    f = g.add_node("perfurar", {"d_min": 0.005, "d_max": 0.04, "forma": "quadrado"}, pos=(520, 60))
    c = g.add_node("verificar_fabrico", pos=(780, 60))
    _chain(g, (p, "painel", q, "painel"), (p, "painel", d, "painel"), (q, "pontos", f, "pontos"),
           (d, "campo", f, "campo"), (f, "furos", c, "furos"))
    return g


def ruido_folhagem():
    g = Graph()
    p = g.add_node("painel_plano", pos=(0, 0))
    h = g.add_node("hexagono", {"passo": 0.04}, pos=(260, -40))
    n = g.add_node("ruido", {"escala": 0.6, "camadas": 3}, pos=(260, 260))
    f = g.add_node("perfurar", {"d_min": 0.0, "d_max": 0.034, "forma": "hexagonal"}, pos=(520, 60))
    c = g.add_node("verificar_fabrico", pos=(780, 60))
    _chain(g, (p, "painel", h, "painel"), (h, "pontos", f, "pontos"), (n, "campo", f, "campo"),
           (f, "furos", c, "furos"))
    return g


def _on_surface(g, holes):
    """…holes → corrected for fabrication → checked → on the wall (the surface whole)."""
    fix = g.add_node("corrigir_fabrico", pos=(1040, 60))
    c = g.add_node("verificar_fabrico", pos=(1300, 60))
    b = g.add_node("aplicar_parede", {"repetir": False}, pos=(1560, 60))
    _chain(g, (holes, "furos", fix, "furos"), (fix, "furos", c, "furos"), (c, "furos", b, "furos"))


def vaos_emoldurados():
    """(0.542) The wall's own windows drive it: holes big round them, fading away."""
    g = Graph()
    s = g.add_node("fachada_bim", pos=(0, 0))
    h = g.add_node("hexagono", {"passo": 0.07}, pos=(260, -60))
    v = g.add_node("distancia_vaos", {"alcance": 1.2}, pos=(260, 240))
    m = g.add_node("remapear", {"curva": 1.6}, pos=(520, 240))
    f = g.add_node("perfurar", {"d_min": 0.006, "d_max": 0.06}, pos=(780, 60))
    _chain(g, (s, "painel", h, "painel"), (s, "painel", v, "painel"), (v, "campo", m, "campo"),
           (h, "pontos", f, "pontos"), (m, "campo", f, "campo"))
    _on_surface(g, f)
    return g


def ondas_degraus():
    """(0.542) Winding bands in four sizes of hole only, clear of the windows."""
    g = Graph()
    s = g.add_node("fachada_bim", pos=(0, 0))
    q = g.add_node("grelha", {"passo": 0.06, "disposicao": "diagonal"}, pos=(260, -60))
    v = g.add_node("distancia_vaos", {"alcance": 0.25}, pos=(260, 200))
    e = g.add_node("escolher_pontos", {"limiar": 0.05, "inverter": True}, pos=(520, -60))
    w = g.add_node("ondas", {"comprimento": 1.2, "angulo": 20.0, "ondular": 1.5}, pos=(260, 420))
    m = g.add_node("remapear", {"degraus": 4}, pos=(520, 420))
    f = g.add_node("perfurar", {"d_min": 0.008, "d_max": 0.05}, pos=(780, 60))
    _chain(g, (s, "painel", q, "painel"), (s, "painel", v, "painel"), (q, "pontos", e, "pontos"),
           (v, "campo", e, "campo"), (w, "campo", m, "campo"), (e, "pontos", f, "pontos"), (m, "campo", f, "campo"))
    _on_surface(g, f)
    return g


def aneis_ventilacao():
    """(0.542) Rings in a spiral from the surface's middle, brought to 25 % of open area."""
    g = Graph()
    s = g.add_node("fachada_bim", pos=(0, 0))
    a = g.add_node("radial", {"x": 2.0, "y": 1.35, "passo": 0.07, "espiral": True}, pos=(260, -60))
    t = g.add_node("atrator", {"x": 2.0, "y": 1.35, "raio": 3.0}, pos=(260, 240))
    f = g.add_node("perfurar", {"d_min": 0.01, "d_max": 0.05}, pos=(520, 60))
    o = g.add_node("area_aberta", {"alvo": 25.0, "d_max": 0.06}, pos=(780, 60))
    _chain(g, (s, "painel", a, "painel"), (a, "pontos", f, "pontos"), (t, "campo", f, "campo"),
           (f, "furos", o, "furos"))
    _on_surface(g, o)
    return g


# key -> (name, description, maker)
TEMPLATES = {
    "imagem_painel": ("Imagem → painel perfurado", "Uma fotografia nos furos: escuro = furo grande; verificado, "
                      "em DXF e pronto para a parede.", imagem_painel),
    "atrator_hexagono": ("Atrator em favo", "Furos hexagonais a crescer junto a um ponto.", atrator_hexagono),
    "voronoi_centro": ("Voronoi denso no centro", "Pontos soltos, mais juntos no meio do painel.", voronoi_centro),
    "gradiente_grelha": ("Gradiente em quincôncio", "Furos quadrados a crescer de baixo para cima.",
                         gradiente_grelha),
    "ruido_folhagem": ("Folhagem (ruído)", "Manchas orgânicas, como luz entre folhas.", ruido_folhagem),
    "vaos_emoldurados": ("Janelas emolduradas", "Na parede toda: furos grandes à volta das portas e janelas, a "
                         "diminuir ao afastar-se; já corrigido para fabrico.", vaos_emoldurados),
    "ondas_degraus": ("Ondas em quatro furos", "Faixas sinuosas com só quatro diâmetros de furo, afastadas dos "
                      "vãos.", ondas_degraus),
    "aneis_ventilacao": ("Espiral com 25 % de área aberta", "Furos em espiral a partir do meio da parede, levados "
                         "a 25 % de área aberta para ventilação.", aneis_ventilacao),
}


def make(key, **kw):
    return TEMPLATES[key][2](**kw)
