"""Calibrate image (0.154, Phase 7, step 2): a background image put to its real size and place, step by step —
1. a click on the image at the start of a measure one knows (a dimension written on the plan, a door's width…);
2. a click at its end (the line drawn meanwhile, its length on the image in the Measurements box);
3. the real length typed ("8,50") and Enter: the image scaled about the first point — and locked;
4. a click where that first point is in the model (snaps: a wall's corner, a grid crossing) — or Esc, left there;
5. a click towards where the second point goes (or the angle typed) — or Esc, left as it is.
Each step its own undo. A locked image is not calibrated again until unlocked (View ▸ Background images…)."""

import numpy as np

from ..core.sketch_geometry import ray_plane
from ..core.units import format_length, parse_angle, parse_length
from ..i18n import decimal_sep, t
from ..model import images as images_model
from ..model.document import ImagesChange
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Tool, infer_point, show_snap

START, END, LENGTH, PLACE, TURN = range(5)


class CalibrateImageTool(Tool):
    name = "calibrate_image"
    accepts_typing = True
    on_storey = True

    def __init__(self, host):
        super().__init__(host)
        self.only = None              # the image to calibrate (the dialog's Calibrate), or None: any under the mouse
        self._reset()

    def _reset(self):
        self._uid = self._a = self._b = self._place = None
        self._step = START

    def _image(self):
        return next((i for i in self.doc.images if i.uid == self._uid), None)

    def hint(self):
        if self._step == START:
            if not any(not i.locked for i in self.doc.images):
                return t("hint.image.none") if not self.doc.images else t("hint.image.locked")
            return t("hint.image.start")
        return t(("hint.image.start", "hint.image.end", "hint.image.length", "hint.image.place",
                  "hint.image.turn")[self._step])

    def vcb_title(self):
        return t("vcb.angle") if self._step == TURN else t("vcb.length")

    def _on_image(self, x, y):
        image, p = self.viewport.image_at(x, y)
        if image is not None and self.only is not None and image.uid != self.only:
            return None, None
        return image, p

    def _on_level(self, x, y, z):
        origin, direction = self.viewport.ray(x, y)
        if abs(direction[2]) < 1e-9:
            return None
        s = (z - origin[2]) / direction[2]
        return origin + direction * s if s > 0 else None

    def _model_point(self, x, y, modifiers, last=None):
        found, snap, _hit = infer_point(self.viewport, x, y, last, modifiers)
        if found is not None:
            return found.point.copy(), found
        image = self._image()
        z = self.viewport.image_level(image) if image is not None else self.doc.work_level()
        return self._on_level(x, y, z), None

    def pointer_move(self, x, y, modifiers):
        if self._step == START:
            return
        if self._step == END:
            image = self._image()
            p = self._on_level(x, y, self.viewport.image_level(image)) if image is not None else None
            if p is None:
                return
            self.viewport.show_polygon([], segments=[self._a, p], colors=[PREVIEW] * 2)
            self.host.set_vcb(format_length(float(np.linalg.norm((p - self._a)[:2])), decimal_sep()))
        elif self._step == PLACE:
            p, snap = self._model_point(x, y, modifiers)
            if p is None:
                return
            show_snap(self.viewport, snap, p)
            self._outline(self._image().moved(p[:2] - self._a[:2]))
        elif self._step == TURN:
            p, snap = self._model_point(x, y, modifiers, self._place)
            if p is None:
                return
            show_snap(self.viewport, snap, p)
            angle = images_model.turn_towards(self._place, self._b, p)
            self._outline(self._image().turned(self._place[:2], angle), extra=[self._place, p])
            self.host.set_vcb("{:.1f}°".format(angle).replace(".", decimal_sep()))

    def _outline(self, image, extra=()):
        z = self.viewport.image_level(image) + 0.01
        c = [np.array((x, y, z)) for x, y in image.corners()]
        segs = [p for k in range(4) for p in (c[k], c[(k + 1) % 4])] + list(extra)
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT:
            return
        if self._step == START:
            image, p = self._on_image(x, y)
            if image is not None and image.vertical:          # (0.208: put on its facade again instead)
                self.host.message(t("err.image_vertical"), warning=True)
                return
            if image is None:
                locked, _p = self.viewport.image_at(x, y, unlocked=False)
                self.host.message(t("hint.image.locked") if locked is not None else
                                  (t("hint.image.none") if not self.doc.images else t("hint.image.start")),
                                  warning=True)
                return
            self._uid, self._a, self._step = image.uid, p, END
        elif self._step == END:
            p = self._on_level(x, y, self.viewport.image_level(self._image()))
            if p is None or np.linalg.norm((p - self._a)[:2]) < 1e-6:
                return
            self._b, self._step = p, LENGTH
            self.viewport.show_polygon([], segments=[self._a, self._b], colors=[PREVIEW] * 2)
            self.host.set_vcb("")
        elif self._step == PLACE:
            p, _snap = self._model_point(x, y, modifiers)
            if p is not None:
                self._move_to(p)
        elif self._step == TURN:
            p, _snap = self._model_point(x, y, modifiers, self._place)
            if p is not None:
                self._turn(images_model.turn_towards(self._place, self._b, p))
        self.host.set_hint(self.hint())

    def typed(self, text):
        if self._step == TURN:
            angle = parse_angle(text)
            if angle is None:
                self.host.message(t("err.bad_value", t=text), warning=True)
                return
            self._turn(angle)
            return
        if self._step != LENGTH:
            self.host.message(t("hint.image.length_later"), warning=True)
            return
        real = parse_length(text)
        factor = images_model.calibration(self._a, self._b, real)
        if factor is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        image = self._image()
        done = image.scaled(self._a[:2], factor)
        done.locked = True
        self._change(image, done, t("cmd.calibrate_image"))
        self._b = self._a + (self._b - self._a) * factor            # (where the second point is now)
        self._step = PLACE
        self.host.message(t("info.image_calibrated", f="{:g}".format(round(factor, 4)).replace(".", decimal_sep()),
                            w=format_length(done.width, decimal_sep())))
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")

    def _move_to(self, p):
        image = self._image()
        delta = p[:2] - self._a[:2]
        self._change(image, image.moved(delta), t("cmd.place_image"))
        self._place = np.array((p[0], p[1], self._a[2]))
        self._b = self._b + np.array((delta[0], delta[1], 0.0))
        self._step = TURN
        self.viewport.clear_overlays()

    def _turn(self, angle):
        image = self._image()
        if abs(angle) > 1e-9:
            self._change(image, image.turned(self._place[:2], angle), t("cmd.turn_image"))
        self.host.message(t("info.image_done"))
        self.cancel()

    def _change(self, before, after, label):
        images = [after if i.uid == before.uid else i for i in self.doc.images]
        self.doc.execute(ImagesChange(self.doc.images, images, label))

    def cancel(self):
        if self._step >= PLACE:
            self.host.message(t("info.image_done"))
        self._reset()
        self.only = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")


