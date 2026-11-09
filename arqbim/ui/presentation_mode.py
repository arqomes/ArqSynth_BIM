"""(0.479) The ArqSynth Presentation tab — the owner, 2026-11-08, with a picture of the Presentation's 3D page: «crie
uma aba de ArqSynth Presentation e use as 2 colunas para replicar a experiência que se tem no ArqSynth Presentation,
preparando o modelo 3D para exportação com todas as configurações do ArqSynth Presentation. Ao clicar na aba a tela
muda a interface para a interface do ArqSynth Presentation».

(0.480) Opened by the left bar's icon (a module); (0.481) in a tab of its own only while it is open (view_tabs.PRESENT)
and laid out as the Presentation's NEW 3D page (its docs/PLANO-LIMPAR-TELA-3D.md — the owner: «a imagem… era apenas uma
referência… faça de acordo com o novo»). While it is in front the window's columns are the Presentation's —
- on the left (PagesPanel): DIVIDIDO / ABAS, the PÁGINAS that go in the package (the Modelo 3D page and a Planta page
  per sheet with views; Capa, Texto and Concept are made over there), the 3D page's scenes as the Presentation's cards
  (thumbnail, number, star of the first one, name, PERSPECTIVA / ORTOGONAL, and Atualizar · Cena inicial · Mostrar ·
  Duplicar · Renomear · Eliminar), «Exportar / atualizar», «Página final»; at its fixed foot CENAS n with «+ Criar cena»
  and the TRANSIÇÃO of every scene;
- on the right (SidePanel): the Presentation's rail — Camadas (every element under its category, its eye; «Procurar
  peça…»), Cenas 3D, Ambiente, Etiquetas, Imagens, Efeitos, Passeio —, each for the scene chosen;
- on the parameters' bar (the Presentation's strip over its 3D view): the camera in one line — PERSP / ORTO, FOV,
  «Enquadrar modelo», «Enquadrar selecção», the lock (CameraStrip);
- on the footer: «Renderizado · Auto ▾» (FooterLook) and the sun's reading (FooterSun);
- under the 3D view: the scenes' player ‹ ▶ 1/4 · nome › (ScenePlayer).
Nothing over the model: the 3D view keeps the BIM's own view cube and navigation (the owner: «o cubo de navegação devia
continuar o mesmo do programa»). The BIM's own columns come back as they were when the tab is closed or left.

What is chosen here goes where the Presentation keeps it, through model/presentation.py (one undo step a change) and
model/presentation_export.py: a scene is a view of the project — «Criar cena» keeps the 3D view as a named 3D view
(«Cena 2»), «Atualizar» keeps the view again —, with its camera (projection, lens, locked), its visual mode, quality and
ambient occlusion, the layers it hides (the eyes, as the Presentation's: live until a scene is made or updated), its
arrival, effect, camera move, sun, exposure, sky, caption and time. The names, ranges and defaults are the
Presentation's own (its SlideSidebar, Model3DViewport, NaviCube, VisualModeMenu and LayersTab)."""

import math

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..model import camera_moves
from ..model import presentation as pm
from ..model import presentation_sun
from ..model import presentation_tags
from ..model import presentation_diagrams as diagrams_model
from . import presentation_diagrams
from . import presentation_glyphs as glyphs
from . import presentation_labels
from . import theme

KEY = QtCore.Qt.ItemDataRole.UserRole
THUMB = QtCore.QSize(84, 47)            # a scene card's picture (16:9)
PAGE_THUMB = QtCore.QSize(150, 84)      # a page card's
MIME = "application/x-arqsynth-scene"   # a scene card dragged to another place
RAIL = (("layers", "layers"), None, ("scenes", "film"), ("cuts", "section"), ("environment", "sun"),
        ("diagrams", "shapes"), ("labels", "tag"), ("images", "pano"), ("effects", "camera"), None, ("walk", "walk"))


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
QToolButton#pm_page:checked { background: %(chip_on)s; color: %(chip_on_text)s; border-color: %(accent)s; }
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
QWidget#pm_strip QLabel#pm_strip_label { color: %(muted)s; font-weight: 700; background: transparent; }
QWidget#pm_strip QToolButton { border: none; border-radius: 5px; padding: 3px 7px; color: %(text)s;
                               background: transparent; font-weight: 700; }
QWidget#pm_strip QToolButton:hover { background: %(button_hover)s; }
QWidget#pm_strip QToolButton:checked { background: %(accent)s; color: %(accent_text)s; }
QWidget#pm_strip QToolButton:disabled { color: %(hint)s; }
QToolButton#pm_footer { border: none; border-radius: 5px; padding: 1px 8px; color: %(text)s; font-weight: 600;
                        background: transparent; }
QToolButton#pm_footer:hover { background: %(button_hover)s; }
QFrame#pm_player { background: %(bar)s; border: none; border-top: 1px solid %(line)s; }
QFrame#pm_player QToolButton { border: none; border-radius: 5px; padding: 2px 8px; color: %(text)s;
                               background: transparent; font-weight: 700; font-size: 14px; }
QFrame#pm_player QToolButton:hover { background: %(button_hover)s; }
QFrame#pm_player QToolButton:disabled { color: %(hint)s; }
QLabel#pm_player_label { color: %(text)s; font-weight: 600; }
QLabel#pm_player_time { color: %(muted)s; }
QPushButton#pm_create { border: 1px solid %(accent)s; border-radius: 6px; padding: 3px 8px; color: %(accent)s;
                        background: transparent; font-weight: 700; }
