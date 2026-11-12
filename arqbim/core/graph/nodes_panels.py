"""(0.539) The Visual Graph's first nodes — perforated panels (PLANO.md, «Gráfico Visual», step 2).

What flows along the links (all in metres, the panel's corner at (0, 0), x along its width, y up):
- panel:  {"width", "height", "margin", "thickness", "shape": shapely Polygon, "inside": the part holes may use}
- points: {"panel", "xy": (n, 2), "pitch": the room each point has (a hole bigger than it touches its neighbours)}
- field:  Field — a value 0–1 at any (x, y): where holes are big (1) or small (0)
- holes:  {"panel", "xy": (n, 2), "d": (n,) diameters (or sides), "shape": "redondo" | "quadrado" | "hexagonal",
           "bad": (n,) bool — set by «Verificar fabrico»}
- report: {"ok", "holes", "small", "bridges", "edge", "open_area", "min_bridge", "problems": [text]}
- bim:    what «Aplicar à parede/fachada» hands the model (the window applies it, step 3)."""

import math

import numpy as np

from .registry import REGISTRY, Port

r = REGISTRY
MIN_CUT = 0.001      # m: a hole smaller than this is not cut at all (the field left it out)


class Field:
    """A value 0–1 at any point (x, y) of the panel. `fn(xy (n, 2)) -> (n,)`."""

    def __init__(self, fn, label=""):
        self.fn, self.label = fn, label

    def __call__(self, xy):
        xy = np.asarray(xy, dtype=float).reshape(-1, 2)
        return np.clip(np.asarray(self.fn(xy), dtype=float).reshape(-1), 0.0, 1.0)


def _num(name, label, default, lo, hi, step=None, unit="m"):
    return Port(name, "number", label, default=default, min=lo, max=hi, step=step, unit=unit)


# ------------------------------------------------------------------ Base
@r.node("painel_plano", "Base", "Painel plano",
        "Uma chapa retangular. A margem fica sem furos à volta.",
        outputs=[Port("painel", "panel", "Painel")],
        params=[_num("largura", "Largura", 3.0, 0.1, 12.0, 0.01), _num("altura", "Altura", 1.2, 0.1, 12.0, 0.01),
                _num("margem", "Margem", 0.05, 0.0, 1.0, 0.005),
                _num("espessura", "Espessura", 0.003, 0.0005, 0.1, 0.0005)],
        example="Painel de 3 × 1,2 m, margem de 5 cm, chapa de 3 mm.")
def painel_plano(largura, altura, margem, espessura):
    from shapely.geometry import box
    shape = box(0.0, 0.0, largura, altura)
    inside = shape.buffer(-margem, join_style=2) if margem > 0 else shape
    if inside.is_empty:
        raise ValueError("a margem não deixa nada para furar")
    return {"painel": {"width": largura, "height": altura, "margin": margem, "thickness": espessura,
                       "shape": shape, "inside": inside}}


# ------------------------------------------------------------------ Padrões
def _keep_inside(panel, xy, clear):
    """The points with `clear` of room to the margin (a hole as big as the pitch stays inside)."""
    import shapely
    if not len(xy):
        return xy
    clear -= 1e-9                        # (a hole touching the margin exactly is still inside)
    area = panel["inside"].buffer(-clear, join_style=2) if clear > 0 else panel["inside"]
    if area.is_empty:
        return xy[:0]
    return xy[shapely.contains_xy(area, xy[:, 0], xy[:, 1])]


def _centred(lo, hi, step):
    """Steps through the middle of lo–hi (a point on the panel's centre), as far as both ends."""
    n = int(math.ceil((hi - lo) / 2.0 / step))
    return (lo + hi) / 2.0 + step * np.arange(-n, n + 1)


def _rotate(xy, degrees, centre):
    if not degrees or not len(xy):
        return xy
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    p = xy - centre
    return np.column_stack((c * p[:, 0] - s * p[:, 1], s * p[:, 0] + c * p[:, 1])) + centre


