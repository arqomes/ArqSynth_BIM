"""(0.542) The Visual Graph's nodes in 3D and from the model (PLANO.md, «Gráfico Visual», step 5): Subdividir (a
panel in modules with joints), Extrudir (the perforated sheet as a solid), Relevo (a field raised or sunk on the
sheet), Dobrar (a flange folded along a line), Fachada do modelo (a wall's face — less its doors and windows — as
the panel).

A "mesh" is {"verts": (n, 3) (x, y along the panel, z out of it), "tris": (m, 3), "panel"}."""

import math

import numpy as np

from .nodes_panels import _num, r
from .registry import Port

# The model the «Fachada do modelo» node reads: set by the window (and the MCP) — {"doc": Document | None}.
MODEL = {"doc": None}


def rings(shape):
    """Every outline of a shape (a polygon or several): their coordinates."""
    for part in getattr(shape, "geoms", [shape]):
        yield part.exterior.coords
        for hole in part.interiors:
            yield hole.coords


def _panel(shape, margin, thickness):
    x0, y0, x1, y1 = shape.bounds
    inside = shape.buffer(-margin, join_style=2) if margin > 0 else shape
    if inside.is_empty:
        raise ValueError("a margem não deixa nada para furar")
    return {"width": x1 - x0, "height": y1 - y0, "margin": margin, "thickness": thickness, "shape": shape,
            "inside": inside}


# ------------------------------------------------------------------ Base
def example_face():
    """(0.541) The face worked on when no wall is chosen: 4 × 2,7 m with a window — an operator of the library is
    seen (and drawn in its thumbnail) on it."""
    from shapely.geometry import box
    return box(0.0, 0.0, 4.0, 2.7).difference(box(1.4, 0.9, 2.6, 2.1))


def wall_face(doc, wall):
    """(0.541) A wall's face — less its doors and windows — in its own measures (x along it from its start, y up
    from its base). ValueError where the wall is gone."""
    from shapely.geometry import box
    if doc is None or doc.ifc.by_guid(wall) is None or doc.ifc.kind_of(wall) != "wall":
        raise ValueError("essa parede já não existe")
    frame = doc.ifc.element_frame(wall)
    face = box(0.0, 0.0, frame.length, frame.height)
    for _gid, lo, hi, _filled, _box in doc.ifc.voids(wall):
        face = face.difference(box(lo[0] - frame.x0, lo[2] - frame.z0, hi[0] - frame.x0, hi[2] - frame.z0))
    return face


def target_face(wall):
    """The face of the wall the graph works on (MODEL's) — or the example one (no wall chosen, no model)."""
    if wall and MODEL["doc"] is not None:
        return wall_face(MODEL["doc"], wall)
    return example_face()


@r.node("fachada_bim", "Base", "Superfície do modelo",
        "A face da parede escolhida no modelo, já sem as portas e as janelas. Sem parede escolhida: uma face de "
        "exemplo, de 4 × 2,7 m com uma janela.",
        outputs=[Port("painel", "panel", "Superfície")],
        params=[Port("parede", "text", "Parede (GlobalId)", default=""),
                _num("margem", "Margem", 0.05, 0.0, 1.0, 0.005),
                _num("espessura", "Espessura", 0.003, 0.0005, 0.1, 0.0005),
                Port("lado", "choice", "Face", default="frente", choices=("frente", "trás"))],
        example="A fachada sul, perfurada à volta das janelas.")
def fachada_bim(parede, margem, espessura, lado="frente"):
    face = target_face(parede)
    if lado == "trás":                  # (0.546) as it is seen standing before that face: left and right swapped
        face = mirrored(face)
    return {"painel": dict(_panel(face, margem, espessura), mirror=lado == "trás")}


def mirrored(shape):
    """A face seen from its other side: turned about the upright line through its middle."""
    from shapely import affinity
    x0, _y0, x1, _y1 = shape.bounds
    return affinity.scale(shape, xfact=-1.0, yfact=1.0, origin=((x0 + x1) / 2.0, 0.0))


# ------------------------------------------------------------------ Operações
@r.node("subdividir", "Operações", "Subdividir",
        "O painel em módulos iguais, com uma junta entre eles (cada módulo com a sua margem).",
        inputs=[Port("painel", "panel", "Painel")], outputs=[Port("painel", "panel", "Módulos")],
        params=[Port("colunas", "int", "Colunas", default=3, min=1, max=40, step=1, unit=""),
                Port("linhas", "int", "Linhas", default=1, min=1, max=40, step=1, unit=""),
                _num("junta", "Junta", 0.01, 0.0, 0.2, 0.001)],
        example="Uma fachada de 9 m em 6 chapas de 1,5 m com juntas de 1 cm.")
