"""Graphic rules (Phase 4, step 1): colour the elements by what they are — IFC class, type,
storey, material, outside or inside, fire rating, or any property in the file — as ArchiCAD's
graphic overrides and Revit's view filters do. Each value gets a colour; a legend says which.
The colours are a way of looking at the model: nothing is written to the IFC.
"""

from ..i18n import t

STATUS = ("status",)                      # the phase (IFC Status): Portuguese renovation drawings' colours
EC3 = ("ec3",)                            # (0.517) the steel pieces by how much of their resistance they use
RULES = (("class",), ("type",), ("storey",), ("material",), ("external",), ("fire",), STATUS, EC3)  # then ("pset", …)
# (0.517) the bands of use, as an engineer's results are coloured: green, yellow, orange, red past 100 %
EC3_BANDS = (("low", 0.5, "#59a14f"), ("mid", 0.8, "#c9b73a"), ("high", 1.0, "#f28e2b"), ("over", None, "#e15759"))
PALETTE = ("#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#b07aa1", "#edc948", "#76b7b2", "#ff9da7",
           "#9c755f", "#86bcb6", "#d37295", "#a0cbe8", "#8cd17d", "#f1ce63", "#499894", "#fabfd2")
NO_VALUE = "#d9d9d9"                      # elements without the property: light grey
YES, NO = "#e15759", "#4e79a7"            # true / false (outside / inside): warm / cool
# phases, as in a renovation drawing ("amarelos e vermelhos"): to build red, to demolish yellow
PHASE_COLOURS = {"NEW": "#e03131", "DEMOLISH": "#f2c200", "EXISTING": "#7d7d7d", "TEMPORARY": "#3a7bd5"}
PHASE_ORDER = ("EXISTING", "DEMOLISH", "NEW", "TEMPORARY")


def rule_label(key):
    if key[0] == "pset":
        return "{} ▸ {}".format(key[1], key[2])
    return t("rules." + key[0])


def ec3_band(utilisation):
    """(0.517) The band a utilisation (0..) falls in: "low" (to 50 %), "mid" (to 80 %), "high" (to 100 %), "over"."""
    for band, limit, _colour in EC3_BANDS:
        if limit is None or utilisation <= limit:
            return band
    return "over"


def value_label(value, key=None):
    if key == STATUS and value in PHASE_COLOURS:
        return t("phase." + value.lower())
    if key == EC3 and value is not None:
        return t("rules.ec3." + value)
    if value is None:
        return t("rules.no_value")
    if isinstance(value, bool):
        return t("rules.yes") if value else t("rules.no")
    if isinstance(value, float):
        return "{:g}".format(value)
    return str(value) or t("rules.no_value")


def legend(values, key=None):
    """[(label, colour, [GlobalIds])] for {GlobalId: value}: one line per value, by label; the
    elements without a value last, in grey. key: the rule (the phases have their own colours)."""
    groups = {}
    for guid, value in values.items():
        groups.setdefault(value, []).append(guid)
    present = [v for v in groups if v is not None]
    if key == STATUS:
        lines = [(value_label(v, key), PHASE_COLOURS[v], sorted(groups[v])) for v in PHASE_ORDER if v in groups]
    elif key == EC3:                                    # (0.517) the bands in their order, their own colours
        lines = [(value_label(b, key), c, sorted(groups[b])) for b, _l, c in EC3_BANDS if b in groups]
    else:
        if all(isinstance(v, bool) for v in present) and present:
            colours = {True: YES, False: NO}
        else:
            ordered = sorted(present, key=lambda v: value_label(v).lower())
            colours = {v: PALETTE[k % len(PALETTE)] for k, v in enumerate(ordered)}
        lines = sorted(((value_label(v), colours[v], sorted(groups[v])) for v in present),
                       key=lambda line: line[0].lower())
    if None in groups:          # (no phase: an existing element that stays — the same grey)
        lines.append((t("props.no_phase"), PHASE_COLOURS["EXISTING"], sorted(groups[None])) if key == STATUS
                     else (value_label(None), NO_VALUE, sorted(groups[None])))
    return lines


def cut_colours(values, key):
    """{GlobalId: colour} for what a drawing fills with colour where it is cut (instead of its
    material's hatch): with the phases, only what is new, to demolish or temporary — what stays
    keeps its hatch, as in a renovation drawing; with other rules, every element with a value."""
    if key == STATUS:
        return {g: PHASE_COLOURS[v] for g, v in values.items() if v in ("NEW", "DEMOLISH", "TEMPORARY")}
    return {g: c for _label, c, guids in legend(values, key) if c != NO_VALUE for g in guids}


def colours(lines):
    """{GlobalId: colour} from a legend."""
    return {guid: colour for _label, colour, guids in lines for guid in guids}
