"""(0.501) DSTV NC1 — the file the steel fabricators' saws and drills read, one per piece mark (DSTV-NC, the German
steel construction association's standard, as DetailCraft writes it): the ST block (the piece: order, drawing, phase,
mark, grade, how many, its section and its code, its length and the section's sizes, kg/m, the paint surface per
metre, the cut angles of its web and flanges at each end), BO (its holes: face, x, y, diameter), AK (a plate's
outline) and EN. Lengths in mm, two decimals; angles in degrees. Pure Python."""

CODES = {"IPE": "I", "HEA": "I", "HEB": "I", "HEM": "I", "UPN": "U", "UPE": "U", "L": "L", "LU": "L", "SHS": "M",
         "RHS": "M", "CHS": "RO", "C": "C", "Z": "SO", "OMEGA": "SO", "PLATE": "B"}


def _n(v):
    return "{:.2f}".format(float(v))


def header_lines(order, drawing, phase, mark, grade, quantity, profile, code, length, h, b, tf, tw, r, kg_m, paint_m,
                 cuts=(0.0, 0.0, 0.0, 0.0), texts=()):
    """The ST block's lines (each indented two spaces, as the standard writes them)."""
    lines = ["ST", "** ArqSynth BIM"]
    values = [order, drawing, phase, mark, grade, int(quantity), profile, code, _n(length), _n(h), _n(b), _n(tf),
              _n(tw), _n(r), _n(kg_m), "{:.3f}".format(float(paint_m))] + [_n(a) for a in cuts]
    values += list(texts)[:4]
    lines += ["  {}".format(v) for v in values]
    return lines


MARK_HEIGHT = 10.0             # mm: (0.511) the marking's letters


def nc1(header, holes=(), contour=None, marking=None):
    """A whole NC1 file's text: header — header_lines' arguments as a dict —, holes [(face, x, y, d)], contour (a plate's
    outline [(x, y)] on face v), closed; (0.511) marking: (face, x, y, text) — the SI block, the piece's mark the
    machine punches or scribes on it (its letters MARK_HEIGHT high, along the piece)."""
    lines = header_lines(**header)
    if contour:
        lines.append("AK")
        pts = list(contour)
        if pts[0] != pts[-1]:
            pts.append(pts[0])
        lines += ["  v  {:>10} {:>10} {:>8}".format(_n(x), _n(y), _n(0.0)) for x, y in pts]
    if holes:
        lines.append("BO")
        lines += ["  {}  {:>10} {:>10} {:>8}".format(face, _n(x), _n(y), _n(d)) for face, x, y, d in holes]
    if marking and marking[3]:
        face, x, y, text = marking
        lines.append("SI")
        lines.append("  {}  {:>10}u{:>10}  0.00r{:g}{}".format(face, _n(x), _n(y), MARK_HEIGHT, text))
    lines.append("EN")
    return "\n".join(lines) + "\n"


def parse(text):
    """An NC1 read back (DetailCraft reads them too): {"ST": [values], "BO": [(face, x, y, d)], "AK": [(x, y)]}."""
    out, block = {"ST": [], "BO": [], "AK": [], "SI": []}, None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line in ("ST", "BO", "AK", "EN", "IK", "SI", "KO", "PU", "KA"):
            block = line
            continue
        if block == "ST":
            out["ST"].append(line)
        elif block == "BO":
            face, x, y, d = line.split()[:4]
            out["BO"].append((face, float(x), float(y), float(d)))
        elif block == "AK":
            parts = line.split()
            out["AK"].append((float(parts[1]), float(parts[2])))
        elif block == "SI":                                    # (0.511) the marking: its text after «r<height>»
            import re
            found = re.match(r"\s*\S+\s+\S+u\s*\S+\s+\S+r([\d.]+)(.*)$", line)
            out["SI"].append(found.group(2).strip() if found else line)
    return out
