"""From a sketch volume to the parameters of a clean BIM element.

A sketch box (drawn with Rectangle + Push/Pull) is read as an upright box:
footprint axes, height and base level. From that, a wall gets an axis line,
length and height; a slab a footprint and top level; a column a centre and
height. The construction type (catalogue) decides thickness / section.

Pure numpy, no IFC: the IFC layer turns these numbers into entities.
"""

from dataclasses import dataclass, field

import numpy as np

from .mesh import polygon_normal
from .sketch_geometry import normalize, transform_point

Z = np.array((0.0, 0.0, 1.0))


@dataclass
class UprightBox:
    base: np.ndarray       # a footprint corner at the bottom level (world)
    x_dir: np.ndarray      # horizontal unit vector along `length`
    y_dir: np.ndarray      # horizontal unit vector along `width` (z x x)
    length: float          # longer horizontal side
    width: float           # shorter horizontal side
    height: float
    bottom: float          # z of the base
    top: float             # z of the top
    voids: list = field(default_factory=list)   # through-holes: (world polygon, world through vector)

    def footprint(self):
        """Four corners (world, at the bottom level), counter-clockwise from above."""
        b, x, y = self.base, self.x_dir * self.length, self.y_dir * self.width
        return [b, b + x, b + x + y, b + y]

    def center(self):
        return self.base + self.x_dir * self.length / 2 + self.y_dir * self.width / 2


def upright_box(obj, rel_tol=1e-6):
    """Read a sketch object as an upright rectangular box, or None.

    The box is measured in the object's own frame (where Rectangle + Push/Pull
    keep it axis-aligned); one of its axes must be vertical.
    """
    mesh = obj.mesh
    if len(mesh.faces) < 6 or not mesh.is_closed():
        return None
    local = np.array(mesh.verts)
    lo, hi = local.min(axis=0), local.max(axis=0)
    sizes_local = hi - lo
    axes = [obj.matrix[:3, i] for i in range(3)]
    sizes = np.array([sizes_local[i] * np.linalg.norm(axes[i]) for i in range(3)])
    if np.any(sizes < 1e-6):
        return None
    world = mesh.transformed(obj.matrix)
    voids = world.voids
    void_volume = sum(_polygon_area(pts) * np.linalg.norm(vec) for pts, vec in voids)
    expected = np.prod(sizes) - void_volume
    if abs(world.volume() - expected) > rel_tol * np.prod(sizes) + 1e-12:
        return None  # not a plain box (e.g. it has a balcony or a recess)

    dirs = [normalize(a) for a in axes]
    vertical = [i for i in range(3) if abs(dirs[i].dot(Z)) > 1 - 1e-9]
    if len(vertical) != 1:
        return None  # tilted
    k = vertical[0]
    h1, h2 = [i for i in range(3) if i != k]
    if sizes[h2] > sizes[h1] + 1e-9:
        h1, h2 = h2, h1                     # h1 = longer horizontal side

    corners = [transform_point(obj.matrix, lo + sizes_local * np.array(c))
               for c in np.ndindex(2, 2, 2)]
    bottom = min(c[2] for c in corners)
    top = max(c[2] for c in corners)
    x_dir = normalize(dirs[h1] * np.array((1, 1, 0)))
    y_dir = np.cross(Z, x_dir)
    # footprint corner: the one minimising x and y along (x_dir, y_dir)
    flat = [c for c in corners if abs(c[2] - bottom) < 1e-9]
    base = min(flat, key=lambda c: (round(c.dot(x_dir), 9), round(c.dot(y_dir), 9)))
    return UprightBox(base=base, x_dir=x_dir, y_dir=y_dir, length=float(sizes[h1]),
                      width=float(sizes[h2]), height=float(top - bottom), bottom=float(bottom), top=float(top),
                      voids=[(list(pts), vec) for pts, vec in voids])


def _polygon_area(pts):
    pts = np.asarray(pts, dtype=float)
    total = np.zeros(3)
    for i in range(1, len(pts) - 1):
        total += np.cross(pts[i] - pts[0], pts[i + 1] - pts[0])
    return 0.5 * float(np.dot(total, polygon_normal(pts)))


