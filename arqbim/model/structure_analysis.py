"""The structure analysed (0.165, Phase 9, step 3): its analytical model a 3D space frame (core/space_frame) —
columns and beams with their concrete's modulus and their sections, the supports as made, each floor a rigid
diaphragm —; its loads: each member's own weight; each slab's G and Q carried to its beams by the area nearest to
each (the 45° rule of a rectangular bay, any shape), to its columns when it has no beams; the wind's and the
earthquake's storey forces both ways (X, Y) on the floors' nodes. Its combinations (EN 1990: ULS 6.10 with the wind
and the earthquake each way, the quasi-permanent one); per member the envelope of its forces, each beam's
deflection; the supports' reactions; the load path checked (what comes down = what goes in).

(0.222) The second order (P-Δ): each storey's sensitivity θ = P·dr / (V·h) under the wind and the earthquake each way
— P the vertical load at and above it, V its shear, dr its drift with the frame cracked (the earthquake's × q), h
its height —; θ ≤ 0,10 ignored (EC8 4.4.2.2(2), EC2 5.8.2(6)); above it that way's horizontal action multiplied by
1/(1 − θ) (EC8 4.4.2.2(3), EC2 H.2); beyond 0,20 the simplified method is told not enough, beyond 0,30 the structure
too flexible (EC8 4.4.2.2(4)).

A pre-design: the structural design is the engineer's."""

from dataclasses import dataclass, field

import numpy as np

from ..core import actions as act
from ..core import rebar as rb
from ..core import shell as sh
from ..core import slab_mesh
from ..core import space_frame as sf

TRIBUTARY_CELL = 0.20           # m: the slabs' area sampled this fine to share it among their beams
ENVELOPE_STATIONS = 21          # (0.229) a beam's moment envelope at this many points along it
SHELL_SIZE = 0.50               # (0.223) m: the slabs' mesh step…
SHELL_NODES = 2500              # …larger for a big building, its slabs' nodes about this many
NEAR_LEVEL = 0.30               # m: a beam this near a slab's level carries it
POISSON = 0.2
# (0.222) the second order: the frame's stiffness cracked, a part of the uncracked one the analysis has — under the
# earthquake one half (EC8 4.3.1(7)), under the wind (ULS) 0,4 Ecd Ic with Ecd = Ecm / γcE, γcE 1,2 (EC2 H.1.2(2),
# 5.8.6(3)); the limits of θ
CRACKED_SEISMIC = 0.5
CRACKED_WIND = 0.4 / 1.2
THETA_IGNORED = 0.10            # EC8 4.4.2.2(2); EC2 5.8.2(6): less than 10 % of the first order's effects
THETA_SIMPLE = 0.20             # EC8 4.4.2.2(3): up to here the effects × 1/(1 − θ)
THETA_MAX = 0.30                # EC8 4.4.2.2(4): never beyond
LATERAL = ("WX", "WY", "EX", "EY")


@dataclass
class PanelMesh:
    """(0.223) A slab's mesh: its height, its vertices (N, 2), its triangles, and its real area over the meshed one
    (its loads scaled by it: what goes in is the slab's)."""
    z: float
    vertices: np.ndarray
    triangles: list
    scale: float = 1.0


@dataclass
class PanelOutcome:
    """(0.223) A slab analysed as a shell: the moments to reinforce for (Wood–Armer, kNm/m) along its main
    direction (x, rebar.slab_axes's) and across it — its bottom's sagging, its top's hogging — over the ULS
    combinations; its deflection (m, quasi-permanent, from its columns and beams' joints)."""
    guid: str
    span: float                 # m: its shorter span
    m_x: float = 0.0
    m_y: float = 0.0
    m_x_top: float = 0.0
    m_y_top: float = 0.0
    deflection: float = 0.0
    combo: str = ""
    triangles: int = 0


@dataclass
class StoreySway:
    """(0.222) A storey's sway under one horizontal action (WX, WY, EX, EY) — its second order's sensitivity."""
    case: str
    level: float                # m over the foundations
    height: float               # m: the storey's
    p: float                    # kN: the vertical load at and above it (earthquake G + ψ2 Q; wind 1,35G + 1,50Q)
    v: float                    # kN: its shear
    drift: float                # m: its interstorey drift, cracked (the earthquake's × q)
    theta: float


