"""The materials (0.89; 0.468: a panel of the column, no longer a window apart — the owner: «A aba materiais eu quero
que fique antes da aba biblioteca, e deve ser semelhante à biblioteca. a janela flutuante de criação e configuração dos
materiais deve ser redesenhada. Vai ter a aba editar/criar para esse efeito. tudo deve ser feito na coluna e nada de
janela flutuante nesse caso»). Two tabs, as SketchUp's Materials panel:

- «Selecionar»: the project's materials — the catalogue's and its own — as pictures (a cube each, as SketchUp's, or a
  sphere, as D5 Render's: ui/material_thumbs.py), by family and searched, small, medium, large or listed; one click
  paints with it (the Paint bucket on: SketchUp's), a double click edits it; New, Duplicate, Delete (only an unused one
  of the project's).
- «Editar»: the material chosen — its name and category (what it is drawn with where cut, kept as the IFC material's
  category), then, each a part that folds:
  - «Na vista» (3D, elevations; 0.314, as Revit's graphics): the surface — a foreground and a background pattern, each
    in its colour —, the shading colour and the transparency;
  - «Em corte» (plans, sections): a foreground and a background pattern (none: the category's pattern in the project's
    graphic style);
  - «Realista» (the realistic render; 0.468, as D5 Render's material editor — core/pbr.py): its kind (standard, glass,
    water, light, cloth) and a quick finish; its base colour, roughness, metallic, reflection, clear coat, a cloth's
    sheen, refraction, emission, each picture (texture) it may have — base colour, normal (relief), roughness,
    metallic, height, ambient occlusion, opacity, emission — and how they lie on the faces (their size in metres,
    turned, shifted);
  - «Dados»: its density and thermal conductivity (IFC4's Pset_MaterialCommon / Pset_MaterialThermal).
  A picture of it, lit, on top, follows each change. Applying is one undo step, done by the window (on_save).

The same editor goes into a window of its own only where a window asks for it (the type editor's «Materiais…»)."""

import dataclasses
import math
import os

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import pbr
from ..i18n import decimal_sep, lang, t
from ..ifc import catalog
from ..ifc.model import HATCH_WORDS
from ..model import graphic_styles as styles_model
from ..model import project_types
from ..model import render_scene
from . import material_thumbs
from . import pattern_paint
from .pattern_picker import PatternButton
from . import theme

HATCHES = ("", "concrete", "masonry", "wood", "insulation", "gypsum", "earth")
PREVIEW = (132, 84)                    # px: each sample
VIEWS = {"small": 44, "medium": 62, "large": 96, "list": 30}
SHAPES = material_thumbs.SHAPES
PICTURE = 170                          # px: the material's picture on the Edit tab
AT_ONCE = 8                            # pictures drawn a tick
SETTINGS = ("ArqSynth", "ArqSynth BIM")
KEY = QtCore.Qt.ItemDataRole.UserRole
# (0.468) the realistic controls each kind shows (as D5's: a glass no metal, a light its emission…)
SHOWN = {"standard": {"base", "roughness", "metallic", "specular", "clearcoat", "normal", "height", "ao", "opacity"},
         "glass": {"base", "roughness", "ior", "normal"},
         "water": {"base", "roughness", "ior", "normal"},
         "emissive": {"base", "emission", "intensity"},
         "cloth": {"base", "roughness", "sheen", "normal", "height", "ao", "opacity"}}


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
    """(0.397) The materials as the lists show them: those of `family` (None: all) whose name has every word searched,
    in alphabetical order."""
    words = words.strip().lower().split()
    found = [m for m in catalog.MATERIALS.values()
             if (family is None or catalog.family_of(m) == family)
             and all(w in (m.name_pt + " " + m.name_en).lower() for w in words)]
    return sorted(found, key=lambda m: _sort_key(_name(m)))


def family_combo():
    """(0.397) The families' list on top: «Todas as famílias», then each family."""
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


def _settings():
    return QtCore.QSettings(*SETTINGS)


class ColourButton(QtWidgets.QPushButton):
    """(0.314) A button showing a colour ("#rrggbb"); clicked, the colour chooser."""

    changed = QtCore.Signal()

    def __init__(self, title, colour="#000000", compact=False):
        super().__init__()
        self.title = title
        self.compact = compact                  # (0.468: in the column — no text, narrow)
        self.setMinimumWidth(36 if compact else 92)
        self.setToolTip(title)
        self.clicked.connect(self._pick)
        self.set_colour(colour)

    def set_colour(self, colour):
        q = QtGui.QColor(colour)
        self.colour = q.name()
        ink = "#000000" if q.lightnessF() > 0.5 else "#ffffff"
        self.setText("" if self.compact else self.colour)
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

    def __init__(self, grid, row, on_change, model=False, narrow=False):
        self.combos, self.colours = [], []
        for k, label in enumerate((t("mat.fg"), t("mat.bg"))):
            button = PatternButton(model=model)
            colour = ColourButton(t("mat.pattern_colour"), compact=narrow)
            colour.setToolTip(t("mat.pattern_colour"))
            if narrow:                                  # (0.468: in the column)
                button.setMinimumWidth(70)
                button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
                colour.setFixedWidth(40)
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


class _Section(QtWidgets.QWidget):
    """(0.468) A part of the form that folds: its title a button (▸ / ▾), open or not as left last time."""

    def __init__(self, title, key, opened=True):
        super().__init__()
        self.key = key
        col = QtWidgets.QVBoxLayout(self)
        col.setContentsMargins(0, 2, 0, 2)
        col.setSpacing(2)
        self.head = QtWidgets.QToolButton()
        self.head.setText(title)
        self.head.setCheckable(True)
        self.head.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.head.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.head.setStyleSheet("QToolButton { border: none; font-weight: 600; text-align: left; padding: 3px 2px; }")
        self.body = QtWidgets.QWidget()
        self.grid = QtWidgets.QGridLayout(self.body)
        self.grid.setContentsMargins(6, 0, 0, 4)
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(3)
        col.addWidget(self.head)
        col.addWidget(self.body)
        stored = _settings().value("materiais/aberta/" + key, None)
        self.head.toggled.connect(self._toggled)
        self.head.setChecked(opened if stored is None else str(stored).lower() in ("true", "1"))
        self._toggled(self.head.isChecked())

    def _toggled(self, on):
        self.head.setArrowType(QtCore.Qt.ArrowType.DownArrow if on else QtCore.Qt.ArrowType.RightArrow)
        self.body.setVisible(on)
        _settings().setValue("materiais/aberta/" + self.key, bool(on))


