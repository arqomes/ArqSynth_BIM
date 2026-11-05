"""The materials window (0.89), as Revit's Material Browser in short: the project's materials — the catalogue's
and its own — with their name, what they are drawn with where cut (their hatch, kept as the IFC material's
category), their colour (the IFC surface style: what Revit and the others show) and their density and thermal
conductivity (IFC4's Pset_MaterialCommon / Pset_MaterialThermal). New, Duplicate, Delete (only an unused one of
the project's). Applying is one undo step, done by the window (on_save).

(0.314) Their graphics, as Revit's: the surface — a foreground and a background pattern, each in its colour, the
shading colour and the transparency — and the cut — a foreground and a background pattern (none: the category's
pattern in the project's graphic style) —, each with a sample. (0.343) Its finish in the realistic render (matte,
satin, glossy, metallic, glass, frosted glass; else its category's)."""

import dataclasses
import math

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import decimal_sep, lang, t
from ..ifc import catalog
from ..ifc.model import HATCH_WORDS
from ..model import graphic_styles as styles_model
from ..model import project_types
from ..model import render_scene
from . import pattern_paint
from .pattern_picker import PatternButton
from . import theme

HATCHES = ("", "concrete", "masonry", "wood", "insulation", "gypsum", "earth")
PREVIEW = (132, 84)                    # px: each sample


def hatch_of(category, name):
    """The hatch a material is drawn with (as ifc.model._hatch_of): from its category, else its name."""
    for text in (category, name):
        text = (text or "").lower()
        for hatch, words in HATCH_WORDS:
            if any(w in text for w in words):
                return hatch
    return ""


def _name(m):
    return m.name_pt if lang() == "pt" else m.name_en


def _sort_key(text):
    """(0.397) A name as it is sorted: accents left out (Aço before Água, as in a dictionary), any case."""
    import unicodedata
    plain = unicodedata.normalize("NFD", text)
    return "".join(c for c in plain if not unicodedata.combining(c)).lower()


def listed(family=None, words=""):
    """(0.397) The materials as both lists show them — this window's and the Materials Browser beside the
    Properties: those of `family` (None: all) whose name has every word searched, in alphabetical order."""
    words = words.strip().lower().split()
    found = [m for m in catalog.MATERIALS.values()
             if (family is None or catalog.family_of(m) == family)
             and all(w in (m.name_pt + " " + m.name_en).lower() for w in words)]
    return sorted(found, key=lambda m: _sort_key(_name(m)))


def family_combo():
    """(0.397) The families' list both show on top: «Todas as famílias», then each family."""
    combo = QtWidgets.QComboBox()
    combo.addItem(t("mat.family.all"), None)
    for name, _categories in catalog.FAMILIES:
        combo.addItem(t("mat.family." + name), name)
    return combo


def _number(text):
    """A number typed with a comma or a point; "" -> None; not a number -> False."""
    text = text.strip().replace(" ", "")
    if not text:
        return None
    try:
        value = float(text.replace(",", "."))
    except ValueError:
        return False
    return value if value >= 0 else False


def _text(value):
    return "" if value is None else ("{:g}".format(value)).replace(".", decimal_sep())


class ColourButton(QtWidgets.QPushButton):
    """(0.314) A button showing a colour ("#rrggbb"); clicked, the colour chooser."""

    changed = QtCore.Signal()

    def __init__(self, title, colour="#000000"):
        super().__init__()
        self.title = title
        self.setMinimumWidth(92)
        self.clicked.connect(self._pick)
        self.set_colour(colour)

    def set_colour(self, colour):
        q = QtGui.QColor(colour)
        self.colour = q.name()
        ink = "#000000" if q.lightnessF() > 0.5 else "#ffffff"
        self.setText(self.colour)
        self.setStyleSheet("QPushButton {{ background: {}; color: {}; border: 1px solid {}; padding: 2px 6px; }}"
                           .format(self.colour, ink, theme.C["edge_2"]))

    def _pick(self):
        q = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.colour), self, self.title)
        if q.isValid():
            self.set_colour(q.name())
            self.changed.emit()


