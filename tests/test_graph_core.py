"""0.538 — Gráfico Visual, step 1: the node registry, links, working out with a cache, JSON."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arqbim.core.graph import Graph, GraphError, Port, Registry  # noqa: E402


def _registry(calls):
    r = Registry()

    @r.node("num", "Base", "Número", "Um número.", outputs=[Port("valor", "number")],
            params=[Port("v", "number", default=1.0, min=0.0, max=10.0)])
    def num(v):
        calls.append("num")
        return {"valor": v}

    @r.node("soma", "Operações", "Soma", "a + b.", inputs=[Port("a", "number"), Port("b", "number", default=0.0,
            optional=True)], outputs=[Port("valor", "number")])
    def soma(a, b):
        calls.append("soma")
        return {"valor": a + b}

    @r.node("txt", "Base", "Texto", "Um texto.", outputs=[Port("t", "text")],
            params=[Port("modo", "choice", default="a", choices=("a", "b"))])
    def txt(modo):
        return {"t": modo}

    @r.node("falha", "Operações", "Falha", "Falha sempre.", inputs=[Port("a", "number")],
            outputs=[Port("valor", "number")])
    def falha(a):
        raise ValueError("furo pequeno demais")

    return r


class GraphCore(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.g = Graph(_registry(self.calls))

    def test_evaluate_and_cache(self):
        a = self.g.add_node("num", {"v": 2})
        b = self.g.add_node("num", {"v": 3})
        s = self.g.add_node("soma")
        self.g.connect(a, "valor", s, "a")
        self.g.connect(b, "valor", s, "b")
        self.assertEqual(self.g.evaluate()[s]["valor"], 5)
        self.calls.clear()
        self.g.evaluate()
        self.assertEqual(self.calls, [])                       # nothing changed: nothing worked again
        self.g.set_param(a, "v", 4)
        self.assertEqual(self.g.evaluate()[s]["valor"], 7)
        self.assertEqual(sorted(self.calls), ["num", "soma"])  # only the changed node and what follows it

    def test_limits_and_choices(self):
        a = self.g.add_node("num")
        self.assertEqual(self.g.set_param(a, "v", 99), 10.0)
        t = self.g.add_node("txt")
        with self.assertRaises(ValueError):
            self.g.set_param(t, "modo", "c")

    def test_kinds_cycles_and_optional(self):
        a, t, s, s2 = (self.g.add_node(k) for k in ("num", "txt", "soma", "soma"))
        with self.assertRaises(GraphError):
            self.g.connect(t, "t", s, "a")                     # text into a number
        self.g.connect(a, "valor", s, "a")
        self.g.connect(s, "valor", s2, "a")
        with self.assertRaises(GraphError):
            self.g.connect(s2, "valor", s, "b")                # a cycle
        self.assertEqual(self.g.evaluate()[s2]["valor"], 1.0)  # "b" optional, default 0

    def test_errors_stop_downstream(self):
        a, f, s = self.g.add_node("num"), self.g.add_node("falha"), self.g.add_node("soma")
        self.g.connect(a, "valor", f, "a")
        self.g.connect(f, "valor", s, "a")
        out = self.g.evaluate()
        self.assertIn(a, out)
        self.assertEqual(self.g.errors[f], "furo pequeno demais")
        self.assertIn(f, self.g.errors[s])
        lonely = self.g.add_node("soma")
        self.g.evaluate()
        self.assertIn("falta ligar", self.g.errors[lonely])

    def test_json_round_trip(self):
        a = self.g.add_node("num", {"v": 6}, pos=(10, 20))
        s = self.g.add_node("soma")
        self.g.connect(a, "valor", s, "a")
        text = self.g.to_json()
        g2 = Graph.from_json(text, self.g.registry)
        self.assertEqual(g2.to_json(), text)
        self.assertEqual(g2.evaluate()[s]["valor"], 6)
        self.assertNotIn(g2.add_node("num"), (a, s))           # new ids don't repeat old ones
        with self.assertRaises(GraphError):
            Graph.from_dict({"format": "outro"}, self.g.registry)

    def test_catalog(self):
        cat = self.g.registry.catalog()
        self.assertEqual([c["family"] for c in cat], ["Base", "Base", "Operações", "Operações"])
        num = next(c for c in cat if c["key"] == "num")
        self.assertEqual(num["params"][0]["max"], 10.0)

    def test_remove_node(self):
        a, s = self.g.add_node("num"), self.g.add_node("soma")
        self.g.connect(a, "valor", s, "a")
        self.g.remove_node(a)
        self.assertEqual(self.g.links, [])


if __name__ == "__main__":
    unittest.main()
