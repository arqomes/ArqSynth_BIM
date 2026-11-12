"""(0.558, PLANO.md «Gerador de formas orgânicas», step 7) The Visual Graph's organic nodes: a form found over a panel's
outline (membrane, cushion, catenary, smoothing — core/form_finding), and the panel's holes laid on that form — to see
a perforated canopy before making it (in the model: Forma orgânica, then a Visual Graph operator applied to it)."""

import numpy as np

from .nodes_panels import _num, hole_extras, r
from .registry import Port

BEHAVIOURS = ("catenaria", "almofada", "membrana", "suavizar")


def _outline(panel):
    shape = panel["shape"]
    q = max(getattr(shape, "geoms", [shape]), key=lambda g: g.area)
    return np.asarray(q.exterior.coords)[:-1]


@r.node("forma_organica", "Orgânico", "Forma orgânica",
        "Encontra a forma sobre o contorno do painel: catenária (casca à compressão), almofada (inflada), membrana "
        "(com um mastro ao centro) ou suavizar. «Bordos livres»: só os cantos presos, os bordos em arco.",
        inputs=[Port("painel", "panel", "Painel")], outputs=[Port("malha", "mesh", "Forma")],
        params=[Port("comportamento", "choice", "Comportamento", default="catenaria", choices=BEHAVIOURS),
                _num("altura", "Altura", 1.0, -20.0, 20.0, 0.05),
                Port("divisoes", "int", "Divisões", default=24, min=6, max=64, step=1, unit=""),
                Port("bordos_livres", "bool", "Bordos livres", default=False)],
        example="Uma pala de 3 × 1,2 m que sobe 40 cm em catenária.")
def forma_organica(painel, comportamento, altura, divisoes, bordos_livres):
    from .. import param_surface as ps
    ring = np.column_stack((_outline(painel), np.zeros(len(_outline(painel)))))
    data = ps.default_definition("organic")
    data["curves"] = [{"id": "c1", "points": ring.tolist(), "closed": True}]
    data["surface"].update(boundary="c1", behaviour=comportamento, height=float(altura), u=int(divisoes),
                           v=int(divisoes), free_edges=bool(bordos_livres))
    try:
        surface = ps.Surface(data)
    except ps.SurfaceError as exc:
        raise ValueError(str(exc)) from None
    verts, tris = surface.triangles()
    return {"malha": {"verts": verts, "tris": tris, "panel": painel, "rows": surface.rows}}


def _heights(form, xy):
    """The form's height over each plan point (its triangle's, by barycentric weights; outside it: 0)."""
    v, t = np.asarray(form["verts"], float), np.asarray(form["tris"])
    z = np.zeros(len(xy))
    done = np.zeros(len(xy), dtype=bool)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    lo = np.minimum(np.minimum(a, b), c)[:, :2]
    hi = np.maximum(np.maximum(a, b), c)[:, :2]
    order = np.argsort(xy[:, 0])
    xs = xy[order, 0]
    for k in range(len(t)):
        i0, i1 = np.searchsorted(xs, lo[k, 0] - 1e-9), np.searchsorted(xs, hi[k, 0] + 1e-9, side="right")
        if i0 >= i1:
            continue
        idx = order[i0:i1]
        idx = idx[~done[idx]]
        p = xy[idx]
        inside = (p[:, 1] >= lo[k, 1] - 1e-9) & (p[:, 1] <= hi[k, 1] + 1e-9)
        if not inside.any():
            continue
        idx, p = idx[inside], p[inside]
        e1, e2, w = b[k, :2] - a[k, :2], c[k, :2] - a[k, :2], p - a[k, :2]
        den = e1[0] * e2[1] - e1[1] * e2[0]
        if abs(den) < 1e-14:
            continue
        s = (w[:, 0] * e2[1] - w[:, 1] * e2[0]) / den
        u = (e1[0] * w[:, 1] - e1[1] * w[:, 0]) / den
        hit = (s >= -1e-9) & (u >= -1e-9) & (s + u <= 1 + 1e-9)
        z[idx[hit]] = a[k, 2] + s[hit] * (b[k, 2] - a[k, 2]) + u[hit] * (c[k, 2] - a[k, 2])
        done[idx[hit]] = True
    return z


@r.node("furos_na_forma", "Orgânico", "Furos sobre a forma",
        "A chapa perfurada posta sobre a forma orgânica: cada furo no sítio da planta, a chapa a seguir a forma.",
        inputs=[Port("furos", "holes", "Furos"), Port("malha", "mesh", "Forma")],
        outputs=[Port("malha", "mesh", "Chapa")],
        params=[_num("espessura", "Espessura (0 = a do painel)", 0.0, 0.0, 0.2, 0.0005)],
        example="Uma pala perfurada que segue a catenária.")
def furos_na_forma(furos, malha, espessura):
    from shapely.geometry.polygon import orient

    from .. import surfaces
    panel = furos["panel"]
    shape = panel["shape"]
    shape = orient(shape, 1.0) if shape.geom_type == "Polygon" else shape
    found = [(shape, furos["xy"], surfaces.with_extras(furos["d"], *hole_extras(furos)))]
    verts, tris = surfaces.free_mesh(shape, espessura or panel["thickness"], found, furos["shape"])
    if len(tris) > 400000:
        raise ValueError("chapa pesada demais: menos furos")
    lifted = verts.copy()
    lifted[:, 2] += _heights(malha, verts[:, :2])
    return {"malha": {"verts": lifted, "tris": tris, "panel": panel}}
