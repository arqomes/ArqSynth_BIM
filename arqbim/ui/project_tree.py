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

from PySide6 import QtCore, QtWidgets

from ..i18n import t
from . import menus
from .storeys import level_text

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
                      "grids": [], "details": [], "rebars": [], "structure": [], "openings": False}, **(views or {}))
        library = library or {"components": [], "groups": []}
        signature = (spatial, tuple(objects), tuple(views["plans"]), tuple(views["sections"]),
                     tuple((name, tuple(placed)) for name, placed in views["sheets"]),
                     tuple(views["templates"]), tuple(sorted(views["assigned"].items())),
                     tuple(library["components"]), tuple(library["groups"]), tuple(views["views3d"]),
                     tuple(views["grids"]), tuple(views["details"]), tuple(views["rebars"]),
                     tuple(views["structure"]), bool(views["openings"]))
        if signature == self._signature:
            return
        self._signature = signature
        self._sheet_names = [name for name, _placed in views["sheets"]]
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
        if self.search.text().strip():                 # (0.184) still searching: the new list too
            self.filter()
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

    def show_selection(self, ids):
        """Mark what is selected in the 3D view (one element: open its category and show it)."""
        ids = set(ids)
        if ids and ids == self._selected_members():
            return                                    # the items just clicked stand for this selection
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

        for k in range(self.tree.topLevelItemCount()):
            walk(self.tree.topLevelItem(k))

    def focus(self, key):
        """(0.184) The group of `key` opened, shown at the top and chosen: ("views", "sheets") the sheets,
        ("library",) the library (the compact bar's modules)."""
        item = self._items.get(key)
        if item is None:
            return False
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
        if key is not None and key[0] in ("view", "views", "lib", "library", "sheet", "sheetview", "grid"):
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
                         ("view", "rebar_details"), ("view", "openings")):                         # 0.237, 0.293)
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
            menu.addAction(t("sheet.title_block"), lambda: self._later(self.on_sheet, "title_block", key[1]))
            menu.addAction(t("tree.remove_sheet"), lambda: self._later(self.on_sheet, "remove", key[1]))
        elif key[0] == "sheetview":
            if key[4] is not None:
                menu.addAction(t("tree.open_view"), lambda: self._later(self.on_view, key[3], key[4]))
            menu.addAction(t("tree.take_off"), lambda: self._later(self.on_sheet, "take_off", key[1], key[2]))
        else:
            return None
        return menu

    def _menu(self, pos):
        item = self.tree.itemAt(pos)
        key = item.data(0, KEY) if item is not None else None
        menu = self.menu_for(key, item) if key is not None else None
        if menu is not None:
            menu.exec(menus.menu_point(menu, self.tree.viewport().mapToGlobal(pos)))   # (0.377) up at the foot


def dock(parent, beside, below=None):
    """The panel as a tab next to `beside` (the Storeys panel), which stays in front; the
    tabs get more height than before (a tree needs it), the rest goes to `below` (Properties)."""
    panel = ProjectTree(parent)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, panel)
    parent.tabifyDockWidget(beside, panel)
    beside.raise_()
    if below is not None:
        parent.resizeDocks([beside, below], [380, 450], QtCore.Qt.Orientation.Vertical)
    return panel
