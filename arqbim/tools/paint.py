"""Paint (0.391), as SketchUp's Paint Bucket (B) — the ArqSynth Modeler's «Pintura (balde)»: a material from the
Materials Browser (it opens beside the view; one click chooses) laid on what is clicked:

- a click: that face of the element (the wall's face, the slab's top, a roof's slope…);
- Ctrl + click: all the element's faces (SketchUp: the connected faces);
- Shift + click: every face in the model painted with the clicked face's paint, the new one instead (SketchUp's
  «replace»);
- Alt + click: the eyedropper — the material of the face clicked becomes the bucket's (its paint, or what it is made
  of there).

«Sem pintura» (SketchUp's Default material) takes the paint off. The paint is the element's (model/paint.py): its
type and layers stay as they were. (0.392) A sketch's faces too, each its own (PolyMesh.paint): a click the face
(its pieces joined by hidden edges), Ctrl the faces joined to it of the same colour — as SketchUp's Ctrl. Esc:
Select."""

import numpy as np

from ..core.sketch_geometry import face_world_normal
from ..i18n import lang, t
from ..ifc import catalog
from ..model import bim
from ..model import paint as paint_model
from .base import LEFT, RIGHT, SNAP_COLORS, Option, Tool

NONE = ""                               # «Sem pintura»


def material_name(key):
    if not key:
        return t("paint.none")
    spec = catalog.MATERIALS.get(key)
    if spec is None:
        return key
    return spec.name_pt if lang() == "pt" else spec.name_en


class PaintTool(Tool):
    name = "paint"
    keys_help = "keys.paint"

    def __init__(self, host):
        super().__init__(host)
        self.material = "tinta_branca"
        self._mods = ()

    # ------------------------------------------------------------ the bar and the browser

    def options(self):
        keys = sorted(catalog.MATERIALS, key=lambda k: (catalog.family_of(catalog.MATERIALS[k]) != "paint",
                                                         material_name(k).lower()))
        return [Option("material", t("ctx.paint_material"), "choice", self.material,
                       ((NONE, t("paint.none")),) + tuple((k, material_name(k)) for k in keys))]

    def set_option(self, key, value):
        if key == "material" and (value == NONE or value in catalog.MATERIALS):
            self.material = value
            self.host.show_paint_material(value)
        self.host.set_hint(self.hint())

    def choose(self, key):
        """A material clicked in the Materials Browser (or taken with the eyedropper): the bucket's now."""
        if key == NONE or key in catalog.MATERIALS:
            self.material = key
            self.host.set_hint(self.hint())
            self.host.show_paint_material(key)
            self.host.paint_bar_changed()

    def hint(self):
        return t("hint.paint", m=material_name(self.material))

    def activate(self):
        super().activate()
        self.host.open_paint_browser(True, self.material)

    def deactivate(self):
        super().deactivate()
        self.host.open_paint_browser(False, None)

    # ------------------------------------------------------------ the mouse

    def modifiers_changed(self, modifiers):
        self._mods = tuple(modifiers or ())

    def _what(self, mods):
        if "Alt" in mods:
            return "pick"
        if "Shift" in mods:
            return "replace"
        if "Control" in mods or "Ctrl" in mods:
            return "element"
        return "face"

    def _hit(self, x, y):
        """(element, face, world normal, point) under the mouse, or None — a sketch's face: (None, …)."""
        hit = self.viewport.pick_point(x, y)
        if hit is None:
            return None
        obj = self.doc.get(hit[0])
        if obj is None:
            return None
        normal = np.asarray(face_world_normal(obj.matrix, obj.mesh, hit[1]), dtype=float)
        normal = normal / max(np.linalg.norm(normal), 1e-12)
        return obj, hit[1], normal, np.asarray(hit[2], dtype=float)

    def pointer_move(self, x, y, modifiers):
        mods = tuple(modifiers or ()) or self._mods
        found = self._hit(x, y)
        if found is None:
            self.viewport.show_marker(None)
            self.viewport.show_tip("", None)
            return
        obj, face, _n, point = found
        what = self._what(mods)
        if what == "pick":
            tip = t("tip.paint_pick", m=material_name(self._material_at(obj, face, found[2], point)))
        elif what == "element" and not obj.is_bim:
            tip = t("tip.paint_connected", m=material_name(self.material))
        else:
            tip = t("tip.paint_" + what, m=material_name(self.material))
        self.viewport.show_marker(point, SNAP_COLORS["on_face"])
        self.viewport.show_tip(tip, point)

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT:
            return
        mods = tuple(modifiers or ()) or self._mods
        found = self._hit(x, y)
        if found is None:
            return
        obj, face, normal, point = found
        what = self._what(mods)
        key = self.material or None
        try:
            if what == "pick":
                taken = self._material_at(obj, face, normal, point)
                self.choose(taken or NONE)
                self.host.message(t("info.paint_picked", m=material_name(taken)))
                self.pointer_move(x, y, ())                 # (the tip with the bucket's new material)
                return
            if what == "replace":                          # (the elements' and the sketches': one undo step)
                old = self._paint_of(obj, face, normal, point)
                if not old:
                    self.host.message(t("err.paint_replace"), warning=True)
                    return
                mark = self.doc.undo_mark()
                n = bim.replace_paint(self.doc, old, key)
                n += paint_model.paint_sketch(self.doc, paint_model.replace_in_sketches(self.doc, old, key))
                self.doc.join_since(mark)
                self.host.message(t("info.paint_replace", a=material_name(old), m=material_name(self.material), n=n))
            elif not obj.is_bim:                           # (0.392) a sketch's faces
                faces = paint_model.sketch_connected(obj.mesh, face) if what == "element" else \
                    paint_model.sketch_face(obj.mesh, face)
                paint_model.paint_sketch(self.doc, [(obj, faces, key)])
                self.host.message(t("info.paint_sketch", m=material_name(self.material), n=len(faces), name=obj.name))
            elif what == "element":
                bim.paint_elements(self.doc, [obj.id], key)
                self.host.message(t("info.paint_element", m=material_name(self.material), name=obj.name))
            else:
                bim.paint_face(self.doc, obj.id, normal, point, key)
                self.host.message(t("info.paint_face", m=material_name(self.material), name=obj.name))
        except ValueError as exc:
            from ..i18n import refusal
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)

    def _material_at(self, obj, face, normal, point):
        """The eyedropper: an element's (its paint, else its own material there) or a sketch face's paint."""
        if not obj.is_bim:
            return obj.mesh.paint_of(face) if hasattr(obj.mesh, "paint_of") else None
        return paint_model.material_at(self.doc.ifc, obj, face, normal, point)

    def _paint_of(self, obj, face, normal, point):
        if not obj.is_bim:
            return obj.mesh.paint_of(face) if hasattr(obj.mesh, "paint_of") else None
        planes = paint_model.world_planes(self.doc.ifc, obj.id)
        if not planes:
            return None
        keys = paint_model.painted(planes, np.asarray(point, dtype=float).reshape(1, 1, 3).repeat(3, axis=1),
                                   np.asarray(normal, dtype=float).reshape(1, 3))
        return keys[0] or None

    def cancel(self):
        self.viewport.show_marker(None)
        self.viewport.show_tip("", None)
