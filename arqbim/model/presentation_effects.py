"""(0.486) The ArqSynth Presentation's scene effects «Construção» and «Explosão» (its lib/editor3d/effects.ts and
components/editor3d/EffectsController.tsx), worked out here as it plays them — so the BIM's interface shows, before the
model is sent, what the Presentation will show:

- construction: each element (a layer of the GLB) appears in the order of the works — its phase found by the words of
  its name and category (terrain, foundations, structure, walls, doors and windows, stairs, roof, finishes, fittings;
  the others between the walls and the openings), then the lowest first, then by name —; the terrain and the
  foundations rise from below, the rest comes down from above; those «removidos do efeito» stay where they are;
- explosion: each element starts away from the middle of the model (its own way with a fixed jitter) and comes back in
  an order that looks random but is the same every time (the Presentation's mulberry32, seeded by how many there are
  and the model's size).

Everything in the model's axes (Z up); the Presentation's (Y up) only inside, where its random jitter is drawn. Pure
Python and NumPy."""

import functools
import math
import unicodedata

import numpy as np

# the Presentation's CONSTRUCTION_PHASES: the first whose word is in the category or the name wins
PHASES = (
    ("site", ("terreno", "terrain", "site", "topo", "topografia", "ground", "chão", "chao", "landscape", "relva",
              "grass", "pavimento exterior")),
    ("foundation", ("funda", "sapata", "footing", "foundation", "estaca", "pile", "ensoleiramento", "radier")),
    ("structure", ("estrutura", "structural", "pilar", "column", "viga", "beam", "laje", "slab", "betão", "betao",
                   "concrete", "framing", "floor", "piso", "pavimento")),
    ("walls", ("parede", "wall", "alvenaria", "masonry", "tijolo", "brick", "divisória", "divisoria", "partition",
               "fachada", "facade")),
    ("openings", ("porta", "door", "janela", "window", "caixilh", "esquadria", "vão", "vao", "vidro", "glass",
                  "glazing", "curtain")),
    ("stairs", ("escada", "stair", "degrau", "step", "rampa", "ramp", "guarda", "railing", "corrimão", "corrimao",
                "handrail")),
    ("roof", ("cobertura", "telhado", "roof", "telha", "tile", "shingle", "chaminé", "chamine", "chimney",
              "claraboia", "skylight")),
    ("finishes", ("acabamento", "finish", "revestimento", "cladding", "tecto", "teto", "ceiling", "rodapé", "rodape",
                  "pintura", "paint")),
    ("fixtures", ("mobiliário", "mobiliario", "furniture", "móvel", "movel", "sofá", "sofa", "mesa", "table",
                  "cadeira", "chair", "cama", "bed", "loiça", "louça", "sanita", "toilet", "lavatório", "lavatorio",
                  "sink", "cozinha", "kitchen", "candeeiro", "lamp", "árvore", "arvore", "tree", "planta", "plant",
                  "carro", "car", "pessoa", "people")))
UNMATCHED = 3.5                 # (after the walls, before the openings)
RISE = (0, 1)                   # the terrain and the foundations rise from below
KINDS = ("construction", "explode")
SPREAD_MIN, SPREAD_MAX, SPREAD_DEFAULT = 0.3, 3.0, 1.2     # (its «Distância» slider, × the model's radius)


def _plain(text):
    """Lower case, without accents (the Presentation's normalize: NFD, the marks taken out)."""
    return "".join(c for c in unicodedata.normalize("NFD", str(text or "").lower())
                   if not 0x300 <= ord(c) <= 0x36f)


_WORDS = tuple(tuple(_plain(w) for w in words) for _phase, words in PHASES)


def _phase_in(text):
    for k, words in enumerate(_WORDS):
        if any(w in text for w in words):
            return k
    return None


def phase_of(name, category=""):
    """The element's phase of the works: its index in PHASES (UNMATCHED: none) — as the Presentation's
    classifyConstructionPhase: on the name and the category up to its first « · » (the GLB's folders are «Paredes ·
    Piso 0»: the storey's «piso» is not the structure's — changed in the Presentation too), else on the whole
    category."""
    category = str(category or "")
    head = category.split(" · ")[0]
    k = _phase_in(_plain("{} {}".format(head, name or "")))
    if k is None and head != category:
        k = _phase_in(_plain("{} {}".format(category, name or "")))
    return UNMATCHED if k is None else k


def phase_name(index):
    """The phase's key (its name in i18n «pmode.phase.<key>»): one of PHASES', or "other"."""
    return PHASES[int(index)][0] if index != UNMATCHED and 0 <= index < len(PHASES) else "other"


