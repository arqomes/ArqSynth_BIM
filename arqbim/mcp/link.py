"""(0.269) The link between an MCP server and the program's open window: the window, when «Ligação à IA» is on,
listens on this computer only (127.0.0.1, a port the system gives) and writes where, with a key made at random, in
~/.arqsynth/mcp.json — the user's own folder. The MCP server reads it and sends each tool's call there, one
connection a call: a line of JSON {"token", "tool", "args"} — the answer a line {"text", "error"}."""

import json
import os
import socket

TIMEOUT = 120.0             # s: what a call may take (a big model's change)


def path():
    return os.path.join(os.path.expanduser("~"), ".arqsynth", "mcp.json")


def write(port, token):
    os.makedirs(os.path.dirname(path()), exist_ok=True)
    with open(path(), "w", encoding="utf-8") as f:
        json.dump({"port": int(port), "token": token, "pid": os.getpid()}, f)
    try:
        os.chmod(path(), 0o600)                            # (the user's alone, where the system allows)
    except OSError:
        pass


def read():
    """{"port", "token", "pid"} of the window listening, or None."""
    try:
        with open(path(), encoding="utf-8") as f:
            found = json.load(f)
        return found if isinstance(found, dict) and found.get("port") and found.get("token") else None
    except (OSError, ValueError):
        return None


def remove(token):
    """The link's file taken away — only if it is still this window's (another may have started since)."""
    found = read()
    if found is not None and found.get("token") == token:
        try:
            os.remove(path())
        except OSError:
            pass


def call(found, tool, args, timeout=TIMEOUT):
    """One tool's call sent to the window: (text, is an error). ConnectionError if the window is not there."""
    request = json.dumps({"token": found["token"], "tool": tool, "args": args or {}}, ensure_ascii=False) + "\n"
    with socket.create_connection(("127.0.0.1", int(found["port"])), timeout=timeout) as s:
        s.sendall(request.encode("utf-8"))
        data = b""
        while not data.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
    if not data:
        raise ConnectionError("no answer")
    answer = json.loads(data.decode("utf-8"))
    return answer.get("text", ""), bool(answer.get("error"))


def alive(found):
    """Whether a window answers at that link (a call of the summary)."""
    try:
        call(found, "summary", {}, timeout=5.0)
        return True
    except (OSError, ValueError, ConnectionError):
        return False
