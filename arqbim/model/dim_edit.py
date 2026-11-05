"""(0.402) Dimensions edited as Revit's (the owner, 2026-11-05: «a cotação manual precisa ser como no Revit»): a
dimension string is chosen whole; its line is dragged off or nearer (all its pieces together); a value's text dragged
apart; a witness line taken to another reference; a witness line deleted (its two pieces become one) or references
added; «IG» makes its pieces equal (the walls, doors and windows in its middle moved) and writes «IG»; a value typed
moves the element at one end; its own words — a text over the value, a prefix, a suffix, words over and under it.
Each edit is one undo step."""

import numpy as np

from . import dimensions as dims_model

FIELDS = ("a", "b", "at", "refs", "at_ref", "note", "eq", "direction", "style", "chain")


def string_of(doc, dim):
    """The pieces of a dimension's string (its chain, in its view), in the order they are kept; [dim] alone."""
    if dim.chain is None:
        return [dim]
    return [d for d in doc.dimensions if d.chain == dim.chain and d.view == dim.view]


def _copy(value):
    if isinstance(value, np.ndarray):
        return value.copy()
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, list):
        return list(value)
    return value


class ChangeDimensions:
    """Dimensions changed (each {field: its new value}), some taken away, others added: one undo step."""

    def __init__(self, changes, label, removed=(), added=()):
        self.changes = [(d, {k: _copy(v) for k, v in new.items()}) for d, new in changes]
        self.before = [(d, {k: _copy(getattr(d, k)) for k in new}) for d, new in self.changes]
        self.removed, self.added, self.label = list(removed), list(added), label
        self._where = []

    def do(self, doc):
        for d, new in self.changes:
            for k, v in new.items():
                setattr(d, k, _copy(v))
        self._where = [(doc.dimensions.index(d), d) for d in self.removed if d in doc.dimensions]
        for _k, d in self._where:
            doc.dimensions.remove(d)
        doc.dimensions.extend(self.added)
        doc.dimensions_changed()

    def undo(self, doc):
        for d in self.added:
            if d in doc.dimensions:
                doc.dimensions.remove(d)
        for k, d in sorted(self._where, key=lambda item: item[0]):
            doc.dimensions.insert(k, d)
        for d, old in self.before:
            for k, v in old.items():
                setattr(d, k, _copy(v))
        doc.dimensions_changed()


def _frame(doc, view):
    """(origin, u, v, normal) of a view's 2D frame (a plan's: level; others' from the document's views)."""
    if view[0] == "plan":
        level = next((z for g, _n, z in doc.ifc.storeys() if g == view[1]), 0.0)
        return np.array((0.0, 0.0, level)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0)), \
            np.array((0.0, 0.0, 1.0))
    return None


def line_normal(doc, dim, plane):
    """The unit vector across a dimension's line in its view (3D), its direction along it: (along, across)."""
    origin, u, v, _n = plane
    a, b = dims_model.ends(doc, dim)
    if dim.direction is not None:
        d = np.asarray(dim.direction, dtype=float)
    else:
        d = b - a
    d2 = np.array((float(d @ u), float(d @ v)))
    norm = float(np.linalg.norm(d2))
    d2 = d2 / norm if norm > 1e-12 else np.array((1.0, 0.0))
    along = u * d2[0] + v * d2[1]
    across = u * -d2[1] + v * d2[0]
    return along, across


def move_line(doc, dims, delta, plane, label):
    """The string's line moved by `delta` (3D) across itself — all its pieces together."""
    changes = []
    for d in dims:
        _along, across = line_normal(doc, d, plane)
        at = dims_model.line_point(doc, d) + across * float(np.asarray(delta, dtype=float) @ across)
        changes.append((d, {"at": at, "at_ref": dims_model.hang_line(doc, d.refs, at)}))
    doc.execute(ChangeDimensions(changes, label))


def move_text(doc, dim, shift2, label):
    """A value's text put by hand: (dx, dy) in its view's 2D frame, its middle from its line's middle — (0.405) where it
    was dropped, whatever it was before (None: back in its place)."""
    note = dict(dim.note or {})
    if shift2 is None:
        note.pop("shift", None)
    else:
        note["shift"] = "{:.4f};{:.4f}".format(shift2[0], shift2[1])
    doc.execute(ChangeDimensions([(dim, {"note": note or None})], label))


def line_middle(doc, dim, plane):
    """(0.405) The middle of a dimension's line in its view's 2D frame (where its value's place is measured from)."""
    origin, u, v, _n = plane
    a, b = dims_model.ends(doc, dim)
    _p1, _p2, l1, l2, _length = dims_model.placed(a, b, dims_model.line_point(doc, dim), origin, u, v, dim.direction)
    return (l1 + l2) / 2


def witness_points(doc, dims):
    """The string's witness points: [(point (3,), [(dim, end 0 / 1)])] — each point once, with the pieces' ends on it."""
    out = []
    for d in dims:
        for k, p in enumerate(dims_model.ends(doc, d)):
            for point, users in out:
                if np.linalg.norm(point - p) < 1e-4:
                    users.append((d, k))
                    break
            else:
                out.append((np.asarray(p, dtype=float), [(d, k)]))
    return out