class FacadeImageTool(Tool):
    """Pôr numa fachada (0.208, Phase 7, step 2): a background image stood up on a face of the model (a wall's, a
    facade's) — a click where its lower-left corner goes, a click where its lower-right goes (or its width typed,
    "8,50" + Enter, towards the mouse): its width their distance, its foot at the first one's height, read from the
    side the face looks to. One undo step; Esc: left as it was."""

    name = "facade_image"
    accepts_typing = True
    title = "tool.facade_image"

    def __init__(self, host):
        super().__init__(host)
        self.only = None              # the image to stand up (the dialog's Pôr numa fachada)
        self._a = self._normal = self._end = None

    def _image(self):
        return next((i for i in self.doc.images if i.uid == self.only), None)

    def hint(self):
        if self._image() is None:
            return t("hint.facade_image.none")
        return t("hint.facade_image.second") if self._a is not None else t("hint.facade_image.first")

    def vcb_title(self):
        return t("vcb.length")

    def _level(self, image):
        return next((float(z) for g, _n, z in self.doc.storeys() if g == image.storey), 0.0)

    def _first(self, x, y, modifiers):
        """The point clicked on a face and that face's way out (horizontal), or (None, None)."""
        hit = self.viewport.pick_point(x, y)
        if hit is None or hit[1] is None:
            return None, None
        obj = self.doc.get(hit[0])
        if obj is None:
            return None, None
        normal = np.asarray(obj.mesh.face_normal(hit[1]), dtype=float)
        if not obj.is_bim:
            normal = np.asarray(obj.matrix, dtype=float)[:3, :3] @ normal
        flat = np.array((normal[0], normal[1], 0.0))
        if np.linalg.norm(flat) < 0.5:                       # (a floor, a roof: not a facade)
            return None, None
        found, _snap, _hit = infer_point(self.viewport, x, y, None, modifiers)
        p = found.point.copy() if found is not None else np.asarray(hit[2], dtype=float)
        return p, flat / np.linalg.norm(flat)

    def _second(self, x, y, modifiers):
        """A point on the facade's plane through the first one."""
        found, _snap, _hit = infer_point(self.viewport, x, y, self._a, modifiers)
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, self._a, self._normal)
        if found is not None and abs(float((found.point - self._a) @ self._normal)) < 0.01:
            p = found.point.copy()
        return p

    def _stood(self, end):
        image = self._image()
        if image is None:
            return None
        end = np.array((end[0], end[1], self._a[2]))
        return image.stood(self._a, end, self._normal, self._level(image))

    def _preview(self, end):
        image = self._stood(end)
        if image is None:
            return
        c = image.corners3d(self._level(image))
        segs = [p for k in range(4) for p in (c[k], c[(k + 1) % 4])]
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))
        self.host.set_vcb(format_length(image.width, decimal_sep()))

    def pointer_move(self, x, y, modifiers):
        if self._a is None:
            return
        p = self._second(x, y, modifiers)
        if p is not None:
            self._end = p
            self._preview(p)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        if button != LEFT or self._image() is None:
            return
        if self._a is None:
            p, normal = self._first(x, y, modifiers)
            if p is None:
                self.host.message(t("err.facade_image_face"), warning=True)
                return
            self._a, self._normal = p, normal
            self.host.set_hint(self.hint())
            return
        p = self._second(x, y, modifiers)
        if p is not None:
            self._apply(p)

    def typed(self, text):
        width = parse_length(text)
        if width is None or width <= 0 or self._a is None or self._end is None:
            self.host.message(t("err.bad_value", t=text), warning=True)
            return
        d = (self._end - self._a)[:2]
        if np.linalg.norm(d) < 1e-9:
            d = np.array((-self._normal[1], self._normal[0]))
        d = d / np.linalg.norm(d) * width
        self._apply(self._a + np.array((d[0], d[1], 0.0)))

    def _apply(self, end):
        image, done = self._image(), self._stood(end)
        if done is None:
            return
        images = [done if i.uid == image.uid else i for i in self.doc.images]
        self.doc.execute(ImagesChange(self.doc.images, images, t("cmd.facade_image")))
        self.host.message(t("info.facade_image", f=image.name, w=format_length(done.width, decimal_sep()),
                            h=format_length(done.height, decimal_sep())))
        self._a = self._normal = self._end = None
        self.only = None
        self.viewport.clear_overlays()
        self.host.set_tool("select")

    def cancel(self):
        self._a = self._normal = self._end = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
        self.host.set_vcb("")


