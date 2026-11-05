"""(0.399) The dimensions made with one click (the owner, 2026-11-05: «quero cotas automáticas, para cotar o interior
com um clique; a mesma coisa para a cotação externa»), on the plan of a storey, every end hung on its wall's line, its
door or its window (model/dim_refs): the wall moved, or given another type, the dimensions follow.

Outside (`exterior`): round the building — its outline, whatever the directions of its sides (not only N/S/E/W) —,
each side that faces one way (its setbacks too) gets its rows, from the building out: its openings (their jambs or
their middles) between its ends; the inner walls that reach it (their faces, cores or axes, as the preference says);
its corners (setbacks and returns); its overall length. A row that says no more than the next one out is left out.

Inside (`interior`, in step 4): in the room clicked."""

import math

import numpy as np

from . import dim_refs
from . import dimensions as dims_model

ROWS = ("openings", "walls", "corners", "overall")
OPENINGS = ("jambs", "centres", "none")
FIRST, STEP = 8.0, 7.0          # mm on paper: the first row out from the building, the others one after another
MIN_SIDE = 0.25                 # m: a side of the outline shorter than this is a notch, not a façade
TOUCH = 0.03                    # m: an inner wall this near a façade wall's inner face reaches it
PAST = 0.3                      # m: looked for past a façade wall's ends (a corner's walls)


def _outline(doc, walls):
    """The building's outline in plan: its largest piece, as a shapely polygon (counter-clockwise), or None."""
    from shapely.geometry.polygon import orient
    from shapely.ops import unary_union
    shapes = [s for s in (dim_refs.footprint(doc, g) for g in walls) if s is not None]
    if not shapes:
        return None
    union = unary_union([s.buffer(0.005, join_style="mitre") for s in shapes]).buffer(-0.005, join_style="mitre")
    pieces = [g for g in getattr(union, "geoms", [union]) if g.geom_type == "Polygon" and not g.is_empty]
    if not pieces:
        return None
    return orient(max(pieces, key=lambda g: g.area).simplify(1e-4), 1.0)


def facades(doc, storey):
    """The building's sides: [(outward (2,), along (2,), [(p, q) edges of the outline facing that way])] — the
    outline's edges grouped by the way they face (within 1°), the notches left out."""
    walls = dim_refs.walls_of(doc, storey)
    building = _outline(doc, walls)
    if building is None:
        return walls, []
    ring = [np.array(c, dtype=float) for c in building.exterior.coords]
    groups = []
    for p, q in zip(ring, ring[1:]):
        d = q - p
        length = float(np.linalg.norm(d))
        if length < MIN_SIDE:
            continue
        n = np.array((d[1], -d[0])) / length            # (counter-clockwise: outside is on the right)
        for g in groups:
            if float(g[0] @ n) > math.cos(math.radians(1.0)):
                g[2].append((p, q))
                break
        else:
            groups.append((n, np.array((-n[1], n[0])), [(p, q)]))
    return walls, groups


def _on_side(walls, edges, outward):
    """The walls whose outer face lies on these edges (the façade's walls) — {GlobalId: side of it outside (+1/-1)}."""
    from shapely.geometry import LineString
    lines = [LineString([tuple(p), tuple(q)]) for p, q in edges]
    out = {}
    for guid, w in walls.items():
        across = w.across[:2]
        if abs(float(across @ outward)) < 0.999:
            continue
        side = 1 if float(across @ outward) > 0 else -1
        y = w.hi if side > 0 else w.lo
        a, b = w.world(0.0, y)[:2], w.world(w.length, y)[:2]
        face = LineString([tuple(a), tuple(b)])
        if any(face.distance(line) < 1e-3 and face.intersection(line.buffer(1e-3)).length > 0.05 for line in lines):
            out[guid] = side
    return out


