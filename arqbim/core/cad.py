"""A 2D CAD drawing read from a DXF (0.158, Phase 8, step 1): its linework by layer — lines, polylines (their arcs,
from the bulges, as short segments), arcs, circles, the blocks inserted (exploded where they are: moved, turned,
scaled), the texts — and its units ($INSUNITS: mm, cm, m; when not said, guessed from its size). Pure Python and
numpy, built on dxf_read's pairs (no library). What the program does with it: a drawing laid under a plan to draw
over (model/cad_links.py), then walls, openings and furniture made from it."""

import math
from dataclasses import dataclass, field

import numpy as np

from .dxf_read import _float, _pairs

ARC_DEG = 7.5                   # an arc as segments this many degrees each
UNITS = {1: 0.0254, 2: 0.3048, 4: 0.001, 5: 0.01, 6: 1.0, 14: 0.1}     # $INSUNITS -> metres (inches, feet, mm…)


@dataclass
class Entity:
    kind: str                   # "line" | "polyline" | "arc" | "circle" | "text" | "insert"
    layer: str
    points: list = field(default_factory=list)     # (x, y) — a polyline's corners, a text's / an insert's point
    closed: bool = False
    radius: float = 0.0
    angles: tuple = (0.0, 360.0)                    # an arc's start and end (degrees, counter-clockwise)
    bulges: list = field(default_factory=list)      # a polyline's, one per corner
    text: str = ""
    block: str = ""
    rotation: float = 0.0
    scale: tuple = (1.0, 1.0)


@dataclass
class Drawing:
    entities: list
    blocks: dict                # name -> (base point (x, y), [Entity])
    units: float                # metres in one drawing unit
    units_given: bool = True


def _sections(text):
    """{section name: [(type, [(code, value)…])]} — and the BLOCKS section's entities keyed by block, with their
    BLOCK / ENDBLK markers kept in order."""
    out, name, current, section_next = {}, None, None, False
    for code, value in _pairs(text):
        v = value.strip()
        if code == 0:
            if current is not None and name is not None:
                out.setdefault(name, []).append(current)
            current = None
            if v == "SECTION":
                section_next = True
            elif v == "ENDSEC":
                name = None
            elif name is not None and v != "EOF":
                current = (v, [])
            continue
        if section_next and code == 2:
            name, section_next = v, False
            out.setdefault(name, [])
            continue
        if current is not None:
            current[1].append((code, v))
        elif name == "HEADER":
            out.setdefault("HEADER", []).append(("$", [(code, v)]))
    if current is not None and name is not None:
        out.setdefault(name, []).append(current)
    return out


def _val(pairs, code, default=None):
    for c, v in pairs:
        if c == code:
            f = _float(v)
            return f if f is not None else default
    return default


def _str(pairs, code, default=""):
    return next((v for c, v in pairs if c == code), default)


def _entity(kind, pairs, polyline=None):
    layer = _str(pairs, 8, "0")
    if kind == "LINE":
        return Entity("line", layer, [(_val(pairs, 10, 0.0), _val(pairs, 20, 0.0)),
                                      (_val(pairs, 11, 0.0), _val(pairs, 21, 0.0))])
    if kind == "LWPOLYLINE":
        pts, bulges = [], []
        for c, v in pairs:
            if c == 10:
                pts.append([_float(v) or 0.0, 0.0])
                bulges.append(0.0)
            elif c == 20 and pts:
                pts[-1][1] = _float(v) or 0.0
            elif c == 42 and bulges:
                bulges[-1] = _float(v) or 0.0
        flags = int(_val(pairs, 70, 0) or 0)
        return Entity("polyline", layer, [tuple(p) for p in pts], bool(flags & 1), bulges=bulges)
    if kind == "ARC":
        return Entity("arc", layer, [(_val(pairs, 10, 0.0), _val(pairs, 20, 0.0))], radius=_val(pairs, 40, 0.0),
                      angles=(_val(pairs, 50, 0.0), _val(pairs, 51, 360.0)))
    if kind == "CIRCLE":
        return Entity("circle", layer, [(_val(pairs, 10, 0.0), _val(pairs, 20, 0.0))], radius=_val(pairs, 40, 0.0))
    if kind in ("TEXT", "MTEXT"):
        import re
        words = _str(pairs, 1)
        if kind == "MTEXT":
            words = re.sub(r"\\P", " ", words)
            words = re.sub(r"\\[A-Za-z][^;]*;|[{}]", "", words)
        return Entity("text", layer, [(_val(pairs, 10, 0.0), _val(pairs, 20, 0.0))], text=words.strip(),
                      radius=_val(pairs, 40, 0.0))
    if kind == "INSERT":
        return Entity("insert", layer, [(_val(pairs, 10, 0.0), _val(pairs, 20, 0.0))], block=_str(pairs, 2),
                      rotation=_val(pairs, 50, 0.0), scale=(_val(pairs, 41, 1.0), _val(pairs, 42, 1.0)))
    return None


