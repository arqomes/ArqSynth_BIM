"""Desenhos CAD ligados (0.158): the DXF drawings linked to the project — each one's name, storey and units, shown
or not, locked or not — and, of the one chosen, its layers to tick (shown) or untick (hidden), with what each has.
Link another, delete the one chosen. Every change one undo step (CadLinksChange)."""

import dataclasses

from PySide6 import QtCore, QtWidgets

from ..i18n import t
from ..model import cad_links as cad_model
from ..model.document import CadLinksChange
from . import theme

LAYER = QtCore.Qt.ItemDataRole.UserRole


class CadDialog(QtWidgets.QDialog):
    def __init__(self, parent, doc, storey_names):
        super().__init__(parent)
        self.setWindowTitle(t("cadlinks.title"))
        self.doc, self.storey_names = doc, storey_names
        self.on_link = None             # () -> None: the window links another
        layout = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(t("cadlinks.intro"))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        top = QtWidgets.QHBoxLayout()
        self.links = QtWidgets.QListWidget()
        self.links.currentRowChanged.connect(lambda _r: self._show_layers())
        top.addWidget(self.links, 1)
        side = QtWidgets.QFormLayout()
        self.units = QtWidgets.QComboBox()
        for label, value in cad_model.UNIT_CHOICES:
            self.units.addItem(label, value)
        self.units.activated.connect(self._units_chosen)
        side.addRow(t("cadlinks.units"), self.units)
        self.visible = QtWidgets.QCheckBox(t("images.visible"))
        self.visible.toggled.connect(lambda on: self._set(visible=bool(on)))
        side.addRow(self.visible)
        self.locked = QtWidgets.QCheckBox(t("images.locked"))
        self.locked.toggled.connect(lambda on: self._set(locked=bool(on)))
        side.addRow(self.locked)
        top.addLayout(side)
        layout.addLayout(top)
        layout.addWidget(QtWidgets.QLabel(t("cadlinks.layers")))
        self.layers = QtWidgets.QListWidget()
        self.layers.itemChanged.connect(self._layer_ticked)
        layout.addWidget(self.layers, 2)
        self.note = QtWidgets.QLabel()
        self.note.setStyleSheet("color: %s;" % theme.C["fail"])
        layout.addWidget(self.note)
        buttons = QtWidgets.QHBoxLayout()
        link = QtWidgets.QPushButton(t("cadlinks.link"))
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
        self.resize(640, 480)
        self.refresh()

    def _current(self):
        row = self.links.currentRow()
        return self.doc.cad_links[row] if 0 <= row < len(self.doc.cad_links) else None

    def refresh(self, row=None):
        row = self.links.currentRow() if row is None else row
        blocker = QtCore.QSignalBlocker(self.links)
        self.links.clear()
        for link in self.doc.cad_links:
            storey = self.storey_names.get(link.storey, t("images.ground"))
            missing = cad_model.drawing_of(link.path) is None
            self.links.addItem("{} — {}{}".format(link.name, storey, "  ({})".format(t("images.missing"))
                                                  if missing else ""))
        del blocker
        if self.doc.cad_links:
            self.links.setCurrentRow(min(max(row, 0), len(self.doc.cad_links) - 1))
        self._show_layers()

    def _show_layers(self):
        link = self._current()
        for w in (self.units, self.visible, self.locked, self.remove_button, self.layers):
            w.setEnabled(link is not None)
        blocker = QtCore.QSignalBlocker(self.layers)
        self.layers.clear()
        if link is None:
            del blocker
            return
        for w, value in ((self.visible, link.visible), (self.locked, link.locked)):
            b = QtCore.QSignalBlocker(w)
            w.setChecked(bool(value))
            del b
        b = QtCore.QSignalBlocker(self.units)
        k = next((i for i, (_l, v) in enumerate(cad_model.UNIT_CHOICES) if abs(v - link.units) < 1e-12), -1)
        self.units.setCurrentIndex(k)
        del b
        found = cad_model.drawing_of(link.path)
        if found is not None:
            from ..core import cad
            for name, (entities, segs) in sorted(cad.layers(found[0]).items()):
                item = QtWidgets.QListWidgetItem(t("cadlinks.layer", name=name, n=entities, s=segs))
                item.setData(LAYER, name)
                item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.CheckState.Unchecked if name in link.hidden
                                   else QtCore.Qt.CheckState.Checked)
                self.layers.addItem(item)
        del blocker

    def _change(self, link, after, label):
        links = [after if c.uid == link.uid else c for c in self.doc.cad_links]
        self.doc.execute(CadLinksChange(self.doc.cad_links, links, label))

    def _set(self, **fields):
        link = self._current()
        if link is None or all(getattr(link, k) == v for k, v in fields.items()):
            return
        if link.locked and "locked" not in fields:
            self.note.setText(t("err.cad_locked", f=link.name))
            return
        self._change(link, dataclasses.replace(link, **fields), t("cmd.cad_change"))
        self.note.setText("")

    def _units_chosen(self, index):
        self._set(units=float(self.units.itemData(index)))
        self.refresh()

    def _layer_ticked(self, item):
        link = self._current()
        if link is None:
            return
        name = item.data(LAYER)
        hidden = [k for k in link.hidden if k != name]
        if item.checkState() != QtCore.Qt.CheckState.Checked:
            hidden.append(name)
        self._set(hidden=sorted(hidden))

    def _link(self):
        if self.on_link is not None:
            self.on_link()
        self.refresh(len(self.doc.cad_links) - 1)

    def _remove(self):
        link = self._current()
        if link is None:
            return
        if link.locked:
            self.note.setText(t("err.cad_locked", f=link.name))
            return
        self.doc.execute(CadLinksChange(self.doc.cad_links, [c for c in self.doc.cad_links if c.uid != link.uid],
                                        t("cmd.cad_remove")))
        self.refresh()
