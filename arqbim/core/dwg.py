"""DWG read (0.286; the owner's go-ahead to install the converter): a DWG — AutoCAD's own, closed format — turned
into a DXF by the Open Design Alliance's free ODA File Converter (its command line, run apart from the program), and
that DXF read as any other (core/cad, core/dxf_read). The DXF is kept in the user's folder (~/.arqsynth/dwg), named
by the DWG's path, size and time: made again only when the DWG changes.

The converter's command line: ODAFileConverter <in folder> <out folder> <version> <type> <recurse> <audit> [filter]
— it converts every file of the folder, so the DWG is copied alone into a folder of its own first."""

import glob
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

PLACES = ("/usr/bin/ODAFileConverter", "/usr/local/bin/ODAFileConverter",
          r"C:\Program Files\ODA\ODAFileConverter*\ODAFileConverter.exe")
TIMEOUT = 300                  # s: a big drawing


def converter():
    """The ODA File Converter's program, or None."""
    found = shutil.which("ODAFileConverter")
    if found:
        return found
    for pattern in PLACES:
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[-1]
    return None


def _env():
    """The converter's environment: it is a Qt program that brings only Qt's X11 (xcb) platform — on Linux it is
    told to use it (whatever this program was started with), on Windows its own."""
    env = dict(os.environ)
    if sys.platform.startswith("linux"):
        env["QT_QPA_PLATFORM"] = "xcb"
    else:
        env.pop("QT_QPA_PLATFORM", None)
    return env


def cache_folder():
    folder = os.path.join(os.path.expanduser("~"), ".arqsynth", "dwg")
    os.makedirs(folder, exist_ok=True)
    return folder


def to_dxf(path, version="ACAD2018"):
    """The DXF of a DWG (its path), converted once while the DWG is unchanged. ValueError("dwg_converter") when the
    converter is not installed, ("dwg_convert") when it gives nothing."""
    exe = converter()
    if exe is None:
        raise ValueError("dwg_converter")
    stat = os.stat(path)
    key = hashlib.sha1("{}|{}|{}".format(os.path.abspath(path), stat.st_size, stat.st_mtime_ns).encode()).hexdigest()
    out = os.path.join(cache_folder(), key[:20] + ".dxf")
    if os.path.exists(out):
        return out
    with tempfile.TemporaryDirectory() as tmp:
        source, target = os.path.join(tmp, "dwg"), os.path.join(tmp, "dxf")
        os.makedirs(source)
        os.makedirs(target)
        shutil.copy2(path, os.path.join(source, "desenho.dwg"))
        subprocess.run([exe, source, target, version, "DXF", "0", "1", "*.dwg"], env=_env(), timeout=TIMEOUT,
                       capture_output=True, check=False)
        made = [f for f in os.listdir(target) if f.lower().endswith(".dxf")]
        if not made:
            raise ValueError("dwg_convert")
        shutil.move(os.path.join(target, made[0]), out)
    return out


def from_dxf(path, out_path, version="ACAD2018"):
    """A DWG written from a DXF (to test, and to hand a drawing back in AutoCAD's format)."""
    exe = converter()
    if exe is None:
        raise ValueError("dwg_converter")
    with tempfile.TemporaryDirectory() as tmp:
        source, target = os.path.join(tmp, "dxf"), os.path.join(tmp, "dwg")
        os.makedirs(source)
        os.makedirs(target)
        shutil.copy2(path, os.path.join(source, "desenho.dxf"))
        subprocess.run([exe, source, target, version, "DWG", "0", "1", "*.dxf"], env=_env(), timeout=TIMEOUT,
                       capture_output=True, check=False)
        made = [f for f in os.listdir(target) if f.lower().endswith(".dwg")]
        if not made:
            raise ValueError("dwg_convert")
        shutil.move(os.path.join(target, made[0]), out_path)
    return out_path
