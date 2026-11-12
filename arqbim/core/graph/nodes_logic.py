"""(0.542, the owner: «preciso de operadores poderosos e lógicos») The Visual Graph's logic nodes (PLANO.md, «Gráfico
Visual, 2.ª fase», step 6): modulators that read the surface itself (its outline, its doors and windows, a line, a
zone), modulators worked on (mixed, remapped, in steps), points chosen, moved, joined and laid along the outline or
in rings, holes joined, scaled, brought to an open area and corrected for fabrication.

The data are nodes_panels' (panel, points, field, holes)."""

import math

import numpy as np

from .nodes_panels import Field, _close_pairs, _keep_inside, _num, _radius_out, hole_extras, r, take_holes
from .registry import Port

HOLE_AREA = {"redondo": math.pi / 4.0, "quadrado": 1.0, "hexagonal": math.sqrt(3.0) / 2.0}


def _int(name, label, default, lo, hi):
    return Port(name, "int", label, default=default, min=lo, max=hi, step=1, unit="")


def _flag(name, label, default=False):
    return Port(name, "bool", label, default=default)


def openings(panel):
    """The doors and windows of a surface: what its rectangle has and it has not (None: none)."""
    from shapely.geometry import box
    gaps = box(*panel["shape"].bounds).difference(panel["shape"].buffer(1e-6))
    return None if gaps.is_empty or gaps.area < 1e-6 else gaps


def _distance(shape, xy):
    import shapely
    return shapely.distance(shape, shapely.points(xy))


def _fade(dist, reach, smooth=True):
    """1 at the thing, 0 at `reach` from it and beyond."""
    t = np.clip(np.asarray(dist, dtype=float) / max(reach, 1e-9), 0.0, 1.0)
    return 1.0 - (t * t * (3.0 - 2.0 * t) if smooth else t)


# ------------------------------------------------------------------ Moduladores: from the surface
@r.node("distancia_vaos", "Moduladores", "Junto aos vãos",
        "Forte (1) junto às portas e janelas da superfície, a enfraquecer até ao alcance. Invertido: fraco junto "
        "aos vãos — para os furos se afastarem ou diminuírem ao chegar às janelas.",
        inputs=[Port("painel", "panel", "Superfície")], outputs=[Port("campo", "field", "Campo")],
        params=[_num("alcance", "Alcance", 0.8, 0.02, 20.0, 0.01), _flag("inverter", "Inverter")],
        example="Furos maiores à volta das janelas, como uma moldura de luz.")
def distancia_vaos(painel, alcance, inverter):
    gaps = openings(painel)

    def fn(xy):
        v = np.zeros(len(xy)) if gaps is None else _fade(_distance(gaps, xy), alcance)
        return 1.0 - v if inverter else v
    return {"campo": Field(fn, "vãos")}


@r.node("distancia_contorno", "Moduladores", "Junto ao contorno",
        "Forte (1) junto às arestas da superfície (o contorno e os vãos), a enfraquecer para dentro até ao alcance.",
        inputs=[Port("painel", "panel", "Superfície")], outputs=[Port("campo", "field", "Campo")],
        params=[_num("alcance", "Alcance", 0.5, 0.02, 20.0, 0.01), _flag("inverter", "Inverter")],
        example="Invertido: furos grandes no meio do painel, a fechar para as arestas.")
def distancia_contorno(painel, alcance, inverter):
    edge = painel["shape"].boundary

    def fn(xy):
        v = _fade(_distance(edge, xy), alcance)
        return 1.0 - v if inverter else v
    return {"campo": Field(fn, "contorno")}


@r.node("distancia_linha", "Moduladores", "Junto a uma linha",
        "Forte (1) sobre a linha entre dois pontos, a enfraquecer até ao alcance: um atrator comprido.",
        outputs=[Port("campo", "field", "Campo")],
        params=[_num("x1", "Início X", 0.0, -50.0, 50.0, 0.01), _num("y1", "Início Y", 0.3, -50.0, 50.0, 0.01),
                _num("x2", "Fim X", 3.0, -50.0, 50.0, 0.01), _num("y2", "Fim Y", 1.0, -50.0, 50.0, 0.01),
                _num("alcance", "Alcance", 0.6, 0.02, 20.0, 0.01), _flag("inverter", "Inverter")],
        example="Uma diagonal de furos grandes a atravessar a fachada.")
