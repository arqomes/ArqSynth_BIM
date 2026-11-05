"""The electrical points proposed for the rooms (0.145, Phase 6, step 4: «perfis por tipo de sala; opções com
pré-visualização»): each room's profile — found from its name (Quarto, Sala, Cozinha, WC, Corredor, Escritório…)
or chosen — says how many lights, switches, outlets, data and counter outlets it gets; they are placed as a
designer would start: the lights on the ceiling (one in the middle, two along a long room), a switch inside each
door beside it (two-way switches in a corridor), the outlets spread along the walls, away from the doors and the
corners. Seen before (a preview), made in one step, tagged as a proposal: taken away again in one step.

Pure placement here (from the rooms' outlines and the doors' places); model/bim.py makes them."""

import math

import numpy as np

# profile -> how many of each
PROFILES = {
    "bedroom": {"light": 1, "switch": 1, "outlet": 3, "data_outlet": 1, "outlet_counter": 0},
    "living": {"light": 2, "switch": 1, "outlet": 5, "data_outlet": 1, "outlet_counter": 0},
    "kitchen": {"light": 1, "switch": 1, "outlet": 2, "data_outlet": 0, "outlet_counter": 4},
    "bathroom": {"light": 1, "switch": 1, "outlet": 0, "data_outlet": 0, "outlet_counter": 1},
    "corridor": {"light": 1, "switch": 2, "outlet": 1, "data_outlet": 0, "outlet_counter": 0},
    "office": {"light": 1, "switch": 1, "outlet": 4, "data_outlet": 2, "outlet_counter": 0},
    "other": {"light": 1, "switch": 1, "outlet": 2, "data_outlet": 0, "outlet_counter": 0},
    "none": {"light": 0, "switch": 0, "outlet": 0, "data_outlet": 0, "outlet_counter": 0},
}
KEYWORDS = (("bathroom", ("wc", "i.s", "is ", "instalação sanitária", "instalacao sanitaria", "casa de banho", "banho",
                          "lavabo", "bathroom")),
            ("kitchen", ("cozinha", "copa", "kitchen")),
            ("bedroom", ("quarto", "suite", "suíte", "bedroom")),
            ("living", ("sala", "estar", "living")),
            ("corridor", ("corredor", "hall", "entrada", "circulação", "circulacao", "vestíbulo", "vestibulo",
                          "corridor")),
            ("office", ("escritório", "escritorio", "estúdio", "estudio", "office")))
SWITCH_BESIDE = 0.15        # m: a switch beside a door's edge, inside the room
KEEP_OFF = 0.30             # m: outlets this far from a door's edges and from the corners
PROPOSAL = "eletrica"       # the tag the proposed points carry


def profile_of(name):
    """The profile a room's name says ("Quarto 2": bedroom), "other" if it says none."""
    text = " {} ".format((name or "").lower())
    for key, words in KEYWORDS:
        if any(w in text for w in words):
            return key
    return "other"


def _ccw(outline):
    pts = [np.array(p, dtype=float) for p in outline]
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) / 2
    return pts if area >= 0 else pts[::-1]


def _edges(outline):
    """[(a, b, along (2,), inward (2,), length)] of a room's outline (counter-clockwise: the room on the left)."""
    pts = _ccw(outline)
    out = []
    for a, b in zip(pts, pts[1:] + pts[:1]):
        d = b - a
        length = float(np.linalg.norm(d))
        if length > 1e-6:
            d = d / length
            out.append((a, b, d, np.array((-d[1], d[0])), length))
    return out


def angle_of(inward):
    """A point's angle (degrees) so that its Y — out of its wall — is `inward`."""
    x = np.array((inward[1], -inward[0]))
    return math.degrees(math.atan2(x[1], x[0]))