@dataclass
class MemberOutcome:
    id: str
    guid: str
    kind: str
    length: float
    n_min: float = 0.0          # kN (compression < 0)
    n_max: float = 0.0
    v: float = 0.0              # kN, the larger shear
    m_pos: float = 0.0          # kNm sagging (a beam's span)
    m_neg: float = 0.0          # kNm hogging (its supports)
    m_column: float = 0.0       # kNm, a column's largest moment (either way)
    combo: str = ""
    deflection: float = 0.0     # m, mid-span, quasi-permanent combination (beams)


@dataclass
class Analysis:
    members: list = field(default_factory=list)        # [MemberOutcome]
    reactions: dict = field(default_factory=dict)      # node -> (Fx, Fy, Fz, Mx, My, Mz) of the ULS 1,35G+1,50Q
    service: dict = field(default_factory=dict)        # …of the characteristic G + Q (0.166: the soil's pressure)
    loads_in: float = 0.0       # kN: G + Q put in (vertical)
    reactions_up: float = 0.0   # kN: the supports' vertical reactions under G + Q
    drift_wind: float = 0.0     # the largest storey drift ratio under the wind (characteristic)
    error: str = ""
    # (0.220) each member's bending moment diagram under the first ULS combination (1,35G+1,50Q): member id ->
    # (end 1 (3,), end 2 (3,), its local z (3,) — the side a sagging moment is drawn away from —, [M kNm at stations])
    diagrams: dict = field(default_factory=dict)
    diagram_combo: str = ""
    # (0.222) the second order: each storey's sway each way; {case: 1/(1 − θ max)} of the horizontal actions that
    # were multiplied by it (θ > 0,10) in the combinations
    sways: list = field(default_factory=list)          # [StoreySway]
    amplification: dict = field(default_factory=dict)
    panels: list = field(default_factory=list)         # (0.223) [PanelOutcome]: the slabs analysed as shells
    shell_size: float = 0.0                            # …their mesh's step (m)
    # (0.229) each beam's bending moment envelope over the ULS combinations at ENVELOPE_STATIONS points evenly along
    # it: member id -> ([the largest, sagging +], [the least, hogging −]) kNm
    envelopes: dict = field(default_factory=dict)
    walls: list = field(default_factory=list)          # (0.336) [model.wall_loads.WallLoad]

    def theta(self, case=None):
        """(0.222) The largest θ (of one action, or of all) and its StoreySway (or None)."""
        rows = [s for s in self.sways if case is None or s.case == case]
        worst = max(rows, key=lambda s: s.theta, default=None)
        return (worst.theta if worst else 0.0), worst


def sway_verdict(theta):
    """(0.222) What a storey's θ asks: "ignored" (≤ 0,10), "amplified" (≤ 0,20: × 1/(1 − θ)), "rigorous" (≤ 0,30: the
    simplified method not enough, a second order analysis wanted), "flexible" (beyond: not allowed)."""
    if theta <= THETA_IGNORED:
        return "ignored"
    if theta <= THETA_SIMPLE:
        return "amplified"
    return "rigorous" if theta <= THETA_MAX else "flexible"


def _section(member, e):
    b, h = float(member.size[0]), float(member.size[1])
    if member.kind == "column":
        # (local z = the column's own x — 0.227: as it is turned in plan; its section as it is: round, L, T)
        a, iy, iz, j, _centroid = sf.section(getattr(member, "shape", "rect"), b, h, getattr(member, "web", 0.0))
        x = getattr(member, "x_dir", (1.0, 0.0))
        return (a, iy, iz, j), (float(x[0]), float(x[1]), 0.0)
    return sf.rectangle(b, h), (0.0, 0.0, 1.0)              # (a beam: local z up, h along it)


