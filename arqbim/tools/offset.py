"""Offset tool (0.152, Phase 7, step 1 — SketchUp's 'F'): a click on a face of a sketch, then the mouse inside it
(or outside) shows its outline offset that far; a second click — or the distance typed, "0,10" + Enter — makes it:
inside, the face is divided along it (a frame round a window, a border to push in); outside, a lone face grows,
its old outline kept inside it. Convex faces (rectangles, circles, regular polygons) and, since 0.206, concave ones
(an L, a U): the frame between the two outlines a four-sided face per side.

(0.373) Lines too, as SketchUp's offset of edges picked: a click on a loose line takes its chain (an arc, a curve:
the whole of it) — or the lines picked before, if there are — and the mouse shows their parallel on the side it is,
in their plane, the corners sharp; an arc's is the arc about the same centre. The copy is new lines."""

from dataclasses import dataclass

import numpy as np

from ..core import curves as core_curves
from ..core.lines import offset_path, paths, plane_of
from ..core.mesh import PolyMesh
from ..core.sketch_geometry import (
    _face_frame, imprint_polygon, plane_axes, polygon_mesh, ray_plane, transform_point,
)
from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, t
from ..model import line_edit
from ..model import parts as parts_model
from ..model.document import ReplaceMesh, ReplaceObjects, SketchObject
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Tool

MIN_OFFSET = 0.001
LINE_PX = 8                 # (0.373) the mouse this near a loose line on the screen: it is what is offset


def _fmt(value):
    return format_length(value, decimal_sep())


def offset_ring(points2, distance):
    """A face's outline (2D) offset `distance` inwards (outwards if negative), its corners kept sharp — or None."""
    from shapely.geometry import Polygon
    poly = Polygon(points2)
    if not poly.is_valid or poly.area <= 0:
        return None
    grown = poly.buffer(-float(distance), join_style=2, mitre_limit=10.0)
    if grown.is_empty or grown.geom_type != "Polygon":
        return None
    ring = list(grown.exterior.coords)[:-1]
    return ring if len(ring) >= 3 else None


@dataclass
class _Lines:
    """(0.373) Loose lines being offset: their plane's frame (world) and, per sketch, its paths in that plane."""
    origin: np.ndarray
    u: np.ndarray
    v: np.ndarray
    normal: np.ndarray
    items: list                 # [(obj_id, [(2D points, closed)], its curve or None)]


