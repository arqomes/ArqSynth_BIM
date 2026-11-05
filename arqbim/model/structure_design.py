"""The structure designed (0.166, Phase 9, step 4): each concrete member verified by Eurocode 2 (core.ec2) with its
forces from the analysis (0.165) — a beam with the envelope over its pieces, a column with its greatest compression
and moment, a footing with the reaction of the column on it (ultimate and service; 0.228: a pile cap by struts and
ties, a strip footing with its wall's weight), a slab with its loads —, and what
its reinforcement needs to be laid out on it (core.rebar): how far a beam's bars run into its supports, whether a
column's go down into a footing and on into a column above, a slab's main direction — (0.224) and the beams it rests
on, for its top bars. What the verification window shows, and what goes into the IFC (IfcReinforcingBar) with each
element.

A pre-design: the structural design is the engineer's."""

import math
from dataclasses import dataclass, field

import numpy as np

from ..core import actions as act
from ..core import ec2
from ..core import rebar as rb
from ..core import slab_mesh

NEAR = 0.60                     # m: a footing's middle this near a support (plan)
FOOTING_COVER_DOWN = 0.08       # m: a column's bars stop this far over a footing's underside (its cover, its mesh)
NEAR_LEVEL = 0.30               # (0.224) m: a beam this near a slab's level holds it…
MIN_SUPPORT = 0.30              # …along this much of it at least


@dataclass
class ElementDesign:
    guid: str
    kind: str                   # "beam" | "column" | "footing" | "slab"
    design: ec2.Design
    span: float = 0.0           # m: a beam's span, a column's height, a slab's shorter span, a footing's length
    info: dict = field(default_factory=dict)    # for the layout: ext (beam), into / lap (column), x_dir (slab)

    def stored(self, settings):
        """What is kept with its bars in the IFC (so they can be laid out again when it changes): JSON-able."""
        d = self.design
        out = {"kind": self.kind, "cover": d.cover, "concrete": settings.concrete, "steel": settings.steel}
        for key in ("bottom", "top", "bars", "links", "mesh_x", "mesh_y", "top_x", "top_y", "vertical",
                    "horizontal"):                      # (0.342: a concrete wall's)
            value = getattr(d, key)
            if value is not None:
                out[key] = list(value)
        if d.bottom2 or d.top2:                         # (0.225) a beam's bars in two layers
            out["layers"] = [int(d.bottom2), int(d.top2)]
        for face in ("bottom", "top"):                  # (0.229) the bars that stop: where
            if getattr(d, face + "_zones", None):
                out[face + "_cont"] = int(getattr(d, face + "_cont"))
                out[face + "_zones"] = [list(z) for z in getattr(d, face + "_zones")]
        out.update(self.info)
        return out


def _wall_bars_info(model, guid, footings):
    """(0.342) How a concrete wall's vertical bars start and end (core.rebar.wall_sets): into the strip footing under it
    (its depth less its cover and mesh), and lapped with the wall standing on it."""
    info = {}
    base = getattr(model, "wall_bases", {}).get(guid)
    if base is not None and base[0] == "footing":
        foot = next((f for f in footings if f.guid == base[1]), None)
        if foot is not None and foot.depth > 0.0:
            info["into"] = round(max(float(foot.depth) - ec2.COVER_FOOTING - 0.02, 0.0), 3)
    if any(b is not None and b[0] == "wall" and guid in b[1] for b in getattr(model, "wall_bases", {}).values()):
        info["lap"] = True
    return info


