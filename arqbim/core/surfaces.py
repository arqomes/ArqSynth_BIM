"""Patterned wall surfaces for fabrication (0.173, Phase 10, step 2): a finish laid on a wall's face — the face less
its doors and windows — as slats (ripado: strips with a gap between them, upright or level), as half-round flutes
(canelado), as a perforated sheet (perfurado: round holes on a square grid, a margin round its edges), or (0.175) as
a wavy surface (ondulado: ribs cut by the CNC, each one's front a wave, the waves turning from one to the next).
Each made as a fabricator makes it: the slats' and flutes' pieces (one per run between openings), the panels a
perforated finish is cut into (boards of 1,22 × 2,44 m cut round the openings) and each panel's holes (only whole
cells of its own grid, clear of its edges and the openings), the ribs' outlines, for the CNC.

Pure numpy and shapely: the face's own 2D frame — u along the wall, v up — and w out of it; metres."""

import math

import numpy as np

PATTERNS = ("ripado", "canelado", "perfurado", "ondulado")
HOLE_SHAPES = ("redondo", "quadrado")   # (0.389) a perforated sheet's holes: round or square
GRIDS = ("reta", "diagonal")            # (0.389) their grid: square, or turned 45° (quincôncio; square holes: losangos)
MIN_HOLE = 0.003                        # m: (0.389) a hole a picture makes smaller than this is left out
DEFAULTS = {                    # slat / flute width, gap, direction; hole diameter, pitch, margin
    # (0.434, the addon's «Ripado») and a frame round it (its width; 0: none), battens behind the slats across them
    # (how many; their width, their thickness: the slats stand off the wall by it)
    "ripado": {"width": 0.04, "gap": 0.02, "direction": "vertical", "frame": 0.0, "battens": 0.0,
               "batten_w": 0.04, "batten_d": 0.02},
    "canelado": {"width": 0.04, "gap": 0.0, "direction": "vertical"},
    # (0.389) and the holes' shape, their grid, the boards' size, the joint between them, a picture («Imagem»: its
    # dark parts big holes, its light parts small ones or none)
    "perfurado": {"diameter": 0.03, "pitch": 0.06, "margin": 0.05, "hole": "redondo", "grid": "reta",
                  "sheet_w": 1.22, "sheet_h": 2.44, "joint": 0.0, "mask": "",
                  # (0.540) free holes from the Visual Graph (free_text: one panel's, repeated board by board or not)
                  "free": "", "free_repeat": 1.0},
    # (0.175) a wavy surface of ribs: their thickness, the gap, level or upright; the wave's amplitude and length,
    # its shift (degrees for each metre across: the waves turn), how far its trough stands out of the wall
    "ondulado": {"width": 0.018, "gap": 0.018, "direction": "horizontal", "amplitude": 0.06, "wavelength": 1.20,
                 "shift": 90.0, "depth": 0.02},
}
WAVE_STEP = 0.02                # m: a rib's wavy front drawn by a point this often
MAX_WAVE_POINTS = 200000        # (all its ribs' points: more is refused — the model would be too heavy)
SHEET = (1.22, 2.44)            # m: a board's size (a perforated finish's panels)
SEGMENTS = 12                   # a hole's sides (a multiple of 4: the grid cell's corners are among its rays)
MAX_HOLES = 20000               # a finish with more is refused (its sheet in the model would be too heavy)
MAX_STRIPS = 3000


def strips(face, width, gap, direction="vertical"):
    """[(u0, v0, u1, v1)] the pieces of slats `width` wide, `gap` apart, across the face (a shapely polygon in
    (u, v)) — upright (along v) or level (along u) — each cut where an opening interrupts it."""
    from shapely.geometry import box
    u0, v0, u1, v1 = face.bounds
    pitch = width + gap
    out = []
    if pitch <= 1e-6:
        return out
    level = direction == "horizontal"
    a0, a1 = (v0, v1) if level else (u0, u1)
    n = int(math.floor((a1 - a0 + gap) / pitch + 1e-9))
    start = a0 + ((a1 - a0) - (n * pitch - gap)) / 2.0              # (centred on the face)
    for k in range(n):
        a, b = round(start + k * pitch, 6), round(start + k * pitch + width, 6)     # (no slivers at an opening)
        strip = box(u0, a, u1, b) if level else box(a, v0, b, v1)
        piece = strip.intersection(face)
        for q in getattr(piece, "geoms", [piece]):
            if q.geom_type == "Polygon" and q.area > 1e-6:
                bu0, bv0, bu1, bv1 = q.bounds
                if ((bu1 - bu0) if level else (bv1 - bv0)) > 0.05:      # (bits shorter than 5 cm left out)
                    out.append((bu0, bv0, bu1, bv1))
    return out


MAX_BATTENS = 12


