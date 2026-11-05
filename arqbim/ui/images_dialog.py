"""Imagens de fundo (0.154): the project's background images, one per line — its name, storey, width, how opaque,
shown or not, locked or not. Import another, calibrate the one chosen (the window starts the tool once this
closes), delete it. Every change one undo step (ImagesChange)."""

import dataclasses

from PySide6 import QtCore, QtWidgets

from ..i18n import t
from ..model.document import ImagesChange
from . import theme

NAME, STOREY, WIDTH, OPACITY, VISIBLE, LOCKED = range(6)


class ImagesDialog(QtWidgets.QDialog):
    def __init__(self, parent, doc, storey_names, missing):
        """storey_names: {GlobalId: name}; missing(image) -> its picture could not be read."""
        super().__init__(parent)
        self.setWindowTitle(t("images.title"))
        self.doc, self.storey_names, self.missing = doc, storey_names, missing
        self.on_import = None           # () -> None: the window imports one (this list then shown again)
        self.calibrate = None           # the uid of the image to calibrate, once closed
        self.facade = None              # (0.208) the uid of the image to stand up on a facade, once closed
        self.crop = None                # (0.209) the uid of the image to crop, once closed
        layout = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(t("images.intro"))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([t("images.name"), t("images.storey"), t("images.width"),
                                              t("images.opacity"), t("images.visible"), t("images.locked")])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(NAME, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.itemChanged.connect(self._renamed)
        layout.addWidget(self.table, 1)
        self.note = QtWidgets.QLabel()
        self.note.setStyleSheet("color: %s;" % theme.C["fail"])
        layout.addWidget(self.note)
        buttons = QtWidgets.QHBoxLayout()
        self.import_button = QtWidgets.QPushButton(t("images.import"))
        self.import_button.clicked.connect(self._import)
        self.calibrate_button = QtWidgets.QPushButton(t("images.calibrate"))
        self.calibrate_button.clicked.connect(self._calibrate)
        self.facade_button = QtWidgets.QPushButton(t("images.facade"))           # (0.208)
        self.facade_button.setToolTip(t("images.facade_tip"))
        self.facade_button.clicked.connect(self._facade)
        self.crop_button = QtWidgets.QPushButton(t("images.crop"))               # (0.209)
        self.crop_button.setToolTip(t("images.crop_tip"))
        self.crop_button.clicked.connect(self._crop)
        self.whole_button = QtWidgets.QPushButton(t("images.whole"))
        self.whole_button.setToolTip(t("images.whole_tip"))
        self.whole_button.clicked.connect(self._whole)
        self.remove_button = QtWidgets.QPushButton(t("images.remove"))
        self.remove_button.clicked.connect(self._remove)
        close = QtWidgets.QPushButton(t("elprop.close"))
        close.clicked.connect(self.accept)
        for b in (self.import_button, self.calibrate_button, self.facade_button, self.crop_button,
                  self.whole_button, self.remove_button):
            buttons.addWidget(b)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(720, 340)
        self.refresh()

    # ------------------------------------------------------------ the list

    def refresh(self):
        row = self.table.currentRow()
        blocker = QtCore.QSignalBlocker(self.table)
        self.table.setRowCount(0)
        lost = []
        for k, image in enumerate(self.doc.images):
            self.table.insertRow(k)
            name = QtWidgets.QTableWidgetItem(image.name)
            name.setData(QtCore.Qt.ItemDataRole.UserRole, image.uid)
            name.setToolTip(image.path)
            if self.missing(image):
                name.setForeground(theme.colour("fail"))
                lost.append(image.name)
            self.table.setItem(k, NAME, name)
            storey = QtWidgets.QTableWidgetItem(self.storey_names.get(image.storey, t("images.ground")))
            storey.setFlags(storey.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(k, STOREY, storey)
            width = QtWidgets.QDoubleSpinBox()
            width.setRange(0.10, 100000.0)
            width.setDecimals(2)
            width.setSuffix(" m")
            width.setValue(image.width)
            width.setEnabled(not image.locked)
            width.editingFinished.connect(lambda uid=image.uid, w=width: self._set_width(uid, w.value()))
            self.table.setCellWidget(k, WIDTH, width)
            opacity = QtWidgets.QSpinBox()
            opacity.setRange(5, 100)
            opacity.setSuffix(" %")
            opacity.setValue(int(round(image.opacity * 100)))
            opacity.editingFinished.connect(lambda uid=image.uid, o=opacity: self._set(uid, opacity=o.value() / 100.0))
            self.table.setCellWidget(k, OPACITY, opacity)
            for column, value, key in ((VISIBLE, image.visible, "visible"), (LOCKED, image.locked, "locked")):
                box = QtWidgets.QCheckBox()
                box.setChecked(bool(value))
                box.toggled.connect(lambda on, uid=image.uid, key=key: self._set(uid, **{key: bool(on)}))
                self.table.setCellWidget(k, column, box)
        del blocker
        if lost:
            self.note.setText("{}: {}".format(t("images.missing"), ", ".join(lost)))
        if self.doc.images:
            self.table.selectRow(min(max(row, 0), len(self.doc.images) - 1))
        for b in (self.calibrate_button, self.facade_button, self.crop_button, self.whole_button, self.remove_button):
            b.setEnabled(bool(self.doc.images))

    def _current(self):
        row = self.table.currentRow()
        return self.doc.images[row] if 0 <= row < len(self.doc.images) else None

    # ------------------------------------------------------------ changes

    def _image(self, uid):
        return next((i for i in self.doc.images if i.uid == uid), None)

    def _change(self, image, after, label):
        images = [after if i.uid == image.uid else i for i in self.doc.images]
        self.doc.execute(ImagesChange(self.doc.images, images, label))

    def _set(self, uid, **fields):
        image = self._image(uid)
        if image is None or all(getattr(image, k) == v for k, v in fields.items()):
            return
        self._change(image, dataclasses.replace(image, **fields), t("cmd.change_image"))
        self.note.setText("")
        QtCore.QTimer.singleShot(0, self.refresh)           # (out of the widget's own signal)

    def _set_width(self, uid, width):
        """Wider / narrower about its lower-left corner (not when locked)."""
        image = self._image(uid)
        if image is None or image.locked or abs(width - image.width) < 1e-6 or width <= 0:
            return
        self._change(image, image.scaled(image.origin, width / image.width), t("cmd.change_image"))
        QtCore.QTimer.singleShot(0, self.refresh)

    def _renamed(self, item):
        if item.column() != NAME:
            return
        image = self._image(item.data(QtCore.Qt.ItemDataRole.UserRole))
        text = item.text().strip()
        if image is not None and text and text != image.name:
            self._set(image.uid, name=text)

    def _import(self):
        if self.on_import is not None:
            self.on_import()
        self.refresh()
        if self.doc.images:
            self.table.selectRow(len(self.doc.images) - 1)

    def _calibrate(self):
        image = self._current()
        if image is None:
            return
        if image.locked:
            self.note.setText(t("err.image_locked", f=image.name))
            return
        if image.vertical:                                  # (0.208: a facade's: put on it again instead)
            self.note.setText(t("err.image_vertical"))
            return
        self.calibrate = image.uid
        self.accept()

    def _facade(self):
        """(0.208) Pôr numa fachada: the window starts the tool once this closes."""
        image = self._current()
        if image is None:
            return
        if image.locked:
            self.note.setText(t("err.image_locked", f=image.name))
            return
        self.facade = image.uid
        self.accept()

    def _crop(self):
        """(0.209) Recortar: the window starts the tool once this closes."""
        image = self._current()
        if image is None:
            return
        if image.locked:
            self.note.setText(t("err.image_locked", f=image.name))
            return
        self.crop = image.uid
        self.accept()

    def _whole(self):
        """(0.209) Inteira: all of the picture shown again."""
        image = self._current()
        if image is None or not image.crop:
            return
        self._set(image.uid, crop=None)

    def _remove(self):
        image = self._current()
        if image is None:
            return
        if image.locked:
            self.note.setText(t("err.image_locked", f=image.name))
            return
        self.doc.execute(ImagesChange(self.doc.images, [i for i in self.doc.images if i.uid != image.uid],
                                      t("cmd.remove_image")))
        self.note.setText("")
        self.refresh()