def _corner_ref(doc, walls, corner, along, outward, preference, own):
    """A corner of the outline as the preference measures it: the wall across the façade at that corner (not one of
    the façade's own), its line nearest the corner — (point, GlobalId, kind); the corner itself on its finish face
    (no wall across there, or the faces)."""
    best = None
    for guid, w in walls.items():
        if abs(float(w.across[:2] @ along)) < 0.999:     # (a wall across the façade: its y runs along the façade)
            continue
        local = w.local(np.array((corner[0], corner[1], w.m[2, 3])))
        # (on it, or just past an end of it: a wall butting against the façade's own stops short of the corner)
        if not (-PAST <= local[0] <= w.length + PAST and w.lo - 0.01 <= local[1] <= w.hi + 0.01):
            continue
        found = min(w.ys(preference), key=lambda yk: abs(yk[0] - local[1]))
        shift = float(w.across[:2] @ along) * (found[0] - local[1])
        candidate = (abs(shift), corner + along * shift, guid, found[1])
        if best is None or candidate[0] < best[0]:
            best = candidate
    if best is None:                                    # (the façade wall's own end: hung on it, as it is)
        nearest = min(own, key=lambda g: abs(walls[g].local(np.array((corner[0], corner[1], walls[g].m[2, 3])))[0]
                                             - np.clip(walls[g].local(np.array((corner[0], corner[1],
                                                                                walls[g].m[2, 3])))[0], 0,
                                                       walls[g].length)), default=None)
        return corner, nearest, None
    return best[1], best[2], best[3]


def exterior(doc, storey, preference="faces", rows=ROWS, openings="jambs", scale=100, near=None, style=None):
    """The outside dimensions of the plan of `storey`: [Dimension], each row a string (Dimension.chain), tag
    "ext:<side>". near: a plan point — only the side nearest it (else all). scale: N of the view's 1:N (the rows'
    distances are on paper)."""
    walls, groups = facades(doc, storey)
    if not groups:
        return []
    if near is not None:
        groups = [min(groups, key=lambda g: _distance(g, near))]
    z = next((level for g, _n, level in doc.ifc.storeys() if g == storey), 0.0)
    view, mm = ("plan", storey), scale / 1000.0
    out = []
    for outward, along, edges in groups:
        own = _on_side(walls, edges, outward)
        key = "ext:{:.0f}".format(math.degrees(math.atan2(outward[1], outward[0])) % 360)
        depth = max(float(p @ outward) for e in edges for p in e)
        # the corners: each end of each edge of this side, as the preference measures it
        corners = []
        for p, q in edges:
            for c in (p, q):
                point, guid, kind = _corner_ref(doc, walls, c, along, outward, preference, own)
                corners.append((float(point @ along), point, guid, kind))
        corners = _unique(corners)
        if len(corners) < 2:
            continue
        ends = [corners[0], corners[-1]]
        found_rows = []
        if "openings" in rows and openings != "none":
            holes = _openings(doc, own, openings, along)
            if holes:
                found_rows.append(_unique(ends + holes))
        if "walls" in rows:
            inner = _inner_walls(walls, own, along, preference)
            if inner:
                found_rows.append(_unique(ends + inner))
        if "corners" in rows and len(corners) > 2:
            found_rows.append(corners)
        if "overall" in rows:
            found_rows.append(ends)
        kept = []
        for row in found_rows:                          # (a row that says what the next one says: left out)
            if kept and [round(r[0], 4) for r in row] == [round(r[0], 4) for r in kept[-1]]:
                continue
            kept.append(row)
        for k, row in enumerate(kept):
            line = depth + (FIRST + STEP * k) * mm
            out += _string(doc, view, row, along, outward, line, z, key, style)
    return out


def _distance(group, point):
    from shapely.geometry import LineString, Point
    q = Point(float(point[0]), float(point[1]))
    return min(LineString([tuple(p), tuple(e)]).distance(q) for p, e in group[2])


def _unique(points):
    points = sorted(points, key=lambda r: r[0])
    out = []
    for r in points:
        if out and abs(r[0] - out[-1][0]) < 1e-3:
            if out[-1][2] is None and r[2] is not None:
                out[-1] = r                             # (the one hung on an element)
            continue
        out.append(r)
    return out


