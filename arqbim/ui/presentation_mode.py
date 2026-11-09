"""(0.479) The ArqSynth Presentation tab — the owner, 2026-11-08, with a picture of the Presentation's 3D page: «crie
uma aba de ArqSynth Presentation e use as 2 colunas para replicar a experiência que se tem no ArqSynth Presentation,
preparando o modelo 3D para exportação com todas as configurações do ArqSynth Presentation. Ao clicar na aba a tela
muda a interface para a interface do ArqSynth Presentation».

The last tab of the views (view_tabs.PRESENT): while it is in front the window's columns are the Presentation's —
- on the left (PagesPanel): DIVIDIDO / ABAS, the PÁGINAS that go in the package (the Modelo 3D page and a Planta page
  per sheet with views; Capa, Texto and Concept are made over there), the 3D page's scenes as the Presentation's cards
  (thumbnail, number, star of the first one, name, PERSPECTIVA / ORTOGONAL, and Atualizar · Cena inicial · Mostrar ·
  Duplicar · Renomear · Eliminar), «Exportar / atualizar», and CENAS with the TRANSIÇÃO of every scene;
- on the right (SidePanel): the Presentation's rail — Camadas (every element under its category, its eye; «Procurar
  peça…»), Cenas 3D, Ambiente, Etiquetas, Imagens, Efeitos, Passeio —, each for the scene chosen;
- over the 3D view (Overlay): «Criar cena», PERSP / ORTO, «Enquadrar modelo», «Enquadrar selecção», the lock, the FOV,
  the keys of the views (T, E, F, D, B, TRÁS and the 90° turns), «Renderizado · Auto» and the sun's reading.
The BIM's own columns come back as they were when another tab is chosen.

What is chosen here goes where the Presentation keeps it, through model/presentation.py (one undo step a change) and
model/presentation_export.py: a scene is a view of the project — «Criar cena» keeps the 3D view as a named 3D view
(«Cena 2»), «Atualizar» keeps the view again —, with its camera (projection, lens, locked), its visual mode, quality and
ambient occlusion, the layers it hides (the eyes, as the Presentation's: live until a scene is made or updated), its
arrival, effect, camera move, sun, exposure, sky, caption and time. The names, ranges and defaults are the
Presentation's own (its SlideSidebar, Model3DViewport, NaviCube, VisualModeMenu and LayersTab)."""

import math

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..model import camera_moves
from ..model import presentation as pm
from ..model import presentation_sun
from . import presentation_glyphs as glyphs
from . import theme

KEY = QtCore.Qt.ItemDataRole.UserRole
THUMB = QtCore.QSize(84, 47)            # a scene card's picture (16:9)
PAGE_THUMB = QtCore.QSize(150, 84)      # a page card's
MARGIN = 12                             # the commands over the 3D view: this far from its edges
MIME = "application/x-arqsynth-scene"   # a scene card dragged to another place
RAIL = (("layers", "layers"), None, ("scenes", "film"), ("environment", "sun"), ("labels", "tag"),
        ("images", "pano"), ("effects", "camera"), None, ("walk", "walk"))
FACES = {"top": (0.0, 0.0, 1.0), "left": (-1.0, 0.0, 0.0), "front": (0.0, -1.0, 0.0), "right": (1.0, 0.0, 0.0),
         "bottom": (0.0, 0.0, -1.0), "back": (0.0, 1.0, 0.0)}      # (the Presentation's −Z is north: the model's +Y)


def vertical_fov(pygfx_fov, aspect):
    """The Presentation's lens (three.js's vertical field of view) of pygfx's, which shares it between the width and
    the height of the view (presentation_export._view_camera's)."""
    if pygfx_fov <= 0:
        return 0.0
    return math.degrees(2.0 * math.atan(math.tan(math.radians(pygfx_fov) / 2.0) * 2.0 / (1.0 + aspect)))


def pygfx_fov(vertical, aspect):
    """pygfx's field of view for the Presentation's vertical one (MainWindow._presentation_fov's)."""
    return math.degrees(2.0 * math.atan(math.tan(math.radians(vertical) / 2.0) * (1.0 + aspect) / 2.0))


def _css():
    c = dict(theme.C)
    return ("""
QWidget#pm_root { background: %(panel)s; }
QScrollArea#pm_scroll, QScrollArea#pm_scroll > QWidget > QWidget { background: %(panel)s; border: none; }
QLabel#pm_head { color: %(muted)s; font-weight: 700; letter-spacing: 1px; }
QLabel#pm_note { color: %(note)s; }
QLabel#pm_name { color: %(text)s; font-weight: 700; }
QLabel#pm_sub { color: %(muted)s; font-size: 10px; letter-spacing: 1px; }
QLabel#pm_badge { background: %(accent)s; color: %(accent_text)s; border-radius: 4px; padding: 0 5px;
                  font-weight: 700; font-size: 10px; }
QLabel#pm_count { background: %(button)s; color: %(text)s; border: 1px solid %(line)s; border-radius: 8px;
                  padding: 0 6px; font-size: 10px; }
QFrame#pm_segbox { background: %(button)s; border: 1px solid %(line)s; border-radius: 8px; }
QToolButton#pm_seg { border: none; border-radius: 6px; padding: 5px 8px; color: %(muted)s; font-weight: 700; }
QToolButton#pm_seg:checked { background: %(chip_on)s; color: %(chip_on_text)s; }
QToolButton#pm_page { border: 1px solid %(line)s; border-radius: 6px; padding: 5px 6px; color: %(text)s;
                      font-weight: 600; background: %(button)s; }
QToolButton#pm_page:hover { background: %(button_hover)s; }
QToolButton#pm_page:disabled { color: %(hint)s; border-style: dashed; background: transparent; }
QFrame#pm_card { background: %(card)s; border: 1px solid %(line)s; border-radius: 8px; }
QFrame#pm_card[active="true"] { border: 2px solid %(accent)s; background: %(select_soft)s; }
QToolButton#pm_icon { border: none; border-radius: 4px; padding: 3px; background: transparent; }
QToolButton#pm_icon:hover { background: %(button_hover)s; }
QToolButton#pm_icon:disabled { background: transparent; }
QPushButton#pm_wide { border: 1px dashed %(line)s; border-radius: 6px; padding: 5px; color: %(text)s;
                      background: transparent; }
QPushButton#pm_wide:hover { background: %(button_hover)s; }
QPushButton#pm_link { border: none; color: %(link)s; background: transparent; text-align: left; padding: 2px; }
QFrame#pm_float { background: %(card)s; border: 1px solid %(line)s; border-radius: 8px; }
QFrame#pm_float QLabel { color: %(muted)s; font-weight: 700; background: transparent; }
QFrame#pm_float QToolButton { border: none; border-radius: 6px; padding: 4px 7px; color: %(text)s;
                              background: transparent; font-weight: 700; }
QFrame#pm_float QToolButton:hover { background: %(button_hover)s; }
QFrame#pm_float QToolButton:checked { background: %(accent)s; color: %(accent_text)s; }
QFrame#pm_float QToolButton:disabled { color: %(hint)s; }
QFrame#pm_float QToolButton#pm_key { border: 1px solid %(line)s; border-radius: 6px; background: %(button)s;
                                     color: %(text)s; font-weight: 700; min-width: 30px; min-height: 26px;
                                     padding: 0 4px; }
QFrame#pm_float QToolButton#pm_key:hover { background: %(button_hover)s; }
QFrame#pm_float QToolButton#pm_key:disabled { background: %(button)s; }
QFrame#pm_line { background: %(line)s; border: none; max-height: 1px; min-height: 1px; }
QFrame#pm_vline { background: %(line)s; border: none; max-width: 1px; min-width: 1px; }
""" % c)


def _icon(kind, key="muted", size=16, on=None):
    return glyphs.icon(kind, theme.colour(key), size, theme.colour(on) if on else None)


def _label(text, name):
    label = QtWidgets.QLabel(text)
    label.setObjectName(name)
    return label


def _repolish(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def _seconds(lo, hi, step):
    box = QtWidgets.QDoubleSpinBox()
    box.setRange(lo, hi)
    box.setDecimals(1)
    box.setSingleStep(step)
    box.setSuffix(" s")
    box.setKeyboardTracking(False)
    return box


def _pair(a, b):
    w = QtWidgets.QWidget()
    row = QtWidgets.QHBoxLayout(w)
    row.setContentsMargins(0, 0, 0, 0)
    row.addWidget(a, 1)
    row.addWidget(b)
    return w


def _narrow(box, chars=9):
    """A list box as narrow as the column (its long names in the open list only)."""
    box.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    box.setMinimumContentsLength(chars)
    return box


def _scroll(widget):
    """A column's content that scrolls up and down, never wider than the column (it would widen the column for good
    and narrow the 3D view: the 0.364 lesson)."""
    area = QtWidgets.QScrollArea()
    area.setObjectName("pm_scroll")
    area.setWidgetResizable(True)
    area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.setWidget(widget)
    area.setMinimumWidth(60)
    return area


class _Form(QtWidgets.QWidget):
    """A page of the right column for the scene chosen: its fields filled quietly (their signals are not the user's)."""

    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.showing = False
        column = QtWidgets.QVBoxLayout(self)               # (the form at the top; the room left below it, not spread
        column.setContentsMargins(10, 8, 10, 8)            #  between its rows)
        self.form = QtWidgets.QFormLayout()
        self.form.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)
        self.form.setVerticalSpacing(8)
        column.addLayout(self.form)
        column.addStretch(1)

    def change(self, **fields):
        if not self.showing:
            self.mode.change(**fields)

    def note(self, key):
        label = _label(t(key), "pm_note")
        label.setWordWrap(True)
        self.form.addRow(label)
        return label


# ------------------------------------------------------------------ the scene cards (left column)

