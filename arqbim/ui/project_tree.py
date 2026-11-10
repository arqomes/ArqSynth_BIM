"""Project panel ("Projeto"): the spatial tree of the IFC file — project, site,
building, storeys (highest first, as in a section) — and in each storey the
elements by category (Walls, Slabs, Doors…), then the sketches (not IFC).

Click = select in the 3D view (a category, a storey or a building: all of its
elements); double-click = frame them. What is selected in the 3D view is shown
here too. A category's elements are listed only when it is opened, so a model
of 10 000 elements stays quick; the tree is rebuilt only when elements appear,
disappear or change name / storey, not when one changes shape.
"""

import re

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from . import menus, theme
from .storeys import level_text

# (0.524, the owner: «controlos para bloquear edição ou não, ocultar, revelar, renderizar ou não, imprimir ou não… um
# comportamento como no Blender») the columns of icons right of the names, as Blender's Outliner: each a flag of
# model/controls (its icon lit = the flag off: selectable, shown, rendered, printed)
CONTROL_COLUMNS = ("locked", "hidden", "no_render", "no_print")
ICON_SIZE = 16
COLUMN_WIDTH = 22


def _control_pixmap(flag, state):
    """The icon of a column: state False (lit: selectable / shown / rendered / printed), True (dim and crossed — the
    flag on), None (some of a group's elements: half lit)."""
    ratio = 2
    pm = QtGui.QPixmap(ICON_SIZE * ratio, ICON_SIZE * ratio)
    pm.setDevicePixelRatio(ratio)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    # (the owner: «ícones minimalista e leve») thin lines, no fills, a soft grey; off: fainter still
    ink = theme.colour("muted")
    ink.setAlpha(220 if state is False else 140 if state is None else 90)
    pen = QtGui.QPen(ink, 1.0)
    pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    s = ICON_SIZE
    if flag == "locked":
        if state is True:                                   # a padlock, shut
            p.drawRoundedRect(QtCore.QRectF(3.5, 7.5, 9, 6.5), 1.2, 1.2)
            p.drawArc(QtCore.QRectF(5, 2.5, 6, 9), 0, 180 * 16)
        else:                                               # Blender's arrow: it can be picked
            arrow = QtGui.QPolygonF([QtCore.QPointF(*xy) for xy in
                                     ((4, 2), (4, 13), (7, 10.5), (9.2, 14.5), (10.8, 13.7), (8.7, 9.8), (12.3, 9.8))])
            p.drawPolygon(arrow)
    elif flag == "hidden":                                  # an eye (shut: its lid and lashes)
        if state is True:
            path = QtGui.QPainterPath(QtCore.QPointF(2, 7))
            path.quadTo(QtCore.QPointF(8, 12.5), QtCore.QPointF(14, 7))
            p.drawPath(path)
            for x0, x1 in ((4.5, 3.5), (8, 8), (11.5, 12.5)):
                p.drawLine(QtCore.QPointF(x0, 9.6), QtCore.QPointF(x1, 12))
        else:
            path = QtGui.QPainterPath(QtCore.QPointF(1.5, 8))
            path.quadTo(QtCore.QPointF(8, 1), QtCore.QPointF(14.5, 8))
            path.quadTo(QtCore.QPointF(8, 15), QtCore.QPointF(1.5, 8))
            p.drawPath(path)
            p.drawEllipse(QtCore.QPointF(8, 8), 2.0, 2.0)
    elif flag == "no_render":                               # a camera
        p.drawRoundedRect(QtCore.QRectF(2, 5, 12, 8.5), 1.5, 1.5)
        p.drawLine(QtCore.QPointF(5.5, 5), QtCore.QPointF(6.5, 3))
        p.drawLine(QtCore.QPointF(6.5, 3), QtCore.QPointF(9.5, 3))
        p.drawLine(QtCore.QPointF(9.5, 3), QtCore.QPointF(10.5, 5))
        p.drawEllipse(QtCore.QPointF(8, 9.2), 2.4, 2.4)
    else:                                                   # a printer
        p.drawRect(QtCore.QRectF(4.5, 2, 7, 4))
        p.drawRoundedRect(QtCore.QRectF(2, 6, 12, 6), 1.2, 1.2)
        p.drawRect(QtCore.QRectF(4.5, 10, 7, 4.5))
    if state is True and flag != "locked" and flag != "hidden":       # crossed out: not rendered / not printed
        p.setPen(QtGui.QPen(theme.colour("fail"), 1.0))
        p.drawLine(QtCore.QPointF(2, s - 2), QtCore.QPointF(s - 2, 2))
    p.end()
    return pm


_ICONS = {}


def control_icon(flag, state):
    key = (flag, state, theme.C.get("muted"), theme.C.get("fail"))
    if key not in _ICONS:
        _ICONS[key] = QtGui.QIcon(_control_pixmap(flag, state))
    return _ICONS[key]


def controlled(key):
    """Does an item of the tree carry the control icons? The IFC elements, their categories, storeys, buildings."""
    return key is not None and (key[0] == "obj" or (key[0] == "cat" and key[1] != "sketches") or key[0] == "spatial")

KEY = QtCore.Qt.ItemDataRole.UserRole          # what an item stands for (a tuple, see _key)
PLACEABLE = QtCore.Qt.ItemDataRole.UserRole + 1     # a component one can place again (made by ArqBIM)
ELEVATIONS = ("N", "S", "E", "W")
CATEGORIES = ("IfcWall", "IfcCurtainWall", "IfcColumn", "IfcBeam", "IfcFooting", "IfcSlab", "IfcReinforcingBar",
              "IfcRamp", "IfcRoof",
              "IfcStair",
              "IfcRailing", "IfcDoor", "IfcWindow", "IfcCovering", "IfcLightFixture", "IfcFurniture",
              "IfcSanitaryTerminal",
              "IfcPipeSegment", "IfcPipeFitting", "IfcDuctSegment", "IfcDuctFitting", "IfcAirTerminal",
              "IfcUnitaryEquipment", "IfcOutlet", "IfcSwitchingDevice", "IfcElectricDistributionBoard",
              "IfcJunctionBox", "IfcCableCarrierSegment", "IfcCableCarrierFitting", "IfcBuildingElementProxy")          # their order in a storey; others follow by name
