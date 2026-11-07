"""A drawing as SVG (0.233, Phase 9, step 5: the calculation report with its drawings) — model.drawings.Drawing's
lines, its annotations (lines and polylines with their pens, filled regions, texts) and its dimensions, at a scale,
in millimetres of paper; no Qt: what a page of HTML takes in as it is. Its texts and pens at their paper sizes."""

import html

import numpy as np

LINE_PEN = 0.35                 # mm: the drawing's own lines (the concrete's outlines)
DIM_PEN = 0.13                  # (0.398: the dimensions as their type says — core/dim_layout)
MARGIN = 6.0                    # mm round it


def svg(drawing, scale=50):
    """The SVG (a string) of a drawing at 1:scale, or "" when it has nothing drawn."""
    found = drawing.bounds()
    if found is None:
        return ""
    lo, hi = (np.asarray(p, dtype=float) for p in found)
    k = 1000.0 / scale                                  # (m in the drawing → mm on paper)
    w, h = (hi - lo) * k + 2 * MARGIN

    def at(p):
        p = np.asarray(p, dtype=float)
        return (p[0] - lo[0]) * k + MARGIN, (hi[1] - p[1]) * k + MARGIN

    def path(points, closed=False):
        pts = [at(p) for p in points]
        return "M" + " L".join("{:.2f} {:.2f}".format(x, y) for x, y in pts) + (" Z" if closed else "")

    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="{:.1f}mm" height="{:.1f}mm" viewBox="0 0 {:.2f} {:.2f}" '
           'font-family="Segoe UI, Arial, sans-serif">'.format(w, h, w, h)]
    for a, b in np.asarray(drawing.lines, dtype=float).reshape(-1, 2, 2):
        out.append('<path d="{}" stroke="#000" stroke-width="{}" fill="none"/>'.format(path((a, b)), LINE_PEN))
    for ann in drawing.annotations:
        kind = ann[0]
        if kind == "text":
            x, y = at(ann[4])
            out.append('<text x="{:.2f}" y="{:.2f}" font-size="{:.2f}">{}</text>'.format(
                x, y, float(ann[5]), html.escape(str(ann[3]))))
        elif kind in ("polyline", "line"):
            pen = ann[7] if len(ann) > 7 and ann[7] else LINE_PEN
            for pts, closed in ann[1]:
                out.append('<path d="{}" stroke="#000" stroke-width="{}" fill="none"/>'.format(
                    path(pts, closed), pen))
        elif kind == "region":
            fill = "#fff" if ann[2] == "mask" else "#000"       # (0.450: a mask white, hiding what is under it)
            for pts, _closed in ann[1]:
                out.append('<path d="{}" fill="{}" stroke="none"/>'.format(path(pts, True), fill))
    if getattr(drawing, "dims", ()):                    # (0.398: laid out by core/dim_layout, as on paper)
        from ..core import dim_layout
        layout = dim_layout.of_drawing(drawing.dims, getattr(drawing, "dim_style", None) or {}, scale / 1000.0,
                                       DIM_PEN)
        out += layout_svg(layout, at, k)
    out.append("</svg>")
    return "".join(out)


def layout_svg(layout, at, k, paper="#ffffff"):
    """(0.398) A core.dim_layout.Layout as SVG elements: `at` the drawing's metres → paper mm (y down), `k` paper mm per
    metre of the model."""
    from ..core.dim_layout import DEFAULT_FONT
    parts = []
    for a, b, pen, colour, _owner in layout.lines:
        (x0, y0), (x1, y1) = at(a), at(b)
        parts.append('<path d="M{:.2f} {:.2f} L{:.2f} {:.2f}" stroke="{}" stroke-width="{:.3f}" fill="none"/>'.format(
            x0, y0, x1, y1, colour, float(pen)))
    for pts, colour, _owner in layout.fills:
        parts.append('<path d="M{}Z" fill="{}" stroke="none"/>'.format(
            " L".join("{:.2f} {:.2f}".format(*at(p)) for p in pts), colour))
    for corners, _owner in layout.backs:
        parts.append('<path d="M{}Z" fill="{}" stroke="none"/>'.format(
            " L".join("{:.2f} {:.2f}".format(*at(p)) for p in corners), paper))
    for item in layout.texts:
        x, y = at(item.at)
        parts.append('<text x="0" y="0" font-family="{}" font-size="{:.2f}"{}{} fill="{}" text-anchor="middle" '
                     'dominant-baseline="central" transform="translate({:.2f} {:.2f}) rotate({:.1f}) scale({:.3f} 1)">'
                     '{}</text>'.format(html.escape(item.font or DEFAULT_FONT), item.height * k,
                                        ' font-weight="bold"' if item.bold else "",
                                        ' font-style="italic"' if item.italic else "", item.colour, x, y,
                                        -item.angle, float(item.width or 1.0), html.escape(item.text)))
    return parts
