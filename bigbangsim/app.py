"""Main application window for BigBangSim.

Subclasses moderngl_window.WindowConfig to create an OpenGL 4.3 window
with GPU particle rendering, post-processing bloom pipeline, orbit camera,
simulation controls, imgui HUD overlay, milestone system, and cinematic
auto-camera.

Phase 4: Integrated imgui-bundle HUD overlay (HUD-01..HUD-05), milestone
notification system (PHYS-04), and cinematic camera controller (CAMR-02/03).
The GLSL timeline bar has been replaced by an imgui-drawn version. All 7
moderngl-window input events are forwarded to imgui for correct widget
interaction. HUD renders AFTER post-processing to avoid bloom bleeding
into text.

PHYS-07: The render loop uses view_matrix_camera_relative() with double-precision
camera coordinates instead of the float32 camera.view_matrix property.
"""
import moderngl
import moderngl_window
from pathlib import Path

import glm
import numpy as np

from imgui_bundle import imgui

# ---------------------------------------------------------------------------
# imgui-bundle 1.92+ broke the API that moderngl-window 3.1.1 expects:
#   - ImFontAtlas.get_tex_data_as_rgba32() removed
#   - ImFontAtlas.tex_id removed (now per-texture in tex_list)
# Subclass the renderer to fix both methods using the new API.
# ---------------------------------------------------------------------------
import ctypes
from moderngl_window.integrations.imgui_bundle import ModernglWindowRenderer as _Base

_NEEDS_COMPAT = not hasattr(imgui.ImFontAtlas, "get_tex_data_as_rgba32")


