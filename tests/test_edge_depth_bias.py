"""(0.532) Edges drawn exactly on the faces: a line lying ON a face shows in front of it (depth bias in the line
shader), with no offset in space — up close it stays on the face's edge instead of floating pixels away."""

import numpy as np
import pytest


def _render(line_z):
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
    camera = gfx.PerspectiveCamera(50)
    camera.local.position = (0, -3, 4)
    camera.look_at((0, 0, 0))
    canvas.request_draw(lambda: renderer.render(scene, camera))
    return np.asarray(canvas.draw())


def test_line_on_face_is_drawn_in_front():
    try:
        img = _render(0.0)
    except Exception as exc:  # no GPU adapter here
        pytest.skip(f"no offscreen GPU: {exc}")
    red = (img[..., 0] > 200) & (img[..., 1] < 80)
    assert red.sum() >= 400           # the whole line shows, not hidden by (nor fighting with) its face
