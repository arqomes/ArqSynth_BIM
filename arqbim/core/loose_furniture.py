"""(0.440, the owner: «Sim, peças próprias») Loose furniture of the program's own: a catalogue of pieces — beds,
bedside tables, sofas, an armchair, a chair, tables, a desk, a bookcase, a TV unit, a plant in its pot —, each made from
its width, depth and height as boxes and cylinders of a material (wood, upholstery, a light fabric, steel, terracotta,
foliage), as the addon's loose library is placed (ripado_core-style: pure, no Blender) but without its third-party
files. The piece's own frame: x across its width (−w/2..w/2), y from its front (−d/2, the side one uses it from) to its
back (+d/2), z up from the floor. Pure Python."""

from dataclasses import dataclass

# a piece: (group, IFC predefined type, its ObjectType (pt, en), its name (pt, en), default (w, d, h))
PIECES = {
    "cama_casal": ("bedroom", "BED", ("Cama de casal", "Double bed"), (1.70, 2.10, 0.95)),
    "cama_solteiro": ("bedroom", "BED", ("Cama de solteiro", "Single bed"), (1.00, 2.05, 0.85)),
    "mesa_cabeceira": ("bedroom", "USERDEFINED", ("Mesa de cabeceira", "Bedside table"), (0.45, 0.40, 0.50)),
    "sofa_2": ("living", "SOFA", ("Sofá de 2 lugares", "Two-seat sofa"), (1.60, 0.90, 0.85)),
    "sofa_3": ("living", "SOFA", ("Sofá de 3 lugares", "Three-seat sofa"), (2.20, 0.90, 0.85)),
    "poltrona": ("living", "CHAIR", ("Poltrona", "Armchair"), (0.85, 0.85, 0.85)),
    "mesa_centro": ("living", "TABLE", ("Mesa de centro", "Coffee table"), (1.10, 0.60, 0.40)),
    "movel_tv": ("living", "USERDEFINED", ("Móvel de TV", "TV unit"), (1.80, 0.45, 0.50)),
    "mesa_jantar_4": ("dining", "TABLE", ("Mesa de jantar (4 lugares)", "Dining table (4 seats)"), (1.20, 0.80, 0.75)),
    "mesa_jantar_6": ("dining", "TABLE", ("Mesa de jantar (6 lugares)", "Dining table (6 seats)"), (1.80, 0.90, 0.75)),
    "cadeira": ("dining", "CHAIR", ("Cadeira", "Chair"), (0.45, 0.50, 0.85)),
    "secretaria": ("office", "DESK", ("Secretária", "Desk"), (1.20, 0.60, 0.75)),
    "estante": ("office", "SHELF", ("Estante", "Bookcase"), (0.80, 0.35, 1.80)),
    "planta": ("other", "USERDEFINED", ("Planta em vaso", "Potted plant"), (0.45, 0.45, 1.20)),
}
GROUPS = ("bedroom", "living", "dining", "office", "other")
LEAST, MOST = 0.15, 4.0                 # m: a piece's sizes, each


@dataclass(frozen=True)
class Part:
    material: str                       # a catalogue material's key
    box: tuple                          # (x0, y0, z0, x1, y1, z1)
    round: bool = False                 # a cylinder standing in the box (its diameter the smaller side)


def _legs(out, x0, y0, x1, y1, z0, z1, size, material):
    """Four legs `size` square at the corners of x0..x1 × y0..y1."""
    for x in (x0, x1 - size):
        for y in (y0, y1 - size):
            out.append(Part(material, (x, y, z0, x + size, y + size, z1)))


def _bed(w, d, h, pillows):
    a, b = w / 2, d / 2
    out = [Part("madeira", (-a, b - 0.06, 0.0, a, b, h)),                                  # (its headboard)
           Part("madeira", (-a + 0.02, -b, 0.08, a - 0.02, b - 0.06, 0.33))]               # (its frame)
    _legs(out, -a + 0.04, -b + 0.04, a - 0.04, b - 0.08, 0.0, 0.08, 0.06, "madeira")
    top = min(0.55, h - 0.05)
    out.append(Part("tecido_claro", (-a + 0.04, -b + 0.02, 0.33, a - 0.04, b - 0.08, top)))   # (its mattress)
    gap = 0.06
    width = (w - 0.08 - gap * (pillows + 1)) / pillows
    for k in range(pillows):
        x = -a + 0.04 + gap + k * (width + gap)
        out.append(Part("tecido_claro", (x, b - 0.50, top, x + width, b - 0.12, top + 0.12)))
    return out


def _seat(w, d, h, cushions):
    """A sofa or an armchair: its base, legs, arms, back and seat cushions."""
    a, b = w / 2, d / 2
    arm = min(0.16, w * 0.15)
    seat, back = 0.42, min(0.22, d * 0.25)
    out = [Part("tecido", (-a + arm, -b, 0.10, a - arm, b, seat)),                       # (its base)
           Part("tecido", (-a, -b, 0.10, -a + arm, b, min(0.62, h))),                    # (its arms)
           Part("tecido", (a - arm, -b, 0.10, a, b, min(0.62, h))),
           Part("tecido", (-a + arm, b - back, seat, a - arm, b, h))]                    # (its back)
    _legs(out, -a + 0.03, -b + 0.03, a - 0.03, b - 0.03, 0.0, 0.10, 0.05, "madeira")
    span = (w - 2 * arm) / cushions
    for k in range(cushions):
        x = -a + arm + k * span
        out.append(Part("tecido", (x + 0.01, -b + 0.02, seat, x + span - 0.01, b - back, seat + 0.12)))
    return out


