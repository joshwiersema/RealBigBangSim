# Phase 2: Core Rendering - Research

**Researched:** 2026-03-28
**Domain:** GPU-accelerated particle rendering, compute shaders, post-processing pipeline (ModernGL + GLSL 4.30)
**Confidence:** HIGH

## Summary

Phase 2 builds the GPU particle rendering pipeline on the Phase 1 foundation. The core challenge is threefold: (1) implementing a compute shader particle system with ping-pong double-buffered SSBOs that handles 100K-1M particles at 30+ FPS, (2) establishing a modular per-era shader architecture with shared GLSL utility libraries that avoids the mega-shader anti-pattern, and (3) building a multi-pass post-processing pipeline (HDR framebuffer, bloom extraction, Gaussian blur, tone mapping) that produces cinematic glow effects.

The existing codebase provides a solid foundation: `app.py` has a working render loop with camera-relative view matrices (PHYS-07), `DampedOrbitCamera` provides view/projection matrices, and GLSL 4.30 shaders are already compiled and running. Phase 2 replaces the test scene (500 random points rendered as `GL_POINTS`) with a proper GPU-resident particle system and wraps the rendering output in an FBO-based post-processing chain.

All technologies are verified available: ModernGL 5.12.0 supports `ctx.compute_shader()`, `ctx.memory_barrier()`, and `ctx.framebuffer()` with RGBA16F textures (`dtype="f2"`). moderngl-window provides `geometry.quad_fs()` for fullscreen post-processing passes. The user's GPU supports OpenGL 4.3+ (required for compute shaders). No new dependencies are needed beyond what Phase 1 already installed.

**Primary recommendation:** Build the particle system with compute shaders from day one (never CPU-side updates), use ping-pong SSBOs with `std430` layout, render particles as `GL_POINTS` with additive blending, route all rendering through an HDR FBO, and implement bloom as a 5-pass chain (bright extract, 2x Gaussian blur, composite + tone map). Shader utility functions (noise, color mapping) live in Python-concatenated include files, not OpenGL extension-based `#include`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None -- user deferred all gray areas to Claude's judgment.

### Claude's Discretion
User deferred all gray areas to Claude's judgment. Full discretion on:
- Compute shader workgroup sizing and SSBO layout
- Ping-pong double-buffer strategy for particle updates
- Bloom kernel size and HDR tone mapping curve
- Shader utility library organization
- Number and nature of initial shader variants for architecture validation
- Particle billboard vs point sprite rendering approach
- FBO chain for multi-pass post-processing

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RNDR-01 | Application renders 100K-1M particles in real-time via GPU compute shaders at 30+ FPS | Compute shader particle system with ping-pong SSBOs; workgroup size 256; `ctx.memory_barrier()` between compute and render; additive blending with `GL_POINTS` rendering |
| RNDR-02 | Post-processing pipeline applies bloom, HDR, and tone mapping to produce cinematic glow effects | HDR FBO (RGBA16F via `dtype="f2"`), bright-pass extraction, separable Gaussian blur (ping-pong FBOs at half-res), exposure-based tone mapping + gamma correction, fullscreen quad via `geometry.quad_fs()` |
| RNDR-06 | Per-era shader architecture uses shared utility libraries with separate programs per era (not a mega-shader) | Python-side shader preprocessor concatenates shared include files (noise, color mapping, common uniforms) into per-era shader sources; separate `ctx.program()` per visual style; program switching at era boundaries |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech Stack**: Python 3.14 (actual install, per Phase 1 decision), ModernGL 5.12.0, GLSL 4.30, PyGLM 2.8.3, NumPy 2.4.3
- **Performance**: Must maintain 30+ FPS on GTX 1060-class GPU with 100K+ particles
- **Scientific Accuracy**: Physics parameters from Planck 2018 / PDG values (constants module already established)
- **Platform**: Windows primary (user environment), cross-platform compatible code
- **Dependencies**: Minimize exotic dependencies -- no new pip installs needed for Phase 2
- **GSD Workflow**: All edits through GSD commands
- **Simulation-Rendering boundary**: Simulation modules have ZERO imports from rendering layer (established Phase 1 decision)

## Standard Stack

### Core (already installed)

