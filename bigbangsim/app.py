"""Main application window for BigBangSim.

Subclasses moderngl_window.WindowConfig to create an OpenGL 4.3 window
with GPU particle rendering, post-processing bloom pipeline, orbit camera,
simulation controls, and timeline bar.

PHYS-07: The render loop uses view_matrix_camera_relative() with double-precision
camera coordinates instead of the float32 camera.view_matrix property.
"""
import math

import glm
import numpy as np
import moderngl
import moderngl_window
from pathlib import Path

from bigbangsim.config import WINDOW_WIDTH, WINDOW_HEIGHT, PHYSICS_DT
from bigbangsim.simulation.engine import SimulationEngine
from bigbangsim.simulation.eras import ERAS
from bigbangsim.rendering.camera import DampedOrbitCamera
from bigbangsim.rendering.coordinates import view_matrix_camera_relative
from bigbangsim.rendering.particles import ParticleSystem
from bigbangsim.rendering.postprocessing import PostProcessingPipeline


class BigBangSimApp(moderngl_window.WindowConfig):
    """Phase 2 application: GPU particles + post-processing + camera + controls."""

    title = "BigBangSim - Cosmic Evolution"
    window_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
    gl_version = (4, 3)
    resource_dir = Path(__file__).parent / "shaders"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Simulation engine
        self.sim = SimulationEngine()

        # Camera
        self.camera = DampedOrbitCamera(
            radius=8.0,
            fov=60.0,
            near=0.01,
            far=1000.0,
            aspect=self.wnd.size[0] / self.wnd.size[1],
        )

        # GPU particle system (RNDR-01)
        self.particles = ParticleSystem(self.ctx, count=200_000)

        # Post-processing pipeline (RNDR-02)
        self.postfx = PostProcessingPipeline(
            self.ctx, self.wnd.size[0], self.wnd.size[1]
        )

        # Load timeline bar shader and create geometry
        self.timeline_bar_prog = self._load_shader("timeline_bar")
        self._create_timeline_bar()

    def _load_shader(self, name: str) -> moderngl.Program:
        """Load vertex + fragment shader pair from resource_dir."""
        vert_path = self.resource_dir / f"{name}.vert"
        frag_path = self.resource_dir / f"{name}.frag"
        return self.ctx.program(
            vertex_shader=vert_path.read_text(),
            fragment_shader=frag_path.read_text(),
        )

    def _create_timeline_bar(self):
        """Create timeline bar geometry as a horizontal bar at the bottom of the screen.

        Bar spans from x=-0.9 to x=0.9 in NDC, at y=-0.92 to y=-0.85.
        Each era gets a proportional segment colored by era index.
        """
        vertices = []
        total = sum(e.screen_seconds for e in ERAS)
        x_start = -0.9
        x_range = 1.8  # from -0.9 to +0.9

        # Era colors (11 distinct colors)
        era_colors = [
            (1.0, 1.0, 1.0),   # 0: Planck - white
            (0.8, 0.6, 1.0),   # 1: GUT - lavender
            (1.0, 0.9, 0.3),   # 2: Inflation - yellow
            (1.0, 0.3, 0.1),   # 3: QGP - orange-red
            (0.9, 0.5, 0.2),   # 4: Hadron - orange
            (0.3, 0.8, 0.3),   # 5: Nucleosynthesis - green
            (1.0, 0.8, 0.4),   # 6: CMB - warm yellow
            (0.15, 0.1, 0.2),  # 7: Dark Ages - near black
            (0.4, 0.6, 1.0),   # 8: First Stars - blue
            (0.6, 0.4, 0.8),   # 9: Galaxy Formation - purple
            (0.3, 0.5, 0.9),   # 10: Large-Scale Structure - deep blue
        ]

        cumulative = 0.0
        for i, era in enumerate(ERAS):
            x0 = x_start + (cumulative / total) * x_range
            x1 = x_start + ((cumulative + era.screen_seconds) / total) * x_range
            y0 = -0.92
            y1 = -0.85
            r, g, b = era_colors[i]
            # Two triangles per quad
            vertices.extend([
                x0, y0, r, g, b,
                x1, y0, r, g, b,
                x0, y1, r, g, b,
                x0, y1, r, g, b,
                x1, y0, r, g, b,
                x1, y1, r, g, b,
            ])
            cumulative += era.screen_seconds

        vert_arr = np.array(vertices, dtype=np.float32)
        vbo = self.ctx.buffer(vert_arr.tobytes())
        self.timeline_vao = self.ctx.vertex_array(
            self.timeline_bar_prog,
            [(vbo, '2f 3f', 'in_position', 'in_color')],
        )
        self.timeline_vertex_count = len(ERAS) * 6

        # Progress indicator (a small white quad that moves along the bar)
        # Will be updated each frame
        indicator_verts = np.zeros(6 * 5, dtype=np.float32)
        self.indicator_vbo = self.ctx.buffer(indicator_verts.tobytes(), dynamic=True)
        self.indicator_vao = self.ctx.vertex_array(
            self.timeline_bar_prog,
            [(self.indicator_vbo, '2f 3f', 'in_position', 'in_color')],
        )

    def _update_indicator(self, progress: float):
        """Update the progress indicator position on the timeline bar."""
        x = -0.9 + progress * 1.8
        hw = 0.005  # half-width of indicator
        y0, y1 = -0.94, -0.83
        verts = np.array([
            x - hw, y0, 1.0, 1.0, 1.0,
            x + hw, y0, 1.0, 1.0, 1.0,
            x - hw, y1, 1.0, 1.0, 1.0,
            x - hw, y1, 1.0, 1.0, 1.0,
            x + hw, y0, 1.0, 1.0, 1.0,
            x + hw, y1, 1.0, 1.0, 1.0,
        ], dtype=np.float32)
        self.indicator_vbo.write(verts.tobytes())

    def on_render(self, time: float, frame_time: float):
        """Main render loop with GPU particles and post-processing.

        Render order:
        1. Update simulation -> PhysicsState
        2. Update camera damping
        3. Update particle compute shader
        4. Begin post-processing scene (bind HDR FBO)
        5. Render particles into HDR FBO
        6. End post-processing scene (bloom + tonemap to screen)
        7. Render timeline bar overlay on top (after post-processing)

        PHYS-07: View matrix is computed via view_matrix_camera_relative()
        using double-precision camera position/target, NOT via the float32
        self.camera.view_matrix property.
        """
        # Update simulation
        state, alpha = self.sim.update(frame_time)

        # Update camera
        self.camera.update(frame_time)

        # Update particle system via compute shader
        self.particles.update(PHYSICS_DT, state)

        # Switch shader variant based on current era (RNDR-06)
        self.particles.set_era_shader(state.current_era)

        # Compute matrices -- PHYS-07: use double-precision camera-relative path
        proj = self.camera.projection_matrix
        view = view_matrix_camera_relative(
            self.camera.position_dvec3,
            self.camera.target_dvec3,
        )
        proj_bytes = bytes(proj)
        view_bytes = bytes(view)

        # --- Post-processing scene pass ---
        self.postfx.begin_scene()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.ONE, moderngl.ONE  # Additive blending
        self.ctx.depth_mask = False  # Don't write depth for particles (Pitfall 6)

        # Set era-specific uniforms on active particle program
        prog = self.particles.get_active_program()
        if 'u_temperature' in prog:
            prog['u_temperature'].value = state.temperature
        if 'u_density_normalized' in prog:
            # Normalize density to 0-1 range (log scale)
            density_norm = min(1.0, max(0.0, math.log10(max(state.matter_density, 1e-30)) / 30.0 + 1.0))
            prog['u_density_normalized'].value = density_norm

        # Render particles
        self.particles.render(proj_bytes, view_bytes)

        # Restore state
        self.ctx.depth_mask = True
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # --- Post-processing bloom + tonemap -> screen ---
        self.postfx.end_scene()

        # --- Timeline bar overlay (rendered AFTER post-processing, directly to screen) ---
        self.ctx.disable(moderngl.DEPTH_TEST)
        total_screen = self.sim.timeline.total_duration()
        progress = self.sim.screen_time / total_screen if total_screen > 0 else 0.0
        self.timeline_bar_prog['u_progress'].value = progress
        self.timeline_bar_prog['u_era_progress'].value = state.era_progress
        self.timeline_vao.render(moderngl.TRIANGLES, vertices=self.timeline_vertex_count)
        self._update_indicator(progress)
        self.indicator_vao.render(moderngl.TRIANGLES, vertices=6)

        # Re-enable depth test for next frame
        self.ctx.enable(moderngl.DEPTH_TEST)

        # Window title with FPS and particle count
        era_name = ERAS[state.current_era].name if 0 <= state.current_era < len(ERAS) else "?"
        speed_str = f"{self.sim.speed_multiplier:.1f}x"
        pause_str = " [PAUSED]" if self.sim.paused else ""
        fps = 1.0 / frame_time if frame_time > 0 else 0.0
        self.wnd.title = (
            f"BigBangSim - {era_name} | T={state.temperature:.1f}K | "
            f"{self.particles.count // 1000}K particles | "
            f"{fps:.0f} FPS | {speed_str}{pause_str}"
        )

    # --- Input Handling ---

    def on_key_event(self, key, action, modifiers):
        """Handle keyboard input for simulation controls."""
        keys = self.wnd.keys
        if action == keys.ACTION_PRESS:
            if key == keys.SPACE:
                self.sim.toggle_pause()
            elif key == keys.EQUAL:
                self.sim.increase_speed()
            elif key == keys.MINUS:
                self.sim.decrease_speed()
            elif key == keys.ESCAPE:
                self.wnd.close()

    def on_mouse_drag_event(self, x: int, y: int, dx: int, dy: int):
        """Left-click drag: orbit camera."""
        self.camera.on_mouse_drag(dx, dy)

    def on_mouse_scroll_event(self, x_offset: float, y_offset: float):
        """Scroll: zoom camera."""
        self.camera.on_scroll(y_offset)

    def on_resize(self, width: int, height: int):
        """Handle window resize: update camera and post-processing FBOs."""
        self.camera.aspect = width / height if height > 0 else 16 / 9
        self.postfx.resize(width, height)