def tributary(panel, beams, nodes, cell=TRIBUTARY_CELL, walls=(), points=(), sides=None):
    """{member id: m² of the panel carried} — each bit of the panel to the beam (at its level) nearest to it. (0.336)
    walls: the load-bearing walls (core.structural.Wall) — those whose top is at its level share it too, as
    "wall:" + their GlobalId; points: nodes (column tops) sharing it too, as "node:" + their index; sides: a dict
    filled with each wall's (area on its left, on its right) — the slabs' balance over it."""
    from shapely import contains_xy
    from shapely.geometry import Polygon
    poly = Polygon(panel.outline)
    if poly.is_empty or not poly.is_valid:
        return {}
    near = [(m.id, nodes[m.n1][:2], nodes[m.n2][:2]) for m in beams if abs(nodes[m.n1][2] - panel.level) < NEAR_LEVEL]
    near += [("wall:" + w.guid, w.start, w.end) for w in walls if abs(w.top - panel.level) < NEAR_LEVEL]
    near += [("node:{}".format(k), nodes[k][:2], nodes[k][:2]) for k in points]
    if not near:
        return {}
    x0, y0, x1, y1 = poly.bounds
    xs, ys = np.arange(x0 + cell / 2, x1, cell), np.arange(y0 + cell / 2, y1, cell)
    gx, gy = np.meshgrid(xs, ys)
    inside = contains_xy(poly, gx.ravel(), gy.ravel())
    pts = np.column_stack((gx.ravel()[inside], gy.ravel()[inside]))
    if not len(pts):
        return {}
    a = np.array([p for _k, p, _q in near], dtype=float)
    b = np.array([q for _k, _p, q in near], dtype=float)
    ab = b - a
    l2 = np.maximum(np.einsum("ij,ij->i", ab, ab), 1e-12)
    t = np.clip(np.einsum("pkj,kj->pk", pts[:, None, :] - a[None, :, :], ab) / l2, 0.0, 1.0)
    closest = a[None, :, :] + ab[None, :, :] * t[:, :, None]
    dist = np.linalg.norm(pts[:, None, :] - closest, axis=2)
    # (0.337) a bit as near to two (the diagonals at a corner) shared alike — not all to the first of them: their
    # order is their GlobalIds', a new one in each project
    tied = dist <= dist.min(axis=1, keepdims=True) + 1e-9
    weight = tied / tied.sum(axis=1, keepdims=True)
    each = cell * cell * (poly.area / max(len(pts) * cell * cell, 1e-12))
    share = weight.sum(axis=0) * each
    if sides is not None:                               # (0.336) which side of each wall its bits lie on
        for k, (key, _p, _q) in enumerate(near):
            if key.startswith("wall:"):
                cross = ab[k, 0] * (pts[:, 1] - a[k, 1]) - ab[k, 1] * (pts[:, 0] - a[k, 0])
                mine = weight[:, k]
                sides[key[5:]] = (float(np.sum(mine * (cross > 0))) * each, float(np.sum(mine * (cross <= 0))) * each)
    return {key: float(share[k]) for k, (key, _p, _q) in enumerate(near) if share[k] > 1e-12}


def wall_slab_shares(model, loads):
    """(0.336) {wall GlobalId: {"G", "Q": kN, "left", "right": m², "span": m}} — of each slab at a load-bearing wall's
    top, the area nearest to it (shared with its beams as build_frame shares it), its loads, which side, the slab's
    shorter span."""
    out = {}
    if not getattr(model, "walls", ()):
        return out
    beams = [m for m in model.members if m.kind == "beam"]
    for p in model.panels:
        sides = {}
        share = tributary(p, beams, model.nodes, walls=model.walls, sides=sides)
        span = 0.0
        if any(k.startswith("wall:") for k in share):
            _x, lx, ly = rb.slab_axes(p.outline)
            span = float(min(lx, ly))
        for key, area in share.items():
            if not key.startswith("wall:"):
                continue
            entry = out.setdefault(key[5:], {"G": 0.0, "Q": 0.0, "left": 0.0, "right": 0.0, "span": 0.0})
            entry["G"] += loads.panel_g.get(p.guid, 0.0) * area
            entry["Q"] += loads.panel_q.get(p.guid, 0.0) * area
            left, right = sides.get(key[5:], (0.0, 0.0))
            entry["left"] += left
            entry["right"] += right
            entry["span"] = max(entry["span"], span)
    return out


def shell_size(model):
    """(0.223) The slabs' mesh step: SHELL_SIZE, larger for a big building (its slabs' nodes about SHELL_NODES)."""
    from shapely.geometry import Polygon
    area = 0.0
    for p in model.panels:
        poly = Polygon(p.outline)
        area += poly.area if poly.is_valid else poly.buffer(0).area
    return max(SHELL_SIZE, float(np.sqrt(area / SHELL_NODES)))


