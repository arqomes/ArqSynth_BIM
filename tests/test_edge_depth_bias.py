"""(0.532) Edges drawn exactly on the faces: a line lying ON a face shows in front of it (depth bias in the line
shader), with no offset in space — up close it stays on the face's edge instead of floating pixels away.
(0.537) Also without perspective (plans, sections): there the bias is a fixed 2 mm — 0.5 % of the distance pushed every
line past the near plane, and a line a little behind a face must stay hidden. (A unittest, so that the unit suite —
unittest discover — runs it: as plain pytest functions it never ran there.)"""

import unittest

import numpy as np


def _render(line_z, ortho=False):
    import arqbim.render  # noqa: F401  (patches the line shader)
    import pygfx as gfx
    try:
        from rendercanvas.offscreen import RenderCanvas
    except ImportError:
        from wgpu.gui.offscreen import WgpuCanvas as RenderCanvas
    canvas = RenderCanvas(size=(200, 200), pixel_ratio=1)
    renderer = gfx.renderers.WgpuRenderer(canvas)
    scene = gfx.Scene()
    scene.add(gfx.Background.from_color("#000000"))
    plane = gfx.Mesh(gfx.plane_geometry(100, 100), gfx.MeshBasicMaterial(color="#ffffff"))
    scene.add(plane)
    seg = np.array([[-50, 0, line_z], [50, 0, line_z]], np.float32)
    scene.add(gfx.Line(gfx.Geometry(positions=seg), gfx.LineSegmentMaterial(thickness=4, color="#ff0000")))
    if ortho:                              # (as a plan: from above, far away, the viewport's clip range)
        camera = gfx.OrthographicCamera(10, 10)
        camera.local.position = (0, 0, 30)
        camera.look_at((0, 0, 0))
        camera.depth_range = (30 / 150, 30 * 3000)
    else:
        camera = gfx.PerspectiveCamera(50)
        camera.local.position = (0, -3, 4)
        camera.look_at((0, 0, 0))
    canvas.request_draw(lambda: renderer.render(scene, camera))
    return np.asarray(canvas.draw())


def _red(img):
    return int(((img[..., 0] > 200) & (img[..., 1] < 80)).sum())


class EdgeDepthBias(unittest.TestCase):
    def _draw(self, *args, **kw):
        try:
            return _render(*args, **kw)
        except Exception as exc:  # no GPU adapter here
            self.skipTest(f"no offscreen GPU: {exc}")

    def test_line_on_face_is_drawn_in_front(self):
        self.assertGreaterEqual(_red(self._draw(0.0)), 400)   # the whole line, not hidden by (nor fighting) its face

    def test_line_on_face_without_perspective(self):
        on, behind = self._draw(0.0, ortho=True), self._draw(-0.1, ortho=True)
        self.assertGreaterEqual(_red(on), 400)    # on the face: seen (0.532: clipped away, nothing of it)
        self.assertEqual(_red(behind), 0)         # 10 cm under it: hidden by the face


if __name__ == "__main__":
    unittest.main()