@r.node("grelha", "Padrões", "Grelha", "Pontos numa grelha quadrada, centrada no painel.",
        inputs=[Port("painel", "panel", "Painel")], outputs=[Port("pontos", "points", "Pontos")],
        params=[_num("passo", "Passo", 0.06, 0.005, 1.0, 0.005),
                Port("disposicao", "choice", "Disposição", default="reta", choices=("reta", "diagonal")),
                _num("rodar", "Rodar", 0.0, -90.0, 90.0, 1.0, "°")],
        example="Passo de 6 cm: furos de até 6 cm encostados.")
def grelha(painel, passo, disposicao, rodar):
    x0, y0, x1, y1 = painel["shape"].bounds
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    big = math.hypot(x1 - x0, y1 - y0) / 2.0 + passo
    xs = _centred(cx - big, cx + big, passo)
    gx, gy = np.meshgrid(xs, xs - cx + cy)        # (rows through the panel's middle too)
    xy = np.column_stack((gx.ravel(), gy.ravel()))
    if disposicao == "diagonal":            # quincôncio: every other row shifted by half the pitch
        row = np.round((gy.ravel() - cy) / passo).astype(int)
        xy[:, 0] += np.where(row % 2 == 1, passo / 2.0, 0.0)
    xy = _rotate(xy, rodar, np.array([cx, cy]))
    return {"pontos": {"panel": painel, "xy": _keep_inside(painel, xy, passo / 2.0), "pitch": passo}}


@r.node("hexagono", "Padrões", "Hexágono", "Pontos em favo: cada um com seis vizinhos à mesma distância.",
        inputs=[Port("painel", "panel", "Painel")], outputs=[Port("pontos", "points", "Pontos")],
        params=[_num("passo", "Passo", 0.06, 0.005, 1.0, 0.005), _num("rodar", "Rodar", 0.0, -90.0, 90.0, 1.0, "°")],
        example="O padrão mais denso: mais área aberta com a mesma ponte.")
def hexagono(painel, passo, rodar):
    x0, y0, x1, y1 = painel["shape"].bounds
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    big = math.hypot(x1 - x0, y1 - y0) / 2.0 + passo
    dy = passo * math.sqrt(3.0) / 2.0
    ys = _centred(cy - big, cy + big, dy)
    xs = _centred(cx - big, cx + big, passo)
    gx, gy = np.meshgrid(xs, ys)
    row = np.arange(len(ys))[:, None].repeat(len(xs), 1)
    gx = gx + np.where(row % 2 == 1, passo / 2.0, 0.0)
    xy = _rotate(np.column_stack((gx.ravel(), gy.ravel())), rodar, np.array([cx, cy]))
    return {"pontos": {"panel": painel, "xy": _keep_inside(painel, xy, passo / 2.0), "pitch": passo}}


@r.node("voronoi", "Padrões", "Voronoi",
        "Pontos soltos e bem espaçados (o centro de cada célula de Voronoi). Com um modulador ligado à "
        "densidade, ficam mais juntos onde ele é forte.",
        inputs=[Port("painel", "panel", "Painel"), Port("densidade", "field", "Densidade", optional=True)],
        outputs=[Port("pontos", "points", "Pontos")],
        params=[Port("quantidade", "int", "Quantidade", default=300, min=5, max=5000, step=1, unit=""),
                Port("semente", "int", "Semente", default=1, min=0, max=9999, step=1, unit=""),
                Port("relaxar", "int", "Relaxar", default=3, min=0, max=10, step=1, unit="")],
        example="300 pontos, mais densos no centro com um Atrator na densidade.")
