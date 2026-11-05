"""Ramps (0.101), mixed into IfcModel: a straight ramp — IfcRamp STRAIGHT_RUN_RAMP with its own body (IFC4 lets a
ramp that is not made of flights carry its shape): its side (the walking surface rising `rise` over its length,
the slab's thickness under it) extruded across its width, centred on its axis. Its material is the slab type's;
Pset_RampCommon.RequiredSlope keeps its slope; IsExternal false.

ArqSynth_Parametros: Elemento "ramp", Comprimento, Largura, Desnivel, Espessura (m) and Tipo (the slab type it
was drawn with). Its placement: the middle of its foot, its x along the axis — moving and turning it is moving its
placement, as for the other elements."""

import math

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from . import catalog
from .edit import EditRefused, MIN_SIZE

api = ifcopenshell.api
MIN_RISE = 0.0                 # a ramp may be flat (a landing drawn with the Ramp tool)


class RampMixin:
    def ramp_params(self, guid):
        """(start, end, width, rise, thickness) of a ramp made by this program: its axis from the middle of its
        foot (on the walking surface) to the middle of its head, at the foot's level."""
        e = self.by_guid(guid)
        p = self._params(e)
        m = self._placement_si(e)
        length = float(p["Comprimento"])
        start = m[:3, 3].copy()
        x = m[:3, 0] / np.linalg.norm(m[:3, 0])
        return start, start + x * length, float(p["Largura"]), float(p["Desnivel"]), float(p["Espessura"])

    def _set_ramp_body(self, ramp, length, width, rise, thickness):
        f, u = self.file, 1.0 / self.unit_scale
        self._clear_representations(ramp)
        side = [(0.0, 0.0), (length, rise), (length, rise - thickness), (0.0, -thickness)]
        profile = f.createIfcArbitraryClosedProfileDef("AREA", None, self._ring_curve(side))
        # the side drawn in the ramp's x-z plane (the position's z along -y), extruded across its width
        solid = f.createIfcExtrudedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, float(width / 2 * u), 0.0)),
                                                 f.createIfcDirection((0.0, -1.0, 0.0)),
                                                 f.createIfcDirection((1.0, 0.0, 0.0))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(width * u))
        body = f.createIfcShapeRepresentation(self.body, self.body.ContextIdentifier, "SweptSolid", [solid])
        api.geometry.assign_representation(f, product=ramp, representation=body)
        common = ifcopenshell.util.element.get_psets(ramp).get("Pset_RampCommon")
        pset = f.by_id(common["id"]) if common else api.pset.add_pset(f, product=ramp, name="Pset_RampCommon")
        api.pset.edit_pset(f, pset=pset, properties={"RequiredSlope": math.atan2(rise, length), "IsExternal": False})

    def add_ramp(self, spec, start, end, width, rise, name, lang="pt", storey=None):
        """A straight ramp from `start` (the middle of its foot, on the walking surface) to `end` (in plan; its
        head `rise` higher), `width` wide, as thick as the slab type `spec`. Returns the IfcRamp."""
        start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
        d = np.array((end[0] - start[0], end[1] - start[1], 0.0))
        length = float(np.linalg.norm(d))
        if length < MIN_SIZE or width < MIN_SIZE:
            raise EditRefused("too_small")
        f = self.file
        ramp = api.root.create_entity(f, ifc_class="IfcRamp", name=name, predefined_type="STRAIGHT_RUN_RAMP")
        x = d / length
        m = np.eye(4)
        m[:3, 0], m[:3, 1], m[:3, 3] = x, np.cross((0.0, 0.0, 1.0), x), start
        self._place(ramp, m)
        container = self.storey(storey) if storey is not None else self.storey_at(float(start[2]))
        api.spatial.assign_container(f, products=[ramp], relating_structure=container)
        if spec.layers:
            material = self._material(spec.layers[0][0], lang)
            api.material.assign_material(f, products=[ramp], type="IfcMaterial", material=material)
        self._set_ramp_body(ramp, length, float(width), float(rise), spec.thickness)
        self._mark(ramp, "ramp")
        self._set_params(ramp, {"Comprimento": length, "Largura": float(width), "Desnivel": float(rise),
                                "Espessura": spec.thickness, "Tipo": spec.key})
        return ramp

    def set_ramp(self, guid, length=None, width=None, rise=None):
        """A ramp's length (its foot stays), width or rise changed."""
        ramp, _ = self._require(guid, "ramp")
        p = self._params(ramp)
        length = float(p["Comprimento"]) if length is None else float(length)
        width = float(p["Largura"]) if width is None else float(width)
        rise = float(p["Desnivel"]) if rise is None else float(rise)
        if length < MIN_SIZE or width < MIN_SIZE:
            raise EditRefused("too_small")
        if rise < MIN_RISE:
            raise EditRefused("too_small")
        self._set_ramp_body(ramp, length, width, rise, float(p["Espessura"]))
        self._set_params(ramp, {"Comprimento": length, "Largura": width, "Desnivel": rise})

    def ramp_spec(self, guid):
        """The slab type a ramp was drawn with (its thickness and material), or None."""
        return catalog.BY_KEY.get(self._params(self.by_guid(guid)).get("Tipo") or "")