QPushButton#pm_create:hover { background: %(select_soft)s; }
QFrame#pm_end { background: transparent; border: 1px dashed %(line)s; border-radius: 8px; }
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
            self.panel.mode.activate(self.key, fly=True)    # (0.483: flown there, as in the Presentation)
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
        # (0.481) «+ Criar cena» on the fixed foot, beside the scenes' count — the Presentation's new place for it (in
        # the list it scrolled away)
        self.create_button = QtWidgets.QPushButton(t("pmode.create"))
        self.create_button.setObjectName("pm_create")
        self.create_button.setToolTip(t("pmode.create_tip"))
        self.create_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.create_button.clicked.connect(lambda: self.mode.create_scene())
        foot.addWidget(self.create_button)
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
        self.create_button.setIcon(_icon("plus", "accent", 14))

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
            self.list_box.addWidget(self._end_card())
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

    @staticmethod
    def _end_card():
        """(0.481) «Página final», as the Presentation's list ends: made over there (its end page), shown here dashed."""
        card = QtWidgets.QFrame()
        card.setObjectName("pm_end")
        card.setToolTip(t("pmode.end_page_tip"))
        box = QtWidgets.QVBoxLayout(card)
        box.setContentsMargins(10, 8, 10, 8)
        box.setSpacing(2)
        box.addWidget(_label(t("pmode.end_page"), "pm_name"))
        note = _label(t("pmode.end_page_note"), "pm_sub")
        note.setWordWrap(True)
        box.addWidget(note)
        return card

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
    how long), its time and its caption (0.486: its effect in EFEITOS, as the Presentation's)."""

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
        self.seconds = _seconds(0.0, 600.0, 1.0)            # (0.486: the effect in the Efeitos tab, as there)
        self.seconds.setSpecialValueText(t("present.seconds_auto"))
        self.seconds.setToolTip(t("present.seconds_tip"))
        self.seconds.valueChanged.connect(lambda v: self.change(seconds=v))
        self.form.addRow(t("present.seconds"), self.seconds)
        self.caption = _Caption(self)
        self.caption.setToolTip(t("present.caption_tip"))
        self.caption.setFixedHeight(64)
        self.form.addRow(t("present.caption"), self.caption)
        self.fields = (self.initial, self.shown, self.transition, self.transition_s, self.seconds, self.caption)

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


class CutsPage(_Form):
    """(0.484) CORTES, as the Presentation's: the section planes seen now — Horizontal, Vertical X, Vertical Z —, each
    at its exact position (m), its side turned or not, removed; non-destructive; kept in the scene with «Criar cena» /
    «Atualizar» (the Presentation: «os cortes guardam-se na cena ao Criar/Actualizar»)."""

    def __init__(self, mode):
        super().__init__(mode)
        self.form.addRow(_label(t("pmode.cuts_planes").upper(), "pm_head"))
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(4)
        self.add_buttons = {}
        for kind in pm.CUT_TYPES:
            button = QtWidgets.QPushButton(t("pmode.cut." + kind))
            button.setToolTip(t("pmode.cut_tip." + kind))
            button.clicked.connect(lambda _on=False, k=kind: self.mode.add_cut(k))
            row.addWidget(button)
            self.add_buttons[kind] = button
        self.form.addRow(row)
        self.holder = QtWidgets.QWidget()
        self.rows = QtWidgets.QVBoxLayout(self.holder)
        self.rows.setContentsMargins(0, 0, 0, 0)
        self.rows.setSpacing(6)
        self.form.addRow(self.holder)
        self.empty = self.note("pmode.cuts_empty")
        # (0.491) ASPETO DO CORTE — the Presentation's «Superfície cortada»: the materials' hatches, Poché, Sólido, Aberto
        self.form.addRow(_label(t("pmode.cut_look").upper(), "pm_head"))
        tiles = QtWidgets.QGridLayout()
        tiles.setSpacing(4)
        self.looks = {}
        for k, look in enumerate(pm.CUT_LOOKS):
            button = QtWidgets.QToolButton()
            button.setObjectName("pm_page")
            button.setCheckable(True)
            button.setText(t("pmode.cut_look." + look))
            button.setToolTip(t("pmode.cut_look_tip." + look))
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
            button.clicked.connect(lambda _on=False, k_=look: self.mode.set_cut_look(k_))
            tiles.addWidget(button, k // 2, k % 2)
            self.looks[look] = button
        self.form.addRow(tiles)
        self.colour = QtWidgets.QPushButton()
        self.colour.setToolTip(t("pmode.cut_colour"))
        self.colour.clicked.connect(self._pick_colour)
        self.form.addRow(t("pmode.cut_colour"), self.colour)
        self.note("pmode.cuts_saved")
        self.spins = []

    def _pick_colour(self):
        colour = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.mode.live["cut_colour"]), self,
                                                 t("pmode.cut_colour"))
        if colour.isValid():
            self.mode.set_cut_colour(colour.name())

    def show_scene(self, _scene):
        """The rows again (a plane added or removed, another scene chosen)."""
        while self.rows.count():
            item = self.rows.takeAt(0)
            if item.widget() is not None:
                item.widget().hide()
                item.widget().deleteLater()
        self.spins = []
        cuts = self.mode.live["cuts"]
        for k, (kind, position, flip) in enumerate(cuts):
            self.rows.addWidget(self._row(k, kind, position, flip))
        self.empty.setVisible(not cuts)
        for button in self.add_buttons.values():
            button.setEnabled(len(cuts) < pm.MAX_CUTS)
        look, colour = self.mode.live["cut_look"], self.mode.live["cut_colour"]
        for name, button in self.looks.items():
            button.setChecked(name == look)
        pixmap = QtGui.QPixmap(14, 14)
        pixmap.fill(QtGui.QColor(colour))
        self.colour.setIcon(QtGui.QIcon(pixmap))
        self.colour.setText(colour)
        self.form.setRowVisible(self.colour, look in ("poche", "solid"))

    def _row(self, k, kind, position, flip):
        box = QtWidgets.QFrame()
        box.setObjectName("pm_card")
        lay = QtWidgets.QVBoxLayout(box)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(4)
        lay.addWidget(_label(t("pmode.cut." + kind), "pm_name"))
        lo, hi = self.mode.cut_range(kind)
        line = QtWidgets.QHBoxLayout()
        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setRange(int(round(lo * 100)), int(round(hi * 100)))       # (cm)
        slider.setValue(int(round(position * 100)))
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(lo, hi)
        spin.setDecimals(2)
        spin.setSingleStep(0.05)
        spin.setSuffix(" m")
        spin.setValue(position)
        spin.setToolTip(t("pmode.cut_position"))
        slider.valueChanged.connect(lambda v, s=spin: s.setValue(v / 100.0))
        spin.valueChanged.connect(lambda v, s=slider, i=k: (s.blockSignals(True), s.setValue(int(round(v * 100))),
                                                            s.blockSignals(False), self.mode.move_cut(i, v)))
        line.addWidget(slider, 1)
        line.addWidget(spin)
        lay.addLayout(line)
        buttons = QtWidgets.QHBoxLayout()
        turn = QtWidgets.QPushButton(t("pmode.cut_flip"))
        turn.setCheckable(True)
        turn.setChecked(flip)
        turn.toggled.connect(lambda on, i=k: self.mode.flip_cut(i, on))
        gone = QtWidgets.QPushButton(t("pmode.cut_remove"))
        gone.clicked.connect(lambda _on=False, i=k: self.mode.remove_cut(i))
        buttons.addWidget(turn)
        buttons.addWidget(gone)
        buttons.addStretch(1)
        lay.addLayout(buttons)
        self.spins.append(spin)
        return box


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
    """EFEITOS, as the Presentation's — its two kinds: MODELO (0.486: the scene's effect — Nenhum, Estudo solar,
    Construção, Explosão —, how long, played when the scene is entered, an explosion's distance, the order of the works
    with the elements taken out of it, «Pré-visualizar» in the 3D view) and CÂMARA (its camera move from the
    Presentation's library, by its groups, how long, the room of an interior one — «Ver movimento»)."""

    def __init__(self, mode):
        super().__init__(mode)
        seg = QtWidgets.QFrame()
        seg.setObjectName("pm_segbox")
        row = QtWidgets.QHBoxLayout(seg)
        row.setContentsMargins(3, 3, 3, 3)
        row.setSpacing(2)
        self.categories = {}
        group = QtWidgets.QButtonGroup(seg)
        for name in ("model", "camera"):
            button = QtWidgets.QToolButton()
            button.setObjectName("pm_seg")
            button.setCheckable(True)
            button.setText(t("pmode.effects_" + name).upper())
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
            button.clicked.connect(lambda _on=False, k=name: self.set_category(k))
            group.addButton(button)
            row.addWidget(button)
            self.categories[name] = button
        self.form.addRow(seg)
        self.category = "model"
        self.model_box = self._model_form()
        self.form.addRow(self.model_box)
        self.camera_box = QtWidgets.QWidget()
        camera = QtWidgets.QFormLayout(self.camera_box)
        camera.setContentsMargins(0, 0, 0, 0)
        camera.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)
        camera.setVerticalSpacing(8)
        self.camera_form = camera
        self.form.addRow(self.camera_box)
        self._camera_rows(camera)
        self.categories["model"].setChecked(True)
        self.camera_box.hide()

    def set_category(self, name):
        """MODELO / CÂMARA (the Presentation's two kinds of effects)."""
        self.category = name if name in self.categories else "model"
        self.categories[self.category].setChecked(True)
        self.model_box.setVisible(self.category == "model")
        self.camera_box.setVisible(self.category == "camera")
        self.show_scene(self.mode.scene())

    def _model_form(self):
        box = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(box)
        form.setContentsMargins(0, 0, 0, 0)
        form.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setVerticalSpacing(8)
        self.model_rows = form
        form.addRow(_label(t("pmode.effect_scene").upper(), "pm_head"))
        tiles = QtWidgets.QGridLayout()
        tiles.setSpacing(4)
        self.kinds = {}
        for k, name in enumerate(pm.EFFECTS):
            button = QtWidgets.QToolButton()
            button.setObjectName("pm_page")
            button.setCheckable(True)
            button.setText(t("pmode.effect_kind." + name))
            button.setToolTip(t("pmode.effect_hint." + name))
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
            button.clicked.connect(lambda _on=False, e=name: self._kind(e))
            tiles.addWidget(button, k // 2, k % 2)
            self.kinds[name] = button
        form.addRow(tiles)
        self.hint = _label("", "pm_note")
        self.hint.setWordWrap(True)
        form.addRow(self.hint)
        self.effect_s = _seconds(2.0, 60.0, 1.0)
        self.effect_s.setDecimals(0)
        self.effect_s.valueChanged.connect(lambda v: self.change(effect_s=v))
        form.addRow(t("pmode.effect_time"), self.effect_s)
        self.auto = QtWidgets.QCheckBox(t("pmode.effect_auto"))
        self.auto.setToolTip(t("pmode.effect_auto_tip"))
        self.auto.toggled.connect(lambda on: self.change(effect_auto=on))
        form.addRow(self.auto)
        self.spread = QtWidgets.QDoubleSpinBox()
        self.spread.setRange(0.3, 3.0)
        self.spread.setDecimals(1)
        self.spread.setSingleStep(0.1)
        self.spread.setSuffix("×")
        self.spread.setKeyboardTracking(False)
        self.spread.setToolTip(t("pmode.effect_spread_tip"))
        self.spread.valueChanged.connect(lambda v: self.change(effect_spread=v))
        form.addRow(t("pmode.effect_spread"), self.spread)
        self.sun_hint = _label(t("pmode.effect_sun_hint"), "pm_note")
        self.sun_hint.setWordWrap(True)
        form.addRow(self.sun_hint)
        self.preview = QtWidgets.QPushButton(t("pmode.effect_preview"))
        self.preview.setObjectName("pm_create")
        self.preview.setToolTip(t("pmode.effect_preview_tip"))
        self.preview.clicked.connect(lambda: self.mode.play_effect())
        form.addRow(self.preview)
        self.order_head = _label("", "pm_head")
        form.addRow(self.order_head)
        self.order = QtWidgets.QListWidget()
        self.order.setMaximumHeight(240)
        self.order.setToolTip(t("pmode.effect_order_tip"))
        self.order.itemChanged.connect(self._order_changed)
        form.addRow(self.order)
        self.order_note = _label(t("pmode.effect_order_note"), "pm_note")
        self.order_note.setWordWrap(True)
        form.addRow(self.order_note)
        note = _label(t("pmode.effect_saved"), "pm_note")
        note.setWordWrap(True)
        form.addRow(note)
        return box

    def _kind(self, name):
        if self.showing:
            return
        if self.mode.playing == "effect":
            self.mode.win.stop_scene_move()
        self.change(effect=name)

    def _order_changed(self, item):
        """An element of the order of the works ticked (in the effect) or not (left out: still from the start)."""
        if self.showing:
            return
        guid = item.data(KEY)
        scene = self.mode.scene()
        if scene is None or not guid:
            return
        static = set(scene.effect_static)
        if item.checkState() == QtCore.Qt.CheckState.Checked:
            static.discard(guid)
        else:
            static.add(guid)
        self.change(effect_static=sorted(static))

    def _show_model(self, scene):
        effect = scene.effect
        for name, button in self.kinds.items():
            button.setChecked(name == effect)
        self.hint.setText(t("pmode.effect_hint." + effect))
        rows = self.model_rows
        on = effect != "none"
        for w in (self.effect_s, self.auto, self.preview):
            rows.setRowVisible(w, on)
        rows.setRowVisible(self.spread, effect == "explode")
        rows.setRowVisible(self.sun_hint, effect == "sun")
        self.effect_s.setValue(scene.effect_s)
        self.auto.setChecked(scene.effect_auto)
        self.spread.setValue(scene.effect_spread)
        playing = self.mode.playing == "effect"
        self.preview.setText(t("present.stop" if playing else "pmode.effect_preview"))
        building = effect == "construction"
        for w in (self.order_head, self.order, self.order_note):
            rows.setRowVisible(w, building)
        if building:
            self._fill_order(scene)

    def _fill_order(self, scene):
        """The order of the works as the Presentation plays it: «1. Parede 3 — Paredes», each ticked unless it was
        taken out of the effect."""
        from ..model import presentation_effects
        units, _centre, _radius = self.mode.effect_units()
        static = set(scene.effect_static)
        by_id = {u["id"]: u for u in units}
        self.order.clear()
        for k, guid in enumerate(presentation_effects.order(units)):
            u = by_id[guid]
            phase = presentation_effects.phase_name(presentation_effects.phase_of(u["name"], u["category"]))
            item = QtWidgets.QListWidgetItem("{}. {}  —  {}".format(k + 1, u["name"], t("pmode.phase." + phase)))
            item.setData(KEY, guid)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Unchecked if guid in static else QtCore.Qt.CheckState.Checked)
            item.setToolTip(t("pmode.effect_restore" if guid in static else "pmode.effect_exclude"))
            self.order.addItem(item)
        self.order_head.setText(t("pmode.effect_order", n=len(units)).upper())

    def _camera_rows(self, form):
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
        form.addRow(t("present.move"), box)
        self.move_s = _seconds(0.0, 120.0, 1.0)
        self.move_s.valueChanged.connect(lambda v: self.change(move_s=v))
        form.addRow(t("pmode.move_time"), self.move_s)
        self.room = _narrow(QtWidgets.QComboBox())
        self.room.setToolTip(t("present.room_tip"))
        self.room.currentIndexChanged.connect(lambda _i: self.change(room=self.room.currentData() or ""))
        form.addRow(t("present.room"), self.room)
        self.play = QtWidgets.QPushButton(t("present.play"))
        self.play.setToolTip(t("present.play_tip"))
        self.play.clicked.connect(lambda: self.mode.play_move())
        form.addRow(self.play)
        note = _label(t("pmode.effects_note"), "pm_note")
        note.setWordWrap(True)
        form.addRow(note)
        self.fields = (self.move_box, self.move_s, self.room, self.play, *self.kinds.values(), self.effect_s,
                       self.auto, self.spread, self.preview, self.order)

    def show_scene(self, scene):
        self.showing = True
        try:
            for w in self.fields:
                w.setEnabled(scene is not None)
            if scene is None:
                return
            self._show_model(scene)
            self.move_box.setCurrentIndex(max(self.move_box.findData(scene.move), 0))
            own = camera_moves.MOVES[scene.move][2] if scene.move else 0.0
            self.move_s.setSpecialValueText(t("present.move_own", s="{:.0f}".format(own)) if scene.move else "—")
            self.move_s.setValue(scene.move_s)
            self.move_s.setEnabled(bool(scene.move))
            inside = camera_moves.interior(scene.move)
            self.camera_form.setRowVisible(self.room, inside)
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


