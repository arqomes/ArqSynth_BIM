"""Core tests (no window, no GPU):  .venv\\Scripts\\python -m unittest discover -s tests"""

import dataclasses
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# the geometry cache of the files the tests save goes to a temporary folder, not the user's
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))

from arqbim import i18n  # noqa: E402
from arqbim.core import inference as inf  # noqa: E402
from arqbim.core import lines, tracking, transform, walls  # noqa: E402
from arqbim.core.units import format_angle, parse_angle, parse_array  # noqa: E402
from arqbim.core import sketch_geometry as sg  # noqa: E402
from arqbim.core.mesh import PolyMesh, TriMesh  # noqa: E402
from arqbim.core.units import format_length, parse_length, parse_lengths  # noqa: E402
from arqbim.model.document import AddObject, Document, ReplaceMesh, SketchObject  # noqa: E402

I4 = np.eye(4)


def rot_z(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    m = np.eye(4)
    m[:2, :2] = [[c, -s], [s, c]]
    return m


def translate(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def face_with_normal(mesh, matrix, normal):
    for fi in range(len(mesh.faces)):
        if np.linalg.norm(sg.face_world_normal(matrix, mesh, fi) - np.array(normal)) < 1e-6:
            return fi
    raise AssertionError("no face with normal {}".format(normal))


def z_range(mesh, matrix=I4):
    zs = [sg.transform_point(matrix, v)[2] for v in mesh.verts]
    return min(zs), max(zs)


class Units(unittest.TestCase):
    def test_single_values(self):
        for text, value in [("3,20", 3.2), ("3.20", 3.2), ("320cm", 3.2), ("3200mm", 3.2),
                            ("3.2m", 3.2), ("-0,5", -0.5), (",5", 0.5)]:
            self.assertAlmostEqual(parse_length(text), value, msg=text)
        for bad in ("", "abc", "3,2,1", "--1", "3cmm", "m"):
            self.assertIsNone(parse_length(bad), bad)

    def test_sums(self):
        """0.430: a sum typed in a length's field is worked out (each number in its unit or the display one)."""
        for text, value in [("3,50+0,15", 3.65), ("2*1,20", 2.4), ("2×1,20", 2.4), ("(4-0,2)/2", 1.9),
                            ("3m+15cm", 3.15), ("1,20 + 0,05", 1.25), ("-0,5+1", 0.5), ("10÷4", 2.5)]:
            self.assertAlmostEqual(parse_length(text), value, msg=text)
        for bad in ("3+", "(1+2", "1/0", "2**3", "1+a", "import os"):
            self.assertIsNone(parse_length(bad), bad)
        from arqbim.core import units
        try:
            units.set_display_unit("cm")
            self.assertAlmostEqual(parse_length("300+15"), 3.15)
            self.assertAlmostEqual(parse_length("2*120"), 2.4)
            self.assertAlmostEqual(parse_length("3m+15"), 3.15)
        finally:
            units.set_display_unit("m")

    def test_pairs(self):
        self.assertEqual(parse_lengths("3,20;4,50", 2), [3.2, 4.5])
        self.assertEqual(parse_lengths("3.2x4.5", 2), [3.2, 4.5])
        self.assertEqual(parse_lengths("3.2,4.5", 2), [3.2, 4.5])
        self.assertEqual(parse_lengths(";4,5", 2), [None, 4.5])
        self.assertEqual(parse_lengths("3,2", 2), [3.2, None])
        self.assertIsNone(parse_lengths("1;2;3", 2))
        self.assertIsNone(parse_lengths(";", 2))
        self.assertEqual(parse_lengths("2,80", 1), [2.8])

    def test_format(self):
        self.assertEqual(format_length(3.2), "3,20 m")
        self.assertEqual(format_length(2.8 + 1.0), "3,80 m")
        self.assertEqual(format_length(3.4871), "~ 3,49 m")
        self.assertEqual(format_length(-0.5), "-0,50 m")
        self.assertEqual(format_length(-0.0001), "~ 0,00 m")
        self.assertEqual(format_length(3.2, "."), "3.20 m")

    def test_display_unit(self):
        """0.186: the footer's Units — lengths shown in cm (a decimal fewer: to the mm) or mm (whole), a bare
        number read in that unit (one with its unit as written); m back as before; levels and schedules ask m."""
        from arqbim.core import units
        try:
            units.set_display_unit("cm")
            self.assertEqual(format_length(3.2), "320,0 cm")
            self.assertEqual(format_length(0.125), "12,5 cm")
            self.assertEqual(format_length(0.12345), "~ 12,3 cm")
            self.assertAlmostEqual(parse_length("320"), 3.2)
            self.assertAlmostEqual(parse_length("3,2m"), 3.2)
            self.assertAlmostEqual(parse_length("12,5"), 0.125)
            self.assertEqual(parse_lengths("320;450", 2), [3.2, 4.5])
            self.assertEqual(format_length(3.2, unit="m"), "3,20 m")
            self.assertAlmostEqual(parse_length("3", unit="m"), 3.0)
            units.set_display_unit("mm")
            self.assertEqual(format_length(3.2), "3200 mm")
            self.assertEqual(format_length(0.01234), "~ 12 mm")
            self.assertAlmostEqual(parse_length("3200"), 3.2)
            self.assertEqual(format_length(-0.0001), "~ 0 mm")
            units.set_display_unit("ft")                           # (not one of ours: metres)
            self.assertEqual(units.display_unit(), "m")
        finally:
            units.set_display_unit("m")
        self.assertEqual(format_length(3.2), "3,20 m")
        self.assertAlmostEqual(parse_length("3,2"), 3.2)
        from arqbim.model import schedules
        units.set_display_unit("mm")
        try:
            self.assertEqual(schedules.text_of("length", 4.5), "4,50 m")
        finally:
            units.set_display_unit("m")

    def test_i18n_strings_format_in_both_languages(self):
        import string
        for key, (pt, en) in i18n._STRINGS.items():
            fields_pt = {f for _, f, _, _ in string.Formatter().parse(pt) if f}
            fields_en = {f for _, f, _, _ in string.Formatter().parse(en) if f}
            self.assertEqual(fields_pt, fields_en, key)               # same placeholders in both languages
            for s in (pt, en):
                s.format(**{f: "x" for f in fields_pt})


class CurvedCorners(unittest.TestCase):
    """0.189: corners with curved walls — the exact mitre: the cut line through the meeting points of the inner faces
    and of the outer faces; each wall's body ends on it (the straight one's footprint, the curved one's faces), so
    their corners are the same points: no gap, no overlap. An arc going on along the straight wall's line is not
    joined (it meets it squarely)."""

    def test_straight_and_arc(self):
        from arqbim.core import curved_joints as cj
        from arqbim.core.walls import cut_angle, footprint
        t = 0.2
        straight = cj.straight_end((4.0, 0.0, 0.0), (-1.0, 0.0, 0.0), t)          # the wall (0,0) -> (4,0), its end
        arc = cj.arc_end((6.0, 0.0), 2.0, math.pi, 1, t)                           # from (4,0), down (counter-clockwise)
        result = cj.corner(straight, arc)
        self.assertIsNotNone(result)
        (p_s, n_s), (p_a, n_a) = result
        q_in = np.array((6.0 - math.sqrt(2.1 ** 2 - 0.01), -0.1))                  # the inner faces meet
        q_out = np.array((6.0 - math.sqrt(1.9 ** 2 - 0.01), 0.1))                  # the outer faces meet
        self.assertAlmostEqual(p_s[1], 0.0)
        self.assertAlmostEqual(p_s[0], (q_in[0] + q_out[0]) / 2, places=9)
        # the straight wall's footprint, its end cut so: its end corners are those two points
        length = float(p_s[0])
        pts = footprint(length, t, 180.0, cut_angle(n_s, np.array((1.0, 0.0, 0.0))))
        ends = sorted([pts[1], pts[2]], key=lambda q: q[1])
        self.assertTrue(np.allclose(ends[0], q_in, atol=1e-9) and np.allclose(ends[1], q_out, atol=1e-9), ends)
        # the curved wall's faces end at the same two points
        angle = math.atan2(p_a[1], p_a[0] - 6.0)
        sweep = math.pi / 2                                                         # (from there, a quarter round)
        cut = cj.arc_cut(angle, sweep, n_a)
        (o0, i0), _end = cj.cut_ends(2.0, sweep, t, start_cut=cut)
        outer = np.array((6.0 + 2.1 * math.cos(angle + o0), 2.1 * math.sin(angle + o0)))
        inner = np.array((6.0 + 1.9 * math.cos(angle + i0), 1.9 * math.sin(angle + i0)))
        self.assertTrue(np.allclose(outer, q_in, atol=1e-9), (outer, q_in))
        self.assertTrue(np.allclose(inner, q_out, atol=1e-9), (inner, q_out))
        band = cj.cut_band((6.0, 0.0), 2.0, angle, sweep, t, start_cut=cut)[0]
        self.assertTrue(np.allclose(band[0], q_in, atol=1e-9) and np.allclose(band[-1], q_out, atol=1e-9))
        self.assertEqual(cj.cut_ends(2.0, 1.0, t), ((0.0, 0.0), (1.0, 1.0)))       # (square ends: as before)

    def test_in_line_and_two_arcs(self):
        from arqbim.core import curved_joints as cj
        straight = cj.straight_end((4.0, 0.0, 0.0), (-1.0, 0.0, 0.0), 0.2)
        tangent = cj.arc_end((4.0, 2.0), 2.0, -math.pi / 2, 1, 0.2)              # on along its line: not joined
        self.assertIsNone(cj.corner(straight, tangent))
        a = cj.arc_end((0.0, 0.0), 3.0, 0.0, 1, 0.2)                               # (3,0), going up
        b = cj.arc_end((5.0, 0.0), 2.0, math.pi, -1, 0.25)                         # (3,0), going up too, the other way
        self.assertIsNone(cj.corner(a, b))                                         # (tangent there: in line)
        b = cj.arc_end((3.0, -2.0), 2.0, math.pi / 2, -1, 0.25)                    # (3,0), going right and down
        result = cj.corner(a, b)
        self.assertIsNotNone(result)
        (pa, na), (pb, nb) = result
        self.assertAlmostEqual(float(np.linalg.norm(pa[:2])), 3.0, places=9)       # still on each axis
        self.assertAlmostEqual(float(np.linalg.norm(pb[:2] - (3.0, -2.0))), 2.0, places=9)
        self.assertTrue(np.allclose(na, -nb))                                     # one cut line, seen from each side


class PlatformBatters(unittest.TestCase):
    """0.203: a 4 × 4 platform at 0 on a ground rising to the east (z = x / 10): its cut's crest to the east where
    the ground meets the 1:1 slope (2,22), its fill's toe to the west where it meets the 2:3 one (−2,35); the ticks
    from each slope's top, one long, one short; on a flat ground at its height, nothing."""

    def ground(self, f):
        return [(x, y, f(x, y)) for x in np.linspace(-10, 10, 21) for y in np.linspace(-10, 10, 21)]

    def test_cut_and_fill(self):
        from arqbim.core import earthworks
        plat = earthworks.Platform([(-2.0, -2.0), (2.0, -2.0), (2.0, 2.0), (-2.0, 2.0)], 0.0)
        lines, ticks = earthworks.batters(self.ground(lambda x, y: x / 10.0), plat)
        self.assertTrue(len(lines) and len(ticks))
        mid = lines[np.abs(lines[:, :, 1]).max(axis=1) < 1.5]           # (across the east and west sides)
        east = mid[mid[:, :, 0].min(axis=1) > 0]
        west = mid[mid[:, :, 0].max(axis=1) < 0]
        self.assertTrue(len(east) and len(west))
        np.testing.assert_allclose(east[:, :, 0], 2.0 + 0.2 / 0.9, atol=0.02)
        np.testing.assert_allclose(west[:, :, 0], -2.0 - 0.2 / (2.0 / 3.0 - 0.1), atol=0.02)
        np.testing.assert_allclose(east[:, :, 2], east[:, :, 0] / 10.0, atol=1e-6)        # (at the ground's height)
        side = ticks[(np.abs(ticks[:, :, 1]).max(axis=1) < 1.9) & (ticks[:, :, 0].min(axis=1) > 1.9)]
        lengths = np.round(np.linalg.norm(side[:, 1, :2] - side[:, 0, :2], axis=1), 3)
        self.assertEqual(sorted(set(lengths)), [round(0.2 / 0.9 / 2, 3), round(0.2 / 0.9, 3)])  # (long, short)
        np.testing.assert_allclose(side[:, 0, 0], 2.0 + 0.2 / 0.9, atol=0.01)              # (from the crest)
        west_ticks = ticks[ticks[:, :, 0].max(axis=1) < -1.9]
        np.testing.assert_allclose(west_ticks[:, 0, 0], -2.0, atol=1e-6)                   # (from the edge)
        flat = earthworks.batters(self.ground(lambda x, y: 0.0), plat)
        self.assertEqual((len(flat[0]), len(flat[1])), (0, 0))


class TerrainRamps(unittest.TestCase):
    """0.205: a ramp 10 m long and 3 m wide on a flat ground, from 0 to 1 m: its outline; its height along it; the
    proposed ground on it and on its fill's 2:3 slopes beside it; its toe lines and ticks; kept and read back."""

    def test_ramp(self):
        from arqbim.core import earthworks, terrain
        outline = earthworks.ramp_outline((0.0, 0.0), (10.0, 0.0), 3.0)
        np.testing.assert_allclose(outline, [(0, -1.5), (10, -1.5), (10, 1.5), (0, 1.5)], atol=1e-12)
        self.assertIsNone(earthworks.ramp_outline((1.0, 1.0), (1.0, 1.0), 3.0))
        ramp = earthworks.Platform(outline, 0.0, axis=[(0.0, 0.0), (10.0, 0.0)], z_end=1.0)
        self.assertTrue(ramp.is_ramp())
        np.testing.assert_allclose(ramp.heights([(0, 0), (5, 1), (10, -1), (12, 0)]), (0.0, 0.5, 1.0, 1.0))
        self.assertAlmostEqual(ramp.slope(), 0.1)
        self.assertEqual(ramp.low_high(), (0.0, 1.0))
        again = earthworks.Platform.from_dict(ramp.to_dict())
        self.assertEqual((again.axis, again.z_end), ([(0.0, 0.0), (10.0, 0.0)], 1.0))
        flat = earthworks.Platform.from_dict(earthworks.Platform(outline, 2.0).to_dict())
        self.assertFalse(flat.is_ramp())
        ground = [(x, y, 0.0) for x in np.linspace(-10, 20, 31) for y in np.linspace(-10, 10, 21)]
        verts, tris = terrain.tin(earthworks.proposed(ground, [ramp]))
        self.assertAlmostEqual(terrain.height_at(verts, tris, (5.0, 0.0)), 0.5, places=6)
        self.assertAlmostEqual(terrain.height_at(verts, tris, (5.0, 1.4)), 0.5, places=6)
        self.assertAlmostEqual(terrain.height_at(verts, tris, (5.0, 2.0)), 0.5 - 0.5 * 2.0 / 3.0, delta=0.02)
        self.assertAlmostEqual(terrain.height_at(verts, tris, (5.0, 3.0)), 0.0, places=6)
        lines, ticks = earthworks.batters(ground, ramp)
        side = lines[(lines[:, :, 0].min(axis=1) > 3.0) & (lines[:, :, 0].max(axis=1) < 7.0) & (lines[:, :, 1].min(axis=1) > 0)]
        self.assertTrue(len(side))
        np.testing.assert_allclose(side[:, :, 1], 1.5 + side[:, :, 0] / 10.0 / (2.0 / 3.0), atol=0.03)  # (its toe)
        self.assertTrue(len(ticks))


class ContourLabels(unittest.TestCase):
    """0.202: a major contour line's height written along it — its text; its segments, in no order, joined into
    one polyline (closed round a hill); its labels spread along it, turned to be read, none on a short piece."""

    def test_text(self):
        from arqbim.core import terrain
        self.assertEqual([terrain.contour_text(h) for h in (12.0, 12.5, -3.25, 0.0, -0.001)],
                         ["12", "12,5", "-3,25", "0", "0"])
        self.assertEqual(terrain.contour_text(7.5, "."), "7.5")

    def test_chains_and_spots(self):
        from arqbim.core import terrain
        # a hill: z = 10 - r, its contour at 5 is a circle of radius 5, cut in triangles shuffled
        verts = [(0.0, 0.0, 10.0)] + [(10 * np.cos(a), 10 * np.sin(a), 0.0) for a in np.linspace(0, 2 * np.pi, 25)[:-1]]
        tris = [(0, 1 + k, 1 + (k + 1) % 24) for k in range(24)]
        found = terrain.contours(np.array(verts), np.array(tris), interval=5.0)
        segs = dict(found)[5.0]
        rng = np.random.default_rng(1)
        segs = segs[rng.permutation(len(segs))]
        lines = terrain.chains(segs)
        self.assertEqual(len(lines), 1)
        self.assertEqual(len(lines[0]), len(segs) + 1)
        np.testing.assert_allclose(lines[0][0], lines[0][-1], atol=1e-6)            # (closed)
        spots = terrain.label_spots(lines[0], every=10.0, shortest=1.0)              # (about 31 m round: 3)
        self.assertEqual(len(spots), 3)
        for point, angle in spots:
            self.assertAlmostEqual(float(np.hypot(*point)), 5.0, delta=0.15)          # (on it)
            self.assertTrue(-90.0 < angle <= 90.0)
        self.assertEqual(terrain.label_spots(np.array(((0.0, 0.0), (0.5, 0.0))), 10.0, 1.0), [])
        (point, angle), = terrain.label_spots(np.array(((0.0, 0.0), (0.0, -4.0))), 10.0, 1.0)
        np.testing.assert_allclose(point, (0.0, -2.0))
        self.assertAlmostEqual(angle, 90.0)                                        # (going down: read upward)
        (_p, angle), = terrain.label_spots(np.array(((4.0, 0.0), (0.0, 0.0))), 10.0, 1.0)
        self.assertAlmostEqual(angle, 0.0)                                         # (leftward: read left to right)


class BranchRouting(unittest.TestCase):
    """0.199: a branch's way in plan round the columns on its line — free: straight; one column: round it with
    square turns, its sides clear, the last run along the line (a tee square to the main); runs too short for their
    bends refused; no way round, or a far longer one: None."""

    @staticmethod
    def square(cx, cy, half):
        return np.array(((cx - half, cy - half), (cx + half, cy - half), (cx + half, cy + half), (cx - half, cy + half)))

    def runs_clear(self, way, boxes):
        from arqbim.core import routing
        for p, q in zip(way, way[1:]):
            self.assertFalse(routing.blocked(p, q, boxes), (p, q))
            d = np.asarray(q) - np.asarray(p)
            self.assertTrue(abs(d[0]) < 1e-9 or abs(d[1]) < 1e-9, d)        # (square turns: along x or along y)

    def test_round_a_column(self):
        from arqbim.core import routing
        a, b = np.array((0.0, 0.0)), np.array((0.0, 3.0))
        self.assertEqual(len(routing.route(a, b, [self.square(2.0, 1.5, 0.2)])), 2)          # (off the line)
        col = [self.square(0.0, 1.5, 0.2)]
        self.assertTrue(routing.blocked(a, b, col))
        way = routing.route(a, b, col, min_run=0.1)
        self.runs_clear(way, col)
        np.testing.assert_allclose(way[0], a)
        np.testing.assert_allclose(way[-1], b)
        self.assertAlmostEqual(abs(float(way[-2][0] - way[-1][0])), 0.0)                      # (the last run along)
        self.assertEqual(len(way), 5)                                       # (out, past it, back: 4 runs)
        self.assertAlmostEqual(sum(float(np.linalg.norm(q - p)) for p, q in zip(way, way[1:])), 3.0 + 0.4)
        first = routing.route(a, b, col, min_run=0.1, first_along=True)
        self.assertAlmostEqual(abs(float(first[1][0] - a[0])), 0.0)                           # (the first run along)
        self.runs_clear(first, col)
        free_end = routing.route(a, b, col, min_run=0.1, last_along=False)
        self.assertEqual(len(free_end), 4)                                  # (out, past, back to it: 3 runs)
        self.runs_clear(free_end, col)

    def test_refused(self):
        from arqbim.core import routing
        a, b = np.array((0.0, 0.0)), np.array((3.0, 0.0))
        col = [self.square(1.5, 0.0, 0.2)]
        self.assertIsNone(routing.route(a, b, col, min_run=2.0))                              # (no room for bends)
        wall = [np.array(((1.4, -5.0), (1.6, -5.0), (1.6, 5.0), (1.4, 5.0)))]
        self.assertIsNone(routing.route(a, b, wall))                                          # (10 m round: no)
        two = [self.square(1.0, 0.0, 0.2), self.square(2.0, 0.1, 0.2)]
        way = routing.route(a, b, two, min_run=0.1)
        self.runs_clear(way, two)
        inside = [self.square(0.0, 0.0, 0.2)]                               # (a box its start is in: not counted)
        self.assertEqual(len(routing.route(a, b, inside)), 2)


class StraightSkeleton(unittest.TestCase):
    """0.190: the straight skeleton — one face per side, the roof whole (every corner as high from each face it is
    on), over rectangles, an L, a T, a U, a cross, a star, outlines at any angle; over a convex outline the same faces
    as before; a hip roof (core/roofs) over an L with slanted sides, its height along it; rejected only where it
    could not be worked out (and then the roof is refused)."""

    SHAPES = {
        "rect": [(0, 0), (8, 0), (8, 5), (0, 5)],
        "L": [(0, 0), (10, 0), (10, 4), (4, 4), (4, 9), (0, 9)],
        "T": [(0, 0), (12, 0), (12, 4), (8, 4), (8, 10), (4, 10), (4, 4), (0, 4)],
        "plus": [(4, 0), (8, 0), (8, 4), (12, 4), (12, 8), (8, 8), (8, 12), (4, 12), (4, 8), (0, 8), (0, 4), (4, 4)],
        "oblique": [(0, 0), (9, 1), (11, 6), (6, 5), (4, 10), (-1, 7)],
        "star": [(math.cos(k * math.pi / 5) * (5 if k % 2 == 0 else 2.2),
                  math.sin(k * math.pi / 5) * (5 if k % 2 == 0 else 2.2)) for k in range(10)],
        "Lslant": [(0, 0), (10, 0), (10, 4), (5, 5), (3, 10), (0, 9)],
    }

    def test_faces(self):
        from shapely.geometry import Polygon
        from arqbim.core.skeleton import roof_faces
        for name, pts in self.SHAPES.items():
            faces = roof_faces(pts)
            self.assertIsNotNone(faces, name)
            self.assertEqual(len(faces), len(pts), name)
            self.assertAlmostEqual(sum(Polygon(f).area for _s, f in faces), Polygon(pts).area, places=6, msg=name)
            heights = {}
            for (a, _b, _e, n), face in faces:
                for p in face:
                    heights.setdefault((round(p[0], 4), round(p[1], 4)), []).append(float(np.dot(n, np.asarray(p) - a)))
            self.assertTrue(all(max(v) - min(v) < 1e-6 for v in heights.values()), name)
        rect = roof_faces(self.SHAPES["rect"])                 # (a rectangle: its ridge 2,5 up, 3 m long)
        top = max(max(float(np.dot(n, np.asarray(p) - a)) for p in f) for (a, _b, _e, n), f in rect)
        self.assertAlmostEqual(top, 2.5)

    def test_convex_as_before_and_roof(self):
        from shapely.geometry import Polygon
        from arqbim.core import roofs
        from arqbim.core.skeleton import roof_faces
        pent = [(0, 0), (6, -1), (9, 3), (5, 7), (-1, 5)]
        mine = sorted(round(Polygon(f).area, 6) for _s, f in roof_faces(pent))
        theirs = sorted(round(Polygon(f).area, 6) for _p, f in roofs.faces(pent, [True] * 5))
        self.assertEqual(mine, theirs)
        slanted = self.SHAPES["Lslant"]
        self.assertTrue(roofs.can_slope(Polygon(slanted), "hip"))
        self.assertFalse(roofs.can_slope(Polygon(slanted), "gable"))    # (a gable over it: still not)
        faces = roofs.faces(slanted, [True] * 6)
        self.assertEqual(len(faces), 6)
        # at 30°: on the wing's ridge, half its width up × tan 30°; at a corner, the eave
        self.assertAlmostEqual(roofs.height_at(slanted, [True] * 6, 30.0, 3.0, (0.0, 0.0)), 3.0)
        h = roofs.height_at(slanted, [True] * 6, 30.0, 3.0, (8.0, 2.0))
        self.assertAlmostEqual(h, 3.0 + 2.0 * math.tan(math.radians(30.0)), places=6)


class Rectangle(unittest.TestCase):
    def test_plane_axes_are_right_handed(self):
        for n in [(0, 0, 1), (0, 0, -1), (0, -1, 0), (1, 0, 0), (0.3, 0.2, 0.9), (0.7, -0.7, 0.1)]:
            n = sg.normalize(n)
            u, v = sg.plane_axes(n)
            self.assertAlmostEqual(np.linalg.norm(u), 1.0)
            self.assertAlmostEqual(u.dot(v), 0.0)
            self.assertTrue(np.allclose(np.cross(u, v), n))
        u, v = sg.plane_axes((0, -1, 0))  # wall facing -Y: U horizontal, V up
        self.assertTrue(np.allclose(u, (1, 0, 0)) and np.allclose(v, (0, 0, 1)))

    def test_normal_points_up_in_every_quadrant(self):
        for du, dv in [(3.2, 4.5), (-3.2, 4.5), (3.2, -4.5), (-3.2, -4.5)]:
            m = sg.rectangle_mesh(du, dv)
            self.assertTrue(np.allclose(m.face_normal(0), (0, 0, 1)), (du, dv))
            self.assertAlmostEqual(m.face_area(0), 14.4)


class Offsets(unittest.TestCase):
    """0.152: a face's outline offset — inside, a square smaller by twice the distance, its corners sharp; a circle
    keeps its sides; outside, it grows; too far inside, nothing."""

    def test_offsets(self):
        from arqbim.tools.offset import offset_ring
        inner = np.array(offset_ring([(0, 0), (2, 0), (2, 2), (0, 2)], 0.2))
        self.assertEqual(len(inner), 4)
        np.testing.assert_allclose(sorted(set(np.round(inner[:, 0], 6))), (0.2, 1.8))
        circle = [tuple(v[:2]) for v in sg.circle_mesh(1.0).verts]
        self.assertEqual(len(offset_ring(circle, 0.1)), 24)
        outer = np.array(offset_ring([(0, 0), (2, 0), (2, 2), (0, 2)], -0.5))
        np.testing.assert_allclose(outer.min(axis=0), (-0.5, -0.5))
        self.assertIsNone(offset_ring([(0, 0), (2, 0), (2, 2), (0, 2)], 1.5))

    def test_l_face(self):
        """0.206: an L face (4 × 3, a 2 × 1,5 corner taken away) offset 0,25 inside: divided in its inner L and a
        frame of six four-sided faces, the areas adding up, the connecting edges hidden; outside, the L grown with
        the old one inside it; an offset that closes the L's arm: refused, the mesh as it was."""
        from shapely.geometry import Polygon
        from arqbim.tools.offset import offset_ring
        ell = [(0, 0), (4, 0), (4, 1.5), (2, 1.5), (2, 3), (0, 3)]
        m = sg.polygon_mesh(ell)
        ring = offset_ring(ell, 0.25)
        self.assertEqual(len(ring), 6)
        inner = sg.imprint_polygon(m, 0, [np.array((x, y, 0.0)) for x, y in ring])
        self.assertIsNotNone(inner)
        self.assertEqual(len(m.faces), 7)
        areas = [Polygon([tuple(m.verts[i][:2]) for i in f]).area for f in m.faces]
        self.assertAlmostEqual(sum(areas), Polygon(ell).area)
        self.assertAlmostEqual(areas[inner], Polygon(ring).area)
        self.assertEqual(len(m.hidden), 6)
        normals = [m.face_normal(k)[2] for k in range(len(m.faces))]
        self.assertTrue(all(z > 0.99 for z in normals))                     # (all facing the same way)
        grown = sg.polygon_mesh(offset_ring(ell, -0.5))
        self.assertIsNotNone(sg.imprint_polygon(grown, 0, [np.array((x, y, 0.0)) for x, y in ell]))
        self.assertEqual(len(grown.faces), 7)
        thin = sg.polygon_mesh(ell)
        far = offset_ring(ell, 0.8)                                          # (the arm 1,5 wide closed: a rectangle)
        self.assertEqual(len(far), 4)
        self.assertIsNone(sg.imprint_polygon(thin, 0, [np.array((x, y, 0.0)) for x, y in far]))
        self.assertEqual(len(thin.faces), 1)


class Scaling(unittest.TestCase):
    """0.153: a sketch scaled about a base point — twice as big from its corner; per axis (taller only); its matrix
    kept, its holes scaled too."""

    def test_scale(self):
        from arqbim.tools.scale import scaled_copy
        m = sg.rectangle_mesh(2.0, 1.0)
        sg.push_pull(m, 0, I4, 1.0)
        mat = np.eye(4)
        mat[:3, 3] = (1.0, 1.0, 0.0)
        obj = SketchObject("Caixa", mat, m)
        big = scaled_copy(obj, (1.0, 1.0, 0.0), (2.0, 2.0, 2.0))
        self.assertEqual(big.id, obj.id)
        self.assertAlmostEqual(big.mesh.volume(), 2.0 * 8)
        np.testing.assert_allclose(big.matrix, mat)
        world = np.array([mat[:3, :3] @ v + mat[:3, 3] for v in big.mesh.verts])
        np.testing.assert_allclose(world.min(axis=0), (1.0, 1.0, 0.0))
        np.testing.assert_allclose(world.max(axis=0), (5.0, 3.0, 2.0))
        tall = scaled_copy(obj, (1.0, 1.0, 0.0), (1.0, 1.0, 3.0))
        self.assertAlmostEqual(tall.mesh.volume(), 2.0 * 3)
        # (0.206) about its middle (2, 1,5, 0,5): twice as big, its middle where it was
        middle = scaled_copy(obj, (2.0, 1.5, 0.5), (2.0, 2.0, 2.0))
        world = np.array([mat[:3, :3] @ v + mat[:3, 3] for v in middle.mesh.verts])
        np.testing.assert_allclose((world.min(axis=0) + world.max(axis=0)) / 2, (2.0, 1.5, 0.5))
        np.testing.assert_allclose(world.max(axis=0) - world.min(axis=0), (4.0, 2.0, 2.0))


class BackgroundImages(unittest.TestCase):
    """0.154: a picture laid on a storey — its corners turned with it; calibrated with a measure (8 m read 4 m on it:
    twice as big about the first point, which stays); placed and turned towards the second point; saved and read
    back (moved with the model's origin, its picture found beside the project)."""

    def test_geometry(self):
        from arqbim.model import images as im
        image = im.placed("planta", "/tmp/planta.png", (400, 200), (10.0, 10.0))
        self.assertAlmostEqual(image.width, 5.0)                        # (4 m: never smaller than 5 m)
        self.assertAlmostEqual(image.height, 2.5)
        np.testing.assert_allclose(image.corners()[0], (7.5, 8.75))
        a, b = np.array((8.0, 9.0)), np.array((10.0, 9.0))
        f = im.calibration(a, b, 4.0)
        self.assertAlmostEqual(f, 2.0)
        big = image.scaled(a, f)
        self.assertAlmostEqual(big.width, 10.0)
        np.testing.assert_allclose(big.local(a), 2 * np.array(image.local(a)))     # (the first point stays put)
        self.assertTrue(big.contains(a) and not big.contains((30.0, 9.0)))
        b2 = a + (b - a) * f                                            # the second point, on the bigger picture
        self.assertAlmostEqual(float(np.linalg.norm(b2 - a)), 4.0)
        moved = big.moved((1.0 - a[0], 1.0 - a[1]))                     # the first point to (1, 1)
        np.testing.assert_allclose(np.array(moved.corners()[0]) + (a - (1.0, 1.0)), big.corners()[0])
        angle = im.turn_towards((1.0, 1.0), b2 - a + (1.0, 1.0), (1.0, 5.0))
        self.assertAlmostEqual(angle, 90.0)
        turned = moved.turned((1.0, 1.0), angle)
        u, v = turned.axes()
        np.testing.assert_allclose(u, (0.0, 1.0), atol=1e-12)
        np.testing.assert_allclose(turned.local((1.0, 5.0)), moved.local(b2 - a + (1.0, 1.0)), atol=1e-9)
        self.assertIsNone(im.calibration(a, a, 4.0))
        self.assertIsNone(im.calibration(a, b, 0.0))

    def test_on_a_facade(self):
        """0.208: stood on a facade facing south (y < 0): from (2, 0, 0,5) to (8, 0, 0,5) — 6 m wide, 3 m high, its
        foot 0,5 m over the storey at 3 m —, read from the south; clicked right to left, the same; kept and read
        back; one point twice: None."""
        from arqbim.model import images as im
        image = im.placed("fachada", "/tmp/fachada.png", (400, 200), (0.0, 0.0))
        up = image.stood((2.0, 0.0, 3.5), (8.0, 0.0, 3.5), (0.0, -1.0, 0.0), 3.0)
        self.assertTrue(up.vertical)
        self.assertAlmostEqual(up.width, 6.0)
        self.assertAlmostEqual(up.base, 0.5)
        np.testing.assert_allclose(up.front(), (0.0, -1.0, 0.0), atol=1e-12)
        np.testing.assert_allclose(up.corners3d(3.0), [(2, 0, 3.5), (8, 0, 3.5), (8, 0, 6.5), (2, 0, 6.5)], atol=1e-9)
        back = image.stood((8.0, 0.0, 3.5), (2.0, 0.0, 3.5), (0.0, -1.0, 0.0), 3.0)
        np.testing.assert_allclose(back.corners3d(3.0), up.corners3d(3.0), atol=1e-9)
        again = im.from_dict(im.to_dict(up))
        self.assertTrue(again.vertical)
        self.assertAlmostEqual(again.base, 0.5)
        self.assertFalse(im.from_dict(im.to_dict(image)).vertical)
        self.assertIsNone(image.stood((1.0, 1.0, 0.0), (1.0, 1.0, 2.0), (0.0, -1.0, 0.0), 0.0))
        np.testing.assert_allclose(image.corners3d(2.0)[0], (*image.corners()[0], 2.0))  # (laid flat: at its level)

    def test_cropped(self):
        """0.209: a 10 × 5 picture cropped to its middle (corners clicked at 20 % / 20 % and 70 % / 80 %, either order):
        the part kept, its corners 2 → 7 m across and 1 → 4 m up, its picture's coordinates; a point outside it no
        longer on it; kept and read back; too thin: None; the whole shown again with crop None."""
        from arqbim.model import images as im
        image = im.placed("planta", "/tmp/planta.png", (1000, 500), (5.0, 2.5))
        self.assertEqual(image.kept(), (0.0, 0.0, 1.0, 1.0))
        cut = image.cropped((0.7, 0.8), (0.2, 0.2))
        self.assertEqual(cut.kept(), (0.2, 0.2, 0.7, 0.8))
        np.testing.assert_allclose(cut.kept_corners(0.0), [(2, 1, 0), (7, 1, 0), (7, 4, 0), (2, 4, 0)], atol=1e-9)
        np.testing.assert_allclose(cut.texcoords(), ((0.2, 0.8), (0.7, 0.8), (0.7, 0.2), (0.2, 0.2)))
        self.assertTrue(cut.contains((4.0, 2.0)) and not cut.contains((1.0, 0.5)) and image.contains((1.0, 0.5)))
        np.testing.assert_allclose(cut.fraction((7.0, 4.0, 0.0), 0.0), (0.7, 0.8))
        self.assertEqual(im.from_dict(im.to_dict(cut)).kept(), (0.2, 0.2, 0.7, 0.8))
        self.assertIsNone(image.cropped((0.5, 0.5), (0.5, 0.9)))
        up = cut.stood((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, -1.0, 0.0), 0.0)        # (on a facade: cropped too)
        np.testing.assert_allclose(up.kept_corners(0.0)[0], (2.0, 0.0, 1.0), atol=1e-9)

    def test_saved(self):
        import tempfile
        from arqbim.model import images as im
        with tempfile.TemporaryDirectory() as folder:
            picture = os.path.join(folder, "levantamento.png")
            with open(picture, "wb") as f:
                f.write(b"\x89PNG")
            image = im.placed("levantamento", picture, (1000, 500), (0.0, 0.0), storey="abc")
            image.locked, image.opacity = True, 0.4
            data = im.to_dict(image, folder)
            self.assertEqual(data["relative"], "levantamento.png")
            moved_folder = os.path.join(folder, "copia")
            os.makedirs(moved_folder)
            with open(os.path.join(moved_folder, "levantamento.png"), "wb") as f:
                f.write(b"\x89PNG")
            back = im.from_dict(data, (1.0, 2.0), moved_folder)         # (the project moved: its picture beside it)
            self.assertEqual(os.path.normpath(back.path), os.path.normpath(os.path.join(moved_folder,
                                                                                        "levantamento.png")))
            np.testing.assert_allclose(back.origin, np.array(image.origin) + (1.0, 2.0))
            self.assertEqual((back.width, back.storey, back.locked, back.opacity, back.uid),
                             (image.width, "abc", True, 0.4, image.uid))
            self.assertIsNone(im.from_dict({"path": picture}))


class TerrainGeometry(unittest.TestCase):
    """0.155: survey points to a surface (a 3 × 3 grid of points on a plane rising 10 % towards +X); its solid down
    to a base (closed, its volume the plane's prism); the height at a point; its contour lines every metre (upright
    lines, at the right x); its slope; a survey's text files read whatever their separators and decimals."""

    def _plane(self):
        return [(x, y, 10.0 + 0.1 * x) for x in (0.0, 10.0, 20.0) for y in (0.0, 10.0, 20.0)]

    def test_surface_and_solid(self):
        from arqbim.core import terrain
        verts, tris = terrain.tin(self._plane())
        self.assertEqual((len(verts), len(tris)), (9, 8))
        p = verts[tris]
        up = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])[:, 2]
        self.assertTrue(np.all(up > 0))                               # (counter-clockwise from above)
        self.assertAlmostEqual(terrain.plan_area(verts, tris), 400.0)
        self.assertAlmostEqual(terrain.height_at(verts, tris, (5.0, 7.0)), 10.5)
        self.assertIsNone(terrain.height_at(verts, tris, (25.0, 5.0)))
        sv, st = terrain.solid(verts, tris, 9.0)
        mesh = TriMesh(sv, st)
        self.assertTrue(mesh.is_closed())
        self.assertAlmostEqual(mesh.volume(), 400.0 * (11.0 - 9.0))  # (the mean height 11 m, down to 9)
        self.assertEqual(len(terrain.surface_of(sv, st)), 8)
        self.assertIsNone(terrain.tin([(0, 0, 0), (1, 1, 0), (2, 2, 0)]))       # (in a line)
        self.assertEqual(len(terrain.unique_points([(0, 0, 1), (0, 0, 2), (1, 0, 0)])), 2)

    def test_contours_and_slopes(self):
        from arqbim.core import terrain
        verts, tris = terrain.tin(self._plane())
        found = terrain.contours(verts, tris, 1.0)
        self.assertEqual([h for h, _s in found], [10.0, 11.0])       # (12 m only at the very border: none)
        for h, segs in found:
            self.assertTrue(np.allclose(segs[:, :, 0], (h - 10.0) / 0.1, atol=1e-6))     # (upright: x = 0, 10)
            self.assertTrue(np.allclose(segs[:, :, 2], h))
        mid = dict(found)[11.0]
        self.assertAlmostEqual(float(np.linalg.norm(mid[:, 1] - mid[:, 0], axis=1).sum()), 20.0)
        self.assertEqual([h for h, _s in terrain.contours(verts, tris, 0.5, top=11.0)], [10.0, 10.5, 11.0])
        self.assertTrue(terrain.is_major(10.0, 1.0) and not terrain.is_major(11.0, 1.0))
        np.testing.assert_allclose(terrain.slopes(verts, tris), 10.0)
        self.assertTrue(np.all(terrain.slope_bands(verts, tris) == 1))   # (0.156: 10 % is in the 5–10 % band)
        steep = terrain.tin([(0, 0, 0), (10, 0, 4), (0, 10, 0)])
        self.assertEqual(int(terrain.slope_bands(*steep)[0]), 4)         # (40 %: the last band)

    def test_reading_points(self):
        from arqbim.core import terrain
        cases = {"x y z\n100.5 200.25 12.1\n101 201 12.4\n": [(100.5, 200.25, 12.1), (101, 201, 12.4)],
                 "100,5;200,25;12,1\n": [(100.5, 200.25, 12.1)],
                 "1,100.5,200.25,12.1,arvore\n2,101,201,12.4,muro\n": [(100.5, 200.25, 12.1), (101, 201, 12.4)],
                 "P1\t100,5\t200,25\t12,1\n": [(100.5, 200.25, 12.1)],
                 "100,5 200,25 12,1\n": [(100.5, 200.25, 12.1)]}
        for text, expected in cases.items():
            points, _skipped = terrain.parse_points(text)
            np.testing.assert_allclose(points, expected, err_msg=text)
        _p, skipped = terrain.parse_points("Ponto;X;Y;Z\n1;2;3;4\n")
        self.assertEqual(skipped, 1)


class Earthworks(unittest.TestCase):
    """0.157: a 10 × 10 m platform on flat ground (40 × 40 m at 0): 1 m up — the proposed surface 1 m on it,
    its fill slope (2:3) down to the ground 1,5 m out, the ground farther; the fill about 100 m³ under it and 33 m³
    in its slopes, no cut. 1 m down: cut about 100 + 21 m³, no fill. A batter typed «1:1,5»."""

    def _ground(self):
        return [(x, y, 0.0) for x in range(0, 45, 5) for y in range(0, 45, 5)]

    def test_fill_and_cut(self):
        from arqbim.core import earthworks as ew
        from arqbim.core import terrain
        square = [(15.0, 15.0), (25.0, 15.0), (25.0, 25.0), (15.0, 25.0)]
        up = ew.proposed(self._ground(), [ew.Platform(square, 1.0)])
        verts, tris = terrain.tin(up)
        self.assertAlmostEqual(terrain.height_at(verts, tris, (20.0, 20.0)), 1.0, places=6)
        self.assertAlmostEqual(terrain.height_at(verts, tris, (25.75, 20.0)), 0.5, places=2)   # (on its slope)
        self.assertAlmostEqual(terrain.height_at(verts, tris, (35.0, 20.0)), 0.0, places=6)
        cut, fill = ew.volumes(self._ground(), up)
        self.assertLess(cut, 0.5)
        self.assertAlmostEqual(fill, 133.0, delta=133.0 * 0.04)
        down = ew.proposed(self._ground(), [ew.Platform(square, -1.0)])
        cut, fill = ew.volumes(self._ground(), down)
        self.assertLess(fill, 0.5)
        self.assertAlmostEqual(cut, 121.3, delta=121.3 * 0.04)
        self.assertAlmostEqual(ew.parse_slope("1:1,5"), 2.0 / 3.0)
        self.assertIsNone(ew.parse_slope("vertical"))
        back = ew.Platform.from_dict(ew.Platform(square, 1.0, name="Casa").to_dict())
        self.assertEqual((back.outline, back.z, back.name), (square, 1.0, "Casa"))


class SpotHeights(unittest.TestCase):
    """0.156: the height a spot marks — the highest surface facing up under it (a box's top, not its bottom; the
    top under a plan's cut only); written +12,35 / -1,20 / ±0,00."""

    def test_heights(self):
        from types import SimpleNamespace
        from arqbim.core import terrain
        from arqbim.model import spots

        def box(bottom, top):
            v, f = terrain.tin([(0.0, 0.0, top), (4.0, 0.0, top), (4.0, 4.0, top), (0.0, 4.0, top)])
            return TriMesh(*terrain.solid(v, f, bottom))

        box, low = box(0.0, 3.0), box(-1.0, -0.5)
        objs = [SimpleNamespace(mesh=box), SimpleNamespace(mesh=low)]
        self.assertAlmostEqual(spots.surface_height(objs, (1.0, 1.0)), 3.0)
        self.assertAlmostEqual(spots.surface_height(objs, (1.0, 1.0), top=1.0), -0.5)
        self.assertIsNone(spots.surface_height(objs, (9.0, 1.0)))
        self.assertEqual([spots.text(h) for h in (12.345, -1.2, 0.001)], ["+12,35", "-1,20", "±0,00"])


class CadDrawing(unittest.TestCase):
    """0.158: a plan's DXF in millimetres — a 5 m line, a polyline with a half circle (its bulge, dipping 1 m), a
    circle, a door block inserted turned 90° (its line on the insert's layer, upright from where it is), a text —
    read as segments in metres by layer; its units guessed when not said."""

    def _dxf(self, units=True):
        head = ["0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4", "0", "ENDSEC"] if units else []
        return "\n".join(head + [
            "0", "SECTION", "2", "BLOCKS",
            "0", "BLOCK", "8", "0", "2", "PORTA", "10", "0", "20", "0",
            "0", "LINE", "8", "0", "10", "0", "20", "0", "11", "900", "21", "0",
            "0", "ENDBLK",
            "0", "ENDSEC",
            "0", "SECTION", "2", "ENTITIES",
            "0", "LINE", "8", "PAREDES", "10", "0", "20", "0", "11", "5000", "21", "0",
            "0", "LWPOLYLINE", "8", "PAREDES", "90", "2", "70", "0", "10", "0", "20", "3000", "42", "1",
            "10", "2000", "20", "3000",
            "0", "CIRCLE", "8", "PILARES", "10", "4000", "20", "4000", "40", "200",
            "0", "INSERT", "8", "PORTAS", "2", "PORTA", "10", "1000", "20", "1000", "50", "90",
            "0", "TEXT", "8", "TEXTOS", "10", "100", "20", "100", "40", "250", "1", "Sala",
            "0", "ENDSEC", "0", "EOF", ""])

    def test_read(self):
        from arqbim.core import cad
        drawing = cad.read(self._dxf())
        self.assertEqual(drawing.units, 0.001)
        segs = cad.segments(drawing)
        walls = segs["PAREDES"]
        self.assertAlmostEqual(float(np.linalg.norm(walls[0, 1] - walls[0, 0])), 5.0)
        arc = walls[1:].reshape(-1, 2)
        self.assertAlmostEqual(float(arc[:, 1].min()), 2.0, places=2)                 # (dips 1 m below 3 m)
        np.testing.assert_allclose(arc[-1], (2.0, 3.0), atol=1e-9)
        door = segs["PORTAS"]
        np.testing.assert_allclose(door[0], ((1.0, 1.0), (1.0, 1.9)), atol=1e-9)
        circle = segs["PILARES"].reshape(-1, 2)
        self.assertAlmostEqual(float(np.linalg.norm(circle - (4.0, 4.0), axis=1).max()), 0.2, places=6)
        self.assertNotIn("TEXTOS", segs)
        self.assertEqual(cad.layers(drawing)["TEXTOS"], (1, 0))
        self.assertEqual(cad.read(self._dxf(units=False)).units, 0.001)               # (5000 across: mm)

    def test_dwg(self):
        """0.286: the same plan made a DWG (the ODA File Converter) and read back as a DWG — through its DXF, kept
        for next time: the 5 m line on PAREDES, the circle on PILARES; without the converter, skipped."""
        import tempfile
        from arqbim.core import cad, dwg
        if dwg.converter() is None:
            self.skipTest("ODA File Converter not installed")
        with tempfile.TemporaryDirectory() as folder:
            source = os.path.join(folder, "planta.dxf")
            with open(source, "w", encoding="utf-8") as f:
                f.write(self._dxf())
            path = dwg.from_dxf(source, os.path.join(folder, "planta.dwg"))
            with open(path, "rb") as f:
                self.assertEqual(f.read(4), b"AC10")                       # (a DWG: "AC1032" for AutoCAD 2018)
            segs = cad.segments(cad.read_file(path))
            self.assertAlmostEqual(float(np.linalg.norm(segs["PAREDES"][0, 1] - segs["PAREDES"][0, 0])), 5.0,
                                   places=6)
            circle = segs["PILARES"].reshape(-1, 2)
            self.assertAlmostEqual(float(np.linalg.norm(circle - (4.0, 4.0), axis=1).max()), 0.2, places=3)
            self.assertEqual(dwg.to_dxf(path), dwg.to_dxf(path))                 # (converted once)

    def test_arcs_apart(self):
        """0.210: the straight lines alone (no arcs, no circles, no bulged sides) and the arcs as arcs — the
        polyline's half circle (centre (1; 3), radius 1, from 180° to 360°), the circle."""
        from arqbim.core import cad
        drawing = cad.read(self._dxf())
        straight = cad.segments(drawing, straight=True)
        self.assertEqual(len(straight["PAREDES"]), 1)                                  # (the 5 m line only)
        self.assertNotIn("PILARES", straight)
        arcs = cad.arcs(drawing)
        (centre, radius, a0, a1), = arcs["PAREDES"]
        np.testing.assert_allclose(centre, (1.0, 3.0), atol=1e-9)
        self.assertAlmostEqual(radius, 1.0)
        self.assertAlmostEqual(a0 % 360, 180.0)
        self.assertAlmostEqual(a1 % 360, 0.0, places=6)
        (c2, r2, b0, b1), = arcs["PILARES"]
        self.assertEqual((round(r2, 6), b0, b1), (0.2, 0.0, 360.0))


class WallsFromLines(unittest.TestCase):
    """0.159: a 10 × 8 m room in double lines 20 cm apart, a 10 cm wall across it (its faces breaking the room's
    inner faces): five walls — the four outer ones 20 cm, their axes 10 cm in, meeting at the corners; the inner one
    10 cm, its ends on the outer walls' axes (a T each side); the bottom wall one wall, not broken at the T."""

    def _rect(self, x0, y0, x1, y1):
        return [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]

    def test_room_with_a_wall_across(self):
        from arqbim.core import cad_walls
        segs = self._rect(0, 0, 10, 8) + self._rect(0.2, 0.2, 4.95, 7.8) + self._rect(5.05, 0.2, 9.8, 7.8)
        walls = cad_walls.wall_axes(np.array(segs, dtype=float))
        self.assertEqual(len(walls), 5)
        thick = sorted(round(t, 3) for _a, _b, t in walls)
        self.assertEqual(thick, [0.1, 0.2, 0.2, 0.2, 0.2])
        ends = {tuple(sorted((tuple(np.round(a, 3)), tuple(np.round(b, 3))))) for a, b, _t in walls}
        self.assertIn(((0.1, 0.1), (9.9, 0.1)), ends)                  # (the bottom one, whole)
        self.assertIn(((0.1, 0.1), (0.1, 7.9)), ends)
        self.assertIn(((5.0, 0.1), (5.0, 7.9)), ends)                  # (across, T at both ends)

    def test_curved_walls(self):
        """0.210: two concentric arcs 3 m and 3,2 m round (0; 0), a quarter: a curved wall, its axis 3,1 m round,
        20 cm thick; two circles 25 cm apart: a round wall (2π); arcs only partly side by side: the part they share;
        arcs round other centres, or too far apart: none."""
        from arqbim.core import cad_walls
        found = cad_walls.arc_walls([((0, 0), 3.0, 0.0, 90.0), ((0, 0), 3.2, 0.0, 90.0)])
        (centre, radius, start, sweep, t), = found
        np.testing.assert_allclose(centre, (0, 0))
        self.assertAlmostEqual(radius, 3.1)
        self.assertAlmostEqual(start, 0.0)
        self.assertAlmostEqual(sweep, np.pi / 2)
        self.assertAlmostEqual(t, 0.2)
        ring, = cad_walls.arc_walls([((5, 5), 2.0, 0.0, 360.0), ((5, 5), 2.25, 0.0, 360.0)])
        self.assertAlmostEqual(ring[3], 2 * np.pi)
        self.assertAlmostEqual(ring[4], 0.25)
        part, = cad_walls.arc_walls([((0, 0), 3.0, 0.0, 90.0), ((0, 0), 3.2, 45.0, 135.0)])
        self.assertAlmostEqual(part[2], np.pi / 4)
        self.assertAlmostEqual(part[3], np.pi / 4)
        across, = cad_walls.arc_walls([((0, 0), 3.0, 300.0, 30.0), ((0, 0), 3.2, 330.0, 60.0)])   # (across 0°)
        self.assertAlmostEqual(across[3], np.radians(60.0))
        self.assertEqual(cad_walls.arc_walls([((0, 0), 3.0, 0.0, 90.0), ((1, 0), 3.2, 0.0, 90.0)]), [])
        self.assertEqual(cad_walls.arc_walls([((0, 0), 3.0, 0.0, 90.0), ((0, 0), 4.0, 0.0, 90.0)]), [])

    def test_opening_sizes(self):
        """0.212: an opening's size as written beside it, in m, cm or mm, with its sill or not; the nearest text to
        each opening, once each, within reach."""
        from arqbim.core import cad_openings
        cases = {"0,90×2,10": (0.9, 2.1, None), "90x210": (0.9, 2.1, None), "P1 0.80 x 2.00": (0.8, 2.0, None),
                 "1,20x1,10 / 1,00": (1.2, 1.1, 1.0), "J2 1,20x1,10 pt 1,00": (1.2, 1.1, 1.0),
                 "1200x1100 peitoril 900": (1.2, 1.1, 0.9), "h=2,20": (None, 2.2, None), "Sala": (None, None, None),
                 "PT1": (None, None, None)}
        for text, want in cases.items():
            got = cad_openings.parse_size(text)
            for g, w in zip(got, want):
                if w is None:
                    self.assertIsNone(g, (text, got))
                else:
                    self.assertAlmostEqual(g, w, places=6, msg=text)
        door = cad_openings.BlockInstance("PORTAS", "P", np.array(((0.0, 0.0), (0.9, 0.0))), [], (0, 0), 0.0, True)
        window = cad_openings.BlockInstance("JANELAS", "J", np.array(((5.0, 0.0), (6.2, 0.0))), [], (5, 0), 0.0,
                                            False)
        far = cad_openings.BlockInstance("PORTAS", "P", np.array(((20.0, 0.0), (20.9, 0.0))), [], (20, 0), 0.0, True)
        words = [(np.array((0.45, 0.6)), "0,90x2,00"), (np.array((5.6, 0.7)), "1,20x1,10 pt 0,90"),
                 (np.array((5.6, 0.9)), "1,20x1,30"), (np.array((10.0, 0.0)), "0,80x2,10")]
        self.assertEqual(cad_openings.read_sizes([door, window, far], words), 2)
        self.assertAlmostEqual(door.height, 2.0)
        self.assertAlmostEqual(window.height, 1.1)
        self.assertAlmostEqual(window.sill, 0.9)
        self.assertIsNone(far.height)

    def test_columns(self):
        """0.211: a closed 30 × 50 rectangle turned 30°, a circle 30 cm across, a closed 30 × 50 drawn twice: three
        columns at most (the twice drawn one once); a long rectangle (a wall's outline), a tiny one, a skewed four-sided
        one, a big circle: none."""
        from arqbim.core import cad_columns
        a = np.radians(30.0)
        u, v = np.array((np.cos(a), np.sin(a))), np.array((-np.sin(a), np.cos(a)))
        turned = [(5, 5) + u * sx * 0.15 + v * sy * 0.25 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        square = [(0, 0), (0.3, 0), (0.3, 0.5), (0, 0.5)]
        found = cad_columns.columns([turned, square, square, [(0, 0), (6, 0), (6, 0.2), (0, 0.2)],
                                     [(0, 0), (0.05, 0), (0.05, 0.05), (0, 0.05)],
                                     [(0, 0), (0.4, 0), (0.5, 0.4), (0.1, 0.4)]],
                                    [((2, 2), 0.15), ((8, 8), 1.0)])
        self.assertEqual(len(found), 3)
        centre, way, width, depth, round_ = found[0]
        np.testing.assert_allclose(centre, (5, 5), atol=1e-9)
        np.testing.assert_allclose(way, u, atol=1e-9)
        self.assertAlmostEqual(width, 0.3)
        self.assertAlmostEqual(depth, 0.5)
        self.assertFalse(round_)
        self.assertTrue(found[2][4] and abs(found[2][2] - 0.3) < 1e-9)
        self.assertEqual(len(cad_columns.outline(found[0])), 4)

    def test_hatch_and_short_lines_left(self):
        from arqbim.core import cad_walls
        ticks = [((k * 0.05, 0.0), (k * 0.05, 0.05)) for k in range(20)]        # (5 cm: shorter than 10 cm)
        self.assertEqual(cad_walls.wall_axes(np.array(ticks, dtype=float)), [])
        apart = [((0, 0), (5, 0)), ((0, 1.0), (5, 1.0))]                         # (1 m apart: no wall)
        self.assertEqual(cad_walls.wall_axes(np.array(apart, dtype=float)), [])


class PointClouds(unittest.TestCase):
    """0.161: a point cloud read from a LAS 1.2 (point format 2: its scale and offset, its colours), a binary PLY
    (with colours) and a text file (a header, x y z r g b); thinned to at most so many points."""

    def test_las(self):
        import struct
        from arqbim.core import pointcloud
        header = bytearray(227)
        header[0:4] = b"LASF"
        header[24], header[25] = 1, 2
        struct.pack_into("<H", header, 94, 227)
        struct.pack_into("<I", header, 96, 227)
        header[104] = 2
        struct.pack_into("<H", header, 105, 26)
        struct.pack_into("<I", header, 107, 3)
        struct.pack_into("<3d", header, 131, 0.001, 0.001, 0.001)
        struct.pack_into("<3d", header, 155, 100000.0, 200000.0, 0.0)
        records = b""
        for (x, y, z), (r, g, b) in (((1000, 2000, 3000), (65535, 0, 0)), ((-500, 0, 10), (0, 65535, 0)),
                                     ((0, 0, 0), (0, 0, 65535))):
            rec = bytearray(26)
            struct.pack_into("<3i", rec, 0, x, y, z)
            struct.pack_into("<3H", rec, 20, r, g, b)
            records += bytes(rec)
        cloud = pointcloud.read_las(bytes(header) + records)
        np.testing.assert_allclose(cloud.points[0], (100001.0, 200002.0, 3.0))
        np.testing.assert_allclose(cloud.points[1], (99999.5, 200000.0, 0.01))
        np.testing.assert_allclose(cloud.colours[0], (1.0, 0.0, 0.0))
        import tempfile
        with tempfile.TemporaryDirectory() as folder:                         # (from the file, mapped, thinned)
            path = os.path.join(folder, "nuvem.las")
            with open(path, "wb") as f:
                f.write(bytes(header) + records)
            every = pointcloud.read_file(path)
            np.testing.assert_allclose(every.points, cloud.points)
            self.assertEqual(len(pointcloud.read_file(path, most=2)), 2)     # (every 2nd: the 1st and 3rd)
            del every

    def test_laz_and_e57(self):
        """0.284: a LAZ (compressed, its scale and offset, its colours) and an E57 (two scans, one placed by its
        pose, with colours) written by their libraries and read back; thinned; without the libraries: refused."""
        import importlib.util
        import tempfile
        from arqbim.core import pointcloud
        if importlib.util.find_spec("laspy") is None or importlib.util.find_spec("pye57") is None:
            self.skipTest("laspy / pye57 not installed")
        import laspy
        import pye57
        xyz = np.array([(100001.0, 200002.0, 3.0), (99999.5, 200000.0, 0.01), (100000.0, 200000.0, 0.0)])
        rgb = np.array([(65535, 0, 0), (0, 65535, 0), (0, 0, 65535)], dtype=np.uint16)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "nuvem.laz")
            las = laspy.create(point_format=2, file_version="1.2")
            las.header.scales, las.header.offsets = (0.001, 0.001, 0.001), (100000.0, 200000.0, 0.0)
            las.x, las.y, las.z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
            las.red, las.green, las.blue = rgb[:, 0], rgb[:, 1], rgb[:, 2]
            las.write(path)                                                   # (compressed: .laz)
            with open(path, "rb") as f:
                self.assertEqual(f.read(4), b"LASF")
            cloud = pointcloud.read_file(path)
            np.testing.assert_allclose(cloud.points, xyz, atol=1e-6)
            np.testing.assert_allclose(cloud.colours[1], (0.0, 1.0, 0.0))
            self.assertEqual(len(pointcloud.read_file(path, most=2)), 2)
            path = os.path.join(folder, "nuvem.e57")
            e57 = pye57.E57(path, mode="w")
            scan = {"cartesianX": np.array([0.0, 1.0]), "cartesianY": np.array([0.0, 2.0]),
                    "cartesianZ": np.array([0.0, 3.0]), "colorRed": np.array([255, 0], dtype=np.uint8),
                    "colorGreen": np.array([0, 255], dtype=np.uint8), "colorBlue": np.array([0, 0], dtype=np.uint8)}
            e57.write_scan_raw(scan, name="a")
            e57.write_scan_raw(scan, name="b", translation=np.array((10.0, 0.0, 0.0)))
            e57.close()
            cloud = pointcloud.read_file(path)
            self.assertEqual(len(cloud), 4)
            self.assertAlmostEqual(float(cloud.points[:, 0].max()), 11.0, places=6)    # (the 2nd scan placed)
            np.testing.assert_allclose(cloud.colours[0], (1.0, 0.0, 0.0))
            self.assertEqual(len(pointcloud.read_file(path, most=3)), 3)

    def test_ply_and_text(self):
        from arqbim.core import pointcloud
        head = ("ply\nformat binary_little_endian 1.0\nelement vertex 2\nproperty float x\nproperty float y\n"
                "property float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n")
        rows = np.array([(1.0, 2.0, 3.0, 255, 0, 0), (4.0, 5.0, 6.0, 0, 0, 255)],
                        dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("r", "u1"), ("g", "u1"), ("b", "u1")])
        cloud = pointcloud.read_ply(head.encode() + rows.tobytes())
        np.testing.assert_allclose(cloud.points, ((1, 2, 3), (4, 5, 6)))
        np.testing.assert_allclose(cloud.colours[1], (0, 0, 1))
        text = pointcloud.read_text("X,Y,Z,R,G,B\n1.5,2,3,255,255,255\n4,5,6,0,0,0\n")
        self.assertEqual(len(text), 2)                                       # (a CSV: its header left out)
        np.testing.assert_allclose(text.colours[0], (1, 1, 1))
        np.testing.assert_allclose(text.points[1], (4, 5, 6))
        many = pointcloud.PointCloud(np.random.default_rng(1).random((1000, 3)))
        self.assertEqual(len(many.thinned(100)), 100)


class SpaceFrameSolver(unittest.TestCase):
    """0.165: the space frame against the beam tables — a 6 m beam with 10 kN/m simply supported (qL²/8 = 45 kNm at
    mid-span, 30 kN at each support, 5qL⁴/384EI), fixed at both ends (−qL²/12 at them, qL²/24 at mid-span); a 3 m
    cantilever with 10 kN at its tip (30 kNm at the support, PL³/3EI); a mechanism told."""

    E = 30e6

    def _beam(self, fixes1, fixes2, q=-10.0, length=6.0):
        from arqbim.core import space_frame as sf
        frame = sf.SpaceFrame()
        a, b = frame.add_node(0, 0, 0), frame.add_node(length, 0, 0)
        area, iy, iz, j = sf.rectangle(0.3, 0.5)
        m = frame.add_member("v", a, b, self.E, self.E / 2.4, area, iy, iz, j)
        frame.set_support(a, fixes1)
        frame.set_support(b, fixes2)
        frame.add_member_load("G", m, qz=q)
        return frame, m, iy

    def test_simply_supported(self):
        from arqbim.core import space_frame as sf
        pin = (True, True, True, True, False, False)
        roller = (False, True, True, False, False, False)
        frame, m, iy = self._beam(pin, roller)
        res = frame.solve(("G",))
        m1, ms, m2 = sf.span_moment(res["G"]["forces"]["v"], -10.0, 6.0)
        self.assertAlmostEqual(ms, 45.0, places=4)
        self.assertAlmostEqual(m1, 0.0, places=4)
        self.assertAlmostEqual(m2, 0.0, places=4)
        reactions = res["G"]["reactions"]
        self.assertAlmostEqual(sum(r[2] for r in reactions.values()), 60.0, places=4)
        self.assertAlmostEqual(frame.deflection_mid(res, {"G": 1.0}, m), 5 * 10 * 6 ** 4 / (384 * self.E * iy),
                               places=8)
        env = frame.envelope(res, [("1,35G", {"G": 1.35})])["v"]
        self.assertAlmostEqual(env["m_pos"], 1.35 * 45.0, places=4)

    def test_fixed_and_cantilever(self):
        from arqbim.core import space_frame as sf
        frame, m, _iy = self._beam((True,) * 6, (True,) * 6)
        res = frame.solve(("G",))
        m1, ms, m2 = sf.span_moment(res["G"]["forces"]["v"], -10.0, 6.0)
        self.assertAlmostEqual(m1, -30.0, places=4)
        self.assertAlmostEqual(ms, 15.0, places=4)
        self.assertAlmostEqual(m2, -30.0, places=4)
        can = sf.SpaceFrame()
        a, b = can.add_node(0, 0, 0), can.add_node(3, 0, 0)
        area, iy, iz, j = sf.rectangle(0.3, 0.5)
        mem = can.add_member("c", a, b, self.E, self.E / 2.4, area, iy, iz, j)
        can.set_support(a)
        can.add_nodal_load("P", b, fz=-10.0)
        res = can.solve(("P",))
        m1, _ms, m2 = sf.span_moment(res["P"]["forces"]["c"], 0.0, 3.0)
        self.assertAlmostEqual(m1, -30.0, places=4)
        self.assertAlmostEqual(m2, 0.0, places=4)
        tip = res["P"]["disp"][6 * b + 2]
        self.assertAlmostEqual(tip, -10.0 * 27 / (3 * self.E * iy), places=8)
        self.assertTrue(mem)

    def test_mechanism(self):
        from arqbim.core import space_frame as sf
        frame, _m, _iy = self._beam((False, True, True, True, False, False), (False, True, True, False, False, False))
        frame.add_nodal_load("G", 0, fx=1.0)
        with self.assertRaises(sf.SpaceFrameError):
            frame.solve(("G",))

    def test_band_solve(self):
        """0.223: the block solver as numpy's on a banded symmetric system (two cases, blocks smaller than it); a
        zero pivot told where."""
        from arqbim.core import space_frame as sf
        rng = np.random.default_rng(7)
        n, bw = 150, 9
        a = np.zeros((n, n))
        for k in range(bw + 1):
            v = rng.uniform(-1.0, 1.0, n - k)
            a[np.arange(n - k), np.arange(k, n)] = v
        a = a + np.triu(a, 1).T + np.eye(n) * 2.0 * (bw + 1)
        band = np.zeros((n, bw + 1))
        for k in range(bw + 1):
            band[:n - k, k] = a[np.arange(n - k), np.arange(k, n)]
        rhs = rng.uniform(-1.0, 1.0, (2, n))
        x = sf.band_solve(band, rhs, bw, 1e-12)
        self.assertTrue(np.allclose(x, np.linalg.solve(a, rhs.T).T, atol=1e-10))
        band[40, :] = 0.0
        band[40 - np.arange(1, bw + 1), np.arange(1, bw + 1)] = 0.0
        with self.assertRaises(sf._Pivot) as caught:
            sf.band_solve(band, rhs, bw, 1e-12)
        self.assertEqual(caught.exception.index, 40)


class ShellElements(unittest.TestCase):
    """0.223: the flat shell triangle (DKT plate + membrane) against Timoshenko's plates — a 4 m square plate,
    20 cm, E 30 GPa, ν 0,3, under 10 kN/m², meshed 8 × 8 (two triangles a square) in the space frame: simply
    supported, its centre's deflection 0,00406 qa⁴/D and moment 0,0479 qa² (within 2 % and 6 %), clamped 0,00126
    qa⁴/D; still with no strain when moved or turned as a whole (in its plane's axes), a uniform stretch's forces
    E t (εx + ν εy)/(1 − ν²); Wood–Armer's moments; the mesh of a 6 × 4 slab on its beams (its nodes along them, its
    area whole, every triangle counter-clockwise), drawn to the beams' faces snapped to their axes."""

    A, T, E, NU, Q = 4.0, 0.2, 30e6, 0.3, 10.0

    def _plate(self, n, clamped=False):
        from arqbim.core import space_frame as sf
        frame = sf.SpaceFrame()
        xs = np.linspace(0.0, self.A, n + 1)
        ids = [[frame.add_node(x, y, 0.0) for x in xs] for y in xs]
        for j in range(n):
            for i in range(n):
                p, r, s, u = ids[j][i], ids[j][i + 1], ids[j + 1][i + 1], ids[j + 1][i]
                for k, tri in enumerate(((p, r, s), (p, s, u))):
                    sh = frame.add_shell("t{}_{}_{}".format(i, j, k), *tri, self.E, self.NU, self.T)
                    frame.add_shell_load("G", sh, qz=-self.Q)
        for j, row in enumerate(ids):
            for i, node in enumerate(row):
                on_x, on_y = i in (0, n), j in (0, n)
                if on_x or on_y:
                    fixes = (True, True, True, clamped or on_x, clamped or on_y, True)
                    frame.set_support(node, fixes)
        res = frame.solve(("G",))
        centre = ids[n // 2][n // 2]
        around = [s for s in frame.shells if centre in s.nodes]
        m = np.mean([res["G"]["shells"][s.id] for s in around], axis=0)
        return -res["G"]["disp"][6 * centre + 2], m, res

    def test_plates(self):
        d = self.E * self.T ** 3 / (12 * (1 - self.NU ** 2))
        w, m, res = self._plate(8)
        self.assertAlmostEqual(w * d / (self.Q * self.A ** 4), 0.00406, delta=0.00406 * 0.02)
        self.assertAlmostEqual(m[0] / (self.Q * self.A ** 2), 0.0479, delta=0.0479 * 0.06)
        self.assertAlmostEqual(m[0], m[1], places=6)
        up = sum(r[2] for r in res["G"]["reactions"].values())
        self.assertAlmostEqual(up, self.Q * self.A ** 2, places=6)
        w, _m, _res = self._plate(8, clamped=True)
        self.assertAlmostEqual(w * d / (self.Q * self.A ** 4), 0.00126, delta=0.00126 * 0.05)

    def test_element(self):
        from arqbim.core import shell
        rot, xy = shell.axes((0.0, 0.0, 0.0), (2.0, 0.3, 0.0), (0.4, 1.5, 0.0))
        self.assertTrue(np.allclose(rot, np.eye(3)))
        k = shell.local_stiffness(xy, self.E, self.NU, self.T)
        self.assertTrue(np.allclose(k, k.T))
        rigid = []
        for d in range(3):                                  # (moved as a whole)
            u = np.zeros(18)
            u[d::6] = 1.0
            rigid.append(u)
        for axis in (0, 1):                                 # (turned about x, about y: w = y θ, w = −x θ)
            u = np.zeros(18)
            for j, (x, y) in enumerate(xy):
                u[6 * j + 2] = y if axis == 0 else -x
                u[6 * j + 3 + axis] = 1.0
            rigid.append(u)
        for u in rigid:
            self.assertLess(np.max(np.abs(k @ u)), 1e-6 * np.max(np.abs(k)))
        ex, ey = 1e-4, -2e-5
        u = np.zeros(18)
        for j, (x, y) in enumerate(xy):
            u[6 * j], u[6 * j + 1] = ex * x, ey * y
        r = shell.resultants(xy, self.E, self.NU, self.T, u)
        self.assertAlmostEqual(r[3], self.E * self.T * (ex + self.NU * ey) / (1 - self.NU ** 2), places=4)
        self.assertAlmostEqual(r[5], 0.0, places=6)
        self.assertTrue(np.allclose(r[:3], 0.0))
        self.assertEqual(shell.design_moments(10.0, 4.0, -3.0), ((13.0, 7.0), (0.0, 0.0)))
        self.assertEqual(shell.design_moments(-10.0, 2.0, 3.0), ((0.0, 5.0), (-13.0, -1.0)))

    def test_mesh(self):
        from arqbim.core import slab_mesh
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        beams = [(corners[k], corners[(k + 1) % 4]) for k in range(4)] + [((3.0, 0.0), (3.0, 4.0))]
        v, tris = slab_mesh.mesh(corners, 0.5, lines=beams, points=corners)
        tri = v[np.array(tris)]
        area2 = (tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1]) \
            - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1])
        self.assertTrue(np.all(area2 > 0))
        self.assertAlmostEqual(float(np.sum(area2)) / 2.0, 24.0, places=6)
        self.assertEqual(sorted(round(p[1], 6) for p in v if abs(p[0] - 3.0) < 1e-9), [k * 0.5 for k in range(9)])
        snapped = slab_mesh.snapped(((0.1, 0.1), (5.9, 0.1), (5.9, 3.9), (0.1, 3.9)), beams)
        self.assertTrue(np.allclose(snapped, corners))
        ell = ((0.0, 0.0), (6.0, 0.0), (6.0, 2.0), (3.0, 2.0), (3.0, 4.0), (0.0, 4.0))
        v, tris = slab_mesh.mesh(ell, 0.5, lines=beams, points=corners)
        tri = v[np.array(tris)]
        area = np.sum((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1])
                      - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1])) / 2.0
        self.assertAlmostEqual(float(area), 18.0, places=6)


class ConcreteDesign(unittest.TestCase):
    """0.166: Eurocode 2 against hand calculations (C25/30, A500) — a 30 × 50 beam with 100 kNm in its span (μ 0,097,
    As 5,34 cm²: 5 Ø12 that fit in one layer), 80 over its supports (4 Ø12), 250 kN of shear (stirrups Ø8//0,175 with
    cot θ 2,5); a section too small told; the basic span / depth ratios of Table 7.4N (20,5 and 14 at ρ 0,5 % and
    1,5 %, C30); the anchorage length of a Ø16 (40 φ); a 30 × 30 column under 1000 kN: slender (λ 35 > 13), its
    second-order moment added, its bars inside its N–M diagram (pure compression Ac fcd + As fyd); a 2 × 2 × 0,5 m
    footing: 192,5 kPa on the soil, rigid, its mesh As,min (5,8 cm²/m → Ø12//0,175), and the size it needs when the
    pressure is too much; a 6 × 4 slab's moment by Marcus."""

    def test_beam(self):
        import math
        from arqbim.core import ec2
        d = ec2.beam(0.30, 0.50, 6.0, 25, 500, 100.0, -80.0, 250.0)
        self.assertEqual(d.status, ec2.OK)
        bend = [n for n in d.notes if n.code == "bending"]
        dd = 0.5 - 0.03 - 0.008 - 0.008
        mu = 100.0 / (0.3 * dd * dd * 25 / 1.5 * 1000)
        self.assertAlmostEqual(bend[0].values["mu"], mu, places=6)
        need = (1 - math.sqrt(1 - 2 * mu)) * 0.3 * dd * (25 / 1.5) / (500 / 1.15)
        self.assertAlmostEqual(bend[0].values["need"], need, places=8)
        self.assertAlmostEqual(need * 1e4, 5.34, places=2)
        self.assertEqual(d.bottom, (5, 12))
        self.assertEqual(d.top, (4, 12))
        self.assertEqual(d.links, (8, 0.175))
        shear = next(n for n in d.notes if n.code == "shear")
        self.assertEqual(shear.values["cot"], 2.5)
        self.assertTrue(shear.values["needed"])
        small = ec2.beam(0.20, 0.30, 5.0, 25, 500, 200.0, 0.0, 50.0)
        self.assertEqual(small.status, ec2.FAIL)
        self.assertEqual(small.worst().code, "bending_fail")

    def test_limits(self):
        from arqbim.core import ec2
        self.assertAlmostEqual(ec2.span_depth_limit(0.005, 0.0, 30), 20.5, delta=0.1)
        self.assertAlmostEqual(ec2.span_depth_limit(0.015, 0.0, 30), 14.0, delta=0.05)
        self.assertAlmostEqual(ec2.bond_length(16, 25, 500), 0.646, places=3)
        self.assertEqual(ec2.fit_bars(5.34e-4, 0.30, 0.03, 8), (5, 12, True))
        self.assertFalse(ec2.fit_bars(20e-4, 0.20, 0.03, 8)[2])

    def test_column(self):
        from arqbim.core import ec2
        d = ec2.column(0.30, 0.30, 3.0, 25, 500, 1000.0, 20.0)
        self.assertNotEqual(d.status, ec2.FAIL)
        second = next(n for n in d.notes if n.code == "second_order")
        self.assertAlmostEqual(second.values["lam"], 3.0 / (0.3 / 12 ** 0.5), places=6)
        self.assertAlmostEqual(second.values["m2"], 1000.0 * (500 / 1.15 / 200e3) / (0.45 * 0.9 * 0.3) * 9 / 10,
                               places=4)
        n, dia = d.bars
        self.assertGreaterEqual(n, 4)
        self.assertEqual(n % 2, 0)
        area = n * ec2.bar_area(dia)
        diagram = ec2.interaction_diagram(0.3, 0.3, 25, 500, area, 0.03 + 0.008 + dia / 2000)
        self.assertAlmostEqual(diagram[0][0], 0.09 * 25 / 1.5 * 1000 + area * 500 / 1.15 * 1000, places=6)
        m = 20.0 + second.values["m2"]
        along, _across = ec2._column_layout(n, 0.3, 0.3)
        faces = 2 * along * ec2.bar_area(dia)                # (the bars on the two faces across the bending)
        cover = 0.03 + 0.008 + dia / 2000
        self.assertLessEqual(ec2.interaction_ratio(ec2.interaction_diagram(0.3, 0.3, 25, 500, faces, cover), 1000.0,
                                                   m), 1.0 + 1e-9)
        tie, s = d.links
        self.assertEqual(tie, 8)
        self.assertAlmostEqual(s, min(0.02 * dia, 0.30), delta=0.025)

    def test_footing(self):
        from arqbim.core import ec2
        d = ec2.footing(2.0, 2.0, 0.5, 0.3, 0.3, 25, 500, 1000.0, 720.0, soil=200.0)
        self.assertEqual(d.status, ec2.OK)
        bearing = next(n for n in d.notes if n.code == "bearing")
        self.assertAlmostEqual(bearing.values["sigma"], (720.0 + 2 * 2 * 0.5 * 25) / 4.0, places=6)
        self.assertTrue(any(n.code == "rigid" for n in d.notes))
        self.assertEqual(d.mesh_x, (12, 0.175))
        mesh = next(n for n in d.notes if n.code == "mesh")
        self.assertAlmostEqual(mesh.values["m"], 1000.0 / 4.0 * 0.85 ** 2 / 2, places=6)
        self.assertAlmostEqual(mesh.values["area"], max(0.26 * 0.3 * 25 ** (2 / 3) / 500, 0.0013) * 0.434, places=8)
        big = ec2.footing(2.0, 2.0, 0.5, 0.3, 0.3, 25, 500, 1200.0, 800.0, soil=200.0)
        self.assertEqual(big.status, ec2.FAIL)
        self.assertAlmostEqual(big.worst().values["side"], 2.10, places=6)

    def test_slab(self):
        from arqbim.core import ec2
        d = ec2.slab(6.0, 4.0, 0.15, 25, 500, 5.25, 2.0)
        load = next(n for n in d.notes if n.code == "slab_load")
        p = 1.35 * 5.25 + 1.5 * 2.0
        self.assertAlmostEqual(load.values["m_short"], 6 ** 4 / (4 ** 4 + 6 ** 4) * p * 16 / 8, places=6)
        self.assertNotEqual(d.status, ec2.FAIL)
        self.assertEqual(d.mesh_y[0], 8)                  # (the short span is along Y: its bars carry the most)
        self.assertLessEqual(d.mesh_y[1], d.mesh_x[1])
        shell = ec2.slab(6.0, 4.0, 0.15, 25, 500, 5.25, 2.0, moments=(3.0, 9.0))     # (0.223: the shell's moments)
        given = next(n for n in shell.notes if n.code == "slab_shell")
        self.assertEqual((given.values["m_short"], given.values["m_long"]), (9.0, 3.0))
        self.assertFalse(any(n.code == "slab_load" for n in shell.notes))

    def test_curtailment(self):
        """0.229: the moment n bars resist the one their area needs (bars_moment against the flexure); an 8 m beam
        30 × 60, 180 kNm sagging in its span and −120 at its ends: 2 of its bottom bars end to end, the others only
        where the envelope moved al = z cot θ / 2 asks more than those two resist, plus lb,rqd — symmetric about
        mid-span, its edges lb,rqd past where the moved envelope meets the two bars' moment; its top bars more than
        two from each end; a beam needing its bars the whole length (a flat envelope): none stopped; in two layers:
        none stopped."""
        from arqbim.core import ec2
        need, _mu = ec2._flexure(80.0, 0.3, 0.45, ec2.fcd(25), ec2.fyd(500))
        n_eq = need / ec2.bar_area(16)
        self.assertAlmostEqual(ec2.bars_moment(n_eq, 16, 0.3, 0.45, 25, 500), 80.0, places=6)
        span = 8.0
        xs = np.linspace(0.0, span, 101)
        m_max = 4 * 300.0 * xs * (span - xs) / span ** 2 - 120.0     # (180 sagging in its span, −120 at its ends)
        d = ec2.beam(0.30, 0.60, span, 25, 500, 180.0, -120.0, 150.0,
                     envelope=(span, xs, list(m_max), list(m_max)))
        n, dia = d.bottom
        self.assertGreater(n, 2)
        self.assertEqual(d.bottom_cont, 2)
        (z0, z1), = d.bottom_zones
        self.assertAlmostEqual(z0, span - z1, places=2)
        note = next(x for x in d.notes if x.code == "curtail")
        dd = 0.60 - 0.03 - 0.008 - dia / 2000
        kept = ec2.bars_moment(2, dia, 0.30, dd, 25, 500)
        al, lbd = note.values["al"], note.values["lbd"]
        self.assertAlmostEqual(lbd, ec2.bond_length(dia, 25, 500, good=True))
        edge = z0 + lbd                                 # (where the moved envelope meets the two bars, ± a step)
        moved = 4 * 300.0 * (edge + al) * (span - edge - al) / span ** 2 - 120.0
        self.assertAlmostEqual(moved, kept, delta=0.12 * kept)
        if d.top[0] > 2:                                # (over its supports: from each end)
            self.assertEqual([z[0] for z in d.top_zones][:1] + [z[1] for z in d.top_zones][-1:], [0.0, span])
        flat = ec2.beam(0.30, 0.60, span, 25, 500, 180.0, 0.0, 100.0,
                        envelope=(span, xs, [180.0] * 101, [0.0] * 101))
        self.assertIsNone(flat.bottom_zones)
        xs = np.linspace(0.0, 6.0, 61)
        two = ec2.beam(0.20, 0.60, 6.0, 25, 500, 280.0, 0.0, 100.0,
                       envelope=(6.0, xs, list(4 * 280.0 * xs * (6.0 - xs) / 36.0), [0.0] * 61))
        self.assertGreater(two.bottom2, 0)
        self.assertIsNone(two.bottom_zones)

    def test_pile_caps(self):
        """0.228: pile caps by struts and ties — on two piles 0,90 m apart (Ø30) under a 30 × 30 column, 1000 kN:
        its weight added (1,35 × 13,5 kN), the tie N (2l − a)/(8d) with d = 0,534 m, the struts' angle from a quarter
        of the column to the piles' axes, the nodes' stresses N/A against k1 ν' fcd and k2 ν' fcd, the tie
        held in the band over the piles, the minimum mesh across; on four piles a tie along each side N (2l − a) /
        (16 d); a column too heavy for its node told; one pile: the minimum mesh. A strip footing 50 × 30 under a
        20 cm wall of 8,4 kN/m: 24,3 kPa with its own weight, its bars across for its sides' bending, those along a
        fifth of them; too narrow for its load: the width it needs."""
        from arqbim.core import ec2
        spots = [(-0.45, 0.0), (0.45, 0.0)]
        d = ec2.pile_cap(spots, 0.30, 1.5, 0.6, 0.6, 0.3, 0.3, 25, 500, 1000.0, 740.0)
        self.assertNotEqual(d.status, ec2.FAIL)
        n = 1000.0 + 1.35 * 1.5 * 0.6 * 0.6 * 25
        dd = 0.6 - 0.05 - 0.016
        tie = next(x for x in d.notes if x.code == "cap_tie")
        self.assertAlmostEqual(tie.values["t"], n * (2 * 0.9 - 0.3) / (8 * dd))
        theta = math.atan2(dd, 0.45 - 0.3 / 4)
        self.assertAlmostEqual(next(x for x in d.notes if x.code == "struts").values["theta"], math.degrees(theta))
        col = next(x for x in d.notes if x.code == "node_column")
        self.assertAlmostEqual(col.values["stress"], n / 0.09 / 1000)
        self.assertAlmostEqual(col.values["limit"], (1 - 25 / 250) * 25 / 1.5)
        pile = next(x for x in d.notes if x.code == "node_pile")
        self.assertAlmostEqual(pile.values["stress"], n / 2 / (math.pi * 0.15 ** 2) / 1000)
        self.assertAlmostEqual(pile.values["limit"], 0.85 * (1 - 25 / 250) * 25 / 1.5)
        self.assertAlmostEqual(tie.values["need"], tie.values["t"] / (500 / 1.15 * 1000) / 0.5)
        self.assertGreaterEqual(ec2.bar_area(d.mesh_x[0]) / d.mesh_x[1] * 0.5 * 500 / 1.15 * 1000,
                                tie.values["t"] - 1e-6)
        self.assertTrue(any(x.code == "cap_mesh" and x.values["face"] == "y" for x in d.notes))
        four = ec2.pile_cap([(-0.45, -0.45), (0.45, -0.45), (0.45, 0.45), (-0.45, 0.45)], 0.30, 1.5, 1.5, 0.7, 0.3,
                            0.3, 25, 500, 1200.0, 880.0)
        n4 = 1200.0 + 1.35 * 1.5 * 1.5 * 0.7 * 25
        ties = {x.values["face"]: x.values["t"] for x in four.notes if x.code == "cap_tie"}
        self.assertAlmostEqual(ties["x"], n4 * (2 * 0.9 - 0.3) / (16 * (0.7 - 0.066)))
        self.assertAlmostEqual(ties["x"], ties["y"])
        heavy = ec2.pile_cap(spots, 0.30, 1.5, 0.6, 0.6, 0.3, 0.3, 25, 500, 9000.0, 6500.0)
        self.assertEqual(heavy.status, ec2.FAIL)
        one = ec2.pile_cap([(0.0, 0.0)], 0.30, 0.6, 0.6, 0.5, 0.3, 0.3, 25, 500, 500.0, 360.0)
        self.assertTrue(any(x.code == "pile_cap_one" for x in one.notes))
        self.assertIsNotNone(one.mesh_x)
        strip = ec2.strip_footing(0.5, 0.3, 0.2, 25, 500, 1.35 * 8.4, 8.4, 200.0)
        bearing = next(x for x in strip.notes if x.code == "strip_bearing")
        self.assertAlmostEqual(bearing.values["sigma"], (8.4 + 0.5 * 0.3 * 25) / 0.5)
        across = next(x for x in strip.notes if x.code == "mesh")
        self.assertAlmostEqual(across.values["m"], 1.35 * 8.4 / 0.5 * 0.15 ** 2 / 2)
        self.assertEqual(strip.mesh_y, (across.values["d"], across.values["s"]))
        along = next(x for x in strip.notes if x.code == "strip_along")
        self.assertAlmostEqual(along.values["area"], 0.2 * ec2.bar_area(strip.mesh_y[0]) / strip.mesh_y[1])
        narrow = ec2.strip_footing(0.5, 0.3, 0.2, 25, 500, 1.35 * 150.0, 150.0, 200.0)
        self.assertEqual(narrow.status, ec2.FAIL)
        self.assertAlmostEqual(narrow.worst().values["side"], math.ceil((150.0 + 3.75) / 200 / 0.05) * 0.05)

    def test_two_layers(self):
        """0.225: a 20 × 60 beam with 280 kNm — its bars do not fit in one layer: 5 Ø20, 3 in the first and 2 over
        them (EC2 8.2(3)), the gaps kept; its effective depth the bars' centre (0,534 m) and what they need worked
        with it; a beam 1,00 m deep told it wants skin bars (EC2 7.3.3(3)), one of 0,95 m not."""
        from arqbim.core import ec2
        d = ec2.beam(0.20, 0.60, 6.0, 25, 500, 280.0, -30.0, 100.0)
        self.assertEqual((d.bottom, d.bottom2, d.top2), ((5, 20), 2, 0))
        two = next(n for n in d.notes if n.code == "two_layers")
        self.assertEqual((two.values["n1"], two.values["n2"]), (3, 2))
        depth = 0.60 - 0.03 - 0.008 - 0.010 - 2 / 5 * (0.020 + ec2.min_gap(20))
        self.assertAlmostEqual(two.values["depth"], depth, places=4)
        bend = next(n for n in d.notes if n.code == "bending" and n.values["face"] == "bottom")
        mu = 280.0 / (0.20 * depth ** 2 * 25 / 1.5 * 1000)
        self.assertAlmostEqual(bend.values["mu"], mu, places=3)
        self.assertGreaterEqual(5 * ec2.bar_area(20), bend.values["need"])
        self.assertGreaterEqual(ec2.clear_gap(3, 20, 0.20, 0.03, 8), ec2.min_gap(20))
        self.assertLess(ec2.clear_gap(4, 20, 0.20, 0.03, 8), ec2.min_gap(20))
        self.assertFalse(any(n.code == "skin" for n in d.notes))
        deep = ec2.beam(0.30, 1.00, 8.0, 25, 500, 300.0, -200.0, 300.0)
        self.assertEqual(next(n for n in deep.notes if n.code == "skin").status, ec2.WARN)
        self.assertFalse(any(n.code == "skin" for n in ec2.beam(0.30, 0.95, 8.0, 25, 500, 300.0, -200.0, 300.0).notes))

    def test_slab_top(self):
        """0.224: a slab's top bars over its supports, each way — for its hogging moment, at least a quarter of its
        span's (EC2 9.3.1.2(2)), never under the minimum; by Marcus, the quarter alone."""
        from arqbim.core import ec2
        d = ec2.slab(6.0, 4.0, 0.20, 25, 500, 6.5, 2.0, moments=(10.0, 20.0), top=(-12.0, -1.0))
        tops = {n.values["face"]: n for n in d.notes if n.code == "slab_top_mesh"}
        self.assertAlmostEqual(tops["x"].values["m"], 12.0)                     # (its own: more than 10/4)
        self.assertAlmostEqual(tops["y"].values["m"], 5.0)                      # (a quarter of 20: more than 1)
        self.assertAlmostEqual(tops["y"].values["quarter"], 5.0)
        self.assertIsNotNone(d.top_x)
        self.assertIsNotNone(d.top_y)
        self.assertGreaterEqual(ec2.bar_area(d.top_x[0]) / d.top_x[1], tops["x"].values["area"] - 1e-9)
        self.assertGreaterEqual(tops["x"].values["area"], tops["x"].values["need"])
        marcus = ec2.slab(6.0, 4.0, 0.20, 25, 500, 6.5, 2.0)
        load = next(n for n in marcus.notes if n.code == "slab_load")
        quarter = {n.values["face"]: n.values["m"] for n in marcus.notes if n.code == "slab_top_mesh"}
        self.assertAlmostEqual(quarter["y"], 0.25 * load.values["m_short"])    # (the short span along y)
        self.assertAlmostEqual(quarter["x"], 0.25 * load.values["m_long"])


class ShapedColumns(unittest.TestCase):
    """0.227: round, L and T columns as they are — their sections (a Ø30: π r², π r⁴/4; an L 40 × 40 with 15 cm
    legs: 0,0975 m², its centroid 4,8 cm off the middle towards its corner; a T 50 × 40: 0,1125 m², 5,8 cm up; a
    rectangle as before); the N–M diagram by fibres the rectangle's (its two ends exactly, within 3 % between);
    the bars round a circle, at an L's six corners and a T's eight, the rest in pairs on its faces, None when they
    do not fit; a Ø30 column under 800 kN and 30 kNm verified with six bars or more, inside its own diagram, and
    laid round a circle with hoops; an L's ties round each leg; the analysis with its true section and weight."""

    def test_sections(self):
        from arqbim.core import space_frame as sf
        a, iy, ix, j, c = sf.section("circle", 0.3, 0.3)
        self.assertAlmostEqual(a, math.pi * 0.15 ** 2)
        self.assertAlmostEqual(iy, math.pi * 0.15 ** 4 / 4)
        self.assertEqual(iy, ix)
        a, iy, ix, j, (cx, cy) = sf.section("L", 0.4, 0.4, 0.15)
        self.assertAlmostEqual(a, 0.15 * (0.4 + 0.4 - 0.15))
        self.assertAlmostEqual(cx, (0.06 * -0.125 + 0.0375 * 0.075) / 0.0975)
        self.assertAlmostEqual(cx, cy)
        self.assertAlmostEqual(iy, ix)
        ref = 0.4 * 0.15 ** 3 / 12 + 0.06 * (-0.125 - cx) ** 2 + 0.15 * 0.25 ** 3 / 12 + 0.0375 * (0.075 - cx) ** 2
        self.assertAlmostEqual(iy, ref)
        a, iy, ix, j, (cx, cy) = sf.section("T", 0.5, 0.4, 0.15)
        self.assertAlmostEqual(a, 0.1125)
        self.assertAlmostEqual(cx, 0.0)
        self.assertAlmostEqual(cy, (0.075 * 0.125 + 0.0375 * -0.075) / 0.1125)
        self.assertAlmostEqual(iy, 0.15 * 0.5 ** 3 / 12 + 0.25 * 0.15 ** 3 / 12)
        self.assertEqual(sf.section("rect", 0.3, 0.5)[:4], sf.rectangle(0.5, 0.3))

    def test_fibres(self):
        from arqbim.core import ec2
        b, h, cov = 0.30, 0.40, 0.046
        area = 4 * ec2.bar_area(16)
        ref = ec2.interaction_diagram(b, h, 25, 500, area, cov)
        bars = [(x, y, area / 4) for x in (-b / 2 + cov, b / 2 - cov) for y in (-h / 2 + cov, h / 2 - cov)]
        fib = ec2.fibre_diagram(ec2.section_fibres("rect", b, h, cells=60), bars, 25, 500, (0.0, 1.0))
        self.assertEqual(len(fib), len(ref))
        self.assertAlmostEqual(fib[0][0], ref[0][0], delta=ref[0][0] * 1e-3)
        self.assertAlmostEqual(fib[-1][0], ref[-1][0], places=6)
        top = max(m for _n, m in ref)
        for (n1, m1), (n2, m2) in zip(ref[3:-3], fib[3:-3]):
            self.assertAlmostEqual(m1, m2, delta=0.03 * top)

    def test_spots(self):
        from arqbim.core import ec2
        circle = ec2.column_spots("circle", 0.3, 0.3, 0.0, 6, 16, 0.03, 8)
        r = 0.15 - 0.03 - 0.008 - 0.008
        self.assertEqual(len(circle), 6)
        self.assertTrue(all(abs(math.hypot(x, y) - r) < 1e-9 for x, y in circle))
        self.assertEqual(len(ec2.column_spots("L", 0.4, 0.4, 0.15, 6, 12, 0.03, 8)), 6)
        self.assertIsNone(ec2.column_spots("L", 0.4, 0.4, 0.15, 5, 12, 0.03, 8))
        self.assertIsNone(ec2.column_spots("L", 0.4, 0.4, 0.15, 7, 12, 0.03, 8))      # (its faces two by two)
        t10 = ec2.column_spots("T", 0.5, 0.4, 0.15, 10, 12, 0.03, 8)
        xs = sorted(round(x, 6) for x, _y in t10)
        self.assertEqual(xs, sorted(round(-x, 6) for x in xs))                        # (symmetric)
        self.assertIsNone(ec2.column_spots("circle", 0.3, 0.3, 0.0, 30, 20, 0.03, 8))

    def test_round_column(self):
        from arqbim.core import ec2, rebar
        d = ec2.column(0.30, 0.30, 3.0, 25, 500, 800.0, 30.0, shape="circle")
        self.assertNotEqual(d.status, ec2.FAIL)
        n, dia = d.bars
        self.assertGreaterEqual(n, ec2.CIRCLE_MIN_BARS)
        self.assertTrue(any(x.code == "column_shape" for x in d.notes))
        inter = next(x for x in d.notes if x.code == "interaction")
        spots = ec2.column_spots("circle", 0.3, 0.3, 0.0, n, dia, d.cover, 8)
        diagram = ec2.fibre_diagram(ec2.section_fibres("circle", 0.3, 0.3), [(x, y, ec2.bar_area(dia)) for x, y in spots],
                                    25, 500, (1.0, 0.0))
        self.assertLessEqual(ec2.interaction_ratio(diagram, 800.0, inter.values["m"]), 1.0 + 1e-9)
        sets = {s.role: s for s in rebar.column_sets((2.0, 1.0), (1.0, 0.0), (0.15, 0.15), 0.0, 3.0, d, 25, 500,
                                                     shape="circle")}
        mains = sets["main"].bars
        self.assertEqual(len(mains), n)
        for bar in mains:
            self.assertAlmostEqual(math.hypot(bar[0][0] - 2.0, bar[0][1] - 1.0), 0.15 - d.cover - d.links[0] / 1000
                                   - dia / 2000, places=6)
        hoop = np.asarray(sets["ties"].bars[0])
        self.assertTrue(np.allclose(np.hypot(hoop[:, 0] - 2.0, hoop[:, 1] - 1.0), 0.15 - d.cover - d.links[0] / 2000))
        el = ec2.column(0.40, 0.40, 3.0, 25, 500, 900.0, 40.0, shape="L", web=0.15)
        self.assertGreaterEqual(el.bars[0], 6)
        ties = {s.role: s for s in rebar.column_sets((0, 0), (1, 0), (0.2, 0.2), 0.0, 3.0, el, 25, 500,
                                                     shape="L", web=0.15)}["ties"]
        levels = {round(float(np.mean(np.asarray(b)[:, 2])), 2) for b in ties.bars}
        self.assertEqual(len(ties.bars), 2 * len(levels))                            # (one round each leg)

    def test_analysis(self):
        from arqbim.core import actions, structural as st
        from arqbim.model import structure_analysis as sa, structure_loads
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        cols = [st.Column("c{}".format(k), p, 0.0, 3.0, (0.3, 0.3), shape="circle") for k, p in enumerate(corners)]
        beams = [st.Beam("b{}".format(k), corners[k], corners[(k + 1) % 4], 3.0, (0.25, 0.5)) for k in range(4)]
        foots = [st.Footing("f{}".format(k), p, 0.0, (1.2, 1.2)) for k, p in enumerate(corners)]
        model = st.build(cols, beams, foots, [st.Panel("s", list(corners), 3.0, 0.2)], levels=[0.0, 3.0])
        self.assertTrue(all(m.shape == "circle" for m in model.members if m.kind == "column"))
        settings = actions.Settings(use="A", roof_use="A", slabs="areas")
        loads = structure_loads.building_actions(model, settings, (), 0.0)
        column = next(m for m in model.members if m.kind == "column")
        self.assertAlmostEqual(loads.member_g[column.id], math.pi * 0.15 ** 2 * 25.0)
        frame, members, _cases = sa.build_frame(model, loads, settings)
        sm = members[column.id][1][0]
        self.assertAlmostEqual(sm.area, math.pi * 0.15 ** 2)
        self.assertAlmostEqual(sm.iy, math.pi * 0.15 ** 4 / 4)
        result = sa.analyse(model, loads, settings)
        self.assertEqual(result.error, "")
        self.assertAlmostEqual(result.reactions_up, result.loads_in, delta=result.loads_in * 1e-6)


class RebarLayout(unittest.TestCase):
    """0.166: the bars laid out — a 6 m beam's 5 Ø12 at the bottom 54,4 cm over its underside, across its width less
    the covers, run 12 cm into each column and bent up 15 cm (shape 21, 6,54 m); its 34 stirrups every 17,5 cm, closed
    with 135° hooks (shape 51); a column's bars from 42 cm down in its footing (bent out on its mesh) to under the floor
    (shape 11); a 1,2 m footing's 7 bars each way; an L-shaped slab's bars all inside it less the cover; equal bars one
    position, a tie and a stirrup of one length but bent otherwise two."""

    def test_beam(self):
        from arqbim.core import ec2, rebar
        d = ec2.Design("beam", bottom=(5, 12), top=(4, 12), links=(8, 0.175))
        sets = {s.role: s for s in rebar.beam_sets((0, 0), (6, 0), 3.0, 0.3, 0.5, d, 25, 500, (0.12, 0.12))}
        bottom = sets["bottom"]
        self.assertEqual(len(bottom.bars), 5)
        ys = sorted(round(b[1][1], 6) for b in bottom.bars)
        self.assertAlmostEqual(ys[0], -(0.15 - 0.03 - 0.008 - 0.006), places=6)
        self.assertAlmostEqual(bottom.bars[0][1][2], 3.0 - 0.5 + 0.03 + 0.008 + 0.006, places=6)
        self.assertAlmostEqual(bottom.bars[0][1][0], -0.12, places=6)
        self.assertAlmostEqual(rebar.BarSet.length_of(bottom.bars[0]), 6.24 + 0.30, places=6)
        self.assertEqual(bottom.shape_of(bottom.bars[0]), "21")
        self.assertLess(sets["top"].bars[0][0][2], sets["top"].bars[0][1][2])        # (the top bars bent down)
        stirrups = sets["stirrups"]
        self.assertEqual(len(stirrups.bars), 34)
        self.assertEqual(stirrups.shape_of(stirrups.bars[0]), "51")
        self.assertAlmostEqual(rebar.BarSet.length_of(stirrups.bars[0]), 2 * (0.232 + 0.432) + 0.16, delta=0.02)
        self.assertEqual(stirrups.kind, "SHEAR")
        self.assertEqual(len(bottom.groups()), 1)

    def test_column_footing_slab(self):
        from arqbim.core import ec2, rebar
        d = ec2.Design("column", bars=(4, 12), links=(8, 0.225))
        sets = {s.role: s for s in rebar.column_sets((1, 1), (1, 0), (0.15, 0.15), 0.0, 3.0, d, 25, 500, 0.42,
                                                      False)}
        main = sets["main"]
        self.assertEqual(len(main.bars), 4)
        self.assertEqual(main.shape_of(main.bars[0]), "11")
        self.assertAlmostEqual(main.bars[0][1][2], -0.42, places=6)
        self.assertAlmostEqual(main.bars[0][2][2], 3.0 - 0.03 - 0.008, places=6)
        self.assertEqual(len(sets["ties"].bars), 13)
        self.assertEqual(sets["ties"].kind, "LIGATURE")
        f = ec2.Design("footing", mesh_x=(12, 0.175), mesh_y=(12, 0.175), cover=0.05)
        mesh = rebar.footing_sets((1, 1), (1, 0), 1.2, 1.2, 0.0, 0.5, f)
        self.assertEqual([len(s.bars) for s in mesh], [7, 7])
        self.assertAlmostEqual(rebar.BarSet.length_of(mesh[0].bars[0]), 2 * 0.544 + 0.30, places=6)
        self.assertGreater(mesh[1].bars[0][1][2], mesh[0].bars[0][1][2])        # (the second layer over the first)
        from shapely.geometry import Point, Polygon
        outline = [(0, 0), (6, 0), (6, 3), (3, 3), (3, 6), (0, 6)]
        s = ec2.Design("slab", mesh_x=(10, 0.20), mesh_y=(10, 0.20), cover=0.025)
        x_dir, lx, ly = rebar.slab_axes(outline)
        self.assertEqual((x_dir, lx, ly), ((1.0, 0.0), 6.0, 6.0))
        bars = rebar.slab_sets(outline, 3.0, 0.2, s, x_dir)
        inner = Polygon(outline).buffer(-0.025 + 1e-6, join_style=2)
        for st in bars:
            for b in st.bars:
                for p in b:
                    self.assertTrue(inner.covers(Point(p[0], p[1])))
        long_bars = [b for b in bars[0].bars if rebar.BarSet.length_of(b) > 5.0]
        self.assertTrue(long_bars and len(bars[0].groups()) == 2)                # (6 m and 3 m long: two positions)

    def test_slab_top(self):
        """0.224: a 6 × 4 m slab, 20 cm, on its four edge beams and one across it at x = 3 — its supports found
        (each edge beam's span inwards, none outwards; the middle one 3 m each side); its top bars Ø8//0,20: over
        the middle beam 0,2 × 3 m + its half width each side (1,40 m, straight), from each edge to 0,2 of the span
        past the beam's face and bent down 10 cm into the beam there; along x over the beams across x, along y over
        the others, these a layer under; all inside the slab less its cover, at its top."""
        from shapely.geometry import Point, Polygon
        from arqbim.core import ec2, rebar, structural as st
        from arqbim.model import structure_design as sd
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        cols = [st.Column("c{}".format(k), p, 0.0, 3.0, (0.3, 0.3)) for k, p in enumerate(corners)]
        beams = [st.Beam("b{}".format(k), corners[k], corners[(k + 1) % 4], 3.0, (0.25, 0.5)) for k in range(4)]
        beams.append(st.Beam("bx", (3.0, 0.0), (3.0, 4.0), 3.0, (0.2, 0.4)))
        panel = st.Panel("s", list(corners), 3.0, 0.2)
        model = st.build(cols, beams, [], [panel], levels=[0.0, 3.0])
        supports = sd.slab_supports(model, panel)
        self.assertEqual(len(supports), 7)
        middle = next(s for s in supports if abs(s[0] - 3.0) < 1e-9 and abs(s[2] - 3.0) < 1e-9)
        self.assertEqual((middle[4], middle[5], middle[6]), (0.1, 3.0, 3.0))
        edges = [s for s in supports if s is not middle]
        self.assertTrue(all(s[6] == 0.0 and s[5] in (3.0, 4.0) for s in edges))
        d = ec2.Design("slab", mesh_x=(8, 0.2), mesh_y=(8, 0.2), top_x=(8, 0.2), top_y=(8, 0.2), cover=0.025)
        sets = {s.role: s for s in rebar.slab_top_sets(corners, 3.0, 0.2, d, (1.0, 0.0), supports)}
        straight = [b for b in sets["top_x"].bars if len(b) == 2]
        self.assertEqual(len(straight), 19)
        self.assertAlmostEqual(rebar.BarSet.length_of(straight[0]), 2 * (0.2 * 3.0 + 0.1), places=6)
        self.assertAlmostEqual(straight[0][0][2], 3.0 - 0.025 - 0.004, places=6)
        bent = [b for b in sets["top_x"].bars if len(b) == 3]
        self.assertTrue(bent)
        b = bent[0]
        self.assertAlmostEqual(min(p[2] for p in b), 3.0 - 0.029 - 0.10, places=6)          # (its leg, down)
        flat = [p for p in b if abs(p[2] - (3.0 - 0.029)) < 1e-9]
        self.assertAlmostEqual(abs(flat[1][0] - flat[0][0]), 0.2 * 3.0 + 0.125 - 0.025, places=6)
        self.assertAlmostEqual(sets["top_y"].bars[0][1][2], 3.0 - 0.025 - 0.008 - 0.004, places=6)
        inner = Polygon(corners).buffer(-0.025 + 1e-6, join_style=2)
        for s in sets.values():
            self.assertEqual(s.kind, "MAIN")
            for bar in s.bars:
                self.assertTrue(all(inner.covers(Point(p[0], p[1])) for p in bar))

    def test_two_layers(self):
        """0.225: a beam's 5 Ø20 in two layers — 3 across its width, 2 over its corner ones by φ and the gap, their
        legs the shorter by it; kept with its bars (layers) and read back."""
        from arqbim.core import ec2, rebar
        from arqbim.model.structure_design import ElementDesign
        from arqbim.core.actions import Settings
        d = ec2.Design("beam", bottom=(5, 20), top=(2, 12), links=(8, 0.15), bottom2=2)
        bottom = {s.role: s for s in rebar.beam_sets((0, 0), (6, 0), 3.0, 0.2, 0.6, d, 25, 500)}["bottom"]
        self.assertEqual(len(bottom.bars), 5)
        low = 3.0 - 0.6 + 0.03 + 0.008 + 0.010
        levels = sorted(round(b[1][2], 6) for b in bottom.bars)
        shift = 0.020 + ec2.min_gap(20)
        self.assertEqual(levels, [round(low, 6)] * 3 + [round(low + shift, 6)] * 2)
        upper = [b for b in bottom.bars if abs(b[1][2] - low - shift) < 1e-6]
        lower = [b for b in bottom.bars if abs(b[1][2] - low) < 1e-6]
        self.assertEqual(sorted(round(b[1][1], 6) for b in upper),
                         [round(min(b[1][1] for b in lower), 6), round(max(b[1][1] for b in lower), 6)])
        self.assertAlmostEqual(upper[0][0][2] - upper[0][1][2], lower[0][0][2] - lower[0][1][2] - shift, places=6)
        stored = ElementDesign("g", "beam", d).stored(Settings())
        self.assertEqual(stored["layers"], [2, 0])
        back = rebar.design_from(stored)
        self.assertEqual((back.bottom, back.bottom2, back.top2), ((5, 20), 2, 0))

    def test_splices(self):
        """0.230: a 20 m bottom bar Ø16 bent up 0,30 m at each end, spliced: pieces no longer than the 12 m sold,
        each lap l0 = 1,5 lb,rqd (rounded up to 5 cm) long, the first piece keeping the bar's start and the last its
        end, every other piece a diameter beside; all the steel the bar's and its laps'; a 10 m bar as it was;
        links as they were."""
        from arqbim.core import ec2, rebar
        bar = [(0.0, 0.0, 0.3), (0.0, 0.0, 0.0), (20.0, 0.0, 0.0), (20.0, 0.0, 0.3)]
        st = rebar.BarSet("bottom", 16, [bar, [(0.0, 1.0, 0.0), (10.0, 1.0, 0.0)]])
        links = rebar.BarSet("stirrups", 8, [[(1.0, 0.0, 0.0), (1.0, 0.0, 0.5)]], 0.2)
        out = {s.role: s for s in rebar.spliced([st, links], 25, 500)}
        l0 = rebar.lap_length(16, 25, 500)
        self.assertAlmostEqual(l0, math.ceil(1.5 * ec2.bond_length(16, 25, 500) / 0.05 - 1e-9) * 0.05)
        pieces = [b for b in out["bottom"].bars if abs(b[0][1]) < 0.5]
        self.assertGreater(len(pieces), 1)
        self.assertTrue(all(rebar.BarSet.length_of(b) <= rebar.STOCK + 1e-9 for b in pieces))
        self.assertEqual(pieces[0][0], bar[0])
        self.assertAlmostEqual(pieces[-1][-1][0], 20.0)
        total = sum(rebar.BarSet.length_of(b) for b in pieces)
        self.assertAlmostEqual(total, rebar.BarSet.length_of(bar) + (len(pieces) - 1) * l0, places=6)
        self.assertAlmostEqual(abs(pieces[1][0][1] - pieces[0][-1][1]), 0.016, places=6)     # (beside it)
        self.assertEqual(len([b for b in out["bottom"].bars if abs(b[0][1] - 1.0) < 0.5]), 1)
        self.assertIs(out["stirrups"], links)

    def test_curtailed_bars(self):
        """0.229: a beam's bars that stop — of 4 Ø16 at the bottom, its 2 corner ones end to end (bent up at the
        supports), the other 2 straight from 1,5 to 4,5 m; of its top bars over its two supports, the extra one from
        each end into its support (bent down there) to 1,2 m and to 4,8 m."""
        from arqbim.core import ec2, rebar
        d = ec2.Design("beam", bottom=(4, 16), top=(3, 12), links=(8, 0.15), bottom_cont=2,
                       bottom_zones=[(1.5, 4.5)], top_cont=2, top_zones=[(0.0, 1.2), (4.8, 6.0)])
        sets = {s.role: s for s in rebar.beam_sets((0, 0), (6, 0), 3.0, 0.3, 0.5, d, 25, 500, (0.12, 0.12))}
        bottom, top = sets["bottom"].bars, sets["top"].bars
        whole = [b for b in bottom if len(b) == 4]
        short = [b for b in bottom if len(b) == 2]
        self.assertEqual((len(whole), len(short)), (2, 2))
        self.assertAlmostEqual(short[0][0][0], 1.5, places=6)
        self.assertAlmostEqual(short[0][1][0], 4.5, places=6)
        ys = sorted(round(b[1][1], 6) for b in whole)
        self.assertEqual(ys, sorted(round(b[1][1], 6) for b in whole))
        self.assertAlmostEqual(abs(ys[0]), abs(ys[1]))                            # (the two corner ones)
        ends = sorted((round(min(p[0] for p in b), 3), round(max(p[0] for p in b), 3)) for b in top if len(b) == 3)
        self.assertEqual(ends, [(-0.12, 1.2), (4.8, 6.12)])
        self.assertEqual(len([b for b in top if len(b) == 4]), 2)

    def test_positions(self):
        from arqbim.core import ec2, rebar
        beam = ec2.Design("beam", bottom=(2, 12), top=(2, 12), links=(8, 0.25))
        column = ec2.Design("column", bars=(4, 12), links=(8, 0.25))
        st = {s.role: s for s in rebar.beam_sets((0, 0), (4, 0), 3.0, 0.2, 0.4, beam, 25, 500)}["stirrups"]
        ti = {s.role: s for s in rebar.column_sets((0, 0), (1, 0), (0.15, 0.15), 0.0, 3.0, column, 25, 500)}["ties"]
        a, b = st.groups()[0], ti.groups()[0]
        self.assertAlmostEqual(a[1], b[1], delta=0.011)
        self.assertNotEqual(a[2], b[2])


class CabinetLayout(unittest.TestCase):
    """0.169: a 60 cm base unit with two doors — its two sides 72 cm tall on a 15 cm plinth, its bottom, two rails
    (the worktop goes on them), its back, a shelf, the plinth set back, two doors with 3 mm gaps and their bar
    handles, 4 hinges and 4 feet; its worktop at 87 cm (+3 cm: 90). A drawer unit: 3 drawer fronts, 3 runners, no
    shelf. A wall unit: a top instead of rails, no plinth, at 1,45 m. The cut list: equal panels together, in mm;
    sizes out of range refused; a 2,40 m run filled with modules of 60."""

    def test_base_unit(self):
        from arqbim.core import cabinets as cab
        c = cab.Cabinet.of("base", width=0.60, fronts="doors", doors=2)
        lay = cab.layout(c)
        roles = sorted(p.role for p in lay.panels)
        self.assertEqual(roles.count("side"), 2)
        self.assertEqual(roles.count("rail"), 2)
        self.assertEqual(roles.count("door"), 2)
        self.assertEqual(roles.count("handle"), 2)
        self.assertEqual(roles.count("plinth"), 1)
        self.assertEqual(roles.count("shelf"), 1)
        self.assertNotIn("top", roles)
        self.assertEqual(lay.hardware, {"hinge": 4, "handle": 2, "foot": 4})
        side = next(p for p in lay.panels if p.role == "side")
        self.assertAlmostEqual(side.box[2], 0.15, places=9)
        self.assertAlmostEqual(side.box[5], 0.87, places=9)
        self.assertEqual([round(v, 3) for v in side.cut()], [0.72, 0.56, 0.018])
        doors = sorted((p for p in lay.panels if p.role == "door"), key=lambda p: p.box[0])
        self.assertAlmostEqual(doors[0].box[3] - doors[0].box[0], 0.30 - cab.GAP, places=9)
        self.assertAlmostEqual(doors[1].box[0] - doors[0].box[3], cab.GAP, places=9)
        self.assertAlmostEqual(c.overall_depth, 0.003 + 0.56 + 0.018, places=9)
        self.assertIsNone(cab.validate(c))

    def test_other_units(self):
        from arqbim.core import cabinets as cab
        d = cab.layout(cab.Cabinet.of("base", fronts="drawers", drawers=3))
        self.assertEqual(sum(1 for p in d.panels if p.role == "drawer"), 3)
        self.assertEqual(sum(1 for p in d.panels if p.role == "shelf"), 0)
        self.assertEqual(d.hardware["runner"], 3)
        w = cab.Cabinet.of("wall")
        lay = cab.layout(w)
        self.assertIn("top", [p.role for p in lay.panels])
        self.assertNotIn("plinth", [p.role for p in lay.panels])
        self.assertAlmostEqual(min(p.box[2] for p in lay.panels), 1.45, places=9)
        self.assertAlmostEqual(w.top, 2.17, places=9)
        self.assertAlmostEqual(cab.Cabinet.of("tall").top, 2.17, places=9)     # (its top with the wall units')
        self.assertEqual(cab.validate(cab.Cabinet.of("base", width=2.0)), "cabinet_size")
        self.assertEqual(cab.fill(2.40), [0.60] * 4)
        self.assertEqual(cab.fill(2.85), [0.60] * 4 + [0.45])
        self.assertEqual(cab.fill(2.75), [0.60] * 4 + [0.30])
        rows = cab.cut_list([cab.layout(cab.Cabinet.of("base")), cab.layout(cab.Cabinet.of("base"))])
        sides = next(r for r in rows if r[0] == "side")
        self.assertEqual(sides[5], 4)                                    # (two cabinets: four equal sides)
        self.assertEqual(round(sides[2] * 1000), 720)
        self.assertNotIn("handle", [r[0] for r in rows])


class CabinetDivisions(unittest.TestCase):
    """0.172: a wardrobe of 1 m — 2,40 m tall on its plinth of 10 cm, two doors — with two compartments: a division
    between them (each 47,3 cm), the left one with a hat shelf and the hanging rail under it, the right one with four
    shelves; three compartments with inner drawers: 3 runners each; compartments under 15 cm refused; an unknown fill
    refused."""

    def test_wardrobe(self):
        from arqbim.core import cabinets as cab
        w = cab.Cabinet.of("wardrobe")
        self.assertAlmostEqual(w.top, 2.40, places=9)
        lay = cab.layout(w)
        roles = [p.role for p in lay.panels]
        self.assertEqual(roles.count("division"), 1)
        self.assertEqual(roles.count("door"), 2)
        self.assertEqual(roles.count("hanger"), 1)
        self.assertEqual(roles.count("shelf"), 1 + 4)
        self.assertEqual(lay.hardware["hanger"], 1)
        division = next(p for p in lay.panels if p.role == "division")
        self.assertAlmostEqual(division.box[0], cab.BOARD + (1.0 - 3 * cab.BOARD) / 2, places=9)
        rail = next(p for p in lay.panels if p.role == "hanger")
        self.assertLess(rail.box[3], division.box[0] + 1e-9)            # (in the left compartment)
        drawers = cab.layout(cab.Cabinet.of("wardrobe", width=1.2, interior="drawers,drawers,shelves"))
        self.assertEqual(drawers.hardware["runner"], 6)
        self.assertEqual(sum(1 for p in drawers.panels if p.role == "inner_drawer"), 6)
        self.assertEqual(cab.validate(cab.Cabinet.of("base", width=0.40, interior="shelves,shelves,shelves")),
                         "cabinet_size")
        self.assertEqual(cab.validate(cab.Cabinet.of("base", interior="shelves,sofa")), "cabinet_bad")
        rows = cab.cut_list([lay])
        self.assertIn("division", [r[0] for r in rows])
        self.assertNotIn("hanger", [r[0] for r in rows])


class KitchenRuns(unittest.TestCase):
    """0.170: a kitchen in L along two walls (3 m, then 2,4 m up the other, the room inside): the first leg filled
    with five modules of 60 to the corner, the second starting clear of their depth (58,1 cm) with three; facing the
    room; the room on the right turns them round; the worktop's two pieces (3,00 × 0,60 and 1,80 × 0,60), its
    outline an L."""

    def test_l_kitchen(self):
        from shapely.geometry import Polygon
        from arqbim.core import cabinets as cab
        from arqbim.core import kitchens
        pts = [(0.0, 0.0), (3.0, 0.0), (3.0, 2.4)]
        mods = kitchens.run_modules(pts, side=1)
        depth = cab.Cabinet.of("base").overall_depth
        first = [m for m in mods if abs(m[1]) < 1e-6]
        second = [m for m in mods if abs(m[1] - 90.0) < 1e-6]
        self.assertEqual(len(first), 5)
        self.assertEqual(len(second), 3)
        self.assertAlmostEqual(first[-1][0][0] + 0.30, 3.0, places=9)        # (the last one at the corner)
        self.assertAlmostEqual(second[0][0][1] - 0.30, depth, places=9)      # (the next one clear of its depth)
        other = kitchens.run_modules([(0.0, 0.0), (3.0, 0.0)], side=-1)
        self.assertTrue(all(abs(m[1] - 180.0) < 1e-6 for m in other))
        spots = [(m[0], m[1], m[2], depth) for m in mods]
        outline, pieces = kitchens.worktop(spots)
        self.assertEqual(sorted((round(a, 3), round(b, 3)) for a, b in pieces),
                         [(1.8, round(depth + kitchens.OVERHANG, 3)), (3.0, round(depth + kitchens.OVERHANG, 3))])
        poly = Polygon(outline)
        self.assertEqual(len(outline), 6)                                    # (an L)
        self.assertAlmostEqual(poly.area, (3.0 + 1.8) * (depth + kitchens.OVERHANG)
                               - 0.0, delta=0.05)


class BlindCorners(unittest.TestCase):
    """0.239: a blind corner base unit of 1,00 m — its 63 cm on the corner side a blind panel (the other run's depth
    and 5 cm), a door of 37 cm beside it opening away from the corner (its handle by the panel), its shelves the
    whole width; the other way round on its left; one leaving a door under 25 cm refused. In a kitchen in L the
    first run's last module is one, flush in the corner (three of 60 before it), the second run starting as
    before, the wall units' corner one of 0,80; the worktop still an L."""

    def test_blind(self):
        from shapely.geometry import Polygon
        from arqbim.core import cabinets as cab
        from arqbim.core import kitchens
        depth = cab.Cabinet.of("base").overall_depth
        blind = cab.corner_blind(depth)
        self.assertAlmostEqual(blind, depth + cab.CORNER_CLEAR, places=9)
        width = cab.corner_width(blind)
        self.assertAlmostEqual(width, 1.00, places=9)
        c = cab.Cabinet.of("base", width=width, doors=2, blind=blind, corner_side="right")
        self.assertIsNone(cab.validate(c))
        lay = cab.layout(c)
        panel = [p for p in lay.panels if p.role == "blind"]
        doors = [p for p in lay.panels if p.role == "door"]
        self.assertEqual((len(panel), len(doors)), (1, 1))
        self.assertAlmostEqual(panel[0].box[3], width - cab.GAP / 2, places=9)
        self.assertAlmostEqual(panel[0].box[3] - panel[0].box[0], blind - cab.GAP, places=9)
        self.assertAlmostEqual(doors[0].box[3] - doors[0].box[0], width - blind - cab.GAP, places=9)
        handle = next(p for p in lay.panels if p.role == "handle")
        self.assertGreater(handle.box[0], doors[0].box[3] - 0.06)        # (by the panel: away from the hinges)
        shelf = next(p for p in lay.panels if p.role == "shelf")
        self.assertGreater(shelf.box[3] - shelf.box[0], width - 2 * cab.BOARD - 0.01)
        self.assertEqual(lay.hardware["hinge"], 2)
        left = cab.layout(cab.Cabinet.of("base", width=width, blind=blind, corner_side="left"))
        lp = next(p for p in left.panels if p.role == "blind")
        ld = next(p for p in left.panels if p.role == "door")
        lh = next(p for p in left.panels if p.role == "handle")
        self.assertAlmostEqual(lp.box[0], cab.GAP / 2, places=9)
        self.assertLess(lh.box[3], ld.box[0] + 0.06)
        self.assertEqual(cab.validate(cab.Cabinet.of("base", width=0.60, blind=0.45)), "cabinet_blind")
        self.assertEqual(cab.validate(cab.Cabinet.of("tall", blind=0.30)), "cabinet_blind")
        # the kitchen in L: the first run's last module a blind corner, flush in the corner
        pts = [(0.0, 0.0), (3.0, 0.0), (3.0, 2.4)]
        mods = kitchens.run_modules(pts, side=1, corners=True)
        first = [m for m in mods if abs(m[1]) < 1e-6]
        second = [m for m in mods if abs(m[1] - 90.0) < 1e-6]
        self.assertEqual([round(m[2], 2) for m in first], [0.6, 0.6, 0.6, 1.0])
        self.assertAlmostEqual(first[-1][0][0] + 0.50, 3.0, places=9)
        self.assertAlmostEqual(first[-1][3], blind, places=9)
        self.assertEqual(first[-1][4], "right")
        self.assertTrue(all(m[3] == 0.0 for m in mods if m is not first[-1]))
        self.assertAlmostEqual(second[0][0][1] - 0.30, depth, places=9)
        self.assertEqual(len(kitchens.run_modules(pts, side=1)[0]), 3)    # (without corners: as before)
        walls = kitchens.run_modules(pts, side=1, kind="wall", corners=True)
        corner = [m for m in walls if m[3] > 0]
        self.assertEqual(len(corner), 1)
        self.assertAlmostEqual(corner[0][2], 0.80, places=9)
        turned = kitchens.run_modules([(3.0, 2.4), (3.0, 0.0), (0.0, 0.0)], side=-1, corners=True)
        self.assertEqual([m[4] for m in turned if m[3] > 0], ["left"])     # (the room on its right: turned round)
        outline, _pieces = kitchens.worktop([(m[0], m[1], m[2], depth) for m in mods])
        self.assertEqual(len(outline), 6)                                    # (from 0,20: what is left by the wall)
        self.assertAlmostEqual(Polygon(outline).area, (2.8 + 1.8) * (depth + kitchens.OVERHANG), delta=0.05)


class LCorners(unittest.TestCase):
    """0.240: an L corner unit of 90 × 90 cm with a carousel — a door on each arm meeting at the inner corner (33,4
    and 31,6 cm), its two trays three quarters of a disc round that corner (none in the room's quarter), four hinges,
    one handle by the first door's free edge, its trays not in the cut list; turned over for a corner on the left;
    a carousel without an L, or arms too short for a door, refused. A kitchen in L with L corners: the first run
    ending in one (its arm 90 cm round the corner, the next run starting past it), the wall units' of 65 cm; the
    worktop an L, its second piece from the first's edge."""

    def test_l_corner(self):
        from shapely.geometry import Polygon
        from arqbim.core import cabinets as cab
        from arqbim.core import kitchens
        c = cab.Cabinet.of("base", width=0.90, arm=0.90, corner_side="right", interior="carousel")
        self.assertIsNone(cab.validate(c))
        lay = cab.layout(c)
        doors = [p for p in lay.panels if p.role == "door"]
        self.assertEqual(len(doors), 2)
        x0 = 0.90 - cab.BACK - c.depth
        y1 = cab.BACK + c.depth
        self.assertAlmostEqual(doors[0].sizes[0], x0 - cab.GAP, places=9)
        self.assertAlmostEqual(doors[1].sizes[1], 0.90 - y1 - cab.FRONT - cab.GAP, places=9)
        trays = [p for p in lay.panels if p.role == "carousel"]
        self.assertEqual(len(trays), cab.CAROUSEL_TRAYS)
        r = min(x0 - cab.BOARD, 0.90 - cab.BOARD - y1, c.depth) - cab.CAROUSEL_CLEAR
        self.assertAlmostEqual(trays[0].sizes[0], 2 * r, places=9)
        ring = cab.carousel_ring(trays[0], "right")
        cx, cy = ring[0]
        self.assertAlmostEqual(cx, x0, places=9)
        self.assertAlmostEqual(cy, y1, places=9)
        self.assertFalse(any(x < cx - 1e-6 and y > cy + 1e-6 for x, y in ring))     # (the room's quarter cut)
        self.assertAlmostEqual(Polygon(ring).area, 0.75 * math.pi * r * r, delta=0.01)
        self.assertEqual((lay.hardware["hinge"], lay.hardware["carousel"], lay.hardware["handle"]), (4, 1, 1))
        handle = next(p for p in lay.panels if p.role == "handle")
        self.assertLess(handle.box[3], 0.06)                                        # (by the free edge)
        self.assertFalse(any(row[0] == "carousel" for row in cab.cut_list([lay])))
        left = cab.layout(cab.Cabinet.of("base", width=0.90, arm=0.90, corner_side="left", interior="carousel"))
        lt = next(p for p in left.panels if p.role == "carousel")
        self.assertAlmostEqual((lt.box[0] + lt.box[3]) / 2, 0.90 - x0, places=9)
        lring = cab.carousel_ring(lt, "left")
        self.assertFalse(any(x > lring[0][0] + 1e-6 and y > lring[0][1] + 1e-6 for x, y in lring))
        self.assertGreater(next(p for p in left.panels if p.role == "handle").box[0], 0.84)
        self.assertEqual(cab.validate(cab.Cabinet.of("base", interior="carousel")), "cabinet_corner")
        self.assertEqual(cab.validate(cab.Cabinet.of("base", width=0.70, arm=0.90)), "cabinet_corner")
        self.assertIsNone(cab.validate(cab.Cabinet.of("wall", width=0.65, arm=0.65)))
        # the kitchen in L with L corners
        pts = [(0.0, 0.0), (3.0, 0.0), (3.0, 2.4)]
        mods = kitchens.run_modules(pts, side=1, corners="l")
        first = [m for m in mods if abs(m[1]) < 1e-6]
        second = [m for m in mods if abs(m[1] - 90.0) < 1e-6]
        self.assertEqual([round(m[2], 2) for m in first], [0.6, 0.6, 0.6, 0.3, 0.9])
        self.assertEqual((round(first[-1][5], 2), first[-1][4], first[-1][3]), (0.9, "right", 0.0))
        self.assertEqual([round(m[2], 2) for m in second], [0.6, 0.6, 0.3])
        self.assertAlmostEqual(second[0][0][1], 0.9 + 0.3, places=9)                 # (past the L's arm)
        walls = kitchens.run_modules(pts, side=1, kind="wall", corners="l")
        self.assertEqual([round(m[5], 2) for m in walls if m[5]], [0.65])
        depth = cab.Cabinet.of("base").overall_depth
        outline, pieces = kitchens.worktop([(m[0], m[1], m[2], depth, m[5], m[4]) for m in mods])
        self.assertEqual(len(outline), 6)
        d = depth + kitchens.OVERHANG
        self.assertEqual(sorted(round(a, 2) for a, _b in pieces), [round(2.4 - d, 2), 3.0])
        self.assertAlmostEqual(Polygon(outline).area, (3.0 + 2.4 - d) * d, delta=0.01)


class SlidingDoors(unittest.TestCase):
    """0.241: a wardrobe of 1,80 m with two sliding doors — each (1,80 + 0,03) / 2 wide, one on each track (the back
    one first), lapped 3 cm in the middle; its tracks over and under them (not in the cut list), a track set and no
    hinges; a pull by each one's free edge; its depth out to the tracks' (and the plinth set back from them); three
    doors over 2,40 m; one door is two; doors under 30 cm refused."""

    def test_sliding(self):
        from arqbim.core import cabinets as cab
        c = cab.Cabinet.of("wardrobe", width=1.80, fronts="sliding", doors=2)
        self.assertIsNone(cab.validate(c))
        self.assertAlmostEqual(c.overall_depth, cab.BACK + c.depth + cab.SLIDE_TRACK, places=9)
        lay = cab.layout(c)
        doors = [p for p in lay.panels if p.role == "sliding_door"]
        self.assertEqual(len(doors), 2)
        dw = (1.80 + cab.SLIDE_OVERLAP) / 2
        self.assertTrue(all(abs(d.sizes[0] - dw) < 1e-9 for d in doors))
        self.assertAlmostEqual(doors[0].box[3] - doors[1].box[0], cab.SLIDE_OVERLAP, places=9)    # (lapped)
        self.assertLess(doors[0].box[1], doors[1].box[1])                       # (the first on the back track)
        self.assertGreaterEqual(doors[1].box[1], doors[0].box[4])               # (…the second clear in front of it)
        self.assertEqual(sum(1 for p in lay.panels if p.role == "track"), 2)
        self.assertNotIn("hinge", lay.hardware)
        self.assertEqual((lay.hardware["slide"], lay.hardware["handle"]), (1, 2))
        handles = [p for p in lay.panels if p.role == "handle"]
        self.assertLess(handles[0].box[0], 0.06)
        self.assertGreater(handles[1].box[3], 1.80 - 0.06)
        rows = cab.cut_list([lay])
        self.assertFalse(any(r[0] == "track" for r in rows))
        self.assertTrue(any(r[0] == "sliding_door" for r in rows))
        plinth = next(p for p in lay.panels if p.role == "plinth")
        self.assertAlmostEqual(plinth.box[4], cab.BACK + c.depth + cab.SLIDE_TRACK - cab.PLINTH_SET_BACK, places=9)
        three = cab.layout(cab.Cabinet.of("wardrobe", width=2.40, fronts="sliding", doors=3))
        self.assertEqual(sum(1 for p in three.panels if p.role == "sliding_door"), 3)
        one = cab.layout(cab.Cabinet.of("wardrobe", width=1.20, fronts="sliding", doors=1))
        self.assertEqual(sum(1 for p in one.panels if p.role == "sliding_door"), 2)
        self.assertEqual(cab.validate(cab.Cabinet.of("wardrobe", width=1.00, fronts="sliding", doors=4)),
                         "cabinet_sliding")


class OvenHousing(unittest.TestCase):
    """0.242: a tall unit of 60 cm with an oven housing — a fixed shelf under the oven (its top at 86 cm) and one
    over its 60 cm opening, two drawers under it, a door over it with its handle low, its shelves behind that door
    only; the oven's casing between the unit's sides (its door over them) at the housing's height; a base unit or
    one too narrow refused; the housed oven not among the appliances put by hand."""

    def test_oven(self):
        from arqbim.core import appliances as app
        from arqbim.core import cabinets as cab
        c = cab.Cabinet.of("tall", width=0.60, fronts="oven", shelves=1)
        self.assertIsNone(cab.validate(c))
        lay = cab.layout(c)
        shelves = sorted(p.box[2] for p in lay.panels if p.role == "shelf")
        self.assertAlmostEqual(shelves[0], cab.OVEN_SILL - cab.BOARD, places=9)
        self.assertAlmostEqual(shelves[1], cab.OVEN_SILL + cab.OVEN_NICHE, places=9)
        self.assertEqual(len(shelves), 3)                                     # (and one behind the door)
        self.assertGreater(shelves[2], cab.OVEN_SILL + cab.OVEN_NICHE)
        drawers = [p for p in lay.panels if p.role == "drawer"]
        door = next(p for p in lay.panels if p.role == "door")
        self.assertEqual(len(drawers), cab.OVEN_DRAWERS)
        self.assertLess(max(d.box[5] for d in drawers), cab.OVEN_SILL)
        self.assertGreater(door.box[2], cab.OVEN_SILL + cab.OVEN_NICHE)
        handle = [p for p in lay.panels if p.role == "handle"][-1]
        self.assertLess(handle.box[2], door.box[2] + 0.30)                    # (low on the door)
        self.assertEqual((lay.hardware["runner"], lay.hardware["hinge"], lay.hardware["handle"]), (2, 2, 3))
        boxes = app.boxes("oven_column")
        self.assertAlmostEqual(boxes[0][0], 0.02, places=9)                    # (its casing inside the sides)
        self.assertAlmostEqual(boxes[0][2], cab.OVEN_SILL, places=9)
        self.assertEqual(cab.validate(cab.Cabinet.of("base", fronts="oven")), "cabinet_oven")
        self.assertEqual(cab.validate(cab.Cabinet.of("tall", width=0.50, fronts="oven")), "cabinet_oven")
        self.assertIn("oven_column", app.HOUSED)


class FrontFinishes(unittest.TestCase):
    """0.243: a base unit's fronts of oak — every front (doors, drawers; a blind corner's panel, sliding doors, an L's
    doors) of the oak front material, its carcass still of board; the cut list its fronts apart; melamine: "front";
    a finish that does not exist refused."""

    def test_finishes(self):
        from arqbim.core import cabinets as cab
        oak = cab.Cabinet.of("base", width=0.60, fronts="door_drawer", finish="oak")
        self.assertIsNone(cab.validate(oak))
        lay = cab.layout(oak)
        fronts = [p for p in lay.panels if p.role in ("door", "drawer")]
        self.assertEqual({p.material for p in fronts}, {"front_oak"})
        self.assertEqual({p.material for p in lay.panels if p.role == "side"}, {"carcass"})
        self.assertTrue(any(r[1] == "front_oak" for r in cab.cut_list([lay])))
        for c in (cab.Cabinet.of("base", width=1.0, blind=0.63, finish="walnut"),
                  cab.Cabinet.of("wardrobe", width=1.8, fronts="sliding", finish="walnut"),
                  cab.Cabinet.of("base", width=0.9, arm=0.9, finish="walnut")):
            self.assertEqual({p.material for p in cab.layout(c).panels if p.role in ("door", "blind", "sliding_door")},
                             {"front_walnut"})
        plain = cab.layout(cab.Cabinet.of("base"))
        self.assertEqual({p.material for p in plain.panels if p.role == "door"}, {"front"})
        self.assertEqual(cab.validate(cab.Cabinet.of("base", finish="gold")), "cabinet_bad")


class CompartmentWidths(unittest.TestCase):
    """0.244: a wardrobe of 1,20 m with two compartments — even (59,1 cm each) until its division is placed at
    45 cm: compartments of 41,1 and 73,1 cm, the division and their shelves there; a division leaving one under
    15 cm refused; a placed one ignored when the compartments are not as many (even again); a drawer unit has
    none."""

    def test_widths(self):
        from arqbim.core import cabinets as cab
        c = cab.Cabinet.of("wardrobe", width=1.20, interior="shelves,shelves", shelves=2)
        self.assertAlmostEqual(c.divisions[0], 0.60, places=9)
        spans = c.compartment_spans()
        self.assertAlmostEqual(spans[0][1] - spans[0][0], (1.20 - 3 * cab.BOARD) / 2, places=9)
        placed = cab.Cabinet.of("wardrobe", width=1.20, interior="shelves,shelves", shelves=2, splits="0.45")
        self.assertIsNone(cab.validate(placed))
        a, b = placed.compartment_spans()
        self.assertAlmostEqual(a[1] - a[0], 0.45 - cab.BOARD - cab.BOARD / 2, places=9)
        self.assertAlmostEqual(b[1] - b[0], 1.20 - cab.BOARD - 0.45 - cab.BOARD / 2, places=9)
        lay = cab.layout(placed)
        division = next(p for p in lay.panels if p.role == "division")
        self.assertAlmostEqual((division.box[0] + division.box[3]) / 2, 0.45, places=9)
        shelves = sorted((p.box[0], p.box[3]) for p in lay.panels if p.role == "shelf")
        self.assertAlmostEqual(shelves[0][1], a[1] - 0.001, places=9)
        self.assertEqual(cab.validate(cab.Cabinet.of("wardrobe", width=1.20, interior="shelves,shelves",
                                                     splits="0.15")), "cabinet_size")
        three = cab.Cabinet.of("wardrobe", width=1.20, interior="shelves,shelves,rail", splits="0.45")
        self.assertEqual(len(three.divisions), 2)
        self.assertAlmostEqual(three.divisions[0], cab.Cabinet.of("wardrobe", width=1.20,
                                                                  interior="shelves,shelves,rail").divisions[0])
        self.assertEqual(cab.Cabinet.of("base", fronts="drawers", interior="shelves,shelves").divisions, [])


class OwnProfiles(unittest.TestCase):
    """0.245: a section drawn (an L of 4 × 6 cm, clockwise) put in a unit square counter-clockwise, its (0, 0) at its
    corner by the wall's foot, its size kept; swept at another size; a project's own profile a wooden moulding on
    the floor; a line or one too big refused."""

    def test_own(self):
        from arqbim.core import profiles as pr
        drawn = [(1.0, 2.0), (1.0, 2.06), (1.01, 2.06), (1.01, 2.01), (1.04, 2.01), (1.04, 2.0)][::-1]
        unit, w, h = pr.unit_section(drawn)
        self.assertAlmostEqual(w, 0.04, places=9)
        self.assertAlmostEqual(h, 0.06, places=9)
        x, y = np.array(unit).T
        self.assertGreater(float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y)), 0.0)   # (counter-clockwise)
        self.assertAlmostEqual(min(x), 0.0, places=9)
        self.assertAlmostEqual(max(y), 1.0, places=9)
        sec = pr.section("custom:L", 0.08, 0.12, custom=unit)
        self.assertAlmostEqual(max(a for a, _b in sec), 0.08, places=9)
        self.assertEqual(pr.spec("custom:L"), ("MOLDING", "madeira"))
        self.assertEqual(pr.foot("custom:L", 0.12, 3.0), 0.0)
        self.assertTrue(pr.is_custom("custom:L") and not pr.is_custom("rodape"))
        with self.assertRaises(ValueError):
            pr.unit_section([(0.0, 0.0), (0.05, 0.0), (0.10, 0.0)])
        with self.assertRaises(ValueError):
            pr.unit_section([(0.0, 0.0), (0.9, 0.0), (0.9, 0.1), (0.0, 0.1)])


class CurvedTeeJoint(unittest.TestCase):
    """0.246: a straight wall (20 cm) at 45° to a curved wall's side (its axis 3 m round the origin, 20 cm): from
    outside, its end on the outer face (both corners on the 3,10 m circle, the axis end at √(3,1² − 0,1²), the cut
    turned to the centre); from inside, on the inner face; along the arc, or past its ends: none."""

    def test_tee(self):
        from arqbim.core.curved_joints import straight_end, tee
        u = np.array((math.cos(math.pi / 4), math.sin(math.pi / 4), 0.0))
        found = tee(straight_end(u * 3.0, u, 0.20), (0.0, 0.0), 3.0, 0.20, 0.0, math.pi / 2)
        self.assertIsNotNone(found)
        point, normal = found
        self.assertAlmostEqual(float(np.linalg.norm(point[:2])), math.sqrt(3.1 ** 2 - 0.1 ** 2), places=9)
        self.assertTrue(np.allclose(normal, -u))
        inside = tee(straight_end(u * 2.8, -u, 0.20), (0.0, 0.0), 3.0, 0.20, 0.0, math.pi / 2)
        self.assertAlmostEqual(float(np.linalg.norm(inside[0][:2])), math.sqrt(2.9 ** 2 - 0.1 ** 2), places=9)
        self.assertTrue(np.allclose(inside[1], u))
        along = np.array((-u[1], u[0], 0.0))
        self.assertIsNone(tee(straight_end(u * 3.0, along, 0.20), (0.0, 0.0), 3.0, 0.20, 0.0, math.pi / 2))
        v = np.array((math.cos(math.radians(120)), math.sin(math.radians(120)), 0.0))
        self.assertIsNone(tee(straight_end(v * 3.0, v, 0.20), (0.0, 0.0), 3.0, 0.20, 0.0, math.pi / 2))
        self.assertIsNotNone(tee(straight_end(v * 3.0, v, 0.20), (0.0, 0.0), 3.0, 0.20))   # (a whole circle)


class CombinedFootingDesign(unittest.TestCase):
    """0.250: a combined footing 4,20 × 1,50 × 0,70 under two columns 3 m apart, 700 kN each (ULS; 500 service), soil
    300 kPa: the soil's pressure; along it, as a beam on the soil, the hogging between them N (L/4 − s/2) = 315 kNm
    (top bars) and the sagging by them q · 0,6² / 2 = 60 kNm (bottom bars); across, the bands' bars; its shear and
    punching checked. Loads too big for the soil: told how wide. The top bars laid along it, bent down, under the
    top cover."""

    def test_combined(self):
        from arqbim.core import ec2
        from arqbim.core import rebar as rb
        cols = [(-1.5, 0.30, 0.30, 700.0, 500.0), (1.5, 0.30, 0.30, 700.0, 500.0)]
        d = ec2.combined_footing(4.2, 1.5, 0.7, cols, 25, 500, soil=300.0)
        self.assertNotEqual(d.status, ec2.FAIL, [n.code for n in d.notes])
        moments = next(n for n in d.notes if n.code == "combined_moments").values
        self.assertAlmostEqual(moments["m_neg"], 700.0 * (3.0 / 2 - 4.2 / 4), delta=0.5)      # (its size)
        self.assertAlmostEqual(moments["m_pos"], 1400.0 / 4.2 * 0.6 ** 2 / 2, delta=1.0)
        self.assertIsNotNone(d.top_x)
        self.assertIsNotNone(d.mesh_x)
        self.assertIsNotNone(d.mesh_y)
        self.assertTrue(any(n.code == "combined_shear" for n in d.notes))
        self.assertTrue(any(n.code.startswith("punching") for n in d.notes))
        heavy = ec2.combined_footing(4.2, 1.5, 0.6, [(-1.5, 0.3, 0.3, 2800, 2000), (1.5, 0.3, 0.3, 2800, 2000)], 25,
                                     500, soil=300.0)
        self.assertEqual(heavy.status, ec2.FAIL)
        fail = next(n for n in heavy.notes if n.code == "combined_bearing_fail")
        self.assertGreater(fail.values["width"], 1.5)
        sets = rb.footing_sets((0.0, 0.0), (1.0, 0.0), 4.2, 1.5, 0.0, 0.7, d)
        top = next(s for s in sets if s.role == "top_x")
        bar = np.asarray(top.bars[0])
        self.assertAlmostEqual(float(bar[1][2]), -d.cover - d.top_x[0] / 2000.0, places=9)   # (under the top cover)
        self.assertLess(float(bar[0][2]), float(bar[1][2]))                                 # (bent down)


class DrawnRoofSection(unittest.TestCase):
    """0.251: a drawn roof section put from its lowest, leftmost point; its underside and top across a span it is
    centred on (none past its ends); one too narrow or with no area refused."""

    def test_section(self):
        from arqbim.core import roofs
        sec = roofs.custom_section([(1.0, 2.0), (8.0, 2.0), (8.0, 2.2), (4.5, 3.5), (1.0, 2.2)])
        self.assertEqual(min(x for x, _y in sec), 0.0)
        self.assertEqual(min(y for _x, y in sec), 0.0)
        low, top = roofs.section_heights(sec, 7.0, 3.5)
        self.assertAlmostEqual(low, 0.0, places=9)
        self.assertAlmostEqual(top, 1.5, places=9)
        self.assertAlmostEqual(roofs.section_heights(sec, 9.0, 1.0)[1], 0.2, places=9)   # (span 9: 1 m in = its edge)
        self.assertIsNone(roofs.section_heights(sec, 9.0, 0.5))
        with self.assertRaises(ValueError):
            roofs.custom_section([(0.0, 0.0), (0.3, 0.0), (0.3, 0.2), (0.0, 0.2)])
        with self.assertRaises(ValueError):
            roofs.custom_section([(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)])
        self.assertIn("custom", roofs.EXTRUDED)


class StairWaist(unittest.TestCase):
    """0.256: a flight of 16 risers of 17,5 cm, treads of 28 cm, a 15 cm waist: the slab under the steps 15 cm thick
    square to the slope from every inner corner of riser and tread (it was none: measured from the nosings); its
    foot on the floor; from a landing, down to the landing's underside; going into a landing, on until the two
    undersides meet."""

    def test_waist(self):
        from arqbim.core import stairs
        n, h, g, t = 16, 0.175, 0.28, 0.15
        side = stairs.flight_side(n, h, g, t)
        slope = h / g
        norm = math.hypot(1.0, slope)
        under = [p for p in side if p[1] < 1e-9 or p[0] > (n - 1) * g + 1e-9]

        def below_line(x, z):                     # (how far under the point the underside is, square to it)
            return (z - (slope * x - t * norm)) / norm

        for k in range(1, n):                     # (each inner corner: 15 cm of slab under it)
            self.assertAlmostEqual(below_line(k * g, k * h), t, places=9)
        self.assertAlmostEqual(min(z for _x, z in side), 0.0, places=9)             # (on the floor)
        self.assertTrue(under)
        landing = stairs.flight_side(8, h, g, t, z0=1.4, below=t)
        self.assertAlmostEqual(min(z for _x, z in landing), 1.4 - t, places=9)       # (from the landing's underside)
        # (0.257) the landing made with it: 1 m past its last riser, t thick, the undersides meeting
        into = stairs.flight_side(8, h, g, t, ahead=1.0)
        top = 8 * h
        meet = (top - t + t * norm) / slope
        for corner in ((7 * g + 1.0, top), (7 * g + 1.0, top - t), (meet, top - t)):
            self.assertTrue(any(math.hypot(x - corner[0], z - corner[1]) < 1e-9 for x, z in into), corner)
        back = stairs.flight_side(8, h, g, t, z0=1.4, below=t, behind=1.0)          # (a U's second: its part of it)
        self.assertAlmostEqual(min(x for x, _z in back), -1.0, places=9)
        self.assertTrue(any(math.hypot(x + 1.0, z - 1.4) < 1e-9 for x, z in back))


class RoofBlocks(unittest.TestCase):
    """0.262: roofs by blocks — one hip block 10 × 6 m (30°, no overhang): four waters, 1,73 m up at its middle, its
    eave at 0, its projected area 60 m² and its true one 60 / cos 30°; two blocks across each other (an L): at every
    point the higher of the two; more waters than one block's, the valleys between; a higher block's overhang
    over a lower one leaves the lower roof running on under it — (two overhangs over each other, out of both
    blocks: only the higher); the text read back; a block mirrored (N and S swapped); the forms; where a line
    crosses the ridge; (0.264) a turned block's side's way, a side taken out and in (the opposite one staying)."""

    def test_blocks(self):
        from shapely.geometry import Point
        from arqbim.core import roof_blocks as rb
        t30 = math.tan(math.radians(30))
        one = rb.make(5.0, 3.0, 0.0, 10.0, 6.0, "hip", 30.0, 0.0)
        regions = rb.regions([one])
        self.assertEqual(len(regions), 4)
        self.assertAlmostEqual(rb.height_at([one], 5.0, 3.0), 3.0 * t30, places=9)
        self.assertAlmostEqual(rb.height_at([one], 5.0, 6.0), 0.0, places=9)
        self.assertIsNone(rb.height_at([one], 20.0, 3.0))
        projected = sum(g.area for _c, g in regions)
        true = sum(g.area * math.sqrt(1 + c[0] ** 2 + c[1] ** 2) for c, g in regions)
        self.assertAlmostEqual(projected, 60.0, places=6)
        self.assertAlmostEqual(true, 60.0 / math.cos(math.radians(30)), places=6)
        other = rb.make(8.0, 6.0, 0.0, 4.0, 8.0, "gable", 30.0, 0.0)                 # (across it: an L)
        both = [one, other]
        for x, y in ((8.0, 8.0), (8.0, 4.0), (6.5, 5.0), (9.5, 2.5), (2.0, 3.0)):
            tops = [z for z in (rb.height_at([b], x, y) for b in both) if z is not None]
            self.assertAlmostEqual(rb.height_at(both, x, y), max(tops), places=9, msg=(x, y))
        regions = rb.regions(both)
        self.assertGreater(len(regions), 4)
        plan = sum(g.area for _c, g in regions)
        self.assertAlmostEqual(plan, rb.footprint(both).area, places=4)               # (no overlap, no gap)
        low = rb.make(0.0, 0.0, 0.0, 6.0, 6.0, "hip", 30.0, 0.5)
        high = rb.replace(rb.make(5.0, 0.0, 0.0, 4.0, 4.0, "hip", 30.0, 0.5), eave=(1.0,) * 4)
        regions = rb.regions([low, high])
        under = Point(2.8, 0.0)                                         # (in the higher's overhang, over the lower)
        low_planes = set(rb.planes(low).values())
        self.assertTrue(any(c in low_planes and g.buffer(1e-9).contains(under) for c, g in regions))
        main = rb.make(5.0, 3.0, 0.0, 10.0, 6.0, "hip", 30.0, 0.5)                    # (an L flush on the east)
        wing = rb.make(8.0, 7.0, 0.0, 4.0, 6.0, "gable", 30.0, 0.5)
        corner = Point(10.3, 6.4)                       # (in both overhangs: only the higher — the wing's east water)
        tops = [c for c, g in rb.regions([main, wing]) if g.buffer(-1e-6).contains(corner)]
        self.assertEqual(tops, [rb.planes(wing)["E"]])
        back = rb.from_text(rb.to_text(both))
        self.assertEqual(back, both)
        from arqbim.ifc.mirror import reflection
        flipped = rb.mirrored(other, reflection((0.0, 0.0), (1.0, 0.0)))        # (about y = 0)
        self.assertAlmostEqual(flipped.cy, -6.0)
        self.assertEqual(flipped.water, (other.water[2], other.water[1], other.water[0], other.water[3]))
        self.assertAlmostEqual(rb.height_at([flipped], 8.0, -6.0), rb.height_at([other], 8.0, 6.0), places=9)
        self.assertEqual([rb.form_of(rb.make(0, 0, 0, 10, 6, f)) for f in rb.FORMS], list(rb.FORMS))
        crossing = rb.breaks([one], (5.0, -1.0), (5.0, 7.0))
        self.assertTrue(any(abs(s - 0.5) < 1e-6 for s in crossing))        # (its ridge at y = 3)
        self.assertEqual(rb.problem(rb.make(0, 0, 0, 0.1, 5.0)), "block_too_small")
        turned = rb.make(0.0, 0.0, 90.0, 4.0, 2.0, "hip")                    # (0.264) its x along the plan's y
        out, half = rb.side_way(turned, 1)                                   # (its E side: towards +y)
        self.assertEqual((round(out[0], 9), round(out[1], 9), half), (0.0, 1.0, 2.0))
        longer = rb.stretched(turned, 1, 1.5)                                # (E out 1,5 m; W where it was)
        self.assertAlmostEqual(longer.width, 5.5)
        self.assertAlmostEqual(longer.cy, 0.75)
        self.assertAlmostEqual(longer.cy - longer.width / 2, turned.cy - turned.width / 2)
        shorter = rb.stretched(turned, 0, -0.5)                              # (its N side, facing −x, in 50 cm)
        self.assertEqual((round(shorter.depth, 9), round(shorter.cx, 9)), (1.5, 0.25))

    def test_edges(self):
        """0.265: the edges of roofs by blocks, 10 × 6 m at 30°, no overhang — four waters: 32 m of eaves, a 4 m
        ridge, four hips (each 3 m across, 3 m along, 3·tan 30° up); two waters: 20 m of eaves, a 10 m ridge, four
        gable edges; one water: its foot an eave, its head a top edge, two gable edges; a T of a hip and a narrower
        gable block: a valley each side of the gable, from the eaves' corner up; every edge counted once."""
        from arqbim.core import roof_blocks as rb
        t30 = math.tan(math.radians(30))
        hip = rb.edge_lengths([rb.make(5.0, 3.0, 0.0, 10.0, 6.0, "hip", 30.0, 0.0)])
        self.assertAlmostEqual(hip["eave"], 32.0, places=6)
        self.assertAlmostEqual(hip["ridge"], 4.0, places=6)
        self.assertAlmostEqual(hip["hip"], 4 * math.sqrt(9 + 9 + (3 * t30) ** 2), places=6)
        self.assertEqual((hip["valley"], hip["gable"], hip["top"]), (0.0, 0.0, 0.0))
        gable = rb.edge_lengths([rb.make(5.0, 3.0, 0.0, 10.0, 6.0, "gable", 30.0, 0.0)])
        self.assertAlmostEqual(gable["eave"], 20.0, places=6)
        self.assertAlmostEqual(gable["ridge"], 10.0, places=6)
        self.assertAlmostEqual(gable["gable"], 4 * math.sqrt(9 + (3 * t30) ** 2), places=6)
        self.assertEqual(gable["hip"], 0.0)
        shed = rb.edge_lengths([rb.make(5.0, 3.0, 0.0, 10.0, 6.0, "shed", 30.0, 0.0)])
        self.assertAlmostEqual(shed["eave"], 10.0, places=6)
        self.assertAlmostEqual(shed["top"], 10.0, places=6)
        self.assertAlmostEqual(shed["gable"], 2 * math.sqrt(36 + (6 * t30) ** 2), places=6)
        main = rb.make(5.0, 3.0, 0.0, 10.0, 6.0, "hip", 30.0, 0.0)
        wing = rb.make(7.5, 7.0, 0.0, 3.0, 6.0, "gable", 30.0, 0.0)              # (x 6..9: a valley each side)
        both = rb.edges([main, wing])
        valleys = [(a, b) for kind, a, b in both if kind == "valley"]
        self.assertEqual(len(valleys), 2)
        for a, b in valleys:                            # (from the eave's corner up to where the ridges meet)
            self.assertAlmostEqual(min(a[2], b[2]), 0.0, places=6)
        keys = [tuple(sorted((tuple(round(v, 6) for v in a), tuple(round(v, 6) for v in b)))) for _k, a, b in both]
        self.assertEqual(len(keys), len(set(keys)))


class RoofCarpentry(unittest.TestCase):
    """0.276: the carpentry of a hip roof by blocks 10,2 × 6,2 m (50 cm eaves, 30°, a 3 cm cover): rafters no more
    than 0,50 m apart over each water, battens at the 0,35 m gauge, two purlins a water (4,16 m of slope: no
    rafter spanning more than 1,50 m), four hip rafters and the ridge board, their top where the rafters' is (the
    cover and a batten under the top); a wall plate lying on its walls; each piece 8 corners, its volume its length
    × its section; a T of a hip and a gable: valley rafters."""

    def test_pieces(self):
        from arqbim.core import roof_blocks as rb
        from arqbim.core import roof_carpentry as rc
        blocks = [rb.make(5.0, 3.0, 0.0, 10.2, 6.2, "hip", 30.0, 0.5)]
        found = rb.regions(blocks)
        waters = [(c, p) for c, g in found for p in rb.polygons(g)]
        pieces = rc.pieces(waters, rb.edges(blocks, found), 0.03, [((0.0, 0.0), (10.0, 0.0), 0.0)])
        counts = {role: n for role, (n, _l, _v) in rc.summary(pieces).items()}
        self.assertEqual(counts["terca"], 8)
        self.assertEqual((counts["rincao"], counts["fileira"], counts["frechal"]), (4, 1, 1))
        # (2 × 24 + 2 × 16 places no more than 0,50 m apart along the eaves, but for the stubs under 15 cm at
        # the hips' feet)
        self.assertTrue(2 * 24 + 2 * 16 - 8 <= counts["caibro"] <= 2 * 24 + 2 * 16, counts["caibro"])
        self.assertGreater(counts["ripa"], 4 * 10)
        cos = math.cos(math.radians(30))
        ridge = next(p for p in pieces if p.role == "fileira")
        top = 3.1 * math.tan(math.radians(30)) - (0.03 + 0.015) / cos
        self.assertTrue(all(abs(c[2] - top) < 1e-9 for c in ridge.corners[4:]))
        plate = next(p for p in pieces if p.role == "frechal")
        self.assertEqual((round(min(c[2] for c in plate.corners), 9), round(plate.length, 9)), (0.0, 10.0))
        for p in pieces:
            self.assertEqual(len(p.corners), 8)
            self.assertAlmostEqual(p.volume, p.length * p.width * p.height)
        t = [rb.make(5.0, 3.0, 0.0, 10.0, 6.0, "hip", 30.0, 0.0), rb.make(7.5, 7.0, 0.0, 3.0, 6.0, "gable", 30.0, 0.0)]
        found = rb.regions(t)
        waters = [(c, p) for c, g in found for p in rb.polygons(g) if abs(c[0]) + abs(c[1]) > 0]
        pieces = rc.pieces(waters, rb.edges(t, found), 0.03)
        self.assertEqual(rc.summary(pieces)["laro"][0], 2)


class RoofTiles(unittest.TestCase):
    """0.279: the add-on's tiles — each a closed mesh, turned out; a cube cut by a plane: closed again, half of it;
    a hip roof by blocks 10,2 × 6,2 m tiled with Marselha tiles: about its waters' area over a tile's (cover width
    × gauge), those by the hips and the ridge cut, the ridge tiles as many as fill the ridge and the hips at their
    gauge; each whole tile's head on the tile below; the plain tile's rows half a tile across every other row."""

    @staticmethod
    def _closed(verts, tris):
        from collections import Counter
        edges = Counter((a, b) for t in tris for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])))
        return all(n == 1 and edges.get((b, a)) == 1 for (a, b), n in edges.items())

    @staticmethod
    def _volume(verts, tris):
        a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
        return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6)

    def test_meshes(self):
        from arqbim.core import roof_tiles as rt
        for spec in list(rt.TILES.values()) + [rt.CAP]:
            v, t = rt.tile_mesh(spec)
            self.assertTrue(self._closed(v, t), spec.key)
            self.assertGreater(self._volume(v, t), 0.0)
        cube = np.array([(x, y, z) for x in (0.0, 1.0) for y in (0.0, 1.0) for z in (0.0, 1.0)])
        quads = ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))
        tris = np.array([tri for a, b, c, d in quads for tri in ((a, b, c), (a, c, d))])
        self.assertGreater(self._volume(cube, tris), 0.0)
        v, t = rt.clip(cube, tris, (1.0, 0.0, 0.0), (0.5, 0.0, 0.0))
        self.assertTrue(self._closed(v, t))
        self.assertAlmostEqual(self._volume(v, t), 0.5, places=9)
        self.assertAlmostEqual(float(v[:, 0].min()), 0.5, places=9)

    def test_lay(self):
        from arqbim.core import roof_blocks as rb
        from arqbim.core import roof_tiles as rt
        blocks = [rb.make(5.0, 3.0, 0.0, 10.2, 6.2, "hip", 30.0, 0.5)]
        found = rb.regions(blocks)
        waters = [(c, p) for c, g in found for p in rb.polygons(g)]
        edges = rb.edges(blocks, found)
        spec = rt.TILES["marselha"]
        tiling = rt.lay(waters, edges, spec)
        expected = tiling.area / (spec.cover_width * spec.gauge)
        self.assertAlmostEqual(tiling.area, 11.2 * 7.2 / math.cos(math.radians(30)), places=6)    # (its eaves too)
        # (more, by the hips: a tile cut along a hip on each side of it — 0.280: those only touching the water too)
        self.assertTrue(expected < tiling.tiles < 1.2 * expected, (tiling.tiles, expected))
        self.assertGreater(tiling.cut_count, 50)
        self.assertEqual(len(tiling.caps), sum(math.ceil((math.dist(a, b) - rt.CAP.length) / rt.CAP.gauge) + 1
                                                for kind, a, b in edges if kind in ("ridge", "hip")))
        def on_edge(p):                                    # (in the plan: on a ridge or hip, between its ends)
            for kind, a, b in edges:
                if kind not in ("ridge", "hip"):
                    continue
                d = np.array((b[0] - a[0], b[1] - a[1]))
                q = np.array((p[0] - a[0], p[1] - a[1]))
                s = float(q @ d) / float(d @ d)
                if -1e-6 <= s <= 1 + 1e-6 and abs(float(q[0] * d[1] - q[1] * d[0])) / np.linalg.norm(d) < 1e-6:
                    return True
            return False
        for origin, axes in tiling.caps:                   # (none past its edge's ends)
            self.assertTrue(all(on_edge(origin + axes[0] * rt.CAP.width / 2 + axes[1] * y)
                                for y in (0.0, rt.CAP.length)))
        self.assertAlmostEqual(tiling.weight, tiling.tiles * 2.8 + len(tiling.caps) * 2.6)
        from shapely.geometry import Point

        def water_of(p):
            return next((c for c, poly in waters if poly.contains(Point(p[0], p[1]))), None)

        # (a whole tile on one water: its head raised by its thickness over the rows' overlap, its tail down)
        origin, axes = next((o, ax) for o, ax in tiling.whole
                            if water_of(o) is not None and water_of(o + spec.length * ax[1]) == water_of(o))
        a, b, c = water_of(origin)
        head = spec.thickness * spec.length / spec.gauge
        self.assertAlmostEqual(float(np.linalg.det(axes)), 1.0, places=9)
        tail = origin + spec.length * axes[1]
        cos = math.cos(math.radians(30))
        self.assertAlmostEqual((origin[2] - (a * origin[0] + b * origin[1] + c)) * cos, head + rt.LIFT, places=6)
        self.assertAlmostEqual((tail[2] - (a * tail[0] + b * tail[1] + c)) * cos, rt.LIFT, places=4)
        sheets = rt.lay(waters, edges, rt.TILES["ondulada"])           # (0.280) the corrugated sheet: as tiles
        expected = sheets.area / (0.85 * 1.80)
        self.assertTrue(expected < sheets.tiles < 1.8 * expected, (sheets.tiles, expected))
        # (no bare triangle by the hips: every point of the waters under a sheet, whole or cut)
        from shapely.geometry import Point, Polygon
        from shapely.ops import unary_union
        inner = unary_union([p for _c, p in waters]).buffer(-0.05)
        points = np.array([(x, y) for x in np.arange(-0.6, 10.7, 0.25) for y in np.arange(-0.6, 6.7, 0.25)
                           if inner.contains(Point(x, y))])
        covered = np.zeros(len(points), dtype=bool)
        for o, a in sheets.whole:
            rect = Polygon([tuple((o + a[0] * x + a[1] * y)[:2]) for x, y in ((0, 0), (0.92, 0), (0.92, 2.0), (0, 2.0))])
            covered |= np.array([rect.contains(Point(p)) for p in points])
        v, t = sheets.cut
        tri = v[t][:, :, :2]
        for i, p in enumerate(points):
            if covered[i]:
                continue
            d0, d1 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
            q = p - tri[:, 0]
            den = d0[:, 0] * d1[:, 1] - d0[:, 1] * d1[:, 0]
            ok = np.abs(den) > 1e-12
            s = np.where(ok, (q[:, 0] * d1[:, 1] - q[:, 1] * d1[:, 0]) / np.where(ok, den, 1.0), -1.0)
            r = np.where(ok, (d0[:, 0] * q[:, 1] - d0[:, 1] * q[:, 0]) / np.where(ok, den, 1.0), -1.0)
            covered[i] = bool(np.any((s >= -1e-9) & (r >= -1e-9) & (s + r <= 1 + 1e-9)))
        self.assertTrue(covered.all(), points[~covered][:5])
        plain = rt.lay(waters[:1], edges, rt.TILES["plana"])
        rows = {}
        for o, ax in plain.whole:
            rows.setdefault(round(float(o[2]), 4), []).append(float(o @ ax[0]))
        firsts = [min(us) % rt.TILES["plana"].cover_width for _z, us in sorted(rows.items())[:2]]
        self.assertAlmostEqual(abs(firsts[0] - firsts[1]), rt.TILES["plana"].cover_width / 2, places=6)

    def test_own_tile(self):
        """0.281: a tile of the user's own, given as the add-on takes it (its corner at the origin, y down the
        slope): turned about z to the program's frame — its size kept, still closed and turned out; laid not tilted
        (as the add-on), a row a gauge apart."""
        from arqbim.core import roof_blocks as rb
        from arqbim.core import roof_tiles as rt
        cube = np.array([(x, y, z) for x in (0.0, 0.3) for y in (0.0, 0.45) for z in (0.0, 0.02)]) + (5.0, 7.0, 1.0)
        quads = ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))
        tris = np.array([tri for a, b, c, d in quads for tri in ((a, b, c), (a, c, d))])
        spec = rt.custom_spec("t:x", "Minha", cube, tris, 0.27, 0.38, 3.1, False)
        self.assertEqual((round(spec.width, 9), round(spec.length, 9), round(spec.top, 9)), (0.3, 0.45, 0.02))
        v, t = rt.tile_mesh(spec)
        self.assertTrue(self._closed(v, t))
        self.assertAlmostEqual(self._volume(v, t), 0.3 * 0.45 * 0.02, places=9)
        self.assertEqual((float(v.min()), round(float(v[:, 1].max()), 9)), (0.0, 0.45))
        blocks = [rb.make(5.0, 3.0, 0.0, 10.2, 6.2, "hip", 30.0, 0.5)]
        found = rb.regions(blocks)
        tiling = rt.lay([(c, p) for c, g in found for p in rb.polygons(g)], rb.edges(blocks, found), spec)
        origin, axes = tiling.whole[0]
        self.assertAlmostEqual(float(np.dot(axes[1], axes[2])), 0.0, places=9)
        self.assertAlmostEqual(float(axes[1][2]), math.sin(math.radians(30)), places=9)   # (not tilted)

    def test_panels(self):
        """0.280: the sandwich panel (flat under, its ribs on top: 4 + 3,8 cm) laid as panels on a shed roof 8 m
        across whose slope runs 11,5 m: one a column (a metre each), each in two lengths (none longer than 6 m),
        their weight their length's; closed where cut on a hip roof."""
        from arqbim.core import roof_blocks as rb
        from arqbim.core import roof_tiles as rt
        spec = rt.TILES["sanduiche"]
        v, t = rt.tile_mesh(spec)
        self.assertTrue(self._closed(v, t))
        self.assertAlmostEqual(spec.top, 0.078, places=9)
        self.assertEqual(float(v[:, 2].min()), 0.0)
        from arqbim.core.roof_carpentry import _Water
        block = rb.make(4.0, 5.0, 0.0, 8.0, 10.0, "shed", 30.0, 0.0)
        found = rb.regions([block])
        waters = [(c, p) for c, g in found for p in rb.polygons(g) if abs(c[0]) + abs(c[1]) > 0]
        w = _Water(*waters[0])
        run, columns = (w.r1 - w.r0) * w.k, math.ceil((w.u1 - w.u0) / spec.cover_width - 1e-9)
        self.assertGreater(run, 6.0)
        self.assertLess(run, 12.0)
        tiling = rt.lay(waters, rb.edges([block], found), spec)
        self.assertEqual((len(tiling.whole), tiling.tiles), (0, 2 * columns))
        self.assertAlmostEqual(tiling.mass, columns * run / 3.0 * 11.0, places=6)
        hip = [rb.make(5.0, 3.0, 0.0, 10.2, 6.2, "hip", 30.0, 0.5)]
        found = rb.regions(hip)
        tiling = rt.lay([(c, p) for c, g in found for p in rb.polygons(g)], rb.edges(hip, found), spec)
        self.assertGreater(tiling.cut_count, 4)
        self.assertGreater(tiling.panels, 4)


class RailingExtensions(unittest.TestCase):
    """0.282: a stair's railing (10 risers of 0,175 at 0,28) with its handrail on past its ends, DL 163/2006 (annex
    2.4.9): at its foot one going on, keeping the slope, its end turned down to the floor; at its top 0,30 m on,
    level, turned down to the floor above; a railing without a handrail: its top rail so; a closed one: none."""

    def test_extensions(self):
        from arqbim.core import railing_types as rtypes
        path = [(0.0, 0.0, 0.175), (9 * 0.28, 0.0, 1.75)]
        wall = rtypes.PRESETS["corrimao"]
        bars = [p for p in rtypes.parts(path, wall, 0.9, extend=(0.28, rtypes.TOP_EXTENSION)) if p[0] == "bar"]
        z = wall.hand_z - wall.hand_w / 2
        ends = [(np.round(p[1], 6), np.round(p[2], 6)) for p in bars]
        self.assertTrue(any(np.allclose(b, (-0.28, 0.0, z)) for _a, b in ends), ends)       # (a going back, sloping)
        self.assertTrue(any(np.allclose(b, (-0.28, 0.0, 0.0)) for _a, b in ends))           # (down to the floor)
        self.assertTrue(any(np.allclose(b, (9 * 0.28 + 0.30, 0.0, 1.75 + z)) for _a, b in ends))   # (level)
        self.assertTrue(any(np.allclose(b, (9 * 0.28 + 0.30, 0.0, 1.75)) for _a, b in ends))
        guard = rtypes.PRESETS["barras"]                    # (no handrail: its top rail is the one gripped)
        bars = [p for p in rtypes.parts(path, guard, 0.9, extend=(0.28, 0.30)) if p[0] == "bar"]
        self.assertTrue(any(abs(p[2][0] + 0.28) < 1e-6 and abs(p[2][2]) < 1e-6 for p in bars))
        plain = rtypes.parts(path, guard, 0.9)
        self.assertEqual(len(bars), len([p for p in plain if p[0] == "bar"]) + 4)
        ring = [(0, 0, 0), (2, 0, 0), (2, 2, 0)]
        self.assertEqual(len(rtypes.parts(ring, wall, closed=True, extend=(0.3, 0.3))),
                         len(rtypes.parts(ring, wall, closed=True)))


class Joinery(unittest.TestCase):
    """0.288 — the door and window generator: a pair of casements meeting with no mullion, a fixed light beside a leaf
    with one; two sliding leaves overlapping by a stile, on two tracks; sizes of 0 sharing what is left; a door's
    fanlight over a transom, its fixed light at the floor on a rail, its casings on both faces; IFC's names of each
    (one leaf, double doors, a leaf and a fixed light, others USERDEFINED; a window's partitioning by its rows); the
    mirror image; kept as text and read back; one made from IFC's names alone; a door's plan symbol."""

    def test_layout_and_parts(self):
        from arqbim.core import joinery as jn
        pair = jn.window(("left", "right"))
        lights, bars = jn.layout(pair, 1.2, 1.2)
        self.assertEqual(bars, [])                                           # (they close on each other)
        self.assertAlmostEqual(lights[0].x1, 0.6)
        self.assertAlmostEqual(lights[1].x0, 0.6)
        self.assertAlmostEqual(lights[0].x0, pair.frame)
        mixed = jn.window(("fixed", "left"))
        lights, bars = jn.layout(mixed, 1.2, 1.2)
        self.assertEqual(len(bars), 1)                                       # a mullion between
        self.assertAlmostEqual(bars[0][1] - bars[0][0], mixed.mullion)
        self.assertAlmostEqual(lights[0].x1, 0.6 - mixed.mullion / 2)
        sliding = jn.window(("slide_right", "slide_left"))
        lights, _bars = jn.layout(sliding, 1.5, 1.2)
        self.assertAlmostEqual(lights[0].x1 - lights[1].x0, sliding.sash)   # (overlapping by a stile)
        tracks = {jn._across(sliding, lt, 0.0, 0.07) for lt in lights}
        self.assertEqual(len(tracks), 2)
        self.assertTrue(np.allclose(jn._sizes([0.3, 0.0, 0.0], 1.3), [0.3, 0.5, 0.5]))
        self.assertTrue(np.allclose(jn._sizes([1.0, 1.0], 1.0), [0.5, 0.5]))     # (given, too big: scaled)
        door = jn.door("left", "fixed", transom=0.5, hardware=False)        # (its handles: JoineryFinish)
        lights, bars = jn.layout(door, 1.4, 2.6)
        self.assertTrue(any(abs(b[2] - (2.1 - door.mullion / 2)) < 1e-9 for b in bars))     # the transom
        fixed = [lt for lt in lights if lt.row == 0 and lt.cell.operation == "fixed"][0]
        self.assertTrue(fixed.rail and abs(fixed.z0 - door.frame) < 1e-9)
        leaf = [lt for lt in lights if lt.cell.operation == "left"][0]
        self.assertAlmostEqual(leaf.z0, 0.0)                                 # (to the floor)
        pieces = jn.parts(door, 1.4, 2.6, 0.0, 0.2)
        lo = np.min([p[1] for p in pieces], axis=0)
        hi = np.max([p[2] for p in pieces], axis=0)
        self.assertTrue(np.allclose(lo, (-door.casing, -door.casing_depth, 0.0)), lo)        # its casings
        self.assertTrue(np.allclose(hi, (1.4 + door.casing, 0.2 + door.casing_depth, 2.6 + door.casing)), hi)
        self.assertEqual({p[0] for p in pieces}, {"frame", "panel", "glass"})
        self.assertEqual([k for _p, k in jn.constituents(door)], ["madeira", "madeira", "vidro"])
        meshes = jn.meshes(jn.window(("left", "right")), 1.2, 1.2, 0.065, 0.135)
        self.assertEqual(set(meshes), {"aluminio", "vidro", "inox"})        # (its handles and hinges: 0.290)
        verts = np.concatenate([v for k, (v, _t) in meshes.items() if k != "inox"])   # (not its handles)
        self.assertTrue(verts[:, 1].min() >= 0.065 - 1e-9 and verts[:, 1].max() <= 0.135 + 1e-9)

    def test_joined_pieces(self):
        """0.312 — a frame's pieces one surface: no seam where a jamb meets the head, a stile a rail, a casing the
        next; the line round each leaf (between it and the frame, between the two of a pair) stays."""
        from arqbim.core import joinery as jn
        from arqbim.core.mesh import TriMesh

        def on_plane(mesh, axis, value):
            v, t = mesh
            pairs, _faces = TriMesh(v, t).edge_array()
            ends = v[pairs]
            return ends[np.all(np.abs(ends[:, :, axis] - value) < 1e-9, axis=1)]

        pair = jn.window(("left", "right"))
        frame = jn.meshes(pair, 1.2, 1.2, 0.065, 0.135)[pair.frame_material]
        self.assertEqual(len(on_plane(frame, 1, 0.065)), 8)             # its outer face: a ring (was 4 boxes, 16)
        inner = on_plane(frame, 1, 0.135)                               # its inner face: the frame's ring and each
        self.assertEqual(len(inner), 24)                                # leaf's, apart (was 12 boxes, 48)
        meeting = inner[np.all(np.abs(inner[:, :, 0] - 0.6) < 1e-9, axis=1)]
        self.assertEqual(len(meeting), 2)                               # (where the two leaves close: both edges)
        loose = sum(TriMesh(*jn.prism_mesh(p, ya, yb)).volume()
                    for role, p, ya, yb in jn.pieces(pair, 1.2, 1.2, 0.065, 0.135) if role in ("frame", "leaf"))
        self.assertAlmostEqual(TriMesh(*frame).volume(), loose, places=9)
        door = jn.door("left", hardware=False)
        lining = jn.meshes(door, 0.9, 2.1, 0.0, 0.2)[door.frame_material]
        self.assertEqual(len(on_plane(lining, 1, -door.casing_depth)), 8)  # its casings' face: one ∩ (was 12)
        self.assertFalse(jn.meshes(door, 0.9, 2.1, 0.0, 0.2)[door.frame_material][0].flags.writeable)   # (kept)
        # each still a closed solid — its corners shared, no T-junction where one plane's corner is on another's side
        # (an arch's band on its jambs; a door's casings round a shutter's box)
        arched = jn.with_arch(jn.window(("left", "right"), stone=0.03), "round", 1.0)
        for design, w, h, y0, y1 in ((pair, 1.2, 1.2, 0.065, 0.135), (arched, 1.0, 1.5, 0.065, 0.135),
                                     (jn.replace(door, shutter=0.25), 0.9, 2.1, 0.0, 0.2)):
            for key, mesh in jn.meshes(design, w, h, y0, y1, (0.0, 0.2)).items():
                self.assertTrue(TriMesh(*mesh).is_closed(), (design.arch, design.shutter, key))

    def test_names_and_text(self):
        from arqbim.core import joinery as jn
        self.assertEqual(jn.door_operation(jn.door("left")), ("SINGLE_SWING_LEFT", None))
        self.assertEqual(jn.door_operation(jn.door("left", "right"))[0], "DOUBLE_DOOR_SINGLE_SWING")
        self.assertEqual(jn.door_operation(jn.door("left", "fixed"))[0], "SWING_FIXED_LEFT")
        self.assertEqual(jn.door_operation(jn.door("slide_left", "slide_right"))[0], "DOUBLE_DOOR_SLIDING")
        self.assertEqual(jn.door_operation(jn.door("fixed", "left", "right")), ("USERDEFINED", "fixed+left+right"))
        self.assertEqual(jn.window_partitioning(jn.window(("left", "right"), ("fixed",)))[0], "TRIPLE_PANEL_TOP")
        self.assertEqual(jn.window_partitioning(jn.window(("fixed",), ("left", "right")))[0], "TRIPLE_PANEL_BOTTOM")
        self.assertEqual(jn.window_partitioning(jn.window(("left", "right"), ("fixed", "fixed"))),
                         ("USERDEFINED", "2×2"))
        door = jn.door("left", "fixed", transom=0.5)
        self.assertEqual(jn.door_operation(jn.mirrored(door))[0], "SWING_FIXED_RIGHT")
        self.assertEqual(jn.mirrored(jn.mirrored(door)), door)
        self.assertEqual(jn.hand(jn.mirrored(jn.door("left"))), "RIGHT")
        self.assertIsNone(jn.hand(jn.door("left", "right")))
        self.assertAlmostEqual(jn.transom_of(door, 2.6), 0.5)
        self.assertEqual(jn.from_json(jn.to_json(door)), door)
        with self.assertRaises(ValueError):
            jn.from_json('{"rows": []}')
        made = jn.standard("door", "SINGLE_SWING_RIGHT", 0.4)
        self.assertEqual([c.operation for c in made.rows[0].cells], ["right"])
        self.assertAlmostEqual(jn.transom_of(made, 2.5), 0.4)
        window = jn.standard("window", "DOUBLE_PANEL_VERTICAL", window_ops=["SIDEHUNGLEFTHAND", "FIXEDCASEMENT"])
        self.assertEqual([c.operation for c in window.rows[0].cells], ["left", "fixed"])
        self.assertEqual([c.operation for c in jn.standard("window", "SINGLE_PANEL").rows[0].cells], ["fixed"])
        positions = [p for _c, p, _s in jn.panels(jn.window(("left", "right"), ("bottom",)), 1.2, 1.6)]
        self.assertEqual(positions, ["LEFT", "RIGHT", "TOP"])

    def test_elevation_signs(self):
        """0.292: in elevation, a side-hung leaf's lines meet at its hinges (a pair: at the outer jambs), a tilt and
        turn one's also at its foot; a top-hung one's at its top; a sliding one an arrow the way it opens; a fixed
        light none."""
        from arqbim.core import joinery as jn
        pair = jn.window(("left", "right"))
        lights = jn.layout(pair, 1.2, 1.2)[0]
        signs = jn.elevation_signs(pair, 1.2, 1.2)
        self.assertEqual(len(signs), 2)
        zm = (lights[0].z0 + lights[0].z1) / 2
        self.assertTrue(np.allclose(signs[0][1], (lights[0].x0, zm)) and np.allclose(signs[1][1], (lights[1].x1, zm)))
        self.assertEqual(len(jn.elevation_signs(jn.window(("tilt_left",)), 1.0, 1.2)), 2)
        top = jn.elevation_signs(jn.window(("top",)), 1.0, 1.0)[0]
        self.assertGreater(top[1][1], top[0][1])                             # (meeting at its top)
        arrow, head = jn.elevation_signs(jn.window(("slide_left",)), 1.0, 1.0)
        self.assertLess(arrow[1][0], arrow[0][0])                            # (to the left)
        self.assertTrue(np.allclose(head[1], arrow[1]))
        self.assertEqual(jn.elevation_signs(jn.window(("fixed",)), 1.0, 1.0), [])

    def test_plan_symbol(self):
        from arqbim.core import joinery as jn
        single = jn.plan_symbol(jn.door("left"), 0.8, 2.1, 0.0, 0.2)
        self.assertEqual(len(single), 2 + 4 + 2)            # jambs, casings, the leaf open and its swing
        arc = single[-1]
        self.assertTrue(np.allclose(arc[0], (0.8 - 0.05, 0.2)) and np.allclose(arc[-1], (0.05, 0.2 + 0.7)), arc)
        right = jn.plan_symbol(jn.door("right"), 0.8, 2.1, 0.0, 0.2)[-1]
        self.assertTrue(np.allclose(right[0], (0.05, 0.2)) and np.allclose(right[-1], (0.75, 0.9)), right)
        both = jn.plan_symbol(jn.door("swing_left"), 0.8, 2.1, 0.0, 0.2)
        self.assertEqual(len(both), 9)                       # (its swing to both sides)
        sliding = jn.plan_symbol(jn.door("slide_left"), 0.9, 2.1, 0.0, 0.2)
        self.assertEqual(len(sliding), 2 + 4 + 3)            # the leaf, the arrow and its head
        fixed = jn.plan_symbol(jn.door("left", "fixed", fill="glass"), 1.2, 2.1, 0.0, 0.2)
        self.assertEqual(len(fixed), 2 + 4 + 2 + 1)          # (and the fixed light, closed)


class JoineryEditing(unittest.TestCase):
    """0.289 — the generator's window, its changes: a cell split in two (the new one fixed), joined back; a row over
    it (a fanlight 40 cm), taken away; a cell's way of opening and width, a row's height; the library's layouts, found
    again in a design; what is wrong said: a frame wider than half, heights that do not add up, a leaf too narrow."""

    def test_editing(self):
        from arqbim.core import joinery as jn
        d = jn.window(("left",))
        two = jn.split(d, 0, 0)
        self.assertEqual([c.operation for c in two.rows[0].cells], ["left", "fixed"])
        self.assertEqual(jn.join(two, 0, 0), d)
        self.assertEqual(jn.join(two, 0, 1), two)                         # (nothing on its right)
        top = jn.add_row(d, 0)
        self.assertEqual((len(top.rows), top.rows[1].height), (2, 0.40))
        self.assertEqual(jn.remove_row(top, 1), d)
        self.assertEqual(jn.remove_row(d, 0), d)                          # (the last row stays)
        changed = jn.set_cell(two, 0, 1, operation="tilt_right", width=0.5)
        self.assertEqual(changed.rows[0].cells[1], jn.Cell("tilt_right", "glass", 0.5))
        self.assertEqual(jn.set_row(top, 1, 0.3).rows[1].height, 0.3)
        self.assertEqual(jn.matching_model(jn.window(("left", "right"))), "batente_2")
        self.assertIsNone(jn.matching_model(changed))
        for kind in ("window", "door"):
            for key, _pt, _en, rows in jn.MODELS[kind]:
                design = dataclasses.replace(jn.window() if kind == "window" else jn.door(), rows=jn.model(kind, key))
                self.assertEqual(jn.problems(design, 1.6, 2.2), [], key)
                self.assertEqual(jn.matching_model(design), key)
        self.assertEqual(jn.problems(dataclasses.replace(d, frame=0.7), 1.2, 1.2)[0][0], "joinery.err_profiles")
        tall = jn.set_row(jn.set_row(top, 0, 1.0), 1, 0.5)
        self.assertEqual([k for k, _v in jn.problems(tall, 1.2, 1.2)], ["joinery.err_heights"])
        narrow = jn.set_cell(jn.split(d, 0, 0), 0, 0, width=0.15)
        self.assertEqual(jn.problems(narrow, 1.2, 1.2), [("joinery.err_small", {"row": 1, "cell": 1})])


class JoineryFinish(unittest.TestCase):
    """0.290 — a door's and a window's finish: a window on a stone sill 3 cm thick — its frame on it, the sill 3 cm out
    of the wall's outer face with its drip groove (1 cm wide, 8 mm deep, 1,5 cm in from the nose) —; a door's stone
    threshold between its jambs, across the wall and out of it, its leaf over it; casings on one face only; a door's
    three hinges on its hinge side and its levers on both faces 1 m up pointing to the hinges, a window's two hinges
    and its handle on its inner face; a sliding leaf's pull at the edge it is pulled by; none when not wanted."""

    def test_finish(self):
        from arqbim.core import joinery as jn
        w = jn.window(("left",), stone=0.03)
        lights, _bars = jn.layout(w, 1.0, 1.2)
        self.assertAlmostEqual(lights[0].z0, 0.03 + w.frame)                 # (the frame on the sill)
        pieces = jn.stones(w, 1.0, 0.065, 0.135, faces=(0.0, 0.2))
        self.assertEqual(len(pieces), 3)                                      # (the groove between)
        self.assertTrue(np.allclose(pieces[0][0], (0.0, -0.03, 0.0)) and np.allclose(pieces[2][1], (1.0, 0.135, 0.03)))
        self.assertTrue(np.allclose((pieces[1][0][1], pieces[1][1][1], pieces[1][0][2]), (-0.015, -0.005, 0.008)))
        self.assertEqual(len(jn.stones(dataclasses.replace(w, drip=False), 1.0, 0.065, 0.135)), 1)
        jambs = [p for p in jn.parts(w, 1.0, 1.2, 0.065, 0.135) if p[0] == "frame" and p[2][0] - p[1][0] < 0.06]
        self.assertTrue(all(abs(p[1][2] - 0.03) < 1e-9 for p in jambs))
        d = jn.door("left", stone=0.03)
        (lo, hi), = jn.stones(d, 0.9, 0.0, 0.2, faces=(0.0, 0.2))
        self.assertTrue(np.allclose(lo, (d.frame, -0.03, 0.0)) and np.allclose(hi, (0.9 - d.frame, 0.2, 0.03)))
        leaf = jn.layout(d, 0.9, 2.1)[0][0]
        self.assertAlmostEqual(leaf.z0, 0.03)
        self.assertEqual(len(jn.plan_symbol(d, 0.9, 2.1, 0.0, 0.2, (0.0, 0.2))), 2 + 4 + 1 + 2)    # (the threshold)
        one = jn.casings(dataclasses.replace(d, casing_sides="open"), 0.9, 2.1, 0.0, 0.2)
        self.assertEqual(len(one), 3)
        self.assertTrue(all(c[4] >= 0.2 - 1e-9 for c in one))
        boxes = jn.hardware(jn.door("left"), 0.9, 2.1, 0.0, 0.2)
        hinges = [b for b in boxes if b[1][0] - b[0][0] < 0.015 + 1e-9 and b[1][2] - b[0][2] > 0.099]
        self.assertEqual(len(hinges), 3)
        self.assertTrue(all(abs((b[0][0] + b[1][0]) / 2 - 0.05) < 1e-9 for b in hinges))    # (on the hinge jamb)
        levers = [b for b in boxes if b[1][0] - b[0][0] > 0.12]
        self.assertEqual(len(levers), 2)                                      # (both faces)
        self.assertTrue(all(abs((b[0][2] + b[1][2]) / 2 - 1.0) < 1e-9 for b in levers))
        self.assertTrue(all(b[0][0] < 0.85 - 0.06 for b in levers))          # (from the free side to the hinges)
        window_boxes = jn.hardware(jn.window(("right",)), 1.0, 1.2, 0.065, 0.135)
        self.assertEqual(len(window_boxes), 2 + 3)                            # (two hinges; a rose, neck, lever)
        self.assertTrue(all(b[0][1] >= 0.135 - 1e-9 for b in window_boxes))   # (on its inner face)
        pull = jn.hardware(jn.door("slide_left"), 0.9, 2.1, 0.0, 0.2)
        self.assertEqual(len(pull), 2)
        self.assertEqual(jn.hardware(jn.window(("left",), hardware=False), 1.0, 1.2, 0.0, 0.07), [])
        self.assertEqual({m for m in jn.meshes(jn.window(("left",), stone=0.03), 1.0, 1.2, 0.065, 0.135)},
                         {"aluminio", "vidro", "pedra", "inox"})


class JoineryOutside(unittest.TestCase):
    """0.291 — outside a window's frame: its mosquiteiro against it (a thin frame and its mesh), its estore further out
    (its guides on the jambs, its slats let down half way, its box 20 cm at the top across the whole wall, the frame
    under it), its grade furthest (bars at most 12 cm apart, two flats); its glazing fraction."""

    def test_outside(self):
        from arqbim.core import joinery as jn
        w = jn.window(("left",), shutter=0.2, shutter_closed=0.5, screen=True, grille=True)
        lights, _bars = jn.layout(w, 1.0, 1.4)
        self.assertAlmostEqual(lights[0].z1, 1.4 - 0.2 - w.frame)            # (the frame under the box)
        pieces = jn.outside(w, 1.0, 1.4, 0.065, 0.135, faces=(0.0, 0.2))
        roles = [p[0] for p in pieces]
        self.assertEqual((roles.count("screen_frame"), roles.count("screen"), roles.count("shutter"),
                          roles.count("grille")), (4, 1, 4, 7 + 2))
        guides = [p for p in pieces if p[0] == "shutter" and abs(p[2][0] - p[1][0] - jn.GUIDE[0]) < 1e-9]
        screen = [p for p in pieces if p[0] == "screen_frame"]
        grille = [p for p in pieces if p[0] == "grille"]
        self.assertEqual(len(guides), 2)
        self.assertAlmostEqual(max(p[2][1] for p in screen), 0.065)          # (against the frame)
        self.assertLessEqual(max(p[2][1] for p in guides), min(p[1][1] for p in screen) + 1e-9)   # (each further
        self.assertLessEqual(max(p[2][1] for p in grille), min(p[1][1] for p in guides) + 1e-9)   # out)
        box = [p for p in pieces if p[0] == "shutter" and p[1][2] >= 1.2 - 1e-9][0]
        self.assertTrue(np.allclose(box[1], (0.0, 0.0, 1.2)) and np.allclose(box[2], (1.0, 0.2, 1.4)))
        slats = [p for p in pieces if p[0] == "shutter" and p[2][0] - p[1][0] < 1.0 and p[2][0] - p[1][0] > 0.5][0]
        self.assertAlmostEqual(slats[1][2], 1.2 - 0.5 * 1.2)
        self.assertEqual(len(jn.outside(jn.window(("left",)), 1.0, 1.4, 0.065, 0.135)), 0)
        self.assertAlmostEqual(jn.glazing_fraction(jn.window(("fixed",), hardware=False), 1.0, 1.0), 0.81)
        self.assertEqual(jn.glazing_fraction(jn.door("left"), 0.9, 2.1), 0.0)
        self.assertIn("rede", jn.meshes(w, 1.0, 1.4, 0.065, 0.135))


class JoineryArches(unittest.TestCase):
    """0.294 — arched heads: a round arch's outline (its jambs to the springing half its width under the top, the half
    circle over), a segmental one's (its rise as given; up to half the width), a pointed one's (√3/2 of the width,
    its crown at the middle); a polygon cut by a convex one; a prism closed, its faces outwards; an arched window — its
    arch a fanlight over its leaves, its frame's head a band of 24 pieces, its jambs to the springing, its fanlight's
    glass under the arch —; a leaf reaching into the arch refused; its glazing fraction over its outline's area."""

    def test_arches(self):
        from arqbim.core import joinery as jn
        w = jn.window(("fixed",), arch="round")
        ring = jn.outline(w, 1.0, 1.5)
        self.assertEqual(len(ring), 2 + jn.ARCH_STEPS + 1)
        self.assertTrue(np.allclose(ring[2], (1.0, 1.0)) and np.allclose(ring[-1], (0.0, 1.0)))
        self.assertAlmostEqual(max(z for _x, z in ring), 1.5)
        self.assertGreater(jn._area(ring), 0.0)                              # (counter-clockwise)
        seg = jn.window(("fixed",), arch="segmental", arch_rise=0.2)
        self.assertAlmostEqual(jn.arch_rise(seg, 1.2), 0.2)
        self.assertAlmostEqual(max(z for _x, z in jn.outline(seg, 1.2, 1.4)), 1.4)
        self.assertAlmostEqual(jn.arch_rise(jn.window(("fixed",), arch="segmental"), 1.2), 0.2)   # (a sixth)
        pointed = jn.outline(jn.window(("fixed",), arch="pointed"), 1.0, 2.0)
        crown = max(pointed[2:], key=lambda p: p[1])
        self.assertTrue(np.allclose(crown, (0.5, 2.0)))
        self.assertAlmostEqual(jn.arch_rise(jn.window(("fixed",), arch="pointed"), 1.0), math.sqrt(3) / 2)
        square = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]
        diamond = [(1.0, 0.0), (2.0, 1.0), (1.0, 2.0), (0.0, 1.0)]
        self.assertAlmostEqual(jn._area(jn.clip_convex(square, diamond)), 4.0 - 4 * 0.5)
        self.assertEqual(jn.clip_convex(square, [(5.0, 5.0), (6.0, 5.0), (6.0, 6.0)]), [])
        verts, tris = jn.prism_mesh(ring, 0.0, 0.1)
        t = verts[tris]
        volume = float(np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])).sum()) / 6
        self.assertAlmostEqual(volume, jn._area(ring) * 0.1, places=9)      # (closed, its faces outwards)
        arched = jn.with_arch(jn.window(("left", "right")), "round", 1.0)
        self.assertEqual((len(arched.rows), arched.rows[1].height), (2, 0.5))
        self.assertEqual(jn.problems(arched, 1.0, 1.5), [])
        parts = jn.pieces(arched, 1.0, 1.5, 0.0, 0.07)
        band = [p for p in parts if p[0] == "frame" and len(p[1]) > 8]          # (one piece: no joints)
        self.assertEqual(len(band), 1)
        self.assertEqual(len(band[0][1]), 2 * (jn.ARCH_STEPS + 1))
        self.assertTrue(min(z for _x, z in band[0][1]) >= 1.0 - 1e-9 and jn._area(band[0][1]) > 0)
        verts, tris = jn.prism_mesh(band[0][1], 0.0, 0.07)
        t = verts[tris]
        self.assertAlmostEqual(float(np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])).sum()) / 6,
                               jn._area(band[0][1]) * 0.07, places=9)          # (not convex: closed all the same)
        jambs = [p for p in parts if p[0] == "frame" and max(x for x, _z in p[1]) <= arched.frame + 1e-9]
        self.assertTrue(jambs and all(max(z for _x, z in p[1]) <= 1.0 + 1e-9 for p in jambs))
        glass = [p for p in parts if p[0] == "glass" and min(z for _x, z in p[1]) > 1.0]
        self.assertEqual(len(glass), 1)
        self.assertTrue(all((x - 0.5) ** 2 + (z - 1.0) ** 2 <= (0.5 - arched.frame) ** 2 + 1e-9 for x, z in glass[0][1]))
        into = dataclasses.replace(jn.window(("slide_left", "slide_right")), arch="round")      # (0.296: sliding
        self.assertEqual([k for k, _v in jn.problems(into, 1.0, 1.5)], ["joinery.err_arch_leaf"] * 2)   # ones)
        self.assertEqual([k for k, _v in jn.problems(jn.with_arch(jn.window(("fixed",)), "segmental", 1.0, 0.8),
                                                     1.0, 1.5)], ["joinery.err_arch"])
        self.assertLess(jn.glazing_fraction(arched, 1.0, 1.5), 0.9)
        self.assertEqual(jn.from_json(jn.to_json(arched)), arched)


class JoineryArchLeaves(unittest.TestCase):
    """0.296 — leaves under an arch: a pair of casements reaching into a round arch — each its stiles, its bottom rail
    and its head along the curve (one piece), its glass cut by the curve a leaf's frame in from it; their hinges, handles
    and signs within the arch; a tilt and turn one, a bottom-hung fanlight in the half circle — no warning; a sliding,
    top-hung or folding one refused there; an arch chosen keeps the fanlight's leaf that can open under it."""

    def test_arch_leaves(self):
        from arqbim.core import joinery as jn
        w = dataclasses.replace(jn.window(("left", "right")), arch="round")
        self.assertEqual(jn.problems(w, 1.2, 1.8), [])
        spring, f, s = 1.8 - 0.6, w.frame, w.sash
        pieces = jn.pieces(w, 1.2, 1.8, 0.0, 0.07)
        leaf = [p for r, p, _a, _b in pieces if r == "leaf"]
        self.assertEqual(len(leaf), 2 * 4)                                   # (stiles, bottom rail, head)
        heads = [p for p in leaf if max(x for x, _z in p) - min(x for x, _z in p) > 0.3]
        heads = [p for p in heads if min(z for _x, z in p) > spring - 1e-9]
        self.assertEqual(len(heads), 2)                                      # (one piece each)
        for x, z in (pt for p in leaf for pt in p):
            if z > spring:                                                   # (under the frame's curve)
                self.assertLessEqual((x - 0.6) ** 2 + (z - spring) ** 2, (0.6 - f) ** 2 + 1e-6)
        glass = [p for r, p, _a, _b in pieces if r == "glass"]
        self.assertEqual(len(glass), 2)
        for x, z in (pt for p in glass for pt in p):
            if z > spring:                                                   # (a leaf's frame in from it)
                self.assertLessEqual((x - 0.6) ** 2 + (z - spring) ** 2, (0.6 - f - s) ** 2 + 1e-6)
        region = jn.outline(w, 1.2, 1.8, 0.0, bottom=-1.0)
        for r, p, _a, _b in pieces:
            if r == "hardware":
                self.assertTrue(jn.clip_convex(p, region), p)
        inside = jn.outline(w, 1.2, 1.8, f - 1e-6, bottom=-1.0)
        for line in jn.elevation_signs(w, 1.2, 1.8):
            for x, z in line:
                self.assertTrue(jn.clip_convex(jn._quad(x - 1e-4, x + 1e-4, z - 1e-4, z + 1e-4), inside))
        lights = jn.layout(w, 1.2, 1.8)[0]
        self.assertTrue(jn.in_arch(w, 1.2, 1.8, lights[0]))
        self.assertGreater(len(jn.light_outline(w, 1.2, 1.8, lights[0])), 4)
        self.assertAlmostEqual(jn.head_at(w, 1.2, 1.8, 0.6, f), 1.8 - f)
        for rows in ((("tilt_left",),), (("pivot_v",),)):
            self.assertEqual(jn.problems(dataclasses.replace(jn.window(*rows), arch="pointed"), 1.2, 1.8), [])
        fan = jn.with_arch(jn.window(("left", "right"), ("bottom",)), "round", 1.2)
        self.assertEqual((fan.rows[1].cells[0].operation, jn.problems(fan, 1.2, 1.8)), ("bottom", []))
        self.assertEqual(jn.with_arch(jn.window(("left",), ("top",)), "round", 1.2).rows[1].cells[0].operation, "fixed")
        for op in ("top", "fold_left"):
            self.assertEqual([k for k, _v in jn.problems(dataclasses.replace(jn.window((op,)), arch="round"),
                                                         1.2, 1.8)], ["joinery.err_arch_leaf"])


class JoineryColumns(unittest.TestCase):
    """0.306 (the Caixilho Studio's way): a window 2,40 × 1,50 by columns — three columns of 0,80, each a bottom-hung
    light 0,40 over a cell 1,10 — has two mullions its whole height and a transom in each column, six lights numbered
    from the bottom of their column; two single leaves that close on each other have no mullion; a door by columns (a
    fanlight over a leaf, a fanlight over a frosted light) opens SWING_FIXED_LEFT; the windows' partitioning; the new
    fills (frosted glass, wood, louvres in slats) and their materials; mirrored; kept as text."""

    def _window(self):
        from arqbim.core import joinery as j
        col = j.Row((j.Cell("bottom", "glass", 0.40), j.Cell("left", "glass", 1.10)), 0.80)
        mid = j.Row((j.Cell("bottom", "glass", 0.40), j.Cell("fixed", "glass", 1.10)), 0.80)
        right = j.Row((j.Cell("bottom", "glass", 0.40), j.Cell("right", "glass", 1.10)), 0.80)
        return j.Design(kind="window", rows=(col, mid, right), columns=True, bottom=True)

    def test_layout(self):
        from arqbim.core import joinery as j
        d = self._window()
        lights, bars = j.layout(d, 2.4, 1.5)
        self.assertEqual(len(lights), 6)
        mullions = [b for b in bars if b[1] - b[0] < 0.1 and b[3] - b[2] > 1.0]
        transoms = [b for b in bars if b[3] - b[2] < 0.1]
        self.assertEqual((len(mullions), len(transoms)), (2, 3))
        self.assertAlmostEqual((mullions[0][0] + mullions[0][1]) / 2, 0.80)
        self.assertAlmostEqual((transoms[0][2] + transoms[0][3]) / 2, 1.5 - 0.40)
        top = [lt for lt in lights if lt.row == 1]
        self.assertEqual([lt.cell.operation for lt in sorted(top, key=lambda lt: lt.index)], ["bottom"] * 3)
        self.assertEqual(j.window_partitioning(d), ("USERDEFINED", "2+2+2"))
        pair = j.Design(kind="window", rows=(j.Row((j.Cell("left"),)), j.Row((j.Cell("right"),))), columns=True)
        self.assertEqual(j.layout(pair, 1.6, 1.3)[1], [])                       # (they close on each other)
        self.assertEqual(j.window_partitioning(pair)[0], "DOUBLE_PANEL_VERTICAL")
        single = j.Design(kind="window", rows=(j.Row((j.Cell("bottom"), j.Cell("tilt_left"))),), columns=True)
        self.assertEqual(j.window_partitioning(single)[0], "DOUBLE_PANEL_HORIZONTAL")
        transoms, mullions = j.bars_offsets(d, 2.4, 1.5)
        self.assertEqual((len(transoms), [round(m, 4) for m in mullions]), (1, [0.3333, 0.6667]))
        self.assertEqual(j.problems(d, 2.4, 1.5), [])
        self.assertTrue(any(k == "joinery.err_widths" for k, _v in j.problems(d, 3.0, 1.5)))

    def test_door_and_fills(self):
        from arqbim.core import joinery as j
        door = j.Design(kind="door", columns=True, bottom=False, frame=0.07, depth=0.0, sash=0.10, sash_depth=0.04,
                        rows=(j.Row((j.Cell("fixed", "glass", 0.45), j.Cell("left", "wood", 2.20)), 1.0),
                              j.Row((j.Cell("fixed", "glass", 0.45), j.Cell("fixed", "frosted", 2.20)), 0.5)))
        self.assertEqual(j.door_operation(door), ("SWING_FIXED_LEFT", None))
        roles = {role for role, *_r in j.pieces(door, 1.5, 2.65, 0.0, 0.2)}
        self.assertTrue({"wood", "frosted", "glass", "frame"} <= roles)
        mats = j.meshes(door, 1.5, 2.65, 0.0, 0.2)
        self.assertTrue({"vidro_fosco", "madeira", "vidro"} <= set(mats))
        self.assertEqual(j.constituents(door)[1:], [("Framing", "madeira"), ("Glazing", "vidro")])
        vent = j.Design(kind="window", columns=True, rows=(j.Row((j.Cell("fixed", "louvre"),)),))
        slats = [p for p in j.pieces(vent, 0.6, 0.6, 0.0, 0.07) if p[0] == "vent"]
        self.assertGreater(len(slats), 8)
        self.assertGreater(len(j.meshes(vent, 0.6, 0.6, 0.0, 0.07)[vent.frame_material][1]), 8 * 12 - 1)
        mirror = j.mirrored(door)
        self.assertEqual([c.cells[-1].operation for c in mirror.rows], ["fixed", "right"])
        self.assertEqual(j.from_json(j.to_json(door)), door)
        self.assertEqual(j.from_json(j.to_json(vent)), vent)


class CaixilhoModel(unittest.TestCase):
    """0.307 (the Caixilho Studio's model): the prototype's J01 made a design by columns; a mullion dropped in, one too
    near refused; a transom in every column (linked) or one only; a linked transom moved moves them all, one alone
    snaps to its middle; mullions and transoms taken out; columns made equal; sizes typed with sums; a panel's way
    copied along its row; the whole width from the left; a window made a door; read back from its design (and a door
    by rows made a grid); its metrics; the presets all right as designs."""

    def test_editing(self):
        from arqbim.core import caixilho as cx
        op = cx.default_window()
        self.assertEqual(cx.ifc_class(op), "IfcWindow · USERDEFINED")
        two = cx.PRESETS[0][1]()
        self.assertTrue(cx.insert_col(two, 400))
        self.assertEqual(cx.widths(two), [400, 400, 800])
        self.assertFalse(cx.insert_col(two, 100))
        self.assertTrue(cx.insert_row(two, 500))                                # (linked: every column)
        self.assertEqual([len(c.panels) for c in two.cols], [2, 2, 2])
        self.assertTrue(cx.insert_row(two, 900, only_x=1000))                   # (that column only)
        self.assertEqual([len(c.panels) for c in two.cols], [2, 2, 3])
        self.assertTrue(cx.move_boundary(two, 0, 500, 600, linked=True))
        self.assertEqual([c.panels[0].h for c in two.cols], [600, 600, 600])
        self.assertTrue(cx.move_boundary(two, 0, 600, 640, linked=False, snap=50))   # (near its middle: on it)
        self.assertEqual(two.cols[0].panels[0].h, 650)
        cx.merge_row(two, 2, 1, linked=False)
        self.assertEqual([len(c.panels) for c in two.cols], [2, 2, 2])
        cx.merge_col(two, 0)
        self.assertEqual(cx.widths(two), [800, 800])
        cx.move_mullion(two, 0, 820, snap=30)
        self.assertEqual(cx.widths(two), [800, 800])
        op.W = 1000
        cx.equalize(op)
        self.assertEqual(cx.widths(op), [333, 333, 334])
        self.assertEqual(cx.evaluate("2400/3"), 800)
        self.assertEqual(cx.evaluate("1200 + 2*150"), 1500)
        self.assertIsNone(cx.evaluate("abc"))
        self.assertIsNone(cx.evaluate("2*(3"))
        op = cx.default_window()
        self.assertTrue(cx.set_size(op, "c0", "2400/3 + 100", linked=True))
        self.assertEqual(cx.widths(op), [900, 700, 800])
        self.assertTrue(cx.set_size(op, "W", "3000", linked=True))
        self.assertEqual((op.W, sum(cx.widths(op))), (3000, 3000))
        self.assertTrue(cx.set_size(op, "r0_0", "500", linked=True))
        self.assertEqual([c.panels[0].h for c in op.cols], [500, 500, 500])
        op.cols[0].panels[1].op = "tilt_left"
        cx.copy_along_row(op, 0, 1)
        self.assertEqual([c.panels[1].op for c in op.cols], ["tilt_left"] * 3)
        cx.resize(op, W=3200, from_left=True)
        self.assertEqual((op.W, op.cols[0].w), (3200, 1125 + 200))
        cx.set_kind(op, "door")
        self.assertEqual((op.kind, op.sill, op.cols[0].panels[1].op), ("door", 0, "fixed"))

    def test_designs(self):
        from arqbim.core import caixilho as cx
        from arqbim.core import joinery as j
        op = cx.default_window()
        back = cx.from_design(cx.to_design(op), op.W / 1000, op.H / 1000, op.sill / 1000, op.name)
        self.assertTrue(cx.same(op, back))
        self.assertEqual(cx.profile_material(op), "aluminio_grafite")
        self.assertEqual(cx.problems(op), [])
        grid = cx.from_design(j.door("left", "right", transom=0.5), 1.6, 2.6)
        self.assertEqual([[(p.h, p.op) for p in c.panels] for c in grid.cols],
                         [[(500, "fixed"), (2100, "left")], [(500, "fixed"), (2100, "right")]])
        self.assertEqual(grid.system, "madeira")
        other = cx.from_design(j.window(("fixed",), frame_material="inox"), 1.0, 1.0)
        self.assertEqual(cx.profile_material(other), "inox")
        m = cx.metrics(cx.PRESETS[3][1]())
        self.assertGreater(m["glass"], 0.2)
        self.assertAlmostEqual(m["open"], 1.0 * 2.2)
        for label, make in cx.PRESETS:
            self.assertEqual(cx.problems(make()), [], label)


class CaixilhoEqual(unittest.TestCase):
    """0.309: «equal widths» and «equal heights» as parameters of the type — on, every column as wide and each
    column's panels as high, kept after a mullion or a transom put in or taken out and its whole size changed; a mullion
    or a transom moved by hand (or a column's width typed) turns it off; kept in its design as sizes 0 (sharing equally
    whatever size the type is made), read back from it."""

    def test_kept(self):
        from arqbim.core import caixilho as cx
        op = cx.default_window()                                    # (2400 × 1500: 800 | 800 | 800, 400 over 1100)
        op.cols[0].w, op.cols[1].w = 700, 900
        cx.set_equal(op, cols=True, rows=True)
        self.assertEqual(cx.widths(op), [800, 800, 800])
        self.assertEqual([cx.heights(c) for c in op.cols], [[750, 750]] * 3)
        self.assertTrue(cx.insert_col(op, 400))
        cx.keep_equal(op)
        self.assertEqual(cx.widths(op), [600, 600, 600, 600])
        self.assertTrue(cx.insert_row(op, 300, only_x=100))
        cx.keep_equal(op)
        self.assertEqual(cx.heights(op.cols[0]), [500, 500, 500])
        self.assertEqual(cx.heights(op.cols[1]), [750, 750])
        self.assertTrue(cx.set_size(op, "W", "2000", linked=True))
        cx.keep_equal(op)
        self.assertEqual(cx.widths(op), [500, 500, 500, 500])
        cx.resize(op, H=1600)
        cx.keep_equal(op)
        self.assertEqual(cx.heights(op.cols[1]), [800, 800])
        self.assertEqual(cx.heights(op.cols[0]), [533, 533, 534])
        cx.merge_col(op, 0)
        cx.keep_equal(op)
        self.assertEqual(cx.widths(op), [666, 666, 668])
        cx.move_mullion(op, 0, 700)                                 # (by hand: its own width)
        self.assertEqual((op.eq_cols, op.eq_rows), (False, True))
        self.assertTrue(cx.set_size(op, "r1_0", "600", linked=False))
        self.assertEqual((op.eq_cols, op.eq_rows), (False, False))
        self.assertEqual(cx.heights(op.cols[1]), [600, 1000])
        cx.keep_equal(op)                                           # (off: as they are)
        self.assertEqual(cx.widths(op), [700, 632, 668])
        other = cx.default_window()
        cx.set_equal(other, cols=True)
        self.assertTrue(cx.set_size(other, "c1", "1000", linked=True))
        self.assertEqual((other.eq_cols, cx.widths(other)), (False, [800, 1000, 600]))

    def test_designs(self):
        from arqbim.core import caixilho as cx
        from arqbim.core import joinery as j
        op = cx.default_window()
        cx.set_equal(op, cols=True, rows=True)
        design = cx.to_design(op)
        self.assertEqual({c.height for c in design.rows}, {0.0})
        self.assertEqual({cell.width for c in design.rows for cell in c.cells}, {0.0})
        back = cx.from_design(j.from_json(j.to_json(design)), 2.4, 1.5, 0.9, "J01")
        self.assertEqual((back.eq_cols, back.eq_rows), (True, True))
        self.assertTrue(cx.same(op, back))
        wide = cx.from_design(design, 3.0, 1.5, 0.9)                # (the type made 3 m wide in its table)
        self.assertEqual(cx.widths(wide), [1000, 1000, 1000])
        transoms, mullions = j.bars_offsets(design, 3.0, 1.5)
        for got, want in zip(mullions, (1 / 3, 2 / 3)):
            self.assertAlmostEqual(got, want)
        for hs in j.column_heights(design, 1.5):
            self.assertAlmostEqual(hs[0], hs[1])
        plain = cx.from_design(cx.to_design(cx.default_window()), 2.4, 1.5, 0.9)
        self.assertEqual((plain.eq_cols, plain.eq_rows), (False, False))
        single = cx.PRESETS[2][1]()                                 # (one column, one panel: nothing to keep equal)
        single.eq_cols = single.eq_rows = True
        back = cx.from_design(cx.to_design(single), 0.9, 2.1)
        self.assertEqual((back.eq_cols, back.eq_rows), (False, False))


class CaixilhoTheme(unittest.TestCase):
    """0.308: the studio in the program's theme — the light one now (its header's dark blue, its blue); the
    prototype's dark one kept, with every colour the light one has."""

    def test_themes(self):
        from arqbim.ui import caixilho_studio as cs
        from arqbim.ui import theme
        self.assertEqual(cs.THEME, "light")
        self.assertEqual(set(cs.THEMES["light"]), set(cs.THEMES["dark"]))
        self.assertEqual((cs.C["header"], cs.C["accent"], cs.C["bar"]), ("#1f2a37", "#2f6fe4", "#f6f7f9"))
        self.assertIs(cs.THEMES, theme.THEMES)                     # (0.338: the program's themes, one place)


class JoineryLouvres(unittest.TestCase):
    """0.295 — portadas de lâminas: a pair shut in the opening flush with the wall's outer face, standing on the
    peitoril, each leaf its stiles and rails and its lâminas about 4,5 cm apart, falling outwards; open: each turned
    half round on its hinges, flat on the wall beside the opening, its lâminas falling to the wall; one leaf hinged on
    a side, its mirror's on the other; under a round arch cut by it, its head one piece; a door's (taller) with a
    middle rail, in its plan; out of the wall's face when the reveal is taken; not with an estore; kept in its text."""

    def test_louvres(self):
        from arqbim.core import joinery as jn
        w = jn.window(("left", "right"), stone=0.03, louvres="pair")
        shut = jn.louvres(w, 1.2, 1.5, 0.115, (0.0, 0.30))
        leaves = [p for p in shut if p[0] in ("portada", "louvre")]
        self.assertEqual({(round(a, 6), round(b, 6)) for _r, _p, a, b in leaves}, {(0.0, 0.035)})   # (flush)
        xs = [x for _r, p, _a, _b in leaves for x, _z in p]
        zs = [z for _r, p, _a, _b in leaves for _x, z in p]
        self.assertTrue(np.allclose((min(xs), max(xs), min(zs), max(zs)), (0.0, 1.2, 0.03, 1.5)))
        slats = [p for r, p, _a, _b in shut if r == "louvre"]
        self.assertEqual(len(slats), 2 * round((1.5 - 0.03 - 0.10 - 0.06) / jn.LOUVRE_PITCH))
        self.assertEqual(len([p for p in shut if p[0] == "portada"]), 2 * 4)              # (stiles and rails)
        self.assertEqual(len([p for p in shut if p[0] == "hardware"]), 2 * 2)             # (two hinges each)
        verts, _tris = jn.slat_mesh(slats[0], 0.0, 0.035, True)
        n = len(verts) // 2
        self.assertLess(verts[:n, 2].mean(), verts[n:, 2].mean())                        # (falling outwards)
        opened = jn.louvres(dataclasses.replace(w, louvres_open=True), 1.2, 1.5, 0.115, (0.0, 0.30))
        leaves = [p for p in opened if p[0] in ("portada", "louvre_in")]
        xs = [x for _r, p, _a, _b in leaves for x, _z in p]
        self.assertTrue(np.allclose((min(xs), max(xs)), (-0.598, 1.798)))                # (beside the opening)
        self.assertEqual({(round(a, 6), round(b, 6)) for _r, _p, a, b in leaves}, {(-0.035, 0.0)})   # (on the wall)
        self.assertTrue(all(jn._area(p) > 0 for _r, p, _a, _b in opened))
        self.assertNotIn("louvre", {p[0] for p in opened})
        one = jn.window(("left",), louvres="right", louvres_open=True)
        xs = [x for r, p, _a, _b in jn.louvres(one, 0.6, 1.0, 0.1) if r == "portada" for x, _z in p]
        self.assertTrue(np.allclose((min(xs), max(xs)), (0.6, 1.2)))                    # (hinged on the right)
        self.assertEqual(jn.mirrored(one).louvres, "left")
        arched = jn.with_arch(w, "round", 1.2)
        cut = jn.louvres(arched, 1.2, 1.5, 0.115, (0.0, 0.30))
        spring = 1.5 - 0.6
        self.assertTrue(all((x - 0.6) ** 2 + (z - spring) ** 2 <= 0.6 ** 2 + 1e-6
                            for r, p, _a, _b in cut if r != "hardware" for x, z in p if z > spring))
        heads = [p for r, p, _a, _b in cut if r == "portada" and max(z for _x, z in p) > spring + 0.3
                 and max(x for x, _z in p) - min(x for x, _z in p) > 0.2]
        self.assertEqual(len(heads), 2)                                                  # (one piece each)
        door = jn.door("left", "right", louvres="pair")
        frames = [p for r, p, _a, _b in jn.louvres(door, 1.4, 2.2, 0.0, (0.0, 0.3)) if r == "portada"]
        self.assertEqual(len(frames), 2 * 5)                                             # (a middle rail)
        plan = jn.plan_symbol(door, 1.4, 2.2, 0.0, 0.3, (0.0, 0.3))
        self.assertEqual(len([line for line in plan if np.allclose([y for _x, y in line][:4],
                                                                   (-0.035, -0.035, 0.0, 0.0))]), 2)   # (its lining
        #                                                                     the wall's depth: they are out of it)
        out = jn.louvres(dataclasses.replace(w, screen=True, grille=True), 1.2, 1.5, 0.0, (0.0, 0.3))
        self.assertAlmostEqual(max(b for r, _p, _a, b in out if r == "portada"),
                               -jn.SCREEN[1] - jn.BAR - 0.016)                         # (out of the face)
        self.assertEqual([k for k, _v in jn.problems(dataclasses.replace(w, shutter=0.2), 1.2, 1.5)],
                         ["joinery.err_louvres_shutter"])
        self.assertEqual([k for k, _v in jn.problems(jn.window(("fixed",), louvres="pair"), 0.3, 1.5)],
                         ["joinery.err_louvres_small"])
        self.assertEqual(jn.from_json(jn.to_json(dataclasses.replace(w, louvres_open=True))).louvres_open, True)
        self.assertIn("madeira", jn.meshes(w, 1.2, 1.5, 0.115, 0.185, (0.0, 0.30)))


class StairRailingSides(unittest.TestCase):
    """0.261: a stair's railings one each side, all the way up — straight: its two sides; an L (left) and a U: from
    the first nosing (17,5 cm up) to the floor above (2,80), level at the landing (1,40) between, the outer one round
    the landing's edges, the U's inner one turning round the well one tread past the last riser; turned right, the
    mirror image."""

    def test_sides(self):
        from arqbim.core import stairs
        straight = stairs.railing_sides("straight", 2.8, 1.0, 0.28)
        self.assertEqual(len(straight), 2)
        for form in ("l", "u", "v"):
            sides = stairs.railing_sides(form, 2.8, 1.0, 0.28, "left")
            self.assertEqual(len(sides), 2, form)
            for path in sides:
                self.assertAlmostEqual(path[0][2], 0.175, places=9)
                self.assertAlmostEqual(path[-1][2], 2.8, places=9)
                self.assertTrue(any(abs(z - 1.4) < 1e-9 for _x, _y, z in path))
                zs = [z for _x, _y, z in path]
                self.assertEqual(zs, sorted(zs))                                # (never down)
            inner, outer = sides
            self.assertGreater(len(outer), len(inner) - (1 if form == "l" else 0))
            right = stairs.railing_sides(form, 2.8, 1.0, 0.28, "right")
            for a, b in zip(sides, right):
                self.assertTrue(all(abs(p[1] + q[1]) < 1e-9 and abs(p[0] - q[0]) < 1e-9 for p, q in zip(a, b)))
        inner = stairs.railing_sides("u", 2.8, 1.0, 0.28)[0]
        turn = [p for p in inner if abs(p[0] - (7 * 0.28 + 0.28)) < 1e-9]
        self.assertEqual(len(turn), 2)                                          # (round the well)


class RailingParts(unittest.TestCase):
    """0.258: the pieces of a 3,6 m railing (1,00 high) of each kind: bars — 4 posts (at most 1,20 apart), no clear
    gap between bars over the type's; cables through the posts; glass held by four clamps a pane; glass in a base
    channel — no posts, the channel, a pane every 1,50 at most; a zigzag — bars from the foot to the top and back;
    a handrail on its left, on brackets; a closed path: a post at each corner, none doubled; every type sound."""

    def test_parts(self):
        from arqbim.core import railing_types as rail
        line = [(0.0, 0.0, 0.0), (3.6, 0.0, 0.0)]

        def of(parts, kind=None, mat=None):
            return [p for p in parts if (kind is None or p[0] == kind) and (mat is None or p[-1] == mat)]

        def upright(p):
            return p[0] == "bar" and abs(p[1][0] - p[2][0]) < 1e-9 and abs(p[1][1] - p[2][1]) < 1e-9

        rt = rail.PRESETS["barras"]
        parts = rail.parts(line, rt)
        posts = [p for p in parts if upright(p) and p[4] == rt.post_w and p[-1] == rt.post_mat and p[3] == "square"
                 and abs(p[2][2] - (1.0 - rt.top_h)) < 1e-9 and abs(p[1][2]) < 1e-9]
        self.assertEqual(sorted(round(p[1][0], 6) for p in posts), [0.0, 1.2, 2.4, 3.6])
        bars = sorted(p[1][0] for p in parts if upright(p) and p[4] == rt.bar_w)
        faces = [0.0, 1.2, 2.4, 3.6]
        for x0, x1 in zip(bars, bars[1:]):
            if not any(x0 < f < x1 for f in faces):
                self.assertLessEqual(x1 - x0 - rt.bar_w, rt.gap + 1e-9)
        cables = of(rail.parts(line, rail.PRESETS["cabos"]), "bar", "inox")
        level = [p for p in cables if abs(p[1][2] - p[2][2]) < 1e-9 and p[3] == "round"]
        self.assertTrue(level)
        self.assertTrue(all(abs(p[1][0] - round(p[1][0] / 1.2) * 1.2) < 1e-9 for p in level))   # (from post to post)
        glass = rail.parts(line, rail.PRESETS["vidro_grampos"])
        panes = of(glass, "pane")
        self.assertEqual(len(panes), 3)
        clamps = [p for p in glass if upright(p) and abs(p[2][2] - p[1][2] - rail.CLAMP[0]) < 1e-9]
        self.assertEqual(len(clamps), 4 * len(panes))
        channel = rail.parts(line, rail.PRESETS["vidro_perfil"])
        self.assertFalse([p for p in channel if upright(p)])                           # (no posts)
        self.assertEqual(len(of(channel, "pane")), 3)                                    # (3,6 m: panes of 1,20)
        self.assertTrue([p for p in channel if p[0] == "bar" and p[5] == rail.PRESETS["vidro_perfil"].shoe_h])
        zig = rail.parts(line, rail.PRESETS["ziguezague"])
        rt = rail.PRESETS["ziguezague"]
        diag = [p for p in zig if p[0] == "bar" and p[4] == rt.bar_w and not upright(p) and abs(p[1][2] - p[2][2]) > 0.5]
        self.assertGreater(len(diag), 10)
        hand = dataclasses.replace(rail.PRESETS["barras"], hand=True, hand_side="left", hand_off=0.08)
        rails = [p for p in rail.parts(line, hand) if p[-1] == "madeira"]
        self.assertTrue(rails and all(abs(p[1][1] - 0.08) < 1e-9 for p in rails))     # (on its left: +y)
        brackets = [p for p in rail.parts(line, hand) if p[0] == "bar" and p[4] == rail.BRACKET]
        self.assertEqual(len(brackets), 2 * 4)
        square = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 2.0, 0.0), (0.0, 2.0, 0.0)]
        posts = [p for p in rail.parts(square, rail.PRESETS["barras"], closed=True)
                 if upright(p) and p[4] == rail.PRESETS["barras"].post_w and p[-1] == "aco" and abs(p[1][2]) < 1e-9
                 and p[3] == "square" and p[2][2] > 0.9]
        corners = {(round(p[1][0], 6), round(p[1][1], 6)) for p in posts}
        self.assertEqual(len(posts), len(corners))                                      # (none doubled)
        self.assertTrue({(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)} <= corners)
        for key, t in rail.PRESETS.items():
            self.assertIsNone(rail.problem(t), key)
            back = rail.from_props(t.name, rail.to_props(t))
            self.assertEqual(back, t, key)


class PlanarUnion(unittest.TestCase):
    """0.257: two boxes side by side, touching along a face: one surface — the faces between them gone, the flush
    faces joined (no seam), the edges a 2 × 1 × 1 box's 12, closed, its volume 2."""

    def test_two_boxes(self):
        from arqbim.core.mesh import TriMesh, planar_union

        def box(x0):
            v = np.array([(x0 + a, b, c) for a in (0, 1) for b in (0, 1) for c in (0, 1)], dtype=float)
            quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
            return v, [(q[0], q[1], q[2]) for q in quads] + [(q[0], q[2], q[3]) for q in quads]

        va, ta = box(0.0)
        vb, tb = box(1.0)
        verts = np.vstack((va, vb))
        tris = np.vstack((np.array(ta), np.array(tb) + len(va)))
        self.assertAlmostEqual(TriMesh(verts, tris).volume(), 2.0, places=9)
        self.assertGreater(len(TriMesh(verts, tris).edge_array()[0]), 12)        # (their seams and the faces between)
        v, t = planar_union(verts, tris)
        mesh = TriMesh(v, t)
        self.assertAlmostEqual(mesh.volume(), 2.0, places=9)
        self.assertEqual(len(mesh.edge_array()[0]), 12)
        self.assertTrue(mesh.is_closed())


class OrientedCutOutlines(unittest.TestCase):
    """0.253: one element's cut outlines turned one way — the outer ones counter-clockwise, its holes (inside an odd
    number of the others) clockwise —, whichever way they came; a ring inside a hole is outer again."""

    def test_oriented(self):
        from arqbim.core import drawing2d

        def square(c, h, ccw=True):
            pts = np.array([(c - h, c - h), (c + h, c - h), (c + h, c + h), (c - h, c + h)], dtype=float)
            return pts if ccw else pts[::-1]

        def area(ring):
            x, y = ring[:, 0], ring[:, 1]
            return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

        rings = drawing2d.oriented([square(0.0, 3.0, False), square(0.0, 2.0), square(0.0, 1.0, False)])
        self.assertEqual([area(r) > 0 for r in rings], [True, False, True])
        self.assertAlmostEqual(sum(area(r) for r in rings), 36.0 - 16.0 + 4.0, places=9)
        self.assertTrue(np.allclose(sorted(map(tuple, rings[0])), sorted(map(tuple, square(0.0, 3.0)))))
        one = drawing2d.oriented([square(5.0, 1.0, False)])
        self.assertGreater(area(one[0]), 0)


class PatternedSurfaces(unittest.TestCase):
    """0.173: on a 4 × 2,6 m face with a door (0,9 × 2,1 m): slats of 4 cm every 6 cm centred on it, those over the
    door cut there (one piece each above it); level ones; a perforated sheet's holes on a grid of 6 cm, only whole
    cells clear of the 5 cm margin round its edges and the door; its mesh — every face turned out (the top's up),
    its cells sharing their edges; the panels it is cut into (boards of 1,22 × 2,44 m cut round the door), each
    perforated on its own (no hole on a joint); its open area."""

    def test_surfaces(self):
        from shapely.geometry import Point, box
        from arqbim.core import surfaces as sf
        face = box(0.0, 0.0, 4.0, 2.6).difference(box(1.0, 0.0, 1.9, 2.1))
        strips = sf.strips(face, 0.04, 0.02, "vertical")
        n = int((4.0 + 0.02) / 0.06)
        over_door = [s for s in strips if s[0] >= 1.0 - 1e-9 and s[2] <= 1.9 + 1e-9]
        self.assertEqual(len(strips), n)                       # (over the door: one piece each, above it)
        self.assertTrue(over_door and all(abs(s[1] - 2.1) < 1e-9 for s in over_door))
        left = min(s[0] for s in strips)
        right = 4.0 - max(s[2] for s in strips)
        self.assertAlmostEqual(left, right, places=9)          # (centred)
        level = sf.strips(box(0, 0, 2, 1), 0.04, 0.02, "horizontal")
        self.assertTrue(all(abs((s[2] - s[0]) - 2.0) < 1e-9 for s in level))
        holes = sf.holes(face, 0.03, 0.06, 0.05)
        inner = face.buffer(-0.05 + 1e-9, join_style=2)
        self.assertTrue(holes and all(inner.contains(Point(u, v).buffer(0.03 - 1e-9)) for u, v in holes))
        verts, tris = sf.perforated_mesh(face, 0.016, 0.03, 0.06, 0.05)
        a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
        normal = np.cross(b - a, c - a)
        top = (np.abs(a[:, 2] - 0.016) < 1e-9) & (np.abs(b[:, 2] - 0.016) < 1e-9) & (np.abs(c[:, 2] - 0.016) < 1e-9)
        self.assertTrue(top.any() and (normal[top][:, 2] > 0).all())
        self.assertEqual(len(tris) >= len(holes) * 72, True)
        panels = sf.panel_holes(face, 0.03, 0.06, 0.05)
        self.assertEqual(len(panels), 8)                       # (4 columns × 2 rows of boards)
        first = panels[0][0]                                   # (0–1,22 × 0–2,44: the door's corner cut out of it)
        self.assertLess(first.area, 1.22 * 2.44 - 0.2 * 2.1 + 1e-6)
        for q, centres in panels:                              # (each panel its own margin: none on a joint)
            inner = q.buffer(-0.05 + 1e-9, join_style=2)
            self.assertTrue(all(inner.contains(Point(u, v).buffer(0.015)) for u, v in centres))
        self.assertFalse(any(abs(u - 1.22) < 0.05 + 0.015 for u, _v in holes))
        self.assertAlmostEqual(sf.open_area(0.03, 0.06), np.pi * 0.03 ** 2 / 4 / 0.06 ** 2, places=12)

    def test_sketch_paint(self):
        """0.392: a sketch's faces keep their paint as SketchUp's do — a painted rectangle pulled up: its top (the face
        moved) keeps it, the sides none; a rectangle drawn on the painted top: both pieces painted; a face divided by a
        line: both halves painted; a face deleted: the others' paint where it was; copied, turned, compacted."""
        from arqbim.core import sketch_geometry as sg
        from arqbim.model import paint
        from arqbim.core.mesh import PolyMesh
        mesh = sg.rectangle_mesh(4.0, 3.0)
        self.assertEqual(mesh.painted(), [None])
        mesh.paint[0] = "tinta_ocre"
        sg.push_pull(mesh, 0, np.eye(4), 2.0)
        top = max(range(len(mesh.faces)), key=lambda g: mesh.face_points(g)[:, 2].mean())
        sides = [g for g in range(len(mesh.faces)) if abs(mesh.face_normal(g)[2]) < 0.5]
        self.assertEqual(mesh.paint_of(top), "tinta_ocre")
        self.assertTrue(sides and all(mesh.paint_of(g) is None for g in sides))
        inner = sg.imprint_polygon(mesh, top, [np.array(p) for p in ((1, 1, 2), (3, 1, 2), (3, 2, 2), (1, 2, 2))])
        self.assertIsNotNone(inner)
        self.assertTrue(all(mesh.paint_of(g) == "tinta_ocre" for g in range(len(mesh.faces))
                            if mesh.face_points(g)[:, 2].min() > 1.99))
        self.assertEqual(len(paint.sketch_face(mesh, inner)), 1)                 # (the inner face alone)
        joined = paint.sketch_connected(mesh, inner)                             # (Ctrl: the top's pieces, ocre)
        self.assertTrue(all(mesh.paint_of(g) == "tinta_ocre" for g in joined) and len(joined) == 5)
        n = len(mesh.faces)
        moved = mesh.copy().transformed(np.diag((1.0, 1.0, 1.0, 1.0)))
        self.assertEqual(moved.painted(), mesh.painted())
        gone = sg.remove_faces(mesh, [inner])
        self.assertEqual(len(gone.faces), n - 1)
        self.assertEqual(sorted(p for p in gone.painted() if p), ["tinta_ocre"] * 5)   # (the frame's 4, the base)
        flat = PolyMesh([(0, 0, 0), (4, 0, 0), (4, 3, 0), (0, 3, 0)], [[0, 1, 2, 3]], paint=["tinta_azul"])
        half = sg.split_face(flat, 0, [np.array((2.0, 0.0, 0.0)), np.array((2.0, 3.0, 0.0))])
        self.assertIsNotNone(half)
        self.assertEqual(flat.painted(), ["tinta_azul", "tinta_azul"])

    def test_organic_roof_forms(self):
        """0.390: an organic roof's forms over a 10 × 6 m rectangle, rise 3 m — the dome 0 along the whole edge, 3 m
        at its middle, lower towards the corners; the vault 3 m along its ridge and at its ends (open arches), 0 along
        its long sides; the wave lower between its crests; the gridshell's bars on a 1,2 m grid from edge to edge; the
        shell a closed solid; a curve through the points clicked."""
        from arqbim.core import organic_roof as orf
        rect = [(0.0, 0.0), (10.0, 0.0), (10.0, 6.0), (0.0, 6.0)]
        dome = orf.Shape(rect, 3.0, "cupula")
        self.assertAlmostEqual(float(dome.height(np.array([[5.0, 3.0]]))[0]), 3.0, delta=0.05)
        self.assertLess(float(dome.height(np.array([[1.0, 1.0]]))[0]), float(dome.height(np.array([[5.0, 1.0]]))[0]))
        v, tr, edge = dome.surface(1.2)
        self.assertTrue(np.allclose(v[edge, 2], 0.0) and v[:, 2].max() > 2.9)
        vault = orf.Shape(rect, 3.0, "abobada")
        h = vault.height(np.array([[5.0, 3.0], [0.0, 3.0], [10.0, 3.0], [5.0, 0.0], [5.0, 1.5]]))
        self.assertTrue(np.allclose(h[:4], (3.0, 3.0, 3.0, 0.0), atol=1e-6))
        self.assertAlmostEqual(float(h[4]), 3.0 * 0.75, places=6)           # (a parabola across)
        wave = orf.Shape(rect, 3.0, "onda")
        self.assertLess(float(wave.height(np.array([[2.5, 3.0]]))[0]), 2.5)  # (between its crests)
        bars = dome.bars(1.2)
        self.assertTrue(all(abs(b[0, 2]) < 1e-9 and abs(b[-1, 2]) < 1e-9 for b in bars))   # (edge to edge)
        self.assertEqual(len(bars), len(dome._lines(1.2, False)) + len(dome._lines(1.2, True)))
        sv, st = dome.shell(1.2, 0.1)
        edges = {}
        for a, b, c in st:
            for e in ((a, b), (b, c), (c, a)):
                edges[e] = edges.get(e, 0) + 1
        self.assertTrue(all(edges.get((b, a), 0) == 1 for (a, b) in edges))   # (closed: each edge both ways)
        smooth = orf.smooth_outline([(0, 0), (4, 0), (4, 3)], 0.25)
        self.assertTrue(any(np.allclose(q, (4, 0)) for q in smooth) and len(smooth) > 20)

    def test_perforation_patterns(self):
        """0.389: a perforated panel's patterns — boards apart by a joint (holes clear of it), a 45° grid (its
        neighbours a pitch apart, along the diagonals), square holes (their mesh's top a square round each), a picture
        (dark on the left: big holes there, none on the white right)."""
        from shapely.geometry import box
        from arqbim.core import surfaces as sf
        face = box(0.0, 0.0, 2.44, 1.2)
        found = sf.perforation(face, 0.02, 0.05, 0.03, (1.22, 2.44), 0.01)
        self.assertEqual(len(found), 2)
        self.assertAlmostEqual(found[0][0].bounds[2], 1.215, places=9)      # (half the joint off each board)
        self.assertTrue(all(c[:, 0].max() < 1.215 for c in [found[0][1]]))
        straight = np.concatenate([c for _q, c, _d in sf.perforation(face, 0.02, 0.05, 0.03)])
        turned = np.concatenate([c for _q, c, _d in sf.perforation(face, 0.02, 0.05, 0.03, grid="diagonal")])
        nearest = lambda c: np.sort(np.linalg.norm(c[1:] - c[0], axis=1))[0]                    # noqa: E731
        self.assertAlmostEqual(nearest(turned), 0.05, places=6)
        d = turned[1:] - turned[0]
        close = d[np.abs(np.linalg.norm(d, axis=1) - 0.05) < 1e-6]
        self.assertTrue(np.allclose(np.abs(close[:, 0]), np.abs(close[:, 1])))   # (along the diagonals)
        self.assertGreater(len(straight), 100)
        verts, tris = sf.perforated_mesh(face, 0.01, 0.02, 0.05, 0.03, hole="quadrado")
        top = verts[np.abs(verts[:, 2] - 0.01) < 1e-9]
        c0 = straight[0]
        ring = top[np.max(np.abs(top[:, :2] - c0), axis=1) < 0.0101]
        self.assertTrue(len(ring) and np.allclose(np.max(np.abs(ring[:, :2] - c0), axis=1), 0.01))   # (a square)
        mask = np.zeros((10, 20))
        mask[:, :10] = 1.0                                                      # (dark left half, white right)
        masked = sf.perforation(face, 0.02, 0.05, 0.03, mask=mask)
        centres = np.concatenate([c for _q, c, _d in masked])
        sizes = np.concatenate([d for _q, _c, d in masked])
        self.assertTrue(len(centres) and (centres[:, 0] < 1.22 + 1e-9).all() and np.allclose(sizes, 0.02))
        v2, t2 = sf.perforated_mesh(face, 0.01, 0.02, 0.05, 0.03, (1.22, 2.44), 0.01, "diagonal", "quadrado", mask)
        a, b, c = v2[t2[:, 0]], v2[t2[:, 1]], v2[t2[:, 2]]
        up = (np.abs(a[:, 2] - 0.01) < 1e-9) & (np.abs(b[:, 2] - 0.01) < 1e-9) & (np.abs(c[:, 2] - 0.01) < 1e-9)
        self.assertTrue(up.any() and (np.cross(b - a, c - a)[up][:, 2] > 0).all())     # (turned back: still up)

    def test_wavy(self):
        """0.175: a wavy surface's ribs on the same face — level ones 18 mm thick every 36 mm, those beside the
        door in two pieces, those above it whole; each one's back on the wall, its front between its trough (2 cm)
        and its crest (8 cm), the wave shifted 90° for each metre up (the waves turning); upright ones over the
        door only above it."""
        from shapely.geometry import Polygon, box
        from arqbim.core import surfaces as sf
        face = box(0.0, 0.0, 4.0, 2.6).difference(box(1.0, 0.0, 1.9, 2.1))
        self.assertAlmostEqual(sf.wave(0.3, 0.06, 1.2, 0.0, 0.02), 0.08, places=12)          # (a crest)
        self.assertAlmostEqual(sf.wave(0.3, 0.06, 1.2, np.pi, 0.02), 0.02, places=12)        # (half a turn: a trough)
        ribs = sf.ribs(face, 0.018, 0.018, 0.06, 1.2, 90.0, 0.02, "horizontal")
        bands = {}
        for a0, a1, outline in ribs:
            bands.setdefault((a0, a1), []).append(outline)
        self.assertEqual(len(bands), int((2.6 + 0.018) / 0.036))
        self.assertTrue(all(len(v) == 2 for (a0, a1), v in bands.items() if a1 <= 2.1))
        self.assertTrue(all(len(v) == 1 for (a0, a1), v in bands.items() if a0 >= 2.1))
        for a0, a1, outline in ribs:
            self.assertEqual((outline[0][1], outline[1][1]), (0.0, 0.0))
            self.assertTrue(all(0.02 - 1e-9 <= w <= 0.08 + 1e-9 for _b, w in outline[2:]))
            self.assertTrue(Polygon(outline).exterior.is_ccw)
            b1, w1 = outline[2]
            self.assertAlmostEqual(w1, sf.wave(b1, 0.06, 1.2, np.radians(90.0) * (a0 + a1) / 2, 0.02), places=12)
        upright = sf.ribs(face, 0.018, 0.018, 0.06, 1.2, 90.0, 0.02, "vertical")
        over = [o for a0, a1, o in upright if a0 >= 1.0 and a1 <= 1.9]
        self.assertTrue(over and all(abs(o[0][0] - 2.1) < 1e-9 for o in over))


class CurvedOpeningsGeometry(unittest.TestCase):
    """0.177: the frame tangent to a curved wall's axis (x along the arc counter-clockwise, y to the centre); the
    depth an opening 90 cm wide must cut through a wall of 5 m radius and 20 cm (the inner face turned in at its
    edges), and none in a tight one; how far along the arc an angle is (beyond its ends: the nearer end; clockwise
    arcs too); an opening's middle kept clear of the ends, and none on an arc too short."""

    def test_curved_openings(self):
        from arqbim.core import arcs
        m = arcs.tangent_frame((0.0, 0.0, 1.0), 5.0, 0.0)
        np.testing.assert_allclose(m[:3, 3], (5.0, 0.0, 1.0), atol=1e-12)
        np.testing.assert_allclose(m[:3, 0], (0.0, 1.0, 0.0), atol=1e-12)
        np.testing.assert_allclose(m[:3, 1], (-1.0, 0.0, 0.0), atol=1e-12)
        lo, hi = arcs.opening_depth(5.0, 0.2, 0.9)
        self.assertAlmostEqual(lo, -0.11, places=12)
        self.assertAlmostEqual(hi, 5.0 - math.sqrt(4.9 ** 2 - 0.45 ** 2) + 0.01, places=12)
        self.assertGreater(hi, 0.1 + 0.01 + 0.02)                      # (the sagitta, about 2 cm)
        self.assertIsNone(arcs.opening_depth(0.5, 0.2, 0.9))
        self.assertAlmostEqual(arcs.along_at(0.0, math.pi / 2, 5.0, math.pi / 4), 5.0 * math.pi / 4, places=12)
        self.assertAlmostEqual(arcs.along_at(0.0, math.pi / 2, 5.0, math.pi), 5.0 * math.pi / 2, places=12)
        self.assertEqual(arcs.along_at(0.0, math.pi / 2, 5.0, -0.1), 0.0)
        self.assertAlmostEqual(arcs.along_at(0.0, -math.pi / 2, 5.0, -math.pi / 4), 5.0 * math.pi / 4, places=12)
        self.assertAlmostEqual(arcs.angle_along(0.0, -math.pi / 2, 5.0, 5.0 * math.pi / 4), -math.pi / 4,
                               places=12)
        self.assertAlmostEqual(arcs.opening_along(0.0, math.pi / 2, 5.0, 0.9, 0.0), 0.5, places=12)
        self.assertIsNone(arcs.opening_along(0.0, 0.1, 5.0, 0.9, 0.05))


class ProfilesSwept(unittest.TestCase):
    """0.174: a skirting board (1,5 × 8 cm) round a 4 × 3 m room (counter-clockwise, into it): a closed solid, every
    face turned out, its volume the section's area times the length of the path its centre runs (Pappus: its corners
    mitred); along an L (open: capped), likewise; the joiner's pieces — 45° mitres, inside corners (+), each piece's
    long point its back — and round a column (outside corners, −: its front the longer); points in a line dropped; a
    path turning back on itself broken there; a section mirrored to the right."""

    @staticmethod
    def volume(verts, tris):
        a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
        return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6.0

    def test_sweep(self):
        from shapely.geometry import Polygon
        from arqbim.core import profiles as pf
        sec = pf.section("rodape", 0.015, 0.08)
        area, ac = Polygon(sec).area, Polygon(sec).centroid.x
        room = [(0, 0), (4, 0), (4, 3), (0, 3)]
        verts, tris = pf.sweep(room, True, sec)
        edges = {}
        for t in tris:                                         # (closed: every edge in two faces, once each way)
            for i in range(3):
                e = (int(t[i]), int(t[(i + 1) % 3]))
                edges[e] = edges.get(e, 0) + 1
        self.assertTrue(all((b, a) in edges for a, b in edges))
        self.assertAlmostEqual(self.volume(verts, tris), area * (14.0 - 8 * ac), places=9)
        verts, tris = pf.sweep([(0, 0), (4, 0), (4, 3)], False, sec)
        self.assertAlmostEqual(self.volume(verts, tris), area * (7.0 - 2 * ac), places=9)
        self.assertAlmostEqual(verts[:, 2].max(), 0.08, places=12)
        cuts = pf.pieces(room, True, 0.015)
        self.assertEqual(sorted(round(c[0], 6) for c in cuts), [3.0, 3.0, 4.0, 4.0])
        self.assertTrue(all(abs(c[1] - 45.0) < 1e-9 and abs(c[2] - 45.0) < 1e-9 for c in cuts))
        column = [(0, 0), (0, 0.3), (0.3, 0.3), (0.3, 0)]          # (clockwise: the profile on its left, outside)
        out = pf.pieces(column, True, 0.015)
        self.assertTrue(all(abs(c[0] - 0.33) < 1e-9 and abs(c[1] + 45.0) < 1e-9 for c in out))
        self.assertEqual(len(pf.clean([(0, 0), (1, 0), (2, 0), (2, 1)], False)), 3)
        self.assertEqual(len(pf.runs([(0, 0), (2, 0), (0, 0.01)], False)), 2)
        right = pf.section("rodape", 0.015, 0.08, side=-1)
        self.assertTrue(all(a <= 0 for a, _b in right) and Polygon(right).exterior.is_ccw)
        self.assertAlmostEqual(pf.foot("sanca", 0.10, 2.80), 2.70, places=12)
        self.assertEqual(pf.foot("rodape", 0.08, 2.80), 0.0)


class Appliances(unittest.TestCase):
    """0.171: the appliances' usual sizes and places — a hob flush on the worktop (90 cm), its cut-out inside its
    plan (56 × 49 cm), a sink's; a dishwisher with its cold water and drain; a gas hob with its gas; a fridge's two
    doors; a hood hung with its chimney."""

    def test_appliances(self):
        from shapely.geometry import Polygon
        from arqbim.core import appliances as app
        from arqbim.core import kitchens
        self.assertAlmostEqual(max(b[5] for b in app.boxes("hob")), app.WORKTOP_TOP, places=9)
        ring = app.cutout_ring("hob", (1.0, 0.0), 0.0)
        cut = Polygon(ring)
        self.assertAlmostEqual(cut.area, 0.56 * 0.49, places=9)
        self.assertTrue(Polygon(kitchens.footprint((1.0, 0.0), 0.0, 0.59, 0.52)).contains(cut))
        self.assertAlmostEqual(Polygon(app.sink_ring((0.0, 0.0), 90.0)).area, 0.76 * 0.46, places=9)
        self.assertIsNone(app.cutout_ring("oven", (0.0, 0.0), 0.0))
        self.assertEqual([p[0] for p in app.ports("dishwasher")], ["cold", "drain"])
        self.assertEqual(app.ports("gas_hob")[0][2], "GAS")
        self.assertEqual(len(app.boxes("fridge")), 3)
        hood = app.boxes("hood")
        self.assertAlmostEqual(min(b[2] for b in hood), 1.55, places=9)


class StructureQuantities(unittest.TestCase):
    """0.167: the formwork of a 20 × 40 beam 6 m long (its sides and soffit: 6,0 m²), of a 30 × 30 column 3 m tall
    (3,6 m²), of a 1,2 × 1,2 × 0,5 footing (its sides: 2,4 m²), of a 6 × 4 slab 15 cm thick (its soffit and edges:
    27,0 m²); the totals by kind and of all; a steel rate out of the usual told (only with bars); the notes worded,
    numbers with the decimal comma, the bars in a few words."""

    def test_quantities(self):
        from arqbim.model import structure_quantities as sq
        self.assertAlmostEqual(sq.formwork("beam", (0.2, 0.4), 6.0), 6.0, places=9)
        self.assertAlmostEqual(sq.formwork("column", (0.3, 0.3), 3.0), 3.6, places=9)
        self.assertAlmostEqual(sq.formwork("footing", perimeter=4.8, thickness=0.5), 2.4, places=9)
        self.assertAlmostEqual(sq.formwork("slab", area=24.0, perimeter=20.0, thickness=0.15), 27.0, places=9)
        rows = [sq.QuantityRow("a", "beam", concrete=0.48, formwork=6.0, steel=40.0, has_bars=True),
                sq.QuantityRow("b", "beam", concrete=0.48, formwork=6.0, steel=10.0, has_bars=True),
                sq.QuantityRow("c", "column", concrete=0.27, formwork=3.6)]
        by_kind, whole = sq.totals(rows)
        self.assertEqual(by_kind["beam"], (0.96, 12.0, 50.0))
        self.assertAlmostEqual(whole[0], 1.23, places=9)
        self.assertFalse(rows[0].implausible)                     # (83 kg/m³: a beam's usual)
        self.assertTrue(rows[1].implausible)                      # (21 kg/m³: too little for a beam)
        self.assertFalse(rows[2].implausible)                     # (no bars: nothing told)

    def test_words(self):
        from arqbim.core import ec2
        from arqbim.model import design_text as dt
        d = ec2.beam(0.30, 0.50, 6.0, 25, 500, 100.0, -80.0, 250.0)
        self.assertEqual(dt.bars_text("beam", d), "inf. 5 Ø12 · sup. 4 Ø12 · estribos Ø8//0,175")
        shear = next(n for n in d.notes if n.code == "shear")
        self.assertIn("Ø8//0,175", dt.note_text(shear))
        self.assertEqual(dt.spacing_text(0.25), "0,25")
        self.assertEqual(dt.spacing_text(0.2), "0,20")
        self.assertEqual(dt.main_note(d).code, "bending")
        self.assertEqual(sorted(["Pilar 10", "Pilar 2"], key=dt.natural), ["Pilar 2", "Pilar 10"])


class StructureAnalysis(unittest.TestCase):
    """0.165: the 6 × 4 m frame with its slab analysed — what comes down (the reactions under G + Q) is what goes
    in (the members' weight and the slab's loads, carried to its beams by their areas: 24 m² shared, none lost); the
    columns compressed; the beams sagging in their spans, hogging over the columns, deflecting a little; the wind's
    drift small; the slab's area shared among its beams as the 45° rule gives (the middle beam the most)."""

    def _model(self):
        from arqbim.core import actions, structural as st
        from arqbim.model import structure_loads
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        cols = [st.Column("c{}".format(k), p, 0.0, 3.0, (0.3, 0.3)) for k, p in enumerate(corners)]
        beams = [st.Beam("b{}".format(k), corners[k], corners[(k + 1) % 4], 3.0, (0.25, 0.5)) for k in range(4)]
        beams.append(st.Beam("bx", (3.0, 0.0), (3.0, 4.0), 3.0, (0.2, 0.4)))
        foots = [st.Footing("f{}".format(k), p, 0.0, (1.2, 1.2)) for k, p in enumerate(corners)]
        panel = st.Panel("s", [(0, 0), (6, 0), (6, 4), (0, 4)], 3.0, 0.2)
        model = st.build(cols, beams, foots, [panel], levels=[0.0, 3.0])
        settings = actions.Settings(use="A", roof_use="A")
        return model, structure_loads.building_actions(model, settings, (), 0.0), settings

    def test_equilibrium_and_signs(self):
        from arqbim.model import structure_analysis as sa
        model, loads, settings = self._model()
        result = sa.analyse(model, loads, settings)
        self.assertEqual(result.error, "")
        self.assertAlmostEqual(result.reactions_up, result.loads_in, delta=result.loads_in * 1e-6)
        slab = (0.2 * 25 + 1.5 + 2.0) * 24.0                 # (G: 5 + 1,5, no partitions on a roof; Q 2,0 — use A)
        self.assertGreater(result.loads_in, slab)
        cols = [m for m in result.members if m.kind == "column"]
        self.assertTrue(all(m.n_min < 0 for m in cols))
        beams = [m for m in result.members if m.kind == "beam"]
        self.assertTrue(all(m.m_pos > 0 for m in beams))
        self.assertTrue(any(m.m_neg < 0 for m in beams))
        self.assertTrue(all(0 < m.deflection < 0.02 for m in beams))
        self.assertLess(result.drift_wind, 1 / 500)

    def test_moment_diagrams(self):
        """0.220: each member's moment diagram under 1,35G+1,50Q: every member there; a beam's ends and its middle as
        its envelope's (hogging over the columns, sagging in its span, the largest in between); drawn away from its
        local z (a beam's: up, so its sagging below); the diagram's ends the span_moment's."""
        from arqbim.core import space_frame as sf
        from arqbim.model import structure_analysis as sa
        model, loads, settings = self._model()
        result = sa.analyse(model, loads, settings)
        self.assertEqual(set(result.diagrams), {m.id for m in result.members})
        self.assertEqual(result.diagram_combo, "1,35G+1,50Q")
        beam = next(m for m in result.members if m.id.startswith("bx"))
        p1, p2, zdir, ms = result.diagrams[beam.id]
        self.assertEqual(len(ms), 11)
        self.assertGreater(zdir[2], 0.99)                                   # (a beam's local z: up)
        self.assertLess(ms[0], 0.0)
        self.assertLess(ms[-1], 0.0)
        self.assertGreater(max(ms), 0.0)
        self.assertLessEqual(max(ms), beam.m_pos + 1e-6)
        self.assertGreaterEqual(min(ms), beam.m_neg - 1e-6)
        self.assertAlmostEqual(float(np.linalg.norm(p2 - p1)), 4.0)
        ends = np.zeros(12)
        ends[2], ends[4] = 30.0, -20.0
        along = sf.moments_along(ends, -15.0, 4.0, 5)
        m1, mspan, m2 = sf.span_moment(ends, -15.0, 4.0)
        self.assertAlmostEqual(along[0], m1)
        self.assertAlmostEqual(along[-1], m2)
        self.assertLessEqual(max(along), mspan + 1e-9)

    def test_shells(self):
        """0.223: the slab as shells (the default) — what goes in comes down; the slab meshed (192 triangles), its
        moments to reinforce for sagging at the bottom and hogging at the top, both ways, its deflection small; the
        middle beam, the most flexible, carrying less than by areas; the beams cut at the mesh's nodes told whole
        (their length, 11 points of their diagram, its ends the envelope's); by areas no slab told; the EC2 slab
        with the shell's moments."""
        import dataclasses
        from arqbim.model import structure_analysis as sa
        from arqbim.model import structure_design as sd
        model, loads, settings = self._model()
        self.assertEqual(settings.slabs, "shells")
        shells = sa.analyse(model, loads, settings)
        self.assertEqual(shells.error, "")
        self.assertAlmostEqual(shells.reactions_up, shells.loads_in, delta=shells.loads_in * 1e-6)
        self.assertEqual(len(shells.panels), 1)
        p = shells.panels[0]
        self.assertEqual(p.triangles, 192)
        self.assertAlmostEqual(shells.shell_size, 0.5)
        self.assertGreater(p.m_x, 0.0)
        self.assertGreater(p.m_y, 0.0)
        self.assertLess(p.m_x_top, 0.0)
        self.assertTrue(0.0 < p.deflection < p.span / 250)
        areas = sa.analyse(model, loads, dataclasses.replace(settings, slabs="areas"))
        self.assertEqual(areas.panels, [])
        self.assertAlmostEqual(areas.loads_in, shells.loads_in, places=6)
        middle = {r.id: r for r in shells.members if r.id.startswith("bx")}
        by_area = {r.id: r for r in areas.members if r.id.startswith("bx")}
        self.assertEqual(set(middle), set(by_area))
        for mid, r in middle.items():
            self.assertAlmostEqual(r.length, 4.0)
            self.assertLess(r.m_pos, by_area[mid].m_pos)
            self.assertGreater(r.deflection, 0.0)
            ms = shells.diagrams[mid][3]
            self.assertEqual(len(ms), 11)
            self.assertLessEqual(max(ms), r.m_pos + 1e-6)
        self.assertEqual(len(shells.members), len(areas.members))
        designs = sd.design_structure(model, shells, loads, settings)
        slab = next(e for e in designs if e.kind == "slab")
        note = next(n for n in slab.design.notes if n.code == "slab_shell")
        self.assertAlmostEqual(max(note.values["m_short"], note.values["m_long"]), max(p.m_x, p.m_y))

    def _tower(self, storeys, col):
        """A 6 × 4 m bay `storeys` high (3 m each), its columns `col` square, in a strong earthquake's zone."""
        from arqbim.core import actions, structural as st
        from arqbim.model import structure_loads
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        cols, beams, panels = [], [], []
        for s in range(storeys):
            z0, z1 = 3.0 * s, 3.0 * (s + 1)
            cols += [st.Column("c{}_{}".format(s, k), p, z0, z1, (col, col)) for k, p in enumerate(corners)]
            beams += [st.Beam("b{}_{}".format(s, k), corners[k], corners[(k + 1) % 4], z1, (0.25, 0.5))
                      for k in range(4)]
            panels.append(st.Panel("s{}".format(s), [(0, 0), (6, 0), (6, 4), (0, 4)], z1, 0.2))
        foots = [st.Footing("f{}".format(k), p, 0.0, (1.2, 1.2)) for k, p in enumerate(corners)]
        model = st.build(cols, beams, foots, panels, levels=[3.0 * s for s in range(storeys + 1)])
        settings = actions.Settings(use="A", roof_use="A", seismic_zone_1="1.1", seismic_zone_2="2.1", ground="D")
        return model, structure_loads.building_actions(model, settings, (), 0.0), settings

    def test_second_order(self):
        """0.222: each storey's θ = P·dr/(V·h) under the wind and the earthquake each way — the one storey's: P its
        weight (earthquake) or 1,35G + 1,50Q (wind), V its force, h 3 m; the same frame's stiffness under both, so
        θ(EX)/θ(WX) is P's ratio × q/0,5 over 1/(0,4/1,2); small (ignored, nothing amplified). Three storeys of 20 cm
        columns: held by the footings only (the upper floors' columns not); V and P summed from the top, θ down to
        the bottom the largest; above 0,10 each action × 1/(1 − θ max) in the combinations — the columns' moments
        larger than the same analysis without it (whose θ the same)."""
        from arqbim.core import actions as act
        from arqbim.model import design_text as dt
        from arqbim.model import structure_analysis as sa
        model, loads, settings = self._model()
        result = sa.analyse(model, loads, settings)
        self.assertEqual(sorted(s.case for s in result.sways), ["EX", "EY", "WX", "WY"])
        st = loads.storeys[0]
        for s in result.sways:
            self.assertAlmostEqual(s.height, 3.0)
            self.assertAlmostEqual(s.theta, s.p * s.drift / (s.v * s.height))
        ex = next(s for s in result.sways if s.case == "EX")
        wx = next(s for s in result.sways if s.case == "WX")
        self.assertAlmostEqual(ex.p, st.weight)
        self.assertAlmostEqual(wx.p, 1.35 * st.g + 1.5 * st.q)
        self.assertAlmostEqual(ex.v, max(st.quake_1, st.quake_2))
        self.assertAlmostEqual(wx.v, st.wind_x)
        ratio = (ex.p * act.BEHAVIOUR_Q / sa.CRACKED_SEISMIC) / (wx.p / sa.CRACKED_WIND)
        self.assertAlmostEqual(ex.theta / wx.theta, ratio, places=4)
        self.assertLess(result.theta()[0], sa.THETA_IGNORED)
        self.assertEqual(result.amplification, {})
        self.assertIn("desprezável", dt.second_order_text(result))
        # three storeys, slender
        model, loads, settings = self._tower(3, 0.2)
        self.assertEqual(len(model.supports), 4)
        result = sa.analyse(model, loads, settings)
        plain = sa.analyse(model, loads, settings, second_order=False)
        ex = [s for s in result.sways if s.case == "EX"]
        self.assertEqual([s.level for s in ex], [3.0, 6.0, 9.0])
        self.assertAlmostEqual(ex[0].v, sum(max(s.quake_1, s.quake_2) for s in loads.storeys))
        self.assertAlmostEqual(ex[0].p, sum(s.weight for s in loads.storeys))
        self.assertEqual([s.theta for s in ex], sorted((s.theta for s in ex), reverse=True))
        theta, worst = result.theta("EX")
        self.assertIs(worst, ex[0])
        self.assertGreater(theta, sa.THETA_IGNORED)
        self.assertAlmostEqual(result.amplification["EX"], 1 / (1 - theta))
        self.assertEqual(plain.amplification, {})
        self.assertAlmostEqual(plain.theta("EX")[0], theta)
        bottom = {m.id: m.m_column for m in plain.members if m.id.startswith("c0_")}
        for m in result.members:
            if m.id in bottom:
                self.assertGreater(m.m_column, bottom[m.id] * 1.05)
        self.assertEqual(sa.sway_verdict(0.1), "ignored")
        self.assertEqual(sa.sway_verdict(0.15), "amplified")
        self.assertEqual(sa.sway_verdict(0.25), "rigorous")
        self.assertEqual(sa.sway_verdict(0.31), "flexible")
        text = dt.second_order_text(result)
        self.assertIn("sismo X × ", text)
        self.assertEqual(len(dt.sway_rows(result)), 12)

    def test_tributary(self):
        from arqbim.model import structure_analysis as sa
        model, _loads, _s = self._model()
        share = sa.tributary(model.panels[0], [m for m in model.members if m.kind == "beam"], model.nodes)
        self.assertAlmostEqual(sum(share.values()), 24.0, places=6)
        middle = sum(v for k, v in share.items() if k.startswith("bx"))
        self.assertGreater(middle, max(v for k, v in share.items() if not k.startswith("bx")))


class WindTerrainNA(unittest.TestCase):
    """0.219: the terrain categories of the Portuguese National Annex — four (I to IV, no 0): z0 0,005 / 0,05 / 0,3 /
    1,0 m, zmin 1 / 3 / 8 / 15 m; the turbulence at 10 m (c0 = 1) as the NA's tables have it (0,13 / 0,19 / 0,29 /
    0,37); under zmin the pressure at zmin (IV: 5 m as 15 m); a project's old category 0 read as I."""

    def test_categories(self):
        from arqbim.core import actions as act
        self.assertEqual(list(act.TERRAIN), ["I", "II", "III", "IV"])
        self.assertEqual(act.TERRAIN["I"], (0.005, 1.0))
        self.assertEqual(act.TERRAIN["IV"], (1.0, 15.0))
        for cat, iv in (("I", 0.13), ("II", 0.19), ("III", 0.29), ("IV", 0.37)):
            z0, zmin = act.TERRAIN[cat]
            self.assertAlmostEqual(1.0 / math.log(max(10.0, zmin) / z0), iv, delta=0.005)
        self.assertAlmostEqual(act.peak_pressure(5.0, "A", "IV"), act.peak_pressure(15.0, "A", "IV"))
        self.assertAlmostEqual(act.peak_pressure(10.0, "A", "0"), act.peak_pressure(10.0, "A", "I"))


class SnowLoads(unittest.TestCase):
    """0.217: the snow (NP EN 1991-1-3, NA) — on the ground sk = Cz [1 + (H/500)²]: Z1 at sea level 0,30, at 1000 m
    1,50 kN/m²; Z3 (the islands) 0,10; on a roof μ1 0,8 to 30°, 0,4 at 45°, none from 60°; a roof loaded with the
    greater of its use's imposed load and the snow, with the governing one's ψ (over 1000 m, the higher ones)."""

    def test_snow(self):
        from arqbim.core import actions as act
        self.assertAlmostEqual(act.snow_ground("Z1", 0.0), 0.30)
        self.assertAlmostEqual(act.snow_ground("Z1", 1000.0), 1.50)
        self.assertAlmostEqual(act.snow_ground("Z3", 0.0), 0.10)
        self.assertAlmostEqual(act.snow_shape(20.0), 0.8)
        self.assertAlmostEqual(act.snow_shape(45.0), 0.4)
        self.assertAlmostEqual(act.snow_shape(70.0), 0.0)
        low = act.Settings()                                          # (at sea level: the roof's use governs)
        self.assertAlmostEqual(low.snow(), 0.24)
        self.assertAlmostEqual(low.imposed(roof=True), act.USES["H"][0])
        self.assertEqual(low.psi(roof=True), act.USES["H"][1:])
        high = act.Settings(altitude=1000.0)
        self.assertAlmostEqual(high.imposed(roof=True), 1.2)
        self.assertEqual(high.psi(roof=True), act.SNOW_PSI)
        self.assertEqual(act.Settings(altitude=1200.0).psi(roof=True), act.SNOW_PSI_HIGH)
        self.assertAlmostEqual(high.imposed(), act.USES["A"][0])      # (the floors: as before)


class StructuralActions(unittest.TestCase):
    """0.164: the wind's peak pressure (zone A, terrain II, 10 m: about 1,07 kPa — 2,35 times the basic 0,456 kPa);
    the seismic action of a three-storey frame in zone 1.4 on ground B (ag 1,0: S 1,35; T1 0,39 s on the plateau:
    Sd 1,69 m/s²; Fb 439 kN for 3000 kN, spread 1:2:3); S falling with ag (zone 1.1: 1,175); the combinations."""

    def test_wind(self):
        from arqbim.core import actions
        self.assertAlmostEqual(actions.peak_pressure(10.0, "A", "II"), 1.072, delta=0.005)
        self.assertGreater(actions.peak_pressure(20.0, "A", "II"), actions.peak_pressure(10.0, "A", "II"))
        self.assertGreater(actions.peak_pressure(10.0, "B", "II"), actions.peak_pressure(10.0, "A", "II"))
        self.assertLess(actions.peak_pressure(10.0, "A", "IV"), actions.peak_pressure(10.0, "A", "II"))
        forces = actions.wind_storey_forces([3.0, 6.0], [10.0, 10.0], "A", "II")
        self.assertEqual(len(forces), 2)
        self.assertGreater(forces[0], forces[1])                    # (the roof: half a storey's strip)

    def test_seismic(self):
        from arqbim.core import actions
        s = actions.Settings(seismic_zone_1="1.4", ground="B")
        fb, fi, t1, sd = actions.seismic_storey_forces([3.0, 6.0, 9.0], [1000.0] * 3, s)
        self.assertAlmostEqual(t1, 0.390, delta=0.001)
        self.assertAlmostEqual(sd, 1.6875, places=4)
        self.assertAlmostEqual(fb, 1.6875 * 3000 / 9.81 * 0.85, places=3)
        np.testing.assert_allclose(np.array(fi) / fb, (1 / 6, 2 / 6, 3 / 6))
        self.assertAlmostEqual(actions.ground_s(2.5, "B"), 1.175, places=6)
        self.assertAlmostEqual(actions.ground_s(0.5, "C"), 1.6, places=6)
        combos = actions.combinations(s)
        self.assertEqual(len(combos), 8)
        self.assertEqual(combos[0][1], {"G": 1.35, "Q": 1.5})
        self.assertEqual(combos[-1][1], {"G": 1.0, "Q": 0.3})

    def test_materials(self):
        from arqbim.core import actions
        s = actions.Settings()
        self.assertAlmostEqual(s.fcd(), 25 / 1.5 * 1000)
        self.assertAlmostEqual(s.fyd(), 500 / 1.15 * 1000)
        self.assertAlmostEqual(s.ecm() / 1e6, 31.476, places=2)        # (C25/30: 31 GPa)
        self.assertEqual((s.imposed(), s.imposed(roof=True)), (2.0, 0.4))


class AnalyticalModel(unittest.TestCase):
    """0.163: a 6 × 4 m frame — four columns 3 m high on footings, four beams on top, one across the middle resting
    on two of them, a slab: ten nodes, eleven members (the two beams it rests on split there), four fixed supports,
    no problems. Without footings, told (and still held); a column standing on nothing above the ground, an error;
    a beam resting on nothing, an error."""

    def _frame(self, footings=True):
        from arqbim.core import structural as st
        corners = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        cols = [st.Column("c{}".format(k), p, 0.0, 3.0, (0.3, 0.3)) for k, p in enumerate(corners)]
        beams = [st.Beam("b{}".format(k), corners[k], corners[(k + 1) % 4], 3.0, (0.25, 0.5)) for k in range(4)]
        beams.append(st.Beam("bx", (3.0, 0.0), (3.0, 4.0), 3.0, (0.2, 0.4)))
        foots = [st.Footing("f{}".format(k), p, 0.0, (1.2, 1.2)) for k, p in enumerate(corners)] if footings else []
        panel = st.Panel("s", [(0, 0), (6, 0), (6, 4), (0, 4)], 3.0, 0.2)
        return st, cols, beams, foots, panel

    def test_frame(self):
        st, cols, beams, foots, panel = self._frame()
        model = st.build(cols, beams, foots, [panel], levels=[0.0, 3.0])
        self.assertEqual(len(model.nodes), 10)
        self.assertEqual(sum(1 for m in model.members if m.kind == "column"), 4)
        self.assertEqual(sum(1 for m in model.members if m.kind == "beam"), 7)
        self.assertEqual(sorted(model.supports.values()), ["fixed"] * 4)
        self.assertEqual(model.issues, [])
        bottom = [m for m in model.members if m.guid == "b0"]
        self.assertEqual(sorted(round(model.length(m), 6) for m in bottom), [3.0, 3.0])     # (split at the middle)

    def test_problems(self):
        st, cols, beams, _foots, panel = self._frame(footings=False)
        cols.append(st.Column("alta", (10.0, 0.0), 3.0, 6.0, (0.3, 0.3)))
        beams.append(st.Beam("solta", (20.0, 0.0), (24.0, 0.0), 3.0, (0.25, 0.5)))
        model = st.build(cols, beams, (), [panel], levels=[0.0, 3.0])
        codes = sorted((i.code, i.severity) for i in model.issues)
        self.assertEqual(codes.count(("no_footing", st.WARNING)), 4)
        self.assertIn(("column_hanging", st.ERROR), codes)
        self.assertIn(("beam_loose", st.ERROR), codes)
        self.assertEqual(len(model.supports), 4)
        self.assertEqual(st.counts(model.issues)[st.ERROR], 2)

    def test_walls(self):
        """0.335: a two-storey house of load-bearing walls — four on strip footings, four on them upstairs, a slab on
        each floor —: the walls in the model, each on what holds it (its footing, the wall under it), the slabs held
        by them, no problems; a beam across from wall to wall held at both ends (pinned on them), a column standing
        on a wall held. A wall up there with nothing under it, an error; one on the slab only, a warning; one at the
        foundations without a footing, a warning; one with no length, an error."""
        from arqbim.core import structural as st
        c = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        ground = [st.Wall("g{}".format(k), c[k], c[(k + 1) % 4], 0.0, 2.85, 0.25, 0.20) for k in range(4)]
        upper = [st.Wall("u{}".format(k), c[k], c[(k + 1) % 4], 3.0, 5.85, 0.25, 0.20) for k in range(4)]
        strips = [st.Footing("f{}".format(k), ((c[k][0] + c[(k + 1) % 4][0]) / 2, (c[k][1] + c[(k + 1) % 4][1]) / 2),
                             0.0, (6.0 if k % 2 == 0 else 4.0, 0.5), kind="strip",
                             x_dir=(1.0, 0.0) if k % 2 == 0 else (0.0, 1.0), wall="g{}".format(k)) for k in range(4)]
        slabs = [st.Panel("s1", list(c), 3.0, 0.15), st.Panel("s2", list(c), 6.0, 0.15)]
        beam = st.Beam("b", (3.0, 0.0), (3.0, 4.0), 3.0, (0.2, 0.4))
        column = st.Column("p", (1.5, 4.0), 3.0, 5.85, (0.2, 0.2))
        model = st.build([column], [beam], strips, slabs, [0.0, 3.0, 6.0], ground + upper)
        self.assertEqual(model.issues, [])
        self.assertEqual(len(model.walls), 8)
        self.assertEqual(model.wall_bases["g0"], ("footing", "f0"))
        self.assertEqual(model.wall_bases["u2"], ("wall", ["g2"]))
        self.assertEqual(sorted(model.supports.values()), ["wall"] * 3)
        self.assertEqual(sorted(model.on_walls.values()), ["g0", "g2", "g2"])
        more = [st.Wall("h", (10.0, 0.0), (14.0, 0.0), 3.0, 5.85, 0.25),
                st.Wall("on_slab", (1.0, 2.0), (5.0, 2.0), 3.0, 5.85, 0.25),
                st.Wall("loose", (0.0, 8.0), (4.0, 8.0), 0.0, 2.85, 0.25),
                st.Wall("none", (1.0, 1.0), (1.0, 1.0), 0.0, 2.85, 0.25)]
        model = st.build([], [], strips, slabs, [0.0, 3.0, 6.0], ground + upper + more)
        found = {(i.code, i.severity, i.guids[0]) for i in model.issues}
        self.assertEqual(found, {("wall_hanging", st.ERROR, "h"), ("wall_on_slab", st.WARNING, "on_slab"),
                                 ("wall_no_footing", st.WARNING, "loose"), ("wall_no_size", st.ERROR, "none")})
        self.assertEqual(model.wall_bases["on_slab"], ("slab", "s1"))


class WallLoads(unittest.TestCase):
    """0.336 — the load-bearing walls' loads: a two-storey house of walls (6 × 4 m, a slab on each floor, strip
    footings): all the slabs' loads go down the walls (none lost), each upper wall's to the one under it, their own
    weight added; the slabs on one side of the perimeter walls, their span 4 m; each storey's wind along X shared
    alike by the two walls along X, none for those across. With a beam from wall to wall under the first floor: its
    share of the slab and its own weight come to the walls as its reactions — none lost —; it is analysed."""

    def _house(self, beam=False):
        from arqbim.core import actions, structural as st
        from arqbim.model import structure_loads
        c = ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0))
        ground = [st.Wall("g{}".format(k), c[k], c[(k + 1) % 4], 0.0, 2.85, 0.25, 0.20) for k in range(4)]
        upper = [st.Wall("u{}".format(k), c[k], c[(k + 1) % 4], 3.0, 5.85, 0.25, 0.20) for k in range(4)]
        strips = [st.Footing("f{}".format(k), ((c[k][0] + c[(k + 1) % 4][0]) / 2, (c[k][1] + c[(k + 1) % 4][1]) / 2),
                             0.0, (6.0 if k % 2 == 0 else 4.0, 0.5), kind="strip",
                             x_dir=(1.0, 0.0) if k % 2 == 0 else (0.0, 1.0), wall="g{}".format(k)) for k in range(4)]
        slabs = [st.Panel("s1", list(c), 3.0, 0.15), st.Panel("s2", list(c), 6.0, 0.15)]
        beams = [st.Beam("b", (3.0, 0.0), (3.0, 4.0), 3.0, (0.2, 0.4))] if beam else []
        model = st.build([], beams, strips, slabs, [0.0, 3.0, 6.0], ground + upper)
        settings = actions.Settings(use="A", roof_use="A")
        return model, structure_loads.building_actions(model, settings, (), 0.0), settings

    def test_walls_only(self):
        from arqbim.model import structure_analysis as sa
        model, loads, settings = self._house()
        result = sa.analyse(model, loads, settings)
        self.assertEqual(result.error, "")
        by = {w.guid: w for w in result.walls}
        self.assertEqual(len(by), 8)
        slabs = sum(loads.panel_g[p.guid] * 24.0 for p in model.panels)
        self.assertAlmostEqual(sum(w.slab_g for w in result.walls), slabs, delta=slabs * 1e-6)
        down = sum(by["g{}".format(k)].base_g for k in range(4))
        self.assertAlmostEqual(down, slabs + sum(w.self_g for w in result.walls), delta=down * 1e-6)
        self.assertTrue(all(abs(w.one_side - 1.0) < 1e-9 for w in result.walls))
        self.assertAlmostEqual(by["g0"].span, 4.0)
        wind = sum(s.wind_x for s in loads.storeys)
        self.assertAlmostEqual(by["g0"].shear["WX"], by["g2"].shear["WX"])
        self.assertAlmostEqual(by["g0"].shear["WX"] + by["g2"].shear["WX"], wind, delta=wind * 1e-9)
        self.assertNotIn("WX", by["g1"].shear)
        self.assertAlmostEqual(by["u0"].shear["WX"] * 2, loads.storeys[-1].wind_x, delta=1e-9)

    def test_beam_on_walls(self):
        from arqbim.model import structure_analysis as sa
        model, loads, settings = self._house(beam=True)
        result = sa.analyse(model, loads, settings)
        self.assertEqual(result.error, "")
        self.assertEqual([m.id for m in result.members], ["b"])
        by = {w.guid: w for w in result.walls}
        first = sum(by["g{}".format(k)].top_g - by["u{}".format(k)].base_g for k in range(4))
        expected = loads.panel_g["s1"] * 24.0 + loads.member_g["b"] * 4.0
        self.assertAlmostEqual(first, expected, delta=expected * 1e-6)
        self.assertGreater(by["g0"].top_g - by["u0"].base_g - by["g0"].slab_g, 1.0)   # (the beam's reaction)
        self.assertAlmostEqual(result.reactions_up, result.loads_in, delta=result.loads_in * 1e-6)


class MasonryEC6(unittest.TestCase):
    """0.337 — the load-bearing walls by Eurocode 6: clay units of group 2, fb 10 N/mm², mortar M5: fk = 0,45 ×
    10^0,7 × 5^0,3 = 3,65 N/mm², fd = fk / 2,5, fvk0 0,20; a 20 cm wall 2,70 m high, 4 m long, 50 kN/m at its top (a
    floor on one side): slenderness 10,1, at its top Φ = 1 − 2e/t with e = M/N + hef/450, NRd = Φ t fd; its shear
    resisted by fvk = 0,20 + 0,4 σd — OK; ten times the load: it fails; 7 cm thick: too slender. The house of walls
    of 0.336 verified: its eight walls OK, their notes in words, ordered after the footings."""

    def test_strength(self):
        from arqbim.core import actions, ec6
        fk, fd, fvk0, fb = ec6.strength(actions.Settings())
        self.assertAlmostEqual(fk, 0.45 * 10 ** 0.7 * 5 ** 0.3, places=9)
        self.assertAlmostEqual(fk, 3.655, places=2)
        self.assertAlmostEqual(fd, fk / 2.5, places=9)
        self.assertEqual((fvk0, fb), (0.20, 10.0))
        stronger = ec6.strength(actions.Settings(masonry_unit="concrete", masonry_group="1", masonry_mortar="M10"))
        self.assertAlmostEqual(stronger[0], 0.55 * 10 ** 0.7 * 10 ** 0.3, places=9)
        self.assertEqual(stronger[2], 0.20)

    def test_wall(self):
        from arqbim.core import actions, ec2, ec6
        s = actions.Settings()
        d = ec6.wall(0.20, 2.70, 4.0, 50.0, 55.0, 60.0, 50.0, 1.0, 20.0, 40.0, s)
        self.assertEqual(d.status, ec2.OK)
        self.assertEqual([n.code for n in d.notes], ["ec6_material", "ec6_slender"] + ["ec6_compression"] * 3
                         + ["ec6_shear"])
        slender = d.notes[1].values["slender"]
        self.assertAlmostEqual(slender, 0.75 * 2.70 / 0.20)
        top = d.notes[2].values
        e = 50.0 * 0.20 / 6.0 / 50.0 + 0.75 * 2.70 / 450.0
        self.assertEqual(top["spot"], "top")
        self.assertAlmostEqual(top["ecc"], e)
        self.assertAlmostEqual(top["nrd"], (1 - 2 * e / 0.20) * 0.20 * ec6.strength(s)[1] * 1000.0)
        self.assertEqual([n.values["spot"] for n in d.notes[2:5]], ["top", "mid", "base"])
        shear = d.notes[5].values
        self.assertAlmostEqual(shear["vrd"], (0.20 + 0.4 * 0.2) / 2.5 * 1000.0 * 0.20 * 4.0)
        self.assertLess(d.ratio, 0.9)
        heavy = ec6.wall(0.20, 2.70, 4.0, 500.0, 550.0, 600.0, 500.0, 1.0, 0.0, 400.0, s)
        self.assertEqual(heavy.status, ec2.FAIL)
        self.assertEqual(heavy.notes[-1].code, "ec6_no_shear")
        self.assertEqual((top["sign"], heavy.notes[2].values["sign"]), ("≤", ">"))     # (what it says: it fails)
        thin = ec6.wall(0.07, 2.70, 4.0, 10.0, 11.0, 12.0, 10.0, 0.0, 0.0, 8.0, s)
        self.assertEqual(thin.status, ec2.FAIL)
        self.assertEqual(thin.notes[1].status, ec2.FAIL)

    def test_house(self):
        from arqbim.core import ec2
        from arqbim.model import design_text, structure_analysis as sa, structure_design as sd
        model, loads, settings = WallLoads()._house()
        result = sa.analyse(model, loads, settings)
        designs = sd.design_structure(model, result, loads, settings, [], [])
        walls = [e for e in designs if e.kind == "wall"]
        self.assertEqual(sorted(e.guid for e in walls), sorted(["g{}".format(k) for k in range(4)]
                                                              + ["u{}".format(k) for k in range(4)]))
        self.assertTrue(all(e.design.status == ec2.OK for e in walls), [(e.guid, e.design.ratio) for e in walls])
        by = {e.guid: e for e in walls}
        self.assertGreater(by["g0"].design.ratio, by["u0"].design.ratio)   # (the ground floor's carry more)
        for e in walls:
            self.assertTrue(all(design_text.note_text(n) for n in e.design.notes))
        governs = design_text.main_note(by["g0"].design)                 # (its most used check)
        self.assertIn(governs.code, ("ec6_compression", "ec6_shear"))
        v = governs.values
        self.assertAlmostEqual(v.get("n", v.get("v")) / v.get("nrd", v.get("vrd")), by["g0"].design.ratio)
        self.assertEqual(design_text.bars_text("wall", by["g0"].design), "—")
        self.assertEqual(designs[-1].kind, "wall")


class FacadeWallsEC6(unittest.TestCase):
    """0.345 — a façade wall's bending out of its plane by the wind (EC6 6.3, annex E): fxk1 / fxk2 of table 3.4 by
    the units and the mortar; the panel's moment by the yield lines — a square held on four edges qL²/24, one spanning
    from base to top qH²/8 (M1), one standing free qH²/2, a long one held at its base and sides tending to qH²/2 and a
    tall one to qL²/8, more edges held never more —; a 15 cm wall spanning 2,70 m under 1,65 kN/m² fails by bending,
    the arch held at its top takes it; one free at its top cannot arch; the corner zones e/5 from a façade's ends."""

    def test_flexural(self):
        from arqbim.core import actions, ec6
        self.assertEqual(ec6.flexural(actions.Settings()), (0.10, 0.40))
        self.assertEqual(ec6.flexural(actions.Settings(masonry_mortar="M2.5")), (0.10, 0.20))
        self.assertEqual(ec6.flexural(actions.Settings(masonry_unit="concrete", masonry_mortar="M2.5")), (0.05, 0.20))
        self.assertEqual([ec6.edges_key(*e) for e in ((True, True, True), (True, False, True), (True, False, False),
                                                       (False, True, True), (False, True, False), (False, False, False))],
                         ["all", "top_side", "top", "sides", "side", "base"])

    def test_panel_moment(self):
        from arqbim.core import ec6
        self.assertAlmostEqual(ec6.panel_moment(3.0, 3.0, 1.0, "all"), 9.0 / 24.0)
        self.assertAlmostEqual(ec6.panel_moment(4.0, 2.7, 0.25, "top"), 2.7 ** 2 / 8.0 / 0.25)
        self.assertAlmostEqual(ec6.panel_moment(4.0, 2.7, 0.25, "base"), 2.7 ** 2 / 2.0 / 0.25)
        self.assertAlmostEqual(ec6.panel_moment(3.0, 300.0, 1.0, "sides"), 9.0 / 8.0, delta=9.0 / 8.0 * 0.02)
        self.assertAlmostEqual(ec6.panel_moment(300.0, 2.0, 1.0, "sides"), 4.0 / 2.0, delta=0.04)
        m = {e: ec6.panel_moment(5.0, 2.7, 0.5, e) for e in ("all", "top_side", "top", "sides", "side", "base")}
        for less, more in (("all", "top_side"), ("top_side", "top"), ("all", "sides"), ("sides", "side"),
                           ("side", "base"), ("top_side", "side")):
            self.assertLessEqual(m[less], m[more] + 1e-9, (less, more, m))
        # Johansen's square, orthotropic: the height over √μ
        h = 2.7 / math.sqrt(0.5)
        s, l = min(5.0, h), max(5.0, h)
        self.assertAlmostEqual(m["all"], s * s / 24.0 * (math.sqrt(3 + (s / l) ** 2) - s / l) ** 2)

    def test_lateral(self):
        from arqbim.core import actions, ec2, ec6
        s = actions.Settings()
        d = ec6.lateral(0.15, 4.0, 2.7, 0.8, 1.1, 6.0, 1.25, 0.02, "top", s)
        self.assertEqual([n.code for n in d.notes], ["ec6_flexural", "ec6_wind", "ec6_lateral_over", "ec6_arch"])
        flex, wind, bend, arch = (n.values for n in d.notes)
        self.assertAlmostEqual(flex["fd1"], 0.10 / 2.5 + 0.02)
        self.assertAlmostEqual(wind["w"], 1.5 * 0.8 * 1.1 * 1.25)
        self.assertAlmostEqual(bend["me1"], 1.65 * 2.7 ** 2 / 8.0)
        self.assertAlmostEqual(bend["mr1"], 0.06 * 1000.0 * 0.15 ** 2 / 6.0)
        self.assertEqual(bend["sign"], ">")                                    # (bending alone: not enough…)
        q = ec6.strength(s)[1] * 1000.0 * (0.15 / 2.7) ** 2
        self.assertAlmostEqual(arch["q"], q)                                   # (…the arch held at its top)
        self.assertEqual(d.status, ec2.OK)
        self.assertAlmostEqual(d.ratio, 1.65 / q)
        free = ec6.lateral(0.15, 4.0, 2.7, 0.8, 1.1, 6.0, 1.25, 0.02, "sides", s)     # (its top free: no arch)
        self.assertEqual(free.notes[-1].code, "ec6_lateral")
        self.assertEqual(free.status, ec2.FAIL)
        bearing = ec6.wall(0.20, 2.70, 4.0, 50.0, 55.0, 60.0, 50.0, 1.0, 20.0, 40.0, s)     # (added to its own)
        before = len(bearing.notes)
        ec6.lateral(0.20, 4.0, 2.7, 0.5, 1.1, 3.0, 1.0, 0.05, "all", s, design=bearing)
        self.assertEqual([n.code for n in bearing.notes[before:]], ["ec6_flexural", "ec6_wind_solid", "ec6_lateral"])
        self.assertEqual(bearing.status, ec2.OK)
        from arqbim.model import design_text
        self.assertTrue(all(design_text.note_text(n) for n in d.notes + free.notes))
        self.assertIn(design_text.main_note(d).code, ("ec6_arch", "ec6_lateral"))

    def test_masonry_of_a_type(self):
        """0.346: a wall type's own masonry kept as text and read back; not understood: none (the project's); the
        project's settings with it — γM the project's."""
        from arqbim.core import actions, ec6
        own = ("aac", "1", 4.0, "M2.5")
        self.assertEqual(ec6.decode(ec6.encode(own)), own)
        self.assertEqual(ec6.encode(None), "")
        for bad in ("", None, "unit=wood;group=1;fb=4;mortar=M5", "unit=clay;group=9;fb=4;mortar=M5",
                    "unit=clay;group=1;fb=x;mortar=M5", "unit=clay;group=1;fb=4"):
            self.assertIsNone(ec6.decode(bad), bad)
        s = actions.Settings(masonry_gamma=2.2)
        mine = ec6.with_masonry(s, own)
        self.assertEqual((mine.masonry_unit, mine.masonry_group, mine.masonry_fb, mine.masonry_mortar,
                          mine.masonry_gamma), ("aac", "1", 4.0, "M2.5", 2.2))
        self.assertIs(ec6.with_masonry(s, None), s)
        self.assertNotAlmostEqual(ec6.strength(mine)[0], ec6.strength(s)[0])

    def test_corner_zone(self):
        from arqbim.model import wall_lateral
        extent, height = ((0.0, 0.0), (20.0, 10.0)), 6.0               # (e = min(10, 12) = 10: 2 m from each end)
        self.assertTrue(wall_lateral.corner_zone({"start": (0.0, 0.0), "end": (3.0, 0.0)}, extent, height))
        self.assertFalse(wall_lateral.corner_zone({"start": (8.0, 0.0), "end": (12.0, 0.0)}, extent, height))
        self.assertTrue(wall_lateral.corner_zone({"start": (19.0, 10.0), "end": (15.0, 10.0)}, extent, height))
        self.assertFalse(wall_lateral.corner_zone({"start": (20.0, 3.0), "end": (20.0, 7.0)}, extent, height))


class ConcreteWallEC2(unittest.TestCase):
    """0.342 — a load-bearing concrete wall by Eurocode 2, on each metre: 20 cm, 2,70 m, C25/30, A500, 300 kN/m at its
    top (a floor on one side), 40 kN of in-plane shear on 4 m: its vertical bars the least (0,002 Ac = 4 cm²/m on the
    two faces), spaced ≤ 40 cm; its horizontal a quarter of them and 0,001 Ac; the shear taken by the concrete; OK. A
    15 cm wall 3,5 m high under 500 kN/m: slender — its second order in its mid-height's moment. 2000 kN/m on 15 cm:
    fails. 900 kN of
    shear on 2 m: the horizontal bars take it. The house of 0.336 with concrete walls: designed by EC2, their bars
    said."""

    def test_wall(self):
        from arqbim.core import ec2
        d = ec2.wall(0.20, 2.70, 4.0, 300.0, 310.0, 320.0, 200.0, 1.0, 40.0, 200.0, 25, 500)
        self.assertEqual(d.status, ec2.OK)
        dv, sv = d.vertical
        self.assertGreaterEqual(2 * ec2.bar_area(dv) / sv, 0.002 * 0.20 - 1e-12)
        self.assertLessEqual(sv, 0.40)
        dh, sh = d.horizontal
        self.assertGreaterEqual(2 * ec2.bar_area(dh) / sh, max(0.25 * 2 * ec2.bar_area(dv) / sv, 0.001 * 0.20) - 1e-12)
        codes = [n.code for n in d.notes]
        self.assertEqual(codes, ["wall_slender"] + ["wall_compression"] * 3 + ["wall_vertical", "wall_shear",
                                                                               "wall_horizontal"])
        self.assertLess(d.ratio, 1.0)
        slender = ec2.wall(0.15, 3.5, 4.0, 500.0, 510.0, 520.0, 200.0, 1.0, 0.0, 400.0, 25, 500)
        self.assertGreater(slender.notes[0].values["m2"], 0.0)
        self.assertEqual(slender.notes[-1].code, "wall_horizontal")
        self.assertIn("wall_no_shear", [n.code for n in slender.notes])
        mid = next(n for n in slender.notes if n.code == "wall_compression" and n.values["spot"] == "mid")
        self.assertGreaterEqual(mid.values["m"], slender.notes[0].values["m2"])      # (its second order in it)
        crushed = ec2.wall(0.15, 3.0, 4.0, 2000.0, 2010.0, 2020.0, 0.0, 0.0, 0.0, 1500.0, 25, 500)
        self.assertEqual(crushed.status, ec2.FAIL)
        self.assertEqual(crushed.notes[-1].code, "wall_fail")
        sheared = ec2.wall(0.20, 2.70, 2.0, 300.0, 310.0, 320.0, 0.0, 0.0, 900.0, 200.0, 25, 500)
        bars = next(n for n in sheared.notes if n.code == "wall_shear_bars")
        dh2, sh2 = sheared.horizontal
        self.assertGreaterEqual(2 * ec2.bar_area(dh2) / sh2, bars.values["need"] - 1e-12)
        self.assertLess(bars.values["vrd"], 900.0)

    def test_house(self):
        from arqbim.core import ec2
        from arqbim.model import design_text, structure_analysis as sa, structure_design as sd
        model, loads, settings = WallLoads()._house()
        for w in model.walls:
            w.material = "concrete"
        result = sa.analyse(model, loads, settings)
        designs = sd.design_structure(model, result, loads, settings, [], [])
        walls = [e for e in designs if e.kind == "wall"]
        self.assertEqual(len(walls), 8)
        self.assertTrue(all(e.design.status == ec2.OK and e.design.vertical for e in walls))
        self.assertFalse(any(design_text.masonry(e) for e in walls))
        self.assertTrue(design_text.bars_text("wall", walls[0].design).startswith("vert. Ø"))
        for e in walls:
            self.assertTrue(all(design_text.note_text(n) for n in e.design.notes))
        stored = walls[0].stored(settings)
        self.assertEqual((stored["kind"], len(stored["vertical"]), len(stored["horizontal"])), ("wall", 2, 2))


class ScanOpenings(unittest.TestCase):
    """0.213: a 20 cm wall 6 m long scanned from both sides, with a door's gap (2,0 to 2,9 m, up to 2,10 m) and a
    window's (4,0 to 5,2 m, from 1,00 to 2,20 m): a door 90 cm × 2,10 and a window 1,20 × 1,20 on a 1,00 m sill
    found; a gap at the wall's end and a narrow one: none."""

    @staticmethod
    def wall_scan():
        pts = []
        for x in np.arange(0.0, 6.0001, 0.02):
            for z in np.arange(0.0, 2.8001, 0.04):
                if 2.0 < x < 2.9 and z < 2.1:
                    continue                                 # (the door)
                if 4.0 < x < 5.2 and 1.0 < z < 2.2:
                    continue                                 # (the window)
                if 5.85 < x and 1.0 < z < 1.6:
                    continue                                 # (an end left open: a corner, not an opening)
                if 0.8 < x < 1.0 and 1.0 < z < 1.6:
                    continue                                 # (a narrow hole: not an opening)
                pts += [(x, -0.1, z), (x, 0.1, z)]
        return np.array(pts)

    def test_door_and_window(self):
        from arqbim.core import scan_walls
        found = scan_walls.openings(self.wall_scan(), [((0.0, 0.0), (6.0, 0.0), 0.2)], 0.0, 2.8)
        self.assertEqual([k for _i, k in found], ["door", "window"])
        door, window = found[0][0], found[1][0]
        np.testing.assert_allclose(door.points[:, 0], (2.0, 2.9), atol=0.051)
        self.assertAlmostEqual(door.height, 2.1, delta=0.051)
        self.assertIsNone(door.sill)
        np.testing.assert_allclose(window.points[:, 0], (4.0, 5.2), atol=0.051)
        self.assertAlmostEqual(window.sill, 1.0, delta=0.051)
        self.assertAlmostEqual(window.height, 1.2, delta=0.101)


class ScanCurvedWalls(unittest.TestCase):
    """0.215: a scan's slice with a curved wall (its two faces, 3,0 and 3,2 m round (0; 0), a quarter) and a straight
    wall (two lines 20 cm apart): the two arcs found and taken away before the lines; the straight wall from the
    lines; the curved wall 3,1 m round, 20 cm; a curved façade seen from inside only (one arc, the room within it): a
    30 cm wall outwards; the straight walls of a plain room: no arcs."""

    def test_curved(self):
        from arqbim.core import scan_walls
        pts = []
        for r in (3.0, 3.2):
            for a in np.arange(0.0, np.pi / 2 + 1e-9, 0.01 / r):
                pts.append((r * np.cos(a), r * np.sin(a)))
        for x in np.arange(-6.0, -1.0, 0.01):
            pts += [(x, -1.0), (x, -1.2)]
        xy = np.array(pts)
        found = scan_walls.arcs(xy)
        radii = sorted(r for _c, r, _a, _b in found)
        self.assertEqual(len(radii), 2)
        np.testing.assert_allclose(radii, (3.0, 3.2), atol=0.02)
        rest = scan_walls.off_arcs(xy, found)
        self.assertLess(len(rest), len(xy) * 0.6)
        walls = scan_walls.wall_axes(scan_walls.lines(rest), rest)
        self.assertEqual([round(t, 2) for _a, _b, t in walls], [0.2])
        (centre, radius, start, sweep, t), = scan_walls.arc_axes(found, xy)
        np.testing.assert_allclose(centre, (0, 0), atol=0.02)
        self.assertAlmostEqual(radius, 3.1, delta=0.02)
        self.assertAlmostEqual(sweep, np.pi / 2, delta=0.03)
        self.assertAlmostEqual(t, 0.2, delta=0.02)

    def test_facade_and_plain_room(self):
        from arqbim.core import scan_walls
        arc = [(4.0 * np.cos(a), 4.0 * np.sin(a)) for a in np.arange(0.0, np.pi, 0.0025)]
        inside = [(x, y) for x in np.arange(-2.0, 2.0, 0.5) for y in np.arange(0.5, 2.0, 0.5)]
        xy = np.array(arc + inside)
        found = scan_walls.arcs(xy)
        self.assertEqual(len(found), 1)
        (_c, radius, _s, _w, t), = scan_walls.arc_axes(found, xy)
        self.assertAlmostEqual(t, scan_walls.OUTER_T)
        self.assertAlmostEqual(radius, 4.0 + scan_walls.OUTER_T / 2, delta=0.01)      # (outwards)
        room = []
        for x in np.arange(0.0, 6.0, 0.01):
            room += [(x, 0.0), (x, 4.0)]
        for y in np.arange(0.0, 4.0, 0.01):
            room += [(0.0, y), (6.0, y)]
        self.assertEqual(scan_walls.arcs(np.array(room)), [])


class ScanStoreys(unittest.TestCase):
    """0.214: the storeys of a scan's heights — one room (0 and 2,80: one storey); two rooms one over the other, a
    desk's top between (0, 0,75, 2,80, 3,05, 5,85: two storeys, 2,80 high, the upper floor at 3,05); a top floor
    with no ceiling scanned: only those below; from a cloud of two rooms, its heights and its storeys."""

    def test_storeys(self):
        from arqbim.core import scan_walls
        self.assertEqual(scan_walls.storeys([0.0, 2.8]), [(0.0, 2.8)])
        found = scan_walls.storeys([0.0, 0.75, 2.8, 3.05, 5.85])
        self.assertEqual(len(found), 2)
        np.testing.assert_allclose(found, [(0.0, 2.8), (3.05, 2.8)])
        self.assertEqual(scan_walls.storeys([0.0, 2.8, 3.05]), [(0.0, 2.8)])
        self.assertEqual(scan_walls.storeys([0.0, 1.0]), [])
        pts = []
        for base in (0.0, 3.05):
            zs = np.arange(base, base + 2.8001, 0.05)
            for x in np.arange(0.0, 5.0001, 0.05):
                pts += [(x, y, z) for y in (0.0, 4.0) for z in zs]
            for x in np.arange(0.0, 5.0001, 0.1):
                for y in np.arange(0.0, 4.0001, 0.1):
                    pts += [(x, y, base), (x, y, base + 2.8)]
        levels = scan_walls.levels(np.array(pts))
        storeys = scan_walls.storeys(levels)
        self.assertEqual(len(storeys), 2)
        self.assertAlmostEqual(storeys[1][0], 3.05, delta=0.03)
        self.assertAlmostEqual(storeys[1][1], 2.8, delta=0.04)


class ScanToWalls(unittest.TestCase):
    """0.162: a 6 × 4 × 2,8 m room scanned from inside, a 10 cm wall across it with a door's gap (no points from 1,0
    to 1,9 m): the floor and the ceiling found (0 and 2,8 m); the slice's lines square; the wall across one 10 cm
    wall over the gap; the four outer faces, seen from inside only, walls of 30 cm outwards."""

    def _scan(self, turn=0.0):
        rng = np.random.default_rng(5)
        pts = []
        zs = np.arange(0.0, 2.8001, 0.05)
        for x in np.arange(0.0, 6.0001, 0.04):
            for y in (0.0, 4.0):
                pts += [(x, y, z) for z in zs]
        for y in np.arange(0.0, 4.0001, 0.04):
            for x in (0.0, 6.0):
                pts += [(x, y, z) for z in zs]
            if not 1.0 < y < 1.9:
                pts += [(2.95, y, z) for z in zs] + [(3.05, y, z) for z in zs]
        for x in np.arange(0.0, 6.0001, 0.1):
            for y in np.arange(0.0, 4.0001, 0.1):
                pts += [(x, y, 0.0), (x, y, 2.8)]
        p = np.array(pts) + rng.normal(0.0, 0.002, (len(pts), 3))
        a = math.radians(turn)
        rot = np.array(((math.cos(a), -math.sin(a)), (math.sin(a), math.cos(a))))
        p[:, :2] = p[:, :2] @ rot.T
        return p

    def test_room(self):
        from arqbim.core import scan_walls
        pts = self._scan()
        lv = scan_walls.levels(pts)
        self.assertEqual(len(lv), 2)
        self.assertAlmostEqual(lv[0], 0.0, delta=0.03)
        self.assertAlmostEqual(lv[1], 2.8, delta=0.03)
        xy = scan_walls.slice_xy(pts, lv[0])
        segs = scan_walls.lines(xy)
        walls = scan_walls.wall_axes(segs, xy)
        thick = sorted(round(t, 2) for _a, _b, t in walls)
        self.assertEqual(thick, [0.1, 0.3, 0.3, 0.3, 0.3])
        inner = next((a, b) for a, b, t in walls if round(t, 2) == 0.1)
        self.assertAlmostEqual(float(inner[0][0]), 3.0, delta=0.01)
        self.assertGreater(abs(float(inner[1][1] - inner[0][1])), 3.9)        # (over the door's gap)
        outer = [(a, b) for a, b, t in walls if round(t, 2) == 0.3]
        lines_at = sorted(round(float(a[0]), 2) if abs(a[0] - b[0]) < 0.01 else round(float(a[1]), 2) + 100
                          for a, b in outer)
        self.assertEqual(lines_at, [-0.15, 6.15, 99.85, 104.15])        # (all four outwards: x, and y + 100)

    def test_turned_and_squared(self):
        from arqbim.core import scan_walls
        pts = self._scan(turn=30.0)
        xy = scan_walls.slice_xy(pts, 0.0)
        segs = scan_walls.squared(scan_walls.lines(xy))
        base = math.degrees(scan_walls.main_direction(segs))
        self.assertAlmostEqual(base, 30.0, delta=0.3)
        d = segs[:, 1] - segs[:, 0]
        a = np.degrees(np.arctan2(d[:, 1], d[:, 0])) % 90.0
        self.assertTrue(np.all(np.minimum(np.abs(a - base), 90 - np.abs(a - base)) < 1e-6))   # (all square)


class OpeningsFromBlocks(unittest.TestCase):
    """0.160: a 10 × 8 m room in double lines with a door's gap in its bottom wall (4,0 to 4,9 m, its jambs drawn)
    and a door block there (its leaf and swing into the room), a table block: the bottom wall one wall across the
    gap; the door 0,9 m wide where it was drawn, opening into the room; the table furniture, its outline 1,6 × 0,9."""

    def _drawing(self):
        from arqbim.core import cad
        lines = [((0, 0), (4000, 0)), ((4900, 0), (10000, 0)), ((10000, 0), (10000, 8000)), ((10000, 8000), (0, 8000)),
                 ((0, 8000), (0, 0)), ((200, 200), (4000, 200)), ((4900, 200), (9800, 200)), ((9800, 200), (9800, 7800)),
                 ((9800, 7800), (200, 7800)), ((200, 7800), (200, 200)), ((4000, 0), (4000, 200)),
                 ((4900, 0), (4900, 200))]
        rows = ["0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
                "0", "SECTION", "2", "BLOCKS",
                "0", "BLOCK", "8", "0", "2", "PORTA90", "10", "0", "20", "0",
                "0", "LINE", "8", "0", "10", "0", "20", "0", "11", "0", "21", "900",
                "0", "ARC", "8", "0", "10", "0", "20", "0", "40", "900", "50", "0", "51", "90",
                "0", "ENDBLK",
                "0", "BLOCK", "8", "0", "2", "MESA160", "10", "0", "20", "0",
                "0", "LWPOLYLINE", "8", "0", "90", "4", "70", "1", "10", "0", "20", "0", "10", "1600", "20", "0",
                "10", "1600", "20", "900", "10", "0", "20", "900",
                "0", "ENDBLK", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
        for (x0, y0), (x1, y1) in lines:
            rows += ["0", "LINE", "8", "PAREDES", "10", str(x0), "20", str(y0), "11", str(x1), "21", str(y1)]
        rows += ["0", "INSERT", "8", "PORTAS", "2", "PORTA90", "10", "4000", "20", "200", "50", "0",
                 "0", "INSERT", "8", "MOBILIARIO", "2", "MESA160", "10", "3000", "20", "3000", "50", "0",
                 "0", "ENDSEC", "0", "EOF", ""]
        return cad.read("\n".join(rows))

    def test_door_and_table(self):
        from arqbim.core import cad, cad_openings, cad_walls
        drawing = self._drawing()
        place = lambda s: np.asarray(s, dtype=float) * 0.001                       # noqa: E731
        segs = place(cad.segments(cad.Drawing(drawing.entities, drawing.blocks, 1.0))["PAREDES"])
        blocks = cad_openings.instances(drawing, place)
        doors = [b for b in blocks if cad_openings.kind_of(b) == "door"]
        tables = [b for b in blocks if cad_openings.kind_of(b) == "furniture"]
        self.assertEqual((len(doors), len(tables)), (1, 1))
        self.assertTrue(doors[0].arc)
        walls = cad_walls.wall_axes(segs, blocks=doors)
        self.assertEqual(len(walls), 4)
        bottom = next(w for w in walls if abs(w[0][1] - 0.1) < 1e-6 and abs(w[1][1] - 0.1) < 1e-6)
        a, b = sorted((bottom[0], bottom[1]), key=lambda p: p[0])
        self.assertAlmostEqual(float(np.linalg.norm(b - a)), 9.8, places=6)
        s0, s1, side = cad_openings.span_on(doors[0], a, b, 0.2)
        self.assertAlmostEqual(s0, 3.9, places=6)
        self.assertAlmostEqual(s1 - s0, 0.9, places=6)
        self.assertEqual(side, 1)                                                  # (into the room: +Y)
        self.assertIsNone(cad_openings.span_on(tables[0], a, b, 0.2))
        outline = cad_openings.footprint(tables[0])
        from shapely.geometry import Polygon
        self.assertAlmostEqual(Polygon(outline).area, 1.6 * 0.9, places=6)
        no_door = cad_walls.wall_axes(segs)
        self.assertEqual(len(no_door), 5)                                          # (the gap: two walls)


class CadLinks(unittest.TestCase):
    """0.158: where a linked drawing goes — in the project's survey coordinates when near them, origin to origin
    when near (0, 0), else in the middle of the view; its segments placed (mm, turned 90°, moved); kept and read
    back (the project moved: its file beside it)."""

    def test_placement(self):
        from arqbim.model import cad_links as cm
        raw = {"PAREDES": np.array([[[0.0, 0.0], [10000.0, 0.0]], [[0.0, 0.0], [0.0, 8000.0]]])}
        self.assertEqual(cm.placement(raw, 0.001, (0.0, 0.0, 0.0), (50.0, 50.0)), ((0.0, 0.0), "origin"))
        far = {"PAREDES": raw["PAREDES"] + (150000000.0, 400000000.0)}             # (mm, 150 km away)
        self.assertEqual(cm.placement(far, 0.001, (150002.0, 400003.0, 0.0), (0.0, 0.0)),
                         ((-150002.0, -400003.0), "shared"))
        origin, how = cm.placement(far, 0.001, (0.0, 0.0, 0.0), (20.0, 10.0))
        self.assertEqual(how, "centre")
        np.testing.assert_allclose(np.array(origin) + (150005.0, 400004.0), (20.0, 10.0))
        link = cm.CadLink("planta", "/tmp/planta.dxf", 0.001, (1.0, 2.0), 90.0)
        np.testing.assert_allclose(link.place(raw["PAREDES"])[0], ((1.0, 2.0), (1.0, 12.0)), atol=1e-9)

    def test_saved(self):
        import tempfile
        from arqbim.model import cad_links as cm
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "planta.dxf")
            with open(path, "w") as f:
                f.write("0\nEOF\n")
            link = cm.CadLink("planta", path, 0.01, (3.0, 4.0), 15.0, "abc", ["COTAS"], locked=True)
            data = cm.to_dict(link, folder)
            other = os.path.join(folder, "copia")
            os.makedirs(other)
            with open(os.path.join(other, "planta.dxf"), "w") as f:
                f.write("0\nEOF\n")
            back = cm.from_dict(data, (1.0, 1.0), other)
            self.assertEqual(os.path.normpath(back.path), os.path.normpath(os.path.join(other, "planta.dxf")))
            self.assertEqual((back.units, back.angle, back.storey, back.hidden, back.locked, back.uid),
                             (0.01, 15.0, "abc", ["COTAS"], True, link.uid))
            np.testing.assert_allclose(back.origin, (4.0, 5.0))


class SurveyDxf(unittest.TestCase):
    """0.156: a survey drawing's points with a height, by layer — a POINT, a contour line (LWPOLYLINE at its
    elevation), a 3D POLYLINE, a 3DFACE, a block, a spot height written («12,35»; a point's number «17» is not);
    the layers with heights told from a 2D one."""

    def test_read(self):
        from arqbim.core import dxf_read
        dxf = "\n".join([
            "0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1015", "0", "ENDSEC",
            "0", "SECTION", "2", "ENTITIES",
            "0", "POINT", "8", "PONTOS", "10", "1.0", "20", "2.0", "30", "10.5",
            "0", "LWPOLYLINE", "8", "CURVAS", "90", "3", "38", "11.0", "10", "0.0", "20", "0.0", "10", "5.0", "20",
            "0.0", "10", "5.0", "20", "5.0",
            "0", "POLYLINE", "8", "LINHA3D", "66", "1", "70", "8",
            "0", "VERTEX", "8", "LINHA3D", "10", "0.0", "20", "9.0", "30", "12.0",
            "0", "VERTEX", "8", "LINHA3D", "10", "3.0", "20", "9.0", "30", "12.5",
            "0", "SEQEND",
            "0", "3DFACE", "8", "FACES", "10", "0", "20", "0", "30", "1", "11", "1", "21", "0", "31", "2",
            "12", "1", "22", "1", "32", "3", "13", "1", "23", "1", "33", "3",
            "0", "INSERT", "8", "PONTOS", "2", "PT", "10", "4.0", "20", "4.0", "30", "10.8",
            "0", "TEXT", "8", "COTAS", "10", "7.0", "20", "7.0", "30", "0.0", "1", "12,35",
            "0", "TEXT", "8", "COTAS", "10", "8.0", "20", "8.0", "30", "0.0", "1", "17",
            "0", "LINE", "8", "PAREDES", "10", "0", "20", "0", "30", "0", "11", "5", "21", "0", "31", "0",
            "0", "LINE", "8", "PAREDES", "10", "5", "20", "0", "30", "0", "11", "5", "21", "5", "31", "0",
            "0", "ENDSEC", "0", "EOF", ""])
        layers = dxf_read.read_points(dxf)
        self.assertEqual(layers["PONTOS"], [(1.0, 2.0, 10.5), (4.0, 4.0, 10.8)])
        self.assertEqual(layers["CURVAS"], [(0.0, 0.0, 11.0), (5.0, 0.0, 11.0), (5.0, 5.0, 11.0)])
        self.assertEqual(layers["LINHA3D"], [(0.0, 9.0, 12.0), (3.0, 9.0, 12.5)])
        self.assertEqual(len(layers["FACES"]), 3)                       # (its 4th corner the 3rd again)
        self.assertEqual(layers["COTAS"], [(7.0, 7.0, 12.35)])
        self.assertEqual(sorted(dxf_read.with_heights(layers)), ["COTAS", "CURVAS", "FACES", "LINHA3D", "PONTOS"])


class TangentArcs(unittest.TestCase):
    """0.151: the arc leaving a point along a direction to another point — a half circle when the end is beside it,
    its points on one circle, tangent at the start; straight ahead: no arc."""

    def test_arcs(self):
        from arqbim.core.lines import tangent_arc
        pts = tangent_arc((0, 0, 0), (1, 0, 0), (0, 2, 0), (0, 0, 1))       # (a half circle up, radius 1)
        self.assertEqual(len(pts), 12)                                        # (180°: 12 pieces of 15°)
        centre = np.array((0.0, 1.0, 0.0))
        self.assertTrue(np.allclose([np.linalg.norm(p - centre) for p in pts], 1.0))
        self.assertTrue(pts[0][0] > 0)                                       # (leaving along +x)
        np.testing.assert_allclose(pts[-1], (0, 2, 0))
        right = tangent_arc((0, 0, 0), (1, 0, 0), (1, -1, 0), (0, 0, 1))      # (a quarter, turning right)
        self.assertEqual(len(right), 6)
        self.assertTrue(all(p[1] <= 1e-9 for p in right))
        self.assertEqual(len(tangent_arc((0, 0, 0), (1, 0, 0), (3, 0, 0), (0, 0, 1))), 1)   # (straight on)


class CirclesAndSmoothSides(unittest.TestCase):
    """0.150 (Phase 7, step 1): a circle is a face of 24 sides (its radius to every corner, its normal up); pulled,
    it is a closed cylinder whose side edges are hidden (one smooth surface); a box keeps its corners."""

    def test_a_circle_pulled(self):
        m = sg.circle_mesh(1.5)
        self.assertEqual((len(m.verts), len(m.faces)), (24, 1))
        self.assertTrue(np.allclose([np.linalg.norm(v) for v in m.verts], 1.5))
        self.assertTrue(np.allclose(m.face_normal(0), (0, 0, 1)))
        sg.push_pull(m, 0, I4, 2.0)
        self.assertTrue(m.is_closed())
        area = 0.5 * 24 * 1.5 ** 2 * math.sin(2 * math.pi / 24)
        self.assertAlmostEqual(m.volume(), area * 2.0)
        self.assertEqual(len(m.hidden), 24)                              # (its 24 side edges: soft)
        drawn = m.visible_edges()
        self.assertEqual(len(drawn), 48)                                 # (only its two circles)

    def test_a_circle_on_a_box_pushed_in(self):
        m = sg.rectangle_mesh(4.0, 4.0)
        sg.push_pull(m, 0, I4, 2.0)
        top = next(k for k in range(len(m.faces)) if np.allclose(m.face_normal(k), (0, 0, 1))
                   and abs(m.verts[m.faces[k][0]][2] - 2.0) < 1e-9)
        ring = [np.array((2.0, 2.0, 2.0)) + v for v in sg.circle_mesh(1.0).verts]
        inner = sg.imprint_polygon(m, top, ring)
        self.assertEqual(inner, top)
        self.assertEqual(len(m.faces[inner]), 24)
        tops = [k for k in range(len(m.faces)) if np.allclose(m.face_normal(k), (0, 0, 1))]
        self.assertAlmostEqual(sum(m.face_area(k) for k in tops), 16.0)        # (the ring and the circle: the top)
        self.assertTrue(m.is_closed())
        sg.push_pull(m, inner, I4, -0.5)                                       # (a round recess)
        self.assertTrue(m.is_closed())
        area = 0.5 * 24 * math.sin(2 * math.pi / 24)
        self.assertAlmostEqual(m.volume(), 32.0 - area * 0.5)

    def test_a_box_keeps_its_corners(self):
        m = sg.rectangle_mesh(2.0, 1.0)
        sg.push_pull(m, 0, I4, 1.0)
        self.assertEqual(len(m.hidden), 0)
        self.assertEqual(len(m.visible_edges()), 12)

    def test_a_polygon(self):
        m = sg.polygon_mesh([(0, 0), (0, 2), (3, 2), (3, 0)])          # (clockwise: turned up)
        self.assertTrue(np.allclose(m.face_normal(0), (0, 0, 1)))
        self.assertAlmostEqual(m.face_area(0), 6.0)


class PushPull(unittest.TestCase):
    def test_pull_rectangle_makes_closed_box(self):
        m = sg.rectangle_mesh(3.2, 4.5)
        r = sg.push_pull(m, 0, I4, 2.8)
        self.assertEqual((r.mode, r.clamped), ("prism", False))
        self.assertEqual((len(m.faces), len(m.verts)), (6, 8))
        self.assertTrue(m.is_closed())
        self.assertAlmostEqual(m.volume(), 3.2 * 4.5 * 2.8)

    def test_push_rectangle_down_makes_box_below(self):
        m = sg.rectangle_mesh(2.0, 1.0)
        sg.push_pull(m, 0, I4, -0.5)
        self.assertTrue(m.is_closed())
        self.assertAlmostEqual(m.volume(), 1.0)
        self.assertEqual(z_range(m), (-0.5, 0.0))

    def test_pull_rectangle_drawn_on_a_wall(self):
        mat = sg.rectangle_matrix((1, 2, 3), (1, 0, 0), (0, 0, 1))  # normal -Y
        m = sg.rectangle_mesh(2.0, 1.0)
        sg.push_pull(m, 0, mat, 0.5)
        w = m.transformed(mat)
        self.assertTrue(w.is_closed())
        self.assertAlmostEqual(w.volume(), 1.0)
        ys = [v[1] for v in w.verts]
        self.assertAlmostEqual(min(ys), 1.5)
        self.assertAlmostEqual(max(ys), 2.0)

    def test_pull_top_of_box_stretches_it(self):
        m = sg.rectangle_mesh(3.2, 4.5)
        sg.push_pull(m, 0, I4, 2.8)
        r = sg.push_pull(m, face_with_normal(m, I4, (0, 0, 1)), I4, 1.0)
        self.assertEqual(r.mode, "stretch")
        self.assertEqual((len(m.faces), len(m.verts)), (6, 8))
        self.assertAlmostEqual(z_range(m)[1], 3.8)
        self.assertAlmostEqual(m.volume(), 3.2 * 4.5 * 3.8)

    def test_push_top_too_far_is_clamped(self):
        m = sg.rectangle_mesh(1.0, 1.0)
        sg.push_pull(m, 0, I4, 1.0)
        r = sg.push_pull(m, face_with_normal(m, I4, (0, 0, 1)), I4, -10.0, min_thickness=0.001)
        self.assertTrue(r.clamped)
        self.assertAlmostEqual(r.distance, -0.999)
        self.assertAlmostEqual(z_range(m)[1], 0.001)
        self.assertTrue(m.is_closed())

    def test_pull_bottom_face(self):
        m = sg.rectangle_mesh(1.0, 1.0)
        sg.push_pull(m, 0, I4, 1.0)
        sg.push_pull(m, face_with_normal(m, I4, (0, 0, -1)), I4, 0.5)
        self.assertAlmostEqual(z_range(m)[0], -0.5)
        self.assertAlmostEqual(m.volume(), 1.5)

    def test_world_distance_on_rotated_and_scaled_object(self):
        mat = translate(5, -2, 1) @ rot_z(30) @ np.diag((2.0, 1.0, 0.5, 1.0))
        m = sg.rectangle_mesh(1.0, 1.0)
        sg.push_pull(m, 0, mat, 1.0)
        lo, hi = z_range(m, mat)
        self.assertAlmostEqual(hi - lo, 1.0)
        sg.push_pull(m, face_with_normal(m, mat, (0, 0, 1)), mat, 0.75)
        lo, hi = z_range(m, mat)
        self.assertAlmostEqual(hi - lo, 1.75)
        self.assertAlmostEqual(m.transformed(mat).volume(), 2.0 * 1.75)

    def test_pull_sloped_face_extrudes(self):
        # Wedge (right triangle in YZ extruded 1 m along X): the slope is not perpendicular to
        # its bottom and back, so Push/Pull adds side faces there; the two triangles at the ends
        # are in the plane of the motion: they stretch (no face beside them on their plane).
        m = PolyMesh([(0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0), (1, 1, 0), (1, 0, 1)],
                     [[0, 2, 1], [3, 4, 5], [0, 1, 4, 3], [0, 3, 5, 2], [1, 2, 5, 4]])
        self.assertTrue(m.is_closed())
        vol0 = m.volume()
        self.assertGreater(vol0, 0)
        area = m.face_area(4)
        faces = len(m.faces)
        r = sg.push_pull(m, 4, I4, 0.3)
        self.assertEqual(r.mode, "stretch")
        self.assertTrue(m.is_closed())
        self.assertAlmostEqual(m.volume(), vol0 + area * 0.3)
        self.assertEqual(len(m.faces), faces + 2)
        ends = [fi for fi in range(len(m.faces)) if abs(m.face_normal(fi)[0]) > 0.99]
        self.assertEqual(sorted(len(m.faces[fi]) for fi in ends), [5, 5])     # each triangle grows a strip


class Imprint(unittest.TestCase):
    """Rectangle drawn on a face of a box: balcony (pull) and recess (push)."""

    def setUp(self):
        self.box = sg.rectangle_mesh(3.2, 4.5)
        sg.push_pull(self.box, 0, I4, 2.8)
        self.front = face_with_normal(self.box, I4, (0, -1, 0))   # wall at y = 0
        self.rect = [(1, 0, 1), (2, 0, 1), (2, 0, 2), (1, 0, 2)]
        self.vol = 3.2 * 4.5 * 2.8

    def test_imprint_splits_the_wall(self):
        fi = sg.imprint_polygon(self.box, self.front, self.rect)
        self.assertEqual(fi, self.front)
        self.assertEqual(len(self.box.faces), 10)
        self.assertTrue(self.box.is_closed())
        self.assertAlmostEqual(self.box.volume(), self.vol)
        self.assertAlmostEqual(self.box.face_area(fi), 1.0)
        self.assertEqual(len(self.box.hidden), 4)
        self.assertEqual(len(self.box.visible_edges()), 12 + 4)

    def test_pull_imprinted_rectangle_makes_a_balcony(self):
        fi = sg.imprint_polygon(self.box, self.front, self.rect)
        r = sg.push_pull(self.box, fi, I4, 1.2)
        self.assertEqual(r.mode, "extrude")
        self.assertTrue(self.box.is_closed())
        self.assertAlmostEqual(self.box.volume(), self.vol + 1.2)
        self.assertAlmostEqual(min(v[1] for v in self.box.verts), -1.2)

    def test_push_imprinted_rectangle_makes_a_recess(self):
        fi = sg.imprint_polygon(self.box, self.front, self.rect)
        sg.push_pull(self.box, fi, I4, -0.3)
        self.assertTrue(self.box.is_closed())
        self.assertAlmostEqual(self.box.volume(), self.vol - 0.3)

    def test_box_still_stretches_after_imprint(self):
        sg.imprint_polygon(self.box, self.front, self.rect)
        top = face_with_normal(self.box, I4, (0, 0, 1))
        r = sg.push_pull(self.box, top, I4, 1.0)
        self.assertEqual(r.mode, "stretch")
        self.assertTrue(self.box.is_closed())
        self.assertAlmostEqual(self.box.volume(), 3.2 * 4.5 * 3.8)

    def test_rectangle_outside_the_face_is_refused(self):
        before = self.box.copy()
        outside = [(2.5, 0, 1), (3.5, 0, 1), (3.5, 0, 2), (2.5, 0, 2)]
        self.assertIsNone(sg.imprint_polygon(self.box, self.front, outside))
        self.assertEqual(self.box.faces, before.faces)
        self.assertEqual(len(self.box.verts), len(before.verts))

    def test_rectangle_inside_a_flat_rectangle(self):
        sheet = sg.rectangle_mesh(4.0, 4.0)
        fi = sg.imprint_polygon(sheet, 0, [(1, 1, 0), (3, 1, 0), (3, 3, 0), (1, 3, 0)])
        self.assertIsNotNone(fi)
        solid = sheet.copy()
        sg.push_pull(sheet, fi, I4, 1.0)  # (0.310) as SketchUp: the face moves up, no bottom left
        self.assertEqual(len(sheet.faces), 4 + 4 + 1)
        self.assertAlmostEqual(z_range(sheet)[1], 1.0)
        sg.push_pull(solid, fi, I4, 1.0, keep_start=True)          # Ctrl: the base stays, a closed box on it
        self.assertEqual(len(solid.faces), 5 + 4 + 1)


class FacesAlone(unittest.TestCase):
    """(0.310) As SketchUp: an offset rectangle's middle pushed down is a tray open on top; Ctrl («criar sólido»)
    leaves the starting face, a closed solid either way; a face picked alone (with the strips joined to it across
    hidden edges) is deleted or moved by itself."""

    def setUp(self):
        self.sheet = sg.rectangle_mesh(4.0, 4.0)
        self.inner = sg.imprint_polygon(self.sheet, 0, [(1, 1, 0), (3, 1, 0), (3, 3, 0), (1, 3, 0)])

    def _at(self, mesh, z):
        return [k for k in range(len(mesh.faces)) if np.allclose(mesh.face_points(k)[:, 2], z)]

    def test_pushed_down_an_open_tray(self):
        r = sg.push_pull(self.sheet, self.inner, I4, -0.5)
        self.assertEqual((r.mode, round(r.distance, 9)), ("extrude", -0.5))
        self.assertEqual(len(self.sheet.faces), 4 + 4 + 1)
        top = self._at(self.sheet, 0.0)
        self.assertAlmostEqual(sum(self.sheet.face_area(k) for k in top), 16.0 - 4.0)    # (the frame only: open)
        bottom = self._at(self.sheet, -0.5)
        self.assertEqual(len(bottom), 1)
        self.assertTrue(np.allclose(self.sheet.face_normal(bottom[0]), (0, 0, 1)))       # (seen from above)
        centre = np.array((2.0, 2.0, -0.25))
        walls = [k for k in range(len(self.sheet.faces)) if abs(self.sheet.face_normal(k)[2]) < 1e-9]
        self.assertEqual(len(walls), 4)
        for k in walls:                                  # (the tray's walls look into it)
            self.assertGreater(float(self.sheet.face_normal(k) @ (centre - self.sheet.face_points(k).mean(axis=0))),
                               0)

    def test_ctrl_a_closed_box_up_or_down(self):
        for d in (-0.5, 0.5):
            sheet = self.sheet.copy()
            sg.push_pull(sheet, self.inner, I4, d, keep_start=True)
            self.assertEqual(len(sheet.faces), 5 + 4 + 1, d)
            frame = set(sg.surface_faces(sheet, next(k for k in self._at(sheet, 0.0) if k != self.inner)))
            box = PolyMesh(sheet.verts, [f for k, f in enumerate(sheet.faces) if k not in frame])
            self.assertTrue(box.is_closed(), d)
            self.assertAlmostEqual(box.volume(), 4.0 * 0.5)                               # (outwards, both ways)

    def test_ctrl_on_a_box(self):
        box = sg.rectangle_mesh(2.0, 1.0)
        sg.push_pull(box, 0, I4, 1.0)
        top = face_with_normal(box, I4, (0, 0, 1))
        stacked = box.copy()
        r = sg.push_pull(stacked, top, I4, 0.5, keep_start=True)       # (not stretched: a new box on it)
        self.assertEqual((r.mode, len(stacked.faces)), ("extrude", 6 + 4 + 1))
        self.assertAlmostEqual(z_range(stacked)[1], 1.5)
        r = sg.push_pull(box, top, I4, -5.0, keep_start=True, min_thickness=0.001)   # (in: never through)
        self.assertTrue(r.clamped)
        self.assertEqual(len(box.faces), 6 + 4 + 1)

    def test_the_face_clicked(self):
        ring = [k for k in range(len(self.sheet.faces)) if k != self.inner]
        self.assertEqual(sg.surface_faces(self.sheet, ring[0]), frozenset(ring))       # (the frame: one face)
        self.assertEqual(sg.surface_faces(self.sheet, self.inner), frozenset({self.inner}))
        cylinder = sg.circle_mesh(1.0)
        sg.push_pull(cylinder, 0, I4, 2.0)
        side = next(k for k in range(len(cylinder.faces)) if abs(cylinder.face_normal(k)[2]) < 1e-9)
        self.assertEqual(len(sg.surface_faces(cylinder, side)), 24)                      # (its smooth side)
        self.assertEqual(len(sg.part_edges(self.sheet, {self.inner})), 4)

    def test_deleted(self):
        ring = frozenset(k for k in range(len(self.sheet.faces)) if k != self.inner)
        hole = sg.remove_faces(self.sheet, {self.inner})                   # (the frame keeps the edges)
        self.assertEqual((len(hole.faces), len(hole.lines), len(hole.verts)), (4, 0, 8))
        middle = sg.remove_faces(self.sheet, ring)                         # (its outline stays as lines)
        self.assertEqual((len(middle.faces), len(middle.lines), len(middle.verts)), (1, 4, 8))
        self.assertAlmostEqual(middle.face_area(0), 4.0)
        self.assertEqual(len(middle.hidden), 0)
        alone = sg.remove_faces(self.sheet, ring, keep_edges=False)        # (picked with its edges: they go)
        self.assertEqual((len(alone.faces), len(alone.lines), len(alone.verts)), (1, 0, 4))

    def test_moved(self):
        box = sg.rectangle_mesh(2.0, 1.0)
        sg.push_pull(box, 0, I4, 1.0)
        top = face_with_normal(box, I4, (0, 0, 1))
        up = sg.move_part(box, {top}, translate(0, 0, 0.5))               # (the sides stretch)
        self.assertEqual(len(up.faces), 6)
        self.assertTrue(up.is_closed())
        self.assertAlmostEqual(up.volume(), 3.0)
        raised = sg.move_part(self.sheet, {self.inner}, translate(0, 0, 0.2))   # (the frame's strips slope, flat)
        self.assertEqual((len(raised.faces), len(raised.hidden)), (5, 4))
        a = np.radians(10.0)
        tilt = translate(0, 2, 0) @ np.array(((1, 0, 0, 0), (0, np.cos(a), -np.sin(a), 0),
                                               (0, np.sin(a), np.cos(a), 0), (0, 0, 0, 1))) @ translate(0, -2, 0)
        tilted = sg.move_part(self.sheet, {self.inner}, tilt)             # (two strips no longer flat: folded)
        self.assertEqual((len(tilted.faces), len(tilted.hidden)), (1 + 2 + 2 * 2, 4 + 2))
        for k in range(len(tilted.faces)):
            pts = tilted.face_points(k)
            n = tilted.face_normal(k)
            self.assertTrue(np.allclose((pts - pts[0]) @ (n / np.linalg.norm(n)), 0.0), k)
        for k in range(len(raised.faces)):
            pts = raised.face_points(k)
            n = raised.face_normal(k)
            self.assertTrue(np.allclose((pts - pts[0]) @ (n / np.linalg.norm(n)), 0.0), k)


class SeveralFaces(unittest.TestCase):
    """(0.311) Push/Pull on several faces at once: the same distance for all, each along its own normal; faces that
    touch go as one piece (no wall between them), as push_pull does one face."""

    def setUp(self):
        self.sheet = sg.rectangle_mesh(4.0, 4.0)
        self.inner = sg.imprint_polygon(self.sheet, 0, [(1, 1, 0), (3, 1, 0), (3, 3, 0), (1, 3, 0)])
        self.frame = [k for k in range(len(self.sheet.faces)) if k != self.inner]

    def _flat(self, mesh):
        for k in range(len(mesh.faces)):
            pts = mesh.face_points(k)
            n = mesh.face_normal(k)
            self.assertTrue(np.allclose((pts - pts[0]) @ (n / np.linalg.norm(n)), 0.0), k)

    def _edges_ok(self, mesh):
        self.assertTrue(all(len(fis) <= 2 for fis in mesh.edge_faces().values()))

    def test_the_frame_as_one_face(self):
        r = sg.push_pull_faces(self.sheet, self.frame, I4, 0.3)
        self.assertEqual((r.mode, round(r.distance, 9)), ("extrude", 0.3))
        self.assertEqual(sorted(r.faces), sorted(self.frame))             # (their numbers hold)
        self.assertEqual(len(self.sheet.faces), 1 + 4 + 8)                # (no wall between the strips)
        self.assertTrue(all(np.allclose(self.sheet.face_points(k)[:, 2], 0.3) for k in self.frame))
        self.assertTrue(np.allclose(self.sheet.face_points(self.inner)[:, 2], 0.0))
        self.assertEqual(len(self.sheet.hidden), 4)                      # (the strips still one face on top)
        self.assertEqual(sg.surface_faces(self.sheet, self.frame[0]), frozenset(self.frame))
        self._edges_ok(self.sheet)
        self._flat(self.sheet)

    def test_all_of_a_sketch_a_closed_box(self):
        r = sg.push_pull_faces(self.sheet, range(5), I4, 0.3)
        self.assertEqual(r.mode, "prism")
        self.assertEqual(len(self.sheet.faces), 5 + 5 + 4)
        self.assertTrue(self.sheet.is_closed())
        self.assertAlmostEqual(self.sheet.volume(), 16.0 * 0.3)
        self.assertEqual(len(self.sheet.hidden), 4 + 4)                  # (the top keeps the frame's strips joined)
        self.assertTrue(all(np.allclose(self.sheet.face_points(k)[:, 2], 0.3) for k in r.faces))

    def test_ctrl_a_closed_ring(self):
        r = sg.push_pull_faces(self.sheet, self.frame, I4, 0.3, keep_start=True)
        self.assertEqual(r.mode, "extrude")
        ring = PolyMesh(self.sheet.verts, [f for k, f in enumerate(self.sheet.faces) if k != self.inner])
        self.assertTrue(ring.is_closed())
        self.assertAlmostEqual(ring.volume(), 12.0 * 0.3)

    def test_two_rooms_of_a_plan(self):
        plan = sg.rectangle_mesh(4.0, 2.0)
        sg.split_by_segment(plan, np.array((2.0, 0, 0)), np.array((2.0, 2.0, 0)))
        self.assertEqual(len(plan.faces), 2)
        r = sg.push_pull_faces(plan, {0, 1}, I4, 2.8)
        self.assertEqual(r.mode, "prism")
        self.assertTrue(plan.is_closed())
        self.assertAlmostEqual(plan.volume(), 4.0 * 2.0 * 2.8)
        self.assertEqual(len(plan.faces), 2 + 2 + 6)                      # (no wall between the rooms)
        self.assertEqual(len(plan.hidden), 2)                            # (the long walls: one face each, seen)

    def test_two_apart_down_and_up(self):
        two = PolyMesh([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (3, 0, 1), (5, 0, 1), (5, 1, 1), (3, 1, 1)],
                       [[0, 1, 2, 3], [4, 5, 6, 7]])
        r = sg.push_pull_faces(two, {0, 1}, I4, 0.5)
        self.assertEqual((r.mode, len(two.faces)), ("prism", 2 * 6))
        self.assertTrue(two.is_closed())
        self.assertAlmostEqual(two.volume(), 3.0 * 0.5)
        self.assertEqual(sorted(round(float(two.face_points(k)[0, 2]), 9) for k in r.faces), [0.5, 1.5])

    def test_on_boxes_the_sides_stretch(self):
        box = sg.rectangle_mesh(2.0, 1.0)
        sg.push_pull(box, 0, I4, 1.0)
        top = face_with_normal(box, I4, (0, 0, 1))
        side = face_with_normal(box, I4, (1, 0, 0))
        r = sg.push_pull_faces(box, {top, side}, I4, 0.5)                # (the top and a side: it grows both ways)
        self.assertEqual((r.mode, len(box.faces)), ("stretch", 6))
        self.assertTrue(box.is_closed())
        self.assertAlmostEqual(box.volume(), 2.5 * 1.0 * 1.5)
        low = sg.rectangle_mesh(1.0, 1.0)
        sg.push_pull(low, 0, I4, 1.0)
        high = sg.rectangle_mesh(1.0, 1.0)
        sg.push_pull(high, 0, I4, 2.0)
        both = PolyMesh(low.verts + [v + (3, 0, 0) for v in high.verts],
                        low.faces + [[i + len(low.verts) for i in f] for f in high.faces])
        tops = {face_with_normal(both, I4, (0, 0, 1)), 6 + face_with_normal(high, I4, (0, 0, 1))}
        r = sg.push_pull_faces(both, tops, I4, -1.5)                      # (the same for both: the low one stops it)
        self.assertTrue(r.clamped)
        self.assertAlmostEqual(r.distance, -(1.0 - sg.MIN_THICKNESS))
        self.assertTrue(both.is_closed())

    def test_a_fold_a_thicker_shell(self):
        corner = PolyMesh([(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0), (0, 2, 2), (0, 0, 2)],
                          [[0, 1, 2, 3], [0, 3, 4, 5]])                  # (a floor and a wall, seen from the room)
        r = sg.push_pull_faces(corner, {0, 1}, I4, 0.2)
        self.assertEqual(r.mode, "prism")
        self.assertTrue(corner.is_closed())
        self.assertAlmostEqual(corner.volume(), 2 * (2.0 * 2.0 * 0.2) - 0.2 * 2.0 * 0.2)   # (no gap at the fold)
        self._flat(corner)
        self._edges_ok(corner)

    def test_a_tray_of_two_rooms(self):
        r = sg.push_pull_faces(self.sheet, {self.inner}, I4, -0.5)        # (one face: as push_pull, open on top)
        self.assertEqual((r.mode, len(self.sheet.faces)), ("extrude", 4 + 4 + 1))
        self.assertTrue(np.allclose(self.sheet.face_points(self.inner)[:, 2], -0.5))


class DivideFaces(unittest.TestCase):
    """A line across a face divides it; Push/Pull then moves one part (0.51)."""

    def setUp(self):
        self.box = sg.rectangle_mesh(2.0, 1.0)              # 2 × 1 × 1 m
        sg.push_pull(self.box, 0, I4, 1.0)
        self.top = face_with_normal(self.box, I4, (0, 0, 1))

    def test_line_across_the_top_divides_it_and_the_box_stays_closed(self):
        new = sg.split_face(self.box, self.top, [(1, 0, 1), (1, 1, 1)])
        self.assertIsNotNone(new)
        self.assertEqual(len(self.box.faces), 7)
        self.assertTrue(self.box.is_closed())                       # the sides got the points too
        self.assertAlmostEqual(self.box.face_area(self.top) + self.box.face_area(new), 2.0)
        self.assertAlmostEqual(self.box.volume(), 2.0)

    def test_refused_along_an_edge_outside_or_not_reaching_the_outline(self):
        for path in ([(0, 0, 1), (2, 0, 1)],                          # along the outline
                     [(1, 0, 1), (1, 0.5, 1)],                        # stops inside
                     [(1, 0, 1), (1, 1, 1.2)],                        # off the face
                     [(1, 0, 1), (3, 1, 1)]):                         # goes out of it
            before = [list(f) for f in self.box.faces]
            self.assertIsNone(sg.split_face(self.box, self.top, path), path)
            self.assertEqual(self.box.faces, before)

    def test_L_path_through_the_face(self):
        new = sg.split_face(self.box, self.top, [(0.5, 0, 1), (0.5, 0.5, 1), (2, 0.5, 1)])
        self.assertIsNotNone(new)
        areas = sorted((self.box.face_area(self.top), self.box.face_area(new)))
        self.assertTrue(np.allclose(areas, (0.75, 1.25)), areas)
        self.assertTrue(self.box.is_closed())

    def test_one_line_across_two_parts_divides_both(self):
        sg.split_face(self.box, self.top, [(1, 0, 1), (1, 1, 1)])
        self.assertEqual(sg.split_by_segment(self.box, (0, 0.5, 1), (2, 0.5, 1)), 2)
        tops = [fi for fi in range(len(self.box.faces)) if np.allclose(self.box.face_normal(fi), (0, 0, 1))]
        self.assertEqual(len(tops), 4)
        self.assertTrue(all(abs(self.box.face_area(fi) - 0.5) < 1e-9 for fi in tops))
        self.assertTrue(self.box.is_closed())

    def test_pull_one_part_up_the_sides_follow(self):
        new = sg.split_face(self.box, self.top, [(1, 0, 1), (1, 1, 1)])
        left = self.top if self.box.face_points(self.top)[:, 0].max() < 1.5 else new
        faces = len(self.box.faces)
        r = sg.push_pull(self.box, left, I4, 0.5)
        self.assertEqual(r.mode, "stretch")
        self.assertTrue(self.box.is_closed())
        self.assertAlmostEqual(self.box.volume(), 2.0 + 0.5)
        self.assertEqual(len(self.box.faces), faces + 1)             # only the step: the sides stretched
        front = face_with_normal(self.box, I4, (0, -1, 0))
        self.assertAlmostEqual(self.box.face_area(front), 2.0 + 0.5)    # an L-shaped front

    def test_push_one_part_down_makes_a_step(self):
        new = sg.split_face(self.box, self.top, [(1, 0, 1), (1, 1, 1)])
        r = sg.push_pull(self.box, new, I4, -0.4)
        self.assertTrue(self.box.is_closed())
        self.assertAlmostEqual(self.box.volume(), 2.0 - 0.4)
        r = sg.push_pull(self.box, new, I4, -5.0)                   # never through the bottom
        self.assertTrue(r.clamped and self.box.is_closed())
        self.assertGreater(min(v[2] for v in self.box.face_points(new)), 0.0)

    def test_a_flat_rectangle_divided_by_a_line(self):
        sheet = sg.rectangle_mesh(4.0, 2.0)
        new = sg.split_face(sheet, 0, [(1, 0, 0), (1, 2, 0)])
        self.assertIsNotNone(new)
        self.assertEqual(sorted(round(sheet.face_area(f), 9) for f in (0, new)), [2.0, 6.0])


def top_view_projection(scale=100.0):
    """Orthographic view from above: 1 m = 100 px, x right, y up (screen y down)."""
    return lambda pts: np.column_stack((np.asarray(pts)[:, 0] * scale, -np.asarray(pts)[:, 1] * scale))


class Inference(unittest.TestCase):
    def setUp(self):
        box = sg.rectangle_mesh(2.0, 1.0)
        sg.push_pull(box, 0, I4, 3.0)
        self.obj = SketchObject("box", translate(1, 1, 0), box)
        self.geom = inf.SnapGeometry([self.obj])
        self.project = top_view_projection()

    def snap_at(self, x, y, hit=None):
        origin = np.array((x / 100.0, -y / 100.0, 100.0))
        return inf.find_snap(self.geom, (x, y), self.project, origin, np.array((0, 0, -1.0)), hit)

    def test_endpoint_beats_everything_nearby(self):
        s = self.snap_at(303, -102)  # 3 px / 2 px from corner (3, 1)
        self.assertEqual(s.kind, inf.ENDPOINT)
        self.assertTrue(np.allclose(s.point[:2], (3, 1)))
        self.assertAlmostEqual(s.point[2], 3.0)  # top corner, seen from above

    def test_midpoint(self):
        s = self.snap_at(200, -104)  # near the middle of edge (1,1)-(3,1)
        self.assertEqual(s.kind, inf.MIDPOINT)
        self.assertTrue(np.allclose(s.point, (2, 1, 3)))

    def test_on_edge(self):
        s = self.snap_at(250, -103)
        self.assertEqual(s.kind, inf.ON_EDGE)
        self.assertTrue(np.allclose(s.point, (2.5, 1, 3)))

    def test_origin(self):
        s = self.snap_at(4, 5)
        self.assertEqual(s.kind, inf.ORIGIN)
        self.assertTrue(np.allclose(s.point, 0))

    def test_on_face_and_nothing(self):
        s = self.snap_at(200, -150, hit=(self.obj.id, np.array((2.0, 1.5, 3.0)), np.array((0, 0, 1.0))))
        self.assertEqual(s.kind, inf.ON_FACE)
        self.assertIsNone(self.snap_at(600, -600))

    def test_hidden_points_are_ignored(self):
        # Seen from below the ground (camera at z = -100 looking up), the face under
        # the cursor is the bottom of the box: the top corners are behind it.
        origin = np.array((3.0, 1.0, -100.0))
        hit = (self.obj.id, np.array((2.97, 1.02, 0.0)), np.array((0, 0, -1.0)))
        s = inf.find_snap(self.geom, (303, -102), self.project, origin, np.array((0, 0, 1.0)), hit)
        self.assertEqual(s.kind, inf.ENDPOINT)
        self.assertAlmostEqual(s.point[2], 0.0)

    def test_corner_of_the_face_under_the_cursor_seen_at_a_grazing_angle(self):
        # Looking almost along the top face: its far corner is farther along the ray
        # than the hit point, but it is ON the face, so it must stay visible.
        origin = np.array((-20.0, 1.5, 3.2))
        target = np.array((3.0, 1.0, 3.0))
        direction = sg.normalize(target - origin)
        hit = (self.obj.id, np.array((2.9, 1.05, 3.0)), np.array((0, 0, 1.0)))
        s = inf.find_snap(self.geom, (303, -102), self.project, origin, direction, hit)
        self.assertEqual(s.kind, inf.ENDPOINT)
        self.assertTrue(np.allclose(s.point, (3, 1, 3)))

    def test_hidden_edges_give_no_snaps(self):
        sheet = sg.rectangle_mesh(4.0, 4.0)
        sg.imprint_polygon(sheet, 0, [(1, 1, 0), (3, 1, 0), (3, 3, 0), (1, 3, 0)])
        geom = inf.SnapGeometry([SketchObject("s", I4, sheet)])
        self.assertEqual(len(geom.edge_a), 8)  # 4 outer + 4 inner, the 4 helper edges are hidden

    def test_square_inference(self):
        self.assertEqual(inf.square_inference(2.0, -1.97), (2.0, -2.0, True))
        self.assertEqual(inf.square_inference(2.0, 1.5), (2.0, 1.5, False))


class Alignments(unittest.TestCase):
    """0.60: points and edges acquired by resting on them; lined up with them, parallel /
    perpendicular, extensions, where lines cross, Shift's lock (core/tracking.py)."""

    def setUp(self):
        self.project = top_view_projection()
        self.now = [0.0]
        self.tracking = tracking.Tracking(clock=lambda: self.now[0])

    def infer(self, wx, wy, last=None, snap=None, lock=None):
        """The point found with the mouse over the world point (wx, wy), seen from above."""
        mouse, origin, direction = (wx * 100.0, -wy * 100.0), np.array((wx, wy, 100.0)), np.array((0.0, 0.0, -1.0))
        found_lines = tracking.inference_lines(self.tracking, last, plan=True)
        return tracking.infer(snap, found_lines, origin, direction, mouse, self.project, last=last, lock=lock)

    def test_resting_acquires(self):
        p = inf.Snap(inf.ENDPOINT, np.array((2.0, 3.0, 0.0)))
        self.assertFalse(self.tracking.rest(p))
        self.now[0] = 0.1
        self.assertFalse(self.tracking.rest(p))                       # only passing over it: not yet
        self.now[0] = 0.3
        self.assertTrue(self.tracking.rest(p))
        self.now[0] = 1.0
        self.tracking.rest(inf.Snap(inf.MIDPOINT, np.array((5.0, 0.0, 0.0))))
        self.now[0] = 1.5
        self.assertTrue(self.tracking.rest(None))                     # rested on it, then moved away
        self.assertEqual(len(self.tracking.points), 2)
        edge = inf.Snap(inf.ON_EDGE, np.array((1.0, 1.0, 0.0)), edge=(np.zeros(3), np.array((2.0, 2.0, 0.0))))
        self.now[0] = 2.0
        self.tracking.rest(edge)
        self.now[0] = 2.5
        self.assertTrue(self.tracking.rest(edge))
        self.assertEqual(len(self.tracking.edges), 1)
        self.tracking.clear()
        self.assertEqual((self.tracking.points, self.tracking.edges), ([], []))

    def test_lined_up_with_a_point_and_where_two_lines_cross(self):
        self.tracking.points = [np.array((2.0, 3.0, 0.0))]
        last = np.zeros(3)
        found = self.infer(2.04, 1.0, last)                           # 4 px from the green line through (2, 3)
        self.assertEqual(found.kind, "align_y")
        np.testing.assert_allclose(found.point, (2, 1, 0), atol=1e-9)
        found = self.infer(2.03, 0.02, last)                          # and by the red axis through the last point
        self.assertEqual(found.kind, tracking.CROSSING)
        np.testing.assert_allclose(found.point, (2, 0, 0), atol=1e-9)
        self.assertEqual(sorted(line.kind for line in found.lines), ["align_y", "axis_x"])
        self.assertIsNone(self.infer(2.5, 1.0))                       # far from every line: the caller's plane

    def test_parallel_and_perpendicular_to_an_acquired_edge(self):
        self.tracking.edges = [(np.array((0.0, 5.0, 0.0)), np.array((3.0, 8.0, 0.0)))]
        last = np.array((10.0, 0.0, 0.0))
        d, n = np.array((1.0, 1.0, 0.0)) / math.sqrt(2), np.array((-1.0, 1.0, 0.0)) / math.sqrt(2)
        found = self.infer(*(last + 2 * d + 0.03 * n)[:2], last)
        self.assertEqual(found.kind, "parallel")
        np.testing.assert_allclose(found.point, last + 2 * d, atol=1e-9)
        found = self.infer(*(last + 2 * n + 0.03 * d)[:2], last)
        self.assertEqual(found.kind, "perpendicular")
        np.testing.assert_allclose(found.point, last + 2 * n, atol=1e-9)

    def test_extension_and_foot_of_the_perpendicular(self):
        self.tracking.edges = [(np.array((0.0, 5.0, 0.0)), np.array((3.0, 5.0, 0.0)))]
        found = self.infer(5.0, 5.03)
        self.assertEqual(found.kind, "extension")
        np.testing.assert_allclose(found.point, (5, 5, 0), atol=1e-9)
        self.assertIsNone(self.infer(1.5, 5.03))                      # along the edge itself: not its extension
        self.tracking.edges = []
        a, b = np.array((2.0, -2.0, 0.0)), np.array((6.0, 2.0, 0.0))
        snap = inf.Snap(inf.ON_EDGE, np.array((4.02, 0.02, 0.0)), edge=(a, b))
        found = self.infer(4.02, 0.02, np.array((0.0, 4.0, 0.0)), snap)
        self.assertEqual(found.kind, tracking.FOOT)
        np.testing.assert_allclose(found.point, (4, 0, 0), atol=1e-9)

    def test_shift_lock(self):
        last = np.zeros(3)
        lock = tracking.InferenceLine(last, np.array((1.0, 0.0, 0.0)), "axis_x")
        found = self.infer(3.0, 4.0, last, inf.Snap(inf.ENDPOINT, np.array((3.0, 4.0, 0.0))), lock)
        self.assertEqual(found.kind, tracking.LOCKED)
        np.testing.assert_allclose(found.point, (3, 0, 0), atol=1e-9)  # the point brought onto the locked line
        np.testing.assert_allclose(self.infer(1.0, 2.5, last, None, lock).point, (1, 0, 0), atol=1e-9)

    def test_corners_near_the_cursor_line_it_up_by_themselves_on_the_level_drawn(self):
        """0.61: no pause needed (Revit): a corner near the cursor gives red and green lines — brought
        down to the level drawn on (a wall's top corner lines up a point on the floor)."""
        last = np.zeros(3)
        lines = tracking.inference_lines(self.tracking, last, auto=[np.array((4.0, 3.0, 2.8))],
                                         plane=(np.zeros(3), np.array((0.0, 0.0, 1.0))))
        mouse, origin = (3.0, -304.0), np.array((0.03, 3.04, 100.0))
        found = tracking.infer(None, lines, origin, np.array((0.0, 0.0, -1.0)), mouse, self.project, last=last)
        self.assertEqual(found.kind, tracking.CROSSING)                 # its red line × the green axis
        np.testing.assert_allclose(found.point, (0, 3, 0), atol=1e-9)
        self.assertNotIn("align_z", [line.kind for line in lines])
        face = (np.array((0.0, 1.0, 0.0)), np.array((0.0, -1.0, 0.0)))        # drawing on a wall's face (y = 1)
        lines = tracking.inference_lines(self.tracking, None, auto=[np.array((4.0, 3.0, 2.8))], plane=face)
        self.assertEqual(sorted(line.kind for line in lines), ["align_x", "align_z"])
        np.testing.assert_allclose(lines[0].point, (4, 1, 2.8), atol=1e-12)   # the corner brought onto the face

    def test_where_two_edges_cross(self):
        from types import SimpleNamespace
        one = SimpleNamespace(obj_id="a", a=np.array([[0.0, 0, 0]]), b=np.array([[6.0, 6, 0]]),
                              corners=np.array([[0.0, 0, 0], [6.0, 6, 0]]))
        two = SimpleNamespace(obj_id="b", a=np.array([[0.0, 2, 0]]), b=np.array([[4.0, -2, 0]]),
                              corners=np.array([[0.0, 2, 0], [4.0, -2, 0]]))
        geom = inf.SnapGeometry(blocks=[one, two])
        s = inf.find_snap(geom, (103, -100), top_view_projection(), np.array((1.03, 1.0, 100.0)),
                          np.array((0, 0, -1.0)))
        self.assertEqual(s.kind, inf.INTERSECTION)
        np.testing.assert_allclose(s.point, (1, 1, 0), atol=1e-9)


class TemporaryDimensions(unittest.TestCase):
    """0.61: Revit's temporary dimensions — their lines, the angle, the walls beside a wall (core/temp_dims.py)."""

    def test_dimension_lines_and_angle(self):
        from arqbim.core import temp_dims as td
        look = td.LOOK["name"]
        td.LOOK["name"] = "addon"                          # (as the addon draws them, 0.361–0.372)
        try:
            self._addon_lines_and_angle(td)
        finally:
            td.LOOK["name"] = look

    def test_revit_lines_and_angle(self):
        """0.446 — as Revit's: a small oblique cross on each end of the line (no arrows), the extension lines going on
        past it; an angle's grey reference line well past its wide arc, a cross on each of the arc's ends, its value
        just outside the arc's middle."""
        from arqbim.core import temp_dims as td
        look = td.LOOK["name"]
        td.LOOK["name"] = "revit"
        try:
            dim = td.TempDim(np.zeros(3), np.array((4.0, 0.0, 0.0)), np.array((0.0, 0.0, 1.0)))
            segs, label = td.dim_segments(dim, 0.01)
            np.testing.assert_allclose(segs[0], ((0, 0.22, 0), (4, 0.22, 0)), atol=1e-12)    # the line, 22 px off
            np.testing.assert_allclose(label, (2, 0.22, 0), atol=1e-12)
            self.assertEqual(len(segs), 1 + 4 + 2)          # the line, two crosses of two strokes, two extension lines
            ends = np.array([p for s in segs[1:3] for p in s])
            np.testing.assert_allclose(ends.mean(axis=0), (0, 0.22, 0), atol=1e-12)   # a cross centred on the end
            np.testing.assert_allclose(np.linalg.norm(segs[1][1] - segs[1][0]), 0.10, atol=1e-12)    # 2 × 5 px
            angle = td.TempAngle(np.zeros(3), np.array((1.0, 0, 0)), 90.0, np.array((0.0, 0, 1)), radius_px=200.0)
            arc, at = td.arc_segments(angle, 0.01)
            np.testing.assert_allclose(arc[0], ((0, 0, 0), (2.9, 0, 0)), atol=1e-9)    # the reference line, past it
            self.assertTrue(any(np.allclose(p, (0, 2.0, 0), atol=1e-9) for s in arc for p in s))   # the arc's end
            self.assertGreater(float(np.linalg.norm(at)), 2.0)                 # its value outside the arc
            self.assertTrue(td.revit())
        finally:
            td.LOOK["name"] = look

    def _addon_lines_and_angle(self, td):
        dim = td.TempDim(np.zeros(3), np.array((4.0, 0.0, 0.0)), np.array((0.0, 0.0, 1.0)))
        segs, label = td.dim_segments(dim, 0.01)                       # 1 px = 1 cm: drawn 22 cm to the left
        np.testing.assert_allclose(segs[0][0], (0, 0.22, 0), atol=1e-12)
        np.testing.assert_allclose(label, (2, 0.22, 0), atol=1e-12)
        self.assertEqual(len(segs), 7)                 # (0.361) the line, two open arrows, two extension lines
        np.testing.assert_allclose(segs[1][1], (0.09, 0.255, 0), atol=1e-12)          # an arrow's wing, 9 px long
        np.testing.assert_allclose(segs[-2][1], (0, 0.31, 0), atol=1e-12)             # going on 9 px past the line
        self.assertEqual(len(td.dim_segments(dim, 0.01, dashed=True)[0]), 31 + 6)     # dashes of 8 + 5 px
        short = td.dim_segments(td.TempDim(np.zeros(3), np.array((0.1, 0, 0)), np.array((0.0, 0, 1))), 0.01)[0]
        self.assertEqual(len(short), 1 + 6 + 2)        # too short for its arrows: outside, on two leaders
        flat = td.TempDim(np.zeros(3), np.array((4.0, 0, 0)), np.array((0.0, 0, 1)), offset_px=0.0, kind="relation")
        self.assertEqual(len(td.dim_segments(flat, 0.01)[0]), 1 + 4)    # a relation, on what it measures: its arrows
        dim.side = -1.0
        self.assertLess(td.dim_segments(dim, 0.01)[1][1], 0)            # the other side
        self.assertAlmostEqual(dim.value, 4.0)
        self.assertAlmostEqual(td.level_angle((0, 0, 0), (1, 1, 0)), 45.0)
        self.assertAlmostEqual(td.level_angle((0, 0, 0), (0, -1, 0)), 270.0)
        angle = td.TempAngle(np.zeros(3), np.array((1.0, 0, 0)), 90.0, np.array((0.0, 0, 1)))
        arc, at = td.arc_segments(angle, 0.01)
        np.testing.assert_allclose(arc[-1][1], (0, 0.42, 0), atol=1e-9)  # ends on the green axis
        self.assertGreater(at[0], 0)
        self.assertGreater(at[1], 0)

    def test_walls_beside_a_wall(self):
        from arqbim.core import temp_dims as td
        axis = (np.zeros(3), np.array((5.0, 0, 0)))
        others = [((0.0, 3, 0), (5.0, 3, 0)),          # left, 3 m
                  ((1.0, -2, 0), (3.0, -2, 0)),        # right, 2 m (measured in the middle of the overlap)
                  ((0.0, 6, 0), (5.0, 6, 0)),          # left, farther
                  ((0.0, 0, 0), (0.0, 4, 0)),          # not parallel
                  ((6.0, 1, 0), (9.0, 1, 0))]          # parallel, not beside it
        found = td.neighbour_walls(axis, others)
        self.assertEqual([(side, round(dist, 6)) for side, dist, _p, _f in found], [(1, 3.0), (-1, -2.0)])
        np.testing.assert_allclose(found[1][2], (2, 0, 0), atol=1e-12)
        np.testing.assert_allclose(found[1][3], (2, -2, 0), atol=1e-12)

    def test_a_walls_relations(self):
        """0.361: the walls round a wall — the nearest parallel on each side, the first wall beyond a free end — from
        axis to axis or from face to face; one against it (joined, or touching) is no relation."""
        from arqbim.core import temp_dims as td
        axis = (np.zeros(3), np.array((4.0, 0, 0)))                     # 20 cm thick
        others = [("A", (0.0, 3, 0), (4.0, 3, 0), 0.2),                  # left, 3 m
                  ("B", (-1.0, -2.5, 0), (6.0, -2.5, 0), 0.3),           # right, 2,5 m
                  ("C", (0.0, -1, 0), (0.0, 4, 0), 0.2),                 # across its start: joined there
                  ("D", (5.0, -2, 0), (5.0, 2, 0), 0.2),                 # across beyond its end, 1 m on
                  ("E", (0.0, 6, 0), (4.0, 6, 0), 0.2),                  # left, farther
                  ("F", (0.0, 0.15, 0), (4.0, 0.15, 0), 0.1)]            # against its left face
        axes = td.wall_relations(axis, 0.2, others)
        self.assertEqual([(r.kind, r.which, r.other, round(r.value, 6)) for r in axes],
                         [("side", 1, "A", 3.0), ("side", -1, "B", 2.5), ("end", 1, "D", 1.0)])
        np.testing.assert_allclose(axes[0].a, (0.8, 0, 0), atol=1e-12)  # at 20 % of the overlap (its length: 50 %)
        faces = td.wall_relations(axis, 0.2, others, faces=True)
        self.assertEqual([round(r.value, 6) for r in faces], [2.8, 2.25, 0.9])
        np.testing.assert_allclose(faces[1].a, (0.8, -0.1, 0), atol=1e-12)
        np.testing.assert_allclose(faces[1].b, (0.8, -2.35, 0), atol=1e-12)
        np.testing.assert_allclose(faces[2].b, (4.9, 0, 0), atol=1e-12)
        in_line = td.wall_relations((np.zeros(3), np.array((2.0, 0, 0))), 0.2, [("G", (3.0, 0, 0), (5.0, 0, 0), 0.2)])
        self.assertEqual([(r.kind, r.which, round(r.value, 6)) for r in in_line], [("end", 1, 1.0)])
        askew = [("H", (-0.5, 1, 0), (4.5, 1.05, 0), 0.2)]               # 0,6° off: parallel enough
        self.assertEqual([r.kind for r in td.wall_relations(axis, 0.2, askew)], ["side"])


class ParametricLines(unittest.TestCase):
    """0.62: lines stay editable — an end moved, a length, an angle — and the lines joined there follow."""

    def setUp(self):
        from arqbim.model import line_edit
        self.le = line_edit
        self.doc = Document()
        self.chain = SketchObject("Linhas 1", I4, PolyMesh([(0, 0, 0), (4, 0, 0), (4, 3, 0)], lines=[(0, 1), (1, 2)]))
        self.other = SketchObject("Linhas 2", translate(4, 3, 0), PolyMesh([(0, 0, 0), (4, 0, 0)], lines=[(0, 1)]))
        for obj in (self.chain, self.other):
            self.doc.execute(AddObject(obj))

    def world(self, obj_id):
        obj = self.doc.get(obj_id)
        return [np.round(sg.transform_point(obj.matrix, v), 9).tolist() for v in obj.mesh.verts]

    def test_an_end_moved_takes_the_joined_lines(self):
        n = self.le.move_points(self.doc, [(np.array((4.0, 3.0, 0.0)), np.array((5.0, 4.0, 0.0)))])
        self.assertEqual(n, 2)                                            # its own chain and the other line
        self.assertEqual(self.world(self.chain.id)[2], [5, 4, 0])
        self.assertEqual(self.world(self.other.id)[0], [5, 4, 0])
        self.doc.undo()                                                   # one step
        self.assertEqual(self.world(self.other.id)[0], [4, 3, 0])

    def test_length_angle_point_and_refusal(self):
        self.le.set_length(self.doc, self.chain.id, 0, 1, 6.0)            # the end moves along it
        self.assertEqual(self.world(self.chain.id)[1], [6, 0, 0])         # (the next segment follows)
        self.le.set_angle(self.doc, self.other.id, 0, 1, 90.0)            # turned about its start, as long
        self.assertEqual(self.world(self.other.id)[1], [4, 7, 0])
        self.le.set_point(self.doc, self.chain.id, 0, (-1.0, 0.0, 0.0))
        self.assertEqual(self.world(self.chain.id)[0], [-1, 0, 0])
        with self.assertRaises(self.le.LineRefused):                       # (6, 0) onto (4, 3): that segment vanishes
            self.le.move_points(self.doc, [(np.array((6.0, 0.0, 0.0)), np.array((4.0, 3.0, 0.0)))])
        self.assertEqual(self.world(self.chain.id)[1], [6, 0, 0])


class PushThrough(unittest.TestCase):
    """A rectangle drawn on a wall-like box and pushed in: niche, or hole right through."""

    def setUp(self):
        self.box = sg.rectangle_mesh(4.5, 0.2)
        sg.push_pull(self.box, 0, I4, 2.8)                       # 4,50 × 0,20 × 2,80
        self.vol = 4.5 * 0.2 * 2.8
        self.front = face_with_normal(self.box, I4, (0, -1, 0))
        self.rect = [(1, 0, 0.5), (2, 0, 0.5), (2, 0, 1.5), (1, 0, 1.5)]   # 1 × 1 m

    def imprint(self):
        return sg.imprint_polygon(self.box, self.front, self.rect)

    def test_push_to_the_back_face_makes_a_hole(self):
        fi = self.imprint()
        r = sg.push_pull(self.box, fi, I4, -0.2)
        self.assertEqual(r.mode, "hole")
        self.assertAlmostEqual(r.distance, -0.2)
        self.assertTrue(self.box.is_closed())
        self.assertAlmostEqual(self.box.volume(), self.vol - 1.0 * 0.2)
        self.assertEqual(len(self.box.voids), 1)
        self.assertEqual(len(self.box.faces), 16)               # 4 + 4 pieces around the hole, 4 sides, 4 tunnel

    def test_push_beyond_the_back_face_is_the_same_hole(self):
        fi = self.imprint()
        r = sg.push_pull(self.box, fi, I4, -1.0)
        self.assertEqual((r.mode, r.clamped), ("hole", True))
        self.assertAlmostEqual(self.box.volume(), self.vol - 0.2)

    def test_push_part_way_is_a_niche(self):
        fi = self.imprint()
        r = sg.push_pull(self.box, fi, I4, -0.1)
        self.assertEqual(r.mode, "extrude")
        self.assertTrue(self.box.is_closed())
        self.assertAlmostEqual(self.box.volume(), self.vol - 0.1)
        self.assertEqual(self.box.voids, [])

    def test_hole_on_a_rotated_wall(self):
        m = translate(3, 2, 0) @ rot_z(30)
        fi = self.imprint()
        sg.push_pull(self.box, fi, m, -0.2)
        self.assertAlmostEqual(self.box.transformed(m).volume(), self.vol - 0.2)

    def test_no_room_for_a_hole_stops_before_the_back(self):
        # the back face was already split by another rectangle across the projection
        back = face_with_normal(self.box, I4, (0, 1, 0))
        sg.imprint_polygon(self.box, back, [(1.5, 0.2, 0.2), (1.5, 0.2, 2.5), (3, 0.2, 2.5), (3, 0.2, 0.2)])
        fi = sg.imprint_polygon(self.box, self.front, self.rect)
        r = sg.push_pull(self.box, fi, I4, -0.5, min_thickness=0.001)
        self.assertEqual((r.mode, r.clamped), ("extrude", True))
        self.assertAlmostEqual(r.distance, -0.199)
        self.assertTrue(self.box.is_closed())


class Rays(unittest.TestCase):
    def test_ray_plane(self):
        p = sg.ray_plane(np.array((0, 0, 10.0)), np.array((0, 0, -1.0)), np.zeros(3), np.array((0, 0, 1.0)))
        self.assertTrue(np.allclose(p, 0))
        self.assertIsNone(sg.ray_plane(np.array((0, 0, 10.0)), np.array((0, 0, 1.0)), np.zeros(3), np.array((0, 0, 1.0))))

    def test_closest_point_on_vertical_line(self):
        s = sg.closest_on_line_to_ray(np.array((10.0, 0, 2.5)), np.array((-1.0, 0, 0)),
                                      np.zeros(3), np.array((0, 0, 1.0)))
        self.assertAlmostEqual(s, 2.5)


L_SHAPE = [(0, 0, 0), (6, 0, 0), (6, 3, 0), (2, 3, 0), (2, 7, 0), (0, 7, 0)]   # 6×3 + 2×4 = 26 m²


def front_view(x_mouse, y_mouse):
    """Orthographic view from the front (looking along +Y): 1 m = 100 px, x right, z up."""
    origin = np.array((x_mouse / 100.0, -100.0, -y_mouse / 100.0))
    return origin, np.array((0.0, 1.0, 0.0))


def front_projection(pts):
    pts = np.asarray(pts)
    return np.column_stack((pts[:, 0] * 100.0, -pts[:, 2] * 100.0))


class LineTool(unittest.TestCase):
    """Line tool and guide lines (pure geometry)."""

    def test_L_shaped_face_is_triangulated_without_spilling_out(self):
        mesh = PolyMesh(L_SHAPE, [list(range(6))])
        tris, owner = mesh.triangulate()
        self.assertEqual(len(tris), 4)
        area = 0.0
        for a, b, c in tris:
            n = np.cross(mesh.verts[b] - mesh.verts[a], mesh.verts[c] - mesh.verts[a])
            self.assertGreater(n[2], 0)                       # same winding as the face
            area += n[2] / 2
        self.assertAlmostEqual(area, 26.0)
        self.assertAlmostEqual(mesh.face_area(0), 26.0)

    def test_level_outline_faces_up_whatever_the_drawing_order(self):
        for pts in (L_SHAPE, L_SHAPE[::-1]):
            m, local = lines.polygon_frame(pts)
            self.assertTrue(np.allclose(m[:3, 2], (0, 0, 1)))
            self.assertTrue(np.allclose(local[:, 2], 0))
            back = [sg.transform_point(m, p) for p in local]
            self.assertTrue(all(any(np.allclose(b, p) for p in pts) for b in back))

    def test_L_face_pulled_up_is_a_closed_prism(self):
        m, local = lines.polygon_frame(L_SHAPE)
        mesh = PolyMesh(local, [list(range(6))])
        r = sg.push_pull(mesh, 0, m, 2.8)
        self.assertEqual(r.mode, "prism")
        self.assertTrue(mesh.is_closed())
        self.assertAlmostEqual(mesh.transformed(m).volume(), 26 * 2.8)
        self.assertAlmostEqual(z_range(mesh, m)[1], 2.8)

    def test_vertical_outline_faces_the_viewer(self):
        pts = [(0, 0, 0), (3, 0, 0), (3, 0, 2), (0, 0, 2)]
        m, _ = lines.polygon_frame(pts, view_dir=np.array((0.0, 1.0, 0.0)))
        self.assertTrue(np.allclose(m[:3, 2], (0, -1, 0)))
        m, _ = lines.polygon_frame(pts, view_dir=np.array((0.0, -1.0, 0.0)))
        self.assertTrue(np.allclose(m[:3, 2], (0, 1, 0)))

    def test_outline_not_on_one_plane_gives_no_face(self):
        self.assertIsNone(lines.polygon_frame([(0, 0, 0), (2, 0, 0), (2, 2, 0.5), (0, 2, 0)]))

    def test_chain_closing_on_itself_makes_its_loops(self):
        """0.372 (the owner: «só cria o polígono se a geometria fechar no mesmo lugar que iniciou»): a chain that
        ends on itself anywhere — on one of its points after a tail, along one of its lines — or crosses itself
        closes the loop it makes, as SketchUp does; the lines on no loop stay loose; two loops side by side are two
        (not their outline round both); an open chain, or one not on one plane, closes nothing."""
        def p(*xy):
            return [np.array((x, y, 0.0)) for x, y in xy]

        def area(loop):
            q = np.asarray(loop)
            return abs(0.5 * float(np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])))

        def same(segs, want):
            got = sorted(tuple(sorted((tuple(np.round(a, 6)), tuple(np.round(b, 6))))) for a, b in segs)
            return got == sorted(tuple(sorted(((float(a[0]), float(a[1]), 0.0), (float(b[0]), float(b[1]), 0.0))))
                                 for a, b in want)

        # the owner's: a tail from the origin, then round and back onto the tail's end (not the first point)
        loops, loose = lines.chain_loops(p((0, 0), (1, 0), (1, 4), (6, 4), (6, 0), (1, 0)))
        self.assertEqual((len(loops), [len(lp) for lp in loops], area(loops[0])), (1, [4], 20.0))
        self.assertTrue(same(loose, [((0, 0), (1, 0))]))
        # ending along one of its lines: the line is cut there, its piece outside stays loose
        loops, loose = lines.chain_loops(p((0, 0), (4, 0), (4, 3), (0, 3), (2, 0)))
        self.assertEqual((len(loops), area(loops[0])), (1, 9.0))             # (bases 2 and 4, 3 high)
        self.assertTrue(same(loose, [((0, 0), (2, 0))]))
        # crossing it: the loop inside, the two pieces outside loose
        loops, loose = lines.chain_loops(p((0, 0), (4, 0), (4, 3), (2, 3), (2, -1)))
        self.assertEqual((len(loops), area(loops[0])), (1, 6.0))
        self.assertTrue(same(loose, [((0, 0), (2, 0)), ((2, 0), (2, -1))]))
        # a rectangle divided by a line laid back along its side: two faces, nothing loose
        loops, loose = lines.chain_loops(p((0, 0), (4, 0), (4, 2), (0, 2), (0, 0), (2, 0), (2, 2)))
        self.assertEqual((len(loops), sorted(area(lp) for lp in loops), loose), (2, [4.0, 4.0], []))
        # open, too short, not on one plane: nothing
        self.assertEqual(lines.chain_loops(p((0, 0), (4, 0), (4, 3), (0, 3))), ([], None))
        self.assertEqual(lines.chain_loops(p((0, 0), (2, 0), (1, 0))), ([], None))
        bent = [np.array(v, dtype=float) for v in ((0, 0, 0), (1, 0, 0), (1, 1, 1), (0, 1, 0), (0.5, 0, 0))]
        self.assertEqual(lines.chain_loops(bent), ([], None))
        # vertical (a wall's outline), closed on its tail: on its plane too
        loops, _loose = lines.chain_loops([np.array(v, dtype=float) for v in
                                           ((0, 0, 0), (0, 0, 1), (3, 0, 1), (3, 0, 3), (0, 0, 3), (0, 0, 1))])
        self.assertEqual((len(loops), len(loops[0])), (1, 4))

    def test_clicks_along_a_straight_side_are_not_corners(self):
        pts = [(0, 0, 0), (2, 0, 0), (4, 0, 0), (4, 3, 0), (0, 3, 0)]
        self.assertEqual(len(lines.drop_collinear(pts)), 4)

    def test_red_and_green_axes_from_the_last_point(self):
        project = top_view_projection()
        origin, down = np.array((3.0, 1.04, 100.0)), np.array((0.0, 0.0, -1.0))
        p, axis = lines.axis_inference((1, 1, 0), origin, down, (300, -104), project)
        self.assertEqual(axis, "x")
        self.assertTrue(np.allclose(p, (3, 1, 0)))
        origin = np.array((1.05, 4.0, 100.0))
        p, axis = lines.axis_inference((1, 1, 0), origin, down, (105, -400), project)
        self.assertEqual(axis, "y")
        self.assertTrue(np.allclose(p, (1, 4, 0)))
        origin = np.array((2.0, 3.0, 100.0))
        self.assertEqual(lines.axis_inference((1, 1, 0), origin, down, (200, -300), project), (None, None))

    def test_blue_axis_seen_from_the_front(self):
        origin, direction = front_view(104, -250)
        p, axis = lines.axis_inference((1, 0, 1), origin, direction, (104, -250), front_projection)
        self.assertEqual(axis, "z")
        self.assertTrue(np.allclose(p, (1, 0, 2.5)))

    def test_loose_lines_are_edges_without_faces(self):
        mesh = PolyMesh([(0, 0, 0), (2, 0, 0), (2, 1, 0)], lines=[(0, 1), (1, 2)])
        self.assertEqual(set(mesh.visible_edges()), {(0, 1), (1, 2)})
        self.assertFalse(mesh.is_closed())
        self.assertEqual(len(mesh.triangulate()[0]), 0)
        geom = inf.SnapGeometry([SketchObject("l", I4, mesh)])
        self.assertEqual(geom.kinds.count(inf.ENDPOINT), 3)
        self.assertEqual(geom.kinds.count(inf.MIDPOINT), 2)


class SnapIndexNearCursor(unittest.TestCase):
    """Phase 2: inference candidates looked up near the cursor only."""

    def setUp(self):
        self.boxes = []
        for k in range(3):                               # three blocks at x = 0, 10 and 20
            mesh = sg.rectangle_mesh(2.0, 1.0)
            sg.push_pull(mesh, 0, I4, 3.0)
            self.boxes.append(SketchObject("b{}".format(k), translate(10.0 * k, 0, 0), mesh))
        self.index = inf.SnapIndex()
        for b in self.boxes:
            self.index.update(b)
        self.down = np.array((0.0, 0.0, -1.0))
        self.slope = 0.01 / 100.0                        # 1 px = 1 cm at 100 m (the top views here)

    def ray_at(self, x, y):
        return np.array((x, y, 100.0)), self.down

    def test_only_the_objects_under_the_cursor(self):
        o, d = self.ray_at(11.0, 0.5)
        self.assertEqual(self.index.near(o, d, self.slope), [self.boxes[1].id])
        o, d = self.ray_at(5.0, 0.5)                     # between the blocks: nothing
        self.assertEqual(self.index.near(o, d, self.slope), [])

    def test_the_same_snap_as_looking_at_everything(self):
        project = top_view_projection()
        mouse = (1203, -102)                             # 3 px / 2 px from the corner (12, 1) of the middle block
        o, d = self.ray_at(12.03, 1.02)
        everything = inf.find_snap(inf.SnapGeometry(self.boxes), mouse, project, o, d)
        near = inf.find_snap(self.index.geometry(o, d, self.slope), mouse, project, o, d)
        self.assertEqual((near.kind, near.obj_id), (everything.kind, everything.obj_id))
        self.assertTrue(np.allclose(near.point, everything.point))

    def test_without_perspective_the_reach_is_the_same_everywhere(self):
        o, d = self.ray_at(9.95, 0.5)                    # 5 cm left of the middle block
        self.assertEqual(self.index.near(o, d, 0.0, pixel=0.001), [])            # 1 px = 1 mm: too far
        self.assertEqual(self.index.near(o, d, 0.0, pixel=0.01), [self.boxes[1].id])   # 1 px = 1 cm: near

    def test_a_section_box_keeps_only_what_is_inside(self):
        o, d = self.ray_at(11.0, 0.5)
        box = [(np.array((1.0, 0, 0)), 10.5), (np.array((0, 0, -1.0)), -2.0)]   # x >= 10,5 and z <= 2
        geom = self.index.geometry(o, d, self.slope, keep=box)
        self.assertTrue(len(geom.points))
        self.assertTrue(all(p[0] >= 10.5 - 1e-9 and p[2] <= 2.0 + 1e-9 for p, k in zip(geom.points, geom.kinds)
                            if k == inf.ENDPOINT))

    def test_moved_removed_and_added_objects(self):
        moved = SketchObject("b1", translate(30.0, 0, 0), self.boxes[1].mesh.copy(), obj_id=self.boxes[1].id)
        self.index.update(moved)
        o, d = self.ray_at(11.0, 0.5)
        self.assertEqual(self.index.near(o, d, self.slope), [])
        o, d = self.ray_at(31.0, 0.5)
        self.assertEqual(self.index.near(o, d, self.slope), [moved.id])
        self.index.remove(moved.id)
        self.assertEqual(self.index.near(o, d, self.slope), [])
        self.index.update(moved)                         # back again
        self.assertEqual(self.index.near(o, d, self.slope), [moved.id])


class GuideLines(unittest.TestCase):
    def setUp(self):
        self.project = top_view_projection()

    def snap_at(self, geom, x, y):
        origin = np.array((x / 100.0, -y / 100.0, 100.0))
        return inf.find_snap(geom, (x, y), self.project, origin, np.array((0, 0, -1.0)))

    def test_guide_parallel_to_an_edge_at_a_distance(self):
        p, d = lines.guide_at_distance((0, 0, 0), (4, 0, 0), (1, 3, 0), 1.2)
        self.assertTrue(np.allclose(p, (0, 1.2, 0)) and np.allclose(np.abs(d), (1, 0, 0)))
        p, d = lines.guide_at_distance((0, 0, 0), (4, 0, 0), (1, -3, 0), 1.2)    # the other side
        self.assertTrue(np.allclose(p, (0, -1.2, 0)))
        self.assertIsNone(lines.guide_at_distance((0, 0, 0), (4, 0, 0), (2, 0, 0), 1.0))
        _p, _d, dist = lines.guide_through((0, 0, 0), (4, 0, 0), (1, 3, 0))
        self.assertAlmostEqual(dist, 3.0)

    def test_snap_on_guides_and_where_they_cross(self):
        geom = inf.SnapGeometry(guides=[((0, 2, 0), (1, 0, 0)), ((3, 0, 0), (0, 1, 0))])
        s = self.snap_at(geom, 303, -204)
        self.assertEqual(s.kind, inf.INTERSECTION)
        self.assertTrue(np.allclose(s.point, (3, 2, 0)))
        s = self.snap_at(geom, 500, -203)
        self.assertEqual(s.kind, inf.ON_GUIDE)
        self.assertTrue(np.allclose(s.point, (5, 2, 0)))
        self.assertIsNotNone(s.edge)

    def test_guide_crossing_an_edge(self):
        sheet = SketchObject("s", I4, sg.rectangle_mesh(4.0, 3.0))
        geom = inf.SnapGeometry([sheet], guides=[((1.5, 0, 0), (0, 1, 0))])
        s = self.snap_at(geom, 151, -302)
        self.assertEqual(s.kind, inf.INTERSECTION)
        self.assertTrue(np.allclose(s.point, (1.5, 3, 0)))
        s = self.snap_at(geom, 250, -302)                  # an edge of the model beats a guide
        self.assertEqual(s.kind, inf.ON_EDGE)

    def test_sketch_file_keeps_lines_and_guides(self):
        from arqbim.model.document import Guide, _read_sketches, _write_sketches
        import tempfile
        mesh = PolyMesh([(0, 0, 0), (2, 0, 0)], lines=[(0, 1)])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "x.arqbim")
            _write_sketches(path, [SketchObject("Linhas 1", I4, mesh)], [Guide((0, 1.2, 0), (1, 0, 0))])
            sketches, guides = _read_sketches(path)
        self.assertEqual(sketches[0].mesh.lines, [(0, 1)])
        self.assertTrue(np.allclose(guides[0].point, (0, 1.2, 0)))


class WallJoints(unittest.TestCase):
    AXES = [("A", (0, 0, 0), (5, 0, 0), 0.2)]

    def test_corner_at_a_wall_end(self):
        up = np.array((0.0, 1.0, 0.0))
        j = walls.find_joint((5, 0, 0), up, self.AXES)
        self.assertEqual(j[:2], ("A", "end"))
        r = walls.joint(((0, 0, 0), (5, 0, 0)), 0.2, "end", ((5, 0, 0), (5, 4, 0)), 0.15, "start")
        self.assertTrue(np.allclose(r["butt"][0], (5, 0.1, 0)))           # B starts at A's face
        self.assertTrue(np.allclose(r["through"][0], (5.075, 0, 0)))      # A runs through the corner
        self.assertEqual((r["butt"][1], r["through"][1]), (180.0, 0.0))   # square ends
        j = walls.find_joint((0, 0, 0), np.array((0.0, -1.0, 0.0)), self.AXES)
        self.assertEqual(j[:2], ("A", "start"))

    def test_t_junction_and_no_joint(self):
        up = np.array((0.0, 1.0, 0.0))
        j = walls.find_joint((2, 0, 0), up, self.AXES)
        self.assertEqual(j[:2], ("A", "mid"))
        r = walls.joint(((0, 0, 0), (5, 0, 0)), 0.2, "path", ((2, 0, 0), (2, 4, 0)), 0.15, "start")
        self.assertTrue(np.allclose(r["butt"][0], (2, 0.1, 0)) and r["through"] is None)
        self.assertIsNone(walls.joint(((0, 0, 0), (5, 0, 0)), 0.2, "path", ((7, 0, 0), (7, 4, 0)), 0.15, "start"))
        self.assertIsNone(walls.find_joint((5, 0, 0), np.array((1.0, 0.0, 0.0)), self.AXES))   # in line
        self.assertIsNone(walls.find_joint((5, 0, 3), up, self.AXES))                         # other level
        self.assertIsNone(walls.find_joint((7, 0, 0), up, self.AXES))                         # past the end

    def test_reference_line_puts_the_wall_on_one_side(self):
        a, b = walls.offset_axis((0, 0, 0), (10, 0, 0), "axis", 0.2)
        self.assertTrue(np.allclose(a, (0, 0, 0)) and np.allclose(b, (10, 0, 0)))
        a, b = walls.offset_axis((0, 0, 0), (10, 0, 0), "right", 0.2)     # drawn line = right face: wall on the left
        self.assertTrue(np.allclose(a, (0, 0.1, 0)) and np.allclose(b, (10, 0.1, 0)))
        a, b = walls.offset_axis((0, 0, 0), (10, 0, 0), "left", 0.2)
        self.assertTrue(np.allclose(a, (0, -0.1, 0)))

    def test_corner_of_walls_drawn_by_their_outside_face(self):
        # A along the outside face y = 0 (axis y = 0,10); B drawn separately up the outside face x = 6
        a_axis = walls.offset_axis((0, 0, 0), (6, 0, 0), "right", 0.2)
        b_start, b_end = walls.offset_axis((6, 0, 0), (6, 4, 0), "right", 0.2)   # axis x = 5,90
        up = np.array((0.0, 1.0, 0.0))
        j = walls.find_joint(b_start, up, [("A", *a_axis, 0.2)], 0.2)
        self.assertEqual(j[:2], ("A", "end"))
        r = walls.joint(a_axis, 0.2, "end", (b_start, b_end), 0.2, "start")
        self.assertTrue(np.allclose(r["butt"][0], (5.9, 0.2, 0)))           # B starts at A's inside face
        self.assertTrue(np.allclose(r["through"][0], a_axis[1]))            # A already ends at the outside corner

    def test_joint_follows_a_moved_wall(self):
        # B ends on A's end; A moved 1 m outwards (y -1): B must get 1 m longer, A keeps its length
        r = walls.joint(((0, -1, 0), (5, -1, 0)), 0.2, "end", ((5, 4, 0), (5, 0.1, 0)), 0.2, "end")
        self.assertTrue(np.allclose(r["butt"][0], (5, -0.9, 0)))
        self.assertTrue(np.allclose(r["through"][0], (5.1, -1, 0)))


class MitreAndCuts(unittest.TestCase):
    def test_mitre_of_a_120_degree_corner(self):
        # A comes along +x to c = (5, 0); B leaves at 60°: the cut is the bisector, 30° off square
        b_dir = np.array((np.cos(np.radians(60)), np.sin(np.radians(60)), 0.0))
        cut_a, cut_b = walls.mitre(np.array((5.0, 0, 0)), np.array((-1.0, 0, 0)), 0.2, b_dir, 0.2)
        self.assertAlmostEqual(walls.cut_angle(cut_a, np.array((1.0, 0, 0))), 30.0)
        self.assertAlmostEqual(walls.cut_angle(cut_b, b_dir), 150.0)
        self.assertTrue(np.allclose(cut_a, -cut_b))

    def test_too_sharp_corner_is_not_joined(self):
        sharp = np.array((np.cos(np.radians(170)), np.sin(np.radians(170)), 0.0))
        self.assertIsNone(walls.mitre(np.zeros(3), np.array((-1.0, 0, 0)), 0.2, sharp, 0.2))
        self.assertFalse(walls.can_join(np.array((1.0, 0, 0)), np.array((np.cos(0.1), np.sin(0.1), 0))))

    def test_cut_footprint_keeps_the_area(self):
        pts = walls.footprint(4.0, 0.2, 180.0 - 30.0, 30.0)
        x, y = np.array(pts).T
        area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
        self.assertAlmostEqual(area, 4.0 * 0.2)                       # axis length × thickness
        lo, hi = walls.clear_range(4.0, 0.2, 180.0 - 30.0, 30.0)
        self.assertAlmostEqual(lo, 0.1 * np.tan(np.radians(30)))
        self.assertAlmostEqual(hi, 4.0 - 0.1 * np.tan(np.radians(30)))

    def test_t_junction_at_45_degrees(self):
        d = np.array((np.cos(np.radians(45)), np.sin(np.radians(45)), 0.0))
        p, cut = walls.face_join(np.array((3.0, 0, 0)), d, True, (0, 0, 0), (8, 0, 0), 0.2)
        self.assertTrue(np.allclose(p, (3.1, 0.1, 0)))                # on the face y = 0,10
        self.assertTrue(np.allclose(cut, (0, -1, 0)))                 # cut along that face


class MoveAndRotate(unittest.TestCase):
    def test_series_of_copies_typed(self):
        self.assertEqual(parse_array("3x"), ("times", 3))
        self.assertEqual(parse_array("x4"), ("times", 4))
        self.assertEqual(parse_array("*2"), ("times", 2))
        self.assertEqual(parse_array("/3"), ("divide", 3))
        self.assertIsNone(parse_array("3"))
        self.assertIsNone(parse_array("3x4"))

    def test_copy_sketches(self):
        from arqbim.model import bim
        doc = Document()
        obj = SketchObject("A", I4, sg.rectangle_mesh(2, 1))
        doc.execute(AddObject(obj))
        new = bim.copy_objects(doc, [obj.id], [transform.translation((3 * k, 0, 0)) for k in (1, 2)], "Copiar")
        self.assertEqual(len(new), 2)
        self.assertEqual(sorted(round(doc.get(i).matrix[0, 3], 6) for i in new), [3.0, 6.0])
        self.assertTrue(np.allclose(doc.get(obj.id).matrix, I4))             # the original stays
        doc.undo()
        self.assertEqual(len(doc.objects), 1)

    def test_angles_typed_and_shown(self):
        self.assertEqual(parse_angle("90"), 90.0)
        self.assertEqual(parse_angle("-22,5"), -22.5)
        self.assertEqual(parse_angle("45°"), 45.0)
        self.assertIsNone(parse_angle("abc"))
        self.assertEqual(format_angle(45.0), "45,0°")

    def test_rotation_about_a_vertical_line(self):
        m = transform.rotation_about_z((1, 1, 0), 90)
        self.assertTrue(np.allclose(sg.transform_point(m, np.array((2.0, 1, 5))), (1, 2, 5)))
        self.assertAlmostEqual(transform.plan_angle((1, 0, 0), (0, 1, 0)), 90.0)
        self.assertAlmostEqual(transform.plan_angle((1, 0, 0), (0, -1, 0)), -90.0)
        self.assertEqual(transform.snap_angle(44.2), (45.0, True))
        self.assertEqual(transform.snap_angle(40.0), (40.0, False))

    def test_move_and_rotate_sketches_undo(self):
        from arqbim.model import bim
        doc = Document()
        obj = SketchObject("A", I4, sg.rectangle_mesh(2, 1))
        doc.execute(AddObject(obj))
        bim.transform_objects(doc, [obj.id], transform.translation((3, 0, 0)), "Mover")
        self.assertTrue(np.allclose(doc.get(obj.id).matrix[:3, 3], (3, 0, 0)))
        bim.transform_objects(doc, [obj.id], transform.rotation_about_z((3, 0, 0), 90), "Rodar")
        corner = sg.transform_point(doc.get(obj.id).matrix, np.array((2.0, 0, 0)))
        self.assertTrue(np.allclose(corner, (3, 2, 0)))
        doc.undo()
        doc.undo()
        self.assertTrue(np.allclose(doc.get(obj.id).matrix, I4))


class Texts(unittest.TestCase):
    def test_no_text_key_written_twice(self):
        """A key written twice in i18n.py silently replaces the first (a message would show the wrong text)."""
        import collections
        import re
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "arqbim", "i18n.py")
        with open(path, encoding="utf-8") as f:
            keys = re.findall(r'^    "([A-Za-z0-9_.]+)":', f.read(), re.M)
        self.assertEqual([k for k, n in collections.Counter(keys).items() if n > 1], [])


class Drawing2D(unittest.TestCase):
    """Plans and sections as 2D linework (Phase 3, step 4)."""

    @staticmethod
    def cube(size=1.0):
        v = np.array([(i * size, j * size, k * size) for i in (0, 1) for j in (0, 1) for k in (0, 1)], float)
        quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        return v, [t for a, b, c, d in quads for t in ((a, b, c), (a, c, d))]

    @staticmethod
    def area(ring):
        x, y = ring[:, 0], ring[:, 1]
        return abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2

    def test_clip_an_outline_to_a_layer(self):
        from arqbim.core import drawing2d
        # a wall's cut 5 m × 0,20 m with a notch, split into plaster | block | plaster across y
        ring = np.array([(0, -0.1, 1), (5, -0.1, 1), (5, 0.1, 1), (3, 0.1, 1), (3, 0.0, 1), (2, 0.0, 1),
                         (2, 0.1, 1), (0, 0.1, 1)], float)
        n = np.array((0.0, 1.0, 0.0))
        parts = [drawing2d.clip_between(ring, n, a, b) for a, b in ((-0.1, -0.08), (-0.08, 0.08), (0.08, 0.1))]
        areas = [self.area(p[:, :2]) for p in parts]
        self.assertTrue(np.allclose(areas, (5 * 0.02, 5 * 0.08 + 4 * 0.08, 4 * 0.02)), areas)   # the notch left out
        self.assertIsNone(drawing2d.clip_between(ring, n, 0.2, 0.3))                         # beyond the wall

    def test_a_cube_cut_at_half_height_is_a_square(self):
        from arqbim.core import drawing2d
        v, tris = self.cube(2.0)
        segs = drawing2d.cut_segments(v, tris, (0.0, 0.0, -1.0), -1.0)      # keep z <= 1
        rings = drawing2d.loops(segs)
        self.assertEqual(len(rings), 1)
        flat = drawing2d.flatten(rings[0], (0, 0, 0), (1, 0, 0), (0, 1, 0))
        self.assertAlmostEqual(self.area(flat), 4.0)
        self.assertTrue(np.allclose(rings[0][:, 2], 1.0))

    def test_a_cut_through_nothing_and_open_meshes(self):
        from arqbim.core import drawing2d
        v, tris = self.cube()
        self.assertEqual(len(drawing2d.cut_segments(v, tris, (0.0, 0.0, -1.0), -5.0)), 0)   # cut above the cube
        segs = drawing2d.cut_segments(v, tris[:4] + tris[8:], (0.0, 0.0, -1.0), -0.5)     # two sides missing
        self.assertEqual(drawing2d.loops(segs), [])

    def test_hidden_lines_are_left_out(self):
        from arqbim.core import drawing2d
        near_v, tris = self.cube(1.0)                              # x, y, z in 0..1
        far_v = near_v * (2.0, 1.0, 2.0) + (0.0, 2.0, 0.0)         # x 0..2, y 2..3, z 0..2: behind, bigger
        triangles = np.concatenate([near_v[tris], far_v[tris]])
        # the bottom front edge of the far box, seen from the front (looking along +y)
        edge = np.array([[(0.0, 2.0, 0.0), (2.0, 2.0, 0.0)]])
        lines = drawing2d.hidden_lines_removed(triangles, edge, (0.0, 1.0, 0.0), -10.0, (0, 0, 0),
                                               (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        seen = sum(np.linalg.norm(b - a) for a, b in lines)
        self.assertAlmostEqual(seen, 1.0, delta=0.01)               # x 0..1 is behind the near box
        self.assertTrue(all(min(a[0], b[0]) >= 0.99 for a, b in lines))
        # the same edge with the near box cut away (a section between the two boxes): all of it
        lines = drawing2d.hidden_lines_removed(triangles, edge, (0.0, 1.0, 0.0), 1.5, (0, 0, 0),
                                               (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        self.assertAlmostEqual(sum(np.linalg.norm(b - a) for a, b in lines), 2.0, delta=0.01)

    def test_edges_beyond_the_cut_are_kept_and_shortened(self):
        from arqbim.core import drawing2d
        a = np.array([(0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 3.0)])
        b = np.array([(1.0, 0.0, 0.0), (0.0, 0.0, 3.0), (1.0, 0.0, 3.0)])
        kept = drawing2d.kept_edges(a, b, (0.0, 0.0, -1.0), -1.2)                         # plan cut at 1.20 m
        self.assertEqual(len(kept), 2)                                                    # the top edge is gone
        self.assertAlmostEqual(kept[1][:, 2].max(), 1.2)                                  # the post stops at the cut


class CropRegion(unittest.TestCase):
    """0.65: what a plan's crop region keeps of outlines and lines (core/drawing2d.py)."""

    def test_clip_ring_and_segments(self):
        from arqbim.core import drawing2d
        rect = (0.0, 0.0, 2.0, 1.0)
        ring = drawing2d.clip_ring_to_rect(np.array([(-1.0, 0.5), (3.0, 0.5), (3.0, 0.7), (-1.0, 0.7)]), rect)
        self.assertAlmostEqual(abs(Drawing2DArea(ring)), 2.0 * 0.2)              # the wall's part inside
        self.assertIsNone(drawing2d.clip_ring_to_rect(np.array([(5.0, 5.0), (6.0, 5.0), (6.0, 6.0)]), rect))
        segs = drawing2d.clip_segments_to_rect(np.array([[(-1.0, 0.5), (3.0, 0.5)], [(5.0, 5.0), (6.0, 6.0)],
                                                         [(1.0, 0.2), (1.5, 0.8)]]), rect)
        np.testing.assert_allclose(segs, [[(0, 0.5), (2, 0.5)], [(1.0, 0.2), (1.5, 0.8)]], atol=1e-12)


def Drawing2DArea(ring):
    x, y = np.asarray(ring)[:, 0], np.asarray(ring)[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def _prism(outline, length):
    """A closed TriMesh: the polygon `outline` (y, z) swept `length` along X (end caps as fans)."""
    n = len(outline)
    verts = [(0.0, y, z) for y, z in outline] + [(length, y, z) for y, z in outline]
    tris = []
    for i in range(n):
        j = (i + 1) % n
        tris += [(i, j, n + j), (i, n + j, n + i)]
    tris += [(0, k + 1, k) for k in range(1, n - 1)] + [(n, n + k, n + k + 1) for k in range(1, n - 1)]
    return TriMesh(np.array(verts), np.array(tris))


class RegionSelect(unittest.TestCase):
    """0.75: what a box, a lasso, a polygon or a fence takes on the screen (core/region_select.py)."""

    def test_window_crossing_and_fence(self):
        from arqbim.core import region_select as rs
        box = [(0, 0), (100, 0), (100, 100), (0, 100)]
        square = np.array([(10, 10), (30, 10), (30, 30), (10, 30)], float)
        tris = [(0, 1, 2), (0, 2, 3)]
        self.assertTrue(rs.takes(square, box, rs.WINDOW, tris))
        half_out = square + (80, 0)                                   # from x 90 to 110
        self.assertFalse(rs.takes(half_out, box, rs.WINDOW, tris))
        self.assertTrue(rs.takes(half_out, box, rs.CROSSING, tris))
        big = np.array([(-50, -50), (150, -50), (150, 150), (-50, 150)], float)
        self.assertTrue(rs.takes(big, box, rs.CROSSING, tris))        # the box inside one face: it touches
        self.assertFalse(rs.takes(big, box, rs.WINDOW, tris))
        far = square + (300, 0)
        self.assertFalse(rs.takes(far, box, rs.CROSSING, tris))
        line = np.array([(-10, 50), (110, 50)], float)                # a sketch line right across the box
        self.assertTrue(rs.takes(line, box, rs.CROSSING, segs=[(0, 1)]))
        self.assertFalse(rs.takes(line, box, rs.WINDOW, segs=[(0, 1)]))
        behind = np.array([(10, 10), (np.nan, np.nan)], float)
        self.assertFalse(rs.takes(behind, box, rs.WINDOW, segs=[(0, 1)]))
        fence = [(20, -10), (20, 200)]                                # a fence through the square
        self.assertTrue(rs.takes(square, fence, rs.FENCE, tris))
        self.assertFalse(rs.takes(far, fence, rs.FENCE, tris))
        lasso = [(0, 0), (50, 60), (100, 0), (100, 100), (0, 100)]    # a V notch at the bottom
        self.assertFalse(rs.points_in_polygon([(50, 20)], lasso)[0])
        self.assertTrue(rs.points_in_polygon([(50, 80)], lasso)[0])
        self.assertEqual(rs.mode_of([(50, 50), (60, 40)]), rs.WINDOW)
        self.assertEqual(rs.mode_of([(50, 50), (40, 70)]), rs.CROSSING)
        self.assertEqual(len(rs.thin_path([(0, 0), (1, 0), (2, 0), (10, 0), (11, 0)])), 3)


class WalkCollision(unittest.TestCase):
    """0.83: walking stops in front of a wall (BODY_RADIUS before it), goes through a door, is stopped by a low
    table (the waist ray), and finds the objects near the step by their boxes (SnapIndex.along)."""

    @staticmethod
    def _element(lo, hi, ifc_class="IfcWall", obj_id=1):
        from types import SimpleNamespace
        v = np.array([(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])], float)
        quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        tris = [t for a, b, c, d in quads for t in ((a, b, c), (a, c, d))]
        return SimpleNamespace(id=obj_id, mesh=TriMesh(v, tris), matrix=np.eye(4), is_bim=True, ifc_class=ifc_class)

    def test_stops_before_a_wall_not_a_door(self):
        from arqbim.core import collide
        eye, ahead = np.array((0.0, 0.0, 1.6)), np.array((1.0, 0.0, 0.0))
        wall = self._element((2.0, -5.0, 0.0), (2.2, 5.0, 3.0))
        self.assertAlmostEqual(collide.free_step(eye, ahead, 5.0, [wall]), 2.0 - collide.BODY_RADIUS)
        self.assertAlmostEqual(collide.free_step(eye, ahead, 1.0, [wall]), 1.0)          # not reached yet
        self.assertAlmostEqual(collide.free_step(eye, -ahead, 5.0, [wall]), 5.0)         # walking away
        door = self._element((2.0, -0.5, 0.0), (2.1, 0.5, 2.1), "IfcDoor")
        self.assertAlmostEqual(collide.free_step(eye, ahead, 5.0, [door]), 5.0)
        table = self._element((1.0, -1.0, 0.0), (2.0, 1.0, 0.75), "IfcFurniture")
        self.assertAlmostEqual(collide.free_step(eye, ahead, 5.0, [table]), 1.0 - collide.BODY_RADIUS)

    def test_boxes_near_the_step(self):
        index = inf.SnapIndex()
        index.update(self._element((2.0, -5.0, 0.0), (2.2, 5.0, 3.0), obj_id="wall"))
        index.update(self._element((0.0, 8.0, 0.0), (1.0, 9.0, 3.0), obj_id="aside"))
        index.update(self._element((-3.0, -0.2, 0.0), (-2.8, 0.2, 3.0), obj_id="behind"))
        found = index.along((0.0, 0.0, 1.6), (1.0, 0.0, 0.0), 3.0, 0.25)
        self.assertEqual(found, ["wall"])
        self.assertEqual(index.along((0.0, 0.0, 1.6), (1.0, 0.0, 0.0), 1.0, 0.25), [])      # too far for this step


class NeighbourColumns(unittest.TestCase):
    """0.94: the columns next to each other in a line along X or Y (5 cm tolerance), only neighbours."""

    def test_pairs(self):
        from arqbim.core.structure import neighbour_pairs
        pts = {"a": (0.0, 0.0), "b": (5.0, 0.02), "c": (10.0, 0.0), "d": (0.0, 6.0), "e": (5.0, 6.0), "f": (7.0, 3.0)}
        pairs = neighbour_pairs(pts)
        self.assertEqual(sorted(tuple(sorted(p)) for p in pairs),
                         [("a", "b"), ("a", "d"), ("b", "c"), ("b", "e"), ("d", "e")])     # f: in no line


class Bays(unittest.TestCase):
    """0.96: the closed bays of columns joined by beams: two in a 3 × 2 frame, none in an open one."""

    def test_bays(self):
        from arqbim.core.structure import bays
        pts = {"a": (0, 0), "b": (5, 0), "c": (10, 0), "d": (0, 6), "e": (5, 6), "f": (10, 6)}
        edges = [("a", "b"), ("b", "c"), ("d", "e"), ("e", "f"), ("a", "d"), ("b", "e"), ("c", "f")]
        found = sorted(sorted(ring) for ring in bays(pts, edges))
        self.assertEqual(found, [[0, 2, 4, 5], [1, 3, 5, 6]])
        self.assertEqual(bays(pts, edges[:4]), [])                    # no closed bay


class ProposalNodes(unittest.TestCase):
    """0.98: the columns of a structure proposed from walls — a 12 × 8 m room with a wall across it: its 4
    corners, the 2 T junctions, one more in the middle of each 8 m wall (6 m at most between them); with 5 m at
    most, one more in each 6 m half too."""

    def test_room_with_a_wall_across(self):
        from arqbim.core.structure import proposal_nodes
        t = 0.2
        walls = [((0, 0), (12, 0), t), ((12, 0), (12, 8), t), ((12, 8), (0, 8), t), ((0, 8), (0, 0), t),
                 ((6, 0), (6, 8), t)]                                  # (across: from wall to wall)
        nodes, along = proposal_nodes(walls, max_span=6.0)
        rounded = sorted((round(x, 6), round(y, 6)) for x, y in nodes)
        self.assertEqual(rounded, [(0, 0), (0, 4), (0, 8), (6, 0), (6, 4), (6, 8), (12, 0), (12, 4), (12, 8)])
        self.assertEqual([len(seq) for seq in along], [3, 3, 3, 3, 3])
        bottom = [tuple(round(c, 6) for c in nodes[k]) for k in along[0]]
        self.assertEqual(bottom, [(0, 0), (6, 0), (12, 0)])
        nodes, along = proposal_nodes(walls, max_span=5.0)
        self.assertEqual([len(seq) for seq in along], [5, 3, 5, 3, 3])          # (3 m apart along the 12 m walls)


class RoomRegion(unittest.TestCase):
    """0.99: the room a click finds between walls — two rooms in a 10 × 6 m house with a wall across (with a
    column inside one: a hole), a hair's gap closed, the outside is not a room."""

    def test_rooms(self):
        from arqbim.core import rooms

        def wall(a, b, t=0.2):
            (x0, y0), (x1, y1) = a, b
            if y0 == y1:
                return [(min(x0, x1) - t / 2, y0 - t / 2), (max(x0, x1) + t / 2, y0 - t / 2),
                        (max(x0, x1) + t / 2, y0 + t / 2), (min(x0, x1) - t / 2, y0 + t / 2)]
            return [(x0 - t / 2, min(y0, y1) - t / 2), (x0 + t / 2, min(y0, y1) - t / 2),
                    (x0 + t / 2, max(y0, y1) + t / 2), (x0 - t / 2, max(y0, y1) + t / 2)]

        walls = [wall((0, 0), (10, 0)), wall((10, 0), (10, 6)), wall((10, 6), (0, 6)), wall((0, 6), (0, 0)),
                 wall((4, 0), (4, 5.99))]                          # (1 cm short of the top wall: still closed)
        column = [(7.0, 2.0), (7.3, 2.0), (7.3, 2.3), (7.0, 2.3)]
        left = rooms.region(walls + [column], (2.0, 3.0))
        right = rooms.region(walls + [column], (8.0, 3.0))
        self.assertAlmostEqual(left.area, 3.8 * 5.8, places=4)          # (0,10 .. 3,90 × 0,10 .. 5,90)
        self.assertAlmostEqual(right.area, 5.8 * 5.8 - 0.09, places=4)   # (less the column)
        self.assertEqual(len(right.interiors), 1)
        self.assertIsNone(rooms.region(walls, (12.0, 3.0)))               # outside: not a room
        self.assertIsNone(rooms.region(walls, (0.0, 3.0)))                # inside a wall
        out, holes = rooms.outline(right)
        self.assertEqual((len(out), len(holes)), (4, 1))


class SlabOutlines(unittest.TestCase):
    """0.100: a slab's outline — an L clicked corner by corner, sides that cross or too few corners refused; the
    magic wand in a 10 × 6 m house: to the walls' inner faces (a column inside: a hole), or to their outer faces
    (under the walls, no hole); outside the walls: none."""

    def test_outlines_and_wand(self):
        from arqbim.core import slabs

        el = slabs.outline_polygon([(0, 0), (6, 0), (6, 3), (3, 3), (3, 5), (0, 5), (0, 0)])   # (closed twice)
        self.assertAlmostEqual(el.area, 6 * 3 + 3 * 2)
        self.assertIsNone(slabs.outline_polygon([(0, 0), (4, 4), (4, 0), (0, 4)]))           # its sides cross
        self.assertIsNone(slabs.outline_polygon([(0, 0), (4, 0)]))
        self.assertIsNone(slabs.outline_polygon([(0, 0), (0.05, 0), (0.05, 0.05)]))          # too small
        self.assertEqual(len(slabs.circle_ring((1, 1), 2)), slabs.CIRCLE_SIDES)
        self.assertAlmostEqual(slabs.ring_area([(0, 0), (2, 0), (2, 1), (0, 1)]), 2.0)

        def wall(a, b, t=0.2):
            (x0, y0), (x1, y1) = a, b
            if y0 == y1:
                return [(min(x0, x1) - t / 2, y0 - t / 2), (max(x0, x1) + t / 2, y0 - t / 2),
                        (max(x0, x1) + t / 2, y0 + t / 2), (min(x0, x1) - t / 2, y0 + t / 2)]
            return [(x0 - t / 2, min(y0, y1) - t / 2), (x0 + t / 2, min(y0, y1) - t / 2),
                    (x0 + t / 2, max(y0, y1) + t / 2), (x0 - t / 2, max(y0, y1) + t / 2)]

        walls = [wall((0, 0), (10, 0)), wall((10, 0), (10, 6)), wall((10, 6), (0, 6)), wall((0, 6), (0, 0))]
        column = [(7.0, 2.0), (7.3, 2.0), (7.3, 2.3), (7.0, 2.3)]
        inner = slabs.wand(walls + [column], (2.0, 3.0))
        self.assertAlmostEqual(inner.area, 9.8 * 5.8 - 0.09, places=4)
        self.assertEqual(len(inner.interiors), 1)
        outer = slabs.wand(walls + [column], (2.0, 3.0), "exterior")
        self.assertAlmostEqual(outer.area, 10.2 * 6.2, places=3)                # out to the outer faces
        self.assertEqual(len(outer.interiors), 0)
        self.assertIsNone(slabs.wand(walls, (12.0, 3.0)))
        # a wall across: the left room's slab out to the outer faces goes over the wall across, not beyond it
        across = slabs.wand(walls + [wall((4, 0), (4, 6))], (2.0, 3.0), "exterior")
        x0, y0, x1, y1 = across.bounds
        self.assertAlmostEqual(x0, -0.1, places=4)
        self.assertAlmostEqual(x1, 4.1, places=4)
        self.assertAlmostEqual(y1 - y0, 6.2, places=4)
        # (0.179) an L of walls not joined (each ending at its axis' corner, a gap left at the corners): out to the
        # outer faces, a clean L — the little step at its inner corner gone
        def bare(a, b, t=0.2):
            (x0, y0), (x1, y1) = a, b
            if y0 == y1:
                return [(min(x0, x1), y0 - t / 2), (max(x0, x1), y0 - t / 2), (max(x0, x1), y0 + t / 2),
                        (min(x0, x1), y0 + t / 2)]
            return [(x0 - t / 2, min(y0, y1)), (x0 + t / 2, min(y0, y1)), (x0 + t / 2, max(y0, y1)),
                    (x0 - t / 2, max(y0, y1))]

        corners = [(0, 0), (8, 0), (8, 4), (4, 4), (4, 8), (0, 8)]
        el_walls = [bare(corners[k], corners[(k + 1) % 6]) for k in range(6)]
        el = slabs.wand(el_walls, (2.0, 2.0), "exterior")
        self.assertEqual(len(el.exterior.coords) - 1, 6)
        self.assertAlmostEqual(el.area, 8.2 * 4.2 + 4.2 * 4.0, places=4)
        self.assertEqual(slabs._drop_steps([(0, 0), (5, 0), (5, 3), (5.1, 3), (5.1, 3.1), (5, 3.1), (5, 6), (0, 6)]),
                         [(0, 0), (5, 0), (5, 3), (5.1, 3), (5.1, 3.1), (5, 3.1), (5, 6), (0, 6)])   # (a real jog)
        self.assertEqual(len(slabs._drop_steps([(0, 0), (5, 0), (5, 3.1), (5.1, 3.1), (5.1, 3.2), (0, 3.2)])), 4)


class RoofFaces(unittest.TestCase):
    """0.111: a 10 × 6 m outline's roof slopes — hip: two trapezoids and two triangles (60 m² in all), the ridge
    3 m in from the long sides; gable: two halves; shed: one; an L not with one slope; the sides grown by the
    overhang keep which slope; (0.179) an L hipped: its slopes fill it, each one's plane its height there (the higher
    arm's roof), turned too; (0.246) an L gabled: two slopes over each arm, a gable at each arm's end."""

    def test_roof_faces(self):
        from shapely.geometry import Polygon
        from arqbim.core import roofs
        rect = [(0, 0), (10, 0), (10, 6), (0, 6)]
        hip = roofs.faces(rect, roofs.sloping_sides(rect, "hip"))
        areas = sorted(round(Polygon(p).area, 6) for _k, p in hip)
        self.assertEqual(areas, [9.0, 9.0, 21.0, 21.0])
        t = math.tan(math.radians(30))
        self.assertAlmostEqual(roofs.height_at(rect, [True] * 4, 30, 2.8, (5.0, 3.0)), 2.8 + 3 * t)
        self.assertAlmostEqual(roofs.height_at(rect, [True] * 4, 30, 2.8, (1.0, 3.0)), 2.8 + 1 * t)   # (the hip end)
        gable = roofs.sloping_sides(rect, "gable")
        self.assertEqual(gable, [True, False, True, False])
        self.assertEqual(sorted(round(Polygon(p).area, 6) for _k, p in roofs.faces(rect, gable)), [30.0, 30.0])
        shed = roofs.faces(rect, roofs.sloping_sides(rect, "shed"))
        self.assertEqual(len(shed), 1)
        self.assertAlmostEqual(roofs.height_at(rect, roofs.sloping_sides(rect, "shed"), 30, 0.0, (5, 6)), 6 * t)
        el = [(0, 0), (6, 0), (6, 3), (3, 3), (3, 5), (0, 5)]
        self.assertIsNone(roofs.faces(el, roofs.sloping_sides(el, "shed")))
        self.assertEqual(len(roofs.faces(el, [False] * 6)), 1)
        # (0.246) two slopes over each arm of the L: they fill it, each one's plane its height there; a gable at
        # each arm's end (full height at the wall's line, where a hip roof is at its eave)
        two = roofs.sloping_sides(el, "gable")
        gable_el = roofs.faces(el, two)
        self.assertAlmostEqual(sum(Polygon(p).area for _plane, p in gable_el), 24.0, places=6)
        for (a, _e, n), p in gable_el:
            q = Polygon(p).representative_point()
            here = ((q.x - a[0]) * n[0] + (q.y - a[1]) * n[1]) * t
            self.assertAlmostEqual(here, roofs.height_at(el, two, 30, 0.0, (q.x, q.y)), places=6)
        self.assertAlmostEqual(roofs.height_at(el, two, 30, 0.0, (6.0, 1.5)), 1.5 * t)          # (a gable end)
        self.assertAlmostEqual(roofs.height_at(el, two, 30, 0.0, (1.5, 5.0)), 1.5 * t)
        self.assertAlmostEqual(roofs.height_at(el, [True] * 6, 30, 0.0, (6.0, 1.5)), 0.0)       # (hipped: its eave)
        # (0.179) a hip roof over the L: its slopes fill it (24 m²), each one's plane the roof's height there —
        # the highest of its two arms' roofs: the ridges 1,50 m up the slope's run, the valley from the inner corner
        hip_el = roofs.faces(el, [True] * 6)
        self.assertAlmostEqual(sum(Polygon(p).area for _plane, p in hip_el), 24.0, places=6)
        for (a, _e, n), p in hip_el:
            q = Polygon(p).representative_point()
            here = ((q.x - a[0]) * n[0] + (q.y - a[1]) * n[1]) * t
            self.assertAlmostEqual(here, roofs.height_at(el, [True] * 6, 30, 0.0, (q.x, q.y)), places=6)
        self.assertAlmostEqual(roofs.height_at(el, [True] * 6, 30, 0.0, (4.5, 1.5)), 1.5 * t)     # (a ridge)
        self.assertAlmostEqual(roofs.height_at(el, [True] * 6, 30, 0.0, (1.5, 4.0)), 1.0 * t)     # (a hip end)
        self.assertEqual(len(roofs.max_rectangles(el)), 2)
        self.assertTrue(roofs.can_slope(Polygon(el), "hip") and roofs.can_slope(Polygon(el), "gable"))   # (0.246)
        self.assertFalse(roofs.can_slope(Polygon(el), "shed"))
        turned = [(x * math.cos(0.5) - y * math.sin(0.5), x * math.sin(0.5) + y * math.cos(0.5)) for x, y in el]
        self.assertAlmostEqual(sum(Polygon(p).area for _plane, p in roofs.faces(turned, [True] * 6)), 24.0, places=6)
        big = roofs.grown(rect, 0.5)
        self.assertAlmostEqual(Polygon(big).area, 11 * 7)
        self.assertEqual(sum(roofs.carried_over(rect, gable, big)), 2)


class ExtrudedRoofs(unittest.TestCase):
    """0.180: a rectangle's frame (the profile across its 6 m span, run along its 10 m); a barrel roof springing from
    the walls at 30° (its radius the span, its rise 1,34 m over 10 m); a butterfly at 10° (its valley 0,88 m down in
    the middle); grown by eaves: the arc carries on; an L refused for both."""

    def test_extruded(self):
        from shapely.geometry import Polygon
        from arqbim.core import roofs
        a, e, n, length, span = roofs.rect_frame([(0, 0), (10, 0), (10, 6), (0, 6)])
        self.assertEqual((length, span), (10.0, 6.0))
        self.assertEqual((tuple(e), tuple(n)), ((1.0, 0.0), (-0.0, 1.0)))
        radius, below = roofs.arch(10.0, 30.0)
        self.assertAlmostEqual(radius, 10.0, places=9)
        self.assertAlmostEqual(roofs.profile_z("barrel", 10.0, 0.0, 30.0, 5.0), 10.0 - below, places=9)
        self.assertAlmostEqual(roofs.profile_z("barrel", 10.0, 0.0, 30.0, 0.0), 0.0, places=9)    # (on the walls)
        self.assertAlmostEqual(roofs.profile_z("barrel", 10.0, 0.0, 30.0, 5.0, 0.2), 9.8 - below, places=9)
        self.assertLess(roofs.profile_z("barrel", 10.0, 0.5, 30.0, 0.0), 0.0)                    # (the eave lower)
        t = math.tan(math.radians(10))
        self.assertAlmostEqual(roofs.profile_z("butterfly", 10.0, 0.0, 10.0, 5.0), -5 * t, places=9)
        self.assertAlmostEqual(roofs.profile_z("butterfly", 10.0, 0.5, 10.0, 0.0), 0.5 * t, places=9)
        self.assertAlmostEqual(roofs.extruded_height_at([(0, 0), (10, 0), (10, 6), (0, 6)], "butterfly", 0.0, 10.0,
                                                        3.0, (4.0, 3.0)), 3.0 - 3 * t, places=9)
        el = Polygon([(0, 0), (6, 0), (6, 3), (3, 3), (3, 5), (0, 5)])
        self.assertFalse(roofs.can_slope(el, "barrel") or roofs.can_slope(el, "butterfly"))
        self.assertTrue(roofs.can_slope(Polygon([(0, 0), (10, 0), (10, 6), (0, 6)]), "barrel"))


class Arcs(unittest.TestCase):
    """0.103: an arc through three points (both ways round), one by its radius bulging to a side, a curved wall's
    band (a circle: two halves), its axis radius from the face drawn."""

    def test_arcs(self):
        from arqbim.core import arcs
        c, r, start, sweep = arcs.arc_through((5, 0), (0, 5), (5 / math.sqrt(2), 5 / math.sqrt(2)))
        self.assertTrue(np.allclose(c, (0, 0)) and abs(r - 5) < 1e-9)
        self.assertAlmostEqual(start, 0.0)
        self.assertAlmostEqual(sweep, math.pi / 2)                              # counter-clockwise, a quarter
        _c, _r, _s, sweep = arcs.arc_through((5, 0), (0, 5), (-5, 0))           # the long way round, clockwise
        self.assertAlmostEqual(sweep, -1.5 * math.pi)
        self.assertIsNone(arcs.arc_through((0, 0), (1, 0), (2, 0)))
        c, r, _s, sweep = arcs.arc_with_radius((0, 0), (6, 0), 5.0, (3, 1))     # bulging up (left of a -> b)
        self.assertAlmostEqual(r, 5.0)
        self.assertTrue(np.allclose(c, (3, -4)))
        self.assertLess(sweep, 0)                                                # (up from (0,0) to (6,0): clockwise)
        self.assertIsNone(arcs.arc_with_radius((0, 0), (6, 0), 2.0, (3, 1)))     # shorter than half the chord
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
        quarter = Polygon(arcs.band((0, 0), 5.0, 0.0, math.pi / 2, 0.2)[0])
        self.assertAlmostEqual(quarter.area, math.pi / 4 * (5.1 ** 2 - 4.9 ** 2), places=2)
        ring = unary_union([Polygon(p) for p in arcs.band((0, 0), 5.0, 0.0, arcs.FULL, 0.2)])
        self.assertEqual(len(arcs.band((0, 0), 5.0, 0.0, arcs.FULL, 0.2)), 2)
        self.assertAlmostEqual(ring.area, math.pi * (5.1 ** 2 - 4.9 ** 2), places=1)
        self.assertAlmostEqual(arcs.axis_radius(5.0, math.pi, "left", 0.2), 5.1)     # its left face: inside
        self.assertAlmostEqual(arcs.axis_radius(5.0, math.pi, "right", 0.2), 4.9)
        self.assertAlmostEqual(arcs.axis_radius(5.0, -math.pi, "left", 0.2), 4.9)    # clockwise: the other way


class PlacementKeys(unittest.TestCase):
    """0.86: the nine insertion points and the quarter turns of a section placed by a point."""

    def test_insertion_and_turns(self):
        from arqbim.core import placement as pl
        centre, x, corners = pl.place_box((0.0, 0.0, 0.0), 0.4, 0.2)
        self.assertTrue(np.allclose(centre, 0.0) and np.allclose(x, (1, 0, 0)))
        self.assertTrue(np.allclose(corners[0], (-0.2, -0.1, 0.0)))
        centre, _x, corners = pl.place_box((0.0, 0.0, 0.0), 0.4, 0.2, 0, 1)     # its bottom left corner on the point
        self.assertTrue(np.allclose(centre, (0.2, 0.1, 0.0)) and np.allclose(corners[0], 0.0))
        centre, x, corners = pl.place_box((1.0, 1.0, 0.0), 0.4, 0.2, 90, 1)     # turned 90°: its x along green
        self.assertTrue(np.allclose(x, (0, 1, 0), atol=1e-12) and np.allclose(corners[0], (1.0, 1.0, 0.0)))
        self.assertTrue(np.allclose(centre, (0.9, 1.2, 0.0)))
        self.assertEqual([pl.turn(0, 1), pl.turn(0, -1), pl.turn(270, 1)], [90, 270, 0])
        self.assertEqual([pl.next_insertion(8, 1), pl.next_insertion(0, -1)], [0, 8])


class Disciplines(unittest.TestCase):
    """0.182 (the environments of 0.84 before): every tool is in some discipline's ribbon (the navigation ones in
    the status bar); every other name is one of the window's actions (act_<name>) or a dropdown; every action the
    menus had is in some discipline; Select first in the drawing disciplines; Ctrl+1…9; the old environments map
    onto disciplines; a long name in two lines under its icon. (0.298) The disciplines in the order of the work; each
    one's tools in named panels — no name twice in a discipline, columns of at most three small buttons —; the tab
    Modify | Walls with every wall modifier; a small button's name in one line."""

    def test_every_tool_somewhere(self):
        import re
        from arqbim import i18n
        from arqbim.tools import ALL_TOOLS
        from arqbim.ui import ribbon
        navigation = {"orbit", "pan", "zoom", "zoom_window", "position_camera", "look_around", "walk"}
        tools = {cls.name for cls in ALL_TOOLS}
        tabs = list(ribbon.DISCIPLINES) + ["ctx:" + k for k in ribbon.CONTEXTS]
        placed = {name for d in tabs for name in ribbon.items_of(d)}
        self.assertEqual(tools - navigation - placed, set())
        with open(os.path.join(os.path.dirname(__file__), "..", "arqbim", "ui", "main_window.py"),
                  encoding="utf-8") as f:
            source = f.read()
        acts = set(re.findall(r"self\.act_(\w+) = self\._action\(", source))
        self.assertEqual(placed - tools - acts - set(ribbon.MENUS), set())
        # (what is left out: the edit, selection and navigation actions — the header, the contextual bar, the
        # status bar have them)
        elsewhere = {"undo", "redo", "delete_guides", "select_all", "select_invert", "select_none", "drag_box",
                     "drag_lasso", "drag_elements", "pick_polygon", "pick_fence", "same_type", "filter_selection",
                     "select_by",
                     "selectable",
                     "zoom_all", "zoom_selection", "view_back", "view_forward", "tool_type",
                     # (0.402: a dimension string's — on the contextual bar and its right button, as Revit's)
                     "dim_eq", "dim_text", "dim_add", "dim_witness", "dim_text_back",
                     # (0.446: how drawing looks — in the header's theme menu)
                     "draw_revit", "draw_addon",
                     # (0.450: the wall's shapes — on the contextual bar, as Revit's «Draw» panel, and on W + letter)
                     "wall_rect", "wall_circle", "wall_arc", "wall_face", "wall_wand"}
        self.assertEqual(acts - placed - elsewhere, set())
        for d in ("modeling", "architecture", "structure", "services", "terrain", "annotate", "massing"):
            self.assertEqual(ribbon.items_of(d)[0], "select")
        self.assertEqual(ribbon.DISCIPLINES, ("home", "modeling", "manage", "massing", "terrain", "architecture",
                                              "structure", "services", "collaborate", "annotate", "view", "render"))
        self.assertEqual(sorted(ribbon.SHORTCUTS.values()), ["Ctrl+{}".format(k) for k in range(1, 10)])
        self.assertEqual(ribbon.SHORTCUTS["architecture"], "Ctrl+5")
        self.assertEqual(ribbon.OLD["concept"], "massing")
        self.assertTrue(set(ribbon.OLD.values()) <= set(ribbon.DISCIPLINES))
        for tab in tabs:
            names = ribbon.items_of(tab)
            self.assertEqual(len(names), len(set(names)), tab)
            for key, items in ribbon.panels_of(tab):
                self.assertTrue(i18n.has("rpanel." + key), key)
                for item in items:
                    self.assertTrue(isinstance(item, str) or 1 <= len(item) <= 3, (tab, key, item))
        walls = set(ribbon.items_of("ctx:walls"))
        self.assertTrue({"merge_walls", "orthogonalize", "unjoin_walls", "attach_top", "detach_top", "edit_profile",
                         "reset_profile", "split_wall", "corner_walls", "align", "offset", "mirror", "move",
                         "wall_finish", "dimension_walls", "flip_walls", "join_wall_ends", "split_gap", "trim_extend",
                         "wall_joins", "attach_base", "detach_base", "wall_opening", "wall_sweep",
                         "wall_reveal"} <= walls)
        self.assertEqual(ribbon.short_label("Revestimento de parede"), "Revestimento\nde parede")
        self.assertEqual(ribbon.short_label("Parede   (W)"), "Parede")
        self.assertEqual(ribbon.small_label("Abertura (cobertura / laje)"), "Abertura")
        self.assertEqual(ribbon.small_label("Repetir nos pavimentos…   (R)"), "Repetir nos pavimentos")


class SmoothEdges(unittest.TestCase):
    """0.69: the strips of a curved surface (a pipe) draw no edges; a roof's low ridge still does."""

    def test_pipe_and_low_ridge(self):
        circle = [(0.05 * math.cos(2 * math.pi * k / 24), 0.05 * math.sin(2 * math.pi * k / 24)) for k in range(24)]
        pipe = _prism(circle, 4.0)
        pairs, _faces = pipe.edge_array()
        along = [p for p in pairs if abs(pipe.verts[p[1]][0] - pipe.verts[p[0]][0]) > 1.0]
        self.assertEqual(along, [])                                      # no stripes along the pipe
        self.assertEqual(len(pairs), 48)                                 # the two end circles
        roof = _prism([(0.0, 0.0), (5.0, 0.0), (5.0, 0.3), (2.5, 0.6), (0.0, 0.3)], 8.0)   # ridge bent ~14°
        pairs, _faces = roof.edge_array()
        ridge = [p for p in pairs if all(abs(roof.verts[v][1] - 2.5) < 1e-9 and abs(roof.verts[v][2] - 0.6) < 1e-9
                                         for v in p)]
        self.assertEqual(len(ridge), 1)

    def test_a_pipes_outline_on_a_drawing(self):
        """0.136: on a drawing a pipe has its two sides — the softened edges where it turns away from the viewer —
        seen from above or from the side; end on, none (its circle is an edge already)."""
        circle = [(0.05 * math.cos(2 * math.pi * k / 24), 0.05 * math.sin(2 * math.pi * k / 24)) for k in range(24)]
        pipe = _prism(circle, 4.0)
        for view in ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0)):
            sides = pipe.contour_edges(np.array(view))
            self.assertEqual(len(sides), 2, view)
            for a, b in sides:
                self.assertAlmostEqual(abs(pipe.verts[b][0] - pipe.verts[a][0]), 4.0)          # along it
            depth = [float(pipe.verts[a] @ np.cross(view, (1.0, 0.0, 0.0))) for a, _b in sides]
            self.assertAlmostEqual(abs(depth[0] - depth[1]), 0.10)                           # its diameter apart
        self.assertEqual(len(pipe.contour_edges(np.array((1.0, 0.0, 0.0)))), 0)


class Commands(unittest.TestCase):
    def test_add_pull_undo_redo(self):
        doc = Document()
        events = []
        doc.subscribe(lambda changed, removed: events.append((set(changed), set(removed))))
        obj = SketchObject("A", I4, sg.rectangle_mesh(1, 1))
        doc.execute(AddObject(obj))
        before = doc.get(obj.id).mesh
        after = before.copy()
        sg.push_pull(after, 0, I4, 1.0)
        doc.execute(ReplaceMesh(obj.id, before, after))
        self.assertEqual(len(doc.get(obj.id).mesh.faces), 6)
        doc.undo()
        self.assertEqual(len(doc.get(obj.id).mesh.faces), 1)
        doc.undo()
        self.assertIsNone(doc.get(obj.id))
        doc.redo()
        doc.redo()
        self.assertEqual(len(doc.get(obj.id).mesh.faces), 6)
        self.assertEqual(events[0], ({obj.id}, set()))
        self.assertEqual(events[2], ({obj.id}, set()))  # undo Push/Pull: mesh changed
        self.assertEqual(events[3], (set(), {obj.id}))  # undo creation: object removed


class FillPatterns(unittest.TestCase):
    """0.314 — the fill patterns (core/patterns.py): families of lines, whole, dashed or dotted, covering a box from
    the same origin; a brick bond's joints halfway along the course below; laid on a mesh's faces in 3D."""

    def test_every_pattern(self):
        from arqbim.core import patterns
        self.assertEqual(set(patterns.DRAFTING) | set(patterns.MODEL), set(patterns.PATTERNS))
        for key, pattern in patterns.PATTERNS.items():
            segs, dots = patterns.segments(key, (0.0, 0.0, 20.0, 10.0), 1.0)
            if pattern.solid:
                self.assertEqual(len(segs) + len(dots), 0)
            else:
                self.assertGreater(len(segs) + len(dots), 3, key)
                self.assertTrue(np.all(np.linalg.norm(segs[:, 1] - segs[:, 0], axis=1) > 0), key)
        self.assertEqual(len(patterns.segments("nada", (0, 0, 1, 1))[0]), 0)
        far = patterns.segments("diagonal", (0.0, 0.0, 1e6, 1e6))       # (far too fine for it: nothing, not a hang)
        self.assertEqual(len(far[0]), 0)

    def test_lines_meet(self):
        from arqbim.core import patterns
        a, _d = patterns.segments("horizontal", (0.0, 0.0, 5.0, 5.0))
        b, _d = patterns.segments("horizontal", (5.0, 0.0, 9.0, 5.0))
        self.assertEqual(sorted(set(np.round(a[:, 0, 1], 6))), sorted(set(np.round(b[:, 0, 1], 6))))

    def test_brick_bond(self):
        from arqbim.core import patterns
        segs, _d = patterns.segments("brick", (0.0, 0.0, 1.0, 0.26))
        joints = segs[np.isclose(segs[:, 0, 0], segs[:, 1, 0])]
        row = {round(float(min(s[:, 1])) / 0.065): set() for s in joints}
        for s in joints:
            row[round(float(min(s[:, 1])) / 0.065)].add(round(float(s[0, 0]) % 0.25, 3))
        self.assertEqual(row[0], {0.0})
        self.assertEqual(row[1], {0.125})                                # (halfway along the course below)
        self.assertEqual(row[2], {0.0})

    def test_on_triangles(self):
        from arqbim.core import patterns
        tri = np.array([[[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, 0.0, 1.0]]])
        segs = patterns.on_triangles("tile_20", tri, np.array([[0.0, -1.0, 0.0]]), lift=0.001)
        self.assertGreater(len(segs), 5)
        self.assertTrue(np.allclose(segs[..., 1], -0.001))             # (a hair in front of the face)
        inside = segs[..., 0] / 2.0 + segs[..., 2] <= 1.0 + 1e-9         # (within the triangle)
        self.assertTrue(np.all(inside))
        self.assertTrue(np.all(np.isclose(np.round(segs[np.isclose(segs[:, 0, 2], segs[:, 1, 2]), 0, 2] / 0.2),
                                          segs[np.isclose(segs[:, 0, 2], segs[:, 1, 2]), 0, 2] / 0.2)))


class SunAndShadows(unittest.TestCase):
    """0.316 — the sun: its direction from an azimuth and an altitude and back; where it is over Lisbon at noon on the
    longest day (high in the south) and at midnight (below the horizon). The shadows on paper: an eave 1 m deep over a
    wall 3 m high, the sun from the south at 45°: a band 1,1 m high under it, and none where the wall is in its own
    shadow."""

    def test_sun(self):
        from datetime import datetime
        from arqbim.core import sun
        v = sun.direction(213.0, 47.0)
        self.assertAlmostEqual(float(np.linalg.norm(v)), 1.0)
        az, alt = sun.angles(v)
        self.assertAlmostEqual(az, 213.0, places=6)
        self.assertAlmostEqual(alt, 47.0, places=6)
        self.assertTrue(np.allclose(sun.direction(180.0, 45.0), (0.0, -math.sqrt(0.5), math.sqrt(0.5))))
        az, alt = sun.position(38.72, -9.14, datetime(2026, 6, 21, 12, 38), 0.0)      # (solar noon, in UTC)
        self.assertAlmostEqual(alt, 90.0 - 38.72 + 23.44, delta=0.6)
        self.assertAlmostEqual(az, 180.0, delta=3.0)
        az, alt = sun.position(38.72, -9.14, datetime(2026, 6, 21, 16, 0), 1.0)       # (the afternoon: west)
        self.assertTrue(220.0 < az < 290.0 and 30.0 < alt < 70.0, (az, alt))
        self.assertLess(sun.position(38.72, -9.14, datetime(2026, 12, 21, 0, 0), 0.0)[1], 0.0)

    def test_eave_shadow(self):
        from arqbim.core import sun
        from arqbim.model import drawings

        def box(lo, hi):
            v = np.array([(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
            quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
            return np.array([v[list(t)] for a, b, c, d in quads for t in ((a, b, c), (a, c, d))])

        face = np.array(((0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (4.0, 0.0, 3.0), (0.0, 0.0, 3.0)))   # (the wall, facing -y)
        eave = box((0.0, -1.0, 2.9), (4.0, 0.0, 3.0))
        light = sun.direction(180.0, 45.0)
        out = drawings.cast_shadows([(face, np.array((0.0, -1.0, 0.0)), (0.2, 0.2, 0.2), 1.0, 5.0)], eave, light,
                                    np.zeros(3), np.array((1.0, 0.0, 0.0)), np.array((0.0, 0.0, 1.0)))
        self.assertTrue(out)
        rings = [r for f in out for r in f[0]]
        area = sum(Drawing2D_area(r) for r in rings)
        self.assertAlmostEqual(area, 4.0 * 1.1, places=6)
        self.assertAlmostEqual(min(float(r[:, 1].min()) for r in rings), 1.9, places=6)
        self.assertTrue(all(f[1] == (0.2, 0.2, 0.2) and f[3] < 5.0 for f in out))      # (its colour, over it)
        behind = drawings.cast_shadows([(face, np.array((0.0, -1.0, 0.0)), (0.2, 0.2, 0.2), 1.0, 5.0)], eave,
                                       sun.direction(0.0, 45.0), np.zeros(3), np.array((1.0, 0.0, 0.0)),
                                       np.array((0.0, 0.0, 1.0)))
        self.assertEqual(behind, [])                                        # (the sun behind it: nothing cast)


class CameraMoves(unittest.TestCase):
    """0.364: the ArqSynth Presentation's camera moves, here (model/camera_moves.py) — the same 21 (its library's
    names, groups, times and speed curves), made from the same measures by the same generators (checked against its
    own code when written: the same points and targets for all 21)."""

    def setUp(self):
        from arqbim.model import camera_moves as cm
        self.cm = cm
        self.building = cm.Building((0.0, 1.0, 0.0), 5.0, (8.0, 2.0, 6.0))

    def test_the_library(self):
        cm = self.cm
        self.assertEqual(len(cm.MOVES), 21)
        self.assertEqual({m[0] for m in cm.MOVES.values()}, set(cm.CATEGORIES))
        self.assertEqual(sum(cm.interior(m) for m in cm.MOVES), 8)
        self.assertEqual(cm.MOVES["orbit_360"][2:], (20.0, "linear"))

    def test_round_the_building(self):
        """A quarter turn at eye height, as far as frames it (the Presentation's framingDistance: 2,2 × the radius,
        6 m at least), a point every 22°, looking at the building's middle; a dolly in from the south (+Z), straight;
        a pull back with a bend: five points, the middle one out to its side."""
        cm = self.cm
        p = cm.points(cm.params("orbit_90", self.building))
        self.assertEqual(len(p), 6)
        np.testing.assert_allclose(p[0], (11.0 * math.cos(math.radians(-45)), 1.6, 11.0 * math.sin(math.radians(-45))))
        np.testing.assert_allclose(np.linalg.norm(p[:, [0, 2]], axis=1), 11.0)
        self.assertEqual(cm.target("orbit_90", self.building), (0.0, 1.0, 0.0))
        dolly = cm.points(cm.params("dolly_in", self.building))
        np.testing.assert_allclose(dolly, ((0.0, 1.6, 16.5), (0.0, 1.6, 5.5)))
        back = cm.points(cm.params("pull_back", self.building))
        self.assertEqual(len(back), 5)
        straight = (back[0] + back[-1]) / 2
        self.assertAlmostEqual(abs(back[2][0] - straight[0]), 0.1 * abs(back[-1][2] - back[0][2]), places=6)

    def test_inside_a_room(self):
        """An L-shaped room: its middle inside it (the centroid falls outside an L), its distance to the nearest wall;
        the turn round it kept 45 cm off that wall; looking at its middle at eye height (1,50 m over its floor). No room
        given: the Presentation's assumed one (4 × 4 m, 2,70 m) under the building's middle."""
        cm = self.cm
        ell = [(0.0, 0.0), (6.0, 0.0), (6.0, 2.0), (2.0, 2.0), (2.0, 6.0), (0.0, 6.0)]
        room = cm.room_from_polygon(ell, 0.0, 2.8)
        self.assertTrue(cm.inside(room.center[0], room.center[2], ell))
        self.assertGreater(room.inradius, 0.5)
        self.assertEqual(room.half, (3.0, 3.0))
        p = cm.points(cm.params("int_orbit_full", self.building, room))
        radius = np.linalg.norm(p[:, [0, 2]] - (room.center[0], room.center[2]), axis=1)
        self.assertTrue(np.all(radius <= room.inradius - cm.WALL_CLEARANCE + 1e-9))
        self.assertEqual(cm.target("int_orbit_full", self.building, room), (room.center[0], 1.5, room.center[2]))
        assumed = cm.target("int_dolly_in", self.building)
        self.assertEqual(assumed, (0.0, 1.5, 0.0))
        self.assertIsNone(cm.room_from_polygon([(0, 0), (1, 1)], 0.0, 2.8))

    def test_played(self):
        """Played at 30 frames a second for its time (or the one given): from its first point to its last, the camera
        always looking at its target, the speed curve's (an easing out: half the way well before half the time)."""
        cm = self.cm
        frames = cm.frames("orbit_rising", self.building)
        self.assertEqual(len(frames), 14 * 30 + 1)
        p = cm.points(cm.params("orbit_rising", self.building))
        np.testing.assert_allclose(frames[0][0], p[0], atol=1e-6)
        np.testing.assert_allclose(frames[-1][0], p[-1], atol=1e-6)
        self.assertTrue(all(np.allclose(look, (0.0, 1.0, 0.0)) for _eye, look in frames))
        self.assertEqual(len(cm.frames("dolly_in", self.building, seconds=2)), 61)
        out = cm.frames("orbit_descending", self.building)             # (ease_out)
        travelled = np.cumsum([0.0] + [np.linalg.norm(b[0] - a[0]) for a, b in zip(out, out[1:])])
        self.assertGreater(travelled[len(out) // 2], 0.6 * travelled[-1])
        point, offset = np.array((3.0, -2.0, 1.5)), np.array((1.0, 2.0, 0.5))
        np.testing.assert_allclose(cm.to_model(cm.to_gl(point, offset), offset), point)


class PresentationSun(unittest.TestCase):
    """0.365: the sun as the ArqSynth Presentation places it (model/presentation_sun.py, its sun.ts — checked against
    its code when written: the same angles, sunrises and sunsets for 100 places, days and hours)."""

    def test_where_it_is(self):
        from arqbim.model import presentation_sun as ps
        azimuth, elevation = ps.angles(38.72, -9.14, 172, 720)        # (Lisbon, 21 June, 12:00 on the Presentation's clock)
        self.assertAlmostEqual(azimuth, 198.58827776729223, places=9)
        self.assertAlmostEqual(elevation, 74.0323366298227, places=9)
        v = ps.direction(38.72, -9.14, 172, 720)
        self.assertAlmostEqual(float(np.linalg.norm(v)), 1.0)
        self.assertTrue(v[1] < 0 and v[2] > 0.9)                      # (in the south, high: north is +y)
        rise, sets = ps.daylight(38.72, -9.14, 172)
        self.assertAlmostEqual(rise, 256.6574388837135, places=6)
        self.assertLess(ps.angles(38.72, -9.14, 172, rise - 30)[1], 0.0)  # (before sunrise: under the horizon)
        self.assertGreater(ps.angles(38.72, -9.14, 172, sets - 30)[1], 0.0)
        self.assertEqual(ps._meridian(7.5), 15.0)                      # (JavaScript's rounding of a half)

    def test_days_and_animations(self):
        from arqbim.model import presentation_sun as ps
        self.assertEqual((ps.day_of(12, 21), ps.day_of(1, 1), ps.day_of(6, 21)), (355, 1, 172))
        self.assertEqual((ps.month_day(355), ps.month_day(1), ps.month_day(365)), ((12, 21), (1, 1), (12, 31)))
        self.assertEqual(all(ps.month_day(ps.day_of(m, d)) == (m, d) for m in range(1, 13) for d in (1, 15, 28)), True)
        day = ps.sweep(38.72, -9.14, 172, 720, "day", 9)
        self.assertEqual(len(day), 9)
        self.assertAlmostEqual(day[0][1], ps.daylight(38.72, -9.14, 172)[0])
        self.assertTrue(all(d == 172 for d, _m in day))
        year = ps.sweep(38.72, -9.14, 172, 600, "year", 13)
        self.assertEqual(([d for d, _m in year][0], [d for d, _m in year][-1]), (1, 365))
        self.assertTrue(all(m == 600 for _d, m in year))
        self.assertEqual(ps.sweep(38.72, -9.14, 172, 600, "none"), [(172, 600)])


class Panorama(unittest.TestCase):
    """0.368: a 360° panorama from six square renders of 90° (render/panorama.py): each face's basis as Mitsuba's
    look_at takes it (checked against Mitsuba itself when written: right = direction × up, the top up), the
    equirectangular picture's middle straight ahead, its right quarter to the right, its top straight up — and a real
    (tiny) Mitsuba panorama of a red wall ahead and a green one to the right, each where it should be."""

    def test_faces_and_equirect(self):
        from arqbim.render import panorama as pano
        forward = (0.0, 1.0, 0.3)                         # (made level: north)
        bases = pano.faces(forward)
        self.assertEqual(set(bases), set(pano.FACES))
        for direction, right, up in bases.values():
            m = np.array((direction, right, up))
            np.testing.assert_allclose(m @ m.T, np.eye(3), atol=1e-12)
        np.testing.assert_allclose(bases["front"][1], (1.0, 0.0, 0.0))          # (looking north, right is east)
        np.testing.assert_allclose(bases["up"][2], (0.0, -1.0, 0.0))            # (looking up, the top is behind)
        n = 24

        def rendered(extra):                              # (each pixel: the way it looks; `extra` pixels round its 90°)
            size = n + 2 * extra
            pictures = {}
            for name, (direction, right, up) in bases.items():
                x = (2.0 * (np.arange(size) + 0.5) / size - 1.0) * size / n
                xx, yy = np.meshgrid(x, -x)
                d = direction + xx[..., None] * right + yy[..., None] * up
                pictures[name] = d / np.linalg.norm(d, axis=-1, keepdims=True)
            return pictures
        want = pano.directions(96, 48, forward)
        out = pano.equirect(rendered(0), forward, 96, 48)
        self.assertLess(float(np.max(np.linalg.norm(out - want, axis=-1))), 0.05)
        wide = pano.equirect(rendered(pano.margin(n)), forward, 96, 48, inner=n)     # (with its margin: the same)
        self.assertLess(float(np.max(np.linalg.norm(wide - want, axis=-1))), 0.05)
        self.assertEqual((pano.margin(24), pano.margin(512)), (2, 16))
        self.assertAlmostEqual(math.tan(math.radians(pano.face_fov(512)) / 2.0), 544 / 512)
        np.testing.assert_allclose(want[24, 48], (0.0, 1.0, 0.0), atol=0.07)     # (the middle: ahead)
        np.testing.assert_allclose(want[24, 72], (1.0, 0.0, 0.0), atol=0.07)     # (a quarter right: east)
        self.assertGreater(want[0, 10][2], 0.99)                                 # (the top: up)
        self.assertEqual(pano.face_size(4096), 1024)

    def test_rendered(self):
        import importlib.util
        import json
        import tempfile
        if importlib.util.find_spec("mitsuba") is None:
            self.skipTest("Mitsuba 3 not installed")
        from arqbim.model.render_scene import RenderScene
        from arqbim.render import path_tracer
        from PySide6 import QtGui

        def wall(x0, y0, x1, y1):
            a, b, c, d = (x0, y0, 0.0), (x1, y1, 0.0), (x1, y1, 3.0), (x0, y0, 3.0)
            return np.array(((a, b, c), (a, c, d)), dtype=np.float32)

        groups = [("matte", (0.9, 0.05, 0.05), wall(-3.0, 3.0, 3.0, 3.0)),      # (red, ahead: north)
                  ("matte", (0.05, 0.8, 0.05), wall(3.0, 3.0, 3.0, -3.0))]       # (green, to the right: east)
        scene = RenderScene(groups, eye=(0.0, 0.0, 1.5), target=(0.0, 5.0, 1.5), up=(0.0, 0.0, 1.0), fov=60.0,
                            sun=(-0.4, -0.4, 0.82), ground=None, lights=[], lighting="sun", clean=False)   # (on both)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cena.npz")
            scene.save(path)
            picture = os.path.join(tmp, "p.png")
            path_tracer.render_panorama(path, picture, 64, 32, 4, passes=1)
            image = QtGui.QImage(picture)
            with open(picture + ".json", encoding="utf-8") as fh:
                state = json.load(fh)
        self.assertEqual((image.width(), image.height(), state["finished"], state["of"]), (64, 32, True, 6))

        def colour(col, row=17):
            c = image.pixelColor(col, row)
            return c.red(), c.green(), c.blue()

        red, green = colour(32), colour(48)              # (ahead; a quarter to the right)
        self.assertTrue(red[0] > red[1] + 30, red)
        self.assertTrue(green[1] > green[0] + 30, green)


def Drawing2D_area(ring):
    ring = np.asarray(ring, dtype=float)
    x, y = ring[:, 0], ring[:, 1]
    return abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))) / 2.0


class FreeDrawingTest(unittest.TestCase):
    """0.373 — the free drawing as SketchUp's (the owner: «não consigo selecionar uma linha, copiar, ou usar o offset;
    preciso de ferramenta de arco, linha livre, curvas de Bézier»)."""

    def test_two_point_arc_by_its_bulge_and_radius(self):
        from arqbim.core import curves
        up = (0, 0, 1)
        centre, start, angle = curves.arc_by_bulge((-1, 0, 0), (1, 0, 0), 1.0, up)      # a half circle, to the left
        self.assertTrue(np.allclose(centre, 0) and np.allclose(start, (-1, 0, 0)) and abs(angle + 180) < 1e-9)
        pts = curves.arc_points(centre, up, start, angle, 4)
        self.assertTrue(np.allclose(pts[2], (0, 1, 0)) and np.allclose(pts[-1], (1, 0, 0)))
        centre, start, angle = curves.arc_by_bulge((0, 0, 0), (4, 0, 0), -0.5, up)     # shallow, to the right
        r = float(np.linalg.norm(start - centre))
        self.assertAlmostEqual(r, (4 + 0.25) / 1.0, places=9)                         # (h² + c²/4) / 2h
        self.assertTrue(np.allclose(curves.arc_points(centre, up, start, angle, 2)[1], (2, -0.5, 0)))
        self.assertAlmostEqual(curves.bulge_for_radius((0, 0, 0), (4, 0, 0), 2.0, 1.0), 2.0)
        self.assertIsNone(curves.bulge_for_radius((0, 0, 0), (4, 0, 0), 1.0, 1.0))      # (under half the chord)
        # the arc tangent to a line coming in along +x at (0, 0), ending at (2, 2): a quarter circle of radius 2
        bulge = curves.tangent_bulge((0, 0, 0), (2, 2, 0), (1, 0, 0), up)
        centre, start, angle = curves.arc_by_bulge((0, 0, 0), (2, 2, 0), bulge, up)
        self.assertTrue(np.allclose(centre, (0, 2, 0)) and abs(abs(angle) - 90) < 1e-6)
        # through three points (3D), and its pieces by default: one every 15° at most
        centre, normal, angle = curves.arc_through((1, 0, 0), (0, 1, 0), (-1, 0, 0))
        self.assertTrue(np.allclose(centre, 0) and np.allclose(normal, up) and abs(angle - 180) < 1e-9)
        self.assertEqual((curves.segments_for(90), curves.segments_for(100), curves.segments_for(1)), (6, 7, 2))

    def test_bezier_and_freehand_points(self):
        from arqbim.core import curves
        corner = [[(0, 0, 0)] * 3, [(4, 0, 0)] * 3]
        self.assertEqual(len(curves.bezier_points(corner)), 2)                        # (two corners: one straight piece)
        smooth = [[(0, 0, 0)] * 3, curves.smooth_anchor((4, 0, 0), (5, 2, 0)), [(8, 0, 0)] * 3]
        self.assertTrue(np.allclose(smooth[1][1], (3, -2, 0)))                         # (the other handle mirrored)
        pts = curves.bezier_points(smooth, steps=12)
        self.assertEqual(len(pts), 25)
        self.assertTrue(np.allclose(pts[12], (4, 0, 0)) and np.allclose(pts[-1], (8, 0, 0)))
        wavy = [(x / 10, 0.0005 * math.sin(x), 0) for x in range(100)]                # (a hand's wobble: one line)
        self.assertEqual(len(curves.simplify(wavy, 0.01)), 2)
        bent = [(0, 0, 0), (1, 0.001, 0), (2, 0, 0), (2, 1, 0), (2, 2, 0)]
        self.assertEqual(len(curves.simplify(bent, 0.01)), 3)

    def test_profile_sides(self):
        """0.375: a profile's sides — an arc through a point, a Bézier between its tangents — in pieces, and as kept
        in the IFC (stretched when read back)."""
        from arqbim.core import curves
        square = [(0, 0), (4, 0), (4, 2), (0, 2)]
        out = curves.profile_outline(square, [None, None, {"kind": "arc", "through": (2, 4)}, None])
        self.assertEqual(out[:3], [(0.0, 0.0), (4.0, 0.0), (4.0, 2.0)])
        self.assertAlmostEqual(max(y for _x, y in out), 4.0, places=2)
        self.assertEqual(len(out), 4 + curves.segments_for(180, curves.PROFILE_ARC_DEG) - 1)
        bez = {"kind": "bezier", "h1": (1, 1), "h2": (3, 1)}
        self.assertEqual(len(curves.profile_outline(square, [bez])), 4 + curves.PROFILE_BEZIER_STEPS - 1)
        self.assertEqual(curves.side_of(curves.side_text(bez), 2.0, 1.0), {"kind": "bezier", "h1": (2.0, 1.0),
                                                                         "h2": (6.0, 1.0)})
        self.assertIsNone(curves.side_of(""))
        self.assertIsNone(curves.side_of("x:1,2"))

    def test_profile_fillet(self):
        """0.380: a corner rounded — two corners where the arc touches its sides, the side between them an arc through
        its middle; the radius kept to what the shorter side allows; not next to a curved side, not on a straight
        angle; the first corner too (its last side kept)."""
        from arqbim.core import curves
        wall = [(0, 0), (6, 0), (6, 2.8), (0, 2.8)]
        corners, sides, r = curves.fillet(wall, [None] * 4, 1, 0.5)
        self.assertTrue(np.allclose(corners[:3], [(0, 0), (5.5, 0.0), (6.0, 0.5)]))
        self.assertEqual(len(corners), 5)
        self.assertEqual([s and s["kind"] for s in sides], [None, "arc", None, None, None])
        mid = 0.5 / math.sin(math.pi / 4) - 0.5                    # (from the corner, along the bisector)
        self.assertTrue(np.allclose(sides[1]["through"], (6 - mid / math.sqrt(2), mid / math.sqrt(2))))
        self.assertAlmostEqual(r, 0.5)
        _c, _s, r = curves.fillet(wall, [None] * 4, 1, 10.0)
        self.assertAlmostEqual(r, 0.98 * 2.8)                      # (a right angle: as far as the 2,8 m side)
        self.assertIsNone(curves.fillet(wall, [None, {"kind": "arc", "through": (6.5, 1.4)}, None, None], 1, 0.5))
        self.assertIsNone(curves.fillet([(0, 0), (3, 0), (6, 0), (6, 2), (0, 2)], [None] * 5, 1, 0.5))
        corners, sides, _r = curves.fillet(wall, [None] * 4, 0, 0.5)
        self.assertTrue(np.allclose(corners[:2], [(0.0, 0.5), (0.5, 0.0)]))
        self.assertEqual(len(sides), 5)
        self.assertEqual(sides[0]["kind"], "arc")
        self.assertIsNotNone(curves.profile_outline(corners, sides))

    def test_wall_band_solid(self):
        """0.383: the walls being drawn as a solid — a ring moved out and in corner for corner (mitred), turned
        counter-clockwise first; a closed band: top, outer and inner faces (6 triangles a side), the lines at its foot
        and top and an upright edge at each corner; an open one (an arc): its two ends closed too."""
        from arqbim.core import band_solid as bs
        square = [(0, 0), (4, 0), (4, 3), (0, 3)]
        self.assertEqual(bs.ccw(square[::-1]), [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)])
        self.assertEqual(bs.ccw(square), [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)])
        self.assertTrue(np.allclose(bs.offset_ring(square, 0.1), [(-0.1, -0.1), (4.1, -0.1), (4.1, 3.1), (-0.1, 3.1)]))
        self.assertTrue(np.allclose(bs.offset_ring(square, -0.1), [(0.1, 0.1), (3.9, 0.1), (3.9, 2.9), (0.1, 2.9)]))
        tris, segs = bs.band_solid(bs.offset_ring(square, 0.1), bs.offset_ring(square, -0.1), 0.0, 2.8)
        self.assertEqual(len(tris), 4 * 6)
        self.assertEqual(len(segs), 4 * 4 * 2 + 4 * 4)          # (4 lines of 4 sides; 2 uprights a corner)
        zs = np.array([p[2] for tri in tris for p in tri])
        self.assertAlmostEqual(zs.min(), 0.0)
        self.assertAlmostEqual(zs.max(), 2.8)
        tris, segs = bs.band_solid([(0, 1.1), (1.1, 0)], [(0, 0.9), (0.9, 0)], 1.0, 2.0, closed=False)
        self.assertEqual(len(tris), 6 + 4)                         # (one piece and its two ends)
        self.assertEqual(bs.band_solid([(0, 0)], [(0, 1)], 0.0, 2.0), ([], []))

    def test_curve_data_follows_a_move_and_a_mirror(self):
        from arqbim.core import curves
        arc = curves.arc_curve((0, 0, 0), (0, 0, 1), (1, 0, 0), 90, 6)
        moved = curves.transform_curve(arc, transform.translation((5, 0, 0)))
        self.assertTrue(np.allclose(moved["centre"], (5, 0, 0)) and np.allclose(moved["start"], (6, 0, 0)))
        mirror = np.diag((-1.0, 1.0, 1.0, 1.0))
        flipped = curves.transform_curve(arc, mirror)
        end = curves.arc_points(flipped["centre"], flipped["normal"], flipped["start"], flipped["angle"], 6)[-1]
        self.assertTrue(np.allclose(end, (0, 1, 0)), end)                              # (still ends where it did)

    def test_paths_planes_and_parallels(self):
        self.assertEqual(lines.paths([(0, 1), (1, 2), (2, 3)]), [[0, 1, 2, 3]])
        self.assertEqual(lines.paths([(0, 1), (1, 2), (2, 0)]), [[0, 1, 2, 0]])
        self.assertEqual(sorted(map(sorted, lines.paths([(0, 1), (1, 2), (1, 3)]))), [[0, 1], [1, 2], [1, 3]])
        self.assertTrue(np.allclose(lines.plane_of([(0, 0, 0), (4, 0, 0)])[1], (0, 0, 1)))       # (a level line)
        self.assertTrue(np.allclose(lines.plane_of([(0, 0, 0), (0, 0, 3)], (0, 1, 0))[1], (0, -1, 0)))
        self.assertIsNone(lines.plane_of([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 1)]))
        self.assertEqual([[tuple(p) for p in path] for path in lines.offset_path([(0, 0), (4, 0), (4, 3)], 0.5)],
                         [[(0.0, 0.5), (3.5, 0.5), (3.5, 3.0)]])                         # (to its left, corners sharp)
        ring = lines.offset_path([(0, 0), (4, 0), (4, 3), (0, 3), (0, 0)], 0.5, closed=True)[0]
        self.assertAlmostEqual(Drawing2D_area(ring[:-1]), 3 * 2, places=9)               # (inwards)

    def test_new_lines_close_faces_with_lines_drawn_before(self):
        """An arc ending on two lines drawn before, a line closing an outline of another chain, a line ending in the
        middle of another (a T): the smallest loops through a new line, the pieces cut where they meet."""
        from arqbim.core import curves
        up = ((0, 0, 0), (0, 0, 1))
        old = [((0, 0, 0), (4, 0, 0)), ((4, 0, 0), (4, 3, 0)), ((0, 0, 0), (0, 3, 0))]
        arc = curves.arc_points((2, 3, 0), (0, 0, 1), (4, 3, 0), 180, 12)
        new = list(zip(arc, arc[1:]))
        loops, pieces = lines.close_loops(new, old, up)
        self.assertEqual(len(loops), 1)
        self.assertTrue(all(used for ps in pieces for _p, _q, used in ps))
        self.assertGreater(Drawing2D_area(loops[0]), 12 + 0.95 * math.pi * 2)          # (the box and the half disc)
        # a T: a line from the middle of a side across to the other — the box is cut in two, the left half
        old = [((0, 0, 0), (4, 0, 0)), ((4, 0, 0), (4, 3, 0)), ((4, 3, 0), (0, 3, 0)), ((0, 3, 0), (0, 0, 0))]
        loops, pieces = lines.close_loops([((2, 0, 0), (2, 3, 0))], old, up)
        self.assertEqual(sorted(round(Drawing2D_area(lp), 9) for lp in loops), [6.0, 6.0])
        self.assertEqual(len(pieces[1]), 2)                                              # (the bottom side cut at x=2)
        # nothing closed: an open L and a line off on its own
        self.assertEqual(lines.close_loops([((5, 5, 0), (6, 5, 0))], old[:2], up), ([], None))
        # lines on another plane are not looked at
        high = [((0, 0, 1), (4, 0, 1)), ((4, 0, 1), (4, 3, 1)), ((4, 3, 1), (0, 3, 1))]
        self.assertEqual(lines.close_loops([((0, 3, 0), (0, 0, 0))], high, up), ([], None))

    def _lines(self, doc, pts, curve=None):
        obj = SketchObject("L", np.eye(4), PolyMesh([np.array(p, float) for p in pts],
                                                    lines=[(k, k + 1) for k in range(len(pts) - 1)]), curve=curve)
        doc.execute(AddObject(obj))
        return obj

    def test_a_line_picked_alone_moved_copied_deleted(self):
        from arqbim.model import parts
        doc = Document()
        chain = self._lines(doc, [(0, 0, 0), (4, 0, 0), (4, 3, 0), (2, 3, 0)])
        other = self._lines(doc, [(4, 3, 0), (6, 3, 0)])                                # (another chain joined there)
        self.assertEqual(parts.joined_lines(chain.mesh, 1), frozenset({0, 1, 2}))
        self.assertEqual(parts.touching_lines(doc, [chain.id]), {chain.id, other.id})
        picked = {chain.id: frozenset({1})}
        self.assertAlmostEqual(parts.line_length(doc, picked), 3.0)
        parts.transform_lines(doc, picked, transform.translation((1, 0, 0)), "Mover")
        w = [tuple(np.round(v, 6)) for v in doc.get(chain.id).mesh.verts]
        self.assertEqual(w, [(0, 0, 0), (5, 0, 0), (5, 3, 0), (2, 3, 0)])              # (the 1st and 3rd stretched)
        self.assertEqual([tuple(np.round(v, 6)) for v in doc.get(other.id).mesh.verts], [(5, 3, 0), (6, 3, 0)])
        new = parts.add_copies(doc, parts.line_copies(doc, picked), [transform.translation((0, 5, 0))], "Copiar")
        copy = doc.get(new[0])
        self.assertEqual((len(copy.mesh.lines), [tuple(np.round(sg.transform_point(copy.matrix, v), 6))
                                                 for v in copy.mesh.verts]), (1, [(5, 5, 0), (5, 8, 0)]))
        self.assertEqual(parts.delete_lines(doc, picked), 1)
        self.assertEqual(len(doc.get(chain.id).mesh.lines), 2)
        doc.undo()
        self.assertEqual(len(doc.get(chain.id).mesh.lines), 3)

    def test_faces_picked_alone_are_copied(self):
        from arqbim.model import parts
        doc = Document()
        mesh = sg.rectangle_mesh(3, 2)
        sg.imprint_polygon(mesh, 0, [(0.5, 0.5, 0), (2.5, 0.5, 0), (2.5, 1.5, 0), (0.5, 1.5, 0)])
        obj = SketchObject("R", np.eye(4), mesh)
        doc.execute(AddObject(obj))
        middle = max(range(len(mesh.faces)), key=mesh.face_area)
        made = parts.face_copies(doc, {obj.id: (frozenset({middle}), False)})
        new = parts.add_copies(doc, made, [transform.translation((0, 3, 0))], "Copiar")
        copy = doc.get(new[0])
        self.assertEqual((len(copy.mesh.faces), round(copy.mesh.face_area(0), 9)), (1, 2.0))
        self.assertAlmostEqual(float(copy.matrix[1, 3]), 3.0)

    def test_closing_with_lines_and_reshaping_a_curve(self):
        from arqbim.core import curves
        from arqbim.model import curve_edit, line_faces
        doc = Document()
        self._lines(doc, [(4, 0, 0), (0, 0, 0)])                                         # (a line drawn before)
        centre, start, angle = curves.arc_by_bulge((0, 0, 0), (4, 0, 0), -1.0, (0, 0, 1))
        c = curves.arc_curve(centre, (0, 0, 1), start, angle)
        pts = curves.curve_points(c)
        arc = SketchObject("Arco", np.eye(4), PolyMesh(pts, lines=[(k, k + 1) for k in range(len(pts) - 1)]),
                           curve=c)
        closed = line_faces.close_with(doc, arc, ((0, 0, 0), (0, 0, 1)), "Arco")
        self.assertIsNotNone(closed)
        faces = [o for o in doc.objects.values() if o.mesh.faces]
        self.assertEqual(len(faces), 1)
        self.assertFalse([o for o in doc.objects.values() if o.mesh.lines])               # (both used up by the face)
        doc.undo()
        self.assertEqual([len(o.mesh.lines) for o in doc.objects.values()], [1])
        # an arc alone, its end dragged: still an arc through its middle; the line at that end follows
        arc = self._lines(doc, pts, curve=c)
        line = self._lines(doc, [(4, 0, 0), (4, 2, 0)])
        what = curve_edit.grips(doc.get(arc.id))[3]
        self.assertEqual(what, ["start", "end", "mid"])
        moved = curve_edit.dragged(doc.get(arc.id), "end", (5, 0, 0))
        curve_edit.reshape(doc, arc.id, moved)
        self.assertEqual(doc.get(arc.id).curve["kind"], "arc")
        self.assertTrue(np.allclose(doc.get(arc.id).mesh.verts[-1], (5, 0, 0)))
        self.assertTrue(np.allclose(doc.get(line.id).mesh.verts[0], (5, 0, 0)))
        # its radius changed (Properties): from the same centre and start direction
        bigger = curves.arc_with(doc.get(arc.id).curve, radius=10)
        curve_edit.reshape(doc, arc.id, bigger)
        self.assertAlmostEqual(curves.arc_radius(doc.get(arc.id).curve), 10)

    def test_bezier_as_blender(self):
        """0.411 (the owner: «a curva Bézier não é uma curva, mas uma linha reta. Esperava nós na linha que podem ser
        movidos criando a curva — faça como o Blender»): points with automatic tangents — the curve passes smoothly
        through them; a straight curve of two points, a point added halfway (its shape kept) and dragged out: it
        bends, smooth; a point moved keeps its automatic tangents; a tangent dragged by hand is no longer automatic;
        kept with the sketches."""
        import tempfile
        from arqbim.core import curves
        from arqbim.model import curve_edit, document
        pts = [(0, 0, 0), (4, 2, 0), (8, 0, 0)]
        anchors = curves.auto_handles([[p] * 3 for p in pts], [True] * 3)
        p, hi, ho = (np.asarray(v) for v in anchors[1])
        self.assertTrue(np.allclose(np.cross(hi - p, ho - p), 0) and float((hi - p) @ (ho - p)) < 0)   # (smooth)
        self.assertAlmostEqual(float(np.linalg.norm(ho - p)), float(np.hypot(4, 2)) / curves.AUTO_HANDLE)
        self.assertTrue(np.allclose(ho - p, (np.linalg.norm(ho - p), 0, 0)))          # (level at the top)
        self.assertTrue(np.allclose(anchors[0][1], anchors[0][0]) and np.allclose(anchors[2][2], anchors[2][0]))
        drawn = curves.bezier_points(anchors, False, 12)
        self.assertTrue(any(np.allclose(q, (4, 2, 0)) for q in drawn))                 # (it passes through it)
        # two points: straight; the «+» halfway dragged 1 m up — a new point there, the curve bent and smooth
        straight = curves.bezier_curve(curves.auto_handles([[(0, 0, 0)] * 3, [(6, 0, 0)] * 3], [True, True]),
                                       (0, 0, 1), auto=[True, True])
        line = SketchObject("B", np.eye(4), PolyMesh(curves.curve_points(straight), lines=[(0, 1)]), curve=straight)
        self.assertTrue(all(abs(q[1]) < 1e-9 for q in curves.curve_points(straight)))
        ends, middles, arrows, what, adds = curve_edit.grips(line)
        self.assertEqual((len(ends), len(adds), what[-1]), (2, 1, ("add", 0)))
        self.assertTrue(np.allclose(adds[0], (3, 0, 0)))
        bent = curve_edit.dragged(line, ("add", 0), (3, 1, 0))
        self.assertEqual((len(bent["anchors"]), bent["auto"]), (3, [True, True, True]))
        drawn = curves.curve_points(bent)
        self.assertAlmostEqual(max(q[1] for q in drawn), 1.0, places=6)                 # (through the point dragged)
        self.assertTrue(all(q[1] > -1e-9 for q in drawn))
        p, hi, ho = (np.asarray(v) for v in bent["anchors"][1])
        self.assertTrue(np.allclose(hi[1], 1.0) and np.allclose(ho[1], 1.0))            # (level at its top: smooth)
        # that point moved on: its tangents (and its neighbours') still automatic
        line2 = SketchObject("B", np.eye(4), PolyMesh(drawn, lines=[(0, 1)]), curve=bent)
        again = curve_edit.dragged(line2, ("anchor", 1), (4, 2, 0))
        p, hi, ho = (np.asarray(v) for v in again["anchors"][1])
        self.assertTrue(np.allclose(np.cross(hi - p, ho - p), 0))
        # a tangent dragged by hand: that point no longer automatic
        by_hand = curve_edit.dragged(line2, ("out", 1), (5, 3, 0))
        self.assertEqual(by_hand["auto"], [True, False, True])
        path = os.path.join(tempfile.mkdtemp(), "c.arqbim")
        document._write_sketches(path, [SketchObject("B", np.eye(4), PolyMesh(drawn, lines=[(0, 1)]), curve=bent)])
        self.assertEqual(document._read_sketches(path)[0][0].curve["auto"], [True, True, True])

    def test_rotation_about_any_axis_and_the_work_plane(self):
        """0.412 (the owner: «um comando rotacionar mais poderoso para rodar em qualquer eixo como o do Blender»; «o
        plano de trabalho… de acordo com eixos… também por seleção de faces»): a turn about X, Y, Z through a centre
        (right hand: about Z as before); its signed angle; the work planes by the axes through a point and by a face;
        where a ray meets them; a sketch turned about X stands up."""
        from arqbim.model import bim, work_plane
        c = np.array((1.0, 2.0, 0.0))
        self.assertTrue(np.allclose(transform.rotation_about(c, (0, 0, 1), 37.0), transform.rotation_about_z(c, 37.0)))
        m = transform.rotation_about(c, (1, 0, 0), 90.0)
        self.assertTrue(np.allclose(m @ (1.0, 3.0, 0.0, 1.0), (1.0, 2.0, 1.0, 1.0)))         # (Y towards Z)
        m = transform.rotation_about((0, 0, 0), (0, 1, 0), 90.0)
        self.assertTrue(np.allclose(m @ (0.0, 0.0, 1.0, 1.0), (1.0, 0.0, 0.0, 1.0)))         # (Z towards X)
        self.assertAlmostEqual(transform.axis_angle((0, 1, 0), (0, 0, 1), (1, 0, 0)), 90.0)
        self.assertAlmostEqual(transform.axis_angle((0, 1, 0), (0, 0, -1), (1, 0, 0)), -90.0)
        xz = work_plane.by_axes("xz", (3.0, 2.0, 1.0))
        self.assertTrue(np.allclose(np.abs(xz.normal), (0, 1, 0)) and np.allclose(xz.u, (1, 0, 0)) and
                        np.allclose(xz.v, (0, 0, 1)))
        self.assertTrue(xz.contains((-5.0, 2.0, 7.0)) and not xz.contains((0.0, 2.5, 0.0)))
        yz = work_plane.by_axes("yz", (4.0, 0.0, 0.0))
        self.assertTrue(np.allclose(yz.u, (0, 1, 0)) and np.allclose(yz.v, (0, 0, 1)))
        self.assertTrue(np.allclose(work_plane.ray_point(xz, (0.0, -8.0, 1.5), (0.0, 1.0, 0.0)), (0.0, 2.0, 1.5)))
        self.assertIsNone(work_plane.ray_point(xz, (0.0, -8.0, 1.5), (1.0, 0.0, 0.0)))     # (along it)
        face = work_plane.by_face((1.0, 1.0, 1.0), (1.0, 1.0, 0.0))
        self.assertAlmostEqual(float(np.linalg.norm(face.normal)), 1.0)
        self.assertTrue(np.allclose(np.cross(face.u, face.v), face.normal))
        doc = Document()
        line = self._lines(doc, [(0, 0, 0), (0, 4, 0)])
        bim.transform_objects(doc, [line.id], transform.rotation_about((0, 0, 0), (1, 0, 0), 90.0), "Rodar")
        pts = [sg.transform_point(doc.get(line.id).matrix, v) for v in doc.get(line.id).mesh.verts]
        self.assertTrue(np.allclose(sorted(p[2] for p in pts), (0.0, 4.0)) and all(abs(p[1]) < 1e-9 for p in pts))

    def test_the_work_plane_is_kept_with_the_project(self):
        """0.413 (the owner: «Sim, guardar»): the work plane set is written to the side file and read back — the model's
        origin moved meanwhile, it stays where it was in the model —; a project saved and opened again has it; a new
        one has none; one not understood is let go."""
        import tempfile
        from arqbim.model import document, work_plane
        plane = work_plane.by_face((1.0, 2.0, 3.0), (0.0, 1.0, 1.0))
        with tempfile.TemporaryDirectory() as tmp:
            side = os.path.join(tmp, "p.arqsynthbim")
            document._write_sketches(side, [], origin=(10.0, 0.0, 0.0), work_plane=plane)
            back = document._read_work_plane(side, origin=(12.0, 0.0, 0.0))
            self.assertEqual(back.kind, "face")
            self.assertTrue(np.allclose(back.origin, (-1.0, 2.0, 3.0)) and np.allclose(back.normal, plane.normal))
            self.assertTrue(np.allclose(back.u, plane.u) and np.allclose(back.v, plane.v))
            document._write_sketches(side, [])
            self.assertIsNone(document._read_work_plane(side))
            self.assertIsNone(work_plane.from_dict({"kind": "xz", "origin": [0, "a", 0]}))
            doc = Document()
            doc.work_plane = work_plane.by_axes("xz", (0.0, 3.0, 0.0))
            path = os.path.join(tmp, "casa.ifc")
            doc.save(path)
            again = Document()
            again.open(path)
            self.assertEqual(again.work_plane.kind, "xz")
            self.assertAlmostEqual(float(again.work_plane.origin[1]), 3.0)
            again.new()
            self.assertIsNone(again.work_plane)

    def test_a_curve_is_saved_with_the_sketches(self):
        import tempfile
        from arqbim.core import curves
        from arqbim.model import document
        c = curves.bezier_curve([[(0, 0, 0)] * 3, [(4, 0, 0), (3, 1, 0), (5, -1, 0)], [(8, 0, 0)] * 3], (0, 0, 1))
        obj = SketchObject("B", np.eye(4), PolyMesh([(0, 0, 0), (8, 0, 0)], lines=[(0, 1)]), curve=c)
        path = os.path.join(tempfile.mkdtemp(), "c.arqbim")
        document._write_sketches(path, [obj])
        back, _guides = document._read_sketches(path)
        self.assertEqual((len(back), back[0].curve), (1, c))


class ParamSurfaceCore(unittest.TestCase):
    """0.395 — the parametric surfaces (the addon's «Superfícies Paramétricas»): formulas read safely, the seven
    ops, the nine modifiers, the nine construction sections, the parts' quantities."""

    @staticmethod
    def circle(r, z, n=48, cx=0.0, cy=0.0):
        a = np.linspace(0, 2 * np.pi, n, endpoint=False)
        return np.column_stack((cx + r * np.cos(a), cy + r * np.sin(a), np.full(n, z)))

    def test_formulas(self):
        from arqbim.core import surface_expr as ex
        c = ex.compile_expression("H*sin(pi*u) + clamp(x, 0, 1) + noise(x, y)", ("H", "u", "x", "y"))
        out = c.evaluate(H=2.0, u=np.array([0.5, 0.0]), x=np.array([0.3, 2.0]), y=np.array([0.1, 0.4]))
        self.assertEqual(out.shape, (2,))
        self.assertAlmostEqual(float(c.evaluate(H=2.0, u=0.5, x=0.3, y=0.1)), float(out[0]))
        n1 = ex.compile_expression("noise(x, y, 0, 7)", ("x", "y")).evaluate(x=1.37, y=-2.5)
        n2 = ex.compile_expression("noise(x, y, 0, 7)", ("x", "y")).evaluate(x=1.37, y=-2.5)
        self.assertEqual(float(n1), float(n2))                       # (the same on every machine)
        self.assertTrue(-1.0 <= float(n1) <= 1.0)
        for bad in ("__import__('os')", "a.b", "[1][0]", "x if x else 1", "2**40", "sqrt(-1)", "foo", "1/0",
                    "sin", "lambda: 1", "x" * 500):
            with self.assertRaises(ex.ExprError):
                ex.compile_expression(bad, ("x",)).evaluate(x=1.0)
        self.assertEqual(ex.number("L/2", {"L": 12.0}), 6.0)

    def test_ops(self):
        from arqbim.core import param_surface as ps
        loft = ps.from_curves([(self.circle(6, 0), True, None), (self.circle(4, 3), True, None),
                               (self.circle(2, 5, 40), True, None)])
        self.assertEqual(loft["surface"]["op"], "loft")
        s = ps.Surface(loft)
        self.assertTrue(s.close_u)
        self.assertAlmostEqual(float(s.rows[..., 2].max()), 5.0, places=6)
        # anti-twist: a section drawn the other way round and from another start makes the same surface
        turned = np.roll(self.circle(4, 3)[::-1], 7, axis=0)
        s2 = ps.Surface(ps.from_curves([(self.circle(6, 0), True, None), (turned, True, None),
                                        (self.circle(2, 5, 40), True, None)]))
        self.assertAlmostEqual(s.area(), s2.area(), delta=s.area() * 0.01)
        line = lambda a, b: np.linspace(a, b, 8)                                           # noqa: E731
        edges = [(line((0, 0, 0), (10, 0, 2)), False, None), (line((10, 0, 2), (10, 8, 0)), False, None),
                 (line((10, 8, 0), (0, 8, 2)), False, None), (line((0, 8, 2), (0, 0, 0)), False, None)]
        coons = ps.from_curves(edges)
        self.assertEqual(coons["surface"]["op"], "coons")             # (4 that touch at their ends)
        self.assertGreater(ps.Surface(coons).area(), 80.0)
        far = [(line((0, 0, 0), (10, 0, 2)), False, None), (line((10, 0, 2), (10, 8, 0)), False, None),
               (line((10, 8, 0), (0, 8, 2)), False, None), (line((0, 9, 2), (0, 1, 0)), False, None)]
        with self.assertRaises(ps.SurfaceError):
            ps.Surface(ps.from_curves(far, op="coons"))                # (they do not meet: refused in words)
        prof = np.column_stack((np.linspace(1, 5, 12), np.zeros(12), 4 * np.sin(np.linspace(0, np.pi, 12))))
        rev = ps.Surface(ps.from_curves([(prof, False, None)], op="revolve"))
        self.assertTrue(rev.close_u)
        ext = ps.Surface(ps.from_curves([(line((0, 0, 0), (10, 0, 0)), False, None)], op="extrude",
                                        direction=[0.0, 0.0, 3.0]))
        self.assertAlmostEqual(ext.area(), 30.0, places=3)
        path = np.column_stack((np.linspace(0, 12, 30), np.zeros(30), np.zeros(30)))
        sweep = ps.Surface(ps.from_curves([(path, False, None), (self.circle(1.0, 0, 64), True, None)], op="sweep"))
        self.assertAlmostEqual(sweep.area(), 2 * np.pi * 12.0, delta=1.0)        # (a tube 12 m long, radius 1)
        blob = self.circle(7, 0, 64) * np.array([1.4, 1.0, 1.0])
        for form in ("cupula", "abobada", "cosseno", "plano"):
            cap = ps.Surface(ps.from_curves([(blob, True, None)], op="patch", form=form, rise=2.0))
            top = float(cap.rows[..., 2].max())
            self.assertAlmostEqual(top, 0.0 if form == "plano" else 2.0, delta=0.15, msg=form)
        grid = ps.Surface(ps.default_definition("grid"))
        self.assertEqual(grid.shape, (21, 33))
        self.assertAlmostEqual(float(grid.rows[..., 2].max()), 1.2, delta=0.01)

    def test_modifiers(self):
        from arqbim.core import param_surface as ps
        base = ps.Surface(ps.default_definition("grid"))
        for op in ps.MODIFIERS:
            d = ps.default_definition("grid")
            m = dict({"op": op}, **ps.MODIFIER_TEMPLATES[op])
            if op == "trim":
                d["curves"] = [{"id": "t", "points": self.circle(4, 0, 32, 6, 4).tolist(), "closed": True}]
                m["curve"] = "t"
            if op == "attractor":
                m["point"] = [6, 4, 0]
            d["modifiers"] = [m]
            self.assertEqual(ps.validate(d), [], op)
            s = ps.Surface(d)
            verts, tris = s.triangles()
            self.assertTrue(len(tris), op)
            if op != "trim":
                self.assertGreater(float(np.abs(s.rows - base.rows).max()), 1e-3, op)     # (it did something)
            d["modifiers"][0]["enabled"] = False
            self.assertTrue(np.allclose(ps.Surface(d).rows, base.rows), op)                 # (off: nothing)
        bad = ps.default_definition("grid")
        bad["modifiers"] = [{"op": "twist", "axis": "w"}]
        self.assertTrue(ps.validate(bad))

    def test_construction(self):
        from arqbim.core import param_surface as ps
        from arqbim.core import surface_build as sb
        d = ps.from_curves([(self.circle(6, 3), True, None), (self.circle(4, 6), True, None),
                            (self.circle(2, 8, 40), True, None)])
        for name in sb.SECTIONS:
            d["build"] = {name: dict(sb.TEMPLATES[name])}
            if name == "supports":
                d["build"][name]["base_z"] = 0.0
            pieces, parts, _w = sb.build(ps.Surface(d))
            self.assertTrue(pieces, name)
            for verts, tris in pieces.values():
                self.assertTrue(len(tris) and tris.min() >= 0 and tris.max() < len(verts), name)
            self.assertTrue(parts, name)
        # the gridshell's cut list: its bars by length to the mm, the nodes as hardware
        d["build"] = {"gridshell": dict(sb.TEMPLATES["gridshell"], mode="quad", u=12, v=6)}
        _p, parts, _w = sb.build(ps.Surface(d))
        q = sb.quantities(parts)
        self.assertEqual(q["no"]["count"], 12 * 7)
        self.assertEqual(q["barra"]["count"], 12 * 7 + 12 * 6)          # (round: as many across as nodes)
        # panels: a joint exactly as asked between neighbours, the warp measured; framed: frame + glass
        g = ps.default_definition("grid")
        g["build"] = {"panels": dict(sb.TEMPLATES["panels"], u=4, v=3, gap=0.02, frame=0.05)}
        pieces, parts, _w = sb.build(ps.Surface(g))
        self.assertEqual(sum(1 for p in parts if p["kind"] == "vidro"), 12)
        self.assertIn("vidro", pieces)
        self.assertIn("aluminio", pieces)
        sq = np.array([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], float)
        inner = sb.inset(sq, 0.1)
        self.assertTrue(np.allclose(inner, [(0.1, 0.1, 0), (0.9, 0.1, 0), (0.9, 0.9, 0), (0.1, 0.9, 0)]))
        warped = sq.copy()
        warped[3, 2] = 0.05
        self.assertAlmostEqual(sb.panel_warp(warped), 0.05)
        # fine perforation: real holes, the open area summed
        g["build"] = {"panels": dict(sb.TEMPLATES["panels"], u=2, v=2, perf=True, perf_spacing=0.3)}
        _p, parts, warns = sb.build(ps.Surface(g))
        self.assertTrue(any(p.get("holes") for p in parts))
        self.assertTrue(any("furo" in w for w in warns))


class DimensionLayout(unittest.TestCase):
    """0.398: one drawer for every dimension (core/dim_layout) — the values as a type writes them, a string's lines,
    marks and texts as its type draws them."""

    def setUp(self):
        from arqbim.core import dim_layout
        self.dl = dim_layout

    def _string(self, xs, style=None, mm=0.05, depth=-0.8):
        """A chain along x through xs, measured on y=0, its line at y=depth; at 1:50 (mm = 0.05 m)."""
        dl = self.dl
        style = dl.clean(style or {})
        pieces = [dl.Piece(np.array((a, 0.0)), np.array((b, 0.0)), np.array((a, depth)), np.array((b, depth)),
                           dl.label(b - a, style), k) for k, (a, b) in enumerate(zip(xs, xs[1:]))]
        return dl.string(pieces, style, mm)

    def test_values(self):
        dl = self.dl
        self.assertEqual(dl.number(2.475, dl.clean({})), ("2,48", ""))
        self.assertEqual(dl.number(2.475, dl.clean({"sup_mm": True})), ("2,47", "5"))     # the mm raised
        self.assertEqual(dl.number(2.47, dl.clean({"sup_mm": True})), ("2,47", ""))       # (none to raise)
        self.assertEqual(dl.number(2.475, dl.clean({"unit": "cm", "decimals": 0, "sup_mm": True})), ("247", "5"))
        self.assertEqual(dl.number(2.4762, dl.clean({"unit": "cm", "decimals": 0, "rounding": 50})), ("250", ""))
        self.assertEqual(dl.number(2.4762, dl.clean({"unit": "mm", "decimals": 0})), ("2476", ""))
        self.assertEqual(dl.number(0.825, dl.clean({"unit": "cm", "decimals": 0})), ("83", ""))   # (half up)
        self.assertEqual(dl.number(0.125, dl.clean({})), ("0,13", ""))
        words = dl.label(2.475, dl.clean({"sup_mm": True, "unit_symbol": True, "prefix": "≈"}))
        self.assertEqual([r[0] for r in words.runs], ["≈2,47", "5", " m"])
        self.assertEqual(words.plain, "≈2,47⁵ m")
        self.assertEqual(dl.label(3.0, dl.clean({}), eq=True).plain, "IG")
        self.assertEqual(dl.label(3.0, dl.clean({}), override="VAR").plain, "VAR")
        clean = dl.clean({"mark": "nope", "text": 99, "colour": "red", "rounding": 4, "bold": 1, "font": "Arial"})
        self.assertEqual((clean["mark"], clean["text"], clean["colour"], clean["rounding"], clean["bold"],
                          clean["font"]), ("tick", 10.0, "#000000", 5.0, True, "Arial"))

    def test_a_chain_shares_its_extension_lines_and_ticks(self):
        out = self._string([0.0, 1.2, 1.35, 4.0])                  # (0,15: too short for its value at 1:50)
        pen = [ln for ln in out.lines]
        witness = [ln for ln in pen if abs(ln[0][0] - ln[1][0]) < 1e-9 and min(ln[0][1], ln[1][1]) < -0.8]
        self.assertEqual(len(witness), 4)                           # one per point: shared between neighbours
        ticks = [ln for ln in pen if abs(abs(ln[1][0] - ln[0][0]) - abs(ln[1][1] - ln[0][1])) < 1e-9
                 and abs(ln[1][0] - ln[0][0]) > 1e-9]
        self.assertEqual(len(ticks), 4)                             # one tick at each point, at 45°
        texts = {t.text: t for t in out.texts}
        self.assertEqual(set(texts), {"1,20", "0,15", "2,65"})
        self.assertGreater(texts["0,15"].at[1], texts["1,20"].at[1] + 0.05)     # (raised: it does not fit)
        self.assertAlmostEqual(texts["1,20"].at[0], 0.6)                         # (the others over their middle)
        self.assertTrue(all(t.at[1] > -0.8 for t in out.texts))                  # (over the line, read from below)
        self.assertAlmostEqual(texts["1,20"].height, 2.2 * 0.05)                 # (its height at the scale)

    def test_marks_and_the_text_in_the_line(self):
        dl = self.dl
        arrows = self._string([0.0, 2.0, 2.1], {"mark": "arrow"})
        self.assertEqual(len(arrows.fills), 4)                      # an arrow at each end of each piece
        # (the 0,10 piece: too short for two arrows inside — they point in from outside)
        short = {round(float(f[0][0][0]), 3): float(f[0][0][0] - f[0][1][0]) for f in arrows.fills if f[2] == 1}
        self.assertGreater(short[2.0], 0)                          # at its left end, pointing right
        self.assertLess(short[2.1], 0)                             # at its right end, pointing left
        long = {round(float(f[0][0][0]), 3): float(f[0][0][0] - f[0][1][0]) for f in arrows.fills if f[2] == 0}
        self.assertLess(long[0.0], 0)                              # (inside: pointing out)
        self.assertGreater(long[2.0], 0)
        self.assertEqual(len(self._string([0.0, 2.0], {"mark": "dot"}).fills), 2)
        self.assertEqual(len(self._string([0.0, 2.0], {"mark": "none"}).fills), 0)
        centred = self._string([0.0, 3.0], {"text_place": "centre", "line_over": 2.0})
        along = [ln for ln in centred.lines if abs(ln[0][1] + 0.8) < 1e-9 and abs(ln[1][1] + 0.8) < 1e-9]
        xs = sorted((float(min(a[0], b[0])), float(max(a[0], b[0]))) for a, b, *_r in along)
        self.assertTrue(any(lo < 1.5 - 0.05 for lo, hi in xs) and any(hi > 1.5 + 0.05 for lo, hi in xs))
        self.assertFalse(any(lo < 1.5 < hi for lo, hi in xs))      # (a gap where its value is)
        self.assertTrue(any(lo < -0.09 for lo, _hi in xs) and any(hi > 3.09 for _lo, hi in xs))   # (on past the ends)
        self.assertEqual(len(centred.backs), 1)
        level = self.dl.string([dl.Piece(np.array((0.0, 0.0)), np.array((0.0, 3.0)), np.array((-0.8, 0.0)),
                                         np.array((-0.8, 3.0)), dl.label(3.0, dl.clean({})), 0)],
                               dl.clean({"reading": "horizontal"}), 0.05)
        self.assertEqual(level.texts[0].angle, 0.0)
        along_y = self.dl.string([dl.Piece(np.array((0.0, 0.0)), np.array((0.0, 3.0)), np.array((-0.8, 0.0)),
                                           np.array((-0.8, 3.0)), dl.label(3.0, dl.clean({})), 0)],
                                 dl.clean({}), 0.05)
        self.assertAlmostEqual(along_y.texts[0].angle, 90.0)        # (read from the right)
        self.assertLess(along_y.texts[0].at[0], -0.8)               # (on its left, as read)
        heavy = self._string([0.0, 2.0], {"mark": "tick_heavy"})
        self.assertTrue(any(ln[2] == dl.HEAVY_PEN for ln in heavy.lines))

    def test_raised_mm_and_the_opening_height(self):
        dl = self.dl
        style = dl.clean({"sup_mm": True})
        words = dl.label(0.825, style, below="2,10")
        out = dl.string([dl.Piece(np.array((0.0, 0.0)), np.array((0.825, 0.0)), np.array((0.0, -0.8)),
                                  np.array((0.825, -0.8)), words, 0)], style, 0.02)
        texts = {t.text: t for t in out.texts}
        self.assertEqual(set(texts), {"0,82", "5", "2,10"})
        self.assertLess(texts["5"].height, texts["0,82"].height)
        self.assertGreater(texts["5"].at[1], texts["0,82"].at[1])  # (raised)
        self.assertGreater(texts["5"].at[0], texts["0,82"].at[0])  # (after it)
        self.assertLess(texts["2,10"].at[1], -0.8)                 # (under the line)


if __name__ == "__main__":
    unittest.main()
