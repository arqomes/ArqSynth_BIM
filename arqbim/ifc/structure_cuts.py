"""(0.531) Structure cuts the masonry: where a column, beam or steel piece passes through a wall, the wall is taken
away there — as a boolean A − B. Each such cut is an IfcOpeningElement RECESS of the wall (Elemento
"corte_estrutura", Estrutura = the piece's GlobalId) whose body is the piece's own shape in the wall's frame, so that
the wall keeps its own body and the program's geometry (and any IFC reader) takes the piece out of it. The cuts are
made again whenever a wall or a piece is made or changed (follow_structure_cuts, after each edit), and taken away
when the piece leaves the wall or is removed."""

import ifcopenshell.api as api
import numpy as np

STRUCTURE = ("IfcColumn", "IfcBeam", "IfcMember")
MARK = "corte_estrutura"
GAP = 1e-3                                  # (overlaps thinner than a millimetre do not cut)


class StructureCutMixin:

    def is_structure_cut(self, opening):
        if isinstance(opening, str):
            opening = self.by_guid(opening)
        return opening is not None and opening.is_a("IfcOpeningElement") and \
            self._params(opening).get("Elemento") == MARK

    def structure_cuts(self, wall):
        """{piece GlobalId: its cut opening} of a wall."""
        e = self.by_guid(wall) if isinstance(wall, str) else wall
        out = {}
        for rel in (getattr(e, "HasOpenings", None) or ()) if e is not None else ():
            o = rel.RelatedOpeningElement
            if self.is_structure_cut(o):
                out[self._params(o).get("Estrutura") or ""] = o
        return out

    def _is_structure(self, e):
        return e is not None and any(e.is_a(c) for c in STRUCTURE)

    def _cuttable_wall(self, guid):
        e = self.by_guid(guid)
        return e is not None and e.is_a("IfcWall") and self.kind_of(guid) == "wall"

    def _piece_mesh(self, guid):
        """(verts, tris) of a piece in the program's coordinates — kept while its body and placement stay as they are."""
        e = self.by_guid(guid)
        cache = self.__dict__.setdefault("_structure_meshes", {})
        key = (e.Representation.id() if e.Representation else 0,
               tuple(np.round(self._placement_si(e), 6).ravel()))
        hit = cache.get(guid)
        if hit is not None and hit[0] == key:
            return hit[1]
        mesh = self.triangulate([guid]).get(guid)
        if mesh is None or len(mesh[0]) == 0:
            mesh = None
        cache[guid] = (key, mesh)
        return mesh

    def _wall_world_box(self, wall):
        length, height, thickness = self.wall_params(wall)
        m = self.placement(wall)
        corners = np.array([(x, y, z, 1.0) for x in (0.0, length) for y in (-thickness, thickness)
                            for z in (0.0, height)])
        w = (m @ corners.T).T[:, :3]
        return w.min(axis=0), w.max(axis=0)

    def _pieces_near(self, wall):
        """The pieces of the wall's storey (and those already cutting it)."""
        storey = self.storey_of(wall)
        out = set(self.structure_cuts(wall))
        for g in self.storey_elements(storey) if storey else ():
            if self._is_structure(self.by_guid(g)):
                out.add(g)
        return out

    def _walls_near(self, piece):
        storey = self.storey_of(piece)
        return [g for g in (self.storey_elements(storey) if storey else ()) if self._cuttable_wall(g)]

    def refit_structure_cuts(self, wall):
        """A wall's cuts made again from the pieces passing through it now. True when its shape changed."""
        if not self._cuttable_wall(wall):
            return False
        e = self.by_guid(wall)
        cuts = self.structure_cuts(e)
        length, height, thickness = self.wall_params(wall)
        m = self.placement(wall)
        inv = np.linalg.inv(m)
        wlo, whi = self._wall_world_box(wall)
        lo_l, hi_l = np.array((0.0, -thickness / 2, 0.0)), np.array((length, thickness / 2, height))
        changed = False
        keep = set()
        for piece in sorted(self._pieces_near(wall)):
            pe = self.by_guid(piece)
            if not self._is_structure(pe):
                continue
            mesh = self._piece_mesh(piece)
            if mesh is None:
                continue
            verts, tris = mesh
            if np.any(verts.min(axis=0) > whi - GAP) or np.any(verts.max(axis=0) < wlo + GAP):
                continue
            local = (inv @ np.column_stack((verts, np.ones(len(verts)))).T).T[:, :3]
            if np.any(local.min(axis=0) > hi_l - GAP) or np.any(local.max(axis=0) < lo_l + GAP):
                continue
            keep.add(piece)
            self._set_cut_body(e, cuts.get(piece), piece, local, tris, m)
            changed = True
        for piece, opening in cuts.items():
            if piece not in keep:
                api.root.remove_product(self.file, product=opening)
                changed = True
        return changed

    def _set_cut_body(self, wall, opening, piece, local, tris, matrix):
        f = self.file
        if opening is None:
            opening = api.root.create_entity(f, ifc_class="IfcOpeningElement", name="Estrutura",
                                             predefined_type="RECESS")
            api.feature.add_feature(f, feature=opening, element=wall)
            self._set_params(opening, {"Elemento": MARK, "Estrutura": piece})
        else:
            self._clear_representations(opening)
        body = api.geometry.add_mesh_representation(
            f, context=self.body, vertices=[[tuple(float(c) for c in v) for v in local]],
            faces=[[[int(i) for i in t] for t in tris]], unit_scale=self.unit_scale)
        api.geometry.assign_representation(f, product=opening, representation=body)
        self._place(opening, matrix)

    def follow_structure_cuts(self, changed):
        """After an edit: the walls among `changed` cut again by the pieces in them, and the walls near the pieces
        among `changed` (and those they cut before) too. The walls whose shape changed."""
        walls = []
        pieces = []
        for g in changed:
            e = self.by_guid(g)
            if e is None:
                continue
            if self._cuttable_wall(g):
                walls.append(g)
            elif self._is_structure(e):
                pieces.append(g)
                self.__dict__.get("_structure_meshes", {}).pop(g, None)
        if not pieces and not any(w for w in walls if self._pieces_near(w)):
            return []
        for p in pieces:
            for w in self._walls_near(p) + self._walls_cut_by(p):
                if w not in walls:
                    walls.append(w)
        return [w for w in walls if self.refit_structure_cuts(w)]

    def _walls_cut_by(self, piece):
        out = []
        for o in self.file.by_type("IfcOpeningElement"):
            if self.is_structure_cut(o) and self._params(o).get("Estrutura") == piece:
                out += [rel.RelatingBuildingElement.GlobalId for rel in o.VoidsElements or ()]
        return out

    def drop_structure_cuts(self, guids):
        """Pieces about to be removed: their cuts in the walls taken away. The walls whose shape changed."""
        out = []
        for g in guids:
            if not self._is_structure(self.by_guid(g)):
                continue
            for w in self._walls_cut_by(g):
                opening = self.structure_cuts(w).get(g)
                if opening is not None:
                    api.root.remove_product(self.file, product=opening)
                    out.append(w)
        return out
