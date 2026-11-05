"""The actions on a building's structure (0.164, Phase 9, step 2): from its analytical model and its settings —
each slab's permanent load (its own weight, finishes, partitions) and imposed one (by its use; the highest slab a
roof), each member's own weight; each storey's seismic weight (G + ψ2 Q), the wind's and the earthquake's forces on
it, both ways (X and Y). What the structural analysis (step 3) is loaded with, and what the dialog tells."""

from dataclasses import dataclass, field

import numpy as np

from ..core import actions as act
from ..core import space_frame as sf

WALL_KN_M3 = 15.0               # kN/m³: a wall's weight (masonry, plastered — a mean, on the safe side for blocks)
SAME_FLOOR = 0.5                # m: levels this near (a slab's top over its beams') are one floor


@dataclass
class StoreyActions:
    level: float                # its height over the foundations (m)
    area: float = 0.0           # its slabs' area (m²)
    g: float = 0.0              # kN: permanent
    q: float = 0.0              # kN: imposed
    weight: float = 0.0         # kN: seismic (G + ψ2 Q)
    width_x: float = 0.0        # m: the building across X (the wind blowing along Y meets it)
    width_y: float = 0.0
    wind_x: float = 0.0         # kN: the wind blowing along X
    wind_y: float = 0.0
    quake_1: float = 0.0        # kN: the seismic action of type 1 (either way)
    quake_2: float = 0.0


@dataclass
class BuildingActions:
    storeys: list = field(default_factory=list)
    panel_g: dict = field(default_factory=dict)        # panel GlobalId -> kN/m² permanent (with its own weight)
    panel_q: dict = field(default_factory=dict)        # …imposed
    member_g: dict = field(default_factory=dict)       # member id -> kN/m (its own weight)
    base_1: float = 0.0         # kN: the seismic base shear, type 1
    base_2: float = 0.0
    period: float = 0.0         # s
    sd_1: float = 0.0
    sd_2: float = 0.0


def _polygon_area(outline):
    x = np.array([p[0] for p in outline], dtype=float)
    y = np.array([p[1] for p in outline], dtype=float)
    return abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))) / 2.0


def _imposed(settings, uses, guid, roof):
    """(0.218) A slab's imposed load (kN/m²) and its ψ: of its own use when it has one (a roof's, or the snow when
    greater), else the project's for its floors or its roof."""
    use = uses.get(guid) if uses else None
    if not use or use not in act.USES:
        return settings.imposed(roof), settings.psi(roof)
    q, psi = act.USES[use][0], act.USES[use][1:]
    if roof and settings.snow() > q:
        return settings.snow(), (act.SNOW_PSI_HIGH if settings.altitude > 1000.0 else act.SNOW_PSI)
    return q, psi


def building_actions(model, settings, walls=(), foundation=None, uses=None):
    """The BuildingActions of an analytical model (core.structural) with these settings (core.actions.Settings).
    walls: [(volume m³, bottom, top)] of the walls, for their weight. uses (0.218): {slab GlobalId: its own use}."""
    out = BuildingActions()
    nodes = np.asarray(model.nodes, dtype=float).reshape(-1, 3)
    if not len(nodes) and not model.panels:
        return out
    low = foundation if foundation is not None else (float(nodes[:, 2].min()) if len(nodes) else 0.0)
    top_level = max([p.level for p in model.panels] + [float(nodes[:, 2].max()) if len(nodes) else low])
    # loads on the slabs and members
    for p in model.panels:
        roof = abs(p.level - top_level) < 0.05
        out.panel_g[p.guid] = p.thickness * act.CONCRETE_KN_M3 + settings.finishes + (0.0 if roof else settings.partitions)
        out.panel_q[p.guid] = _imposed(settings, uses, p.guid, roof)[0]
    for m in model.members:                             # (0.227: a column's section as it is — round, L, T)
        area = sf.section(m.shape, m.size[0], m.size[1], m.web)[0] if m.kind == "column" else m.size[0] * m.size[1]
        out.member_g[m.id] = area * act.CONCRETE_KN_M3
    # the storeys: the levels with slabs or beams, over the foundations
    found = sorted({round(p.level, 3) for p in model.panels}
                   | {round(float(model.nodes[m.n1][2]), 3) for m in model.members if m.kind == "beam"})
    levels = []                                     # (a slab on its beams — 3,15 over 3,00 — is one floor: its top)
    for z in found:
        if levels and z - levels[-1] < SAME_FLOOR:
            levels[-1] = z
        else:
            levels.append(z)
    levels = [z for z in levels if z > low + 0.5]
    storeys = [StoreyActions(level=z - low) for z in levels]
    if not storeys:
        return out
    abs_levels = levels

    def storey_of(z):
        """The storey a height belongs to (the one at or above it — its weight goes to the floor it hangs from)."""
        return min(range(len(abs_levels)), key=lambda k: abs(abs_levels[k] - z))

    for p in model.panels:
        k = storey_of(p.level)
        area = _polygon_area(p.outline)
        roof = abs(p.level - top_level) < 0.05
        psi2 = _imposed(settings, uses, p.guid, roof)[1][2]
        st = storeys[k]
        st.area += area
        st.g += out.panel_g[p.guid] * area
        st.q += out.panel_q[p.guid] * area
        st.weight += (out.panel_g[p.guid] + psi2 * out.panel_q[p.guid]) * area
    for m in model.members:
        a, b = np.asarray(model.nodes[m.n1]), np.asarray(model.nodes[m.n2])
        w = out.member_g[m.id] * float(np.linalg.norm(b - a))
        if m.kind == "beam":
            k = storey_of(float(a[2]))
            storeys[k].g += w
            storeys[k].weight += w
        else:                                           # (a column: half to the floor above, half to the one below)
            for z in (float(a[2]), float(b[2])):
                if z > low + 0.5:
                    k = storey_of(z)
                    storeys[k].g += w / 2
                    storeys[k].weight += w / 2
    for volume, bottom, top in walls:
        w = float(volume) * WALL_KN_M3
        for z in (bottom, top):
            if z > low + 0.5:
                k = storey_of(z)
                storeys[k].g += w / 2
                storeys[k].weight += w / 2
    # the building's width across each way, at each storey: of what stands on it (nodes, slabs)
    xy = [tuple(p[:2]) for p in model.nodes] + [tuple(q) for p in model.panels for q in p.outline]
    if xy:
        pts = np.array(xy, dtype=float)
        wx, wy = float(np.ptp(pts[:, 0])), float(np.ptp(pts[:, 1]))
        for st in storeys:
            st.width_x, st.width_y = wx, wy
    heights = [st.level for st in storeys]
    wind_x = act.wind_storey_forces(heights, [st.width_y for st in storeys], settings.wind_zone, settings.terrain)
    wind_y = act.wind_storey_forces(heights, [st.width_x for st in storeys], settings.wind_zone, settings.terrain)
    weights = [st.weight for st in storeys]
    out.base_1, f1, out.period, out.sd_1 = act.seismic_storey_forces(heights, weights, settings, 1)
    out.base_2, f2, _t, out.sd_2 = act.seismic_storey_forces(heights, weights, settings, 2)
    for k, st in enumerate(storeys):
        st.wind_x, st.wind_y, st.quake_1, st.quake_2 = wind_x[k], wind_y[k], f1[k], f2[k]
    out.storeys = storeys
    return out
