"""0.486 — The ArqSynth Presentation's scene effects worked out as it plays them (model/presentation_effects.py)."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arqbim.model import presentation_effects as fx  # noqa: E402


def unit(uid, name, category, low, high):
    low, high = np.asarray(low, dtype=float), np.asarray(high, dtype=float)
    return {"id": uid, "name": name, "category": category, "low": tuple(low), "high": tuple(high),
            "centre": tuple((low + high) / 2.0)}


class Phases(unittest.TestCase):
    def test_phase_of(self):
        """The Presentation's phases by the words of the name and the category (no accents, no capitals); the
        storey of the BIM's folders («Paredes · Piso 0») does not make everything the structure."""
        name = lambda k: fx.phase_name(k)                                       # noqa: E731
        self.assertEqual(name(fx.phase_of("Parede exterior")), "walls")
        self.assertEqual(name(fx.phase_of("PILAR P12")), "structure")
        self.assertEqual(name(fx.phase_of("Geom3D_6", "Fundações")), "foundation")
        self.assertEqual(name(fx.phase_of("Sofá da sala")), "fixtures")
        self.assertEqual(fx.phase_of("Component#3483"), fx.UNMATCHED)
        self.assertEqual(name(fx.phase_of("Component#3483")), "other")
        self.assertEqual(name(fx.phase_of("Parede 1", "Paredes · Piso 0")), "walls")
        self.assertEqual(name(fx.phase_of("Porta 1", "Portas · Piso 1")), "openings")
        self.assertEqual(name(fx.phase_of("Peça 7", "Diversos · Fundações")), "foundation")

    def test_order(self):
        """The order of the works: phase, then the lowest, then the name; «Outros» between the walls and the
        openings."""
        units = [unit("door", "Porta 1", "Portas · Piso 0", (0, 0, 0), (1, 0.2, 2.1)),
                 unit("roof", "Cobertura", "Coberturas · Piso 1", (0, 0, 3), (6, 4, 4)),
                 unit("w_up", "Parede 2", "Paredes · Piso 1", (0, 0, 3), (6, 0.2, 6)),
                 unit("w_b", "Parede B", "Paredes · Piso 0", (0, 0, 0), (6, 0.2, 3)),
                 unit("w_a", "Parede A", "Paredes · Piso 0", (0, 0, 0), (6, 0.2, 3)),
                 unit("slab", "Laje 1", "Lajes · Piso 0", (0, 0, -0.2), (6, 4, 0)),
                 unit("odd", "Coisa", "", (0, 0, 0), (1, 1, 1))]
        self.assertEqual(fx.order(units), ["slab", "w_a", "w_b", "w_up", "odd", "door", "roof"])

    def test_random_as_the_presentation(self):
        """mulberry32: the Presentation's numbers (worked out by its own code in Node)."""
        for seed, numbers in ((1, (0.627073940588, 0.002735721180, 0.527447039960, 0.981050967472)),
                              (12345, (0.979728267761, 0.306752264500, 0.484205421526, 0.817934412509)),
                              (40055, (0.102167483186, 0.032710884698, 0.170823019464, 0.133256408852))):
            rnd = fx.seeded_random(seed)
            np.testing.assert_allclose([rnd() for _ in range(4)], numbers, atol=1e-11)


class Plans(unittest.TestCase):
    def setUp(self):
        self.units = [unit("slab", "Laje 1", "Lajes · Térreo", (0, 0, -0.2), (6, 4, 0)),
                      unit("wall", "Parede 1", "Paredes · Térreo", (0, 0, 0), (6, 0.2, 3)),
                      unit("ground", "Terreno", "Terreno", (-10, -10, -1), (16, 14, 0)),
                      unit("door", "Porta 1", "Portas · Térreo", (2, 0, 0), (3, 0.2, 2.1))]
        self.centre, self.radius = (3.0, 2.0, 1.0), 10.0

    def test_construction(self):
        """Each element in the order of the works, a share of the time each (2,5 / n, between 8 % and 50 %), spread
        over it; the terrain and the foundations rise from below (90 % of their height), the rest comes down (60 % of
        its height and 6 % of the model's radius); unseen until it starts."""
        moves = fx.plan("construction", self.units, self.centre, self.radius)
        self.assertEqual([m["id"] for m in moves], ["ground", "slab", "wall", "door"])
        frac = 2.5 / 4 if 2.5 / 4 < 0.5 else 0.5
        self.assertEqual([round(m["start"], 6) for m in moves], [round(k / 3 * (1 - frac), 6) for k in range(4)])
        ground, slab, wall = moves[0], moves[1], moves[2]
        self.assertEqual(ground["way"], (0.0, 0.0, -1.0))
        self.assertAlmostEqual(ground["amplitude"], 0.9)
        self.assertEqual(wall["way"], (0.0, 0.0, 1.0))
        self.assertAlmostEqual(wall["amplitude"], 3.0 * 0.6 + 10.0 * 0.06)
        self.assertAlmostEqual(slab["amplitude"], 0.2 * 0.6 + 0.6)
        self.assertTrue(all(m["hide"] for m in moves))
        offsets, seen = fx.at(moves, 0.0)
        self.assertEqual(seen.tolist(), [True, False, False, False])
        np.testing.assert_allclose(offsets[0], (0.0, 0.0, -0.9))                  # (the terrain: below, rising)
        offsets, seen = fx.at(moves, 1.0)
        self.assertTrue(seen.all())
        np.testing.assert_allclose(offsets, 0.0)                                   # (all in place at the end)

    def test_explode(self):
        """Each element away from the model's middle (its own way, a fixed jitter), back in an order that looks
        random — the same each time —, a distance of spread × radius × (0,55–1,1); seen from the start."""
        moves = fx.plan("explode", self.units, self.centre, self.radius, spread=2.0)
        again = fx.plan("explode", self.units, self.centre, self.radius, spread=2.0)
        self.assertEqual(moves, again)
        self.assertEqual([m["id"] for m in moves], [u["id"] for u in self.units])
        for m, u in zip(moves, self.units):
            self.assertAlmostEqual(np.linalg.norm(m["way"]), 1.0)
            self.assertTrue(2.0 * 10.0 * 0.55 <= m["amplitude"] <= 2.0 * 10.0 * 1.1)
            self.assertTrue(0.0 <= m["start"] <= 0.55 and abs(m["end"] - m["start"] - 0.45) < 1e-12)
            self.assertFalse(m["hide"])
        wall = moves[1]                                                             # (the wall is south: it goes south)
        self.assertLess(wall["way"][1], 0.0)
        _offsets, seen = fx.at(moves, 0.0)
        self.assertTrue(seen.all())
        self.assertEqual(fx.plan("explode", [], self.centre, self.radius), [])
        self.assertEqual(fx.seconds_of(0), 6.0)
        self.assertEqual(fx.seconds_of(0.4), 1.0)


if __name__ == "__main__":
    unittest.main()
