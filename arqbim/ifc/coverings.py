"""Ceilings (0.118), mixed into IfcModel: an IfcCovering CEILING with its own body — its outline (a room's, or
drawn) at a height over the storey: one gypsum board (continuous) or its tiles on a 60 cm grid with the joints
showing; its holes (round a column) left out. Material: gypsum; Qto_CoveringBaseQuantities (Width, GrossArea,
NetArea), Pset_CoveringCommon.

ArqSynth_Parametros: Elemento "ceiling", Contorno and Furos (in its own frame: its placement at the outline's
lower left corner, at the ceiling's underside), Estilo (continuous / tiles), Espessura."""

import dataclasses
import math

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.owner
import ifcopenshell.guid
import ifcopenshell.util.element
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from ..core import ceilings as core_ceilings
from ..core import outline_loops
from ..core import surfaces as core_surfaces
from .edit import EditRefused

api = ifcopenshell.api
BOARD = 0.0125              # m: a gypsum board
TILE_THICKNESS = 0.015      # m
# (0.119) wall finishes (core_ceilings.FINISHES): key -> (material, thickness); (0.173) the patterned ones too —
# slats, flutes (wood), a perforated sheet (acoustic MDF)
CLADDINGS = {"azulejo": ("azulejo", 0.01), "reboco": ("reboco", 0.02), "pedra": ("pedra", 0.03),
             "ripado": ("madeira", 0.02), "canelado": ("madeira", 0.02), "perfurado": ("madeira", 0.016),
             "ondulado": ("madeira", 0.08)}            # (0.175: its thickness the wave's crest, as usual)
FLOORINGS = {"ceramico": ("azulejo", 0.02), "madeira": ("madeira", 0.02), "pedra": ("pedra", 0.03),   # (0.374)
             "vinilico": ("pvc", 0.005), "betao": ("concreto", 0.05)}      # key -> (material, thickness with its bed)
PATTERN_NAMES = {"width": "Ripa", "gap": "Intervalo", "direction": "Sentido", "diameter": "Furo", "pitch": "Passo",
                 "margin": "Margem", "amplitude": "Amplitude", "wavelength": "Onda", "shift": "Desfasamento",
                 "depth": "Fundo",
                 # (0.389) a perforated panel's: the holes' shape, their grid, the boards' size, the joint, a picture
                 "hole": "FormaFuro", "grid": "Malha", "sheet_w": "PainelLargura", "sheet_h": "PainelAltura",
                 "joint": "Junta", "mask": "Imagem",
                 # (0.540) free holes from the Visual Graph (core_surfaces.free_text), repeated board by board or not
                 "free": "FurosLivres", "free_repeat": "FurosRepetir",
                 # (0.434) a slatted panel's frame and battens (core_surfaces.ripado_parts); its slats' thickness
                 "frame": "Moldura", "battens": "Fixacoes", "batten_w": "FixacaoLargura",
                 "batten_d": "FixacaoEspessura", "thickness": "Espessura"}
TEXT_KEYS = {"direction", "hole", "grid", "mask", "free"}
CHOICES = {"direction": ("vertical", "horizontal"), "hole": core_surfaces.HOLE_SHAPES, "grid": core_surfaces.GRIDS}
REGION_NAMES = {"start": "Inicio", "end": "Fim", "base": "Base"}      # (0.389) a rectangle on the face (m)


def _pattern_of(p, finish):
    """A patterned finish's measures from its parameters (p: its pset), the pattern's usual ones where not given."""
    d = dict(core_surfaces.DEFAULTS.get(finish, {}))
    for key, name in PATTERN_NAMES.items():
        if p.get(name) is not None:
            d[key] = str(p[name]) if key in TEXT_KEYS else float(p[name])
    return d


def _framed(d):
    """(0.434) A slatted finish with a frame round it or battens behind it (else its slats alone, as before)."""
    return float(d.get("frame") or 0.0) > 1e-9 or int(round(float(d.get("battens") or 0.0))) > 0


def _mask(d):
    """(0.389) The picture of a perforated panel's holes (its darkness), or None."""
    if not d.get("mask"):
        return None
    from ..model import image_masks
    return image_masks.load(d["mask"])


def _free(d):
    """(0.540) (shape, holes) of a perforated finish's free holes (the Visual Graph's), or None."""
    return core_surfaces.free_read(d.get("free") or "")


def _perforation(face, d):
    """(0.389) core_surfaces.perforation with a finish's measures (0.540: or its free holes)."""
    free = _free(d)
    if free is not None:
        return core_surfaces.free_perforation(face, free[0], free[1], d["margin"], (d["sheet_w"], d["sheet_h"]),
                                              float(d.get("free_repeat", 1.0)) > 0.5)
    return core_surfaces.perforation(face, d["diameter"], d["pitch"], d["margin"], (d["sheet_w"], d["sheet_h"]),
                                     d["joint"], d["grid"], _mask(d))
LIGHTS = core_ceilings.LIGHTS


def _pts(text):
    return [tuple(float(v) for v in pair.split(",")) for pair in (text or "").split(";") if pair]


def _text(pts):
    return ";".join("{:.6f},{:.6f}".format(x, y) for x, y in pts)


