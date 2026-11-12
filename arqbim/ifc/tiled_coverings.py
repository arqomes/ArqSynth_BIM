"""(0.563, PLANO.md «Gerador de revestimentos 3D em IFC», step 2) A Revestimento, mixed into IfcModel: an IfcCovering
(CLADDING on an upright face, FLOORING on a floor, CEILING under one) laid in pieces on a flat face — each piece its
own solid with the joints between, on its bed of glue or mortar, the grout set back in the joints. Its type an
IfcCoveringType of the finish's name; its material a layer set (bed, piece); its body two tessellated items, the
pieces in their material's colour and the bed and grout in theirs; Qto_CoveringBaseQuantities (Width, GrossArea,
NetArea) and ArqSynth_Paginacao (whole and cut pieces, narrow cuts, the narrowest).

ArqSynth_Parametros: Elemento "tiled_covering", Contorno and Furos (the face in its own frame — its placement: x, y
in the face, z out of it), Paginacao (core/tiling's layout, JSON), Acabamento (core/covering_finishes key), Material,
Espessura (the piece's), Cama, MaterialCama, Junta (the grout's material, «» none), Recuo, Origem (the element or
drawing it was laid on)."""

import json

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.owner
import ifcopenshell.guid
import ifcopenshell.util.element
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from ..core import covering_finishes as cf
from ..core import tiling as tl
from .edit import EditRefused

api = ifcopenshell.api
KIND = "tiled_covering"
MAX_PIECES = 20000          # the most pieces one Revestimento carries (a whole façade in 10 × 10 cm mosaic is not one)


def _pts(text):
    return [tuple(float(v) for v in q.split(",")) for q in (text or "").split(";") if q]


def _text(pts):
    return ";".join("{:.6f},{:.6f}".format(float(x), float(y)) for x, y in pts)


def predefined_for(normal):
    """CLADDING on an upright face, FLOORING on one facing up, CEILING on one facing down."""
    nz = float(normal[2])
    return "FLOORING" if nz > 0.7 else "CEILING" if nz < -0.7 else "CLADDING"


def face_frame_and_shape(outline, holes=()):
    """(frame (4, 4), face shapely in it) of a 3D face (its outline and holes): on a wall x level along it and y
    up, on a floor x east and y north."""
    fr = tl.face_frame(outline)
    o, x, y, n = fr
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, y, n, o
    face = Polygon(tl.to_plane(outline, fr), [tl.to_plane(h, fr) for h in holes if len(h) >= 3]).buffer(0)
    return m, face


CUSTOM_KEY = "RevestimentosProprios"


