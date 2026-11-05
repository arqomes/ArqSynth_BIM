"""(0.368) The project's 360° panoramas (Render ▸ Panorama 360°: render/path_tracer.render_panorama): each a JPEG in
a folder beside the project («<projeto> - panoramas»), and where it was taken from — its eye (the model's axes), the
way it looks ahead (level), its storey — kept with the views (Document.panoramas, in the .arqsynthbim file), one undo
step a change (the picture stays on disk). They go to the ArqSynth Presentation in the package, as 360° points on the
plans of their storey."""

import copy
import os
import uuid

FOLDER = "{} - panoramas"


def folder(doc):
    """The folder of a saved project's panoramas (None: the project was never saved)."""
    if not getattr(doc, "path", None):
        return None
    base = os.path.splitext(os.path.basename(doc.path))[0]
    return os.path.join(os.path.dirname(os.path.abspath(doc.path)), FOLDER.format(base))


def path_of(doc, panorama):
    """The panorama's picture on disk (its file, relative to the project's folder)."""
    if not getattr(doc, "path", None):
        return None
    return os.path.join(os.path.dirname(os.path.abspath(doc.path)), panorama["file"])


def clean(items):
    """The panoramas as they are kept: [{uid, name, file, eye [x, y, z], forward [x, y], storey}]."""
    out = []
    for p in items or ():
        try:
            out.append({"uid": str(p["uid"]), "name": str(p.get("name") or ""), "file": str(p["file"]),
                        "eye": [float(c) for c in p["eye"]][:3], "forward": [float(c) for c in p["forward"]][:2],
                        "storey": p.get("storey")})
        except (KeyError, TypeError, ValueError):
            continue
    return out


def next_name(doc, base):
    """«Panorama 3»: one more than the highest numbered."""
    numbers = []
    for p in getattr(doc, "panoramas", ()):
        tail = p["name"].rsplit(" ", 1)[-1]
        if p["name"].startswith(base) and tail.isdigit():
            numbers.append(int(tail))
    return "{} {}".format(base, max(numbers, default=0) + 1)


def made(doc, picture_name, name, eye, forward, storey):
    """A new panorama's record (its picture already written in folder(doc) as `picture_name`)."""
    base = os.path.basename(folder(doc))
    return {"uid": uuid.uuid4().hex, "name": name, "file": "{}/{}".format(base, picture_name),
            "eye": [float(c) for c in eye][:3], "forward": [float(c) for c in forward][:2], "storey": storey}


def with_added(items, panorama):
    return clean(copy.deepcopy(list(items)) + [panorama])


def without(items, uid):
    return [p for p in clean(items) if p["uid"] != uid]
