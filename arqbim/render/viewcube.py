"""The view cube (0.79; as Revit's ViewCube, 0.81): in the 3D view's top-right corner, a cube that turns with
the camera, on a compass ring.

- A click on a face looks from that side; on an edge or a corner, from between them (the model framed, the
  camera turning smoothly). The part under the mouse is lit in blue.
- Dragging the cube orbits round the model; dragging the ring turns it round (as a turntable); a click on a
  letter of the ring (N, E, S, O) looks from that side, as high as before (seen from above: that side at the top).
- Seen square from a face: four triangles beside the cube go to the face next to it; two curved arrows roll the
  view 90°.
- The house goes to the starting view (or the one set as it); the ▾ opens a menu (the window's).
- Half see-through with the mouse elsewhere.

Two scenes drawn into the corner square after the model: the cube and its ring (no depth test — the ring first,
then the faces turned towards the camera: a cube is convex, they never cover one another), and the buttons, flat
on the square. Every picture (the faces' names, the ring's letters, the buttons) is made by the window with Qt:
no text shader. Clicks are worked out here, by casting a ray at the cube and its ring."""

import math

import numpy as np
import pygfx as gfx

SIZE_PX = 150                   # the corner square (logical pixels)
MARGIN_PX = 6                   # from the view's top-right corner
SPAN = 2.5                      # cube units across the square: the cube (1) and its ring
EDGE = 0.22                     # a click this near a face's border (of 1) is on its edge / corner
RING_IN, RING_OUT, RING_Z = 0.82, 1.15, -0.5
LETTER_DEG = 22                 # a click on the ring this near a letter (in angle) is on it
BUTTON_PX, ARROW_PX = 20, 14
INACTIVE = 0.55                 # how opaque it is with the mouse elsewhere
SQUARE_COS = math.cos(math.radians(4.0))    # looking this square at a face: its triangles and roll arrows show
HIGHLIGHT = (0.20, 0.55, 0.95, 0.55)

# the six faces: (name, outward normal, the face's "up" as seen from outside)
FACES = (("top", (0, 0, 1), (0, 1, 0)), ("bottom", (0, 0, -1), (0, -1, 0)),
         ("front", (0, -1, 0), (0, 0, 1)), ("back", (0, 1, 0), (0, 0, 1)),
         ("right", (1, 0, 0), (0, 0, 1)), ("left", (-1, 0, 0), (0, 0, 1)))
CARDINALS = {"N": (0.0, 1.0), "E": (1.0, 0.0), "S": (0.0, -1.0), "W": (-1.0, 0.0)}


def _material(cls=gfx.MeshBasicMaterial, **kw):
    return cls(depth_test=False, depth_write=False, alpha_mode="blend", **kw)


def _quad(corners, uv=((0, 1), (1, 1), (1, 0), (0, 0))):
    return gfx.Geometry(positions=np.array(corners, np.float32), indices=np.array([[0, 1, 2], [0, 2, 3]], np.uint32),
                        texcoords=np.array(uv, np.float32))


def _texture(image):
    return gfx.Texture(np.ascontiguousarray(image), dim=2)