def _side(path2, closed, q):
    """+1 when q is left of the path (inside a closed one running counter-clockwise), else -1; and how far."""
    from shapely.geometry import LineString, Point, Polygon
    pt = Point(float(q[0]), float(q[1]))
    line = LineString(path2)
    d = float(line.distance(pt))
    if closed:
        poly = Polygon(path2)
        inside = poly.contains(pt)
        return (1.0 if inside == poly.exterior.is_ccw else -1.0), d
    best, sign = None, 1.0
    for a, b in zip(path2, path2[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        ab = b - a
        s = np.clip(float((np.asarray(q) - a) @ ab) / max(float(ab @ ab), 1e-30), 0.0, 1.0)
        dist = float(np.linalg.norm(np.asarray(q) - (a + ab * s)))
        if best is None or dist < best - 1e-12:
            cross = ab[0] * (q[1] - a[1]) - ab[1] * (q[0] - a[0])
            best, sign = dist, (1.0 if cross >= 0 else -1.0)
    return sign, d


class OffsetTool(Tool):
    name = "offset"
    accepts_typing = True

    def __init__(self, host):
        super().__init__(host)
        self._face = None          # (obj_id, face index, origin, u, v, normal (world), outline 2D)
        self._lines = None         # (0.373) _Lines being offset
        self._q = None             # (0.373) where the mouse is on their plane (2D): the side of each path
        self._distance = 0.0
        self._last = None

    def hint(self):
        return t("hint.offset.distance") if self._face or self._lines else t("hint.offset.face")

    def vcb_title(self):
        return t("vcb.distance")

    def activate(self):
        super().activate()
        picked = self._picked_lines()             # (0.373) lines picked before: offset them at once
        if picked:
            self._start_lines(picked)

    def _pick(self, x, y):
        """The sketch face under (x, y): (obj, face index), or None."""
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None
        obj = self.doc.get(hit[0])
        if obj is None or obj.is_bim or hit[1] is None:
            return None
        return obj, int(hit[1])

    def _frame(self, obj, fi):
        """(origin, u, v, normal) of the face in world, and its outline in that 2D frame."""
        origin, u, v, n = _face_frame(obj.mesh, fi)
        m = obj.matrix
        o = transform_point(m, origin)
        uw, vw = m[:3, :3] @ u, m[:3, :3] @ v
        nw = np.cross(uw, vw)
        nw = nw / np.linalg.norm(nw)
        pts = [transform_point(m, obj.mesh.verts[i]) - o for i in obj.mesh.faces[fi]]
        outline = [(float(p @ uw), float(p @ vw)) for p in pts]
        return o, uw, vw, nw, outline

    # ------------------------------------------------------------ lines (0.373)

    def _picked_lines(self):
        """The loose lines picked before: {obj_id: line indices} — those picked alone, and the lines-only sketches
        selected — or {}."""
        out = {k: set(v) for k, v in self.viewport.line_selection.items()}
        for i in self.viewport.selection:
            obj = self.doc.get(i)
            if line_edit.is_lines(obj):
                out[i] = set(range(len(obj.mesh.lines)))
        return {k: v for k, v in out.items() if v}

    def _hovered_lines(self, x, y):
        """The chain of the loose line under the mouse (a curve: all of it): {obj_id: line indices}, or {}."""
        hit = self.viewport.line_at(x, y, radius_px=LINE_PX)
        if hit is None:
            return {}
        obj = self.doc.get(hit[0])
        if obj.curve:
            return {obj.id: set(range(len(obj.mesh.lines)))}
        return {obj.id: set(parts_model.joined_lines(obj.mesh, hit[1]))}

    def _source(self, lines):
        """_Lines for {obj_id: line indices}, or None (they are not on one plane)."""
        pieces, points = [], []
        for obj_id, ks in lines.items():
            obj = self.doc.get(obj_id)
            if not line_edit.is_lines(obj):
                continue
            world = [transform_point(obj.matrix, p) for p in obj.mesh.verts]
            chains = [[world[i] for i in path] for path in paths([obj.mesh.lines[k] for k in sorted(ks)])]
            pieces.append((obj, chains))
            points += [p for c in chains for p in c]
        if not points:
            return None
        plane = plane_of(points, self.viewport.view_direction())
        if plane is None:
            return None
        origin, normal = plane
        u, v = plane_axes(normal)
        items = []
        for obj, chains in pieces:
            flat = []
            for c in chains:
                closed = len(c) > 3 and np.linalg.norm(c[0] - c[-1]) < line_edit.TOL
                flat.append(([(float((p - origin) @ u), float((p - origin) @ v)) for p in c], closed))
            items.append((obj.id, flat, obj.curve))
        return _Lines(origin, u, v, normal, items)

    def _start_lines(self, lines):
        source = self._source(lines)
        if source is None:
            self.host.message(t("err.offset_lines_plane"), warning=True)
            return False
        self._lines, self._face, self._q = source, None, None
        self._show_source()
        self.host.set_hint(self.hint())
        return True

    def _to3(self, a, b):
        s = self._lines
        return s.origin + s.u * a + s.v * b

    def _show_source(self, extra=()):
        segs = []
        for _id, flat, _curve in self._lines.items:
            for path2, _closed in flat:
                pts = [self._to3(*p) for p in path2]
                segs += [q for a, b in zip(pts, pts[1:]) for q in (a, b)]
        segs += list(extra)
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))

    def _lines_offset(self, distance, q=None):
        """The paths offset `distance` towards q (each to the side q is of it): [(obj_id, [3D paths], curve)]."""
        q = self._q if q is None else q
        out = []
        for obj_id, flat, curve in self._lines.items:
            made = []
            arc = curve if curve and curve.get("kind") == "arc" and not curve.get("pie") else None
            for path2, closed in flat:
                sign = _side(path2, closed, q)[0] if q is not None else 1.0
                for p2 in offset_path(path2, sign * abs(distance), closed):
                    made.append([self._to3(*p) for p in p2])
            if arc is not None and made:            # an arc's: the arc about the same centre (not a polygon's)
                obj = self.doc.get(obj_id)
                local = core_curves.transform_curve(arc, obj.matrix)
                centre, r = np.asarray(local["centre"], float), core_curves.arc_radius(local)
                into = q is not None and np.linalg.norm(self._flat(centre) - np.asarray(q)) < r
                radius = r - abs(distance) if into else r + abs(distance)
                if radius <= MIN_OFFSET:
                    made = []
                else:
                    arc = core_curves.arc_with(local, radius=radius)
                    made = [core_curves.arc_points(arc["centre"], arc["normal"], arc["start"], arc["angle"],
                                                   arc.get("segments"))]
            out.append((obj_id, made, arc if arc is not None else ({"kind": "curve"} if curve else None)))
        return out

    def _flat(self, p):
        s = self._lines
        return np.array((float((p - s.origin) @ s.u), float((p - s.origin) @ s.v)))

    def _show_lines(self):
        segs = []
        for _id, made, _curve in self._lines_offset(self._distance):
            for pts in made:
                segs += [q for a, b in zip(pts, pts[1:]) for q in (a, b)]
        self._show_source(segs)
        self.host.set_vcb(_fmt(abs(self._distance)))

    def _apply_lines(self, distance):
        if abs(distance) < MIN_OFFSET or self._lines is None:
            return
        made = []
        for _obj_id, paths3, curve in self._lines_offset(distance):
            verts, pairs = [], []
            for pts in paths3:
                ids = []
                for p in pts:
                    k = next((i for i, w in enumerate(verts) if np.linalg.norm(w - p) < line_edit.TOL), None)
                    if k is None:
                        verts.append(np.asarray(p, dtype=float))
                        k = len(verts) - 1
                    ids.append(k)
                pairs += [(a, b) for a, b in zip(ids, ids[1:]) if a != b]
            if pairs:
                made.append(SketchObject(t("obj.lines", n=self.doc.next_number()), np.eye(4),
                                         PolyMesh(verts, lines=pairs), curve=curve))
        if not made:
            self.host.message(t("err.offset_too_far"), warning=True)
            return
        source, q = self._lines, self._q
        cmd = self.doc.execute(ReplaceObjects([], made, t("cmd.offset")))
        self._last = (cmd, ("lines", source, q), distance)
        self.viewport.clear_overlays()
        self._lines = self._q = None
        self.viewport.set_selection({o.id for o in made})
        self.host.set_hint(self.hint())
        self.host.message(t("info.offset_lines", d=_fmt(abs(distance))))

    # ------------------------------------------------------------ mouse

    def pointer_move(self, x, y, modifiers):
        if self._lines is not None:
            s = self._lines
            origin, direction = self.viewport.ray(x, y)
            p = ray_plane(origin, direction, s.origin, s.normal)
            if p is None:
                p = ray_plane(origin, direction, s.origin, -s.normal)
            if p is None:
                return
            self._q = self._flat(p)
            near = [_side(path2, closed, self._q)[1] for _id, flat, _c in s.items for path2, closed in flat]
            self._distance = min(near) if near else 0.0
            self._show_lines()
            return
        if self._face is None:
            hovered = self._hovered_lines(x, y)
            if hovered:                               # (0.373) a loose line: its chain shown
                source = self._source(hovered)
                if source is not None:
                    self._lines, saved = source, self._lines
                    self._show_source()
                    self._lines = saved
                    return
            found = self._pick(x, y)
            if found is None:
                self.viewport.clear_overlays()
                return
            obj, fi = found
            o, u, v, _n, outline = self._frame(obj, fi)
            ring = [o + u * a + v * b for a, b in outline]
            segs = [q for a, b in zip(ring, ring[1:] + ring[:1]) for q in (a, b)]
            self.viewport.show_polygon(ring, segments=segs, colors=[PREVIEW] * len(segs))
            return
        _id, _fi, o, u, v, n, outline = self._face
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, o, n)
        if p is None:
            p = ray_plane(origin, direction, o, -n)
        if p is None:
            return
        from shapely.geometry import Point, Polygon
        q = Point(float((p - o) @ u), float((p - o) @ v))
        poly = Polygon(outline)
        d = poly.exterior.distance(q)
        self._distance = float(d if poly.contains(q) else -d)
        self._show()

    def _show(self):
        _id, _fi, o, u, v, _n, outline = self._face
        ring = offset_ring(outline, self._distance)
        if ring is None:
            self.viewport.clear_overlays()
            return
        pts = [o + u * a + v * b for a, b in ring]
        segs = [q for a, b in zip(pts, pts[1:] + pts[:1]) for q in (a, b)]
        self.viewport.show_polygon(pts, segments=segs, colors=[PREVIEW] * len(segs))
        self.host.set_vcb(_fmt(abs(self._distance)))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self._lines is not None:
            if self._q is not None:
                self._apply_lines(self._distance)
            return
        if self._face is None:
            hovered = self._hovered_lines(x, y)
            if hovered:                               # (0.373) a loose line: its chain offset
                self._start_lines(hovered)
                return
            found = self._pick(x, y)
            if found is None:
                self.host.message(t("err.offset_face"), warning=True)
                return
            obj, fi = found
            self._face = (obj.id, fi) + self._frame(obj, fi)
            self.host.set_hint(self.hint())
            return
        self._apply(self._distance)

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None or values[0] is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        value = float(values[0])
        if self._lines is not None:
            self._apply_lines(abs(value))
            return
        if self._face is not None:
            sign = -1.0 if self._distance < 0 else 1.0
            self._apply(sign * abs(value))
            return
        last = self._last
        if last is not None and self.doc.last_command() is last[0]:
            self.doc.undo()                       # (a value typed right after corrects the last offset)
            if isinstance(last[1], tuple) and last[1][0] == "lines":
                self._lines, self._q = last[1][1], last[1][2]
                self._apply_lines(abs(value))
                return
            self._face = last[1]
            sign = -1.0 if last[2] < 0 else 1.0
            self._apply(sign * abs(value))
            return
        self.host.message(t("hint.offset.face"), warning=True)

    def cancel(self):
        self._face = None
        self._lines = self._q = None
        self._distance = 0.0
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    def _apply(self, distance):
        if abs(distance) < MIN_OFFSET or self._face is None:
            return
        face = self._face
        obj_id, fi, o, u, v, _n, outline = face
        obj = self.doc.get(obj_id)
        ring = offset_ring(outline, distance)
        if obj is None or ring is None:
            self.host.message(t("err.offset_too_far"), warning=True)
            return
        to_local = np.linalg.inv(obj.matrix)
        local = [transform_point(to_local, o + u * a + v * b) for a, b in ring]
        mesh = obj.mesh.copy()
        if distance > 0:                          # inside: the face divided along it
            if imprint_polygon(mesh, fi, local) is None:
                self.host.message(t("err.offset_convex"), warning=True)
                return
        else:                                     # outside: a lone face grows, its old outline inside it
            if len(mesh.faces) != 1:
                self.host.message(t("err.offset_outside"), warning=True)
                return
            old = [mesh.verts[i] for i in mesh.faces[0]]
            n_local = mesh.face_normal(0)
            pu, pv = _face_frame(mesh, 0)[1:3]
            base = old[0]
            grown = polygon_mesh([((p - base) @ pu, (p - base) @ pv) for p in local])
            grown.verts = [base + pu * q[0] + pv * q[1] for q in grown.verts]
            if np.dot(grown.face_normal(0), n_local) < 0:
                grown.flip_face(0)
            if imprint_polygon(grown, 0, old) is None:
                self.host.message(t("err.offset_convex"), warning=True)
                return
            mesh = grown
        cmd = self.doc.execute(ReplaceMesh(obj.id, obj.mesh, mesh, t("cmd.offset")))
        self._last = (cmd, face, distance)
        self.viewport.clear_overlays()
        self._face = None
        self.host.set_hint(self.hint())
        self.host.message(t("info.offset", d=_fmt(abs(distance)),
                            w=t("offset.inside") if distance > 0 else t("offset.outside")))
