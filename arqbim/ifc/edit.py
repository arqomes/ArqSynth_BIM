"""Parametric editing of elements made by ArqBIM (mixed into IfcModel).

Elements created by this program carry a small Pset ("ArqBIM_Parametros")
saying what they are; only those are edited parametrically (geometry is
regenerated from their parameters). Elements from other programs stay
read-only until we support their representations.

Every method here runs inside an IFC transaction opened by the caller
(model.document.IfcCommand), so it can be undone.
"""

import dataclasses
import importlib
import math

import numpy as np

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element

from ..core import classify
from ..core import joinery as core_joinery
from ..core.openings import EDGE_CLEARANCE, wall_frame
from ..core.walls import clear_range, footprint, is_square, joint
from . import catalog
from .services import segment_qto

for _m in ("attribute", "geometry", "material", "pset", "root", "style", "type"):
    importlib.import_module("ifcopenshell.api." + _m)
api = ifcopenshell.api

PARAM_PSET = "ArqSynth_Parametros"     # (0.77; until 0.76 "ArqBIM_Parametros": renamed when a file is opened)
LEGACY_PARAM_PSET = "ArqBIM_Parametros"
_CONNECTION = {"start": "ATSTART", "end": "ATEND", "path": "ATPATH"}
_CONNECTION_END = {v: k for k, v in _CONNECTION.items()}
MITRE_NAME = "MeiaEsquadria"    # (0.301) the Name of a right-angle corner mitred by hand (Revit's Wall Joins)


def is_mitred(rel):
    """(0.301) A joint made a mitre at a right angle (the others are mitred anyway)."""
    return (getattr(rel, "Name", None) or "") == MITRE_NAME


MARGIN = 0.01        # openings stick out of the faces by 1 cm (clean boolean cuts)
MIN_SIZE = 0.10      # m: smallest length / height an edit can leave


class NotEditable(ValueError):
    pass


class EditRefused(ValueError):
    """An edit that would break the model. `code` is translated by the interface."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def profile_size(profile):
    """(width, depth, area, perimeter) of a section, in the file's units: a rectangle, a circle (its diameter
    both ways), an L or a T (0.97: their outer sizes)."""
    if profile.is_a("IfcCircleProfileDef"):
        r = float(profile.Radius)
        return 2 * r, 2 * r, math.pi * r * r, 2 * math.pi * r
    from ..core import steel
    if steel.is_steel_profile(profile):                 # (0.494) a steel section: by its real outline
        found = steel.ifc_outline(profile)
        if found is not None:
            outer, holes, w, d = found
            area, perimeter = steel.area_and_perimeter(outer, holes)
            return w, d, area, perimeter
    if profile.is_a("IfcLShapeProfileDef"):
        w, d, t = float(profile.Width or profile.Depth), float(profile.Depth), float(profile.Thickness)
        return w, d, t * (w + d - t), 2 * (w + d)
    if profile.is_a("IfcTShapeProfileDef"):
        w, d = float(profile.FlangeWidth), float(profile.Depth)
        tf, tw = float(profile.FlangeThickness), float(profile.WebThickness)
        return w, d, w * tf + tw * (d - tf), 2 * (w + d)
    x, y = float(profile.XDim), float(profile.YDim)
    return x, y, x * y, 2 * (x + y)


def _translation(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


_ROT_Z_180 = np.diag((-1.0, -1.0, 1.0, 1.0))
RIGHT_HAND = {"pt": " (à direita)", "en": " (right-hand)"}     # the name of a door type hinged on the right
MIRRORED = {"pt": " (espelhada)", "en": " (mirrored)"}          # (0.289) a window type's mirror image
VARIANTS = tuple(RIGHT_HAND.values()) + tuple(MIRRORED.values())   # the endings of a type made from another


def _template_type(pset_name, prop):
    """IFC4's template type of a standard property ("P_SINGLEVALUE", "P_ENUMERATEDVALUE"…), or None."""
    import ifcopenshell.util.pset
    template = ifcopenshell.util.pset.get_template("IFC4").get_by_name(pset_name)
    found = next((p for p in (template.HasPropertyTemplates if template else ()) if p.Name == prop), None)
    return found.TemplateType if found is not None else None


def _hand(door):
    """"LEFT" / "RIGHT": the side a door's hinges are on (as seen along its +Y), from its type's
    operation (else its own); None for doors with no one side (double doors, revolving…)."""
    type_ = ifcopenshell.util.element.get_type(door)
    operation = (getattr(type_, "OperationType", None) or door.OperationType or "SINGLE_SWING_LEFT")
    if operation.startswith("DOUBLE_DOOR"):
        return None
    return "RIGHT" if operation.endswith("RIGHT") else "LEFT" if operation.endswith("LEFT") else None


def _with_hand(operation, hand):
    return operation[:-len("RIGHT")] + hand if operation.endswith("RIGHT") else \
        operation[:-len("LEFT")] + hand if operation.endswith("LEFT") else operation


_MISSING = object()


def _own_param(element, name):
    """(0.225) One of the program's parameters of an element, read straight from its own pset (get_psets makes
    every pset and quantity set of it into a dict): its value, or _MISSING when its own pset of ours has it not
    (then read as get_psets does: from its type too)."""
    for rel in getattr(element, "IsDefinedBy", None) or ():
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        pset = rel.RelatingPropertyDefinition
        if not pset.is_a("IfcPropertySet") or pset.Name != PARAM_PSET:
            continue
        for prop in pset.HasProperties or ():
            if prop.Name == name and prop.is_a("IfcPropertySingleValue"):
                return prop.NominalValue.wrappedValue if prop.NominalValue is not None else None
        return _MISSING
    return _MISSING


def _single_values(pset):
    """(0.287) A pset's values as get_psets gives them ({name: value, "id": its id}), or None when one of them is not
    a single value (then get_psets reads it)."""
    out = {}
    for prop in pset.HasProperties or ():
        if not prop.is_a("IfcPropertySingleValue"):
            return None
        out[prop.Name] = prop.NominalValue.wrappedValue if prop.NominalValue is not None else None
    out["id"] = pset.id()
    return out


