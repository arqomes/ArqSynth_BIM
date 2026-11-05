"""View templates (Phase 4, step 3): a named set of view settings — a plan's cut height, the IFC
classes not shown (furniture in a construction plan…), what the elements are coloured by, the
scale on sheets — given to several plans, sections and elevations at once, as Revit's view
templates. Changing the template changes all its views. Kept with the views in the .arqbim file.

A view without a template has its own properties (0.59: the Properties panel with nothing
selected), the same settings for that view alone: a dict of OWN_FIELDS, kept in the .arqbim file.
"""

import uuid
from dataclasses import dataclass, field

CUT_HEIGHT = 1.20
# which phases a view shows (a renovation project): the phases each choice hides — "" for the
# elements without a phase, taken as existing ones that stay
PHASE_FILTERS = {
    "all": (),                                        # everything (the changes: yellows and reds)
    "existing": ("NEW", "TEMPORARY"),                 # the building as it is, before the works
    "proposal": ("DEMOLISH",),                        # the building as it will be
    "new": ("EXISTING", "DEMOLISH", ""),              # only what is built
}


@dataclass
class ViewTemplate:
    name: str
    cut_height: float = CUT_HEIGHT       # m above the storey (plans)
    hidden: list = field(default_factory=list)     # IFC classes not shown
    rule: tuple = None                   # graphic rule key (model/graphic_rules), None: usual colours
    scale: int = None                    # N of 1:N on sheets, None: automatic
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)
    phases: str = "all"                  # which phases are shown (PHASE_FILTERS)
    style: str = None                    # (0.315) the view style its views are drawn with (model/view_styles), None: theirs


@dataclass
class Settings:
    """What a view shows (its template's, or the defaults)."""
    cut_height: float = CUT_HEIGHT
    hidden: frozenset = frozenset()
    rule: tuple = None
    scale: int = None
    template: str = None                 # its template's name, or None
    hidden_phases: frozenset = frozenset()   # phases not shown ("" = elements without one)
    phases: str = "all"                  # the choice those come from (PHASE_FILTERS)
    # the 3D view's look (0.63): always its own (a template does not give it)
    style: str = "shaded"                # STYLES
    edges: bool = True
    grid: bool = True                    # the ground grid
    axonometric: bool = False            # seen without perspective
    box: tuple = None                    # its section box (0.64): (lowest, highest corner), or None
    # a plan's range and look (0.65): always its own too
    depth: float = 0.0                   # m below its storey's level: the storeys down to there are seen too
    underlay: str = None                 # "below" | "above": that storey drawn in grey under it
    crop: tuple = None                   # (x0, y0, x1, y1): only that rectangle drawn (on screen and paper)
    detail: str = "fine"                 # DETAILS: what is cut — solid ("coarse"), one hatch, its layers ("fine")
    home: dict = None                    # the 3D view's starting view (0.81): {"eye", "target"}, or None
    slopes: bool = False                 # (0.201) the terrains coloured by their slope — a plan on paper too
    labels: dict = None                  # (0.238) its labels moved by hand: {key: (dx, dy) m} — always its own
    # (0.315) the view style given to it (its own, or its template's), None: none — its drawings on paper as before
    # (lines, the cut by material), its 3D look the usual (`style`)
    drawn_style: str = None
    # (0.331) its hatches by element, as Revit's «Override graphics in view ▸ by element» — always its own: {GlobalId:
    # (cut foreground, cut background, surface foreground, surface background)}, each (pattern, colour) or None
    # (that one not changed: its category's, its materials'); None: none
    elements: dict = None


STYLES = ("shaded", "hidden", "wire", "xray")         # (0.315: the first of view_styles.BUILTIN; the others there)
DETAILS = ("coarse", "medium", "fine")
UNDERLAYS = ("below", "above")
LOOK_FIELDS = ("style", "edges", "grid", "axonometric", "box", "home", "slopes")
PLAN_FIELDS = ("depth", "underlay", "crop", "detail")
NOTE_FIELDS = ("labels",)                # (0.238)
ELEMENT_FIELDS = ("elements",)           # (0.331)
OWN_FIELDS = ("cut_height", "hidden", "rule", "scale", "phases") + LOOK_FIELDS + PLAN_FIELDS + NOTE_FIELDS + \
    ELEMENT_FIELDS


def settings_of(template, own=None):
    """What a view shows: its template's settings when it has one, else its own properties
    (a dict of OWN_FIELDS; what is not there is the default). The look is always its own."""
    own = own or {}
    box, crop = own.get("box"), own.get("crop")
    look = (own.get("style", "shaded"), own.get("edges", True), own.get("grid", True), own.get("axonometric", False),
            (tuple(box[0]), tuple(box[1])) if box else None,
            float(own.get("depth", 0.0)), own.get("underlay"), tuple(crop) if crop else None, own.get("detail", "fine"),
            own.get("home"), bool(own.get("slopes", False)))
    labels = {str(k): (float(v[0]), float(v[1])) for k, v in (own.get("labels") or {}).items()} or None
    elements = element_hatches(own.get("elements"))                   # (0.331)
    drawn = own.get("style")
    if template is not None and getattr(template, "style", None):      # (0.315: a template's style is its views')
        drawn = template.style
        look = (drawn,) + look[1:]
    if template is None:
        phases = own.get("phases", "all")
        return Settings(float(own.get("cut_height", CUT_HEIGHT)), frozenset(own.get("hidden", ())),
                        tuple(own["rule"]) if own.get("rule") else None, own.get("scale") or None, None,
                        frozenset(PHASE_FILTERS.get(phases, ())), phases, *look, labels=labels, drawn_style=drawn,
                        elements=elements)
    return Settings(template.cut_height, frozenset(template.hidden), tuple(template.rule) if template.rule else None,
                    template.scale, template.name, frozenset(PHASE_FILTERS.get(template.phases, ())),
                    template.phases, *look, labels=labels, drawn_style=drawn, elements=elements)


