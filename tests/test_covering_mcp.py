"""0.570 — Gerador de revestimentos, step 10: the AI's tool «covering» (keys, lay, edit, qty)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "."), "arqbim_test_cache"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from arqbim.mcp import tools  # noqa: E402


class CoveringTool(unittest.TestCase):
    def setUp(self):
        self.s = tools.Session()

    def run_tool(self, name, **args):
        return tools.run(self.s, name, args)

    def test_listed_and_used(self):
        self.assertIn("covering", [d[0] for d in tools.definitions()])
        self.assertIn("azulejo_30x60", self.run_tool("covering", do="keys", opt={"group": "ceramico"}))
        made = self.run_tool("create", kind="wall", params={"a": [0, 0], "b": [4, 0]})
        wall = next(w for w in made.replace(",", " ").split() if w.startswith("#"))
        out = self.run_tool("covering", do="lay", id=wall, normal=[0, -1, 0], finish="metro_10x20")
        self.assertTrue(out.startswith("#"))
        edited = self.run_tool("covering", do="edit", id=out.split()[0], layout={"pattern": "espinha_reta"})
        self.assertIn("pieces=", edited)
        folder = tempfile.mkdtemp()
        q = self.run_tool("covering", do="qty", opt={"dxf": os.path.join(folder, "p.dxf")})
        self.assertIn("area=", q)
        self.assertTrue(os.path.exists(os.path.join(folder, "p.dxf")))


if __name__ == "__main__":
    unittest.main()
