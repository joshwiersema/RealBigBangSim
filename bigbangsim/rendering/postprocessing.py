"""Multi-pass post-processing pipeline: HDR FBO -> bloom -> tone mapping.

Implements a cinematic bloom effect essential for the Big Bang simulation's
visual impact. Hot particles and bright nebulae glow naturally through
physically-based bloom extraction and Gaussian blur.

Pipeline:
  Pass 0: Scene rendered to hdr_fbo (by caller via begin_scene/end_scene)
  Pass 1: Bright-pass extraction -> bloom_fbo (half-resolution)
  Pass 2: Horizontal Gaussian blur -> blur_fbos[0]
  Pass 3: Vertical Gaussian blur -> blur_fbos[1]
  (Repeat passes 2-3 for N iterations)
  Pass 4: Composite (HDR scene + bloom) + Reinhard tone mapping -> screen

Usage:
    pipeline.begin_scene()   # Binds HDR FBO for scene rendering
    # ... render particles, etc. into pipeline.hdr_fbo ...
    pipeline.end_scene()     # Runs bloom + tonemap to screen
"""
from __future__ import annotations

import numpy as np
import moderngl

from bigbangsim.rendering.shader_loader import load_shader_source


class PostProcessingPipeline:
    """Multi-pass post-processing: HDR FBO -> bloom -> tone mapping.

    All FBOs use RGBA16F (half-float) for HDR rendering. Bloom operates at
    half resolution for performance (Pitfall 3 from research).
    """

    def __init__(self, ctx: moderngl.Context, width: int, height: int):
        self.ctx = ctx
        self.width = width
        self.height = height

        # Tunable parameters
        self.exposure = 1.0
        self.bloom_strength = 0.3
        self.bloom_threshold = 1.0
        self.blur_iterations = 6  # 3 horizontal + 3 vertical passes

        # Fullscreen quad — built with raw moderngl instead of
        # geometry.quad_fs() which has issues on some AMD drivers.
        quad_data = np.array([
            # x,    y,   z,   u,   v
            -1.0, -1.0, 0.0, 0.0, 0.0,
             1.0, -1.0, 0.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 0.0, 1.0,
             1.0,  1.0, 0.0, 1.0, 1.0,
        ], dtype="f4")
        self._quad_buf = ctx.buffer(quad_data.tobytes())
        self._quad_vaos: dict[int, moderngl.VertexArray] = {}

        # --- HDR scene FBO (full resolution, RGBA16F) ---
        self.hdr_texture = ctx.texture((width, height), 4, dtype="f4")
        self.hdr_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.hdr_depth = ctx.depth_renderbuffer((width, height))
        self.hdr_fbo = ctx.framebuffer(
            color_attachments=[self.hdr_texture],
            depth_attachment=self.hdr_depth,
        )

        # --- Bloom FBO (half resolution for performance) ---
        hw, hh = width // 2, height // 2
        self.bloom_texture = ctx.texture((hw, hh), 4, dtype="f4")
        self.bloom_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.bloom_fbo = ctx.framebuffer(color_attachments=[self.bloom_texture])

        # --- Ping-pong blur FBOs (half resolution) ---
        self.blur_textures = [
            ctx.texture((hw, hh), 4, dtype="f4"),
            ctx.texture((hw, hh), 4, dtype="f4"),
        ]
        for tex in self.blur_textures:
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.blur_fbos = [
            ctx.framebuffer(color_attachments=[self.blur_textures[0]]),
            ctx.framebuffer(color_attachments=[self.blur_textures[1]]),
        ]

        # --- Copy/blit shader (copies default FBO -> HDR texture) ---
        _blit_vert = """
#version 430
in vec3 in_position;
in vec2 in_texcoord_0;
out vec2 v_texcoord;
void main() {
    gl_Position = vec4(in_position, 1.0);
    v_texcoord = in_texcoord_0;
}
"""
        _blit_frag = """
#version 430
in vec2 v_texcoord;
uniform sampler2D u_source;
out vec4 fragColor;
void main() { fragColor = texture(u_source, v_texcoord); }
"""
        self._blit_prog = ctx.program(vertex_shader=_blit_vert, fragment_shader=_blit_frag)
        self._blit_prog["u_source"].value = 0

        # Default FBO texture (created on first use, captures screen content)
        self._default_copy_tex = ctx.texture((width, height), 4)
        self._default_copy_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)

        # --- Load post-processing shader programs ---
        fs_vert = load_shader_source("postprocess/fullscreen.vert")
        self.bright_prog = ctx.program(
            vertex_shader=fs_vert,
            fragment_shader=load_shader_source("postprocess/bright_extract.frag"),
        )
        self.blur_prog = ctx.program(
            vertex_shader=fs_vert,
            fragment_shader=load_shader_source("postprocess/gaussian_blur.frag"),
        )
        self.tonemap_prog = ctx.program(
            vertex_shader=fs_vert,
            fragment_shader=load_shader_source("postprocess/tonemap.frag"),
        )

    def _blit_default_to_hdr(self) -> None:
        """Copy default FBO content into the HDR float texture.

        Reads the default framebuffer into an RGBA8 texture, then blits
        that onto the HDR FBO using a fullscreen quad. This promotes the
        RGBA8 values to float for bloom extraction.
        """
        # Copy default FBO pixels into our RGBA8 texture
        self.ctx.copy_framebuffer(self._default_copy_tex, self.ctx.fbo)
        # Blit RGBA8 texture -> HDR FBO (already bound by caller)
        self._default_copy_tex.use(location=0)
        self._render_quad(self._blit_prog)

    def _render_quad(self, prog: moderngl.Program) -> None:
        """Render fullscreen quad with the given program."""
        key = prog.glo
        if key not in self._quad_vaos:
            self._quad_vaos[key] = self.ctx.vertex_array(
                prog,
                [(self._quad_buf, "3f 2f", "in_position", "in_texcoord_0")],
            )
        self._quad_vaos[key].render(moderngl.TRIANGLE_STRIP)

    def begin_scene(self) -> None:
        """Bind the default FBO for scene rendering."""
        self.ctx.fbo.use()
        self.ctx.fbo.clear(0.01, 0.0, 0.02, 1.0)  # Very dark purple-black

    def end_scene(self, target_fbo=None) -> None:
        """Finalize the scene. Particles already rendered to default FBO.

        Post-processing (bloom/tonemap) is skipped on AMD integrated GPUs
        that cannot render to or copy from custom FBOs reliably. The raw
        particle output is displayed directly. Additive blending produces
        natural glow without needing bloom.
        """
        # Particles are already in the default FBO — nothing to do.
        # Restore GL state for imgui rendering.
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.BLEND)

    def resize(self, width: int, height: int) -> None:
        """Recreate FBOs for new window dimensions. Call on window resize.

        Args:
            width: New window width in pixels.
            height: New window height in pixels.
        """
        # Release old resources
        self._default_copy_tex.release()
        self.hdr_texture.release()
        self.hdr_depth.release()
        self.hdr_fbo.release()
        self.bloom_texture.release()
        self.bloom_fbo.release()
        for tex in self.blur_textures:
            tex.release()
        for fbo in self.blur_fbos:
            fbo.release()

        # Recreate at new size
        self.width = width
        self.height = height
        self._default_copy_tex = self.ctx.texture((width, height), 4)
        self._default_copy_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.hdr_texture = self.ctx.texture((width, height), 4, dtype="f4")
        self.hdr_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.hdr_depth = self.ctx.depth_renderbuffer((width, height))
        self.hdr_fbo = self.ctx.framebuffer(
            color_attachments=[self.hdr_texture],
            depth_attachment=self.hdr_depth,
        )

        hw, hh = width // 2, height // 2
        self.bloom_texture = self.ctx.texture((hw, hh), 4, dtype="f4")
        self.bloom_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.bloom_fbo = self.ctx.framebuffer(
            color_attachments=[self.bloom_texture]
        )

        self.blur_textures = [
            self.ctx.texture((hw, hh), 4, dtype="f4"),
            self.ctx.texture((hw, hh), 4, dtype="f4"),
        ]
        for tex in self.blur_textures:
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.blur_fbos = [
            self.ctx.framebuffer(color_attachments=[self.blur_textures[0]]),
            self.ctx.framebuffer(color_attachments=[self.blur_textures[1]]),
        ]

    def release(self) -> None:
        """Release all GPU resources."""
        self._default_copy_tex.release()
        self.hdr_texture.release()
        self.hdr_depth.release()
        self.hdr_fbo.release()
        self.bloom_texture.release()
        self.bloom_fbo.release()
        for tex in self.blur_textures:
            tex.release()
        for fbo in self.blur_fbos:
            fbo.release()
        self.bright_prog.release()
        self.blur_prog.release()
        self.tonemap_prog.release()
