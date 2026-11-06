"""The open project: an IFC model (the source of truth for BIM elements), free
sketch objects (not IFC), and one undo/redo stack for both.

Every user action is a Command (do/undo). Sketch commands keep before/after
snapshots. IFC commands run inside one IfcOpenShell transaction and are undone
with the IFC file's own undo, so both histories always stay in step.

Saving writes `<name>.ifc` (BIM) and, beside it, `<name>.arqbim` (sketches,
JSON). Sketches never go into the IFC file.
"""

import contextlib
import copy
import dataclasses
import itertools
import json
import os
import re
import threading
import uuid
from dataclasses import dataclass, field

import numpy as np

from ..core.mesh import PolyMesh, TriMesh
from ..i18n import lang
from . import geomcache
from .sheets import Placed, Sheet
from . import annotations as notes2d
from . import dimensions as dims_model
from . import graphic_styles as styles_model
from . import notes as notes_model
from . import presentation as presentation_model
from . import sheets as sheets_model
from . import view_styles as view_styles_model
from . import view_templates as templates_model


class SketchObject:
    """Free sketch geometry (not IFC yet): a polygon mesh with a placement."""

    is_bim = False
    _ids = itertools.count(1)

    def __init__(self, name, matrix, mesh, obj_id=None, component=None, curve=None, uid=None):
        self.id = obj_id if obj_id is not None else next(SketchObject._ids)
        # (0.395) A name of its own that outlives saving and opening (its id does not), given when a parametric surface
        # is made of its lines: the surface follows them when they change (Document._follow_curves)
        self.uid = uid
        self.name = name
        self.matrix = np.array(matrix, dtype=float)
        self.mesh = mesh
        # A component being edited: {"type", "guid", "name", "storey", "component"} (see model.bim.edit_component)
        self.component = dict(component) if component else None
        # (0.373) Loose lines that are one curve (an arc, a freehand line, a Bézier curve), picked whole as SketchUp's:
        # {"kind": "arc" | "freehand" | "bezier" | "curve", …its own data in the sketch's frame} (core/curves.py)
        self.curve = copy.deepcopy(curve) if curve else None

    def copy(self):
        return SketchObject(self.name, self.matrix, self.mesh.copy(), obj_id=self.id, component=self.component,
                            curve=self.curve, uid=getattr(self, "uid", None))


class BimObject:
    """Display of an IFC element. The element itself lives in Document.ifc;
    this only carries what the viewport and inferences need."""

    is_bim = True

    def __init__(self, guid, name, ifc_class, mesh, storey=None):
        self.id = guid
        self.name = name
        self.ifc_class = ifc_class
        self.matrix = np.eye(4)          # geometry comes in world coordinates
        self.mesh = mesh
        self.storey = storey             # GlobalId of its building storey (None if not in one)

    def copy(self):
        return self


@dataclass
class SectionView:
    """A section drawn with the Section tool: the vertical plane through `point` facing
    `normal` (where it looks). A view, not IFC: saved with the sketches (.arqbim). (0.358) ends: where its line
    starts and ends in the plan ((x, y), (x, y)), when its grips were dragged — else (None) across the building.
    (0.363) uid: the same whatever its name (its scene in the ArqSynth Presentation is known by it)."""
    name: str
    point: np.ndarray
    normal: np.ndarray
    ends: tuple = None
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass
class DetailView:
    """A detail view (0.133): a piece of another view — the plan of a storey, a section — inside the rectangle
    (x0, y0, x1, y1) of that view's 2D frame, at a scale of its own (1:20…), for the sheets; its callout drawn in
    the view it comes from. A view, not IFC: saved with the sketches."""
    name: str
    parent: tuple
    rect: tuple
    scale: int = 20
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass
class GridAxis:
    """An axis of the structural grid (0.67): its tag ("A", "1"…) and its two ends on the plan (x, y),
    program coordinates. Kept in the .arqbim file; written to the IFC as an IfcGrid when it is a valid
    one (axes both ways: IfcGrid's UAxes and VAxes may not be empty)."""
    tag: str
    start: tuple
    end: tuple
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)   # (0.92) the same whatever its tag: columns
    #                                                                tied to a crossing know their axes by it

    @property
    def numbered(self):
        """Running more along Y than X: one of the numbered axes (1, 2, 3… from left to right)."""
        return abs(self.end[1] - self.start[1]) >= abs(self.end[0] - self.start[0])


@dataclass
class View3D:
    """A named 3D view (0.64): where its camera is (Viewport.camera_snapshot, program coordinates).
    Its look and section box are its view properties (Document.view_props[("3d", uid)])."""
    name: str
    uid: str
    camera: dict = None


def view3d_name(n):
    return "3D {}".format(n)


class Guide:
    """An infinite construction line (Tape Measure). Not IFC: saved with the sketches."""

    _ids = itertools.count(1)

    def __init__(self, point, direction, guide_id=None):
        self.id = guide_id if guide_id is not None else "g{}".format(next(Guide._ids))
        self.point = np.array(point, dtype=float)
        self.direction = np.array(direction, dtype=float)


def _label(key):
    from ..i18n import t
    return t(key)


GUIDES_CHANGED = "__guides__"   # marker in the change set: the viewport redraws the guides
STOREY_CHANGED = "__storey__"   # marker: the active storey (work level) changed
VIEWS_CHANGED = "__views__"     # marker: the named sections or the sheets changed (the Project panel lists them)
GRID_CHANGED = "__grid__"       # marker: the structural grid's axes changed (0.67)
# the structural grid's settings (0.91): which axes are numbered ("numbers_y": those running along Y — 1, 2, 3…
# from left to right —, the others lettered; "letters_y": the other way), its dimensions in the plans, the
# radius (m) of its bubbles
GRID_DEFAULTS = {"scheme": "numbers_y", "dims": False, "bubble": 0.35}
DIMS_CHANGED = "__dims__"       # marker: a dimension was added or removed
NOTES_CHANGED = "__notes__"     # marker: the coordination notes (BCF) changed
IMAGES_CHANGED = "__images__"   # marker: the background images changed (0.154)
CAD_CHANGED = "__cad__"         # marker: the CAD drawings linked changed (0.158)
CLOUD_CHANGED = "__clouds__"    # marker: the point clouds linked changed (0.161)


class Command:
    label = ""

    def do(self, doc):
        raise NotImplementedError

    def undo(self, doc):
        raise NotImplementedError


class AddObject(Command):
    def __init__(self, obj, label=""):
        self.obj, self.label = obj, label

    def do(self, doc):
        doc._put(self.obj.copy())

    def undo(self, doc):
        doc._drop(self.obj.id)


class RemoveObjects(Command):
    def __init__(self, objs, label=""):
        self.objs, self.label = [o.copy() for o in objs], label

    def do(self, doc):
        for o in self.objs:
            doc._drop(o.id)

    def undo(self, doc):
        for o in self.objs:
            doc._put(o.copy())


class ReplaceObjects(Command):
    """Some sketch objects become others in one step (e.g. closed lines -> a face)."""

    def __init__(self, remove, add, label=""):
        self.remove, self.add, self.label = [o.copy() for o in remove], [o.copy() for o in add], label

    def do(self, doc):
        for o in self.remove:
            doc._drop(o.id)
        for o in self.add:
            doc._put(o.copy())

    def undo(self, doc):
        for o in self.add:
            doc._drop(o.id)
        for o in self.remove:
            doc._put(o.copy())


class ReplaceMesh(Command):
    def __init__(self, obj_id, before, after, label=""):
        self.obj_id, self.before, self.after, self.label = obj_id, before.copy(), after.copy(), label

    def do(self, doc):
        doc._set_mesh(self.obj_id, self.after.copy())

    def undo(self, doc):
        doc._set_mesh(self.obj_id, self.before.copy())


class ReplaceMeshes(Command):
    """Several sketches change shape in one step (lines joined at a point that moves: 0.62)."""

    def __init__(self, changes, label=""):
        self.changes = [(obj_id, before.copy(), after.copy()) for obj_id, before, after in changes]
        self.label = label

    def do(self, doc):
        for obj_id, _before, after in self.changes:
            doc._set_mesh(obj_id, after.copy())

    def undo(self, doc):
        for obj_id, before, _after in self.changes:
            doc._set_mesh(obj_id, before.copy())


class GridChange(Command):
    """The structural grid changed (0.67): its axes (Document.grids) and the IfcGrid written from them,
    as one undo step — the IFC part is an IfcCommand of its own, run and undone with it."""

    def __init__(self, label, before, after, ifc_command, settings=None):
        """settings: (before, after) of Document.grid_settings changed in the same step (0.91), or None."""
        self.label = label
        self.before, self.after = copy.deepcopy(list(before)), copy.deepcopy(list(after))
        self.ifc_command = ifc_command
        self.settings = copy.deepcopy(settings)

    def do(self, doc):
        doc.grids = copy.deepcopy(self.after)
        if self.settings is not None:
            doc.grid_settings = dict(self.settings[1])
        self.ifc_command.do(doc)
        doc._changed |= {GRID_CHANGED, DIMS_CHANGED}

    def undo(self, doc):
        self.ifc_command.undo(doc)
        doc.grids = copy.deepcopy(self.before)
        if self.settings is not None:
            doc.grid_settings = dict(self.settings[0])
        doc._changed |= {GRID_CHANGED, DIMS_CHANGED}


class AddGuide(Command):
    def __init__(self, guide, label=""):
        self.guide, self.label = guide, label

    def do(self, doc):
        doc.guides[self.guide.id] = self.guide
        doc._changed.add(GUIDES_CHANGED)

    def undo(self, doc):
        doc.guides.pop(self.guide.id, None)
        doc._changed.add(GUIDES_CHANGED)


class RemoveGuides(Command):
    def __init__(self, guides, label=""):
        self.guides, self.label = list(guides), label

    def do(self, doc):
        for g in self.guides:
            doc.guides.pop(g.id, None)
        doc._changed.add(GUIDES_CHANGED)

    def undo(self, doc):
        for g in self.guides:
            doc.guides[g.id] = g
        doc._changed.add(GUIDES_CHANGED)


class ImagesChange(Command):
    """(0.154) The background images before and after a change (imported, calibrated, placed, removed…): one
    undo step."""

    def __init__(self, before, after, label=""):
        self.before, self.after, self.label = list(before), list(after), label

    def do(self, doc):
        doc.images = list(self.after)
        doc._changed.add(IMAGES_CHANGED)

    def undo(self, doc):
        doc.images = list(self.before)
        doc._changed.add(IMAGES_CHANGED)


class CadLinksChange(Command):
    """(0.158) The CAD drawings linked before and after a change (linked, moved, layers hidden, removed…): one
    undo step."""

    def __init__(self, before, after, label=""):
        self.before, self.after, self.label = list(before), list(after), label

    def do(self, doc):
        doc.cad_links = list(self.after)
        doc._changed.add(CAD_CHANGED)

    def undo(self, doc):
        doc.cad_links = list(self.before)
        doc._changed.add(CAD_CHANGED)


class CloudLinksChange(Command):
    """(0.161) The point clouds linked before and after a change: one undo step."""

    def __init__(self, before, after, label=""):
        self.before, self.after, self.label = list(before), list(after), label

    def do(self, doc):
        doc.cloud_links = list(self.after)
        doc._changed.add(CLOUD_CHANGED)

    def undo(self, doc):
        doc.cloud_links = list(self.before)
        doc._changed.add(CLOUD_CHANGED)


