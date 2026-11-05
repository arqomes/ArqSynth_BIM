"""(0.399) What a dimension is taken to on a wall — Revit's «Preferência» of a dimension (the owner, 2026-11-05:
«precisa ter opção de cotar acabamento externo, núcleo da parede, eixos da parede etc.»):
- the finish faces — the wall's outer and inner faces, as built (its plaster on);
- the core's faces — its structure's (its layer whose function in its type is «Estrutura», else its thickest): the
  dimensions «em osso», without the finishes;
- its axis;
- the core's axis (the middle of its structure).

A straight wall made by this program is measured in its own frame (x along its axis, from its start; y across it, 0
on its axis): each of its lines is a y. A dimension's end taken to one of them keeps which one (`kind`): when the wall
moves its end goes along, and when the wall's type changes (another thickness, other layers) it stays on that line.

`lines(doc, guids)` reads them in bulk (one reading of the layers for all), kept per wall while its thickness is the
same (`doc._dim_lines`, emptied when another file opens)."""

from dataclasses import dataclass

import numpy as np

PREFERENCES = ("faces", "core_faces", "axis", "core_axis")
KINDS = ("face_lo", "face_hi", "core_lo", "core_hi", "axis", "core_axis")
WALL_CLASSES = ("IfcWall", "IfcWallStandardCase")


@dataclass
class WallLines:
    guid: str
    m: np.ndarray            # its placement (4×4, program coordinates)
    length: float
    lo: float                # its faces (y)…
    hi: float
    core: tuple              # …its core's faces (y0, y1)

    @property
    def axis_dir(self):
        x = self.m[:3, 0]
        return x / np.linalg.norm(x)

    @property
    def across(self):
        y = self.m[:3, 1]
        return y / np.linalg.norm(y)

    def y_of(self, kind):
        """The y of one of its lines (KINDS), or None."""
        return {"face_lo": self.lo, "face_hi": self.hi, "core_lo": self.core[0], "core_hi": self.core[1],
                "axis": 0.0, "core_axis": (self.core[0] + self.core[1]) / 2}.get(kind)

    def ys(self, preference):
        """[(y, kind)] of the lines a preference takes on this wall."""
        if preference == "axis":
            return [(0.0, "axis")]
        if preference == "core_axis":
            return [((self.core[0] + self.core[1]) / 2, "core_axis")]
        if preference == "core_faces":
            return [(self.core[0], "core_lo"), (self.core[1], "core_hi")]
        return [(self.lo, "face_lo"), (self.hi, "face_hi")]

    def side_kind(self, preference, side):
        """The line a preference takes on one side of the wall (side +1: its y > 0 side, -1: the other) — a face or a
        core face on that side, else its axis or its core's."""
        found = self.ys(preference)
        if len(found) == 1:
            return found[0]
        return found[1] if side > 0 else found[0]

    def local(self, p):
        p = np.asarray(p, dtype=float)
        return np.linalg.solve(self.m[:3, :3], (p if len(p) == 3 else np.array((p[0], p[1], self.m[2, 3])))
                               - self.m[:3, 3])

    def world(self, x, y, z=0.0):
        return self.m[:3, :3] @ np.array((x, y, z)) + self.m[:3, 3]


def lines(doc, guids):
    """{GlobalId: WallLines} of the straight walls of this program among `guids`."""
    cache = getattr(doc, "_dim_lines", None)
    if cache is None or cache.get("_file") is not getattr(doc, "ifc", None):
        cache = doc._dim_lines = {"_file": getattr(doc, "ifc", None)}
    out, todo = {}, []
    revision = getattr(doc, "revision", None)
    for guid in guids:
        kept = cache.get(guid)
        if kept is not None and len(kept) > 3 and kept[3] == revision and revision is not None:
            lo, hi, core = kept[2]                      # (the model as it was: not read again)
            out[guid] = WallLines(guid, kept[4], kept[1], lo, hi, core)
            continue
        obj = doc.get(guid)
        if obj is None or not getattr(obj, "is_bim", False) or obj.ifc_class not in WALL_CLASSES:
            continue
        try:
            length, _height, thickness = doc.ifc.wall_params(guid)
            m = doc.ifc.placement(guid)
        except Exception:
            continue
        if kept is not None and abs(kept[0] - thickness) < 1e-9 and abs(kept[1] - length) < 1e-9:
            lo, hi, core = kept[2]
            cache[guid] = (kept[0], kept[1], kept[2], revision, m)
            out[guid] = WallLines(guid, m, float(length), lo, hi, core)
        else:
            todo.append((guid, float(length), float(thickness), m))
    if not todo:
        return out
    try:
        kinds = {g: doc.ifc.kind_of(g) for g, *_r in todo}
        layers = doc.ifc.layers([g for g, *_r in todo], single=True)
        strengths = doc.ifc.layer_strengths([g for g, *_r in todo])
    except Exception:
        kinds, layers, strengths = {}, {}, {}
    for guid, length, thickness, m in todo:
        if kinds.get(guid) != "wall":
            continue                                    # (a curved wall, one of another program's: not yet)
        y = m[:3, 1] / np.linalg.norm(m[:3, 1])
        origin = float(y @ m[:3, 3])
        spans = []
        for _hatch, n, d0, d1 in layers.get(guid, ()):
            if float(np.asarray(n, dtype=float) @ y) >= 0:          # (d0 <= n·p <= d1, n along its y…)
                spans.append((d0 - origin, d1 - origin))
            else:                                                   # (…or against it)
                spans.append((-d1 - origin, -d0 - origin))
        verts = doc.get(guid).mesh.verts
        local_y = (np.asarray(verts, dtype=float) - m[:3, 3]) @ y if len(verts) else np.array((-thickness / 2,
                                                                                               thickness / 2))
        lo, hi = float(local_y.min()), float(local_y.max())
        if hi - lo < 1e-6 or hi - lo > thickness * 1.5 + 0.05:          # (an odd shape: its thickness round its axis)
            lo, hi = -thickness / 2, thickness / 2
        core = _core(spans, strengths.get(guid), lo, hi)
        cache[guid] = (thickness, length, (lo, hi, core), revision, m)
        out[guid] = WallLines(guid, m, length, lo, hi, core)
    return out


