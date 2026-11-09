"""(0.485) The Presentation tab's «Etiquetas» — the owner, 2026-11-09: «é importante criar cortes, ter diagramas,
etiqueta, efeitos». As the ArqSynth Presentation's (its LabelsTab and buildLabelTexture):

- the picture of a label (tag_pixels): a rounded box with its name in capitals over its note, or a circle with its
  number, name and note, in its colours, as the Presentation draws it on its canvas;
- the page of the right column (LabelsPage): «Adicionar etiqueta» — Piso, Parede, Em pé, Chamada: a click on the model
  puts one there (tools/presentation_label.py) —; the labels, each with its eye (the scene's: kept with «Criar cena» /
  «Atualizar»); the one chosen — its name and note with their letter's size, its shape and number, its colours, its
  opacity and size, its turn (eight steps of 45° and a slider that sticks to them), its post or leader, «Virar para a
  câmara», «Ocultar quando tapada», Apagar —; and the rooms as labels on their floors (the 0.366 option).

The labels are the model's (Document.presentation["tags"], model/presentation_tags.py), one undo step a change."""

import math

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..model import presentation_tags as tags_model
from . import presentation_glyphs as glyphs
from . import theme

S = 2                                   # the picture's resolution (the Presentation's TEX_SCALE is 3)
STROKE = "#151515"                      # the Presentation's outline of a label (drawn: not the window's colours)
MAX_SIDE = 4096
ANGLES = (0, 45, 90, 135, 180, 225, 270, 315)
_cache = {}


def _font(px, heavy):
    font = QtGui.QFont()
    font.setFamilies(["Geist", "Segoe UI", "Arial", "DejaVu Sans", "sans-serif"])
    font.setPixelSize(max(1, int(round(px))))
    font.setWeight(QtGui.QFont.Weight.ExtraBold if heavy else QtGui.QFont.Weight.Normal)
    return font


def _width(font, text):
    return QtGui.QFontMetricsF(font).horizontalAdvance(text) if text else 0.0


def _fill(tag):
    colour = QtGui.QColor(tag["background"])
    colour.setAlphaF(min(max(float(tag["opacity"]), 0.0), 1.0))
    return colour