class ViewsChange(Command):
    """A change to the views kept in the .arqbim file — sections, sheets, which view a dimension
    is in — as one undo step: undone by putting back what they were (sections and sheets as
    copies; the dimension objects themselves stay, so the dimension commands keep working)."""

    def __init__(self, label, change):
        self.label, self.change = label, change
        self.result = None
        self._before = self._after = None

    @staticmethod
    def _state(doc):
        return (copy.deepcopy(doc.sections), doc.last_section, copy.deepcopy(doc.sheets),
                list(doc.dimensions), [d.view for d in doc.dimensions],
                copy.deepcopy(doc.templates), dict(doc.view_templates), copy.deepcopy(doc.title_block),
                copy.deepcopy(doc.view_props), copy.deepcopy(doc.views3d),
                list(doc.annotations), [a.view for a in doc.annotations], copy.deepcopy(doc.details),
                list(doc.view_styles), copy.deepcopy(doc.presentation), copy.deepcopy(doc.panoramas))

    @staticmethod
    def _put_back(doc, state):
        sections, last, sheets, dims, views, templates, assigned, title_block, view_props, views3d, anns, \
            ann_views, details, view_styles, presentation, panoramas = state
        doc.view_styles = list(view_styles)             # (the view styles, 0.315: frozen, shared)
        doc.presentation = copy.deepcopy(presentation)  # (the scenes for the Presentation, 0.363)
        doc.panoramas = copy.deepcopy(panoramas)        # (the 360° panoramas, 0.368)
        doc.details = copy.deepcopy(details)            # (the detail views, 0.133)
        doc.sections, doc.last_section = copy.deepcopy(sections), last
        doc.sheets = copy.deepcopy(sheets)
        doc.dimensions = list(dims)
        for dim, view in zip(dims, views):
            dim.view = view
        doc.templates, doc.view_templates = copy.deepcopy(templates), dict(assigned)
        doc.title_block = copy.deepcopy(title_block)
        doc.view_props = copy.deepcopy(view_props)
        doc.views3d = copy.deepcopy(views3d)
        doc.annotations = list(anns)                    # (the drawings in the views, 0.120: as the dimensions)
        for ann, view in zip(anns, ann_views):
            ann.view = view

    def do(self, doc):
        if self._after is None:                     # the first time: make the change
            self._before = self._state(doc)
            self.result = self.change(doc)
            self._after = self._state(doc)
        else:                                       # redo
            self._put_back(doc, self._after)
        doc._changed |= {VIEWS_CHANGED, DIMS_CHANGED}

    def undo(self, doc):
        self._put_back(doc, self._before)
        doc._changed |= {VIEWS_CHANGED, DIMS_CHANGED}


class JoinedCommand(Command):
    """(0.187) Several commands done one after the other, undone and redone as one step (a change made in the
    Properties to several elements at once)."""

    def __init__(self, commands, label=None):
        self.commands = list(commands)
        self.label = label or (self.commands[0].label if self.commands else "")

    def do(self, doc):                              # (only on redo: each was done when it was executed)
        for cmd in self.commands:
            cmd.do(doc)

    def undo(self, doc):
        for cmd in reversed(self.commands):
            cmd.undo(doc)


class IfcCommand(Command):
    """IFC changes made by `action(ifc_model)` inside one IFC transaction, plus
    optional sketches removed/added in the same step (e.g. Classify turns a
    sketch volume into a wall)."""

    def __init__(self, label, action, remove_sketches=(), add_sketches=(), changed=(), touched=(), plan=True):
        self.label, self.action = label, action
        self.plan = plan               # (0.267) False: nothing moves in the plan (a height…): rooms ring as they did
        self.remove_sketches = [o.copy() for o in remove_sketches]
        self.add_sketches = [o.copy() for o in add_sketches]
        self.changed = list(changed)   # existing elements whose shape changes (e.g. a wall that gets a door)
        self.touched = list(touched)   # existing elements whose data (not shape) changes (e.g. their phase)
        self.result = None
        self._ran = False

    def _touch(self, doc):
        for guid in self.touched:
            if guid in doc.objects:
                doc._changed.add(guid)
                doc._status.pop(guid, None)
                doc._systems.pop(guid, None)

    def do(self, doc):
        if not self._ran:
            doc.ifc.begin()
            try:
                self.result = self.action(doc.ifc)
                # what it made on a typical floor goes on its equal storeys too, in this same step (0.90)
                self.changed += [g for g in doc.ifc.replicate_typical() if g not in self.changed]
                # the carpentry of the roofs it changed made again under them (0.276)
                self.changed += [g for g in doc.ifc.follow_carpentry(self.changed) if g not in self.changed]
                # …and their tiles laid again on them (0.279)
                self.changed += [g for g in doc.ifc.follow_tiles(self.changed) if g not in self.changed]
                # the walls and columns tied by their top to a slab it changed follow it (0.106)
                self.changed += [g for g in doc.ifc.follow_slab_tops(self.changed) if g not in self.changed]
                # …and those tied by their base to a slab or footing (0.302)
                self.changed += [g for g in doc.ifc.follow_slab_bases(self.changed) if g not in self.changed]
                # …and those tied to a roof (0.112)
                self.changed += [g for g in doc.ifc.follow_roof_tops(self.changed) if g not in self.changed]
                # the reveals of the walls it changed made again to fit them (0.305)
                doc.ifc.follow_reveals(self.changed)
                # the curtain walls it made or changed that embed themselves cut their walls again (0.188)
                embedded = doc.ifc.follow_embedded(list(self.changed) + list(doc.ifc.made or ()))
                self.changed += [g for g in embedded if g not in self.changed]
                # the finishes on the walls it changed made again on them (0.119)
                self.changed += [g for g in doc.ifc.follow_claddings(self.changed) if g not in self.changed]
                # the reinforcement of the members it changed laid out again on them (0.166)
                doc.ifc.follow_rebars(self.changed)
                # …and the worktops over the cabinets it changed (0.170)
                self.changed += [g for g in doc.ifc.follow_worktops(self.changed) if g not in self.changed]
                # …and the combined footings under the columns it changed (0.249)
                self.changed += [g for g in doc.ifc.follow_combined_footings(self.changed) if g not in self.changed]
                # …and the ovens in the tall units it made or changed (0.242)
                ovens = doc.ifc.follow_ovens(list(self.changed) + list(doc.ifc.made or ()))
                self.changed += [g for g in ovens if g not in self.changed]
                # …and the profiles along the walls it changed, round their rooms, cut at their doors (0.174)
                self.changed += [g for g in doc.ifc.follow_profiles(self.changed) if g not in self.changed]
                # whether the walls of the storeys where walls changed are on the outside, their doors too (0.267)
                storeys, rooms = (doc.ifc.external_storeys(self.changed) if self.plan else set()), {}
                if storeys:
                    doc.ifc.update_external(storeys, rooms)
                # (0.297) the windows it made, and those of those storeys, turned with their peitoril to the outside
                windows = [g for g in doc.ifc.made or () if doc.ifc.by_guid(g) is not None
                           and doc.ifc.by_guid(g).is_a("IfcWindow")]
                windows += [g for s in storeys for g in doc.ifc.storey_elements(s)
                            if g not in windows and doc.ifc.by_guid(g).is_a("IfcWindow")]
                for g in doc.ifc.orient_windows(windows, lang(), rooms) if windows else ():
                    self.changed += [h for h in (g, doc.ifc.host_wall(g)) if h and h not in self.changed]
                # what the program knows of the elements it made or changed, in their standard IFC sets (0.266)
                doc.ifc.fill_ifc_data(list(self.changed) + list(doc.ifc.made or ()))
                # the rooms of the storeys it changed found again from their walls (0.99)
                doc.ifc.update_spaces(doc.ifc.touched_storeys(self.changed))
            except Exception:
                doc.ifc.discard()   # roll back whatever was half-done
                raise
            doc.ifc.end()
            self._ran = True
        else:
            doc.ifc.redo()
        for o in self.remove_sketches:
            doc._drop(o.id)
        for o in self.add_sketches:
            doc._put(o.copy())
        doc._sync_ifc(changed=self.changed, delta=doc.ifc.last_changes())
        self._touch(doc)

    def undo(self, doc):
        doc.ifc.undo()
        for o in self.add_sketches:
            doc._drop(o.id)
        for o in self.remove_sketches:
            doc._put(o.copy())
        doc._sync_ifc(changed=self.changed, delta=doc.ifc.last_changes(undone=True))
        self._touch(doc)