def _entities_of(items):
    """Entities from (type, pairs) items — a POLYLINE's VERTEXes gathered into it."""
    out, poly = [], None
    for kind, pairs in items:
        if kind == "VERTEX" and poly is not None:
            poly.points.append((_val(pairs, 10, 0.0), _val(pairs, 20, 0.0)))
            poly.bulges.append(_val(pairs, 42, 0.0) or 0.0)
            continue
        if kind == "SEQEND":
            poly = None
            continue
        poly = None
        if kind == "POLYLINE":
            flags = int(_val(pairs, 70, 0) or 0)
            poly = Entity("polyline", _str(pairs, 8, "0"), [], bool(flags & 1))
            out.append(poly)
            continue
        e = _entity(kind, pairs)
        if e is not None:
            out.append(e)
    return out


def read(text):
    """The Drawing of a DXF's text."""
    sections = _sections(text)
    header = [p for _k, ps in sections.get("HEADER", []) for p in ps]
    units, given = None, False
    for k, (code, value) in enumerate(header):
        if code == 9 and value == "$INSUNITS" and k + 1 < len(header):
            units = UNITS.get(int(_float(header[k + 1][1]) or 0))
            given = units is not None
    blocks, current, items = {}, None, []
    for kind, pairs in sections.get("BLOCKS", []):
        if kind == "BLOCK":
            current = (_str(pairs, 2), (_val(pairs, 10, 0.0), _val(pairs, 20, 0.0)))
            items = []
        elif kind == "ENDBLK":
            if current is not None:
                blocks[current[0]] = (current[1], _entities_of(items))
            current = None
        elif current is not None:
            items.append((kind, pairs))
    drawing = Drawing(_entities_of(sections.get("ENTITIES", [])), blocks, units or 1.0, given)
    if not given:
        drawing.units = guess_units(drawing)
    return drawing


def read_file(path):
    if path.lower().endswith(".dwg"):                      # (0.286) a DWG: through its DXF (core/dwg)
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
    return read(text)


def guess_units(drawing):
    """A drawing that does not say its units: a building's plan 3 to 300 m across — in millimetres when it is
    thousands of units across, centimetres when hundreds, else metres."""
    segs = segments(Drawing(drawing.entities, drawing.blocks, 1.0))
    every = np.concatenate(list(segs.values())) if segs else np.zeros((0, 2, 2))
    if not len(every):
        return 1.0
    pts = every.reshape(-1, 2)
    span = float((pts.max(axis=0) - pts.min(axis=0)).max())
    return 0.001 if span > 2000 else (0.01 if span > 400 else 1.0)


def _arc_points(c, r, a0, a1):
    a0, a1 = math.radians(a0), math.radians(a1)
    while a1 <= a0:
        a1 += 2 * math.pi
    n = max(int(math.ceil(math.degrees(a1 - a0) / ARC_DEG)), 1)
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * k / n), c[1] + r * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(n + 1)]


def _bulge_points(p, q, bulge):
    """The arc from p to q of a polyline's bulge (tan of a quarter of its angle; + counter-clockwise)."""
    if abs(bulge) < 1e-9:
        return [p, q]
    theta = 4 * math.atan(bulge)
    chord = math.hypot(q[0] - p[0], q[1] - p[1])
    if chord < 1e-12:
        return [p, q]
    r = chord / (2 * math.sin(theta / 2))                  # (signed: < 0 clockwise)
    d = r * math.cos(theta / 2)                             # the centre from the chord's middle, to its left
    nx, ny = -(q[1] - p[1]) / chord, (q[0] - p[0]) / chord
    c = ((p[0] + q[0]) / 2 + nx * d, (p[1] + q[1]) / 2 + ny * d)
    a0 = math.atan2(p[1] - c[1], p[0] - c[0])
    radius = math.hypot(p[0] - c[0], p[1] - c[1])
    n = max(int(math.ceil(abs(math.degrees(theta)) / ARC_DEG)), 1)
    return [(c[0] + radius * math.cos(a0 + theta * k / n), c[1] + radius * math.sin(a0 + theta * k / n))
            for k in range(n)] + [q]


