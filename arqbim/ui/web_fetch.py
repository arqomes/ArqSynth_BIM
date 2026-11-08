"""(0.471) Reading from the web for the panels (the Materials panel's Poly Haven textures; the Library has its own since
0.467): a request that says which program asks (Poly Haven's API wants it) and follows redirects, a list kept a day on
this computer, miniatures fetched a few at a time and kept on disk, files fetched into a folder whole or not at all."""

import hashlib
import os
import shutil

from PySide6 import QtCore, QtGui, QtNetwork

from ..model import component_library as lib
from . import component_thumbs

AT_ONCE = 6                       # miniatures fetched at the same time
LIST_HOURS = 24                   # a list read again after this long


class Fetcher(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._net = None
        self._waiting, self._running = [], 0
        self.generation = 0           # (a new list: the miniatures asked for before it are dropped)

    def _network(self):
        if self._net is None:
            self._net = QtNetwork.QNetworkAccessManager(self)
        return self._net

    @staticmethod
    def request(url):
        request = QtNetwork.QNetworkRequest(QtCore.QUrl(url) if isinstance(url, str) else url)
        request.setRawHeader(b"User-Agent", lib.user_agent().encode("ascii"))
        request.setAttribute(QtNetwork.QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QtNetwork.QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
        return request

    def get(self, url, done):
        """`done(bytes or None, error text)` once the address is read (None: it failed)."""
        reply = self._network().get(self.request(url))

        def finished(r=reply):
            ok = r.error() == QtNetwork.QNetworkReply.NetworkError.NoError
            data, error = (bytes(r.readAll()) if ok else None), r.errorString()
            r.deleteLater()
            done(data, error)
        reply.finished.connect(finished)

    def kept_list(self, url, name, done):
        """`done(text or None, error)` of an address read at most once a day (kept as `name` on this computer)."""
        kept = os.path.join(component_thumbs.cache_dir(), name)
        try:
            if os.path.exists(kept) and \
                    QtCore.QDateTime.currentSecsSinceEpoch() - os.path.getmtime(kept) < LIST_HOURS * 3600:
                with open(kept, encoding="utf-8") as fh:
                    done(fh.read(), "")
                    return
        except OSError:
            pass

        def read(data, error):
            if data is None:
                done(None, error)
                return
            text = data.decode("utf-8", "replace")
            try:
                with open(kept, "w", encoding="utf-8") as fh:
                    fh.write(text)
            except OSError:
                pass
            done(text, "")
        self.get(url, read)

    def picture(self, url, show):
        """A miniature: `show(QPixmap)` from this computer when kept, else once fetched (AT_ONCE at a time)."""
        self._waiting.append((self.generation, str(url), show))
        self._next()

    def drop_pictures(self):
        self.generation += 1
        self._waiting = []

    def _next(self):
        while self._waiting and self._running < AT_ONCE:
            generation, url, show = self._waiting.pop(0)
            if generation != self.generation:
                continue
            kept = os.path.join(component_thumbs.cache_dir(),
                                "web_" + hashlib.sha1(url.encode("utf-8")).hexdigest() + ".png")
            pm = QtGui.QPixmap(kept) if os.path.exists(kept) else QtGui.QPixmap()
            if not pm.isNull():
                show(pm)
                continue
            self._running += 1

            def done(data, _error, show=show, kept=kept, generation=generation):
                self._running -= 1
                if data is not None and generation == self.generation:
                    picture = QtGui.QPixmap()
                    if picture.loadFromData(data):
                        picture.save(kept, "PNG")
                        show(picture)
                self._next()
            self.get(url, done)

    def files(self, folder, parts, done, step=None):
        """Files fetched into `folder` — parts: [(file name, address)] — whole or not at all (a «.parcial» folder put
        in its place at the end); `done(error or None)`; step(n done, of): as they come."""
        work = folder + ".parcial"
        shutil.rmtree(work, ignore_errors=True)
        os.makedirs(work, exist_ok=True)
        state = {"left": len(parts), "failed": None}
        if not parts:
            done("—")
            return

        def one(name):
            def saved(content, error):
                state["left"] -= 1
                if content is None:
                    state["failed"] = error or "—"
                else:
                    with open(os.path.join(work, name), "wb") as fh:
                        fh.write(content)
                if step is not None:
                    step(len(parts) - state["left"], len(parts))
                if state["left"]:
                    return
                if state["failed"] is not None:
                    shutil.rmtree(work, ignore_errors=True)
                    done(state["failed"])
                    return
                shutil.rmtree(folder, ignore_errors=True)
                os.replace(work, folder)
                done(None)
            return saved
        for name, address in parts:
            self.get(address, one(name))