def _openings(doc, own, mode, along):
    """The doors' and windows' jambs (or middles) in the façade's walls: [(s, point, GlobalId, None)]."""
    from . import bim
    out = []
    for guid, side in own.items():
        for filling in bim._fillings(doc, guid):
            try:
                st = doc.ifc.filling_state(filling)
            except Exception:
                continue
            f = st["frame"]
            y = f.y1 if side > 0 else f.y0
            xs = (st["s"] + st["width"] / 2,) if mode == "centres" else (st["s"], st["s"] + st["width"])
            for x in xs:
                c = np.asarray(f.to_world((x, y, f.z0)), dtype=float)[:2]
                out.append((float(c @ along), c, filling, None))
    return out


def _inner_walls(walls, own, along, preference):
    """The walls that reach the façade's walls from inside (a T): their lines as the preference takes them, measured
    along the façade — [(s, point on the façade's outer face, GlobalId, kind)]."""
    out = []
    for guid, side in own.items():
        w = walls[guid]
        inner_y = (w.lo - TOUCH) if side > 0 else (w.hi + TOUCH)       # (just inside its inner face)
        outer_y = w.hi if side > 0 else w.lo
        start = w.world(-PAST, inner_y)                 # (its axis stops short of a corner's faces: past its ends)
        for _t, p, other, kind in dim_refs.crossings(walls, start, w.axis_dir, w.length + 2 * PAST, preference,
                                                     skip=set(own)):
            o = walls[other]
            if abs(float(o.across[:2] @ along)) < 0.999:                # (square to the façade only)
                continue
            face = w.local(p)
            q = w.world(face[0], outer_y)[:2]
            out.append((float(q @ along), q, other, kind))
    return out


# ------------------------------------------------------------ inside (0.400)

MODES = ("size", "run", "walls")         # its width and depth; a run across the building; along its walls, openings
DIRECTIONS = ("both", "width", "depth")


def rooms(doc, storey, walls=None):
    """The rooms of a storey as its walls close them (with an «Ambiente» or not): the holes of the walls' union —
    [shapely Polygon], by their finish faces."""
    from shapely.ops import unary_union
    walls = dim_refs.walls_of(doc, storey) if walls is None else walls
    shapes = [s for s in (dim_refs.footprint(doc, g) for g in walls) if s is not None]
    if not shapes:
        return []
    union = unary_union([s.buffer(0.005, join_style="mitre") for s in shapes]).buffer(-0.005, join_style="mitre")
    from shapely.geometry import Polygon
    out = []
    for piece in getattr(union, "geoms", [union]):
        if piece.geom_type != "Polygon":
            continue
        for hole in piece.interiors:
            room = Polygon(hole).buffer(0)
            if room.area > 0.3:
                out.append(room.simplify(1e-4))
    return out


def room_at(rooms_found, point):
    from shapely.geometry import Point
    q = Point(float(point[0]), float(point[1]))
    return next((r for r in rooms_found if r.contains(q)), None)


SKEW = 0.17                     # (0.409) sin ≈ 10°: two sides less apart than this are taken as one way


def room_axes(room, point=None):
    """A room's two directions, (its width, its depth) — along its longest side and square to it; (0.408) given a
    point (the mouse), along the side of the room nearest it (one at least MIN_SIDE long), so that near a wall askew
    the dimensions follow that wall and near the others they follow them (the owner: «precisa alinhar com as paredes
    ao aproximar das paredes»); (0.409) and the other along the nearest side that is not parallel to it (the owner,
    in a room with a wall askew: «devia pegar as 2 paredes» — near the corner of a straight wall and one askew, one
    dimension along each: across the room parallel to the straight one, and along the one askew), square to it when
    there is none. The width is the one of the two nearer the longest side's way."""
    ring = [np.array(c, dtype=float) for c in room.exterior.coords]
    edges = [(p, q) for p, q in zip(ring, ring[1:]) if float(np.linalg.norm(q - p)) > 1e-9]

    def way(e):
        return (e[1] - e[0]) / float(np.linalg.norm(e[1] - e[0]))

    def readable(d):
        return -d if d[0] < -1e-9 or (abs(d[0]) <= 1e-9 and d[1] < 0) else d     # (left to right, else upwards)

    longest = way(max(edges, key=lambda e: float(np.linalg.norm(e[1] - e[0]))))
    if point is None:
        d = readable(longest)
        return d, np.array((-d[1], d[0]))
    from shapely.geometry import LineString
    sides = [e for e in edges if float(np.linalg.norm(e[1] - e[0])) >= MIN_SIDE] or edges
    q = _pt(np.asarray(point, dtype=float)[:2])
    sides.sort(key=lambda e: LineString([tuple(e[0]), tuple(e[1])]).distance(q))
    first = way(sides[0])
    second = next((w for w in (way(e) for e in sides[1:]) if abs(float(first[0] * w[1] - first[1] * w[0])) > SKEW),
                  np.array((-first[1], first[0])))
    if abs(float(first @ longest)) < abs(float(second @ longest)):
        first, second = second, first                   # (the width stays the way of the longest side)
    return readable(first), readable(second)