def voronoi(painel, densidade, quantidade, semente, relaxar):
    import shapely
    rng = np.random.default_rng(semente)
    inside = painel["inside"]
    x0, y0, x1, y1 = inside.bounds

    def sample(n):                       # points in the inside, as many where the density is strong
        out = np.empty((0, 2))
        for _ in range(60):
            p = rng.uniform((x0, y0), (x1, y1), size=(max(4 * n, 64), 2))
            p = p[shapely.contains_xy(inside, p[:, 0], p[:, 1])]
            if densidade is not None and len(p):
                p = p[rng.uniform(size=len(p)) < 0.05 + 0.95 * densidade(p)]
            out = np.vstack((out, p))
            if len(out) >= n:
                return out[:n]
        return out

    seeds = sample(quantidade)
    if not len(seeds):
        raise ValueError("não cabem pontos no painel")
    if relaxar:                          # Lloyd: each point to the middle of its cell (cells from many samples)
        dense = sample(min(40 * len(seeds), 60000))
        for _ in range(relaxar):
            near = _nearest(dense, seeds)
            sums = np.zeros_like(seeds)
            np.add.at(sums, near, dense)
            count = np.bincount(near, minlength=len(seeds))[:, None]
            seeds = np.where(count > 0, sums / np.maximum(count, 1), seeds)
    pitch = math.sqrt(inside.area / len(seeds))
    if len(seeds) > 1:
        pitch = min(pitch, float(np.median(_neighbour_gap(seeds))))
    return {"pontos": {"panel": painel, "xy": seeds, "pitch": pitch}}


def _nearest(points, seeds, chunk=4096):
    out = np.empty(len(points), dtype=int)
    for i in range(0, len(points), chunk):
        p = points[i:i + chunk]
        d = ((p[:, None, :] - seeds[None, :, :]) ** 2).sum(-1)
        out[i:i + chunk] = d.argmin(1)
    return out


def _neighbour_gap(xy, chunk=2048):
    """Each point's distance to its nearest other point."""
    out = np.empty(len(xy))
    for i in range(0, len(xy), chunk):
        d = ((xy[i:i + chunk, None, :] - xy[None, :, :]) ** 2).sum(-1)
        d[np.arange(len(d)), np.arange(i, i + len(d))] = np.inf
        out[i:i + chunk] = np.sqrt(d.min(1))
    return out


# ------------------------------------------------------------------ Moduladores
@r.node("atrator", "Moduladores", "Atrator", "Forte (1) junto ao ponto, a enfraquecer até ao raio.",
        outputs=[Port("campo", "field", "Campo")],
        params=[_num("x", "Posição X", 1.5, -50.0, 50.0, 0.01), _num("y", "Posição Y", 0.6, -50.0, 50.0, 0.01),
                _num("raio", "Raio", 1.0, 0.01, 50.0, 0.01),
                Port("suave", "bool", "Suave", default=True), Port("inverter", "bool", "Inverter", default=False)],
        example="Os furos crescem junto ao ponto (1,5; 0,6).")
def atrator(x, y, raio, suave, inverter):
    def fn(xy):
        t = np.clip(np.hypot(xy[:, 0] - x, xy[:, 1] - y) / raio, 0.0, 1.0)
        v = 1.0 - (t * t * (3.0 - 2.0 * t) if suave else t)
        return 1.0 - v if inverter else v
    return {"campo": Field(fn, "atrator")}


@r.node("gradiente", "Moduladores", "Gradiente", "De 0 a 1 de um lado ao outro do painel, na direção escolhida.",
        inputs=[Port("painel", "panel", "Painel")], outputs=[Port("campo", "field", "Campo")],
        params=[_num("angulo", "Direção", 0.0, -180.0, 180.0, 1.0, "°"),
                _num("inicio", "Início", 0.0, 0.0, 1.0, 0.01, ""), _num("fim", "Fim", 1.0, 0.0, 1.0, 0.01, "")],
        example="0°: furos pequenos à esquerda, grandes à direita.")
def gradiente(painel, angulo, inicio, fim):
    a = math.radians(angulo)
    d = np.array([math.cos(a), math.sin(a)])
    x0, y0, x1, y1 = painel["shape"].bounds
    corners = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    proj = corners @ d
    lo, hi = proj.min(), proj.max()

    def fn(xy):
        t = (xy @ d - lo) / max(hi - lo, 1e-9)
        return inicio + (fim - inicio) * t
    return {"campo": Field(fn, "gradiente")}