class _Pair:
    """(0.314) A foreground and a background pattern, each with its colour, in a grid — (0.319) each pattern a button
    showing it (its sample, its name); clicked, the window that chooses one, makes or edits one (ui/pattern_picker.py).
    model: the kind of patterns shown first (a surface's: model; a cut's: drafting)."""

    def __init__(self, grid, row, on_change, model=False):
        self.combos, self.colours = [], []
        for k, label in enumerate((t("mat.fg"), t("mat.bg"))):
            button = PatternButton(model=model)
            colour = ColourButton(t("mat.pattern_colour"))
            colour.setToolTip(t("mat.pattern_colour"))
            grid.addWidget(QtWidgets.QLabel(label), row + k, 0)
            grid.addWidget(button, row + k, 1)
            grid.addWidget(colour, row + k, 2)
            button.changed.connect(on_change)
            colour.changed.connect(on_change)
            self.combos.append(button)
            self.colours.append(colour)

    def set(self, fg, bg):
        for button, colour, value, default in zip(self.combos, self.colours, (fg, bg), ("#2b2f36", "#ffffff")):
            button.set_key(value[0] if value else None)
            colour.set_colour(value[1] if value else default)

    def values(self):
        return tuple((button.key(), colour.colour) if button.key() else None
                     for button, colour in zip(self.combos, self.colours))


class _Sample(QtWidgets.QLabel):
    """(0.319) A group's sample: clicked, the window that chooses its foreground's pattern."""

    def __init__(self, on_click):
        super().__init__()
        self.on_click = on_click
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setToolTip(t("pick.sample_tip"))

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.on_click()
        super().mousePressEvent(event)