class _SceneCard(QtWidgets.QFrame):
    """A scene as the Presentation's card: its picture (its number, the star of the first scene), its name, its camera
    («PERSPECTIVA», «ORTOGONAL», «FORA DA APRESENTAÇÃO»), its six buttons. Clicked: the scene chosen (its view shown);
    dragged: to another place in the order."""

    def __init__(self, panel, scene, number, initial, only_visible, thumb):
        super().__init__()
        self.panel, self.key = panel, scene.key
        self.setObjectName("pm_card")
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setAcceptDrops(True)
        self._press = None
        box = QtWidgets.QVBoxLayout(self)
        box.setContentsMargins(8, 8, 8, 6)
        box.setSpacing(4)
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(8)
        self.picture = QtWidgets.QLabel()
        self.picture.setFixedSize(THUMB)
        self.picture.setPixmap(thumb)
        badge = _label("{:02d}".format(number), "pm_badge")
        badge.setParent(self.picture)
        badge.move(3, 3)
        self.star = QtWidgets.QLabel(self.picture)
        self.star.setPixmap(glyphs.pixmap("star_on", theme.colour("attention"), 13))
        self.star.move(THUMB.width() - 17, 3)
        self.star.setVisible(scene.key == initial and not scene.hidden)
        self.star.setToolTip(t("pmode.initial_mark"))
        top.addWidget(self.picture)
        words = QtWidgets.QVBoxLayout()
        words.setSpacing(2)
        self.name = _label(scene.name, "pm_name")
        self.name.setWordWrap(True)
        self.name.setToolTip(scene.name)
        font = self.name.font()
        font.setStrikeOut(scene.hidden)
        self.name.setFont(font)
        self.sub = _label(subtitle(panel.mode, scene).upper(), "pm_sub")
        self.sub.setWordWrap(True)
        words.addWidget(self.name)
        words.addWidget(self.sub)
        words.addStretch(1)
        top.addLayout(words, 1)
        box.addLayout(top)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(0)
        mode = panel.mode
        self.buttons = {}
        hide_tip = "pmode.show_tip" if scene.hidden else ("pmode.only_visible" if only_visible else "pmode.hide_tip")
        for name, kind, tip, call in (
                ("update", "refresh", "pmode.update_tip", lambda: mode.update_scene(self.key)),
                ("initial", "star_on" if scene.key == initial else "star", "pmode.initial_tip",
                 lambda: mode.set_initial(self.key)),
                ("visible", "eye_off" if scene.hidden else "eye", hide_tip, lambda: mode.toggle_hidden(self.key)),
                ("duplicate", "copy", "pmode.duplicate_tip", lambda: mode.duplicate(self.key)),
                ("rename", "pencil", "pmode.rename_tip", lambda: mode.rename(self.key)),
                ("delete", "trash", "pmode.delete_tip", lambda: mode.delete(self.key))):
            button = QtWidgets.QToolButton()
            button.setObjectName("pm_icon")
            colour = "attention" if name == "initial" and scene.key == initial else "muted"
            button.setIcon(_icon(kind, colour, 16))
            button.setIconSize(QtCore.QSize(16, 16))
            button.setToolTip(t(tip))
            button.setAutoRaise(True)
            button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            button.clicked.connect(lambda _on=False, c=call: c())
            row.addWidget(button)
            row.addStretch(1)
            self.buttons[name] = button
        self.buttons["visible"].setEnabled(scene.hidden or not only_visible)
        if scene.kind != "view3d":
            self.buttons["delete"].setToolTip(t("pmode.delete_view_tip"))
        box.addLayout(row)
        if scene.hidden:                                    # (as the Presentation's: dimmed, its name struck through)
            fade = QtWidgets.QGraphicsOpacityEffect(self)
            fade.setOpacity(0.55)
            self.setGraphicsEffect(fade)
        self.set_active(False)

    def set_active(self, on):
        self.setProperty("active", "true" if on else "false")
        _repolish(self)

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._press = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # noqa: N802
        if self._press is not None and (event.position().toPoint() - self._press).manhattanLength() > 8:
            self._press = None
            drag = QtGui.QDrag(self)
            data = QtCore.QMimeData()
            data.setData(MIME, self.key.encode("utf-8"))
            drag.setMimeData(data)
            drag.setPixmap(self.grab().scaledToWidth(160, QtCore.Qt.TransformationMode.SmoothTransformation))
            drag.exec(QtCore.Qt.DropAction.MoveAction)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: N802
        if self._press is not None and event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._press = None
            self.panel.mode.activate(self.key)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):  # noqa: N802
        self.panel.mode.open_view_of(self.key)                # (its view in the BIM's own tab)

    def dragEnterEvent(self, event):  # noqa: N802
        if event.mimeData().hasFormat(MIME):
            event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802
        key = bytes(event.mimeData().data(MIME)).decode("utf-8")
        after = event.position().y() > self.height() / 2
        self.panel.mode.move_scene(key, self.key, after)
        event.acceptProposedAction()


def subtitle(mode, scene):
    """A card's second line: «Fora da apresentação», else its camera — «Perspectiva» / «Ortogonal» — (a plan's, a
    section's: and what it is)."""
    if scene.hidden:
        return t("pmode.sub_hidden")
    words = t("pmode.ortho" if mode.ortho_of(scene) else "pmode.persp")
    if scene.kind in ("plan", "section", "overview"):
        words += " · " + t("pmode.kind." + scene.kind)
    return words


class _PageCard(QtWidgets.QFrame):
    """A page of the package: the Modelo 3D page (its first scene's picture), a sheet's Planta page (its paper)."""

    def __init__(self, panel, page, number, title, kind, picture):
        super().__init__()
        self.panel, self.page = panel, page
        self.setObjectName("pm_card")
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        box = QtWidgets.QHBoxLayout(self)
        box.setContentsMargins(8, 8, 8, 8)
        box.setSpacing(8)
        self.picture = QtWidgets.QLabel()
        self.picture.setFixedSize(PAGE_THUMB.width() // 2 + 20, PAGE_THUMB.height() // 2 + 11)
        self.picture.setPixmap(picture.scaled(self.picture.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                              QtCore.Qt.TransformationMode.SmoothTransformation))
        box.addWidget(self.picture)
        words = QtWidgets.QVBoxLayout()
        words.setSpacing(2)
        head = QtWidgets.QHBoxLayout()
        head.addWidget(_label("{:02d}".format(number), "pm_badge"))
        head.addStretch(1)
        words.addLayout(head)
        name = _label(title, "pm_name")
        name.setWordWrap(True)
        words.addWidget(name)
        words.addWidget(_label(t("pmode.page_kind." + kind).upper(), "pm_sub"))
        words.addStretch(1)
        box.addLayout(words, 1)
        self.set_active(False)

    def set_active(self, on):
        self.setProperty("active", "true" if on else "false")
        _repolish(self)

    def mouseReleaseEvent(self, event):  # noqa: N802
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.panel.choose_page(self.page)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):  # noqa: N802
        if self.page != "model":
            self.panel.mode.open_sheet(self.page)


