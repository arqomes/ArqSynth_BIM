"""Builds the Phase 1 acceptance house with the program's own commands and saves it.

    .venv\\Scripts\\python scripts\\casa_exemplo.py [output.ifc]
    .venv\\Scripts\\python scripts\\casa_exemplo.py --georreferenciada [output.ifc]

6 × 4 m, walls 20 cm × 2,80 m, concrete roof slab 12 cm, 2 doors, 4 windows.
--georreferenciada: the same house with its site 512 km E / 4 301 km N of the IFC origin
(as Revit's shared coordinates do), to try a model far from the origin.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from arqbim.core import sketch_geometry as sg  # noqa: E402
from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import AddObject, Document, SketchObject  # noqa: E402


def sketch_box(doc, x, y, z, dx, dy, dz):
    """Rectangle + Push/Pull, exactly as with the tools."""
    m = sg.rectangle_matrix(np.array((x, y, z), float), np.array((1.0, 0, 0)), np.array((0, 1.0, 0)))
    mesh = sg.rectangle_mesh(dx, dy)
    sg.push_pull(mesh, 0, m, dz)
    obj = SketchObject("Esboço", m, mesh)
    doc.execute(AddObject(obj))
    return obj.id


def build_house(doc):
    walls = [sketch_box(doc, 0, 0, 0, 6.0, 0.2, 2.8),      # south (front)
             sketch_box(doc, 0, 3.8, 0, 6.0, 0.2, 2.8),    # north (back)
             sketch_box(doc, 0, 0.2, 0, 0.2, 3.6, 2.8),    # west
             sketch_box(doc, 5.8, 0.2, 0, 0.2, 3.6, 2.8)]  # east
    slab = sketch_box(doc, 0, 0, 2.8, 6.0, 4.0, 0.12)
    south, north, west, east = bim.classify(doc, walls, catalog.BY_KEY["parede_alv_20"]).guids
    bim.classify(doc, [slab], catalog.BY_KEY["laje_12"])

    door90, door80, win = (catalog.OPENING_BY_KEY[k] for k in ("porta_90", "porta_80", "janela_120"))
    f = bim.wall_frame(doc, south)
    bim.add_opening(doc, south, door90, f, f.x0 + (f.length - door90.width) / 2, -1)   # front door, centred
    bim.add_opening(doc, south, win, bim.wall_frame(doc, south), 0.8, -1)
    bim.add_opening(doc, south, win, bim.wall_frame(doc, south), 4.0, -1)
    bim.add_opening(doc, north, door80, bim.wall_frame(doc, north), 1.0, -1)            # back door
    for wall in (west, east):
        f = bim.wall_frame(doc, wall)
        bim.add_opening(doc, wall, win, f, f.x0 + (f.length - win.width) / 2, -1)
    return {"walls": [south, north, west, east]}


FAR = (512345.0, 4301234.0, 0.0)      # m, a typical map position (UTM-like)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    far = "--georreferenciada" in sys.argv
    name = "casa_georreferenciada.ifc" if far else "casa_exemplo.ifc"
    out = args[0] if args else os.path.join(ROOT, "exemplos", name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    doc = Document()
    build_house(doc)
    if far:
        from arqbim.core.transform import translation
        site = doc.ifc.file.by_type("IfcSite")[0]
        doc.ifc._place(site, translation(FAR), should_transform_children=True)   # the whole house goes along
    doc.save(out)
    errors = doc.ifc.validate(express_rules=True)
    counts = {c: doc.ifc.count(c) for c in ("IfcWall", "IfcSlab", "IfcDoor", "IfcWindow", "IfcOpeningElement")}
    print(out, counts, "erros de validação:", len(errors))
