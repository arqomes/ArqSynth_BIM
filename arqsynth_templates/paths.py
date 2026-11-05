"""Where the ArqSynth suite keeps what its programs share — a folder of its own, outside every program's installation
(an update never touches it):

- Windows: %APPDATA%\\ArqSynth
- macOS:   ~/Library/Application Support/ArqSynth
- Linux:   $XDG_CONFIG_HOME/ArqSynth (~/.config/ArqSynth)
- the Linux of Windows (WSL) — where ArqSynth BIM runs: the *Windows* folder (/mnt/c/Users/<you>/AppData/Roaming/
  ArqSynth), so that the suite's Windows programs (the Blender addon…) read the same templates.

ARQSYNTH_HOME, when set, is used instead (tests, a folder shared on a network).

    <suite folder>/templates/*.astpl      the templates
    <suite folder>/settings.json          each program's default template (and other shared settings)
"""

import os
import subprocess
import sys

SUITE = "ArqSynth"
TEMPLATES = "templates"
SETTINGS = "settings.json"
_found = {}


def in_wsl():
    """Running in the Linux of Windows (WSL)?"""
    if not sys.platform.startswith("linux"):
        return False
    try:
        with open("/proc/version", encoding="utf-8", errors="replace") as f:
            return "microsoft" in f.read().lower()
    except OSError:
        return False


def _windows_appdata_from_wsl():
    """The Windows %APPDATA% seen from WSL (/mnt/c/Users/…/AppData/Roaming), or None."""
    try:
        out = subprocess.run(["cmd.exe", "/c", "echo %APPDATA%"], cwd="/mnt/c", capture_output=True, timeout=8,
                             text=True, errors="replace").stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    if len(out) < 3 or out[1] != ":" or "%" in out:
        return None
    path = "/mnt/{}/{}".format(out[0].lower(), out[3:].replace("\\", "/"))
    return path if os.path.isdir(path) else None


def suite_dir():
    """The suite's shared folder (not made here: see ensure())."""
    own = os.environ.get("ARQSYNTH_HOME")
    if own:
        return os.path.abspath(os.path.expanduser(own))
    if "suite" not in _found:
        if sys.platform == "win32":
            base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
        elif sys.platform == "darwin":
            base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
        else:
            base = _windows_appdata_from_wsl() if in_wsl() else None
            base = base or os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
        _found["suite"] = os.path.join(base, SUITE)
    return _found["suite"]


def templates_dir(root=None):
    return os.path.join(root or suite_dir(), TEMPLATES)


def settings_file(root=None):
    return os.path.join(root or suite_dir(), SETTINGS)