def ripado_parts(face, d):
    """(0.434, the addon's «Ripado»: ripado_core.layout over a wall's face) (frame, battens, slats, inner): `frame` the
    band `d["frame"]` wide round the face's outline (a shapely geometry, or None); `battens` [polygons] —
    `d["battens"]` of them, `d["batten_w"]` wide, behind the slats and across them, in equal bands of the face inside
    the frame, each cut where an opening interrupts it —; `slats` the strips (as strips()) of that inside; `inner`
    that inside. Refused (ValueError) when the frame leaves nothing inside."""
    from shapely.geometry import box
    f = max(0.0, float(d.get("frame") or 0.0))
    inner, frame = face, None
    if f > 1e-9:
        u0, v0, u1, v1 = face.bounds
        if 2 * f >= min(u1 - u0, v1 - v0) - 0.05:
            raise ValueError("frame")
        core = box(u0 + f, v0 + f, u1 - f, v1 - f)
        inner = face.intersection(core)
        frame = face.difference(core)
    battens = []
    n = min(MAX_BATTENS, max(0, int(round(float(d.get("battens") or 0)))))
    if n and not inner.is_empty:
        u0, v0, u1, v1 = inner.bounds
        w = float(d.get("batten_w") or 0.04) / 2.0
        level = d.get("direction") == "horizontal"        # (level slats: upright battens, and the other way)
        for k in range(n):
            if level:
                c = u0 + (k + 0.5) * (u1 - u0) / n
                band = box(c - w, v0, c + w, v1)
            else:
                c = v0 + (k + 0.5) * (v1 - v0) / n
                band = box(u0, c - w, u1, c + w)
            piece = inner.intersection(band)
            battens += [q for q in getattr(piece, "geoms", [piece]) if q.geom_type == "Polygon" and q.area > 1e-6]
    slats = strips(inner, d["width"], d["gap"], d.get("direction", "vertical")) if not inner.is_empty else []
    return frame, battens, slats, inner


def wave(b, amplitude, wavelength, phase, depth):
    """How far a wavy surface stands out of the wall at b (m along its wave): from `depth` (its trough) to
    `depth` + `amplitude` (its crest)."""
    return depth + amplitude * (1.0 + np.sin(2.0 * np.pi * np.asarray(b, dtype=float) / wavelength + phase)) / 2.0


def ribs(face, rib, gap, amplitude, wavelength, shift, depth, direction="horizontal"):
    """[(a0, a1, outline)] a wavy surface's ribs (0.175, ondulado): boards `rib` thick, `gap` apart, across the
    face — level ones stacked up it, the wave along the wall; or upright ones side by side, the wave up it —, each
    cut where an opening interrupts it (as the slats). a0..a1: the rib across; outline [(b, w)]: its back on the
    wall (w = 0) from b0 to b1 along it, its front the wave — shifted `shift` degrees for each metre across, so that
    the waves turn — counter-clockwise."""
    level = direction == "horizontal"
    out = []
    for u0, v0, u1, v1 in strips(face, rib, gap, direction):
        a0, a1, b0, b1 = (v0, v1, u0, u1) if level else (u0, u1, v0, v1)
        phase = math.radians(shift) * (a0 + a1) / 2.0
        b = np.linspace(b0, b1, max(2, int(math.ceil((b1 - b0) / WAVE_STEP)) + 1))
        w = wave(b, amplitude, wavelength, phase, depth)
        out.append((a0, a1, [(b0, 0.0), (b1, 0.0)] + [(float(x), float(y)) for x, y in zip(b[::-1], w[::-1])]))
    return out


def panels(face, size=SHEET):
    """[shapely Polygon] the panels a perforated finish is cut into: boards of `size` (w, h) from the face's corner,
    each cut to the face — round its edges and its openings; a board an opening parts in two, two panels."""
    from shapely.geometry import box
    u0, v0, u1, v1 = face.bounds
    out = []
    w, h = size
    u = u0
    while u < u1 - 1e-6:
        v = v0
        while v < v1 - 1e-6:
            piece = box(u, v, min(u + w, u1), min(v + h, v1)).intersection(face)
            out += [q for q in getattr(piece, "geoms", [piece]) if q.geom_type == "Polygon" and q.area > 1e-4]
            v += h
        u += w
    return out


def panel_holes(face, diameter, pitch, margin, size=SHEET):
    """[(panel, [(u, v)])] each panel of the face with its holes' centres: every panel perforated on its own, a
    `margin` clear round its edges (the joints between two too) and its openings — as the panels are made."""
    return [(q, [tuple(c) for c in centres]) for q, centres, _d in perforation(face, diameter, pitch, margin, size)]


def holes(face, diameter, pitch, margin, size=SHEET, joint=0.0, grid="reta", mask=None):
    """[(u, v)] the centres of a perforated finish's holes, all its panels'."""
    return [tuple(c) for _q, centres, _d in perforation(face, diameter, pitch, margin, size, joint, grid, mask)
            for c in centres]


def _turned(points, degrees):
    """(N, 2) points turned about (0, 0)."""
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    p = np.asarray(points, dtype=float).reshape(-1, 2)
    return np.column_stack((c * p[:, 0] - s * p[:, 1], s * p[:, 0] + c * p[:, 1]))


def _polygons(geom):
    return [q for q in getattr(geom, "geoms", [geom]) if q.geom_type == "Polygon" and q.area > 1e-6]


