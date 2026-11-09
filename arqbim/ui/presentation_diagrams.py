"""(0.487) The Presentation tab's «Diagramas» — the owner: «é importante criar cortes, ter diagramas, etiqueta,
efeitos». As the ArqSynth Presentation's «Volumes para diagramas» (its DiagramPanel): the scene chosen's volumes —
«Criar volume» (Caixa, Cilindro, Esfera, Cone, Plano: beside the model), «Enquadrar volumes», the list with each one's
eye and lock; the one chosen: its name and kind (with its volume), Duplicar · Focar · Bloquear · Remover, «Mostrar volume
nesta cena», its measures and where the middle of its base is, its turn and scale («Repor rotação e escala»), its colour
(the Presentation's five, or any), opacity and lines, its description; «Duplicar cena com estes volumes».

The volumes are the scene's (Scene.diagrams, model/presentation_diagrams.py): each change one undo step, kept at once
(as there — not live until «Atualizar» like the eyes)."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import decimal_sep, t
from ..model import presentation_diagrams as dia
from . import presentation_glyphs as glyphs
from . import theme


def _head(text):
    label = QtWidgets.QLabel(text)
    label.setObjectName("pm_head")
    return label


def _note(text):
    label = QtWidgets.QLabel(text)
    label.setObjectName("pm_note")
    label.setWordWrap(True)
    return label


def _swatch(colour, size=14):
    pm_ = QtGui.QPixmap(size, size)
    pm_.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pm_)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    p.setPen(QtGui.QPen(theme.colour("line"), 1))
    p.setBrush(QtGui.QColor(colour))
    p.drawRoundedRect(QtCore.QRectF(0.5, 0.5, size - 1, size - 1), 3, 3)
    p.end()
    return QtGui.QIcon(pm_)


def _spin(lo, hi, step, decimals=2, suffix=""):
    box = QtWidgets.QDoubleSpinBox()
    box.setRange(lo, hi)
    box.setSingleStep(step)
    box.setDecimals(decimals)
    box.setSuffix(suffix)
    box.setKeyboardTracking(False)
    box.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
    return box


def _number(value):
    return "{:.2f}".format(value).replace(".", decimal_sep())


class _Row(QtWidgets.QFrame):
    """A volume in the list: its colour, its name (a click chooses it), its eye, its lock."""

    def __init__(self, page, d, chosen):
        super().__init__()
        self.setObjectName("pm_card")
        self.setProperty("active", "true" if chosen else "false")
        self.d_id = d["id"]
        mode = page.mode
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(6, 2, 2, 2)
        row.setSpacing(4)
        self.button = QtWidgets.QPushButton(_swatch(d["color"]), d["name"])
        self.button.setObjectName("pm_link")
        self.button.clicked.connect(lambda: mode.choose_diagram(None if chosen else self.d_id))
        row.addWidget(self.button, 1)
        self.eye = QtWidgets.QToolButton()
        self.eye.setObjectName("pm_icon")
        self.eye.setIcon(glyphs.icon("eye" if d["visible"] else "eye_off", theme.colour("muted"), 14))
        self.eye.setToolTip(t("pmode.dia_hide_named" if d["visible"] else "pmode.dia_show_named", name=d["name"]))
        self.eye.setEnabled(not d["locked"])
        self.eye.clicked.connect(lambda: mode.update_diagram(self.d_id, visible=not d["visible"]))
        row.addWidget(self.eye)
        self.lock = QtWidgets.QToolButton()
        self.lock.setObjectName("pm_icon")
        self.lock.setCheckable(True)
        self.lock.setChecked(d["locked"])
        self.lock.setIcon(glyphs.icon("lock" if d["locked"] else "unlock", theme.colour("muted"), 14))
        self.lock.setToolTip(t("pmode.dia_lock_named", name=d["name"]))
        self.lock.clicked.connect(lambda: mode.update_diagram(self.d_id, locked=not d["locked"]))
        row.addWidget(self.lock)


class _Description(QtWidgets.QPlainTextEdit):
    """The description, kept when it is left (one undo step for the text)."""

    def __init__(self, page):
        super().__init__()
        self.page = page

    def focusOutEvent(self, event):  # noqa: N802
        super().focusOutEvent(event)
        self.page.set(description=self.toPlainText().strip())


class DiagramsPage(QtWidgets.QWidget):
    """DIAGRAMAS, as the Presentation's «Volumes para diagramas»."""

    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.showing = False
        column = QtWidgets.QVBoxLayout(self)
        column.setContentsMargins(10, 8, 10, 8)
        column.setSpacing(6)
        top = QtWidgets.QHBoxLayout()
        self.scene_name = _head("")
        top.addWidget(self.scene_name, 1)
        self.frame_all = QtWidgets.QToolButton()
        self.frame_all.setObjectName("pm_icon")
        self.frame_all.setToolTip(t("pmode.dia_frame_all"))
        self.frame_all.clicked.connect(lambda: self.mode.frame_diagrams())
        top.addWidget(self.frame_all)
        column.addLayout(top)
        column.addWidget(_note(t("pmode.dia_intro")))
        column.addWidget(_head(t("pmode.dia_create").upper()))
        tiles = QtWidgets.QGridLayout()
        tiles.setSpacing(4)
        self.create = {}
        for k, kind in enumerate(dia.TYPES):
            button = QtWidgets.QToolButton()
            button.setObjectName("pm_page")
            button.setText(t("pmode.dia_shape." + kind))
            button.setToolTip(t("pmode.dia_new_hint"))
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
            button.clicked.connect(lambda _on=False, k_=kind: self.mode.add_diagram(k_))
            tiles.addWidget(button, k // 3, k % 3)
            self.create[kind] = button
        column.addLayout(tiles)
        self.empty = _note(t("pmode.dia_empty"))
        column.addWidget(self.empty)
        self.holder = QtWidgets.QWidget()
        self.rows = QtWidgets.QVBoxLayout(self.holder)
        self.rows.setContentsMargins(0, 0, 0, 0)
        self.rows.setSpacing(3)
        column.addWidget(self.holder)
        self.editor = self._build_editor()
        column.addWidget(self.editor)
        self.dup_scene = QtWidgets.QPushButton(t("pmode.dia_dup_scene"))
        self.dup_scene.setObjectName("pm_wide")
        self.dup_scene.clicked.connect(lambda: self.mode.duplicate(self.mode.scene_key))
        column.addWidget(self.dup_scene)
        column.addStretch(1)
        self.restyle()

    def restyle(self):
        self.frame_all.setIcon(glyphs.icon("expand", theme.colour("muted"), 16))

    # ------------------------------------------------------------ the one chosen

    def _build_editor(self):
        box = QtWidgets.QFrame()
        box.setObjectName("pm_card")
        form = QtWidgets.QFormLayout(box)
        form.setContentsMargins(8, 8, 8, 8)
        form.setVerticalSpacing(6)
        form.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)
        self.form = form
        self.name = QtWidgets.QLineEdit()
        self.name.setPlaceholderText(t("pmode.dia_name"))
        self.name.editingFinished.connect(lambda: self.set(name=self.name.text().strip()))
        form.addRow(self.name)
        self.info = _note("")
        form.addRow(self.info)
        buttons = QtWidgets.QHBoxLayout()
        buttons.setSpacing(3)
        self.duplicate = QtWidgets.QPushButton(t("pmode.dia_duplicate"))
        self.duplicate.clicked.connect(lambda: self.mode.duplicate_diagram(self.mode.diagram_key))
        self.focus = QtWidgets.QPushButton(t("pmode.dia_focus"))
        self.focus.clicked.connect(lambda: self.mode.frame_diagrams([self.mode.diagram_key]))
        self.lock = QtWidgets.QPushButton(t("pmode.dia_lock"))
        self.lock.setCheckable(True)
        self.lock.clicked.connect(lambda on: self.mode.update_diagram(self.mode.diagram_key, locked=on))
        self.remove = QtWidgets.QPushButton(t("pmode.dia_remove"))
        self.remove.clicked.connect(lambda: self.mode.remove_diagram(self.mode.diagram_key))
        for b in (self.duplicate, self.focus, self.lock, self.remove):
            b.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
            buttons.addWidget(b)
        form.addRow(buttons)
        self.shown = QtWidgets.QCheckBox(t("pmode.dia_show"))
        self.shown.toggled.connect(lambda on: self.set(visible=on))
        form.addRow(self.shown)
        self.locked_note = _note(t("pmode.dia_locked"))
        form.addRow(self.locked_note)
        form.addRow(_head(t("pmode.dia_measures").upper()))
        self.measures = self._triple(form, ("pmode.dia_width", "pmode.dia_height", "pmode.dia_depth"),   # (not
                                     (0.01, 10000.0), 0.1, " m", "dimensions")                     # `size`: Qt's)
        form.addRow(_head(t("pmode.dia_position").upper()))
        self.place = self._triple(form, ("pmode.dia_x", "pmode.dia_y", "pmode.dia_elevation"),
                                  (-100000.0, 100000.0), 0.1, " m", "position")
        form.addRow(_note(t("pmode.dia_base_hint")))
        form.addRow(_head(t("pmode.dia_rotation").upper()))
        self.turn = self._triple(form, ("pmode.dia_rot_x", "pmode.dia_rot_v", "pmode.dia_rot_y"),
                                 (-36000.0, 36000.0), 15.0, "°", "rotation")
        form.addRow(_head(t("pmode.dia_scale").upper()))
        self.scale = self._triple(form, ("pmode.dia_scale_x", "pmode.dia_scale_v", "pmode.dia_scale_y"),
                                  (0.01, 100.0), 0.1, "", "scale")
        self.reset = QtWidgets.QPushButton(t("pmode.dia_reset"))
        self.reset.clicked.connect(lambda: self.set(rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)))
        form.addRow(self.reset)
        form.addRow(_head(t("pmode.dia_appearance").upper()))
        colours = QtWidgets.QHBoxLayout()
        colours.setSpacing(3)
        self.swatches = {}
        for colour in dia.COLOURS:
            b = QtWidgets.QToolButton()
            b.setObjectName("pm_icon")
            b.setCheckable(True)
            b.setIcon(_swatch(colour, 18))
            b.setToolTip(colour)
            b.clicked.connect(lambda _on=False, c=colour: self.set(color=c))
            colours.addWidget(b)
            self.swatches[colour] = b
        colours.addStretch(1)
        form.addRow(colours)
        self.colour = QtWidgets.QPushButton()
        self.colour.clicked.connect(self._pick_colour)
        form.addRow(t("pmode.dia_colour"), self.colour)
        self.opacity = _spin(0.0, 100.0, 5.0, 0, " %")
        self.opacity.valueChanged.connect(lambda v: self.set(opacity=v / 100.0))
        form.addRow(t("pmode.dia_opacity"), self.opacity)
        self.wire = QtWidgets.QCheckBox(t("pmode.dia_wireframe"))
        self.wire.toggled.connect(lambda on: self.set(wireframe=on))
        form.addRow(self.wire)
        form.addRow(_head(t("pmode.dia_description").upper()))
        self.description = _Description(self)
        self.description.setFixedHeight(64)
        form.addRow(self.description)
        self.editable = [self.name, self.shown, self.remove, self.reset, self.colour, self.opacity, self.wire,
                         self.description, *self.measures, *self.place, *self.turn, *self.scale,
                         *self.swatches.values()]
        return box

    def _triple(self, form, keys, limits, step, suffix, field):
        boxes = []
        for k, key in enumerate(keys):
            box = _spin(limits[0], limits[1], step, 2, suffix)
            box.setToolTip(t(key))
            box.valueChanged.connect(lambda v, i=k, f=field: self._axis(f, i, v))
            form.addRow(t(key), box)
            boxes.append(box)
        return boxes

    def _axis(self, field, k, value):
        d = self.mode.diagram(self.mode.diagram_key)
        if self.showing or d is None:
            return
        values = list(d[field])
        values[k] = float(value)
        self.set(**{field: tuple(values)})

    def set(self, **fields):
        if not self.showing and self.mode.diagram_key:
            self.mode.update_diagram(self.mode.diagram_key, **fields)

    def _pick_colour(self):
        d = self.mode.diagram(self.mode.diagram_key)
        if d is None:
            return
        colour = QtWidgets.QColorDialog.getColor(QtGui.QColor(d["color"]), self, t("pmode.dia_colour"))
        if colour.isValid():
            self.set(color=colour.name())

    # ------------------------------------------------------------ shown

    def show_scene(self, scene):
        """The scene chosen's volumes and the one chosen again."""
        self.showing = True
        try:
            mode = self.mode
            items = mode.diagrams(scene)
            self.scene_name.setText(t("pmode.dia_scene", name=scene.name if scene is not None else "—").upper())
            while self.rows.count():
                item = self.rows.takeAt(0)
                if item.widget() is not None:
                    item.widget().hide()
                    item.widget().deleteLater()
            for d in items:
                self.rows.addWidget(_Row(self, d, d["id"] == mode.diagram_key))
            self.empty.setVisible(not items)
            self.holder.setVisible(bool(items))
            for button in self.create.values():
                button.setEnabled(scene is not None and len(items) < dia.MAX)
            self.frame_all.setEnabled(any(d["visible"] and d["opacity"] > 0 for d in items))
            self.dup_scene.setVisible(bool(items))
            d = mode.diagram(mode.diagram_key)
            self.editor.setVisible(d is not None)
            if d is not None:
                self._fill(d)
        finally:
            self.showing = False

    def _fill(self, d):
        if not self.name.hasFocus():
            self.name.setText(d["name"])
        kind = t("pmode.dia_shape." + d["type"])
        self.info.setText(kind if d["type"] == "plane" else
                          t("pmode.dia_info", shape=kind, v=_number(dia.volume(d))))
        self.lock.setChecked(d["locked"])
        self.shown.setChecked(d["visible"])
        self.locked_note.setVisible(d["locked"])
        for boxes, field in ((self.measures, "dimensions"), (self.place, "position"), (self.turn, "rotation"),
                             (self.scale, "scale")):
            for box, value in zip(boxes, d[field]):
                box.setValue(value)
        self.form.setRowVisible(self.measures[1], d["type"] != "plane")
        for colour, button in self.swatches.items():
            button.setChecked(colour == d["color"])
        self.colour.setIcon(_swatch(d["color"]))
        self.colour.setText(d["color"])
        self.opacity.setValue(round(d["opacity"] * 100))
        self.wire.setChecked(d["wireframe"])
        if not self.description.hasFocus() and self.description.toPlainText() != d["description"]:
            self.description.setPlainText(d["description"])
        for w in self.editable:
            w.setEnabled(not d["locked"])