def void_boxes(element_matrix, voids, through_axis, lo, hi, margin=0.01):
    """Voids (world polygons + through vectors) as axis-aligned boxes in an
    element's own frame, cutting right through along `through_axis` (0, 1 or 2)
    between lo and hi. Returns [(box_lo, box_hi)], or None if a void does not go
    through along that axis."""
    inv = np.linalg.inv(element_matrix)
    axis = np.zeros(3)
    axis[through_axis] = 1.0
    out = []
    for pts, vec in voids:
        v = inv[:3, :3] @ vec
        if abs(abs(normalize(v).dot(axis)) - 1) > 1e-6:
            return None
        local = np.array([(inv @ np.append(p, 1.0))[:3] for p in pts])
        box_lo, box_hi = local.min(axis=0), local.max(axis=0)
        box_lo[through_axis], box_hi[through_axis] = lo - margin, hi + margin
        out.append((box_lo, box_hi))
    return out


def box_from_axis(start, end, thickness, height):
    """Upright box of a wall drawn along its axis (start -> end, at the base level)."""
    start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    x_dir = normalize((end - start) * np.array((1, 1, 0)))
    y_dir = np.cross(Z, x_dir)
    base = start - y_dir * thickness / 2
    return UprightBox(base=base, x_dir=x_dir, y_dir=y_dir, length=float(np.linalg.norm((end - start)[:2])),
                      width=thickness, height=height, bottom=float(start[2]), top=float(start[2] + height))


def box_from_rect(corner, du, dv, bottom, top):
    """Upright box over a level rectangle drawn along world X (du) and Y (dv)."""
    c = np.asarray(corner, dtype=float)
    x0, x1 = sorted((c[0], c[0] + du))
    y0, y1 = sorted((c[1], c[1] + dv))
    return UprightBox(base=np.array((x0, y0, bottom)), x_dir=np.array((1.0, 0, 0)), y_dir=np.array((0, 1.0, 0)),
                      length=x1 - x0, width=y1 - y0, height=top - bottom, bottom=bottom, top=top)


def placement(origin, x_dir):
    """4x4 matrix: origin, X along x_dir (horizontal), Z up."""
    m = np.eye(4)
    m[:3, 0] = x_dir
    m[:3, 1] = np.cross(Z, x_dir)
    m[:3, 2] = Z
    m[:3, 3] = origin
    return m


def wall_from_box(box):
    """Wall axis along the long side, centred in the box width, at the base level.
    Returns (placement matrix, length, height)."""
    start = box.base + box.y_dir * box.width / 2
    return placement(start, box.x_dir), box.length, box.height


def slab_from_box(box, thickness):
    """Slab with its TOP at the top of the box. Returns (placement, footprint (2D local), thickness)."""
    origin = box.base.copy()
    origin[2] = box.top - thickness
    return placement(origin, box.x_dir), [(0.0, 0.0), (box.length, 0.0), (box.length, box.width), (0.0, box.width)]


def column_from_box(box):
    """Column centred in the footprint, from the base level. Returns (placement, height)."""
    return placement(box.center(), box.x_dir), box.height


def beam_placement(start, end, top, height):
    """A beam along start -> end (made level), its top at `top`, its section `height` tall (0.66):
    the placement has Z along the beam, X across it (to its left), Y up — the section's middle on
    that line, as IfcRectangleProfileDef is centred. Returns (placement, length)."""
    start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    d = normalize((end - start) * np.array((1, 1, 0)))
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2] = np.cross(Z, d), Z, d
    m[:3, 3] = (start[0], start[1], top - height / 2)
    return m, float(np.linalg.norm((end - start)[:2]))


def segment_placement(start, end, x_hint=None):
    """A pipe / duct along start -> end in 3D (0.136: level as before, sloped, or vertical): Z along it, X across
    it and level (to its left; a vertical one's: x_hint, default the red axis), Y = Z × X (up, for a level one) —
    its section's middle on that line. Returns (placement, length)."""
    start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    d = normalize(end - start)
    x = np.cross(Z, d)
    if np.linalg.norm(x) < 1e-9:
        hint = np.array((1.0, 0.0, 0.0)) if x_hint is None else np.asarray(x_hint, dtype=float) * np.array((1, 1, 0))
        x = hint if np.linalg.norm(hint) > 1e-9 else np.array((1.0, 0.0, 0.0))
    x = normalize(x)
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2] = x, np.cross(d, x), d
    m[:3, 3] = start
    return m, float(np.linalg.norm(end - start))


def beam_from_box(box, height):
    """A beam along a box's long side, in its middle, its top at the box's top."""
    start = box.base + box.y_dir * box.width / 2
    return beam_placement(start, start + box.x_dir * box.length, box.top, height)