def distancia_linha(x1, y1, x2, y2, alcance, inverter):
    a, b = np.array((x1, y1)), np.array((x2, y2))
    ab = b - a
    length2 = max(float(ab @ ab), 1e-12)

    def fn(xy):
        t = np.clip(((xy - a) @ ab) / length2, 0.0, 1.0)
        v = _fade(np.hypot(*(xy - (a + t[:, None] * ab)).T), alcance)
        return 1.0 - v if inverter else v
    return {"campo": Field(fn, "linha")}


@r.node("ondas", "Moduladores", "Ondas",
        "Faixas que sobem e descem (0 a 1) numa direção, com o comprimento de onda escolhido.",
        outputs=[Port("campo", "field", "Campo")],
        params=[_num("comprimento", "Comprimento de onda", 0.8, 0.02, 50.0, 0.01),
                _num("angulo", "Direção", 0.0, -180.0, 180.0, 1.0, "°"),
                _num("fase", "Desfasamento", 0.0, 0.0, 1.0, 0.01, ""),
                _num("ondular", "Ondular", 0.0, 0.0, 5.0, 0.01)],
        example="Faixas verticais de furos grandes e pequenos; «Ondular» torna-as sinuosas.")
def ondas(comprimento, angulo, fase, ondular):
    a = math.radians(angulo)
    d, across = np.array((math.cos(a), math.sin(a))), np.array((-math.sin(a), math.cos(a)))

    def fn(xy):
        along = xy @ d + ondular * comprimento * 0.25 * np.sin(2.0 * math.pi * (xy @ across) / (comprimento * 2.0))
        return 0.5 + 0.5 * np.sin(2.0 * math.pi * (along / comprimento + fase))
    return {"campo": Field(fn, "ondas")}


@r.node("mascara", "Moduladores", "Zona",
        "Uma zona retangular ou redonda: 1 dentro, 0 fora (ao contrário, invertida), com a orla suavizada. Com "
        "«Escolher pontos» ou «Misturar», limita um efeito a uma parte da superfície.",
        outputs=[Port("campo", "field", "Campo")],
        params=[_num("x", "Centro X", 1.5, -50.0, 50.0, 0.01), _num("y", "Centro Y", 0.6, -50.0, 50.0, 0.01),
                _num("largura", "Largura", 1.0, 0.01, 50.0, 0.01), _num("altura", "Altura", 0.6, 0.01, 50.0, 0.01),
                Port("forma", "choice", "Forma", default="retângulo", choices=("retângulo", "elipse")),
                _num("suavizar", "Orla suave", 0.0, 0.0, 5.0, 0.01), _flag("inverter", "Inverter")],
        example="Uma faixa sem furos à altura dos olhos.")
def mascara(x, y, largura, altura, forma, suavizar, inverter):
    def fn(xy):
        dx, dy = np.abs(xy[:, 0] - x), np.abs(xy[:, 1] - y)
        if forma == "elipse":
            k = np.hypot(dx / (largura / 2.0), dy / (altura / 2.0))
            out = (k - 1.0) * min(largura, altura) / 2.0          # (how far outside, about)
        else:
            out = np.maximum(dx - largura / 2.0, dy - altura / 2.0)
        v = (out <= 0).astype(float) if suavizar <= 0 else _fade(np.maximum(out, 0.0), suavizar)
        return 1.0 - v if inverter else v
    return {"campo": Field(fn, "zona")}


@r.node("aleatorio", "Moduladores", "Aleatório",
        "Um valor ao acaso (0 a 1) em cada quadrícula do tamanho escolhido: cada furo, ou cada grupo de furos, com o "
        "seu tamanho.",
        outputs=[Port("campo", "field", "Campo")],
        params=[_num("tamanho", "Quadrícula", 0.06, 0.005, 10.0, 0.005), _int("semente", "Semente", 1, 0, 9999)],
        example="Quadrícula igual ao passo: cada furo com um tamanho diferente.")
def aleatorio(tamanho, semente):
    def fn(xy):
        cell = np.floor(xy / tamanho + 0.5).astype(np.int64)
        h = (cell[:, 0] * 73856093) ^ (cell[:, 1] * 19349663) ^ (int(semente) * 83492791 + 12345)
        h = (h ^ (h >> 13)) * 1274126177
        return ((h ^ (h >> 16)) & 0xFFFFFF) / float(0xFFFFFF)
    return {"campo": Field(fn, "aleatório")}


