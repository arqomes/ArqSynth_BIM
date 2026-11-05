"""The snaps of a CAD drawing linked (0.158): its lines' ends, middles and the lines themselves, found by the tools as
an element's edges are (the Wall tool takes a wall's corner on the drawing, as Revit's on a linked CAD). An object
the snap index keeps beside the document's: it is not in the document (nothing selects, moves or deletes it)."""

import numpy as np

_I4 = np.eye(4)
CAD_CLASS = "CAD"


class _Lines:
    """What the snap index asks of an element's shape: its corners, its edges, its box."""

    def __init__(self, segments, z):
        segs = np.asarray(segments, dtype=float).reshape(-1, 2, 2)
        pts = np.column_stack((segs.reshape(-1, 2), np.full(len(segs) * 2, float(z))))
        self.verts, index = np.unique(np.round(pts, 6), axis=0, return_inverse=True)
        pairs = index.reshape(-1, 2)
        self._pairs = pairs[pairs[:, 0] != pairs[:, 1]]
        self._faces = np.full((len(self._pairs), 2), -1, dtype=np.int64)
        self._bounds = (self.verts.min(axis=0), self.verts.max(axis=0)) if len(self.verts) else None

    def edge_array(self):
        return self._pairs, self._faces

    def bounds(self):
        return self._bounds


class CadSnapObject:
    is_bim = True                      # (its shape in world coordinates, as an element's)
    ifc_class = CAD_CLASS

    def __init__(self, uid, segments, z, storey):
        self.id = "cad:" + uid
        self.name = ""
        self.storey = storey
        self.matrix = _I4
        self.mesh = _Lines(segments, z)
