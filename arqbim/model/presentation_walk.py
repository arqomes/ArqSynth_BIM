"""(0.488) The ArqSynth Presentation's «Passeio virtual» worked out in the BIM, from what it is sent (the rooms as zones,
the doors between two rooms as the ways from one to the other, the stairs between storeys —
presentation_export.spaces): which rooms are linked, the room one starts in, the guided tour (the Presentation's
guidedTour: every room one can reach, in the order a visitor walks them — from the start, each next room through a
door, back when there is none —, each leg as the Presentation walks it: from the middle of a room to the door, through
it, to the middle of the next; a stair from its foot to its head), and the camera walking it at a person's eye.

Rooms can be left out of the walk (not navigable there: not in the tour, not walked through). Everything in the GLB's
axes (Y up) as the description has them; `to_model` takes a point back to the model's. Pure Python and NumPy."""

import heapq
import math

import numpy as np

DOOR_STEP = 0.6         # m: a way through a door starts and ends this far from its middle (the importer's)
EYE = 1.65              # m: the eye over the floor (the Presentation's «Passeio suave»)
SPEED = 1.4             # m/s (its cameraSettings.walkSpeed)
DWELL = 3.0             # s in each room of the guided tour (its guidedTour.dwellMs)
DWELL_MIN, DWELL_MAX = 0.5, 60.0
AHEAD = 2.0             # m: where the eye looks, along the way


def to_model(p):
    """A point of the GLB's axes (x, y up, z = −north) in the model's (offset none)."""
    return (float(p[0]), -float(p[2]), float(p[1]))


def _rooms(sp):
    return {r["id"]: r for r in sp.get("rooms", ())}


def _middle(room):
    """The middle of its floor (the GLB's axes): the camera moves' room middle, at its level."""
    c = room["center"]
    return np.array((float(c[0]), float(room["level"]), float(c[2])))


def links(sp, off=()):
    """{room: [(other room, way points from this one to that one)]} — through a door between them (both rooms
    known), or a stair; rooms left out have none."""
    rooms = _rooms(sp)
    off = set(off)
    out = {rid: [] for rid in rooms if rid not in off}
    for d in sp.get("doors", ()):
        a, b = d.get("from"), d.get("to")
        if a not in out or b not in out or a == b:
            continue
        p, w = np.asarray(d["point"], dtype=float), np.asarray(d["way"], dtype=float)
        ra, rb = rooms[a], rooms[b]
        there = [_middle(ra), np.array((p[0] - w[0] * DOOR_STEP, ra["level"], p[2] - w[2] * DOOR_STEP)),
                 np.array((p[0], ra["level"], p[2])),
                 np.array((p[0] + w[0] * DOOR_STEP, rb["level"], p[2] + w[2] * DOOR_STEP)), _middle(rb)]
        out[a].append((b, there))
        out[b].append((a, there[::-1]))
    for s in sp.get("stairs", ()):
        a, b = s.get("from"), s.get("to")
        if a not in out or b not in out or a == b or len(s.get("points", ())) < 2:
            continue
        pts = [np.asarray(q, dtype=float) for q in s["points"]]
        there = [_middle(rooms[a])] + pts + [_middle(rooms[b])]
        out[a].append((b, there))
        out[b].append((a, there[::-1]))
    return out


def _length(points):
    return float(sum(np.linalg.norm(np.asarray(b) - np.asarray(a)) for a, b in zip(points, points[1:])))


def start_of(sp, chosen="", off=()):
    """The room the walk starts in: the one chosen, else the one the description says (behind a door from outside, on
    the lowest storey), else the first — none of them left out; None: no room."""
    rooms = [r["id"] for r in sp.get("rooms", ()) if r["id"] not in set(off)]
    for candidate in (chosen, sp.get("start")):
        if candidate and candidate in rooms:
            return candidate
    return rooms[0] if rooms else None


