"""(0.466) The components' library, as SketchUp's Components panel (the owner: «Nessa aba quero uma biblioteca mesmo dos
componentes com miniaturas dos componentes assim como no Sketchup. Deve ser feita com as opções de visualização,
biblioteca local e web. No futuro os criadores poderão vender componentes dentro desse ecossistema»).

Three sources:
- the project's — its components (IFC types with their shape kept once), placed again with a click;
- the local library — a folder on this computer (Documents/ArqSynth/Biblioteca by default, another one chosen), its
  subfolders its categories: a component kept by ArqSynth is a small IFC file of its own (its type, shape, materials,
  properties — what Revit or another BIM program reads too); a SketchUp, Rhino, glTF / GLB, OBJ or STL file there is one
  as well (brought in as the Import ▸ 3D model does);
- the web — a catalogue (CATALOGUE: a JSON list of components with their miniature, author, licence, price and files)
  read from an address: the ArqSynth store, where creators will publish and sell components, when it opens.

Pure Python on the document (no Qt): the panel (ui/library_panel.py) shows, the main window acts."""

import json
import os
import re

ITEM_EXTENSIONS = (".ifc", ".skp", ".3dm", ".glb", ".gltf", ".obj", ".stl")
MODEL_EXTENSIONS = ITEM_EXTENSIONS[1:]                  # (the 3D files: brought in as a component when used)
FOLDER_NAME = os.path.join("ArqSynth", "Biblioteca")


def default_folder():
    """The local library's folder: Documents/ArqSynth/Biblioteca (made when first used)."""
    home = os.path.expanduser("~")
    docs = os.path.join(home, "Documents")
    if not os.path.isdir(docs):
        docs = os.path.join(home, "Documentos") if os.path.isdir(os.path.join(home, "Documentos")) else home
    return os.path.join(docs, FOLDER_NAME)


def listing(folder):
    """A library folder's contents: (its subfolders [(name, path)], its components [(name, path, extension)]) — each
    by name, the files ArqSynth can bring in only."""
    folders, items = [], []
    try:                                                # (by name without its extension: «Mesa» before «Mesa 2»)
        names = sorted(os.listdir(folder), key=lambda n: (os.path.splitext(n)[0].lower(), n.lower()))
    except OSError:
        return [], []
    for name in names:
        if name.startswith("."):
            continue
        path = os.path.join(folder, name)
        if os.path.isdir(path):
            folders.append((name, path))
            continue
        stem, ext = os.path.splitext(name)
        if ext.lower() in ITEM_EXTENSIONS:
            items.append((stem, path, ext.lower()))
    return folders, items


def file_name(name):
    """A component's name made a file's (the characters a file cannot have taken out)."""
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", str(name)).strip().strip(".")
    return clean or "Componente"


def free_path(folder, name, ext=".ifc"):
    """A path in `folder` for `name` that is not taken ("Cadeira.ifc", "Cadeira 2.ifc"…)."""
    base = file_name(name)
    path, n = os.path.join(folder, base + ext), 2
    while os.path.exists(path):
        path = os.path.join(folder, "{} {}{}".format(base, n, ext))
        n += 1
    return path


def save_component(doc, type_guid, folder, name=None):
    """A component of the project kept in the local library: a small IFC file of its own (its type with its shape,
    materials and properties). Returns its path."""
    from ..ifc.model import IfcModel
    type_ = doc.ifc.by_guid(type_guid)
    if type_ is None:
        raise ValueError("no component")
    os.makedirs(folder, exist_ok=True)
    path = free_path(folder, name or type_.Name or "Componente")
    out = IfcModel.new(name=type_.Name or "Componente")
    out.append_components(doc.ifc.file, [type_.id()])
    out.file.write(path)
    return path


def read_item(path):
    """What a library file holds, to show it: ("ifc", the file, [(type id, name, class, copies)]) or ("model",
    mesh_import.Model3D)."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".ifc":
        from ..ifc.model import IfcModel
        library, found = IfcModel.read_library(path)
        return "ifc", library, found
    from . import mesh_import
    return "model", mesh_import.read(path)


def item_shape(path):
    """A library file's shape for its miniature: (triangles' corners (T, 3, 3) in metres, sRGB (T, 3)), or None."""
    import numpy as np
    read = read_item(path)
    if read[0] == "ifc":
        _kind, library, found = read
        if not found:
            return None
        from ..ifc.model import type_shape
        import ifcopenshell.util.unit
        return type_shape(library.by_id(found[0][0]), ifcopenshell.util.unit.calculate_unit_scale(library))
    model = read[1]
    corners, colours = [], []
    for (_name, rgb, _alpha), tris in model.parts_m().items():
        tris = np.asarray(tris, dtype=float).reshape(-1, 3, 3)
        corners.append(tris)
        colours.append(np.tile(np.asarray(rgb, dtype=float)[:3], (len(tris), 1)))
    if not corners:
        return None
    return np.concatenate(corners), np.concatenate(colours)


def bring(doc, path, category="furniture"):
    """A library file's component brought into the project (one undo step; one already there: as it is). Returns its
    type's GlobalId."""
    from . import bim
    read = read_item(path)
    if read[0] == "ifc":
        _kind, library, found = read
        if not found:
            raise ValueError("empty")
        guids = bim.import_components(doc, library, [found[0][0]])
        return guids[0]
    model = read[1]
    name = os.path.splitext(os.path.basename(path))[0]
    return bim.import_model_component(doc, model, name, category)


# ---------------------------------------------------------------- the web (the ArqSynth store, when it opens)

CATALOGUE_KEY = "biblioteca/catalogo"      # (QSettings) the web catalogue's address, "" none yet
CATALOGUE_FIELDS = ("id", "name", "author", "licence", "price", "currency", "thumbnail", "file", "size", "category")


def read_catalogue(text):
    """A web catalogue (JSON: {"name", "items": [{id, name, author, licence, price, currency, thumbnail (address),
    file (address of its IFC / GLB…), size, category}]}) — (its name, [dict]) with the items it understands (an id, a
    name, a file); price 0 or none: free."""
    data = json.loads(text)
    out = []
    for item in data.get("items", ()) if isinstance(data, dict) else ():
        if not isinstance(item, dict) or not item.get("id") or not item.get("name") or not item.get("file"):
            continue
        row = {k: item.get(k) for k in CATALOGUE_FIELDS}
        try:
            row["price"] = float(row["price"] or 0.0)
        except (TypeError, ValueError):
            row["price"] = 0.0
        out.append(row)
    return (data.get("name") or "") if isinstance(data, dict) else "", out
