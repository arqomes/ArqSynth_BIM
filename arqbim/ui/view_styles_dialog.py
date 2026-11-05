"""(0.315) View ▸ View styles…: the view styles (model/view_styles.py), as Revit's visual styles and graphic display
options — the program's (fixed: duplicated to be changed) and the project's, made, named, duplicated, changed and
deleted. Each: how the faces are seen, their colours, the edges and how thick, the sun's shadows, the materials'
surface patterns and transparency, what is cut. One undo step when closed with OK (the window: on accepted)."""

from dataclasses import replace

from PySide6 import QtCore, QtWidgets

from ..i18n import t
from ..model import view_styles as styles_model
from . import icons
from . import theme


CATEGORIES = ("IfcWall", "IfcSlab", "IfcRoof", "IfcColumn", "IfcBeam", "IfcFooting", "IfcStair", "IfcRamp",
              "IfcCovering", "IfcCurtainWall", "IfcDoor", "IfcWindow", "IfcRailing", "IfcFurniture",
              "IfcBuildingElementProxy")


def _summary(entry, category_label):
    """A category's hatches in a line: «Paredes — corte: Betão / superfície: Tijolo à vista»."""
    from . import pattern_paint
    cls, cut_fg, cut_bg, surface_fg, surface_bg = entry

    def names(*layers):
        found = [pattern_paint.name(v[0]) for v in layers if v]
        return " + ".join(found) if found else t("vstyle.cat_materials")
    return "{} — {}: {} / {}: {}".format(category_label(cls), t("vstyle.cat_cut"), names(cut_fg, cut_bg),
                                         t("vstyle.cat_surface"), names(surface_fg, surface_bg))


class CategoryHatches(QtWidgets.QDialog):
    """(0.318) A category's hatches in a view style: which category, its cut and its surface — each a foreground and a
    background pattern with its colour (none: its materials')."""

    def __init__(self, parent, current=None, taken=()):
        from .material_editor import _Pair
        from .project_tree import category_label
        super().__init__(parent)
        self.setWindowTitle(t("vstyle.cat_title"))
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        self.category = QtWidgets.QComboBox()
        for cls in CATEGORIES:
            if cls not in taken:
                self.category.addItem(category_label(cls), cls)
        if current is not None:
            self.category.setCurrentIndex(max(0, self.category.findData(current[0])))
        form.addRow(t("vstyle.cat_category"), self.category)
        layout.addLayout(form)
        boxes = []
        for title, model in (("vstyle.cat_cut_box", False), ("vstyle.cat_surface_box", True)):
            box = QtWidgets.QGroupBox(t(title))
            grid = QtWidgets.QGridLayout(box)
            boxes.append(_Pair(grid, 0, lambda: None, model=model))    # (0.319: each pattern a button)
            layout.addWidget(box)
        self.cut, self.surface = boxes
        if current is not None:
            self.cut.set(current[1], current[2])
            self.surface.set(current[3], current[4])
        note = QtWidgets.QLabel(t("vstyle.cat_note"))
        note.setWordWrap(True)
        note.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        layout.addWidget(note)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def entry(self):
        """(class, cut foreground, cut background, surface foreground, surface background)."""
        cut_fg, cut_bg = self.cut.values()
        surface_fg, surface_bg = self.surface.values()
        return self.category.currentData(), cut_fg, cut_bg, surface_fg, surface_bg


class ElementHatches(QtWidgets.QDialog):
    """(0.331) Some elements' hatches in one view, as Revit's «Override graphics in view ▸ by element»: their cut and
    their surface — each a foreground and a background pattern with its colour (none: their category's, their
    materials'). «Repor» puts theirs back (entry() is then None). current: the hatches they all have (None: none, or
    not the same); own: some of them have hatches of their own here (Repor is offered)."""

    def __init__(self, parent, current, what, view, own=False):
        from .material_editor import _Pair
        super().__init__(parent)
        self.setWindowTitle(t("ehatch.title"))
        self.reset = False
        layout = QtWidgets.QVBoxLayout(self)
        head = QtWidgets.QLabel(t("ehatch.head", what=what, view=view))
        head.setWordWrap(True)
        layout.addWidget(head)
        boxes = []
        for title, model in (("vstyle.cat_cut_box", False), ("vstyle.cat_surface_box", True)):
            box = QtWidgets.QGroupBox(t(title))
            grid = QtWidgets.QGridLayout(box)
            boxes.append(_Pair(grid, 0, lambda: None, model=model))
            layout.addWidget(box)
        self.cut, self.surface = boxes
        if current is not None:
            self.cut.set(current[0], current[1])
            self.surface.set(current[2], current[3])
        note = QtWidgets.QLabel(t("ehatch.note"))
        note.setWordWrap(True)
        note.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        layout.addWidget(note)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.reset_button = buttons.addButton(t("ehatch.reset"), QtWidgets.QDialogButtonBox.ButtonRole.ResetRole)
        self.reset_button.setToolTip(t("ehatch.reset_tip"))
        self.reset_button.setEnabled(current is not None or own)
        self.reset_button.clicked.connect(self._reset)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _reset(self):
        self.reset = True
        self.accept()

    def entry(self):
        """(cut foreground, cut background, surface foreground, surface background) as chosen; None: «Repor», or none
        chosen (theirs back)."""
        if self.reset:
            return None
        found = self.cut.values() + self.surface.values()
        return found if any(found) else None


