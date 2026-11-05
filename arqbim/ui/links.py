"""(0.387) Opening a web address or a folder from the program — in Windows' own browser and Explorer also when the
program runs in Linux on Windows (WSL), where there is no xdg-open: Windows' explorer.exe is called through WSL."""

import os
import shutil
import subprocess
import sys

from PySide6 import QtCore, QtGui


def in_wsl():
    """Running in Linux on Windows (WSL)?"""
    if not sys.platform.startswith("linux"):
        return False
    try:
        with open("/proc/version", encoding="utf-8") as f:
            return "microsoft" in f.read().lower()
    except OSError:
        return False


def _explorer():
    return shutil.which("explorer.exe") or next((p for p in ("/mnt/c/Windows/explorer.exe",
                                                             "/mnt/c/WINDOWS/explorer.exe") if os.path.exists(p)), None)


def _windows_path(path):
    """A WSL path as Windows sees it (/mnt/c/BIM → C:\\BIM), by wslpath; the path as it was if it cannot."""
    try:
        return subprocess.run(["wslpath", "-w", path], capture_output=True, text=True, timeout=5).stdout.strip() or path
    except (OSError, subprocess.SubprocessError):
        return path


def open_url(url):
    """A web address in the browser. False if it could not be opened (no address)."""
    url = str(url or "").strip()
    if not url:
        return False
    if in_wsl() and _explorer():
        subprocess.Popen([_explorer(), url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    return bool(QtGui.QDesktopServices.openUrl(QtCore.QUrl(url)))


def open_folder(path):
    """A folder in the file explorer (made first if it is not there)."""
    os.makedirs(path, exist_ok=True)
    if in_wsl() and _explorer():
        subprocess.Popen([_explorer(), _windows_path(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    return bool(QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path)))
