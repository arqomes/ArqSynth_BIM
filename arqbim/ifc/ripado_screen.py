"""A free-standing slatted screen (0.441, the addon's «Ripado» with no wall behind it — «Apoio: Livre»), mixed into
IfcModel: a divider or a brise drawn by its line, as a wall — an IfcBuildingElementProxy (USERDEFINED «Ripado»), its
slats (upright or level, of a width and a thickness, at a pitch, centred) between its frame, its battens across them on
its back (core/surfaces.ripado_parts over its face, as the slatted finish's), each piece a box; of wood.

ArqSynth_Parametros: Elemento "ripado_screen", Comprimento, Altura, and the slatted
finish's measures (ifc/coverings.PATTERN_NAMES: Ripa, Intervalo, Sentido, Espessura, Moldura, Fixacoes,
FixacaoLargura, FixacaoEspessura). Its placement: its start at its base, x along its line (moved, turned or mirrored,
it stays as it is)."""

import numpy as np

import ifcopenshell.api

from ..core import surfaces as core_surfaces
from .coverings import PATTERN_NAMES, _pattern_of
from .edit import EditRefused

api = ifcopenshell.api
SCREEN = {"width": 0.04, "gap": 0.04, "direction": "vertical", "thickness": 0.04, "frame": 0.0, "battens": 0.0,
          "batten_w": 0.04, "batten_d": 0.02}


class RipadoScreenMixin:
    def screen_params(self, guid):
        """{start, end, length, height, and its pattern's measures} of a free-standing slatted screen."""
        e = self.by_guid(guid)
        p = self._params(e)
        d = dict(SCREEN)
        d.update(_pattern_of(p, "ripado"))
        d["thickness"] = float(p.get("Espessura") or SCREEN["thickness"])
        m = self._placement_si(e)
        x = m[:3, 0] / np.linalg.norm(m[:3, 0])
        length = float(p["Comprimento"])
        d.update(start=m[:3, 3].copy(), end=m[:3, 3] + x * length, length=length, height=float(p["Altura"]))
        return d

    def _screen_pieces(self, d):
        """(frame boxes, batten boxes, slat boxes) in its frame (x along, y across — its slats centred —, z up)."""
        from shapely.geometry import box
        d = dict(d)
        if d.get("direction") == "horizontal" and not float(d.get("frame") or 0.0) and \
                not int(round(float(d.get("battens") or 0.0))):
            d["battens"] = 2                          # (level slats with nothing to hold them: two posts behind)
        try:
            band, battens, slats, _inner = core_surfaces.ripado_parts(box(0.0, 0.0, d["length"], d["height"]), d)
        except ValueError:
            raise EditRefused("ripado_frame")
        t = float(d["thickness"])
        bd = float(d.get("batten_d") or 0.0) if battens else 0.0
        frames = []
        if band is not None:                          # (its four sides: top and bottom whole, the sides between)
            f, L, H = float(d["frame"]), d["length"], d["height"]
            frames = [(0.0, 0.0, L, f), (0.0, H - f, L, H), (0.0, f, f, H - f), (L - f, f, L, H - f)]
        frame_boxes = [(u0, -t / 2, v0, u1, t / 2 + bd, v1) for u0, v0, u1, v1 in frames]
        batten_boxes = [(q.bounds[0], t / 2, q.bounds[1], q.bounds[2], t / 2 + bd, q.bounds[3]) for q in battens]
        slat_boxes = [(u0, -t / 2, v0, u1, t / 2, v1) for u0, v0, u1, v1 in slats]
        return frame_boxes, batten_boxes, slat_boxes

    def _set_screen_body(self, element):
        d = self.screen_params(element.GlobalId)
        if d["length"] < 0.1 or d["height"] < 0.1:
            raise EditRefused("too_small")
        frames, battens, slats = self._screen_pieces(d)
        if len(slats) > core_surfaces.MAX_STRIPS:
            raise EditRefused("pattern_many")
        items = []
        for x0, y0, z0, x1, y1, z1 in frames + battens + slats:
            if min(x1 - x0, y1 - y0, z1 - z0) <= 1e-6:
                continue
            items.append(self._profile_solid([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z1 - z0, at=(0.0, 0.0, z0)))
        if not items:
            raise EditRefused("too_small")
        for rep in list(element.Representation.Representations if element.Representation else ()):
            api.geometry.unassign_representation(self.file, product=element, representation=rep)
            api.geometry.remove_representation(self.file, representation=rep)
        self._body(element, items)
        return len(slats)

    def add_ripado_screen(self, start, end, height, name, pattern=None, storey=None, lang="pt"):
        """(0.441) A free-standing slatted screen along start -> end (plan; its base at start's level), `height` high,
        its slats as `pattern` (the slatted finish's measures, ifc/coverings: width, gap, direction, thickness, frame,
        battens…). Returns the IfcBuildingElementProxy."""
        a, b = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
        b = np.array((b[0], b[1], a[2]))
        if np.linalg.norm((b - a)[:2]) < 0.1 or float(height) < 0.1:
            raise EditRefused("too_small")
        f = self.file
        element = api.root.create_entity(f, ifc_class="IfcBuildingElementProxy", name=name,
                                         predefined_type="USERDEFINED")
        element.ObjectType = "Ripado" if lang == "pt" else "Slatted screen"
        x = (b - a) / np.linalg.norm(b - a)
        m = np.eye(4)
        m[:3, 0], m[:3, 1], m[:3, 3] = x, np.cross((0.0, 0.0, 1.0), x), a
        self._place(element, m)
        self._contain(element, storey, a[2])
        api.material.assign_material(f, products=[element], type="IfcMaterial", material=self._material("madeira", lang))
        self._mark(element, "ripado_screen")
        values = {"Comprimento": float(np.linalg.norm((b - a)[:2])), "Altura": float(height)}
        values.update(self._pattern_changes(dict(SCREEN, **(pattern or {}))))
        self._set_params(element, values)
        self._set_screen_body(element)
        return element

    def set_ripado_screen(self, guid, height=None, **pattern):
        """(0.441) A slatted screen's length (its start stays), height or its slats' measures changed: made again."""
        element, _ = self._require(guid, "ripado_screen")
        values = {}
        length = pattern.pop("length", None)
        if length is not None:
            if float(length) < 0.1:
                raise EditRefused("too_small")
            values["Comprimento"] = float(length)
        if height is not None:
            if float(height) < 0.1:
                raise EditRefused("too_small")
            values["Altura"] = float(height)
        values.update(self._pattern_changes({k: v for k, v in pattern.items() if k in PATTERN_NAMES}))
        self._set_params(element, values)
        self._set_screen_body(element)