@r.node("imagem", "Moduladores", "Imagem (luminância)",
        "Uma fotografia sobre o painel, a cobri-lo como numa moldura: escuro = 1 (furos grandes).",
        inputs=[Port("painel", "panel", "Painel")], outputs=[Port("campo", "field", "Campo")],
        params=[Port("ficheiro", "text", "Imagem", default=""), Port("inverter", "bool", "Inverter", default=False),
                _num("contraste", "Contraste", 1.0, 0.1, 5.0, 0.05, "")],
        example="Um rosto ou uma paisagem a aparecer nos furos.")
def imagem(painel, ficheiro, inverter, contraste):
    if not ficheiro:
        raise ValueError("escolha uma imagem")
    from ...model import image_masks
    from .. import surfaces
    dark = image_masks.load(ficheiro)
    if dark is None:
        raise ValueError(f"imagem não encontrada: {ficheiro}")
    bounds = painel["shape"].bounds

    def fn(xy):
        v = surfaces.darkness(dark, bounds, xy)
        v = np.clip((v - 0.5) * contraste + 0.5, 0.0, 1.0)
        return 1.0 - v if inverter else v
    return {"campo": Field(fn, "imagem")}


@r.node("ruido", "Moduladores", "Ruído", "Manchas suaves ao acaso (do tamanho da escala).",
        outputs=[Port("campo", "field", "Campo")],
        params=[_num("escala", "Escala", 0.5, 0.02, 20.0, 0.01),
                Port("semente", "int", "Semente", default=1, min=0, max=9999, step=1, unit=""),
                Port("camadas", "int", "Detalhe", default=2, min=1, max=5, step=1, unit="")],
        example="Uma textura orgânica, como folhagem.")
def ruido(escala, semente, camadas):
    rng = np.random.default_rng(semente)
    tables = [rng.uniform(size=(256, 256)) for _ in range(camadas)]

    def layer(xy, table, s):
        p = xy / s
        i = np.floor(p).astype(int)
        f = p - i
        f = f * f * (3.0 - 2.0 * f)
        a, b = i[:, 0] % 256, i[:, 1] % 256
        a1, b1 = (a + 1) % 256, (b + 1) % 256
        top = table[a, b] * (1 - f[:, 0]) + table[a1, b] * f[:, 0]
        bot = table[a, b1] * (1 - f[:, 0]) + table[a1, b1] * f[:, 0]
        return top * (1 - f[:, 1]) + bot * f[:, 1]

    def fn(xy):
        total, weight = np.zeros(len(xy)), 0.0
        for k, table in enumerate(tables):
            w = 0.5 ** k
            total += w * layer(xy, table, escala / 2 ** k)
            weight += w
        return total / weight
    return {"campo": Field(fn, "ruído")}


# ------------------------------------------------------------------ Operações
SHAPES = ("redondo", "quadrado", "hexagonal", "triangular", "losango", "ranhura")     # (0.545: the last three)


def hole_extras(furos):
    """(0.545) (angle (n,) °, ratio (n,)) of holes: each one's turn and stretch (none: 0 and 1)."""
    n = len(furos["xy"])
    angle, ratio = furos.get("angle"), furos.get("ratio")
    return (np.zeros(n) if angle is None else np.asarray(angle, dtype=float),
            np.ones(n) if ratio is None else np.asarray(ratio, dtype=float))


def take_holes(furos, keep, **changes):
    """Holes chosen (`keep`: a mask or indices), all that each carries going with it; not checked any more."""
    angle, ratio = hole_extras(furos)
    out = dict(furos, xy=furos["xy"][keep], d=furos["d"][keep], angle=angle[keep], ratio=ratio[keep])
    out.update(changes)
    out["bad"] = np.zeros(len(out["xy"]), dtype=bool)
    return out


