"""(0.362) The ArqSynth Presentation's test file for its importer (its scripts/test-bim-import.mts): the model for the
Presentation of a small house, written by this program — the contract between the two.

    python scripts/fixture_presentation.py <the Presentation's folder>/scripts/fixtures/arqsynth-bim-casa.glb

A room of 5 × 4 m on the ground floor (four 20 cm walls, a window, a slab), two walls on a floor above (at 3 m), a
named 3D view (the slabs hidden, a section box round half the room), a section across the room.

(0.363) And what the Presentation panel chooses: the section moved before the plans, reached by a cut, with the
construction effect (10 s), a caption and 8 s in the tour; the upper floor's plan left out; the 3D view the first
scene; a thumbnail of the general view (a small JPEG). (0.364) A room drawn in the ground floor's room; the general
view with the rising orbit (its own 14 s), the 3D view with the turn round the room (10 s) — made in that room.
(0.365) A light (a panel) in the room's ceiling, a pond (a slab of water) outside; the 3D view's sun on 21/12 at
10:00, through the day, its exposure 1,2, with a sky. (0.366) A partition with a door making a kitchen beside the
living room, the kitchen's door to outside: the rooms as labels and as the Virtual Walk (a flow through the inner door,
the walk starting in the kitchen).
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pylinalg as la  # noqa: E402

from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim, presentation, presentation_export  # noqa: E402
from arqbim.model.document import Document  # noqa: E402


def casa():
    """The house, its view and its section, in a new document."""
    doc = Document()
    spec = catalog.BY_KEY["parede_alv_20"]
    corners = [np.array(p) for p in ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 4.0, 0.0), (0.0, 4.0, 0.0))]
    walls = bim.add_wall_loop(doc, corners, spec)
    bim.add_opening(doc, walls[0], catalog.OPENING_BY_KEY["janela_120"], bim.wall_frame(doc, walls[0]), 1.5, -1)
    partition = bim.add_wall(doc, np.array((3.0, 0.0, 0.0)), np.array((3.0, 4.0, 0.0)), spec)
    door = catalog.OPENING_BY_KEY["porta_90"]
    bim.add_opening(doc, partition, door, bim.wall_frame(doc, partition), 2.0, -1)
    bim.add_opening(doc, walls[0], door, bim.wall_frame(doc, walls[0]), 4.0, -1)
    bim.add_slab(doc, np.array((0.0, 0.0, 2.8)), 5.0, 4.0, catalog.BY_KEY["laje_12"])
    upper = bim.add_storey(doc, "Piso 1", 3.0)
    for k in (0.0, 4.0):
        bim.add_wall(doc, np.array((0.0, k, 3.0)), np.array((5.0, k, 3.0)), spec, storey=upper)
    eye, focus = np.array((10.0, -8.0, 6.0)), np.array((1.2, 2.0, 1.0))
    back = (eye - focus) / np.linalg.norm(eye - focus)
    right = np.cross((0.0, 0.0, 1.0), back)
    right /= np.linalg.norm(right)
    turn = la.quat_from_mat(np.column_stack((right, np.cross(back, right), back)))
    doc.add_view3d({"position": tuple(eye), "rotation": tuple(float(q) for q in turn), "fov": 50.0, "width": 16.0,
                    "height": 9.0, "zoom": 1.0, "focus": focus},
                   {"hidden": ["IfcSlab"], "box": [[0.0, 0.0, 0.0], [2.5, 4.0, 3.0]]})
    doc.add_section(np.array((2.5, 2.0, 0.0)), np.array((0.0, 1.0, 0.0)))
    ground = next(g for g, _n, z in doc.storeys() if z == 0.0)
    bim.set_site_location(doc, 38.72, -9.14)                # (Lisbon: the sun of a day at an hour)
    bim.add_room(doc, (1.5, 2.0), "Sala", storey=ground)
    bim.add_room(doc, (4.0, 2.0), "Cozinha", storey=ground)
    bim.add_light(doc, (1.5, 2.0), "panel", storey=ground)
    pond = catalog.TypeSpec("lago", "slab", "Lago", "Pond", layers=(("agua", 0.10),))
    bim.add_slab(doc, np.array((6.0, 0.0, 0.0)), 2.0, 3.0, pond, storey=ground, function="acabamento")
    keys = [s.key for s in presentation.scenes(doc)]       # general, 3D view, plan, plan, section
    data = presentation.ordered(doc.presentation, [keys[0], keys[1], keys[4], keys[2], keys[3]])
    data = presentation.with_initial(data, keys[1])
    data = presentation.changed(data, keys[3], hidden=True)
    data = presentation.changed(data, keys[4], transition="cut", effect="construction", effect_s=10,
                                caption="O corte pela sala, de nascente para poente.", seconds=8)
    data = presentation.changed(data, keys[0], move="orbit_rising")
    data = presentation.changed(data, keys[1], move="int_orbit_full", move_s=10, sun_day=355, sun_minutes=600,
                                sun_animate="day", exposure=1.2, sky=True)
    doc.set_presentation(data)
    return doc, {keys[0]: thumbnail()}


def thumbnail():
    """A small JPEG (the thumbnail of a scene, as the window makes them): 32 × 18, sky blue."""
    from PySide6 import QtCore, QtGui
    app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication(["fixture"])  # noqa: F841 (Qt's images need it)
    image = QtGui.QImage(32, 18, QtGui.QImage.Format.Format_RGB888)
    image.fill(QtGui.QColor("#9cc2ff"))
    data = QtCore.QByteArray()
    buffer = QtCore.QBuffer(data)
    buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "JPG", 80)
    buffer.close()
    return bytes(data)


def panorama_picture():
    """(0.368) A small equirectangular JPEG (a panorama, as Render ▸ Panorama 360° makes them): 64 × 32, the sky
    above the horizon, the floor under it."""
    from PySide6 import QtCore, QtGui
    app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication(["fixture"])  # noqa: F841
    image = QtGui.QImage(64, 32, QtGui.QImage.Format.Format_RGB888)
    image.fill(QtGui.QColor("#9cc2ff"))
    painter = QtGui.QPainter(image)
    painter.fillRect(0, 16, 64, 16, QtGui.QColor("#b8a58c"))
    painter.end()
    data = QtCore.QByteArray()
    buffer = QtCore.QBuffer(data)
    buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "JPG", 80)
    buffer.close()
    return bytes(data)


def package(doc, thumbs, path):
    """(0.367) The package of the house (its ZIP), as the window writes it: the GLB, the ground floor's plan on an A3
    sheet as a single-page PDF with its two rooms as zones of the page. (0.368) A 360° panorama taken in the living
    room (at 1,5 × 2 m, eye height): a point of that page."""
    import tempfile

    from arqbim.model import drawings, gltf_export, presentation_package
    from arqbim.model import sheets as sheets_model
    from arqbim.ui import pdf
    ground = next(g for g, _n, z in doc.storeys() if z == 0.0)
    doc.make_sheets([("Planta do Térreo", [("plan", ground)])], "A3", "full")
    sheet = doc.sheets[-1]
    drawing = drawings.plan(doc, ground, "Planta do Térreo")
    [frame] = sheets_model.layout(sheet, [sheets_model.extent(drawing)],
                                  [doc.view_settings(("plan", ground)).scale])
    block = sheets_model.title_texts(doc.title_block, sheet.name, "A-01", "Casa")
    with tempfile.TemporaryDirectory() as folder:
        one = os.path.join(folder, "folha.pdf")
        pdf.write_sheets(one, [(sheet, [(drawing, frame, None)], block)], "ArqSynth BIM")
        with open(one, "rb") as fh:
            sheet_pdf = fh.read()
    name = presentation_package.file_name("A-01", sheet.name, set())
    size = sheet.size()
    pages = [{"id": presentation_package.PAGE_ID + sheet.uid, "title": "A-01 " + sheet.name, "file": name,
              "size": [float(size[0]), float(size[1])],
              "zones": presentation_package.page_zones(doc, [(drawing, frame, ("plan", ground))], size)}]
    shot = {"uid": "f1c7a0e3panorama0000000000000001", "name": "Panorama da sala",
            "file": "Casa - panoramas/sala.jpg", "eye": [1.5, 2.0, 1.6], "forward": [0.0, 1.0], "storey": ground}
    points = presentation_package.panorama_points([(drawing, frame, ("plan", ground))], size, [shot])
    entries = presentation_package.panorama_entries([shot], {pages[0]["id"]: points})
    gltf, binary, description = presentation_export.package(doc, "Casa", thumbs)
    return presentation_package.write(path, gltf_export.glb(gltf, binary), description, pages, {name: sheet_pdf},
                                      entries, {entries[0]["file"]: panorama_picture()})


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "exemplos", "arqsynth-bim-casa.glb")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    doc, thumbs = casa()
    print(presentation_export.export(doc, path, "Casa", thumbnails=thumbs), path)
    zipped = os.path.join(os.path.dirname(os.path.abspath(path)), "arqsynth-bim-pacote.zip")      # (0.367)
    found = package(doc, thumbs, zipped)
    print(len(found["package"]["pages"]), "folha(s),", sum(len(p["zones"]) for p in found["package"]["pages"]),
          "zona(s),", len(found["package"]["panoramas"]), "panorama(s)", zipped)