class WalkPage(_Form):
    """PASSEIO (0.488): the rooms as the Virtual Walk's zones, linked by the doors and stairs — on or off; how many rooms,
    doors and stairs; the room it starts in (the usual: behind the door from outside, on the lowest storey); the
    seconds in each room of its guided tour; the guided tour in the order it is walked, each room ticked (in the walk)
    or not (left out: not navigable there), those it cannot reach marked; «Percorrer a visita guiada» and «Ir até ao
    escolhido» walk it in the 3D view at a person's eye. Its zones and ways are seen over the model while it is open."""

    def __init__(self, mode):
        super().__init__(mode)
        self.box = QtWidgets.QCheckBox(t("present.walk"))
        self.box.toggled.connect(lambda on: None if self.showing else self.mode.set_option(walk=on))
        self.form.addRow(self.box)
        self.note("pmode.walk_note")
        self.counts = _label("", "pm_note")
        self.counts.setWordWrap(True)
        self.form.addRow(self.counts)
        self.start = _narrow(QtWidgets.QComboBox())
        self.start.setToolTip(t("pmode.walk_start_tip"))
        self.start.currentIndexChanged.connect(
            lambda _i: None if self.showing else self.mode.set_option(walk_start=self.start.currentData() or ""))
        self.form.addRow(t("pmode.walk_start"), self.start)
        self.dwell = _seconds(0.5, 60.0, 0.5)
        self.dwell.valueChanged.connect(lambda v: None if self.showing else self.mode.set_option(walk_dwell=v))
        self.form.addRow(t("pmode.walk_dwell"), self.dwell)
        self.form.addRow(_label(t("pmode.walk_tour").upper(), "pm_head"))
        self.tour = QtWidgets.QListWidget()
        self.tour.setMaximumHeight(220)
        self.tour.setToolTip(t("pmode.walk_off_tip"))
        self.tour.itemChanged.connect(self._ticked)
        self.tour.itemDoubleClicked.connect(lambda item: self.mode.play_walk(item.data(KEY)))
        self.form.addRow(self.tour)
        self.play = QtWidgets.QPushButton(t("pmode.walk_play"))
        self.play.setObjectName("pm_create")
        self.play.setToolTip(t("pmode.walk_play_tip"))
        self.play.clicked.connect(lambda: self.mode.play_walk())
        self.form.addRow(self.play)
        self.go = QtWidgets.QPushButton(t("pmode.walk_go"))
        self.go.setToolTip(t("pmode.walk_go_tip"))
        self.go.clicked.connect(self._go)
        self.form.addRow(self.go)
        self.empty = self.note("pmode.walk_no_rooms")
        self.note("pmode.walk_shown_note")
        self.fields = (self.start, self.dwell, self.tour, self.play, self.go)

    def _go(self):
        item = self.tour.currentItem()
        if item is not None and item.data(KEY):
            self.mode.play_walk(item.data(KEY))

    def _ticked(self, item):
        """A room ticked (in the walk) or not (left out)."""
        if self.showing or not item.data(KEY):
            return
        _start, off, _dwell = pm.walk_options(self.mode.doc)
        off = set(off)
        if item.checkState() == QtCore.Qt.CheckState.Checked:
            off.discard(item.data(KEY))
        else:
            off.add(item.data(KEY))
        self.mode.set_option(walk_off=sorted(off))

    def show_scene(self, _scene):
        self.showing = True
        try:
            mode = self.mode
            options, rooms = mode.options(), mode.room_count()
            on = bool(options.get("walk", True))
            self.box.setChecked(on)
            self.box.setText(t("present.walk") + (" ({})".format(rooms) if rooms else ""))
            self.box.setEnabled(bool(rooms))
            sp = mode.walk_data() if rooms else {"rooms": [], "tour": [], "start": None}
            names = mode.walk_names() if rooms else {}
            chosen, off, dwell = pm.walk_options(mode.doc)
            from ..model import presentation_walk
            n_rooms, n_doors, n_stairs = presentation_walk.counts(sp) if rooms else (0, 0, 0)
            self.counts.setText(t("pmode.walk_counts", rooms=n_rooms, doors=n_doors, stairs=n_stairs))
            self.start.clear()
            usual = presentation_walk.start_of(sp, "", off)
            self.start.addItem(t("pmode.walk_start_auto", name=names.get(usual, ("—", ""))[0]), "")
            for r in sp["rooms"]:
                if r["id"] not in off:
                    self.start.addItem(names[r["id"]][0], r["id"])
            self.start.setCurrentIndex(max(self.start.findData(chosen), 0))
            self.dwell.setValue(dwell)
            self.tour.clear()
            tour, loose = presentation_walk.tour(sp, sp.get("start"), off) if sp["rooms"] else ([], [])
            listed = [(k + 1, rid) for k, rid in enumerate(tour)] + [(None, rid) for rid in loose] \
                + [(None, r["id"]) for r in sp["rooms"] if r["id"] in off]
            for number, rid in listed:
                name, storey = names.get(rid, (rid, ""))
                marks = [storey] if storey else []
                if rid == sp.get("start"):
                    marks.append(t("pmode.walk_start_mark"))
                elif rid in loose:
                    marks.append(t("pmode.walk_loose"))
                text = "{}{}{}".format("{}. ".format(number) if number else "", name,
                                       "  —  " + " · ".join(marks) if marks else "")
                item = QtWidgets.QListWidgetItem(text)
                item.setData(KEY, rid)
                item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.CheckState.Unchecked if rid in off else QtCore.Qt.CheckState.Checked)
                self.tour.addItem(item)
            playing = mode.playing == "walk"
            self.play.setText(t("present.stop" if playing else "pmode.walk_play"))
            for w in self.fields:
                w.setEnabled(on and bool(sp["rooms"]))
            self.play.setEnabled((on and len(tour) > 1) or playing)
            self.empty.setVisible(not rooms)
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
        self.pages = {"layers": LayersPage(mode), "scenes": ScenesPage(mode), "cuts": CutsPage(mode),
                      "environment": EnvironmentPage(mode),
                      "diagrams": presentation_diagrams.DiagramsPage(mode),           # (0.487; in the rail's order)
                      "labels": presentation_labels.LabelsPage(mode),                 # (0.485)
                      "images": ImagesPage(mode), "effects": EffectsPage(mode),
                      "walk": WalkPage(mode)}                                            # (0.488)
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
        self.pages["diagrams"].restyle()
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
        self.mode.apply_walk()                            # (0.488: its zones and ways seen only in its tab)

    def show_scene(self, scene):
        """The pages of the scene chosen (the one in view: the others when they are chosen)."""
        if self.tab != "layers":
            self.pages[self.tab].show_scene(scene)


