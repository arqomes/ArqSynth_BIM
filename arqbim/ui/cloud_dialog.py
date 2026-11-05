"""Nuvens de pontos ligadas (0.161): the scans linked to the project — each one's name, storey, how many points are
shown — and, of the one chosen, its units, how big its points are drawn, shown or not. Link another, delete the one
chosen. Every change one undo step (CloudLinksChange)."""

import dataclasses

from PySide6 import QtCore, QtWidgets

from ..i18n import t
from ..model import cad_links as cad_model
from ..model import cloud_links as cloud_model
from ..model.document import CloudLinksChange


class CloudDialog(QtWidgets.QDialog):
    def __init__(self, parent, doc, storey_names):
        super().__init__(parent)
        self.setWindowTitle(t("clouds.title"))
        self.doc, self.storey_names = doc, storey_names
        self.on_link = None
        layout = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(t("clouds.intro"))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        top = QtWidgets.QHBoxLayout()
        self.list = QtWidgets.QListWidget()
        self.list.currentRowChanged.connect(lambda _r: self._show())
        top.addWidget(self.list, 1)
        side = QtWidgets.QFormLayout()
        self.units = QtWidgets.QComboBox()
        for label, value in cad_model.UNIT_CHOICES:
            self.units.addItem(label, value)
        self.units.activated.connect(lambda k: self._set(units=float(self.units.itemData(k))))
        side.addRow(t("cadlinks.units"), self.units)
        self.size = QtWidgets.QDoubleSpinBox()
        self.size.setRange(1.0, 8.0)
        self.size.setSingleStep(0.5)
        self.size.setSuffix(" px")
        self.size.editingFinished.connect(lambda: self._set(size=float(self.size.value())))
        side.addRow(t("clouds.size"), self.size)
        self.visible = QtWidgets.QCheckBox(t("images.visible"))
        self.visible.toggled.connect(lambda on: self._set(visible=bool(on)))
        side.addRow(self.visible)
        self.count = QtWidgets.QLabel()
        side.addRow(self.count)
        top.addLayout(side)
        layout.addLayout(top, 1)
        buttons = QtWidgets.QHBoxLayout()
        link = QtWidgets.QPushButton(t("clouds.link"))
        link.clicked.connect(self._link)
        self.remove_button = QtWidgets.QPushButton(t("images.remove"))
        self.remove_button.clicked.connect(self._remove)
        close = QtWidgets.QPushButton(t("elprop.close"))
        close.clicked.connect(self.accept)
        buttons.addWidget(link)
        buttons.addWidget(self.remove_button)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(560, 320)
        self.refresh()

    def _current(self):
        row = self.list.currentRow()
        return self.doc.cloud_links[row] if 0 <= row < len(self.doc.cloud_links) else None

    def refresh(self, row=None):
        row = self.list.currentRow() if row is None else row
        blocker = QtCore.QSignalBlocker(self.list)
        self.list.clear()
        for link in self.doc.cloud_links:
            missing = cloud_model.cloud_of(link.path) is None
            self.list.addItem("{} — {}{}".format(link.name, self.storey_names.get(link.storey, t("images.ground")),
                                                 "  ({})".format(t("images.missing")) if missing else ""))
        del blocker
        if self.doc.cloud_links:
            self.list.setCurrentRow(min(max(row, 0), len(self.doc.cloud_links) - 1))
        self._show()

    def _show(self):
        link = self._current()
        for w in (self.units, self.size, self.visible, self.remove_button):
            w.setEnabled(link is not None)
        if link is None:
            self.count.setText("")
            return
        for w, setter in ((self.visible, lambda: self.visible.setChecked(link.visible)),
                          (self.size, lambda: self.size.setValue(link.size)),
                          (self.units, lambda: self.units.setCurrentIndex(next(
                              (i for i, (_l, v) in enumerate(cad_model.UNIT_CHOICES) if abs(v - link.units) < 1e-12),
                              -1)))):
            b = QtCore.QSignalBlocker(w)
            setter()
            del b
        cloud = cloud_model.cloud_of(link.path)
        self.count.setText(t("clouds.count", n="{:,}".format(len(cloud)).replace(",", " ")) if cloud is not None
                           else t("images.missing"))

    def _set(self, **fields):
        link = self._current()
        if link is None or all(getattr(link, k) == v for k, v in fields.items()):
            return
        after = dataclasses.replace(link, **fields)
        self.doc.execute(CloudLinksChange(self.doc.cloud_links,
                                          [after if c.uid == link.uid else c for c in self.doc.cloud_links],
                                          t("cmd.cloud_change")))

    def _link(self):
        if self.on_link is not None:
            self.on_link()
        self.refresh(len(self.doc.cloud_links) - 1)

    def _remove(self):
        link = self._current()
        if link is None:
            return
        self.doc.execute(CloudLinksChange(self.doc.cloud_links, [c for c in self.doc.cloud_links if c.uid != link.uid],
                                          t("cmd.cloud_remove")))
        self.refresh()
