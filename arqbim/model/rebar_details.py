"""(0.237) The typical reinforcement details of a project (Phase 9, step 5), drawn from its bars in the IFC as they
are laid: a beam-column joint — the end of the first reinforced beam on a column, their bars round it (the beam's
bent into the column, the column's going up through it, the links) cut out of the model in a window — and a lap
splice of each diameter of its main bars, l0 = 1,5 lb,rqd with its concrete and steel (core.rebar.lap_length, the
length the model's splices take). Each with its title, its labels (the bar schedule's positions) and dimensions. An
ordinary drawing (model.drawings.Drawing, metres), at 1:20 on a sheet."""

import json

import numpy as np

from ..core import actions as act
from ..core import rebar as rb
from ..i18n import t
from . import design_text as dt
from .rebar_drawings import BAR_PEN, LINK_PEN, TEXT, _dim, _label, _poly, _room_for_texts, _text, sets_of, short_tag

SCALE = 20                      # its usual scale on a sheet (sheets.USUAL_SCALES): its labels' room counted so
WINDOW = (0.25, 1.20, 0.90, 0.35)   # m round a joint: behind the column, along the beam, under it, over it
ROW = 0.08                      # m between two labels' lines (2,5 mm at 1:20 and its gap)
SPLICE_GAP = 1.40               # m from the joint's window to the splices
SPLICE_ROW = 0.45               # m between two splices
SPLICE_RUN = 0.40               # m: each bar past the lap
SPLICE_SIDE = 0.025             # m between the two lapped bars, as drawn
MAIN = ("bottom", "top", "main", "mesh_x", "mesh_y", "top_x", "top_y")
TITLE = 0.20                    # m over the beam's top: each detail's title


def details_drawing(doc, title):
    """The typical details of the project's reinforcement, or None when it has no bars."""
    hosts = {}
    for e in doc.ifc.file.by_type("IfcReinforcingBar"):
        p = doc.ifc._params(e)
        if p.get("Armadura") and p.get("Projeto") and p["Armadura"] not in hosts:
            hosts[p["Armadura"]] = json.loads(p["Projeto"])
    if not hosts:
        return None
    from .drawings import Drawing
    drawing = Drawing(title)
    lines, ann = [], []
    x1 = _joint(doc, hosts, drawing, lines, ann)
    _splices(doc, hosts, drawing, ann, x1 + SPLICE_GAP)
    drawing.lines = np.concatenate(lines) if lines else np.zeros((0, 2, 2))
    drawing.annotations = ann
    _room_for_texts(drawing, SCALE)
    return drawing


def _joint(doc, hosts, drawing, lines, ann):
    """The beam-column joint drawn round (0, 0) — the column's middle, the beam's top —: returns how far right it
    goes (0 when there is none to draw)."""
    from shapely.geometry import LineString, box
    found = _a_joint(doc, hosts)
    if found is None:
        return 0.0
    beam, column, o, x, a, height = found
    z = np.array((0.0, 0.0, 1.0))
    back, along, under, over = WINDOW
    x0, x1, z0, z1 = -a - back, a + along, -height - under, over
    window = box(x0, z0, x1, z1)
    # the concrete: the column under the beam, the beam off its face
    lines.append(np.array((((-a, z0), (-a, 0.0)), ((-a, 0.0), (x1, 0.0)), ((a, z0), (a, -height)),
                           ((a, -height), (x1, -height)))))
    for host, labels in ((beam, "beam"), (column, "column")):
        for k, (row, bars) in enumerate(sets_of(doc, host)):
            pen = LINK_PEN if row["role"] in ("stirrups", "ties") else BAR_PEN
            for bar in bars:
                p = (np.asarray(bar, dtype=float) - o) @ np.column_stack((x, z))
                if len(p) < 2 or np.ptp(p, axis=0).max() < 1e-6:
                    continue
                part = LineString(p).intersection(window)
                for piece in getattr(part, "geoms", [part]):
                    if piece.geom_type == "LineString" and piece.length > 1e-6:
                        ann.append(_poly(np.asarray(piece.coords), pen))
            if labels == "beam" and row["role"] in ("top", "bottom"):        # (at its level, off the window)
                level = float(np.median([((np.asarray(b) - o) @ z).mean() for b in bars]))
                ann.append(_text((x1 + 0.05, level - 0.02), _label(row)))
            elif labels == "beam":
                ann.append(_text((a + 0.10, -height - 0.15), _label(row)))
            else:
                ann.append(_text((x0, z0 - 0.30 - k * ROW), _label(row)))
    # its dimensions: the column across, the anchorage of the beam's top bars down into it
    _dim(drawing, (-a, z0), (a, z0), -0.10)
    leg = _top_leg(doc, beam, o, x, a)
    if leg is not None:
        (lx, ztop), (_lx, zlow) = leg
        _dim(drawing, (lx, ztop), (lx, zlow), (-a - 0.12) - lx)
    ann.append(_text((x0, TITLE), t("rdet.joint", beam=short_tag(doc.get(beam).name),
                                         column=short_tag(doc.get(column).name))))
    return x1 + 1.0                                     # (its labels on the right)


