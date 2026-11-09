"""(0.510) The steel structure's erection plan — «Planta de montagem» (the plan's step 6; Tekla's general arrangement,
which DetailCraft has not): every steel piece seen from above as it stands — the columns, beams, rafters, braces,
purlins, truss and stair members, drawn by the same projection as the structure plans (drawings._draw, coarse) —,
the grid's axes, and each piece's mark beside it (the marks «Numerar peças» writes, as they would be now): what the
erectors put where. Not the connections' plates and bolts (the fabrication drawing has them). At 1:100 on a sheet."""

import numpy as np

SCALE = 100
CLEAR = 0.10                    # m: a mark this far off its piece's side


def erection_plan(doc, title):
    """The erection plan, or None when the model has no steel piece."""
    from .drawings import _draw
    from .rebar_drawings import _text
    try:
        marks, pieces = doc.ifc.steel_marks()
    except Exception:
        return None
    objs = []
    for p in pieces:
        if p["prefix"] == "Ch":
            continue
        o = doc.get(p["guid"])
        if o is not None and o.mesh is not None and len(o.mesh.verts):
            objs.append((o, marks.get(p["guid"], "")))
    if not objs:
        return None
    top = max(float(o.mesh.verts[:, 2].max()) for o, _m in objs) + 0.5
    low = min(float(o.mesh.verts[:, 2].min()) for o, _m in objs)
    drawing = _draw(doc, [o for o, _m in objs], np.array((0.0, 0.0, -1.0)), -top, np.array((0.0, 0.0, low)),
                    np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0)), title, detail="coarse")
    drawing.grids = [(np.array(a.start, dtype=float), np.array(a.end, dtype=float), a.tag)
                     for a in getattr(doc, "grids", ())]
    drawing.north = True
    ann, taken = [], []
    axes = {o.id: _axis(o.mesh.verts) for o, _m in objs}       # (each piece's line seen from above: what to keep off)
    order = sorted(objs, key=lambda item: float(np.ptp(item[0].mesh.verts[:, :2], axis=0).max()))   # (the short
    for o, mark in order:                                                                          # first: they
        if not mark:                                                                               # have least room)
            continue
        others = [line for g, line in axes.items() if g != o.id and line is not None]
        where = _label_at(o.mesh.verts, mark, taken, others)
        drawing.movable.append((len(ann), o.id))
        ann.append(_text(where, mark))
    drawing.annotations = list(drawing.annotations or []) + ann
    return drawing


def _axis(verts):
    """A piece's line seen from above (a shapely LineString along its length), or its footprint's box (an upright
    piece seen end on)."""
    from shapely.geometry import LineString, box
    xy = np.asarray(verts, dtype=float)[:, :2]
    lo, hi = xy.min(axis=0), xy.max(axis=0)
    if float((hi - lo).max()) < 0.6:
        return box(lo[0], lo[1], hi[0], hi[1])
    mean = xy.mean(axis=0)
    centred = xy - mean
    _ev, vecs = np.linalg.eigh(centred.T @ centred)
    along = vecs[:, -1]
    s = centred @ along
    return LineString([tuple(mean + along * float(s.min())), tuple(mean + along * float(s.max()))])


def _box(where, mark):
    """The room a mark's text takes on the drawing (m), from where it is written (its lower left)."""
    from .rebar_drawings import TEXT
    w = len(mark) * 0.55 * TEXT * SCALE / 1000.0
    h = 1.2 * TEXT * SCALE / 1000.0
    return float(where[0]), float(where[1]), float(where[0]) + w, float(where[1]) + h


def _free(box, taken):
    return all(box[2] <= b[0] or box[0] >= b[2] or box[3] <= b[1] or box[1] >= b[3] for b in taken)


def _label_at(verts, mark, taken, others=()):
    """Where a piece's mark goes, seen from above, clear of the marks already placed (`taken`, their boxes — this one's
    added) and of the other pieces' lines (`others`): beside an upright piece's section (a corner of it); beside a
    long one, square to its length past half its width, at its middle — or, taken, a little along it either way, or on
    its other side. The first free place; none clear of the lines: the first clear of the marks; none: its middle."""
    from shapely.geometry import box as shape_box
    xy = np.asarray(verts, dtype=float)[:, :2]
    lo, hi = xy.min(axis=0), xy.max(axis=0)
    size = hi - lo
    w, h = _box((0.0, 0.0), mark)[2:]
    if float(size.max()) < 0.6:                                 # (a column — or a short piece — seen end on)
        places = [hi + CLEAR, (lo[0] - w - CLEAR, hi[1] + CLEAR), (hi[0] + CLEAR, lo[1] - h - CLEAR),
                  (lo[0] - w - CLEAR, lo[1] - h - CLEAR)]
    else:
        mean = xy.mean(axis=0)
        centred = xy - mean
        _ev, vecs = np.linalg.eigh(centred.T @ centred)
        along = vecs[:, -1]
        normal = np.array((-along[1], along[0]))
        if normal[1] < -1e-9 or (abs(normal[1]) <= 1e-9 and normal[0] < 0):    # (over it, or to its right)
            normal = -normal
        s = centred @ along
        half = float(np.abs(centred @ normal).max())
        places = []
        for f in (0.5, 0.35, 0.65, 0.25, 0.75, 0.42, 0.58, 0.15, 0.85):
            point = mean + along * (float(s.min()) + f * float(np.ptp(s)))
            for side in (1.0, -1.0):
                out = normal * side
                tip = point + out * (half + CLEAR)
                # (the text's corner, its lower left: beside a piece across the sheet, centred over or under it;
                # beside one up the sheet, starting at its right or ending at its left, centred on its height)
                if abs(out[1]) >= abs(out[0]):
                    corner = tip - np.array((w / 2.0, h if out[1] < 0 else 0.0))
                else:
                    corner = tip - np.array((0.0 if out[0] > 0 else w, h / 2.0))
                places.append(corner)
    free = [where for where in places if _free(_box(where, mark), taken)]
    clear = [where for where in free if not any(shape_box(*_box(where, mark)).intersects(line) for line in others)]
    where = (clear or free or places)[0]
    taken.append(_box(where, mark))
    return np.asarray(where, dtype=float)
