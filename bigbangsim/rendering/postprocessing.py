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
        self.hdr_texture = ctx.texture((width, height), 4, dtype="f2")
        self.hdr_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.hdr_depth = ctx.depth_renderbuffer((width, height))
        self.hdr_fbo = ctx.framebuffer(
            color_attachments=[self.hdr_texture],
            depth_attachment=self.hdr_depth,
        )

        # --- Bloom FBO (half resolution for performance) ---
        hw, hh = width // 2, height // 2
        self.bloom_texture = ctx.texture((hw, hh), 4, dtype="f2")
        self.bloom_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.bloom_fbo = ctx.framebuffer(color_attachments=[self.bloom_texture])

        # --- Ping-pong blur FBOs (half resolution) ---
        self.blur_textures = [
            ctx.texture((hw, hh), 4, dtype="f2"),
            ctx.texture((hw, hh), 4, dtype="f2"),
        ]
        for tex in self.blur_textures:
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.blur_fbos = [
            ctx.framebuffer(color_attachments=[self.blur_textures[0]]),
            ctx.framebuffer(color_attachments=[self.blur_textures[1]]),
        ]

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
        """Bind the HDR FBO for scene rendering. Call before rendering particles."""
        self.hdr_fbo.use()
        self.hdr_fbo.clear(0.0, 0.0, 0.0, 0.0)

    def end_scene(self, target_fbo=None) -> None:
        """Run the bloom + tone mapping chain, output to target_fbo or screen.

        Args:
            target_fbo: Target framebuffer. If None, renders to ctx.fbo
                       (moderngl-window's default framebuffer).
        """
        # Post-processing is 2D screen-space — disable depth test and blending
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.BLEND)

        # Pass 1: Bright-pass extraction -> bloom FBO (half-res)
        self.bloom_fbo.use()
        self.bloom_fbo.clear(0.0, 0.0, 0.0, 0.0)
        self.hdr_texture.use(location=0)
        self.bright_prog["u_scene"].value = 0
        self.bright_prog["u_threshold"].value = self.bloom_threshold
        self._render_quad(self.bright_prog)

        # Pass 2-3: Gaussian blur iterations (ping-pong between blur FBOs)
        horizontal = True
        first_pass = True
        for _i in range(self.blur_iterations):
            target_idx = 1 if horizontal else 0
            self.blur_fbos[target_idx].use()
            self.blur_fbos[target_idx].clear(0.0, 0.0, 0.0, 0.0)

            if first_pass:
                self.bloom_texture.use(location=0)
                first_pass = False
            else:
                source_idx = 0 if horizontal else 1
                self.blur_textures[source_idx].use(location=0)

            self.blur_prog["u_image"].value = 0
            self.blur_prog["u_horizontal"].value = horizontal
            self._render_quad(self.blur_prog)

            horizontal = not horizontal

        # Pass 4: Composite (HDR + bloom) + tone mapping -> screen
        if target_fbo is not None:
            target_fbo.use()
        else:
            self.ctx.fbo.use()  # moderngl-window's default framebuffer

        self.hdr_texture.use(location=0)
        # Last blur result is in the FBO we wrote to last
        last_blur_idx = 0 if horizontal else 1
        self.blur_textures[last_blur_idx].use(location=1)

        self.tonemap_prog["u_scene"].value = 0
        self.tonemap_prog["u_bloom"].value = 1
        self.tonemap_prog["u_exposure"].value = self.exposure
        self.tonemap_prog["u_bloom_strength"].value = self.bloom_strength
        self._render_quad(self.tonemap_prog)

    def resize(self, width: int, height: int) -> None:
        """Recreate FBOs for new window dimensions. Call on window resize.

        Args:
            width: New window width in pixels.
            height: New window height in pixels.
        """
        # Release old resources
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
        self.hdr_texture = self.ctx.texture((width, height), 4, dtype="f2")
        self.hdr_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.hdr_depth = self.ctx.depth_renderbuffer((width, height))
        self.hdr_fbo = self.ctx.framebuffer(
            color_attachments=[self.hdr_texture],
            depth_attachment=self.hdr_depth,
        )

        hw, hh = width // 2, height // 2
        self.bloom_texture = self.ctx.texture((hw, hh), 4, dtype="f2")
        self.bloom_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.bloom_fbo = self.ctx.framebuffer(
            color_attachments=[self.bloom_texture]
        )

        self.blur_textures = [
            self.ctx.texture((hw, hh), 4, dtype="f2"),
            self.ctx.texture((hw, hh), 4, dtype="f2"),
        ]
        for tex in self.blur_textures:
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.blur_fbos = [
            self.ctx.framebuffer(color_attachments=[self.blur_textures[0]]),
            self.ctx.framebuffer(color_attachments=[self.blur_textures[1]]),
        ]

    def release(self) -> None:
        """Release all GPU resources."""
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