def _key(room):
    c = room.representative_point()
    return "{:.2f},{:.2f}".format(c.x, c.y)


def interior(doc, storey, point, preference="faces", mode="size", directions="both", openings="jambs", scale=100,
             style=None, every=False):
    """The inside dimensions of the room under `point` (every: of every room of the storey, each through a point well
    inside it) on the plan of `storey`: [Dimension], each a string, tag "int:<room>" ("run:" for a run).
    - size: its width and its depth, from wall to wall, on lines through the point — (0.408) along and square to the
      room's side nearest the point;
    - run: lines through the point right across the building — each room and each wall's thickness on the way;
    - walls: along each of its walls, inside it: its corners, its doors and windows, the walls that reach it."""
    walls = dim_refs.walls_of(doc, storey)
    found = rooms(doc, storey, walls)
    if every:
        chosen = [(r, _inside_point(r)) for r in found]
    else:
        room = room_at(found, point) if point is not None else None
        chosen = [(room, np.asarray(point, dtype=float)[:2])] if room is not None else []
    if not chosen:
        return []
    z = next((level for g, _n, level in doc.ifc.storeys() if g == storey), 0.0)
    view, mm = ("plan", storey), scale / 1000.0
    out = []
    for room, at in chosen:
        d1, d2 = room_axes(room, None if every else at)      # (0.408: the wall nearest the point clicked)
        ways = {"both": (d1, d2), "width": (d1,), "depth": (d2,)}[directions]
        tag = "{}:{}:{}".format("run" if mode == "run" else "int", mode, _key(room))
        if mode == "walls":
            out += _along_walls(doc, walls, room, preference, openings, mm, z, view, tag, style)
            continue
        reach = -(room.length + 50.0)
        for d in ways:
            start = np.array((at[0], at[1], z))
            points = dim_refs.crossings(walls, start, np.array((d[0], d[1], 0.0)), reach, preference)
            if mode == "size":
                before = [c for c in points if c[0] < 0]
                after = [c for c in points if c[0] > 0]
                if not before or not after:
                    continue
                points = [before[-1], after[0]]
                # (0.409) and the room's corners between them — an L's inner corner, a recess (the owner: «na cota
                # automática não pega as paredes em esquinas no interior»)
                points = sorted(points + _room_corners(doc, walls, room, start, d, points[0][0], points[1][0],
                                                       preference), key=lambda c: c[0])
            if len(points) < 2:
                continue
            row = [(float(t), p[:2], g, k) for t, p, g, k in points]
            out += _string(doc, view, row, d, np.array((-d[1], d[0])), 0.0, z, tag, style, through=at)
    return out