| Library | Version | Purpose | Verified |
|---------|---------|---------|----------|
| ModernGL | 5.12.0 | OpenGL 4.3 binding: compute shaders, SSBOs, FBOs | Installed, verified via import |
| moderngl-window | 3.1.1 | Windowing, `geometry.quad_fs()` for fullscreen passes | Installed |
| PyGLM | 2.8.3 | Matrix/vector math for uniforms | Installed |
| NumPy | 2.4.3 | Particle data initialization, buffer marshaling | Installed |

### No new dependencies needed

Phase 2 uses only ModernGL APIs that are already available:
- `ctx.compute_shader(source)` -- create compute shader
- `ctx.memory_barrier()` -- synchronize after compute dispatch
- `ctx.texture(size, components, dtype="f2")` -- RGBA16F textures
- `ctx.framebuffer(color_attachments=[texture], depth_attachment=...)` -- FBO creation
- `buffer.bind_to_storage_buffer(binding)` -- SSBO binding for compute shaders
- `geometry.quad_fs()` -- fullscreen quad for post-processing passes

## Architecture Patterns

### Recommended Project Structure (Phase 2 additions)

```
bigbangsim/
  rendering/
    __init__.py          # (existing)
    camera.py            # (existing) DampedOrbitCamera
    coordinates.py       # (existing) Camera-relative transforms
    particles.py         # NEW: ParticleSystem class (SSBOs, compute dispatch)
    postprocessing.py    # NEW: PostProcessingPipeline class (FBO chain, bloom)
    shader_loader.py     # NEW: Shader loading with include preprocessing
  shaders/
    test_scene.vert/frag # (existing, kept for reference but replaced in render loop)
    timeline_bar.vert/frag # (existing, kept)
    compute/
      particle_update.comp # NEW: Compute shader for particle physics
    vertex/
      particle.vert       # NEW: Particle rendering vertex shader
    fragment/
      particle_hot.frag   # NEW: Variant 1 -- hot plasma particles (early eras)
      particle_cool.frag  # NEW: Variant 2 -- cool matter particles (later eras)
    postprocess/
      bright_extract.frag # NEW: Bright-pass extraction for bloom
      gaussian_blur.frag  # NEW: Separable Gaussian blur
      tonemap.frag        # NEW: HDR tone mapping + bloom composite
      fullscreen.vert     # NEW: Simple passthrough vertex shader for quad_fs
    include/
      common.glsl         # NEW: Shared uniforms, constants
      noise.glsl          # NEW: Simplex/Perlin noise functions
      colormap.glsl       # NEW: Temperature-to-color mapping
```

### Pattern 1: Ping-Pong Double-Buffered SSBO Particle System

**What:** Two Shader Storage Buffer Objects alternate roles each frame -- one is the read source, the other is the write destination. After compute shader dispatch, they swap.

**When to use:** Always for GPU particle systems. Avoids read-write hazards on the same buffer.

**ModernGL implementation:**

```python
# Source: ModernGL docs (ctx.compute_shader, buffer.bind_to_storage_buffer)
class ParticleSystem:
    def __init__(self, ctx: moderngl.Context, count: int):
        self.ctx = ctx
        self.count = count
        self.current = 0  # Index of "read" buffer

        # Particle data: vec4 position (xyz + padding), vec4 velocity (xyz + padding),
        # vec4 color (rgba)
        stride = 4 * 4 * 3  # 3 vec4s = 48 bytes per particle

        # Initialize positions on CPU, upload once
        init_data = self._generate_initial_particles(count)

        # Two position+velocity+color buffers for ping-pong
        self.buffers = [
            ctx.buffer(init_data),
            ctx.buffer(init_data),  # Both start identical
        ]

        # Load compute shader with include preprocessing
        self.compute = ctx.compute_shader(
            load_shader_source('compute/particle_update.comp')
        )

    def update(self, dt: float, physics_state):
        """Dispatch compute shader to update particles."""
        read_buf = self.buffers[self.current]
        write_buf = self.buffers[1 - self.current]

        read_buf.bind_to_storage_buffer(0)   # binding=0 readonly
        write_buf.bind_to_storage_buffer(1)   # binding=1 writeonly

        # Upload physics uniforms
        self.compute['u_dt'].value = dt
        self.compute['u_temperature'].value = physics_state.temperature
        self.compute['u_scale_factor'].value = physics_state.scale_factor
        self.compute['u_era'].value = physics_state.current_era

        # Dispatch: 256 threads per workgroup
        num_groups = (self.count + 255) // 256
        self.compute.run(group_x=num_groups)

        # Memory barrier: ensure compute writes are visible to vertex shader
        self.ctx.memory_barrier()

        # Swap buffers
        self.current = 1 - self.current

    def get_render_buffer(self):
        """Return the buffer containing the latest particle data for rendering."""
        return self.buffers[self.current]
```