def tag_pixels(tag):
    """(RGBA pixels (H, W, 4) uint8 — row 0 at the top —, width / height) of the label's picture, as the Presentation's
    buildLabelTexture (kept for the same name, note, number, shape and look)."""
    key = tuple(tag[k] for k in ("title", "note", "number", "shape", "title_scale", "note_scale", "background",
                                 "opacity", "text_color"))
    found = _cache.get(key)
    if found is not None:
        return found
    title = (tag["title"] or " ").upper()
    note, number = tag["note"], tag["number"]
    ts, ns = float(tag["title_scale"]), float(tag["note_scale"])
    if tag["shape"] == "circle":
        title_font, number_font, note_font = _font(30 * S * ts, True), _font(40 * S, True), _font(21 * S * ns, False)
        content = max(_width(title_font, title), _width(note_font, note), 60 * S)
        h_number, h_title, h_note = (40 * S if number else 0), 32 * S * ts, (26 * S * ns if note else 0)
        diameter = max(content + 50 * S, h_number + h_title + h_note + 46 * S, 170 * S)
        width = height = int(math.ceil(diameter + 8 * S))
    else:
        title_font, note_font = _font(34 * S * ts, True), _font(23 * S * ns, False)
        pad_x, pad_y = 22 * S, 14 * S
        inner_w = max(_width(title_font, title), _width(note_font, note), 90 * S)
        inner_h = 40 * S * ts + (30 * S * ns if note else 6 * S)
        width, height = int(math.ceil(inner_w + pad_x * 2 + 8 * S)), int(math.ceil(inner_h + pad_y * 2 + 8 * S))
    image = QtGui.QImage(width, height, QtGui.QImage.Format.Format_RGBA8888_Premultiplied)
    image.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(image)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
    p.setPen(QtGui.QPen(QtGui.QColor(STROKE), 3.5 * S))
    p.setBrush(_fill(tag))
    ink = QtGui.QColor(tag["text_color"])
    if tag["shape"] == "circle":
        c = width / 2.0
        p.drawEllipse(QtCore.QPointF(c, c), diameter / 2.0, diameter / 2.0)
        p.setPen(ink)
        lines = ([(number, number_font, h_number)] if number else []) + [(title, title_font, h_title)] \
            + ([(note, note_font, h_note)] if note else [])
        y = c - sum(h for _s, _f, h in lines) / 2.0
        for text, font, h in lines:
            p.setFont(font)
            p.drawText(QtCore.QRectF(c - diameter / 2.0 + 15 * S, y, diameter - 30 * S, h),
                       QtCore.Qt.AlignmentFlag.AlignCenter, text)
            y += h
    else:
        x, y0 = 4 * S, 4 * S
        p.drawRoundedRect(QtCore.QRectF(x, y0, width - 8 * S, height - 8 * S), 9 * S, 9 * S)
        p.setPen(ink)
        p.setFont(title_font)
        baseline = y0 + pad_y + 32 * S * ts
        p.drawText(QtCore.QPointF(x + pad_x, baseline), title)
        if note:
            p.setFont(note_font)
            p.drawText(QtCore.QPointF(x + pad_x, baseline + 26 * S * ns), note)
    p.end()
    if max(width, height) > MAX_SIDE:                     # (a very long name: the picture no bigger than a GPU's)
        image = image.scaled(min(width, MAX_SIDE), min(height, MAX_SIDE),
                             QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                             QtCore.Qt.TransformationMode.SmoothTransformation)
    image = image.convertToFormat(QtGui.QImage.Format.Format_RGBA8888)
    w, h = image.width(), image.height()
    data = np.frombuffer(image.constBits(), np.uint8, count=image.bytesPerLine() * h)
    pixels = data.reshape(h, image.bytesPerLine() // 4, 4)[:, :w].copy()
    if len(_cache) > 400:
        _cache.clear()
    _cache[key] = (pixels, width / float(height))
    return _cache[key]


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


def _spin(lo, hi, step, decimals, suffix):
    box = QtWidgets.QDoubleSpinBox()
    box.setRange(lo, hi)
    box.setSingleStep(step)
    box.setDecimals(decimals)
    box.setSuffix(suffix)
    box.setKeyboardTracking(False)
    return box


def _head(text):
    label = QtWidgets.QLabel(text)
    label.setObjectName("pm_head")
    return label


def _note(text):
    label = QtWidgets.QLabel(text)
    label.setObjectName("pm_note")
    label.setWordWrap(True)
    return label


class _Row(QtWidgets.QFrame):
    """A label in the list: its colour, its name, where it is, its eye — a click chooses it (again: not chosen)."""

    def __init__(self, page, tag, hidden, chosen):
        super().__init__()
        self.setObjectName("pm_card")
        self.setProperty("active", "true" if chosen else "false")
        self.tag_id = tag["id"]
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(6, 2, 2, 2)
        row.setSpacing(4)
        name = tag["title"] or t("pmode.tag_unnamed")
        self.button = QtWidgets.QPushButton(_swatch(tag["background"]), name)
        self.button.setObjectName("pm_link")
        self.button.setToolTip(t("pmode.tag_close" if chosen else "pmode.tag_edit", name=name))
        self.button.clicked.connect(lambda: page.mode.choose_tag(None if chosen else self.tag_id))
        row.addWidget(self.button, 1)
        where = QtWidgets.QLabel(t("pmode.tag_place." + tag["placement"]))
        where.setObjectName("pm_sub")
        row.addWidget(where)
        self.eye = QtWidgets.QToolButton()
        self.eye.setObjectName("pm_icon")
        self.eye.setIcon(glyphs.icon("eye_off" if hidden else "eye", theme.colour("muted"), 14))
        self.eye.setToolTip(t("pmode.tag_show" if hidden else "pmode.tag_hide", name=name))
        self.eye.clicked.connect(lambda: page.mode.toggle_tag(self.tag_id))
        row.addWidget(self.eye)
        if hidden:
            effect = QtWidgets.QGraphicsOpacityEffect(self)
            effect.setOpacity(0.6)
            self.setGraphicsEffect(effect)


class LabelsPage(QtWidgets.QWidget):
    """ETIQUETAS, as the Presentation's: add one, the list, the one chosen; the rooms as labels."""

    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.showing = False
        column = QtWidgets.QVBoxLayout(self)
        column.setContentsMargins(10, 8, 10, 8)
        column.setSpacing(6)
        column.addWidget(_head(t("pmode.tag_add").upper()))
        tiles = QtWidgets.QGridLayout()                    # (two by two: «Chamada» whole in a narrow column)
        tiles.setSpacing(4)
        self.place_buttons = {}
        for k, placement in enumerate(tags_model.PLACEMENTS):
            button = QtWidgets.QToolButton()
            button.setObjectName("pm_page")
            button.setCheckable(True)
            button.setText(t("pmode.tag_place." + placement))
            button.setToolTip(t("pmode.tag_place_tip." + placement))
            button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
            button.clicked.connect(lambda _on=False, p=placement: self.mode.start_label(p))
            tiles.addWidget(button, k // 2, k % 2)
            self.place_buttons[placement] = button
        column.addLayout(tiles)
        self.placing = _note(t("pmode.tag_place_hint"))
        column.addWidget(self.placing)
        self.count = _head(t("pmode.rail.labels").upper())
        column.addWidget(self.count)
        self.empty = _note(t("pmode.tag_empty"))
        column.addWidget(self.empty)
        self.holder = QtWidgets.QWidget()
        self.rows = QtWidgets.QVBoxLayout(self.holder)
        self.rows.setContentsMargins(0, 0, 0, 0)
        self.rows.setSpacing(3)
        column.addWidget(self.holder)
        self.editor = self._build_editor()
        column.addWidget(self.editor)
        column.addWidget(_note(t("pmode.tag_saved")))
        line = QtWidgets.QFrame()
        line.setObjectName("pm_line")
        column.addWidget(line)
        self.rooms = QtWidgets.QCheckBox(t("present.labels"))
        self.rooms.toggled.connect(lambda on: None if self.showing else self.mode.set_option(labels=on))
        column.addWidget(self.rooms)
        column.addWidget(_note(t("pmode.labels_note")))
        column.addStretch(1)

    # ------------------------------------------------------------ the one chosen

    def _build_editor(self):
        box = QtWidgets.QFrame()
        box.setObjectName("pm_card")
        form = QtWidgets.QFormLayout(box)
        form.setContentsMargins(8, 8, 8, 8)
        form.setVerticalSpacing(6)
        form.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)
        self.editor_form = form
        top = QtWidgets.QHBoxLayout()
        top.addWidget(_head(t("pmode.tag_name").upper()), 1)
        self.delete = QtWidgets.QPushButton(t("pmode.tag_delete"))
        self.delete.clicked.connect(lambda: self.mode.remove_tag(self.mode.tag_key))
        top.addWidget(self.delete)
        form.addRow(top)
        self.title = QtWidgets.QLineEdit()
        self.title.setPlaceholderText(t("pmode.tag_name_hint"))
        self.title.editingFinished.connect(lambda: self._set(title=self.title.text().strip()))
        form.addRow(self.title)
        self.title_scale = _spin(0.6, 2.0, 0.05, 2, "×")
        self.title_scale.valueChanged.connect(lambda v: self._set(title_scale=v))
        form.addRow(t("pmode.tag_letter"), self.title_scale)
        form.addRow(_head(t("pmode.tag_note").upper()))
        self.note = QtWidgets.QLineEdit()
        self.note.setPlaceholderText(t("pmode.tag_note_hint"))
        self.note.editingFinished.connect(lambda: self._set(note=self.note.text().strip()))
        form.addRow(self.note)
        self.note_scale = _spin(0.6, 2.5, 0.05, 2, "×")
        self.note_scale.valueChanged.connect(lambda v: self._set(note_scale=v))
        form.addRow(t("pmode.tag_letter"), self.note_scale)
        shape = QtWidgets.QHBoxLayout()
        self.shapes = {}
        group = QtWidgets.QButtonGroup(box)
        for name in tags_model.SHAPES:
            button = QtWidgets.QToolButton()
            button.setObjectName("pm_seg")
            button.setCheckable(True)
            button.setText(t("pmode.tag_shape." + name))
            button.clicked.connect(lambda _on=False, k=name: self._set(shape=k))
            group.addButton(button)
            shape.addWidget(button)
            self.shapes[name] = button
        self.number = QtWidgets.QLineEdit()
        self.number.setPlaceholderText(t("pmode.tag_number_hint"))
        self.number.setMaximumWidth(56)
        self.number.setToolTip(t("pmode.tag_number"))
        self.number.editingFinished.connect(lambda: self._set(number=self.number.text().strip()))
        shape.addWidget(self.number)
        shape.addStretch(1)
        form.addRow(t("pmode.tag_shape"), shape)
        self.background = QtWidgets.QPushButton()
        self.background.clicked.connect(lambda: self._colour("background"))
        form.addRow(t("pmode.tag_background"), self.background)
        self.ink = QtWidgets.QPushButton()
        self.ink.clicked.connect(lambda: self._colour("text_color"))
        form.addRow(t("pmode.tag_text"), self.ink)
        self.opacity = _spin(0.0, 100.0, 5.0, 0, " %")
        self.opacity.valueChanged.connect(lambda v: self._set(opacity=v / 100.0))
        form.addRow(t("pmode.tag_opacity"), self.opacity)
        self.size = _spin(0.4, 3.0, 0.1, 1, "×")
        self.size.valueChanged.connect(lambda v: self._set(scale=v))
        form.addRow(t("pmode.tag_size"), self.size)
        steps = QtWidgets.QGridLayout()
        steps.setSpacing(2)
        self.steps = {}
        for k, angle in enumerate(ANGLES):
            button = QtWidgets.QToolButton()
            button.setObjectName("pm_seg")
            button.setCheckable(True)
            button.setText("{}°".format(angle))
            button.setToolTip(t("pmode.tag_steps"))
            button.clicked.connect(lambda _on=False, a=angle: self._set(rotation=float(a)))
            steps.addWidget(button, k // 4, k % 4)
            self.steps[angle] = button
        self.steps_box = QtWidgets.QWidget()
        self.steps_box.setLayout(steps)
        form.addRow(self.steps_box)
        self.rotation = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.rotation.setRange(0, 359)
        self.rotation.setToolTip(t("pmode.tag_rotation"))
        self.rotation_text = QtWidgets.QLabel("0°")
        self.rotation.valueChanged.connect(self._turned)
        self.rotation.sliderReleased.connect(lambda: self._set(rotation=tags_model.snap_angle(self.rotation.value())))
        turn = QtWidgets.QHBoxLayout()
        turn.addWidget(self.rotation, 1)
        turn.addWidget(self.rotation_text)
        self.turn_box = QtWidgets.QWidget()
        self.turn_box.setLayout(turn)
        turn.setContentsMargins(0, 0, 0, 0)
        form.addRow(t("pmode.tag_rotation"), self.turn_box)
        self.leader = _spin(0.2, 4.0, 0.05, 2, " m")
        self.leader.valueChanged.connect(lambda v: self._set(leader=v))
        form.addRow(t("pmode.tag_post"), self.leader)
        self.face = QtWidgets.QCheckBox(t("pmode.tag_face"))
        self.face.setToolTip(t("pmode.tag_face_tip"))
        self.face.toggled.connect(lambda on: self._set(face_camera=on))
        form.addRow(self.face)
        self.occluded = QtWidgets.QCheckBox(t("pmode.tag_occluded"))
        self.occluded.setToolTip(t("pmode.tag_occluded_tip"))
        self.occluded.toggled.connect(lambda on: self._set(hide_occluded=on))
        form.addRow(self.occluded)
        return box

    def _set(self, **fields):
        if not self.showing and self.mode.tag_key:
            self.mode.update_tag(self.mode.tag_key, **fields)

    def _turned(self, value):
        self.rotation_text.setText("{}°".format(value))
        if not self.showing and not self.rotation.isSliderDown():
            self._set(rotation=tags_model.snap_angle(value))

    def _colour(self, name):
        tag = self.mode.tag(self.mode.tag_key)
        if tag is None:
            return
        colour = QtWidgets.QColorDialog.getColor(QtGui.QColor(tag[name]), self, t("pmode.tag_" + (
            "background" if name == "background" else "text")))
        if colour.isValid():
            self._set(**{name: colour.name()})

    # ------------------------------------------------------------ shown

    def show_placing(self, placement):
        """The placement being put (its tile pressed, the step said), or None."""
        for name, button in self.place_buttons.items():
            button.setChecked(name == placement)
        self.placing.setVisible(placement is not None)

    def show_scene(self, _scene):
        """The list and the one chosen again (a label put, changed, removed; another scene chosen)."""
        self.showing = True
        try:
            mode = self.mode
            tags = mode.tags()
            hidden = mode.live["hidden_tags"]
            while self.rows.count():
                item = self.rows.takeAt(0)
                if item.widget() is not None:
                    item.widget().hide()
                    item.widget().deleteLater()
            for tag in tags:
                self.rows.addWidget(_Row(self, tag, tag["id"] in hidden, tag["id"] == mode.tag_key))
            self.count.setText("{}  ({})".format(t("pmode.rail.labels").upper(), len(tags)) if tags
                               else t("pmode.rail.labels").upper())
            self.empty.setVisible(not tags)
            self.holder.setVisible(bool(tags))
            self.show_placing(mode.placing())
            tag = mode.tag(mode.tag_key)
            self.editor.setVisible(tag is not None)
            if tag is not None:
                self._fill(tag)
            options, rooms = mode.options(), mode.room_count()
            self.rooms.setChecked(bool(options.get("labels", True)))
            self.rooms.setText(t("present.labels") + (" ({})".format(rooms) if rooms else ""))
            self.rooms.setEnabled(bool(rooms))
        finally:
            self.showing = False

    def _fill(self, tag):
        if not self.title.hasFocus():
            self.title.setText(tag["title"])
        if not self.note.hasFocus():
            self.note.setText(tag["note"])
        if not self.number.hasFocus():
            self.number.setText(tag["number"])
        self.title_scale.setValue(tag["title_scale"])
        self.note_scale.setValue(tag["note_scale"])
        for name, button in self.shapes.items():
            button.setChecked(name == tag["shape"])
        self.number.setVisible(tag["shape"] == "circle")
        self.background.setIcon(_swatch(tag["background"]))
        self.background.setText(tag["background"])
        self.ink.setIcon(_swatch(tag["text_color"]))
        self.ink.setText(tag["text_color"])
        self.opacity.setValue(round(tag["opacity"] * 100))
        self.size.setValue(tag["scale"])
        turns = tags_model.turns(tag)
        degrees = int(round(tag["rotation"])) % 360
        for angle, button in self.steps.items():
            button.setChecked(angle == degrees)
        self.rotation.setValue(degrees)
        self.rotation_text.setText("{}°".format(degrees))
        form = self.editor_form
        form.setRowVisible(self.steps_box, turns)
        form.setRowVisible(self.turn_box, turns)
        self.leader.setValue(tag["leader"])
        reach = tag["placement"] in ("standing", "wall_leader")
        form.setRowVisible(self.leader, reach)
        if reach:
            form.labelForField(self.leader).setText(t("pmode.tag_post" if tag["placement"] == "standing"
                                                      else "pmode.tag_callout"))
        self.face.setChecked(tag["face_camera"])
        form.setRowVisible(self.face, tag["placement"] == "standing")
        self.occluded.setChecked(tag["hide_occluded"])