def perforation(face, diameter, pitch, margin, size=SHEET, joint=0.0, grid="reta", mask=None):
    """(0.389) [(panel, centres (k, 2), diameters (k,))] a perforated sheet's panels — boards of `size` from the face's
    corner, `joint` apart (each one that much smaller round its edges) —, each with its holes: a square grid of
    `pitch` (or turned 45°: «diagonal»), only whole cells clear of a `margin` round the panel's edges and openings;
    each hole `diameter` — or, with a picture (`mask`: (h, w) darkness 0–1, row 0 at the top, laid over the whole
    face, its middle on the face's middle, as big as it must be to cover it), as much of it as the picture is dark
    there (those smaller than MIN_HOLE left out)."""
    from shapely import affinity
    out = []
    turn = 45.0 if grid == "diagonal" else 0.0
    for board in panels(face, size):
        for q in _polygons(board.buffer(-joint / 2.0, join_style=2) if joint > 0 else board):
            local = affinity.rotate(q, -turn, origin=(0.0, 0.0)) if turn else q
            centres = np.array(_grid(local, diameter, pitch, margin), dtype=float).reshape(-1, 2)
            if turn and len(centres):
                centres = _turned(centres, turn)
            sizes = np.full(len(centres), float(diameter))
            if mask is not None and len(centres):
                sizes = diameter * darkness(mask, face.bounds, centres)
                keep = sizes >= MIN_HOLE
                centres, sizes = centres[keep], sizes[keep]
            out.append((q, centres, sizes))
    return out


def darkness(mask, bounds, points):
    """(0.389) How dark a picture is (0–1) at these points of a face (u, v): the picture over the face's bounds,
    centred and big enough to cover them (as a photograph cut to a frame)."""
    mask = np.asarray(mask, dtype=float)
    h, w = mask.shape[:2]
    u0, v0, u1, v1 = bounds
    fw, fh = max(u1 - u0, 1e-9), max(v1 - v0, 1e-9)
    scale = max(w / fw, h / fh)                         # (pixels per metre: the picture covers the face)
    ox, oy = (w - fw * scale) / 2.0, (h - fh * scale) / 2.0
    p = np.asarray(points, dtype=float).reshape(-1, 2)
    x = np.clip(np.floor(ox + (p[:, 0] - u0) * scale), 0, w - 1).astype(int)
    y = np.clip(np.floor(oy + (v1 - p[:, 1]) * scale), 0, h - 1).astype(int)
    return np.clip(mask[y, x], 0.0, 1.0)


def _grid(face, diameter, pitch, margin):
    """[(u, v)] the holes of one panel: a square grid of `pitch` centred on it (a `margin` in), only the cells wholly
    inside the panel less the margin round its edges and openings."""
    import shapely
    if pitch <= diameter + 0.002 or diameter <= 0.0:
        return []
    inner = face.buffer(-margin, join_style=2)
    if inner.is_empty:
        return []
    u0, v0, u1, v1 = inner.bounds
    nu, nv = int((u1 - u0) / pitch + 1e-9), int((v1 - v0) / pitch + 1e-9)
    if nu < 1 or nv < 1:
        return []
    cu = u0 + ((u1 - u0) - nu * pitch) / 2.0 + pitch / 2.0
    cv = v0 + ((v1 - v0) - nv * pitch) / 2.0 + pitch / 2.0
    gu, gv = np.meshgrid(cu + np.arange(nu) * pitch, cv + np.arange(nv) * pitch)
    centres = np.column_stack((gu.ravel(), gv.ravel()))
    cells = shapely.box(centres[:, 0] - pitch / 2, centres[:, 1] - pitch / 2, centres[:, 0] + pitch / 2,
                        centres[:, 1] + pitch / 2)
    shapely.prepare(inner)
    return [tuple(c) for c in centres[shapely.contains(inner, cells)]]


def perforated_mesh(face, thickness, diameter, pitch, margin, size=SHEET, joint=0.0, grid="reta", hole="redondo",
                    mask=None):
    """(vertices (N, 3) in (u, v, w), triangles (M, 3)) of a perforated sheet on the face: its grid's cells
    triangulated with their hole (round or square; the hole's wall too) — every cell edge shares its points with the
    next, so the sheet has no cracks —, the rest of the face (its edges, round its openings) by a constrained
    triangulation, its edges' sides. (0.389) With a `joint`, each panel a sheet of its own; a «diagonal» grid made in
    its own frame (turned 45°) and turned back; a picture (`mask`) makes each hole its own size."""
    from shapely import affinity
    from shapely.geometry.polygon import orient
    face = orient(face, 1.0)                          # (its outline counter-clockwise, its openings clockwise)
    found = perforation(face, diameter, pitch, margin, size, joint, grid, mask)
    if joint > 0:
        regions = [(orient(q, 1.0), c, d) for q, c, d in found]
    else:                                             # (one sheet: the panels' holes on it, no joints)
        regions = [(face, np.concatenate([c for _q, c, _d in found]) if found else np.zeros((0, 2)),
                    np.concatenate([d for _q, _c, d in found]) if found else np.zeros(0))]
    turn = 45.0 if grid == "diagonal" else 0.0
    verts, tris, count = [], [], 0
    for region, centres, sizes in regions:
        local = orient(affinity.rotate(region, -turn, origin=(0.0, 0.0)), 1.0) if turn else region
        v, tr = _sheet_mesh(local, thickness, _turned(centres, -turn) if turn else centres, sizes, pitch,
                            hole == "quadrado")
        if not len(v):
            continue
        if turn:
            v[:, :2] = _turned(v[:, :2], turn)
        verts.append(v)
        tris.append(tr + count)
        count += len(v)
    if not verts:
        return np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64)
    return np.concatenate(verts), np.concatenate(tris).astype(np.int64)