class CoveringMixin:
    def ceiling_params(self, guid):
        e = self.by_guid(guid)
        p = self._params(e)
        m = self._placement_si(e)
        local = _pts(p.get("Contorno"))
        holes = [_pts(h) for h in (p.get("Furos") or "").split("|") if h]
        world = lambda pts: [tuple((m @ np.array((x, y, 0.0, 1.0)))[:2]) for x, y in pts]      # noqa: E731
        # (0.410) as drawn — the outline and its holes, their sides arcs or curves — while it still is this one
        loops = outline_loops.drawn([local] + holes, p.get("Desenho")) if len(local) >= 3 else []
        return {"outline": world(local), "holes": [world(h) for h in holes], "local": local, "local_holes": holes,
                "style": p.get("Estilo") or "continuous", "thickness": float(p.get("Espessura") or BOARD),
                "z": float(m[2, 3]),
                "loops": outline_loops.mapped(loops, lambda q: tuple(float(c) for c in world([q])[0]))}

    def set_covering_outline(self, guid, loops):
        """(0.410) A ceiling's or a floor finish's plan made these loops (core/outline_loops, program's coordinates):
        its outline and its holes as drawn, their sides arcs or Bézier curves — kept in pieces in «Contorno» /
        «Furos» (what the body and everything else read) and as drawn in «Desenho»."""
        covering, kind = self._require(guid, "ceiling", "flooring")
        m = self._placement_si(covering)
        inv = np.linalg.inv(m)
        local = outline_loops.rounded(outline_loops.mapped(
            loops, lambda q: tuple(float(c) for c in (inv @ np.array((q[0], q[1], m[2, 3], 1.0)))[:2])))
        rings = outline_loops.rings(local)
        if not rings or outline_loops.polygon(local) is None:
            raise EditRefused("slab_outline")
        self._set_params(covering, {"Contorno": _text(rings[0]), "Furos": "|".join(_text(h) for h in rings[1:]),
                                    "Desenho": outline_loops.text(local) if outline_loops.curved(local) else None})
        if kind == "ceiling":
            self._set_ceiling_body(covering)
        else:
            self._set_flooring_body(covering)

    def set_flooring(self, guid, finish, lang="pt"):
        """(0.415) A floor finish's finish changed: its material and thickness (with its bed) the new one's, its body
        again."""
        floor, _ = self._require(guid, "flooring")
        if finish not in FLOORINGS:
            raise EditRefused("not_editable")
        material, thickness = FLOORINGS[finish]
        self._set_params(floor, {"Acabamento": finish, "Espessura": thickness})
        wanted = self._material(material, lang)
        if ifcopenshell.util.element.get_material(floor) != wanted:
            api.material.unassign_material(self.file, products=[floor])
            api.material.assign_material(self.file, products=[floor], type="IfcMaterial", material=wanted)
        self._set_flooring_body(floor)

    def _set_flooring_body(self, floor):
        """(0.374) A floor finish's body: its plan («Contorno», «Furos») its finish's thickness thick, and its
        quantities."""
        f, u = self.file, 1.0 / self.unit_scale
        p = self._params(floor)
        local = _pts(p.get("Contorno"))
        local_holes = [_pts(h) for h in (p.get("Furos") or "").split("|") if h]
        thickness = float(p.get("Espessura") or FLOORINGS["ceramico"][1])
        poly = Polygon(local, local_holes).buffer(0)
        if poly.is_empty or poly.area < 0.01:
            raise EditRefused("too_small")
        items = []
        for q in getattr(poly, "geoms", [poly]):
            q = orient(q, 1.0)
            outer = self._ring_curve(list(q.exterior.coords)[:-1])
            inner = [self._ring_curve(list(h.coords)[:-1]) for h in q.interiors]
            profile = f.createIfcArbitraryProfileDefWithVoids("AREA", None, outer, inner) if inner else \
                f.createIfcArbitraryClosedProfileDef("AREA", None, outer)
            items.append(f.createIfcExtrudedAreaSolid(
                profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)), None, None),
                f.createIfcDirection((0.0, 0.0, 1.0)), float(thickness * u)))
        self._clear_representations(floor)
        api.geometry.assign_representation(f, product=floor, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))
        self._set_qto(floor, "Qto_CoveringBaseQuantities", {"Width": thickness * u, "GrossArea": poly.area,
                                                            "NetArea": poly.area})

    def _set_ceiling_body(self, ceiling):
        f, u = self.file, 1.0 / self.unit_scale
        p = self.ceiling_params(ceiling.GlobalId)
        poly = Polygon(p["local"], p["local_holes"]).buffer(0)
        params = self._params(ceiling)
        gap = float(params.get("Rasgo") or 0.0)            # (0.119) a shadow gap along the walls
        if gap > 0:
            poly = poly.buffer(-gap, join_style="mitre")
        if poly.is_empty or poly.area < 0.05:
            raise EditRefused("too_small")
        band_w, drop = float(params.get("SancaLargura") or 0.0), float(params.get("SancaAltura") or 0.0)
        band = None
        if band_w > 0 and drop > 0:                        # (0.119) a bulkhead round the edge, lower
            inner = poly.buffer(-band_w, join_style="mitre")
            if not inner.is_empty and inner.geom_type == "Polygon":
                band, poly = poly.difference(inner), inner
        rings = lambda g: [(list(orient(q, 1.0).exterior.coords)[:-1], [list(h.coords)[:-1] for h in q.interiors])  # noqa
                           for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon" and q.area > 1e-6]
        if p["style"] == "tiles":
            exterior, holes = rings(poly)[0]
            pieces = [(ring, [], 0.0, p["thickness"]) for ring in core_ceilings.tiles(exterior, holes=holes)]
        else:
            pieces = [(ring, holes, 0.0, p["thickness"]) for ring, holes in rings(poly)]
        if band is not None:
            pieces += [(ring, holes, -drop, drop + p["thickness"]) for ring, holes in rings(band)]
        items = []
        for ring, holes, z0, depth in pieces:
            outer = self._ring_curve(ring)
            if holes:
                profile = f.createIfcArbitraryProfileDefWithVoids("AREA", None, outer,
                                                                  [self._ring_curve(h) for h in holes])
            else:
                profile = f.createIfcArbitraryClosedProfileDef("AREA", None, outer)
            items.append(f.createIfcExtrudedAreaSolid(
                profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, float(z0 * u))), None, None),
                f.createIfcDirection((0.0, 0.0, 1.0)), float(depth * u)))
        self._clear_representations(ceiling)
        api.geometry.assign_representation(f, product=ceiling, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))
        area = poly.area + (band.area if band is not None else 0.0)
        self._set_qto(ceiling, "Qto_CoveringBaseQuantities", {"Width": p["thickness"] * u, "GrossArea": area,
                                                              "NetArea": area})

    def add_ceiling(self, outline, z, name, style="continuous", holes=(), lang="pt", storey=None):
        """A ceiling over `outline` (plan, with holes), its underside at the level z. Returns the IfcCovering."""
        ring = orient(Polygon(outline), 1.0)
        pts = [tuple(c) for c in list(ring.exterior.coords)[:-1]]
        x0, y0 = min(x for x, _y in pts), min(y for _x, y in pts)
        f = self.file
        ceiling = api.root.create_entity(f, ifc_class="IfcCovering", name=name, predefined_type="CEILING")
        m = np.eye(4)
        m[:3, 3] = (x0, y0, float(z))
        self._place(ceiling, m)
        container = self.storey(storey) if storey is not None else self.storey_at(float(z))
        api.spatial.assign_container(f, products=[ceiling], relating_structure=container)
        api.material.assign_material(f, products=[ceiling], type="IfcMaterial", material=self._material("gesso", lang))
        common = api.pset.add_pset(f, product=ceiling, name="Pset_CoveringCommon")
        api.pset.edit_pset(f, pset=common, properties={"IsExternal": False})
        self._mark(ceiling, "ceiling")
        local = [(x - x0, y - y0) for x, y in pts]
        local_holes = [[(x - x0, y - y0) for x, y in h] for h in holes]
        self._set_params(ceiling, {"Contorno": _text(local), "Furos": "|".join(_text(h) for h in local_holes),
                                   "Estilo": style, "Espessura": TILE_THICKNESS if style == "tiles" else BOARD})
        self._set_ceiling_body(ceiling)
        return ceiling

    def add_flooring(self, outline, z, name, finish="ceramico", holes=(), lang="pt", storey=None):
        """(0.374, the study's «Piso») A floor finish over `outline` (plan, with holes): an IfcCovering FLOORING its
        finish's thickness thick, laid on the level z (the storey's: on the slab). Returns the IfcCovering."""
        material, thickness = FLOORINGS.get(finish, FLOORINGS["ceramico"])
        ring = orient(Polygon(outline), 1.0)
        pts = [tuple(c) for c in list(ring.exterior.coords)[:-1]]
        x0, y0 = min(x for x, _y in pts), min(y for _x, y in pts)
        f, u = self.file, 1.0 / self.unit_scale
        floor = api.root.create_entity(f, ifc_class="IfcCovering", name=name, predefined_type="FLOORING")
        m = np.eye(4)
        m[:3, 3] = (x0, y0, float(z))
        self._place(floor, m)
        container = self.storey(storey) if storey is not None else self.storey_at(float(z))
        api.spatial.assign_container(f, products=[floor], relating_structure=container)
        api.material.assign_material(f, products=[floor], type="IfcMaterial", material=self._material(material, lang))
        common = api.pset.add_pset(f, product=floor, name="Pset_CoveringCommon")
        api.pset.edit_pset(f, pset=common, properties={"IsExternal": False})
        self._mark(floor, "flooring")
        local = [(x - x0, y - y0) for x, y in pts]
        local_holes = [[(x - x0, y - y0) for x, y in h] for h in holes]
        self._set_params(floor, {"Contorno": _text(local), "Furos": "|".join(_text(h) for h in local_holes),
                                 "Acabamento": finish, "Espessura": thickness})
        self._set_flooring_body(floor)
        return floor

    def set_ceiling(self, guid, style=None, z=None, gap=None, bulkhead=None):
        """A ceiling's style, the level of its underside, its shadow gap along the walls or its bulkhead (width,
        drop: (0, 0) none) changed."""
        ceiling, _ = self._require(guid, "ceiling")
        if style is not None:
            if style not in core_ceilings.STYLES:
                raise EditRefused("not_editable")
            self._set_params(ceiling, {"Estilo": style, "Espessura": TILE_THICKNESS if style == "tiles" else BOARD})
        if gap is not None:
            if not 0.0 <= float(gap) <= 0.20:
                raise EditRefused("ceiling_gap")
            self._set_params(ceiling, {"Rasgo": float(gap)})
        if bulkhead is not None:
            width, drop = (float(v) for v in bulkhead)
            if width < 0 or drop < 0:
                raise EditRefused("too_small")
            self._set_params(ceiling, {"SancaLargura": width, "SancaAltura": drop})
        if z is not None:
            m = self._placement_si(ceiling)
            m[2, 3] = float(z)
            self._place(ceiling, m)
        self._set_ceiling_body(ceiling)

    def ceiling_z_at(self, point, storey=None):
        """The level of the underside of a ceiling of the storey over the plan point `point` (a bulkhead's, if it
        is under one), or None (0.119)."""
        from shapely.geometry import Point
        q = Point(float(point[0]), float(point[1]))
        for e in self.file.by_type("IfcCovering"):
            if self.kind_of(e.GlobalId) != "ceiling" or (storey is not None and self.storey_of(e.GlobalId) != storey):
                continue
            p = self.ceiling_params(e.GlobalId)
            poly = Polygon(p["outline"], p["holes"]).buffer(0)
            if not poly.contains(q):
                continue
            params = self._params(e)
            band_w, drop = float(params.get("SancaLargura") or 0.0), float(params.get("SancaAltura") or 0.0)
            gap = float(params.get("Rasgo") or 0.0)
            if band_w > 0 and drop > 0 and not poly.buffer(-gap - band_w, join_style="mitre").contains(q):
                return p["z"] - drop
            return p["z"]
        return None

    # ------------------------------------------------------------ wall finishes (0.119)

    def _cladding_body(self, covering):
        """A wall finish's body from its wall as it is now: the wall's face (where it has its full thickness)
        from its base up to the finish's height, less the wall's doors, windows and openings, as thick as its
        finish — in the wall's own frame (its placement the wall's)."""
        from shapely.geometry import box as shapely_box
        f, u = self.file, 1.0 / self.unit_scale
        p = self._params(covering)
        wall = p.get("Parede")
        if not wall or self.by_guid(wall) is None:
            raise EditRefused("not_editable")
        frame, face, height = self.cladding_face(covering)
        base = self._layer_base(covering, face)            # (0.178) over the layers beneath it on the same face
        if base:
            frame = dataclasses.replace(frame, y0=frame.y0 - base, y1=frame.y1 + base)
        side = 1 if int(p.get("Lado") or 1) > 0 else -1
        t = float(p.get("Espessura") or 0.01)
        m = self._placement_si(self.by_guid(wall))
        y = frame.y1 + t if side > 0 else frame.y0
        curve = lambda pts: f.createIfcIndexedPolyCurve(f.createIfcCartesianPointList2D(pts + [pts[0]]),  # noqa
                                                        None, False)
        on_face = lambda: f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, float(y * u), 0.0)),  # noqa
                                                      f.createIfcDirection((0.0, -1.0, 0.0)),
                                                      f.createIfcDirection((1.0, 0.0, 0.0)))
        finish = p.get("Acabamento") or ""
        kind, items = "SweptSolid", []
        if finish in core_surfaces.PATTERNS:                 # (0.173) slats, flutes, a perforated sheet
            kind, items = self._pattern_items(p, finish, face, frame, side, t, curve, on_face)
        for q in [] if finish in core_surfaces.PATTERNS else getattr(face, "geoms", [face]):
            if q.geom_type != "Polygon" or q.area < 1e-4:
                continue
            q = orient(q, 1.0)
            outer = [(float(x * u), float((z + frame.z0) * u)) for x, z in list(q.exterior.coords)[:-1]]
            holes = [[(float(x * u), float((z + frame.z0) * u)) for x, z in list(h.coords)[:-1]] for h in q.interiors]
            profile = f.createIfcArbitraryProfileDefWithVoids("AREA", None, curve(outer), [curve(h) for h in holes]) \
                if holes else f.createIfcArbitraryClosedProfileDef("AREA", None, curve(outer))
            items.append(f.createIfcExtrudedAreaSolid(profile, on_face(), f.createIfcDirection((0.0, 0.0, 1.0)),
                                                      float(t * u)))
        if not items:
            raise EditRefused("too_small")
        self._cover(covering, self.by_guid(wall))
        self._place(covering, m)
        self._clear_representations(covering)
        api.geometry.assign_representation(f, product=covering, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, kind, items))
        area = float(face.area)
        x0, z0, x1, z1 = self.cladding_box(p, self.element_frame(wall))         # (0.389: a rectangle on the face)
        if finish == "ripado":                             # (0.434) its battens behind it: as much thicker
            d = _pattern_of(p, finish)
            t += float(d.get("batten_d") or 0.0) if int(round(float(d.get("battens") or 0.0))) > 0 else 0.0
        self._set_qto(covering, "Qto_CoveringBaseQuantities", {"Width": t * u, "GrossArea": (x1 - x0) * (z1 - z0),
                                                               "NetArea": area})

    def cladding_face(self, covering):
        """(its wall's frame, the face it covers — shapely, (x along the wall, z from its base) —, its height): the
        wall's face up to the finish's height, less its doors, windows and openings."""
        from shapely.geometry import box as shapely_box
        if isinstance(covering, str):
            covering = self.by_guid(covering)
        p = self._params(covering)
        wall = p.get("Parede")
        frame = self.element_frame(wall)
        x0, z0, x1, height = self.cladding_box(p, frame)
        face = shapely_box(x0, z0, x1, height)
        side = 1 if int(p.get("Lado") or 1) > 0 else -1
        for gid, lo, hi, _filled, _box in self.voids(wall):
            reveal = self.reveal_params(gid)
            if reveal is not None and reveal["side"] != side:
                continue                                # (0.305: a reveal on the other face)
            face = face.difference(shapely_box(lo[0], lo[2] - frame.z0, hi[0], hi[2] - frame.z0))
        return frame, face, height

    @staticmethod
    def cladding_box(p, frame):
        """(0.389) (x0, z0, x1, z1) of a finish on its wall's face (frame: x along it, z from its base): the whole
        face up to its height («Altura»), or the rectangle drawn on it — «Inicio»/«Fim» along the wall from its
        start, «Base» up — kept on the face (at least 5 cm of it) when the wall gets shorter or lower."""
        top = min(float(p.get("Altura") or frame.height), frame.height)
        start = min(max(0.0, float(p.get("Inicio") or 0.0)), max(0.0, frame.length - 0.05))
        end = frame.length if p.get("Fim") is None else min(frame.length, max(float(p["Fim"]), start + 0.05))
        base = min(max(0.0, float(p.get("Base") or 0.0)), max(0.0, top - 0.05))
        return frame.x0 + start, base, frame.x0 + end, top

    # ------------------------------------------------------------ layers on one face (0.178)

    def face_claddings(self, guid):
        """The other finishes on the same face of the same wall as this one (any layer)."""
        p = self._params(self.by_guid(guid))
        wall, side = p.get("Parede"), 1 if int(p.get("Lado") or 1) > 0 else -1
        return [e.GlobalId for e in self.file.by_type("IfcCovering") if e.GlobalId != guid
                and self._params(e).get("Elemento") == "cladding" and self._params(e).get("Parede") == wall
                and (1 if int(self._params(e).get("Lado") or 1) > 0 else -1) == side]

    def _layer_base(self, covering, face):
        """How far a finish stands off its wall: the thickness of the finishes beneath it on the same face (a lower
        Camada) where they and it overlap — plaster under tiles."""
        layer = int(self._params(covering).get("Camada") or 0)
        if layer <= 0:
            return 0.0
        base = 0.0
        for g in self.face_claddings(covering.GlobalId):
            q = self._params(self.by_guid(g))
            if int(q.get("Camada") or 0) >= layer:
                continue
            if self.cladding_face(g)[1].intersection(face).area > 1e-4:
                base += float(q.get("Espessura") or 0.0)
        return base

    def restack_claddings(self, guids):
        """These finishes made again over what is beneath them now (one beneath changed or went), lowest first."""
        alive = [g for g in guids if self.by_guid(g) is not None]
        for g in sorted(alive, key=lambda g: int(self._params(self.by_guid(g)).get("Camada") or 0)):
            self._cladding_body(self.by_guid(g))
        return alive

    def cladding_layer(self, guid):
        """(its layer — 1 on the wall —, the finishes beneath it on its face, lowest first)."""
        layer = int(self._params(self.by_guid(guid)).get("Camada") or 0)
        under = [g for g in self.face_claddings(guid) if int(self._params(self.by_guid(g)).get("Camada") or 0) < layer]
        return max(layer, 1), sorted(under, key=lambda g: int(self._params(self.by_guid(g)).get("Camada") or 0))

    def pattern_params(self, guid):
        """(0.173) A patterned finish's {finish, width, gap, direction, diameter, pitch, margin, thickness} — its own
        or the pattern's usual ones."""
        p = self._params(self.by_guid(guid))
        finish = p.get("Acabamento") or ""
        d = _pattern_of(p, finish)
        d["finish"], d["thickness"] = finish, float(p.get("Espessura") or CLADDINGS.get(finish, ("", 0.01))[1])
        if finish in core_surfaces.PATTERNS:              # (how many slats / holes; its pieces, its sheets)
            _frame, face, _h = self.cladding_face(guid)
            if finish == "perfurado":                    # (0.389: each hole its size — a picture —, its shape)
                d["panels"] = [(q, [tuple(c) for c in centres], [float(s) for s in sizes])
                               for q, centres, sizes in _perforation(face, d)]
                d["holes"] = [c for _q, centres, _s in d["panels"] for c in centres]
                d["count"] = len(d["holes"])
                hole_area = sum((s * s if d["hole"] == "quadrado" else math.pi * s * s / 4.0)
                                for _q, _c, sizes in d["panels"] for s in sizes)
                d["open_area"] = hole_area / face.area if face.area > 1e-9 else 0.0
                d["mask_found"] = bool(d["mask"]) and _mask(d) is not None
            elif finish == "ondulado":                    # (0.175) its ribs
                d["ribs"] = core_surfaces.ribs(face, d["width"], d["gap"], d["amplitude"], d["wavelength"],
                                               d["shift"], d["depth"], d["direction"])
                d["count"] = len(d["ribs"])
            elif finish == "ripado" and _framed(d):      # (0.434) inside its frame; its battens; its frame's pieces
                try:
                    band, battens, d["strips"], _inner = core_surfaces.ripado_parts(face, d)
                except ValueError:
                    band, battens, d["strips"] = None, [], []
                d["count"], d["batten_count"] = len(d["strips"]), len(battens)
                d["batten_pieces"] = [q.bounds for q in battens]
                d["frame_pieces"] = []
                if band is not None:                     # (its four sides: top and bottom across, the sides between)
                    fw = float(d["frame"])
                    u0, v0, u1, v1 = face.bounds
                    d["frame_pieces"] = [(u0, v0, u1, v0 + fw), (u0, v1 - fw, u1, v1),
                                         (u0, v0 + fw, u0 + fw, v1 - fw), (u1 - fw, v0 + fw, u1, v1 - fw)]
            else:
                d["strips"] = core_surfaces.strips(face, d["width"], d["gap"], d["direction"])
                d["count"] = len(d["strips"])
            d["face"] = face
        return d

    def _pattern_items(self, p, finish, face, frame, side, t, curve, on_face):
        """(representation type, items) of a patterned finish on the face (wall frame: x along, z from its base):
        its slats, flutes or perforated sheet."""
        f, u = self.file, 1.0 / self.unit_scale
        d = _pattern_of(p, finish)
        z0 = frame.z0
        items = []
        if finish == "perfurado":
            found = _perforation(face, d)
            if sum(len(c) for _q, c, _s in found) > core_surfaces.MAX_HOLES:
                raise EditRefused("pattern_many")
            free = _free(d)
            if free is not None:                           # (0.540) the Visual Graph's holes
                from shapely.geometry.polygon import orient
                verts, tris = core_surfaces.free_mesh(orient(face, 1.0), t, found, free[0])
            else:
                verts, tris = core_surfaces.perforated_mesh(face, t, d["diameter"], d["pitch"], d["margin"],
                                                            (d["sheet_w"], d["sheet_h"]), d["joint"], d["grid"],
                                                            d["hole"], _mask(d))
            if not len(tris):
                raise EditRefused("too_small")
            yface = frame.y1 if side > 0 else frame.y0
            pts = np.column_stack((verts[:, 0], yface + side * verts[:, 2], verts[:, 1] + z0)) * u
            if side < 0:
                tris = tris[:, ::-1]                       # (mirrored through the face: its faces turned back out)
            items.append(f.createIfcTriangulatedFaceSet(
                f.createIfcCartesianPointList3D([tuple(float(c) for c in row) for row in pts]), None, False,
                [tuple(int(i) + 1 for i in row) for row in tris], None))
            return "Tessellation", items
        if finish == "ondulado":                           # (0.175) each rib its outline extruded across it
            pieces = core_surfaces.ribs(face, d["width"], d["gap"], d["amplitude"], d["wavelength"], d["shift"],
                                        d["depth"], d["direction"])
            if len(pieces) > core_surfaces.MAX_STRIPS or \
                    sum(len(o) for _a0, _a1, o in pieces) > core_surfaces.MAX_WAVE_POINTS:
                raise EditRefused("pattern_many")
            yface = frame.y1 if side > 0 else frame.y0
            level = d["direction"] == "horizontal"
            for a0, a1, outline in pieces:
                if level:                                  # (in plan — x along the wall, y out —, extruded up)
                    out = side
                    place = f.createIfcAxis2Placement3D(
                        f.createIfcCartesianPoint((0.0, float(yface * u), float((a0 + z0) * u))),
                        f.createIfcDirection((0.0, 0.0, 1.0)), f.createIfcDirection((1.0, 0.0, 0.0)))
                else:                                      # (upright — x up, y the wall's −y —, extruded along it)
                    out = -side
                    place = f.createIfcAxis2Placement3D(
                        f.createIfcCartesianPoint((float(a0 * u), float(yface * u), float(z0 * u))),
                        f.createIfcDirection((1.0, 0.0, 0.0)), f.createIfcDirection((0.0, 0.0, 1.0)))
                pts = [(float(b * u), float(out * w * u)) for b, w in outline]
                if out < 0:                                # (mirrored: turned back counter-clockwise)
                    pts = pts[::-1]
                items.append(f.createIfcExtrudedAreaSolid(f.createIfcArbitraryClosedProfileDef("AREA", None,
                                                                                               curve(pts)),
                                                          place, f.createIfcDirection((0.0, 0.0, 1.0)),
                                                          float((a1 - a0) * u)))
            return "SweptSolid", items
        if finish == "ripado" and _framed(d):              # (0.434) with a frame round it, battens behind
            return self._ripado_items(d, face, frame, side, t, curve)
        runs = core_surfaces.strips(face, d["width"], d["gap"], d.get("direction", "vertical"))
        if len(runs) > core_surfaces.MAX_STRIPS:
            raise EditRefused("pattern_many")
        for u0, v0, u1, v1 in runs:
            if finish == "ripado":
                ring = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
                profile = f.createIfcArbitraryClosedProfileDef("AREA", None, curve(
                    [(float(x * u), float((z + z0) * u)) for x, z in ring]))
                items.append(f.createIfcExtrudedAreaSolid(profile, on_face(), f.createIfcDirection((0.0, 0.0, 1.0)),
                                                          float(t * u)))
                continue
            # a flute: a half-round across it, bulging out of the face, run along it
            level = d.get("direction") == "horizontal"
            a0, a1, b0, b1 = (v0, v1, u0, u1) if level else (u0, u1, v0, v1)
            r = (a1 - a0) / 2.0
            yface = frame.y1 if side > 0 else frame.y0
            out = side if not level else -side             # (a level one's profile y is the wall's −y)
            pts2 = [(0.0, 0.0), (r, out * min(r, t)), (2 * r, 0.0)]
            arc = f.createIfcIndexedPolyCurve(f.createIfcCartesianPointList2D(
                [(float(x * u), float(y * u)) for x, y in pts2]),
                [f.createIfcArcIndex((1, 2, 3)), f.createIfcLineIndex((3, 1))], False)
            if level:                                      # (along x: the profile in the y–z plane)
                place = f.createIfcAxis2Placement3D(
                    f.createIfcCartesianPoint((float(b0 * u), float(yface * u), float((a0 + z0) * u))),
                    f.createIfcDirection((1.0, 0.0, 0.0)), f.createIfcDirection((0.0, 0.0, 1.0)))
            else:                                          # (upright: the profile in the x–y plane)
                place = f.createIfcAxis2Placement3D(
                    f.createIfcCartesianPoint((float(a0 * u), float(yface * u), float((b0 + z0) * u))),
                    f.createIfcDirection((0.0, 0.0, 1.0)), f.createIfcDirection((1.0, 0.0, 0.0)))
            items.append(f.createIfcExtrudedAreaSolid(f.createIfcArbitraryClosedProfileDef("AREA", None, arc), place,
                                                      f.createIfcDirection((0.0, 0.0, 1.0)), float((b1 - b0) * u)))
        return "SweptSolid", items

    def _ripado_items(self, d, face, frame, side, t, curve):
        """(0.434, the addon's «Ripado») A slatted panel's pieces on the face: its battens on the wall (as thick as
        `batten_d`), its slats `t` thick over them — standing off the wall by the battens —, its frame round it as deep
        as both. Each its outline on the face extruded out of it."""
        from shapely.geometry import box
        f, u = self.file, 1.0 / self.unit_scale
        try:
            band, battens, slats, _inner = core_surfaces.ripado_parts(face, d)
        except ValueError:
            raise EditRefused("ripado_frame")
        if len(slats) > core_surfaces.MAX_STRIPS:
            raise EditRefused("pattern_many")
        standoff = float(d.get("batten_d") or 0.0) if battens else 0.0
        z0 = frame.z0
        items = []

        def extrude(geometry, offset, depth):
            """Its polygons extruded out of the face from `offset` to `offset` + `depth`."""
            y = (frame.y1 + offset + depth) if side > 0 else (frame.y0 - offset)
            place = f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, float(y * u), 0.0)),
                                                f.createIfcDirection((0.0, -1.0, 0.0)),
                                                f.createIfcDirection((1.0, 0.0, 0.0)))
            for q in getattr(geometry, "geoms", [geometry]):
                if q.geom_type != "Polygon" or q.area < 1e-6:
                    continue
                q = orient(q, 1.0)
                outer = [(float(x * u), float((z + z0) * u)) for x, z in list(q.exterior.coords)[:-1]]
                holes = [[(float(x * u), float((z + z0) * u)) for x, z in list(h.coords)[:-1]] for h in q.interiors]
                profile = f.createIfcArbitraryProfileDefWithVoids("AREA", None, curve(outer), [curve(h) for h in holes]) \
                    if holes else f.createIfcArbitraryClosedProfileDef("AREA", None, curve(outer))
                items.append(f.createIfcExtrudedAreaSolid(profile, place, f.createIfcDirection((0.0, 0.0, 1.0)),
                                                          float(depth * u)))

        if band is not None:
            extrude(band, 0.0, standoff + t)
        for q in battens:
            extrude(q, 0.0, standoff)
        for u0, v0, u1, v1 in slats:
            extrude(box(u0, v0, u1, v1), standoff, t)
        return "SweptSolid", items

    def _cover(self, covering, wall):
        """The finish tied to its wall (IfcRelCoversBldgElements): to that one only — a copy is tied to the copy
        of the wall, not to the original's."""
        here = None
        for rel in list(getattr(covering, "CoversElements", None) or ()):
            if rel.RelatingBuildingElement == wall:
                here = rel
                continue
            others = [c for c in rel.RelatedCoverings if c != covering]
            if others:
                rel.RelatedCoverings = others
            else:
                self.file.remove(rel)
        if here is None:                              # (as IfcOpenShell's own api makes its relationships)
            self.file.create_entity("IfcRelCoversBldgElements", GlobalId=ifcopenshell.guid.new(),
                                    OwnerHistory=api.owner.create_owner_history(self.file),
                                    RelatingBuildingElement=wall, RelatedCoverings=[covering])

    def uncover(self, element):
        """An element going (a wall, a finish): its finish ties let go, none left empty (IfcOpenShell's
        remove_product does not know them)."""
        for rel in list(getattr(element, "HasCoverings", None) or ()):
            self.file.remove(rel)
        for rel in list(getattr(element, "CoversElements", None) or ()):
            others = [c for c in rel.RelatedCoverings if c != element]
            if others:
                rel.RelatedCoverings = others
            else:
                self.file.remove(rel)

    def remove_cladding(self, covering):
        self.uncover(covering)
        api.root.remove_product(self.file, product=covering)

    def add_cladding(self, wall, side, finish, height, name, lang="pt", pattern=None, region=None):
        """A finish on a wall's face (0.119: IfcCovering CLADDING — tiles, plaster, stone), side ±1 (its frame's
        y), from its base up to `height`, cut round its doors and windows; tied to it (IfcRelCoversBldgElements)
        so that it follows it. (0.389) `pattern`: its pattern's measures (as set_cladding's); `region`: {start, end,
        base} a rectangle on the face (m along the wall from its start, up from its base) — else the whole face.
        Returns the IfcCovering."""
        self._require(wall, "wall")
        if finish not in CLADDINGS:
            raise EditRefused("not_editable")
        material, thickness = CLADDINGS[finish]
        f = self.file
        covering = api.root.create_entity(f, ifc_class="IfcCovering", name=name, predefined_type="CLADDING")
        container = ifcopenshell.util.element.get_container(self.by_guid(wall)) or self.storey()
        api.spatial.assign_container(f, products=[covering], relating_structure=container)
        api.material.assign_material(f, products=[covering], type="IfcMaterial",
                                     material=self._material(material, lang))
        self._mark(covering, "cladding")
        side = 1 if side > 0 else -1
        layers = [int(self._params(e).get("Camada") or 1) for e in f.by_type("IfcCovering")    # (0.178) its layer
                  if e != covering and self._params(e).get("Elemento") == "cladding"
                  and self._params(e).get("Parede") == wall and (1 if int(self._params(e).get("Lado") or 1) > 0
                                                                 else -1) == side]
        self._set_params(covering, {"Parede": wall, "Lado": side, "Altura": float(height),
                                    "Espessura": thickness, "Acabamento": finish, "Camada": max(layers, default=0) + 1})
        extra = self._pattern_changes(pattern or {})
        extra.update(self._region_changes(region or {}))
        if extra:
            self._set_params(covering, extra)
        self._cladding_body(covering)
        return covering

    @staticmethod
    def _pattern_changes(pattern):
        """{pset name: value} of a pattern's measures (0.173), checked; (0.389) the hole's shape, the grid, the
        boards, the joint, the picture («» none)."""
        changes = {}
        for key, value in pattern.items():
            if key not in PATTERN_NAMES or value is None:
                continue
            if key in CHOICES:
                if value not in CHOICES[key]:
                    raise EditRefused("not_editable")
                changes[PATTERN_NAMES[key]] = str(value)
            elif key == "mask":
                changes[PATTERN_NAMES[key]] = str(value)
            elif key == "free":                          # (0.540) the Visual Graph's holes («» none)
                if value and core_surfaces.free_read(str(value)) is None:
                    raise EditRefused("pattern_bad")
                changes[PATTERN_NAMES[key]] = str(value)
            elif key == "shift":                         # (0.175) any angle — negative: the waves turn the other way
                changes[PATTERN_NAMES[key]] = float(value)
            else:
                if float(value) <= 0.0 and key not in ("gap", "margin", "depth", "joint", "frame", "battens",
                                                       "free_repeat") \
                        or float(value) < 0.0:
                    raise EditRefused("pattern_bad")
                if key in ("sheet_w", "sheet_h") and float(value) < 0.1:
                    raise EditRefused("pattern_bad")
                if key == "battens" and float(value) > core_surfaces.MAX_BATTENS:        # (0.434)
                    raise EditRefused("pattern_bad")
                if key in ("thickness", "batten_d") and float(value) > 0.30:
                    raise EditRefused("pattern_bad")
                changes[PATTERN_NAMES[key]] = float(round(float(value))) if key == "battens" else float(value)
        return changes

    @staticmethod
    def _region_changes(region):
        """(0.389) {pset name: value} of a rectangle on the face (start, end, base: m)."""
        changes = {}
        for key, value in region.items():
            if key in REGION_NAMES and value is not None:
                if float(value) < 0.0:
                    raise EditRefused("pattern_bad")
                changes[REGION_NAMES[key]] = float(value)
        if "Inicio" in changes and "Fim" in changes and changes["Fim"] - changes["Inicio"] < 0.05:
            raise EditRefused("too_small")
        return changes

    def claddings_of(self, walls):
        """{finish GlobalId: its wall} of the finishes on any of these walls."""
        wanted, out = set(walls), {}
        for e in self.file.by_type("IfcCovering"):
            wall = self._params(e).get("Parede")
            if wall in wanted:
                out[e.GlobalId] = wall
        return out

    def follow_claddings(self, changed):
        """After walls changed (longer, moved, mirrored, a door put in…): their finishes made again on them; a
        wall gone takes its finishes (0.119). Returns those that changed."""
        out, changed = [], set(changed)
        for e in list(self.file.by_type("IfcCovering")):
            wall = self._params(e).get("Parede")
            if not wall:
                continue
            if self.by_guid(wall) is None:            # (whatever took the wall away: merged into another…)
                out.append(e.GlobalId)
                self.remove_cladding(e)
            elif wall in changed:
                self._cladding_body(e)
                out.append(e.GlobalId)
        return out

    def carry_claddings(self, source, target, copy=False, flip=False):
        """A wall split (copy): the new part gets copies of the finishes of the first; two walls merged: the one
        going hands its finishes to the one staying — but those on a face that already has one; flip: the two
        drawn the opposite way (a face's side the other) (0.119)."""
        have = {int(self._params(self.by_guid(g)).get("Lado") or 1) for g in self.claddings_of([target])}
        for g in self.claddings_of([source]):
            e = self.by_guid(g)
            side = int(self._params(e).get("Lado") or 1) * (-1 if flip else 1)
            if copy:
                e = self.copy_element(g)
                if self.created is not None and e.GlobalId in self.created:
                    self.created.remove(e.GlobalId)
            elif side in have:
                self.remove_cladding(e)
                continue
            self._set_params(e, {"Parede": target, "Lado": side})
            self._cladding_body(e)

    def set_cladding(self, guid, height=None, finish=None, **pattern):
        covering, _ = self._require(guid, "cladding")
        changes = {}
        if height is not None:
            changes["Altura"] = float(height)
        changes.update(self._pattern_changes(pattern))   # (0.173) a pattern's measures; (0.389) and the panel's
        changes.update(self._region_changes({k: v for k, v in pattern.items() if k in REGION_NAMES}))
        if finish is not None:
            if finish not in CLADDINGS:
                raise EditRefused("not_editable")
            material, thickness = CLADDINGS[finish]
            changes.update(Acabamento=finish, Espessura=thickness)
            api.material.unassign_material(self.file, products=[covering])
            api.material.assign_material(self.file, products=[covering], type="IfcMaterial",
                                         material=self._material(material, "pt"))
        self._set_params(covering, changes)
        self._cladding_body(covering)
        layer = int(self._params(covering).get("Camada") or 0)     # (0.178) the layers over it follow
        self.restack_claddings([g for g in self.face_claddings(guid)
                                if int(self._params(self.by_guid(g)).get("Camada") or 0) > layer])

    # ------------------------------------------------------------ lights (0.119)

    def add_light(self, point, z, kind, name, storey=None):
        """A light fixture under a ceiling (IfcLightFixture POINTSOURCE): a 60 × 60 panel or a round downlight,
        its face at the level z."""
        f, u = self.file, 1.0 / self.unit_scale
        light = api.root.create_entity(f, ifc_class="IfcLightFixture", name=name, predefined_type="POINTSOURCE")
        m = np.eye(4)
        m[:3, 3] = (float(point[0]), float(point[1]), float(z))
        self._place(light, m)
        origin2 = f.createIfcAxis2Placement2D(f.createIfcCartesianPoint((0.0, 0.0)), None)
        if kind == "downlight":
            profile = f.createIfcCircleProfileDef("AREA", None, origin2, float(0.075 * u))
        else:
            profile = f.createIfcRectangleProfileDef("AREA", None, origin2, float(0.595 * u), float(0.595 * u))
        solid = f.createIfcExtrudedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)), None, None),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(0.06 * u))
        api.geometry.assign_representation(f, product=light, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", [solid]))
        container = self.storey(storey) if storey is not None else self.storey_at(float(z))
        api.spatial.assign_container(f, products=[light], relating_structure=container)
        self._mark(light, "light")
        self._set_params(light, {"Luminaria": kind})
        return light