# ------------------------------------------------------------------ Moduladores: worked on
MODES = ("multiplicar", "somar", "subtrair", "máximo", "mínimo", "média", "diferença", "trocar pelo fator")


@r.node("misturar", "Moduladores", "Misturar",
        "Dois moduladores num só: multiplicar (os dois têm de ser fortes), somar, subtrair, o máximo, o mínimo, a "
        "média, a diferença. O fator doseia quanto do segundo entra.",
        inputs=[Port("a", "field", "A"), Port("b", "field", "B")], outputs=[Port("campo", "field", "Campo")],
        params=[Port("modo", "choice", "Modo", default="multiplicar", choices=MODES),
                _num("fator", "Fator", 1.0, 0.0, 1.0, 0.01, "")],
        example="Imagem × «Junto aos vãos» invertido: a fotografia a apagar-se ao chegar às janelas.")
def misturar(a, b, modo, fator):
    def fn(xy):
        va, vb = a(xy), b(xy)
        if modo == "trocar pelo fator":
            return va + (vb - va) * fator
        mixed = {"multiplicar": va * vb, "somar": va + vb, "subtrair": va - vb, "máximo": np.maximum(va, vb),
                 "mínimo": np.minimum(va, vb), "média": (va + vb) / 2.0, "diferença": np.abs(va - vb)}[modo]
        return va + (mixed - va) * fator
    return {"campo": Field(fn, "mistura")}


@r.node("remapear", "Moduladores", "Remapear",
        "Afina um modulador: corta abaixo e acima de dois valores, dobra a resposta com a curva (mais de 1: só os "
        "valores fortes contam) e, com degraus, reduz a poucos tamanhos de furo (brocas ou punções disponíveis).",
        inputs=[Port("campo", "field", "Modulador")], outputs=[Port("campo", "field", "Campo")],
        params=[_num("de", "Entrada mínima", 0.0, 0.0, 1.0, 0.01, ""), _num("ate", "Entrada máxima", 1.0, 0.0, 1.0,
                                                                              0.01, ""),
                _num("curva", "Curva", 1.0, 0.1, 6.0, 0.05, ""), _int("degraus", "Degraus (0 = contínuo)", 0, 0, 12),
                _flag("inverter", "Inverter")],
        example="4 degraus: a fachada toda com só quatro diâmetros de furo.")
def remapear(campo, de, ate, curva, degraus, inverter):
    lo, hi = min(de, ate), max(de, ate)

    def fn(xy):
        v = np.clip((campo(xy) - lo) / max(hi - lo, 1e-9), 0.0, 1.0) ** curva
        if degraus >= 2:
            v = np.round(v * (degraus - 1)) / (degraus - 1)
        elif degraus == 1:
            v = (v >= 0.5).astype(float)
        return 1.0 - v if inverter else v
    return {"campo": Field(fn, "remapeado")}


# ------------------------------------------------------------------ Padrões: more ways of laying points
@r.node("radial", "Padrões", "Anéis",
        "Pontos em anéis à volta de um centro, à mesma distância uns dos outros em cada anel.",
        inputs=[Port("painel", "panel", "Painel")], outputs=[Port("pontos", "points", "Pontos")],
        params=[_num("x", "Centro X", 1.5, -50.0, 50.0, 0.01), _num("y", "Centro Y", 0.6, -50.0, 50.0, 0.01),
                _num("passo", "Passo", 0.06, 0.005, 1.0, 0.005), _flag("espiral", "Em espiral")],
        example="Um sol de furos a partir do centro de uma janela.")
def radial(painel, x, y, passo, espiral):
    x0, y0, x1, y1 = painel["shape"].bounds
    far = max(math.hypot(cx - x, cy - y) for cx in (x0, x1) for cy in (y0, y1))
    pts = [(x, y)]
    if espiral:                                   # (Fermat's: every point with the same room)
        n = int(math.pi * far * far / (passo * passo)) + 1
        if n > 200000:
            raise ValueError("passo pequeno demais para esta superfície")
        k = np.arange(1, n)
        rad, ang = passo * np.sqrt(k / math.pi), k * math.pi * (3.0 - math.sqrt(5.0))
        xy = np.vstack((pts, np.column_stack((x + rad * np.cos(ang), y + rad * np.sin(ang)))))
    else:
        rings = int(far / passo) + 1
        if rings * rings * 3.3 > 200000:
            raise ValueError("passo pequeno demais para esta superfície")
        for k in range(1, rings + 1):
            n = max(6, int(round(2.0 * math.pi * k)))
            ang = 2.0 * math.pi * np.arange(n) / n + (k % 2) * math.pi / n
            pts += list(zip(x + k * passo * np.cos(ang), y + k * passo * np.sin(ang)))
        xy = np.array(pts, dtype=float)
    return {"pontos": {"panel": painel, "xy": _keep_inside(painel, xy, passo / 2.0), "pitch": passo}}