def _sheet_mesh(face, thickness, centres, sizes, pitch, square=False):
    """One perforated sheet (face: oriented, in the grid's own frame — its cells upright squares of `pitch`):
    vertices (u, v, w) and triangles; each hole of its own size (`sizes`, the diameter or the square's side)."""
    import shapely
    from shapely.ops import unary_union
    centres = np.asarray(centres, dtype=float).reshape(-1, 2)
    verts, tris = [], []
    count = 0
    t = float(thickness)
    if len(centres):
        n = SEGMENTS                                  # (rays at 15° + k·30°: the cell's corners at 45°, 135°…)
        ang = np.radians(15.0) + np.arange(n) * (2 * np.pi / n)
        ca, sa = np.cos(ang), np.sin(ang)
        r = np.asarray(sizes, dtype=float).reshape(-1, 1) / 2.0
        if square:                                    # (0.389) a square hole: its corners on the 45° rays
            r = r / np.maximum(np.abs(ca), np.abs(sa))
        s = pitch / 2.0
        rb = s / np.maximum(np.abs(ca), np.abs(sa))               # (the ray to the cell's edge: its corners among them)
        m = len(centres)
        cu, cv = centres[:, 0:1], centres[:, 1:2]
        hole_u, hole_v = cu + r * ca, cv + r * sa                 # (m, n)
        edge_u, edge_v = cu + rb * ca, cv + rb * sa
        # per cell: hole top [0:n], edge top [n:2n], hole bottom [2n:3n], edge bottom [3n:4n]
        block = np.zeros((m, 4 * n, 3))
        for k, (uu, vv, w) in enumerate(((hole_u, hole_v, t), (edge_u, edge_v, t), (hole_u, hole_v, 0.0),
                                         (edge_u, edge_v, 0.0))):
            block[:, k * n:(k + 1) * n, 0], block[:, k * n:(k + 1) * n, 1], block[:, k * n:(k + 1) * n, 2] = uu, vv, w
        verts.append(block.reshape(-1, 3))
        j = np.arange(n)
        jn = (j + 1) % n
        local = np.concatenate([                     # (each face turned outwards: the top up, the hole's wall in)
            np.column_stack((j, n + jn, jn)), np.column_stack((j, n + j, n + jn)),                           # top
            np.column_stack((2 * n + j, 2 * n + jn, 3 * n + jn)), np.column_stack((2 * n + j, 3 * n + jn,
                                                                                    3 * n + j)),            # bottom
            np.column_stack((j, 2 * n + jn, 2 * n + j)), np.column_stack((j, jn, 2 * n + jn))])             # hole
        offsets = (np.arange(m) * 4 * n)[:, None, None]
        tris.append((local[None, :, :] + offsets).reshape(-1, 3))
        count = m * 4 * n
        grid = unary_union(shapely.box(centres[:, 0] - s, centres[:, 1] - s, centres[:, 0] + s, centres[:, 1] + s))
        rest = face.difference(grid.buffer(1e-9, join_style=2))
    else:
        rest = face
    # the rest of the sheet: its top and bottom by a constrained triangulation
    for part in getattr(rest, "geoms", [rest]):
        if part.geom_type != "Polygon" or part.area < 1e-8:
            continue
        tri = shapely.constrained_delaunay_triangles(part)
        coords = []
        for g in tri.geoms:
            ring = np.asarray(g.exterior.coords)[:3]
            # (its winding up: counter-clockwise seen from outside, w up)
            if (ring[1, 0] - ring[0, 0]) * (ring[2, 1] - ring[0, 1]) - (ring[1, 1] - ring[0, 1]) * (ring[2, 0] -
                                                                                                    ring[0, 0]) < 0:
                ring = ring[::-1]
            coords.append(ring)
        if not coords:
            continue
        coords = np.array(coords).reshape(-1, 2)
        k = len(coords)
        top = np.column_stack((coords, np.full(k, t)))
        bottom = np.column_stack((coords, np.zeros(k)))
        verts += [top, bottom]
        idx = np.arange(k).reshape(-1, 3)
        tris += [idx + count, idx[:, ::-1] + count + k]
        count += 2 * k
    # the sides along the face's edges (its outline, its openings)
    rings = [np.asarray(face.exterior.coords)] + [np.asarray(h.coords) for h in face.interiors]
    for ring in rings:
        a, b = ring[:-1], ring[1:]
        k = len(a)
        quad = np.zeros((k * 4, 3))
        quad[0::4, :2], quad[1::4, :2], quad[2::4, :2], quad[3::4, :2] = a, b, b, a
        quad[0::4, 2], quad[1::4, 2], quad[2::4, 2], quad[3::4, 2] = 0.0, 0.0, t, t
        verts.append(quad)
        base = count + np.arange(k)[:, None] * 4
        tris += [np.hstack((base, base + 1, base + 2)), np.hstack((base, base + 2, base + 3))]
        count += 4 * k
    return np.concatenate(verts), np.concatenate(tris).astype(np.int64)


