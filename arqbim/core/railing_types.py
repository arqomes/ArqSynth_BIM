"""Railing types (0.258), as Revit's: a railing is drawn along a path, and its type says what it is made of —
its top rail, its posts (with or without a base plate), what fills it between them (upright bars, horizontal rails
or cables, glass held by clamps, glass set in a base channel, a sheet, a mesh, bars in a zigzag, nothing), a bottom
rail, a handrail on brackets beside it — each part's size and material. Pure geometry: `parts` gives a railing's
pieces in its own frame, ready to be made into IFC solids.

Sizes in metres. A type is kept in the IFC as an IfcRailingType with its fields in ArqSynth_Guarda (to_props /
from_props); the program's presets (PRESETS) are made in a project the first time they are used."""

import dataclasses
import math
from dataclasses import dataclass

import numpy as np

INFILLS = ("bars", "rails", "cables", "glass", "glass_channel", "panel", "mesh", "zigzag", "none")
SHAPES = ("square", "round", "flat")          # a bar's or a post's section (flat: wider along the railing)
TOP_SHAPES = ("rect", "round", "none")
PLATES = ("none", "square", "round")
HAND_SIDES = ("left", "right", "both")        # the handrail: on the left of the path as drawn, the right, both
FLOOR_GAP = 0.05             # m: the clear gap under a glass or a sheet held between posts
CLAMP = (0.05, 0.02, 0.04)   # m: a glass clamp (up, across, along)
BRACKET = 0.012              # m: a handrail bracket's bar (Ø)
GLASS_JOINT = 0.005          # m: between the glass panes in a base channel
# (0.282) DL 163/2006 (Portugal's accessibility rules), annex 2.4.9 2) — a stair's handrails "devem prolongar-se pelo
# menos 0,3 m para além do último degrau do lanço" at its top, level; 3) at its foot by one going, keeping its slope;
# 2.5.8 1) a ramp's, at least 0,3 m at its foot and top
TOP_EXTENSION = 0.30


@dataclass(frozen=True)
class RailingType:
    key: str
    name_pt: str
    name_en: str
    height: float = 1.00        # the usual height of its top over the floor (each railing may have its own)
    # its top rail
    top: str = "rect"           # TOP_SHAPES
    top_w: float = 0.05         # its width (round: its Ø)
    top_h: float = 0.04         # its height (rect)
    top_mat: str = "aco"
    # its posts
    post: str = "square"        # SHAPES or "none"
    post_w: float = 0.04        # along the railing (round: Ø)
    post_d: float = 0.04        # across it
    spacing: float = 1.20       # the most between two posts (a glass channel: between two panes)
    plate: str = "none"         # PLATES: a base plate under each post
    plate_w: float = 0.12
    plate_t: float = 0.01
    post_mat: str = "aco"
    # what fills it
    infill: str = "bars"        # INFILLS
    bar: str = "square"         # SHAPES: bars, rails, the mesh's frame
    bar_w: float = 0.02         # along the railing (round: Ø); a rail's or cable's Ø / height
    bar_d: float = 0.02         # across it
    gap: float = 0.10           # the most clear gap between bars, rails, cables; a zigzag's pitch; a mesh's cell
    count: int = 0              # rails, cables: how many (0: as many as the gap asks)
    sheet_t: float = 0.012      # a glass's or a sheet's thickness
    infill_mat: str = "aco"
    # a bottom rail
    bottom: bool = True
    bottom_z: float = 0.05      # its underside over the floor
    # a handrail on brackets, beside it
    hand: bool = False
    hand_side: str = "left"     # HAND_SIDES
    hand_shape: str = "round"   # "round" | "rect"
    hand_w: float = 0.042       # Ø (round) or width
    hand_z: float = 0.90        # its top over the floor
    hand_off: float = 0.08      # its axis from the railing's line
    hand_mat: str = "madeira"
    # glass in a base channel
    shoe_w: float = 0.07
    shoe_h: float = 0.11

    @property
    def name(self):
        return self.name_pt

    def label(self, lang="pt"):
        return self.name_pt if lang == "pt" else self.name_en

    @property
    def has_posts(self):
        return self.post != "none" and self.infill != "glass_channel"


