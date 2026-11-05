"""Structure automation (0.94), pure geometry: which columns a beam goes between — as the ArqSynth Modeler's
"Vigas": columns in a line along X or along Y (within a tolerance), only neighbours."""

TOLERANCE = 0.05               # m: columns this near the same line are in line


def _lines(points, along, tol):
    """Groups of ids whose coordinate across `along` (0: x, 1: y) agree within `tol`, each sorted along it."""
    across = 1 - along
    order = sorted(points, key=lambda k: points[k][across])
    groups, current = [], []
    for k in order:
        if current and abs(points[k][across] - points[current[0]][across]) > tol:
            groups.append(current)
            current = []
        current.append(k)
    if current:
        groups.append(current)
    return [sorted(g, key=lambda k: points[k][along]) for g in groups if len(g) > 1]


def proposal_nodes(walls, max_span=5.0, tol=0.05):
    """Where a structure proposed from walls puts its columns (0.98): walls [(start (x, y), end (x, y),
    thickness)] -> (nodes [(x, y)], per wall the nodes along it in order [[node index]]). A node at each wall's
    corner, T junction and crossing (where the axes meet), at each free end, and more along a wall between two
    nodes further apart than `max_span`, evenly."""
    import math
    import numpy as np
    segs = [(np.array(a, dtype=float), np.array(b, dtype=float), float(t)) for a, b, t in walls]
    points = []

    def cross_point(i, j):
        """Where the axis lines of walls i and j meet, or None (parallel)."""
        (p, q, _ti), (r, s, _tj) = segs[i], segs[j]
        d1, d2 = q - p, s - r
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-9:
            return None
        u = ((r - p)[0] * d2[1] - (r - p)[1] * d2[0]) / den
        return p + d1 * u

    def near_segment(x, j, reach):
        r, s, _t = segs[j]
        d = s - r
        length = float(np.linalg.norm(d))
        if length < 1e-9:
            return False
        u = float(np.dot(x - r, d) / length)
        return -reach <= u <= length + reach and abs(float(d[0] * (x - r)[1] - d[1] * (x - r)[0])) / length <= reach

    for i, (a, b, ti) in enumerate(segs):
        for end in (a, b):
            node = end
            for j, (_r, _s, tj) in enumerate(segs):
                if j != i and near_segment(end, j, (ti + tj) / 2 + tol):
                    c = cross_point(i, j)
                    if c is not None and np.linalg.norm(c - end) <= (ti + tj) / 2 + tol:
                        node = c                         # (a corner / T: where the axes meet)
                        break
            points.append(node)
        for j in range(i + 1, len(segs)):                 # crossings in the middle of both
            c = cross_point(i, j)
            if c is not None and near_segment(c, i, -tol) and near_segment(c, j, -tol):
                points.append(c)
    nodes = []
    for p in points:                                      # (the same place once)
        if not any(np.linalg.norm(p - n) <= tol * 2 for n in nodes):
            nodes.append(p)
    along = []
    for i, (a, b, t) in enumerate(segs):
        d = b - a
        length = float(np.linalg.norm(d))
        if length < 1e-9:
            along.append([])
            continue
        mine = sorted((float(np.dot(nodes[k] - a, d) / length), k) for k in range(len(nodes))
                      if near_segment(nodes[k], i, t / 2 + tol))
        seq = []
        for (u0, k0), (u1, _k1) in zip(mine, mine[1:] + [mine[-1]]):
            seq.append(k0)
            if u1 - u0 > max_span + 1e-9:                 # (more between them: none further apart than max_span)
                parts = int(math.ceil((u1 - u0) / max_span))
                for m in range(1, parts):
                    nodes.append(a + d / length * (u0 + (u1 - u0) * m / parts))
                    seq.append(len(nodes) - 1)
        along.append(seq)
    return [(float(n[0]), float(n[1])) for n in nodes], along


def bays(points, edges):
    """The closed bays of a plan graph (0.96: columns joined by beams): [[edge indices]] round each smallest
    closed contour — the outer one left out. points: {node: (x, y)}; edges: [(a, b)]."""
    import math
    adjacent = {}
    for k, (a, b) in enumerate(edges):
        if a == b or a not in points or b not in points:
            continue
        adjacent.setdefault(a, []).append((b, k))
        adjacent.setdefault(b, []).append((a, k))

    def angle(a, b):
        return math.atan2(points[b][1] - points[a][1], points[b][0] - points[a][0])

    for node in adjacent:
        adjacent[node].sort(key=lambda nk: angle(node, nk[0]))
    used, out = set(), []
    for k, (a, b) in enumerate(edges):
        for start in ((a, b), (b, a)):
            if start in used or start[0] not in adjacent:
                continue
            ring, ring_edges, (u, v), edge = [], [], start, k
            while (u, v) not in used:
                used.add((u, v))
                ring.append(u)
                ring_edges.append(edge)
                # at v, the next edge clockwise from the one we came by: the smallest contour on the left
                around = adjacent[v]
                back = next(i for i, (n, e) in enumerate(around) if n == u and e == edge)
                u, (v, edge) = v, around[(back - 1) % len(around)]
                if len(ring) > len(edges) + 1:
                    break
            area = sum(points[ring[i]][0] * points[ring[(i + 1) % len(ring)]][1]
                       - points[ring[(i + 1) % len(ring)]][0] * points[ring[i]][1] for i in range(len(ring))) / 2
            if area > 1e-9 and len(ring) >= 3:            # counter-clockwise: a bay (the outer one runs clockwise)
                out.append(ring_edges)
    return out


def neighbour_pairs(points, tol=TOLERANCE):
    """[(a, b)] of the columns (points: {id: (x, y)}) next to each other in a line along X, then along Y."""
    out = []
    for along in (0, 1):
        for line in _lines(points, along, tol):
            out += list(zip(line, line[1:]))
    return out