def doors_of(outline, doors, near=0.30):
    """The doors (their middle (2,), width) on this room's outline: [(edge index, distance along it, width)]."""
    edges = _edges(outline)
    out = []
    for middle, width in doors:
        m = np.asarray(middle, dtype=float)
        best = None
        for k, (a, _b, d, n, length) in enumerate(edges):
            s = float(np.dot(m - a, d))
            gap = abs(float(np.dot(m - a, n)))
            if -0.05 <= s <= length + 0.05 and gap <= near and (best is None or gap < best[0]):
                best = (gap, k, s)
        if best is not None:
            out.append((best[1], best[2], float(width)))
    return out


def wall_spots(outline, count, doors=()):
    """`count` places along the walls (the outline's edges) for outlets — spread by length, each off the doors
    (KEEP_OFF from their edges) and the corners: [(point (2,), inward (2,))]."""
    if count <= 0:
        return []
    edges = _edges(outline)
    # the free stretches of each edge
    free = []
    for k, (a, _b, d, n, length) in enumerate(edges):
        taken = sorted((s - w / 2 - KEEP_OFF, s + w / 2 + KEEP_OFF) for e, s, w in doors if e == k)
        start = KEEP_OFF
        for lo, hi in taken + [(length - KEEP_OFF, length)]:
            if lo - start > 1e-6:
                free.append((a, d, n, start, lo))
            start = max(start, hi)
    total = sum(hi - lo for _a, _d, _n, lo, hi in free)
    if total <= 1e-6:
        return []
    out = []
    for j in range(count):
        target = total * (j + 0.5) / count
        for a, d, n, lo, hi in free:
            if target <= hi - lo + 1e-9:
                out.append((a + d * (lo + target), n))
                break
            target -= hi - lo
    return out


def switch_spots(outline, doors, count):
    """A switch beside each door, inside the room (at most `count`; a corridor's two at two doors, or at its
    ends): [(point (2,), inward (2,))]."""
    edges = _edges(outline)
    out = []
    for k, s, w in doors[:count]:
        a, _b, d, n, length = edges[k]
        for side in (1.0, -1.0):
            along = s + side * (w / 2 + SWITCH_BESIDE)
            if 0.05 <= along <= length - 0.05:
                out.append((a + d * along, n))
                break
    if len(out) < count and edges:                       # (no door — or fewer than wanted: on the longest wall)
        a, _b, d, n, length = max(edges, key=lambda e: e[4])
        for frac in (0.1, 0.9)[:count - len(out)]:
            out.append((a + d * length * frac, n))
    return out[:count]


def light_spots(outline, count, label_point):
    """The lights on the ceiling: one at the room's middle (label_point), two along its longer side."""
    if count <= 0:
        return []
    middle = np.asarray(label_point, dtype=float)
    if count == 1:
        return [middle]
    pts = np.array(outline, dtype=float)
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    axis = 0 if hi[0] - lo[0] >= hi[1] - lo[1] else 1
    out = []
    for j in range(count):
        p = middle.copy()
        p[axis] = lo[axis] + (hi[axis] - lo[axis]) * (j + 1) / (count + 1)
        out.append(p)
    return out


def propose_room(outline, doors, counts, label_point):
    """One room's proposal: [(kind — "light", "switch", "switch_two_way", "outlet", "data_outlet",
    "outlet_counter" —, point (2,), inward (2,) or None for a light)]."""
    on = doors_of(outline, doors)
    out = [("light", p, None) for p in light_spots(outline, counts.get("light", 0), label_point)]
    n_switch = counts.get("switch", 0)
    kind = "switch_two_way" if n_switch >= 2 else "switch"
    out += [(kind, p, n) for p, n in switch_spots(outline, on, n_switch)]
    wanted = [("outlet", counts.get("outlet", 0)), ("outlet_counter", counts.get("outlet_counter", 0)),
              ("data_outlet", counts.get("data_outlet", 0))]
    spots = wall_spots(outline, sum(n for _k, n in wanted), on)
    k = 0
    for kind_, n in wanted:                              # (the spots in turn: the outlets, the counter's, the data)
        for _ in range(n):
            if k < len(spots):
                out.append((kind_, spots[k][0], spots[k][1]))
            k += 1
    return out
