"""Application entry point:  python -m arqbim"""

import logging
import os
import sys
import traceback

from .paths import local_base, user_dir

APP_NAME = "ArqSynth BIM"                # the brand (0.77; until 0.76: ArqBIM)
LOG_DIR = user_dir(local_base())


def _setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(filename=os.path.join(LOG_DIR, "arqbim.log"), level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _excepthook(exc_type, exc, tb):
    text = "".join(traceback.format_exception(exc_type, exc, tb))
    logging.error("Unhandled exception:\n%s", text)
    sys.__stderr__ and sys.__stderr__.write(text)
    from PySide6 import QtWidgets
    if QtWidgets.QApplication.instance() is not None:
        QtWidgets.QMessageBox.critical(
            None, APP_NAME,
            "Ocorreu um erro inesperado. O programa continua aberto.\n\n"
            "Detalhes guardados em:\n{}\n\n{}".format(os.path.join(LOG_DIR, "arqbim.log"), exc))


def _startup_failed(exc):
    """The window could not be made: say so (not "it stays open"), and why when Windows blocked a file."""
    text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logging.error("Could not start:\n%s", text)
    sys.__stderr__ and sys.__stderr__.write(text)
    from PySide6 import QtWidgets
    _app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    why = ""
    if "Application Control" in str(exc):
        why = ("O Windows (Controlo Inteligente de Aplicações / Smart App Control) bloqueou um ficheiro de uma "
               "biblioteca do programa, por não estar assinado. Não é um problema do seu projeto. Feche esta "
               "mensagem e abra o ArqSynth BIM outra vez; se continuar, diga qual é o ficheiro (abaixo).\n\n")
    QtWidgets.QMessageBox.critical(
        None, APP_NAME, "O ArqSynth BIM não conseguiu abrir.\n\n{}Detalhes guardados em:\n{}\n\n{}".format(
            why, os.path.join(LOG_DIR, "arqbim.log"), exc))


def _application():
    from PySide6 import QtWidgets  # Qt must be imported before rendercanvas.qt
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    from .i18n import lang
    if lang() == "pt":
        from .ui import qt_portuguese
        qt_portuguese.install(app)            # (0.330: Qt's own buttons and windows in Portuguese of Portugal)
    from .ui import brand, theme
    theme.apply(theme.saved())                # (0.338: the theme chosen on this computer — light or dark)
    icon = brand.app_icon()
    if icon is not None:
        app.setWindowIcon(icon)
    return app


def create_window(splash=None):
    """The application and its window; `splash` (the starting screen) says what is being loaded."""
    app = _application()
    from .i18n import t
    if splash is not None:
        splash.say(t("splash.engine"))
    from .ui.main_window import MainWindow
    if splash is not None:
        splash.say(t("splash.window"))
    return app, MainWindow()


def _windows_taskbar():
    """On Windows, the program's own button on the taskbar (with its icon), not Python's."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ArqSynth.BIM")
    except (AttributeError, OSError):
        pass


def main():
    _setup_logging()
    sys.excepthook = _excepthook
    _windows_taskbar()
    splash = None
    try:
        _application()
        from . import __version__
        from .i18n import t
        from .ui.brand import Splash
        splash = Splash(APP_NAME, t("splash.version", v=__version__))
        splash.show()
        splash.say(t("splash.engine"))
        app, win = create_window(splash)
    except Exception as exc:                  # (e.g. a library file blocked by Windows)
        if splash is not None:
            splash.close()
        _startup_failed(exc)
        sys.exit(1)
    win.showMaximized()
    win.show_start_page()                     # (0.387) the start page first
    splash.finish(win)
    # We own the QApplication, so we run Qt's loop ourselves
    # (rendercanvas' loop.run() returns immediately in that case).
    sys.exit(app.exec())
