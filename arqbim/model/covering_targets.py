"""(0.567, PLANO.md «Gerador de revestimentos 3D em IFC», step 4) Where Revestimentos go, many at once:

- by category: the faces of every wall (outside, inside or both — a face is inside when a room is in front of it),
  slab (its top, its underside, its edges), column or beam (its sides) of the elements given;
- by room: its floor, its walls up to a height (each wall's face cut to the stretch of it along the room), its
  skirting, its ceiling.

Each a (host, point, normal, outline, holes) — a face to lay a finish on, the host followed. Pure lookups (the
model
is not changed here)."""

import numpy as np
from shapely.geometry import Point, Polygon

from ..core import face_region
from ..core import tiling as tl

CATEGORIES = ("parede", "laje", "pilar", "viga")
SIDES = ("ambas", "exterior", "interior")
SLAB_FACES = ("topo", "baixo", "bordos")
IFC_CLASSES = {"parede": ("IfcWall", "IfcWallStandardCase"), "laje": ("IfcSlab",), "pilar": ("IfcColumn",),
               "viga": ("IfcBeam",)}


def _mesh(ifc, guid, cache):
    if guid not in cache:
        cache[guid] = ifc.triangulate([guid]).get(guid)
    return cache[guid]


def face_along(ifc, guid, normal, cache, at=None):
    """The face of element `guid` furthest along `normal` (its outer face that way), nearest its middle — or `at` (a
    point) —: (point, outline, holes) or None."""
    found = _mesh(ifc, guid, cache)
    if found is None:
        return None
    v, t = np.asarray(found[0], float), np.asarray(found[1])
    n = np.asarray(normal, float)
    n /= np.linalg.norm(n) or 1.0
    mid = (v.min(axis=0) + v.max(axis=0)) / 2.0 if at is None else np.asarray(at, float)
    point = mid + n * (float((v @ n).max()) - float(mid @ n))
    out = face_region.face_at(v, t, point, n, reach=1e9)
    if out is None:
        return None
    return point, out[0], out[1]


def _rooms(ifc, storey):
    return [Polygon(s["outline"], s["holes"]).buffer(0) for s in ifc.spaces(storey) if len(s["outline"]) >= 3]


def _inside(rooms, point, normal):
    """Is the face at `point` facing `normal` inside (a room in front of it)?"""
    q = Point(float(point[0] + normal[0] * 0.25), float(point[1] + normal[1] * 0.25))
    return any(r.covers(q) for r in rooms)


def by_category(ifc, guids, category, sides="ambas", slab_faces=("topo",)):
    """[(host, point, normal, outline, holes)] of the faces of the elements `guids` of that category."""
    cache, out = {}, []
    classes = IFC_CLASSES[category]
    rooms_by_storey = {}
    for g in guids:
        e = ifc.by_guid(g)
        if e is None or not any(e.is_a(c) for c in classes):
            continue
        m = ifc._placement_si(e)
        if category == "parede":
            y = m[:3, 1] / (np.linalg.norm(m[:3, 1]) or 1.0)
            normals = [y, -y]
        elif category == "laje":
            normals = []
            if "topo" in slab_faces:
                normals.append(np.array((0.0, 0.0, 1.0)))
            if "baixo" in slab_faces:
                normals.append(np.array((0.0, 0.0, -1.0)))
            if "bordos" in slab_faces:
                normals += _edge_normals(ifc, g, cache)
        else:
            x = m[:3, 0] / (np.linalg.norm(m[:3, 0]) or 1.0)
            y = m[:3, 1] / (np.linalg.norm(m[:3, 1]) or 1.0)
            normals = [x, -x, y, -y] if category == "pilar" else [y, -y, np.array((0.0, 0.0, -1.0))]
        for n in normals:
            found = face_along(ifc, g, n, cache)
            if found is None:
                continue
            point, outline, holes = found
            if category == "parede" and sides != "ambas":
                st = ifc.storey_of(g)
                if st not in rooms_by_storey:
                    rooms_by_storey[st] = _rooms(ifc, st)
                inside = _inside(rooms_by_storey[st], point, n)
                if (sides == "interior") != inside:
                    continue
            out.append((g, point, n, outline, holes))
    return out


