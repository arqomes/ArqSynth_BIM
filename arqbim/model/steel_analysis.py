"""(0.516) The steel structure analysed and checked by Eurocode 3 — the plan's step 8, for pre-design: the steel
pieces as a space frame (core/space_frame) — each piece its line (its section's middle), cut where another piece meets
it (a purlin on a rafter, a brace at a column, a beam on a girder: their lines within half their depths of each other;
the node on the deeper one's line), the columns' feet fixed —, loaded by their own weight, the roof's cladding and the
roof's imposed load or snow (the project's actions: the greater of the two, NP EN 1991-1-1 3.3.2) carried by the
purlins over the width each one takes; combined by EN 1990 (1,35 G + 1,5 Q; G + Q for the deflections); each piece
checked by core/ec3 with the forces of its worst part, its buckling lengths its own length about y and its longest part
about z (held by what meets it), its deflection against L/200.

Wind and the earthquake are not taken here, nor the floors' loads on steel beams (the slabs' analysis is the
concrete structure's) — said in the results. Units: kN, m."""

import math
from dataclasses import dataclass, field

import numpy as np

from ..core import ec3, steel
from ..core import space_frame as sf

ROOF_DEAD = 0.20                # kN/m²: the roof's cladding (a sandwich panel and its fixings)
REACH = 0.05                    # m: two lines this far apart past half their depths meet
NODE = 0.03                     # m: points this near are one node
DEFLECTION = 200.0              # L / 200 (a roof's members, EN 1993-1-1 NA)
BRACE_BENDING = 1e-3            # a brace's bending stiffness, of its section's: as pinned (a bar)
END_SNAP = 0.30                 # m: a piece's end this near where another meets it rests on it
E_KPA, G_KPA = steel.E * 1000.0, steel.G * 1000.0
COMBOS = (("1,35G + 1,5Q", {"G": 1.35, "Q": 1.5}), ("1,35G", {"G": 1.35}), ("1,0G + 1,5Q", {"G": 1.0, "Q": 1.5}))
SLS = {"G": 1.0, "Q": 1.0}


@dataclass
class Piece:
    guid: str
    mark: str
    prefix: str
    section: str
    grade: str
    a: np.ndarray               # its line's ends (its section's middle)
    b: np.ndarray
    up: np.ndarray              # its section's depth way (the frame's local z)
    depth: float                # m
    stops: list = field(default_factory=list)       # [(t along it 0..1, node)]


@dataclass
class Result:
    rows: list = field(default_factory=list)
    error: str = ""
    notes: list = field(default_factory=list)
    loads: dict = field(default_factory=dict)


def pieces_of(doc):
    """The steel pieces as lines: [Piece]."""
    marks, found = doc.ifc.steel_marks()
    out = []
    for p in found:
        if p["prefix"] == "Ch":
            continue
        g = p["guid"]
        kind = doc.ifc.kind_of(g)
        sec = steel.get(doc.ifc.steel_section(g) or "")
        if sec is None:
            continue
        m = doc.ifc.placement(g)
        up = m[:3, 1] / np.linalg.norm(m[:3, 1])
        if kind == "column":
            centre, _x, _half, base, top = doc.ifc.column_box(g)
            a, b = np.array((centre[0], centre[1], base)), np.array((centre[0], centre[1], top))
        else:
            a, b = (np.asarray(v, dtype=float) for v in doc.ifc._beam_line(g))
        if float(np.linalg.norm(b - a)) < 0.05:
            continue
        out.append(Piece(g, marks.get(g, ""), p["prefix"], sec.name, p["grade"] or "S275", a, b, up,
                         steel.size(sec)[1] / 1000.0))
    return out


def _closest(a0, a1, b0, b1):
    """(s, t, distance) of the nearest points of two segments' lines (s, t along each, 0..1), or None if parallel."""
    u, v, w = a1 - a0, b1 - b0, a0 - b0
    uu, vv, uv = float(u @ u), float(v @ v), float(u @ v)
    den = uu * vv - uv * uv
    if den < 1e-12 * uu * vv:
        return None
    s = (uv * float(v @ w) - vv * float(u @ w)) / den
    t = (uu * float(v @ w) - uv * float(u @ w)) / den
    return s, t, float(np.linalg.norm((a0 + u * s) - (b0 + v * t)))


def _node(nodes, p):
    for k, q in enumerate(nodes):
        if float(np.linalg.norm(q - p)) <= NODE:
            return k
    nodes.append(np.asarray(p, dtype=float))
    return len(nodes) - 1


