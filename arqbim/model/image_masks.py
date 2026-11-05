"""(0.389) A picture as a perforated panel's mask: how dark it is at each pixel (0 white — or transparent — to 1
black), made small (at most MAX_SIDE pixels a side: a hole is never finer than that) and kept while the file is the
same. The holes are as big as the picture is dark where they are (core/surfaces.perforation)."""

import os

import numpy as np

MAX_SIDE = 400
_cache = {}
IMAGE_FILTER = "*.png *.jpg *.jpeg *.bmp *.gif *.webp"


def load(path):
    """(h, w) darkness 0–1, row 0 at the top — or None (no picture, not there, not a picture)."""
    if not path:
        return None
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        return None
    key = (os.path.normcase(os.path.abspath(path)), stamp)
    if key in _cache:
        return _cache[key]
    from PySide6 import QtCore, QtGui
    image = QtGui.QImage(path)
    if image.isNull():
        return None
    if max(image.width(), image.height()) > MAX_SIDE:
        image = image.scaled(MAX_SIDE, MAX_SIDE, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                             QtCore.Qt.TransformationMode.SmoothTransformation)
    image = image.convertToFormat(QtGui.QImage.Format.Format_RGBA8888)
    w, h = image.width(), image.height()
    rows = np.frombuffer(image.constBits(), np.uint8, count=image.bytesPerLine() * h).reshape(h, image.bytesPerLine())
    rgba = rows[:, :w * 4].reshape(h, w, 4).astype(float) / 255.0
    grey = rgba[..., 0] * 0.299 + rgba[..., 1] * 0.587 + rgba[..., 2] * 0.114
    grey = grey * rgba[..., 3] + (1.0 - rgba[..., 3])           # (what is transparent: white — no holes)
    dark = np.ascontiguousarray(1.0 - grey)
    _cache.clear()                                               # (only the last one kept: they can be big)
    _cache[key] = dark
    return dark