def _edge_normals(ifc, guid, cache):
    """A slab's edges' outward directions (its level outline's sides)."""
    found = _mesh(ifc, guid, cache)
    if found is None:
        return []
    v, t = np.asarray(found[0], float), np.asarray(found[1])
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    nn = np.cross(b - a, c - a)
    ln = np.linalg.norm(nn, axis=1)
    nn = nn[ln > 1e-9] / ln[ln > 1e-9, None]
    level = nn[np.abs(nn[:, 2]) < 0.01]
    out = []
    for n in level:
        if not any(float(n @ o) > 0.999 for o in out):
            out.append(n)
    return out


def room_floor(info, lift=0.0):
    """The floor of a room (space_info): (outline, holes) at its level, facing up."""
    z = float(info["level"]) + lift
    ring = Polygon(info["outline"]).exterior
    pts = [(x, y, z) for x, y in list(ring.coords)[:-1]]
    if Polygon(info["outline"]).exterior.is_ccw is False:
        pts = pts[::-1]
    holes = [[(x, y, z) for x, y in h] for h in info["holes"]]
    return pts, holes


def room_ceiling(info):
    """Its ceiling: its outline at its top, facing down."""
    pts, holes = room_floor(info, float(info["height"]))
    return pts[::-1], [h[::-1] for h in holes]


def room_walls(ifc, info, height):
    """[(host, point, normal, outline, holes)] of the walls round a room: each wall face facing into it, cut to the
    stretch of the room along it and up to `height` over its floor."""
    poly = Polygon(info["outline"]).buffer(0)
    if poly.is_empty:
        return []
    ccw = Polygon(info["outline"]).exterior.is_ccw
    ring = list(Polygon(info["outline"]).exterior.coords)
    level = float(info["level"])
    walls = [e.GlobalId for e in ifc.file.by_type("IfcWall") if ifc.storey_of(e.GlobalId) == info["storey"]]
    cache, out, done = {}, [], set()
    for a, b in zip(ring, ring[1:]):
        a, b = np.array((a[0], a[1], level)), np.array((b[0], b[1], level))
        d = b - a
        ln = float(np.linalg.norm(d[:2]))
        if ln < 0.05:
            continue
        inward = np.array((-d[1], d[0], 0.0)) / ln * (1.0 if ccw else -1.0)
        n = inward                                        # (the wall's face looks into the room)
        mid = (a + b) / 2.0 + np.array((0.0, 0.0, min(1.0, height / 2.0)))
        best = None
        for g in walls:
            found = _mesh(ifc, g, cache)
            if found is None:
                continue
            v = np.asarray(found[0], float)
            if (v.min(axis=0)[:2] - 0.05 > np.maximum(a, b)[:2]).any() or \
                    (v.max(axis=0)[:2] + 0.05 < np.minimum(a, b)[:2]).any():
                continue
            face = face_region.face_at(v, np.asarray(found[1]), mid - n * 0.0, n, reach=max(ln, 0.5))
            if face is None:
                continue
            gap = abs(float((np.asarray(face[0][0]) - a) @ n))
            if gap < 0.02 and (best is None or gap < best[0]):
                best = (gap, g, face)
        if best is None:
            continue
        _gap, g, (outline, holes, fn) = best
        key = (g, tuple(np.round(a, 3)), tuple(np.round(b, 3)))
        if key in done:
            continue
        done.add(key)
        for ol, hs in face_region.clip_to_stretch(outline, holes, a, b, height):
            c = Polygon(tl.to_plane(ol, tl.face_frame(ol))).representative_point()
            point = tl.to_space([(c.x, c.y)], tl.face_frame(ol))[0]
            out.append((g, point, np.asarray(fn, float), ol, hs, (a, b, float(height))))
    return out