class CropImageTool(Tool):
    """Recortar (0.209, Phase 7, step 2): the part of a background image kept — a click at one corner of it, a click
    at the other (on the picture, its whole frame shown meanwhile): the rest no longer drawn, on screen and on
    paper. One undo step; the dialog's «Inteira» shows it all again."""

    name = "crop_image"
    title = "tool.crop_image"

    def __init__(self, host):
        super().__init__(host)
        self.only = None              # the image to crop (the dialog's Recortar)
        self._a = None                # the first corner (fractions across, up)

    def _image(self):
        return next((i for i in self.doc.images if i.uid == self.only), None)

    def _level(self, image):
        return next((float(z) for g, _n, z in self.doc.storeys() if g == image.storey), 0.0)

    def hint(self):
        if self._image() is None:
            return t("hint.crop_image.none")
        return t("hint.crop_image.second") if self._a is not None else t("hint.crop_image.first")

    def _on_picture(self, x, y):
        """Where the mouse is on the image's whole frame: (across, up) fractions — None off its plane / outside."""
        image = self._image()
        if image is None:
            return None
        level = self._level(image)
        corner = image.corners3d(level)[0]
        normal = image.front() if image.vertical else np.array((0.0, 0.0, 1.0))
        origin, direction = self.viewport.ray(x, y)
        p = ray_plane(origin, direction, corner, normal)
        if p is None:
            p = ray_plane(origin, direction, corner, -normal)
        return None if p is None else image.fraction(p, level)

    def _show(self, b=None):
        image = self._image()
        level = self._level(image)
        ll, lr, _ur, ul = image.corners3d(level)
        across, up = lr - ll, ul - ll
        lift = image.front() * 0.01 if image.vertical else np.array((0.0, 0.0, 0.01))
        segs = []
        frame = [ll, lr, lr + up, ul]
        for k in range(4):                                   # (its whole frame)
            segs += [frame[k] + lift, frame[(k + 1) % 4] + lift]
        if self._a is not None and b is not None:            # (the part kept)
            s0, s1 = sorted((self._a[0], b[0]))
            r0, r1 = sorted((self._a[1], b[1]))
            part = [ll + across * s + up * r + lift for s, r in ((s0, r0), (s1, r0), (s1, r1), (s0, r1))]
            for k in range(4):
                segs += [part[k], part[(k + 1) % 4]]
        self.viewport.show_polygon([], segments=segs, colors=[PREVIEW] * len(segs))

    def activate(self):
        super().activate()
        self._a = None
        if self._image() is not None:
            self._show()

    def pointer_move(self, x, y, modifiers):
        if self._image() is None:
            return
        b = self._on_picture(x, y)
        if b is not None:
            self._show(tuple(min(max(c, 0.0), 1.0) for c in b))

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.cancel()
            return
        image = self._image()
        if button != LEFT or image is None:
            return
        f = self._on_picture(x, y)
        if f is None or not (-0.02 <= f[0] <= 1.02 and -0.02 <= f[1] <= 1.02):
            self.host.message(t("err.crop_image_outside"), warning=True)
            return
        if self._a is None:
            self._a = f
            self.host.set_hint(self.hint())
            return
        done = image.cropped(self._a, f)
        if done is None:
            self.host.message(t("err.crop_image_thin"), warning=True)
            return
        images = [done if i.uid == image.uid else i for i in self.doc.images]
        self.doc.execute(ImagesChange(self.doc.images, images, t("cmd.crop_image")))
        self.host.message(t("info.crop_image", f=image.name))
        self._a = None
        self.only = None
        self.viewport.clear_overlays()
        self.host.set_tool("select")

    def cancel(self):
        self._a = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())