def _transform(points, base, at, rotation, scale):
    a = math.radians(rotation)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for x, y in points:
        x, y = (x - base[0]) * scale[0], (y - base[1]) * scale[1]
        out.append((at[0] + x * ca - y * sa, at[1] + x * sa + y * ca))
    return out


def entity_polylines(e, blocks, depth=0, straight=False):
    """An entity as polylines (lists of (x, y), drawing units) with their layers: [(layer, points)] — a block's
    entities moved where it is inserted (inside it, layer "0" takes the insert's layer). straight (0.210): its
    straight lines only (no arcs, circles, nor a polyline's bulged sides — see `arcs`)."""
    if e.kind == "line":
        return [(e.layer, list(e.points))]
    if e.kind == "polyline":
        pts = list(e.points)
        if len(pts) < 2:
            return []
        n = len(pts) if e.closed else len(pts) - 1
        if straight:                                         # (each straight side a polyline of its own)
            return [(e.layer, [pts[k], pts[(k + 1) % len(pts)]]) for k in range(n)
                    if abs(e.bulges[k] if k < len(e.bulges) else 0.0) < 1e-9]
        out = [pts[0]]
        for k in range(n):
            b = e.bulges[k] if k < len(e.bulges) else 0.0
            out += _bulge_points(pts[k], pts[(k + 1) % len(pts)], b)[1:]
        return [(e.layer, out)]
    if e.kind in ("arc", "circle") and straight:
        return []
    if e.kind == "arc":
        return [(e.layer, _arc_points(e.points[0], e.radius, *e.angles))]
    if e.kind == "circle":
        return [(e.layer, _arc_points(e.points[0], e.radius, 0.0, 360.0))]
    if e.kind == "insert" and e.block in blocks and depth < 8:
        base, inner = blocks[e.block]
        out = []
        for sub in inner:
            for layer, pts in entity_polylines(sub, blocks, depth + 1, straight):
                out.append((e.layer if layer == "0" else layer,
                            _transform(pts, base, e.points[0], e.rotation, e.scale)))
        return out
    return []


def _bulge_arc(p, q, bulge):
    """(0.210) The arc of a polyline's side from p to q with this bulge: (centre, radius, start, end) in degrees,
    counter-clockwise — or None (straight)."""
    if abs(bulge) < 1e-9:
        return None
    theta = 4 * math.atan(bulge)
    chord = math.hypot(q[0] - p[0], q[1] - p[1])
    if chord < 1e-12:
        return None
    r = chord / (2 * math.sin(theta / 2))
    d = r * math.cos(theta / 2)
    nx, ny = -(q[1] - p[1]) / chord, (q[0] - p[0]) / chord
    c = ((p[0] + q[0]) / 2 + nx * d, (p[1] + q[1]) / 2 + ny * d)
    a_p = math.degrees(math.atan2(p[1] - c[1], p[0] - c[0]))
    a_q = math.degrees(math.atan2(q[1] - c[1], q[0] - c[0]))
    return c, math.hypot(p[0] - c[0], p[1] - c[1]), *((a_p, a_q) if theta > 0 else (a_q, a_p))


