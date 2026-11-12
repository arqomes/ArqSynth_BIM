"""(0.565, PLANO.md «Gerador de revestimentos 3D em IFC», step 5) Paginação: a Revestimento's layout set out on it in
the view, as a fitter chalks it — its start (a joint's corner) a square grip, dragged where the joints should be: it
snaps to the face's corners and the middles of its edges and of its openings' (a joint on a door's jamb, a tile's
middle on a window's axis); its angle a diamond grip turned round it (every 15°, or along an edge of the face). The
pieces follow the mouse — the cut ones orange —, laid when let go (one undo step). Esc / right click: Select."""

import math

import numpy as np

from ..core import tiling as tl
from ..i18n import t
from ..model import bim
from .base import LEFT, RIGHT, SNAP_COLORS, Tool

SNAP_PX = 12               # px: a corner or an edge's middle this near takes the start
ANGLE_STEP = 15.0          # degrees
EDGE_SNAP = 3.0            # degrees: an edge's direction this near takes the angle


class CoveringLayoutTool(Tool):
    name = "covering_layout"
    keys_help = "keys.covering_layout"

    def __init__(self, host):
        super().__init__(host)
        self.guid = None
        self._drag = None        # "origin" | "angle"
        self._d = None           # the layout being changed
        self._frame = None       # (4, 4) the finish's plane
        self._face = None        # shapely, in it
        self._lift = 0.0

    def edit(self, guid):
        self.guid = guid
        self.host.set_tool(self.name)

    def activate(self):
        super().activate()
        self._load()

    def deactivate(self):
        super().deactivate()
        self.viewport.show_grips()
        self.viewport.show_operator_preview()
        self.viewport.show_tip("", None)

    def hint(self):
        return t("hint.covering_layout")

    # ------------------------------------------------------------ the finish in its plane

    def _load(self):
        ifc = self.doc.ifc
        if self.guid is None or ifc.by_guid(self.guid) is None:
            self.host.set_tool("select")
            return
        p = ifc.tiled_params(self.guid)
        self._frame, self._face = ifc.tiled_face(self.guid)
        self._d = dict(p["layout"])
        self._lift = p["bed"] + p["thickness"] + 0.003
        result = ifc.tiled_layout(self.guid)
        self._d["origin"], self._d["point"], self._d["align"] = "ponto", result.origin, "junta"
        self._d["dx"] = self._d["dy"] = 0.0
        self._show(result)

    def _world(self, uv, lift=None):
        m = self._frame
        u, v = uv
        z = self._lift if lift is None else lift
        return m[:3, 3] + m[:3, 0] * u + m[:3, 1] * v + m[:3, 2] * z

    def _plane(self, x, y):
        """The point of the finish's plane under the mouse (its u, v), or None."""
        o, d = self.viewport.ray(x, y)
        m = self._frame
        n, base = m[:3, 2], m[:3, 3] + m[:3, 2] * self._lift
        den = float(np.dot(d, n))
        if abs(den) < 1e-9:
            return None
        s = float(np.dot(base - o, n)) / den
        q = o + d * s - m[:3, 3]
        return float(q @ m[:3, 0]), float(q @ m[:3, 1])

    def _handle(self):
        """Where the angle's grip is: along the pattern's x from the start."""
        a = math.radians(self._d["angle"] + tl.EXTRA_ANGLE.get(self._d["pattern"], 0.0))
        r = max(0.4, 1.5 * max(self._d["w"], self._d["h"]))
        u, v = self._d["point"]
        return u + r * math.cos(a), v + r * math.sin(a)

    def _show(self, result=None):
        if result is None:
            try:
                q = self._face
                from shapely.geometry.polygon import orient
                q = orient(q, 1.0)
                result = tl.lay(list(q.exterior.coords)[:-1], self._d, [list(h.coords)[:-1] for h in q.interiors])
            except tl.LayoutError:
                return
        tris, whole = tl.top_triangles(result)
        if len(tris):
            m = self._frame
            flat = tris.reshape(-1, 3)
            world = m[:3, 3] + flat[:, :1] * m[:3, 0] + flat[:, 1:2] * m[:3, 1] + (flat[:, 2:3] + self._lift) * m[:3, 2]
            rgba = np.where(whole[:, None], np.array((0.30, 0.50, 0.85, 0.45)), np.array((0.95, 0.55, 0.20, 0.65)))
            self.viewport.show_operator_preview(world.reshape(-1, 3, 3), rgba)
        start, handle = self._world(self._d["point"]), self._world(self._handle())
        self.viewport.show_grips(ends=[start], middles=[handle])
        self._result = result

    # ------------------------------------------------------------ snapping

    def _snaps(self):
        """The face's corners and the middles of its edges (its openings' too): [(u, v)]."""
        out = []
        for ring in [self._face.exterior] + list(self._face.interiors):
            c = list(ring.coords)[:-1]
            for i, a in enumerate(c):
                b = c[(i + 1) % len(c)]
                out += [tuple(a), ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)]
        return out

    def _snap_point(self, x, y, uv):
        best, tip = uv, ""
        pts = self._snaps()
        if pts:
            xy = self.viewport.project_many(np.array([self._world(p) for p in pts]))
            dist = np.hypot(xy[:, 0] - x, xy[:, 1] - y)
            k = int(np.nanargmin(np.nan_to_num(dist, nan=np.inf)))
            if dist[k] <= SNAP_PX:
                best, tip = pts[k], t("tip.covering_snap")
        return best, tip

    def _snap_angle(self, a):
        """`a` (degrees) to the nearest edge direction (within EDGE_SNAP), else to the nearest ANGLE_STEP."""
        c = list(self._face.exterior.coords)
        for p, q in zip(c, c[1:]):
            e = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
            for k in range(-4, 5):
                if abs(a - (e + 90.0 * k)) < EDGE_SNAP:
                    return e + 90.0 * k, t("tip.covering_along_edge")
        return round(a / ANGLE_STEP) * ANGLE_STEP, ""

    # ------------------------------------------------------------ the mouse

    def pointer_down(self, x, y, button, modifiers):
        if button == RIGHT:
            self.host.set_tool("select")
            return
        if button != LEFT or self._d is None:
            return
        grip = self.viewport.grip_at(x, y)
        if grip is None:
            return
        self._drag = "origin" if grip[0] == "end" else "angle"

    def pointer_move(self, x, y, modifiers):
        if self._d is None:
            return
        uv = self._plane(x, y)
        if uv is None:
            return
        if self._drag is None:
            grip = self.viewport.grip_at(x, y)
            tip = "" if grip is None else t("tip.covering_move" if grip[0] == "end" else "tip.covering_turn")
            self.viewport.show_tip(tip, self._world(uv) if tip else None)
            return
        if self._drag == "origin":
            uv, tip = self._snap_point(x, y, uv)
            self._d["point"] = uv
        else:
            u0, v0 = self._d["point"]
            a = math.degrees(math.atan2(uv[1] - v0, uv[0] - u0)) - tl.EXTRA_ANGLE.get(self._d["pattern"], 0.0)
            a, tip = self._snap_angle(a)
            self._d["angle"] = ((a + 180.0) % 360.0) - 180.0
            tip = tip or "{:.0f}°".format(self._d["angle"])
        self._show()
        self.viewport.show_tip(tip, self._world(uv) if tip else None)

    def pointer_up(self, x, y, button, modifiers):
        if self._drag is None:
            return
        self._drag = None
        keep = {k: self._d[k] for k in ("origin", "point", "align", "angle", "dx", "dy")}
        keep["point"] = tuple(float(c) for c in keep["point"])
        try:
            bim.set_covering(self.doc, self.guid, layout=keep)
        except ValueError as exc:
            from ..i18n import refusal
            self.host.message(t("err.edit_refused", e=refusal(exc)), warning=True)
        self._load()
        s = self._result.summary(self._d["min_cut"])
        self.host.message(t("info.covering_layout", n=s["pieces"], c=s["cut"], k=s["narrow"]))

    def cancel(self):
        self.viewport.show_tip("", None)
