"""Main application window for BigBangSim.

Subclasses moderngl_window.WindowConfig to create an OpenGL 4.3 window
with GPU particle rendering, post-processing bloom pipeline, orbit camera,
simulation controls, and timeline bar.

Phase 3: Integrated per-era visual configs, physics sub-module uniforms,
and FBO crossfade transitions. Each of the 11 eras has unique shader
selection, bloom parameters, compute behavior, and optional physics-
specific uniforms (helium fraction, ionization, collapsed fraction).

PHYS-07: The render loop uses view_matrix_camera_relative() with double-precision
camera coordinates instead of the float32 camera.view_matrix property.
"""
import moderngl
import moderngl_window
from pathlib import Path

import glm
import numpy as np

from bigbangsim.config import WINDOW_WIDTH, WINDOW_HEIGHT, PHYSICS_DT
from bigbangsim.simulation.engine import SimulationEngine
from bigbangsim.simulation.eras import ERAS
from bigbangsim.simulation.era_visual_config import (
    get_era_visual_config,
    ERA_VISUAL_CONFIGS,
)
from bigbangsim.simulation.physics.nucleosynthesis import get_bbn_fractions
from bigbangsim.simulation.physics.recombination import (
    build_ionization_table,
    get_ionization_fraction,
)
from bigbangsim.simulation.physics.structure import (
    build_collapsed_fraction_table,
    get_collapsed_fraction,
)
from bigbangsim.rendering.camera import DampedOrbitCamera
from bigbangsim.rendering.coordinates import view_matrix_camera_relative
from bigbangsim.rendering.particles import ParticleSystem
from bigbangsim.rendering.postprocessing import PostProcessingPipeline
from bigbangsim.rendering.era_transition import EraTransitionManager