@r.node("perfurar", "Operações", "Perfurar",
        "Um furo em cada ponto. Sem modulador, todos do tamanho máximo; com ele, entre o mínimo e o máximo. O "
        "tamanho é o diâmetro do círculo, o lado do quadrado ou do triângulo, a largura do hexágono ou da ranhura, a "
        "diagonal do losango. «Alongar» estica o furo (a ranhura: o comprimento sobre a largura); «Rodar» vira-o.",
        inputs=[Port("pontos", "points", "Pontos"), Port("campo", "field", "Modulador", optional=True)],
        outputs=[Port("furos", "holes", "Furos")],
        params=[_num("d_min", "Tamanho mínimo", 0.0, 0.0, 0.2, 0.001),
                _num("d_max", "Tamanho máximo", 0.03, 0.001, 0.2, 0.001),
                Port("forma", "choice", "Forma", default="redondo", choices=SHAPES),
                Port("inverter", "bool", "Inverter", default=False),
                _num("sem_furo", "Sem furo abaixo de", MIN_CUT, MIN_CUT, 0.05, 0.0005),
                _num("alongar", "Alongar", 1.0, 1.0, 12.0, 0.05, "×"),
                _num("rodar", "Rodar", 0.0, -180.0, 180.0, 1.0, "°")],
        example="Ranhuras de 8 × 32 mm (alongar 4) a 45°.")
def perfurar(pontos, campo, d_min, d_max, forma, inverter, sem_furo=MIN_CUT, alongar=1.0, rodar=0.0):
    xy = pontos["xy"]
    if campo is None:
        f = np.ones(len(xy))
    else:
        f = campo(xy)
        if inverter:
            f = 1.0 - f
    lo, hi = min(d_min, d_max), max(d_min, d_max)
    d = lo + (hi - lo) * f
    keep = d >= max(MIN_CUT, sem_furo)       # (0.540: those smaller not cut at all — the picture's light parts)
    n = int(keep.sum())
    return {"furos": {"panel": pontos["panel"], "xy": xy[keep], "d": d[keep], "shape": forma,
                      "pitch": pontos["pitch"], "bad": np.zeros(n, dtype=bool),
                      "angle": np.full(n, float(rodar)), "ratio": np.full(n, float(alongar))}}


# ------------------------------------------------------------------ Fabrico
def _radius_out(shape, d, ratio=None):
    """How far a hole reaches from its centre at most (a square's corner, a hexagon's; 0.545: a slot's end)."""
    from .. import surfaces
    return surfaces.hole_reach(shape, d, ratio)


def _close_pairs(xy, reach):
    """(i, j, distance) of every pair closer than `reach` (points hashed into cells of that size)."""
    if len(xy) < 2 or reach <= 0:
        return np.empty(0, int), np.empty(0, int), np.empty(0)
    cell = np.floor(xy / reach).astype(np.int64)
    buckets = {}
    for k, c in enumerate(map(tuple, cell)):
        buckets.setdefault(c, []).append(k)
    I, J = [], []
    for (cx, cy), members in buckets.items():
        a = np.array(members)
        for dx, dy in ((0, 0), (1, -1), (1, 0), (1, 1), (0, 1)):
            other = buckets.get((cx + dx, cy + dy))
            if other is None:
                continue
            b = np.array(other)
            ii, jj = np.meshgrid(a, b, indexing="ij")
            ii, jj = ii.ravel(), jj.ravel()
            if dx == 0 and dy == 0:
                m = ii < jj
                ii, jj = ii[m], jj[m]
            I.append(ii)
            J.append(jj)
    if not I:
        return np.empty(0, int), np.empty(0, int), np.empty(0)
    I, J = np.concatenate(I), np.concatenate(J)
    dist = np.hypot(*(xy[I] - xy[J]).T)
    m = dist < reach
    return I[m], J[m], dist[m]


