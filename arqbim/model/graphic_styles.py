"""The project's graphic styles (Phase 5, step 5): how its drawings look on paper — for each kind of material
cut (ifc HATCH_WORDS: concrete, masonry, wood, insulation, gypsum; and the rest), its fill colour, its pattern
(solid, lines, crossed lines, nothing) at an angle and so many mm apart; and the pens, the width of each kind of
line (what is cut, what is seen beyond, the hatches, the dimensions, what is drawn in the views). The line
types of what is drawn in the views (continuous, dashed, dash-dot, hidden) are here too.

Kept with the views beside the IFC (as the dimension style); one undo step to change. Pure data (no Qt)."""

import copy

MATERIALS = ("concrete", "masonry", "wood", "insulation", "gypsum", "earth", "other")      # (earth: 0.155)
# (0.314) and core.patterns' drafting patterns (their own sizes on paper: no angle nor spacing), over the fill
LIBRARY = ("concrete", "sand", "insulation", "earth", "wood", "steel", "square")
PATTERNS = ("solid", "lines", "cross", "none") + tuple("pat:" + k for k in LIBRARY)
PENS = ("cut", "seen", "hatch", "dimension", "drawn")
LINE_TYPES = ("continuous", "dashed", "dashdot", "hidden")
LINE_WIDTHS = (0.13, 0.18, 0.25, 0.35, 0.50, 0.70)      # mm: the usual pens
DASHES = {"continuous": None, "dashed": (6.0, 3.0), "dashdot": (10.0, 2.5, 1.5, 2.5), "hidden": (2.5, 2.0)}   # mm

DEFAULTS = {
    "hatches": {                     # as they were drawn before (ui/pdf.py, until 0.125)
        "concrete": {"fill": "#3c3c3c", "pattern": "solid", "angle": 45.0, "spacing": 1.0},
        "masonry": {"fill": "#ffffff", "pattern": "lines", "angle": 45.0, "spacing": 1.0},
        "wood": {"fill": "#ffffff", "pattern": "cross", "angle": 45.0, "spacing": 1.6},
        "insulation": {"fill": "#ffffff", "pattern": "lines", "angle": -45.0, "spacing": 0.6},
        "gypsum": {"fill": "#b9b9b9", "pattern": "solid", "angle": 45.0, "spacing": 1.0},
        "earth": {"fill": "#efe8da", "pattern": "lines", "angle": 45.0, "spacing": 2.5},
        "other": {"fill": "#3c3c3c", "pattern": "solid", "angle": 45.0, "spacing": 1.0},
    },
    "pens": {"cut": 0.50, "seen": 0.18, "hatch": 0.10, "dimension": 0.13, "drawn": 0.25},
    # (0.360) the views' symbols, as drawn until then: a section's / an elevation's / a detail's head, a level's mark
    # — sizes in mm on paper (a head's radius, its text's height), the pen of their lines
    "symbols": {
        "section": {"head": "circle", "size": 4.0, "arrow": "filled", "text": 4.8, "line": "dashdot", "pen": 0.30},
        "elevation": {"head": "circle", "size": 4.0, "arrow": "filled", "text": 4.8, "pen": 0.30},
        "detail": {"head": "circle", "size": 3.2, "line": "dashed", "text": 3.8, "pen": 0.25},
        "level": {"mark": "triangle", "size": 1.8, "line": "dashdot", "text": 2.2, "pen": 0.18},
    },
}
# (0.360) what each part of a symbol may be
SYMBOL_KINDS = ("section", "elevation", "detail", "level")
SYMBOL_CHOICES = {"head": ("circle", "square", "none"), "arrow": ("filled", "open", "none"),
                  "line": ("dashdot", "dashed", "continuous", "ends"), "mark": ("triangle", "target", "none")}
SYMBOL_SIZES = {"size": (1.0, 12.0), "text": (1.0, 12.0), "pen": (0.05, 1.0)}


def defaults():
    return copy.deepcopy(DEFAULTS)


def _project_pattern(name):
    """(0.318) "pat:" + a project's own drafting pattern (core.patterns: made in the pattern editor)."""
    from ..core import patterns as core_patterns
    found = core_patterns.get(name[4:]) if isinstance(name, str) and name.startswith("pat:") else None
    return found is not None and not found.builtin and not found.model