@r.node("contorno_pontos", "Padrões", "Ao longo do contorno",
        "Pontos em fila ao longo das arestas da superfície — o contorno, os vãos, ou ambos —, a uma distância delas, "
        "em uma ou mais filas.",
        inputs=[Port("painel", "panel", "Superfície")], outputs=[Port("pontos", "points", "Pontos")],
        params=[Port("onde", "choice", "Onde", default="vãos", choices=("vãos", "contorno", "ambos")),
                _num("distancia", "Distância à aresta", 0.12, 0.005, 5.0, 0.005),
                _num("passo", "Passo", 0.06, 0.005, 1.0, 0.005), _int("filas", "Filas", 1, 1, 12)],
        example="Três filas de furos a emoldurar cada janela.")
def contorno_pontos(painel, onde, distancia, passo, filas):
    from shapely.geometry import box
    shape = painel["shape"]
    frame = box(*shape.bounds)
    gaps = openings(painel)
    pts = []
    for k in range(filas):
        off = distancia + k * passo
        lines = []
        if onde in ("vãos", "ambos") and gaps is not None:
            lines.append(gaps.buffer(off, join_style=2).boundary)
        if onde in ("contorno", "ambos"):
            inner = frame.buffer(-off, join_style=2)
            if not inner.is_empty:
                lines.append(inner.boundary)
        for line in lines:
            for part in getattr(line, "geoms", [line]):
                n = max(1, int(round(part.length / passo)))
                pts += [part.interpolate(i / n, normalized=True).coords[0] for i in range(n)]
    xy = np.array(pts, dtype=float).reshape(-1, 2)
    if not len(xy) and onde == "vãos":
        raise ValueError("esta superfície não tem vãos")
    # (kept wherever a hole may be: its distance to the edge is the owner's — «Verificar fabrico» says if too near)
    return {"pontos": {"panel": painel, "xy": _keep_inside(painel, xy, 0.0), "pitch": passo}}


# ------------------------------------------------------------------ Operações: points
@r.node("escolher_pontos", "Operações", "Escolher pontos",
        "Fica só com os pontos onde o modulador é forte (acima do limiar) — ou, invertido, onde é fraco. Com uma "
        "«Zona» ou «Junto aos vãos», tira os furos de uma parte da superfície.",
        inputs=[Port("pontos", "points", "Pontos"), Port("campo", "field", "Modulador")],
        outputs=[Port("pontos", "points", "Pontos")],
        params=[_num("limiar", "Limiar", 0.5, 0.0, 1.0, 0.01, ""), _flag("inverter", "Inverter")],
        example="«Junto aos vãos» invertido: nenhum furo a menos de 30 cm das janelas.")
def escolher_pontos(pontos, campo, limiar, inverter):
    xy = pontos["xy"]
    keep = campo(xy) >= limiar if len(xy) else np.zeros(0, dtype=bool)
    return {"pontos": dict(pontos, xy=xy[~keep if inverter else keep])}


@r.node("desalinhar", "Operações", "Desalinhar",
        "Cada ponto sai do sítio ao acaso, até uma parte do passo — toda a superfície, ou mais onde o modulador é "
        "forte: uma grelha que se desfaz.",
        inputs=[Port("pontos", "points", "Pontos"), Port("campo", "field", "Modulador", optional=True)],
        outputs=[Port("pontos", "points", "Pontos")],
        params=[_num("quanto", "Quanto (do passo)", 0.3, 0.0, 1.0, 0.01, ""), _int("semente", "Semente", 1, 0, 9999)],
        example="Uma grelha certa em baixo que se desarruma para cima (com um Gradiente).")