class Document:
    def __init__(self, ifc_model=None):
        from ..ifc.model import IfcModel
        self.ifc = ifc_model or IfcModel.new(lang=lang())
        self.objects = {}           # id -> SketchObject | BimObject
        self.guides = {}            # id -> Guide
        self.active_storey = None   # GlobalId of the storey being drawn on (the work level)
        self._no_geometry = set()   # elements the geometry kernel gave nothing for (not retried every change)
        self.cache_hits = 0         # shapes read from the geometry cache at the last opening
        self.loading = False        # shown from the geometry cache, IFC still being read: nothing to edit yet
        self.sections = []          # SectionView, named (kept in the .arqbim file)
        self.last_section = None    # index of the section shown last (F5)
        self.sheets = []            # Sheet: views laid out on paper (kept in the .arqbim file)
        self.dimensions = []        # dimensions.Dimension, each in its view (kept in the .arqbim file)
        self.annotations = []       # annotations.Annotation: drawn in a view (0.120; kept with the dimensions)
        self.dim_style = dict(dims_model.STYLE_DEFAULTS)   # the dimensions' style (0.124; kept with them)
        self.graphic_style = styles_model.defaults()      # hatches and pens on paper (0.126; kept with the views)
        self.schedule_defs = []     # schedules.ScheduleDef: the project's own schedules (0.131; kept with the views)
        self.details = []           # DetailView: the detail views (0.133; kept with the views)
        self.clash_status = {}      # clash key ("a|b") -> "new" | "active" | "resolved" | "approved" (0.150)
        self.images = []            # images.BackgroundImage: pictures laid on the storeys (0.154; kept with the views)
        self.cad_links = []         # cad_links.CadLink: DXF drawings laid on the storeys (0.158; kept with the views)
        self.cloud_links = []       # cloud_links.CloudLink: point clouds in the model (0.161; kept with the views)
        self.templates = []         # view_templates.ViewTemplate (kept in the .arqbim file)
        self.view_styles = []       # view_styles.ViewStyle: the project's own (0.315; kept with the views)
        self.notes = []             # notes.Note: coordination notes (kept in <name>.bcfzip beside the IFC)
        self.view_templates = {}    # view key (("plan", storey) | ("section", name) | ("elevation", side)) -> template uid
        self.view_props = {}        # view key (those, or ("3d",)) -> its own properties (view_templates.OWN_FIELDS),
        #                             used when it has no template (kept in the .arqbim file)
        self.views3d = []           # View3D: the named 3D views ("3d", uid) — the 3D view ("3d",) is always there
        self.presentation = presentation_model.empty()   # (0.363) the scenes for the ArqSynth Presentation: their
        #                                                  order, entry, transitions… (model/presentation.py)
        self.panoramas = []         # (0.368) the 360° panoramas: [{uid, name, file, eye, forward, storey}]
        #                             (model/panoramas.py; their pictures beside the project)
        self.work_plane = None      # (0.412) model/work_plane.WorkPlane the drawing starts on in 3D (None: the level)
        self.grids = []             # GridAxis: the structural grid's axes (kept in the .arqbim file; IfcGrid in the IFC)
        self.grid_settings = dict(GRID_DEFAULTS)    # its tags, dimensions, bubbles (0.91; kept in the .arqbim file)
        self._grid_dims = {}        # view -> the grid's dimensions drawn in it (made again when the grid changes)
        self.title_block = {}       # the sheets' title block: sheets.TITLE_FIELDS -> text (kept in the .arqbim file)
        self.open_views = None      # the window's view tabs as saved ({"tabs": [{"key", "camera"}], "current"}): set
        #                             by the window before saving, read back at opening (ui/view_tabs.py)
        self._symbols = {}         # GlobalId -> plan symbol segments or None, made when first asked
        self._signs = {}           # (0.292) GlobalId -> elevation sign segments or None, the same
        self._status = {}           # GlobalId -> phase ("NEW", "EXISTING"…) or None, read when first asked
        self._systems = {}          # GlobalId -> its system's key (0.141) or None, read when first asked
        self.path = None            # .ifc path once saved/opened
        self.modified = False
        self._undo, self._redo = [], []
        self._listeners = []
        self.revision = 0           # (0.225) one more at every change told to the listeners
        # (0.254) set by the window: fn(call) runs `call` in its own thread — a change made in a worker thread
        # (run_busy) is told to the listeners (the window, the 3D view) there, never from the worker
        self.relay = None
        self._changed, self._removed = set(), set()
        self._counter = 0
        self._sync_ifc()
        self._changed.clear()

    # ------------------------------------------------------------ undo / redo

    def subscribe(self, fn):
        """fn(changed_ids, removed_ids) is called after every change."""
        self._listeners.append(fn)

    def execute(self, cmd):
        with self.ifc.remembering():                    # (0.225: what one edit asks again and again, once)
            cmd.do(self)
            follow = self._follow_curves()              # (0.395: the surfaces made of the lines it changed)
            if follow is not None:
                cmd = JoinedCommand([cmd, follow], cmd.label)
            self._undo.append(cmd)
            self._redo.clear()
            self.modified = True
            self._notify()
        return cmd

    def _follow_curves(self):
        """(0.395) When a change moved or reshaped the lines a parametric surface was made of (sketches with a uid),
        the surface made again from them, as part of the same step: the command that did it (done), or None."""
        moved = {}
        for obj_id in self._changed:
            obj = self.objects.get(obj_id)
            if obj is not None and not obj.is_bim and getattr(obj, "uid", None):
                moved[obj.uid] = obj
        if not moved or self.loading:
            return None
        found = self.ifc.surfaces_following(list(moved))
        if not found:
            return None
        from .surface_curves import sketch_chains
        chains = {uid: sketch_chains(obj) for uid, obj in moved.items()}
        language = lang()

        def action(ifc):
            done = []
            for guid, uids in found.items():
                try:
                    if ifc.follow_curves(guid, {u: chains[u] for u in uids}, language):
                        done.append(guid)
                except ValueError:                      # (a curve that no longer makes it: the surface stays)
                    continue
            return done

        cmd = IfcCommand("", action, changed=list(found))
        cmd.do(self)
        return cmd

    def undo(self):
        if not self._undo:
            return None
        with self.ifc.remembering():
            cmd = self._undo.pop()
            cmd.undo(self)
            self._redo.append(cmd)
            self.modified = True
            self._notify()
        return cmd

    def redo(self):
        if not self._redo:
            return None
        with self.ifc.remembering():
            cmd = self._redo.pop()
            cmd.do(self)
            self._undo.append(cmd)
            self.modified = True
            self._notify()
        return cmd

    def last_command(self):
        return self._undo[-1] if self._undo else None

    def undo_mark(self):
        """(0.187) Where the undo list is now, for join_since."""
        return len(self._undo)

    def join_since(self, mark, label=None):
        """(0.187) The commands executed since undo_mark() gave `mark` become one undo step; how many they were."""
        commands = self._undo[mark:]
        if len(commands) > 1:
            del self._undo[mark:]
            self._undo.append(JoinedCommand(commands, label))
        return len(commands)

    def can_undo(self):
        return bool(self._undo)

    def can_redo(self):
        return bool(self._redo)

    def next_number(self):
        """1, 2, 3... for default sketch names ("Esboço 1")."""
        self._counter += 1
        return self._counter

    def get(self, obj_id):
        return self.objects.get(obj_id)

    def sketches(self):
        return [o for o in self.objects.values() if not o.is_bim]

    # ------------------------------------------------------------ views (not IFC: kept in the .arqbim file)

    @property
    def section(self):
        """(point, normal) of the section shown last (F5), or None."""
        if self.last_section is None or not 0 <= self.last_section < len(self.sections):
            return None
        s = self.sections[self.last_section]
        return s.point, s.normal

    def _views_command(self, label, change):
        """Run change(doc) as one undo step (see ViewsChange). Returns what it returns."""
        return self.execute(ViewsChange(label, change)).result

    def add_section(self, point, normal):
        """A new named section ("Corte 3": one more than the highest number). Returns its index."""
        def change(doc):
            numbers = [int(m.group(1)) for s in doc.sections for m in [re.search(r"(\d+)$", s.name)] if m]
            doc.sections.append(SectionView(section_name(max(numbers, default=0) + 1),
                                            np.asarray(point, dtype=float), np.asarray(normal, dtype=float)))
            doc.last_section = len(doc.sections) - 1
            return doc.last_section
        return self._views_command(_label("cmd.section"), change)

    def rename_section(self, index, name):
        """A new name (the sheets and dimensions that show it follow). Refused (False) if another
        section has it."""
        name = name.strip()
        if not 0 <= index < len(self.sections) or not name or self.sections[index].name == name:
            self._views_changed()                 # (the panel shows the name it has)
            return False
        old = self.sections[index].name
        if any(s.name == name for k, s in enumerate(self.sections) if k != index):
            self._views_changed()
            return False

        def change(doc):
            doc.sections[index].name = name
            for sheet in doc.sheets:
                for view in sheet.views:
                    if view.kind == "section" and view.ref == old:
                        view.ref = name
            for dim in doc.dimensions + doc.annotations:
                if dim.view == ("section", old):
                    dim.view = ("section", name)
            for detail in doc.details:                     # (its detail views, 0.133)
                if detail.parent == ("section", old):
                    detail.parent = ("section", name)
            if ("section", old) in doc.view_templates:
                doc.view_templates[("section", name)] = doc.view_templates.pop(("section", old))
            if ("section", old) in doc.view_props:
                doc.view_props[("section", name)] = doc.view_props.pop(("section", old))
            return True
        return self._views_command(_label("cmd.rename_view"), change)

    def set_section_ends(self, index, a, b):
        """(0.358) A section's line from a to b in the plan (its grips dragged); None, None: across the building
        again. One undo step."""
        if not 0 <= index < len(self.sections):
            return

        def change(doc):
            s = doc.sections[index]
            s.ends = None if a is None else ((float(a[0]), float(a[1])), (float(b[0]), float(b[1])))
        self._views_command(_label("cmd.section_ends"), change)

    def flip_section(self, index):
        """(0.358) A section looking the other way (its arrows turned): the same line. One undo step."""
        if not 0 <= index < len(self.sections):
            return

        def change(doc):
            s = doc.sections[index]
            s.normal = -np.asarray(s.normal, dtype=float)
            if s.ends is not None:                      # (its start still on its left as it looks)
                s.ends = (s.ends[1], s.ends[0])
        self._views_command(_label("cmd.section_flip"), change)

    def remove_section(self, index):
        """Gone from the sheets too, with its dimensions."""
        if not 0 <= index < len(self.sections):
            return

        def change(doc):
            name = doc.sections.pop(index).name
            if doc.last_section is not None:
                doc.last_section = (None if doc.last_section == index else
                                    doc.last_section - (doc.last_section > index))
            for sheet in doc.sheets:
                sheet.views = [v for v in sheet.views if not (v.kind == "section" and v.ref == name)]
            doc.dimensions = [d for d in doc.dimensions if d.view != ("section", name)]
            doc.annotations = [a for a in doc.annotations if a.view != ("section", name)]
            gone = {d.uid for d in doc.details if d.parent == ("section", name)}        # (its details, 0.133)
            doc.details = [d for d in doc.details if d.uid not in gone]
            for sheet in doc.sheets:
                sheet.views = [v for v in sheet.views if not (v.kind == "detail" and v.ref in gone)]
            doc.view_templates.pop(("section", name), None)
            doc.view_props.pop(("section", name), None)
        self._views_command(_label("cmd.remove_section"), change)

    def set_panoramas(self, items, label=None):
        """(0.368) The 360° panoramas as given (model/panoramas.py): one undo step (their pictures stay on disk)."""
        from . import panoramas as panoramas_model
        items = panoramas_model.clean(items)

        def change(doc):
            doc.panoramas = copy.deepcopy(items)
        self._views_command(label or _label("cmd.panorama"), change)

    def set_presentation(self, data, label=None):
        """(0.363) The scenes for the ArqSynth Presentation as chosen (model/presentation.py): one undo step; nothing
        when it is the same."""
        data = presentation_model.clean(data)
        if data == presentation_model.clean(self.presentation):
            return

        def change(doc):
            doc.presentation = copy.deepcopy(data)
        self._views_command(label or _label("cmd.presentation"), change)

    def view3d(self, uid):
        return next((v for v in self.views3d if v.uid == uid), None)

    def add_view3d(self, camera, props=None):
        """A named 3D view ("3D 2": one more than the highest number) seen from `camera`, with the look and
        section box `props` (the view properties it starts from). One undo step. Returns its key."""
        uid = uuid.uuid4().hex

        def change(doc):
            numbers = [int(m.group(1)) for v in doc.views3d for m in [re.search(r"(\d+)$", v.name)] if m]
            doc.views3d.append(View3D(view3d_name(max(numbers, default=0) + 1), uid, copy.deepcopy(camera)))
            if props:
                doc.view_props[("3d", uid)] = copy.deepcopy(dict(props))
            return ("3d", uid)
        return self._views_command(_label("cmd.view3d_new"), change)

    def rename_view3d(self, uid, name):
        """A new name for a named 3D view; refused (False) if empty or another one has it."""
        name = name.strip()
        view = self.view3d(uid)
        if view is None or not name or name == view.name or any(v.name == name for v in self.views3d):
            self._views_changed()
            return False

        def change(doc):
            doc.view3d(uid).name = name
            return True
        return self._views_command(_label("cmd.rename_view"), change)

    def remove_view3d(self, uid):
        if self.view3d(uid) is None:
            return

        def change(doc):
            doc.views3d = [v for v in doc.views3d if v.uid != uid]
            doc.view_props.pop(("3d", uid), None)
            doc.view_templates.pop(("3d", uid), None)
        self._views_command(_label("cmd.view3d_remove"), change)

    def keep_view3d_camera(self, uid, camera):
        """Where a named 3D view was left (not an undo step: it is saved with the project)."""
        view = self.view3d(uid)
        if view is not None:
            view.camera = copy.deepcopy(camera)

    def template_of(self, view):
        """The view template given to a view, or None."""
        uid = self.view_templates.get(tuple(view)) if view is not None else None
        return next((tpl for tpl in self.templates if tpl.uid == uid), None) if uid else None

    def view_settings(self, view):
        """What a view shows: its template's settings, else its own properties, else the defaults
        (view_templates.Settings)."""
        if view is not None and view[0] == "detail":          # (a detail view: its parent's, at its scale, 0.133)
            detail = self.detail(view[1])
            if detail is None:
                return templates_model.settings_of(None, None)
            return dataclasses.replace(self.view_settings(detail.parent), scale=detail.scale)
        own = self.view_props.get(tuple(view)) if view is not None else None
        return templates_model.settings_of(self.template_of(view), own)

    def set_view_props(self, view, **changes):
        """A view's own properties (view_templates.OWN_FIELDS; None: back to the default), as the
        Properties panel changes them with nothing selected. One undo step; nothing if unchanged."""
        view = tuple(view)
        own = dict(self.view_props.get(view, {}))
        new = dict(own)
        for key, value in changes.items():
            if key not in templates_model.OWN_FIELDS:
                raise KeyError(key)
            if value is None or (key == "hidden" and not value):
                new.pop(key, None)
            else:
                new[key] = sorted(value) if key == "hidden" else tuple(value) if key == "rule" else value
        if new == own:
            return False

        def change(doc):
            if new:
                doc.view_props[view] = new
            else:
                doc.view_props.pop(view, None)
            return True
        return self._views_command(_label("cmd.view_props"), change)

    def set_element_hatches(self, view, guids, entry):
        """(0.331) Some elements' hatches in a view, as Revit's «Override graphics in view ▸ by element»: entry (cut
        foreground, cut background, surface foreground, surface background), each (pattern, colour) or None; None (or
        all four None): back to their category's and materials'. The view's own property, one undo step; False if
        unchanged."""
        view = tuple(view)
        kept = dict(self.view_settings(view).elements or {})
        entry = tuple(entry) if entry is not None and any(entry) else None
        for guid in guids:
            if entry is None:
                kept.pop(guid, None)
            else:
                kept[guid] = entry
        return self.set_view_props(view, elements=kept or None)

    def move_label(self, view, key, offset):
        """(0.238) A label of a view's drawing (model.drawings.Drawing.movable) moved by hand: `offset` (dx, dy) m
        from where the drawing puts it — None: back there. The view's own property, one undo step; False if
        unchanged."""
        labels = {k: tuple(v) for k, v in (self.view_props.get(tuple(view), {}).get("labels") or {}).items()}
        if offset is None:
            labels.pop(key, None)
        else:
            labels[key] = (float(offset[0]), float(offset[1]))
        return self.set_view_props(view, labels=labels or None)

    def view_style(self, key):
        """(0.315) The view style of a key (a built-in's name, a project style's uid); not known: the usual."""
        return view_styles_model.find(self.view_styles, key)

    def view_style_of(self, view):
        """(0.315) The view style a view is drawn with (its template's, else its own)."""
        return self.view_style(self.view_settings(view).style)

    def set_view_styles(self, styles):
        """(0.315) The project's view styles as edited (the window): one undo step. Views and templates given a style
        that is gone go back to the usual one."""
        styles = list(styles)

        def change(doc):
            doc.view_styles = styles
            uids = {s.uid for s in styles} | set(view_styles_model.BUILTIN)
            for view, own in list(doc.view_props.items()):
                if own.get("style") is not None and own["style"] not in uids:
                    own = dict(own)
                    own.pop("style")
                    if own:
                        doc.view_props[view] = own
                    else:
                        doc.view_props.pop(view)
            for tpl in doc.templates:
                if tpl.style is not None and tpl.style not in uids:
                    tpl.style = None
        return self._views_command(_label("cmd.view_styles"), change)

    def set_templates(self, templates):
        """The view templates as edited (the dialog): one undo step. Views given a template that
        is gone go back to the defaults."""
        templates = copy.deepcopy(list(templates))

        def change(doc):
            doc.templates = templates
            uids = {tpl.uid for tpl in templates}
            doc.view_templates = {k: v for k, v in doc.view_templates.items() if v in uids}
        self._views_command(_label("cmd.templates"), change)

    def assign_template(self, view, uid):
        """Give a view a template (uid), or none (None). One undo step."""
        view = tuple(view)
        if self.view_templates.get(view) == uid:
            return

        def change(doc):
            if uid is None:
                doc.view_templates.pop(view, None)
            else:
                doc.view_templates[view] = uid
        self._views_command(_label("cmd.assign_template"), change)

    def dimensions_of(self, view):
        """The dimensions drawn in a view (("plan", storey) | ("section", name) | ("elevation", side)); a plan's
        with the grid's own (0.91: between its axes, when the grid's settings say so — made from the axes, not
        kept, not picked)."""
        if view is None:
            return []
        out = [d for d in self.dimensions if d.view == tuple(view)]
        if view[0] == "plan" and self.grid_settings.get("dims") and self.grids:
            out += self.grid_dimensions(tuple(view))
        return out

    def grid_dimensions(self, view):
        """The grid's dimensions in a plan (dims_model.Dimension, tag "grid"), the same objects until the grid
        changes (the drawings that show them are kept)."""
        from . import dimensions as dims_model
        key = (view, tuple((a.tag, tuple(a.start), tuple(a.end)) for a in self.grids),
               float(self.grid_settings.get("bubble", GRID_DEFAULTS["bubble"])))
        found = self._grid_dims.get(view)
        if found is None or found[0] != key:
            z = next((level for g, _n, level in self.storeys() if g == view[1]), 0.0)
            found = (key, dims_model.grid_chains(self.grids, z, view, key[2]))
            self._grid_dims[view] = found
        return found[1]

    def annotations_of(self, view):
        """The lines, regions and texts drawn in a view (0.120)."""
        return [] if view is None else [a for a in self.annotations if a.view == tuple(view)]

    def schedules_changed(self):
        """(called by the command of the project's own schedules, 0.131)"""
        self._changed.add(VIEWS_CHANGED)

    def dimensions_changed(self):
        """(called by the dimension commands — and by those of the drawings in the views)"""
        self._changed.add(DIMS_CHANGED)

    def notes_changed(self):
        """(called by the notes commands)"""
        self._changed.add(NOTES_CHANGED)

    def reload_notes(self):
        """The notes read again from the project's .bcfzip (others' comments came in) — not an undo step."""
        if self.path:
            self.notes = _read_notes(self.path)
            self._changed.add(NOTES_CHANGED)
            self._notify()

    def change_notes(self, label, change):
        """Run change(doc) on the notes as one undo step. Returns what it returns."""
        return self.execute(notes_model.NotesChange(label, change)).result

    def _views_changed(self):
        self.modified = True
        self._changed.add(VIEWS_CHANGED)
        self._notify()

    @staticmethod
    def _new_sheet(doc):
        numbers = [int(m.group(1)) for s in doc.sheets for m in [re.search(r"(\d+)$", s.name)] if m]
        doc.sheets.append(Sheet(sheet_name(max(numbers, default=0) + 1)))
        return len(doc.sheets) - 1

    def add_sheet(self):
        """A new empty sheet ("Folha 2": one more than the highest number). Returns its index."""
        return self._views_command(_label("cmd.sheet"), self._new_sheet)

    def add_detail(self, parent, rect, scale=20):
        """A new detail view (0.133) of `parent` (("plan", storey) | ("section", name) | ("elevation", side))
        inside rect (x0, y0, x1, y1) of its 2D frame, at 1:scale: "Pormenor 2", one more than the highest
        number. One undo step. Returns its index."""
        x0, y0, x1, y1 = (float(c) for c in rect)
        rect = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

        def change(doc):
            numbers = [int(m.group(1)) for d in doc.details for m in [re.search(r"(\d+)$", d.name)] if m]
            doc.details.append(DetailView(_label("detail.name").format(n=max(numbers, default=0) + 1),
                                          tuple(parent), rect, int(scale)))
            return len(doc.details) - 1
        return self._views_command(_label("cmd.detail"), change)

    def change_detail(self, index, **changes):
        """A detail view's name, rectangle or scale changed (0.133). One undo step."""
        if not 0 <= index < len(self.details):
            return

        def change(doc):
            for key, value in changes.items():
                setattr(doc.details[index], key, tuple(value) if key == "rect" else value)
        self._views_command(_label("cmd.detail"), change)

    def remove_detail(self, index):
        """A detail view gone, from the sheets too (0.133). One undo step."""
        if not 0 <= index < len(self.details):
            return

        def change(doc):
            uid = doc.details.pop(index).uid
            for sheet in doc.sheets:
                sheet.views = [v for v in sheet.views if not (v.kind == "detail" and v.ref == uid)]
        self._views_command(_label("cmd.remove_detail"), change)

    def detail(self, uid):
        return next((d for d in self.details if d.uid == uid), None)

    def make_sheets(self, pages, paper="A3", template="full"):
        """(0.127, Sheets by storey) new sheets at once, one undo step: pages = [(name, [(kind, ref)…])], each a
        sheet on `paper` (0.129: with that title block template) with those views laid out. Returns how many."""
        def change(doc):
            for name, views in pages:
                doc.sheets.append(Sheet(name, paper if paper in sheets_model.PAPERS else "A3",
                                        [Placed(kind, ref) for kind, ref in views],
                                        template=template if template in sheets_model.TEMPLATES else "full"))
            return len(pages)
        return self._views_command(_label("cmd.sheets_by_storey"), change) if pages else 0

    def set_sheet_sets(self, index, names):
        """(0.128) The sets sheet `index` is in (names; a new name makes a new set). One undo step."""
        if not 0 <= index < len(self.sheets):
            return
        names = sheets_model.clean_sets(names)
        if names == self.sheets[index].sets:
            return

        def change(doc):
            doc.sheets[index].sets = list(names)
        self._views_command(_label("cmd.sheet_sets"), change)

    def rename_sheet(self, index, name):
        if not 0 <= index < len(self.sheets) or not name.strip() or self.sheets[index].name == name.strip():
            self._views_changed()                 # (the panel shows the name it has)
            return

        def change(doc):
            doc.sheets[index].name = name.strip()
        self._views_command(_label("cmd.rename_view"), change)

    def remove_sheet(self, index):
        if not 0 <= index < len(self.sheets):
            return

        def change(doc):
            del doc.sheets[index]
        self._views_command(_label("cmd.remove_sheet"), change)

    def put_on_sheet(self, index, kind, ref, also=()):
        """A view (see sheets.Placed) on sheet `index` (None: on a new sheet), laid out with the
        others. Returns (sheet index, its index on the sheet); a view already there is not put twice.
        also: more views (kind, ref) put after it in the same step (0.234: a member's section beside its
        reinforcement)."""
        if index is not None:
            for k, view in enumerate(self.sheets[index].views):
                if view.kind == kind and view.ref == ref:
                    return index, k

        def change(doc):
            i = self._new_sheet(doc) if index is None else index
            doc.sheets[i].views.append(Placed(kind, ref))
            k = len(doc.sheets[i].views) - 1
            for more in also:
                if not any((v.kind, v.ref) == tuple(more) for v in doc.sheets[i].views):
                    doc.sheets[i].views.append(Placed(*more))
            return i, k
        return self._views_command(_label("cmd.put_on_sheet"), change)

    def change_sheet(self, index, view=None, **changes):
        """Change a sheet (paper=…) or one of its views (view=k; scale=N or None, at=(x, y) mm or
        None). remove=True with view=k takes that view off the sheet; tidy=True puts every view
        back in its automatic place. One undo step."""
        remove = changes.pop("remove", False)
        tidy = changes.pop("tidy", False)

        def change(doc):
            sheet = doc.sheets[index]
            if tidy:
                for v in sheet.views:
                    v.at = None
            if view is None:
                for key, value in changes.items():
                    setattr(sheet, key, value)
            elif remove:
                del sheet.views[view]
            else:
                for key, value in changes.items():
                    setattr(sheet.views[view], key, value)
        self._views_command(_label("cmd.change_sheet"), change)

    def set_title_block(self, fields, index=None, name=None, number=None, revisions=None):
        """The title block: the project's fields ({sheets.TITLE_FIELDS: text}, the same on every
        sheet; 0.127: its own fields and the numbering too) and, for sheet `index`, its name, number
        ("" = automatic) and revisions ([{code, date, text}]). One undo step; nothing if nothing changes."""
        fields = sheets_model.read_title_fields({k: (v.strip() if isinstance(v, str) else v) for k, v in fields.items()})
        sheet = self.sheets[index] if index is not None and 0 <= index < len(self.sheets) else None
        name = name.strip() if sheet is not None and name is not None and name.strip() else None
        number = number.strip() if sheet is not None and number is not None else None
        revisions = sheets_model.clean_revisions(revisions) if sheet is not None and revisions is not None else None
        if fields == self.title_block and (sheet is None or (name in (None, sheet.name) and
                                                             number in (None, sheet.number) and
                                                             revisions in (None, sheet.revisions))):
            return

        def change(doc):
            doc.title_block = copy.deepcopy(fields)
            if sheet is not None:
                target = doc.sheets[index]
                target.name = name if name is not None else target.name
                target.number = number if number is not None else target.number
                target.revisions = revisions if revisions is not None else target.revisions
        self._views_command(_label("cmd.title_block"), change)

    # ------------------------------------------------------------ storeys

    def storeys(self):
        """[(GlobalId, name, level in m)], lowest first."""
        return self.ifc.storeys()

    def set_active_storey(self, guid):
        if guid in {g for g, _n, _z in self.storeys()} and guid != self.active_storey:
            self.active_storey = guid
            self._changed.add(STOREY_CHANGED)
            self._notify()

    def work_level(self):
        """Level (m) where drawing happens when nothing is under the cursor: the active storey's."""
        for g, _n, z in self.storeys():
            if g == self.active_storey:
                return z
        return 0.0

    def storey_band(self, guid):
        """(bottom, top) levels of a storey: from its level up to the next storey (top = inf for the highest)."""
        levels = self.storeys()
        for i, (g, _n, z) in enumerate(levels):
            if g == guid:
                return (z if i > 0 else -np.inf), (levels[i + 1][2] if i + 1 < len(levels) else np.inf)
        return -np.inf, np.inf

    # ------------------------------------------------------------ files

    def _replace_all(self, ifc_model, path, opened=None):
        self._removed |= set(self.objects)
        self.objects.clear()
        self.guides.clear()
        self._changed.add(GUIDES_CHANGED)
        self._undo.clear()
        self._redo.clear()
        self._counter = 0
        self.ifc = ifc_model
        self.path = path
        self.active_storey = None
        self.loading = False
        side = sidecar_path(path) if path else None
        with _reading_sidecar():                    # (0.255: parsed once for all its parts)
            self.sections, self.last_section = _read_sections(side, ifc_model.origin) if path else ([], None)
            self.sheets = _read_sheets(side) if path else []
            self.title_block = _read_title_block(side) if path else {}
            self.open_views = _read_open_views(side, ifc_model.origin) if path else None
            self.dimensions = _read_dimensions(side, ifc_model.origin) if path else []
            self.annotations = _read_annotations(side, ifc_model.origin) if path else []
            self.dim_style = _read_dim_style(side) if path else dict(dims_model.STYLE_DEFAULTS)
            self.graphic_style = _read_graphic_style(side) if path else styles_model.defaults()
            self.schedule_defs = _read_schedule_defs(side) if path else []
            self.details = _read_details(side, ifc_model.origin) if path else []
            self.clash_status = _read_clash_status(side) if path else {}
            self.images = _read_images(side, ifc_model.origin) if path else []
            self.cad_links = _read_cad_links(side, ifc_model.origin) if path else []
            self.cloud_links = _read_cloud_links(side, ifc_model.origin) if path else []
            self.templates, self.view_templates = _read_templates(side) if path else ([], {})
            self.view_styles = _read_view_styles(side) if path else []
            self.view_props = _read_view_props(side, ifc_model.origin) if path else {}
            self.views3d = _read_views3d(side, ifc_model.origin) if path else []
            self.presentation = _read_presentation(side) if path else presentation_model.empty()
            self.panoramas = _read_panoramas(side) if path else []
            self.grids = _read_grids(side, ifc_model.origin) if path else []
            self.grid_settings = _read_grid_settings(side) if path else dict(GRID_DEFAULTS)
            # (0.412) the storey's level for a new project; (0.413) the one kept with a project opened
            self.work_plane = _read_work_plane(side, ifc_model.origin) if path else None
        self._changed |= {IMAGES_CHANGED, CAD_CHANGED, CLOUD_CHANGED}
        if path and not self.grids and hasattr(ifc_model, "read_grids"):
            self.grids = [GridAxis(*axis) for axis in ifc_model.read_grids()]      # (a grid from another program)
        self._grid_dims = {}
        self._changed.add(GRID_CHANGED)
        self.notes = _read_notes(path) if path else []
        self._changed |= {DIMS_CHANGED, NOTES_CHANGED}
        self._symbols = {}
        self._signs = {}
        self._status = {}
        self._systems = {}
        self._no_geometry = set(opened.no_geometry) if opened else set()
        if opened:
            self._sync_ifc(shapes=opened.shapes, elements=opened.elements, storeys=opened.storeys)
        else:
            self._sync_ifc()

    def new(self):
        from ..ifc.model import IfcModel
        self._replace_all(IfcModel.new(lang=lang()), None)
        self.modified = False
        self._notify()

    def open(self, path):
        self.show_file(read_file(path))

    def show_preview(self, preview):
        """First part of opening a file opened before (Phase 2, step 7): its elements are shown
        straight away from the geometry cache, while its IFC is still being read — to look at,
        not to edit (self.loading; finish_opening ends it)."""
        self._removed |= set(self.objects)
        self.objects.clear()
        self.guides.clear()
        self._changed.add(GUIDES_CHANGED)
        self._undo.clear()
        self._redo.clear()
        self._counter = 0
        self.ifc = PreviewModel(preview.info)
        self.path = preview.path
        self.active_storey = None
        side, origin = sidecar_path(preview.path), self.ifc.origin
        with _reading_sidecar():                    # (0.255: parsed once for all its parts)
            self.sections, self.last_section = _read_sections(side, origin)
            self.sheets = _read_sheets(side)
            self.title_block = _read_title_block(side)
            self.open_views = _read_open_views(side, origin)
            self.dimensions = _read_dimensions(side, origin)
            self.annotations = _read_annotations(side, origin)
            self.dim_style = _read_dim_style(side)
            self.graphic_style = _read_graphic_style(side)
            self.schedule_defs = _read_schedule_defs(side)
            self.details = _read_details(side, origin)
            self.clash_status = _read_clash_status(side)
            self.images = _read_images(side, origin)
            self.cad_links = _read_cad_links(side, origin)
            self.cloud_links = _read_cloud_links(side, origin)
            self.templates, self.view_templates = _read_templates(side)
            self.view_styles = _read_view_styles(side)
            self.view_props = _read_view_props(side, origin)
            self.views3d = _read_views3d(side, origin)
            self.presentation = _read_presentation(side)
            self.panoramas = _read_panoramas(side)
            self.grids = _read_grids(side, origin)
            self.grid_settings = _read_grid_settings(side)
            self.work_plane = _read_work_plane(side, origin)         # (0.413)
        self._changed |= {IMAGES_CHANGED, CAD_CHANGED, CLOUD_CHANGED}
        self._grid_dims = {}
        self._changed.add(GRID_CHANGED)
        self.notes = _read_notes(preview.path)
        self._changed |= {DIMS_CHANGED, NOTES_CHANGED}
        self._symbols = {}
        self._signs = {}
        self._status = {}
        self._systems = {}
        self._no_geometry = set()
        self.loading = True
        info = self._preview_info = preview.info
        for guid, mesh in preview.meshes.items():
            self._put(BimObject(guid, info["names"][guid], info["classes"][guid], mesh, info["storeys"][guid]))
        for obj in preview.sketches:
            self._put(obj)
            self._counter += 1
        for g in preview.guides:
            self.guides[g.id] = g
        self._check_active_storey()
        self.modified = False
        self._notify()

    def add_preview_shapes(self, meshes):
        """More elements of a file being opened for the first time, as the geometry kernel
        makes them (read_file's partial): shown at once, still not editable."""
        if not self.loading:
            return
        info = self._preview_info
        for guid, mesh in meshes.items():
            self._put(BimObject(guid, info["names"][guid], info["classes"][guid], mesh, info["storeys"][guid]))
        self._notify()

    def finish_opening(self, opened):
        """The IFC of a previewed file is read. When it is what the preview showed (it is, unless
        the file changed meanwhile), the elements on screen stay and only get their IFC; else
        the document is made again from the file."""
        shown = {i: o for i, o in self.objects.items() if o.is_bim}
        same = self.loading and set(shown) == set(opened.shapes) and all(
            shown[e.GlobalId].mesh is opened.shapes[e.GlobalId]
            and shown[e.GlobalId].ifc_class == e.is_a()
            and shown[e.GlobalId].storey == opened.storeys.get(e.GlobalId)
            for e in opened.elements if e.GlobalId in opened.shapes)
        self.loading = False
        if not same:
            self.show_file(opened)
            return
        self.ifc = opened.model
        self._no_geometry = set(opened.no_geometry)
        self.cache_hits = opened.from_cache
        self._changed.add(STOREY_CHANGED)          # the panels look again (now at the IFC itself)
        self._check_active_storey()
        self.modified = False
        self._notify()

    def show_file(self, opened):
        """Second part of opening, quick (no geometry kernel): the file read by read_file()
        becomes the document. Runs where the document lives (the window's thread)."""
        self._replace_all(opened.model, opened.path, opened)
        self.cache_hits = opened.from_cache
        for obj in opened.sketches:
            self._put(obj)
            self._counter += 1
        for g in opened.guides:
            self.guides[g.id] = g
        self.modified = False
        self._notify()

    def save(self, path):
        with self._verifier_stamp():                    # (0.416: the rooms' uses and the dwellings, in the file)
            self.ifc.save(path)
        _write_sketches(sidecar_path(path, write=True), self.sketches(), self.guides.values(), self.ifc.origin, self.sections,
                        self.last_section, self.sheets, self.dimensions, self.templates, self.view_templates,
                        self.title_block, self.open_views, self.view_props, self.views3d, self.grids,
                        self.grid_settings, self.annotations, self.dim_style, self.graphic_style,
                        self.schedule_defs, self.details, self.clash_status, self.images, self.cad_links,
                        self.cloud_links, self.view_styles, self.presentation, self.panoramas,
                        work_plane=self.work_plane)
        notes_path = notes_file(path)
        if self.notes or os.path.exists(notes_path):      # (no notes left: the file is kept, empty)
            notes_model.save(self.notes, notes_path, os.path.splitext(os.path.basename(path))[0])
        self._save_geometry(path)
        self.path = path
        self.modified = False

    def _verifier_stamp(self):
        """(0.416) What the Verifier found — each room's use, the dwellings and their type — put in the IFC for the
        file being written (IfcSpace.ObjectType, IfcZone), and taken out again after. Never in the way of saving: if
        it cannot be found, the file is written without it."""
        try:
            from ..verify import reader, uses
            facts = reader.read(self)
            if not facts.rooms:
                return contextlib.nullcontext()
            language = lang()
            labels = {g: uses.label(r.use, language) for g, r in facts.rooms.items() if r.use != "outro"}
            return self.ifc.stamped({g: r.use for g, r in facts.rooms.items()}, facts.dwellings, labels,
                                    "Fogo" if language == "pt" else "Dwelling")
        except Exception:                                   # noqa: BLE001 (never stops a save)
            import logging
            logging.getLogger("arqbim").exception("verifier stamp")
            return contextlib.nullcontext()

    def _save_geometry(self, path):
        """The shapes on screen are those of the file just written / opened: keep them for next
        time, with what shows them before the IFC is read (class, name, storey; storeys, tree)."""
        bim = {i: o for i, o in self.objects.items() if o.is_bim}
        geomcache.save(path, {i: o.mesh for i, o in bim.items()}, self.ifc.geometry_key(), self._no_geometry,
                       preview_info(self.ifc, {i: (o.ifc_class, o.name, o.storey) for i, o in bim.items()}))

    # ------------------------------------------------------------ used by commands

    def _put(self, obj):
        self.objects[obj.id] = obj
        self._changed.add(obj.id)
        self._removed.discard(obj.id)
        self._symbols.pop(obj.id, None)
        self._signs.pop(obj.id, None)
        self._status.pop(obj.id, None)
        self._systems.pop(obj.id, None)

    def _drop(self, obj_id):
        self.objects.pop(obj_id, None)
        self._removed.add(obj_id)
        self._changed.discard(obj_id)
        self._symbols.pop(obj_id, None)
        self._signs.pop(obj_id, None)
        self._status.pop(obj_id, None)
        self._systems.pop(obj_id, None)

    def status_of(self, guid):
        """An element's phase — "EXISTING", "NEW", "DEMOLISH", "TEMPORARY" (the Status of its
        Pset_…Common) — or None; kept until it changes. None while the IFC is still being read."""
        if guid not in self._status:
            try:
                value = self.ifc.property_values([guid], ("status",)).get(guid)
            except RuntimeError:
                return None
            self._status[guid] = value
        return self._status[guid]

    def system_of(self, guid):
        """(0.141) The key of the system a pipe, a duct, a fitting… is in (ifc/systems.SYSTEMS), or None; kept until
        it changes. None while the IFC is still being read."""
        if guid not in self._systems:
            try:
                value = self.ifc.system_of(guid)
            except RuntimeError:
                return None
            self._systems[guid] = value
        return self._systems[guid]

    def plan_symbols(self, guids):
        """{GlobalId: (K, 2, 3) segments} of these elements' plan symbols (a door's linings, open
        leaf and swing arc; see IfcModel.plan_symbols), kept until the element changes. {} while
        the IFC is still being read."""
        missing = [g for g in guids if g not in self._symbols]
        if missing:
            try:
                found = self.ifc.plan_symbols(missing)
            except RuntimeError:
                return {}
            for g in missing:
                self._symbols[g] = found.get(g)
        return {g: self._symbols[g] for g in guids if self._symbols.get(g) is not None}

    def elevation_signs(self, guids):
        """(0.292) {GlobalId: (K, 2, 3) segments} of these doors' and windows' opening signs in elevations and sections
        (see IfcModel.elevation_signs), kept until the element changes. {} while the IFC is still being read."""
        missing = [g for g in guids if g not in self._signs]
        if missing:
            try:
                found = self.ifc.elevation_signs(missing)
            except RuntimeError:
                return {}
            for g in missing:
                self._signs[g] = found.get(g)
        return {g: self._signs[g] for g in guids if self._signs.get(g) is not None}

    def has_plan_symbol(self, guid):
        """Quick: is this element drawn by a plan symbol in plans? (While the IFC is read: as the
        geometry cache says.)"""
        return self.ifc.has_plan_symbol(guid)

    def _set_mesh(self, obj_id, mesh):
        self.objects[obj_id].mesh = mesh
        self._changed.add(obj_id)

    def _sync_ifc(self, changed=(), delta=None, shapes=None, elements=None, storeys=None):
        """Bring the displayed BIM objects in line with the IFC file.

        delta: (created, deleted) GlobalIds of what the last action did (from the
        IFC transaction): then only those and `changed` are looked at, whatever
        the size of the model. Without it (opening a file...): a full scan, where
        `shapes` ({GlobalId: TriMesh}, from read_file) are used instead of the kernel;
        `elements` (the displayable elements) and `storeys` when already known."""
        if delta is not None:
            created, deleted = delta
            for guid in deleted:
                obj = self.objects.get(guid)
                if obj is not None and obj.is_bim:
                    self._drop(guid)
            todo = (set(created) | set(changed)) - set(deleted)
            colours = {}                          # (0.259: a railing's parts in their colours)
            made = self.ifc.triangulate(todo, colours=colours)
            for guid in todo - set(made):
                obj = self.objects.get(guid)
                if obj is not None and obj.is_bim:
                    self._drop(guid)              # it has no geometry any more
            self._no_geometry = (self._no_geometry | (todo - set(made))) - set(made)
            for guid, (verts, tris) in made.items():
                e = self.ifc.by_guid(guid)
                self._put(BimObject(guid, e.Name or e.is_a(), e.is_a(), TriMesh(verts, tris, colors=colours.get(guid)),
                                    self.ifc.storey_of(guid)))
            self._check_active_storey()
            return
        displayable = elements if elements is not None else self.ifc.displayable_elements()
        elements = {e.GlobalId: e for e in displayable}
        shown = {i for i, o in self.objects.items() if o.is_bim}
        for guid in shown - set(elements):
            self._drop(guid)
        # new elements and changed ones; not again the ones known to have no geometry (unless changed)
        todo = ((set(elements) - shown) - self._no_geometry) | (set(changed) & set(elements))
        meshes = {guid: shapes[guid] for guid in todo if guid in shapes} if shapes else {}
        colours = {}
        made = self.ifc.triangulate(todo - set(meshes), elements=displayable, colours=colours) \
            if todo - set(meshes) else {}
        meshes.update({guid: TriMesh(verts, tris, colors=colours.get(guid)) for guid, (verts, tris) in made.items()})
        self._no_geometry = (self._no_geometry | (todo - set(meshes))) - set(meshes)
        for guid, mesh in meshes.items():
            e = elements[guid]
            storey = storeys[guid] if storeys is not None and guid in storeys else self.ifc.storey_of(guid)
            self._put(BimObject(guid, e.Name or e.is_a(), e.is_a(), mesh, storey))
        self._check_active_storey()

    def _check_active_storey(self):
        # the active storey may have been removed (undo of "new storey", another file...): lowest one
        levels = self.ifc.storeys()
        if self.active_storey not in {g for g, _n, _z in levels}:
            self.active_storey = levels[0][0] if levels else None
            self._changed.add(STOREY_CHANGED)

    def _notify(self):
        self.revision += 1                  # (0.225: what is worked out from the whole model is kept until then)
        changed, removed = self._changed, self._removed
        self._changed, self._removed = set(), set()
        if self.relay is not None and threading.current_thread() is not threading.main_thread():
            self.relay(lambda: self._tell(changed, removed))
            return
        self._tell(changed, removed)

    def _tell(self, changed, removed):
        for fn in self._listeners:
            fn(changed, removed)


