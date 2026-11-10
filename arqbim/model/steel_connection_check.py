"""(0.520) The steel connections checked by NP EN 1993-1-8 (core/ec3_joints) with the forces the steel analysis gives
at their pieces' ends (model/steel_analysis) — the plan's step 8, for pre-design:

- a fin plate: the beam's end shear and axial force on its column of bolts, with the moment of the shear's
  eccentricity (the bolts' distance from the support); bearing on the beam's web or the plate; its welds;
- a gusset: the brace's tension shared by its bolts; bearing on the angle's leg or the gusset; its welds;
- a purlin's cleat: the purlin's reaction on that rafter (the force its link carries) on its bolts; bearing on the
  purlin's thin web; its welds;
- an end plate, a bolted knee: the shear on all the bolts, the moment's tension on the outer row (the moment over the
  lever arm, shared by its two bolts), and both at once; their welds, the flanges' carrying the moment;
- a base plate: the column's foot — its uplift and its moments in tension on the anchors (each moment over its lever
  arm, shared by a side's two anchors), its shear shared by all; the weld round the column.

The bolts and the anchors as class 8.8. Each connection the worst of its combinations' forces taken together (on the
safe side). Units: kN, m (the sizes in mm)."""

import json
import math

import numpy as np

from ..core import ec3_joints as joints
from ..core import steel
from ..ifc.steel_connections import hole


def _end_forces(ctx, piece, end):
    """The greatest (tension kN, compression kN, shear kN, moment kN·m) at a piece's end over the ULS combinations —
    its first bar's start or its last bar's end, local."""
    bars = ctx["by_piece"].get(piece) or []
    if not bars:
        return 0.0, 0.0, 0.0, 0.0
    bar = bars[0] if end == 0 else bars[-1]
    side = 0 if end == 0 else 6
    frame, results = ctx["frame"], ctx["results"]
    tension = compression = shear = moment = 0.0
    for _name, factors in ctx["uls"]:
        f = frame.combined_forces(results, factors, bar)
        n = -f[side] if side == 0 else f[side]                # (tension +)
        tension, compression = max(tension, n), max(compression, -n)
        shear = max(shear, math.hypot(f[side + 1], f[side + 2]))
        moment = max(moment, math.hypot(f[side + 4], f[side + 5]))
    return tension, compression, shear, moment


def _link_force(ctx, a, b):
    """The greatest force (kN) the link between two pieces carries (a purlin's reaction on a rafter), or None."""
    frame, results = ctx["frame"], ctx["results"]
    out = None
    for m in frame.members:
        pair = getattr(frame, "link_pieces", {}).get(m.id)
        if pair is None or set(pair) != {a, b}:
            continue
        for _name, factors in ctx["uls"]:
            f = frame.combined_forces(results, factors, m)
            out = max(out or 0.0, float(np.linalg.norm(f[:3])))
    return out


def _weld_of(doc, assembly):
    """(throat mm, length mm) of a connection's welds, from their Pset_FastenerWeld."""
    import ifcopenshell.util.element as ue
    a = length = 0.0
    for part in doc.ifc.connection_parts(assembly):
        if part.is_a("IfcFastener"):
            p = ue.get_psets(part).get("Pset_FastenerWeld", {})
            s = doc.ifc.unit_scale * 1000.0
            a = max(a, float(p.get("a") or 0.0) * s)
            length += float(p.get("l") or 0.0) * s
    return a, length


def check(doc, analysis):
    """The connections checked: [{"guid" (the assembly's), "kind", "name", "bolts" («4 × M20»), "shear", "tension"
    (kN a bolt), "weld" (its use), "utilisation", "governing", "ok"}] — the most used first."""
    from ..core import steel as _steel
    ctx = analysis.context
    if not ctx:
        return []
    index = ctx["index"]
    out = []
    for assembly in doc.ifc.file.by_type("IfcElementAssembly"):
        if doc.ifc.kind_of(assembly.GlobalId) != "steel_connection":
            continue
        kind, members, params = doc.ifc.connection_params(assembly.GlobalId)
        if any(m not in index for m in members):
            continue
        secs = [_steel.get(doc.ifc.steel_section(m) or "") for m in members]
        grade = ctx["pieces"][index[members[0]]].grade or "S275"
        d = float(params.get("d", 20.0))
        d0 = hole(d)
        a, weld_length = _weld_of(doc, assembly)
        found = _connection(kind, members, params, secs, ctx, index, d, d0, grade, doc)
        if found is None:
            continue
        shear, tension, bolts, t_min, e1, weld_force, weld_util_extra = found
        bolt = joints.check_bolts(d, d0, t_min, grade, e1, shear, tension)
        weld = joints.check_weld(weld_force, weld_length, a, grade)
        ratios = dict(bolt["ratios"])
        ratios["Fw"] = max(weld["util"], weld_util_extra(a) if weld_util_extra else 0.0)
        name, util = max(ratios.items(), key=lambda kv: kv[1])
        out.append({"guid": assembly.GlobalId, "kind": kind, "name": assembly.Name or "",
                    "bolts": "{} × M{:g}".format(bolts, d), "shear": shear, "tension": tension,
                    "weld": ratios["Fw"], "utilisation": util, "governing": name, "ok": util <= 1.0})
    out.sort(key=lambda r: -r["utilisation"])
    return out


