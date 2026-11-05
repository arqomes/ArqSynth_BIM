"""Stairs (0.114): straight, L (a quarter turn at a landing) and U (a half turn). Pure geometry.

The rise is split into equal risers no higher than MAX_RISER; the last riser lands on the floor above, so a
flight of n risers has n − 1 treads (its top is the floor or the landing). Each flight is drawn by its side — the
risers and treads, and the waist (the slab carrying them) under the line of their inner corners — to be extruded
across its width; a landing is a plate as deep as the stair is wide, as thick as the waist, one slab with the
flights that meet it (0.256). Everything in the stair's own frame: its foot (the
middle of the first riser, at the floor) at 0, 0, 0, its first flight going along +x."""

import math

FORMS = ("straight", "l", "u", "v", "spiral")
TURNS = ("left", "right")
MAX_RISER = 0.18            # m
GAP = 0.10                  # m: between the two flights of a U (a V: none, side by side)
COLUMN = 0.10               # m: a spiral stair's column's radius
TREAD = 0.06                # m: a spiral stair's treads' thickness (open risers)
BEARING = 0.10              # m: a flight's top resting on the floor or landing it reaches, past its last riser
BLONDEL = 0.63              # m: 2 risers + 1 tread, a comfortable step


def risers(rise, max_riser=MAX_RISER):
    """(how many risers, their height) for a rise."""
    n = max(2, int(math.ceil(rise / max_riser - 1e-9)))
    return n, rise / n


def flight_side(n, h, g, waist, z0=0.0, below=0.0, ahead=0.0, behind=0.0):
    """The side of a flight of n risers h high and treads g deep from its first riser (x = 0) at the level z0:
    [(x, z)] counter-clockwise — the steps, then back down the waist: the slab that carries them, its underside
    parallel to the line of the steps' inner corners and `waist` thick square to it (0.256: measured to the inner
    corner of riser and tread, as IFC's WaistThickness — before, to the nosings' line, which left no slab at all
    under a 15 cm waist and 17,5 cm risers).
    Its foot on the floor (below = 0) or, from a landing, down to the landing's underside (`below` under z0) —
    (0.257) with that landing made with it, `behind` deep behind its first riser. Its top: BEARING past its last
    riser, cut upright (resting on the floor it reaches); or (0.257) with the landing it reaches made with it,
    `ahead` deep past its last riser, `waist` thick, its underside meeting the landing's: one piece, no seam."""
    head = [(0.0, z0)]
    if behind > 0:
        head = [(-behind, z0 - below), (-behind, z0), (0.0, z0)]
    pts = list(head)
    for k in range(n):
        pts += [(k * g, z0 + (k + 1) * h)]
        if k < n - 1:
            pts += [((k + 1) * g, z0 + (k + 1) * h)]
    slope = h / g
    drop = waist * math.sqrt(1 + slope * slope)          # (the waist measured upright)
    top = z0 + n * h
    under = lambda x: z0 + slope * x - drop              # noqa: E731  (the underside)
    if ahead > 0:
        end = (n - 1) * g + ahead                        # (the landing's far edge)
        pts.append((end, top))
        if under(end) > top - waist:                     # (the underside rises to the landing's within it)
            pts += [(end, top - waist), ((top - waist - z0 + drop) / slope, top - waist)]
        else:                                            # (a landing too short for the underside to meet it)
            pts.append((end, under(end)))
    else:
        top_x = (n - 1) * g + BEARING                    # (its top rests on the floor it reaches)
        pts.append((top_x, top))
        pts.append((top_x, min(top - 0.02, under(top_x))))
    x_low = (drop - below) / slope                       # (where the underside meets the floor / the landing's)
    if x_low > 0:
        pts.append((x_low, z0 - below))
        if below > 0 and behind <= 0:
            pts.append((0.0, z0 - below))
    else:
        pts.append((0.0, z0 - drop))
        if behind > 0:                                   # (a landing thicker than the waist: down its front)
            pts.append((0.0, z0 - below))
    out = []                                             # (counter-clockwise in x-z, no repeats)
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 1e-9:
            out.append(p)
    area = sum(out[k][0] * out[(k + 1) % len(out)][1] - out[(k + 1) % len(out)][0] * out[k][1]
               for k in range(len(out))) / 2
    return out if area > 0 else out[::-1]


