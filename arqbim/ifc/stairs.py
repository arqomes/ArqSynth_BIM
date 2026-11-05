"""Stairs (0.114), mixed into IfcModel: an IfcStair (STRAIGHT_RUN_STAIR, QUARTER_TURN_STAIR, HALF_TURN_STAIR) with
its own body — as the ramp's and the roof's, one element to select, move, copy and mirror. Each flight is its side
(core/stairs.flight_side: the steps and the waist under them) extruded across its width; each landing a plate.
Its material: the slab type's; Pset_StairCommon (risers, treads, riser height, tread length, waist).

ArqSynth_Parametros: Elemento "stair", Forma, Viragem (left / right), Desnivel, Largura, Cobertor, Espessura
(the waist), Tipo. Its placement: the middle of its first riser at the floor, its x along its first flight."""

import math

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import stairs as core_stairs
from . import catalog
from .edit import EditRefused

api = ifcopenshell.api
PREDEFINED = {"straight": "STRAIGHT_RUN_STAIR", "l": "QUARTER_TURN_STAIR", "u": "HALF_TURN_STAIR",
              "v": "HALF_TURN_STAIR", "spiral": "SPIRAL_STAIR"}


def _merged_landings(pieces, width, going):
    """(0.257) A stair's landing made with its flights, so that the stair is one slab with no seams: {"flights":
    {piece index: (ahead, behind)} — the flight reaching the landing takes it on past its last riser, as deep as it
    goes that way; a flight leaving it from its far edge (a U's, a V's) the part behind its foot, unless that is
    taken already (an L's) —, "rest": the landing's plan outside them (a U's gap between its flights), as rings}."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    landing = next((piece for piece in pieces if piece[0] == "landing"), None)
    if landing is None:
        return {"flights": {}, "rest": []}
    ring, top = landing[1], landing[2]
    corners = np.array(ring, dtype=float)
    flights, covered = {}, []

    def strip(a, d, left, depth):
        return Polygon([a + left * width / 2, a - left * width / 2, a - left * width / 2 + d * depth,
                        a + left * width / 2 + d * depth])

    for k, piece in enumerate(pieces):                   # (first those reaching it, then those leaving it)
        if piece[0] == "flight" and abs(piece[5] + piece[3] * piece[4] - top) < 1e-9:
            _kind, o, d, n, _h, _z0 = piece
            o, d = np.array(o, dtype=float), np.array(d, dtype=float)
            last = o + d * (n - 1) * going
            ahead = float(max(0.0, ((corners - last) @ d).max()))
            flights[k] = (ahead, 0.0)
            covered.append(strip(last, d, np.array((-d[1], d[0])), ahead))
    for k, piece in enumerate(pieces):
        if piece[0] == "flight" and abs(piece[5] - top) < 1e-9:
            _kind, o, d, _n, _h, _z0 = piece
            o, d = np.array(o, dtype=float), np.array(d, dtype=float)
            behind = float(max(0.0, ((o - corners) @ d).max()))
            part = strip(o, -d, np.array((-d[1], d[0])), behind)
            if behind > 1e-9 and (not covered or part.intersection(unary_union(covered)).area < 1e-6):
                flights[k] = (0.0, behind)
                covered.append(part)
    rest = Polygon(ring).difference(unary_union(covered)) if covered else Polygon(ring)
    rings = [[tuple(map(float, c)) for c in g.exterior.coords[:-1]]
             for g in getattr(rest, "geoms", [rest]) if g.geom_type == "Polygon" and g.area > 1e-6]
    return {"flights": flights, "rest": rings}


class StairMixin:
    def stair_params(self, guid):
        e = self.by_guid(guid)
        p = self._params(e)
        return {"form": p.get("Forma") or "straight", "turn": p.get("Viragem") or "left",
                "rise": float(p["Desnivel"]), "width": float(p["Largura"]), "going": float(p["Cobertor"]),
                "waist": float(p.get("Espessura") or 0.15), "spec": catalog.BY_KEY.get(p.get("Tipo") or "")}

    def _set_stair_body(self, stair):
        f, u = self.file, 1.0 / self.unit_scale
        p = self.stair_params(stair.GlobalId)
        if p["width"] < 0.5 or p["going"] < 0.15 or p["rise"] < 0.30:
            raise EditRefused("stair_small")
        pieces = core_stairs.layout(p["form"], p["rise"], p["width"], p["going"], p["turn"])
        merged = _merged_landings(pieces, p["width"], p["going"])
        items = []
        for k, piece in enumerate(pieces):
            if piece[0] == "column":                     # (0.116) a spiral stair's column
                _kind, (cx, cy), r, height = piece
                items.append(f.createIfcExtrudedAreaSolid(
                    f.createIfcCircleProfileDef("AREA", None, f.createIfcAxis2Placement2D(
                        f.createIfcCartesianPoint((0.0, 0.0)), None), float(r * u)),
                    f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((float(cx * u), float(cy * u), 0.0)),
                                                None, None),
                    f.createIfcDirection((0.0, 0.0, 1.0)), float(height * u)))
                continue
            if piece[0] == "wedge":                      # (0.116) a tread round it: true arcs
                _kind, (cx, cy), r0, r1, a0, a1, top = piece
                am = (a0 + a1) / 2
                ring = [(r0, a0), (r1, a0), (r1, am), (r1, a1), (r0, a1), (r0, am)]
                coords = [(float((cx + r * math.cos(a)) * u), float((cy + r * math.sin(a)) * u)) for r, a in ring]
                curve = f.createIfcIndexedPolyCurve(f.createIfcCartesianPointList2D(coords), [
                    f.createIfcLineIndex((1, 2)), f.createIfcArcIndex((2, 3, 4)), f.createIfcLineIndex((4, 5)),
                    f.createIfcArcIndex((5, 6, 1))], False)
                items.append(f.createIfcExtrudedAreaSolid(
                    f.createIfcArbitraryClosedProfileDef("AREA", None, curve),
                    f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, float(top * u))), None, None),
                    f.createIfcDirection((0.0, 0.0, -1.0)), float(core_stairs.TREAD * u)))
                continue
            if piece[0] == "landing":                    # (0.257: made with its flights; only what lies between them)
                _kind, _ring, top = piece
                for ring in merged["rest"]:
                    coords = [(float(x * u), float(y * u)) for x, y in ring + ring[:1]]
                    items.append(f.createIfcExtrudedAreaSolid(
                        f.createIfcArbitraryClosedProfileDef("AREA", None, f.createIfcIndexedPolyCurve(
                            f.createIfcCartesianPointList2D(coords), None, False)),
                        f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, float(top * u))), None, None),
                        f.createIfcDirection((0.0, 0.0, -1.0)), float(p["waist"] * u)))
                continue
            _kind, (ox, oy), (dx, dy), n, h, z0 = piece
            # (0.256) the first flight stands on the floor, the next ones from the landing's underside; (0.257) the
            # landing made with the flights that meet it — the one reaching it on into it, the one leaving it (a U's)
            # from behind — one slab, no seam
            ahead, behind = merged["flights"].get(k, (0.0, 0.0))
            side = core_stairs.flight_side(n, h, p["going"], p["waist"], z0, below=p["waist"] if z0 > 1e-9 else 0.0,
                                           ahead=ahead, behind=behind)
            coords = [(float(x * u), float(z * u)) for x, z in side] + [(float(side[0][0] * u), float(side[0][1] * u))]
            lx, ly = -dy, dx                              # (its left: the side drawn, extruded to the right)
            w = p["width"]
            items.append(f.createIfcExtrudedAreaSolid(
                f.createIfcArbitraryClosedProfileDef("AREA", None, f.createIfcIndexedPolyCurve(
                    f.createIfcCartesianPointList2D(coords), None, False)),
                f.createIfcAxis2Placement3D(
                    f.createIfcCartesianPoint((float((ox + lx * w / 2) * u), float((oy + ly * w / 2) * u), 0.0)),
                    f.createIfcDirection((float(-lx), float(-ly), 0.0)), f.createIfcDirection((float(dx), float(dy), 0.0))),
                f.createIfcDirection((0.0, 0.0, 1.0)), float(w * u)))
        self._clear_representations(stair)
        api.geometry.assign_representation(f, product=stair, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))
        n, h = core_stairs.risers(p["rise"])
        common = ifcopenshell.util.element.get_psets(stair).get("Pset_StairCommon")
        pset = f.by_id(common["id"]) if common else api.pset.add_pset(f, product=stair, name="Pset_StairCommon")
        api.pset.edit_pset(f, pset=pset, properties={
            "NumberOfRiser": n, "NumberOfTreads": core_stairs.treads(p["form"], p["rise"]),
            "RiserHeight": h * u, "TreadLength": p["going"] * u, "WaistThickness": p["waist"] * u,
            "IsExternal": False})

    def add_stair(self, spec, foot, direction, form, rise, width, going, turn, name, lang="pt", storey=None):
        """A stair from `foot` (the middle of its first riser, at the floor) going along `direction` (plan),
        rising `rise`: its form, turn (an L / a U: to the left or right), width and tread; its waist and material
        the slab type `spec`'s. Returns the IfcStair."""
        f = self.file
        d = np.array((float(direction[0]), float(direction[1]), 0.0))
        d /= np.linalg.norm(d)
        stair = api.root.create_entity(f, ifc_class="IfcStair", name=name, predefined_type=PREDEFINED[form])
        m = np.eye(4)
        m[:3, 0], m[:3, 1], m[:3, 3] = d, np.cross((0.0, 0.0, 1.0), d), np.asarray(foot, dtype=float)
        self._place(stair, m)
        container = self.storey(storey) if storey is not None else self.storey_at(float(foot[2]))
        api.spatial.assign_container(f, products=[stair], relating_structure=container)
        if spec.layers:
            api.material.assign_material(f, products=[stair], type="IfcMaterial",
                                         material=self._material(spec.layers[0][0], lang))
        self._mark(stair, "stair")
        self._set_params(stair, {"Forma": form, "Viragem": turn, "Desnivel": float(rise), "Largura": float(width),
                                 "Cobertor": float(going), "Espessura": spec.thickness, "Tipo": spec.key})
        self._set_stair_body(stair)
        return stair

    def set_stair(self, guid, **changes):
        """A stair's form, turn, rise, width or tread changed (its foot stays)."""
        stair, _ = self._require(guid, "stair")
        names = {"form": "Forma", "turn": "Viragem", "rise": "Desnivel", "width": "Largura", "going": "Cobertor"}
        values = {}
        for key, value in changes.items():
            if key not in names or value is None:
                continue
            if key == "form" and value not in core_stairs.FORMS or key == "turn" and value not in core_stairs.TURNS:
                raise EditRefused("not_editable")
            values[names[key]] = value if key in ("form", "turn") else float(value)
        self._set_params(stair, values)
        if "Forma" in values:
            stair.PredefinedType = PREDEFINED[values["Forma"]]
        self._set_stair_body(stair)
