"""Navigation tools (0.78), for a mouse with no middle button or a touchpad — as SketchUp's Orbit (O), Pan (H)
and Zoom (Z): the left button drags the view. And Zoom window: a box dragged (or two clicks) fills the view
with what is inside it; then the tool used before comes back.

In a plan or a section Orbit pans: a drawing never turns.

Walking through the model (0.80), as SketchUp's: Position camera (a click where one stands: the eye at 1,60 m
over it), Look around (dragging turns the head) and Walk (dragging walks and turns, at the same height; the
arrow keys too; Shift: up / down; Ctrl: faster). In the 3D view with perspective only."""

import numpy as np

from ..core.units import format_length, parse_lengths
from ..i18n import decimal_sep, t
from .base import LEFT, RIGHT, Tool, moved_enough

ZOOM_DRAG_SPEED = 4.0           # Zoom tool: wheel units per pixel dragged
EYE_HEIGHT = 1.60               # m: Position camera puts the eye this high over the point clicked
WALK_STEP = 0.02                # m walked per pixel dragged (Ctrl: three times as far)
TURN_STEP = 0.004               # radians turned per pixel dragged
ARROW_STEP, ARROW_TURN = 0.5, 0.17   # one arrow key: 50 cm, or about 10°


class _DragTool(Tool):
    """The left button held down moves the view; the right button, Esc: back to Select."""

    def __init__(self, host):
        super().__init__(host)
        self._last = None
        self._pivot = None

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        self.viewport.remember_view()
        self._last = (x, y)
        self._start = (x, y)
        self._pivot = self.viewport.point_under(x, y)

    def pointer_move(self, x, y, modifiers):
        if self._last is None:
            return
        dx, dy = x - self._last[0], y - self._last[1]
        self._last = (x, y)
        self.drag(dx, dy, modifiers)

    def pointer_up(self, x, y, button, modifiers):
        self._last = None

    def drag(self, dx, dy, modifiers):
        raise NotImplementedError

    def cancel(self):
        self._last = None


class OrbitTool(_DragTool):
    name = "orbit"

    def hint(self):
        return t("hint.orbit")

    def drag(self, dx, dy, modifiers):
        vp = self.viewport
        if vp.cutting() or "Shift" in (modifiers or ()):
            vp.pan(dx, dy)                        # (a plan / section: it pans; Shift: pan for a moment)
        else:
            vp.orbit(dx, dy, self._pivot)


class PanTool(_DragTool):
    name = "pan"

    def hint(self):
        return t("hint.pan")

    def drag(self, dx, dy, modifiers):
        self.viewport.pan(dx, dy)


class ZoomTool(_DragTool):
    name = "zoom"

    def hint(self):
        return t("hint.zoom")

    def drag(self, dx, dy, modifiers):
        self.viewport.zoom_at(self._start[0], self._start[1], dy * ZOOM_DRAG_SPEED)    # up (dy < 0): closer


def _perspective_only(tool):
    """The walking tools need the 3D view with perspective: else they say so (True: they can go on)."""
    vp = tool.viewport
    if vp.cutting() or vp.is_ortho():
        tool.host.message(t("err.walk_3d"), warning=True)
        return False
    return True


class PositionCameraTool(Tool):
    """A click where one stands: the eye `eye` m over that point, looking the way the view looked (level);
    then Look around."""

    name = "position_camera"
    accepts_typing = True

    def __init__(self, host):
        super().__init__(host)
        self.eye = EYE_HEIGHT

    def hint(self):
        return t("hint.position_camera", h=format_length(self.eye, decimal_sep()))

    def vcb_title(self):
        return t("vcb.eye_height")

    def pointer_move(self, x, y, modifiers):
        self.viewport.show_marker(self.viewport.point_under(x, y))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT or not _perspective_only(self):
            return
        ground = self.viewport.point_under(x, y)
        self.viewport.show_marker(None)
        self.viewport.place_eye(ground + np.array((0.0, 0.0, self.eye)))
        self.host.message(t("info.position_camera", h=format_length(self.eye, decimal_sep())))
        self.host.set_tool("look_around")

    def typed(self, text):
        values = parse_lengths(text, 1)
        if values is None or values[0] is None or not 0.1 <= values[0] <= 100:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        self.eye = values[0]
        self.host.set_hint(self.hint())

    def cancel(self):
        self.viewport.show_marker(None)


