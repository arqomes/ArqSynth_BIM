"""The only modules that talk to the GPU (wgpu through pygfx).

Windows' Smart App Control may block a library file that is not signed: on 2026-10-22 it
blocked uharfbuzz's (`_harfbuzz.pyd`), which pygfx imports to lay out the texts of the 3D view
— without it pygfx does not load and the program does not open. Then pygfx's own FreeType text
layout (its `shape_text_ft`, kept as a fallback) is used instead: enough for the program's
labels (measures, names: no ligatures to make). Nothing in Windows is changed.

In Linux on Windows (WSL, scripts/arqbim_wsl.sh) the graphics card is reached through OpenGL
(Mesa's d3d12 driver; WSL has no Vulkan driver for it): that OpenGL cannot filter 32-bit float
textures, which pygfx asks for by default (for volume rendering). ArqBIM draws no such texture
(meshes, lines, points, text from an 8-bit atlas), so the request is dropped — the way pygfx
documents for older hardware (enable_wgpu_features("!float32-filterable")).
Also through that OpenGL, a text kept the same size on screen (screen_space: the snap tips, the
dimensions' values, the measures while drawing) was not drawn at all (found 2026-10-22): its
shader turns each letter by a 2×2 matrix (`rot_scale_transform`) that reaches OpenGL's uniform
buffer with another layout, so every letter had no size. ArqBIM never turns nor scales those
texts: the shader is given the letters as they are.
"""

import logging
import os
import sys
import types

try:
    import uharfbuzz  # noqa: F401
    HARFBUZZ = True
except ImportError as exc:          # blocked (or missing): pygfx only needs the name when it loads
    HARFBUZZ = False
    logging.getLogger(__name__).warning("uharfbuzz not loaded (%s): texts laid out with FreeType", exc)
    sys.modules["uharfbuzz"] = types.ModuleType("uharfbuzz")

import pygfx  # noqa: E402

if not HARFBUZZ:
    from pygfx.utils.text import _shaper
    _shaper.shape_text_hb = _shaper.shape_text_ft
    pygfx.Text._text_engine.shape_text = _shaper.shape_text_ft

# (0.532) Lines drawn a hair in front of the faces they lie on by DEPTH, along the line of sight (z' = z - k(w - z):
# a fixed fraction of the distance to the eye, so on screen the line stays exactly on the face's edge at any zoom).
# Before, the edges were moved 2 mm out along the faces' normals: up close that was many pixels off the solid.
LINE_DEPTH_BIAS = 0.005             # 0.5 % of the distance (0.002 still left half a thick line in a slanted face)
# (0.537) Without perspective (plans, sections, elevations, axonometries) the depth is linear and the clip range is
# thousands of times deeper than the model (Viewport._set_focus: far = 3000 × the distance), so the whole model lies in
# the first thousandth of it: k(w − z) = 0.5 % pushed every line past the near plane — clipped away (the walls' cut
# hatch, the elevation marks, every edge: white walls in every plan since 0.532). There the lines go a fixed hair nearer
# instead, in metres (the 2 mm the edges were lifted by before 0.532): δ·|P[2][2]| in depth (P = the projection; its
# P[3][3] is 1 without perspective, 0 with it). And never pushed out of the near plane (z < 0 is clipped).
LINE_DEPTH_ORTHO = 0.002            # m
from pygfx.renderers.wgpu.shaders import lineshader as _lineshader  # noqa: E402

_line_code = _lineshader.LineShader.get_code


def _line_code_in_front(self):
    return _line_code(self).replace(
        "varyings.position = vec4<f32>(the_pos_n);",
        "let line_ortho = u_stdinfo.projection_transform[3][3];\n"
        f"    let line_bias = mix({LINE_DEPTH_BIAS} * (the_pos_n.w - the_pos_n.z),"
        f" {LINE_DEPTH_ORTHO} * abs(u_stdinfo.projection_transform[2][2]), line_ortho);\n"
        "    varyings.position = vec4<f32>(the_pos_n.xy, max(the_pos_n.z - line_bias, min(the_pos_n.z, 0.0)),"
        " the_pos_n.w);", 1)


_lineshader.LineShader.get_code = _line_code_in_front

if os.environ.get("WGPU_BACKEND_TYPE", "").strip().lower() == "opengl":
    pygfx.renderers.wgpu.enable_wgpu_features("!float32-filterable")

    from pygfx.renderers.wgpu.shaders import textshader

    _text_code = textshader.TextShader.get_code

    def _text_code_for_opengl(self):
        return _text_code(self).replace("u_wobject.rot_scale_transform * vec2<f32>(vertex_pos)",
                                        "vec2<f32>(vertex_pos)")

    textshader.TextShader.get_code = _text_code_for_opengl