def panel_meshes(model, size=None):
    """(0.223) {panel GlobalId: PanelMesh} — each slab's mesh at the height of the frame's nodes at its level (its
    beams'), through its beams and its columns."""
    from shapely.geometry import Polygon
    size = size or shell_size(model)
    out = {}
    for p in model.panels:
        near = [n[2] for n in model.nodes if abs(n[2] - p.level) < NEAR_LEVEL]
        z = float(max(set(np.round(near, 4)), key=lambda v: sum(1 for w in near if abs(w - v) < 1e-3))) if near \
            else float(p.level)
        lines = [(model.nodes[m.n1][:2], model.nodes[m.n2][:2]) for m in model.members if m.kind == "beam"
                 and abs(model.nodes[m.n1][2] - z) < 1e-3 and abs(model.nodes[m.n2][2] - z) < 1e-3]
        lines += [(w.start, w.end) for w in getattr(model, "walls", ())          # (0.336: on its walls too)
                  if abs(w.top - p.level) < NEAR_LEVEL]
        points = [n[:2] for n in model.nodes if abs(n[2] - z) < 1e-3]
        vertices, triangles = slab_mesh.mesh(p.outline, size, lines=lines, points=points)
        if not triangles:
            continue
        tri = vertices[np.array(triangles)]
        meshed = float(np.sum(np.abs((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1])
                                     - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1])))) / 2.0
        poly = Polygon(p.outline)
        real = poly.area if poly.is_valid else poly.buffer(0).area
        out[p.guid] = PanelMesh(z, vertices, triangles, real / meshed if meshed > 1e-9 else 1.0)
    return out


def _wall_support(model, node):
    """(0.336) How a node resting on a load-bearing wall is held: its three translations, its turn about the vertical,
    and — a beam's end — its turn about the beam's axis (the beam lies on the wall: it cannot roll over), its bending
    turn free; a column's foot only its translations and the vertical turn (its top is held by its beams)."""
    ways = [np.abs(np.subtract(model.nodes[m.n2], model.nodes[m.n1])[:2]) for m in model.members
            if m.kind == "beam" and node in (m.n1, m.n2)]
    if not ways:
        return (True, True, True, False, False, True)
    dx, dy = np.sum(ways, axis=0)
    return (True, True, True, bool(dx >= dy), bool(dy > dx), True)


def _plan_distance(p, a, b):
    """(0.336) The distance in plan from p to the segment a–b, and where along it (0…1)."""
    p, a, b = (np.asarray(v, dtype=float)[:2] for v in (p, a, b))
    ab = b - a
    l2 = float(ab @ ab)
    t = float(np.clip((p - a) @ ab / l2, 0.0, 1.0)) if l2 > 1e-12 else 0.0
    return float(np.linalg.norm(p - (a + ab * t))), t


def _along(frame, m, candidates):
    """(0.223) The frame's nodes (of `candidates`) on a member's axis between its ends, from its first end."""
    a, b = np.asarray(frame.nodes[m.n1]), np.asarray(frame.nodes[m.n2])
    ab = b - a
    l2 = float(ab @ ab)
    on = []
    for k in candidates:
        if k in (m.n1, m.n2):
            continue
        p = np.asarray(frame.nodes[k])
        t = float((p - a) @ ab) / l2
        if 1e-6 < t < 1.0 - 1e-6 and np.linalg.norm(a + ab * t - p) < 1e-3:
            on.append((t, k))
    return [k for _t, k in sorted(on)]


