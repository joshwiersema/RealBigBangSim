"""GPU-resident particle system with ping-pong double-buffered SSBOs.

The ParticleSystem manages 100K-1M particles entirely on the GPU. A compute
shader reads from one SSBO and writes updated particle data to the other.
After dispatch, the buffers swap roles. The vertex shader reads particle data
from the current read buffer via gl_VertexID (no VAO vertex attributes needed).

Pipeline:
  1. update() -- dispatches compute shader (reads SSBO[current], writes SSBO[1-current])
  2. render() -- draws particles using SSBO[current] as data source

Particle struct layout (matches common.glsl):
  vec4 position  -- xyz=position, w=life (0.0-1.0)
  vec4 velocity  -- xyz=velocity, w=type (float-encoded int)
  vec4 color     -- rgba
  Total: 3 * vec4 * 4 bytes = 48 bytes per particle

Phase 3: Expanded to support 11 per-era fragment shaders (era_00_planck through
era_10_lss) with per-era uniform uploads and shader-key-based rendering.
"""
from __future__ import annotations

import moderngl
import numpy as np

from bigbangsim.rendering.shader_loader import load_shader_source

# 3 vec4 * 4 bytes = 48 bytes per particle (matches common.glsl Particle struct)
PARTICLE_STRIDE = 48

# Default particle count: 200K for a balance of visual density and performance
DEFAULT_PARTICLE_COUNT = 200_000

# 11 per-era fragment shaders matching EraVisualConfig.shader_key
_ERA_SHADER_NAMES = [
    ("era_00_planck", "fragment/era_00_planck.frag"),
    ("era_01_gut", "fragment/era_01_gut.frag"),
    ("era_02_inflation", "fragment/era_02_inflation.frag"),
    ("era_03_qgp", "fragment/era_03_qgp.frag"),
    ("era_04_hadron", "fragment/era_04_hadron.frag"),
    ("era_05_nucleosynthesis", "fragment/era_05_nucleosynthesis.frag"),
    ("era_06_recombination", "fragment/era_06_recombination.frag"),
    ("era_07_dark_ages", "fragment/era_07_dark_ages.frag"),
    ("era_08_first_stars", "fragment/era_08_first_stars.frag"),
    ("era_09_galaxy_formation", "fragment/era_09_galaxy_formation.frag"),
    ("era_10_lss", "fragment/era_10_lss.frag"),
]