# ------------------------------------------------------------------ (0.481) as the Presentation's new 3D page
# (its docs/PLANO-LIMPAR-TELA-3D.md: «nada no centro do viewport»): the camera in one line on the strip over the 3D view
# — here the BIM's parameters' bar —, «Renderizado · Auto» and the sun on the footer, the scenes' player under the 3D
# view, «+ Criar cena» on the left column's foot; the 3D view keeps the BIM's own view cube (the owner: «o cubo de
# navegação devia continuar o mesmo do programa»)

class CameraStrip(QtWidgets.QWidget):
    """The Presentation's camera in one line: PERSP / ORTO · FOV · Enquadrar modelo · Enquadrar selecção · Bloquear —
    at the right end of the parameters' bar (the Presentation's strip over its 3D view, in a wide window)."""

    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.setObjectName("pm_strip")
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(4, 0, 4, 0)
        row.setSpacing(2)
        self.persp = self._button(t("pmode.persp_short").upper(), "pmode.persp_tip", lambda: mode.set_ortho(False))
        self.ortho = self._button(t("pmode.ortho_short").upper(), "pmode.ortho_tip", lambda: mode.set_ortho(True))
        for b in (self.persp, self.ortho):
            b.setCheckable(True)
            row.addWidget(b)
        row.addSpacing(8)
        self.fov_label = QtWidgets.QLabel(t("pmode.fov"))
        self.fov_label.setObjectName("pm_strip_label")
        row.addWidget(self.fov_label)
        self.fov_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.fov_slider.setRange(int(pm.FOV_MIN), int(pm.FOV_MAX))
        self.fov_slider.setFixedWidth(80)
        self.fov_slider.setToolTip(t("pmode.fov_tip"))
        self.fov_slider.valueChanged.connect(self._fov)
        row.addWidget(self.fov_slider)
        self.fov_value = QtWidgets.QLabel(str(int(pm.FOV_DEFAULT)))
        self.fov_value.setObjectName("pm_strip_label")
        self.fov_value.setMinimumWidth(20)
        row.addWidget(self.fov_value)
        row.addSpacing(6)
        self.frame_model = self._button("", "pmode.frame_model", mode.frame_model)
        self.frame_selection = self._button("", "pmode.frame_selection", mode.frame_selection)
        self.lock = self._button("", "pmode.lock_tip", mode.toggle_lock)
        self.lock.setCheckable(True)
        for b in (self.frame_model, self.frame_selection, self.lock):
            row.addWidget(b)
        self.restyle()

    def _button(self, text, tip, call):
        button = QtWidgets.QToolButton()
        button.setText(text)
        button.setToolTip(t(tip))
        button.setAutoRaise(True)
        button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda _on=False: call())
        return button

    def restyle(self):
        self.setStyleSheet(_css())
        self.frame_model.setIcon(_icon("expand", "text", 15))
        self.frame_selection.setIcon(_icon("focus", "text", 15))
        self.show_state()

    def show_state(self):
        """As the camera is now: its projection, its lens (in perspective only), the lock; «Enquadrar selecção» only
        with something selected."""
        mode = self.mode
        ortho = mode.vp.is_ortho()
        self.persp.setChecked(not ortho)
        self.ortho.setChecked(ortho)
        locked = mode.live["locked"]
        self.lock.setChecked(locked)
        self.lock.setIcon(_icon("lock" if locked else "unlock", "accent_text" if locked else "text", 15))
        self.lock.setToolTip(t("pmode.unlock_tip" if locked else "pmode.lock_tip"))
        self.frame_selection.setEnabled(bool(mode.vp.selection))
        for w in (self.fov_label, self.fov_slider, self.fov_value):
            w.setVisible(not ortho)
        self.fov_slider.blockSignals(True)
        self.fov_slider.setValue(int(round(mode.current_fov())))
        self.fov_slider.blockSignals(False)
        self.fov_value.setText(str(self.fov_slider.value()))

    def _fov(self, value):
        self.fov_value.setText(str(value))
        self.mode.set_fov(float(value))


