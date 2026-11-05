"""Profiles run along a path (0.174, Phase 10, step 2: the Profile Pen), mixed into IfcModel: an IfcCovering —
SKIRTINGBOARD (a skirting board) or MOLDING (a cornice, a dado rail, an outside cornice) — its body the section swept
along its path (core/profiles.sweep: an IfcTriangulatedFaceSet, its corners mitred, read straight from the file),
broken where a door or a window of a wall it runs along crosses it. Round a room: its path is the room's outline, the
section into the room, found again from the room's point when its walls change — as the rooms are (0.99) — and the
doors put in, moved or taken away cut it again.

ArqSynth_Parametros: Elemento "profile", Perfil (its key in core/profiles.PROFILES), Caminho (its rings "x,y;x,y…"
joined by "|", in its own frame — placed at the first point, on the floor's level —, so that moving it moves them),
Fechado (each ring goes round), Largura, Altura (the section's), Cota (its foot over the floor), Lado (+1: the
section to the path's left), SalaX / SalaY (round a room: the point it was made from, in its own frame)."""

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import profiles as core_profiles
from .edit import EditRefused

api = ifcopenshell.api
REACH = 0.05                # m: a wall this near its path cuts it at its doors and windows


def _ring_text(pts):
    return ";".join("{:.6f},{:.6f}".format(x, y) for x, y in pts)


def _rings(text):
    return [[tuple(float(v) for v in pair.split(",")) for pair in ring.split(";") if pair]
            for ring in (text or "").split("|") if ring]


