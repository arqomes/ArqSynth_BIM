"""Fabrication of the patterned finishes (0.173, Phase 10, step 2): their pieces as the cut list gives them — the
slats' and flutes' (one per run between openings, equal ones together), the perforated finishes' panels (boards of
1,22 × 2,44 m cut round the doors and windows) — and the DXF a CNC router cuts from: each perforated panel laid flat,
its outline (and the openings' cuts), its holes, its name; each length of slat once, with how many. (0.174) The
profiles' straight pieces too (skirting boards, cornices…): in the cut list by their long point, in the DXF each
piece once in plan — its back and its front, the mitres at its ends —, with how many. (0.175) The wavy surfaces'
ribs: each one's outline (its back straight, its front the wave), every one of them. In millimetres (the machine's
unit), DXF R12 as model/dxf.py writes it."""

import math
from collections import Counter

from ..i18n import t
from . import dxf

LAYERS = {"CONTORNO": 7, "FUROS": 1, "TEXTOS": 3}
GAP = 100.0                     # mm between two pieces laid out
TEXT = 25.0                     # mm: the pieces' names


def pieces(doc, guids=None):
    """(rows, panels) of the project's patterned finishes (those of `guids`, or all): rows as the cut list's (role,
    material, length, width, thickness, quantity, edges) — slats and flutes, perforated panels —, and panels
    [(name, (w, h) m, [its outline's rings], [(u, v, size) its holes], {hole, grid})] for the CNC (m, from the
    panel's corner; 0.389: each hole its size — a picture —, round or square, the grid straight or at 45°)."""
    from ..core import surfaces
    from ..core import profiles
    chosen = set(guids) if guids is not None else None
    count, panels = Counter(), []
    for e in doc.ifc.file.by_type("IfcCovering"):
        p = doc.ifc._params(e)
        finish = p.get("Acabamento")
        if chosen is not None and e.GlobalId not in chosen and p.get("Parede") not in chosen:
            continue
        if p.get("Elemento") == "profile":              # (0.174) a profile's straight pieces, by their long point
            pp = doc.ifc.profile_params(e.GlobalId)
            material = profiles.spec(pp["profile"])[1]  # (0.245: a project's own too)
            for long, _a0, _a1 in doc.ifc.profile_pieces(e.GlobalId):
                count[(pp["profile"], material, round(long, 3), round(pp["height"], 3), round(pp["width"], 3),
                       0)] += 1
            continue
        if finish not in surfaces.PATTERNS:
            continue
        d = doc.ifc.pattern_params(e.GlobalId)
        th = round(d["thickness"], 3)
        if finish == "perfurado":                       # (0.389: each hole its size and shape)
            for k, (q, centres, sizes) in enumerate(d["panels"]):
                u0, v0, u1, v1 = q.bounds
                w, h = round(u1 - u0, 3), round(v1 - v0, 3)
                count[("perforated", "perforated", max(w, h), min(w, h), th, 4)] += 1
                rings = [[(u - u0, v - v0) for u, v in list(r.coords)[:-1]] for r in [q.exterior, *q.interiors]]
                panels.append(("{} — {} {}".format(e.Name or "", t("fab.panel"), k + 1), (w, h), rings,
                               [(u - u0, v - v0, s) for (u, v), s in zip(centres, sizes)],
                               {"hole": d["hole"], "grid": d["grid"]}))
        elif finish == "ondulado":                      # (0.175) each rib: its length, its crest, its thickness
            for a0, a1, outline in d["ribs"]:
                b0, b1 = outline[0][0], outline[1][0]
                crest = max(w for _b, w in outline)
                count[("rib", "rib", round(b1 - b0, 3), round(crest, 3), round(a1 - a0, 3), 0)] += 1
        else:
            role = "slat" if finish == "ripado" else "flute"
            for u0, v0, u1, v1 in d["strips"]:
                a, b = sorted((round(u1 - u0, 3), round(v1 - v0, 3)), reverse=True)
                count[(role, "slat", a, b, th, 0)] += 1
    rows = [(role, mat, a, b, c, n, edges) for (role, mat, a, b, c, edges), n in count.items()]
    return sorted(rows, key=lambda r: (r[0], -r[2])), panels


def profile_cuts(doc, guids=None):
    """(0.174) [((profile, back length, mitre at its start, at its end — degrees, + an inside corner —, its width),
    how many)] the profiles' straight pieces as the joiner cuts them, equal ones together, the longest first."""
    from ..core import profiles
    chosen = set(guids) if guids is not None else None
    count = Counter()
    for e in doc.ifc.profiles():
        if chosen is not None and e.GlobalId not in chosen:
            continue
        pp = doc.ifc.profile_params(e.GlobalId)
        for pts, closed in doc.ifc.profile_runs(e.GlobalId):
            for long, a0, a1 in profiles.pieces(pts, closed, pp["width"], pp["side"]):
                back = long - max(0.0, -pp["width"] * (math.tan(math.radians(a0)) + math.tan(math.radians(a1))))
                count[(pp["profile"], round(back, 3), round(a0, 1), round(a1, 1), round(pp["width"], 3))] += 1
    return sorted(count.items(), key=lambda kv: (kv[0][0], -kv[0][1]))


