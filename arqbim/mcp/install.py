"""(0.270) The MCP server put in the AI's programs: its entry (this Python, `-m arqbim.mcp`, the program's folder in
PYTHONPATH) as Claude Desktop's config file and Claude Code's .mcp.json want it — {"mcpServers": {name: {command,
args, env}}} — merged into what is there (the other servers kept, a copy of the file kept beside it), and the
`claude mcp add` line for Claude Code (its documented form: options, the name, `--`, the command)."""

import json
import os
import shutil
import subprocess
import sys

NAME = "arqsynth-bim"


def root():
    """The program's folder (where the package arqbim is)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def python():
    """The Python that runs the program (pythonw.exe: its console twin, an MCP server talks on stdio)."""
    exe = sys.executable
    if os.path.basename(exe).lower() == "pythonw.exe":
        console = os.path.join(os.path.dirname(exe), "python.exe")
        exe = console if os.path.exists(console) else exe
    return exe


def entry(file=None):
    """The server's entry: {command, args, env}."""
    args = ["-m", "arqbim.mcp"] + (["--file", file] if file else [])
    return {"command": python(), "args": args, "env": {"PYTHONPATH": root(), "PYTHONIOENCODING": "utf-8"}}


def config_text(file=None):
    """The JSON to paste: {"mcpServers": {"arqsynth-bim": …}}."""
    return json.dumps({"mcpServers": {NAME: entry(file)}}, indent=2, ensure_ascii=False)


def desktop_config_path():
    """Claude Desktop's config file on this system."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
        return os.path.join(base, "Claude", "claude_desktop_config.json")
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Claude",
                            "claude_desktop_config.json")
    return os.path.join(os.path.expanduser("~"), ".config", "Claude", "claude_desktop_config.json")


def merge_into(path, file=None):
    """The server's entry put into a config file of {"mcpServers": …} (Claude Desktop's, a .mcp.json): made if
    missing; else its other contents kept and a copy of it left beside it (.bak). ValueError if it is not JSON."""
    data = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        data = json.loads(text) if text.strip() else {}
        if not isinstance(data, dict):
            raise ValueError("not a JSON object")
        shutil.copyfile(path, path + ".bak")
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        servers = data["mcpServers"] = {}
    servers[NAME] = entry(file)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def claude_code_line(file=None):
    """The command that adds the server to Claude Code (for this user, every folder)."""
    e = entry(file)                     # (Claude Code's options before the name, --transport after the --env pairs)
    envs = " ".join("--env {}".format(_quoted("{}={}".format(k, v))) for k, v in e["env"].items())
    return "claude mcp add {} --transport stdio --scope user {} -- {} {}".format(
        envs, NAME, _quoted(e["command"]), " ".join(_quoted(a) for a in e["args"]))


def _quoted(text):
    return subprocess.list2cmdline([text]) if sys.platform == "win32" else (
        "'{}'".format(text.replace("'", "'\\''")) if any(c in text for c in " '\"$\\") else text)
