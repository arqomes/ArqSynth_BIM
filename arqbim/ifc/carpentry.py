"""A roof's carpentry in the IFC (0.276), mixed into IfcModel: an IfcElementAssembly (USERDEFINED «Madeiramento»)
aggregating its pieces, IfcMember each — the wall plates PLATE, the rafters (and the hip and valley rafters)
RAFTER, the purlins PURLIN, the ridge board and the battens USERDEFINED («Fileira», «Ripa»: IFC4 has no kind of
their own) — each a closed IfcTriangulatedFaceSet (its 8 corners, bevelled ends), of wood. Made from the roof's
waters and edges (core/roof_carpentry) and the walls under its waters (the plates on their top).

The roof rests on its carpentry, which rests on the walls: made, its cover goes up by as much as the carpentry is
deep — the plate, then the rafters and the battens square to the slope — so that the rafters lie on the plates'
inner edge (as the cover itself did on the walls', 0.275); taken away, it comes down by as much (kept in its
parameters: MadeiramentoSubida). The roof changed, its carpentry is made again (follow_carpentry).

ArqSynth_Parametros of the assembly: Elemento "carpentry", Cobertura (the roof's GlobalId), Madeiramento (its
settings, JSON); of the roof: Madeiramento (the assembly's GlobalId), MadeiramentoSubida (what it went up, JSON:
{"roof": m} or {"i,k": m} for a roof by blocks' block i side k)."""

import json
import math

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import roof_blocks as core_blocks
from ..core import roof_carpentry as core_carpentry
from ..core import roofs as core_roofs
from .edit import EditRefused

api = ifcopenshell.api
KIND = {"frechal": ("PLATE", None), "caibro": ("RAFTER", None), "rincao": ("RAFTER", None),
        "laro": ("RAFTER", None), "terca": ("PURLIN", None), "fileira": ("USERDEFINED", "Fileira"),
        "ripa": ("USERDEFINED", "Ripa")}
NAMES = {"frechal": ("Frechal", "Wall plate"), "caibro": ("Caibro", "Rafter"),
         "rincao": ("Vara de rincão", "Hip rafter"), "laro": ("Vara de laró", "Valley rafter"),
         "terca": ("Terça", "Purlin"), "fileira": ("Fileira", "Ridge board"), "ripa": ("Ripa", "Batten")}
_WALL_GAP = 0.05            # m: a wall this far from a water's side (beyond its half thickness) carries its plate
_QUAD_FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))


def settings_text(settings):
    return json.dumps({"caibros": settings.rafter_spacing, "terca": settings.purlin_span, "galga": settings.gauge,
                       "seccoes": {k: list(v) for k, v in settings.sections}})


def settings_from(text):
    try:
        data = json.loads(text or "{}")
    except ValueError:
        data = {}
    base = core_carpentry.Settings()
    sections = dict(base.sections)
    sections.update({k: tuple(v) for k, v in (data.get("seccoes") or {}).items() if k in sections})
    return core_carpentry.Settings(rafter_spacing=float(data.get("caibros", base.rafter_spacing)),
                                   purlin_span=float(data.get("terca", base.purlin_span)),
                                   gauge=float(data.get("galga", base.gauge)),
                                   sections=tuple(sorted(sections.items())))


def _triangles(corners):
    """The 12 triangles of a piece's 8 corners (1-based), each turned out of it."""
    pts = np.asarray(corners, dtype=float)
    centre = pts.mean(axis=0)
    out = []
    for quad in _QUAD_FACES:
        for tri in ((quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])):
            a, b, c = pts[list(tri)]
            if float(np.dot(np.cross(b - a, c - a), (a + b + c) / 3 - centre)) < 0:
                tri = (tri[0], tri[2], tri[1])
            out.append(tuple(i + 1 for i in tri))
    return out