def desalinhar(pontos, campo, quanto, semente):
    xy = pontos["xy"]
    rng = np.random.default_rng(semente)
    ang, rad = rng.uniform(0.0, 2.0 * math.pi, len(xy)), np.sqrt(rng.uniform(size=len(xy)))
    reach = quanto * pontos["pitch"] * rad * (campo(xy) if campo is not None and len(xy) else 1.0)
    moved = xy + np.column_stack((reach * np.cos(ang), reach * np.sin(ang)))
    return {"pontos": dict(pontos, xy=_keep_inside(pontos["panel"], moved, 0.0))}


@r.node("juntar_pontos", "Operações", "Juntar pontos",
        "Dois conjuntos de pontos num só (os do segundo que caírem em cima dos do primeiro saem).",
        inputs=[Port("a", "points", "A"), Port("b", "points", "B")], outputs=[Port("pontos", "points", "Pontos")],
        params=[_num("folga", "Distância mínima (do passo)", 0.8, 0.0, 2.0, 0.05, "")],
        example="Uma grelha em toda a superfície mais filas a emoldurar as janelas.")
def juntar_pontos(a, b, folga):
    pitch = min(a["pitch"], b["pitch"])
    xa, xb = a["xy"], b["xy"]
    if len(xa) and len(xb) and folga > 0:
        both = np.vstack((xa, xb))
        i, j, _d = _close_pairs(both, folga * pitch)
        clash = set(j[(i < len(xa)) & (j >= len(xa))] - len(xa)) | set(i[(j < len(xa)) & (i >= len(xa))] - len(xa))
        xb = xb[[k for k in range(len(xb)) if k not in clash]]
    return {"pontos": {"panel": a["panel"], "xy": np.vstack((xa, xb)) if len(xb) else xa, "pitch": pitch}}


# ------------------------------------------------------------------ Operações: holes
@r.node("escalar_furos", "Operações", "Escalar furos",
        "Todos os furos maiores ou menores pelo fator — ou, com um modulador, só onde ele é forte.",
        inputs=[Port("furos", "holes", "Furos"), Port("campo", "field", "Modulador", optional=True)],
        outputs=[Port("furos", "holes", "Furos")],
        params=[_num("fator", "Fator", 1.2, 0.0, 4.0, 0.01, "×")],
        example="Fator 0 com «Junto aos vãos»: os furos a fecharem-se ao chegar às janelas.")
def escalar_furos(furos, campo, fator):
    k = fator if campo is None or not len(furos["xy"]) else 1.0 + (fator - 1.0) * campo(furos["xy"])
    d = furos["d"] * k
    keep = d >= 0.001
    return {"furos": take_holes(furos, keep, d=d[keep])}


@r.node("juntar_furos", "Operações", "Juntar furos",
        "Dois conjuntos de furos na mesma chapa (com a forma do primeiro). «Verificar fabrico» diz se algum toca "
        "noutro.",
        inputs=[Port("a", "holes", "A"), Port("b", "holes", "B")], outputs=[Port("furos", "holes", "Furos")],
        example="Furos grandes à volta das janelas mais uma grelha fina no resto.")
def juntar_furos(a, b):
    xy = np.vstack((a["xy"], b["xy"]))
    (aa, ar), (ba, br) = hole_extras(a), hole_extras(b)
    return {"furos": dict(a, xy=xy, d=np.concatenate((a["d"], b["d"])), pitch=min(a["pitch"], b["pitch"]),
                          angle=np.concatenate((aa, ba)), ratio=np.concatenate((ar, br)),
                          bad=np.zeros(len(xy), dtype=bool))}


def open_area(furos):
    from .. import surfaces
    area = surfaces.hole_area(furos["shape"], furos["d"], hole_extras(furos)[1]).sum()
    return float(area / max(furos["panel"]["shape"].area, 1e-12))


# ------------------------------------------------------------------ (0.545) each hole turned, each hole stretched
TURNS = ("ângulo fixo", "pelo modulador", "ao longo do modulador", "para um ponto", "ao acaso")


