"""(0.317) What a plan or a section cuts, for the screen as it is on paper (ui/pdf.py): each fill's background — its
material's own, or its category's fill in the project's graphic style — as triangles, and its pattern's lines over it,
drafting patterns at the view's scale; in 3D on the cutting plane, element by element (a selected one leaves its fills
out: its selection's colour shows). Pure NumPy and shapely (no GPU), made once per change of what is cut."""

import numpy as np

from ..core import drawing2d
from ..core import patterns as core_patterns
from . import graphic_styles as styles_model

WHITE = "#ffffff"
INK = "#000000"
DOT = 0.25            # mm on paper: a dot drawn as a stroke this long
SEAMS = "~seams"      # (0.428) the owner of the lines between materials inside what is cut (None: the outline round it)


def layers_of(key, own, gstyle):
    """What a fill is painted with, bottom first: [(pattern key, or families of lines, colour)] — "solid" a fill;
    None: the dark poché as it is (detail "coarse")."""
    if key is None:
        return None
    if key in own:                                          # (its material's own: paper, its background, its foreground)
        background, foreground = own[key]
        out = [] if background and background[0] == core_patterns.SOLID else [(core_patterns.SOLID, WHITE)]
        return out + [layer for layer in (background, foreground) if layer]
    if isinstance(key, str) and key.startswith("colour:"):  # (a graphic rule's colour, an empty cut)
        return [(core_patterns.SOLID, key[len("colour:"):])]
    fill, angles, spacing = styles_model.hatch(gstyle, key)
    out = [(core_patterns.SOLID, fill)]
    library = styles_model.library_pattern(gstyle, key)
    if library:
        out.append((library, INK))
    if angles:
        out.append((tuple((float(a), 0.0, 0.0, 0.0, float(spacing), ()) for a in angles), INK))
    return out


def _lines(boundary):
    """The line strings of a region's boundary (one, or several)."""
    if boundary.is_empty:
        return []
    if boundary.geom_type in ("LineString", "LinearRing"):
        return [boundary]
    return [g for part in getattr(boundary, "geoms", ()) for g in _lines(part)]


def _rgb(colour):
    text = str(colour or INK)
    try:
        return tuple(int(text[k:k + 2], 16) / 255.0 for k in (1, 3, 5))
    except ValueError:
        return 0.0, 0.0, 0.0


def build(fills, whose, own, gstyle, scale, origin, u, v, lift):
    """{element: (triangles (T, 3, 3), their sRGB colours (T, 3), lines (K, 2, 3), their colours (K, 3))} of fills
    [(outline (N, 2), key)] (drawings.cut_fills): on the plane (origin, u, v), moved by `lift` (towards the viewer).
    scale: N of 1:N (a drafting pattern's mm on paper, so many mm on the building). (0.320) The outlines are of
    all elements at once, under the key None: round each material's parts joined (cut_joins.merged) — a line only
    where the material changes, none where two walls of one material meet. (0.428) Under None only the outline round
    all that is cut (drawn with the cut pen); the lines between materials inside it under SEAMS (the hatch pen)."""
    import shapely
    from . import cut_joins
    origin, u, v, lift = (np.asarray(a, dtype=float) for a in (origin, u, v, lift))
    groups = {}
    for (ring, key), owner in zip(fills, whose):
        groups.setdefault((owner, key), []).append(ring)
    out = {}
    paper = float(scale) / 1000.0                           # (m on the building a mm on paper)

    def to3d(xy):
        xy = np.asarray(xy, dtype=float)
        return origin + xy[..., :1] * u + xy[..., 1:2] * v + lift

    known = getattr(fills, "parts", None) or {}              # (0.320: each element's part, as joined)
    for (owner, key), rings in groups.items():
        layers = layers_of(key, own, gstyle)
        if not layers:
            continue
        area = known.get((owner, key))
        if area is None:
            area = drawing2d.region(rings)
        if area.is_empty:
            continue
        tris, tri_rgb, segs, seg_rgb = [], [], [], []
        x0, y0, x1, y1 = area.bounds
        for pattern, colour in layers:
            rgb = _rgb(colour)
            if pattern == core_patterns.SOLID:
                pieces = shapely.constrained_delaunay_triangles(area)
                for t in getattr(pieces, "geoms", ()):
                    corners = np.asarray(t.exterior.coords, dtype=float)[:3]
                    if len(corners) == 3:
                        tris.append(to3d(corners))
                        tri_rgb.append(rgb)
                continue
            if isinstance(pattern, tuple):
                lines, dots = core_patterns.families_segments(pattern, (x0, y0, x1, y1), paper)
            else:
                found = core_patterns.get(pattern)
                if found is None:
                    continue
                lines, dots = core_patterns.segments(pattern, (x0, y0, x1, y1), 1.0 if found.model else paper)
            if len(lines):
                for found in shapely.intersection(shapely.linestrings(lines), area):
                    for part in getattr(found, "geoms", [found]):
                        if part.geom_type != "LineString" or part.is_empty:
                            continue
                        c = np.asarray(part.coords, dtype=float)
                        if len(c) >= 2:
                            pairs = np.stack((c[:-1], c[1:]), axis=1)
                            segs.append(to3d(pairs))
                            seg_rgb += [rgb] * len(pairs)
            if len(dots):
                inside = dots[shapely.contains_xy(area, dots[:, 0], dots[:, 1])]
                if len(inside):
                    step = np.array((DOT * paper, 0.0))
                    segs.append(to3d(np.stack((inside, inside + step), axis=1)))
                    seg_rgb += [rgb] * len(inside)
        mine = out.setdefault(owner, ([], [], [], []))
        mine[0].extend(tris)
        mine[1].extend(tri_rgb)
        if segs:
            mine[2].append(np.concatenate(segs))
        mine[3].extend(seg_rgb)
    # (0.428) the outline round all that is cut — the cut pen —, apart from the seams between materials inside it —
    # the hatch pen —, as on paper (ui/pdf.py)
    regions = {key: region for key, region in cut_joins.merged(fills, whose).items() if layers_of(key, own, gstyle)}
    segs, seams = [], []

    def pairs(line):
        c = np.asarray(line.coords, dtype=float)
        return to3d(np.stack((c[:-1], c[1:]), axis=1)) if len(c) >= 2 else None

    if regions:
        from shapely.ops import unary_union
        outer = cut_joins.whole(regions.values()).boundary         # (0.442: the cracks between them closed)
        for part in _lines(outer):
            p = pairs(part)
            if p is not None:
                segs.append(p)
        if len(regions) > 1:                            # (a seam is two materials' edge: once, the lines joined)
            inner = unary_union([region.boundary for region in regions.values()]).difference(outer.buffer(1e-5))
            for part in _lines(inner) if not inner.is_empty else ():
                p = pairs(part)
                if p is not None:
                    seams.append(p)
    breaks = getattr(fills, "breaks", None)                  # (0.333: between elements unjoined by hand)
    if breaks is not None and len(breaks):
        segs.append(to3d(np.asarray(breaks, dtype=float)))
    if segs:
        segs = np.concatenate(segs)
        out[None] = ([], [], [segs], [_rgb(INK)] * len(segs))
    if seams:
        seams = np.concatenate(seams)
        out[SEAMS] = ([], [], [seams], [_rgb(INK)] * len(seams))
    return {owner: (np.array(t, dtype=float).reshape(-1, 3, 3), np.array(c, dtype=float).reshape(-1, 3),
                    np.concatenate(s) if s else np.zeros((0, 2, 3)), np.array(sc, dtype=float).reshape(-1, 3))
            for owner, (t, c, s, sc) in out.items()}
