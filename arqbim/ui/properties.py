"""Properties panel: what the selected object is, in BIM terms, and its editable
parameters (name, type, sizes, door/window position, Pset values). With nothing
selected, the view shown: its name, its view template and what it shows (0.59).

Edits are reported through `on_edit(action, guid, value)` (for the view: its key in
place of guid); the main window turns them into undoable commands. Quantities (Qto)
are computed, so read-only.
"""

import math
import os
import textwrap

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..core import curves
from ..core import joinery as core_joinery
from ..core import slabs as core_slabs
from ..core.classify import upright_box
from ..core.units import format_angle, format_length, format_slope, parse_angle, parse_length, parse_lengths
from ..i18n import decimal_sep, has, lang, t
from ..ifc import catalog
from ..ifc.edit import VARIANTS
from ..model import element_types
from ..model import graphic_rules as rules_model
from ..model import sheets as sheets_model
from ..model import view_styles as view_styles_model
from ..model.view_templates import DETAILS, PHASE_FILTERS
from . import theme, type_thumbs

_LENGTH_KEYS = {"Length", "Height", "Width", "Depth", "Perimeter"}
_INTERNAL_PSETS = {"ArqSynth_Parametros", "ArqBIM_Parametros"}     # (the program's own; the old name too)


MAX_LINE_ROWS = 12          # a line of more segments lists the first ones


def _len(m):
    return format_length(m, decimal_sep())


def _int_or_none(s):
    try:
        return int(round(float(str(s).strip().replace(",", "."))))
    except ValueError:
        return None


def _float_or_none(s):
    try:
        return float(str(s).strip().replace(",", "."))
    except ValueError:
        return None


def _coord(c):
    """A coordinate as it is typed: "1,2" (metres, to the millimetre)."""
    c = 0.0 if abs(float(c)) < 5e-4 else float(c)
    return "{:.3f}".format(c).rstrip("0").rstrip(".").replace(".", decimal_sep())


def _point(p):
    """A point as it is typed: "1,2; 3; 0"."""
    return "; ".join(_coord(c) for c in p)


def _parse_span(text):
    """ "from; to" (metres), the first below the second -> (from, to), or None."""
    values = parse_lengths(text, 2)
    if values is None or None in values or values[0] >= values[1]:
        return None
    return float(values[0]), float(values[1])


def _parse_point(text):
    values = parse_lengths(text, 3)
    if values is None or any(v is None for v in values):
        return None
    return np.array(values, dtype=float)


def _parse_plan_point(text):
    """A point on the plan: "x; y" (metres)."""
    values = parse_lengths(text, 2)
    if values is None or any(v is None for v in values):
        return None
    return float(values[0]), float(values[1])


def _cm(m):
    return "{:.1f} cm".format(m * 100).replace(".", decimal_sep())


def _value(key, value, unit_scale):
    if isinstance(value, bool):
        return ("Sim" if value else "Não") if lang() == "pt" else ("Yes" if value else "No")
    if isinstance(value, (int, float)):
        if key in _LENGTH_KEYS:
            return _len(value * unit_scale)
        if "Area" in key:
            return "{:.2f} m²".format(value).replace(".", decimal_sep())
        if "Volume" in key:
            return "{:.3f} m³".format(value).replace(".", decimal_sep())
    return str(value)


def _type_name(spec):
    return spec.name_pt if lang() == "pt" else spec.name_en


GROUP = QtCore.Qt.ItemDataRole.UserRole + 7     # (0.185) a group's row (left out when nothing went in it)
# (0.396) an element's groups in this order (Revit's: what is edited first, who it is after), whatever order made in
GROUP_ORDER = ("props.g.parameters", "props.g.materials", "props.g.identity", "props.g.phase", "props.g.ifc")
DIVIDER_DEFAULT, DIVIDER_LEAST, DIVIDER_MOST = 0.5, 0.25, 0.75   # the names' column: its share of the panel at most
GROUP_EXTRA = 8                 # (0.414) px more for a group's title (a band of its own)
SUB = QtCore.Qt.ItemDataRole.UserRole + 8       # (0.414) a subgroup's row (Forma, Nervuras…): a lighter band


class _WrapDelegate(QtWidgets.QStyledItemDelegate):
    """(0.396) A row as tall as its name or its value needs in its column's width (Qt's tree wraps the words but
    keeps every row one line tall, cutting them «…»): two lines for a long name, never cut."""

    def sizeHint(self, option, index):
        base = super().sizeHint(option, index)
        view = self.parent()
        text = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        if isinstance(view, QtWidgets.QTreeView) and index.sibling(index.row(), 0).data(GROUP):
            return QtCore.QSize(base.width(), base.height() + GROUP_EXTRA)      # (0.414) a group's title: taller
        if not text or not isinstance(view, QtWidgets.QTreeView) or view.isFirstColumnSpanned(index.row(),
                                                                                              index.parent()):
            return base
        width = view.columnWidth(index.column()) - 10
        if index.column() == 0:
            depth, up = 1 if view.rootIsDecorated() else 0, index.parent()
            while up.isValid():
                depth, up = depth + 1, up.parent()
            width -= depth * view.indentation()
        if width < 30:
            return base
        font = index.data(QtCore.Qt.ItemDataRole.FontRole) or option.font
        rect = QtGui.QFontMetrics(font).boundingRect(QtCore.QRect(0, 0, width, 10000),
                                                     int(QtCore.Qt.TextFlag.TextWordWrap), str(text))
        return QtCore.QSize(base.width(), max(base.height(), rect.height() + 4))


class _Editors(dict):
    """action -> its editor; (0.187) every editor made also listed with its action (several share one: "pset")."""

    def __init__(self):
        super().__init__()
        self.made = []

    def __setitem__(self, action, widget):
        super().__setitem__(action, widget)
        self.made.append((action, widget))
# (0.185) the header's icon: an element's kind (or IFC class) -> the tool that draws it
_KIND_ICONS = {"curved_wall": "wall", "pile": "footing", "cladding": "wall_finish", "fitting": "pipe",
               "space": "room", "sketch": "rectangle", "IfcWall": "wall", "IfcSlab": "slab", "IfcColumn": "column",
               "IfcBeam": "beam", "IfcDoor": "door", "IfcWindow": "window", "IfcRoof": "roof", "IfcStair": "stair",
               "IfcRailing": "railing", "IfcCovering": "wall_finish", "IfcFurniture": "cabinet",
               "IfcPipeSegment": "pipe", "IfcDuctSegment": "duct", "view_3d": "orbit", "view_section": "section",
               "view_elevation": "section", "view_detail": "detail"}


def _kind_icon(kind):
    """The icon of what is shown on top of the panel (an element's kind, a view's, a sketch), or None."""
    from . import icons
    if kind == "view_plan":
        return icons.plan_view_icon()
    make = icons.TOOL_ICONS.get(_KIND_ICONS.get(kind, kind))
    return make() if make is not None else None