# ---------------------------------------------------------------- (0.540) free holes, from the Visual Graph
# (0.545) triangles, lozenges and slots too; each hole may be turned (its angle, °) and stretched (its ratio: as many
# times longer than wide — a slot's length over its width)
FREE_SHAPES = ("redondo", "quadrado", "hexagonal", "triangular", "losango", "ranhura")
SLOT_RATIO = 3.0                     # a slot's, where none is given (ratio 1)


# (0.551) a hole of the user's own drawing: «desenho:x,y x,y …» — its outline as drawn, made 1 across (its
# width or its height, the larger) about its middle; turned and stretched as the others
DRAWN = "desenho"
_DRAWN = {}


def drawn_ring(shape):
    """(m, 2) the outline of a drawn hole's shape text (size 1, counter-clockwise) — None: not a drawn one, or not
    a closed outline that holds together."""
    if not isinstance(shape, str) or not shape.startswith(DRAWN + ":"):
        return None
    if shape not in _DRAWN:
        ring = None
        try:
            pts = np.array([[float(c) for c in pair.split(",")] for pair in shape[len(DRAWN) + 1:].split()],
                           dtype=float).reshape(-1, 2)
            from shapely.geometry import Polygon
            from shapely.geometry.polygon import orient
            if len(pts) >= 3:
                poly = Polygon(pts)
                if poly.is_valid and poly.area > 1e-6:
                    ring = np.asarray(orient(poly, 1.0).exterior.coords)[:-1]
        except (ValueError, TypeError):
            ring = None
        _DRAWN[shape] = ring
    return _DRAWN[shape]


def drawn_text(points):
    """The shape text of an outline drawn (any size, anywhere): its middle at (0, 0), 1 across. ValueError where it
    does not make a hole (fewer than three points, its sides crossing)."""
    from shapely.geometry import Polygon
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    poly = Polygon(pts) if len(pts) >= 3 else None
    if poly is None or not poly.is_valid or poly.area <= 1e-12:
        raise ValueError("o desenho do furo tem de ser um contorno fechado, sem lados a cruzar")
    x0, y0, x1, y1 = poly.bounds
    size = max(x1 - x0, y1 - y0)
    pts = (pts - ((x0 + x1) / 2.0, (y0 + y1) / 2.0)) / size
    text = DRAWN + ":" + " ".join("{:.4f},{:.4f}".format(x, y) for x, y in pts)
    if drawn_ring(text) is None:
        raise ValueError("o desenho do furo tem de ser um contorno fechado, sem lados a cruzar")
    return text


def valid_shape(shape):
    return shape in FREE_SHAPES or drawn_ring(shape) is not None


def hole_rows(holes):
    """(n, 5) x, y, d, angle (°), ratio of holes given as rows of 3 (x, y, d: not turned, not stretched) or 5."""
    rows = [list(h) for h in holes]
    out = np.zeros((len(rows), 5))
    out[:, 4] = 1.0
    for k, row in enumerate(rows):
        out[k, :len(row)] = row[:5]
    out[:, 4] = np.where(out[:, 4] > 0, out[:, 4], 1.0)
    return out


def free_text(shape, holes):
    """The text a finish keeps its free holes in: «shape|x,y,d;…», mm, one panel's (its corner at 0, 0). (0.545) A
    hole turned or stretched: «x,y,d,angle,ratio» (° and times)."""
    if not valid_shape(shape):
        raise ValueError(shape)
    rows = []
    for x, y, d, a, k in hole_rows(holes):
        row = "{:.1f},{:.1f},{:.1f}".format(x * 1000.0, y * 1000.0, d * 1000.0)
        if abs(a) > 1e-9 or abs(k - 1.0) > 1e-9:
            row += ",{:.1f},{:.3f}".format(a, k)
        rows.append(row)
    return shape + "|" + ";".join(rows)


def free_read(text):
    """(shape, (n, 5) x, y, d in m, angle in °, ratio) of free_text — or None (none, or not readable)."""
    if not text or "|" not in text:
        return None
    shape, _, rows = text.partition("|")
    if not valid_shape(shape):
        return None
    try:
        vals = []
        for row in rows.split(";"):
            if not row:
                continue
            c = [float(v) for v in row.split(",")]
            if len(c) not in (3, 5):
                return None
            vals.append([c[0] / 1000.0, c[1] / 1000.0, c[2] / 1000.0] + c[3:])
    except ValueError:
        return None
    return shape, hole_rows(vals)


_UNIT = {}