class ViewCube:
    def __init__(self, images):
        """images: {face name: picture of its label, "ring", "home", "roll_ccw", "roll_cw", "menu", "arrow"} —
        (H, W, 4) uint8 RGBA."""
        self.scene = gfx.Scene()
        self.camera = gfx.OrthographicCamera(SPAN, SPAN)
        r = RING_OUT
        self.ring = gfx.Mesh(_quad([(-r, -r, RING_Z), (r, -r, RING_Z), (r, r, RING_Z), (-r, r, RING_Z)]),
                             _material(map=_texture(images["ring"]), side="both"))
        self.scene.add(self.ring)
        self.faces = {}
        for name, normal, up in FACES:
            n, u = np.array(normal, float), np.array(up, float)
            right = np.cross(u, n)
            corners = [0.5 * n + 0.5 * (sx * right + sy * u) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            mesh = gfx.Mesh(_quad(corners), _material(map=_texture(images[name]), side="front"))
            self.faces[name] = mesh
            self.scene.add(mesh)
        self.lit = gfx.Mesh(_quad([(0, 0, 0)] * 4), _material(color=HIGHLIGHT, side="front"))
        self.lit.visible = False
        self.scene.add(self.lit)
        # the outline: only the edges of the faces turned towards the camera (no depth test: the hidden ones
        # would show through)
        self.corners = np.array([(x, y, z) for x in (-0.5, 0.5) for y in (-0.5, 0.5) for z in (-0.5, 0.5)], np.float32)
        edges = [(i, j) for i in range(8) for j in range(i + 1, 8) if np.sum(self.corners[i] != self.corners[j]) == 1]
        self.face_edges = {}
        for name, normal, _up in FACES:
            axis = int(np.argmax(np.abs(normal)))
            side = 0.5 * normal[axis]
            self.face_edges[name] = [e for e in edges if all(self.corners[k][axis] == side for k in e)]
        self.outline = gfx.Line(gfx.Geometry(positions=np.zeros((2, 3), np.float32)),
                                _material(gfx.LineSegmentMaterial, thickness=1.2, color="#5a6470", aa=True))
        self.scene.add(self.outline)
        self.seen = None              # the faces turned towards the camera
        # the buttons, flat on the square: x right, y up, one unit a pixel
        self.ui = gfx.Scene()
        self.ui_camera = gfx.OrthographicCamera(SIZE_PX, SIZE_PX)
        self.ui_camera.local.position = (SIZE_PX / 2, -SIZE_PX / 2, 10.0)
        self.buttons = {}
        for name, (x, y, w, h), image, turn in self._layout(images):
            uv = [(0, 1), (1, 1), (1, 0), (0, 0)]
            uv = uv[turn:] + uv[:turn]                     # (the one triangle turned for each side)
            mesh = gfx.Mesh(_quad([(x, -y - h, 0), (x + w, -y - h, 0), (x + w, -y, 0), (x, -y, 0)], uv),
                            _material(map=_texture(image)))
            self.buttons[name] = (mesh, (x, y, w, h))
            self.ui.add(mesh)
        self.hover = None             # the part under the mouse
        self.active = None            # the mouse over the square (opaque) or not
        self.square = None            # looking square at a face (its triangles and roll arrows shown)
        self.set_active(False)

    @staticmethod
    def _layout(images):
        b, a, c = BUTTON_PX, ARROW_PX, SIZE_PX / 2
        half = 0.5 / (SPAN / 2) * SIZE_PX / 2               # the cube's half side on the screen, seen square
        gap = half + 3
        return (("home", (2, 2, b, b), images["home"], 0),
                ("roll_ccw", (SIZE_PX - 2 * b - 4, 2, b, b), images["roll_ccw"], 0),
                ("roll_cw", (SIZE_PX - b - 2, 2, b, b), images["roll_cw"], 0),
                ("menu", (SIZE_PX - b - 2, SIZE_PX - b - 2, b, b), images["menu"], 0),
                ("up", (c - a / 2, c - gap - a, a, a), images["arrow"], 0),
                ("right", (c + gap, c - a / 2, a, a), images["arrow"], 1),
                ("down", (c - a / 2, c + gap, a, a), images["arrow"], 2),
                ("left", (c - gap - a, c - a / 2, a, a), images["arrow"], 3))

    # ------------------------------------------------------------ drawing

    def rect(self, size):
        """(x, y, w, h) of its square in the view (logical pixels)."""
        w, _h = size
        return (w - SIZE_PX - MARGIN_PX, MARGIN_PX, SIZE_PX, SIZE_PX)

    def follow(self, rotation):
        """Turned as the view's camera is (its rotation quaternion)."""
        self.camera.local.rotation = tuple(rotation)
        forward = np.asarray(self.camera.world.forward, float)
        self.camera.local.position = tuple(-forward * 5.0)
        seen = frozenset(name for name, normal, _up in FACES if -forward @ normal > 1e-3)
        if seen != self.seen:
            self.seen = seen
            pairs = sorted({e for name in seen for e in self.face_edges[name]})
            self.outline.geometry = gfx.Geometry(positions=self.corners[[k for e in pairs for k in e]])
        # each face a little darker the more it turns from a light over the viewer's left shoulder
        light = -forward + 0.7 * np.asarray(self.camera.world.up, float) - 0.35 * np.asarray(self.camera.world.right,
                                                                                               float)
        light /= np.linalg.norm(light)
        for name, normal, _up in FACES:
            shade = 0.80 + 0.20 * max(float(light @ normal), 0.0)
            self.faces[name].material.color = (shade, shade, shade, 1.0)
        square = float(np.max(np.abs(forward))) > SQUARE_COS
        if square != self.square:
            self.square = square
            for name in ("roll_ccw", "roll_cw", "up", "right", "down", "left"):
                self.buttons[name][0].visible = square

    def render(self, renderer, size):
        rect = self.rect(size)
        renderer.render(self.scene, self.camera, rect=rect, flush=False)
        renderer.render(self.ui, self.ui_camera, rect=rect, flush=False)

    def set_active(self, on):
        """Opaque with the mouse over it, half see-through otherwise. True if it changed."""
        if on == self.active:
            return False
        self.active = on
        alpha = 1.0 if on else INACTIVE
        for mesh in [self.ring, self.outline, *self.faces.values()] + [m for m, _r in self.buttons.values()]:
            mesh.material.opacity = alpha
        return True

    def set_hover(self, part):
        """The part under the mouse lit: the face, the edge's two strips, the corner's three squares; a button
        or the ring fully opaque. True if it changed."""
        if part == self.hover:
            return False
        self.hover = part
        self.lit.visible = False
        for name, (mesh, _r) in self.buttons.items():
            mesh.material.color = "#ffffff" if part == ("button", name) else "#e6e9ee"
        self.ring.material.color = "#ffffff" if part is not None and part[0] in ("compass", "ring") else "#f0f2f5"
        if part is not None and part[0] == "cube":
            quads = _lit_quads(np.asarray(part[1], float))
            if quads:
                pts = np.array([p for q in quads for p in q], np.float32)
                idx = np.array([[4 * k, 4 * k + 1, 4 * k + 2, 4 * k, 4 * k + 2, 4 * k + 3]
                                for k in range(len(quads))], np.uint32).reshape(-1, 3)
                self.lit.geometry = gfx.Geometry(positions=pts, indices=idx)
                self.lit.visible = True
        return True

    # ------------------------------------------------------------ clicks

    def inside(self, x, y, size):
        rx, ry, rw, rh = self.rect(size)
        return rx <= x <= rx + rw and ry <= y <= ry + rh

    def center(self, size):
        rx, ry, rw, rh = self.rect(size)
        return rx + rw / 2, ry + rh / 2

    def hit(self, x, y, size):
        """What is under (x, y): ("button", name) — home, roll_ccw, roll_cw, menu, up / right / down / left —,
        ("cube", direction from the model to the eye), ("compass", (dx, dy) of the letter), ("ring",), or None."""
        if not self.inside(x, y, size):
            return None
        rx, ry, rw, rh = self.rect(size)
        u, v = x - rx, y - ry
        for name, (mesh, (bx, by, bw, bh)) in self.buttons.items():
            if mesh.visible and bx <= u <= bx + bw and by <= v <= by + bh:
                return ("button", name)
        origin, d = self._ray(2.0 * u / rw - 1.0, 1.0 - 2.0 * v / rh)
        on_cube = _cube_hit(origin, d)
        if on_cube is not None:
            return ("cube", tuple(on_cube))
        if abs(d[2]) > 1e-9:
            p = origin + d * ((RING_Z - origin[2]) / d[2])
            r = float(np.hypot(p[0], p[1]))
            if RING_IN * 0.9 <= r <= RING_OUT:
                angle = math.degrees(math.atan2(p[1], p[0]))
                for letter, (cx, cy) in CARDINALS.items():
                    gap = abs((angle - math.degrees(math.atan2(cy, cx)) + 180) % 360 - 180)
                    if gap <= LETTER_DEG:
                        return ("compass", (cx, cy))
                return ("ring",)
        return None

    def _ray(self, nx, ny):
        inverse = np.linalg.inv(np.asarray(self.camera.camera_matrix, float))
        near, far = inverse @ np.array((nx, ny, 0.0, 1.0)), inverse @ np.array((nx, ny, 1.0, 1.0))
        origin = near[:3] / near[3]
        return origin, far[:3] / far[3] - origin


def _cube_hit(origin, d):
    """The direction (±1 on each axis it is near: a face, an edge, a corner) of where the ray meets the cube."""
    with np.errstate(divide="ignore", invalid="ignore"):
        t1, t2 = (-0.5 - origin) / d, (0.5 - origin) / d
    t_near, t_far = np.nanmax(np.minimum(t1, t2)), np.nanmin(np.maximum(t1, t2))
    if not np.isfinite(t_near) or t_near > t_far:
        return None
    p = origin + d * t_near
    out = np.where(np.abs(p) > 0.5 - EDGE, np.sign(p), 0.0)
    return out if out.any() else None


def _lit_quads(direction, lift=0.004):
    """The patches of the cube's faces that a direction (a face, edge or corner) covers: on each face it touches,
    the middle square (a face), a strip along the edge, or the corner's square."""
    quads = []
    inner = 0.5 - EDGE
    for axis in range(3):
        side = direction[axis]
        if side == 0:
            continue
        a, b = [k for k in range(3) if k != axis]
        spans = []
        for k in (a, b):
            s = direction[k]
            spans.append((inner, 0.5) if s > 0 else (-0.5, -inner) if s < 0 else (-inner, inner))
        (a0, a1), (b0, b1) = spans
        quad = []
        for ca, cb in ((a0, b0), (a1, b0), (a1, b1), (a0, b1)):
            p = np.zeros(3)
            p[axis], p[a], p[b] = side * (0.5 + lift), ca, cb
            quad.append(p)
        normal = np.zeros(3)
        normal[axis] = side
        if np.dot(np.cross(quad[1] - quad[0], quad[2] - quad[0]), normal) < 0:
            quad.reverse()                                # (facing out: drawn only from the front)
        quads.append(quad)
    return quads