class ViewStylesDialog(QtWidgets.QDialog):
    def __init__(self, parent, styles, select=None, site=(None, None)):
        super().__init__(parent)
        self.setWindowTitle(t("vstyle.title"))
        self.styles = list(styles)                      # the project's, as edited here
        self.site = site                                # (0.316) the project's (latitude, longitude), for its sun
        self._loading = False
        left = QtWidgets.QVBoxLayout()
        self.list = QtWidgets.QListWidget()
        self.list.setIconSize(QtCore.QSize(24, 24))
        self.list.setMinimumWidth(230)
        self.list.currentRowChanged.connect(lambda _r: self._show())
        left.addWidget(self.list, 1)
        row = QtWidgets.QHBoxLayout()
        self.new = QtWidgets.QPushButton(t("vstyle.new"))
        self.new.setToolTip(t("vstyle.new_tip"))
        self.new.clicked.connect(self.duplicate_style)
        self.delete = QtWidgets.QPushButton(t("vstyle.delete"))
        self.delete.clicked.connect(self.delete_style)
        row.addWidget(self.new)
        row.addWidget(self.delete)
        left.addLayout(row)

        form = QtWidgets.QFormLayout()
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.name = QtWidgets.QLineEdit()
        self.name.textEdited.connect(lambda text: self._set(name=text.strip() or self._current().name))
        form.addRow(t("vstyle.name"), self.name)
        self.faces = self._combo(styles_model.FACES, "vstyle.faces.", "faces")
        form.addRow(t("vstyle.faces"), self.faces)
        self.colours = self._combo(styles_model.COLOURS, "vstyle.colours.", "colours")
        form.addRow(t("vstyle.colours"), self.colours)
        self.edges = QtWidgets.QCheckBox(t("vstyle.edges_on"))
        self.edges.toggled.connect(lambda on: self._set(edges=bool(on)))
        self.width = QtWidgets.QComboBox()
        for w in styles_model.EDGE_WIDTHS:
            self.width.addItem(t("vstyle.width_px", w="{:g}".format(w).replace(".", ",")), w)
        self.width.activated.connect(lambda _i: self._set(edge_width=float(self.width.currentData())))
        line = QtWidgets.QHBoxLayout()
        line.addWidget(self.edges)
        line.addWidget(self.width, 1)
        form.addRow(t("vstyle.edges"), line)
        self.shadows = QtWidgets.QCheckBox(t("vstyle.shadows_on"))
        self.shadows.toggled.connect(lambda on: self._set(shadows=bool(on)))
        form.addRow(t("vstyle.shadows"), self.shadows)
        # (0.316) where its sun is: azimuth and altitude, or worked out from the site, a day and an hour
        self.azimuth = QtWidgets.QDoubleSpinBox()
        self.azimuth.setRange(0.0, 359.0)
        self.azimuth.setDecimals(0)
        self.azimuth.setWrapping(True)
        self.azimuth.setSuffix("°")
        self.altitude = QtWidgets.QDoubleSpinBox()
        self.altitude.setRange(*styles_model.ALTITUDES)
        self.altitude.setDecimals(0)
        self.altitude.setSuffix("°")
        self.azimuth.valueChanged.connect(lambda value: self._set(sun_azimuth=float(value)))
        self.altitude.valueChanged.connect(lambda value: self._set(sun_altitude=float(value)))
        self.from_site = QtWidgets.QPushButton(t("vstyle.sun_from_site"))
        self.from_site.clicked.connect(self.sun_from_site)
        sun = QtWidgets.QHBoxLayout()
        sun.addWidget(QtWidgets.QLabel(t("vstyle.azimuth")))
        sun.addWidget(self.azimuth)
        sun.addWidget(QtWidgets.QLabel(t("vstyle.altitude")))
        sun.addWidget(self.altitude)
        sun.addWidget(self.from_site, 1)
        form.addRow(t("vstyle.sun"), sun)
        sun_hint = QtWidgets.QLabel(t("vstyle.sun_hint"))
        sun_hint.setWordWrap(True)
        sun_hint.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        form.addRow("", sun_hint)
        self.patterns = QtWidgets.QCheckBox(t("vstyle.patterns_on"))
        self.patterns.toggled.connect(lambda on: self._set(patterns=bool(on)))
        form.addRow(t("vstyle.patterns"), self.patterns)
        self.transparency = QtWidgets.QCheckBox(t("vstyle.transparency_on"))
        self.transparency.toggled.connect(lambda on: self._set(transparency=bool(on)))
        form.addRow(t("vstyle.transparency"), self.transparency)
        self.cut = self._combo(styles_model.CUTS, "vstyle.cut.", "cut")
        form.addRow(t("vstyle.cut"), self.cut)
        # (0.318) its hatches by category, over the materials'
        self.categories = QtWidgets.QListWidget()
        self.categories.setMaximumHeight(110)
        self.categories.itemDoubleClicked.connect(lambda _i: self.edit_category())
        buttons = QtWidgets.QHBoxLayout()
        self.add_category = QtWidgets.QPushButton(t("vstyle.cat_add"))
        self.change_category = QtWidgets.QPushButton(t("vstyle.cat_change"))
        self.drop_category = QtWidgets.QPushButton(t("vstyle.cat_drop"))
        self.add_category.clicked.connect(lambda: self.edit_category(new=True))
        self.change_category.clicked.connect(lambda: self.edit_category())
        self.drop_category.clicked.connect(self.remove_category)
        for b in (self.add_category, self.change_category, self.drop_category):
            buttons.addWidget(b)
        box = QtWidgets.QVBoxLayout()
        box.addWidget(self.categories)
        box.addLayout(buttons)
        form.addRow(t("vstyle.categories"), box)
        self.form = QtWidgets.QWidget()
        self.form.setLayout(form)
        self.locked = QtWidgets.QLabel(t("vstyle.builtin_note"))
        self.locked.setWordWrap(True)
        self.locked.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        right = QtWidgets.QVBoxLayout()
        right.addWidget(self.form)
        right.addWidget(self.locked)
        right.addStretch(1)

        hint = QtWidgets.QLabel(t("vstyle.hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        body = QtWidgets.QHBoxLayout()
        body.addLayout(left, 2)
        body.addLayout(right, 3)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(body, 1)
        layout.addWidget(hint)
        layout.addWidget(buttons)
        self.resize(800, 700)
        self._fill_list(select or "shaded")

    def _combo(self, keys, prefix, attr):
        combo = QtWidgets.QComboBox()
        for key in keys:
            combo.addItem(t(prefix + key), key)
        combo.activated.connect(lambda _i: self._set(**{attr: combo.currentData()}))
        return combo

    # ------------------------------------------------------------ the list

    def all(self):
        return styles_model.all_styles(self.styles)

    def _fill_list(self, uid):
        blocker = QtCore.QSignalBlocker(self.list)
        self.list.clear()
        builtin = len(styles_model.BUILTIN)
        for k, style in enumerate(self.all()):
            item = QtWidgets.QListWidgetItem(icons.view_style_icon(style), styles_model.label(style, t))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, style.uid)
            if k < builtin:
                item.setForeground(theme.colour("note"))
            self.list.addItem(item)
        del blocker
        uids = [s.uid for s in self.all()]
        self.list.setCurrentRow(uids.index(uid) if uid in uids else 0)
        self._show()

    def _current(self):
        row = self.list.currentRow()
        styles = self.all()
        return styles[row] if 0 <= row < len(styles) else None

    def select(self, uid):
        self._fill_list(uid)

    # ------------------------------------------------------------ one style

    def _show(self):
        style = self._current()
        if style is None:
            return
        self._loading = True
        self.name.setText(styles_model.label(style, t))
        for combo, value in ((self.faces, style.faces), (self.colours, style.colours), (self.cut, style.cut)):
            combo.setCurrentIndex(max(0, combo.findData(value)))
        self.edges.setChecked(style.edges)
        self.width.setCurrentIndex(min(range(self.width.count()),
                                       key=lambda k: abs(self.width.itemData(k) - style.edge_width)))
        self.shadows.setChecked(style.shadows)
        self.azimuth.setValue(style.sun_azimuth)
        self.altitude.setValue(style.sun_altitude)
        self.patterns.setChecked(style.patterns)
        self.transparency.setChecked(style.transparency)
        self._fill_categories(style)
        self._loading = False
        self.form.setEnabled(not style.builtin)
        self.locked.setVisible(style.builtin)
        self.delete.setEnabled(not style.builtin)

    def _set(self, **changes):
        style = self._current()
        if style is None or style.builtin or self._loading:
            return
        k = next(i for i, s in enumerate(self.styles) if s.uid == style.uid)
        self.styles[k] = replace(style, **changes)
        item = self.list.currentItem()
        item.setText(styles_model.label(self.styles[k], t))
        item.setIcon(icons.view_style_icon(self.styles[k]))

    # ------------------------------------------------------------ hatches by category (0.318)

    def _fill_categories(self, style):
        from .project_tree import category_label
        self.categories.clear()
        for entry in style.categories:
            item = QtWidgets.QListWidgetItem(_summary(entry, category_label))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, entry[0])
            self.categories.addItem(item)

    def edit_category(self, new=False, entry=None):
        """A category's hatches added or changed (the small window; `entry` given: as it is, no window). True if set."""
        style = self._current()
        if style is None or style.builtin:
            return False
        if entry is None:
            item = None if new else self.categories.currentItem()
            if not new and item is None:
                return False
            cls = item.data(QtCore.Qt.ItemDataRole.UserRole) if item is not None else None
            current = (cls,) + (style.category(cls) or (None,) * 4) if cls else None
            dialog = CategoryHatches(self, current, [c[0] for c in style.categories if c[0] != cls])
            if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
                return False
            entry = dialog.entry()
        kept = tuple(c for c in style.categories if c[0] != entry[0])
        self._set(categories=kept + (tuple(entry),))
        self._fill_categories(self._current())
        return True

    def remove_category(self):
        style = self._current()
        item = self.categories.currentItem()
        if style is None or style.builtin or item is None:
            return
        cls = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self._set(categories=tuple(c for c in style.categories if c[0] != cls))
        self._fill_categories(self._current())

    def sun_from_site(self, when=None, utc_offset=None):
        """(0.316) The chosen style's sun where it is over the project's site on a day, at an hour (asked, unless given:
        a datetime of the site's clock and its hours ahead of UTC). True if set."""
        from ..core import sun as core_sun
        lat, lon = self.site
        if lat is None or lon is None or (abs(lat) < 1e-9 and abs(lon) < 1e-9):
            QtWidgets.QMessageBox.information(self, t("vstyle.sun_title"), t("vstyle.sun_no_site"))
            return False
        if when is None:
            asked = self._ask_when(lat, lon)
            if asked is None:
                return False
            when, utc_offset = asked
        azimuth, altitude = core_sun.position(lat, lon, when, utc_offset or 0.0)
        if altitude < styles_model.ALTITUDES[0]:
            QtWidgets.QMessageBox.information(self, t("vstyle.sun_title"),
                                              t("vstyle.sun_night", alt="{:.0f}".format(altitude)))
            return False
        self.azimuth.setValue(round(azimuth) % 360)
        self.altitude.setValue(round(altitude))
        return True

    def _ask_when(self, lat, lon):
        """(datetime, hours ahead of UTC) asked: today at three in the afternoon, the computer's time zone."""
        from datetime import datetime
        box = QtWidgets.QDialog(self)
        box.setWindowTitle(t("vstyle.sun_title"))
        form = QtWidgets.QFormLayout(box)
        form.addRow(QtWidgets.QLabel(t("vstyle.sun_site", lat="{:.4f}".format(lat), lon="{:.4f}".format(lon))))
        edit = QtWidgets.QDateTimeEdit(QtCore.QDateTime(QtCore.QDate.currentDate(), QtCore.QTime(15, 0)))
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("dd/MM/yyyy  HH:mm")
        form.addRow(t("vstyle.sun_when"), edit)
        zone = QtWidgets.QDoubleSpinBox()
        zone.setRange(-12.0, 14.0)
        zone.setDecimals(1)
        zone.setSingleStep(0.5)
        offset = datetime.now().astimezone().utcoffset()
        zone.setValue(offset.total_seconds() / 3600.0 if offset is not None else 0.0)
        form.addRow(t("vstyle.sun_utc"), zone)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(box.accept)
        buttons.rejected.connect(box.reject)
        form.addRow(buttons)
        if box.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return None
        return edit.dateTime().toPython(), zone.value()

    def duplicate_style(self):
        """A new style of the project's, made from the one chosen (a built-in, or the project's)."""
        base = self._current() or styles_model.BUILTIN["shaded"]
        names = {styles_model.label(s, t) for s in self.all()}
        stem = t("vstyle.copy_of", name=styles_model.label(base, t))
        name, n = stem, 2
        while name in names:
            name = "{} ({})".format(stem, n)
            n += 1
        made = styles_model.new_from(base, name)
        self.styles.append(made)
        self._fill_list(made.uid)
        self.name.setFocus()
        self.name.selectAll()
        return made

    def delete_style(self):
        style = self._current()
        if style is None or style.builtin:
            return
        self.styles = [s for s in self.styles if s.uid != style.uid]
        self._fill_list("shaded")