# ---------------------------------------------------------------- opening a file

class OpenedFile:
    """A file read by read_file(), not shown yet (Document.show_file)."""

    def __init__(self, path, model, elements, shapes, storeys, no_geometry, from_cache, worked_out, sketches,
                 guides):
        self.path = path
        self.model = model                  # IfcModel
        self.elements = elements            # the displayable IFC elements
        self.shapes = shapes                # {GlobalId: TriMesh}
        self.storeys = storeys              # {GlobalId: storey GlobalId or None} of the elements with a shape
        self.no_geometry = no_geometry      # GlobalIds the kernel could not make a shape for
        self.from_cache = from_cache        # shapes read from the geometry cache
        self.worked_out = worked_out        # shapes worked out by the geometry kernel
        self.sketches = sketches
        self.guides = guides


STREAM_FROM = 500   # elements to work out from which a first opening shows them as they come


class Preview:
    """What can be shown of a file before its IFC is read (the geometry cache, Phase 2 step 7):
    the elements' shapes with their class, name and storey, the storeys, the spatial tree."""

    def __init__(self, path, cached, info, sketches, guides, meshes=None):
        self.path = path
        self.cached = cached                # as geomcache.load gives it (read_file takes it from here)
        self.info = info
        self.meshes = meshes if meshes is not None else {g: TriMesh(*v) for g, v in cached.items() if v is not None}
        self.sketches = sketches
        self.guides = guides


