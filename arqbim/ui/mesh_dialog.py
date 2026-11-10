"""Structure ▸ Welded mesh (0.522): the mesh put on the slabs selected — its wires' Ø and spacing, the face, the
cover, the direction —, its checks shown as they change; generic, by Ø and spacing (the makers' names to confirm)."""

from PySide6 import QtWidgets

from ..core import rebar_mesh as rm
from ..i18n import decimal_sep, t
from . import theme


class MeshDialog(QtWidgets.QDialog):
    def __init__(self, parent, mesh, thickness, can_remove=False):
        super().__init__(parent)
        self.setWindowTitle(t("mesh.title"))
        self.thickness = thickness
        self.removing = False
        form = QtWidgets.QFormLayout()
        self.diameter = QtWidgets.QComboBox()
        for d in rm.DIAMETERS:
            self.diameter.addItem("Ø{}".format(d), d)
        self.diameter.setCurrentIndex(max(rm.DIAMETERS.index(mesh.diameter) if mesh.diameter in rm.DIAMETERS else 1, 0))
        self.spacing = QtWidgets.QComboBox()
        for s in rm.SPACINGS:
            self.spacing.addItem("{:.2f} m".format(s).replace(".", decimal_sep()), s)
        self.spacing.setCurrentIndex(min(range(len(rm.SPACINGS)), key=lambda k: abs(rm.SPACINGS[k] - mesh.spacing)))
        self.face = QtWidgets.QComboBox()
        for f in rm.FACES:
            self.face.addItem(t("mesh.face." + f), f)
        self.face.setCurrentIndex(rm.FACES.index(mesh.face) if mesh.face in rm.FACES else 0)
        self.cover = QtWidgets.QSpinBox()
        self.cover.setRange(10, 80)
        self.cover.setValue(round(mesh.cover * 1000))
        self.angle = QtWidgets.QSpinBox()
        self.angle.setRange(-90, 90)
        self.angle.setValue(round(mesh.angle))
        form.addRow(t("mesh.diameter"), self.diameter)
        form.addRow(t("mesh.spacing"), self.spacing)
        form.addRow(t("mesh.face"), self.face)
        form.addRow(t("mesh.cover"), self.cover)
        form.addRow(t("mesh.angle"), self.angle)
        self.checks = QtWidgets.QLabel()
        self.checks.setWordWrap(True)
        note = QtWidgets.QLabel(t("mesh.note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: {};".format(theme.C["note"]))
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        if can_remove:
            remove = buttons.addButton(t("mesh.remove"), QtWidgets.QDialogButtonBox.ButtonRole.DestructiveRole)
            remove.clicked.connect(self._remove)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(self.checks)
        lay.addWidget(note)
        lay.addWidget(buttons)
        for w in (self.diameter, self.spacing, self.face):
            w.currentIndexChanged.connect(self._update)
        for w in (self.cover, self.angle):
            w.valueChanged.connect(self._update)
        self._update()

    def mesh(self):
        return rm.Mesh(int(self.diameter.currentData()), float(self.spacing.currentData()), self.face.currentData(),
                       self.cover.value() / 1000.0, float(self.angle.value()))

    def _update(self, *_):
        lines = []
        for key, ok, values in rm.checks(self.mesh(), self.thickness):
            text = t("mesh.check." + key, **{k: ("{:.2f}" if key == "minimum" else "{:.0f}").format(v)
                                             .replace(".", decimal_sep()) for k, v in values.items()})
            colour = theme.C["ok"] if ok else theme.C["fail"]
            lines.append("<span style='color:{}'>{}</span> {}".format(colour, "✓" if ok else "✗", text))
        self.checks.setText("<br>".join(lines))

    def _remove(self):
        self.removing = True
        self.accept()
