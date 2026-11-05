"""(0.314) A material's graphics in the IFC, as other programs read them and this one reopens them:

- its shading colour and transparency: its IfcSurfaceStyle's IfcSurfaceStyleShading (SurfaceColour, Transparency);
- its surface and cut patterns: an IfcFillAreaStyle each ("Surface", a model pattern; "Cut", a drafting one) beside
  that surface style, in the same IfcStyledItem of the material's IfcMaterialDefinitionRepresentation. A solid
  background (or foreground) is its one IfcColourRgb (named "Background" / "Foreground"); each pattern's families of
  lines are IfcFillAreaStyleHatching, their IfcCurveStyle named "Foreground" or "Background" and coloured so, dashed by
  an IfcCurveStyleFont (IFC4 allows one colour per fill style and no external style beside hatchings);
- which patterns exactly (their keys in core.patterns): the material's ArqSynth_Parametros "Graficos";
- (0.343) its finish in the realistic render: its ArqSynth_Parametros "Acabamento" ("auto": its category's).

Sizes in the project's units: a model pattern's metres, a drafting pattern's millimetres on paper."""

import math

import ifcopenshell.util.element
import ifcopenshell.util.unit

from ..core import patterns as core_patterns

PARAMS = "ArqSynth_Parametros"
GRAPHICS = "Graficos"
FINISH, FINISH_AUTO = "Acabamento", "auto"
LAYERS = ("Foreground", "Background")
FIELDS = ("surface_fg", "surface_bg", "cut_fg", "cut_bg")
STYLE_NAMES = {"surface": "Surface", "cut": "Cut"}


def hex_of(rgb):
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(float(c) * 255))) for c in rgb))


def rgb_of(text):
    text = str(text or "#000000")
    try:
        return tuple(int(text[k:k + 2], 16) / 255.0 for k in (1, 3, 5))
    except ValueError:
        return 0.0, 0.0, 0.0


def encode(spec):
    """The four patterns as the parameter keeps them: "surface_fg=tile_15 #8d979d;surface_bg=;cut_fg=;cut_bg=" ."""
    parts = []
    for name in FIELDS:
        value = getattr(spec, name)
        parts.append("{}={}".format(name, "{} {}".format(*value) if value else ""))
    return ";".join(parts)


def decode(text):
    """{field: (pattern, colour) or None} from the parameter (what is not understood: None)."""
    out = {name: None for name in FIELDS}
    for part in str(text or "").split(";"):
        name, _sep, value = part.partition("=")
        bits = value.split()
        if name.strip() in out and len(bits) == 2 and bits[0] in core_patterns.PATTERNS:
            out[name.strip()] = (bits[0], bits[1] if len(bits[1]) == 7 and bits[1].startswith("#") else "#000000")
    return out


def _styled_item(material):
    """The IfcStyledItem holding the material's surface style, or None."""
    for rep in material.HasRepresentation or ():
        for representation in rep.Representations or ():
            for item in representation.Items or ():
                if any(s.is_a("IfcSurfaceStyle") for s in item.Styles or ()):
                    return item
    return None


def _shading(material):
    item = _styled_item(material)
    for style in (item.Styles if item is not None else ()):
        for s in getattr(style, "Styles", None) or ():
            if s.is_a("IfcSurfaceStyleShading"):
                return s
    return None


def set_transparency(material, value):
    shading = _shading(material)
    if shading is not None and hasattr(shading, "Transparency"):
        shading.Transparency = float(min(max(value or 0.0, 0.0), 1.0))


def transparency(material):
    """Its surface style's transparency (0 … 1), or None when not given (a file made before 0.314)."""
    shading = _shading(material)
    value = getattr(shading, "Transparency", None) if shading is not None else None
    return None if value is None else float(value)


def _angle_unit(f):
    """Project angles in radians (1.0) or degrees (π/180 a degree): what one unit is, in radians."""
    try:
        unit = ifcopenshell.util.unit.get_project_unit(f, "PLANEANGLEUNIT")
        if unit is not None and unit.is_a("IfcConversionBasedUnit"):
            return math.pi / 180.0
    except Exception:            # (no unit assignment: radians, the IFC default)
        pass
    return 1.0


def _colour(f, rgb, name=None):
    r, g, b = rgb
    return f.create_entity("IfcColourRgb", Name=name, Red=float(r), Green=float(g), Blue=float(b))


def _hatchings(f, key, colour, layer, unit, angle_unit, pattern=None):
    """The IfcFillAreaStyleHatching of a pattern's families, in a colour (its layer's curve style). pattern (0.318): the
    pattern itself, when it is not the key's yet (a project's, being saved)."""
    pattern = pattern or core_patterns.get(key)
    if pattern is None:
        return []
    size = unit * (1.0 if pattern.model else 0.001)          # (a model pattern's m; a drafting one's mm)
    out = []
    for angle, x0, y0, shift, step, dashes in pattern.families:
        if dashes:
            pairs, pending = [], None
            for d in dashes:
                if d >= 0 and pending is None:
                    pending = d
                elif d < 0:
                    pairs.append((pending or 0.0, -d))
                    pending = None
            if pending is not None:
                pairs.append((pending, 1e-6))
            font = f.create_entity("IfcCurveStyleFont", Name=None, PatternList=[
                f.create_entity("IfcCurveStyleFontPattern", VisibleSegmentLength=float(a * size),
                                InvisibleSegmentLength=float(max(b * size, 1e-9))) for a, b in pairs])
        else:
            font = f.create_entity("IfcDraughtingPreDefinedCurveFont", Name="continuous")
        look = f.create_entity("IfcCurveStyle", Name=layer, CurveFont=font, CurveColour=_colour(f, rgb_of(colour)))
        if abs(shift) < 1e-12 and step > 0:
            start = f.create_entity("IfcPositiveLengthMeasure", float(step * size))
        else:
            length = math.hypot(shift, step)
            start = f.create_entity("IfcVector", Orientation=f.create_entity(
                "IfcDirection", DirectionRatios=(float(shift / length), float(step / length))),
                Magnitude=float(length * size))
        origin = f.create_entity("IfcCartesianPoint", Coordinates=(float(x0 * size), float(y0 * size))) \
            if abs(x0) > 1e-12 or abs(y0) > 1e-12 else None
        out.append(f.create_entity("IfcFillAreaStyleHatching", HatchLineAppearance=look, StartOfNextHatchLine=start,
                                   PointOfReferenceHatchLine=origin, PatternStart=None,
                                   HatchLineAngle=float(math.radians(angle) / angle_unit)))
    return out


