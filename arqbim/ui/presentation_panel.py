"""(0.363) The Presentation panel: the scenes prepared here for the ArqSynth Presentation (model/presentation.py) — in
the presentation's order (dragged, or Up / Down), each with its thumbnail; for the one chosen, whether the presentation
opens on it, whether it is left out of the sequence, how it is reached, its effect, how long it stays and its caption.
The window does the rest (its callables): it keeps what is chosen (one undo step each), opens a scene's view
(double-click), takes the thumbnails and exports. The owner, 2026-11-02: «cenas 3D, cortes, animações, efeitos etc.
podia ser preparada aqui no BIM e depois migrada para a plataforma de apresentação»."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..model import camera_moves
from ..model import presentation as presentation_model
from ..model import presentation_sun
from . import theme

THUMB = QtCore.QSize(80, 45)            # a thumbnail in the list (16:9)
COMBO_CHARS = 10                        # (0.364) the choices' boxes this wide: the panel no wider than the others
KEY = QtCore.Qt.ItemDataRole.UserRole


class _List(QtWidgets.QListWidget):
    """The scenes, dragged into their order (the panel told after a drop)."""

    def __init__(self, panel):
        super().__init__()
        self.panel = panel
        self.setIconSize(THUMB)
        self.setSpacing(2)
        self.setWordWrap(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)

    def dropEvent(self, event):  # noqa: N802
        super().dropEvent(event)
        self.panel._dropped()


class _Caption(QtWidgets.QPlainTextEdit):
    """The caption, kept when it is left (not at every letter: one undo step for the text)."""

    def __init__(self, panel):
        super().__init__()
        self.panel = panel
        self.setTabChangesFocus(True)

    def focusOutEvent(self, event):  # noqa: N802
        super().focusOutEvent(event)
        self.panel._caption_done()


class PresentationPanel(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__(t("present.title"), parent)
        self.setObjectName("presentation")
        self.on_change = None            # callable(key, **fields): a scene's settings changed
        self.on_order = None             # callable([key…]): the scenes in a new order
        self.on_initial = None           # callable(key | None): the scene the presentation opens on
        self.on_open = None              # callable(key): its view shown (double-click)
        self.on_thumbnails = None        # callable(): the thumbnails taken again
        self.on_export = None            # callable(): exported for the Presentation
        self.on_play = None              # callable(key): (0.364) its camera move played in the 3D view (or stopped)
        self.rooms = None                # callable() -> [(GlobalId, its name)]: the rooms an interior move may be in
        self.on_sun = None               # callable(key): (0.365) its sun shown in the 3D view, with shadows (or not)
        self.has_site = None             # callable() -> bool: the site has a place (else no sun of a day and hour)
        self.on_options = None           # callable(**{labels | walk: bool}): (0.366) what goes of the rooms
        self.on_panorama_new = None      # callable(): (0.368) a 360° panorama from the 3D view's camera
        self.on_panorama_remove = None   # callable(uid): a panorama out of the project
        self.playing = None              # what is being played in the 3D view: "move", "sun" or None
        self.scenes = []                 # [presentation.Scene], as shown
        self.initial = None
        self._thumbs = {}                # key -> JPEG bytes
        self._pixmaps = {}               # JPEG bytes -> QPixmap (made once)
        self._showing = False            # the form being filled in (its signals are not the user's)
        page = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(page)
        column.setContentsMargins(4, 4, 4, 4)
        self.hint = QtWidgets.QLabel(t("present.hint"))
        self.hint.setWordWrap(True)
        self.list = _List(self)
        self.list.currentItemChanged.connect(lambda *_: self._show_chosen())
        self.list.itemDoubleClicked.connect(lambda item: self._call(self.on_open, item.data(KEY)))
        row = QtWidgets.QHBoxLayout()
        self.up_button = QtWidgets.QPushButton(t("present.up"))
        self.up_button.clicked.connect(lambda: self._move(-1))
        self.down_button = QtWidgets.QPushButton(t("present.down"))
        self.down_button.clicked.connect(lambda: self._move(1))
        self.thumbs_button = QtWidgets.QPushButton(t("present.thumbs"))
        self.thumbs_button.setToolTip(t("present.thumbs_tip"))
        self.thumbs_button.clicked.connect(lambda: self._call(self.on_thumbnails))
        for b in (self.up_button, self.down_button, self.thumbs_button):
            row.addWidget(b)
        row.addStretch(1)
        self.count = QtWidgets.QLabel("")
        top = QtWidgets.QWidget()                   # (the list over the chosen scene's form: their line dragged)
        upper = QtWidgets.QVBoxLayout(top)
        upper.setContentsMargins(0, 0, 0, 0)
        upper.addWidget(self.list, 1)
        upper.addLayout(row)
        upper.addWidget(self.count)
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(top)
        scroll = QtWidgets.QScrollArea()             # (the form scrolls: on a low screen the list keeps its share)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self._form())
        scroll.setMinimumWidth(self.group.minimumSizeHint().width() + scroll.verticalScrollBar().sizeHint().width() + 4)
        self.splitter.addWidget(scroll)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        column.addWidget(self.hint)
        column.addWidget(self.splitter, 1)
        # (0.366) the rooms: as labels, and as the Virtual Walk (linked by their doors)
        self.labels_box = QtWidgets.QCheckBox(t("present.labels"))
        self.labels_box.setToolTip(t("present.labels_tip"))
        self.labels_box.toggled.connect(lambda on: self._option(labels=on))
        self.walk_box = QtWidgets.QCheckBox(t("present.walk"))
        self.walk_box.setToolTip(t("present.walk_tip"))
        self.walk_box.toggled.connect(lambda on: self._option(walk=on))
        column.addWidget(self.labels_box)
        column.addWidget(self.walk_box)
        # (0.368) the 360° panoramas: kept with the project, sent as 360° points on their storey's plans
        self.panoramas_label = QtWidgets.QLabel(t("present.panoramas"))
        self.panoramas = QtWidgets.QListWidget()
        self.panoramas.setFixedHeight(64)
        self.panoramas.currentItemChanged.connect(lambda *_: self.panorama_remove.setEnabled(
            self.panoramas.currentItem() is not None and self.panoramas.currentItem().data(KEY) is not None))
        row2 = QtWidgets.QHBoxLayout()
        self.panorama_new = QtWidgets.QPushButton(t("present.panorama_new"))
        self.panorama_new.setToolTip(t("tip.panorama"))
        self.panorama_new.clicked.connect(lambda: self._call(self.on_panorama_new))
        self.panorama_remove = QtWidgets.QPushButton(t("present.panorama_remove"))
        self.panorama_remove.setEnabled(False)
        self.panorama_remove.clicked.connect(
            lambda: self._call(self.on_panorama_remove, self.panoramas.currentItem().data(KEY))
            if self.panoramas.currentItem() is not None else None)
        row2.addWidget(self.panorama_new)
        row2.addWidget(self.panorama_remove)
        row2.addStretch(1)
        column.addWidget(self.panoramas_label)
        column.addWidget(self.panoramas)
        column.addLayout(row2)
        self.export_button = QtWidgets.QPushButton(t("present.export"))
        self.export_button.clicked.connect(lambda: self._call(self.on_export))
        column.addWidget(self.export_button)
        self.setWidget(page)
        self.restyle()
        self._show_chosen()

    def _form(self):
        self.group = QtWidgets.QGroupBox(t("present.scene"))
        form = QtWidgets.QFormLayout(self.group)
        form.setContentsMargins(6, 6, 6, 6)
        form.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)    # (narrow: the label above)
        self.none_label = QtWidgets.QLabel(t("present.none"))
        form.addRow(self.none_label)
        self.initial_box = QtWidgets.QCheckBox(t("present.initial"))
        self.initial_box.setToolTip(t("present.initial_tip"))
        self.initial_box.toggled.connect(self._initial_toggled)
        self.hidden_box = QtWidgets.QCheckBox(t("present.hidden"))
        self.hidden_box.setToolTip(t("present.hidden_tip"))
        self.hidden_box.toggled.connect(lambda on: self._changed(hidden=on))
        form.addRow(self.initial_box)
        form.addRow(self.hidden_box)
        self.transition = QtWidgets.QComboBox()
        for name in presentation_model.TRANSITIONS:
            self.transition.addItem(t("present.transition." + name), name)
        self.transition.currentIndexChanged.connect(
            lambda _i: self._changed(transition=self.transition.currentData()))
        self.transition_s = self._seconds(0.0, 10.0, 0.1)
        self.transition_s.valueChanged.connect(lambda v: self._changed(transition_s=v))
        form.addRow(t("present.transition"), self._pair(self.transition, self.transition_s))
        self.effect = QtWidgets.QComboBox()
        for name in presentation_model.EFFECTS:
            self.effect.addItem(t("present.effect." + name), name)
        self.effect.currentIndexChanged.connect(lambda _i: self._changed(effect=self.effect.currentData()))
        self.effect_s = self._seconds(1.0, 60.0, 0.5)
        self.effect_s.valueChanged.connect(lambda v: self._changed(effect_s=v))
        form.addRow(t("present.effect"), self._pair(self.effect, self.effect_s))
        self.move = QtWidgets.QComboBox()                  # (0.364) the camera move, by the Presentation's groups
        self.move.setToolTip(t("present.move_tip"))
        self.move.addItem(t("present.move.none"), "")
        items = self.move.model()
        for category in camera_moves.CATEGORIES:
            self.move.addItem(t("move.cat." + category), None)
            head = items.item(self.move.count() - 1)
            head.setEnabled(False)
            font = head.font()
            font.setBold(True)
            head.setFont(font)
            for move, (cat, *_rest) in camera_moves.MOVES.items():
                if cat == category:
                    self.move.addItem("   " + t("move." + move), move)
        self.move.currentIndexChanged.connect(lambda _i: self._changed(move=self.move.currentData() or ""))
        self.move_s = self._seconds(0.0, 120.0, 1.0)
        self.move_s.valueChanged.connect(lambda v: self._changed(move_s=v))
        form.addRow(t("present.move"), self._pair(self.move, self.move_s))
        self.room = QtWidgets.QComboBox()
        self.room.setToolTip(t("present.room_tip"))
        self.room.currentIndexChanged.connect(lambda _i: self._changed(room=self.room.currentData() or ""))
        form.addRow(t("present.room"), self.room)
        self.play_button = QtWidgets.QPushButton(t("present.play"))
        self.play_button.setToolTip(t("present.play_tip"))
        self.play_button.clicked.connect(lambda: self._call(self.on_play, self.chosen_key()))
        form.addRow("", self.play_button)
        # (0.365) the scene's sun (the site's, on a day at an hour), its animation, the exposure, the sky
        self.sun_date = QtWidgets.QDateEdit()
        self.sun_date.setDisplayFormat("dd/MM")
        self.sun_date.setDateRange(QtCore.QDate(2025, 1, 1), QtCore.QDate(2025, 12, 31))     # (a year without 29/02)
        self.sun_date.setKeyboardTracking(False)
        self.sun_date.dateChanged.connect(
            lambda d: self._changed(sun_day=presentation_sun.day_of(d.month(), d.day())))
        self.sun_time = QtWidgets.QTimeEdit()
        self.sun_time.setDisplayFormat("HH:mm")
        self.sun_time.setKeyboardTracking(False)
        self.sun_time.timeChanged.connect(lambda tm: self._changed(sun_minutes=tm.hour() * 60 + tm.minute()))
        form.addRow(t("present.sun"), self._pair(self.sun_date, self.sun_time))
        self.sun_animate = QtWidgets.QComboBox()
        for name in presentation_model.SUN_ANIMATIONS:
            self.sun_animate.addItem(t("present.sun_animate." + name), name)
        self.sun_animate.setToolTip(t("present.sun_animate_tip"))
        self.sun_animate.currentIndexChanged.connect(
            lambda _i: self._changed(sun_animate=self.sun_animate.currentData()))
        form.addRow(t("present.sun_animate"), self.sun_animate)
        self.exposure = QtWidgets.QDoubleSpinBox()
        self.exposure.setRange(0.3, 1.6)
        self.exposure.setDecimals(2)
        self.exposure.setSingleStep(0.05)
        self.exposure.setKeyboardTracking(False)
        self.exposure.setToolTip(t("present.exposure_tip"))
        self.exposure.valueChanged.connect(lambda v: self._changed(exposure=v))
        form.addRow(t("present.exposure"), self.exposure)
        self.sky = QtWidgets.QCheckBox(t("present.sky"))
        self.sky.setToolTip(t("present.sky_tip"))
        self.sky.toggled.connect(lambda on: self._changed(sky=on))
        form.addRow("", self.sky)
        self.sun_button = QtWidgets.QPushButton(t("present.sun_play"))
        self.sun_button.setToolTip(t("present.sun_play_tip"))
        self.sun_button.clicked.connect(lambda: self._call(self.on_sun, self.chosen_key()))
        form.addRow("", self.sun_button)
        self.sun_note = QtWidgets.QLabel(t("present.no_site"))
        self.sun_note.setWordWrap(True)
        form.addRow(self.sun_note)
        self._form_layout = form
        self.seconds = self._seconds(0.0, 600.0, 1.0)
        self.seconds.setSpecialValueText(t("present.seconds_auto"))
        self.seconds.setToolTip(t("present.seconds_tip"))
        self.seconds.valueChanged.connect(lambda v: self._changed(seconds=v))
        form.addRow(t("present.seconds"), self.seconds)
        self.caption = _Caption(self)
        self.caption.setToolTip(t("present.caption_tip"))
        self.caption.setFixedHeight(64)
        form.addRow(t("present.caption"), self.caption)
        self._fields = (self.initial_box, self.hidden_box, self.transition, self.transition_s, self.effect,
                        self.effect_s, self.move, self.move_s, self.room, self.play_button, self.sun_date,
                        self.sun_time, self.sun_animate, self.exposure, self.sky, self.sun_button, self.seconds,
                        self.caption)
        for box in (self.transition, self.effect, self.move, self.room, self.sun_animate):  # (as narrow as the panel: the
            box.setSizeAdjustPolicy(                                         # long names in the open list only)
                QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            box.setMinimumContentsLength(COMBO_CHARS)
        self.move.view().setMinimumWidth(self.move.view().sizeHintForColumn(0) + 24)
        return self.group

    @staticmethod
    def _seconds(lo, hi, step):
        box = QtWidgets.QDoubleSpinBox()
        box.setRange(lo, hi)
        box.setDecimals(1)
        box.setSingleStep(step)
        box.setSuffix(" s")
        box.setKeyboardTracking(False)              # (a number typed: kept when it is done, not at every digit)
        return box

    @staticmethod
    def _pair(a, b):
        w = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(w)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(a, 1)
        row.addWidget(b)
        return w

    def restyle(self):
        self.hint.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        self.count.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        if hasattr(self, "sun_note"):
            self.sun_note.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        self._pixmaps = {}
        if self.scenes:
            self.show_scenes(self.scenes, self.initial, self._thumbs, getattr(self, "_options", None),
                             getattr(self, "_rooms", 0), getattr(self, "_panoramas", None))

    # ------------------------------------------------------------ shown

    def show_scenes(self, scenes, initial, thumbs=None, options=None, rooms=0, panoramas=None):
        """The scenes (presentation.scenes, in order), the key of the one it opens on and {key: JPEG bytes}: the
        list again, the same scene still chosen; (0.366) the options ({labels, walk}) and how many rooms there are;
        (0.368) the panoramas ([{uid, name}])."""
        self.scenes, self.initial, self._thumbs = list(scenes), initial, dict(thumbs or {})
        self._options, self._rooms, self._panoramas = dict(options or {}), rooms, list(panoramas or ())
        chosen = self.chosen_key()
        self._showing = True
        try:
            picked = self.panoramas.currentItem().data(KEY) if self.panoramas.currentItem() is not None else None
            self.panoramas.clear()
            for p in self._panoramas:
                item = QtWidgets.QListWidgetItem(p["name"])
                item.setData(KEY, p["uid"])
                self.panoramas.addItem(item)
                if p["uid"] == picked:
                    self.panoramas.setCurrentItem(item)
            if not self._panoramas:
                empty = QtWidgets.QListWidgetItem(t("present.panoramas_none"))
                empty.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                self.panoramas.addItem(empty)
            self.panorama_remove.setEnabled(self.panoramas.currentItem() is not None
                                            and self.panoramas.currentItem().data(KEY) is not None)
            options = options or {}
            self.labels_box.setChecked(bool(options.get("labels", True)))
            self.walk_box.setChecked(bool(options.get("walk", True)))
            for box, key in ((self.labels_box, "present.labels"), (self.walk_box, "present.walk")):
                box.setText(t(key) + (" ({})".format(rooms) if rooms else ""))
                box.setEnabled(bool(rooms))
            self.list.clear()
            for k, scene in enumerate(self.scenes):
                marks = [t("present.marks.initial")] if scene.key == initial else []
                if scene.hidden:
                    marks.append(t("present.marks.hidden"))
                text = "{:02d}  {}".format(k + 1, scene.name) + ("\n" + " · ".join(marks) if marks else "")
                item = QtWidgets.QListWidgetItem(QtGui.QIcon(self._pixmap(self._thumbs.get(scene.key))), text)
                item.setData(KEY, scene.key)
                item.setToolTip(scene.name)
                if scene.hidden:
                    item.setForeground(QtGui.QBrush(theme.colour("note")))
                self.list.addItem(item)
                if scene.key == chosen:
                    self.list.setCurrentItem(item)
        finally:
            self._showing = False
        hidden = sum(1 for s in self.scenes if s.hidden)
        self.count.setText(t("present.count", n=len(self.scenes), h=hidden))
        self._show_chosen()

    def _pixmap(self, jpeg):
        if jpeg:
            if jpeg not in self._pixmaps:
                pm = QtGui.QPixmap()
                pm.loadFromData(bytes(jpeg), "JPG")
                self._pixmaps[jpeg] = pm.scaled(THUMB, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                                QtCore.Qt.TransformationMode.SmoothTransformation)
            return self._pixmaps[jpeg]
        pm = QtGui.QPixmap(THUMB)                  # (no thumbnail yet: a plain card)
        pm.fill(theme.colour("panel"))
        return pm

    def chosen_key(self):
        item = self.list.currentItem()
        return item.data(KEY) if item is not None else None

    def chosen(self):
        key = self.chosen_key()
        return next((s for s in self.scenes if s.key == key), None)

    def _show_chosen(self):
        scene = self.chosen()
        self._showing = True
        try:
            self.none_label.setVisible(scene is None)
            for w in self._fields:
                w.setEnabled(scene is not None)
            k = self.list.currentRow()
            self.up_button.setEnabled(scene is not None and k > 0)
            self.down_button.setEnabled(scene is not None and k < self.list.count() - 1)
            if scene is None:
                self._form_layout.setRowVisible(self.room, False)
                self.sun_note.setVisible(False)
                return
            self.initial_box.setChecked(scene.key == self.initial)
            self.hidden_box.setChecked(scene.hidden)
            self.transition.setCurrentIndex(max(self.transition.findData(scene.transition), 0))
            self.transition_s.setValue(scene.transition_s)
            self.transition_s.setEnabled(scene.transition != "cut")
            self.effect.setCurrentIndex(max(self.effect.findData(scene.effect), 0))
            self.effect_s.setValue(scene.effect_s)
            self.effect_s.setEnabled(scene.effect != "none")
            self.move.setCurrentIndex(max(self.move.findData(scene.move), 0))
            own = camera_moves.MOVES[scene.move][2] if scene.move else 0.0
            self.move_s.setSpecialValueText(t("present.move_own", s="{:.0f}".format(own)) if scene.move else "—")
            self.move_s.setValue(scene.move_s)
            self.move_s.setEnabled(bool(scene.move))
            inside = camera_moves.interior(scene.move)
            self._form_layout.setRowVisible(self.room, inside)
            if inside:
                self.room.clear()
                self.room.addItem(t("present.room_auto"), "")
                for guid, name in (self.rooms() if self.rooms else []):
                    self.room.addItem(name, guid)
                self.room.setCurrentIndex(max(self.room.findData(scene.room), 0))
            self.play_button.setEnabled(bool(scene.move) or self.playing == "move")
            self.play_button.setText(t("present.stop" if self.playing == "move" else "present.play"))
            month, day = presentation_sun.month_day(scene.sun_day)
            self.sun_date.setDate(QtCore.QDate(2025, month, day))
            self.sun_time.setTime(QtCore.QTime(scene.sun_minutes // 60, scene.sun_minutes % 60))
            self.sun_animate.setCurrentIndex(max(self.sun_animate.findData(scene.sun_animate), 0))
            self.exposure.setValue(scene.exposure)
            self.sky.setChecked(scene.sky)
            placed = bool(self.has_site()) if self.has_site else True
            for w in (self.sun_date, self.sun_time, self.sun_animate):
                w.setEnabled(placed)
            self.sun_button.setEnabled(placed or self.playing == "sun")
            self.sun_button.setText(t("present.stop" if self.playing == "sun" else "present.sun_play"))
            self.sun_note.setVisible(not placed)
            self.seconds.setValue(scene.seconds)
            if self.caption.toPlainText() != scene.caption:
                self.caption.setPlainText(scene.caption)
        finally:
            self._showing = False

    def set_playing(self, kind):
        """(0.364) What is being played in the 3D view — "move" (a camera move), (0.365) "sun", or None: its button
        stops it."""
        self.playing = kind or None
        self._show_chosen()

    # ------------------------------------------------------------ the user's

    def _call(self, fn, *args, **fields):
        if fn is not None:
            fn(*args, **fields)

    def _changed(self, **fields):
        scene = self.chosen()
        if self._showing or scene is None:
            return
        self._call(self.on_change, scene.key, **fields)

    def _option(self, **options):
        if not self._showing:
            self._call(self.on_options, **options)

    def _initial_toggled(self, on):
        scene = self.chosen()
        if self._showing or scene is None:
            return
        self._call(self.on_initial, scene.key if on else None)

    def _caption_done(self):
        scene = self.chosen()
        text = self.caption.toPlainText().strip()
        if not self._showing and scene is not None and text != scene.caption:
            self._call(self.on_change, scene.key, caption=text)

    def _dropped(self):
        keys = [self.list.item(k).data(KEY) for k in range(self.list.count())]
        if keys != [s.key for s in self.scenes]:
            self._call(self.on_order, keys)

    def _move(self, step):
        k = self.list.currentRow()
        keys = [s.key for s in self.scenes]
        if not 0 <= k < len(keys) or not 0 <= k + step < len(keys):
            return
        keys[k], keys[k + step] = keys[k + step], keys[k]
        self._call(self.on_order, keys)


def dock(parent, beside):
    """The panel as a tab next to `beside` (on the left), hidden until asked for."""
    panel = PresentationPanel(parent)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, panel)
    parent.tabifyDockWidget(beside, panel)
    panel.hide()
    return panel