PRESETS = {t.key: t for t in (
    RailingType("barras", "Barras verticais", "Upright bars"),
    RailingType("barras_redondas", "Barras redondas, corrimão redondo", "Round bars, round rail", top="round",
                top_w=0.05, post="round", post_w=0.05, post_d=0.05, bar="round", bar_w=0.016, bar_d=0.016,
                plate="round", plate_w=0.10, post_mat="inox", top_mat="inox", infill_mat="inox"),
    RailingType("travessas", "Travessas horizontais", "Horizontal rails", infill="rails", bar="square", bar_w=0.03,
                bar_d=0.03, gap=0.30, bottom=False, post_w=0.05, post_d=0.05, top_w=0.08, top_h=0.04,
                post_mat="aco_preto", top_mat="aco_preto", infill_mat="aco_preto"),
    RailingType("cabos", "Cabos de aço", "Steel cables", infill="cables", bar="round", bar_w=0.005, bar_d=0.005,
                gap=0.075, bottom=False, top_w=0.09, top_h=0.04, post_w=0.05, post_d=0.05, plate="square",
                plate_w=0.14, top_mat="madeira", post_mat="inox", infill_mat="inox"),
    RailingType("vidro_grampos", "Vidro com grampos", "Glass with clamps", infill="glass", top="round",
                top_w=0.042, post="round", post_w=0.042, post_d=0.042, plate="round", plate_w=0.10, bottom=False,
                sheet_t=0.010, top_mat="inox", post_mat="inox", infill_mat="vidro"),
    RailingType("vidro_perfil", "Vidro encastrado em perfil", "Glass in a base channel", infill="glass_channel",
                post="none", top="rect", top_w=0.03, top_h=0.025, spacing=1.50, bottom=False, sheet_t=0.017,
                top_mat="aluminio", post_mat="aluminio", infill_mat="vidro"),
    RailingType("chapa", "Chapa cheia", "Solid sheet", infill="panel", bottom=False, sheet_t=0.006,
                post_w=0.05, post_d=0.05, top_w=0.06, top_h=0.04, post_mat="aco_preto", top_mat="aco_preto",
                infill_mat="aco_preto"),
    RailingType("malha", "Malha com corrimão de madeira", "Mesh with a wooden rail", infill="mesh", bar="flat",
                bar_w=0.03, bar_d=0.008, gap=0.05, bottom=False, top_w=0.07, top_h=0.05, post_w=0.05, post_d=0.03,
                top_mat="madeira", post_mat="aco_preto", infill_mat="aco_preto"),
    RailingType("ziguezague", "Barras em ziguezague", "Zigzag bars", infill="zigzag", bar="round", bar_w=0.012,
                bar_d=0.012, gap=0.16, top="rect", top_w=0.03, top_h=0.03, post="flat", post_w=0.04, post_d=0.01,
                spacing=3.0, bottom=True, top_mat="aco_preto", post_mat="aco_preto", infill_mat="aco_preto"),
    RailingType("corrimao", "Corrimão de parede", "Wall handrail", infill="none", top="none", post="none",
                bottom=False, hand=True, hand_off=0.0, height=0.90, hand_z=0.90),
)}
DEFAULT = "barras"
OLD_STYLES = {"bars": "barras", "glass": "vidro_grampos", "rails": "travessas"}      # (0.115's styles)
FIELDS = [f.name for f in dataclasses.fields(RailingType) if f.name not in ("key", "name_pt", "name_en")]


def to_props(rt):
    """Its fields as IFC properties (ArqSynth_Guarda)."""
    out = {"Chave": rt.key, "NomeEN": rt.name_en}
    for name in FIELDS:
        out[name] = getattr(rt, name)
    return out


def from_props(name, props, fallback=None):
    """A type read back from its properties (unknown or wrong ones: the fallback's / the defaults)."""
    base = fallback or PRESETS[DEFAULT]
    values = {}
    for f in dataclasses.fields(RailingType):
        if f.name in ("key", "name_pt", "name_en") or f.name not in props:
            continue
        v = props[f.name]
        try:
            values[f.name] = type(getattr(base, f.name))(v)
        except (TypeError, ValueError):
            continue
    return dataclasses.replace(base, key=str(props.get("Chave") or base.key), name_pt=name,
                               name_en=str(props.get("NomeEN") or name), **values)


