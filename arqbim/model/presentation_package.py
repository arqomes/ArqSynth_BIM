"""(0.367) The package for the ArqSynth Presentation (PLANO, the Presentation's step 7): one ZIP with all that goes —
the model (its GLB, the presentation in it: model/presentation_export.py) and the sheets as plan pages, a single-page
PDF each with the rooms on its plans as zones of the page — read by the Presentation's «Import from ArqSynth BIM»,
which makes the 3D page from the GLB and a plan page from each PDF.

The manifest (manifest.json) is the brand's handoff envelope, as the GLB's description (its target the
Presentation, its source the BIM, its checksum over the rest), with `package`: {schema, model, pages: [{id, title,
file, size [w, h] mm, zones: [{room, name, number, area, kind, points [[x, y]], label [x, y]}]}]} — the zones'
points in hundredths of the page, x from its left, y from its top (the Presentation's plan layers' own measure). A
page is known by its sheet's uid («bim_sheet_…»): sent again, the Presentation updates that page. Pure Python (the
PDFs are made by the window, ui/pdf.py)."""

import json
import os
import re
import zipfile

import numpy as np

from . import presentation as presentation_model
from . import presentation_export

MANIFEST = "manifest.json"
MODEL = "modelo.glb"
PAGES = "folhas"
SCHEMA = 1
PAGE_ID = "bim_sheet_"


def to_page(point, drawing_middle, frame, size):
    """A point of a plan (the model's x, y in metres) on its sheet, in hundredths of the page: as ui/pdf.paint_drawing
    places the drawing (its middle at the frame's centre, at 1:scale, y down)."""
    cx, cy = frame.centre
    x = cx + (float(point[0]) - float(drawing_middle[0])) * 1000.0 / frame.scale
    y = cy - (float(point[1]) - float(drawing_middle[1])) * 1000.0 / frame.scale
    return [round(x / float(size[0]) * 100.0, 3), round(y / float(size[1]) * 100.0, 3)]


def page_zones(doc, placed, size, rooms=None):
    """The rooms of the plans placed on a sheet as zones of its page. placed: [(drawing, Frame, view key)]; size:
    (w, h) mm of the paper. A room whose middle is outside its plan's drawing (cropped away) is left out."""
    from . import camera_moves
    rooms = presentation_model.spaces(doc) if rooms is None else rooms
    out = []
    for drawing, frame, view in placed:
        if not view or view[0] != "plan" or hasattr(drawing, "paper_size"):
            continue
        box = drawing.bounds()
        if box is None:
            continue
        lo, hi = (np.asarray(c, dtype=float) for c in box)
        middle = (lo + hi) / 2.0
        for r in rooms:
            if r.get("storey") != view[1] or len(r["outline"]) < 3:
                continue
            inner = camera_moves.room_from_polygon([(x, y) for x, y in r["outline"]], 0.0, float(r["height"]))
            if inner is None:
                continue
            centre = (inner.center[0], inner.center[2])
            if not (lo[0] - 1e-6 <= centre[0] <= hi[0] + 1e-6 and lo[1] - 1e-6 <= centre[1] <= hi[1] + 1e-6):
                continue
            name = r.get("name") or r.get("number") or ""
            out.append({"room": r["guid"], "name": name, "number": r.get("number", ""),
                        "area": round(float(r.get("area") or 0.0) or presentation_model._area(r["outline"]), 2),
                        "kind": presentation_model.room_kind(name, r.get("external")),
                        "points": [to_page(p, middle, frame, size) for p in r["outline"]],
                        "label": to_page(centre, middle, frame, size)})
    return out


PANORAMAS = "panoramas"
PANORAMA_ID = "bim_pano_"


def panorama_points(placed, size, panoramas):
    """(0.368) Where the panoramas are on a sheet's plans: [(panorama uid, x, y)] in hundredths of the page — each on
    the plans of its storey, where its eye is, if that is inside the plan's drawing. placed as page_zones'."""
    out = []
    for drawing, frame, view in placed:
        if not view or view[0] != "plan" or hasattr(drawing, "paper_size"):
            continue
        box = drawing.bounds()
        if box is None:
            continue
        lo, hi = (np.asarray(c, dtype=float) for c in box)
        middle = (lo + hi) / 2.0
        for p in panoramas:
            x, y = float(p["eye"][0]), float(p["eye"][1])
            if p.get("storey") == view[1] and lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]:
                out.append((p["uid"], *to_page((x, y), middle, frame, size)))
    return out


def panorama_entries(panoramas, placements):
    """The manifest's panoramas: [{id, name, file, placements: [{page, x, y}]}] — placements: {page id: [(uid, x,
    y)]}."""
    out = []
    for p in panoramas:
        where = [{"page": page, "x": x, "y": y} for page, points in placements.items()
                 for uid, x, y in points if uid == p["uid"]]
        out.append({"id": PANORAMA_ID + p["uid"], "name": p["name"], "file": "{}/{}.jpg".format(PANORAMAS, p["uid"]),
                    "placements": where})
    return out


def file_name(number, name, used):
    """A page's file in the package: «folhas/A-01 Planta — Térreo.pdf» (as ui/pdf.file_name names a sheet's file),
    each once."""
    text = " ".join(p for p in (str(number or "").strip(), str(name or "").strip()) if p) or "folha"
    base = re.sub(r'[\\/:*?"<>|]+', "-", text)
    candidate, k = base, 1
    while candidate.lower() in used:
        k += 1
        candidate = "{} ({})".format(base, k)
    used.add(candidate.lower())
    return "{}/{}.pdf".format(PAGES, candidate)


def manifest(description, pages, panoramas=()):
    """The package's manifest: the GLB's envelope (its target, source, disclaimer) with `package` in place of the
    model's description, its checksum over the rest; (0.368) the panoramas (panorama_entries)."""
    out = {k: v for k, v in description.items() if k not in ("presentation", "checksum")}
    out["package"] = {"schema": SCHEMA, "model": MODEL, "pages": list(pages), "panoramas": list(panoramas)}
    out["checksum"] = presentation_export.checksum(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    return out


def write(path, glb, description, pages, pdfs, panoramas=(), pictures=None):
    """The package at `path`: the GLB's bytes, the manifest (pages: as `manifest` takes them, their `file` in
    pdfs: {file: PDF bytes}; panoramas: panorama_entries', their `file` in pictures: {file: JPEG bytes}). Returns the
    manifest."""
    found = manifest(description, pages, panoramas)
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(MANIFEST, json.dumps(found, ensure_ascii=False, indent=1))
        z.writestr(zipfile.ZipInfo(MODEL), glb, compress_type=zipfile.ZIP_STORED)    # (a GLB hardly shrinks)
        for page in pages:
            z.writestr(page["file"], pdfs[page["file"]])
        for p in panoramas:                                                        # (a JPEG does not shrink)
            z.writestr(zipfile.ZipInfo(p["file"]), (pictures or {})[p["file"]], compress_type=zipfile.ZIP_STORED)
    return found


def read(path):
    """(manifest, {name: bytes}) of a package written here, or None (not one)."""
    try:
        with zipfile.ZipFile(path) as z:
            found = json.loads(z.read(MANIFEST).decode("utf-8"))
            files = {n: z.read(n) for n in z.namelist() if n != MANIFEST}
    except (OSError, KeyError, ValueError, zipfile.BadZipFile):
        return None
    if not isinstance(found, dict) or found.get("format") != presentation_export.FORMAT:
        return None
    return found, files
