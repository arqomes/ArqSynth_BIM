"""(0.387) The documents opened or saved last (the start page's «Documentos recentes»): kept for the computer, not the
project (QSettings «recentes/…»), the most recent first, as many as chosen (20 unless changed, at most 100); each with
a small picture of its view when it was last saved or opened (in the program's cache folder, «miniaturas»)."""

import hashlib
import json
import os

import numpy as np
from PySide6 import QtCore, QtGui

DEFAULT_KEEP, MOST = 20, 100
THUMB_W, THUMB_H = 160, 100            # px: the picture kept (shown smaller)


def _settings():
    return QtCore.QSettings("ArqSynth", "ArqSynth BIM")


def _group():
    """The settings' group: «recentes» — the tests set ARQBIM_RECENT_GROUP, not to touch the user's list."""
    return os.environ.get("ARQBIM_RECENT_GROUP") or "recentes"


def keep():
    """How many are kept."""
    try:
        return max(1, min(MOST, int(_settings().value(_group() + "/manter", DEFAULT_KEEP))))
    except (TypeError, ValueError):
        return DEFAULT_KEEP


def set_keep(n):
    n = max(1, min(MOST, int(n)))
    _settings().setValue(_group() + "/manter", n)
    _write(files()[:n])


def files():
    """The paths, the most recent first."""
    try:
        found = json.loads(str(_settings().value(_group() + "/arquivos", "[]") or "[]"))
    except ValueError:
        return []
    return [str(p) for p in found if isinstance(p, str) and p]


def _write(paths):
    _settings().setValue(_group() + "/arquivos", json.dumps(list(paths)))


# (0.388) how the start page shows them: big pictures in a grid, a list, or details; in what order
VIEWS = ("grid", "list", "details")
ORDERS = ("used", "name", "modified")


def view():
    v = str(_settings().value(_group() + "/vista", "grid") or "grid")
    return v if v in VIEWS else "grid"


def set_view(v):
    if v in VIEWS:
        _settings().setValue(_group() + "/vista", v)


def order():
    o = str(_settings().value(_group() + "/ordem", "used") or "used")
    return o if o in ORDERS else "used"


def set_order(o):
    if o in ORDERS:
        _settings().setValue(_group() + "/ordem", o)


def modified(path):
    """When the file was last changed (seconds), or None (not there)."""
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def arranged(paths, how="used", find=""):
    """The paths in the order asked — "used" (the most recently used first), "name" (A–Z, accents aside),
    "modified" (the file's last change, newest first; those not there last) — those whose name or folder has the
    words of `find` (accents and capitals aside)."""
    from .help_window import folded
    words = folded(find).split()
    out = [p for p in paths if all(w in folded(p) for w in words)]
    if how == "name":
        out.sort(key=lambda p: folded(os.path.basename(p)))
    elif how == "modified":
        out.sort(key=lambda p: (modified(p) is None, -(modified(p) or 0.0)))
    return out


def _same(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def add(path):
    """This document the most recent (once)."""
    if not path:
        return
    path = os.path.abspath(path)
    _write(([path] + [p for p in files() if not _same(p, path)])[:keep()])


def remove(path):
    _write([p for p in files() if not _same(p, path)])


def thumb_file(path):
    """Where its picture is kept."""
    from ..model.geomcache import cache_dir
    name = hashlib.sha1(os.path.normcase(os.path.abspath(path)).encode("utf-8")).hexdigest()[:20] + ".png"
    return os.path.join(cache_dir(), "miniaturas", name)


def save_thumb(path, rgba):
    """Its picture from the view's last image ((h, w, 4) bytes): cut to the picture's shape round its middle,
    made small. False if there is nothing to keep."""
    if not path or rgba is None:
        return False
    rgba = np.ascontiguousarray(np.asarray(rgba, dtype=np.uint8))
    if rgba.ndim != 3 or rgba.shape[2] != 4 or rgba.shape[0] < 4 or rgba.shape[1] < 4:
        return False
    h, w = rgba.shape[:2]
    image = QtGui.QImage(rgba.data, w, h, 4 * w, QtGui.QImage.Format.Format_RGBA8888).copy()
    want = THUMB_W / THUMB_H
    if w / h > want:                                       # (too wide: its middle)
        cw = int(h * want)
        image = image.copy((w - cw) // 2, 0, cw, h)
    else:
        ch = int(w / want)
        image = image.copy(0, (h - ch) // 2, w, ch)
    image = image.scaled(THUMB_W, THUMB_H, QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
                         QtCore.Qt.TransformationMode.SmoothTransformation)
    target = thumb_file(path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    return image.save(target, "PNG")