class FooterLook(QtWidgets.QToolButton):
    """«Renderizado · Auto ▾» at the footer's left, as the Presentation's: its menu opens upwards — the visual mode,
    the quality, the ambient occlusion and its strength, «Aplicar a todas as cenas»."""

    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.setObjectName("pm_footer")
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setAutoRaise(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setToolTip(t("pmode.look_tip"))
        self.menu_ = QtWidgets.QMenu(self)
        self.clicked.connect(self._open)
        self.hide()

    def restyle(self):
        self.setStyleSheet(_css())
        self.setIcon(_icon("palette", "accent", 15))
        self.show_state()

    def show_state(self):
        self.setText(self.mode.look_text() + "  ▾")

    def fill(self):
        mode, menu = self.mode, self.menu_
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
        return menu

    def _open(self):
        from . import menus
        menu = self.fill()
        menu.exec(menus.above(menu, self, x=0))           # (up from the footer, as the Presentation's)


class FooterSun(QtWidgets.QToolButton):
    """The sun's reading at the footer's right, as the Presentation's: «☀ 12:00  Az 199°  Alt 74°» — a click: the
    Ambiente tab, where it is set."""

    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.setObjectName("pm_footer")
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setAutoRaise(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setToolTip(t("pmode.sun_tip"))
        self.clicked.connect(lambda: mode.side.show_tab("environment"))
        self.hide()

    def restyle(self):
        self.setStyleSheet(_css())
        self.setIcon(_icon("sun", "attention", 15))
        self.show_state()

    def show_state(self):
        self.setText(self.mode.sun_text())


class ScenePlayer(QtWidgets.QFrame):
    """The scenes' player under the 3D view, as the Presentation's (in its timeline's line): ‹ ▶ 1/4 · Vista geral › —
    the scene before / after in the presentation's sequence (those shown), or all of them one after the other, each
    reached as it is (a smooth flight or a cut) and kept its time on screen."""

    STAY = 4.0                  # s on a scene with no time of its own (the Presentation's)

    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.setObjectName("pm_player")
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(10, 3, 10, 3)
        row.setSpacing(4)
        self.prev = self._button("‹", "pmode.prev_scene", lambda: mode.step_scene(-1))
        self.play = self._button("", "pmode.play_scenes", self.toggle)
        self.next = self._button("›", "pmode.next_scene", lambda: mode.step_scene(1))
        self.label = QtWidgets.QLabel("")
        self.label.setObjectName("pm_player_label")
        self.label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Preferred)
        for w in (self.prev, self.play, self.next):
            row.addWidget(w)
        row.addWidget(self.label, 1)
        self.time = QtWidgets.QLabel("")
        self.time.setObjectName("pm_player_time")
        row.addWidget(self.time)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._on)
        self.playing = False
        self.hide()

    def _button(self, text, tip, call):
        button = QtWidgets.QToolButton()
        button.setText(text)
        button.setToolTip(t(tip))
        button.setAutoRaise(True)
        button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda _on=False: call())
        return button

    def restyle(self):
        self.setStyleSheet(_css())
        self.show_state()

    def show_state(self):
        mode = self.mode
        shown = [s for s in mode.scenes() if not s.hidden]
        keys = [s.key for s in shown]
        scene = mode.scene()
        k = keys.index(scene.key) + 1 if scene is not None and scene.key in keys else 0
        self.label.setText("{}/{} · {}".format(k, len(keys), scene.name) if scene is not None else
                           t("pmode.no_scenes"))
        stay = (scene.seconds or self.STAY) if scene is not None else 0.0
        self.time.setText(t("pmode.scene_time", s="{:.1f}".format(stay).replace(".", ",")) if scene else "")
        self.play.setIcon(_icon("pause" if self.playing else "play", "text", 14))
        self.play.setToolTip(t("pmode.pause_scenes" if self.playing else "pmode.play_scenes"))
        for b in (self.prev, self.next, self.play):
            b.setEnabled(len(keys) > 1 or (b is self.play and self.playing))

    def toggle(self):
        """▶: the scenes one after the other (from the one chosen); ❚❚: stopped where it is."""
        if self.playing:
            self.stop()
            return
        self.playing = True
        self._wait()
        self.show_state()

    def stop(self):
        self.playing = False
        self.timer.stop()
        self.show_state()

    def _wait(self):
        scene = self.mode.scene()
        if scene is None:
            self.stop()
            return
        stay = scene.seconds or self.STAY
        if scene.effect != "none" and scene.effect_auto:      # (0.486: its effect played to its end first)
            stay = max(stay, scene.effect_s)
        self.timer.start(int(1000 * (stay + (scene.transition_s if scene.transition != "cut" else 0.0))))

    def _on(self):
        if not self.playing or not self.mode.active:
            self.stop()
            return
        if not self.mode.step_scene(1, wrap=False):
            self.stop()
            return
        self._wait()
        self.show_state()


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
                     "locked": False, "ortho": False, "cuts": [],      # (0.484: [[type, position, flipped]])
                     "hidden_tags": set(),                             # (0.485: the labels' eyes)
                     "cut_look": "material", "cut_colour": "#1f1f1f"}  # (0.491: how the cuts are filled)
        self.tag_key = None                 # (0.485) the label chosen (its editor open in «Etiquetas»)
        self.label_placement = None         # (0.485) how the next one is put (Piso, Parede, Em pé, Chamada)
        self._tags_drawn = None             # (what the 3D view shows of them: drawn again only when it changed)
        self.diagram_key = None             # (0.487) the volume chosen in «Diagramas» (its editor open)
        self._diagrams_drawn = None
        self._walk_data = None              # (0.488) the walk as it goes (worked out again after each change)
        self._walk_drawn = False
        self._put_aside = None              # the BIM's panels hidden while the tab is in front, and their widths
        self._layers_stale = True
        self._entered_once = False
        self.came_from = None               # (0.481) the view it was opened from: shown again when it is put away
        self.pages = PagesPanel(self, win)
        self.side = SidePanel(self, win)
        win.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.pages)
        win.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.side)
        self.pages.hide()
        self.side.hide()
        # (0.481) as the Presentation's new page: the camera on the parameters' bar, the look and the sun on the footer,
        # the scenes' player under the 3D view (nothing over the model)
        self.camera = CameraStrip(self)
        self.act_camera = QtWidgets.QWidgetAction(self)                 # (kept: the bar only borrows its widget)
        self.act_camera.setDefaultWidget(self.camera)
        self.look_button = FooterLook(self)
        self.sun_button = FooterSun(self)
        bar = win.statusBar()
        bar.insertWidget(0, self.look_button)
        bar.insertPermanentWidget(0, self.sun_button)
        self.player = ScenePlayer(self)
        win._central_layout.addWidget(self.player)
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
        its size), its camera on the parameters' bar, its look and sun on the footer, its scenes' player under the 3D
        view, the scene chosen (the first one, the first time)."""
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
        self.vp.camera_locked = self.live["locked"]
        self.vp.set_hidden_elements(self.live["hidden"])
        self.apply_cuts()
        self.apply_tags()                                  # (0.485)
        self.apply_diagrams()                              # (0.487)
        if self.scene_key is None or self.scene(self.scene_key) is None:
            self.scene_key = pm.initial(self.doc)
        for w in (self.look_button, self.sun_button, self.player):
            w.show()
        self.refresh(layers=True)
        win.refresh_context_bar()
        if hasattr(win, "_presentation_module"):          # (0.480: its icon lit in the left bar)
            win._presentation_module(True)
        if not self._entered_once:                         # (the tab's camera: the first scene's, the first time)
            self._entered_once = True
            QtCore.QTimer.singleShot(0, lambda: self.activate(self.scene_key) if self.active else None)

    def leave(self):
        """Another tab: the BIM's columns again as they were, every element drawn, the mouse free."""
        if not self.active:
            return
        if self.placing():                                # (0.485: a label being put: given up)
            self.win.set_tool("select")
        if self.playing == "effect":                      # (0.486: the model whole again)
            self.win.stop_scene_move()
        self.active = False
        self.player.stop()
        for w in (self.look_button, self.sun_button, self.player):
            w.hide()
        self.vp.set_hidden_elements(set())
        self.apply_cuts()                                 # (0.484: the BIM's 3D view whole; 0.491: its own cut look)
        self.apply_tags()                                 # (0.485: none)
        self.apply_diagrams()                             # (0.487: none)
        self.apply_walk()                                 # (0.488: none)
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
        self.live.update(hidden=set(), style="", quality="auto", ao=True, ao_intensity=1.0, locked=False, cuts=[],
                         hidden_tags=set(), cut_look="material", cut_colour="#1f1f1f")
        self.tag_key = None
        self._tags_drawn = None
        self.diagram_key = None
        self._diagrams_drawn = None
        self._walk_data = None
        self._entered_once = False
        self.came_from = None
        self._layers_stale = True
        if self.active:
            self.vp.set_hidden_elements(set())
            self.apply_cuts()
            self.vp.camera_locked = False
            self.apply_tags()
            self.apply_diagrams()

    def restyle(self):
        self.pages.restyle()
        self.side.restyle()
        for w in (self.camera, self.look_button, self.sun_button, self.player):
            w.restyle()
        if self.active:
            self.refresh(layers=False)

    def show_state(self):
        """(0.481) The camera's buttons, the footer's look and sun, the player — as they are now."""
        for w in (self.camera, self.look_button, self.sun_button, self.player):
            w.show_state()

    def refresh(self, layers=None, changed=None, removed=None):
        """The columns again (the project changed): the pages and the scenes; the layers when elements changed."""
        self._walk_data = None                            # (0.488: worked out again when it is asked for)
        if not self.active or self.doc.loading:
            if layers or changed is None or removed or any(self.doc.get(i) is not None for i in (changed or ())
                                                           if isinstance(i, str)):
                self._layers_stale = True
            return
        if self.scene(self.scene_key) is None:
            self.scene_key = pm.initial(self.doc)
        known = {g["id"] for g in self.tags()}            # (0.485: an undo may take a label back)
        self.live["hidden_tags"] &= known
        if self.tag_key not in known:
            self.tag_key = None
        self.apply_tags()
        if self.diagram(self.diagram_key) is None:        # (0.487: the scene's volumes, as they are now)
            self.diagram_key = None
        self.apply_diagrams()
        self.apply_walk()                                 # (0.488)
        if layers is None:
            layers = changed is None or bool(removed) or any(isinstance(i, str) and self.doc.get(i) is not None
                                                             for i in changed)
        if layers and self.playing == "effect":           # (0.486: the model changed: its effect put away)
            self.win.stop_scene_move()
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
        self.show_state()

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
        """The parameters' bar while the tab is in front — the Presentation's strip over its 3D view: its commands,
        and at its right end the camera in one line (0.481)."""
        icon = glyphs.icon("scene", theme.colour("text"), 20)
        return [("title", t("pmode.title"), icon), ("action", self.act_thumbs), ("action", self.act_export),
                ("spacer",), ("action", self.act_camera)]

    def selection_changed(self, ids):
        if self.active:
            self.side.pages["layers"].show_selection(ids)
            self.camera.show_state()

    def set_playing(self, kind):
        self.playing = kind or None
        if self.active:
            self.side.show_scene(self.scene())
            self.apply_walk()                             # (0.488: not over the view while it is walked)

    # ------------------------------------------------------------ the scene chosen

    def activate(self, key, fly=False):
        """A scene chosen (its card clicked): the 3D view as it was kept — its camera, projection and lens, the
        layers it hides, its visual mode, its lock — as the Presentation's «setActiveScene3D». fly: (0.481, the
        scenes' player) reached as the scene is — a smooth flight (the same projection) or a cut."""
        scene = self.scene(key)
        if scene is None:
            return False
        if self.playing == "effect":                      # (0.486: another scene: its effect put away)
            self.win.stop_scene_move()
        self.scene_key = key
        vp = self.vp
        self.live.update(hidden=set(scene.hidden_layers), style=scene.style, quality=scene.quality, ao=scene.ao,
                         ao_intensity=scene.ao_intensity, locked=scene.locked,
                         cuts=[list(c) for c in scene.cuts],                   # (0.484)
                         hidden_tags=set(scene.hidden_tags),                   # (0.485)
                         cut_look=scene.cut_look, cut_colour=scene.cut_colour)  # (0.491)
        ortho = self.ortho_of(scene)
        vp.camera_locked = False                          # (placed by the program, not the mouse)
        self.apply_cuts()
        self.apply_tags()
        if self.diagram(self.diagram_key) is None:        # (0.487: its own volumes)
            self.diagram_key = None
        self.apply_diagrams()

        def place():
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

        flight = 0.0
        if fly and scene.transition != "cut" and ortho == vp.is_ortho():
            vp.fly(place, scene.transition_s)             # (0.483: as the Presentation's — its time, its lens too)
            flight = scene.transition_s
        else:
            vp.fly(place, 0)                              # (a cut: there at once)
        if fly and self.player.playing and scene.effect != "none" and scene.effect_auto:     # (0.486: as entering it
            QtCore.QTimer.singleShot(int(flight * 1000) + 50, lambda k=key: self._auto_effect(k))   # in the tour)
        self.live["ortho"] = ortho
        vp.set_axonometric(ortho)
        vp.camera_locked = self.live["locked"]
        vp.set_hidden_elements(self.live["hidden"])
        self.win._apply_look()
        self.side.pages["layers"].set_hidden(self.live["hidden"])
        self.pages.mark(key)
        self.side.show_scene(scene)
        self.show_state()
        vp.redraw()
        return True

    def step_scene(self, n, wrap=True):
        """(0.481) The scenes' player: the scene before (n = −1) or after (n = 1) in the presentation's sequence (those
        shown), reached as it is; past the last (wrap False): none — returns whether one was."""
        sequence = [s.key for s in self.scenes() if not s.hidden]
        if not sequence:
            return False
        k = sequence.index(self.scene_key) if self.scene_key in sequence else (-1 if n > 0 else 0)
        k += n
        if not 0 <= k < len(sequence):
            if not wrap:
                return False
            k %= len(sequence)
        return self.activate(sequence[k], fly=True)

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
                  "ao_intensity": self.live["ao_intensity"], "hidden_layers": sorted(self.live["hidden"]),
                  "cuts": [tuple(c) for c in self.live["cuts"]],                # (0.484)
                  "cut_look": self.live["cut_look"], "cut_colour": self.live["cut_colour"],   # (0.491)
                  "hidden_tags": [g["id"] for g in self.tags() if g["id"] in self.live["hidden_tags"]]}   # (0.485)
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
        self.show_state()
        self.pages.show_all()

    def set_fov(self, vertical):
        """The FOV (the Presentation's 20–65°): the lens changed, the camera moved so that what is at the focus stays
        as big (as the Presentation's dolly zoom)."""
        vp = self.vp
        if vp.is_ortho() or self.live["locked"]:
            self.camera.show_state()
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
        self.camera.show_state()
        self.win.message(t("pmode.locked" if self.live["locked"] else "pmode.unlocked"))

    def set_style(self, name):
        """A visual mode of «Renderizado · Auto» (seen in the 3D view with the BIM's style most like it); with
        «Aplicar a todas as cenas», every scene's at once."""
        self.live["style"] = name if name in pm.STYLES else ""
        self.win._apply_look()
        if self.apply_all:
            self._to_all(style=self.live["style"])
        self.show_state()

    def set_look(self, **fields):
        """The quality, the ambient occlusion and its strength (they go to the Presentation; the BIM's view does not
        show them)."""
        for name in ("quality", "ao", "ao_intensity"):
            if name in fields:
                self.live[name] = fields[name]
        if self.apply_all:
            self._to_all(**{k: self.live[k] for k in fields if k in self.live})
        self.show_state()

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

    # ------------------------------------------------------------ (0.484) the cuts (the right column's «Cortes»)

    def cut_range(self, kind):
        """Where a plane of that kind may go: the model's extent along its axis, half a metre beyond each side."""
        axis = {"horizontal": 2, "transversal": 0, "longitudinal": 1}[kind]
        box = self.vp.bounds()
        if box is None:
            return -10.0, 10.0
        return round(float(box[0][axis]) - 0.5, 2), round(float(box[1][axis]) + 0.5, 2)

    def apply_cuts(self):
        """The planes seen now on the 3D view (none when the tab is put away) — (0.491) filled as chosen (the BIM's 3D
        view's own: the materials' hatches)."""
        self.vp.set_cut_look(*((self.live["cut_look"], self.live["cut_colour"]) if self.active else
                               ("material", "#1f1f1f")))
        self.vp.set_cuts([pm.cut_plane(*c) for c in self.live["cuts"]] if self.active else [])

    def set_cut_look(self, look):
        """(0.491) ASPETO DO CORTE: Material, Poché, Sólido, Aberto (live, kept in the scene with Criar / Atualizar)."""
        if look in pm.CUT_LOOKS:
            self.live["cut_look"] = look
            self.apply_cuts()
            self.side.show_scene(self.scene())

    def set_cut_colour(self, colour):
        text = str(colour or "").lower()
        if len(text) == 7 and text.startswith("#"):
            self.live["cut_colour"] = text
            self.apply_cuts()
            self.side.show_scene(self.scene())

    def add_cut(self, kind):
        """A plane more: a horizontal one at the height a plan cuts (1,20 m over the lowest floor), a vertical one
        through the middle of the model."""
        if len(self.live["cuts"]) >= pm.MAX_CUTS:
            return None
        lo, hi = self.cut_range(kind)
        if kind == "horizontal":
            from ..model import view_templates
            levels = [z for _g, _n, z in self.doc.storeys()]
            position = min(max((min(levels) if levels else lo + 0.5) + view_templates.CUT_HEIGHT, lo), hi)
        else:
            position = (lo + hi) / 2.0
        self.live["cuts"].append([kind, round(position, 2), False])
        self.apply_cuts()
        self.side.show_tab("cuts")
        return len(self.live["cuts"]) - 1

    def move_cut(self, k, position):
        if 0 <= k < len(self.live["cuts"]):
            self.live["cuts"][k][1] = round(float(position), 3)
            self.apply_cuts()

    def flip_cut(self, k, on):
        if 0 <= k < len(self.live["cuts"]):
            self.live["cuts"][k][2] = bool(on)
            self.apply_cuts()

    def remove_cut(self, k):
        if 0 <= k < len(self.live["cuts"]):
            del self.live["cuts"][k]
            self.apply_cuts()
            self.side.show_scene(self.scene())

    # ------------------------------------------------------------ (0.488) the Virtual Walk («Passeio»)

    def walk_data(self):
        """The rooms, doors and stairs as they go to the Presentation, with the walk's start, rooms left out and guided
        tour (presentation_export.spaces, in the GLB's axes without offset) — worked out once a change."""
        if self._walk_data is None:
            from ..model import presentation_export
            self._walk_data = presentation_export.spaces(self.doc, (0.0, 0.0, 0.0))
        return self._walk_data

    def walk_names(self):
        storeys = {g: n for g, n, _z in self.doc.storeys()}
        return {r["id"]: (r["name"] or r["number"] or t("pmode.walk_room"), storeys.get(r.get("storey"), ""))
                for r in self.walk_data()["rooms"]}

    def apply_walk(self):
        """The walk's zones (the start in the «good» colour, those left out greyed) and its ways through the doors and
        up the stairs, over the 3D view while the Passeio tab is open (not while it is walked)."""
        from ..model import presentation_walk
        shown = self.active and self.side.tab == "walk" and self.playing != "walk" \
            and bool(self.options().get("walk", True))
        if not shown:
            if self._walk_drawn:
                self._walk_drawn = False
                self.vp.set_walk()
            return
        sp = self.walk_data()
        _start, off, _dwell = pm.walk_options(self.doc)
        zones = []
        for r in sp["rooms"]:
            outline = [(x, -z, r["level"]) for x, z in r["outline"]]
            key = "good" if r["id"] == sp["start"] else "neutral" if r["id"] in off else "accent"
            zones.append((outline, theme.colour(key).name(), 0.38 if key != "neutral" else 0.2))
        ways, seen = [], set()
        for a, legs in presentation_walk.links(sp, off).items():
            for b, pts in legs:
                if (b, a) in seen:
                    continue
                seen.add((a, b))
                ways.append(([presentation_walk.to_model(p) for p in pts], theme.colour("accent").name(), 2.5))
        self.vp.set_walk(zones, ways)
        self._walk_drawn = True

    def play_walk(self, room=None):
        """«Percorrer a visita guiada» (room None) or «Ir até ao escolhido»: the camera walking the way at a person's
        eye, as the Presentation will (again: stopped, the camera back)."""
        from ..model import presentation_walk
        sp = self.walk_data()
        _start, off, dwell = pm.walk_options(self.doc)
        rooms = sp["tour"] if room is None else [sp["start"], room]
        frames = presentation_walk.frames(sp, [r for r in rooms if r], off, fps=self.win.MOVE_FPS, dwell=dwell)
        frames = [(presentation_walk.to_model(e), presentation_walk.to_model(g)) for e, g in frames]
        names = self.walk_names()
        message = t("info.walk_playing", n=len(rooms), v="1,4") if room is None else \
            t("info.walk_to", name=names.get(room, ("", ""))[0])
        return self.win.play_walk(frames, message)

    # ------------------------------------------------------------ (0.487) the volumes for diagrams («Diagramas»)

    def diagrams(self, scene=None):
        """The scene's volumes (the one chosen's by default)."""
        scene = scene if scene is not None else self.scene()
        return list(scene.diagrams) if scene is not None else []

    def diagram(self, d_id):
        return next((d for d in self.diagrams() if d["id"] == d_id), None) if d_id else None

    def _keep_diagrams(self, items, label):
        """The scene chosen's volumes these: one undo step."""
        if self.scene() is None:
            return False
        self.doc.set_presentation(pm.changed(self.doc.presentation, self.scene_key, diagrams=list(items)), t(label))
        self.refresh(layers=False)
        return True

    def add_diagram(self, kind):
        """«Criar volume»: a box, cylinder, sphere, cone or plane beside the model (the Presentation's createDiagram),
        chosen. One undo step."""
        items = self.diagrams()
        if self.scene() is None:
            return None
        if len(items) >= diagrams_model.MAX:
            self.win.message(t("pmode.dia_full", n=diagrams_model.MAX), warning=True)
            return None
        box = self.vp.bounds()
        d = diagrams_model.new(kind, items, box[0] if box is not None else None, box[1] if box is not None else None,
                               base=t("pmode.dia_shape." + kind))
        self.diagram_key = d["id"]
        if self.side.tab != "diagrams":
            self.side.show_tab("diagrams")
        self._keep_diagrams(items + [d], "pmode.cmd_dia_add")
        self.win.message(t("pmode.dia_put", name=d["name"]))
        return d["id"]

    def update_diagram(self, d_id, **fields):
        """A volume's fields changed (its editor, its eye, its lock) — a locked one only unlocked. One undo step."""
        d = self.diagram(d_id)
        if d is None or (d["locked"] and set(fields) - {"locked"}):
            return False
        changed = diagrams_model.clean(dict(d, **fields))
        if changed is None or changed == d:
            return False
        return self._keep_diagrams(diagrams_model.with_one(self.diagrams(), changed), "pmode.cmd_dia")

    def remove_diagram(self, d_id):
        d = self.diagram(d_id)
        if d is None or d["locked"]:
            return False
        if self.diagram_key == d_id:
            self.diagram_key = None
        self._keep_diagrams(diagrams_model.without(self.diagrams(), d_id), "pmode.cmd_dia_remove")
        self.win.message(t("pmode.dia_removed", name=d["name"]))
        return True

    def duplicate_diagram(self, d_id):
        d = self.diagram(d_id)
        items = self.diagrams()
        if d is None or len(items) >= diagrams_model.MAX:
            return None
        copy_ = diagrams_model.duplicate(d, items, t("pmode.copy_word"))
        self.diagram_key = copy_["id"]
        self._keep_diagrams(items + [copy_], "pmode.cmd_dia_dup")
        return copy_["id"]

    def choose_diagram(self, d_id):
        """A volume chosen in the list (its editor, its outline in the 3D view), or none."""
        self.diagram_key = d_id if self.diagram(d_id) is not None else None
        self.apply_diagrams()
        self.side.show_scene(self.scene())

    def frame_diagrams(self, ids=None):
        """«Enquadrar volumes» / «Focar volume»: those shown in view (the direction of view kept)."""
        items = [d for d in self.diagrams() if ids is None or d["id"] in ids]
        box = diagrams_model.bounds(items)
        if box is not None:
            self.vp.zoom_box(box)
        return box is not None

    def apply_diagrams(self):
        """The scene chosen's volumes on the 3D view (those shown), the one chosen outlined; none when the tab is put
        away. Drawn again only when they changed."""
        if not self.active:
            if self._diagrams_drawn is not None:
                self._diagrams_drawn = None
                self.vp.set_diagrams([])
            return
        items = [d for d in self.diagrams() if d["visible"]]
        chosen = self.diagram(self.diagram_key)
        key = repr((items, chosen if chosen is not None and chosen["visible"] else None))
        if key == self._diagrams_drawn:
            return
        self._diagrams_drawn = key
        draw = []
        for d in items:
            points, normals, triangles = diagrams_model.shape(d)
            draw.append((points, normals, triangles, d["color"], d["opacity"], d["wireframe"]))
        outline = diagrams_model.outline(chosen) if chosen is not None and chosen["visible"] else ()
        self.vp.set_diagrams(draw, outline, theme.colour("accent").name())

    # ------------------------------------------------------------ (0.486) the effects (the right column's «Efeitos»)

    def effect_units(self):
        """The model's elements as the Presentation's layers will be, in the order of the GLB's nodes (by storey, then
        category, as gltf_export.build puts them): ([{id, name, category («Paredes · Piso 0»), low, high, centre}] —
        those drawn here, their boxes from their pieces —, the whole model's middle, half its box's diagonal)."""
        from ..model import gltf_export
        bim = self.vp.bim
        storeys = {g: n for g, n, _z in self.doc.storeys()}
        tree, lows, highs = {}, [], []
        for obj in self.doc.objects.values():
            if not obj.is_bim or obj.mesh is None or obj.ifc_class in gltf_export.SKIP:
                continue
            batch = bim.where.get(obj.id)
            piece = batch.pieces.get(obj.id) if batch is not None else None
            if piece is None or not len(piece.positions):
                continue
            low, high = piece.positions.min(axis=0).astype(float), piece.positions.max(axis=0).astype(float)
            lows.append(low)
            highs.append(high)
            storey = storeys.get(obj.storey) or t("gltf.no_storey")
            category = gltf_export._category(obj.ifc_class)
            tree.setdefault(storey, {}).setdefault(category, []).append(
                {"id": obj.id, "name": obj.name or obj.id, "category": " · ".join(c for c in (category, storey) if c),
                 "low": tuple(low), "high": tuple(high), "centre": tuple((low + high) / 2.0)})
        units = [u for categories in tree.values() for members in categories.values() for u in members]
        if not units:
            return [], (0.0, 0.0, 0.0), 0.5
        lo, hi = np.min(lows, axis=0), np.max(highs, axis=0)
        return units, tuple((lo + hi) / 2.0), max(float(np.linalg.norm(hi - lo)) / 2.0, 0.5)

    def effect_moves(self, scene):
        """How each element moves in the scene's effect (model/presentation_effects.plan): those drawn now take part
        — not those whose eye is off, nor (a construction) those taken out of it."""
        from ..model import presentation_effects
        units, centre, radius = self.effect_units()
        left_out = set(self.live["hidden"]) | (set(scene.effect_static) if scene.effect == "construction" else set())
        return presentation_effects.plan(scene.effect, [u for u in units if u["id"] not in left_out], centre, radius,
                                         scene.effect_spread)

    def play_effect(self, key=None):
        """«Pré-visualizar»: the scene's effect played in the 3D view as the Presentation will play it (again: stopped)."""
        return self.win.play_scene_effect(key or self.scene_key)

    def _auto_effect(self, key):
        """(the scenes' player) A scene reached with an effect played when it is entered: played, after its flight."""
        if self.active and self.player.playing and self.scene_key == key:
            self.win.play_scene_effect(key)

    # ------------------------------------------------------------ (0.485) the labels (the right column's «Etiquetas»)

    def tags(self):
        return pm.tags(self.doc)

    def tag(self, tag_id):
        return next((g for g in self.tags() if g["id"] == tag_id), None) if tag_id else None

    def placing(self):
        """How a label is being put (the label tool in use), or None."""
        tool = getattr(self.win, "tool", None)
        return self.label_placement if tool is not None and tool.name == "pres_label" else None

    def show_placing(self, on=True):
        """The tile of the placement being put pressed, the step said (on False: the tool is being put away)."""
        self.side.pages["labels"].show_placing(self.placing() if on else None)

    def start_label(self, placement):
        """Piso / Parede / Em pé / Chamada: the next click on the model puts a label so (the same again: none)."""
        if self.placing() == placement:
            self.win.set_tool("select")
            return
        self.label_placement = placement if placement in presentation_tags.PLACEMENTS else "floor"
        if self.side.tab != "labels":
            self.side.show_tab("labels")
        if self.placing():
            self.show_placing()
        else:
            self.win.set_tool("pres_label")

    def _new_look(self):
        """The look a new label takes: the one chosen's, else the last one put's (as the Presentation's)."""
        tags = self.tags()
        return presentation_tags.look_of(self.tag(self.tag_key) or (tags[-1] if tags else None))

    def _new_tag(self, point, normal):
        return presentation_tags.new_tag(self.label_placement or "floor", tuple(float(c) for c in point),
                                         tuple(float(c) for c in normal), self.tags(), base=t("pmode.tag_word"),
                                         style=self._new_look())

    def label_preview(self, point, normal):
        """Where a label put at that point would be: {"corners", "lines"} (the tool's outline under the cursor)."""
        tag = self._new_tag(point, normal)
        _pixels, aspect = presentation_labels.tag_pixels(tag)
        return presentation_tags.frame(tag, aspect, toward=-self.vp.view_direction())

    def place_label(self, point, normal):
        """A label put on the model at that point of a surface (its normal): «Ambiente N», chosen. One undo step."""
        tags = self.tags()
        if len(tags) >= presentation_tags.MAX_TAGS:
            self.win.message(t("pmode.tag_full", n=presentation_tags.MAX_TAGS), warning=True)
            return None
        tag = self._new_tag(point, normal)
        self.doc.set_presentation(pm.with_tags(self.doc.presentation, tags + [tag]), t("pmode.cmd_tag_add"))
        self.tag_key = tag["id"]
        if self.side.tab != "labels":
            self.side.show_tab("labels")
        self.refresh(layers=False)
        self.win.message(t("pmode.tag_put", name=tag["title"]))
        return tag["id"]

    def update_tag(self, tag_id, **fields):
        """The label's fields changed (its editor). One undo step."""
        tag = self.tag(tag_id)
        if tag is None:
            return False
        changed = presentation_tags.clean_tag(dict(tag, **fields))
        if changed == tag:
            return False
        self.doc.set_presentation(pm.with_tags(self.doc.presentation,
                                               presentation_tags.with_tag(self.tags(), changed)), t("pmode.cmd_tag"))
        self.refresh(layers=False)
        return True

    def remove_tag(self, tag_id):
        """«Apagar»: the label gone from the model (and from what the scenes hide). One undo step."""
        tag = self.tag(tag_id)
        if tag is None:
            return False
        self.live["hidden_tags"].discard(tag_id)
        if self.tag_key == tag_id:
            self.tag_key = None
        self.doc.set_presentation(pm.with_tags(self.doc.presentation, presentation_tags.without(self.tags(), tag_id)),
                                  t("pmode.cmd_tag_remove"))
        self.refresh(layers=False)
        self.win.message(t("pmode.tag_removed", name=tag["title"] or t("pmode.tag_unnamed")))
        return True

    def toggle_tag(self, tag_id):
        """The label's eye (live, as the layers': kept in the scene with «Criar cena» / «Atualizar»)."""
        if self.tag(tag_id) is None:
            return
        hidden = self.live["hidden_tags"]
        if tag_id in hidden:
            hidden.discard(tag_id)
        else:
            hidden.add(tag_id)
        self.apply_tags()
        self.side.show_scene(self.scene())

    def choose_tag(self, tag_id):
        """A label chosen in the list (its editor), or none."""
        self.tag_key = tag_id if self.tag(tag_id) is not None else None
        self.side.show_scene(self.scene())

    def apply_tags(self):
        """The labels seen now on the 3D view — all but those turned off; none when the tab is put away. Drawn again
        only when they changed."""
        if not self.active:
            if self._tags_drawn is not None:
                self._tags_drawn = None
                self.vp.set_tags([])
            return
        shown = [g for g in self.tags() if g["id"] not in self.live["hidden_tags"]]
        key = repr(shown)
        if key == self._tags_drawn:
            return
        self._tags_drawn = key
        toward = -self.vp.view_direction()
        items, looks = [], []
        for tag in shown:
            pixels, aspect = presentation_labels.tag_pixels(tag)
            frame = presentation_tags.frame(tag, aspect, toward)
            items.append((pixels, frame["corners"], frame["lines"], not tag["hide_occluded"]))
            looks.append((tag, aspect))
        follow = None
        if any(g["placement"] == "standing" and g["face_camera"] for g in shown):
            def follow(way):
                frames = (presentation_tags.frame(g, a, way) for g, a in looks)
                return [(f["corners"], f["lines"]) for f in frames]
        self.vp.set_tags(items, follow)

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