def unit_ring(shape):
    """A hole of size 1's outline ((m, 2), about its centre, counter-clockwise): a circle's diameter, a square's
    side, a hexagon's width between flats, a triangle's side, a lozenge's diagonal — 1. (A slot is not one outline
    stretched: slot_ring.)"""
    drawn = drawn_ring(shape)
    if drawn is not None:
        return drawn
    if shape not in _UNIT:
        n, start, radius = {"redondo": (SEGMENTS, 0.0, 0.5), "quadrado": (4, 45.0, math.sqrt(2.0) / 2.0),
                            "hexagonal": (6, 0.0, 1.0 / math.sqrt(3.0)),
                            "triangular": (3, 90.0, 1.0 / math.sqrt(3.0)), "losango": (4, 0.0, 0.5),
                            "ranhura": (SEGMENTS, 0.0, 0.5)}[shape]
        ang = np.radians(start + np.arange(n) * 360.0 / n)
        _UNIT[shape] = np.column_stack((radius * np.cos(ang), radius * np.sin(ang)))
    return _UNIT[shape]


def slot_ring(ratio):
    """A slot of width 1 and length `ratio` (≥ 1) along x: two half circles joined."""
    half = max(float(ratio), 1.0) / 2.0 - 0.5
    n = max(SEGMENTS // 2, 4)
    right = np.radians(-90.0 + np.arange(n + 1) * 180.0 / n)
    left = right + math.pi
    return np.vstack((np.column_stack((half + 0.5 * np.cos(right), 0.5 * np.sin(right))),
                      np.column_stack((-half + 0.5 * np.cos(left), 0.5 * np.sin(left)))))


def _ratio(shape, ratio, n):
    k = np.ones(n) if ratio is None else np.broadcast_to(np.asarray(ratio, dtype=float), (n,)).copy()
    if shape == "ranhura":
        k = np.where(k > 1.0 + 1e-9, k, SLOT_RATIO)
    return np.maximum(k, 1e-6)


def hole_rings(shape, centres, sizes, angle=None, ratio=None):
    """Each hole's outline, a list of (m, 2) arrays (m): its unit outline stretched along its own x, sized, turned
    and put at its centre."""
    centres = np.asarray(centres, dtype=float).reshape(-1, 2)
    sizes = np.asarray(sizes, dtype=float).reshape(-1)
    n = len(sizes)
    k = _ratio(shape, ratio, n)
    a = np.zeros(n) if angle is None else np.radians(np.broadcast_to(np.asarray(angle, dtype=float), (n,)))
    out = []
    unit = unit_ring(shape)
    for i in range(n):
        ring = slot_ring(k[i]) if shape == "ranhura" else unit * (k[i], 1.0)
        c, s = math.cos(a[i]), math.sin(a[i])
        ring = ring * sizes[i]
        out.append(np.column_stack((ring[:, 0] * c - ring[:, 1] * s, ring[:, 0] * s + ring[:, 1] * c)) + centres[i])
    return out


def hole_reach(shape, d, ratio=None):
    """How far a hole reaches from its centre (its corners; stretched: its far end)."""
    d = np.asarray(d, dtype=float)
    if ratio is None and shape in FREE_SHAPES and shape != "ranhura":
        return d / 2.0 * {"redondo": 1.0, "quadrado": math.sqrt(2.0), "hexagonal": 2.0 / math.sqrt(3.0),
                          "triangular": 2.0 / math.sqrt(3.0), "losango": 1.0}[shape]
    k = _ratio(shape, ratio, d.size).reshape(d.shape)
    if shape == "ranhura":
        return d * k / 2.0
    unit = unit_ring(shape)
    far = np.hypot(unit[:, 0][None, :] * k.reshape(-1, 1), unit[:, 1][None, :]).max(axis=1)
    return d * far.reshape(d.shape)


def hole_area(shape, d, ratio=None):
    """Each hole's area."""
    d = np.asarray(d, dtype=float)
    k = _ratio(shape, ratio, d.size).reshape(d.shape)
    if shape == "ranhura":
        return d * d * (k - 1.0) + math.pi * d * d / 4.0
    drawn = drawn_ring(shape)
    if drawn is not None:                                # (0.551) its outline's own area, at size 1
        x, y = drawn[:, 0], drawn[:, 1]
        return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))) * d * d * k
    unit = {"redondo": math.pi / 4.0, "quadrado": 1.0, "hexagonal": math.sqrt(3.0) / 2.0,
            "triangular": math.sqrt(3.0) / 4.0, "losango": 0.5}[shape]
    return unit * d * d * k


class HoleSizes(np.ndarray):
    """Holes' sizes (as free_perforation always gave them) that also carry each hole's `angle` (°) and `ratio`."""
    angle = None
    ratio = None


def with_extras(sizes, angle, ratio):
    out = np.asarray(sizes, dtype=float).view(HoleSizes)
    out.angle, out.ratio = np.asarray(angle, dtype=float), np.asarray(ratio, dtype=float)
    return out


def extras(sizes):
    """(angle (n,), ratio (n,)) of sizes (HoleSizes: its own; plain numbers: none turned, none stretched)."""
    n = len(sizes)
    angle, ratio = getattr(sizes, "angle", None), getattr(sizes, "ratio", None)
    return (np.zeros(n) if angle is None or len(angle) != n else angle,
            np.ones(n) if ratio is None or len(ratio) != n else ratio)