@r.node("verificar_fabrico", "Fabrico", "Verificar fabrico",
        "Marca a vermelho os furos que não se fabricam: menores que o furo mínimo, pontes entre furos mais finas que "
        "a ponte mínima, ou a invadir a margem.",
        inputs=[Port("furos", "holes", "Furos")],
        outputs=[Port("furos", "holes", "Furos"), Port("relatorio", "report", "Relatório")],
        params=[_num("furo_min", "Furo mínimo", 0.003, 0.0005, 0.1, 0.0005),
                _num("ponte_min", "Ponte mínima", 0.003, 0.0005, 0.1, 0.0005)],
        example="Regra prática: furo e ponte nunca menores que a espessura da chapa.")
def verificar_fabrico(furos, furo_min, ponte_min):
    import shapely
    from .. import surfaces
    xy, d, shape, panel = furos["xy"], furos["d"], furos["shape"], furos["panel"]
    ratio = hole_extras(furos)[1]
    reach = _radius_out(shape, d, ratio) if len(d) else np.zeros(0)
    small = d < furo_min
    bad = small.copy()
    min_bridge = math.inf
    if len(xy) > 1:                       # (round holes exact; the others by their outer circle: on the safe side)
        # (as far as the next point too, so the thinnest bridge is known even when all are fine)
        I, J, dist = _close_pairs(xy, max(2.0 * float(reach.max()) + ponte_min, 1.01 * furos.get("pitch", 0.0)))
        if len(I):
            bridge = dist - reach[I] - reach[J]
            min_bridge = float(bridge.min())
            thin = bridge < ponte_min
            bad[I[thin]] = True
            bad[J[thin]] = True
            bridges = int(thin.sum())
        else:
            bridges = 0
    else:
        bridges = 0
    edge = np.zeros(len(xy), dtype=bool)
    if len(xy):
        to_edge = shapely.distance(panel["inside"].boundary, shapely.points(xy))
        within = shapely.contains_xy(panel["inside"], xy[:, 0], xy[:, 1])
        edge = ~within | (to_edge < reach)
        bad |= edge
    open_area = float(surfaces.hole_area(shape, d, ratio).sum() / max(panel["shape"].area, 1e-12))
    problems = []
    if small.any():
        problems.append(f"{int(small.sum())} furos menores que {furo_min * 1000:.1f} mm")
    if bridges:
        problems.append(f"{bridges} pontes mais finas que {ponte_min * 1000:.1f} mm")
    if edge.any():
        problems.append(f"{int(edge.sum())} furos a invadir a margem")
    report = {"ok": not bad.any(), "holes": int(len(xy)), "bad": int(bad.sum()), "small": int(small.sum()),
              "bridges": bridges, "edge": int(edge.sum()), "open_area": open_area,
              "min_bridge": None if min_bridge == math.inf else min_bridge, "problems": problems}
    return {"furos": {**furos, "bad": bad}, "relatorio": report}


def hole_outline(shape, cx, cy, d):
    """The corners of a square or hexagonal hole (mm or m: the units of the arguments)."""
    if shape == "quadrado":
        h = d / 2.0
        return [(cx + h, cy + h), (cx - h, cy + h), (cx - h, cy - h), (cx + h, cy - h)]
    rr = d / math.sqrt(3.0)              # hexagon: `d` between flat sides, flats top and bottom
    return [(cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))) for a in range(0, 360, 60)]