def subdividir(painel, colunas, linhas, junta):
    from shapely.geometry import MultiPolygon, box
    x0, y0, x1, y1 = painel["shape"].bounds
    w, h = (x1 - x0) / colunas, (y1 - y0) / linhas
    parts = []
    for i in range(colunas):
        for j in range(linhas):
            cell = box(x0 + i * w + junta / 2, y0 + j * h + junta / 2, x0 + (i + 1) * w - junta / 2,
                       y0 + (j + 1) * h - junta / 2).intersection(painel["shape"])
            parts += [q for q in getattr(cell, "geoms", [cell]) if q.geom_type == "Polygon" and q.area > 1e-6]
    if not parts:
        raise ValueError("a junta não deixa módulos")
    shape = MultiPolygon(parts)
    inside = MultiPolygon([q for q in (p.buffer(-painel["margin"], join_style=2) for p in parts)
                           if q.geom_type == "Polygon" and not q.is_empty]) if painel["margin"] > 0 else shape
    if inside.is_empty:
        raise ValueError("a margem não deixa nada para furar")
    out = dict(painel, shape=shape, inside=inside, modules=len(parts))
    return {"painel": out}


@r.node("extrudir", "Operações", "Extrudir",
        "A chapa perfurada como sólido 3D, da espessura do painel (ou outra).",
        inputs=[Port("furos", "holes", "Furos")], outputs=[Port("malha", "mesh", "Sólido")],
        params=[_num("espessura", "Espessura (0 = a do painel)", 0.0, 0.0, 0.2, 0.0005)],
        example="Ver o painel em 3D antes de o pôr na parede.")
def extrudir(furos, espessura):
    from shapely.geometry.polygon import orient

    from .. import surfaces
    panel = furos["panel"]
    t = espessura or panel["thickness"]
    shape = panel["shape"]
    shape = orient(shape, 1.0) if shape.geom_type == "Polygon" else shape
    from .nodes_panels import hole_extras
    found = [(shape, furos["xy"], surfaces.with_extras(furos["d"], *hole_extras(furos)))]   # (0.545: turned…)
    verts, tris = surfaces.free_mesh(shape, t, found, furos["shape"])
    if len(tris) > 400000:
        raise ValueError("sólido pesado demais: menos furos")
    return {"malha": {"verts": verts, "tris": tris, "panel": panel}}


@r.node("relevo", "Operações", "Relevo",
        "A chapa com saliências (ou reentrâncias) a seguir um modulador, sem furos: como uma chapa estampada.",
        inputs=[Port("painel", "panel", "Painel"), Port("campo", "field", "Modulador")],
        outputs=[Port("malha", "mesh", "Superfície")],
        params=[_num("altura", "Altura", 0.02, -0.3, 0.3, 0.001), _num("resolucao", "Resolução", 0.02, 0.005, 0.2,
                                                                          0.005)],
        example="Um muro com ondas a seguir uma imagem.")
def relevo(painel, campo, altura, resolucao):
    import shapely
    x0, y0, x1, y1 = painel["shape"].bounds
    nx = max(2, int(math.ceil((x1 - x0) / resolucao)) + 1)
    ny = max(2, int(math.ceil((y1 - y0) / resolucao)) + 1)
    if nx * ny > 250000:
        raise ValueError("resolução fina demais para este painel")
    X, Y = np.meshgrid(np.linspace(x0, x1, nx), np.linspace(y0, y1, ny))
    xy = np.column_stack((X.ravel(), Y.ravel()))
    z = campo(xy) * altura
    inside = shapely.contains_xy(painel["inside"].buffer(1e-9), xy[:, 0], xy[:, 1])
    z = np.where(inside, z, 0.0) + painel["thickness"]
    verts = np.column_stack((xy, z))
    i = np.arange(nx * ny).reshape(ny, nx)
    a, b, c, d = i[:-1, :-1].ravel(), i[:-1, 1:].ravel(), i[1:, 1:].ravel(), i[1:, :-1].ravel()
    tris = np.concatenate([np.column_stack((a, b, c)), np.column_stack((a, c, d))])
    centre = verts[tris].mean(1)[:, :2]                   # (only what is on the panel: its openings left out)
    keep = shapely.contains_xy(painel["shape"].buffer(resolucao * 0.5), centre[:, 0], centre[:, 1])
    return {"malha": {"verts": verts, "tris": tris[keep], "panel": painel}}


@r.node("dobrar", "Operações", "Dobrar",
        "Dobra a chapa ao longo de uma linha vertical ou horizontal: a parte além da linha roda pelo ângulo.",
        inputs=[Port("malha", "mesh", "Sólido")], outputs=[Port("malha", "mesh", "Dobrado")],
        params=[Port("eixo", "choice", "Linha", default="vertical", choices=("vertical", "horizontal")),
                _num("posicao", "Posição", 0.1, 0.0, 50.0, 0.005), _num("angulo", "Ângulo", 90.0, -180.0, 180.0, 1.0,
                                                                         "°"),
                Port("lado", "choice", "Parte que dobra", default="início", choices=("início", "fim"))],
        example="Abas de 10 cm a 90° para fixar a chapa.")
def dobrar(malha, eixo, posicao, angulo, lado):
    v = np.array(malha["verts"], dtype=float)
    k = 0 if eixo == "vertical" else 1                    # (a vertical line: x is what changes)
    lo = malha["panel"]["shape"].bounds[k]
    line = lo + posicao
    s = v[:, k] - line
    part = s < 0 if lado == "início" else s > 0
    a = math.radians(angulo) * (1 if lado == "fim" else -1)
    c, sn = math.cos(a), math.sin(a)
    u, w = s[part], v[part, 2]
    v[part, k] = line + u * c - w * sn
    v[part, 2] = u * sn + w * c
    return {"malha": dict(malha, verts=v)}