LINK = (0.05, 1e-3, 1e-3, 1e-3)  # (A m², Iy, Iz, J m⁴) an eccentricity's link: rigid next to the pieces
FREE = {frozenset(("CV",)), frozenset(("CV", "M"))}     # (an X's diagonals cross free; a brace and a purlin too)


def frame_of(pieces):
    """The space frame of the pieces: (SpaceFrame, {member id: piece index}, nodes) — each piece on its own line, cut
    at its ends and where another meets it; where their lines pass apart (a purlin on a rafter's top), a short rigid
    link between them (the eccentricity); a piece's end that near a meeting rests there (no stub left)."""
    nodes = []
    for p in pieces:
        p.stops = [(0.0, _node(nodes, p.a)), (1.0, _node(nodes, p.b))]
    links = []

    def meet(piece, u, length):
        """The node where a piece is met at u (0..1), on its own line: cut there — or, that near one of its ends,
        that end moved there."""
        k = _node(nodes, piece.a + (piece.b - piece.a) * u)
        if u * length <= END_SNAP:
            piece.stops[0] = (0.0, k)
        elif (1.0 - u) * length <= END_SNAP:
            piece.stops[1] = (1.0, k)
        else:
            piece.stops.append((u, k))
        return k

    for i, p in enumerate(pieces):
        for j in range(i + 1, len(pieces)):
            q = pieces[j]
            if frozenset((p.prefix, q.prefix)) in FREE:
                continue
            found = _closest(p.a, p.b, q.a, q.b)
            if found is None:
                continue
            s, t, d = found
            lp, lq = float(np.linalg.norm(p.b - p.a)), float(np.linalg.norm(q.b - q.a))
            slack_p, slack_q = 0.3 / lp, 0.3 / lq
            if d > (p.depth + q.depth) / 2.0 + REACH or not (-slack_p <= s <= 1 + slack_p) \
                    or not (-slack_q <= t <= 1 + slack_q):
                continue
            s, t = min(max(s, 0.0), 1.0), min(max(t, 0.0), 1.0)
            kp, kq = meet(p, s, lp), meet(q, t, lq)
            if kp != kq:
                links.append((kp, kq))
    used = sorted({k for p in pieces for _t, k in p.stops} | {k for pair in links for k in pair})
    frame = sf.SpaceFrame(tolerance=1e-4)
    place = {k: frame.add_node(*nodes[k]) for k in used}
    nodes = [nodes[k] for k in used]
    for p in pieces:
        p.stops = [(t, place[k]) for t, k in p.stops]
    for n, (k0, k1) in enumerate(sorted(set(links))):
        way = nodes[place[k1]] - nodes[place[k0]]
        up = (1.0, 0.0, 0.0) if abs(float(way[2])) > 0.9 * float(np.linalg.norm(way)) else (0.0, 0.0, 1.0)
        frame.add_member("link/{}".format(n), place[k0], place[k1], E_KPA, G_KPA, *LINK, orientation=up)
    owners = {}
    for i, p in enumerate(pieces):
        props = steel.properties(p.section)
        area, iy, iz, it = props["A"] * 1e-4, props["Iy"] * 1e-8, props["Iz"] * 1e-8, max(props["It"], 1e-3) * 1e-8
        if p.prefix == "CV":                            # (a brace: pinned at its ends — a bar, no bending to speak of)
            iy, iz = iy * BRACE_BENDING, iz * BRACE_BENDING
        seen = sorted({(round(t, 6), k) for t, k in p.stops})
        chain = []
        for t, k in seen:
            if not chain or chain[-1][1] != k:
                chain.append((t, k))
        for c, ((_t0, k0), (_t1, k1)) in enumerate(zip(chain[:-1], chain[1:])):
            if k0 == k1 or float(np.linalg.norm(nodes[k0] - nodes[k1])) < 1e-3:
                continue
            mid = "{}/{}".format(p.guid, c)
            m = frame.add_member(mid, k0, k1, E_KPA, G_KPA, area, iy, iz, it, orientation=tuple(p.up))
            owners[m.id] = i
    return frame, owners, nodes