class CarpentryMixin:
    # ------------------------------------------------------------ the roof's waters

    def roof_waters(self, guid):
        """A pitched roof's waters and edges in its own frame, and the walls' outer line under each water: (
        [((a, b, c), Polygon)], [(kind, a, b)], [((x, y), (x, y), slope, block index or None, side index)]).
        EditRefused for a flat or extruded one (a barrel, a butterfly, a drawn section)."""
        from shapely.geometry import Polygon
        p = self.roof_params(guid)
        if p["form"] == "blocks":
            blocks = p["blocks"]
            found = core_blocks.regions(blocks)
            waters = [(c, g) for c, geometry in found for g in core_blocks.polygons(geometry)
                      if abs(c[0]) + abs(c[1]) > 1e-12]
            sides = []
            for i, b in enumerate(blocks):
                corners = core_blocks.rect(b)          # (counter-clockwise from its −x −y corner: S, E, N, W)
                for side, (s, e) in zip((2, 1, 0, 3), ((0, 1), (1, 2), (2, 3), (3, 0))):
                    if b.water[side]:
                        sides.append((corners[s], corners[e], b.slope[side], i, side))
            if not waters:
                raise EditRefused("roof_carpentry_form")
            return waters, core_blocks.edges(blocks, found), sides
        if p["form"] in core_roofs.EXTRUDED or p["form"] == "flat" or not any(p["sloping"]):
            raise EditRefused("roof_carpentry_form")
        _outline, _flags, faces = self._roof_faces(p["local"], p["sloping"], p["overhang"])
        if faces is None:
            raise EditRefused("roof_not_convex")
        tan = math.tan(math.radians(p["slope"]))
        drop = tan * p["overhang"]
        waters = []
        for plane, polygon in faces:
            if plane is not None:
                start, _e, n = plane
                waters.append(((tan * n[0], tan * n[1], -drop - tan * (start[0] * n[0] + start[1] * n[1])),
                               Polygon(polygon)))
        local = p["local"]
        sides = [(local[k], local[(k + 1) % len(local)], p["slope"], None, k)
                 for k in range(len(local)) if p["sloping"][k]]
        return waters, core_blocks.edges([], waters), sides

    # ------------------------------------------------------------ the walls under them

    def _plates_and_rise(self, roof, sides, settings):
        """The wall plates in the roof's frame — [((x, y), (x, y), z)], each on a straight wall's top where it runs
        along a water's side — and how much each side's cover goes up for the carpentry to sit on them: {(block,
        side): m} (only the sides with walls under them)."""
        inv = np.linalg.inv(self._placement_si(roof))
        storey = self.storey_of(roof.GlobalId)
        walls = []
        for g in self.storey_elements(storey) if storey else ():
            if self.kind_of(g) != "wall":
                continue
            p, q, thickness = self.wall_axis(g)
            height = self.wall_params(g)[1]
            a = (inv @ np.array((p[0], p[1], p[2], 1.0)))[:3]
            b = (inv @ np.array((q[0], q[1], q[2], 1.0)))[:3]
            walls.append((a, b, float(thickness), float(a[2] + height)))
        plate_w, plate_h = settings.section("frechal")
        cover = self.roof_params(roof.GlobalId)["thickness"]
        plates, rise = [], {}
        for s0, s1, slope, block, side in sides:
            s0, s1 = np.asarray(s0, dtype=float), np.asarray(s1, dtype=float)
            length = float(np.linalg.norm(s1 - s0))
            if length < 1e-6:
                continue
            u = (s1 - s0) / length
            inward = np.array((-u[1], u[0]))               # (the outline counter-clockwise: in, to its left)
            found = []
            for a, b, thickness, top in walls:
                d = b[:2] - a[:2]
                if np.linalg.norm(d) < 1e-6 or abs(float(np.dot(d / np.linalg.norm(d), inward))) > 0.02:
                    continue
                off = float(np.dot(a[:2] - s0, inward))    # (its axis this far in from the outer line)
                if abs(off - thickness / 2) > thickness / 2 + _WALL_GAP:
                    continue
                ta, tb = sorted((float(np.dot(a[:2] - s0, u)), float(np.dot(b[:2] - s0, u))))
                lo, hi = max(ta, 0.0), min(tb, length)
                if hi - lo >= settings.min_length:
                    found.append((lo, hi, off, thickness, top))
            if not found:
                continue
            wall = max(f[3] for f in found)
            tan, sec = math.tan(math.radians(slope)), 1.0 / math.cos(math.radians(slope))
            # (the rafters on the plates' inner top edge: the plate, the rafter and the batten square to the slope,
            # less the plate's inner edge being nearer the wall's middle than the wall's inner face — over the seat
            # the cover had on the walls themselves, 0.275; 0.278: less the gap a thin cover had over them)
            rise[(block, side)] = plate_h + settings.depth * sec + (wall / 2 - plate_w / 2) * tan - \
                core_roofs.seat_gap(slope, cover, wall)
            for lo, hi, off, _thickness, top in found:
                a, b = s0 + u * lo + inward * off, s0 + u * hi + inward * off
                plates.append(((float(a[0]), float(a[1])), (float(b[0]), float(b[1])), top))
        return plates, rise

    # ------------------------------------------------------------ made, made again, taken away

    def carpentry_of(self, roof_guid):
        """The roof's carpentry assembly (IfcElementAssembly), or None."""
        found = self._params(self.by_guid(roof_guid)).get("Madeiramento") if self.by_guid(roof_guid) else None
        return self.by_guid(found) if found else None

    def _raise_cover(self, roof, rise, sign):
        """The roof's cover up (sign 1) or down (−1) by its sides' rise."""
        p = self.roof_params(roof.GlobalId)
        if p["form"] == "blocks":
            blocks = list(p["blocks"])
            for (i, side), r in rise.items():
                eaves = list(blocks[i].eave)
                eaves[side] += sign * r
                blocks[i] = core_blocks.replace(blocks[i], eave=tuple(eaves))
            self._set_params(roof, {"Blocos": core_blocks.to_text(blocks)})
        elif rise:
            m = self._placement_si(roof)
            m[2, 3] += sign * max(rise.values())
            self._place(roof, m)
        self._set_roof_body(roof)

    def set_roof_carpentry(self, guid, settings=None, lang="pt"):
        """(0.276) A roof's carpentry made (or made again with these settings; None: those it has, else the
        add-on's): its cover raised onto it, its pieces under it. Returns the assembly."""
        roof, _ = self._require(guid, "roof")
        old = self.carpentry_of(guid)
        if settings is None:
            settings = settings_from(self._params(old).get("Madeiramento")) if old is not None else \
                core_carpentry.Settings()
        self.remove_roof_carpentry(guid)
        _waters, _edges, sides = self.roof_waters(guid)
        _plates, rise = self._plates_and_rise(roof, sides, settings)
        self._raise_cover(roof, rise, 1)
        waters, edges, sides = self.roof_waters(guid)
        plates, _rise = self._plates_and_rise(roof, sides, settings)    # (in its frame as it is now: raised)
        p = self.roof_params(guid)
        found = core_carpentry.pieces(waters, edges, p["thickness"], plates, settings)
        assembly = self._make_carpentry(roof, found, settings, lang)
        self._set_params(roof, {"Madeiramento": assembly.GlobalId, "MadeiramentoSubida": json.dumps(
            {"{},{}".format(-1 if i is None else i, k): r for (i, k), r in rise.items()})})
        return assembly

    def remove_roof_carpentry(self, guid):
        """(0.276) A roof's carpentry taken away and its cover brought down onto the walls again."""
        roof = self.by_guid(guid)
        assembly = self.carpentry_of(guid)
        if assembly is None:
            return False
        for rel in list(assembly.IsDecomposedBy or ()):
            for part in list(rel.RelatedObjects):
                api.root.remove_product(self.file, product=part)
        api.root.remove_product(self.file, product=assembly)
        params = self._params(roof)
        try:
            stored = json.loads(params.get("MadeiramentoSubida") or "{}")
        except ValueError:
            stored = {}
        rise = {}
        for key, r in stored.items():
            i, k = (int(v) for v in key.split(","))
            rise[(None if i < 0 else i, k)] = float(r)
        self._set_params(roof, {"Madeiramento": None, "MadeiramentoSubida": None})
        self._raise_cover(roof, rise, -1)
        return True

    def carpentry_summary(self, guid):
        """A roof's carpentry by kind of piece: {role: (count, length m, volume m³)} — None when it has none."""
        assembly = self.carpentry_of(guid)
        if assembly is None:
            return None
        by_name = {name: role for role, names in NAMES.items() for name in names}
        s = self.unit_scale
        out = {}
        for rel in assembly.IsDecomposedBy or ():
            for part in rel.RelatedObjects:
                role = by_name.get((part.Name or "").rsplit(" ", 1)[0])
                if role is None:
                    continue
                q = ifcopenshell.util.element.get_psets(part).get("Qto_MemberBaseQuantities", {})
                n, length, volume = out.get(role, (0, 0.0, 0.0))
                out[role] = (n + 1, length + float(q.get("Length") or 0.0) * s, volume + float(q.get("NetVolume") or 0.0))
        return {r: out[r] for r in core_carpentry.ROLES if r in out}

    def drop_carpentry(self, guid):
        """A roof being removed: its carpentry with it (nothing to bring down)."""
        assembly = self.carpentry_of(guid)
        if assembly is None:
            return
        for rel in list(assembly.IsDecomposedBy or ()):
            for part in list(rel.RelatedObjects):
                api.root.remove_product(self.file, product=part)
        api.root.remove_product(self.file, product=assembly)

    def follow_carpentry(self, changed):
        """The carpentry of the roofs changed (their slope, overhang, blocks…) made again: the cover brought down,
        then up onto the new pieces. Returns what it made (what it took away goes with the step's changes)."""
        out = []
        made = set(getattr(self, "made", None) or ())
        for g in list(dict.fromkeys(changed)):
            e = self.by_guid(g)
            if e is None or not e.is_a("IfcRoof") or self.carpentry_of(g) is None:
                continue
            old = self.carpentry_of(g)
            if old.GlobalId in made:                       # (made in this very step: as asked)
                continue
            try:
                assembly = self.set_roof_carpentry(g)
            except EditRefused:                            # (made flat: no carpentry for it)
                self.remove_roof_carpentry(g)
                continue
            out += [assembly.GlobalId] + [p.GlobalId for rel in assembly.IsDecomposedBy or ()
                                          for p in rel.RelatedObjects]
        return out

    def _make_carpentry(self, roof, found, settings, lang):
        f, u = self.file, 1.0 / self.unit_scale
        m = self._placement_si(roof)
        storey = self.storey_of(roof.GlobalId)
        assembly = api.root.create_entity(f, ifc_class="IfcElementAssembly", predefined_type="USERDEFINED",
                                          name="{} — {}".format("Madeiramento" if lang == "pt" else "Carpentry",
                                                                roof.Name or ""))
        assembly.ObjectType = "Madeiramento"
        self._place(assembly, m)
        if storey:
            api.spatial.assign_container(f, products=[assembly], relating_structure=self.storey(storey))
        self._mark(assembly, "carpentry")
        self._set_params(assembly, {"Cobertura": roof.GlobalId, "Madeiramento": settings_text(settings)})
        members, counts = [], {}
        for piece in found:
            predefined, object_type = KIND[piece.role]
            counts[piece.role] = counts.get(piece.role, 0) + 1
            member = api.root.create_entity(f, ifc_class="IfcMember", predefined_type=predefined,
                                            name="{} {}".format(NAMES[piece.role][0 if lang == "pt" else 1],
                                                                counts[piece.role]))
            if object_type:
                member.ObjectType = object_type
            self._place(member, m)
            coords = f.createIfcCartesianPointList3D([tuple(float(c * u) for c in corner)
                                                      for corner in piece.corners])
            body = f.createIfcTriangulatedFaceSet(coords, None, True, _triangles(piece.corners), None)
            api.geometry.assign_representation(f, product=member, representation=f.createIfcShapeRepresentation(
                self.body, self.body.ContextIdentifier, "Tessellation", [body]))
            self._set_qto(member, "Qto_MemberBaseQuantities", {"Length": piece.length * u,
                                                               "NetVolume": piece.volume})
            members.append(member)
        if members:
            api.aggregate.assign_object(f, products=members, relating_object=assembly)
            api.material.assign_material(f, products=members, type="IfcMaterial",
                                         material=self._material("madeira", lang))
        return assembly
