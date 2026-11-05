"""Reading a DXF (0.156; ASCII, any version) for what a survey drawing has: the points with a height, by layer —
POINT, the ends of a LINE, a LWPOLYLINE's corners at its elevation (contour lines), a 3D POLYLINE's vertices, a
3DFACE's corners, an INSERT's point (a survey point as a block), a CIRCLE's centre, and a TEXT / MTEXT that is only
a number with decimals (a spot height written on the plan: the number is the height, the text's point where it is;
a whole number is a point's number, not read).

Pure Python: pairs of lines (group code, value) — no library. Entities inside blocks are not read (a block's
insertion is). Binary DXF is not read."""

import re

HEIGHT = re.compile(r"^\s*[+-]?\d+[.,]\d+\s*$")          # (a spot height has decimals; a point's number has none)


def _pairs(text):
    lines = text.splitlines()
    for k in range(0, len(lines) - 1, 2):
        code = lines[k].strip()
        if not code.lstrip("-").isdigit():
            continue
        yield int(code), lines[k + 1].rstrip("\r\n")


def _entities(text):
    """The ENTITIES section's entities: [(type, [(code, value)…])]."""
    out, current, in_entities, section_next = [], None, False, False
    for code, value in _pairs(text):
        v = value.strip()
        if code == 0:
            if current is not None:
                out.append(current)
                current = None
            if v == "SECTION":
                section_next = True
                continue
            if v == "ENDSEC":
                in_entities = False
                continue
            if in_entities and v != "EOF":
                current = (v, [])
            continue
        if section_next and code == 2:
            in_entities = v == "ENTITIES"
            section_next = False
            continue
        if current is not None:
            current[1].append((code, v))
    if current is not None:
        out.append(current)
    return out


def _float(value):
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def _get(pairs, code, default=None):
    for c, v in pairs:
        if c == code:
            f = _float(v)
            return f if f is not None else default
    return default


def _text(pairs, code=1, default=""):
    return next((v for c, v in pairs if c == code), default)


def read_points(text):
    """{layer: [(x, y, z)…]} of a DXF's text."""
    out = {}
    polyline = None                                         # (layer, its elevation, its vertices, 3D?)

    def add(layer, x, y, z):
        if x is not None and y is not None and z is not None:
            out.setdefault(layer or "0", []).append((x, y, z))

    for kind, pairs in _entities(text):
        layer = _text(pairs, 8, "0")
        if polyline is not None and kind not in ("VERTEX",):
            polyline = None                                 # (its SEQEND, or anything else: it ended)
        if kind == "POINT":
            add(layer, _get(pairs, 10), _get(pairs, 20), _get(pairs, 30, 0.0))
        elif kind == "LINE":
            add(layer, _get(pairs, 10), _get(pairs, 20), _get(pairs, 30, 0.0))
            add(layer, _get(pairs, 11), _get(pairs, 21), _get(pairs, 31, 0.0))
        elif kind == "LWPOLYLINE":
            z = _get(pairs, 38, 0.0)
            xs = [_float(v) for c, v in pairs if c == 10]
            ys = [_float(v) for c, v in pairs if c == 20]
            for x, y in zip(xs, ys):
                add(layer, x, y, z)
        elif kind == "POLYLINE":
            flags = int(_get(pairs, 70, 0) or 0)
            polyline = (layer, _get(pairs, 30, 0.0), bool(flags & 8))
        elif kind == "VERTEX" and polyline is not None:
            p_layer, elevation, three_d = polyline
            z = _get(pairs, 30, 0.0) if three_d else elevation
            add(p_layer, _get(pairs, 10), _get(pairs, 20), z)
        elif kind == "3DFACE":
            for k in range(4):
                add(layer, _get(pairs, 10 + k), _get(pairs, 20 + k), _get(pairs, 30 + k, 0.0))
        elif kind in ("INSERT", "CIRCLE"):
            add(layer, _get(pairs, 10), _get(pairs, 20), _get(pairs, 30, 0.0))
        elif kind in ("TEXT", "MTEXT"):
            words = _text(pairs, 1).strip()
            if kind == "MTEXT":
                words = re.sub(r"\\[A-Za-z][^;]*;|[{}]", "", words).strip()     # (its formatting codes)
            if HEIGHT.match(words):
                add(layer, _get(pairs, 10), _get(pairs, 20), _float(words.strip()))
    for layer in list(out):                                 # (the same point twice in a layer: once)
        out[layer] = list(dict.fromkeys((round(x, 6), round(y, 6), round(z, 6)) for x, y, z in out[layer]))
    return out


def read_file(path):
    """{layer: [(x, y, z)…]} of a DXF file (UTF-8, else the old Windows encoding) — (0.286) or a DWG's (its DXF)."""
    if path.lower().endswith(".dwg"):
        from .dwg import to_dxf
        path = to_dxf(path)
    with open(path, "rb") as f:
        data = f.read()
    if data[:22].startswith(b"AutoCAD Binary DXF"):
        raise ValueError("binary DXF")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("cp1252", errors="replace")
    return read_points(text)


def with_heights(layers):
    """The layers whose points have heights (a drawing in 2D has them all at 0)."""
    return [name for name, pts in layers.items() if any(abs(z) > 1e-9 for _x, _y, z in pts)]