def _walls(analysis, settings, model=None, footings=()):
    """(0.337) [ElementDesign] of the load-bearing walls with their loads (model.wall_loads.WallLoad): each metre of
    their length less their openings — at the top what comes on them, at mid-height half their own weight more, at
    the base all of it (ULS 1,35G+1,50Q); the floors' part at the top, their balance; the largest horizontal force in
    their plane (the wind × 1,5, the earthquake × 1); the permanent loads alone for the shear's friction. Masonry ones
    verified by Eurocode 6 (core.ec6); (0.342) concrete ones by Eurocode 2 (core.ec2.wall: their bars too)."""
    from ..core import ec6
    fck, fyk = act.CONCRETE[settings.concrete], act.STEEL[settings.steel]
    out = []
    for w in getattr(analysis, "walls", ()):
        net = max(w.net, 1e-9)
        top = (act.GAMMA_G * w.top_g + act.GAMMA_Q * w.top_q) / net
        own = act.GAMMA_G * w.self_g / net
        floors = (act.GAMMA_G * w.slab_g + act.GAMMA_Q * w.slab_q) / net
        shear = max((v * (1.5 if case.startswith("W") else 1.0) for case, v in w.shear.items()), default=0.0)
        info = {}
        if w.material == "masonry":                     # (0.346: its type's masonry, else the project's)
            masonry = getattr(w, "masonry", None)
            d = ec6.wall(w.t, w.height, net, top, top + own / 2.0, top + own, floors, w.one_side, shear,
                         w.base_g / net, ec6.with_masonry(settings, masonry), own=bool(masonry))
        else:
            d = ec2.wall(w.t, w.height, net, top, top + own / 2.0, top + own, floors, w.one_side, shear,
                         w.base_g / net, fck, fyk)
            info = _wall_bars_info(model, w.guid, footings)
        out.append(ElementDesign(w.guid, "wall", d, float(w.length), info))
    return out


def _combined(model, analysis, f, nodes, fck, fyk, settings):
    """(0.250) A combined footing's design (ec2.combined_footing): each of its columns' reaction where it stands
    along it, its size along and across; None without its two reactions."""
    x = np.asarray(f.x_dir, dtype=float)
    x = x / np.linalg.norm(x)
    columns = []
    for node in nodes:
        if node not in analysis.reactions:
            continue
        uls = analysis.reactions[node]
        serv = analysis.service.get(node, tuple(v / 1.4 for v in uls))
        p = model.nodes[node]
        u = float((p[0] - f.centre[0]) * x[0] + (p[1] - f.centre[1]) * x[1])
        col = next((m for m in model.members if m.kind == "column" and m.n1 == node), None)
        cx, cy = (float(col.size[0]), float(col.size[1])) if col is not None else (0.30, 0.30)
        columns.append((u, cx, cy, uls[2], serv[2]))
    if len(columns) != 2:
        return None
    return ec2.combined_footing(f.size[0], f.size[1], f.depth, sorted(columns), fck, fyk, settings.soil_kpa)


def _node_near(model, xy, z, tol_z=0.30):
    best, dist = None, NEAR
    for k, p in enumerate(model.nodes):
        if abs(p[2] - z) > tol_z:
            continue
        dd = math.hypot(p[0] - xy[0], p[1] - xy[1])
        if dd < dist:
            best, dist = k, dd
    return best


def _support_half(model, node, beam_guid):
    """Half the width of what holds a beam's end at this node: a column's smaller side, else another beam's width."""
    cols = [m for m in model.members if m.kind == "column" and node in (m.n1, m.n2)]
    if cols:
        return min(min(m.size) for m in cols) / 2.0
    beams = [m for m in model.members if m.kind == "beam" and m.guid != beam_guid and node in (m.n1, m.n2)]
    return min(m.size[0] for m in beams) / 2.0 if beams else 0.0


_STATUS_RANK = {ec2.OK: 0, ec2.WARN: 1, ec2.FAIL: 2}