def move_witness(doc, dims, index, point, ref, label):
    """A witness line taken to another reference: the pieces' ends on it go to `point` (hung by `ref`)."""
    found = witness_points(doc, dims)
    if not 0 <= index < len(found):
        return False
    changes = []
    for d, k in found[index][1]:
        refs = list(d.refs)
        refs[k] = ref
        changes.append((d, {"a" if k == 0 else "b": np.asarray(point, dtype=float), "refs": refs}))
    doc.execute(ChangeDimensions(changes, label))
    return True


def remove_witness(doc, dims, index, label):
    """A witness line deleted, as Revit's: the two pieces on each side of it become one; at an end of the string, the
    piece there goes. A string of one piece is left as it is (False)."""
    found = witness_points(doc, dims)
    if len(dims) < 2 or not 0 <= index < len(found):
        return False
    users = found[index][1]
    if len(users) == 1:                                  # (an end of the string: its piece goes)
        doc.execute(ChangeDimensions([], label, removed=[users[0][0]]))
        return True
    (d0, k0), (d1, k1) = users[:2]
    far1 = 1 - k1                                        # (d1's other end: d0 reaches to it)
    refs = list(d0.refs)
    refs[k0] = d1.refs[far1]
    point = dims_model.ends(doc, d1)[far1]
    doc.execute(ChangeDimensions([(d0, {"a" if k0 == 0 else "b": np.asarray(point, dtype=float), "refs": refs})],
                                 label, removed=[d1]))
    return True


def set_note(doc, dims, note, label):
    """Their own words: {"override", "prefix", "suffix", "above", "below"} (empty ones taken away)."""
    changes = []
    for d in dims:
        new = dict(d.note or {})
        for k in ("override", "prefix", "suffix", "above", "below"):
            if k in note:
                if note[k]:
                    new[k] = str(note[k])
                else:
                    new.pop(k, None)
        changes.append((d, {"note": new or None}))
    doc.execute(ChangeDimensions(changes, label))


def _along(doc, dims, plane):
    """The string's direction (3D) and its pieces' points along it, in order: (d, [(s, point, [(dim, end)])])."""
    along, _across = line_normal(doc, dims[0], plane)
    points = [(float(p @ along), p, users) for p, users in witness_points(doc, dims)]
    points.sort(key=lambda r: r[0])
    return along, points


def _move_element(doc, guid, delta):
    """An element moved by `delta` (3D, in plan): a door or window along its wall, anything else as it is. True if
    it moved."""
    from . import bim
    obj = doc.get(guid)
    if obj is None or not getattr(obj, "is_bim", False):
        return False
    if obj.ifc_class in ("IfcDoor", "IfcWindow"):
        st = doc.ifc.filling_state(guid)
        axis = st["matrix"][:3, 0] / np.linalg.norm(st["matrix"][:3, 0])
        step = float(np.asarray(delta, dtype=float) @ axis)
        if abs(step) < 1e-9:
            return False
        bim.move_filling(doc, guid, s=st["s"] + step)
        return True
    m = np.eye(4)
    m[:3, 3] = delta
    bim.transform_objects(doc, [guid], m, "")
    return True


def equalize(doc, dims, plane, label):
    """«IG»: the string's pieces made equal — the elements at its inner witness lines moved along it to their equal
    places (its ends stay), every piece then writing «IG». One undo step. How many elements moved."""
    along, points = _along(doc, dims, plane)
    if len(points) < 3:
        changes = [(d, {"eq": True}) for d in dims]
        doc.execute(ChangeDimensions(changes, label))
        return 0
    s0, s1 = points[0][0], points[-1][0]
    step = (s1 - s0) / (len(points) - 1)
    mark = doc.undo_mark()
    moved = 0
    for k, (s, _p, users) in enumerate(points[1:-1], 1):
        target = s0 + step * k
        if abs(target - s) < 1e-6:
            continue
        guid = next((d.refs[e][0] for d, e in users if d.refs[e] is not None), None)
        if guid is not None and _move_element(doc, guid, along * (target - s)):
            moved += 1
        else:                                            # (a free point: the dimensions' own points move)
            changes = [(d, {"a" if e == 0 else "b": np.asarray(dims_model.ends(doc, d)[e], dtype=float)
                            + along * (target - s)}) for d, e in users]
            doc.execute(ChangeDimensions(changes, label))
    doc.execute(ChangeDimensions([(d, {"eq": True}) for d in dims], label))
    doc.join_since(mark, label)
    return moved


def unequalize(doc, dims, label):
    """«IG» off: the values written again (nothing moves)."""
    doc.execute(ChangeDimensions([(d, {"eq": False}) for d in dims], label))


def set_value(doc, dim, value, plane, moving=None, label=""):
    """A dimension made `value` long by moving the element at one of its ends — `moving` (a GlobalId; None: the one
    at its second end, else at its first) — along it. True if something moved."""
    a, b = dims_model.ends(doc, dim)
    along, _across = line_normal(doc, dim, plane)
    sa, sb = float(a @ along), float(b @ along)
    current = abs(sb - sa)
    if current < 1e-9 or value <= 0:
        return False
    ends = [r[0] if r is not None else None for r in dim.refs]
    if moving is None:
        moving = ends[1] if ends[1] is not None else ends[0]
    if moving is None or moving not in ends:
        return False
    k = ends.index(moving)
    sign = (1.0 if sb >= sa else -1.0) * (1.0 if k == 1 else -1.0)
    mark = doc.undo_mark()
    moved = _move_element(doc, moving, along * sign * (value - current))
    if moved:
        doc.join_since(mark, label)
    return moved