def tour(sp, start, off=()):
    """(the guided tour — the rooms from the start, each next one through a door from the last when there is one,
    else from the nearest one before it: a depth-first walk —, the rooms it cannot reach)."""
    graph = links(sp, off)
    if start not in graph:
        return [], [r for r in graph]
    order, seen, stack = [], set(), [start]
    while stack:
        room = stack.pop()
        if room in seen:
            continue
        seen.add(room)
        order.append(room)
        nexts = [b for b, _pts in graph[room] if b not in seen]
        # (the nearest door first: pushed last)
        here = _middle(_rooms(sp)[room])
        nexts.sort(key=lambda b: -float(np.linalg.norm(_middle(_rooms(sp)[b]) - here)))
        stack += nexts
    return order, [r for r in graph if r not in seen]


def path(sp, a, b, off=()):
    """The way from room a to room b — the shortest through doors and stairs —: its points, or None."""
    graph = links(sp, off)
    if a not in graph or b not in graph:
        return None
    if a == b:
        return [_middle(_rooms(sp)[a])]
    best, queue, before = {a: 0.0}, [(0.0, a)], {}
    while queue:
        cost, room = heapq.heappop(queue)
        if room == b:
            break
        if cost > best.get(room, math.inf):
            continue
        for other, pts in graph[room]:
            c = cost + _length(pts)
            if c < best.get(other, math.inf) - 1e-9:
                best[other], before[other] = c, (room, pts)
                heapq.heappush(queue, (c, other))
    if b not in before:
        return None
    legs, room = [], b
    while room != a:
        prev, pts = before[room]
        legs.append(pts)
        room = prev
    out = []
    for pts in reversed(legs):
        out += pts if not out else pts[1:]
    return out


def _sample(points, step):
    """Points every `step` m along the polyline (its ends kept)."""
    pts = [np.asarray(p, dtype=float) for p in points]
    out = [pts[0]]
    for p, q in zip(pts, pts[1:]):
        n = max(1, int(math.ceil(float(np.linalg.norm(q - p)) / step)))
        out += [p + (q - p) * (k / n) for k in range(1, n + 1)]
    return out


def frames(sp, rooms, off=(), fps=30, eye=EYE, speed=SPEED, dwell=DWELL):
    """The guided tour walked by the camera: [(eye, target)] a frame each, in the GLB's axes — in the first room for
    `dwell` s, then along the way to each next one at `speed`, the eye `eye` m over the floor looking `AHEAD` m along
    the way, `dwell` s in each one, looking on as it came in. [] when it cannot be walked."""
    if not rooms:
        return []
    known = _rooms(sp)
    lift = np.array((0.0, eye, 0.0))
    out = []
    look = np.array((0.0, 0.0, -1.0))                   # (north, the first room's)

    def stay(at):
        out.extend([(tuple(at + lift), tuple(at + lift + look * AHEAD))] * max(1, int(dwell * fps)))

    stay(_middle(known[rooms[0]]))
    for a, b in zip(rooms, rooms[1:]):
        way = path(sp, a, b, off)
        if way is None:
            return out
        pts = _sample(way, speed / fps)
        for k, p in enumerate(pts):
            ahead = pts[min(k + int(AHEAD / (speed / fps)), len(pts) - 1)]
            d = np.asarray(ahead, dtype=float) - p
            d[1] = 0.0
            if float(np.linalg.norm(d)) > 1e-6:
                look = d / np.linalg.norm(d)
            out.append((tuple(p + lift), tuple(p + lift + look * AHEAD)))
        stay(np.asarray(pts[-1], dtype=float))
    return out


def counts(sp):
    """(rooms, doors between two rooms, stairs) the walk has."""
    rooms = _rooms(sp)
    doors = sum(1 for d in sp.get("doors", ()) if d.get("from") in rooms and d.get("to") in rooms)
    return len(rooms), doors, len(sp.get("stairs", ()))