def unify_typical(designs, equals):
    """(0.231) The members on typical floors with the reinforcement of the most stressed of their equals (equals:
    {GlobalId: their key}, model.bim's) — one drawing for the floors alike, as built: each gets a copy of its design
    (its worst status, its largest use) and a note of it; their own layout (how far into the supports, the main
    direction) stays theirs, alike anyway."""
    import copy
    groups = {}
    for e in designs:
        if e.guid in equals:
            groups.setdefault((equals[e.guid], e.kind), []).append(e)
    for members in groups.values():
        if len(members) < 2:
            continue
        worst = max(members, key=lambda e: (_STATUS_RANK[e.design.status], e.design.ratio))
        for e in members:
            if e is not worst:
                e.design = copy.deepcopy(worst.design)
                for key in ("ext", "into", "lap", "supports", "x_dir"):
                    if key in worst.info and key not in e.info:
                        e.info[key] = worst.info[key]
            e.design.add("typical", n=len(members))
    return designs


def _strips(footings, fck, fyk, settings, walls=()):
    """(0.228) [ElementDesign] of the strip footings: their wall's weight on each metre (no analysis needed) — (0.336)
    a load-bearing wall's: all it brings down (model.wall_loads.WallLoad), G and Q."""
    by = {w.guid: w for w in walls or ()}
    out = []
    for f in footings:
        if getattr(f, "kind", "pad") != "strip":
            continue
        w = by.get(getattr(f, "wall", ""))
        if w is not None and w.length > 1e-6:
            g, q = w.base_g / w.length, w.base_q / w.length
            uls, service = act.GAMMA_G * g + act.GAMMA_Q * q, g + q
        elif f.line_load > 0.0:
            uls, service = act.GAMMA_G * f.line_load, f.line_load
        else:
            continue
        d = ec2.strip_footing(f.size[1], f.depth, f.wall_t, fck, fyk, uls, service, settings.soil_kpa)
        out.append(ElementDesign(f.guid, "footing", d, float(f.size[1]), {"strip": True}))
    return out


def _beam_envelope(model, analysis, members, phys):
    """(0.229) A physical beam's moment envelope for ec2.beam: (its length, the points along it from its start — the
    beam drawn, its ends at its supports' faces —, the largest moments there, the least), from its analytical
    pieces in order; None without them."""
    xs, top, low = [], [], []
    offset = 0.0
    for m in members:
        env = getattr(analysis, "envelopes", {}).get(m.id)
        if env is None:
            return None
        length = model.length(m)
        xs += list(offset + np.linspace(0.0, length, len(env[0])))
        top += list(env[0])
        low += list(env[1])
        offset += length
    start, total = 0.0, offset
    if phys is not None:
        first = np.asarray(model.nodes[members[0].n1][:2], dtype=float)
        start = float(np.hypot(*(np.asarray(phys.start, dtype=float)[:2] - first)))
        total = float(np.hypot(*np.subtract(phys.end, phys.start)[:2]))
    return total, np.asarray(xs) - start, top, low


