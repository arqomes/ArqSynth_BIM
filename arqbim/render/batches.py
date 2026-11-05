"""Batched display of IFC elements (Phase 2, step 1 â€” "agrupamento de desenho").

Before, each element was two GPU objects (faces + edges): two draw calls per
frame and ~5 ms to create. Now elements are packed into batches: one mesh and
one set of lines per batch, by storey (so a storey can be hidden at once), up
to MAX_TRIANGLES each. A frame is a few dozen draw calls whatever the size of
the model. Colours are per vertex: selecting an element recolours its range in
place; editing an element only rebuilds its own batch, which stays small.

Picking: the GPU says which batch mesh and which triangle; the batch maps the
triangle back to the element and its face. All shading is shared: one face
material and one line material for every batch.
"""

import time

import numpy as np
import pygfx as gfx

from . import canvas

MAX_TRIANGLES = 30000          # per batch (measured: fewer, bigger batches navigate faster; rebuilding one stays ~5 ms)
FEW_BATCHES = 4                # (0.328) changed at once up to so many (an edit): all made again in one image
EDGE_LIFT = 0.002              # m; keeps edge lines visible on top of their faces
POCHE_COLOR = "#3a3a3a"        # what a plan cuts through
EARTH_POCHE = "#9a8866"        # …the terrain (0.156: its batches marked GROUND)
GROUND = "ground"              # the mark of a terrain's batch (in its key)
POCHE_LIFT = 0.01              # m (see Batch._sync_poche)
# the 3D view's faces (BatchedElements.set_look): shaded, hidden lines (white), wireframe, x-ray — and (0.315)
# consistent colours (no light)
STYLES = ("shaded", "hidden", "wire", "xray", "consistent")
CLEAR = "clear"                # (0.315) the mark of a batch of elements with see-through parts (glass): drawn after
CLEAR_QUEUE = 3000             # the others (pygfx's queue of the transparent)
_I4 = np.eye(4)