def _connection(kind, members, params, secs, ctx, index, d, d0, grade, doc):
    """(shear kN a bolt, tension kN a bolt, bolts, the thinner part t mm, e1 mm, the welds' force kN, an extra weld
    check (a ↦ use) or None) of a connection — None when it is not one checked here."""
    if kind == "fin_plate":
        beam = index[members[0]]
        tension, compression, v, _m = _end_forces(ctx, beam, int(params["end"]))
        n_ax = max(tension, compression)
        rows, p, eh = int(params["rows"]), float(params["p"]), float(params["eh"])
        ys = [(j - (rows - 1) / 2.0) * p for j in range(rows)]
        sum_y2 = sum(y * y for y in ys) or 1.0
        moment = v * eh                                           # kN·mm (the eccentricity)
        across = moment * max(abs(y) for y in ys) / sum_y2 if rows > 1 else 0.0
        shear = math.hypot(v / rows, n_ax / rows + across)
        t_min = min(secs[0].tw, float(params["tp"]))
        return shear, 0.0, rows, t_min, float(params["e"]), math.hypot(v, n_ax), None
    if kind == "gusset":
        brace = index[members[0]]
        tension, _c, _v, _m = _end_forces(ctx, brace, int(params["end"]))
        rows = int(params["rows"])
        t_min = min(secs[0].tw, float(params["tp"]))
        return tension / rows, 0.0, rows, t_min, float(params["e"]), tension, None
    if kind == "purlin_cleat":
        force = _link_force(ctx, index[members[0]], index[members[1]]) or 0.0
        rows, p = int(params["rows"]), float(params["p"])
        h = float(params["H"]) or max(60.0, round(0.7 * secs[0].h / 10.0) * 10.0)
        e1 = (h - (rows - 1) * p) / 2.0
        t_min = min(secs[0].tw, float(params["tp"]))
        return force / rows, 0.0, rows, t_min, e1, force, None
    if kind in ("end_plate", "knee_plate"):
        if kind == "end_plate":
            piece, end = index[members[0]], int(params["end"])
            sec = secs[0]
            t_min = min(float(params["tp"]), secs[1].tf)
        else:
            found = doc.ifc.mitre_plane(members[0], members[1])
            if found is None:
                return None
            piece, end, sec = index[members[0]], found[0], secs[0]
            t_min = float(params["tp"])
        tension, compression, v, m = _end_forces(ctx, piece, end)
        rows = int(params["rows"])
        bolts = 2 * rows
        lever = max(sec.h - sec.tf, 50.0) / 1000.0              # m
        pull = m / lever / 2.0 + max(tension, 0.0) / bolts      # (the outer row's two bolts)
        flange = m / lever                                      # kN: the moment's flange force on its welds

        def flange_weld(a, b=sec.b):
            return flange / (joints.weld_rd(a, grade) * 2.0 * b) if a > 0 else 0.0
        return v / bolts, pull, bolts, t_min, float(params["e"]), max(v, compression, tension), flange_weld
    if kind == "base_plate":
        column = index[members[0]]
        pieces = ctx["pieces"]
        p = pieces[column]
        end = 0 if p.a[2] <= p.b[2] else 1
        tension, compression, v, m = _end_forces(ctx, column, end)
        n = int(params["n"])
        sec = secs[0]
        b, h = steel.size(sec)
        from ..ifc.steel_connections import base_plate_layout
        a_plate, b_plate, _spots, _w = base_plate_layout(params, b, h)
        lever = max(min(a_plate, b_plate) - 2.0 * float(params["e"]), 50.0) / 1000.0
        pull = max(tension, 0.0) / n + m / lever / 2.0
        flange = m / max(h - sec.tf, 50.0) * 1000.0

        def foot_weld(a, b=sec.b):
            return flange / (joints.weld_rd(a, grade) * 2.0 * b) if a > 0 else 0.0
        return v / n, pull, n, float(params["tp"]), float(params["e"]), max(compression, tension, v), foot_weld
    return None


def summary(rows):
    """{"count", "failing"} of the connections checked."""
    return {"count": len(rows), "failing": sum(1 for r in rows if not r["ok"])}