def build_frame(model, loads, settings):
    """The SpaceFrame of an analytical model with its loads (model.structure_loads.BuildingActions) — and the cases
    it has. (0.223) members: {member id: (its analytical member, [its pieces in the frame])} — a beam cut at its
    slabs' mesh nodes; shells: {panel GlobalId: [its SpaceShells]}."""
    e = settings.ecm()
    g = e / (2.0 * (1.0 + POISSON))
    frame = sf.SpaceFrame(tolerance=1e-4)
    for p in model.nodes:
        frame.add_node(*p)
    meshes = panel_meshes(model) if getattr(settings, "slabs", "areas") == "shells" else {}
    shells, mesh_nodes = {}, set()
    frame.wall_nodes = {}                               # (0.336) a slab's nodes on a load-bearing wall: held there
    for guid, pm in meshes.items():
        ids = [frame.add_node(float(x), float(y), pm.z) for x, y in pm.vertices]
        mesh_nodes.update(ids)
        panel = next(p for p in model.panels if p.guid == guid)
        for w in getattr(model, "walls", ()):
            if abs(w.top - panel.level) >= NEAR_LEVEL:
                continue
            for k, (x, y) in zip(ids, pm.vertices):
                d, _t = _plan_distance((x, y), w.start, w.end)
                if d < 1e-3 and k not in frame.wall_nodes:
                    frame.wall_nodes[k] = w.guid
                    frame.set_support(k, (True, True, True, False, False, False))
        made = []
        for k, (a, b, c) in enumerate(pm.triangles):
            s = frame.add_shell("{}#{}".format(guid, k), ids[a], ids[b], ids[c], e, POISSON, panel.thickness)
            made.append(s)
        shells[guid] = made
    members = {}
    for m in model.members:
        (area, iy, iz, j), orientation = _section(m, e)
        chain = [m.n1] + (_along(frame, m, mesh_nodes) if m.kind == "beam" and mesh_nodes else []) + [m.n2]
        pieces = []
        for k, (n1, n2) in enumerate(zip(chain[:-1], chain[1:])):
            sm = frame.add_member(m.id if len(chain) == 2 else "{}~{}".format(m.id, k + 1), n1, n2, e, g, area, iy,
                                  iz, j, orientation)
            frame.add_member_load("G", sm, qz=-loads.member_g.get(m.id, area * act.CONCRETE_KN_M3))
            pieces.append(sm)
        members[m.id] = (m, pieces)
    for node, kind in model.supports.items():
        if kind == "wall":                                  # (0.336) resting on a load-bearing wall
            frame.set_support(node, _wall_support(model, node))
        else:
            frame.set_support(node, (True,) * 6 if kind == "fixed" else (True, True, True, False, False, False))
    beams = [m for m in model.members if m.kind == "beam"]
    for p in model.panels:
        if p.guid in shells:                                # (0.223: the slab's loads on its shells)
            scale = meshes[p.guid].scale
            for case, per in (("G", loads.panel_g), ("Q", loads.panel_q)):
                q = per.get(p.guid, 0.0)
                if q:
                    for s in shells[p.guid]:
                        frame.add_shell_load(case, s, qz=-q * scale)
            continue
        # (0.336) with its load-bearing walls: they take the part nearest to them (wall_slab_shares); with no beam,
        # its columns' tops share the rest the same way
        walls_here = [w for w in getattr(model, "walls", ()) if abs(w.top - p.level) < NEAR_LEVEL]
        beamless = not any(abs(model.nodes[m.n1][2] - p.level) < NEAR_LEVEL for m in beams)
        tops = [k for k, n in enumerate(model.nodes) if abs(n[2] - p.level) < NEAR_LEVEL] \
            if walls_here and beamless else []
        share = tributary(p, beams, model.nodes, walls=walls_here, points=tops)
        for case, per in (("G", loads.panel_g), ("Q", loads.panel_q)):
            q = per.get(p.guid, 0.0)
            if not q:
                continue
            if share:
                for mid, area in share.items():
                    if mid.startswith("wall:"):
                        continue                         # (the walls' part: not the frame's)
                    if mid.startswith("node:"):
                        frame.add_nodal_load(case, int(mid[5:]), fz=-q * area)
                        continue
                    m, pieces = members[mid]
                    length = sum(sm.length for sm in pieces)
                    for sm in pieces:
                        frame.add_member_load(case, sm, qz=-q * area / length)
            else:                                        # (a flat slab: on the columns' tops at its level)
                tops = [k for k, n in enumerate(model.nodes) if abs(n[2] - p.level) < NEAR_LEVEL]
                if tops:
                    from shapely.geometry import Polygon
                    each = q * Polygon(p.outline).area / len(tops)
                    for k in tops:
                        frame.add_nodal_load(case, k, fz=-each)
    # each storey a rigid diaphragm; the wind and the earthquake on its nodes
    cases = ["G", "Q"]
    for st, at in storey_nodes(model, loads):
        frame.add_diaphragm("piso {:.2f}".format(st.level), at)
        for case in LATERAL:
            f = lateral_force(st, case)
            if f:
                fx, fy = (f, 0.0) if case.endswith("X") else (0.0, f)
                for k in at:
                    frame.add_nodal_load(case, k, fx=fx / len(at), fy=fy / len(at))
                if case not in cases:
                    cases.append(case)
    frame.panel_shells = shells
    return frame, members, cases