class PagesPanel(QtWidgets.QDockWidget):
    """The Presentation's left column."""

    def __init__(self, mode, parent):
        super().__init__(t("pmode.title"), parent)
        self.mode = mode
        self.setObjectName("presentation_pages")
        self.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.layout_kind = "split"                 # DIVIDIDO | ABAS (the Presentation keeps it only while it is open)
        self.tab = "pages"                         # in ABAS: «Páginas» | «Cenas»
        self.page = "model"                        # the page chosen: the 3D page, or a sheet's uid
        self.cards, self.page_cards = {}, {}
        root = QtWidgets.QWidget()
        root.setObjectName("pm_root")
        column = QtWidgets.QVBoxLayout(root)
        column.setContentsMargins(8, 8, 8, 8)
        column.setSpacing(8)
        self.layout_row = self._segments((("split", "split", "pmode.split", "pmode.split_tip"),
                                          ("tabs", "tabs", "pmode.tabs", "pmode.tabs_tip")), self.set_layout)
        column.addWidget(self.layout_row[0])
        self.tab_row = self._segments((("pages", "cover", "pmode.tab_pages", "pmode.tab_pages_tip"),
                                       ("scenes", "film", "pmode.tab_scenes", "pmode.tab_scenes_tip")), self.set_tab)
        column.addWidget(self.tab_row[0])
        self.pages_head = _label(t("pmode.pages").upper(), "pm_head")
        column.addWidget(self.pages_head)
        self.add_box = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(self.add_box)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(6)
        self.add_buttons = {}
        for k, (name, kind) in enumerate((("cover", "cover"), ("text", "text"), ("plan", "plan"),
                                          ("model", "cube"), ("concept", "concept"))):
            button = QtWidgets.QToolButton()
            button.setObjectName("pm_page")
            button.setText(t("pmode.add." + name))
            button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
            button.setToolTip(t("pmode.add_tip." + name))
            button.clicked.connect(lambda _on=False, n=name: self.mode.add_page(n))
            if name in ("cover", "text", "concept"):            # (made in the Presentation: the BIM sends the model
                button.setEnabled(False)                        #  and the plans)
            grid.addWidget(button, k // 3, (k % 3) * 2 if k < 3 else (k - 3) * 3, 1, 2 if k < 3 else 3)
            self.add_buttons[name] = button
        column.addWidget(self.add_box)
        line = QtWidgets.QFrame()
        line.setObjectName("pm_line")
        column.addWidget(line)
        self.list = QtWidgets.QWidget()
        self.list_box = QtWidgets.QVBoxLayout(self.list)
        self.list_box.setContentsMargins(0, 0, 4, 0)
        self.list_box.setSpacing(8)
        self.scroller = _scroll(self.list)
        column.addWidget(self.scroller, 1)
        line = QtWidgets.QFrame()
        line.setObjectName("pm_line")
        column.addWidget(line)
        foot = QtWidgets.QHBoxLayout()
        self.scenes_icon = QtWidgets.QLabel()
        foot.addWidget(self.scenes_icon)
        foot.addWidget(_label(t("pmode.scenes").upper(), "pm_head"))
        self.count = _label("0", "pm_count")
        foot.addWidget(self.count)
        foot.addStretch(1)
        column.addLayout(foot)
        slide = QtWidgets.QHBoxLayout()
        self.transition_label = _label(t("pmode.transition").upper(), "pm_sub")
        slide.addWidget(self.transition_label)
        self.transition = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.transition.setRange(int(pm.TRANSITION_MIN * 10), int(pm.TRANSITION_MAX * 10))  # (tenths: 300–5000 ms)
        self.transition.setSingleStep(1)
        self.transition.setPageStep(5)
        self.transition.setToolTip(t("pmode.transition_tip"))
        self.transition.valueChanged.connect(lambda v: self.transition_value.setText("{:.1f}s".format(v / 10.0)))
        self.transition.sliderReleased.connect(self._transition_done)
        self.transition.setTracking(True)
        self._transition_keyed = QtCore.QTimer(self)        # (moved by the keys: kept when they stop)
        self._transition_keyed.setSingleShot(True)
        self._transition_keyed.setInterval(400)
        self._transition_keyed.timeout.connect(self._transition_done)
        self.transition.actionTriggered.connect(lambda _a: None if self.transition.isSliderDown()
                                                else self._transition_keyed.start())
        slide.addWidget(self.transition, 1)
        self.transition_value = _label("1.2s", "pm_sub")
        slide.addWidget(self.transition_value)
        column.addLayout(slide)
        self.setWidget(root)
        self.root = root
        self.restyle()

    def _segments(self, items, call):
        box = QtWidgets.QFrame()
        box.setObjectName("pm_segbox")
        row = QtWidgets.QHBoxLayout(box)
        row.setContentsMargins(3, 3, 3, 3)
        row.setSpacing(2)
        group = QtWidgets.QButtonGroup(box)
        buttons = {}
        for value, kind, text, tip in items:
            button = QtWidgets.QToolButton()
            button.setObjectName("pm_seg")
            button.setText(t(text).upper())
            button.setToolTip(t(tip))
            button.setCheckable(True)
            button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
            button.setProperty("glyph", kind)
            group.addButton(button)
            button.clicked.connect(lambda _on=False, v=value: call(v))
            row.addWidget(button, 1)
            buttons[value] = button
        return box, buttons

    def restyle(self):
        self.root.setStyleSheet(_css())
        for row in (self.layout_row, self.tab_row):
            for button in row[1].values():
                button.setIcon(_icon(button.property("glyph"), "muted", 14, on="chip_on_text"))
        for name, button in self.add_buttons.items():
            button.setIcon(_icon({"cover": "cover", "text": "text", "plan": "plan", "model": "cube",
                                  "concept": "concept"}[name], "text" if button.isEnabled() else "hint", 15))
        self.scenes_icon.setPixmap(glyphs.pixmap("film", theme.colour("accent"), 14))

    # ------------------------------------------------------------ shown

    def set_layout(self, kind):
        """DIVIDIDO (the pages, the 3D page's scenes under it) or ABAS (one of them at a time)."""
        self.layout_kind = kind
        self.show_all()

    def set_tab(self, tab):
        self.tab = tab
        self.show_all()

    def choose_page(self, page):
        self.page = page
        self.show_all()

    def show_all(self):
        """The column again, as the project and the scene chosen are now."""
        mode = self.mode
        self.layout_row[1][self.layout_kind].setChecked(True)
        tabs = self.layout_kind == "tabs"
        self.tab_row[0].setVisible(tabs)
        self.tab_row[1][self.tab].setChecked(True)
        pages = not tabs or self.tab == "pages"
        scenes_shown = (not tabs and self.page == "model") or (tabs and self.tab == "scenes")
        self.pages_head.setVisible(pages)
        self.add_box.setVisible(pages)
        while self.list_box.count():
            item = self.list_box.takeAt(0)
            if item.widget() is not None:
                item.widget().hide()                       # (not seen under the new ones until it is deleted)
                item.widget().deleteLater()
        self.cards, self.page_cards = {}, {}
        found = mode.scenes()
        initial = pm.initial(mode.doc, found)
        visible = [s for s in found if not s.hidden]
        sheets = mode.sheets()
        if self.page != "model" and self.page not in {s.uid for s in sheets}:
            self.page = "model"
        if pages:
            card = _PageCard(self, "model", 1, t("pmode.page_model"), "model", mode.page_picture(found, initial))
            self.list_box.addWidget(card)
            self.page_cards["model"] = card
        if scenes_shown:
            self.list_box.addWidget(self._scenes_block(found, initial, visible))
        if pages:
            for k, sheet in enumerate(sheets):
                card = _PageCard(self, sheet.uid, k + 2, sheet.name, "plan", mode.sheet_picture(sheet))
                self.list_box.addWidget(card)
                self.page_cards[sheet.uid] = card
            if not sheets:
                note = _label(t("pmode.no_sheets"), "pm_note")
                note.setWordWrap(True)
                self.list_box.addWidget(note)
        self.list_box.addStretch(1)
        for page, card in self.page_cards.items():
            card.set_active(page == self.page)
        self.mark(mode.scene_key)
        self.count.setText(str(len(found)))
        value = pm.transition_of(found)
        if not self.transition.isSliderDown():
            self.transition.blockSignals(True)
            self.transition.setValue(int(round(min(max(value, pm.TRANSITION_MIN), pm.TRANSITION_MAX) * 10)))
            self.transition.blockSignals(False)
            self.transition_value.setText("{:.1f}s".format(self.transition.value() / 10.0))
        self.transition.setEnabled(bool(found))

    def _scenes_block(self, found, initial, visible):
        block = QtWidgets.QWidget()
        box = QtWidgets.QVBoxLayout(block)
        box.setContentsMargins(12 if self.layout_kind == "split" else 0, 0, 0, 0)
        box.setSpacing(8)
        self.export_button = QtWidgets.QPushButton(t("pmode.export"))
        self.export_button.setObjectName("pm_wide")
        self.export_button.setIcon(_icon("upload", "text", 15))
        self.export_button.setToolTip(t("pmode.export_tip"))
        self.export_button.clicked.connect(lambda: self.mode.export())
        box.addWidget(self.export_button)
        for k, scene in enumerate(found):
            card = _SceneCard(self, scene, k + 1, initial, len(visible) == 1 and not scene.hidden,
                              self.mode.thumb(scene.key))
            box.addWidget(card)
            self.cards[scene.key] = card
        omitted = self.mode.omitted()
        if omitted:
            back = QtWidgets.QPushButton(t("pmode.omitted", n=len(omitted)))
            back.setObjectName("pm_link")
            back.setToolTip(t("pmode.omitted_tip"))
            back.clicked.connect(lambda: self.mode.restore_omitted())
            box.addWidget(back)
        if not found:
            box.addWidget(_label(t("pmode.no_scenes"), "pm_note"))
        return block

    def mark(self, key):
        for k, card in self.cards.items():
            card.set_active(k == key)

    def _transition_done(self):
        self.mode.set_transition(self.transition.value() / 10.0)


# ------------------------------------------------------------------ the right column

class _RailButton(QtWidgets.QAbstractButton):
    """A tab of the Presentation's rail: its icon; the one chosen lit, its name written down under it."""

    def __init__(self, name, kind):
        super().__init__()
        self.name, self.kind = name, kind
        self.label = t("pmode.rail." + name)
        self.setCheckable(True)
        self.setToolTip(self.label)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.toggled.connect(lambda _on: self.updateGeometry())

    def sizeHint(self):  # noqa: N802
        if self.isChecked():
            font = QtGui.QFont(self.font())
            font.setBold(True)
            font.setPixelSize(10)
            return QtCore.QSize(34, 38 + QtGui.QFontMetrics(font).horizontalAdvance(self.label.upper()) + 8)
        return QtCore.QSize(34, 34)

    def minimumSizeHint(self):  # noqa: N802
        return self.sizeHint()

    def enterEvent(self, event):  # noqa: N802
        self.update()

    def leaveEvent(self, event):  # noqa: N802
        self.update()

    def paintEvent(self, event):  # noqa: N802
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        on = self.isChecked()
        if self.underMouse() and not on:
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.setBrush(theme.colour("button_hover"))
            p.drawRoundedRect(QtCore.QRectF(2, 2, 30, 30), 6, 6)
        colour = theme.colour("accent" if on else "muted")
        p.drawPixmap(8, 8, glyphs.pixmap(self.kind, colour, 18))
        if on:
            font = QtGui.QFont(self.font())
            font.setBold(True)
            font.setPixelSize(10)
            p.setFont(font)
            p.setPen(colour)
            fm = QtGui.QFontMetrics(font)
            p.translate(17 - (fm.ascent() - fm.descent()) / 2.0, 38)
            p.rotate(90)
            p.drawText(0, 0, self.label.upper())
        p.end()


class LayersPage(QtWidgets.QWidget):
    """CAMADAS: every element that goes (an element a layer, as the Presentation makes its own), under its category;
    its eye; «Procurar peça…»; clicked: selected in the 3D view (Shift: a series, Ctrl: one more), double-clicked: in
    view."""

    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self._quiet = False
        box = QtWidgets.QVBoxLayout(self)
        box.setContentsMargins(8, 8, 8, 6)
        box.setSpacing(6)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText(t("pmode.search"))
        self.search.setClearButtonEnabled(True)
        self.search_icon = self.search.addAction(QtGui.QIcon(), QtWidgets.QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(self._filter)
        box.addWidget(self.search)
        self.pick_all = QtWidgets.QPushButton(t("pmode.select_matches"))
        self.pick_all.setObjectName("pm_link")
        self.pick_all.clicked.connect(self._select_matches)
        self.pick_all.hide()
        box.addWidget(self.pick_all)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(14)
        self.tree.setUniformRowHeights(True)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.tree.header().resizeSection(1, 28)
        self.tree.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree.itemClicked.connect(self._clicked)
        self.tree.itemDoubleClicked.connect(self._double)
        self.tree.itemSelectionChanged.connect(self._selected)
        box.addWidget(self.tree, 1)
        self.hint = _label(t("pmode.layers_hint"), "pm_note")
        self.hint.setWordWrap(True)
        box.addWidget(self.hint)
        self.groups = {}                       # category -> its item
        self.items = {}                        # GlobalId -> its item

    def restyle(self):
        self.search_icon.setIcon(_icon("search", "muted", 15))
        self._eyes()

    def show_layers(self, rows, hidden):
        """rows: [(GlobalId, name, category, storey, IFC class)]; hidden: the GlobalIds turned off."""
        self._quiet = True
        try:
            opened = {c for c, item in self.groups.items() if item.isExpanded()} if self.groups else None
            self.tree.clear()
            self.groups, self.items = {}, {}
            bold = QtGui.QFont(self.tree.font())
            bold.setBold(True)
            for guid, name, category, storey, cls in rows:
                group = self.groups.get(category)
                if group is None:
                    group = QtWidgets.QTreeWidgetItem([category.upper(), ""])
                    group.setFont(0, bold)
                    group.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
                    group.setData(0, KEY, None)
                    self.tree.addTopLevelItem(group)
                    self.groups[category] = group
                item = QtWidgets.QTreeWidgetItem(group, [name, ""])
                item.setData(0, KEY, guid)
                item.setToolTip(0, "{} · {} · {}".format(name, storey, cls))
                self.items[guid] = item
            for category, group in self.groups.items():
                group.setExpanded(opened is None or category in opened)
                group.setText(0, "{}  ({})".format(category.upper(), group.childCount()))
            self.hidden = set(hidden)
            self._eyes()
            self._filter(self.search.text())
        finally:
            self._quiet = False

    def set_hidden(self, hidden):
        self.hidden = set(hidden)
        self._eyes()

    def _eyes(self):
        if not hasattr(self, "hidden"):
            return
        on, off = _icon("eye", "muted", 15), _icon("eye_off", "hint", 15)
        dim, ink = theme.colour("hint"), theme.colour("text")
        for guid, item in self.items.items():
            gone = guid in self.hidden
            item.setIcon(1, off if gone else on)
            item.setToolTip(1, t("pmode.layer_show" if gone else "pmode.layer_hide"))
            item.setForeground(0, QtGui.QBrush(dim if gone else ink))
        for group in self.groups.values():
            ids = [group.child(k).data(0, KEY) for k in range(group.childCount())]
            gone = bool(ids) and all(i in self.hidden for i in ids)
            group.setIcon(1, off if gone else on)
            group.setToolTip(1, t("pmode.folder_show" if gone else "pmode.folder_hide"))

    def _clicked(self, item, column):
        if column != 1:
            return
        guid = item.data(0, KEY)
        if guid is None:                                   # a category: all of it
            ids = [item.child(k).data(0, KEY) for k in range(item.childCount())]
            hide = not all(i in self.hidden for i in ids)
        else:
            chosen = [i.data(0, KEY) for i in self.tree.selectedItems() if i.data(0, KEY)]
            ids = chosen if item.isSelected() and len(chosen) > 1 else [guid]   # (the eye of a row selected: all)
            hide = guid not in self.hidden
        self.mode.set_layers_hidden(ids, hide)

    def _double(self, item, column):
        guid = item.data(0, KEY)
        if guid and column == 0:
            self.mode.frame([guid])

    def _selected(self):
        if not self._quiet:
            self.mode.select([i.data(0, KEY) for i in self.tree.selectedItems() if i.data(0, KEY)])

    def show_selection(self, ids):
        """The 3D view's selection marked in the list (quietly)."""
        self._quiet = True
        try:
            self.tree.clearSelection()
            first = None
            for guid in ids:
                item = self.items.get(guid)
                if item is not None:
                    item.setSelected(True)
                    first = first or item
            if first is not None:
                self.tree.scrollToItem(first)
        finally:
            self._quiet = False

    def _filter(self, text):
        words = text.strip().lower()
        for group in self.groups.values():
            shown = 0
            for k in range(group.childCount()):
                child = group.child(k)
                hit = not words or words in child.text(0).lower()
                child.setHidden(not hit)
                shown += hit
            group.setHidden(shown == 0)
            if words and shown:
                group.setExpanded(True)
        self.pick_all.setVisible(bool(words))

    def _select_matches(self):
        self.tree.clearSelection()
        for item in self.items.values():
            if not item.isHidden() and not item.parent().isHidden():
                item.setSelected(True)


class ScenesPage(_Form):
    """CENAS 3D: the scene chosen — its name, the first one, shown or left out, how it is reached (Suave / Corte, in
    how long), its effect, its time and its caption."""

    def __init__(self, mode):
        super().__init__(mode)
        self.title = _label("", "pm_name")
        self.title.setWordWrap(True)
        self.form.addRow(self.title)
        self.initial = QtWidgets.QCheckBox(t("pmode.initial"))
        self.initial.setToolTip(t("pmode.initial_tip"))
        self.initial.toggled.connect(lambda on: self.mode.set_initial(self.mode.scene_key) if on and not self.showing
                                     else self._again())
        self.form.addRow(self.initial)
        self.shown = QtWidgets.QCheckBox(t("pmode.shown"))
        self.shown.setToolTip(t("present.hidden_tip"))
        self.shown.toggled.connect(lambda on: self.change(hidden=not on))
        self.form.addRow(self.shown)
        self.transition = _narrow(QtWidgets.QComboBox())
        for name in pm.TRANSITIONS:
            self.transition.addItem(t("pmode.move." + name), name)
        self.transition.currentIndexChanged.connect(lambda _i: self.change(transition=self.transition.currentData()))
        self.transition_s = _seconds(0.0, 10.0, 0.1)
        self.transition_s.valueChanged.connect(lambda v: self.change(transition_s=v))
        self.form.addRow(t("pmode.arrival"), _pair(self.transition, self.transition_s))
        self.effect = _narrow(QtWidgets.QComboBox())
        for name in pm.EFFECTS:
            self.effect.addItem(t("present.effect." + name), name)
        self.effect.currentIndexChanged.connect(lambda _i: self.change(effect=self.effect.currentData()))
        self.effect_s = _seconds(1.0, 60.0, 0.5)
        self.effect_s.valueChanged.connect(lambda v: self.change(effect_s=v))
        self.form.addRow(t("present.effect"), _pair(self.effect, self.effect_s))
        self.seconds = _seconds(0.0, 600.0, 1.0)
        self.seconds.setSpecialValueText(t("present.seconds_auto"))
        self.seconds.setToolTip(t("present.seconds_tip"))
        self.seconds.valueChanged.connect(lambda v: self.change(seconds=v))
        self.form.addRow(t("present.seconds"), self.seconds)
        self.caption = _Caption(self)
        self.caption.setToolTip(t("present.caption_tip"))
        self.caption.setFixedHeight(64)
        self.form.addRow(t("present.caption"), self.caption)
        self.fields = (self.initial, self.shown, self.transition, self.transition_s, self.effect, self.effect_s,
                       self.seconds, self.caption)

    def _again(self):
        if not self.showing:                    # (the first scene is not turned off: another one is chosen instead)
            self.show_scene(self.mode.scene())

    def show_scene(self, scene):
        self.showing = True
        try:
            for w in self.fields:
                w.setEnabled(scene is not None)
            self.title.setText(scene.name if scene is not None else t("present.none"))
            if scene is None:
                return
            found = self.mode.scenes()
            self.initial.setChecked(scene.key == pm.initial(self.mode.doc, found))
            self.shown.setChecked(not scene.hidden)
            self.shown.setEnabled(scene.hidden or sum(1 for s in found if not s.hidden) > 1)
            self.transition.setCurrentIndex(max(self.transition.findData(scene.transition), 0))
            self.transition_s.setValue(scene.transition_s)
            self.transition_s.setEnabled(scene.transition != "cut")
            self.effect.setCurrentIndex(max(self.effect.findData(scene.effect), 0))
            self.effect_s.setValue(scene.effect_s)
            self.effect_s.setEnabled(scene.effect != "none")
            self.seconds.setValue(scene.seconds)
            if self.caption.toPlainText() != scene.caption:
                self.caption.setPlainText(scene.caption)
        finally:
            self.showing = False


class _Caption(QtWidgets.QPlainTextEdit):
    """The caption, kept when it is left (one undo step for the text)."""

    def __init__(self, page):
        super().__init__()
        self.page = page
        self.setTabChangesFocus(True)

    def focusOutEvent(self, event):  # noqa: N802
        super().focusOutEvent(event)
        scene = self.page.mode.scene()
        text = self.toPlainText().strip()
        if not self.page.showing and scene is not None and text != scene.caption:
            self.page.mode.change(caption=text)


class EnvironmentPage(_Form):
    """AMBIENTE: the scene's sun (the site's, on a day at an hour; still, through the day or the year), the exposure,
    the sky — «Ver sol» shows it in the 3D view with its shadows."""

    def __init__(self, mode):
        super().__init__(mode)
        self.date = QtWidgets.QDateEdit()
        self.date.setDisplayFormat("dd/MM")
        self.date.setDateRange(QtCore.QDate(2025, 1, 1), QtCore.QDate(2025, 12, 31))
        self.date.setKeyboardTracking(False)
        self.date.dateChanged.connect(lambda d: self.change(sun_day=presentation_sun.day_of(d.month(), d.day())))
        self.time = QtWidgets.QTimeEdit()
        self.time.setDisplayFormat("HH:mm")
        self.time.setKeyboardTracking(False)
        self.time.timeChanged.connect(lambda tm: self.change(sun_minutes=tm.hour() * 60 + tm.minute()))
        self.form.addRow(t("present.sun"), _pair(self.date, self.time))
        self.animate = _narrow(QtWidgets.QComboBox())
        for name in pm.SUN_ANIMATIONS:
            self.animate.addItem(t("present.sun_animate." + name), name)
        self.animate.setToolTip(t("present.sun_animate_tip"))
        self.animate.currentIndexChanged.connect(lambda _i: self.change(sun_animate=self.animate.currentData()))
        self.form.addRow(t("present.sun_animate"), self.animate)
        self.exposure = QtWidgets.QDoubleSpinBox()
        self.exposure.setRange(0.3, 1.6)
        self.exposure.setDecimals(2)
        self.exposure.setSingleStep(0.05)
        self.exposure.setKeyboardTracking(False)
        self.exposure.setToolTip(t("present.exposure_tip"))
        self.exposure.valueChanged.connect(lambda v: self.change(exposure=v))
        self.form.addRow(t("present.exposure"), self.exposure)
        self.sky = QtWidgets.QCheckBox(t("present.sky"))
        self.sky.setToolTip(t("present.sky_tip"))
        self.sky.toggled.connect(lambda on: self.change(sky=on))
        self.form.addRow(self.sky)
        self.play = QtWidgets.QPushButton(t("present.sun_play"))
        self.play.setToolTip(t("present.sun_play_tip"))
        self.play.clicked.connect(lambda: self.mode.play_sun())
        self.form.addRow(self.play)
        self.site_note = self.note("present.no_site")
        self.fields = (self.date, self.time, self.animate, self.exposure, self.sky, self.play)

    def show_scene(self, scene):
        self.showing = True
        try:
            for w in self.fields:
                w.setEnabled(scene is not None)
            if scene is None:
                return
            month, day = presentation_sun.month_day(scene.sun_day)
            self.date.setDate(QtCore.QDate(2025, month, day))
            self.time.setTime(QtCore.QTime(scene.sun_minutes // 60, scene.sun_minutes % 60))
            self.animate.setCurrentIndex(max(self.animate.findData(scene.sun_animate), 0))
            self.exposure.setValue(scene.exposure)
            self.sky.setChecked(scene.sky)
            placed = self.mode.site() is not None
            for w in (self.date, self.time, self.animate):
                w.setEnabled(placed)
            playing = self.mode.playing == "sun"
            self.play.setEnabled(placed or playing)
            self.play.setText(t("present.stop" if playing else "present.sun_play"))
            self.site_note.setVisible(not placed)
        finally:
            self.showing = False


class EffectsPage(_Form):
    """EFEITOS: the scene's camera move (the Presentation's library, by its groups), how long, the room of an interior
    one — «Ver movimento» plays it in the 3D view."""

    def __init__(self, mode):
        super().__init__(mode)
        self.move_box = _narrow(QtWidgets.QComboBox())       # (not `move`: QWidget's own)
        box = self.move_box
        box.setToolTip(t("present.move_tip"))
        box.addItem(t("present.move.none"), "")
        items = box.model()
        for category in camera_moves.CATEGORIES:
            box.addItem(t("move.cat." + category), None)
            head = items.item(box.count() - 1)
            head.setEnabled(False)
            font = head.font()
            font.setBold(True)
            head.setFont(font)
            for move, (cat, *_rest) in camera_moves.MOVES.items():
                if cat == category:
                    box.addItem("   " + t("move." + move), move)
        box.view().setMinimumWidth(box.view().sizeHintForColumn(0) + 24)
        box.currentIndexChanged.connect(lambda _i: self.change(move=self.move_box.currentData() or ""))
        self.form.addRow(t("present.move"), box)
        self.move_s = _seconds(0.0, 120.0, 1.0)
        self.move_s.valueChanged.connect(lambda v: self.change(move_s=v))
        self.form.addRow(t("pmode.move_time"), self.move_s)
        self.room = _narrow(QtWidgets.QComboBox())
        self.room.setToolTip(t("present.room_tip"))
        self.room.currentIndexChanged.connect(lambda _i: self.change(room=self.room.currentData() or ""))
        self.form.addRow(t("present.room"), self.room)
        self.play = QtWidgets.QPushButton(t("present.play"))
        self.play.setToolTip(t("present.play_tip"))
        self.play.clicked.connect(lambda: self.mode.play_move())
        self.form.addRow(self.play)
        self.note("pmode.effects_note")
        self.fields = (self.move_box, self.move_s, self.room, self.play)

    def show_scene(self, scene):
        self.showing = True
        try:
            for w in self.fields:
                w.setEnabled(scene is not None)
            if scene is None:
                return
            self.move_box.setCurrentIndex(max(self.move_box.findData(scene.move), 0))
            own = camera_moves.MOVES[scene.move][2] if scene.move else 0.0
            self.move_s.setSpecialValueText(t("present.move_own", s="{:.0f}".format(own)) if scene.move else "—")
            self.move_s.setValue(scene.move_s)
            self.move_s.setEnabled(bool(scene.move))
            inside = camera_moves.interior(scene.move)
            self.form.setRowVisible(self.room, inside)
            if inside:
                self.room.clear()
                self.room.addItem(t("present.room_auto"), "")
                for guid, name in self.mode.rooms():
                    self.room.addItem(name, guid)
                self.room.setCurrentIndex(max(self.room.findData(scene.room), 0))
            playing = self.mode.playing == "move"
            self.play.setEnabled(bool(scene.move) or playing)
            self.play.setText(t("present.stop" if playing else "present.play"))
        finally:
            self.showing = False


class _OptionPage(_Form):
    """ETIQUETAS / PASSEIO: the rooms as labels on their floors, as the Virtual Walk (its zones linked by the doors)."""

    def __init__(self, mode, option, text, note):
        super().__init__(mode)
        self.option, self.text = option, text
        self.box = QtWidgets.QCheckBox(t(text))
        self.box.toggled.connect(lambda on: None if self.showing else self.mode.set_option(**{self.option: on}))
        self.form.addRow(self.box)
        self.note(note)

    def show_scene(self, _scene):
        self.showing = True
        try:
            options, rooms = self.mode.options(), self.mode.room_count()
            self.box.setChecked(bool(options.get(self.option, True)))
            self.box.setText(t(self.text) + (" ({})".format(rooms) if rooms else ""))
            self.box.setEnabled(bool(rooms))
        finally:
            self.showing = False


class ImagesPage(_Form):
    """IMAGENS: the 360° panoramas rendered here — each one a 360° point on its storey's plans in the Presentation."""

    def __init__(self, mode):
        super().__init__(mode)
        self.list = QtWidgets.QListWidget()
        self.list.setMinimumHeight(90)
        self.form.addRow(self.list)
        row = QtWidgets.QHBoxLayout()
        self.new = QtWidgets.QPushButton(t("present.panorama_new"))
        self.new.setToolTip(t("tip.panorama"))
        self.new.clicked.connect(lambda: self.mode.win.render_panorama())
        self.remove = QtWidgets.QPushButton(t("present.panorama_remove"))
        self.remove.clicked.connect(self._remove)
        row.addWidget(self.new)
        row.addWidget(self.remove)
        self.form.addRow(row)
        self.list.currentItemChanged.connect(lambda *_: self.remove.setEnabled(
            self.list.currentItem() is not None and self.list.currentItem().data(KEY) is not None))
        self.note("pmode.images_note")

    def _remove(self):
        item = self.list.currentItem()
        if item is not None and item.data(KEY):
            self.mode.win.remove_panorama(item.data(KEY))

    def show_scene(self, _scene):
        self.list.clear()
        for p in getattr(self.mode.doc, "panoramas", ()):
            item = QtWidgets.QListWidgetItem(p["name"])
            item.setData(KEY, p["uid"])
            self.list.addItem(item)
        if not self.list.count():
            empty = QtWidgets.QListWidgetItem(t("present.panoramas_none"))
            empty.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
            self.list.addItem(empty)
        self.remove.setEnabled(False)


class SidePanel(QtWidgets.QDockWidget):
    """The Presentation's right column: its rail and the page of the tab chosen."""

    def __init__(self, mode, parent):
        super().__init__(t("pmode.rail.layers").upper(), parent)
        self.mode = mode
        self.setObjectName("presentation_side")
        self.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        root = QtWidgets.QWidget()
        root.setObjectName("pm_root")
        row = QtWidgets.QHBoxLayout(root)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        rail = QtWidgets.QWidget()
        rail.setObjectName("pm_rail")
        self.rail_box = QtWidgets.QVBoxLayout(rail)
        self.rail_box.setContentsMargins(3, 6, 3, 6)
        self.rail_box.setSpacing(4)
        self.stack = QtWidgets.QStackedWidget()
        self.pages = {"layers": LayersPage(mode), "scenes": ScenesPage(mode), "environment": EnvironmentPage(mode),
                      "labels": _OptionPage(mode, "labels", "present.labels", "pmode.labels_note"),
                      "images": ImagesPage(mode), "effects": EffectsPage(mode),
                      "walk": _OptionPage(mode, "walk", "present.walk", "pmode.walk_note")}
        self.buttons = {}
        group = QtWidgets.QButtonGroup(rail)
        for entry in RAIL:
            if entry is None:
                line = QtWidgets.QFrame()
                line.setObjectName("pm_line")
                self.rail_box.addWidget(line)
                continue
            name, kind = entry
            button = _RailButton(name, kind)
            group.addButton(button)
            button.clicked.connect(lambda _on=False, n=name: self.show_tab(n))
            self.rail_box.addWidget(button, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
            self.buttons[name] = button
            page = self.pages[name]
            self.stack.addWidget(page if name == "layers" else _scroll(page))
        self.rail_box.addStretch(1)
        row.addWidget(rail)
        line = QtWidgets.QFrame()
        line.setObjectName("pm_vline")
        row.addWidget(line)
        row.addWidget(self.stack, 1)
        self.setWidget(root)
        self.root = root
        self.tab = "layers"
        self.buttons["layers"].setChecked(True)
        self.restyle()

    def restyle(self):
        self.root.setStyleSheet(_css())
        self.pages["layers"].restyle()
        for button in self.buttons.values():
            button.update()

    def show_tab(self, name):
        """A tab of the rail: its page, its name on the column's title (as the Presentation's header)."""
        self.tab = name
        self.buttons[name].setChecked(True)
        page = self.pages[name]
        self.stack.setCurrentIndex(list(self.pages).index(name))
        self.setWindowTitle(t("pmode.rail." + name).upper())
        if name != "layers":
            page.show_scene(self.mode.scene())

    def show_scene(self, scene):
        """The pages of the scene chosen (the one in view: the others when they are chosen)."""
        if self.tab != "layers":
            self.pages[self.tab].show_scene(scene)


# ------------------------------------------------------------------ over the 3D view

class Overlay(QtCore.QObject):
    """The Presentation's commands over the 3D view: «Criar cena» (top left); PERSP / ORTO, «Enquadrar modelo»,
    «Enquadrar selecção», the lock and the FOV (top right); the keys of the views (bottom right, over the sun's
    reading); «Renderizado · Auto» (bottom left)."""

    def __init__(self, mode, parent, canvas):
        super().__init__(parent)
        self.mode, self.host, self.canvas = mode, parent, canvas      # (host: not `parent`, QObject's own)
        self.widgets = []
        self.create = self._float()
        row = QtWidgets.QHBoxLayout(self.create)
        row.setContentsMargins(2, 2, 2, 2)
        self.create_button = self._button(t("pmode.create"), "pmode.create_tip", mode.create_scene)
        self.create_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        row.addWidget(self.create_button)
        self.camera = self._float()
        row = QtWidgets.QHBoxLayout(self.camera)
        row.setContentsMargins(3, 3, 3, 3)
        row.setSpacing(2)
        self.persp = self._button(t("pmode.persp_short").upper(), "pmode.persp_tip", lambda: mode.set_ortho(False))
        self.ortho = self._button(t("pmode.ortho_short").upper(), "pmode.ortho_tip", lambda: mode.set_ortho(True))
        for b in (self.persp, self.ortho):
            b.setCheckable(True)
            row.addWidget(b)
        row.addSpacing(6)
        self.frame_model = self._button("", "pmode.frame_model", mode.frame_model)
        self.frame_selection = self._button("", "pmode.frame_selection", mode.frame_selection)
        self.lock = self._button("", "pmode.lock_tip", mode.toggle_lock)
        self.lock.setCheckable(True)
        for b in (self.frame_model, self.frame_selection, self.lock):
            row.addWidget(b)
        self.fov = self._float()
        row = QtWidgets.QHBoxLayout(self.fov)
        row.setContentsMargins(10, 3, 10, 3)
        row.addWidget(QtWidgets.QLabel(t("pmode.fov")))
        self.fov_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.fov_slider.setRange(int(pm.FOV_MIN), int(pm.FOV_MAX))
        self.fov_slider.setFixedWidth(120)
        self.fov_slider.setToolTip(t("pmode.fov_tip"))
        self.fov_slider.valueChanged.connect(self._fov)
        row.addWidget(self.fov_slider)
        self.fov_value = QtWidgets.QLabel("35")
        self.fov_value.setMinimumWidth(22)
        row.addWidget(self.fov_value)
        self.keys = self._float()
        grid = QtWidgets.QGridLayout(self.keys)
        grid.setContentsMargins(6, 6, 6, 6)
        grid.setSpacing(4)
        for face, r, c in (("top", 0, 1), ("left", 1, 0), ("front", 1, 1), ("right", 1, 2), ("bottom", 2, 1)):
            key = self._key(t("pmode.face_short." + face), t("pmode.face." + face), lambda f=face: mode.look(f))
            grid.addWidget(key, r, c)
        for r, c in ((0, 0), (0, 2), (2, 0), (2, 2)):          # (the keypad's empty corners, as the Presentation's)
            blank = self._key("", "", lambda: None)
            blank.setEnabled(False)
            grid.addWidget(blank, r, c)
        self.turn_left = self._key("", t("pmode.turn_left"), lambda: mode.turn(1))
        self.back = self._key(t("pmode.face_short.back"), t("pmode.face.back"), lambda: mode.look("back"))
        self.turn_right = self._key("", t("pmode.turn_right"), lambda: mode.turn(-1))
        grid.addWidget(self.turn_left, 3, 0)
        grid.addWidget(self.back, 3, 1)
        grid.addWidget(self.turn_right, 3, 2)
        self.look = self._float()
        row = QtWidgets.QHBoxLayout(self.look)
        row.setContentsMargins(2, 2, 2, 2)
        self.look_button = self._button("", "pmode.look_tip", None)
        self.look_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.look_button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.look_menu = QtWidgets.QMenu(self.look_button)
        self.look_menu.aboutToShow.connect(self._fill_look_menu)
        self.look_button.setMenu(self.look_menu)
        row.addWidget(self.look_button)
        self.sun = self._float()
        row = QtWidgets.QHBoxLayout(self.sun)
        row.setContentsMargins(2, 2, 2, 2)
        self.sun_button = self._button("", "pmode.sun_tip", lambda: mode.side.show_tab("environment"))
        self.sun_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        row.addWidget(self.sun_button)
        parent.installEventFilter(self)
        canvas.installEventFilter(self)
        self.hide()

    def _float(self):
        frame = QtWidgets.QFrame(self.host)
        frame.setObjectName("pm_float")
        frame.hide()
        self.widgets.append(frame)
        return frame

    def _button(self, text, tip, call):
        button = QtWidgets.QToolButton()
        button.setText(text)
        button.setToolTip(t(tip))
        button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        if call is not None:
            button.clicked.connect(lambda _on=False: call())
        return button

    def _key(self, text, tip, call):
        button = QtWidgets.QToolButton()
        button.setObjectName("pm_key")
        button.setText(text)
        button.setToolTip(tip)
        button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda _on=False: call())
        return button

    def restyle(self):
        css = _css()
        for w in self.widgets:
            w.setStyleSheet(css)
        self.create_button.setIcon(_icon("plus", "text", 15))
        self.frame_model.setIcon(_icon("expand", "text", 15))
        self.frame_selection.setIcon(_icon("focus", "text", 15))
        self.turn_left.setIcon(_icon("rotate_l", "text", 14))
        self.turn_right.setIcon(_icon("rotate_r", "text", 14))
        self.look_button.setIcon(_icon("palette", "accent", 15))
        self.sun_button.setIcon(_icon("sun", "attention", 15))
        self.show_state()

    def show_state(self):
        """The buttons as the camera is now (its projection, lens, lock) and the look and the sun as chosen."""
        mode = self.mode
        ortho = mode.vp.is_ortho()
        self.persp.setChecked(not ortho)
        self.ortho.setChecked(ortho)
        self.lock.setChecked(mode.live["locked"])
        self.lock.setIcon(_icon("lock" if mode.live["locked"] else "unlock",
                                "accent_text" if mode.live["locked"] else "text", 15))
        self.lock.setToolTip(t("pmode.unlock_tip" if mode.live["locked"] else "pmode.lock_tip"))
        self.frame_selection.setEnabled(bool(mode.vp.selection))
        self.fov.setVisible(self.is_on() and not ortho)
        self.fov_slider.blockSignals(True)
        self.fov_slider.setValue(int(round(mode.current_fov())))
        self.fov_slider.blockSignals(False)
        self.fov_value.setText(str(self.fov_slider.value()))
        for w in (self.keys,):
            w.setEnabled(not mode.live["locked"])
        self.look_button.setText(mode.look_text())
        self.sun_button.setText(mode.sun_text())
        for w in self.widgets:
            w.adjustSize()
        self.place()

    def _fov(self, value):
        self.fov_value.setText(str(value))
        self.mode.set_fov(float(value))

    def _fill_look_menu(self):
        """«Renderizado · Auto»: the Presentation's menu — the visual mode, the quality, the ambient occlusion and
        its strength, «Aplicar a todas as cenas»."""
        mode, menu = self.mode, self.look_menu
        menu.clear()
        menu.addSection(t("pmode.look_modes"))
        group = QtGui.QActionGroup(menu)
        current = mode.live_mode()
        for name in pm.STYLES:
            act = menu.addAction(t("pmode.style." + name), lambda n=name: mode.set_style(n))
            act.setCheckable(True)
            act.setChecked(name == current)
            group.addAction(act)
        menu.addSection(t("pmode.quality"))
        group = QtGui.QActionGroup(menu)
        for name in ("high", "medium", "low", "auto"):
            act = menu.addAction(t("pmode.quality." + name), lambda n=name: mode.set_look(quality=n))
            act.setCheckable(True)
            act.setChecked(mode.live["quality"] == name)
            group.addAction(act)
        menu.addSeparator()
        ao = menu.addAction(t("pmode.ao"), lambda: mode.set_look(ao=not mode.live["ao"]))
        ao.setCheckable(True)
        ao.setChecked(mode.live["ao"])
        strength = QtWidgets.QWidget(menu)
        line = QtWidgets.QHBoxLayout(strength)
        line.setContentsMargins(24, 2, 10, 2)
        line.addWidget(QtWidgets.QLabel(t("pmode.ao_intensity")))
        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setRange(0, 40)                         # (0–2 in steps of 0,05)
        slider.setValue(int(round(mode.live["ao_intensity"] * 20)))
        slider.setEnabled(mode.live["ao"])
        slider.sliderReleased.connect(lambda s=slider: mode.set_look(ao_intensity=s.value() / 20.0))
        line.addWidget(slider)
        action = QtWidgets.QWidgetAction(menu)
        action.setDefaultWidget(strength)
        menu.addAction(action)
        menu.addSeparator()
        every = menu.addAction(t("pmode.apply_all"), lambda: mode.set_apply_all(not mode.apply_all))
        every.setCheckable(True)
        every.setChecked(mode.apply_all)
        every.setToolTip(t("pmode.apply_all_tip"))

    def is_on(self):
        return self.mode.active

    def show(self):
        for w in self.widgets:
            w.show()
            w.raise_()
        self.show_state()

    def hide(self):
        for w in self.widgets:
            w.hide()

    def place(self):
        """Each box in its corner of the 3D view."""
        if not self.mode.active:
            return
        g = self.canvas.geometry()
        left, top, right, bottom = g.left() + MARGIN, g.top() + MARGIN, g.right() - MARGIN, g.bottom() - MARGIN
        self.create.move(left, top)
        self.camera.move(right - self.camera.width(), top)
        self.fov.move(right - self.fov.width(), top + self.camera.height() + 6)
        self.look.move(left, bottom - self.look.height())
        self.sun.move(right - self.sun.width(), bottom - self.sun.height())
        self.keys.move(right - self.keys.width(), bottom - self.sun.height() - 8 - self.keys.height())
        for w in self.widgets:
            w.raise_()

    def eventFilter(self, obj, event):  # noqa: N802
        if event.type() in (QtCore.QEvent.Type.Resize, QtCore.QEvent.Type.Move) and self.mode.active:
            QtCore.QTimer.singleShot(0, self.place)
        return False


# ------------------------------------------------------------------ the tab itself

class PresentationMode(QtCore.QObject):
    """What the ArqSynth Presentation tab is: its two columns, its commands over the 3D view, the scene chosen and what
    is seen live (the layers turned off, the visual mode, the lock), and what each command does to the presentation
    kept with the project."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.active = False
        self.scene_key = None               # the scene chosen (its card lit; the right column's pages are its)
        self.playing = None                 # "move" | "sun" while one is played in the 3D view
        self.apply_all = False              # «Aplicar a todas as cenas» (the look menu)
        self.live = {"hidden": set(), "style": "", "quality": "auto", "ao": True, "ao_intensity": 1.0,
                     "locked": False, "ortho": False}
        self._put_aside = None              # the BIM's panels hidden while the tab is in front, and their widths
        self._layers_stale = True
        self._entered_once = False
        self.pages = PagesPanel(self, win)
        self.side = SidePanel(self, win)
        win.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.pages)
        win.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.side)
        self.pages.hide()
        self.side.hide()
        self.overlay = Overlay(self, win.centralWidget(), win.canvas)
        self.act_create = QtGui.QAction(t("pmode.create"), win)
        self.act_create.setToolTip(t("pmode.create_tip"))
        self.act_create.triggered.connect(lambda _on=False: self.create_scene())
        self.act_thumbs = QtGui.QAction(t("present.thumbs"), win)
        self.act_thumbs.setToolTip(t("present.thumbs_tip"))
        self.act_thumbs.triggered.connect(lambda _on=False: self.win.scene_thumbnails())
        self.act_export = QtGui.QAction(t("present.export"), win)
        self.act_export.setToolTip(t("pmode.export_tip"))
        self.act_export.triggered.connect(lambda _on=False: self.export())
        self.restyle()

    # ------------------------------------------------------------ what it reads

    @property
    def doc(self):
        return self.win.doc

    @property
    def vp(self):
        return self.win.viewport

    def scenes(self):
        return pm.scenes(self.doc)

    def omitted(self):
        return pm.omitted(self.doc)

    def scene(self, key=None):
        key = key or self.scene_key
        return next((s for s in self.scenes() if s.key == key), None)

    def sheets(self):
        """The sheets that go as plan pages (those with views)."""
        return [s for s in self.doc.sheets if s.views]

    def site(self):
        return self.win._site_place()

    def rooms(self):
        return self.win._room_names()

    def room_count(self):
        try:
            return self.doc.ifc.count("IfcSpace")
        except AttributeError:
            return 0

    def options(self):
        return self.doc.presentation or pm.empty()

    def aspect(self):
        w, h = self.vp.logical_size()
        return w / h if h else 16 / 9

    def current_fov(self):
        """The Presentation's lens of the 3D view's camera now (its 35° when there is no perspective)."""
        fov = float(self.vp.camera.fov)
        return vertical_fov(fov, self.aspect()) if fov > 0 else pm.FOV_DEFAULT

    def ortho_of(self, scene):
        """Is the scene's camera without perspective (its own choice, else its view's)?"""
        if scene.projection:
            return scene.projection == "orthographic"
        if scene.kind == "view3d":
            view = self.doc.view3d(scene.view[1])
            return view is not None and bool(view.camera) and float(view.camera.get("fov") or 0) == 0
        return False

    def live_mode(self):
        """The visual mode seen now: the one chosen, else the 3D view style's as the Presentation's."""
        if self.live["style"]:
            return self.live["style"]
        from ..model import presentation_export
        return presentation_export._style(self.doc, self.doc.view_settings(("3d",)).style)["mode"]

    def look_text(self):
        return "{} · {}".format(t("pmode.style." + self.live_mode()), t("pmode.quality." + self.live["quality"]))

    def sun_text(self):
        """The sun's reading, as the Presentation's: «12:00  Az 199°  Alt 74°» (the site's, on the scene's day at its
        hour), or the view style's direction alone without a site."""
        scene = self.scene()
        place = self.site()
        if place is not None and scene is not None:
            az, alt = presentation_sun.angles(place[0], place[1], scene.sun_day, scene.sun_minutes)
            return "{:02d}:{:02d}   Az {:.0f}°   Alt {:.0f}°".format(scene.sun_minutes // 60, scene.sun_minutes % 60,
                                                                     az % 360, alt)
        from ..model import view_styles
        style = view_styles.BUILTIN["shaded"]
        return "Az {:.0f}°   Alt {:.0f}°".format(getattr(style, "sun_azimuth", 213.0),
                                                 getattr(style, "sun_altitude", 47.0))

    def thumb(self, key):
        """A scene card's picture: its thumbnail, or a plain card with the 3D page's cube."""
        jpeg = self.win._scene_thumbs.get(key)
        if jpeg:
            pm_ = QtGui.QPixmap()
            pm_.loadFromData(bytes(jpeg), "JPG")
            return pm_.scaled(THUMB, QtCore.Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                              QtCore.Qt.TransformationMode.SmoothTransformation).copy(0, 0, THUMB.width(),
                                                                                      THUMB.height())
        return self._blank(THUMB, "cube")

    @staticmethod
    def _blank(size, kind):
        out = QtGui.QPixmap(size)
        out.fill(theme.colour("header"))
        p = QtGui.QPainter(out)
        p.drawPixmap((size.width() - 22) // 2, (size.height() - 22) // 2,
                     glyphs.pixmap(kind, theme.colour("header_muted"), 22))
        p.end()
        return out

    def page_picture(self, found, initial):
        jpeg = self.win._scene_thumbs.get(initial) if initial else None
        if jpeg:
            out = QtGui.QPixmap()
            out.loadFromData(bytes(jpeg), "JPG")
            return out
        return self._blank(PAGE_THUMB, "cube")

    @staticmethod
    def sheet_picture(sheet):
        """A plan page's picture: its paper, its views as boxes, its title block's band."""
        out = QtGui.QPixmap(PAGE_THUMB)
        out.fill(QtGui.QColor("#ffffff"))                  # (paper stays white, as the drawings)
        p = QtGui.QPainter(out)
        p.setPen(QtGui.QPen(QtGui.QColor("#8a8f96"), 1))
        p.drawRect(4, 4, PAGE_THUMB.width() - 9, PAGE_THUMB.height() - 9)
        p.drawLine(PAGE_THUMB.width() - 40, 4, PAGE_THUMB.width() - 40, PAGE_THUMB.height() - 5)
        n = max(1, len(sheet.views))
        w = (PAGE_THUMB.width() - 56) // n
        for k in range(n):
            p.drawRect(10 + k * w, 12, w - 8, PAGE_THUMB.height() - 26)
        p.end()
        return out

    # ------------------------------------------------------------ in front, put away

    def enter(self):
        """The tab in front: the Presentation's columns instead of the BIM's (their widths kept: the 3D view keeps
        its size), its commands over the 3D view, the scene chosen (the first one, the first time)."""
        win = self.win
        if not self.active:
            left = QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
            right = QtCore.Qt.DockWidgetArea.RightDockWidgetArea
            shown = [d for d in win.findChildren(QtWidgets.QDockWidget)
                     if d.isVisible() and d not in (self.pages, self.side) and win.dockWidgetArea(d) in (left, right)]
            widths = {area: max([d.width() for d in shown if win.dockWidgetArea(d) == area] or [0])
                      for area in (left, right)}
            self._put_aside = shown
            for d in shown:
                d.hide()
            self.active = True
            self.pages.show()
            self.side.show()
            win.resizeDocks([self.pages, self.side], [widths[left] or 270, widths[right] or 300],
                            QtCore.Qt.Orientation.Horizontal)
        self.vp.cube_hidden = True
        self.vp.camera_locked = self.live["locked"]
        self.vp.set_hidden_elements(self.live["hidden"])
        if self.scene_key is None or self.scene(self.scene_key) is None:
            self.scene_key = pm.initial(self.doc)
        self.refresh(layers=True)
        self.overlay.restyle()
        self.overlay.show()
        win.refresh_context_bar()
        if hasattr(win, "_presentation_module"):          # (0.480: its icon lit in the left bar)
            win._presentation_module(True)
        if not self._entered_once:                         # (the tab's camera: the first scene's, the first time)
            self._entered_once = True
            QtCore.QTimer.singleShot(0, lambda: self.activate(self.scene_key) if self.active else None)

    def leave(self):
        """Another tab: the BIM's columns again as they were, every element drawn, the view cube back."""
        if not self.active:
            return
        self.active = False
        self.overlay.hide()
        self.vp.set_hidden_elements(set())
        self.vp.cube_hidden = False
        self.vp.camera_locked = False
        self.pages.hide()
        self.side.hide()
        for d in self._put_aside or ():
            d.show()
        self._put_aside = None
        self.win.refresh_context_bar()
        if hasattr(self.win, "_presentation_module"):
            self.win._presentation_module(False)

    def reset(self):
        """Another project: nothing chosen, nothing hidden."""
        self.scene_key = None
        self.live.update(hidden=set(), style="", quality="auto", ao=True, ao_intensity=1.0, locked=False)
        self._entered_once = False
        self._layers_stale = True
        if self.active:
            self.vp.set_hidden_elements(set())
            self.vp.camera_locked = False

    def restyle(self):
        self.pages.restyle()
        self.side.restyle()
        self.overlay.restyle()
        if self.active:
            self.refresh(layers=False)

    def refresh(self, layers=None, changed=None, removed=None):
        """The columns again (the project changed): the pages and the scenes; the layers when elements changed."""
        if not self.active or self.doc.loading:
            if layers or changed is None or removed or any(self.doc.get(i) is not None for i in (changed or ())
                                                           if isinstance(i, str)):
                self._layers_stale = True
            return
        if self.scene(self.scene_key) is None:
            self.scene_key = pm.initial(self.doc)
        if layers is None:
            layers = changed is None or bool(removed) or any(isinstance(i, str) and self.doc.get(i) is not None
                                                             for i in changed)
        if layers or self._layers_stale:
            self._layers_stale = False
            rows = self.layer_rows()
            known = {r[0] for r in rows}
            if self.live["hidden"] - known:               # (elements gone: no longer hidden)
                self.live["hidden"] &= known
                self.vp.set_hidden_elements(self.live["hidden"])
            self.side.pages["layers"].show_layers(rows, self.live["hidden"])
        self.pages.show_all()
        self.side.show_scene(self.scene())
        self.overlay.show_state()

    def layer_rows(self):
        """[(GlobalId, name, category, storey, IFC class)] of what goes to the Presentation, a layer each (the GLB's
        elements: model/gltf_export's), by category and name."""
        from ..model import gltf_export
        storeys = {g: n for g, n, _z in self.doc.storeys()}
        rows = []
        for obj in self.doc.objects.values():
            if not obj.is_bim or obj.mesh is None or obj.ifc_class in gltf_export.SKIP:
                continue
            category = gltf_export._category(obj.ifc_class) or t("pmode.no_category")
            rows.append((obj.id, obj.name or obj.id, category, storeys.get(obj.storey, t("gltf.no_storey")),
                         obj.ifc_class))
        return sorted(rows, key=lambda r: (r[2].lower(), r[1].lower()))

    def context_items(self):
        """The parameters' bar while the tab is in front: its commands, as a tool's."""
        icon = glyphs.icon("scene", theme.colour("text"), 20)
        return [("title", t("pmode.title"), icon), ("action", self.act_create), ("action", self.act_thumbs),
                ("separator",), ("action", self.act_export), ("separator",), ("hint", t("pmode.bar_hint"))]

    def selection_changed(self, ids):
        if self.active:
            self.side.pages["layers"].show_selection(ids)
            self.overlay.show_state()

    def set_playing(self, kind):
        self.playing = kind or None
        if self.active:
            self.side.show_scene(self.scene())

    # ------------------------------------------------------------ the scene chosen

    def activate(self, key):
        """A scene chosen (its card clicked): the 3D view as it was kept — its camera, projection and lens, the
        layers it hides, its visual mode, its lock — as the Presentation's «setActiveScene3D»."""
        scene = self.scene(key)
        if scene is None:
            return False
        self.scene_key = key
        vp = self.vp
        self.live.update(hidden=set(scene.hidden_layers), style=scene.style, quality=scene.quality, ao=scene.ao,
                         ao_intensity=scene.ao_intensity, locked=scene.locked)
        ortho = self.ortho_of(scene)
        vp.camera_locked = False                          # (placed by the program, not the mouse)
        if scene.kind == "view3d":
            view = self.doc.view3d(scene.view[1])
            camera = view.camera if view is not None else None
            if camera:
                vp.set_axonometric(float(camera.get("fov") or 0) == 0)
                vp.restore_camera(camera)
        elif scene.eye and scene.target:
            vp.set_axonometric(False)
            vp.look_at(scene.eye, scene.target)
        elif scene.kind == "overview":
            vp.set_axonometric(False)
            self.win._look_overview()
        elif scene.kind == "plan":
            self._frame_storey(scene.view[1])
        elif scene.kind == "section":
            self._frame_section(scene.view[1])
        if scene.fov > 0 and not vp.is_ortho():
            vp.camera.fov = pygfx_fov(scene.fov, self.aspect())
        self.live["ortho"] = ortho
        vp.set_axonometric(ortho)
        vp.camera_locked = self.live["locked"]
        vp.set_hidden_elements(self.live["hidden"])
        self.win._apply_look()
        self.side.pages["layers"].set_hidden(self.live["hidden"])
        self.pages.mark(key)
        self.side.show_scene(scene)
        self.overlay.show_state()
        vp.redraw()
        return True

    def _frame_storey(self, guid):
        objs = [o for o in self.doc.objects.values() if o.is_bim and o.storey == guid and o.mesh is not None]
        box = self.vp.bounds(objs or None)
        if box is None:
            self.vp.set_view("top")
            return
        lo, hi = (tuple(float(c) for c in corner) for corner in box)
        centre = tuple((a + b) / 2.0 for a, b in zip(lo, hi))
        radius = max(math.dist(lo, hi) / 2.0, 1.0)
        self.vp.set_view("top", centre, radius)

    def _frame_section(self, name):
        section = next((s for s in self.doc.sections if s.name == name), None)
        if section is None:
            return
        n = (float(section.normal[0]), float(section.normal[1]), 0.0)
        self.vp.view_along(n)

    def capture(self, scene):
        """What «Criar cena» / «Atualizar» keep of the 3D view as it is now (the Presentation's handleUpdateScene):
        its projection, lens, lock, visual mode, quality, ambient occlusion, the layers turned off — and, for a scene
        that is not a named 3D view, where its eye and target are."""
        vp = self.vp
        ortho = vp.is_ortho()
        fields = {"projection": "orthographic" if ortho else "perspective",
                  "fov": 0.0 if ortho else round(self.current_fov(), 2), "locked": self.live["locked"],
                  "style": self.live["style"], "quality": self.live["quality"], "ao": self.live["ao"],
                  "ao_intensity": self.live["ao_intensity"], "hidden_layers": sorted(self.live["hidden"])}
        if scene is None or scene.kind != "view3d":
            fields.update(eye=tuple(float(c) for c in vp.camera_position()), target=tuple(float(c) for c in vp._focus))
        return fields

    def _thumb_now(self, key):
        """The scene's thumbnail from the 3D view as it is (it is the scene's now)."""
        try:
            self.win._scene_thumbs[key] = self.win.thumbnail_now()
        except Exception:                                   # noqa: BLE001 — a thumbnail missing is no reason to stop
            import logging
            logging.getLogger(__name__).exception("thumbnail of a scene")

    def create_scene(self):
        """«Criar cena»: the 3D view as it is now kept as a new scene — a named 3D view «Cena N» (the lowest N not
        taken), with what is seen live —, chosen, its thumbnail taken. One undo step."""
        doc, vp = self.doc, self.vp
        if not any(o.is_bim for o in doc.objects.values()):
            self.win.message(t("info.presentation_empty"), warning=True)
            return None
        names = [s.name for s in pm.all_scenes(doc)] + [v.name for v in doc.views3d]
        name = pm.free_name(names, t("pmode.scene_word"))
        from ..model import view_templates
        props = {k: v for k, v in doc.view_props.get(("3d",), {}).items() if k in view_templates.LOOK_FIELDS}
        mark = doc.undo_mark()
        snapshot = vp.camera_snapshot()
        view = doc.add_view3d(snapshot, props, name)
        key = "vista_" + view[1]
        fields = self.capture(None)
        fields.update(eye=(), target=())                  # (a named 3D view: its own camera)
        doc.set_presentation(pm.changed(doc.presentation, key, **fields))
        doc.join_since(mark, t("pmode.cmd_create"))
        self.scene_key = key
        self._thumb_now(key)
        self.refresh(layers=False)
        self.win.message(t("pmode.created", name=doc.view3d(view[1]).name))
        return key

    def update_scene(self, key):
        """«Atualizar esta cena com a vista actual»: its camera (a named 3D view's own), what is seen live, its
        thumbnail. One undo step."""
        scene = self.scene(key)
        if scene is None:
            return False
        doc = self.doc
        if scene.kind == "view3d":
            doc.keep_view3d_camera(scene.view[1], self.vp.camera_snapshot())
        doc.set_presentation(pm.changed(doc.presentation, key, **self.capture(scene)))
        self.scene_key = key
        self._thumb_now(key)
        self.refresh(layers=False)
        self.win.message(t("pmode.updated", name=scene.name))
        return True

    def set_initial(self, key):
        """«Definir como cena inicial» (it is not turned off: another one is chosen instead)."""
        if key and self.scene(key) is not None:
            self.doc.set_presentation(pm.with_initial(self.doc.presentation, key))
            self.refresh(layers=False)

    def toggle_hidden(self, key):
        """«Esconder da apresentação» / «Mostrar na apresentação» — never the last scene shown."""
        scene = self.scene(key)
        if scene is None:
            return False
        if not scene.hidden and sum(1 for s in self.scenes() if not s.hidden) <= 1:
            self.win.message(t("pmode.only_visible"), warning=True)
            return False
        self.doc.set_presentation(pm.changed(self.doc.presentation, key, hidden=not scene.hidden))
        self.refresh(layers=False)
        return True

    def duplicate(self, key):
        """«Duplicar cena»: a copy after it («Cena 1 cópia»), as a named 3D view seen as the scene is, with what was
        chosen for it; the copy chosen. One undo step."""
        scene = self.scene(key)
        if scene is None:
            return None
        doc = self.doc
        if key != self.scene_key:
            self.activate(key)
        kept = dict((doc.presentation or pm.empty())["scenes"].get(key, {}))
        for name in ("name", "eye", "target", "omit"):
            kept.pop(name, None)
        names = [s.name for s in pm.all_scenes(doc)] + [v.name for v in doc.views3d]
        if scene.kind == "view3d" and doc.view3d(scene.view[1]) is not None:
            source = doc.view3d(scene.view[1])
            camera, props = source.camera, doc.view_props.get(("3d", source.uid))
        else:
            camera, props = self.vp.camera_snapshot(), None
        mark = doc.undo_mark()
        view = doc.add_view3d(camera, props, pm.copy_name(scene.name, names, t("pmode.copy_word")))
        new = "vista_" + view[1]
        order = [s.key for s in pm.all_scenes(doc) if s.key != new]
        order.insert(order.index(key) + 1, new)
        data = pm.ordered(doc.presentation, order)
        if kept:
            data = pm.changed(data, new, **kept)
        doc.set_presentation(data)
        doc.join_since(mark, t("pmode.cmd_duplicate"))
        self.scene_key = new
        self.refresh(layers=False)
        return new

    def rename(self, key, name=None):
        """«Renomear cena»: a named 3D view renamed (its tab too); another scene given a name of its own here."""
        scene = self.scene(key)
        if scene is None:
            return False
        if name is None:
            name, ok = QtWidgets.QInputDialog.getText(self.win, t("pmode.rename_tip"), t("pmode.rename_label"),
                                                      text=scene.name)
            if not ok:
                return False
        name = (name or "").strip()
        if not name or name == scene.name:
            return False
        if scene.kind == "view3d":
            if not self.doc.rename_view3d(scene.view[1], name):
                self.win.message(t("err.view_name", name=name), warning=True)
                return False
        else:
            self.doc.set_presentation(pm.changed(self.doc.presentation, key, name=name))
        self.refresh(layers=False)
        return True

    def delete(self, key):
        """«Eliminar cena»: a scene made here (a named 3D view) deleted with its view; a view's scene (the general view,
        a plan, a section) left out of what is sent — the view stays in the project. The scene chosen: the first one
        then. One undo step (Ctrl+Z brings it back)."""
        scene = self.scene(key)
        if scene is None:
            return False
        if scene.kind == "view3d":
            self.doc.remove_view3d(scene.view[1])
        else:
            self.doc.set_presentation(pm.changed(self.doc.presentation, key, omit=True))
        if self.scene_key == key:
            found = self.scenes()
            self.scene_key = found[0].key if found else None
        self.refresh(layers=False)
        self.win.message(t("pmode.deleted", name=scene.name))
        return True

    def restore_omitted(self):
        """The views' scenes left out, sent again."""
        keys = [s.key for s in self.omitted()]
        if keys:
            self.doc.set_presentation(pm.changed_all(self.doc.presentation, keys, omit=False))
            self.refresh(layers=False)

    def move_scene(self, key, target, after=False):
        """A card dropped on another: the scene before (or after) it."""
        order = [s.key for s in pm.all_scenes(self.doc)]
        if key not in order or target not in order or key == target:
            return False
        order.remove(key)
        order.insert(order.index(target) + (1 if after else 0), key)
        self.doc.set_presentation(pm.ordered(self.doc.presentation, order))
        self.refresh(layers=False)
        return True

    def set_transition(self, seconds):
        """«Transição»: every scene's arrival this long (each keeps its kind). One undo step."""
        found = self.scenes()
        seconds = round(min(max(float(seconds), pm.TRANSITION_MIN), pm.TRANSITION_MAX), 1)
        if found and any(abs(s.transition_s - seconds) > 1e-9 for s in found):
            self.doc.set_presentation(pm.changed_all(self.doc.presentation, [s.key for s in found],
                                                     transition_s=seconds), t("pmode.cmd_transition"))
            self.refresh(layers=False)

    def change(self, **fields):
        """The scene chosen's settings (the right column's pages). One undo step."""
        if self.scene_key is not None and self.scene() is not None:
            self.doc.set_presentation(pm.changed(self.doc.presentation, self.scene_key, **fields))
            self.refresh(layers=False)

    def set_option(self, **options):
        self.doc.set_presentation(pm.with_options(self.doc.presentation, **options))
        self.refresh(layers=False)

    def open_view_of(self, key):
        """A card double-clicked: its view in the BIM's own tab (the Presentation's columns put away)."""
        self.win.open_scene(key)

    def open_sheet(self, uid):
        index = next((k for k, s in enumerate(self.doc.sheets) if s.uid == uid), None)
        if index is not None:
            self.win.sheet_action("open", index)

    def add_page(self, kind):
        """PÁGINAS: «Modelo 3D» — the 3D page chosen; «Planta» — a new sheet (it goes as a plan page once it has
        views). Capa, Texto and Concept are made in the Presentation."""
        if kind == "model":
            self.pages.choose_page("model")
        elif kind == "plan":
            self.win.sheet_action("new")
            self.win.message(t("pmode.sheet_new"))

    def export(self):
        """«Exportar / atualizar»: the package for the Presentation (its «Importar / atualizar» reads it)."""
        return self.win.export_presentation()

    def play_move(self):
        return self.win.play_scene_move(self.scene_key)

    def play_sun(self):
        return self.win.play_scene_sun(self.scene_key)

    # ------------------------------------------------------------ the 3D view's commands

    def set_ortho(self, on):
        """PERSP / ORTO (the 3D view's own projection is not changed: this tab's)."""
        self.live["ortho"] = bool(on)
        self.vp.set_axonometric(bool(on))
        self.overlay.show_state()
        self.pages.show_all()

    def set_fov(self, vertical):
        """The FOV (the Presentation's 20–65°): the lens changed, the camera moved so that what is at the focus stays
        as big (as the Presentation's dolly zoom)."""
        vp = self.vp
        if vp.is_ortho() or self.live["locked"]:
            self.overlay.show_state()
            return
        before = self.current_fov()
        focus = vp._focus.copy()
        eye = vp.camera_position()
        reach = float(((focus - eye) ** 2).sum()) ** 0.5
        if reach > 1e-6:
            scale = math.tan(math.radians(before) / 2.0) / math.tan(math.radians(vertical) / 2.0)
            vp.camera.fov = pygfx_fov(vertical, self.aspect())
            vp.look_at(focus - (focus - eye) * scale, focus, up=tuple(vp.camera.world.up))
        else:
            vp.camera.fov = pygfx_fov(vertical, self.aspect())
            vp.redraw()

    def frame_model(self):
        self.vp.zoom_extents()

    def frame_selection(self):
        ids = [i for i in self.vp.selection if isinstance(i, str)]
        if ids:
            self.vp.zoom_extents(ids)

    def toggle_lock(self):
        """«Bloquear câmara da cena»: the mouse no longer moves the camera (kept with the scene)."""
        self.live["locked"] = not self.live["locked"]
        self.vp.camera_locked = self.live["locked"]
        self.overlay.show_state()
        self.win.message(t("pmode.locked" if self.live["locked"] else "pmode.unlocked"))

    def look(self, face):
        """T, E, F, D, B, TRÁS: the model seen from that side, framed."""
        if self.live["locked"]:
            return
        self.vp.look_from(FACES[face])

    def turn(self, sign):
        """The view turned 90° round the model (left: 1, right: −1)."""
        if not self.live["locked"]:
            self.vp.turn_about(sign * math.pi / 2.0)

    def set_style(self, name):
        """A visual mode of «Renderizado · Auto» (seen in the 3D view with the BIM's style most like it); with
        «Aplicar a todas as cenas», every scene's at once."""
        self.live["style"] = name if name in pm.STYLES else ""
        self.win._apply_look()
        if self.apply_all:
            self._to_all(style=self.live["style"])
        self.overlay.show_state()

    def set_look(self, **fields):
        """The quality, the ambient occlusion and its strength (they go to the Presentation; the BIM's view does not
        show them)."""
        for name in ("quality", "ao", "ao_intensity"):
            if name in fields:
                self.live[name] = fields[name]
        if self.apply_all:
            self._to_all(**{k: self.live[k] for k in fields if k in self.live})
        self.overlay.show_state()

    def set_apply_all(self, on):
        self.apply_all = bool(on)
        if self.apply_all:
            self._to_all(style=self.live["style"], quality=self.live["quality"], ao=self.live["ao"],
                         ao_intensity=self.live["ao_intensity"])

    def _to_all(self, **fields):
        found = self.scenes()
        if found:
            self.doc.set_presentation(pm.changed_all(self.doc.presentation, [s.key for s in found], **fields),
                                      t("pmode.cmd_look"))
            self.refresh(layers=False)

    def live_view_style(self):
        """The BIM view style the 3D view is drawn with in the tab (None: the 3D view's own)."""
        return pm.STYLE_VIEW.get(self.live["style"]) if self.active and self.live["style"] else None

    def set_layers_hidden(self, ids, hide):
        """The eyes of the layers: these elements not seen (live, as in the Presentation: kept in a scene when it is
        made or updated)."""
        ids = {i for i in ids if i}
        hidden = (self.live["hidden"] | ids) if hide else (self.live["hidden"] - ids)
        self.live["hidden"] = hidden
        self.vp.set_hidden_elements(hidden)
        self.side.pages["layers"].set_hidden(hidden)

    def select(self, ids):
        self.win._select_from_tree([i for i in ids if i not in self.live["hidden"]])

    def frame(self, ids):
        self.win._frame_from_tree(ids)