class PropertiesPanel(QtWidgets.QDockWidget):
    def __init__(self, parent, quick=False):
        """quick (0.354): the TAB's quick edit's (ui/quick_edit.py) — its type on top and its «Parâmetros» rows only,
        no search nor materials' browser; its page (`content`) is put over the view, not docked."""
        super().__init__(t("props.title"), parent)
        self.quick = quick
        self.setObjectName("quick_properties" if quick else "properties")
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(14)
        self.tree.setWordWrap(True)
        self.tree.setUniformRowHeights(False)
        self.tree.setItemDelegate(_WrapDelegate(self.tree))
        # (0.414, the owner: «destacando os títulos colapsáveis e com trama») the rows striped; a title folds with a
        # click anywhere on it (a double click no longer folds and opens it again at once)
        self.tree.setAlternatingRowColors(True)
        self.tree.setExpandsOnDoubleClick(False)
        # (0.396) the names' column as wide as its longest name, at most the share of the panel its divider was
        # dragged to (Revit's); a longer name, a longer value: in two lines, never cut ("…"); the groups folded by
        # hand stay folded (remembered)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setMinimumSectionSize(60)
        self._fitting = False
        self.tree.header().sectionResized.connect(self._divider_moved)
        self.tree.viewport().installEventFilter(self)
        self.tree.itemCollapsed.connect(lambda item: self._folded(item, True))
        self.tree.itemExpanded.connect(lambda item: self._folded(item, False))
        # (0.185, the interface's panel 7) what is shown on top — its icon, its name, its type —, a search over
        # the rows, the rows in groups that fold, and beside them the materials' browser
        self.header = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(self.header)
        row.setContentsMargins(6, 6, 6, 2)
        self.header_icon = QtWidgets.QLabel()
        self.header_icon.setFixedSize(40, 40)
        self.header_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        texts = QtWidgets.QVBoxLayout()
        texts.setSpacing(0)
        self.header_title = QtWidgets.QLabel()
        self.header_title.setStyleSheet("QLabel { font-weight: 600; }")
        self.header_sub = QtWidgets.QLabel()
        self._header_style()
        for label in (self.header_title, self.header_sub):
            label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            texts.addWidget(label)
        self.header_texts = texts
        self.type_combo = None       # (0.313) its type, chosen on top from the types' miniatures (ui/type_thumbs)
        row.addWidget(self.header_icon)
        row.addLayout(texts, 1)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText(t("props.search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _text: self.filter())
        page = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(page)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)
        column.addWidget(self.header)
        if not quick:
            column.addWidget(self.search)
        column.addWidget(self.tree, 1)
        self.materials = QtWidgets.QListWidget()               # (the materials' browser)
        self.materials.setIconSize(QtCore.QSize(22, 22))
        self.materials.setToolTip(t("props.mat_hint"))
        self.materials.itemDoubleClicked.connect(
            lambda item: self.on_material(item.data(QtCore.Qt.ItemDataRole.UserRole)) if self.on_material else None)
        # (0.391) with the Paint bucket on: one click chooses the bucket's material (SketchUp's Materials panel)
        self.on_pick = None
        self.materials.itemClicked.connect(
            lambda item: self.on_pick(item.data(QtCore.Qt.ItemDataRole.UserRole) or "") if self.on_pick else None)
        # (0.397) over it the same family list and search as the materials window's: the same order in both
        from .material_editor import family_combo
        self.mat_family = family_combo()
        self.mat_search = QtWidgets.QLineEdit()
        self.mat_search.setPlaceholderText(t("mat.search"))
        self.mat_search.setClearButtonEnabled(True)
        self.mat_family.currentIndexChanged.connect(lambda _i: self._fill_materials())
        self.mat_search.textChanged.connect(lambda _t: self._fill_materials())
        browser = QtWidgets.QWidget()
        mat_column = QtWidgets.QVBoxLayout(browser)
        mat_column.setContentsMargins(0, 4, 0, 0)
        mat_column.setSpacing(4)
        for w in (self.mat_family, self.mat_search):
            mat_column.addWidget(w)
        mat_column.addWidget(self.materials, 1)
        self.tabs = QtWidgets.QTabWidget()
        if quick:
            self.content = page
        else:
            self.tabs.addTab(page, t("props.tab_props"))
            self.tabs.addTab(browser, t("props.tab_materials"))
            self.tabs.currentChanged.connect(lambda i: self._fill_materials() if i == 1 else None)
            self.content = self.tabs
        self.setWidget(self.content)
        self.setMinimumWidth(340)
        self.on_edit = None          # callable(action, guid, value)
        self.on_edit_many = None     # (0.187) callable(action, guids, value): a change made to several elements
        self.on_material = None      # (0.185) callable(material key): a material double-clicked in the browser
        self.on_restyle = None       # (0.338) callable(): the theme changed — show again what is shown
        self.editors = _Editors()    # action -> widget (also used by tests)
        self._group = None           # (0.185) the group the rows go into now
        self._many = None            # (0.187) the elements the edits go to, when several are shown
        self._many_kind = None       # …the category chosen among them (None: all)
        self._many_view = None       # …and what was shown: (doc, ids)

    # ------------------------------------------------------------ the header, the groups, the search (0.185)

    def _header_style(self):
        """(0.338) Its header's icon box and second line in the theme's colours; (0.414) the rows' stripes, the
        editors in them see-through (the stripe goes on under a value)."""
        self.header_icon.setStyleSheet("QLabel { background: %s; border: 1px solid %s; border-radius: 4px; }"
                                       % (theme.C["panel"], theme.C["line"]))
        self.header_sub.setStyleSheet("QLabel { color: %s; }" % theme.C["muted"])
        self.tree.setStyleSheet("QTreeWidget { alternate-background-color: %s; }"
                                "QTreeWidget QLineEdit { background: transparent; }" % theme.props_colours()["stripe"])

    def restyle(self):
        """(0.338) In the theme in use: its header; its rows' colours, made again (on_restyle: the window shows what
        it showed)."""
        self._header_style()
        if self.on_restyle is not None:
            self.on_restyle()

    def _set_header(self, title, sub="", icon=None):
        self.header_title.setText(title)
        self.header_sub.setText(sub)
        self.header_icon.setPixmap(icon.pixmap(30, 30) if icon is not None else QtGui.QPixmap())
        self._sub_shown()

    def _sub_shown(self):
        """(0.313) The line under the name hidden when it only says the type the list under it shows."""
        combo = self.type_combo
        self.header_sub.setVisible(bool(self.header_sub.text()) and
                                   (combo is None or self.header_sub.text() != combo.currentText()))

    def _set_type_combo(self, combo, picture):
        """(0.313) The type's list on top, under the name — as Revit's Type Selector —, its miniature beside it."""
        self._drop_type_combo()
        self.type_combo = combo
        self.header_texts.addWidget(combo)
        if picture is not None:
            self.header_icon.setPixmap(picture.pixmap(36, 36))
        self._sub_shown()

    def _drop_type_combo(self):
        if self.type_combo is not None:
            self.header_texts.removeWidget(self.type_combo)
            self.type_combo.hide()
            self.type_combo.deleteLater()
            if self.editors.get("type") is self.type_combo:
                dict.__delitem__(self.editors, "type")
            self.type_combo = None
        self.header_sub.setVisible(bool(self.header_sub.text()))

    def _begin(self, title):
        """A group of rows that folds (Identification, Constraints and dimensions…): the rows after it go in it."""
        item = QtWidgets.QTreeWidgetItem([title, ""])
        font = item.font(0)
        font.setBold(True)
        font.setPointSizeF(font.pointSizeF() + 0.5 if font.pointSizeF() > 0 else 10.0)
        item.setFont(0, font)
        colours = theme.props_colours()                  # (0.414) a band of its own, the theme's
        for col in (0, 1):
            item.setBackground(col, QtGui.QBrush(QtGui.QColor(colours["group"])))
            item.setForeground(col, QtGui.QBrush(QtGui.QColor(colours["group_text"])))
        item.setToolTip(0, t("props.group_tip"))
        item.setData(0, GROUP, True)
        # (0.396) an element's groups in Revit's order — what is edited first (constraints and dimensions, materials),
        # then who it is (identification), its phase, its IFC data —, whatever the order they are made in: each put
        # before the first one made that comes after it (put in place now: moving a group later would lose its
        # editors)
        rank = {t(k): n for n, k in enumerate(GROUP_ORDER)}
        at = self.tree.topLevelItemCount()
        if title in rank and not self.quick:
            for k in range(self.tree.topLevelItemCount()):
                other = self.tree.topLevelItem(k)
                if other.data(0, GROUP) and rank.get(other.text(0), -1) > rank[title]:
                    at = k
                    break
        self.tree.insertTopLevelItem(at, item)
        item.setFirstColumnSpanned(True)
        item.setExpanded(True)
        self._group = item
        return item

    # ------------------------------------------------------------ (0.396) columns that fit, groups that stay folded

    @staticmethod
    def _settings():
        return QtCore.QSettings("ArqSynth", "ArqSynth BIM")

    def _ratio(self):
        try:
            r = float(self._settings().value("propriedades/divisor", DIVIDER_DEFAULT))
        except (TypeError, ValueError):
            r = DIVIDER_DEFAULT
        return min(DIVIDER_MOST, max(DIVIDER_LEAST, r))

    def _divider_moved(self, index, _old, new):
        """The divider dragged by hand: that share of the panel kept for the names (here and next time)."""
        if index != 0 or self._fitting:
            return
        room = self.tree.viewport().width()
        if room > 120:
            self._settings().setValue("propriedades/divisor", round(min(DIVIDER_MOST, max(DIVIDER_LEAST,
                                                                                            new / room)), 3))
        self.tree.doItemsLayout()

    def _fit_columns(self):
        """The names' column as wide as its longest name (bold ones bold, deeper ones further in), at most the
        divider's share of the panel; the rows laid out again (a name or a value too long: two lines)."""
        room = self.tree.viewport().width()
        if room < 120:
            return
        self._fit_room = room
        plain = self.tree.fontMetrics()
        bold_font = QtGui.QFont(self.tree.font())
        bold_font.setBold(True)
        bold = QtGui.QFontMetrics(bold_font)
        need = 0
        it = QtWidgets.QTreeWidgetItemIterator(self.tree)
        while it.value():
            item = it.value()
            it += 1
            if item.isFirstColumnSpanned() or item.isHidden() or not item.text(0):
                continue
            depth, up = 1, item.parent()
            while up is not None:
                depth, up = depth + 1, up.parent()
            metrics = bold if item.font(0).bold() else plain
            width = max(metrics.horizontalAdvance(line) for line in item.text(0).split("\n"))
            need = max(need, width + depth * self.tree.indentation() + 16)
        width = max(90, min(need, int(room * self._ratio())))
        self._fitting = True
        try:
            self.tree.setColumnWidth(0, width)
        finally:
            self._fitting = False
        self.tree.doItemsLayout()

    def eventFilter(self, obj, event):
        if obj is self.tree.viewport() and event.type() == QtCore.QEvent.Type.Resize and \
                abs(self.tree.viewport().width() - getattr(self, "_fit_room", 0)) > 2:
            QtCore.QTimer.singleShot(0, self._fit_columns)       # (the panel made wider or narrower)
        if obj is self.tree.viewport() and event.type() == QtCore.QEvent.Type.MouseButtonRelease and \
                event.button() == QtCore.Qt.MouseButton.LeftButton and self._title_click(event.position().toPoint()):
            return True
        return super().eventFilter(obj, event)

    def _title_click(self, pos):
        """(0.414) A click on a group's title — anywhere on its band —, or on a subgroup's name: it folds (or opens).
        Not on its arrow (Qt's own) nor on a value's editor."""
        index = self.tree.indexAt(pos)
        item = self.tree.itemFromIndex(index) if index.isValid() else None
        if item is None or not item.childCount():
            return False
        if not (item.data(0, GROUP) or (item.data(0, SUB) and index.column() == 0)):
            return False
        if pos.x() < self.tree.visualRect(index.sibling(index.row(), 0)).x():
            return False                                 # (its arrow: Qt folds it)
        item.setExpanded(not item.isExpanded())
        return True

    @staticmethod
    def _fold_key(item):
        return item.text(0).split("\n")[0]

    def _folded_keys(self):
        value = self._settings().value("propriedades/fechados", [])
        if isinstance(value, str):
            value = [value] if value else []
        return set(value or ())

    def _folded(self, item, folded):
        """A group folded or opened by hand: remembered (by its name) for every element shown after."""
        if self._fitting or not item.childCount():
            return
        keys = self._folded_keys()
        key = self._fold_key(item)
        if folded == (key in keys):
            return
        keys = keys | {key} if folded else keys - {key}
        self._settings().setValue("propriedades/fechados", sorted(keys))

    def _clear(self):
        self._group = None
        self._many = None
        self._drop_type_combo()
        self.editors = _Editors()
        self.tree.clear()

    def _done(self):
        """The rows made: every group open, an empty one left out, the search applied again. (0.354) The quick edit's:
        its «Parâmetros» group only."""
        if self.quick:
            keep = t("props.g.parameters")
            for k in reversed(range(self.tree.topLevelItemCount())):
                item = self.tree.topLevelItem(k)
                if not item.data(0, GROUP) or item.text(0) != keep:
                    self.tree.takeTopLevelItem(k)
        for k in reversed(range(self.tree.topLevelItemCount())):
            item = self.tree.topLevelItem(k)
            if item.data(0, GROUP) and item.childCount() == 0:
                self.tree.takeTopLevelItem(k)
        self._subgroups()
        self._fitting = True
        try:
            self.tree.expandAll()
            folded = self._folded_keys()
            if folded:
                it = QtWidgets.QTreeWidgetItemIterator(self.tree)
                while it.value():
                    item = it.value()
                    if item.childCount() and self._fold_key(item) in folded:
                        item.setExpanded(False)
                    it += 1
        finally:
            self._fitting = False
        self._fit_columns()
        if self.search.text().strip():
            self.filter()

    def _subgroups(self):
        """(0.414) A row with rows under it, inside a group (a surface's Forma, Modificadores, Nervuras; a joinery's
        cells…): a lighter band, its name bold — a title that folds as the groups' do."""
        sub = QtGui.QBrush(QtGui.QColor(theme.props_colours()["sub"]))
        it = QtWidgets.QTreeWidgetItemIterator(self.tree)
        while it.value():
            item = it.value()
            it += 1
            if item.parent() is None or not item.childCount() or item.isFirstColumnSpanned():
                continue
            item.setData(0, SUB, True)
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            for col in (0, 1):
                item.setBackground(col, sub)

    def filter(self):
        """Only the rows whose name or value has the search's text (any case), in their groups."""
        text = self.search.text().strip().lower()

        def value(item):
            widget = self.tree.itemWidget(item, 1)
            if isinstance(widget, QtWidgets.QLineEdit):
                return widget.text()
            if isinstance(widget, QtWidgets.QComboBox):
                return widget.currentText()
            return item.text(1)

        def walk(item):
            own = not text or text in item.text(0).lower() or text in value(item).lower()
            shown = False
            for k in range(item.childCount()):
                shown = walk(item.child(k)) or shown
            item.setHidden(not (own or shown))
            return own or shown

        for k in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(k)
            if text and group.childCount() and not walk(group):
                group.setHidden(True)
            elif not text or group.childCount() == 0:
                walk(group)
            else:
                group.setHidden(False)
                self._fitting = True                      # (opened for the search: not remembered as opened)
                group.setExpanded(True)
                self._fitting = False

    def _fill_materials(self):
        """The project's materials, each its colour and its name (a double click opens it). (0.391) With the Paint
        bucket on: «Sem pintura» first — one click chooses. (0.397) As the materials window lists them: the family
        and the words chosen on top, in alphabetical order (the paints under «Tintas»)."""
        from .material_editor import listed
        self.materials.clear()
        name = lambda s: s.name_pt if lang() == "pt" else s.name_en          # noqa: E731
        painting = self.on_pick is not None
        if painting:
            item = QtWidgets.QListWidgetItem(t("paint.none"))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, "")
            self.materials.addItem(item)
        for spec in listed(self.mat_family.currentData(), self.mat_search.text()):
            swatch = QtGui.QPixmap(22, 22)
            swatch.fill(QtGui.QColor.fromRgbF(*[min(max(float(c), 0.0), 1.0) for c in spec.color]))
            item = QtWidgets.QListWidgetItem(QtGui.QIcon(swatch), name(spec))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, spec.key)
            self.materials.addItem(item)
        if painting and getattr(self, "_marked", None) is not None:
            self.mark_material(self._marked)                # (the bucket's, still marked if listed)

    @staticmethod
    def _paint_text(doc, guid):
        """(0.391) «Tinta branca 12,30 m²; …» of an element's painted faces, or ""."""
        from ..model import paint as paint_model
        obj = doc.get(guid) if doc is not None else None
        if obj is None or not getattr(obj, "is_bim", False) or not paint_model.entries(doc.ifc, guid):
            return ""
        from ..tools.paint import material_name
        try:
            areas = paint_model.area_by_material(doc.ifc, obj)
        except (AttributeError, RuntimeError, ValueError):
            return ""
        return "; ".join("{} {:.2f} m²".format(material_name(k), a).replace(".", decimal_sep())
                         for k, a in sorted(areas.items()))

    def show_paint(self, on, key=None):
        """(0.391) The Paint bucket on (the browser in front, one click chooses, its material marked) or off."""
        self.on_pick = (self.on_pick or (lambda _k: None)) if on else None
        if on:
            self.show()
            self.raise_()
            self._fill_materials()
            self.tabs.setCurrentIndex(1)
            self.mark_material(key)
        else:
            self.tabs.setCurrentIndex(0)

    def mark_material(self, key):
        """(0.391) The bucket's material marked in the browser."""
        self._marked = key
        for k in range(self.materials.count()):
            item = self.materials.item(k)
            if (item.data(QtCore.Qt.ItemDataRole.UserRole) or "") == (key or ""):
                self.materials.setCurrentItem(item)
                self.materials.scrollToItem(item)
                return

    # ------------------------------------------------------------ rows

    def _row(self, key, value="", parent=None, bold=False):
        item = QtWidgets.QTreeWidgetItem([key, value])
        if len(key) > 24:                                  # (0.395: whole in a tip, should its column cut it)
            item.setToolTip(0, key)
        if bold:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
        parent = parent if parent is not None else self._group
        (parent.addChild(item) if parent is not None else self.tree.addTopLevelItem(item))
        return item

    def _emit(self, action, guid, value):
        # Applying an edit rebuilds this panel, which deletes the widget that sent the
        # signal: run it once the signal has returned.
        if self._many and self.on_edit_many is not None:             # (0.187) several elements: to all of them
            many = list(self._many)
            QtCore.QTimer.singleShot(0, lambda: self.on_edit_many(action, many, value))
        elif self.on_edit is not None:
            QtCore.QTimer.singleShot(0, lambda: self.on_edit(action, guid, value))

    def _text_editor(self, key, text, action, guid, parse=None):
        item = self._row(key, "")
        edit = QtWidgets.QLineEdit(text)
        edit.setFrame(False)

        def finished():
            new = edit.text().strip()
            varies = bool(edit.property("varies"))        # (0.187) blank: it differs among the elements
            if (not new) if varies else (new == text):
                return
            if parse is None:
                self._emit(action, guid, new)
                return
            value = parse(new)
            if value is None:
                edit.setText("" if varies else text)   # invalid: put the old value back
                return
            self._emit(action, guid, value)

        edit.editingFinished.connect(finished)
        edit.setCursorPosition(0)                        # (0.396: a long value shown from its start)
        if len(text) > 18:
            edit.setToolTip(text)
        self.tree.setItemWidget(item, 1, edit)
        self.editors[action] = edit
        return edit

    def _length_editor(self, key, meters, action, guid):
        return self._text_editor(key, _len(meters).replace("~ ", ""), action, guid,
                                 parse=lambda s: (lambda v: v if v is not None and v > 0 else None)(parse_length(s)))

    def _length0_editor(self, key, meters, action, guid):
        """A length that may be 0 (a gap, a margin, a height over the floor)."""
        return self._text_editor(key, _len(meters).replace("~ ", ""), action, guid,
                                 parse=lambda s: (lambda v: v if v is not None and v >= 0 else None)(parse_length(s)))

    def text(self):
        """All rows as plain text, editors included (used by tests) — (0.313) the type on top first."""
        out = ["{}: {}".format(t("props.type"), self.type_combo.currentText())] if self.type_combo is not None else []
        it = QtWidgets.QTreeWidgetItemIterator(self.tree)
        while it.value():
            item = it.value()
            widget = self.tree.itemWidget(item, 1)
            if isinstance(widget, QtWidgets.QLineEdit):
                value = widget.text()
            elif isinstance(widget, QtWidgets.QComboBox):
                value = widget.currentText()
            elif isinstance(widget, QtWidgets.QCheckBox):
                value = str(widget.isChecked())
            else:
                value = item.text(1)
            out.append("{}: {}".format(item.text(0), value))
            it += 1
        return "\n".join(out)

    # ------------------------------------------------------------ content

    def show_selection(self, doc, ids):
        self._clear()
        ids = [i for i in ids if doc.get(i) is not None]
        if not ids:
            self._set_header(t("props.nothing"))
            self._row(t("props.nothing"), bold=True)
            self._row(t("props.hint"))
        elif len(ids) > 1:
            group = self._whole_group(doc, ids)
            if group is not None:
                self._set_header(t("props.many", n=len(ids)))
                self._show_group(doc, group, len(ids))
            else:
                self._show_many(doc, ids)
                return
        else:
            obj = doc.get(ids[0])
            if obj.is_bim:
                self._show_bim(doc, obj)
                group = doc.ifc.group_of(obj.id)
                if group is not None:
                    copies = len(doc.ifc.group_copies(doc.ifc.group_model(group)))
                    self._row(t("props.group"), t("props.group_member", name=group.Name or "", n=copies))
            else:
                self._set_header(obj.name, t("props.sketch_kind"), _kind_icon("sketch"))
                self._show_sketch(obj)
        self._done()

    # ------------------------------------------------------------ several elements (0.187)

    MANY_MAX = 150                  # more than this: how many and of what only (comparing them all takes too long)
    MANY_SKIP = {"name", "mark"}    # one for each element: not given to many at once

    def _show_many(self, doc, ids):
        """Several elements, as in Revit: on top, what they are — all of them or one category (a list, when they
        are of more than one) —, and the properties they have in common: a value they share shown, one that
        differs left blank (a box half ticked). A change made here goes to every one of them (on_edit_many), as
        one undo step. Their name, their GlobalId and the buttons that work on one element are left out."""
        from .project_tree import category_label
        cats = {}
        for i in ids:
            obj = doc.get(i)
            cats.setdefault(obj.ifc_class if obj.is_bim else "", []).append(i)
        if self._many_view is None or set(self._many_view[1]) != set(ids):
            self._many_kind = None                              # (another selection: all of it again)
        kind = self._many_kind if self._many_kind in cats else None
        targets = cats[kind] if kind is not None else list(ids)
        self._many_view = (doc, list(ids))
        objs = [doc.get(i) for i in targets]
        snaps = []
        comparable = all(o.is_bim for o in objs) and len(objs) <= self.MANY_MAX
        if comparable:
            self.tree.setUpdatesEnabled(False)
            try:
                for obj in objs[1:]:
                    self._clear()
                    self._show_bim(doc, obj)
                    snaps.append(self._snapshot())
            finally:
                self.tree.setUpdatesEnabled(True)
        self._clear()
        label = lambda c: category_label(c) if c else t("props.sketches")                      # noqa: E731
        if len(cats) > 1:                                       # which of them: all, or one category
            item = self._row(t("props.many_filter"), "")
            combo = QtWidgets.QComboBox()
            combo.addItem(t("props.many_all", n=len(ids)), None)
            for c in sorted(cats, key=lambda c: label(c).lower()):
                combo.addItem("{} ({})".format(label(c), len(cats[c])), c)
            combo.setCurrentIndex(max(0, combo.findData(kind)))
            combo.activated.connect(lambda _k: self._pick_many(combo.currentData()))
            self.tree.setItemWidget(item, 1, combo)
            self.editors["many_filter"] = combo
        if comparable and len(objs) == 1:                       # (one of that category: it, as on its own)
            self._show_bim(doc, objs[0])
            self._done()
            return
        if comparable:
            self._show_bim(doc, objs[0])
            self._merge(snaps)
        else:
            self._note(t("props.many_too_many", n=self.MANY_MAX) if len(objs) > self.MANY_MAX
                       else t("props.many_sketches"), theme.C["note"])
        one = kind if kind is not None else (next(iter(cats)) if len(cats) == 1 else None)
        self._set_header(t("props.many", n=len(targets)),
                         label(one) if one is not None else ", ".join(label(c) for c in sorted(cats, key=label)),
                         _kind_icon(one) if one else None)
        self._many = list(targets)
        self._done()

    def _pick_many(self, kind):
        """The category chosen in the list on top (None: all of them): the panel again, for those."""
        self._many_kind = kind
        doc, ids = self._many_view
        QtCore.QTimer.singleShot(0, lambda: self.show_selection(doc, ids))

    def _rows(self):
        """Every row under the groups, with its path ((group, …, name), the row)."""
        out = []

        def walk(item, path):
            for k in range(item.childCount()):
                child = item.child(k)
                out.append((path + (child.text(0),), child))
                walk(child, path + (child.text(0),))

        for g in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(g)
            if group.data(0, GROUP):
                walk(group, (group.text(0),))
        return out

    def _row_value(self, item, actions):
        """A row's (key part, value): what edits it — its action and kind of editor, a list's choices — and the
        value shown; ("button", …) for one that works on one element."""
        widget = self.tree.itemWidget(item, 1)
        action = actions.get(id(widget)) if widget is not None else None
        if widget is None:
            return ("shown", None), item.text(1)
        if isinstance(widget, QtWidgets.QLineEdit):
            return ("text", repr(action)), widget.text()
        if isinstance(widget, QtWidgets.QComboBox):
            items = tuple(widget.itemText(k) for k in range(widget.count()))
            return ("choice", repr(action), items), widget.currentText()
        if isinstance(widget, QtWidgets.QCheckBox):
            return ("check", repr(action)), widget.isChecked()
        return ("button", repr(action)), None

    def _snapshot(self):
        """The rows as they are now: {(path, what edits it): value}."""
        actions = {id(w): a for a, w in self.editors.made}
        snap = {}
        for path, item in self._rows():
            what, value = self._row_value(item, actions)
            snap[(path, what)] = value
        if self.type_combo is not None:                 # (0.313) the type, on top
            snap[self._type_key()] = self.type_combo.currentText()
        return snap

    def _type_key(self):
        combo = self.type_combo
        return ("header",), ("choice", "'type'", tuple(combo.itemText(k) for k in range(combo.count())))

    def _merge(self, snaps):
        """The first element's rows (made already) left as the ones the others share: a row they do not all have
        taken out, a value that differs left blank — and edits that then go to all of them."""
        actions = {id(w): a for a, w in self.editors.made}
        drop = []
        for path, item in self._rows():
            what, value = self._row_value(item, actions)
            action = actions.get(id(self.tree.itemWidget(item, 1)))
            if what[0] == "button" or path[-1] == "GlobalId" or action in self.MANY_SKIP or \
                    any((path, what) not in s for s in snaps):
                drop.append(item)
                continue
            if all(s[(path, what)] == value for s in snaps):
                continue
            widget = self.tree.itemWidget(item, 1)
            if widget is None:
                item.setText(1, t("props.varies"))
                item.setForeground(1, QtGui.QBrush(theme.colour("note")))
            else:
                self._varies(widget, action)
        gone = {id(self.tree.itemWidget(item, 1)) for item in drop if self.tree.itemWidget(item, 1) is not None}
        for action, widget in list(self.editors.items()):          # (their editors are no more)
            if id(widget) in gone:
                dict.__delitem__(self.editors, action)
        self.editors.made = [(a, w) for a, w in self.editors.made if id(w) not in gone]
        for item in reversed(drop):
            (item.parent() or self.tree.invisibleRootItem()).removeChild(item)
        if self.type_combo is not None:                 # (0.313) the type on top: theirs, blank, or none to choose
            key = self._type_key()
            if any(key not in s for s in snaps):        # (of several kinds: no list of types for all of them)
                combo = self.type_combo
                self._drop_type_combo()
                self.editors.made = [(a, w) for a, w in self.editors.made if w is not combo]
            elif any(s[key] != self.type_combo.currentText() for s in snaps):
                self._varies(self.type_combo, "type")
                self._sub_shown()

    def _varies(self, widget, action):
        """An editor whose value differs among the elements: blank (a box half ticked); what is chosen or typed
        in it then goes to all of them, even the value one of them already has."""
        widget.setProperty("varies", True)
        blocker = QtCore.QSignalBlocker(widget)
        if isinstance(widget, QtWidgets.QLineEdit):
            widget.setText("")
            widget.setPlaceholderText(t("props.varies"))
        elif isinstance(widget, QtWidgets.QComboBox):
            widget.setPlaceholderText(t("props.varies"))
            widget.setCurrentIndex(-1)
        elif isinstance(widget, QtWidgets.QCheckBox):
            widget.setTristate(True)
            widget.setCheckState(QtCore.Qt.CheckState.PartiallyChecked)
            try:
                widget.toggled.disconnect()                # (its one element's: the value goes to all now)
            except (RuntimeError, TypeError):
                pass

            def picked(state):
                if state == QtCore.Qt.CheckState.PartiallyChecked:
                    return
                widget.setTristate(False)
                self._emit(action, None, state == QtCore.Qt.CheckState.Checked)

            widget.checkStateChanged.connect(picked)
        del blocker

    def show_grid_axes(self, doc, indices):
        """Grid axes selected (0.72): one — its tag, its two ends and its length, editable; several — how many."""
        self._clear()
        self._set_header(t("props.grid_axes", n=len(indices)), "", _kind_icon("grid"))
        indices = [k for k in sorted(indices) if 0 <= k < len(doc.grids)]
        if len(indices) != 1:
            self._row(t("props.grid_axes", n=len(indices)), bold=True)
        else:
            k = indices[0]
            axis = doc.grids[k]
            self._row(t("props.kind"), t("props.grid_axis"), bold=True)
            self._text_editor(t("props.grid_tag"), axis.tag, "grid_tag", k)
            for key, which, p in (("props.grid_start", "start", axis.start), ("props.grid_end", "end", axis.end)):
                self._text_editor(t(key), _point(p), ("grid_point", which), k, parse=_parse_plan_point)
            length = float(np.hypot(axis.end[0] - axis.start[0], axis.end[1] - axis.start[1]))
            self._row(t("props.length"), _len(length))
        self._note(t("props.grid_hint"), theme.C["link"])
        self._done()

    def show_annotations(self, doc, anns, plane):
        """(0.191) Drawings in the view selected: one — what it is, its words, size and angle (a text), its hatch (a
        region), its line type and pen, its sizes (a line's length, a circle's radius, a region's area); several —
        how many. Its points move by their grips."""
        from ..model import annotations as notes2d
        from ..model import graphic_styles as styles_model
        from ..tools.draft import TEXT_SIZES
        self._clear()
        kinds = {a.kind for a in anns}
        one = anns[0] if len(anns) == 1 else None
        title = t("draft." + one.kind) if one is not None else t("props.anns", n=len(anns))
        self._set_header(title, t("props.ann_sub"), _kind_icon("draft"))
        self._begin(t("props.g.drawing"))
        if one is None:
            self._row(t("props.anns", n=len(anns)), ", ".join(sorted(t("draft." + k).lower() for k in kinds)))
            self._note(t("props.ann_hint"), theme.C["link"])
            self._done()
            return
        self._row(t("props.kind"), title, bold=True)
        if one.kind == "text":
            self._text_editor(t("props.ann_text"), one.text, "ann_text", one)
            sizes = sorted(set(TEXT_SIZES) | {float(one.size)})
            self._choice_combo(t("ctx.text_size"), "ann_size", one,
                               [("{} mm".format(str(s).replace(".", decimal_sep())), s) for s in sizes], float(one.size))
            self._text_editor(t("props.ann_angle"), format_angle(notes2d.angle(one), decimal_sep()), "ann_angle", one,
                              parse=parse_angle)
        else:
            if one.kind == "region":
                self._choice_combo(t("ctx.draft_hatch"), "ann_hatch", one,
                                   [(t("drafthatch." + h), h) for h in notes2d.HATCHES], one.hatch)
            if one.kind not in notes2d.MARKS:
                self._choice_combo(t("ctx.line_type"), "ann_line", one,
                                   [(t("linetype." + k), k) for k in styles_model.LINE_TYPES],
                                   one.extra.get("line", "continuous"))
                widths = [(t("linewidth.project"), 0.0)] + [("{:.2f} mm".format(w).replace(".", decimal_sep()), w)
                                                            for w in styles_model.LINE_WIDTHS]
                self._choice_combo(t("ctx.line_width"), "ann_width", one, widths, float(one.extra.get("width") or 0.0))
            if plane is not None:
                origin, u, v, _n = plane
                p = notes2d.to2(one.points, origin, u, v)
                if one.kind == "line" and len(p) >= 2:
                    self._length_editor(t("props.length"), float(np.linalg.norm(p[1] - p[0])), "ann_length", one)
                elif one.kind == "circle" and len(p) >= 2:
                    self._length_editor(t("props.radius"), float(np.linalg.norm(p[1] - p[0])), "ann_radius", one)
                elif one.kind in ("region", "rectangle", "circle"):
                    self._row(t("props.area"), "{:.2f} m²".format(notes2d.area(one, origin, u, v)).replace(".",
                                                                                                      decimal_sep()))
        self._note(t("props.ann_hint"), theme.C["link"])
        self._done()

    def show_dimensions(self, doc, dims, plane):
        """(0.193) Dimensions selected: their value (one alone), and their dimension type — the project's style, or
        one of its types —, changed here for all of them. (0.405, as Revit's) The type on top, in its list (the Type
        Selector), «Editar tipo…» beside its properties; the string's: its values (one alone: typed, the element at
        its far end moves), IG, its words (a text over a value alone, a prefix, a suffix, words over and under), the
        values put back in their place; its text's window, references added."""
        from ..model import dimensions as dims_model
        self._clear()
        linear = [d for d in dims if d.vertex is None]
        one = dims[0] if len(dims) == 1 else None
        self._set_header(t("props.dimension") if one is not None else t("props.dimensions", n=len(dims)),
                         t("props.ann_sub"), _kind_icon("dimension"))
        names = dims_model.type_names(doc.dim_style)
        styles = {d.style if d.style in names else "" for d in dims}
        current = styles.pop() if len(styles) == 1 else None
        combo = QtWidgets.QComboBox()                   # (the type on top, as Revit's Type Selector)
        combo.setObjectName("props_type")
        combo.setToolTip(t("ctx.dim_type"))
        choices = [(t("dimtype.project"), "")] + [(n, n) for n in names]
        for text, value in choices:
            combo.addItem(text, value)
        combo.setCurrentIndex(max(0, combo.findData(current if current is not None else "")))
        combo.activated.connect(lambda k: self._emit("dim_type", list(dims), combo.itemData(k))
                                if combo.itemData(k) != current else None)
        self._set_type_combo(combo, None)
        self.editors["dim_type"] = combo
        if current is None:
            self._varies(combo, "dim_type")
        self._begin(t("props.g.dim_type"))
        item = self._row(t("props.type"), "")
        button = QtWidgets.QPushButton(t("props.edit_type"))
        button.setToolTip(t("props.dim_edit_type_tip"))
        button.clicked.connect(lambda _c=False: self._emit("dim_edit_type", list(dims), current or None))
        self.tree.setItemWidget(item, 1, button)
        self.editors["dim_edit_type"] = button
        self._begin(t("props.g.dim_values"))
        lengths = []
        if plane is not None:
            origin, u, v, _n = plane
            for d in linear:
                a, b = dims_model.ends(doc, d)
                lengths.append(dims_model.placed(a, b, dims_model.line_point(doc, d), origin, u, v, d.direction)[4])
        style = dims_model.style_of(doc.dim_style, dims[0])
        unit = style.get("unit", "m")
        if one is not None and lengths:
            movable = [r for r in one.refs if r is not None and doc.get(r[0]) is not None]
            if movable:                                  # (typed: the element at its far end moves, as Revit's)
                self._length_editor(t("props.dim_value"), lengths[0], "dim_value", one)
            else:
                self._row(t("props.dim_value"), "{} {}".format(dims_model.text(lengths[0], decimal_sep(), style),
                                                               unit), bold=True)
        elif lengths:
            self._row(t("props.dim_string"), t("props.dim_string_n", n=len(lengths),
                                                v="{} {}".format(dims_model.text(sum(lengths), decimal_sep(), style),
                                                                 unit)), bold=True)
        if linear:
            self._check_row(t("props.dim_eq"), "dim_eq", list(linear), all(d.eq for d in linear))
        self._begin(t("props.g.dim_text"))
        notes = [d.note or {} for d in linear] or [{}]
        keys = (("override", "props.dim_override"),) if one is not None else ()
        keys += (("prefix", "props.dim_prefix"), ("suffix", "props.dim_suffix"), ("above", "props.dim_above"),
                 ("below", "props.dim_below"))
        for key, label in keys:
            values = {n.get(key, "") for n in notes}
            edit = self._text_editor(t(label), values.pop() if len(values) == 1 else "", "dim_note_" + key,
                                     list(linear))
            if len(values) > 0:
                self._varies(edit, "dim_note_" + key)
        if any(dims_model.text_shift(d) is not None for d in linear):
            item = self._row(t("props.dim_shifted"), "")
            back = QtWidgets.QPushButton(t("act.dim_text_back"))
            back.clicked.connect(lambda _c=False: self._emit("dim_text_back", list(linear), None))
            self.tree.setItemWidget(item, 1, back)
            self.editors["dim_text_back"] = back
        for action, label, text in (("dim_text_window", "props.dim_text_window", "props.dim_open"),
                                    ("dim_add", "props.dim_refs", "props.dim_add")):     # (one a row: never cut)
            item = self._row(t(label), "")
            b = QtWidgets.QPushButton(t(text))
            b.clicked.connect(lambda _c=False, a=action: self._emit(a, list(linear), None))
            self.tree.setItemWidget(item, 1, b)
            self.editors[action] = b
        self._note(t("props.dim_hint"), theme.C["link"])
        self._done()

    def show_rooms(self, doc, guids):
        """Rooms selected (0.99): one — its name and number, its area, perimeter and height, its finishes,
        editable; several — how many."""
        self._clear()
        guids = [g for g in guids if doc.ifc.by_guid(g) is not None]
        self._set_header(t("props.rooms", n=len(guids)) if len(guids) != 1 else t("props.room"), "",
                         _kind_icon("room"))
        if len(guids) != 1:
            self._row(t("props.rooms", n=len(guids)), bold=True)
        else:
            g = guids[0]
            info = doc.ifc.space_info(g)
            if info is None:
                return
            self._row(t("props.kind"), t("props.room"), bold=True)
            self._text_editor(t("props.room_name"), info["name"], "room_name", g)
            self._text_editor(t("props.room_number"), info["number"], "room_number", g)
            self._choice_combo(t("props.room_where"), "room_external", g,                     # (0.357)
                               [(t("props.room_interior"), False), (t("props.room_exterior"), True)],
                               bool(info.get("external")))
            self._row(t("props.room_area"), "{:.2f} m²".format(info["area"]).replace(".", decimal_sep()))
            self._row(t("props.room_perimeter"), _len(info["perimeter"]))
            self._row(t("props.room_height"), _len(info["height"]))
            for key, label in (("FloorCovering", "props.room_floor"), ("WallCovering", "props.room_wall"),
                               ("CeilingCovering", "props.room_ceiling")):
                self._text_editor(t(label), info["finishes"].get(key, ""), ("room_finish", key), g)
        self._note(t("props.room_hint"), theme.C["link"])
        self._done()

    # ------------------------------------------------------------ the view shown (nothing selected)

    def show_view(self, doc, view, label, classes):
        """The properties of the view shown, as Revit's with nothing selected: its name (a section's
        can be changed), its view template, and what it shows — for that view alone, or, with a
        template, the template's (read only). `classes`: () -> the IFC classes in the model (asked
        for when the Visibility window opens)."""
        self._clear()
        kind = view[0]
        tpl = doc.template_of(view)
        s = doc.view_settings(view)
        self._set_header(label, t("props.view_kind." + kind), _kind_icon("view_" + kind))
        self._view_type_header(doc, view, tpl)
        self._begin(t("props.g.view"))
        if kind == "section" or (kind == "3d" and len(view) > 1):     # (a named view: its name changes here)
            self._text_editor(t("props.view"), label, "view_name", view)
        else:
            self._row(t("props.view"), label, bold=True)
        self._row(t("props.view_kind"), t("props.view_kind." + kind))
        item = self._row(t("props.view_template"), "")              # (0.414) a template made of this view
        button = QtWidgets.QPushButton(t("props.view_template_save"))
        button.setToolTip(t("props.view_template_save_tip"))
        button.clicked.connect(lambda _c=False: self._emit("view_template_save", view, True))
        self.tree.setItemWidget(item, 1, button)
        self.editors["view_template_save"] = button
        styles = [(view_styles_model.label(vs, t), vs.uid) for vs in view_styles_model.all_styles(doc.view_styles)]
        if kind in ("plan", "section", "elevation"):       # (0.315) a drawing's: none — lines, as always — or one
            self._choice_combo(t("props.view_style"), "view_style", view,
                               [(t("props.view_style.none"), None)] + styles, s.drawn_style)
        if kind == "3d":                                   # its look (0.63): its own, template or not
            self._choice_combo(t("props.view_style"), "view_style", view, styles, s.style)
            self._choice_combo(t("props.view_projection"), "view_axonometric", view,
                               [(t("props.view_perspective"), False), (t("props.view_axonometric"), True)],
                               s.axonometric)
            self._check_row(t("props.view_edges"), "view_edges", view, s.edges)
            self._check_row(t("props.view_grid"), "view_grid", view, s.grid)
            self._check_row(t("props.view_slopes"), "view_slopes", view, s.slopes)         # (0.201)
            self._check_row(t("props.view_box"), "view_box_on", view, s.box is not None)
            if s.box is not None:                          # its faces, typed (0.64)
                for axis, name in enumerate("XYZ"):
                    self._text_editor(t("props.view_box_axis", axis=name),
                                      "{}; {}".format(_coord(s.box[0][axis]), _coord(s.box[1][axis])),
                                      ("view_box", axis), view, parse=_parse_span)
        if kind == "plan":                                 # its range and look (0.65): its own, template or not
            self._text_editor(t("props.view_depth"), _len(s.depth).replace("~ ", ""), "view_depth", view,
                              parse=lambda text: (lambda v: v if v is not None and v >= 0 else None)(parse_length(text)))
            self._choice_combo(t("props.view_underlay"), "view_underlay", view,
                               [(t("props.view_underlay.none"), None), (t("props.view_underlay.below"), "below"),
                                (t("props.view_underlay.above"), "above")], s.underlay)
            self._check_row(t("props.view_crop"), "view_crop_on", view, s.crop is not None)
            if s.crop is not None:
                x0, y0, x1, y1 = s.crop
                for axis, (lo, hi) in enumerate(((x0, x1), (y0, y1))):
                    self._text_editor(t("props.view_crop_axis", axis="XY"[axis]), "{}; {}".format(_coord(lo), _coord(hi)),
                                      ("view_crop", axis), view, parse=_parse_span)
            self._check_row(t("props.view_slopes"), "view_slopes", view, s.slopes)         # (0.201: on paper too)
        if kind in ("plan", "section", "elevation"):
            self._choice_combo(t("props.view_detail"), "view_detail", view,
                               [(t("props.view_detail." + k), k) for k in DETAILS], s.detail)
        if tpl is not None:
            if kind != "3d":
                self._row(t("tpl.scale"), "1:{}".format(s.scale) if s.scale else t("sheet.scale_auto"))
            if kind == "plan":
                self._row(t("props.view_cut"), _len(s.cut_height))
            self._row(t("tpl.phases"), t("tpl.phases." + s.phases))
            if tpl.style:                                  # (0.315) its views' style
                self._row(t("tpl.style"), view_styles_model.label(doc.view_style(tpl.style), t))
            self._row(t("tpl.rule"), rules_model.rule_label(s.rule) if s.rule else t("rules.none"))
            self._row(t("props.view_categories"), self._hidden_text(s.hidden))
            self._note(t("props.view_by_template", name=tpl.name), theme.C["link"])
        else:
            if kind != "3d":
                self._scale_combo(view, s.scale)
            if kind == "plan":
                self._length_editor(t("props.view_cut"), s.cut_height, "view_cut", view)
            self._choice_combo(t("tpl.phases"), "view_phases", view,
                               [(t("tpl.phases." + k), k) for k in PHASE_FILTERS], s.phases)
            rules = [(t("rules.none"), None)] + [(rules_model.rule_label(k), k) for k in rules_model.RULES]
            if s.rule is not None and s.rule not in rules_model.RULES:
                rules.append((rules_model.rule_label(s.rule), s.rule))
            self._choice_combo(t("tpl.rule"), "view_rule", view, rules, s.rule)
            self._row(t("props.view_categories"), self._hidden_text(s.hidden))
            item = self._row("", "")
            button = QtWidgets.QPushButton(t("props.view_visibility"))
            button.setToolTip(t("props.view_visibility_tip"))
            button.clicked.connect(lambda: self._visibility(view, label, classes, s.hidden))
            self.tree.setItemWidget(item, 1, button)
            self.editors["view_hidden"] = button
        self._note(t("props.view_hint"), theme.C["note"])
        self._done()
        self.tree.setCurrentItem(None)

    def _note(self, text, colour):
        """A line of advice across the panel (broken in lines: the panel is narrow)."""
        note = self._row(textwrap.fill(text, 48))
        note.setFirstColumnSpanned(True)
        note.setForeground(0, QtGui.QBrush(QtGui.QColor(colour)))
        return note

    @staticmethod
    def _hidden_text(hidden):
        if not hidden:
            return t("props.view_all_shown")
        from .project_tree import category_label
        names = sorted(category_label(c) for c in hidden)
        return textwrap.fill(t("props.view_n_hidden", n=len(names), names=", ".join(names)), 30)

    def _choice_combo(self, key, action, view, choices, current):
        """A row with a list to choose from: choices [(text, value)]; on_edit gets the value."""
        item = self._row(key, "")
        combo = QtWidgets.QComboBox()
        for text, value in choices:
            combo.addItem(text, value)
        combo.setCurrentIndex(next((k for k, (_t, v) in enumerate(choices) if v == current), 0))

        def chosen(k):
            if choices[k][1] != current or combo.property("varies"):
                self._emit(action, view, choices[k][1])

        combo.activated.connect(chosen)
        self.tree.setItemWidget(item, 1, combo)
        self.editors[action] = combo
        return combo

    def _system_combo(self, info, guid, kind):
        """(0.141) A pipe's / duct's / fitting's system — chosen here, the whole run it is in goes into it."""
        from ..ifc import systems as systems_model
        current = info.get("system")
        choices = [] if current else [(t("system.none"), "")]
        choices += [(t("system." + k), k) for k in systems_model.of_kind(kind)]
        self._choice_combo(t("props.system"), "system", guid, choices, current or "")

    def _tiles_rows(self, guid, tiles, specs=None):
        """(0.279) A pitched roof's tiles: which tile (chosen: laid with it — 0.281: the project's own too), laid
        again or taken away; how many, cut, the ridge tiles, their weight."""
        from ..core import roof_tiles as core_tiles
        specs = specs or list(core_tiles.TILES.values())
        self._choice_combo(t("props.tile_kind"), "roof_tiles_kind", guid,
                           [(s.name_pt if lang() == "pt" else s.name_en, s.key) for s in specs],
                           (tiles or {}).get("tile") or core_tiles.DEFAULT)
        item = self._row(t("props.tiles"), "")
        buttons = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(buttons)
        lay.setContentsMargins(0, 0, 0, 0)
        make = QtWidgets.QPushButton(t("props.tiles_again" if tiles else "props.tiles_make"))
        make.setToolTip(t("props.tiles_tip"))
        make.clicked.connect(lambda _c=False: self._emit("roof_tiles", guid, "make"))
        lay.addWidget(make)
        self.editors["roof_tiles"] = make
        if tiles:
            off = QtWidgets.QPushButton(t("props.tiles_remove"))
            off.clicked.connect(lambda _c=False: self._emit("roof_tiles", guid, "remove"))
            lay.addWidget(off)
            self.editors["roof_tiles_off"] = off
        self.tree.setItemWidget(item, 1, buttons)
        if tiles:
            self._check_row(t("props.tiles_stagger"), "roof_tiles_stagger", guid, tiles["stagger"])
            self._tiles_count_rows(tiles)

    def _tiles_count_rows(self, tiles):
        from ..core import roof_tiles as core_tiles
        spec = core_tiles.TILES.get(tiles.get("tile"))          # (0.280: tiles, sheets or panels)
        self._row(t("props.noun." + (spec.noun if spec else "tiles")),
                  t("props.tiles_count", n=tiles["tiles"], c=tiles["cut"]))   # (the user's own: tiles)
        self._row(t("props.tiles_caps"), str(tiles["caps"]))
        self._row(t("props.tiles_weight"), "{:,.0f} kg".format(tiles["weight"]).replace(",", " "))

    def _check_row(self, key, action, view, on):
        """A row with a box to tick: on_edit gets True / False."""
        item = self._row(key, "")
        box = QtWidgets.QCheckBox()
        box.setChecked(bool(on))
        box.toggled.connect(lambda checked: self._emit(action, view, bool(checked)))
        self.tree.setItemWidget(item, 1, box)
        self.editors[action] = box
        return box

    # ------------------------------------------------------------ (0.395) a parametric surface

    def _surface_value(self, v):
        """A field's value as text: a number with the decimal comma, a formula as written, a point as x; y; z."""
        if isinstance(v, bool):
            return ""
        if isinstance(v, (int, float)):
            text = ("{:d}".format(v) if isinstance(v, int) else "{:.4f}".format(v).rstrip("0").rstrip("."))
            return text.replace(".", decimal_sep())
        if isinstance(v, list):
            return "; ".join(self._surface_value(x) for x in v)
        return str(v)

    def _surface_field(self, label, action, guid, value, choices=None, curves=None):
        """One field of the surface's op, modifier or section: a choice, a tick, a curve, a picture, a number or a
        formula (text)."""
        from ..model.surface_edits import number_or_formula
        if choices is not None:
            return self._choice_combo(label, action, guid, [(t("schoice." + c) if has("schoice." + c) else
                                                             t("surface.form." + c) if has("surface.form." + c)
                                                             else t("surface.grid." + c) if has("surface.grid." + c)
                                                             else c, c) for c in choices], value)
        if isinstance(value, bool):
            return self._check_row(label, action, guid, value)
        if curves is not None:
            return self._choice_combo(label, action, guid, [(t("props.surface_none"), "")] + [(c, c) for c in curves],
                                      value or "")
        if action.endswith(":point"):
            def parse_point(s):
                vals = [number_or_formula(x) for x in s.replace(",", ".").split(";")]
                return vals if len(vals) == 3 and all(v is not None for v in vals) else None
            edit = self._text_editor(label, self._surface_value(value), action, guid, parse=parse_point)
        else:
            edit = self._text_editor(label, self._surface_value(value), action, guid,
                                     parse=lambda s: s if s.strip() else None)
        edit.setToolTip(t("props.surface_formula_tip"))
        return edit

    def _surface_list_row(self, label, on, base, guid, index, count, movable=True):
        """A modifier's / a section's row: its name; on/off, up, down, away."""
        item = self._row(label, "", bold=True)
        box = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        check = QtWidgets.QCheckBox()
        check.setToolTip(t("props.surface_on"))
        check.setChecked(bool(on))
        check.toggled.connect(lambda c, a=base + "_toggle:" + str(index): self._emit(a, guid, bool(c)))
        lay.addWidget(check)
        self.editors[base + "_toggle:" + str(index)] = check
        for text, tip, action, enabled in (("▲", "props.surface_up", "{}_move:{}:-1".format(base, index),
                                            movable and index != 0 and isinstance(index, int)),
                                           ("▼", "props.surface_down", "{}_move:{}:1".format(base, index),
                                            movable and isinstance(index, int) and index < count - 1),
                                           ("✕", "props.surface_remove", "{}_remove:{}".format(base, index), True)):
            if not movable and text in ("▲", "▼"):
                continue
            b = QtWidgets.QToolButton()
            b.setText(text)
            b.setToolTip(t(tip))
            b.setAutoRaise(True)
            b.setEnabled(enabled)
            b.clicked.connect(lambda _c=False, a=action: self._emit(a, guid, True))
            lay.addWidget(b)
            self.editors[action] = b
        lay.addStretch(1)
        self.tree.setItemWidget(item, 1, box)
        return item

    def _surface_add_combo(self, label, action, guid, choices):
        item = self._row(label, "")
        combo = QtWidgets.QComboBox()
        combo.addItem("…", "")
        for text, value in choices:
            combo.addItem(text, value)
        combo.activated.connect(lambda k: combo.itemData(k) and self._emit(action, guid, combo.itemData(k)))
        self.tree.setItemWidget(item, 1, combo)
        self.editors[action] = combo
        return combo

    def _surface_rows(self, guid, p):
        from ..core import param_surface as ps
        from ..core import surface_build as sb
        from ..ifc.param_surfaces import USAGES
        d = p.get("definition") or {}
        s = d.get("surface") or {}
        op = s.get("op", "grid")
        curves = [c.get("id") for c in d.get("curves") or ()]
        closed = [c.get("id") for c in d.get("curves") or () if c.get("closed")]
        self._choice_combo(t("ctx.surface_usage"), "surface_usage", guid,
                           [(t("surface.usage." + k), k) for k in USAGES], p.get("usage") or "estrutura")
        saved = self._group
        try:
            # the form
            self._group = self._row(t("props.surface_form"), t("surface.op." + op), bold=True)
            if curves:
                self._row(t("props.surface_curves"), t("props.surface_curves_v", n=len(curves),
                                                       k=sum(1 for c in d.get("curves") or () if c.get("source"))))
            for key in ("u", "v"):
                self._text_editor(t("sfield." + key), str(s.get(key, ps.OP_DEFAULTS[op].get(key, 8))),
                                  "surface_" + key, guid,
                                  parse=lambda x: (lambda v: v if v is not None and 1 <= v <= ps.MAX_DIVISIONS
                                                   else None)(_int_or_none(x)))
            if op == "patch":
                self._surface_field(t("sfield.rise"), "surface_field:rise", guid, s.get("rise", 2.0))
                self._surface_field(t("sfield.form"), "surface_field:form", guid, s.get("form", "cupula"),
                                    choices=ps.PATCH_FORMS)
                self._surface_field(t("sfield.grid"), "surface_field:grid", guid, s.get("grid", "quadras"),
                                    choices=ps.PATCH_GRIDS)
            elif op == "revolve":
                self._surface_field(t("sfield.angle"), "surface_field:angle", guid, s.get("angle", 360.0))
            elif op == "extrude":
                self._surface_field(t("sfield.height"), "surface_field:height", guid,
                                    (s.get("direction") or (0, 0, 3))[2])
            elif op == "loft":
                self._surface_field(t("sfield.smooth"), "surface_field:smooth", guid, bool(s.get("smooth", True)))
            elif op == "grid":
                for key, label in (("width", "sfield.width"), ("depth", "sfield.grid_depth"), ("z", "sfield.z")):
                    self._surface_field(t(label), "surface_field:" + key, guid, s.get(key))
            # the parameters (the formulas' names)
            inputs = d.get("inputs") or {}
            if inputs:
                self._group = self._row(t("props.surface_inputs"), "", parent=saved, bold=True)
                for name, value in inputs.items():
                    self._text_editor(name, self._surface_value(float(value)), "surface_input:" + name, guid,
                                      parse=lambda x: (lambda v: v if isinstance(v, float) else None)(
                                          _float_or_none(x)))
            # the modifiers, in order
            self._group = self._row(t("props.surface_modifiers"), "", parent=saved, bold=True)
            mods = d.get("modifiers") or []
            for k, m in enumerate(mods):
                head = self._surface_list_row("{}. {}".format(k + 1, t("surface.mod." + m["op"])),
                                              m.get("enabled", True), "surface_mod", guid, k, len(mods))
                group = self._group
                self._group = head
                for key, default in ps.MODIFIER_TEMPLATES[m["op"]].items():
                    value = m.get(key, default)
                    self._surface_field(t("sfield." + key), "surface_mod:{}:{}".format(k, key), guid, value,
                                        choices=ps.MODIFIER_FIELDS.get(m["op"], {}).get(key),
                                        curves=(closed if m["op"] == "trim" else curves) if key == "curve" else None)
                self._group = group
            self._surface_add_combo(t("props.surface_add_mod"), "surface_mod_add", guid,
                                    [(t("surface.mod." + k), k) for k in ps.MODIFIERS])
            # the construction, in the order it is made
            self._group = self._row(t("props.surface_build"), "", parent=saved, bold=True)
            build = d.get("build") or {}
            for name in sb.SECTIONS:
                if name not in build:
                    continue
                sec = build[name]
                head = self._surface_list_row(t("surface.build." + name), sec.get("enabled", True), "surface_build",
                                              guid, name, 0, movable=False)
                group = self._group
                self._group = head
                for key, default in sb.TEMPLATES[name].items():
                    value = sec.get(key, default)
                    action = "surface_build:{}:{}".format(name, key)
                    if key == "material":
                        self._surface_material(action, guid, name, value)
                    elif key == "mask":
                        self._choice_combo(t("sfield.mask"), action, guid,
                                           [(t("mask.none"), ""), (t("mask.choose"), "__escolher__")] +
                                           ([(value.replace("\\", "/").split("/")[-1], value)] if value else []),
                                           value or "")
                    else:
                        self._surface_field(t("sfield." + key), action, guid, value, choices=sb.CHOICES.get((name, key)))
                self._group = group
            self._surface_add_combo(t("props.surface_add_build"), "surface_build_add", guid,
                                    [(t("surface.build." + k), k) for k in sb.SECTIONS if k not in build])
            # how much
            summary = p.get("summary") or {}
            self._group = self._row(t("props.surface_parts"), str(summary.get("parts", 0)), parent=saved, bold=True)
            self._row(t("props.surface_area"), "{:.2f} m²".format(summary.get("area", 0.0)).replace(".", decimal_sep()))
            for kind_, q in (summary.get("families") or {}).items():
                bits = []
                if q.get("length_m"):
                    bits.append("{:.1f} m".format(q["length_m"]))
                if q.get("area_m2"):
                    bits.append("{:.1f} m²".format(q["area_m2"]))
                if q.get("volume_m3"):
                    bits.append("{:.2f} m³".format(q["volume_m3"]))
                label = t("sfamily." + kind_.replace(" ", "_")) if has("sfamily." + kind_.replace(" ", "_")) \
                    else kind_
                self._row(label, "{} · {}".format(q.get("count", 0), ", ".join(bits).replace(".", decimal_sep()))
                          if bits else str(q.get("count", 0)))
            self._group = saved
            for w in summary.get("warnings") or ():         # (narrow: the panel's names column is not widened)
                note = self._row(textwrap.fill(w, 34))
                note.setFirstColumnSpanned(True)
                note.setForeground(0, QtGui.QBrush(QtGui.QColor(theme.C["attention"])))
                note.setToolTip(0, w)
            # its definition and its parts, as files — (0.414) on a row of their own, the panel's whole width (in the
            # values' column they were cut)
            item = self._row("", "", parent=saved)
            item.setFirstColumnSpanned(True)
            box = QtWidgets.QWidget()
            column = QtWidgets.QVBoxLayout(box)
            column.setContentsMargins(4, 2, 4, 4)
            column.setSpacing(2)
            title = QtWidgets.QLabel(t("props.surface_file"))
            title.setStyleSheet("QLabel { font-weight: 600; background: transparent; }")
            column.addWidget(title)
            grid = QtWidgets.QGridLayout()
            grid.setSpacing(2)
            for n, key in enumerate(("csv", "text", "export", "import")):
                b = QtWidgets.QPushButton(t("props.surface_" + key))
                b.clicked.connect(lambda _c=False, a="surface_" + key: self._emit(a, guid, True))
                grid.addWidget(b, n // 2, n % 2)
                self.editors["surface_" + key] = b
            column.addLayout(grid)
            item.setSizeHint(0, box.sizeHint())
            self.tree.setItemWidget(item, 0, box)
        finally:
            self._group = saved

    def _surface_material(self, action, guid, section, value):
        from ..core import surface_build as sb
        from ..ifc import catalog
        keys = ("aco_preto", "aco", "inox", "aco_s275", "aluminio", "aluminio_branco", "aluminio_grafite", "madeira",
                "pinho", "carvalho_macico", "contraplacado", "betao_armado", "concreto", "betao_leve", "vidro",
                "vidro_fosco", "fibrocimento", "zinco", "cobre_chapa", "tela", "rede")
        named = lambda k: (catalog.MATERIALS[k].name_pt if lang() == "pt" else catalog.MATERIALS[k].name_en) \
            if k in catalog.MATERIALS else k                                                      # noqa: E731
        own = sb.FAMILIES[sb.SECTION_FAMILY[section]]
        self._choice_combo(t("sfield.material"), action, guid,
                           [(t("props.organic_material_auto", m=named(own)), "")] +
                           [(named(k), k) for k in keys if k in catalog.MATERIALS], value or "")

    def _view_type_header(self, doc, view, tpl):
        """(0.414, the owner: «os tipos devem ficar no cabeçalho como o da porta») A view's type — its view template,
        what a view's settings are kept in and given to other views — chosen on top, under its name, as an element's
        type is."""
        combo = QtWidgets.QComboBox()
        combo.setObjectName("props_type")
        combo.setToolTip(t("props.view_template_tip"))
        combo.addItem(t("props.view_no_template"), None)
        for x in doc.templates:
            combo.addItem(x.name, x.uid)
        combo.setCurrentIndex(max(0, combo.findData(tpl.uid if tpl else None)))

        def chosen(index):
            uid = combo.itemData(index)
            if uid != (tpl.uid if tpl else None):
                self._emit("view_template", view, uid)

        combo.activated.connect(chosen)
        self._set_type_combo(combo, None)
        self.editors["view_template"] = combo

    def _scale_combo(self, view, scale):
        choices = [(t("sheet.scale_auto"), None)] + [("1:{}".format(n), n) for n in sheets_model.SCALES]
        if scale and scale not in sheets_model.SCALES:
            choices.append(("1:{}".format(scale), scale))
        self._choice_combo(t("tpl.scale"), "view_scale", view, choices, scale)

    def _visibility(self, view, label, classes, hidden):
        dialog = VisibilityDialog(self, label, classes(), hidden)
        self._visibility_dialog = dialog                     # (tests fill it in)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted and set(dialog.hidden()) != set(hidden):
            self._emit("view_hidden", view, dialog.hidden())

    @staticmethod
    def _whole_group(doc, ids):
        """The group copy these ids are exactly, or None."""
        first = doc.get(ids[0])
        group = doc.ifc.group_of(ids[0]) if first is not None and first.is_bim else None
        if group is not None and set(doc.ifc.group_members(group)) == set(ids):
            return group
        return None

    def _show_group(self, doc, group, count):
        copies = len(doc.ifc.group_copies(doc.ifc.group_model(group)))
        self._row(t("props.name"), group.Name or "", bold=True)
        self._row(t("props.kind"), t("props.group_value", n=copies, m=count))
        hint = self._row(t("props.group_hint"))
        hint.setFirstColumnSpanned(True)
        hint.setForeground(0, QtGui.QBrush(theme.colour("link")))

    def _show_sketch(self, obj):
        self._row(t("props.name"), obj.name, bold=True)
        if getattr(obj, "component", None):
            self._row(t("props.kind"), t("props.component_editing", name=obj.component["component"]))
            hint = self._row(t("props.component_close_hint"))
            hint.setFirstColumnSpanned(True)
            hint.setForeground(0, QtGui.QBrush(theme.colour("link")))
            return
        mesh = obj.mesh.transformed(obj.matrix)
        curve = getattr(obj, "curve", None)
        if curve and not mesh.faces:             # (0.373) a curve: picked whole; an arc's radius, angle, segments
            total = sum(np.linalg.norm(mesh.verts[a] - mesh.verts[b]) for a, b in mesh.lines)
            self._row(t("props.kind"), t("curve." + curve.get("kind", "curve")))
            self._row(t("props.length"), _len(total))
            if curve.get("kind") == "arc":
                scale = float(np.linalg.norm(obj.matrix[:3, 0]))
                self._length_editor(t("props.arc_radius"), curves.arc_radius(curve) * scale, "arc_radius", obj.id)
                self._text_editor(t("props.arc_angle"), format_angle(abs(curve["angle"]), decimal_sep()),
                                  "arc_angle", obj.id, parse=lambda s: (lambda v: v if v is not None and
                                                                        0 < abs(v) <= 360 else None)(parse_angle(s)))
                self._text_editor(t("props.arc_segments"), str(curve.get("segments")), "arc_segments", obj.id,
                                  parse=lambda s: int(s) if s.strip().isdigit() and int(s) >= 2 else None)
            elif curve.get("kind") == "bezier":
                self._row(t("props.bezier_points"), str(len(curve["anchors"])))
            self._note(t("props.curve_hint"), theme.C["link"])
            return
        self._row(t("props.kind"), t("props.sketch"))
        if not mesh.faces:                       # loose lines (Line tool): each one editable (0.62)
            total = sum(np.linalg.norm(mesh.verts[a] - mesh.verts[b]) for a, b in mesh.lines)
            self._row(t("props.lines"), t("props.lines_value", n=len(mesh.lines), l=_len(total)))
            for k, (i, j) in enumerate(mesh.lines[:MAX_LINE_ROWS]):
                length = float(np.linalg.norm(mesh.verts[j] - mesh.verts[i]))
                self._length_editor(t("props.segment", n=k + 1), length, ("line_length", k), (obj.id, i, j))
            if len(mesh.lines) == 1:
                i, j = mesh.lines[0]
                a, b = mesh.verts[i], mesh.verts[j]
                if np.hypot(*(b - a)[:2]) > 1e-9:
                    angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360.0
                    self._text_editor(t("props.line_angle"), format_angle(angle, decimal_sep()), "line_angle",
                                      (obj.id, i, j), parse=parse_angle)
                for key, k, p in (("props.line_start", i, a), ("props.line_end", j, b)):
                    self._text_editor(t(key), _point(p), ("line_point", k), (obj.id, k), parse=_parse_point)
            self._note(t("props.lines_hint"), theme.C["link"])
            return
        if not mesh.is_closed():                 # a flat face not pulled yet
            area = sum(mesh.face_area(fi) for fi in range(len(mesh.faces)))
            self._row(t("props.area"), "{:.2f} m²".format(area).replace(".", decimal_sep()))
        box = upright_box(obj)
        if box is not None:
            self._row(t("props.dims"), "{} × {} × {}".format(_len(box.length), _len(box.width), _len(box.height)))
        else:
            self._row(t("props.dims"), t("props.free"))
        if obj.mesh.is_closed():
            vol = obj.mesh.transformed(obj.matrix).volume()
            self._row(t("props.volume"), "{:.3f} m³".format(vol).replace(".", decimal_sep()))
        hint = self._row(t("props.classify_hint"))
        hint.setFirstColumnSpanned(True)
        hint.setForeground(0, QtGui.QBrush(theme.colour("link")))

    def _type_editor(self, info, guid):
        kind = "wall" if info["kind"] == "curved_wall" else info["kind"]      # (0.103: a wall type)
        if kind in ("door", "window"):
            specs = [s for s in catalog.openings() if s.kind == kind]    # (the project's too, 0.88)
        else:
            specs = [s for s in catalog.types() if s.kind == kind]       # (the project's too, 0.87)
        names = [_type_name(s) for s in specs]
        base = info["type"] or ""
        for suffix in VARIANTS:                     # (a door hinged on the right, a mirrored window: its type)
            if base.endswith(suffix):
                base = base[:-len(suffix)]
        current = next((s for s, n in zip(specs, names) if n == base), None)
        shown = current                             # (its miniature: a variant's the mirror image of its type's)
        if current is not None and base != (info["type"] or "") and kind in ("door", "window"):
            shown = catalog.with_design(current, core_joinery.mirrored(catalog.design_of(current)))
        # (0.313) on top, under its name, as Revit's Type Selector: the types with their miniatures
        combo = type_thumbs.TypeCombo()
        combo.setObjectName("props_type")
        combo.setToolTip(t("props.type"))
        if info["type"] not in names:      # a type that is not in the catalogue: keep it listed
            combo.add_type(shown, info["type"], None)
        for s, n in zip(specs, names):
            combo.add_type(s, n, s.key)
        combo.setCurrentIndex(combo.findText(info["type"]))

        def chosen(index):
            key = combo.itemData(index)
            if key is not None and (combo.itemText(index) != info["type"] or combo.property("varies")):
                spec = catalog.BY_KEY.get(key) or catalog.OPENING_BY_KEY.get(key)
                self._emit("type", guid, spec)

        combo.activated.connect(chosen)
        self._set_type_combo(combo, type_thumbs.icon(shown) if shown is not None else None)
        self.editors["type"] = combo
        if current is not None:                                          # (0.87) its type in the type editor
            edit = self._row(t("props.type"), "")
            button = QtWidgets.QPushButton(t("props.edit_type"))
            button.setToolTip(t("props.edit_type_tip"))
            button.clicked.connect(lambda _c=False: self._emit("edit_type", guid, current))
            self.tree.setItemWidget(edit, 1, button)
            self.editors["edit_type"] = button
        if current is not None and kind in ("door", "window"):          # (0.289) its type in the generator
            row = self._row("", "")
            button = QtWidgets.QPushButton(t("joinery.button"))
            button.setToolTip(t("joinery.button_tip"))
            button.clicked.connect(lambda _c=False: self._emit("joinery", guid, current))
            self.tree.setItemWidget(row, 1, button)
            self.editors["joinery"] = button

    def _header_choice(self, tip, action, guid, choices, current, enabled=True):
        """(0.415) A type chosen on top, under the name — a list of (text, value) — as the wall's and the door's (a
        railing's railing types; a lamp's catalogue type, shown only)."""
        combo = QtWidgets.QComboBox()
        combo.setObjectName("props_type")
        combo.setToolTip(tip)
        for text, value in choices:
            combo.addItem(text, value)
        combo.setCurrentIndex(max(0, combo.findData(current)))
        combo.setEnabled(enabled)
        combo.activated.connect(lambda k: combo.itemData(k) is not None and combo.itemData(k) != current and
                                self._emit(action, guid, combo.itemData(k)))
        self._set_type_combo(combo, None)
        self.editors[action] = combo
        return combo

    def _element_type_editor(self, doc, kind, guid):
        """(0.414, the owner: «quero todos os elementos IFC tenham tipo, guardado e aplicado a outros elementos») On
        top, as Revit's Type Selector, the types saved for its kind — one chosen is put on it (on all of them, several
        chosen) —, «(sem tipo)» first; under it «Guardar como tipo…» (a new type from it) and «Atualizar o tipo»
        (its changes taken to its type and to the other elements of it)."""
        current = doc.ifc.element_type_of(guid)
        combo = QtWidgets.QComboBox()
        combo.setObjectName("props_type")
        combo.setToolTip(t("props.element_type_tip"))
        combo.addItem(t("props.no_type"), "")
        for type_guid, name in element_types.types_of(doc, kind):
            combo.addItem(name, type_guid)
        combo.setCurrentIndex(max(0, combo.findData(current or "")))

        def chosen(index):
            value = combo.itemData(index) or ""
            if value != (current or "") or combo.property("varies"):
                self._emit("element_type", guid, value or None)

        combo.activated.connect(chosen)
        self._set_type_combo(combo, None)
        self.editors["type"] = combo
        item = self._row(t("props.type"), "")
        box = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)
        save = QtWidgets.QPushButton(t("props.type_save"))
        save.setToolTip(t("props.type_save_tip"))
        save.clicked.connect(lambda _c=False: self.on_edit and QtCore.QTimer.singleShot(
            0, lambda: self.on_edit("element_type_save", guid, None)))
        row.addWidget(save)
        self.editors["element_type_save"] = save
        update = QtWidgets.QPushButton(t("props.type_update"))
        update.setToolTip(t("props.type_update_tip"))
        update.setEnabled(current is not None and element_types.differs(doc, guid))
        update.clicked.connect(lambda _c=False: self.on_edit and QtCore.QTimer.singleShot(
            0, lambda: self.on_edit("element_type_update", guid, None)))
        row.addWidget(update)
        self.editors["element_type_update"] = update
        self.tree.setItemWidget(item, 1, box)

    def _phase_editor(self, status, guid):
        """The element's phase in a renovation project (IFC Status): existing, new, to demolish…"""
        item = self._row(t("props.phase"), "")
        combo = QtWidgets.QComboBox()
        combo.addItem(t("props.no_phase"), "")
        for value in ("EXISTING", "NEW", "DEMOLISH", "TEMPORARY"):
            combo.addItem(t("phase." + value.lower()), value)
        combo.setCurrentIndex(max(0, combo.findData(status or "")))
        combo.activated.connect(lambda _k: self._emit("status", guid, combo.currentData() or None))
        self.tree.setItemWidget(item, 1, combo)
        self.editors["status"] = combo

    def _swing_buttons(self, guid, window=False):
        """A door: its hinges to the other jamb, or opening to the other side — (0.290) a window: to the other side."""
        item = self._row(t("props.swing_window" if window else "props.swing"), "")
        box = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)
        buttons = (("flip_hinge", "props.flip_hinge", "props.flip_hinge_tip"),
                   ("flip_side", "props.flip_side", "props.flip_side_tip"))
        if window:
            buttons = (("flip_side", "props.flip_side", "props.flip_side_window_tip"),)
        for action, text, tip in buttons:
            button = QtWidgets.QPushButton(t(text))
            button.setToolTip(t(tip))
            button.clicked.connect(lambda _c=False, a=action: self._emit(a, guid, None))
            row.addWidget(button)
            self.editors[action] = button
        self.tree.setItemWidget(item, 1, box)

    def _constraint_rows(self, doc, info, guid, height_action):
        """A wall's or column's base and top, as Revit's (0.73): base storey and offset; top — not connected
        (its height typed) or up to a storey, with an offset (its height follows)."""
        c = info.get("constraints")
        height = info["params"]["height"]
        if c is None:
            self._length_editor(t("props.height"), height, height_action, guid)
            return
        storeys = [(name or g, g) for g, name, _z in doc.ifc.storeys()]
        self._choice_combo(t("props.base_level"), "c_base", guid, storeys, c["base"])
        self._signed_length_editor(t("props.base_offset"), c["base_offset"], "c_base_offset", guid)
        tops = [(t("props.top_free"), None)] + storeys
        current = c["top"]
        if c.get("top_slab"):                          # (0.106) tied to a slab's underside
            slab = doc.get(c["top_slab"])
            tops.append((t("props.top_slab", name=slab.name if slab else ""), "slab"))
            current = "slab"
        if c.get("top_roof"):                          # (0.112) …or a roof's
            roof = doc.get(c["top_roof"])
            tops.append((t("props.top_roof", name=roof.name if roof else ""), "slab"))
            current = "slab"
        self._choice_combo(t("props.top"), "c_top", guid, tops, current)
        if c["top"] or c.get("top_slab"):
            self._signed_length_editor(t("props.top_offset"), c["top_offset"], "c_top_offset", guid)
            self._row(t("props.height"), _len(height))
        elif c.get("top_roof"):                        # (its height: the roof's underside over it)
            self._row(t("props.height"), _len(height))
        else:
            self._length_editor(t("props.height_free"), height, height_action, guid)

    def _signed_length_editor(self, key, meters, action, guid):
        """A length that may be 0 or below (an offset)."""
        text = _len(abs(meters)).replace("~ ", "")
        return self._text_editor(key, ("-" + text) if meters < -5e-4 else text, action, guid, parse=parse_length)

    def _show_bim(self, doc, obj):
        info = doc.ifc.describe(obj.id)
        if info is None:
            return
        guid, kind, p = obj.id, info["kind"], info["params"]
        # (0.185) on top its name and its type; the rows in groups: identification, constraints and dimensions,
        # materials, phase, the IFC's data
        self._set_header(info["name"], info.get("type") or info["class"], _kind_icon(kind or obj.ifc_class))
        self._begin(t("props.g.identity"))
        if kind:
            self._text_editor(t("props.name"), info["name"], "name", guid)
        else:
            self._row(t("props.name"), info["name"], bold=True)
        self._row(t("props.class"), info["class"])
        if kind == "component":
            self._row(t("props.component"), t("props.component_value", name=info["type"], n=info.get("instances", 1)))
            hint = self._row(t("props.component_hint"))
            hint.setFirstColumnSpanned(True)
            hint.setForeground(0, QtGui.QBrush(theme.colour("link")))
            item = self._row("", "")                       # (0.281) registered as a tile of the user's own
            button = QtWidgets.QPushButton(t("props.register_tile"))
            button.setToolTip(t("props.register_tile_tip"))
            button.clicked.connect(lambda _c=False: self._emit("register_tile", guid, info["type"]))
            self.tree.setItemWidget(item, 1, button)
            self.editors["register_tile"] = button
        elif kind in element_types.KINDS:          # (0.414) its saved types: chosen on top, saved, brought up to date
            self._element_type_editor(doc, kind, guid)
            spec = p.get("spec")                   # (0.415: a stair's slab, a ceiling's board… from the catalogue)
            if spec is not None:
                self._row(t("props.catalog_type"), _type_name(spec))
        elif kind == "railing":                    # (0.415) its railing types, on top
            self._header_choice(t("props.railing_type"), "railing_style", guid,
                                [(name, key) for key, name in p["types"]], p["type"])
        elif kind in ("light", "air_terminal", "equipment", "fixture", "electrical", "profile"):    # (shown only)
            spec = p.get("spec")                   # (0.415: on top too — a catalogue's, chosen when placed)
            self._header_choice(t("props.type_fixed"), "type_fixed", guid,
                                [(_type_name(spec) if spec is not None else info["type"] or "—", None)], None,
                                enabled=False)
        elif kind == "roof":                       # (0.278) a roof type; made before: its slab type's name, listed
            spec = p.get("spec")
            self._type_editor(dict(info, type=info["type"] or (_type_name(spec) if spec is not None else "")), guid)
        elif kind and kind != "fitting":                # (a bend's type follows its pipe's: shown only)
            self._type_editor(info, guid)
        else:
            self._row(t("props.type"), info["type"])
        self._row(t("props.storey"), info["storey"])
        self._row("GlobalId", info["guid"])
        painted = self._paint_text(doc, guid)               # (0.391) its faces painted: each paint, how much
        if painted:
            self._row(t("props.paint"), painted)
        self._begin(t("props.g.parameters"))

        if kind == "wall":
            self._length_editor(t("props.length"), p["length"], "length", guid)
            self._constraint_rows(doc, info, guid, "height")
            self._row(t("props.thickness"), t("props.by_type", v=_len(p["thickness"])))
            item = self._row(t("props.profile_drawn") if p.get("profiled") else t("props.profile_wall"), "")
            button = QtWidgets.QPushButton(t("act.edit_profile"))                     # (0.109)
            button.setToolTip(t("tip.edit_profile"))
            button.clicked.connect(lambda _c=False: self._emit("edit_profile", guid, None))
            self.tree.setItemWidget(item, 1, button)
            self.editors["edit_profile"] = button
        elif kind == "slab":
            shape = p.get("shape") or "retangulo"
            if shape == "retangulo":
                self._length_editor(t("props.lx"), p["lx"], "lx", guid)
                self._length_editor(t("props.ly"), p["ly"], "ly", guid)
            elif shape == "circulo":                       # (0.100) a round slab: its radius
                self._length_editor(t("props.radius"), p["radius"], "slab_radius", guid)
            self._row(t("props.thickness"), t("props.by_type", v=_len(p["thickness"])))
            if p.get("area") is not None:
                self._row(t("props.area"), "{:.2f} m²".format(p["area"]).replace(".", decimal_sep()))
            self._choice_combo(t("props.slab_function"), "slab_function", guid,
                               [(t("slabfn." + f), f) for f in core_slabs.FUNCTIONS], p.get("function"))
            from ..core import actions as core_actions                  # (0.218) its own use, for its loads
            self._choice_combo(t("props.slab_use"), "slab_use", guid,
                               [(t("props.slab_use_project"), "")] + [(t("actions.use." + k), k)
                                                                         for k in core_actions.USES], p.get("use") or "")
            if shape != "circulo":                         # its corners as grips (the rectangle's too)
                item = self._row(t("props.outline"), "")
                button = QtWidgets.QPushButton(t("act.edit_outline"))
                button.setToolTip(t("tip.edit_outline"))
                button.clicked.connect(lambda _c=False: self._emit("edit_outline", guid, None))
                self.tree.setItemWidget(item, 1, button)
                self.editors["edit_outline"] = button
        elif kind == "ceiling":                            # (0.118) its style, its height over its storey
            from ..core import ceilings as core_ceilings
            self._choice_combo(t("ctx.ceiling_style"), "ceiling_style", guid,
                               [(t("ceilstyle." + s), s) for s in core_ceilings.STYLES], p["style"])
            self._length_editor(t("ctx.ceiling_height"), p["height"], "ceiling_height", guid)
            self._length_editor(t("ctx.ceiling_gap"), p["gap"], "ceiling_gap", guid)          # (0.119)
            self._length_editor(t("ctx.bulkhead"), p["bulkhead"], "ceiling_bulkhead", guid)
            if p["bulkhead"] > 0:
                self._length_editor(t("ctx.bulkhead_drop"), p["drop"], "ceiling_drop", guid)
            self._row(t("props.area"), "{:.2f} m²".format(p["area"]).replace(".", decimal_sep()))
        elif kind == "flooring":                           # (0.415) a floor finish: its finish (material, thickness)
            from ..ifc.coverings import FLOORINGS
            self._choice_combo(t("ctx.flooring"), "flooring_finish", guid,
                               [(t("flooring." + k), k) for k in FLOORINGS], p["finish"])
            self._row(t("props.thickness"), _len(p["thickness"]))
            self._row(t("props.area"), "{:.2f} m²".format(p["area"]).replace(".", decimal_sep()))
            item = self._row(t("props.outline"), "")
            button = QtWidgets.QPushButton(t("act.edit_outline"))                  # (0.410: its outline, as a slab's)
            button.clicked.connect(lambda _c=False: self._emit("edit_outline", guid, None))
            self.tree.setItemWidget(item, 1, button)
            self.editors["edit_outline"] = button
        elif kind == "roof_tiles":                         # (0.279) a roof's tiles: its roof, how many, their weight
            item = self._row(t("props.tiles_roof"), p.get("roof_name") or "")
            if p.get("roof"):
                button = QtWidgets.QPushButton(t("props.tiles_select_roof"))
                button.clicked.connect(lambda _c=False: self._emit("select_element", p["roof"], None))
                self.tree.setItemWidget(item, 1, button)
                self.editors["tiles_roof"] = button
            if p.get("tiles") is not None:
                self._tiles_count_rows(p)
        elif kind == "cladding":                           # (0.119) a wall's finish: what, how high, on which wall
            from ..core.ceilings import FINISHES
            self._choice_combo(t("ctx.finish"), "cladding_finish", guid,
                               [(t("finish." + f), f) for f in FINISHES], p["finish"])
            self._length_editor(t("ctx.finish_height") if p.get("whole", True) else t("props.region_top"),
                                p["height"] or p.get("top", 0.0), "cladding_height", guid)
            d = p.get("pattern")
            if d:                                          # (0.173) a pattern's measures
                if p["finish"] in ("ripado", "canelado", "ondulado"):
                    self._length_editor(t("props.rib_width" if p["finish"] == "ondulado" else "props.slat_width"),
                                        d["width"], "cladding_width", guid)
                    if p["finish"] in ("ripado", "ondulado"):
                        self._length0_editor(t("props.slat_gap"), d["gap"], "cladding_gap", guid)
                    self._choice_combo(t("props.slat_direction"), "cladding_direction", guid,
                                       [(t("slat.vertical"), "vertical"), (t("slat.horizontal"), "horizontal")],
                                       d["direction"])
                    if p["finish"] == "ondulado":          # (0.175) the wave
                        self._length_editor(t("props.wave_amplitude"), d["amplitude"], "cladding_amplitude", guid)
                        self._length_editor(t("props.wave_length"), d["wavelength"], "cladding_wavelength", guid)
                        self._text_editor(t("props.wave_shift"), format_angle(d["shift"], decimal_sep()),
                                          "cladding_shift", guid, parse=parse_angle)
                        self._length0_editor(t("props.wave_depth"), d["depth"], "cladding_depth", guid)
                    self._row(t("props.slats"), str(d["count"]))
                else:
                    from ..core.surfaces import GRIDS, HOLE_SHAPES
                    from ..tools.perforated import CHOOSE
                    self._choice_combo(t("props.hole_shape"), "cladding_hole", guid,
                                       [(t("hole." + k), k) for k in HOLE_SHAPES], d["hole"])      # (0.389)
                    self._choice_combo(t("props.hole_grid"), "cladding_grid", guid,
                                       [(t("grid." + k), k) for k in GRIDS], d["grid"])
                    self._length_editor(t("props.hole_diameter"), d["diameter"], "cladding_diameter", guid)
                    self._length_editor(t("props.hole_pitch"), d["pitch"], "cladding_pitch", guid)
                    self._length0_editor(t("props.hole_margin"), d["margin"], "cladding_margin", guid)
                    self._length_editor(t("props.sheet_w"), d["sheet_w"], "cladding_sheet_w", guid)
                    self._length_editor(t("props.sheet_h"), d["sheet_h"], "cladding_sheet_h", guid)
                    self._length0_editor(t("props.sheet_joint"), d["joint"], "cladding_joint", guid)
                    masks = [(t("mask.none"), "")]
                    if d["mask"]:
                        name = os.path.basename(d["mask"])
                        masks.append((name if d.get("mask_found") else t("props.mask_missing", f=name), d["mask"]))
                    masks.append((t("mask.choose"), CHOOSE))
                    self._choice_combo(t("props.mask"), "cladding_mask", guid, masks, d["mask"])
                    self._row(t("props.holes"), t("props.holes_v", n=d["count"],
                                                  a="{:.0f}".format(100 * d["open_area"])))
            if "start" in p:                               # (0.389) the rectangle of the face it covers
                if p.get("whole"):
                    self._row(t("props.region_whole"), t("props.region_whole_v"))
                else:
                    self._length0_editor(t("props.region_start"), p["start"], "cladding_start", guid)
                    self._length_editor(t("props.region_end"), p["end"], "cladding_end", guid)
                    self._length0_editor(t("props.region_base"), p["base"], "cladding_base", guid)
            self._row(t("props.host"), p["wall"])
            if p.get("under"):                             # (0.178) a layer over others
                self._row(t("props.layer"), t("props.layer_v", n=p["layer"], under=", ".join(p["under"])))
            self._row(t("props.area"), "{:.2f} m²".format(p["area"]).replace(".", decimal_sep()))
        elif kind == "profile":                            # (0.174) which section, its size, how high, which side
            from ..core.profiles import CUSTOM, PROFILES                # (0.245: the project's own too)
            self._choice_combo(t("ctx.profile"), "profile_profile", guid,
                               [(t("profile." + k), k) for k in PROFILES] + [(n, CUSTOM + n) for n in p.get("own", ())],
                               p["profile"])
            self._length_editor(t("props.profile_width"), p["width"], "profile_width", guid)
            self._length_editor(t("props.profile_height"), p["height"], "profile_height", guid)
            self._length0_editor(t("ctx.profile_foot"), p["foot"], "profile_foot", guid)
            if p["room"]:
                self._row(t("ctx.profile_shape"), t("profshape.room"))
            else:
                self._choice_combo(t("ctx.profile_side"), "profile_side", guid,
                                   [(t("profside.left"), 1), (t("profside.right"), -1)], p["side"])
            self._row(t("props.length"), _len(p["length"]))
        elif kind == "organic_roof":                       # (0.390) its form, its system, its pieces
            from ..core import organic_roof as core_or
            from ..ifc import catalog
            from ..ifc.organic_roofs import MATERIALS, system_material
            spec = lambda k: catalog.MATERIALS[k]                           # noqa: E731
            named = lambda k: spec(k).name_pt if lang() == "pt" else spec(k).name_en    # noqa: E731
            self._choice_combo(t("ctx.organic_form"), "organic_form", guid,
                               [(t("organic.form." + k), k) for k in core_or.FORMS], p["form"])
            self._choice_combo(t("ctx.organic_system"), "organic_system", guid,
                               [(t("organic.system." + k), k) for k in core_or.SYSTEMS], p["system"])
            self._length_editor(t("props.organic_base"), p["base"], "organic_base", guid)
            self._length_editor(t("ctx.organic_rise"), p["rise"], "organic_rise", guid)
            self._length_editor(t("ctx.organic_spacing"), p["spacing"], "organic_spacing", guid)
            self._text_editor(t("props.organic_angle"), format_angle(p["angle"], decimal_sep()), "organic_angle",
                              guid, parse=parse_angle)
            if p["system"] == "casca":
                self._length_editor(t("props.organic_thickness"), p["thickness"], "organic_thickness", guid)
            else:
                self._length_editor(t("props.organic_diameter"), p["diameter"], "organic_diameter", guid)
            self._choice_combo(t("props.organic_material"), "organic_material", guid,
                               [(t("props.organic_material_auto", m=named(system_material(dict(p, material="")))), "")]
                               + [(named(k), k) for k in MATERIALS], p["material"])
            self._check_row(t("props.organic_ring"), "organic_ring", guid, p["ring"])
            if p["ring"]:
                self._length_editor(t("props.organic_ring_width"), p["ring_width"], "organic_ring_width", guid)
                self._length_editor(t("props.organic_ring_height"), p["ring_height"], "organic_ring_height", guid)
            self._choice_combo(t("props.organic_supports"), "organic_supports", guid,
                               [(t("organic.supports." + k), k) for k in core_or.SUPPORTS], p["supports"])
            if p["supports"] != "nenhum":
                if p["supports"] == "espacados":
                    self._length_editor(t("props.organic_support_spacing"), p["support_spacing"],
                                        "organic_support_spacing", guid)
                self._length_editor(t("props.organic_support_diameter"), p["support_diameter"],
                                    "organic_support_diameter", guid)
            if "area" in p:
                self._row(t("props.area"), "{:.2f} m²".format(p["area"]).replace(".", decimal_sep()))
                if p["system"] != "casca":
                    self._row(t("props.organic_bars"), t("props.organic_bars_v", n=p["bars"],
                                                         l="{:.1f}".format(p["bars_length"]).replace(".", decimal_sep())))
                if p["system"] == "envidracada":
                    self._row(t("props.organic_glass"), "{:.2f} m²".format(p["glass"]).replace(".", decimal_sep()))
                if p["supports"] != "nenhum":
                    self._row(t("props.organic_support_count"), str(p["support_count"]))
        elif kind == "param_surface":                      # (0.395) its form, its modifiers, its construction
            self._surface_rows(guid, p)
        elif kind == "light":                              # (0.119)
            self._row(t("ctx.light"), t("light." + p["light"]))
        elif kind == "air_terminal":                       # (0.138) which, the air it moves
            self._row(t("ctx.air_terminal"), t("terminal." + p["terminal"]))
            self._row(t("props.air"), t("air." + p["air"]))
        elif kind == "equipment":                          # (0.139) which, its base's height
            self._row(t("ctx.equipment"), t("equipment." + p["equipment"]))
            self._row(t("ctx.equipment_base"), _len(p["base"]))
        elif kind == "electrical":                         # (0.143) which, how high
            self._row(t("ctx.electrical"), t("point." + p["point"]))
            self._row(t("props.height"), _len(p["height"]))
        elif kind == "fitting":                            # (0.141) a bend's, a tee's system: its run's
            self._system_combo(info, guid, "duct" if info["class"] == "IfcDuctFitting" else "pipe")
        elif kind == "terrain":                            # (0.155) its points, extent, heights; contours, base
            self._row(t("props.terrain_points"), str(p["points"]))
            self._row(t("props.area"), "{:.2f} m²".format(p["area"]).replace(".", decimal_sep()))
            self._row(t("props.terrain_heights"), "{} — {}".format(format_length(p["low"], decimal_sep()),
                                                                   format_length(p["high"], decimal_sep())))
            self._length_editor(t("props.terrain_interval"), p["interval"], "terrain_interval", guid)
            self._length_editor(t("props.terrain_depth"), p["depth"], "terrain_depth", guid)
            if p.get("platforms"):                         # (0.157) its platforms and their earth
                self._row(t("props.platforms"), str(p["platforms"]))
                self._row(t("props.earthworks"), "{:.1f} m³ / {:.1f} m³".format(p["cut"], p["fill"]).replace(
                    ".", decimal_sep()))
        elif kind == "appliance":                          # (0.171) which; its connections (shown below)
            self._row(t("ctx.appliance"), t("appliance." + p["kind"]))
        elif kind == "cabinet":                            # (0.169) a module: its kind, sizes, fronts, handle
            from ..core import cabinets as core_cab
            self._choice_combo(t("ctx.cabinet"), "cab_kind", guid,
                               [(t("cabinet.kind." + k), k) for k in core_cab.KINDS], p["kind"])
            self._length_editor(t("props.width"), p["width"], "cab_width", guid)
            self._length_editor(t("props.cab_height"), p["height"], "cab_height", guid)
            self._length_editor(t("props.cab_depth"), p["depth"], "cab_depth", guid)
            if p["kind"] == "wall":
                self._length_editor(t("props.cab_elevation"), p["elevation"], "cab_elevation", guid)
            else:
                self._length_editor(t("props.cab_plinth"), p["plinth"], "cab_plinth", guid)
            self._choice_combo(t("ctx.fronts"), "cab_fronts", guid,
                               [(t("cabinet.fronts." + k), k) for k in core_cab.FRONTS], p["fronts"])
            if p["fronts"] in ("doors", "sliding"):         # (0.241: sliding doors, 2 to 4)
                self._choice_combo(t("props.cab_doors"), "cab_doors", guid,
                                   [(str(n), n) for n in range(2 if p["fronts"] == "sliding" else 1, 5)],
                                   max(p["doors"], 2) if p["fronts"] == "sliding" else p["doors"])
            if p["kind"] in ("base", "wall") and p["fronts"] == "doors":     # (0.239) a blind corner unit
                if not p.get("arm"):
                    self._length_editor(t("props.cab_blind"), p.get("blind", 0.0), "cab_blind", guid)
                if not p.get("blind"):                                        # (0.240) an L corner unit
                    self._length_editor(t("props.cab_arm"), p.get("arm", 0.0), "cab_arm", guid)
                if p.get("blind") or p.get("arm"):
                    self._choice_combo(t("props.cab_corner_side"), "cab_corner_side", guid,
                                       [(t("cabinet.side." + s), s) for s in core_cab.SIDES], p.get("corner_side"))
            if p["fronts"] == "drawers":
                self._choice_combo(t("props.cab_drawers"), "cab_drawers", guid,
                                   [(str(n), n) for n in range(1, 7)], p["drawers"])
            if p["fronts"] != "drawers":                   # (0.172) its compartments, each with what it holds
                fills = [f.strip() for f in (p["interior"] or "").split(",") if f.strip()] or ["shelves"]
                self._choice_combo(t("props.cab_compartments"), "cab_compartments", guid,
                                   [(str(n), n) for n in range(1, 6)], len(fills))
                spans = core_cab.Cabinet.of(p["kind"], **{k: v for k, v in p.items() if k in (
                    "width", "fronts", "interior", "splits")}).compartment_spans() if len(fills) > 1 else []
                for k, fill in enumerate(fills):
                    self._choice_combo(t("props.cab_compartment", k=k + 1), "cab_fill_{}".format(k), guid,
                                       [(t("cabinet.fill." + f), f) for f in core_cab.FILLS], fill)
                    if spans:                               # (0.244) its width: its division moves
                        self._length_editor(t("props.cab_cwidth", k=k + 1), spans[k][1] - spans[k][0],
                                            "cab_cwidth_{}".format(k), guid)
                self._choice_combo(t("props.cab_shelves"), "cab_shelves", guid,
                                   [(str(n), n) for n in range(0, 9)], p["shelves"])
            if p["fronts"] != "open":                       # (0.243) their finish: material and colour
                self._choice_combo(t("props.cab_finish"), "cab_finish", guid,
                                   [(t("cabinet.finish." + k), k) for k in core_cab.FINISHES], p.get("finish"))
            self._choice_combo(t("ctx.handle"), "cab_handle", guid,
                               [(t("cabinet.handle." + k), k) for k in core_cab.HANDLES], p["handle"])
            self._row(t("props.cab_overall"), "{} × {} × {}".format(_len(p["width"]), _len(p["overall_depth"]),
                                                                    _len(p["top"])))
        elif kind == "rebar":                              # (0.166) a set of bars: its member, its bars
            self._row(t("props.rebar_host"), p["host_name"])
            self._row(t("props.rebar_mark"), p["mark"])
            self._row(t("props.rebar_bars"), t("props.rebar_bars_v", n=p["count"], d=p["diameter"],
                                               l=_len(p["length"]), s=p["shape"]))
            self._row(t("props.rebar_weight"), "{:.1f} kg".format(p["weight"]).replace(".", decimal_sep()))
        elif kind == "fixture":                            # (0.140) which; its connections, joined or free
            self._row(t("ctx.fixture"), t("fixture." + p["fixture"]))
            self._row(t("props.connections_of"), " · ".join(
                "{}: {}".format(t("conn." + name) if name in ("drain", "cold", "hot") else name,
                                t("props.end_joined") if joined else t("props.end_free"))
                for name, joined in p["ports"]))
        elif kind == "curtain_wall":                       # (0.117) its length, height, spacings
            self._length_editor(t("props.length"), p["length"], "cw2_length", guid)
            self._length_editor(t("props.height"), p["height"], "cw2_height", guid)
            self._length_editor(t("ctx.mullions"), p["mullions"], "cw2_mullions", guid)
            self._length_editor(t("ctx.transoms"), p["transoms"], "cw2_transoms", guid)
            self._check_row(t("props.cw_embed"), "cw2_embed", guid, p.get("embed"))         # (0.188) in its wall
            if info.get("host"):                           # (its wall: the row every filling has, below)
                self._length0_editor(t("props.from_start"), p["from_start"], "from_start", guid)
                self._length0_editor(t("props.to_end"), p["to_end"], "to_end", guid)
            if p.get("panels"):                            # (0.181) the cells that are not glass
                self._row(t("props.cw_panels"), ", ".join("{} × {}".format(n, t("cwpanel." + k).lower())
                                                          for k, n in p["panels"].items()))
        elif kind == "railing":                            # (0.115) its type (0.258; 0.415: on top) and height
            edit = self._row(t("props.type"), "")          # (0.260) its type in the railing type editor
            button = QtWidgets.QPushButton(t("props.edit_type"))
            button.setToolTip(t("props.edit_railing_type_tip"))
            button.clicked.connect(lambda _c=False: self._emit("edit_railing_type", guid, p["type"]))
            self.tree.setItemWidget(edit, 1, button)
            self.editors["edit_railing_type"] = button
            self._length_editor(t("props.height"), p["height"], "railing_height", guid)
            self._row(t("props.length"), _len(p["length"]))
            if not p["closed"]:                            # (0.282) its handrail on past its ends (DL 163/2006)
                base, top = p.get("extend") or (0.0, 0.0)
                self._length0_editor(t("props.rail_ext_base"), base, "railing_ext_base", guid)
                self._length0_editor(t("props.rail_ext_top"), top, "railing_ext_top", guid)
                note = self._row(t("props.rail_ext_note"))
                note.setFirstColumnSpanned(True)
                note.setForeground(0, QtGui.QBrush(theme.colour("note")))
        elif kind == "stair":                              # (0.114) its form, turn, width, tread, rise
            from ..core import stairs as core_stairs
            self._choice_combo(t("props.stair_form"), "stair_form", guid,
                               [(t("stairform." + f), f) for f in core_stairs.FORMS], p["form"])
            if p["form"] != "straight":
                self._choice_combo(t("props.stair_turn"), "stair_turn", guid,
                                   [(t("stairturn." + s), s) for s in core_stairs.TURNS], p["turn"])
            self._length_editor(t("props.width"), p["width"], "stair_width", guid)
            self._length_editor(t("props.going"), p["going"], "stair_going", guid)
            self._length_editor(t("props.rise"), p["rise"], "stair_rise", guid)
            self._row(t("props.risers"), "{} × {}".format(p["risers"], _len(p["riser"])))
            self._row(t("props.blondel"), _len(2 * p["riser"] + p["going"]))
        elif kind == "roof":                               # (0.111) its form, slope, overhang, height
            from ..core import roofs as core_roofs
            if p["form"] == "blocks":                      # (0.262) by blocks: how many; its slope / overhang for all
                self._row(t("props.roof_form"), t("roof.by_blocks", n=p["blocks"]))
                edit = self._row("", "")                   # (0.263) its blocks in the block editor
                button = QtWidgets.QPushButton(t("props.edit_blocks"))
                button.setToolTip(t("props.edit_blocks_tip"))
                button.clicked.connect(lambda _c=False: self._emit("edit_roof_blocks", guid, None))
                self.tree.setItemWidget(edit, 1, button)
                self.editors["edit_roof_blocks"] = button
            else:
                self._choice_combo(t("props.roof_form"), "roof_form", guid,
                                   [(t("roofform." + f), f) for f in core_roofs.FORMS], p["form"])
            if p["form"] != "flat":
                self._text_editor(t("props.roof_slope"), format_angle(p["slope"], decimal_sep()), "roof_slope", guid,
                                  parse=lambda s: (lambda v: v if v is not None and 0 <= v < 80 else None)(
                                      parse_angle(s)))
            self._text_editor(t("props.overhang"), _len(p["overhang"]).replace("~ ", ""), "roof_overhang", guid,
                              parse=lambda s: (lambda v: v if v is not None and v >= 0 else None)(parse_length(s)))
            self._signed_length_editor(t("props.eave"), p["eave"], "roof_eave", guid)
            self._row(t("props.thickness"), t("props.by_type", v=_len(p["thickness"])))
            self._row(t("props.roof_area"), "{:.2f} m²".format(p["area"]).replace(".", decimal_sep()))
            self._row(t("props.projected"), "{:.2f} m²".format(p["projected"]).replace(".", decimal_sep()))
            for k, v in (p.get("edges") or {}).items():    # (0.265) by blocks: its eaves', ridges'… lengths
                if v > 1e-6:
                    self._row(t("props.edge." + k), _len(v))
            if p.get("pitched"):                           # (0.276) its carpentry: made, its pieces; or made here
                carpentry = p.get("carpentry")
                item = self._row(t("props.carpentry"), "")
                buttons = QtWidgets.QWidget()
                lay = QtWidgets.QHBoxLayout(buttons)
                lay.setContentsMargins(0, 0, 0, 0)
                make = QtWidgets.QPushButton(t("props.carpentry_again" if carpentry else "props.carpentry_make"))
                make.setToolTip(t("props.carpentry_tip"))
                make.clicked.connect(lambda _c=False: self._emit("roof_carpentry", guid, "make"))
                lay.addWidget(make)
                self.editors["roof_carpentry"] = make
                if carpentry:
                    sizes = QtWidgets.QPushButton(t("props.carpentry_sizes"))             # (0.277)
                    sizes.clicked.connect(lambda _c=False: self._emit("roof_carpentry", guid, "sizes"))
                    lay.addWidget(sizes)
                    self.editors["roof_carpentry_sizes"] = sizes
                    off = QtWidgets.QPushButton(t("props.carpentry_remove"))
                    off.clicked.connect(lambda _c=False: self._emit("roof_carpentry", guid, "remove"))
                    lay.addWidget(off)
                    self.editors["roof_carpentry_off"] = off
                self.tree.setItemWidget(item, 1, buttons)
                for role, (n, length, volume) in (carpentry or {}).items():
                    self._row(t("carp." + role), t("props.carpentry_row", n=n, m=_len(length),
                                                    v="{:.3f}".format(volume).replace(".", decimal_sep())))
                self._tiles_rows(guid, p.get("tiles"), p.get("tile_specs"))
        elif kind == "curved_wall":                        # (0.103) its axis radius, its sweep, its height
            self._length_editor(t("props.radius_axis"), p["radius"], "cw_radius", guid)
            if abs(abs(p["sweep"]) - 360.0) > 1e-6:
                self._text_editor(t("props.sweep"), format_angle(abs(p["sweep"]), decimal_sep()), "cw_sweep", guid,
                                  parse=lambda s: (lambda v: v if v is not None and 0 < v <= 360 else None)(
                                      parse_angle(s)))
            self._row(t("props.length_axis"), _len(p["length"]))
            self._length_editor(t("props.height"), p["height"], "cw_height", guid)
            self._row(t("props.thickness"), t("props.by_type", v=_len(p["thickness"])))
        elif kind == "ramp":                               # (0.101) its length, width, rise; its slope
            self._length_editor(t("props.length"), p["length"], "ramp_length", guid)
            self._length_editor(t("props.width"), p["width"], "ramp_width", guid)
            self._text_editor(t("props.rise"), _len(p["rise"]).replace("~ ", ""), "ramp_rise", guid,
                              parse=lambda s: (lambda v: v if v is not None and v >= 0 else None)(parse_length(s)))
            self._row(t("props.slope"), "{:.1f} %".format(100 * p["slope"]).replace(".", decimal_sep()))
            self._row(t("props.thickness"), t("props.by_type", v=_len(p["thickness"])))
        elif kind == "column":
            self._constraint_rows(doc, info, guid, "column_height")
        elif kind == "beam":                               # (0.66)
            self._length_editor(t("props.length"), p["length"], "beam_length", guid)
            self._length_editor(t("props.beam_top"), p["top"], "beam_top", guid)
        elif kind in ("pipe", "duct", "conduit"):          # (0.69; a conduit: 0.146)
            self._length_editor(t("props.length"), p["length"], "segment_length", guid)
            self._length_editor(t("props.axis_z"), p["z"], "segment_z", guid)
            if kind != "conduit":
                self._system_combo(info, guid, kind)      # (0.141)
            if p.get("vertical"):                          # (0.136) a stack, a riser: from its top / foot
                self._row(t("props.vertical_from"), "{} → {}".format(_len(p["z"]), _len(p["end_z"])))
            elif abs(p.get("slope", 0.0)) > 1e-9:          # (0.136) a pipe that falls along it
                self._row(t("props.slope"), format_slope(p["slope"], decimal_sep()))
                self._row(t("props.end_z"), _len(p["end_z"]))
        elif kind == "footing":                            # (0.68) a pad's size is its type's
            if p["strip"]:
                self._length_editor(t("props.length"), p["length"], "footing_length", guid)
            else:
                self._row(t("props.size"), t("props.by_type", v="{} × {}".format(_len(p["length"]), _len(p["width"]))))
            self._length_editor(t("props.footing_top"), p["top"], "footing_top", guid)
        elif kind in ("door", "window"):
            self._text_editor(t("props.mark"), p.get("mark", ""), "mark", guid)         # (0.110)
            self._length_editor(t("props.from_start"), p["from_start"], "from_start", guid)
            self._length_editor(t("props.to_end"), p["to_end"], "to_end", guid)
            if kind == "window":
                self._length_editor(t("props.sill"), p["sill"], "sill", guid)
                self._swing_buttons(guid, window=True)             # (0.290: to open to the other side)
            else:
                self._swing_buttons(guid)
        if info.get("connections") is not None:           # a pipe's / bend's ends: what each is connected to (0.74)
            ends = [t("props.end_n", n=k + 1, what=name or t("props.end_free"))
                    for k, name in enumerate(info["connections"])]
            self._row(t("props.connections"), " · ".join(ends) or t("props.end_none"))
        if info.get("size"):
            self._row(t("props.size"), "{} × {}".format(_len(info["size"][0]), _len(info["size"][1])))
        if info.get("host"):
            self._row(t("props.host"), info["host"])
        if info["layers"] or info["profile"]:
            self._begin(t("props.g.materials"))               # (the type's: "do tipo" — every one of it)
        if info["layers"]:
            layers = self._row(t("props.layers"), _cm(sum(th for _, th in info["layers"])), bold=True)
            for name, thickness in info["layers"]:
                self._row(name, _cm(thickness), layers)
        if info["profile"]:
            name, x, y = info["profile"]
            size = "Ø {}".format(_cm(x)) if y is None else "{} × {}".format(_cm(x), _cm(y))
            self._row(t("props.profile"), "{} — {}".format(name, size))
        if info.get("can_status"):
            self._begin(t("props.g.phase"))
            self._phase_editor(info.get("status"), guid)

        self._begin(t("props.g.ifc"))
        from ..model import keynotes                       # (0.194) its keynote (its type's: all of them have it)
        code, words = info.get("keynote") or ("", "")
        own = doc.ifc.keynote_table() if hasattr(doc.ifc, "keynote_table") else {}   # (0.248: the project's own)
        notes = [(t("keynote.none"), "")] + keynotes.choices(lang(), own)
        if code and code not in keynotes.BY_CODE and code not in own:
            notes.append(("{} — {}".format(code, words), code))
        self._choice_combo(t("props.keynote"), "keynote", guid, notes, code)
        scale = doc.ifc.unit_scale
        standard = info.get("ifc_data")
        if standard is not None and kind is not None:      # (0.266) its standard set: every property, in place
            self._ifc_data_rows(guid, standard, scale)
        for pset_name, props in sorted(info["psets"].items()):
            if pset_name in _INTERNAL_PSETS or (standard is not None and kind is not None
                                                and pset_name == standard[0]):
                continue
            group = self._row(pset_name, bold=True)
            editable = kind is not None and not pset_name.startswith("Qto_")
            for key, value in props.items():
                if key == "id":
                    continue
                if editable and isinstance(value, bool):
                    item = self._row(key, "", group)
                    box = QtWidgets.QCheckBox()
                    box.setChecked(value)
                    box.toggled.connect(lambda on, ps=pset_name, k=key: self._emit("pset", guid, (ps, k, on)))
                    self.tree.setItemWidget(item, 1, box)
                    self.editors[("pset", key)] = box
                elif editable and isinstance(value, (str, int, float)):
                    item = self._row(key, "", group)
                    edit = QtWidgets.QLineEdit(str(value))
                    edit.setFrame(False)
                    edit.editingFinished.connect(
                        lambda e=edit, ps=pset_name, k=key, old=str(value), num=isinstance(value, (int, float)):
                        self._pset_text_done(e, guid, ps, k, old, num))
                    self.tree.setItemWidget(item, 1, edit)
                    self.editors[("pset", key)] = edit
                else:
                    self._row(key, _value(key, value, scale), group)
        if kind is None:
            note = self._row(t("props.readonly"))
            note.setFirstColumnSpanned(True)
        item = self._row(t("props.more"), "")
        button = QtWidgets.QPushButton(t("props.add_property"))
        button.clicked.connect(lambda: self._add_property(doc, guid))
        self.tree.setItemWidget(item, 1, button)
        self.editors["add_property"] = button
        self.tree.setCurrentItem(None)

    def _ifc_data_rows(self, guid, standard, scale):
        """(0.266) The element's standard IFC set (Pset_…Common), every property of it: the ones set and the empty
        ones, each with its editor — a yes / no / "—" list, a list of the enumeration's values, a text, a number or a
        length (m). "—" or an empty field: not set (the program's value back, if it has one). Its words in
        Portuguese, its IFC name in the tip; the program's values marked as such."""
        pset_name, rows = standard
        group = self._row(t("props.ifc_data", pset=pset_name), pset_name, bold=True)   # (0.396: its set beside it)
        group.setToolTip(0, t("props.ifc_data_tip"))
        group.setToolTip(1, pset_name)
        group.setForeground(1, QtGui.QBrush(QtGui.QColor(theme.C["muted"])))
        for prop, kind, choices, value, how in rows:
            label = t("ifcprop." + prop) if has("ifcprop." + prop) else prop
            item = self._row(label, "", group)
            tip = "{}.{}".format(pset_name, prop) + ("\n" + t("ifcdata." + how) if how else "")
            item.setToolTip(0, tip)
            if how in ("auto", "type"):
                item.setForeground(0, QtGui.QBrush(theme.colour("link" if how == "auto" else "muted")))
            if kind in ("bool", "choice"):
                combo = QtWidgets.QComboBox()
                combo.addItem("—", None)
                options = ((t("rules.yes"), True), (t("rules.no"), False)) if kind == "bool" else \
                    tuple((str(c), c) for c in choices or ())
                for text, data in options:
                    combo.addItem(text, data)
                combo.setCurrentIndex(max(combo.findData(value), 0) if value is not None else 0)
                combo.setToolTip(tip)
                combo.activated.connect(lambda k, c=combo, p=prop, old=value: c.itemData(k) != old and self._emit(
                    "pset", guid, (pset_name, p, c.itemData(k))))
                widget = combo
            else:
                shown = "" if value is None else _len(value) if kind == "length" else \
                    str(value).replace(".", decimal_sep()) if isinstance(value, float) else str(value)
                edit = QtWidgets.QLineEdit(shown)
                edit.setFrame(False)
                edit.setPlaceholderText("—")
                edit.setToolTip(tip)
                edit.editingFinished.connect(lambda e=edit, p=prop, k=kind, old=shown: self._ifc_data_done(
                    e, guid, pset_name, p, k, old, scale))
                widget = edit
            self.tree.setItemWidget(item, 1, widget)
            self.editors[("ifc", prop)] = widget

    def _ifc_data_done(self, edit, guid, pset_name, prop, kind, old, scale):
        new = edit.text().strip()
        if new == old:
            return
        if not new:
            value = None                                  # (cleared: not set — or the program's value back)
        elif kind == "length":
            value = parse_length(new)
            value = value / scale if value is not None else None
        elif kind in ("number", "integer"):
            value = float(new.replace(",", ".")) if _is_number(new) else None
            value = int(round(value)) if kind == "integer" and value is not None else value
        else:
            value = new
        if new and value is None:                         # (not a number / a length: put the old one back)
            edit.setText(old)
            return
        self._emit("pset", guid, (pset_name, prop, value))

    def _add_property(self, doc, guid):
        """+ Property…: one of IFC4's standard properties for this element (FireRating of a door…)."""
        dialog = AddPropertyDialog(self, doc.ifc.property_templates(guid))
        self._add_dialog = dialog                      # (tests fill it in)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted and dialog.result_value() is not None:
            self._emit("pset_add", guid, dialog.result_value())

    def _pset_text_done(self, edit, guid, pset_name, key, old, numeric):
        new = edit.text().strip()
        if new == old:
            return
        if numeric:
            if not _is_number(new):
                edit.setText(old)   # not a number: put the old value back
                return
            value = float(new.replace(",", "."))
        else:
            value = new
        self._emit("pset", guid, (pset_name, key, value))


