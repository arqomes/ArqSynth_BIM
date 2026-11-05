"""(0.332) Model patterns (tiles, bricks…) aligned by hand on an element's faces, as Revit's Align on a pattern line:
each face's pattern moved and turned, kept in the element — ArqSynth_Parametros, AlinhamentoPadroes: JSON {face: [x,
y, z, angle]}, the face named by its normal in the element's own frame, its pattern's origin a point in that frame
(metres) and its angle in degrees about the face's normal —, so that it follows the element when it moves or turns.
A face not listed: its pattern as always (from the world's origin, core.patterns.face_axes)."""

import json
import math

import numpy as np

from ..core import patterns as core_patterns
from .edit import PARAM_PSET

PROPERTY = "AlinhamentoPadroes"


def face_key(local_normal):
    """A face's name: its unit normal in the element's frame, to a thousandth ("0.000,-1.000,0.000")."""
    n = np.asarray(local_normal, dtype=float)
    n = n / max(float(np.linalg.norm(n)), 1e-12)
    return ",".join("{:.3f}".format(round(float(c), 3) + 0.0) for c in n)


def read(ifc, guid):
    """{face: (x, y, z, angle)} of an element's aligned patterns ({} when none, or not understood)."""
    element = ifc.by_guid(guid) if ifc is not None else None
    if element is None:
        return {}
    text = ifc._params(element).get(PROPERTY)
    if not text:
        return {}
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        return {}
    found = {}
    for key, value in (data.items() if isinstance(data, dict) else ()):
        try:
            x, y, z, angle = (float(c) for c in value)
        except (TypeError, ValueError):
            continue
        found[str(key)] = (x, y, z, angle)
    return found


def frames(ifc, guid):
    """(normal) -> (origin, u, v) for core.patterns.on_triangles: an element's faces' patterns as aligned — None for a
    face not aligned —; None when none of its faces is."""
    kept = read(ifc, guid)
    if not kept:
        return None
    m = ifc.placement(guid)
    turn = m[:3, :3]

    def frame(normal):
        w = np.asarray(normal, dtype=float)
        w = w / max(float(np.linalg.norm(w)), 1e-12)
        found = kept.get(face_key(turn.T @ w))
        if found is None:
            return None
        origin = (m @ np.array((*found[:3], 1.0)))[:3]
        u, v = core_patterns.turned_axes(w, found[3])
        return origin, u, v
    return frame


def _turn(axis, angle):
    """The rotation matrix of `angle` degrees about a unit axis (Rodrigues)."""
    k = np.asarray(axis, dtype=float)
    a = math.radians(angle)
    cross = np.array(((0.0, -k[2], k[1]), (k[2], 0.0, -k[0]), (-k[1], k[0], 0.0)))
    return np.eye(3) + math.sin(a) * cross + (1.0 - math.cos(a)) * cross @ cross


def align(ifc, guid, normal, pivot, angle=0.0, shift=(0.0, 0.0, 0.0)):
    """An element's patterns on its faces turned `normal` (world) turned `angle` degrees about that normal through
    `pivot`, then moved by `shift` (a vector on the face) — from where they are (as aligned before, or as always) —
    and kept in it. Runs inside the caller's IFC transaction."""
    m = ifc.placement(guid)
    w = np.asarray(normal, dtype=float)
    w = w / max(float(np.linalg.norm(w)), 1e-12)
    key = face_key(m[:3, :3].T @ w)
    kept = read(ifc, guid)
    if key in kept:
        origin, before = (m @ np.array((*kept[key][:3], 1.0)))[:3], kept[key][3]
    else:
        origin, before = np.zeros(3), 0.0
    pivot = np.asarray(pivot, dtype=float)
    origin = pivot + _turn(w, angle) @ (origin - pivot) + np.asarray(shift, dtype=float)
    local = (np.linalg.inv(m) @ np.array((*origin, 1.0)))[:3]
    turned = (before + angle + 180.0) % 360.0 - 180.0
    kept[key] = tuple(round(float(c), 6) for c in local) + (round(turned, 6),)
    _write(ifc, guid, kept)


def reset(ifc, guid):
    """An element's patterns as always again (on all its faces)."""
    if read(ifc, guid):
        _write(ifc, guid, {})


def _write(ifc, guid, kept):
    if not kept:
        ifc.set_property(guid, PARAM_PSET, PROPERTY, None)
        return
    text = json.dumps({k: list(v) for k, v in sorted(kept.items())}, separators=(",", ":"))
    # (in its own set, never its type's — shared by others; an IfcText: an IfcLabel is 255 characters at most)
    ifc.set_property(guid, PARAM_PSET, PROPERTY, ifc.file.create_entity("IfcText", text))
