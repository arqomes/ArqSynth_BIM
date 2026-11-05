"""(0.318) The project's own fill patterns kept in its IFC, so that they go with it: each an IfcFillAreaStyle of its own
(on no material: a definition), named "ArqSynth:" + its key + ":" + its name, ModelorDraughting its kind (measured on
the building or on paper), its families of lines IfcFillAreaStyleHatching as a material's are written
(ifc/material_graphics.py) — and read back from them. Sizes in the project's units (a drafting pattern's mm on paper
too)."""

import math

from ..core import patterns as core_patterns
from . import material_graphics

PREFIX = "ArqSynth:"


def _name(pattern):
    return "{}{}:{}".format(PREFIX, pattern.key, pattern.name)


def _parts(name):
    """(key, name) of a definition's IFC name, or None."""
    if not str(name or "").startswith(PREFIX):
        return None
    rest = str(name)[len(PREFIX):]
    if not rest.startswith(core_patterns.PROJECT):
        return None
    head, _sep, label = rest[len(core_patterns.PROJECT):].partition(":")
    key = core_patterns.PROJECT + head
    if not head:
        return None
    return key, label


def definitions(f):
    """{key: IfcFillAreaStyle} of the project's patterns."""
    out = {}
    for style in f.by_type("IfcFillAreaStyle"):
        found = _parts(style.Name)
        if found is not None:
            out[found[0]] = style
    return out


def write(f, pattern, unit):
    """A pattern's definition in the file (unit: project units a metre)."""
    hatchings = material_graphics._hatchings(f, pattern.key, "#000000", material_graphics.LAYERS[0], unit,
                                              material_graphics._angle_unit(f), pattern=pattern)
    style = f.create_entity("IfcFillAreaStyle", Name=_name(pattern), FillStyles=hatchings)
    if hasattr(style, "ModelorDraughting"):
        style.ModelorDraughting = bool(pattern.model)
    return style


def remove(f, key):
    style = definitions(f).get(key)
    if style is not None:
        material_graphics._remove(f, style)


def read(f, unit):
    """The project's patterns ([core.patterns.Pattern]) read from their definitions."""
    angle_unit = material_graphics._angle_unit(f)
    out = []
    for key, style in definitions(f).items():
        label = _parts(style.Name)[1]
        model = bool(getattr(style, "ModelorDraughting", False))
        size = unit * (1.0 if model else 0.001)
        families = []
        for h in style.FillStyles or ():
            if not h.is_a("IfcFillAreaStyleHatching"):
                continue
            angle = math.degrees(float(h.HatchLineAngle or 0.0) * angle_unit)
            start = h.StartOfNextHatchLine
            if start is not None and start.is_a("IfcVector"):
                dx, dy = (float(c) for c in start.Orientation.DirectionRatios[:2])
                shift, step = dx * float(start.Magnitude) / size, dy * float(start.Magnitude) / size
            else:
                shift, step = 0.0, float(getattr(start, "wrappedValue", 0.0) or 0.0) / size
            ref = h.PointOfReferenceHatchLine
            x0, y0 = ((float(c) / size for c in ref.Coordinates[:2]) if ref is not None else (0.0, 0.0))
            dashes = []
            font = getattr(h.HatchLineAppearance, "CurveFont", None)
            if font is not None and font.is_a("IfcCurveStyleFont"):
                for part in font.PatternList or ():
                    dashes += [float(part.VisibleSegmentLength) / size, -float(part.InvisibleSegmentLength) / size]
            families.append((round(angle, 9), round(x0, 9), round(y0, 9), round(shift, 9), round(step, 9),
                             tuple(round(d, 9) for d in dashes)))
        if families:
            out.append(core_patterns.Pattern(key, model, tuple(families), label))
    return out