class ParticleSystem:
    """GPU-resident particle system with ping-pong double-buffered SSBOs.

    Particles live entirely on the GPU. The compute shader reads from one
    SSBO and writes to the other. After dispatch, the buffers swap roles.
    The vertex shader reads particle data from the current read buffer
    via gl_VertexID (no VAO vertex attributes needed for particle data).

    Phase 3: Supports 11 per-era fragment shader programs with per-era
    uniform uploads. Each era's visual config drives shader selection
    and uniform values.
    """

    def __init__(self, ctx: moderngl.Context, count: int = DEFAULT_PARTICLE_COUNT):
        self.ctx = ctx
        self.count = count
        self.current = 0  # Index of the "read" buffer (just updated)

        # Initialize particle data on CPU, upload once
        init_data = self._generate_initial_particles(count)

        # Two SSBOs for ping-pong double buffering
        self.buffers = [
            ctx.buffer(init_data.tobytes()),
            ctx.buffer(init_data.tobytes()),
        ]

        # Compile compute shader (includes are preprocessed by shader_loader)
        compute_src = load_shader_source("compute/particle_update.comp")
        self.compute = ctx.compute_shader(compute_src)

        # Compile vertex shader (shared by all era fragment shaders)
        vert_src = load_shader_source("vertex/particle.vert")

        # Compile all 11 per-era fragment shaders
        self.programs: dict[str, moderngl.Program] = {}
        for shader_key, frag_path in _ERA_SHADER_NAMES:
            frag_src = load_shader_source(frag_path)
            self.programs[shader_key] = ctx.program(
                vertex_shader=vert_src, fragment_shader=frag_src
            )

        # Backward compatibility aliases (Phase 2 used hot/cool)
        self.programs["hot"] = self.programs["era_03_qgp"]
        self.programs["cool"] = self.programs["era_07_dark_ages"]

        self.active_program_key = "era_00_planck"

        # Empty VAO for gl_VertexID-based rendering (no vertex attributes)
        try:
            self.vao = ctx.vertex_array(self.get_active_program(), [])
        except Exception:
            dummy = ctx.buffer(b"\x00")
            self.vao = ctx.vertex_array(self.get_active_program(), [(dummy, "1x")])

    @staticmethod
    def _generate_initial_particles(count: int) -> np.ndarray:
        """Generate initial particle data as a flat float32 array.

        Each particle: 12 floats (3 vec4s):
          [px, py, pz, life, vx, vy, vz, type, r, g, b, a]

        Returns:
            np.ndarray shape (count, 12), dtype float32
        """
        rng = np.random.default_rng(42)

        # Positions: Gaussian cloud centered at origin, sigma=2.0
        positions = rng.normal(0, 2.0, (count, 3)).astype(np.float32)
        life = np.ones((count, 1), dtype=np.float32)  # w = life = 1.0

        # Velocities: small random initial motion
        velocities = rng.normal(0, 0.1, (count, 3)).astype(np.float32)
        ptype = np.zeros((count, 1), dtype=np.float32)  # w = type = 0

        # Colors: warm gradient (white-hot to orange)
        r = rng.uniform(0.8, 1.0, (count, 1)).astype(np.float32)
        g = rng.uniform(0.4, 0.8, (count, 1)).astype(np.float32)
        b = rng.uniform(0.1, 0.4, (count, 1)).astype(np.float32)
        a = np.ones((count, 1), dtype=np.float32)

        # Pack: [pos.xyz, life, vel.xyz, type, rgba]
        data = np.hstack([positions, life, velocities, ptype, r, g, b, a])
        return data  # shape (count, 12), dtype float32

    def update(self, dt: float, physics_state) -> None:
        """Dispatch compute shader to update all particles.

        Args:
            dt: Simulation timestep in seconds.
            physics_state: PhysicsState with temperature, scale_factor, current_era, etc.
        """
        read_buf = self.buffers[self.current]
        write_buf = self.buffers[1 - self.current]

        read_buf.bind_to_storage_buffer(0)   # binding=0 readonly
        write_buf.bind_to_storage_buffer(1)  # binding=1 writeonly

        # Upload physics uniforms to compute shader (with guards for GLSL optimization)
        if 'u_dt' in self.compute:
            self.compute["u_dt"].value = dt
        if 'u_temperature' in self.compute:
            self.compute["u_temperature"].value = physics_state.temperature
        if 'u_scale_factor' in self.compute:
            self.compute["u_scale_factor"].value = physics_state.scale_factor
        if 'u_particle_count' in self.compute:
            self.compute["u_particle_count"].value = self.count
        if 'u_era' in self.compute:
            self.compute["u_era"].value = physics_state.current_era

        # Dispatch: ceiling division for workgroup count (local_size_x = 256)
        num_groups = (self.count + 255) // 256
        self.compute.run(group_x=num_groups)

        # Memory barrier: compute writes must be visible to vertex shader reads
        self.ctx.memory_barrier()

        # Swap buffers: the write buffer becomes the new read buffer
        self.current = 1 - self.current

    def get_render_buffer(self) -> moderngl.Buffer:
        """Return the SSBO containing the latest particle data (read buffer)."""
        return self.buffers[self.current]

    def get_active_program(self) -> moderngl.Program:
        """Return the currently active rendering program."""
        return self.programs[self.active_program_key]

    def set_era_shader(self, era_index: int) -> None:
        """Switch fragment shader variant based on era index.

        Looks up the shader_key from ERA_VISUAL_CONFIGS and sets
        the active program accordingly.

        Args:
            era_index: Era index (0-10).
        """
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS

        if 0 <= era_index < len(ERA_VISUAL_CONFIGS):
            self.active_program_key = ERA_VISUAL_CONFIGS[era_index].shader_key
        else:
            # Fallback to first era
            self.active_program_key = "era_00_planck"

    def upload_era_uniforms(self, config, physics_uniforms: dict | None = None) -> None:
        """Upload per-era visual config uniforms to the active shader programs.

        Uses 'if name in prog' guards on all uniform accesses to prevent
        KeyError from GLSL compiler optimization removing unused uniforms.

        Args:
            config: EraVisualConfig with base_color, accent_color, brightness, etc.
            physics_uniforms: Optional dict of physics-specific uniform name -> value
                             (e.g., u_helium_fraction, u_ionization_fraction).
        """
        prog = self.get_active_program()

        # Fragment shader uniforms
        if 'u_base_color' in prog:
            prog['u_base_color'].value = config.base_color
        if 'u_accent_color' in prog:
            prog['u_accent_color'].value = config.accent_color
        if 'u_brightness' in prog:
            prog['u_brightness'].value = config.brightness

        # Vertex shader uniforms
        if 'u_point_scale_era' in prog:
            prog['u_point_scale_era'].value = config.particle_size

        # Compute shader uniforms (per-era behavior)
        if 'u_expansion_rate' in self.compute:
            self.compute['u_expansion_rate'].value = config.expansion_rate
        if 'u_noise_strength' in self.compute:
            self.compute['u_noise_strength'].value = config.noise_strength
        if 'u_gravity_strength' in self.compute:
            self.compute['u_gravity_strength'].value = config.gravity_strength
        if 'u_damping' in self.compute:
            self.compute['u_damping'].value = config.damping

        # Physics-specific uniforms (era-dependent)
        if physics_uniforms:
            for name, value in physics_uniforms.items():
                if name in prog:
                    prog[name].value = value

    def render(self, projection: bytes, view: bytes) -> None:
        """Render all particles using the active shader program.

        Args:
            projection: Projection matrix as bytes (from bytes(glm.mat4)).
            view: View matrix as bytes (from bytes(glm.mat4)).
        """
        prog = self.get_active_program()

        # Bind latest particle data to SSBO binding 0
        self.get_render_buffer().bind_to_storage_buffer(0)

        # Upload matrices
        prog["u_projection"].write(projection)
        prog["u_view"].write(view)
        if "u_point_scale" in prog:
            prog["u_point_scale"].value = 50.0

        # Render as points using gl_VertexID
        self.vao = self.ctx.vertex_array(prog, [])
        self.vao.render(moderngl.POINTS, vertices=self.count)

    def render_with_shader_key(
        self,
        shader_key: str,
        projection: bytes,
        view: bytes,
    ) -> None:
        """Render all particles using a specific shader program by key.

        Used during transitions to render the outgoing era with its
        previous shader program while the active program has already
        switched to the incoming era.

        Args:
            shader_key: Key into self.programs (e.g., "era_03_qgp").
            projection: Projection matrix as bytes.
            view: View matrix as bytes.
        """
        prog = self.programs.get(shader_key)
        if prog is None:
            # Fallback to active program
            prog = self.get_active_program()

        # Bind latest particle data to SSBO binding 0
        self.get_render_buffer().bind_to_storage_buffer(0)

        # Upload matrices
        prog["u_projection"].write(projection)
        prog["u_view"].write(view)
        if "u_point_scale" in prog:
            prog["u_point_scale"].value = 50.0

        # Render as points
        vao = self.ctx.vertex_array(prog, [])
        vao.render(moderngl.POINTS, vertices=self.count)

    def release(self) -> None:
        """Release GPU resources."""
        for buf in self.buffers:
            buf.release()
        # Track unique programs to avoid double-release (aliases share objects)
        released = set()
        for prog in self.programs.values():
            prog_id = id(prog)
            if prog_id not in released:
                prog.release()
                released.add(prog_id)
        self.compute.release()