def patterns():
    """(0.318) The patterns a category can be given: PATTERNS, then the project's own drafting ones."""
    from ..core import patterns as core_patterns
    return PATTERNS + tuple("pat:" + p.key for p in core_patterns.project_patterns() if not p.model)


def _colour(value, fallback):
    text = str(value or "")
    return text if len(text) == 7 and text.startswith("#") and all(c in "0123456789abcdefABCDEF"
                                                                   for c in text[1:]) else fallback


def clean(style):
    """A graphic style read from a file or a dialog: its known parts, sensible values; the rest defaults."""
    out = defaults()
    style = style if isinstance(style, dict) else {}
    for key, given in (style.get("hatches") or {}).items():
        if key not in out["hatches"] or not isinstance(given, dict):
            continue
        h = out["hatches"][key]
        h["fill"] = _colour(given.get("fill"), h["fill"])
        if given.get("pattern") in PATTERNS or _project_pattern(given.get("pattern")):
            h["pattern"] = given["pattern"]
        for name, low, high in (("angle", -90.0, 90.0), ("spacing", 0.3, 10.0)):
            try:
                h[name] = min(max(float(given.get(name, h[name])), low), high)
            except (TypeError, ValueError):
                pass
    for key, value in (style.get("pens") or {}).items():
        if key in out["pens"]:
            try:
                out["pens"][key] = min(max(float(value), 0.05), 2.0)
            except (TypeError, ValueError):
                pass
    for kind, given in (style.get("symbols") or {}).items():          # (0.360)
        if kind not in out["symbols"] or not isinstance(given, dict):
            continue
        mine = out["symbols"][kind]
        for name in mine:
            if name in SYMBOL_CHOICES and given.get(name) in SYMBOL_CHOICES[name]:
                mine[name] = given[name]
            elif name in SYMBOL_SIZES and name in given:
                low, high = SYMBOL_SIZES[name]
                try:
                    mine[name] = min(max(float(given[name]), low), high)
                except (TypeError, ValueError):
                    pass
    return out


def symbol(style, kind):
    """(0.360) A kind of symbol's style (SYMBOL_KINDS) in a graphic style (its defaults' where it says nothing)."""
    found = ((style or {}).get("symbols") or {}).get(kind)
    return dict(DEFAULTS["symbols"][kind], **(found or {}))


def hatch(style, material):
    """(fill colour, line angles in degrees, spacing in mm) of a cut material (a HATCH_WORDS key, None or
    "colour:#rrggbb" for the rest) in this style — what the PDF fills and hatches it with."""
    h = (style or DEFAULTS)["hatches"].get(material if material in MATERIALS else "other") \
        or DEFAULTS["hatches"]["other"]
    angles = {"lines": (h["angle"],), "cross": (h["angle"], -h["angle"])}.get(h["pattern"], ())
    fill = "#ffffff" if h["pattern"] == "none" else h["fill"]
    return fill, angles, float(h["spacing"])


def library_pattern(style, material):
    """(0.314) The core.patterns drafting pattern a cut material is drawn with over its fill, or None (its lines are
    hatch()'s angles)."""
    h = (style or DEFAULTS)["hatches"].get(material if material in MATERIALS else "other") \
        or DEFAULTS["hatches"]["other"]
    return h["pattern"][4:] if str(h["pattern"]).startswith("pat:") else None


def pen(style, kind):
    """A pen's width in mm (PENS)."""
    return float((style or DEFAULTS)["pens"].get(kind, DEFAULTS["pens"].get(kind, 0.18)))


class SetGraphicStyle:
    """The project's graphic style changed, one undo step: its drawings are made again."""

    def __init__(self, before, after, label):
        self.before, self.after, self.label = copy.deepcopy(before), copy.deepcopy(after), label

    def do(self, doc):
        doc.graphic_style = copy.deepcopy(self.after)
        doc.dimensions_changed()                 # (the views and sheets are drawn again)

    def undo(self, doc):
        doc.graphic_style = copy.deepcopy(self.before)
        doc.dimensions_changed()
