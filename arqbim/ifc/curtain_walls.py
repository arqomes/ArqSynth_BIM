"""Curtain walls (0.117), mixed into IfcModel: an IfcCurtainWall with its own body — as the stair's and the
roof's, one element to select, move, copy and mirror: its mullions (upright, at most `Montantes` apart, equal),
its transoms (level, at most `Travessas` apart, equal) and a glass panel in each cell. Its materials: an
IfcMaterialConstituentSet of aluminium (the frame) and glass (the panels); Qto_CurtainWallQuantities,
Pset_CurtainWallCommon.IsExternal.

ArqSynth_Parametros: Elemento "curtain_wall", Comprimento, Altura, Montantes, Travessas (m); (0.181) Paineis — the
cells that are not glass, "column,row=kind;…" (opaque, a door, empty); (0.188) Embutir — 1 when it goes into the
wall it lies in. Its placement: the start of its line at its base, its x along it (as a wall's).

(0.188) Embedded in a wall (Revit's Automatically Embed): drawn along a straight wall, inside its thickness, its ends
and top within it, it cuts its opening in it — an IfcOpeningElement voiding the wall, which the curtain wall fills
(IfcRelFillsElement), as a door's — and so goes with the wall (moved, copied, mirrored, split, deleted) and slides
along it; its opening follows it when it changes (fit_embedding, after every change of it).

(0.252) Along an arc, in a curved wall: drawn inside a curved wall (the same centre, between its faces), it follows
the wall's arc — Raio (its line's radius) and Abertura (degrees, + counter-clockwise) among its parameters, its
placement the arc's centre at its base, its x towards its start (as a curved wall's) — its mullions on the arc,
square to it, its transoms and panels flat between them (chords, as built). Its opening is the ring's sector right
through the wall; where it is in it is kept on the opening (AoLongo, Largura: along the wall's axis; Desvio: its line
off the axis; Sentido; Peitoril, Altura), so that it follows the wall as a door does (follow_curved_openings)."""

import math

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import arcs
from .edit import MARGIN, MIN_SIZE, EditRefused

api = ifcopenshell.api
MULLION = (0.05, 0.15)      # m: a mullion's width along the facade and depth across it
TRANSOM = (0.12, 0.05)      # m: a transom's depth and height
PANEL = 0.024               # m: a double glazing's thickness
# (0.181) what a cell holds: a glass panel, an opaque one (a spandrel, 6 cm), a glass door (the cell to the floor,
# a handle on each side; only in the bottom row), or nothing
PANELS = ("glass", "solid", "door", "empty")
SOLID = 0.06                # m
LEAF = 0.05                 # m: a door leaf's thickness
HANDLE = (0.03, 0.03, 0.30)     # m: a handle bar (along, across, up)
DOOR_LOW = 1.90             # m: a door's cell at least this high (the transoms far enough apart)
SPANDREL_STYLE = "ArqSynth Painel opaco"
EMBED_TOL = 0.005           # m: (0.188) how far off a wall's line, faces, ends or top a curtain wall still lies in it


def divisions(length, spacing):
    """Equal divisions of `length` no longer than `spacing`: their positions, both ends included."""
    n = max(1, int(math.ceil(length / spacing - 1e-9)))
    return [length * k / n for k in range(n + 1)]


def _panels(text):
    """{(column, row): kind} of the cells that are not glass ("1,0=door;2,3=solid")."""
    out = {}
    for item in (text or "").split(";"):
        if "=" in item:
            cell, kind = item.split("=")
            i, j = (int(v) for v in cell.split(","))
            if kind in PANELS:
                out[(i, j)] = kind
    return out


def _panels_text(panels):
    return ";".join("{},{}={}".format(i, j, k) for (i, j), k in sorted(panels.items()) if k != "glass")


def _along(p, s):
    """Where `s` m along a curtain wall's line is, in its own frame — (x, y) — and the way it runs there; (0.252) on
    its arc when it has one."""
    if p["radius"] is None:
        return np.array((s, 0.0)), np.array((1.0, 0.0))
    r, turn = p["radius"], math.copysign(1.0, p["sweep"])
    a = turn * s / r
    return r * np.array((math.cos(a), math.sin(a))), turn * np.array((-math.sin(a), math.cos(a)))


