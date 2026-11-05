"""Water and drainage proposed from the fixtures (0.148, Phase 6, step 5: «propostas automáticas de abastecimento e
drenagem a partir das salas e dos aparelhos, removíveis»): in each room with sanitary fixtures, a stack in its corner
nearest the WC (or its first fixture) — sewage with a WC, waste water without —, and the cold and hot water pipes
along the wall the fixtures are against, over the ceiling; then every fixture connected to them (ifc/branches.py).
Tagged as the water proposal: taken away again in one step.

Pure placement here (from the rooms' outlines and the fixtures' places); model/bim.py makes them."""

import numpy as np

STACK_IN = 0.15             # m: the stack this far from each of the corner's walls (its axis)
MAINS_IN = (0.10, 0.16)     # m: the cold / hot water pipes this far from the wall (their axes)
MAINS_END = 0.20            # m: the water pipes stop this far from the room's corners
COLD_Z, HOT_Z = 2.40, 2.50  # m over the storey: the cold and hot water pipes (over a 2,60 m ceiling: under it)
PROPOSAL = "aguas"          # the tag the proposed pipes carry


def _ccw(outline):
    pts = [np.array(p, dtype=float) for p in outline]
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) / 2
    return pts if area >= 0 else pts[::-1]


def room_of(point, rooms):
    """The room (its GlobalId) whose outline holds the plan point, or None. rooms: [(GlobalId, outline)]."""
    from shapely.geometry import Point, Polygon
    q = Point(float(point[0]), float(point[1]))
    for guid, outline in rooms:
        if Polygon(outline).buffer(1e-6).contains(q):
            return guid
    return None


def stack_spot(outline, near):
    """Where a room's stack goes: in its corner nearest `near` (plan), STACK_IN from both walls."""
    pts = _ccw(outline)
    k = min(range(len(pts)), key=lambda i: float(np.linalg.norm(pts[i] - np.asarray(near, dtype=float))))
    prev, here, nxt = pts[k - 1], pts[k], pts[(k + 1) % len(pts)]
    a, b = here - prev, nxt - here
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    na, nb = np.array((-a[1], a[0])), np.array((-b[1], b[0]))       # (inward: the room is on the left)
    return here + (na + nb) * STACK_IN


def mains_line(outline, near, inset):
    """The water pipe along the room's wall nearest `near` (a fixture's back): its two ends (plan), `inset` from that
    wall into the room, MAINS_END from the corners."""
    pts = _ccw(outline)
    q = np.asarray(near, dtype=float)
    best = None
    for a, b in zip(pts, pts[1:] + pts[:1]):
        d = b - a
        length = float(np.linalg.norm(d))
        if length < 2 * MAINS_END + 0.1:
            continue
        d = d / length
        s = min(max(float(np.dot(q - a, d)), 0.0), length)
        gap = float(np.linalg.norm(a + d * s - q))
        if best is None or gap < best[0]:
            n = np.array((-d[1], d[0]))
            best = (gap, a + d * MAINS_END + n * inset, b - d * MAINS_END + n * inset)
    return None if best is None else (best[1], best[2])


def propose(rooms, fixtures):
    """{room: {"stack": (2,), "sewage": a WC is there, "cold": (a, b), "hot": (a, b), "fixtures": [GlobalIds]}} for the
    rooms with fixtures. rooms: [(GlobalId, outline)]; fixtures: [(GlobalId, kind, back (2,), out (2,))] — the
    fixtures' backs and the way they face (a little in front of the back says which room they are in)."""
    by_room = {}
    for guid, kind, back, out in fixtures:
        room = room_of(np.asarray(back, dtype=float) + np.asarray(out, dtype=float) * 0.2, rooms)
        if room is not None:
            by_room.setdefault(room, []).append((guid, kind, np.asarray(back, dtype=float)))
    outlines = dict(rooms)
    plan = {}
    for room, items in by_room.items():
        outline = outlines[room]
        wc = next((b for _g, k, b in items if k == "wc"), None)
        first = items[0][2]
        cold = mains_line(outline, first, MAINS_IN[0])
        hot = mains_line(outline, first, MAINS_IN[1])
        plan[room] = {"stack": stack_spot(outline, wc if wc is not None else first), "sewage": wc is not None,
                      "cold": cold, "hot": hot, "fixtures": [g for g, _k, _b in items]}
    return plan