def read_preview(path):
    """A Preview of a file whose shapes were kept last time, or None. Quick (no IFC reading):
    run first, so the model is on screen while read_file reads the IFC."""
    from ..ifc.model import IfcModel
    cached, info = geomcache.load_all(path, IfcModel.kernel_key())
    if not cached or info is None:
        return None
    sketches, guides = _read_sketches(sidecar_path(path), info["origin"])
    return Preview(path, cached, info, sketches, guides)


def preview_info(model, elements):
    """What a geometry cache keeps to show the model before its IFC is read.
    elements: {GlobalId: (IFC class, name, storey GlobalId or None)}."""
    return {"classes": {g: c for g, (c, _n, _s) in elements.items()},
            "names": {g: n for g, (_c, n, _s) in elements.items()},
            "storeys": {g: s for g, (_c, _n, s) in elements.items()},
            "levels": [list(level) for level in model.storeys()], "spatial": model.spatial_tree(),
            "origin": [float(c) for c in model.origin],
            "symbols": sorted(g for g, (c, _n, _s) in elements.items()       # doors drawn by a plan symbol
                              if c == "IfcDoor" and model.has_plan_symbol(g))}


def read_file(path, progress=None, cancelled=None, preview=None, started=None, partial=None):
    """The slow part of opening a file: read the IFC, take the shapes kept from last
    time (geometry cache, principle 2) and work out the others with the kernel, then
    keep them for next time. It touches no document, so the window can run it in a
    worker thread and stay alive (Phase 2, step 4). preview: the file's Preview, if it
    was shown — its shapes are used again (the elements on screen keep them).

    A model opened for the first time with many elements comes in as it is worked out
    (step 8): started(Preview) once the IFC is read (classes, names, storeys known; no
    shapes yet), then partial({GlobalId: TriMesh}) now and then; the final result has
    those same meshes.

    progress(stage, percent): stage "read" (reading the IFC, percent None) or
    "shapes" (0–100). cancelled(): asked now and then; if it says yes, ifc.model.Cancelled
    is raised (reading the IFC itself cannot be stopped half-way)."""
    from ..ifc.model import Cancelled, IfcModel
    report = progress or (lambda stage, percent=None: None)
    report("read")
    model = IfcModel.open(path)
    model.strip_dwellings()                          # (0.416: found again from the rooms, not kept in memory)
    if cancelled is not None and cancelled():
        raise Cancelled()
    key = model.geometry_key()
    cached, info = (preview.cached, preview.info) if preview is not None else geomcache.load_all(path, key)
    if info is None or not np.allclose(info["origin"], model.origin):
        cached = {}                                  # made for another origin: not these coordinates
    reuse = preview.meshes if preview is not None else {}
    elements = model.displayable_elements()
    shapes, no_geometry, missing = {}, set(), []
    for e in elements:
        guid = e.GlobalId
        if guid not in cached:
            missing.append(e)
        elif cached[guid] is None:
            no_geometry.add(guid)                    # known: the kernel makes no shape for it
        else:
            shapes[guid] = reuse.get(guid) or TriMesh(*cached[guid])
    from_cache = len(shapes)
    made, streamed, storeys, colours = {}, {}, None, {}
    if missing:
        report("shapes", 0)
        on_chunk = None
        if started is not None and len(missing) >= STREAM_FROM:
            storeys = model.storeys_of(elements)
            info = preview_info(model, {e.GlobalId: (e.is_a(), e.Name or e.is_a(), storeys[e.GlobalId])
                                        for e in elements})
            sketches, guides = _read_sketches(sidecar_path(path), model.origin)
            started(Preview(path, {}, info, sketches, guides, meshes=dict(shapes)))

            def on_chunk(raw):
                meshes = {guid: TriMesh(verts, tris, colors=colours.get(guid)) for guid, (verts, tris) in raw.items()}
                streamed.update(meshes)
                if partial is not None:
                    partial(meshes)

        made = model.triangulate(elements=missing, progress=lambda p: report("shapes", p), cancelled=cancelled,
                                 chunk=on_chunk, colours=colours)
        for guid, (verts, tris) in made.items():
            mesh = streamed.get(guid)
            shapes[guid] = mesh if mesh is not None else TriMesh(verts, tris, colors=colours.get(guid))
        no_geometry |= {e.GlobalId for e in missing} - set(made)
    with_shape = [e for e in elements if e.GlobalId in shapes]
    storeys = {e.GlobalId: storeys[e.GlobalId] for e in with_shape} if storeys else model.storeys_of(with_shape)
    if missing:                                      # the next opening of this file will be quick
        geomcache.save(path, shapes, key, no_geometry, preview_info(model, {
            e.GlobalId: (e.is_a(), e.Name or e.is_a(), storeys[e.GlobalId]) for e in with_shape}))
    sketches, guides = _read_sketches(sidecar_path(path), model.origin)
    return OpenedFile(path, model, elements, shapes, storeys, no_geometry, from_cache, len(made), sketches, guides)