def physical(rgb):
    """sRGB colours (…, 3) in 0–1 as the physical (linear) values the batches' vertex colours are."""
    c = np.asarray(rgb, dtype=np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


class Piece:
    """One element's display data, in world coordinates, ready to be concatenated."""

    def __init__(self, mesh, matrix, face_color, edge_color, ground=False, pattern=None, split=None, seams=None,
                 turned=False):
        """ground (0.155): a terrain — the edges between its surface's triangles not drawn. face_color None
        (0.259): the mesh's own colours, triangle by triangle (a railing's wooden rail, steel posts, glass).
        pattern (0.315): its materials' surface patterns, (segments' ends (2M, 3), their colours (2M, 4)), world.
        split (0.315): its faces drawn as other triangles — (their corners (K, 3, 3), each one's face (K,), their
        normals (K, 3)), world — a wall's top cut along its layers; its edges are the mesh's. seams (0.320): its
        seams with its neighbours of one material (model/seen_joins.seams: each edge kept or not, what is left of
        those partly joined and their planes' normals), world — left out. turned (0.341): its own colours' greys
        turned over (render/canvas: a plan or a section on the dark views)."""
        self.seams = seams
        if pattern is not None and len(pattern[0]):
            self.pattern = np.ascontiguousarray(pattern[0], dtype=np.float32).reshape(-1, 3)
            self.pattern_colors = np.ascontiguousarray(pattern[1], dtype=np.float32).reshape(-1, 4)
        else:
            self.pattern = np.zeros((0, 3), np.float32)
            self.pattern_colors = np.zeros((0, 4), np.float32)
        verts = np.asarray(mesh.verts, dtype=float).reshape(-1, 3)
        m = np.asarray(matrix, dtype=float)
        tris, owner = mesh.triangulate()
        own = getattr(mesh, "colors", None)
        self.own = None                                 # (per vertex, physical, its alpha 1)
        if own is not None and len(own) == len(owner):
            seen = canvas.ink_array(own[owner]) if turned else own[owner]
            rgb = np.repeat(physical(seen), 3, axis=0)
            self.own = np.column_stack((rgb, np.ones(len(rgb), np.float32))).astype(np.float32)
        if face_color is None:
            face_color = self.own if self.own is not None else (0.5, 0.5, 0.5, 1.0)
        normals = np.asarray(mesh.normals, dtype=float) if hasattr(mesh, "normals") else \
            np.array([mesh.face_normal(fi) for fi in range(len(mesh.faces))]).reshape(-1, 3)
        if not np.array_equal(m, _I4):           # IFC elements come in world coordinates: nothing to do
            verts = verts @ m[:3, :3].T + m[:3, 3]
            normals = normals @ m[:3, :3].T
        if split is not None:                    # (0.315: cut along its layers, to be coloured each its own)
            corners, faces_of, split_normals = split
            self.positions = np.ascontiguousarray(np.asarray(corners).reshape(-1, 3), dtype=np.float32)
            self.normals = np.ascontiguousarray(np.repeat(split_normals, 3, axis=0), dtype=np.float32)
            self.owner = np.asarray(faces_of, dtype=np.int64)
        else:
            self.positions = np.ascontiguousarray(verts[tris.reshape(-1)], dtype=np.float32)
            self.normals = np.ascontiguousarray(np.repeat(normals[owner], 3, axis=0), dtype=np.float32)
            self.owner = np.asarray(owner, dtype=np.int64)              # triangle -> face of the element
        pairs, faces = mesh.edge_array()
        if seams is not None and len(seams[0]) == len(pairs):           # (0.320: its seams left out)
            pairs, faces = pairs[seams[0]], faces[seams[0]]
        if ground and len(pairs):
            up = normals[:, 2] > 0.05
            keep = ~((faces[:, 1] >= 0) & up[faces[:, 0]] & up[np.maximum(faces[:, 1], 0)])
            pairs, faces = pairs[keep], faces[keep]
        lift = normals[faces[:, 0]] + np.where(faces[:, 1:] >= 0, normals[np.maximum(faces[:, 1], 0)], 0.0)
        length = np.linalg.norm(lift, axis=1)
        lift = lift / np.where(length > 1e-9, length, 1.0)[:, None] * EDGE_LIFT
        ends = np.stack((verts[pairs[:, 0]] + lift, verts[pairs[:, 1]] + lift), axis=1)
        if seams is not None and len(seams[1]):                          # (…what is left of those partly joined)
            ends = np.concatenate((ends, seams[1] + seams[2][:, None, :] * EDGE_LIFT))
        self.edges = np.ascontiguousarray(ends.reshape(-1, 3), dtype=np.float32)
        self.face_color = face_color
        self.edge_color = edge_color
        self.source = mesh                      # the mesh it was made from

    @property
    def triangles(self):
        return len(self.owner)


_NO_PATTERN = np.zeros((0, 3), np.float32)
_NO_PATTERN_COLORS = np.zeros((0, 4), np.float32)


def plain_pieces(meshes, face_colors, edge_color):
    """(0.344) Many elements' plain pieces at once — in world coordinates, in one colour each (`face_colors`, one per
    mesh; None: the mesh's own colours, triangle by triangle), without seams, patterns or cuts: the same as Piece one
    by one, worked out on all of them together (a big model opening: 12 000 pieces in a tenth of the time). Their
    bounds worked out too (mesh.bounds())."""
    meshes = list(meshes)
    if not meshes:
        return []
    verts = [np.asarray(m.verts, dtype=float).reshape(-1, 3) for m in meshes]
    tris = [np.asarray(m.tris, dtype=np.int64).reshape(-1, 3) for m in meshes]
    normals = [np.asarray(m.normals, dtype=float).reshape(-1, 3) for m in meshes]
    edges = [m.edge_array() for m in meshes]
    nv = np.array([len(v) for v in verts])
    nt = np.array([len(t) for t in tris])
    ne = np.array([len(p) for p, _f in edges])
    v0 = np.concatenate(([0], np.cumsum(nv)[:-1]))
    t0 = np.concatenate(([0], np.cumsum(nt)[:-1]))
    V = np.concatenate(verts)
    N = np.concatenate(normals)
    T = np.concatenate(tris) + np.repeat(v0, nt)[:, None]
    owner = np.arange(int(nt.sum()), dtype=np.int64) - np.repeat(t0, nt)          # (triangle -> face of its element)
    positions = np.ascontiguousarray(V[T.reshape(-1)], dtype=np.float32)
    tri_normals = np.ascontiguousarray(np.repeat(N, 3, axis=0), dtype=np.float32)
    P = np.concatenate([p for p, _f in edges]).astype(np.int64).reshape(-1, 2) + np.repeat(v0, ne)[:, None]
    F = np.concatenate([f for _p, f in edges]).astype(np.int64).reshape(-1, 2)
    first = F[:, 0] + np.repeat(t0, ne)
    second = np.where(F[:, 1] >= 0, F[:, 1] + np.repeat(t0, ne), -1)
    lift = N[first] + np.where((second >= 0)[:, None], N[np.maximum(second, 0)], 0.0)
    length = np.linalg.norm(lift, axis=1)
    lift = lift / np.where(length > 1e-9, length, 1.0)[:, None] * EDGE_LIFT
    ends = np.ascontiguousarray(np.stack((V[P[:, 0]] + lift, V[P[:, 1]] + lift), axis=1).reshape(-1, 3),
                                dtype=np.float32)
    at_t, at_e = np.cumsum(nt)[:-1], np.cumsum(ne)[:-1]
    pos_of = np.split(positions, at_t * 3)
    nrm_of = np.split(tri_normals, at_t * 3)
    face_of = np.split(owner, at_t)
    end_of = np.split(ends, at_e * 2)
    own_of = {}
    owned = [k for k, c in enumerate(face_colors) if c is None]
    if owned:                                          # (0.259: in their parts' own colours, by vertex, physical)
        rgb = np.repeat(physical(np.concatenate([np.asarray(meshes[k].colors).reshape(-1, 3) for k in owned])), 3,
                        axis=0)
        rgba = np.column_stack((rgb, np.ones(len(rgb), np.float32))).astype(np.float32)
        own_of = dict(zip(owned, np.split(rgba, np.cumsum([nt[k] * 3 for k in owned])[:-1])))
    filled = nv > 0
    if filled.any():                                   # (each one's box: for the inferences and framing)
        starts = v0[filled]
        lows, highs = np.minimum.reduceat(V, starts, axis=0), np.maximum.reduceat(V, starts, axis=0)
        for k, low, high in zip(np.flatnonzero(filled), lows, highs):
            if meshes[k]._bounds is None:
                meshes[k]._bounds = (low, high)
    out = []
    for k, mesh in enumerate(meshes):
        p = Piece.__new__(Piece)
        p.seams, p.own, p.source = None, own_of.get(k), mesh
        p.pattern, p.pattern_colors = _NO_PATTERN, _NO_PATTERN_COLORS
        p.positions, p.normals, p.owner, p.edges = pos_of[k], nrm_of[k], face_of[k], end_of[k]
        p.face_color = face_colors[k] if face_colors[k] is not None else p.own
        p.edge_color = edge_color
        out.append(p)
    return out


def _face_material(style, clear=False):
    """The faces' material of a visual style; clear (0.315): for the batches with glass — their see-through parts
    blended, drawn after all the others (CLEAR_QUEUE)."""
    queue = {"render_queue": CLEAR_QUEUE} if clear else {}
    if style == "hidden":                       # (0.341: white — a plan's on the dark views, nearly its background)
        return gfx.MeshBasicMaterial(color="#ffffff", color_mode="uniform", side="both", pick_write=True)
    if style == "wire":
        return gfx.MeshBasicMaterial(color=(1.0, 1.0, 1.0, 0.0), color_mode="uniform", alpha_mode="blend",
                                     depth_write=False, side="both", pick_write=True)
    if style == "xray":
        return gfx.MeshPhongMaterial(color_mode="vertex", specular="#000", flat_shading=True, side="both",
                                     opacity=0.3, alpha_mode="blend", depth_write=False, pick_write=True)
    if style == "consistent":
        return gfx.MeshBasicMaterial(color_mode="vertex", side="both", pick_write=True, **queue)
    return gfx.MeshPhongMaterial(color_mode="vertex", specular="#000", flat_shading=True, side="both",
                                 pick_write=True, **queue)


def _spread(colour, n):
    """A piece's colour for its n vertices: one colour repeated, or (0.259) its own colour by vertex."""
    c = np.asarray(colour, dtype=np.float32)
    return c.reshape(n, 4) if c.ndim == 2 else np.repeat(c.reshape(1, 4), n, axis=0)


class Batch:
    def __init__(self, key, root, face_material, line_material, poche_material=None, pattern_material=None):
        self.key = key                # storey GlobalId (or None)
        self.root = root
        self.face_material, self.line_material = face_material, line_material
        self.poche_material = poche_material
        self.pattern_material = pattern_material        # (0.315) its surface patterns' lines
        self.poche = None             # the same triangles seen from inside, filled dark (plans: what is cut)
        self.patterns = None          # (0.315) its pieces' surface patterns (one line object)
        self.show_poche = False
        self.poche_lift = (0.0, 0.0, POCHE_LIFT)
        self.show_edges = True        # the edges drawn (the 3D view's visual style can leave them out)
        self.show_patterns = True     # (0.315) its surface patterns drawn
        self.shadows = False          # (0.315) its faces cast and receive the sun's shadows
        self.clear = isinstance(key, tuple) and len(key) > 4 and key[4] == CLEAR
        self.pieces = {}              # obj_id -> Piece (insertion order kept)
        self.ranges = {}              # obj_id -> (first vertex, vertices, first edge vertex, edge vertices)
        self.tri_obj = np.zeros(0, np.int64)
        self.tri_face = np.zeros(0, np.int64)
        self.ids = []
        self.mesh = self.lines = None
        self.used = {}                # "mesh" / "lines" -> items in use in its buffers (the rest is spare)
        self.dirty = True
        self.visible = True
        self.triangles = 0            # kept up to date by set_piece / drop_piece
        self._added = []              # pieces new since the last rebuild (only these: see _append)
        self._reshaped = False        # a piece replaced or removed since the last rebuild

    def set_piece(self, obj_id, piece):
        old = self.pieces.get(obj_id)
        self.triangles += piece.triangles - (old.triangles if old is not None else 0)
        if old is None:
            self._added.append(obj_id)
        else:
            self._reshaped = True
        self.pieces[obj_id] = piece
        self.dirty = True

    def drop_piece(self, obj_id):
        old = self.pieces.pop(obj_id, None)
        if old is not None:
            self.triangles -= old.triangles
            self._reshaped = True
            self.dirty = True

    def _drop_gpu(self):
        for wobj in (self.mesh, self.lines, self.poche, self.patterns):
            if wobj is not None:
                self.root.remove(wobj)
        self.mesh = self.lines = self.poche = self.patterns = None
        self.used = {}

    def _sync_poche(self):
        """The poché object shares the mesh's buffers; shown in plans only."""
        if self.mesh is None or self.poche_material is None:
            if self.poche is not None:
                self.root.remove(self.poche)
                self.poche = None
            return
        if self.poche is None:
            self.poche = gfx.Mesh(self.mesh.geometry, self.poche_material)
            self.root.add(self.poche)
        elif self.poche.geometry is not self.mesh.geometry:
            self.poche.geometry = self.mesh.geometry
        # a hair towards the viewer: in a plan the inside of a cut wall (its bottom face) sits on the
        # floor slab's top, at the same depth — the slab would show through in specks; moved, it wins
        self.poche.local.position = self.poche_lift
        self.poche.visible = self.visible and self.show_poche

    def rebuild(self):
        """Concatenate the pieces into one mesh and one line object."""
        self.dirty = False
        added, reshaped = self._added, self._reshaped
        self._added, self._reshaped = [], False
        if added and not reshaped and self._append(added):
            return
        self.ids = list(self.pieces)
        if not self.ids:
            self._drop_gpu()
            return
        pieces = [self.pieces[i] for i in self.ids]
        self.ranges, v, e = {}, 0, 0
        for obj_id, p in zip(self.ids, pieces):
            self.ranges[obj_id] = (v, len(p.positions), e, len(p.edges))
            v += len(p.positions)
            e += len(p.edges)
        self.tri_obj = np.repeat(np.arange(len(pieces), dtype=np.int64), [p.triangles for p in pieces])
        self.tri_face = np.concatenate([p.owner for p in pieces])
        faces = lines = None
        if v:                                   # (0.256: the pieces' parts, written straight into the buffers)
            faces = {"positions": [p.positions for p in pieces], "normals": [p.normals for p in pieces],
                     "colors": [(p.face_color, len(p.positions)) for p in pieces]}
        if e:
            lines = {"positions": [p.edges for p in pieces], "colors": [(p.edge_color, len(p.edges)) for p in pieces]}
        # the same GPU objects keep their place: only their data changes (cheaper than new objects)
        self.mesh = self._update(self.mesh, faces, v, gfx.Mesh, self.face_material, "mesh")
        self.lines = self._update(self.lines, lines, e, gfx.Line, self.line_material, "lines")
        self._sync_poche()
        self._sync_shadows()
        n = sum(len(p.pattern) for p in pieces)                   # (0.315) their surface patterns
        drawn = {"positions": [p.pattern for p in pieces if len(p.pattern)],
                 "colors": [(p.pattern_colors, len(p.pattern)) for p in pieces if len(p.pattern)]} if n else None
        if self.pattern_material is not None:
            self.patterns = self._update(self.patterns, drawn, n, gfx.Line, self.pattern_material, "patterns")

    def _sync_shadows(self):
        if self.mesh is not None:
            self.mesh.cast_shadow = self.mesh.receive_shadow = self.shadows

    def _append(self, added):
        """Only pieces were added since the last rebuild (a file coming in as its shapes are made):
        write them after the others, in the same buffers, if these have room. False: they have
        not (or there are none yet) — the whole batch is made again."""
        pieces = [self.pieces[i] for i in added]
        if self.patterns is not None or any(len(p.pattern) for p in pieces):
            return False                                          # (0.315: with surface patterns, made again)
        nv, ne = sum(len(p.positions) for p in pieces), sum(len(p.edges) for p in pieces)
        v0, e0 = self.used.get("mesh", 0), self.used.get("lines", 0)
        for wobj, n0, n in ((self.mesh, v0, nv), (self.lines, e0, ne)):
            if n and (wobj is None or wobj.geometry.positions.nitems < n0 + n):
                return False
        k0, v, e = len(self.ids), v0, e0
        for obj_id, p in zip(added, pieces):
            self.ranges[obj_id] = (v, len(p.positions), e, len(p.edges))
            v += len(p.positions)
            e += len(p.edges)
        self.ids += added
        self.tri_obj = np.concatenate([self.tri_obj] + [np.full(p.triangles, k0 + k, np.int64)
                                                        for k, p in enumerate(pieces)])
        self.tri_face = np.concatenate([self.tri_face] + [p.owner for p in pieces])
        if nv:
            self._write(self.mesh.geometry, v0, {
                "positions": np.concatenate([p.positions for p in pieces]),
                "normals": np.concatenate([p.normals for p in pieces]),
                "colors": np.concatenate([_spread(p.face_color, len(p.positions)) for p in pieces])})
            self.used["mesh"] = v0 + nv
            self.mesh.geometry.indices.draw_range = (0, (v0 + nv) // 3)
        if ne:
            self._write(self.lines.geometry, e0, {
                "positions": np.concatenate([p.edges for p in pieces]),
                "colors": np.concatenate([_spread(p.edge_color, len(p.edges)) for p in pieces])})
            self.used["lines"] = e0 + ne
            self.lines.geometry.positions.draw_range = (0, e0 + ne)
        return True

    @staticmethod
    def _write(geometry, start, arrays):
        n = len(arrays["positions"])
        for k, a in arrays.items():
            buf = getattr(geometry, k)
            buf.data[start:start + n] = a
            buf.update_range(start, n)

    def _update(self, wobj, parts, n, cls, material, kind):
        """Put new data in a GPU object — parts: {"positions" / "normals": [the pieces' arrays], "colors":
        [(colour, items)]}, n items in all, written straight into the buffers (0.256: no array of the whole batch
        made first and copied again). Its buffers are reused while they are big enough: an edit then costs one
        upload, with no new GPU memory nor bindings (which made the image after an edit 2–3 times slower); else
        bigger ones are made, with room to grow."""
        if parts is None:
            if wobj is not None:
                self.root.remove(wobj)
            self.used.pop(kind, None)
            return None
        geometry = wobj.geometry if wobj is not None else None
        fresh = geometry is None or geometry.positions.nitems < n
        before = self.used.get(kind, 0)
        if fresh:
            # with room to grow: a quarter more, or twice the old size for a batch that is growing
            room = max(n + n // 4, 2 * geometry.positions.nitems if geometry is not None else 0) + 6
            room -= room % 6                       # whole triangles (3) and whole segments (2)
            data = {k: np.empty((room, 4 if k == "colors" else 3), np.float32) for k in parts}
            spare = room
        else:
            data = {k: getattr(geometry, k).data for k in parts}
            spare = before                         # (what is no longer used: back to spare room)
        for k, items in parts.items():
            dest = data[k]
            if k == "colors":
                at = 0
                for colour, count in items:
                    dest[at:at + count] = colour
                    at += count
            else:
                np.concatenate(items, out=dest[:n])
            if spare > n:
                dest[n:spare] = dest[0]            # spare room: copies of a point, never drawn
        if fresh:
            if kind == "mesh":
                data["indices"] = np.arange(room, dtype=np.uint32).reshape(-1, 3)
            geometry = gfx.Geometry(**data)
            if wobj is None:
                wobj = cls(geometry, material)
                self.root.add(wobj)
            else:
                wobj.geometry = geometry
        else:
            for k in parts:
                getattr(geometry, k).update_range(0, max(n, before))
        self.used[kind] = n
        if kind == "mesh":
            geometry.indices.draw_range = (0, n // 3)
        else:
            geometry.positions.draw_range = (0, n)
        wobj.visible = self.visible and (kind == "mesh" or (self.show_patterns if kind == "patterns"
                                                            else self.show_edges))
        return wobj

    def recolor(self, obj_id, face_color, edge_color):
        piece = self.pieces[obj_id]
        if face_color is None:                # (0.259: back to its own colours, else a grey)
            face_color = piece.own if piece.own is not None else (0.5, 0.5, 0.5, 1.0)
        piece.face_color, piece.edge_color = face_color, edge_color
        if obj_id not in self.ranges or self._reshaped:
            # not in the buffers yet — or (0.333) a piece replaced or removed since they were written: their places
            # are old (a new piece's colours, one per vertex, do not fit its old place) and the next rebuild writes
            # them all, with these colours
            return
        # (in the buffers already: written now even if the batch waits for a rebuild — when that only adds pieces
        # after the others, this one is not written again, and kept its old colours: 0.96)
        v0, nv, e0, ne = self.ranges[obj_id]
        if nv and self.mesh is not None:
            buf = self.mesh.geometry.colors
            buf.data[v0:v0 + nv] = face_color
            buf.update_range(v0, nv)
        if ne and self.lines is not None:
            buf = self.lines.geometry.colors
            buf.data[e0:e0 + ne] = edge_color
            buf.update_range(e0, ne)

    def set_visible(self, on):
        self.visible = on
        if self.mesh is not None:
            self.mesh.visible = on
        if self.lines is not None:
            self.lines.visible = on and self.show_edges
        if self.poche is not None:
            self.poche.visible = on and self.show_poche
        if self.patterns is not None:
            self.patterns.visible = on and self.show_patterns

    def set_look(self, face_material, edges, patterns=True):
        """The 3D view's visual style: the faces' material, the edges drawn or not — (0.315) and the surface
        patterns."""
        self.face_material, self.show_edges, self.show_patterns = face_material, edges, patterns
        if self.mesh is not None:
            self.mesh.material = face_material
        if self.lines is not None:
            self.lines.visible = self.visible and edges
        if self.patterns is not None:
            self.patterns.visible = self.visible and patterns

    def set_shadows(self, on):
        self.shadows = bool(on)
        self._sync_shadows()

    def set_poche(self, on):
        self.show_poche = on
        self._sync_poche()

    def pick(self, face_index):
        """(obj_id, face of that element) of a triangle of this batch's mesh."""
        if face_index is None or not 0 <= face_index < len(self.tri_obj):
            return None
        return self.ids[int(self.tri_obj[face_index])], int(self.tri_face[face_index])


class BatchedElements:
    """All IFC elements on screen, in batches."""

    def __init__(self, root):
        self.root = root
        self.batches = []
        self.where = {}               # obj_id -> Batch
        # the faces' material for each visual style of the 3D view (0.63): shaded (the usual), hidden lines (white
        # faces, the edges in front), wireframe (edges only: faces still picked) and x-ray (see-through colours);
        # (0.315) consistent colours (each its colour, no light); and each again for the batches with glass, drawn
        # after the others (CLEAR)
        self.face_materials = {style: _face_material(style) for style in STYLES}
        self.clear_materials = {style: _face_material(style, clear=True) for style in STYLES}
        self.style, self.edges, self.patterns, self.shadows = "shaded", True, True, False
        self.face_material = self.face_materials["shaded"]
        self.line_material = gfx.LineSegmentMaterial(thickness=1.5, color_mode="vertex", aa=True)
        self.pattern_material = gfx.LineSegmentMaterial(thickness=1.0, color_mode="vertex", aa=True)    # (0.315)
        # Plans: the solids are cut by a plane; through the cut one sees the inside of the solids, i.e.
        # their faces from behind — drawn in one dark colour they fill what is cut (the poché).
        self.poche_material = gfx.MeshBasicMaterial(color=canvas.ink(POCHE_COLOR), side="back", pick_write=True)
        self.earth_material = gfx.MeshBasicMaterial(color=canvas.ink(EARTH_POCHE), side="back", pick_write=True)
        self.cutting = False
        self.poche_lift = (0.0, 0.0, POCHE_LIFT)

    def set_canvas(self, turned):
        """(0.341) The colours of its own materials in the canvas in use (render/canvas): the poché; the hidden-line
        style's white faces — turned over (dark) when the model's greys are (a plan or a section on the dark views).
        The elements' edges and faces are recoloured by the viewport."""
        for materials in (self.face_materials, self.clear_materials):
            materials["hidden"].color = canvas.ink("#ffffff") if turned else "#ffffff"
        self.poche_material.color = canvas.ink(POCHE_COLOR)
        self.earth_material.color = canvas.ink(EARTH_POCHE)

    def set_cut(self, on, planes=(), lift=(0.0, 0.0, POCHE_LIFT)):
        """Plan / section display: everything cut by `planes` (pygfx clipping planes), the cut
        filled dark, the faces drawn from the front only (so the poché shows through the cut);
        lift: where the poché is moved, a hair towards the viewer."""
        self.cutting = bool(on)
        self.poche_lift = tuple(lift)
        for material in (*self.face_materials.values(), *self.clear_materials.values()):
            material.side = "front" if self.cutting else "both"
        for material in (*self.face_materials.values(), *self.clear_materials.values(), self.line_material,
                         self.poche_material, self.earth_material, self.pattern_material):
            material.clipping_planes = list(planes)
        for batch in self.batches:
            batch.poche_lift = self.poche_lift
            batch.set_poche(self.cutting)

    def set_look(self, style, edges=True, width=None, patterns=None):
        """The visual style (STYLES) and whether the edges are drawn — (0.315) how thick (px), and the surface
        patterns."""
        style = style if style in self.face_materials else "shaded"
        if width is not None and abs(self.line_material.thickness - float(width)) > 1e-9:
            self.line_material.thickness = float(width)
        patterns = self.patterns if patterns is None else bool(patterns)
        if (style, bool(edges), patterns) == (self.style, self.edges, self.patterns):
            return
        self.style, self.edges, self.patterns = style, bool(edges), patterns
        self.face_material = self.face_materials[style]
        for batch in self.batches:
            batch.set_look(self.clear_materials[style] if batch.clear else self.face_material, self.edges, patterns)

    def set_shadows(self, on):
        """(0.315) The faces cast and receive the sun's shadows."""
        self.shadows = bool(on)
        for batch in self.batches:
            batch.set_shadows(self.shadows)

    def set_poche_lift(self, lift):
        """Move the poché a hair towards the viewer (a section box: wherever they look from)."""
        self.poche_lift = tuple(lift)
        for batch in self.batches:
            batch.poche_lift = self.poche_lift
            if batch.poche is not None:
                batch.poche.local.position = self.poche_lift

    def set_poche_colours(self, on):
        """What is cut filled with each element's own colour (a graphic rule: a demolished wall
        yellow…) instead of the one dark poché."""
        mode = "vertex" if on else "uniform"
        if self.poche_material.color_mode != mode:
            self.poche_material.color_mode = mode

    def __contains__(self, obj_id):
        return obj_id in self.where

    def put(self, obj_id, piece, key):
        """Add or replace an element (its batch is rebuilt at the next flush)."""
        batch = self.where.get(obj_id)
        if batch is not None and batch.key != key:
            self.remove(obj_id)
            batch = None
        if batch is None:
            batch = next((b for b in reversed(self.batches)
                          if b.key == key and b.triangles + piece.triangles <= MAX_TRIANGLES), None)
            if batch is None:
                ground = isinstance(key, tuple) and len(key) > 2 and key[2] == GROUND
                clear = isinstance(key, tuple) and len(key) > 4 and key[4] == CLEAR
                batch = Batch(key, self.root, self.clear_materials[self.style] if clear else self.face_material,
                              self.line_material, self.earth_material if ground else self.poche_material,
                              self.pattern_material)
                batch.show_poche, batch.poche_lift, batch.show_edges = self.cutting, self.poche_lift, self.edges
                batch.show_patterns, batch.shadows = self.patterns, self.shadows
                self.batches.append(batch)
            self.where[obj_id] = batch
        batch.set_piece(obj_id, piece)

    def remove(self, obj_id):
        batch = self.where.pop(obj_id, None)
        if batch is not None:
            batch.drop_piece(obj_id)

    def flush(self, budget=None):
        """Rebuild the batches that changed (called before drawing). (0.328) budget (s): when many changed at once
        (a file opened: all of them), as many as fit in it now and the others at the next images — the window never
        stops for long: each image also sends to the graphics card only the batches made for it (reopening the big
        building: one stop of 1,1 s, now a dozen images of ~0,1 s). A few changed (an edit): all now, as before.
        True if some are left."""
        dirty = [b for b in self.batches if b.dirty]
        start = time.perf_counter()
        for k, batch in enumerate(dirty):
            if budget is not None and k and len(dirty) > FEW_BATCHES and time.perf_counter() - start > budget:
                return True
            batch.rebuild()
            if not batch.pieces:
                self.batches.remove(batch)
        return False

    def pending(self):
        """(0.328) Batches still to be made again (see flush's budget)."""
        return any(b.dirty for b in self.batches)

    def recolor(self, obj_id, face_color, edge_color):
        batch = self.where.get(obj_id)
        if batch is not None:
            batch.recolor(obj_id, face_color, edge_color)

    def set_visible(self, shown):
        """shown(key) -> bool for each batch's storey."""
        for batch in self.batches:
            batch.set_visible(shown(batch.key))

    def is_visible(self, obj_id):
        batch = self.where.get(obj_id)
        return batch is not None and batch.visible

    def pick(self, world_object, face_index):
        for batch in self.batches:
            if batch.mesh is world_object or (batch.poche is not None and batch.poche is world_object):
                return batch.pick(face_index)          # (in a plan, clicking what is cut picks it)
        return None

    def owns(self, world_object):
        return any(world_object is b.mesh or world_object is b.lines or world_object is b.poche
                   for b in self.batches if world_object is not None)

    def stats(self):
        return {"batches": len(self.batches), "elements": len(self.where)}
