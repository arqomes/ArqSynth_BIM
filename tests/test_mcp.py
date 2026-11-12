"""The MCP server (0.268): the protocol (initialize, tools/list, tools/call, errors, notifications), the tools on a
model (a house made, read back as a table, a door, its IFC data, a change, undone, saved and opened again), a real
session through stdin / stdout, and what it costs to read its tools."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arqbim.mcp.protocol import Server  # noqa: E402
from arqbim.mcp.tools import INSTRUCTIONS, Session, tools  # noqa: E402


def _read(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def call(server, name, arguments=None, mid=1):
    answer = server.handle({"jsonrpc": "2.0", "id": mid, "method": "tools/call",
                            "params": {"name": name, "arguments": arguments or {}}})
    result = answer["result"]
    return result["content"][0]["text"], result["isError"]


class McpProtocol(unittest.TestCase):
    """initialize agrees the client's version (an unknown one: the newest), says its tools and a few words of how
    to use them; ping; tools/list with read-only hints; an unknown method: -32601; a notification: no answer; the
    tool list short (what every request of the AI carries)."""

    def setUp(self):
        self.server = Server("arqsynth-bim", "test", tools(Session()), INSTRUCTIONS)

    def test_protocol(self):
        init = self.server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                   "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                                              "clientInfo": {"name": "t", "version": "1"}}})["result"]
        self.assertEqual(init["protocolVersion"], "2025-03-26")
        self.assertIn("tools", init["capabilities"])
        self.assertTrue(init["instructions"])
        newer = self.server.handle({"jsonrpc": "2.0", "id": 2, "method": "initialize",
                                    "params": {"protocolVersion": "2099-01-01"}})["result"]
        self.assertEqual(newer["protocolVersion"], "2025-06-18")
        self.assertIsNone(self.server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertEqual(self.server.handle({"jsonrpc": "2.0", "id": 3, "method": "ping"})["result"], {})
        listed = self.server.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/list"})["result"]["tools"]
        names = [t["name"] for t in listed]
        self.assertEqual(names, ["summary", "query", "get", "create", "edit", "delete", "undo", "file",
                                 "graph_nodes", "graph", "graph_eval", "graph_apply",     # (0.543: the Visual Graph)
                                 "covering"])                                             # (0.570: Revestimentos)
        self.assertTrue(next(t for t in listed if t["name"] == "query")["annotations"]["readOnlyHint"])
        self.assertEqual(self.server.handle({"jsonrpc": "2.0", "id": 5, "method": "nope"})["error"]["code"], -32601)
        size = len(json.dumps(listed, ensure_ascii=False, separators=(",", ":")))
        self.assertLess(size, 4600)                         # (about a thousand tokens, all the tools; 0.570: one
        #                                                      more tool for the Revestimentos, ~150 tokens)


class McpTools(unittest.TestCase):
    """A house of four walls made in one call; the summary; the walls as a table with their IsExternal; a door in
    the first; its IFC data; a fire rating set on a wall; a column moved; undone; saved, opened again; a wrong id:
    an error the AI can read."""

    def test_tools(self):
        server = Server("arqsynth-bim", "test", tools(Session()), INSTRUCTIONS)
        text, error = call(server, "create", {"kind": "walls", "params": {
            "points": [[0, 0], [10, 0], [10, 6], [0, 6]], "closed": True}})
        self.assertFalse(error, text)
        self.assertEqual(text.count("#"), 4)
        self.assertIn("IfcWall 4", call(server, "summary")[0])
        table, _ = call(server, "query", {"class": "wall", "fields": ["id", "name", "length", "IsExternal"]})
        rows = table.splitlines()
        self.assertEqual(rows[0], "id\tname\tlength\tIsExternal")
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(r.endswith("\ttrue") for r in rows[1:]))
        first = rows[1].split("\t")[0]
        text, error = call(server, "create", {"kind": "door", "params": {"wall": first, "at": 1.0}})
        self.assertFalse(error, text)
        door = text.split()[1]
        info, _ = call(server, "get", {"id": door})
        self.assertIn("IfcDoor", info)
        self.assertIn("IsExternal=true", info)
        self.assertIn("in wall: " + first, info)
        call(server, "edit", {"ids": [first], "set": {"FireRating": "EI 30"}})
        self.assertIn("FireRating=EI 30", call(server, "get", {"id": first})[0])
        text, _ = call(server, "create", {"kind": "column", "params": {"at": [20, 0]}})
        column = text.split()[1]
        call(server, "edit", {"ids": [column], "move": [1, 2]})
        self.assertIn("undone", call(server, "undo")[0])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "casa.ifc")
            self.assertIn("saved", call(server, "file", {"action": "save", "path": path})[0])
            self.assertIn("opened", call(server, "file", {"action": "open", "path": path})[0])
            self.assertIn("IfcWall 4", call(server, "summary")[0])
        text, error = call(server, "get", {"id": "#99999999"})
        self.assertTrue(error)
        self.assertIn("no element", text)


class McpIfcData(unittest.TestCase):
    """0.274: the IFC data through the MCP — a house of four walls: the summary with missing=true says the walls' fire
    rating is missing in 4; the wall types as a table (one, 4 of it); the type's fire rating set in one call: every
    wall has it (the type's), the summary no longer says it is missing; get on the type: its data."""

    def test_ifc_data(self):
        server = Server("arqsynth-bim", "test", tools(Session()), INSTRUCTIONS)
        call(server, "create", {"kind": "walls", "params": {"points": [[0, 0], [10, 0], [10, 6], [0, 6]]}})
        text, _ = call(server, "summary", {"missing": True})
        self.assertIn("missing in IfcWall of 4 (Pset_WallCommon)", text)
        self.assertIn("FireRating 4", text)
        table, _ = call(server, "query", {"class": "IfcWallType"})
        rows = table.splitlines()
        self.assertEqual(rows[0], "id\tname\tcount")
        self.assertEqual(len(rows), 2)
        type_id, _name, count = rows[1].split("\t")
        self.assertEqual(count, "4")
        text, error = call(server, "edit", {"ids": [type_id], "set": {"FireRating": "EI 60"}})
        self.assertFalse(error, text)
        walls, _ = call(server, "query", {"class": "wall", "fields": ["id", "FireRating"]})
        self.assertTrue(all(r.endswith("\tEI 60") for r in walls.splitlines()[1:]))
        self.assertNotIn("FireRating 4", call(server, "summary", {"missing": True})[0])
        info, _ = call(server, "get", {"id": type_id})
        self.assertIn("elements of it: 4", info)
        self.assertIn("FireRating=EI 60", info)


class McpLink(unittest.TestCase):
    """0.269: the window's link written in the user's folder (port, key), read back, taken away only by the window
    that wrote it; with no window listening, a linked server's tools say so (an error the AI can read); the show
    tool only there."""

    def test_link(self):
        from arqbim.mcp import link
        from arqbim.mcp.tools import definitions, linked_tools
        old = os.environ.get("HOME"), os.environ.get("USERPROFILE")
        with tempfile.TemporaryDirectory() as home:
            os.environ["HOME"] = os.environ["USERPROFILE"] = home
            try:
                self.assertIsNone(link.read())
                link.write(1, "abc")
                self.assertEqual((link.read()["port"], link.read()["token"]), (1, "abc"))
                link.remove("other")
                self.assertIsNotNone(link.read())
                server = Server("arqsynth-bim", "test", linked_tools(), INSTRUCTIONS)
                text, error = call(server, "summary")
                self.assertTrue(error)
                self.assertIn("does not answer", text)
                link.remove("abc")
                self.assertIsNone(link.read())
                text, error = call(server, "summary")
                self.assertIn("not open", text)
            finally:
                for k, v in zip(("HOME", "USERPROFILE"), old):
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
        self.assertNotIn("show", [d[0] for d in definitions()])
        self.assertIn("show", [d[0] for d in definitions(live=True)])


class McpInstall(unittest.TestCase):
    """0.270: the server's entry (this Python, -m arqbim.mcp, the program's folder in PYTHONPATH); put into a config
    file that has another server — the other kept, a copy left beside it; into one not there yet — made; the line
    for Claude Code in its documented form (options, the name, --, the command)."""

    def test_install(self):
        from arqbim.mcp import install
        e = install.entry()
        self.assertEqual(e["args"], ["-m", "arqbim.mcp"])
        self.assertTrue(os.path.isdir(os.path.join(e["env"]["PYTHONPATH"], "arqbim")))
        self.assertIn(install.NAME, json.loads(install.config_text())["mcpServers"])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "Claude", "claude_desktop_config.json")
            install.merge_into(path)
            self.assertIn(install.NAME, _read(path)["mcpServers"])
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"mcpServers": {"other": {"command": "x"}}, "theme": "dark"}, f)
            install.merge_into(path, file="/tmp/casa.ifc")
            data = _read(path)
            self.assertEqual(set(data["mcpServers"]), {"other", install.NAME})
            self.assertEqual(data["theme"], "dark")
            self.assertEqual(data["mcpServers"][install.NAME]["args"][-2:], ["--file", "/tmp/casa.ifc"])
            self.assertTrue(os.path.exists(path + ".bak"))
            with open(path, "w", encoding="utf-8") as f:
                f.write("[1, 2]")
            with self.assertRaises(ValueError):
                install.merge_into(path)
        line = install.claude_code_line()
        self.assertTrue(line.startswith("claude mcp add --env "))
        self.assertIn("--transport stdio --scope user {} -- ".format(install.NAME), line)
        self.assertTrue(line.endswith("-m arqbim.mcp"))


class McpStdio(unittest.TestCase):
    """python -m arqbim.mcp spoken to through stdin / stdout as a client does: an answer a line each, valid JSON,
    nothing else on stdout."""

    def test_stdio(self):
        messages = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "summary", "arguments": {}}},
        ]
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as home:         # (no window's link there: a model of its own)
            env = dict(os.environ, HOME=home, USERPROFILE=home)
            run = subprocess.run([sys.executable, "-m", "arqbim.mcp"], cwd=root, timeout=120, capture_output=True,
                                 input="\n".join(json.dumps(m) for m in messages) + "\n", text=True,
                                 encoding="utf-8", env=env)
        lines = [line for line in run.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 3, run.stdout + run.stderr)
        answers = [json.loads(line) for line in lines]
        self.assertEqual([a["id"] for a in answers], [1, 2, 3])
        self.assertIn("storeys:", answers[2]["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