class PreviewModel:
    """Stands in for the IFC model while a previewed file's IFC is still being read
    (Document.loading): answers what the panels and the view ask — storeys, spatial tree —
    from the geometry cache. Anything else (editing) waits for the IFC."""

    def __init__(self, info):
        self.origin = np.array(info["origin"], dtype=float)
        self._levels = [tuple(level) for level in info["levels"]]
        self._spatial = _as_tuples(info["spatial"])
        self._storeys = info["storeys"]
        self._symbols = set(info.get("symbols", ()))

    def storeys(self):
        return list(self._levels)

    def has_plan_symbol(self, guid):
        return guid in self._symbols

    def spatial_tree(self):
        return self._spatial

    def storey_of(self, guid):
        return self._storeys.get(guid)

    def geometry_key(self):
        from ..ifc.model import IfcModel
        return IfcModel.kernel_key()

    @contextlib.contextmanager
    def remembering(self):
        """(0.225) As IfcModel.remembering — nothing to keep: what it is asked here comes ready from the cache."""
        yield

    def __getattr__(self, name):
        raise RuntimeError("the IFC is still being read (IfcModel.{} not available yet)".format(name))


def _as_tuples(node):
    """A spatial tree read back from JSON (lists) as IfcModel.spatial_tree gives it (tuples)."""
    if node is None:
        return None
    guid, ifc_class, name, level, children = node
    return (guid, ifc_class, name, level, [_as_tuples(c) for c in children])