def problem(rt):
    """What makes a type unusable, or None (a refusal key)."""
    if rt.infill not in INFILLS or rt.top not in TOP_SHAPES or rt.post not in SHAPES + ("none",) or \
            rt.plate not in PLATES or rt.hand_side not in HAND_SIDES or rt.bar not in SHAPES:
        return "not_editable"
    if not 0.3 <= rt.height <= 3.0 or rt.spacing < 0.3 or rt.gap < 0.004:
        return "railing_height" if not 0.3 <= rt.height <= 3.0 else "too_small"
    for v in (rt.top_w, rt.post_w, rt.post_d, rt.bar_w, rt.bar_d, rt.sheet_t, rt.hand_w):
        if not 0.002 <= v <= 0.5:
            return "too_small"
    return None


# ---------------------------------------------------------------- geometry

def _horizontal(d):
    h = np.array((d[0], d[1], 0.0))
    n = np.linalg.norm(h)
    return h / n if n > 1e-12 else np.array((1.0, 0.0, 0.0))


def parts(points, rt, height=None, closed=False, extend=(0.0, 0.0)):
    """A railing's pieces along `points` ([(x, y, z)…]: level or sloping; its own frame), `height` its top over
    them (else the type's): [("bar", a, b, shape, w, d, ref, material) — a straight bar from a to b, its section
    w × d (round: Ø w), w along `ref`; ("pane", a, b, z0, z1, t, material) — a flat piece upright on the line a -> b
    from z0 to z1 over it, t thick; ("plate", centre, shape, w, t, material) — a base plate on the floor]. (0.282)
    extend: (at its start, at its end) how far its handrail goes on past them (see _extensions)."""
    h = float(rt.height if height is None else height)
    pts = [np.asarray(q, dtype=float) for q in points]
    if closed and len(pts) > 2:
        pts.append(pts[0])
    up = np.array((0.0, 0.0, 1.0))
    out = []
    segments = [(a, b) for a, b in zip(pts, pts[1:]) if np.linalg.norm((b - a)[:2]) > 1e-6]
    top_size = 0.0 if rt.top == "none" else (rt.top_w if rt.top == "round" else rt.top_h)
    under_top = h - top_size                                  # (the top rail's underside over the line)
    bottom_size = max(rt.bar_d, 0.02) if rt.bar != "round" else max(rt.bar_w, 0.02)
    with_bottom = rt.bottom and rt.infill in ("bars", "zigzag", "mesh", "panel", "glass")
    low = rt.bottom_z + (bottom_size if with_bottom else 0.0)  # (the infill's foot over the line)
    posts = []
    for i, (a, b) in enumerate(segments):
        d = b - a
        along = _horizontal(d)
        left = np.cross(up, along)
        run = float(np.linalg.norm(d[:2]))
        first = i == 0 and not closed
        last = i == len(segments) - 1 and not closed
        # the top rail: on past the ends a hair at corners, to close them
        if rt.top != "none":
            ext = np.zeros(3) if first else -along * rt.top_w / 2
            ext2 = np.zeros(3) if last else along * rt.top_w / 2
            z = up * (h - top_size / 2)
            shape = "round" if rt.top == "round" else "square"
            out.append(("bar", a + z + ext, b + z + ext2, shape, rt.top_w, rt.top_h, left, rt.top_mat))
        # the posts: at its start (and the last end), and between, at most `spacing` apart
        stops = [0.0, 1.0]
        if rt.has_posts or rt.infill == "glass_channel":
            k = max(1, int(math.ceil(run / rt.spacing - 1e-9)))
            stops = [j / k for j in range(k + 1)]
        if rt.has_posts:
            here = stops[:-1] + ([1.0] if last else [])
            for s in here:
                posts.append((a + d * s, along))
        # what fills it, bay by bay (between two posts)
        for s0, s1 in zip(stops, stops[1:]):
            out += _bay(a + d * s0, a + d * s1, along, left, rt, low, under_top, h)
        if with_bottom:
            z = up * (rt.bottom_z + bottom_size / 2)
            out.append(("bar", a + z, b + z, "square", bottom_size, bottom_size, left, rt.infill_mat))
        if rt.infill == "glass_channel":                       # (its base channel, on the floor)
            z = up * (rt.shoe_h / 2)
            out.append(("bar", a + z, b + z, "square", rt.shoe_w, rt.shoe_h, left, rt.post_mat))
        if rt.hand:
            out += _handrail(a, b, along, left, rt, [a + d * s for s in stops], first, last)
    for q, along in posts:
        top = h if rt.top == "none" else under_top
        shape = "round" if rt.post == "round" else "square"
        out.append(("bar", q, q + up * top, shape, rt.post_w, rt.post_d, along, rt.post_mat))
        if rt.plate != "none":
            out.append(("plate", q, rt.plate, rt.plate_w, rt.plate_t, rt.post_mat))
    if segments and not closed and max(extend) > 1e-9:
        out += _extensions(segments, rt, h, extend)
    return out