def free_perforation(face, shape, holes, margin, size, repeat=True):
    """[(panel, centres (k, 2), sizes (k,))] free holes (one panel's: x, y, d from its corner) on the face: boards
    of `size` from its corner, each with the same holes (`repeat`) — or only the first board —, only those wholly
    `margin` clear of the board's edges and the openings. (0.545) The sizes carry each hole's angle and ratio
    (extras)."""
    import shapely
    holes = hole_rows(holes)
    out = []
    u0, v0 = face.bounds[:2]
    for board in panels(face, size):
        i = math.floor((board.bounds[0] - u0) / size[0] + 1e-6)   # (the board's tile, even where an opening cut it)
        j = math.floor((board.bounds[1] - v0) / size[1] + 1e-6)
        if not repeat and (i, j) != (0, 0):
            continue
        ox, oy = u0 + i * size[0], v0 + j * size[1]
        if not len(holes):
            out.append((board, np.zeros((0, 2)), np.zeros(0)))
            continue
        c = holes[:, :2] + (ox, oy)
        d = holes[:, 2]
        room = board.buffer(-margin, join_style=2) if margin > 0 else board
        keep = np.zeros(len(c), dtype=bool)
        if not room.is_empty:
            pts = shapely.points(c)
            keep = shapely.contains_xy(room, c[:, 0], c[:, 1]) & \
                (shapely.distance(room.boundary, pts) >= hole_reach(shape, d, holes[:, 4]) - 1e-9)
        out.append((board, c[keep], with_extras(d[keep], holes[keep, 3], holes[keep, 4])))
    return out


def _hole_polygons(shape, centres, sizes, angle=None, ratio=None):
    import shapely
    sizes = np.asarray(sizes, dtype=float)
    plain = (angle is None or not np.any(angle)) and (ratio is None or np.allclose(ratio, 1.0))
    if plain and shape in ("redondo", "quadrado", "hexagonal"):       # (as before 0.545, all at once)
        n = {"redondo": SEGMENTS, "quadrado": 4, "hexagonal": 6}[shape]
        start = {"redondo": 0.0, "quadrado": 45.0, "hexagonal": 0.0}[shape]
        ang = np.radians(start + np.arange(n) * 360.0 / n)
        r = hole_reach(shape, sizes)[:, None]
        ring = np.stack((centres[:, 0:1] + r * np.cos(ang), centres[:, 1:2] + r * np.sin(ang)), axis=-1)
        return shapely.polygons(ring)
    return np.array([shapely.Polygon(ring) for ring in hole_rings(shape, centres, sizes, angle, ratio)], dtype=object)


def free_mesh(face, thickness, found, shape):
    """(vertices (u, v, w), triangles) of a sheet with free holes (free_perforation's): the face less its holes,
    top and bottom by a constrained triangulation, the sides of every edge (outline, openings, holes)."""
    import shapely
    from shapely.geometry.polygon import orient
    t = float(thickness)
    centres = np.concatenate([c for _q, c, _d in found]) if found else np.zeros((0, 2))
    sizes = np.concatenate([d for _q, _c, d in found]) if found else np.zeros(0)
    angle = np.concatenate([extras(d)[0] for _q, _c, d in found]) if found else np.zeros(0)       # (0.545)
    ratio = np.concatenate([extras(d)[1] for _q, _c, d in found]) if found else np.zeros(0)
    sheet = face
    if len(centres):
        sheet = face.difference(shapely.union_all(_hole_polygons(shape, centres, sizes, angle, ratio)))
    verts, tris, count = [], [], 0
    for part in getattr(sheet, "geoms", [sheet]):
        if part.geom_type != "Polygon" or part.area < 1e-8:
            continue
        part = orient(part, 1.0)
        tri = shapely.constrained_delaunay_triangles(part)
        coords = np.array([np.asarray(g.exterior.coords)[:3] for g in tri.geoms]).reshape(-1, 3, 2)
        if len(coords):
            a, b, c = coords[:, 0], coords[:, 1], coords[:, 2]
            cw = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0]) < 0
            coords[cw] = coords[cw][:, ::-1]
            flat = coords.reshape(-1, 2)
            k = len(flat)
            verts += [np.column_stack((flat, np.full(k, t))), np.column_stack((flat, np.zeros(k)))]
            idx = np.arange(k).reshape(-1, 3)
            tris += [idx + count, idx[:, ::-1] + count + k]
            count += 2 * k
        for ring in [np.asarray(part.exterior.coords)] + [np.asarray(h.coords) for h in part.interiors]:
            a, b = ring[:-1], ring[1:]
            k = len(a)
            quad = np.zeros((k * 4, 3))
            quad[0::4, :2], quad[1::4, :2], quad[2::4, :2], quad[3::4, :2] = a, b, b, a
            quad[2::4, 2], quad[3::4, 2] = t, t
            verts.append(quad)
            base = count + np.arange(k)[:, None] * 4
            tris += [np.hstack((base, base + 1, base + 2)), np.hstack((base, base + 2, base + 3))]
            count += 4 * k
    if not verts:
        return np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64)
    # (0.548) each point once: the view then hides the lines between the triangles of one flat face — they were
    # all drawn, the sheet crossed by its own triangulation
    return weld(np.concatenate(verts), np.concatenate(tris).astype(np.int64))