def slab_supports(model, panel, reach=slab_mesh.REACH):
    """(0.224) The beams a slab rests on — at its level, along its edges (their axes within reach) or across it —,
    each clipped to it: [[x1, y1, x2, y2, half its width, the span on its left, on its right]] (m), a span the
    distance square to it (from its middle) to the next support or to the slab's far edge; 0 on a side with no slab
    (an edge beam's outer side)."""
    from shapely.geometry import LineString, Point, Polygon
    poly = Polygon(panel.outline)
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty:
        return []
    grown = poly.buffer(reach)
    segs = []
    for m in model.members:
        if m.kind != "beam":
            continue
        a, b = model.nodes[m.n1], model.nodes[m.n2]
        if abs(a[2] - panel.level) > NEAR_LEVEL or abs(b[2] - panel.level) > NEAR_LEVEL:
            continue
        part = LineString((a[:2], b[:2])).intersection(grown)
        for piece in getattr(part, "geoms", [part]):
            if piece.geom_type == "LineString" and piece.length >= MIN_SUPPORT:
                segs.append((piece, float(m.size[0]) / 2.0))
    out = []
    for k, (piece, half) in enumerate(segs):
        (ax, ay), (bx, by) = piece.coords[0], piece.coords[-1]
        d = np.array((bx - ax, by - ay)) / piece.length
        n = np.array((-d[1], d[0]))
        mid = np.array(((ax + bx) / 2.0, (ay + by) / 2.0))
        spans = []
        for side in (1.0, -1.0):
            ray = LineString((tuple(mid), tuple(mid + side * n * 1000.0)))
            inside = ray.intersection(poly)
            near = [g for g in getattr(inside, "geoms", [inside]) if g.geom_type == "LineString"
                    and Point(tuple(mid)).distance(Point(g.coords[0])) <= reach + 1e-6]
            if not near:
                spans.append(0.0)
                continue
            far = max(float(np.hypot(*(np.asarray(c) - mid))) for c in near[0].coords)
            for j, (other, _half) in enumerate(segs):
                hit = ray.intersection(other) if j != k else None
                if hit is not None and hit.geom_type == "Point":
                    dist = float(np.hypot(hit.x - mid[0], hit.y - mid[1]))
                    if dist > 0.05:
                        far = min(far, dist)
            spans.append(far)
        out.append([float(ax), float(ay), float(bx), float(by), half, spans[0], spans[1]])
    return out