def _extensions(segments, rt, h, extend):
    """(0.282) The handrail — or, with none, the top rail (the hand's grip on a stair's guard) — on past the
    railing's ends, as DL 163/2006 asks of a stair's (annex 2.4.9): at its start extend[0] on (in the plan), keeping
    its slope; at its end extend[1] on, level. Each turned down to the line's level where it ends — the floor, on a
    stair: one going before its first nosing, the floor it climbs to after its last — as Revit's «Floor» extension:
    held up, no end sticking out."""
    up = np.array((0.0, 0.0, 1.0))
    if rt.hand:
        sides = {"left": (1.0,), "right": (-1.0,), "both": (1.0, -1.0)}[rt.hand_side]
        offsets = [s * rt.hand_off for s in sides]
        shape = "round" if rt.hand_shape == "round" else "square"
        w, d, z, mat = rt.hand_w, rt.hand_w if shape == "round" else rt.hand_w * 0.8, rt.hand_z - rt.hand_w / 2, \
            rt.hand_mat
    elif rt.top != "none":
        offsets = [0.0]
        shape = "round" if rt.top == "round" else "square"
        size = rt.top_w if rt.top == "round" else rt.top_h
        w, d, z, mat = rt.top_w, rt.top_h, h - size / 2, rt.top_mat
    else:
        return []
    out = []
    for (a, b), length, at_start in ((segments[0], extend[0], True), (segments[-1], extend[1], False)):
        if length <= 1e-9:
            continue
        step = b - a
        along = _horizontal(step)
        left = np.cross(up, along)
        if at_start:                                           # (back down the slope)
            start, end = a, a - step * (length / float(np.linalg.norm(step[:2])))
        else:                                                  # (on, level)
            start, end = b, b + along * length
        for off in offsets:
            o = left * off
            out.append(("bar", start + o + up * z, end + o + up * z, shape, w, d, left, mat))
            out.append(("bar", end + o + up * (z + w / 2), end + o, shape, w, d, along, mat))
    return out