def weld(verts, tris, places=7):
    """(0.548) A mesh with each point once (those at the same place — to a tenth of a micron — made one): the view
    then knows which triangles are neighbours, and draws no line between two of one flat face."""
    verts = np.asarray(verts, dtype=float)
    tris = np.asarray(tris, dtype=np.int64)
    if not len(verts):
        return verts, tris
    _keys, first, inverse = np.unique(np.round(verts, places), axis=0, return_index=True, return_inverse=True)
    tris = inverse.reshape(-1)[tris]
    keep = (tris[:, 0] != tris[:, 1]) & (tris[:, 1] != tris[:, 2]) & (tris[:, 0] != tris[:, 2])
    return verts[first], tris[keep]


def strip_step(radius, length, sag=0.0005):
    """(0.548) How wide the flat strips of a sheet bent round an arc of `radius` are, for each to stay within `sag`
    of the arc (between 0,5° and 4° of it) — a whole number of them in `length`."""
    angle = 2.0 * math.acos(max(-1.0, min(1.0, 1.0 - sag / max(radius, 1e-6))))
    angle = min(max(angle, math.radians(0.5)), math.radians(4.0))
    n = max(1, int(math.ceil(length / (radius * angle) - 1e-9)))
    return length / n


def split_strips(verts, tris, step):
    """(0.548) A flat mesh (x along, y up, z out) cut along the upright lines x = k·step, so that no triangle
    crosses one: bent strip by strip (bend), each strip stays flat and only those lines fold. A cut point is worked
    out from its edge's two ends in one order, whichever triangle asks: neighbours meet exactly."""
    verts = np.asarray(verts, dtype=float)
    tris = np.asarray(tris, dtype=np.int64)
    x = verts[:, 0][tris]
    lo = np.floor(x.min(axis=1) / step + 1e-9)
    hi = np.ceil(x.max(axis=1) / step - 1e-9)
    crossing = hi - lo > 1
    if not crossing.any():
        return verts, tris
    new_v, new_t, n = [], [], len(verts)

    def cut(p, q, at):                                   # (the point of the edge pq at x = at)
        if tuple(q) < tuple(p):
            p, q = q, p
        f = (at - p[0]) / (q[0] - p[0])
        out = p + (q - p) * f
        out[0] = at
        return out

    def clip(poly, at, keep_left):
        out = []
        for i, p in enumerate(poly):
            q = poly[(i + 1) % len(poly)]
            pin = p[0] <= at + 1e-12 if keep_left else p[0] >= at - 1e-12
            qin = q[0] <= at + 1e-12 if keep_left else q[0] >= at - 1e-12
            if pin:
                out.append(p)
            if pin != qin and abs(q[0] - p[0]) > 1e-12:
                out.append(cut(p, q, at))
        return out

    for tri, k0, k1 in zip(tris[crossing], lo[crossing].astype(int), hi[crossing].astype(int)):
        poly = [verts[i] for i in tri]
        for k in range(k0, k1):
            part = clip(clip(poly, k * step, False), (k + 1) * step, True)
            part = [p for i, p in enumerate(part) if np.abs(p - part[i - 1]).max() > 1e-10]
            for i in range(1, len(part) - 1):
                new_v += [part[0], part[i], part[i + 1]]
                new_t.append((n, n + 1, n + 2))
                n += 3
    if not new_t:
        return verts, tris[~crossing]
    return np.vstack((verts, np.array(new_v))), np.vstack((tris[~crossing], np.array(new_t, dtype=np.int64)))


def bend(uvw, radius, turn=1.0, out=1.0, step=None):
    """(0.548) A flat sheet (u along, v up, w off the face) bent round an upright axis at the origin: u along the
    arc of `radius` from the x axis (`turn` +1: counter-clockwise), w away from the axis (`out` +1) or towards it.
    `step`: in flat strips that wide (split_strips's) — each point between its strip's two lines, straight —, as a
    curved wall itself is drawn; None: on the arc itself."""
    uvw = np.asarray(uvw, dtype=float)

    def on_arc(u, w):
        a = turn * u / radius
        r = radius + out * w
        return np.column_stack((r * np.cos(a), r * np.sin(a)))
    if step is None:
        return np.column_stack((on_arc(uvw[:, 0], uvw[:, 2]), uvw[:, 1]))
    k = np.floor(uvw[:, 0] / step + 1e-9)
    f = np.clip(uvw[:, 0] / step - k, 0.0, 1.0)[:, None]
    xy = on_arc(k * step, uvw[:, 2]) * (1.0 - f) + on_arc((k + 1.0) * step, uvw[:, 2]) * f
    return np.column_stack((xy, uvw[:, 1]))


def open_area(diameter, pitch):
    """The share of a perforated sheet that is holes (its open area, as the makers give it)."""
    return math.pi * diameter * diameter / 4.0 / (pitch * pitch)