class BigBangSimApp(moderngl_window.WindowConfig):
    """Phase 3 application: per-era visuals + physics uniforms + transitions."""

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

        # GPU particle system (RNDR-01, expanded for 11 eras in Phase 3)
        self.particles = ParticleSystem(self.ctx, count=200_000)

        # Post-processing pipeline (RNDR-02)
        self.postfx = PostProcessingPipeline(
            self.ctx, self.wnd.size[0], self.wnd.size[1]
        )

        # Era transition manager (RNDR-04) -- FBO crossfade between eras
        self.transition = EraTransitionManager(
            self.ctx, self.wnd.size[0], self.wnd.size[1]
        )

        # Pre-compute physics lookup tables at startup (NOT per-frame)
        self.ionization_table = build_ionization_table(n_points=500)
        self.collapsed_fraction_table = build_collapsed_fraction_table(n_points=200)

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

    def _compute_physics_uniforms(self, state) -> dict[str, float]:
        """Compute era-specific physics uniforms from simulation state.

        Only computes values for eras that need them, keeping per-frame
        work minimal.

        Args:
            state: PhysicsState with current_era, temperature, cosmic_time, era_progress.

        Returns:
            Dictionary of uniform name -> value for the current era.
        """
        physics_uniforms: dict[str, float] = {}

        if state.current_era == 5:  # Nucleosynthesis
            bbn = get_bbn_fractions(state.temperature)
            physics_uniforms['u_helium_fraction'] = bbn['helium_fraction']
        elif state.current_era == 6:  # Recombination
            physics_uniforms['u_ionization_fraction'] = get_ionization_fraction(
                state.temperature, self.ionization_table
            )
        elif state.current_era == 8:  # First Stars
            # Reionization fraction: ramp from 0 to 1 over the era
            physics_uniforms['u_reionization_frac'] = state.era_progress
        elif state.current_era in (9, 10):  # Galaxy Formation, LSS
            physics_uniforms['u_collapsed_fraction'] = get_collapsed_fraction(
                state.cosmic_time, self.collapsed_fraction_table
            )

        return physics_uniforms

    def _upload_uniforms_to_program(self, prog, config, state, physics_uniforms):
        """Upload per-era visual and physics uniforms to a shader program.

        All uniform accesses use 'if name in prog' guards to prevent
        KeyError from GLSL optimization removing unused uniforms (Pitfall 1,
        commit c94d2c1).

        Args:
            prog: The moderngl.Program to upload to.
            config: EraVisualConfig with colors, brightness, etc.
            state: PhysicsState with temperature, era_progress.
            physics_uniforms: Dict of physics-specific uniform name -> value.
        """
        # Fragment shader visual uniforms
        if 'u_base_color' in prog:
            prog['u_base_color'].value = config.base_color
        if 'u_accent_color' in prog:
            prog['u_accent_color'].value = config.accent_color
        if 'u_brightness' in prog:
            prog['u_brightness'].value = config.brightness

        # Vertex shader uniforms
        if 'u_point_scale_era' in prog:
            prog['u_point_scale_era'].value = config.particle_size

        # State-derived uniforms
        if 'u_temperature' in prog:
            prog['u_temperature'].value = state.temperature
        if 'u_era_progress' in prog:
            prog['u_era_progress'].value = state.era_progress

        # Physics-specific uniforms (era-dependent)
        for name, value in physics_uniforms.items():
            if name in prog:
                prog[name].value = value

    def _upload_compute_uniforms(self, config):
        """Upload per-era compute shader uniforms.

        Controls how particles move differently in each era (expansion,
        turbulence, gravity, damping).

        Args:
            config: EraVisualConfig with expansion_rate, noise_strength, etc.
        """
        compute = self.particles.compute
        if 'u_expansion_rate' in compute:
            compute['u_expansion_rate'].value = config.expansion_rate
        if 'u_noise_strength' in compute:
            compute['u_noise_strength'].value = config.noise_strength
        if 'u_gravity_strength' in compute:
            compute['u_gravity_strength'].value = config.gravity_strength
        if 'u_damping' in compute:
            compute['u_damping'].value = config.damping

    def on_render(self, time: float, frame_time: float):
        """Main render loop with per-era visuals, physics uniforms, and transitions.

        Render order:
        1. Update simulation -> PhysicsState
        2. Update camera damping
        3. Look up current era's visual config
        4. Upload per-era compute uniforms and update particles
        5. Switch to current era's shader
        6. Check for era transition
        7. Render (with or without crossfade transition)
        8. Render timeline bar overlay (after post-processing)

        PHYS-07: View matrix is computed via view_matrix_camera_relative()
        using double-precision camera position/target.
        """
        # 1. Update simulation
        state, alpha = self.sim.update(frame_time)

        # 2. Update camera
        self.camera.update(frame_time)

        # 3. Look up current era's visual config
        config = get_era_visual_config(state.current_era)

        # 4. Update bloom parameters per era
        self.postfx.bloom_strength = config.bloom_strength
        self.postfx.bloom_threshold = config.bloom_threshold

        # 5. Upload per-era compute uniforms BEFORE dispatch
        self._upload_compute_uniforms(config)

        # 6. Update particle system via compute shader
        self.particles.update(PHYSICS_DT, state)

        # 7. Switch to current era's shader
        self.particles.set_era_shader(state.current_era)

        # 8. Check for era transition
        self.transition.check_transition(
            state.current_era, frame_time, config.transition_seconds
        )

        # 9. Compute matrices -- PHYS-07: use double-precision camera-relative path
        proj = self.camera.projection_matrix
        view = view_matrix_camera_relative(
            self.camera.position_dvec3,
            self.camera.target_dvec3,
        )
        proj_bytes = bytes(proj)
        view_bytes = bytes(view)

        # 10. Compute physics uniforms for the current era
        physics_uniforms = self._compute_physics_uniforms(state)

        # 11. Render scene (with or without transition crossfade)
        if self.transition.in_transition:
            self._render_with_transition(
                state, config, physics_uniforms, proj_bytes, view_bytes
            )
        else:
            self._render_normal(
                state, config, physics_uniforms, proj_bytes, view_bytes
            )

        # 12. Timeline bar overlay (rendered AFTER post-processing, directly to screen)
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

    def _render_with_transition(
        self, state, config, physics_uniforms, proj_bytes, view_bytes
    ):
        """Render scene with FBO crossfade transition between eras.

        Renders outgoing era to transition FBO, incoming era to HDR FBO,
        then composites them with the transition blend factor.

        Args:
            state: Current PhysicsState.
            config: Current (incoming) era's visual config.
            physics_uniforms: Physics-specific uniforms for current era.
            proj_bytes: Projection matrix as bytes.
            view_bytes: View matrix as bytes.
        """
        outgoing_config = get_era_visual_config(self.transition.outgoing_era)

        # --- Render OUTGOING era into transition FBO ---
        self.transition.begin_outgoing()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.ONE, moderngl.ONE
        self.ctx.depth_mask = False

        # Upload outgoing era uniforms to outgoing shader
        outgoing_prog = self.particles.programs.get(
            outgoing_config.shader_key,
            self.particles.get_active_program()
        )
        self._upload_uniforms_to_program(
            outgoing_prog, outgoing_config, state, {}
        )
        self.particles.render_with_shader_key(
            outgoing_config.shader_key, proj_bytes, view_bytes
        )

        # Restore state
        self.ctx.depth_mask = True
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # --- Render INCOMING era into HDR FBO ---
        self.postfx.begin_scene()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.ONE, moderngl.ONE
        self.ctx.depth_mask = False

        # Upload incoming (current) era uniforms
        incoming_prog = self.particles.get_active_program()
        self._upload_uniforms_to_program(
            incoming_prog, config, state, physics_uniforms
        )
        self.particles.render(proj_bytes, view_bytes)

        # Restore state
        self.ctx.depth_mask = True
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # --- Composite: blend outgoing + incoming into HDR FBO ---
        self.transition.composite(self.postfx.hdr_texture, self.postfx.hdr_fbo)

        # --- Post-processing: bloom + tonemap on composited result ---
        self.postfx.end_scene()

    def _render_normal(
        self, state, config, physics_uniforms, proj_bytes, view_bytes
    ):
        """Render scene normally (no transition active).

        Single-pass rendering: particles to HDR FBO, then post-processing.

        Args:
            state: Current PhysicsState.
            config: Current era's visual config.
            physics_uniforms: Physics-specific uniforms for current era.
            proj_bytes: Projection matrix as bytes.
            view_bytes: View matrix as bytes.
        """
        self.postfx.begin_scene()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.ONE, moderngl.ONE  # Additive blending
        self.ctx.depth_mask = False  # Don't write depth for particles (Pitfall 6)

        # Upload current era uniforms
        prog = self.particles.get_active_program()
        self._upload_uniforms_to_program(prog, config, state, physics_uniforms)

        # Render particles
        self.particles.render(proj_bytes, view_bytes)

        # Restore state
        self.ctx.depth_mask = True
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # Post-processing bloom + tonemap -> screen
        self.postfx.end_scene()

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
        """Handle window resize: update camera, post-processing, and transition FBOs."""
        self.camera.aspect = width / height if height > 0 else 16 / 9
        self.postfx.resize(width, height)
        self.transition.resize(width, height)
