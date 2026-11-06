"""(0.423) The lot in the IFC, mixed into IfcModel: the IfcSite's «FootPrint» — a closed 2D polyline in the Plan /
FootPrint / PLAN_VIEW context, as the IFC has it for a site's boundary (and other programs read and write it) — and,
in the program's parameters of the site, the sides chosen as the front («LoteFrentes»: "0,2"; none: found from the
entrance, verify/measures.py) and its name («LoteNome»)."""

import numpy as np

import ifcopenshell.api
import ifcopenshell.util.representation

from ..core import lot as core_lot

api = ifcopenshell.api
FOOTPRINT = "FootPrint"


class LotMixin:
    def _footprint_context(self):
        get = ifcopenshell.util.representation.get_context
        context = get(self.file, "Plan", FOOTPRINT, "PLAN_VIEW")
        if context is None:
            plan = get(self.file, "Plan") or api.context.add_context(self.file, context_type="Plan")
            context = api.context.add_context(self.file, context_type="Plan", context_identifier=FOOTPRINT,
                                              target_view="PLAN_VIEW", parent=plan)
        return context

    def _site_matrix(self, site):
        """The site's placement in metres, in the world's coordinates (not the program's: no origin taken away)."""
        m = self._local_placement(site.ObjectPlacement).copy()
        m[:3, 3] *= self.unit_scale
        return m

    def _footprints(self, site):
        shape = getattr(site, "Representation", None)
        return [r for r in (shape.Representations if shape else ()) if r.RepresentationIdentifier == FOOTPRINT]

    def lot(self):
        """{"outline": [(x, y)] (program coordinates, counter-clockwise), "fronts": [side index] chosen (none: []),
        "chosen": whether the fronts were chosen, "name": str, "area": m²} — or None (no lot)."""
        sites = self.file.by_type("IfcSite")
        if not sites:
            return None
        site = sites[0]
        s = self.unit_scale
        m = self._site_matrix(site)
        shift = np.asarray(self.origin, dtype=float)
        for rep in self._footprints(site):
            for item in rep.Items or ():
                pts = _curve_points(item)
                if len(pts) < 3:
                    continue
                world = [(m @ np.array((x * s, y * s, 0.0, 1.0)))[:2] - shift[:2] for x, y in pts]
                ring = core_lot.ring([(float(p[0]), float(p[1])) for p in world])
                if ring is None:
                    continue
                params = self._params(site)
                text = str(params.get("LoteFrentes") or "")
                fronts = [int(k) for k in text.split(",") if k.strip().lstrip("-").isdigit()]
                return {"outline": ring, "fronts": fronts, "chosen": bool(fronts),
                        "name": params.get("LoteNome") or "", "area": core_lot.area(ring)}
        return None

    def set_lot(self, outline, fronts=None, name=None):
        """The lot drawn: its outline (program coordinates), the sides chosen as the front (None: as they were when
        the outline has as many sides, else none). Returns the IfcSite."""
        ring = core_lot.ring(outline)
        if ring is None:
            raise ValueError("no lot")
        site = self._site()
        old = self.lot()
        self._drop_footprint(site)
        s = self.unit_scale
        inverse = np.linalg.inv(self._site_matrix(site))
        shift = np.asarray(self.origin, dtype=float)
        local = [(inverse @ np.array((x + shift[0], y + shift[1], 0.0, 1.0)))[:2] / s for x, y in ring]
        f = self.file
        points = [f.createIfcCartesianPoint((float(x), float(y))) for x, y in local]
        curve = f.createIfcPolyline(points + [points[0]])
        rep = f.createIfcShapeRepresentation(self._footprint_context(), FOOTPRINT, "Curve2D", [curve])
        api.geometry.assign_representation(f, product=site, representation=rep)
        if fronts is None:
            fronts = old["fronts"] if old is not None and len(old["outline"]) == len(ring) else []
        values = {"LoteFrentes": ",".join(str(int(k)) for k in fronts if 0 <= int(k) < len(ring)) or None}
        if name is not None:
            values["LoteNome"] = name or None
        self._set_params(site, values)
        return site

    def set_lot_fronts(self, fronts):
        """The sides of the lot that face the street (indices), or [] / None: found from the entrance."""
        sites = self.file.by_type("IfcSite")
        if sites:
            self._set_params(sites[0], {"LoteFrentes": ",".join(str(int(k)) for k in (fronts or ())) or None})

    def remove_lot(self):
        sites = self.file.by_type("IfcSite")
        if sites:
            self._drop_footprint(sites[0])
            self._set_params(sites[0], {"LoteFrentes": None})

    def _drop_footprint(self, site):
        for rep in self._footprints(site):
            api.geometry.unassign_representation(self.file, product=site, representation=rep)
            api.geometry.remove_representation(self.file, representation=rep)


def _curve_points(item):
    """[(x, y)] of a footprint's curve: a polyline, an indexed polycurve, a curve in a set (another program's)."""
    if item.is_a("IfcGeometricCurveSet") or item.is_a("IfcGeometricSet"):
        for element in item.Elements or ():
            pts = _curve_points(element)
            if len(pts) >= 3:
                return pts
        return []
    if item.is_a("IfcPolyline"):
        pts = [tuple(p.Coordinates[:2]) for p in item.Points]
    elif item.is_a("IfcIndexedPolyCurve"):
        pts = [tuple(c[:2]) for c in item.Points.CoordList]
    else:
        return []
    if len(pts) > 1 and np.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1e-9:
        pts = pts[:-1]
    return [(float(x), float(y)) for x, y in pts]