# ---------------------------------------------------------------- sketch side file

SIDECAR_EXT, LEGACY_SIDECAR_EXT = ".arqsynthbim", ".arqbim"     # (0.77; ".arqbim" until 0.76)


def sidecar_path(ifc_path, write=False):
    """The file beside the IFC with its sketches, views, sheets…: "projeto.arqsynthbim". Read, an old
    "projeto.arqbim" is taken when there is no new one; written, always the new."""
    stem = os.path.splitext(ifc_path)[0]
    new = stem + SIDECAR_EXT
    if write or os.path.exists(new):
        return new
    old = stem + LEGACY_SIDECAR_EXT
    return old if os.path.exists(old) else new


_ONCE = threading.local()       # (0.255) the side file parsed while a project's parts are read from it


@contextlib.contextmanager
def _reading_sidecar():
    """While a project is put on screen, its side file — read by a score of readers, one part each (sheets,
    dimensions, views…) — is opened and parsed once (a file with many sketches took as many parses)."""
    _ONCE.data = {}
    try:
        yield
    finally:
        _ONCE.data = None


def _sidecar_data(path):
    """The side file's data (json): parsed once inside _reading_sidecar, else each time. Raises OSError /
    ValueError as reading it does."""
    cache = getattr(_ONCE, "data", None)
    if cache is None:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    if path not in cache:
        try:
            with open(path, encoding="utf-8") as f:
                cache[path] = json.load(f)
        except (OSError, ValueError) as exc:
            cache[path] = exc
    found = cache[path]
    if isinstance(found, Exception):
        raise found
    return found


def _write_sketches(path, sketches, guides=(), origin=(0.0, 0.0, 0.0), sections=(), last_section=None,
                    sheets=(), dimensions=(), templates=(), view_templates=None, title_block=None, open_views=None,
                    view_props=None, views3d=(), grids=(), grid_settings=None, annotations=(), dim_style=None,
                    graphic_style=None, schedule_defs=(), details=(), clash_status=None, images=(), cad_links=(),
                    cloud_links=(), view_styles=(), presentation=None, panoramas=(), work_plane=None):
    """Sketches, guides, the named sections and the dimensions in the program's coordinates, with
    the model origin they are relative to; the sheets (in mm on paper) and their title block; the
    views' templates and own properties."""
    data = {"format": "arqbim-sketches", "version": 1, "origin": [float(c) for c in origin], "sketches": [
        {"name": o.name, "matrix": o.matrix.tolist(),
         "verts": [list(map(float, v)) for v in o.mesh.verts],
         "faces": o.mesh.faces, "hidden": sorted(list(e) for e in o.mesh.hidden),
         "voids": [[[list(map(float, p)) for p in pts], list(map(float, vec))] for pts, vec in o.mesh.voids],
         "lines": [list(e) for e in o.mesh.lines],
         **({"paint": o.mesh.painted()} if any(o.mesh.painted()) else {}),        # (0.392: its faces' paint)
         "component": o.component, **({"curve": o.curve} if getattr(o, "curve", None) else {}),
         **({"uid": o.uid} if getattr(o, "uid", None) else {})}                    # (0.395: a surface follows it)
        for o in sketches],
        "guides": [{"point": list(map(float, g.point)), "direction": list(map(float, g.direction))}
                   for g in guides]}
    if sections:
        data["sections"] = [dict({"name": s.name, "point": [float(c) for c in s.point],
                                  "normal": [float(c) for c in s.normal], "uid": s.uid},
                                 **({"ends": [list(map(float, p)) for p in s.ends]} if s.ends else {}))
                            for s in sections]
        data["last_section"] = last_section
    if sheets:
        data["sheets"] = [sheets_model.to_dict(s) for s in sheets]
    if dimensions:
        data["dimensions"] = [dims_model.to_dict(d) for d in dimensions]
    if annotations:
        data["annotations"] = [notes2d.to_dict(a) for a in annotations]
    if dim_style and dims_model.clean_style(dim_style) != dims_model.STYLE_DEFAULTS:
        data["dim_style"] = dims_model.clean_style(dim_style)
    if graphic_style and styles_model.clean(graphic_style) != styles_model.DEFAULTS:
        data["graphic_style"] = styles_model.clean(graphic_style)
    if view_styles:                                     # (0.315) the project's view styles
        data["view_styles"] = [view_styles_model.to_dict(s) for s in view_styles]
    if presentation and presentation_model.clean(presentation) != presentation_model.empty():
        data["presentation"] = presentation_model.clean(presentation)      # (0.363) the scenes for the Presentation
    if panoramas:                                       # (0.368) the 360° panoramas (their pictures beside it)
        from . import panoramas as panoramas_model
        data["panoramas"] = panoramas_model.clean(panoramas)
    if schedule_defs:
        from . import schedules as schedules_model
        data["schedules"] = [schedules_model.def_to_dict(d) for d in schedule_defs]
    if details:
        data["details"] = [{"name": d.name, "parent": list(d.parent), "rect": [float(c) for c in d.rect],
                            "scale": int(d.scale), "uid": d.uid} for d in details]
    if clash_status:                                    # (0.150) the clashes' statuses, by their pair of elements
        data["clashes"] = {str(k): str(v) for k, v in clash_status.items()}
    if images:                                          # (0.154) the background images (their pictures where they are)
        from . import images as images_model
        data["images"] = [images_model.to_dict(i, os.path.dirname(os.path.abspath(path))) for i in images]
    if cad_links:                                       # (0.158) the DXF drawings linked (their files where they are)
        from . import cad_links as cad_model
        data["cad"] = [cad_model.to_dict(c, os.path.dirname(os.path.abspath(path))) for c in cad_links]
    if cloud_links:                                     # (0.161) the point clouds linked (their files where they are)
        from . import cloud_links as cloud_model
        data["clouds"] = [cloud_model.to_dict(c, os.path.dirname(os.path.abspath(path))) for c in cloud_links]
    if templates:
        data["templates"] = [templates_model.to_dict(tpl) for tpl in templates]
        data["view_templates"] = [[list(view), uid] for view, uid in (view_templates or {}).items()]
    if view_props:
        data["view_props"] = [[list(view), templates_model.own_to_dict(own)] for view, own in view_props.items()]
    if views3d:
        data["views3d"] = [{"name": v.name, "uid": v.uid, "camera": camera_json(v.camera)} for v in views3d]
    if grids:
        data["grids"] = [{"tag": g.tag, "start": [float(c) for c in g.start], "end": [float(c) for c in g.end],
                          "uid": g.uid} for g in grids]
    if grid_settings and dict(grid_settings) != GRID_DEFAULTS:
        data["grid_settings"] = dict(grid_settings)
    if work_plane is not None:                          # (0.413) the work plane set
        from . import work_plane as work_plane_model
        data["work_plane"] = work_plane_model.to_dict(work_plane)
    if title_block:
        data["title_block"] = dict(title_block)
    if open_views:
        data["open_views"] = open_views
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def notes_file(ifc_path):
    """Where a project's coordination notes are kept: <name>.bcfzip beside the IFC."""
    return os.path.splitext(ifc_path)[0] + ".bcfzip"


def _read_notes(ifc_path):
    path = notes_file(ifc_path)
    if not os.path.exists(path):
        return []
    try:
        return notes_model.load(path)
    except (ValueError, OSError):
        return []