def _widths(pieces):
    """{purlin index: the roof's width it carries (m, along the slope)} — half the way to the next purlin each side
    (an edge's: half the way in and 0,15 m out)."""
    out = {}
    purlins = [i for i, p in enumerate(pieces) if p.prefix == "M"]
    for i in purlins:
        p = pieces[i]
        d = (p.b - p.a) / np.linalg.norm(p.b - p.a)
        across = np.cross(p.up, d)
        sides = {1: [], -1: []}
        for j in purlins:
            if j == i:
                continue
            q = pieces[j]
            dq = (q.b - q.a) / np.linalg.norm(q.b - q.a)
            if abs(float(dq @ d)) < 0.99:
                continue
            rel = q.a - p.a
            off = float(rel @ across)
            if abs(float(rel @ p.up)) > 0.5 or abs(off) > 4.0 or abs(off) < 0.05:
                continue
            sides[1 if off > 0 else -1].append(abs(off))
        near = [min(v) / 2.0 if v else None for v in (sides[1], sides[-1])]
        known = [v for v in near if v is not None]
        out[i] = sum(v if v is not None else 0.15 for v in near) if known else 1.0
    return out


def analyse(doc, settings=None):
    """The steel structure analysed and checked: Result (rows a piece — mark, piece, section, grade, N, M, V kN /
    kN·m, deflection, utilisation, the governing check, ok —, the notes, the loads taken)."""
    settings = settings or doc.ifc.structural_settings()
    out = Result()
    pieces = pieces_of(doc)
    if not pieces:
        return out
    frame, owners, nodes = frame_of(pieces)
    columns = [i for i, p in enumerate(pieces) if p.prefix == "P"]
    feet = []
    for i in columns:
        p = pieces[i]
        feet.append(p.stops[0][1] if p.a[2] <= p.b[2] else p.stops[1][1])     # (its lower end's node)
    if not columns:
        bottom = min(float(n[2]) for n in nodes)
        feet = [k for k, n in enumerate(nodes) if float(n[2]) <= bottom + 0.05]
    for k in set(feet):
        frame.set_support(k)
    imposed = settings.imposed(roof=True)
    widths = _widths(pieces)
    out.loads = {"dead": ROOF_DEAD, "imposed": imposed, "snow": settings.snow()}
    for m in frame.members:
        if m.id not in owners:                          # (an eccentricity's link: no weight of its own)
            continue
        p = pieces[owners[m.id]]
        weight = steel.properties(p.section)["mass"] * 9.81 / 1000.0
        frame.add_member_load("G", m, qz=-weight)
        if owners[m.id] in widths:
            w = widths[owners[m.id]]
            frame.add_member_load("G", m, qz=-ROOF_DEAD * w)
            frame.add_member_load("Q", m, qz=-imposed * w * abs(float(p.up[2])))
    try:
        results = frame.solve(("G", "Q"))
    except sf.SpaceFrameError as exc:
        out.error = str(exc)
        return out
    env = frame.envelope(results, COMBOS)
    by_piece = {}
    for m in frame.members:
        if m.id in owners:
            by_piece.setdefault(owners[m.id], []).append(m)
    for i, p in enumerate(pieces):
        members = by_piece.get(i, [])
        if not members:
            continue
        n = min(env[m.id]["n_min"] for m in members)
        tension = max(env[m.id]["n_max"] for m in members)
        my = max(max(env[m.id]["m_pos"], -env[m.id]["m_neg"]) for m in members)
        mz = max(env[m.id]["mz"] for m in members)
        vz = max(env[m.id]["vz"] for m in members)
        vy = max(env[m.id]["vy"] for m in members)
        length = float(np.linalg.norm(p.b - p.a))
        longest = max(m.length for m in members)
        axial = n if abs(n) >= tension else tension
        notes = []
        if p.prefix == "CV":                            # (an X's diagonals: tension only — the one squeezed buckles,
            axial, my, mz, vz, vy = tension, 0.0, 0.0, 0.0, 0.0        # the other holds)
            notes.append("tension_only")
        found = ec3.check(p.section, p.grade, axial, my, mz, vz, vy, length, longest)
        found["notes"] = found["notes"] + notes
        deflection = 0.0
        if p.prefix != "CV" and abs(float((p.b - p.a)[2])) < 0.5 * length:    # (a beam, a rafter, a purlin)
            for m in members:
                deflection = max(deflection, frame.deflection_mid(results, SLS, m) / (m.length / DEFLECTION))
        util = max(found["util"], deflection)
        check = found["check"] if found["util"] >= deflection else "delta"
        out.rows.append({"guid": p.guid, "mark": p.mark, "prefix": p.prefix, "section": steel.display(p.section),
                         "grade": p.grade, "n_ed": axial, "m_ed": max(my, mz), "v_ed": max(vz, vy),
                         "deflection": deflection, "utilisation": util, "governing": check, "ok": util <= 1.0,
                         "notes": found["notes"], "class": found["class"]})
    out.notes = ["wind", "floors"]
    return out