def storey_nodes(model, loads):
    """[(StoreyActions, [node])]: each storey with its floor's nodes (not the supports) — one with none left out."""
    low = min((n[2] for n in model.nodes), default=0.0)
    out = []
    for st in loads.storeys:
        level = low + st.level
        at = [k for k, n in enumerate(model.nodes) if abs(n[2] - level) < NEAR_LEVEL and k not in model.supports]
        if at:
            out.append((st, at))
    return out


def lateral_force(st, case):
    """A storey's horizontal force (kN) of an action: the wind along X / Y, the earthquake (the greater type)."""
    if case == "WX":
        return st.wind_x
    if case == "WY":
        return st.wind_y
    return max(st.quake_1, st.quake_2)


def storey_sways(model, loads, results):
    """(0.222) [StoreySway] of each horizontal action the frame was solved for, storey by storey from the bottom: its
    drift the mean of its floor's sway less the one's below (the foundations' none), the analysis's (uncracked)
    divided by the cracked part — the earthquake's also × q (EC8 4.3.4: ds = q de) —; θ = P dr / (V h)."""
    floors = storey_nodes(model, loads)
    out = []
    for case in LATERAL:
        if case not in results:
            continue
        d = results[case]["disp"]
        axis = 0 if case.endswith("X") else 1
        seismic = case.startswith("E")
        scale = act.BEHAVIOUR_Q / CRACKED_SEISMIC if seismic else 1.0 / CRACKED_WIND
        below_level, below_sway = 0.0, 0.0
        for k, (st, at) in enumerate(floors):
            sway = float(np.mean([d[6 * n + axis] for n in at]))
            h = st.level - below_level
            p = sum((s.weight if seismic else 1.35 * s.g + 1.5 * s.q) for s in loads.storeys
                    if s.level > st.level - 1e-6)
            v = sum(lateral_force(s, case) for s, _ in floors[k:])
            drift = abs(sway - below_sway) * scale
            theta = p * drift / (v * h) if v > 1e-9 and h > 1e-6 else 0.0
            out.append(StoreySway(case, st.level, h, p, v, drift, theta))
            below_level, below_sway = st.level, sway
    return out


def combinations(settings, cases):
    """The ULS combinations with the wind and the earthquake each way (those the frame has), and the
    quasi-permanent one last."""
    base = act.combinations(settings, wind=False, seismic=False)
    uls, qp = base[:-1], base[-1]
    psi0, _psi1, psi2 = settings.psi()
    out = list(uls)
    for w in ("WX", "WY"):
        if w in cases:
            for sign, tag in ((1.0, "+"), (-1.0, "−")):
                out.append(("1,35G+1,50Q{}0,9{}".format(tag, w), {"G": 1.35, "Q": 1.5, w: 0.9 * sign}))
                out.append(("1,35G+{:g}Q{}1,5{}".format(1.5 * psi0, tag, w).replace(".", ","),
                            {"G": 1.35, "Q": 1.5 * psi0, w: 1.5 * sign}))
    for e in ("EX", "EY"):
        if e in cases:
            for sign, tag in ((1.0, "+"), (-1.0, "−")):
                out.append(("G+{:g}Q{}{}".format(psi2, tag, e).replace(".", ","), {"G": 1.0, "Q": psi2, e: sign}))
    return out, qp


def _chain_deflection(frame, results, factors, pieces):
    """(0.223) A beam cut in pieces: its largest deflection (m, down) from the chord of its ends, at its inner
    nodes, under a combination — across its local z."""
    nodes = [pieces[0].n1] + [sm.n2 for sm in pieces]
    zdir = pieces[0].rotation[2]
    disp = sum(float(f) * results[c]["disp"] for c, f in factors.items() if c in results)
    w = [float(disp[6 * n:6 * n + 3] @ zdir) for n in nodes]
    x = np.concatenate(([0.0], np.cumsum([sm.length for sm in pieces])))
    chord = w[0] + (w[-1] - w[0]) * x / x[-1]
    return max(0.0, float(np.max(chord - np.array(w))))