def _read_templates(path):
    """([ViewTemplate], {view key: template uid}) saved beside an IFC file."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return [], {}
    templates = [tpl for tpl in (templates_model.from_dict(d) for d in data.get("templates", ()) if isinstance(d, dict))
                 if tpl is not None]
    uids = {tpl.uid for tpl in templates}
    assigned = {}
    for item in data.get("view_templates", ()):
        try:
            view, uid = tuple(item[0]), str(item[1])
        except (TypeError, IndexError):
            continue
        if uid in uids:
            assigned[view] = uid
    return templates, assigned


def _read_view_props(path, origin=(0.0, 0.0, 0.0)):
    """{view key: its own properties} saved beside an IFC file (a section box in the program's coordinates)."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return {}
    shift = np.array(data.get("origin", (0.0, 0.0, 0.0)), dtype=float) - np.asarray(origin, dtype=float)
    props = {}
    for item in data.get("view_props", ()):
        try:
            view, own = tuple(item[0]), templates_model.own_from_dict(item[1])
        except (TypeError, IndexError):
            continue
        if own.get("box"):
            own["box"] = [[float(c) for c in np.asarray(corner, dtype=float) + shift] for corner in own["box"]]
        if own.get("crop"):
            x0, y0, x1, y1 = own["crop"]
            own["crop"] = [x0 + shift[0], y0 + shift[1], x1 + shift[0], y1 + shift[1]]
        if own.get("home"):
            own["home"] = {k: [float(c) for c in np.asarray(own["home"][k], dtype=float) + shift]
                           for k in ("eye", "target")}
        if own:
            props[view] = own
    return props


def camera_json(camera):
    """A camera (Viewport.camera_snapshot) as JSON."""
    return None if camera is None else {
        "position": [float(c) for c in camera["position"]], "rotation": [float(c) for c in camera["rotation"]],
        "focus": [float(c) for c in camera["focus"]],
        **{name: float(camera[name]) for name in ("fov", "width", "height", "zoom")}}


def camera_from_json(data, shift=(0.0, 0.0, 0.0)):
    """A camera read back (moved by `shift`: the model origin then and now), or None."""
    try:
        camera = dict(data)
        camera["position"] = tuple(float(c) for c in np.asarray(camera["position"], dtype=float) + shift)
        camera["focus"] = tuple(float(c) for c in np.asarray(camera["focus"], dtype=float) + shift)
        camera["rotation"] = tuple(float(c) for c in camera["rotation"])
        for name in ("fov", "width", "height", "zoom"):
            camera[name] = float(camera[name])
        return camera
    except (KeyError, TypeError, ValueError):
        return None


def _read_work_plane(path, origin=(0.0, 0.0, 0.0)):
    """(0.413) The work plane saved beside an IFC file, in the program's coordinates — None (none, or not
    understood)."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("work_plane"), dict):
        return None
    from . import work_plane as work_plane_model
    shift = np.array(data.get("origin", (0.0, 0.0, 0.0)), dtype=float) - np.asarray(origin, dtype=float)
    return work_plane_model.from_dict(data["work_plane"], shift)


def _read_grid_settings(path):
    """The grid's settings saved beside an IFC file (0.91); what is not there (or not understood): the defaults."""
    out = dict(GRID_DEFAULTS)
    try:
        data = _sidecar_data(path).get("grid_settings") or {}
    except (OSError, ValueError, AttributeError):
        return out
    if data.get("scheme") in ("numbers_y", "letters_y"):
        out["scheme"] = data["scheme"]
    if isinstance(data.get("dims"), bool):
        out["dims"] = data["dims"]
    try:
        bubble = float(data.get("bubble", out["bubble"]))
        if 0.05 <= bubble <= 2.0:
            out["bubble"] = bubble
    except (TypeError, ValueError):
        pass
    return out


def _read_grids(path, origin=(0.0, 0.0, 0.0)):
    """[GridAxis] saved beside an IFC file, in the program's coordinates."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return []
    shift = np.array(data.get("origin", (0.0, 0.0, 0.0)), dtype=float) - np.asarray(origin, dtype=float)
    axes = []
    for item in data.get("grids", ()):
        try:
            a = tuple(float(c) + float(s) for c, s in zip(item["start"][:2], shift[:2]))
            b = tuple(float(c) + float(s) for c, s in zip(item["end"][:2], shift[:2]))
            axis = GridAxis(str(item["tag"]), a, b)
            if item.get("uid"):
                axis.uid = str(item["uid"])
            axes.append(axis)
        except (KeyError, TypeError, ValueError):
            continue
    return axes


def _read_views3d(path, origin=(0.0, 0.0, 0.0)):
    """[View3D] saved beside an IFC file, their cameras in the program's coordinates."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return []
    shift = np.array(data.get("origin", (0.0, 0.0, 0.0)), dtype=float) - np.asarray(origin, dtype=float)
    views = []
    for item in data.get("views3d", ()):
        if isinstance(item, dict) and item.get("uid") and item.get("name"):
            views.append(View3D(str(item["name"]), str(item["uid"]),
                                camera_from_json(item["camera"], shift) if item.get("camera") else None))
    return views


def _read_dimensions(path, origin=(0.0, 0.0, 0.0)):
    """[Dimension] saved beside an IFC file, in the program's coordinates."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return []
    shift = np.array(data.get("origin", (0.0, 0.0, 0.0)), dtype=float) - np.asarray(origin, dtype=float)
    return [d for d in (dims_model.from_dict(x, shift) for x in data.get("dimensions", ()) if isinstance(x, dict))
            if d is not None]


def _read_details(path, origin=(0.0, 0.0, 0.0)):
    """The detail views (0.133) saved beside an IFC file — their rectangles in their views' 2D frames: a plan's
    is the program's plan coordinates (moved with the model's origin, as the dimensions are), a section's its own
    (from its point: it moves with it)."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return []
    shift = np.array(data.get("origin", (0.0, 0.0, 0.0)), dtype=float) - np.asarray(origin, dtype=float)
    out = []
    for item in data.get("details", ()):
        try:
            rect = tuple(float(c) for c in item["rect"])
            if len(rect) != 4:
                continue
            if tuple(item["parent"])[0] == "plan":
                rect = (rect[0] + shift[0], rect[1] + shift[1], rect[2] + shift[0], rect[3] + shift[1])
            detail = DetailView(str(item["name"]), tuple(item["parent"]), rect, int(item.get("scale") or 20))
            if item.get("uid"):
                detail.uid = str(item["uid"])
            out.append(detail)
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _read_clash_status(path):
    """(0.150) The clashes' statuses saved beside an IFC file: {"a|b": status}."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return {}
    found = data.get("clashes")
    if not isinstance(found, dict):
        return {}
    return {str(k): str(v) for k, v in found.items() if v in ("new", "active", "resolved", "approved")}


def _read_images(path, origin=(0.0, 0.0, 0.0)):
    """(0.154) The background images saved beside an IFC file, in the program's coordinates."""
    from . import images as images_model
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return []
    shift = np.array(data.get("origin", (0.0, 0.0, 0.0)), dtype=float) - np.asarray(origin, dtype=float)
    base = os.path.dirname(os.path.abspath(path))
    found = [images_model.from_dict(item, shift, base) for item in data.get("images", ()) if isinstance(item, dict)]
    return [i for i in found if i is not None]


def _read_cad_links(path, origin=(0.0, 0.0, 0.0)):
    """(0.158) The CAD drawings linked, saved beside an IFC file, in the program's coordinates."""
    from . import cad_links as cad_model
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return []
    shift = np.array(data.get("origin", (0.0, 0.0, 0.0)), dtype=float) - np.asarray(origin, dtype=float)
    base = os.path.dirname(os.path.abspath(path))
    found = [cad_model.from_dict(item, shift, base) for item in data.get("cad", ()) if isinstance(item, dict)]
    return [c for c in found if c is not None]


def _read_cloud_links(path, origin=(0.0, 0.0, 0.0)):
    """(0.161) The point clouds linked, saved beside an IFC file, in the program's coordinates."""
    from . import cloud_links as cloud_model
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return []
    shift = np.array(data.get("origin", (0.0, 0.0, 0.0)), dtype=float) - np.asarray(origin, dtype=float)
    base = os.path.dirname(os.path.abspath(path))
    found = [cloud_model.from_dict(item, shift, base) for item in data.get("clouds", ()) if isinstance(item, dict)]
    return [c for c in found if c is not None]


def _read_schedule_defs(path):
    """The project's own schedules (0.131) saved beside an IFC file."""
    from . import schedules as schedules_model
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return []
    return [d for d in (schedules_model.def_from_dict(x) for x in data.get("schedules", ()) if isinstance(x, dict))
            if d is not None]


def _read_view_styles(path):
    """(0.315) The project's view styles saved beside an IFC file."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return []
    return [s for s in (view_styles_model.from_dict(d) for d in data.get("view_styles", ())) if s is not None]


def _read_panoramas(path):
    """(0.368) The 360° panoramas saved beside an IFC file (their records; the pictures are in their folder)."""
    from . import panoramas as panoramas_model
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return []
    return panoramas_model.clean(data.get("panoramas"))


def _read_presentation(path):
    """(0.363) The scenes for the ArqSynth Presentation as chosen, saved beside an IFC file (none: the usual)."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return presentation_model.empty()
    return presentation_model.clean(data.get("presentation"))


def _read_graphic_style(path):
    """The hatches and pens on paper (0.126) saved beside an IFC file, else the usual ones."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return styles_model.defaults()
    return styles_model.clean(data.get("graphic_style"))


def _read_dim_style(path):
    """The dimensions' style (0.124) saved beside an IFC file, else the usual one."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return dict(dims_model.STYLE_DEFAULTS)
    return dims_model.clean_style(data.get("dim_style") if isinstance(data.get("dim_style"), dict) else None)


def _read_annotations(path, origin=(0.0, 0.0, 0.0)):
    """[Annotation] (the drawings in the views, 0.120) saved beside an IFC file, in the program's coordinates."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return []
    shift = np.array(data.get("origin", (0.0, 0.0, 0.0)), dtype=float) - np.asarray(origin, dtype=float)
    return [a for a in (notes2d.from_dict(x, shift) for x in data.get("annotations", ()) if isinstance(x, dict))
            if a is not None]


def _read_sheets(path):
    """[Sheet] saved beside an IFC file."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return []
    return [s for s in (sheets_model.from_dict(d) for d in data.get("sheets", ()) if isinstance(d, dict))
            if s is not None]


def _read_open_views(path, origin=(0.0, 0.0, 0.0)):
    """The view tabs saved beside an IFC file, their cameras in the program's coordinates (or None)."""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return None
    views = data.get("open_views")
    if not isinstance(views, dict) or not isinstance(views.get("tabs"), list):
        return None
    shift = np.array(data.get("origin", (0.0, 0.0, 0.0)), dtype=float) - np.asarray(origin, dtype=float)
    tabs = []
    for tab in views["tabs"]:
        try:
            key = tuple(tab["key"])
            camera = dict(tab["camera"]) if tab.get("camera") else None
            if camera is not None:
                camera["position"] = tuple(float(c) for c in np.asarray(camera["position"], dtype=float) + shift)
                camera["focus"] = tuple(float(c) for c in np.asarray(camera["focus"], dtype=float) + shift)
                camera["rotation"] = tuple(float(c) for c in camera["rotation"])
                for name in ("fov", "width", "height", "zoom"):
                    camera[name] = float(camera[name])
        except (KeyError, TypeError, ValueError):
            continue
        tabs.append({"key": key, "camera": camera})
    current = views.get("current")
    return {"tabs": tabs, "current": tuple(current) if isinstance(current, list) else None}


def _read_title_block(path):
    """The sheets' title block fields saved beside an IFC file."""
    try:
        return sheets_model.read_title_fields(_sidecar_data(path).get("title_block"))
    except (OSError, ValueError, AttributeError):
        return {}


def sheet_name(n):
    return ("Folha {}" if lang() == "pt" else "Sheet {}").format(n)


def _read_sections(path, origin=(0.0, 0.0, 0.0)):
    """([SectionView], index of the last one shown or None) saved beside an IFC file, in the
    program's coordinates. (0.28 kept only one, as "section": it becomes "Corte 1".)"""
    try:
        data = _sidecar_data(path)
    except (OSError, ValueError):
        return [], None
    shift = np.array(data.get("origin", (0.0, 0.0, 0.0)), dtype=float) - np.asarray(origin, dtype=float)
    saved = data.get("sections")
    if saved is None and isinstance(data.get("section"), dict):
        saved, data["last_section"] = [dict(data["section"], name=section_name(1))], 0
    out = []
    for s in saved or ():
        try:
            ends = s.get("ends")
            if ends is not None:                       # (0.358) its line's own ends
                ends = tuple((float(p[0]) + shift[0], float(p[1]) + shift[1]) for p in ends[:2])
            out.append(SectionView(str(s["name"]), np.asarray(s["point"], dtype=float) + shift,
                                   np.asarray(s["normal"], dtype=float), ends,
                                   str(s.get("uid") or _old_section_uid(s["name"]))))
        except (KeyError, TypeError, ValueError, IndexError):
            continue
    last = data.get("last_section")
    return out, (last if isinstance(last, int) and 0 <= last < len(out) else None)


def section_name(n):
    return ("Corte {}" if lang() == "pt" else "Section {}").format(n)


def _old_section_uid(name):
    """(0.363) A section saved before it had a uid: one made from its name, the same every time the file is opened
    until it is saved with it."""
    import hashlib
    return "s" + hashlib.sha1(str(name).encode("utf-8")).hexdigest()[:31]


def _read_sketches(path, origin=(0.0, 0.0, 0.0)):
    """(sketch objects, guides) saved beside an IFC file, in the program's coordinates for a
    model whose origin is `origin` (they are moved if the file was saved with another one)."""
    if not os.path.exists(path):
        return [], []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    shift = np.array(data.get("origin", (0.0, 0.0, 0.0)), dtype=float) - np.asarray(origin, dtype=float)
    sketches = []
    for s in data.get("sketches", []):
        matrix = np.array(s["matrix"], dtype=float)
        matrix[:3, 3] += shift
        sketches.append(SketchObject(s["name"], matrix,
                                     PolyMesh(s["verts"], s["faces"], [tuple(e) for e in s.get("hidden", [])],
                                              [(pts, vec) for pts, vec in s.get("voids", [])],
                                              [tuple(e) for e in s.get("lines", [])], s.get("paint") or ()),
                                     component=s.get("component"), curve=s.get("curve"), uid=s.get("uid")))
    guides = [Guide(np.asarray(g["point"], dtype=float) + shift, g["direction"]) for g in data.get("guides", [])]
    return sketches, guides
