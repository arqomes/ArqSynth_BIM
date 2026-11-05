"""Coordination notes (Phase 4, step 4): BCF topics — "this beam crosses the duct", with where
one was looking, the elements concerned, a picture and the comments that followed — read from
and written to .bcfzip files with bcf-client (LGPL-3.0, the owner's go-ahead of 2026-10-21), the
format Revit, ArchiCAD, Solibri and BIMcollab exchange. BCF 2.1 and 3.0 are read; 2.1 is written
(the one every program reads).

Positions are in the IFC's own (real-world) coordinates, as BCF wants them; the window brings
them to its working coordinates (near the origin) and back.
"""

import copy
import datetime
import uuid
from dataclasses import dataclass, field
from pathlib import Path

OPEN, CLOSED = "Open", "Closed"          # (BCF's usual words, kept in the file as they are)


@dataclass
class Camera:
    position: tuple
    direction: tuple
    up: tuple = (0.0, 0.0, 1.0)
    fov: float = 60.0                    # degrees (a perspective camera)
    scale: float = None                  # view-to-world scale (an orthogonal camera), else None


@dataclass(eq=False)
class Note:
    title: str
    description: str = ""
    status: str = OPEN
    author: str = ""
    date: str = ""                       # ISO 8601
    kind: str = ""                       # BCF topic type ("Issue", "Clash"…)
    comments: list = field(default_factory=list)      # [(author, ISO date, text)]
    camera: Camera = None
    selected: list = field(default_factory=list)      # GlobalIds of the elements concerned
    snapshot: bytes = None               # PNG
    guid: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def closed(self):
        return self.status.strip().lower() in ("closed", "resolved", "fechada", "fechado")


def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


class NotesChange:
    """A change to the notes, one undo step (the notes are put back as they were)."""

    def __init__(self, label, change):
        self.label, self.change = label, change
        self.result = None
        self._before = self._after = None

    def do(self, doc):
        if self._after is None:
            self._before = copy.deepcopy(doc.notes)
            self.result = self.change(doc)
            self._after = copy.deepcopy(doc.notes)
        else:
            doc.notes = copy.deepcopy(self._after)
        doc.notes_changed()

    def undo(self, doc):
        doc.notes = copy.deepcopy(self._before)
        doc.notes_changed()


# ---------------------------------------------------------------- reading

def _point(p):
    return (float(p.x), float(p.y), float(p.z)) if p is not None else None


def load(path):
    """[Note] of a .bcfzip (BCF 2.1 or 3.0). Raises ValueError if it is not one."""
    import bcf.bcfxml
    try:
        bcf_file = bcf.bcfxml.load(Path(path))
    except Exception as exc:
        raise ValueError(str(exc)[:300]) from exc
    notes = []
    try:
        for handler in bcf_file.topics.values():
            topic = handler.topic
            note = Note(topic.title or "", topic.description or "", topic.topic_status or OPEN,
                        topic.creation_author or "", str(topic.creation_date or ""), topic.topic_type or "",
                        guid=topic.guid)
            note.comments = [(c.author or "", str(c.date or ""), c.comment or "") for c in handler.comments or ()]
            viewpoints = list(handler.viewpoints.values())
            if viewpoints:
                first = viewpoints[0]
                info = first.visualization_info
                cam = info.perspective_camera or info.orthogonal_camera
                if cam is not None:
                    note.camera = Camera(_point(cam.camera_view_point), _point(cam.camera_direction),
                                         _point(cam.camera_up_vector) or (0.0, 0.0, 1.0),
                                         float(getattr(cam, "field_of_view", 60.0) or 60.0),
                                         getattr(cam, "view_to_world_scale", None))
                note.selected = list(first.get_selected_guids() or [])
                note.snapshot = first.snapshot
            notes.append(note)
    finally:
        bcf_file.close()
    return notes


# ---------------------------------------------------------------- writing

def save(notes, path, project_name=""):
    """Write the notes to a .bcfzip (BCF 2.1)."""
    from xsdata.models.datatype import XmlDateTime
    from bcf.v2 import model as mdl
    from bcf.v2.bcfxml import BcfXml
    from bcf.v2.topic import TopicHandler
    from bcf.v2.visinfo import VisualizationInfoHandler, build_components

    def when(text):
        try:
            return XmlDateTime.from_string(text)
        except Exception:
            return XmlDateTime.from_datetime(datetime.datetime.now())

    bcf_file = BcfXml.create_new(project_name or None)
    for note in notes:
        topic = mdl.Topic(title=note.title or "-", description=note.description, creation_author=note.author or "-",
                          creation_date=when(note.date), guid=note.guid, topic_type=note.kind,
                          topic_status=note.status)
        markup = mdl.Markup(topic=topic)
        markup.comment = [mdl.Comment(date=when(d), author=a or "-", comment=text, guid=str(uuid.uuid4()))
                          for a, d, text in note.comments]
        handler = TopicHandler(topic_dir=Path(note.guid))
        handler.markup = markup
        if note.camera is not None or note.selected:
            info = mdl.VisualizationInfo(guid=str(uuid.uuid4()))
            if note.selected:
                info.components = build_components(*note.selected)
            if note.camera is not None:
                cam = note.camera
                p, d, u = ([float(c) for c in v] for v in (cam.position, cam.direction, cam.up))   # (plain floats)
                point = mdl.Point(x=p[0], y=p[1], z=p[2])
                direction = mdl.Direction(x=d[0], y=d[1], z=d[2])
                up = mdl.Direction(x=u[0], y=u[1], z=u[2])
                if cam.scale:
                    info.orthogonal_camera = mdl.OrthogonalCamera(camera_view_point=point, camera_direction=direction,
                                                                  camera_up_vector=up,
                                                                  view_to_world_scale=float(cam.scale))
                else:
                    info.perspective_camera = mdl.PerspectiveCamera(camera_view_point=point,
                                                                    camera_direction=direction, camera_up_vector=up,
                                                                    field_of_view=float(cam.fov))
            handler.add_visinfo_handler(VisualizationInfoHandler(info, snapshot=note.snapshot),
                                        "snapshot.png" if note.snapshot else None)
        bcf_file.topics[note.guid] = handler
    bcf_file.save(Path(path))
    bcf_file.close()
