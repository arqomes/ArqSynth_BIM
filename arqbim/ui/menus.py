"""(0.377) Where a menu opens. At the screen's foot a menu opened downwards went under the Windows taskbar:
in WSLg Qt does not know the taskbar is there (the screen's free area is the whole screen), so its own
turning round never happens. A menu that would reach that room opens upwards instead."""

from PySide6 import QtCore, QtGui

TASKBAR_PX = 56                                  # the Windows taskbar's room at the screen's foot


def _free_foot(point):
    """The lowest y a menu may reach on the screen at `point` (None: no screen)."""
    screen = QtGui.QGuiApplication.screenAt(point) or QtGui.QGuiApplication.primaryScreen()
    return None if screen is None else (screen.availableGeometry().bottom() - TASKBAR_PX,
                                        screen.availableGeometry().top())


class _KeepUp(QtCore.QObject):
    """Moves a menu shown by Qt itself (a submenu) up when it reaches the taskbar's room — just after it is
    shown: Qt places it again after its Show event."""

    def eventFilter(self, menu, event):
        if event.type() == QtCore.QEvent.Type.Show:
            QtCore.QTimer.singleShot(0, menu, lambda: self._up(menu))
        return False

    @staticmethod
    def _up(menu):
        if not menu.isVisible():
            return
        box = menu.geometry()
        room = _free_foot(box.center())
        if room is not None and box.bottom() > room[0]:
            menu.move(box.x(), max(room[1], box.y() - (box.bottom() - room[0])))


def keep_up(menu):
    """`menu` (a submenu: Qt places it) never goes under the taskbar — once per menu."""
    if not menu.property("arqsynth_keep_up"):
        menu.setProperty("arqsynth_keep_up", True)
        menu.installEventFilter(_KeepUp(menu))
    return menu


def menu_point(menu, point):
    """Where `menu`, asked to open at `point` (global), goes: there, or above it when it would reach the
    screen's foot (the taskbar's room left free)."""
    room = _free_foot(point)
    height = menu.sizeHint().height()
    if room is not None and point.y() + height > room[0]:
        return QtCore.QPoint(point.x(), max(room[1], point.y() - height))
    return point


def above(menu, widget, x=None):
    """The point where `menu` opens upwards from `widget`'s foot (its foot on the widget's foot) — for a button at
    the window's foot, as the settings gear. x: from the widget's left (default: its right side)."""
    foot = widget.mapToGlobal(QtCore.QPoint(widget.width() if x is None else x, widget.height()))
    return foot - QtCore.QPoint(0, menu.sizeHint().height())
