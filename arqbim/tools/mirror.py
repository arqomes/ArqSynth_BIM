"""Mirror (0.108), as Revit's Mirror – Draw Axis: with things selected, two clicks give the mirror axis (a line
in plan, with the snaps and alignments); the selection goes to the other side of it — or, Ctrl (or the
contextual bar), mirror-image copies are made there. While the second point is sought, the selection's outline
is shown reflected."""

import numpy as np

from ..i18n import t
from ..ifc.mirror import reflection
from ..model import bim
from ..render.viewport import PREVIEW
from .base import LEFT, RIGHT, Option
from .bim_draw import _PointTool


class MirrorTool(_PointTool):
    name = "mirror"
    placement = True                     # (Esc: back to Select)
    on_storey = False
    accepts_typing = False
    common_keys = frozenset(("x", "y", "n"))
    keys_help = "keys.mirror"

    def common_key(self, name):
        return self.lock_key(name)

    def __init__(self, host):
        super().__init__(host)
        self.copy = False
        self._start = None

    def activate(self):
        self.copy = False
        self._start = None
        super().activate()

    def options(self):
        return [Option("copy", t("ctx.copy"), "toggle", self.copy)]

    def set_option(self, key, value):
        if key == "copy" and bool(value) != self.copy:
            self.ctrl_tap()

    def ctrl_tap(self):
        self.copy = not self.copy
        self.host.set_hint(self.hint())
        self.host.message(t("info.copy_on" if self.copy else "info.copy_off"))

    def _ids(self):
        return [i for i in self.viewport.selection if self.doc.get(i) is not None]

    def hint(self):
        if not self._ids():
            return t("hint.mirror_none")
        if self._start is None:
            return t("hint.mirror")
        return t("hint.mirror_2", copy=t("hint.mirror_copy") if self.copy else "")

    def _outline(self, mat):
        """The selection's outline (its objects' bottom boxes) reflected by `mat`."""
        segs = []
        for i in self._ids():
            obj = self.doc.get(i)
            v = np.asarray(obj.mesh.verts, dtype=float)
            if not len(v):
                continue
            v = (obj.matrix @ np.column_stack((v, np.ones(len(v)))).T).T[:, :3]
            lo, hi = v.min(axis=0), v.max(axis=0)
            ring = [np.array((x, y, lo[2])) for x, y in ((lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1]))]
            ring = [(mat @ np.append(p, 1.0))[:3] for p in ring]
            segs += [q for a, b in zip(ring, ring[1:] + ring[:1]) for q in (a, b)]
        return segs

    def pointer_move(self, x, y, modifiers):
        p, snap = self._point(x, y, None if self._start is None else self._start[2], self._start, modifiers)
        if p is None:
            return
        self._hover = (p, snap)
        if self._start is None or np.linalg.norm((p - self._start)[:2]) < 1e-6:
            self.viewport.show_marker(p)
            return
        mat = reflection(self._start, p)
        d = (p - self._start) / np.linalg.norm(p - self._start)
        axis = [self._start - d * 50.0, self._start + d * 50.0]
        segs = self._outline(mat)
        self.viewport.show_lines(axis + segs, [PREVIEW] * (2 + len(segs)))
        self.viewport.show_marker(p)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            if self._start is not None:
                self.cancel()
            else:
                self.host.set_tool("select")
            return
        if button != LEFT:
            return
        ids = self._ids()
        if not ids:
            self.host.message(t("hint.mirror_none"), warning=True)
            return
        p, _snap = self._point(x, y, None if self._start is None else self._start[2], self._start, modifiers)
        if p is None:
            return
        if self._start is None:
            self._start = p
            self.host.set_hint(self.hint())
            return
        if np.linalg.norm((p - self._start)[:2]) < 1e-6:
            return
        copy = self.copy or "Control" in (modifiers or ())
        try:
            made, left_out = bim.mirror_objects(self.doc, ids, self._start[:2], p[:2], copy=copy)
        except ValueError as exc:
            from ..i18n import refusal
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self.cancel()
            return
        self.cancel()
        if copy and made:
            self.viewport.set_selection(set(made))
        text = t("info.mirrored", n=len(made), copy=t("info.mirrored_copy") if copy else "")
        if left_out:
            text += t("info.mirror_left_out", k=len(left_out))
        self.host.message(text)

    def cancel(self):
        self._start = None
        self.viewport.clear_overlays()
        self.host.set_hint(self.hint())