### Pattern 2: HDR Framebuffer + Multi-Pass Post-Processing

**What:** Scene is rendered to an off-screen RGBA16F FBO. A chain of fullscreen quad passes (bright extraction, Gaussian blur, composite + tone mapping) transforms the image before display.

**Pipeline:**
```
Pass 0: Scene render (particles) -> HDR FBO (RGBA16F)
Pass 1: Bright-pass extraction -> Bloom FBO (half-res RGBA16F)
Pass 2: Horizontal Gaussian blur -> Blur ping FBO
Pass 3: Vertical Gaussian blur -> Blur pong FBO
Pass 4: Composite (HDR scene + bloom) + tone mapping + gamma -> Screen
```

**ModernGL implementation:**

```python
# Source: ModernGL docs (ctx.texture, ctx.framebuffer), LearnOpenGL Bloom
class PostProcessingPipeline:
    def __init__(self, ctx: moderngl.Context, width: int, height: int):
        self.ctx = ctx
        self.quad = geometry.quad_fs()  # moderngl-window fullscreen quad

        # HDR scene FBO (full resolution, RGBA16F)
        self.hdr_texture = ctx.texture((width, height), 4, dtype="f2")
        self.hdr_depth = ctx.depth_renderbuffer((width, height))
        self.hdr_fbo = ctx.framebuffer(
            color_attachments=[self.hdr_texture],
            depth_attachment=self.hdr_depth,
        )

        # Bloom FBOs (half resolution for performance)
        hw, hh = width // 2, height // 2
        self.bloom_texture = ctx.texture((hw, hh), 4, dtype="f2")
        self.bloom_fbo = ctx.framebuffer(color_attachments=[self.bloom_texture])

        # Ping-pong blur FBOs (half resolution)
        self.blur_textures = [
            ctx.texture((hw, hh), 4, dtype="f2"),
            ctx.texture((hw, hh), 4, dtype="f2"),
        ]
        self.blur_fbos = [
            ctx.framebuffer(color_attachments=[self.blur_textures[0]]),
            ctx.framebuffer(color_attachments=[self.blur_textures[1]]),
        ]

        # Load post-processing shaders
        self.bright_prog = ctx.program(...)   # bright extraction
        self.blur_prog = ctx.program(...)     # separable Gaussian blur
        self.tonemap_prog = ctx.program(...)  # composite + tone map

    def render(self):
        """Execute the full post-processing chain."""
        # Pass 1: Extract bright pixels
        self.bloom_fbo.use()
        self.hdr_texture.use(location=0)
        self.bright_prog['u_scene'].value = 0
        self.bright_prog['u_threshold'].value = 1.0
        self.quad.render(self.bright_prog)

        # Pass 2-3: Gaussian blur (ping-pong, N iterations)
        horizontal = True
        first = True
        for i in range(10):  # 10 blur iterations
            self.blur_fbos[int(horizontal)].use()
            tex = self.bloom_texture if first else self.blur_textures[int(not horizontal)]
            tex.use(location=0)
            self.blur_prog['u_image'].value = 0
            self.blur_prog['u_horizontal'].value = horizontal
            self.quad.render(self.blur_prog)
            horizontal = not horizontal
            first = False

        # Pass 4: Composite + tone map -> default framebuffer (screen)
        self.ctx.screen.use()
        self.hdr_texture.use(location=0)
        self.blur_textures[int(not horizontal)].use(location=1)
        self.tonemap_prog['u_scene'].value = 0
        self.tonemap_prog['u_bloom'].value = 1
        self.tonemap_prog['u_exposure'].value = 1.0
        self.quad.render(self.tonemap_prog)
```

### Pattern 3: Python-Side Shader Include Preprocessing

**What:** Since `#include` is not standard GLSL (requires `GL_ARB_shading_language_include` which is driver-dependent), we preprocess includes on the Python side: read include files, replace `#include "filename"` directives with file contents, then pass the assembled source to `ctx.program()` or `ctx.compute_shader()`.

**Why not use the GL extension:** The `GL_ARB_shading_language_include` extension is implemented on NVIDIA but not reliably on AMD/Intel. Python-side preprocessing is portable, simple, and debuggable.

