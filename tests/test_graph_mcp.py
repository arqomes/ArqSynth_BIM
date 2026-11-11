"""0.543 — Gráfico Visual, step 6: the AI's tools (graph_nodes, graph, graph_eval, graph_apply)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from arqbim.mcp import tools  # noqa: E402
from arqbim.mcp.protocol import Server, ToolError  # noqa: E402


class GraphTools(unittest.TestCase):
    def setUp(self):
        self.s = tools.Session()

    def run_tool(self, name, **args):
        return tools.run(self.s, name, args)

    def test_listed(self):
        names = [d[0] for d in tools.definitions()]
        for n in ("graph_nodes", "graph", "graph_eval", "graph_apply"):
            self.assertIn(n, names)
        text = self.run_tool("graph_nodes")
        self.assertIn("voronoi Padrões painel,densidade>pontos", text)
        self.assertIn("d_max=0.03[0.001..0.2]", self.run_tool("graph_nodes", key="perfurar"))

    def test_build_and_evaluate(self):
        self.run_tool("graph", action="new")
        p = self.run_tool("graph", action="add", type="painel_plano", params={"largura": 1.2}).split()[-1]
        v = self.run_tool("graph", action="add", type="voronoi", params={"quantidade": 200}).split()[-1]
        a = self.run_tool("graph", action="add", type="atrator", params={"x": 0.6, "y": 0.6}).split()[-1]
        f = self.run_tool("graph", action="add", type="perfurar", params={"d_max": 0.04}).split()[-1]
        c = self.run_tool("graph", action="add", type="verificar_fabrico").split()[-1]
        for frm, to in ((p + ".painel", v + ".painel"), (a + ".campo", v + ".densidade"),
                        (v + ".pontos", f + ".pontos"), (f + ".furos", c + ".furos")):
            shown = self.run_tool("graph", action="connect", **{"from": frm, "to": to})
        self.assertIn("{}.furos>{}.furos".format(f, c), shown)
        self.assertIn("largura=1.2", shown)
        with self.assertRaises(ToolError):
            self.run_tool("graph", action="connect", **{"from": p + ".painel", "to": f + ".pontos"})
        out = tools.run(self.s, "graph_eval", {"path": os.path.join(tempfile.mkdtemp(), "g.png")})
        self.assertIsInstance(out, dict)
        self.assertIn("{} ".format(c), out["text"])
        self.assertIn("holes=200", out["text"])
        self.assertTrue(os.path.getsize(out["png"]) > 1000)

    def test_protocol_sends_the_picture(self):
        server = Server("t", "0", tools.tools(self.s))
        self.run_tool("graph", action="template", key="atrator_hexagono")
        answer = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                "params": {"name": "graph_eval", "arguments": {}}})
        kinds = [c["type"] for c in answer["result"]["content"]]
        self.assertEqual(kinds, ["text", "image"])

    def test_apply_to_wall(self):
        made = self.run_tool("create", kind="wall", params={"a": [0, 0], "b": [4, 0]})
        wall = made.split()[1] if made.split()[1].startswith("#") else made.split()[-1]
        self.run_tool("graph", action="template", key="atrator_hexagono")
        text = self.run_tool("graph_apply", wall=wall)
        self.assertTrue(text.startswith("made #"), text)


if __name__ == "__main__":
    unittest.main()