def _room_corners(doc, walls, room, start, d, t0, t1, preference):
    """(0.409) The corners of a room between the two ends of its width or depth (t0 < t1 along `d` from `start`): an
    L's inner corner, a recess's — each on the line the preference takes on the wall across `d` there (as the façade's
    corners, _corner_ref), one per place along the line (the corner nearest the line): [(t, point (3,), GlobalId,
    kind)]."""
    o = np.asarray(start, dtype=float)
    d = np.asarray(d, dtype=float)[:2]
    across = np.array((-d[1], d[0]))
    found = []
    for c in list(room.exterior.coords)[:-1]:
        corner = np.array(c, dtype=float)
        point, guid, kind = _corner_ref(doc, walls, corner, d, None, preference, {})
        if guid is None:
            continue                                    # (no wall square to the line there: a wall askew's corner)
        t = float((point - o[:2]) @ d)
        if t0 + 0.01 < t < t1 - 0.01:
            found.append((t, abs(float((corner - o[:2]) @ across)), point, guid, kind))
    found.sort(key=lambda f: f[0])
    groups = []                                         # (corners at one place along it: the one nearer the line)
    for f in found:
        if groups and abs(f[0] - groups[-1][0][0]) < 0.01:
            groups[-1].append(f)
        else:
            groups.append([f])
    z = float(o[2]) if len(o) > 2 else 0.0
    out = []
    for group in groups:
        t, _off, point, guid, kind = min(group, key=lambda f: f[1])
        out.append((t, np.array((point[0], point[1], z)), guid, kind))
    return out


def _inside_point(room):
    """A point well inside a room, a quarter of its depth off its middle (clear of its name), if still inside it."""
    from shapely.geometry import Point
    c = room.representative_point()
    _d1, d2 = room_axes(room)
    x0, y0, x1, y1 = room.bounds
    reach = abs(float(d2 @ np.array((x1 - x0, y1 - y0))))
    for k in (0.25, -0.25, 0.0):
        q = np.array((c.x, c.y)) + d2 * reach * k
        if room.contains(Point(float(q[0]), float(q[1]))):
            return q
    return np.array((c.x, c.y))


def _along_walls(doc, walls, room, preference, openings, mm, z, view, tag, style):
    """Along each wall of a room, inside it, FIRST mm of paper off its face: its corners (as the preference takes
    them), its doors and windows, the walls that reach it from the room."""
    from shapely.geometry import LineString
    from shapely.geometry.polygon import orient
    from . import bim
    ring = [np.array(c, dtype=float) for c in orient(room, 1.0).exterior.coords]
    out = []
    for p, q in zip(ring, ring[1:]):
        length = float(np.linalg.norm(q - p))
        if length < MIN_SIDE:
            continue
        along = (q - p) / length
        inward = np.array((-along[1], along[0]))          # (counter-clockwise: the room on the left)
        edge = LineString([tuple(p), tuple(q)])
        host = None
        for guid, w in walls.items():
            if abs(float(w.across[:2] @ inward)) < 0.999:
                continue
            side = 1 if float(w.across[:2] @ inward) > 0 else -1      # (its face towards the room: the room's side)
            y = w.hi if side > 0 else w.lo
            face = LineString([tuple(w.world(0.0, y)[:2]), tuple(w.world(w.length, y)[:2])])
            if face.distance(edge) < 1e-3 and face.intersection(edge.buffer(1e-3)).length > 0.05:
                host = (guid, side)
                break
        if host is None:
            continue
        guid, side = host
        own = {guid: side}
        row = []
        for c in (p, q):
            point, g, kind = _corner_ref(doc, walls, c, along, -inward, preference, own)
            row.append((float(point @ along), point, g, kind))
        if openings != "none":
            for filling in bim._fillings(doc, guid):
                try:
                    st = doc.ifc.filling_state(filling)
                except Exception:
                    continue
                f = st["frame"]
                y = f.y1 if side > 0 else f.y0
                xs = (st["s"] + st["width"] / 2,) if openings == "centres" else (st["s"], st["s"] + st["width"])
                for x in xs:
                    c = np.asarray(f.to_world((x, y, f.z0)), dtype=float)[:2]
                    if edge.distance(_pt(c)) < 0.01:
                        row.append((float(c @ along), c, filling, None))
        w = walls[guid]
        start = p + inward * TOUCH                      # (the walls that reach it from the room: just inside)
        for _t, cp, other, kind in dim_refs.crossings(walls, np.array((start[0], start[1], w.m[2, 3])),
                                                      np.array((along[0], along[1], 0.0)), length, preference,
                                                      skip={guid}):
            if abs(float(walls[other].across[:2] @ along)) < 0.999:
                continue
            c = cp[:2] - inward * TOUCH
            row.append((float(c @ along), c, other, kind))
        row = _unique(row)
        lo, hi = float(p @ along), float(q @ along)
        row = [r for r in row if lo - 0.5 <= r[0] <= hi + 0.5]
        if len(row) >= 2:
            out += _string(doc, view, row, along, inward, FIRST * mm + float(p @ inward), z, tag, style)
    return out


