"""Reading a background image's picture (0.154) with Qt: its size in pixels, and its pixels for the viewport —
a big one made smaller on the way (a texture no larger than MOST pixels on its longest side: what any graphics
card takes, and plenty to draw over)."""

import numpy as np
from PySide6 import QtCore, QtGui

MOST = 4096


def picture_size(path):
    """(width, height) in pixels, or None when it is not a picture Qt reads."""
    reader = QtGui.QImageReader(path)
    reader.setAutoTransform(True)                       # (a photo turned by its camera: as it is seen)
    if not reader.canRead():
        return None
    size = reader.size()
    if not size.isValid() or size.width() <= 0:
        image = reader.read()                           # (some formats only say it once read)
        return None if image.isNull() else (image.width(), image.height())
    if reader.transformation() & QtGui.QImageIOHandler.Transformation.TransformationRotate90:
        return size.height(), size.width()
    return size.width(), size.height()


def load_pixels(path):
    """The picture as (H, W, 4) uint8 RGBA, row 0 at its top — or None."""
    reader = QtGui.QImageReader(path)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid() and max(size.width(), size.height()) > MOST:
        reader.setScaledSize(size.scaled(MOST, MOST, QtCore.Qt.AspectRatioMode.KeepAspectRatio))
    image = reader.read()
    if image.isNull():
        return None
    if max(image.width(), image.height()) > MOST:
        image = image.scaled(MOST, MOST, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                             QtCore.Qt.TransformationMode.SmoothTransformation)
    image = image.convertToFormat(QtGui.QImage.Format.Format_RGBA8888)
    w, h = image.width(), image.height()
    data = np.frombuffer(image.constBits(), np.uint8, count=image.bytesPerLine() * h)
    return data.reshape(h, image.bytesPerLine() // 4, 4)[:, :w].copy()


def file_filter():
    from ..i18n import t
    from ..model.images import EXTENSIONS
    return "{} ({})".format(t("file.images"), " ".join("*." + e for e in EXTENSIONS))
