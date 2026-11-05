"""(0.329) Export ▸ Image of the view, as Revit's «Exportar imagem»: how wide it is — Full HD, 2K, 4K, an A4 or A3 sheet
across at 300 ppp, the window's own width, or typed —, its height from the view's proportion (what is seen is what is
exported), and its background: the view's, white, or transparent (PNG only). The window draws it
(Viewport.render_image) and writes it (save_image)."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import decimal_sep, t

# (name, width in px); an A sheet across at 300 ppp: written so (its dots per inch), it prints at that size
SIZES = (("full_hd", 1920), ("qhd", 2560), ("uhd", 3840), ("a4", 3508), ("a3", 4961))
PRINT_DPI = 300
PRINT_WIDTHS = {3508, 4961}
BACKGROUNDS = ("view", "white", "transparent")
JPEG_QUALITY = 92


class ImageDialog(QtWidgets.QDialog):
    """The image's size and background. size_of(width) -> (width, height): the view's (Viewport.image_size)."""

    last = {"width": 1920, "background": None}      # (what was chosen the last time, in this session)

    def __init__(self, parent, size_of, window_width, cutting=False):
        super().__init__(parent)
        self.setWindowTitle(t("imgdlg.title"))
        self._size_of = size_of
        form = QtWidgets.QFormLayout(self)
        note = QtWidgets.QLabel(t("imgdlg.note"))
        note.setWordWrap(True)
        form.addRow(note)
        self.preset = QtWidgets.QComboBox()
        self._widths = [w for _n, w in SIZES] + [int(window_width), None]
        for name, width in SIZES:
            self.preset.addItem(t("imgdlg.size." + name, w=width))
        self.preset.addItem(t("imgdlg.size.window", w=int(window_width)))
        self.preset.addItem(t("imgdlg.size.other"))
        form.addRow(t("imgdlg.size"), self.preset)
        self.width = QtWidgets.QSpinBox()
        self.width.setRange(320, size_of(10 ** 6)[0])
        self.width.setSuffix(" px")
        self.width.setSingleStep(100)
        self.size_text = QtWidgets.QLabel()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.width)
        row.addWidget(self.size_text, 1)
        form.addRow(t("imgdlg.width"), row)
        self.background = QtWidgets.QComboBox()
        for key in BACKGROUNDS:
            self.background.addItem(t("imgdlg.bg." + key), key)
        form.addRow(t("imgdlg.background"), self.background)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText(t("imgdlg.export"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        self.preset.currentIndexChanged.connect(self._preset_chosen)
        self.width.valueChanged.connect(self._width_typed)
        # (a plan or a section on white, as on paper; the 3D view on its sky — unless chosen otherwise before)
        chosen = self.last["background"] or ("white" if cutting else "view")
        self.background.setCurrentIndex(BACKGROUNDS.index(chosen))
        self.width.setValue(int(self.last["width"]))
        self._width_typed(self.width.value())

    def _preset_chosen(self, k):
        width = self._widths[k] if 0 <= k < len(self._widths) else None
        if width is not None and width != self.width.value():
            self.width.setValue(width)

    def _width_typed(self, width):
        w, h = self._size_of(width)
        mp = "{:.1f}".format(w * h / 1e6).replace(".", decimal_sep())
        self.size_text.setText(t("imgdlg.pixels", w=w, h=h, mp=mp))
        k = self._widths.index(width) if width in self._widths else len(self._widths) - 1
        if k != self.preset.currentIndex():
            self.preset.blockSignals(True)
            self.preset.setCurrentIndex(k)
            self.preset.blockSignals(False)

    def values(self):
        """(width in px, background) as chosen — kept for the next time."""
        width, background = self.width.value(), self.background.currentData()
        ImageDialog.last = {"width": width, "background": background}
        return width, background


def save_image(path, rgba):
    """Write an (H, W, 4) RGBA image as PNG (its transparency kept) or JPEG (on white, without it); an A sheet's width
    with PRINT_DPI written in it. True if written."""
    import numpy as np
    rgba = np.ascontiguousarray(rgba, dtype=np.uint8)
    h, w = rgba.shape[:2]
    image = QtGui.QImage(rgba.data, w, h, 4 * w, QtGui.QImage.Format.Format_RGBA8888)
    jpeg = path.lower().endswith((".jpg", ".jpeg"))
    if jpeg:
        flat = QtGui.QImage(w, h, QtGui.QImage.Format.Format_RGB888)
        flat.fill(QtCore.Qt.GlobalColor.white)
        painter = QtGui.QPainter(flat)
        painter.drawImage(0, 0, image)
        painter.end()
        image = flat
    else:
        image = image.copy()                 # (its own pixels: rgba may go before Qt writes them)
    if w in PRINT_WIDTHS:
        dots = round(PRINT_DPI / 0.0254)
        image.setDotsPerMeterX(dots)
        image.setDotsPerMeterY(dots)
    return image.save(path, "JPEG" if jpeg else "PNG", JPEG_QUALITY if jpeg else -1)
