"""Main application window for BigBangSim.

Subclasses moderngl_window.WindowConfig to create an OpenGL 4.3 window
with a test scene, orbit camera, simulation controls, and timeline bar.

PHYS-07: The render loop uses view_matrix_camera_relative() with double-precision
camera coordinates instead of the float32 camera.view_matrix property.
"""
import math
import struct

import glm
import numpy as np
import moderngl
import moderngl_window
from moderngl_window import geometry
from pathlib import Path

from bigbangsim.config import WINDOW_WIDTH, WINDOW_HEIGHT
from bigbangsim.simulation.engine import SimulationEngine
from bigbangsim.simulation.eras import ERAS
from bigbangsim.rendering.camera import DampedOrbitCamera
from bigbangsim.rendering.coordinates import view_matrix_camera_relative


class BigBangSimApp(moderngl_window.WindowConfig):
    """Phase 1 application shell: test scene + camera + controls + timeline bar."""

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

        # Load shaders
        self.test_scene_prog = self._load_shader("test_scene")
        self.timeline_bar_prog = self._load_shader("timeline_bar")

        # Create test scene geometry: grid + axis lines + placeholder particles
        self._create_test_scene()
        self._create_timeline_bar()

    def _load_shader(self, name: str) -> moderngl.Program:
        """Load vertex + fragment shader pair from resource_dir."""
        vert_path = self.resource_dir / f"{name}.vert"
        frag_path = self.resource_dir / f"{name}.frag"
        return self.ctx.program(
            vertex_shader=vert_path.read_text(),
            fragment_shader=frag_path.read_text(),
        )

    def _create_test_scene(self):
        """Create a colored grid, axis lines, and placeholder particles."""
        vertices = []
        colors = []

        # Grid lines (XZ plane, -5 to +5)
        for i in range(-5, 6):
            # X-parallel lines
            vertices.extend([i, 0, -5, i, 0, 5])
            c = [0.3, 0.3, 0.3] if i != 0 else [0.5, 0.5, 0.5]
            colors.extend(c + c)
            # Z-parallel lines
            vertices.extend([-5, 0, i, 5, 0, i])
            colors.extend(c + c)

        # Axis lines (colored)
        # X axis: red
        vertices.extend([0, 0, 0, 5, 0, 0])
        colors.extend([1, 0, 0, 1, 0, 0])
        # Y axis: green
        vertices.extend([0, 0, 0, 0, 5, 0])
        colors.extend([0, 1, 0, 0, 1, 0])
        # Z axis: blue
        vertices.extend([0, 0, 0, 0, 0, 5])
        colors.extend([0, 0, 1, 0, 0, 1])

        # Placeholder particles (small random cloud)
        rng = np.random.default_rng(42)
        n_particles = 500
        particle_pos = rng.normal(0, 1.5, (n_particles, 3)).astype(np.float32)
        particle_col = np.column_stack([
            np.linspace(1.0, 0.2, n_particles),   # R: hot to cool
            np.linspace(0.5, 0.5, n_particles),   # G: mid
            np.linspace(0.2, 1.0, n_particles),   # B: cool to hot
        ]).astype(np.float32)

        vert_arr = np.array(vertices, dtype=np.float32)
        col_arr = np.array(colors, dtype=np.float32)

        # Grid + axis VAO (lines)
        grid_vbo = self.ctx.buffer(vert_arr.tobytes())
        grid_cbo = self.ctx.buffer(col_arr.tobytes())
        self.grid_vao = self.ctx.vertex_array(
            self.test_scene_prog,
            [(grid_vbo, '3f', 'in_position'), (grid_cbo, '3f', 'in_color')],
        )
        self.grid_vertex_count = len(vertices) // 3

        # Particle VAO (points)
        part_vbo = self.ctx.buffer(particle_pos.tobytes())
        part_cbo = self.ctx.buffer(particle_col.tobytes())
        self.particle_vao = self.ctx.vertex_array(
            self.test_scene_prog,
            [(part_vbo, '3f', 'in_position'), (part_cbo, '3f', 'in_color')],
        )
        self.particle_count = n_particles

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
        """Main render loop -- called every frame by moderngl-window.

        PHYS-07: View matrix is computed via view_matrix_camera_relative()
        using double-precision camera position/target, NOT via the float32
        self.camera.view_matrix property. This is the architectural pattern
        that prevents floating-point precision breakdown at large coordinates.
        """
        self.ctx.clear(0.05, 0.05, 0.08, 1.0)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # Update simulation
        state, alpha = self.sim.update(frame_time)

        # Update camera
        self.camera.update(frame_time)

        # Compute matrices -- PHYS-07: use double-precision camera-relative path
        proj = self.camera.projection_matrix
        view = view_matrix_camera_relative(
            self.camera.position_dvec3,
            self.camera.target_dvec3,
        )
        model = glm.mat4(1.0)

        # Upload uniforms to test scene shader
        self.test_scene_prog['u_projection'].write(bytes(proj))
        self.test_scene_prog['u_view'].write(bytes(view))
        self.test_scene_prog['u_model'].write(bytes(model))

        # Render grid (lines)
        self.grid_vao.render(moderngl.LINES, vertices=self.grid_vertex_count)

        # Render placeholder particles (points)
        self.ctx.point_size = 3.0
        self.particle_vao.render(moderngl.POINTS, vertices=self.particle_count)

        # Render timeline bar (disable depth test for overlay)
        self.ctx.disable(moderngl.DEPTH_TEST)
        total_screen = self.sim.timeline.total_duration()
        progress = self.sim.screen_time / total_screen if total_screen > 0 else 0.0
        self.timeline_bar_prog['u_progress'].value = progress
        self.timeline_bar_prog['u_era_progress'].value = state.era_progress
        self.timeline_vao.render(moderngl.TRIANGLES, vertices=self.timeline_vertex_count)
        self._update_indicator(progress)
        self.indicator_vao.render(moderngl.TRIANGLES, vertices=6)

        # Re-enable depth test
        self.ctx.enable(moderngl.DEPTH_TEST)

        # Set window title with state info
        era_name = ERAS[state.current_era].name if 0 <= state.current_era < len(ERAS) else "?"
        speed_str = f"{self.sim.speed_multiplier:.1f}x"
        pause_str = " [PAUSED]" if self.sim.paused else ""
        self.wnd.title = f"BigBangSim - {era_name} | T={state.temperature:.1f}K | {speed_str}{pause_str}"

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
        """Handle window resize: update camera aspect ratio."""
        self.camera.aspect = width / height if height > 0 else 16 / 9