**Implementation:**

```python
import re
from pathlib import Path

SHADER_DIR = Path(__file__).parent.parent / "shaders"

def load_shader_source(shader_path: str) -> str:
    """Load a GLSL shader file with #include preprocessing.

    Replaces lines matching: #include "path/to/file.glsl"
    with the contents of that file relative to shaders/ directory.
    """
    full_path = SHADER_DIR / shader_path
    source = full_path.read_text()

    include_pattern = re.compile(r'#include\s+"([^"]+)"')

    def replace_include(match):
        include_path = SHADER_DIR / "include" / match.group(1)
        if not include_path.exists():
            raise FileNotFoundError(f"Shader include not found: {include_path}")
        return include_path.read_text()

    return include_pattern.sub(replace_include, source)
```

### Pattern 4: Per-Era Shader Program Switching

**What:** Compile separate fragment shader programs per visual style. The compute shader stays the same (physics is physics), but the fragment shader determines the look. At era transitions, switch the active program.

**Validation requirement (RNDR-06):** At least 2 distinct shader variants must load successfully.

**Recommended initial variants:**
1. `particle_hot.frag` -- Bright, additive, orange-white glow (Planck through Nucleosynthesis eras). Uses temperature-based color from colormap.glsl.
2. `particle_cool.frag` -- Dimmer, point-like, blue-white (Dark Ages through Large-Scale Structure eras). Uses density-based sizing.