def design_structure(model, analysis, loads, settings, beams=(), footings=()):
    """[ElementDesign] of the structure: its analytical model (core.structural), analysis
    (model.structure_analysis.Analysis), loads (model.structure_loads.BuildingActions); `beams` and `footings` the
    physical ones (core.structural.Beam, Footing: their ends, their sizes)."""
    fck, fyk = act.CONCRETE[settings.concrete], act.STEEL[settings.steel]
    out = []
    if analysis is None or analysis.error:
        return _strips(footings, fck, fyk, settings)       # (0.230: a strip needs only its wall)
    by_guid = {}
    for o in analysis.members:
        by_guid.setdefault((o.kind, o.guid), []).append(o)
    pieces = {}
    for m in model.members:
        pieces.setdefault(m.guid, []).append(m)
    physical = {b.guid: b for b in beams}
    # beams: the envelope over their pieces
    for (kind, guid), outs in by_guid.items():
        if kind != "beam":
            continue
        m0 = pieces[guid][0]
        b, h = float(m0.size[0]), float(m0.size[1])
        span = max(o.length for o in outs)
        d = ec2.beam(b, h, span, fck, fyk, max(o.m_pos for o in outs), min(o.m_neg for o in outs),
                     max(o.v for o in outs), max(o.deflection for o in outs),
                     envelope=_beam_envelope(model, analysis, pieces[guid], physical.get(guid)))
        ext = [0.0, 0.0]
        phys = physical.get(guid)
        if phys is not None:
            ends = [model.nodes[pieces[guid][0].n1], model.nodes[pieces[guid][-1].n2]]
            for k, (p, node_xyz) in enumerate(zip((phys.start, phys.end), ends)):
                node = pieces[guid][0].n1 if k == 0 else pieces[guid][-1].n2
                half = _support_half(model, node, guid)
                if half > 0.0:
                    past = math.hypot(node_xyz[0] - p[0], node_xyz[1] - p[1])
                    ext[k] = max(past + half - ec2.COVER, 0.0)
        out.append(ElementDesign(guid, "beam", d, span, {"ext": ext}))
    # columns: the greatest compression and moment over their pieces
    footing_at = {}
    for f in footings:
        kind = getattr(f, "kind", "pad")
        if kind == "combined":                           # (0.250) under each of its columns
            for spot in f.columns:
                node = _node_near(model, spot, f.top)
                if node is not None:
                    footing_at[node] = f
            continue
        node = _node_near(model, f.centre, f.top) if kind != "strip" else None
        if node is not None:
            footing_at[node] = f
    for (kind, guid), outs in by_guid.items():
        if kind != "column":
            continue
        ms = pieces[guid]
        b, h = float(ms[0].size[0]), float(ms[0].size[1])
        shape, web = getattr(ms[0], "shape", "rect"), float(getattr(ms[0], "web", 0.0))    # (0.227)
        height = max(o.length for o in outs)
        d = ec2.column(b, h, height, fck, fyk, max(-o.n_min for o in outs), max(o.m_column for o in outs),
                       shape=shape, web=web)
        bottom, top = ms[0].n1, ms[-1].n2
        foot = footing_at.get(bottom)
        into = max(foot.depth - FOOTING_COVER_DOWN, 0.0) if foot is not None else 0.0
        above = any(m.kind == "column" and m.n1 == top and m.guid != guid for m in model.members)
        info = {"into": into, "lap": above}
        if shape != "rect":
            info.update(shape=shape, web=web)
        out.append(ElementDesign(guid, "column", d, height, info))
    # footings: the reaction of the column on each — (0.250) of its two on a combined one
    combined = {}
    for node, f in footing_at.items():
        if getattr(f, "kind", "pad") == "combined":
            combined.setdefault(f.guid, (f, []))[1].append(node)
    for f, nodes in combined.values():
        d = _combined(model, analysis, f, nodes, fck, fyk, settings)
        if d is not None:
            out.append(ElementDesign(f.guid, "footing", d, float(f.size[0]), {}))
    for node, f in footing_at.items():
        if node not in analysis.reactions or getattr(f, "kind", "pad") == "combined":
            continue
        uls = analysis.reactions[node]
        serv = analysis.service.get(node, tuple(v / 1.4 for v in uls))
        col = next((m for m in model.members if m.kind == "column" and m.n1 == node), None)
        cx, cy = (float(col.size[0]), float(col.size[1])) if col is not None else (0.30, 0.30)
        if getattr(f, "kind", "pad") == "cap":           # (0.228) on its piles: struts and ties
            d = ec2.pile_cap(list(f.piles), f.pile_d, f.size[0], f.size[1], f.depth, cx, cy, fck, fyk, uls[2],
                             serv[2])
            out.append(ElementDesign(f.guid, "footing", d, float(f.size[0]), {"cap": True}))
            continue
        d = ec2.footing(f.size[0], f.size[1], f.depth, cx, cy, fck, fyk, uls[2], serv[2], abs(serv[4]),
                        abs(serv[3]), settings.soil_kpa)
        out.append(ElementDesign(f.guid, "footing", d, float(f.size[0]), {}))
    out += _strips(footings, fck, fyk, settings, getattr(analysis, "walls", ()))     # (0.228; 0.336: their walls)
    out += _walls(analysis, settings, model, footings)                               # (0.337; 0.342: concrete)
    # slabs: their loads, both ways — (0.223) analysed as shells: their moments
    shells = {o.guid: o for o in getattr(analysis, "panels", [])}
    for p in model.panels:
        if p.thickness <= 0 or p.guid not in loads.panel_g:
            continue
        x_dir, lx, ly = rb.slab_axes(p.outline)
        shell = shells.get(p.guid)
        d = ec2.slab(lx, ly, p.thickness, fck, fyk, loads.panel_g[p.guid], loads.panel_q.get(p.guid, 0.0),
                     moments=(shell.m_x, shell.m_y) if shell is not None else None,
                     top=(shell.m_x_top, shell.m_y_top) if shell is not None else None)
        out.append(ElementDesign(p.guid, "slab", d, min(lx, ly), {"x_dir": list(x_dir),
                                                                  "supports": slab_supports(model, p)}))
    order = {"column": 0, "beam": 1, "slab": 2, "footing": 3, "wall": 4}
    out.sort(key=lambda e: order[e.kind])
    return out


def counts(designs):
    out = {ec2.OK: 0, ec2.WARN: 0, ec2.FAIL: 0}
    for e in designs:
        out[e.design.status] += 1
    return out
