"""0.488 — The ArqSynth Presentation's Virtual Walk worked out in the BIM (model/presentation_walk.py)."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arqbim.model import presentation_walk as pw  # noqa: E402


def spaces():
    """The Presentation's own test house (scripts/test-bim-import.mts): a living room and a kitchen with a door between
    them and one from outside into the kitchen, a hall upstairs by a stair; a box room with no door."""
    return {"rooms": [
        {"id": "S", "name": "Sala", "outline": [[0, 0], [4, 0], [4, -4], [0, -4]], "level": 0, "center": [2, 0, -2]},
        {"id": "C", "name": "Cozinha", "outline": [[4, 0], [6, 0], [6, -4], [4, -4]], "level": 0, "center": [5, 0, -2]},
        {"id": "H", "name": "Hall", "outline": [[0, 0], [4, 0], [4, -2], [0, -2]], "level": 3, "center": [2, 3, -1]},
        {"id": "Q", "name": "Arrumos", "outline": [[6, 0], [7, 0], [7, -1], [6, -1]], "level": 0,
         "center": [6.5, 0, -0.5]}],
        "doors": [{"id": "D1", "point": [4, 0, -2], "way": [1, 0, 0], "from": "S", "to": "C"},
                  {"id": "D2", "point": [5, 0, 0], "way": [0, 0, 1], "from": "C", "to": None}],
        "stairs": [{"id": "E1", "from": "S", "to": "H", "points": [[1, 0, -3], [1, 3, -0.5]]}],
        "start": "C"}


class Walk(unittest.TestCase):
    def test_links_and_start(self):
        """The rooms linked by the doors between two of them and by the stairs; the start: the one chosen, else the
        description's, else the first — none left out."""
        sp = spaces()
        graph = pw.links(sp)
        self.assertEqual(sorted(b for b, _p in graph["S"]), ["C", "H"])
        self.assertEqual([b for b, _p in graph["C"]], ["S"])
        self.assertEqual(graph["Q"], [])
        _to, through = graph["S"][0]
        np.testing.assert_allclose(through[2], (4, 0, -2))                      # (through the door's middle)
        np.testing.assert_allclose(through[1], (4 - 0.6, 0, -2))                # (from 0,6 m before it)
        self.assertEqual(pw.start_of(sp), "C")
        self.assertEqual(pw.start_of(sp, "H"), "H")
        self.assertEqual(pw.start_of(sp, "", off=["C"]), "S")
        self.assertNotIn("S", pw.links(sp, off=["S"]))
        self.assertEqual(pw.counts(sp), (4, 1, 1))

    def test_tour_and_path(self):
        """The guided tour from the start through the doors (depth first, the nearest first), the rooms it cannot reach
        apart; the way between two rooms the shortest, from the middle of one to the middle of the other."""
        sp = spaces()
        self.assertEqual(pw.tour(sp, "C"), (["C", "S", "H"], ["Q"]))
        self.assertEqual(pw.tour(sp, "C", off=["S"]), (["C"], ["H", "Q"]))
        way = pw.path(sp, "C", "H")
        np.testing.assert_allclose(way[0], (5, 0, -2))
        np.testing.assert_allclose(way[-1], (2, 3, -1))
        self.assertTrue(any(np.allclose(p, (4, 0, -2)) for p in way))           # (through the door)
        self.assertTrue(any(np.allclose(p, (1, 3, -0.5)) for p in way))         # (up the stair)
        self.assertIsNone(pw.path(sp, "C", "Q"))
        self.assertIsNone(pw.path(sp, "C", "H", off=["S"]))

    def test_frames(self):
        """The camera walking the tour: in the first room at a person's eye (1,65 m) for the time in each room, along
        the ways at 1,4 m/s, looking along them; in the last room at its end. In the model's axes by to_model."""
        sp = spaces()
        fps = 10
        frames = pw.frames(sp, ["C", "S"], fps=fps, dwell=1.0)
        eye, target = frames[0]
        np.testing.assert_allclose(eye, (5, 1.65, -2))
        np.testing.assert_allclose(frames[-1][0], (2, 1.65, -2))
        legs = pw._length(pw.path(sp, "C", "S"))
        self.assertAlmostEqual(len(frames), 2 * fps + legs / (1.4 / fps), delta=8)
        k = fps + 3                                                              # (walking west, to the door)
        d = np.asarray(frames[k][1]) - np.asarray(frames[k][0])
        self.assertLess(d[0], 0.0)
        self.assertEqual(pw.frames(sp, ["C", "Q"], fps=fps, dwell=1.0)[-1], frames[fps - 1])   # (no way: stops)
        self.assertEqual(pw.to_model((1.0, 2.0, -3.0)), (1.0, 3.0, 2.0))
        self.assertEqual(pw.frames(sp, []), [])


if __name__ == "__main__":
    unittest.main()