def _fill_style(f, name, fg, bg, unit, angle_unit):
    """An IfcFillAreaStyle of a foreground and a background (each (pattern, colour) or None), or None for nothing."""
    styles, colour_used = [], False
    for layer, value in ((LAYERS[0], fg), (LAYERS[1], bg)):
        if value is None:
            continue
        key, colour = value
        if key == core_patterns.SOLID:
            if not colour_used:                               # (IFC: one colour; a solid foreground hides the rest)
                styles.append(_colour(f, rgb_of(colour), layer))
                colour_used = True
            if layer == LAYERS[0]:
                break
            continue
        styles += _hatchings(f, key, colour, layer, unit, angle_unit)
    if not styles:
        return None
    style = f.create_entity("IfcFillAreaStyle", Name=name, FillStyles=styles)
    pattern = core_patterns.get((fg or bg)[0])
    if hasattr(style, "ModelorDraughting") and pattern is not None:
        style.ModelorDraughting = bool(pattern.model)
    return style


def _remove(f, entity):
    try:
        ifcopenshell.util.element.remove_deep2(f, entity)
    except Exception:            # (an older IfcOpenShell: the style itself)
        f.remove(entity)


def write_patterns(f, material, spec, unit):
    """The material's surface and cut patterns as fill area styles beside its surface style (those of before
    replaced). unit: project units a metre."""
    item = _styled_item(material)
    if item is None:
        return
    kept = [s for s in item.Styles if not (s.is_a("IfcFillAreaStyle") and s.Name in STYLE_NAMES.values())]
    old = [s for s in item.Styles if s not in kept]
    angle_unit = _angle_unit(f)
    for which in ("surface", "cut"):
        style = _fill_style(f, STYLE_NAMES[which], getattr(spec, which + "_fg"), getattr(spec, which + "_bg"), unit,
                            angle_unit)
        if style is not None:
            kept.append(style)
    item.Styles = kept
    for style in old:
        if not f.get_inverse(style):
            _remove(f, style)


def read_patterns(material):
    """{field: (pattern, colour) or None} as kept in the material's parameter, or None when it has none (a file made
    before 0.314, or by another program: then what its fill area styles say, roughly — see read_foreign)."""
    for rel in getattr(material, "HasProperties", None) or ():
        if rel.is_a("IfcMaterialProperties") and rel.Name == PARAMS:
            for prop in rel.Properties or ():
                if prop.Name == GRAPHICS and getattr(prop, "NominalValue", None) is not None:
                    return decode(prop.NominalValue.wrappedValue)
    return None


def read_finish(material):
    """(0.343) Its finish in the render as kept in its parameter ("": its category's), or None when not kept."""
    for rel in getattr(material, "HasProperties", None) or ():
        if rel.is_a("IfcMaterialProperties") and rel.Name == PARAMS:
            for prop in rel.Properties or ():
                if prop.Name == FINISH and getattr(prop, "NominalValue", None) is not None:
                    value = str(prop.NominalValue.wrappedValue or "")
                    return "" if value == FINISH_AUTO else value
    return None


def read_foreign(material):
    """{field: …} from the fill area styles of a material made by another program — a solid background its colour,
    its hatchings a diagonal or crossed pattern in their colour —, or None when it has none."""
    item = _styled_item(material)
    found = None
    for style in (item.Styles if item is not None else ()):
        if not style.is_a("IfcFillAreaStyle"):
            continue
        which = "surface" if (style.Name == "Surface" or getattr(style, "ModelorDraughting", False)) else "cut"
        fg = bg = None
        angles, colour = set(), "#000000"
        for s in style.FillStyles or ():
            if s.is_a("IfcColourRgb"):
                value = (core_patterns.SOLID, hex_of((s.Red, s.Green, s.Blue)))
                if s.Name == LAYERS[0]:
                    fg = value
                else:
                    bg = value
            elif s.is_a("IfcFillAreaStyleHatching"):
                look = s.HatchLineAppearance
                c = getattr(look, "CurveColour", None)
                if c is not None and c.is_a("IfcColourRgb"):
                    colour = hex_of((c.Red, c.Green, c.Blue))
                angles.add(round(float(s.HatchLineAngle or 0.0), 3))
        if angles and fg is None and which == "cut":           # (a surface's hatching: its size not known here)
            fg = ("cross" if len(angles) > 1 else "diagonal", colour)
        found = found or {name: None for name in FIELDS}
        found[which + "_fg"], found[which + "_bg"] = fg, bg
    return found