def order(units):
    """The units [{id, name, category, low}] in the order of the works (the Presentation's sortLayersForConstruction:
    phase, then the lowest — `low` its box's lowest corner, None: not known —, then the name); their ids."""
    keyed = [(phase_of(u["name"], u.get("category", "")), u) for u in units]

    def bottom(u):
        low = u.get("low")
        return float(low[2]) if low is not None else None

    def before(a, b):
        (pa, ua), (pb, ub) = a, b
        if pa != pb:
            return -1 if pa < pb else 1
        ya, yb = bottom(ua), bottom(ub)
        if ya is not None and yb is not None and abs(ya - yb) > 1e-4:
            return -1 if ya < yb else 1
        na, nb = _plain(ua["name"]), _plain(ub["name"])
        return (na > nb) - (na < nb)

    return [u["id"] for _p, u in sorted(keyed, key=functools.cmp_to_key(before))]


def seeded_random(seed):
    """The Presentation's mulberry32: the same numbers in [0, 1) for the same seed."""
    state = [seed & 0xFFFFFFFF]

    def imul(a, b):
        return (a * b) & 0xFFFFFFFF

    def rnd():
        a = (state[0] + 0x6D2B79F5) & 0xFFFFFFFF
        state[0] = a
        t = imul(a ^ (a >> 15), 1 | a)
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF) ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0
    return rnd


def _js_round(x):
    return math.floor(x + 0.5)


def plan(kind, units, center, radius, spread=SPREAD_DEFAULT):
    """How each element moves in the effect: [{id, start, end (fractions of its time), amplitude (m), way (the
    model's axes, unit: where it is when it starts, from where it ends), hide (not seen before it starts)}] — the
    Presentation's EffectsController. units: those that take part, in the order of the GLB's nodes — [{id, name,
    category, low, high (its box's corners), centre}]; center, radius: the whole model's box's middle and half its
    diagonal (≥ 0,5 m)."""
    radius = max(float(radius), 0.5)
    center = np.asarray(center, dtype=float)
    out = []
    if not units:
        return out
    if kind == "construction":
        ids = order(units)
        by_id = {u["id"]: u for u in units}
        n = len(ids)
        frac = min(0.5, max(0.08, 2.5 / n))
        for k, uid in enumerate(ids):
            u = by_id[uid]
            start = k / (n - 1) * (1 - frac) if n > 1 else 0.0
            height = max(float(u["high"][2]) - float(u["low"][2]), radius * 0.02)
            rises = phase_of(u["name"], u.get("category", "")) in RISE
            out.append({"id": uid, "start": start, "end": start + frac,
                        "amplitude": height * 0.9 if rises else height * 0.6 + radius * 0.06,
                        "way": (0.0, 0.0, -1.0) if rises else (0.0, 0.0, 1.0), "hide": True})
        return out
    spread = max(0.2, float(spread or SPREAD_DEFAULT))
    rnd = seeded_random(len(units) * 7919 + _js_round(radius * 100))
    frac = 0.45
    for u in units:
        d = np.asarray(u["centre"], dtype=float) - center
        g = np.array((d[0], d[2], -d[1]))                  # (in the Presentation's axes: its jitter is drawn there)
        if float(g @ g) < 1e-6:
            g = np.array((rnd() - 0.5, rnd() - 0.5, rnd() - 0.5))
        g = g / np.linalg.norm(g)
        g = g + np.array(((rnd() - 0.5) * 0.7, (rnd() - 0.5) * 0.5, (rnd() - 0.5) * 0.7))
        g = g / np.linalg.norm(g)
        start = rnd() * (1 - frac)
        amplitude = spread * radius * (0.55 + rnd() * 0.55)
        out.append({"id": u["id"], "start": start, "end": start + frac, "amplitude": amplitude,
                    "way": (float(g[0]), float(-g[2]), float(g[1])), "hide": False})
    return out


def at(moves, t):
    """Where the elements are at the fraction `t` of the effect's time: (offsets (N, 3) in m, seen (N,) bool) — each
    eased out (the Presentation's easeOutCubic), those that are «hide» unseen until they start."""
    if not moves:
        return np.zeros((0, 3)), np.zeros(0, bool)
    start = np.array([m["start"] for m in moves])
    end = np.array([m["end"] for m in moves])
    span = end - start
    local = np.where(span > 0, np.clip((t - start) / np.where(span > 0, span, 1.0), 0.0, 1.0), 1.0)
    k = 1.0 - (1.0 - local) ** 3
    distance = np.array([m["amplitude"] for m in moves]) * (1.0 - k)
    distance[distance <= 1e-5] = 0.0
    seen = ~np.array([m["hide"] for m in moves]) | (t >= start)
    return np.array([m["way"] for m in moves]) * distance[:, None], seen


def seconds_of(seconds):
    """How long it plays (the Presentation's: at least 1 s; nothing given, 6 s)."""
    return max(1.0, float(seconds or 6.0))