def _table(w, d, h, top=0.03, leg=0.06, material="madeira"):
    a, b = w / 2, d / 2
    out = [Part(material, (-a, -b, h - top, a, b, h))]
    inset = min(0.05, w * 0.05)
    _legs(out, -a + inset, -b + inset, a - inset, b - inset, 0.0, h - top, leg, material)
    return out


def _chair(w, d, h):
    a, b = w / 2, d / 2
    seat = min(0.46, h * 0.55)
    out = [Part("madeira", (-a, -b, seat - 0.04, a, b, seat))]
    _legs(out, -a, -b, a, b, 0.0, seat - 0.04, 0.035, "madeira")
    out.append(Part("madeira", (-a, b - 0.035, seat, a, b, h)))                          # (its back)
    return out


def _desk(w, d, h):
    a, b = w / 2, d / 2
    return [Part("madeira", (-a, -b, h - 0.03, a, b, h)),
            Part("madeira", (-a, -b + 0.02, 0.0, -a + 0.025, b, h - 0.03)),               # (its sides)
            Part("madeira", (a - 0.025, -b + 0.02, 0.0, a, b, h - 0.03)),
            Part("madeira", (-a + 0.025, b - 0.04, h * 0.35, a - 0.025, b - 0.02, h - 0.03))]   # (its modesty panel)


def _bookcase(w, d, h):
    a, b, t = w / 2, d / 2, 0.02
    out = [Part("madeira", (-a, -b, 0.0, -a + t, b, h)), Part("madeira", (a - t, -b, 0.0, a, b, h)),
           Part("madeira", (-a + t, -b, h - t, a - t, b, h)), Part("madeira", (-a + t, -b, 0.0, a - t, b, 0.06)),
           Part("madeira", (-a + t, b - 0.01, 0.06, a - t, b, h - t))]                    # (its back)
    shelves = max(1, int(round(h / 0.35)) - 1)
    for k in range(1, shelves + 1):
        z = 0.06 + k * (h - t - 0.06) / (shelves + 1)
        out.append(Part("madeira", (-a + t, -b + 0.01, z - t / 2, a - t, b - 0.01, z + t / 2)))
    return out


def _tv_unit(w, d, h):
    a, b = w / 2, d / 2
    return [Part("madeira", (-a + 0.02, -b + 0.02, 0.0, a - 0.02, b - 0.02, 0.08)),       # (its plinth)
            Part("lacado_branco", (-a, -b, 0.08, a, b, h - 0.02)),
            Part("madeira", (-a, -b, h - 0.02, a, b, h))]


def _plant(w, d, h):
    r = min(w, d) / 2
    pot = min(0.35, h * 0.3)
    return [Part("telha", (-r * 0.7, -r * 0.7, 0.0, r * 0.7, r * 0.7, pot), round=True),
            Part("folhagem", (-r, -r, pot, r, r, pot + (h - pot) * 0.65), round=True),
            Part("folhagem", (-r * 0.6, -r * 0.6, pot + (h - pot) * 0.65, r * 0.6, r * 0.6, h), round=True)]


def parts(key, width=None, depth=None, height=None):
    """The parts of a piece (its key) of these sizes (None: its own)."""
    _group, _ptype, _names, (w0, d0, h0) = PIECES[key]
    w, d, h = (float(v) if v else v0 for v, v0 in ((width, w0), (depth, d0), (height, h0)))
    if key.startswith("cama"):
        return _bed(w, d, h, 2 if w >= 1.30 else 1)
    if key == "mesa_cabeceira":
        return [Part("madeira", (-w / 2, -d / 2, 0.0, w / 2, d / 2, h - 0.02)),
                Part("madeira", (-w / 2 - 0.01, -d / 2 - 0.01, h - 0.02, w / 2 + 0.01, d / 2 + 0.01, h))]
    if key.startswith("sofa"):
        return _seat(w, d, h, 3 if key == "sofa_3" else 2)
    if key == "poltrona":
        return _seat(w, d, h, 1)
    if key == "mesa_centro":
        return _table(w, d, h, top=0.04, leg=0.05)
    if key.startswith("mesa_jantar"):
        return _table(w, d, h)
    if key == "cadeira":
        return _chair(w, d, h)
    if key == "secretaria":
        return _desk(w, d, h)
    if key == "estante":
        return _bookcase(w, d, h)
    if key == "movel_tv":
        return _tv_unit(w, d, h)
    return _plant(w, d, h)


def defaults(key):
    return PIECES[key][3]


def check(key, width, depth, height):
    """None, or why these sizes will not do."""
    if key not in PIECES:
        return "loose_bad"
    if not all(LEAST - 1e-9 <= float(v) <= MOST + 1e-9 for v in (width, depth, height)):
        return "loose_size"
    return None