# (0.461) the tabs at the panel's foot: what the tree shows — all of it, the views, the library, the model (its spatial
# tree and the sketches) — each the tree's top-level groups whose key starts so
# (0.470, the owner: «Colocar a opção de filtro da folha também no rodapé… deve ficar última aba, já que a ultima
# coisa a ser feita é folha e impressão») the sheets last: their group alone, its sheets at the top of the tree
SCOPES = ("all", "views", "library", "project", "sheets")
SCOPE_ROOTS = {"views": ("views",), "library": ("library",), "project": ("spatial", "cat"), "sheets": ("views",)}
SHEETS = ("views", "sheets")         # the sheets' group (in the views')


def category_label(ifc_class):
    key = "tree.cat." + ifc_class
    try:
        return t(key)
    except KeyError:
        return ifc_class[3:] if ifc_class.startswith("Ifc") else ifc_class


def _row(obj):
    """What the tree lists of a document object."""
    if obj.is_bim:
        return obj.id, obj.name, obj.ifc_class, obj.storey
    return obj.id, obj.name, None, None


def rows(doc):
    return [_row(o) for o in doc.objects.values()]


def _natural(text):
    """Sort key: 'Parede 2' before 'Parede 10'."""
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", text)]


class ProjectTree(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__(t("tree.title"), parent)
        self.setObjectName("project_tree")
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderHidden(True)
        # (0.524) the name, then a column of icons per control (as Blender's Outliner)
        self.tree.setColumnCount(1 + len(CONTROL_COLUMNS))
        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        for c in range(1, 1 + len(CONTROL_COLUMNS)):
            header.setSectionResizeMode(c, QtWidgets.QHeaderView.ResizeMode.Fixed)
            header.resizeSection(c, COLUMN_WIDTH)
        self.tree.setIconSize(QtCore.QSize(ICON_SIZE, ICON_SIZE))
        self.tree.setMouseTracking(True)
        self.tree.viewport().installEventFilter(self)
        self.state_of = None         # (ids, flag) -> True | False | None (some): set by the window (model/controls)
        self.on_control = None       # (ids, flag, on): a control switched — on many rows at once when dragged
        self.on_element = None       # (action, ids, arg): the elements' right-click menu
        self._drag = None            # (column, flag, value, {item keys passed over}) while dragging down a column
        self._storeys = []           # [(GlobalId, name, level)] for "Replicate on storey ▸"
        self.tree.setIndentation(14)                 # project / site / building / storey: keep the names in view
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setToolTip(t("tree.hint"))
        # (0.184, the interface's panel 5) a search over what is listed, above the tree
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText(t("tree.search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.filter)
        box = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(box)
        column.setContentsMargins(4, 4, 4, 0)
        column.setSpacing(4)
        column.addWidget(self.search)
        column.addWidget(self.tree, 1)
        # (0.461, the owner: «no rodapé, vamos colocar outras abas de filtro… Vistas… Biblioteca… Projeto») what the
        # tree shows: all of it, the views only, the library only, the model only
        self.scope = "all"
        self.scope_bar = QtWidgets.QTabBar()
        self.scope_bar.setObjectName("tree_scopes")
        self.scope_bar.setShape(QtWidgets.QTabBar.Shape.RoundedSouth)
        self.scope_bar.setExpanding(True)
        self.scope_bar.setDocumentMode(True)
        self.scope_bar.setDrawBase(False)
        self.scope_bar.setUsesScrollButtons(False)        # (all four in view: a narrow panel shortens their words)
        self.scope_bar.setElideMode(QtCore.Qt.TextElideMode.ElideRight)
        # (0.470: five of them — narrow enough to be read whole in the panel's usual width)
        self.scope_bar.setStyleSheet("QTabBar::tab { padding: 4px 1px; min-width: 0px; }")
        small = self.scope_bar.font()
        if small.pointSizeF() > 0:
            small.setPointSizeF(small.pointSizeF() - 0.5)
            self.scope_bar.setFont(small)
        for k, name in enumerate(SCOPES):
            self.scope_bar.addTab(t("tree.scope." + name))
            self.scope_bar.setTabToolTip(k, t("tip.tree.scope." + name))
        saved = QtCore.QSettings("ArqSynth", "ArqSynth BIM").value("navegador/filtro", "all")
        if saved in SCOPES:                           # (the tab chosen last time)
            self.scope = saved
            self.scope_bar.setCurrentIndex(SCOPES.index(saved))
        self.scope_bar.currentChanged.connect(lambda k: self.set_scope(SCOPES[k]))
        column.addWidget(self.scope_bar)
        self.setWidget(box)

        # callbacks set by the main window
        self.on_select = None        # (ids)
        self.on_frame = None         # (ids)
        self.on_shown = None         # () the panel came into view and is out of date: call show_project
        self.on_view = None          # (kind "plan" | "section" | "elevation" | "3d", storey GlobalId | index | side | uid)
        self.on_view3d = None        # ("rename", uid, name) | ("remove", uid): a named 3D view
        self.on_grid = None          # ("rename", index, tag) | ("remove", index): an axis of the structural grid
        self.on_rename_section = None    # (index, name)
        self.on_remove_section = None    # (index)
        self.on_library = None       # ("select" | "place" | "import", "component" | "group", type GlobalId | group model)
        self.on_sheet = None         # (action, …): see MainWindow.sheet_action
        self.on_template = None      # ("assign", view key, template uid or None) | ("edit", None, None)
        self._building = False
        self._sheet_names = []       # as listed, for "Put on sheet ▸"
        self.set_names_of = None     # () -> the sheet sets' names, for "Publish a set ▸" (set by the window, 0.128)
        self._section_names = []
        self._templates = []         # [(uid, name)] for "View template ▸"
        self._assigned = {}          # view key -> template uid
        self.tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.EditKeyPressed)   # (double-click opens)
        self.tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._menu)
        self.tree.itemChanged.connect(self._renamed)

        self._signature = None       # what the tree shows, to rebuild only when it changes
        self._stale = True           # the document changed while the panel was not in view
        self._listed = {}            # object id -> (name, IFC class, storey) as listed
        self._members = {}           # item key -> [object ids] (storeys, categories, spatial levels)
        self._names = {}             # object id -> name
        self._where = {}             # object id -> category item key
        self._items = {}             # item key -> QTreeWidgetItem
        self._filled = set()         # category keys whose elements are listed
        self._closed = set()         # spatial levels the user closed
        self.tree.itemExpanded.connect(self._fill)
        self.tree.itemClicked.connect(self._clicked)
        self.tree.itemDoubleClicked.connect(self._double_clicked)
        self.visibilityChanged.connect(self._visibility)

    def _visibility(self, shown):
        if shown and self._stale and self.on_shown is not None:
            self.on_shown()

    @staticmethod
    def _later(fn, *args):
        if fn is not None:
            QtCore.QTimer.singleShot(0, lambda: fn(*args))

    # ------------------------------------------------------------ content

    def mark_stale(self):
        self._stale = True

    def wants(self, spatial, changed, removed, get):
        """Does a document change need show_project? Not when the panel is out of view (it
        is brought up to date when shown), nor when the changed objects are listed as they
        are (a wall changed shape) — so editing a big model costs nothing here."""
        if not self.isVisible():
            self._stale = True
            return False
        if changed is None or self._stale or self._signature is None or removed or spatial != self._signature[0]:
            return True
        for obj_id in changed:
            obj = get(obj_id)
            if obj is None:
                if obj_id in self._listed:
                    return True                       # was listed, now gone
            elif self._listed.get(obj_id) != _row(obj)[1:]:
                return True
        return False

    def show_project(self, spatial, objects, views=None, library=None):
        """spatial: IfcModel.spatial_tree(); objects: [row(obj)] = (id, name, IFC class or
        None for a sketch, storey GlobalId or None); views: {"plans": [(GlobalId, name, level)],
        "sections": [names], "sheets": [(name, [(label, kind, ref as for on_view or None)])]}
        (the elevations are always there); library: {"components": [(type GlobalId, name,
        copies, placeable)], "groups": [(model, name, copies)]}. Rebuilt only if something
        listed changed."""
        self._stale = False
        views = dict({"plans": [], "sections": [], "sheets": [], "templates": [], "assigned": {}, "views3d": [],
                      "grids": [], "details": [], "rebars": [], "structure": [], "openings": False, "steel": False},
                     **(views or {}))
        library = library or {"components": [], "groups": []}
        signature = (spatial, tuple(objects), tuple(views["plans"]), tuple(views["sections"]),
                     tuple((name, tuple(placed)) for name, placed in views["sheets"]),
                     tuple(views["templates"]), tuple(sorted(views["assigned"].items())),
                     tuple(library["components"]), tuple(library["groups"]), tuple(views["views3d"]),
                     tuple(views["grids"]), tuple(views["details"]), tuple(views["rebars"]),
                     tuple(views["structure"]), bool(views["openings"]), bool(views["steel"]))
        if signature == self._signature:
            return
        self._signature = signature
        self._sheet_names = [name for name, _placed in views["sheets"]]
        self._storeys = list(views["plans"])
        self._section_names = list(views["sections"])
        self._templates = list(views["templates"])                 # [(uid, name)]
        self._assigned = dict(views["assigned"])                    # view key -> template uid
        names = dict(views["templates"])

        def with_template(text, view):
            uid = self._assigned.get(view)
            return "{}   · {}".format(text, names[uid]) if uid in names else text
        self._listed = {row[0]: row[1:] for row in objects}
        # what the user opened or closed stays so (spatial levels and views are open unless closed by hand)
        folds = ("spatial", "views", "library", "sheet")
        self._closed |= {k for k, item in self._items.items() if k[0] in folds and not item.isExpanded()}
        self._closed -= {k for k, item in self._items.items() if k[0] in folds and item.isExpanded()}
        opened = {k for k, item in self._items.items() if k[0] == "cat" and item.isExpanded()}
        self._building = True
        self.tree.clear()
        self._members, self._names, self._where, self._items, self._filled = {}, {}, {}, {}, set()

        by_storey = {}
        sketches = []
        for obj_id, name, ifc_class, storey in objects:
            self._names[obj_id] = name
            if ifc_class is None:
                sketches.append(obj_id)
            else:
                by_storey.setdefault(storey, {}).setdefault(ifc_class, []).append(obj_id)
        storeys = set()

        def add(parent, key, text, members, lazy=False):
            item = QtWidgets.QTreeWidgetItem([text])
            item.setData(0, KEY, key)
            if lazy:
                item.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
            (parent.addChild if parent is not None else self.tree.addTopLevelItem)(item)
            self._items[key] = item
            self._members[key] = members
            return item

        def add_storey_content(parent, storey):
            members = []
            classes = by_storey.get(storey, {})
            order = sorted(classes, key=lambda c: (CATEGORIES.index(c) if c in CATEGORIES else len(CATEGORIES),
                                                   category_label(c)))
            for cls in order:
                ids = sorted(classes[cls], key=lambda i: _natural(self._names[i]))
                key = ("cat", storey, cls)
                add(parent, key, "{} ({})".format(category_label(cls), len(ids)), ids, lazy=True)
                for i in ids:
                    self._where[i] = key
                members += ids
            return members

        def add_spatial(parent, node):
            guid, ifc_class, name, level, children = node
            key = ("spatial", guid)
            if ifc_class == "IfcBuildingStorey":
                storeys.add(guid)
                item = add(parent, key, "", [])
                members = add_storey_content(item, guid)
                item.setText(0, "{}   {}   ({})".format(name or ifc_class, level_text(level or 0.0), len(members)))
            else:
                item = add(parent, key, name or category_label(ifc_class), [])
                members = []
                for child in children:
                    members += add_spatial(item, child)
            self._members[key] = members
            return members

        # the views first: plans (one per storey, highest first), named sections, the four elevations
        root = add(None, ("views",), t("tree.views"), [])
        plans = add(root, ("views", "plans"), t("tree.plans"), [])
        for guid, name, level in reversed(views["plans"]):
            add(plans, ("view", "plan", guid), with_template("{}   {}".format(name, level_text(level)), ("plan", guid)),
                [])
        sections = add(root, ("views", "sections"), "{} ({})".format(t("tree.sections"), len(views["sections"])), [])
        for k, name in enumerate(views["sections"]):
            item = add(sections, ("view", "section", k), name, [])
            if ("section", name) in self._assigned:
                item.setToolTip(0, with_template("", ("section", name)).strip(" ·"))
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)     # F2: a new name
        elevations = add(root, ("views", "elevations"), t("tree.elevations"), [])
        for side in ELEVATIONS:
            add(elevations, ("view", "elevation", side), with_template(t("tree.elevation." + side), ("elevation", side)),
                [])
        if views["openings"]:                                                 # (the mapa de vãos, 0.293)
            add(root, ("view", "openings", ""), t("tree.openings"), [])
        if views["steel"]:                                                    # (0.502: the steel pieces' drawing)
            add(root, ("view", "steel_parts", ""), t("tree.steel_parts"), [])
            add(root, ("view", "steel_assemblies", ""), t("tree.steel_assemblies"), [])   # (0.515)
            add(root, ("view", "steel_erection", ""), t("tree.steel_erection"), [])     # (0.510)
        if views["details"]:                                                  # (the detail views, 0.133)
            details = add(root, ("views", "details"), "{} ({})".format(t("tree.details"), len(views["details"])), [])
            for uid, name in views["details"]:
                add(details, ("view", "detail", uid), name, [])
        if views["structure"]:                                                # (the structure plans, 0.168)
            plans_s = add(root, ("views", "structure"), "{} ({})".format(t("tree.structure"),
                                                                        len(views["structure"])), [])
            for guid, name in views["structure"]:
                add(plans_s, ("view", "structure", guid), name, [])
                add(plans_s, ("view", "structure_below", guid), t("tree.structure_below", name=name), [])  # (0.235)
        if views["rebars"]:                                                   # (the reinforcement drawings, 0.168)
            rebars = add(root, ("views", "rebars"), "{} ({})".format(t("tree.rebars"), len(views["rebars"])), [])
            add(rebars, ("view", "rebar_details", ""), t("tree.rebar_details"), [])        # (0.237: the project's)
            for guid, name in views["rebars"]:
                add(rebars, ("view", "rebar", guid), name, [])
        # the 3D views (0.64): the 3D view, and those kept under a name (each its camera, look and box)
        views3d = add(root, ("views", "3d"), "{} ({})".format(t("tree.views3d"), 1 + len(views["views3d"])), [])
        add(views3d, ("view", "3d", None), t("tab.3d"), [])
        for uid, name in views["views3d"]:
            item = add(views3d, ("view", "3d", uid), name, [])
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)     # F2: a new name
        # the structural grid's axes (0.67)
        grid = add(root, ("views", "grid"), "{} ({})".format(t("tree.grid"), len(views["grids"])), [])
        for k, tag in enumerate(views["grids"]):
            item = add(grid, ("grid", k), tag, [])
            item.setToolTip(0, t("tree.grid_axis", tag=tag))
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)     # F2: another tag
        # the sheets: several views on paper, each listed with its views
        sheets = add(root, ("views", "sheets"), "{} ({})".format(t("tree.sheets"), len(views["sheets"])), [])
        for k, (name, placed) in enumerate(views["sheets"]):
            item = add(sheets, ("sheet", k), name, [])
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)     # F2: a new name
            for j, (label, kind, ref) in enumerate(placed):
                add(item, ("sheetview", k, j, kind, ref), label, [])
        # the library: components (one shape, many copies) and groups (apartments, bathrooms…)
        lib = add(None, ("library",), t("tree.library"), [])
        comps = add(lib, ("library", "components"), "{} ({})".format(t("tree.components"),
                                                                     len(library["components"])), [])
        for guid, name, copies, placeable in library["components"]:
            item = add(comps, ("lib", "component", guid), t("tree.copies", name=name, n=copies), [])
            item.setData(0, PLACEABLE, placeable)
        groups = add(lib, ("library", "groups"), "{} ({})".format(t("tree.groups"), len(library["groups"])), [])
        for model, name, copies in library["groups"]:
            add(groups, ("lib", "group", model), t("tree.copies", name=name, n=copies), [])

        if spatial is not None:
            add_spatial(None, spatial)
        loose = [s for s in by_storey if s not in storeys]       # elements in no (known) storey
        if loose:
            item = add(None, ("spatial", None), "", [])
            members = []
            for s in loose:
                members += add_storey_content(item, s)
            item.setText(0, "{} ({})".format(t("tree.no_storey"), len(members)))
            self._members[("spatial", None)] = members
        if sketches:
            ids = sorted(sketches, key=lambda i: _natural(self._names[i]))
            key = ("cat", "sketches", None)
            add(None, key, "{} ({})".format(t("tree.sketches"), len(ids)), ids, lazy=True)
            for i in ids:
                self._where[i] = key

        for key, item in list(self._items.items()):    # (opening a category adds its elements)
            if (key[0] in folds and key not in self._closed) or key in opened:
                item.setExpanded(True)
        self.filter()                                  # (0.184: still searching — 0.461: the tab chosen — the new list too)
        self.refresh_controls()
        self._building = False

    def _fill(self, item):
        """List a category's elements, the first time it is opened."""
        key = item.data(0, KEY)
        if key[0] != "cat" or key in self._filled:
            return
        self._filled.add(key)
        for obj_id in self._members[key]:
            child = QtWidgets.QTreeWidgetItem([self._names[obj_id]])
            child.setData(0, KEY, ("obj", obj_id))
            item.addChild(child)
            self._items[("obj", obj_id)] = child
            self._paint_controls(child)

    # ------------------------------------------------------------ controls (0.524)

    def _ifc_members(self, item):
        return [i for i in self._members_of(item) if isinstance(i, str)]

    def _paint_controls(self, item, preview=None):
        """The icons of an item's columns from its elements' flags (preview: {flag: state} shown while dragging)."""
        key = item.data(0, KEY)
        if not controlled(key) or self.state_of is None:
            return
        ids = self._ifc_members(item)
        if not ids:
            return
        for c, flag in enumerate(CONTROL_COLUMNS, start=1):
            state = preview[flag] if preview and flag in preview else self.state_of(ids, flag)
            item.setIcon(c, control_icon(flag, state))
            item.setToolTip(c, t("tree.col." + flag))

    def refresh_controls(self):
        """Every item's icons again (a flag changed — an undo, a file opened)."""
        building, self._building = self._building, True
        try:
            for key, item in self._items.items():
                if controlled(key):
                    self._paint_controls(item)
        finally:
            self._building = building

    def _control_at(self, pos):
        """(item, column, flag) under a point of the tree's viewport, if it is a control's icon."""
        item = self.tree.itemAt(pos)
        if item is None or not controlled(item.data(0, KEY)) or not self._ifc_members(item):
            return None
        column = self.tree.columnAt(pos.x())
        if not 1 <= column <= len(CONTROL_COLUMNS):
            return None
        return item, column, CONTROL_COLUMNS[column - 1]

    def eventFilter(self, obj, event):  # noqa: N802
        """(0.524) As Blender's Outliner: a click on an icon switches it; dragged down (or up) the column, the same
        state on every row the mouse runs over — applied in one undo step when the button is let go."""
        if getattr(self, "state_of", None) is None or obj is not self.tree.viewport():
            return False
        kind = event.type()
        if kind == QtCore.QEvent.Type.MouseButtonPress and event.button() == QtCore.Qt.MouseButton.LeftButton:
            found = self._control_at(event.position().toPoint())
            if found is None:
                return False
            item, column, flag = found
            value = self.state_of(self._ifc_members(item), flag) is not True       # off (or some) -> on, on -> off
            self._drag = (column, flag, value, {})
            self._drag_over(item)
            return True
        if kind == QtCore.QEvent.Type.MouseButtonDblClick and self._control_at(event.position().toPoint()):
            return True                                # (a quick second click: not the row's double-click)
        if kind == QtCore.QEvent.Type.MouseMove and self._drag is not None:
            column = self._drag[0]
            x = self.tree.header().sectionViewportPosition(column) + COLUMN_WIDTH // 2
            item = self.tree.itemAt(QtCore.QPoint(x, int(event.position().y())))
            if item is not None and controlled(item.data(0, KEY)) and self._ifc_members(item):
                self._drag_over(item)
            return True
        if kind == QtCore.QEvent.Type.MouseButtonRelease and self._drag is not None:
            self.finish_drag()
            return True
        return False

    def _drag_over(self, item):
        _column, flag, value, passed = self._drag
        key = item.data(0, KEY)
        if key in passed:
            return
        passed[key] = item
        self._paint_controls(item, {flag: value})

    def finish_drag(self):
        """The drag's state put on every row passed over (one undo step)."""
        if self._drag is None:
            return []
        _column, flag, value, passed = self._drag
        self._drag = None
        ids = []
        for item in passed.values():
            for i in self._ifc_members(item):
                if i not in ids:
                    ids.append(i)
        if ids and self.on_control is not None:
            self.on_control(ids, flag, value)
        self.refresh_controls()
        return ids

    def press_control(self, key, flag):
        """A click on an item's icon (used by tests): as the mouse would."""
        item = self._items.get(key)
        if item is None:
            return
        self._drag = (1 + CONTROL_COLUMNS.index(flag), flag, self.state_of(self._ifc_members(item), flag) is not True, {})
        self._drag_over(item)

    def drag_control_over(self, key):
        item = self._items.get(key)
        if item is not None and self._drag is not None:
            self._drag_over(item)

    def show_selection(self, ids):
        """Mark what is selected in the 3D view (one element: open its category and show it)."""
        ids = set(ids)
        chosen = self._selected_members()
        if ids and ids == chosen:
            return                                    # the items just clicked stand for this selection
        if chosen and ids <= chosen and self.state_of is not None and \
                self.state_of([i for i in chosen - ids if isinstance(i, str)], "locked") is True:
            return                                    # (0.524) the rows clicked, but those locked not picked in the view
        self.tree.blockSignals(True)
        try:
            self.tree.clearSelection()
            if len(ids) == 1:
                where = self._where.get(next(iter(ids)))
                if where is not None:
                    cat = self._items[where]
                    self._fill(cat)
                    parent = cat
                    while parent is not None:
                        parent.setExpanded(True)
                        parent = parent.parent()
            for obj_id in ids:
                item = self._items.get(("obj", obj_id))
                if item is not None:
                    item.setSelected(True)
                    if len(ids) == 1:
                        self.tree.setCurrentItem(item, 0, QtCore.QItemSelectionModel.SelectionFlag.NoUpdate)
                        self.tree.scrollToItem(item)
        finally:
            self.tree.blockSignals(False)

    def _members_of(self, item):
        key = item.data(0, KEY)
        if key is None:
            return []
        if key[0] == "obj":
            return [key[1]]
        return list(self._members.get(key, []))

    def _selected_members(self):
        ids = set()
        for item in self.tree.selectedItems():
            ids.update(self._members_of(item))
        return ids

    def filter(self, text=None):
        """(0.184) Only the items whose name has `text` (any case), with the groups they are in — every one again
        when it is empty. The categories not opened yet are searched by their names only."""
        text = (self.search.text() if text is None else text).strip().lower()

        def walk(item):
            own = not text or text in item.text(0).lower()
            shown = False
            for k in range(item.childCount()):
                shown = walk(item.child(k)) or shown
            item.setHidden(not (own or shown))
            if text and shown:
                item.setExpanded(True)
            return own or shown

        sheets = self._items.get(SHEETS)
        if self.scope == "sheets" and sheets is not None:   # (0.470: the sheets' group as the tree's top)
            walk(sheets)
            sheets.setHidden(False)
            sheets.setExpanded(True)
            if self.tree.rootIndex() != self.tree.indexFromItem(sheets):
                self.tree.setRootIndex(self.tree.indexFromItem(sheets))
            return
        if self.tree.rootIndex().isValid():
            self.tree.setRootIndex(QtCore.QModelIndex())
        for k in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(k)
            if self.in_scope(item.data(0, KEY)):
                walk(item)
            else:
                item.setHidden(True)                  # (0.461: another tab's)

    def in_scope(self, key):
        """(0.461) Is a group of the tree (its key) in the tab chosen at the panel's foot? (0.470) The sheets' tab:
        their group and what is in it."""
        if self.scope == "sheets":
            return key is not None and (key[:2] == SHEETS or key[0] in ("sheet", "sheetview"))
        roots = SCOPE_ROOTS.get(self.scope)
        return roots is None or (key is not None and key[0] in roots)

    def set_scope(self, scope):
        """(0.461) The tab at the panel's foot: what the tree shows — "all", "views", "library" or "project" (the
        model: its spatial tree and the sketches) — (0.470) or "sheets" (their group alone, last: the last thing
        done); the one chosen kept for the next session."""
        if scope not in SCOPES:
            return
        self.scope = scope
        k = SCOPES.index(scope)
        if self.scope_bar.currentIndex() != k:
            self.scope_bar.blockSignals(True)
            self.scope_bar.setCurrentIndex(k)
            self.scope_bar.blockSignals(False)
        self.filter()
        for key in ([("views",)] if scope == "views" else [("library",)] if scope == "library" else []):
            item = self._items.get(key)
            if item is not None:
                item.setExpanded(True)
        QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue("navegador/filtro", scope)

    def focus(self, key):
        """(0.184) The group of `key` opened, shown at the top and chosen: ("views", "sheets") the sheets,
        ("library",) the library (the compact bar's modules)."""
        item = self._items.get(key)
        if item is None:
            return False
        if not self.in_scope(key):                    # (0.461: its tab chosen — the library's, the views')
            self.set_scope("sheets" if key[:2] == SHEETS or key[0] in ("sheet", "sheetview") else    # (0.470)
                           next((s for s, roots in SCOPE_ROOTS.items() if key[0] in roots), "all"))
        parent = item
        while parent is not None:
            parent.setExpanded(True)
            parent = parent.parent()
        self.tree.setCurrentItem(item)
        self.tree.scrollToItem(item, QtWidgets.QAbstractItemView.ScrollHint.PositionAtTop)
        return True

    def item_for(self, key):
        """The item standing for `key` (used by tests): ('spatial', guid), ('cat', storey, class)
        or ('obj', id); a category's elements exist once it has been opened."""
        return self._items.get(key)

    def text(self):
        """The open part of the tree as indented lines (used by tests)."""
        lines = []

        def walk(item, depth):
            lines.append("  " * depth + item.text(0))
            if item.isExpanded():
                for k in range(item.childCount()):
                    walk(item.child(k), depth + 1)

        for k in range(self.tree.topLevelItemCount()):
            walk(self.tree.topLevelItem(k), 0)
        return "\n".join(lines)

    # ------------------------------------------------------------ user actions

    def _clicked(self, item, _column):
        key = item.data(0, KEY)
        if key is not None and key[0] == "sheet":    # (0.470) a sheet: its properties (Revit's), opened on a double one
            self._later(self.on_sheet, "props", key[1])
            return
        if key is not None and key[0] in ("view", "views", "lib", "library", "sheetview", "grid"):
            return                                    # views and the library work with a double-click
        self._later(self.on_select, sorted(self._selected_members() or set(self._members_of(item)), key=str))

    def _double_clicked(self, item, _column):
        key = item.data(0, KEY)
        if key is not None and key[0] == "view":
            self._later(self.on_view, key[1], key[2])
            return
        if key is not None and key[0] == "sheet":
            self._later(self.on_sheet, "open", key[1])
            return
        if key is not None and key[0] == "sheetview":
            if key[4] is not None:
                self._later(self.on_view, key[3], key[4])                 # the view itself, in 3D
            return
        if key is not None and key[0] == "lib":
            self._later(self.on_library, "select", key[1], key[2])        # every copy
            return
        if key is not None and key[0] in ("views", "library", "grid"):
            return
        ids = self._members_of(item)
        self._later(self.on_select, ids)
        self._later(self.on_frame, ids)

    def _renamed(self, item, _column):
        key = item.data(0, KEY)
        if self._building or key is None:
            return
        if key[:2] == ("view", "section"):
            self._later(self.on_rename_section, key[2], item.text(0))
        elif key[:2] == ("view", "3d") and key[2]:
            self._later(self.on_view3d, "rename", key[2], item.text(0))
        elif key[0] == "grid":
            self._later(self.on_grid, "rename", key[1], item.text(0))
        elif key[0] == "sheet":
            self._later(self.on_sheet, "rename", key[1], item.text(0))

    def sheet_ref(self, kind, ref):
        """A view's reference as a sheet keeps it (a section by its name, not its place in the list)."""
        if kind == "section":
            return self._section_names[ref] if 0 <= ref < len(self._section_names) else None
        return ref

    def menu_for(self, key, item=None):
        """The right-click menu of an item (None: it has none)."""
        menu = QtWidgets.QMenu(self)
        if key[0] == "lib":
            menu.addAction(t("tree.select_copies"), lambda: self._later(self.on_library, "select", key[1], key[2]))
            if key[1] == "component" and item is not None and item.data(0, PLACEABLE):
                menu.addAction(t("tree.place"), lambda: self._later(self.on_library, "place", key[1], key[2]))
        elif key[:2] == ("view", "3d"):
            menu.addAction(t("tree.open_view"), lambda: self._later(self.on_view, key[1], key[2]))
            if key[2]:
                menu.addAction(t("tree.rename"), lambda: self.tree.editItem(item, 0))
                menu.addAction(t("tree.remove_view3d"), lambda: self._later(self.on_view3d, "remove", key[2]))
            put = menu.addMenu(t("tree.put_on_sheet"))                     # (in lines, 0.134)
            for k, name in enumerate(self._sheet_names):
                put.addAction(name, lambda k=k: self._later(self.on_sheet, "put", k, "3d", key[2] or ""))
            put.addSeparator()
            put.addAction(t("tree.new_sheet"), lambda: self._later(self.on_sheet, "put", None, "3d", key[2] or ""))
        elif key == ("views", "3d"):
            menu.addAction(t("act.view3d_new"), lambda: self._later(self.on_view3d, "new", None))
        elif key[0] == "grid":
            menu.addAction(t("tree.rename"), lambda: self.tree.editItem(item, 0))
            menu.addAction(t("tree.remove_grid_axis"), lambda: self._later(self.on_grid, "remove", key[1]))
        elif key[:2] in (("view", "rebar"), ("view", "structure"), ("view", "structure_below"),    # (0.168, 0.235,
                         ("view", "rebar_details"), ("view", "openings"),                          # 0.237, 0.293)
                         ("view", "steel_parts"), ("view", "steel_erection"),                      # (0.502, 0.510,
                         ("view", "steel_assemblies")):                                            # 0.515)
            put = menu.addMenu(t("tree.put_on_sheet"))
            for k, name in enumerate(self._sheet_names):
                put.addAction(name, lambda k=k: self._later(self.on_sheet, "put", k, key[1], key[2]))
            put.addSeparator()
            put.addAction(t("tree.new_sheet"), lambda: self._later(self.on_sheet, "put", None, key[1], key[2]))
        elif key[:2] == ("view", "detail"):                                                   # (0.133)
            put = menu.addMenu(t("tree.put_on_sheet"))
            for k, name in enumerate(self._sheet_names):
                put.addAction(name, lambda k=k: self._later(self.on_sheet, "put", k, "detail", key[2]))
            put.addSeparator()
            put.addAction(t("tree.new_sheet"), lambda: self._later(self.on_sheet, "put", None, "detail", key[2]))
            menu.addAction(t("tree.remove_detail"), lambda: self._later(self.on_sheet, "remove_detail", key[2]))
        elif key[0] == "view":
            menu.addAction(t("tree.open_view"), lambda: self._later(self.on_view, key[1], key[2]))
            if key[1] == "section":
                menu.addAction(t("tree.rename"), lambda: self.tree.editItem(item, 0))
                menu.addAction(t("tree.remove_section"), lambda: self._later(self.on_remove_section, key[2]))
            ref = self.sheet_ref(key[1], key[2])
            put = menu.addMenu(t("tree.put_on_sheet"))
            for k, name in enumerate(self._sheet_names):
                put.addAction(name, lambda k=k: self._later(self.on_sheet, "put", k, key[1], ref))
            put.addSeparator()
            put.addAction(t("tree.new_sheet"), lambda: self._later(self.on_sheet, "put", None, key[1], ref))
            view = (key[1], ref)
            sub = menu.addMenu(t("tree.template"))
            current = self._assigned.get(view)
            for uid, name in [(None, t("tree.no_template"))] + list(self._templates):
                act = sub.addAction(name, lambda uid=uid: self._later(self.on_template, "assign", view, uid))
                act.setCheckable(True)
                act.setChecked(uid == current)
            sub.addSeparator()
            sub.addAction(t("act.templates"), lambda: self._later(self.on_template, "edit", None, None))
        elif key == ("views",):
            menu.addAction(t("act.templates"), lambda: self._later(self.on_template, "edit", None, None))
        elif key in (("library",), ("library", "components")):
            menu.addAction(t("tree.import"), lambda: self._later(self.on_library, "import", None, None))
        elif key == ("views", "sheets"):
            menu.addAction(t("tree.new_sheet"), lambda: self._later(self.on_sheet, "new"))
            menu.addAction(t("act.sheets_by_storey"), lambda: self._later(self.on_sheet, "by_storey"))   # (0.127)
            if self._sheet_names:
                menu.addAction(t("tree.export_sheets"), lambda: self._later(self.on_sheet, "export_all"))
                for fmt in ("png", "svg"):                                                           # (0.128)
                    menu.addAction(t("tree.export_sheets_" + fmt),
                                   lambda f=fmt: self._later(self.on_sheet, "export_" + f, None))
                menu.addAction(t("tree.print_sheets"), lambda: self._later(self.on_sheet, "print", None))
                names = self.set_names_of() if self.set_names_of is not None else []
                if names:
                    publish = menu.addMenu(t("tree.publish_set"))
                    for name in names:
                        publish.addAction(name, lambda n=name: self._later(self.on_sheet, "publish", n))
            menu.addAction(t("sheet.title_block"), lambda: self._later(self.on_sheet, "title_block", None))
        elif key[0] == "sheet":
            menu.addAction(t("tree.open_sheet"), lambda: self._later(self.on_sheet, "open", key[1]))
            menu.addAction(t("tree.export_sheet"), lambda: self._later(self.on_sheet, "export", key[1]))
            for fmt in ("png", "svg"):                                                               # (0.128)
                menu.addAction(t("tree.export_sheet_" + fmt),
                               lambda f=fmt: self._later(self.on_sheet, "export_" + f, key[1]))
            menu.addAction(t("tree.print_sheet"), lambda: self._later(self.on_sheet, "print", key[1]))
            menu.addAction(t("tree.sheet_sets"), lambda: self._later(self.on_sheet, "sets", key[1]))
            menu.addAction(t("tree.rename"), lambda: self.tree.editItem(item, 0))
            menu.addAction(t("props.edit_type"), lambda: self._later(self.on_sheet, "edit_type", key[1]))   # (0.470)
            menu.addAction(t("tree.remove_sheet"), lambda: self._later(self.on_sheet, "remove", key[1]))
        elif key[0] == "sheetview":
            if key[4] is not None:
                menu.addAction(t("tree.open_view"), lambda: self._later(self.on_view, key[3], key[4]))
            menu.addAction(t("tree.take_off"), lambda: self._later(self.on_sheet, "take_off", key[1], key[2]))
        elif controlled(key) and item is not None and self._ifc_members(item):
            self._element_menu(menu, item)
        else:
            return None
        return menu

    def menu_ids(self, item):
        """The elements a right-click works on: the selected rows' if the row is one of them (Shift / Ctrl), its own
        otherwise."""
        if item.isSelected():
            ids = []
            for it in self.tree.selectedItems():
                ids += [i for i in self._ifc_members(it) if i not in ids]
            return ids
        return self._ifc_members(item)

    def _element_menu(self, menu, item):
        """(0.524) An element's / group's / category's menu: the program's own commands on them."""
        ids = self.menu_ids(item)

        def act(text, action, arg=None):
            return menu.addAction(text, lambda: self._later(self.on_element, action, list(ids), arg))

        if item.data(0, KEY)[0] == "obj" and len(ids) == 1:
            act(t("tree.el.edit_type"), "edit_type")
        act(t("tree.el.copy"), "copy")
        act(t("tree.el.duplicate"), "duplicate")
        put = menu.addMenu(t("tree.el.replicate"))
        for guid, name, level in reversed(self._storeys):
            put.addAction("{}   {}".format(name, level_text(level)),
                          lambda g=guid: self._later(self.on_element, "replicate", list(ids), g))
        put.setEnabled(bool(self._storeys))
        act(t("tree.el.delete"), "delete")
        menu.addSeparator()
        act(t("tree.el.isolate"), "isolate").setShortcut(QtGui.QKeySequence("Shift+H"))        # (0.525: shown)
        act(t("tree.el.show_all"), "show_all").setShortcut(QtGui.QKeySequence("Alt+H"))
        state = (lambda flag: self.state_of(ids, flag)) if self.state_of is not None else (lambda flag: False)
        for flag, off, on in (("hidden", "tree.el.hide", "tree.el.reveal"), ("locked", "tree.el.lock", "tree.el.unlock"),
                              ("no_render", "tree.el.render_off", "tree.el.render_on"),
                              ("no_print", "tree.el.print_off", "tree.el.print_on")):
            switched = state(flag) is True
            a = menu.addAction(control_icon(flag, not switched), t(on if switched else off),
                               lambda f=flag, v=not switched: self._later(self.on_control, list(ids), f, v))
            a.setObjectName("tree_control_" + flag)

    def _menu(self, pos):
        item = self.tree.itemAt(pos)
        if item is None and self.scope == "sheets":     # (0.470: the sheets' tab — its group's menu, under them too)
            item = self._items.get(SHEETS)
        key = item.data(0, KEY) if item is not None else None
        menu = self.menu_for(key, item) if key is not None else None
        if menu is not None:
            menu.exec(menus.menu_point(menu, self.tree.viewport().mapToGlobal(pos)))   # (0.377) up at the foot


def dock(parent, beside, below=None):
    """The panel beside `beside` (the Storeys panel) — (0.461) not as a tab with it: the window puts the left panels in
    view one at a time (MainWindow._build_modules); a tab group made here left its tabs' bar behind, over the view."""
    panel = ProjectTree(parent)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, panel)
    if below is not None:
        parent.resizeDocks([beside, below], [380, 450], QtCore.Qt.Orientation.Vertical)
    return panel