@r.node("rodar_furos", "Operações", "Rodar furos",
        "Vira cada furo: todos pelo mesmo ângulo; pelo modulador (0 a 1 = de 0 ao ângulo); ao longo do modulador "
        "(cada furo deitado segundo as suas curvas de nível — ranhuras a fluir à volta de um atrator); a apontar "
        "para um ponto; ou ao acaso.",
        inputs=[Port("furos", "holes", "Furos"), Port("campo", "field", "Modulador", optional=True)],
        outputs=[Port("furos", "holes", "Furos")],
        params=[Port("modo", "choice", "Modo", default="ângulo fixo", choices=TURNS),
                _num("angulo", "Ângulo", 45.0, -180.0, 180.0, 1.0, "°"),
                _num("x", "Ponto X", 1.5, -50.0, 50.0, 0.01), _num("y", "Ponto Y", 0.6, -50.0, 50.0, 0.01),
                _int("semente", "Semente", 1, 0, 9999)],
        example="Ranhuras «ao longo do modulador» de um Ruído: um campo de linhas a fluir.")
def rodar_furos(furos, campo, modo, angulo, x, y, semente):
    xy = furos["xy"]
    old = hole_extras(furos)[0]
    if modo in ("pelo modulador", "ao longo do modulador") and campo is None:
        raise ValueError("ligue um modulador")
    if not len(xy):
        return {"furos": furos}
    if modo == "ângulo fixo":
        turn = np.full(len(xy), float(angulo))
    elif modo == "pelo modulador":
        turn = campo(xy) * angulo
    elif modo == "ao longo do modulador":         # (square to the way the modulator grows fastest)
        h = max(float(furos.get("pitch") or 0.05) * 0.5, 1e-3)
        gx = campo(xy + (h, 0.0)) - campo(xy - (h, 0.0))
        gy = campo(xy + (0.0, h)) - campo(xy - (0.0, h))
        turn = np.degrees(np.arctan2(gy, gx)) + 90.0 + angulo
        turn = np.where(np.hypot(gx, gy) < 1e-9, float(angulo), turn)
    elif modo == "para um ponto":
        turn = np.degrees(np.arctan2(y - xy[:, 1], x - xy[:, 0])) + angulo
    else:
        turn = np.random.default_rng(semente).uniform(-abs(angulo), abs(angulo), len(xy))
    return {"furos": dict(furos, angle=old + turn, bad=np.zeros(len(xy), dtype=bool))}


@r.node("alongar_furos", "Operações", "Alongar furos",
        "Estica cada furo ao comprido (círculos em ovais, quadrados em retângulos, ranhuras mais longas): todos pelo "
        "mesmo valor — ou, com um modulador, de 1 (fraco) até ao valor (forte).",
        inputs=[Port("furos", "holes", "Furos"), Port("campo", "field", "Modulador", optional=True)],
        outputs=[Port("furos", "holes", "Furos")],
        params=[_num("alongar", "Alongar", 3.0, 1.0, 12.0, 0.05, "×")],
        example="Ranhuras curtas em cima e compridas em baixo, com um Gradiente.")
def alongar_furos(furos, campo, alongar):
    xy = furos["xy"]
    k = np.full(len(xy), float(alongar)) if campo is None or not len(xy) else 1.0 + (alongar - 1.0) * campo(xy)
    return {"furos": dict(furos, ratio=k, bad=np.zeros(len(xy), dtype=bool))}


def modules_of(panel):
    """(0.552) The panel's modules (Subdividir's), each a polygon — one: the panel itself."""
    shape = panel["shape"]
    return [q for q in getattr(shape, "geoms", [shape]) if q.geom_type == "Polygon" and q.area > 1e-9]


def module_index(panel, xy):
    """Each hole's module (its index in modules_of; −1: in none)."""
    import shapely
    out = np.full(len(xy), -1)
    if not len(xy):
        return out
    for k, q in enumerate(modules_of(panel)):
        inside = shapely.contains_xy(q.buffer(1e-9), xy[:, 0], xy[:, 1])
        out[(out < 0) & inside] = k
    return out


def module_open_areas(furos):
    """(0.552) The open area (0–1) of each module of the panel, in modules_of's order."""
    from .. import surfaces
    mods = modules_of(furos["panel"])
    if not len(furos["xy"]):
        return [0.0] * len(mods)
    where = module_index(furos["panel"], furos["xy"])
    area = surfaces.hole_area(furos["shape"], furos["d"], hole_extras(furos)[1])
    return [float(area[where == k].sum() / max(q.area, 1e-12)) for k, q in enumerate(mods)]


def _scale_to(furos, d, target, d_max, area_of, rounds=40):
    for _ in range(rounds):                       # (those at the largest diameter stop growing: the others go on)
        now = area_of(d)
        if abs(now - target) < 1e-4 or now <= 0:
            break
        d = np.minimum(d * math.sqrt(target / now), d_max)
        if np.all(d >= d_max - 1e-12):
            break
    return d


