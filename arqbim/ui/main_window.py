"""Main window: 3D view, toolbar, menus, status bar with the Measurements box,
properties panel, IFC open/save and BIM classification."""

import dataclasses
import logging
import math
import os
import queue
import threading
import time
import weakref

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from rendercanvas.qt import QRenderWidget

from .. import __version__
from ..core import curves as core_curves
from ..core import units as units_core
from ..core.units import format_angle, format_length, parse_length, parse_lengths
from ..i18n import decimal_sep, lang, refusal, t
from ..i18n import has as i18n_has
from ..ifc import catalog, certify
from ..ifc import ids as ids_check
from ..ifc.model import Cancelled, IfcModel
from ..model import bim, controls, curve_edit, line_edit, parts, project_types
from ..model import drawings
from ..model import schedules as schedules_model
from ..model import dimensions as dims_model
from ..model import annotations as notes2d
from ..model import graphic_rules as rules_model
from ..model import graphic_styles as styles_model
from ..model import notes as notes_model
from ..model import sharing
from ..model import sheets as sheets_model
from ..model import view_templates as templates_model
from ..model import view_styles as view_styles_model
from ..model.document import (CAD_CHANGED, CLOUD_CHANGED, DIMS_CHANGED, GRID_CHANGED, GUIDES_CHANGED,
                              IMAGES_CHANGED, NOTES_CHANGED, STOREY_CHANGED, VIEWS_CHANGED, CadLinksChange,
                              CloudLinksChange, Document, ImagesChange, RemoveGuides, read_file, read_preview)
from ..render import viewcube
from ..render.viewport import CUT_HEIGHT, Viewport, prepare_pieces
from ..tools import ALL_TOOLS
from ..tools.place import PlaceTool
from ..tools.image import CropImageTool, FacadeImageTool
from ..tools.platform import PlatformOutlineTool
from ..tools.slab import SlabOutlineTool
from ..tools.roof_blocks import RoofBlocksTool
from ..tools.presentation_label import LabelPlaceTool
from ..tools.wall_profile import WallProfileTool
from ..tools.base import MIDDLE
from ..tools.base import Option
from . import (context_bar, graphic_rules, icons, ids_panel, menus, notes_panel, notice, pdf, picture, project_tree,
               properties, quick_edit, ribbon, schedules, selection_dialogs, sheet_view, storeys, theme,
               title_block_dialog, view_tabs, view_templates)
from . import room_program as room_program_panel
from . import tool_cursors                                  # (0.526) the cursor by tool
from . import verify_bar                                    # (0.417) the Verifier
from . import verify_panel                                  # (0.418) its panel

Key = QtCore.Qt.Key
Mod = QtCore.Qt.KeyboardModifier


def _by_kind(specs):
    """Types in the order of their kinds (walls, slabs, columns…), each kind's in their own order."""
    return sorted(specs, key=lambda s: catalog.KINDS.index(s.kind))
TYPED_CHARS = set("0123456789.,;-+*/x")   # x, * and /: series of copies ("3x", "x3", "/3")
QUIET_TOOLS = {"select", "orbit", "pan", "zoom", "zoom_window"}     # (0.321) no balloon with their step
VIEW_TOOLS = {"dimension", "draft", "detail", "dim_exterior", "dim_interior"}   # (0.323) drawn in a plan, a section…


@dataclasses.dataclass
class _Pick:
    """(0.322) A command waiting for the elements it needs, as Revit's «pick»: instead of refusing with nothing (or
    not enough) selected, it asks for them in the balloon and the Select tool picks them — a click takes one in or
    out, a box adds; Enter (or the right button) goes on, unless `most` are enough to go on by themselves; Esc gives
    it up. `then` runs the command again, with `keep` and the elements picked selected."""
    title: str              # the command's name, on top of the balloon
    what: str               # what to click («Clique nas paredes…»)
    accept: object          # id -> bool: what it takes
    then: object            # () -> None
    least: int = 1
    most: int = 0           # 0: as many as wanted
    keep: frozenset = frozenset()
    icon: object = None
OPEN_DIALOG_AFTER_MS = 400   # a file that opens faster shows no progress window
WINDOW_WAIT_S = 1.0          # the most the reading thread waits for the window (if it never says "free")
UNIT_CHARS = set("xmc")  # accepted once a number has been started ("320cm", "3x4")
THUMB_RENDER_PX = 384        # (0.363) a scene drawn this wide for its thumbnail…
THUMB_PX = (320, 180)        # …cut to 16:9 and made this size (the Presentation makes its own about 384 wide)


def _thumbnail_jpeg(image, size=THUMB_PX, quality=82):
    """(0.363) A scene's thumbnail: the image of its view ((h, w, 4) RGBA) cut to the thumbnail's proportion round its
    middle, made that size, on white (a JPEG has no transparency) — its JPEG bytes."""
    h, w = image.shape[:2]
    rgba = np.ascontiguousarray(image[:, :, :4], dtype=np.uint8)
    picture = QtGui.QImage(rgba.data, w, h, 4 * w, QtGui.QImage.Format.Format_RGBA8888).copy()
    tw, th = size
    if w * th > h * tw:                                     # wider than 16:9: its sides cut
        cw = max(1, int(round(h * tw / th)))
        picture = picture.copy((w - cw) // 2, 0, cw, h)
    else:
        ch = max(1, int(round(w * th / tw)))
        picture = picture.copy(0, (h - ch) // 2, w, ch)
    picture = picture.scaled(tw, th, QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
                             QtCore.Qt.TransformationMode.SmoothTransformation)
    out = QtGui.QImage(tw, th, QtGui.QImage.Format.Format_RGB888)
    out.fill(QtGui.QColor("#ffffff"))
    painter = QtGui.QPainter(out)
    painter.drawImage(0, 0, picture)
    painter.end()
    data = QtCore.QByteArray()
    buffer = QtCore.QBuffer(data)
    buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
    out.save(buffer, "JPG", quality)
    buffer.close()
    return bytes(data)


def _documents_dir():
    """Where open / save dialogs start: the user's Documents (in Linux on Windows, WSL: the Windows
    one, given by scripts/arqbim_wsl.sh)."""
    return os.environ.get("ARQBIM_DOCUMENTS") or \
        QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.DocumentsLocation)


def _author():
    """Who writes a note: the user's name on this computer."""
    import getpass
    try:
        return getpass.getuser()
    except Exception:
        return "ArqSynth BIM"


def _png(image, max_width=1024):
    """RGBA pixels (height, width, 4) -> PNG bytes, at most max_width wide (a note's picture)."""
    image = np.ascontiguousarray(image)
    h, w = image.shape[:2]
    qimage = QtGui.QImage(image.data, w, h, image.strides[0], QtGui.QImage.Format.Format_RGBA8888).copy()
    if w > max_width:
        qimage = qimage.scaledToWidth(max_width, QtCore.Qt.TransformationMode.SmoothTransformation)
    data = QtCore.QByteArray()
    buffer = QtCore.QBuffer(data)
    buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
    qimage.save(buffer, "PNG")
    buffer.close()
    return bytes(data)


def _seconds(s):
    text = "{:.1f}".format(s) if s >= 1 else "{:.2f}".format(s)
    return text.replace(".", ",") if lang() == "pt" else text


class _FileReader(QtCore.QThread):
    """Reads a file (document.read_file: IFC, geometry cache, kernel) in a worker thread,
    so the window keeps drawing and answering while a big file opens."""

    progress = QtCore.Signal(str, int)          # stage ("read" / "shapes"), percent (-1: unknown)
    preview_ready = QtCore.Signal()             # self.preview / preview_pieces can be shown (IFC still to read)
    shapes_ready = QtCore.Signal()              # more shapes in self.chunks (a first opening, as they come)

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self.preview = None
        self.preview_pieces = {}
        self.chunks = queue.SimpleQueue()       # (meshes, pieces) for the window's thread
        self.result = None
        self.pieces = {}
        self.error = None
        self._sent = {}                         # GlobalId -> mesh already handed over with its piece
        # Both threads share Python's lock (GIL): while the window puts shapes in place (many small
        # NumPy steps, each letting go of the lock and waiting for it again — on Windows ~1 ms each
        # while this thread runs Python) this thread waits at its next check, so the window is quick.
        self.window_free = threading.Event()
        self.window_free.set()

    def _check(self):
        """Asked between elements: wait while the window is busy with shapes; stop if cancelled."""
        self.window_free.wait(timeout=WINDOW_WAIT_S)
        return self.isInterruptionRequested()

    def run(self):
        try:
            # a file opened before: its kept shapes first, so the window shows it at once
            preview = read_preview(self.path)
            if preview is not None and not self.isInterruptionRequested():
                self._started(preview)
            # else a big file opened for the first time comes in as its shapes are worked out
            result = read_file(self.path, self._report, self._check, self.preview,
                               started=self._started if self.preview is None else None, partial=self._partial)
            self._report("prepare")
            # the display pieces too (numpy only): the window's thread just puts them in place
            fresh = {g: m for g, m in result.shapes.items() if self._sent.get(g) is not m}
            self.pieces = prepare_pieces(fresh, {e.GlobalId: e.is_a() for e in result.elements})
            self.result = result
        except Exception as exc:  # noqa: BLE001 — unreadable file or Cancelled: the window tells the user
            self.error = exc

    def _started(self, preview):
        self.preview_pieces = prepare_pieces(preview.meshes, preview.info["classes"])
        self._sent.update(preview.meshes)
        self.preview = preview
        self.preview_ready.emit()

    def _partial(self, meshes):
        self.chunks.put((meshes, prepare_pieces(meshes, self.preview.info["classes"], pause=self._check)))
        self._sent.update(meshes)
        self.shapes_ready.emit()

    def _report(self, stage, percent=None):
        self.progress.emit(stage, -1 if percent is None else int(percent))


class _Job(QtCore.QThread):
    """A slow piece of work (e.g. a drawing with its hidden lines worked out) in a worker thread."""

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn, self.result, self.error = fn, None, None

    def run(self):
        try:
            self.result = self.fn()
        except Exception as exc:  # noqa: BLE001 — shown by the window
            self.error = exc


class _Relay(QtCore.QObject):
    """(0.254) Calls run in the window's thread, whichever thread asks for them: the document's changes made in a
    worker thread are told to the window and the 3D view there — after the work (run_busy holds them until it is
    done: nothing reads the model while the worker still writes it), else as soon as the window is free (a queued
    signal)."""
    asked = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pending, self._lock, self.held = [], threading.Lock(), 0
        self.asked.connect(self.flush, QtCore.Qt.ConnectionType.QueuedConnection)

    def __call__(self, call):
        with self._lock:
            self._pending.append(call)
        if not self.held:
            self.asked.emit()

    @QtCore.Slot()
    def flush(self):
        with self._lock:
            calls, self._pending = self._pending, []
        for call in calls:
            call()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.doc = Document()
        self._relay = _Relay(self)
        self.doc.relay = self._relay
        self._readers = set()       # files being read in a worker thread (see open_path)
        self._view_name = ""        # the section or elevation shown ("Corte 2", "Alçado Norte")
        self._tree_lib_key = None   # (groups, types) when the Project panel last listed the library
        self._loading = False       # a file on screen from its kept shapes, IFC still being read
        central = QtWidgets.QWidget(self)         # the views' tabs over the 3D canvas, or a sheet
        self.view_bar = QtWidgets.QTabBar(central)
        self.canvas = QRenderWidget(central, update_mode="ondemand", max_fps=120)
        self.sheet_window = None                  # a sheet, shown in place of the canvas (made with the first)
        self.start_page = None                    # (0.387) the start page, in place of the canvas (made when first shown)
        self._docks_hidden = None                 # (0.387) the side panels it put aside, to show again
        self._central_layout = layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.view_bar)
        layout.addWidget(self.canvas, 1)
        self.notice = notice.Notice(central, tabs=self.view_bar)    # (0.321) what a command says, over the view
        self.notice.on_cancel = lambda: self.cancel_pick()
        self.last_message = ""                    # (0.321) the last thing said, ⚠ first for a refusal
        self.pick_request = None                  # (0.322) a command waiting for elements to be picked (_Pick)
        self._pick_busy = False
        self._help = None                         # (0.327) the Help window, made when first asked for
        self._verify_dialog = None                # (0.423) the Project regulations dialog while it is open
        self._rules_dialog = None                 # (0.426) the rules editor while it is open
        from ..render import canvas as views_canvas            # (0.341) the views light or dark, as chosen last
        views_canvas.set_dark(theme.dark_views())
        self.viewport = Viewport(self.canvas, self.doc)
        self.viewport.picture_loader = picture.load_pixels          # (the background images' pictures, 0.154)
        self.viewport.on_host_face = lambda obj: not self.doc.loading and bim.sheet_host(self.doc, obj) is not None
        cube = {name: icons.cube_face_image(t("cube." + name))                          # the view cube (0.79, 0.81)
                for name in ("top", "bottom", "front", "back", "right", "left")}
        cube.update(ring=icons.compass_image(t("cube.letters").split(), viewcube.RING_IN / viewcube.RING_OUT),
                    home=icons.house_image(),
                    roll_ccw=icons.roll_image(False), roll_cw=icons.roll_image(True), menu=icons.menu_image(),
                    arrow=icons.arrow_image())
        self.viewport.set_cube(cube)
        self.viewport.on_cube_menu = self._cube_menu
        self.setCentralWidget(central)
        self._current_3d = view_tabs.THREE_D          # the 3D view shown last: ("3d",) or a named one ("3d", uid)
        self._underlay_shown = None                   # (plan key, "below" | "above") of the underlay on screen
        self._underlay_later = False                  # (it is to be drawn again: the model changed)
        from . import presentation_glyphs
        self.views = view_tabs.ViewTabs(self.view_bar, self._show_view, self._view_tab_label,
                                        self.viewport.camera_snapshot, self.viewport.restore_camera,
                                        home_icon=lambda: ribbon.header_icon("home", theme.colour("text")),   # (0.403)
                                        present_icon=lambda: presentation_glyphs.icon(                        # (0.479)
                                            "scene", theme.colour("accent"), 16))
        self.presentation_mode = None             # (0.479) the ArqSynth Presentation tab (made with the panels)
        self.views.on_leave = self._left_view
        self.setWindowIcon(icons.app_icon())

        self.tools = {cls.name: cls(self) for cls in ALL_TOOLS}
        self.tool = None
        self._typed = ""
        self.pending_classify = None   # type chosen in "Classify as…" with nothing selected

        self._build_status_bar()
        self._build_actions()
        self._command_tips()
        self.tools["place"] = PlaceTool(self)      # (no button: started from the Project panel's library)
        self.tools["slab_outline"] = SlabOutlineTool(self)     # (no button: Editar contorno of a slab, 0.100)
        self.tools["platform_outline"] = PlatformOutlineTool(self)     # (Editar plataforma, 0.204)
        self.tools["facade_image"] = FacadeImageTool(self)     # (no button: an image put on a facade, 0.208)
        self.tools["crop_image"] = CropImageTool(self)         # (no button: a part of an image kept, 0.209)
        self.tools["wall_profile"] = WallProfileTool(self)     # (no button: Editar perfil of a wall, 0.109)
        self.tools["roof_blocks"] = RoofBlocksTool(self)       # (no button: a roof's blocks in the 3D view, 0.385)
        self.tools["pres_label"] = LabelPlaceTool(self)        # (no button: the Presentation tab's labels, 0.485)
        self._build_menus()
        self._build_toolbar()
        self._load_mouse_scheme()                  # (the middle button as chosen last time, 0.78)
        self.props = properties.dock(self)
        self.props.on_edit = self._on_property_edit
        self.props.on_edit_many = self._on_property_edit_many                  # (0.187) several at once
        self.props.on_restyle = self._show_properties                          # (0.338) the theme changed
        # (0.354) TAB: the quick edit of what is chosen, over the view beside it (ui/quick_edit.py)
        self.quick = quick_edit.QuickEdit(self.notice.parentWidget(), self._on_property_edit,
                                          self._on_property_edit_many)
        self.storeys_panel = storeys.dock(self, below=self.props)
        sp = self.storeys_panel
        sp.on_activate, sp.on_rename, sp.on_level = self.set_active_storey, self._rename_storey, self._move_storey
        sp.on_new, sp.on_delete, sp.on_only_active = self.new_storey, self._delete_storey, self.set_only_active_storey
        sp.on_typical = self.typical_floors
        sp.on_level_style = self.set_level_style                                # (0.462) the levels' look
        sp.on_typical_live = self.set_typical_live                              # (0.465) «=» on / off
        self.tree_panel = project_tree.dock(self, beside=self.storeys_panel, below=self.props)
        self.tree_panel.on_select, self.tree_panel.on_frame = self._select_from_tree, self._frame_from_tree
        self.tree_panel.on_shown = self._refresh_tree
        self.tree_panel.on_view = self.open_view
        self.tree_panel.on_view3d = self._view3d_action
        self.tree_panel.on_grid = self._grid_action
        self.tree_panel.on_library = self._library_action
        self.tree_panel.on_rename_section = self._rename_section
        self.tree_panel.on_remove_section = self.doc.remove_section
        self.tree_panel.on_sheet = self.sheet_action
        self.tree_panel.state_of = lambda ids, flag: controls.state_of(self.doc, ids, flag)      # (0.524)
        self.tree_panel.on_control = self.set_control
        self.tree_panel.on_element = self.tree_element_action
        self._isolated = None            # (0.524) the elements isolated from the navigator (the others hidden for now)
        self.tree_panel.set_names_of = lambda: sheets_model.set_names(self.doc.sheets)      # (0.128)
        self.tree_panel.on_template = self.template_action
        self.rules_panel = graphic_rules.dock(self, beside=self.storeys_panel)
        self.rules_panel.on_rule = self.apply_rule
        # (0.466) the Library: the components with their miniatures — the project's, a local folder's, the web's
        from . import library_panel
        self.library_panel = library_panel.dock(self)
        lp = self.library_panel
        lp.project_items = self._library_rows
        lp.project_shape = lambda guid: self.doc.ifc.component_shape(guid)
        lp.on_place = lambda guid: self._library_action("place", "component", guid)
        lp.on_bring, lp.on_save = self.library_bring, self.library_save
        lp.on_select = lambda guid: self._library_action("select", "component", guid)
        # (0.468) the Materials in the column, before the Library: their pictures («Selecionar») and the one chosen
        # («Editar»: in view, cut, realistic) — no window apart
        from . import material_editor
        self.materials_panel = material_editor.dock(self, self.doc)
        me = self.materials_panel.editor
        me.on_save, me.on_delete, me.on_pick = self._save_material, self._delete_material, self.pick_material
        QtCore.QTimer.singleShot(0, self.dock_titles)    # (0.374: a study palette chosen last time — its panels' titles,
        QtCore.QTimer.singleShot(0, self._tint_views)    #  its drawing area)
        self.rules_panel.on_select = self._select_from_tree
        self.rules_panel.on_properties = self._property_keys
        self.rule = None              # what the elements are coloured by (graphic rules), None: by class
        self._template_rule = None    # the rule the view template of the view shown set (None: none did)
        self._rule_values = {}        # GlobalId -> its value for the rule
        self._checked_commands = weakref.WeakSet()   # commands whose reservations were checked (shared projects)
        self._known_bim = set()       # BIM elements before the last change (to know what was removed)
        self._scene_thumbs = {}       # (0.363) scene key -> JPEG of its view (the Presentation panel's thumbnails)
        self._move_play = None        # (0.364) a scene's camera move being played: {frames, kept, timer, started}
        self._sheet_drawings = {}     # drawing key -> Drawing, made since the model last changed
        # (0.477, the owner: «a tabela deve ser gerada na tela e não no rodapé») a table is a tab's page over the canvas,
        # as a sheet is; the tables are chosen in the side panel «Tabelas»
        self.schedules_panel = schedules.dock(self.centralWidget())
        self._central_layout.addWidget(self.schedules_panel, 1)
        sp = self.schedules_panel
        sp.on_edit, sp.on_frame = self._on_property_edit, self._frame_from_tree
        sp.on_select = lambda ids: self._select_from_tree(self._circuit_points(ids))      # (a circuit: its points)
        sp.on_defs = lambda defs, label=None: self.doc.execute(schedules_model.SetScheduleDefs(   # (0.131) its own
            self.doc.schedule_defs, defs, label or t("cmd.schedules")))                 # (0.478: its cells' too)
        sp.on_message = lambda text, warning=True: self.message(text, warning=warning)   # (0.478)
        sp.on_put = lambda index, kind, ref: self.sheet_action("put", index, kind, ref)   # (0.132) on a sheet
        sp.on_shown, sp.on_export = lambda: self._refresh_schedules(), self._export_schedule
        sp.on_ref = self._table_ref_shown                                              # (0.477)
        sp.on_highlight = lambda ids: (self._select_from_tree(ids), self._frame_from_tree(ids))
        self.act_tables = QtGui.QAction(t("sched.title"), self)
        self.act_tables.setShortcut(QtGui.QKeySequence("Ctrl+T"))
        self.act_tables.triggered.connect(lambda _on=False: self.toggle_table())
        self.addAction(self.act_tables)  # (0.182: its key works with the menus hidden — a menu's own would not)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.props.toggleViewAction())   # reopen the panels after closing them
        self.view_menu.addAction(self.storeys_panel.toggleViewAction())
        self.view_menu.addAction(self.tree_panel.toggleViewAction())
        self.view_menu.addAction(self.act_tables)
        self.view_menu.addAction(self.rules_panel.toggleViewAction())
        self.ids_panel = ids_panel.dock(self)
        self.ids_panel.on_open = lambda: self.check_ids()
        self.ids_panel.on_again = lambda: self.check_ifc() if self._last_check == "ifc" else self.check_ids(
            self._ids_path)
        self.ids_panel.on_select = lambda ids: (self._select_from_tree(ids), self._frame_from_tree(ids))
        self.ids_panel.on_save = lambda: self.save_check_report()
        self._ids_path = None         # the IDS checked last
        self._last_check = "ids"      # what the panel shows: "ids" | "ifc" (the certification checks, 0.70)
        self.view_menu.addAction(self.ids_panel.toggleViewAction())
        self.notes_panel = notes_panel.dock(self, beside=self.ids_panel)
        np_ = self.notes_panel
        np_.on_new, np_.on_go, np_.on_comment = self.new_note, self.go_to_note, self.comment_note
        np_.on_toggle, np_.on_delete = self.toggle_note, self.delete_note
        np_.on_import, np_.on_export = self.import_notes, self.export_notes
        self.view_menu.addAction(self.notes_panel.toggleViewAction())
        self.panels_menu.addActions([p.toggleViewAction() for p in (                 # (0.182: the ribbon's View)
            self.props, self.storeys_panel, self.tree_panel, self.rules_panel, self.ids_panel, self.notes_panel)])
        self.panels_menu.addAction(self.act_tables)                                  # (0.477: a table's tab)
        self._build_modules()

        self.viewport.renderer.add_event_handler(self._on_pointer, "pointer_down", "pointer_move", "pointer_up")
        # Measurements can be typed whatever has the keyboard focus in this window
        # (the 3D view, the toolbar, the properties panel…), as in SketchUp.
        app = QtWidgets.QApplication.instance()
        app.installEventFilter(self)
        app.aboutToQuit.connect(lambda: app.removeEventFilter(self))    # (not while Qt takes things down)
        self.doc.subscribe(lambda changed, removed: self._on_document_changed(changed, removed))
        # (0.417) the Verifier: it watches the project and says what fails in the footer and at the foot of the view
        self.verifier = verify_bar.Verifier(self, self.doc, self.statusBar(), self.notice.parentWidget())
        self.hint_label.setMinimumWidth(64)     # (its room to the Verifier's indicator: the hint is whole in the balloon)
        self.verifier.on_goto = self._verify_goto
        self.verifier.on_marks = lambda marks: self.viewport.set_verify_marks(marks)
        self.verifier.on_settings = lambda: self.verify_settings()
        self.verify_panel = verify_panel.dock(self, beside=self.ids_panel)                   # (0.418)
        vpanel = self.verify_panel
        vpanel.on_goto, vpanel.on_why = self._verify_goto, self.verifier.why
        vpanel.on_except, vpanel.on_settings = self.verify_exception, lambda: self.verify_settings()
        vpanel.on_other = lambda name: self.ribbon_item(name).trigger()
        vpanel.on_sheet = lambda: self.verify_sheet()                   # (0.425)
        self.verifier.on_panel = self.show_verify_panel
        self.verifier.on_result = lambda result: vpanel.show_result(self.doc, result)
        self.panels_menu.addAction(vpanel.toggleViewAction())
        self.doc.subscribe(lambda changed, removed: self.verifier.changed())
        self.viewport.selection_listeners.append(lambda ids: self._refresh_properties())
        self.viewport.axes_listeners.append(lambda axes: self._refresh_properties())
        self.viewport.selection_listeners.append(lambda ids: self.tree_panel.show_selection(ids))
        self.viewport.selection_listeners.append(lambda ids: self.schedules_panel.show_selection(ids))
        self.viewport.selection_listeners.append(lambda ids: self._selection_changed_bar())     # (0.85)
        self.viewport.selection_listeners.append(lambda ids: self._update_context_tab())       # (0.298)
        self.viewport.selection_listeners.append(lambda ids: self.notice.dismiss())            # (0.321)
        self.viewport.selection_listeners.append(lambda ids: self._pick_changed())             # (0.322)
        self.viewport.axes_listeners.append(lambda axes: self._selection_changed_bar())
        self.viewport.rooms_listeners.append(lambda rooms: self._refresh_properties())          # (0.99)
        self.viewport.annotation_listeners.append(lambda anns: self._refresh_properties())      # (0.191)
        self.viewport.annotation_listeners.append(lambda anns: self._selection_changed_bar())   # (0.402: dimensions)

        self.resize(1440, 900)
        self.set_tool("select")
        self.views.open(view_tabs.THREE_D)
        self._on_document_changed()
        self.viewport.warm_up()     # GPU programs ready before the first file is opened

    # ------------------------------------------------------------ building the UI

    def _command_tips(self):
        """(0.346) Each window command with a tip of its own («tip.<name>» for act_<name>) shows it over its button and
        in the Help (F1) — those set one by one before too."""
        for name, act in list(vars(self).items()):
            if name.startswith("act_") and isinstance(act, QtGui.QAction) and i18n_has("tip." + name[4:]):
                act.setToolTip(t("tip." + name[4:]))

    def _action(self, text, slot, shortcuts=(), icon=None, checkable=False):
        act = QtGui.QAction(text, self)
        if icon is not None:
            act.setIcon(icon)
        act.setShortcuts([QtGui.QKeySequence(s) for s in shortcuts])
        act.setCheckable(checkable)
        act.triggered.connect(slot)
        self.addAction(act)  # shortcuts work wherever the focus is in the window
        return act

    def _build_actions(self):
        self.act_new = self._action(t("act.new"), self.new_document, ["Ctrl+N"])
        self.act_open = self._action(t("act.open"), self.open_file, ["Ctrl+O"])
        # (0.387) the start page, and a new project from a base file (a template)
        self.act_start_page = self._action(t("act.start_page"), lambda: self.show_start_page())
        self.act_new_from_base = self._action(t("act.new_from_base"), lambda: self.new_from_base())
        self.act_save = self._action(t("act.save"), self.save, ["Ctrl+S"])
        self.act_save_as = self._action(t("act.save_as"), self.save_as, ["Ctrl+Shift+S"])
        self.act_share = self._action(t("act.share"), lambda: self.share_project())
        self.act_open_shared = self._action(t("act.open_shared"), lambda: self.open_shared())
        self.act_sync = self._action(t("act.sync"), lambda: self.synchronise(), ["Ctrl+Alt+S"])
        self.act_reserve_views = self._action(t("act.reserve_views"), self.reserve_views)
        self.act_give_back = self._action(t("act.give_back"), self.give_back)
        self.act_pdf = self._action(t("act.export_pdf"), self.export_pdf, ["Ctrl+P"])
        self.act_dxf = self._action(t("act.export_dxf"), lambda: self.export_dxf())             # (0.129)
        self.act_splat = self._action(t("act.export_splat"), lambda: self.export_splat())       # (0.176)
        self.act_export_model = self._action(t("act.export_model"), lambda: self.export_model())  # (0.348; 0.349)
        self.act_export_presentation = self._action(t("act.export_presentation"),
                                                    lambda: self.export_presentation())             # (0.362)
        self.act_presentation_panel = self._action(t("act.presentation_panel"),
                                                   lambda: self.show_presentation_panel())          # (0.363)
        self.act_panorama = self._action(t("act.panorama"), lambda: self.render_panorama())       # (0.368)
        self.act_export_image = self._action(t("act.export_image"), lambda: self.export_image())  # (0.329)
        self.act_export_image.setToolTip("{}\n{}".format(t("act.export_image"), t("tip.export_image")))
        self.act_render = self._action(t("act.render"), lambda: self.render_realistic())         # (0.343)
        self.act_render.setToolTip("{}\n{}".format(t("act.render"), t("tip.render")))
        self.act_element_hatches = self._action(t("act.element_hatches"), lambda: self.element_hatches())   # (0.331)
        self.act_element_hatches.setToolTip("{}\n{}".format(t("act.element_hatches"), t("tip.element_hatches")))
        self.act_reset_patterns = self._action(t("act.reset_patterns"), lambda: self.reset_patterns())   # (0.332)
        self.act_reset_patterns.setToolTip("{}\n{}".format(t("act.reset_patterns"), t("tip.reset_patterns")))
        self.act_sheets_pdf = self._action(t("act.export_sheets"), lambda: self.sheet_action("export_all"))
        self.act_sheets_by_storey = self._action(t("act.sheets_by_storey"), lambda: self.sheets_by_storey())  # (0.127)
        self.act_sheets_by_storey.setToolTip(t("tip.sheets_by_storey"))
        self.act_quit = self._action(t("act.quit"), self.close, ["Ctrl+Q"])
        self.classify_actions = {}
        self.draw_type_actions = {}   # wall / slab / column / beam / footing / pipe / duct types for their tools
        self.opening_actions = {}     # door / window types
        self._make_type_actions()     # (made again when the project's types change, 0.87)
        self.act_types = self._action(t("act.types"), lambda: self.edit_types())
        self.act_tool_type = self._action(t("act.tool_type"), lambda: self.edit_tool_type(),
                                          icon=icons.gear_icon())                               # (0.183)
        self.act_materials = self._action(t("act.materials"), lambda: self.edit_materials())       # (0.89)
        self.act_undo = self._action(t("act.undo"), self.undo, ["Ctrl+Z"])
        self.act_redo = self._action(t("act.redo"), self.redo, ["Ctrl+Y", "Ctrl+Shift+Z"])
        self.act_delete = self._action(t("act.delete"), self._delete, ["Delete"])
        # (0.326) copy and paste, as Revit's clipboard: Ctrl+C, Ctrl+V (on the cursor), Ctrl+Shift+V (on storeys)
        self.act_copy_clip = self._action(t("act.copy_clip"), lambda: self.copy_to_clipboard(), ["Ctrl+C"],
                                          icon=icons.copy_clip_icon())
        self.act_paste = self._action(t("act.paste"), lambda: self.paste(), ["Ctrl+V"], icon=icons.paste_icon())
        # (0.525, as Blender's: Alt+H reveal, Shift+H hide the others, and Ctrl+H hide — H alone is the Pan)
        self.act_hide_sel = self._action(t("act.hide_sel"), lambda: self.hide_keys("hide"), ["Ctrl+H"])
        self.act_isolate = self._action(t("act.isolate"), lambda: self.hide_keys("isolate"), ["Shift+H"])
        self.act_reveal = self._action(t("act.reveal"), lambda: self.hide_keys("show_all"), ["Alt+H"])
        self.act_paste_storeys = self._action(t("act.paste_storeys"), lambda: self.paste_on_storeys(),
                                              ["Ctrl+Shift+V"], icon=icons.paste_storeys_icon())
        for act, key, tip in ((self.act_copy_clip, "Ctrl+C", "tip.copy_clip"), (self.act_paste, "Ctrl+V", "tip.paste"),
                              (self.act_paste_storeys, "Ctrl+Shift+V", "tip.paste_storeys")):
            act.setToolTip("{}   ({})\n{}".format(act.text(), key, t(tip)))
        self._clipboard = None                    # (ids, base point) copied with Ctrl+C
        self.act_delete_guides = self._action(t("act.delete_guides"), self.delete_guides)
        self.act_zoom_all = self._action(t("act.zoom_all"), lambda: self.viewport.zoom_extents(), ["Shift+Z"],
                                         icon=icons.zoom_all_icon())
        # navigation (0.78): zoom to the selection, the view history, the middle button's scheme
        self.act_zoom_selection = self._action(t("act.zoom_selection"), lambda: self.zoom_selection(), ["Shift+F"],
                                               icon=icons.zoom_selection_icon())
        self.act_view_back = self._action(t("act.view_back"), lambda: self.view_back(), ["Alt+Left"],
                                          icon=icons.view_back_icon())
        self.act_view_forward = self._action(t("act.view_forward"), lambda: self.view_forward(), ["Alt+Right"],
                                             icon=icons.view_forward_icon())
        schemes = QtGui.QActionGroup(self)
        self.act_mouse_sketchup = self._action(t("act.mouse_sketchup"), lambda: self.set_mouse_scheme("orbit"),
                                               checkable=True)
        self.act_mouse_revit = self._action(t("act.mouse_revit"), lambda: self.set_mouse_scheme("pan"),
                                            checkable=True)
        for act in (self.act_mouse_sketchup, self.act_mouse_revit):
            schemes.addAction(act)
        themes = QtGui.QActionGroup(self)                   # (0.338) the interface light or dark, on this computer
        self.act_theme_light = self._action(t("act.theme_light"), lambda: self.set_theme("light"), checkable=True)
        self.act_theme_dark = self._action(t("act.theme_dark"), lambda: self.set_theme("dark"), checkable=True)
        for act in (self.act_theme_light, self.act_theme_dark):
            themes.addAction(act)
        # (0.374) the five palettes of the owner's study
        self.act_theme_bege = self._action(t("act.theme_bege"), lambda: self.set_theme("bege"), checkable=True)
        self.act_theme_pedra = self._action(t("act.theme_pedra"), lambda: self.set_theme("pedra"), checkable=True)
        self.act_theme_escuro = self._action(t("act.theme_escuro"), lambda: self.set_theme("escuro"), checkable=True)
        self.act_theme_grafite = self._action(t("act.theme_grafite"), lambda: self.set_theme("grafite"),
                                              checkable=True)
        self.act_theme_revit = self._action(t("act.theme_revit"), lambda: self.set_theme("revit"), checkable=True)
        for name in theme.STUDY:
            themes.addAction(getattr(self, "act_theme_" + name))
        self.act_theme_studio = self._action(t("act.theme_studio"), lambda: self.explore_colours())
        self._check_theme()
        # (0.341) the views' background dark — apart from the interface's theme, as Revit's canvas theme
        self.act_canvas_dark = self._action(t("act.canvas_dark"), lambda: self.set_dark_views(
            self.act_canvas_dark.isChecked()), checkable=True)
        self.act_canvas_dark.setToolTip(t("tip.canvas_dark"))
        self.act_canvas_dark.setChecked(theme.dark_views())
        # (0.446) how drawing looks — the temporary dimensions, the angle, the snaps' glyphs, the outline being drawn: as
        # Revit's (the owner: «quero ter essa experiência no desenho como a do revit»), or as the addon's (0.372)
        looks = QtGui.QActionGroup(self)
        self.act_draw_revit = self._action(t("act.draw_revit"), lambda: self.set_draw_look("revit"), checkable=True)
        self.act_draw_addon = self._action(t("act.draw_addon"), lambda: self.set_draw_look("addon"), checkable=True)
        for act, tip in ((self.act_draw_revit, "tip.draw_revit"), (self.act_draw_addon, "tip.draw_addon")):
            looks.addAction(act)
            act.setToolTip(t(tip))
        saved = str(QtCore.QSettings("ArqSynth", "ArqSynth BIM").value("desenho/aspeto", "revit"))
        self.set_draw_look(saved if saved in ("revit", "addon") else "revit", remember=False)
        for act, key in ((self.act_zoom_all, "Shift+Z"), (self.act_zoom_selection, "Shift+F"),
                         (self.act_view_back, "Alt+←"), (self.act_view_forward, "Alt+→")):
            act.setToolTip("{}   ({})".format(act.text(), key))
        self.act_iso = self._action(t("act.view_iso"), lambda: self.set_view("iso"), ["F8"])
        self.act_top = self._action(t("act.view_top"), lambda: self.set_view("top"), ["F2"])
        self.act_front = self._action(t("act.view_front"), lambda: self.set_view("front"), ["F3"])
        self.act_plan = self._action(t("act.view_plan"), self.set_plan, ["F4"], checkable=True)
        self.act_last_section = self._action(t("act.last_section"), self.last_section, ["F5"])
        self.act_close_view = self._action(t("act.close_view"), lambda: self.views.close_current(), ["Ctrl+W"])
        self.act_next_view = self._action(t("act.next_view"), lambda: self.views.step(1), ["Ctrl+Tab"])
        self.act_prev_view = self._action(t("act.prev_view"), lambda: self.views.step(-1), ["Ctrl+Shift+Tab"])
        self.act_box = self._action(t("act.box"), self.set_box, ["F6"], checkable=True)
        self.act_box_selection = self._action(t("act.box_selection"), lambda: self.set_box(True, fit=True),
                                              ["Shift+F6"])
        self.act_view3d_new = self._action(t("act.view3d_new"), self.new_view3d, ["Ctrl+Shift+3"])
        self.act_dimension_walls = self._action(t("act.dimension_walls"), self.dimension_walls,
                                                icon=icons.dimension_walls_icon())
        self.act_dimension_facades = self._action(t("act.dimension_facades"), lambda: self.dimension_auto("facade"),
                                                  icon=icons.dimension_facades_icon())             # (0.123)
        self.act_dimension_facades.setToolTip(t("tip.dimension_facades"))
        self.act_dimension_rooms = self._action(t("act.dimension_rooms"), lambda: self.dimension_auto("room"),
                                                icon=icons.dimension_rooms_icon())
        self.act_dimension_rooms.setToolTip(t("tip.dimension_rooms"))
        self.act_dimension_style = self._action(t("act.dimension_style"), lambda: self.dimension_style())   # (0.124)
        # (0.402) a dimension string chosen, as Revit's: equal, its words, more references, a witness line taken away
        self.act_dim_eq = self._action(t("act.dim_eq"), lambda: self.dimension_equal())
        self.act_dim_text = self._action(t("act.dim_text"), lambda: self.edit_dimension_text())
        self.act_dim_add = self._action(t("act.dim_add"), lambda: self.dimension_add_references())
        self.act_dim_witness = self._action(t("act.dim_witness"), lambda: self.dimension_remove_witness())
        self.act_dim_text_back = self._action(t("act.dim_text_back"), lambda: self.dimension_text_back())
        for act, tip in ((self.act_dim_eq, "tip.dim_eq"), (self.act_dim_text, "tip.dim_text"),
                         (self.act_dim_add, "tip.dim_add"), (self.act_dim_witness, "tip.dim_witness")):
            act.setToolTip(t(tip))
        self.act_graphic_styles = self._action(t("act.graphic_styles"), lambda: self.graphic_styles())      # (0.126)
        self.act_symbol_styles = self._action(t("act.symbol_styles"), lambda: self.symbol_styles())       # (0.360)
        self.act_view_styles = self._action(t("act.view_styles"), lambda: self.edit_view_styles())          # (0.315)
        self.act_patterns = self._action(t("act.patterns"), lambda: self.edit_patterns())                   # (0.318)
        self.act_patterns.setToolTip(t("tip.patterns"))
        from . import pattern_picker                        # (0.319: «New…» / «Edit…» where a pattern is chosen)
        pattern_picker.EDITOR = lambda parent, key, new: self.edit_patterns(parent=parent, key=key, new=new)
        self.act_view_styles.setToolTip(t("tip.view_styles"))
        self.act_templates = self._action(t("act.templates"), lambda: self.template_action("edit"),
                                          icon=icons.view_templates_icon())
        self.act_edit_outline = self._action(t("act.edit_outline"), lambda: self.edit_slab_outline(),
                                             icon=icons.slab_outline_icon())
        self.act_edit_outline.setToolTip(t("tip.edit_outline"))
        self.act_merge_walls = self._action(t("act.merge_walls"), lambda: self.merge_walls(),
                                            icon=icons.merge_walls_icon())                  # (0.105)
        self.act_merge_walls.setToolTip(t("tip.merge_walls"))
        self.act_orthogonalize = self._action(t("act.orthogonalize"), lambda: self.orthogonalize_walls(),
                                              icon=icons.orthogonalize_icon())
        self.act_orthogonalize.setToolTip(t("tip.orthogonalize"))
        self.act_unjoin_walls = self._action(t("act.unjoin_walls"), lambda: self.unjoin_walls(),
                                             icon=icons.unjoin_walls_icon())
        self.act_unjoin_walls.setToolTip(t("tip.unjoin_walls"))
        self.act_attach_top = self._action(t("act.attach_top"), lambda: self.attach_top(),
                                           icon=icons.attach_top_icon())                    # (0.106)
        self.act_attach_top.setToolTip(t("tip.attach_top"))
        self.act_edit_profile = self._action(t("act.edit_profile"), lambda: self.edit_wall_profile(),
                                             icon=icons.wall_profile_icon())                # (0.109)
        self.act_edit_profile.setToolTip(t("tip.edit_profile"))
        self.act_reset_profile = self._action(t("act.reset_profile"), lambda: self.reset_wall_profiles(),
                                              icon=icons.reset_profile_icon())              # (0.298)
        self.act_reset_profile.setToolTip(t("tip.reset_profile"))
        self.act_detach_top = self._action(t("act.detach_top"), lambda: self.detach_top(),
                                           icon=icons.detach_top_icon())
        self.act_detach_top.setToolTip(t("tip.detach_top"))
        self.act_caixilho = self._action(t("act.caixilho"), lambda: self.open_caixilho_studio(),
                                         icon=icons.caixilho_icon())                        # (0.307)
        self.act_caixilho.setToolTip(t("tip.caixilho"))
        self.act_attach_base = self._action(t("act.attach_base"), lambda: self.attach_base(),
                                            icon=icons.attach_base_icon())                  # (0.302)
        self.act_attach_base.setToolTip(t("tip.attach_base"))
        self.act_detach_base = self._action(t("act.detach_base"), lambda: self.detach_base(),
                                            icon=icons.detach_base_icon())
        self.act_detach_base.setToolTip(t("tip.detach_base"))
        self.act_flip_walls = self._action(t("act.flip_walls"), lambda: self.flip_walls(),
                                           icon=icons.flip_walls_icon())                    # (0.299)
        self.act_flip_walls.setToolTip(t("tip.flip_walls"))
        self.act_join_wall_ends = self._action(t("act.join_wall_ends"), lambda: self.join_wall_ends(),
                                               icon=icons.join_wall_ends_icon())
        self.act_join_wall_ends.setToolTip(t("tip.join_wall_ends"))
        self.act_renumber = self._action(t("act.renumber"), lambda: self.renumber_openings(),
                                         icon=icons.renumber_icon())                       # (0.110)
        self.act_renumber.setToolTip(t("tip.renumber"))
        self.act_plan.setIcon(icons.plan_view_icon())
        for act, key in ((self.act_plan, "F4"), (self.act_dimension_walls, None), (self.act_templates, None)):
            act.setToolTip("{}   ({})".format(act.text(), key) if key else act.text())
        # the disciplines (0.182, the header's tabs; they replace the environments of 0.84): each its tools in the
        # ribbon — Ctrl+1…9 the first nine after Home
        self.disc_actions = {}
        discs = QtGui.QActionGroup(self)
        for d in ribbon.DISCIPLINES:
            key = ribbon.SHORTCUTS.get(d)
            act = self._action(t("disc." + d), lambda _=False, x=d: self.set_discipline(x), [key] if key else [],
                               checkable=True)
            act.setToolTip("{}{}\n{}".format(t("disc." + d), "   ({})".format(key) if key else "", t("tip.disc." + d)))
            discs.addAction(act)
            self.disc_actions[d] = act
        self.act_help = self._action(t("act.shortcuts"), lambda: self.show_help(), ["F1"])
        self.act_component_make = self._action(t("act.component_make"), lambda: self.make_component(), ["G"])
        self.act_component_edit = self._action(t("act.component_edit"), self.edit_component)
        self.act_component_close = self._action(t("act.component_close"), self.close_component)
        self.act_import_components = self._action(t("act.import_components"), lambda: self.import_components())
        self.act_import_model = self._action(t("act.import_model"), lambda: self.import_model())       # (0.351)
        self.act_room_program = self._action(t("act.room_program"), lambda: self.show_room_program())  # (0.357)
        self.act_import_image = self._action(t("act.import_image"), lambda: self.import_image(),
                                             icon=icons.image_icon())                                  # (0.154)
        self.act_images = self._action(t("act.images"), lambda: self.background_images())
        self.act_terrain_points = self._action(t("act.terrain_points"), lambda: self.import_terrain_points(),
                                               icon=icons.terrain_points_icon())                       # (0.155)
        self.act_terrain_dxf = self._action(t("act.terrain_dxf"), lambda: self.import_terrain_dxf())   # (0.156)
        self.act_slopes = self._action(t("act.terrain_slopes"), self.set_show_slopes, checkable=True)
        self.act_earthworks = self._action(t("act.earthworks"), lambda: self.earthworks(),
                                           icon=icons.earthworks_icon())                               # (0.157)
        self.act_edit_platform = self._action(t("act.edit_platform"), lambda: self.edit_platform(),
                                              icon=icons.platform_icon())                              # (0.204)
        self.act_edit_platform.setToolTip(t("tip.edit_platform"))
        self.act_cad_link = self._action(t("act.cad_link"), lambda: self.link_cad(), icon=icons.cad_link_icon())
        self.act_cad_links = self._action(t("act.cad_links"), lambda: self.cad_links())                # (0.158)
        self.act_walls_from_cad = self._action(t("act.walls_from_cad"), lambda: self.walls_from_cad(),
                                               icon=icons.walls_from_cad_icon())                       # (0.159)
        self.act_cloud_link = self._action(t("act.cloud_link"), lambda: self.link_cloud(),
                                           icon=icons.cloud_link_icon())                               # (0.161)
        self.act_cloud_links = self._action(t("act.cloud_links"), lambda: self.cloud_links())
        self.act_model_from_scan = self._action(t("act.model_from_scan"), lambda: self.model_from_scan(),
                                                icon=icons.model_from_scan_icon())                     # (0.162)
        self.act_analytical = self._action(t("act.analytical"), lambda: self.structure_check(),
                                           icon=icons.analytical_icon())                               # (0.163)
        self.act_show_analytical = self._action(t("act.show_analytical"), self.set_show_analytical, checkable=True)
        self.act_thin_lines = self._action(t("act.thin_lines"), lambda on=False: self.set_thin_lines(on),
                                           checkable=True)                    # (0.428)
        self.act_thin_lines.setToolTip(t("tip.thin_lines"))
        if str(QtCore.QSettings("ArqSynth", "ArqSynth BIM").value("vista/linhas_finas", "false")).lower() == "true":
            self.act_thin_lines.setChecked(True)
            self.viewport.set_thin_lines(True)
        self.act_moments = self._action(t("act.moments"), self.show_moments, checkable=True)     # (0.220)
        self.act_moments.setToolTip(t("tip.moments"))
        self.act_actions = self._action(t("act.actions"), lambda: self.structure_actions(),
                                        icon=icons.actions_icon())                                     # (0.164)
        self.act_analyse = self._action(t("act.analyse"), lambda: self.analyse_structure(),
                                        icon=icons.analyse_icon())                                     # (0.165)
        self.act_verify_ec2 = self._action(t("act.verify_ec2"), lambda: self.verify_structure(),
                                           icon=icons.verify_ec2_icon())                               # (0.166)
        self.act_rebar_schedule = self._action(t("act.rebar_schedule"), lambda: self.rebar_schedule(),
                                               icon=icons.rebar_schedule_icon())
        self.act_structure_quantities = self._action(t("act.structure_quantities"),
                                                     lambda: self.structure_quantities(),
                                                     icon=icons.structure_quantities_icon())            # (0.167)
        self.act_calc_report = self._action(t("act.calc_report"), lambda: self.calc_report(),
                                            icon=icons.calc_report_icon())
        self.act_steel_report = self._action(t("act.steel_report"), lambda: self.steel_report(),
                                             icon=icons.steel_report_icon())                            # (0.521)
        self.act_steel_report.setToolTip(t("tip.steel_report"))
        self.act_rebar_mesh = self._action(t("act.rebar_mesh"), lambda: self.rebar_mesh(),
                                           icon=icons.rebar_mesh_icon())                                # (0.522)
        self.act_rebar_mesh.setToolTip(t("tip.rebar_mesh"))
        self.act_cut_list = self._action(t("act.cut_list"), lambda: self.cut_list(), icon=icons.cut_list_icon())   # (0.169)
        self.act_profile_from_face = self._action(t("act.profile_from_face"), lambda: self.profile_from_face(),
                                                  icon=icons.profile_icon())                                # (0.245)
        self.act_control_ring = self._action(t("act.control_ring"), lambda: self.control_ring(),
                                             icon=icons.control_ring_icon())                            # (0.395)
        self.act_control_ring.setToolTip(t("tip.control_ring"))
        self.act_organic_form = self._action(t("act.organic_form"), lambda: self.organic_form(),
                                             icon=icons.control_ring_icon())                            # (0.555)
        self.act_organic_form.setToolTip(t("tip.organic_form"))
        self.act_keynote_table = self._action(t("act.keynote_table"), lambda: self.edit_keynote_table())    # (0.248)
        self.act_roof_profile = self._action(t("act.roof_profile"), lambda: self.roof_profile_from_face())   # (0.251)
        self.act_roof_profile.setToolTip(t("tip.roof_profile"))
        self.act_railing_types = self._action(t("act.railing_types"), lambda: self.edit_railing_types(),
                                              icon=icons.railing_icon())                                    # (0.260)
        self.act_railing_types.setToolTip(t("tip.railing_types"))
        self.act_ai_link = self._action(t("act.ai_link"), lambda on: self.set_ai_link(on), icon=icons.ai_link_icon(),
                                        checkable=True)                                                 # (0.269)
        self.act_ai_link.setToolTip(t("tip.ai_link"))
        self.act_ai_install = self._action(t("act.ai_install"), lambda: self.ai_install())                # (0.270)
        self.act_ai_install.setToolTip(t("tip.ai_install"))
        self.act_missing_data = self._action(t("act.missing_data"), lambda: self.missing_data())         # (0.273)
        self.act_missing_data.setToolTip(t("tip.missing_data"))
        self.act_worktop = self._action(t("act.worktop"), lambda: self.add_worktop(), icon=icons.worktop_icon())    # (0.170)
        self.act_verify_settings = self._action(t("act.verify_settings"), lambda: self.verify_settings())  # (0.417)
        self.act_verify_panel = self._action(t("act.verify_panel"), lambda: self.show_verify_panel())      # (0.418)
        self.act_verify_sheet = self._action(t("act.verify_sheet"), lambda: self.verify_sheet())          # (0.425)
        self.act_rules_editor = self._action(t("act.rules_editor"), lambda: self.rules_editor())          # (0.426)
        self.act_check_ids = self._action(t("act.check_ids"), lambda: self.check_ids())
        self.act_check_ifc = self._action(t("act.check_ifc"), lambda: self.check_ifc())
        self.act_site_location = self._action(t("act.site_location"), lambda: self.site_location())
        self.act_grid_generate = self._action(t("act.grid_generate"), lambda: self.generate_grid())
        self.act_grid_settings = self._action(t("act.grid_settings"), lambda: self.grid_settings())       # (0.91)
        self.act_columns_on_grid = self._action(t("act.columns_on_grid"), lambda: self.columns_on_grid(),
                                                icon=icons.columns_on_grid_icon())                     # (0.92)
        self.act_columns_on_grid.setToolTip(t("tip.columns_on_grid"))
        self.act_connect_network = self._action(t("act.connect_network"), lambda: self.connect_network(),
                                                icon=icons.fixture_icon())                             # (0.142)
        self.act_connect_network.setToolTip(t("tip.connect_network"))
        self.act_new_circuit = self._action(t("act.new_circuit"), lambda: self.new_circuit(),
                                            icon=icons.electrical_icon())                              # (0.144)
        self.act_new_circuit.setToolTip(t("tip.new_circuit"))
        self.act_route_circuits = self._action(t("act.route_circuits"), lambda: self.route_circuits(),
                                               icon=icons.conduit_icon())                              # (0.146)
        self.act_route_circuits.setToolTip(t("tip.route_circuits"))
        self.act_water_proposal = self._action(t("act.water_proposal"), lambda: self.water_proposal(),
                                               icon=icons.fixture_icon())                              # (0.148)
        self.act_water_proposal.setToolTip(t("tip.water_proposal"))
        self.act_remove_water_proposal = self._action(t("act.remove_water_proposal"),
                                                      lambda: self.remove_water_proposal())
        self.act_clashes = self._action(t("act.clashes"), lambda: self.clashes())                    # (0.149)
        self.act_clashes.setToolTip(t("tip.clashes"))
        self.act_electrical_check = self._action(t("act.electrical_check"), lambda: self.electrical_check())  # (0.147)
        self.act_electrical_check.setToolTip(t("tip.electrical_check"))
        self.act_electrical_proposal = self._action(t("act.electrical_proposal"), lambda: self.electrical_proposal(),
                                                    icon=icons.electrical_icon())                      # (0.145)
        self.act_electrical_proposal.setToolTip(t("tip.electrical_proposal"))
        self.act_remove_electrical_proposal = self._action(t("act.remove_electrical_proposal"),
                                                           lambda: self.remove_electrical_proposal())
        self.act_remove_electrical_proposal.setToolTip(t("tip.remove_electrical_proposal"))
        self.act_footings_under = self._action(t("act.footings_under"), lambda: self.footings_under(),
                                               icon=icons.footings_under_icon())                       # (0.93)
        self.act_footings_under.setToolTip(t("tip.footings_under"))
        self.act_combined_footing = self._action(t("act.combined_footing"), lambda: self.combined_footing(),
                                                 icon=icons.footings_under_icon())                     # (0.249)
        self.act_combined_footing.setToolTip(t("tip.combined_footing"))
        self.act_beams_between = self._action(t("act.beams_between"), lambda: self.beams_between(),
                                              icon=icons.beams_between_icon())                         # (0.94)
        self.act_beams_between.setToolTip(t("tip.beams_between"))
        self.act_base_plate = self._action(t("act.base_plate"), lambda: self.base_plates(),
                                           icon=icons.base_plate_icon())                                # (0.497)
        self.act_base_plate.setToolTip(t("tip.base_plate"))
        self.act_number_steel = self._action(t("act.number_steel"), lambda: self.number_steel(),
                                             icon=icons.number_steel_icon())                            # (0.500)
        self.act_number_steel.setToolTip(t("tip.number_steel"))
        self.act_steel_nc = self._action(t("act.steel_nc"), lambda: self.export_steel_nc(),
                                         icon=icons.steel_nc_icon())                                    # (0.501)
        self.act_steel_nc.setToolTip(t("tip.steel_nc"))
        self.act_end_plate = self._action(t("act.end_plate"), lambda: self.beam_connections("end_plate"),
                                          icon=icons.end_plate_icon())                                  # (0.498)
        self.act_end_plate.setToolTip(t("tip.end_plate"))
        self.act_fin_plate = self._action(t("act.fin_plate"), lambda: self.beam_connections("fin_plate"),
                                          icon=icons.fin_plate_icon())
        self.act_fin_plate.setToolTip(t("tip.fin_plate"))
        self.act_gusset = self._action(t("act.gusset"), lambda: self.gussets(), icon=icons.gusset_icon())  # (0.503)
        self.act_gusset.setToolTip(t("tip.gusset"))
        self.act_purlin_cleat = self._action(t("act.purlin_cleat"), lambda: self.purlin_cleats(),
                                             icon=icons.purlin_cleat_icon())                            # (0.504)
        self.act_purlin_cleat.setToolTip(t("tip.purlin_cleat"))
        self.act_knee_plate = self._action(t("act.knee_plate"), lambda: self.knee_plate(),
                                           icon=icons.knee_plate_icon())                                # (0.513)
        self.act_knee_plate.setToolTip(t("tip.knee_plate"))
        self.act_steel_mitre = self._action(t("act.steel_mitre"), lambda: self.steel_mitre(),
                                            icon=icons.steel_mitre_icon())                              # (0.496)
        self.act_steel_mitre.setToolTip(t("tip.steel_mitre"))
        self.act_walls_under_beams = self._action(t("act.walls_under_beams"), lambda: self.walls_under_beams(),
                                                  icon=icons.walls_under_beams_icon())                 # (0.95)
        self.act_walls_under_beams.setToolTip(t("tip.walls_under_beams"))
        self.act_slabs_in_bays = self._action(t("act.slabs_in_bays"), lambda: self.slabs_in_bays(),
                                              icon=icons.slabs_in_bays_icon())                         # (0.96)
        self.act_slabs_in_bays.setToolTip(t("tip.slabs_in_bays"))
        self.act_beam_system = self._action(t("act.beam_system"), lambda: self.beam_system(),
                                            icon=icons.beam_system_icon())                             # (0.97)
        self.act_beam_system.setToolTip(t("tip.beam_system"))
        self.act_propose_structure = self._action(t("act.propose_structure"), lambda: self.propose_structure(),
                                                  icon=icons.propose_structure_icon())                 # (0.98)
        self.act_propose_structure.setToolTip(t("tip.propose_structure"))
        self.act_remove_proposal = self._action(t("act.remove_proposal"), lambda: self.remove_proposal(),
                                                icon=icons.remove_proposal_icon())
        self.act_remove_proposal.setToolTip(t("tip.remove_proposal"))
        # selection (0.75): select all / invert / none; what dragging draws; a polygon or a fence clicked
        self.act_select_all = self._action(t("act.select_all"), lambda: self.select_all(), ["Ctrl+A"])
        self.act_select_invert = self._action(t("act.select_invert"), lambda: self.select_invert(), ["Ctrl+I"])
        self.act_select_none = self._action(t("act.select_none"), lambda: self.select_none())
        shapes = QtGui.QActionGroup(self)
        self.act_drag_box = self._action(t("act.drag_box"), lambda: self.set_drag_shape("box"), checkable=True)
        self.act_drag_lasso = self._action(t("act.drag_lasso"), lambda: self.set_drag_shape("lasso"), checkable=True)
        for act in (self.act_drag_box, self.act_drag_lasso):
            shapes.addAction(act)
        self.act_drag_box.setChecked(True)
        self.act_drag_elements = self._action(t("act.drag_elements"), lambda on=False: self.set_drag_elements(on),
                                              checkable=True)                 # (0.427)
        self.act_drag_elements.setToolTip(t("act.drag_elements") + " — " + t("tip.drag_elements"))
        from . import command_icons
        drawn = command_icons.icon("drag_elements")
        if drawn is not None:
            self.act_drag_elements.setIcon(drawn)
        self.act_drag_elements.setChecked(str(QtCore.QSettings("ArqSynth", "ArqSynth BIM").value(
            "selecao/arrastar", "true")).lower() == "true")
        self.tools["select"].drag_elements = self.act_drag_elements.isChecked()
        faces = QtGui.QActionGroup(self)                    # (0.361) a wall's temporary dimensions: axes or faces
        self.act_dims_axes = self._action(t("act.dims_axes"), lambda: self.set_dim_faces(False), checkable=True)
        self.act_dims_faces = self._action(t("act.dims_faces"), lambda: self.set_dim_faces(True), checkable=True)
        for act, tip in ((self.act_dims_axes, "tip.dims_axes"), (self.act_dims_faces, "tip.dims_faces")):
            faces.addAction(act)
            act.setToolTip(t(tip))
        self.dim_faces = str(QtCore.QSettings("ArqSynth", "ArqSynth BIM").value("cotas/face_a_face",
                                                                                "false")).lower() == "true"
        (self.act_dims_faces if self.dim_faces else self.act_dims_axes).setChecked(True)
        self.act_pick_polygon =self._action(t("act.pick_polygon"), lambda: self.pick_region("polygon"))
        self.act_pick_fence = self._action(t("act.pick_fence"), lambda: self.pick_region("fence"))
        self.act_same_type = self._action(t("act.same_type"), lambda: self.select_same("view"))     # (0.85)
        self.act_same_type.setToolTip(t("act.same_type_view"))
        self.act_filter_selection = self._action(t("act.filter_selection"), lambda: self.filter_selection())
        self.act_select_by = self._action(t("act.select_by"), lambda: self.select_by())
        self.act_selectable = self._action(t("act.selectable"), lambda: self.selectable_categories())
        for act, tip in ((self.act_filter_selection, "tip.filter_selection"), (self.act_select_by, "tip.select_by"),
                         (self.act_selectable, "tip.selectable")):
            act.setToolTip(t(tip))
        for act, tip in ((self.act_drag_box, "tip.drag_box"), (self.act_drag_lasso, "tip.drag_lasso"),
                         (self.act_pick_polygon, "tip.pick_polygon"), (self.act_pick_fence, "tip.pick_fence")):
            act.setToolTip(t(tip))
        self.act_new_note = self._action(t("act.new_note"), lambda: self.new_note())
        self.act_group_make = self._action(t("act.group_make"), lambda: self.make_group(), ["Ctrl+G"])
        self.act_group_ungroup = self._action(t("act.group_ungroup"), self.ungroup)
        self.act_repeat = self._action(t("act.repeat_storeys"), lambda: self.repeat_on_storeys())
        self.act_storey_new = self._action(t("act.storey_new"), self.new_storey)
        self.act_storey_up = self._action(t("act.storey_up"), lambda: self.step_storey(+1), ["PgUp"])
        self.act_storey_down = self._action(t("act.storey_down"), lambda: self.step_storey(-1), ["PgDown"])
        self.act_only_active = self._action(t("storeys.only_active"), self.set_only_active_storey, checkable=True)
        self.act_typical = self._action(t("act.typical"), lambda: self.typical_floors())       # (0.90)
        # (0.374, the study's ribbon) the Wall tool's shapes as buttons of their own; rooms found at once; the areas
        self.act_wall_rect = self._action(t("act.wall_rect"), lambda: self.wall_shape("rect"))
        self.act_wall_circle = self._action(t("act.wall_circle"), lambda: self.wall_shape("circle"))
        self.act_wall_arc = self._action(t("act.wall_arc"), lambda: self.wall_shape("arc"))
        self.act_wall_face = self._action(t("act.wall_face"), lambda: self.wall_shape("face"))
        self.act_wall_wand = self._action(t("act.wall_wand"), lambda: self.wall_shape("wand"))
        self.act_rooms_identify = self._action(t("act.rooms_identify"), lambda: self.identify_rooms())
        self.act_areas = self._action(t("act.areas"), lambda: self.show_areas())

        self.tool_actions = {}
        group = QtGui.QActionGroup(self)
        keys = {"select": "Space", "line": "L", "rectangle": "R", "push_pull": "P", "move": "M", "rotate": "Q",
                "tape": "T", "wall": "W", "slab": "", "column": "", "beam": "", "footing": "", "door": "D",
                "window": "J", "pipe": "", "duct": "", "grid": "", "section": "", "dimension": "C",
                "orbit": "O", "pan": "H", "zoom": "Z", "zoom_window": "Ctrl+Shift+W",      # (as SketchUp's, 0.78)
                "position_camera": "", "look_around": "", "walk": "", "room": "", "ramp": "", "split_wall": "",
                "corner_walls": "", "align": "", "mirror": "", "roof": "", "drain": "", "roof_opening": "",
                "stair": "", "railing": "", "curtain_wall": "", "ceiling": "", "wall_finish": "", "light": "", "draft": "", "detail": "",
                "air_terminal": "", "equipment": "", "fixture": "", "electrical": "", "conduit": "", "circle": "", "offset": "F", "scale": "",
                "calibrate_image": "", "terrain": "", "platform": "", "terrain_ramp": "", "cabinet": "", "kitchen": "",
                "appliance": "",
                "profile": "", "curtain_panel": "", "split_gap": "", "trim_extend": "", "wall_joins": "",
                "wall_opening": "", "wall_sweep": "", "wall_reveal": "", "copy": "", "array": "",
                "join_geometry": "", "unjoin_geometry": "",
                "arc": "A", "freehand": "", "bezier": "",                                 # (0.373, as SketchUp's A)
                "niche": "", "flooring": "", "gutter": "", "elevator": "", "room_separator": "",   # (0.374)
                "perforated_panel": "",                                                    # (0.389)
                "ripado_panel": "",                                                        # (0.434)
                "loose_furniture": "",                                                     # (0.440)
                "ripado_screen": "",                                                       # (0.441)
                "paint": "B",                                         # (0.391, SketchUp's Paint Bucket)
                "param_surface": "",                                  # (0.395)
                "organic_points": "",                                 # (0.556)
                "dim_exterior": "", "dim_interior": "",               # (0.399, 0.400)
                "work_plane": "",                                     # (0.412)
                "lot": "",                                            # (0.423)
                "room_need": "",                                      # (0.475: a programme line placed)
                "steel_member": "",                                   # (0.495)
                "steel_shed": "",                                     # (0.499)
                "steel_truss": "",                                    # (0.507)
                "steel_stair": ""}                                    # (0.509)
        for name in self.tools:
            key = keys[name]
            shown = ("Espaço" if lang() == "pt" else "Space") if key == "Space" else key
            label = "{}   ({})".format(t("tool." + name), shown) if key else t("tool." + name)
            slot = (lambda _=False: self.zoom_window()) if name == "zoom_window" else \
                (lambda _=False, n=name: self.set_tool(n))
            act = self._action(label, slot, [key] if key else [], icon=icons.TOOL_ICONS[name](), checkable=True)
            act.setToolTip(label)
            group.addAction(act)
            self.tool_actions[name] = act

    def _build_menus(self):
        mb = self.menuBar()
        m = mb.addMenu(t("menu.file"))
        m.addActions([self.act_new, self.act_open, self.act_save, self.act_save_as])
        m.addSeparator()
        m.addAction(self.act_import_image)                  # (0.154)
        m.addAction(self.act_terrain_points)                # (0.155)
        m.addAction(self.act_terrain_dxf)                   # (0.156)
        m.addAction(self.act_cad_link)                      # (0.158)
        m.addAction(self.act_cloud_link)                    # (0.161)
        m.addSeparator()
        team = m.addMenu(t("menu.team"))
        team.addActions([self.act_share, self.act_open_shared])
        team.addSeparator()
        team.addActions([self.act_sync, self.act_reserve_views, self.act_give_back])
        m.addSeparator()
        m.addAction(self.act_pdf)
        m.addAction(self.act_dxf)
        m.addAction(self.act_splat)
        m.addAction(self.act_export_image)
        m.addAction(self.act_sheets_pdf)
        m.addAction(self.act_sheets_by_storey)
        m.addSeparator()
        m.addAction(self.act_quit)
        m = mb.addMenu(t("menu.edit"))
        m.addActions([self.act_undo, self.act_redo])
        m.addSeparator()
        m.addAction(self.act_delete)
        m.addAction(self.act_delete_guides)
        m.addSeparator()
        sel = m.addMenu(t("menu.selection"))                  # (0.75)
        sel.addActions([self.act_select_all, self.act_select_invert, self.act_select_none])
        sel.addSeparator()
        sel.addActions([self.act_drag_box, self.act_drag_lasso, self.act_pick_polygon, self.act_pick_fence])
        sel.addSeparator()
        sel.addActions([self.act_drag_elements])                # (0.427)
        sel.addSeparator()
        sel.addActions([self.act_filter_selection, self.act_select_by, self.act_selectable])
        m = mb.addMenu(t("menu.view"))
        env = m.addMenu(t("menu.disciplines"))              # (0.182: the disciplines; the environments, 0.84)
        env.addActions([self.disc_actions[d] for d in ribbon.DISCIPLINES])
        m.addSeparator()
        m.addActions([self.act_zoom_all, self.tool_actions["zoom_window"], self.act_zoom_selection,
                      self.act_view_back, self.act_view_forward])
        nav = m.addMenu(t("menu.navigate"))
        nav.addActions([self.tool_actions["orbit"], self.tool_actions["pan"], self.tool_actions["zoom"]])
        nav.addSeparator()
        nav.addActions([self.tool_actions["position_camera"], self.tool_actions["look_around"],
                        self.tool_actions["walk"]])
        nav.addSeparator()
        nav.addActions([self.act_mouse_sketchup, self.act_mouse_revit])
        m.addSeparator()
        m.addActions([self.act_iso, self.act_top, self.act_front])
        m.addSeparator()
        m.addAction(self.act_plan)
        m.addAction(self.tool_actions["section"])
        m.addAction(self.act_last_section)
        m.addActions([self.act_box, self.act_box_selection, self.act_view3d_new])
        m.addSeparator()
        m.addActions([self.act_next_view, self.act_prev_view, self.act_close_view])
        m.addAction(self.tool_actions["dimension"])
        m.addActions([self.act_dimension_walls, self.act_dimension_facades, self.act_dimension_rooms,
                      self.act_dimension_style, self.act_graphic_styles])
        m.addSeparator()
        m.addAction(self.act_templates)
        m.addAction(self.act_images)                        # (0.154)
        m.addAction(self.act_cad_links)                     # (0.158)
        m.addAction(self.act_cloud_links)                   # (0.161)
        m.addAction(self.act_slopes)                        # (0.156)
        m.addAction(self.act_earthworks)                    # (0.157)
        m.addAction(self.act_show_analytical)               # (0.163)
        self.view_menu = m
        m = mb.addMenu(t("menu.tools"))
        m.addActions(list(self.tool_actions.values()))
        m = mb.addMenu(t("menu.bim"))
        self.classify_menu = m.addMenu(t("act.classify"))
        m.addAction(self.act_walls_from_cad)                # (0.159)
        m.addAction(self.act_model_from_scan)               # (0.162)
        m.addAction(self.act_analytical)                    # (0.163)
        m.addAction(self.act_actions)                       # (0.164)
        m.addAction(self.act_analyse)                       # (0.165)
        m.addAction(self.act_verify_ec2)                    # (0.166)
        m.addAction(self.act_rebar_schedule)
        m.addAction(self.act_structure_quantities)          # (0.167)
        m.addAction(self.act_calc_report)
        m.addAction(self.act_steel_report)                  # (0.521)
        m.addAction(self.act_cut_list)                      # (0.169)
        m.addAction(self.act_worktop)                       # (0.170)
        m.addSeparator()
        m.addAction(self.act_types)                         # (0.87)
        m.addAction(self.act_materials)                     # (0.89)
        self.type_menus = {}
        for kind, label in (("wall", "act.wall_types"), ("slab", "act.slab_types"),
                            ("roof", "act.roof_types"), ("column", "act.column_types"),             # (roof: 0.278)
                            ("beam", "act.beam_types"), ("footing", "act.footing_types"),
                            ("pipe", "act.pipe_types"), ("duct", "act.duct_types"),
                            ("conduit", "act.conduit_types")):
            self.type_menus[kind] = m.addMenu(t(label))
        for kind, label in (("door", "act.door_types"), ("window", "act.window_types")):
            self.type_menus[kind] = m.addMenu(t(label))
        self._fill_type_menus()
        m.addAction(self.act_renumber)                     # (0.110)
        m.addAction(self.act_connect_network)              # (0.142)
        m.addAction(self.act_water_proposal)               # (0.148)
        m.addAction(self.act_remove_water_proposal)
        m.addAction(self.act_new_circuit)                  # (0.144)
        m.addAction(self.act_route_circuits)               # (0.146)
        m.addAction(self.act_electrical_check)             # (0.147)
        m.addAction(self.act_clashes)                      # (0.149)
        m.addAction(self.act_electrical_proposal)          # (0.145)
        m.addAction(self.act_remove_electrical_proposal)
        m.addAction(self.act_grid_generate)
        m.addAction(self.act_grid_settings)
        m.addAction(self.act_columns_on_grid)
        m.addAction(self.act_footings_under)
        m.addAction(self.act_beams_between)
        m.addAction(self.act_walls_under_beams)
        m.addAction(self.act_slabs_in_bays)
        m.addAction(self.act_beam_system)
        m.addActions([self.act_propose_structure, self.act_remove_proposal])
        m.addSeparator()
        m.addActions([self.act_component_make, self.act_component_edit, self.act_component_close,
                      self.act_import_components, self.act_import_model])
        m.addSeparator()
        m.addActions([self.act_group_make, self.act_group_ungroup])
        m.addSeparator()
        m.addActions([self.act_storey_new, self.act_storey_up, self.act_storey_down, self.act_only_active,
                      self.act_repeat, self.act_typical])
        m.addSeparator()
        phases = m.addMenu(t("act.phase"))
        self.phase_menu = phases                            # (0.182: also a dropdown of the ribbon's Manage)
        self.phase_actions = {}
        for value in ("EXISTING", "NEW", "DEMOLISH", "TEMPORARY", None):
            label = t("phase." + value.lower()) if value else t("props.no_phase")
            act = phases.addAction(label, lambda v=value: self.set_phase(v))
            self.phase_actions[value] = act
        m.addSeparator()
        m.addAction(self.act_check_ids)
        m.addAction(self.act_check_ifc)
        m.addAction(self.act_site_location)
        m.addAction(self.act_new_note)
        m = mb.addMenu(t("menu.help"))
        m.addAction(self.act_help)

    def _make_type_actions(self):
        """The actions that choose a type (Classify as…, the BIM menu's lists of types): one per type to draw
        with (catalog.types()) — made again when the project's types change (0.87)."""
        for act in list(self.classify_actions.values()) + list(self.draw_type_actions.values()) + \
                list(self.opening_actions.values()):
            self.removeAction(act)
            act.deleteLater()
        self.classify_actions, self.draw_type_actions, self.opening_actions = {}, {}, {}
        for spec in _by_kind(catalog.types()):
            name = spec.name_pt if lang() == "pt" else spec.name_en
            if spec.kind in catalog.CLASSIFIABLE:
                self.classify_actions[spec.key] = self._action(name, lambda _=False, s=spec: self.classify(s))
            self.draw_type_actions[spec.key] = self._action(name, lambda _=False, s=spec: self.use_draw_type(s))
        for spec in catalog.openings():
            name = spec.name_pt if lang() == "pt" else spec.name_en
            self.opening_actions[spec.key] = self._action(name, lambda _=False, s=spec: self.use_opening_type(s))

    def _fill_type_menus(self):
        """Classify as… and the BIM menu's lists of types, as the types are now."""
        self.classify_menu.clear()
        kind = None
        for spec in (s for s in _by_kind(catalog.types()) if s.kind in catalog.CLASSIFIABLE):
            if kind is not None and spec.kind != kind:
                self.classify_menu.addSeparator()
            kind = spec.kind
            self.classify_menu.addAction(self.classify_actions[spec.key])
        for kind, menu in self.type_menus.items():
            menu.clear()
            if kind in ("door", "window"):
                menu.addActions([self.opening_actions[s.key] for s in catalog.openings() if s.kind == kind])
            else:
                menu.addActions([self.draw_type_actions[s.key] for s in catalog.types() if s.kind == kind])

    def _refresh_types(self):
        """The project's types (in its IFC, 0.87) as the ones to draw with: when they change (the type editor,
        undo, another file), the menus, the contextual bar, the Properties panel and the tools follow."""
        if not hasattr(self, "type_menus") or self.doc.loading:
            return
        from ..core import patterns as core_patterns
        own_patterns = self.doc.ifc.patterns() if hasattr(self.doc.ifc, "patterns") else []
        core_patterns.set_project(own_patterns)             # (0.318: before the materials that may use them)
        specs = project_types.read(self.doc.ifc)
        materials = project_types.materials(self.doc.ifc)
        openings = project_types.read_openings(self.doc.ifc)
        signature = (tuple(specs), tuple(materials), tuple(openings), tuple(own_patterns))
        if signature == getattr(self, "_types_signature", None):
            return
        self._types_signature = signature
        catalog.set_project(specs, materials)
        catalog.set_project_openings(openings)
        if hasattr(self, "materials_panel"):
            self.materials_panel.materials_changed()        # (0.468: their pictures, again)
        if hasattr(self, "viewport"):
            self.viewport.materials_changed()               # (0.315: the elements seen by their materials)
        self._make_type_actions()
        self._fill_type_menus()
        for tool in self.tools.values():                     # (a type changed or gone: the tool's follows)
            for attr in ("spec", "pad", "strip"):
                spec = getattr(tool, attr, None)
                if isinstance(spec, catalog.TypeSpec):
                    same = catalog.BY_KEY.get(spec.key)
                    if same is None or same.kind != spec.kind:
                        same = next(s for s in catalog.types() if s.kind == spec.kind and s.strip == spec.strip)
                    setattr(tool, attr, same)
                elif isinstance(spec, catalog.OpeningSpec):
                    same = catalog.OPENING_BY_KEY.get(spec.key)
                    if same is None or same.kind != spec.kind:
                        same = next(s for s in catalog.openings() if s.kind == spec.kind)
                    setattr(tool, attr, same)
        self._sync_context_bar()

    def edit_types(self, kind=None, key=None):
        """BIM ▸ Types… (0.87): the type editor — make, duplicate, change and remove the project's types
        (key: the one shown first)."""
        from .type_editor import TypeEditor
        dialog = TypeEditor(self, self.doc, kind)
        if key in catalog.BY_KEY or key in catalog.OPENING_BY_KEY:
            dialog.select(key)
        dialog.on_save = self._save_type
        dialog.on_delete = self._delete_type
        dialog.on_where = self._type_where                  # (0.429)
        dialog.on_replace = self._replace_type
        dialog.on_materials = lambda: self.edit_materials(parent=dialog)
        dialog.on_type_data = self._save_type_data          # (0.271: the type's IFC data)
        self._type_dialog = dialog                          # (tests)
        dialog.exec()
        self._type_dialog = None

    def edit_opening_design(self, spec):
        """(0.289) The door and window editor on a door / window type (an OpeningSpec) — (0.307) the Caixilho Studio:
        Guardar saves the type with its new design — its doors / windows follow, one undo step. The saved type's key,
        or None."""
        keys = self.open_caixilho_studio([spec], insert=False)
        return keys[0] if keys else None

    def open_caixilho_studio(self, specs=None, insert=True):
        """(0.307) The Caixilho Studio (the owner's prototype) on door / window types — the one being drawn with, else
        a new window: what is new or changed is saved as types (one undo step each; a type made a door from a window,
        or the other way, a new one), «Inserir no modelo» then draws with the one shown. The keys saved."""
        from ..core import caixilho as cx
        from .caixilho_studio import CaixilhoStudio
        if getattr(self.doc, "loading", False):
            return []
        if specs is None:
            spec = getattr(self.tool, "spec", None)
            specs = [spec] if isinstance(spec, catalog.OpeningSpec) else []
        name = (lambda s: s.name_pt if lang() == "pt" else s.name_en)                  # noqa: E731
        items = [cx.from_design(catalog.design_of(s), s.width, s.height, s.sill, name(s), s.key) for s in specs]
        taken = {name(s) for s in catalog.openings()}
        if not items:
            first = cx.default_window()
            first.name = cx.next_name([cx.Opening(n, "", 0, 0, 0, 0, "", "", []) for n in taken], "window")
            items = [first]
        dialog = CaixilhoStudio(self, items, insert=insert, taken=taken)
        self._studio = dialog                               # (tests)
        accepted = dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
        self._studio = None
        if not accepted:
            return []
        saved = {}
        for op, design in dialog.changed_items():
            spec = catalog.OPENING_BY_KEY.get(op.key) if op.key else None
            old = spec if spec is not None and spec.kind == op.kind and \
                project_types.find_type(self.doc.ifc, spec) is not None else None
            if spec is None or spec.kind != op.kind:
                spec = catalog.OpeningSpec("t:new", op.kind, op.name, op.name, 1.0, 1.0)
            others = {name(s) for s in catalog.openings() if s.key != spec.key}
            label, n = op.name, 2
            while label in others:
                label, n = "{} ({})".format(op.name, n), n + 1
            new = catalog.with_design(dataclasses.replace(spec, name_pt=label, name_en=label, width=op.W / 1000.0,
                                                          height=op.H / 1000.0, sill=op.sill / 1000.0), design)
            key = self._save_type(new, old)
            if key is not None:
                saved[id(op)] = key
        if dialog.inserting:
            key = saved.get(id(dialog.op)) or dialog.op.key
            spec = catalog.OPENING_BY_KEY.get(key)
            if spec is not None:
                self.use_opening_type(spec)
                self.message(t("info.caixilho_inserted", name=name(spec)))
        elif saved:
            self.message(t("info.caixilho_saved", n=len(saved)))
        return list(saved.values())

    def edit_tool_type(self):
        """(0.183) The contextual bar's gear: the type the tool draws with, in the type editor — (0.260) the
        Railing tool's in the railing type editor."""
        if getattr(self.tool, "name", None) == "railing":
            self.edit_railing_types(self.tool.style)
            return
        spec = getattr(self.tool, "spec", None)
        if isinstance(spec, (catalog.TypeSpec, catalog.OpeningSpec)):
            self.edit_types(spec.kind, key=spec.key)

    def edit_railing_types(self, key=None):
        """(0.260) Architecture ▸ Railing types…: the railing type editor — the program's types and the project's,
        made (duplicated), changed, removed; applying one makes its railings again."""
        from .railing_type_editor import RailingTypeEditor
        if getattr(self.doc, "loading", False):
            return
        dialog = RailingTypeEditor(self, self.doc, key)
        dialog.on_save = self._save_railing_type
        dialog.on_delete = self._delete_railing_type
        self._railing_type_dialog = dialog                  # (tests)
        dialog.exec()
        self._railing_type_dialog = None
        if self.tool is not None and getattr(self.tool, "name", None) == "railing":
            self._refresh_context_bar()                     # (the Type list: its new types)

    def register_tile(self, instance, name):
        """(0.281) A component (one of its instances) measured and registered as a tile of the user's own."""
        from .tile_dialog import TileDialog
        shape = bim.tile_shape(self.doc, instance)
        if shape is None:
            return
        dialog = TileDialog(self, name or "", shape[0])

        def apply(tile_name, cover, gauge, weight, stagger):
            try:
                bim.register_tile(self.doc, instance, tile_name, cover, gauge, weight, stagger)
            except ValueError as exc:
                self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
                return False
            self.message(t("info.tile_registered", name=tile_name, c=format_length(cover, decimal_sep(), 3),
                           g=format_length(gauge, decimal_sep(), 3)))
            return True

        dialog.on_apply = apply
        self._tile_dialog = dialog                          # (tests)
        dialog.exec()
        self._tile_dialog = None

    def _tiles_message(self, roof):
        """(0.279) The status bar: a roof's tiles as laid."""
        found = self.doc.ifc.tiles_summary(roof)
        if found:
            spec = self.doc.ifc.tile_spec(found["tile"])
            self.message(t("info.tiles", n=found["tiles"], c=found["caps"], w="{:,.0f}".format(found["weight"]).replace(
                ",", " "), tile=(spec.name_pt if lang() == "pt" else spec.name_en) if spec else "",
                noun=t("props.noun." + (spec.noun if spec else "tiles")).lower()))

    def carpentry_sizes(self, guid):
        """(0.277) A roof's carpentry, its sizes chosen: made again with them (one undo step)."""
        from ..ifc.carpentry import settings_from
        from .carpentry_dialog import CarpentryDialog
        assembly = self.doc.ifc.carpentry_of(guid)
        if assembly is None:
            return
        dialog = CarpentryDialog(self, settings_from(self.doc.ifc._params(assembly).get("Madeiramento")))

        def apply(settings):
            try:
                bim.set_roof_carpentry(self.doc, guid, settings)
            except ValueError as exc:
                self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
                return False
            found = self.doc.ifc.carpentry_summary(guid) or {}
            self.message(t("info.carpentry", n=sum(v[0] for v in found.values()),
                           v="{:.2f}".format(sum(v[2] for v in found.values())).replace(".", decimal_sep())))
            return True

        dialog.on_apply = apply
        self._carpentry_dialog = dialog                     # (tests)
        dialog.exec()
        self._carpentry_dialog = None

    def missing_data(self):
        """(0.273) Collaborate ▸ IFC data missing…: what the elements do not say yet, by class and property; a
        double click selects them; what the program knows filled in at a click."""
        from .missing_data_dialog import MissingDataDialog
        if getattr(self.doc, "loading", False):
            return
        dialog = MissingDataDialog(self, self.doc)
        dialog.on_select = lambda guids: (self.viewport.set_selection(set(guids)), self.zoom_selection())
        dialog.on_fill = lambda: bim.fill_known_data(self.doc)
        self._missing_dialog = dialog                       # (tests)
        dialog.exec()
        self._missing_dialog = None

    def ai_install(self):
        """(0.270) Manage ▸ Connect an AI assistant…: the MCP server put in Claude Desktop, Claude Code or another."""
        from .ai_install_dialog import AiInstallDialog
        dialog = AiInstallDialog(self)
        self._ai_install_dialog = dialog                    # (tests)
        dialog.exec()
        self._ai_install_dialog = None

    def set_ai_link(self, on):
        """(0.269) Manage ▸ Ligação à IA: an MCP server (python -m arqbim.mcp) works on this window's model — this
        computer only, with a key made at random; kept on or off for the next time."""
        from .ai_link import AiLink
        if on:
            if getattr(self, "ai_link", None) is None:
                self.ai_link = AiLink(self)
            if self.ai_link.start():
                self.message(t("info.ai_link_on"))
            else:
                self.message(t("err.ai_link"), warning=True)
        elif getattr(self, "ai_link", None) is not None:
            self.ai_link.stop()
            self.message(t("info.ai_link_off"))
        on = bool(on and getattr(self, "ai_link", None) is not None and self.ai_link.on)
        self.act_ai_link.blockSignals(True)
        self.act_ai_link.setChecked(on)
        self.act_ai_link.blockSignals(False)
        QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue("ia/ligacao", "true" if on else "false")

    def edit_roof_blocks(self, guid, at=None):
        """(0.263) Properties ▸ Edit blocks…: a roof by blocks' blocks in the block editor; applying makes the roof
        again (one undo step). (0.356) at: a point of the roof (a double click on it) — the block under it chosen first
        (the smallest, where blocks overlap)."""
        from .roof_block_editor import RoofBlockEditor, _contains
        if getattr(self.doc, "loading", False) or self.doc.ifc.by_guid(guid) is None or \
                self.doc.ifc.roof_params(guid)["form"] != "blocks":
            return
        roof = self.doc.ifc.by_guid(guid)
        blocks = self.doc.ifc.roof_blocks_world(guid)
        current = 0
        if at is not None:
            under = [k for k, b in enumerate(blocks) if _contains(b, float(at[0]), float(at[1]), grow=b.overhang)]
            if under:
                current = min(under, key=lambda k: blocks[k].width * blocks[k].depth)
        dialog = RoofBlockEditor(self, blocks, self.doc.ifc.roof_params(guid)["eave"], roof.Name or "",
                                 current=current)
        dialog.on_save = lambda blocks: self._save_roof_blocks(guid, blocks)
        self._roof_block_dialog = dialog                    # (tests)
        dialog.exec()
        self._roof_block_dialog = None

    def edit_roof_blocks_3d(self, guid, at=None):
        """(0.385) A roof by blocks' blocks edited in the 3D view (two clicks on it): the tool Blocos da cobertura, the
        block under `at` (a point of the roof) chosen. The block editor window stays in Properties ▸ Edit blocks…."""
        if getattr(self.doc, "loading", False) or self.doc.ifc.by_guid(guid) is None or \
                (self.doc.ifc.roof_params(guid) or {}).get("form") != "blocks":
            return False
        self.viewport.set_selection(set())
        self.tools["roof_blocks"].edit(guid, at)
        self.message(t("info.roof_blocks_edit", name=self.doc.get(guid).name))
        return True

    def _save_roof_blocks(self, guid, blocks):
        try:
            bim.set_roof_blocks(self.doc, guid, blocks, world=True)
        except Exception as exc:                            # (the IFC change was rolled back)
            QtWidgets.QMessageBox.warning(self, t("app.title"), t("err.edit_refused", e=refusal(exc)))
            return False
        self.message(t("info.roof_blocks_saved", roof=self.doc.ifc.by_guid(guid).Name or "", n=len(blocks)))
        return True

    def _save_railing_type(self, rt, old_key):
        try:
            railings = bim.set_railing_type(self.doc, rt, old_key)
        except Exception as exc:                            # (the IFC change was rolled back)
            QtWidgets.QMessageBox.warning(self, t("app.title"), t("err.edit_refused", e=refusal(exc)))
            return False
        self.message(t("info.railing_type_saved", name=rt.label(lang()), n=len(railings)))
        return True

    def _delete_railing_type(self, key):
        try:
            bim.remove_railing_type(self.doc, key)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, t("app.title"), t("err.edit_refused", e=refusal(exc)))
            return False
        return True

    def _save_type_data(self, spec, prop, value):
        """(0.271) A property of a type's IFC data: its elements have it (one undo step)."""
        try:
            elements = bim.set_type_property(self.doc, spec, prop, value)
        except Exception as exc:                            # (the IFC change was rolled back)
            QtWidgets.QMessageBox.warning(self, t("app.title"), t("err.edit_refused", e=refusal(exc)))
            return False
        self.message(t("info.type_data", prop=t("ifcprop." + prop) if i18n_has("ifcprop." + prop) else prop,
                       n=len(elements or ())))
        return True

    def _save_type(self, spec, old):
        """The type editor's Apply: one undo step; the elements of that type follow. The saved type's key."""
        try:
            guid = bim.save_type(self.doc, spec, old)
        except Exception as exc:                            # (the IFC change was rolled back)
            QtWidgets.QMessageBox.warning(self, t("app.title"), t("err.type_failed", e=exc))
            return None
        self._refresh_types()
        known = catalog.OPENING_BY_KEY if spec.kind in ("door", "window") else catalog.BY_KEY
        key = "t:" + guid if "t:" + guid in known else spec.key              # (a catalogue entry keeps its key)
        n = len(project_types.instances(self.doc.ifc, known.get(key) or spec))
        self.message(t("info.type_saved", name=spec.name_pt if lang() == "pt" else spec.name_en, n=n))
        return key

    def edit_materials(self, parent=None, key=None):
        """BIM ▸ Materials… (0.89; 0.468: the column's Materials panel — `key` shown on its Edit tab): name, category,
        how it is seen in view, cut and realistic, its pictures, density, thermal conductivity; new, duplicate, delete
        an unused one. Over another window (the type editor's «Materiais…»: the column out of reach) the same editor
        in a window of its own."""
        from .material_editor import MaterialsDialog
        if parent is not None and parent is not self:
            dialog = MaterialsDialog(parent, self.doc)
            editor = dialog.editor
            editor.on_save, editor.on_delete = self._save_material, self._delete_material
            if key in catalog.MATERIALS:
                editor.select(key)
                editor.tabs.setCurrentIndex(1)
            self._material_dialog = dialog                  # (tests)
            dialog.exec()
            self._material_dialog = None
            return
        panel = self.materials_panel
        self._left_up(panel)
        self.module = "materials"
        self.module_actions["materials"].setChecked(True)
        if key in catalog.MATERIALS:
            panel.editor.select(key)
            panel.editor.tabs.setCurrentIndex(1)

    def pick_material(self, key):
        """(0.468) A material clicked in the Materials panel: the Paint bucket's (the bucket taken up, as SketchUp's)."""
        if getattr(self.tool, "name", "") != "paint":
            self.tools["paint"].material = key or ""
            self.set_tool("paint")
        self.tool.choose(key or "")

    def edit_patterns(self, parent=None, key=None, new=False):
        """Manage ▸ Fill patterns… (0.318): the program's patterns and the project's — made, named, duplicated,
        changed, deleted; each kept in the project's IFC. One undo step each. (0.319) Also from the window that chooses
        a pattern (pattern_picker.EDITOR): new — a new one made at once. Returns the key of the one chosen at the end."""
        from .pattern_editor import PatternEditor
        dialog = PatternEditor(parent or self, select=key)
        dialog.on_save = self._save_pattern
        dialog.on_delete = self._delete_pattern
        self._pattern_dialog = dialog                       # (tests)
        if new:
            dialog.new_pattern()
        dialog.exec()
        self._pattern_dialog = None
        return dialog.current.key if dialog.current is not None else None

    def _save_pattern(self, pattern, old):
        try:
            key = bim.save_pattern(self.doc, pattern, old)
        except Exception as exc:                            # (the IFC change was rolled back)
            QtWidgets.QMessageBox.warning(self, t("app.title"), t("err.pattern_failed", e=exc))
            return None
        self._refresh_types()
        self.message(t("info.pattern_saved", name=pattern.name))
        return key

    def _delete_pattern(self, key):
        if not bim.delete_pattern(self.doc, key):
            return False
        self._refresh_types()
        return True

    def _save_material(self, spec, old):
        try:
            bim.save_material(self.doc, spec, old)
        except Exception as exc:                            # (the IFC change was rolled back)
            QtWidgets.QMessageBox.warning(self, t("app.title"), t("err.material_failed", e=exc))
            return None
        self._refresh_types()
        name = spec.name_pt if lang() == "pt" else spec.name_en
        self.message(t("info.material_saved", name=name))
        return project_types.material_key(name)

    def _delete_material(self, spec):
        if not bim.delete_material(self.doc, spec):
            self.message(t("err.material_in_use"), warning=True)
            return False
        self._refresh_types()
        return True

    def _delete_type(self, spec):
        if not bim.delete_type(self.doc, spec):
            self.message(t("err.type_in_use"), warning=True)
            return False
        self._refresh_types()
        return True

    def _type_where(self, spec):
        """(0.429) «Onde se usa»: the elements of a type chosen and framed. True if there were any."""
        from ..model import project_types
        guids = [g for g in project_types.instances(self.doc.ifc, spec) if self.doc.get(g) is not None]
        if not guids:
            return False
        if self.tool is None or self.tool.name != "select":
            self.set_tool("select")
        self.viewport.set_selection(set(guids))
        self.viewport.zoom_extents(guids)
        name = spec.name_pt if lang() == "pt" else spec.name_en
        self.message(t("info.where_used", n=len(guids), name=name))
        return True

    def _replace_type(self, spec, other):
        """(0.429) A type in use deleted: its elements given `other` first — all one undo step. True if done."""
        from ..model import project_types
        guids = project_types.instances(self.doc.ifc, spec)
        mark = self.doc.undo_mark()
        try:
            for g in guids:
                if self.doc.ifc.by_guid(g) is not None and g in project_types.instances(self.doc.ifc, spec):
                    bim.set_type(self.doc, g, other)          # (a group's copies go with the first: not twice)
            done = bim.delete_type(self.doc, spec)
        except ValueError as exc:
            self.doc.join_since(mark, t("cmd.replace_type"))
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return False
        self.doc.join_since(mark, t("cmd.replace_type"))
        self._refresh_types()
        name = (lambda s: s.name_pt if lang() == "pt" else s.name_en)                  # noqa: E731
        self.message(t("info.type_replaced", n=len(guids), new=name(other), old=name(spec)))
        return done

    def _build_toolbar(self):
        """(0.182) Panel 1, the header: the disciplines' tabs and the global commands; panel 2, the ribbon: the
        active discipline's tools as large buttons; panel 3, the contextual bar. The menus stay, hidden: what
        they had is in the disciplines now. The navigation goes to the status bar (panel 8)."""
        self.menuBar().setVisible(False)
        self.panels_menu = QtWidgets.QMenu(t("rib.panels"), self)      # (filled once the panels are made)
        self.type_lists_menu = QtWidgets.QMenu(t("rib.type_lists"), self)
        for menu in self.type_menus.values():               # (their entries, not addMenu: PySide would make
            self.type_lists_menu.addAction(menu.menuAction())   # them this menu's, and the BIM menu's no more)
        self.header = ribbon.Header(
            self, icons.app_icon(), {d: t("disc." + d) for d in ribbon.DISCIPLINES},
            {d: t("tip.disc." + d) for d in ribbon.DISCIPLINES}, self.set_discipline,
            [("save", t("act.save") + "   (Ctrl+S)", self.act_save.trigger),
             ("undo", t("act.undo") + "   (Ctrl+Z)", self.act_undo.trigger),
             ("redo", t("act.redo") + "   (Ctrl+Y)", self.act_redo.trigger),
             ("sync", t("act.sync"), self.act_sync.trigger),
             ("theme", t("tip.theme_menu"), lambda: self.theme_menu()),          # (0.376: always in sight)
             ("help", t("act.shortcuts") + "   (F1)", self.act_help.trigger)])
        self.header.tabs.tabBarDoubleClicked.connect(lambda _i: self.ribbon_bar.setVisible(
            not self.ribbon_bar.isVisible()))                         # (a double click folds the ribbon away)
        head = QtWidgets.QToolBar(t("rib.header"), self)
        head.setObjectName("header_bar")
        head.setMovable(False)
        head.setFloatable(False)
        head.setStyleSheet(ribbon.header_bar_style())
        head.addWidget(self.header)
        self.header.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.header_bar = head
        self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, head)
        self.addToolBarBreak(QtCore.Qt.ToolBarArea.TopToolBarArea)
        tb = QtWidgets.QToolBar(t("rib.ribbon"), self)
        tb.setObjectName("ribbon")
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setIconSize(QtCore.QSize(30, 30))
        tb.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        tb.setStyleSheet(ribbon.ribbon_style())
        tb.setFixedHeight(ribbon.RIBBON_HEIGHT)        # (0.298: the same for every discipline)
        self.ribbon = ribbon.Ribbon(tb)                 # (0.298: the panels, folded when there is no room)
        tb.addWidget(self.ribbon)
        self.ribbon_bar = self.tools_bar = tb          # (filled by set_discipline: the discipline's tools)
        self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, tb)
        self.addToolBarBreak(QtCore.Qt.ToolBarArea.TopToolBarArea)
        self.discipline = None
        self.ribbon_tab = None                          # (0.298: the discipline shown, or "ctx:walls")
        self.context_tab = None                         # (0.298: the contextual tab there is, "walls", or None)
        saved = QtCore.QSettings("ArqSynth", "ArqSynth BIM").value("disciplina/atual", ribbon.DEFAULT)
        self.set_discipline(saved, remember=False)
        # the navigation (0.78) in the status bar (0.182, panel 8): zooms, the view history, orbit / pan / zoom
        nav = QtWidgets.QToolBar(t("menu.navigate"), self)
        nav.setObjectName("navigation")
        nav.setMovable(False)
        nav.setIconSize(QtCore.QSize(20, 20))
        nav.setStyleSheet("QToolBar#navigation { border: none; background: transparent; spacing: 1px; }")
        nav.addActions([self.act_zoom_all, self.tool_actions["zoom_window"], self.act_zoom_selection,
                        self.act_view_back, self.act_view_forward])
        nav.addSeparator()
        nav.addActions([self.tool_actions["orbit"], self.tool_actions["pan"], self.tool_actions["zoom"]])
        nav.addSeparator()
        nav.addActions([self.tool_actions["position_camera"], self.tool_actions["look_around"],
                        self.tool_actions["walk"]])
        self.navigation_bar = nav
        self.statusBar().addPermanentWidget(nav)
        self._build_footer()
        # the contextual bar (0.85; the selection bar of 0.75 is its Select part), over the view
        bar = context_bar.ContextBar(t("menu.context"), self)
        bar.setObjectName("context")
        bar.on_option = self._context_option
        bar.on_done = lambda: self.canvas.setFocus()
        bar.on_invalid = lambda text: self.message(t("err.bad_value", t=text), warning=True)     # (0.183)
        self.selection_bar = self.context_bar = bar
        self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, bar)

    # ------------------------------------------------------------ the footer's view controls (0.186, panel 8)

    ORIENTATIONS = (("top", "F2"), ("front", "F3"), ("back", ""), ("left", ""), ("right", ""), None,
                    ("iso", "F8"), ("iso_sw", ""), ("iso_ne", ""), ("iso_nw", ""))

    def _build_footer(self):
        """(0.186) Panel 8 after the navigation: the orientation (the starting view, the sides, the isometrics),
        the view shown's graphic style, its scale, the ground grid, and the unit lengths are shown and typed in.
        Each changes the view as its Properties do (one undo step); the style and the grid are a 3D view's, the
        scale a drawing's (a plan, a section, an elevation) — its template's, if it has one."""
        bar = QtWidgets.QToolBar(t("foot.title"), self)
        bar.setObjectName("footer_view")
        bar.setMovable(False)
        bar.setIconSize(QtCore.QSize(20, 20))
        bar.setStyleSheet("QToolBar#footer_view { border: none; background: transparent; spacing: 1px; }"
                          " QToolButton { padding: 0 3px; }")
        self.footer_bar = bar
        self.orientation_button = self._footer_button(bar, "orientation", t("tip.foot.orientation"),
                                                      icon=icons.orientation_icon())
        menu = self.orientation_button.menu()
        menu.addAction(t("cube.menu.home"), self.go_home_view)
        menu.addSeparator()
        for entry in self.ORIENTATIONS:
            if entry is None:
                menu.addSeparator()
                continue
            kind, key = entry
            menu.addAction(t("foot.view." + kind) + ("\t" + key if key else ""), lambda k=kind: self.set_view(k))
        self._style_icons = {}
        self.style_button = self._footer_button(bar, "style", t("tip.foot.style_3d"))
        self.style_button.menu().aboutToShow.connect(self._fill_style_menu)
        self._fill_style_menu()
        self.scale_button = self._footer_button(bar, "scale", t("tip.foot.scale"), text="1:100")
        self.scale_button.menu().aboutToShow.connect(self._fill_scale_menu)
        # (0.445) the drawing's detail level beside its scale, as in Revit's view control bar: Coarse, Medium, Fine
        self._detail_icons = {level: icons.detail_level_icon(level) for level in templates_model.DETAILS}
        self.detail_button = self._footer_button(bar, "detail", t("tip.foot.detail_3d"),
                                                 icon=self._detail_icons["fine"])
        group = QtGui.QActionGroup(self.detail_button)
        for level in templates_model.DETAILS:
            act = self.detail_button.menu().addAction(self._detail_icons[level], t("foot.detail." + level),
                                                      lambda v=level: self._footer_edit("view_detail", v))
            act.setData(level)
            act.setCheckable(True)
            group.addAction(act)
        self.act_ground_grid = QtGui.QAction(icons.ground_grid_icon(), t("props.view_grid"), self)
        self.act_ground_grid.setCheckable(True)
        self.act_ground_grid.triggered.connect(lambda on: self._footer_edit("view_grid", bool(on)))
        bar.addAction(self.act_ground_grid)
        self.units_button = self._footer_button(bar, "units", t("tip.foot.units"), text=units_core.display_unit())
        group = QtGui.QActionGroup(self.units_button)
        for unit in units_core.LENGTH_UNITS:
            act = self.units_button.menu().addAction(t("foot.unit." + unit), lambda u=unit: self.set_units(u))
            act.setData(unit)
            act.setCheckable(True)
            group.addAction(act)
        saved = QtCore.QSettings("ArqSynth", "ArqSynth BIM").value("unidades/comprimento", "m")
        self.set_units(saved if saved in units_core.LENGTH_UNITS else "m", remember=False)
        self.statusBar().addPermanentWidget(bar)
        if str(QtCore.QSettings("ArqSynth", "ArqSynth BIM").value("ia/ligacao", "false")).lower() == "true":
            QtCore.QTimer.singleShot(0, lambda: self.set_ai_link(True))      # (0.269: on, as it was left)

    @staticmethod
    def _footer_button(bar, name, tip, icon=None, text=None):
        """A footer button opening its own menu (kept with it: the footer is made once)."""
        button = QtWidgets.QToolButton(bar)
        button.setObjectName("footer_" + name)
        button.setAutoRaise(True)
        button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        if icon is not None:
            button.setIcon(icon)
        if text is not None:
            button.setText(text)
            button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setToolTip(tip)
        button.setMenu(QtWidgets.QMenu(button))
        bar.addWidget(button)
        return button

    def _style_icon(self, style):
        """A view style's icon (a key: the style found in the project)."""
        found = self.doc.view_style(style) if isinstance(style, str) else style
        key = (found.faces, found.shadows)
        if key not in self._style_icons:
            self._style_icons[key] = icons.view_style_icon(found)
        return self._style_icons[key]

    def _style_label(self, style):
        return view_styles_model.label(self.doc.view_style(style) if isinstance(style, str) else style, t)

    def _fill_style_menu(self):
        """(0.315) The footer's view styles: the program's, the project's, the one of the 3D view ticked; and the window
        that makes them."""
        menu = self.style_button.menu()
        menu.clear()
        view = self._footer_view() if hasattr(self, "footer_bar") else None
        current = self.doc.view_settings(view).style if view is not None and view[0] == "3d" else None
        group = QtGui.QActionGroup(menu)
        builtin = list(view_styles_model.BUILTIN.values())
        for k, style in enumerate(view_styles_model.all_styles(self.doc.view_styles)):
            if k == len(builtin):
                menu.addSeparator()
            act = menu.addAction(self._style_icon(style), self._style_label(style),
                                 lambda s=style.uid: self._footer_edit("view_style", s))
            act.setData(style.uid)
            act.setCheckable(True)
            act.setChecked(style.uid == current)
            group.addAction(act)
        menu.addSeparator()
        menu.addAction(t("act.view_styles"), self.edit_view_styles)

    def go_home_view(self):
        """The footer's (and the cube's) starting view, in the 3D view shown last."""
        self.views.open(self._live_3d())
        self.viewport.go_home()

    def _footer_view(self):
        """The view the footer changes: the one shown (None while a sheet is)."""
        if not hasattr(self, "views") or self.sheet_shown():
            return None
        return self._view_key()

    def _footer_edit(self, action, value):
        view = self._footer_view()
        if view is None:
            return
        self._edit_view(action, view, value)
        self._sync_footer()

    def _fill_scale_menu(self):
        """The scales a drawing can have on the sheets (its Properties' list), the current one ticked."""
        menu = self.scale_button.menu()
        menu.clear()
        view = self._footer_view()
        current = self.doc.view_settings(view).scale if view is not None else None
        scales = list(sheets_model.SCALES) + ([current] if current and current not in sheets_model.SCALES else [])
        for text, value in [(t("sheet.scale_auto"), None)] + [("1:{}".format(n), n) for n in scales]:
            act = menu.addAction(text, lambda v=value: self._footer_edit("view_scale", v))
            act.setCheckable(True)
            act.setChecked(value == current)

    def _fill_storey_menu(self):
        """The footer's storey (0.186): the storeys, the highest first, the active one ticked; and the panel."""
        menu = self.storey_menu
        menu.clear()
        for guid, name, z in reversed(self.doc.storeys()):
            act = menu.addAction("{}   {}".format(name, storeys.level_text(z)),
                                 lambda g=guid: self.set_active_storey(g))
            act.setCheckable(True)
            act.setChecked(guid == self.doc.active_storey)
        menu.addSeparator()
        menu.addAction(t("mod.storeys") + "…", lambda: self.set_module("storeys"))

    def _sync_footer(self):
        """The footer's controls as the view shown is: a 3D view's style and ground grid, a drawing's scale (not
        changed here when its template sets it), the units."""
        if not hasattr(self, "footer_bar"):
            return
        view = self._footer_view()
        s = self.doc.view_settings(view) if view is not None else None
        is_3d = view is not None and view[0] == "3d"
        style = s.style if is_3d else "shaded"
        self.style_button.setEnabled(is_3d)
        self.style_button.setIcon(self._style_icon(style))
        self.style_button.setToolTip(t("tip.foot.style", style=self._style_label(style)) if is_3d
                                     else t("tip.foot.style_3d"))
        for act in self.style_button.menu().actions():
            if act.isCheckable():
                act.setChecked(act.data() == style)
        self.act_ground_grid.setEnabled(is_3d)
        self.act_ground_grid.setChecked(bool(s.grid) if is_3d else False)
        self.act_ground_grid.setToolTip(t("props.view_grid") if is_3d else t("tip.foot.grid_3d"))
        drawing = view is not None and not is_3d
        by_template = drawing and self.doc.template_of(view) is not None
        self.scale_button.setText(("1:{}".format(s.scale) if s.scale else t("sheet.scale_auto")) if drawing else "1:—")
        self.scale_button.setEnabled(drawing and not by_template)
        self.scale_button.setToolTip(t("tip.foot.scale_template") if by_template else t("tip.foot.scale") if drawing
                                     else t("tip.foot.scale_3d"))
        level = (s.detail or "fine") if drawing else "fine"                    # (0.445)
        self.detail_button.setIcon(self._detail_icons.get(level, self._detail_icons["fine"]))
        self.detail_button.setEnabled(drawing and not by_template)
        self.detail_button.setToolTip(t("tip.foot.detail_template") if by_template else
                                      t("tip.foot.detail", level=t("foot.detail." + level)) if drawing
                                      else t("tip.foot.detail_3d"))
        for act in self.detail_button.menu().actions():
            act.setChecked(act.data() == level)
        self.orientation_button.setEnabled(not self.doc.loading)

    def set_units(self, unit, remember=True):
        """(0.186) The footer's Units: lengths shown in m, cm or mm — the Measurements box, the temporary
        dimensions, the Properties, the bars — and a number typed without a unit read in it. Kept for the next
        session (the user's, not the project's: the drawings' dimensions have their style, the schedules and the
        storeys' levels stay in metres)."""
        units_core.set_display_unit(unit)
        unit = units_core.display_unit()
        self.units_button.setText(unit)
        for act in self.units_button.menu().actions():
            act.setChecked(act.data() == unit)
        if not remember:
            return
        QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue("unidades/comprimento", unit)
        self._refresh_properties()
        self._refresh_context_bar()
        self._refresh_vcb()
        self.message(t("info.units", unit=t("foot.unit." + unit)))

    # ------------------------------------------------------------ the compact bar and its modules (0.184)

    # (0.468, the owner: «A aba materiais eu quero que fique antes da aba biblioteca»)
    MODULES = ("project", "storeys", "materials", "library", "sheets", "rooms", "quantities", "rules",
               "presentation", "graph", "settings")  # (0.480, the owner's mark: the ArqSynth Presentation after the
    #                                                   rules; 0.540: the Visual Graph, its own window)
    LEFT_MODULES = {"project": "tree_panel", "library": "library_panel", "sheets": "tree_panel",    # (0.466: its own)
                    "storeys": "storeys_panel", "rules": "rules_panel", "materials": "materials_panel",   # (0.468)
                    "rooms": "program_panel",                   # (0.475: the programme's manager, no longer a table)
                    "quantities": "tables_panel",               # (0.477: the tables' tree, each opened in its tab)
                    "graph": "operators_panel"}                 # (0.541: the operators kept; the editor from it)

    def _build_modules(self):
        """(0.184) Panel 4, the compact bar at the far left — icons only — and panel 5 beside it: the Project
        navigator, the storeys and the graphic rules, stacked on the left (the navigator first). A module of the
        bar brings its panel up (the library and the sheets: the navigator open at them); the quantities and the
        rooms are the schedules panel's, the materials their window, the settings a menu. A click on the module in
        view folds the left panels away; another brings them back."""
        left = QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
        self.left_panels = [self.tree_panel, self.storeys_panel, self.rules_panel, self.library_panel,
                            self.materials_panel]
        # (0.461, the owner: «remover essas abas atuais») one left panel in view at a time — no tabs at their foot
        # (those are the navigator's own now: what its tree shows); the module bar chooses — and a panel brought up
        # (raise_) shows alone
        for p in self.left_panels:
            self.removeDockWidget(p)
            self.addDockWidget(left, p)
            p.setVisible(p is self.tree_panel)
            p.raise_ = lambda p=p: self._left_up(p)
        # (0.357, hidden until asked for; 0.475, the owner: «A aba ambiente quero que funcione no painel lateral» — the
        # «Ambientes» module's panel, one of the left ones: the programme's manager)
        self.program_panel = room_program_panel.ProgramPanel(self)
        self.addDockWidget(left, self.program_panel)
        self.program_panel.hide()
        self.left_panels.append(self.program_panel)
        self.program_panel.raise_ = lambda p=self.program_panel: self._left_up(p)
        self.program_panel.on_import = lambda: self.import_room_program()
        self.program_panel.on_clear = lambda: self.clear_room_program()
        self.program_panel.on_change = self.change_room_program
        self.program_panel.on_place = self.start_room_need
        self.program_panel.on_storey = lambda guid: self.set_active_storey(guid)
        self.program_panel.on_ai = lambda: self.copy_program_prompt()
        self.program_panel.visibilityChanged.connect(lambda shown: self._refresh_program() if shown else None)
        # (0.477, the owner: «A aba de tabelas também deve ser gerenciada pelo painel lateral») the «Quantidades»
        # module's panel: the tree of every table, each opened in its tab over the canvas
        from . import tables_panel as tables_ui
        self.tables_panel = tables_ui.TablesPanel(self)
        self.addDockWidget(left, self.tables_panel)
        self.tables_panel.hide()
        self.left_panels.append(self.tables_panel)
        self.tables_panel.raise_ = lambda p=self.tables_panel: self._left_up(p)
        tp = self.tables_panel
        tp.on_open, tp.on_new, tp.on_properties = self.open_table, self.new_table, self.table_properties
        tp.on_duplicate, tp.on_delete, tp.on_export = self.duplicate_table, self.delete_table, self.export_table
        tp.on_put = lambda ref: self.sheet_action("put", None, "schedule", ref)
        tp.on_insert = lambda kind, key: self.schedules_panel.insert(kind, key) if self.table_shown() else None
        tp.on_make_own = lambda: self.schedules_panel.make_own() if self.table_shown() else None      # (0.478)
        tp.visibilityChanged.connect(lambda shown: self._refresh_tables_panel() if shown else None)
        # (0.541, the owner: «O botão no BIM deve abrir apenas o painel lateral com os operadores guardados») the
        # «Gráfico Visual» module's panel: the library of operators, with Aplicar / Criar novo / Editar
        from . import operators_panel as operators_ui
        self.operators_panel = operators_ui.OperatorsPanel(self)
        self.addDockWidget(left, self.operators_panel)
        self.operators_panel.hide()
        self.left_panels.append(self.operators_panel)
        self.operators_panel.raise_ = lambda p=self.operators_panel: self._left_up(p)
        op = self.operators_panel
        op.target = lambda: len(self.chosen_walls())
        op.on_apply, op.on_new, op.on_edit = self.apply_operator, self.new_operator, self.edit_operator
        op.kept = lambda: len(self.operator_finishes())                 # (0.543) panels that keep their operator
        op.on_update, op.on_edit_wall = self.update_operators, self.edit_wall_operator
        op.on_remove = self.remove_operators                            # (0.551)
        self.viewport.selection_listeners.append(
            lambda _ids: op.refresh_target() if op.isVisible() else None)
        # (0.479) the ArqSynth Presentation tab: its two columns and its commands over the 3D view, hidden until the
        # tab is chosen (ui/presentation_mode.py). (0.480, the owner: «não quero essa divisão na coluna») it took the
        # place of the 0.363 Presentation panel, which split the left column under the navigator
        from . import presentation_mode
        self.presentation_mode = presentation_mode.PresentationMode(self)
        self.viewport.selection_listeners.append(lambda ids: self.presentation_mode.selection_changed(ids))
        for w in (self.canvas, getattr(self.canvas, "_subwidget", None)):        # (its names dropped on the view)
            if w is not None:
                w.setAcceptDrops(True)
        self.tree_panel.raise_()
        self.resizeDocks([self.tree_panel], [270], QtCore.Qt.Orientation.Horizontal)
        bar = QtWidgets.QToolBar(t("mod.title"), self)
        bar.setObjectName("modules")
        bar.setMovable(False)
        bar.setFloatable(False)
        bar.setIconSize(QtCore.QSize(22, 22))
        bar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        bar.setStyleSheet(self._modules_style())
        group = QtGui.QActionGroup(self)
        group.setExclusionPolicy(QtGui.QActionGroup.ExclusionPolicy.ExclusiveOptional)
        self.module_actions = {}
        for name in self.MODULES:
            act = QtGui.QAction(icons.module_icon(name), t("mod." + name), self)
            act.setToolTip("{}\n{}".format(t("mod." + name), t("tip.mod." + name)))
            if name in self.LEFT_MODULES or name == "presentation":
                act.setCheckable(True)
                group.addAction(act)
            act.triggered.connect(lambda _=False, n=name: self.set_module(n))
            if name == "settings":
                spacer = QtWidgets.QWidget()
                spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
                bar.addWidget(spacer)                       # (the settings at the bottom)
            bar.addAction(act)
            self.module_actions[name] = act
        self.addToolBar(QtCore.Qt.ToolBarArea.LeftToolBarArea, bar)
        self.module_bar = bar
        self.module = "project"
        self.module_actions["project"].setChecked(True)

    @staticmethod
    def _modules_style():
        """The modules' bar (0.184; 0.338: the theme's colours): the module in view lit, a stripe on its left."""
        c = theme.C
        return ("QToolBar#modules { background: %s; border: none; border-right: 1px solid %s;"
                " padding: 4px 3px; spacing: 4px; }"
                "QToolBar#modules QToolButton { padding: 5px; border-radius: 5px; }"
                "QToolBar#modules QToolButton:hover { background: %s; }"
                "QToolBar#modules QToolButton:checked { background: %s; border-left: 3px solid %s; }"
                % (c["panel"], c["line"], c["panel_hover"], c["select_soft"], c["accent"]))

    @staticmethod
    def _share_style():
        """(0.338) The footer's «shared» label: green, the theme's."""
        return "QLabel { padding: 0 8px; color: %s; font-weight: 600; }" % theme.C["good"]

    @staticmethod
    def _vcb_style():
        """(0.338) The footer's measurements box: a field's colours, the theme's."""
        return ("QLabel { background: %s; color: %s; padding: 2px 6px; font-weight: 600; }"
                % (theme.C["input"], theme.C["text"]))

    def _left_up(self, panel):
        """(0.461) A left panel in view alone (the others hidden: no tabs at their foot), the module bar following.
        (0.479) The ArqSynth Presentation in front: put away first (0.481: its tab closed — the BIM's columns back)."""
        if self.presentation_shown():
            self.close_presentation()
        for p in self.left_panels:
            if p is not panel and p.isVisible():
                p.hide()
        if not panel.isVisible():
            panel.show()
        QtWidgets.QDockWidget.raise_(panel)
        names = {"tree_panel": "project", "storeys_panel": "storeys", "rules_panel": "rules", "library_panel": "library",
                 "materials_panel": "materials", "program_panel": "rooms", "tables_panel": "quantities",
                 "operators_panel": "graph"}
        name = names.get(next((a for a in names if getattr(self, a, None) is panel), ""))
        if name and getattr(self, "module_actions", None) and \
                not (name == "project" and self.module in ("library", "sheets")):
            self.module = name
            self.module_actions[name].setChecked(True)

    def _presentation_module(self, on):
        """(0.480) The left bar's ArqSynth Presentation icon lit while its interface is in front; after it, the module
        that was lit before."""
        acts = getattr(self, "module_actions", None)
        if not acts or "presentation" not in acts:
            return
        if on:
            if self.module != "presentation":
                self._module_before = self.module
            self.module = "presentation"
            acts["presentation"].setChecked(True)
        elif self.module == "presentation":
            before = getattr(self, "_module_before", None)
            self.module = before
            if before in acts and acts[before].isCheckable():
                acts[before].setChecked(True)
            else:
                acts["presentation"].setChecked(False)

    def chosen_walls(self):
        """(0.541) The walls chosen in the model (their GlobalIds), in a stable order."""
        from ..core.graph import operators
        out = []
        for guid in sorted(self.viewport.selection, key=str):
            wall = operators.host_wall(self.doc, guid)       # (0.543: a wall's panel chosen stands for its wall)
            if wall and wall not in out:
                out.append(wall)
        return out

    def operator_finishes(self):
        """(0.543) The panels that keep their operator among what is chosen (themselves, or on the walls chosen)."""
        from ..core.graph import operators
        if not self.viewport.selection:
            return []
        return operators.finishes_of(self.doc, sorted(self.viewport.selection, key=str))

    def update_operators(self):
        """(0.543) «Atualizar na parede»: each such panel worked out again on its wall as it is now."""
        from ..core.graph import operators
        done, problems = [], []
        for guid in self.operator_finishes():
            try:
                done.append(operators.update(self.doc, guid))
            except ValueError as e:
                problems.append(str(e))
        if problems:
            QtWidgets.QMessageBox.warning(self, "Operadores", "Não atualizado:\n" + "\n".join(sorted(set(problems))))
        if done:
            self.statusBar().showMessage("{} painel(éis) atualizado(s).".format(len(done)), 6000)
        return done

    def edit_wall_operator(self):
        """(0.543) «Editar o da parede»: the operator the chosen wall's panel keeps, in the editor on that face."""
        from ..core.graph import operators
        found = self.operator_finishes()
        if not found:
            return None
        kept = operators.operator_of(self.doc, found[0])
        exposed = []
        if kept["slug"]:
            try:
                exposed = operators.exposed_of(kept["slug"])[1]
            except ValueError:                               # (not in this computer's library: edited all the same)
                kept["slug"] = ""
        return self.show_visual_graph(kept["graph"], slug=kept["slug"] or None, name=kept["name"], side=kept["side"],
                                      wall=kept["wall"], exposed=exposed, cladding=found[0])

    def face_in_view(self, wall):
        """(0.541) "frente" | "trás": the face of the wall turned to the eye in the view (seen from above, or the
        view not telling: the front)."""
        try:
            from ..core.graph.sketch_host import is_sketch_surface
            if is_sketch_surface(self.doc, wall) or self.doc.ifc.kind_of(wall) in ("ceiling", "slab", "plane_panel"):
                return "frente"                                       # (0.549, 0.553) the one face
            if self.doc.ifc.kind_of(wall) == "param_surface":        # (0.551) the side its middle turns to the eye
                from ..core import param_surface as ps
                on = ps.Surface(self.doc.ifc.surface_definition(wall))
                j, i = on.rows.shape[0] // 2, on.rows.shape[1] // 2
                m = self.doc.ifc._placement_si(self.doc.ifc.by_guid(wall))
                point = (m @ np.append(on.rows[j, i], 1.0))[:3]
                normal = m[:3, :3] @ ps.grid_normals(on.rows, on.close_u)[j, i]
                eye = np.asarray(self.viewport.camera_position(), dtype=float)
                return "frente" if float((eye - point) @ normal) >= 0 else "trás"
            if self.doc.ifc.kind_of(wall) == "curved_wall":  # (0.548) inside its circle: its inner face ("frente")
                centre, radius, _s, _sw, _h, _t = self.doc.ifc.curved_wall_params(wall)
                eye = np.asarray(self.viewport.camera_position(), dtype=float)
                return "frente" if np.linalg.norm((eye - centre)[:2]) < radius else "trás"
            frame = self.doc.ifc.element_frame(wall)
            across = frame.matrix[:3, 1] / np.linalg.norm(frame.matrix[:3, 1])
            middle = frame.to_world((frame.x0 + frame.length / 2.0, (frame.y0 + frame.y1) / 2.0,
                                     (frame.z0 + frame.z1) / 2.0))
            eye = np.asarray(self.viewport.camera_position(), dtype=float) - middle
            d = float(eye @ across) / max(float(np.linalg.norm(eye)), 1e-9)
        except Exception:  # (no camera yet, a wall gone)
            return "frente"
        return "trás" if d < -0.05 else "frente"

    def show_visual_graph(self, graph=None, slug=None, name="", side=None, wall=None, exposed=(), cladding=None):
        """(0.540) The Visual Graph's window, in front. (0.541) Opened from the «Operadores» panel: on the face of
        the wall chosen in the model (none: the example face), with the operator being edited (None: a new one)."""
        from . import visual_graph
        if wall is None:
            walls = self.chosen_walls()
            wall = walls[0] if walls else ""
        side = side or (self.face_in_view(wall) if wall else "frente")
        old = getattr(self, "graph_window", None)
        if old is not None:
            old.close()
        win = self.graph_window = visual_graph.GraphWindow(self, graph, slug=slug, name=name, wall=wall, side=side,
                                                           exposed=exposed, cladding=cladding)
        win.show()
        win.raise_()
        win.activateWindow()
        return win

    def new_operator(self, side=None):
        """«Criar novo»: the editor on the wall's face chosen, with a first graph to change."""
        return self.show_visual_graph(side=side)

    def edit_operator(self, slug, side=None):
        from ..core.graph import operators
        from ..core.graph.graph import GraphError
        try:
            name, _about, graph = operators.load(slug)
            exposed = operators.exposed_of(slug)[1]
        except GraphError as e:
            QtWidgets.QMessageBox.warning(self, "Operadores", str(e))
            return None
        return self.show_visual_graph(graph, slug=slug, name=name, side=side, exposed=exposed)

    def apply_operator(self, slug, side=None, values=None):
        """«Aplicar»: the operator on the face (`side`; None: the one in view) of every wall chosen. Returns the
        finishes made."""
        from ..core.graph import operators
        from ..model.bim import CEILING_DROP
        chosen = self.chosen_walls()
        drop = None
        if any(isinstance(g, str) and self.doc.ifc.kind_of(g) == "slab" for g in chosen):   # (0.551) how far under
            drop = getattr(self, "_ceiling_drop", CEILING_DROP)
            if not getattr(self, "_quiet_ceiling_drop", False):
                drop, ok = QtWidgets.QInputDialog.getDouble(
                    self, "Teto falso perfurado", "Distância do teto à face de baixo da laje (m):", drop, 0.0, 5.0,
                    2)
                if not ok:
                    return []
            self._ceiling_drop = drop
        made, problems = [], []
        for wall in chosen:
            try:
                made += operators.apply_to(self.doc, slug, wall, side or self.face_in_view(wall), values, drop=drop)
            except ValueError as e:                              # (GraphError too)
                problems.append(str(e))
        if problems:
            QtWidgets.QMessageBox.warning(self, "Operadores", "Não aplicado:\n" + "\n".join(sorted(set(problems))))
        if made:
            self.statusBar().showMessage("{} painel(éis) perfurado(s) aplicado(s).".format(len(made)), 6000)
            self.operators_panel.refresh_target()            # (0.548: «Atualizar…» lit at once)
        return made

    def remove_operators(self):
        """(0.551) «Tirar o aplicado»: the chosen panels' operators taken off (a wall's panel deleted; a ceiling, a
        surface plain again)."""
        from ..core.graph import operators
        done, problems = [], []
        for guid in self.operator_finishes():
            try:
                done.append(operators.remove(self.doc, guid))
            except ValueError as e:
                problems.append(str(e))
        if problems:
            QtWidgets.QMessageBox.warning(self, "Operadores", "Não tirado:\n" + "\n".join(sorted(set(problems))))
        if done:
            self.statusBar().showMessage("{} tirado(s). Ctrl+Z repõe.".format(len(done)), 6000)
            self.operators_panel.refresh_target()
        return done

    def set_module(self, name):
        """(0.184) A module of the compact bar: its panel up in panel 5 — or, the module in view clicked again,
        the left panels folded away."""
        attr = self.LEFT_MODULES.get(name)
        presenting = attr is not None and self.presentation_shown()
        if presenting:                                         # (0.479: the BIM's columns back, its panel up;
            self.close_presentation()                          #  0.481: the Presentation's tab closed)
        if attr is not None:
            panel = getattr(self, attr)
            in_view = panel.isVisible() and not panel.visibleRegion().isEmpty()
            if name == self.module and in_view and not presenting:
                for p in self.left_panels:
                    p.hide()
                self.module_actions[name].setChecked(False)
                self.module = None
                return
            self._left_up(panel)
            if name == "sheets":
                self.tree_panel.set_scope("sheets")         # (0.470: the navigator's own Folhas tab)
                self.tree_panel.focus(("views", "sheets"))
            self.module = name
            self.module_actions[name].setChecked(True)
        elif name == "presentation":                        # (0.480) the ArqSynth Presentation's interface — again:
            if self.presentation_shown():                   # (0.481) its tab closed, the BIM's view it came from
                self.close_presentation()
            else:
                self.show_presentation_tab()
        elif name == "settings":
            menu = QtWidgets.QMenu(self)
            menu.addActions([self.act_mouse_sketchup, self.act_mouse_revit])
            menu.addSeparator()
            menu.addActions([self.act_theme_light, self.act_theme_dark, self.act_canvas_dark])   # (0.338, 0.341)
            palettes = menu.addMenu(t("menu.study_palettes"))  # (0.376: the study's palettes here too)
            palettes.addActions([self.act_theme_bege, self.act_theme_pedra,
                                 self.act_theme_escuro, self.act_theme_grafite, self.act_theme_revit])
            palettes.addSeparator()
            palettes.addAction(self.act_theme_studio)
            menu.addSeparator()
            menu.addAction(self.panels_menu.menuAction())     # (its entry: not addMenu — see _build_toolbar)
            button = self.module_bar.widgetForAction(self.module_actions["settings"])
            # (0.377) up from the button (its foot on the button's): at the window's foot, downwards it went under the
            # Windows taskbar — in WSLg Qt does not know where that is, and does not turn the menu round
            self._settings_menu = menu                       # (tests)
            menus.keep_up(palettes)
            menus.keep_up(self.panels_menu)                  # (their lists: up too, not under the taskbar)
            menu.exec(menus.above(menu, button) if button is not None
                      else menus.menu_point(menu, QtGui.QCursor.pos()))
            menu.deleteLater()

    def _context_items(self):
        """What goes on the contextual bar now: the tool's settings, or (Select) the selection's."""
        tool = self.tool
        if tool is None:
            return []
        if self.presentation_shown() and tool.name == "select":    # (0.479) the Presentation tab's commands
            return self.presentation_mode.context_items()
        if self.table_shown():                      # (0.477) a table: its commands (Propriedades…, Exportar…)
            return self.schedules_panel.context_items()
        if self.sheet_shown():                      # (0.472, the owner) a sheet: its commands, as a tool's
            return self.sheet_window.context_items()
        if tool.name != "select":
            title = t(tool.title) if tool.title else \
                t("tool." + tool.name) if tool.name in self.tool_actions else t("ctx.placing")
            icon = self.tool_actions[tool.name].icon() if tool.name in self.tool_actions else None
            items = [("title", title, icon)] + [("option", o) for o in self._tool_options()]
            if isinstance(getattr(tool, "spec", None), (catalog.TypeSpec, catalog.OpeningSpec)) or tool.name == "railing":
                items += [("icon_action", self.act_tool_type)]          # (0.183) its type, in the type editor
            if tool.keys_help:                          # (its placement keys, 0.86)
                items += [("separator",), ("hint", t(tool.keys_help))]
            return items
        items = [("title", t("menu.selection") + ":", self.tool_actions["select"].icon()),
                 ("action", self.act_drag_box), ("action", self.act_drag_lasso),
                 ("icon_action", self.act_drag_elements),                       # (0.427: its icon — the bar's room)
                 ("separator",), ("action", self.act_pick_polygon), ("action", self.act_pick_fence), ("separator",),
                 ("action", self.act_filter_selection), ("action", self.act_select_by), ("action", self.act_selectable),
                 ("separator",), ("action", self.act_select_all), ("action", self.act_select_invert)]
        ids, axes = set(self.viewport.selection), set(self.viewport.selected_axes)
        if ids or axes:
            counts = self._categories(ids, axes)
            what = ", ".join("{} {}".format(n, selection_dialogs.category_text(c))
                             for c, n in sorted(counts.items(), key=lambda kv: -kv[1]))
            items += [("separator",), ("text", t("ctx.selected", n=sum(counts.values()), what=what))]
            items += [("action", a) for a in self._selection_actions(counts)]
        elif self.viewport.selected_dims:                    # (0.402) a dimension string: as Revit's «Modificar | Cotas»
            dims = [d for d in self.viewport.selected_dims if d in self.doc.dimensions]
            self.act_dim_eq.setText(t("act.dim_eq_off" if dims and all(d.eq for d in dims) else "act.dim_eq"))
            items += [("separator",), ("text", t("ctx.dims_selected", n=len(dims))),
                      ("action", self.act_dim_eq), ("action", self.act_dim_text), ("action", self.act_dim_add)]
        return items

    def _selection_actions(self, counts):
        """The buttons for what is selected ({category: how many}), as the addon's header: the same type, the
        view framed on it, a section box round it — and those for its kind (walls: their dimensions)."""
        acts = []
        if "grid" in counts:                                # (0.92) axes selected: columns where they cross
            acts.append(self.act_columns_on_grid)
        if "IfcColumn" in counts:                           # (0.93) columns selected: their footings
            acts.append(self.act_footings_under)
        if counts.get("IfcColumn", 0) >= 2:                 # (0.94) 2+ columns: beams between them
            acts.append(self.act_beams_between)
        if "IfcBeam" in counts:                             # (0.95) beams: the walls under them
            acts.append(self.act_walls_under_beams)
        if counts.get("IfcBeam", 0) >= 3:                   # (0.96) 3+ beams: slabs in their bays
            acts += [self.act_slabs_in_bays, self.act_beam_system]
        if sum(counts.values()) == 2 and len(self._steel_pieces()) == 2:      # (0.496) two steel pieces: a mitre
            acts += [self.act_steel_mitre, self.act_knee_plate]                # (0.513) …or bolted
        if "IfcColumn" in counts and any(isinstance(g, str) and self.doc.ifc.steel_section(g) is not None
                                         for g in list(self.viewport.selection)[:20]):     # (0.497) steel columns
            acts.append(self.act_base_plate)
        if any(isinstance(g, str) and self.doc.ifc.kind_of(g) in ("beam", "steel_member")
               and self.doc.ifc.steel_section(g) is not None for g in list(self.viewport.selection)[:20]):
            acts += [self.act_end_plate, self.act_fin_plate]          # (0.498) steel beams: their ends' connections
        if "IfcMember" in counts and any(isinstance(g, str) and self.doc.ifc.kind_of(g) == "steel_member"
                                         and (self.doc.ifc.steel_section(g) or "")[:1] == "L"
                                         for g in list(self.viewport.selection)[:20]):
            acts.append(self.act_gusset)                              # (0.503) braces of angles: their gussets
        if "IfcMember" in counts and any(isinstance(g, str) and self.doc.ifc.kind_of(g) == "steel_member"
                                         and self.doc.ifc.steel_member_params(g)["function"] == "purlin"
                                         for g in list(self.viewport.selection)[:20]):
            acts.append(self.act_purlin_cleat)                        # (0.504) purlins: their cleats
        if sum(counts.values()) == 1 and (counts.get("IfcSlab", 0) == 1 or (     # (0.100) one slab: its outline
                counts.get("IfcCovering", 0) == 1 and any(          # (0.410) a floor finish's, a ceiling's
                    isinstance(i, str) and self.doc.ifc.kind_of(i) in ("flooring", "ceiling")
                    for i in list(self.viewport.selection)[:2]))):
            acts.append(self.act_edit_outline)
        if counts.get("IfcGeographicElement", 0) == 1:      # (0.204) a terrain: its platforms
            acts.append(self.act_edit_platform)
        if counts.get("IfcSlab", 0) + counts.get("IfcRoof", 0) == 1 and ("IfcWall" in counts or "IfcColumn" in counts):
            acts.append(self.act_attach_top)                # (0.106; a roof, 0.112)
        if counts.get("IfcWall", 0) == 2:                   # (0.105) two walls: one, if they are in line
            acts.append(self.act_merge_walls)
        if counts.get("IfcWall", 0) == 1 and sum(counts.values()) == 1:     # (0.109) one wall: its profile
            acts.append(self.act_edit_profile)
        if "IfcWall" in counts:                             # (0.298) a profile drawn, a top attached: undone
            ids = sorted(i for i in self.viewport.selection if isinstance(i, str))[:200]
            if any(self.doc.ifc.kind_of(i) == "wall" and self.doc.ifc.wall_profile(i) is not None for i in ids):
                acts.append(self.act_reset_profile)
            if any(self.doc.ifc.top_tied(i) for i in ids):
                acts.append(self.act_detach_top)
        if "IfcDoor" in counts or "IfcWindow" in counts:    # (0.110) doors / windows: number them all again
            acts.append(self.act_renumber)
        if "IfcSanitaryTerminal" in counts:                 # (0.142) fixtures: their branches to the network
            acts.append(self.act_connect_network)
        if set(counts) & set(bim.CIRCUIT_LOADS):            # (0.144) points, lights: a circuit of them
            acts.append(self.act_new_circuit)
        if "IfcWall" in counts:
            acts += [self.act_orthogonalize, self.act_unjoin_walls]
        acts += [self.act_same_type, self.act_zoom_selection, self.act_box_selection]
        if "IfcWall" in counts:
            acts.append(self.act_dimension_walls)
        return acts

    def _selected_walls(self):
        return sorted(i for i in self.viewport.selection if isinstance(i, str) and self.doc.ifc.kind_of(i) == "wall")

    def _kind_is(self, *kinds):
        """(0.322) What a command asks for, by the program's kind of element ("wall", "slab"…)."""
        return lambda i: isinstance(i, str) and self.doc.ifc.kind_of(i) in kinds

    def _class_is(self, *classes):
        """(0.322) What a command asks for, by IFC class."""
        return lambda i: self.doc.get(i) is not None and self.doc.get(i).ifc_class in classes

    def _ask(self, act, what, accept, then, **kw):
        """(0.322) ask_pick for a command of the ribbon: its name and icon on the balloon."""
        self.ask_pick(act.text(), t(what), accept, then, icon=act.icon(), **kw)

    def renumber_openings(self):
        """Numerar portas e janelas (0.110): P1, P2… and J1, J2… in the plans' reading order, storey by storey."""
        n = bim.renumber_openings(self.doc)
        self.message(t("info.renumbered", n=n) if n else t("info.renumbered_none"), warning=not n)
        self._refresh_properties()
        return n

    def edit_wall_profile(self, guid=None):
        """Editar perfil (0.109): the selected wall's elevation outline as grips (the tool Perfil da parede)."""
        if guid is None:
            walls = self._selected_walls()
            if len(walls) != 1:                  # (0.322) the wall asked for
                self._ask(self.act_edit_profile, "pick.profile_wall", self._kind_is("wall"), self.edit_wall_profile,
                          most=1, fresh=bool(walls))
                return False
            guid = walls[0]
        if self.doc.ifc.kind_of(guid) != "wall":
            self.message(t("info.edit_profile_none"), warning=True)
            return False
        self.viewport.set_selection(set())
        self.tools["wall_profile"].edit(guid)
        self.message(t("info.edit_profile", name=self.doc.get(guid).name))
        return True

    def attach_top(self):
        """Ligar o topo à laje (0.106): the walls and columns selected reach up (or down) to the underside of the
        slab selected with them, and follow it."""
        ids = list(self.viewport.selection)
        slabs = [i for i in ids if self.doc.ifc.kind_of(i) in ("slab", "roof")]        # (a roof too, 0.112)
        others = [i for i in ids if self.doc.ifc.kind_of(i) in ("wall", "column")]
        if len(slabs) > 1:
            self.message(t("info.attach_top_select"), warning=True)
            return []
        if not others:                           # (0.322) what is asked for: the walls and columns, then the slab
            self._ask(self.act_attach_top, "pick.attach_top", self._kind_is("wall", "column"), self.attach_top,
                      keep=slabs)
            return []
        if not slabs:
            self._ask(self.act_attach_top, "pick.attach_top_to", self._kind_is("slab", "roof"), self.attach_top,
                      most=1, keep=others)
            return []
        try:
            done = bim.attach_top(self.doc, others, slabs[0])
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return []
        self.message(t("info.attach_top", n=len(done), slab=self.doc.get(slabs[0]).name))
        return done

    def _selected_any_walls(self):
        """The walls selected, straight and curved."""
        return sorted(i for i in self.viewport.selection
                      if isinstance(i, str) and self.doc.ifc.kind_of(i) in ("wall", "curved_wall"))

    def flip_walls(self):
        """Virar a parede (0.299, Revit's flip arrows): the walls selected turned inside out — their layers."""
        try:
            done = bim.flip_walls(self.doc, self._selected_any_walls())
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return []
        self.message(t("info.flip_walls", n=len(done)) if done else t("info.flip_walls_none"), warning=not done)
        self._refresh_properties()
        return done

    def join_wall_ends(self):
        """Ligar as pontas (0.299, Revit's Allow Join): the free ends of the walls selected joined again."""
        walls = self._selected_any_walls()
        done = bim.join_wall_ends(self.doc, walls) if walls else []
        self.message(t("info.join_wall_ends", n=len(done)) if done else t("info.join_wall_ends_none"),
                     warning=not done)
        return done

    def attach_base(self):
        """Ligar a base (0.302, Revit's Attach Base): the walls and columns selected stand on the top of the slab or
        footing selected with them, and follow it."""
        ids = [i for i in self.viewport.selection if isinstance(i, str)]
        supports = [i for i in ids if self.doc.ifc.kind_of(i) in ("slab", "footing")]
        others = [i for i in ids if self.doc.ifc.kind_of(i) in ("wall", "column")]
        if len(supports) > 1:
            self.message(t("info.attach_base_select"), warning=True)
            return []
        if not others:                           # (0.322) asked for: the walls and columns, then what they stand on
            self._ask(self.act_attach_base, "pick.attach_base", self._kind_is("wall", "column"), self.attach_base,
                      keep=supports)
            return []
        if not supports:
            self._ask(self.act_attach_base, "pick.attach_base_to", self._kind_is("slab", "footing"), self.attach_base,
                      most=1, keep=others)
            return []
        try:
            done = bim.attach_base(self.doc, others, supports[0])
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return []
        self.message(t("info.attach_base", n=len(done), slab=self.doc.get(supports[0]).name))
        self._refresh_properties()
        return done

    def detach_base(self):
        """Desligar a base (0.302): the walls and columns selected no longer follow the slab or footing under them."""
        ids = [i for i in self.viewport.selection if isinstance(i, str) and self.doc.ifc.kind_of(i) in ("wall", "column")]
        done = bim.detach_base(self.doc, ids) if ids else []
        self.message(t("info.detach_base", n=len(done)) if done else t("info.detach_base_none"), warning=not done)
        self._refresh_properties()
        return done

    def detach_top(self):
        """Desligar o topo (0.298, Revit's Detach Top): the walls and columns selected no longer follow the slab or
        roof their top was attached to."""
        ids = [i for i in self.viewport.selection if isinstance(i, str) and self.doc.ifc.kind_of(i) in ("wall", "column")]
        done = bim.detach_top(self.doc, ids) if ids else []
        self.message(t("info.detach_top", n=len(done)) if done else t("info.detach_top_none"), warning=not done)
        self._refresh_properties()
        return done

    def reset_wall_profiles(self):
        """Repor perfil (0.298, Revit's Reset Profile): the walls selected with a drawn profile plain again."""
        done = bim.reset_wall_profiles(self.doc, self._selected_walls())
        self.message(t("info.reset_profile", n=len(done)) if done else t("info.reset_profile_none"),
                     warning=not done)
        self._refresh_properties()
        return done

    def merge_walls(self):
        """Juntar paredes (0.105): the two walls selected, in line and end to end, made one."""
        walls = self._selected_walls()
        if len(walls) != 2:                      # (0.322) the two walls asked for
            self._ask(self.act_merge_walls, "pick.merge", self._kind_is("wall"), self.merge_walls, least=2, most=2,
                      fresh=len(walls) > 2)
            return False
        # the one kept: the longer (its name and properties go on), else the first by name
        walls.sort(key=lambda g: (-round(self.doc.ifc.wall_params(g)[0], 6), self.doc.get(g).name))
        names = [self.doc.get(g).name for g in walls]
        try:
            bim.merge_walls(self.doc, *walls)
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return False
        self.viewport.set_selection({walls[0]})
        self.message(t("info.merged", a=names[0], b=names[1]))
        return True

    def orthogonalize_walls(self):
        """Ortogonalizar (0.105): the walls selected that are nearly along the red / green axis made exact."""
        walls = self._selected_walls()
        n = bim.orthogonalize(self.doc, walls) if walls else 0
        self.message(t("info.orthogonalized", n=n) if n else t("info.orthogonalized_none"), warning=not n)
        return n

    def unjoin_walls(self):
        """Soltar ligações (0.105): the walls selected no longer follow the walls they meet."""
        walls = self._selected_walls()
        n = bim.unjoin_walls(self.doc, walls) if walls else 0
        self.message(t("info.unjoined", n=n) if n else t("info.unjoined_none"), warning=not n)
        return n

    def edit_platform(self, guid=None, index=None):
        """Editar plataforma (0.204): the platforms of the terrain selected (or the only one) — the one clicked, or
        its only one — with their corners as grips (the tool Editar plataforma)."""
        if guid is None:
            every = [o.id for o in self.doc.objects.values() if o.is_bim and o.ifc_class == "IfcGeographicElement"]
            chosen = [i for i in self.viewport.selection if i in every]
            guid = chosen[0] if len(chosen) == 1 else (every[0] if len(every) == 1 else None)
            with_platforms = [g for g in every if self.doc.ifc.terrain_platforms(g)]
            if guid is None and with_platforms:      # (0.322) several terrains: the one asked for
                self._ask(self.act_edit_platform, "pick.platform", lambda i: i in with_platforms,
                          lambda: self.edit_platform(index=index), most=1, fresh=True)
                return False
        if guid is None or not self.doc.ifc.terrain_platforms(guid):
            terrain = any(o.is_bim and o.ifc_class == "IfcGeographicElement" for o in self.doc.objects.values())
            self.message(t("info.edit_platform_none"), warning=True,
                         action=self.tool_actions["platform" if terrain else "terrain"])          # (0.324)
            return False
        self.viewport.set_selection(set())
        self.tools["platform_outline"].edit(guid, index)
        self.message(t("info.edit_platform", name=self.doc.get(guid).name))
        return True

    # ------------------------------------------------------------ (0.414) types saved and applied

    def save_element_type(self, guid, name=None):
        """«Guardar como tipo…»: a type made from this element (model/element_types), named (asked when not given) —
        the element tied to it. Returns its GlobalId, or None."""
        from ..model import element_types
        kind = self.doc.ifc.kind_of(guid)
        if kind not in element_types.KINDS:
            return None
        if name is None:
            n = len(element_types.types_of(self.doc, kind)) + 1
            name, ok = QtWidgets.QInputDialog.getText(self, t("props.type_save").rstrip("…"), t("ask.type_name"),
                                                      text=t("type.default_name", k=t("elem." + kind), n=n))
            if not ok or not name.strip():
                return None
        try:
            made = element_types.save_type(self.doc, guid, name.strip())
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return None
        self._refresh_properties()
        self.message(t("info.element_type_saved", n=name.strip()))
        return made

    def apply_element_type(self, guids, type_guid):
        """A saved type put on these elements (and them tied to it) — None: tied to no type, their values kept."""
        from ..model import element_types
        done = element_types.apply_type(self.doc, guids, type_guid)
        if not done:
            return []
        if type_guid is None:
            self.message(t("info.type_none", n=len(done)))
        else:
            self.message(t("info.type_applied", n=self.doc.ifc.by_guid(type_guid).Name or "", k=len(done)))
        return done

    def update_element_type(self, guid):
        """«Atualizar o tipo»: this element's values taken to its type and to every other element of it."""
        from ..model import element_types
        type_guid = self.doc.ifc.element_type_of(guid)
        try:
            done = element_types.update_type(self.doc, guid)
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return []
        if done:
            self._refresh_properties()
            self.message(t("info.type_updated", n=self.doc.ifc.by_guid(type_guid).Name or "", k=len(done)))
        return done

    def set_work_plane(self, plane):
        """(0.412) The work plane the drawing tools start on in the 3D view (model/work_plane) — None: the active
        storey's level again. Shown as a blue grid."""
        from ..model.work_plane import describe
        from ..tools.work_plane import where
        if plane is not self.doc.work_plane:
            self.doc.work_plane = plane
            self.doc.modified = True                 # (0.413: kept with the project — saved with it)
            self._update_title()
        self.viewport.redraw()
        if plane is None:
            self.message(t("info.work_plane_off"))
            return
        at = where(plane)
        self.message(t("info.work_plane", p=t(describe(plane)), at=(" ({})".format(at) if at else "")))

    def edit_slab_outline(self, guid=None):
        """Editar contorno (0.100): the selected slab's corners as grips (the tool Contorno da laje). A round
        slab changes by its radius, in the Properties panel. (0.410) A floor finish's or a ceiling's too, with
        the wall profile's gestures and holes."""
        from ..tools.slab import OUTLINED
        if guid is None:
            slabs = [i for i in self.viewport.selection
                     if isinstance(i, str) and self.doc.ifc.kind_of(i) in OUTLINED]
            if len(slabs) != 1:                  # (0.322) the slab asked for
                self._ask(self.act_edit_outline, "pick.outline", self._kind_is(*OUTLINED), self.edit_slab_outline,
                          most=1, fresh=bool(slabs))
                return False
            guid = slabs[0]
        if self.doc.ifc.kind_of(guid) not in OUTLINED:
            self.message(t("info.edit_outline_none"), warning=True)
            return False
        if self.doc.ifc.kind_of(guid) == "slab" and self.doc.ifc.slab_shape(guid) == "circulo":
            self.message(t("info.edit_outline_circle"), warning=True)
            return False
        self.viewport.set_selection(set())
        self.tools["slab_outline"].edit(guid)
        self.message(t("info.edit_outline", name=self.doc.get(guid).name))
        return True

    def _tool_options(self):
        """The tool's settings, and the storey it draws on (a tool that draws on the active storey)."""
        options = list(self.tool.options())
        storeys = self.doc.storeys()
        if self.tool.on_storey and storeys:
            options.append(Option("storey", t("ctx.storey"), "choice", self.doc.active_storey,
                                  tuple((g, name) for g, name, _z in storeys)))
        return options

    def _refresh_context_bar(self):
        self.context_bar.show_items(self._context_items())

    def refresh_context_bar(self):
        """(0.472) The parameters' bar shows again what is to be shown now (a sheet: what was picked on it)."""
        if hasattr(self, "context_bar"):
            self._refresh_context_bar()

    def documents_folder(self):
        """(0.472) Where a file dialog starts: the project's folder, else the user's Documents."""
        return os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()

    def _sync_context_bar(self):
        """The tool's settings changed some other way (Tab, typed, a menu): the bar shows them."""
        if self.tool is None or not hasattr(self, "context_bar"):
            return
        if self.tool.name == "select":
            return
        if not self.context_bar.sync(self._tool_options()):
            self._refresh_context_bar()

    def _context_option(self, key, value):
        if self.sheet_shown() and isinstance(key, str) and key.startswith("sheet_"):   # (0.472) the sheet's
            self.sheet_window.option(key, value)
            return
        if key == "storey":
            self.set_active_storey(value)
        else:
            self.tool.set_option(key, value)
        self._sync_context_bar()

    def _build_status_bar(self):
        sb = self.statusBar()
        self.hint_label = QtWidgets.QLabel()
        # (0.184) a long hint is cut, not pushing the navigation and the measurements off the status bar
        self.hint_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Preferred)
        self.hint_label.setMinimumWidth(120)
        sb.addWidget(self.hint_label, 1)
        self.share_label = QtWidgets.QLabel()           # a shared project: its reservations
        self.share_label.setStyleSheet(self._share_style())
        self.share_label.setVisible(False)
        sb.addPermanentWidget(self.share_label)
        # the storey being drawn on — (0.186) a click lists the storeys: another becomes the active one
        self.storey_label = QtWidgets.QToolButton()
        self.storey_label.setObjectName("footer_storey")
        self.storey_label.setAutoRaise(True)
        self.storey_label.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.storey_label.setStyleSheet("QToolButton#footer_storey { padding: 0 8px; font-weight: 600; }")
        self.storey_label.setToolTip(t("tip.foot.storey"))
        self.storey_menu = QtWidgets.QMenu(self.storey_label)
        self.storey_menu.aboutToShow.connect(self._fill_storey_menu)
        self.storey_label.setMenu(self.storey_menu)
        sb.addPermanentWidget(self.storey_label)
        self.vcb_title = QtWidgets.QLabel()
        self.vcb = QtWidgets.QLabel()
        self.vcb.setMinimumWidth(220)
        self.vcb.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.vcb.setStyleSheet(self._vcb_style())
        sb.addPermanentWidget(self.vcb_title)
        sb.addPermanentWidget(self.vcb)
        # shown while a file opened from its kept shapes still has its IFC being read (see open_path)
        self.loading_box = QtWidgets.QWidget()
        box = QtWidgets.QHBoxLayout(self.loading_box)
        box.setContentsMargins(0, 0, 0, 0)
        self.loading_label = QtWidgets.QLabel()
        self.loading_bar = QtWidgets.QProgressBar()
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setMaximumWidth(120)
        self.loading_cancel = QtWidgets.QPushButton(t("open.cancel"))
        for w in (self.loading_label, self.loading_bar, self.loading_cancel):
            box.addWidget(w)
        sb.insertPermanentWidget(0, self.loading_box)
        self.loading_box.hide()

    # ------------------------------------------------------------ tool host API

    def set_hint(self, text):
        self.hint_label.setText(text)
        self.hint_label.setToolTip(text)          # (0.321) whole, when the footer cuts it
        self.notice.hint_changed(text)
        self._sync_context_bar()                  # (a setting may have changed with it: Tab, a typed height)

    def _selection_changed_bar(self):
        if self.tool is not None and self.tool.name == "select":
            self._refresh_context_bar()

    def set_vcb(self, text):
        self._vcb_live = text
        self._refresh_vcb()

    def message(self, text, warning=False, action=None):
        """What a command says — a refusal (warning) or what it did — in the balloon over the view (0.321: it was a
        line at the foot of the window, cut short, gone in 10 s, and it hid the tool's step meanwhile). (0.324)
        action: the step that is missing (a QAction: a tool, a command), a button in the balloon."""
        self.last_message = ("⚠ " if warning else "") + text
        self.notice.say(text, warning, self._as_button(action))

    @staticmethod
    def _as_button(act):
        """(0.324) A QAction as the balloon's button: its name (without its key) and what it does."""
        if act is None:
            return None
        return act.text().split("   (")[0].strip(), act.trigger

    def _on_storey(self, ifc_class):
        storey = self.doc.active_storey
        return any(o.is_bim and o.ifc_class == ifc_class and o.storey == storey for o in self.doc.objects.values())

    def _columns_offer(self):
        """(0.324) No column on the active storey: «Pilares na grelha» (there is a grid) or the Column tool."""
        if self._on_storey("IfcColumn"):
            return None
        return self.act_columns_on_grid if self.doc.grids else self.tool_actions["column"]

    def _beams_offer(self):
        """(0.324) No beam on the active storey: «Vigas entre pilares» — or, with no columns either, those first."""
        if self._on_storey("IfcBeam"):
            return None
        return self._columns_offer() or self.act_beams_between

    def _missing_for(self, name):
        """(0.324) What a tool needs that is not there yet, as the button of its balloon: an image to calibrate, a
        terrain for a platform or a ramp."""
        if name == "calibrate_image" and not self.doc.images:
            return self.act_import_image
        if name in ("platform", "terrain_ramp") and self.tools[name].terrain() is None:
            return self.tool_actions["terrain"]
        return None

    def vcb_title_changed(self):
        """The tool's Measurements box now asks for something else (a beam: its top, then its length)."""
        self.vcb_title.setText((self.tool.vcb_title() or t("vcb.label")) + ":")

    def _refresh_vcb(self):
        self.vcb.setText(self._typed + "▏" if self._typed else getattr(self, "_vcb_live", ""))
        typing = getattr(getattr(self, "tool", None), "typing", None)   # (0.361) what is typed, shown where it goes
        if callable(typing):
            typing(self._typed)

    # ------------------------------------------------------------ commands

    def set_tool(self, name):
        if name in ("mirror", "scale") and self.tool is not None and self._pick_first(name):
            return
        plan = self._plan_for(name)
        with self.doc.ifc.remembering():                # (0.225: its bar asks the storeys a few times: once)
            self._set_tool(name)
        if plan is not None:                            # (0.323: why the view changed, with the tool's step)
            act = self.tool_actions.get(name)
            self.notice.hint(t("tool." + name), "{} {}".format(t("info.plan_for_tool", plan=plan),
                                                               notice._step(t("tool." + name), self.hint_label.text())),
                             act.icon() if act is not None else None)

    def _tool_cursor(self):
        """(0.526) The 3D view's cursor: the tool's (ui/tool_cursors)."""
        if getattr(self, "tool", None) is None:
            return None
        act = self.tool_actions.get(self.tool.name)
        # (0.529) drawn at the screen's own pixel ratio: at 2× on a 1× screen (the WSL's) the X server showed the
        # picture twice as big, its cross's centre 10 px off the point clicked — the profile's grips were missed
        try:
            ratio = max(1.0, float(self.canvas.devicePixelRatioF()))
        except (AttributeError, RuntimeError):
            ratio = 1.0
        cursor = tool_cursors.cursor_for(self.tool.name, act.icon() if act is not None else None, ratio=ratio)
        for w in (self.canvas, getattr(self.canvas, "_subwidget", None)):
            if w is not None:
                w.setCursor(cursor)
        return cursor

    def _plan_for(self, name):
        """(0.323) Cota, Desenho 2D and Pormenor chosen in a 3D view: they are drawn in a plan, a section or an
        elevation — the active storey's plan is opened for them (until 0.322 their step said «open a plan first»
        and a click in the 3D view did nothing). The plan's storey name, or None (nothing opened)."""
        if name not in VIEW_TOOLS or self.tool is None or self.sheet_shown() or self._loading \
                or self.viewport.current_view() is not None or not self.doc.storeys():
            return None
        self.set_plan(True)
        return self._storey(self.doc.active_storey)[0] if self.viewport.current_view() is not None else None

    def _set_tool(self, name):
        if name != "select" and self.pick_request is not None:
            self.cancel_pick()                # (0.322) another tool: the command waiting for elements given up
        if self.tool is not None:
            self.tool.deactivate()
        self.notice.dismiss()                 # (0.321: not a refusal said just now — that one stays)
        if hasattr(self, "quick"):
            self.quick.close_panel()          # (0.354)
        self.tool = self.tools[name]
        if name in self.tool_actions:
            self.tool_actions[name].setChecked(True)
        else:                                 # a tool with no button (placing a component): none pressed
            for act in self.tool_actions.values():
                if act.isChecked():
                    act.actionGroup().setExclusive(False)
                    act.setChecked(False)
                    act.actionGroup().setExclusive(True)
        self._typed = ""
        self.vcb_title.setText((self.tool.vcb_title() or t("vcb.label")) + ":")
        self.tool.activate()
        if name not in QUIET_TOOLS:           # (0.321) its first step, whole, over the view: until its first click
            act = self.tool_actions.get(name)
            self.notice.hint(t("tool." + name) if i18n_has("tool." + name) else "", self.hint_label.text(),
                             act.icon() if act is not None else None, self._as_button(self._missing_for(name)))
        self._refresh_context_bar()
        self._tool_cursor()                               # (0.526) the cursor says which tool: cross + its icon
        self.canvas.setFocus()
        self.viewport.redraw()
        if self._help is not None and self._help.isVisible():
            self._help.refresh_tool()             # (0.327: the Help window follows the tool in use)

    # ------------------------------------------------------------ elements asked for (0.322)

    def ask_pick(self, title, what, accept, then, least=1, most=0, keep=(), fresh=False, icon=None):
        """A command short of the elements it needs asks for them (_Pick): the Select tool picks them, the balloon
        says what to click and how many are chosen. What is selected and fits is kept as picked (fresh: not — a
        command for one element with several selected); `keep`: chosen before (another kind), kept selected."""
        self.pick_request = None
        if self.tool.name != "select":
            self.set_tool("select")
        self.tool_actions["select"].setChecked(True)          # (Mirror's button, pressed on the way, let go)
        keep = frozenset(keep)
        self.pick_request = _Pick(title.split("   (")[0].replace("…", "").strip(), what, accept, then, least, most,
                                  keep, icon)
        chosen = set() if fresh else {i for i in self.viewport.selection if i not in keep and accept(i)}
        self._pick_busy = True
        try:
            self.viewport.set_selection(set(keep) | chosen)
        finally:
            self._pick_busy = False
        self.set_hint(self.tool.hint())
        self._show_pick()
        if most and len(chosen) >= most:
            QtCore.QTimer.singleShot(0, self.finish_pick)

    def _picked(self):
        p = self.pick_request
        return sorted((i for i in self.viewport.selection if i not in p.keep and p.accept(i)), key=str)

    def _show_pick(self):
        p = self.pick_request
        keys = t("pick.keys_one") if p.most == 1 else t("pick.keys", n=len(self._picked()))
        self.notice.ask(p.title, "{}\n{}".format(p.what, keys), p.icon)

    def _pick_changed(self):
        """The selection changed while a command waits: what does not fit it is let go (said), the count shown; with
        `most` picked it goes on by itself."""
        p = self.pick_request
        if p is None or self._pick_busy:
            return
        wrong = [i for i in self.viewport.selection if i not in p.keep and not p.accept(i)]
        if wrong:
            self._pick_busy = True
            try:
                self.viewport.set_selection(set(self.viewport.selection) - set(wrong), keep_faces=True)
            finally:
                self._pick_busy = False
            self.message(t("pick.wrong", c=p.title), warning=True)
        self._show_pick()
        if p.most and len(self._picked()) >= p.most:
            QtCore.QTimer.singleShot(0, self.finish_pick)

    def finish_pick(self):
        """Enter / the right button (or `most` picked): the command goes on with what was picked. False if there is
        no command waiting, or too few are picked (said)."""
        p = self.pick_request
        if p is None:
            return False
        chosen = self._picked()
        if len(chosen) < p.least:
            self.message(t("pick.few", n=p.least - len(chosen)), warning=True)
            return False
        self.pick_request = None
        self.notice.end_ask()
        self._pick_busy = True
        try:
            self.viewport.set_selection(set(p.keep) | set(chosen))
        finally:
            self._pick_busy = False
        self.set_hint(self.tool.hint())
        p.then()
        return True

    def cancel_pick(self):
        """Esc, the balloon's ×, another tool: the command waiting is given up (the selection stays)."""
        if self.pick_request is None:
            return False
        title, self.pick_request = self.pick_request.title, None
        self.notice.end_ask()
        self.set_hint(self.tool.hint())
        self.message(t("pick.cancelled", c=title))
        return True

    def _pick_first(self, name):
        """Mirror and Scale chosen with nothing selected that they work on: what to mirror (to scale: sketches) is
        asked for first — then the tool, on it."""
        if name == "mirror":
            def accept(i):
                return self.doc.get(i) is not None
        else:
            def accept(i):
                return self.doc.get(i) is not None and not self.doc.get(i).is_bim
        if any(accept(i) for i in self.viewport.selection):
            return False
        if name == "scale" and self.presentation_mode is not None \
                and self.presentation_mode.chosen_volume() is not None:
            return False                                  # (0.492: the Presentation tab's volume chosen is scaled)
        act = self.tool_actions.get(name)
        self.ask_pick(t("tool." + name), t("pick." + name), accept, lambda: self.set_tool(name),
                      icon=act.icon() if act is not None else None)
        return True

    def _title_block_editor(self):
        """(0.473) The company's title block being drawn on the sheet shown, or None."""
        return self.sheet_window.editor if hasattr(self, "sheet_window") and self.sheet_shown() else None

    def undo(self):
        if self._title_block_editor() is not None:     # (0.473: the drawing's own steps until «Concluir»)
            self._title_block_editor().undo()
            return
        self.tool.cancel()
        self.doc.undo()

    def redo(self):
        if self._title_block_editor() is not None:
            self._title_block_editor().redo()
            return
        self.tool.cancel()
        self.doc.redo()

    # ------------------------------------------------------------ components

    def _component_dialog(self, default_name):
        """Name and kind of a new component (OK / Cancel). Returns (name, category) or None."""
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(t("act.component_make").rstrip("…"))
        form = QtWidgets.QFormLayout(dlg)
        name = QtWidgets.QLineEdit(default_name)
        kind = QtWidgets.QComboBox()
        for category in bim.COMPONENT_CATEGORIES:
            kind.addItem(t("cat." + category), category)
        form.addRow(t("props.name"), name)
        form.addRow(t("props.kind"), kind)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return None
        return name.text().strip() or default_name, kind.currentData()

    def continue_wall(self, guid, end=1):
        """(0.353) The «+» on an end of a wall chosen alone (Select): the Wall tool, of that wall's type and height, by
        its axis, drawing on from that end (0: its start, 1: its end) — the next click makes a wall joined to it there,
        and the chain goes on as usual. Returns whether it started."""
        import ifcopenshell.util.element
        ifc = self.doc.ifc
        if ifc.by_guid(guid) is None or ifc.kind_of(guid) != "wall":
            return False
        a, b, _thickness = ifc.wall_axis(guid)
        _length, height, _width = ifc.wall_params(guid)
        type_ = ifcopenshell.util.element.get_type(ifc.by_guid(guid))
        name = type_.Name if type_ is not None else None
        spec = next((s for s in catalog.types() if s.kind == "wall" and name in (s.name_pt, s.name_en)), None)
        self.viewport.set_selection(set())
        self.set_tool("wall")
        tool = self.tools["wall"]
        if tool.shape != "line":
            tool.set_option("shape", "line")
        tool.reference = "axis"
        if spec is not None:
            tool.spec = spec
        tool.height = height
        tool.cancel()
        tool._start = np.array(a if end == 0 else b, dtype=float)
        self.set_hint(tool.hint())
        self._refresh_context_bar()
        self.message(t("info.wall_continue", name=self.doc.get(guid).name))
        return True

    def make_component(self, name=None, category=None):
        """BIM ▸ Make component (G): the selected sketch volumes become one component (a face picked alone: its
        volume, 0.310)."""
        ids = [i for i in self.viewport.objects_picked()
               if self.doc.get(i) is not None and not self.doc.get(i).is_bim and self.doc.get(i).mesh.faces]
        if not ids:                              # (0.322) the sketch volumes asked for
            self._ask(self.act_component_make, "pick.component",
                      lambda i: self.doc.get(i) is not None and not self.doc.get(i).is_bim
                      and bool(self.doc.get(i).mesh.faces), lambda: self.make_component(name, category))
            return None
        if name is None:
            n = sum(1 for e in self.doc.ifc.file.by_type("IfcTypeProduct")
                    if self.doc.ifc.kind_of(e.GlobalId) == "component") + 1
            answer = self._component_dialog(t("component.default_name", n=n))
            if answer is None:
                return None
            name, category = answer
        guid = bim.make_component(self.doc, ids, name, category or "furniture", storey=self.doc.active_storey)
        if guid:
            self.viewport.set_selection({guid})
            self.message(t("info.component_made", name=name))
        return guid

    def edit_component(self):
        """BIM ▸ Edit component: the selected copy turns into a sketch to reshape."""
        guids = [i for i in self.viewport.selection if self.doc.get(i) is not None and self.doc.get(i).is_bim
                 and self.doc.ifc.component_type(i)]
        if len(guids) != 1:                      # (0.322) the copy asked for
            self._ask(self.act_component_edit, "pick.component_edit",
                      lambda i: self.doc.get(i) is not None and self.doc.get(i).is_bim
                      and bool(self.doc.ifc.component_type(i)), self.edit_component, most=1, fresh=bool(guids))
            return None
        self._stop_drawing()
        name = self.doc.get(guids[0]).name
        sketch_id = bim.edit_component(self.doc, guids[0])
        self.viewport.set_selection({sketch_id})
        self.message(t("info.component_editing", name=name))
        return sketch_id

    def close_component(self):
        """BIM ▸ Close component: the new shape goes to every copy."""
        editing = [o for o in self.doc.sketches() if o.component]
        chosen = [o for o in editing if o.id in self.viewport.selection] or editing
        if not editing:                           # (0.327: it said «select the component…» with none open)
            self.message(t("err.component_none_open"), warning=True, action=self.act_component_edit)
            return None
        if len(chosen) != 1:                      # (several open: the one to close, asked for)
            ids = {o.id for o in editing}
            self._ask(self.act_component_close, "pick.component_close", lambda i: i in ids, self.close_component,
                      most=1, fresh=True)
            return None
        self._stop_drawing()
        sketch = chosen[0]
        n = len(self.doc.ifc.component_instances(sketch.component["type"])) + 1
        guid = bim.finish_component(self.doc, sketch.id)
        if guid:
            self.viewport.set_selection({guid})
            self.message(t("info.component_closed", name=sketch.component["component"], n=n))
        return guid

    # ------------------------------------------------------------ groups

    def _selected_bim(self):
        return [i for i in self.viewport.selection if self.doc.get(i) is not None and self.doc.get(i).is_bim]

    def make_group(self, name=None):
        """BIM ▸ Make group (Ctrl+G): the selected IFC elements become a group."""
        guids = self._selected_bim()
        if not guids:                            # (0.322) the elements asked for
            self._ask(self.act_group_make, "pick.group", lambda i: self.doc.get(i) is not None
                      and self.doc.get(i).is_bim, lambda: self.make_group(name))
            return None
        if name is None:
            n = sum(1 for g in self.doc.ifc.file.by_type("IfcGroup")
                    if self.doc.ifc._params(g).get("Elemento") == "group") + 1
            name, ok = QtWidgets.QInputDialog.getText(self, t("act.group_make").rstrip("…"), t("props.name"),
                                                      text=t("group.default_name", n=n))
            if not ok:
                return None
            name = name.strip() or t("group.default_name", n=n)
        try:
            group = bim.make_group(self.doc, guids, name)
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return None
        self.viewport.set_selection(set(self.doc.ifc.group_members(group)))
        self.message(t("info.group_made", name=name))
        return group

    def ungroup(self):
        guids = self._selected_bim()
        if not guids:                            # (0.322) the group asked for
            self._ask(self.act_group_ungroup, "pick.ungroup", lambda i: self.doc.get(i) is not None
                      and self.doc.get(i).is_bim and bool(bim.group_members_of(self.doc, i)), self.ungroup, most=1)
            return None
        group = bim.ungroup(self.doc, guids[0])
        if group is None:
            self.message(t("err.group_pick"), warning=True)
            return None
        self.message(t("info.ungrouped"))
        return group

    def _storeys_dialog(self, exclude):
        """Which storeys to repeat the selection on (check boxes). Returns GlobalIds or None."""
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(t("act.repeat_storeys").rstrip("…"))
        layout = QtWidgets.QVBoxLayout(dlg)
        layout.addWidget(QtWidgets.QLabel(t("repeat.ask")))
        listing = QtWidgets.QListWidget()
        for guid, name, z in reversed(self.doc.storeys()):
            if guid == exclude:
                continue
            item = QtWidgets.QListWidgetItem("{}   ({})".format(name, storeys.level_text(z)))
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, guid)
            listing.addItem(item)
        layout.addWidget(listing)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return None
        return [listing.item(i).data(QtCore.Qt.ItemDataRole.UserRole) for i in range(listing.count())
                if listing.item(i).checkState() == QtCore.Qt.CheckState.Checked]

    def wall_shape(self, shape):
        """(0.374) The Wall tool in that shape (a rectangle, a circle, an arc, along a face, the magic wand)."""
        self.set_tool("wall")
        self.tools["wall"].set_option("shape", shape)
        self._sync_context_bar()
        return self.tools["wall"]

    def identify_rooms(self):
        """(0.374, the study's «Identificar») A room in every closed space of the active storey that has none."""
        made = bim.identify_rooms(self.doc)
        self.message(t("info.rooms_identified", n=len(made)) if made else t("info.rooms_none_new"),
                     warning=not made)
        return made

    def show_areas(self):
        """(0.374, the study's «Áreas») The net (its rooms) and gross areas of each storey, in a table."""
        rows = bim.storey_areas(self.doc)
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(t("act.areas").split("   (")[0])
        box = QtWidgets.QVBoxLayout(dlg)
        table = QtWidgets.QTableWidget(len(rows) + 1, 4)
        table.setHorizontalHeaderLabels([t("areas.storey"), t("areas.rooms"), t("areas.net"), t("areas.gross")])
        fmt = lambda a: "{:.2f} m²".format(a).replace(".", decimal_sep())          # noqa: E731
        for k, (name, _z, net, gross, n) in enumerate(rows):
            for j, text in enumerate((name, str(n), fmt(net), fmt(gross))):
                table.setItem(k, j, QtWidgets.QTableWidgetItem(text))
        total = (t("areas.total"), str(sum(r[4] for r in rows)), fmt(sum(r[2] for r in rows)),
                 fmt(sum(r[3] for r in rows)))
        for j, text in enumerate(total):
            item = QtWidgets.QTableWidgetItem(text)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            table.setItem(len(rows), j, item)
        table.resizeColumnsToContents()
        table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        box.addWidget(QtWidgets.QLabel(t("areas.note")))
        box.addWidget(table)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dlg.reject)
        box.addWidget(buttons)
        dlg.resize(560, 260)
        self._areas_dialog = dlg
        dlg.exec()
        return rows

    def copy_to_clipboard(self):
        """(0.326) Ctrl+C: the elements selected kept to be pasted — Ctrl+V where clicked, Ctrl+Shift+V on other
        storeys —, from the lowest corner of their box. Nothing selected: what to copy is asked for."""
        ids = [i for i in self.viewport.selection if self.doc.get(i) is not None]
        # (0.373) loose lines / faces picked alone: copied as they are now (sketches of their own)
        alone = [] if ids else (parts.line_copies(self.doc, self.viewport.line_selection)
                                + parts.face_copies(self.doc, self.viewport.face_selection))
        if not ids and not alone:
            self._ask(self.act_copy_clip, "pick.copy_clip", lambda i: self.doc.get(i) is not None,
                      self.copy_to_clipboard)
            return []
        low = None
        for obj in [self.doc.get(i) for i in ids] + alone:
            v = np.asarray(obj.mesh.verts, dtype=float).reshape(-1, 3)
            if len(v):
                w = (v @ obj.matrix[:3, :3].T + obj.matrix[:3, 3]).min(axis=0)
                low = w if low is None else np.minimum(low, w)
        self._clipboard = (list(ids), low if low is not None else np.zeros(3), alone)
        self.message(t("info.clip_copied", n=len(ids) or len(alone)))
        return ids or alone

    def _clip_ids(self):
        """The elements copied that are still there (the Ctrl+V's), said when there are none."""
        ids = [i for i in (self._clipboard[0] if self._clipboard else []) if self.doc.get(i) is not None]
        if not ids:
            self.message(t("info.clip_gone" if self._clipboard else "info.clip_empty"), warning=True,
                         action=None if self._clipboard else self.act_copy_clip)
        return ids

    def paste(self):
        """(0.326) Ctrl+V, as Revit's Paste: the elements copied on the cursor, from their base point (the Copy tool);
        a click puts the copy there."""
        alone = self._clipboard[2] if self._clipboard else []          # (0.373) lines / faces copied alone
        ids = [] if alone else self._clip_ids()
        if not (ids or alone) or self.sheet_shown():
            return False
        self.set_tool("copy")
        return self.tools["copy"].paste(ids, self._clipboard[1], sketches=alone)

    def paste_on_storeys(self):
        """(0.326) Ctrl+Shift+V, as Revit's Paste Aligned to selected levels: the elements copied, in the same place,
        on the storeys chosen (Repetir nos pavimentos)."""
        ids = self._clip_ids()
        if not ids:
            return []
        self.viewport.set_selection(set(ids))
        return self.repeat_on_storeys()

    def repeat_on_storeys(self, storey_guids=None):
        """BIM ▸ Repeat on storeys: copies of the selection on other storeys (a typical floor)."""
        ids = [i for i in self.viewport.selection if self.doc.get(i) is not None]
        if len(self.doc.storeys()) < 2:
            self.message(t("err.repeat_storeys"), warning=True, action=self.act_storey_new)       # (0.327)
            return []
        if not ids:                              # (0.322) what to repeat, asked for
            self._ask(self.act_repeat, "pick.repeat", lambda i: self.doc.get(i) is not None,
                      lambda: self.repeat_on_storeys(storey_guids))
            return []
        bim_objs = [self.doc.get(i) for i in ids if self.doc.get(i).is_bim]
        source = bim_objs[0].storey if bim_objs else self.doc.active_storey
        if storey_guids is None:
            storey_guids = self._storeys_dialog(source)
            if not storey_guids:
                return []
        self._stop_drawing()
        try:
            new = bim.repeat_on_storeys(self.doc, ids, storey_guids)
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return []
        self.message(t("info.repeated", n=len(storey_guids)))
        return new

    # ------------------------------------------------------------ storeys

    def _storey(self, guid):
        for g, name, z in self.doc.storeys():
            if g == guid:
                return name, z
        return "", 0.0

    def _stop_drawing(self):
        if self.tool.name != "select":        # (Select keeps its selection)
            self.tool.cancel()

    def set_active_storey(self, guid):
        """Draw on this storey from now on (its level becomes the work plane)."""
        if guid == self.doc.active_storey:
            return
        self._stop_drawing()                  # a half-drawn wall stays on its own storey
        self.doc.set_active_storey(guid)
        if self.viewport.plan and not self.views.retarget(("plan", guid)):
            self._apply_view(("plan", guid))                # (this plan moves to that storey: its own template)
        name, z = self._storey(guid)
        self.message(t("info.storey_active", name=name, z=storeys.level_text(z)))

    def step_storey(self, step):
        """PgUp / PgDn: the storey above / below becomes the active one."""
        levels = [g for g, _n, _z in self.doc.storeys()]
        if self.doc.active_storey in levels:
            i = levels.index(self.doc.active_storey) + step
            if 0 <= i < len(levels):
                self.set_active_storey(levels[i])
            elif step > 0:                        # (0.325: it said nothing) the highest: a new one above?
                self.message(t("info.storey_top"), action=self.act_storey_new)
            else:
                self.message(t("info.storey_bottom"))

    def new_storey(self):
        levels = self.doc.storeys()
        z = (levels[-1][2] if levels else 0.0) + 3.0
        name = t("storeys.default_name", n=len(levels))
        self._stop_drawing()
        guid = bim.add_storey(self.doc, name, z)
        self.doc.set_active_storey(guid)
        self.message(t("info.storey_new", name=name, z=storeys.level_text(z)))
        return guid

    def _rename_storey(self, guid, name):
        bim.rename_storey(self.doc, guid, name)

    def _move_storey(self, guid, z):
        n = len(self.doc.ifc.storey_elements(guid))
        self._stop_drawing()
        bim.set_storey_elevation(self.doc, guid, z)
        self.message(t("info.storey_moved", name=self._storey(guid)[0], z=storeys.level_text(z), n=n))

    def _delete_storey(self, guid):
        try:
            bim.remove_storey(self.doc, guid)
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)

    def set_only_active_storey(self, on):
        on = bool(on)
        for widget in (self.act_only_active, self.storeys_panel.only_active):
            if widget.isChecked() != on:
                widget.blockSignals(True)
                widget.setChecked(on)
                widget.blockSignals(False)
        self.viewport.set_only_active_storey(on)

    def set_plan(self, on=True):
        """View ▸ Plan of the active storey (F4): its tab (opened if it is not), cut at 1,20 m,
        seen from above; F4 again: the 3D view's tab. PgUp / PgDn: the plan of the storey above /
        below (its tab if open, else this plan moves there)."""
        self.views.open(("plan", self.doc.active_storey) if on else view_tabs.THREE_D)
        self._tick_plan(self.viewport.plan and not self.sheet_shown())   # (as the view is, whatever was clicked)

    def _show_plan(self, on):
        on = bool(on)
        self._tick_plan(on)
        self._apply_view(("plan", self.doc.active_storey) if on else None)
        self.viewport.set_plan(on)
        self._refresh_storeys()
        if on:
            name, z = self._storey(self.doc.active_storey)
            self.message(t("info.plan", name=name, z=storeys.level_text(z + self.viewport.cut_height)))

    def set_box(self, on=True, fit=False, store=True):
        """View ▸ Section box (F6): the 3D view shows only what is inside a box — round the
        selection if there is one, else round the whole model — what it cuts filled dark (as
        ArchiCAD's 3D cutaway); its faces are moved by dragging their blue dots (Select). F6
        again: the whole model. fit (Shift+F6): the box round the selection again. The box is
        the 3D view's (0.64: a view property, kept with the project, one undo step) — store:
        False for another project coming in."""
        self._set_box(on, fit)
        if store:
            self._store_box()

    def _set_box(self, on, fit):
        on = bool(on)
        if on and (fit or self.viewport.box is None):
            ids = set(self.viewport.selection) or None
            if fit and ids is None:                  # (0.322) what to see in the box, asked for
                self._ask(self.act_box_selection, "pick.box", lambda i: self.doc.get(i) is not None,
                          lambda: self.set_box(True, fit=True))
                on = self.viewport.box is not None
            else:
                box = self.viewport.box_around(ids)
                if box is None:
                    self.message(t("info.box_nothing"), warning=True)
                    on = False
                else:
                    if self.viewport.cutting():
                        self.set_view("iso")             # (a plan or section has its own cut)
                    self.viewport.set_box(*box)
                    if self.tool.name != "select":
                        self.set_tool("select")          # (its dots are dragged with Select)
                    self.message(t("info.box_on_selection" if ids else "info.box_on"))
        if not on and self.viewport.box is not None:
            self.viewport.set_box(None)
            self.message(t("info.box_off"))
        self._tick_box(on)

    def _tick_box(self, on):
        if self.act_box.isChecked() != on:
            self.act_box.blockSignals(True)
            self.act_box.setChecked(on)
            self.act_box.blockSignals(False)

    def _store_box(self):
        """The section box as it is now becomes the 3D view's (one undo step)."""
        box = self.viewport.box
        value = [[float(c) for c in box[0]], [float(c) for c in box[1]]] if box is not None else None
        if self.doc.view_settings(self._live_3d()).box != (None if value is None else
                                                             (tuple(value[0]), tuple(value[1]))):
            self.doc.set_view_props(self._live_3d(), box=value)

    def box_changed(self):
        """A face of the section box was dragged (Select): kept as the 3D view's."""
        self._store_box()

    def _apply_box(self, box):
        """The 3D view's section box on screen (as its properties keep it)."""
        now = self.viewport.box
        same = (now is None and box is None) or (now is not None and box is not None and np.allclose(
            np.array(now), np.array(box), atol=1e-9))
        if not same:
            self.viewport.set_box(*[np.array(c, dtype=float) for c in box] if box is not None else (None,))
        self._tick_box(box is not None)

    # ------------------------------------------------------------ the view cube's menu (0.81)

    def _cube_menu(self, x, y):
        """The view cube's ▾: the starting view (go, set the current one, back to the usual), zoom all,
        perspective or axonometry."""
        menu = QtWidgets.QMenu(self)
        menu.addAction(t("cube.menu.home"), lambda: self.viewport.go_home())
        menu.addAction(t("cube.menu.set_home"), lambda: self._set_home_view())
        reset = menu.addAction(t("cube.menu.reset_home"), lambda: self._set_home_view(reset=True))
        reset.setEnabled(self.viewport.home_view is not None)
        menu.addSeparator()
        menu.addAction(self.act_zoom_all)
        menu.addSeparator()
        axonometric = self.doc.view_settings(self._live_3d()).axonometric
        for text, value in ((t("props.view_perspective"), False), (t("props.view_axonometric"), True)):
            act = menu.addAction(text, lambda v=value: self._edit_view("view_axonometric", self._live_3d(), v))
            act.setCheckable(True)
            act.setChecked(axonometric == value)
        self._cube_menu_shown = menu                  # (tests)
        menu.popup(menus.menu_point(menu, self.canvas.mapToGlobal(QtCore.QPoint(int(x), int(y)))))

    def _set_home_view(self, reset=False):
        """The view as it is now becomes the 3D view's starting one (the cube's house goes there); kept with
        the project; one undo step."""
        view = self._live_3d()
        self.doc.set_view_props(view, home=None if reset else self.viewport.home_from_here())
        self._apply_look()
        self.message(t("info.home_reset" if reset else "info.home_set"))

    # ------------------------------------------------------------ navigation (0.78)

    def zoom_window(self):
        """View ▸ Zoom window (Ctrl+Shift+W): a box fills the view; then the tool used before comes back."""
        back = self.tool.name if self.tool is not None and self.tool.name != "zoom_window" else "select"
        self.tools["zoom_window"].back_to = back
        self.set_tool("zoom_window")

    def zoom_selection(self):
        """View ▸ Zoom to the selection (Shift+F): what is selected fills the view (nothing: all)."""
        ids = list(self.viewport.selection)
        if not ids and self.viewport.selected_axes:
            self.viewport.zoom_extents()
            return
        self.viewport.zoom_extents(ids or None)
        if not ids:
            self.message(t("info.zoom_all_no_selection"))

    def view_back(self):
        if not self.viewport.view_back():
            self.message(t("info.no_view_back"))

    def view_forward(self):
        if not self.viewport.view_forward():
            self.message(t("info.no_view_forward"))

    def set_mouse_scheme(self, middle):
        """What the middle button does: "orbit" (as SketchUp; Shift: pan) or "pan" (as Revit; Shift: orbit).
        Kept for next time."""
        self.viewport.middle_drag = middle
        (self.act_mouse_revit if middle == "pan" else self.act_mouse_sketchup).setChecked(True)
        QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue("navegacao/botao_do_meio", middle)
        self.message(t("info.mouse_revit" if middle == "pan" else "info.mouse_sketchup"))

    def set_theme(self, name):
        """(0.338) Visualizar ▸ Tema: the interface light or dark, at once — the Qt windows by the palette, the
        window's own pieces restyled, every icon in the theme's ink. Kept on this computer (not in the project)."""
        if name == theme.NAME and name != theme.CUSTOM:
            self._check_theme()
            return
        theme.apply(name, remember=True)
        self._restyle()
        self._check_theme()
        self._tint_views()
        self._tool_cursor()                               # (0.526) the tool's cursor in the theme's colours
        self.message(t("info.theme_" + theme.NAME))

    def _tint_views(self):
        """(0.374) The views' light ground in the palette's drawing-area colour (the study's «canvas»)."""
        from ..render import canvas as views_canvas
        views_canvas.set_tint(theme.C.get("palette", {}).get("canvas"))
        vp = self.viewport
        if hasattr(vp, "refresh_ground"):                 # (0.393: the ground grid with it, from that colour)
            vp.refresh_ground()

    def theme_menu(self, show=True):
        """(0.376, the owner: «não consegui ver os temas, onde estão as opções?») The header's palette button: every
        theme — light, dark, the study's five —, «Explorar cores…» and the dark views, under it. The menu (show=False:
        not opened, for the tests)."""
        menu = QtWidgets.QMenu(self)
        menu.addActions([self.act_theme_light, self.act_theme_dark])
        menu.addSeparator()
        menu.addActions([self.act_theme_bege, self.act_theme_pedra, self.act_theme_escuro,
                         self.act_theme_grafite, self.act_theme_revit])
        menu.addSeparator()
        menu.addActions([self.act_theme_studio, self.act_canvas_dark])
        menu.addSeparator()                               # (0.446) how drawing looks: as Revit's, as the addon's
        menu.addActions([self.act_draw_revit, self.act_draw_addon])
        if show:
            button = self.header.buttons.get("theme")
            menu.exec(button.mapToGlobal(QtCore.QPoint(0, button.height())) if button is not None
                      else QtGui.QCursor.pos())
            menu.deleteLater()
        return menu

    def dock_titles(self):
        """(0.374) The panels' titles in the study's header colour (white on it), with a study palette; as Qt draws
        them with the others."""
        head = theme.C.get("panel_head")
        mark = "/* study */"                          # (only this rule is put or taken: a panel's own sheet stays)
        rule = mark + (("QDockWidget { color: %s; } QDockWidget > QWidget { color: %s; }"
                        "QDockWidget::title { background: %s; padding: 5px 8px; }")
                       % (theme.C.get("panel_head_text", theme.C["text"]), theme.C["text"], head) if head else "")
        for dock in self.findChildren(QtWidgets.QDockWidget):
            sheet = dock.styleSheet()
            new = sheet.split(mark)[0] + rule
            if new != sheet:
                dock.setStyleSheet(new)

    def _check_theme(self):
        """The theme in use ticked (the program's two, the study's five; the owner's own palette: none)."""
        act = getattr(self, "act_theme_" + theme.NAME, None)
        for other in [self.act_theme_light, self.act_theme_dark] + [getattr(self, "act_theme_" + n)
                                                                    for n in theme.STUDY]:
            other.setChecked(other is act)

    def explore_colours(self):
        """(0.374, the study's «Explorar cores») The nine colours of the interface, tuned live and kept on this
        computer: from one of the study's palettes, each colour by its picker or its code."""
        from .theme_studio import ThemeStudio
        studio = ThemeStudio(self)
        self._theme_studio = studio
        studio.show()
        return studio

    def set_dark_views(self, on):
        """(0.341) Visualizar ▸ Tema ▸ Vistas escuras: the views' background dark (the 3D view, the plans, sections and
        elevations; what is grey turned over: the lines and texts light, white and grey faces dark) or light, at once.
        Kept on this computer. The sheets and what is exported stay on paper."""
        on = bool(on)
        self.act_canvas_dark.setChecked(on)
        theme.set_dark_views(on)
        if self.viewport.set_canvas(on):
            self.message(t("info.canvas_dark" if on else "info.canvas_light"))

    # ------------------------------------------------------------ the Verifier (0.417)

    def verify_settings(self):
        """«Regulamentos do projeto…»: the country, the building's use, the kind of work, its height — one undo step;
        the check made again."""
        from ..verify import check as check_mod
        from ..verify import measures as ms
        from ..verify import reader, urban
        from . import verify_settings as dialog
        height, _n = check_mod._building_height(self.doc)
        current = self.verifier.settings()
        lot = self.doc.ifc.lot()                   # (0.423: the lot and what is built on it, for the plan's page)
        summary = urban.summary(ms.Context(self.doc, reader.read(self.doc), current)) if lot is not None else {}
        answer = dialog.ask(self, current, height, lot, summary)
        if answer is None:
            return None
        values, fronts = answer
        merged = dict(current)                     # (0.418: the exceptions kept)
        merged.update(values)
        bim.set_verify_settings(self.doc, merged)
        if lot is not None and fronts is not None and sorted(fronts) != (sorted(lot["fronts"]) if lot["chosen"] else []):
            bim.set_lot_fronts(self.doc, fronts)
        self.verifier.run()
        return merged

    def show_verify_panel(self):
        """(0.418) The Verification panel shown (in front of the panels beside it), the check as it is now."""
        self.verify_panel.show()
        self.verify_panel.raise_()
        self.verifier.run()

    def verify_exception(self, finding, why):
        """(0.418) A failure accepted as an exception (why: the reason, kept in the project), or the exception taken
        away (why None). One undo step."""
        import datetime
        settings = dict(self.verifier.settings())
        exceptions = dict(settings.get("exceptions") or {})
        if why is None:
            exceptions.pop(finding.key, None)
        else:
            exceptions[finding.key] = {"why": why, "when": datetime.date.today().isoformat(),
                                       "rule": finding.rule.id, "subject": finding.subject.name}
        settings["exceptions"] = exceptions
        bim.set_verify_settings(self.doc, settings)
        self.verifier.run()

    def rules_editor(self):
        """(0.426) «Editor de regulamentos…»: the packs of rules, the program's and the architect's; the check made
        again with them after."""
        from . import rules_editor
        self._rules_dialog = rules_editor.RulesEditor(self)
        try:
            self._rules_dialog.exec()
        finally:
            self._rules_dialog = None
        self.verifier.run()

    def verify_sheet(self, path=None):
        """(0.425) «Ficha de verificação…»: the sheet for the permit file — as a PDF or an XLSX (by the name chosen).
        Returns its path, or None."""
        from ..verify import check as check_mod
        from ..verify import project
        from ..verify import sheet as sheet_mod
        from . import report_pdf
        settings = self.verifier.settings()
        if not settings.get("country") or not project.active(settings):
            self.message(t("sheet.none"), warning=True)
            return None
        path = path or getattr(self, "_sheet_path", None)       # (the GUI test answers the dialog)
        if path is None:
            base = os.path.splitext(self.doc.path)[0] if self.doc.path else os.path.join(_documents_dir(), "projeto")
            path, chosen = QtWidgets.QFileDialog.getSaveFileName(self, t("sheet.save_title"),
                                                                 base + " - ficha de verificação.pdf",
                                                                 t("sheet.filter"))
            if not path:
                return None
            if not os.path.splitext(path)[1]:
                path += ".xlsx" if "xlsx" in (chosen or "") else ".pdf"
        try:
            data = sheet_mod.sheet(self.doc, settings, check_mod.check(self.doc, settings))
            if path.lower().endswith(".xlsx"):
                sheet_mod.write_xlsx(path, data)
            else:
                report_pdf.html_to_pdf(sheet_mod.page(data), path)
        except Exception as e:                                  # noqa: BLE001 (said, never a crash)
            self.message(t("sheet.failed", e=e), warning=True)
            return None
        self.message(t("sheet.saved", path=path))
        return path

    def _verify_goto(self, finding):
        """«Ir para»: the plan of the storey of what fails, it chosen and framed (a room, a door; a dwelling's rooms)."""
        s = finding.subject
        rooms = [g for g in s.elements if self.doc.ifc.by_guid(g) is not None and
                 self.doc.ifc.by_guid(g).is_a("IfcSpace")]
        storey = s.storey or (self.doc.ifc.space_storey(rooms[0]) if rooms else None)
        if storey:
            self.set_active_storey(storey)
            self.open_view("plan", storey)
        vp = self.viewport
        if rooms:
            infos = [self.doc.ifc.space_info(g) for g in rooms]
            pts = np.array([p for info in infos if info for p in info["outline"]], dtype=float)
            vp.select_rooms(set(rooms))
            if len(pts):
                level = infos[0]["level"] if infos[0] else 0.0
                lo, hi = pts.min(axis=0), pts.max(axis=0)
                vp.zoom_box((np.array((lo[0] - 1.0, lo[1] - 1.0, level)), np.array((hi[0] + 1.0, hi[1] + 1.0,
                                                                                  level + 1.0))))
        else:
            ids = {g for g in s.elements if self.doc.get(g) is not None}
            if ids:
                vp.set_selection(ids)
                vp.zoom_extents(ids)
        self.canvas.setFocus()

    def _restyle(self):
        """(0.338) The window's own pieces in the theme in use: the header, the ribbon (its buttons made again), the
        contextual bar, the modules' bar, the properties, the balloon; every icon in the theme's ink."""
        self.header.restyle()
        if hasattr(self, "tree_panel"):
            self.tree_panel.restyle()                     # (0.527) its active tab lit, its categories' hatch
        self.header_bar.setStyleSheet(ribbon.header_bar_style())
        self.ribbon_bar.setStyleSheet(ribbon.ribbon_style())
        self.context_bar.setStyleSheet(context_bar.style())
        self.module_bar.setStyleSheet(self._modules_style())
        self.notice.restyle()
        if getattr(self, "verifier", None) is not None:      # (0.417)
            self.verifier.restyle()
        self.share_label.setStyleSheet(self._share_style())
        self.vcb.setStyleSheet(self._vcb_style())
        theme.retheme_icons(self)
        if self.ribbon_tab is not None:
            self._fill_ribbon()
        self.dock_titles()                                 # (0.374: before the panels are made again in the theme)
        self.props.restyle()
        self.quick.restyle()                               # (0.354)
        for panel in (getattr(self, "program_panel", None), getattr(self, "materials_panel", None),
                      getattr(self, "presentation_mode", None)):                                         # (0.479)
            if panel is not None:                          # (0.357; 0.363: their notes, the thumbnails' cards; 0.474:
                panel.restyle()                            # the Materials panel's notes)
        if getattr(self, "_help", None) is not None:       # (the Help panel, once F1 made it)
            self._help.restyle()
        if getattr(self, "start_page", None) is not None:  # (0.387)
            self.start_page.restyle()
        if getattr(self, "views", None) is not None:       # (0.403) the start page's house, in the theme's text colour
            self.views.retheme()
        # a widget with a style sheet of its own keeps the palette it was polished with (the footer's storey, a bold
        # title): its sheet set again, it takes the theme's
        for w in [self] + self.findChildren(QtWidgets.QWidget):
            sheet = w.styleSheet()
            if sheet:
                w.setStyleSheet(sheet)
            w.update()

    def set_environment(self, env, remember=True):
        """The work environments of 0.84 (Concept, BIM, Structure, Docs) are now disciplines (0.182): the one
        that took each's place."""
        self.set_discipline(ribbon.OLD.get(env, env), remember)

    def set_discipline(self, discipline, remember=True):
        """The discipline (0.182, the header's tabs): the ribbon shows its tools (the keys of the others keep
        working; the tool in use goes on). Kept for next time. (0.298) "ctx:walls": the contextual tab's, while
        there is one — not kept."""
        if discipline.startswith("ctx:"):
            if discipline[4:] != self.context_tab:
                return
            self._show_ribbon(discipline)
            return
        discipline = ribbon.OLD.get(discipline, discipline)
        if discipline not in ribbon.DISCIPLINES:
            discipline = ribbon.DEFAULT
        if discipline == self.discipline and self.ribbon_tab == discipline:
            return
        self.discipline = discipline
        self.disc_actions[discipline].setChecked(True)
        self._show_ribbon(discipline)
        if remember:
            QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue("disciplina/atual", discipline)
        # (0.321: no more a line saying what the discipline is for — its tab's tip says it: it hid the tool's step)

    def _show_ribbon(self, tab):
        """The ribbon with a discipline's panels, or a contextual tab's ("ctx:walls"); its tab lit."""
        self.header.show_discipline(tab)
        if tab != self.ribbon_tab:
            self.ribbon_tab = tab
            self._fill_ribbon()

    def _update_context_tab(self):
        """(0.298) The contextual tab follows the selection, as Revit's "Modify | Walls": walls selected — it comes
        and is shown; none — it goes, and the discipline it took over from is shown again."""
        if not hasattr(self, "header"):
            return
        wanted = "walls" if any(isinstance(i, str) and self.doc.ifc.kind_of(i) in ("wall", "curved_wall")
                                for i in self.viewport.selection) else None
        if wanted == self.context_tab:
            return
        self.context_tab = wanted
        if wanted is None:
            self.header.set_context(None)
            if self.ribbon_tab is not None and self.ribbon_tab.startswith("ctx:"):
                self._show_ribbon(self.discipline)
            return
        self.header.set_context(wanted, t("ctxtab." + wanted), t("tip.ctxtab." + wanted))
        self._show_ribbon("ctx:" + wanted)

    def ribbon_item(self, name):
        """What a name of the ribbon stands for: a tool's action, one of the window's (act_<name>), or a menu."""
        if name in self.tool_actions:
            return self.tool_actions[name]
        menus = {"classify": self.classify_menu, "type_lists": self.type_lists_menu, "phase": self.phase_menu,
                 "panels": self.panels_menu}
        return menus.get(name) or getattr(self, "act_" + name, None)

    def ribbon_actions(self):
        """The commands on the ribbon now: each button's action (or its dropdown's menu), folded panels' too."""
        return [item for _name, item in getattr(self, "_ribbon_items", [])]

    def _ribbon_button(self, name, item, small):
        """A button of the ribbon: large, an icon over a short name; (0.298) small, an icon beside its name in one
        line. A command with no icon of its own gets its initials."""
        button = ribbon.RibbonButton()
        button.setObjectName(name)
        button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon if small
                                  else QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setIconSize(QtCore.QSize(16, 16) if small else self.ribbon_bar.iconSize())
        button.setProperty("small", small)
        if isinstance(item, QtWidgets.QMenu):
            # a click shows the window's menu under the button — not setMenu: PySide would take the menu down with
            # the button when the ribbon is filled again
            text = item.title()
            button.clicked.connect(lambda _=False, b=button, m=item: m.exec(
                b.mapToGlobal(QtCore.QPoint(0, b.height()))))
            button.setIcon(icons.bim_icon() if name == "classify" else
                           ribbon.command_icon(name) or ribbon.stand_in_icon(text))
            button.setToolTip(text)
        else:
            text = t("tool." + name) if name in self.tool_actions else item.text()
            button.setDefaultAction(item)
            if item.icon().isNull():
                button.setIcon(ribbon.command_icon(name) or ribbon.stand_in_icon(text))
        if small:
            label = "rib.small." + name
            button.setText(t(label) if i18n_has(label) else ribbon.small_label(
                t("rib.short." + name) if i18n_has("rib.short." + name) else text))
        else:
            short = "rib.short." + name                          # (a shorter name under the icon)
            button.setText(t(short) if i18n_has(short) else ribbon.short_label(text))
        from .art_icons import icon as art_icon          # (0.535: the pictures as Revit's — large and small alike)
        drawn = art_icon(name)
        if drawn is not None:
            button.setIcon(drawn)
        button.keep()
        return button

    def _fill_ribbon(self):
        """The ribbon: the discipline's (or the contextual tab's) panels, each its buttons over its name (0.298)."""
        panels, self._ribbon_items = [], []
        for key, items in ribbon.panels_of(self.ribbon_tab):
            columns, entries, icon = [], [], None
            for entry in items:
                if isinstance(entry, list):               # (0.482) a large button with an arrow, as Revit's «Roof ▾»
                    found = [(n, self.ribbon_item(n)) for n in entry]
                    found = [(n, item) for n, item in found if item is not None]
                    if not found:
                        continue
                    button = self._ribbon_button(found[0][0], found[0][1], False)
                    if len(found) > 1:
                        menu = QtWidgets.QMenu(button)    # (the button's own: made again with the ribbon)
                        for _n, item in found[1:]:
                            menu.addAction(item.menuAction() if isinstance(item, QtWidgets.QMenu) else item)
                        button.setMenu(menu)
                        button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.MenuButtonPopup)
                        button.setProperty("arrow", True)          # (its look: ribbon.ribbon_style)
                    columns.append(button)
                    for name, item in found:
                        entries.append(item)
                        self._ribbon_items.append((name, item))
                    if icon is None:
                        icon = button.icon()
                    continue
                names = entry if isinstance(entry, tuple) else (entry,)
                column = []
                for name in names:
                    item = self.ribbon_item(name)
                    if item is None:
                        continue
                    button = self._ribbon_button(name, item, isinstance(entry, tuple))
                    column.append(button)
                    entries.append(item)
                    self._ribbon_items.append((name, item))
                    if icon is None:
                        icon = button.icon()
                if column:
                    columns.append(column if isinstance(entry, tuple) else column[0])
            if columns:
                panels.append(ribbon.Panel(t("rpanel." + key), columns, icon, entries))
        self.ribbon.show_panels(panels)

    def _load_mouse_scheme(self):
        middle = QtCore.QSettings("ArqSynth", "ArqSynth BIM").value("navegacao/botao_do_meio", "orbit")
        middle = middle if middle in ("orbit", "pan") else "orbit"
        self.viewport.middle_drag = middle
        (self.act_mouse_revit if middle == "pan" else self.act_mouse_sketchup).setChecked(True)

    def set_view(self, kind):
        """The 3D view's tab (the one shown last), looking from that side ("iso" F8, "top" F2, "front" F3)."""
        self.views.open(self._live_3d())
        self.viewport.set_view(kind)

    def _live_3d(self):
        """The 3D view shown last — the 3D view itself if that one is gone (deleted, undone)."""
        if not self._view_exists(self._current_3d):
            self._current_3d = view_tabs.THREE_D
        return self._current_3d

    def new_view3d(self):
        """View ▸ New 3D view: the 3D view as it is now (camera, look, section box) kept under a name
        ("3D 1"), listed in the Project panel, in a tab of its own (0.64)."""
        if self.viewport.cutting():
            self.views.open(self._live_3d())
        camera = self.viewport.camera_snapshot()
        props = {k: v for k, v in self.doc.view_props.get(self._live_3d(), {}).items()
                 if k in templates_model.LOOK_FIELDS}
        key = self.doc.add_view3d(camera, props)
        self.views.cameras[key] = camera
        self.views.open(key)
        self.message(t("info.view3d_new", name=self.doc.view3d(key[1]).name))
        return key

    def _left_view(self, key, camera):
        """A view left or closed: a named 3D view keeps where its camera was (saved with the project)."""
        if key[0] == "3d" and len(key) > 1:
            self.doc.keep_view3d_camera(key[1], camera)

    def _grid_action(self, action, index, tag=None):
        """The Project panel: an axis of the structural grid given another tag, or deleted (0.67)."""
        if action == "rename":
            tag = (tag or "").strip()
            if 0 <= index < len(self.doc.grids) and tag != self.doc.grids[index].tag:
                if not bim.rename_grid_axis(self.doc, index, tag):
                    self.message(t("err.grid_tag", tag=tag), warning=True)
                    self._refresh_tree()
        elif action == "remove":
            bim.remove_grid_axis(self.doc, index)

    def _view3d_action(self, action, uid, name=None):
        """The Project panel: a new named 3D view, one renamed or removed."""
        if action == "new":
            self.new_view3d()
        elif action == "rename":
            self._rename_view3d(uid, name)
        elif action == "remove":
            self._remove_view3d(uid)

    def _rename_view3d(self, uid, name):
        if not self.doc.rename_view3d(uid, name):
            self.message(t("err.view_name", name=name), warning=True)
        self.views.refresh(self._view_exists)

    def _remove_view3d(self, uid):
        self.doc.remove_view3d(uid)

    def _show_3d(self):
        if self.viewport.plan:
            self._show_plan(False)
        else:
            if self.viewport.section is not None:
                self.viewport.set_section(None, None)
                self._refresh_storeys()
            self._apply_view(None)                 # (the 3D view's own properties)

    def _show_view(self, key):
        """Show a view (its tab was chosen): the 3D view, a storey's plan, a section, an elevation,
        a sheet (the sheet's page instead of the 3D canvas)."""
        self._stop_drawing()
        self._props_sheet = None                    # (0.470: a sheet chosen in the navigator: no longer)
        kind = key[0]
        mode = self.presentation_mode
        if mode is not None and mode.active and kind != "presentation":
            mode.leave()                           # (0.479: the BIM's columns back as they were)
        if kind == "start":                        # (0.387) the start page: the side panels step aside
            if self.start_page is None:
                self.start_page = self._make_start_page()
            self.canvas.hide()
            if self.sheet_window is not None:
                self.sheet_window.hide()
            self.schedules_panel.hide()                # (0.477: a table's page)
            # (0.476) the side panels aside first: the page shown beside them asked for its width and theirs at once
            # (1 258 + 610 px) — the window grew past the screen, to 2 039 px, and never shrank back
            self._step_docks_aside(True)
            self.start_page.refresh()
            self._start_scroll.show()
            self._tick_plan(False)
            return
        if self.start_shown():
            self._start_scroll.hide()
            self._step_docks_aside(False)
            self.canvas.show()                     # (a sheet's branch below hides it again)
        if kind == "table":                        # (0.477) a table, in place of the canvas as a sheet
            self.canvas.hide()
            if self.sheet_window is not None:
                self.sheet_window.hide()
            sp = self.schedules_panel
            sp.doc = self.doc
            sp.show()
            sp.show_ref(key[1])
            self._tick_plan(False)
            self._refresh_properties()
            self.refresh_context_bar()
            if hasattr(self, "tables_panel"):
                self.tables_panel.mark(key[1])
                self._tables_insert()
            return
        if self.table_shown():
            self.schedules_panel.hide()
            self.canvas.show()
            self.refresh_context_bar()
            self._tables_insert()                      # (0.478: nothing to insert in)
        if kind == "sheet":
            sheet = next((s for s in self.doc.sheets if s.uid == key[1]), None)
            if sheet is not None:
                if self.sheet_window is None:
                    self.sheet_window = sheet_view.SheetWindow(self, self.centralWidget())
                    self._central_layout.addWidget(self.sheet_window, 1)
                self.canvas.hide()
                self.sheet_window.show()
                self.sheet_window.show_sheet(sheet)
            self._tick_plan(False)
            self._refresh_properties()
            self.refresh_context_bar()             # (0.472: the sheet's commands on the parameters' bar)
            return
        if self.sheet_shown():
            self.sheet_window.hide()
            self.canvas.show()
            self.refresh_context_bar()
        self.canvas.setFocus()
        self.viewport.redraw()
        if kind == "presentation":                 # (0.479) the ArqSynth Presentation tab: its columns, the 3D view
            self._current_3d = view_tabs.THREE_D   # (the 3D view's look: its own, under what the tab chooses)
            mode.enter()
            self._show_3d()
            self._refresh_properties()
            QtCore.QTimer.singleShot(0, lambda: mode.show_state() if mode.active else None)
            return
        if kind == "plan":
            if key[1] != self.doc.active_storey and any(g == key[1] for g, _n, _z in self.doc.storeys()):
                self.doc.set_active_storey(key[1])
            self._show_plan(True)
        elif kind == "section":
            self._show_section(next((k for k, s in enumerate(self.doc.sections) if s.name == key[1]), None))
        elif kind == "elevation":
            self._show_elevation(key[1])
        else:
            self._current_3d = tuple(key)
            self._show_3d()
        self._refresh_properties()                 # (nothing selected: this view's properties)

    # ------------------------------------------------------------ the start page (0.387)

    def _make_start_page(self):
        from . import start_page
        page = start_page.StartPage(self.centralWidget(), _documents_dir())
        page.on_new = self.new_document
        page.on_open = self.open_file
        page.on_open_path = self.open_recent
        page.on_base = self.new_from_base
        page.on_help = lambda tab: self.show_help(tab)
        page.on_show = self.show_command            # (0.406) «Mostrar onde está» of the tutorial read on the page
        page.on_message = self.message
        # (0.476) in a scroll area, as a web page: its five columns ask for 1 258 px; laid in the window itself, that
        # width (and with the side panels coming back, more) made the window grow past the screen and stay so —
        # narrower than the page, it scrolls instead
        scroll = QtWidgets.QScrollArea(self.centralWidget())
        scroll.setObjectName("start_scroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setWidget(page)
        scroll.hide()
        self._central_layout.addWidget(scroll, 1)
        self._start_scroll = scroll
        return page

    def show_start_page(self):
        """Início ▸ Página inicial (and when the program starts): the start page's tab."""
        self.views.open(view_tabs.START)
        return self.start_page

    def start_shown(self):
        return self.start_page is not None and not self._start_scroll.isHidden()

    def _step_docks_aside(self, aside):
        """The side panels hidden while the start page is in front (all its columns in the window), shown again
        after."""
        if aside:
            if self._docks_hidden is None:
                self._docks_hidden = [d for d in self.findChildren(QtWidgets.QDockWidget) if d.isVisible()]
                for d in self._docks_hidden:
                    d.hide()
                # (the tabs of panels in a group stayed over the page: Qt leaves their bar shown)
                for bar in self.findChildren(QtWidgets.QTabBar, options=QtCore.Qt.FindChildOption.FindDirectChildrenOnly):
                    if bar is not self.view_bar:
                        bar.hide()
        elif self._docks_hidden is not None:
            for d in self._docks_hidden:
                d.show()
            self._docks_hidden = None

    def open_recent(self, path):
        """A recent document clicked: opened (one that is not there any more taken off the list)."""
        from . import recent
        if not os.path.exists(path):
            recent.remove(path)
            self.message(t("info.recent_missing", f=os.path.basename(path)), warning=True)
            if self.start_page is not None:
                self.start_page.refresh()
            return False
        if not self._confirm_discard():
            return False
        return self.open_path(path)

    def base_folder(self):
        from . import start_page
        return start_page.base_folder(_documents_dir())

    # ------------------------------------------------------------ (0.391) the Paint bucket's browser

    def open_paint_browser(self, on, key):
        """While the Paint bucket is on (0.468: the column's Materials panel): its pictures in view, «Sem pintura»
        first, the bucket's marked — one click chooses."""
        editor = self.materials_panel.editor
        editor.set_painting(on)
        if on:
            self._left_up(self.materials_panel)
            editor.tabs.setCurrentIndex(0)
            editor.mark(key)

    def show_paint_material(self, key):
        self.materials_panel.editor.mark(key)

    def paint_bar_changed(self):
        self._sync_context_bar()

    def choose_image(self):
        """(0.389) A picture for a perforated panel's holes (dark: big holes): its path, or ""."""
        from ..model.image_masks import IMAGE_FILTER
        start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("dlg.mask_image"), start,
                                                        "{} ({})".format(t("dlg.images"), IMAGE_FILTER))
        return path or ""

    def new_from_base(self, path=None):
        """(0.387) Ficheiro ▸ Novo a partir de arquivo base: a base file (a template) opened as a new project — the
        same walls, types, storeys, sheets…, saved under another name (Gravar asks for one)."""
        if path is None:
            start = self.base_folder() if os.path.isdir(self.base_folder()) else _documents_dir()
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("act.new_from_base"), start, t("file.filter"))
            if not path:
                return False
        if not self._confirm_discard():
            return False
        if not self.open_path(path, remember=False):
            return False
        self.doc.path = None                       # (a new project: saved under a name of its own)
        self.doc.modified = False
        self._update_title()
        self.message(t("info.new_from_base", f=os.path.basename(path)))
        return True

    def _remember_file(self, path, picture=True):
        """(0.387) The document among the recent ones, with a picture of its view (the start page's list)."""
        from . import recent
        try:
            recent.add(path)
            if picture and self.canvas.isVisible():
                recent.save_thumb(path, self.viewport.snapshot())
        except Exception:                          # noqa: BLE001 — a list of conveniences: never in the way
            return

    def _view_tab_label(self, key):
        if key[0] == "start":
            return t("tab.start")
        if key[0] == "presentation":                             # (0.479)
            return t("pmode.title")
        if key[0] == "3d":
            view = self.doc.view3d(key[1]) if len(key) > 1 else None
            return view.name if view is not None else t("tab.3d")
        if key[0] == "sheet":
            return next((s.name for s in self.doc.sheets if s.uid == key[1]), t("sheet.window"))
        if key[0] == "table":                                    # (0.477)
            self.schedules_panel.doc = self.doc
            return t("tab.table", name=self.schedules_panel.title_of(key[1]))
        return self.view_label(key[0], key[1])

    def _view_exists(self, key):
        """Is that view still there (its storey, its section, its sheet)?"""
        if key[0] == "plan":
            return key[1] is None or any(g == key[1] for g, _n, _z in self.doc.storeys())
        if key[0] == "section":
            return any(s.name == key[1] for s in self.doc.sections)
        if key[0] == "sheet":
            return any(s.uid == key[1] for s in self.doc.sheets)
        if key[0] == "table":                                    # (0.477) a category's, or the project's own
            ref = str(key[1])
            return ref in schedules_model.CATEGORIES or any("def:" + d.uid == ref for d in self.doc.schedule_defs)
        if key[0] == "3d" and len(key) > 1:
            return self.doc.view3d(key[1]) is not None
        return True

    def _tick_plan(self, on):
        """The F4 tick: whether a plan is shown."""
        if self.act_plan.isChecked() != on:
            self.act_plan.blockSignals(True)
            self.act_plan.setChecked(on)
            self.act_plan.blockSignals(False)

    def sheet_shown(self):
        """A sheet's tab is shown (not the 3D canvas)."""
        return self.sheet_window is not None and not self.sheet_window.isHidden()

    def table_shown(self):
        """(0.477) A table's tab is shown (not the 3D canvas)."""
        return hasattr(self, "schedules_panel") and not self.schedules_panel.isHidden()

    def presentation_shown(self):
        """(0.479) The ArqSynth Presentation tab is in front (its columns instead of the BIM's)."""
        return getattr(self, "presentation_mode", None) is not None and self.presentation_mode.active

    def show_presentation_tab(self):
        """(0.479) The ArqSynth Presentation's interface in front — (0.481) its tab opened (the last one) by the left
        bar's icon; the view it came from remembered."""
        current = self.views.current()
        if current is not None and current != view_tabs.PRESENT:
            self.presentation_mode.came_from = current
        self.views.open(view_tabs.PRESENT)
        return self.presentation_mode

    def close_presentation(self):
        """(0.481) The ArqSynth Presentation's interface put away: its tab closed, the view it came from shown again
        (the BIM's columns as they were)."""
        if view_tabs.PRESENT not in self.views.keys:
            return False
        back = getattr(self.presentation_mode, "came_from", None)
        if back is None or back not in self.views.keys:
            back = self._live_3d()
        self.views.open(back)                       # (the view it came from first: no other tab shown on the way)
        self.views.close(self.views.keys.index(view_tabs.PRESENT))
        return True

    def thumbnail_now(self):
        """(0.479) A scene's thumbnail (JPEG bytes) of the 3D view as it is now."""
        return _thumbnail_jpeg(self.viewport.render_image(THUMB_RENDER_PX))

    # ------------------------------------------------------------ (0.477) the tables, in their tabs

    def open_table(self, ref=None):
        """A table in its tab over the canvas: `ref` a category's key or "def:<uid>" (None: the one last shown, at
        first the walls')."""
        ref = ref or self.schedules_panel.ref() or "walls"
        self.views.open(("table", ref))
        return self.schedules_panel

    def toggle_table(self):
        """Ctrl+T: the table last shown in its tab — or, a table's tab in view, it closed (as the panel it was)."""
        current = self.views.current()
        if current is not None and current[0] == "table":
            self.views.close_current()
            return None
        return self.open_table()

    def _table_ref_shown(self, ref):
        """The table page shows another table (chosen there): its tab follows, the side panel marks it."""
        if self.table_shown():
            current = self.views.current()
            if current is None or current[0] != "table" or current[1] != ref:
                self.views.retarget(("table", ref))
            self.refresh_context_bar()
        if hasattr(self, "tables_panel"):
            self.tables_panel.mark(ref)
            self._tables_insert()

    def new_table(self, category="walls"):
        """Nova tabela… (as Revit's New Schedule): a table of the project's own of that category — its Properties
        asked (name, fields, filter, sort…) and, on OK, opened in its tab."""
        category = category if category in schedules_model.CATEGORIES else "walls"
        self.open_table(category)
        defn = schedules_model.ScheduleDef(t("sched.untitled"), category, list(schedules_model.available(category)))
        self.schedules_panel.edit_schedule(defn)
        return self.schedules_panel

    def table_properties(self, ref):
        """A table's Propriedades… (its tab opened first)."""
        self.open_table(ref)
        self.schedules_panel.properties()

    def duplicate_table(self, ref):
        """Duplicar: a table of the project's own like this one (a category's: its columns), opened. One undo step."""
        own = next((d for d in self.doc.schedule_defs if "def:" + d.uid == ref), None)
        if own is not None:
            copy_ = schedules_model.def_from_dict(dict(schedules_model.def_to_dict(own), uid=None))
            copy_.name = t("tables.copy_name", name=own.name)
        elif ref in schedules_model.CATEGORIES:
            copy_ = schedules_model.ScheduleDef(t("sched.cat." + ref), ref, list(schedules_model.available(ref)))
        else:
            return None
        self.doc.execute(schedules_model.SetScheduleDefs(self.doc.schedule_defs, self.doc.schedule_defs + [copy_],
                                                         t("cmd.schedules")))
        self.open_table("def:" + copy_.uid)
        return copy_

    def delete_table(self, ref):
        """Apagar a table of the project's own (its tab closed). One undo step."""
        if not any("def:" + d.uid == ref for d in self.doc.schedule_defs):
            return False
        self.doc.execute(schedules_model.SetScheduleDefs(
            self.doc.schedule_defs, [d for d in self.doc.schedule_defs if "def:" + d.uid != ref], t("cmd.schedules")))
        self.views.refresh(self._view_exists)
        self.message(t("info.table_deleted"))
        return True

    def export_table(self, ref):
        """Exportar… a table (opened in its tab first): Excel, CSV or JSON for other programs (KazaFix Cost)."""
        self.open_table(ref)
        self.schedules_panel._export()

    def _refresh_tables_panel(self):
        if hasattr(self, "tables_panel") and self.tables_panel.isVisible() and not self.doc.loading:
            self.tables_panel.show_document(self.doc, self.schedules_panel.ref() if self.table_shown() else None)
            self._tables_insert()

    def _tables_insert(self):
        """(0.478) The side panel's «Inserir na tabela» for the table in view: a table of the project's — the fields it
        does not show, functions, the project's data, rows; a category's list — «Formatar como no Excel»."""
        if not hasattr(self, "tables_panel"):
            return
        sp = self.schedules_panel
        state = None if not self.table_shown() else ("own" if sp._own() is not None else "list")
        fields = [(k, t("sched.col." + k)) for k in sp.free_fields()] if state == "own" else ()
        self.tables_panel.show_insert(state, fields)

    def _delete(self):
        """Delete: on a sheet, the view picked there comes off the sheet (nothing of the model is
        deleted); else what the tool has selected."""
        if self.sheet_shown():
            if self.sheet_window.editor is not None:                          # (0.473) the title block drawn
                self.sheet_window.editor.delete_picked()
            elif self.sheet_window.canvas.selected is not None:
                self.sheet_window.take_off(self.sheet_window.canvas.selected)
            elif self.sheet_window.picked_import is not None:                 # (0.472) a drawing from outside
                self.sheet_window.take_off_import(self.sheet_window.picked_import)
            return
        if self.table_shown() and self.schedules_panel.clear_cells():          # (0.478) a title's, a note's… cleared
            return
        if self.pick_request is not None:         # (0.325) Delete while a command waits: only its own (Apagar)
            if self.pick_request.title == self._delete_title():
                self.finish_pick()
            return
        vp = self.viewport
        volume = self.presentation_mode is not None and self.presentation_mode.chosen_volume() is not None   # (0.492)
        if self.tool.name == "select" and not volume and not (
                vp.selection or vp.face_selection or vp.line_selection or vp.selected_dims or vp.selected_annotations
                or vp.selected_axes or vp.selected_rooms):
            self.ask_pick(self._delete_title(), t("pick.delete"), lambda i: self.doc.get(i) is not None,
                          lambda: self.tool.delete())             # (0.325, as Revit's: what to delete, asked for)
            return
        self.tool.delete()

    def _delete_title(self):
        return self.act_delete.text().split("   (")[0].strip()

    def _rename_section(self, index, name):
        """The Project panel renames a section: its tab (and the view shown) follow."""
        old = self.doc.sections[index].name if 0 <= index < len(self.doc.sections) else None
        ok = self.doc.rename_section(index, name)
        if ok and old is not None:
            new = self.doc.sections[index].name
            self.views.rename(("section", old), ("section", new))
            if self.viewport.section_view == ("section", old):
                self.viewport.section_view = ("section", new)
                self._view_name = new
                self._refresh_storeys()
        return ok

    def template_action(self, action, view=None, uid=None):
        """View templates: "edit" (View ▸ View templates…, the dialog) or "assign" a template (uid,
        None: none) to a view (Project panel ▸ right-click a view ▸ View template)."""
        if action == "edit":
            classes = {o.ifc_class for o in self.doc.objects.values() if o.is_bim}
            dialog = view_templates.TemplatesDialog(self, self.doc.templates, classes, self.doc.view_styles)
            self._templates_dialog = dialog                  # (tests fill it in)
            if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                self.doc.set_templates(dialog.templates)
                self.message(t("info.templates", n=len(dialog.templates)))
        elif action == "assign":
            self.doc.assign_template(view, uid)
            tpl = self.doc.template_of(view)
            label = self.view_label(view[0], view[1])
            self.message(t("info.template_assigned", view=label, tpl=tpl.name) if tpl is not None
                         else t("info.template_none", view=label))
        QtCore.QTimer.singleShot(0, self._refresh_view_settings)

    def save_view_template(self, view, name=None):
        """(0.414) «Guardar como modelo…»: a view template made of what this view shows now (its cut height, the
        categories it hides, its colours, scale, phases and style), given to it — the view's type, chosen on top of
        the Properties of other views. One undo step. Returns the template, or None."""
        view = tuple(view)
        if name is None:
            label = self.view_label(view[0], view[1] if len(view) > 1 else None)
            name, ok = QtWidgets.QInputDialog.getText(self, t("props.view_template_save").rstrip("…"),
                                                      t("ask.template_name"), text=label)
            if not ok or not name.strip():
                return None
        name = name.strip()
        if any(x.name.lower() == name.lower() for x in self.doc.templates):
            self.message(t("err.edit_refused", e=t("refuse.type_exists")), warning=True)
            return None
        s = self.doc.view_settings(view)
        tpl = templates_model.ViewTemplate(name, cut_height=s.cut_height, hidden=sorted(s.hidden), rule=s.rule,
                                           scale=s.scale, phases=s.phases,
                                           style=s.style if view[0] == "3d" else s.drawn_style)
        mark = self.doc.undo_mark()
        self.doc.set_templates(list(self.doc.templates) + [tpl])
        self.doc.assign_template(view, tpl.uid)
        self.doc.join_since(mark, t("cmd.view_template_save"))
        QtCore.QTimer.singleShot(0, self._refresh_view_settings)
        self._refresh_properties()
        self.message(t("info.view_template_saved", n=name))
        return tpl

    def _refresh_view_settings(self):
        """The view shown takes its template's settings again if they changed (a template was
        edited or given, an undo…)."""
        self._apply_look()
        view = self.viewport.current_view()
        settings = self.doc.view_settings(view or self._live_3d())
        plan = view is not None and view[0] == "plan"
        self.viewport.set_element_hatches(settings.elements)            # (0.331: given, put back, undone)
        underlay = (tuple(view), settings.underlay) if plan and settings.underlay else None
        if (settings.hidden != frozenset(self.viewport.hidden_classes) or settings.cut_height != self.viewport.cut_height
                or settings.hidden_phases != frozenset(self.viewport.hidden_phases)
                or settings.rule != self._template_rule
                or (settings.depth if plan else 0.0) != self.viewport.view_depth
                or (settings.crop if plan else None) != self.viewport.crop
                or settings.slopes != self.viewport.show_slopes
                or underlay != getattr(self, "_underlay_shown", None)
                or (view is not None and view[0] != "3d" and settings.drawn_style != self.viewport.cut_style)):
            self._apply_view(view)

    def _apply_underlay(self, view, settings):
        """A plan's underlay (0.65): the storey below / above drawn in grey under it (its plan, as lines)."""
        which = settings.underlay if view is not None and view[0] == "plan" else None
        other = drawings.underlay_storey(self.doc, view[1], which) if which else None
        if other is None or self.doc.loading:
            self._underlay_shown = None
            self.viewport.show_underlay()
            return
        self._underlay_shown = (tuple(view), which)
        self.viewport.show_underlay(drawings.underlay_lines(self.doc, other), self.doc.work_level())

    def _refresh_underlay(self):
        """The model changed: the underlay of the plan shown drawn again."""
        self._underlay_later = False
        if getattr(self, "_underlay_shown", None) is not None:
            view = self.viewport.current_view()
            if view is not None:
                self._apply_underlay(view, self.doc.view_settings(view))

    def _apply_look(self):
        """The 3D view's look (its properties: visual style, edges, ground grid, axonometry) — kept by the
        viewport for when the 3D view is shown (a plan or a section has its own). (0.479) The ArqSynth Presentation
        tab in front: its visual mode and its PERSP / ORTO over them."""
        s = self.doc.view_settings(self._live_3d())
        mode = self.presentation_mode
        if mode is not None and mode.active:
            self.viewport.set_look(mode.live_view_style() or s.style, s.edges, s.grid, mode.live["ortho"])
        else:
            self.viewport.set_look(s.style, s.edges, s.grid, s.axonometric)
        self.viewport.home_view = s.home                # (the view cube's house, 0.81)
        self._apply_box(s.box)                     # (its section box: a plan or a section shows its own cut)

    def _apply_view(self, view):
        """The view shown takes its template's settings (view_templates), or its own properties: the
        classes it hides, a plan's cut height, what the elements are coloured by. In 3D (None): the
        3D view's own — and colours a view had set go back to the usual ones when this one has none."""
        settings = self.doc.view_settings(view or self._live_3d())
        plan = view is not None and view[0] == "plan"
        self.viewport.view_key3d = self._live_3d()          # (0.464: its levels' ring, its own)
        self.viewport.set_view_settings(settings.hidden, settings.cut_height, settings.hidden_phases,
                                        settings.depth if plan else 0.0, settings.crop if plan else None)
        self.viewport.set_element_hatches(settings.elements)            # (0.331: its hatches by element)
        # (0.315) a plan's / section's own view style (the 3D view's is its look)
        self.viewport.set_cut_style(settings.drawn_style if view is not None and view[0] != "3d" else None)
        if settings.slopes != self.viewport.show_slopes:                # (its slope colours, 0.201)
            self.viewport.set_show_slopes(settings.slopes)
        self.act_slopes.setChecked(settings.slopes)
        self._apply_look()
        self._apply_underlay(view, settings)
        if settings.rule is not None:
            self._template_rule = settings.rule
            self.rules_panel.show_rule(settings.rule)
            if settings.rule != self.rule:
                self.apply_rule(settings.rule)
        elif self._template_rule is not None:
            self._template_rule = None
            self.rules_panel.reset()
            self.apply_rule(None)

    def show_section(self, a, b, normal):
        """A section drawn with the Section tool: it gets a name ("Corte 2", listed in the Project
        panel, saved with the project) and the view becomes it."""
        self.doc.add_section(a, normal)
        self._enter_section(self.doc.last_section)

    def last_section(self):
        """View ▸ Last section (F5)."""
        if self.doc.section is None:
            self.message(t("info.no_section"), action=self.tool_actions["section"])               # (0.324)
            return
        self._enter_section(self.doc.last_section)

    def open_view(self, kind, ref):
        """A view chosen in the Project panel (double-click): a storey's plan, a named section
        (its index), an elevation (N, S, E, W), a 3D view (None: the 3D view; a named one's uid)
        — in its tab (opened if it is not)."""
        if kind == "3d":
            key = ("3d", ref) if ref else view_tabs.THREE_D
            view = self.doc.view3d(ref) if ref else None
            if view is not None and view.camera and key not in self.views.keys:
                self.views.cameras[key] = view.camera         # (where it was left)
            self.views.open(key)
            return
        if kind == "plan":
            self.views.open(("plan", ref))
            self.set_plan(True)                   # (the F4 tick)
        elif kind == "section":
            self._enter_section(ref)
        elif kind == "elevation":
            self.show_elevation(ref)

    # ------------------------------------------------------------ team work (shared folder)

    def _central(self):
        return sharing.central_of(self.doc.path)

    def share_project(self, folder=None):
        """File ▸ Team ▸ Share the project in a folder: the project (saved first) becomes the
        central model there; from now on one works on a local copy and synchronises."""
        if not self.doc.path or self.doc.modified:
            self.save()
            if not self.doc.path or self.doc.modified:
                return                                    # (not saved: nothing to share)
        if folder is None:
            folder = QtWidgets.QFileDialog.getExistingDirectory(self, t("act.share"), os.path.dirname(self.doc.path))
            if not folder:
                return
        try:
            central = sharing.share(self.doc.path, folder)
        except FileExistsError as exc:
            self.message(t("share.exists", f=str(exc)), warning=True)
            return
        self.open_shared(central)
        self.message(t("info.shared", f=central))

    def open_shared(self, central=None):
        """File ▸ Team ▸ Open a shared project: its central model (in the shared folder) — worked
        on through a local copy (kept between sessions, with what is not synchronised yet)."""
        if central is None:
            start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
            central, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("act.open_shared"), start, t("file.filter"))
            if not central:
                return
        if not self._confirm_discard():
            return
        local = sharing.open_shared(central)
        self.open_path(local)
        self._update_title()
        self._show_share_status()

    def synchronise(self):
        """File ▸ Team ▸ Synchronise (Ctrl+Alt+S): this copy saved, merged with the central model
        (what others did comes here, what was done here goes there), and opened again."""
        central = self._central()
        if central is None:
            self.message(t("share.not_shared"), warning=True, action=self.act_share)               # (0.324)
            return
        local = self.doc.path
        self.save_to(local)
        user = _author()
        try:
            result = self.run_busy(lambda: sharing.sync(local, user), t("share.working"))
        except (TimeoutError, ValueError, OSError) as exc:
            self.message(t("share.failed", e=exc), warning=True)
            return
        if result.theirs_changed or result.views == "received":
            self.open_path(local)                          # (others' work came in: the project is read again)
        else:
            self.doc.reload_notes()                        # (nothing new in the model: Ctrl+Z keeps its history)
        parts = [t("share.sent") if result.mine_changed else t("share.nothing_sent"),
                 t("share.received") if result.theirs_changed else t("share.nothing_received")]
        if result.views:
            parts.append(t("share.views_" + result.views))
        if result.conflicts:
            parts.append(t("share.conflicts", n=len(result.conflicts)))
        self.message(t("info.synced", what="; ".join(parts)), warning=bool(result.conflicts))
        self._show_share_status()

    def reserve_views(self):
        """The views (sections, sheets, dimensions, view templates) go to the central model with
        their reservation: one person changes them at a time."""
        central = self._central()
        if central is None:
            self.message(t("share.not_shared"), warning=True, action=self.act_share)               # (0.324)
            return
        taken = sharing.Reservations(central).take(_author(), [sharing.VIEWS])
        self.message(t("share.views_taken", user=taken[sharing.VIEWS]) if taken else t("share.views_mine"),
                     warning=bool(taken))
        self._show_share_status()

    def give_back(self):
        central = self._central()
        if central is None:
            self.message(t("share.not_shared"), warning=True, action=self.act_share)               # (0.324)
            return
        sharing.Reservations(central).give_back(_author())
        self.message(t("share.given_back"))
        self._show_share_status()

    def _check_reservations(self, changed, removed):
        """Shared project: what a new command changed is reserved for this user; if someone else
        has any of it, the command is undone (they are changing it)."""
        central = self._central() if hasattr(self, "doc") else None
        cmd = self.doc.last_command() if central else None
        if cmd is None or cmd in self._checked_commands:
            return
        self._checked_commands.add(cmd)
        keys = {i for i in (changed or ()) if self.doc.get(i) is not None and self.doc.get(i).is_bim}
        keys |= {i for i in (removed or ()) if i in self._known_bim}
        if {VIEWS_CHANGED, DIMS_CHANGED, IMAGES_CHANGED, CAD_CHANGED, CLOUD_CHANGED} & set(changed or ()):
            keys.add(sharing.VIEWS)
        if not keys:
            return
        taken = sharing.Reservations(central).take(_author(), sorted(keys))
        if taken:
            who = sorted(set(taken.values()))
            QtCore.QTimer.singleShot(0, lambda: self._refuse_command(cmd, who))
        self._show_share_status()

    def _refuse_command(self, cmd, who):
        if self.doc.last_command() is cmd:
            self.doc.undo()
            self.doc._redo.clear()                        # (what was undone cannot come back)
        self.message(t("share.reserved", users=", ".join(who)), warning=True)

    def _show_share_status(self):
        central = self._central() if hasattr(self, "doc") else None
        if central is None:
            self.share_label.setVisible(False)
            return
        mine = [k for k, (u, _s) in sharing.Reservations(central).read().items() if u == _author()]
        self.share_label.setText(t("share.status", n=len(mine)))
        self.share_label.setVisible(True)

    # ------------------------------------------------------------ phases (renovation)

    def set_phase(self, status, ids=None):
        """BIM ▸ Phase of the selection (or the Properties panel): existing, new, to demolish,
        temporary — the IFC Status of the elements. One undo step."""
        ids = [i for i in (ids if ids is not None else self.viewport.selection)
               if self.doc.get(i) is not None and self.doc.get(i).is_bim]
        if not ids:
            self.message(t("info.select_first"), warning=True)
            return
        n = bim.set_status(self.doc, ids, status)
        self.message(t("info.status", n=n, phase=t("phase." + status.lower()) if status else t("props.no_phase")))

    # ------------------------------------------------------------ coordination notes (BCF)

    def new_note(self, title=None, description=""):
        """Notes ▸ New note: a title and a description, with the view as it is now — where one is
        looking, the elements selected, a picture."""
        if title is None:
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle(t("notes.new"))
            name = QtWidgets.QLineEdit()
            text = QtWidgets.QPlainTextEdit()
            form = QtWidgets.QFormLayout(dialog)
            form.addRow(t("notes.field_title"), name)
            form.addRow(t("notes.field_description"), text)
            buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                                 | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            form.addRow(buttons)
            self._note_dialog = dialog                       # (tests fill it in)
            if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted or not name.text().strip():
                return None
            title, description = name.text().strip(), text.toPlainText().strip()
        origin = np.asarray(self.doc.ifc.origin, dtype=float)
        position, direction, up, fov = self.viewport.camera_state()
        selected = sorted(i for i in self.viewport.selection if self.doc.get(i) is not None and self.doc.get(i).is_bim)
        note = notes_model.Note(title, description, author=_author(), date=notes_model.now(),
                                camera=notes_model.Camera(tuple(float(c) for c in position + origin),
                                                          tuple(float(c) for c in direction),
                                                          tuple(float(c) for c in up), float(fov)),
                                selected=selected, snapshot=_png(self.viewport.snapshot()))
        self.doc.change_notes(t("cmd.note_new"), lambda doc: doc.notes.append(note))
        self.notes_panel.show()
        self.notes_panel.raise_()
        self.message(t("info.note_new", t=title, n=len(selected)))
        return note

    def go_to_note(self, note):
        """The view a note was made in: its camera (back in 3D), its elements selected."""
        if note.camera is None and not note.selected:
            self.message(t("info.note_no_view"))
            return
        if self.viewport.cutting():
            self.set_view("iso")
        if note.camera is not None:
            origin = np.asarray(self.doc.ifc.origin, dtype=float)
            self.viewport.set_camera(np.asarray(note.camera.position) - origin, note.camera.direction,
                                     note.camera.up, note.camera.fov)
        ids = {g for g in note.selected if self.doc.get(g) is not None}
        self.viewport.set_selection({i for i in ids if self.viewport.is_shown(self.doc.get(i))})
        self.message(t("info.note_go", t=note.title, n=len(ids)))

    def _change_note(self, label, guid, change):
        def apply(doc):
            for note in doc.notes:
                if note.guid == guid:
                    change(doc, note)
        self.doc.change_notes(label, apply)

    def comment_note(self, note, text):
        self._change_note(t("cmd.note_comment"), note.guid,
                          lambda doc, n: n.comments.append((_author(), notes_model.now(), text)))

    def toggle_note(self, note):
        state = notes_model.OPEN if note.closed else notes_model.CLOSED

        def change(doc, n):
            n.status = state
        self._change_note(t("cmd.note_status"), note.guid, change)

    def delete_note(self, note):
        def change(doc):
            doc.notes = [n for n in doc.notes if n.guid != note.guid]
        self.doc.change_notes(t("cmd.note_delete"), change)

    def import_notes(self, path=None):
        """Notes ▸ Import BCF: another's notes into this project (one already here is replaced by
        the one in the file — the other person's latest)."""
        if path is None:
            start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("notes.import"), start, t("notes.filter"))
            if not path:
                return
        try:
            found = notes_model.load(path)
        except ValueError as exc:
            self.message(t("notes.error", f=os.path.basename(path), e=exc), warning=True)
            return

        def change(doc):
            mine = {n.guid: k for k, n in enumerate(doc.notes)}
            for note in found:
                if note.guid in mine:
                    doc.notes[mine[note.guid]] = note
                else:
                    doc.notes.append(note)
        self.doc.change_notes(t("cmd.notes_import"), change)
        self.notes_panel.show()
        self.notes_panel.raise_()
        self.message(t("info.notes_imported", n=len(found), f=os.path.basename(path)))

    def export_notes(self, path=None):
        """Notes ▸ Export BCF: the notes to a .bcfzip (BCF 2.1) for Revit, ArchiCAD, Solibri…"""
        if path is None:
            base = os.path.splitext(self.doc.path)[0] if self.doc.path else os.path.join(_documents_dir(), "projeto")
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, t("notes.export"), base + " - notas.bcfzip",
                                                            t("notes.filter"))
            if not path:
                return
        notes_model.save(self.doc.notes, path, self._file_label())
        self.message(t("info.notes_exported", n=len(self.doc.notes), f=os.path.basename(path)))

    # ------------------------------------------------------------ IDS requirements

    def check_ids(self, path=None):
        """BIM ▸ Check against IDS requirements: an IDS file (buildingSMART: what the model must
        say — properties, classifications, materials…) is checked against the model as it is now;
        the Requirements panel lists each requirement met or not and the elements that fail."""
        if path is None:
            start = os.path.dirname(self._ids_path or self.doc.path or "") or _documents_dir()
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("act.check_ids"), start, t("ids.filter"))
            if not path:
                return
        if self.doc.loading:
            self.message(t("rules.loading"), warning=True)
            return
        doc = self.doc
        try:
            title, requirements = self.run_busy(lambda: ids_check.check(doc.ifc, path), t("ids.working"))
        except ids_check.IdsError as exc:
            self.message(t("ids.error", f=os.path.basename(path), e=exc), warning=True)
            return
        self._ids_path, self._last_check = path, "ids"
        self.ids_panel.show()
        self.ids_panel.raise_()
        self.ids_panel.show_results(title, requirements)
        failing = len({g for r in requirements for g, _label, _reason in r.failures})
        self.message(t("info.ids", ok=sum(1 for r in requirements if r.status), n=len(requirements), e=failing))

    def check_ifc(self):
        """BIM ▸ Check the IFC for certification (0.70): the header, schema and rules, spatial structure,
        units, GlobalIds, shapes and names, and the recommended quantities, types, materials and
        georeferencing — in the Requirements panel, each with what fails."""
        if self.doc.loading:
            self.message(t("rules.loading"), warning=True)
            return
        doc = self.doc
        title, requirements = self.run_busy(lambda: certify.check(doc.ifc), t("cert.working"))
        self._last_check = "ifc"
        self.ids_panel.show()
        self.ids_panel.raise_()
        self.ids_panel.show_results(title, requirements, t("act.check_ifc"))
        self.message(t("info.cert", ok=sum(1 for r in requirements if r.status), n=len(requirements)))

    def save_check_report(self, path=None):
        """The panel's checks (IDS or certification) as a page to keep or send (0.70)."""
        if self.ids_panel.last is None:
            return
        if path is None:
            base = os.path.splitext(self.doc.path or os.path.join(_documents_dir(), "modelo"))[0]
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, t("ids.save_report"), base + "_verificacao.html",
                                                            t("ids.report_filter"))
            if not path:
                return
        title, requirements = self.ids_panel.last
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(certify.report_html(title, requirements, os.path.basename(self.doc.path or "")))
        self.message(t("info.report_saved", f=os.path.basename(path)))

    # ------------------------------------------------------------ selection (0.75)

    def _selectable_shown(self):
        """What can be selected in the view shown: (object ids, grid axis indices)."""
        vp = self.viewport
        ids = {o.id for o in vp.shown_objects()
               if vp.selectable(o) and not (o.is_bim and o.id in vp.bim and not vp.bim.is_visible(o.id))}
        axes = set(range(len(self.doc.grids))) if "grid" not in vp.unselectable and vp.section is None else set()
        return ids, axes

    def _select(self, ids, axes):
        if self.tool.name != "select":
            self.set_tool("select")
        self.viewport.set_selection(ids)
        self.viewport.select_axes(axes)
        n = len(ids) + len(axes)
        self.message(t("info.selected", n=n) if n else t("info.selected_none"))

    def select_all(self):
        """Edit ▸ Selection ▸ Select all (Ctrl+A): everything shown in the view that can be selected."""
        self._select(*self._selectable_shown())

    def select_invert(self):
        """Edit ▸ Selection ▸ Invert (Ctrl+I): what is shown and not selected, instead of what is."""
        ids, axes = self._selectable_shown()
        self._select(ids - self.viewport.selection, axes - self.viewport.selected_axes)

    def select_none(self):
        self._select(set(), set())

    # filters (0.76)

    def _categories(self, ids, axes=()):
        """{category: how many} of these objects (and grid axes)."""
        counts = {}
        for i in ids:
            obj = self.doc.get(i)
            if obj is not None:
                c = self.viewport.category(obj)
                counts[c] = counts.get(c, 0) + 1
        if axes:
            counts["grid"] = len(axes)
        return counts

    def filter_selection(self):
        """Selection ▸ Filter… (Revit's funnel): the categories of what is selected, how many of each, ticked;
        untick some and only the others stay selected."""
        ids, axes = set(self.viewport.selection), set(self.viewport.selected_axes)
        if not ids and not axes:
            self.message(t("info.select_first"), warning=True)
            return
        counts = self._categories(ids, axes)
        dialog = selection_dialogs.CategoryDialog(self, t("sel.filter_title"), t("sel.filter_note"), counts,
                                                  set(counts))
        self._sel_dialog = dialog                     # (tests fill it in)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        keep = set(dialog.list.ticked())
        self._select({i for i in ids if self.doc.get(i) is not None and self.viewport.category(self.doc.get(i)) in keep},
                     axes if "grid" in keep else set())

    def selectable_categories(self):
        """Selection ▸ Selectable… (AutoCAD's selection filter): the categories that clicks, boxes and Select
        all can take — the others are left alone (e.g. the floor slabs while picking the walls over them)."""
        everything = {o.id for o in self.doc.objects.values()}
        counts = self._categories(everything, range(len(self.doc.grids)))
        counts.setdefault("sketch", 0)
        counts.setdefault("grid", 0)
        vp = self.viewport
        dialog = selection_dialogs.CategoryDialog(self, t("sel.selectable_title"), t("sel.selectable_note"), counts,
                                                  set(counts) - vp.unselectable)
        self._sel_dialog = dialog
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        vp.unselectable = (vp.unselectable - set(counts)) | (set(counts) - set(dialog.list.ticked()))
        self._select({i for i in vp.selection if vp.selectable(self.doc.get(i))},
                     vp.selected_axes if "grid" not in vp.unselectable else set())
        self._show_selectable()

    def _show_selectable(self):
        off = len(self.viewport.unselectable)
        self.act_selectable.setText(t("act.selectable") if not off else t("act.selectable_some", n=off))

    def _scope_ids(self, scope):
        """The IFC elements that Select by… looks at: those shown in the view, or all in the project — of the
        categories that can be selected."""
        vp = self.viewport
        objs = vp.shown_objects() if scope == "view" else self.doc.objects.values()
        return [o.id for o in objs if o.is_bim and vp.selectable(o)]

    def _criteria(self):
        keys = list(rules_model.RULES) + [("pset", p, q) for p, q in self.doc.ifc.property_keys()]
        return [(t("sel.by.class") if k == ("class",) else rules_model.rule_label(k), k) for k in keys]

    def _value_rows(self, key, scope):
        """[(label, value, how many)] of the values of `key` among the elements looked at."""
        counts = {}
        for value in self.doc.ifc.property_values(self._scope_ids(scope), key).values():
            counts[value] = counts.get(value, 0) + 1
        label = (lambda v: selection_dialogs.category_text(v)) if key == ("class",) else \
            (lambda v: rules_model.value_label(v, key))
        return sorted(((label(v), v, n) for v, n in counts.items()), key=lambda r: (r[1] is None, r[0].lower()))

    def select_by(self):
        """Selection ▸ Select by…: the elements whose category / type / material / storey / phase / property has
        one of the values ticked — in the view or in the whole project; replacing the selection or joining it."""
        if self.doc.loading:
            self.message(t("rules.loading"), warning=True)
            return
        dialog = selection_dialogs.SelectByDialog(self, self._criteria(), self._value_rows)
        self._sel_dialog = dialog
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        key, values, scope, add = dialog.choice()
        found = {g for g, v in self.doc.ifc.property_values(self._scope_ids(scope), key).items() if v in values}
        if add:
            self._select(found | self.viewport.selection, set(self.viewport.selected_axes))
        else:
            self._select(found, set())

    def select_same(self, scope, by="type"):
        """Revit's Select All Instances (0.76): the elements of the same type(s) as those selected (by "class":
        of the same categories) — visible in the view, or in the whole project."""
        chosen = [i for i in self.viewport.selection if self.doc.get(i) is not None and self.doc.get(i).is_bim]
        if not chosen:
            self.message(t("info.select_first"), warning=True)
            return
        ifc = self.doc.ifc
        if by == "type":
            classes = ifc.property_values(chosen, ("class",))
            types = ifc.property_values(chosen, ("type",))
            wanted = {(classes[g], types[g]) for g in chosen if types.get(g) is not None}
            ids = self._scope_ids(scope)
            classes, types = ifc.property_values(ids, ("class",)), ifc.property_values(ids, ("type",))
            found = {g for g in ids if (classes.get(g), types.get(g)) in wanted}
        else:
            wanted = {self.doc.get(g).ifc_class for g in chosen}
            found = {g for g in self._scope_ids(scope) if self.doc.get(g).ifc_class in wanted}
        self._select(found | set(chosen), set())

    def selection_menu(self, x, y):
        """The Select tool's right button (0.76): select alike, filters, all / invert / none — (0.402) and, a dimension
        string chosen, what Revit's offers: delete the witness line under the mouse, add references, IG, its text."""
        menu = QtWidgets.QMenu(self)
        dims = [d for d in self.viewport.selected_dims if d in self.doc.dimensions]
        if dims and not self.viewport.selection:
            select = self.tools.get("select")
            self._witness_clicked = select.witness_at(x, y) if select is not None else None
            self.act_dim_witness.setEnabled(self._witness_clicked is not None)
            self.act_dim_eq.setText(t("act.dim_eq_off" if all(d.eq for d in dims) else "act.dim_eq"))
            menu.addActions([self.act_dim_witness, self.act_dim_add, self.act_dim_eq, self.act_dim_text])
            if any(dims_model.text_shift(d) is not None for d in dims):
                menu.addAction(self.act_dim_text_back)
            menu.addSeparator()
        has = bool(self.viewport.selection)
        for text, slot in ((t("act.same_type_view"), lambda: self.select_same("view")),
                           (t("act.same_type_project"), lambda: self.select_same("project")),
                           (t("act.same_category_view"), lambda: self.select_same("view", by="class"))):
            act = menu.addAction(text, slot)
            act.setEnabled(has)
        menu.addSeparator()
        menu.addAction(self.act_element_hatches)        # (0.331, as Revit's «Override graphics in view ▸ by element»)
        menu.addAction(self.act_reset_patterns)         # (0.332)
        menu.addSeparator()
        menu.addAction(self.act_filter_selection)
        menu.addAction(self.act_select_by)
        menu.addAction(self.act_selectable)
        menu.addSeparator()
        menu.addActions([self.act_select_all, self.act_select_invert, self.act_select_none])
        self._selection_menu = menu                   # (tests)
        menu.popup(menus.menu_point(menu, self.canvas.mapToGlobal(QtCore.QPoint(int(x), int(y)))))

    def set_draw_look(self, name, remember=True):
        """(0.446) How drawing looks: "revit" — the outline being drawn and its dashed location line, the temporary
        dimensions crossed at their ends with their values orange beside them, the angle's wide arc from a grey
        reference line, the snaps' magenta glyphs — or "addon" (0.372: arrows, values on dark boxes, coloured dots).
        Kept for the next session."""
        from ..core import temp_dims
        temp_dims.LOOK["name"] = "addon" if name == "addon" else "revit"
        (self.act_draw_addon if name == "addon" else self.act_draw_revit).setChecked(True)
        if remember:
            QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue("desenho/aspeto", temp_dims.LOOK["name"])
            self.viewport.clear_overlays()
            self.message(t("info.draw_" + temp_dims.LOOK["name"]))

    def set_dim_faces(self, on, remember=True):
        """(0.361) A wall's temporary dimensions to the walls round it from face to face (on: the clear distances),
        or from axis to axis — the owner's «opções de cotas de eixo a eixo, e de face a face». Kept for next time."""
        self.dim_faces = bool(on)
        (self.act_dims_faces if self.dim_faces else self.act_dims_axes).setChecked(True)
        if remember:
            QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue("cotas/face_a_face",
                                                                  "true" if self.dim_faces else "false")
        select = self.tools.get("select")
        if select is not None and self.tool is select:
            select._refresh_dims(keep=False)
            self.set_hint(select.hint())
        self.message(t("info.dims_faces" if self.dim_faces else "info.dims_axes"))

    def set_thin_lines(self, on):
        """(0.428) «Linhas finas»: the cut's lines on the screen all 1 px (as Revit's Thin Lines) — or with their
        pens' widths at the zoom. Kept for the next time; paper keeps its pens."""
        on = bool(on)
        self.viewport.set_thin_lines(on)
        if self.act_thin_lines.isChecked() != on:
            self.act_thin_lines.setChecked(on)
        QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue("vista/linhas_finas", "true" if on else "false")

    def set_drag_elements(self, on):
        """(0.427) «Arrastar elementos»: whether a drag that starts on an element moves it (else it draws a box, as
        before) — kept for the next time."""
        on = bool(on)
        self.tools["select"].drag_elements = on
        if self.act_drag_elements.isChecked() != on:
            self.act_drag_elements.setChecked(on)
        QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue("selecao/arrastar", "true" if on else "false")

    def set_drag_shape(self, shape):
        """What dragging with the Select tool draws: "box" or "lasso"."""
        self.tools["select"].drag_shape = shape
        (self.act_drag_lasso if shape == "lasso" else self.act_drag_box).setChecked(True)
        if self.tool.name != "select":
            self.set_tool("select")
        self.set_hint(self.tool.hint())

    def pick_region(self, kind):
        """Selection ▸ Polygon / Fence: the next clicks draw it."""
        if self.tool.name != "select":
            self.set_tool("select")
        self.tool.start_picking(kind)

    def generate_grid(self):
        """BIM ▸ Generate grid… (0.72): how many numbered axes (running along Y) and lettered axes (along X),
        how far apart — one value, or several separated by ";" in turn —, from which point, and how far they
        reach past the outermost ones; added to the axes there are, or replacing them. One undo step."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(t("gen.title"))
        form = QtWidgets.QFormLayout(dialog)
        note = QtWidgets.QLabel(t("gen.hint"))
        note.setWordWrap(True)
        form.addRow(note)
        sep = decimal_sep()
        fields = {}
        for key, default in (("numbered", 4), ("lettered", 3)):
            count = QtWidgets.QSpinBox()
            count.setRange(0, 60)
            count.setValue(default)
            spacing = QtWidgets.QLineEdit("5{}00".format(sep))
            form.addRow(t("gen." + key), count)
            form.addRow(t("gen.spacing"), spacing)
            fields[key] = (count, spacing)
        origin = QtWidgets.QLineEdit("0; 0")
        extension = QtWidgets.QLineEdit("1{}50".format(sep))
        form.addRow(t("gen.origin"), origin)
        form.addRow(t("gen.extension"), extension)
        replace = QtWidgets.QCheckBox(t("gen.replace"))
        replace.setEnabled(bool(self.doc.grids))
        form.addRow(replace)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        self._grid_dialog = dialog                    # (tests fill it in)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        xs = bim.spacings_to_positions(fields["numbered"][0].value(), fields["numbered"][1].text())
        ys = bim.spacings_to_positions(fields["lettered"][0].value(), fields["lettered"][1].text())
        point = parse_lengths(origin.text(), 2)
        reach = parse_length(extension.text())
        if xs is None or ys is None or point is None or None in point or reach is None or reach < 0:
            self.message(t("err.bad_value", t=t("gen.title")), warning=True)
            return
        if not xs and not ys:
            return
        tags = bim.generate_grid(self.doc, xs, ys, point, reach, replace.isChecked())
        self.message(t("info.grid_generated", n=len(tags), first=tags[0], last=tags[-1]))

    def columns_on_grid(self):
        """Columns on the grid (0.92): a column at each crossing of the axes selected (one way only: where they
        cross the others; none: all), with the Column tool's type and height, on the active storey — tied to the
        axes. One undo step; the new columns selected."""
        if not self.doc.grids:
            self.message(t("info.no_grid"), warning=True, action=self.act_grid_generate)          # (0.324)
            return []
        tool = self.tools["column"]
        made = bim.columns_on_grid(self.doc, sorted(self.viewport.selected_axes) or None, tool.spec, tool.height,
                                   self.doc.active_storey)
        if not made:
            self.message(t("info.columns_on_grid_none"), warning=True)
            return []
        self.viewport.select_axes(set())
        self.viewport.set_selection(set(made))
        self.message(t("info.columns_on_grid", n=len(made)))
        return made

    def electrical_proposal(self):
        """Propor pontos elétricos (0.145): the dialog with the active storey's rooms, their profiles and numbers;
        its preview drawn on the plan; applied in one undo step."""
        from ..ifc.electrical import point_symbol
        from ..model import electrical_proposal as ep
        from ..render.viewport import PREVIEW
        from . import electrical_proposal_dialog as epd
        storey = self.doc.active_storey
        rooms = [(i["guid"], i["name"], ep.profile_of(i["name"])) for i in self.doc.ifc.spaces(storey)]
        if not rooms:
            self.message(t("elprop.none"), warning=True, action=self.tool_actions["room"])        # (0.324)
            return None
        dialog = epd.ElectricalProposalDialog(self, rooms)
        self._elprop_dialog = dialog
        level = self.doc.work_level()

        def preview(profiles, counts):
            plan = bim.propose_electrical(self.doc, storey, profiles, counts)
            try:
                mm = (self.doc.view_settings(self.viewport.current_view()).scale or 100) / 1000.0
            except Exception:
                mm = 0.1
            segs = []
            for _room, (_name, _profile, _counts, items) in plan.items():
                for kind, p, inward in items:
                    if kind == "light":                   # (a light: a circle with a cross)
                        r = 3.0 * mm
                        ring = [np.array((p[0] + r * np.cos(a), p[1] + r * np.sin(a), level))
                                for a in np.linspace(0, 2 * np.pi, 17)]
                        segs += [q for a, b in zip(ring, ring[1:]) for q in (a, b)]
                        for d in ((0.7, 0.7), (0.7, -0.7)):
                            segs += [np.array((p[0] - d[0] * r, p[1] - d[1] * r, level)),
                                     np.array((p[0] + d[0] * r, p[1] + d[1] * r, level))]
                        continue
                    lines, solids = point_symbol(kind, (p[0], p[1], level), ep.angle_of(inward), mm)
                    segs += [np.array((q[0], q[1], level)) for a, b in lines for q in (a, b)]
                    for poly in solids:
                        segs += [np.array((q[0], q[1], level)) for a, b in zip(poly, poly[1:] + poly[:1]) for q in (a, b)]
            self.viewport.show_lines(segs, [PREVIEW] * len(segs))
            self._elprop_preview = sum(len(v[3]) for v in plan.values())

        def apply(profiles, counts):
            plan = bim.propose_electrical(self.doc, storey, profiles, counts)
            self.viewport.clear_overlays()
            made = bim.apply_electrical_proposal(self.doc, plan, storey)
            self.message(t("info.electrical_proposal", n=len(made), r=len(plan)))

        dialog.on_preview, dialog.on_apply = preview, apply
        dialog.exec()
        self.viewport.clear_overlays()
        self._elprop_dialog = None
        return True

    def remove_electrical_proposal(self):
        """Retirar a proposta elétrica (0.145): its points and lights on the active storey deleted, in one step."""
        n = bim.remove_electrical_proposal(self.doc, self.doc.active_storey)
        self.message(t("info.electrical_removed", n=n) if n else t("info.electrical_removed_none"), warning=not n)
        return n

    def water_proposal(self):
        """Propor águas e esgotos (0.148): in the active storey's rooms with fixtures, a stack, the water pipes and
        every fixture connected to them. One undo step."""
        plan = bim.propose_water(self.doc)
        if not plan:                              # (0.324) the rooms first, then the fixtures in them
            rooms = self.doc.ifc.spaces(self.doc.active_storey)
            self.message(t("info.water_none"), warning=True, action=self.tool_actions["fixture" if rooms else "room"])
            return []
        made = bim.apply_water_proposal(self.doc, plan)
        self.message(t("info.water_proposal", r=len(plan), n=len(made)))
        return made

    def remove_water_proposal(self):
        """Retirar a proposta de águas e esgotos (0.148): what it made on the active storey deleted, in one step."""
        n = bim.remove_water_proposal(self.doc, self.doc.active_storey)
        self.message(t("info.water_removed", n=n) if n else t("info.water_removed_none"), warning=not n)
        return n

    def clashes(self, report_path=None):
        """Detetar conflitos (0.149–0.150): the dialog; its clashes shown (selected and framed), approved, made BCF
        notes of, written to an HTML report (report_path: where, without asking — the tests)."""
        from ..model import clashes as clashes_model
        from . import clash_dialog
        dialog = clash_dialog.ClashDialog(self, self.doc)
        dialog.on_show = lambda ids: (self._select_from_tree(ids), self._frame_from_tree(ids))

        def note(c):
            a, b = self.doc.get(c.a), self.doc.get(c.b)
            title = t("clash.note_title", a=a.name if a else c.a, b=b.name if b else c.b)
            where = "{:.2f}; {:.2f}; {:.2f}".format(*c.point).replace(".", decimal_sep())
            origin = np.asarray(self.doc.ifc.origin, dtype=float)
            eye = np.asarray(c.point, dtype=float) + np.array((-4.0, -4.0, 3.0))
            look = np.asarray(c.point, dtype=float) - eye
            made = notes_model.Note(title, t("clash.note_text", pair=clashes_model.pair_text(c.pair), where=where),
                                    author=_author(), date=notes_model.now(), kind="Clash",
                                    camera=notes_model.Camera(tuple(float(v) for v in eye + origin),
                                                              tuple(float(v) for v in look / np.linalg.norm(look))),
                                    selected=[c.a, c.b])
            self.doc.change_notes(t("cmd.note_new"), lambda doc: doc.notes.append(made))
            self.message(t("info.clash_note", title=title))

        def report(found):
            path = report_path
            if path is None:
                base = os.path.splitext(self.doc.path or "conflitos")[0] + " - conflitos.html"
                path, _f = QtWidgets.QFileDialog.getSaveFileName(self, t("clash.report"), base, "HTML (*.html)")
            if not path:
                return
            with open(path, "w", encoding="utf-8") as f:
                f.write(clashes_model.report_html(self.doc, found, t("clash.title"), self.doc.clash_status))
            self.message(t("info.clash_report", path=path))

        dialog.on_note, dialog.on_report = note, report
        self._clash_dialog = dialog
        dialog.exec()
        self._clash_dialog = None
        return dialog.found

    def electrical_check(self):
        """Verificar a instalação elétrica (0.147): the active storey's problems in a list; a double-click selects
        what one is about."""
        from ..model import electrical_check
        from . import electrical_check_dialog as ecd
        storey = self.doc.active_storey
        dialog = ecd.ElectricalCheckDialog(self, lambda: electrical_check.problems(self.doc, storey))
        dialog.on_select = lambda ids: self._select_from_tree([i for i in ids if self.doc.get(i) is not None])
        self._elcheck_dialog = dialog
        dialog.exec()
        self._elcheck_dialog = None
        return dialog.found

    def route_circuits(self):
        """Ligar ao quadro (0.146): the conduits of the active storey's circuits that have none, from their board to
        their points. One undo step; the load schedule shows their length."""
        made = bim.route_circuits(self.doc)
        if not made:
            self.message(t("info.route_none"), warning=True, action=self.act_new_circuit)         # (0.324)
            return made
        length = sum(self.doc.ifc.conduit_length(g) for g in made)
        self.message(t("info.routed", n=len(made), l=format_length(length, decimal_sep())))
        return made

    def new_circuit(self):
        """Novo circuito com a seleção (0.144): the selected electrical points and lights make a new circuit (C1,
        C2…) of the type they say (lights and switches: lighting…), on their storey's board. One undo step; the
        load schedule (Tables ▸ Circuits) shows it."""
        points = [i for i in self.viewport.selection
                  if self.doc.get(i) is not None and self.doc.get(i).ifc_class in bim.CIRCUIT_LOADS]
        if not points:                           # (0.322) the points asked for
            self._ask(self.act_new_circuit, "pick.circuit", self._class_is(*bim.CIRCUIT_LOADS), self.new_circuit)
            return None
        made = bim.add_circuit(self.doc, points)
        if made is None:
            self.message(t("info.circuit_none"), warning=True)
            return None
        r = self.doc.ifc.circuit_report(made)
        self.message(t("info.circuit_made", name=r["name"], k=t("circuit." + r["kind"]), n=r["points"],
                       p="{:.0f} W".format(r["power"])))
        return made

    def connect_network(self):
        """Ligar à rede (0.142): the selected sanitary fixtures (none: all those of the active storey) get their
        branches to the network of each outlet's system. One undo step; what had no network is told."""
        fixtures = [i for i in self.viewport.selection if self.doc.get(i) is not None and self.doc.get(i).ifc_class
                    in ("IfcSanitaryTerminal", "IfcElectricAppliance", "IfcBurner")]     # (appliances: 0.198)
        report = bim.connect_to_network(self.doc, fixtures or None)
        if not report:
            self.message(t("info.connect_none"), warning=True, action=self.tool_actions["fixture"])   # (0.324)
            return report
        done = [r for r in report if r[3] is not None]
        missing = sorted({t("system." + r[2]) for r in report if r[3] is None})
        text = t("info.connected_network", n=len(done))
        if missing:
            text += " " + t("info.connected_missing", what=", ".join(missing))
        self.message(text, warning=bool(missing))
        self._refresh_properties()
        return report

    def footings_under(self):
        """Footings under the columns (0.93): under each column selected (none: all those of the active
        storey) that has none yet, the Footing tool's pad type — tied to the column. One undo step."""
        columns = [i for i in self.viewport.selection
                   if self.doc.get(i) is not None and self.doc.get(i).ifc_class == "IfcColumn"]
        made = bim.footings_under(self.doc, columns or None, self.tools["footing"].pad)
        if not made:                              # (0.324) no column at all: one to make (on the grid, if any)
            offer = self._columns_offer()         # (0.325: which of the two it is, said)
            self.message(t("info.no_columns" if offer else "info.footings_under_none"), warning=True, action=offer)
            return []
        self.message(t("info.footings_under", n=len(made)))
        return made

    def combined_footing(self):
        """(0.249) A combined footing under the two columns selected, of the Footing tool's pad type — tied to both.
        One undo step; selected."""
        columns = [i for i in self.viewport.selection
                   if self.doc.get(i) is not None and self.doc.get(i).ifc_class == "IfcColumn"]
        if len(columns) != 2:                    # (0.322) the two columns asked for
            self._ask(self.act_combined_footing, "pick.combined_footing", self._class_is("IfcColumn"),
                      self.combined_footing, least=2, most=2, fresh=len(columns) > 2)
            return None
        made = bim.combined_footing(self.doc, *columns, self.tools["footing"].pad)
        if made is None:
            self.message(t("info.combined_footing_none"), warning=True)
            return None
        self.viewport.set_selection({made})
        self.message(t("info.combined_footing"))
        return made

    def _steel_pieces(self):
        """(0.496) The steel pieces selected (their GlobalIds)."""
        return [g for g in self.viewport.selection if isinstance(g, str) and self.doc.ifc.kind_of(g) == "steel_member"]

    def base_plates(self):
        """(0.497) Estrutura ▸ Ligação ▸ Chapa de base: under the steel columns selected — none selected: under every
        steel column without one —, each with its anchor bolts and its weld."""
        chosen = [g for g in self.viewport.selection if isinstance(g, str)
                  and self.doc.get(g) is not None and self.doc.get(g).ifc_class == "IfcColumn"]
        made = bim.add_base_plates(self.doc, chosen or None)
        if made:
            self.message(t("info.base_plates", n=len(made)))
        else:
            self.message(t("info.base_plates_none"), warning=True)
        return made

    def export_steel_nc(self, folder=None):
        """(0.501) Estrutura ▸ Ligação ▸ Exportar para fabrico: the DSTV NC1 files (a mark each) and the bars' cutting
        plan, in a folder chosen."""
        from ..model import steel_fabrication
        if not any(True for _ in steel_fabrication.nc1_files(self.doc)):
            self.message(t("info.steel_nc_none"), warning=True)
            return []
        if folder is None:
            folder = QtWidgets.QFileDialog.getExistingDirectory(self, t("steel_nc.folder"))
        if not folder:
            return []
        paths = steel_fabrication.write(self.doc, folder)
        self.message(t("info.steel_nc", n=sum(1 for p in paths if p.endswith(".nc1")), folder=folder))
        return paths

    def number_steel(self):
        """(0.500) Estrutura ▸ Ligação ▸ Numerar peças: the steel pieces' marks written on them."""
        n = bim.number_steel(self.doc)
        self.message(t("info.number_steel", n=n) if n else t("info.number_steel_none"))
        return n

    def beam_connections(self, kind):
        """(0.498) Estrutura ▸ Ligação ▸ Chapa de topo / Cutelo: at the ends of the steel beams selected that reach
        steel columns."""
        beams = [g for g in self.viewport.selection if isinstance(g, str) and self.doc.ifc.steel_section(g)
                 and self.doc.ifc.kind_of(g) in ("beam", "steel_member")]
        made = bim.add_beam_connections(self.doc, kind, beams)
        if made:
            self.message(t("info.beam_connections", n=len(made), what=t("connection." + kind)))
        else:
            self.message(t("info.beam_connections_none"), warning=True)
        return made

    def gussets(self):
        """(0.503) Estrutura ▸ Ligação ▸ Gousset: at the ends of the braces selected (angles) that reach steel
        columns — none selected: of every brace —, a gusset welded to the column, the brace bolted to it."""
        braces = [g for g in self.viewport.selection if isinstance(g, str) and self.doc.ifc.kind_of(g) == "steel_member"]
        made = bim.add_gussets(self.doc, braces or None)
        if made:
            self.message(t("info.gussets", n=len(made)))
        else:
            self.message(t("info.gussets_none"), warning=True)
        return made

    def knee_plate(self):
        """(0.513) Estrutura ▸ Ligação ▸ Joelho aparafusado: the two steel pieces selected mitred and bolted (an end
        plate on each in the mitre's plane)."""
        pieces = self._steel_pieces()
        made = bim.knee_plates(self.doc, pieces[0], pieces[1]) if len(pieces) == 2 else None
        if made is None:
            self.message(t("info.knee_plate_no"), warning=True)
            return None
        self.message(t("info.knee_plate", a=self.doc.get(pieces[0]).name, b=self.doc.get(pieces[1]).name))
        return made

    def purlin_cleats(self):
        """(0.504) Estrutura ▸ Ligação ▸ Apoio de madre: where the purlins selected — none selected: every purlin — sit
        on steel beams, a cleat welded to the beam, the purlin bolted to it."""
        purlins = [g for g in self.viewport.selection if isinstance(g, str)
                   and self.doc.ifc.kind_of(g) == "steel_member"]
        made = bim.add_purlin_cleats(self.doc, purlins or None)
        if made:
            self.message(t("info.purlin_cleats", n=len(made)))
        else:
            self.message(t("info.purlin_cleats_none"), warning=True)
        return made

    def steel_mitre(self):
        """(0.496) Estrutura ▸ Meia-esquadria: the two steel pieces selected cut to a mitre where their lines meet."""
        pieces = self._steel_pieces()
        if len(pieces) != 2:
            self.message(t("info.steel_mitre_pick"), warning=True)
            return False
        if not bim.mitre(self.doc, pieces[0], pieces[1]):
            self.message(t("info.steel_mitre_no"), warning=True)
            return False
        self.message(t("info.steel_mitre", a=self.doc.get(pieces[0]).name, b=self.doc.get(pieces[1]).name))
        return True

    def beams_between(self):
        """Beams between columns (0.94): between the columns selected (none: all those of the active storey)
        next to each other in a line, with the Beam tool's type — tied to them. One undo step; the new beams
        selected."""
        columns = [i for i in self.viewport.selection
                   if self.doc.get(i) is not None and self.doc.get(i).ifc_class == "IfcColumn"]
        made = bim.beams_between(self.doc, columns or None, self.tools["beam"].spec)
        if not made:
            offer = self._columns_offer()         # (0.324; 0.325: no columns, or none to join, said)
            self.message(t("info.no_columns" if offer else "info.beams_between_none"), warning=True, action=offer)
            return []
        self.viewport.set_selection(set(made))
        self.message(t("info.beams_between", n=len(made)))
        return made

    def walls_under_beams(self):
        """Walls under the beams (0.95): under the beams selected (none: all those of the active storey tied to
        columns), with the Wall tool's type — tied to the beams. One undo step; the new walls selected."""
        beams = [i for i in self.viewport.selection
                 if self.doc.get(i) is not None and self.doc.get(i).ifc_class == "IfcBeam"]
        made = bim.walls_under_beams(self.doc, beams or None, self.tools["wall"].spec)
        if not made:
            offer = self._beams_offer()           # (0.324; 0.325: no beams, or they have walls, said)
            self.message(t("info.no_beams" if offer else "info.walls_under_beams_none"), warning=True, action=offer)
            return []
        self.viewport.set_selection(set(made))
        self.message(t("info.walls_under_beams", n=len(made)))
        return made

    def slabs_in_bays(self):
        """Slabs in the beams' bays (0.96): in each closed bay of the beams selected (none: all those of the
        active storey), with the Slab tool's type — tied to the beams. One undo step; the new slabs selected."""
        beams = [i for i in self.viewport.selection
                 if self.doc.get(i) is not None and self.doc.get(i).ifc_class == "IfcBeam"]
        made, skipped = bim.slabs_in_bays(self.doc, beams or None, self.tools["slab"].spec)
        note = t("info.slabs_in_bays_skipped", k=skipped) if skipped else ""
        if not made:
            offer = self._beams_offer()           # (0.324; 0.325: no beams, or no bay closed, said)
            self.message((t("info.no_beams") if offer else t("info.slabs_in_bays_none")) + note, warning=True,
                         action=offer)
            return []
        self.viewport.set_selection(set(made))
        self.message(t("info.slabs_in_bays", n=len(made)) + note)
        return made

    def beam_system(self):
        """A beam system (0.97): in each bay closed by the beams selected (none: all those of the active storey),
        parallel beams along X or Y (or both: a grid), by number or spacing, of a beam type. One undo step."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(t("bsys.title"))
        form = QtWidgets.QFormLayout(dialog)
        way, mode, kind = QtWidgets.QComboBox(), QtWidgets.QComboBox(), QtWidgets.QComboBox()
        for key in ("x", "y", "grid"):
            way.addItem(t("bsys.way." + key), key)
        for key in ("count", "spacing"):
            mode.addItem(t("bsys.mode." + key), key)
        value = QtWidgets.QLineEdit("3")
        mode.currentIndexChanged.connect(lambda _i: value.setText(
            "3" if mode.currentData() == "count" else format_length(1.5, decimal_sep()).replace(" m", "")))
        current = self.tools["beam"].spec
        for spec in (s for s in catalog.types() if s.kind == "beam"):
            kind.addItem(spec.name_pt if lang() == "pt" else spec.name_en, spec.key)
        kind.setCurrentIndex(max(0, kind.findData(current.key)))
        form.addRow(t("bsys.way"), way)
        form.addRow(t("bsys.mode"), mode)
        form.addRow(t("bsys.value"), value)
        form.addRow(t("bsys.type"), kind)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        dialog.way, dialog.mode, dialog.value, dialog.kind = way, mode, value, kind
        self._beam_system_dialog = dialog                  # (tests fill it in)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return []
        if mode.currentData() == "count":
            try:
                amount = int(value.text().strip())
            except ValueError:
                amount = -1
        else:
            amount = parse_length(value.text()) or -1
        if amount <= 0:
            self.message(t("err.bad_value", t=value.text()), warning=True)
            return []
        beams = [i for i in self.viewport.selection
                 if self.doc.get(i) is not None and self.doc.get(i).ifc_class == "IfcBeam"]
        made, skipped = bim.beam_system(self.doc, beams or None, way.currentData(), mode.currentData(), amount,
                                        catalog.BY_KEY[kind.currentData()])
        note = t("info.slabs_in_bays_skipped", k=skipped) if skipped else ""
        if not made:
            self.message(t("info.beam_system_none") + note, warning=True)
            return []
        self.viewport.set_selection(set(made))
        self.message(t("info.beam_system", n=len(made)) + note)
        return made

    def propose_structure(self):
        """Propose a structure (0.98): from the active storey's walls (or those selected), columns, beams along the
        walls and footings — the largest span and the types chosen. One undo step; again: it replaces the
        proposal."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(t("prop.title"))
        form = QtWidgets.QFormLayout(dialog)
        note = QtWidgets.QLabel(t("prop.note"))
        note.setWordWrap(True)
        form.addRow(note)
        span = QtWidgets.QLineEdit(format_length(5.0, decimal_sep()).replace(" m", ""))
        form.addRow(t("prop.span"), span)
        combos = {}
        for kind, label, current in (("column", "prop.column", "pilar_20"), ("beam", "prop.beam", "viga_15x30"),
                                     ("footing", "prop.footings", "sapata_80")):
            combo = QtWidgets.QComboBox()
            if kind == "footing":
                combo.addItem(t("prop.no_footings"), None)
            for spec in (s for s in catalog.types() if s.kind == kind and not s.strip):
                combo.addItem(spec.name_pt if lang() == "pt" else spec.name_en, spec.key)
            combo.setCurrentIndex(max(0, combo.findData(current)))
            form.addRow(t(label), combo)
            combos[kind] = combo
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        dialog.span, dialog.combos = span, combos
        self._proposal_dialog = dialog                     # (tests fill it in)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return None
        largest = parse_length(span.text())
        if largest is None or largest < 1.0:
            self.message(t("err.bad_value", t=span.text()), warning=True)
            return None
        walls = [i for i in self.viewport.selection
                 if self.doc.get(i) is not None and self.doc.get(i).ifc_class == "IfcWall"]
        footing = combos["footing"].currentData()
        counts = bim.propose_structure(self.doc, walls or None, largest, catalog.BY_KEY[combos["column"].currentData()],
                                       catalog.BY_KEY[combos["beam"].currentData()],
                                       catalog.BY_KEY[footing] if footing else None)
        if counts is None:
            self.message(t("info.proposal_no_walls"), warning=True, action=self.tool_actions["wall"])   # (0.324)
            return None
        self.message(t("info.proposal", c=counts["columns"], b=counts["beams"], f=counts["footings"]))
        return counts

    def remove_proposal(self):
        if bim.remove_proposal(self.doc):
            self.message(t("info.proposal_removed"))
        else:
            self.message(t("info.proposal_none"), warning=True)

    def grid_settings(self):
        """BIM ▸ Structural grid… (0.91): the tags' scheme (vertical axes numbered or lettered), renumbering the
        axes in order, the dimensions between axes in the plans, the bubbles' radius. One undo step."""
        current = dict(self.doc.grid_settings)
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(t("grid.title"))
        form = QtWidgets.QFormLayout(dialog)
        scheme = QtWidgets.QComboBox()
        for key in ("numbers_y", "letters_y"):
            scheme.addItem(t("grid.scheme." + key), key)
        scheme.setCurrentIndex(max(0, scheme.findData(current.get("scheme"))))
        form.addRow(t("grid.scheme"), scheme)
        renumber = QtWidgets.QCheckBox(t("grid.renumber"))
        renumber.setEnabled(bool(self.doc.grids))
        scheme.currentIndexChanged.connect(lambda _i: renumber.setChecked(
            scheme.currentData() != current.get("scheme") and bool(self.doc.grids)))
        form.addRow(renumber)
        dims = QtWidgets.QCheckBox(t("grid.dims"))
        dims.setChecked(bool(current.get("dims")))
        form.addRow(dims)
        bubble = QtWidgets.QLineEdit(format_length(float(current.get("bubble", 0.35)), decimal_sep()))
        form.addRow(t("grid.bubble"), bubble)
        note = QtWidgets.QLabel(t("grid.note"))
        note.setWordWrap(True)
        note.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        form.addRow(note)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        self._grid_settings_dialog = dialog              # (tests fill it in)
        dialog.scheme, dialog.renumber, dialog.dims, dialog.bubble = scheme, renumber, dims, bubble
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        radius = parse_length(bubble.text())
        if radius is None or not 0.05 <= radius <= 2.0:
            self.message(t("err.bad_value", t=bubble.text()), warning=True)
            return
        bim.set_grid_settings(self.doc, {"scheme": scheme.currentData(), "dims": dims.isChecked(), "bubble": radius},
                              renumber=renumber.isChecked())
        self.message(t("info.grid_settings"))

    def dimension_style(self, select=None):
        """Anotar ▸ Tipos de cota… (0.124: the project's dimension style; 0.193: its types; 0.398: every property of a
        type, as Revit's — ui/dim_types_dialog.py, with a sample on paper). Every dimension follows its type, on
        screen and on paper. One undo step."""
        from . import dim_types_dialog
        current = dims_model.clean_style(self.doc.dim_style)
        dialog = dim_types_dialog.DimTypesDialog(self, current)
        if select is not None:                           # (0.405: from a dimension's Properties, its own type)
            dialog.select_type(select)
        self._dim_style_dialog = dialog                  # (tests fill it in)
        accepted = dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
        self._dim_style_dialog = None
        if not accepted:
            return
        new = dialog.style()
        if new != current:
            self.doc.execute(dims_model.SetDimensionStyle(current, new, t("cmd.dimension_style"),
                                                          getattr(dialog, "renamed", None)))
            self.message(t("info.dimension_style", v=dims_model.text(2.475, decimal_sep(), new)))

    def graphic_styles(self):
        """View ▸ Graphic styles… (0.126): how the project's drawings look on paper — for each kind of material
        cut, its pattern (solid, lines, crossed lines, nothing), colour, angle and spacing; and the pens (what is
        cut, seen, hatched, dimensioned, drawn). Every view and sheet follows it. One undo step."""
        from . import graphic_styles_dialog
        current = styles_model.clean(self.doc.graphic_style)
        dialog = graphic_styles_dialog.GraphicStylesDialog(self, current)
        self._graphic_styles_dialog = dialog              # (tests fill it in)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        new = styles_model.clean(dialog.style())
        if new != current:
            self.doc.execute(styles_model.SetGraphicStyle(current, new, t("cmd.graphic_styles")))
            self.message(t("info.graphic_styles"))

    def symbol_styles(self):
        """Anotar ▸ Símbolos… (0.360): the symbols' generator (ui/symbol_styles_dialog.py) — how the sections', the
        elevations', the details' and the levels' symbols look, in every view, sheet, PDF and DXF. One undo step."""
        from . import symbol_styles_dialog
        current = styles_model.clean(self.doc.graphic_style)
        dialog = symbol_styles_dialog.SymbolStylesDialog(self, current)
        self._symbol_styles_dialog = dialog                # (tests fill it in)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return False
        new = styles_model.clean(dialog.style())
        if new == current:
            return False
        self.doc.execute(styles_model.SetGraphicStyle(current, new, t("cmd.symbol_styles")))
        self.viewport.apply_storey_view()                  # (the view's symbols drawn again in them)
        self.message(t("info.symbol_styles"))
        return True

    def set_typical_live(self, on):
        """(0.465, the owner: «O botão = deve ligável e desligavel. Só faz o efeito quando o botão está ligado») The
        typical floors' replication switched on or off (the Storeys panel's «=»): off, what is made, changed or deleted
        on a typical storey — its plan's dimensions and drawing too — is on it alone (and stays so); on again, the
        floors go on being equal. For this session (on when a project is opened)."""
        self.doc.typical_live = bool(on)
        self.viewport.apply_storey_view()                  # (a plan's shared drawing shown, or not)
        self._refresh_storeys()
        self.message(t("info.typical_live_on" if on else "info.typical_live_off"), warning=not on)

    def set_level_style(self, level):
        """(0.462) The levels' look from the Storeys panel (their line, colour, end, words, seen in 3D): the project's
        graphic style's level symbol — every section, elevation, sheet, PDF, DXF and the 3D view follow. One undo
        step."""
        import copy as _copy
        current = styles_model.clean(self.doc.graphic_style)
        new = _copy.deepcopy(current)
        new["symbols"]["level"] = dict(current["symbols"]["level"], **dict(level))
        new = styles_model.clean(new)
        if new == current:
            return False
        self.doc.execute(styles_model.SetGraphicStyle(current, new, t("cmd.level_style")))
        self.viewport.apply_storey_view()                  # (the view's levels drawn again)
        self._refresh_storeys()
        self.message(t("info.level_style"))
        return True

    def edit_view_styles(self):
        """View ▸ View styles… (0.315): the program's view styles and the project's — made, named, duplicated,
        changed, deleted; how the faces are seen, their colours, edges, shadows, surface patterns, transparency and
        what is cut. One undo step; the views drawn with a style changed follow."""
        from . import view_styles_dialog
        view = self._footer_view() if hasattr(self, "footer_bar") else None
        current = self.doc.view_settings(view).style if view is not None else None
        try:
            site = self.doc.ifc.site_location()[:2]         # (0.316: its sun by the site, a day and an hour)
        except (AttributeError, RuntimeError):
            site = (None, None)
        dialog = view_styles_dialog.ViewStylesDialog(self, self.doc.view_styles, select=current, site=site)
        self._view_styles_dialog = dialog                  # (tests fill it in)
        accepted = dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
        self._view_styles_dialog = None
        if accepted and dialog.styles != list(self.doc.view_styles):
            self.doc.set_view_styles(dialog.styles)
            self.message(t("info.view_styles", n=len(dialog.styles)))

    def site_location(self):
        """BIM ▸ Site location (0.70): latitude and longitude (as on a map) and the height above sea level of
        the site — the model's place on Earth (georeferencing, for certification and other programs)."""
        lat, lon, elevation = self.doc.ifc.site_location()
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(t("site.title"))
        form = QtWidgets.QFormLayout(dialog)
        note = QtWidgets.QLabel(t("site.hint"))
        note.setWordWrap(True)
        form.addRow(note)
        fields = []
        for label, value, low, high, decimals in ((t("site.latitude"), lat, -90.0, 90.0, 6),
                                                  (t("site.longitude"), lon, -180.0, 180.0, 6),
                                                  (t("site.elevation"), elevation, -500.0, 9000.0, 2)):
            box = QtWidgets.QDoubleSpinBox()
            box.setRange(low, high)
            box.setDecimals(decimals)
            box.setValue(value or 0.0)
            form.addRow(label, box)
            fields.append(box)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        self._site_dialog = dialog                    # (tests fill it in)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        bim.set_site_location(self.doc, *(f.value() for f in fields))
        lat, lon = ("{:.6f}°".format(f.value()).replace(".", decimal_sep()) for f in fields[:2])
        self.message(t("info.site_location", lat=lat, lon=lon))

    # ------------------------------------------------------------ graphic rules

    def apply_rule(self, key):
        """Graphic rules panel: colour the elements by `key` (see IfcModel.property_values); None:
        the usual colours, by class. The values are read in a worker thread (a big model)."""
        self.rule = key
        if key is None:
            self._rule_values = {}
            self.viewport.set_colours({})
            self.rules_panel.show_legend([])
            return
        ids = [o.id for o in self.doc.objects.values() if o.is_bim]
        doc = self.doc
        if tuple(key) == rules_model.EC3:                  # (0.517) the steel's use by Eurocode 3: analysed
            from ..model import steel_analysis
            read = lambda: steel_analysis.bands(doc, ids)  # noqa: E731
        else:
            read = lambda: doc.ifc.property_values(ids, key)  # noqa: E731
        try:
            self._rule_values = self.run_busy(read, t("rules.working"))
        except RuntimeError:                       # the IFC is still being read
            self.rule, self._rule_values = None, {}
            self.rules_panel.reset()
            self.message(t("rules.loading"), warning=True)
            return
        lines = self._show_rule()
        self.message(t("info.rule", rule=rules_model.rule_label(key), n=len(lines)))

    def _show_rule(self):
        lines = rules_model.legend(self._rule_values, self.rule)
        self.viewport.set_colours(rules_model.colours(lines))
        self.rules_panel.show_legend(lines)
        return lines

    def _property_keys(self):
        try:
            return self.doc.ifc.property_keys()
        except RuntimeError:
            return []

    def _refresh_rule(self, changed=None, removed=None):
        """The elements changed while coloured by a rule: their values read again (only theirs)."""
        if getattr(self, "rule", None) is None or self.doc.loading:
            return
        if changed is None or tuple(self.rule) == rules_model.EC3:     # (0.517: the whole steel analysed again —
            self.apply_rule(self.rule)                                 # one piece changes all the forces)
            return
        ids = [i for i in changed if self.doc.get(i) is not None and self.doc.get(i).is_bim]
        gone = [i for i in removed or () if i in self._rule_values]
        if not ids and not gone:
            return
        for i in gone:
            self._rule_values.pop(i, None)
        self._rule_values.update(self.doc.ifc.property_values(ids, self.rule))
        self._show_rule()

    def reset_rule(self):
        """Another file (or a new one): back to the usual colours, and to the views' usual settings."""
        self._template_rule = None
        self.viewport.set_view_settings((), CUT_HEIGHT)
        if getattr(self, "rule", None) is not None:
            self.rules_panel.reset()
            self.apply_rule(None)

    def dimension_walls(self):
        """View ▸ Dimension the walls: the selected walls (none: all of the active storey) get, on
        their outer side, a chain through their doors and windows and their overall length, on
        the plan of the active storey. Doing it again replaces them (one undo step)."""
        storey = self.doc.active_storey
        walls = [i for i in self.viewport.selection
                 if self.doc.get(i) is not None and self.doc.get(i).is_bim and self.doc.get(i).ifc_class == "IfcWall"]
        if not walls:
            walls = [o.id for o in self.doc.objects.values()
                     if o.is_bim and o.ifc_class == "IfcWall" and o.storey == storey]
        if not walls:
            self.message(t("info.no_walls"), warning=True, action=self.tool_actions["wall"])      # (0.324)
            return
        new = dims_model.wall_chains(self.doc, walls, storey)
        tags = {"wall:" + g for g in walls}
        old = [d for d in self.doc.dimensions if d.tag in tags]
        self.doc.execute(dims_model.ReplaceDimensions(old, new, t("cmd.dimension_walls")))
        if not self.viewport.plan:
            self.set_plan(True)
        self.message(t("info.walls_dimensioned", n=len(walls), d=len(new), name=self._storey(storey)[0]))

    def dimension_auto(self, which):
        """View ▸ Dimension the façades / the rooms (0.123): on the plan of the active storey, round the
        building (each side: its corners and openings, its corners, its length) or across each room (its width
        and depth, from wall to wall). Doing it again replaces them (one undo step)."""
        storey = self.doc.active_storey
        if which == "facade":                     # (0.399: round the building, in any direction, as the tool's)
            from ..model import auto_dims
            tool = self.tools.get("dim_exterior")
            try:
                scale = self.doc.view_settings(("plan", storey)).scale or 100
            except Exception:
                scale = 100
            new = auto_dims.exterior(self.doc, storey, getattr(tool, "preference", "faces"),
                                     tool._rows() if tool is not None else auto_dims.ROWS,
                                     getattr(tool, "openings", "jambs"), scale)
            prefixes = ("facade:", "ext:")
        else:                                     # (0.400: every room the walls close, with a Room or not)
            from ..model import auto_dims
            tool = self.tools.get("dim_interior")
            try:
                scale = self.doc.view_settings(("plan", storey)).scale or 100
            except Exception:
                scale = 100
            new = auto_dims.interior(self.doc, storey, None, getattr(tool, "preference", "faces"), "size",
                                     scale=scale, every=True)
            prefixes = ("room:", "int:size:")
        if not new:                               # (0.324) what is missing, a click away
            self.message(t("info.no_walls" if which == "facade" else "info.no_rooms_dims"), warning=True,
                         action=self.tool_actions["wall" if which == "facade" else "room"])
            return
        old = [d for d in self.doc.dimensions if d.view in self.doc.twin_views(("plan", storey))   # (0.463: its equals')
               and (d.tag or "").startswith(prefixes)]
        self.doc.execute(dims_model.ReplaceDimensions(old, new, t("cmd.dimension_" + which)))
        if not self.viewport.plan:
            self.set_plan(True)
        self.message(t("info.dimensioned_" + which, d=len(new), name=self._storey(storey)[0]))

    # ------------------------------------------------------------ (0.402) dimension strings edited as Revit's

    def _chosen_string(self, dim=None):
        """The dimension string chosen (its pieces, linear ones), or []."""
        from ..model import dim_edit
        if dim is None:
            dims = [d for d in self.viewport.selected_dims if d in self.doc.dimensions and d.vertex is None]
            dim = dims[0] if dims else None
        return [d for d in dim_edit.string_of(self.doc, dim) if d.vertex is None] if dim is not None else []

    def dimension_equal(self):
        """«IG»: the string's pieces made equal (the walls, doors and windows in its middle moved), writing «IG»; again:
        the values written again. One undo step."""
        from ..model import dim_edit
        string, plane = self._chosen_string(), self.viewport.view_plane()
        if not string or plane is None:
            self.message(t("info.dim_pick"), warning=True)
            return
        if all(d.eq for d in string):
            dim_edit.unequalize(self.doc, string, t("cmd.dim_eq_off"))
            self.message(t("info.dim_eq_off"))
        else:
            try:
                moved = dim_edit.equalize(self.doc, string, plane, t("cmd.dim_eq"))
            except ValueError as exc:
                self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
                return
            self.message(t("info.dim_eq", n=len(string), m=moved))
        self.viewport.select_dimensions({d for d in string if d in self.doc.dimensions})

    def dimension_add_references(self):
        """Revit's «Editar linhas de chamada»: the Dimension tool with the string's references, to add more."""
        string = self._chosen_string()
        if not string:
            self.message(t("info.dim_pick"), warning=True)
            return
        self.viewport.select_dimensions(set())
        self.set_tool("dimension")
        if self.tool.add_to(string):
            self.message(t("hint.dimension.add_refs"))

    def dimension_remove_witness(self):
        """Revit's «Apagar linha de chamada»: the witness line right-clicked taken away — its two pieces made one."""
        from ..model import dim_edit
        string, index = self._chosen_string(), getattr(self, "_witness_clicked", None)
        if not string or index is None:
            self.message(t("info.dim_witness_pick"), warning=True)
            return
        if dim_edit.remove_witness(self.doc, string, index, t("cmd.dim_witness")):
            self.message(t("info.dim_witness_removed"))
        else:
            self.message(t("info.dim_witness_last"), warning=True)
        self.viewport.select_dimensions({d for d in string if d in self.doc.dimensions})

    def dimension_text_back(self):
        """The values dragged apart put back in their place."""
        from ..model import dim_edit
        string = self._chosen_string()
        moved = [d for d in string if dims_model.text_shift(d) is not None]
        if moved:
            changes = [(d, {"note": {k: v for k, v in (d.note or {}).items() if k != "shift"} or None}) for d in moved]
            self.doc.execute(dim_edit.ChangeDimensions(changes, t("cmd.dim_move_text")))
            self.viewport.select_dimensions(set(string))

    def edit_dimension_text(self, dim=None):
        """Revit's «Texto da cota» (a double click on a value): its value — typed, the element at one of its ends
        moves —, the real value or a text over it, a prefix, a suffix, words over and under it; for this dimension or
        its whole string. One undo step each."""
        from ..core.units import parse_length
        from ..model import dim_edit
        if dim is None:
            dims = [d for d in self.viewport.selected_dims if d in self.doc.dimensions and d.vertex is None]
            dim = dims[0] if dims else None
        plane = self.viewport.view_plane()
        if dim is None or plane is None:
            self.message(t("info.dim_pick"), warning=True)
            return False
        string = self._chosen_string(dim)
        origin, u, v, _n = plane
        a, b = dims_model.ends(self.doc, dim)
        length = dims_model.placed(a, b, dims_model.line_point(self.doc, dim), origin, u, v, dim.direction)[4]
        note = dict(dim.note or {})
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(t("dimtext.title"))
        form = QtWidgets.QFormLayout(dialog)
        value = QtWidgets.QLineEdit(format_length(length, decimal_sep()))
        movable = [(r[0], self.doc.get(r[0])) for r in dim.refs if r is not None and self.doc.get(r[0]) is not None]
        moving = QtWidgets.QComboBox()
        for guid, obj in movable:
            moving.addItem(obj.name or guid, guid)
        value.setEnabled(bool(movable))
        moving.setEnabled(bool(movable))
        form.addRow(t("dimtext.value"), value)
        form.addRow(t("dimtext.moving"), moving)
        real = QtWidgets.QRadioButton(t("dimtext.real"))
        over = QtWidgets.QRadioButton(t("dimtext.override"))
        override = QtWidgets.QLineEdit(note.get("override", ""))
        (over if note.get("override") else real).setChecked(True)
        override.setEnabled(over.isChecked())
        over.toggled.connect(override.setEnabled)
        form.addRow(real)
        form.addRow(over, override)
        fields = {}
        for key in ("prefix", "suffix", "above", "below"):
            fields[key] = QtWidgets.QLineEdit(note.get(key, ""))
            form.addRow(t("dimtext." + key), fields[key])
        whole = QtWidgets.QCheckBox(t("dimtext.whole", n=len(string)))
        whole.setEnabled(len(string) > 1)
        form.addRow(whole)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        dialog.value, dialog.moving, dialog.real, dialog.over, dialog.override = value, moving, real, over, override
        dialog.fields, dialog.whole = fields, whole
        self._dim_text_dialog = dialog                          # (tests fill it in)
        accepted = dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
        self._dim_text_dialog = None
        if not accepted:
            return False
        new = {k: f.text().strip() for k, f in fields.items()}
        new["override"] = override.text().strip() if over.isChecked() else ""
        targets = string if whole.isChecked() else [dim]
        old = {k: (dim.note or {}).get(k, "") for k in new}
        if new != old or whole.isChecked():
            dim_edit.set_note(self.doc, targets, new, t("cmd.dim_text"))
        typed = parse_length(value.text())
        if movable and typed is not None and abs(typed - length) > 1e-6:
            try:
                if dim_edit.set_value(self.doc, dim, typed, plane, moving.currentData(), t("cmd.dim_value")):
                    self.message(t("info.dim_value", v=format_length(typed, decimal_sep()),
                                   e=moving.currentText()))
                else:
                    self.message(t("info.dim_value_none"), warning=True)
            except ValueError as exc:
                self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
        return True

    def _dimension_property(self, action, target, value):
        """(0.405) What the Properties panel changes on the dimensions chosen (`target`: them, or one): its value (the
        element at its far end moves), IG, its words, its values put back in place, its type's properties, its text's
        window, references added. One undo step each."""
        from ..model import dim_edit
        dims = [d for d in (target if isinstance(target, list) else [target]) if d in self.doc.dimensions]
        plane = self.viewport.view_plane()
        if not dims and action != "dim_edit_type":
            return
        if action == "dim_value":
            if plane is not None and dim_edit.set_value(self.doc, dims[0], value, plane, None, t("cmd.dim_value")):
                self.message(t("info.dim_value", v=format_length(value, decimal_sep()), e=""))
            else:
                self.message(t("info.dim_value_none"), warning=True)
        elif action == "dim_eq":
            if bool(value) != all(d.eq for d in dims):
                self.viewport.select_dimensions(set(dims))
                self.dimension_equal()
        elif action.startswith("dim_note_"):
            dim_edit.set_note(self.doc, dims, {action[len("dim_note_"):]: value}, t("cmd.dim_text"))
        elif action == "dim_text_back":
            self.viewport.select_dimensions(set(dims))
            self.dimension_text_back()
        elif action == "dim_edit_type":
            self.dimension_style(select=value)
        elif action == "dim_text_window":
            self.edit_dimension_text(dims[0])
        elif action == "dim_add":
            self.viewport.select_dimensions(set(dims))
            self.dimension_add_references()
        if action not in ("dim_add",):
            self.viewport.select_dimensions({d for d in self.viewport.selected_dims if d in self.doc.dimensions})

    def edit_dimension_value(self, dim, guid):
        """(Revit's) a dimension of the element selected clicked: its value typed moves that element."""
        from ..core.units import parse_length
        from ..model import dim_edit
        plane = self.viewport.view_plane()
        if plane is None:
            return False
        origin, u, v, _n = plane
        a, b = dims_model.ends(self.doc, dim)
        length = dims_model.placed(a, b, dims_model.line_point(self.doc, dim), origin, u, v, dim.direction)[4]
        obj = self.doc.get(guid)
        text, ok = QtWidgets.QInputDialog.getText(self, t("dimtext.value_title"),
                                                  t("dimtext.value_of", e=obj.name if obj is not None else guid),
                                                  text=format_length(length, decimal_sep()))
        typed = parse_length(text) if ok else None
        if typed is None or abs(typed - length) < 1e-6:
            return False
        try:
            moved = dim_edit.set_value(self.doc, dim, typed, plane, guid, t("cmd.dim_value"))
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return False
        if moved:
            self.message(t("info.dim_value", v=format_length(typed, decimal_sep()), e=obj.name if obj else guid))
        return moved

    def _library_rows(self):
        """(0.466) The project's components for the Library panel: [(type GlobalId, name, copies, placeable)]."""
        try:
            components = self.doc.ifc.library()["components"]
        except Exception:                                   # (the IFC still being read)
            return []
        return sorted(((g, name, len(copies), placeable) for g, name, copies, placeable in components),
                      key=lambda row: row[1].lower())

    def library_bring(self, path):
        """(0.466) A component of the local library (or fetched from the web) brought into the project — one there
        already: as it is — and placed with the mouse. Returns its type's GlobalId, or None."""
        from ..model import component_library
        name = os.path.basename(path)
        try:
            guid = self.run_busy(lambda: component_library.bring(self.doc, path), t("lib.reading", f=name))
        except Exception as exc:                            # (not a component, damaged…)
            self.message(t("libp.bring_failed", f=name, e=exc), warning=True)
            return None
        self._library_action("place", "component", guid)
        self.message(t("libp.brought", name=self.doc.ifc.by_guid(guid).Name or name))
        return guid

    def library_save(self, guid):
        """(0.466) A project's component kept in the local library (a small IFC file of its own), for other projects.
        Returns its path, or None."""
        from ..model import component_library
        panel = self.library_panel
        try:
            path = component_library.save_component(self.doc, guid, panel.folder)
        except Exception as exc:
            self.message(t("libp.save_failed", e=exc), warning=True)
            return None
        self.message(t("libp.saved", name=self.doc.ifc.by_guid(guid).Name or "", f=path))
        return path

    def _library_action(self, action, kind, ref):
        """The Project panel's library: "select" every copy of a component / group model, or
        "place" another copy of a component (with the mouse)."""
        if action == "select":
            ids = [i for i in bim.library_members(self.doc, kind, ref) if self.doc.get(i) is not None]
            self._select_from_tree(ids)
            self.message(t("info.copies_selected", n=len(ids)))
        elif action == "place":
            self.tools["place"].use(ref)
            self.set_tool("place")
        elif action == "import":
            self.import_components()

    def import_image(self, path=None):
        """File ▸ Import background image… (0.154): a picture laid flat on the active storey, in the middle of what
        is seen (a centimetre a pixel until it is calibrated), framed; then the Calibrate image tool, on it."""
        from ..model import images as images_model
        if path is None:
            start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("act.import_image"), start, picture.file_filter())
            if not path:
                return None
        name = os.path.basename(path)
        size = picture.picture_size(path)
        if size is None or picture.load_pixels(path) is None:
            self.message(t("err.image_read", f=name), warning=True)
            return None
        w, h = self.viewport.logical_size()
        origin, direction = self.viewport.ray(w / 2, h / 2)
        level = self.doc.work_level()
        centre = (0.0, 0.0)
        if abs(direction[2]) > 1e-6 and (level - origin[2]) / direction[2] > 0:
            p = origin + direction * (level - origin[2]) / direction[2]
            centre = (float(p[0]), float(p[1]))
        image = images_model.placed(os.path.splitext(name)[0], path, size, centre, self.doc.active_storey)
        self.tool.cancel()
        self.doc.execute(ImagesChange(self.doc.images, self.doc.images + [image], t("cmd.import_image")))
        z = self.viewport.image_level(image)
        corners = np.array([(x, y, z) for x, y in image.corners()])
        self.viewport.zoom_box((corners.min(axis=0), corners.max(axis=0)))
        self.set_tool("calibrate_image")
        self.tool.only = image.uid
        self.message(t("info.image_imported", f=image.name, w=format_length(image.width, decimal_sep())))
        return image

    def import_terrain_points(self, path=None, points=None, name=None):
        """File ▸ Import survey points… (0.155): a survey's text file (x y z a line: CSV, TXT, XYZ) made a terrain
        (or the points given: a DXF's, 0.156). Points in survey coordinates far from the origin: in a project with
        nothing in it yet the project takes them (the IFC keeps them as they are, the program works near its
        origin); else they are brought near it. Returns the terrain's GlobalId, or None."""
        from ..core import terrain as terrain_geo
        from ..ifc.model import FAR_FROM_ORIGIN
        skipped = 0
        if points is None:
            if path is None:
                start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
                path, _ = QtWidgets.QFileDialog.getOpenFileName(
                    self, t("act.terrain_points"), start, "{} (*.csv *.txt *.xyz *.pts *.asc)".format(t("file.points")))
                if not path:
                    return None
            name = os.path.basename(path)
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    points, skipped = terrain_geo.parse_points(f.read())
            except OSError as exc:
                self.message(t("err.open", f=name, e=exc), warning=True)
                return None
        name = name or t("elem.terrain")
        if len(points) < terrain_geo.MIN_POINTS:
            self.message(t("err.points_read", f=name), warning=True)
            return None
        notes = []
        centre = np.round(points[:, :2].mean(axis=0))
        far = float(np.hypot(*centre))
        if far > FAR_FROM_ORIGIN:
            shift = np.array((centre[0], centre[1], 0.0))
            empty = not self.doc.ifc.file.by_type("IfcElement") and not np.any(self.doc.ifc.origin)
            if empty:
                self.doc.ifc.origin = shift                 # (the project in the survey's coordinates)
            notes.append(t("info.terrain_far" if empty else "info.terrain_moved",
                           d=format_length(far, decimal_sep(), 0)))
            points = points - shift
        self.tool.cancel()
        try:
            guid = bim.add_terrain(self.doc, points, os.path.splitext(name)[0])
        except ValueError:
            self.message(t("err.terrain_few"), warning=True)
            return None
        info = self.doc.ifc.terrain_info(guid)
        if skipped:
            notes.append(t("info.points_skipped", n=skipped))
        self.viewport.set_selection({guid})
        self.viewport.zoom_extents([guid])
        self.message(" ".join([t("info.terrain_made", n=info["points"], lo=format_length(info["low"], decimal_sep()),
                                 hi=format_length(info["high"], decimal_sep()),
                                 i=format_length(info["interval"], decimal_sep()))] + notes))
        return guid

    def _dwg_ready(self, path):
        """(0.286) A DWG can be read only with the ODA File Converter: said so when it is missing."""
        from ..core import dwg
        if path.lower().endswith(".dwg") and dwg.converter() is None:
            self.message(t("err.dwg_converter", f=os.path.basename(path)), warning=True)
            return False
        return True

    def link_cad(self, path=None):
        """File ▸ Link a DXF drawing… (0.158): a plan's DXF laid on the active storey as lines — in the project's
        survey coordinates when it is near them, origin to origin when near (0, 0), else in the middle of the view;
        its units from the file (or guessed by its size). Returns the link, or None."""
        from ..model import cad_links as cad_model
        if path is None:
            start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("act.cad_link"), start, "DXF / DWG (*.dxf *.dwg)")
            if not path:
                return None
        name = os.path.basename(path)
        if not self._dwg_ready(path):
            return None
        found = cad_model.drawing_of(os.path.abspath(path))
        if found is None:
            self.message(t("err.cad_read", f=name), warning=True)
            return None
        drawing, raw = found
        if not raw:
            self.message(t("err.cad_empty", f=name), warning=True)
            return None
        w, h = self.viewport.logical_size()
        origin, direction = self.viewport.ray(w / 2, h / 2)
        level = self.doc.work_level()
        centre = (0.0, 0.0)
        if abs(direction[2]) > 1e-6 and (level - origin[2]) / direction[2] > 0:
            p = origin + direction * (level - origin[2]) / direction[2]
            centre = (float(p[0]), float(p[1]))
        where, how = cad_model.placement(raw, drawing.units, self.doc.ifc.origin, centre)
        link = cad_model.CadLink(os.path.splitext(name)[0], os.path.abspath(path), drawing.units, where,
                                 storey=self.doc.active_storey)
        self.tool.cancel()
        self.doc.execute(CadLinksChange(self.doc.cad_links, self.doc.cad_links + [link], t("cmd.cad_link")))
        self.viewport.zoom_extents()
        unit = next((label for label, v in cad_model.UNIT_CHOICES if abs(v - drawing.units) < 1e-12), "?")
        storey = next((n for g, n, _z in self.doc.storeys() if g == self.doc.active_storey), "")
        self.message(t("info.cad_linked", f=name, s=storey,
                       u=t("cadlinks.units_given" if drawing.units_given else "cadlinks.units_guessed", u=unit),
                       how=t("cadlinks.how." + how)))
        return link

    def walls_from_cad(self):
        """BIM ▸ Walls from the drawing… (0.159): of a linked DXF, its walls (pairs of parallel lines on the layers
        chosen) shown as they are found, then made — each of the type of its thickness, joined at its corners —
        on the drawing's storey: one undo step. Returns their GlobalIds, or None."""
        from . import cad_walls_dialog
        from ..model.bim import WALL_HEIGHT
        links = [c for c in self.doc.cad_links if c.visible]
        if not links:
            self.message(t("err.cadwalls_no_link"), warning=True, action=self.act_cad_link)       # (0.324)
            return None

        def show(axes, link, blocks=(), arcs=(), columns=()):
            z = (self.viewport.image_level(link) if link is not None else self.doc.work_level()) + 0.05
            segs = [np.array((p[0], p[1], z)) for a, b, _t in axes for p in (a, b)]
            for centre, radius, start, sweep, _t in arcs:     # (the curved walls found, 0.210)
                n = max(int(abs(sweep) / np.radians(7.5)) + 1, 2)
                ring = [np.array((centre[0] + radius * np.cos(start + sweep * k / n),
                                  centre[1] + radius * np.sin(start + sweep * k / n), z)) for k in range(n + 1)]
                segs += [p for a, b in zip(ring[:-1], ring[1:]) for p in (a, b)]
            from ..core import cad_columns
            for column in columns:                          # (the columns found, 0.211)
                ring = [np.array((p[0], p[1], z)) for p in cad_columns.outline(column)]
                segs += [p for a, b in zip(ring, ring[1:] + ring[:1]) for p in (a, b)]
            for block in blocks:                            # (the doors and windows found, 0.160)
                for line in block.lines:
                    for p, q in zip(line[:-1], line[1:]):
                        segs += [np.array((p[0], p[1], z)), np.array((q[0], q[1], z))]
            self.viewport.show_polygon([], segments=segs, colors=[(0.12, 0.37, 0.84, 1.0)] * len(segs))

        self.tool.cancel()
        dialog = cad_walls_dialog.CadWallsDialog(self, links, show, WALL_HEIGHT)
        self._cad_walls_dialog = dialog
        accepted = dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
        self._cad_walls_dialog = None
        self.viewport.clear_overlays()
        if not accepted or not (dialog.axes or dialog.arcs or dialog.columns or dialog.furniture):
            return None
        link = dialog.link()
        report = bim.model_from_cad(self.doc, dialog.axes, dialog.openings, dialog.furniture, dialog.height.value(),
                                    storey=link.storey, arcs=dialog.arcs, columns=dialog.columns)
        text = t("info.cadmodel", w=len(report["walls"]), d=len(report["doors"]), j=len(report["windows"]),
                 f=len(report["furniture"]))
        if report.get("columns"):
            text += " " + t("info.cadmodel_columns", n=len(report["columns"]))
        if report["left"]:
            text += " " + t("info.cadmodel_left", n=report["left"])
        self.message(text, warning=bool(report["left"]))
        self._last_cad_model = report
        return report["walls"]

    def link_cloud(self, path=None):
        """File ▸ Link a point cloud… (0.161): a scan (XYZ / PTS / TXT, PLY, LAS) laid in the model on the active
        storey — in the project's survey coordinates when near them, as it is when near (0, 0), else in the middle
        of the view with its lowest point at 0; its units guessed by its size. Returns the link, or None."""
        from ..core import pointcloud
        from ..model import cloud_links as cloud_model
        if path is None:
            start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, t("act.cloud_link"), start,
                "{} ({})".format(t("file.clouds"), " ".join("*." + e for e in pointcloud.EXTENSIONS)))
            if not path:
                return None
        name = os.path.basename(path)
        path = os.path.abspath(path)
        cloud = self.run_busy(lambda: cloud_model.cloud_of(path), t("clouds.reading", f=name))
        if cloud is None or not len(cloud):
            self.message(t("err.cloud_read", f=name), warning=True)
            return None
        lo, hi = cloud.bounds()
        span = float((np.asarray(hi) - np.asarray(lo))[:2].max())
        units = 0.001 if span > 2000 and not path.lower().endswith(".las") else 1.0
        w, h = self.viewport.logical_size()
        origin, direction = self.viewport.ray(w / 2, h / 2)
        level = self.doc.work_level()
        centre = (0.0, 0.0)
        if abs(direction[2]) > 1e-6 and (level - origin[2]) / direction[2] > 0:
            p = origin + direction * (level - origin[2]) / direction[2]
            centre = (float(p[0]), float(p[1]))
        where, how = cloud_model.placement(cloud, units, self.doc.ifc.origin, centre)
        link = cloud_model.CloudLink(os.path.splitext(name)[0], path, units, where, storey=self.doc.active_storey)
        self.tool.cancel()
        self.doc.execute(CloudLinksChange(self.doc.cloud_links, self.doc.cloud_links + [link], t("cmd.cloud_link")))
        self.viewport.zoom_extents()
        self.message(t("info.cloud_linked", f=name, n="{:,}".format(len(cloud)).replace(",", " "),
                       how=t("cadlinks.how." + how)))
        return link

    def set_show_analytical(self, on=None):
        """View ▸ Analytical model (0.163): the analytical model drawn over the model."""
        on = self.act_show_analytical.isChecked() if on is None else bool(on)
        self.act_show_analytical.setChecked(on)
        self.viewport.set_show_analytical(on)

    def show_moments(self, on=None):
        """(0.220) Structure ▸ Moment diagrams: the structure analysed (its project's settings) and each member's
        bending moment diagram under 1,35G+1,50Q drawn over the model; off, gone. Returns the Analysis shown."""
        on = self.act_moments.isChecked() if on is None else bool(on)
        self.act_moments.setChecked(on)
        if not on:
            self.viewport.show_diagrams(None)
            return None
        _model, _loads, analysis = self.run_busy(lambda: bim.analyse_structure(self.doc), t("moments.working"))
        if analysis.error or not analysis.diagrams:
            self.act_moments.setChecked(False)
            self.viewport.show_diagrams(None)
            self.message(t("moments.none"), warning=True, action=self.act_analyse)                # (0.324)
            return analysis
        self.viewport.show_diagrams(analysis.diagrams)
        top = max(abs(m) for *_r, ms in analysis.diagrams.values() for m in ms)
        self.message(t("info.moments", c=analysis.diagram_combo, m="{:.1f}".format(top).replace(".", decimal_sep()),
                       n=len(analysis.diagrams)))
        return analysis

    def analyse_structure(self):
        """Structure ▸ Analyse the structure… (0.165): the structure analysed with its actions; its members' forces,
        deflections, the load path, the drift listed. Returns the Analysis."""
        from . import analysis_dialog
        self.tool.cancel()
        names = {o.id: o.name for o in self.doc.objects.values() if o.is_bim}
        dialog = analysis_dialog.AnalysisDialog(self, lambda: bim.analyse_structure(self.doc), names)
        dialog.on_select = lambda ids: self._select_from_tree([i for i in ids if self.doc.get(i) is not None])
        dialog.on_save = lambda: self.save_analysis_results()                         # (0.221)
        self._analysis_dialog = dialog
        if not dialog.result.error and not dialog.result.members:            # (0.336) walls only
            self.message(t("info.analysed_walls", w=len(dialog.result.walls)))
        elif not dialog.result.error:
            self.message(t("info.analysed", n=len(dialog.result.members),
                           up="{:.1f}".format(dialog.result.reactions_up).replace(".", decimal_sep())))
        dialog.exec()
        self._analysis_dialog = None
        return dialog.result

    def save_analysis_results(self):
        """(0.221) The analysis's results saved in the IFC (with the analytical model and its loads): one undo step.
        Returns the Analysis."""
        analysis = self.run_busy(lambda: bim.save_analysis_results(self.doc), t("moments.working"))
        if analysis.error:
            self.message(t("analysis.not_saved"), warning=True)
        else:
            self.message(t("info.results_saved", n=len(analysis.diagrams), r=len(analysis.reactions)))
        return analysis

    def verify_structure(self):
        """Structure ▸ EC2 check and reinforcement… (0.166): each concrete member checked by Eurocode 2 with the
        analysis's forces, its reinforcement chosen; put in the model on demand (one undo step); the bar schedule from
        there. Returns the [ElementDesign] last shown."""
        from . import design_dialog
        self.tool.cancel()
        names = {o.id: o.name for o in self.doc.objects.values() if o.is_bim}
        settings = self.doc.ifc.structural_settings()
        dialog = design_dialog.DesignDialog(self, lambda: bim.design_structure(self.doc, settings), names, settings,
                                            self.doc.ifc.rebar_design)
        dialog.on_select = lambda ids: self._select_from_tree([i for i in ids if self.doc.get(i) is not None])
        dialog.on_make = lambda designs: self.make_rebars(designs, settings)
        dialog.on_schedule = lambda: self.rebar_schedule()
        self._design_dialog = dialog
        dialog.exec()
        self._design_dialog = None
        return dialog.designs

    def make_rebars(self, designs, settings=None):
        """The reinforcement of these member designs put in the model (0.166). Returns (members, bars)."""
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)   # (the bars' solids take time)
        try:
            members, bars = bim.make_rebars(self.doc, designs, settings)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        if members:
            self.message(t("ec2.done", n=members, b=bars))
        else:
            self.message(t("ec2.nothing"), warning=True)
        return members, bars

    def rebar_mesh(self, mesh=None, remove=False):
        """Structure ▸ Welded mesh (0.522): a mesh on the slabs selected (asked for when `mesh` is not given), or theirs
        taken out. Returns the IfcReinforcingMeshes made ([] when removed or cancelled), None without slabs."""
        from ..core import rebar_mesh as rm
        slabs = [g for g in self.viewport.selection if self.doc.get(g) is not None
                 and self.doc.get(g).ifc_class == "IfcSlab"]       # (before the tool's cancel clears the selection)
        self.tool.cancel()
        if slabs:
            self.viewport.set_selection(set(slabs))
        if not slabs:
            self.message(t("mesh.no_slab"), warning=True)
            return None
        if mesh is None and not remove:
            from . import mesh_dialog
            outline = self.doc.ifc.slab_outline(slabs[0])
            thickness = float(outline["thickness"]) if outline else 0.20
            current = self.doc.ifc.mesh_of(slabs[0])
            dialog = mesh_dialog.MeshDialog(self, current or rm.Mesh(), thickness,
                                            can_remove=bool(self.doc.ifc.meshes_of(slabs)))
            self._mesh_dialog = dialog
            accepted = dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
            self._mesh_dialog = None
            if not accepted:
                return []
            remove, mesh = dialog.removing, dialog.mesh()
        if remove:
            if bim.remove_meshes(self.doc, slabs):
                self.message(t("mesh.removed"))
            return []
        made = self.run_busy(lambda: bim.put_mesh(self.doc, slabs, mesh), t("moments.working"))
        rows = [r for r in self.doc.ifc.mesh_rows() if r["guid"] in set(made)]
        self.message(t("mesh.done", m=mesh.name(decimal_sep()), n=len({r["host"] for r in rows}),
                       s=sum(r["sheets"] for r in rows),
                       kg="{:.0f}".format(sum(r["weight"] for r in rows))))
        return made

    def rebar_schedule(self):
        """Structure ▸ Bar schedule… (0.166): the reinforcement in the model listed by position, with its totals;
        exported to CSV."""
        from . import rebar_schedule_dialog
        self.tool.cancel()
        dialog = rebar_schedule_dialog.RebarScheduleDialog(self, lambda: bim.rebar_schedule(self.doc))
        dialog.on_select = lambda ids: self._select_from_tree([i for i in ids if self.doc.get(i) is not None])
        dialog.on_export = lambda: self.export_rebar_schedule()
        self._schedule_dialog = dialog
        dialog.exec()
        self._schedule_dialog = None
        return dialog.rows

    def export_rebar_schedule(self, path=None):
        """The bar schedule to an Excel workbook (0.370) or a CSV file, by its extension (asked for when not given).
        Returns its path, or None."""
        from . import rebar_schedule_dialog as rsd
        rows, totals = bim.rebar_schedule(self.doc)
        if not rows:
            return None
        if path is None:
            start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
            path = self._table_path(t("rsched.export_title"), os.path.join(start, t("rsched.title") + ".xlsx"))
            if path is None:
                return None
        header = [t("rsched.col." + c) for c in rsd.COLUMNS]
        if not self._write_table(path, header, rsd.table_of(rows) + [[], [rsd.totals_text(totals)]],
                                 t("rsched.title")):
            return None
        self.message(t("info.sched_exported", f=os.path.basename(path)))
        return path

    def add_worktop(self):
        """BIM ▸ Worktop (0.170): a worktop over the base units selected (else all those of the active storey).
        Returns its GlobalId, or None."""
        self.tool.cancel()
        chosen = [g for g in self.viewport.selection if self.doc.get(g) is not None
                  and self.doc.get(g).ifc_class == "IfcFurniture"]
        made = bim.add_worktop(self.doc, chosen or None)
        if made is None:
            self.message(t("err.worktop_none"), warning=True, action=self.tool_actions["cabinet"])   # (0.324)
        else:
            self.message(t("info.worktop"))
        return made

    def roof_profile_from_face(self):
        """(0.251) The roof and the flat sketch selected: the roof made by extrusion of the sketch's outline."""
        sel = [self.doc.get(i) for i in self.viewport.selection]
        roofs = [o for o in sel if o is not None and o.is_bim and o.ifc_class == "IfcRoof"]
        sketches = [o for o in sel if o is not None and not o.is_bim]
        if len(roofs) > 1 or len(sketches) > 1:
            self.message(t("err.roof_profile"), warning=True)
            return False
        if not roofs:                            # (0.322) asked for: the roof, then the face (the other kept)
            self._ask(self.act_roof_profile, "pick.roof_profile_roof", self._class_is("IfcRoof"),
                      self.roof_profile_from_face, most=1, keep=[o.id for o in sketches])
            return False
        if not sketches:
            self._ask(self.act_roof_profile, "pick.roof_profile_face", lambda i: self.doc.get(i) is not None
                      and not self.doc.get(i).is_bim, self.roof_profile_from_face, most=1, keep=[roofs[0].id])
            return False
        try:
            bim.roof_profile_from_face(self.doc, roofs[0].id, sketches[0].id)
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return False
        self.message(t("info.roof_profile"))
        return True

    def edit_keynote_table(self):
        """(0.248) The project's own keynote table, in its window: OK makes it so (one undo step)."""
        from . import keynote_table_dialog
        dialog = keynote_table_dialog.KeynoteTableDialog(self, self.doc.ifc.keynote_table())
        self._keynote_dialog = dialog                     # (tests fill it in)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        if bim.set_keynote_table(self.doc, dialog.entries()):
            self.message(t("info.keynote_table", n=len(dialog.entries())))

    def _organic_source(self):
        """(0.555) (the thing selected an organic form is made over, in words) — (None, None): nothing that serves."""
        for guid in sorted(self.viewport.selection, key=str):
            try:
                _ring, _uid, what = bim.organic_outline(self.doc, guid)
            except ValueError:
                continue
            obj = self.doc.get(guid)
            name = getattr(obj, "name", None) or ""
            words = {"sketch": "o desenho «{}»", "wall": "a face da parede «{}»", "slab": "a laje «{}»",
                     "ceiling": "o teto «{}»"}[what].format(name)
            return guid, words
        return None, None

    def _organic_centre(self):
        """Where a form made from measures goes: where the view looks at the working level (else 0, 0)."""
        level = float(self.doc.work_level()) if hasattr(self.doc, "work_level") else 0.0
        try:
            position, forward, _up, _fov = self.viewport.camera_state()
            if forward[2] < -1e-6:
                k = (level - position[2]) / forward[2]
                p = position + forward * k
                return np.array((round(float(p[0]), 2), round(float(p[1]), 2), level))
        except Exception:  # (no camera yet)
            pass
        return np.array((0.0, 0.0, level))

    def organic_form(self, values=None):
        """(0.555, PLANO.md «Gerador de formas orgânicas») «Forma orgânica»: the window (or `values`, as it gives
        them) — then a Superfície paramétrica of op «organic» over the thing selected or the measures. Its GlobalId."""
        source, words = self._organic_source()
        if values is None:
            from .organic_dialog import OrganicDialog
            dlg = OrganicDialog(words, self)
            if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
                return None
            values = dlg.values()
        try:
            if values.get("measures") or source is None:
                ring = bim.organic_shape(values.get("shape", "retangulo"), self._organic_centre(),
                                         float(values.get("length", 12.0)), float(values.get("width", 8.0)),
                                         int(values.get("sides", 6)))
                uid = None
            else:
                ring, uid, _what = bim.organic_outline(self.doc, source)
            guid = bim.add_organic_form(self.doc, ring, values.get("behaviour", "catenaria"),
                                        float(values.get("height", 3.0)), source_uid=uid, usage=values.get("usage"),
                                        grid=values.get("grid", "quadras"))
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return None
        self.viewport.set_selection({guid})
        self.message("Forma orgânica criada — mude o comportamento e a altura nas Propriedades.")
        return guid

    def control_ring(self, height=1.0, factor=0.75):
        """(0.395, the addon's «Anel de controlo») The highest curve selected copied `height` above it, `factor` its
        size (about its middle): the stack kept selected with it — again and again, then Superfície paramétrica makes a
        loft through them all (a dome, a tower)."""
        vp = self.viewport
        chosen = [self.doc.get(i) for i in list(vp.selection) + list(getattr(vp, "line_selection", {}) or {})]
        sketches = [o for o in chosen if o is not None and not o.is_bim]
        if not sketches:
            self._ask(self.act_control_ring, "pick.control_ring", lambda i: self.doc.get(i) is not None
                      and not self.doc.get(i).is_bim, lambda: self.control_ring(height, factor), most=1,
                      fresh=bool(chosen))
            return None
        from ..model.surface_curves import sketch_chains
        top = max(sketches, key=lambda o: float(np.vstack([c[0] for c in sketch_chains(o)] or
                                                          [np.zeros((1, 3))])[:, 2].mean()))
        try:
            new = bim.control_ring(self.doc, top.id, height, factor)
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return None
        vp.set_selection({o.id for o in sketches} | {new})
        self.message(t("info.control_ring", n=len(sketches) + 1))
        return new

    def profile_from_face(self, name=None):
        """(0.245) The flat sketch selected kept as a profile's section in the project, under a name asked for (or
        `name`): the Profile tool then runs it."""
        sel = [self.doc.get(i) for i in self.viewport.selection]
        sketches = [o for o in sel if o is not None and not o.is_bim]
        if len(sketches) != 1 or len(sel) != 1:  # (0.322) the face asked for
            self._ask(self.act_profile_from_face, "pick.face_profile", lambda i: self.doc.get(i) is not None
                      and not self.doc.get(i).is_bim, lambda: self.profile_from_face(name), most=1, fresh=bool(sel))
            return None
        try:
            bim.face_section(sketches[0])
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return None
        if name is None:
            n = len(self.doc.ifc.custom_profiles()) + 1
            name, ok = QtWidgets.QInputDialog.getText(self, t("act.profile_from_face"), t("ask.profile_name"),
                                                      text=t("profile.own_default", n=n))
            if not ok:
                return None
        try:
            key = bim.profile_from_face(self.doc, sketches[0].id, name)
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return None
        self.message(t("info.profile_from_face", n=name.strip()))
        return key

    def cut_list(self):
        """BIM ▸ Cut list… (0.169): the panels of the cabinets — those selected, else all — and their hardware, the
        patterned finishes' slats and perforated panels (0.173); exported to CSV, or to the CNC's DXF. Returns the
        rows."""
        from . import cutlist_dialog
        self.tool.cancel()
        chosen = [g for g in self.viewport.selection if self.doc.get(g) is not None
                  and self.doc.get(g).ifc_class in ("IfcFurniture", "IfcCovering")]
        guids = chosen or None
        count = len(self.doc.ifc.cabinets(set(guids) if guids else None))
        dialog = cutlist_dialog.CutListDialog(self, lambda: bim.cut_list(self.doc, guids), count)
        dialog.on_export = lambda: self.export_cut_list(guids)
        dialog.on_dxf = lambda: self.export_fabrication(guids)          # (0.173)
        self._cut_dialog = dialog
        dialog.exec()
        self._cut_dialog = None
        return dialog.rows

    def export_fabrication(self, guids=None, path=None):
        """(0.173) The CNC's DXF of the patterned finishes (perforated panels with their holes, the slats' lengths),
        in mm. Returns its path, or None when there are none."""
        from ..model import fabrication
        if not fabrication.pieces(self.doc, guids)[0]:
            self.message(t("fab.none"), warning=True)
            return None
        if path is None:
            start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, t("fab.export"),
                                                            os.path.join(start, t("fab.file") + ".dxf"), "DXF (*.dxf)")
            if not path:
                return None
        panels, lengths = fabrication.write_dxf(path, self.doc, guids)
        self.message(t("info.fab_exported", f=os.path.basename(path), p=panels, s=lengths))
        return path

    def export_cut_list(self, guids=None, path=None):
        """The cut list to an Excel workbook (0.370) or a CSV file, by its extension (asked for when not given).
        Returns its path, or None."""
        from . import cutlist_dialog as cd
        rows, hardware, areas = bim.cut_list(self.doc, guids)
        if not rows:
            return None
        if path is None:
            start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
            path = self._table_path(t("cut.export"), os.path.join(start, t("cut.title") + ".xlsx"))
            if path is None:
                return None
        count = len(self.doc.ifc.cabinets(set(guids) if guids else None))
        if not self._write_table(path, [t("cut.col." + c) for c in cd.COLUMNS],
                                 cd.table_of(rows) + [[], [cd.summary_text(count, rows, hardware, areas)]],
                                 t("cut.title")):
            return None
        self.message(t("info.cut_exported", f=os.path.basename(path)))
        return path

    def structure_quantities(self):
        """Structure ▸ Structure quantities… (0.167): each concrete member's concrete, formwork and steel, the totals;
        exported to CSV. Returns the rows."""
        from . import quantities_dialog
        self.tool.cancel()
        names = {o.id: o.name for o in self.doc.objects.values() if o.is_bim}
        dialog = quantities_dialog.QuantitiesDialog(self, lambda: bim.structure_quantities(self.doc), names)
        dialog.on_select = lambda ids: self._select_from_tree([i for i in ids if self.doc.get(i) is not None])
        dialog.on_export = lambda: self.export_structure_quantities()
        self._quantities_dialog = dialog
        dialog.exec()
        self._quantities_dialog = None
        return dialog.rows

    def export_structure_quantities(self, path=None):
        """The structure's quantities to an Excel workbook (0.370) or a CSV file, by its extension (asked for when
        not given). Returns its path, or None."""
        from . import quantities_dialog as qd
        names = {o.id: o.name for o in self.doc.objects.values() if o.is_bim}
        rows = qd.ordered(bim.structure_quantities(self.doc), names)
        if not rows:
            return None
        if path is None:
            start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
            path = self._table_path(t("qty.export"), os.path.join(start, t("qty.title") + ".xlsx"))
            if path is None:
                return None
        if not self._write_table(path, [t("qty.col." + c) for c in qd.COLUMNS], qd.table_of(rows, names),
                                 t("qty.title")):
            return None
        self.message(t("info.qty_exported", f=os.path.basename(path)))
        return path

    def calc_report(self, path=None):
        """Structure ▸ Calculation report… (0.167): the structure worked out — project, codes and materials, actions,
        the model's check, the analysis, the EC2 verification, quantities, reinforcement — as an HTML page or a PDF
        (by the file's extension). Returns its path, or None."""
        from ..model import structure_report
        self.tool.cancel()
        if path is None:
            base = os.path.splitext(self.doc.path)[0] + " - " if self.doc.path else os.path.join(_documents_dir(), "")
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, t("report.save"), base + t("act.calc_report").rstrip("…") + ".pdf",
                "PDF (*.pdf);;HTML (*.html)")
            if not path:
                return None
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            page = structure_report.report_html(bim.report_data(self.doc))
            if path.lower().endswith(".pdf"):
                from .report_pdf import html_to_pdf
                html_to_pdf(page, path)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(page)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        self.message(t("info.calc_report_saved", f=os.path.basename(path)))
        return path

    def steel_report(self, path=None):
        """(0.521) Analisar ▸ Memória de cálculo (aço)…: the steel structure worked out — project, codes, actions, model,
        the EC3 verification of each piece and connection, the bill of materials — as an HTML page or a PDF (by the
        file's extension). Returns its path, or None."""
        from ..model import steel_report
        self.tool.cancel()
        if not any(True for o in self.doc.objects.values() if o.is_bim and self.doc.ifc.steel_section(o.id)):
            self.message(t("info.steel_report_none"), warning=True)
            return None
        if path is None:
            base = os.path.splitext(self.doc.path)[0] + " - " if self.doc.path else os.path.join(_documents_dir(), "")
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, t("report.save"), base + t("act.steel_report").rstrip("…") + ".pdf",
                "PDF (*.pdf);;HTML (*.html)")
            if not path:
                return None
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            page = steel_report.report_html(steel_report.report_data(self.doc))
            if path.lower().endswith(".pdf"):
                from .report_pdf import html_to_pdf
                html_to_pdf(page, path)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(page)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        self.message(t("info.calc_report_saved", f=os.path.basename(path)))
        return path

    def structure_actions(self):
        """Structure ▸ Actions and materials… (0.164): the structure's settings, each storey's loads, wind and
        seismic forces worked out as they change; OK keeps them and loads the analytical model. Returns the loads,
        or None."""
        from . import actions_dialog
        self.tool.cancel()
        dialog = actions_dialog.ActionsDialog(self, self.doc.ifc.structural_settings(),
                                              lambda s: bim.actions_of(self.doc, s))
        self._actions_dialog = dialog
        accepted = dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
        self._actions_dialog = None
        if not accepted:
            return None
        _model, loads = bim.structural_actions(self.doc, dialog.settings())
        self.set_show_analytical(True)
        self.message(t("info.actions", n=len(loads.storeys), b="{:.1f}".format(loads.base_1).replace(".",
                                                                                                    decimal_sep())))
        return loads

    def structure_check(self):
        """Structure ▸ Analytical model and check… (0.163): the analytical model made again from the columns, beams,
        footings and slabs (written to the IFC) and its problems listed; the model shown over the model."""
        from . import structure_check_dialog as scd
        self.tool.cancel()

        def make():
            model = bim.analytical_model(self.doc)
            self.set_show_analytical(True)
            return model

        dialog = scd.StructureCheckDialog(self, make)
        dialog.on_select = lambda ids: self._select_from_tree([i for i in ids if self.doc.get(i) is not None])
        self._structure_dialog = dialog
        if dialog.model.walls:                    # (0.335) its load-bearing walls
            self.message(t("info.analytical_walls", n=len(dialog.model.members), w=len(dialog.model.walls),
                           s=len(dialog.model.supports)))
        elif dialog.model.members:
            self.message(t("info.analytical", n=len(dialog.model.members), s=len(dialog.model.supports)))
        else:                                     # (0.325) why there is nothing to calculate, and what to do
            self.message(t("info.analytical_empty"), warning=True, action=self.act_propose_structure)
        dialog.exec()
        self._structure_dialog = None
        return dialog.model

    def model_from_scan(self):
        """BIM ▸ Model from the point cloud… (0.162): of a linked scan, its floor and height, the walls read in a
        slice of it (pairs of faces; a façade seen from inside only, outwards), shown as found; then made on the
        scan's storey with a floor slab under them: one undo step. Returns their GlobalIds, or None."""
        from . import scan_dialog
        links = [c for c in self.doc.cloud_links if c.visible]
        if not links:
            self.message(t("err.scan_no_cloud"), warning=True, action=self.act_cloud_link)        # (0.324)
            return None

        def show(axes, link, floor, arcs=()):
            z = floor + 0.05
            segs = [np.array((p[0], p[1], z)) for a, b, _t in axes for p in (a, b)]
            for centre, radius, start, sweep, _t in arcs:     # (the curved walls found, 0.215)
                n = max(int(abs(sweep) / np.radians(7.5)) + 1, 2)
                ring = [np.array((centre[0] + radius * np.cos(start + sweep * k / n),
                                  centre[1] + radius * np.sin(start + sweep * k / n), z)) for k in range(n + 1)]
                segs += [p for a, b in zip(ring[:-1], ring[1:]) for p in (a, b)]
            self.viewport.show_polygon([], segments=segs, colors=[(0.12, 0.37, 0.84, 1.0)] * len(segs))

        self.tool.cancel()
        dialog = scan_dialog.ScanDialog(self, links, show)
        self._scan_dialog = dialog
        accepted = dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
        self._scan_dialog = None
        self.viewport.clear_overlays()
        if not accepted or not (dialog.axes or dialog.arcs):
            return None
        link = dialog.link()
        if len(dialog.per_storey) > 1:                      # (0.214: every storey of the cloud, one undo step)
            report = self._model_from_scan_storeys(dialog)
        else:
            slab = None
            if dialog.slab.isChecked() and dialog.outline is not None:
                slab = (dialog.outline, catalog.BY_KEY["laje_15"])
            report = bim.model_from_cad(self.doc, dialog.axes, dialog.openings, height=dialog.height.value(),
                                        storey=link.storey, slab=slab, arcs=dialog.arcs)   # (0.213, 0.215)
        text = t("info.scanmodel", w=len(report["walls"]), s=len(report["slabs"]))
        if report.get("storeys"):
            text += " " + t("info.scanmodel_storeys", n=report["storeys"])
        if report["doors"] or report["windows"]:
            text += " " + t("info.scanmodel_openings", d=len(report["doors"]), j=len(report["windows"]))
        self.message(text)
        self._last_scan_model = report
        return report["walls"]

    def _model_from_scan_storeys(self, dialog):
        """(0.214) Each storey found in the cloud made: its storey (the project's at that height, else a new one),
        its walls, doors and windows and its floor slab — all one undo step. Returns the report of them all."""
        mark = self.doc.undo_mark()
        total = {"walls": [], "doors": [], "windows": [], "slabs": [], "furniture": [], "left": 0, "storeys": 0}
        for k, (floor, height, axes, outline, found, curved) in enumerate(dialog.per_storey):
            if not axes and not curved:
                continue
            storey = next((g for g, _n, z in self.doc.ifc.storeys() if abs(z - floor) <= 0.05), None)
            if storey is None:
                storey = bim.add_storey(self.doc, t("scan.storey_name", n=k), floor)
            slab = (outline, catalog.BY_KEY["laje_15"]) if dialog.slab.isChecked() and outline is not None else None
            report = bim.model_from_cad(self.doc, axes, found, height=height, storey=storey, level=floor, slab=slab,
                                        arcs=curved)
            for key_ in ("walls", "doors", "windows", "slabs", "furniture"):
                total[key_] += report[key_]
            total["left"] += report["left"]
            total["storeys"] += 1
        self.doc.join_since(mark, t("cmd.model_from_scan"))
        return total

    def cloud_links(self):
        """View ▸ Linked point clouds… (0.161)."""
        from . import cloud_dialog
        dialog = cloud_dialog.CloudDialog(self, self.doc, {g: n for g, n, _z in self.doc.storeys()})
        dialog.on_link = lambda: self.link_cloud()
        self._cloud_dialog = dialog
        dialog.exec()
        self._cloud_dialog = None
        return dialog

    def cad_links(self):
        """View ▸ Linked CAD drawings… (0.158): the DXF drawings linked — units, shown, locked, their layers."""
        from . import cad_dialog
        dialog = cad_dialog.CadDialog(self, self.doc, {g: n for g, n, _z in self.doc.storeys()})
        dialog.on_link = lambda: self.link_cad()
        self._cad_dialog = dialog
        dialog.exec()
        self._cad_dialog = None
        return dialog

    def earthworks(self):
        """View ▸ Cut and fill… (0.157): the terrains' platforms with the earth each takes away and brings, the
        totals; one can be deleted."""
        from . import earthworks_dialog
        terrains = self.doc.ifc.terrains() if not self.doc.loading else []
        dialog = earthworks_dialog.EarthworksDialog(self, self.doc, terrains)
        self._earthworks_dialog = dialog
        dialog.exec()
        self._earthworks_dialog = None
        return dialog

    def set_show_slopes(self, on=None):
        """View ▸ Terrain slopes (0.156): the terrains coloured by their slope — the legend on the status bar. The
        view's own property (0.201): a plan shows them on its sheets too."""
        on = self.act_slopes.isChecked() if on is None else bool(on)
        self.act_slopes.setChecked(on)
        self.viewport.set_show_slopes(on)
        self.doc.set_view_props(self.viewport.current_view() or self._live_3d(), slopes=on or None)
        if on:
            self.message(t("info.slopes"))

    def import_terrain_dxf(self, path=None, layers=None):
        """File ▸ Terrain from a DXF… (0.156): a survey drawing's points with a height (points, contour lines,
        3D lines and faces, blocks, spot heights written), the layers to take chosen (those with heights ticked);
        far from the origin as the survey points' (import_terrain_points). Returns the terrain's GlobalId or None."""
        from ..core import dxf_read
        if path is None:
            start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("act.terrain_dxf"), start,
                                                            "DXF / DWG (*.dxf *.dwg)")
            if not path:
                return None
        name = os.path.basename(path)
        if not self._dwg_ready(path):
            return None
        try:
            found = dxf_read.read_file(path)
        except (OSError, ValueError) as exc:
            self.message(t("err.dxf_read", f=name, e=exc), warning=True)
            return None
        heights = dxf_read.with_heights(found)
        if not heights:
            self.message(t("err.dxf_none", f=name), warning=True)
            return None
        if layers is None:
            from .dxf_points_dialog import DxfPointsDialog
            dialog = DxfPointsDialog(self, name, {k: found[k] for k in heights}, heights)
            self._dxf_points_dialog = dialog
            accepted = dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
            self._dxf_points_dialog = None
            if not accepted:
                return None
            layers = dialog.chosen()
        points = [p for k in layers if k in found for p in found[k]]
        return self.import_terrain_points(points=np.array(points, dtype=float).reshape(-1, 3), name=name)

    def background_images(self):
        """View ▸ Background images… (0.154): the list of them — width, opacity, shown, locked; import, calibrate,
        delete."""
        from . import images_dialog
        dialog = images_dialog.ImagesDialog(self, self.doc, {g: n for g, n, _z in self.doc.storeys()},
                                            self.viewport.picture_missing)
        dialog.on_import = lambda: self.import_image()
        self._images_dialog = dialog
        dialog.exec()
        self._images_dialog = None
        if dialog.calibrate:
            self.set_tool("calibrate_image")
            self.tool.only = dialog.calibrate
            self.set_hint(self.tool.hint())
        elif dialog.facade:                                 # (0.208: stood up on a facade)
            self.stand_image(dialog.facade)
        elif dialog.crop:                                   # (0.209: the part of it kept)
            self.crop_image(dialog.crop)
        return dialog

    def crop_image(self, uid):
        """(0.209) Recortar: the tool that keeps a part of this background image."""
        self.tools["crop_image"].only = uid
        self.set_tool("crop_image")
        self.set_hint(self.tool.hint())

    def stand_image(self, uid):
        """(0.208) Pôr numa fachada: the tool that stands this background image up on a face of the model."""
        self.tools["facade_image"].only = uid
        self.set_tool("facade_image")
        self.tools["facade_image"].only = uid
        self.set_hint(self.tool.hint())

    def import_components(self, path=None):
        """BIM ▸ Bring components from another project: an IFC file's furniture, fixtures… (types
        with their shape) into this project's library, to place copies of."""
        if path is None:
            start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("act.import_components"), start, t("file.filter"))
            if not path:
                return
        name = os.path.basename(path)
        try:
            library, found = self.run_busy(lambda: IfcModel.read_library(path), t("lib.reading", f=name))
        except Exception as exc:      # not an IFC file, damaged…
            self.message(t("err.open", f=name, e=exc), warning=True)
            return
        if not found:
            self.message(t("lib.none", f=name), warning=True)
            return
        chosen = self._choose_components(name, found)
        if not chosen:
            return
        guids = bim.import_components(self.doc, library, chosen)
        names = ", ".join(self.doc.ifc.by_guid(g).Name or "" for g in guids)
        self.message(t("info.imported", n=len(guids), names=names))
        self.tree_panel.raise_()

    def import_model(self, path=None, how=None, name=None, category="furniture", where="click", unit=None, up=None):
        """(0.351) Import ▸ 3D model: a SketchUp, Rhino, glTF / GLB, OBJ or STL file (model/mesh_import.py) brought in
        — as a component (how "component": an IFC type keeping its shape once, its pieces in their colours, of the
        `category`; where "click": placed after where clicked, as the library's, or "file": where it is in the file)
        or as a sketch ("sketch": where it is in the file, its faces whole). How, name, category, where, the unit and
        the vertical of an OBJ / STL asked when `how` is not given. Returns the type's GlobalId or the sketch's id,
        or None."""
        from ..model import mesh_import
        if path is None:
            start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("act.import_model"), start,
                                                            t("model3d.import_filter"))
            if not path:
                return None
        file_name = os.path.basename(path)
        try:
            model = self.run_busy(lambda: mesh_import.read(path), t("lib.reading", f=file_name))
        except ValueError as exc:
            self.message(t("err.model3d_empty", f=file_name) if str(exc) == "empty" else
                         t("err.model3d", f=file_name, e=exc), warning=True)
            return None
        except OSError as exc:
            self.message(t("err.model3d", f=file_name, e=exc), warning=True)
            return None
        if how is None:
            answer = self._import_model_dialog(model)
            if answer is None:
                return None
            how, name, category, where, unit, up = answer
        name = name or model.name
        self._stop_drawing()
        if how == "sketch":
            sketch_id = self.run_busy(lambda: bim.import_model_sketch(self.doc, model, name, unit, up),
                                      t("model3d.working"))
            self.viewport.set_selection({sketch_id})
            self.message(t("info.model3d_sketch", name=name, n=len(self.doc.get(sketch_id).mesh.faces)))
            return sketch_id
        type_guid = self.run_busy(lambda: bim.import_model_component(self.doc, model, name, category, unit, up,
                                                                     in_place=where == "file"), t("model3d.working"))
        if where == "file":
            self.viewport.set_selection(set(self.doc.ifc.component_instances(type_guid)))
            self.message(t("info.model3d_component", name=name))
        else:
            self.tools["place"].use(type_guid)
            self.set_tool("place")
            self.message(t("info.model3d_place", name=name))
        return type_guid

    def _import_model_dialog(self, model):
        """(0.351) How a 3D file read comes in: (how, name, category, where, unit, up), or None (Cancel). Its size in
        metres shown, following the unit and the vertical asked for an OBJ / STL (a file that says neither)."""
        from ..model import mesh_import
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(t("act.import_model").rstrip("…"))
        form = QtWidgets.QFormLayout(dlg)
        summary = t("model3d.summary", f=model.name, tri=model.triangles(), n=len(model.parts))
        if model.skipped:
            summary += "\n" + t("model3d.skipped", n=model.skipped)
        about = QtWidgets.QLabel(summary)
        about.setWordWrap(True)
        form.addRow(about)
        how = QtWidgets.QComboBox()
        for k in ("component", "sketch"):
            how.addItem(t("model3d.as." + k), k)
        name = QtWidgets.QLineEdit(model.name)
        kind = QtWidgets.QComboBox()
        for category in bim.COMPONENT_CATEGORIES:
            kind.addItem(t("cat." + category), category)
        where = QtWidgets.QComboBox()
        for k in ("click", "file"):
            where.addItem(t("model3d.where." + k), k)
        unit = QtWidgets.QComboBox()
        for k in mesh_import.UNITS:
            unit.addItem(t("model3d.unit." + k), k)
        unit.setCurrentIndex(unit.findData(model.unit))
        up = QtWidgets.QComboBox()
        for k in ("z", "y"):
            up.addItem(t("model3d.up." + k), k)
        up.setCurrentIndex(up.findData(model.up))
        size = QtWidgets.QLabel()
        form.addRow(t("model3d.as"), how)
        form.addRow(t("props.name"), name)
        form.addRow(t("props.kind"), kind)
        form.addRow(t("model3d.where"), where)
        if not model.known:
            form.addRow(t("model3d.unit"), unit)
            form.addRow(t("model3d.up"), up)
        form.addRow(t("model3d.size"), size)

        def refresh():
            w, d, h = model.size(unit.currentData(), up.currentData())
            size.setText(" × ".join(format_length(round(float(v), 3), decimal_sep(), 2, "m") for v in (w, d, h)))
            component = how.currentData() == "component"
            kind.setEnabled(component)
            where.setEnabled(component)

        for box in (how, unit, up):
            box.currentIndexChanged.connect(refresh)
        refresh()
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)
        dlg.resize(460, dlg.sizeHint().height())
        self._model3d_dialog = dlg                       # (tests read and answer it)
        dlg.widgets = {"about": about, "how": how, "name": name, "kind": kind, "where": where, "unit": unit, "up": up,
                       "size": size}
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return None
        return (how.currentData(), name.text().strip() or model.name, kind.currentData(), where.currentData(),
                unit.currentData(), up.currentData())

    def _choose_components(self, file_name, found):
        """A list of another file's components to tick; the entity ids of those chosen."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(t("lib.title"))
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addWidget(QtWidgets.QLabel(t("lib.pick", f=file_name)))
        items = QtWidgets.QListWidget()
        for entity_id, name, cls, copies in found:
            item = QtWidgets.QListWidgetItem(t("lib.item", name=name, cls=cls[3:].replace("Type", ""), n=copies))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, entity_id)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            items.addItem(item)
        items.itemClicked.connect(lambda it: it.setCheckState(
            QtCore.Qt.CheckState.Unchecked if it.checkState() == QtCore.Qt.CheckState.Checked
            else QtCore.Qt.CheckState.Checked))
        layout.addWidget(items)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.resize(520, 420)
        self._components_dialog = dialog                  # (tests tick and accept it)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return []
        return [items.item(k).data(QtCore.Qt.ItemDataRole.UserRole) for k in range(items.count())
                if items.item(k).checkState() == QtCore.Qt.CheckState.Checked]

    def _leave_plan(self):
        if self.act_plan.isChecked():
            self.act_plan.blockSignals(True)
            self.act_plan.setChecked(False)
            self.act_plan.blockSignals(False)

    def _enter_section(self, index):
        """A named section (its index), in its tab."""
        if index is None or not 0 <= index < len(self.doc.sections):
            return
        self.doc.last_section = index
        self.views.open(("section", self.doc.sections[index].name))

    def _show_section(self, index):
        if index is None or not 0 <= index < len(self.doc.sections):
            return
        self.doc.last_section = index
        view = self.doc.sections[index]
        self._leave_plan()
        self.set_tool("select")
        self._view_name = view.name
        self._apply_view(("section", view.name))
        self.viewport.set_section(view.point, view.normal, ("section", view.name))
        self._refresh_storeys()
        self.message(t("info.section", name=view.name))

    def show_elevation(self, side):
        """Elevation N / S / E / W, in its tab: the whole model seen from that side, from outside —
        a section whose plane is behind the viewer, so nothing is cut."""
        self.views.open(("elevation", side))

    def _show_elevation(self, side):
        looks = drawings.ELEVATION_LOOKS[side]
        objects = [o for o in self.doc.objects.values() if o.is_bim] or list(self.doc.objects.values())
        center, radius = self.viewport.scene_bounds(objects or None)
        normal = np.array(looks)
        self._leave_plan()
        self.set_tool("select")
        self._view_name = t("tree.elevation_title", side=t("tree.elevation." + side))
        self._apply_view(("elevation", side))
        self.viewport.set_section(center - normal * (radius + 1.0), normal, ("elevation", side))
        self._refresh_storeys()
        self.message(t("info.elevation", name=self._view_name))

    def delete_guides(self):
        """Edit ▸ Delete guide lines: all of them, in one undo step."""
        if not self.doc.guides:
            self.message(t("info.no_guides"))
            return
        n = len(self.doc.guides)
        self.tool.cancel()
        self.doc.execute(RemoveGuides(list(self.doc.guides.values()), t("act.delete_guides")))
        self.message(t("info.guides_deleted", n=n))

    def show_help(self, tab=None):
        """F1 / the header's «?»: the Help window (0.327; it was a list of keys) — on the tool in use, or on Find."""
        from . import help_window
        if self._help is None:
            self._help = help_window.dock(self).widget()
        if tab is None:
            tab = "tool" if self.tool is not None and self.tool.name not in QUIET_TOOLS else "find"
        self._help.open_on(tab)
        return self._help

    def show_command(self, name):
        """(0.327) Where a command is: its discipline's tab chosen and its button lit a moment (in a folded panel:
        the panel's button). A command of the contextual tab (walls selected) is said to be there. False if it is not
        on the ribbon."""
        from . import help_window
        found = help_window.where(name)
        if found is None:
            return False
        tab, _panel = found
        if tab.startswith("ctx:"):
            if self.context_tab != tab[4:]:
                self.message(t("help.needs_" + tab[4:]))
                return False
            self._show_ribbon(tab)
        else:
            self.set_discipline(tab)
        main = next((ribbon.names_of(i)[0] for _key, items in ribbon.panels_of(tab) for i in items
                     if isinstance(i, list) and name in i), name)          # (0.482: in a button's arrow — that button)
        button = next((b for b in self.ribbon.findChildren(ribbon.RibbonButton) if b.objectName() == main), None)
        if button is None:
            return False
        panel = button.parent()
        while panel is not None and not isinstance(panel, ribbon.Panel):
            panel = panel.parent()
        target = panel.folded if panel is not None and panel.is_folded() else button
        if panel is not None and panel.isHidden() and self.ribbon.overflow is not None:
            target = self.ribbon.overflow                                  # (0.482: in «»», the panels left over)
        target.setStyleSheet("QToolButton { background: %s; border: 2px solid %s; border-radius: 4px; }"
                             % (theme.C["target"], theme.C["target_border"]))
        self._lit = target

        def unlit():
            try:
                target.setStyleSheet("")
            except RuntimeError:                  # (the ribbon was filled again meanwhile: that button is gone)
                pass
        QtCore.QTimer.singleShot(2500, unlit)
        return True

    def use_command(self, name):
        """(0.327) Help ▸ Find ▸ Use: the command shown on the ribbon and run (a tool: chosen)."""
        self.show_command(name)
        item = self.ribbon_item(name)
        if isinstance(item, QtGui.QAction):
            item.trigger()
            return True
        return False

    def use_opening_type(self, spec):
        """Choose a door/window type and switch to its tool."""
        self.tools[spec.kind].set_spec(spec)
        self.set_tool(spec.kind)

    def use_draw_type(self, spec):
        """Choose a wall/slab type and switch to the Wall/Slab tool."""
        self.tools[spec.kind].set_spec(spec)
        self.set_tool(spec.kind)

    def classify(self, spec):
        # (0.310) a face of a sketch volume picked alone classifies its volume: one click and the type, as before
        ids = [i for i in self.viewport.objects_picked() if self.doc.get(i) is not None and not self.doc.get(i).is_bim]
        type_name = spec.name_pt if lang() == "pt" else spec.name_en
        if not ids:
            # Nothing selected yet: the next click on a sketch volume classifies it.
            self.set_tool("select")
            self.pending_classify = spec
            self.set_hint(self.tool.hint())
            self.message(t("hint.classify_pick", type=type_name))
            return None
        self.pending_classify = None
        if self.tool.name == "select":
            self.set_hint(self.tool.hint())
        try:
            res = bim.classify(self.doc, ids, spec)
        except Exception as exc:  # e.g. an IFC2x3 file from another program: the IFC change was rolled back
            QtWidgets.QMessageBox.warning(self, t("app.title"), t("err.classify_failed", e=exc))
            return None
        if res.guids:
            self.viewport.set_selection(set(res.guids))
            self.props.show()
            if res.adjusted:
                self.message(t("warn.adjusted", n=len(res.adjusted), type=type_name), warning=True)
            else:
                self.message(t("info.classified", n=len(res.guids), type=type_name))
        if res.refused:
            QtWidgets.QMessageBox.information(self, t("app.title"), t("dlg.not_box", type=type_name))
        return res

    def _on_property_edit(self, action, guid, value):
        """An edit made in the Properties panel -> one undoable command."""
        doc, ifc = self.doc, self.doc.ifc
        full = action
        if isinstance(action, tuple):                      # (one of several editors of the same kind)
            action = action[0]
        if action.startswith("ann_"):                      # (0.191) a drawing in the view: guid is it
            self._edit_annotation(action, guid, value)
            return
        if action == "dim_type":                           # (0.193) dimensions given a type: guid is them
            dims = [d for d in guid if d in self.doc.dimensions]
            if dims:
                self.doc.execute(dims_model.SetDimensionTypeOf(dims, value or None, t("cmd.dimension_type")))
                self.message(t("info.dimension_type", n=len(dims), k=value or t("dimtype.project")))
            return
        if isinstance(action, str) and action.startswith("dim_"):     # (0.405) a dimension's own, in the Properties
            self._dimension_property(action, guid, value)
            return
        if isinstance(action, str) and action.startswith("surface_"):      # (0.395) a parametric surface
            self._surface_property(action, guid, value)
            return
        if isinstance(action, str) and action.startswith("sheet_"):        # (0.470) a sheet's: guid is its uid
            self._sheet_property(action, guid, value)
            return
        try:
            if action == "line_length":                    # a line (0.62): the lines joined at its end follow
                line_edit.set_length(doc, *guid, value)
            elif action == "line_angle":
                line_edit.set_angle(doc, *guid, value)
            elif action == "line_point":
                line_edit.set_point(doc, *guid, value)
            elif action == "arc_radius" and line_edit.fillet_radius(doc, guid, value):
                # (0.455) a fillet's arc, as Revit's: still tangent to its two lines (they are trimmed / stretched)
                self.message(t("info.fillet_lines", r=format_length(value, decimal_sep())))
            elif action in ("arc_radius", "arc_angle", "arc_segments"):     # (0.373) an arc: made again from its data
                obj = doc.get(guid)
                scale = float(np.linalg.norm(obj.matrix[:3, 0]))
                arc = core_curves.arc_with(obj.curve, radius=value / scale if action == "arc_radius" else None,
                                           angle=(math.copysign(value, obj.curve["angle"]) if action == "arc_angle"
                                                  else None),
                                           segments=value if action == "arc_segments" else None)
                curve_edit.reshape(doc, guid, arc)
                self.message(t("info.arc_changed", r=format_length(core_curves.arc_radius(arc) * scale, decimal_sep()),
                               a=format_angle(abs(arc["angle"]), decimal_sep()), n=arc["segments"]))
            elif action in ("ellipse_axis", "ellipse_minor", "ellipse_segments"):     # (0.458) an ellipse, again
                obj = doc.get(guid)
                scale = float(np.linalg.norm(obj.matrix[:3, 0]))
                lengths = {} if action == "ellipse_segments" else {action[8:]: value / scale}
                curve = core_curves.ellipse_with(obj.curve, segments=value if action == "ellipse_segments" else None,
                                                 **lengths)
                curve_edit.reshape(doc, guid, curve)
                _c, a, b = core_curves.ellipse_axes(curve)
                self.message(t("info.ellipse_changed", a=format_length(float(np.linalg.norm(a)) * scale, decimal_sep()),
                               b=format_length(float(np.linalg.norm(b)) * scale, decimal_sep())))
            elif action == "change_storey":                # (0.527) as Revit's Level
                self.change_storey([guid], value)
                return
            elif action == "name":
                bim.rename(doc, guid, value)
            elif action == "mark":                         # (0.110) a door's / window's mark
                bim.set_mark(doc, guid, value)
            elif action == "type":
                bim.set_type(doc, guid, value)
            elif action == "element_type":                 # (0.414) a saved type put on it — or none
                self.apply_element_type([guid], value)
            elif action == "element_type_save":
                self.save_element_type(guid)
                return
            elif action == "element_type_update":
                self.update_element_type(guid)
                return
            elif action == "room_name":                    # (0.99) a room's name, number, finishes
                bim.set_room(doc, guid, name=str(value))
            elif action == "room_number":
                bim.set_room(doc, guid, number=str(value))
            elif action == "room_external":                # (0.357) interior / exterior
                bim.set_room(doc, guid, external=bool(value))
            elif action == "room_finish":
                bim.set_room(doc, guid, finishes={full[1]: str(value)})
            elif action == "room_use":                     # (0.416) chosen, or None: automatic
                bim.set_room_use(doc, guid, value or None)
            elif action == "room_dwelling":                # (0.416) named by hand, or "": found by the doors
                bim.set_room_dwelling(doc, guid, str(value or "").strip() or None)
            elif action == "edit_type":                    # (0.87) the type editor on this element's type
                QtCore.QTimer.singleShot(0, lambda: self.edit_types(value.kind, value.key))
                return
            elif action == "joinery":                      # (0.289) the generator on a door's / window's type
                QtCore.QTimer.singleShot(0, lambda: self.edit_opening_design(value))
                return
            elif action == "edit_railing_type":            # (0.260) a railing's type in its editor
                QtCore.QTimer.singleShot(0, lambda: self.edit_railing_types(value))
                return
            elif action == "edit_roof_blocks":             # (0.263) a roof by blocks' blocks in their editor
                QtCore.QTimer.singleShot(0, lambda: self.edit_roof_blocks(guid))
                return
            elif action == "roof_carpentry":               # (0.276) its carpentry made (again) or taken away
                if value == "sizes":                       # (0.277) its sizes chosen
                    QtCore.QTimer.singleShot(0, lambda: self.carpentry_sizes(guid))
                    return
                if value == "remove":
                    bim.remove_roof_carpentry(doc, guid)
                    self.message(t("info.carpentry_off"))
                else:
                    bim.set_roof_carpentry(doc, guid)
                    found = ifc.carpentry_summary(guid) or {}
                    self.message(t("info.carpentry", n=sum(v[0] for v in found.values()),
                                   v="{:.2f}".format(sum(v[2] for v in found.values())).replace(".", decimal_sep())))
            elif action in ("roof_tiles", "roof_tiles_kind", "roof_tiles_stagger"):   # (0.279) its tiles
                if action == "roof_tiles" and value == "remove":
                    bim.remove_roof_tiles(doc, guid)
                    self.message(t("info.tiles_off"))
                else:
                    kind = value if action == "roof_tiles_kind" else None
                    if kind is None and ifc.tiles_of(guid) is None:
                        kind = getattr(self.props.editors.get("roof_tiles_kind"), "currentData", lambda: None)()
                    bim.set_roof_tiles(doc, guid, kind, value if action == "roof_tiles_stagger" else None)
                    self._tiles_message(guid)
            elif action == "register_tile":                # (0.281) a component as a tile of the user's own
                QtCore.QTimer.singleShot(0, lambda: self.register_tile(guid, value))
                return
            elif action == "select_element":               # (0.279) another element (a tiles' roof) selected
                QtCore.QTimer.singleShot(0, lambda: self.viewport.set_selection({guid}))
                return
            elif action == "length":
                bim.resize_wall(doc, guid, at_end=value - ifc.wall_params(guid)[0])
            elif action == "height":
                bim.resize_wall(doc, guid, height=value)
            elif action == "column_height":
                bim.resize_column(doc, guid, value)
            elif action == "beam_length":
                bim.resize_beam(doc, guid, length=value)
            elif action == "beam_top":
                bim.resize_beam(doc, guid, top=value)
            elif action == "footing_length":
                bim.resize_footing(doc, guid, length=value)
            elif action == "footing_top":
                bim.resize_footing(doc, guid, top=value)
            elif action in ("c_base", "c_base_offset", "c_top", "c_top_offset"):    # base / top (0.73)
                bim.set_constraints(doc, guid, **{action[2:]: value})
            elif action == "grid_tag":                     # a grid axis (0.72): guid is its index
                if not bim.rename_grid_axis(doc, guid, value):
                    self.message(t("err.grid_tag", tag=value), warning=True)
            elif action == "grid_point":
                axis = doc.grids[guid]
                start, end = (value, axis.end) if full[1] == "start" else (axis.start, value)
                bim.move_grid_axes(doc, {guid: (start, end)})
            elif action == "segment_length":
                bim.resize_segment(doc, guid, length=value)
            elif action == "segment_z":
                bim.resize_segment(doc, guid, z=value)
            elif action == "system":                       # (0.141) the whole run into that system
                if value:
                    bim.set_system(doc, guid, value)
            elif action in ("circuit_name", "circuit_breaker", "circuit_section"):    # (0.144) a circuit's
                bim.edit_circuit(doc, guid, **{action[8:]: value})
            elif action in ("ceiling_style", "ceiling_height", "ceiling_gap"):           # (0.118) a ceiling
                bim.set_ceiling(doc, guid, **{action[8:]: value})
            elif action == "flooring_finish":              # (0.415) a floor finish's finish
                bim.set_flooring(doc, guid, value)
            elif action in ("ceiling_bulkhead", "ceiling_drop"):          # (0.119) its bulkhead: width, drop
                params = ifc.describe(guid)["params"]
                width = value if action == "ceiling_bulkhead" else params["bulkhead"]
                drop = value if action == "ceiling_drop" else params["drop"]
                bim.set_ceiling(doc, guid, bulkhead=(width, drop if width <= 0 or drop > 0 else 0.30))
            elif action in ("cladding_finish", "cladding_height", "cladding_width", "cladding_gap",
                            "cladding_direction", "cladding_diameter", "cladding_pitch", "cladding_margin",
                            "cladding_amplitude", "cladding_wavelength", "cladding_shift",
                            "cladding_depth",                               # (0.119; its pattern: 0.173, 0.175)
                            "cladding_hole", "cladding_grid", "cladding_sheet_w", "cladding_sheet_h",
                            "cladding_joint", "cladding_mask", "cladding_start", "cladding_end",
                            "cladding_base",                                # (0.389) a perforated panel's
                            "cladding_thickness", "cladding_frame", "cladding_battens", "cladding_batten_w",
                            "cladding_batten_d"):                           # (0.434) a slatted panel's
                if action == "cladding_mask" and value == "__escolher__":
                    value = self.choose_image()
                    if not value:                          # (none chosen: the list as it was)
                        self._refresh_properties()
                        return
                bim.set_cladding(doc, guid, **{action[9:]: value})
            elif action.startswith("organic_"):            # (0.390) an organic roof's measures
                bim.set_organic_roof(doc, guid, **{action[8:]: value})
            elif action == "keynote":                      # (0.194) its type's keynote
                bim.set_keynote(doc, guid, value)
            elif action == "cw2_embed":                    # (0.188) into the wall it lies in, or out of it
                bim.set_curtain_embedding(doc, guid, bool(value))
            elif action in ("cw2_length", "cw2_height", "cw2_mullions", "cw2_transoms"):    # (0.117)
                bim.set_curtain_wall(doc, guid, **{action[4:]: value})
            elif action in ("terrain_interval", "terrain_depth"):         # (0.155) a terrain
                bim.set_terrain_params(doc, guid, **{action[8:]: value})
            elif action in ("railing_style", "railing_height"):           # (0.115) a railing
                bim.set_railing(doc, guid, **{action[8:]: value})
            elif action in ("railing_ext_base", "railing_ext_top"):       # (0.282) its handrail's extensions
                base, top = ifc.railing_params(guid)["extend"]
                bim.set_railing(doc, guid, extend=(value, top) if action.endswith("base") else (base, value))
            elif action in ("profile_profile", "profile_width", "profile_height", "profile_foot",
                            "profile_side"):                              # (0.174) a profile
                bim.set_profile(doc, guid, **{action[8:]: value})
            elif action in ("stair_form", "stair_turn", "stair_width", "stair_going", "stair_rise"):   # (0.114)
                bim.set_stair(doc, guid, **{action[6:]: value})
            elif action == "cab_compartments" or action.startswith("cab_fill_"):    # (0.172) its compartments
                fills = list(doc.ifc.cabinet_params(guid).compartments)
                if action == "cab_compartments":
                    fills = (fills + ["shelves"] * 5)[:int(value)]
                    bim.set_cabinet(doc, guid, interior="" if fills == ["shelves"] else ",".join(fills),
                                    splits="")                    # (0.244: their widths even again)
                else:
                    fills[int(action[len("cab_fill_"):])] = value
                    bim.set_cabinet(doc, guid, interior="" if fills == ["shelves"] else ",".join(fills))
            elif action.startswith("cab_cwidth_"):            # (0.244) a compartment's width: its division moves
                from ..core import cabinets as core_cab
                c = doc.ifc.cabinet_params(guid)
                k, mids, spans = int(action[len("cab_cwidth_"):]), list(c.divisions), c.compartment_spans()
                if k < len(mids):                             # (its right one; the last's: its left one)
                    mids[k] = spans[k][0] + float(value) + core_cab.BOARD / 2
                else:
                    mids[k - 1] = spans[k][1] - float(value) - core_cab.BOARD / 2
                bim.set_cabinet(doc, guid, splits=",".join("{:g}".format(round(v, 3)) for v in mids))
            elif action.startswith("cab_"):                                  # (0.169) a cabinet
                bim.set_cabinet(doc, guid, **{action[4:]: value})
            elif action in ("roof_form", "roof_slope", "roof_overhang", "roof_eave"):     # (0.111) a roof
                bim.set_roof(doc, guid, **{action[5:]: value})
            elif action == "cw_radius":                    # (0.103) a curved wall's radius, sweep, height
                bim.set_curved_wall(doc, guid, radius=value)
            elif action == "cw_sweep":                     # (degrees typed; it keeps turning the same way)
                sweep = ifc.curved_wall_params(guid)[3]
                bim.set_curved_wall(doc, guid, sweep=math.copysign(math.radians(value), sweep))
            elif action == "cw_height":
                bim.set_curved_wall(doc, guid, height=value)
            elif action in ("ramp_length", "ramp_width", "ramp_rise"):     # (0.101) a ramp's sizes
                bim.set_ramp(doc, guid, **{action[5:]: value})
            elif action == "slab_function":                # (0.100) a slab's function, its radius, its outline
                bim.set_slab_function(doc, [guid], value)
            elif action == "slab_use":                     # (0.218) its own use, for its loads
                bim.set_slab_use(doc, [guid], value or "")
            elif action == "slab_radius":
                bim.set_slab_radius(doc, guid, value)
            elif action in ("screen_length", "screen_height", "screen_direction", "screen_width", "screen_gap",
                            "screen_thickness", "screen_frame", "screen_battens"):     # (0.441) a slatted screen
                bim.set_ripado_screen(doc, guid, **{action[7:]: value})
            elif action in ("loose_piece", "loose_width", "loose_depth", "loose_height"):   # (0.440)
                bim.set_loose(doc, guid, **{action[6:]: value})
            elif action in ("gutter_shape", "gutter_downpipes"):        # (0.438) a gutter's section, its downpipes
                bim.set_gutter(doc, guid, **{action[7:]: value})
            elif action == "connection_equal":            # (0.505) its values to the alike nodes
                changed, made = bim.apply_to_equal(doc, guid)
                self.message(t("info.apply_equal", changed=changed, made=made) if changed or made
                             else t("info.apply_equal_none"), warning=not (changed or made))
            elif action.startswith("connection."):        # (0.497) a steel connection's value: made again
                bim.set_connection(doc, guid, **{action[len("connection."):]: value})
            elif action in ("wall_framing", "wall_framing_spacing", "wall_framing_blocking"):   # (0.437)
                if action == "wall_framing":
                    bim.set_wall_framing(doc, guid, kind=value or "")
                elif action == "wall_framing_spacing":
                    bim.set_wall_framing(doc, guid, spacing=value)
                else:
                    bim.set_wall_framing(doc, guid, blocking=int(value))
                found = ifc.framing_summary(guid)
                if found:
                    self.message(t("info.wall_framing", n=sum(n for n, _m in found.values()),
                                   m=format_length(sum(m for _n, m in found.values()), decimal_sep())))
            elif action == "slab_corner_z":                # (0.433) a corner's height over its top: its slope
                bim.set_slab_corner_height(doc, guid, full[1], value)
            elif action == "slab_slope":                   # (0.433) falling from a side, % (value: (%, side))
                bim.set_slab_slope(doc, guid, *value)
                self.message(t("info.slab_slope", s=int(value[1]) + 1,
                               p="{:.2f}".format(value[0]).rstrip("0").rstrip(".").replace(".", decimal_sep())))
            elif action == "slab_flat":                    # (0.433) flat again
                info = ifc.slab_outline(guid)
                if info is not None and info.get("heights"):
                    bim.set_slab_heights(doc, guid, [0.0] * len(info["outline"]))
            elif action == "edit_outline":
                QtCore.QTimer.singleShot(0, lambda: self.edit_slab_outline(guid))
                return
            elif action == "edit_profile":                 # (0.109)
                QtCore.QTimer.singleShot(0, lambda: self.edit_wall_profile(guid))
                return
            elif action in ("lx", "ly"):
                x0, y0, x1, y1, _t = ifc.slab_extents(guid)
                if action == "lx":
                    x1 = x0 + value
                else:
                    y1 = y0 + value
                bim.resize_slab(doc, guid, x0, y0, x1, y1)
            elif action in ("from_start", "to_end"):
                st = ifc.filling_state(guid)
                f = st["frame"]
                s = f.x0 + value if action == "from_start" else f.x0 + f.length - value - st["width"]
                bim.move_filling(doc, guid, s=s)
            elif action == "sill":
                bim.move_filling(doc, guid, sill=value)
            elif action in ("flip_hinge", "flip_side"):
                bim.flip_door(doc, guid, hinge=action == "flip_hinge", side=action == "flip_side")
            elif action == "status":
                self.set_phase(value, [guid])
            elif action == "pset":
                pset, prop, v = value
                bim.set_property(doc, guid, pset, prop, v)
            elif action == "pset_add":                     # + Property… (a length is given in metres)
                pset, prop, kind, v = value
                bim.set_property(doc, guid, pset, prop, v / ifc.unit_scale if kind == "length" else v)
                self.message(t("info.property_added", prop=prop, pset=pset))
            elif action.startswith("view_"):
                self._edit_view(full, guid, value)
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            self._refresh_properties()   # show the unchanged values again

    def _surface_property(self, action, guid, value, path=None, text=None):
        """(0.395) A parametric surface's change made in the Properties: a field of its form, of a modifier or of a
        section (model/surface_edits.py), its use (its class); or its parts list, its definition saved, read or
        edited as text. `path` / `text`: given (tests), no dialog."""
        import json
        from ..core import param_surface as ps
        from ..core import surface_build as sb
        from ..model import surface_edits
        doc, ifc = self.doc, self.doc.ifc
        e = ifc.by_guid(guid)
        name = (e.Name or "") if e is not None else ""
        base = os.path.splitext(self.doc.path)[0] if self.doc.path else os.path.join(_documents_dir(), name or "sup")
        try:
            if action == "surface_usage":
                bim.set_param_surface(doc, guid, usage=value)
            elif action == "surface_csv":
                if path is None:
                    path, _ = QtWidgets.QFileDialog.getSaveFileName(self, t("dlg.surface_csv"),
                                                                    "{} - {}.csv".format(base, name), "CSV (*.csv)")
                    if not path:
                        return
                sb.write_csv(path, ifc.surface_parts(guid), title=name)
                self.message(t("info.surface_csv", path=path))
            elif action == "surface_export":
                if path is None:
                    path, _ = QtWidgets.QFileDialog.getSaveFileName(self, t("dlg.surface_export"),
                                                                    "{} - {}.arqsurf".format(base, name),
                                                                    "ArqSynth (*.arqsurf *.json)")
                    if not path:
                        return
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(json.dumps(ifc.surface_definition(guid), ensure_ascii=False, indent=2) + "\n")
                self.message(t("info.surface_export", path=path))
            elif action in ("surface_import", "surface_text"):
                if action == "surface_import" and text is None:
                    if path is None:
                        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("dlg.surface_import"), base,
                                                                        "ArqSynth (*.arqsurf *.json)")
                        if not path:
                            return
                    with open(path, encoding="utf-8") as f:
                        text = f.read()
                elif text is None:
                    text = self._surface_text_dialog(json.dumps(ifc.surface_definition(guid), ensure_ascii=False,
                                                                indent=2))
                    if text is None:
                        return
                data, errors = ps.loads(text)
                if errors:
                    self.message(t("err.surface_import", e=" | ".join(errors[:3])), warning=True)
                    return
                bim.set_param_surface(doc, guid, data)
            else:
                if action.endswith(":mask") and value == "__escolher__":
                    value = self.choose_image()
                    if not value:
                        self._refresh_properties()
                        return
                data = surface_edits.apply_action(ifc.surface_definition(guid), action, value)
                bim.set_param_surface(doc, guid, data)
        except (ValueError, OSError) as exc:
            self.message(t("err.edit_refused", e=refusal(exc) if isinstance(exc, ValueError) else str(exc)),
                         warning=True)
            self._refresh_properties()

    def _surface_text_dialog(self, text):
        """(0.395) The definition as text to edit (JSON): the new text, or None if let go."""
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(t("dlg.surface_text"))
        lay = QtWidgets.QVBoxLayout(dlg)
        edit = QtWidgets.QPlainTextEdit(text)
        edit.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont))
        edit.setMinimumSize(560, 460)
        lay.addWidget(edit)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok |
                                             QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        lay.addWidget(buttons)
        return edit.toPlainText() if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted else None

    def _edit_annotation(self, action, ann, value):
        """(0.191) A drawing in the view changed in the Properties: its words, size, angle, hatch, line type, pen,
        a line's length (from its start), a circle's radius. One undo step."""
        if ann not in self.doc.annotations:
            return
        extra = dict(ann.extra)
        changes = {}
        if action == "ann_text":
            if not str(value).strip():
                self._refresh_properties()                 # (no words: as it was)
                return
            changes["text"] = str(value)
        elif action == "ann_size":
            changes["size"] = float(value)
        elif action == "ann_angle":
            extra["angle"] = (float(value) + 180.0) % 360.0 - 180.0
            changes["extra"] = extra
        elif action == "ann_hatch":
            changes["hatch"] = value
        elif action in ("ann_line", "ann_width"):
            key = "line" if action == "ann_line" else "width"
            if value and value != "continuous":
                extra[key] = value
            else:
                extra.pop(key, None)
            changes["extra"] = extra
        elif action in ("ann_length", "ann_radius"):       # (the second point moves: along, or round, the first)
            a, b = (np.asarray(p, dtype=float) for p in ann.points[:2])
            d = b - a
            if np.linalg.norm(d) < 1e-9 or value <= 0:
                return
            points = [np.asarray(p, dtype=float) for p in ann.points]
            points[1] = a + d / np.linalg.norm(d) * float(value)
            changes["points"] = points
        if changes:
            self.doc.execute(notes2d.EditAnnotation(ann, t("cmd.draft_edit"), **changes))
            self.message(t("info.ann_edit", k=t("draft." + ann.kind).lower()))

    def _on_property_edit_many(self, action, guids, value):
        """(0.187) A change made in the Properties to several elements: made in each of them, one undo step (the
        panel shown again once, at the end)."""
        mark = self.doc.undo_mark()
        self._editing_many = True
        try:
            for guid in guids:
                if self.doc.get(guid) is not None:
                    self._on_property_edit(action, guid, value)
        finally:
            self._editing_many = False
        done = self.doc.join_since(mark)
        self._refresh_properties()
        if done:
            self.message(t("info.edit_many", n=len(guids)))

    def _edit_view(self, action, view, value):
        """A view's property changed in the Properties panel (nothing selected): one undo step."""
        doc = self.doc
        if isinstance(action, tuple) and action[0] == "view_box":     # a section box's faces on one axis, typed
            box = doc.view_settings(view).box
            if box is not None:
                box = [list(box[0]), list(box[1])]
                box[0][action[1]], box[1][action[1]] = value
                doc.set_view_props(view, box=box)
                self.message(t("info.view_props", view=self._view_tab_label(view)))
            return
        if isinstance(action, tuple) and action[0] == "view_crop":   # a plan's crop region on one axis, typed
            crop = doc.view_settings(view).crop
            if crop is not None:
                crop = list(crop)
                crop[action[1]], crop[action[1] + 2] = value
                doc.set_view_props(view, crop=crop)
                self.message(t("info.view_props", view=self._view_tab_label(view)))
            return
        if action == "view_crop_on":                                  # on: round what the plan shows
            crop = None
            if value:
                box = self.viewport.bounds()
                if box is None:
                    self.message(t("info.box_nothing"), warning=True)
                    self._refresh_properties()
                    return
                (x0, y0, _z0), (x1, y1, _z1) = box
                crop = [float(x0) - 0.5, float(y0) - 0.5, float(x1) + 0.5, float(y1) + 0.5]
            doc.set_view_props(view, crop=crop)
            self.message(t("info.view_props", view=self._view_tab_label(view)))
            return
        if action == "view_box_on":                                   # on: round the whole model
            around = self.viewport.box_around(None) if value else None
            box = [[float(c) for c in around[0]], [float(c) for c in around[1]]] if around is not None else None
            if value and box is None:
                self.message(t("info.box_nothing"), warning=True)
                self._refresh_properties()
                return
            doc.set_view_props(view, box=box)
            self.message(t("info.box_on" if box else "info.box_off"))
            return
        if action == "view_name" and view[0] == "3d":
            self._rename_view3d(view[1], value)
            return
        if action == "view_name":
            index = next((k for k, s in enumerate(doc.sections) if s.name == view[1]), None)
            if index is not None and not self._rename_section(index, value):
                self.message(t("err.view_name", name=value), warning=True)
                self._refresh_properties()
            return
        if action == "view_template":
            self.template_action("assign", view, value)
            return
        if action == "view_template_save":                 # (0.414) a template made of this view, given to it
            self.save_view_template(view)
            return
        if action == "view_cut" and not 0.10 - 1e-9 <= value <= 5.00 + 1e-9:
            self.message(t("err.cut_height"), warning=True)
            self._refresh_properties()
            return
        field = {"view_cut": "cut_height", "view_scale": "scale", "view_phases": "phases", "view_rule": "rule",
                 "view_hidden": "hidden", "view_style": "style", "view_edges": "edges", "view_grid": "grid",
                 "view_axonometric": "axonometric", "view_depth": "depth", "view_underlay": "underlay",
                 "view_detail": "detail", "view_slopes": "slopes"}[action]
        defaults = {"phases": "all", "style": "shaded", "edges": True, "grid": True, "axonometric": False,
                    "depth": 0.0, "detail": "fine", "slopes": False}
        if field == "cut_height":
            value = round(value, 3)
        elif field in defaults and value == defaults[field] and not (field == "style" and view[0] != "3d"):
            value = None                                   # (the default: not kept — 0.315: a drawing's style is)
        if doc.set_view_props(view, **{field: value}):
            self.message(t("info.view_props", view=self._view_tab_label(view)))

    # ------------------------------------------------------------ files

    def _file_label(self):
        return os.path.basename(self.doc.path) if self.doc.path else t("app.untitled")

    def _confirm_discard(self):
        """True if it is fine to drop the current document (saved, discarded or unchanged)."""
        if not self.doc.modified:
            return True
        buttons = QtWidgets.QMessageBox.StandardButton
        answer = QtWidgets.QMessageBox.question(
            self, t("app.title"), t("ask.save", f=self._file_label()),
            buttons.Save | buttons.Discard | buttons.Cancel, buttons.Save)
        if answer == buttons.Save:
            self.save()
            return not self.doc.modified
        return answer == buttons.Discard

    def new_document(self):
        if not self._confirm_discard():
            return
        self.tool.cancel()
        self.viewport.set_selection(set())
        self.reset_rule()
        self.set_box(False, store=False)
        self.doc.new()
        if self.presentation_mode is not None:    # (0.479: nothing chosen, nothing hidden)
            self.presentation_mode.reset()
        self.views.reset()                        # (only the 3D view's tab)
        self.viewport.set_view("iso")

    def open_file(self):
        if not self._confirm_discard():
            return
        start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("act.open"), start, t("file.filter"))
        if path:
            self.open_path(path)

    def open_path(self, path, remember=True):
        """Open an IFC file without freezing the window. The slow part (reading the IFC, the 3D
        shapes) runs in a worker thread (Phase 2, step 4). A file opened before is on screen
        at once, drawn from the shapes kept last time: one can look around — not edit — while
        its IFC is read, with the status bar saying so (step 7). Otherwise a progress window
        with Cancel. Returns True when the file is open. (0.387) `remember`: among the recent
        documents (not a base file opened as a new project)."""
        self.tool.cancel()
        self.viewport.set_selection(set())
        self.reset_rule()
        self.set_box(False, store=False)
        if self.presentation_mode is not None:    # (0.479: nothing chosen, nothing hidden)
            self.presentation_mode.reset()
        self.views.reset()                        # (only the 3D view's tab)
        start = time.perf_counter()
        name = os.path.basename(path)
        reader = _FileReader(path, self)
        dialog = QtWidgets.QProgressDialog(t("open.reading", f=name), t("open.cancel"), 0, 0, self)
        dialog.setWindowTitle(t("app.title"))
        dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        dialog.setAutoClose(False)
        dialog.setAutoReset(False)
        dialog.setMinimumDuration(10 ** 9)          # shown below, only if opening takes a while
        state = {"preview": None, "cancelled": False}   # preview: seconds until it was on screen

        def show_progress(stage, percent):
            if state["preview"] is None:
                self._open_progress(dialog, name, stage, percent)
            elif stage == "shapes":
                self.loading_label.setText(t("open.loading_shapes", f=name, p=max(0, percent)))

        def frame():
            # the view on the model once something is there (again at the end, if not moved meanwhile)
            if any(o.is_bim for o in self.doc.objects.values()):
                self.viewport.set_view("iso")
                state["view"] = self._camera_state()

        def show_preview():
            if state["cancelled"] or state.get("over"):
                return                              # (it came too late: this opening is over)
            reader.window_free.clear()              # the reader waits until this is drawn
            dialog.hide()
            self.viewport.adopt_pieces(reader.preview_pieces)
            try:
                self.doc.show_preview(reader.preview)
            finally:
                self.viewport.adopt_pieces({})
            frame()
            self._set_loading(True, name)
            state["preview"] = time.perf_counter() - start
            self.viewport.after_all_drawn(reader.window_free.set)     # (0.328: a few images, the batches a few each)
            loop.quit()

        def add_shapes():
            if state["cancelled"] or state.get("over") or state["preview"] is None:
                return
            reader.window_free.clear()              # the reader waits until these are drawn
            self.viewport.after_all_drawn(reader.window_free.set)
            while True:
                try:
                    meshes, pieces = reader.chunks.get_nowait()
                except queue.Empty:
                    break
                self.viewport.adopt_pieces(pieces)
                try:
                    self.doc.add_preview_shapes(meshes)
                finally:
                    self.viewport.adopt_pieces({})
                if state.get("first_shapes") is None:
                    state["first_shapes"] = time.perf_counter() - start
                    if state.get("view") is None:
                        frame()

        def cancel():
            state["cancelled"] = True
            reader.requestInterruption()
            loop.quit()

        loop = QtCore.QEventLoop()
        reader.finished.connect(loop.quit)
        reader.preview_ready.connect(show_preview)
        reader.shapes_ready.connect(add_shapes)
        dialog.canceled.connect(cancel)
        self.loading_cancel.clicked.connect(cancel)
        reader.progress.connect(show_progress)
        self._readers.add(reader)
        reader.finished.connect(lambda: self._readers.discard(reader))
        reader.start()
        # the first moments: clicks and keys wait (nothing may change the project being replaced) ...
        timer = QtCore.QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(OPEN_DIALOG_AFTER_MS)
        loop.exec(QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        timer.stop()
        if reader.isRunning() and state["preview"] is None and not state["cancelled"]:
            dialog.show()                           # ... then the progress window, which holds the rest
            loop.exec()
        if reader.isRunning() and state["preview"] is not None and not state["cancelled"]:
            loop.exec()                             # the model is on screen: look around while the IFC is read
        if dialog.wasCanceled() and not state["cancelled"]:   # (cancel() called directly emits no signal)
            cancel()
        if not state["cancelled"]:
            reader.wait()
            add_shapes()                            # the last shapes handed over, if still waiting
        state["over"] = True
        reader.progress.disconnect(show_progress)
        reader.preview_ready.disconnect(show_preview)
        reader.shapes_ready.disconnect(add_shapes)
        self.loading_cancel.clicked.disconnect(cancel)
        previewed = state["preview"] is not None
        if state["cancelled"] or reader.error is not None:
            dialog.deleteLater()
            if previewed:                           # the preview had replaced the project: none is left
                self._set_loading(False)
                self.doc.new()
                self.viewport.set_view("iso")
            if state["cancelled"]:                  # the reader stops by itself (reading the IFC cannot be cut short)
                self.message(t("info.open_cancelled_preview" if previewed else "info.open_cancelled"))
            else:                                   # unreadable or broken file: tell the user, keep running
                QtWidgets.QMessageBox.critical(self, t("app.title"), t("err.open", f=path, e=reader.error))
            return False
        if dialog.isVisible():
            dialog.setCancelButton(None)
            dialog.setLabelText(t("open.preparing"))
            dialog.setRange(0, 0)
            QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        self._set_loading(False)
        self.viewport.adopt_pieces(reader.pieces)
        try:
            if previewed:
                self.doc.finish_opening(reader.result)  # the elements on screen stay: they get their IFC
            else:
                self.doc.show_file(reader.result)       # quick: no geometry kernel here
        except Exception as exc:  # noqa: BLE001 — keep the program running
            QtWidgets.QMessageBox.critical(self, t("app.title"), t("err.open", f=path, e=exc))
            return False
        finally:
            self.viewport.adopt_pieces({})
            QtWidgets.QApplication.restoreOverrideCursor()
            dialog.close()
            dialog.deleteLater()
        if not previewed or state.get("view") in (None, self._camera_state()):
            self.viewport.set_view("iso")           # (unless the user moved the view meanwhile)
            # the view tabs saved with the project, each as it was left
            self.views.restore(self.doc.open_views, self._view_exists)
        n = sum(o.is_bim for o in self.doc.objects.values())
        seconds = _seconds(time.perf_counter() - start)
        if state.get("first_shapes") is not None:
            text = t("info.opened_streamed", f=name, n=n, p=_seconds(state["first_shapes"]), s=seconds)
        elif previewed:
            text = t("info.opened_preview", f=name, n=n, p=_seconds(state["preview"]), s=seconds)
        else:
            text = t("info.opened_cached" if n and self.doc.cache_hits == n else "info.opened",
                     f=name, n=n, s=seconds)
        x, y, _z = self.doc.ifc.origin
        if x or y:
            sep = "." if lang() == "pt" else ","
            text += t("info.recentred", x="{:,.0f}".format(x).replace(",", sep), y="{:,.0f}".format(y).replace(",", sep))
        self.message(text)
        if remember:                                # (0.387) the recent documents; its picture once it is drawn
            self._remember_file(path, picture=False)
            QtCore.QTimer.singleShot(1500, lambda p=path: self._remember_file(p) if self.doc.path == p else None)
        return True

    def _camera_state(self):
        local = self.viewport.camera.local
        return tuple(np.round(local.position, 6)) + tuple(np.round(local.rotation, 6))

    def _set_loading(self, on, name=""):
        """While the IFC of a file shown from its kept shapes is read (Document.loading): one can
        orbit, pan, zoom and change the view; drawing, editing, selecting and saving wait."""
        self._loading = on
        if on:
            self.set_tool("select")
            # (the window's own actions only: the contextual bar's are made again as it changes)
            self._enabled_before = {act: act.isEnabled() for act in self.findChildren(QtGui.QAction)
                                    if act.parent() is self}
            keep = {self.act_zoom_all, self.act_iso, self.act_top, self.act_front, self.act_plan,
                    self.act_last_section, self.act_help, self.act_quit}
            for act in self._enabled_before:
                if act not in keep:
                    act.setEnabled(False)
            self.loading_label.setText(t("open.loading", f=name))
        else:
            for act, was in getattr(self, "_enabled_before", {}).items():
                act.setEnabled(was)
            self._enabled_before = {}
        for panel in (self.tree_panel, self.storeys_panel, self.props, self.rules_panel):
            panel.widget().setEnabled(not on)
        self.schedules_panel.setEnabled(not on)            # (0.477: a tab's page, no longer a panel)
        self.loading_box.setVisible(on)

    def _open_progress(self, dialog, name, stage, percent):
        if dialog.wasCanceled():
            return
        if stage == "shapes":
            dialog.setLabelText(t("open.shapes", f=name))
            dialog.setRange(0, 100)
            dialog.setValue(max(0, min(99, percent)))
        else:
            dialog.setLabelText(t("open.preparing" if stage == "prepare" else "open.reading", f=name))
            dialog.setRange(0, 0)

    def save(self):
        if self.doc.path:
            return self.save_to(self.doc.path)
        return self.save_as()

    def save_as(self):
        start = self.doc.path or os.path.join(_documents_dir(), "projeto.ifc")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, t("act.save_as"), start, t("file.filter"))
        if not path:
            return None
        if not path.lower().endswith(".ifc"):
            path += ".ifc"
        return self.save_to(path)

    def save_to(self, path):
        """Write the IFC (+ sketches beside it) and validate it. Returns the validation errors."""
        if self.tool.name != "select":
            self.tool.cancel()  # drop a half-drawn rectangle / push-pull preview
        self.doc.open_views = self.views.state()      # (the view tabs come back when it is opened again)
        for key, camera in self.views.cameras.items():
            self._left_view(key, camera)              # (the named 3D views where they are now)
        self.doc.save(path)
        self._remember_file(path)                     # (0.387: the start page's recent documents)
        errors = self.doc.ifc.validate()
        name = os.path.basename(path)
        if errors:
            self.message(t("warn.invalid", f=name, n=len(errors), first=errors[0]), warning=True)
        else:
            self.message(t("info.saved", f=name))
        self._update_title()
        return errors

    def closeEvent(self, event):  # noqa: N802
        if self._confirm_discard():
            for reader in list(self._readers):      # a cancelled opening still reading the IFC
                reader.requestInterruption()
                reader.wait()
            if getattr(self, "ai_link", None) is not None:      # (0.269) the port closed, the link's file gone
                self.ai_link.stop()
            QtWidgets.QApplication.instance().removeEventFilter(self)
            event.accept()
        else:
            event.ignore()

    # ------------------------------------------------------------ state

    def _on_document_changed(self, changed=None, removed=None):
        self._refresh_types()                               # (the project's types, 0.87)
        self.act_undo.setEnabled(self.doc.can_undo())
        self.act_redo.setEnabled(self.doc.can_redo())
        self._update_title()
        self._refresh_properties()
        self._refresh_storeys()
        if not self.doc.loading:
            controls.refresh(self.doc, None if changed is None else list(changed) + list(removed or ()))
            self._apply_controls()
        self._refresh_tree(changed, removed)
        if hasattr(self, "library_panel") and not self.doc.loading:
            self.library_panel.mark_stale()                 # (0.466: the project's components, again)
        self._refresh_schedules(changed, removed)
        self._refresh_sheet(changed, removed)
        self._refresh_rule(changed, removed)
        if changed is None or STOREY_CHANGED in changed:
            self._sync_context_bar()                        # (the storeys to draw on, the active one)
        if hasattr(self, "notes_panel") and (changed is None or NOTES_CHANGED in changed):
            self.notes_panel.show_notes(self.doc.notes)
        drawn_only = {GUIDES_CHANGED, DIMS_CHANGED, IMAGES_CHANGED, CAD_CHANGED, CLOUD_CHANGED}
        mode = getattr(self, "presentation_mode", None)
        if mode is not None and (changed is None or removed or not changed or not set(changed) <= drawn_only):
            # (0.479) the Presentation tab's columns again (out of the document's notification; also a change of no
            # element — the site's place); its layers only when elements changed — while it is not in front, they are
            # made again when it is
            QtCore.QTimer.singleShot(0, lambda c=changed, r=removed: mode.refresh(changed=c, removed=r))
        if hasattr(self, "views") and not self.doc.loading:
            # tabs of views that are gone closed, names again (out of the document's notification)
            QtCore.QTimer.singleShot(0, lambda: self.views.refresh(self._view_exists))
        if getattr(self, "_underlay_shown", None) is not None and not getattr(self, "_underlay_later", False) and (
                changed is None or removed or set(changed) - {GUIDES_CHANGED, VIEWS_CHANGED, DIMS_CHANGED,
                                                              IMAGES_CHANGED, CAD_CHANGED, CLOUD_CHANGED}):
            self._underlay_later = True                     # (the model changed: a plan's underlay drawn again)
            QtCore.QTimer.singleShot(200, self._refresh_underlay)
        if hasattr(self, "_checked_commands"):
            self._check_reservations(changed, removed)
            self._known_bim = {i for i, o in self.doc.objects.items() if o.is_bim}

    def _refresh_sheet(self, changed=None, removed=None):
        """The sheet drawings made so far no longer stand when the model changes (the sheet
        window says so); a sheet changed (a view put on it, moved…): laid out again."""
        if not hasattr(self, "_sheet_drawings"):
            return                            # (first call, while the window is being built)
        markers = {GUIDES_CHANGED, STOREY_CHANGED, VIEWS_CHANGED, DIMS_CHANGED, IMAGES_CHANGED,   # (a view's dims in
                   CAD_CHANGED, CLOUD_CHANGED}
        if changed is None or removed or set(changed) - markers:                   # its drawing's key)
            self._sheet_drawings = {}
            if self.sheet_window is not None:
                self.sheet_window.model_changed()
        if self.sheet_window is not None and self.sheet_window.isVisible() and (
                changed is None or VIEWS_CHANGED in changed or DIMS_CHANGED in changed):
            QtCore.QTimer.singleShot(0, self.sheet_window.refresh)     # (out of the document's notification)

    def _refresh_schedules(self, changed=None, removed=None):
        if not hasattr(self, "schedules_panel"):
            return                            # (first call, while the window is being built)
        if self.doc.loading:
            self.schedules_panel.mark_stale()     # (no IFC to read quantities from yet)
            return
        self.schedules_panel.doc = self.doc
        if self.schedules_panel.wants(changed, removed):
            self.schedules_panel.refresh()
        if hasattr(self, "tables_panel") and self.tables_panel.isVisible() and (       # (0.477: the tree's counts)
                changed is None or removed or VIEWS_CHANGED in changed or any(
                    self.doc.get(i) is not None and self.doc.get(i).is_bim for i in changed)):
            self._refresh_tables_panel()

    def run_busy(self, fn, label):
        """Run fn() in a worker thread; the window keeps drawing, with a progress window (no
        clicks meanwhile) if it takes more than 0,4 s. Returns its result (or raises its error)."""
        job = _Job(fn, self)
        dialog = QtWidgets.QProgressDialog(label, None, 0, 0, self)
        dialog.setWindowTitle(t("app.title"))
        dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        dialog.setMinimumDuration(OPEN_DIALOG_AFTER_MS)
        dialog.setValue(0)
        loop = QtCore.QEventLoop()
        job.finished.connect(loop.quit)
        self._relay.held += 1                  # (0.254: the document's changes told after the work, here)
        try:
            job.start()
            if not job.isFinished():
                loop.exec(QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            job.wait()
        finally:
            self._relay.held -= 1
        dialog.close()
        dialog.deleteLater()
        self._relay.flush()
        if job.error is not None:
            raise job.error
        return job.result

    def export_pdf(self):
        """File ▸ Export view as PDF (Ctrl+P): the section or elevation shown, else the plan of the
        active storey, as a vector drawing on A3 at the largest usual scale that fits — with the
        hidden lines left out (worked out in a worker thread)."""
        vp = self.viewport
        name, z = self._storey(self.doc.active_storey)
        if vp.section is not None:
            point, normal = vp.section
            title = self._view_name or t("pdf.title_section")
            view = vp.section_view
            make = lambda: drawings.section(self.doc, point, normal, title, view)  # noqa: E731
            suffix = (self._view_name or t("pdf.file_section")).lower()
        else:
            storey = self.doc.active_storey
            cut = self.doc.view_settings(("plan", storey)).cut_height
            title = t("pdf.title_plan", name=name, z=storeys.level_text(z + cut))
            make = lambda: drawings.plan(self.doc, storey, title)                  # noqa: E731
            suffix = t("pdf.file_plan", name=name)
        drawing = self.run_busy(make, t("pdf.working"))
        if drawing.bounds() is None:
            self.message(t("info.pdf_empty"), warning=True)
            return
        base = os.path.splitext(self.doc.path)[0] if self.doc.path else os.path.join(_documents_dir(), "projeto")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, t("act.export_pdf"), "{} - {}.pdf".format(base, suffix),
                                                        t("pdf.filter"))
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        scale = pdf.write(path, drawing, self.title_block(title=drawing.title), "ArqSynth BIM {}".format(__version__))
        self.message(t("info.pdf", f=os.path.basename(path), s=scale))

    VIEW_FORMATS = (".dxf", ".dwg", ".svg")          # (0.369) the view's drawing for CAD and for drawing programs

    def export_dxf(self, path=None):
        """File ▸ Export view as DXF… (0.129): the section or elevation shown, else the plan of the active storey,
        for AutoCAD and the other CAD programs — in metres, each kind of line on its own layer, its texts sized
        for the view's scale on the sheets (else 1:100). (0.369) Or as a DWG (that DXF turned into AutoCAD's own
        format, 2018, by the ODA File Converter the program reads DWGs with: core/dwg.py) or an SVG (drawn as on
        the sheets, at the view's scale, in millimetres: ui/pdf.write_svg) — by the file's extension, the type chosen
        when it has none. Returns its path, or None."""
        import subprocess
        import tempfile
        from ..core import dwg
        from ..model import dxf
        vp = self.viewport
        name, z = self._storey(self.doc.active_storey)
        if vp.section is not None:
            point, normal = vp.section
            title = self._view_name or t("pdf.title_section")
            view = vp.section_view
            make = lambda: drawings.section(self.doc, point, normal, title, view)  # noqa: E731
            suffix = (self._view_name or t("pdf.file_section")).lower()
        else:
            view = ("plan", self.doc.active_storey)
            cut = self.doc.view_settings(view).cut_height
            title = t("pdf.title_plan", name=name, z=storeys.level_text(z + cut))
            make = lambda: drawings.plan(self.doc, self.doc.active_storey, title)    # noqa: E731
            suffix = t("pdf.file_plan", name=name)
        drawing = self.run_busy(make, t("pdf.working"))
        if drawing.bounds() is None:
            self.message(t("info.pdf_empty"), warning=True)
            return None
        if path is None:
            base = os.path.splitext(self.doc.path)[0] if self.doc.path else os.path.join(_documents_dir(), "projeto")
            path, chosen = QtWidgets.QFileDialog.getSaveFileName(self, t("act.export_dxf"),
                                                                 "{} - {}.dxf".format(base, suffix), t("dxf.filter"))
            if not path:
                return None
            if os.path.splitext(path)[1].lower() not in self.VIEW_FORMATS:
                path += next((e for e in self.VIEW_FORMATS if e[1:] in (chosen or "").lower()), ".dxf")
        kind = os.path.splitext(path)[1].lower()
        scale = (self.doc.view_settings(view).scale if view is not None else None) or 100
        if kind == ".svg":
            w, h = pdf.write_svg(path, drawing, scale, "ArqSynth BIM {}".format(__version__))
            self.message(t("info.svg_view", f=os.path.basename(path), s=scale, w=round(w), h=round(h)))
            return path
        if kind == ".dwg":
            if dwg.converter() is None:
                self.message(t("err.dwg_converter_export"), warning=True)
                return None
            with tempfile.TemporaryDirectory(prefix="arqsynth_dwg_") as folder:
                source = os.path.join(folder, "vista.dxf")
                n = dxf.write(source, drawing, scale)
                try:
                    self.run_busy(lambda: dwg.from_dxf(source, path), t("dwg.working"))
                except (ValueError, OSError, subprocess.SubprocessError):
                    self.message(t("err.dwg_convert_export"), warning=True)
                    return None
            self.message(t("info.dwg", f=os.path.basename(path), n=n, s=scale))
            return path
        n = dxf.write(path, drawing, scale)
        self.message(t("info.dxf", f=os.path.basename(path), n=n, s=scale))
        return path

    def export_splat(self, path=None, quality=None, clouds=None):
        """File ▸ Export Gaussian splat (0.176): the model as splats in a PLY file, for presentation in the web
        viewers — how far apart they are asked for (low 8 cm, medium 5 cm, high 3 cm). (0.216) The linked point
        clouds shown too, straight from their points, when asked (clouds: True / False; None: asked when there are
        any). Returns its path, or None."""
        from ..model import cloud_links as cloud_model
        from ..model import splat
        links = [c for c in self.doc.cloud_links if c.visible]
        model = any(o.is_bim or getattr(o, "mesh", None) is not None for o in self.doc.objects.values())
        if not model and not links:
            self.message(t("info.pdf_empty"), warning=True)
            return None
        if links and clouds is None:
            buttons = QtWidgets.QMessageBox.StandardButton
            clouds = QtWidgets.QMessageBox.question(self, t("act.export_splat"), t("splat.ask_clouds", n=len(links)),
                                                    buttons.Yes | buttons.No, buttons.Yes) == buttons.Yes
        chosen = []
        for link in links if clouds else ():
            cloud = cloud_model.cloud_of(link.path)
            if cloud is not None and len(cloud):
                chosen.append((link.place(cloud.points), cloud.colours))
        if not model and not chosen:
            self.message(t("info.pdf_empty"), warning=True)
            return None
        if quality is None:
            names = [t("splat.q_" + q) for q in splat.QUALITY]
            chosen, ok = QtWidgets.QInputDialog.getItem(self, t("act.export_splat"), t("splat.quality"), names, 1,
                                                        False)
            if not ok:
                return None
            quality = list(splat.QUALITY)[names.index(chosen)]
        if path is None:
            base = os.path.splitext(self.doc.path)[0] if self.doc.path else os.path.join(_documents_dir(), "projeto")
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, t("act.export_splat"), base + " - splat.ply",
                                                            "PLY (*.ply)")
            if not path:
                return None
            if not path.lower().endswith(".ply"):
                path += ".ply"
        try:
            n = self.run_busy(lambda: splat.export(self.doc, path, quality, chosen, model), t("splat.working"))
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return None
        self.message(t("info.splat", f=os.path.basename(path), n=n, q=t("splat.q_" + quality)))
        return path

    def export_model(self, path=None, what=None, scale=None):
        """Export ▸ 3D model (0.348: GLB; 0.349: OBJ and STL too; 0.350: SKP and 3DM): the elements and sketches —
        those shown in the view ("shown"), the whole model ("all") or the selection ("selection"), asked when not given
        — in a file of the format its name says (asked with the file): a GLB (model/gltf_export.py) for the ArqSynth
        Presentation, the web viewers, Blender, Twinmotion…; an SKP for SketchUp and a 3DM for Rhino
        (model/cad3d_export.py); an OBJ with its MTL for nearly every 3D program; an STL to print a model in 3D at a
        scale (1:N, asked when not given — model/mesh_export.py); (0.371) a USDZ for augmented reality on an iPhone or
        iPad (model/usdz_export.py). Returns its path, or None."""
        from ..model import cad3d_export, gltf_export, mesh_export, usdz_export
        kinds = ("glb", "skp", "3dm", "obj", "stl", "usdz")
        choices = ("shown", "all", "selection")
        if what is None:
            names = [t("gltf.what." + c) for c in choices]
            chosen, ok = QtWidgets.QInputDialog.getItem(self, t("act.export_model"), t("gltf.what"), names, 0, False)
            if not ok:
                return None
            what = choices[names.index(chosen)]
        if what == "selection":
            objects = [self.doc.get(g) for g in self.viewport.selection if self.doc.get(g) is not None]
        elif what == "all":
            objects = list(self.doc.objects.values())
        else:
            objects = self.viewport.shown_objects()
        objects = [o for o in objects if getattr(o, "mesh", None) is not None]
        if not objects:
            self.message(t("info.gltf_empty_selection" if what == "selection" else "info.pdf_empty"), warning=True)
            return None
        projects = self.doc.ifc.file.by_type("IfcProject") if getattr(self.doc, "ifc", None) is not None else []
        title = (projects[0].Name if projects else "") or (os.path.splitext(os.path.basename(self.doc.path))[0]
                                                           if self.doc.path else t("gltf.model"))
        if path is None:
            base = os.path.splitext(self.doc.path)[0] if self.doc.path else os.path.join(_documents_dir(), "projeto")
            filters = [t("model3d.filter." + k) for k in kinds]
            path, chosen = QtWidgets.QFileDialog.getSaveFileName(self, t("act.export_model"), base + ".glb",
                                                                 ";;".join(filters))
            if not path:
                return None
            if not path.lower().endswith(tuple("." + k for k in kinds)):   # (no extension written: the filter's)
                path += "." + next((k for k, f in zip(kinds, filters) if f == chosen), "glb")
        kind = os.path.splitext(path)[1].lower().lstrip(".")
        if kind not in kinds:
            kind, path = "glb", path + ".glb"
        if kind == "stl" and scale is None:
            names = ["1:{}".format(s) for s in mesh_export.SCALES]
            chosen, ok = QtWidgets.QInputDialog.getItem(self, t("act.export_model"), t("model3d.scale"), names,
                                                        mesh_export.SCALES.index(100), False)
            if not ok:
                return None
            scale = mesh_export.SCALES[names.index(chosen)]

        def write():
            if kind == "glb":
                return gltf_export.export(self.doc, objects, path, title)
            elements, materials = gltf_export.gather(self.doc, objects)
            if kind == "skp":
                return cad3d_export.write_skp(path, elements, materials)
            if kind == "3dm":
                return cad3d_export.write_3dm(path, elements, materials)
            if kind == "obj":
                return mesh_export.write_obj(path, elements, materials)
            if kind == "usdz":
                return usdz_export.write_usdz(path, elements, materials, title)
            return len(elements), mesh_export.write_stl(path, elements, scale)

        try:
            n, triangles = self.run_busy(write, t("gltf.working"))
        except ValueError:
            self.message(t("info.pdf_empty"), warning=True)
            return None
        except ImportError:                                 # (0.371: usd-core not installed)
            self.message(t("err.usd_missing"), warning=True)
            return None
        except OSError:
            self.message(t("err.image_write", f=os.path.basename(path)), warning=True)
            return None
        mb = "{:.1f}".format(os.path.getsize(path) / 1e6).replace(".", decimal_sep())
        if kind == "stl":
            self.message(t("info.stl", f=os.path.basename(path), tri=triangles, s=scale, mb=mb))
        else:
            self.message(t("info.gltf", f=os.path.basename(path), n=n, tri=triangles, mb=mb))
        return path

    def export_presentation(self, path=None):
        """Export ▸ For the ArqSynth Presentation… (0.362): the whole model in a GLB with its presentation in it
        (model/presentation_export.py) — a layer per element, the scenes (the general view, the named 3D views, the
        plans, the sections), the sun —, for the Presentation's importer. (0.367) By default the package: a ZIP with
        that GLB and the sheets as plan pages (model/presentation_package.py); a path ending in .glb, the GLB alone.
        Returns its path, or None."""
        from ..model import presentation_export
        if not any(getattr(o, "is_bim", False) for o in self.doc.objects.values()):
            self.message(t("info.presentation_empty"), warning=True)
            return None
        if path is None:
            base = os.path.splitext(self.doc.path)[0] if self.doc.path else os.path.join(_documents_dir(), "projeto")
            path, chosen = QtWidgets.QFileDialog.getSaveFileName(self, t("act.export_presentation"),
                                                                 base + " - Presentation.zip",
                                                                 t("present.filter"))
            if not path:
                return None
            if not path.lower().endswith((".zip", ".glb")):
                path += ".glb" if "glb" in chosen.lower() else ".zip"
        thumbs = self.scene_thumbnails(quiet=True)          # (0.363: each scene as its view is now)
        if path.lower().endswith(".zip"):
            return self._export_presentation_package(path, thumbs)
        try:
            done = self.run_busy(lambda: presentation_export.export(self.doc, path, thumbnails=thumbs),
                                 t("present.working"))
        except ValueError:
            self.message(t("info.presentation_empty"), warning=True)
            return None
        mb = "{:.1f}".format(os.path.getsize(path) / 1e6).replace(".", decimal_sep())
        self.message(t("info.presentation", f=os.path.basename(path), n=done["elements"], s=done["scenes"], mb=mb))
        return path

    def _export_presentation_package(self, path, thumbs):
        """(0.367) The package for the Presentation at `path` (a ZIP): the GLB with the presentation in it, and each
        sheet with views as a plan page — its own single-page PDF, as File ▸ Sheets ▸ PDF draws it, the rooms of the
        plans on it as zones of the page. Returns its path, or None."""
        import tempfile
        from ..model import gltf_export, presentation_export, presentation_package
        from ..model import presentation as presentation_model
        try:
            gltf, binary, description = self.run_busy(lambda: presentation_export.package(self.doc, thumbnails=thumbs),
                                                      t("present.working"))
        except ValueError:
            self.message(t("info.presentation_empty"), warning=True)
            return None
        sheets = [s for s in self.doc.sheets if s.views]
        made = self.make_drawings([v for s in sheets for v in s.views]) if sheets else {}
        rooms = presentation_model.spaces(self.doc) if sheets else []
        credit = "ArqSynth BIM {}".format(__version__)
        from ..model import panoramas as panoramas_model
        shots = [p for p in getattr(self.doc, "panoramas", ())                       # (0.368: those still on disk)
                 if panoramas_model.path_of(self.doc, p) and os.path.exists(panoramas_model.path_of(self.doc, p))]
        placements = {}
        pages, pdfs, used = [], {}, set()
        with tempfile.TemporaryDirectory() as folder:
            for sheet in sheets:
                got = [made[self.drawing_key(v.kind, v.ref)] for v in sheet.views]
                frames = sheets_model.layout(sheet, [sheets_model.extent(d) for d in got],
                                             [self.doc.view_settings((v.kind, v.ref)).scale for v in sheet.views],
                                             len(self.doc.title_block.get(sheets_model.EXTRA_KEY) or ()))
                kept = [(d, f, v) for d, f, v in zip(got, frames, sheet.views) if f is not None]
                if not kept:
                    continue
                block = self.title_block(sheet)
                number = sheets_model.number_of(self.doc.sheets, sheet, self.doc.title_block)
                name = presentation_package.file_name(number, sheet.name, used)
                one = os.path.join(folder, "{}.pdf".format(len(pages)))
                pdf.write_sheets(one, [(sheet, [(d, f, self.view_label(v.kind, v.ref)) for d, f, v in kept], block)],
                                 credit)
                with open(one, "rb") as fh:
                    pdfs[name] = fh.read()
                size = sheet.size()
                pages.append({"id": presentation_package.PAGE_ID + sheet.uid,
                              "title": " ".join(p for p in (str(number or ""), sheet.name) if p),
                              "file": name, "size": [float(size[0]), float(size[1])],
                              "zones": presentation_package.page_zones(
                                  self.doc, [(d, f, (v.kind, v.ref)) for d, f, v in kept], size, rooms)})
                placements[pages[-1]["id"]] = presentation_package.panorama_points(
                    [(d, f, (v.kind, v.ref)) for d, f, v in kept], size, shots)
        entries = presentation_package.panorama_entries(shots, placements)
        pictures = {}
        for p, entry in zip(shots, entries):
            with open(panoramas_model.path_of(self.doc, p), "rb") as fh:
                pictures[entry["file"]] = fh.read()
        presentation_package.write(path, gltf_export.glb(gltf, binary), description, pages, pdfs, entries, pictures)
        model3d = description["presentation"]["model3d"]
        mb = "{:.1f}".format(os.path.getsize(path) / 1e6).replace(".", decimal_sep())
        self.message(t("info.presentation_package", f=os.path.basename(path), n=len(model3d["layers"]),
                       s=len(model3d["scenes"]), mb=mb,
                       p=t("present.sheets_1") if len(pages) == 1 else t("present.sheets_n", n=len(pages)),
                       v="" if not entries else t("present.panoramas_1") if len(entries) == 1
                       else t("present.panoramas_n", n=len(entries))))
        return path

    # ------------------------------------------------------------ the scenes of the presentation (0.363)

    def show_presentation_panel(self):
        """Render ▸ Scenes of the presentation — (0.480) the ArqSynth Presentation's interface (the tab; the 0.363 panel
        that split the left column is gone): its scenes, their settings, the export."""
        return self.show_presentation_tab()

    def open_scene(self, key):
        """A scene's view shown (the panel's double-click): a named 3D view, a plan, a section in its tab; the general
        view in the 3D view, from where the Presentation shows it. Returns whether there was one."""
        from ..model import presentation as presentation_model
        scene = next((s for s in presentation_model.scenes(self.doc) if s.key == key), None)
        if scene is None:
            return False
        kind, ref = scene.view[0], scene.view[1] if len(scene.view) > 1 else None
        if scene.kind == "overview":
            self.open_view("3d", None)
            self._look_overview()
        elif kind == "section":
            index = next((k for k, s in enumerate(self.doc.sections) if s.name == ref), None)
            if index is None:
                return False
            self.open_view("section", index)
        else:
            self.open_view(kind, ref)
        return True

    def _look_overview(self):
        """The 3D view from where the Presentation's general view is: south-west of the model and above it, the same
        lens (model/presentation_export.overview_eye) — or, the 3D view being an axonometry, from that side, the
        whole model framed."""
        from ..model import presentation_export
        vp = self.viewport
        centre, radius = vp.scene_bounds()
        if radius <= 0:
            return
        if vp.is_ortho():                                   # (its projection is the view's own: kept)
            vp.look_from(presentation_export.OVERVIEW, animate=False)
            vp.zoom_extents()
            return
        eye = presentation_export.overview_eye(centre, radius)
        vp.set_camera(eye, np.asarray(centre, dtype=float) - eye, fov=self._presentation_fov())

    def _presentation_fov(self):
        """The Presentation's lens (its vertical field of view, model/presentation_export.FOV) as pygfx's, which
        shares its field of view between the width and the height of the view."""
        from ..model import presentation_export
        w, h = self.viewport.logical_size()
        aspect = w / h if h else 16 / 9
        return math.degrees(2.0 * math.atan(math.tan(math.radians(presentation_export.FOV) / 2.0)
                                            * (1.0 + aspect) / 2.0))

    def _room_names(self):
        """(0.364) The rooms an interior camera move may be made in: [(GlobalId, «number name — storey»)]."""
        storeys = {g: n for g, n, _z in self.doc.storeys()}
        out = []
        try:
            found = self.doc.ifc.file.by_type("IfcSpace")
        except AttributeError:
            return []
        for space in found:
            name = " ".join(p for p in (space.Name or "", space.LongName or "") if p) or space.GlobalId
            storey = storeys.get(self.doc.ifc.space_storey(space.GlobalId), "")
            out.append((space.GlobalId, "{} — {}".format(name, storey) if storey else name))
        return sorted(out, key=lambda item: item[1])

    MOVE_FPS = 30

    def play_scene_move(self, key):
        """(0.364) The panel's «Ver movimento»: the scene's camera move played in the 3D view — the scene's own named
        3D view, else the 3D view — as the Presentation will play it (model/presentation.move_frames), at its speed;
        at its end, or with Esc or the button again, the camera back where it was. Returns whether it started."""
        from ..model import presentation as presentation_model
        if self._move_play is not None:
            kind = self._move_play["kind"]
            self.stop_scene_move()
            if kind == "move":
                return False
        scene = next((s for s in presentation_model.scenes(self.doc) if s.key == key), None)
        if scene is None or not scene.move:
            self.message(t("info.move_none"), warning=True)
            return False
        frames = presentation_model.move_frames(self.doc, scene, self.MOVE_FPS)
        if not frames:
            self.message(t("info.presentation_empty"), warning=True)
            return False
        if self.tool is not None and self.tool.name not in QUIET_TOOLS:
            self.set_tool("select")
        if not self.presentation_shown():                   # (0.479: in the Presentation tab, played there)
            self.open_view("3d", scene.view[1] if scene.kind == "view3d" else None)
        vp = self.viewport
        kept = (vp.camera.fov, vp.camera_snapshot())
        vp.camera.fov = self._presentation_fov()
        timer = QtCore.QTimer(self)
        timer.setInterval(int(1000 / self.MOVE_FPS))
        timer.timeout.connect(self._move_step)
        self._move_play = {"kind": "move", "frames": frames, "kept": kept, "timer": timer,
                           "started": time.monotonic(), "view": self.views.current()}
        vp.look_at(*frames[0])
        timer.start()
        self.presentation_mode.set_playing("move")
        self.message(t("info.move_playing", name=t("move." + scene.move),
                       s="{:.0f}".format(presentation_model.move_seconds(scene))))
        return True

    def _move_step(self):
        """A frame of the camera move played: the one its time has reached (a slow drawing skips frames, the move
        keeps its time); past the last, stopped."""
        play = self._move_play
        if play is None:
            return
        if self.views.current() != play["view"]:            # (another view shown meanwhile: the move ends there)
            self.stop_scene_move()
            return
        if play["kind"] == "sun":                           # (0.365: the sun's frames spread over SUN_SECONDS)
            k = int((time.monotonic() - play["started"]) / play.get("seconds", self.SUN_SECONDS)
                    * len(play["frames"]))
            if k >= len(play["frames"]):
                self.stop_scene_move()
            else:
                self.viewport.preview_sun(play["frames"][k][0])
            return
        k = int((time.monotonic() - play["started"]) * self.MOVE_FPS)
        if k >= len(play["frames"]):
            self.viewport.look_at(*play["frames"][-1])
            self.stop_scene_move()
            return
        self.viewport.look_at(*play["frames"][k])

    def play_scene_effect(self, key):
        """(0.486) The Efeitos tab's «Pré-visualizar»: the scene's effect played in the 3D view as the Presentation
        will play it — Construção and Explosão (model/presentation_effects, Viewport.play_effect), Estudo solar the
        sun through the day in the effect's time. Again, or Esc: stopped, the model whole. Returns whether it
        started."""
        from ..model import presentation as presentation_model
        from ..model import presentation_effects
        if self._move_play is not None:
            kind = self._move_play["kind"]
            self.stop_scene_move()
            if kind == "effect":
                return False
        scene = next((s for s in presentation_model.scenes(self.doc) if s.key == key), None)
        if scene is None or scene.effect == "none":
            return False
        if scene.effect == "sun":
            return self.play_scene_sun(key, seconds=presentation_effects.seconds_of(scene.effect_s))
        if self.tool is not None and self.tool.name not in QUIET_TOOLS:
            self.set_tool("select")
        if not self.presentation_shown():
            self.open_view("3d", scene.view[1] if scene.kind == "view3d" else None)
        moves = self.presentation_mode.effect_moves(scene)
        if not moves:
            self.message(t("info.presentation_empty"), warning=True)
            return False
        seconds = presentation_effects.seconds_of(scene.effect_s)
        self.viewport.play_effect(moves, seconds, done=self._effect_done)
        self._move_play = {"kind": "effect", "frames": None, "timer": None, "started": time.monotonic(),
                           "view": self.views.current()}
        self.presentation_mode.set_playing("effect")
        self.message(t("info.effect_playing", name=t("pmode.effect_kind." + scene.effect), n=len(moves),
                       s="{:.0f}".format(seconds)))
        return True

    def play_walk(self, frames, message):
        """(0.488) The Passeio tab's «Percorrer»: the camera along the Virtual Walk — frames [(eye, target)] in the
        model's axes, at MOVE_FPS, with the Presentation's lens —; at its end, again or with Esc, the camera back where
        it was. Returns whether it started."""
        if self._move_play is not None:
            kind = self._move_play["kind"]
            self.stop_scene_move()
            if kind == "walk":
                return False
        if not frames:
            self.message(t("info.walk_none"), warning=True)
            return False
        if self.tool is not None and self.tool.name not in QUIET_TOOLS:
            self.set_tool("select")
        vp = self.viewport
        kept = (vp.camera.fov, vp.camera_snapshot())
        vp.camera.fov = self._presentation_fov()
        timer = QtCore.QTimer(self)
        timer.setInterval(int(1000 / self.MOVE_FPS))
        timer.timeout.connect(self._move_step)
        self._move_play = {"kind": "walk", "frames": frames, "kept": kept, "timer": timer,
                           "started": time.monotonic(), "view": self.views.current()}
        vp.look_at(*frames[0])
        timer.start()
        self.presentation_mode.set_playing("walk")
        self.message(message)
        return True

    def _effect_done(self):
        """(0.486) The effect played to its end (the model is whole again)."""
        if self._move_play is not None and self._move_play["kind"] == "effect":
            self._move_play = None
            self.presentation_mode.set_playing(None)

    def stop_scene_move(self):
        """(0.364) The camera move stopped, the camera where it was before it."""
        play, self._move_play = self._move_play, None
        if play is None:
            return
        if play["timer"] is not None:
            play["timer"].stop()
        if play["kind"] == "effect":                        # (0.486: the model drawn whole again)
            self.viewport.stop_effect()
            self.presentation_mode.set_playing(None)
            return
        if play["kind"] == "sun":                           # (0.365: the view style's sun and shadows again)
            self.viewport.preview_sun(None)
            self.presentation_mode.set_playing(None)
            return
        fov, snapshot = play["kept"]
        if self.views.current() == play["view"]:
            self.viewport.camera.fov = fov
            self.viewport.restore_camera(snapshot)
        elif play["view"] is not None:                      # (left meanwhile: kept as it was before the move)
            self.views.cameras[play["view"]] = snapshot
            self._left_view(play["view"], snapshot)         # (a named 3D view's camera as it was, not mid-move)
        self.presentation_mode.set_playing(None)

    SUN_SECONDS = 8.0       # (0.365) a sun animation previewed: the day, or the year, in this long
    SUN_FRAMES = 240

    def _site_place(self):
        from ..model import presentation as presentation_model
        return presentation_model.site(self.doc)

    def play_scene_sun(self, key, seconds=None):
        """(0.365) The panel's «Ver sol»: the scene's sun in its 3D view (its own named one, else the 3D view), with
        its shadows, where the Presentation will place it — the site's, on its day at its hour —; animated, through
        that day or that year in SUN_SECONDS. Again, or Esc: the view style's sun again. Returns whether it shows.
        (0.486) seconds: the «Estudo solar» effect — through the day, in so long."""
        import dataclasses
        from ..model import presentation as presentation_model
        from ..model import presentation_sun
        if self._move_play is not None:
            kind = self._move_play["kind"]
            self.stop_scene_move()
            if kind == "sun":
                return False
        scene = next((s for s in presentation_model.scenes(self.doc) if s.key == key), None)
        if scene is None:
            return False
        if seconds:
            scene = dataclasses.replace(scene, sun_animate="day")
        frames = presentation_model.sun_frames(self.doc, scene, self.SUN_FRAMES)
        if not frames:
            self.message(t("info.no_site"), warning=True, action=getattr(self, "act_site_location", None))
            return False
        month, day = presentation_sun.month_day(scene.sun_day)
        date, hour = "{:02d}/{:02d}".format(day, month), "{:02d}:{:02d}".format(*divmod(scene.sun_minutes, 60))
        frames = [f for f in frames if f[0][2] > 0.0]       # (under the horizon: no sun to show, it is night)
        if not frames:
            self.message(t("info.sun_night", date=date, time=hour))
            return False
        if self.tool is not None and self.tool.name not in QUIET_TOOLS:
            self.set_tool("select")
        if not self.presentation_shown():                   # (0.479: in the Presentation tab, shown there)
            self.open_view("3d", scene.view[1] if scene.kind == "view3d" else None)
        self.viewport.preview_sun(frames[0][0])
        timer = None
        if len(frames) > 1:
            timer = QtCore.QTimer(self)
            timer.setInterval(int(1000 / self.MOVE_FPS))
            timer.timeout.connect(self._move_step)
            timer.start()
            self.message(t("info.sun_" + scene.sun_animate, date=date, time=hour,
                           s="{:.0f}".format(seconds or self.SUN_SECONDS)))
        else:
            place = self._site_place()
            azimuth, altitude = presentation_sun.angles(place[0], place[1], scene.sun_day, scene.sun_minutes)
            self.message(t("info.sun_shown", date=date, time=hour, az=round(azimuth), alt=round(altitude)))
        self._move_play = {"kind": "sun", "frames": frames, "timer": timer, "started": time.monotonic(),
                           "view": self.views.current(), "seconds": float(seconds or self.SUN_SECONDS)}
        self.presentation_mode.set_playing("sun")
        return True

    def scene_thumbnails(self, quiet=False):
        """The panel's Thumbnails (and before an export): each scene's view shown in turn and drawn small, as the
        Image of the view is (Viewport.render_image), then back to the view it was in — the tabs opened for them
        closed again, the 3D view's camera where it was. Returns {scene key: JPEG bytes}."""
        from ..model import presentation as presentation_model
        found = presentation_model.scenes(self.doc)
        if not found or self.doc.loading:
            return {}
        if self.tool is not None and self.tool.name not in QUIET_TOOLS:
            self.set_tool("select")                 # (a preview of the tool's is not of the model)
        vp = self.viewport
        back, opened = self.views.current(), list(self.views.keys)
        thumbs = {}
        dialog = QtWidgets.QProgressDialog(t("present.thumbs_working"), None, 0, len(found), self)
        dialog.setWindowTitle(t("app.title"))
        dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        dialog.setMinimumDuration(OPEN_DIALOG_AFTER_MS)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            for k, scene in enumerate(found):
                dialog.setValue(k)
                kept = None
                if scene.kind == "overview":
                    self.open_view("3d", None)
                    kept = (vp.camera.fov, vp.camera_snapshot())
                    self._look_overview()
                elif not self.open_scene(scene.key):
                    continue
                QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
                try:
                    thumbs[scene.key] = _thumbnail_jpeg(vp.render_image(THUMB_RENDER_PX))
                except Exception:                    # (one scene's thumbnail missing is no reason to stop)
                    logging.getLogger(__name__).exception("thumbnail of a scene")
                finally:
                    if kept is not None:
                        vp.camera.fov = kept[0]
                        vp.restore_camera(kept[1])
        finally:
            dialog.setValue(len(found))
            QtWidgets.QApplication.restoreOverrideCursor()
            for key in [key for key in self.views.keys if key not in opened]:
                self.views.close(self.views.keys.index(key))
            if back is not None:
                self.views.open(back)
        self._scene_thumbs = dict(thumbs)
        self.presentation_mode.refresh(layers=False)        # (0.479: the Presentation tab's cards)
        if not quiet:
            self.message(t("info.present_thumbs", n=len(thumbs)))
        return thumbs

    def element_hatches(self, entry=False):
        """View ▸ Hatches by element… (0.331), as Revit's «Override graphics in view ▸ by element»: the elements
        selected (asked for when none are) given their own hatches in the view shown — their cut and their surface,
        each a foreground and a background pattern with its colour —, over their category's and their materials';
        «Repor» puts theirs back. One undo step. entry: (cut fg, cut bg, surface fg, surface bg), or None to put them
        back, without asking. Returns whether they changed."""
        current = self.views.current()
        if current is not None and current[0] == "sheet":
            self.message(t("info.element_hatches_sheet"), warning=True)
            return False
        guids = sorted(g for g in self.viewport.selection if self.doc.get(g) is not None and self.doc.get(g).is_bim)
        if not guids:
            self._ask(self.act_element_hatches, "pick.element_hatches",
                      lambda i: self.doc.get(i) is not None and self.doc.get(i).is_bim,
                      lambda: self.element_hatches(entry))
            return False
        view = self.viewport.current_view() or self._live_3d()
        name = self._view_tab_label(view)
        if entry is False:
            from .project_tree import category_label
            from .view_styles_dialog import ElementHatches
            kept = self.doc.view_settings(view).elements or {}
            theirs = {kept.get(g) for g in guids}
            counts = {}
            for g in guids:
                cls = self.doc.get(g).ifc_class
                counts[cls] = counts.get(cls, 0) + 1
            what = ", ".join("{} × {}".format(category_label(cls), n) for cls, n in sorted(counts.items()))
            dialog = ElementHatches(self, theirs.pop() if len(theirs) == 1 else None, what, name,
                                    own=any(kept.get(g) for g in guids))
            if not dialog.exec():
                return False
            entry = dialog.entry()
        changed = self.doc.set_element_hatches(view, guids, entry)
        if changed:
            self.message(t("info.element_hatches" if entry is not None and any(entry) else "info.element_hatches_back",
                           n=len(guids), view=name))
        return changed

    def reset_patterns(self):
        """(0.332) The selected elements' surface patterns as they were before being aligned by hand (Modify ▸ Align
        on a pattern's line); the elements asked for when none is selected. One undo step."""
        guids = sorted(g for g in self.viewport.selection if self.doc.get(g) is not None and self.doc.get(g).is_bim)
        if not guids:
            self._ask(self.act_reset_patterns, "pick.reset_patterns",
                      lambda i: self.doc.get(i) is not None and self.doc.get(i).is_bim, self.reset_patterns)
            return False
        if not bim.reset_patterns(self.doc, guids):
            self.message(t("info.patterns_not_aligned"), action=self.tool_actions["align"])
            return False
        self.message(t("info.patterns_reset", n=len(guids)))
        return True

    def render_realistic(self, width=None, quality=None, samples=None, lighting="sun_lights", sun=None, exposure=0.0,
                         clean=True):
        """Render ▸ Realistic render (0.343): the 3D view (or the plan, section, elevation shown) as it is seen — what
        is shown, from its camera, its materials' colours and finishes, its lights — rendered by path tracing
        (render/path_tracer.py, Mitsuba 3) `width` pixels wide (its proportion the view's) at a quality ("draft",
        "normal", "high"; samples: so many instead), lit so (render_scene.LIGHTINGS) under `sun` ((azimuth, altitude);
        None: its view style's), `exposure` EV over the automatic, its grain filtered out or not — all asked when no
        width is given —, in a process of its own: its window (ui/render_dialog) shows the picture getting finer.
        Returns the window, or None."""
        import importlib.util
        import tempfile
        from ..core import sun as core_sun
        from ..model import render_scene
        from ..render import path_tracer
        from . import render_dialog
        current = self.views.current()
        if current is not None and current[0] == "sheet":
            self.message(t("info.image_sheet"), action=self.act_sheets_pdf)
            return None
        if importlib.util.find_spec("mitsuba") is None:
            self.message(t("info.render_missing"), warning=True)
            return None
        vp = self.viewport
        if self.tool is not None and self.tool.name not in QUIET_TOOLS:
            self.set_tool("select")
        if width is None:
            try:
                site = self.doc.ifc.site_location()[:2]
            except (AttributeError, RuntimeError):
                site = (None, None)
            dialog = render_dialog.RenderSetup(self, vp.image_size, (vp.vstyle.sun_azimuth, vp.vstyle.sun_altitude),
                                               site)
            self._render_setup = dialog                       # (tests fill it in)
            accepted = dialog.exec()
            self._render_setup = None
            if not accepted:
                return None
            chosen = dialog.values()
            width, quality, lighting, sun = chosen["width"], chosen["quality"], chosen["lighting"], chosen["sun"]
            exposure, clean = chosen["exposure"], chosen["clean"]
        w, h = vp.image_size(width)
        objects = [o for o in vp.shown_objects() if o.mesh is not None]
        if not objects:
            self.message(t("info.render_empty"), warning=True)
            return None
        towards = core_sun.direction(*sun) if sun is not None else vp.vstyle.sun()
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            scene = render_scene.scene_of(self.doc, objects, vp.render_camera(), towards, lighting, exposure, clean)
            folder = tempfile.mkdtemp(prefix=render_dialog.TEMP_PREFIX)     # (0.347: gone with its window)
            scene.save(os.path.join(folder, "cena.npz"))
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        spp = int(samples or path_tracer.QUALITIES.get(quality or "normal", path_tracer.QUALITIES["normal"]))
        picture = os.path.join(folder, "render.png")
        base = os.path.splitext(self.doc.path)[0] if self.doc.path else os.path.join(_documents_dir(), "projeto")
        name = self._view_tab_label(current) if current is not None else t("tab.3d")
        name = "".join("-" if c in '\\/:*?"<>|' else c for c in name)
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        window = render_dialog.RenderWindow(self, path_tracer.command(os.path.join(folder, "cena.npz"), picture, w, h,
                                                                      spp), picture,
                                            "{} - {} - render".format(base, name), cwd=root)
        self._render_window = window
        window.start()
        window.show()
        self.message(t("info.render_started", w=w, h=h, n=scene.triangles))
        return window

    PANORAMA_SIZES = (2048, 4096)           # (0.368) a panorama's width (its height half): 2048 × 1024, 4096 × 2048

    def render_panorama(self, name=None, width=None, quality=None, samples=None):
        """Render ▸ Panorama 360°… (0.368): a 360° panorama rendered by path tracing (render_realistic's, six faces of
        90° made one equirectangular picture: render/path_tracer.render_panorama) from where the 3D view's camera is —
        inside a room, at eye height —, looking (level) where it looks; asked its name, size and quality when no width
        is given. Its picture is kept beside the project (model/panoramas.py), and it goes to the ArqSynth
        Presentation as a 360° point on the plans of its storey. Returns the render's window, or None."""
        import importlib.util
        import tempfile
        from ..model import panoramas as panoramas_model
        from ..model import render_scene
        from ..render import path_tracer
        from . import render_dialog
        current = self.views.current()
        vp = self.viewport
        if current is None or current[0] != "3d" or vp.is_ortho() or vp.cutting():
            self.message(t("info.panorama_3d"), warning=True)
            return None
        if not self.doc.path:
            self.message(t("info.panorama_save"), warning=True, action=self.act_save)
            return None
        if importlib.util.find_spec("mitsuba") is None:
            self.message(t("info.render_missing"), warning=True)
            return None
        if self.tool is not None and self.tool.name not in QUIET_TOOLS:
            self.set_tool("select")
        name = name or panoramas_model.next_name(self.doc, t("panorama.name"))
        if width is None:
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle(t("act.panorama"))
            form = QtWidgets.QFormLayout(dialog)
            name_edit = QtWidgets.QLineEdit(name)
            size = QtWidgets.QComboBox()
            for w in self.PANORAMA_SIZES:
                size.addItem("{} × {}".format(w, w // 2), w)
            quality_box = QtWidgets.QComboBox()
            for key in path_tracer.QUALITIES:
                quality_box.addItem(t("render.quality." + key), key)
            quality_box.setCurrentIndex(max(quality_box.findData("normal"), 0))
            form.addRow(t("panorama.name_label"), name_edit)
            form.addRow(t("panorama.size"), size)
            form.addRow(t("render.quality"), quality_box)
            hint = QtWidgets.QLabel(t("panorama.hint"))
            hint.setWordWrap(True)
            form.addRow(hint)
            buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                                 | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            form.addRow(buttons)
            self._panorama_dialog = dialog                    # (tests fill it in)
            accepted = dialog.exec()
            self._panorama_dialog = None
            if not accepted:
                return None
            name = name_edit.text().strip() or name
            width, quality = size.currentData(), quality_box.currentData()
        objects = [o for o in vp.shown_objects() if o.mesh is not None]
        if not objects:
            self.message(t("info.render_empty"), warning=True)
            return None
        camera = vp.render_camera()
        eye = np.asarray(camera["eye"], dtype=float)
        forward = np.asarray(camera["target"], dtype=float) - eye
        storey = max(((g, z) for g, _n, z in self.doc.storeys() if z <= eye[2] + 0.1), key=lambda gz: gz[1],
                     default=(self.doc.active_storey, 0.0))[0]
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            scene = render_scene.scene_of(self.doc, objects, camera, vp.vstyle.sun(), "sun_lights", 0.0, True)
            folder = tempfile.mkdtemp(prefix=render_dialog.TEMP_PREFIX)
            scene.save(os.path.join(folder, "cena.npz"))
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        spp = int(samples or path_tracer.QUALITIES.get(quality or "normal", path_tracer.QUALITIES["normal"]))
        picture = os.path.join(folder, "panorama.png")
        base = os.path.splitext(self.doc.path)[0]
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        window = render_dialog.RenderWindow(self, path_tracer.command(os.path.join(folder, "cena.npz"), picture,
                                                                      width, width // 2, spp, panorama=True),
                                            picture, "{} - {}".format(base, name), cwd=root)
        window.on_finished = lambda png: self._keep_panorama(png, name, eye, forward, storey)
        self._render_window = window
        window.start()
        window.show()
        self.message(t("info.panorama_started", name=name, w=width, h=width // 2))
        return window

    def _keep_panorama(self, png, name, eye, forward, storey):
        """(0.368) A panorama finished: its picture as a JPEG in the project's panoramas folder, and its record kept
        (one undo step). Returns the record, or None."""
        from ..model import panoramas as panoramas_model
        image = QtGui.QImage(png)
        folder = panoramas_model.folder(self.doc)
        if image.isNull() or folder is None:
            return None
        os.makedirs(folder, exist_ok=True)
        record = panoramas_model.made(self.doc, "", name, eye, forward, storey)
        picture_name = "{}.jpg".format(record["uid"])
        record["file"] += picture_name
        if not image.save(os.path.join(folder, picture_name), "JPEG", 90):
            self.message(t("err.image_write", f=picture_name), warning=True)
            return None
        self.doc.set_panoramas(panoramas_model.with_added(self.doc.panoramas, record))
        self.message(t("info.panorama_kept", name=name))
        return record

    def remove_panorama(self, uid):
        """(0.368) A panorama out of the project (one undo step; its picture stays in its folder)."""
        from ..model import panoramas as panoramas_model
        if any(p["uid"] == uid for p in self.doc.panoramas):
            self.doc.set_panoramas(panoramas_model.without(self.doc.panoramas, uid))

    def export_image(self, path=None, width=None, background=None):
        """Export ▸ Image of the view (0.329), as Revit's: the 3D view, plan, section or elevation shown, drawn again
        `width` pixels wide (its proportion the view's) on its background ("view", "white", "transparent") — both asked
        when not given — without what only the tools show; written as PNG or JPEG. Returns its path, or None."""
        from . import image_dialog
        current = self.views.current()
        if current is not None and current[0] == "sheet":
            self.message(t("info.image_sheet"), action=self.act_sheets_pdf)
            return None
        vp = self.viewport
        if self.tool is not None and self.tool.name not in QUIET_TOOLS:
            self.set_tool("select")                 # (a preview of the tool's is not of the model)
        if width is None:
            dialog = image_dialog.ImageDialog(self, vp.image_size, vp.logical_size()[0], cutting=vp.cutting())
            if not dialog.exec():
                return None
            width, background = dialog.values()
        background = background or "view"
        if path is None:
            base = os.path.splitext(self.doc.path)[0] if self.doc.path else os.path.join(_documents_dir(), "projeto")
            name = self._view_tab_label(current) if current is not None else t("tab.3d")
            name = "".join("-" if c in '\\/:*?"<>|' else c for c in name)     # (a file's name: the view's)
            path, chosen = QtWidgets.QFileDialog.getSaveFileName(self, t("act.export_image"),
                                                                 "{} - {}.png".format(base, name), t("image.filter"))
            if not path:
                return None
            if not path.lower().endswith((".png", ".jpg", ".jpeg")):
                path += ".jpg" if "jpg" in chosen.lower() else ".png"
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)   # (drawn here: the GPU's thread)
        try:
            image = vp.render_image(width, background)
        except Exception as exc:                     # (the GPU out of memory for so large an image: a smaller one)
            logging.getLogger(__name__).exception("image of the view")
            self.message(t("err.image", e=exc), warning=True)
            return None
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        if not image_dialog.save_image(path, image):
            self.message(t("err.image_write", f=os.path.basename(path)), warning=True)
            return None
        h, w = image.shape[:2]
        self.message(t("info.image", f=os.path.basename(path), w=w, h=h))
        return path

    # ------------------------------------------------------------ sheets

    def title_block(self, sheet=None, title=""):
        """The texts of a sheet's title block (sheets.title_texts): the project's fields — its
        name, if not given, is the file's — and the sheet's name and number (or `title`)."""
        doc = self.doc
        project = os.path.splitext(os.path.basename(doc.path))[0] if doc.path else t("app.untitled")
        if sheet is None:
            return sheets_model.title_texts(doc.title_block, title, "", project)
        return sheets_model.title_texts(doc.title_block, sheet.name,
                                        sheets_model.number_of(doc.sheets, sheet, doc.title_block), project,
                                        sheet.revisions, len(doc.sheets))

    def edit_company_title_block(self, index=None):
        """(0.472, the owner: «um botão editar o carimbo… personalizada de acordo com a sua empresa»; 0.473: «se o
        carimbo pudesse abrir na tela e o utilizador usar as ferramentas de desenhos e inserir os campos») The
        company's own title block drawn on the sheet (`index`, the one shown, else the first): its tools on the
        parameters' bar (ui/title_block_editor); «Concluir» keeps it with the project — one undo step. Returns the
        editor, None when there is no sheet to draw it on."""
        doc = self.doc
        if not doc.sheets:
            self.message(t("tbe.no_sheet"), warning=True)
            return None
        if index is None:
            shown = self.sheet_window.sheet if self.sheet_shown() else None
            index = doc.sheets.index(shown) if shown is not None else 0
        index = min(max(int(index), 0), len(doc.sheets) - 1)
        if not (self.sheet_shown() and self.sheet_window.sheet is doc.sheets[index]):
            self.open_sheet(index)
        return self.sheet_window.start_editor()

    def edit_sheet_type(self, index):
        """(0.470) A sheet's «Editar tipo…», as Revit's Type Properties of a title block: its paper, how it stands, its
        title block's template — for every sheet of the type, or this one — and what the title block shows on every
        sheet. One undo step on OK."""
        if not 0 <= index < len(self.doc.sheets):
            return
        from .sheet_type_dialog import SheetTypeDialog
        doc, sheet = self.doc, self.doc.sheets[index]
        dialog = SheetTypeDialog(self, sheet, doc.sheets, doc.title_block, self.title_block()["project"],
                                 sheets_model.number_of(doc.sheets, sheet, doc.title_block))
        self._sheet_type_dialog = dialog                  # (tests fill it in)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            self._sheet_type_dialog = None
            return
        self._sheet_type_dialog = None
        targets = [k for k, s in enumerate(doc.sheets) if s.kind == sheet.kind] if dialog.everyone() else [index]
        doc.set_sheet_type(targets, *dialog.kind(), fields=dialog.fields())
        from .sheet_type_dialog import kind_label
        self.message(t("info.sheet_type", type=kind_label(dialog.kind()), n=len(targets)))

    def _sheet_property(self, action, uid, value):
        """(0.470) A sheet's property changed in the Properties panel (uid: the sheet's)."""
        doc = self.doc
        index = next((k for k, s in enumerate(doc.sheets) if s.uid == uid), None)
        if index is None:
            return
        sheet = doc.sheets[index]
        if action == "sheet_type":
            doc.set_sheet_type([index], *value)
        elif action == "sheet_edit_type":
            self.edit_sheet_type(index)
        elif action == "sheet_name":
            doc.rename_sheet(index, value)
        elif action == "sheet_number":
            doc.set_title_block(doc.title_block, index, number=value)
        elif action == "sheet_sets":
            doc.set_sheet_sets(index, [n.strip() for n in str(value).split(",") if n.strip()])
        elif action == "sheet_revisions":
            from .sheet_type_dialog import RevisionsDialog
            dialog = RevisionsDialog(self, sheet)
            self._revisions_dialog = dialog               # (tests fill it in)
            if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                doc.set_title_block(doc.title_block, index, revisions=dialog.revisions())
            self._revisions_dialog = None
        self._show_properties()

    def _properties_sheet(self):
        """(0.470) The sheet whose properties the panel shows: the sheet tab's shown, else the one chosen in the
        navigator (until something else is chosen); None."""
        if self.sheet_shown():
            return self.sheet_window.sheet
        uid = getattr(self, "_props_sheet", None)
        return next((s for s in self.doc.sheets if s.uid == uid), None) if uid else None

    def edit_title_block(self, index=None):
        """The title block dialog: the project's fields (0.127: its own ones, the sheets' numbering) and, for
        sheet `index`, its name, number and revisions."""
        sheet = self.doc.sheets[index] if index is not None and 0 <= index < len(self.doc.sheets) else None
        dialog = title_block_dialog.TitleBlockDialog(
            self, self.doc.title_block, sheet,
            sheets_model.number_of(self.doc.sheets, sheet, self.doc.title_block) if sheet else "",
            self.title_block()["project"])
        self._title_block_dialog = dialog                 # (tests fill it in)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        name, number = dialog.sheet_values()
        self.doc.set_title_block(dialog.fields(), index if sheet is not None else None, name, number,
                                 dialog.revisions() if sheet is not None else None)

    def view_label(self, kind, ref):
        """A view's name, as on a sheet and in the Project panel."""
        if kind == "plan":
            return t("sheet.plan", name=self._storey(ref)[0])
        if kind == "elevation":
            return t("tree.elevation_title", side=t("tree.elevation." + ref))
        if kind == "detail":                                           # (a detail view, 0.133)
            detail = self.doc.detail(ref)
            return detail.name if detail is not None else ref
        if kind == "3d":                                               # (a 3D view, 0.134)
            view = self.doc.view3d(ref) if ref else None
            return view.name if view is not None else t("tab.3d")
        if kind == "rebar":                                            # (a member's reinforcement, 0.168)
            obj = self.doc.get(ref)
            return t("tree.rebar_view", name=obj.name if obj is not None else ref)
        if kind == "rebar_cut":                                        # (…its section, 0.234)
            from ..model import rebar_drawings
            obj = self.doc.get(ref)
            letter = rebar_drawings.cut_letter(self.doc, ref) if obj is not None else "A"
            return t("tree.rebar_cut_view", k=letter, name=obj.name if obj is not None else ref)
        if kind == "structure":                                        # (a storey's structure plan, 0.168)
            return t("tree.structure_view", name=self._storey(ref)[0])
        if kind == "structure_below":                                  # (…its formwork seen from below, 0.235)
            return t("tree.structure_below_view", name=self._storey(ref)[0])
        if kind == "rebar_details":                                    # (the typical details, 0.237)
            return t("tree.rebar_details_view")
        if kind == "openings":                                         # (the mapa de vãos, 0.293)
            return t("tree.openings")
        if kind == "steel_parts":                                      # (0.502: the steel pieces' drawing)
            return t("tree.steel_parts")
        if kind == "steel_erection":                                   # (0.510: the steel's erection plan)
            return t("tree.steel_erection")
        if kind == "steel_assemblies":                                 # (0.515: the steel assemblies' drawing)
            return t("tree.steel_assemblies")
        if kind == "schedule":                                         # (a schedule's table, 0.132)
            if str(ref).startswith("def:"):
                own = next((d for d in self.doc.schedule_defs if "def:" + d.uid == ref), None)
                return own.name if own is not None else ref
            return t("sched.cat." + ref) if ref in schedules_model.CATEGORIES else ref
        return ref

    def _has_steel(self):
        """(0.502) Whether the model has steel pieces (its fabrication drawing offered in the browser)."""
        for o in self.doc.objects.values():
            if not o.is_bim or o.ifc_class not in ("IfcColumn", "IfcBeam", "IfcMember", "IfcPlate"):
                continue
            kind = self.doc.ifc.kind_of(o.id)
            if kind in ("steel_member", "steel_part"):
                return True
            if kind in ("column", "beam") and self.doc.ifc.steel_section(o.id) is not None:
                return True
        return False

    def _structural_storeys(self):
        """[(GlobalId, name)] of the storeys with columns, beams or footings (0.168: their structure plans)."""
        from ..model.rebar_drawings import STRUCTURE
        with_members = {o.storey for o in self.doc.objects.values() if o.is_bim and o.ifc_class in STRUCTURE}
        return [(g, n) for g, n, _z in sorted(self.doc.ifc.storeys(), key=lambda s: s[2]) if g in with_members]

    def _reinforced(self):
        """[(GlobalId, name)] of the members with bars in the model (0.168: their reinforcement drawings)."""
        from ..model.design_text import natural
        hosts = {self.doc.ifc._params(e).get("Armadura") for e in self.doc.ifc.file.by_type("IfcReinforcingBar")}
        out = [(g, self.doc.get(g).name) for g in hosts if g and self.doc.get(g) is not None]
        return sorted(out, key=lambda gn: natural(gn[1]))

    def drawing_key(self, kind, ref):
        """What a view's drawing depends on (besides the model): a section by its plane, so
        renaming it does not make its drawing again; its template's cut height and hidden classes;
        its dimensions. (A schedule's table: its definition, 0.132.)"""
        if kind == "schedule":
            own = next((d for d in self.doc.schedule_defs if "def:" + d.uid == ref), None)
            return ("schedule", ref, repr(schedules_model.def_to_dict(own)) if own is not None else None)
        if kind == "3d":                                  # (its camera and what its view hides, 0.134)
            view = self.doc.view3d(ref) if ref else None
            settings = self.doc.view_settings(("3d", ref) if ref else ("3d",))
            return ("3d", ref, repr(view.camera) if view is not None else None, tuple(sorted(settings.hidden)))
        if kind == "detail":                              # (its rectangle, scale and its view's drawing, 0.133)
            detail = self.doc.detail(ref)
            if detail is None:
                return ("detail", ref, None)
            return ("detail", ref, tuple(detail.rect), detail.scale) + self.drawing_key(*detail.parent)
        settings = self.doc.view_settings((kind, ref))
        dims = tuple(id(d) for d in self.doc.dimensions_of((kind, ref)))
        dims += tuple((id(a), tuple(tuple(p) for p in a.points), a.text, a.hatch, a.size,  # (what is drawn in it,
                       repr(sorted(a.extra.items())))                                  # 0.120; its angle, line: 0.191)
                      for a in self.doc.annotations_of((kind, ref)))
        dims += (repr(sorted(self.doc.dim_style.items())),)                          # (their style, 0.124)
        dims += (repr(self.doc.graphic_style),)                                     # (hatches and pens, 0.126)
        extra = (settings.cut_height, tuple(sorted(settings.hidden)), tuple(sorted(settings.hidden_phases)),
                 settings.rule, dims, settings.depth, settings.underlay, settings.crop, settings.detail,
                 settings.slopes,                                              # (its slope colours, 0.201)
                 tuple(sorted((k, tuple(v)) for k, v in (settings.labels or {}).items())))   # (moved by hand, 0.238)
        if kind == "section":
            s = next((s for s in self.doc.sections if s.name == ref), None)
            return ("section", None) if s is None else ("section", tuple(np.round(s.point, 6)),
                                                        tuple(np.round(s.normal, 6))) + extra
        return (kind, ref) + extra

    def make_drawings(self, views, fresh=False):
        """{drawing key: Drawing or None} of sheet views (sheets.Placed): kept ones unless
        fresh, the others made in a worker thread (hidden lines), with a progress window."""
        if fresh:
            for v in views:
                self._sheet_drawings.pop(self.drawing_key(v.kind, v.ref), None)
        wanted = {self.drawing_key(v.kind, v.ref): v for v in views}
        missing = [(k, v) for k, v in wanted.items() if k not in self._sheet_drawings]
        if missing:
            doc = self.doc
            made = self.run_busy(lambda: {k: drawings.of_view(doc, v.kind, v.ref, "") for k, v in missing},
                                 t("pdf.working"))
            self._sheet_drawings.update(made)
        return {k: self._sheet_drawings.get(k) for k in wanted}

    def sheet_action(self, action, *args):
        """The Project panel's sheets: "new"; "put" (sheet index or None for a new sheet, kind,
        ref); "open" / "export" / "remove" (index); "rename" (index, name); "take_off" (index,
        view index); "export_all"."""
        doc = self.doc
        if action == "new":
            self.open_sheet(doc.add_sheet())
        elif action == "put":
            index, kind, ref = args
            also = ()                                       # (0.234) a member's section beside its reinforcement
            if kind == "rebar" and doc.get(ref) is not None:
                from ..model import rebar_drawings
                also = (("rebar_cut", ref),) if rebar_drawings.has_cut(doc, ref) else ()
            index, _k = doc.put_on_sheet(index, kind, ref, also)    # (None: on a new sheet, one undo step)
            self.message(t("info.on_sheet", view=self.view_label(kind, ref), sheet=doc.sheets[index].name))
            self.open_sheet(index)
        elif action == "open":
            self.open_sheet(args[0])
        elif action == "export":
            self.export_sheets([doc.sheets[args[0]]])
        elif action == "export_all":
            self.export_sheets(list(doc.sheets))
        elif action == "rename":
            doc.rename_sheet(*args)
        elif action == "remove":
            doc.remove_sheet(args[0])
        elif action == "take_off":
            doc.change_sheet(args[0], view=args[1], remove=True)
        elif action == "title_block":
            self.edit_title_block(args[0])
        elif action == "props":                             # (0.470) a sheet chosen in the navigator: its properties
            self._props_sheet = doc.sheets[args[0]].uid if 0 <= args[0] < len(doc.sheets) else None
            self.props.show()
            self._show_properties()
        elif action == "edit_type":                         # (0.470)
            self.edit_sheet_type(args[0])
        elif action == "by_storey":
            self.sheets_by_storey()
        elif action in ("export_png", "export_svg"):        # (0.128) one sheet, or all (index None)
            chosen = list(doc.sheets) if args[0] is None else [doc.sheets[args[0]]]
            self.export_sheets(chosen, action[len("export_"):])
        elif action == "print":
            self.print_sheets(list(doc.sheets) if args[0] is None else [doc.sheets[args[0]]])
        elif action == "sets":
            self.edit_sheet_sets(args[0])
        elif action == "publish":
            self.publish_set(args[0])
        elif action == "remove_detail":                     # (0.133)
            index = next((k for k, d in enumerate(doc.details) if d.uid == args[0]), None)
            if index is not None:
                doc.remove_detail(index)

    def sheets_by_storey(self):
        """Sheets ▸ Sheets by storey… (0.127): a sheet with the plan of each storey chosen (all of them at
        first), on the paper chosen; and, if ticked, one with the four elevations and one with the sections. One
        undo step."""
        levels = sorted(self.doc.storeys(), key=lambda s: s[2])
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(t("wizard.title"))
        layout = QtWidgets.QVBoxLayout(dialog)
        intro = QtWidgets.QLabel(t("wizard.intro"))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        checks = []
        for guid, name, z in levels:
            box = QtWidgets.QCheckBox("{}  ({})".format(name, storeys.level_text(z)))
            box.setChecked(True)
            checks.append((guid, name, box))
            layout.addWidget(box)
        form = QtWidgets.QFormLayout()
        paper = QtWidgets.QComboBox()
        for key in sheets_model.PAPERS:
            paper.addItem(key, key)
        form.addRow(t("wizard.paper"), paper)
        template = QtWidgets.QComboBox()                  # (0.129) the title block's template
        for key in sheets_model.TEMPLATES:
            template.addItem(t("sheet.template." + key), key)
        form.addRow(t("sheet.template"), template)
        layout.addLayout(form)
        elevations = QtWidgets.QCheckBox(t("wizard.elevations"))
        sections = QtWidgets.QCheckBox(t("wizard.sections"))
        sections.setEnabled(bool(self.doc.sections))
        for box in (elevations, sections):
            layout.addWidget(box)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        self._sheets_dialog = dialog                      # (tests fill it in)
        dialog.checks, dialog.paper, dialog.elevations, dialog.sections = checks, paper, elevations, sections
        dialog.template = template
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        pages = [(t("wizard.plan_sheet", name=name), [("plan", guid)]) for guid, name, box in checks if box.isChecked()]
        if elevations.isChecked():
            pages.append((t("wizard.elevations_sheet"), [("elevation", side) for side in ("N", "S", "E", "W")]))
        if sections.isChecked() and self.doc.sections:
            pages.append((t("wizard.sections_sheet"), [("section", s.name) for s in self.doc.sections]))
        n = self.doc.make_sheets(pages, paper.currentData(), template.currentData())
        if n:
            self.message(t("info.sheets_by_storey", n=n))
            self.open_sheet(len(self.doc.sheets) - n)

    def open_sheet(self, index):
        """A sheet, in its tab (opened if it is not)."""
        if not 0 <= index < len(self.doc.sheets):
            return
        self.views.open(("sheet", self.doc.sheets[index].uid))

    def _sheet_pages(self, sheets):
        """[(sheet, [(drawing, Frame, label)], title block texts)] of sheets with views, the model as it is now
        (their drawings made in a worker thread when needed)."""
        sheets_model.use_company(self.doc.title_block.get(sheets_model.COMPANY_KEY))   # (0.472: its boxes)
        made = self.make_drawings([v for s in sheets for v in s.views])
        pages = []
        for sheet in sheets:
            got = [made[self.drawing_key(v.kind, v.ref)] for v in sheet.views]
            frames = sheets_model.layout(sheet, [sheets_model.extent(d) for d in got],
                                         [self.doc.view_settings((v.kind, v.ref)).scale for v in sheet.views],
                                         len(self.doc.title_block.get(sheets_model.EXTRA_KEY) or ()))
            pages.append((sheet, [(d, f, self.view_label(v.kind, v.ref))
                                  for d, f, v in zip(got, frames, sheet.views) if f is not None],
                          self.title_block(sheet)))
        return pages

    def export_sheets(self, sheets, fmt="pdf", name=None):
        """Sheets with the model as it is now: to one PDF, a page each; or (0.128) a PNG picture or an SVG
        drawing each, in a folder chosen. name: the PDF's (a set's)."""
        sheets = [s for s in sheets if s is not None and (s.views or s.imports)]     # (0.472: or drawings put on it)
        if not sheets:
            self.message(t("info.sheet_empty"), warning=True, action=self.act_sheets_by_storey)   # (0.324)
            return
        base = os.path.splitext(self.doc.path)[0] if self.doc.path else os.path.join(_documents_dir(), "projeto")
        credit = "ArqSynth BIM {}".format(__version__)
        if fmt in ("png", "svg"):
            folder = QtWidgets.QFileDialog.getExistingDirectory(self, t("sheet.export_" + fmt),
                                                                os.path.dirname(base))
            if not folder:
                return
            paths = pdf.write_images(folder, self._sheet_pages(sheets), fmt, credit=credit)
            self.message(t("info.sheets_images", n=len(paths), fmt=fmt.upper(), f=folder))
            return
        name = name or (sheets[0].name if len(sheets) == 1 else t("sheet.file_all"))
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, t("sheet.export"), "{} - {}.pdf".format(base, name),
                                                        t("pdf.filter"))
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        pages = self._sheet_pages(sheets)
        pdf.write_sheets(path, pages, credit)
        self.message(t("info.sheets_pdf", f=os.path.basename(path), n=len(pages)))

    def print_sheets(self, sheets):
        """Sheets ▸ Print… (0.128): the printer's dialog, then the sheets, a page each, on their paper."""
        from PySide6 import QtPrintSupport
        sheets = [s for s in sheets if s is not None and (s.views or s.imports)]     # (0.472: or drawings put on it)
        if not sheets:
            self.message(t("info.sheet_empty"), warning=True, action=self.act_sheets_by_storey)   # (0.324)
            return
        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.PrinterMode.HighResolution)
        dialog = QtPrintSupport.QPrintDialog(printer, self)
        dialog.setWindowTitle(t("sheet.print"))
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        pdf.print_sheets(printer, self._sheet_pages(sheets), "ArqSynth BIM {}".format(__version__))
        self.message(t("info.sheets_printed", n=len(sheets)))

    def edit_sheet_sets(self, index):
        """A sheet's sets (0.128): the sets there are, ticked if it is in them, and a new one typed. One undo
        step."""
        if not 0 <= index < len(self.doc.sheets):
            return
        sheet = self.doc.sheets[index]
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(t("sets.title", name=sheet.name))
        layout = QtWidgets.QVBoxLayout(dialog)
        note = QtWidgets.QLabel(t("sets.note"))
        note.setWordWrap(True)
        layout.addWidget(note)
        boxes = []
        for name in sheets_model.set_names(self.doc.sheets):
            box = QtWidgets.QCheckBox(name)
            box.setChecked(name in sheet.sets)
            boxes.append(box)
            layout.addWidget(box)
        new = QtWidgets.QLineEdit()
        new.setPlaceholderText(t("sets.new"))
        layout.addWidget(new)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        self._sets_dialog = dialog                        # (tests fill it in)
        dialog.boxes, dialog.new = boxes, new
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        names = [b.text() for b in boxes if b.isChecked()] + ([new.text().strip()] if new.text().strip() else [])
        self.doc.set_sheet_sets(index, names)

    def publish_set(self, name, fmt="pdf"):
        """Sheets ▸ Publish a set (0.128): the sheets of the set, as one PDF named after it (or pictures)."""
        sheets = sheets_model.in_set(self.doc.sheets, name)
        if not sheets:
            self.message(t("info.set_empty", name=name), warning=True)
            return
        self.export_sheets(sheets, fmt, name=name)

    def _export_schedule(self, header, table, path=None, columns=None, grid=None):
        """Schedules ▸ Export: the table as shown — (0.370) an Excel workbook, its numbers as numbers, or a CSV for
        Excel (';' and decimal comma in Portuguese); (0.477) or JSON for other programs (KazaFix Cost: its columns'
        keys and units); (0.478) a table of the project's with its grid (grid: its cells as shown — titles, notes,
        merges, formats, formulas as Excel's). Returns its path, or None."""
        sp = getattr(self, "schedules_panel", None)
        title = sp.title_of(sp.ref()) if sp is not None and sp.ref() else ""
        if path is None:
            base = os.path.splitext(self.doc.path)[0] if self.doc.path else os.path.join(_documents_dir(), "tabela")
            path = self._table_path(t("sched.export"), "{} - {}.xlsx".format(base, title) if title else base + ".xlsx")
            if path is None:
                return None
        if not self._write_table(path, header, table, title, columns, grid):
            return None
        self.message(t("info.schedule_exported", f=os.path.basename(path)))
        return path

    def _table_path(self, title, start):
        """(0.370) Where a table goes: asked — an Excel workbook (XLSX) first, or a CSV, (0.477) or JSON —; a name typed
        without an extension takes the type chosen's. None: not given."""
        path, chosen = QtWidgets.QFileDialog.getSaveFileName(self, title, start, t("sched.table_filter"))
        if not path:
            return None
        if os.path.splitext(path)[1].lower() not in schedules_model.TABLE_FORMATS:
            chosen = (chosen or "").lower()
            path += ".csv" if "csv" in chosen else ".json" if "json" in chosen else ".xlsx"
        return path

    def _write_table(self, path, header, table, title=None, columns=None, grid=None):
        """(0.370) A table to `path`, an Excel workbook, a CSV or (0.477) JSON by its extension
        (model/schedules.write_table); (0.478) grid: a table of the project's cells. False (and said why) when it could
        not be written."""
        project = os.path.splitext(os.path.basename(self.doc.path))[0] if self.doc.path else ""
        try:
            schedules_model.write_table(path, header, table, decimal=decimal_sep(), title=title, columns=columns,
                                        project=project, grid=grid)
        except ImportError:
            self.message(t("err.xlsx_missing"), warning=True)
            return False
        except OSError as exc:
            self.message(t("err.table_write", f=os.path.basename(path), e=exc.strerror or exc), warning=True)
            return False
        return True

    def _refresh_tree(self, changed=None, removed=None):
        """changed / removed: what the last document change touched (None: look at everything)."""
        if not hasattr(self, "tree_panel"):
            return                            # (first call, while the window is being built)
        spatial = self.doc.ifc.spatial_tree()
        if self.doc.loading:
            self.tree_panel.mark_stale()          # (switched off while a file is read: brought up to date after)
            return
        if changed is not None and GRID_CHANGED in changed:
            changed = None                        # the grid's axes changed: list them again
        if changed is not None and VIEWS_CHANGED in changed:
            changed = None                        # the named sections changed: list them again
            QtCore.QTimer.singleShot(0, self._refresh_view_settings)    # (a template may have changed, an undo…)
        lib_key = (self.doc.ifc.count("IfcGroup"), self.doc.ifc.count("IfcTypeProduct"))
        if lib_key != self._tree_lib_key:
            changed = None                        # a group or a component made / removed: the library too
        self._tree_lib_key = lib_key
        if not self.tree_panel.wants(spatial, changed, removed, self.doc.get):
            return
        names = [s.name for s in self.doc.sections]
        storey_ids = {g for g, _n, _z in self.doc.storeys()}

        def opens(kind, ref):
            """The view as the panel opens it (a section by its index), None if it is gone."""
            if kind == "section":
                return names.index(ref) if ref in names else None
            return ref if kind == "elevation" or ref in storey_ids else None

        sheets = [(s.name, [(self.view_label(v.kind, v.ref), v.kind, opens(v.kind, v.ref)) for v in s.views])
                  for s in self.doc.sheets]
        views = {"plans": self.doc.storeys(), "sections": names, "sheets": sheets,
                 "templates": [(tpl.uid, tpl.name) for tpl in self.doc.templates],
                 "assigned": dict(self.doc.view_templates),
                 "views3d": [(v.uid, v.name) for v in self.doc.views3d],
                 "grids": [a.tag for a in self.doc.grids],
                 "details": [(d.uid, d.name) for d in self.doc.details],                   # (0.133)
                 "rebars": self._reinforced(), "structure": self._structural_storeys(),  # (0.168)
                 "openings": any(o.is_bim and o.ifc_class in ("IfcDoor", "IfcWindow")              # (0.293: of
                                 for o in self.doc.objects.values()),                                # the model's)
                 "steel": self._has_steel()}                                                         # (0.502)
        lib = self.doc.ifc.library()
        library = {"components": [(g, name, len(inst), placeable) for g, name, inst, placeable in lib["components"]],
                   "groups": [(m, name, len(copies)) for m, name, copies in lib["groups"]]}
        self.tree_panel.show_project(spatial, project_tree.rows(self.doc), views, library)

    def _circuit_points(self, ids):
        """(0.144) The ids, a circuit's (a row of the load schedule) in place of its points."""
        out = []
        for i in ids:
            if self.doc.get(i) is None:
                try:
                    out += self.doc.ifc.circuit_points(i)
                    continue
                except Exception:
                    pass
            out.append(i)
        return out

    def _select_from_tree(self, ids):
        """Select what was clicked in the Project panel. With "only the active storey", clicking
        elements of another storey makes that storey active (it would be hidden otherwise)."""
        objs = [o for o in (self.doc.get(i) for i in ids) if o is not None]
        if self.viewport.only_active_storey:
            others = {o.storey for o in objs if o.is_bim and not self.viewport.is_shown(o)}
            if len(others) == 1:
                self.set_active_storey(others.pop())
        if self.tool.name != "select":
            self.set_tool("select")
        self.viewport.set_selection({o.id for o in objs if self.viewport.is_shown(o)})

    # ------------------------------------------------------------ the navigator's controls (0.524)

    def _apply_controls(self):
        """The flags kept in the IFC (model/controls) on the views: hidden, out of the Realistic style, not picked —
        and the elements isolated from the navigator."""
        if not hasattr(self, "viewport"):
            return
        hidden = controls.ids_with(self.doc, "hidden")
        if self._isolated is not None:
            hidden |= {o.id for o in self.doc.objects.values() if o.is_bim and o.id not in self._isolated}
        self.viewport.set_controls(hidden=hidden, no_render=controls.ids_with(self.doc, "no_render"),
                                   locked=controls.ids_with(self.doc, "locked"))
        if hasattr(self, "tree_panel"):
            self.tree_panel.refresh_controls()

    def set_control(self, ids, flag, on):
        """A navigator's control switched on these elements (one undo step), kept in the IFC."""
        n = controls.set_flag(self.doc, ids, flag, on)
        self._apply_controls()
        return n

    def _unlocked(self, ids):
        """The ids without the locked ones (told when some were left out)."""
        locked = [i for i in ids if controls.has(self.doc, i, "locked")]
        if locked:
            self.message(t("info.locked_refused", n=len(locked)), warning=True)
        return [i for i in ids if i not in locked and self.doc.get(i) is not None]

    def change_storey(self, ids, storey_guid):
        """(0.527) Elements put on another storey (Properties ▸ Pavimento, the navigator's menu): up / down by the
        difference of levels; the locked ones left out. Returns the GlobalIds moved."""
        ids = self._unlocked([i for i in ids if isinstance(i, str)])
        try:
            moved = bim.change_storey(self.doc, ids, storey_guid)
        except ValueError as exc:
            self.message(t("err.edit_refused", e=refusal(exc)), warning=True)
            return []
        if not moved:
            self.message(t("info.storey_same"))
            return []
        name = next((n for g, n, _z in self.doc.storeys() if g == storey_guid), "")
        self.message(t("info.storey_changed", n=len(moved), s=name))
        return moved

    def hide_keys(self, action):
        """(0.525) Ctrl+H / Shift+H / Alt+H on what is selected (in the view or the navigator)."""
        if action == "show_all":
            self.tree_element_action("show_all", [])
            return
        ids = [i for i in self.viewport.selection if isinstance(i, str) and self.doc.get(i) is not None]
        if not ids and hasattr(self, "tree_panel"):
            ids = [i for i in self.tree_panel._selected_members() if isinstance(i, str)]
        if not ids:
            self.message(t("info.hide_nothing"), warning=True)
            return
        if action == "hide":
            self.set_control(ids, "hidden", True)
        else:
            self.tree_element_action("isolate", ids)

    def tree_element_action(self, action, ids, arg=None):
        """(0.524) The navigator's right-click menu on elements, a group, a category: the program's own commands."""
        if action == "isolate":
            self._isolated = set(ids)
            self._apply_controls()
            self.message(t("info.isolated", n=len(ids)))
            return
        if action == "show_all":
            self._isolated = None
            self.set_control(list(controls.ids_with(self.doc, "hidden")), "hidden", False)
            self._apply_controls()
            return
        if action == "change_storey":
            self.change_storey(ids, arg)
            return
        ids = self._unlocked(ids) if action in ("delete", "duplicate", "edit_type") else \
            [i for i in ids if self.doc.get(i) is not None]
        if not ids:
            return
        if self.tool.name != "select":
            self.set_tool("select")
        old = self.viewport.locked_ids
        self.viewport.locked_ids = set()                 # (copied / replicated as they are, even locked)
        try:
            self.viewport.set_selection(set(ids))
        finally:
            self.viewport.locked_ids = old
        if action == "delete":
            self._delete()
        elif action == "copy":
            self.copy_to_clipboard()
        elif action == "duplicate":                      # (as Blender's Shift+D: the copy on the cursor, a click puts it)
            self.copy_to_clipboard()
            self.paste()
        elif action == "replicate":
            self.repeat_on_storeys([arg])
        elif action == "edit_type":
            self._refresh_properties()
            button = self.props.findChild(QtWidgets.QPushButton, "props_edit_type")
            if button is None:
                self.message(t("info.no_type"), warning=True)
            else:
                button.click()

    def _frame_from_tree(self, ids):
        shown = [i for i in ids if self.doc.get(i) is not None and self.viewport.is_shown(self.doc.get(i))]
        if shown:
            self.viewport.zoom_extents(shown)

    def typical_floors(self, chosen=None):
        """Typical floors (0.90): the active storey made equal to the storeys chosen (its elements copied to
        them; from then on what is drawn, changed or deleted on one is on all) — or, if it already is, no longer
        (each keeps its elements). One undo step. (0.463) chosen: the storeys picked in the Storeys panel's list —
        two or more: made equal at once (the active one's elements, or the lowest's, copied to the others; their
        plans' dimensions and drawing shared from then on)."""
        active = self.doc.active_storey
        if self.doc.ifc.typical_of(active) is not None:
            others = [n for g, n, _z in self.doc.storeys()
                      if g != active and self.doc.ifc.typical_of(g) == self.doc.ifc.typical_of(active)]
            bim.unmake_typical(self.doc, active)
            self.message(t("info.untypical", name=self._storey(active)[0], others=", ".join(others)))
            return
        levels = {g: (n, z) for g, n, z in self.doc.storeys()}
        chosen = [g for g in (chosen or ()) if g in levels]
        if len(chosen) >= 2:
            taken = [g for g in chosen if self.doc.ifc.typical_of(g) is not None]
            if taken:
                self.message(t("info.typical_taken", name=levels[taken[0]][0]), warning=True)
                return
            source = active if active in chosen else min(chosen, key=lambda g: levels[g][1])
            others = sorted((g for g in chosen if g != source), key=lambda g: levels[g][1])
            full = [g for g in others if self.doc.ifc._storey_elements(g)]
            self._stop_drawing()
            bim.make_typical(self.doc, [source] + others, source, t("typical.default_name"))
            kept = t("info.typical_kept", names=", ".join(levels[g][0] for g in full), name=levels[source][0]) \
                if full else ""
            self.message(t("info.typical_made", name=levels[source][0],
                           others=", ".join(levels[g][0] for g in others), kept=kept))
            return
        dialog = storeys.TypicalDialog(self, self.doc.storeys(), active)
        self._sel_dialog = dialog                           # (tests)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        chosen = dialog.list.ticked()
        if not chosen:
            self.message(t("info.typical_none"), warning=True)
            return
        name = dialog.name.text().strip() or t("typical.default_name")
        self._stop_drawing()
        bim.make_typical(self.doc, [active] + chosen, active, name)
        names = [n for g, n, _z in self.doc.storeys() if g in chosen]
        self.message(t("info.typical", name=self._storey(active)[0], others=", ".join(names)))

    def _refresh_storeys(self):
        if not hasattr(self, "storeys_panel"):
            return                            # (first call, while the window is being built)
        letters = {}
        if not self.doc.loading:
            for k, (_model, members) in enumerate(sorted(self.doc.ifc.typical_sets().items(), key=lambda kv: kv[1])):
                letters.update({s: chr(ord("A") + k % 26) for s in members})
        self.storeys_panel.show_storeys(self.doc.storeys(), self.doc.active_storey, letters,
                                        live=self.doc.typical_live)                       # (0.465: «=» on / off)
        self.storeys_panel.show_level_style(styles_model.symbol(self.doc.graphic_style, "level"))     # (0.462)
        name, z = self._storey(self.doc.active_storey)
        view = (t("storeys.status_plan") if self.viewport.plan
                else " — " + self._view_name if self.viewport.section is not None else "")
        equal = ""                                       # (0.463) a typical storey: its equals named in the footer
        if letters.get(self.doc.active_storey):
            mates = [n for g, n, _z in self.doc.storeys() if g != self.doc.active_storey
                     and letters.get(g) == letters[self.doc.active_storey]]
            equal = t("storeys.status_typical", others=", ".join(mates)) if mates else ""
            if mates and not self.doc.typical_live:
                equal += t("storeys.status_live_off")
        self.storey_label.setText(t("storeys.status", name=name, z=storeys.level_text(z)) + equal + view)
        if hasattr(self, "program_panel") and self.program_panel.isVisible():         # (0.475: its storey's lines)
            self.program_panel.follow_storey(self.doc.active_storey)

    def _update_title(self):
        shared = t("share.title_mark") if sharing.central_of(self.doc.path) else ""
        self.setWindowTitle("{} {} — {}{}{}".format(t("app.title"), __version__, self._file_label(), shared,
                                                    " *" if self.doc.modified else ""))
        if hasattr(self, "header"):                    # (0.182) the project's name in the header too
            self.header.set_project("{}{}{}".format(self._file_label(), shared, "*" if self.doc.modified else ""))

    def _refresh_properties(self):
        """The selection's properties; with nothing selected, the view shown's (not a sheet's, nor
        while a file's IFC is still being read)."""
        if not hasattr(self, "props") or getattr(self, "_editing_many", False):
            return                                # (first call, while the window is being built; 0.187: once, after)
        with self.doc.ifc.remembering():          # (0.225: the panel asks the storeys a few times: once)
            self._show_properties()
            if hasattr(self, "quick"):            # (0.354: the quick edit, the same elements shown again)
                self.quick.refresh(self.doc, list(self.viewport.selection))
            self._refresh_program()               # (0.357: the rooms made against the programme)

    # ------------------------------------------------------------ the programme (0.357)

    def show_room_program(self):
        """Arquitetura ▸ Programa de necessidades: its panel, beside the Project panel — empty, it says how to import
        one."""
        self.program_panel.show()
        self.program_panel.raise_()
        self._refresh_program()
        if not self.doc.ifc.room_program():
            self.message(t("info.program_none"))

    def import_room_program(self, path=None):
        """The programme read from a file (CSV / TXT: model/room_program.py), in place of the one kept: one undo
        step. Returns how many rooms it asks for."""
        from ..model import room_program
        if path is None:
            start = os.path.dirname(self.doc.path) if self.doc.path else _documents_dir()
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("program.import"), start, t("program.filter"))
            if not path:
                return 0
        try:
            building, needs = room_program.read_program(path, self.doc.storeys())   # (0.475: JSON too, an AI's)
        except OSError as exc:
            self.message(t("err.open", f=os.path.basename(path), e=exc), warning=True)
            return 0
        except ValueError as exc:
            self.message(t("err.program_json", f=os.path.basename(path), e=exc), warning=True)
            return 0
        if not needs:
            self.message(t("err.program_empty", f=os.path.basename(path)), warning=True)
            return 0
        bim.set_room_program(self.doc, needs, building)
        self.program_panel.show()
        self.program_panel.raise_()
        self._refresh_program()
        self.message(t("info.program_imported", n=len(needs), f=os.path.basename(path)))
        return len(needs)

    def clear_room_program(self):
        if self.doc.ifc.room_program():
            bim.set_room_program(self.doc, [])
            self._refresh_program()

    def _refresh_program(self):
        """(0.475) The Programme panel shown again: each line against the rooms placed, the conflicting zones."""
        if not (hasattr(self, "program_panel") and self.program_panel.isVisible()) or self.doc.loading:
            return
        from ..model import program_rules, room_program
        ifc = self.doc.ifc
        needs = ifc.room_program()
        storeys = self.doc.storeys()
        states = room_program.states(needs, ifc.spaces(), ifc.room_program_links(), storeys)
        try:
            found = program_rules.conflicts(self.doc)
        except Exception:                                 # noqa: BLE001 (the IFC still being read)
            found = []
        self.program_panel.show_program(needs, building=program_rules.project_type(self.doc), states=states,
                                        conflicts=found, storeys=storeys, active=self.doc.active_storey)
        # a conflict that was not there (a door put between them, a room's use changed): said at once
        pairs = {frozenset(c[:2]) for c in found}
        before, self._program_pairs = getattr(self, "_program_pairs", None), (id(self.doc.ifc), pairs)
        if before is not None and before[0] == id(self.doc.ifc):
            new = [c for c in found if frozenset(c[:2]) not in before[1]]
            if new:
                a, b = (((self.doc.ifc.space_info(g) or {}).get("name") or "?") for g in new[0][:2])
                self.message(t("info.program_conflict_new", a=a, b=b, why=new[0][3][2]), warning=True)

    def _room_drop(self, event, et):
        """A drag over the view: a name of the programme taken (its own kind of data), dropped — the room there."""
        from ..model import room_program
        from . import room_program as program_ui
        data = event.mimeData()
        if not data.hasFormat(program_ui.MIME):
            return False
        if et != QtCore.QEvent.Type.Drop:
            event.acceptProposedAction()
            return True
        needs = room_program.from_text(bytes(data.data(program_ui.MIME)).decode("utf-8"))
        pos = event.position()
        if needs:
            QtCore.QTimer.singleShot(0, lambda: self.drop_room_need(needs[0], float(pos.x()), float(pos.y())))
        event.acceptProposedAction()
        return True

    def drop_room_need(self, need, x, y):
        """(0.357) A name of the programme dropped on the view at (x, y): the room there named so (interior or exterior
        as the programme says) — the one already there, or a new one between the walls of the active storey.
        Returns its GlobalId, or None."""
        from ..core.sketch_geometry import ray_plane
        z = self.doc.work_level()
        origin, direction = self.viewport.ray(x, y)
        up = np.array((0.0, 0.0, 1.0))
        p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), up)
        if p is None:
            p = ray_plane(origin, direction, np.array((0.0, 0.0, z)), -up)
        found = bim.room_from_program(self.doc, (p[0], p[1]), need) if p is not None else None
        if found is None:
            self.message(t("err.room_open"), warning=True)
            return None
        guid, made = found
        self._refresh_program()
        self._said_room_need(need, guid, made)
        return guid

    # ------------------------------------------------------------ (0.475) the programme's manager

    def change_room_program(self, needs, building=None):
        """The Programme panel's lines (or its type of building) changed there: kept — one undo step."""
        bim.set_room_program(self.doc, needs, building)
        self._refresh_program()

    def start_room_need(self, need):
        """A line of the Programme panel clicked: placed with the next click inside walls (tools/room_need.py) — on
        its storey (made the active one)."""
        from ..model import room_program
        floor = room_program.storey_of(need, self.doc.storeys())
        if floor is not None and floor != self.doc.active_storey:
            self.set_active_storey(floor)
        if self.tool.name != "room_need":
            self.set_tool("room_need")
        self.tools["room_need"].set_need(need)
        return self.tools["room_need"]

    def place_room_need(self, need, x, y):
        """The Room-from-the-programme tool's click at (x, y): the room there (as a name dropped), then the next line of
        the storey still to place — none left: Selecionar."""
        guid = self.drop_room_need(need, x, y)
        if guid is None:
            return None
        from ..model import room_program
        ifc = self.doc.ifc
        storeys = self.doc.storeys()
        states = room_program.states(ifc.room_program(), ifc.spaces(), ifc.room_program_links(), storeys)
        here = self.doc.active_storey
        state = next((s for s in states if s.need.uid == need.uid), None)
        if state is not None and state.made < need.count:
            return guid                                   # (more of it to place: the same line)
        following = [s.need for s in states if s.status == "todo"
                     and room_program.storey_of(s.need, storeys) in (here, None)]
        if following and self.tool.name == "room_need":
            self.tools["room_need"].set_need(following[0])
        elif self.tool.name == "room_need":
            self.set_tool("select")
            self.message(t("info.program_storey_done"))
        return guid

    def _said_room_need(self, need, guid, made):
        """What a room placed from the programme says: made or named, its area against the one wanted — and, when it
        opens into a room it should not, the conflicting zones (the Verifier's warning in the footer too)."""
        from ..model import program_rules
        info = self.doc.ifc.space_info(guid) or {}
        area = float(info.get("area") or 0.0)
        text = t("info.program_made" if made else "info.program_named", name=need.name)
        if need.area:
            m2 = "{:.2f} m²".format(area).replace(".", decimal_sep())
            text += " " + (t("info.program_area_ok", a=m2) if area >= need.area - 0.005 else
                           t("info.program_area_short", a=m2, w="{:.2f} m²".format(need.area).replace(
                               ".", decimal_sep())))
        try:
            mine = [c for c in program_rules.conflicts(self.doc) if guid in c[:2]]
        except Exception:                                 # noqa: BLE001 (the IFC still being read)
            mine = []
        if mine:                                          # (the footer's warning follows the model by itself)
            self.message(t("info.program_conflict", name=need.name, why=mine[0][3][2]), warning=True)
            return
        self.message(text, warning=bool(need.area) and area < need.area - 0.005)

    def copy_program_prompt(self, what=None):
        """«Pedir à IA…»: the request for an AI — the programme of this type of building, as JSON this panel reads —
        copied to paste in it (ChatGPT, Claude, Gemini…). Returns the text."""
        from ..model import program_rules, room_program
        building = program_rules.project_type(self.doc)
        language = lang()
        text = room_program.AI_PROMPT.format(
            what=what or t("program.ai_what", type=program_rules.type_label(building, language).lower()),
            type=building, uses=", ".join(program_rules.uses_for(building)),
            types=", ".join(program_rules.BUILDING_TYPES))
        QtWidgets.QApplication.clipboard().setText(text)
        self.message(t("info.program_ai"))
        return text

    def quick_edit(self):
        """(0.354) TAB with elements chosen (Select): their quick edit beside them, over the view (ui/quick_edit.py) —
        or closed, if it is open. Returns whether TAB was used."""
        if self.quick.isVisible():
            self.quick.close_panel()
            return True
        ids = [i for i in self.viewport.selection if self.doc.get(i) is not None]
        if not ids or self.sheet_shown():
            return False
        view = QtCore.QRect(self.canvas.mapTo(self.quick.parentWidget(), QtCore.QPoint(0, 0)), self.canvas.size())
        with self.doc.ifc.remembering():
            self.quick.show_for(self.doc, ids, self._screen_box(ids), view)
        return True

    def _screen_box(self, ids):
        """(0.354) The elements' box on the view, in the views' area's coordinates (a QRect)."""
        pts = []
        for i in ids:
            obj = self.doc.get(i)
            mesh = getattr(obj, "mesh", None)
            if mesh is None:
                continue
            if hasattr(mesh, "bounds"):
                bounds = mesh.bounds()
            else:                                           # (a sketch's: its corners)
                verts = np.asarray(mesh.verts, dtype=float).reshape(-1, 3)
                bounds = (verts.min(axis=0), verts.max(axis=0)) if len(verts) else None
            if bounds is None:
                continue
            lo, hi = np.asarray(bounds[0], dtype=float), np.asarray(bounds[1], dtype=float)
            corners = np.array([(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
            m = np.asarray(getattr(obj, "matrix", np.eye(4)), dtype=float)
            pts.append(corners @ m[:3, :3].T + m[:3, 3])
        size = self.canvas.size()
        if pts:
            xy = self.viewport.project_many(np.concatenate(pts))
            xy = xy[~np.isnan(xy).any(axis=1)]
        else:
            xy = np.zeros((0, 2))
        if len(xy):
            lo = np.clip(xy.min(axis=0), 0, (size.width(), size.height()))
            hi = np.clip(xy.max(axis=0), 0, (size.width(), size.height()))
        else:
            lo = hi = np.array((size.width() / 2.0, size.height() / 2.0))
        top_left = self.canvas.mapTo(self.quick.parentWidget(), QtCore.QPoint(int(lo[0]), int(lo[1])))
        return QtCore.QRect(top_left, QtCore.QSize(max(1, int(hi[0] - lo[0])), max(1, int(hi[1] - lo[1]))))

    def _show_properties(self):
        self._sync_footer()                       # (the footer's view controls: the view shown's, 0.186)
        if self.viewport.selected_axes and not self.viewport.selection and not self.doc.loading:
            self.props.show_grid_axes(self.doc, self.viewport.selected_axes)       # grid axes (0.72)
            return
        if self.viewport.selected_rooms and not self.viewport.selection and not self.doc.loading:
            self.props.show_rooms(self.doc, self.viewport.selected_rooms)          # rooms (0.99)
            return
        anns = [a for a in self.viewport.selected_annotations if a in self.doc.annotations]
        if anns and not self.viewport.selection and not self.doc.loading:         # drawings in the view (0.191)
            self.props.show_annotations(self.doc, anns, self.viewport.view_plane())
            return
        dims = [d for d in self.viewport.selected_dims if d in self.doc.dimensions]
        if dims and not self.viewport.selection and not self.doc.loading:         # dimensions (0.193)
            self.props.show_dimensions(self.doc, dims, self.viewport.view_plane())
            return
        if self.viewport.selection:
            self._props_sheet = None                # (0.470: something chosen in the model: its, from now on)
        sheet = self._properties_sheet() if not self.viewport.selection and not self.doc.loading else None
        if sheet is not None:                     # (0.470) a sheet's, as Revit's: its type on top, Editar tipo…
            from .sheet_type_dialog import kinds
            self.props.show_sheet(self.doc, sheet, sheets_model.number_of(self.doc.sheets, sheet, self.doc.title_block),
                                  kinds(), self.title_block()["project"])
            return
        if self.viewport.selection or not hasattr(self, "views") or self.sheet_shown() or self.doc.loading:
            self.props.show_selection(self.doc, self.viewport.selection)
            return
        view = self._view_key()
        self.props.show_view(self.doc, view, self._view_tab_label(view),
                             lambda: {o.ifc_class for o in self.doc.objects.values() if o.is_bim})

    def _view_key(self):
        """The view shown, as its properties are kept: ("plan", storey), ("section", name),
        ("elevation", side) or ("3d",)."""
        return self.viewport.current_view() or self._live_3d()

    # ------------------------------------------------------------ input

    def _on_pointer(self, event):
        kind = {"pointer_down": "down", "pointer_move": "move", "pointer_up": "up"}.get(event.type)
        if kind == "down":
            self.notice.dismiss()                   # (0.321) read: the next click in the view takes it down
        if kind is not None and self.viewport.cube_event(kind, event.x, event.y, getattr(event, "button", None)):
            return                                  # the view cube took it (0.79, 0.81): not the tool
        if self._loading:
            return                                  # looking around only (the view moves by itself)
        buttons = tuple(getattr(event, "buttons", ()) or ())
        if event.type == "pointer_move" and MIDDLE in buttons:
            return  # orbiting / panning: leave the tool alone
        x, y = event.x, event.y
        mods = tuple(event.modifiers or ())
        if event.type == "pointer_down":
            self.canvas.setFocus()
            self.quick.close_panel()                  # (0.354: a click in the view closes the quick edit)
            self.tool.pointer_down(x, y, event.button, mods)
        elif event.type == "pointer_move":
            self.tool.pointer_move(x, y, mods)
        elif event.type == "pointer_up":
            self.tool.pointer_up(x, y, event.button, mods)

    def _is_typing_key(self, event):
        if event.modifiers() & (Mod.ControlModifier | Mod.AltModifier | Mod.MetaModifier):
            return False
        ch = event.text()
        if not ch or not self.tool.accepts_typing:
            return False
        if getattr(self.tool, "accepts_text", False):     # (words: a text drawn in a view, 0.120)
            return ch.isprintable()
        ch = ch.lower()
        return ch in TYPED_CHARS or (bool(self._typed) and (ch in UNIT_CHARS or      # (0.373: "2r", "12s" in the Arc)
                                                            ch in getattr(self.tool, "typed_suffixes", "")))

    def _common_key_name(self, event):
        """The placement key (0.86) of a key event — "r", "shift+r", "space", "shift+space", "f", "x", "y", "n" —
        if the tool in use takes it (and nothing is being typed: then x is a series of copies…), else None."""
        if self.tool is None or not self.tool.common_keys:
            return None
        mods = event.modifiers()
        if mods & (Mod.ControlModifier | Mod.AltModifier | Mod.MetaModifier):
            return None
        name = {Key.Key_R: "r", Key.Key_Space: "space", Key.Key_F: "f", Key.Key_X: "x", Key.Key_Y: "y",
                Key.Key_Z: "z", Key.Key_N: "n"}.get(event.key())         # (0.412: Z — Rotate's axis)
        if name is None or (self._typed and name != "space"):
            return None
        if mods & Mod.ShiftModifier:
            name = "shift+" + name
        return name if name in self.tool.common_keys else None

    def _owns_keys(self, obj):
        """Key events to intercept: widgets of this window that are not text fields."""
        if not isinstance(obj, QtWidgets.QWidget) or obj.window() is not self:
            return False
        return not isinstance(obj, (QtWidgets.QLineEdit, QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit,
                                    QtWidgets.QAbstractSpinBox, QtWidgets.QComboBox))

    def centre_window(self, window):
        """(0.526, the owner: «organize melhor as janelas flutuantes, para ficar mais centralizada») A dialog or a
        floating panel, the first time it is shown, centred over the program's window (not left where the system put
        it — under WSLg, often at the screen's corner), and kept inside the screen. Moved by hand later: left there."""
        # (0.537) by QWidget's own methods: a dialog may have a field of the same name — the View styles' «width» (its
        # lines' thickness, a QComboBox) made «window.width()» fail each time it opened
        widget = QtWidgets.QWidget
        if window is self or widget.property(window, "arq_centred") or \
                widget.windowType(window) == QtCore.Qt.WindowType.Popup:
            return False
        widget.setProperty(window, "arq_centred", True)
        if widget.width(window) < 50:
            widget.adjustSize(window)
        frame = widget.frameGeometry(window)
        centre = self.frameGeometry().center()
        frame.moveCenter(centre)
        screen = (self.screen() or QtGui.QGuiApplication.primaryScreen()).availableGeometry()
        frame.moveLeft(max(screen.left(), min(frame.left(), screen.right() - frame.width())))
        frame.moveTop(max(screen.top(), min(frame.top(), screen.bottom() - frame.height())))
        widget.move(window, frame.topLeft())
        return True

    def _footer_tip(self, widget):
        """(0.526, the owner: «no rodapé… a descrição fique para cima… fica oculta e não se lê nada») A button of the
        footer (the status bar: navigation, views, scale…): its tip shown above it, not under it — under it, it went
        under the screen's foot (WSLg does not know the taskbar). True when shown so."""
        bar = self.statusBar()
        if not (widget is bar or bar.isAncestorOf(widget)):
            return False
        text = widget.toolTip()
        if not text:
            return False
        top = widget.mapToGlobal(QtCore.QPoint(widget.width() // 2, 0))
        QtWidgets.QToolTip.showText(top, text, widget)
        tip = next((w for w in QtWidgets.QApplication.topLevelWidgets()
                    if w.isVisible() and w.inherits("QTipLabel")), None)
        if tip is None:
            return True
        tip.adjustSize()
        screen = (widget.screen() or QtGui.QGuiApplication.primaryScreen()).availableGeometry()
        x = min(max(screen.left() + 4, top.x() - tip.width() // 2), screen.right() - tip.width() - 4)
        tip.move(x, top.y() - tip.height() - 6)
        self.footer_tip_shown = tip.geometry()      # (for the tests)
        return True

    def eventFilter(self, obj, event):
        try:
            return self._filter(obj, event)
        except RuntimeError:                        # (Qt objects already gone: the program is closing)
            return False

    def _filter(self, obj, event):
        et = event.type()
        if et == QtCore.QEvent.Type.ToolTip and isinstance(obj, QtWidgets.QWidget) and self._footer_tip(obj):
            return True                             # (0.526) the footer's tips shown above it
        if et == QtCore.QEvent.Type.Show and isinstance(obj, (QtWidgets.QDialog, QtWidgets.QDockWidget)) \
                and obj.isWindow():
            self.centre_window(obj)                 # (0.526) the floating windows over the middle of the program
        if self._loading:
            return False                            # no typed measurements while a file is being read
        if et in (QtCore.QEvent.Type.DragEnter, QtCore.QEvent.Type.DragMove, QtCore.QEvent.Type.Drop) and \
                obj in (self.canvas, getattr(self.canvas, "_subwidget", None)):
            return self._room_drop(event, et)       # (0.357) a name of the programme dragged onto the view
        if et in (QtCore.QEvent.Type.KeyPress, QtCore.QEvent.Type.ShortcutOverride) and \
                (self.sheet_shown() or self.start_shown()):
            return False                            # (a sheet, the start page: no measurements typed for the 3D tools)
        if et in (QtCore.QEvent.Type.KeyPress, QtCore.QEvent.Type.ShortcutOverride) \
                and event.key() != Key.Key_Control:
            self._ctrl_alone = False                # (0.310: Ctrl+Z, a shortcut, is not Ctrl alone either)
        if et in (QtCore.QEvent.Type.KeyPress, QtCore.QEvent.Type.KeyRelease) and self._owns_keys(obj) \
                and not event.isAutoRepeat():
            # Ctrl pressed and released on its own (no other key, no click): Move / Rotate copy on / off
            if event.key() == Key.Key_Control:
                if et == QtCore.QEvent.Type.KeyPress:
                    self._ctrl_alone = True
                elif getattr(self, "_ctrl_alone", False):
                    self._ctrl_alone = False
                    self.tool.ctrl_tap()
                    self._sync_context_bar()        # (its toggle on the contextual bar, as tapped)
            # (0.380) Shift / Alt pressed or let go with the mouse still: a tool that shows something by them (the
            # wall's profile: a side pulled as a corner, an arc, a curve) shows it now, not at the next move
            hook = getattr(self.tool, "modifiers_changed", None)
            if hook is not None and event.key() == Key.Key_Control and not event.isAutoRepeat():
                # (0.528) Ctrl: a wall's ends show their «+» while it is held (the select tool); not swallowed
                held = {n for n, m in (("Shift", Mod.ShiftModifier), ("Alt", Mod.AltModifier)) if event.modifiers() & m}
                if et == QtCore.QEvent.Type.KeyPress:
                    held.add("Ctrl")
                hook(tuple(sorted(held)))
            elif hook is not None and event.key() in (Key.Key_Shift, Key.Key_Alt):
                held = {n for n, m in (("Shift", Mod.ShiftModifier), ("Alt", Mod.AltModifier)) if event.modifiers() & m}
                name = "Shift" if event.key() == Key.Key_Shift else "Alt"
                if et == QtCore.QEvent.Type.KeyPress:
                    held.add(name)
                else:
                    held.discard(name)
                hook(tuple(sorted(held)))
                return True                         # (Alt alone: not the hidden menu bar's)
        if et == QtCore.QEvent.Type.MouseButtonPress:
            self._ctrl_alone = False
        if et in (QtCore.QEvent.Type.ShortcutOverride, QtCore.QEvent.Type.KeyPress) and self._owns_keys(obj) \
                and self._wall_chord(event, et):
            return True                             # (0.432: «W + letra», the walls' second letter)
        if et in (QtCore.QEvent.Type.ShortcutOverride, QtCore.QEvent.Type.KeyPress) and self._owns_keys(obj):
            name = self._common_key_name(event)
            if name is not None:                    # a placement key the tool uses (0.86): not a shortcut
                event.accept()
                if et == QtCore.QEvent.Type.KeyPress and self.tool.common_key(name):
                    self._sync_context_bar()
                return True
            if et == QtCore.QEvent.Type.ShortcutOverride and self._is_typing_key(event):
                event.accept()  # deliver as a key press, not as a shortcut
                return True
            if et == QtCore.QEvent.Type.KeyPress and self._handle_key(event):
                return True
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------ (0.432) «W + letra», as the addon's
    WALL_CHORD_S = 1.25
    # (W W is the Wall tool itself — W is not a second letter: the same press, passed up the widgets, would be taken
    # for its own second letter)
    WALL_CHORD = {"T": "trim_extend", "E": "trim_extend", "A": "align", "O": "orthogonalize",
                  "R": "rotate", "S": "split_wall", "M": "mirror", "J": "wall_joins", "C": "wall_joins",
                  "U": "attach_top", "B": "attach_base", "G": "select", "L": "select_linked", "Q": "quick_edit"}

    def _wall_chord(self, event, et):
        """(0.432) W pressed alone: the Wall tool as always — and for 1,25 s a second letter is a walls' command (T
        trim, E extend, A align, O orthogonalize, R rotate, S split, M mirror, J / C joins, U / B attach top / base, G
        grips, L the walls joined, Q quick edit), the balloon saying them. True when the key was the second letter."""
        import time as _time
        Key = QtCore.Qt.Key
        if event.key() in (Key.Key_Shift, Key.Key_Control, Key.Key_Alt, Key.Key_Meta, Key.Key_AltGr):
            return False                            # (a modifier pressed alone: the window stays open)
        held = event.modifiers() & (Mod.ControlModifier | Mod.AltModifier | Mod.ShiftModifier | Mod.MetaModifier)
        letter = QtGui.QKeySequence(event.key()).toString().upper()
        now = _time.monotonic()
        until = getattr(self, "_chord_until", 0.0)
        if not held and now < until and letter in self.WALL_CHORD and not self._typed:
            if et == QtCore.QEvent.Type.ShortcutOverride:
                event.accept()                      # (its own shortcut — T is the Tape's — not this time)
                return True
            self._chord_until = 0.0
            self.wall_command(self.WALL_CHORD[letter])
            return True
        if letter == "W" and not held:
            if et == QtCore.QEvent.Type.ShortcutOverride and not self._typed and self._common_key_name(event) is None:
                self._chord_until = now + self.WALL_CHORD_S    # (the shortcut goes on: the Wall tool)
                QtCore.QTimer.singleShot(0, lambda: self.message(t("chord.walls")))
            return False
        if now < until:                             # (another key between — W, F1, R —: no second letter; R the
            self._chord_until = 0.0                 #  Rectangle, as always)
        return False

    def wall_command(self, name):
        """(0.432) A walls' command by its name (the second letter of «W + letra»)."""
        acts = {"orthogonalize": self.act_orthogonalize, "attach_top": self.act_attach_top,
                "attach_base": self.act_attach_base}
        if name in acts:
            acts[name].trigger()
        elif name == "select_linked":
            self.select_linked_walls()
        elif name == "quick_edit":
            self.quick_edit()
        elif name in self.tools:
            self.set_tool(name)
        label = t("chord.cmd." + name)
        self.message(t("chord.done", c=label))

    def select_linked_walls(self):
        """(0.432) W L: the walls joined to the ones chosen, and those joined to them, all chosen."""
        walls = {g for g in self.viewport.selection if self.doc.ifc.kind_of(g) == "wall"}
        if not walls:
            self.message(t("chord.no_walls"), warning=True)
            return 0
        seen, todo = set(walls), list(walls)
        while todo:
            for g in self.doc.ifc.joined_walls([todo.pop()]):
                if g not in seen and self.doc.get(g) is not None:
                    seen.add(g)
                    todo.append(g)
        if self.tool is None or self.tool.name != "select":
            self.set_tool("select")
        self.viewport.set_selection(seen)
        return len(seen)

    def _handle_key(self, event):
        key = event.key()
        if key == Key.Key_Escape:
            self.notice.dismiss(force=True)          # (0.321)
            if self._move_play is not None:          # (0.364: a camera move played: stopped, nothing else)
                self.stop_scene_move()
                return True
            if self.quick.isVisible():               # (0.354: the quick edit closed, nothing else)
                self.quick.close_panel()
                return True
            if not self._typed and self.cancel_pick():
                return True                          # (0.322: the command waiting given up, the selection kept)
            if self._typed:
                self._typed = ""
                self._refresh_vcb()
            elif getattr(self.tool, "escape", None) is not None and self.tool.escape():
                pass                          # (0.410) the tool took it: a hole being drawn given up, its mode left
            elif self.tool.placement:
                self.set_tool("select")       # (placing ends with Esc: Space is the insertion point there, 0.86)
            elif self.tool.name == "zoom_window":
                self.tool.cancel()
                self.set_tool(self.tool.back_to if self.tool.back_to in self.tools else "select")
            else:
                self.tool.cancel()
                self.viewport.tracking.clear()          # (the points acquired are let go)
            return True
        if key in (Key.Key_Return, Key.Key_Enter):
            if not self._typed and self.pick_request is not None and self.tool.name == "select" \
                    and getattr(self.tool, "_picking", None) is None:
                self.finish_pick()                   # (0.322) the elements asked for: picked
                return True
            if self._typed:
                text, self._typed = self._typed, ""
                self._refresh_vcb()
                self.tool.typed(text)
            else:
                self.tool.enter()
            return True
        if key == Key.Key_Backspace and self._typed:
            self._typed = self._typed[:-1]
            self._refresh_vcb()
            return True
        if key == Key.Key_Tab and not event.modifiers() & Mod.ControlModifier:
            return self.tool.tab()            # e.g. the wall's reference line (else Qt moves the focus)
        arrows = {Key.Key_Up: "up", Key.Key_Down: "down", Key.Key_Left: "left", Key.Key_Right: "right"}
        if key in arrows and not event.modifiers() & (Mod.AltModifier | Mod.ControlModifier):
            return self.tool.arrow(arrows[key])       # (Walk: the arrow keys walk and turn, 0.80)
        if self._is_typing_key(event):
            self._typed += event.text() if getattr(self.tool, "accepts_text", False) else event.text().lower()
            self._refresh_vcb()
            return True
        return False