def _core(spans, given, lo, hi):
    """The core's faces (y0, y1): the layers of the strongest function given (its type's «Estrutura»), else the
    thickest; the whole wall when it has no layers."""
    if not spans:
        return (lo, hi)
    given = list(given or ())
    if len(given) == len(spans) and any(v is not None for v in given):
        best = min(v for v in given if v is not None)
        chosen = [s for s, v in zip(spans, given) if v == best]
    else:
        chosen = [max(spans, key=lambda s: s[1] - s[0])]
    return (min(s[0] for s in chosen), max(s[1] for s in chosen))


def walls_of(doc, storey):
    """The straight walls of this program on a storey, shown: {GlobalId: WallLines}."""
    guids = [o.id for o in doc.objects.values() if getattr(o, "is_bim", False) and o.storey == storey
             and o.ifc_class in WALL_CLASSES]
    return lines(doc, guids)


def footprint(doc, guid):
    """A wall's outline in plan (a shapely polygon: its shape's convex hull), or None."""
    from shapely.geometry import MultiPoint
    obj = doc.get(guid)
    if obj is None or not len(obj.mesh.verts):
        return None
    hull = MultiPoint([(float(p[0]), float(p[1])) for p in obj.mesh.verts]).convex_hull
    return hull if hull.geom_type == "Polygon" else None


def crossings(walls, start, direction, reach, preference, skip=(), within=0.02):
    """Where the line start + t·direction (plan, 0 <= t <= reach; negative reach: both ways) crosses the walls'
    lines a preference takes: [(t, point (3,), GlobalId, kind)] by t — only on the walls it goes through (across
    them, not along), within each one's length (± `within`)."""
    start = np.asarray(start, dtype=float)
    d = np.asarray(direction, dtype=float)
    d = d / max(float(np.linalg.norm(d[:2])), 1e-12)
    out = []
    for guid, w in walls.items():
        if guid in skip:
            continue
        across = w.across
        dy = float(across[:2] @ d[:2])
        if abs(dy) < 0.05:                             # (along it, not across)
            continue
        base = w.local(np.array((start[0], start[1], w.m[2, 3])))
        ax = w.axis_dir
        dx = float(ax[:2] @ d[:2])
        for y, kind in w.ys(preference):
            t = (y - base[1]) / dy
            if (reach >= 0 and not -1e-9 <= t <= reach) or (reach < 0 and abs(t) > -reach):
                continue
            x = base[0] + dx * t
            if -within <= x <= w.length + within:
                p = np.array((start[0] + d[0] * t, start[1] + d[1] * t, float(start[2]) if len(start) > 2 else 0.0))
                out.append((float(t), p, guid, kind))
    out.sort(key=lambda c: c[0])
    kept = []
    for c in out:                                       # (two walls meeting there: one point)
        if kept and abs(c[0] - kept[-1][0]) < 1e-3:
            continue
        kept.append(c)
    return kept


def hang(doc, guid, point, kind=None):
    """A dimension's end on an element (model/dimensions.hang), and the wall's line it is on (`kind`), if any."""
    from . import dimensions as dims_model
    ref = dims_model.hang(doc, guid, point)
    if ref is None or kind is None:
        return ref
    return ref[0], ref[1], ref[2], kind