@r.node("area_aberta", "Operações", "Levar à área aberta",
        "Aumenta ou diminui todos os furos por igual até a chapa ter a percentagem de área aberta pedida (luz, "
        "ventilação, sombreamento), sem passar do diâmetro máximo. «Cada módulo»: depois de Subdividir, cada chapa "
        "chega à percentagem por si (todas iguais), não só o conjunto.",
        inputs=[Port("furos", "holes", "Furos")], outputs=[Port("furos", "holes", "Furos")],
        params=[_num("alvo", "Área aberta", 25.0, 0.5, 80.0, 0.5, "%"),
                _num("d_max", "Diâmetro máximo", 0.1, 0.001, 0.5, 0.001),
                Port("por_modulo", "bool", "Cada módulo", default=False)],
        example="Ventilação natural: 30 % de área aberta, qualquer que seja o desenho.")
def area_aberta(furos, alvo, d_max, por_modulo=False):
    from .. import surfaces
    if not len(furos["xy"]):
        raise ValueError("não há furos")
    d = furos["d"].copy()
    target = alvo / 100.0
    mods = modules_of(furos["panel"])
    if por_modulo and len(mods) > 1:              # (0.552) each module on its own
        where = module_index(furos["panel"], furos["xy"])
        ratio = hole_extras(furos)[1]
        for k, q in enumerate(mods):
            mine = where == k
            if not mine.any():
                continue
            d[mine] = _scale_to(furos, d[mine], target, d_max, lambda dd, m=mine, a=q.area: float(
                surfaces.hole_area(furos["shape"], dd, ratio[m]).sum() / max(a, 1e-12)))
    else:
        d = _scale_to(furos, d, target, d_max, lambda dd: open_area(dict(furos, d=dd)))
    return {"furos": dict(furos, d=d, bad=np.zeros(len(d), dtype=bool))}


# ------------------------------------------------------------------ Fabrico
@r.node("corrigir_fabrico", "Fabrico", "Corrigir para fabrico",
        "Emenda sozinho o que «Verificar fabrico» recusaria: encolhe os furos que deixam pontes finas demais ou "
        "invadem a margem, e tira os que ficam menores que o furo mínimo.",
        inputs=[Port("furos", "holes", "Furos")], outputs=[Port("furos", "holes", "Furos")],
        params=[_num("furo_min", "Furo mínimo", 0.003, 0.0005, 0.1, 0.0005),
                _num("ponte_min", "Ponte mínima", 0.003, 0.0005, 0.1, 0.0005)],
        example="Antes de «Verificar fabrico»: o desenho fica todo fabricável.")
def corrigir_fabrico(furos, furo_min, ponte_min):
    import shapely
    xy, d, shape, panel = furos["xy"], furos["d"].copy(), furos["shape"], furos["panel"]
    if not len(xy):
        return {"furos": furos}
    # (how far a hole of size 1 reaches: each its own, 0.545 — a slot's end, a stretched one's)
    out_of = np.asarray(_radius_out(shape, np.ones(len(d)), hole_extras(furos)[1]), dtype=float)
    within = shapely.contains_xy(panel["inside"], xy[:, 0], xy[:, 1])
    room = shapely.distance(panel["inside"].boundary, shapely.points(xy))
    d = np.where(within, np.minimum(d, room / out_of * 0.999), 0.0)
    for _ in range(6):                            # (each pair's bridge shared by its two holes, as they are big)
        i, j, dist = _close_pairs(xy, 2.0 * float((out_of * d).max(initial=0.0)) + ponte_min)
        if not len(i):
            break
        reach = out_of * d
        short = dist - reach[i] - reach[j] < ponte_min - 1e-9
        if not short.any():
            break
        i, j, dist = i[short], j[short], dist[short]
        total = np.maximum(reach[i] + reach[j], 1e-12)
        room_ij = np.maximum(dist - ponte_min, 0.0) * 0.999
        limit = np.full(len(d), np.inf)
        np.minimum.at(limit, i, room_ij * reach[i] / total / out_of[i])
        np.minimum.at(limit, j, room_ij * reach[j] / total / out_of[j])
        d = np.minimum(d, limit)
    keep = d >= furo_min
    return {"furos": take_holes(furos, keep, d=d[keep])}
