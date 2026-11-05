"""Spot heights (0.156, Phase 7, step 3 — as Revit's spot elevation): a mark drawn in a view (an annotation of kind
"spot") whose text is worked out whenever it is drawn, so it is always the model's — in a plan, the height of the
highest surface under it that the plan sees (a terrain, a slab, a step: under its cut); in a section or an
elevation, the height of the point clicked. Written as architects do: "+12,35", "-1,20", "±0,00"."""

import numpy as np

UP = 0.05                       # a triangle facing up at least this much is a surface one stands on


def heights_at(verts, tris, normals, xy):
    """The heights of the faces facing up of a mesh over the plan point xy (all of them: a stair has many)."""
    verts, tris = np.asarray(verts, dtype=float), np.asarray(tris, dtype=np.int64)
    if not len(tris):
        return np.zeros(0)
    keep = np.asarray(normals)[:, 2] > UP
    p = verts[tris[keep]]
    if not len(p):
        return np.zeros(0)
    x, y = float(xy[0]), float(xy[1])
    a, b, c = p[:, 0], p[:, 1], p[:, 2]
    det = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    ok = np.abs(det) > 1e-15
    det = np.where(ok, det, 1.0)
    l1 = ((b[:, 1] - c[:, 1]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (y - c[:, 1])) / det
    l2 = ((c[:, 1] - a[:, 1]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (y - c[:, 1])) / det
    l3 = 1.0 - l1 - l2
    inside = ok & (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
    return (l1 * a[:, 2] + l2 * b[:, 2] + l3 * c[:, 2])[inside]


def surface_height(objects, xy, top=None):
    """The highest surface facing up under xy among these objects (BimObjects: world meshes) — under `top` when
    given — or None."""
    best = None
    for obj in objects:
        mesh = obj.mesh
        box = mesh.bounds() if hasattr(mesh, "bounds") else None
        if box is None or not (box[0][0] - 1e-6 <= xy[0] <= box[1][0] + 1e-6
                               and box[0][1] - 1e-6 <= xy[1] <= box[1][1] + 1e-6):
            continue
        if not hasattr(mesh, "normals"):
            continue
        found = heights_at(mesh.verts, mesh.tris, mesh.normals, xy)
        if top is not None:
            found = found[found <= top + 1e-6]
        if len(found):
            h = float(found.max())
            best = h if best is None or h > best else best
    return best


def text(height, sep=","):
    """+12,35 / -1,20 / ±0,00."""
    if abs(height) < 0.005:
        return "±0" + sep + "00"
    return "{:+.2f}".format(height).replace(".", sep)


def spot_height(doc, ann):
    """The height an annotation of kind "spot" marks now (m)."""
    point = np.asarray(ann.points[0], dtype=float)
    view = tuple(ann.view) if ann.view else ()
    if view and view[0] == "plan":
        storey = view[1]
        try:
            settings = doc.view_settings(("plan", storey))
            cut = float(settings.cut_height)
        except Exception:
            cut = 1.2
        level = next((z for g, _n, z in doc.storeys() if g == storey), 0.0)
        objects = [o for o in doc.objects.values() if o.is_bim and o.storey in (storey, None)]
        found = surface_height(objects, point[:2], level + cut)
        return found if found is not None else float(level)
    return float(point[2])
