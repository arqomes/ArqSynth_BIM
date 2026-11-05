"""Terrain from a DXF (0.156): the drawing's layers with points that have a height, one per line with how many —
ticked those that have heights (a drawing in 2D has none); the terrain is made through the points of the layers
ticked."""

from PySide6 import QtCore, QtWidgets

from ..i18n import t

LAYER = QtCore.Qt.ItemDataRole.UserRole


class DxfPointsDialog(QtWidgets.QDialog):
    def __init__(self, parent, file_name, layers, ticked):
        """layers: {name: [(x, y, z)…]}; ticked: the names ticked to start with."""
        super().__init__(parent)
        self.setWindowTitle(t("dxfpts.title"))
        layout = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(t("dxfpts.intro", f=file_name))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.list = QtWidgets.QListWidget()
        for name in sorted(layers):
            pts = layers[name]
            zs = [z for _x, _y, z in pts]
            item = QtWidgets.QListWidgetItem(t("dxfpts.layer", name=name, n=len(pts),
                                               lo="{:.2f}".format(min(zs)).replace(".", ","),
                                               hi="{:.2f}".format(max(zs)).replace(".", ",")))
            item.setData(LAYER, name)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Checked if name in ticked else QtCore.Qt.CheckState.Unchecked)
            self.list.addItem(item)
        layout.addWidget(self.list, 1)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.resize(520, 360)

    def chosen(self):
        return [self.list.item(k).data(LAYER) for k in range(self.list.count())
                if self.list.item(k).checkState() == QtCore.Qt.CheckState.Checked]