class _CompatRenderer(_Base):
    """Compatibility wrapper for imgui-bundle 1.92+ with moderngl-window 3.1.1.

    imgui-bundle 1.92+ changed several APIs that moderngl-window 3.1.1 uses:
      - ImFontAtlas.get_tex_data_as_rgba32() removed (now tex_list API)
      - ImFontAtlas.tex_id removed (now per-texture set_tex_id/get_tex_id)
      - ImDrawCmd.texture_id removed (now get_tex_id())
      - Backends must set renderer_has_textures flag
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.io.backend_flags |= imgui.BackendFlags_.renderer_has_textures

    def refresh_font_texture(self):
        fonts = self.io.fonts
        if len(fonts.tex_list) == 0:
            if len(fonts.fonts) == 0:
                fonts.add_font_default()
        tex = fonts.tex_list[0]
        pixels = tex.get_pixels_array()
        width, height = tex.width, tex.height

        if self._font_texture:
            self.remove_texture(self._font_texture)
            self._font_texture.release()

        self._font_texture = self.ctx.texture(
            (width, height), 4, data=pixels,
        )
        self.register_texture(self._font_texture)
        tex.set_tex_id(self._font_texture.glo)
        tex.set_status(imgui.ImTextureStatus.ok)

    def render(self, draw_data: imgui.ImDrawData):
        io = self.io
        display_width, display_height = io.display_size
        fb_width = int(display_width * io.display_framebuffer_scale[0])
        fb_height = int(display_height * io.display_framebuffer_scale[1])

        if fb_width == 0 or fb_height == 0:
            return

        self.projMat.value = (
            2.0 / display_width, 0.0, 0.0, 0.0,
            0.0, 2.0 / -display_height, 0.0, 0.0,
            0.0, 0.0, -1.0, 0.0,
            -1.0, 1.0, 0.0, 1.0,
        )

        draw_data.scale_clip_rects(imgui.ImVec2(*io.display_framebuffer_scale))

        self.ctx.enable_only(moderngl.BLEND)
        self.ctx.blend_equation = moderngl.FUNC_ADD
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        self._font_texture.use()

        for commands in draw_data.cmd_lists:
            vtx_type = ctypes.c_byte * commands.vtx_buffer.size() * imgui.VERTEX_SIZE
            idx_type = ctypes.c_byte * commands.idx_buffer.size() * imgui.INDEX_SIZE
            vtx_arr = (vtx_type).from_address(commands.vtx_buffer.data_address())
            idx_arr = (idx_type).from_address(commands.idx_buffer.data_address())
            self._vertex_buffer.write(vtx_arr)
            self._index_buffer.write(idx_arr)

            idx_pos = 0
            for command in commands.cmd_buffer:
                # imgui-bundle 1.92+: texture_id -> get_tex_id()
                tex_id = command.get_tex_id()
                texture = self._textures.get(tex_id)
                if texture is None:
                    raise ValueError(
                        f"Texture {tex_id} is not registered. "
                        f"Current textures: {list(self._textures)}"
                    )

                texture.use(0)

                x, y, z, w = command.clip_rect
                self.ctx.scissor = int(x), int(fb_height - w), int(z - x), int(w - y)
                self._vao.render(
                    moderngl.TRIANGLES, vertices=command.elem_count, first=idx_pos,
                )
                idx_pos += command.elem_count

        self.ctx.scissor = None

    def _invalidate_device_objects(self):
        if self._font_texture:
            self._font_texture.release()
        if self._vertex_buffer:
            self._vertex_buffer.release()
        if self._index_buffer:
            self._index_buffer.release()
        if self._vao:
            self._vao.release()
        if self._prog:
            self._prog.release()

        fonts = self.io.fonts
        if len(fonts.tex_list) > 0:
            fonts.tex_list[0].set_tex_id(0)
        self._font_texture = None


ModernglWindowRenderer = _CompatRenderer if _NEEDS_COMPAT else _Base

from bigbangsim.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    PHYSICS_DT,
    save_window_state,
    load_window_state,
)
from bigbangsim.capture.screenshot import take_screenshot
from bigbangsim.capture.recorder import VideoRecorder
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

from bigbangsim.presentation.hud import HUDManager
from bigbangsim.presentation.milestones import MilestoneManager
from bigbangsim.presentation.camera_controller import CinematicCameraController
from bigbangsim.presentation.educational_content import MILESTONES


class BigBangSimApp(moderngl_window.WindowConfig):
    """Phase 4 application: per-era visuals, physics uniforms, transitions,
    imgui HUD, milestones, and cinematic auto-camera."""

    title = "BigBangSim - Cosmic Evolution"
    window_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
    gl_version = (4, 3)
    resource_dir = Path(__file__).parent / "shaders"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Enable gl_PointSize in vertex shaders (required by AMD drivers,
        # NVIDIA often enables this by default but the spec requires it)
        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)

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

        # --- Phase 4: imgui + presentation layer ---
        imgui.create_context()
        self.imgui_renderer = ModernglWindowRenderer(self.wnd)

        self.hud = HUDManager()
        self.milestones = MilestoneManager(MILESTONES)
        self.camera_controller = CinematicCameraController(self.camera)

        # --- Phase 5: Capture & Polish ---
        self._screenshot_requested = False

        # Video recorder (CAPT-02, CAPT-03) -- None until recording starts
        self.recorder: VideoRecorder | None = None
        self._ffmpeg_available = VideoRecorder.is_available()

        # Restore saved window state (RNDR-05)
        saved_state = load_window_state()
        if saved_state:
            if saved_state.get("fullscreen"):
                self.wnd.fullscreen = True
            elif "position" in saved_state and "size" in saved_state:
                try:
                    self.wnd.position = tuple(saved_state["position"])
                    self.wnd.size = tuple(saved_state["size"])
                except Exception:
                    pass  # Ignore if backend doesn't support position/size set

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
        """Main render loop with per-era visuals, physics, transitions, and HUD.

        Render order:
        1. Update simulation -> PhysicsState
        2. Update milestones
        3. Update camera damping
        4. Update cinematic camera controller
        5. Look up current era's visual config
        6. Upload per-era compute uniforms and update particles
        7. Switch to current era's shader
        8. Check for era transition
        9. Render (with or without crossfade transition)
        10. Render imgui HUD overlay (AFTER post-processing)

        PHYS-07: View matrix is computed via view_matrix_camera_relative()
        using double-precision camera position/target.
        """
        # 1. Update simulation (frame-locked during recording -- CAPT-03)
        effective_frame_time = frame_time
        if self.recorder and self.recorder.recording:
            override = self.recorder.frame_time_override
            if override is not None:
                effective_frame_time = override
        state, alpha = self.sim.update(effective_frame_time)

        # 2. Update milestones
        self.milestones.update(state.cosmic_time, effective_frame_time)

        # 3. Update camera damping
        self.camera.update(effective_frame_time)

        # 4. Update cinematic camera controller
        self.camera_controller.update(effective_frame_time, state.current_era, state.era_progress)

        # 5. Look up current era's visual config
        config = get_era_visual_config(state.current_era)

        # 6. Update bloom parameters per era
        self.postfx.bloom_strength = config.bloom_strength
        self.postfx.bloom_threshold = config.bloom_threshold

        # 7. Upload per-era compute uniforms BEFORE dispatch
        self._upload_compute_uniforms(config)

        # 8. Update particle system via compute shader
        self.particles.update(PHYSICS_DT, state)

        # 9. Switch to current era's shader
        self.particles.set_era_shader(state.current_era)

        # 10. Check for era transition
        self.transition.check_transition(
            state.current_era, frame_time, config.transition_seconds
        )

        # 11. Compute matrices -- PHYS-07: use double-precision camera-relative path
        proj = self.camera.projection_matrix
        view = view_matrix_camera_relative(
            self.camera.position_dvec3,
            self.camera.target_dvec3,
        )
        # bytes(glm.mat4) gives ROW-MAJOR data, but OpenGL expects COLUMN-MAJOR.
        # Use numpy Fortran-order (column-major) serialization instead.
        proj_bytes = np.array(proj, dtype='f4').tobytes(order='F')
        view_bytes = np.array(view, dtype='f4').tobytes(order='F')

        # 12. Compute physics uniforms for the current era
        physics_uniforms = self._compute_physics_uniforms(state)

        # 13. Render scene (with or without transition crossfade)
        if self.transition.in_transition:
            self._render_with_transition(
                state, config, physics_uniforms, proj_bytes, view_bytes
            )
        else:
            self._render_normal(
                state, config, physics_uniforms, proj_bytes, view_bytes
            )

        # 14. HUD overlay (rendered AFTER post-processing, directly to default framebuffer)
        self._render_hud(state)

        # Window title with FPS, particle count, camera mode, and recording status
        era_name = ERAS[state.current_era].name if 0 <= state.current_era < len(ERAS) else "?"
        speed_str = f"{self.sim.speed_multiplier:.1f}x"
        pause_str = " [PAUSED]" if self.sim.paused else ""
        fps = 1.0 / frame_time if frame_time > 0 else 0.0
        cam_str = "Auto" if self.camera_controller.is_auto else "Free"
        rec_str = " | REC" if (self.recorder and self.recorder.recording) else ""
        self.wnd.title = (
            f"BigBangSim - {era_name} | T={state.temperature:.1f}K | "
            f"{self.particles.count // 1000}K particles | "
            f"{fps:.0f} FPS | {speed_str}{pause_str} | Cam: {cam_str}{rec_str}"
        )

        # Phase 5: Screenshot capture (after HUD rendering, before swap)
        if self._screenshot_requested:
            self._screenshot_requested = False
            path = take_screenshot(self.ctx.fbo, self.wnd.size[0], self.wnd.size[1])
            print(f"Screenshot saved: {path}")

        # Phase 5: Video frame capture (after HUD, frame-locked -- CAPT-02)
        if self.recorder and self.recorder.recording:
            self.recorder.write_frame(self.ctx.fbo)

    def _render_hud(self, state):
        """Render imgui HUD overlay after post-processing."""
        imgui.new_frame()
        recording = self.recorder is not None and self.recorder.recording
        self.hud.render(
            state, self.sim, self.milestones,
            self.camera_controller.is_auto, ERAS,
            recording=recording,
        )
        imgui.render()
        self.imgui_renderer.render(imgui.get_draw_data())

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
        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)  # Re-enable (imgui's enable_only wipes it)
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
        # === DIAGNOSTIC: render test triangle + particles direct to screen ===
        self.ctx.fbo.use()
        self.ctx.fbo.clear(0.02, 0.0, 0.05, 1.0)  # Very dark purple

        # --- Test A: Simple colored triangle (no SSBO, no points) ---
        if not hasattr(self, '_diag_prog'):
            self._diag_prog = self.ctx.program(
                vertex_shader="""
                #version 430
                const vec2 verts[3] = vec2[](
                    vec2(-0.5, -0.5), vec2(0.5, -0.5), vec2(0.0, 0.5)
                );
                const vec3 colors[3] = vec3[](
                    vec3(1, 0, 0), vec3(0, 1, 0), vec3(0, 0, 1)
                );
                out vec3 v_color;
                void main() {
                    gl_Position = vec4(verts[gl_VertexID], 0.0, 1.0);
                    v_color = colors[gl_VertexID];
                }
                """,
                fragment_shader="""
                #version 430
                in vec3 v_color;
                out vec4 fragColor;
                void main() { fragColor = vec4(v_color, 1.0); }
                """,
            )
            self._diag_vao = self.ctx.vertex_array(self._diag_prog, [])

        self.ctx.disable(moderngl.DEPTH_TEST)
        self._diag_vao.render(moderngl.TRIANGLES, vertices=3)

        # --- Test B: Particles with big white points (simple shader) ---
        if not hasattr(self, '_diag_pt_prog'):
            self._diag_pt_prog = self.ctx.program(
                vertex_shader="""
                #version 430
                struct P { vec4 pos; vec4 vel; vec4 col; };
                layout(std430, binding = 0) readonly buffer Particles { P particles[]; };
                uniform mat4 u_projection;
                uniform mat4 u_view;
                void main() {
                    vec3 p = particles[gl_VertexID].pos.xyz;
                    gl_Position = u_projection * u_view * vec4(p, 1.0);
                    gl_PointSize = clamp(200.0 / max(gl_Position.w, 0.1), 2.0, 64.0);
                }
                """,
                fragment_shader="""
                #version 430
                out vec4 fragColor;
                void main() { fragColor = vec4(1.0, 0.8, 0.3, 1.0); }
                """,
            )

        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.ONE, moderngl.ONE
        self.particles.get_render_buffer().bind_to_storage_buffer(0)
        self._diag_pt_prog["u_projection"].write(proj_bytes)
        self._diag_pt_prog["u_view"].write(view_bytes)
        diag_vao = self.ctx.vertex_array(self._diag_pt_prog, [])
        diag_vao.render(moderngl.POINTS, vertices=min(self.particles.count, 10000))

        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

    # --- Input Handling ---
    # All 7 event types forwarded to imgui first (Pitfall 2 from research).

    def on_key_event(self, key, action, modifiers):
        """Handle keyboard input for simulation and presentation controls."""
        self.imgui_renderer.key_event(key, action, modifiers)
        io = imgui.get_io()
        if io.want_capture_keyboard:
            return
        keys = self.wnd.keys
        if action == keys.ACTION_PRESS:
            if key == keys.SPACE:
                self.sim.toggle_pause()
            elif key == keys.EQUAL:
                self.sim.increase_speed()
            elif key == keys.MINUS:
                self.sim.decrease_speed()
            elif key == keys.H:
                self.hud.toggle()
            elif key == keys.C:
                self.camera_controller.toggle_mode()
            elif key == keys.F12:
                self._screenshot_requested = True
            elif key == keys.F11:
                self.wnd.fullscreen = not self.wnd.fullscreen
            elif key == keys.F9:
                if self.recorder and self.recorder.recording:
                    self.recorder.stop()
                    print(f"Recording saved: {self.recorder.output_path}")
                    self.recorder = None
                elif self._ffmpeg_available:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    self.recorder = VideoRecorder(
                        self.wnd.size[0], self.wnd.size[1],
                        fps=60,
                        output_path=f"bigbangsim_{timestamp}.mp4",
                    )
                    self.recorder.start()
                    print("Recording started...")
                else:
                    print("FFmpeg not found. Install via: winget install FFmpeg")
            elif key == keys.ESCAPE:
                self.wnd.close()

    def on_mouse_drag_event(self, x: int, y: int, dx: int, dy: int):
        """Left-click drag: orbit camera (guarded by imgui capture)."""
        self.imgui_renderer.mouse_drag_event(x, y, dx, dy)
        io = imgui.get_io()
        if not io.want_capture_mouse:
            self.camera.on_mouse_drag(dx, dy)

    def on_mouse_scroll_event(self, x_offset: float, y_offset: float):
        """Scroll: zoom camera (guarded by imgui capture)."""
        self.imgui_renderer.mouse_scroll_event(x_offset, y_offset)
        io = imgui.get_io()
        if not io.want_capture_mouse:
            self.camera.on_scroll(y_offset)

    def on_mouse_position_event(self, x: int, y: int, dx: int, dy: int):
        """Forward mouse position to imgui for hover detection."""
        self.imgui_renderer.mouse_position_event(x, y, dx, dy)

    def on_mouse_press_event(self, x: int, y: int, button: int):
        """Forward mouse press to imgui for click detection."""
        self.imgui_renderer.mouse_press_event(x, y, button)

    def on_mouse_release_event(self, x: int, y: int, button: int):
        """Forward mouse release to imgui for click detection."""
        self.imgui_renderer.mouse_release_event(x, y, button)

    def on_unicode_char_entered(self, char: str):
        """Forward unicode character input to imgui for text fields."""
        self.imgui_renderer.unicode_char_entered(char)

    def on_resize(self, width: int, height: int):
        """Handle window resize: update camera, post-processing, transition, and imgui."""
        self.camera.aspect = width / height if height > 0 else 16 / 9
        self.postfx.resize(width, height)
        self.transition.resize(width, height)
        self.imgui_renderer.resize(width, height)

    def on_close(self):
        """Save window state and stop recording on application close."""
        if self.recorder and self.recorder.recording:
            self.recorder.stop()
        save_window_state(self.wnd)