def entity_arcs(e, blocks, depth=0):
    """(0.210) An entity's arcs as arcs — an ARC, a CIRCLE (0 to 360), a polyline's bulged sides, those of the blocks
    inserted (moved, turned; a block scaled unevenly or mirrored left out): [(layer, centre (x, y), radius, start,
    end)] in drawing units and degrees, counter-clockwise."""
    if e.kind == "arc":
        return [(e.layer, tuple(e.points[0]), float(e.radius), float(e.angles[0]), float(e.angles[1]))]
    if e.kind == "circle":
        return [(e.layer, tuple(e.points[0]), float(e.radius), 0.0, 360.0)]
    if e.kind == "polyline":
        pts = list(e.points)
        n = len(pts) if e.closed else len(pts) - 1
        out = []
        for k in range(max(n, 0)):
            found = _bulge_arc(pts[k], pts[(k + 1) % len(pts)], e.bulges[k] if k < len(e.bulges) else 0.0)
            if found is not None:
                out.append((e.layer,) + found)
        return out
    if e.kind == "insert" and e.block in blocks and depth < 8:
        sx, sy = e.scale
        if abs(abs(sx) - abs(sy)) > 1e-9 or sx <= 0 or sy <= 0:
            return []
        base, inner = blocks[e.block]
        out = []
        for sub in inner:
            for layer, c, r, a0, a1 in entity_arcs(sub, blocks, depth + 1):
                c2 = _transform([c], base, e.points[0], e.rotation, e.scale)[0]
                out.append((e.layer if layer == "0" else layer, c2, r * sx, a0 + e.rotation, a1 + e.rotation))
        return out
    return []


def arcs(drawing):
    """(0.210) {layer: [(centre (x, y), radius, start, end)]} — every arc drawn as an arc, in metres and degrees."""
    out = {}
    s = float(drawing.units)
    for e in drawing.entities:
        for layer, c, r, a0, a1 in entity_arcs(e, drawing.blocks):
            if r > 0:
                out.setdefault(layer, []).append(((c[0] * s, c[1] * s), r * s, a0, a1))
    return out


def entity_closed(e, blocks, depth=0):
    """(0.211) An entity's closed shapes: a closed polyline with straight sides — [(layer, "polygon", corners)] —, a
    circle — [(layer, "circle", (centre, radius))] —, those of the blocks inserted (moved, turned; a circle in a block
    scaled unevenly or mirrored left out); drawing units."""
    if e.kind == "polyline" and e.closed and len(e.points) >= 3 and all(abs(b) < 1e-9 for b in e.bulges):
        return [(e.layer, "polygon", list(e.points))]
    if e.kind == "circle":
        return [(e.layer, "circle", (tuple(e.points[0]), float(e.radius)))]
    if e.kind == "insert" and e.block in blocks and depth < 8:
        base, inner = blocks[e.block]
        sx, sy = e.scale
        out = []
        for sub in inner:
            for layer, kind, data in entity_closed(sub, blocks, depth + 1):
                layer = e.layer if layer == "0" else layer
                if kind == "polygon":
                    out.append((layer, kind, _transform(data, base, e.points[0], e.rotation, e.scale)))
                elif abs(abs(sx) - abs(sy)) < 1e-9 and sx > 0 and sy > 0:
                    c = _transform([data[0]], base, e.points[0], e.rotation, e.scale)[0]
                    out.append((layer, kind, (c, data[1] * sx)))
        return out
    return []


def closed_shapes(drawing):
    """(0.211) {layer: ([polygon corners (N, 2)], [(centre (2,), radius)])} in metres — what columns are drawn as."""
    out = {}
    s = float(drawing.units)
    for e in drawing.entities:
        for layer, kind, data in entity_closed(e, drawing.blocks):
            polygons, circles = out.setdefault(layer, ([], []))
            if kind == "polygon":
                polygons.append(np.asarray(data, dtype=float) * s)
            else:
                circles.append((np.asarray(data[0], dtype=float) * s, float(data[1]) * s))
    return out


def segments(drawing, straight=False):
    """{layer: (K, 2, 2) segments in metres} of everything drawn (texts left out) — straight (0.210): of its
    straight lines only (the arcs: `arcs`)."""
    out = {}
    s = float(drawing.units)
    for e in drawing.entities:
        for layer, pts in entity_polylines(e, drawing.blocks, straight=straight):
            if len(pts) < 2:
                continue
            p = np.asarray(pts, dtype=float) * s
            out.setdefault(layer, []).append(np.stack((p[:-1], p[1:]), axis=1))
    return {k: np.concatenate(v) for k, v in out.items()}


def layers(drawing):
    """{layer: (entities, segments)} — what each layer has, for the list of layers."""
    counts = {}
    for e in drawing.entities:
        counts.setdefault(e.layer, [0, 0])[0] += 1
    for layer, segs in segments(drawing).items():
        counts.setdefault(layer, [0, 0])[1] = len(segs)
    return {k: tuple(v) for k, v in counts.items()}