class CurtainWallMixin:
    def curtain_params(self, guid):
        e = self.by_guid(guid)
        p = self._params(e)
        m = self._placement_si(e)
        x = m[:3, 0] / np.linalg.norm(m[:3, 0])
        length = float(p["Comprimento"])
        out = {"start": m[:3, 3].copy(), "end": m[:3, 3] + x * length, "length": length,
               "height": float(p["Altura"]), "mullions": float(p["Montantes"]), "transoms": float(p["Travessas"]),
               "panels": _panels(p.get("Paineis")), "radius": None, "sweep": None}
        if p.get("Raio"):                          # (0.252) along an arc: placed at its centre, x towards its start
            radius, sweep = float(p["Raio"]), math.radians(float(p["Abertura"]))
            y = m[:3, 1] / np.linalg.norm(m[:3, 1])
            centre = m[:3, 3].copy()
            out.update(radius=radius, sweep=sweep, centre=centre, angle=math.atan2(x[1], x[0]),
                       start=centre + x * radius, end=centre + (x * math.cos(sweep) + y * math.sin(sweep)) * radius)
        return out

    def curtain_grid(self, guid):
        """(xs, zs) the curtain wall's mullions' and transoms' positions along it and up it (both ends included)."""
        p = self.curtain_params(guid)
        return divisions(p["length"], p["mullions"]), divisions(p["height"], p["transoms"])

    def _set_curtain_body(self, cw):
        p = self.curtain_params(cw.GlobalId)
        length, height = p["length"], p["height"]
        if length < MIN_SIZE or height < MIN_SIZE:
            raise EditRefused("too_small")
        xs = divisions(length, p["mullions"])
        zs = divisions(height, p["transoms"])
        panels = {cell: kind for cell, kind in p["panels"].items()                      # (0.181) the cells' panels,
                  if cell[0] < len(xs) - 1 and cell[1] < len(zs) - 1}                   # those still on the grid
        at = lambda s, z: np.append(_along(p, s)[0], z)          # noqa: E731  (0.252: on its arc, when it has one)
        items = []
        mw, md = MULLION
        for x in xs:                                         # (the end ones inside the line)
            x = min(max(x, mw / 2), length - mw / 2)
            items.append(self._box_along(at(x, 0.0), at(x, height), mw, md, ref=np.append(_along(p, x)[1], 0.0)))
        td, th = TRANSOM
        for j, z in enumerate(zs):
            z = min(max(z, th / 2), height - th / 2)
            # a transom runs whole but under a door (the bottom one: the door goes to the floor)
            runs, start = [], 0.0
            for i, (x0, x1) in enumerate(zip(xs, xs[1:])):
                if j == 0 and panels.get((i, 0)) == "door":
                    if x0 > start + 1e-9:
                        runs.append((start, x0))
                    start = x1
            if length > start + 1e-9:
                runs.append((start, length))
            for a, b in runs:                                # (0.252: on an arc, a chord from mullion to mullion)
                cuts = [a] + [x for x in xs if a + 1e-9 < x < b - 1e-9] + [b] if p["radius"] is not None else [a, b]
                for u, v in zip(cuts, cuts[1:]):
                    items.append(self._box_along(at(u, z), at(v, z), td, th))
        for i, (x0, x1) in enumerate(zip(xs, xs[1:])):
            p0, p1 = _along(p, x0)[0], _along(p, x1)[0]          # (the cell's chord: a flat panel)
            chord = float(np.linalg.norm(p1 - p0))
            run = (p1 - p0) / chord
            a, b = p0 + run * mw / 2, p1 - run * mw / 2
            for j, (z0, z1) in enumerate(zip(zs, zs[1:])):
                kind = panels.get((i, j), "glass")
                lo, hi = (0.0 if kind == "door" else z0 + th / 2), z1 - th / 2
                if kind == "empty" or chord - mw <= 0.02 or hi - lo <= 0.02:
                    continue
                mid = (lo + hi) / 2
                thickness = {"glass": PANEL, "solid": SOLID, "door": LEAF}[kind]
                items.append(self._box_along(np.append(a, mid), np.append(b, mid), thickness, hi - lo))
                if kind == "solid":                        # (its own colour in the IFC: grey, not glass)
                    self.file.createIfcStyledItem(items[-1], [self._spandrel_style()], None)
                if kind == "door":                         # (its handles, on both sides, by its free edge)
                    hx, hy, hz = HANDLE
                    for side in (-1, 1):
                        q = b - run * 0.10 + np.array((-run[1], run[0])) * side * (LEAF / 2 + hy / 2)
                        items.append(self._box_along(np.append(q, 1.05 - hz / 2), np.append(q, 1.05 + hz / 2),
                                                     hx, hy, ref=np.append(run, 0.0)))
        f, u = self.file, 1.0 / self.unit_scale
        self._clear_representations(cw)
        api.geometry.assign_representation(f, product=cw, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))
        self._set_qto(cw, "Qto_CurtainWallQuantities", {"Length": length * u, "Height": height * u,
                                                        "Width": md * u, "GrossSideArea": length * height,
                                                        "NetSideArea": length * height})

    def add_curtain_wall(self, start, end, height, mullions, transoms, name, lang="pt", storey=None, embed=False,
                         arc=None):
        """A curtain wall along start -> end (plan; its base at start's level), `height` high: mullions at most
        `mullions` apart, transoms at most `transoms` apart; (0.188) embed: it goes into the wall it lies in (cut
        in it after every change, see IfcCommand); (0.252) arc: (centre (x, y, z: its base), radius, start angle,
        sweep — radians) — along that arc instead (start and end unused). Returns the IfcCurtainWall."""
        if arc is not None:
            centre, radius, angle, sweep = arc
            start = np.asarray(centre, dtype=float)
            length = float(radius) * abs(float(sweep))
            x = np.array((math.cos(angle), math.sin(angle), 0.0))
            if abs(sweep) >= arcs.FULL - 1e-9:
                raise EditRefused("not_editable")
        else:
            start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
            d = np.array((end[0] - start[0], end[1] - start[1], 0.0))
            length = float(np.linalg.norm(d))
            x = d / length if length > 0 else d
        if length < MIN_SIZE or height < MIN_SIZE or mullions < 0.3 or transoms < 0.3:
            raise EditRefused("too_small")
        f = self.file
        cw = api.root.create_entity(f, ifc_class="IfcCurtainWall", name=name)
        m = np.eye(4)
        m[:3, 0], m[:3, 1], m[:3, 3] = x, np.cross((0.0, 0.0, 1.0), x), start
        self._place(cw, m)
        container = self.storey(storey) if storey is not None else self.storey_at(float(start[2]))
        api.spatial.assign_container(f, products=[cw], relating_structure=container)
        frame, glass = self._material("aluminio", lang), self._material("vidro", lang)
        mats = api.material.add_material_set(f, name=name, set_type="IfcMaterialConstituentSet")
        for material, label in ((frame, "Frame"), (glass, "Panel")):
            api.material.add_constituent(f, constituent_set=mats, material=material).Name = label
        api.material.assign_material(f, products=[cw], type="IfcMaterialConstituentSet", material=mats)
        common = api.pset.add_pset(f, product=cw, name="Pset_CurtainWallCommon")
        api.pset.edit_pset(f, pset=common, properties={"IsExternal": True})
        self._mark(cw, "curtain_wall")
        params = {"Comprimento": length, "Altura": float(height), "Montantes": float(mullions),
                  "Travessas": float(transoms)}
        if embed:
            params["Embutir"] = 1.0
        if arc is not None:                                 # (0.252)
            params.update(Raio=float(arc[1]), Abertura=math.degrees(float(arc[3])))
        self._set_params(cw, params)
        self._set_curtain_body(cw)
        return cw

    def set_curtain_wall(self, guid, length=None, height=None, mullions=None, transoms=None):
        """A curtain wall's length (its start stays), height or spacings changed — (0.188) embedded in a wall, within
        it."""
        cw, _ = self._require(guid, "curtain_wall")
        changes = {}
        for value, name, low in ((length, "Comprimento", MIN_SIZE), (height, "Altura", MIN_SIZE),
                                 (mullions, "Montantes", 0.3), (transoms, "Travessas", 0.3)):
            if value is None:
                continue
            if float(value) < low:
                raise EditRefused("too_small")
            changes[name] = float(value)
        p = self.curtain_params(guid)
        if "Comprimento" in changes and p["radius"] is not None:     # (0.252) on its arc: its start stays
            sweep = math.copysign(changes["Comprimento"] / p["radius"], p["sweep"])
            if abs(sweep) >= arcs.FULL - 1e-9:
                raise EditRefused("not_editable")
            changes["Abertura"] = math.degrees(sweep)
        self._set_params(cw, changes)
        self._set_curtain_body(cw)
        host = self.host_wall(guid)
        if host is not None and self._in_wall(guid, host) is None:
            raise EditRefused("cw_outside_wall")

    # ------------------------------------------------------------ embedded in a wall (0.188)

    def _wall_box(self, wall_guid):
        """A straight wall as a WallFrame from its own measures (not its shape, which its openings may cut short):
        x along its axis from its start (its full thickness), y across it (its faces), z up from its base."""
        from ..core.openings import WallFrame
        length, height, thickness = self.wall_params(wall_guid)
        frame = WallFrame(self.placement(wall_guid), length, 0.0, -thickness / 2, thickness / 2, 0.0, height)
        return self.trim_frame(wall_guid, frame)

    def _line_in_wall(self, start, end, height, wall_guid):
        """(x0, x1, y, z0, z1) of a curtain wall's line start -> end (at its base), `height` high, in the wall's frame
        when it lies in the wall — along its axis, between its faces (on one too), its ends and its top within it —
        else None."""
        f = self._wall_box(wall_guid)
        a, b = f.to_local(np.asarray(start, dtype=float)), f.to_local(np.asarray(end, dtype=float))
        tol = EMBED_TOL
        if abs(a[1] - b[1]) > tol or abs(a[2] - b[2]) > tol:
            return None
        x0, x1 = sorted((float(a[0]), float(b[0])))
        z0, z1 = float(a[2]), float(a[2]) + float(height)
        if not (f.y0 - tol <= a[1] <= f.y1 + tol and x0 >= f.x0 - tol and x1 <= f.x0 + f.length + tol
                and z0 >= f.z0 - tol and z1 <= f.z1 + tol):
            return None
        return x0, x1, float(a[1]), z0, z1

    def _in_wall(self, guid, wall_guid):
        """Where the curtain wall lies in the wall — _line_in_wall's, or (0.252) on an arc in a curved wall
        _arc_in_wall's — or None."""
        p = self.curtain_params(guid)
        kind = self.kind_of(wall_guid)
        if p["radius"] is not None:
            return self._arc_in_wall(p, wall_guid) if kind == "curved_wall" else None
        return self._line_in_wall(p["start"], p["end"], p["height"], wall_guid) if kind == "wall" else None

    def wall_for_line(self, start, end, height):
        """The straight wall a curtain wall start -> end, `height` high, would lie in (the first, if more than
        one), or None."""
        for wall in self.file.by_type("IfcWall"):
            if self.kind_of(wall.GlobalId) == "wall" and \
                    self._line_in_wall(start, end, height, wall.GlobalId) is not None:
                return wall.GlobalId
        return None

    def embedding_wall(self, guid):
        """The wall the curtain wall lies in — straight, or (0.252) curved when it runs on an arc — (the first, if
        it lay in more than one), or None."""
        p = self.curtain_params(guid)
        if p["radius"] is None:
            return self.wall_for_line(p["start"], p["end"], p["height"])
        for wall in self.file.by_type("IfcWall"):
            if self.kind_of(wall.GlobalId) == "curved_wall" and self._arc_in_wall(p, wall.GlobalId) is not None:
                return wall.GlobalId
        return None

    # ------------------------------------------------------------ in a curved wall (0.252)

    def curved_wall_at(self, point, height):
        """The curved wall a curtain wall started at `point` (its base), `height` high, would go into — `point`
        between its faces, within its ends, the curtain wall within its foot and top: (its GlobalId, its centre
        (x, y, z), the radius through `point`, its start angle, its sweep) — or None."""
        point = np.asarray(point, dtype=float)
        for wall in self.file.by_type("IfcWall"):
            g = wall.GlobalId
            if self.kind_of(g) != "curved_wall":
                continue
            centre, radius, start, sweep, h, thickness = self.curved_wall_params(g)
            r = float(np.linalg.norm((point - centre)[:2]))
            z = float(point[2] - centre[2])
            if abs(r - radius) > thickness / 2 + EMBED_TOL or z < -EMBED_TOL or z + height > h + EMBED_TOL:
                continue
            angle = math.atan2(point[1] - centre[1], point[0] - centre[0])
            turn = ((angle - start) * (1.0 if sweep >= 0 else -1.0)) % arcs.FULL
            if arcs.is_full(sweep) or turn <= abs(sweep) + EMBED_TOL / radius or turn >= arcs.FULL - EMBED_TOL / radius:
                return g, centre, r, start, sweep
        return None

    def _arc_in_wall(self, p, wall_guid):
        """(lo, hi, offset, z0, z1, forward) of a curtain wall on an arc (its params p) in a curved wall: its ends
        along the wall's axis (m from its start, lo < hi), its line off the axis (+ away from the centre), its foot
        and top over the wall's base, whether it runs as the wall does — when it lies in it (the same centre,
        between its faces, within its ends and its top), else None."""
        centre, radius, start, sweep, height, thickness = self.curved_wall_params(wall_guid)
        tol = EMBED_TOL
        c = p["centre"]
        if np.linalg.norm((c - centre)[:2]) > tol or abs(p["radius"] - radius) > thickness / 2 + tol:
            return None
        z0 = float(c[2] - centre[2])
        z1 = z0 + p["height"]
        if z0 < -tol or z1 > height + tol:
            return None
        turn = 1.0 if sweep >= 0 else -1.0
        t0 = ((p["angle"] - start) * turn) % arcs.FULL       # (its start, the wall's way round from the wall's)
        run = p["sweep"] * turn
        slack = tol / radius
        if not arcs.is_full(sweep):
            if t0 > arcs.FULL - slack:
                t0 -= arcs.FULL
            if min(t0, t0 + run) < -slack or max(t0, t0 + run) > abs(sweep) + slack:
                return None
        lo, hi = sorted((t0, t0 + run))
        return max(lo, 0.0) * radius, hi * radius, p["radius"] - radius, z0, z1, run > 0

    def _set_sector_body(self, opening, wall_guid, lo, hi, z0, z1):
        """A curved wall's opening from `lo` to `hi` m along its axis, `z0` to `z1` over its base: the ring's
        sector from just outside one face to just beyond the other, extruded up (true arcs, as the wall's body)."""
        f, u = self.file, 1.0 / self.unit_scale
        _c, radius, _start, sweep, _h, thickness = self.curved_wall_params(wall_guid)
        turn = 1.0 if sweep >= 0 else -1.0
        a0, a1 = turn * lo / radius, turn * hi / radius            # (in the wall's frame: its start at 0)
        ro = (radius + thickness / 2 + MARGIN) * u
        ri = max(radius - thickness / 2 - MARGIN, MIN_SIZE / 4) * u
        pts = [(ro * math.cos(a), ro * math.sin(a)) for a in (a0, (a0 + a1) / 2, a1)] + \
            [(ri * math.cos(a), ri * math.sin(a)) for a in (a1, (a0 + a1) / 2, a0)]
        curve = f.createIfcIndexedPolyCurve(
            f.createIfcCartesianPointList2D([(float(x), float(y)) for x, y in pts]),
            [f.createIfcArcIndex((1, 2, 3)), f.createIfcLineIndex((3, 4)), f.createIfcArcIndex((4, 5, 6)),
             f.createIfcLineIndex((6, 1))], False)
        solid = f.createIfcExtrudedAreaSolid(
            f.createIfcArbitraryClosedProfileDef("AREA", None, curve),
            f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)), f.createIfcDirection((0.0, 0.0, 1.0)),
                                        f.createIfcDirection((1.0, 0.0, 0.0))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float((z1 - z0) * u))
        self._clear_representations(opening)
        api.geometry.assign_representation(f, product=opening, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", [solid]))
        m = self._placement_si(self.by_guid(wall_guid))
        m[:3, 3] += m[:3, 2] * z0
        self._place(opening, m)

    def _embed_arc(self, cw, wall_guid):
        """Its opening in a curved wall: made (the curtain wall filling it, placed in it as a door is) or fitted
        again, and where it is kept on it."""
        lo, hi, offset, z0, z1, forward = self._in_wall(cw.GlobalId, wall_guid)
        world = self._placement_si(cw)
        if cw.FillsVoids:
            opening = cw.FillsVoids[0].RelatingOpeningElement
            self._set_sector_body(opening, wall_guid, lo, hi, z0, z1)
        else:
            opening = api.root.create_entity(self.file, ifc_class="IfcOpeningElement", name=cw.Name or "",
                                             predefined_type="OPENING")
            self._set_sector_body(opening, wall_guid, lo, hi, z0, z1)
            api.feature.add_feature(self.file, feature=opening, element=self.by_guid(wall_guid))
            api.feature.add_filling(self.file, opening=opening, element=cw)
            cw.ObjectPlacement.PlacementRelTo = opening.ObjectPlacement
        self._set_params(opening, {"AoLongo": float(lo), "Largura": float(hi - lo), "Desvio": float(offset),
                                   "Sentido": 1 if forward else -1, "Peitoril": float(z0), "Altura": float(z1 - z0)})
        self._place(cw, world)

    def _refit_arc_curtain(self, guid, wall_guid, s, sill, offset, forward):
        """A curtain wall in a curved wall put again — its near end `s` m along the wall's axis, its foot `sill` over
        its base, its line `offset` off the axis (kept between the faces), running as the wall (forward) or against
        it — with its own length and height (its arc follows the wall's radius): it and its opening. Refused when
        it would leave the wall."""
        cw = self.by_guid(guid)
        p = self.curtain_params(guid)
        centre, radius, start, sweep, height, thickness = self.curved_wall_params(wall_guid)
        offset = min(max(offset, -thickness / 2), thickness / 2)
        mine = radius + offset
        span = p["length"] / mine if mine > MIN_SIZE / 2 else arcs.FULL
        hi = s + span * radius
        if span >= arcs.FULL or s < -1e-6 or sill < -1e-6 or sill + p["height"] > height + 1e-6 or \
                (not arcs.is_full(sweep) and hi > radius * abs(sweep) + 1e-6):
            raise EditRefused("opening_outside")
        turn = 1.0 if sweep >= 0 else -1.0
        angle = arcs.angle_along(start, sweep, radius, s if forward else hi)
        m = np.eye(4)
        m[:3, 0] = (math.cos(angle), math.sin(angle), 0.0)
        m[:3, 1] = (-math.sin(angle), math.cos(angle), 0.0)
        m[:3, 3] = (centre[0], centre[1], centre[2] + sill)
        self._set_params(cw, {"Raio": float(mine), "Abertura": math.degrees(turn * span if forward else -turn * span)})
        self._set_curtain_body(cw)
        opening = cw.FillsVoids[0].RelatingOpeningElement
        self._set_sector_body(opening, wall_guid, s, hi, sill, sill + p["height"])
        self._set_params(opening, {"AoLongo": float(s), "Largura": float(hi - s), "Desvio": float(offset),
                                   "Sentido": 1 if forward else -1, "Peitoril": float(sill),
                                   "Altura": float(p["height"])})
        self._place(cw, m)

    def embeds(self, guid):
        """The curtain wall goes into the wall it lies in (its Embutir)."""
        return bool(self._params(self.by_guid(guid)).get("Embutir"))

    def set_embedding(self, guid, on):
        """The curtain wall made to go into the wall it lies in (refused when it lies in none), or to come out of
        it. The walls whose shape changed."""
        cw, _ = self._require(guid, "curtain_wall")
        if on and self.host_wall(guid) is None and self.embedding_wall(guid) is None:
            raise EditRefused("cw_no_wall")
        self._set_params(cw, {"Embutir": 1.0 if on else 0.0})
        return self.fit_embedding(guid)

    def fit_embedding(self, guid):
        """The curtain wall's opening as the curtain wall is now: made in the wall it lies in (when it embeds
        itself), fitted to it again, or taken away (it no longer embeds itself, or it left the wall). The walls
        whose shape changed."""
        cw = self.by_guid(guid)
        old = self.host_wall(guid)
        new = None
        if self.embeds(guid):
            new = old if old is not None and self._in_wall(guid, old) is not None else self.embedding_wall(guid)
        if old is not None and old != new:
            self._unembed(cw)
        if new is not None:
            self._embed(cw, new)
        return sorted({w for w in (old, new) if w})

    def follow_embedded(self, changed):
        """The curtain walls among `changed` fitted into their walls again (fit_embedding): the walls whose shape
        changed with them."""
        out = []
        for g in list(changed):
            if self.by_guid(g) is not None and self.kind_of(g) == "curtain_wall":
                out += [w for w in self.fit_embedding(g) if w not in out]
        return out

    def _embed(self, cw, wall_guid):
        """Its opening in the wall: made (the curtain wall filling it, placed in it as a door is) or fitted again."""
        if self.kind_of(wall_guid) == "curved_wall":                  # (0.252)
            self._embed_arc(cw, wall_guid)
            return
        x0, x1, _y, z0, z1 = self._in_wall(cw.GlobalId, wall_guid)
        f = self._wall_box(wall_guid)
        lo, hi = (x0, f.y0 - MARGIN, z0), (x1, f.y1 + MARGIN, z1)
        world = self._placement_si(cw)
        if cw.FillsVoids:
            self._set_box_body(cw.FillsVoids[0].RelatingOpeningElement, f.matrix, lo, hi)
        else:
            opening = self.add_void(wall_guid, f.matrix, lo, hi, cw.Name or "")
            api.feature.add_filling(self.file, opening=opening, element=cw)
            cw.ObjectPlacement.PlacementRelTo = opening.ObjectPlacement
        self._place(cw, world)

    def _unembed(self, cw):
        """Out of its wall: its opening taken away, the curtain wall where it is (placed in its storey again)."""
        world = self._placement_si(cw)
        openings = [rel.RelatingOpeningElement for rel in cw.FillsVoids or ()]
        api.feature.remove_filling(self.file, element=cw)
        container = ifcopenshell.util.element.get_container(cw)
        cw.ObjectPlacement.PlacementRelTo = container.ObjectPlacement if container is not None else None
        self._place(cw, world)
        for opening in openings:
            api.root.remove_product(self.file, product=opening)

    def curtain_filling_state(self, guid):
        """Where an embedded curtain wall is in its wall, as filling_state gives a door's: s (its left end along the
        wall), sill, width (its length), height; and y (its line across the wall), forward (it runs as the wall)."""
        cw = self.by_guid(guid)
        opening = cw.FillsVoids[0].RelatingOpeningElement
        wall = opening.VoidsElements[0].RelatingBuildingElement
        p = self.curtain_params(guid)
        if self.kind_of(wall.GlobalId) == "curved_wall":       # (0.252) the wall unrolled: s along its axis
            from .curved_walls import unrolled_frame
            q = self._params(opening)
            frame = unrolled_frame(*self.curved_wall_params(wall.GlobalId))
            return {"wall": wall.GlobalId, "frame": frame, "opening": opening, "matrix": frame.matrix,
                    "kind": "curtain_wall", "s": float(q["AoLongo"]), "sill": float(q["Peitoril"]),
                    "width": float(q["Largura"]), "height": p["height"], "side": -1, "curtain": True,
                    "curved": True, "offset": float(q.get("Desvio") or 0.0), "forward": int(q.get("Sentido") or 1) > 0}
        frame = self._wall_box(wall.GlobalId)
        a, b = frame.to_local(p["start"]), frame.to_local(p["end"])
        return {"wall": wall.GlobalId, "frame": frame, "opening": opening, "matrix": frame.matrix,
                "kind": "curtain_wall", "s": float(min(a[0], b[0])), "sill": float(a[2] - frame.z0),
                "width": p["length"], "height": p["height"], "side": -1, "curtain": True, "y": float(a[1]),
                "forward": bool(b[0] > a[0])}

    def _refit_curtain(self, guid, st, s, sill):
        """An embedded curtain wall slid along its wall (s: its left end) and up (sill): it and its opening."""
        if st.get("curved"):                                   # (0.252) along a curved wall
            self._refit_arc_curtain(guid, st["wall"], s, sill, st["offset"], st["forward"])
            return
        f, m = st["frame"], st["matrix"]
        z = f.z0 + sill
        self._set_box_body(st["opening"], m, (s, f.y0 - MARGIN, z), (s + st["width"], f.y1 + MARGIN, z + st["height"]))
        local = np.eye(4)
        local[:3, 3] = (s if st["forward"] else s + st["width"], st["y"], z)
        if not st["forward"]:
            local[:2, :2] = ((-1.0, 0.0), (0.0, -1.0))
        self._place(self.by_guid(guid), m @ local)

    def _spandrel_style(self):
        """(0.181) The surface style of the opaque panels (a grey aluminium sheet), made once."""
        for s in self.file.by_type("IfcSurfaceStyle"):
            if s.Name == SPANDREL_STYLE:
                return s
        style = api.style.add_style(self.file, name=SPANDREL_STYLE)
        api.style.add_surface_style(self.file, style=style, ifc_class="IfcSurfaceStyleShading",
                                    attributes={"SurfaceColour": {"Name": None, "Red": 0.49, "Green": 0.52,
                                                                  "Blue": 0.55}})
        return style

    def curtain_cell_at(self, guid, point):
        """(0.181) The cell (column, row) of the curtain wall at a world point on it, or None."""
        m = self._placement_si(self.by_guid(guid))
        local = np.linalg.inv(m) @ np.array((float(point[0]), float(point[1]), float(point[2]), 1.0))
        xs, zs = self.curtain_grid(guid)
        p = self.curtain_params(guid)
        s = float(local[0])
        if p["radius"] is not None:                            # (0.252) how far round its arc
            s = arcs.along_at(0.0, p["sweep"], p["radius"], math.atan2(local[1], local[0]))
        if not (xs[0] - 1e-6 <= s <= xs[-1] + 1e-6 and zs[0] - 1e-6 <= local[2] <= zs[-1] + 1e-6):
            return None
        i = min(max(int(np.searchsorted(xs, s) - 1), 0), len(xs) - 2)
        j = min(max(int(np.searchsorted(zs, local[2]) - 1), 0), len(zs) - 2)
        return i, j

    def curtain_cell_box(self, guid, cell):
        """(0.181) The four world corners of a cell (on the curtain wall's line — 0.252: its chord), for showing it."""
        m = self._placement_si(self.by_guid(guid))
        xs, zs = self.curtain_grid(guid)
        p = self.curtain_params(guid)
        i, j = cell
        return [(m @ np.append(_along(p, x)[0], (z, 1.0)))[:3]
                for x, z in ((xs[i], zs[j]), (xs[i + 1], zs[j]), (xs[i + 1], zs[j + 1]), (xs[i], zs[j + 1]))]

    def set_curtain_panel(self, guid, cell, kind):
        """(0.181) A cell's panel: glass, opaque, a door (only in the bottom row) or none."""
        cw, _ = self._require(guid, "curtain_wall")
        if kind not in PANELS:
            raise EditRefused("not_editable")
        xs, zs = self.curtain_grid(guid)
        i, j = cell
        if not (0 <= i < len(xs) - 1 and 0 <= j < len(zs) - 1):
            raise EditRefused("not_editable")
        if kind == "door" and j != 0:
            raise EditRefused("cw_door_row")
        if kind == "door" and zs[1] - zs[0] < DOOR_LOW:
            raise EditRefused("cw_door_low")
        panels = self.curtain_params(guid)["panels"]
        panels[(i, j)] = kind
        self._set_params(cw, {"Paineis": _panels_text(panels)})
        self._set_curtain_body(cw)
