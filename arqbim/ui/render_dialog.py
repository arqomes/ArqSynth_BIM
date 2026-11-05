"""(0.343) Render ▸ Realistic render: its size, quality, lighting (the sun and the sky; and the lights on; the lights
at night), its sun (the view style's, or the site's on a day at an hour), its exposure and whether its grain is
filtered out (RenderSetup), then its window (RenderWindow) — the render in a process of its own
(render/path_tracer.py: Mitsuba 3, path tracing), the picture getting finer pass by pass, how far it got and how long
it has taken; Stop (the process ended, the picture as far as it got kept), Save (PNG or JPEG), Close. The program goes
on answering meanwhile: several renders may be open."""

import json
import os
import shutil
from datetime import datetime

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import sun as core_sun
from ..i18n import decimal_sep, t
from ..model.render_scene import LIGHTINGS
from . import theme

# (name, width in px): smaller than the image of the view's — a render's time grows with its pixels
SIZES = (("hd", 1280), ("full_hd", 1920), ("qhd", 2560), ("uhd", 3840))
QUALITIES = ("draft", "normal", "high")
POLL_MS = 300
TEMP_PREFIX = "arqsynth_render_"        # a render's temporary folder (its scene, its picture): gone when its window is


class RenderSetup(QtWidgets.QDialog):
    """The render's width (its height the view's proportion: size_of(width) -> (w, h)), quality, lighting, sun —
    `style_sun` (azimuth, altitude: the view style's) or the `site`'s (latitude, longitude; None, None: not known) on
    a day at an hour —, exposure and grain filter."""

    last = {"width": 1280, "quality": "normal", "lighting": "sun_lights", "sun": "style", "when": None,
            "exposure": 0.0, "clean": True}

    def __init__(self, parent, size_of, style_sun=(213.0, 47.0), site=(None, None)):
        super().__init__(parent)
        self.setWindowTitle(t("render.title"))
        self._size_of = size_of
        self.style_sun = tuple(float(v) for v in style_sun)
        self.site = site
        form = QtWidgets.QFormLayout(self)
        note = QtWidgets.QLabel(t("render.note"))
        note.setWordWrap(True)
        note.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        form.addRow(note)
        self.width = QtWidgets.QComboBox()
        for name, width in SIZES:
            self.width.addItem(t("render.size." + name, w=width), width)
        self.width.setCurrentIndex(max(self.width.findData(self.last["width"]), 0))
        self.size_text = QtWidgets.QLabel()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.width)
        row.addWidget(self.size_text, 1)
        form.addRow(t("render.size"), row)
        self.quality = QtWidgets.QComboBox()
        for key in QUALITIES:
            self.quality.addItem(t("render.quality." + key), key)
        self.quality.setCurrentIndex(max(self.quality.findData(self.last["quality"]), 0))
        form.addRow(t("render.quality"), self.quality)
        self.lighting = QtWidgets.QComboBox()
        for key in LIGHTINGS:
            self.lighting.addItem(t("render.lighting." + key), key)
        self.lighting.setCurrentIndex(max(self.lighting.findData(self.last["lighting"]), 0))
        form.addRow(t("render.lighting"), self.lighting)
        # its sun: the view style's, or the site's on a day at an hour (the site's clock, its hours ahead of UTC)
        self.sun_from = QtWidgets.QComboBox()
        self.sun_from.addItem(t("render.sun.style", az=round(self.style_sun[0]), alt=round(self.style_sun[1])),
                              "style")
        self.sun_from.addItem(t("render.sun.site"), "site")
        known = site is not None and site[0] is not None and site[1] is not None
        if not known:
            self.sun_from.model().item(1).setEnabled(False)
            self.sun_from.setToolTip(t("render.sun.no_site"))
        self.sun_from.setCurrentIndex(1 if known and self.last["sun"] == "site" else 0)
        form.addRow(t("render.sun"), self.sun_from)
        when = self.last["when"] or datetime.combine(datetime.now().date(), datetime.min.time()).replace(hour=15)
        self.when = QtWidgets.QDateTimeEdit(QtCore.QDateTime(QtCore.QDate(when.year, when.month, when.day),
                                                             QtCore.QTime(when.hour, when.minute)))
        self.when.setCalendarPopup(True)
        self.when.setDisplayFormat("dd/MM/yyyy  HH:mm")
        self.zone = QtWidgets.QDoubleSpinBox()
        self.zone.setRange(-12.0, 14.0)
        self.zone.setDecimals(1)
        self.zone.setSingleStep(0.5)
        self.zone.setPrefix("UTC ")
        self.zone.setToolTip(t("vstyle.sun_utc"))
        offset = when.astimezone().utcoffset()               # (the computer's clock on that day: summer time)
        self.zone.setValue(offset.total_seconds() / 3600.0 if offset is not None else 0.0)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.when, 1)
        row.addWidget(self.zone)
        form.addRow(t("render.when"), row)
        self.sun_text = QtWidgets.QLabel()
        self.sun_text.setWordWrap(True)
        self.sun_text.setStyleSheet("QLabel { color: %s; }" % theme.C["note"])
        form.addRow("", self.sun_text)
        self.exposure = QtWidgets.QDoubleSpinBox()
        self.exposure.setRange(-3.0, 3.0)
        self.exposure.setSingleStep(0.5)
        self.exposure.setDecimals(1)
        self.exposure.setSuffix(" EV")
        self.exposure.setValue(float(self.last["exposure"]))
        self.exposure.setToolTip(t("render.exposure_tip"))
        form.addRow(t("render.exposure"), self.exposure)
        self.clean = QtWidgets.QCheckBox(t("render.clean"))
        self.clean.setToolTip(t("render.clean_tip"))
        self.clean.setChecked(bool(self.last["clean"]))
        form.addRow("", self.clean)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText(t("render.start"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        self.width.currentIndexChanged.connect(lambda _i: self._sized())
        self.sun_from.currentIndexChanged.connect(lambda _i: self._sun_shown())
        self.when.dateTimeChanged.connect(lambda _d: self._sun_shown())
        self.zone.valueChanged.connect(lambda _v: self._sun_shown())
        self._sized()
        self._sun_shown()

    def _sized(self):
        w, h = self._size_of(self.width.currentData())
        mp = "{:.1f}".format(w * h / 1e6).replace(".", decimal_sep())
        self.size_text.setText(t("render.pixels", w=w, h=h, mp=mp))

    def sun(self):
        """(azimuth, altitude) of its sun as chosen."""
        if self.sun_from.currentData() == "site":
            return core_sun.position(self.site[0], self.site[1], self.when.dateTime().toPython(), self.zone.value())
        return self.style_sun

    def _sun_shown(self):
        by_site = self.sun_from.currentData() == "site"
        self.when.setEnabled(by_site)
        self.zone.setEnabled(by_site)
        azimuth, altitude = self.sun()
        self.sun_text.setText(t("render.sun_down") if altitude <= 0.0 else
                              t("render.sun_at", az=round(azimuth), alt=round(altitude)))

    def values(self):
        """{width (px), quality, lighting, sun (azimuth, altitude), exposure (EV), clean} as chosen — kept for the
        next time. A sun under the horizon: night (the lights)."""
        width, quality = int(self.width.currentData()), self.quality.currentData()
        lighting, sun = self.lighting.currentData(), self.sun()
        RenderSetup.last = {"width": width, "quality": quality, "lighting": lighting,
                            "sun": self.sun_from.currentData(), "when": self.when.dateTime().toPython(),
                            "exposure": self.exposure.value(), "clean": self.clean.isChecked()}
        return {"width": width, "quality": quality, "lighting": "night" if sun[1] <= 0.0 else lighting,
                "sun": tuple(sun), "exposure": self.exposure.value(), "clean": self.clean.isChecked()}


class RenderWindow(QtWidgets.QDialog):
    """A render's window: `command` (path_tracer.command) run, `picture` (its PNG) shown as it gets finer; save_to:
    the path its Save proposes (without its extension)."""

    def __init__(self, parent, command, picture, save_to, cwd=None):
        super().__init__(parent)
        self.setWindowTitle(t("render.window"))
        self.setModal(False)
        self.command, self.picture, self.save_to, self.cwd = command, picture, save_to, cwd
        self.state = {}                 # the render's last progress (path_tracer's JSON)
        self.stopped = False
        self.on_finished = None         # (0.368) callable(picture): called once the render has finished (not stopped)
        self._seen = None               # (the picture's time when last shown)
        layout = QtWidgets.QVBoxLayout(self)
        self.view = QtWidgets.QLabel(t("render.starting"))
        self.view.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.view.setMinimumSize(480, 270)
        self.view.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Ignored)
        self.view.setStyleSheet("QLabel { background: %s; }" % theme.C["canvas"])
        layout.addWidget(self.view, 1)
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        self.status = QtWidgets.QLabel()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.progress, 1)
        row.addWidget(self.status)
        layout.addLayout(row)
        buttons = QtWidgets.QHBoxLayout()
        self.stop_button = QtWidgets.QPushButton(t("render.stop"))
        self.stop_button.clicked.connect(self.stop)
        self.save_button = QtWidgets.QPushButton(t("render.save"))
        self.save_button.clicked.connect(lambda: self.save())
        self.save_button.setEnabled(False)
        close = QtWidgets.QPushButton(t("elprop.close"))
        close.clicked.connect(self.close)
        buttons.addWidget(self.stop_button)
        buttons.addStretch(1)
        buttons.addWidget(self.save_button)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(980, 640)
        self.process = QtCore.QProcess(self)
        self.process.setProcessChannelMode(QtCore.QProcess.ProcessChannelMode.MergedChannels)
        self.process.finished.connect(self._ended)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(POLL_MS)
        self.timer.timeout.connect(self.poll)

    def start(self):
        if self.cwd:
            self.process.setWorkingDirectory(self.cwd)
        env = QtCore.QProcessEnvironment.systemEnvironment()
        env.insert("QT_QPA_PLATFORM", "offscreen")
        self.process.setProcessEnvironment(env)
        self.process.start(self.command[0], self.command[1:])
        self.timer.start()

    def running(self):
        return self.process.state() != QtCore.QProcess.ProcessState.NotRunning

    def finished(self):
        return bool(self.state.get("finished"))

    def poll(self):
        """The render's progress read, its picture shown again when it changed."""
        try:
            with open(self.picture + ".json", encoding="utf-8") as fh:
                self.state = json.load(fh)
        except (OSError, ValueError):
            pass
        if self.state:
            done, of = int(self.state.get("done", 0)), max(int(self.state.get("of", 1)), 1)
            self.progress.setValue(int(100 * done / of))
            self.status.setText(t("render.progress", n=done, of=of, s=_clock(self.state.get("seconds", 0.0)),
                                  spp=int(self.state.get("samples", 0))))
        try:
            when = os.path.getmtime(self.picture)
        except OSError:
            return
        if when != self._seen:
            self._seen = when
            self._show()

    def _show(self):
        image = QtGui.QImage(self.picture)
        if image.isNull():
            return
        self.image = image
        self.view.setPixmap(QtGui.QPixmap.fromImage(image).scaled(
            self.view.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation))
        self.save_button.setEnabled(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, "image", None) is not None:
            self.view.setPixmap(QtGui.QPixmap.fromImage(self.image).scaled(
                self.view.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation))

    def _ended(self, code, _status):
        self.poll()
        self.timer.stop()
        self.stop_button.setEnabled(False)
        if self.finished():
            self.status.setText(t("render.done", s=_clock(self.state.get("seconds", 0.0)),
                                  spp=int(self.state.get("samples", 0))))
            if self.on_finished is not None:
                self.on_finished(self.picture)
        elif self.stopped:
            self.status.setText(t("render.stopped", n=int(self.state.get("done", 0)), of=int(self.state.get("of", 0))))
        else:
            said = bytes(self.process.readAll()).decode("utf-8", "replace").strip().splitlines()
            self.status.setText(t("render.failed", e=said[-1] if said else code))

    def stop(self):
        """The render ended where it got: its picture so far kept."""
        if self.running():
            self.stopped = True
            self.process.kill()

    def save(self, path=None):
        """Its picture written (PNG or JPEG — asked when not given). Returns its path, or None."""
        if getattr(self, "image", None) is None:
            return None
        if path is None:
            path, chosen = QtWidgets.QFileDialog.getSaveFileName(self, t("render.save"), self.save_to + ".png",
                                                                 t("image.filter"))
            if not path:
                return None
            if not path.lower().endswith((".png", ".jpg", ".jpeg")):
                path += ".jpg" if "jpg" in chosen.lower() else ".png"
        jpeg = path.lower().endswith((".jpg", ".jpeg"))
        return path if self.image.save(path, "JPEG" if jpeg else "PNG", 92 if jpeg else -1) else None

    def closeEvent(self, event):
        self.stop()
        self.process.waitForFinished(2000)
        self.timer.stop()
        folder = os.path.dirname(self.picture)           # (0.347) its scene and picture: not left in the temporary
        if os.path.basename(folder).startswith(TEMP_PREFIX):     # folder (its Save copies the picture elsewhere)
            shutil.rmtree(folder, ignore_errors=True)
        super().closeEvent(event)


def _clock(seconds):
    s = int(round(float(seconds)))
    return "{}:{:02d}".format(s // 60, s % 60)