def _chain_moments(frame, results, factors, pieces, stations=11):
    """(0.220, 0.223) A member's bending moment at `stations` points evenly along it (sagging positive) under a
    combination — of the piece each point falls in, when it is cut."""
    if len(pieces) == 1:
        sm = pieces[0]
        return sf.moments_along(frame.combined_forces(results, factors, sm), frame.local_qz(sm, factors), sm.length,
                                stations)
    starts = np.concatenate(([0.0], np.cumsum([sm.length for sm in pieces])))
    forces = [(frame.combined_forces(results, factors, sm), frame.local_qz(sm, factors)) for sm in pieces]
    out = []
    for x in np.linspace(0.0, starts[-1], stations):
        k = min(int(np.searchsorted(starts, x, side="right")) - 1, len(pieces) - 1)
        f, q = forces[k]
        u = x - starts[k]
        out.append(float(f[4] + f[2] * u + q * u * u / 2.0))
    return out


def _panel_outcomes(model, frame, results, combos, qp):
    """(0.223) [PanelOutcome] of the slabs meshed as shells: in each triangle the moments turned to the slab's main
    direction, Wood–Armer's to reinforce for, the envelope over the ULS combinations; the deflection the largest of
    its nodes' under the quasi-permanent one, less its columns and beams' joints' (the frame's own nodes in it)."""
    out = []
    shells = getattr(frame, "panel_shells", {})
    own = set(range(len(model.nodes)))
    for p in model.panels:
        tris = shells.get(p.guid)
        if not tris:
            continue
        x_dir, lx, ly = rb.slab_axes(p.outline)
        c, s = float(x_dir[0]), float(x_dir[1])
        o = PanelOutcome(p.guid, min(lx, ly), triangles=len(tris))
        biggest = -1.0
        for name, factors in combos:
            for t in tris:
                mx, my, mxy = frame.combined_shell(results, factors, t)[:3]
                # (the triangle's local x is the global X laid on it: turned by the slab's main direction)
                mn = mx * c * c + my * s * s + 2.0 * mxy * c * s
                mt = mx * s * s + my * c * c - 2.0 * mxy * c * s
                mnt = (my - mx) * c * s + mxy * (c * c - s * s)
                (bx, by), (tx, ty) = sh.design_moments(mn, mt, mnt)
                o.m_x, o.m_y = max(o.m_x, bx), max(o.m_y, by)
                o.m_x_top, o.m_y_top = min(o.m_x_top, tx), min(o.m_y_top, ty)
                size = max(bx, by, -tx, -ty)
                if size > biggest:
                    biggest, o.combo = size, name
        disp = sum(float(f) * results[k]["disp"] for k, f in qp.items() if k in results)
        nodes = {v for t in tris for v in t.nodes}
        down = {v: -float(disp[6 * v + 2]) for v in nodes}
        held = [down[v] for v in nodes if v in own]
        o.deflection = max(0.0, max(down.values()) - (float(np.mean(held)) if held else 0.0))
        out.append(o)
    return out


