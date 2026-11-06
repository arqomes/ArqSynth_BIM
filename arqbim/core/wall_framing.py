"""(0.437, the addon's «Steel Frame / Wood Frame») A light wall's frame, in the wall's own frame — x along it from its
start, y across it, z up from its base; metres —: its plates (the bottom one cut at the doors, the top one whole), its
studs at a spacing from its start, an end stud at each end, a jamb stud each side of every opening, a header over it,
a sill under a window, cripple studs over the header and under the sill where the studs would have been, and rows of
blocking between the studs. Each piece a box (lo, hi) inside the wall's core (y0..y1). Pure Python."""

from dataclasses import dataclass

KINDS = ("steel", "wood")
# stud: its width along the wall; plate: a plate's height; header: a header's height
DEFAULTS = {"steel": {"spacing": 0.60, "stud": 0.04, "plate": 0.04, "header": 0.15, "blocking": 1},
            "wood": {"spacing": 0.40, "stud": 0.045, "plate": 0.045, "header": 0.20, "blocking": 1}}
ROLES = ("plate", "stud", "jamb", "header", "sill", "cripple", "blocking")
MAX_BLOCKING = 4
MIN_PIECE = 0.03            # m: a piece shorter than this is left out


@dataclass(frozen=True)
class Piece:
    role: str
    lo: tuple
    hi: tuple

    @property
    def size(self):
        return tuple(b - a for a, b in zip(self.lo, self.hi))

    @property
    def length(self):
        """Its long side: up the wall for the studs, along it for the rest."""
        dx, _dy, dz = self.size
        return dz if self.role in ("stud", "jamb", "cripple") else dx

    @property
    def volume(self):
        dx, dy, dz = self.size
        return dx * dy * dz


def _runs(a, b, gaps):
    """The stretches of a..b left between the gaps [(g0, g1)]."""
    out, at = [], a
    for g0, g1 in sorted(gaps):
        if g0 > at + 1e-9:
            out.append((at, min(g0, b)))
        at = max(at, g1)
    if b > at + 1e-9:
        out.append((at, b))
    return [(p, q) for p, q in out if q - p >= MIN_PIECE]


def layout(length, height, y0, y1, openings=(), kind="steel", spacing=None, blocking=None):
    """The frame's pieces of a wall `length` × `height`, its core y0..y1, with these openings [(x0, x1, z0, z1)] (in
    its frame), of `kind` (steel / wood: its studs, plates and headers), its studs `spacing` apart (axis to axis,
    from its start), `blocking` rows of blocking."""
    d = DEFAULTS[kind if kind in DEFAULTS else "steel"]
    s = float(spacing) if spacing else d["spacing"]
    w, p, hh = d["stud"], d["plate"], d["header"]
    rows = d["blocking"] if blocking is None else max(0, min(MAX_BLOCKING, int(blocking)))
    L, H = float(length), float(height)
    if L < 2 * w or H < 2 * p + 0.1 or s < w + 0.01:
        return []
    ops = []
    for x0, x1, z0, z1 in openings:
        x0, x1, z0, z1 = max(0.0, x0), min(L, x1), max(0.0, z0), min(H, z1)
        if x1 - x0 > 0.01 and z1 - z0 > 0.01:
            ops.append((x0, x1, z0, z1))
    pieces = []

    def box(role, xa, xb, za, zb):
        if xb - xa >= MIN_PIECE * (0.5 if role in ("stud", "jamb", "cripple") else 1.0) and zb - za >= MIN_PIECE / 2:
            pieces.append(Piece(role, (xa, y0, za), (xb, y1, zb)))

    # the plates: the bottom one cut at the doors (the openings down to the floor), the top one whole
    for a, b in _runs(0.0, L, [(x0, x1) for x0, x1, z0, _z1 in ops if z0 <= p + 1e-6]):
        box("plate", a, b, 0.0, p)
    box("plate", 0.0, L, H - p, H)
    # the zone of each opening the studs keep clear of: from the outer face of its jambs
    zones = [(x0 - w, x1 + w) for x0, x1, _z0, _z1 in ops]

    def clear(xa, xb):
        return all(xb <= z0 + 1e-9 or xa >= z1 - 1e-9 for z0, z1 in zones)

    verticals = []                                    # (x0, x1) of the studs that go from plate to plate
    for xa in [0.0, L - w]:                           # (the end studs)
        if clear(xa, xa + w) and all(abs(xa - v[0]) > 1e-6 for v in verticals):
            verticals.append((xa, xa + w))
    k = 1
    while k * s + w / 2 < L - w - 1e-6:               # (the studs at the spacing, axis to axis from the start)
        xa = k * s - w / 2
        if clear(xa, xa + w) and xa > w - 1e-6:
            verticals.append((xa, xa + w))
        k += 1
    for x0, x1, _z0, _z1 in ops:                      # (a jamb each side of an opening)
        for xa in (x0 - w, x1):
            if 0.0 <= xa and xa + w <= L + 1e-9:
                verticals.append((xa, xa + w))
    verticals = sorted(set((round(a, 6), round(b, 6)) for a, b in verticals))
    for xa, xb in verticals:
        role = "jamb" if any(abs(xa - (x0 - w)) < 1e-6 or abs(xa - x1) < 1e-6 for x0, x1, _z0, _z1 in ops) \
            else "stud"
        box(role, xa, xb, p, H - p)
    # over and under each opening: its header, its sill, the cripples where the studs would have been
    for x0, x1, z0, z1 in ops:
        top = min(z1 + hh, H - p)
        box("header", max(0.0, x0 - w), min(L, x1 + w), z1, top)
        sill = z0 > p + 0.05
        if sill:
            box("sill", x0, x1, max(p, z0 - p), z0)
        k = 1
        while k * s - w / 2 < x1:
            xa = k * s - w / 2
            if xa >= x0 and xa + w <= x1:
                if H - p - top > 0.05:
                    box("cripple", xa, xa + w, top, H - p)
                if sill and z0 - p - p > 0.05:
                    box("cripple", xa, xa + w, p, z0 - p)
            k += 1
    # the blocking: rows at equal heights, between the studs, not across an opening
    for r in range(1, rows + 1):
        zc = H * r / (rows + 1)
        za, zb = zc - w / 2, zc + w / 2
        for (a0, a1), (b0, _b1) in zip(verticals, verticals[1:]):
            if b0 - a1 < MIN_PIECE:
                continue
            inside = any(a1 >= x0 - w - 1e-6 and b0 <= x1 + w + 1e-6 and zb > z0 - p and za < min(z1 + hh, H)
                         for x0, x1, z0, z1 in ops)
            if not inside:
                box("blocking", a1, b0, za, zb)
    return pieces


def summary(pieces):
    """{role: (count, total length m)} in ROLES' order."""
    out = {}
    for piece in pieces:
        n, total = out.get(piece.role, (0, 0.0))
        out[piece.role] = (n + 1, total + piece.length)
    return {r: out[r] for r in ROLES if r in out}