def _a_joint(doc, hosts):
    """(beam, column, origin (3,), the beam's way from the column (3,), the column's half size along it, the beam's
    height) of the first reinforced beam (by name) with a reinforced column under one of its ends — or None."""
    beams = sorted((g for g, i in hosts.items() if i.get("kind") == "beam" and doc.get(g) is not None),
                   key=lambda g: dt.natural(doc.get(g).name))
    columns = [g for g, i in hosts.items() if i.get("kind") == "column" and doc.get(g) is not None]
    for beam in beams:
        start, end, top, _width, height = doc.ifc.beam_params(beam)
        start, end = np.asarray(start, dtype=float)[:2], np.asarray(end, dtype=float)[:2]
        span = float(np.linalg.norm(end - start))
        if span < 1e-6:
            continue
        for g in columns:
            centre, xc, (ha, hb), _base, ctop = doc.ifc.column_box(g)
            if abs(float(ctop) - float(top)) > 0.05:
                continue
            for near, far in ((start, end), (end, start)):
                if np.linalg.norm(np.asarray(centre, dtype=float)[:2] - near) < max(ha, hb):
                    way = (far - near) / span
                    x = np.array((way[0], way[1], 0.0))
                    xc = np.array((xc[0], xc[1], 0.0), dtype=float) / max(float(np.linalg.norm(xc[:2])), 1e-12)
                    yc = np.array((-xc[1], xc[0], 0.0))
                    a = abs(float(x @ xc)) * ha + abs(float(x @ yc)) * hb
                    o = np.array((centre[0], centre[1], float(top)))
                    return beam, g, o, x, a, float(height)
    return None


def _top_leg(doc, beam, o, x, a):
    """The bent leg of the beam's top bars in the column: its two ends (x, z) in the joint's plane, or None."""
    z = np.array((0.0, 0.0, 1.0))
    for row, bars in sets_of(doc, beam):
        if row["role"] != "top":
            continue
        for bar in bars:
            p = (np.asarray(bar, dtype=float) - o) @ np.column_stack((x, z))
            for q0, q1 in zip(p[:-1], p[1:]):
                if abs(q1[0] - q0[0]) < 1e-3 and abs(q1[1] - q0[1]) > 0.05 and abs(q0[0]) < a:
                    hi, lo = (q0, q1) if q0[1] > q1[1] else (q1, q0)
                    return (float(hi[0]), float(hi[1])), (float(lo[0]), float(lo[1]))
    return None


def _splices(doc, hosts, drawing, ann, x0):
    """A lap splice of each diameter of the main bars, one under another from (x0, 0)."""
    info = next(iter(hosts.values()))
    concrete, steel = info.get("concrete", "C25/30"), info.get("steel", "A500")
    fck, fyk = act.CONCRETE.get(concrete), act.STEEL.get(steel)
    if fck is None or fyk is None:
        return
    diameters = sorted({int(r["diameter"]) for r in doc.ifc.rebar_rows() if r["role"] in MAIN})
    if not diameters:
        return
    ann.append(_text((x0, TITLE), t("rdet.splices")))
    for k, d in enumerate(diameters):
        l0 = rb.lap_length(d, fck, fyk)
        zk = -k * SPLICE_ROW - 0.10
        ann.append(_poly(((x0, zk), (x0 + SPLICE_RUN + l0, zk))))
        ann.append(_poly(((x0 + SPLICE_RUN, zk - SPLICE_SIDE), (x0 + 2 * SPLICE_RUN + l0, zk - SPLICE_SIDE))))
        _dim(drawing, (x0 + SPLICE_RUN, zk), (x0 + SPLICE_RUN + l0, zk), 0.08)
        ann.append(_text((x0, zk - SPLICE_SIDE - 0.12), t("rdet.splice", d=d, l=dt.num(l0, 2), c=concrete,
                                                            s=steel), TEXT))