class EditMixin:
    # ------------------------------------------------------------ marker

    def _mark(self, element, kind):
        pset = api.pset.add_pset(self.file, product=element, name=PARAM_PSET)
        api.pset.edit_pset(self.file, pset=pset, properties={"Elemento": kind})
        if self.created is not None:
            self.created.append(element.GlobalId)     # (a typical floor copies it, 0.90)
        if getattr(self, "made", None) is not None:
            self.made.append(element.GlobalId)        # (its storey's rooms are found again, 0.99)

    def kind_of(self, guid):
        """'wall' | 'slab' | 'column' | 'door' | 'window' for editable elements, else None. (0.225) Read straight
        from the program's pset (not all its psets made into dicts); in an edit (remembering()) once — an element's
        kind is set when it is made and never changes."""
        e = self.by_guid(guid)
        if e is None:
            return None
        scope = getattr(self, "_remember", None)
        kinds = scope.setdefault("kinds", {}) if scope is not None else None
        if kinds is not None and guid in kinds:
            return kinds[guid]
        kind = _own_param(e, "Elemento")
        if kind is _MISSING:                            # (no pset of ours on it: as get_psets reads it — a type's)
            kind = ifcopenshell.util.element.get_psets(e).get(PARAM_PSET, {}).get("Elemento")
        if kinds is not None and kind is not None:      # (none yet: being made — not remembered)
            kinds[guid] = kind
        return kind

    def _require(self, guid, *kinds):
        kind = self.kind_of(guid)
        if kind not in kinds:
            raise NotEditable(guid)
        return self.by_guid(guid), kind

    # ------------------------------------------------------------ representation helpers

    def _clear_representations(self, product):
        if not product.Representation:
            return
        for rep in list(product.Representation.Representations):
            api.geometry.unassign_representation(self.file, product=product, representation=rep)
            api.geometry.remove_representation(self.file, representation=rep)

    def _set_qto(self, product, name, values):
        qto = None
        for rel in getattr(product, "IsDefinedBy", None) or ():   # (0.287: found straight, not by get_psets)
            if rel.is_a("IfcRelDefinesByProperties"):
                definition = rel.RelatingPropertyDefinition
                if definition.is_a("IfcElementQuantity") and definition.Name == name:
                    qto = definition
                    break
        if qto is None and not hasattr(product, "IsDefinedBy"):        # (a type: as get_psets finds it)
            existing = ifcopenshell.util.element.get_psets(product).get(name)
            qto = self.file.by_id(existing["id"]) if existing else None
        if qto is None:
            qto = api.pset.add_qto(self.file, product=product, name=name)
        api.pset.edit_qto(self.file, qto=qto, properties=values)

    def _params(self, element):
        """The program's parameters of an element (ArqSynth_Parametros): (0.287) read straight from its own pset —
        get_psets makes every pset and quantity set of it into a dict, 5 ms on a wall with openings —, over its
        type's own when it has one (as get_psets merges them); a type, or an element without one of its own, or one
        with values that are not single: as get_psets reads it."""
        own = None
        for rel in getattr(element, "IsDefinedBy", None) or ():
            if rel.is_a("IfcRelDefinesByProperties"):
                pset = rel.RelatingPropertyDefinition
                if pset.is_a("IfcPropertySet") and pset.Name == PARAM_PSET:
                    own = _single_values(pset)
                    break
        if own is None:
            return ifcopenshell.util.element.get_psets(element).get(PARAM_PSET, {})
        for rel in getattr(element, "IsTypedBy", None) or ():
            for pset in getattr(rel.RelatingType, "HasPropertySets", None) or ():
                if pset.is_a("IfcPropertySet") and pset.Name == PARAM_PSET:
                    base = _single_values(pset)
                    if base is None:
                        return ifcopenshell.util.element.get_psets(element).get(PARAM_PSET, {})
                    base.update(own)
                    return base
        return own

    def _set_params(self, element, values):
        existing = ifcopenshell.util.element.get_psets(element).get(PARAM_PSET)
        pset = self.file.by_id(existing["id"]) if existing else api.pset.add_pset(self.file, product=element,
                                                                                    name=PARAM_PSET)
        api.pset.edit_pset(self.file, pset=pset, properties=dict(values))   # (a copy: IfcOpenShell empties it)

    def wall_cuts(self, wall):
        """(start, end) cut angles of a wall's ends in degrees (180 / 0 = square ends)."""
        if isinstance(wall, str):
            wall = self.by_guid(wall)
        p = self._params(wall)
        return float(p.get("CorteInicio", 180.0)), float(p.get("CorteFim", 0.0))

    def set_wall_cuts(self, guid, start=None, end=None):
        """Cut a wall's start and/or end at an angle (mitre corners, T junctions at
        an angle). The axis length and the quantities stay those of the axis."""
        wall, _ = self._require(guid, "wall")
        start_cut, end_cut = self.wall_cuts(wall)
        self._set_params(wall, {"CorteInicio": float(start_cut if start is None else start),
                                "CorteFim": float(end_cut if end is None else end)})
        length, height, thickness = self.wall_params(guid)
        self._set_wall_body(wall, length, height, thickness)

    def trim_frame(self, guid, frame):
        """A wall's frame limited to where it has its full thickness (its cut ends excluded)."""
        if frame is None or self.kind_of(guid) != "wall":
            return frame
        start_cut, end_cut = self.wall_cuts(guid)
        if is_square(start_cut, True) and is_square(end_cut, False):
            return frame
        length, _h, thickness = self.wall_params(guid)
        lo, hi = clear_range(length, thickness, start_cut, end_cut)
        return dataclasses.replace(frame, x0=lo, length=hi - lo)

    def _cut_wall_solid(self, length, height, thickness, start_cut, end_cut):
        """Extruded plan of a wall with angled ends (one SweptSolid, no booleans)."""
        f, u = self.file, 1.0 / self.unit_scale
        pts = [(float(x * u), float(y * u)) for x, y in footprint(length, thickness, start_cut, end_cut)]
        pts.append(pts[0])
        if f.schema == "IFC2X3":
            curve = f.createIfcPolyline([f.createIfcCartesianPoint(p) for p in pts])
        else:
            curve = f.createIfcIndexedPolyCurve(f.createIfcCartesianPointList2D(pts), None, False)
        solid = f.createIfcExtrudedAreaSolid(
            f.createIfcArbitraryClosedProfileDef("AREA", None, curve),
            f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)),
                                        f.createIfcDirection((0.0, 0.0, 1.0)), f.createIfcDirection((1.0, 0.0, 0.0))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(height * u))
        return f.createIfcShapeRepresentation(self.body, self.body.ContextIdentifier, "SweptSolid", [solid])

    def wall_profile(self, wall):
        """A wall's elevation profile (0.109): [(x along its axis, z above its base)] scaled to its length and
        height now, or None (a plain wall)."""
        parts = self.wall_profile_parts(wall)
        if parts is None:
            return None
        from ..core.curves import profile_outline
        return profile_outline(*parts)

    def wall_profile_parts(self, wall):
        """(0.375) A wall's profile as drawn: (its corners [(x, z)], its sides [None | arc | Bézier] — side i from
        corner i to corner i + 1, core/curves.side_of) scaled to its length and height now, or None (a plain
        wall)."""
        if isinstance(wall, str):
            wall = self.by_guid(wall)
        p = self._params(wall)
        if not p.get("Perfil"):
            return None
        q = ifcopenshell.util.element.get_psets(wall).get("Qto_WallBaseQuantities", {})
        s = self.unit_scale
        sx = q["Length"] * s / float(p["PerfilComprimento"]) if q.get("Length") else 1.0
        sz = q["Height"] * s / float(p["PerfilAltura"]) if q.get("Height") else 1.0
        return self._profile_parts(p, sx, sz)

    @staticmethod
    def _profile_parts(p, sx, sz):
        from ..core.curves import side_of
        pts = [tuple(float(v) for v in pair.split(",")) for pair in p["Perfil"].split(";") if pair]
        texts = str(p.get("PerfilLados") or "").split("|")
        sides = [side_of(texts[k] if k < len(texts) else "", sx, sz) for k in range(len(pts))]
        return [(x * sx, z * sz) for x, z in pts], sides

    @staticmethod
    def _profile_holes(p, sx, sz):
        """(0.410) The holes drawn in a wall's profile [[corners, sides]…] (core/outline_loops) stretched by (sx, sz)."""
        from ..core import outline_loops
        loops = outline_loops.parse(p.get("PerfilFuros")) if p.get("Perfil") else None
        return outline_loops.mapped(loops, lambda q: (q[0] * sx, q[1] * sz)) if loops else []

    def wall_profile_holes(self, wall):
        """(0.410) The holes drawn in a wall's profile — [[corners [(x, z)], sides]…], core/outline_loops — scaled to
        its length and height now ([]: none)."""
        if isinstance(wall, str):
            wall = self.by_guid(wall)
        p = self._params(wall)
        if not p.get("Perfil") or not p.get("PerfilFuros"):
            return []
        q = ifcopenshell.util.element.get_psets(wall).get("Qto_WallBaseQuantities", {})
        s = self.unit_scale
        sx = q["Length"] * s / float(p["PerfilComprimento"]) if q.get("Length") else 1.0
        sz = q["Height"] * s / float(p["PerfilAltura"]) if q.get("Height") else 1.0
        return self._profile_holes(p, sx, sz)

    def _scale_of(self, wall, length, height):
        p = self._params(wall)
        sx = length / float(p["PerfilComprimento"]) if p.get("PerfilComprimento") else 1.0
        sz = height / float(p["PerfilAltura"]) if p.get("PerfilAltura") else 1.0
        return p, sx, sz

    def _scaled_profile(self, wall, length, height):
        """The profile stretched to this length and height (as it was drawn for its own) — (0.375) its curved sides
        in pieces —, or None."""
        p, sx, sz = self._scale_of(wall, length, height)
        if not p.get("Perfil"):
            return None
        from ..core.curves import profile_outline
        return profile_outline(*self._profile_parts(p, sx, sz))

    def _scaled_holes(self, wall, length, height):
        """(0.410) The profile's holes stretched to this length and height, their curved sides in pieces."""
        from ..core import outline_loops
        p, sx, sz = self._scale_of(wall, length, height)
        return outline_loops.rings(self._profile_holes(p, sx, sz))

    def set_wall_profile(self, guid, points, sides=None, holes=None):
        """A wall's elevation drawn by its profile — [(x, z)] corners in its own frame, x from 0 to its length; (0.375)
        sides: each side straight (None), an arc or a Bézier (core/curves) — or plain again (None). Its height is
        the profile's top; a door / window must stay inside it.

        (0.410) holes: the holes drawn in it ([[corners, sides]…], core/outline_loops; [] none) — None keeps the
        ones it has (those still inside it)."""
        wall, _ = self._require(guid, "wall")
        length, _h, thickness = self.wall_params(guid)
        if points is None:
            pts = self.wall_profile(wall)
            height = max(z for _x, z in pts) if pts else _h
            self._set_params(wall, {"Perfil": None, "PerfilComprimento": None, "PerfilAltura": None,
                                    "PerfilLados": None, "PerfilFuros": None})
            self._set_wall_body(wall, length, height, thickness)
            return
        from ..core import outline_loops
        from ..core import slabs as core_slabs
        from ..core.curves import profile_outline, side_text
        pts = [(min(max(float(x), 0.0), length), max(float(z), 0.0)) for x, z in points]
        sides = list(sides or [])[:len(pts)]
        sides += [None] * (len(pts) - len(sides))
        outline = profile_outline(pts, sides)
        outline = [(min(max(x, 0.0), length), max(z, 0.0)) for x, z in outline]    # (a curve kept in the wall)
        poly = core_slabs.outline_polygon(outline)
        if poly is None:
            raise EditRefused("profile_bad")
        height = max(z for _x, z in outline)
        if height < MIN_SIZE - 1e-9:
            raise EditRefused("too_small")
        if holes is None:                           # (0.410) kept — those no longer inside the new profile let go
            holes = [h for h in outline_loops.rounded(self.wall_profile_holes(wall))
                     if core_slabs.outline_polygon(outline, outline_loops.rings([h])) is not None]
        else:
            holes = outline_loops.rounded(holes)
        if holes:
            poly = core_slabs.outline_polygon(outline, outline_loops.rings(holes))
            if poly is None:
                raise EditRefused("profile_bad")
        bounds = self.opening_bounds(guid)
        if bounds is not None:
            lo, hi = bounds
            from shapely.geometry import box as shapely_box
            if not poly.buffer(1e-6).contains(shapely_box(max(lo[0], 0.0), max(lo[2], 0.0), min(hi[0], length),
                                                          hi[2])):
                raise EditRefused("opening_outside")
        self._set_params(wall, {"Perfil": ";".join("{:.6f},{:.6f}".format(x, z) for x, z in pts),
                                "PerfilComprimento": length, "PerfilAltura": height,
                                "PerfilLados": "|".join(side_text(s) for s in sides) if any(sides) else None,
                                "PerfilFuros": outline_loops.text(holes) if holes else None})
        self._set_wall_body(wall, length, height, thickness)

    def _profile_wall_solid(self, points, thickness, holes=()):
        """A wall's body from its elevation profile: the outline in its x-z plane — (0.410) less its holes —
        extruded across its thickness (centred on its axis)."""
        f, u = self.file, 1.0 / self.unit_scale

        def curve_of(ring):
            coords = [(float(x * u), float(z * u)) for x, z in ring]
            coords.append(coords[0])
            if f.schema == "IFC2X3":
                return f.createIfcPolyline([f.createIfcCartesianPoint(p) for p in coords])
            return f.createIfcIndexedPolyCurve(f.createIfcCartesianPointList2D(coords), None, False)

        profile = f.createIfcArbitraryProfileDefWithVoids("AREA", None, curve_of(points),
                                                          [curve_of(h) for h in holes]) if holes else \
            f.createIfcArbitraryClosedProfileDef("AREA", None, curve_of(points))
        solid = f.createIfcExtrudedAreaSolid(       # (the position's z along -y: its y is the wall's z)
            profile,
            f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, float(thickness / 2 * u), 0.0)),
                                        f.createIfcDirection((0.0, -1.0, 0.0)), f.createIfcDirection((1.0, 0.0, 0.0))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(thickness * u))
        return f.createIfcShapeRepresentation(self.body, self.body.ContextIdentifier, "SweptSolid", [solid])

    def _set_wall_body(self, wall, length, height, thickness):
        u = 1.0 / self.unit_scale
        profile = self._scaled_profile(wall, length, height)
        if profile is not None:                     # (0.109) drawn by its elevation profile
            from ..core.slabs import ring_area
            holes = self._scaled_holes(wall, length, height)
            self._clear_representations(wall)
            api.geometry.assign_representation(self.file, product=wall,
                                               representation=self._profile_wall_solid(profile, thickness, holes))
            axis = api.geometry.add_axis_representation(self.file, context=self.axis,
                                                        axis=[(0.0, 0.0), (length, 0.0)])
            api.geometry.assign_representation(self.file, product=wall, representation=axis)
            area = ring_area(profile) - sum(ring_area(h) for h in holes)
            self._set_qto(wall, "Qto_WallBaseQuantities", {"Length": length * u, "Height": height * u,
                                                           "Width": thickness * u, "GrossVolume": area * thickness,
                                                           "GrossSideArea": area})
            return
        self._clear_representations(wall)
        start_cut, end_cut = self.wall_cuts(wall)
        if is_square(start_cut, True) and is_square(end_cut, False):
            body = api.geometry.add_wall_representation(self.file, context=self.body, length=length, height=height,
                                                        thickness=thickness, offset=-thickness / 2)
        else:
            body = self._cut_wall_solid(length, height, thickness, start_cut, end_cut)
        api.geometry.assign_representation(self.file, product=wall, representation=body)
        axis = api.geometry.add_axis_representation(self.file, context=self.axis, axis=[(0.0, 0.0), (length, 0.0)])
        api.geometry.assign_representation(self.file, product=wall, representation=axis)
        self._set_qto(wall, "Qto_WallBaseQuantities", {"Length": length * u, "Height": height * u,
                                                       "Width": thickness * u,
                                                       "GrossVolume": length * height * thickness})

    def _set_wall_height(self, wall, length, height, thickness):
        """(0.287) Only a wall's height changed: its body's one extrusion straight up made as deep — the same solid,
        not taken apart and made again (half the time of a group's change) —, its quantities. False when its body
        is not that (drawn by a profile, or by another program): then _set_wall_body."""
        if self._params(wall).get("Perfil") or wall.Representation is None:
            return False
        body = [r for r in wall.Representation.Representations if r.RepresentationIdentifier == "Body"]
        if len(body) != 1 or len(body[0].Items) != 1:
            return False
        solid = body[0].Items[0]
        if not solid.is_a("IfcExtrudedAreaSolid") or solid.Position is None:
            return False
        axis = solid.Position.Axis
        if axis is not None and tuple(round(float(c), 9) for c in axis.DirectionRatios) != (0.0, 0.0, 1.0):
            return False
        direction = tuple(float(c) for c in solid.ExtrudedDirection.DirectionRatios)
        if len(direction) != 3 or abs(direction[0]) > 1e-9 or abs(direction[1]) > 1e-9 or direction[2] <= 0:
            return False
        u = 1.0 / self.unit_scale
        solid.Depth = height * u / direction[2]
        self._set_qto(wall, "Qto_WallBaseQuantities", {"Length": length * u, "Height": height * u,
                                                       "Width": thickness * u,
                                                       "GrossVolume": length * height * thickness})
        return True

    def _set_slab_body(self, slab, x0, y0, x1, y1, thickness):
        u = 1.0 / self.unit_scale
        self._clear_representations(slab)
        body = api.geometry.add_slab_representation(self.file, context=self.body, depth=thickness,
                                                    polyline=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        api.geometry.assign_representation(self.file, product=slab, representation=body)
        lx, ly = x1 - x0, y1 - y0
        self._set_qto(slab, "Qto_SlabBaseQuantities", {"Width": thickness * u, "Length": lx * u,
                                                       "GrossArea": lx * ly, "GrossVolume": lx * ly * thickness,
                                                       "Perimeter": 2 * (lx + ly) * u})

    def _set_footing_body(self, footing, length, width, depth):
        """A footing's body (0.68): its plan rectangle (0, 0)-(length, width) extruded up `depth` (m);
        its layers stack up, like a slab's."""
        u = 1.0 / self.unit_scale
        usage = ifcopenshell.util.element.get_material(footing, should_skip_usage=False)
        if usage is not None and usage.is_a("IfcMaterialLayerSetUsage"):
            usage.LayerSetDirection = "AXIS3"
        self._clear_representations(footing)
        body = api.geometry.add_slab_representation(self.file, context=self.body, depth=depth,
                                                    polyline=[(0.0, 0.0), (length, 0.0), (length, width), (0.0, width)])
        api.geometry.assign_representation(self.file, product=footing, representation=body)
        self._set_qto(footing, "Qto_FootingBaseQuantities", {"Length": length * u, "Width": width * u,
                                                             "Height": depth * u, "GrossVolume": length * width * depth})

    def _set_column_body(self, column, profile, height):
        self._set_profile_body(column, profile, height, "Qto_ColumnBaseQuantities")

    def _set_profile_body(self, element, profile, length, qto, cardinal=5):
        """A column's, beam's, pipe's or duct's body: its section extruded `length` (m) along its placement's Z —
        (0.495) by one of IFC's cardinal points of the section (5: its middle, on the placement's Z)."""
        u, s = 1.0 / self.unit_scale, self.unit_scale
        self._clear_representations(element)
        body = api.geometry.add_profile_representation(self.file, context=self.body, profile=profile, depth=length,
                                                        cardinal_point=int(cardinal))
        self._apply_cuts(element, body, length)            # (0.496) its ends cut, its copes, as it keeps them
        api.geometry.assign_representation(self.file, product=element, representation=body)
        _w, _d, area, perimeter = profile_size(profile)
        area, perimeter = area * s * s, perimeter * s
        if qto in ("Qto_PipeSegmentBaseQuantities", "Qto_DuctSegmentBaseQuantities"):     # (their own names)
            values = {"Length": length * u, "GrossCrossSectionArea": area, "OuterSurfaceArea": perimeter * length}
        elif qto == "Qto_CableCarrierSegmentBaseQuantities":                                # (a conduit's, 0.146)
            values = {"Length": length * u, "CrossSectionArea": area, "OuterSurfaceArea": perimeter * length}
        else:
            values = {"Length": length * u, "CrossSectionArea": area, "GrossVolume": area * length}
            from ..core import steel
            if steel.is_steel_profile(profile):         # (0.494) a steel piece: its weight and its painted surface
                sec = steel.get(getattr(profile, "ProfileName", None))
                mass = steel.properties(sec.name)["mass"] if sec is not None else area * steel.DENSITY
                values.update({"NetWeight": mass * length, "GrossWeight": mass * length,
                               "OuterSurfaceArea": perimeter * length})
        self._set_qto(element, qto, values)

    def _set_filling_body(self, filling, kind, width, height, thickness):
        """A door's / window's body in a wall `thickness` thick: (0.288) made by its type's design (core/joinery) — its
        frame, leaves and glass, each in its material — with a door's plan symbol (drawn in plans instead of its
        cut: its jambs, its leaves open, their swing)."""
        u = 1.0 / self.unit_scale
        self._clear_representations(filling)
        self._set_joinery_body(filling, self.opening_design(filling), width, height, thickness)
        filling.OverallWidth, filling.OverallHeight = width * u, height * u
        self._set_qto(filling, "Qto_DoorBaseQuantities" if kind == "door" else "Qto_WindowBaseQuantities",
                      {"Width": width * u, "Height": height * u, "Area": width * height})      # (0.70)

    def _set_box_body(self, product, matrix, lo, hi):
        """Axis-aligned box (in the frame `matrix`) as the body of an opening — (0.294) the outline of the door's /
        window's arch in it, when it has one (core.joinery.outline), across from lo to hi."""
        self._clear_representations(product)
        size = np.asarray(hi, dtype=float) - np.asarray(lo, dtype=float)
        design = self._arched(product)
        if design is not None:
            body = self._outline_body(core_joinery.outline(design, size[0], size[2]), size[1])
        else:
            body = api.geometry.add_wall_representation(self.file, context=self.body, length=size[0], height=size[2],
                                                        thickness=size[1], offset=0.0)
        api.geometry.assign_representation(self.file, product=product, representation=body)
        self._place(product, matrix @ _translation(*lo))

    def _arched(self, opening):
        """(0.294) The design of the door / window filling an opening, when it is arched; else None."""
        if not opening.is_a("IfcOpeningElement"):
            return None
        for rel in opening.HasFillings or ():
            filling = rel.RelatedBuildingElement
            if filling.is_a("IfcDoor") or filling.is_a("IfcWindow"):
                design = self.opening_design(filling)
                return design if design.arch else None
        return None

    def _outline_body(self, ring, depth):
        """(0.294) A body: an outline in elevation ([(x, z)], m) extruded across, from y = depth to 0."""
        f, u = self.file, 1.0 / self.unit_scale
        pts = [(float(x * u), float(z * u)) for x, z in ring]
        profile = f.createIfcArbitraryClosedProfileDef("AREA", None, f.createIfcIndexedPolyCurve(
            f.createIfcCartesianPointList2D(pts + pts[:1]), None, False))
        # (its plane: x along, its y up — the placement's z points to −y, so that the extrusion goes across)
        place = f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, float(depth * u), 0.0)),
                                            f.createIfcDirection((0.0, -1.0, 0.0)), f.createIfcDirection((1.0, 0.0, 0.0)))
        solid = f.createIfcExtrudedAreaSolid(profile, place, f.createIfcDirection((0.0, 0.0, 1.0)), float(depth * u))
        return f.createIfcShapeRepresentation(self.body, self.body.ContextIdentifier, "SweptSolid", [solid])

    # ------------------------------------------------------------ measuring

    def element_frame(self, guid):
        verts, _ = self.triangulate([guid])[guid]
        return self.trim_frame(guid, wall_frame(self.placement(guid), verts))

    def _local_aabb(self, product, matrix):
        s = ifcopenshell.geom.settings()
        s.set("use-world-coords", True)
        shape = ifcopenshell.geom.create_shape(s, product)
        v = np.array(shape.geometry.verts, dtype=float).reshape(-1, 3) - self.origin   # program's coordinates
        local = (np.linalg.inv(matrix) @ np.column_stack((v, np.ones(len(v)))).T).T[:, :3]
        return local.min(axis=0), local.max(axis=0)

    def _openings_local(self, element, matrix):
        return [(rel.RelatedOpeningElement, *self._local_aabb(rel.RelatedOpeningElement, matrix))
                for rel in element.HasOpenings or ()]

    def add_wall_reveal(self, wall, side, vertical, at, width, depth, name):
        """(0.305, Revit's Wall Reveal) A groove in a straight wall's face — its left (side +1) or right —, `width`
        wide and `depth` deep: level, along the whole wall, its middle `at` over the wall's base; or vertical, up the
        whole wall, its middle `at` along it. An IfcOpeningElement RECESS of the wall, made again to fit whenever the
        wall changes (follow_reveals)."""
        self._require(wall, "wall")
        length, height, thickness = self.wall_params(wall)
        width, depth, at = float(width), float(depth), float(at)
        if not (0.005 - 1e-9 <= width <= 0.5 and 0.002 - 1e-9 <= depth <= thickness / 2 + 1e-9):
            raise EditRefused("reveal_size")
        if (at - width / 2 < -1e-6 or at + width / 2 > (length if vertical else height) + 1e-6):
            raise EditRefused("opening_outside")
        lo = np.array((at - width / 2 if vertical else 0.0, -thickness / 2, 0.0))       # (a first box: made below)
        opening = self.add_void(wall, self._placement_si(self.by_guid(wall)), lo,
                                lo + np.array((width, thickness, width)), name, recess=True)
        self._set_params(opening, {"Elemento": "reveal", "Lado": 1 if side > 0 else -1, "Vertical": bool(vertical),
                                   "Posicao": at, "Largura": width, "Profundidade": depth})
        self._set_reveal_body(opening, wall)
        return opening

    def _set_reveal_body(self, opening, wall):
        """A reveal's box made again from its parameters on its wall as it is now: level, past both ends (the wall's
        material alone is cut: a mitred corner too); vertical, where it is along the wall, past the base and top."""
        r = self.reveal_params(opening)
        length, height, thickness = self.wall_params(wall)
        m = self._placement_si(self.by_guid(wall))
        margin = 0.01
        y0, y1 = (thickness / 2 - r["depth"], thickness / 2 + margin) if r["side"] > 0 else \
            (-thickness / 2 - margin, -thickness / 2 + r["depth"])
        if r["vertical"]:
            local = np.linalg.inv(m) @ self._placement_si(opening)[:, 3]       # (it went with the wall)
            x0 = float(local[0])
            lo, hi = (x0, y0, -margin), (x0 + r["width"], y1, height + margin)
            self._set_params(opening, {"Posicao": x0 + r["width"] / 2})
        else:
            lo = (-thickness, y0, r["at"] - r["width"] / 2)
            hi = (length + thickness, y1, r["at"] + r["width"] / 2)
        size = np.asarray(hi, dtype=float) - np.asarray(lo, dtype=float)
        self._clear_representations(opening)
        body = api.geometry.add_wall_representation(self.file, context=self.body, length=size[0], height=size[2],
                                                    thickness=size[1], offset=0.0)
        api.geometry.assign_representation(self.file, product=opening, representation=body)
        t = np.eye(4)
        t[:3, 3] = lo
        self._place(opening, m @ t)

    def wall_reveals(self, wall):
        """(0.305) The reveals of a wall: [(opening GlobalId, its parameters)]."""
        e = self.by_guid(wall)
        out = []
        for rel in (getattr(e, "HasOpenings", None) or ()) if e is not None else ():
            r = self.reveal_params(rel.RelatedOpeningElement)
            if r is not None:
                out.append((rel.RelatedOpeningElement.GlobalId, r))
        return out

    def follow_reveals(self, changed):
        """(0.305) After walls changed: their reveals made again to fit them (longer, taller, thicker, split)."""
        for g in changed:
            if self.by_guid(g) is not None and self.kind_of(g) == "wall":
                for opening, _r in self.wall_reveals(g):
                    self._set_reveal_body(self.by_guid(opening), g)
        return []

    def remove_wall_reveal(self, wall, opening):
        """(0.305) A reveal of a wall taken away."""
        e = self.by_guid(opening)
        if e is None or self.reveal_params(e) is None:
            raise NotEditable(opening)
        api.root.remove_product(self.file, product=e)

    def reveal_params(self, opening):
        """(0.305) A reveal's {"side": +1 the wall's left face / −1 its right, "vertical", "at" (a level one: its middle
        over the wall's base; a vertical one: along the wall from its start), "width", "depth"}, or None when the
        opening is not a reveal."""
        if isinstance(opening, str):
            opening = self.by_guid(opening)
        if opening is None or not opening.is_a("IfcOpeningElement"):
            return None
        p = self._params(opening)
        if p.get("Elemento") != "reveal":
            return None
        return {"side": 1 if int(p.get("Lado") or 1) > 0 else -1, "vertical": bool(p.get("Vertical")),
                "at": float(p.get("Posicao") or 0.0), "width": float(p.get("Largura") or 0.02),
                "depth": float(p.get("Profundidade") or 0.01)}

    def opening_bounds(self, guid):
        """Smallest local box (lo, hi) that must stay inside the element because of
        its openings, or None. ((0.305) Its reveals left out: they are made again to fit.)"""
        e = self.by_guid(guid)
        boxes = [b for b in self._openings_local(e, self.placement(guid)) if self.reveal_params(b[0]) is None]
        if not boxes:
            return None
        return np.min([b[1] for b in boxes], axis=0), np.max([b[2] for b in boxes], axis=0)

    def voids(self, guid):
        """The openings and niches of a wall / slab as [(opening GlobalId, lo, hi, filled, box)]: the
        box round each in the element's local frame (m); filled: a door or window is in it; box: it
        is that box (not an outline drawn with slanted lines)."""
        e, m = self.by_guid(guid), self.placement(guid)
        s = ifcopenshell.geom.settings()
        s.set("use-world-coords", True)
        out = []
        for rel in e.HasOpenings or ():
            o = rel.RelatedOpeningElement
            shape = ifcopenshell.geom.create_shape(s, o)
            v = np.array(shape.geometry.verts, dtype=float).reshape(-1, 3) - self.origin
            local = (np.linalg.inv(m) @ np.column_stack((v, np.ones(len(v)))).T).T[:, :3]
            tris = local[np.array(shape.geometry.faces, dtype=np.int64).reshape(-1, 3)]
            volume = abs(float(np.einsum("ij,ij->i", tris[:, 0], np.cross(tris[:, 1], tris[:, 2])).sum())) / 6
            lo, hi = local.min(axis=0), local.max(axis=0)
            box_volume = float(np.prod(hi - lo))
            out.append((o.GlobalId, lo, hi, bool(o.HasFillings), abs(volume - box_volume) <= 1e-6 * max(box_volume, 1.0)))
        return out

    def resize_void(self, element_guid, opening_guid, lo, hi):
        """An empty opening or niche of a wall / slab becomes the box lo..hi of the element's local
        frame (m): one of its sides moved (Push/Pull on it)."""
        opening = self.by_guid(opening_guid)
        if opening is None or not opening.is_a("IfcOpeningElement") or (opening.HasFillings or ()):
            raise NotEditable(opening_guid)
        lo, hi = np.asarray(lo, dtype=float), np.asarray(hi, dtype=float)
        if np.any(hi - lo < 0.01 - 1e-9):
            raise EditRefused("too_small")
        self._set_box_body(opening, self.placement(element_guid), lo, hi)

    # ------------------------------------------------------------ walls, slabs, columns

    def resize_wall(self, guid, at_start=0.0, at_end=0.0, height=None, detach=True, at_base=0.0):
        """Lengthen/shorten a wall at its start and/or end and/or change its height; at_base: its
        base goes down by that much (negative: up), its top staying where it is. Doors and windows
        stay where they are. An end that moves leaves its joint (detach=False: the joint itself is
        moving it)."""
        wall, _ = self._require(guid, "wall")
        length, old_height, thickness = self.wall_params(guid)
        new_length = length + at_start + at_end
        new_height = (old_height if height is None else height) + at_base
        if new_length < MIN_SIZE - 1e-9 or new_height < MIN_SIZE - 1e-9:
            raise EditRefused("too_small")
        # (0.287) its openings measured only when it shrinks somewhere: made longer or taller none can be left out
        shrinks = at_start < 0 or at_end < 0 or at_base < 0 or new_height < old_height + at_base - 1e-12
        bounds = self.opening_bounds(guid) if shrinks else None     # local frame: x from the wall start, z from its base
        if bounds is not None:
            lo, hi = bounds
            if (lo[0] < -at_start - 1e-6 or hi[0] > length + at_end + 1e-6 or hi[2] + at_base > new_height + 1e-6
                    or lo[2] < -at_base - 1e-6):
                raise EditRefused("opening_outside")
        m = self._placement_si(wall)
        openings = [(rel.RelatedOpeningElement, self._placement_si(rel.RelatedOpeningElement))
                    for rel in wall.HasOpenings or ()]
        start_cut, end_cut = self.wall_cuts(wall)
        if (at_start and not is_square(start_cut, True)) or (at_end and not is_square(end_cut, False)):
            # an end that moves leaves its corner: it becomes square again
            self._set_params(wall, {"CorteInicio": 180.0 if at_start else start_cut,
                                    "CorteFim": 0.0 if at_end else end_cut})
        if at_start or at_end or at_base or not self._set_wall_height(wall, new_length, new_height, thickness):
            self._set_wall_body(wall, new_length, new_height, thickness)
        if at_start or at_base:
            m = m.copy()
            m[:3, 3] -= m[:3, 0] / np.linalg.norm(m[:3, 0]) * at_start + m[:3, 2] / np.linalg.norm(m[:3, 2]) * at_base
            self._place(wall, m)
            for opening, matrix in openings:   # openings are placed relative to the wall: put them back
                self._place(opening, matrix)
        if detach:
            for moved, kind in ((at_start, "ATSTART"), (at_end, "ATEND")):
                if abs(moved) > 1e-9:
                    api.geometry.disconnect_path(self.file, element=wall, connection_type=kind)
        if height is not None or at_base:
            self._retie_top(guid)

    def extend_wall(self, guid, at_start, at_end):
        self.resize_wall(guid, at_start, at_end)

    def followers(self, guid, at_start=0.0, at_end=0.0):
        """The walls joined at the ends of `guid` that move: [(guid, world move)] — those met at a corner or
        on their side go along with the end (moved, not turned), so that the joint stays (0.71)."""
        if not (at_start or at_end):
            return []
        s, e, _t = self.wall_axis(guid)
        d = (e - s) * np.array((1.0, 1.0, 0.0))
        d /= np.linalg.norm(d)
        moves = {"start": -d * at_start, "end": d * at_end}
        out = {}
        for _rel, through, through_end, butt, butt_end in self.wall_joints(guid):
            mine, other = (through_end, butt) if through == guid else (butt_end, through)
            move = moves.get(mine)
            if move is None or np.linalg.norm(move) < 1e-9 or self.kind_of(other) != "wall":
                continue
            os_, oe, _ot = self.wall_axis(other)
            od = (oe - os_) * np.array((1.0, 1.0, 0.0))
            od /= np.linalg.norm(od)
            if abs(d[0] * od[1] - d[1] * od[0]) < 1e-6:
                continue                           # in line with it: it stretches (the joint is made again)
            out[other] = move
        return list(out.items())

    def stretch_wall(self, guid, at_start=0.0, at_end=0.0):
        """Lengthen / shorten a wall keeping its joints (0.71, as Revit): the walls joined at an end that
        moves go along with it, and the walls joined to those stretch or shrink to meet them again."""
        followers = self.followers(guid, at_start, at_end)
        self.resize_wall(guid, at_start, at_end, detach=False)
        for other, move in followers:
            m = np.eye(4)
            m[:3, 3] = move
            self.transform(other, m)
        self.rejoin([guid] + [g for g, _m in followers])

    # ------------------------------------------------------------ wall joints

    def set_wall_end(self, guid, end, point, cut):
        """Bring a wall's "start" / "end" to `point` (on its axis line), cut at `cut` degrees."""
        s, e, _t = self.wall_axis(guid)
        d = (e - s) / np.linalg.norm(e - s)
        if end == "start":
            change = float((s - np.asarray(point, dtype=float))[:2].dot(d[:2]))
            self.resize_wall(guid, at_start=change, detach=False)
        else:
            change = float((np.asarray(point, dtype=float) - e)[:2].dot(d[:2]))
            self.resize_wall(guid, at_end=change, detach=False)
        current = self.wall_cuts(guid)[0 if end == "start" else 1]
        if abs(current - cut) > 1e-9:
            self.set_wall_cuts(guid, **{end: cut})

    def connect_walls(self, through, through_end, butt, butt_end, mitred=False):
        """Record a joint (IfcRelConnectsPathElements, as Revit / ArchiCAD do): `through`
        runs on (or is met at its side, "path"), `butt` stops against it. (0.301) mitred: a right-angle corner
        mitred (its Name says it: MITRE_NAME)."""
        rel = api.geometry.connect_path(self.file, relating_element=self.by_guid(through),
                                        related_element=self.by_guid(butt), relating_connection=_CONNECTION[through_end],
                                        related_connection=_CONNECTION[butt_end], description="ArqSynth BIM")
        if mitred and rel is not None:
            rel.Name = MITRE_NAME
        return rel

    def wall_joints(self, guid):
        """[(relation, through guid, its end, butt guid, its end)] of the joints a wall takes part in."""
        e = self.by_guid(guid)
        out = []
        for rel in list(getattr(e, "ConnectedTo", None) or ()) + list(getattr(e, "ConnectedFrom", None) or ()):
            if not rel.is_a("IfcRelConnectsPathElements"):
                continue
            ends = _CONNECTION_END.get(rel.RelatingConnectionType), _CONNECTION_END.get(rel.RelatedConnectionType)
            if None in ends or ends[1] == "path":
                continue                      # a kind of joint we do not make (e.g. from another program)
            out.append((rel, rel.RelatingElement.GlobalId, ends[0], rel.RelatedElement.GlobalId, ends[1]))
        return out

    def joined_walls(self, guids):
        """The walls joined to any of these (themselves excluded)."""
        found = {g for guid in guids for _r, a, _ea, b, _eb in self.wall_joints(guid) for g in (a, b)}
        return sorted(found - set(guids))

    def rejoin(self, guids):
        """Re-make the joints of these walls (after moving / rotating them or a
        thickness change): the walls joined to them stretch or shrink to meet
        them again. A joint that can no longer be made is removed."""
        rels = {}
        for guid in guids:
            for j in self.wall_joints(guid):
                rels[j[0].id()] = j
        for rel, through, through_end, butt, butt_end in rels.values():
            kinds = {self.kind_of(through), self.kind_of(butt)}
            if "curved_wall" in kinds and kinds <= {"wall", "curved_wall"} and through_end != "path":
                try:                                  # (0.189) a corner with a curved wall: the exact mitre
                    self._curved_corner(rel, through, through_end, butt, butt_end)
                except EditRefused:
                    self.file.remove(rel)             # (it cannot be made so: let go, as below)
                continue
            if through_end == "path" and self.kind_of(through) == "curved_wall" and self.kind_of(butt) == "wall":
                try:                                  # (0.246) a T at a curved wall's side
                    self._curved_tee(rel, through, butt, butt_end)
                except EditRefused:
                    self.file.remove(rel)
                continue
            if self.kind_of(through) != "wall" or self.kind_of(butt) != "wall":
                continue
            ts, te, t_through = self.wall_axis(through)
            bs, be, t_butt = self.wall_axis(butt)
            result = joint((ts, te), t_through, through_end, (bs, be), t_butt, butt_end, mitred=is_mitred(rel))
            try:
                if result is None:
                    raise EditRefused("joint")
                if result["through"] is not None:
                    self.set_wall_end(through, through_end, *result["through"])
                self.set_wall_end(butt, butt_end, *result["butt"])
            except EditRefused:
                self.file.remove(rel)         # they no longer meet: the walls stay as they are

    def slab_extents(self, guid):
        """(x0, y0, x1, y1, thickness) of a rectangular slab in its own frame."""
        f = self.element_frame(guid)
        thickness = f.z1 - f.z0
        slab = self.by_guid(guid)
        if slab is not None and self._slab_solid(slab) is None:     # (0.433) a sloped slab: its own, not its box's
            own = self._slab_thickness(slab)
            thickness = own if own is not None else thickness
        return f.x0, f.y0, f.x0 + f.length, f.y1, thickness

    def resize_slab(self, guid, x0, y0, x1, y1):
        slab, _ = self._require(guid, "slab")
        if self.slab_shape(guid) != "retangulo":       # (0.100: a polygon / circle changes by its outline)
            raise EditRefused("slab_outline_edit")
        *_, thickness = self.slab_extents(guid)
        if x1 - x0 < MIN_SIZE - 1e-9 or y1 - y0 < MIN_SIZE - 1e-9:
            raise EditRefused("too_small")
        bounds = self.opening_bounds(guid)
        if bounds is not None:
            lo, hi = bounds
            if lo[0] < x0 - 1e-6 or lo[1] < y0 - 1e-6 or hi[0] > x1 + 1e-6 or hi[1] > y1 + 1e-6:
                raise EditRefused("opening_outside")
        self._set_slab_body(slab, x0, y0, x1, y1, thickness)

    def resize_column(self, guid, height):
        column, _ = self._require(guid, "column")
        if height < MIN_SIZE - 1e-9:
            raise EditRefused("too_small")
        profile = ifcopenshell.util.element.get_material(column, should_skip_usage=True).MaterialProfiles[0].Profile
        self._set_column_body(column, profile, height)
        self._retie_top(guid)

    def resize_beam(self, guid, length=None, top=None):
        """A beam's length (its end moves along it) and / or the height of its top (0.66)."""
        beam, _ = self._require(guid, "beam")
        start, end, old_top, _w, height = self.beam_params(guid)
        length = float(np.linalg.norm((end - start)[:2])) if length is None else float(length)
        if length < MIN_SIZE - 1e-9:
            raise EditRefused("too_small")
        if top is not None:
            m = self._placement_si(beam)
            m[:3, 3] += np.array((0.0, 0.0, float(top) - old_top))
            self._place(beam, m)
        profile = ifcopenshell.util.element.get_material(beam, should_skip_usage=True).MaterialProfiles[0].Profile
        self._set_profile_body(beam, profile, length, "Qto_BeamBaseQuantities")

    # ------------------------------------------------------------ base and top constraints (0.73, as Revit's)

    def _height_of(self, e, kind):
        if kind == "wall":
            return self.wall_params(e.GlobalId)[1]
        q = ifcopenshell.util.element.get_psets(e).get("Qto_ColumnBaseQuantities", {})
        return q["Length"] * self.unit_scale if "Length" in q else self.element_frame(e.GlobalId).height

    def _retie_top(self, guid):
        """A wall / column tied to a storey by its top, made taller or moved by hand: its top offset follows
        (as Revit's), so the storey moving later keeps it where it is now."""
        e = self.by_guid(guid)
        kind = self.kind_of(guid)
        if kind not in ("wall", "column"):
            return
        params = self._params(e)
        top = params.get("TopoPavimento")
        storey = self.by_guid(top) if top else None                 # (0.287: its storey's level, not all of them)
        top_z = float(self._placement_si(e)[2, 3]) + self._height_of(e, kind)
        if storey is not None and storey.is_a("IfcBuildingStorey"):
            self._set_params(e, {"TopoDesvio": top_z - self._elevation(storey)})
        under = self._slab_underside(params.get("TopoLaje"))
        if under is not None:                       # (0.106) tied to a slab: its offset from the slab's underside
            self._set_params(e, {"TopoDesvio": top_z - under})

    def _slab_underside(self, slab_guid):
        """The level of a slab's underside (0.106), or None if there is no such slab."""
        if not slab_guid or self.by_guid(slab_guid) is None or self.kind_of(slab_guid) != "slab":
            return None
        info = self.slab_outline(slab_guid)
        return info["bottom"] if info is not None else self.element_frame(slab_guid).z0

    def constraints(self, guid):
        """A wall's or column's base and top, as Revit's: {"base": storey GlobalId, "base_offset": m above it,
        "top": storey GlobalId or None (not connected), "top_offset": m, "height": m}. The base is the storey
        it is in unless one was chosen; its offset is read from where it is."""
        e, kind = self._require(guid, "wall", "column")
        p = self._params(e)
        levels = {g: z for g, _n, z in self.storeys()}
        base = p.get("BasePavimento")
        if base not in levels:
            base = self.storey_of(guid)
        top = p.get("TopoPavimento") or None
        if top not in levels:
            top = None
        top_slab = p.get("TopoLaje") if self._slab_underside(p.get("TopoLaje")) is not None else None
        roof = p.get("TopoCobertura")
        top_roof = roof if roof and self.by_guid(roof) is not None and self.kind_of(roof) == "roof" else None
        base_z = float(self._placement_si(e)[2, 3])
        return {"base": base, "base_offset": base_z - levels.get(base, 0.0), "top": top, "top_slab": top_slab,
                "top_roof": top_roof,
                "top_offset": float(p.get("TopoDesvio", 0.0)) if (top or top_slab) else 0.0,
                "height": self._height_of(e, kind)}

    def set_constraints(self, guid, **changes):
        """New base / top for a wall or column (0.73): base (storey), base_offset, top (storey, or "" / None:
        not connected), top_offset, height (when not connected). It moves and changes height to match; it
        goes in its base storey. Refused if it would be too short or leave its doors/windows outside."""
        e, kind = self._require(guid, "wall", "column")
        c = self.constraints(guid)
        c.update({k: v for k, v in changes.items() if k in c})
        if "top" in changes:
            c["top_slab"] = None                    # (a storey, or not connected: no longer the slab's, 0.106)
        if changes.get("top_slab"):
            c["top"] = None
        levels = {g: z for g, _n, z in self.storeys()}
        if c["base"] not in levels:
            raise EditRefused("no_storey")
        top = c["top"] or None
        if top is not None and top not in levels:
            raise EditRefused("no_storey")
        under = self._slab_underside(c["top_slab"])
        if c["top_slab"] and under is None:
            raise EditRefused("no_slab")
        base_z = levels[c["base"]] + float(c["base_offset"])
        if under is not None:                       # (0.106) up to the slab's underside, with its offset
            height = under + float(c["top_offset"]) - base_z
        else:
            height = (levels[top] + float(c["top_offset"]) - base_z) if top else float(c["height"])
        if height < MIN_SIZE - 1e-9:
            raise EditRefused("too_small")
        old_z = float(self._placement_si(e)[2, 3])
        if kind == "wall":
            self.resize_wall(guid, height=height)
        else:
            self.resize_column(guid, height)
        if abs(base_z - old_z) > 1e-9:
            m = np.eye(4)
            m[2, 3] = base_z - old_z
            self.transform(guid, m)
        if self.storey_of(guid) != c["base"]:
            self.move_to_storey(guid, c["base"])
        tied = top or (c["top_slab"] if under is not None else None)
        self._set_params(e, {"BasePavimento": c["base"], "TopoPavimento": top,
                             "TopoLaje": c["top_slab"] if under is not None else None,
                             "TopoCobertura": None,                     # (0.112: not the roof's any more)
                             "TopoDesvio": float(c["top_offset"]) if tied else None})

    def layer_sense(self, guid):
        """(0.299) "POSITIVE" or "NEGATIVE" (flipped: its layers from its other face), the sense of an element's layer
        set usage, or None when it has none."""
        e = self.by_guid(guid)
        usage = ifcopenshell.util.element.get_material(e, should_skip_usage=False) if e is not None else None
        if usage is None or not usage.is_a("IfcMaterialLayerSetUsage"):
            return None
        return "NEGATIVE" if usage.DirectionSense == "NEGATIVE" else "POSITIVE"

    def _centre_layers(self, element, thickness, sense=None):
        """A wall's layers centred on its axis (its usage's offset), in their sense — (0.299) a flipped wall's
        (NEGATIVE) laid from its other face: the offset is then +t/2."""
        usage = ifcopenshell.util.element.get_material(element, should_skip_usage=False)
        if usage is None or not usage.is_a("IfcMaterialLayerSetUsage"):
            return
        if sense is not None and usage.DirectionSense != sense:
            usage.DirectionSense = sense
        sign = 1.0 if usage.DirectionSense == "NEGATIVE" else -1.0
        usage.OffsetFromReferenceLine = sign * thickness / 2 / self.unit_scale

    def top_tied(self, guid):
        """(0.298) What a wall's or column's top is tied to and follows: "slab", "roof", or None (a storey's level, or
        its own height)."""
        e = self.by_guid(guid)
        if e is None or self.kind_of(guid) not in ("wall", "column"):
            return None
        p = self._params(e)
        if p.get("TopoCobertura") and self.by_guid(p["TopoCobertura"]) is not None:
            return "roof"
        if self._slab_underside(p.get("TopoLaje")) is not None:
            return "slab"
        return None

    def detach_top(self, guid):
        """(0.298, Revit's Detach Top) A wall's or column's top no longer tied to a slab or roof: it keeps the height
        and the profile it has, and no longer follows it. False if it was tied to neither."""
        e, _kind = self._require(guid, "wall", "column")
        if self.top_tied(guid) is None:
            return False
        self._set_params(e, {"TopoLaje": None, "TopoCobertura": None, "TopoDesvio": None})
        return True

    def _support_top(self, guid):
        """(0.302) The level of the top face of a slab or a footing, or None if it is neither."""
        kind = self.kind_of(guid) if guid and self.by_guid(guid) is not None else None
        if kind == "slab":
            info = self.slab_outline(guid)
            return info["top"] if info is not None else self.element_frame(guid).z1
        if kind == "footing":
            return float(self.footing_params(guid)[4])
        return None

    def base_tied(self, guid):
        """(0.302) The slab or footing a wall's or column's base is tied to (it follows it), or None."""
        e = self.by_guid(guid)
        if e is None or self.kind_of(guid) not in ("wall", "column"):
            return None
        support = self._params(e).get("BaseLaje")
        return support if self._support_top(support) is not None else None

    def attach_base(self, guid, support):
        """(0.302, Revit's Attach Base) A wall's or column's base brought down (or up) to the top face of a slab or
        footing — its top staying where it is — and tied to it: it follows it when it changes."""
        e, kind = self._require(guid, "wall", "column")
        level = self._support_top(support)
        if level is None:
            raise EditRefused("no_slab")
        base = float(self._placement_si(e)[2, 3])
        height = self._height_of(e, kind)
        if base + height - level < MIN_SIZE - 1e-9:
            raise EditRefused("too_small")
        if abs(base - level) > 1e-9:
            if kind == "wall":
                self.resize_wall(guid, at_base=base - level)
            else:
                self.resize_column(guid, height + base - level)
                m = np.eye(4)
                m[2, 3] = level - base
                self.transform(guid, m)
        self._set_params(e, {"BaseLaje": support})

    def detach_base(self, guid):
        """(0.302, Revit's Detach Base) A wall's or column's base no longer tied to a slab or footing: it stays where
        it is. False if it was not tied."""
        e, _kind = self._require(guid, "wall", "column")
        if self.base_tied(guid) is None:
            return False
        self._set_params(e, {"BaseLaje": None})
        return True

    def follow_slab_bases(self, changed):
        """(0.302) After slabs or footings changed: the walls and columns tied to them by their base meet their top
        again. Looked for among their storeys' elements. Returns those that changed."""
        supports = [g for g in changed if self.kind_of(g) in ("slab", "footing")]
        if not supports:
            return []
        wanted, out = set(supports), []
        storeys = {self.storey_of(g) for g in supports}
        for storey in [s for s in storeys if s]:
            for guid in self.storey_elements(storey):
                if guid in changed or self.kind_of(guid) not in ("wall", "column"):
                    continue
                support = self._params(self.by_guid(guid)).get("BaseLaje")
                if support not in wanted:
                    continue
                before = float(self._placement_si(self.by_guid(guid))[2, 3])
                try:
                    self.attach_base(guid, support)
                except EditRefused:
                    continue                            # (it would be too short: left as it was)
                if abs(float(self._placement_si(self.by_guid(guid))[2, 3]) - before) > 1e-9:
                    out.append(guid)
        return out

    def slab_tops(self, slabs):
        """The walls and columns whose top is tied to any of these slabs (0.106)."""
        wanted, out = set(slabs), []
        if not wanted:                                  # (no slab changed: none read — every edit asks)
            return out
        for cls in ("IfcWall", "IfcColumn"):
            for e in self.file.by_type(cls):
                p = self._params(e)
                if p.get("Elemento") in ("wall", "column") and p.get("TopoLaje") in wanted:
                    out.append(e.GlobalId)
        return out

    def follow_slab_tops(self, changed):
        """After slabs changed (moved, another thickness, …): the walls and columns tied to them by their top
        take the height that keeps them tied (0.106). Returns those that changed."""
        out = []
        for guid in self.slab_tops([g for g in changed if self.kind_of(g) == "slab"]):
            if guid in changed:
                continue
            before = self.constraints(guid)["height"]
            try:
                self.set_constraints(guid)
            except EditRefused:
                continue                            # (the slab now under its base: left as it was)
            if abs(self.constraints(guid)["height"] - before) > 1e-9:
                out.append(guid)
        return out

    def constrained_to(self, storey_guid):
        """The walls and columns whose base or top is this storey (0.73: they follow when it moves)."""
        out = []
        for cls in ("IfcWall", "IfcColumn"):
            for e in self.file.by_type(cls):
                p = self._params(e)
                if p.get("Elemento") in ("wall", "column") and storey_guid in (p.get("BasePavimento"),
                                                                                 p.get("TopoPavimento")):
                    out.append(e.GlobalId)
        return out

    def refresh_constraints(self, storey_guid):
        """After a storey moved: the walls and columns tied to it by their top take the height that keeps
        them tied (those standing on it moved with it already)."""
        for guid in self.constrained_to(storey_guid):
            c = self.constraints(guid)
            if c["top"]:
                self.set_constraints(guid)

    def resize_segment(self, guid, length=None, z=None):
        """A pipe's or duct's length (its end moves along it) and / or the height of its axis (0.69). Joined
        to others (0.74): a new height takes the whole run along; a longer / shorter one moves what is
        connected after its end, so that they stay connected."""
        element, _ = self._require(guid, "pipe", "duct", "conduit")
        start, end, old_z = self.segment_params(guid)
        old_length = float(np.linalg.norm(end - start))           # (along it: sloped or vertical too, 0.136)
        length = old_length if length is None else float(length)
        if length < MIN_SIZE - 1e-9:
            raise EditRefused("too_small")
        whole = self.run(guid) if z is not None and abs(float(z) - old_z) > 1e-9 else []
        after = self.run(guid, through=1) if abs(length - old_length) > 1e-9 else []
        if z is not None:
            m = self._placement_si(element)
            m[:3, 3] += np.array((0.0, 0.0, float(z) - old_z))
            self._place(element, m)
        profile = ifcopenshell.util.element.get_material(element, should_skip_usage=True).MaterialProfiles[0].Profile
        qto = segment_qto(element)
        self._set_profile_body(element, profile, length, qto)
        self.update_segment_ports(guid)            # its ports at its ends again (0.74)
        moves = [(g, np.array((0.0, 0.0, float(z or 0.0) - old_z))) for g in whole]
        d = end - start
        moves += [(g, d / np.linalg.norm(d) * (length - old_length)) for g in after]
        for g, delta in moves:
            m = np.eye(4)
            m[:3, 3] = delta
            self.transform(g, m)

    def resize_footing(self, guid, length=None, top=None):
        """A footing's length (a strip's: its end moves along it) and / or the height of its top (0.68)."""
        footing, _ = self._require(guid, "footing")
        _c, _x, old_length, width, old_top = self.footing_params(guid)
        length = old_length if length is None else float(length)
        if length < MIN_SIZE - 1e-9:
            raise EditRefused("too_small")
        if top is not None:
            m = self._placement_si(footing)
            m[:3, 3] += np.array((0.0, 0.0, float(top) - old_top))
            self._place(footing, m)
        depth = ifcopenshell.util.element.get_psets(footing)["Qto_FootingBaseQuantities"]["Height"] * self.unit_scale
        self._set_footing_body(footing, length, width, depth)

    # ------------------------------------------------------------ columns tied to the grid (0.92)

    def tie_to_grid(self, guid, uids):
        """An element tied to the crossing of two grid axes (their uids, kept with the grid in the .arqsynthbim
        file): when the axes move, it goes along."""
        a, b = sorted(uids)
        self._set_params(self.by_guid(guid), {"EixoA": a, "EixoB": b})

    def grid_ties(self):
        """{GlobalId: frozenset of the two axes' uids} of the elements tied to a crossing."""
        out = {}
        for e in self.file.by_type("IfcColumn"):
            p = self._params(e)
            if p.get("EixoA") and p.get("EixoB"):
                out[e.GlobalId] = frozenset((p["EixoA"], p["EixoB"]))
        return out

    def tie_footing(self, footing, host):
        """A footing tied to the column or wall it is under (0.93): it goes with it."""
        self._set_params(self.by_guid(footing), {"Apoia": host})

    def footings_of(self, guids, combined=True):
        """{column / wall / pile cap GlobalId: [the footings (or piles, 0.94) tied to it]} for these elements —
        (0.249) a combined footing under each of its two columns (combined=False: left out)."""
        wanted, out = set(guids), {}
        for cls in ("IfcFooting", "IfcPile"):
            for e in self.file.by_type(cls):
                p = self._params(e)
                second = p.get("Apoia2")
                if second and not combined:
                    continue
                for host in (p.get("Apoia"), second):
                    if host and host in wanted:
                        out.setdefault(host, []).append(e.GlobalId)
        return out

    def tie_combined(self, footing, a, b):
        """(0.249) A combined footing tied to its two columns: made again under them when they move (Vao: the span
        between them it was made for — what goes past them is kept)."""
        span = float(np.linalg.norm((self.placement(b)[:3, 3] - self.placement(a)[:3, 3])[:2]))
        self._set_params(self.by_guid(footing), {"Apoia": a, "Apoia2": b, "Vao": span})

    def follow_combined_footings(self, changed):
        """(0.249) The combined footings under the columns among `changed` (moved, made another size): along,
        between and under them again, their size and type kept. Returns those that moved."""
        wanted, moved = set(changed), []
        for e in self.file.by_type("IfcFooting"):
            p = self._params(e)
            a, b = p.get("Apoia"), p.get("Apoia2")
            if not b or not (a in wanted or b in wanted) or self.by_guid(a) is None or self.by_guid(b) is None:
                continue
            ma, mb = self.placement(a), self.placement(b)
            d = (mb[:3, 3] - ma[:3, 3]) * np.array((1.0, 1.0, 0.0))
            span = float(np.linalg.norm(d))
            if span < 1e-6:
                continue
            _c, _x, length, width, old_top = self.footing_params(e.GlobalId)
            pad = length - float(p.get("Vao") or 0.0)           # (what goes past the columns: kept)
            depth = old_top - float(self.placement(e.GlobalId)[2, 3])
            x = d / span
            y = np.cross((0.0, 0.0, 1.0), x)
            top = min(float(ma[2, 3]), float(mb[2, 3]))
            centre = (ma[:3, 3] + mb[:3, 3]) / 2
            corner = np.array((centre[0], centre[1], top - depth)) - x * (span + pad) / 2 - y * width / 2
            self._set_footing_body(e, span + pad, width, depth)
            self._place(e, classify.placement(corner, x))
            self._set_params(e, {"Vao": span})
            moved.append(e.GlobalId)
        return moved

    def supports_of(self, guids):
        """Every footing and pile under these elements, tied to them or to one under them: {element: [them]} —
        (0.249) but the combined footings: they are made again under their columns, not moved with one."""
        out, todo, seen = {}, list(guids), set(guids)
        while todo:
            found = self.footings_of(todo, combined=False)
            todo = []
            for host, under in found.items():
                for g in under:
                    if g not in seen:
                        seen.add(g)
                        out.setdefault(host, []).append(g)
                        todo.append(g)
        return out

    # ------------------------------------------------------------ beams between columns (0.94)

    def column_box(self, guid):
        """(centre (x, y), its x direction (x, y), half sizes along its own x / y, base, top) of a column made
        by this program."""
        e = self.by_guid(guid)
        profile = ifcopenshell.util.element.get_material(e, should_skip_usage=True).MaterialProfiles[0].Profile
        s = self.unit_scale
        w, d, _area, _p = profile_size(profile)
        a, b = w * s / 2, d * s / 2
        m = self.placement(guid)
        x = m[:3, 0] / np.linalg.norm(m[:3, 0])
        base = float(m[2, 3])
        return m[:2, 3].copy(), x[:2].copy(), (a, b), base, base + self._height_of(e, "column")

    def column_section(self, guid):
        """(0.227) ("rect" | "circle" | "L" | "T", its legs' thickness in m — an L's, a T's web) of a column made by
        this program, from its profile."""
        e = self.by_guid(guid)
        profile = ifcopenshell.util.element.get_material(e, should_skip_usage=True).MaterialProfiles[0].Profile
        if profile.is_a("IfcCircleProfileDef"):
            return "circle", 0.0
        if profile.is_a("IfcLShapeProfileDef"):
            return "L", float(profile.Thickness) * self.unit_scale
        if profile.is_a("IfcTShapeProfileDef"):
            return "T", float(profile.WebThickness) * self.unit_scale
        return "rect", 0.0

    def steel_section(self, guid):
        """(0.494) The steel section (core/steel's name: «HEB200») of a column / beam made of one, or None."""
        from ..core import steel
        material = ifcopenshell.util.element.get_material(self.by_guid(guid), should_skip_usage=True)
        if material is None or not material.is_a("IfcMaterialProfileSet") or not material.MaterialProfiles:
            return None
        profile = material.MaterialProfiles[0].Profile
        if not steel.is_steel_profile(profile):
            return None
        sec = steel.from_ifc(profile, self.unit_scale)
        return sec.name if sec is not None else None

    def pile_diameter(self, guid):
        """(0.228) A pile's diameter (m), from its round profile (its larger side if not round)."""
        profile = ifcopenshell.util.element.get_material(self.by_guid(guid),
                                                         should_skip_usage=True).MaterialProfiles[0].Profile
        return max(profile_size(profile)[:2]) * self.unit_scale

    def beam_between(self, a, b):
        """(start, end, top) of a beam from column a to column b: from face to face, along the line between
        their middles; its top at the lower of their tops."""
        ca, xa, (ha, ka), _ba, ta = self.column_box(a)
        cb, xb, (hb, kb), _bb, tb = self.column_box(b)
        d = cb - ca
        span = float(np.linalg.norm(d))
        if span < 1e-9:
            return None
        d /= span

        def reach(x, h, k):
            return abs(float(x @ d)) * h + abs(float(x[0] * -d[1] + x[1] * d[0])) * k

        top = min(ta, tb)
        start, end = ca + d * reach(xa, ha, ka), cb - d * reach(xb, hb, kb)
        return np.array((start[0], start[1], top)), np.array((end[0], end[1], top)), top

    def tie_beam(self, guid, a, b):
        """A beam tied to the two columns it goes between: when they move, it follows (its ends at their faces)."""
        self._set_params(self.by_guid(guid), {"PilarA": a, "PilarB": b})

    def beams_of(self, columns):
        """{beam GlobalId: (column a, column b)} of the beams tied to any of these columns."""
        wanted, out = set(columns), {}
        if not wanted:                                  # (0.225: none asked)
            return out
        for e in self.file.by_type("IfcBeam"):
            p = self._params(e)
            if p.get("PilarA") in wanted or p.get("PilarB") in wanted:
                out[e.GlobalId] = (p.get("PilarA"), p.get("PilarB"))
        return out

    def set_beam_ends(self, guid, start, end):
        """A beam's new ends (plan), its top and section the same."""
        beam, _ = self._require(guid, "beam")
        _s, _e, top, _w, height = self.beam_params(guid)
        matrix, length = classify.beam_placement(start, end, top, height)
        if length < MIN_SIZE - 1e-9:
            raise EditRefused("too_small")
        self._place(beam, matrix)
        profile = ifcopenshell.util.element.get_material(beam, should_skip_usage=True).MaterialProfiles[0].Profile
        self._set_profile_body(beam, profile, length, "Qto_BeamBaseQuantities")

    TIE_KEYS = ("Apoia", "PilarA", "PilarB", "Viga", "Parede",      # (Parede: a wall's finish, 0.119)
                "Apoia2")                                          # (a combined footing's second column, 0.249)

    def remap_ties(self, copy_map, elsewhere=None):
        """Copies (copy_map: original -> copy) tied to elements: to their copies; else elsewhere(original) (a
        typical floor: the same element on the copy's storey); else no longer tied (a beam copied alone is not
        between those columns)."""
        for copy in copy_map.values():
            e = self.by_guid(copy)
            params = self._params(e)
            fix = {}
            for key in self.TIE_KEYS:
                ref = params.get(key)
                if ref:
                    new = copy_map.get(ref) or (elsewhere(ref) if elsewhere is not None else None)
                    if new != ref:
                        fix[key] = new
            ring = [g for g in (params.get("Vigas") or "").split(";") if g]    # (a slab in a bay, 0.96)
            if ring:
                new = [copy_map.get(g) or (elsewhere(g) if elsewhere is not None else None) for g in ring]
                fix["Vigas"] = ";".join(new) if all(new) else None
            if fix:
                self._set_params(e, fix)
            if "Parede" in fix:                       # (a finish copied with its wall: made on the copy, 0.119)
                if fix["Parede"]:
                    self._cladding_body(e)
                else:
                    self.remove_cladding(e)

    def follow_columns(self, columns, keep=()):
        """The beams tied to these columns (but those in `keep`, moving with them) made again between them — and
        the walls under them (0.95)."""
        moved = []
        for beam, (a, b) in self.beams_of(columns).items():
            if beam in keep or self.by_guid(a) is None or self.by_guid(b) is None:
                continue
            found = self.beam_between(a, b)
            if found is not None:
                self.set_beam_ends(beam, found[0], found[1])
                moved.append(beam)
        self.follow_beams(moved, keep)

    # ------------------------------------------------------------ walls under beams (0.95)

    def walls_of(self, beams):
        """{wall GlobalId: beam} of the walls tied to (under) any of these beams."""
        wanted, out = set(beams), {}
        if not wanted:                                  # (0.225: none asked — every move asks)
            return out
        for e in self.file.by_type("IfcWall"):
            beam = self._params(e).get("Viga")
            if beam in wanted:
                out[e.GlobalId] = beam
        return out

    def wall_under(self, beam):
        """(start, end, height) of a wall under a beam: along its axis, from face to face of its columns, its
        base at the lower of their bases (else the beam's storey), its top at the beam's underside."""
        start, end, top, _w, height = self.beam_params(beam)
        p = self._params(self.by_guid(beam))
        bases = [self.column_box(c)[3] for c in (p.get("PilarA"), p.get("PilarB")) if c and self.by_guid(c)]
        base = min(bases) if bases else self._elevation(self.storey(self.storey_of(beam)))
        a, b = np.array((start[0], start[1], base)), np.array((end[0], end[1], base))
        return a, b, (top - height) - base

    def set_wall_line(self, guid, start, end, height):
        """A wall made to run start -> end (its base at start's level), `height` tall; its thickness the same."""
        wall, _ = self._require(guid, "wall")
        _length, _height, thickness = self.wall_params(guid)
        box = classify.box_from_axis(np.asarray(start, dtype=float), np.asarray(end, dtype=float), thickness, height)
        matrix, length, h = classify.wall_from_box(box)
        if length < MIN_SIZE - 1e-9 or h < MIN_SIZE - 1e-9:
            raise EditRefused("too_small")
        self._place(wall, matrix)
        self._set_wall_body(wall, length, h, thickness)

    def follow_beams(self, beams, keep=()):
        """The walls under these beams (but those in `keep`) made again under them — and the slabs in the bays
        they close (0.96)."""
        for wall, beam in self.walls_of(beams).items():
            if wall in keep:
                continue
            a, b, height = self.wall_under(beam)
            if height >= MIN_SIZE and np.linalg.norm((b - a)[:2]) >= MIN_SIZE:
                self.set_wall_line(wall, a, b, height)
        for slab, ring in self.slabs_of(beams).items():
            if slab in keep:
                continue
            found = self.bay_rectangle(ring)
            if found is not None:
                self.set_slab_rect(slab, *found)
        self.follow_systems(beams, keep)

    # ------------------------------------------------------------ slabs in the bays of the beams (0.96)

    def slabs_of(self, beams):
        """{slab GlobalId: [its beams]} of the slabs made in a bay of any of these beams."""
        wanted, out = set(beams), {}
        if not wanted:                                  # (0.225: none asked)
            return out
        for e in self.file.by_type("IfcSlab"):
            ring = [g for g in (self._params(e).get("Vigas") or "").split(";") if g]
            if ring and wanted & set(ring):
                out[e.GlobalId] = ring
        return out

    def bay_rectangle(self, beams):
        """(x0, y0, x1, y1, top) of the slab in a bay closed by these beams — between their inner faces, its top
        at theirs — when they run along X and Y (a rectangle); else None."""
        lines = []
        for g in beams:
            if self.by_guid(g) is None:
                return None
            start, end, top, width, _h = self.beam_params(g)
            d = (end - start)[:2]
            if abs(d[0]) > 1e-6 and abs(d[1]) > 1e-6:
                return None                                # (not along X nor Y)
            lines.append(("x" if abs(d[0]) > abs(d[1]) else "y", float(start[1] if abs(d[0]) > abs(d[1])
                                                                       else start[0]), width / 2, top))
        across_x = sorted((at, half) for way, at, half, _t in lines if way == "y")     # beams along Y: x positions
        across_y = sorted((at, half) for way, at, half, _t in lines if way == "x")
        if len(across_x) < 2 or len(across_y) < 2:
            return None
        x0, x1 = across_x[0][0] + across_x[0][1], across_x[-1][0] - across_x[-1][1]
        y0, y1 = across_y[0][0] + across_y[0][1], across_y[-1][0] - across_y[-1][1]
        if x1 - x0 < MIN_SIZE or y1 - y0 < MIN_SIZE:
            return None
        return x0, y0, x1, y1, min(t for *_rest, t in lines)

    # ------------------------------------------------------------ beam systems (0.97)

    @staticmethod
    def system_lines(rect, way, mode, value):
        """The axes of a beam system in a bay: [(start, end)] (plan points) of the beams running along `way`
        ("x" / "y") in the rectangle (x0, y0, x1, y1): `value` of them evenly spaced (mode "count"), or one every
        `value` m from the first side (mode "spacing")."""
        x0, y0, x1, y1 = rect[:4]
        lo, hi = (y0, y1) if way == "x" else (x0, x1)
        span = hi - lo
        if mode == "count":
            n = max(int(value), 0)
            at = [lo + span * (k + 1) / (n + 1) for k in range(n)]
        else:
            step = float(value)
            at = []
            if step > MIN_SIZE:
                k = 1
                while lo + k * step < hi - MIN_SIZE / 2:
                    at.append(lo + k * step)
                    k += 1
        if way == "x":
            return [((x0, a), (x1, a)) for a in at]
        return [((a, y0), (a, y1)) for a in at]

    def systems_of(self, beams):
        """{beam GlobalId: (its bay's beams, its rule "way|mode|value|k")} of the beams of a system laid in a bay
        of any of these beams."""
        wanted, out = set(beams), {}
        if not wanted:                                  # (0.225: none asked)
            return out
        for e in self.file.by_type("IfcBeam"):
            p = self._params(e)
            ring = [g for g in (p.get("Vigas") or "").split(";") if g]
            if ring and p.get("Sistema") and wanted & set(ring):
                out[e.GlobalId] = (ring, p["Sistema"])
        return out

    def follow_systems(self, beams, keep=()):
        """The beams of the systems in the bays of these beams laid again (their k-th place in the bay as it is)."""
        for beam, (ring, rule) in self.systems_of(beams).items():
            if beam in keep:
                continue
            rect = self.bay_rectangle(ring)
            if rect is None:
                continue
            way, mode, value, k = rule.split("|")
            lines = self.system_lines(rect, way, mode, float(value))
            if int(k) < len(lines):
                (sx, sy), (ex, ey) = lines[int(k)]
                self.set_beam_ends(beam, np.array((sx, sy, rect[4])), np.array((ex, ey, rect[4])))
                if self.steel_section(beam) is not None:      # (0.508: a steel floor's — to the girders' webs)
                    self.steel_system_fit(beam)

    def set_slab_rect(self, guid, x0, y0, x1, y1, top):
        """A slab made the rectangle x0..x1 × y0..y1 (plan, along X / Y), its top at `top`; its thickness the
        same."""
        slab, _ = self._require(guid, "slab")
        *_xy, thickness = self.slab_extents(guid)
        m = np.eye(4)
        m[:3, 3] = (x0, y0, top - thickness)
        self._place(slab, m)
        self._set_slab_body(slab, 0.0, 0.0, x1 - x0, y1 - y0, thickness)

    def follow_grid(self, moves):
        """The tied elements moved with their crossing: {GlobalId: (dx, dy)}."""
        for guid, (dx, dy) in moves.items():
            m = np.eye(4)
            m[0, 3], m[1, 3] = dx, dy
            self.transform(guid, m)

    # ------------------------------------------------------------ the type editor (0.87)

    def save_type(self, spec, lang="pt", old=None):
        """A type made or changed in the type editor: the IFC type `spec` describes (its layers or its
        section, its name). old: the IFC type it replaces (GlobalId) — every element of that type gets the new
        one (thickness, section… follow, as set_element_type), the old one is removed and the new one keeps its
        GlobalId. Returns (the new type's GlobalId, the elements changed)."""
        old_type = self.by_guid(old) if old else None
        if old_type is not None:
            old_type.Name = "{} ~{}".format(old_type.Name or "", old_type.GlobalId)    # (out of the way of the name)
        type_ = self.ensure_type(spec, lang)
        if spec.kind == "footing":
            existing = ifcopenshell.util.element.get_psets(type_).get(PARAM_PSET)
            pset = self.file.by_id(existing["id"]) if existing else api.pset.add_pset(self.file, product=type_,
                                                                                        name=PARAM_PSET)
            values = {"PlantaX": float(spec.profile[0]), "PlantaY": float(spec.profile[1])}
            if spec.piles:                                # a pile cap's piles (0.94)
                values.update({"Estacas": int(spec.piles), "EstacaTipo": spec.pile,
                               "EstacaComprimento": float(spec.pile_length)})
            api.pset.edit_pset(self.file, pset=pset, properties=values)
        if spec.kind == "wall" and (spec.masonry or PARAM_PSET in ifcopenshell.util.element.get_psets(type_)):
            from ..core import ec6                        # (0.346) its own masonry, for Eurocode 6 ("": the project's)
            self._set_params(type_, {"Alvenaria": ec6.encode(spec.masonry)})
        changed = []
        if old_type is not None:
            changed = [e.GlobalId for e in ifcopenshell.util.element.get_types(old_type)]
            for g in changed:
                if self.kind_of(g) == "steel_member" and spec.section:      # (0.495) a steel piece: its new section
                    api.type.assign_type(self.file, related_objects=[self.by_guid(g)], relating_type=type_)
                    self.set_steel_member(g, lang=lang)
                elif self.kind_of(g) == spec.kind:
                    self.set_element_type(g, spec, lang)
                else:                                     # (one from another program: only its type changes)
                    api.type.assign_type(self.file, related_objects=[self.by_guid(g)], relating_type=type_)
            guid = old_type.GlobalId
            self.remove_type(old_type)
            type_.GlobalId = guid
        return type_.GlobalId, changed

    def save_opening_type(self, spec, lang="pt", old=None):
        """A door or window type made or changed in the type editor (0.88): its sizes kept in its
        ArqSynth_Parametros. old: the IfcDoorType / IfcWindowType it replaces — its doors / windows (hinged on
        either side) get the new size where they are (set_filling_type), the old types are removed and the new
        one keeps its GlobalId. Returns (GlobalId, the doors / windows changed)."""
        old_type = self.by_guid(old) if old else None
        olds = []
        if old_type is not None:
            names = {(old_type.Name or "") + suffix for suffix in VARIANTS}        # (0.289: a mirrored window's too)
            olds = [old_type] + [t for t in self.file.by_type(old_type.is_a()) if t.Name in names]
            for t in olds:
                t.Name = "{} ~{}".format(t.Name or "", t.GlobalId)
        type_ = self.ensure_opening_type(spec, lang)
        design = catalog.design_of(spec)
        self._set_params(type_, {"Largura": float(spec.width), "Altura": float(spec.height),
                                 "Peitoril": float(spec.sill),
                                 "Aro": float(design.depth if spec.kind == "window" else spec.lining_depth or 0.0),
                                 "Bandeira": float(spec.transom or 0.0)})
        self.set_opening_design(type_, design, spec.width, spec.height, lang)     # (0.288: its design, as made)
        changed = []
        for t in olds:
            for e in list(ifcopenshell.util.element.get_types(t)):
                changed.append(e.GlobalId)
                if self.kind_of(e.GlobalId) == spec.kind:
                    self.set_filling_type(e.GlobalId, spec, lang)
                else:
                    api.type.assign_type(self.file, related_objects=[e], relating_type=type_)
        if old_type is not None:
            guid = old_type.GlobalId
            for t in olds:
                self.remove_type(t)
            type_.GlobalId = guid
        return type_.GlobalId, changed

    # ------------------------------------------------------------ the materials window (0.89)

    def save_material(self, spec, lang="pt", old=None):
        """A material made or changed: its name, its category (what it is drawn with where cut), its style's
        colour, its density (Pset_MaterialCommon) and thermal conductivity (Pset_MaterialThermal). old: the
        IfcMaterial's name before (None: a new one). Returns the IfcMaterial."""
        name = spec.name_pt if lang == "pt" else spec.name_en
        material = next((m for m in self.file.by_type("IfcMaterial") if m.Name == old), None) if old else None
        if material is None:
            material = api.material.add_material(self.file, name=name, category=spec.category or None)
        material.Name = name
        material.Category = spec.category or None
        self.set_material_colour(material, spec.color)
        self.set_material_properties(material, spec)
        self.set_material_graphics(material, spec)         # (0.314)
        return material

    def set_material_graphics(self, material, spec, always=True):
        """(0.314) A material's transparency (its surface style's) and its surface and cut patterns (fill area styles
        beside it, and their keys in its ArqSynth_Parametros: ifc/material_graphics.py). always False (a catalogue
        material made as it is): the parameter only for patterns it has."""
        from . import material_graphics
        material_graphics.set_transparency(material, spec.transparency)
        material_graphics.write_patterns(self.file, material, spec, 1.0 / self.unit_scale)
        text = material_graphics.encode(spec)
        look = getattr(spec, "look", None)
        if look is not None or always:                     # (0.468: its realistic look, as others read it too)
            material_graphics.write_look(self.file, material, look, 1.0 / self.unit_scale)
        existing = ifcopenshell.util.element.get_psets(material).get(PARAM_PSET)
        if existing is None and not always and not any(getattr(spec, k) for k in material_graphics.FIELDS) and \
                look is None:
            return                                         # (nothing to keep: no parameter made for it)
        pset = self.file.by_id(existing["id"]) if existing else api.pset.add_pset(self.file, product=material,
                                                                                    name=PARAM_PSET)
        from ..core import pbr
        api.pset.edit_pset(self.file, pset=pset, properties={      # (0.343: its finish in the render)
            material_graphics.GRAPHICS: text, material_graphics.FINISH: spec.finish or material_graphics.FINISH_AUTO,
            material_graphics.REAL: self.file.create_entity("IfcText", pbr.encode(look))    # (0.468: long: a text)
            if look is not None else None})

    def set_material_colour(self, material, colour):
        """The colour of a material's surface style (made if it has none)."""
        r, g, b = (float(c) for c in colour)
        for rep in material.HasRepresentation or ():
            for representation in rep.Representations or ():
                for item in representation.Items or ():
                    for style in item.Styles or ():
                        for s in getattr(style, "Styles", None) or ():
                            if s.is_a("IfcSurfaceStyleShading") and s.SurfaceColour is not None:
                                s.SurfaceColour.Red, s.SurfaceColour.Green, s.SurfaceColour.Blue = r, g, b
                                return
        style = api.style.add_style(self.file, name=material.Name)
        api.style.add_surface_style(self.file, style=style, ifc_class="IfcSurfaceStyleShading",
                                    attributes={"SurfaceColour": {"Name": None, "Red": r, "Green": g, "Blue": b}})
        api.style.assign_material_style(self.file, material=material, style=style, context=self.body)

    def set_material_properties(self, material, spec):
        """Density and thermal conductivity, in IFC4's material property sets (None: left out)."""
        for pset_name, prop, value in (("Pset_MaterialCommon", "MassDensity", spec.density),
                                       ("Pset_MaterialThermal", "ThermalConductivity", spec.conductivity)):
            existing = ifcopenshell.util.element.get_psets(material).get(pset_name)
            if value is None and existing is None:
                continue
            pset = self.file.by_id(existing["id"]) if existing else api.pset.add_pset(self.file, product=material,
                                                                                        name=pset_name)
            api.pset.edit_pset(self.file, pset=pset, properties={prop: None if value is None else float(value)})

    def save_pattern(self, pattern, old=None):
        """(0.318) A fill pattern of the project's made or changed (old: the key it had), its definition in the IFC."""
        from . import pattern_defs
        for key in {old, pattern.key} - {None}:
            pattern_defs.remove(self.file, key)
        return pattern_defs.write(self.file, pattern, 1.0 / self.unit_scale)

    def remove_pattern(self, key):
        """(0.318) A fill pattern of the project's taken away (its materials then go without it)."""
        from . import pattern_defs
        pattern_defs.remove(self.file, key)

    def patterns(self):
        """(0.318) The project's own fill patterns, read from their definitions."""
        from . import pattern_defs
        return pattern_defs.read(self.file, 1.0 / self.unit_scale)

    def remove_material(self, name):
        """A material nothing uses (no layer, section, element nor type)."""
        material = next((m for m in self.file.by_type("IfcMaterial") if m.Name == name), None)
        if material is not None:
            api.material.remove_material(self.file, material=material)

    def remove_type(self, type_):
        """An IFC type no element uses, with its layer / profile set when nothing else uses it."""
        if isinstance(type_, str):
            type_ = self.by_guid(type_)
        material = ifcopenshell.util.element.get_material(type_)
        api.root.remove_product(self.file, product=type_)
        if material is not None and material.is_a() in ("IfcMaterialLayerSet", "IfcMaterialProfileSet") and \
                not self.file.get_inverse(material):
            api.material.remove_material_set(self.file, material=material)

    def set_element_type(self, guid, spec, lang="pt"):
        """Change the type of a wall / slab / column / beam / footing: thickness or section follow,
        and the doors, windows and voids in it are rebuilt to fit. (0.278) A roof: its layers and thickness."""
        if spec.kind == "roof":
            self.set_roof_type(guid, spec, lang)
            return
        if self.kind_of(guid) == "steel_member":            # (0.495) a steel piece: another section, as it is drawn
            self.set_steel_member(guid, spec=spec, lang=lang)
            return
        element, kind = self._require(guid, *((spec.kind, "curved_wall") if spec.kind == "wall" else (spec.kind,)))
        u = 1.0 / self.unit_scale
        type_ = self.ensure_type(spec, lang)
        if kind == "curved_wall":             # (0.103) its axis stays; the layers stay centred on it
            sense = self.layer_sense(guid)
            api.type.assign_type(self.file, related_objects=[element], relating_type=type_)
            self._centre_layers(element, spec.thickness, sense)
            self.set_curved_wall(guid, thickness=spec.thickness)
        elif kind == "wall":
            length, height, old_t = self.wall_params(guid)
            m = self._placement_si(element)
            before = self._openings_local(element, m)
            sense = self.layer_sense(guid)
            api.type.assign_type(self.file, related_objects=[element], relating_type=type_)
            new_t = spec.thickness
            self._centre_layers(element, new_t, sense)          # (0.299: a flipped wall stays flipped)
            self._set_wall_body(element, length, height, new_t)
            self._rebuild_openings(element, m, before, 1, (-old_t / 2, old_t / 2), (-new_t / 2, new_t / 2))
            self.rejoin([guid])               # corners follow the new thickness
        elif kind == "slab":
            x0, y0, x1, y1, old_t = self.slab_extents(guid)
            m = self._placement_si(element)
            before = self._openings_local(element, m)
            api.type.assign_type(self.file, related_objects=[element], relating_type=type_)
            new_t = spec.thickness
            m2 = m.copy()
            m2[:3, 3] += m[:3, 2] / np.linalg.norm(m[:3, 2]) * (old_t - new_t)   # the top of the slab stays put
            self._place(element, m2)
            if self.slab_shape(guid) == "retangulo":
                self._set_slab_body(element, x0, y0, x1, y1, new_t)
            else:                                      # (0.100: a polygon / circle keeps its plan)
                self.reshape_slab_thickness(element, new_t)
            # openings measured in the old frame, expressed in the new one (moved up by old_t - new_t)
            shift = np.array((0.0, 0.0, old_t - new_t))
            shifted = [(op, lo - shift, hi - shift) for op, lo, hi in before]
            self._rebuild_openings(element, m2, shifted, 2, (-(old_t - new_t), new_t), (0.0, new_t))
        elif kind == "footing":               # its middle and its top stay; its size and depth are the type's
            centre, x, length, width, top = self.footing_params(guid)
            api.type.assign_type(self.file, related_objects=[element], relating_type=type_)
            if spec.strip:
                width = spec.profile[0]
            else:
                length, width = spec.profile
            y = np.cross((0.0, 0.0, 1.0), x)
            corner = np.array((centre[0], centre[1], top - spec.thickness)) - x * length / 2 - y * width / 2
            m = np.eye(4)
            m[:3, 0], m[:3, 1], m[:3, 3] = x, y, corner
            self._place(element, m)
            self._set_footing_body(element, length, width, spec.thickness)
        elif kind in ("pipe", "duct", "conduit"):        # the axis stays where it is
            start, end, _z = self.segment_params(guid)
            api.type.assign_type(self.file, related_objects=[element], relating_type=type_)
            profile = ifcopenshell.util.element.get_material(type_).MaterialProfiles[0].Profile
            qto = segment_qto(element)
            self._set_profile_body(element, profile, float(np.linalg.norm(end - start)), qto)
        elif kind == "beam":                  # the top stays where it is: a deeper section hangs lower
            start, end, top, _w, old_h = self.beam_params(guid)
            api.type.assign_type(self.file, related_objects=[element], relating_type=type_)
            profile = ifcopenshell.util.element.get_material(type_).MaterialProfiles[0].Profile
            new_h = profile_size(profile)[1] * self.unit_scale
            m = self._placement_si(element)
            m[:3, 3] += np.array((0.0, 0.0, (old_h - new_h) / 2))
            self._place(element, m)
            self._set_profile_body(element, profile, float(np.linalg.norm((end - start)[:2])),
                                   "Qto_BeamBaseQuantities")
        else:
            height = self.element_frame(guid).height
            api.type.assign_type(self.file, related_objects=[element], relating_type=type_)
            profile = ifcopenshell.util.element.get_material(type_).MaterialProfiles[0].Profile
            self._set_column_body(element, profile, height)

    def _rebuild_openings(self, element, matrix, before, axis, old, new):
        """After a thickness change: openings keep their size and position along the
        element but span the new thickness; niches keep their depth from their face."""
        for opening, lo, hi in before:
            lo, hi = lo.copy(), hi.copy()
            if opening.PredefinedType == "RECESS":
                low_side = abs(lo[axis] - (old[0] - MARGIN)) < abs(hi[axis] - (old[1] + MARGIN))
                depth = min((hi[axis] - old[0]) if low_side else (old[1] - lo[axis]), new[1] - new[0])
                lo[axis], hi[axis] = ((new[0] - MARGIN, new[0] + depth) if low_side
                                      else (new[1] - depth, new[1] + MARGIN))
            else:
                lo[axis], hi[axis] = new[0] - MARGIN, new[1] + MARGIN
            self._set_box_body(opening, matrix, lo, hi)
            for rel in opening.HasFillings or ():
                filling = rel.RelatedBuildingElement
                if not filling.is_a("IfcDoor") and not filling.is_a("IfcWindow"):
                    continue                    # (0.188: a curtain wall stays as it is, its opening across the wall)
                side = self._filling_side(filling, matrix)
                self._place_filling(filling, matrix, lo[0], hi[0], lo[2], new, side)

    # ------------------------------------------------------------ doors and windows

    def _filling_side(self, filling, wall_matrix):
        x = self._placement_si(filling)[:3, 0]
        return -1 if float(np.dot(x, wall_matrix[:3, 0])) > 0 else 1

    def _place_filling(self, filling, wall_matrix, x_left, x_right, z, faces, side):
        kind = "door" if filling.is_a("IfcDoor") else "window"
        s = self.unit_scale
        width, height = filling.OverallWidth * s, filling.OverallHeight * s
        # (0.288: its frame as its type's design has it — no longer a window's frame 10 cm deep whatever its type)
        self._set_filling_body(filling, kind, width, height, faces[1] - faces[0])
        local = _translation(x_left, faces[0], z) if side < 0 else _translation(x_right, faces[1], z) @ _ROT_Z_180
        self._place(filling, wall_matrix @ local)

    def filling_state(self, guid):
        """Where a door/window is in its wall: dict with wall, frame, s (left edge
        along the wall), sill, width, height, side, kind — (0.188) or a curtain wall embedded in one."""
        e, kind = self._require(guid, "door", "window", "curtain_wall")
        if kind == "curtain_wall":
            if not e.FillsVoids:
                raise NotEditable(guid)
            return self.curtain_filling_state(guid)
        opening = e.FillsVoids[0].RelatingOpeningElement
        wall = opening.VoidsElements[0].RelatingBuildingElement
        if self.kind_of(wall.GlobalId) == "curved_wall":       # (0.177) the wall unrolled: x along its arc
            from .curved_walls import unrolled_frame
            p = self._params(opening)
            frame = unrolled_frame(*self.curved_wall_params(wall.GlobalId))
            along, width = float(p["AoLongo"]), float(p["Largura"])
            return {"wall": wall.GlobalId, "frame": frame, "opening": opening, "matrix": frame.matrix, "kind": kind,
                    "s": along - width / 2, "sill": float(p["Peitoril"]), "width": width,
                    "height": float(p["Altura"]), "side": int(p.get("Lado") or -1), "curved": True}
        m = self._placement_si(wall)
        frame = self.element_frame(wall.GlobalId)
        lo, hi = self._local_aabb(opening, m)
        return {"wall": wall.GlobalId, "frame": frame, "opening": opening, "matrix": m, "kind": kind,
                "s": float(lo[0]), "sill": float(lo[2] - frame.z0), "width": float(hi[0] - lo[0]),
                "height": float(hi[2] - lo[2]), "side": self._filling_side(e, m)}

    def _check_fits(self, st, s, sill, width, height):
        f = st["frame"]
        if s < f.x0 + EDGE_CLEARANCE - 1e-9 or s + width > f.x0 + f.length - EDGE_CLEARANCE + 1e-9:
            raise EditRefused("outside_wall")
        if sill < -1e-9 or sill + height > f.height + 1e-9:
            raise EditRefused("taller_than_wall")

    def move_filling(self, guid, s=None, sill=None):
        """Move a door/window along its wall (s = left edge) and/or change its sill."""
        st = self.filling_state(guid)
        s = st["s"] if s is None else s
        sill = st["sill"] if sill is None else sill
        if st.get("curtain"):                  # (0.188) an embedded curtain wall: anywhere in the wall, to its ends
            f, tol = st["frame"], 1e-6
            if s < f.x0 - tol or s + st["width"] > f.x0 + f.length + tol:
                raise EditRefused("outside_wall")
            if sill < -tol or sill + st["height"] > f.height + tol:
                raise EditRefused("taller_than_wall")
            self._refit_curtain(guid, st, s, sill)
            return
        self._check_fits(st, s, sill, st["width"], st["height"])
        self._refit_filling(guid, st, s, sill, st["width"], st["height"])

    def set_filling_type(self, guid, spec, lang="pt"):
        """Change a door/window type: new size, same left edge and sill."""
        st = self.filling_state(guid)
        if spec.kind != st["kind"]:
            raise NotEditable(guid)
        sill = st["sill"] if st["kind"] == "window" else 0.0
        self._check_fits(st, st["s"], sill, spec.width, spec.height)
        e = self.by_guid(guid)
        before = ifcopenshell.util.element.get_type(e)
        type_ = self.ensure_opening_type(spec, lang)
        if st["kind"] == "door" and _hand(e) == "RIGHT":
            type_ = self._door_type_with_hand(type_, "RIGHT", lang)          # a new size keeps its hinge side
        elif st["kind"] == "window" and before is not None and \
                any((before.Name or "").split(" ~")[0].endswith(s) for s in MIRRORED.values()):
            # (0.289) and a mirrored window, so — its type's name maybe with save_opening_type's " ~<id>" on
            type_ = self.mirrored_window_type(type_, lang)
        api.type.assign_type(self.file, related_objects=[e], relating_type=type_)
        if st["kind"] == "door":
            e.OperationType, e.UserDefinedOperationType = type_.OperationType, type_.UserDefinedOperationType
        else:                                           # (0.289: a window's too, its type's design's)
            e.PartitioningType, e.UserDefinedPartitioningType = type_.PartitioningType, type_.UserDefinedPartitioningType
        u = 1.0 / self.unit_scale
        e.OverallWidth, e.OverallHeight = spec.width * u, spec.height * u
        self._refit_filling(guid, st, st["s"], sill, spec.width, spec.height)

    def flip_door(self, guid, hinge=False, side=False, lang="pt"):
        """hinge: the hinges to the other jamb (it opens to the same side); side: it opens to the
        other side of the wall, hinges on the same jamb. A door's hinge side is its type's
        (IfcDoorType.OperationType …_LEFT / …_RIGHT): the right-hand one is "<type> (à direita)"."""
        st = self.filling_state(guid)
        e = self.by_guid(guid)
        if st["kind"] == "window" and side and not hinge:
            self.turn_window(guid, lang)
            # (0.297) turned by hand: the program no longer turns it to the outside
            self.set_property(guid, PARAM_PSET, "LadoManual", True)
            return
        if st["kind"] != "door" or _hand(e) is None:
            raise NotEditable(guid)
        if side:
            st["side"] = -st["side"]       # turned half round: it opens to the other side, hinged on the other jamb…
            hinge = not hinge              # …so the hinges change hands too, to stay on the same jamb
        if hinge:
            other = "RIGHT" if _hand(e) == "LEFT" else "LEFT"
            type_ = ifcopenshell.util.element.get_type(e)
            if type_ is not None:
                type_ = self._door_type_with_hand(type_, other, lang)
                api.type.assign_type(self.file, related_objects=[e], relating_type=type_)
            e.OperationType = _with_hand(e.OperationType or "SINGLE_SWING_LEFT", other)
        self._refit_filling(guid, st, st["s"], st["sill"], st["width"], st["height"])

    def turn_window(self, guid, lang="pt"):
        """(0.290) A window turned half round, to open to the other side — its peitoril to the other face —: its mirror
        image's type keeps its hinges on the same jamb."""
        st = self.filling_state(guid)
        e = self.by_guid(guid)
        st["side"] = -st["side"]
        type_ = ifcopenshell.util.element.get_type(e)
        other = self.mirrored_window_type(type_, lang) if type_ is not None else type_
        if other is not type_:
            api.type.assign_type(self.file, related_objects=[e], relating_type=other)
            e.PartitioningType, e.UserDefinedPartitioningType = \
                other.PartitioningType, other.UserDefinedPartitioningType
        self._refit_filling(guid, st, st["s"], st["sill"], st["width"], st["height"])

    def _door_type_with_hand(self, type_, hand, lang):
        """The door type like `type_` hinged on `hand` ("LEFT" / "RIGHT"): found by name or made — (0.288) the mirror
        image of `type_`'s design, with its sizes and fanlight (its parameters; the fanlight was lost before) and its
        materials."""
        operation = _with_hand(type_.OperationType or "SINGLE_SWING_LEFT", hand)
        if operation == type_.OperationType:
            return type_
        base = type_.Name or ""
        for suffix in RIGHT_HAND.values():
            if base.endswith(suffix):
                base = base[:-len(suffix)]
        name = base + (RIGHT_HAND.get(lang, RIGHT_HAND["en"]) if hand == "RIGHT" else "")
        for other in self.file.by_type("IfcDoorType"):
            if other.Name == name and other.OperationType == operation:
                return other
        new = api.root.create_entity(self.file, ifc_class="IfcDoorType", name=name, predefined_type="DOOR")
        params = {k: v for k, v in self._type_params(type_).items() if k not in ("id", "Desenho")}
        if params:
            self._set_params(new, params)
        width, height = self._opening_type_size(type_)
        design = core_joinery.mirrored(self.opening_design(type_))
        if core_joinery.door_operation(design)[0] != operation:      # (a design that is not one hand's mirror)
            design = core_joinery.standard("door", operation, core_joinery.transom_of(design, height))
        self.set_opening_design(new, design, width, height, lang=lang)
        return new

    def _opening_type_size(self, type_):
        """(0.288) A door / window type's size (width, height): its parameters', else a door's / window's of it, else
        its catalogue entry's."""
        params = self._type_params(type_)
        if params.get("Largura") and params.get("Altura"):
            return float(params["Largura"]), float(params["Altura"])
        for e in ifcopenshell.util.element.get_types(type_):
            if e.OverallWidth and e.OverallHeight:
                return float(e.OverallWidth) * self.unit_scale, float(e.OverallHeight) * self.unit_scale
        name = type_.Name or ""
        for suffix in VARIANTS:
            name = name[:-len(suffix)] if name.endswith(suffix) else name
        spec = next((o for o in catalog.OPENING_BY_KEY.values() if name in (o.name_pt, o.name_en)), None)
        return (spec.width, spec.height) if spec is not None else (0.90, 2.10)

    def _refit_filling(self, guid, st, s, sill, width, height):
        if st.get("curved"):                                   # (0.177) put again in the curved wall, s along it
            self._refit_curved_filling(guid, st, s, sill, width, height)
            return
        f, m = st["frame"], st["matrix"]
        z = f.z0 + sill
        self._set_box_body(st["opening"], m, (s, f.y0 - MARGIN, z), (s + width, f.y1 + MARGIN, z + height))
        self._place_filling(self.by_guid(guid), m, s, s + width, z, (f.y0, f.y1), st["side"])

    # ------------------------------------------------------------ attributes and properties

    def rename(self, guid, name):
        api.attribute.edit_attributes(self.file, product=self.by_guid(guid), attributes={"Name": name})

    def set_property(self, guid, pset_name, prop, value):
        """A property of an element, in its own property set — made if missing; if the set is its
        type's, the element gets its own (the type, shared by others, is not changed). An
        enumerated property (IFC4's templates) is written as one. (0.266) None: the property goes — and its set,
        if emptied (IFC wants a set to have one)."""
        e = self.by_guid(guid)
        own = {rel.RelatingPropertyDefinition.Name: rel.RelatingPropertyDefinition
               for rel in getattr(e, "IsDefinedBy", None) or ()
               if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.is_a("IfcPropertySet")}
        if value is None and pset_name not in own:
            return
        pset = own.get(pset_name) or api.pset.add_pset(self.file, product=e, name=pset_name)
        old = next((p for p in pset.HasProperties or () if p.Name == prop), None)
        enumerated = (old.is_a("IfcPropertyEnumeratedValue") if old is not None
                      else _template_type(pset_name, prop) == "P_ENUMERATEDVALUE")
        if enumerated and value is not None and not isinstance(value, (list, tuple)):
            value = [value]
        api.pset.edit_pset(self.file, pset=pset, properties={prop: value})
        if value is None and not pset.HasProperties:
            api.pset.remove_pset(self.file, product=e, pset=pset)
