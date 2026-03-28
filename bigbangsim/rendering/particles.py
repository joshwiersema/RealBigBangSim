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
"""
from __future__ import annotations

import moderngl
import numpy as np

from bigbangsim.rendering.shader_loader import load_shader_source

# 3 vec4 * 4 bytes = 48 bytes per particle (matches common.glsl Particle struct)
PARTICLE_STRIDE = 48

# Default particle count: 200K for a balance of visual density and performance
DEFAULT_PARTICLE_COUNT = 200_000


class ParticleSystem:
    """GPU-resident particle system with ping-pong double-buffered SSBOs.

    Particles live entirely on the GPU. The compute shader reads from one
    SSBO and writes to the other. After dispatch, the buffers swap roles.
    The vertex shader reads particle data from the current read buffer
    via gl_VertexID (no VAO vertex attributes needed for particle data).
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

        # Compile particle rendering shaders (hot for early eras, cool for late)
        vert_src = load_shader_source("vertex/particle.vert")
        hot_frag_src = load_shader_source("fragment/particle_hot.frag")
        cool_frag_src = load_shader_source("fragment/particle_cool.frag")

        self.programs = {
            "hot": ctx.program(vertex_shader=vert_src, fragment_shader=hot_frag_src),
            "cool": ctx.program(vertex_shader=vert_src, fragment_shader=cool_frag_src),
        }
        self.active_program_key = "hot"

        # Empty VAO for gl_VertexID-based rendering (no vertex attributes)
        try:
            self.vao = ctx.vertex_array(self.programs["hot"], [])
        except Exception:
            dummy = ctx.buffer(b"\x00")
            self.vao = ctx.vertex_array(self.programs["hot"], [(dummy, "1x")])

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

        # Upload physics uniforms to compute shader
        self.compute["u_dt"].value = dt
        self.compute["u_temperature"].value = physics_state.temperature
        self.compute["u_scale_factor"].value = physics_state.scale_factor
        self.compute["u_particle_count"].value = self.count
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
        """Switch fragment shader variant based on era.

        Eras 0-5 (Planck through Nucleosynthesis): 'hot' shader
        Eras 6-10 (CMB through LSS): 'cool' shader
        """
        self.active_program_key = "hot" if era_index <= 5 else "cool"

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

    def release(self) -> None:
        """Release GPU resources."""
        for buf in self.buffers:
            buf.release()
        for prog in self.programs.values():
            prog.release()
        self.compute.release()