def wall_points(doc, walls, guid, side, preference="faces", openings="jambs", crossing=True):
    """(0.401, the manual Dimension's «paredes inteiras», as Revit's «Entire walls») A wall measured along itself, on its
    face `side` (+1 / -1): its ends (the lines the preference takes on the walls across it there, else its own ends),
    its doors and windows (jambs or middles), the walls that cross it or reach it (their lines) — [(s, point (2,),
    GlobalId, kind)] by s along its axis."""
    from . import bim
    w = walls.get(guid)
    if w is None:
        return []
    along = w.axis_dir[:2] / max(float(np.linalg.norm(w.axis_dir[:2])), 1e-12)
    y = w.hi if side > 0 else w.lo
    verts = np.asarray(doc.get(guid).mesh.verts, dtype=float)
    xs = (verts - w.m[:3, 3]) @ w.axis_dir
    out = []
    for x in (float(xs.min()), float(xs.max())):
        corner = w.world(x, y)[:2]
        point, g, kind = _corner_ref(doc, walls, corner, along, None, preference, {guid: side})   # (not itself:
        #                                                                     its across is square to `along`)
        out.append((float(point @ along), point, g, kind))
    if openings != "none":
        for filling in bim._fillings(doc, guid):
            try:
                st = doc.ifc.filling_state(filling)
            except Exception:
                continue
            f = st["frame"]
            fy = f.y1 if side > 0 else f.y0
            for x in ((st["s"] + st["width"] / 2,) if openings == "centres" else (st["s"], st["s"] + st["width"])):
                c = np.asarray(f.to_world((x, fy, f.z0)), dtype=float)[:2]
                out.append((float(c @ along), c, filling, None))
    if crossing:
        for line_y in (w.lo - TOUCH, w.hi + TOUCH):
            start = w.world(-PAST, line_y)
            for _t, cp, other, kind in dim_refs.crossings(walls, start, w.axis_dir, w.length + 2 * PAST, preference,
                                                          skip={guid}):
                if abs(float(walls[other].across[:2] @ along)) < 0.999:
                    continue
                c = w.world(w.local(cp)[0], y)[:2]
                out.append((float(c @ along), c, other, kind))
    return _unique(out)


def _pt(c):
    from shapely.geometry import Point
    return Point(float(c[0]), float(c[1]))


def _string(doc, view, row, along, outward, line, z, tag, style, through=None):
    """A row of points along the façade as one dimension string, its line `line` out along `outward` — (0.400) or
    through the point `through`."""
    chain = dims_model.new_chain()
    out = []
    for (s0, p0, g0, k0), (s1, p1, g1, k1) in zip(row, row[1:]):
        a, b = np.array((p0[0], p0[1], z)), np.array((p1[0], p1[1], z))
        if through is not None:
            mid = (np.asarray(p0, dtype=float) + np.asarray(p1, dtype=float)) / 2
            mid = mid + outward * float((np.asarray(through, dtype=float)[:2] - mid) @ outward)
        else:
            mid = along * (s0 + s1) / 2 + outward * line
        at = np.array((mid[0], mid[1], z))
        refs = [dim_refs.hang(doc, g0, a, k0), dim_refs.hang(doc, g1, b, k1)]
        out.append(dims_model.Dimension(view, a, b, at, refs, tag, dims_model.hang_line(doc, refs, at),
                                        direction=np.array((along[0], along[1], 0.0)), style=style, chain=chain))
    return out