def dxf_text(furos, name="Painel"):
    """The CNC's DXF (mm): CONTORNO (the panel), FUROS (one circle or polyline each), TEXTOS."""
    from ...model import dxf
    w = dxf._Writer()
    panel = furos["panel"]
    for part in getattr(panel["shape"], "geoms", [panel["shape"]]):     # (0.542: modules too)
        for ring in [part.exterior, *part.interiors]:
            w.polyline("CONTORNO", [(x * 1000.0, y * 1000.0) for x, y in ring.coords[:-1]], closed=True)
    from .. import surfaces
    shape = furos["shape"]
    angle, ratio = hole_extras(furos)
    for k, ((x, y), d) in enumerate(zip(furos["xy"], furos["d"])):
        cx, cy, dd = x * 1000.0, y * 1000.0, d * 1000.0
        plain = abs(angle[k]) < 1e-9 and abs(ratio[k] - 1.0) < 1e-9
        if shape == "redondo" and plain:
            w.circle("FUROS", (cx, cy), dd / 2.0)
        elif shape in ("quadrado", "hexagonal") and plain:
            w.polyline("FUROS", hole_outline(shape, cx, cy, dd), closed=True)
        else:                                     # (0.545) turned, stretched, a triangle, a lozenge, a slot
            ring = surfaces.hole_rings(shape, [(cx, cy)], [dd], [angle[k]], [ratio[k]])[0]
            w.polyline("FUROS", [tuple(p) for p in ring], closed=True)
    text = 0.02 * 1000.0
    w.text("TEXTOS", (0.0, -2 * text), text, name)
    w.text("TEXTOS", (0.0, -3.5 * text), text, "{:.0f} × {:.0f} mm — {} furos".format(
        panel["width"] * 1000.0, panel["height"] * 1000.0, len(furos["xy"])))
    return w.document({"CONTORNO": 7, "FUROS": 1, "TEXTOS": 3})


@r.node("exportar_dxf", "Fabrico", "Exportar DXF",
        "Grava o desenho de corte em milímetros: camadas CONTORNO, FUROS e TEXTOS.",
        inputs=[Port("furos", "holes", "Furos")], outputs=[Port("ficheiro", "file", "Ficheiro")],
        params=[Port("ficheiro", "text", "Gravar em", default=""), Port("nome", "text", "Nome", default="Painel")],
        example="painel-fachada-sul.dxf para a máquina de corte.")
def exportar_dxf(furos, ficheiro, nome):
    if not ficheiro:
        raise ValueError("escolha onde gravar o DXF")
    with open(ficheiro, "w", encoding="utf-8") as f:
        f.write(dxf_text(furos, nome))
    return {"ficheiro": ficheiro}


# ------------------------------------------------------------------ BIM
def cladding_pattern(bim):
    """(0.540) The perforated finish's measures for `bim.add_cladding(doc, wall, side, "perfurado", height, …)`
    from what «Aplicar à parede/fachada» hands over: its holes kept as free holes, its panel as the boards."""
    from .. import surfaces
    p = bim["panel"]
    return {"free": surfaces.free_text(bim["shape"], bim["holes"]), "free_repeat": 1.0 if bim["repeat"] else 0.0,
            "sheet_w": p["width"], "sheet_h": p["height"], "margin": p["margin"], "joint": 0.0,
            "thickness": p["thickness"]}


@r.node("aplicar_parede", "BIM", "Aplicar à parede/fachada",
        "Põe o painel perfurado como revestimento na parede escolhida (com quantidades e IFC).",
        inputs=[Port("furos", "holes", "Furos")], outputs=[Port("bim", "bim", "BIM")],
        params=[Port("parede", "text", "Parede (GlobalId)", default=""),
                Port("lado", "choice", "Lado", default="frente", choices=("frente", "trás")),
                Port("repetir", "bool", "Repetir pela parede", default=True)],
        example="O mesmo painel repetido ao longo da fachada sul.")
def aplicar_parede(furos, parede, lado, repetir):
    panel = furos["panel"]
    return {"bim": {"wall": parede, "side": lado, "repeat": repetir,
                    "panel": {"width": panel["width"], "height": panel["height"], "margin": panel["margin"],
                              "thickness": panel["thickness"]},
                    "shape": furos["shape"],
                    "holes": _hole_rows(furos)}}


def _hole_rows(furos):
    """(x, y, d) of each hole — (x, y, d, angle, ratio) of those turned or stretched (0.545)."""
    angle, ratio = hole_extras(furos)
    out = []
    for k, ((x, y), d) in enumerate(zip(furos["xy"], furos["d"])):
        row = (float(x), float(y), float(d))
        if abs(angle[k]) > 1e-9 or abs(ratio[k] - 1.0) > 1e-9:
            row += (float(angle[k]), float(ratio[k]))
        out.append(row)
    return out
