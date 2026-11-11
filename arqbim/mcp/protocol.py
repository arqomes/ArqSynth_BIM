"""The Model Context Protocol over stdio, with the standard library only: JSON-RPC 2.0, one message a line (UTF-8).
The server answers initialize (agreeing a protocol version), ping, tools/list and tools/call; a notification gets
no answer; an unknown method, a bad request: a JSON-RPC error. Nothing but messages goes to stdout — anything
printed while a tool runs goes to stderr."""

import base64
import contextlib
import json
import os
import sys
import traceback

VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")       # the newest first
PARSE_ERROR, INVALID_REQUEST, NO_METHOD, INVALID_PARAMS, INTERNAL = -32700, -32600, -32601, -32602, -32603


class ToolError(Exception):
    """A tool's call that cannot be done (said back to the AI as a tool's error, in a few words)."""


class Server:
    def __init__(self, name, version, tools, instructions=""):
        """tools: [(name, description, input schema, handler(arguments) -> text, read_only)]."""
        self.name, self.version, self.instructions = name, version, instructions
        self.tools = {t[0]: t for t in tools}
        self.order = [t[0] for t in tools]

    # ------------------------------------------------------------ one message

    def handle(self, message):
        """The answer (a dict) to one message (a dict), or None for a notification."""
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or "method" not in message:
            return _error(message.get("id") if isinstance(message, dict) else None, INVALID_REQUEST,
                          "invalid request")
        method, params, mid = message["method"], message.get("params") or {}, message.get("id")
        notification = "id" not in message
        try:
            if method == "initialize":
                result = self._initialize(params)
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": [self._listed(n) for n in self.order]}
            elif method == "tools/call":
                result = self._call(params)
            elif method.startswith("notifications/"):
                return None
            else:
                return None if notification else _error(mid, NO_METHOD, "unknown method: " + method)
        except _Invalid as exc:
            return None if notification else _error(mid, INVALID_PARAMS, str(exc))
        except Exception as exc:                            # (a fault of ours: said, never a crash)
            traceback.print_exc(file=sys.stderr)
            return None if notification else _error(mid, INTERNAL, "{}: {}".format(type(exc).__name__, exc))
        return None if notification else {"jsonrpc": "2.0", "id": mid, "result": result}

    def _initialize(self, params):
        asked = params.get("protocolVersion")
        result = {"protocolVersion": asked if asked in VERSIONS else VERSIONS[0],
                  "capabilities": {"tools": {"listChanged": False}},
                  "serverInfo": {"name": self.name, "version": self.version}}
        if self.instructions:
            result["instructions"] = self.instructions
        return result

    def _listed(self, name):
        _n, description, schema, _handler, read_only = self.tools[name]
        out = {"name": name, "description": description, "inputSchema": schema}
        if read_only:
            out["annotations"] = {"readOnlyHint": True}
        return out

    def _call(self, params):
        name = params.get("name")
        if name not in self.tools:
            raise _Invalid("unknown tool: {}".format(name))
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise _Invalid("arguments must be an object")
        handler = self.tools[name][3]
        try:
            with contextlib.redirect_stdout(sys.stderr):    # (stdout is the protocol's)
                text = handler(arguments)
            if isinstance(text, dict):                      # (0.543) a picture with it: the AI sees the result
                content = [{"type": "text", "text": text["text"]}]
                png = text.get("png")
                if png and os.path.exists(png):
                    with open(png, "rb") as fh:
                        content.append({"type": "image", "mimeType": "image/png",
                                        "data": base64.b64encode(fh.read()).decode("ascii")})
                return {"content": content, "isError": False}
            return {"content": [{"type": "text", "text": text}], "isError": False}
        except ToolError as exc:
            return {"content": [{"type": "text", "text": "error: {}".format(exc)}], "isError": True}
        except (ValueError, KeyError, TypeError) as exc:    # (a refused edit, a bad value…)
            reason = getattr(exc, "code", None) or str(exc)
            return {"content": [{"type": "text", "text": "error: {}".format(reason)}], "isError": True}

    # ------------------------------------------------------------ stdio

    def serve(self, stdin=None, stdout=None):
        """Reads messages a line each until stdin ends; writes the answers, a line each."""
        stdin = stdin or sys.stdin
        stdout = stdout or sys.stdout
        for line in stdin:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                answers = [_error(None, PARSE_ERROR, "parse error")]
            else:
                batch = message if isinstance(message, list) else [message]
                answers = [a for a in (self.handle(m) for m in batch) if a is not None]
            for answer in answers:
                stdout.write(json.dumps(answer, ensure_ascii=False, separators=(",", ":")) + "\n")
            stdout.flush()


class _Invalid(Exception):
    pass


def _error(mid, code, message):
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}}