def layout(form, rise, width, going, turn="left", max_riser=MAX_RISER):
    """The pieces of a stair in its own frame: [("flight", (x, y) of its first riser's middle, (dx, dy) its way,
    risers, riser height, z of its foot) | ("landing", [(x, y)] its plan, z of its top)]."""
    n, h = risers(rise, max_riser)
    g = going
    side = 1.0 if turn == "left" else -1.0
    if form == "spiral":                                 # (0.116) wedges round a column
        return spiral(rise, width, going, turn, max_riser)
    if form == "straight" or n < 4:
        return [("flight", (0.0, 0.0), (1.0, 0.0), n, h, 0.0)]
    n1 = n // 2
    n2 = n - n1
    z1 = n1 * h
    x1 = (n1 - 1) * g                                    # (the landing starts at the first flight's last riser)
    pieces = [("flight", (0.0, 0.0), (1.0, 0.0), n1, h, 0.0)]
    if form == "l":
        landing = [(x1, -width / 2), (x1 + width, -width / 2), (x1 + width, width / 2), (x1, width / 2)]
        pieces.append(("landing", landing, z1))
        pieces.append(("flight", (x1 + width / 2, side * width / 2), (0.0, side), n2, h, z1))
    else:
        far = side * (width + (0.0 if form == "v" else GAP))
        ys = sorted((-side * width / 2, far + side * width / 2))
        landing = [(x1, ys[0]), (x1 + width, ys[0]), (x1 + width, ys[1]), (x1, ys[1])]
        pieces.append(("landing", landing, z1))
        pieces.append(("flight", (x1, far), (-1.0, 0.0), n2, h, z1))
    return pieces


def spiral(rise, width, going, turn="left", max_riser=MAX_RISER):
    """A spiral stair (0.116) in its own frame: its foot (the middle of its first riser, on the walking line) at
    0, 0, going along +x round a centre on its left (a left turn) or right: [("column", centre, radius, height),
    ("wedge", centre, inner, outer, from angle, to angle, z of its top) …] — the treads n − 1 wedges, each
    `going` along the walking line (the middle of the treads)."""
    n, h = risers(rise, max_riser)
    s = 1.0 if turn == "left" else -1.0
    inner, outer = COLUMN, COLUMN + width
    walk = (inner + outer) / 2
    centre = (0.0, s * walk)
    step = going / walk                                  # (each tread's angle)
    start = math.atan2(-s * walk, 0.0)                   # (the foot seen from the centre)
    pieces = [("column", centre, inner, rise)]
    for k in range(n - 1):
        a0 = start + s * k * step
        pieces.append(("wedge", centre, inner, outer, a0, a0 + s * step, (k + 1) * h))
    return pieces


def wedge_ring(centre, inner, outer, a0, a1, segments=8):
    """A wedge's plan [(x, y)] (its arcs as points: the previews, the plans)."""
    cx, cy = centre
    outer_pts = [(cx + outer * math.cos(a0 + (a1 - a0) * k / segments),
                  cy + outer * math.sin(a0 + (a1 - a0) * k / segments)) for k in range(segments + 1)]
    inner_pts = [(cx + inner * math.cos(a1 + (a0 - a1) * k / segments),
                  cy + inner * math.sin(a1 + (a0 - a1) * k / segments)) for k in range(segments + 1)]
    return outer_pts + inner_pts


