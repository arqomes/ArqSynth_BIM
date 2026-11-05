"""(0.315) View styles, as Revit's visual styles and graphic display options: a named way of looking at the model, given
to views — how the faces are seen (shaded, in consistent colours without light, white, not at all, see-through), their
colours (each category's, as until 0.314, or each material's, layer by layer), the edges and how thick, the sun's
shadows, the materials' surface patterns (tiles, bricks…), their transparency (glass) and what is cut (each
material's own patterns, the project's graphic style by category, solid, empty).

The program's own (BUILTIN: the four looks of the 3D view since 0.63 and two more) cannot be changed; the project's
are made, named, duplicated, changed and deleted (ui/view_styles_dialog.py) and kept with the views in the
.arqsynthbim file. A view's "style" property is one of their keys: a built-in's name or a project style's uid.
Pure data (no Qt)."""

import uuid
from dataclasses import asdict, dataclass, field, replace

FACES = ("shaded", "consistent", "white", "none", "xray")
COLOURS = ("category", "material")
CUTS = ("material", "category", "solid", "empty")
EDGE_WIDTHS = (1.0, 1.5, 2.0, 3.0)        # px on screen
SUN_AZIMUTH, SUN_ALTITUDE = 213.0, 47.0   # (0.316) degrees: the shadows' sun unless a style says another
ALTITUDES = (5.0, 89.0)                   # its height above the horizon, at least / at most


@dataclass(frozen=True)
class ViewStyle:
    name: str
    faces: str = "shaded"                 # FACES
    colours: str = "category"             # COLOURS
    edges: bool = True
    edge_width: float = 1.5               # px
    shadows: bool = False
    patterns: bool = False                # the materials' surface patterns drawn on the faces
    transparency: bool = False            # the materials' transparency (glass seen through)
    cut: str = "material"                 # CUTS
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)
    # (0.316) where its sun shines from, for its shadows (in 3D and on paper): degrees from north towards east (180:
    # south), and above the horizon — from the south-south-west, fairly high
    sun_azimuth: float = SUN_AZIMUTH
    sun_altitude: float = SUN_ALTITUDE
    # (0.318) hatches by category, over the materials', as Revit's visibility / graphics overrides: ((IFC class,
    # cut foreground, cut background, surface foreground, surface background), …) — each (pattern, colour) or None
    categories: tuple = ()

    @property
    def builtin(self):
        return self.uid in BUILTIN

    def category(self, ifc_class):
        """(0.318) Its hatches for a category: (cut foreground, cut background, surface foreground, surface background),
        or None."""
        return next((tuple(c[1:5]) for c in self.categories if c[0] == ifc_class), None)

    def sun(self):
        """(0.316) The unit vector towards its sun."""
        from ..core.sun import direction
        return direction(self.sun_azimuth, self.sun_altitude)


# the program's: the 3D view's looks (0.63) as they were, and two more — keyed by their old names
BUILTIN = {                       # (0.317: the materials' surface patterns seen in the usual looks too, as in Revit)
    "shaded": ViewStyle("shaded", patterns=True, uid="shaded"),
    "hidden": ViewStyle("hidden", faces="white", patterns=True, uid="hidden"),
    "wire": ViewStyle("wire", faces="none", uid="wire"),
    "xray": ViewStyle("xray", faces="xray", uid="xray"),
    "consistent": ViewStyle("consistent", faces="consistent", colours="material", patterns=True, transparency=True,
                            uid="consistent"),
    "realistic": ViewStyle("realistic", colours="material", patterns=True, transparency=True, shadows=True,
                           edge_width=1.0, uid="realistic"),
}
DEFAULT = "shaded"


def label(style, translate):
    """A style's name as shown: a built-in's in the language (translate(key)), a project's its own."""
    return translate("vstyle.builtin." + style.uid) if style.builtin else style.name


def find(styles, key):
    """The style of a key (a built-in's name, a project style's uid) among the project's `styles`; a key not known:
    the usual (shaded)."""
    if key in BUILTIN:
        return BUILTIN[key]
    return next((s for s in styles or () if s.uid == key), BUILTIN[DEFAULT])


def known(styles, key):
    return key in BUILTIN or any(s.uid == key for s in styles or ())


def all_styles(styles):
    """The program's styles, then the project's."""
    return list(BUILTIN.values()) + list(styles or ())


def new_from(style, name):
    """A project style made from another (a built-in or the project's): the same settings, a new name and uid."""
    return replace(style, name=name, uid=uuid.uuid4().hex)


def to_dict(style):
    return asdict(style)


def from_dict(data):
    """A project style as read from the .arqsynthbim file (what is not understood: the usual), or None."""
    if not isinstance(data, dict) or not str(data.get("name") or "").strip():
        return None
    try:
        width = float(data.get("edge_width", 1.5))
    except (TypeError, ValueError):
        width = 1.5
    uid = str(data.get("uid") or uuid.uuid4().hex)
    if uid in BUILTIN:
        uid = uuid.uuid4().hex
    try:                                                     # (0.316) its sun
        azimuth = float(data.get("sun_azimuth", SUN_AZIMUTH)) % 360.0
        altitude = min(max(float(data.get("sun_altitude", SUN_ALTITUDE)), ALTITUDES[0]), ALTITUDES[1])
    except (TypeError, ValueError):
        azimuth, altitude = SUN_AZIMUTH, SUN_ALTITUDE
    categories = []                                          # (0.318) its hatches by category
    for item in data.get("categories") or ():
        if isinstance(item, (list, tuple)) and len(item) == 5 and isinstance(item[0], str) and item[0]:
            categories.append((item[0],) + tuple(_layer(x) for x in item[1:5]))
    return ViewStyle(str(data["name"]).strip(),
                     data.get("faces") if data.get("faces") in FACES else "shaded",
                     data.get("colours") if data.get("colours") in COLOURS else "category",
                     bool(data.get("edges", True)), min(max(width, 0.5), 6.0), bool(data.get("shadows", False)),
                     bool(data.get("patterns", False)), bool(data.get("transparency", False)),
                     data.get("cut") if data.get("cut") in CUTS else "material", uid, azimuth, altitude,
                     tuple(categories))


def _layer(value):
    """(pattern, colour) as read, or None."""
    if isinstance(value, (list, tuple)) and len(value) == 2 and isinstance(value[0], str) and value[0] \
            and isinstance(value[1], str) and len(value[1]) == 7 and value[1].startswith("#"):
        return value[0], value[1]
    return None
