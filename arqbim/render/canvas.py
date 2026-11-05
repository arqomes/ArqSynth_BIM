"""(0.341) The views' canvas — light, as it always was, or dark (Visualizar ▸ Tema ▸ Vistas escuras: the owner's
«fundo escuro nas vistas», 2026-11-01), as Revit's canvas theme, apart from the interface's.

On the dark canvas the background is dark and what is grey turns over (ink): black lines, the cut's fill, the
dimensions' and the texts' ink come light; white and grey faces (the categories' colours, a sketch's, the hidden-line
style's white) come dark, so that the lines are still seen on them. A colour (a material's in a realistic style, glass,
brick, a system's, a phase's, the selection's blue, the axes') stays as it is. What is exported (PDF, DXF, the view's
image on white) is drawn on the light canvas: paper. Pure colour arithmetic — the viewport and the batches ask."""

import functools

import pygfx as gfx

DARK = False
BACKGROUNDS = {False: ("#f3f3f0", "#cfdbe6"),        # light at the bottom, a pale sky at the top
               True: ("#1b1e22", "#2a3139")}         # (dark: the interface's dark greys, a hint of blue at the top)
NEUTRAL = 0.15                                       # a colour whose channels differ less than this: a grey


def set_dark(on):
    """The canvas dark (True) or light from now on; True if it changed."""
    global DARK
    changed = bool(on) != DARK
    DARK = bool(on)
    return changed


TINT = None                 # (0.374) the drawing area's colour of the interface's palette (its study's «canvas»)


def set_tint(colour):
    """(0.374) The light canvas in this colour ("#rrggbb", lighter towards the top) — None: the program's own."""
    global TINT
    TINT = colour or None


def _lighter(colour, f=0.3):
    c = colour.lstrip("#")
    r, g, b = (int(c[k:k + 2], 16) for k in (0, 2, 4))
    return "#{:02x}{:02x}{:02x}".format(*(round(v + (255 - v) * f) for v in (r, g, b)))


def background():
    """The view's background: (bottom, top) — (0.374) the palette's drawing area, when it has one, on a light
    canvas."""
    if TINT and not DARK:
        return _lighter(TINT, 0.35), _lighter(TINT, 0.10)
    return BACKGROUNDS[DARK]


GRID_ON_LIGHT = 0.14        # (0.393) the ground grid on a palette's light drawing area: this much darker…
GRID_ON_DARK = 0.08         # …and on a dark one this much lighter — softer (the owner: «muito forte no tema escuro»)


def ground_grid(colour):
    """(0.393) The ground grid's lines on the canvas in use: `colour` on the program's own light canvas (as always);
    on the dark canvas or a palette's drawing area, made from that background's colour where the ground is (its
    bottom) — a little darker on a light one, a little lighter on a dark one (a light grey made for white was hard
    light lines on the dark ones)."""
    if not DARK and not TINT:
        return colour
    low = gfx.Color(background()[0])
    rgb = (low.r, low.g, low.b)
    shift = GRID_ON_DARK if (max(rgb) + min(rgb)) / 2.0 < 0.5 else -GRID_ON_LIGHT
    return gfx.Color(*(min(1.0, max(0.0, c + shift)) for c in rgb)).hex


LIFT = 0.45, 0.62           # a colour darker than the first: made as light as the second (seen on the dark ground)


@functools.lru_cache(maxsize=8192)
def _turned(r, g, b):
    """A grey turned over (its lightness L → 0.92 − 0.8 L: black → light, white → nearly the background); a dark
    colour lightened (the grid's blue, a CAD drawing's, the contours' brown), its hue kept; a colour as it is."""
    high, low = max(r, g, b), min(r, g, b)
    light = (high + low) / 2.0
    if high - low >= NEUTRAL:
        if light >= LIFT[0]:
            return r, g, b
        shift = LIFT[1] - light
    else:
        shift = 0.92 - 0.8 * light - light
    return tuple(min(1.0, max(0.0, c + shift)) for c in (r, g, b))


def ink_array(rgb):
    """(N, 3) sRGB colours of 0–1, their greys turned over as ink() turns one (always: the caller says when)."""
    import numpy as np
    c = np.asarray(rgb, dtype=np.float64).reshape(-1, 3)
    high, low = c.max(axis=1), c.min(axis=1)
    light = (high + low) / 2.0
    grey = (high - low) < NEUTRAL
    shift = np.where(grey, 0.92 - 0.8 * light - light, np.where(light < LIFT[0], LIFT[1] - light, 0.0))
    return np.clip(c + shift[:, None], 0.0, 1.0)


def ink(colour):
    """A colour of the light canvas as the canvas in use draws it — the same kind it was given: "#rrggbb" (or any
    name pygfx knows) → "#rrggbb[aa]"; an (r, g, b[, a]) of 0–1 → the same. None as None."""
    if not DARK or colour is None:
        return colour
    if isinstance(colour, str):
        c = gfx.Color(colour)
        r, g, b = _turned(round(c.r, 4), round(c.g, 4), round(c.b, 4))
        return gfx.Color(r, g, b, c.a).hex if c.a < 1.0 else gfx.Color(r, g, b).hex
    values = tuple(float(v) for v in colour)
    if len(values) not in (3, 4):
        return colour
    r, g, b = _turned(round(values[0], 4), round(values[1], 4), round(values[2], 4))
    return (r, g, b) + values[3:]