class MaterialEditor(QtWidgets.QDialog):
    def __init__(self, parent, doc):
        super().__init__(parent)
        self.setWindowTitle(t("mat.title"))
        self.doc = doc
        self.on_save = None           # (spec, old spec or None) -> the saved material's key, or None
        self.on_delete = None         # (spec) -> True if removed
        self.current = None
        self._loading = False
        outer = QtWidgets.QVBoxLayout(self)
        body = QtWidgets.QHBoxLayout()
        outer.addLayout(body, 1)
        left = QtWidgets.QVBoxLayout()
        # (0.318) the library is long: by family, and a search
        self.family = family_combo()                    # (0.397: the same as the Materials Browser's)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText(t("mat.search"))
        self.search.setClearButtonEnabled(True)
        left.addWidget(self.family)
        left.addWidget(self.search)
        self.list = QtWidgets.QListWidget()
        self.list.setMinimumWidth(240)
        self.list.setIconSize(QtCore.QSize(28, 18))
        left.addWidget(self.list, 1)
        self.family.currentIndexChanged.connect(lambda _i: self._fill_list(self._chosen_key(), force=False))
        self.search.textChanged.connect(lambda _t: self._fill_list(self._chosen_key(), force=False))
        row = QtWidgets.QHBoxLayout()
        self.new = QtWidgets.QPushButton(t("mat.new"))
        self.duplicate = QtWidgets.QPushButton(t("types.duplicate"))
        self.remove = QtWidgets.QPushButton(t("types.delete"))
        for b in (self.new, self.duplicate, self.remove):
            row.addWidget(b)
        left.addLayout(row)
        body.addLayout(left)
        right = QtWidgets.QVBoxLayout()
        form = QtWidgets.QFormLayout()
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.name = QtWidgets.QLineEdit()
        form.addRow(t("types.name"), self.name)
        self.hatch = QtWidgets.QComboBox()
        for h in HATCHES:
            self.hatch.addItem(t("mat.hatch." + (h or "none")), h)
        form.addRow(t("mat.category"), self.hatch)
        right.addLayout(form)

        # (0.314) the surface: its patterns, its shading colour, how clear — (0.319) each pattern a button with its
        # sample: clicked, the window that chooses one, makes one, edits one
        surface = QtWidgets.QGroupBox(t("mat.surface"))
        grid = QtWidgets.QGridLayout(surface)
        self.surface = _Pair(grid, 0, self._refresh_samples, model=True)
        grid.addWidget(QtWidgets.QLabel(t("mat.shading")), 2, 0)
        self.colour_button = ColourButton(t("mat.shading"))
        self.colour_button.changed.connect(self._refresh_samples)
        grid.addWidget(self.colour_button, 2, 1, 1, 2)
        grid.addWidget(QtWidgets.QLabel(t("mat.transparency")), 3, 0)
        self.transparency = QtWidgets.QSpinBox()
        self.transparency.setRange(0, 100)
        self.transparency.setSuffix(" %")
        self.transparency.valueChanged.connect(lambda _v: self._refresh_samples())
        grid.addWidget(self.transparency, 3, 1, 1, 2)
        grid.addWidget(QtWidgets.QLabel(t("mat.finish")), 4, 0)      # (0.343) in the realistic render
        self.finish = QtWidgets.QComboBox()
        self.finish.setToolTip(t("mat.finish_tip"))
        self.finish.addItem(t("mat.finish.auto"), "")
        for f in render_scene.FINISHES:
            self.finish.addItem(t("render.finish." + f), f)
        grid.addWidget(self.finish, 4, 1, 1, 2)
        grid.addWidget(self._hint(), 5, 0, 1, 3)
        self.surface_sample = _Sample(lambda: self.surface.combos[0].pick())
        self.surface_sample.setFixedSize(*PREVIEW)
        grid.addWidget(self.surface_sample, 0, 3, 6, 1)
        right.addWidget(surface)

        # (0.314) the cut: its patterns (none: its category's, in the project's graphic style)
        cut = QtWidgets.QGroupBox(t("mat.cut"))
        grid = QtWidgets.QGridLayout(cut)
        self.cut = _Pair(grid, 0, self._refresh_samples, model=False)
        self.cut_note = QtWidgets.QLabel(t("mat.cut_by_category"))
        self.cut_note.setWordWrap(True)
        self.cut_note.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        grid.addWidget(self.cut_note, 2, 0, 1, 3)
        grid.addWidget(self._hint(), 3, 0, 1, 3)
        self.cut_sample = _Sample(lambda: self.cut.combos[0].pick())
        self.cut_sample.setFixedSize(*PREVIEW)
        grid.addWidget(self.cut_sample, 0, 3, 4, 1)
        right.addWidget(cut)
        self.hatch.currentIndexChanged.connect(lambda _i: self._refresh_samples())

        data = QtWidgets.QFormLayout()
        data.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.density = QtWidgets.QLineEdit()
        self.density.setPlaceholderText(t("mat.not_given"))
        data.addRow(t("mat.density"), self.density)
        self.conductivity = QtWidgets.QLineEdit()
        self.conductivity.setPlaceholderText(t("mat.not_given"))
        data.addRow(t("mat.conductivity"), self.conductivity)
        right.addLayout(data)
        self.used = QtWidgets.QLabel()
        self.used.setWordWrap(True)
        self.used.setStyleSheet("QLabel { color: %s; }" % theme.C["ctx_text"])
        right.addWidget(self.used)
        right.addStretch(1)
        body.addLayout(right, 1)
        bottom = QtWidgets.QHBoxLayout()
        bottom.addStretch(1)
        self.apply = QtWidgets.QPushButton(t("types.apply"))
        self.apply.setDefault(True)
        close = QtWidgets.QPushButton(t("types.close"))
        bottom.addWidget(self.apply)
        bottom.addWidget(close)
        outer.addLayout(bottom)
        self.resize(860, 640)

        self.list.currentRowChanged.connect(lambda _r: self._show(self._chosen()))
        self.new.clicked.connect(self.new_material)
        self.duplicate.clicked.connect(self.duplicate_material)
        self.remove.clicked.connect(self.delete_material)
        self.apply.clicked.connect(self.apply_changes)
        close.clicked.connect(self.reject)
        self._fill_list()

    @staticmethod
    def _hint():
        """(0.319) A group's line of advice: the pattern is chosen by clicking it."""
        hint = QtWidgets.QLabel(t("mat.pick_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        return hint

    @property
    def colour(self):
        """The shading colour chosen (RGB 0..1)."""
        q = QtGui.QColor(self.colour_button.colour)
        return q.redF(), q.greenF(), q.blueF()

    # ------------------------------------------------------------ the list

    def _shown(self, m):
        """(0.318) Is a material in the list as filtered (its family, the words searched)?"""
        family = self.family.currentData() if hasattr(self, "family") else None
        words = self.search.text().strip().lower() if hasattr(self, "search") else ""
        return (family is None or catalog.family_of(m) == family) and \
            all(w in (m.name_pt + " " + m.name_en).lower() for w in words.split())

    def _chosen_key(self):
        item = self.list.currentItem()
        return item.data(QtCore.Qt.ItemDataRole.UserRole) if item is not None else None

    def _fill_list(self, select=None, force=True):
        """The list as filtered; `select` chosen in it — force: shown even if the filter hides it (one asked for, one
        just saved), the filter undone."""
        blocker = QtCore.QSignalBlocker(self.list)
        self.list.clear()
        if force and select in catalog.MATERIALS and not self._shown(catalog.MATERIALS[select]):
            for w in (self.family, self.search):            # (one asked for: shown, whatever the filter)
                w.blockSignals(True)
            self.family.setCurrentIndex(0)
            self.search.clear()
            for w in (self.family, self.search):
                w.blockSignals(False)
        for m in listed(self.family.currentData(), self.search.text()):        # (0.397: alphabetical, as the
            item = QtWidgets.QListWidgetItem(_name(m))                       # Materials Browser)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, m.key)
            item.setIcon(QtGui.QIcon(self._swatch(m, (28, 18))))
            self.list.addItem(item)
        del blocker
        keys = [self.list.item(i).data(QtCore.Qt.ItemDataRole.UserRole) for i in range(self.list.count())]
        self.list.setCurrentRow(keys.index(select) if select in keys else 0)
        self._show(self._chosen())

    @staticmethod
    def _swatch(m, size):
        """A material in the list: its shading colour and its surface's patterns."""
        return pattern_paint.sample(m.surface_bg, m.surface_fg, size, base=QtGui.QColor.fromRgbF(*m.color),
                                    mm=pattern_paint.SAMPLE_MM * 0.6)

    def _chosen(self):
        item = self.list.currentItem()
        return catalog.MATERIALS.get(item.data(QtCore.Qt.ItemDataRole.UserRole)) if item is not None else None

    def select(self, key):
        self._fill_list(select=key)

    # ------------------------------------------------------------ the form

    def _show(self, m):
        self.current = m
        if m is None:
            return
        self._loading = True
        self.name.setText(_name(m))
        self.hatch.setCurrentIndex(max(0, self.hatch.findData(hatch_of(m.category, _name(m)))))
        self._set_colour(m.color)
        self.surface.set(m.surface_fg, m.surface_bg)
        self.transparency.setValue(round(float(m.transparency or 0.0) * 100))
        self.finish.setCurrentIndex(max(0, self.finish.findData(m.finish or "")))
        self.cut.set(m.cut_fg, m.cut_bg)
        self.density.setText(_text(m.density))
        self.conductivity.setText(_text(m.conductivity))
        self._loading = False
        self._refresh_samples()
        users = project_types.material_users(self.doc.ifc, m.key)
        names = ", ".join((s.name_pt if lang() == "pt" else s.name_en) for s in users[:4])
        self.used.setText(t("mat.used", n=len(users), names=names) if users else t("mat.unused"))
        self.remove.setEnabled(not users and not catalog.is_starter_material(m.key)
                               and project_types.find_material(self.doc.ifc, m) is not None)

    def _set_colour(self, colour):
        self.colour_button.set_colour(QtGui.QColor.fromRgbF(*[min(max(float(c), 0.0), 1.0) for c in colour]).name())

    def _refresh_samples(self):
        """The surface's and the cut's samples, as the form has them."""
        if self._loading:
            return
        fg, bg = self.surface.values()
        w, h = PREVIEW
        image = QtGui.QPixmap(w, h)
        image.fill(QtGui.QColor("white"))
        p = QtGui.QPainter(image)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        for y in range(0, h, 8):                          # (a light chequer: what shows through a clear one)
            for x in range(0, w, 8):
                if (x // 8 + y // 8) % 2:
                    p.fillRect(QtCore.QRectF(x, y, 8, 8), QtGui.QColor("#e3e6ea"))
        base = QtGui.QColor(self.colour_button.colour)
        base.setAlphaF(1.0 - self.transparency.value() / 100.0)
        p.fillRect(QtCore.QRectF(0, 0, w, h), base)
        path = QtGui.QPainterPath()
        path.addRect(QtCore.QRectF(0, 0, w, h))
        pattern_paint.paint_pair(p, path, bg, fg, pattern_paint.SAMPLE_MM, width=1.0)
        self._frame(p, w, h)
        p.end()
        self.surface_sample.setPixmap(image)
        cfg, cbg = self.cut.values()
        self.cut_note.setVisible(cfg is None and cbg is None)
        image = QtGui.QPixmap(w, h)
        image.fill(QtGui.QColor("white"))
        p = QtGui.QPainter(image)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        if cfg is None and cbg is None:                   # (its category's, in the project's graphic style)
            gstyle = getattr(self.doc, "graphic_style", None)
            fill, angles, spacing = styles_model.hatch(gstyle, self.hatch.currentData() or None)
            p.fillRect(QtCore.QRectF(0, 0, w, h), QtGui.QColor(fill))
            library = styles_model.library_pattern(gstyle, self.hatch.currentData() or None)
            if library:
                pattern_paint.paint(p, path, library, "black", pattern_paint.SAMPLE_MM, 1.0)
            p.setPen(QtGui.QPen(QtGui.QColor("black"), 1.0))
            step = max(spacing * pattern_paint.SAMPLE_MM, 2.0)
            for a in angles:
                d = QtCore.QPointF(math.cos(math.radians(a)), -math.sin(math.radians(a)))
                n = QtCore.QPointF(-d.y(), d.x())
                c = QtCore.QPointF(w / 2, h / 2)
                for k in range(-60, 61):
                    q = c + n * (k * step)
                    p.drawLine(q - d * 200, q + d * 200)
        else:
            pattern_paint.paint_pair(p, path, cbg, cfg, pattern_paint.SAMPLE_MM, width=1.0)
        self._frame(p, w, h)
        p.end()
        self.cut_sample.setPixmap(image)

    @staticmethod
    def _frame(p, w, h):
        p.setPen(QtGui.QPen(QtGui.QColor("#9aa3ad"), 1.0))
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.drawRect(QtCore.QRectF(0.5, 0.5, w - 1, h - 1))

    def draft(self):
        """The material as the form has it (a MaterialSpec with the shown one's key), or an error text."""
        m = self.current
        name = self.name.text().strip()
        if not name:
            return t("types.err_name")
        if any(_name(o) == name for o in catalog.MATERIALS.values() if o.key != m.key):
            return t("mat.err_same_name", name=name)
        density, conductivity = _number(self.density.text()), _number(self.conductivity.text())
        if density is False or conductivity is False:
            return t("mat.err_number")
        hatch = self.hatch.currentData()
        category = m.category if hatch == hatch_of(m.category, _name(m)) else hatch    # (kept unless changed)
        surface_fg, surface_bg = self.surface.values()
        cut_fg, cut_bg = self.cut.values()
        return catalog.MaterialSpec(m.key, name, name, category, self.colour, density, conductivity,
                                    surface_fg=surface_fg, surface_bg=surface_bg,
                                    transparency=self.transparency.value() / 100.0, cut_fg=cut_fg, cut_bg=cut_bg,
                                    finish=self.finish.currentData() or "")

    # ------------------------------------------------------------ actions

    def apply_changes(self):
        new = self.draft()
        if isinstance(new, str):
            QtWidgets.QMessageBox.warning(self, t("mat.title"), new)
            return None
        key = self.on_save(new, self.current) if self.on_save is not None else None
        if key is not None:
            self._fill_list(select=key)
        return key

    def _unique(self, base, copy=False):
        names = {_name(o) for o in catalog.MATERIALS.values()}
        if not copy and base not in names:
            return base
        n = 2
        while "{} ({})".format(base, n) in names:
            n += 1
        return "{} ({})".format(base, n)

    def new_material(self):
        name = self._unique(t("mat.new_name"))
        spec = catalog.MaterialSpec("m:new", name, name, "", (0.80, 0.80, 0.80))
        key = self.on_save(spec, None) if self.on_save is not None else None
        if key is not None:
            self._fill_list(select=key)
        return key

    def duplicate_material(self):
        m = self.draft()
        if isinstance(m, str):
            m = self.current
        name = self._unique(_name(m), copy=True)
        spec = dataclasses.replace(m, key="m:new", name_pt=name, name_en=name)     # (0.314: its graphics too)
        key = self.on_save(spec, None) if self.on_save is not None else None
        if key is not None:
            self._fill_list(select=key)
        return key

    def delete_material(self):
        if self.current is not None and self.on_delete is not None and self.on_delete(self.current):
            self._fill_list()
