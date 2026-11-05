"""«Ligação à IA» (0.269): the window as the MCP server's other end. On, it listens on this computer only
(127.0.0.1, a port the system gives) and writes where, with a key made at random, in the user's ~/.arqsynth/mcp.json
(mcp/link.py); an MCP server (python -m arqbim.mcp) reads it and sends each tool's call. The tools run here, in the
window's thread, on the model open — seen as they work, each change one undo step as the user's own — and what the AI
did is said in the status bar. Off (or the window closed): the port closed, the file taken away."""

import json
import secrets

from PySide6 import QtCore, QtNetwork

from ..i18n import t
from ..mcp import link
from ..mcp.protocol import ToolError
from ..mcp.tools import Session, run

MAX_REQUEST = 4 * 1024 * 1024           # bytes: a call's line at most (a long outline…)
SAID = {"created": "ai.created", "ok:": "ai.changed", "deleted": "ai.deleted", "undone:": "ai.undone",
        "saved": "ai.saved"}            # (the tools' answers' first word, for the status bar)


class LiveSession(Session):
    """The tools' session on the window's own model: new, open and save as the window does them."""

    def __init__(self, window):
        self.window = window

    @property
    def doc(self):
        return self.window.doc

    def new_model(self):
        raise ToolError("in the window the user opens or starts models (File)")

    def open_model(self, path):
        raise ToolError("in the window the user opens or starts models (File)")

    def save_model(self, path):
        self.window.save_to(path)

    def show(self, guids):
        self.window.viewport.set_selection(set(guids))
        self.window.zoom_selection()


class AiLink(QtCore.QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.server = None
        self.token = None
        self.session = LiveSession(window)
        self.calls = 0                      # (tests)

    @property
    def on(self):
        return self.server is not None and self.server.isListening()

    def start(self):
        if self.on:
            return True
        server = QtNetwork.QTcpServer(self)
        if not server.listen(QtNetwork.QHostAddress(QtNetwork.QHostAddress.SpecialAddress.LocalHost), 0):
            return False
        server.newConnection.connect(self._connected)
        self.server, self.token = server, secrets.token_hex(16)
        link.write(server.serverPort(), self.token)
        return True

    def stop(self):
        if self.server is not None:
            self.server.close()
            self.server.deleteLater()
        if self.token:
            link.remove(self.token)
        self.server = self.token = None

    def _connected(self):
        while self.server is not None and self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.setProperty("buffer", b"")
            socket.readyRead.connect(lambda s=socket: self._read(s))
            socket.disconnected.connect(socket.deleteLater)

    def _read(self, socket):
        data = bytes(socket.property("buffer") or b"") + bytes(socket.readAll())
        if len(data) > MAX_REQUEST:
            socket.abort()
            return
        if b"\n" not in data:
            socket.setProperty("buffer", data)
            return
        line = data.split(b"\n", 1)[0]
        socket.setProperty("buffer", b"")
        answer = self.answer(line)
        socket.write((json.dumps(answer, ensure_ascii=False) + "\n").encode("utf-8"))
        socket.flush()
        socket.disconnectFromHost()

    def answer(self, line):
        """A call's answer: {"text", "error"} — a call without this window's key: refused."""
        try:
            request = json.loads(line.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {"text": "error: not JSON", "error": True}
        if not isinstance(request, dict) or not secrets.compare_digest(str(request.get("token", "")),
                                                                        self.token or "\0"):
            return {"text": "error: wrong key", "error": True}
        tool, args = str(request.get("tool") or ""), request.get("args") or {}
        if getattr(self.window.doc, "loading", False):
            return {"text": "error: the model is still being read; try again in a moment", "error": True}
        self.calls += 1
        try:
            text = run(self.session, tool, args)
        except ToolError as exc:
            return {"text": "error: {}".format(exc), "error": True}
        except (ValueError, KeyError, TypeError) as exc:
            return {"text": "error: {}".format(getattr(exc, "code", None) or exc), "error": True}
        if tool not in ("summary", "query", "get", "show"):          # (what it changed, said in the window's words)
            first = text.splitlines()[0][:120]
            for english, words in SAID.items():
                if first.startswith(english):
                    first = t(words) + first[len(english):]
                    break
            self.window.message(t("info.ai_did", what=first))
        return {"text": text, "error": False}