class Amount(QtWidgets.QWidget):
    """(0.468) A value as a slider and a number beside it (0–1 shown in %, or another range)."""

    changed = QtCore.Signal()

    def __init__(self, low=0.0, high=1.0, percent=True, decimals=2, suffix=""):
        super().__init__()
        self.low, self.high, self.percent = low, high, percent
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(0, 1000)
        self.spin = QtWidgets.QDoubleSpinBox()
        if percent:
            self.spin.setRange(low * 100.0, high * 100.0)
            self.spin.setDecimals(0)
            self.spin.setSuffix(" %")
        else:
            self.spin.setRange(low, high)
            self.spin.setDecimals(decimals)
            self.spin.setSuffix(suffix)
        self.spin.setMaximumWidth(58)
        self.spin.setMinimumWidth(44)
        self.slider.setMinimumWidth(30)
        self.spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin.setKeyboardTracking(False)
        row.addWidget(self.slider, 1)
        row.addWidget(self.spin)
        self.slider.valueChanged.connect(self._slid)
        self.spin.valueChanged.connect(self._typed)
        self._busy = False

    def value(self):
        v = self.spin.value()
        return v / 100.0 if self.percent else v

    def set_value(self, value):
        self._busy = True
        value = min(max(float(value), self.low), self.high)
        self.spin.setValue(value * 100.0 if self.percent else value)
        self.slider.setValue(round((value - self.low) / max(self.high - self.low, 1e-9) * 1000))
        self._busy = False

    def _slid(self, k):
        if self._busy:
            return
        self._busy = True
        value = self.low + (self.high - self.low) * k / 1000.0
        self.spin.setValue(value * 100.0 if self.percent else value)
        self._busy = False
        self.changed.emit()

    def _typed(self, _v):
        if self._busy:
            return
        self._busy = True
        self.slider.setValue(round((self.value() - self.low) / max(self.high - self.low, 1e-9) * 1000))
        self._busy = False
        self.changed.emit()