def _bay(p, q, along, left, rt, low, top, h):
    """The infill between two posts (p, q: on the line, their middles)."""
    up = np.array((0.0, 0.0, 1.0))
    half = (rt.post_w / 2) if rt.has_posts else 0.0
    d = q - p
    run = float(np.linalg.norm(d[:2]))
    if run <= 2 * half + 0.01:
        return []
    a = p + d * (half / run)                                   # (from the posts' faces)
    b = q - d * (half / run)
    span = float(np.linalg.norm((b - a)[:2]))
    out = []
    kind = rt.infill
    if kind == "bars":                                         # (n bars, n + 1 equal clear gaps, none over rt.gap)
        n = max(1, int(math.ceil((span - rt.gap) / (rt.gap + rt.bar_w) - 1e-9)))
        clear = (span - n * rt.bar_w) / (n + 1)
        for j in range(n):
            s = (clear * (j + 1) + rt.bar_w * (j + 0.5)) / span
            c = a + (b - a) * s
            out.append(("bar", c + up * low, c + up * top, rt.bar, rt.bar_w, rt.bar_d, along, rt.infill_mat))
    elif kind in ("rails", "cables"):
        height = top - low
        size = rt.bar_w
        n = rt.count if rt.count > 0 else max(1, int(math.ceil((height - rt.gap) / (rt.gap + size) - 1e-9)))
        for j in range(n):
            z = up * (low + height * (j + 1) / (n + 1))
            ends = (p, q) if kind == "cables" else (a, b)       # (cables through the posts)
            shape = "round" if kind == "cables" else rt.bar
            out.append(("bar", ends[0] + z, ends[1] + z, shape, size, rt.bar_d, left, rt.infill_mat))
    elif kind == "glass":
        inset = (b - a) * (0.02 / span)
        g0, g1 = a + inset, b - inset
        out.append(("pane", g0, g1, FLOOR_GAP if not rt.bottom else low, top - 0.03, rt.sheet_t, rt.infill_mat))
        cz, cy, cx = CLAMP
        for c, inward in ((g0, 1.0), (g1, -1.0)):              # (two clamps by each post)
            for frac in (0.25, 0.75):
                z = FLOOR_GAP + (top - 0.03 - FLOOR_GAP) * frac
                m = c + along * inward * (cx / 2 - 0.01)
                out.append(("bar", m + up * (z - cz / 2), m + up * (z + cz / 2), "square", cx, rt.sheet_t + 2 * cy,
                            along, rt.post_mat))
    elif kind == "glass_channel":
        joint = (b - a) * (GLASS_JOINT / 2 / span)
        z0 = 0.03                                              # (its foot set in the channel)
        z1 = top if rt.top != "none" else h
        out.append(("pane", a + joint, b - joint, z0, z1, rt.sheet_t, rt.infill_mat))
    elif kind == "panel":
        out.append(("pane", a, b, low if rt.bottom else FLOOR_GAP, top, rt.sheet_t, rt.infill_mat))
    elif kind == "mesh":
        z0, z1 = (low if rt.bottom else FLOOR_GAP), top
        w = rt.bar_w
        for c in (a + (b - a) * (w / 2 / span), b - (b - a) * (w / 2 / span)):     # (its frame)
            out.append(("bar", c + up * z0, c + up * z1, rt.bar, w, rt.bar_d, along, rt.infill_mat))
        for z in (z0 + w / 2, z1 - w / 2):
            out.append(("bar", a + up * z, b + up * z, rt.bar, w, rt.bar_d, left, rt.infill_mat))
        wire = 0.004
        n = max(1, int(round(span / rt.gap)))
        for j in range(1, n):
            c = a + (b - a) * j / n
            out.append(("bar", c + up * z0, c + up * z1, "round", wire, wire, along, rt.infill_mat))
        m = max(1, int(round((z1 - z0) / rt.gap)))
        for j in range(1, m):
            z = up * (z0 + (z1 - z0) * j / m)
            out.append(("bar", a + z, b + z, "round", wire, wire, left, rt.infill_mat))
    elif kind == "zigzag":
        n = max(1, int(math.ceil(span / rt.gap - 1e-9)))
        for j in range(n):
            c0, c1 = a + (b - a) * j / n, a + (b - a) * (j + 1) / n
            mid = (c0 + c1) / 2
            out.append(("bar", c0 + up * low, mid + up * top, "round", rt.bar_w, rt.bar_w, left, rt.infill_mat))
            out.append(("bar", mid + up * top, c1 + up * low, "round", rt.bar_w, rt.bar_w, left, rt.infill_mat))
    return out


def _handrail(a, b, along, left, rt, stops, first, last):
    """A handrail on brackets beside the line a -> b, on its side(s), and its brackets at the stops."""
    up = np.array((0.0, 0.0, 1.0))
    out = []
    sides = {"left": (1.0,), "right": (-1.0,), "both": (1.0, -1.0)}[rt.hand_side]
    size = rt.hand_w
    for s in sides:
        off = left * s * rt.hand_off
        z = up * (rt.hand_z - size / 2)
        shape = "round" if rt.hand_shape == "round" else "square"
        out.append(("bar", a + off + z, b + off + z, shape, size, size if shape == "round" else size * 0.8, left,
                     rt.hand_mat))
        if rt.hand_off > size / 2 + 0.01:                      # (its brackets, from the line out to it)
            below = up * (rt.hand_z - size - 0.03)
            for c in stops:
                out.append(("bar", c + below, c + off + below, "round", BRACKET, BRACKET, along, rt.post_mat))
                out.append(("bar", c + off + below, c + off + up * (rt.hand_z - size), "round", BRACKET, BRACKET,
                            along, rt.post_mat))
    return out