class LookAroundTool(_DragTool):
    """Dragging turns the head: the camera stays where it is."""

    name = "look_around"

    def hint(self):
        return t("hint.look_around")

    def pointer_down(self, x, y, button, modifiers):
        if button == LEFT and not _perspective_only(self):
            return
        super().pointer_down(x, y, button, modifiers)

    def drag(self, dx, dy, modifiers):
        vp = self.viewport
        vp.orbit(dx, dy, vp.camera_position())      # (turning round its own place)


class WalkTool(_DragTool):
    """Dragging up / down walks forward / back, left / right turns — at the same height (Shift: up / down;
    Ctrl: faster). The arrow keys walk and turn too."""

    name = "walk"

    def hint(self):
        return t("hint.walk")

    def pointer_down(self, x, y, button, modifiers):
        if button == LEFT and not _perspective_only(self):
            return
        super().pointer_down(x, y, button, modifiers)

    def drag(self, dx, dy, modifiers):
        mods = set(modifiers or ())
        speed = WALK_STEP * (3.0 if mods & {"Control", "Ctrl"} else 1.0)
        if "Shift" in mods:
            self.viewport.walk(0.0, -dy * speed, 0.0)
        else:                                     # (Alt: through the walls, as in SketchUp)
            self._stopped(self.viewport.walk(-dy * speed, 0.0, dx * TURN_STEP, collide="Alt" not in mods))

    def arrow(self, key):
        if not _perspective_only(self):
            return True
        forward, turn = {"up": (ARROW_STEP, 0.0), "down": (-ARROW_STEP, 0.0),
                         "left": (0.0, -ARROW_TURN), "right": (0.0, ARROW_TURN)}[key]
        self._stopped(self.viewport.walk(forward, 0.0, turn))
        return True

    def _stopped(self, stopped):
        if stopped:
            self.host.message(t("info.walk_blocked"))


class ZoomWindowTool(Tool):
    """One box: what is inside fills the view. Then back to the tool used before (`back_to`)."""

    name = "zoom_window"

    def __init__(self, host):
        super().__init__(host)
        self.back_to = "select"
        self._corner = None
        self._dragging = False

    def hint(self):
        return t("hint.zoom_window")

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self._finish()
            return
        if button != LEFT:
            return
        if self._corner is None:
            self._corner = (x, y)
            self._dragging = True
        else:                                     # a second click: the other corner
            self._zoom(x, y)

    def pointer_move(self, x, y, modifiers):
        if self._corner is None:
            return
        (x0, y0) = self._corner
        self.viewport.show_region([(x0, y0), (x, y0), (x, y), (x0, y)], "window")

    def pointer_up(self, x, y, button, modifiers):
        if button != LEFT or self._corner is None or not self._dragging:
            return
        self._dragging = False
        if moved_enough(self._corner, (x, y)):    # dragged: done; else the next click is the other corner
            self._zoom(x, y)

    def _zoom(self, x, y):
        x0, y0 = self._corner
        self._corner = None
        self.viewport.show_region()
        if self.viewport.zoom_to_region(x0, y0, x, y):
            self.host.message(t("info.zoom_window"))
        self._finish()

    def _finish(self):
        self._corner = None
        self.viewport.show_region()
        self.host.set_tool(self.back_to if self.back_to in self.host.tools else "select")

    def cancel(self):
        if self._corner is not None:
            self._corner = None
            self.viewport.show_region()