These two variants prove the architecture without needing all 11 era-specific shaders (which is Phase 3's job).

### Anti-Patterns to Avoid

- **CPU-side particle updates:** Never update particle positions in Python/NumPy and re-upload per frame. At 1M particles = 48MB/frame = 2.8 GB/s transfer. Use compute shaders exclusively.
- **Mega-shader with era branching:** No `if (era == 0) ... else if (era == 1) ...` in fragment shaders. Compile separate programs per visual style.
- **Recreating GPU resources per frame:** All buffers, programs, FBOs, and textures created at initialization. Only uniforms are uploaded per frame.
- **Reading back GPU buffers per frame:** No `buffer.read()` or `fbo.read()` in the render loop. Data stays GPU-resident.
- **Same-buffer read-write in compute:** Always use ping-pong double-buffering for SSBOs to avoid driver-dependent read-write hazards.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fullscreen quad geometry | Manual vertex buffer for a 2-triangle screen quad | `moderngl_window.geometry.quad_fs()` | Returns a configured VAO with position, normals, UV coords. 1 line vs 30. |
| Shader program compilation | Raw `ctx.program()` calls scattered through code | `shader_loader.py` with include preprocessing | Centralizes error handling, include resolution, caching. Shared by all modules. |
| Gaussian blur weights | Computing Gaussian distribution coefficients at runtime | Hardcoded 5-tap weights: `[0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216]` | These weights are the standard 5-sample Gaussian approximation. Computing them is unnecessary math. |
| Memory barrier management | Manual `glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)` calls | `ctx.memory_barrier()` (defaults to ALL_BARRIER_BITS) | ModernGL wraps this cleanly. Using ALL_BARRIER_BITS is safe and prevents subtle sync bugs. |
| Tone mapping math | Custom tone curve | Exposure-based: `vec3(1.0) - exp(-hdrColor * exposure)` | Standard, adjustable via single float uniform. Better than Reinhard for scenes with high dynamic range variation. |

## Common Pitfalls

### Pitfall 1: SSBO Alignment and Padding

**What goes wrong:** GLSL `std430` layout has alignment rules. A `struct { vec3 pos; float life; vec3 vel; float pad; }` would pack incorrectly because `vec3` aligns to 16 bytes in some contexts. Subtle data corruption causes particles to fly to infinity.

**Why it happens:** `std430` aligns `vec3` to 4-byte boundaries (unlike `std140` which aligns to 16), but mixing `vec3` and scalar types can still cause confusion. The safest approach is to use `vec4` for everything.

**How to avoid:** Use `vec4` for all SSBO fields. Pad with unused `.w` components. This wastes 25% memory but guarantees correct alignment on all drivers.

```glsl
// GOOD: All vec4, no alignment ambiguity
struct Particle {
    vec4 position;  // xyz = position, w = life
    vec4 velocity;  // xyz = velocity, w = type
    vec4 color;     // rgba
};
```

**Memory cost:** 48 bytes/particle. At 1M particles = 48 MB per buffer, 96 MB for ping-pong pair. Trivial for a 3GB+ GPU.

### Pitfall 2: Missing Memory Barrier After Compute Dispatch

**What goes wrong:** Particles render with stale positions (one frame behind), causing visible stuttering or doubling effect.

**Why it happens:** GPU operations are asynchronous. After `compute_shader.run()`, the GPU may not have finished writing to the SSBO before the vertex shader tries to read it.

**How to avoid:** Always call `ctx.memory_barrier()` between compute dispatch and the render pass that reads the SSBO. This is a single line but absolutely critical.

```python
self.compute.run(group_x=num_groups)
self.ctx.memory_barrier()  # MUST call this before rendering
```

### Pitfall 3: Bloom at Full Resolution

**What goes wrong:** Bloom blur passes at full resolution (1920x1080) with 10 iterations cost 3-5ms per frame on a GTX 1060, eating a significant portion of the 33ms budget for 30 FPS.

**Why it happens:** Each blur pass is a fullscreen fragment shader invocation. At full resolution with 10 iterations, that is 10 fullscreen passes.

**How to avoid:** Run bloom at half resolution (960x540). Glow effects are inherently blurry -- downsampling is visually indistinguishable from full-res bloom but costs 4x less. The final composite pass samples the bloom texture at full resolution using bilinear filtering.

### Pitfall 4: Forgetting to Swap FBO Back to Screen

**What goes wrong:** After rendering to the HDR FBO and running post-processing, the timeline bar and future HUD elements also render into the wrong FBO, or nothing appears on screen.

**Why it happens:** The `fbo.use()` call sets the active render target. If you forget to call `ctx.screen.use()` (or `self.ctx.fbo.use()` in moderngl-window which represents the default framebuffer) before rendering overlays, they go to the wrong target.

**How to avoid:** The post-processing pipeline's final pass explicitly targets the screen. All subsequent rendering (timeline bar, HUD) happens after this. Document the render order clearly.

### Pitfall 5: Particle Count Not Matching Workgroup Dispatch

**What goes wrong:** If particle count is not a multiple of the workgroup size (256), the last workgroup reads/writes beyond the buffer bounds, causing GPU crashes or garbage data.

**Why it happens:** `compute.run(group_x=count // 256)` drops the remainder.

**How to avoid:** Use ceiling division: `group_x = (count + 255) // 256`, and guard in the compute shader:

```glsl
void main() {
    uint idx = gl_GlobalInvocationID.x;
    if (idx >= u_particle_count) return;
    // ... process particle
}
```

### Pitfall 6: Additive Blending Without Disabling Depth Write

**What goes wrong:** Particles use additive blending (`GL_ONE, GL_ONE`) for glow effects, but depth test discards particles behind others. Overlapping particles do not accumulate light -- the result looks flat instead of glowing.

**Why it happens:** Default depth test + depth write discards fragments at equal or greater depth. Particles are not opaque objects -- they should all contribute to the final color.

**How to avoid:** Disable depth write (but keep depth test for scene ordering) when rendering particles with additive blending:

```python
self.ctx.enable(moderngl.BLEND)
self.ctx.blend_func = moderngl.ONE, moderngl.ONE  # Additive
self.ctx.depth_mask = False  # Don't write depth
# ... render particles
self.ctx.depth_mask = True   # Restore for next pass
```

## Code Examples

### Compute Shader: Particle Update (GLSL 4.30)

```glsl
// Source: Verified GLSL 4.30 compute shader pattern
// File: shaders/compute/particle_update.comp
#version 430

layout(local_size_x = 256) in;

struct Particle {
    vec4 position;  // xyz = pos, w = life
    vec4 velocity;  // xyz = vel, w = type
    vec4 color;     // rgba
};

layout(std430, binding = 0) readonly buffer ParticlesIn {
    Particle particles_in[];
};

layout(std430, binding = 1) writeonly buffer ParticlesOut {
    Particle particles_out[];
};

uniform float u_dt;
uniform float u_temperature;
uniform float u_scale_factor;
uniform uint u_particle_count;
uniform int u_era;

void main() {
    uint idx = gl_GlobalInvocationID.x;
    if (idx >= u_particle_count) return;

    Particle p = particles_in[idx];

    // Simple expansion: scale positions by Hubble-like flow
    vec3 pos = p.position.xyz;
    vec3 vel = p.velocity.xyz;

    // Hubble flow: velocity proportional to distance from origin
    float expansion_rate = u_scale_factor * 0.01;
    vel += pos * expansion_rate * u_dt;

    // Damping to prevent runaway
    vel *= (1.0 - 0.01 * u_dt);

    // Integrate position
    pos += vel * u_dt;

    particles_out[idx].position = vec4(pos, p.position.w);
    particles_out[idx].velocity = vec4(vel, p.velocity.w);
    particles_out[idx].color = p.color;
}
```

### Particle Rendering Vertex Shader

```glsl
// File: shaders/vertex/particle.vert
#version 430

uniform mat4 u_projection;
uniform mat4 u_view;
uniform float u_point_scale;

struct Particle {
    vec4 position;
    vec4 velocity;
    vec4 color;
};

layout(std430, binding = 0) readonly buffer Particles {
    Particle particles[];
};

out vec4 v_color;

void main() {
    Particle p = particles[gl_VertexID];
    gl_Position = u_projection * u_view * vec4(p.position.xyz, 1.0);
    gl_PointSize = u_point_scale / max(gl_Position.w, 0.01);
    v_color = p.color;
}
```

### Bright-Pass Extraction Fragment Shader

```glsl
// Source: LearnOpenGL Bloom tutorial, adapted for GLSL 4.30
// File: shaders/postprocess/bright_extract.frag
#version 430

in vec2 v_texcoord;
out vec4 fragColor;

uniform sampler2D u_scene;
uniform float u_threshold;

void main() {
    vec3 color = texture(u_scene, v_texcoord).rgb;
    float brightness = dot(color, vec3(0.2126, 0.7152, 0.0722));
    if (brightness > u_threshold)
        fragColor = vec4(color, 1.0);
    else
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
}
```

### Separable Gaussian Blur Fragment Shader

```glsl
// Source: LearnOpenGL Bloom tutorial
// File: shaders/postprocess/gaussian_blur.frag
#version 430

in vec2 v_texcoord;
out vec4 fragColor;

uniform sampler2D u_image;
uniform bool u_horizontal;

// Standard 5-tap Gaussian weights
const float weight[5] = float[](0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);

void main() {
    vec2 tex_offset = 1.0 / textureSize(u_image, 0);
    vec3 result = texture(u_image, v_texcoord).rgb * weight[0];

    if (u_horizontal) {
        for (int i = 1; i < 5; ++i) {
            result += texture(u_image, v_texcoord + vec2(tex_offset.x * i, 0.0)).rgb * weight[i];
            result += texture(u_image, v_texcoord - vec2(tex_offset.x * i, 0.0)).rgb * weight[i];
        }
    } else {
        for (int i = 1; i < 5; ++i) {
            result += texture(u_image, v_texcoord + vec2(0.0, tex_offset.y * i)).rgb * weight[i];
            result += texture(u_image, v_texcoord - vec2(0.0, tex_offset.y * i)).rgb * weight[i];
        }
    }
    fragColor = vec4(result, 1.0);
}
```

### Tone Mapping + Bloom Composite Fragment Shader

```glsl
// Source: LearnOpenGL HDR + Bloom tutorial
// File: shaders/postprocess/tonemap.frag
#version 430

in vec2 v_texcoord;
out vec4 fragColor;

uniform sampler2D u_scene;
uniform sampler2D u_bloom;
uniform float u_exposure;
uniform float u_bloom_strength;

void main() {
    const float gamma = 2.2;
    vec3 hdrColor = texture(u_scene, v_texcoord).rgb;
    vec3 bloomColor = texture(u_bloom, v_texcoord).rgb;

    // Additive bloom blending
    hdrColor += bloomColor * u_bloom_strength;

    // Exposure-based tone mapping
    vec3 mapped = vec3(1.0) - exp(-hdrColor * u_exposure);

    // Gamma correction
    mapped = pow(mapped, vec3(1.0 / gamma));

    fragColor = vec4(mapped, 1.0);
}
```

### Fullscreen Vertex Shader for Post-Processing

```glsl
// File: shaders/postprocess/fullscreen.vert
#version 430

in vec3 in_position;
in vec2 in_texcoord_0;

out vec2 v_texcoord;

void main() {
    gl_Position = vec4(in_position, 1.0);
    v_texcoord = in_texcoord_0;
}
```

**Note on attribute names:** `geometry.quad_fs()` uses attribute names `in_position` (3f) and `in_texcoord_0` (2f) by default. The vertex shader must match these names exactly.

### Rendering Particles via gl_VertexID (No VAO Needed)

```python
# Particles are read from SSBO via gl_VertexID in the vertex shader
# No VAO with vertex attributes needed -- SSBO provides all data
particle_buf = self.particle_system.get_render_buffer()
particle_buf.bind_to_storage_buffer(0)

# Create an empty VAO for the draw call
empty_vao = ctx.vertex_array(particle_prog, [])
empty_vao.render(moderngl.POINTS, vertices=self.particle_system.count)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CPU particle updates with buffer re-upload | GPU compute shaders with SSBO ping-pong | OpenGL 4.3 (2013) | 100x+ throughput for 1M particles |
| Single monolithic shader with branching | Per-era shader programs with shared includes | Best practice, ongoing | Maintainability, GPU branch divergence avoidance |
| LDR rendering with fake glow | HDR FBO + physically-based bloom + tone mapping | Standard since ~2010 | Realistic light behavior, cinematic quality |
| `#include` via GL extension | Python-side shader preprocessing | Practical standard | Cross-vendor compatibility |
| `GL_POINTS` with fixed size | `GL_POINTS` with `gl_PointSize` in vertex shader | Core since GL 3.2 | Perspective-correct particle sizing |

## Open Questions

1. **gl_VertexID vs traditional VAO for SSBO-based rendering**
   - What we know: Reading particle data from SSBO via `gl_VertexID` in the vertex shader avoids needing a VAO with vertex attribute pointers. An "empty" VAO is passed to the render call.
   - What's unclear: ModernGL 5.12's exact behavior with empty VAOs and `gl_VertexID`. Some older ModernGL versions required at least one buffer in the VAO.
   - Recommendation: Test with an empty VAO first. If it fails, create a minimal dummy buffer. The ParticleSim community example used this pattern successfully with ModernGL.

2. **Bloom iteration count tuning**
   - What we know: 10 blur iterations is the LearnOpenGL default. More iterations = wider bloom.
   - What's unclear: What looks best for this specific particle aesthetic. Too much bloom washes out details; too little looks like no post-processing.
   - Recommendation: Start with 6 iterations (3 horizontal + 3 vertical) at half resolution. Expose `u_bloom_strength` and iteration count as tunable uniforms. Final tuning is visual, not algorithmic.

3. **Point size scaling formula**
   - What we know: `gl_PointSize = scale / gl_Position.w` gives perspective-correct sizing.
   - What's unclear: Best default scale factor for the cosmological scene. Particles too large = blobby mess; too small = invisible.
   - Recommendation: Default `u_point_scale` to 50.0, allow per-era adjustment. The fragment shaders can also alpha-fade based on distance from point center for soft particles.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >= 9 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `py -3.14 -m pytest tests/ -x -q` |
| Full suite command | `py -3.14 -m pytest tests/ -v` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RNDR-01 | 100K+ particles rendered via compute shaders at 30+ FPS | manual + smoke | Manual: run app, check FPS in title bar | N/A -- requires GPU |
| RNDR-01 | ParticleSystem creates correct SSBO buffers | unit | `py -3.14 -m pytest tests/test_particles.py -x` | Wave 0 |
| RNDR-01 | Particle count and buffer sizes are correct | unit | `py -3.14 -m pytest tests/test_particles.py -x` | Wave 0 |
| RNDR-02 | PostProcessingPipeline creates HDR FBO with RGBA16F | unit | `py -3.14 -m pytest tests/test_postprocessing.py -x` | Wave 0 |
| RNDR-02 | Bloom visible in rendered output | manual | Manual: run app, verify glow effects visually | N/A |
| RNDR-06 | Shader loader resolves includes correctly | unit | `py -3.14 -m pytest tests/test_shader_loader.py -x` | Wave 0 |
| RNDR-06 | At least 2 distinct shader variants compile and load | unit | `py -3.14 -m pytest tests/test_shader_loader.py -x` | Wave 0 |
| RNDR-06 | No mega-shader branching in fragment shaders | structural | `py -3.14 -m pytest tests/test_shader_loader.py -x` (source inspection) | Wave 0 |

### Sampling Rate
- **Per task commit:** `py -3.14 -m pytest tests/ -x -q`
- **Per wave merge:** `py -3.14 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_particles.py` -- covers RNDR-01 (buffer creation, particle count, data layout)
- [ ] `tests/test_postprocessing.py` -- covers RNDR-02 (FBO creation, texture formats)
- [ ] `tests/test_shader_loader.py` -- covers RNDR-06 (include preprocessing, shader variant compilation)

**Note:** GPU-dependent tests (actual rendering, FPS measurement, visual bloom verification) require a GPU context and must be tested manually or via integration tests that create a standalone ModernGL context. The unit tests above validate the Python-side logic (buffer sizes, data layout, shader source assembly) without requiring a GPU.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | Yes | 3.14 | -- |
| ModernGL | All GPU operations | Yes | 5.12.0 | -- |
| moderngl-window | Window, geometry.quad_fs() | Yes | 3.1.1 | -- |
| PyGLM | Matrix uniforms | Yes | 2.8.3 | -- |
| NumPy | Particle initialization | Yes | 2.4.3 | -- |
| OpenGL 4.3+ GPU | Compute shaders | Yes (user has GTX-class GPU) | -- | CPU fallback (not in Phase 2 scope) |
| pytest | Testing | Yes | Installed as dev dep | -- |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None.

## Sources

### Primary (HIGH confidence)
- [ModernGL 5.12.0 ComputeShader docs (GitHub RST)](https://raw.githubusercontent.com/moderngl/moderngl/main/docs/reference/compute_shader.rst) -- `ctx.compute_shader()`, `run()`, uniform access
- [ModernGL 5.12.0 Context docs (GitHub RST)](https://raw.githubusercontent.com/moderngl/moderngl/main/docs/reference/context.rst) -- `ctx.memory_barrier()`, `ctx.framebuffer()`, `ctx.texture()`
- [ModernGL 5.12.0 Framebuffer docs (GitHub RST)](https://raw.githubusercontent.com/moderngl/moderngl/main/docs/reference/framebuffer.rst) -- FBO creation, `use()`, `clear()`, `read()`
- [ModernGL Texture Formats (GitHub RST)](https://raw.githubusercontent.com/moderngl/moderngl/main/docs/topics/texture_formats.rst) -- `dtype="f2"` for RGBA16F, `dtype="f4"` for RGBA32F
- [moderngl-window geometry.quad_fs() source](https://github.com/moderngl/moderngl-window/blob/master/moderngl_window/geometry/quad.py) -- `quad_fs()` returns VAO with `in_position` (3f) + `in_texcoord_0` (2f)
- [moderngl-window shader_includes.py example](https://github.com/moderngl/moderngl-window/blob/master/examples/advanced/shader_includes.py) -- shader include pattern

### Secondary (MEDIUM confidence)
- [LearnOpenGL - Bloom](https://learnopengl.com/Advanced-Lighting/Bloom) -- bright-pass extraction, separable Gaussian blur, ping-pong FBOs, compositing shader code
- [LearnOpenGL - HDR](https://learnopengl.com/Advanced-Lighting/HDR) -- Reinhard and exposure-based tone mapping, RGBA16F framebuffer setup
- [Khronos OpenGL Wiki - Compute Shader](https://www.khronos.org/opengl/wiki/Compute_Shader) -- workgroup sizing, dispatch, shared memory
- [Khronos OpenGL Wiki - Memory Model](https://www.khronos.org/opengl/wiki/Memory_Model) -- memory barrier requirements
- [J Stephano SSBO Tutorial](https://ktstephano.github.io/rendering/opengl/ssbos) -- std430 layout, SSBO binding patterns
- [ModernGL_ParticleSim](https://github.com/casparmaria/ModernGL_ParticleSim) -- Community example: 2^27 particles at 60fps with ModernGL compute shaders

### Tertiary (LOW confidence)
- [Rendering Particles with Compute Shaders (Mike Turitzin)](https://miketuritzin.com/post/rendering-particles-with-compute-shaders/) -- Atomic operations for single-pixel particle rendering (explored but not recommended for our use case)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and verified from Phase 1
- Architecture: HIGH -- ping-pong SSBO + FBO post-processing is the established pattern for GPU particle systems, verified across multiple authoritative sources
- Pitfalls: HIGH -- all pitfalls documented from official sources (Khronos wiki, ModernGL docs, LearnOpenGL)
- Code examples: MEDIUM -- shader code adapted from LearnOpenGL (C++/OpenGL) to ModernGL Python API, ModernGL-specific patterns verified from docs but not all tested on this exact codebase yet

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable domain -- OpenGL 4.3 and ModernGL 5.12 are mature)