def footprint(pieces, width, going):
    """Plan polygons [(x, y)] of the pieces (the previews, the plans)."""
    out = []
    for piece in pieces:
        if piece[0] == "landing":
            out.append(list(piece[1]))
            continue
        if piece[0] == "column":
            (cx, cy), r, _h = piece[1], piece[2], piece[3]
            out.append([(cx + r * math.cos(2 * math.pi * k / 16), cy + r * math.sin(2 * math.pi * k / 16))
                        for k in range(16)])
            continue
        if piece[0] == "wedge":
            _kind, centre, inner, outer, a0, a1, _z = piece
            out.append(wedge_ring(centre, inner, outer, a0, a1))
            continue
        _kind, (ox, oy), (dx, dy), n, _h, _z = piece
        lx, ly = -dy, dx
        length = (n - 1) * going + BEARING
        w = width / 2
        out.append([(ox + lx * w, oy + ly * w), (ox - lx * w, oy - ly * w),
                    (ox - lx * w + dx * length, oy - ly * w + dy * length),
                    (ox + lx * w + dx * length, oy + ly * w + dy * length)])
    return out


RAIL_INSET = 0.05           # m: a stair's railing in from its edge


def railing_sides(form, rise, width, going, turn="left", max_riser=MAX_RISER):
    """(0.261) The paths of a stair's railings, one each side, all the way up — along the line of the nosings on the
    flights, level along the landing between them (round its outer edges on the outside; on the inside, an L's
    corner, a U's or a V's turn round the well one tread past the last riser): [[(x, y, z)…], …] in the stair's
    own frame. A straight stair: its two sides. (A spiral stair: see the railing module.)"""
    n, h = risers(rise, max_riser)
    g, e = going, width / 2 - RAIL_INSET
    if form in ("straight", "spiral") or n < 4:
        return [[(0.0, s * e, h), ((n - 1) * g, s * e, n * h)] for s in (1.0, -1.0)]
    n1, n2 = n // 2, n - n // 2
    x1, z1 = (n1 - 1) * g, n1 * h
    sigma = 1.0 if turn == "left" else -1.0
    top = z1 + n2 * h
    if form == "l":
        inner_x, outer_x = x1 + width / 2 - e, x1 + width / 2 + e
        foot_y = sigma * width / 2

        def up(x, t):                                    # (flight 2's side at t along it from its foot)
            return (x, foot_y + sigma * t, z1 + h + t * h / g)

        corner_t = sigma * (sigma * e - foot_y)          # (the inner corner along flight 2)
        inner = [(0.0, sigma * e, h), (x1, sigma * e, z1),
                 (inner_x, sigma * e, max(z1, z1 + h + corner_t * h / g)), up(inner_x, (n2 - 1) * g)]
        outer = [(0.0, -sigma * e, h), (x1, -sigma * e, z1), (outer_x, -sigma * e, z1), up(outer_x, -g)[:2] + (z1,),
                 up(outer_x, (n2 - 1) * g)]
        return [inner, outer]
    far = sigma * (width + (0.0 if form == "v" else GAP))
    end_x = x1 - (n2 - 1) * g                            # (flight 2's last nosing, going back along -x)
    inner = [(0.0, sigma * e, h), (x1, sigma * e, z1), (x1 + g, sigma * e, z1), (x1 + g, far - sigma * e, z1),
             (end_x, far - sigma * e, top)]
    edge = x1 + width - RAIL_INSET
    outer = [(0.0, -sigma * e, h), (x1, -sigma * e, z1), (edge, -sigma * e, z1), (edge, far + sigma * e, z1),
             (x1 + g, far + sigma * e, z1), (end_x, far + sigma * e, top)]
    return [inner, outer]


def treads(form, rise, max_riser=MAX_RISER):
    """How many treads (the landing not counted)."""
    n, _h = risers(rise, max_riser)
    landings = 0 if form in ("straight", "spiral") or n < 4 else 1
    return n - 1 - landings
