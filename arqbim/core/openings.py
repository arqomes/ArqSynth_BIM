"""Where a door or window goes in a straight wall. Pure numpy, no IFC.

A wall is read in its own frame (its IFC placement): X along the wall,
Y across the thickness, Z up. An opening is placed by `s`, the distance
along X from the wall start to the opening's left edge.
"""

from dataclasses import dataclass

import numpy as np

EDGE_CLEARANCE = 0.05     # m kept between an opening and the wall ends / top
CENTER_SNAP = 0.10        # m: within this distance the opening snaps to the wall centre
STEP = 0.01               # m: positions from the mouse are rounded to whole centimetres
# (0.409) the owner: «snap na inserção da porta e janela no meio de um compartimento e a 10, 20 cm da gola da parede»
GAPS = (0.10, 0.20)       # m from the face of the wall across (the room's corner) to the opening's jamb
GAP_SNAP = 0.04           # m: within this the jamb snaps to one of GAPS (they are 10 cm apart: the nearest wins)


@dataclass
class WallFrame:
    matrix: np.ndarray    # wall placement (meters), X along the wall, Z up
    length: float         # extent along X (from x0)
    x0: float
    y0: float             # the two faces, in the wall frame
    y1: float
    z0: float             # base and top
    z1: float

    @property
    def thickness(self):
        return self.y1 - self.y0

    @property
    def height(self):
        return self.z1 - self.z0

    def to_local(self, p):
        return (np.linalg.inv(self.matrix) @ np.append(p, 1.0))[:3]

    def to_world(self, p):
        return (self.matrix @ np.append(np.asarray(p, dtype=float), 1.0))[:3]

    def face_side(self, world_normal):
        """-1 / +1 for the two large faces (normal across the wall), else 0 (ends, top)."""
        y = self.matrix[:3, 1] / np.linalg.norm(self.matrix[:3, 1])
        d = float(np.dot(world_normal, y))
        return -1 if d < -0.9 else (1 if d > 0.9 else 0)


def wall_frame(matrix, world_verts):
    """Measure a wall (its display mesh) in its own placement frame."""
    m = np.asarray(matrix, dtype=float)
    local = (np.linalg.inv(m) @ np.column_stack((world_verts, np.ones(len(world_verts)))).T).T[:, :3]
    lo, hi = local.min(axis=0), local.max(axis=0)
    return WallFrame(m, float(hi[0] - lo[0]), float(lo[0]), float(lo[1]), float(hi[1]), float(lo[2]), float(hi[2]))


def fits(frame, width, height, sill):
    return (width <= frame.length - 2 * EDGE_CLEARANCE + 1e-9
            and sill + height <= frame.height - (0.0 if sill == 0 else EDGE_CLEARANCE) + 1e-9)


def clamp_s(frame, s, width):
    lo = frame.x0 + EDGE_CLEARANCE
    hi = frame.x0 + frame.length - EDGE_CLEARANCE - width
    return float(min(max(s, lo), hi))


def s_from_cursor(frame, hit_point, width):
    """Opening centred on the cursor, rounded to the centimetre, snapped to the
    wall centre when close. Returns (s, centred)."""
    x = frame.to_local(hit_point)[0]
    s = round((x - width / 2) / STEP) * STEP
    centre = frame.x0 + (frame.length - width) / 2
    if abs(s - centre) <= CENTER_SNAP:
        return float(centre), True
    return clamp_s(frame, s, width), False


def bounds_at(faces, x, frame):
    """(0.409) The room's side the point `x` (local) is on, along the wall: (left, right) — the nearest faces of the
    walls across it (local x, `faces`) on each side, else the wall's ends."""
    left = max((f for f in faces if f <= x + 1e-9), default=frame.x0)
    right = min((f for f in faces if f >= x - 1e-9), default=frame.x0 + frame.length)
    return float(left), float(right)


def snap_s(frame, hit_point, width, faces=()):
    """(0.409) Where an opening goes from the cursor: centred on it, to the centimetre — snapped, when near, to the
    middle of the room's side it is on (between the walls across: `faces`, their local x on the face the mouse is on;
    none: the whole wall, its centre as before) within CENTER_SNAP, or with a jamb GAPS from either of those walls
    within GAP_SNAP (the nearer of all wins). Returns (s, what): what "" (free), "middle" (of a room's side: a wall
    across on at least one side), "centre" (of the wall: none), or the gap (0.10 / 0.20)."""
    x = float(frame.to_local(hit_point)[0])
    raw = x - width / 2
    left, right = bounds_at(faces, x, frame)
    lo = frame.x0 + EDGE_CLEARANCE - 1e-9
    hi = frame.x0 + frame.length - EDGE_CLEARANCE - width + 1e-9
    whole = abs(left - frame.x0) < 1e-9 and abs(right - frame.x0 - frame.length) < 1e-9
    candidates = [((left + right - width) / 2, "centre" if whole else "middle", CENTER_SNAP)]
    for gap in GAPS:
        candidates += [(left + gap, gap, GAP_SNAP), (right - gap - width, gap, GAP_SNAP)]
    best = None
    for s, what, reach in candidates:
        if not (lo <= s <= hi) or s < left - 1e-9 or s + width > right + 1e-9:
            continue                                    # (past the wall's ends, or into the walls across)
        d = abs(raw - s)
        if d <= reach + 1e-9 and (best is None or d < best[0]):
            best = (d, s, what)
    if best is not None:
        return float(best[1]), best[2]
    return clamp_s(frame, round(raw / STEP) * STEP, width), ""


def s_from_typed(frame, distance, width, near_start):
    """Opening whose near edge is `distance` from the chosen wall end."""
    if near_start:
        s = frame.x0 + distance
    else:
        s = frame.x0 + frame.length - distance - width
    return clamp_s(frame, s, width)


def nearest_end(frame, hit_point):
    """True if the cursor is closer to the wall start than to its end."""
    x = frame.to_local(hit_point)[0]
    return x - frame.x0 <= frame.x0 + frame.length - x


def distance_to_end(frame, s, width, near_start):
    return (s - frame.x0) if near_start else (frame.x0 + frame.length - s - width)


def face_rectangle(frame, s, width, sill, height, side):
    """World corners of the opening outline on the clicked face (for preview)."""
    y = frame.y0 if side < 0 else frame.y1
    z = frame.z0 + sill
    pts = [(s, y, z), (s + width, y, z), (s + width, y, z + height), (s, y, z + height)]
    return [frame.to_world(p) for p in pts]