def _layer(value):
    """(0.331) A hatch's layer as kept — (pattern, colour) — or None."""
    if isinstance(value, (list, tuple)) and len(value) == 2 and isinstance(value[0], str) and value[0] \
            and isinstance(value[1], str) and len(value[1]) == 7 and value[1].startswith("#"):
        return str(value[0]), str(value[1])
    return None


def element_hatches(data):
    """(0.331) A view's hatches by element as kept ({GlobalId: four layers}), cleaned: each layer (pattern, colour) or
    None, an element with none left out. None when there are none."""
    found = {}
    if isinstance(data, dict):
        for guid, layers in data.items():
            if isinstance(guid, str) and guid and isinstance(layers, (list, tuple)) and len(layers) == 4:
                entry = tuple(_layer(x) for x in layers)
                if any(entry):
                    found[guid] = entry
    return found or None


def own_to_dict(own):
    return {k: list(v) if isinstance(v, (tuple, list, set, frozenset)) else v for k, v in own.items()}


def own_from_dict(data):
    """A view's own properties as read from the .arqbim file (what is not understood is left out)."""
    own = {}
    if not isinstance(data, dict):
        return own
    try:
        if data.get("cut_height") is not None:
            own["cut_height"] = float(data["cut_height"])
        if data.get("hidden"):
            own["hidden"] = sorted(str(c) for c in data["hidden"])
        if data.get("rule"):
            own["rule"] = tuple(data["rule"])
        if data.get("scale"):
            own["scale"] = int(data["scale"])
        if data.get("phases") in PHASE_FILTERS:
            own["phases"] = data["phases"]
        if isinstance(data.get("style"), str) and 0 < len(data["style"]) <= 64:   # (0.315: a project style's uid too)
            own["style"] = data["style"]
        for key in ("edges", "grid", "axonometric", "slopes"):
            if isinstance(data.get(key), bool):
                own[key] = data[key]
        box = data.get("box")
        if box and len(box) == 2 and all(len(c) == 3 for c in box):
            lo, hi = ([float(v) for v in c] for c in box)
            if all(a < b for a, b in zip(lo, hi)):
                own["box"] = [lo, hi]
        if data.get("depth") is not None and float(data["depth"]) > 0:
            own["depth"] = float(data["depth"])
        if data.get("underlay") in UNDERLAYS:
            own["underlay"] = data["underlay"]
        crop = data.get("crop")
        if crop and len(crop) == 4:
            x0, y0, x1, y1 = (float(v) for v in crop)
            if x0 < x1 and y0 < y1:
                own["crop"] = [x0, y0, x1, y1]
        if data.get("detail") in DETAILS:
            own["detail"] = data["detail"]
        home = data.get("home")
        if isinstance(home, dict) and all(len(home.get(k) or ()) == 3 for k in ("eye", "target")):
            own["home"] = {k: [float(v) for v in home[k]] for k in ("eye", "target")}
        labels = data.get("labels")                                  # (0.238)
        if isinstance(labels, dict):
            moved = {str(k): [float(v[0]), float(v[1])] for k, v in labels.items()
                     if isinstance(v, (list, tuple)) and len(v) == 2}
            if moved:
                own["labels"] = moved
        elements = element_hatches(data.get("elements"))             # (0.331)
        if elements:
            own["elements"] = elements
    except (TypeError, ValueError):
        pass
    return own


def phase_templates(label):
    """The three templates of a renovation project, made at once: label(key) -> name."""
    from .graphic_rules import STATUS
    return [ViewTemplate(label("existing"), phases="existing"),
            ViewTemplate(label("proposal"), phases="proposal"),
            ViewTemplate(label("changes"), phases="all", rule=STATUS)]


def to_dict(template):
    return {"name": template.name, "cut_height": template.cut_height, "hidden": list(template.hidden),
            "rule": list(template.rule) if template.rule else None, "scale": template.scale, "uid": template.uid,
            "phases": template.phases, "style": template.style}


def from_dict(data):
    try:
        rule = data.get("rule")
        phases = data.get("phases", "all")
        style = data.get("style")
        return ViewTemplate(str(data["name"]), float(data.get("cut_height", CUT_HEIGHT)),
                            [str(c) for c in data.get("hidden", ())], tuple(rule) if rule else None,
                            int(data["scale"]) if data.get("scale") else None, str(data.get("uid") or uuid.uuid4().hex),
                            phases if phases in PHASE_FILTERS else "all",
                            str(style) if isinstance(style, str) and style else None)
    except (KeyError, TypeError, ValueError):
        return None