def _is_number(s):
    try:
        float(s.replace(",", "."))
        return True
    except ValueError:
        return False


class AddPropertyDialog(QtWidgets.QDialog):
    """Choose a standard property (IfcModel.property_templates) and give its value."""

    def __init__(self, parent, templates):
        super().__init__(parent)
        self.setWindowTitle(t("props.add_title"))
        self.templates = list(templates) + [("", "", "free", None)]      # the last: a property of one's own
        self.choose = QtWidgets.QComboBox()
        for pset, prop, kind, _choices in self.templates:
            self.choose.addItem("{} ▸ {}".format(pset, prop) if kind != "free" else t("props.add_free"))
        self.choose.currentIndexChanged.connect(self._kind_changed)
        self.free_pset = QtWidgets.QLineEdit(t("props.free_pset"))     # a property of one's own: its set,
        self.free_prop = QtWidgets.QLineEdit()                         # its name, the kind of value
        self.free_kind = QtWidgets.QComboBox()
        for kind in ("text", "number", "bool"):
            self.free_kind.addItem(t("props.kind." + kind), kind)
        self.free_kind.currentIndexChanged.connect(lambda _k: self._kind_changed(self.choose.currentIndex()))
        self.check = QtWidgets.QCheckBox(t("rules.yes"))
        self.choices = QtWidgets.QComboBox()
        self.text = QtWidgets.QLineEdit()
        self.number = QtWidgets.QDoubleSpinBox()
        self.number.setRange(-1e9, 1e9)
        self.number.setDecimals(3)
        self.integer = QtWidgets.QSpinBox()
        self.integer.setRange(-1000000, 1000000)
        self.stack = QtWidgets.QStackedWidget()
        for w in (self.check, self.choices, self.text, self.number, self.integer):
            self.stack.addWidget(w)
        form = QtWidgets.QFormLayout(self)
        if not templates:
            form.addRow(QtWidgets.QLabel(t("props.add_none")))
        form.addRow(t("props.add_choose"), self.choose)
        self.free_rows = []
        for label, widget in (("props.free_pset_label", self.free_pset), ("props.free_prop_label", self.free_prop),
                              ("props.free_kind_label", self.free_kind)):
            caption = QtWidgets.QLabel(t(label))
            form.addRow(caption, widget)
            self.free_rows += [caption, widget]
        form.addRow(t("props.add_value"), self.stack)
        self.error = QtWidgets.QLabel()
        self.error.setStyleSheet("color: %s" % theme.C["bad"])
        form.addRow(self.error)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        self.resize(560, 160)
        self._kind_changed(0)

    def _accept(self):
        """A property of one's own needs a set and a name; IFC keeps "Pset_" and "Qto_" for its own."""
        if self.templates[self.choose.currentIndex()][2] == "free":
            pset, prop = self.free_pset.text().strip(), self.free_prop.text().strip()
            if not pset or not prop:
                self.error.setText(t("props.free_missing"))
                return
            if pset.lower().startswith(("pset_", "qto_")):
                self.error.setText(t("props.free_reserved"))
                return
        self.accept()

    def _kind_changed(self, index):
        if not 0 <= index < len(self.templates):
            return
        _pset, _prop, kind, choices = self.templates[index]
        for w in self.free_rows:
            w.setVisible(kind == "free")
        if kind == "free":
            kind = self.free_kind.currentData()
        if kind == "choice":
            self.choices.clear()
            self.choices.addItems([str(c) for c in choices])
        self.number.setSuffix(" m" if kind == "length" else "")
        self.stack.setCurrentWidget({"bool": self.check, "choice": self.choices, "text": self.text,
                                     "integer": self.integer}.get(kind, self.number))

    def select(self, pset, prop):
        """Choose a property by name (used by tests)."""
        for k, (ps, pr, _kind, _choices) in enumerate(self.templates):
            if (ps, pr) == (pset, prop):
                self.choose.setCurrentIndex(k)

    def result_value(self):
        """(property set, property, kind, value) as given, or None."""
        index = self.choose.currentIndex()
        if not 0 <= index < len(self.templates):
            return None
        pset, prop, kind, _choices = self.templates[index]
        if kind == "free":
            pset, prop, kind = self.free_pset.text().strip(), self.free_prop.text().strip(), self.free_kind.currentData()
            if not pset or not prop:
                return None
        value = {"bool": lambda: self.check.isChecked(), "choice": lambda: self.choices.currentText(),
                 "text": lambda: self.text.text().strip(), "integer": lambda: self.integer.value()
                 }.get(kind, lambda: float(self.number.value()))()
        if kind == "text" and not value:
            return None
        return pset, prop, kind, value