class TiledCoveringMixin:
    def load_custom_finishes(self):
        """(0.569) The project's own finishes put in the catalogue (once per change of them)."""
        project = self.file.by_type("IfcProject")
        raw = self._params(project[0]).get(CUSTOM_KEY) if project else None
        if raw and raw != getattr(self, "_custom_seen", None):
            self._custom_seen = raw
            try:
                cf.register(json.loads(raw))
            except ValueError:
                pass

    def save_custom_finish(self, guid, name):
        """(0.569) A Revestimento's finish as it is now — piece, bond, joints, bed, grout — kept as a finish of one's
        own under `name` (in the project, its key returned)."""
        import re
        p = self.tiled_params(guid)
        d = p["layout"]
        key = cf.CUSTOM_PREFIX + (re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "revestimento")
        entry = {"key": key, "name_pt": name, "name_en": name, "material": p["material"], "w": d["w"], "h": d["h"],
                 "thickness": p["thickness"], "pattern": d["pattern"], "joint": d["joint"], "bond": d["bond"],
                 "bed": p["bed"], "bed_material": p["bed_material"], "grout": p["grout"] or "",
                 "recess": p["recess"], "lengths": list(d.get("lengths") or [])}
        project = self.file.by_type("IfcProject")[0]
        try:
            old = json.loads(self._params(project).get(CUSTOM_KEY) or "[]")
        except ValueError:
            old = []
        old = [q for q in old if q.get("key") != key] + [entry]
        self._set_params(project, {CUSTOM_KEY: json.dumps(old, ensure_ascii=False)})
        cf.register([entry])
        e = self.by_guid(guid)
        self._set_params(e, {"Acabamento": key})
        self._tiled_body(e)                               # (its type now the finish's own name)
        return key, entry

    def tiled_on(self, host, point, normal, reach=0.01):
        """(outline, holes, normal) of the flat face of element `host` round `point` (world), facing `normal` — or
        None. `reach`: how far the face may be from the point (following: anywhere in its plane)."""
        from ..core import face_region
        e = self.by_guid(host)
        joined = [host]                                   # (0.568) a wall's: the walls joined to it too — at a
        for rel in list(getattr(e, "ConnectedTo", None) or ()) + list(getattr(e, "ConnectedFrom", None) or ()):
            for other in (getattr(rel, "RelatingElement", None), getattr(rel, "RelatedElement", None)):
                if other is not None and other.GlobalId not in joined and other.is_a("IfcWall"):
                    joined.append(other.GlobalId)        # corner the square of it in this face's plane is its own
        shapes = self.triangulate(joined)
        found = shapes.get(host)
        if found is None:
            return None
        verts, tris = [np.asarray(found[0], float)], [np.asarray(found[1])]
        lo, hi = verts[0].min(axis=0) - 0.6, verts[0].max(axis=0) + 0.6
        k = len(verts[0])
        for g in joined[1:]:                              # (only its pieces by the host's end — the corner — not a
            if g not in shapes:                           # wall in line with it all along)
                continue
            v, t = np.asarray(shapes[g][0], float), np.asarray(shapes[g][1])
            c = v[t].mean(axis=1)
            near = ((c[:, :2] >= lo[:2]) & (c[:, :2] <= hi[:2])).all(axis=1)
            if near.any():
                verts.append(v)
                tris.append(t[near] + k)
                k += len(v)
        return face_region.face_at(np.vstack(verts), np.vstack(tris), point, normal, reach)

    def remember_face(self, guid, host, point, normal, stretch=None):
        """(0.564) The face a Revestimento was laid on, kept in its host's own coordinates (so that it follows it):
        Origem, FacePonto, FaceNormal; (0.567) `stretch` (a, b, height): only that stretch of it (a room's) —
        Recorte."""
        e, _ = self._require(guid, KIND)
        h = self.by_guid(host)
        m = self._placement_si(h)
        inv = np.linalg.inv(m)
        local = inv @ np.append(np.asarray(point, float), 1.0)
        n = inv[:3, :3] @ np.asarray(normal, float)
        changes = {"Origem": host, "FacePonto": "{:.6f},{:.6f},{:.6f}".format(*local[:3]),
                   "FaceNormal": "{:.6f},{:.6f},{:.6f}".format(*n)}
        if stretch is not None:
            a, b, height = stretch
            la, lb = (inv @ np.append(np.asarray(q, float), 1.0) for q in (a, b))
            changes["Recorte"] = "{:.6f},{:.6f},{:.6f};{:.6f},{:.6f},{:.6f};{:.6f}".format(*la[:3], *lb[:3], height)
        self._set_params(e, changes)
        if h.is_a("IfcElement") and not h.is_a("IfcCovering"):
            self._cover(e, h)                             # (IfcRelCoversBldgElements: the host knows it)

    def cover_space(self, guid, space):
        """(0.567) A Revestimento tied to the room it finishes (IfcRelCoversSpaces: a floor, a ceiling)."""
        e, _ = self._require(guid, KIND)
        s = self.by_guid(space)
        if s is None:
            return
        rel = next((r for r in self.file.by_type("IfcRelCoversSpaces") if r.RelatingSpace == s), None)
        if rel is None:
            self.file.create_entity("IfcRelCoversSpaces", GlobalId=ifcopenshell.guid.new(),
                                    OwnerHistory=api.owner.create_owner_history(self.file), RelatingSpace=s,
                                    RelatedCoverings=[e])
        elif e not in rel.RelatedCoverings:
            rel.RelatedCoverings = list(rel.RelatedCoverings) + [e]
        self._set_params(e, {"Ambiente": space})

    def follow_tiled(self, changed):
        """(0.564) After elements changed: the Revestimentos laid on their faces laid again on those faces as they
        are now (a wall longer, a window put in, a slab moved); a host gone takes them. Returns those changed."""
        changed = set(changed)
        if not changed:
            return []
        out, found_on = [], []
        for g in changed:                                 # (through the hosts' own ties: no look through the model)
            h = self.by_guid(g)
            for rel in (getattr(h, "HasCoverings", None) or ()) if h is not None else ():
                found_on += [c for c in rel.RelatedCoverings if c not in found_on]
        for e in found_on:
            p = self._params(e)
            if p.get("Elemento") != KIND or p.get("Origem") not in changed or not p.get("FacePonto"):
                continue
            host = self.by_guid(p["Origem"])
            m = self._placement_si(host)
            point = (m @ np.append([float(v) for v in p["FacePonto"].split(",")], 1.0))[:3]
            normal = m[:3, :3] @ np.array([float(v) for v in p["FaceNormal"].split(",")])
            found = self.tiled_on(host.GlobalId, point, normal, reach=1e9)
            if found is None:
                continue
            outline, holes = found[0], found[1]
            if p.get("Recorte"):                          # (0.567) a room's stretch of the face only
                from ..core import face_region
                qa, qb, height = p["Recorte"].split(";")
                a, b = ((m @ np.append([float(v) for v in q.split(",")], 1.0))[:3] for q in (qa, qb))
                parts = face_region.clip_to_stretch(outline, holes, a, b, float(height))
                if not parts:
                    continue
                outline, holes = max(parts, key=lambda q: Polygon(tl.to_plane(q[0], tl.face_frame(q[0]))).area)
            frame, face = face_frame_and_shape(outline, holes)
            try:
                self.set_tiled_covering(e.GlobalId, frame=frame, face=face)
            except EditRefused:
                continue
            out.append(e.GlobalId)
        return out

    def tiled_params(self, guid):
        """{finish, layout, material, thickness, bed, bed_material, grout, recess, source} of a Revestimento."""
        e, _ = self._require(guid, KIND)
        self.load_custom_finishes()
        p = self._params(e)
        try:
            layout = json.loads(p.get("Paginacao") or "{}")
        except ValueError:
            layout = {}
        fin = cf.finish(p.get("Acabamento"))
        return {"finish": p.get("Acabamento") or fin.key, "layout": tl.layout(layout),
                "material": p.get("Material") or fin.material,
                "thickness": float(p.get("Espessura") if p.get("Espessura") is not None else fin.thickness),
                "bed": float(p.get("Cama") if p.get("Cama") is not None else fin.bed),
                "bed_material": p.get("MaterialCama") or fin.bed_material,
                "grout": p.get("Junta") if p.get("Junta") is not None else fin.grout,
                "recess": float(p.get("Recuo") if p.get("Recuo") is not None else fin.recess),
                "source": p.get("Origem") or ""}

    def tiled_face(self, guid):
        """(frame (4, 4), face shapely in it) of a Revestimento."""
        e, _ = self._require(guid, KIND)
        p = self._params(e)
        face = Polygon(_pts(p.get("Contorno")), [_pts(h) for h in (p.get("Furos") or "").split("|") if h]).buffer(0)
        e0, e1 = self.tiled_extend(guid)
        if (e0 or e1) and not face.is_empty:              # (0.568) prolonged at its start / end (over a corner)
            from shapely.geometry import box as _box
            c = np.asarray(face.exterior.coords)
            u0, u1 = c[:, 0].min(), c[:, 0].max()
            for e_, u, side in ((e0, u0, -1), (e1, u1, 1)):
                if e_ > 1e-6:
                    at = c[np.abs(c[:, 0] - u) < 1e-3]
                    if len(at):
                        lo, hi = at[:, 1].min(), at[:, 1].max()
                        face = face.union(_box(min(u, u + side * e_), lo, max(u, u + side * e_), hi)).buffer(0)
        return self._placement_si(e), face

    def tiled_extend(self, guid):
        """(0.568) How far a Revestimento goes on past its face at its start and its end (m)."""
        p = self._params(self.by_guid(guid))
        try:
            a, b = (float(v) for v in (p.get("Prolongar") or "0;0").split(";"))
        except ValueError:
            a = b = 0.0
        auto = (p.get("ProlongarAuto") or ";").split(";")      # (the corner's neighbour: as thick as it is now)
        out = [a, b]
        for k, g in enumerate(auto[:2]):
            other = self.by_guid(g) if g else None
            if other is not None and self._params(other).get("Elemento") == KIND:
                q = self._params(other)
                fin = cf.finish(q.get("Acabamento"))
                out[k] = float(q.get("Cama") if q.get("Cama") is not None else fin.bed) + \
                    float(q.get("Espessura") if q.get("Espessura") is not None else fin.thickness)
        return tuple(out)

    def set_tiled_extend(self, guid, start=None, end=None, lang="pt"):
        """(0.568) Its start / end prolonged (0–1 m); its body made again."""
        e, _ = self._require(guid, KIND)
        a, b = self.tiled_extend(guid)
        a = a if start is None else float(start)
        b = b if end is None else float(end)
        if not (0.0 <= a <= 1.0 and 0.0 <= b <= 1.0):
            raise EditRefused("tiling_thickness")
        self._set_params(e, {"Prolongar": "{:.4f};{:.4f}".format(a, b)})
        self._tiled_body(e, lang)

    def close_corners(self, guids, lang="pt"):
        """(0.568) Where two of these Revestimentos meet at an outside corner (a building's edge), the first goes on
        past the corner as far as the other is thick — over its end, as a fitter laps them. Those changed."""
        info = []
        for g in guids:
            e = self.by_guid(g)
            if e is None:
                continue
            m, face = self.tiled_face(g)
            if face.is_empty:
                continue
            p = self.tiled_params(g)
            x0, y0, x1, y1 = face.bounds
            info.append((g, m, (x0, x1, (y0 + y1) / 2.0), p["bed"] + p["thickness"]))
        out = []
        for i, (g, m, (u0, u1, vm), _t) in enumerate(info):
            ext, who = [0.0, 0.0], ["", ""]
            for k, (u, side) in enumerate(((u0, -1.0), (u1, 1.0))):
                end = m[:3, 3] + m[:3, 0] * u + m[:3, 1] * vm
                way = m[:3, 0] * side
                for j, (g2, m2, _b, t2) in enumerate(info):
                    if j <= i:
                        continue
                    n2 = m2[:3, 2]
                    if abs(float(n2 @ (end - m2[:3, 3]))) < 0.03 and float(way @ n2) > 0.99 and t2 > ext[k]:
                        ext[k], who[k] = t2, g2
            if ext[0] or ext[1]:
                self._set_params(self.by_guid(g), {"ProlongarAuto": ";".join(who)})
                self.set_tiled_extend(g, ext[0] or None, ext[1] or None, lang)
                out.append(g)
        return out

    def _relap(self, guid, lang="pt"):
        """(0.569) The Revestimentos lapped over this one's end (at a corner) made again — it got thicker or
        thinner."""
        for e in self.file.by_type("IfcCovering"):
            if guid in (self._params(e).get("ProlongarAuto") or "").split(";") and e.GlobalId != guid:
                self._tiled_body(e, lang)

    def tiled_layout(self, guid):
        """core/tiling's Result of a Revestimento's pieces as they are."""
        return self.tiled_pieces(guid)[0]

    def tiled_extras(self, guid):
        """(0.566) {zones, mix, picks} of a Revestimento: its bands and border, its mix of materials, the pieces
        given their own one by one."""
        e, _ = self._require(guid, KIND)
        p = self._params(e)

        def read(key, empty):
            try:
                return json.loads(p.get(key) or "") if p.get(key) else empty
            except ValueError:
                return empty

        return {"zones": read("Zonas", []), "mix": read("Mistura", {}), "picks": read("Escolhas", [])}

    def tiled_pieces(self, guid):
        """(Result, [material per piece]) of a Revestimento — its zones, mix and picked pieces with it (0.566)."""
        _m, face = self.tiled_face(guid)
        x = self.tiled_extras(guid)
        return tl.lay_all(orient(face, 1.0), self.tiled_params(guid)["layout"], x["zones"], x["mix"],
                          [tuple(q) for q in x["picks"]])

    def set_tiled_extras(self, guid, zones=None, mix=None, picks=None, lang="pt"):
        """(0.566) A Revestimento's bands and border, its mix, its pieces picked one by one — each given (a list or
        {} empty: none) replaces what it had; its body made again."""
        from . import catalog
        e, _ = self._require(guid, KIND)
        changes = {}
        if zones is not None:
            try:
                zones = tl.check_zones(zones)
            except tl.LayoutError as exc:
                raise EditRefused(exc.code) from None
            for z in zones:
                if z.get("material") and z["material"] not in catalog.MATERIALS:
                    raise EditRefused("tiling_material")
            changes["Zonas"] = json.dumps(zones) if zones else ""
        if mix is not None:
            mats = [m for m in (mix or {}).get("materials", []) if m]
            if any(m not in catalog.MATERIALS for m in mats):
                raise EditRefused("tiling_material")
            changes["Mistura"] = json.dumps({"materials": mats, "seed": int((mix or {}).get("seed", 1))}) \
                if mats else ""
        if picks is not None:
            if any(len(q) != 3 or q[2] not in catalog.MATERIALS for q in picks):
                raise EditRefused("tiling_material")
            changes["Escolhas"] = json.dumps([[float(q[0]), float(q[1]), q[2]] for q in picks]) if picks else ""
        self._set_params(e, changes)
        self._tiled_body(e, lang)

    def add_tiled_covering(self, frame, face, finish, name, layout=None, source="", lang="pt", storey=None,
                           **changes):
        """A Revestimento on a flat face: `frame` (4, 4) its plane (x, y in it, z out of it, its origin on it),
        `face` (shapely, the frame's x, y) the part covered; `finish` a core/covering_finishes key — its layout
        (`layout` over it) and anything of it changed by `changes` (as set_tiled_covering's). Returns it."""
        self.load_custom_finishes()
        if finish not in cf.FINISHES:
            raise EditRefused("tiling_finish")
        fin = cf.FINISHES[finish]
        frame = np.array(frame, dtype=float)
        f = self.file
        e = api.root.create_entity(f, ifc_class="IfcCovering", name=name,
                                   predefined_type=predefined_for(frame[:3, 2]))
        self._place(e, frame)
        container = self.storey(storey) if storey is not None else self.storey_at(float(frame[2, 3]) + 0.01)
        api.spatial.assign_container(f, products=[e], relating_structure=container)
        self._mark(e, KIND)
        d = fin.layout()
        d.update(layout or {})
        self._set_params(e, {"Acabamento": finish, "Origem": str(source or "")})
        self.set_tiled_covering(e.GlobalId, layout=d, face=face, lang=lang, **changes)
        return e

    def set_tiled_covering(self, guid, layout=None, face=None, frame=None, finish=None, material=None,
                           thickness=None, bed=None, bed_material=None, grout=None, recess=None, lang="pt"):
        """A Revestimento changed: its layout (all of it, or the keys given), its face or plane, another finish
        (its piece, layout, bed and grout — the layout's origin kept), or any one of these; its body made again."""
        e, _ = self._require(guid, KIND)
        p = self._params(e)
        old = json.loads(p.get("Paginacao") or "{}") if p.get("Paginacao") else {}
        changes = {}
        if finish is not None:
            if finish not in cf.FINISHES:
                raise EditRefused("tiling_finish")
            fin = cf.FINISHES[finish]
            keep = {k: old[k] for k in ("origin", "point", "align", "dx", "dy", "angle", "min_cut") if k in old}
            old = dict(fin.layout(), **keep)
            changes.update({"Acabamento": finish, "Material": fin.material, "Espessura": fin.thickness,
                            "Cama": fin.bed, "MaterialCama": fin.bed_material, "Junta": fin.grout,
                            "Recuo": fin.recess})
        if layout is not None:
            old.update(layout)
        try:
            d = tl.layout(old)
        except tl.LayoutError as exc:
            raise EditRefused(exc.code) from None
        changes["Paginacao"] = json.dumps({k: (list(v) if isinstance(v, tuple) else v) for k, v in d.items()},
                                          sort_keys=True)
        for key, value in (("Material", material), ("Espessura", thickness), ("Cama", bed),
                           ("MaterialCama", bed_material), ("Junta", grout), ("Recuo", recess)):
            if value is not None:
                changes[key] = value
        from . import catalog
        for key in ("Material", "MaterialCama"):
            if changes.get(key) is not None and changes[key] not in catalog.MATERIALS:
                raise EditRefused("tiling_material")
        if changes.get("Junta") and changes["Junta"] not in catalog.MATERIALS:
            raise EditRefused("tiling_material")
        for key in ("Espessura", "Cama", "Recuo"):
            if key in changes and not 0.0 <= float(changes[key]) <= 0.5:
                raise EditRefused("tiling_thickness")
        if frame is not None:
            self._place(e, np.array(frame, dtype=float))
        if face is not None:
            rings = [q for q in getattr(face, "geoms", [face]) if q.geom_type == "Polygon" and q.area > 1e-6]
            if not rings:
                raise EditRefused("tiling_empty")
            q = orient(max(rings, key=lambda r: r.area), 1.0)
            changes.update({"Contorno": _text(list(q.exterior.coords)[:-1]),
                            "Furos": "|".join(_text(list(h.coords)[:-1]) for h in q.interiors)})
        self._set_params(e, changes)
        self._tiled_body(e, lang)
        if any(k in changes for k in ("Espessura", "Cama")):  # (0.569) those lapped over its end follow it
            self._relap(guid, lang)

    def _tiled_body(self, e, lang="pt"):
        f, u = self.file, 1.0 / self.unit_scale
        p = self.tiled_params(e.GlobalId)
        _m, face = self.tiled_face(e.GlobalId)
        if face.is_empty or face.area < 1e-6:
            raise EditRefused("tiling_empty")
        try:
            result, mats = self.tiled_pieces(e.GlobalId)
        except tl.LayoutError as exc:
            raise EditRefused(exc.code) from None
        if len(result.pieces) > MAX_PIECES:
            raise EditRefused("tiling_too_many")
        bed, t, recess = p["bed"], max(p["thickness"], 0.001), min(p["recess"], p["thickness"])
        items, styled = [], []

        def item(verts, tris, key):
            if not len(tris):
                return
            it = f.createIfcTriangulatedFaceSet(
                f.createIfcCartesianPointList3D([tuple(float(c) * u for c in row) for row in verts]), None, True,
                [tuple(int(i) + 1 for i in row) for row in tris], None)
            items.append(it)
            styled.append((it, key))

        groups = {}                                      # (0.566: each material its own item — bands, mix, picks)
        for pc, m in zip(result.pieces, mats):
            groups.setdefault(m or p["material"], []).append((pc.points, pc.holes))
        for key, polys in groups.items():
            verts, tris = tl.prisms(polys, bed, bed + t)
            item(verts, tris, key)
        q = orient(face, 1.0)
        outline = (list(q.exterior.coords)[:-1], [list(h.coords)[:-1] for h in q.interiors])
        if bed > 1e-6:                                   # (the bed under the pieces)
            verts, tris = tl.prisms([outline], 0.0, bed)
            item(verts, tris, p["bed_material"])
        if p["grout"] and recess > 1e-6 and t - recess > 1e-6:   # (the grout in the joints only, back from the
            verts, tris = tl.prisms(tl.joints(result, face, p["layout"]), bed, bed + t - recess)  # face — never
            item(verts, tris, p["grout"])                        # behind a piece, where it would show through)
        if not items:
            raise EditRefused("tiling_empty")
        self._clear_representations(e)
        api.geometry.assign_representation(f, product=e, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "Tessellation", items))
        materials = {}
        for it, key in styled:
            if key not in materials:
                materials[key] = self._material(key, lang)
            f.createIfcStyledItem(it, [self._material_style(materials[key])], None)
        self._tiled_material(e, p, lang)
        total = bed + t
        self._set_qto(e, "Qto_CoveringBaseQuantities", {"Width": total * u, "GrossArea": float(face.area),
                                                        "NetArea": float(sum(pc.area for pc in result.pieces))})
        s = result.summary(p["layout"]["min_cut"])
        own = ifcopenshell.util.element.get_psets(e).get("ArqSynth_Paginacao")
        pset = f.by_id(own["id"]) if own else api.pset.add_pset(f, product=e, name="ArqSynth_Paginacao")
        api.pset.edit_pset(f, pset=pset, properties={
            "Pecas": int(s["pieces"]), "PecasInteiras": int(s["whole"]), "PecasCortadas": int(s["cut"]),
            "CortesEstreitos": int(s["narrow"]),
            "CorteMaisEstreito": float(s["narrowest"]) if s["narrowest"] != float("inf") else 0.0,
            "Aparelho": p["layout"]["pattern"]})

    def _tiled_material(self, e, p, lang):
        """Its material: a layer set — the bed (if any), the piece — shared by those alike; its type: an
        IfcCoveringType of the finish's name."""
        f = self.file
        fin = cf.finish(p["finish"])
        layers = ([(p["bed_material"], p["bed"])] if p["bed"] > 1e-6 else []) + [(p["material"], p["thickness"])]
        mats = [(self._material(k, lang), t) for k, t in layers]
        name = " + ".join("{} {:.0f} mm".format(m.Name, t * 1000) for m, t in mats)
        wanted = next((s for s in f.by_type("IfcMaterialLayerSet") if s.LayerSetName == name), None)
        if wanted is None:
            wanted = api.material.add_material_set(f, name=name, set_type="IfcMaterialLayerSet")
            for m, t in mats:
                layer = api.material.add_layer(f, layer_set=wanted, material=m)
                layer.LayerThickness = float(t) / self.unit_scale
        if ifcopenshell.util.element.get_material(e, should_skip_usage=True) != wanted:
            api.material.unassign_material(f, products=[e])
            api.material.assign_material(f, products=[e], type="IfcMaterialLayerSet", material=wanted)
        tname = fin.name_pt if lang == "pt" else fin.name_en
        kind = predefined_for(self._placement_si(e)[:3, 2])   # (the occurrence's own goes when typed: the type's)
        ctype = next((ty for ty in f.by_type("IfcCoveringType") if ty.Name == tname
                      and ty.PredefinedType == kind), None)
        if ctype is None:
            ctype = api.root.create_entity(f, ifc_class="IfcCoveringType", name=tname, predefined_type=kind)
        if ifcopenshell.util.element.get_type(e) != ctype:
            api.type.assign_type(f, related_objects=[e], relating_type=ctype)