class ProfileMixin:
    def profile_params(self, guid):
        """{profile, width, height, foot, side, closed, rings (world plan), level (its floor's), room (world plan
        point or None), length} of a profile made by this program."""
        e = self.by_guid(guid)
        p = self._params(e)
        m = self._placement_si(e)
        key = p.get("Perfil") or "rodape"
        world = lambda q: tuple((m @ np.array((q[0], q[1], 0.0, 1.0)))[:2])        # noqa: E731
        rings = [[world(q) for q in ring] for ring in _rings(p.get("Caminho"))]
        room = (world((float(p["SalaX"]), float(p["SalaY"]))) if p.get("SalaX") is not None else None)
        custom = None
        if core_profiles.is_custom(key):                 # (0.245) a project's own: its section kept with it
            custom = (_rings(p.get("Seccao")) or [[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]])[0]
            size = (0.02, 0.02)
        else:
            size = core_profiles.PROFILES.get(key, core_profiles.PROFILES["rodape"])[2]
        return {"profile": key, "width": float(p.get("Largura") or size[0]), "height": float(p.get("Altura") or size[1]),
                "foot": float(p.get("Cota") or 0.0), "side": 1 if int(p.get("Lado") or 1) > 0 else -1,
                "closed": bool(p.get("Fechado")), "rings": rings, "level": float(m[2, 3]), "room": room,
                "length": float(p.get("Comprimento") or 0.0), "custom": custom}

    # ------------------------------------------------------------ a project's own profiles (0.245)

    def custom_profiles(self):
        """{name: [(a, b)…] m} of the project's own profiles: IfcArbitraryClosedProfileDefs with a name that nothing
        uses — a library of sections, drawn in the program (add_custom_profile)."""
        out = {}
        s = self.unit_scale
        for prof in self.file.by_type("IfcArbitraryClosedProfileDef"):
            curve = prof.OuterCurve
            if not prof.ProfileName or not curve.is_a("IfcIndexedPolyCurve") or self.file.get_total_inverses(prof):
                continue
            pts = [(float(a) * s, float(b) * s) for a, b in curve.Points.CoordList]
            out[prof.ProfileName] = pts[:-1] if len(pts) > 3 and pts[0] == pts[-1] else pts
        return out

    def add_custom_profile(self, name, points):
        """A section (points [(a, b)…] m: a out of the wall, b up) kept in the project under `name`, for profiles to
        run. Refused when the name is taken or it is no section."""
        name = str(name).strip()
        if not name or name in self.custom_profiles():
            raise EditRefused("profile_name")
        try:
            unit, w, h = core_profiles.unit_section(points)
        except ValueError as exc:
            raise EditRefused(str(exc)) from None
        u = 1.0 / self.unit_scale
        coords = [(float(a * w * u), float(b * h * u)) for a, b in unit]
        curve = self.file.createIfcIndexedPolyCurve(self.file.createIfcCartesianPointList2D(coords + coords[:1]),
                                                    None, False)
        return self.file.createIfcArbitraryClosedProfileDef("AREA", name, curve)

    def _custom_section(self, key):
        """(its section in a unit square, width, height) of a project's own profile (its key "custom:" + name)."""
        found = self.custom_profiles().get(key[len(core_profiles.CUSTOM):])
        if found is None:
            raise EditRefused("not_editable")
        return core_profiles.unit_section(found)

    def _profile_walls(self, storey, rings):
        """The walls of the storey that run along the path (within REACH of it)."""
        from shapely.geometry import LineString, Polygon
        lines = [LineString(list(r) + ([r[0]] if len(r) > 2 else [])) for r in rings if len(r) > 1]
        out = []
        for rel in (self.storey(storey).ContainsElements or ()) if storey else ():
            for w in rel.RelatedElements:
                if self.kind_of(w.GlobalId) != "wall":
                    continue
                band = self._wall_band(w.GlobalId)
                if band is not None and any(Polygon(band).distance(line) <= REACH for line in lines):
                    out.append(w.GlobalId)
        return out

    def wall_face_run(self, wall, point):
        """(0.304) The faces a wall sweep runs along from `point` (plan, on a straight wall's face): that face and, on
        the same side, those of the walls joined to it (at a corner, at a T) — the outline of their union, its
        corners mitred — up to a free end; all round when it closes (a building's outside, a room's inside).
        ([points], closed), the walls on the run's left (the sweep to its right), or None."""
        from shapely.geometry import LineString, Point, Polygon
        from shapely.geometry.polygon import orient
        from shapely.ops import unary_union
        if self.by_guid(wall) is None or self.kind_of(wall) != "wall":
            return None
        storey = self.storey_of(wall)
        chain, todo = {wall}, [wall]
        while todo:                                       # (the walls joined to it, and to those, on its storey)
            g = todo.pop()
            for _rel, a, _ea, b, _eb in self.wall_joints(g):
                for h in (a, b):
                    if h not in chain and self.kind_of(h) == "wall" and self.storey_of(h) == storey:
                        chain.add(h)
                        todo.append(h)
        axes = [(np.asarray(s, dtype=float), np.asarray(e, dtype=float), t) for s, e, t in
                (self.wall_axis(g) for g in chain)]
        # (the hairline slits left where two walls touch closed: the run would go in and out of them)
        union = unary_union([Polygon(self._wall_band(g)) for g in chain]).buffer(
            1e-4, join_style="mitre").buffer(-1e-4, join_style="mitre")
        here = Point(float(point[0]), float(point[1]))
        polygons = [p for p in getattr(union, "geoms", [union]) if not p.is_empty]
        if not polygons:
            return None
        polygon = orient(min(polygons, key=lambda p: p.boundary.distance(here)).simplify(1e-6), 1.0)
        rings = [list(polygon.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in polygon.interiors]

        def is_face(a, b):
            """A side of the outline that is a wall's face (along its axis, half its thickness off), not an end."""
            a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
            v = b - a
            size = float(np.hypot(*v))
            if size < 1e-3:
                return True                             # (a hair where two walls meet: the run goes on over it)
            v /= size
            mid = (a + b) / 2
            for s, e, t in axes:
                d = (e - s)[:2] / np.linalg.norm((e - s)[:2])
                off = mid - s[:2]
                if abs(d[0] * v[1] - d[1] * v[0]) < 1e-4 and abs(abs(d[0] * off[1] - d[1] * off[0]) - t / 2) < 1e-3:
                    return True
            return False

        _d, r_index, i = min((LineString([r[k], r[(k + 1) % len(r)]]).distance(here), ri, k)
                             for ri, r in enumerate(rings) for k in range(len(r)))
        ring = rings[r_index]
        n = len(ring)
        faces = [is_face(ring[k], ring[(k + 1) % n]) for k in range(n)]
        if not faces[i]:
            return None
        if all(faces):
            return [tuple(q) for q in ring], True
        first = last = i
        while faces[(first - 1) % n]:
            first = (first - 1) % n
        while faces[(last + 1) % n]:
            last = (last + 1) % n
        return [tuple(ring[(first + k) % n]) for k in range((last - first) % n + 2)], False

    def wall_sweep_rings(self, guid):
        """(0.304) A wall sweep's run found again from its wall (the point it was made from, which goes with the
        wall): ([points], closed), or None when the wall is gone."""
        p = self._params(self.by_guid(guid))
        wall = p.get("Parede")
        if not wall or self.by_guid(wall) is None:
            return None
        m = self._placement_si(self.by_guid(wall))
        q = m @ np.array((float(p.get("ParedeX") or 0.0), float(p.get("ParedeY") or 0.0), 0.0, 1.0))
        return self.wall_face_run(wall, q[:2])

    def _wall_band(self, wall):
        from ..core.walls import footprint
        length, _h, thickness = self.wall_params(wall)
        start_cut, end_cut = self.wall_cuts(self.by_guid(wall))
        m = self.placement(wall)
        return [tuple((m @ np.array((x, y, 0.0, 1.0)))[:2]) for x, y in footprint(length, thickness, start_cut, end_cut)]

    def _profile_cuts(self, walls, z_lo, z_hi, width):
        """The plan rectangles (world) of the doors and windows of these walls that cross the band z_lo..z_hi: the
        opening's width, across the wall and `width` beyond each face."""
        from shapely.geometry import Polygon
        out = []
        for wall in walls:
            m = self.placement(wall)
            frame = self.element_frame(wall)
            reach = width + REACH
            for gid, lo, hi, _filled, _box in self.voids(wall):
                if self.reveal_params(gid) is not None:
                    continue                            # (0.305: a reveal is no door)
                zl, zh = float(lo[2] + m[2, 3]), float(hi[2] + m[2, 3])
                if zh <= z_lo + 1e-6 or zl >= z_hi - 1e-6:
                    continue
                corners = [(lo[0], frame.y0 - reach), (hi[0], frame.y0 - reach), (hi[0], frame.y1 + reach),
                           (lo[0], frame.y1 + reach)]
                out.append(Polygon([tuple((m @ np.array((x, y, 0.0, 1.0)))[:2]) for x, y in corners]))
        return out

    def profile_runs(self, guid):
        """[(points [(x, y)…] world, closed)] the profile's runs after the doors' and windows' cuts."""
        from shapely.geometry import LineString
        from shapely.ops import linemerge, unary_union
        p = self.profile_params(guid)
        z_lo = p["level"] + p["foot"]
        walls = self._profile_walls(self.storey_of(guid), p["rings"])
        cuts = self._profile_cuts(walls, z_lo, z_lo + p["height"], p["width"])
        cut = unary_union(cuts) if cuts else None
        out = []
        for ring in p["rings"]:
            closed = p["closed"] and len(ring) > 2
            line = LineString(list(ring) + ([ring[0]] if closed else []))
            if cut is None or not line.intersects(cut):
                out.append((list(ring), closed))
                continue
            rest = line.difference(cut)
            if rest.is_empty:
                continue
            rest = linemerge(rest) if rest.geom_type == "MultiLineString" else rest
            for piece in getattr(rest, "geoms", [rest]):
                if piece.length >= 0.02:
                    out.append(([tuple(c) for c in piece.coords], False))
        return out

    def _set_run_body(self, e):
        f, u = self.file, 1.0 / self.unit_scale
        p = self.profile_params(e.GlobalId)
        sec = core_profiles.section(p["profile"], p["width"], p["height"], p["side"], custom=p["custom"])
        m = self._placement_si(e)
        inv = np.linalg.inv(m)
        verts, tris, total = [], [], 0.0
        count = 0
        for pts, closed in self.profile_runs(e.GlobalId):
            v, t = core_profiles.sweep(pts, closed, sec, p["level"] + p["foot"])
            if not len(t):
                continue
            local = (inv @ np.column_stack((v, np.ones(len(v)))).T).T[:, :3]
            verts.append(local)
            tris.append(t + count)
            count += len(v)
            total += core_profiles.length(pts, closed)
        if not verts:
            raise EditRefused("profile_short")
        verts, tris = np.concatenate(verts), np.concatenate(tris)
        self._clear_representations(e)
        item = f.createIfcTriangulatedFaceSet(
            f.createIfcCartesianPointList3D([tuple(float(c * u) for c in row) for row in verts]), None, True,
            [tuple(int(i) + 1 for i in row) for row in tris], None)
        api.geometry.assign_representation(f, product=e, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "Tessellation", [item]))
        self._set_params(e, {"Comprimento": round(total, 4)})
        self._set_qto(e, "Qto_CoveringBaseQuantities", {"Width": p["width"] * u})

    def profile_top(self, storey, rings):
        """The level a cornice goes under: the lowest top of the walls along the path, else the storey's height."""
        walls = self._profile_walls(storey, rings)
        tops = [float(self.element_frame(w).z1 + self.placement(w)[2, 3]) for w in walls]
        return min(tops) if tops else self._level(storey) + self._space_height(storey)

    def add_profile(self, rings, closed, key, name, storey, level, width=None, height=None, foot=None, side=1,
                    room=None, lang="pt", wall=None):
        """A profile (core/profiles.PROFILES) along `rings` [[(x, y)…]…] (world plan) on the floor at `level`: its
        section width × height (the profile's own when None), its foot over the floor (its own, or a cornice under
        the walls' top when None), to the path's left (side +1) or right; room: the plan point it goes round;
        (0.304) wall: (its GlobalId, the plan point clicked on its face) — a wall sweep, found again from there when
        the wall changes. Returns the IfcCovering."""
        extra = {}
        if core_profiles.is_custom(key):                 # (0.245) a project's own: its section drawn, at its size
            unit, w0, h0 = self._custom_section(key)
            size = (w0, h0)
            extra["Seccao"] = _ring_text(unit)
        elif key in core_profiles.PROFILES:
            size = core_profiles.PROFILES[key][2]
        else:
            raise EditRefused("not_editable")
        kind, material = core_profiles.spec(key)
        width = float(size[0] if width is None else width)
        height = float(size[1] if height is None else height)
        if not (core_profiles.MIN_SIZE <= width <= core_profiles.MAX_SIZE and
                core_profiles.MIN_SIZE <= height <= core_profiles.MAX_SIZE):
            raise EditRefused("profile_size")
        rings = [[tuple(map(float, q[:2])) for q in r] for r in rings]
        if not rings or sum(core_profiles.length(r, closed) for r in rings) < 0.05:
            raise EditRefused("profile_short")
        if foot is None:
            foot = core_profiles.foot(key, height, self.profile_top(storey, rings) - level)
        f = self.file
        e = api.root.create_entity(f, ifc_class="IfcCovering", name=name, predefined_type=kind)
        x0, y0 = rings[0][0]
        m = np.eye(4)
        m[:3, 3] = (x0, y0, level)
        self._place(e, m)
        api.spatial.assign_container(f, products=[e], relating_structure=self.storey(storey))
        api.material.assign_material(f, products=[e], type="IfcMaterial", material=self._material(material, lang))
        common = api.pset.add_pset(f, product=e, name="Pset_CoveringCommon")
        api.pset.edit_pset(f, pset=common, properties={"IsExternal": key == "cimalha"})
        self._mark(e, "profile")
        params = {"Perfil": key, "Caminho": "|".join(_ring_text([(x - x0, y - y0) for x, y in r]) for r in rings),
                  "Fechado": bool(closed), "Largura": width, "Altura": height, "Cota": float(foot),
                  "Lado": 1 if side > 0 else -1}
        if room is not None:
            params.update(SalaX=float(room[0]) - x0, SalaY=float(room[1]) - y0)
        if wall is not None:                            # (0.304) the point in the wall's own frame: it goes with it
            inv = np.linalg.inv(self._placement_si(self.by_guid(wall[0])))
            q = inv @ np.array((float(wall[1][0]), float(wall[1][1]), 0.0, 1.0))
            params.update(Parede=wall[0], ParedeX=float(q[0]), ParedeY=float(q[1]))
        params.update(extra)
        self._set_params(e, params)
        self._set_run_body(e)
        return e

    def room_rings(self, storey, point):
        """The rings of the room where `point` is (its outline counter-clockwise, round its columns), the room on
        their left — or None when it is not enclosed."""
        from shapely.geometry.polygon import orient
        polygon = self.room_region(storey, point)
        if polygon is None:
            return None
        polygon = orient(polygon, 1.0)
        return [[tuple(c) for c in polygon.exterior.coords[:-1]]] + \
            [[tuple(c) for c in ring.coords[:-1]] for ring in polygon.interiors]

    def set_profile(self, guid, profile=None, width=None, height=None, foot=None, side=None):
        """A profile's section (another of the catalogue: its own size, and its foot unless given), its size, its
        foot over the floor, its side."""
        e, _ = self._require(guid, "profile")
        p = self.profile_params(guid)
        changes = {}
        if profile is not None and profile != p["profile"]:
            if core_profiles.is_custom(profile):        # (0.245) a project's own
                unit, w0, h0 = self._custom_section(profile)
                size = (w0, h0)
                changes["Seccao"] = _ring_text(unit)
            elif profile in core_profiles.PROFILES:
                size = core_profiles.PROFILES[profile][2]
            else:
                raise EditRefused("not_editable")
            kind, material = core_profiles.spec(profile)
            changes.update(Perfil=profile, Largura=float(size[0]), Altura=float(size[1]))
            if foot is None:
                top = self.profile_top(self.storey_of(guid), p["rings"]) - p["level"]
                changes["Cota"] = core_profiles.foot(profile, size[1], top)
            e.PredefinedType = kind
            api.material.unassign_material(self.file, products=[e])
            api.material.assign_material(self.file, products=[e], type="IfcMaterial",
                                         material=self._material(material, "pt"))
        for key, value in (("Largura", width), ("Altura", height)):
            if value is not None:
                if not core_profiles.MIN_SIZE <= float(value) <= core_profiles.MAX_SIZE:
                    raise EditRefused("profile_size")
                changes[key] = float(value)
        if foot is not None:
            if float(foot) < 0.0:
                raise EditRefused("profile_foot")
            changes["Cota"] = float(foot)
        if side is not None:
            changes["Lado"] = 1 if int(side) > 0 else -1
        self._set_params(e, changes)
        self._set_run_body(e)

    def profiles(self):
        return [e for e in self.file.by_type("IfcCovering") if self._params(e).get("Elemento") == "profile"]

    def follow_profiles(self, changed):
        """After walls, doors or windows changed: the profiles on their storeys made again — round a room, its
        outline found again from its point; along a path, cut again at the doors. Returns those that changed."""
        kinds = ("wall", "curved_wall", "column", "door", "window", "opening")
        storeys = {self.storey_of(g) for g in changed if self.by_guid(g) is not None and self.kind_of(g) in kinds}
        mine = {g for g in changed if self.by_guid(g) is not None and self.kind_of(g) == "profile"}
        storeys.discard(None)
        out = []
        for e in self.profiles():
            g = e.GlobalId
            storey = self.storey_of(g)
            if storey not in storeys and g not in mine:
                continue
            p = self.profile_params(g)
            inv = np.linalg.inv(self._placement_si(e))
            local = lambda q: tuple((inv @ np.array((q[0], q[1], p["level"], 1.0)))[:2])            # noqa: E731
            if p["room"] is not None:
                rings = self.room_rings(storey, p["room"])
                if rings is not None:
                    self._set_params(e, {"Caminho": "|".join(_ring_text([local(q) for q in r]) for r in rings)})
            elif self._params(e).get("Parede"):         # (0.304) a wall sweep: along its wall's faces again
                run = self.wall_sweep_rings(g)
                if run is not None:
                    self._set_params(e, {"Caminho": _ring_text([local(q) for q in run[0]]), "Fechado": run[1]})
            try:
                self._set_run_body(e)
            except EditRefused:                     # (cut away whole: kept as it was)
                continue
            out.append(g)
        return out

    def profile_pieces(self, guid):
        """[(length, angle at its start, angle at its end)] its straight pieces, as a joiner cuts them."""
        p = self.profile_params(guid)
        out = []
        for pts, closed in self.profile_runs(guid):
            out += core_profiles.pieces(pts, closed, p["width"], p["side"])
        return out
