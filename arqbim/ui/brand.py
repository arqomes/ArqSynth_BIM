"""The brand (0.82): the ArqSynth symbol — the blue mark of www.arqsynth.com, in assets/ — as the window's icon,
and the starting screen shown while the program loads (the 3D engine and IFC take some seconds).

The program's name is not in the picture: it is written here, from APP_NAME, so a new name is one line."""

import os

from PySide6 import QtCore, QtGui, QtWidgets

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
SYMBOL = os.path.join(ASSETS, "arqsynth-simbolo.png")
BLUE = QtGui.QColor("#2f75fd")            # the symbol's blue
INK = QtGui.QColor("#1b2430")
ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)
SPLASH_W, SPLASH_H = 560, 300


def symbol(size):
    """The symbol in a square of `size` pixels (transparent round it), or None if its file is missing."""
    image = QtGui.QImage(SYMBOL)
    if image.isNull():
        return None
    pm = QtGui.QPixmap(size, size)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    scaled = image.scaled(size, size, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                          QtCore.Qt.TransformationMode.SmoothTransformation)
    p = QtGui.QPainter(pm)
    p.drawImage(QtCore.QPointF((size - scaled.width()) / 2, (size - scaled.height()) / 2), scaled)
    p.end()
    return pm


def app_icon():
    """The window's icon (every size drawn from the big picture: sharp in the title bar and the taskbar), or
    None without the symbol's file."""
    icon = QtGui.QIcon()
    for size in ICON_SIZES:
        pm = symbol(size)
        if pm is None:
            return None
        icon.addPixmap(pm)
    return icon


def _name_parts(name):
    """The name with "Synth" in the brand's blue, as on the site: [(text, colour)]."""
    at = name.find("Synth")
    if at < 0:
        return [(name, INK)]
    return [(name[:at], INK), ("Synth", BLUE), (name[at + 5:], INK)]


def splash_pixmap(name, version):
    """The starting screen: the symbol, the name, the version; the message at the bottom is the splash's."""
    ratio = 2.0                                     # (drawn at twice the size: sharp on high-density screens)
    pm = QtGui.QPixmap(int(SPLASH_W * ratio), int(SPLASH_H * ratio))
    pm.setDevicePixelRatio(ratio)
    pm.fill(QtGui.QColor("#ffffff"))
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform)
    p.fillRect(QtCore.QRectF(0, SPLASH_H - 6, SPLASH_W, 6), BLUE)
    mark = symbol(int(150 * ratio))
    if mark is not None:
        mark.setDevicePixelRatio(ratio)
        p.drawPixmap(QtCore.QPointF(40, 60), mark)
    font = QtGui.QFont(p.font())
    font.setBold(True)
    room = SPLASH_W - 215 - 30
    for px in range(46, 17, -2):                   # (as big as fits: any name)
        font.setPixelSize(px)
        metrics = QtGui.QFontMetricsF(font)
        if metrics.horizontalAdvance(name) <= room:
            break
    p.setFont(font)
    x, y = 215.0, 145.0
    for text, color in _name_parts(name):
        p.setPen(color)
        p.drawText(QtCore.QPointF(x, y), text)
        x += metrics.horizontalAdvance(text)
    small = QtGui.QFont(font)
    small.setPixelSize(15)
    small.setBold(False)
    p.setFont(small)
    p.setPen(QtGui.QColor("#5b6675"))
    p.drawText(QtCore.QPointF(217, 178), version)
    p.end()
    return pm


class Splash(QtWidgets.QSplashScreen):
    """The starting screen, with a line saying what is being loaded."""

    def __init__(self, name, version):
        super().__init__(splash_pixmap(name, version))

    def say(self, text):
        self.showMessage(text)
        QtWidgets.QApplication.processEvents()

    def drawContents(self, painter):
        """The message under the version, lined up with the name (Qt's own is in the very corner)."""
        painter.setPen(QtGui.QColor("#5b6675"))
        painter.drawText(QtCore.QRectF(217, SPLASH_H - 70, SPLASH_W - 240, 30),
                         QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter, self.message())