class VisibilityDialog(QtWidgets.QDialog):
    """Which categories a view shows (Revit's Visibility/Graphics): a list to tick, OK / Cancel."""

    def __init__(self, parent, label, classes, hidden):
        super().__init__(parent)
        from .project_tree import category_label
        from .view_templates import COMMON
        self.setWindowTitle(t("vis.title", view=label))
        self.list = QtWidgets.QListWidget()
        for cls in sorted(set(COMMON) | set(classes) | set(hidden), key=lambda c: category_label(c).lower()):
            item = QtWidgets.QListWidgetItem("{}  ({})".format(category_label(cls), cls))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, cls)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Unchecked if cls in hidden else QtCore.Qt.CheckState.Checked)
            self.list.addItem(item)
        every = QtWidgets.QPushButton(t("vis.all"))
        every.clicked.connect(lambda: self.set_hidden(()))
        hint = QtWidgets.QLabel(t("vis.hint"))
        hint.setWordWrap(True)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addWidget(self.list, 1)
        layout.addWidget(every, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(buttons)
        self.resize(420, 480)

    def set_hidden(self, hidden):
        """Untick these categories, tick the others (also used by tests)."""
        for k in range(self.list.count()):
            item = self.list.item(k)
            off = item.data(QtCore.Qt.ItemDataRole.UserRole) in hidden
            item.setCheckState(QtCore.Qt.CheckState.Unchecked if off else QtCore.Qt.CheckState.Checked)

    def hidden(self):
        return sorted(self.list.item(k).data(QtCore.Qt.ItemDataRole.UserRole) for k in range(self.list.count())
                      if self.list.item(k).checkState() != QtCore.Qt.CheckState.Checked)


def dock(parent):
    panel = PropertiesPanel(parent)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, panel)
    return panel
