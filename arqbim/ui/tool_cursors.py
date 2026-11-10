"""(0.526, the owner: «tornar o cursor dinâmico que muda consoante a ferramenta ativada») The 3D view's cursor by tool,
as SketchUp's and Revit's: the arrow to select, a hand to pan, and for the drawing / editing tools a fine cross whose
centre is the exact point clicked, with the tool's own icon small beside it — so one sees at a glance what a click will
do. Colours from ui/theme (the cross with an outline that reads on light and dark views)."""

from PySide6 import QtCore, QtGui

from . import theme

SIZE = 32                 # the cursor's picture (px, logical)
HOT = 10                  # where the click lands: the cross's centre
BADGE = 14                # the tool's icon, below right of the cross

# tools with a shape of Qt's own (the pointer itself says it)
SHAPES = {"select": QtCore.Qt.CursorShape.ArrowCursor, "pan": QtCore.Qt.CursorShape.OpenHandCursor,
          "look_around": QtCore.Qt.CursorShape.SizeAllCursor}

_made = {}


def _cross(p):
    """A fine cross with a gap at the centre (the point stays seen), outlined."""
    arms = ((HOT, 1, HOT, HOT - 3), (HOT, HOT + 3, HOT, 2 * HOT - 1),
            (1, HOT, HOT - 3, HOT), (HOT + 3, HOT, 2 * HOT - 1, HOT))
    for colour, width in ((theme.colour("grip_outline"), 3.0), (theme.colour("select"), 1.2)):
        pen = QtGui.QPen(colour, width)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.FlatCap)
        p.setPen(pen)
        for x0, y0, x1, y1 in arms:
            p.drawLine(QtCore.QPointF(x0 + 0.5, y0 + 0.5), QtCore.QPointF(x1 + 0.5, y1 + 0.5))


def cursor_for(name, icon=None, ratio=2.0):
    """The cursor of a tool; `icon`: its button's (QIcon), drawn beside the cross."""
    if name in SHAPES:
        return QtGui.QCursor(SHAPES[name])
    key = (name, theme.C.get("select"), theme.C.get("grip_outline"), ratio, icon is not None)
    if key in _made:
        return _made[key]
    pm = QtGui.QPixmap(int(SIZE * ratio), int(SIZE * ratio))
    pm.setDevicePixelRatio(ratio)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    _cross(p)
    if icon is not None and not icon.isNull():
        badge = QtCore.QRectF(SIZE - BADGE - 1, SIZE - BADGE - 1, BADGE, BADGE)
        back = theme.colour("card")
        back.setAlpha(230)
        p.setPen(QtGui.QPen(theme.colour("edge"), 1.0))
        p.setBrush(back)
        p.drawRoundedRect(badge.adjusted(-1.5, -1.5, 1.5, 1.5), 3, 3)
        icon.paint(p, badge.toRect())
    p.end()
    found = QtGui.QCursor(pm, HOT, HOT)
    _made[key] = found
    return found