class PictureSlot(QtWidgets.QToolButton):
    """(0.468) A material's picture (texture) of one kind: its little picture (none: «+»); clicked, a picture file
    chosen (copied to the textures' folder, core/pbr.keep); right click: another, turned over (white for black), taken
    away."""

    changed = QtCore.Signal()

    def __init__(self, slot, beside=lambda: None):
        super().__init__()
        self.slot = slot
        self.beside = beside
        self.path, self.inverted = "", False
        self.setFixedSize(38, 38)
        self.setIconSize(QtCore.QSize(32, 32))
        self.setToolTip(t("matp.pic." + slot) + "\n" + t("matp.pic_tip"))
        self.clicked.connect(self.choose)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)
        self._show()

    def value(self):
        return (self.path, self.inverted) if self.path else None

    def set(self, value):
        self.path, self.inverted = (value[0], bool(value[1])) if value else ("", False)
        self._show()

    def take(self, path):
        """A picture file chosen: kept in the textures' folder, shown, said."""
        try:
            kept = pbr.keep(path)
        except OSError as exc:
            QtWidgets.QMessageBox.warning(self, t("matp.title"), t("matp.pic_failed", e=exc))
            return False
        self.path, self.inverted = kept, False
        self._show()
        self.changed.emit()
        return True

    def choose(self):
        start = os.path.dirname(self.path) if self.path else _settings().value("materiais/pasta_imagens", "") or \
            pbr.folder()
        path, _f = QtWidgets.QFileDialog.getOpenFileName(self, t("matp.pic_choose"), start, t("matp.pic_filter"))
        if path:
            _settings().setValue("materiais/pasta_imagens", os.path.dirname(path))
            self.take(path)

    def _menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction(t("matp.pic_change"), self.choose)
        if self.path:
            act = menu.addAction(t("matp.pic_invert"), self._invert)
            act.setCheckable(True)
            act.setChecked(self.inverted)
            menu.addAction(t("matp.pic_remove"), self.clear)
        menu.exec(self.mapToGlobal(pos))

    def _invert(self):
        self.inverted = not self.inverted
        self._show()
        self.changed.emit()

    def clear(self):
        if self.path:
            self.path, self.inverted = "", False
            self._show()
            self.changed.emit()

    def _show(self):
        size = 32
        pm = QtGui.QPixmap(size, size)
        pm.fill(QtGui.QColor(0, 0, 0, 0))
        p = QtGui.QPainter(pm)
        found = pbr.find(self.path, self.beside()) if self.path else None
        image = QtGui.QImage(found) if found else QtGui.QImage()
        if not image.isNull():
            if self.inverted:
                image.invertPixels()
            p.drawImage(QtCore.QRectF(0, 0, size, size), image)
        else:
            p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            pen = QtGui.QPen(QtGui.QColor(theme.C["note"]), 1, QtCore.Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.drawRoundedRect(QtCore.QRectF(1, 1, size - 2, size - 2), 4, 4)
            p.setPen(QtGui.QPen(QtGui.QColor("#d9534f" if self.path else theme.C["note"]), 1.6))
            if self.path:                                  # (not found where it was: a cross)
                p.drawLine(9, 9, size - 9, size - 9)
                p.drawLine(size - 9, 9, 9, size - 9)
            else:
                p.drawLine(size // 2, 10, size // 2, size - 10)
                p.drawLine(10, size // 2, size - 10, size // 2)
        p.end()
        self.setIcon(QtGui.QIcon(pm))
        if self.path:
            tip = t("matp.pic." + self.slot) + "\n" + (self.path if found else t("matp.pic_missing", f=self.path))
            self.setToolTip(tip + "\n" + t("matp.pic_tip"))
        else:
            self.setToolTip(t("matp.pic." + self.slot) + "\n" + t("matp.pic_tip"))


class MaterialEditor(QtWidgets.QWidget):
    """The materials: «Selecionar» (their pictures) and «Editar» (the one chosen) — see the module's note."""

    def __init__(self, parent, doc):
        super().__init__(parent)
        self.doc = doc
        self.on_save = None           # (spec, old spec or None) -> the saved material's key, or None
        self.on_delete = None         # (spec) -> True if removed
        self.on_pick = None           # (0.468) (key): a material clicked — the Paint bucket's
        self.current = None
        self._loading = False
        self._dirty = False           # (0.468) the form changed since shown / applied
        self._look_touched = False    # …its realistic look changed
        self._queue, self._generation = [], 0
        self.painting = False         # (0.468) the Paint bucket on: «Sem pintura» first
        s = _settings()
        self.view = s.value("materiais/vista", "medium")
        self.view = self.view if self.view in VIEWS else "medium"
        self.shape = s.value("materiais/forma", "cube")
        self.shape = self.shape if self.shape in SHAPES else "cube"
        self.preview_shape = s.value("materiais/forma_editar", "sphere")
        self.preview_shape = self.preview_shape if self.preview_shape in SHAPES else "sphere"
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        outer.addWidget(self.tabs, 1)
        self.tabs.addTab(self._select_page(), t("matp.tab.select"))
        self.tabs.addTab(self._edit_page(), t("matp.tab.edit"))
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(0)
        self._timer.timeout.connect(self._next_pictures)
        self._redraw = QtCore.QTimer(self)                 # (the picture after a change: once things settle)
        self._redraw.setSingleShot(True)
        self._redraw.setInterval(60)
        self._redraw.timeout.connect(self._refresh_picture)
        self._apply_view()
        self._fill_list()

    # ------------------------------------------------------------ «Selecionar»

    def _select_page(self):
        page = QtWidgets.QWidget()
        col = QtWidgets.QVBoxLayout(page)
        col.setContentsMargins(0, 4, 0, 0)
        col.setSpacing(4)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(2)
        self.new = QtWidgets.QPushButton(t("mat.new"))
        self.new.setToolTip(t("tip.matp.new"))
        self.duplicate = QtWidgets.QPushButton(t("types.duplicate"))
        self.duplicate.setToolTip(t("tip.matp.duplicate"))
        self.remove = QtWidgets.QPushButton(t("types.delete"))
        for b in (self.new, self.duplicate, self.remove):
            row.addWidget(b)
        row.addStretch(1)
        self.view_button = QtWidgets.QToolButton()
        self.view_button.setText("▦")
        self.view_button.setToolTip(t("libp.view"))
        self.view_button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QtWidgets.QMenu(self.view_button)
        self.view_actions, self.shape_actions = {}, {}
        group = QtGui.QActionGroup(self)
        for v in VIEWS:
            act = menu.addAction(t("libp.view." + v), lambda v=v: self.set_view(v))
            act.setCheckable(True)
            act.setChecked(v == self.view)
            group.addAction(act)
            self.view_actions[v] = act
        menu.addSeparator()
        shapes = QtGui.QActionGroup(self)
        for s in SHAPES:
            act = menu.addAction(t("matp.shape." + s), lambda s=s: self.set_shape(s))
            act.setCheckable(True)
            act.setChecked(s == self.shape)
            shapes.addAction(act)
            self.shape_actions[s] = act
        self.view_button.setMenu(menu)
        row.addWidget(self.view_button)
        col.addLayout(row)
        self.family = family_combo()                    # (0.397) by family, and a search
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText(t("mat.search"))
        self.search.setClearButtonEnabled(True)
        col.addWidget(self.family)
        col.addWidget(self.search)
        self.list = QtWidgets.QListWidget()
        self.list.setObjectName("materials_grid")
        self.list.setMovement(QtWidgets.QListView.Movement.Static)
        self.list.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.list.setUniformItemSizes(True)
        self.list.setWordWrap(True)
        self.list.setSpacing(3)
        self.list.setMinimumWidth(200)
        col.addWidget(self.list, 1)
        self.hint = QtWidgets.QLabel(t("matp.hint"))
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        col.addWidget(self.hint)
        self.family.currentIndexChanged.connect(lambda _i: self._fill_list(self._chosen_key(), force=False))
        self.search.textChanged.connect(lambda _t: self._fill_list(self._chosen_key(), force=False))
        self.list.currentItemChanged.connect(self._current_changed)
        self.list.itemClicked.connect(self._clicked)
        self.list.itemDoubleClicked.connect(lambda _item: self.tabs.setCurrentIndex(1))
        self.new.clicked.connect(self.new_material)
        self.duplicate.clicked.connect(self.duplicate_material)
        self.remove.clicked.connect(self.delete_material)
        return page

    # ------------------------------------------------------------ «Editar»

    def _edit_page(self):
        page = QtWidgets.QWidget()
        col = QtWidgets.QVBoxLayout(page)
        col.setContentsMargins(0, 4, 0, 0)
        col.setSpacing(4)
        top = QtWidgets.QHBoxLayout()
        self.picture = QtWidgets.QLabel()
        self.picture.setFixedSize(PICTURE // 2 + 6, PICTURE // 2 + 6)
        self.picture.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        top.addWidget(self.picture)
        side = QtWidgets.QVBoxLayout()
        self.name = QtWidgets.QLineEdit()
        self.name.setPlaceholderText(t("types.name"))
        side.addWidget(self.name)
        shapes = QtWidgets.QHBoxLayout()
        shapes.setSpacing(2)
        self.preview_buttons = {}
        group = QtWidgets.QButtonGroup(self)
        for s in SHAPES:
            b = QtWidgets.QToolButton()
            b.setText(t("matp.shape1." + s))
            b.setCheckable(True)
            b.setChecked(s == self.preview_shape)
            b.clicked.connect(lambda _on=False, s=s: self.set_preview_shape(s))
            group.addButton(b)
            shapes.addWidget(b)
            self.preview_buttons[s] = b
        shapes.addStretch(1)
        side.addLayout(shapes)
        self.used = QtWidgets.QLabel()
        self.used.setWordWrap(True)
        self.used.setStyleSheet("QLabel { color: %s; }" % theme.C["ctx_text"])
        side.addWidget(self.used)
        side.addStretch(1)
        top.addLayout(side, 1)
        col.addLayout(top)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QtWidgets.QWidget()
        form = QtWidgets.QVBoxLayout(inner)
        form.setContentsMargins(0, 0, 4, 0)
        form.setSpacing(2)
        head = QtWidgets.QFormLayout()
        head.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.hatch = QtWidgets.QComboBox()
        for h in HATCHES:
            self.hatch.addItem(t("mat.hatch." + (h or "none")), h)
        self.hatch.setMinimumWidth(80)
        self.hatch.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
        head.addRow(t("matp.category"), self.hatch)
        form.addLayout(head)

        # «Na vista» (0.314): the surface's patterns, the shading colour, how clear
        view = _Section(t("matp.section.view"), "vista")
        g = view.grid
        self.surface = _Pair(g, 0, self._changed, model=True, narrow=True)
        g.addWidget(QtWidgets.QLabel(t("matp.shading")), 2, 0)
        self.colour_button = ColourButton(t("mat.shading"))
        self.colour_button.setMinimumWidth(70)
        self.colour_button.changed.connect(self._changed)
        g.addWidget(self.colour_button, 2, 1, 1, 2)
        g.addWidget(QtWidgets.QLabel(t("mat.transparency")), 3, 0)
        self.transparency = QtWidgets.QSpinBox()
        self.transparency.setRange(0, 100)
        self.transparency.setSuffix(" %")
        self.transparency.valueChanged.connect(lambda _v: self._changed())
        g.addWidget(self.transparency, 3, 1, 1, 2)
        self.surface_sample = _Sample(lambda: self.surface.combos[0].pick())
        self.surface_sample.setFixedSize(*PREVIEW)
        g.addWidget(self.surface_sample, 4, 0, 1, 3, QtCore.Qt.AlignmentFlag.AlignLeft)
        g.addWidget(self._hint(), 5, 0, 1, 3)
        form.addWidget(view)

        # «Em corte»: its patterns (none: its category's, in the project's graphic style)
        cut = _Section(t("matp.section.cut"), "corte")
        g = cut.grid
        self.cut = _Pair(g, 0, self._changed, model=False, narrow=True)
        self.cut_note = QtWidgets.QLabel(t("mat.cut_by_category"))
        self.cut_note.setWordWrap(True)
        self.cut_note.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        g.addWidget(self.cut_note, 2, 0, 1, 3)
        self.cut_sample = _Sample(lambda: self.cut.combos[0].pick())
        self.cut_sample.setFixedSize(*PREVIEW)
        g.addWidget(self.cut_sample, 3, 0, 1, 3, QtCore.Qt.AlignmentFlag.AlignLeft)
        g.addWidget(self._hint(), 4, 0, 1, 3)
        form.addWidget(cut)
        self.hatch.currentIndexChanged.connect(lambda _i: self._changed())

        # «Realista» (0.468), as D5 Render's
        real = _Section(t("matp.section.real"), "realista")
        form.addWidget(real)
        self._real_rows = {}
        g = real.grid
        self.kind = QtWidgets.QComboBox()
        for k in pbr.KINDS:
            self.kind.addItem(t("matp.kind." + k), k)
        self.kind.currentIndexChanged.connect(lambda _i: self._kind_changed())
        g.addWidget(QtWidgets.QLabel(t("matp.kind")), 0, 0)
        g.addWidget(self.kind, 0, 1, 1, 2)
        self.preset = QtWidgets.QComboBox()
        self.preset.addItem(t("matp.preset.custom"), "")
        for name in pbr.PRESETS:
            self.preset.addItem(t("matp.preset." + name), name)
        self.preset.setToolTip(t("tip.matp.preset"))
        for combo in (self.kind, self.preset):
            combo.setMinimumWidth(80)
            combo.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
        self.preset.activated.connect(lambda _i: self._preset_chosen())
        g.addWidget(QtWidgets.QLabel(t("matp.preset")), 1, 0)
        g.addWidget(self.preset, 1, 1, 1, 2)
        beside = self._beside
        self.slots = {s: PictureSlot(s, beside) for s in pbr.SLOTS}
        for s in self.slots.values():
            s.changed.connect(lambda s=s: self._slot_changed(s))
        # the base colour: its own, else the shading colour (with a picture: the picture as it is)
        base = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(base)
        h.setContentsMargins(0, 0, 0, 0)
        self.base_own = QtWidgets.QCheckBox(t("matp.base_own"))
        self.base_own.setToolTip(t("tip.matp.base_own"))
        self.base_colour = ColourButton(t("matp.base"), compact=True)
        h.addWidget(self.base_own)
        h.addWidget(self.base_colour, 1)
        self.base_own.toggled.connect(lambda _on: self._real_changed())
        self.base_colour.changed.connect(lambda: (self.base_own.setChecked(True), self._real_changed()))
        self.roughness = Amount()
        self.metallic = Amount()
        self.specular = Amount()
        self.clearcoat = Amount()
        self.sheen = Amount()
        self.ior = Amount(1.0, 3.0, percent=False, decimals=2)
        self.normal = Amount(0.0, 5.0, percent=False, decimals=2)
        self.height = Amount(0.0, 50.0, percent=False, decimals=1, suffix=" cm")
        self.ao = Amount()
        for w in (self.roughness, self.metallic, self.specular, self.clearcoat, self.sheen, self.ior, self.normal,
                  self.height, self.ao):
            w.changed.connect(self._real_changed)
        self.roughness.setToolTip(t("tip.matp.roughness"))
        self.metallic.setToolTip(t("tip.matp.metallic"))
        opacity_note = QtWidgets.QLabel(t("matp.opacity_note"))
        opacity_note.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        opacity_note.setWordWrap(True)
        self.emission_colour = ColourButton(t("matp.emission"), "#ffffff")
        self.emission_colour.setMinimumWidth(70)
        self.emission = QtWidgets.QDoubleSpinBox()
        self.emission.setRange(0.0, 1.0e6)
        self.emission.setDecimals(0)
        self.emission.setSingleStep(100.0)
        self.emission.setSuffix(" cd/m²")
        self.emission.setKeyboardTracking(False)
        self.emission.setMinimumWidth(70)
        self.emission_colour.changed.connect(self._real_changed)
        self.emission.valueChanged.connect(lambda _v: self._real_changed())
        rows = (("base", base, "base"), ("roughness", self.roughness, "roughness"),
                ("metallic", self.metallic, "metallic"), ("specular", self.specular, None),
                ("clearcoat", self.clearcoat, None), ("sheen", self.sheen, None), ("ior", self.ior, None),
                ("normal", self.normal, "normal"), ("height", self.height, "height"), ("ao", self.ao, "ao"),
                ("opacity", opacity_note, "opacity"), ("emission", self.emission_colour, "emission"),
                ("intensity", self.emission, None))
        for k, (name, widget, slot) in enumerate(rows, start=2):
            label = QtWidgets.QLabel(t("matp." + name))
            label.setWordWrap(True)                     # (the column narrow: «Altura do / relevo»)
            g.addWidget(label, k, 0)
            g.addWidget(widget, k, 1)
            parts = [label, widget]
            if slot:
                g.addWidget(self.slots[slot], k, 2)
                parts.append(self.slots[slot])
            self._real_rows[name] = parts
        k = len(rows) + 2
        # how the pictures lie on the faces: their size in the model, turned, shifted
        mapping = QtWidgets.QLabel(t("matp.mapping"))
        mapping.setStyleSheet("QLabel { font-weight: 600; }")
        g.addWidget(mapping, k, 0, 1, 3)
        self.map_width, self.map_height = self._metres(), self._metres()
        self.keep_ratio = QtWidgets.QToolButton()
        self.keep_ratio.setText("🔗")
        self.keep_ratio.setCheckable(True)
        self.keep_ratio.setChecked(True)
        self.keep_ratio.setToolTip(t("tip.matp.keep_ratio"))
        size = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(size)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self.map_width, 1)
        h.addWidget(QtWidgets.QLabel("×"))
        h.addWidget(self.map_height, 1)
        g.addWidget(QtWidgets.QLabel(t("matp.size")), k + 1, 0)
        g.addWidget(size, k + 1, 1)
        g.addWidget(self.keep_ratio, k + 1, 2)
        self.map_width.valueChanged.connect(lambda _v: self._size_changed(self.map_width))
        self.map_height.valueChanged.connect(lambda _v: self._size_changed(self.map_height))
        self.rotation = QtWidgets.QDoubleSpinBox()
        self.rotation.setRange(-360.0, 360.0)
        self.rotation.setDecimals(1)
        self.rotation.setSuffix(" °")
        self.rotation.setKeyboardTracking(False)
        self.rotation.setMinimumWidth(60)
        self.rotation.valueChanged.connect(lambda _v: self._real_changed())
        g.addWidget(QtWidgets.QLabel(t("matp.rotation")), k + 2, 0)
        g.addWidget(self.rotation, k + 2, 1)
        self.offset_x, self.offset_y = self._metres(-1000.0), self._metres(-1000.0)
        for w in (self.offset_x, self.offset_y):
            w.valueChanged.connect(lambda _v: self._real_changed())
        shift = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(shift)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self.offset_x, 1)
        h.addWidget(self.offset_y, 1)
        g.addWidget(QtWidgets.QLabel(t("matp.offset")), k + 3, 0)
        g.addWidget(shift, k + 3, 1)
        self.mapping_rows = [mapping, size, self.keep_ratio, self.rotation, shift]
        g.setColumnStretch(1, 1)

        # «Dados»
        data = _Section(t("matp.section.data"), "dados", opened=False)
        g = data.grid
        self.density = QtWidgets.QLineEdit()
        self.density.setPlaceholderText(t("mat.not_given"))
        g.addWidget(QtWidgets.QLabel(t("mat.density")), 0, 0)
        g.addWidget(self.density, 0, 1)
        self.conductivity = QtWidgets.QLineEdit()
        self.conductivity.setPlaceholderText(t("mat.not_given"))
        g.addWidget(QtWidgets.QLabel(t("mat.conductivity")), 1, 0)
        g.addWidget(self.conductivity, 1, 1)
        for w in (self.density, self.conductivity):
            w.setMaximumWidth(110)
        form.addWidget(data)
        form.addStretch(1)
        scroll.setWidget(inner)
        col.addWidget(scroll, 1)
        self.edit_scroll = scroll
        bottom = QtWidgets.QHBoxLayout()
        self.revert = QtWidgets.QPushButton(t("matp.revert"))
        self.revert.setToolTip(t("tip.matp.revert"))
        self.apply = QtWidgets.QPushButton(t("types.apply"))
        self.apply.setDefault(True)
        bottom.addStretch(1)
        bottom.addWidget(self.revert)
        bottom.addWidget(self.apply)
        col.addLayout(bottom)
        self.name.textEdited.connect(lambda _t: self._changed())
        for w in (self.density, self.conductivity):
            w.textEdited.connect(lambda _t: self._changed())
        self.apply.clicked.connect(self.apply_changes)
        self.revert.clicked.connect(lambda: self._show(self.current))
        return page

    def _metres(self, low=0.001):
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(low, 1000.0)
        spin.setDecimals(2)
        spin.setMinimumWidth(48)                 # (narrow: the column's width)
        spin.setSingleStep(0.05)
        spin.setSuffix(" m")
        spin.setKeyboardTracking(False)
        spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        return spin

    @staticmethod
    def _hint():
        """(0.319) A group's line of advice: the pattern is chosen by clicking it."""
        hint = QtWidgets.QLabel(t("mat.pick_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        return hint

    def _beside(self):
        """The project's folder (a picture not found where it was is looked for there)."""
        path = getattr(self.doc, "path", None)
        return os.path.dirname(path) if path else None

    @property
    def colour(self):
        """The shading colour chosen (RGB 0..1)."""
        q = QtGui.QColor(self.colour_button.colour)
        return q.redF(), q.greenF(), q.blueF()

    # ------------------------------------------------------------ how the list is shown

    def set_view(self, view):
        if view in VIEWS:
            self.view = view
            self.view_actions[view].setChecked(True)
            _settings().setValue("materiais/vista", view)
            self._apply_view()
            self._fill_list(self._chosen_key(), force=False)

    def set_shape(self, shape):
        if shape in SHAPES:
            self.shape = shape
            self.shape_actions[shape].setChecked(True)
            _settings().setValue("materiais/forma", shape)
            self._fill_list(self._chosen_key(), force=False)

    def set_preview_shape(self, shape):
        if shape in SHAPES:
            self.preview_shape = shape
            self.preview_buttons[shape].setChecked(True)
            _settings().setValue("materiais/forma_editar", shape)
            self._refresh_picture()

    def _apply_view(self):
        size = VIEWS[self.view]
        self.list.setIconSize(QtCore.QSize(size, size))
        if self.view == "list":
            self.list.setViewMode(QtWidgets.QListView.ViewMode.ListMode)
            self.list.setGridSize(QtCore.QSize())
        else:
            self.list.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
            self.list.setGridSize(QtCore.QSize(size + 16, size + 34))

    # ------------------------------------------------------------ the list

    def _shown(self, m):
        """(0.318) Is a material in the list as filtered (its family, the words searched)?"""
        family = self.family.currentData()
        words = self.search.text().strip().lower()
        return (family is None or catalog.family_of(m) == family) and \
            all(w in (m.name_pt + " " + m.name_en).lower() for w in words.split())

    def _chosen_key(self):
        item = self.list.currentItem()
        return item.data(KEY) if item is not None else None

    def _blank(self):
        size = VIEWS[self.view]
        pm = QtGui.QPixmap(size, size)
        pm.fill(QtGui.QColor(0, 0, 0, 0))
        return QtGui.QIcon(pm)

    def _no_paint(self):
        """«Sem pintura»'s picture: an empty square, crossed."""
        size = VIEWS[self.view]
        pm = QtGui.QPixmap(size, size)
        pm.fill(QtGui.QColor(0, 0, 0, 0))
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        m = size * 0.16
        p.setPen(QtGui.QPen(QtGui.QColor(theme.C["note"]), 1.4))
        p.setBrush(QtGui.QColor("#ffffff"))
        p.drawRoundedRect(QtCore.QRectF(m, m, size - 2 * m, size - 2 * m), 4, 4)
        p.setPen(QtGui.QPen(QtGui.QColor("#d9534f"), 2.0))
        p.drawLine(QtCore.QPointF(m + 3, size - m - 3), QtCore.QPointF(size - m - 3, m + 3))
        p.end()
        return QtGui.QIcon(pm)

    def set_painting(self, on):
        """(0.468) The Paint bucket on or off: «Sem pintura» listed first, or not."""
        if bool(on) != self.painting:
            self.painting = bool(on)
            self._fill_list(self._chosen_key(), force=False)

    def _fill_list(self, select=None, force=True):
        """The list as filtered; `select` chosen in it — force: shown even if the filter hides it (one asked for, one
        just saved), the filter undone. Each its picture, drawn a few at a time."""
        blocker = QtCore.QSignalBlocker(self.list)
        self.list.clear()
        if force and select in catalog.MATERIALS and not self._shown(catalog.MATERIALS[select]):
            for w in (self.family, self.search):            # (one asked for: shown, whatever the filter)
                w.blockSignals(True)
            self.family.setCurrentIndex(0)
            self.search.clear()
            for w in (self.family, self.search):
                w.blockSignals(False)
        self._generation += 1
        self._queue = []
        blank = self._blank()
        list_mode = self.view == "list"
        align = QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter if list_mode else \
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        if self.painting:                       # (0.391: «Sem pintura» first — the paint taken off; SketchUp's Default)
            item = QtWidgets.QListWidgetItem(self._no_paint(), t("paint.none"))
            item.setData(KEY, "")
            item.setToolTip(t("tip.matp.no_paint"))
            item.setTextAlignment(align)
            self.list.addItem(item)
        for m in listed(self.family.currentData(), self.search.text()):        # (0.397: alphabetical)
            item = QtWidgets.QListWidgetItem(blank, _name(m))
            item.setData(KEY, m.key)
            item.setToolTip(_name(m))
            item.setTextAlignment(align)
            self.list.addItem(item)
            self._queue.append((self._generation, item, m.key))
        del blocker
        keys = [self.list.item(i).data(KEY) for i in range(self.list.count())]
        row = keys.index(select) if select in keys else (1 if self.painting and len(keys) > 1 else 0)
        if self.list.count():
            blocker = QtCore.QSignalBlocker(self.list)
            self.list.setCurrentRow(row)
            del blocker
            self.list.scrollToItem(self.list.item(row))
        chosen = self._chosen()
        if chosen is None or self.current is None or chosen.key != self.current.key or not self._dirty:
            self._show(chosen)
        if self._queue:
            self._timer.start()

    def _next_pictures(self):
        """A few more of the list's pictures drawn."""
        size = max(VIEWS[self.view], 48)
        for _k in range(AT_ONCE):
            if not self._queue:
                self._timer.stop()
                return
            generation, item, key = self._queue.pop(0)
            m = catalog.MATERIALS.get(key)
            if generation != self._generation or m is None:
                continue
            try:
                image = material_thumbs.material_image(m, size, self.shape, self._beside())
            except Exception:                              # (a picture that cannot be drawn: its blank tile)
                continue
            item.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(image)))

    def finish_pictures(self):
        """Every picture of the list drawn now (tests, an image of the panel)."""
        while self._queue:
            self._next_pictures()
        self._timer.stop()

    def _chosen(self):
        item = self.list.currentItem()
        return catalog.MATERIALS.get(item.data(KEY)) if item is not None else None

    def select(self, key):
        self._fill_list(select=key)

    def materials_changed(self):
        """(0.468) The project's materials changed (saved, undone, another project): the list again, the one chosen
        kept — and its form, unless it is being changed."""
        self._fill_list(self._chosen_key(), force=False)

    def mark(self, key):
        """(0.468) The Paint bucket's material marked in the list (no form asked about)."""
        for k in range(self.list.count()):
            item = self.list.item(k)
            if (item.data(KEY) or "") == (key or ""):
                if self.list.currentItem() is not item:
                    self.list.setCurrentItem(item)
                self.list.scrollToItem(item)
                return

    def _current_changed(self, item, previous):
        """Another material chosen: its form — one being changed first applied or not, as asked."""
        if self._loading:
            return
        if self._dirty and self.current is not None and not self._settle():
            blocker = QtCore.QSignalBlocker(self.list)
            self.list.setCurrentItem(previous)
            del blocker
            return
        self._show(catalog.MATERIALS.get(item.data(KEY)) if item is not None else None)

    def _settle(self):
        """(0.468) The form changed and another material asked for: apply, leave or stay? True to go on."""
        box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Question, t("matp.title"),
                                    t("matp.ask_apply", name=_name(self.current)), parent=self)
        apply = box.addButton(t("types.apply"), QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        box.addButton(t("matp.discard"), QtWidgets.QMessageBox.ButtonRole.DestructiveRole)
        stay = box.addButton(t("matp.stay"), QtWidgets.QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is stay:
            return False
        if box.clickedButton() is apply:
            return self.apply_changes() is not None
        self._dirty = False
        return True

    def _clicked(self, item):
        """(0.468) One click: the Paint bucket takes it (SketchUp's)."""
        if item is not None and self.on_pick is not None:
            self.on_pick(item.data(KEY))

    # ------------------------------------------------------------ the form

    def _show(self, m):
        self.current = m
        self._dirty = self._look_touched = False
        if m is None:
            self.apply.setEnabled(False)
            self.revert.setEnabled(False)
            return
        self._loading = True
        self.name.setText(_name(m))
        self.hatch.setCurrentIndex(max(0, self.hatch.findData(hatch_of(m.category, _name(m)))))
        self._set_colour(m.color)
        self.surface.set(m.surface_fg, m.surface_bg)
        self.transparency.setValue(round(float(m.transparency or 0.0) * 100))
        self.cut.set(m.cut_fg, m.cut_bg)
        self.density.setText(_text(m.density))
        self.conductivity.setText(_text(m.conductivity))
        self._set_look(render_scene.look_of(m))
        self._loading = False
        self._refresh_samples()
        self._refresh_picture()
        users = project_types.material_users(self.doc.ifc, m.key)
        names = ", ".join((s.name_pt if lang() == "pt" else s.name_en) for s in users[:4])
        self.used.setText(t("mat.used", n=len(users), names=names) if users else t("mat.unused"))
        self.remove.setEnabled(not users and not catalog.is_starter_material(m.key)
                               and project_types.find_material(self.doc.ifc, m) is not None)
        self.apply.setEnabled(False)
        self.revert.setEnabled(False)

    def _set_colour(self, colour):
        self.colour_button.set_colour(QtGui.QColor.fromRgbF(*[min(max(float(c), 0.0), 1.0) for c in colour]).name())

    def _set_look(self, look):
        """The realistic controls as a look has them."""
        self.kind.setCurrentIndex(max(0, self.kind.findData(look.kind)))
        self.preset.setCurrentIndex(max(0, self.preset.findData(pbr.preset_of(look))))
        self.base_own.setChecked(bool(look.tint))
        self.base_colour.set_colour(look.tint or self.colour_button.colour)
        for name in ("roughness", "metallic", "specular", "clearcoat", "sheen", "ior", "normal", "ao"):
            getattr(self, name).set_value(getattr(look, name))
        self.height.set_value(look.height * 100.0)
        self.emission_colour.set_colour(look.emission_colour)
        self.emission.setValue(look.emission)
        for slot, widget in self.slots.items():
            widget.set(look.map(slot))
        for spin, value in ((self.map_width, look.width), (self.map_height, look.height_m),
                            (self.rotation, look.rotation), (self.offset_x, look.offset_x),
                            (self.offset_y, look.offset_y)):
            spin.setValue(value)
        self._show_kind(look.kind)

    def look(self):
        """(0.468) The realistic look as the form has it (core/pbr.Look)."""
        maps = tuple((slot, *w.value()) for slot, w in self.slots.items() if w.value() is not None)
        return pbr.Look(kind=self.kind.currentData() or "standard", roughness=self.roughness.value(),
                        metallic=self.metallic.value(), specular=self.specular.value(),
                        clearcoat=self.clearcoat.value(), sheen=self.sheen.value(), ior=self.ior.value(),
                        emission=self.emission.value(), emission_colour=self.emission_colour.colour,
                        tint=self.base_colour.colour if self.base_own.isChecked() else "", maps=maps,
                        normal=self.normal.value(), height=self.height.value() / 100.0, ao=self.ao.value(),
                        width=self.map_width.value(), height_m=self.map_height.value(),
                        rotation=self.rotation.value(), offset_x=self.offset_x.value(),
                        offset_y=self.offset_y.value())

    def _show_kind(self, kind):
        shown = SHOWN.get(kind, SHOWN["standard"])
        for name, parts in self._real_rows.items():
            for w in parts:
                w.setVisible(name in shown)

    def _changed(self):
        """Something of the form changed: kept to apply; the samples and the picture again."""
        if self._loading:
            return
        self._dirty = True
        self.apply.setEnabled(True)
        self.revert.setEnabled(True)
        self._refresh_samples()
        self._redraw.start()

    def _real_changed(self):
        if self._loading:
            return
        self._look_touched = True
        self._loading = True
        self.preset.setCurrentIndex(max(0, self.preset.findData(pbr.preset_of(self.look()))))
        self._loading = False
        self._changed()

    def _kind_changed(self):
        if self._loading:
            return
        self._show_kind(self.kind.currentData())
        self._real_changed()

    def _preset_chosen(self):
        name = self.preset.currentData()
        if not name:
            return
        look = pbr.preset(name, self.look())
        self._loading = True
        self._set_look(look)
        self._loading = False
        self._look_touched = True
        self._changed()

    def _slot_changed(self, slot):
        """A picture chosen or taken away: with a roughness or metallic one, its value 50 % (the picture as it is); a
        base picture's size in the model, as its proportions."""
        if self._loading:
            return
        if slot.path and slot.slot in ("roughness", "metallic"):
            getattr(self, slot.slot).set_value(pbr.AS_PICTURE)
        if slot.path and slot.slot == "base":
            image = QtGui.QImageReader(pbr.find(slot.path, self._beside()) or "")
            size = image.size()
            if size.isValid() and size.width() > 0:
                self._loading = True
                self.map_height.setValue(self.map_width.value() * size.height() / size.width())
                self._loading = False
        self._real_changed()

    def _size_changed(self, spin):
        if self._loading:
            return
        if self.keep_ratio.isChecked():
            other = self.map_height if spin is self.map_width else self.map_width
            ratio = self._ratio()
            self._loading = True
            if ratio:
                other.setValue(spin.value() * ratio if spin is self.map_width else spin.value() / ratio)
            self._loading = False
        self._real_changed()

    def _ratio(self):
        """Height over width of the base picture (else of its other pictures), or None."""
        for slot in pbr.SLOTS:
            value = self.slots[slot].value()
            if value:
                size = QtGui.QImageReader(pbr.find(value[0], self._beside()) or "").size()
                if size.isValid() and size.width() > 0:
                    return size.height() / size.width()
        return None

    def _refresh_picture(self):
        """The material's picture on top, as the form has it."""
        if self.current is None:
            self.picture.clear()
            return
        spec = self.draft()
        if isinstance(spec, str):
            spec = self.current
        if not self._look_touched and spec.look is None:
            spec = dataclasses.replace(spec, look=render_scene.look_of(spec))
        try:
            look = spec.look
            pattern = material_thumbs.pattern_of(spec, 128) if look.map("base") is None else None
            image = material_thumbs.render(spec.color, look, PICTURE, self.preview_shape, spec.transparency, pattern,
                                           self._beside())
        except Exception:                                  # (never a broken form for a picture)
            return
        pm = QtGui.QPixmap.fromImage(image)
        pm = pm.scaled(PICTURE // 2 + 4, PICTURE // 2 + 4, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                       QtCore.Qt.TransformationMode.SmoothTransformation)
        self.picture.setPixmap(pm)

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
        look, finish = m.look, m.finish or ""
        if self._look_touched:                              # (0.468: its own look, and the finish nearest it)
            look = self.look()
            finish = pbr.finish_of(look)
        return catalog.MaterialSpec(m.key, name, name, category, self.colour, density, conductivity,
                                    surface_fg=surface_fg, surface_bg=surface_bg,
                                    transparency=self.transparency.value() / 100.0, cut_fg=cut_fg, cut_bg=cut_bg,
                                    finish=finish, look=look)

    # ------------------------------------------------------------ actions

    def apply_changes(self):
        new = self.draft()
        if isinstance(new, str):
            QtWidgets.QMessageBox.warning(self, t("matp.title"), new)
            return None
        key = self.on_save(new, self.current) if self.on_save is not None else None
        if key is not None:
            self._dirty = False
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
            self._dirty = False
            self._fill_list(select=key)
            self.tabs.setCurrentIndex(1)
        return key

    def duplicate_material(self):
        m = self.draft() if self.current is not None else None
        if isinstance(m, str) or m is None:
            m = self.current
        if m is None:
            return None
        name = self._unique(_name(m), copy=True)
        spec = dataclasses.replace(m, key="m:new", name_pt=name, name_en=name)     # (0.314: its graphics too)
        key = self.on_save(spec, None) if self.on_save is not None else None
        if key is not None:
            self._dirty = False
            self._fill_list(select=key)
            self.tabs.setCurrentIndex(1)
        return key

    def delete_material(self):
        if self.current is not None and self.on_delete is not None and self.on_delete(self.current):
            self._dirty = False
            self._fill_list()


class MaterialsPanel(QtWidgets.QDockWidget):
    """(0.468) The materials in the column: the module bar's «Materiais», before the Library."""

    def __init__(self, parent, doc):
        super().__init__(t("matp.title"), parent)
        self.setObjectName("materials")
        self.editor = MaterialEditor(self, doc)
        self.setWidget(self.editor)
        self.visibilityChanged.connect(lambda shown: self.editor._fill_list(self.editor._chosen_key(), force=False)
                                       if shown and self._stale else None)
        self._stale = False

    def materials_changed(self):
        if self.isVisible():
            self.editor.materials_changed()
            self._stale = False
        else:
            self._stale = True


class MaterialsDialog(QtWidgets.QDialog):
    """(0.468) The same editor in a window of its own — only where a window asks for it (the type editor's
    «Materiais…»: a window over the others, the column out of reach)."""

    def __init__(self, parent, doc):
        super().__init__(parent)
        self.setWindowTitle(t("matp.title"))
        col = QtWidgets.QVBoxLayout(self)
        col.setContentsMargins(4, 4, 4, 4)
        self.editor = MaterialEditor(self, doc)
        col.addWidget(self.editor, 1)
        close = QtWidgets.QPushButton(t("types.close"))
        close.clicked.connect(self.reject)
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close)
        col.addLayout(row)
        self.resize(420, 720)


def dock(parent, doc):
    """The panel, hidden until the module bar's Materials brings it up (the window puts it with the left panels)."""
    panel = MaterialsPanel(parent, doc)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, panel)
    panel.hide()
    return panel