def analyse(model, loads, settings, second_order=True):
    """The Analysis of an analytical model with its loads — (0.222) with the second order's amplification of the
    horizontal actions unless `second_order` is False (their sways still told)."""
    out = Analysis()
    if not model.members:
        if getattr(model, "walls", ()):                 # (0.336) load-bearing walls only: their loads
            out.walls = _wall_loads(model, loads, None, None)
            return out
        out.error = "no_members"
        return out
    frame, members, cases = build_frame(model, loads, settings)
    try:
        results = frame.solve(tuple(cases))
    except sf.SpaceFrameError as exc:
        out.error = str(exc)
        return out
    combos, qp = combinations(settings, cases)
    out.sways = storey_sways(model, loads, results)
    for case in LATERAL:
        theta, _worst = out.theta(case)
        if second_order and theta > THETA_IGNORED:
            out.amplification[case] = 1.0 / (1.0 - theta) if theta < 0.9 else 10.0
    if out.amplification:
        combos = [(name, {c: f * out.amplification.get(c, 1.0) for c, f in factors.items()})
                  for name, factors in combos]
    env = frame.envelope(results, combos)
    for mid, (m, pieces) in members.items():           # (0.223: a beam cut at its slabs' nodes — over its pieces)
        rs = [env[sm.id] for sm in pieces]
        worst = max(rs, key=lambda r: max(r["m_pos"], -r["m_neg"], abs(r["n_min"]), r["vz"]))
        o = MemberOutcome(mid, m.guid, m.kind, sum(sm.length for sm in pieces), min(r["n_min"] for r in rs),
                          max(r["n_max"] for r in rs), max(max(r["vz"], r["vy"]) for r in rs),
                          max(r["m_pos"] for r in rs), min(r["m_neg"] for r in rs), combo=worst["combo"])
        if m.kind == "column":
            o.m_column = max(max(abs(r["m_pos"]), abs(r["m_neg"]), r["mz"]) for r in rs)
        elif len(pieces) == 1:
            o.deflection = frame.deflection_mid(results, qp[1], pieces[0])
        else:
            o.deflection = _chain_deflection(frame, results, qp[1], pieces)
        out.members.append(o)
    # the load path: what comes down — (0.336) to the walls holding a slab's shells too
    uls = {"G": 1.0, "Q": 1.0}
    for node in list(model.supports) + [k for k in getattr(frame, "wall_nodes", {}) if k not in model.supports]:
        rz = sum(results[c]["reactions"][node][2] * f for c, f in uls.items() if c in results)
        out.reactions_up += rz
    for case in ("G", "Q"):
        if case not in results:
            continue
        put = 0.0
        for sm in frame.members:
            put += -sm.loads.get(case, (0.0, 0.0, 0.0))[2] * sm.length
        for s in frame.shells:
            put += -s.loads.get(case, (0.0, 0.0, 0.0))[2] * s.area
        for node, f6 in frame.nodal_loads.get(case, {}).items():
            put += -f6[2]
        out.loads_in += put
    first = combos[0][1]
    out.diagram_combo = combos[0][0]
    for mid, (m, pieces) in members.items():            # (0.220: the moments along each member, to draw them)
        p1, p2 = np.asarray(model.nodes[m.n1], dtype=float), np.asarray(model.nodes[m.n2], dtype=float)
        axes = sf.local_axes(p1, p2, pieces[0].orientation)
        out.diagrams[mid] = (p1, p2, axes[2], _chain_moments(frame, results, first, pieces))
        if m.kind == "beam":                            # (0.229: the envelope along it, where its bars stop)
            each = np.array([_chain_moments(frame, results, factors, pieces, ENVELOPE_STATIONS)
                             for _name, factors in combos])
            out.envelopes[mid] = (each.max(axis=0).tolist(), each.min(axis=0).tolist())
    out.panels = _panel_outcomes(model, frame, results, combos, qp[1])
    out.shell_size = shell_size(model) if out.panels else 0.0
    for node in model.supports:
        out.reactions[node] = tuple(sum(results[c]["reactions"][node][k] * f for c, f in first.items()
                                        if c in results) for k in range(6))
        out.service[node] = tuple(sum(results[c]["reactions"][node][k] for c in ("G", "Q") if c in results)
                                  for k in range(6))
    # the wind's drift: the largest storey sway over its height
    for w in ("WX", "WY"):
        if w not in results:
            continue
        d = results[w]["disp"]
        for m in model.members:
            if m.kind != "column":
                continue
            a, b = np.asarray(model.nodes[m.n1]), np.asarray(model.nodes[m.n2])
            h = abs(b[2] - a[2])
            if h < 1e-6:
                continue
            sway = np.hypot(*(d[6 * m.n2:6 * m.n2 + 2] - d[6 * m.n1:6 * m.n1 + 2]))
            out.drift_wind = max(out.drift_wind, float(sway / h))
    out.walls = _wall_loads(model, loads, frame, results)          # (0.336)
    return out


def _wall_loads(model, loads, frame, results):
    """(0.336) The load-bearing walls' loads (model.wall_loads): the slabs' part at their tops, the reactions of the
    frame's members resting on them (G and Q) — and of a slab's shells held by them —, the storeys' horizontal
    forces."""
    from . import wall_loads as wl
    if not getattr(model, "walls", ()):
        return []
    reactions = {}
    if frame is not None and results is not None:
        held = dict(getattr(model, "on_walls", {}))
        held.update({k: g for k, g in getattr(frame, "wall_nodes", {}).items() if k not in held})
        for node, guid in held.items():
            entry = reactions.setdefault(guid, {"G": 0.0, "Q": 0.0})
            for case in ("G", "Q"):
                if case in results:
                    entry[case] += float(results[case]["reactions"][node][2])
    slabs = wall_slab_shares(model, loads)
    if frame is not None and getattr(frame, "wall_nodes", None):
        for entry in slabs.values():                    # (the shells' reactions bring the slabs' loads already)
            entry["G"] = entry["Q"] = 0.0
    low = min([w.base for w in model.walls] + [n[2] for n in model.nodes])
    return wl.wall_loads(model, loads, slabs, reactions, lateral_force, low)