def rib_outlines(doc, guids=None):
    """(0.175) [(name, [(x, y)…] m)] every rib of the wavy surfaces, laid flat: x along it from its start, y out of
    the wall — each one its own (the waves turn from one to the next)."""
    chosen = set(guids) if guids is not None else None
    out = []
    for e in doc.ifc.file.by_type("IfcCovering"):
        p = doc.ifc._params(e)
        if p.get("Acabamento") != "ondulado" or (chosen is not None and e.GlobalId not in chosen and
                                                  p.get("Parede") not in chosen):
            continue
        for k, (_a0, _a1, outline) in enumerate(doc.ifc.pattern_params(e.GlobalId)["ribs"]):
            b0 = outline[0][0]
            out.append(("{} — {} {}".format(e.Name or "", t("cut.role.rib").lower(), k + 1),
                        [(b - b0, w) for b, w in outline]))
    return out


def write_dxf(path, doc, guids=None):
    """The CNC's DXF of the patterned finishes (mm): the perforated panels side by side (outline, holes, name),
    then each length of slat once under them, the profiles' pieces (0.174), every rib of the wavy surfaces (0.175).
    Returns how many panels, how many other pieces."""
    rows, panels = pieces(doc, guids)
    w = dxf._Writer()
    x = 0.0
    for name, (pw, ph), rings, holes, shape in panels:
        W, H = pw * 1000.0, ph * 1000.0
        for ring in rings:                                  # (its outline, cut round the doors and windows)
            w.polyline("CONTORNO", [(x + u * 1000.0, v * 1000.0) for u, v in ring], closed=True)
        turned = shape.get("grid") == "diagonal"
        for u, v, size in holes:                            # (0.389) round or square (on a 45° grid: turned)
            cx, cy, r = x + u * 1000.0, v * 1000.0, size * 500.0
            if shape.get("hole") == "quadrado":
                corners = [(r, 0.0), (0.0, r), (-r, 0.0), (0.0, -r)] if turned else \
                    [(r, r), (-r, r), (-r, -r), (r, -r)]
                if turned:                                  # (its corners on the turned grid's axes: √2 out)
                    corners = [(a * math.sqrt(2.0), b * math.sqrt(2.0)) for a, b in corners]
                w.polyline("FUROS", [(cx + a, cy + b) for a, b in corners], closed=True)
            else:
                w.circle("FUROS", (cx, cy), r)
        w.text("TEXTOS", (x, -2 * TEXT), TEXT, name)
        w.text("TEXTOS", (x, -3.5 * TEXT), TEXT, "{:.0f} × {:.0f} mm — {} {}".format(W, H, len(holes), t("fab.holes")))
        x += W + GAP
    y = -10 * TEXT
    lengths = [r for r in rows if r[0] in ("slat", "flute")]
    for role, _mat, a, b, c, n, _e in lengths:
        L, B = a * 1000.0, b * 1000.0
        w.polyline("CONTORNO", [(0.0, y - B), (L, y - B), (L, y), (0.0, y)], closed=True)
        w.text("TEXTOS", (L + GAP, y - B), TEXT, "{} × {} {:.0f} × {:.0f} × {:.0f} mm".format(
            n, t("cut.role." + role), L, B, c * 1000.0))
        y -= B + GAP
    cuts = profile_cuts(doc, guids)                     # (0.174) each profile piece in plan: its back, its front
    for (key, back, a0, a1, width), n in cuts:          # (its width out), its mitres
        L, B = back * 1000.0, width * 1000.0
        d0, d1 = B * math.tan(math.radians(a0)), B * math.tan(math.radians(a1))
        shift = max(0.0, -d0)                           # (its front longer at the start: the back drawn further in)
        w.polyline("CONTORNO", [(shift, y - B), (shift + L, y - B), (shift + L - d1, y), (shift + d0, y)],
                   closed=True)
        long = max(L, L - d0 - d1)
        from ..core.profiles import CUSTOM, is_custom
        name = key[len(CUSTOM):] if is_custom(key) else t("cut.role." + key)     # (0.245: a project's own: its name)
        w.text("TEXTOS", (shift + max(L, L - d1) + GAP, y - B), TEXT, "{} × {} {:.0f} mm — {:.0f}° / {:.0f}°".format(
            n, name, long, abs(a0), abs(a1)))
        y -= B + GAP
    ribs = rib_outlines(doc, guids)                     # (0.175) every rib laid flat, its wavy front up
    for name, outline in ribs:
        B = max(v for _u, v in outline) * 1000.0
        w.polyline("CONTORNO", [(u * 1000.0, y - B + v * 1000.0) for u, v in outline], closed=True)
        w.text("TEXTOS", (max(u for u, _v in outline) * 1000.0 + GAP, y - B), TEXT, name)
        y -= B + GAP
    lengths = lengths + cuts + ribs
    with open(path, "w", encoding="cp1252", errors="replace", newline="\r\n") as f:     # (as model/dxf.py: R12)
        f.write(w.document(LAYERS))
    return len(panels), len(lengths)
